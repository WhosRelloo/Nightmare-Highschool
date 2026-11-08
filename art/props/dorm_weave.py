"""The dorm room kit's rug (props batch 34, the dorm kit): an original knotted design woven with batch 29's machinery
(weave_textiles.py's Canvas, pile and finish), so it matches the furnishings kit's rugs.

  DormRug  6 x 4: a crimson field of small keys and four-point stars, an ink border with crescents and bats, bone guard
           stripes, the school crest on an ink lozenge in the middle, a little worn down the middle

  python art/props/dorm_weave.py      writes textures/DormRug_{color,normal,rough}.png (2048 x 1365, the 32 px band at the foot)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import weave_textiles as WT  # noqa: E402
import weave_motifs as M  # noqa: E402
from weave_textiles import Canvas, pile, finish, px, crest, star, key_shape, crescent, diamond, lobed, foil, _guard  # noqa: E402


def dorm_rug():
    W, H = px(6, 4)
    cv = Canvas(W, H, "crimson")
    cv.rect(0, 0, W, H, "bone")
    b0, g, bw = 14, 22, 150
    cv.rect(b0, b0, W - b0, H - b0, "ink")
    for (x0, y0, x1, y1) in ((b0, b0, W - b0, b0 + g), (b0, H - b0 - g, W - b0, H - b0)):
        _guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 34)
    for (x0, y0, x1, y1) in ((b0, b0 + g, b0 + g, H - b0 - g), (W - b0 - g, b0 + g, W - b0, H - b0 - g)):
        _guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 34)
    m0, m1 = b0 + g, b0 + g + bw
    # the border: crescents and bats in turn along the ink band
    for horiz, fixed in ((True, m0 + bw / 2), (True, H - m0 - bw / 2), (False, m0 + bw / 2), (False, W - m0 - bw / 2)):
        L = (W - 2 * m1) if horiz else (H - 2 * m1)
        n = max(2, int(L / 170))
        for i in range(n):
            t = m1 + (i + 0.5) * L / n
            x, y = (t, fixed) if horiz else (fixed, t)
            if i % 2 == 0:
                cv.poly(crescent(x, y, 44, tilt=math.pi / 2 if horiz else 0.0, shift=0.45, bite=0.9), "gold")
            else:
                M.bat(cv, x, y, 120, "crimsonlt", "gold", tilt=0.0 if horiz else math.pi / 2)
    for x, y in ((m0, m0), (W - m1, m0), (m0, H - m1), (W - m1, H - m1)):
        cv.rect(x, y, x + bw, y + bw, "crimsondk")
        cv.poly(foil(x + bw / 2, y + bw / 2, 52, 4), "gold")
        cv.circle(x + bw / 2, y + bw / 2, 18, "crimsondk")
    f0 = m1
    cv.rect(f0, f0, W - f0, H - f0, "bone")
    f0 += 12
    cv.rect(f0, f0, W - f0, H - f0, "crimson")
    cx, cy = W / 2, H / 2
    sp = 112
    for i in range(-10, 11):
        for j in range(-7, 8):
            x, y = cx + i * sp, cy + j * sp * 0.82
            if not (f0 + 46 < x < W - f0 - 46 and f0 + 46 < y < H - f0 - 46):
                continue
            if abs(x - cx) / 520 + abs(y - cy) / 330 < 1.08:
                continue
            if (i + j) % 2 == 0:
                key_shape(cv, x, y, 70, "crimsondk", "crimson")
            else:
                cv.poly(star(x, y, 15, 4), "golddk")
    # the medallion: a bone-edged ink lozenge with lobes, the crest in the middle, keys either side
    cv.poly(diamond(cx, cy, 470, 300), "bone")
    cv.poly(diamond(cx, cy, 446, 282), "ink")
    cv.poly(lobed(cx, cy, 250, 220, 12, 0.08), "crimsondk")
    cv.poly(lobed(cx, cy, 232, 204, 12, 0.08), "ink")
    for sx in (-1, 1):
        key_shape(cv, cx + sx * 330, cy, 110, "gold", "ink")
    crest(cv, cx, cy, 330)
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.3, seed=3420)
    finish("DormRug", col, hgt, rough, (2048, 1365 + WT.SW), backing="ink")


if __name__ == "__main__":
    dorm_rug()
