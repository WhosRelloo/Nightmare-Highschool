"""Nightmare Highschool shift-lock cursor (Pillow). usage: python make_cursor.py <out.png>

A dark, wrought-iron design to match the academy gate:
  - a black iron ring with a fine bevel highlight, and a faint crimson glow ring inside it
  - 12 tiny candle-gold hour ticks (like the clock seal)
  - at 12 / 3 / 6 / 9, small iron spear-point finials (like the fence tops), each tipped in gold
  - a deep crimson diamond in the centre with a dark rim and a tiny gold pin
  - a soft dark halo under everything so it reads on bright scenes too
Drawn on a 64-unit grid at 8x and downsampled to OUT x OUT (44 by default: shift-lock cursors draw at their pixel size).
"""
import math
import sys

from PIL import Image, ImageDraw, ImageFilter

S = 8
N = 64 * S
c = N / 2
IRON = (24, 22, 28, 255)
IRON_HI = (92, 86, 100, 255)
GOLD = (226, 192, 110, 255)
GOLD_DEEP = (130, 96, 44, 255)
CRIMSON = (170, 18, 34, 255)
CRIMSON_HOT = (235, 60, 72, 255)
INK = (6, 4, 8, 255)


def P(r, deg):
    a = math.radians(deg - 90)  # 0 deg = up
    return (c + math.cos(a) * r * S, c + math.sin(a) * r * S)


def finial(d, deg, inner, outer, width, fill, tip=None):
    # a spear point: a thin shaft and a diamond head pointing outward
    a0 = P(inner, deg)
    a1 = P(outer - 3.2, deg)
    d.line([a0, a1], fill=fill, width=int(width * S))
    head_base_l = P(outer - 3.2, deg - 9)
    head_base_r = P(outer - 3.2, deg + 9)
    head_mid = P(outer - 4.6, deg)
    head_tip = P(outer, deg)
    d.polygon([head_mid, head_base_l, head_tip, head_base_r], fill=fill)
    if tip:
        d.polygon([P(outer - 1.4, deg - 4), P(outer, deg), P(outer - 1.4, deg + 4), P(outer - 2.2, deg)], fill=tip)


img = Image.new("RGBA", (N, N), (0, 0, 0, 0))

# soft dark halo for contrast on bright backgrounds
halo = Image.new("RGBA", (N, N), (0, 0, 0, 0))
h = ImageDraw.Draw(halo)
h.ellipse([c - 19 * S, c - 19 * S, c + 19 * S, c + 19 * S], outline=(0, 0, 0, 150), width=9 * S)
h.ellipse([c - 7 * S, c - 7 * S, c + 7 * S, c + 7 * S], fill=(0, 0, 0, 140))
for deg in (0, 90, 180, 270):
    finial(h, deg, 18, 27, 4, (0, 0, 0, 150))
halo = halo.filter(ImageFilter.GaussianBlur(2.5 * S))
img.alpha_composite(halo)

# faint crimson glow ring inside the iron
glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
g = ImageDraw.Draw(glow)
g.ellipse([c - 13 * S, c - 13 * S, c + 13 * S, c + 13 * S], outline=(200, 24, 44, 150), width=int(1.6 * S))
glow = glow.filter(ImageFilter.GaussianBlur(1.2 * S))
img.alpha_composite(glow)

d = ImageDraw.Draw(img)
# iron ring: dark body, dark outline, thin bevel highlight on the upper-left
R = 16.5
d.ellipse([c - (R + 1.6) * S, c - (R + 1.6) * S, c + (R + 1.6) * S, c + (R + 1.6) * S], outline=INK, width=int(4.4 * S))
d.ellipse([c - R * S - 0.6 * S, c - R * S - 0.6 * S, c + R * S + 0.6 * S, c + R * S + 0.6 * S], outline=IRON, width=int(2.6 * S))
d.arc([c - (R + 0.4) * S, c - (R + 0.4) * S, c + (R + 0.4) * S, c + (R + 0.4) * S], 200, 290, fill=IRON_HI, width=int(0.7 * S))
# thin crimson line just inside
d.ellipse([c - 13 * S, c - 13 * S, c + 13 * S, c + 13 * S], outline=CRIMSON, width=int(0.8 * S))

# 12 hour ticks on the ring (gold), the quarter ones longer
for i in range(12):
    deg = i * 30
    if deg % 90 == 0:
        continue
    d.line([P(14.6, deg), P(18.2, deg)], fill=GOLD_DEEP, width=int(1.4 * S))
    d.line([P(15.0, deg), P(17.8, deg)], fill=GOLD, width=int(0.8 * S))

# spear-point finials at the quarters: iron with a gold tip
for deg in (0, 90, 180, 270):
    finial(d, deg, 17.5, 27, 2.6, INK)
    finial(d, deg, 17.8, 26.4, 1.5, IRON, tip=GOLD)

# centre: dark rim, crimson diamond, a hot facet and a tiny gold pin
def diamond(r, fill):
    d.polygon([(c, c - r * S), (c + r * S, c), (c, c + r * S), (c - r * S, c)], fill=fill)


diamond(6.2, INK)
diamond(5.0, CRIMSON)
d.polygon([(c, c - 5.0 * S), (c + 5.0 * S, c), (c, c)], fill=CRIMSON_HOT)  # lit upper-right facet
diamond(1.3, GOLD)

OUT = int(sys.argv[2]) if len(sys.argv) > 2 else 44
img.resize((OUT, OUT), Image.Resampling.LANCZOS).save(sys.argv[1] if len(sys.argv) > 1 else "nh_shiftlock.png")
print("saved")
