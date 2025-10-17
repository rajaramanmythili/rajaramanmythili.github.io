#!/opt/homebrew/opt/python@3.9/libexec/bin/python

from PIL import Image, ImageDraw, ImageFont
import os
import shutil

# CONFIG
# based on macOS and Windows, set FONT_PATH_SANSKRIT and FONT_PATH_TAMIL accordingly
# macOS
FONT_PATH_SANSKRIT = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"
FONT_PATH_TAMIL = "/Library/Fonts/NotoSansTamil-Regular.ttf"
if os.name == 'nt': # Windows
    FONT_PATH_SANSKRIT = "C:/Windows/Fonts/mangal.ttf"
    FONT_PATH_TAMIL = "C:/Windows/Fonts/Nirmala.ttf"
FONT_SIZE_SANSKRIT = 55
FONT_SIZE_TAMIL = 45
LINES_PER_SLIDE = 5
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080
LINE_SPACING = 100
MARGIN_LEFT = 725
MARGIN_TOP_SANSKRIT = 90
MARGIN_TOP_TAMIL = 620
ASTRING = "sri-krishna-suprabhatam"
SKIP_LINES = 2  # Number of lines to skip at the start of each file

# get home folder from os env which works in macOS and Windows powershell too
HOME = os.path.expanduser("~")

# Load text
with open(HOME + f"/books/srisrianna/laghustotramala/{ASTRING}-sanskrit.txt", "r", encoding="utf-8") as f:
    sanskrit_lines = [line.strip() for i, line in enumerate(f) if i >= SKIP_LINES]

with open(HOME + f"/books/srisrianna/laghustotramala/{ASTRING}-tamil.txt", "r", encoding="utf-8") as f:
    tamil_lines = [line.strip() for i, line in enumerate(f) if i >= SKIP_LINES]

assert len(sanskrit_lines) == len(tamil_lines), "Line count mismatch."

# Create output folder
if os.path.exists(HOME + "/Downloads/" + ASTRING):
    shutil.rmtree(HOME + "/Downloads/" + ASTRING)
os.makedirs(HOME + "/Downloads/" + ASTRING, exist_ok=True)

# Load fonts
font_sanskrit = ImageFont.truetype(FONT_PATH_SANSKRIT, FONT_SIZE_SANSKRIT)
font_tamil = ImageFont.truetype(FONT_PATH_TAMIL, FONT_SIZE_TAMIL)

def draw_slide(s_chunk, t_chunk, highlight_idx, slide_num, first_line_title=False):
    # Skip slide if the highlighted line is blank in either language
    if not s_chunk[highlight_idx].strip() or not t_chunk[highlight_idx].strip():
        return

    # Load and cache the background image only once
    if not hasattr(draw_slide, "background"):
        draw_slide.background = Image.open(HOME + "/Downloads/" + ASTRING + "_background.png").convert("RGB").resize((SLIDE_WIDTH, SLIDE_HEIGHT))
    img = draw_slide.background.copy()
    draw = ImageDraw.Draw(img)

    first_line_fill = (0, 0, 255)
    text_fill = (0, 0, 0)
    text_highlight_fill = (0, 255, 255)
    text_shadow_fill = (0, 0, 0)
    text_shadow_highlight_fill = (0, 0, 0)

    no_blanks = first_line_title and len(s_chunk) == LINES_PER_SLIDE and all(line.strip() for line in s_chunk)
    def draw_lines(chunk, font, margin_top):
        for i, line in enumerate(chunk):
            fill = text_highlight_fill if i == highlight_idx else text_fill
            shadow_fill = text_shadow_highlight_fill if i == highlight_idx else text_shadow_fill

            # if i != highlight_idx:
            #     # Draw shadow for better visibility
            #     draw.text((MARGIN_LEFT+2, margin_top + i * LINE_SPACING + 2), line, font=font, fill=shadow_fill)
            fill = first_line_fill if i == 0 and i != highlight_idx and no_blanks else fill
            # draw a rounded corner box around the text if it's the highlighted line
            if i == highlight_idx:
                bbox = font.getbbox(line)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                draw.rounded_rectangle(
                    (
                        MARGIN_LEFT - 10,
                        margin_top + i * LINE_SPACING - 10,
                        MARGIN_LEFT + width + 10,
                        margin_top + i * LINE_SPACING + height + 10
                    ),
                    radius=15,
                    fill=(0, 0, 0, 128)
                )

            draw.text((MARGIN_LEFT, margin_top + i * LINE_SPACING), line, font=font, fill=fill)

    draw_lines(s_chunk, font_sanskrit, MARGIN_TOP_SANSKRIT)
    draw_lines(t_chunk, font_tamil, MARGIN_TOP_TAMIL)

    img.save(HOME + f"/Downloads/{ASTRING}/{ASTRING}-Slide{slide_num:04d}.png", "PNG")

if os.path.exists(HOME + "/Downloads/" + ASTRING + "_cover.png"):
    shutil.copy(HOME + "/Downloads/" + ASTRING + "_cover.png", HOME + "/Downloads/" + ASTRING + "/" + ASTRING + "-Slide0001.png")

# Generate slides
slide_num = 2
for i in range(0, len(sanskrit_lines), LINES_PER_SLIDE):
    s_chunk = sanskrit_lines[i:i+LINES_PER_SLIDE]
    t_chunk = tamil_lines[i:i+LINES_PER_SLIDE]
    max_lines = max(len(s_chunk), len(t_chunk))
    # if len(s_chunk) < LINES_PER_SLIDE:
    #    break  # skip last chunk if incomplete

    for hl in range(max_lines):
        draw_slide(s_chunk, t_chunk, hl, slide_num, first_line_title=False)
        slide_num += 1

if os.path.exists(HOME + "/Downloads/mythili-end-slide.png"):
    shutil.copy(f"{HOME}/Downloads/mythili-end-slide.png", f"{HOME}/Downloads/{ASTRING}/{ASTRING}-Slide{slide_num:04d}.png")

print(f"Done. Slides saved to {HOME}/Downloads/" + ASTRING)
