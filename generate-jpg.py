#!/opt/homebrew/opt/python@3.9/libexec/bin/python

from PIL import Image, ImageDraw, ImageFont
import os
import shutil

# CONFIG
FONT_PATH_SANSKRIT = "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc"
FONT_PATH_TAMIL = "/Library/Fonts/NotoSansTamil-Regular.ttf"
FONT_SIZE_SANSKRIT = 55
FONT_SIZE_TAMIL = 45
LINES_PER_SLIDE = 5
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080
LINE_SPACING = 100
MARGIN_TOP_SANSKRIT = 50
MARGIN_TOP_TAMIL = 580
ASTRING = "BKS"

# Load text
with open("/Users/rajaramaniyer/books/srisrianna/laghustotramala/bhaktakolahala_stotram-sanskrit.txt", "r", encoding="utf-8") as f:
    sanskrit_lines = [line.strip() for i, line in enumerate(f) if i >= 14]

with open("/Users/rajaramaniyer/books/srisrianna/laghustotramala/bhaktakolahala_stotram-tamil.txt", "r", encoding="utf-8") as f:
    tamil_lines = [line.strip() for i, line in enumerate(f) if i >= 14]

assert len(sanskrit_lines) == len(tamil_lines), "Line count mismatch."

# Create output folder
if os.path.exists("/Users/rajaramaniyer/Downloads/" + ASTRING):
    shutil.rmtree("/Users/rajaramaniyer/Downloads/" + ASTRING)
os.makedirs("/Users/rajaramaniyer/Downloads/" + ASTRING, exist_ok=True)

# Load fonts
font_sanskrit = ImageFont.truetype(FONT_PATH_SANSKRIT, FONT_SIZE_SANSKRIT)
font_tamil = ImageFont.truetype(FONT_PATH_TAMIL, FONT_SIZE_TAMIL)

def draw_slide(s_chunk, t_chunk, highlight_idx, slide_num, first_line_title=False):
    # Skip slide if the highlighted line is blank in either language
    if not s_chunk[highlight_idx].strip() or not t_chunk[highlight_idx].strip():
        return

    # Load and cache the background image only once
    if not hasattr(draw_slide, "background"):
        draw_slide.background = Image.open("/Users/rajaramaniyer/Downloads/" + ASTRING + "_background.png").convert("RGB").resize((SLIDE_WIDTH, SLIDE_HEIGHT))
    img = draw_slide.background.copy()
    draw = ImageDraw.Draw(img)

    no_blanks = first_line_title and len(s_chunk) == LINES_PER_SLIDE and all(line.strip() for line in s_chunk)
    for i, line in enumerate(s_chunk):
        fill = (255, 0, 0) if i == highlight_idx else (0, 0, 0)
        # is the first line and not highlighted, use blue
        fill = (0, 0, 255) if i == 0 and i != highlight_idx and no_blanks else fill
        draw.text((50, MARGIN_TOP_SANSKRIT + i * LINE_SPACING), line, font=font_sanskrit, fill=fill)

    for i, line in enumerate(t_chunk):
        fill = (255, 0, 0) if i == highlight_idx else (0, 0, 0)
        # is the first line and not highlighted, use blue
        fill = (0, 0, 255) if i == 0 and i != highlight_idx and no_blanks else fill
        draw.text((50, MARGIN_TOP_TAMIL + i * LINE_SPACING), line, font=font_tamil, fill=fill)

    img.save(f"/Users/rajaramaniyer/Downloads/{ASTRING}/{ASTRING}-Slide{slide_num:04d}.png", "PNG")

if os.path.exists("/Users/rajaramaniyer/Downloads/" + ASTRING + "_cover.png"):
    shutil.copy("/Users/rajaramaniyer/Downloads/" + ASTRING + "_cover.png", "/Users/rajaramaniyer/Downloads/" + ASTRING + "/" + ASTRING + "-Slide0001.png")

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

print(f"Done. Slides saved to /Users/rajaramaniyer/Downloads/" + ASTRING)
