#!/usr/bin/env python3
"""Generate compelling Twitter Card for agentcheck.site"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

W, H = 1200, 630
OUT_TW = "/root/agentready/frontend/public/twitter-card.png"
OUT_OG = "/root/agentready/frontend/public/og-image.png"

# Colors - dark dramatic palette for X timeline impact
BG_DARK = (10, 20, 22)           # near black with teal tint
TEAL = (13, 180, 185)            # vibrant teal
TEAL_DIM = (13, 115, 119)        # original brand teal
TEAL_GLOW = (20, 200, 205)       # bright teal for accents
WHITE = (255, 255, 255)
OFF_WHITE = (220, 225, 226)
GRAY = (140, 150, 155)
RED_ACCENT = (239, 68, 68)       # subtle red for "competitors"

def load_font(size, bold=False):
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

font_hook_large = load_font(52, bold=True)
font_hook_small = load_font(48, bold=True)
font_sub = load_font(28, bold=False)
font_cta = load_font(26, bold=True)
font_brand = load_font(32, bold=True)
font_brand_sub = load_font(18, bold=False)
font_score = load_font(54, bold=True)
font_grade = load_font(20, bold=True)
font_label = load_font(14, bold=True)

img = Image.new("RGB", (W, H), BG_DARK)
draw = ImageDraw.Draw(img, "RGBA")

# ── Subtle background grid ───────────────────────────────────────────────────
for x in range(0, W, 32):
    for y in range(0, H, 32):
        draw.ellipse([x, y, x+1, y+1], fill=(30, 45, 48))

# ── Decorative glow in top-right ─────────────────────────────────────────────
for r in range(200, 0, -2):
    alpha = max(0, int(8 * (1 - r / 200)))
    draw.ellipse(
        [W - 150 - r, -100 - r, W - 150 + r, -100 + r],
        fill=(13, 115, 119, alpha)
    )

# ── Teal top accent line ─────────────────────────────────────────────────────
draw.rectangle([0, 0, W, 4], fill=TEAL)

# ── Left content area ────────────────────────────────────────────────────────
lx = 70
ly = 80

# Hook line 1: "Right now, AI is recommending"
line1 = "Right now, AI is recommending"
draw.text((lx, ly), line1, font=font_hook_large, fill=OFF_WHITE)

# Hook line 2: "your competitors." in teal/red for emphasis
line2_y = ly + 68
draw.text((lx, line2_y), "your competitors.", font=font_hook_large, fill=TEAL_GLOW)

# Teal underline accent under "your competitors"
comp_bb = draw.textbbox((lx, line2_y), "your competitors.", font=font_hook_large)
comp_w = comp_bb[2] - comp_bb[0]
draw.rectangle([lx, line2_y + 62, lx + comp_w, line2_y + 66], fill=TEAL)

# Subtitle
sub_y = line2_y + 95
draw.text((lx, sub_y), "Is your website visible to AI agents?", font=font_sub, fill=GRAY)

# CTA pill
cta_y = sub_y + 65
cta_text = "Free scan  -  30 seconds  -  No signup"
cta_bb = draw.textbbox((0, 0), cta_text, font=font_cta)
cta_w = cta_bb[2] - cta_bb[0]
cta_h = cta_bb[3] - cta_bb[1]
pad_x, pad_y = 24, 14
draw.rounded_rectangle(
    [lx, cta_y, lx + cta_w + pad_x * 2, cta_y + cta_h + pad_y * 2],
    radius=8, fill=TEAL_DIM
)
draw.text((lx + pad_x, cta_y + pad_y), cta_text, font=font_cta, fill=WHITE)

# ── Right side: Score circle ─────────────────────────────────────────────────
cx_c = W - 200
cy_c = 280
R_outer = 105
R_inner = 88

# Glow rings
for r_off, a in [(R_outer + 30, 6), (R_outer + 18, 14), (R_outer + 8, 28)]:
    draw.ellipse(
        [cx_c - r_off, cy_c - r_off, cx_c + r_off, cy_c + r_off],
        outline=(*TEAL_DIM, a), width=2
    )

# Dark circle base
draw.ellipse(
    [cx_c - R_outer, cy_c - R_outer, cx_c + R_outer, cy_c + R_outer],
    fill=(20, 35, 38), outline=(*TEAL_DIM, 80), width=2
)

# Arc progress (87% = ~313 degrees)
arc_bbox = [cx_c - R_outer + 8, cy_c - R_outer + 8,
            cx_c + R_outer - 8, cy_c + R_outer - 8]
draw.arc(arc_bbox, start=-90, end=223, fill=TEAL, width=10)

# Score "87"
score_text = "87"
sb = draw.textbbox((0, 0), score_text, font=font_score)
sw, sh = sb[2] - sb[0], sb[3] - sb[1]
draw.text((cx_c - sw // 2, cy_c - sh // 2 - 10), score_text, font=font_score, fill=WHITE)

# "/100" below
grade = "/100"
gb = draw.textbbox((0, 0), grade, font=font_grade)
gw = gb[2] - gb[0]
draw.text((cx_c - gw // 2, cy_c + sh // 2 - 6), grade, font=font_grade, fill=GRAY)

# Label above circle
label = "AI VISIBILITY"
lb = draw.textbbox((0, 0), label, font=font_label)
lw = lb[2] - lb[0]
draw.text((cx_c - lw // 2, cy_c - R_outer - 24), label, font=font_label, fill=TEAL)

# ── Bottom bar ────────────────────────────────────────────────────────────────
bar_y = H - 72
draw.rectangle([0, bar_y, W, H], fill=(15, 28, 30))
draw.line([(0, bar_y), (W, bar_y)], fill=(*TEAL_DIM, 60), width=1)

# Brand name left
draw.text((70, bar_y + 20), "AgentCheck", font=font_brand, fill=WHITE)

# URL right
url = "agentcheck.site"
ub = draw.textbbox((0, 0), url, font=font_brand_sub)
uw = ub[2] - ub[0]
draw.text((W - 70 - uw, bar_y + 28), url, font=font_brand_sub, fill=TEAL)

# ── Save both twitter and OG ─────────────────────────────────────────────────
img.save(OUT_TW, "PNG", optimize=True)
print(f"Twitter card saved: {OUT_TW}")
print(f"Size: {os.path.getsize(OUT_TW):,} bytes")

img.save(OUT_OG, "PNG", optimize=True)
print(f"OG image saved: {OUT_OG}")
print(f"Size: {os.path.getsize(OUT_OG):,} bytes")

# Verify
verify = Image.open(OUT_TW)
print(f"Dimensions: {verify.size[0]}x{verify.size[1]}")
print("OK")
