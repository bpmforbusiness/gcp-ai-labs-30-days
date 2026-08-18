#!/usr/bin/env python3
"""Day 1 thumbnail: AI artwork + person cutout + crisp PIL text overlay."""
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont
import os

BASE = os.path.expanduser("~/gcp-ai-labs-30-days/01-rag-barista-agent")
ART = os.path.join(BASE, "screenshots/day1_art.png")
FONT = os.path.expanduser("~/youtube_30labs_30days/Anton-Regular.ttf")
OUT = os.path.join(BASE, "screenshots/day1_thumbnail.png")

W, H = 1280, 720

# 1. Background: cover-fit artwork
art = Image.open(ART).convert("RGB")
bg = ImageOps.fit(art, (W, H), Image.LANCZOS)

# Darken left side for text contrast
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(overlay)
d.rectangle([0, 0, 720, H], fill=(0, 0, 20, 120))
d.rectangle([0, 0, 500, H], fill=(0, 0, 25, 80))
img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
dr = ImageDraw.Draw(img)

def draw_text(dr, xy, text, font, fill, outline, width=8):
    x, y = xy
    for dx in range(-width, width + 1, 2):
        for dy in range(-width, width + 1, 2):
            if dx * dx + dy * dy <= width * width:
                dr.text((x + dx, y + dy), text, font=font, fill=outline)
    dr.text((x, y), text, font=font, fill=fill)

# 2. DAY 1/30 badge (top-left)
badge_font = ImageFont.truetype(FONT, 60)
badge_text = "DAY 1 / 30"
bw = dr.textlength(badge_text, font=badge_font)
bx, by = 30, 30
dr.rounded_rectangle([bx, by, bx + bw + 50, by + 84], radius=16, fill=(255, 200, 0, 255))
draw_text(dr, (bx + 25, by + 10), badge_text, badge_font, (0, 0, 0, 255), (255, 255, 255, 255), 4)

# 3. Main headline
main_font = ImageFont.truetype(FONT, 130)
draw_text(dr, (30, 210), "RAG AGENT", main_font, (255, 255, 255, 255), (0, 0, 0, 255), 10)

# 4. Sub line
sub_font = ImageFont.truetype(FONT, 62)
draw_text(dr, (32, 370), "AI COFFEE BARISTA", sub_font, (80, 220, 255, 255), (0, 0, 0, 255), 7)

# 5. Tagline
tag_font = ImageFont.truetype(FONT, 42)
draw_text(dr, (32, 470), "GCP · ADK · CLOUD RUN", tag_font, (255, 190, 80, 255), (0, 0, 0, 255), 5)

# 6. Series line
ser_font = ImageFont.truetype(FONT, 38)
draw_text(dr, (32, 560), "30 LABS IN 30 DAYS", ser_font, (255, 255, 255, 255), (0, 0, 0, 255), 5)

img.save(OUT, quality=95)
print(f"SAVED: {OUT} ({os.path.getsize(OUT)} bytes)")
