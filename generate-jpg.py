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
    FONT_PATH_SANSKRIT = "C:/Windows/Fonts/Shobhika.ttf"
    FONT_PATH_TAMIL = "C:/Windows/Fonts/NotoSansTamil-Regular.ttf"
FONT_SIZE_SANSKRIT = 55
FONT_SIZE_TAMIL = 45
LINES_PER_SLIDE = 4
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080
LINE_SPACING = 100
MARGIN_TOP_SANSKRIT = 90
MARGIN_TOP_TAMIL = 620
ASTRING = "sriradhastotram"
SKIP_LINES = 1  # Number of lines to skip at the start of each file

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
    text_fill = (0, 0, 128)
    text_highlight_fill = (255, 255, 255)
    shadow_fill = (0, 0, 0)
    shadow_highlight_fill = (173, 216, 230)

    no_blanks = first_line_title and len(s_chunk) == LINES_PER_SLIDE and all(line.strip() for line in s_chunk)
    for i, line in enumerate(s_chunk):
        # navy blue if highlighted, white otherwise
        fill = text_fill if i == highlight_idx else text_highlight_fill
        # shadow fill while if highlighted, light blue otherwise
        shadow_fill = shadow_fill if i == highlight_idx else shadow_highlight_fill
        
        # draw text shadow
        draw.text((52, MARGIN_TOP_SANSKRIT + i * LINE_SPACING + 2), line, font=font_sanskrit, fill=shadow_fill)
        # is the first line and not highlighted, use blue
        # fill = first_line_fill if i == 0 and i != highlight_idx and no_blanks else fill
        draw.text((50, MARGIN_TOP_SANSKRIT + i * LINE_SPACING), line, font=font_sanskrit, fill=fill)
        
    for i, line in enumerate(t_chunk):
        # navy blue if highlighted, white otherwise
        fill = text_fill if i == highlight_idx else text_highlight_fill
        # shadow fill while if highlighted, light blue otherwise
        shadow_fill = shadow_fill if i == highlight_idx else shadow_highlight_fill
        
        # draw text shadow
        draw.text((52, MARGIN_TOP_TAMIL + i * LINE_SPACING + 2), line, font=font_tamil, fill=shadow_fill)
        # is the first line and not highlighted, use blue
        # fill = first_line_fill if i == 0 and i != highlight_idx and no_blanks else fill
        draw.text((50, MARGIN_TOP_TAMIL + i * LINE_SPACING), line, font=font_tamil, fill=fill)

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
        draw_slide(s_chunk, t_chunk, hl, slide_num, first_line_title=True)
        slide_num += 1

print(f"Done. Slides saved to {HOME}/Downloads/" + ASTRING)
