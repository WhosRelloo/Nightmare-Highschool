"""The art kit's paintings (props batch 21): original gothic-romantic oil paintings drawn procedurally, then given a
painterly finish: thousands of short oriented brush strokes that pick up the colour beneath, impasto in the normal map,
canvas weave, an aged amber varnish and a soft vignette. Writes art/props/textures/<Painting>_canvas.png (colour) and
the shared Canvas_normal.png / Canvas_rough.png.

  python art/props/paint_canvases.py [names...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
RNG = np.random.default_rng(1919)


# ------------------------------------------------------------------ helpers

def grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x / w, y / h


def fbm(w, h, scale, octaves=5, seed=0):
    """Smooth value-noise fbm (0..1) by summing upscaled random grids."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cw, ch = max(2, int(scale * 2 ** o)), max(2, int(scale * 2 ** o * h / w))
        g = rng.random((ch, cw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return out / tot


def mix(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def col(*c):
    return np.array(c, np.float32)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def poly_mask(w, h, pts, blur=0.0):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).polygon([(x * w, y * h) for x, y in pts], fill=255)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255


def lines_mask(w, h, segs, blur=0.0):
    """Tapered strokes: segs of (x0, y0, x1, y1, width_px)."""
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for x0, y0, x1, y1, wd in segs:
        d.line([(x0 * w, y0 * h), (x1 * w, y1 * h)], fill=255, width=max(1, int(wd)))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255


def ellipse_mask(w, h, cx, cy, rx, ry, blur=0.0):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).ellipse([(cx - rx) * w, (cy - ry) * h, (cx + rx) * w, (cy + ry) * h], fill=255)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.float32) / 255


def tree(segs, x, y, ang, length, width, depth, rng, droop=0.0):
    """A bare tree as recursive tapered branches (y grows down the canvas)."""
    if depth == 0 or length < 0.004:
        return
    x1, y1 = x + math.cos(ang) * length, y - math.sin(ang) * length
    segs.append((x, y, x1, y1, width))
    n = 2 if depth > 2 else rng.integers(2, 4)
    for k in range(n):
        da = rng.uniform(0.25, 0.75) * (1 if k % 2 else -1)
        tree(segs, x1, y1, ang + da - droop, length * rng.uniform(0.62, 0.8), width * 0.68, depth - 1, rng, droop)


def moon(img, w, h, cx, cy, r, tint, glow, halo=3.5):
    """A moon disc with soft maria and a wide glow."""
    x, y = grid(w, h)
    asp = w / h
    d = np.sqrt(((x - cx) * asp) ** 2 + (y - cy) ** 2)
    g = np.exp(-(d / (r * halo)) ** 2) * glow
    img[:] = img + col(*tint)[None, None, :] * g[..., None] * 0.6
    disc = smooth(r, r * 0.97, d)
    maria = fbm(w, h, 14, 4, seed=7)
    face = col(*tint) * (0.86 + 0.18 * maria[..., None])
    img[:] = mix(img, face, disc)
    return d


def paint(img, rng, strokes=60000, length=(6, 22), width=(2, 5), flow=None, jitter=0.05):
    """The painterly pass: short oriented strokes that take the colour under them (a touch varied), and the height
    of the impasto for the normal map."""
    h, w, _ = img.shape
    base = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    out = base.copy()
    d = ImageDraw.Draw(out)
    hgt = Image.new("L", (w, h), 128)
    dh = ImageDraw.Draw(hgt)
    flow = flow if flow is not None else fbm(w, h, 3, 3, seed=11) * math.pi * 2
    xs = rng.integers(0, w, strokes)
    ys = rng.integers(0, h, strokes)
    src = np.asarray(base, np.int32)
    for x, y in zip(xs, ys):
        c = src[y, x] + rng.normal(0, 255 * jitter, 3)
        a = flow[y, x] + rng.normal(0, 0.25)
        L = rng.uniform(*length)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        wd = int(rng.uniform(*width))
        d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=tuple(int(v) for v in np.clip(c, 0, 255)), width=wd)
        dh.line([(x - dx, y - dy), (x + dx, y + dy)], fill=int(rng.uniform(100, 200)), width=wd)
    res = np.asarray(out, np.float32) / 255
    res = res * 0.8 + img * 0.2                # keep the drawing's crisp edges under the strokes
    return res, np.asarray(hgt, np.float32) / 255


def finish(img, w, h, seed=3):
    """Aged varnish (warm amber, a little darker at the edges), fine crackle and a vignette."""
    x, y = grid(w, h)
    vig = 1 - 0.38 * (((x - 0.5) * 2) ** 2 + ((y - 0.5) * 2) ** 2) ** 1.2
    img = img * np.clip(vig, 0.4, 1)[..., None]
    amber = col(1.0, 0.9, 0.7)
    img = img * (0.88 + 0.12 * amber)
    crack = fbm(w, h, 60, 2, seed=seed)
    img = img * (1 - 0.05 * smooth(0.62, 0.66, crack))[..., None]
    return np.clip(img, 0, 1)


def save(name, img):
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_canvas.png"))
    print("wrote", name)


# ------------------------------------------------------------------ the paintings

def abbey():
    """A ruined abbey on a hill under the full moon: a blue-violet night, mist in the valley, a bare oak, gravestones."""
    w, h = 2048, 1365
    rng = np.random.default_rng(21)
    x, y = grid(w, h)
    sky = mix(col(0.05, 0.05, 0.12), col(0.22, 0.2, 0.36), smooth(0.0, 0.75, y))
    clouds = fbm(w, h, 5, 6, seed=2)
    img = mix(sky, col(0.32, 0.3, 0.45), smooth(0.55, 0.8, clouds) * (1 - y) * 0.7)
    moon(img, w, h, 0.27, 0.24, 0.075, (0.96, 0.94, 0.84), 0.9)
    # moonlit cloud edges
    img = img + col(0.25, 0.24, 0.3) * (smooth(0.62, 0.7, clouds) * np.exp(-(((x - 0.27) * 1.5) ** 2 + (y - 0.24) ** 2) * 6))[..., None]
    # far hills, valley mist, the abbey hill
    far = poly_mask(w, h, [(0, 0.66), (0.15, 0.6), (0.32, 0.63), (0.5, 0.58), (0.7, 0.62), (0.88, 0.57), (1, 0.6), (1, 1), (0, 1)], 2)
    img = mix(img, col(0.16, 0.15, 0.26), far)
    mist = np.exp(-((y - 0.68) / 0.05) ** 2) * (0.5 + 0.5 * fbm(w, h, 6, 4, seed=5))
    img = mix(img, col(0.42, 0.42, 0.55), mist * 0.6)
    hill = poly_mask(w, h, [(0.25, 1), (0.38, 0.74), (0.52, 0.66), (0.72, 0.64), (0.86, 0.7), (1, 0.78), (1, 1)], 1.5)
    img = mix(img, col(0.06, 0.06, 0.1), hill)
    # the abbey: a broken nave wall with lancets, the east window's tall gable, a tower
    ruin = np.zeros((h, w), np.float32)
    ruin = np.maximum(ruin, poly_mask(w, h, [(0.5, 0.67), (0.5, 0.5), (0.53, 0.48), (0.56, 0.51), (0.6, 0.47), (0.63, 0.5), (0.66, 0.46),
                                           (0.69, 0.5), (0.69, 0.66)], 0.6))
    ruin = np.maximum(ruin, poly_mask(w, h, [(0.68, 0.65), (0.68, 0.4), (0.73, 0.3), (0.78, 0.4), (0.78, 0.66)], 0.6))
    ruin = np.maximum(ruin, poly_mask(w, h, [(0.47, 0.67), (0.47, 0.32), (0.485, 0.3), (0.5, 0.29), (0.515, 0.32), (0.515, 0.67)], 0.6))
    holes = np.zeros((h, w), np.float32)
    for cx in (0.535, 0.575, 0.615, 0.655):
        holes = np.maximum(holes, poly_mask(w, h, [(cx - 0.008, 0.62), (cx - 0.008, 0.555), (cx, 0.535), (cx + 0.008, 0.555), (cx + 0.008, 0.62)]))
    holes = np.maximum(holes, poly_mask(w, h, [(0.715, 0.6), (0.715, 0.43), (0.73, 0.38), (0.745, 0.43), (0.745, 0.6)]))
    holes = np.maximum(holes, poly_mask(w, h, [(0.487, 0.42), (0.487, 0.37), (0.493, 0.355), (0.499, 0.37), (0.499, 0.42)]))
    ruin = ruin * (1 - holes)
    stone = mix(col(0.07, 0.07, 0.11), col(0.2, 0.2, 0.28), smooth(0.85, 0.5, x) * 0.6)    # moonlit from the left
    img = mix(img, stone, ruin)
    # a warm candle in one lancet
    img = img + col(1.0, 0.6, 0.25) * (ellipse_mask(w, h, 0.575, 0.6, 0.006, 0.01, 4) * 0.9)[..., None]
    # the oak and gravestones in the foreground
    segs = []
    tree(segs, 0.13, 1.0, math.pi / 2 + 0.05, 0.22, 26, 8, rng, droop=0.05)
    oak = lines_mask(w, h, segs, 0.8)
    img = mix(img, col(0.025, 0.025, 0.04), oak)
    for gx, gh in ((0.36, 0.06), (0.41, 0.045), (0.82, 0.05), (0.9, 0.065)):
        gy = 0.95
        stone_m = poly_mask(w, h, [(gx - 0.012, gy), (gx - 0.012, gy - gh), (gx, gy - gh - 0.015), (gx + 0.012, gy - gh), (gx + 0.012, gy)], 0.5)
        img = mix(img, col(0.1, 0.1, 0.14), stone_m)
    fg = poly_mask(w, h, [(0, 0.9), (0.3, 0.93), (0.6, 0.91), (1, 0.94), (1, 1), (0, 1)], 2)
    img = mix(img, col(0.03, 0.035, 0.05), fg)
    img, hgt = paint(img, rng, 70000, (8, 24), (3, 6))
    return finish(img, w, h), hgt


def bloodmoon():
    """A wolf howling on a crag at a huge crimson moon over ridges of pines."""
    w, h = 2048, 1536
    rng = np.random.default_rng(22)
    x, y = grid(w, h)
    img = mix(col(0.04, 0.01, 0.02), col(0.36, 0.06, 0.05), smooth(0.0, 0.85, y))
    clouds = fbm(w, h, 4, 6, seed=9)
    img = mix(img, col(0.18, 0.03, 0.04), smooth(0.55, 0.75, clouds) * 0.7)
    moon(img, w, h, 0.58, 0.42, 0.2, (0.9, 0.32, 0.18), 0.8, halo=2.2)
    for k, (base, c) in enumerate(((0.66, (0.16, 0.03, 0.04)), (0.74, (0.09, 0.02, 0.03)), (0.84, (0.04, 0.01, 0.015)))):
        pts = [(0, 1)]
        xx = 0.0
        while xx <= 1.02:
            pts.append((xx, base + 0.03 * math.sin(xx * (5 + k * 3) + k)))
            hgt_ = rng.uniform(0.03, 0.07) * (1 + 0.4 * k)
            pts += [(xx + 0.006, base - hgt_ * 0.4), (xx + 0.012, base - hgt_ * 0.3), (xx + 0.018, base - hgt_), (xx + 0.024, base - hgt_ * 0.3),
                    (xx + 0.03, base - hgt_ * 0.4)]
            xx += rng.uniform(0.028, 0.045)
        pts.append((1, 1))
        img = mix(img, col(*c), poly_mask(w, h, pts, 1.2))
    crag = poly_mask(w, h, [(0.0, 1.0), (0.0, 0.7), (0.08, 0.66), (0.18, 0.6), (0.27, 0.58), (0.33, 0.62), (0.4, 0.72), (0.46, 1.0)], 1.0)
    img = mix(img, col(0.02, 0.005, 0.01), crag)
    # the wolf, head raised, on the crag's top
    wolf = [(0.2, 0.585), (0.205, 0.56), (0.215, 0.545), (0.24, 0.535), (0.265, 0.53), (0.278, 0.5), (0.285, 0.47), (0.29, 0.44),
            (0.302, 0.415), (0.31, 0.405), (0.305, 0.43), (0.315, 0.425), (0.312, 0.45), (0.3, 0.47), (0.298, 0.5), (0.295, 0.54),
            (0.298, 0.585), (0.29, 0.586), (0.286, 0.55), (0.272, 0.56), (0.268, 0.586), (0.26, 0.586), (0.258, 0.56), (0.235, 0.56),
            (0.232, 0.586), (0.224, 0.586), (0.222, 0.565), (0.205, 0.575), (0.19, 0.6), (0.18, 0.59), (0.195, 0.57)]
    img = mix(img, col(0.01, 0.004, 0.006), poly_mask(w, h, wolf, 0.6))
    # a crimson rim light on the wolf from the moon
    rim = poly_mask(w, h, [(px + 0.003, py) for px, py in wolf], 0.6) * (1 - poly_mask(w, h, wolf, 0.0))
    img = img + col(0.5, 0.1, 0.06) * rim[..., None]
    img, hgt = paint(img, rng, 60000, (8, 22), (3, 6))
    return finish(img, w, h), hgt


def stretched(w, h, sx, sy, octaves, seed):
    """fbm squashed: noise made at w/sx by h/sy and resized back, so its features run long (sx > sy: horizontal)."""
    small = fbm(max(8, int(w / sx)), max(8, int(h / sy)), 6, octaves, seed=seed)
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def load_rgba(name):
    return np.asarray(Image.open(os.path.join(OUT, name)).convert("RGBA"), np.float32) / 255


def place_alpha(w, h, alpha, cx, cy, height):
    """Scale an alpha silhouette (cropped to its bounds) to `height` (of the canvas) and centre it at (cx, cy)."""
    ys, xs = np.nonzero(alpha > 0.5)
    a = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ph = int(height * h)
    pw = max(1, int(a.shape[1] * ph / a.shape[0]))
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((pw, ph), Image.LANCZOS)
    out = Image.new("L", (w, h), 0)
    out.paste(im, (int(cx * w - pw / 2), int(cy * h - ph / 2)))
    return np.asarray(out, np.float32) / 255


def catmull(pts, n=12, closed=True):
    """A smooth closed Catmull-Rom curve through the points."""
    P_ = pts + pts[:3] if closed else pts
    out = []
    m = len(pts) if closed else len(pts) - 3
    for i in range(m):
        p0, p1, p2, p3 = P_[i], P_[i + 1], P_[i + 2], P_[i + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    return out


def spline_mask(w, h, pts, cx=0.0, cy=0.0, scale=1.0, flip=False, ss=3):
    """An anti-aliased filled silhouette from a smooth curve through pts (unit coords), placed at (cx, cy) with scale."""
    curve = catmull(pts)
    W, H = w * ss, h * ss
    im = Image.new("L", (W, H), 0)
    xy = [((cx + ((1 - x) if flip else x) * scale) * W, (cy + y * scale * w / h) * H) for x, y in curve]
    ImageDraw.Draw(im).polygon(xy, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


# a lady in profile, facing left: a chignon at the back of the head, a fine nose and lips, a slender neck, a ruffled
# collar (unit square, y down)
PROFILE = [(0.8, 0.97), (0.74, 0.85), (0.64, 0.76), (0.6, 0.66), (0.6, 0.56), (0.63, 0.48), (0.68, 0.42), (0.75, 0.39), (0.78, 0.33),
           (0.76, 0.26), (0.7, 0.22), (0.64, 0.2), (0.6, 0.15), (0.52, 0.11), (0.43, 0.11), (0.36, 0.14), (0.32, 0.19), (0.305, 0.24),
           (0.302, 0.28), (0.296, 0.305), (0.288, 0.318), (0.287, 0.33), (0.275, 0.36), (0.258, 0.39), (0.25, 0.403), (0.262, 0.41),
           (0.277, 0.418), (0.278, 0.43), (0.27, 0.438), (0.279, 0.447), (0.272, 0.456), (0.284, 0.468), (0.28, 0.485), (0.295, 0.505),
           (0.33, 0.52), (0.355, 0.56), (0.36, 0.62), (0.37, 0.67), (0.345, 0.69), (0.36, 0.71), (0.335, 0.735), (0.33, 0.78), (0.3, 0.86),
           (0.25, 0.97)]

# a raven perched, facing left: a heavy beak, shaggy throat hackles, the wing folded, a wedge tail, feet on a branch
RAVEN = [(0.1, 0.305), (0.17, 0.28), (0.24, 0.255), (0.3, 0.225), (0.36, 0.215), (0.42, 0.23), (0.47, 0.27), (0.53, 0.32), (0.62, 0.38),
         (0.72, 0.46), (0.82, 0.56), (0.93, 0.67), (0.96, 0.72), (0.9, 0.73), (0.79, 0.67), (0.68, 0.63), (0.6, 0.645), (0.53, 0.66),
         (0.52, 0.72), (0.515, 0.78), (0.49, 0.8), (0.455, 0.8), (0.47, 0.78), (0.475, 0.72), (0.46, 0.66), (0.4, 0.62), (0.34, 0.56),
         (0.3, 0.49), (0.29, 0.445), (0.27, 0.41), (0.26, 0.385), (0.235, 0.36), (0.19, 0.335), (0.13, 0.318)]


def ghostship():
    """A pale ghost galleon with tattered sails in a moonlit storm; a fork of lightning far off."""
    w, h = 2048, 1365
    rng = np.random.default_rng(23)
    x, y = grid(w, h)
    clouds = fbm(w, h, 4, 7, seed=4)
    img = mix(col(0.03, 0.05, 0.07), col(0.17, 0.23, 0.27), smooth(0.35, 0.8, clouds))
    hole = np.exp(-(((x - 0.7) * 1.4) ** 2 + ((y - 0.22) * 2.2) ** 2) * 9)
    img = mix(img, col(0.5, 0.58, 0.6), hole * 0.8)
    moon(img, w, h, 0.71, 0.2, 0.035, (0.9, 0.95, 0.92), 0.6)
    segs, px, py = [], 0.2, 0.05
    for k in range(9):
        nx, ny = px + rng.uniform(-0.03, 0.03), py + 0.055
        segs.append((px, py, nx, ny, 3))
        if k == 4:
            segs.append((nx, ny, nx + 0.05, ny + 0.08, 2))
        px, py = nx, ny
    img = img + col(0.8, 0.85, 1.0) * (lines_mask(w, h, segs, 1.0) + lines_mask(w, h, segs, 12) * 0.35)[..., None]
    # the sea: long swells that grow toward us, a hazy horizon, the moon's broken path, foam streaks
    hz = 0.58
    depth = smooth(hz, 1.0, y)
    far, near = stretched(w, h, 10, 1, 5, 41), stretched(w, h, 4, 1, 5, 42)
    swell = far * (1 - depth) + near * depth
    water = mix(col(0.02, 0.05, 0.06), col(0.12, 0.2, 0.22), smooth(0.35, 0.75, swell) * (0.4 + 0.6 * depth))
    glint = stretched(w, h, 14, 1, 3, 43)
    path = np.exp(-((x - 0.71) / (0.03 + 0.16 * depth)) ** 2) * smooth(0.55, 0.8, glint)
    water = water + col(0.55, 0.62, 0.58) * (path * 0.8)[..., None]
    foam = smooth(0.78, 0.86, stretched(w, h, 6, 1, 3, 44)) * depth
    water = mix(water, col(0.55, 0.62, 0.6), foam * 0.45)
    sea = smooth(hz - 0.004, hz + 0.004, y)
    img = mix(img, water, sea)
    img = mix(img, col(0.24, 0.3, 0.33), np.exp(-((y - hz) / 0.012) ** 2) * 0.6)   # horizon haze
    # the ghost ship: a curved hull with a raised stern, a bowsprit, three masts with yards and tattered sails
    hull = [(0.3, 0.585), (0.33, 0.615), (0.37, 0.64), (0.45, 0.655), (0.55, 0.655), (0.6, 0.64), (0.625, 0.6), (0.63, 0.555), (0.6, 0.56),
            (0.6, 0.585), (0.42, 0.592), (0.36, 0.585)]
    ship = poly_mask(w, h, hull, 0.8)
    ship = np.maximum(ship, lines_mask(w, h, [(0.31, 0.585, 0.24, 0.53, 4), (0.24, 0.53, 0.41, 0.3, 2), (0.24, 0.53, 0.33, 0.58, 2)], 0.5))
    for mx, top in ((0.405, 0.3), (0.48, 0.26), (0.555, 0.33)):
        ship = np.maximum(ship, lines_mask(w, h, [(mx, 0.6, mx, top, 4)], 0.5))
        for k, (sy, sw, sh) in enumerate(((top + 0.03, 0.024, 0.05), (top + 0.1, 0.031, 0.06), (top + 0.18, 0.036, 0.065))):
            ship = np.maximum(ship, lines_mask(w, h, [(mx - sw - 0.008, sy, mx + sw + 0.008, sy, 3)], 0.4))
            pts = [(mx - sw, sy)] + [(mx - sw + 2 * sw * t, sy - 0.012 * math.sin(math.pi * t)) for t in np.linspace(0.1, 0.9, 5)] + [(mx + sw, sy)]
            for t in np.linspace(1, 0, 12):
                pts.append((mx - sw + 2 * sw * t, sy + sh * (0.75 + 0.25 * math.sin(t * 23 + k * 2 + mx * 40))))
            sail = poly_mask(w, h, pts, 1.0)
            hx, hy = rng.uniform(mx - sw * 0.5, mx + sw * 0.5), rng.uniform(sy + sh * 0.35, sy + sh * 0.65)
            sail = sail * (1 - 0.7 * ellipse_mask(w, h, hx, hy, rng.uniform(0.003, 0.006), rng.uniform(0.004, 0.008), 1.5))
            ship = np.maximum(ship, sail * 0.85)
    ship = ship * (0.65 + 0.35 * fbm(w, h, 30, 3, seed=12))
    glow = np.asarray(Image.fromarray((ship * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
    img = img + col(0.3, 0.5, 0.42) * (glow * 0.45)[..., None]
    img = mix(img, col(0.64, 0.8, 0.74), ship * 0.6)
    refl = np.flipud(ship)
    shift = int((2 * 0.655 - 1.0) * h)
    refl = np.roll(refl, shift, axis=0) * sea * 0.18 * (0.5 + 0.5 * near)
    img = img + col(0.4, 0.55, 0.5) * refl[..., None]
    img, hgt = paint(img, rng, 70000, (8, 26), (3, 6), flow=(stretched(w, h, 6, 1, 3, 45) - 0.5) * 0.8)
    return finish(img, w, h), hgt


def raven_still():
    """The 3D still life (paint_renders.py: skull, books, quill, candle), graded warm, the raven painted onto the skull's
    crown facing the flame with a candlelit sheen on its feathers, then painted over."""
    rng = np.random.default_rng(24)
    src = load_rgba("_paint_raven_still.png")[..., :3]
    h, w, _ = src.shape
    x, y = grid(w, h)
    img = np.clip(src ** 0.9 * 1.15, 0, 1) * col(1.0, 0.93, 0.82)
    rs, cx, cy = 0.5, 0.18, 0.165
    rav = spline_mask(w, h, RAVEN, cx, cy, rs, flip=True)
    img = mix(img, col(0.012, 0.012, 0.02), rav)
    flame_x, flame_y = 0.88, 0.36
    toward = smooth(0.25, 0.65, x) * np.exp(-(((x - flame_x) * 1.2) ** 2 + ((y - flame_y) * 1.2) ** 2) * 3)
    edge = rav - spline_mask(w, h, RAVEN, cx - 0.006, cy, rs, flip=True)
    img = img + col(0.55, 0.42, 0.3) * (np.clip(edge, 0, 1) * toward * 1.4)[..., None]
    img = img + col(0.16, 0.17, 0.26) * (rav * toward * 0.5)[..., None]
    ex, ey = cx + (1 - 0.29) * rs, cy + 0.27 * rs * w / h
    img = img + col(0.9, 0.75, 0.45) * ellipse_mask(w, h, ex, ey, 0.004, 0.003, 0.5)[..., None]
    img, hgt = paint(img, rng, 55000, (5, 15), (2, 4), jitter=0.035)
    return finish(img, w, h), hgt


def cameo():
    """A Victorian silhouette portrait: a lady in profile in black on a crimson oval with a cream line."""
    w, h = 1536, 2048
    rng = np.random.default_rng(25)
    x, y = grid(w, h)
    d = np.sqrt(((x - 0.5) / 0.46) ** 2 + ((y - 0.5) / 0.47) ** 2)
    img = mix(col(0.44, 0.05, 0.06), col(0.2, 0.02, 0.03), np.clip(d, 0, 1))
    ring = smooth(0.9, 0.905, d) * smooth(0.925, 0.92, d)
    img = mix(img, col(0.85, 0.78, 0.6), ring)
    sc = 0.8
    sil = spline_mask(w, h, PROFILE, 0.5 - 0.5 * sc, 0.5 - 0.5 * sc * w / h + 0.02, sc) * smooth(0.89, 0.86, d)
    img = mix(img, col(0.018, 0.014, 0.018), sil)
    # a cream cameo at the throat
    img = mix(img, col(0.85, 0.78, 0.6), ellipse_mask(w, h, 0.5 - 0.5 * sc + 0.42 * sc, 0.5 - 0.5 * sc * w / h + 0.02 + 0.66 * sc * w / h,
                                                       0.014, 0.011, 1.0))
    # a gilt name ribbon below the bust
    img = mix(img, col(0.7, 0.55, 0.22), lines_mask(w, h, [(0.36, 0.86, 0.64, 0.86, 10)], 1.0))
    img, hgt = paint(img, rng, 38000, (5, 14), (2, 4), jitter=0.02)
    return finish(img, w, h), hgt


def triptych():
    """Three arched panels in one image (a third each): gold ground and the school crest's symbols in tempera: the crescent
    moon and stars, the raven on the key under a crimson halo, the candle in gilt rays."""
    w, h = 2048, 1365
    rng = np.random.default_rng(26)
    x, y = grid(w, h)
    gold = mix(col(0.55, 0.38, 0.12), col(0.86, 0.67, 0.3), fbm(w, h, 30, 4, seed=3))
    punch = smooth(0.8, 0.82, (np.sin(x * w * 0.16) * np.sin(y * h * 0.16)) * 0.5 + 0.5) * 0.1
    img = gold * (1 - punch[..., None])
    ink, red, pale = col(0.04, 0.03, 0.03), col(0.48, 0.05, 0.05), col(0.88, 0.84, 0.72)
    # left: the crescent moon and stars
    m1 = ellipse_mask(w, h, 0.165, 0.45, 0.08, 0.12, 0.8) * (1 - ellipse_mask(w, h, 0.2, 0.43, 0.075, 0.115, 0.8))
    img = mix(img, pale, m1)
    for sx, sy in ((0.08, 0.22), (0.26, 0.27), (0.23, 0.7), (0.09, 0.74), (0.27, 0.52), (0.12, 0.33)):
        st = lines_mask(w, h, [(sx - 0.012, sy, sx + 0.012, sy, 4), (sx, sy - 0.018, sx, sy + 0.018, 4),
                               (sx - 0.007, sy - 0.011, sx + 0.007, sy + 0.011, 2), (sx - 0.007, sy + 0.011, sx + 0.007, sy - 0.011, 2)], 0.6)
        img = mix(img, pale, st)
    # centre: the crimson halo, the key, the raven standing on it
    halo = ellipse_mask(w, h, 0.5, 0.36, 0.1, 0.15, 0.8) * (1 - ellipse_mask(w, h, 0.5, 0.36, 0.092, 0.138, 0.8))
    img = mix(img, red, halo)
    key = lines_mask(w, h, [(0.42, 0.66, 0.58, 0.66, 12), (0.565, 0.66, 0.565, 0.7, 9), (0.54, 0.66, 0.54, 0.69, 9)], 0.6)
    key = np.maximum(key, ellipse_mask(w, h, 0.41, 0.66, 0.026, 0.039, 0.8) * (1 - ellipse_mask(w, h, 0.41, 0.66, 0.012, 0.018)))
    img = mix(img, col(0.3, 0.22, 0.1), key)
    rs = 0.227
    rav = spline_mask(w, h, RAVEN, 0.5 - 0.5 * rs, 0.378, rs)
    img = mix(img, ink, rav)
    # right: the candle on its pricket in gilt rays
    rays = np.zeros((h, w), np.float32)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        rays = np.maximum(rays, lines_mask(w, h, [(0.83, 0.36, 0.83 + math.cos(a) * 0.11, 0.36 + math.sin(a) * 0.17, 5)], 0.6))
    img = mix(img, col(0.95, 0.78, 0.36), rays * 0.8)
    img = mix(img, pale, poly_mask(w, h, [(0.815, 0.72), (0.815, 0.42), (0.845, 0.42), (0.845, 0.72)], 0.6))
    img = mix(img, col(0.97, 0.72, 0.26), ellipse_mask(w, h, 0.83, 0.38, 0.012, 0.036, 1.0))
    img = mix(img, col(0.3, 0.22, 0.1), poly_mask(w, h, [(0.78, 0.76), (0.88, 0.76), (0.86, 0.72), (0.8, 0.72)], 0.6))
    # dark tempera outlines round the figures
    edges = np.clip(m1 + halo + key + rav, 0, 1)
    out = np.asarray(Image.fromarray((edges * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1)),
                     np.float32) / 255
    img = mix(img, ink, np.clip(out * 2, 0, 1) * 0.6)
    img, hgt = paint(img, rng, 30000, (4, 12), (2, 3), jitter=0.025)
    return finish(img, w, h), hgt


PAINTINGS = {"PaintingAbbey": abbey, "PaintingBloodMoon": bloodmoon, "PaintingGhostShip": ghostship, "PaintingRaven": raven_still,
             "CameoSilhouette": cameo, "Triptych": triptych}


def canvas_maps():
    """The shared canvas normal (weave + a soft impasto field) and roughness (varnish: fairly glossy)."""
    n = 1024
    x, y = grid(n, n)
    weave = (np.sin(x * n * 0.9) * 0.5 + 0.5) * (np.sin(y * n * 0.9 + np.sin(x * n * 0.45) * 0.5) * 0.5 + 0.5)
    hgt = weave * 0.4 + fbm(n, n, 16, 4, seed=31) * 0.6
    gx = np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)
    gy = np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)
    nrm = np.dstack([-gx * 2.0, gy * 2.0, np.ones_like(hgt)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, "Canvas_normal.png"))
    rough = 0.42 + 0.2 * fbm(n, n, 12, 3, seed=32)
    Image.fromarray((rough * 255).astype(np.uint8)).save(os.path.join(OUT, "Canvas_rough.png"))
    Image.fromarray(np.zeros((64, 64), np.uint8)).save(os.path.join(OUT, "Canvas_metal.png"))
    print("wrote canvas maps")


if __name__ == "__main__":
    want = sys.argv[1:] or list(PAINTINGS)
    for name in want:
        img, _ = PAINTINGS[name]()
        save(name, img)
    canvas_maps()
