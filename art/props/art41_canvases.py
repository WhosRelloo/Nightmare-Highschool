"""Props batch 41's paintings (the art kit), in the style of paint_canvases.py: each scene painted procedurally, the
figures (posed on the owner's R6 rig and lit in Blender by art41_renders.py) set in, the effects (candle and torch
glow, bloom, mist, snow), then the painterly brush pass, and an old master's finish: amber varnish yellowed unevenly,
a craquelure of fine cracks in two sizes, a vignette. Also the drawn pieces (the clique heraldry, the stained-glass
roundel, the mosaic) and the two tapestries, woven with tapestry_weave.py's weave and border.

Writes art/props/textures/<Name>_canvas.png (and Tapestry<Name>Weave_* for the tapestries).
  python art/props/art41_canvases.py [names...]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint_canvases as PC  # noqa: E402
import tapestry_weave as TW  # noqa: E402
import weave_textiles as T  # noqa: E402
import weave_motifs as MO  # noqa: E402
import art41_layout as L  # noqa: E402

OUT = os.path.join(HERE, "textures")
SRC = os.path.join(HERE, "source_art41")
grid, fbm, mix, col, smooth = PC.grid, PC.fbm, PC.mix, PC.col, PC.smooth
poly_mask, lines_mask, ellipse_mask = PC.poly_mask, PC.lines_mask, PC.ellipse_mask
blur, bloom, glow, mist, stars = TW.blur, TW.bloom, TW.glow, TW.mist, TW.stars
SERIF = "C:/Windows/Fonts/palab.ttf"
BLACK = "C:/Windows/Fonts/gothice_.ttf"


# ------------------------------------------------------------------ figures

def figs(name, w, h, fit="stretch", x=0.5, y=1.0, height=None):
    """The render as (rgb, alpha, gilt, ghost, points px). stretch: the render's field is the canvas. Otherwise scaled to
    `height` (of the canvas) and placed with its foot centre at (x, y)."""
    rgba = np.asarray(Image.open(os.path.join(SRC, f"{name}_beauty.png")).convert("RGBA"), np.float32) / 255
    gl = np.asarray(Image.open(os.path.join(SRC, f"{name}_gilt.png")).convert("L"), np.float32) / 255
    gh = np.asarray(Image.open(os.path.join(SRC, f"{name}_ghost.png")).convert("L"), np.float32) / 255
    with open(os.path.join(SRC, f"{name}_points.json")) as f:
        pts = json.load(f)
    rh, rw = rgba.shape[:2]
    if fit == "stretch":
        nw, nh, ox, oy = w, h, 0, 0
    else:
        nh = int(h * (height or 1.0))
        nw = int(rw * nh / rh)
        ox, oy = int(x * w - nw / 2), int(y * h - nh)
    sx, sy = nw / rw, nh / rh

    def place(a, mode):
        im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), mode).resize((nw, nh), Image.LANCZOS)
        can = Image.new(mode, (w, h), 0 if mode == "L" else (0, 0, 0, 0))
        can.paste(im, (ox, oy))
        return np.asarray(can, np.float32) / 255
    a = place(rgba, "RGBA")
    g = place(gl, "L") * a[..., 3]
    hst = place(gh, "L") * a[..., 3]
    pts = {k: [(px * sx + ox, py * sy + oy) for px, py in v] for k, v in pts.items()}
    return a[..., :3], a[..., 3], g, hst, pts


def set_in(bg, F, rim=(0.25, 0.3, 0.45), ghost_k=0.62, shadow=True, gain=1.3):
    rgb, alpha, _, ghost, _ = F
    rgb = np.clip(rgb * gain, 0, 1.2)
    out = TW.comp(bg, rgb, alpha, shadow=shadow)
    if rim != (0.25, 0.3, 0.45):
        edge = np.clip(alpha - blur(alpha, 3), 0, 1)
        out = out + (col(*rim) - col(0.25, 0.3, 0.45)) * (edge * 0.6)[..., None]
    if ghost.max() > 0:
        pale = bg * 0.55 + col(0.55, 0.68, 0.85) * 0.55 * rgb.mean(2, keepdims=True)
        out = mix(out, pale + col(0.05, 0.08, 0.14), ghost * ghost_k)
        out = out + col(0.25, 0.4, 0.6) * (blur(ghost, 14) * 0.35)[..., None]
    return out


def glows(img, pts, kinds, r, colour, k=1.0):
    for kind in kinds:
        for x, y in pts.get(kind, []):
            glow(img, x, y, r, col(*colour), k)


# ------------------------------------------------------------------ the old master's finish

def craquelure(w, h, seed, cell=42, warp=0.012):
    """A crack network: the edges between irregular cells (jittered Voronoi, warped by noise), 1 on a crack."""
    rng = np.random.default_rng(seed)
    n = int(w * h / cell ** 2)
    pts = rng.random((n, 2)) * [w, h]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wx = (fbm(w, h, 6, 3, seed=seed + 1) - 0.5) * w * warp * 4
    wy = (fbm(w, h, 6, 3, seed=seed + 2) - 0.5) * w * warp * 4
    q = np.stack([(xx + wx).ravel(), (yy + wy).ravel()], 1)
    d, _ = cKDTree(pts).query(q, k=2, workers=-1)
    e = (d[:, 1] - d[:, 0]).reshape(h, w)
    return smooth(2.2, 0.4, e)


def finish(img, seed=3, crack=1.0, amber=1.0, vig=0.36):
    h, w, _ = img.shape
    x, y = grid(w, h)
    v = 1 - vig * (((x - 0.5) * 2) ** 2 + ((y - 0.5) * 2) ** 2) ** 1.2
    img = img * np.clip(v, 0.4, 1)[..., None]
    yel = fbm(w, h, 3, 4, seed=seed + 5)
    tint = mix(np.ones(3, np.float32), col(1.0, 0.86, 0.6), (0.12 + 0.2 * yel) * amber)
    img = img * tint
    if crack > 0:
        big = craquelure(w, h, seed, cell=46 * w / 2048)
        fine = craquelure(w, h, seed + 9, cell=17 * w / 2048, warp=0.02)
        where = smooth(0.3, 0.7, fbm(w, h, 4, 4, seed=seed + 7)) * 0.7 + 0.3
        lift = np.roll(np.roll(big, 1, 0), 1, 1)
        img = img * (1 - (0.26 * big + 0.09 * fine) * where * crack)[..., None] + img * (0.12 * lift * (1 - big) * where * crack)[..., None]
    grain = fbm(w, h, 90, 2, seed=seed + 11)
    img = img * (0.97 + 0.06 * grain)[..., None]
    return np.clip(img, 0, 1)


def brush(img, seed, k=1.0, length=(8, 22), width=(3, 6), flow=None):
    rng = np.random.default_rng(seed)
    h, w, _ = img.shape
    out, _ = PC.paint(np.clip(img, 0, 1), rng, int(w * h / 42 * k), length, width, flow=flow)
    return out


def save(name, img):
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_canvas.png"))
    print("wrote", name, img.shape[1], img.shape[0])


def size(name):
    return L.px(name)


# ------------------------------------------------------------------ painted backgrounds

def lancet_window(img, x0, x1, y0, y1, sky_top, sky_bot, moon_at=None, mull=True, seed=0):
    h, w, _ = img.shape
    hw = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    ys = y0 + (y1 - y0) * 0.3
    pts = [(x0, y1), (x0, ys)] + [(cx - hw * math.cos(t * math.pi / 2) ** 0.9, ys - (ys - y0) * math.sin(t * math.pi / 2)) for t in np.linspace(0, 1, 12)] + \
          [(cx + hw * math.cos(t * math.pi / 2) ** 0.9, ys - (ys - y0) * math.sin(t * math.pi / 2)) for t in np.linspace(1, 0, 12)] + [(x1, ys), (x1, y1)]
    m = poly_mask(w, h, pts, 1.0)
    x, y = grid(w, h)
    sky = mix(col(*sky_top), col(*sky_bot), smooth(y0, y1, y))
    sky = mix(sky, sky * 1.4, smooth(0.55, 0.8, fbm(w, h, 5, 5, seed=seed)) * 0.5)
    if moon_at:
        PC.moon(sky, w, h, *moon_at)
    img[:] = mix(img, sky, m)
    if mull:
        seg = [((x0 + x1) / 2, ys - (ys - y0) * 0.6, (x0 + x1) / 2, y1, max(3, w * 0.006))]
        for t in (0.35, 0.65):
            yy = ys + (y1 - ys) * t
            seg.append((x0, yy, x1, yy, max(3, w * 0.005)))
        img[:] = mix(img, col(0.03, 0.025, 0.03), lines_mask(w, h, seg, 1.0) * m)
    # the reveal
    ring = np.clip(poly_mask(w, h, pts, 6) - m * 0.85, 0, 1)
    img[:] = mix(img, col(0.1, 0.08, 0.07), ring * 0.6)
    return m


def oak_panels(w, h, base=(0.07, 0.045, 0.03), seed=0, cols=4, rows=2, top=0.0, bot=1.0):
    x, y = grid(w, h)
    img = np.ones((h, w, 3), np.float32) * col(*base)
    grain = PC.stretched(w, h, 1, 10, 4, seed)
    img = img * (0.75 + 0.5 * grain)[..., None]
    for i in range(cols):
        for j in range(rows):
            px0, px1 = (i + 0.12) / cols, (i + 0.88) / cols
            py0, py1 = top + (bot - top) * (j + 0.08) / rows, top + (bot - top) * (j + 0.92) / rows
            m = poly_mask(w, h, [(px0, py0), (px1, py0), (px1, py1), (px0, py1)], 2)
            inner = poly_mask(w, h, [(px0 + 0.01, py0 + 0.01), (px1 - 0.01, py0 + 0.01), (px1 - 0.01, py1 - 0.01), (px0 + 0.01, py1 - 0.01)], 2)
            img = img * (1 - 0.35 * np.clip(m - inner, 0, 1))[..., None] + col(0.08, 0.05, 0.03) * (np.clip(m - inner, 0, 1) * 0.3)[..., None]
    return img


def curtain(img, x0, x1, y0, y1, colour, folds=7, seed=0):
    h, w, _ = img.shape
    x, y = grid(w, h)
    m = poly_mask(w, h, [(x0, y0), (x1, y0), (x1, y1), (x0 + (x1 - x0) * 0.25, y1)], 2)
    u = (x - x0) / max(1e-3, x1 - x0)
    f = 0.5 + 0.5 * np.sin(u * folds * 2 * math.pi + np.sin(y * 9 + seed) * 0.6)
    cloth = col(*colour) * (0.35 + 0.95 * f ** 1.5)[..., None]
    img[:] = mix(img, cloth, m)
    return m


def floor_checker(img, y0, light, dark, vp=(0.5, 0.3), n=16):
    h, w, _ = img.shape
    x, y = grid(w, h)
    t = np.clip((y - y0) / (1 - y0), 1e-3, 1)
    depth = 1 / (t + 0.05)
    u = (x - vp[0]) * (1 / (t + 0.05)) * 0.12
    v = depth * 0.12
    chk = ((np.floor(u * n) + np.floor(v * n * 0.5)) % 2)
    fl = mix(col(*dark), col(*light), chk) * (0.4 + 0.6 * t)[..., None]
    m = smooth(y0 - 0.002, y0 + 0.002, y)
    img[:] = mix(img, fl, m)
    return m


def reflect(img, F, y0, k=0.25):
    """A soft mirror of the figures in a polished floor below y0 (unit)."""
    rgb, alpha = F[0], F[1]
    h, w, _ = img.shape
    r = (rgb * alpha[..., None])[::-1]
    a = alpha[::-1]
    yy = int(h * y0)
    shift = 2 * yy - h
    r = np.roll(r, shift, 0)
    a = np.roll(a, shift, 0)
    x, y = grid(w, h)
    fade = smooth(y0, y0 + 0.02, y) * smooth(1.0, y0, y)
    img[:] = img + blur(r, 3) * (fade * k * blur(a, 3))[..., None]


def bookshelves(w, h, seed):
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * col(0.04, 0.03, 0.025)
    im = Image.fromarray((img * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    shelf_h = h / 6
    pal = [(70, 20, 22), (32, 40, 60), (60, 48, 28), (28, 44, 30), (54, 30, 50), (80, 62, 40), (40, 26, 18)]
    for r in range(6):
        y1 = (r + 1) * shelf_h - 18
        x = 0
        while x < w:
            bw = rng.integers(14, 34)
            bh = rng.uniform(0.62, 0.92) * (shelf_h - 22)
            c = pal[rng.integers(0, len(pal))]
            k = rng.uniform(0.6, 1.1)
            d.rectangle([x, y1 - bh, x + bw - 2, y1], fill=tuple(int(v * k) for v in c))
            for b in (0.2, 0.8):
                d.rectangle([x + 2, y1 - bh * b - 3, x + bw - 4, y1 - bh * b], fill=(110, 86, 40))
            x += bw
            if rng.random() < 0.05:
                x += rng.integers(20, 60)
        d.rectangle([0, y1, w, y1 + 18], fill=(36, 22, 14))
    return np.asarray(im, np.float32) / 255


def damask(w, h, ground, figure, seed=0, s=180):
    cv = T.Canvas(w, h, ground)
    for j in range(-1, int(h / s) + 2):
        for i in range(-1, int(w / s) + 2):
            T.damask_motif(cv, i * s + (s / 2 if j % 2 else 0), j * s * 1.1, s * 0.9, figure)
    return cv.array()


# ------------------------------------------------------------------ the paintings

def portrait_headmaster_gallery():
    """Headmaster Corvin Ashgrave at full length in his study at night: oak panelling, a lancet window with the moon, a
    crimson curtain, his candle lighting his face, the raven on its pedestal."""
    name = "PortraitHeadmasterGallery"
    w, h = size(name)
    img = oak_panels(w, h, seed=1, cols=3, rows=3, top=0.0, bot=0.86)
    lancet_window(img, 0.08, 0.5, 0.05, 0.52, (0.03, 0.04, 0.1), (0.12, 0.14, 0.26), moon_at=(0.36, 0.17, 0.05, (0.95, 0.93, 0.82), 0.7), seed=3)
    curtain(img, 0.7, 1.02, -0.01, 0.92, (0.42, 0.04, 0.05), folds=5, seed=2)
    x, y = grid(w, h)
    fl = mix(col(0.06, 0.04, 0.03), col(0.12, 0.08, 0.05), PC.stretched(w, h, 8, 1, 4, 5))
    img = mix(img, fl, smooth(0.86, 0.87, y))
    F = figs("HeadmasterGallery", w, h)
    glows(img, F[4], ["candle"], w * 0.22, (0.55, 0.32, 0.12), 0.7)
    img = set_in(img, F)
    glows(img, F[4], ["candle"], w * 0.05, (1.0, 0.7, 0.35), 0.8)
    img = bloom(img, 0.8)
    img = brush(img, 11)
    return finish(img, seed=11)


def portrait_headmistress():
    name = "PortraitHeadmistress"
    w, h = size(name)
    img = bookshelves(w, h, 4) * 0.8
    x, y = grid(w, h)
    img = img * (0.35 + 0.9 * np.exp(-(((x - 0.2) * 1.6) ** 2 + ((y - 0.35) * 1.4) ** 2)))[..., None]
    img = img + col(0.35, 0.2, 0.08) * (np.exp(-(((x - 0.12) * 4) ** 2 + ((y - 0.42) * 4) ** 2)) * 0.6)[..., None]
    PC.candle = None
    img = mix(img, col(0.85, 0.75, 0.55), ellipse_mask(w, h, 0.12, 0.47, 0.012, 0.06, 2))
    glow(img, 0.12 * w, 0.4 * h, 60, col(1.0, 0.65, 0.3), 1.0)
    F = figs("Headmistress", w, h)
    img = set_in(img, F)
    img = bloom(img, 0.85)
    img = brush(img, 12, length=(6, 18))
    return finish(img, seed=12)


def portrait_cursed_student():
    """The cursed student: a cold corridor of arches behind him, ghost hands on his shoulders, pale glowing eyes, and his
    face scratched through to the ground as if someone tried to scrape him out of the picture."""
    name = "PortraitCursedStudent"
    w, h = size(name)
    x, y = grid(w, h)
    img = mix(col(0.03, 0.04, 0.06), col(0.09, 0.11, 0.15), smooth(1.0, 0.2, y))
    for k in range(7):
        t = 1 - k / 7
        aw, ah = 0.5 * t ** 1.2 + 0.04, 0.62 * t ** 1.2 + 0.05
        cx, cy = 0.5, 0.48
        o = PC.ellipse_mask(w, h, cx, cy - ah * 0.25, aw, ah * 0.75, 2) + poly_mask(w, h, [(cx - aw, cy - ah * 0.25), (cx + aw, cy - ah * 0.25), (cx + aw, cy + ah), (cx - aw, cy + ah)], 2)
        img = img * (1 - 0.18 * np.clip(o, 0, 1))[..., None] + col(0.06, 0.07, 0.1) * (np.clip(o, 0, 1) * 0.15 * t)[..., None]
    img = mix(img, col(0.75, 0.82, 0.9), ellipse_mask(w, h, 0.5, 0.5, 0.035, 0.05, 8) * 0.8)
    mist(img, 0.6, 1.0, col(0.2, 0.25, 0.32), k=0.4, seed=4)
    F = figs("CursedStudent", w, h)
    img = set_in(img, F, rim=(0.35, 0.45, 0.6))
    rgb, alpha = F[0], F[1]
    ys, xs = np.nonzero(alpha > 0.5)
    top = ys.min()
    hx0, hx1 = np.percentile(xs[ys < top + h * 0.2], [5, 95])
    rng = np.random.default_rng(7)
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(22):
        cx = rng.uniform(hx0 + 40, hx1 - 40)
        cy = rng.uniform(top + h * 0.06, top + h * 0.15)
        a = rng.uniform(-0.6, 0.6) + math.pi / 2 * rng.choice([0.5, 0.3, 0.6])
        Ln = rng.uniform(60, 220)
        d.line([(cx - math.cos(a) * Ln, cy - math.sin(a) * Ln), (cx + math.cos(a) * Ln, cy + math.sin(a) * Ln)], fill=int(rng.uniform(140, 255)),
               width=int(rng.uniform(2, 6)))
    sc = np.asarray(lay.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    img = brush(img, 13, length=(6, 18))
    img = mix(img, col(0.78, 0.72, 0.6), sc * 0.9)
    img = img * (1 - 0.4 * np.roll(sc, 3, 0))[..., None]
    return finish(img, seed=13)


def portrait_countess():
    name = "PortraitCountessOval"
    w, h = size(name)
    img = damask(w, h, (40, 6, 10), (70, 12, 18), seed=5, s=200)
    x, y = grid(w, h)
    img = img * (0.5 + 0.7 * np.exp(-(((x - 0.6) * 1.4) ** 2 + ((y - 0.3) * 1.4) ** 2)))[..., None]
    lancet_window(img, 0.66, 0.92, 0.08, 0.5, (0.02, 0.02, 0.06), (0.15, 0.06, 0.1), moon_at=(0.79, 0.2, 0.07, (0.95, 0.9, 0.85), 0.5), seed=6)
    F = figs("Countess", w, h)
    img = set_in(img, F, rim=(0.5, 0.15, 0.15))
    glows(img, F[4], [], 1, (1, 1, 1))
    img = bloom(img, 0.8)
    img = brush(img, 14, length=(6, 18))
    return finish(img, seed=14)


def painting_vampire_ball():
    name = "PaintingVampireBall"
    w, h = size(name)
    x, y = grid(w, h)
    img = mix(col(0.05, 0.015, 0.02), col(0.15, 0.04, 0.05), smooth(0.0, 0.7, y))
    # three tall windows: the blood moon in the middle one, behind the dais
    for cx, wd in ((0.5, 0.11), (0.2, 0.07), (0.8, 0.07)):
        lancet_window(img, cx - wd, cx + wd, 0.04, 0.6, (0.06, 0.01, 0.02), (0.3, 0.05, 0.05),
                      moon_at=(cx, 0.2, 0.06, (0.85, 0.25, 0.15), 0.9) if cx == 0.5 else None, seed=int(cx * 10))
    for cx in (0.06, 0.34, 0.66, 0.94):
        col_m = poly_mask(w, h, [(cx - 0.025, 0.0), (cx + 0.025, 0.0), (cx + 0.025, 0.72), (cx - 0.025, 0.72)], 2)
        shade = mix(col(0.06, 0.04, 0.05), col(0.18, 0.12, 0.12), smooth(cx + 0.02, cx - 0.02, x))
        img = mix(img, shade, col_m)
    for x0, x1 in ((0.0, 0.1), (0.9, 1.0)):
        curtain(img, x0, x1, 0.0, 0.75, (0.45, 0.04, 0.06), folds=3)
    floor_checker(img, 0.7, (0.4, 0.33, 0.3), (0.05, 0.02, 0.03))
    F = figs("VampireBall", w, h)
    glows(img, F[4], ["chandelier"], w * 0.12, (0.5, 0.3, 0.12), 0.12)
    reflect(img, F, 0.78, 0.22)
    img = set_in(img, F, rim=(0.45, 0.12, 0.1))
    glows(img, F[4], ["chandelier"], 14, (1.0, 0.75, 0.4), 0.35)
    mist(img, 0.72, 1.0, col(0.25, 0.08, 0.1), k=0.25, seed=9)
    img = bloom(img, 0.78)
    img = brush(img, 15)
    return finish(img, seed=15)


def pines(img, rng, base, hmin, hmax, colour, snow, n, x0=0.0, x1=1.0):
    h, w, _ = img.shape
    m = np.zeros((h, w), np.float32)
    s = np.zeros((h, w), np.float32)
    for _ in range(n):
        cx = rng.uniform(x0, x1)
        th = rng.uniform(hmin, hmax)
        tw = th * 0.28
        b = base + rng.uniform(-0.01, 0.02)
        pts = [(cx, b - th)]
        for k in range(1, 6):
            t = k / 5
            pts += [(cx + tw * t * 0.9, b - th + th * t * 0.85), (cx + tw * t * 0.45, b - th + th * t * 0.85 - 0.004)]
        pts += [(cx + 0.006, b), (cx - 0.006, b)]
        for k in range(5, 0, -1):
            t = k / 5
            pts += [(cx - tw * t * 0.45, b - th + th * t * 0.85 - 0.004), (cx - tw * t * 0.9, b - th + th * t * 0.85)]
        pm = poly_mask(w, h, pts, 0.8)
        m = np.maximum(m, pm)
        s = np.maximum(s, pm * (np.roll(pm, 4, 0) < 0.5))
    img[:] = mix(img, col(*colour), m)
    img[:] = mix(img, col(*snow), blur(s, 1.2) * 0.8)


def painting_wolf_hunt_snow():
    name = "PaintingWolfHuntSnow"
    w, h = size(name)
    rng = np.random.default_rng(16)
    x, y = grid(w, h)
    img = mix(col(0.02, 0.03, 0.08), col(0.14, 0.17, 0.28), smooth(0.0, 0.6, y))
    stars(img, rng, 300, 0.4)
    PC.moon(img, w, h, 0.82, 0.16, 0.05, (0.92, 0.95, 1.0), 0.6)
    pines(img, rng, 0.5, 0.12, 0.22, (0.05, 0.07, 0.1), (0.5, 0.56, 0.68), 70)
    snow = mix(col(0.35, 0.4, 0.55), col(0.62, 0.68, 0.82), smooth(0.5, 1.0, y) * (0.7 + 0.3 * fbm(w, h, 4, 4, seed=3)))
    img = mix(img, snow, smooth(0.5, 0.52, y))
    pines(img, rng, 0.6, 0.2, 0.36, (0.03, 0.05, 0.06), (0.62, 0.68, 0.82), 26, 0.45, 1.0)
    # the hunters' trail through the snow toward the wood
    trail = lines_mask(w, h, [(0.2, 1.0, 0.45, 0.78, 50), (0.45, 0.78, 0.62, 0.62, 24)], 6)
    img = mix(img, col(0.3, 0.32, 0.42), trail * 0.6)
    # the snowy crag the werewolf crouches on (upper left)
    crag = [(0.0, 0.62), (0.0, 0.5), (0.08, 0.47), (0.17, 0.44), (0.3, 0.45), (0.4, 0.5), (0.46, 0.6), (0.4, 0.66), (0.2, 0.66)]
    TW.crag(img, crag, col(0.06, 0.07, 0.1), rim=col(0.4, 0.45, 0.6), rim_dir=(0, -1), k=0.6)
    img = mix(img, col(0.75, 0.8, 0.92), poly_mask(w, h, [(0.0, 0.5), (0.08, 0.47), (0.17, 0.44), (0.3, 0.45), (0.4, 0.5), (0.3, 0.475), (0.17, 0.465),
                                                         (0.08, 0.49), (0.0, 0.52)], 2) * 0.85)
    F = figs("WolfHuntSnow", w, h)
    rgb, alpha = F[0], F[1]
    # snow settled on the ridge the wolf crouches on (the render's grey ridge block) and on its shoulders
    top = alpha * (np.roll(alpha, 6, 0) < 0.5)
    glows(img, F[4], ["torch"], w * 0.05, (0.6, 0.3, 0.1), 0.25)
    img = set_in(img, F, rim=(0.4, 0.45, 0.6))
    img = mix(img, col(0.8, 0.85, 0.95), blur(top, 1.5) * 0.55)
    glows(img, F[4], ["torch"], 18, (1.0, 0.6, 0.25), 0.5)
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for _ in range(1600):
        sx, sy, r = rng.uniform(0, w), rng.uniform(0, h), rng.choice([1.2, 1.8, 2.5, 3.5])
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=int(rng.uniform(120, 255)))
    img = mix(img, col(0.85, 0.9, 1.0), np.asarray(lay.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255 * 0.8)
    img = bloom(img, 0.8)
    img = brush(img, 16)
    return finish(img, seed=16)


def tondo_moon_cloister():
    """A ruined cloister under the moon seen through its own arcade: the garth, a dry fountain in mist, broken arches
    on the far walk, ivy. Painted for a round frame."""
    name = "TondoMoonCloister"
    w, h = size(name)
    rng = np.random.default_rng(17)
    x, y = grid(w, h)
    img = mix(col(0.03, 0.04, 0.1), col(0.2, 0.2, 0.34), smooth(0.0, 0.55, y))
    cl = fbm(w, h, 5, 6, seed=7)
    img = mix(img, col(0.3, 0.3, 0.42), smooth(0.58, 0.8, cl) * (1 - y) * 0.6)
    PC.moon(img, w, h, 0.62, 0.2, 0.07, (0.96, 0.94, 0.84), 0.9)
    stars(img, rng, 200, 0.4)
    # far walk: an arcade of pointed arches, two broken
    wall = poly_mask(w, h, [(0, 0.42), (1, 0.42), (1, 0.66), (0, 0.66)], 1)
    stone = mix(col(0.12, 0.12, 0.17), col(0.22, 0.22, 0.3), fbm(w, h, 20, 4, seed=8))
    img = mix(img, stone, wall)
    holes = np.zeros((h, w), np.float32)
    for k in range(9):
        cx = 0.06 + k * 0.11
        holes = np.maximum(holes, poly_mask(w, h, [(cx - 0.035, 0.66), (cx - 0.035, 0.52), (cx, 0.46), (cx + 0.035, 0.52), (cx + 0.035, 0.66)], 1))
    sky = mix(col(0.03, 0.04, 0.1), col(0.2, 0.2, 0.34), smooth(0.0, 0.55, y))
    img = mix(img, sky * 0.7 + col(0.02, 0.02, 0.03), holes)
    bites = poly_mask(w, h, [(0.25, 0.4), (0.33, 0.4), (0.31, 0.47), (0.27, 0.44)], 1) + poly_mask(w, h, [(0.68, 0.4), (0.8, 0.4), (0.76, 0.5), (0.72, 0.45)], 1)
    img = mix(img, sky, np.clip(bites, 0, 1))
    # the garth, the fountain, mist
    grass = mix(col(0.04, 0.07, 0.05), col(0.1, 0.14, 0.1), fbm(w, h, 12, 4, seed=9))
    img = mix(img, grass, smooth(0.66, 0.67, y))
    img = mix(img, col(0.25, 0.25, 0.3), ellipse_mask(w, h, 0.5, 0.76, 0.16, 0.035, 2))
    img = mix(img, col(0.12, 0.12, 0.16), ellipse_mask(w, h, 0.5, 0.75, 0.13, 0.025, 2))
    img = mix(img, col(0.22, 0.22, 0.28), poly_mask(w, h, [(0.48, 0.75), (0.48, 0.64), (0.52, 0.64), (0.52, 0.75)], 1))
    img = mix(img, col(0.26, 0.26, 0.33), ellipse_mask(w, h, 0.5, 0.64, 0.06, 0.015, 1))
    img = mix(img, col(0.24, 0.24, 0.3), poly_mask(w, h, [(0.495, 0.64), (0.495, 0.58), (0.505, 0.58), (0.505, 0.64)], 1))
    img = img + col(0.35, 0.36, 0.4) * (ellipse_mask(w, h, 0.5, 0.72, 0.13, 0.02, 2) * 0.4)[..., None]
    mist(img, 0.62, 0.86, col(0.4, 0.42, 0.52), k=0.5, seed=10)
    # the near arcade framing the view: two columns and an arch soffit, ivy on them
    near = np.zeros((h, w), np.float32)
    for cx in (0.09, 0.91):
        near = np.maximum(near, poly_mask(w, h, [(cx - 0.07, 1.0), (cx - 0.07, 0.28), (cx + 0.07, 0.28), (cx + 0.07, 1.0)], 1.5))
    arch = np.clip(poly_mask(w, h, [(0, 0), (1, 0), (1, 0.32), (0, 0.32)], 1) - ellipse_mask(w, h, 0.5, 0.36, 0.42, 0.3, 1.5), 0, 1)
    near = np.maximum(near, arch)
    img = mix(img, mix(col(0.03, 0.03, 0.05), col(0.1, 0.1, 0.14), smooth(0.3, 0.0, np.abs(x - 0.5))) * 1.0, near)
    edge = np.clip(near - np.roll(near, -8, 1), 0, 1)
    img = img + col(0.3, 0.3, 0.4) * (blur(edge, 2) * 0.5)[..., None]
    ivy = (fbm(w, h, 40, 3, seed=11) > 0.62) * near * smooth(0.2, 0.6, fbm(w, h, 6, 3, seed=12))
    img = mix(img, col(0.04, 0.1, 0.05), blur(ivy.astype(np.float32), 1) * 0.8)
    img = brush(img, 17)
    return finish(img, seed=17)



def academy(w, h, rng):
    """The school on its cliff as a gothic silhouette, in unit coords (y down): a long hall under a steep roof with
    buttresses and a row of lancets, a central bell tower with an open belfry and a needle spire, a chapel with a rose
    window and pinnacles, round corner towers with conical caps, a gatehouse; windows lit at varied heights."""
    m = np.zeros((h, w), np.float32)
    win = np.zeros((h, w), np.float32)
    base = 0.735

    def add(pts, b=0.6):
        nonlocal m
        m = np.maximum(m, poly_mask(w, h, pts, b))

    def lancet_win(cx, top, ww, hh, lit=True):
        nonlocal win
        if not lit:
            return
        pts = [(cx - ww, top + hh), (cx - ww, top + hh * 0.3), (cx, top), (cx + ww, top + hh * 0.3), (cx + ww, top + hh)]
        win = np.maximum(win, poly_mask(w, h, pts, 0.4) * rng.uniform(0.6, 1.0))

    def tower(cx, tw, top, cap="spire", caph=0.2):
        add([(cx - tw, base), (cx - tw, top), (cx + tw, top), (cx + tw, base)])
        if cap == "spire":
            add([(cx - tw * 1.15, top + 0.004), (cx, top - caph), (cx + tw * 1.15, top + 0.004)])
            add([(cx - 0.0012, top - caph), (cx - 0.0012, top - caph - 0.035), (cx + 0.0012, top - caph - 0.035), (cx + 0.0012, top - caph)])
        elif cap == "cone":
            add([(cx - tw * 1.3, top + 0.01), (cx, top - caph), (cx + tw * 1.3, top + 0.01)])
        else:
            for k in range(4):
                bx = cx - tw + k * tw * 2 / 3.5
                add([(bx, top), (bx, top - 0.02), (bx + tw * 0.3, top - 0.02), (bx + tw * 0.3, top)], 0.3)
        y = top + 0.04
        while y < base - 0.06:
            lancet_win(cx, y, tw * 0.22, 0.045, rng.random() < 0.55)
            y += rng.uniform(0.07, 0.11)

    # the long hall: wall, steep roof, buttresses, a row of lancets
    x0, x1, eave = 0.4, 0.66, 0.5
    add([(x0, base), (x0, eave), (x1, eave), (x1, base)])
    add([(x0 - 0.004, eave + 0.004), (x0 + 0.03, eave - 0.11), (x1 - 0.03, eave - 0.11), (x1 + 0.004, eave + 0.004)])
    for k in range(8):
        bx = x0 + 0.01 + k * (x1 - x0 - 0.02) / 7
        add([(bx - 0.006, base), (bx - 0.003, eave + 0.02), (bx + 0.003, eave + 0.02), (bx + 0.012, base)])
        add([(bx - 0.003, eave + 0.02), (bx, eave - 0.03), (bx + 0.003, eave + 0.02)], 0.3)
        if k < 7:
            lancet_win(bx + (x1 - x0) / 14, eave + 0.05, 0.006, 0.09, rng.random() < 0.8)
            lancet_win(bx + (x1 - x0) / 14, eave + 0.17, 0.005, 0.04, rng.random() < 0.5)
    for k in range(5):
        dx = x0 + 0.05 + k * 0.045
        add([(dx - 0.008, eave - 0.07), (dx - 0.008, eave - 0.1), (dx, eave - 0.12), (dx + 0.008, eave - 0.1), (dx + 0.008, eave - 0.07)], 0.3)
        lancet_win(dx, eave - 0.1, 0.004, 0.025, rng.random() < 0.6)
    # the bell tower in the middle of the hall, an open belfry, a needle spire
    bt = 0.535
    add([(bt - 0.022, base), (bt - 0.022, 0.24), (bt + 0.022, 0.24), (bt + 0.022, base)])
    for sx in (-1, 1):
        add([(bt + sx * 0.022, 0.24), (bt + sx * 0.03, 0.235), (bt + sx * 0.03, 0.2), (bt + sx * 0.022, 0.2)], 0.3)
    add([(bt - 0.028, 0.245), (bt, 0.04), (bt + 0.028, 0.245)])
    belfry = poly_mask(w, h, [(bt - 0.01, 0.33), (bt - 0.01, 0.29), (bt, 0.275), (bt + 0.01, 0.29), (bt + 0.01, 0.33)], 0.4)
    m = m * (1 - belfry * 0.85)
    win = np.maximum(win, belfry * 0.25)
    lancet_win(bt, 0.4, 0.007, 0.05)
    lancet_win(bt, 0.52, 0.007, 0.05, rng.random() < 0.7)
    # the chapel to the left: a gable, a rose window, pinnacles
    c0, c1 = 0.31, 0.39
    add([(c0, base), (c0, 0.55), (c1, 0.55), (c1, base)])
    add([(c0 - 0.004, 0.555), ((c0 + c1) / 2, 0.36), (c1 + 0.004, 0.555)])
    for px in (c0, c1):
        add([(px - 0.006, 0.56), (px - 0.006, 0.48), (px, 0.4), (px + 0.006, 0.48), (px + 0.006, 0.56)], 0.4)
    rose = ellipse_mask(w, h, (c0 + c1) / 2, 0.5, 0.012, 0.042, 0.6)
    win = np.maximum(win, rose)
    lancet_win((c0 + c1) / 2 - 0.02, 0.6, 0.006, 0.09)
    lancet_win((c0 + c1) / 2 + 0.02, 0.6, 0.006, 0.09)
    # towers: a tall corner keep with a spire, round towers with conical caps, a battlemented gatehouse
    tower(0.68, 0.016, 0.3, "spire", 0.18)
    tower(0.72, 0.012, 0.42, "cone", 0.1)
    tower(0.295, 0.012, 0.45, "cone", 0.11)
    tower(0.79, 0.022, 0.52, "flat")
    tower(0.825, 0.01, 0.48, "cone", 0.08)
    add([(0.74, base), (0.74, 0.58), (0.84, 0.58), (0.84, base)])
    for k in range(9):
        bx = 0.74 + k * 0.011
        if k % 2 == 0:
            add([(bx, 0.58), (bx, 0.565), (bx + 0.006, 0.565), (bx + 0.006, 0.58)], 0.3)
    gate = poly_mask(w, h, [(0.775, base), (0.775, 0.67), (0.79, 0.65), (0.805, 0.67), (0.805, base)], 0.4)
    win = np.maximum(win, gate * 0.5)
    for x in np.linspace(0.42, 0.65, 6):
        lancet_win(x, 0.66, 0.004, 0.03, rng.random() < 0.6)
    rim = np.clip(m - np.roll(m, 4, 1), 0, 1)
    return m, win * (m > 0.3), rim


def painting_academy_panorama():
    name = "PaintingAcademyPanorama"
    w, h = size(name)
    rng = np.random.default_rng(18)
    x, y = grid(w, h)
    img = mix(col(0.03, 0.03, 0.09), col(0.32, 0.25, 0.44), smooth(0.0, 0.72, y))
    cl = PC.stretched(w, h, 4, 1, 5, 3)
    img = mix(img, col(0.32, 0.27, 0.42), smooth(0.55, 0.8, cl) * 0.6)
    stars(img, rng, 220, 0.5)
    PC.moon(img, w, h, 0.12, 0.28, 0.07, (0.96, 0.94, 0.84), 0.9)
    # the sea and its moon path
    sea = mix(col(0.03, 0.05, 0.08), col(0.1, 0.12, 0.2), PC.stretched(w, h, 12, 1, 4, 5))
    path = np.exp(-((x - 0.12) / (0.02 + 0.1 * smooth(0.78, 1.0, y))) ** 2) * smooth(0.5, 0.8, PC.stretched(w, h, 18, 1, 3, 6))
    sea = sea + col(0.5, 0.52, 0.45) * (path * 0.8)[..., None]
    img = mix(img, sea, smooth(0.77, 0.78, y))
    # the cliff and the school on it
    cliff = poly_mask(w, h, [(0.2, 1.0), (0.22, 0.82), (0.26, 0.76), (0.4, 0.74), (0.62, 0.73), (0.86, 0.75), (0.92, 0.84), (0.96, 1.0)], 1.5)
    img = mix(img, col(0.04, 0.035, 0.05), cliff)
    cm, win, rim_m = academy(w, h, rng)
    img = mix(img, col(0.05, 0.045, 0.07), cm)
    img = img + col(0.35, 0.36, 0.48) * (blur(rim_m, 1.2) * 0.55)[..., None]
    img = mix(img, col(1.0, 0.72, 0.35), win)
    img = img + col(0.6, 0.35, 0.1) * blur(win, 6)[..., None] * 0.6
    # the moat below the walls, the lit windows trembling in it
    moat = poly_mask(w, h, [(0.27, 0.735), (0.86, 0.735), (0.86, 0.76), (0.27, 0.76)], 1)
    img = mix(img, col(0.04, 0.05, 0.09), moat)
    refl = np.roll(win[::-1], int(2 * 0.735 * h) - h, 0) * moat
    img = img + col(0.8, 0.5, 0.2) * blur(refl, 2)[..., None] * 0.4
    mist(img, 0.66, 0.8, col(0.32, 0.32, 0.45), k=0.55, seed=8)
    TW.flying_ravens(img, rng, 14, 0.3 * w, 0.85 * w, 0.04 * h, 0.32 * h, col(0.02, 0.02, 0.03), s=(14, 26))
    mist(img, 0.72, 0.92, col(0.3, 0.3, 0.42), k=0.45, seed=7)
    img = bloom(img, 0.85)
    img = brush(img, 18, length=(5, 14), width=(2, 4))
    img = mix(img, col(1.0, 0.76, 0.4), win * 0.75)          # the lit windows again, crisp over the brushwork
    return finish(img, seed=18, crack=0.8)


def painting_class_1887():
    name = "PaintingClassOf1887"
    w, h = size(name)
    x, y = grid(w, h)
    img = mix(col(0.22, 0.17, 0.12), col(0.1, 0.08, 0.06), np.clip(np.sqrt((x - 0.45) ** 2 + (y - 0.4) ** 2) * 1.5, 0, 1))
    img = img * (0.8 + 0.4 * fbm(w, h, 6, 5, seed=4))[..., None]
    curtain(img, -0.02, 0.16, 0.0, 0.7, (0.32, 0.06, 0.06), folds=3)
    img = mix(img, col(0.12, 0.08, 0.05), smooth(0.84, 0.86, y))
    F = figs("Class1887", w, h)
    img = set_in(img, F, ghost_k=0.7)
    lum = img.mean(2, keepdims=True)
    img = mix(img, lum * col(1.15, 0.95, 0.72), 0.35)
    img = brush(img, 19, length=(5, 15), width=(2, 5))
    return finish(img, seed=19, crack=1.15)


# ------------------------------------------------------------------ the drawn pieces

EMBLEM = L.EMBLEM
CLIQUES = [("Vigil", "The Vigil", (235, 205, 120), "candle"), ("Court", "Crimson Court", (200, 40, 60), "crown"),
           ("Athletes", "Athletes", (90, 150, 220), "pennant"), ("Delinquents", "Delinquents", (150, 110, 70), "flames"),
           ("Pack", "The Pack", (130, 150, 90), "paw"), ("Ordinary", "The Ordinary", (200, 190, 170), "smiley"),
           ("Choir", "Chapel Choir", (230, 225, 210), "halo"), ("Ink", "Ink Club", (150, 80, 190), "quill")]


def draw_emblem(d, kind, cx, cy, s, fill, width):
    """An emblem from the clique config (y up in its unit space) onto a PIL draw."""
    e = EMBLEM[kind]
    for f in e["fills"]:
        d.polygon([(cx + x * s, cy - y * s) for x, y in f], fill=fill)
    for st in e["strokes"]:
        d.line([(cx + x * s, cy - y * s) for x, y in st], fill=fill, width=int(width), joint="curve")


def _shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


def clique_heraldry():
    """The eight cliques' arms painted on an oak board as the school blazons them: two rows of shields in the clique
    colours, each charged with its emblem, a name scroll beneath, on an oxblood ground with a gilt diaper."""
    name = "CliqueHeraldry"
    w, h = size(name)
    im = Image.new("RGB", (w, h), (44, 10, 14))
    d = ImageDraw.Draw(im)
    for j in range(0, h, 64):
        for i in range(0, w, 64):
            o = 32 if (j // 64) % 2 else 0
            d.polygon([(i + o, j - 10), (i + o + 10, j), (i + o, j + 10), (i + o - 10, j)], fill=(92, 62, 26))
    font = ImageFont.truetype(BLACK, 46)
    cols_, rows_ = 4, 2
    cw, rh = w / cols_, h / rows_
    for k, (_, title, c, kind) in enumerate(CLIQUES):
        cx, cy = cw * (k % cols_ + 0.5), rh * (k // cols_ + 0.44)
        s = rh * 0.62
        sh = [(cx + x * s, cy + y * s) for x, y in [(-0.42, -0.42), (0.42, -0.42), (0.42, 0.02), (0.3, 0.3), (0, 0.46), (-0.3, 0.3), (-0.42, 0.02)]]
        d.polygon([(px + 8, py + 10) for px, py in sh], fill=(16, 4, 6))
        d.polygon(sh, fill=(196, 150, 64))
        inner = [(cx + (px - cx) * 0.9, cy + (py - cy) * 0.9) for px, py in sh]
        d.polygon(inner, fill=c)
        # a dark half for counterchange, then the emblem in a contrasting tincture
        half = [(cx, cy - 0.38 * s), (cx + 0.38 * s, cy - 0.38 * s), (cx + 0.38 * s, cy + 0.02 * s), (cx + 0.27 * s, cy + 0.27 * s), (cx, cy + 0.41 * s)]
        d.polygon(half, fill=_shade(c, 0.72))
        lum = sum(c) / 3
        charge = (28, 18, 20) if lum > 150 else (226, 196, 110)
        draw_emblem(d, kind, cx, cy - 0.02 * s, s * 0.62, charge, s * 0.035)
        sy = cy + 0.58 * s
        d.polygon([(cx - 0.62 * s, sy - 26), (cx + 0.62 * s, sy - 26), (cx + 0.7 * s, sy + 6), (cx + 0.62 * s, sy + 34), (cx - 0.62 * s, sy + 34), (cx - 0.7 * s, sy + 6)],
                  fill=(222, 204, 160), outline=(120, 90, 40))
        d.text((cx, sy + 4), title, font=font, fill=(90, 14, 18), anchor="mm")
    img = np.asarray(im, np.float32) / 255
    img = brush(img, 20, k=0.5, length=(4, 10), width=(2, 3))
    return finish(img, seed=20, vig=0.25)


def stained_glass_roundel():
    """A leaded roundel: the raven perched on the school key under a crescent, on deep blue quarries with gold stars,
    a ring of crimson and amber lights round it, lead cames between every piece."""
    name = "StainedGlassRoundel"
    w, h = size(name)
    cv = T.Canvas(w, h, (10, 10, 14))
    cx, cy, R = w / 2, h / 2, w * 0.49
    cv.circle(cx, cy, R, (24, 34, 110))
    # quarries: a diamond lattice clipped by the circle later (lead drawn after)
    n = 22
    for i in range(-n, n):
        for j in range(-n, n):
            px, py = cx + (i - j) * 70, cy + (i + j) * 90
            if (px - cx) ** 2 + (py - cy) ** 2 < (R * 0.78) ** 2:
                k = ((i * 7 + j * 13) % 5) / 10
                cv.poly([(px, py - 90), (px + 70, py), (px, py + 90), (px - 70, py)], (int(30 + 40 * k), int(42 + 30 * k), int(130 + 60 * k)))
    # the border ring of lights
    for k in range(16):
        a0, a1 = k / 16 * 2 * math.pi, (k + 1) / 16 * 2 * math.pi
        c = (170, 20, 30) if k % 2 else (230, 150, 40)
        pts = [(cx + math.cos(a0 + (a1 - a0) * t) * R, cy + math.sin(a0 + (a1 - a0) * t) * R) for t in np.linspace(0, 1, 8)] + \
              [(cx + math.cos(a1 - (a1 - a0) * t) * R * 0.8, cy + math.sin(a1 - (a1 - a0) * t) * R * 0.8) for t in np.linspace(0, 1, 8)]
        cv.poly(pts, c)
    cv.poly(T.crescent(cx, cy - R * 0.45, R * 0.16, tilt=math.pi / 2, shift=0.4), (236, 226, 180))
    for sx, sy in ((-0.4, -0.35), (0.42, -0.3), (-0.5, 0.05), (0.52, 0.1), (-0.25, -0.6), (0.3, -0.6)):
        cv.poly(T.star(cx + sx * R, cy + sy * R, R * 0.05, 4), (240, 200, 90))
    T.key_shape(cv, cx + R * 0.02, cy + R * 0.42, R * 0.75, (230, 180, 70), ring_col=(30, 40, 120))
    MO.raven(cv, cx, cy + R * 0.02, R * 0.85, (20, 18, 30), (220, 60, 50), (70, 60, 110))
    base = cv.array()
    # the lead: edges between differently coloured glass, thickened, plus the radial cames of the ring
    lum = base.mean(2)
    edge = np.zeros_like(lum)
    for ax in (0, 1):
        edge = np.maximum(edge, np.abs(np.diff(base, axis=ax, prepend=base.take([0], axis=ax))).max(2))
    lead = (edge > 0.05).astype(np.float32)
    lead = ndimage.binary_dilation(lead, iterations=4).astype(np.float32)
    x, y = grid(w, h)
    rr = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.49
    lead = np.maximum(lead, ((np.abs(rr - 0.8) < 0.012) | (np.abs(rr - 1.0) < 0.02)).astype(np.float32))
    glass = base * (0.82 + 0.36 * fbm(w, h, 24, 3, seed=21))[..., None]
    streak = PC.stretched(w, h, 1, 8, 3, 22)
    glass = glass * (0.9 + 0.2 * streak)[..., None]
    pits = fbm(w, h, 120, 1, seed=23)
    glass = glass * (0.94 + 0.12 * pits)[..., None]
    lead_c = col(0.07, 0.07, 0.08) + col(0.15, 0.15, 0.17) * blur(lead, 2)[..., None] * 0.3
    img = mix(glass, lead_c, blur(lead, 1.0))
    img = img * smooth(1.02, 0.99, rr)[..., None]
    return np.clip(img, 0, 1)


def mosaic_raven():
    """A Byzantine-style mosaic for an arched wall panel: the raven on the key under the crescent moon on a gold
    tessera ground, a band of crimson and ink, laid in small irregular tesserae with dark grout."""
    name = "MosaicRaven"
    w, h = size(name)
    cv = T.Canvas(w, h, (170, 120, 40))
    x, y = grid(w, h)
    cv.poly(T.crescent(w * 0.5, h * 0.2, w * 0.13, tilt=math.pi / 2, shift=0.4), (232, 228, 210))
    for sx, sy in ((0.2, 0.15), (0.8, 0.18), (0.15, 0.4), (0.85, 0.42)):
        cv.poly(T.star(w * sx, h * sy, w * 0.04, 6), (236, 230, 205))
    T.key_shape(cv, w * 0.52, h * 0.66, w * 0.9, (110, 76, 30), ring_col=(170, 120, 40))
    MO.raven(cv, w * 0.5, h * 0.48, w * 0.85, (18, 16, 26), (190, 30, 40), (60, 60, 100))
    for k, c in enumerate(((120, 18, 26), (20, 22, 40), (120, 18, 26))):
        cv.rect(0, h * (0.9 + k * 0.035), w, h * (0.935 + k * 0.035), c)
    design = cv.array()
    design = mix(design, design * col(1.15, 1.05, 0.85), fbm(w, h, 8, 3, seed=3) * 0.3)
    # tesserae: jittered cells, each one flat colour from the design at its centre, set a little unevenly
    rng = np.random.default_rng(24)
    cell = 26
    gx, gy = np.meshgrid(np.arange(0, w + cell, cell), np.arange(0, h + cell, cell))
    pts = np.stack([gx.ravel() + rng.uniform(-7, 7, gx.size) + (gy.ravel() // cell % 2) * cell / 2, gy.ravel() + rng.uniform(-7, 7, gy.size)], 1)
    yy, xx = np.mgrid[0:h, 0:w]
    q = np.stack([xx.ravel(), yy.ravel()], 1)
    d, idx = cKDTree(pts).query(q, k=2, workers=-1)
    near = idx[:, 0]
    cxs = np.clip(pts[near, 0].astype(int), 0, w - 1)
    cys = np.clip(pts[near, 1].astype(int), 0, h - 1)
    tile = design[cys, cxs].reshape(h, w, 3)
    jit = rng.uniform(0.82, 1.12, len(pts)).astype(np.float32)[near].reshape(h, w)
    tile = tile * jit[..., None]
    is_gold = (design[..., 0] > 0.55) & (design[..., 2] < 0.3)
    glint = rng.uniform(0, 1, len(pts))[near].reshape(h, w) > 0.85
    tile = tile + col(0.25, 0.2, 0.08) * (glint & is_gold)[..., None]
    gap = (d[:, 1] - d[:, 0]).reshape(h, w)
    grout = smooth(4.0, 1.5, gap)
    img = mix(tile, col(0.12, 0.1, 0.09), grout)
    return np.clip(img * (0.94 + 0.08 * fbm(w, h, 30, 2, seed=5))[..., None], 0, 1)


def _icon_panel(name, scene, colour_halo=(0.95, 0.75, 0.3), title=None):
    w, h = size(name)
    x, y = grid(w, h)
    gold = mix(col(0.55, 0.38, 0.12), col(0.88, 0.68, 0.3), fbm(w, h, 24, 4, seed=len(name)))
    punch = smooth(0.82, 0.84, (np.sin(x * w * 0.14) * np.sin(y * h * 0.14)) * 0.5 + 0.5) * 0.1
    img = gold * (1 - punch[..., None])
    F = figs(scene, w, h, fit="h", x=0.5, y=0.99, height=0.86)
    rgb, alpha = F[0], F[1]
    ys, xs = np.nonzero(alpha > 0.5)
    hy = ys.min() + (ys.max() - ys.min()) * 0.12
    hx = xs[ys < ys.min() + 30].mean()
    ring = ellipse_mask(w, h, hx / w, hy / h, 0.26 * h / w * 0.75, 0.155, 1) * (1 - ellipse_mask(w, h, hx / w, hy / h, 0.24 * h / w * 0.75, 0.143, 1))
    halo_disc = ellipse_mask(w, h, hx / w, hy / h, 0.26 * h / w * 0.75, 0.155, 1)
    img = mix(img, img * col(1.1, 1.0, 0.8) + 0.06, halo_disc * 0.6)
    img = mix(img, col(0.45, 0.3, 0.08), ring)
    # tempera: the figure's colours flattened a little and outlined in dark
    flat_ = np.round(rgb * 6) / 6 * 0.5 + rgb * 0.5
    img = TW.comp(img, flat_ * 1.25, alpha, shadow=False)
    out = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    img = mix(img, col(0.08, 0.05, 0.04), np.clip(out * 2, 0, 1) * 0.7)
    if title:
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        dd = ImageDraw.Draw(im)
        f = ImageFont.truetype(SERIF, int(w * 0.075))
        dd.text((w / 2, h * 0.045), title, font=f, fill=(140, 20, 24), anchor="mm")
        img = np.asarray(im, np.float32) / 255
    img = brush(img, len(name), k=0.5, length=(4, 10), width=(2, 3))
    return finish(img, seed=len(name) + 30, crack=1.2, vig=0.2)


def icon_centre():
    return _icon_panel("IconTriptych", "IconFounder", title="S. FUNDATOR")


def icon_left():
    return _icon_panel("IconTriptychL", "IconVigil", title="S. VIGIL")


def icon_right():
    return _icon_panel("IconTriptychR", "IconCantor", title="S. CANTOR")


def portrait_miniatures():
    """Five miniature portraits for the salon cluster, painted into one image laid out as the board (art41_layout.MINIS):
    each on its own coloured ground, a vignette, the sitter from the R6 renders."""
    x0, x1, z0, z1 = L.minis_bounds()
    W = 2048
    H = int(round(W * (z1 - z0) / (x1 - x0)))
    img = np.ones((H, W, 3), np.float32) * col(0.2, 0.03, 0.05)
    grounds = {"MiniCourtGirl": (0.2, 0.22, 0.3), "MiniVampire": (0.3, 0.05, 0.06), "MiniWolfGirl": (0.12, 0.18, 0.12), "MiniProfessor": (0.22, 0.17, 0.1),
               "MiniChoirBoy": (0.1, 0.12, 0.26)}
    for scene, shape, cx, cz, pw, ph in L.MINIS:
        px0 = int((cx - pw / 2 - x0) / (x1 - x0) * W)
        px1 = int((cx + pw / 2 - x0) / (x1 - x0) * W)
        py0 = int((z1 - (cz + ph / 2)) / (z1 - z0) * H)
        py1 = int((z1 - (cz - ph / 2)) / (z1 - z0) * H)
        w, h = px1 - px0, py1 - py0
        x, y = grid(w, h)
        g = col(*grounds[scene])
        sub = g * (0.45 + 0.9 * np.exp(-(((x - 0.45) * 1.6) ** 2 + ((y - 0.35) * 1.6) ** 2)))[..., None]
        F = figs(scene, w, h, fit="h", x=0.5, y=1.02, height=1.05)
        sub = set_in(sub, F)
        img[py0:py1, px0:px1] = sub
    img = brush(img, 25, k=0.7, length=(4, 12), width=(2, 4))
    return finish(img, seed=25, vig=0.1)


# ------------------------------------------------------------------ the tapestries

def tapestry_cliques():
    """The Cliques of Nightmare High: the school crest in the middle, the eight clique emblems on roundels in their
    colours round it, joined by a thorned vine, on a dark millefleur ground; the weave, border and title as batch 29's."""
    W, H = TW.PORTRAIT
    Hd = H - T.SW
    B = TW.BORDER
    fw, fh = W - 2 * B, Hd - 2 * B
    rng = np.random.default_rng(141)
    x, y = grid(fw, fh)
    img = mix(col(0.05, 0.08, 0.1), col(0.02, 0.03, 0.05), np.clip(np.sqrt((x - 0.5) ** 2 + (y - 0.45) ** 2) * 1.6, 0, 1))
    cv = T.Canvas(fw, fh, (0, 0, 0))
    for _ in range(160):
        fx, fy = rng.uniform(0, fw), rng.uniform(0, fh)
        cc = ["crimsonlt", "bone", "gold", "rose", "plumlt"][rng.integers(0, 5)]
        cv.line([(fx, fy + 30), (fx, fy)], "mossdk", 5)
        cv.poly(T.leaf(fx, fy + 24, fx - 22, fy + 8, 10), "moss")
        cv.poly(T.leaf(fx, fy + 24, fx + 22, fy + 10, 10), "moss")
        cv.poly(T.foil(fx, fy - 5, 15, 5, k=0.5), cc)
        cv.circle(fx, fy - 5, 4, "gold")
    fl = cv.array()
    flm = (fl.max(2) > 0.02).astype(np.float32)
    img = mix(img, fl * 0.7, flm[..., None] * 0.75)
    cv2 = T.Canvas(fw, fh, (0, 0, 0))
    cxp, cyp = fw / 2, fh * 0.48
    R = fw * 0.36
    ring = [(cxp + math.cos(a) * R, cyp + math.sin(a) * R * 1.12) for a in np.linspace(0, 2 * math.pi, 120)]
    MO.thorn_vine(cv2, ring, 12, "mossdk")
    T.crest(cv2, cxp, cyp, 420)
    im2 = cv2.im
    d2 = ImageDraw.Draw(im2)
    for k, (_, title, c, kind) in enumerate(CLIQUES):
        a = -math.pi / 2 + k / 8 * 2 * math.pi
        ex, ey = cxp + math.cos(a) * R, cyp + math.sin(a) * R * 1.12
        r = 120
        d2.ellipse([ex - r - 10, ey - r - 10, ex + r + 10, ey + r + 10], fill=T.C["gold"] if hasattr(T, "C") else (200, 160, 70))
        d2.ellipse([ex - r, ey - r, ex + r, ey + r], fill=tuple(c))
        lum = sum(c) / 3
        draw_emblem(d2, kind, ex, ey, r * 1.35, (30, 20, 22) if lum > 150 else (230, 200, 120), 14)
    arms = np.asarray(im2, np.float32) / 255
    am = (arms.max(2) > 0.02).astype(np.float32)
    am = blur(am, 0.7)
    img = img * (1 - (blur(np.roll(am, 12, 0), 10) * 0.55)[..., None])
    img = mix(img, arms, am)
    gm = TW.gilt_of(arms) * am
    img = bloom(img)
    img, _ = PC.paint(np.clip(img, 0, 1), rng, int(fw * fh / 40), (4, 12), (2, 4), jitter=0.03)
    cvb = T.Canvas(W, Hd, "ink")
    TW.border(cvb, W, Hd, B)
    full = cvb.array()
    full[B:B + fh, B:B + fw] = img
    gilt = TW.gilt_of(full)
    gilt[B:B + fh, B:B + fw] = gm
    bcv = T.Canvas(W, Hd, (0, 0, 0))
    TW.banner(bcv, W / 2, Hd - B - 64, fw * 0.66, "Octo Domus, Una Nox", 62)
    band_rgb = bcv.array()
    band_m = (band_rgb.max(2) > 0.02).astype(np.float32)
    full = mix(full, band_rgb, band_m)
    gilt = np.maximum(gilt, TW.gilt_of(band_rgb) * band_m)
    col_, hgt, rough, metal = TW.tapestry_weave(full, gilt, seed=141)
    T.finish("TapestryCliquesWeave", col_, hgt, rough, (W, H), fringe="gold", backing="ink", strength=4.0, metal=metal)
    print("wrote TapestryCliquesWeave")


def tapestry_procession():
    """The Midnight Procession: the Chapel Choir and the Vigil cross the old bridge with lanterns and candles, the cantor
    with the crescent staff leading; the school on its hill behind, the moon, the river in mist below."""
    W, H = TW.FRIEZE
    Hd = H - T.SW
    B = TW.BORDER
    fw, fh = W - 2 * B, Hd - 2 * B
    rng = np.random.default_rng(142)
    x, y = grid(fw, fh)
    img = mix(col(0.03, 0.03, 0.09), col(0.18, 0.15, 0.3), smooth(0.0, 0.8, y))
    stars(img, rng, 300, 0.5)
    PC.moon(img, fw, fh, 0.8, 0.18, 0.07, (0.96, 0.94, 0.84), 0.9)
    cm, win = TW.castle(fw, fh, 0.05, 0.6, 0.45, 0.88, rng, lit=0.5)
    img = mix(img, col(0.08, 0.07, 0.12), cm)
    img = mix(img, col(1.0, 0.72, 0.35), win)
    # the bridge: a parapet the figures walk along, arches over the river
    deck = 0.86
    img = mix(img, col(0.1, 0.1, 0.13), smooth(deck - 0.005, deck, y))
    for k in range(5):
        cx = 0.1 + k * 0.2
        img = mix(img, col(0.02, 0.03, 0.05), ellipse_mask(fw, fh, cx, 1.02, 0.08, 0.11, 2))
    mist(img, 0.88, 1.0, col(0.35, 0.36, 0.48), k=0.6, seed=4)
    rgb, alpha, gmask, ghost, pts = figs("Procession", fw, fh)
    img = TW.comp(img, rgb, alpha)
    for kind in ("lantern", "candle"):
        for px, py in pts.get(kind, []):
            glow(img, px, py, 40 if kind == "lantern" else 24, col(1.0, 0.62, 0.3), 0.9)
    img = bloom(img)
    img, _ = PC.paint(np.clip(img, 0, 1), rng, int(fw * fh / 40), (4, 12), (2, 4), jitter=0.03)
    cvb = T.Canvas(W, Hd, "ink")
    TW.border(cvb, W, Hd, B)
    full = cvb.array()
    full[B:B + fh, B:B + fw] = img
    gilt = TW.gilt_of(full)
    gilt[B:B + fh, B:B + fw] = gmask
    bcv = T.Canvas(W, Hd, (0, 0, 0))
    TW.banner(bcv, W / 2, Hd - B - 58, fw * 0.48, "The Midnight Procession", 58)
    band_rgb = bcv.array()
    band_m = (band_rgb.max(2) > 0.02).astype(np.float32)
    full = mix(full, band_rgb, band_m)
    gilt = np.maximum(gilt, TW.gilt_of(band_rgb) * band_m)
    col_, hgt, rough, metal = TW.tapestry_weave(full, gilt, seed=142)
    T.finish("TapestryProcessionWeave", col_, hgt, rough, (W, H), fringe="gold", backing="ink", strength=4.0, metal=metal)
    print("wrote TapestryProcessionWeave")


PAINTINGS = {
    "PortraitHeadmasterGallery": portrait_headmaster_gallery,
    "PortraitHeadmistress": portrait_headmistress,
    "PortraitCursedStudent": portrait_cursed_student,
    "PortraitCountessOval": portrait_countess,
    "PaintingVampireBall": painting_vampire_ball,
    "PaintingWolfHuntSnow": painting_wolf_hunt_snow,
    "TondoMoonCloister": tondo_moon_cloister,
    "PaintingAcademyPanorama": painting_academy_panorama,
    "PaintingClassOf1887": painting_class_1887,
    "CliqueHeraldry": clique_heraldry,
    "StainedGlassRoundel": stained_glass_roundel,
    "MosaicRaven": mosaic_raven,
    "IconTriptych": icon_centre,
    "IconTriptychL": icon_left,
    "IconTriptychR": icon_right,
    "PortraitMiniatures": portrait_miniatures,
}
WEAVES = {"TapestryCliques": tapestry_cliques, "TapestryProcession": tapestry_procession}

if __name__ == "__main__":
    want = sys.argv[1:] or list(PAINTINGS) + list(WEAVES)
    for n in want:
        if n in WEAVES:
            WEAVES[n]()
        else:
            save(n, PAINTINGS[n]())
