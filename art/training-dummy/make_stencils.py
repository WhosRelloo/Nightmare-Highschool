"""Nightmare Highschool training dummy: the spray-stencil mask for the back of the Torso.

Run with any Python that has Pillow:  python make_stencils.py
Writes src/stencil_back.png (white = paint). It covers the Torso's whole back face: u = x in [-1, 1] studs,
v = z in [-1, 1] studs, 500 px per stud, seen from behind (Blender front view). build_training_dummy.py reads it.
The marks are fictional: the game's own school, no real brands.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 500                     # pixels per stud
W = H = 2 * PX
FONT = "C:/Windows/Fonts/impact.ttf"


def px(u, v):
    return (u + 1) * PX, (1 - v) * PX


def text_box(draw, text, cu, cv, height, max_w=None):
    """draw text centred at (cu, cv) studs with cap height ~height studs"""
    size = int(height * PX * 1.32)
    font = ImageFont.truetype(FONT, size)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    tw, th = r - l, b - t
    if max_w and tw > max_w * PX:
        size = int(size * max_w * PX / tw)
        font = ImageFont.truetype(FONT, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        tw, th = r - l, b - t
    x, y = px(cu, cv)
    draw.text((x - tw / 2 - l, y - th / 2 - t), text, font=font, fill=255)
    return (x - tw / 2, y - th / 2, x + tw / 2, y + th / 2)


def stencil_bridges(img, boxes, every):
    """cut thin vertical gaps through big letters, the way a cut stencil leaves bridges"""
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in boxes:
        x = x0 + every * 0.55
        while x < x1:
            d.rectangle([x - 4, y0 + (y1 - y0) * 0.42, x + 4, y0 + (y1 - y0) * 0.58], fill=0)
            x += every


def main():
    os.makedirs(os.path.join(HERE, "src"), exist_ok=True)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    # between the belts (belts sit at z 0.38..0.60 and -0.62..-0.40)
    big = text_box(d, "N.H.", 0.0, 0.07, 0.34, max_w=1.45)
    text_box(d, "BOXING CLUB", 0.0, -0.25, 0.1, max_w=1.3)
    # under the lower belt, small
    text_box(d, "PROPERTY OF NIGHTMARE HIGH ATHLETICS", 0.0, -0.76, 0.055, max_w=1.5)
    # above the upper belt: a bag number
    text_box(d, "No. 3", 0.0, 0.75, 0.09, max_w=0.6)
    # (stencil_bridges is available but the cut gaps read as glitches at game distance)
    img = img.filter(ImageFilter.GaussianBlur(1.6))      # soft spray edge
    img.save(os.path.join(HERE, "src", "stencil_back.png"))
    print("wrote src/stencil_back.png")


if __name__ == "__main__":
    main()
