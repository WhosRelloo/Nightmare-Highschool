"""Nightmare Highschool - Developer Product icon generator.

Renders the 8 dev-product icons (512x512 PNG) plus a labelled contact sheet.
Everything is procedural: shapes are drawn as masks, turned into height maps
(distance transforms), lit with a small normal-map shader (candle-gold key light
from the top-left, crimson rim light from the bottom-right) and composited at 2x
supersampling, then downsampled.  No external art is used.

Re-run (Python 3 with Pillow, numpy, scipy):

    python E:/Nightmare-Highschool/tools/dev-products/make_dev_product_icons.py
    python E:/Nightmare-Highschool/tools/dev-products/make_dev_product_icons.py Clan1 Race3   # just some

Output: E:/Nightmare-Highschool/art/dev-products/<Key>.png and contact_sheet.png
(override the folder with --out <dir>).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

# ----------------------------------------------------------------------------
# setup
# ----------------------------------------------------------------------------
SS = 2                      # supersampling factor
N = 512 * SS                # working resolution
OUT_DIR = r"E:\Nightmare-Highschool\art\dev-products"
FONTS = r"C:\Windows\Fonts"
F_PLATE = os.path.join(FONTS, "palab.ttf")      # Palatino Linotype Bold (lining numerals)
F_RIBBON = os.path.join(FONTS, "georgiab.ttf")
F_HAND = os.path.join(FONTS, "segoesc.ttf")     # handwriting for the ledger
F_LABEL = os.path.join(FONTS, "georgia.ttf")


def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0


GOLD = hexc("#EBCD78")
DGOLD = hexc("#966E32")
CRIMSON = hexc("#C8283C")
INK0 = hexc("#0E0C12")
INK1 = hexc("#24202A")


def nrm(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v)


LIGHT = nrm([-0.45, -0.65, 0.62])      # toward the key light (image y points down)
HALF = nrm(LIGHT + np.array([0, 0, 1], np.float32))
RIM = nrm([0.62, 0.62, 0.48])          # crimson rim light from bottom-right

YY, XX = np.mgrid[0:N, 0:N].astype(np.float32) / SS   # coordinates in 512-space


def dist(cx, cy):
    return np.hypot(XX - cx, YY - cy)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


FALL = (1.14 - 0.34 * np.clip(dist(110, 60) / 560.0, 0, 1)).astype(np.float32)

# ----------------------------------------------------------------------------
# masks
# ----------------------------------------------------------------------------


class M:
    """Binary mask painter working in 512-space coordinates."""

    def __init__(self):
        self.img = Image.new("L", (N, N), 0)
        self.d = ImageDraw.Draw(self.img)

    def poly(self, pts, fill=255):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)
        return self

    def circle(self, cx, cy, r, fill=255):
        self.d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=fill)
        return self

    def rect(self, x0, y0, x1, y1, radius=0, fill=255):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=radius * SS, fill=fill)
        return self

    def line(self, pts, width, fill=255):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=max(1, int(round(width * SS))), joint="curve")
        return self

    def rotate(self, ang, cx, cy):
        self.img = self.img.rotate(ang, resample=Image.BILINEAR, center=(cx * SS, cy * SS))
        self.d = ImageDraw.Draw(self.img)
        return self

    def arr(self):
        return (np.asarray(self.img, np.float32) > 127).astype(np.float32)


def poly_mask(pts):
    return M().poly(pts).arr()


def rot_pts(pts, ang_deg, cx, cy):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def edt(mask):
    return ndi.distance_transform_edt(mask > 0.5).astype(np.float32) / SS


def dilate(mask, r):
    return (edt(1 - mask) <= r).astype(np.float32)


def bevel(mask, w, kind="round"):
    t = np.clip(edt(mask) / w, 0, 1)
    if kind == "round":
        p = np.sqrt(1 - (1 - t) ** 2)
    elif kind == "lin":
        p = t
    else:
        p = t * t * (3 - 2 * t)
    return p * w


def soft(mask, s=0.45):
    return ndi.gaussian_filter(mask.astype(np.float32), s * SS)


# ----------------------------------------------------------------------------
# shading
# ----------------------------------------------------------------------------


def normals(h, blur=0.5):
    if blur > 0:
        h = ndi.gaussian_filter(h, blur * SS)
    gy, gx = np.gradient(h)
    n = np.empty(h.shape + (3,), np.float32)
    n[..., 0] = -gx * SS
    n[..., 1] = -gy * SS
    n[..., 2] = 1.0
    n /= np.sqrt((n ** 2).sum(-1, keepdims=True))
    return n


def ramp(t, stops):
    pos = [s[0] for s in stops]
    cols = np.array([s[1] for s in stops], np.float32)
    return np.stack([np.interp(t, pos, cols[:, c]) for c in range(3)], -1).astype(np.float32)


MAT = {
    "gold": dict(stops=[(0, (0.07, 0.04, 0.02)), (0.30, (0.30, 0.19, 0.07)), (0.55, DGOLD * 1.05),
                        (0.78, GOLD), (1.0, (1.0, 0.97, 0.86))], spec=0.85, shin=55, rim=0.55),
    "wax": dict(stops=[(0, (0.09, 0.01, 0.02)), (0.35, (0.28, 0.03, 0.06)), (0.6, (0.56, 0.07, 0.11)),
                       (0.8, (0.80, 0.14, 0.18)), (1.0, (0.96, 0.38, 0.38))], spec=0.40, shin=30, rim=0.6),
    "blood": dict(stops=[(0, (0.07, 0.0, 0.01)), (0.35, (0.26, 0.01, 0.04)), (0.6, (0.55, 0.04, 0.09)),
                         (0.82, (0.82, 0.10, 0.15)), (1.0, (1.0, 0.36, 0.36))], spec=1.4, shin=110, rim=0.9),
    "silver": dict(stops=[(0, (0.05, 0.05, 0.07)), (0.35, (0.22, 0.22, 0.27)), (0.6, (0.55, 0.56, 0.62)),
                          (0.8, (0.86, 0.87, 0.92)), (1.0, (1, 1, 1))], spec=0.9, shin=70, rim=0.55),
    "obsid": dict(stops=[(0, (0.02, 0.02, 0.03)), (0.5, (0.075, 0.065, 0.09)), (0.62, (0.115, 0.10, 0.14)),
                         (0.85, (0.24, 0.21, 0.28)), (1.0, (0.38, 0.34, 0.42))], spec=0.35, shin=60, rim=0.4),
    "parch": dict(stops=[(0, (0.30, 0.22, 0.13)), (0.4, (0.60, 0.50, 0.34)), (0.62, (0.86, 0.78, 0.60)),
                         (0.85, (0.95, 0.90, 0.75)), (1.0, (1.0, 0.97, 0.88))], spec=0.05, shin=10, rim=0.12),
    "leather": dict(stops=[(0, (0.05, 0.01, 0.015)), (0.4, (0.18, 0.03, 0.04)), (0.62, (0.32, 0.05, 0.07)),
                           (0.85, (0.50, 0.10, 0.11)), (1.0, (0.70, 0.22, 0.20))], spec=0.18, shin=16, rim=0.35),
    "silk": dict(stops=[(0, (0.04, 0.005, 0.01)), (0.4, (0.16, 0.02, 0.035)), (0.62, (0.30, 0.04, 0.06)),
                        (0.85, (0.55, 0.10, 0.12)), (1.0, (0.85, 0.35, 0.33))], spec=0.45, shin=22, rim=0.5),
    "feather": dict(stops=[(0, (0.10, 0.01, 0.02)), (0.4, (0.38, 0.04, 0.07)), (0.62, (0.66, 0.09, 0.14)),
                           (0.85, (0.86, 0.22, 0.24)), (1.0, (1.0, 0.52, 0.46))], spec=0.25, shin=20, rim=0.4),
    "ivory": dict(stops=[(0, (0.25, 0.21, 0.16)), (0.45, (0.62, 0.56, 0.46)), (0.62, (0.85, 0.80, 0.68)),
                         (0.85, (0.96, 0.93, 0.84)), (1.0, (1, 1, 0.96))], spec=0.6, shin=40, rim=0.3),
}


def mat_color(n, m, fall=True):
    m = MAT[m] if isinstance(m, str) else m
    ndl = np.clip(n @ LIGHT, 0, 1)
    col = ramp(ndl, m["stops"])
    if fall:
        col *= FALL[..., None]
    sp = (np.clip(n @ HALF, 0, 1) ** m["shin"]) * m["spec"]
    rim = (np.clip((n @ RIM - 0.52) / 0.48, 0, 1) ** 2) * m["rim"]
    col += sp[..., None] * np.array([1.0, 0.95, 0.85], np.float32)
    col += rim[..., None] * CRIMSON
    return col


def over(c, rgb, a):
    a = np.clip(a, 0, 1)[..., None]
    return c * (1 - a) + rgb * a


def screen(c, add):
    return 1 - (1 - c) * (1 - np.clip(add, 0, 1))


def shadow(c, mask, dx=5, dy=8, blur=7, op=0.65):
    sh = np.roll(mask, (int(dy * SS), int(dx * SS)), (0, 1))
    sh = soft(sh, blur) * op
    return c * (1 - np.clip(sh, 0, 1)[..., None])


def glow(c, mask, color, blur, amt):
    g = soft(mask, blur) * amt
    return screen(c, np.asarray(color, np.float32) * g[..., None])


def put(c, mask, col, sh=(5, 8, 7, 0.65), aa=0.45):
    if sh:
        c = shadow(c, mask, *sh)
    return over(c, col, soft(mask, aa))


def sparkle(c, x, y, size, amt=1.0, col=(1.0, 0.93, 0.75)):
    dx, dy = np.abs(XX - x), np.abs(YY - y)
    th = 0.55
    arms = np.exp(-(dy / th) ** 2) * np.exp(-dx / (size * 0.35)) + np.exp(-(dx / th) ** 2) * np.exp(-dy / (size * 0.35))
    diag = (np.exp(-((dx - dy) / th) ** 2) * np.exp(-(dx + dy) / (size * 0.18))) * 0.5
    core = np.exp(-(dx ** 2 + dy ** 2) / (2 * (size * 0.12) ** 2))
    v = (arms + diag + core) * amt
    return screen(c, np.asarray(col, np.float32) * v[..., None])


def noise(seed, scale, shape=(N, N)):
    rng = np.random.default_rng(seed)
    small = rng.standard_normal((max(2, shape[0] // scale), max(2, shape[1] // scale))).astype(np.float32)
    small = ndi.gaussian_filter(small, 1.0)
    z = ndi.zoom(small, (shape[0] / small.shape[0], shape[1] / small.shape[1]), order=3)[: shape[0], : shape[1]]
    return (z - z.mean()) / (z.std() + 1e-6)


# ----------------------------------------------------------------------------
# text
# ----------------------------------------------------------------------------


def font(path, size):
    return ImageFont.truetype(path, int(round(size * SS)))


def text_mask(parts, cx, cy, tracking=0.0):
    """parts = [(text, font)], baseline aligned, centred on cap height. Returns (mask, width512)."""
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    chars = sum(len(s) for s, _ in parts)
    total = sum(f.getlength(s) for s, f in parts) + tracking * SS * (chars - 1)
    cap = -parts[-1][1].getbbox("H", anchor="ls")[1]
    x = cx * SS - total / 2
    base = cy * SS + cap / 2
    for s, f in parts:
        for ch in s:
            d.text((x, base), ch, font=f, fill=255, anchor="ls")
            x += f.getlength(ch) + tracking * SS
    return np.asarray(img, np.float32) / 255.0, total / SS


# ----------------------------------------------------------------------------
# common pieces: background, frame, badge plate, ribbon
# ----------------------------------------------------------------------------


def background(cy=245, crim=0.36, gold=0.0, gold_r=150, seed=3):
    r = dist(256, 256) / 256.0
    t = smoothstep(0.0, 1.3, r)[..., None]
    c = INK1 * 1.2 * (1 - t) + INK0 * 0.75 * t
    c = c * (1 + 0.07 * noise(seed, 16)[..., None])
    # faint rose-window tracery inside the medallion
    tr = M()
    for k in range(16):
        a = 2 * math.pi * k / 16 + math.pi / 16
        tr.line([(256 + 70 * math.cos(a), 256 + 70 * math.sin(a)), (256 + 218 * math.cos(a), 256 + 218 * math.sin(a))], 1.4)
        ax, ay = 256 + 192 * math.cos(a + math.pi / 16), 256 + 192 * math.sin(a + math.pi / 16)
        tr.d.ellipse([(ax - 20) * SS, (ay - 20) * SS, (ax + 20) * SS, (ay + 20) * SS], outline=255, width=int(1.4 * SS))
    for rr in (70, 150, 218):
        tr.d.ellipse([(256 - rr) * SS, (256 - rr) * SS, (256 + rr) * SS, (256 + rr) * SS], outline=255, width=int(1.6 * SS))
    c = over(c, GOLD * 0.55, soft(tr.arr(), 0.5) * 0.06)
    g = np.exp(-(dist(256, cy) / 150.0) ** 2)
    c = screen(c, np.array([0.80, 0.07, 0.13], np.float32) * (g * crim)[..., None])
    if gold:
        gg = np.exp(-(dist(256, cy) / gold_r) ** 2)
        c = screen(c, GOLD * (gg * gold)[..., None])
    c = c * (1 - 0.55 * smoothstep(0.78, 1.45, r))[..., None]
    return c.astype(np.float32)


def frame(c):
    # medallion ring (survives a circular crop)
    r = dist(256, 256)
    ring = ((r <= 231) & (r >= 226.5)).astype(np.float32)
    ring2 = ((r <= 221) & (r >= 219.5)).astype(np.float32)
    beads = np.zeros((N, N), np.float32)
    hb = np.zeros((N, N), np.float32)
    for k in range(48):
        a = 2 * math.pi * (k + 0.5) / 48
        bx, by = 256 + 224 * math.cos(a), 256 + 224 * math.sin(a)
        d2 = (XX - bx) ** 2 + (YY - by) ** 2
        hb += np.sqrt(np.clip(1.6 ** 2 - d2, 0, None))
        beads = np.maximum(beads, (d2 <= 1.6 ** 2).astype(np.float32))
    rm = np.maximum(np.maximum(ring, ring2), beads)
    h = np.sqrt(np.clip(2.25 ** 2 - (r - 228.75) ** 2, 0, None)) + np.sqrt(np.clip(0.75 ** 2 - (r - 220.25) ** 2, 0, None)) + hb
    c = put(c, rm, mat_color(normals(h, 0.3), "gold"), sh=(1.5, 2.5, 2, 0.8))
    # square frame with concave Victorian corners
    def concave(inset, rc):
        m = M().rect(inset, inset, 512 - inset, 512 - inset)
        for x, y in ((10, 10), (502, 10), (10, 502), (502, 502)):
            m.circle(x, y, rc, fill=0)
        return m.arr()
    f1 = concave(10, 24)
    l1 = ((edt(f1) <= 3.2) & (f1 > 0)).astype(np.float32)
    f2 = concave(17, 31)
    l2 = ((edt(f2) <= 1.3) & (f2 > 0)).astype(np.float32)
    fm = np.maximum(l1, l2)
    h = bevel(l1, 1.6) + bevel(l2, 0.65)
    # corner gems + small trefoils pointing inward
    gems = M()
    orn = M()
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cx = 256 - sx * (256 - 21)
        cy = 256 - sy * (256 - 21)
        gems.circle(cx, cy, 5.2)
        tx = 256 - sx * (256 - 46)
        ty = 256 - sy * (256 - 46)
        orn.circle(tx, ty, 3.4)
        orn.circle(tx + sx * 5.5, ty - sy * 1.5, 2.4)
        orn.circle(tx - sx * 1.5, ty + sy * 5.5, 2.4)
        orn.poly([(tx + sx * 2, ty + sy * 2), (tx + sx * 11, ty + sy * 6), (tx + sx * 13, ty + sy * 13), (tx + sx * 6, ty + sy * 11)])
    gm = gems.arr()
    om = orn.arr()
    setting = dilate(gm, 1.6)
    h = h + bevel(om, 1.6) + bevel(setting, 1.2)
    allm = np.maximum(np.maximum(fm, om), setting)
    col = mat_color(normals(h, 0.3), "gold")
    c = put(c, allm, col, sh=(1.5, 2.5, 2, 0.8))
    hg = bevel(gm, 4.0)
    c = put(c, gm, mat_color(normals(hg, 0.3), "blood"), sh=None)
    return c


def plate(c, label, cy=406):
    if label.startswith("x"):
        parts = [("x", font(F_PLATE, 32)), (label[1:], font(F_PLATE, 46))]
        tm, tw = text_mask(parts, 256, cy + 1, tracking=0.5)
    else:
        parts = [(label, font(F_PLATE, 34))]
        tm, tw = text_mask(parts, 256, cy + 1, tracking=2.4)
    w = max(tw + 70, 136)
    hh = 30
    x0, x1, y0, y1 = 256 - w / 2, 256 + w / 2, cy - hh, cy + hh
    k = 18
    pts = [(x0 + k, y0), (x1 - k, y0), (x1, cy), (x1 - k, y1), (x0 + k, y1), (x0, cy)]
    pm = poly_mask(pts)
    back = dilate(pm, 3.0)
    c = shadow(c, back, 3, 7, 7, 0.8)
    c = over(c, np.array([0.05, 0.03, 0.04], np.float32), soft(back))
    d = edt(pm)
    h = np.sqrt(1 - (1 - np.clip(d / 6.0, 0, 1)) ** 2) * 6.0
    h -= 1.1 * np.exp(-((d - 8.5) / 0.9) ** 2)
    ts = soft(tm, 0.8)
    h -= 2.6 * ts
    col = mat_color(normals(h, 0.35), "gold", fall=False)
    col *= (1.10 - 0.22 * np.clip((YY - y0) / (2 * hh), 0, 1))[..., None]
    ink = np.array([0.13, 0.05, 0.04], np.float32)
    col = over(col, ink, np.clip(tm * 1.15, 0, 1) * 0.86)
    c = over(c, col, soft(pm))
    return c


def ribbon(c, text, cy=84):
    f = font(F_RIBBON, 22)
    tm, tw = text_mask([(text, f)], 256, cy, tracking=1.6)
    w = tw + 44
    hh = 18
    x0, x1 = 256 - w / 2, 256 + w / 2
    for s in (-1, 1):
        xe = 256 + s * (w / 2 - 8)
        xo = 256 + s * (w / 2 + 30)
        yt, yb = cy - hh + 10, cy + hh + 10
        tail = poly_mask([(xe, yt), (xo, yt), (xo - s * 11, (yt + yb) / 2), (xo, yb), (xe, yb)])
        ht = bevel(tail, 3) + 2.0 * np.cos(np.clip((YY - (yt + yb) / 2) / hh, -1, 1) * 1.4)
        col = mat_color(normals(ht, 0.4), "gold") * 0.62
        c = put(c, tail, col, sh=(2, 4, 4, 0.7))
        fold = poly_mask([(256 + s * (w / 2 - 1), cy + hh), (256 + s * (w / 2 - 8), cy + hh + 10), (256 + s * (w / 2 - 8), cy + hh - 2)])
        c = over(c, np.array([0.16, 0.09, 0.03], np.float32), soft(fold))
    band = []
    for x in np.linspace(x0, x1, 25):
        band.append((x, cy - hh - 3.0 * (1 - ((x - 256) / (w / 2)) ** 2)))
    for x in np.linspace(x1, x0, 25):
        band.append((x, cy + hh - 3.0 * (1 - ((x - 256) / (w / 2)) ** 2)))
    bm = poly_mask(band)
    hb = bevel(bm, 3) + 3.0 * np.cos(np.clip((YY - cy) / (hh + 3), -1, 1) * 1.45)
    hb -= 1.8 * soft(tm, 0.7)
    col = mat_color(normals(hb, 0.4), "gold", fall=False)
    col = over(col, np.array([0.22, 0.03, 0.05], np.float32), np.clip(tm * 1.1, 0, 1) * 0.9)
    c = put(c, bm, col, sh=(2, 5, 5, 0.75))
    return c


# ----------------------------------------------------------------------------
# subjects
# ----------------------------------------------------------------------------


def shield_pts(cx, cy, s, ang=0.0):
    pts = [(-1.0, -1.0), (-0.5, -0.96), (0.0, -1.04), (0.5, -0.96), (1.0, -1.0), (1.0, -0.15)]
    for t in np.linspace(0, 1, 16)[1:]:
        pts.append((1 - t ** 1.7, -0.15 + 1.38 * t))
    right = pts[5:]
    left = [(-x, y) for x, y in reversed(right[:-1])]
    pts = pts + left
    pts = [(cx + x * 0.78 * s, cy + y * s) for x, y in pts]
    return rot_pts(pts, ang, cx, cy)


def seal(c, cx, cy, R, ang=0.0, seed=0, sh_op=0.7):
    rng = np.random.default_rng(seed)
    dx, dy = XX - cx, YY - cy
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    edge = np.ones_like(r)
    for k, a in ((3, 0.022), (5, 0.016), (7, 0.011), (11, 0.007), (17, 0.004)):
        edge += a * np.sin(k * th + rng.uniform(0, 2 * np.pi))
    for _ in range(int(rng.integers(3, 6))):
        t0 = rng.uniform(-np.pi, np.pi)
        dth = (th - t0 + np.pi) % (2 * np.pi) - np.pi
        edge += rng.uniform(0.04, 0.085) * np.exp(-(dth / rng.uniform(0.12, 0.25)) ** 2)
    outer = (r <= R * edge).astype(np.float32)
    h = bevel(outer, 0.30 * R)
    Ri = 0.70 * R
    inner = (r <= Ri).astype(np.float32)
    h -= 0.11 * R * smoothstep(0, 0.045 * R, edt(inner))
    h += 0.045 * R * np.exp(-((r - Ri * 1.05) / (0.05 * R)) ** 2) * outer
    nb, br, rb = 24, 0.03 * R, 0.62 * R
    a0 = math.radians(ang)
    for i in range(nb):
        a = a0 + 2 * math.pi * i / nb
        d2 = (XX - (cx + rb * math.cos(a))) ** 2 + (YY - (cy + rb * math.sin(a))) ** 2
        h += np.sqrt(np.clip(br * br - d2, 0, None))
    shm = poly_mask(shield_pts(cx, cy - 0.05 * R, 0.40 * R, ang))
    h += bevel(shm, 0.05 * R) + 0.25 * bevel(shm, 0.3 * R) + 0.02 * R * shm
    h += 0.006 * R * noise(seed + 101, 24) * outer + 0.0025 * R * noise(seed + 202, 6) * outer
    n = normals(h, 0.5)
    col = mat_color(n, "wax")
    ss = soft(shm, 0.4)[..., None]
    col = col * (1 - ss) + mat_color(n, "gold") * ss
    s = max(2.0, 0.06 * R)
    return put(c, outer, col, sh=(s * 0.8, s * 1.3, s * 1.2, sh_op))


def silk_tail(c, p0, p1, w):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -dy, dx
    hw = w / 2
    pts = [(x0 + px * hw, y0 + py * hw), (x1 + px * hw, y1 + py * hw), (x1 - dx * w * 0.45, y1 - dy * w * 0.45),
           (x1 - px * hw, y1 - py * hw), (x0 - px * hw, y0 - py * hw)]
    m = poly_mask(pts)
    u = ((XX - x0) * px + (YY - y0) * py) / hw
    h = bevel(m, 2.0) + 0.35 * w * np.sqrt(np.clip(1 - u ** 2, 0, None)) * 0.4
    n = normals(h, 0.5)
    col = mat_color(n, "silk")
    stripe = (((np.abs(u) > 0.62) & (np.abs(u) < 0.74)).astype(np.float32)) * m
    col = over(col, mat_color(n, "gold") * 0.9, soft(stripe, 0.4))
    return put(c, m, col, sh=(4, 6, 6, 0.6))


def medallion(c, cx, cy, R):
    r = dist(cx, cy)
    disc = (r <= R).astype(np.float32)
    inner = (r <= 0.82 * R).astype(np.float32)
    h = bevel(disc, 0.12 * R) - 0.07 * R * smoothstep(0, 0.03 * R, edt(inner))
    h -= 0.012 * R * np.exp(-((r - 0.91 * R) / (0.012 * R)) ** 2)
    n = normals(h, 0.4)
    w = soft(inner, 0.4)[..., None]
    col = mat_color(n, "gold") * (1 - w) + mat_color(n, "obsid") * w
    col = screen(col, CRIMSON * (0.55 * np.exp(-(r / (0.62 * R)) ** 2))[..., None] * w)
    return put(c, disc, col, sh=(5, 9, 8, 0.75))


def nib(c, cx, cy, s, ang=0.0, sh=(3, 5, 4, 0.7)):
    half = [(0.30, -1.0), (0.37, -0.78), (0.45, -0.38), (0.43, -0.10), (0.33, 0.25), (0.19, 0.60), (0.05, 0.95), (0.0, 1.02)]
    pts = [(0.0, -0.94)] + half + [(-x, y) for x, y in reversed(half[:-1])]
    T = lambda P: rot_pts([(cx + x * s, cy + y * s) for x, y in P], ang, cx, cy)
    m = M().poly(T(pts))
    slit = T([(-0.022, 0.05), (0.022, 0.05), (0.012, 1.05), (-0.012, 1.05)])
    m.poly(slit, fill=0)
    hx, hy = T([(0.0, 0.0)])[0]
    m.circle(hx, hy, 0.085 * s, fill=0)
    mask = m.arr()
    a = math.radians(ang)
    u = ((XX - cx) * math.cos(a) + (YY - cy) * math.sin(a)) / s
    h = bevel(mask, 0.05 * s) + 0.14 * s * np.sqrt(np.clip(1 - (u / 0.5) ** 2, 0, None)) * mask
    g = M()
    g.line(T([(x, -0.44 + 0.16 * (x / 0.38) ** 2) for x in np.linspace(-0.38, 0.38, 15)]), 0.028 * s)
    g.line(T([(x, -0.76) for x in (-0.33, 0.33)]), 0.022 * s)
    g.line(T([(x, -0.20 - 0.12 * (1 - (x / 0.30) ** 2)) for x in np.linspace(-0.30, 0.30, 15)]), 0.02 * s)
    h -= 0.025 * s * soft(g.arr() * mask, 0.4)
    col = mat_color(normals(h, 0.35), "silver")
    return put(c, mask, col, sh=sh)


def cross(c, cx, cy, s, sh=(3, 5, 4, 0.7)):
    m = M()
    m.rect(cx - 0.12 * s, cy - 0.98 * s, cx + 0.12 * s, cy + 1.0 * s)
    m.rect(cx - 0.72 * s, cy - 0.42 * s, cx + 0.72 * s, cy - 0.18 * s)
    for x, y in ((0, -1.02), (-0.78, -0.30), (0.78, -0.30), (0, 1.04)):
        m.circle(cx + x * s, cy + y * s, 0.17 * s)
    m.circle(cx, cy - 0.30 * s, 0.24 * s)
    mask = m.arr()
    gem = M().circle(cx, cy - 0.30 * s, 0.13 * s).arr()
    h = bevel(mask, 0.12 * s, "lin")
    h = h - 0.03 * s * smoothstep(0, 0.02 * s, edt(dilate(gem, 0.03 * s)))
    hg = bevel(gem, 0.13 * s) * 0.9 + 0.06 * s * gem
    n = normals(np.maximum(h, hg), 0.35)
    col = mat_color(n, "gold")
    w = soft(gem, 0.4)[..., None]
    col = col * (1 - w) + mat_color(n, "blood") * w
    return put(c, mask, col, sh=sh)


def drop_pts(cx, cy, s, k=1.0, offset=0.0, n=90):
    out = []
    for t in np.linspace(0, 2 * np.pi, n, endpoint=False) + offset:
        x = 0.95 * math.sin(t) * abs(math.sin(t / 2)) ** 1.3
        y = -math.cos(t)
        out.append((cx + s * k * x, cy + s * (0.28 + k * (y - 0.28))))
    return out


def drop(c, cx, cy, s, sh=(3, 5, 4, 0.7)):
    mask = poly_mask(drop_pts(cx, cy, s))
    h = bevel(mask, 0.62 * s, "round")
    n = normals(h, 0.6)
    col = mat_color(n, "blood")
    core = np.exp(-(dist(cx + 0.15 * s, cy + 0.55 * s) / (0.38 * s)) ** 2)
    col = screen(col, CRIMSON * (0.45 * core)[..., None])
    hl = M()
    hl.line([(cx - 0.42 * s + 0.12 * s * math.sin(t), cy + 0.25 * s - 0.4 * s * math.cos(t)) for t in np.linspace(-0.25, 0.9, 10)], 0.07 * s)
    col = screen(col, np.ones(3, np.float32) * (soft(hl.arr() * mask, 0.08 * s) * 0.55)[..., None])
    return put(c, mask, col, sh=sh)


GEM_STOPS = [(0, (0.10, 0.0, 0.02)), (0.3, (0.32, 0.01, 0.05)), (0.55, (0.62, 0.05, 0.10)),
             (0.78, (0.90, 0.16, 0.20)), (1.0, (1.0, 0.62, 0.58))]


def gem_drop(c, cx, cy, s, seed=1, stops=GEM_STOPS, sh=(5, 8, 8, 0.7), core_col=CRIMSON):
    rng = np.random.default_rng(seed)
    K = 16
    d = 2 * np.pi / K
    o = [(x, y, 0.0) for x, y in drop_pts(cx, cy, s, 1.0, 0.0, K)]
    m = [(x, y, 0.20 * s) for x, y in drop_pts(cx, cy, s, 0.74, d / 2, K)]
    t = [(x, y, 0.33 * s) for x, y in drop_pts(cx, cy, s, 0.44, 0.0, K)]
    ctr = (cx - 0.04 * s, cy + 0.22 * s, 0.38 * s)
    tris = []
    for i in range(K):
        j = (i + 1) % K
        tris += [(o[i], o[j], m[i]), (m[i], o[j], m[j]), (m[i], m[j], t[j]), (t[i], m[i], t[j]), (t[i], t[j], ctr)]
    img = Image.new("RGB", (N, N), 0)
    dr = ImageDraw.Draw(img)
    edges = M()
    for k, (p0, p1, p2) in enumerate(tris):
        a = np.array(p1) - np.array(p0)
        b = np.array(p2) - np.array(p0)
        nn = np.cross(a, b)
        if nn[2] < 0:
            nn = -nn
        nn = nn / (np.linalg.norm(nn) + 1e-9)
        ndl = max(0.0, float(nn @ LIGHT))
        tv = float(np.clip(0.05 + 0.8 * ndl + 0.42 * (rng.random() - 0.5), 0, 1))
        col = ramp(np.array([tv]), stops)[0]
        col = col + (max(0.0, float(nn @ HALF)) ** 24) * 0.9
        col = np.clip(col, 0, 1)
        dr.polygon([(p[0] * SS, p[1] * SS) for p in (p0, p1, p2)], fill=tuple(int(v * 255) for v in col))
        edges.line([(p0[0], p0[1]), (p1[0], p1[1]), (p2[0], p2[1]), (p0[0], p0[1])], 0.6)
    rgb = np.asarray(img, np.float32) / 255.0
    mask = poly_mask([(p[0], p[1]) for p in o])
    rgb = over(rgb, np.array([1.0, 0.72, 0.66], np.float32), soft(edges.arr(), 0.3) * 0.22)
    core = np.exp(-(dist(cx + 0.12 * s, cy + 0.5 * s) / (0.45 * s)) ** 2)
    rgb = screen(rgb, core_col * (0.35 * core)[..., None])
    rgb *= FALL[..., None] * 0.5 + 0.55
    return put(c, mask, rgb, sh=sh), mask


def beam(c, p0, p1, w0, w1, col, amt, blur=4, rev=False):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -dy, dx
    m = poly_mask([(x0 + px * w0, y0 + py * w0), (x1 + px * w1, y1 + py * w1), (x1 - px * w1, y1 - py * w1), (x0 - px * w0, y0 - py * w0)])
    t = np.clip(((XX - x0) * dx + (YY - y0) * dy) / L, 0, 1)
    v = soft(m, blur) * ((0.25 + 0.75 * t) if rev else (1 - t ** 1.5)) * amt
    return screen(c, np.asarray(col, np.float32) * v[..., None])


# ----------------------------------------------------------------------------
# icons
# ----------------------------------------------------------------------------


def icon_clan1():
    c = background(cy=232, crim=0.5)
    c = frame(c)
    c = glow(c, M().circle(256, 228, 120).arr(), CRIMSON, 26, 0.55)
    c = silk_tail(c, (248, 236), (160, 366), 46)
    c = silk_tail(c, (264, 236), (352, 366), 46)
    c = seal(c, 256, 220, 118, ang=0, seed=11)
    c = sparkle(c, 205, 168, 26, 0.7)
    c = plate(c, "x1")
    return c


def icon_clan5():
    c = background(cy=250, crim=0.5)
    c = frame(c)
    lay = [(114, 276, 48, -16, 5), (398, 276, 48, 16, 6), (174, 252, 58, -8, 3), (338, 252, 58, 8, 4), (256, 236, 80, 0, 2)]
    c = glow(c, M().circle(256, 250, 150).arr(), CRIMSON, 30, 0.45)
    for x, y, R, a, sd in lay:
        c = seal(c, x, y, R, ang=a, seed=sd)
    c = sparkle(c, 222, 186, 22, 0.6)
    c = ribbon(c, "POPULAR")
    c = plate(c, "x5")
    return c


def icon_clan15():
    c = background(cy=262, crim=0.35, gold=0.32, gold_r=170)
    th = np.arctan2(YY - 262, XX - 256)
    rays = (0.5 + 0.5 * np.cos(14 * th)) ** 6 * np.exp(-dist(256, 262) / 150) * smoothstep(240, 200, dist(256, 256))
    c = screen(c, GOLD * (rays * 0.35)[..., None])
    c = frame(c)
    rng = np.random.default_rng(7)
    rows = [(1, 140), (2, 188), (3, 236), (4, 286), (5, 336)]
    sd = 20
    pyr = M()
    for cnt, y in rows:
        for i in range(cnt):
            x = 256 + (i - (cnt - 1) / 2) * 63
            pyr.circle(x, y, 34)
    c = glow(c, pyr.arr(), GOLD, 22, 0.55)
    for cnt, y in rows:
        for i in range(cnt):
            x = 256 + (i - (cnt - 1) / 2) * 63 + rng.uniform(-3, 3)
            R = (40 if cnt == 1 else 33) + rng.uniform(-1.5, 1.5)
            c = seal(c, x, y + rng.uniform(-3, 3), R, ang=rng.uniform(-14, 14), seed=sd, sh_op=0.8)
            sd += 1
    for x, y, s in ((170, 150, 20), (352, 176, 16), (118, 300, 14), (398, 268, 18), (300, 110, 12)):
        c = sparkle(c, x, y, s, 0.9)
    c = ribbon(c, "BEST VALUE")
    c = plate(c, "x15")
    return c


def icon_race3():
    c = background(cy=250, crim=0.45)
    c = frame(c)
    R = 70
    spots = [(146, 276), (366, 276), (256, 212)]
    for x, y in spots:
        c = medallion(c, x, y, R)
    c = nib(c, 146, 276, 50, ang=28)
    c = drop(c, 366, 270, 47)
    c = cross(c, 256, 218, 51)
    c = sparkle(c, 236, 160, 18, 0.6)
    c = plate(c, "x3")
    return c


def icon_race10():
    c = background(cy=240, crim=0.45, gold=0.12, gold_r=110)
    r = dist(256, 240)
    th = np.arctan2(YY - 240, XX - 256)
    inside = smoothstep(150, 120, r)
    c = screen(c, np.array([0.55, 0.03, 0.07], np.float32) * (0.35 * inside * (0.6 + 0.4 * np.exp(-(r / 90) ** 2)))[..., None])
    rays = (0.5 + 0.5 * np.cos(18 * th)) ** 8 * np.exp(-r / 120) * smoothstep(232, 190, dist(256, 256))
    c = screen(c, GOLD * (rays * 0.45)[..., None])
    c = frame(c)
    ring = ((r >= 138) & (r <= 156)).astype(np.float32)
    c = glow(c, ring, CRIMSON, 12, 0.9)
    c = glow(c, ring, GOLD, 5, 0.5)
    h = np.sqrt(np.clip(9 ** 2 - (r - 147) ** 2, 0, None))
    notch = (0.5 + 0.5 * np.cos(36 * th)) ** 30
    h -= 0.8 * notch * (h > 3)
    c = put(c, ring, mat_color(normals(h, 0.35), "gold"), sh=(3, 6, 6, 0.7))
    c = cross(c, 256, 192, 62, sh=(5, 8, 7, 0.75))
    c = nib(c, 186, 300, 50, ang=-28, sh=(5, 8, 7, 0.75))
    c = drop(c, 330, 296, 47, sh=(5, 8, 7, 0.75))
    for x, y, s in ((210, 112, 20), (356, 150, 16), (130, 220, 14), (390, 330, 16)):
        c = sparkle(c, x, y, s, 0.9)
    c = ribbon(c, "BEST VALUE")
    c = plate(c, "x10")
    return c


def icon_variant3():
    c = background(cy=240, crim=0.4)
    c = frame(c)
    c = beam(c, (52, 78), (226, 212), 2, 9, (1.0, 0.92, 0.75), 0.75, blur=2.5, rev=True)
    exits = [((278, 232), (390, 168), (0.95, 0.18, 0.24), 1), ((282, 252), (406, 250), (1.0, 0.80, 0.42), 2),
             ((278, 274), (390, 332), (1.0, 0.62, 0.66), 3)]
    for p0, p1, col, _ in exits:
        c = beam(c, p0, p1, 4, 15, col, 0.9, blur=3.5)
    c, gm = gem_drop(c, 218, 236, 112, seed=4)
    c = sparkle(c, 182, 168, 30, 0.95)
    stops_gold = [(0, (0.10, 0.05, 0.0)), (0.3, (0.40, 0.24, 0.06)), (0.55, DGOLD * 1.1), (0.78, GOLD), (1, (1, 0.97, 0.86))]
    stops_rose = [(0, (0.12, 0.02, 0.04)), (0.3, (0.45, 0.10, 0.16)), (0.55, (0.78, 0.36, 0.42)), (0.78, (0.97, 0.66, 0.68)), (1, (1, 0.92, 0.9))]
    for (p0, p1, col, sd), st in zip(exits, (GEM_STOPS, stops_gold, stops_rose)):
        c = glow(c, M().circle(p1[0], p1[1], 16).arr(), col, 9, 0.7)
        c, _ = gem_drop(c, p1[0], p1[1] - 5, 28, seed=sd + 10, stops=st, sh=(2, 3, 3, 0.6), core_col=np.asarray(col, np.float32))
    c = plate(c, "x3")
    return c


def g_moon(m, x, y, g):
    m.circle(x, y, g)
    m.circle(x + 0.48 * g, y - 0.22 * g, 0.84 * g, fill=0)


def g_star(m, x, y, g):
    pts = []
    for k in range(10):
        rr = g if k % 2 == 0 else 0.42 * g
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    m.poly(pts)


def g_eye(m, x, y, g):
    top = [(x + g * u, y - 0.62 * g * (1 - u * u)) for u in np.linspace(-1.1, 1.1, 25)]
    bot = [(x + g * u, y + 0.62 * g * (1 - u * u)) for u in np.linspace(1.1, -1.1, 25)]
    m.poly(top + bot)
    top = [(x + g * 0.82 * u, y - 0.42 * g * (1 - u * u)) for u in np.linspace(-1.05, 1.05, 25)]
    bot = [(x + g * 0.82 * u, y + 0.42 * g * (1 - u * u)) for u in np.linspace(1.05, -1.05, 25)]
    m.poly(top + bot, fill=0)
    m.circle(x, y, 0.33 * g)


def g_flame(m, x, y, g):
    m.poly(drop_pts(x, y - 0.1 * g, g * 1.05))
    m.poly(drop_pts(x + 0.05 * g, y + 0.25 * g, g * 0.62), fill=0)
    m.poly(drop_pts(x + 0.05 * g, y + 0.45 * g, g * 0.32))


def g_dagger(m, x, y, g):
    m.poly([(x, y + 1.15 * g), (x - 0.2 * g, y - 0.15 * g), (x + 0.2 * g, y - 0.15 * g)])
    m.rect(x - 0.62 * g, y - 0.32 * g, x + 0.62 * g, y - 0.16 * g)
    m.rect(x - 0.09 * g, y - 0.78 * g, x + 0.09 * g, y - 0.3 * g)
    m.circle(x, y - 0.88 * g, 0.16 * g)


def card(c, ang, glyph_fn, px=256, py=500):
    ccx, ccy, w, hgt = 256, 254, 108, 160
    cm = M().rect(ccx - w / 2, ccy - hgt / 2, ccx + w / 2, ccy + hgt / 2, radius=9)
    gm = M()
    glyph_fn(gm, ccx, ccy - 2, 29)
    pm = M()
    for sx, sy in ((-1, -1), (1, 1), (1, -1), (-1, 1)):
        qx, qy = ccx + sx * (w / 2 - 19), ccy + sy * (hgt / 2 - 19)
        pm.poly([(qx, qy - 4), (qx + 3, qy), (qx, qy + 4), (qx - 3, qy)])
    for mm in (cm, gm, pm):
        mm.rotate(ang, px, py)
    cmask, gmask, pmask = cm.arr(), gm.arr() * cm.arr(), pm.arr()
    d = edt(cmask)
    h = bevel(cmask, 2.5) - 1.6 * smoothstep(5.0, 6.5, d)
    line = ((d >= 10.5) & (d <= 12.0)).astype(np.float32)
    h += 0.9 * soft(line, 0.4) + 1.0 * bevel(pmask, 1.5)
    n = normals(h, 0.4)
    goldw = np.clip(1 - smoothstep(5.0, 6.5, d) + soft(line, 0.4) + soft(pmask, 0.4), 0, 1)[..., None]
    col = mat_color(n, "gold") * goldw + mat_color(n, "obsid") * (1 - goldw)
    face = smoothstep(6.5, 9, d)
    col = screen(col, CRIMSON * (soft(gmask, 7) * 0.9 * face)[..., None])
    core = soft((edt(gmask) > 1.0).astype(np.float32), 0.6)
    emis = CRIMSON * 1.25 + np.array([1.0, 0.85, 0.7], np.float32) * core[..., None] * 0.75
    col = over(col, np.clip(emis, 0, 1), soft(gmask, 0.4))
    return put(c, cmask, col, sh=(4, 7, 6, 0.75))


def icon_trait5():
    c = background(cy=262, crim=0.45)
    c = frame(c)
    seq = [(30, g_moon), (-30, g_star), (15, g_dagger), (-15, g_flame), (0, g_eye)]
    for a, fn in seq:
        c = card(c, a, fn)
    c = sparkle(c, 226, 196, 18, 0.55)
    c = plate(c, "x5")
    return c


def scribble_line(m, x0, x1, y, rng, width=1.25, amp=2.6):
    x = x0
    while x < x1 - 8:
        wl = rng.uniform(12, 30)
        xe = min(x + wl, x1)
        xs = np.linspace(x, xe, int((xe - x) * 1.5) + 2)
        ph = rng.uniform(0, 6)
        ys = y - amp * (0.5 + 0.5 * np.sin(xs * 1.15 + ph)) - 0.8 * np.sin(xs * 0.37 + ph)
        m.line(list(zip(xs, ys)), width)
        x = xe + rng.uniform(5, 9)


def icon_rename():
    c = background(cy=250, crim=0.42)
    c = frame(c)
    rng = np.random.default_rng(5)
    cover = M().rect(82, 122, 430, 366, radius=8).arr()
    hc = bevel(cover, 5) + 0.12 * noise(9, 10) * cover + 0.05 * noise(19, 3) * cover
    c = put(c, cover, mat_color(normals(hc, 0.6), "leather"), sh=(6, 10, 10, 0.8))
    caps = M()
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x = 82 if sx == 0 else 430
        y = 122 if sy == 0 else 366
        dx = 30 if sx == 0 else -30
        dy = 30 if sy == 0 else -30
        caps.poly([(x, y), (x + dx, y), (x, y + dy)])
    capm = caps.arr() * cover
    c = put(c, capm, mat_color(normals(bevel(capm, 2.5), 0.4), "gold"), sh=(1, 2, 2, 0.6))

    def page_pts(side, yoff=0.0):
        xs = np.linspace(256, 256 + side * 160, 40)
        top = [(x, 132 + yoff + 9 * math.exp(-abs(x - 256) / 24) - 4 * (abs(x - 256) / 160) ** 4) for x in xs]
        bot = [(x, 352 + yoff + 7 * math.exp(-abs(x - 256) / 24) - 2 * (abs(x - 256) / 160) ** 4) for x in xs[::-1]]
        return top + bot

    for side in (-1, 1):
        blk = np.maximum(poly_mask(page_pts(side, 5)), poly_mask(page_pts(side, 2.5)))
        hb = bevel(blk, 1.5)
        col = mat_color(normals(hb, 0.4), "parch") * 0.62
        col *= (0.85 + 0.15 * np.sin(YY * SS * 2.2))[..., None]
        c = put(c, blk, col, sh=(2, 3, 3, 0.6))
    pages = np.maximum(poly_mask(page_pts(-1)), poly_mask(page_pts(1)))
    ax = np.abs(XX - 256)
    hp = (12 * (1 - np.exp(-ax / 26)) - 5 * (ax / 160) ** 3) * pages + 0.05 * noise(3, 12) * pages
    col = mat_color(normals(hp, 1.0), "parch")
    col *= (1 - 0.45 * np.exp(-ax / 9))[..., None]
    dpg = edt(pages)
    col = col * (1 - 0.32 * np.exp(-dpg / 5.0))[..., None] * (1 + 0.05 * noise(8, 24))[..., None]
    col = col * np.array([1.0, 0.97, 0.92], np.float32)
    # ruling and margins
    rl = M()
    for k in range(9):
        y = 176 + 20 * k
        rl.line([(104, y), (240, y)], 0.9)
        rl.line([(272, y), (408, y)], 0.9)
    col = over(col, np.array([0.40, 0.36, 0.38], np.float32), soft(rl.arr(), 0.35) * 0.45 * pages)
    mg = M().line([(124, 140), (124, 350)], 1.0).line([(290, 140), (290, 350)], 1.0)
    col = over(col, CRIMSON * 0.85, soft(mg.arr(), 0.35) * 0.45 * pages)
    ink = np.array([0.12, 0.08, 0.07], np.float32)
    hdr, _ = text_mask([("REGISTER", font(F_PLATE, 12.5))], 176, 156, tracking=2.0)
    col = over(col, ink, hdr * 0.8)
    hl = M().line([(130, 165), (222, 165)], 0.8).line([(300, 158), (392, 158)], 0.8).line([(300, 162), (392, 162)], 0.8)
    col = over(col, ink, soft(hl.arr(), 0.3) * 0.55)
    sc = M()
    for k in range(9):
        scribble_line(sc, 130, 236 - rng.uniform(0, 40), 176 + 20 * k - 2.5, rng)
    scribble_line(sc, 296, 392, 194, rng)
    scribble_line(sc, 296, 352, 314, rng)
    scribble_line(sc, 296, 380, 334, rng)
    col = over(col, ink, soft(sc.arr(), 0.35) * 0.6)
    # the old name, struck through in red ink
    fsz = 23
    old, ow = text_mask([("Ashcombe", font(F_HAND, fsz))], 336, 226)
    col = over(col, ink, old * 0.92)
    strike = M()
    xs = np.linspace(336 - ow / 2 - 8, 336 + ow / 2 + 8, 30)
    strike.line([(x, 225 - 2.2 * (x - 336) / ow + 0.8 * math.sin(x * 0.2)) for x in xs], 4.6)
    stm = strike.arr()
    col = over(col, np.array([0.70, 0.05, 0.09], np.float32), soft(stm, 0.4) * 0.95)
    new, nw = text_mask([("Raven", font(F_HAND, fsz))], 300 + 0, 266)
    shift = int(round((nw / 2 - 0) * SS))
    new = np.roll(new, shift, 1)    # left-align the new name at x=300
    col = over(col, ink * 0.6, new)
    c = over(c, col, soft(pages, 0.45))
    # quill: tip at the end of the new name, feather leaning up-right
    tx, ty = 300 + nw + 3, 262
    c = quill(c, tx, ty, 68, 172)
    c = plate(c, "RENAME")
    return c


def quill(c, tx, ty, ang_deg, L):
    a = math.radians(ang_deg)
    dx, dy = math.cos(a), -math.sin(a)
    al = (XX - tx) * dx + (YY - ty) * dy
    b = -(XX - tx) * dy + (YY - ty) * dx
    b = b - 0.06 * L * (np.clip(al, 0, None) / L) ** 2
    s0 = 0.30 * L
    tt = np.clip((al - s0) / (L - s0), 0, 1)
    env = np.clip(np.sin(np.pi * np.clip(tt, 0, 1) ** 0.8), 0, 1) ** 0.55
    wl, wr = 24 * env, 15 * env
    inr = (al > s0) & (al < L)
    vane = (inr & (((b < 0) & (-b < wl)) | ((b >= 0) & (b < wr)))).astype(np.float32)
    phase = (al + 0.75 * np.abs(b)) / 3.4
    for gap in (0.55, 0.78):
        g0 = s0 + gap * (L - s0)
        cut = (np.abs(al + 0.75 * np.abs(b) - g0 - 12) < 1.0) & (b < -4)
        vane = vane * (1 - cut.astype(np.float32))
    rach = ((al > 4) & (al < L - 2) & (np.abs(b) < 1.6 * (1 - 0.55 * al / L) + 0.4)).astype(np.float32)
    calamus = ((al > 6) & (al <= s0 + 2) & (np.abs(b) < 2.4)).astype(np.float32)
    tip = ((al >= 0) & (al <= 8) & (np.abs(b) < 2.4 * np.clip(al / 8, 0, 1))).astype(np.float32)
    allm = np.clip(vane + rach + calamus + tip, 0, 1)
    h = bevel(vane, 3.5) - 0.45 * (0.5 + 0.5 * np.cos(2 * np.pi * phase)) * vane
    h = np.maximum(h, (2.0 * np.sqrt(np.clip(1 - (b / 2.4) ** 2, 0, None))) * np.clip(rach + calamus + tip, 0, 1))
    n = normals(h, 0.35)
    col = mat_color(n, "feather")
    iv = soft(np.clip(rach + calamus, 0, 1), 0.3)[..., None]
    col = col * (1 - iv) + mat_color(n, "ivory") * iv
    col = over(col, np.array([0.05, 0.03, 0.04], np.float32), soft(tip, 0.3))
    c = shadow(c, allm, 7, 10, 5, 0.55)
    c = over(c, col, soft(allm, 0.45))
    return c


ICONS = {
    "Clan1": (icon_clan1, "1 clan spin"),
    "Clan5": (icon_clan5, "5 clan spins - Popular"),
    "Clan15": (icon_clan15, "15 clan spins - Best value"),
    "Race3": (icon_race3, "3 race spins"),
    "Race10": (icon_race10, "10 race spins - Best value"),
    "Variant3": (icon_variant3, "3 variant spins"),
    "Trait5": (icon_trait5, "5 trait spins"),
    "NameChange": (icon_rename, "Name change"),
}


def finish(c, seed=0):
    img = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8), "RGB").resize((512, 512), Image.LANCZOS)
    a = np.asarray(img, np.float32)
    a += np.random.default_rng(seed).normal(0, 1.6, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def contact_sheet(out_dir):
    cell, pad, lab = 300, 20, 52
    W = 4 * (cell + pad) + pad
    H = 2 * (cell + lab + pad) + pad + 200
    sheet = Image.new("RGB", (W, H), (14, 12, 18))
    d = ImageDraw.Draw(sheet)
    fk = ImageFont.truetype(F_RIBBON, 19)
    fd = ImageFont.truetype(F_LABEL, 14)
    for i, (key, (_, desc)) in enumerate(ICONS.items()):
        p = os.path.join(out_dir, key + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        x = pad + (i % 4) * (cell + pad)
        y = pad + (i // 4) * (cell + lab + pad)
        sheet.paste(im.resize((cell, cell), Image.LANCZOS), (x, y))
        d.text((x + cell / 2, y + cell + 8), key, font=fk, fill=(235, 205, 120), anchor="ma")
        d.text((x + cell / 2, y + cell + 31), desc, font=fd, fill=(190, 180, 190), anchor="ma")
        # circle-cropped 150px preview (as shown in some Roblox UI)
        sm = im.resize((150, 150), Image.LANCZOS)
        mk = Image.new("L", (600, 600), 0)
        ImageDraw.Draw(mk).ellipse([0, 0, 599, 599], fill=255)
        sx = pad + i * ((W - 2 * pad) // 8) + 4
        sy = H - 180
        sheet.paste(sm, (sx, sy), mk.resize((150, 150), Image.LANCZOS))
    d.text((pad, H - 200), "150 px circle-crop preview", font=fd, fill=(150, 140, 150))
    sheet.save(os.path.join(out_dir, "contact_sheet.png"))


def main(argv):
    out = OUT_DIR
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    os.makedirs(out, exist_ok=True)
    keys = argv or list(ICONS)
    for k in keys:
        fn, _ = ICONS[k]
        img = finish(fn(), seed=sum(map(ord, k)))
        img.save(os.path.join(out, k + ".png"))
        print("wrote", k)
    contact_sheet(out)
    print("wrote contact_sheet.png")


if __name__ == "__main__":
    main(sys.argv[1:])
