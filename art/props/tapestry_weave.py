"""Props batch 29's tapestries: each a painted night scene in the art kit's style (paint_canvases.py), the posed and lit
figures from tapestry_renders.py set into it, its effects (bloom on everything that glows, god rays, rising embers,
lightning, mist, holy light), the painterly pass, then woven: ribbed weft-faced wool with hatched tone steps as real
tapestry weaving has, abrash, gilt thread (the metal map), and a woven border of thorned roses with bats in the corners
and a title banner in blackletter.

  TapestryHeadmaster    the Headmaster before the school under a vast moon: a crimson-lined cape and high collar, the
                        great gilt key raised high and blazing, the crescent staff with a ghost-blue orb, a raven on his
                        shoulder, ravens wheeling round the towers ("The Headmaster")
  TapestryPriestDemon   a priest in a holy circle holds up his lantern against a horned demon in a graveyard; the light
                        cuts a cone through the mist and the demon recoils in a swirl of embers ("Lux in Tenebris")
  TapestryAngelDemon    an armoured angel dives from a break in the storm with a burning sword; the demon below raises a
                        trident over a cracked, glowing ground under lightning ("The Last Watch")
  TapestryJudgement     a crowned, radiant sovereign enthroned on clouds, arms spread, a sunburst behind; demons fall
                        into the fiery pit below ("Dies Irae")
  TapestryWolfHunt      a frieze: hunters with lanterns and boar-spears and their hounds run at a werewolf on a crag under
                        a huge moon in a misty pine wood ("The Hunt of the Grey Wolf")
  TapestryCrest         the school's arms: the crest shield supported by two ravens, roses, candles and a crescent moon,
                        on a dark millefleur ground ("Per Noctem ad Lucem")

Writes textures/Tapestry<Name>Weave_{color,normal,rough,metal}.png (with the 32 px swatch band at the foot).

  python art/props/tapestry_weave.py [names...]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint_canvases as PC  # noqa: E402
import weave_textiles as T  # noqa: E402
import weave_motifs as M  # noqa: E402
from weave_dyes import C  # noqa: E402

SRC = os.path.join(HERE, "source_tapestry")
grid, fbm, mix, col, smooth = PC.grid, PC.fbm, PC.mix, PC.col, PC.smooth
poly_mask, lines_mask, ellipse_mask = PC.poly_mask, PC.lines_mask, PC.ellipse_mask

PORTRAIT = (1536, 2048)
FRIEZE = (2048, 1184)
BORDER = 116


def c(name, k=1.0):
    return np.array(C[name], np.float32) / 255 * k


# ------------------------------------------------------------------ effects

def blur(a, s):
    if a.ndim == 3:
        return np.dstack([ndimage.gaussian_filter(a[..., i], s) for i in range(a.shape[2])])
    return ndimage.gaussian_filter(a, s)


def bloom(img, thresh=0.86, sizes=(5, 18, 50), strength=(0.35, 0.22, 0.14)):
    """Everything bright spills light: the over-threshold part blurred at three sizes and added back."""
    lum = img.max(2)
    hot = img * smooth(thresh, 1.0, lum)[..., None]
    out = img.copy()
    for s, k in zip(sizes, strength):
        out += blur(hot, s) * k
    return out


def glow(img, x, y, r, colour, k=1.0):
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    img += colour * (np.exp(-(d / r) ** 2) * k + np.exp(-d / (r * 2.5)) * k * 0.35)[..., None]


def god_rays(img, x, y, colour, k=0.6, length=900, n=40, spread=(0, 2 * math.pi), seed=0, soft=1.0):
    """Shafts of light fanning from (x, y) between the angles in spread (y down), each a different width and strength."""
    h, w, _ = img.shape
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = np.arctan2(yy - y, xx - x)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    a0, a1 = spread
    inside = ((ang - a0) % (2 * math.pi)) <= ((a1 - a0) % (2 * math.pi) or 2 * math.pi)
    rays = np.zeros_like(d)
    for _ in range(n):
        a = a0 + rng.uniform(0, (a1 - a0) % (2 * math.pi) or 2 * math.pi)
        wd = rng.uniform(0.008, 0.035) * soft
        da = np.angle(np.exp(1j * (ang - a)))
        rays += np.exp(-(da / wd) ** 2) * rng.uniform(0.3, 1.0)
    fall = np.exp(-d / length) * smooth(0, 60, d)
    img += colour * (np.clip(rays, 0, 1.6) * fall * inside * k)[..., None]


def light_cone(img, x, y, ang, half, colour, k=0.7, length=900, seed=0):
    """A lantern's beam: a soft cone from (x, y) toward ang (y down), streaked, fading with distance, dust in it."""
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.arctan2(yy - y, xx - x)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    da = np.abs(np.angle(np.exp(1j * (a - ang))))
    cone = smooth(half, half * 0.35, da) * np.exp(-d / length) * smooth(0, 40, d)
    streak = 0.75 + 0.25 * np.sin(a * 140 + seed) * np.sin(a * 57)
    dust = fbm(w, h, 30, 3, seed=seed + 1)
    img += colour * (cone * streak * (0.8 + 0.4 * dust) * k)[..., None]


def embers(img, rng, n, x0, x1, y0, y1, colour=None, size=(1.5, 4.5), rise=(10, 40), k=1.0):
    """Sparks drifting up: bright cores with short trails, then bloom picks them up."""
    h, w, _ = img.shape
    colour = colour if colour is not None else c("ember")
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(*size)
        L = rng.uniform(*rise)
        a = -math.pi / 2 + rng.normal(0, 0.35)
        d.line([(x, y), (x - math.cos(a) * L, y - math.sin(a) * L)], fill=int(rng.uniform(60, 140)), width=max(1, int(r * 0.6)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    m = np.asarray(lay, np.float32) / 255
    img += colour * (m * 1.4 * k)[..., None]


def lightning(img, rng, x0, y0, x1, y1, colour=None, width=4, branches=4, k=1.0):
    """A forked bolt from (x0, y0) to (x1, y1): a jagged core, a wide glow."""
    h, w, _ = img.shape
    colour = colour if colour is not None else col(0.75, 0.82, 1.0)
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)

    def bolt(ax, ay, bx, by, wd, depth):
        pts = [(ax, ay)]
        n = 14
        for i in range(1, n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rng.normal(0, 18 * (1 - abs(t - 0.5))), ay + (by - ay) * t + rng.normal(0, 6)))
        pts.append((bx, by))
        d.line(pts, fill=255, width=max(1, int(wd)), joint="curve")
        if depth > 0:
            for _ in range(branches if depth == 2 else 1):
                i = rng.integers(3, n - 3)
                px, py = pts[i]
                bolt(px, py, px + rng.normal(0, 140), py + rng.uniform(80, 240), wd * 0.55, depth - 1)
    bolt(x0, y0, x1, y1, width, 2)
    m = np.asarray(lay, np.float32) / 255
    img += colour * (m * 1.6 * k + blur(m, 10) * 1.2 * k + blur(m, 40) * 0.8 * k)[..., None]


def mist(img, y0, y1, colour, k=0.6, seed=0, scale=7):
    h, w, _ = img.shape
    x, y = grid(w, h)
    band = smooth(y0, (y0 + y1) / 2, y) * smooth(y1, (y0 + y1) / 2, y)
    n = fbm(w, h, scale, 5, seed=seed)
    img[:] = mix(img, colour, np.clip(band * (0.35 + 0.9 * n) * k, 0, 1))


def stars(img, rng, n, y1=0.6, colour=None):
    h, w, _ = img.shape
    colour = colour if colour is not None else col(0.85, 0.85, 1.0)
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h * y1)
        r = rng.choice([0.8, 1.0, 1.4, 2.2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(80, 255)))
    img += colour * (np.asarray(lay, np.float32) / 255 * 0.7)[..., None]


def silhouette(img, pts, colour, blur_=1.0):
    h, w, _ = img.shape
    img[:] = mix(img, colour, poly_mask(w, h, pts, blur_))


def castle(w, h, x0, x1, base, top, rng, lit=0.4):
    """A gothic castle skyline in unit coords: towers with steep spires, curtain walls with battlements, lit windows.
    Returns (mask, windows)."""
    m = np.zeros((h, w), np.float32)
    win = np.zeros((h, w), np.float32)
    x = x0
    while x < x1:
        tw = rng.uniform(0.05, 0.1)
        th = rng.uniform(0.45, 1.0) * (top - base)
        tx = min(x + tw, x1)
        m = np.maximum(m, poly_mask(w, h, [(x, base), (x, base + th), (tx, base + th), (tx, base)], 0.5))
        if rng.random() < 0.45:
            sh = rng.uniform(0.7, 1.1) * tw * 1.5
            m = np.maximum(m, poly_mask(w, h, [(x - 0.004, base + th), ((x + tx) / 2, base + th + sh), (tx + 0.004, base + th)], 0.5))
        else:
            m = np.maximum(m, poly_mask(w, h, [(x - 0.006, base + th - 0.01), (x - 0.006, base + th), (tx + 0.006, base + th), (tx + 0.006, base + th - 0.01)], 0.4))
            for k in range(4):
                bx = x - 0.006 + (tx - x + 0.012) * (k / 4)
                m = np.maximum(m, poly_mask(w, h, [(bx, base + th), (bx, base + th + 0.014), (bx + (tx - x + 0.012) / 8, base + th + 0.014), (bx + (tx - x + 0.012) / 8, base + th)], 0.4))
        for j in range(int(th / 0.05)):
            if rng.random() < lit:
                wy = base + 0.03 + j * 0.05
                wx = x + (tx - x) * rng.uniform(0.3, 0.7)
                win = np.maximum(win, poly_mask(w, h, [(wx - 0.004, wy), (wx - 0.004, wy + 0.016), (wx, wy + 0.022), (wx + 0.004, wy + 0.016), (wx + 0.004, wy)], 0.4))
        gap = rng.uniform(0.02, 0.08)
        wall_h = rng.uniform(0.18, 0.32) * (top - base)
        m = np.maximum(m, poly_mask(w, h, [(tx, base), (tx, base + wall_h), (tx + gap, base + wall_h), (tx + gap, base)], 0.5))
        for k in range(int(gap / 0.008)):
            bx = tx + k * 0.008
            if k % 2 == 0:
                m = np.maximum(m, poly_mask(w, h, [(bx, base + wall_h), (bx, base + wall_h + 0.008), (bx + 0.004, base + wall_h + 0.008), (bx + 0.004, base + wall_h)], 0.3))
        x = tx + gap
    # y in these masks grows downward from the top: base / top are given as heights from the bottom, so flip
    return m[::-1].copy(), win[::-1].copy()


def flying_ravens(img, rng, n, x0, x1, y0, y1, colour, s=(40, 90)):
    """Ravens wheeling in the sky: wings in mid-beat, long primaries, a wedge tail."""
    h, w, _ = img.shape
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        sz = rng.uniform(*s)
        up = rng.uniform(-0.5, 0.6)
        flip = rng.choice([-1, 1])
        pts = [(0.0, 0.0), (0.18, -0.08 - up * 0.4), (0.42, -0.22 - up), (0.62, -0.18 - up * 1.2), (0.5, -0.1 - up * 0.6), (0.3, -0.02), (0.22, 0.04),
               (0.08, 0.06), (0.06, 0.16), (-0.02, 0.06), (-0.12, 0.04), (-0.22, -0.02), (-0.44, -0.12 - up * 0.8), (-0.6, -0.2 - up), (-0.4, -0.1 - up * 0.5),
               (-0.2, -0.04)]
        d.polygon([(x + flip * u * sz, y + v * sz) for u, v in pts], fill=255)
    m = np.asarray(lay.filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    img[:] = mix(img, colour, m)


def crag(img, pts, colour, rim=None, rim_dir=(1, 0), k=0.5):
    """A rock silhouette with a light edge on one side."""
    h, w, _ = img.shape
    m = poly_mask(w, h, pts, 1.0)
    img[:] = mix(img, colour, m)
    if rim is not None:
        dx, dy = rim_dir
        sh = np.roll(np.roll(m, int(-dx * 6), 1), int(-dy * 6), 0)
        edge = np.clip(m - sh, 0, 1)
        img += rim * (blur(edge, 2) * k)[..., None]


def flames(img, rng, n, x0, x1, base, height, k=1.0):
    """Tongues of fire licking up from base (px): orange bodies, yellow cores."""
    h, w, _ = img.shape
    lay = Image.new("L", (w, h), 0)
    core = Image.new("L", (w, h), 0)
    d, dc = ImageDraw.Draw(lay), ImageDraw.Draw(core)
    for _ in range(n):
        x = rng.uniform(x0, x1)
        hh = rng.uniform(0.3, 1.0) * height
        ww = rng.uniform(0.08, 0.2) * height
        bend = rng.normal(0, ww * 0.6)
        pts = [(x - ww, base), (x - ww * 0.6, base - hh * 0.4), (x + bend, base - hh), (x + ww * 0.6, base - hh * 0.45), (x + ww, base)]
        d.polygon(pts, fill=int(rng.uniform(150, 255)))
        dc.polygon([(x - ww * 0.4, base), (x + bend * 0.5, base - hh * 0.55), (x + ww * 0.4, base)], fill=255)
    m = np.asarray(lay.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    mc = np.asarray(core.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    img[:] = mix(img, c("ember") * 1.1, m * 0.85 * k)
    img += col(1.0, 0.82, 0.4) * (mc * 0.9 * k)[..., None]


def holy_circle(img, cx, cy, rx, ry, colour, k=1.0):
    """A ring of holy light on the ground: two rings, runes between them, a glow."""
    h, w, _ = img.shape
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for r, wd in ((1.0, 5), (0.84, 3)):
        d.ellipse([cx - rx * r, cy - ry * r, cx + rx * r, cy + ry * r], outline=255, width=wd)
    for i in range(24):
        a = i / 24 * 2 * math.pi
        x, y = cx + math.cos(a) * rx * 0.92, cy + math.sin(a) * ry * 0.92
        if i % 3 == 0:
            d.polygon([(x, y - 7), (x + 5, y), (x, y + 7), (x - 5, y)], fill=255)
        else:
            d.line([(x - 4, y - 5), (x + 4, y + 5)], fill=200, width=2)
            d.line([(x + 4, y - 5), (x, y)], fill=200, width=2)
    m = np.asarray(lay, np.float32) / 255
    img += colour * (m * 1.3 * k + blur(m, 8) * 0.9 * k + blur(m, 30) * 0.5 * k)[..., None]


def feathers(img, rng, n, x0, x1, y0, y1, colour):
    h, w, _ = img.shape
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(16, 34)
        pts = T.leaf(x, y, x + math.cos(a) * L, y + math.sin(a) * L, L * 0.32)
        d.polygon(pts, fill=int(rng.uniform(150, 255)))
    img[:] = mix(img, colour, np.asarray(lay.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255)


# ------------------------------------------------------------------ the figures from Blender

def figures(name, w, h):
    """The lit render scaled to the field's width and set on its foot; returns rgb, alpha, gilt mask, glow points (px)."""
    rgba = np.asarray(Image.open(os.path.join(SRC, f"{name}_beauty.png")).convert("RGBA"), np.float32) / 255
    gilt = np.asarray(Image.open(os.path.join(SRC, f"{name}_gilt.png")).convert("L"), np.float32) / 255
    with open(os.path.join(SRC, f"{name}_points.json")) as f:
        pts = json.load(f)
    rh, rw = rgba.shape[:2]
    s = w / rw
    nh = int(round(rh * s))
    im = Image.fromarray((rgba * 255).astype(np.uint8)).resize((w, nh), Image.LANCZOS)
    gm = Image.fromarray((gilt * 255).astype(np.uint8)).resize((w, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gcan = Image.new("L", (w, h), 0)
    oy = h - nh
    canvas.paste(im, (0, oy))
    gcan.paste(gm, (0, oy))
    a = np.asarray(canvas, np.float32) / 255
    pts = {k: [(x * s, y * s + oy) for x, y in v] for k, v in pts.items()}
    g = np.asarray(gcan, np.float32) / 255 * a[..., 3]
    return a[..., :3], a[..., 3], g, pts


def comp(bg, rgb, alpha, shadow=True):
    h, w, _ = bg.shape
    if shadow:
        sh = blur(np.roll(alpha, 14, 0), 10) * 0.6
        bg = bg * (1 - sh[..., None])
    # a cool rim where the figure meets the night, so it lifts off the background as in the paintings
    edge = np.clip(alpha - blur(alpha, 3), 0, 1)
    out = bg * (1 - alpha[..., None]) + rgb * alpha[..., None]
    return out + col(0.25, 0.3, 0.45) * (edge * 0.6)[..., None]


# ------------------------------------------------------------------ the scenes

def sky(w, h, top, bottom, seed, clouds=(0.55, 0.8), cloud_col=None, k=0.7):
    x, y = grid(w, h)
    img = mix(col(*top), col(*bottom), smooth(0.0, 1.0, y))
    cl = fbm(w, h, 4, 6, seed=seed)
    if cloud_col is not None:
        img = mix(img, col(*cloud_col), smooth(*clouds, cl) * k)
    return img, cl


def headmaster(w, h, rng):
    img, cl = sky(w, h, (0.03, 0.03, 0.09), (0.2, 0.16, 0.32), 31, cloud_col=(0.26, 0.22, 0.38))
    x, y = grid(w, h)
    stars(img, rng, 500, 0.55)
    PC.moon(img, w, h, 0.5, 0.22, 0.13, (0.86, 0.84, 0.76), 0.55, halo=2.4)
    img += col(0.3, 0.28, 0.4) * (smooth(0.58, 0.68, cl) * np.exp(-(((x - 0.5) * 1.3) ** 2 + (y - 0.22) ** 2) * 6))[..., None]
    god_rays(img, w * 0.5, h * 0.22, col(0.45, 0.45, 0.6), k=0.14, length=900, n=36, seed=3)
    flying_ravens(img, rng, 11, 0.05 * w, 0.95 * w, 0.06 * h, 0.4 * h, col(0.02, 0.02, 0.04))
    far, _ = castle(w, h, 0.0, 1.0, 0.3, 0.56, np.random.default_rng(5), lit=0.0)
    img = mix(img, col(0.12, 0.1, 0.2), far * 0.9)
    mist(img, 0.62, 0.8, col(0.35, 0.33, 0.48), 0.55, seed=6)
    near, win = castle(w, h, -0.02, 1.02, 0.18, 0.5, np.random.default_rng(8), lit=0.45)
    img = mix(img, col(0.04, 0.035, 0.07), near)
    img += col(1.0, 0.6, 0.25) * (win * near * 1.1 + blur(win * near, 6) * 0.8)[..., None]
    # a stone terrace and its balustrade under his feet
    silhouette(img, [(0, 0.86), (1, 0.86), (1, 1), (0, 1)], col(0.08, 0.07, 0.1))
    for k in range(22):
        bx = k / 21
        silhouette(img, [(bx - 0.008, 0.86), (bx - 0.012, 0.83), (bx, 0.815), (bx + 0.012, 0.83), (bx + 0.008, 0.86)], col(0.1, 0.09, 0.13), 0.5)
    silhouette(img, [(0, 0.805), (1, 0.805), (1, 0.818), (0, 0.818)], col(0.13, 0.12, 0.17))
    mist(img, 0.8, 0.98, col(0.2, 0.18, 0.3), 0.4, seed=7)
    return img


def priest_demon(w, h, rng):
    img, cl = sky(w, h, (0.02, 0.05, 0.07), (0.12, 0.16, 0.2), 41, cloud_col=(0.16, 0.2, 0.24))
    x, y = grid(w, h)
    stars(img, rng, 300, 0.5)
    PC.moon(img, w, h, 0.22, 0.14, 0.08, (0.85, 0.92, 0.95), 0.8, halo=3.0)
    # the demon's side burns: a crimson-orange glow behind it
    img += col(0.55, 0.08, 0.04) * (np.exp(-(((x - 0.8) * 1.6) ** 2 + ((y - 0.62) * 1.2) ** 2) * 3) * 0.9)[..., None]
    # a ruined chapel and bare trees
    ruin = np.maximum(poly_mask(w, h, [(0.38, 0.72), (0.38, 0.5), (0.42, 0.44), (0.46, 0.5), (0.46, 0.72)], 0.6),
                      poly_mask(w, h, [(0.46, 0.72), (0.46, 0.58), (0.58, 0.58), (0.6, 0.62), (0.6, 0.72)], 0.6))
    ruin *= 1 - poly_mask(w, h, [(0.41, 0.62), (0.41, 0.53), (0.42, 0.51), (0.43, 0.53), (0.43, 0.62)], 0.4)
    img = mix(img, col(0.05, 0.06, 0.08), ruin)
    for tx, ln, dr in ((0.06, 0.3, 0.05), (0.95, 0.26, -0.04)):
        segs = []
        PC.tree(segs, tx, 0.86, math.pi / 2 + dr, ln, 30, 8, rng, droop=0.04)
        img = mix(img, col(0.015, 0.02, 0.025), lines_mask(w, h, segs, 0.8))
    mist(img, 0.6, 0.85, col(0.3, 0.36, 0.4), 0.55, seed=8)
    for gx, gh in ((0.12, 0.07), (0.2, 0.05), (0.6, 0.06), (0.7, 0.045), (0.9, 0.065)):
        gy = 0.9
        silhouette(img, [(gx - 0.02, gy), (gx - 0.02, gy - gh), (gx, gy - gh - 0.02), (gx + 0.02, gy - gh), (gx + 0.02, gy)], col(0.05, 0.06, 0.07), 0.6)
    silhouette(img, [(0, 0.88), (0.3, 0.9), (0.7, 0.88), (1, 0.9), (1, 1), (0, 1)], col(0.025, 0.03, 0.035))
    return img


def angel_demon(w, h, rng):
    img, cl = sky(w, h, (0.04, 0.04, 0.08), (0.08, 0.03, 0.05), 51, cloud_col=(0.14, 0.13, 0.2), clouds=(0.45, 0.75), k=0.85)
    x, y = grid(w, h)
    # swirling storm clouds, torn open top-left where the light breaks through
    swirl = fbm(w, h, 3, 6, seed=52)
    img = mix(img, col(0.22, 0.2, 0.3), smooth(0.55, 0.75, swirl) * (1 - y) * 0.8)
    hole = np.exp(-(((x - 0.22) * 1.4) ** 2 + ((y - 0.12) * 1.8) ** 2) * 6)
    img = mix(img, col(0.95, 0.88, 0.7), hole * 0.85)
    god_rays(img, w * 0.22, h * 0.1, col(1.0, 0.9, 0.65), k=0.32, length=1200, n=60, seed=53)
    # the cathedral spire far off, the cracked burning ground the demon stands on
    silhouette(img, [(0.5, 0.82), (0.5, 0.52), (0.52, 0.5), (0.535, 0.34), (0.55, 0.5), (0.57, 0.52), (0.57, 0.82)], col(0.07, 0.05, 0.08), 0.6)
    img += col(0.7, 0.15, 0.04) * (np.exp(-(((x - 0.75) * 1.4) ** 2 + ((y - 0.95) * 2.2) ** 2) * 2.5))[..., None]
    silhouette(img, [(0, 0.86), (0.25, 0.84), (0.55, 0.87), (0.8, 0.83), (1, 0.85), (1, 1), (0, 1)], col(0.03, 0.02, 0.025))
    cracks = []
    for _ in range(9):
        px_, py_ = rng.uniform(0.4, 1.0), rng.uniform(0.88, 0.99)
        for _ in range(5):
            nx_, ny_ = px_ + rng.normal(0, 0.05), py_ + rng.normal(0, 0.012)
            cracks.append((px_, py_, nx_, ny_, rng.uniform(2, 5)))
            px_, py_ = nx_, ny_
    cm = lines_mask(w, h, cracks, 0.6)
    img += c("ember") * (cm * 1.2 + blur(cm, 8) * 0.8)[..., None]
    lightning(img, rng, w * 0.92, 0, w * 0.75, h * 0.55, width=5)
    lightning(img, rng, w * 0.65, 0, w * 0.6, h * 0.3, width=3, branches=2, k=0.6)
    return img


def judgement(w, h, rng):
    x, y = grid(w, h)
    img = mix(col(0.5, 0.34, 0.16), col(0.16, 0.06, 0.04), smooth(0.1, 0.62, y))
    cl = fbm(w, h, 4, 6, seed=61)
    img = mix(img, col(0.8, 0.66, 0.46), smooth(0.5, 0.75, cl) * smooth(0.6, 0.2, y) * 0.7)
    god_rays(img, w * 0.5, h * 0.3, col(1.0, 0.88, 0.55), k=0.3, length=1000, n=60, seed=62)
    # the cloud bank he sits on
    for k in range(9):
        cx_, cy_ = 0.1 + k * 0.1, 0.6 + 0.03 * math.sin(k * 1.7)
        img = mix(img, col(0.6, 0.52, 0.42), ellipse_mask(w, h, cx_, cy_, 0.1, 0.05, 6))
        img = mix(img, col(0.78, 0.7, 0.56), ellipse_mask(w, h, cx_ - 0.02, cy_ - 0.015, 0.06, 0.03, 6) * 0.8)
    # the pit: dark crags framing a fiery chasm
    img = mix(img, col(0.06, 0.02, 0.02), smooth(0.66, 0.74, y))
    img += c("ember", 0.9) * (np.exp(-(((x - 0.5) * 2.2) ** 2 + ((y - 1.0) * 3.0) ** 2) * 2))[..., None]
    flames(img, rng, 70, 0.2 * w, 0.8 * w, h * 1.0, h * 0.18)
    crag(img, [(0, 0.68), (0.12, 0.7), (0.22, 0.78), (0.3, 0.92), (0.26, 1), (0, 1)], col(0.03, 0.015, 0.015), c("ember"), (1, 0), 0.6)
    crag(img, [(1, 0.68), (0.86, 0.71), (0.78, 0.8), (0.72, 0.93), (0.76, 1), (1, 1)], col(0.03, 0.015, 0.015), c("ember"), (-1, 0), 0.6)
    return img


def wolf_hunt(w, h, rng):
    img, cl = sky(w, h, (0.03, 0.04, 0.08), (0.16, 0.2, 0.28), 71, cloud_col=(0.2, 0.24, 0.32))
    x, y = grid(w, h)
    stars(img, rng, 500, 0.5)
    PC.moon(img, w, h, 0.78, 0.3, 0.17, (0.96, 0.94, 0.84), 1.0, halo=2.4)
    for k, (base, colr) in enumerate(((0.55, (0.1, 0.13, 0.18)), (0.66, (0.06, 0.08, 0.11)), (0.78, (0.03, 0.04, 0.06)))):
        pts = [(0, 1)]
        xx = 0.0
        while xx < 1.02:
            hh = rng.uniform(0.05, 0.14) * (1 + k * 0.4)
            pts += [(xx, base), (xx + 0.008, base - hh * 0.4), (xx + 0.014, base - hh), (xx + 0.02, base - hh * 0.4), (xx + 0.028, base)]
            xx += rng.uniform(0.02, 0.04)
        pts.append((1.02, 1))
        silhouette(img, pts, col(*colr), 0.8)
        mist(img, base - 0.05, base + 0.08, col(0.3, 0.34, 0.42), 0.35, seed=72 + k)
    # the crag the werewolf stands on (right), the ground the hunt runs over
    crag(img, [(0.72, 1), (0.74, 0.86), (0.8, 0.8), (0.88, 0.78), (0.94, 0.82), (1, 0.86), (1, 1)], col(0.04, 0.045, 0.06), col(0.4, 0.45, 0.6), (1, -1), 0.7)
    silhouette(img, [(0, 0.92), (0.4, 0.94), (0.75, 0.93), (1, 0.95), (1, 1), (0, 1)], col(0.02, 0.025, 0.035))
    return img


SCENES = {
    "Headmaster": ("The Headmaster", headmaster, PORTRAIT),
    "PriestDemon": ("Lux in Tenebris", priest_demon, PORTRAIT),
    "AngelDemon": ("The Last Watch", angel_demon, PORTRAIT),
    "Judgement": ("Dies Irae", judgement, PORTRAIT),
    "WolfHunt": ("The Hunt of the Grey Wolf", wolf_hunt, FRIEZE),
}


def effects(name, img, pts, w, h, rng):
    """The effects over figures and ground: halos at the glow sources, beams, embers, holy light, then bloom."""
    for x, y in pts.get("lantern", []):
        glow(img, x, y, 60, col(1.0, 0.62, 0.28), 0.9)
    if name == "Headmaster":
        for x, y in pts.get("key", []):
            glow(img, x, y, 70, col(1.0, 0.85, 0.5), 1.0)
            god_rays(img, x, y, col(1.0, 0.86, 0.55), k=0.5, length=420, n=24, seed=11, soft=0.7)
        for x, y in pts.get("orb", []):
            glow(img, x, y, 50, col(0.5, 0.7, 1.0), 1.0)
            embers(img, rng, 60, x - 120, x + 120, y - 160, y + 120, col(0.55, 0.75, 1.0), size=(1, 3), rise=(8, 24))
    if name == "PriestDemon":
        (lx, ly), = pts["lantern"][:1]
        light_cone(img, lx, ly, math.radians(28), 0.3, col(1.0, 0.75, 0.42), k=0.32, length=800, seed=21)
        holy_circle(img, w * 0.27, h * 0.9, w * 0.2, h * 0.03, col(1.0, 0.85, 0.5), 0.9)
        embers(img, rng, 220, w * 0.55, w * 0.98, h * 0.35, h * 0.95)
    if name == "AngelDemon":
        for x, y in pts.get("sword", []):
            glow(img, x, y, 90, col(1.0, 0.8, 0.45), 1.0)
        feathers(img, rng, 26, w * 0.02, w * 0.6, h * 0.1, h * 0.8, col(0.92, 0.88, 0.8))
        embers(img, rng, 260, w * 0.45, w * 1.0, h * 0.45, h * 1.0)
    if name == "Judgement":
        embers(img, rng, 320, w * 0.15, w * 0.85, h * 0.62, h * 1.0, size=(1.5, 5))
        glow(img, w * 0.5, h * 0.3, 160, col(1.0, 0.9, 0.6), 0.12)
    if name == "WolfHunt":
        embers(img, rng, 70, 0, w * 0.6, h * 0.55, h * 0.95, col(0.75, 0.9, 0.5), size=(1, 2.5), rise=(2, 6))     # fireflies
    return bloom(img)


# ------------------------------------------------------------------ border, banner, weave

def border(cv, W, H, B):
    """The woven border: a bone guard with crimson teeth, an ink band with a thorned rose stem all round, a bat on crimson
    in each corner, the crest at the top, a gilt line and a crimson fillet inside."""
    cv.rect(0, 0, W, H, "ink")
    cv.rect(0, 0, W, H, "bone")
    g = 14
    cv.rect(g, g, W - g, H - g, "ink")
    for (x0, y0, x1, y1) in ((g, 0, W - g, g), (g, H - g, W - g, H)):
        T._guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 30)
    for (x0, y0, x1, y1) in ((0, g, g, H - g), (W - g, g, W, H - g)):
        T._guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 30)
    bw = B - g - 16
    m0, m1 = g, g + bw
    for y in (m0, H - m1):
        T._rose_border(cv, m1, y, W - m1, y + bw, bw)
    for x in (m0, W - m1):
        T._rose_border(cv, x, m1, x + bw, H - m1, bw)
    for x, y in ((m0, m0), (W - m1, m0), (m0, H - m1), (W - m1, H - m1)):
        cv.rect(x, y, x + bw, y + bw, "crimsondk")
        cv.poly(T.foil(x + bw / 2, y + bw / 2, bw * 0.48, 4), "crimson", "gold", 3)
        M.bat(cv, x + bw / 2, y + bw / 2 + 4, bw * 0.82, "soot", "gold")
    cv.rect(W / 2 - bw * 0.7, m0, W / 2 + bw * 0.7, m1, "ink")
    T.crest(cv, W / 2, m0 + bw / 2, bw * 1.05)
    cv.rect(m1, m1, W - m1, H - m1, "gold")
    cv.rect(m1 + 8, m1 + 8, W - m1 - 8, H - m1 - 8, "crimsondk")


def banner(cv, cx, cy, wid, text, size):
    """A ribbon across the field with folded, forked ends: crimson, gilt edges, the title in gilt blackletter."""
    hh = size * 1.3
    sag = size * 0.3
    pts_top = [(cx - wid / 2 + t * wid, cy - hh / 2 + sag * (1 - (2 * t - 1) ** 2)) for t in [i / 30 for i in range(31)]]
    pts_bot = [(x, y + hh) for x, y in reversed(pts_top)]
    for sx in (-1, 1):
        ex = cx + sx * wid / 2
        tail = [(ex - sx * 10, cy - hh / 2 + size * 0.35), (ex + sx * size * 1.1, cy - hh / 2 + size * 0.3), (ex + sx * size * 0.7, cy + size * 0.32),
                (ex + sx * size * 1.1, cy + hh / 2 + size * 0.35), (ex - sx * 10, cy + hh / 2 + size * 0.4)]
        cv.poly(tail, "crimsondk", "gold", 4)
    cv.poly(pts_top + pts_bot, "crimson", "gold", 5)
    inner = [(x, y + 9) for x, y in pts_top] + [(x, y - 9) for x, y in pts_bot]
    cv.line(inner[:31], "golddk", 2)
    cv.line(inner[31:], "golddk", 2)
    cv.text((cx, cy + sag * 0.75 + hh * 0.02), text, size * 0.82, "gold")


def tapestry_weave(img, gilt, seed=0):
    """Weave a painted image: horizontal ribs of weft over the warp, tone stepped with hatched teeth along the ribs,
    dye-lot abrash, gilt thread where gilt is (returns colour, height, roughness, metal)."""
    h, w, _ = img.shape
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    P = 6.0
    row = np.floor(yy / P)
    rib = np.sin(np.pi * (yy % P) / P) ** 0.6
    bead = 0.5 + 0.5 * np.cos(2 * np.pi * (xx + (row % 2) * 2) / 4)
    hgt = rib * (0.72 + 0.28 * bead)
    # hatching: luminance stepped into levels, the boundary between two steps interlocking in teeth along each rib
    L = img.mean(2) + 1e-4
    q = 18.0
    s = np.clip(L, 0, 1.4) * q
    phase = rng.uniform(0, 1, int(h / P) + 2).astype(np.float32)[row.astype(int)]
    tooth = np.abs(((xx / 11.0 + phase) % 1.0) * 2 - 1)
    Lq = (np.floor(s) + ((s % 1.0) > tooth)) / q
    img = img * np.clip(Lq / L, 0.55, 1.7)[..., None]
    # dye lots along the rows, a little irregularity in each thread
    ab = 1 + 0.035 * (T.pnoise(int(h / P) + 2, 1, 3, seed + 1)[row.astype(int), 0] - 0.5) * 2
    img = img * ab[..., None] * (1 + rng.normal(0, 0.02, (h, w, 1)).astype(np.float32))
    img = img * (0.8 + 0.3 * hgt[..., None])
    # gilt thread: gold, glinting on each bead
    g = np.clip(gilt, 0, 1)
    lum = img.mean(2, keepdims=True)
    gold = c("gold") * (0.35 + 1.4 * lum) * (0.8 + 0.3 * hgt[..., None]) * (1 + 0.2 * bead[..., None])
    img = mix(img, gold, g * 0.7)
    metal = g * (0.8 + 0.2 * bead)
    rough = 0.88 - 0.5 * g + 0.04 * (bead - 0.5)
    # age: a touch faded and warm, darker toward the edges
    x, y = grid(w, h)
    grey = img.mean(2, keepdims=True)
    img = img * 0.9 + grey * 0.1
    img = img * col(1.0, 0.95, 0.86) ** 0.4
    vig = 1 - 0.22 * (((x - 0.5) * 2) ** 2 + ((y - 0.5) * 2) ** 2) ** 1.4
    img = img * np.clip(vig, 0.6, 1)[..., None]
    return np.clip(img, 0, 1), hgt, rough, metal


def gilt_of(arr):
    """Gilt mask of a drawn design: pixels near the gold dyes."""
    g = np.array(C["gold"], np.float32) / 255
    d = np.sqrt(((arr - g) ** 2).sum(2))
    return smooth(0.12, 0.04, d)


def make(name):
    rng = np.random.default_rng(abs(hash(name)) % 2 ** 31)
    title, painter, size = SCENES[name]
    W, H = size
    Hd = H - T.SW
    B = BORDER
    fw, fh = W - 2 * B, Hd - 2 * B
    bg = painter(fw, fh, rng)
    rgb, alpha, gmask, pts = figures(name, fw, fh)
    img = comp(bg, rgb, alpha)
    img = effects(name, img, pts, fw, fh, rng)
    img, _ = PC.paint(np.clip(img, 0, 1), rng, int(fw * fh / 40), (4, 12), (2, 4), jitter=0.03)
    # the border and the banner, drawn crisp on the full map
    cv = T.Canvas(W, Hd, "ink")
    border(cv, W, Hd, B)
    full = cv.array()
    full[B:B + fh, B:B + fw] = img
    gilt = gilt_of(full)
    gilt[B:B + fh, B:B + fw] = gmask
    bcv = T.Canvas(W, Hd, (0, 0, 0))
    bsize = 70 if size == PORTRAIT else 64
    banner(bcv, W / 2, Hd - B - bsize * 0.9, fw * (0.62 if size == PORTRAIT else 0.5), title, bsize)
    band_rgb = bcv.array()
    band_m = (band_rgb.max(2) > 0.02).astype(np.float32)
    band_m = np.asarray(Image.fromarray((band_m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    full = mix(full, band_rgb, band_m)
    gilt = np.maximum(gilt, gilt_of(band_rgb) * band_m)
    col_, hgt, rough, metal = tapestry_weave(full, gilt, seed=len(name))
    T.finish(f"Tapestry{name}Weave", col_, hgt, rough, (W, H), fringe="gold", backing="ink", strength=4.0, metal=metal)


def crest_tapestry():
    """The school's arms (drawn, no render): the crest held by two displayed ravens, roses, candles, a crescent, on a
    dark millefleur ground; then the same weave."""
    name = "Crest"
    W, H = PORTRAIT
    Hd = H - T.SW
    B = BORDER
    fw, fh = W - 2 * B, Hd - 2 * B
    rng = np.random.default_rng(81)
    # the painted ground: deep crimson velvet darkening to the corners, candle-glow
    x, y = grid(fw, fh)
    img = mix(col(0.2, 0.025, 0.04), col(0.05, 0.01, 0.02), np.clip(np.sqrt((x - 0.5) ** 2 + (y - 0.45) ** 2) * 1.6, 0, 1))
    # the millefleur, drawn
    cv = T.Canvas(fw, fh, (0, 0, 0))
    for _ in range(140):
        fx, fy = rng.uniform(0, fw), rng.uniform(0, fh)
        cc = ["crimsonlt", "bone", "gold", "rose"][rng.integers(0, 4)]
        cv.line([(fx, fy + 34), (fx, fy)], "mossdk", 6)
        cv.poly(T.leaf(fx, fy + 26, fx - 26, fy + 8, 12), "moss")
        cv.poly(T.leaf(fx, fy + 26, fx + 26, fy + 12, 12), "moss")
        cv.poly(T.foil(fx, fy - 6, 18, 5, k=0.5), cc)
        cv.circle(fx, fy - 6, 5, "gold")
    fl = cv.array()
    flm = (fl.max(2) > 0.02).astype(np.float32)
    img = mix(img, fl * 0.75, flm[..., None] * 0.8)
    # the arms on top
    cv2 = T.Canvas(fw, fh, (0, 0, 0))
    cxp, cyp = fw / 2, fh * 0.46
    cv2.poly(T.crescent(cxp, fh * 0.13, 110, tilt=math.pi / 2, shift=0.42), "bone")
    for sx in (-1, 1):
        M.raven(cv2, cxp + sx * 330, cyp + 30, 430, "soot", "gold", "inklt")
        M.candle(cv2, cxp + sx * 520, fh * 0.86, 44, 220, "bone", "amber", "holy", "golddk")
        M.rose_spray(cv2, [(cxp + sx * (120 + i * 12), fh * 0.82 - math.sin(i / 6) * 40) for i in range(40)], 10, "mossdk", "crimson", "crimsondk", "rose",
                     "moss", "mossdk", every=12, r=34)
    T.crest(cv2, cxp, cyp, 620)
    arms = cv2.array()
    am = (arms.max(2) > 0.02).astype(np.float32)
    am = np.asarray(Image.fromarray((am * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    sh = blur(np.roll(am, 12, 0), 10) * 0.55
    img = img * (1 - sh[..., None])
    img = mix(img, arms, am)
    for sx in (-1, 1):
        glow(img, cxp + sx * 520, fh * 0.86 - 270, 50, col(1.0, 0.65, 0.3), 0.9)
    glow(img, cxp, fh * 0.13, 120, col(0.8, 0.8, 0.9), 0.35)
    gm = gilt_of(arms) * am
    img = bloom(img)
    img, _ = PC.paint(np.clip(img, 0, 1), rng, int(fw * fh / 40), (4, 12), (2, 4), jitter=0.03)
    cvb = T.Canvas(W, Hd, "ink")
    border(cvb, W, Hd, B)
    full = cvb.array()
    full[B:B + fh, B:B + fw] = img
    gilt = gilt_of(full)
    gilt[B:B + fh, B:B + fw] = gm
    bcv = T.Canvas(W, Hd, (0, 0, 0))
    banner(bcv, W / 2, Hd - B - 64, fw * 0.66, "Per Noctem ad Lucem", 62)
    band_rgb = bcv.array()
    band_m = (band_rgb.max(2) > 0.02).astype(np.float32)
    full = mix(full, band_rgb, band_m)
    gilt = np.maximum(gilt, gilt_of(band_rgb) * band_m)
    col_, hgt, rough, metal = tapestry_weave(full, gilt, seed=99)
    T.finish("TapestryCrestWeave", col_, hgt, rough, (W, H), fringe="gold", backing="ink", strength=4.0, metal=metal)


JOBS = {n: (lambda n=n: make(n)) for n in SCENES}
JOBS["Crest"] = crest_tapestry

if __name__ == "__main__":
    for n in sys.argv[1:] or list(JOBS):
        JOBS[n]()
