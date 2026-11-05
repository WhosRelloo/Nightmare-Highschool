"""PBR "Report Card" phone-app icon for the UI kit (Theme.Images.IconReport), baked to an image.

Like the Seal and the other kit icons it stays GREYSCALE: the shapes are built as a height field, shaded in full PBR
(make_health_pbr.shade: GGX specular, Lambert diffuse, a warm key, a cool fill, a candle rim, an environment reflection,
AO from the height), then reduced to luminance with alpha, and ImageColor3 tints it in game (pale gold on an ink tile).

The design, kept to a few bold shapes so it reads at ~60 px on a phone tile:
  - a stiff report card, tilted a little, with a bevelled edge, an engraved border line and a folded dog-ear corner,
  - a big inked "A+" grade, and three ruled rows of grades under it,
  - a scalloped wax seal stamped over its lower-right corner (the kit Seal's diamond-cross emblem, simplified),
    with two short ribbon tails.

    python make_report_icon.py
Writes art/ui/hud/out/report_icon/IconReport.png (512), IconReport_256.png and preview.png (tinted pale gold on a dark
ink tile at 60 px and 128 px, beside the kit seal and crest for a style check).
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as H

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "report_icon"
OUT.mkdir(parents=True, exist_ok=True)
S = 1024                       # work size; saved at 512 (and 256)
SS = 3                         # supersampling for the vector masks
FONT = Path("C:/Windows/Fonts/georgiab.ttf")

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur_noise(sigma, seed):
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.random((S, S)).astype(np.float32), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def mask(draw_fn):
    """Draw with PIL at SS x and box-filter down: an anti-aliased 0..1 mask."""
    m = Image.new("L", (S * SS, S * SS), 0)
    draw_fn(ImageDraw.Draw(m), SS)
    return np.array(m.resize((S, S), Image.BOX), np.float32) / 255.0


def inner_dist(m):
    """Distance (px) from the edge, inside a soft mask (sub-pixel via the mask's own ramp)."""
    return ndimage.distance_transform_edt(m > 0.5) + (m - 0.5) * (m < 1)


def rotate(a, deg, cx, cy):
    """Rotate a field about (cx, cy), bilinear, without resizing."""
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    # output (x, y) samples input at R^-1 (x - c) + c
    dx, dy = xx - cx, yy - cy
    sx = c * dx + s * dy + cx
    sy = -s * dx + c * dy + cy
    return ndimage.map_coordinates(a, [sy, sx], order=1, mode="constant", cval=0.0).astype(np.float32)


# ======================================================================= the card (drawn upright, then tilted)
CX, CY = 476, 452              # card centre (upright frame)
CW, CH = 560, 720              # card size
EAR = 150                      # dog-ear size at the top-right corner
x0, y0, x1, y1 = CX - CW / 2, CY - CH / 2, CX + CW / 2, CY + CH / 2
TILT = -8.0                    # degrees (counter-clockwise on screen)


def card_shape(d, k):
    p = [(x0, y0), (x1 - EAR, y0), (x1, y0 + EAR), (x1, y1), (x0, y1)]
    d.polygon([(x * k, y * k) for x, y in p], fill=255)


def ear_shape(d, k):
    # the corner folded down over the card: the cut triangle mirrored across its diagonal
    p = [(x1 - EAR, y0), (x1, y0 + EAR), (x1 - EAR, y0 + EAR)]
    d.polygon([(x * k, y * k) for x, y in p], fill=255)


card = mask(card_shape)
ear = mask(ear_shape)

# the engraved border line, inset from the edge (with its own cut corner)
INS = 40


def border_shape(d, k):
    e = EAR + 6
    p = [(x0 + INS, y0 + INS), (x1 - e - INS * 0.4, y0 + INS), (x1 - INS, y0 + e + INS * 0.4),
         (x1 - INS, y1 - INS), (x0 + INS, y1 - INS)]
    d.line([(x * k, y * k) for x, y in p + p[:1]], fill=255, width=int(12 * k), joint="curve")


border = mask(border_shape) * (1 - smooth(0.2, 0.6, ear))

# the grade: a big inked "A+"
font = ImageFont.truetype(str(FONT), int(330 * SS))
font_p = ImageFont.truetype(str(FONT), int(250 * SS))


def grade_shape(d, k):
    ax, ay = x0 + 72, y0 + 66
    d.text((ax * k, ay * k), "A", font=font, fill=255)
    aw = d.textlength("A", font=font) / k
    d.text(((ax + aw - 8) * k, (ay + 30) * k), "+", font=font_p, fill=255)


grade = mask(grade_shape)

# three ruled rows under it: a short label dash and a longer grade line per row
ROWS = [y0 + 470, y0 + 548, y0 + 626]


def rows_shape(d, k):
    for i, ry in enumerate(ROWS):
        w = 15
        d.rounded_rectangle(((x0 + 82) * k, (ry - w) * k, (x0 + 170) * k, (ry + w) * k), radius=w * k, fill=255)
        end = x1 - 90 - (130 if i == 2 else 0)        # the last row stops short of the seal
        d.rounded_rectangle(((x0 + 205) * k, (ry - w) * k, end * k, (ry + w) * k), radius=w * k, fill=255)


rows = mask(rows_shape)
ink = np.clip(grade + rows, 0, 1)

# --- card height (upright frame)
paper_tex = blur_noise(2.0, 41) * 0.012 + blur_noise(14, 42) * 0.02
bow = 0.05 * np.cos((xx - CX) / (CW / 2) * 1.2) + 0.03 * np.cos((yy - CY) / (CH / 2) * 1.2)   # a gentle bow in the board
card_h = card * (0.20 + bow + 0.16 * H.dome(inner_dist(card), 26)) + paper_tex * card
card_h -= border * 0.07                                     # engraved border
ink_d = inner_dist(ink)
card_h += ink * (0.035 + 0.075 * H.dome(ink_d, 7))         # raised, bevelled ink (embossed print)
# the folded flap: lies on top of the card, sloping up toward its fold line, with a soft shadow under it
fold_t = np.clip(((xx - (x1 - EAR)) - (yy - y0)) / EAR, 0, 1)    # 0 at the fold diagonal side .. 1 at the corner
ear_h = ear * (0.40 + 0.08 * H.dome(inner_dist(ear), 10) - 0.06 * fold_t)
ear_shadow = ndimage.gaussian_filter(np.roll(np.roll(ear, 16, 0), -10, 1), 10) * card * (1 - ear)
card_h = np.maximum(card_h, ear_h)
card_alpha = np.clip(card + ear, 0, 1)

# rotate the card layers into place
card_h = rotate(card_h, TILT, CX, CY)
card_alpha = rotate(card_alpha, TILT, CX, CY)
ink = rotate(ink, TILT, CX, CY)
ear = rotate(ear, TILT, CX, CY)
ear_shadow = rotate(ear_shadow, TILT, CX, CY)
border = rotate(border, TILT, CX, CY)

# ======================================================================= the wax seal (lower-right corner)
SX, SY, SR = 730, 724, 172
X = (xx - SX) / SR
Y = (yy - SY) / SR
R = np.hypot(X, Y)
TH = np.arctan2(Y, X)

# ribbon tails hanging from under the seal (V-notched ends)


def ribbon_shape(d, k):
    for ang, ln in ((math.radians(114), 1.42), (math.radians(70), 1.32)):
        ux, uy = math.cos(ang), math.sin(ang)
        px, py = -uy, ux                                  # across
        w = 0.36
        a = (SX, SY)
        b = (SX + ux * SR * ln, SY + uy * SR * ln)
        n = (b[0] - ux * SR * 0.22, b[1] - uy * SR * 0.22)  # the V notch
        poly = [(a[0] + px * SR * w * 0.8, a[1] + py * SR * w * 0.8), (b[0] + px * SR * w, b[1] + py * SR * w), n,
                (b[0] - px * SR * w, b[1] - py * SR * w), (a[0] - px * SR * w * 0.8, a[1] - py * SR * w * 0.8)]
        d.polygon([(x * k, y * k) for x, y in poly], fill=255)


ribbon = mask(ribbon_shape)
rib_d = inner_dist(ribbon)
ribbon_h = ribbon * (0.30 + 0.10 * H.dome(rib_d, 14))
# a centre crease along each tail
for ang in (math.radians(112), math.radians(68)):
    ux, uy = math.cos(ang), math.sin(ang)
    across = np.abs(-(xx - SX) * uy + (yy - SY) * ux)
    ribbon_h -= ribbon * 0.05 * np.exp(-(across / 5) ** 2)

edge = 1.0 + 0.045 * np.cos(12 * TH)                        # scalloped rim (12 lobes)
inside = R / edge
seal = smooth(1.0, 0.975, inside)
to_edge = np.clip(1 - inside, 0, 1)
seal_h = H.dome(np.clip(to_edge * 4, 0, 1), 1.0) * 0.36 + blur_noise(10, 51) * 0.02
seal_h += 0.10 * np.exp(-((to_edge - 0.11) / 0.045) ** 2)    # raised lip where the stamp pushed the wax out
STAMP = 0.70
stamp = smooth(STAMP + 0.02, STAMP - 0.02, R)
seal_h -= 0.10 * stamp
seal_h += 0.09 * np.exp(-((R - (STAMP - 0.08)) / 0.03) ** 2) * stamp     # stamp border ring
diam = np.abs(X) + np.abs(Y)
seal_h += smooth(0.06, 0.025, np.abs(diam - 0.40)) * 0.09 * stamp        # diamond outline
seal_h += H.dome(np.clip((0.22 - diam) / 0.22, 0, 1), 1.0) * 0.10        # raised inner diamond
cross = np.maximum(smooth(0.05, 0.02, np.abs(X)) * smooth(0.56, 0.50, np.abs(Y)),
                   smooth(0.05, 0.02, np.abs(Y)) * smooth(0.56, 0.50, np.abs(X)))
seal_h += cross * smooth(0.40, 0.48, diam) * smooth(STAMP - 0.12, STAMP - 0.16, R) * 0.06   # short cross bars
seal_h = seal_h * seal + 0.42 * seal                                       # sits on top of the card

# ======================================================================= composite
ribbon_top = card_h * card_alpha + ribbon_h * 0.6           # the tails rest on the card (or hang past it)
base = card_h * (1 - ribbon) + ribbon_top * ribbon
height = base * (1 - seal) + seal_h
height = ndimage.gaussian_filter(height, 0.8)
alpha = np.clip(np.maximum(np.maximum(card_alpha, ribbon), seal), 0, 1)

# contact shadows cast on the card by the seal and the ribbons
cast = ndimage.gaussian_filter(np.roll(np.roll(np.maximum(seal, ribbon * 0.8), 10, 0), 6, 1), 9)
cast = cast * (1 - seal) * (1 - ribbon * (1 - seal))

# ======================================================================= materials (greyscale: the kit tints it)
is_ink = ink * (1 - seal) * (1 - ribbon)
is_seal = seal
is_rib = ribbon * (1 - seal)
paper_a = 0.86 * (0.93 + 0.07 * blur_noise(3, 61))
albedo1 = paper_a * (1 - is_ink) + 0.20 * is_ink
albedo1 = albedo1 * (1 - is_rib) + 0.52 * is_rib
albedo1 = albedo1 * (1 - is_seal) + 0.70 * (0.92 + 0.08 * blur_noise(3, 62)) * is_seal
albedo1 *= 1 - 0.07 * border * (1 - seal)
albedo = H.srgb_to_lin(np.dstack([albedo1] * 3).astype(np.float32))
rough = np.clip(0.55 * (1 - is_seal) + 0.2 * is_seal - 0.2 * is_ink + 0.1 * (blur_noise(6, 63) - 0.5), 0.1, 1)
rough = rough * (1 - is_rib) + 0.4 * is_rib
metal = np.zeros((S, S), np.float32)
micro = np.dstack([(blur_noise(1.5, 71) - 0.5), (blur_noise(1.5, 72) - 0.5), np.zeros((S, S))]).astype(np.float32)
N = H.normals_from(height * S * 0.5, 1.0 / 7.5, micro, 0.25)
ao = H.ao_from(height, 10, 5) * H.ao_from(height, 3, 9)
ao *= 1 - 0.8 * cast - 0.45 * ear_shadow * (1 - seal)
rgb = H.shade(albedo, N, rough, metal, ao)
lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.55 + rgb[..., 2] * 0.15
lum = np.clip((lum - 0.04) * 1.25, 0, 1)


def save(img, size, name):
    a = np.dstack([img, img, img, alpha]) * 255
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
    im.save(OUT / name, optimize=True)
    return im


big = save(lum, 512, "IconReport.png")
save(lum, 256, "IconReport_256.png")


# ======================================================================= preview: as the phone tile shows it
GOLD = np.array((232, 214, 168), np.float32) / 255           # pale gold / bone
INKBG = (22, 19, 27, 255)
TILE = (36, 31, 42, 255)


def tinted(im, size, inset=0.14):
    t = np.array(im.convert("RGBA"), np.float32)
    t[..., :3] *= GOLD
    t = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA")
    w, h = t.size
    sc = size * (1 - 2 * inset) / max(w, h)
    return t.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)


def tile(im, size):
    t = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(t).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=TILE,
                                        outline=(70, 60, 70, 255), width=max(1, size // 60))
    ic = tinted(im, size)
    t.alpha_composite(ic, ((size - ic.size[0]) // 2, (size - ic.size[1]) // 2))
    return t


refs = [("IconReport", big)]
for name, p in (("Seal", HERE / "out" / "seal_v2" / "seal.png"), ("Crest", HERE.parent / "kit2" / "out" / "crest.png")):
    if p.exists():
        refs.append((name, Image.open(p)))

COLW = 220
pv = Image.new("RGBA", (COLW * len(refs) + 20, 380), INKBG)
d = ImageDraw.Draw(pv)
for i, (name, im) in enumerate(refs):
    x = 20 + i * COLW
    pv.alpha_composite(tile(im, 128), (x, 20))
    pv.alpha_composite(tile(im, 60), (x, 170))
    d.text((x, 350), name, fill=(200, 190, 170, 255))
# 60 px blown up (nearest) for pixel inspection, beside the strip
zoom = tile(big, 60).resize((180, 180), Image.NEAREST)
pv2 = Image.new("RGBA", (pv.size[0] + 200, pv.size[1]), INKBG)
pv2.alpha_composite(pv, (0, 0))
pv2.alpha_composite(zoom, (pv.size[0], 170))
ImageDraw.Draw(pv2).text((pv.size[0], 350), "60px x3", fill=(200, 190, 170, 255))
pv2.save(OUT / "preview.png")
print("wrote", OUT / "IconReport.png", OUT / "preview.png")
