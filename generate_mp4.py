#!/usr/bin/env python3
"""
Stitch slide images + Audacity label file + wav into an mp4 using ffmpeg.

Usage:
    python generate_mp4.py 10
    python generate_mp4.py 10 --dry-run         # only write kbr10_concat.txt
    python generate_mp4.py 10 --tail-trim 0.02  # video ends 20 ms before the wav

Expects (relative to --base, default current directory, unless noted):
    kbr{num}/kbr{num}-Slide0001.png ...   (sorted by the slide number in the name)
    kbr{num}.txt                          (Audacity labels)
    ~/lmms/projects/kbr{num}.wav

Timing:
    - Slide 1 starts at 0 (it has no label).
    - Each label is the time the NEXT slide appears, so slides = labels + 1.
    - The last slide runs until the end of the wav minus --tail-trim seconds.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def read_labels(label_file: Path) -> list[float]:
    times = []
    for line in label_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Audacity also writes spectral-range lines starting with '\' - skip them
        if not line or line.startswith("\\"):
            continue
        times.append(float(line.split("\t")[0]))
    return sorted(times)


def find_slides(folder: Path) -> list[Path]:
    slides = []
    for p in folder.glob("*.png"):
        m = re.search(r"Slide(\d+)", p.name, re.IGNORECASE)
        if m:
            slides.append((int(m.group(1)), p))
    slides.sort(key=lambda x: x[0])
    return [p for _, p in slides]


def wav_duration(wav_file: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(wav_file),
        ],
        text=True,
    )
    return float(out.strip())


def compute_durations(times: list[float], end_time: float) -> list[float]:
    bounds = [0.0] + times + [end_time]
    return [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]


def write_concat(concat_file: Path, slides: list[Path], durations: list[float]) -> None:
    def esc(path: Path) -> str:
        return str(path.resolve()).replace("'", r"'\''")

    lines = []
    for slide, dur in zip(slides, durations):
        lines.append(f"file '{esc(slide)}'")
        lines.append(f"duration {dur:.6f}")
    # concat demuxer quirk: last file must be repeated, otherwise its duration is ignored
    lines.append(f"file '{esc(slides[-1])}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("num", help="number in kbr{num}")
    ap.add_argument("--base", default=".", help="folder holding kbr{num}/ and kbr{num}.txt")
    ap.add_argument("--wav-dir", default="~/lmms/projects", help="folder holding kbr{num}.wav")
    ap.add_argument("--tail-trim", type=float, default=0.05,
                    help="seconds the video ends before the wav (default 0.05)")
    ap.add_argument("--extra-dur", type=float, default=1.0,
                    help="seconds each surplus slide is shown at the end when slides > labels+1")
    ap.add_argument("--concat", default=None, help="defaults to kbr{num}_concat.txt")
    ap.add_argument("--dry-run", action="store_true", help="write the concat file but don't run ffmpeg")
    args = ap.parse_args()

    name = f"kbr{args.num}"
    base = Path(args.base).expanduser()
    slides_dir = base / name
    label_file = base / f"{name}.txt"
    wav_file = Path(args.wav_dir).expanduser() / f"{name}.wav"
    out_file = base / f"{name}.mp4"

    for p in (slides_dir, label_file, wav_file):
        if not p.exists():
            print(f"Missing: {p}", file=sys.stderr)
            return 1

    slides = find_slides(slides_dir)
    times = read_labels(label_file)

    if not slides:
        print("No slides found.", file=sys.stderr)
        return 1
    expected = len(times) + 1
    extra_slides: list[Path] = []
    if len(slides) > expected:
        extra_slides = slides[expected:]
        slides = slides[:expected]
        print(
            f"WARNING: {len(slides) + len(extra_slides)} slides but only {len(times)} labels "
            f"(expected {len(slides) + len(extra_slides) - 1}). Slides are paired in order, so "
            f"everything after the missing label will be out of sync. The last "
            f"{len(extra_slides)} slide(s) are flashed at the very end ({args.extra_dur}s each).",
            file=sys.stderr,
        )
    elif len(slides) < expected:
        times = times[: len(slides) - 1]
        print(
            f"WARNING: {len(slides)} slides but {len(times) + (expected - len(slides))} labels; "
            f"extra labels ignored.",
            file=sys.stderr,
        )

    total = wav_duration(wav_file)
    end_time = total - args.tail_trim
    durations = compute_durations(times, end_time)

    if extra_slides:
        carve = args.extra_dur * len(extra_slides)
        if durations[-1] - carve > 0.5:  # take the time from the stretched last slide
            durations[-1] -= carve
        slides = slides + extra_slides
        durations = durations + [args.extra_dur] * len(extra_slides)

    if any(d <= 0 for d in durations):
        bad = [i + 1 for i, d in enumerate(durations) if d <= 0]
        print(f"Non-positive duration for slide(s): {bad} - check labels vs wav length", file=sys.stderr)
        return 1

    concat_file = Path(args.concat) if args.concat else base / f"{name}_concat.txt"
    write_concat(concat_file, slides, durations)
    print(f"Wrote {concat_file} ({len(slides)} slides, wav {total:.3f}s, video {end_time:.3f}s)")

    # Timeline: use this to compare against the finished video and spot where sync breaks
    t = 0.0
    print("\n  #  start        slide")
    for i, (s, d) in enumerate(zip(slides, durations), 1):
        print(f"{i:3d}  {int(t // 60):02d}:{t % 60:06.3f}  {s.name}")
        t += d
    print()

    if args.dry_run:
        return 0

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-i", str(wav_file),
        "-r", "10",
        "-fps_mode", "cfr",
        "-preset", "veryfast",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-g", "30",
        "-movflags", "+faststart",
        "-fflags", "+genpts",
        "-shortest",
        "-y",
        str(out_file),
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
