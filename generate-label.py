import numpy as np
from scipy.io import wavfile
import sys

def filter_close(onsets, min_gap=2.5):
    """
    Filter onsets to ensure minimum gap; keep the first in close clusters.
    """
    if not onsets:
        return []
    sorted_onsets = sorted(onsets)
    filtered = [sorted_onsets[0]]
    for t in sorted_onsets[1:]:
        if t - filtered[-1] >= min_gap:
            filtered.append(t)
    return filtered

def detect_onsets(data, fs, silence_thresh, min_pause_dur, max_pause_dur, pre_onset_window=0.01, start_idx=0, end_idx=None):
    """
    Detect onsets after pauses in the specified segment.
    """
    if end_idx is None:
        end_idx = len(data)
    segment_data = data[start_idx:end_idx]
    
    # Frame parameters
    frame_length = int(0.005 * fs)  # 5ms frames
    hop_length = int(0.002 * fs)    # 2ms hop
    
    frames = []
    for i in range(0, len(segment_data) - frame_length, hop_length):
        frame = segment_data[i:i + frame_length]
        rms = np.sqrt(np.mean(frame**2))
        frames.append(rms)
    
    segment_times = np.arange(len(frames)) * hop_length / fs
    pause_mask = np.array(frames) < silence_thresh
    
    onsets = []
    i = 0
    while i < len(pause_mask):
        if pause_mask[i]:
            pause_start = i
            while i < len(pause_mask) and pause_mask[i]:
                i += 1
            pause_end = i
            pause_dur = (pause_end - pause_start) * hop_length / fs
            if min_pause_dur <= pause_dur <= max_pause_dur:
                look_ahead = int(0.1 * fs / hop_length)  # 100ms ahead
                segment_rms = frames[pause_end:pause_end + look_ahead]
                if len(segment_rms) > 10:
                    rises = np.diff(segment_rms)
                    if len(rises) > 0:
                        peak_rise_idx = np.argmax(rises)
                        onset_frame_idx = pause_end + peak_rise_idx + 1
                        onset_frame_idx -= int(pre_onset_window * fs / hop_length)
                        onset_time = segment_times[onset_frame_idx] + (start_idx / fs)
                        onsets.append(onset_time)
        else:
            i += 1
    return onsets

def find_sloka_onsets(wav_file, silence_thresh=0.015, rescan_thresh_increase=0.01,
                      min_pause_dur=0.015, max_pause_dur=0.15, min_gap=2.5, max_gap=8.0,
                      expected_interval=4.5, initial_skip=3.0):
    """
    Detect sloka onsets with post-processing for min gaps and filling large gaps.
    """
    fs, data = wavfile.read(wav_file)
    
    # Mono and normalize
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    data = data.astype(np.float32)
    data /= np.max(np.abs(data))
    
    # Initial detection
    initial_onsets = detect_onsets(data, fs, silence_thresh, min_pause_dur, max_pause_dur)
    
    # Filter initial skip and close ones
    onsets = [t for t in initial_onsets if t > initial_skip]
    onsets = filter_close(onsets, min_gap)
    
    # Loop to fill large gaps
    rescan_thresh = silence_thresh + rescan_thresh_increase
    rescan_min_dur = min_pause_dur * 0.75  # Relax a bit
    rescan_max_dur = max_pause_dur * 1.5
    
    while True:
        gaps = [onsets[i+1] - onsets[i] for i in range(len(onsets)-1)] if len(onsets) > 1 else []
        large_gap_indices = [i for i, g in enumerate(gaps) if g > max_gap]
        if not large_gap_indices:
            break
        
        additional = []
        for idx in large_gap_indices:
            t1 = onsets[idx]
            t2 = onsets[idx + 1]
            start_idx = int((t1 + 1.0) * fs)  # Start 1s after t1 to avoid overlap
            end_idx = int((t2 - 1.0) * fs)    # End 1s before t2
            if end_idx <= start_idx:
                continue
            
            missed_onsets = detect_onsets(data, fs, rescan_thresh, rescan_min_dur, rescan_max_dur,
                                          start_idx=start_idx, end_idx=end_idx)
            
            if missed_onsets:
                # Pick the one closest to expected interval (t1 + expected_interval)
                best = min(missed_onsets, key=lambda m: abs(m - (t1 + expected_interval)))
                # Check not too close to existing
                if all(abs(best - existing) >= min_gap for existing in onsets):
                    additional.append(best)
        
        if not additional:
            break  # No more to add
        
        onsets = sorted(onsets + additional)
        onsets = filter_close(onsets, min_gap)
    
    return onsets

def generate_point_labels(wav_file, output_file="labels.txt"):
    onsets = find_sloka_onsets(wav_file)
    
    with open(output_file, 'w') as f:
        for t in onsets:
            f.write(f"{t:.6f}\t{t:.6f}\n")
    
    print(f"Found {len(onsets)} sloka onsets.")
    print(f"Labels saved to {output_file}")
    for i, t in enumerate(onsets, 1):
        print(f"{i:2d}. {t:.3f} seconds")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sloka_markers.py <input.wav>")
        sys.exit(1)
    
    wav_path = sys.argv[1]
    generate_point_labels(wav_path)