"""Sable Vey's fortune deck for Nightmare Highschool (the Ink Club's fortune teller), baked to images.

Eight original cards, one hand-made deck: a bone-parchment ground, inked engraving (line hatching whose width follows
the tone, contour lines, ink outlines), limited washes (crimson #600E1A, brass gold, night blue), and the same brass
frame on every card. The frame, the corner rosettes, the numeral cartouche and the art window's molding are lit in PBR
by make_health_pbr.shade (the kit's brass); the art is painted in 2D at 2x and box/Lanczos reduced to 600 x 1024.

Face layout (final px, 600 x 1024): brass frame band 0..21 with corner rosettes; a dark cartouche with the Roman numeral
at the top (y ~62); a pointed-arch art window (x 46..554, apex y 106, springing y 250, foot y 910) with gothic tracery in
the spandrels; a crimson scroll banner with the title in bone capitals at the bottom (y ~922). The game draws the hint
text under the card, so there is none on the cards.

  CardBack    crimson-and-ink lattice, a crescent moon over an ink-blot eye, brass filigree
  TheTower    XVI    the school bell tower struck by pale lightning; sparks, falling slates
  TheFool     0      a student in a long scarf stepping off a rooftop ledge toward a sealed dare; a black cat
  TheMoon     XVIII  a great moon over two spires, a wolf and a raven calling, a winding path
  TheSeeker   IX     a hooded figure raising a lantern down a dark corridor; a lost key glints on the floor
  TheFeast    III    a long candlelit table, one steaming dish under a cloche, garlic and a goblet
  TheCrown    IV     a thorned iron crown on a cushion, laurel, a prize ribbon, rays
  TheScholar  V      books, inkwell and quill, a sealed report card, an owl on top

No blood or gore anywhere (Roblox moderation).

    python make_tarot_cards.py              # all eight
    python make_tarot_cards.py TheTower     # just some
Writes art/ui/hud/out/tarot/<Name>.png (600 x 1024 RGBA), contact_sheet.png (all eight at 300 x 512 on ink),
crop_1to1.png (two cards at 1:1), and copies the finals to art/group-upload/tarot-cards/FortuneCard_<Name>.png.
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as PBR

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "tarot"
UPLOAD = HERE.parents[1] / "group-upload" / "tarot-cards"
OUT.mkdir(parents=True, exist_ok=True)
FONT_TITLE = "C:/Windows/Fonts/palab.ttf"
FONT_NUM = "C:/Windows/Fonts/palab.ttf"
f32 = np.float32

CW, CH = 600, 1024            # final card size
K = 2                         # work at 2x
SS = 2                        # extra supersampling for PIL-drawn masks
WW, WH = CW * K, CH * K
_gy, _gx = np.mgrid[0:WH, 0:WW].astype(f32)
X = (_gx + 0.5) / K           # every coordinate below is in FINAL card pixels
Y = (_gy + 0.5) / K
del _gy, _gx

# ---------------------------------------------------------------- palette (sRGB 0..1)
PARCH = np.array((0.925, 0.878, 0.770), f32)
BONE = np.array((0.965, 0.935, 0.860), f32)
INK = np.array((0.070, 0.055, 0.070), f32)
CRIM = np.array((0.376, 0.055, 0.102), f32)        # #600E1A
CRIM_L = np.array((0.640, 0.150, 0.170), f32)
GOLD = np.array((0.850, 0.660, 0.320), f32)
GOLD_L = np.array((0.990, 0.880, 0.600), f32)
NIGHT = np.array((0.120, 0.160, 0.290), f32)
NIGHT_L = np.array((0.420, 0.500, 0.660), f32)
WHITE = np.array((1.0, 1.0, 1.0), f32)


# ================================================================ masks (all coordinates in final px)
def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def M(sd):
    """Signed distance in final px (negative inside) -> mask anti-aliased over one work pixel."""
    return np.clip(0.5 - sd * K, 0, 1).astype(f32)


def sd_circle(cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def circle(cx, cy, r):
    return M(sd_circle(cx, cy, r))


def ring(cx, cy, r, w):
    return M(np.abs(sd_circle(cx, cy, r)) - w / 2)


def local(cx, cy, rot=0.0):
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    dx, dy = X - cx, Y - cy
    return c * dx + s * dy, -s * dx + c * dy


def sd_box(cx, cy, w, h, r=0.0, rot=0.0):
    u, v = local(cx, cy, rot)
    qx, qy = np.abs(u) - (w / 2 - r), np.abs(v) - (h / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def box(cx, cy, w, h, r=0.0, rot=0.0):
    return M(sd_box(cx, cy, w, h, r, rot))


def ellipse(cx, cy, rx, ry, rot=0.0):
    u, v = local(cx, cy, rot)
    k = np.hypot(u / rx, v / ry) + 1e-6
    g = np.hypot(u / (rx * rx), v / (ry * ry)) / k + 1e-6
    return M((k - 1) / g)


def seg(x0, y0, x1, y1, w0, w1=None):
    """A capsule from (x0, y0) to (x1, y1), w0 wide at the start tapering to w1."""
    w1 = w0 if w1 is None else w1
    px, py = X - x0, Y - y0
    dx, dy = x1 - x0, y1 - y0
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
    return M(np.hypot(px - t * dx, py - t * dy) - (w0 + (w1 - w0) * t) / 2)


def U(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = np.maximum(out, m)
    return out


def sub(a, *bs):
    for b in bs:
        a = a * (1 - b)
    return a


def _bbox(pts, pad):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0 = max(0, int((min(xs) - pad) * K))
    y0 = max(0, int((min(ys) - pad) * K))
    x1 = min(WW, int((max(xs) + pad) * K) + 1)
    y1 = min(WH, int((max(ys) + pad) * K) + 1)
    return x0, y0, x1, y1


def _pil(pts, pad, fn):
    out = np.zeros((WH, WW), f32)
    x0, y0, x1, y1 = _bbox(pts, pad)
    if x1 <= x0 or y1 <= y0:
        return out
    k = K * SS
    im = Image.new("L", ((x1 - x0) * SS, (y1 - y0) * SS), 0)
    d = ImageDraw.Draw(im)
    tr = lambda p: ((p[0] * K - x0) * SS, (p[1] * K - y0) * SS)
    fn(d, tr, k)
    out[y0:y1, x0:x1] = np.array(im.resize((x1 - x0, y1 - y0), Image.BOX), f32) / 255.0
    return out


def poly(pts):
    pts = [tuple(p[:2]) for p in pts]
    return _pil(pts, 4, lambda d, tr, k: d.polygon([tr(p) for p in pts], fill=255))


def stroke(pts, w, closed=False):
    """A polyline stroked w px wide with round joints and caps."""
    pts = [tuple(p[:2]) for p in pts]
    if closed:
        pts = pts + [pts[0]]

    def fn(d, tr, k):
        q = [tr(p) for p in pts]
        d.line(q, fill=255, width=max(1, int(round(w * k))), joint="curve")
        r = w * k / 2
        for p in (q[0], q[-1]):
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    return _pil(pts, w + 4, fn)


def taper(pts, w0, w1):
    """A smooth stroke whose width runs from w0 to w1 along the polyline (built from capsules)."""
    n = len(pts) - 1
    out = np.zeros((WH, WW), f32)
    x0, y0, x1, y1 = _bbox(pts, max(w0, w1) + 4)
    sl = (slice(y0, y1), slice(x0, x1))
    Xs, Ys = X[sl], Y[sl]
    acc = np.zeros(Xs.shape, f32)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i][:2], pts[i + 1][:2]
        wa = w0 + (w1 - w0) * i / n
        wb = w0 + (w1 - w0) * (i + 1) / n
        px, py = Xs - ax, Ys - ay
        dx, dy = bx - ax, by - ay
        t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
        acc = np.maximum(acc, np.clip(0.5 - (np.hypot(px - t * dx, py - t * dy) - (wa + (wb - wa) * t) / 2) * K, 0, 1))
    out[sl] = acc
    return out


def spline(pts, closed=True, n=14):
    """Catmull-Rom through the points; a point given as (x, y, 1) is a sharp corner."""
    P = [np.array(p[:2], f32) for p in pts]
    sharp = [len(p) > 2 and p[2] for p in pts]
    m = len(P)
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        p0, p1 = P[i], P[(i + 1) % m]
        pm = P[(i - 1) % m] if (closed or i > 0) else p0
        pn = P[(i + 2) % m] if (closed or i + 2 < m) else p1
        t0 = np.zeros(2, f32) if sharp[i] else (p1 - pm) * 0.5
        t1 = np.zeros(2, f32) if sharp[(i + 1) % m] else (pn - p0) * 0.5
        for t in np.linspace(0, 1, n, endpoint=False):
            h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
            h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
            out.append(tuple(h00 * p0 + h10 * t0 + h01 * p1 + h11 * t1))
    if not closed:
        out.append(tuple(P[-1]))
    return out


def blob(pts, n=14):
    return poly(spline(pts, True, n))


def mirror_pts(pts, cx=300):
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def text_mask(s, size, cx, cy, font=FONT_TITLE, track=0.0):
    f = ImageFont.truetype(font, int(size * K * SS))
    widths = [f.getlength(ch) for ch in s]
    total = sum(widths) + track * K * SS * (len(s) - 1)
    pad = int(size * 2)
    pts = [(cx - total / (K * SS) / 2 - 10, cy - size), (cx + total / (K * SS) / 2 + 10, cy + size)]

    def fn(d, tr, k):
        x, yc = tr((cx, cy))
        x -= total / 2
        for ch, w in zip(s, widths):
            d.text((x, yc), ch, font=f, fill=255, anchor="lm")
            x += w + track * k
    return _pil(pts, pad, fn)


def text_width(s, size, font=FONT_TITLE, track=0.0):
    f = ImageFont.truetype(font, int(size * 10))
    return (sum(f.getlength(ch) for ch in s)) / 10 + track * (len(s) - 1)


# ---------------------------------------------------------------- fields
def sdf(m, pad=60):
    """Signed distance (final px, negative inside) of an anti-aliased mask, computed in its bounding box."""
    ys, xs = np.nonzero(m > 0.02)
    full = np.full(m.shape, pad / K, f32)
    if len(ys) == 0:
        return full + 1000
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad + 1)
    s = m[y0:y1, x0:x1]
    inside = s > 0.5
    di = ndimage.distance_transform_edt(inside)
    do = ndimage.distance_transform_edt(~inside)
    sd = np.where(inside, -(di - 0.5), do - 0.5)
    edge = (s > 0.02) & (s < 0.98)
    sd = np.where(edge, 0.5 - s, sd)
    full[y0:y1, x0:x1] = ndimage.gaussian_filter(sd.astype(f32), 0.6) / K
    return full


_NOISE = {}


def noise(sigma, seed):
    """Smooth 0..1 noise, sigma in final px (large sigmas are made small and scaled up)."""
    key = (sigma, seed)
    if key not in _NOISE:
        r = np.random.default_rng(seed)
        sk = sigma * K
        f = max(1, int(sk / 3))
        h, w = -(-WH // f) + 2, -(-WW // f) + 2
        n = ndimage.gaussian_filter(r.random((h, w)).astype(f32), sk / f, mode="wrap")
        if f > 1:
            n = ndimage.zoom(n, f, order=3)[:WH, :WW]
        else:
            n = n[:WH, :WW]
        _NOISE[key] = ((n - n.min()) / (n.max() - n.min() + 1e-6)).astype(f32)
    return _NOISE[key]


def pillow(m, sigma, light=(-0.6, -0.75), z=0.55):
    """Lambert light on the mask blurred into a pillow: 0 (dark) .. 1 (lit)."""
    h = ndimage.gaussian_filter(m, sigma * K)
    gy, gx = np.gradient(h)
    s = sigma * K * 1.8
    nx, ny = -gx * s, -gy * s
    nz = np.ones_like(h)
    nl = np.sqrt(nx * nx + ny * ny + 1)
    L = np.array((light[0], light[1], z), f32)
    L /= np.linalg.norm(L)
    return np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / nl, 0, 1).astype(f32)


def lin(x0, y0, x1, y1):
    """0 at (x0, y0) .. 1 at (x1, y1), along that direction."""
    dx, dy = x1 - x0, y1 - y0
    return np.clip(((X - x0) * dx + (Y - y0) * dy) / (dx * dx + dy * dy), 0, 1).astype(f32)


def radial(cx, cy, r):
    """1 at the centre .. 0 at radius r (smooth)."""
    return (1 - smooth(0, r, np.hypot(X - cx, Y - cy))).astype(f32)


# ================================================================ the painter
def bbox_of(m, thr=1e-3, pad=2):
    """Slices bounding the non-zero part of a full-frame mask (None if empty)."""
    rows = np.flatnonzero(m.max(axis=1) > thr)
    if len(rows) == 0:
        return None
    cols = np.flatnonzero(m[rows[0]:rows[-1] + 1].max(axis=0) > thr)
    y0, y1 = max(0, rows[0] - pad), min(m.shape[0], rows[-1] + pad + 1)
    x0, x1 = max(0, cols[0] - pad), min(m.shape[1], cols[-1] + pad + 1)
    return (slice(y0, y1), slice(x0, x1))


def _cut(v, sl):
    """Slice v to sl if it is a full-frame array, else pass it through."""
    if isinstance(v, np.ndarray) and v.ndim >= 2 and v.shape[0] == WH and v.shape[1] == WW:
        return v[sl]
    return v


class Canvas:
    def __init__(self, base=PARCH, seed=1):
        self.seed = seed
        self.k = 0
        self.rgb = np.empty((WH, WW, 3), f32)
        self.rgb[:] = base

    def n(self, sigma):
        self.k += 1
        return noise(sigma, self.seed * 101 + self.k)

    def fill(self, m, col, a=1.0):
        """Paint col (an RGB triple or a full-frame RGB map) through mask m at opacity a."""
        sl = bbox_of(m)
        if sl is None:
            return
        mm = (m[sl] * _cut(a, sl))
        mm = np.clip(mm, 0, 1)[..., None]
        c = _cut(np.asarray(col, f32), sl)
        self.rgb[sl] = self.rgb[sl] * (1 - mm) + c * mm

    def fillv(self, m, colmap):
        self.fill(m, colmap)

    def glaze(self, m, col, k=1.0):
        """Multiply a transparent wash over what's there (watercolour)."""
        sl = bbox_of(m)
        if sl is None:
            return
        mm = np.clip(m[sl] * _cut(k, sl), 0, 1)[..., None]
        c = _cut(np.asarray(col, f32), sl)
        self.rgb[sl] = self.rgb[sl] * (1 - mm + mm * c)

    def light(self, m, col, k=1.0):
        """Screen light onto what's there (glows)."""
        sl = bbox_of(m)
        if sl is None:
            return
        mm = np.clip(m[sl] * _cut(k, sl), 0, 1)[..., None]
        c = _cut(np.asarray(col, f32), sl)
        self.rgb[sl] = 1 - (1 - self.rgb[sl]) * (1 - mm * c)

    def hatch(self, m, tone, angle=45.0, spacing=3.4, col=INK, cross=None, wob=0.10, phase=None, a=1.0):
        """Engraved line hatching (angle = the lines' direction): line width follows tone (0 none .. 1 ~70% ink),
        with a cross-hatch past ~0.5 unless cross=False. phase: a field whose integer contours are the lines."""
        sl = bbox_of(m)
        if sl is None:
            return
        tone = np.clip(np.broadcast_to(_cut(tone, sl), m[sl].shape), 0, 1)
        ph = _cut(phase, sl) if phase is not None else None
        self.k += 1
        ink = _lines(sl, np.clip(tone * 1.35, 0, 0.68), angle, spacing, wob, noise(14, 9000 + self.k % 5)[sl], ph)
        if cross is not False:
            ca = angle + (62 if cross is None else cross)
            ink = np.maximum(ink, _lines(sl, np.clip((tone - 0.48) * 1.25, 0, 0.6), ca, spacing * 1.05, wob,
                                         noise(14, 9010 + self.k % 5)[sl]))
        full = np.zeros((WH, WW), f32)
        full[sl] = m[sl] * ink
        self.fill(full, col, a)

    def outline(self, m, w=2.0, col=INK, a=1.0, sd=None):
        sd = sdf(m) if sd is None else sd
        self.fill(M(np.abs(sd) - w / 2), col, a)
        return sd

    def inline(self, m, w=2.0, col=INK, a=1.0, sd=None):
        """A line just inside the edge."""
        sd = sdf(m) if sd is None else sd
        self.fill(M(np.abs(sd + w / 2) - w / 2) * (m > 0.01), col, a)
        return sd

    def rim(self, m, dx, dy, w, col=BONE, a=1.0):
        """A light rim on the edge of m facing (dx, dy)."""
        sl = bbox_of(m, pad=int(w * K) + 4)
        if sl is None:
            return
        sub_ = m[sl]
        sh = ndimage.shift(sub_, (dy * K * w, dx * K * w), order=1, mode="constant")
        full = np.zeros((WH, WW), f32)
        full[sl] = ndimage.gaussian_filter(np.clip(sub_ - sh, 0, 1), 0.6)
        self.fill(full, col, a)

    def shadow(self, m, dx, dy, blur, k=0.5, under=None):
        pad = int((abs(dx) + abs(dy) + blur * 3) * K) + 4
        sl = bbox_of(m, pad=pad)
        if sl is None:
            return
        sub_ = m[sl]
        sh = ndimage.gaussian_filter(ndimage.shift(sub_, (dy * K, dx * K), order=1), blur * K)
        full = np.zeros((WH, WW), f32)
        full[sl] = sh * (1 - sub_)
        if under is not None:
            full *= under
        self.glaze(full, INK, k)


def _lines(sl, tone, angle, spacing, wob, nz, phase=None):
    if phase is None:
        th = math.radians(angle + 90)          # angle = the lines' direction (0 = horizontal)
        u = (X[sl] * math.cos(th) + Y[sl] * math.sin(th)) / spacing
        g = 1.0 / (spacing * K)
    else:
        u = phase
        gy, gx = np.gradient(u)
        g = np.hypot(gx, gy) + 1e-5
    u = u + (nz - 0.5) * wob * 6
    f = np.abs((u % 1.0) - 0.5)
    return np.clip((tone * 0.5 - f) / g + 0.5, 0, 1) * (tone > 0.02)


# ================================================================ shared frame and layout
CARD_R = 30
WIN_X0, WIN_X1, WIN_APEX, WIN_SPRING, WIN_BOT = 46, 554, 106, 250, 910
CX = 300


def card_sd():
    return sd_box(CW / 2, CH / 2, CW, CH, CARD_R)


def arch_y(x):
    a = (WIN_X1 - WIN_X0) / 2
    t = np.clip(np.abs(x - CX) / a, 0, 1)
    R = 1.25
    f = np.sqrt(np.clip(R * R - (t + R - 1) ** 2, 0, None)) / math.sqrt(R * R - (R - 1) ** 2)
    return WIN_SPRING - (WIN_SPRING - WIN_APEX) * f


def window_mask(inset=0.0):
    xs = np.linspace(WIN_X0 + inset, WIN_X1 - inset, 241)
    top = [(x, arch_y(x) + inset * 1.15) for x in xs]
    pts = [(WIN_X0 + inset, WIN_BOT - inset)] + top + [(WIN_X1 - inset, WIN_BOT - inset)]
    return poly(pts)


def parchment(cv, strength=1.0):
    """Bone parchment: soft mottling, fibres, a few foxing spots."""
    mot = cv.n(40) * 0.6 + cv.n(9) * 0.4
    fib = cv.n(0.8)
    tone = 1 - strength * (0.07 * (mot - 0.5) + 0.035 * (fib - 0.5))
    cv.rgb *= tone[..., None]
    fox = smooth(0.70, 0.80, cv.n(22)) * 0.10 * strength
    cv.glaze(fox, (0.78, 0.62, 0.42), 1.0)


class Brass:
    """Accumulates the brass parts (height in px, mask), lit once in PBR at the end."""
    def __init__(self):
        self.h = np.zeros((WH, WW), f32)
        self.m = np.zeros((WH, WW), f32)
        self.gem = np.zeros((WH, WW), f32)
        self.dark = np.zeros((WH, WW), f32)       # inset dark enamel (cartouche field)

    def add(self, m, h):
        self.h = self.h * (1 - m) + h * m
        self.m = np.maximum(self.m, m)

    def render(self):
        hgt = ndimage.gaussian_filter(self.h, 0.7) * K
        col = np.array((0.80, 0.60, 0.30), f32)
        alb = np.empty((WH, WW, 3), f32)
        alb[:] = PBR.srgb_to_lin(col)
        mott = noise(6, 77)[..., None]
        alb *= 0.85 + 0.25 * mott
        gem = self.gem[..., None]
        alb = alb * (1 - gem) + PBR.srgb_to_lin(np.array((0.55, 0.05, 0.09), f32)) * gem
        enamel = self.dark[..., None]
        alb = alb * (1 - enamel) + PBR.srgb_to_lin(INK * 1.2) * enamel
        rough = np.clip(0.34 + 0.18 * noise(1.5, 78) - 0.2 * self.gem + 0.3 * self.dark, 0.08, 1)
        metal = np.clip(0.88 * (1 - self.gem) * (1 - self.dark), 0, 1)
        scratch = np.dstack([noise(0.7, 79) - 0.5, noise(0.7, 80) - 0.5, np.zeros((WH, WW), f32)])
        Nn = PBR.normals_from(hgt, 0.55, scratch, 0.18)
        ao = PBR.ao_from(hgt / K, 3 * K, 0.18) * PBR.ao_from(hgt / K, 1 * K, 0.3)
        rgb = PBR.shade(alb, Nn, rough, metal, ao)
        return rgb.astype(f32), self.m


def dome(dist, r):
    t = np.clip(dist / r, 0, 1)
    return np.sqrt(1 - (1 - t) ** 2)


def frame_brass(br, face=True):
    """The shared brass: frame band with a bead row, corner rosettes with crimson gems, the window molding and the
    numeral cartouche."""
    sd = card_sd()
    t = -sd                                        # depth into the card from its edge (px)
    band = M(sd) * M(-(21.5 + sd))                 # 0 <= t <= 21.5
    # moldings across the band: an outer roll, a cove, a bead row, an inner lip
    roll = np.exp(-((t - 6.0) / 4.2) ** 2) * 5.0
    lip = np.exp(-((t - 20.0) / 1.5) ** 2) * 2.2
    h = 1.0 + roll + lip
    # beads along the straight runs
    along = np.where(np.minimum(t, 9999) == t, 0, 0)
    on_tb = (Y < 40) | (Y > CH - 40)
    pos = np.where(on_tb, X, Y)
    ph = (pos % 9.0) - 4.5
    bead_d = np.hypot(ph, t - 14.0)
    beads = np.sqrt(np.clip(3.6 ** 2 - bead_d ** 2, 0, None)) * 0.9
    corner = (np.minimum(X, CW - X) < 44) & (np.minimum(Y, CH - Y) < 44)
    beads *= ~corner
    h += beads
    br.add(band, h)
    # corner rosettes
    for cx, cy in ((24, 24), (CW - 24, 24), (24, CH - 24), (CW - 24, CH - 24)):
        r = np.hypot(X - cx, Y - cy)
        th = np.arctan2(Y - cy, X - cx)
        petal = 17 + 2.2 * np.cos(8 * th)
        m = M(r - petal)
        hh = 3 + 5 * dome(petal - r, 6) + 1.6 * np.cos(8 * th) * smooth(14, 6, r)
        hh += np.exp(-((r - 9.5) / 1.2) ** 2) * 1.8
        br.add(m, hh)
        gm = circle(cx, cy, 6.2)
        br.add(gm, 7 + 4 * dome(6.2 - r, 6.2))
        br.gem = np.maximum(br.gem, gm)
    # side studs
    for cx in (10.5, CW - 10.5):
        m = M(np.abs(X - cx) + np.abs(Y - CH / 2) * 0.55 - 10)
        br.add(m, 6 + 3 * dome(10 - (np.abs(X - cx) + np.abs(Y - CH / 2) * 0.55), 6))
    if not face:
        return
    # the window molding (a round bead along the arch and sides)
    wsd = sdf(window_mask())
    mold = M(np.abs(wsd) - 3.4)
    br.add(mold, 1 + 3.4 * np.sqrt(np.clip(1 - (wsd / 3.4) ** 2, 0, 1)))
    # the numeral cartouche: a lozenge with pointed ends, brass rim, dark enamel field
    cart_sd = cartouche_sd()
    cm = M(cart_sd)
    rimh = 2 + 4.5 * dome(-cart_sd, 4) - 4.5 * smooth(4.5, 6.5, -cart_sd)
    br.add(cm, rimh)
    field = M(cart_sd + 6.0)
    br.dark = np.maximum(br.dark, field)
    br.add(field, np.full((WH, WW), 0.8, f32))


CART_Y, CART_W, CART_H = 62, 150, 50


def cartouche_sd():
    body = sd_box(CX, CART_Y, CART_W - 40, CART_H, 8)
    u = np.abs(X - CX) - (CART_W / 2 - 34)
    tips = (np.maximum(u, 0) * 0.62 + np.abs(Y - CART_Y)) - CART_H / 2      # pointed ends
    tips = np.where(u > 0, tips, 999)
    return np.minimum(body, tips).astype(f32)


def spandrels(cv):
    """Gothic tracery in the two spandrels beside the arch (a ring round a crimson trefoil, a little ink tendril),
    and a double ink rule inside the frame."""
    for side in (-1, 1):
        cx, cy = CX + side * 203, 94
        cv.fill(circle(cx, cy, 29), PARCH * 0.97)
        tre = np.zeros((WH, WW), f32)
        for k in range(3):
            a = math.radians(-90 + k * 120)
            tre = np.maximum(tre, circle(cx + 10 * math.cos(a), cy + 10 * math.sin(a), 10.5))
        cv.glaze(tre, CRIM_L, 0.6)
        cv.hatch(tre, 0.35, -45 * side, 2.6)
        cv.outline(tre, 1.6)
        cv.fill(ring(cx, cy, 29, 2.4), INK)
        cv.fill(ring(cx, cy, 24.5, 1.2), INK)
        cv.fill(circle(cx, cy, 2.6), INK)
        # a tendril from the ring toward the cartouche, ending in a curl and a dot
        pts = spline([(cx - side * 31, cy - 4), (cx - side * 52, cy - 22), (cx - side * 76, cy - 30),
                      (cx - side * 92, cy - 22), (cx - side * 88, cy - 12), (cx - side * 80, cy - 16)], closed=False)
        cv.fill(taper(pts, 2.0, 1.0), INK)
        cv.fill(circle(cx - side * 98, cy - 34, 2.2), INK)
        leaf = ellipse(cx - side * 58, cy - 36, 7, 3, -30 * side)
        cv.glaze(leaf, CRIM_L, 0.6)
        cv.outline(leaf, 1.2)
    sd_in = card_sd() + 27
    cv.fill(M(np.abs(sd_in) - 0.7), INK, 0.9)
    cv.fill(M(np.abs(sd_in - 3.2) - 0.5), INK, 0.55)


BAN_Y0, BAN_Y1, BAN_X0, BAN_X1 = 886, 958, 70, 530
TITLE_SIZE = 34


def banner(cv, title):
    """A crimson scroll across the window's foot with the title in bone capitals."""
    y0, y1, x0, x1 = BAN_Y0, BAN_Y1, BAN_X0, BAN_X1
    yc = (y0 + y1) / 2
    hh = y1 - y0
    cover = np.zeros((WH, WW), f32)
    for side in (-1, 1):
        xa = CX + side * (CX - x0)              # the band's end
        xo = CX + side * (CX - 26)              # the tail's outer end
        tail = [(xa - side * 2, y0 + 18), (xo, y0 + 18), (xo - side * 18, y0 + 18 + hh / 2), (xo, y1 + 18),
                (xa - side * 2, y1 + 18)]
        tm = poly(tail)
        cover = np.maximum(cover, tm)
        cv.shadow(tm, 2, 3, 3, 0.35)
        cv.fill(tm, CRIM * 0.78)
        cv.hatch(tm, 0.45, 0, 3.0, cross=False)
        cv.fill(box(CX + side * (CX - 54), y0 + 24, 50, 1.4) * tm, GOLD, 0.8)
        cv.fill(box(CX + side * (CX - 54), y1 + 12, 50, 1.4) * tm, GOLD, 0.8)
        cv.outline(tm, 1.8)
        fold = poly([(xa, y0 + 18), (xa, y1), (xa - side * 18, y1 + 18), (xa - side * 18, y0 + 18)])
        cv.fill(fold, CRIM * 0.5)
        cv.hatch(fold, 0.7, 60 * side, 2.6)
        cv.outline(fold, 1.6)
    band = box(CX, yc, x1 - x0, hh, 2)
    cover = np.maximum(cover, band)
    cv.shadow(band, 2, 4, 4, 0.45)
    cv.fill(band, CRIM)
    v = np.abs(Y - yc) / (hh / 2)
    cv.light(band * np.exp(-((Y - (yc - 9)) / 11) ** 2) * (1 - smooth(150, 240, np.abs(X - CX))), (0.55, 0.2, 0.2), 0.4)
    cv.hatch(band, 0.6 * smooth(0.5, 1.0, v), 0, 2.6, cross=False)
    for yy in (y0 + 6, y1 - 6):
        cv.fill(box(CX, yy, x1 - x0 - 12, 1.8), GOLD, 0.95)
    cv.outline(band, 2.0)
    size = TITLE_SIZE
    tw = text_width(title, size, FONT_TITLE, 2.5)
    if tw > (x1 - x0) - 50:
        size = size * ((x1 - x0) - 50) / tw
    tm = text_mask(title, size, CX, yc + 1.5, FONT_TITLE, track=2.5)
    cv.fill(ndimage.gaussian_filter(ndimage.shift(tm, (1.6 * K, 1.2 * K), order=1), 0.9 * K), INK, 0.9)
    cv.fill(tm, BONE)
    cv.fill(tm * smooth(yc - 10, yc + 14, Y), GOLD_L * 0.92, 0.5)
    return ndimage.maximum_filter(cover, 3)


def numeral(cv, s):
    size = 34
    tm = text_mask(s, size, CX, CART_Y + 1.5, FONT_NUM, track=1.5)
    cv.fill(ndimage.gaussian_filter(ndimage.shift(tm, (1.0 * K, 1.0 * K), order=1), 0.7 * K), INK, 0.9)
    cv.fill(tm, GOLD_L)
    cv.fill(tm * smooth(CART_Y - 10, CART_Y + 14, Y), GOLD * 0.9, 0.6)


def to_image(cv, alpha):
    rgba = np.dstack([np.clip(cv.rgb, 0, 1), alpha])
    im = Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA")
    return im.resize((CW, CH), Image.LANCZOS)


_CHROME = {}


def chrome():
    """The parts every face shares (paper, spandrels, the lit brass), built once."""
    if not _CHROME:
        cv = Canvas(PARCH, 7)
        parchment(cv)
        spandrels(cv)
        win = window_mask()
        br = Brass()
        frame_brass(br)
        rgb_b, mb = br.render()
        _CHROME.update(rgb=cv.rgb.copy(), win=win, wsd=sdf(win), brass=rgb_b, mb=mb)
    return _CHROME


def face(name, num, title, scene, seed):
    c = chrome()
    art = Canvas(PARCH, seed + 500)
    parchment(art, 0.8)
    scene(art)
    cv = Canvas(PARCH, seed)
    cv.rgb = c["rgb"].copy()
    win, wsd = c["win"], c["wsd"]
    cv.fill(win, art.rgb)
    cv.glaze(smooth(-12, 0, wsd) * win, INK, 0.30)
    cv.fill(M(np.abs(wsd + 4.8) - 0.6), INK, 0.85)
    cv.fill(M(np.abs(wsd - 4.8) - 0.6), INK, 0.85)
    ban = banner(cv, title)
    mb = c["mb"] * (1 - ban)
    cv.shadow(mb, 1.5, 2.5, 2.5, 0.55)
    cv.fill(mb, c["brass"])
    numeral(cv, num)
    sd = card_sd()
    cv.fill(M(np.abs(sd + 0.9) - 0.9), INK, 0.8)              # a dark lip on the card's edge
    return to_image(cv, M(sd))


# ================================================================ scene helpers
def sky(cv, top, bottom, y0=WIN_APEX, y1=760, lines=0.32, angle=0.0, spacing=3.2, k=1.0):
    """A night wash (multiplied into the paper) with engraved lines, darker toward the top."""
    t = lin(0, y0, 0, y1)[..., None]
    col = np.asarray(top, f32) * (1 - t) + np.asarray(bottom, f32) * t
    cv.rgb = cv.rgb * (1 - k) + cv.rgb * col / PARCH * k
    if lines:
        cv.hatch(np.ones((WH, WW), f32), lines * (1.15 - 0.75 * t[..., 0]), angle, spacing, cross=False, wob=0.05)


def puff_cloud(cv, lobes, light, dark=None, lite=None, spacing=2.8, ink=0.9, flat=1.3):
    """An engraved cloud: overlapping lobes (flattened balls) drawn back to front, each lit as a ball and hatched with
    level lines, only their upper arcs inked so the billows read; one outline round the whole bank."""
    dark = NIGHT * 0.5 if dark is None else dark
    lite = NIGHT_L * 1.2 if lite is None else lite
    L = np.array((light[0], light[1], 0.55), f32)
    L /= np.linalg.norm(L)
    union = np.zeros((WH, WW), f32)
    for (x, y, r) in lobes:
        rx, ry = r * flat, r
        nx, ny = (X - x) / rx, (Y - y) / ry
        rr = np.sqrt(nx * nx + ny * ny)
        m = M((rr - 1) * ry)
        nz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
        lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1) * (1 - 0.35 * smooth(-0.2, 0.9, ny))
        col = dark + (lite - dark) * lam[..., None]
        cv.fill(m, col)
        cv.hatch(m, 0.62 * (1 - lam) + 0.04, 0, spacing, cross=False)
        cv.fill(M(np.abs(rr - 1) * ry - 1.3) * m * np.clip(nx * L[0] + ny * L[1], 0, 1), BONE, 0.55)
        cv.fill(M(np.abs(rr - 1) * ry - 0.75) * smooth(0.45, 0.0, ny), INK, ink)
        union = np.maximum(union, m)
    cv.outline(union, 1.5, INK, ink)


def jag(p0, p1, n, amp, rng):
    pts = [p0]
    for i in range(1, n):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        dx, dy = p1[1] - p0[1], -(p1[0] - p0[0])
        L = math.hypot(dx, dy)
        o = rng.uniform(-amp, amp) * (0.5 + 0.5 * math.sin(math.pi * t))
        o = math.copysign(max(abs(o), amp * 0.35), o) * (1 if i % 2 else -1)
        pts.append((x + dx / L * o, y + dy / L * o))
    pts.append(p1)
    return pts


def star4(cx, cy, r, w=0.22):
    """A four-point sparkle, r to the tips."""
    u, v = np.abs(X - cx), np.abs(Y - cy)
    return M((np.minimum(u / (r * w) + v / r, v / (r * w) + u / r) - 1) * r * 0.35)


def bolt(cv, main, branches, w0=9.0, w1=4.0):
    m = taper(main, w0, w1)
    for b in branches:
        m = U(m, taper(b, w1 * 0.9, 0.8))
    g = ndimage.gaussian_filter(m, 16 * K)
    cv.light(g / (g.max() + 1e-6), (0.72, 0.80, 1.0), 0.85)
    g = ndimage.gaussian_filter(m, 4 * K)
    cv.light(g / (g.max() + 1e-6), (0.90, 0.94, 1.0), 0.9)
    cv.outline(m, 1.6, INK, 0.75)
    cv.fill(m, (0.98, 0.99, 1.0))
    return m


# ================================================================ XVI  The Tower
def tower_scene(cv):
    rng = np.random.default_rng(16)
    sky(cv, NIGHT * 0.55, NIGHT_L * 0.85, lines=0.30, angle=96, spacing=3.4)
    sx, cut_y = 300, 246
    # storm clouds rolling in from both sides of the arch
    puff_cloud(cv, [(70, 250, 44), (130, 236, 40), (40, 300, 36), (100, 290, 34), (175, 214, 34), (150, 268, 26),
                    (220, 196, 26), (205, 236, 22)], light=(1.0, 0.4))
    puff_cloud(cv, [(540, 250, 44), (480, 236, 40), (560, 300, 36), (505, 290, 34), (425, 214, 34), (455, 268, 26),
                    (382, 196, 26), (400, 236, 22)], light=(-1.0, 0.4))
    puff_cloud(cv, [(30, 420, 30), (80, 430, 26), (124, 438, 18)], light=(0.9, -0.2), lite=NIGHT_L * 0.9)
    puff_cloud(cv, [(570, 460, 30), (520, 470, 24), (482, 476, 16)], light=(-0.9, -0.2), lite=NIGHT_L * 0.9)
    cv.light(radial(sx, cut_y - 40, 330) ** 2.2, (0.70, 0.78, 0.95), 0.55)
    # --- distant school roofs and spires
    far = poly([(46, 790), (80, 770), (96, 730, 1), (110, 640, 1), (124, 730, 1), (150, 742), (196, 742),
                (204, 712, 1), (218, 712, 1), (228, 765), (372, 765), (380, 708, 1), (394, 708, 1), (404, 748),
                (440, 748), (452, 690, 1), (466, 612, 1), (480, 690, 1), (494, 740), (554, 770), (554, 910),
                (46, 910)])
    cv.fill(far, NIGHT * 0.62)
    cv.hatch(far, 0.55, 0, 3.0, cross=False)
    cv.fill(M(np.abs(sdf(far)) - 0.6), NIGHT_L, 0.8)
    for wx, wy in ((172, 760), (190, 760), (420, 770), (520, 790), (106, 700)):
        w = box(wx, wy, 5, 11, 2.5)
        cv.light(radial(wx, wy, 16), GOLD, 0.35)
        cv.fill(w, GOLD_L)
    near = poly(spline([(30, 860), (150, 818), (300, 806), (450, 818), (570, 860), (570, 940, 1), (30, 940, 1)]))
    cv.fill(near, INK * 1.4)
    cv.fill(M(np.abs(sdf(near)) - 0.9) * (Y < 870), NIGHT_L * 1.1, 0.7)
    # --- the tower: shaft, belfry, parapet with pinnacles, slate spire; the strike lights the left faces
    fl, edge, sr = 238, 330, 362
    lit = X < edge
    STONE_L, STONE_D = BONE, PARCH * 0.80
    shaft = box((fl + sr) / 2, 645, sr - fl, 350)
    cv.fill(shaft, np.where(lit[..., None], STONE_L, STONE_D))
    tone = np.where(lit, 0.02 + 0.22 * lin(fl, 0, edge, 0), 0.72)
    cv.hatch(shaft, tone, 0, 3.0)
    cv.glaze(shaft * ~lit, NIGHT_L, 0.45)
    course = M(np.abs(((Y - 470) % 15) - 7.5) - 6.9)
    joints = M(np.abs((((X - fl) + 13 * (np.floor((Y - 470) / 15) % 2)) % 26) - 13) - 12.4) * (1 - course)
    cv.fill(shaft * U(course, joints), INK, np.where(lit, 0.32, 0.8))
    for bx, bw, tn in ((fl + 6, 14, 0.12), (edge + 2, 10, 0.3), (sr - 5, 10, 0.85)):
        bm = U(box(bx, 700, bw, 240), poly([(bx - bw / 2, 581), (bx + bw / 2, 581), (bx + bw / 2 - 2, 556),
                                            (bx - bw / 2 + 2, 556)]))
        cv.fill(bm, STONE_L if bx < edge else STONE_D)
        cv.hatch(bm, tn, 90, 2.6)
        cv.outline(bm, 1.5)
    ccx, ccy, cr = 284, 565, 30
    cm = circle(ccx, ccy, cr)
    cv.shadow(cm, 2, 3, 2, 0.4)
    cv.fill(cm, BONE)
    cv.glaze(cm, GOLD, 0.45)
    cv.hatch(cm, 0.35 * lin(ccx - cr, 0, ccx + cr, 0), 90, 2.2, cross=False)
    cv.fill(ring(ccx, ccy, cr - 4, 1.2), INK)
    for i in range(12):
        a = i * math.pi / 6
        r0 = cr - 12 if i % 3 == 0 else cr - 9
        cv.fill(seg(ccx + math.cos(a) * r0, ccy + math.sin(a) * r0, ccx + math.cos(a) * (cr - 5),
                    ccy + math.sin(a) * (cr - 5), 2.4 if i % 3 == 0 else 1.3), INK)
    cv.fill(seg(ccx, ccy, ccx - 1, ccy - 19, 3.2, 1.6), INK)              # a minute to midnight
    cv.fill(seg(ccx, ccy, ccx + 2, ccy - 13, 4.0, 2.2), INK)
    cv.fill(circle(ccx, ccy, 3), INK)
    cv.outline(cm, 2.4)
    for wx, wy in ((262, 668), (306, 668), (284, 748)):
        wm = U(box(wx, wy + 6, 14, 36), poly([(wx - 7, wy - 12), (wx, wy - 26), (wx + 7, wy - 12)]))
        cv.light(radial(wx, wy, 30), GOLD, 0.3)
        cv.fill(wm, GOLD_L)
        cv.glaze(wm * lin(0, wy - 26, 0, wy + 24), GOLD, 0.9)
        cv.fill(box(wx, wy + 2, 1.6, 40) * wm, INK, 0.8)
        cv.fill(box(wx, wy + 2, 14, 1.4) * wm, INK, 0.8)
        cv.outline(wm, 1.6)
    cv.outline(shaft, 2.4)
    cv.fill(seg(edge, 470, edge, 820, 1.6), INK)
    # belfry
    bel = box(300, 424, 140, 84)
    cv.fill(bel, np.where(lit[..., None], STONE_L, STONE_D))
    cv.hatch(bel, np.where(lit, 0.08, 0.75), 0, 3.0)
    cv.glaze(bel * ~lit, NIGHT_L, 0.45)
    sill = box(300, 466, 152, 10)
    cv.fill(sill, np.where(lit[..., None], STONE_L, STONE_D))
    cv.hatch(sill, np.where(lit, 0.25, 0.8), 90, 2.2)
    cv.outline(sill, 1.6)
    for ox in (264, 306):
        op = U(box(ox, 436, 30, 44), poly([(ox - 15, 414), (ox, 386), (ox + 15, 414)]))
        cv.fill(op, INK * 1.3)
        bm = poly(spline([(ox - 5, 404), (ox + 5, 404), (ox + 8, 420), (ox + 13, 444, 1), (ox - 13, 444, 1),
                          (ox - 8, 420)])) * op
        cv.fill(bm, GOLD)
        cv.light(bm * lin(ox + 12, 0, ox - 12, 0), GOLD_L, 0.7)
        cv.hatch(bm, 0.5 * lin(ox - 12, 0, ox + 14, 0), 90, 2.2, cross=False)
        cv.fill(circle(ox, 447, 3) * op, GOLD)
        cv.outline(bm, 1.2)
        cv.outline(op, 2.0)
    cv.outline(bel, 2.4)
    par = U(box(300, 374, 152, 16), *[box(x, 362, 9, 8) for x in np.arange(232, 372, 16)])
    cv.fill(par, np.where(lit[..., None], STONE_L, STONE_D))
    cv.hatch(par, np.where(lit, 0.18, 0.8), 90, 2.4)
    cv.outline(par, 1.8)
    for px_ in (230, 370):
        pin = poly([(px_ - 7, 382), (px_ + 7, 382), (px_ + 7, 345), (px_, 296), (px_ - 7, 345)])
        cv.fill(pin, STONE_L if px_ < 300 else STONE_D)
        cv.hatch(pin, np.where(X < px_, 0.1, 0.85), 90, 2.2)
        cv.outline(pin, 1.6)
        cv.fill(circle(px_, 294, 3.4), BONE)
        cv.outline(circle(px_, 294, 3.4), 1.3)
    # the slate spire, its tip blown off
    apex = (300, 192)
    bl, brr, ridge = (246, 366), (354, 366), (318, 366)

    def on(p, q, y):
        t = (y - p[1]) / (q[1] - p[1])
        return (p[0] + (q[0] - p[0]) * t, y)
    cl, cr_, cm_ = on(bl, apex, cut_y), on(brr, apex, cut_y), on(ridge, apex, cut_y)
    crack = [cl, (cl[0] + 8, cut_y - 7), (cl[0] + 15, cut_y + 4), (cm_[0] - 4, cut_y - 10), (cm_[0] + 6, cut_y + 2),
             (cr_[0] - 6, cut_y - 6), cr_]
    spire = poly([bl, brr] + crack[::-1])
    face_l = poly([bl, ridge, (cm_[0] + 6, cut_y + 2), (cm_[0] - 4, cut_y - 10), (cl[0] + 15, cut_y + 4),
                   (cl[0] + 8, cut_y - 7), cl])
    cv.fill(spire, CRIM * 0.75)
    cv.fill(face_l, CRIM_L)
    rowh = 9.0
    rowi = np.floor((Y - cut_y) / rowh)
    xo = (X - 300) + (rowi % 2) * 5
    cell = np.hypot(((xo % 10) - 5) / 5, ((Y - cut_y) % rowh) / rowh - 1.0)
    cv.hatch(spire, np.where(face_l > 0.5, 0.12 + 0.25 * lin(240, 0, 318, 0), 0.7), 90, 2.4)
    cv.fill(M(np.abs(cell - 0.95) * 4 - 0.35) * spire, INK, 0.75)
    cv.outline(spire, 2.4)
    cv.fill(seg(ridge[0], ridge[1], cm_[0] + 6, cut_y + 2, 1.6), INK)
    # falling slates and stone chips down the dark side
    chips = [(356, 296, 16, 9, 30), (386, 350, 14, 8, -20), (404, 420, 15, 8, 55), (372, 486, 12, 7, 10),
             (416, 548, 13, 7, -40), (222, 306, 13, 7, -35), (200, 372, 11, 6, 20), (430, 300, 11, 6, 70),
             (396, 640, 10, 6, -15)]
    for (x, y, w, h, a) in chips:
        cv.fill(seg(x - 2, y - 7, x - 7, y - 34, 2.0, 0.3), NIGHT_L * 1.3, 0.6)
        sm = box(x, y, w, h, 1.0, a)
        cv.fill(sm, CRIM * 0.8)
        cv.rim(sm, -0.6, -0.8, 1.3, CRIM_L * 1.4, 1.0)
        cv.outline(sm, 1.4)
    # --- the bolt, straight down from the arch's point, with branches either way
    main = jag((300, 104), (sx - 2, cut_y - 4), 7, 20, rng)
    b1 = jag(main[2], (196, 196), 4, 8, rng)
    b2 = jag(main[3], (404, 214), 4, 8, rng)
    b3 = jag(b1[2], (150, 238), 3, 6, rng)
    bolt(cv, main, [b1, b2, b3])
    # the burst at the break: a glow and gold sparks
    cv.light(radial(sx, cut_y - 4, 60) ** 1.6, GOLD_L, 1.0)
    cv.light(radial(sx, cut_y - 4, 22), WHITE, 0.9)
    for i in range(18):
        a = rng.uniform(-math.pi, 0.25)
        d = rng.uniform(24, 84)
        px_, py_ = sx + math.cos(a) * d, cut_y - 4 + math.sin(a) * d * 0.85
        r = rng.uniform(3.0, 6.5) if i % 3 == 0 else rng.uniform(1.6, 3.0)
        cv.light(radial(px_, py_, r * 3.2), GOLD_L, 0.7)
        cv.fill(star4(px_, py_, r * 2.0, 0.2) if r > 2.9 else circle(px_, py_, r * 0.7), (1.0, 0.96, 0.82))


# ================================================================ shared scene pieces
def stars(cv, rng, n, avoid=None, y0=WIN_APEX + 10, y1=520, big=0.25):
    for i in range(n):
        x, y = rng.uniform(56, 544), rng.uniform(y0, y1)
        if y < arch_y(x) + 8:
            continue
        if avoid is not None and avoid[int(y * K), int(x * K)] > 0.1:
            continue
        if rng.random() < big:
            r = rng.uniform(4.5, 7.5)
            cv.light(radial(x, y, r * 2.2), GOLD_L, 0.45)
            cv.fill(star4(x, y, r, 0.18), BONE)
        else:
            cv.fill(circle(x, y, rng.uniform(0.8, 1.6)), BONE, rng.uniform(0.6, 1.0))


def engraved_moon(cv, cx, cy, r, light=(-0.45, -0.35), halo=0.55, craters=None):
    """A full moon: bone with a gold wash, soft seas, ringed craters, contour-hatched limb shading."""
    if halo:
        cv.light(radial(cx, cy, r * 2.4) ** 2.2, GOLD_L, halo)
        cv.light(radial(cx, cy, r * 1.35) ** 1.5, BONE, halo * 0.6)
    m = circle(cx, cy, r)
    cv.fill(m, BONE)
    cv.glaze(m, GOLD_L, 0.55)
    seas = U(ellipse(cx - 0.30 * r, cy - 0.25 * r, 0.32 * r, 0.24 * r, 20), ellipse(cx + 0.18 * r, cy - 0.32 * r, 0.22 * r, 0.17 * r),
             ellipse(cx + 0.30 * r, cy + 0.12 * r, 0.20 * r, 0.26 * r, -30), ellipse(cx - 0.12 * r, cy + 0.30 * r, 0.18 * r, 0.12 * r))
    seas = ndimage.gaussian_filter(seas, 0.05 * r * K) * m
    cv.glaze(seas, GOLD, 0.45)
    cv.hatch(seas, 0.22, 20, 2.4, cross=False)
    d = np.hypot(X - cx, Y - cy)
    L = np.array((light[0], light[1], 0.75), f32)
    L /= np.linalg.norm(L)
    nx, ny = (X - cx) / r, (Y - cy) / r
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    for (u, v, cr) in (craters or ((-0.42, 0.18, 0.13), (0.38, -0.42, 0.09), (0.10, 0.52, 0.11), (0.52, 0.30, 0.07),
                                   (-0.20, -0.55, 0.07), (0.05, 0.05, 0.06), (-0.60, -0.15, 0.06))):
        x, y, rr = cx + u * r, cy + v * r, cr * r
        cm = circle(x, y, rr)
        cv.glaze(cm, GOLD, 0.35)
        cv.fill(M(np.abs(np.hypot(X - x, Y - y) - rr) - 0.6) * smooth(-0.2, 0.4, (Y - y) / rr + (X - x) / rr), INK, 0.7)
        cv.fill(M(np.abs(np.hypot(X - x, Y - y) - rr) - 0.7) * smooth(0.2, -0.4, (Y - y) / rr + (X - x) / rr), BONE, 0.9)
    cv.hatch(m, 0.55 * (1 - lam) ** 2.4, 0, 2.6, cross=False, phase=(r - d) / 2.6)
    cv.outline(m, 2.2)
    return m


def silhouette(cv, m, light, rim_w=1.8, col=None, rim=None, a=0.95):
    col = INK if col is None else col
    cv.fill(m, col)
    cv.rim(m, light[0], light[1], rim_w, BONE if rim is None else rim, a)


def flame(cv, x, y, h, glow=0.6):
    """A candle flame with its glow; (x, y) is the wick, h the flame height."""
    cv.light(radial(x, y - h * 0.5, h * 4.5) ** 2, GOLD, glow)
    cv.light(radial(x, y - h * 0.5, h * 1.6) ** 1.5, GOLD_L, glow)
    f = poly(spline([(x, y - h, 1), (x + h * 0.30, y - h * 0.35), (x + h * 0.22, y), (x - h * 0.22, y),
                     (x - h * 0.30, y - h * 0.35)], n=10))
    cv.fill(f, GOLD_L)
    cv.fill(ellipse(x, y - h * 0.25, h * 0.12, h * 0.28), WHITE, 0.9)
    cv.outline(f, max(0.9, h * 0.06), CRIM * 0.8, 0.8)
    cv.fill(seg(x, y + 1, x, y - h * 0.15, max(1.0, h * 0.08)), INK)


def candle(cv, x, y, h, w, glow=0.6, holder=True):
    """A bone candle standing at (x, y) (its foot), h tall, w wide, on a small brass cup."""
    body = box(x, y - h / 2, w, h, w * 0.2)
    top = y - h
    cv.fill(body, BONE)
    cv.hatch(body, 0.55 * lin(x - w / 2, 0, x + w / 2, 0) ** 1.5, 90, max(1.6, w * 0.16), cross=False)
    drip = seg(x - w * 0.28, top + 1, x - w * 0.28, top + h * 0.22, w * 0.22, w * 0.18)
    cv.fill(drip, BONE)
    cv.outline(U(body, drip), max(1.0, w * 0.10))
    if holder:
        cup = U(ellipse(x, y, w * 1.4, w * 0.38), box(x, y - w * 0.1, w * 1.2, w * 0.4))
        cv.fill(cup, GOLD)
        cv.hatch(cup, 0.5 * lin(x - w, 0, x + w, 0), 90, max(1.6, w * 0.16), cross=False)
        cv.outline(cup, max(1.0, w * 0.10))
    flame(cv, x, top, w * 2.0, glow)


# ================================================================ 0  The Fool
def fool_scene(cv):
    rng = np.random.default_rng(0)
    sky(cv, NIGHT * 0.50, NIGHT_L * 0.95, lines=0.34, angle=0, spacing=3.2)
    mx, my, mr = 330, 404, 142
    stars(cv, rng, 70, circle(mx, my, mr * 1.5))
    engraved_moon(cv, mx, my, mr)
    # far below in the abyss: the school's roofs and spires, hazy
    far = poly([(300, 886), (300, 760), (330, 750), (342, 700, 1), (352, 640, 1), (362, 700, 1), (380, 740),
                (420, 740), (428, 712, 1), (446, 712, 1), (452, 744), (486, 744), (498, 690, 1), (510, 610, 1),
                (522, 690, 1), (536, 736), (554, 736), (554, 886)])
    cv.fill(far, NIGHT * 0.95)
    cv.glaze(far, NIGHT_L, 0.5)
    cv.hatch(far, 0.45, 90, 3.0, cross=False)
    cv.outline(far, 1.2, INK, 0.6)
    for wx, wy in ((396, 770), (412, 770), (470, 776), (510, 720), (540, 790)):
        cv.light(radial(wx, wy, 12), GOLD, 0.4)
        cv.fill(box(wx, wy, 4, 8, 2), GOLD_L)
    cv.light(smooth(690, 880, Y) * smooth(290, 330, X), NIGHT_L, 0.35)          # mist rising from below
    # the rooftop ledge: a projecting slab over a stone wall, a pinnacle at the far end
    wall = poly([(40, 658), (292, 658), (292, 920), (40, 920)])
    cv.fill(wall, PARCH * 0.78)
    course = M(np.abs(((Y - 658) % 24) - 12) - 10.9)
    joints = M(np.abs((((X - 40) + 28 * (np.floor((Y - 658) / 24) % 2)) % 56) - 28) - 26.9) * (1 - course)
    cv.hatch(wall, 0.10 + 0.32 * lin(0, 658, 0, 880) + 0.25 * lin(290, 0, 60, 0), 0, 3.0, cross=False)
    cv.glaze(wall, NIGHT_L, 0.4)
    cv.fill(wall * U(course, joints), INK, 0.9)
    cv.fill(wall * ndimage.shift(U(course, joints), (-1.5 * K, -1.5 * K), order=1) * (1 - U(course, joints)),
            NIGHT_L * 1.3, 0.5)
    cv.rim(wall, 1, 0, 2.2, NIGHT_L * 1.3, 0.9)
    cv.outline(wall, 2.0)
    slab = poly([(40, 636), (300, 636), (304, 642), (304, 660), (40, 660)])
    cv.fill(slab, PARCH * 0.92)
    cv.hatch(slab, np.where(Y < 642, 0.05, 0.45), 0, 2.6)
    cv.glaze(slab * (Y > 642), NIGHT_L, 0.5)
    cv.fill(box(172, 638, 264, 3), BONE)
    cv.outline(slab, 2.0)
    pin = poly([(62, 636), (98, 636), (98, 560), (80, 470, 1), (62, 560)])
    cv.fill(pin, PARCH * 0.85)
    cv.hatch(pin, np.where(X < 80, 0.65, 0.25), 90, 2.6)
    cv.glaze(pin * (X < 80), NIGHT_L, 0.5)
    for yy_ in (580, 610):
        cv.fill(box(80, yy_, 38, 2.0), INK, 0.8)
    cv.outline(pin, 1.8)
    cv.fill(circle(80, 466, 4.5), BONE)
    cv.outline(circle(80, 466, 4.5), 1.4)
    # the dare: a sealed letter hanging in the air, glowing
    ex, ey, er = 470, 250, -14
    cv.light(radial(ex, ey, 80) ** 1.8, GOLD_L, 0.75)
    env = box(ex, ey, 66, 44, 2.5, er)
    cv.shadow(env, 2, 3, 2, 0.35)
    cv.fill(env, BONE)
    cv.hatch(env, 0.18 * lin(ex - 30, ey - 20, ex + 30, ey + 20), er, 2.2, cross=False)

    def W(u, v):
        th = math.radians(er)
        return (ex + u * math.cos(th) - v * math.sin(th), ey + u * math.sin(th) + v * math.cos(th))
    cv.fill(stroke([W(-31, -20), W(0, 3), W(31, -20)], 1.6), INK)
    cv.fill(stroke([W(-31, 20), W(-6, 0)], 1.2), INK, 0.8)
    cv.fill(stroke([W(31, 20), W(6, 0)], 1.2), INK, 0.8)
    cv.outline(env, 2.0)
    seal = circle(*W(0, 3), 9.5)
    th_ = np.arctan2(Y - W(0, 3)[1], X - W(0, 3)[0])
    seal = M(np.hypot(X - W(0, 3)[0], Y - W(0, 3)[1]) - 9.5 - 1.0 * np.cos(9 * th_))
    cv.fill(seal, CRIM)
    cv.light(seal * radial(W(-3, 0)[0], W(-3, 0)[1], 8), CRIM_L * 1.3, 0.9)
    cv.fill(ring(*W(0, 3), 5, 1.2), INK, 0.6)
    cv.outline(seal, 1.4)
    for (u, v, r) in ((-48, -30, 5), (44, -34, 4), (52, 26, 5.5), (-46, 30, 3.5)):
        cv.fill(star4(*W(u, v), r, 0.2), GOLD_L)
    # the student, stepping off the ledge (ink silhouette with a moonlit rim)
    body = student_mask()
    cv.fill(body, INK)
    cv.rim(body, 0.7, -0.7, 1.8, BONE, 0.95)
    cv.rim(body, -0.6, -0.8, 1.2, NIGHT_L * 1.4, 0.8)
    # the long striped scarf, streaming back in the wind
    path = []
    for i in range(40):
        t = i / 39
        x = 282 - 200 * t
        y = 452 - 40 * t + 16 * math.sin(t * 7.0 + 0.5) * t
        path.append((x, y))
    scarf = U(taper(path, 15, 10), ellipse(285, 455, 13, 9, -10))
    tail2 = taper([(280, 462), (270, 490), (262, 512), (248, 528)], 12, 9)
    sm = U(scarf, tail2)
    cv.fill(sm, CRIM_L)
    stripe = M(np.abs(((X + 0.3 * Y) % 22) - 11) - 3.2)
    cv.fill(sm * stripe, BONE, 0.95)
    cv.hatch(sm, 0.4 * smooth(-0.2, 1, (Y - 440) / 30), 90, 2.2, cross=False)
    fr = U(*[seg(path[-1][0], path[-1][1] + o, path[-1][0] - 9, path[-1][1] + o * 1.2 - 2, 1.6) for o in (-5, -1.5, 2, 5.5)])
    cv.fill(fr, CRIM_L)
    cv.outline(U(sm, fr), 1.6)
    # the black cat at their heels, looking up
    cx, by, s = 186, 636, 1.35
    cat = blob([(cx - 20 * s, by, 1), (cx - 25 * s, by - 13 * s), (cx - 21 * s, by - 30 * s), (cx - 11 * s, by - 41 * s),
                (cx - 4 * s, by - 50 * s), (cx - 7 * s, by - 63 * s, 1), (cx + 1 * s, by - 56 * s), (cx + 9 * s, by - 63 * s, 1),
                (cx + 12 * s, by - 51 * s), (cx + 13 * s, by - 44 * s), (cx + 7 * s, by - 38 * s), (cx + 6 * s, by - 22 * s),
                (cx + 9 * s, by, 1)], n=12)
    tail = taper(spline([(cx - 22 * s, by - 4), (cx - 40 * s, by - 10 * s), (cx - 44 * s, by - 30 * s),
                         (cx - 36 * s, by - 44 * s), (cx - 30 * s, by - 40 * s)], closed=False, n=8), 7, 4.5)
    catm = U(cat, tail)
    cv.fill(catm, INK)
    cv.rim(catm, 0.7, -0.7, 1.6, BONE, 0.9)
    cv.fill(ellipse(cx + 7 * s, by - 50 * s, 3.2, 1.8, -20), GOLD_L)


# ================================================================ XVIII  The Moon
def raven_pts(rx, ry, s=1.0):
    """A perched raven in profile facing left, beak raised and open (calling); (rx, ry) is the perch under its feet."""
    P = [(-70, -112, 1), (-50, -108), (-34, -106, 1), (-22, -112), (-6, -110), (6, -98), (22, -84), (42, -72),
         (58, -54), (68, -36), (100, -4, 1), (90, 2, 1), (76, -2, 1), (56, -12), (32, -6), (10, -6), (-8, -18),
         (-20, -40), (-26, -58), (-34, -66, 1), (-30, -72), (-36, -80, 1), (-32, -84), (-60, -92, 1), (-36, -94, 1)]
    return [(rx + p[0] * s, ry + p[1] * s) + tuple(p[2:]) for p in P]


def wolf_mask(bx, by, s=1.0):
    """A sitting wolf in profile facing right, head thrown back howling, built from smooth parts."""
    P = lambda x, y: (bx + x * s, by + y * s)

    def tp(pts, w0, w1):
        return taper([P(*p) for p in pts], w0 * s, w1 * s)
    parts = [
        ellipse(*P(-26, -44), 36 * s, 42 * s, -10),                                  # haunch
        tp([(-14, -40), (0, -86), (12, -122)], 62, 46),                              # torso, upright
        tp([(10, -118), (18, -146), (24, -164)], 42, 32),                            # neck
        ellipse(*P(26, -170), 22 * s, 18 * s, -45),                                  # skull
        tp([(28, -176), (44, -196), (60, -214)], 22, 11),                            # muzzle, raised
        tp([(32, -166), (44, -180), (54, -194)], 12, 6),                             # lower jaw, open
        poly([P(8, -178), P(-2, -204), P(22, -186)]),                                # ear
        tp([(30, -84), (34, -40), (36, -6)], 16, 11),                                # front legs
        tp([(18, -84), (20, -40), (22, -6)], 15, 11),
        ellipse(*P(42, -4), 12 * s, 5 * s), ellipse(*P(28, -4), 11 * s, 5 * s),       # paws
        ellipse(*P(-14, -6), 24 * s, 7 * s),                                         # hind foot
        tp([(-44, -14), (-66, -12), (-94, -6)], 22, 8),                              # bushy tail on the ground
    ]
    for (x, y) in ((32, -152), (37, -138), (41, -124)):                             # the chest ruff
        parts.append(poly([P(x - 7, y - 5), P(x + 5, y - 2), P(x + 4, y + 9)]))
    m = U(*parts)
    gap = tp([(36, -180), (52, -200)], 4.5, 2.5)                                     # the open mouth
    m = sub(m, gap)
    return smooth(0.35, 0.65, ndimage.gaussian_filter(m, 0.8 * K))


def student_mask():
    """The Fool: a student mid-step off the ledge, facing right, one arm reaching for the dare."""
    parts = [
        circle(290, 428, 19),                                                         # head
        blob([(272, 418), (284, 404), (302, 406), (310, 420), (302, 416), (292, 416), (284, 424), (272, 432)]),
        circle(309, 433, 4.2),                                                        # nose
        seg(286, 446, 284, 464, 14),                                                  # neck
        blob([(260, 470), (284, 460), (304, 466), (306, 484), (300, 508), (298, 530), (306, 556, 1), (256, 562, 1),
              (260, 530), (258, 500)]),                                               # blazer
        poly([(262, 540), (258, 562), (238, 572, 1), (250, 548)]),                    # blazer tail in the wind
        taper([(276, 544), (264, 592), (246, 632)], 23, 12),                          # rear leg
        ellipse(252, 636, 17, 6, 4),                                                  # rear shoe
        taper([(286, 542), (318, 574), (344, 602)], 23, 12),                          # front leg, stepping off
        ellipse(354, 604, 16, 6.5, -12),                                              # front shoe
        taper([(292, 472), (320, 444), (346, 414)], 16, 10),                          # arm reaching for the dare
        ellipse(352, 406, 10, 6, -48), seg(348, 412, 344, 400, 3.6),                  # hand and thumb
        taper([(270, 476), (246, 498), (222, 512)], 16, 10),                          # arm out for balance
        circle(218, 514, 6.5),
    ]
    return smooth(0.35, 0.65, ndimage.gaussian_filter(U(*parts), 1.0 * K))


def seeker_robe():
    """The hooded seeker: a peaked cowl turned toward the corridor, a long robe, the lantern sleeve raised."""
    robe = blob([(150, 540), (164, 510), (190, 486, 1), (214, 494), (232, 512), (242, 528, 1), (242, 552), (236, 570),
                 (246, 594), (252, 640), (262, 760), (280, 882, 1), (120, 886, 1), (132, 760), (140, 640),
                 (146, 590)], n=12)
    sleeve = blob([(228, 580), (264, 550), (296, 524, 1), (308, 538, 1), (280, 580), (252, 622)], n=10)
    hole = blob([(220, 514), (238, 526), (240, 550), (232, 568), (216, 566), (208, 540)], n=10)
    return U(robe, sleeve), hole


def moon_scene(cv):
    rng = np.random.default_rng(18)
    sky(cv, NIGHT * 0.42, NIGHT_L * 0.80, lines=0.36, angle=0, spacing=3.2, y1=660)
    mx, my, mr = 300, 300, 112
    # rays: alternating long and short wedges
    th = np.arctan2(Y - my, X - mx)
    d = np.hypot(X - mx, Y - my)
    nr = 28
    ph = (th / (2 * math.pi) * nr) % 1.0
    wedge = M((np.abs(ph - 0.5) - 0.13) * d * 2 * math.pi / nr)
    idx = np.floor(th / (2 * math.pi) * nr + nr) % 2
    reach = np.where(idx == 0, mr + 70, mr + 44)
    rays = wedge * smooth(reach, reach - 30, d) * (d > mr)
    cv.glaze(rays, GOLD_L, 0.0)
    cv.light(rays, GOLD, 0.55)
    cv.hatch(rays, 0.25, 0, 2.6, cross=False)
    stars(cv, rng, 60, circle(mx, my, mr + 80), y1=560)
    engraved_moon(cv, mx, my, mr, halo=0.45)
    # far hills on the horizon
    hills = poly(spline([(30, 640), (120, 612), (210, 626), (300, 606), (390, 624), (480, 610), (570, 636),
                         (570, 920, 1), (30, 920, 1)]))
    cv.fill(hills, NIGHT * 0.9)
    cv.hatch(hills, 0.5, 0, 3.0, cross=False)
    cv.fill(M(np.abs(sdf(hills)) - 0.9) * (Y < 650), NIGHT_L * 1.2, 0.8)
    # the two spires, inner faces moonlit
    for side in (-1, 1):
        x0 = CX + side * 190
        wdt = 70
        tw = box(x0, 740, wdt, 420)
        inner = (X - x0) * side < 0
        cv.fill(tw, np.where(inner[..., None], BONE, PARCH * 0.7))
        cv.hatch(tw, np.where(inner, 0.10 + 0.25 * np.abs(X - x0) / 35 * 0, 0.72), 0, 3.0)
        cv.glaze(tw * ~inner, NIGHT_L, 0.55)
        course = M(np.abs(((Y - 520) % 16) - 8) - 7.4)
        cv.fill(tw * course, INK, 0.45)
        roof = poly([(x0 - wdt / 2 - 8, 532), (x0 + wdt / 2 + 8, 532), (x0, 330)])
        cv.fill(roof, CRIM)
        cv.fill(roof * inner, CRIM_L)
        cv.hatch(roof, np.where(inner, 0.2, 0.65), 90 - side * 12, 2.4)
        cv.outline(roof, 2.0)
        cv.fill(seg(x0, 330, x0, 300, 2.2), INK)
        cv.fill(circle(x0, 298, 3.5), GOLD_L)
        cv.outline(circle(x0, 298, 3.5), 1.2)
        for wy in (580, 680):
            wm = U(box(x0, wy + 6, 14, 30), poly([(x0 - 7, wy - 9), (x0, wy - 22), (x0 + 7, wy - 9)]))
            cv.light(radial(x0, wy, 26), GOLD, 0.3)
            cv.fill(wm, GOLD_L)
            cv.glaze(wm * lin(0, wy - 22, 0, wy + 22), GOLD, 0.8)
            cv.outline(wm, 1.5)
        cv.outline(tw, 2.2)
    # the winding path from our feet to the horizon between the spires
    pts = []
    for i in range(60):
        t = i / 59
        y = 900 - (900 - 612) * (1 - (1 - t) ** 1.3)
        x = CX + 70 * math.sin(t * 5.2 + 0.4) * (1 - t) ** 1.2
        w = 4 + 150 * (1 - t) ** 1.8
        pts.append((x, y, w))
    left = [(x - w / 2, y) for x, y, w in pts]
    right = [(x + w / 2, y) for x, y, w in pts]
    path = poly(left + right[::-1])
    cv.fill(path, BONE)
    cv.glaze(path, GOLD_L, 0.55)
    cv.hatch(path, 0.12 + 0.25 * lin(0, 900, 0, 620), 0, 2.6, cross=False)
    for i in range(0, 50, 3):                                     # flagstones across the path
        x, y, w = pts[i]
        cv.fill(seg(x - w / 2, y, x + w / 2, y, max(0.7, 1.6 * (1 - i / 60))) * path, INK, 0.5)
    cv.outline(path, 1.6)
    # foreground: dark ground with the wolf on a rock (left) and the raven on a stone (right)
    ground = poly(spline([(30, 800), (110, 776), (200, 790), (250, 820), (240, 920, 1), (30, 920, 1)]))
    ground = U(ground, poly(spline([(570, 800), (490, 780), (400, 790), (350, 820), (360, 920, 1), (570, 920, 1)])))
    cv.fill(ground, INK * 1.6)
    cv.rim(ground, 0, -1, 1.6, NIGHT_L * 1.2, 0.8)
    wolf = wolf_mask(158, 790, 0.95)
    silhouette(cv, wolf, (0.75, -0.65), 2.0)
    cv.fill(ellipse(158 + 26 * 0.95, 790 - 174 * 0.95, 2.6, 1.5, -40), GOLD_L)
    rock = poly(spline([(400, 790), (412, 744), (446, 732), (478, 744), (488, 790)]))
    cv.fill(rock, PARCH * 0.8)
    cv.hatch(rock, np.where(X < 444, 0.25, 0.7), 60, 2.6)
    cv.glaze(rock, NIGHT_L, 0.5)
    cv.outline(rock, 1.8)
    rs = 1.1
    raven = U(blob(raven_pts(440, 740, rs), n=10), seg(438, 728, 436, 742, 2.6), seg(448, 728, 450, 742, 2.6))
    silhouette(cv, raven, (-0.8, -0.6), 1.8)
    wing = spline([(440 - 4 * rs, 740 - 96 * rs), (440 + 24 * rs, 740 - 70 * rs), (440 + 48 * rs, 740 - 44 * rs),
                   (440 + 64 * rs, 740 - 22 * rs)], closed=False, n=8)
    cv.fill(taper(wing, 1.6, 0.6), NIGHT_L * 1.2, 0.8)
    cv.fill(circle(440 - 18 * rs, 740 - 100 * rs, 2.2), GOLD_L)


# ================================================================ IX  The Seeker
def seeker_scene(cv):
    vpx, vpy, f, hc, wc, hceil = 330, 470, 500.0, 1.6, 1.5, 1.9
    lx, ly = 318, 540                                             # the lantern
    # base: everything painted lit, darkness laid over afterwards
    cv.fill(np.ones((WH, WW), f32), PARCH * 0.86)
    dy = np.maximum(Y - vpy, 0.5)
    Zf = f * hc / dy
    floor = (Y > vpy + 2).astype(f32)
    wall_line = vpy + (hc / wc) * np.abs(X - vpx)
    floor *= smooth(-1, 1, Y - wall_line)
    Xw = (X - vpx) * Zf / f
    u, v = Xw / 0.42, Zf / 0.42
    wu = np.abs(np.gradient(u, axis=1)) + 1e-4
    wv = np.abs(np.gradient(v, axis=0)) + 1e-4
    au = np.clip(np.abs(u - np.round(u)) / wu, 0, 1)
    av = np.clip(np.abs(v - np.round(v)) / wv, 0, 1)
    su = np.where(np.floor(u) % 2 == 0, 1.0, -1.0)
    sv = np.where(np.floor(v) % 2 == 0, 1.0, -1.0)
    chk = 0.5 + 0.5 * su * sv * au * av
    chk = 0.5 + (chk - 0.5) * smooth(30, 8, Zf) * smooth(0.9, 0.3, wv)
    floor_col = BONE[None, None, :] * chk[..., None] + (INK * 1.6)[None, None, :] * (1 - chk[..., None])
    cv.fill(floor, floor_col)
    # walls (left and right) and the vault, with transverse arches marching away
    walls = (1 - floor) * (Y > vpy - (hceil / wc) * np.abs(X - vpx))
    cv.fill(walls, PARCH * 0.72)
    cv.hatch(walls, 0.35, 90, 3.0, cross=False)
    vault = (1 - floor) * (1 - walls)
    cv.fill(vault, PARCH * 0.55)
    cv.hatch(vault, 0.5, 0, 3.0)
    # the far end: a wall with a moonlit lancet window
    Zend = 26.0
    ex0, ex1 = vpx - f * wc / Zend, vpx + f * wc / Zend
    ey0, ey1 = vpy - f * hceil / Zend, vpy + f * hc / Zend
    endw = box((ex0 + ex1) / 2, (ey0 + ey1) / 2, ex1 - ex0, ey1 - ey0)
    cv.fill(endw, PARCH * 0.6)
    lw = U(box(vpx, vpy - 4, 10, 22), poly([(vpx - 5, vpy - 15), (vpx, vpy - 26), (vpx + 5, vpy - 15)]))
    cv.fill(lw, NIGHT_L * 1.4)
    for Z in (22.0, 16.0, 11.5, 8.2, 5.9, 4.2, 3.0):
        xl, xr = vpx - f * wc / Z, vpx + f * wc / Z
        yt, yb = vpy - f * hceil / Z, vpy + f * hc / Z
        pw = f * 0.22 / Z
        apex = vpy - f * 3.1 / Z
        a = (xr - xl) / 2
        arch_o, arch_i = [], []
        for t in np.linspace(-1, 1, 61):
            R = 1.4
            ff = math.sqrt(max(0.0, R * R - (abs(t) + R - 1) ** 2)) / math.sqrt(R * R - (R - 1) ** 2)
            arch_o.append((vpx + t * (a + pw), yt - (yt - apex) * ff - pw * 0.4))
            arch_i.append((vpx + t * (a - pw * 0.2), yt - (yt - apex) * ff * 0.93 + pw * 0.6))
        band = poly(arch_o + arch_i[::-1])
        pil_l = box(xl, (yt + yb) / 2, pw * 2, yb - yt)
        pil_r = box(xr, (yt + yb) / 2, pw * 2, yb - yt)
        portal = U(band, pil_l, pil_r)
        cv.fill(portal, BONE)
        cv.hatch(portal, np.where(X < vpx, 0.15, 0.4), 90, max(1.4, 2.8 * 3 / Z), cross=False)
        cv.outline(portal, max(0.8, 2.2 * 3 / Z))
    # darkness, except in the lantern's pool of light
    Lpool = np.exp(-(((X - lx) / 170) ** 2 + ((Y - ly) / 200) ** 2))
    Lfloor = np.exp(-(((X - 370) / 150) ** 2 + ((Y - 790) / 70) ** 2)) * floor
    Lt = np.clip(Lpool + 0.9 * Lfloor, 0, 1)
    cv.glaze(np.ones((WH, WW), f32), INK * 1.5, 0.88 * (1 - Lt))
    cv.hatch(np.ones((WH, WW), f32), 0.45 * (1 - Lt), 30, 3.2)
    cv.glaze(np.ones((WH, WW), f32), (1.0, 0.82, 0.55), 0.55 * Lt)
    # the lost key on the floor, glinting
    kx, ky = 392, 800
    key = U(ring(kx - 16, ky, 7, 3.6), seg(kx - 9, ky, kx + 16, ky, 3.6), box(kx + 12, ky + 5, 3.2, 7),
            box(kx + 6, ky + 4, 3.0, 5))
    cv.shadow(key, 1.5, 2, 1.5, 0.5)
    cv.fill(key, GOLD)
    cv.rim(key, -0.5, -0.8, 1.0, GOLD_L, 1.0)
    cv.outline(key, 1.0, INK, 0.8)
    cv.light(radial(kx - 14, ky - 4, 30), GOLD_L, 0.6)
    cv.fill(star4(kx - 14, ky - 5, 14, 0.14), WHITE)
    # the hooded seeker (crimson robe, the face lost in the hood), lantern raised into the dark
    fig, face_hole = seeker_robe()
    cv.shadow(fig, -6, 4, 6, 0.6)
    cv.fill(fig, CRIM * 0.95)
    lam = pillow(fig, 22, light=(lx - 200, ly - 640), z=0.35)
    cv.light(fig * lam ** 1.6, CRIM_L * 1.35, 0.9)
    cv.hatch(fig, 0.6 * (1 - lam) + 0.08, 92, 2.6)
    for (x0, y0, x1, y1) in ((206, 610, 226, 880), (180, 600, 170, 880), (232, 640, 250, 870), (156, 650, 146, 860)):
        cv.fill(taper(spline([(x0, y0), ((x0 + x1) / 2 + 4, (y0 + y1) / 2), (x1, y1)], closed=False, n=10), 1.0, 2.2),
                INK, 0.8)
    cv.fill(M(np.abs(sdf(face_hole)) - 2.4), GOLD_L, 0.85)
    cv.fill(face_hole, INK)
    cv.rim(fig, 0.9, -0.4, 2.2, GOLD_L, 0.95)
    cv.outline(fig, 2.0)
    cv.fill(ellipse(302, 530, 6, 7), PARCH * 0.75)                # the hand
    cv.outline(ellipse(302, 530, 6, 7), 1.2)
    # the lantern
    cv.light(radial(lx, ly + 8, 260) ** 2, GOLD, 0.5)
    cv.light(radial(lx, ly + 8, 70) ** 1.5, GOLD_L, 0.9)
    cv.fill(ring(lx, ly - 22, 6, 2.2), INK)
    cv.fill(seg(300, 528, lx, ly - 26, 2.0), INK)
    roofm = poly([(lx - 15, ly - 4), (lx + 15, ly - 4), (lx + 4, ly - 16), (lx, ly - 20), (lx - 4, ly - 16)])
    glass = box(lx, ly + 14, 24, 32, 2)
    basem = box(lx, ly + 33, 30, 7, 2)
    cv.fill(glass, GOLD_L)
    cv.fill(ellipse(lx, ly + 16, 6, 11), WHITE, 0.9)
    flame(cv, lx, ly + 24, 12, 0.3)
    cv.fill(glass * U(box(lx - 6, ly + 14, 2.0, 32), box(lx + 6, ly + 14, 2.0, 32)), INK, 0.9)
    cv.outline(glass, 2.0)
    for pm in (roofm, basem):
        cv.fill(pm, GOLD)
        cv.hatch(pm, 0.4, 90, 2.0, cross=False)
        cv.outline(pm, 1.6)


# ================================================================ III  The Feast
def feast_scene(cv):
    vpx, vpy = 300, 420
    # the hall: a dark wall, a tall moonlit window behind the table
    cv.fill(np.ones((WH, WW), f32), CRIM * 0.55)
    cv.hatch(np.ones((WH, WW), f32), 0.55, 90, 3.2)
    win = U(box(300, 400, 150, 260), poly([(225, 272), (300, 170), (375, 272)]))
    win = U(box(300, 410, 150, 260), poly(spline([(225, 282, 1), (238, 220), (300, 164, 1), (362, 220), (375, 282, 1)],
                                                 closed=False, n=10) + [(375, 540), (225, 540)]))
    cv.fill(win, NIGHT * 1.1)
    cv.light(win * lin(0, 540, 0, 170), NIGHT_L, 0.6)
    cv.hatch(win, 0.3, 0, 3.0, cross=False)
    cv.light(radial(326, 246, 70) ** 2 * win, GOLD_L, 0.5)
    cres = sub(circle(326, 246, 26), circle(314, 238, 23))
    cv.fill(cres, BONE)
    cv.glaze(cres, GOLD_L, 0.6)
    cv.outline(cres, 1.4)
    for (sx_, sy_, sr_) in ((262, 230, 4), (352, 300, 3), (250, 300, 3)):
        cv.fill(star4(sx_, sy_, sr_ * 1.6, 0.2), BONE)
    mull = U(box(300, 430, 5, 230), box(300, 330, 150, 5), box(300, 450, 150, 5))
    cv.fill(mull * win, INK * 1.5)
    cv.outline(win, 3.0)
    frame_ = M(np.abs(sdf(win)) - 7) * (1 - win)
    cv.fill(frame_, PARCH * 0.8)
    cv.hatch(frame_, 0.4, 90, 2.4)
    cv.outline(frame_, 1.4)
    # the long table, in perspective
    near_y, far_y = 760, 540
    nl, nr_ = 56, 544
    t_far = (far_y - vpy) / (near_y - vpy)
    fl, fr = vpx + (nl - vpx) * t_far, vpx + (nr_ - vpx) * t_far
    top = poly([(fl, far_y), (fr, far_y), (nr_, near_y), (nl, near_y)])
    cv.fill(top, BONE)
    cv.hatch(top, 0.1 + 0.3 * lin(0, near_y, 0, far_y), 0, 2.6, cross=False)
    run_n, run_f = 70, 70 * t_far
    runner = poly([(vpx - run_f, far_y), (vpx + run_f, far_y), (vpx + run_n, near_y), (vpx - run_n, near_y)])
    cv.fill(runner, CRIM)
    cv.hatch(runner, 0.3, 0, 2.6, cross=False)
    cv.fill(M(np.abs(sdf(runner)) - 1.6) * top, GOLD, 0.9)
    cv.outline(top, 1.8)
    cloth = poly([(nl - 4, near_y)] + [(x, 900 + 6 * math.sin((x - nl) / 30 * math.pi)) for x in np.linspace(nl, nr_, 40)]
                 + [(nr_ + 4, near_y)])
    cv.fill(cloth, BONE * 0.95)
    folds = np.abs(np.sin((X - nl) / 30 * math.pi))
    cv.hatch(cloth, 0.55 * (1 - folds) + 0.08, 90, 2.4)
    cv.fill(box(300, near_y + 14, nr_ - nl, 3) * cloth, CRIM, 0.9)
    cv.outline(cloth, 1.8)
    rf = poly([(vpx - run_n, near_y), (vpx + run_n, near_y), (vpx + run_n, 860), (vpx, 884, 1), (vpx - run_n, 860)])
    cv.fill(rf, CRIM)
    cv.hatch(rf, 0.35 + 0.3 * folds, 90, 2.4)
    cv.fill(M(np.abs(sdf(rf)) - 1.4) * rf, GOLD)
    cv.outline(rf, 1.6)
    # candles and place-settings receding along both sides
    for side in (-1, 1):
        for t in (0.93, 0.62, 0.38, 0.18):
            s = (far_y - vpy + (near_y - far_y) * (1 - t)) / (near_y - vpy)     # scale at this depth
            y = far_y + (near_y - far_y) * (1 - t)
            xedge = vpx + side * ((nr_ - vpx) * s)
            x = vpx + side * (nr_ - vpx - 40) * s
            px_ = vpx + side * (nr_ - vpx - 108) * s
            plate = ellipse(px_, y - 6 * s, 24 * s, 7 * s)
            cv.fill(plate, PARCH * 0.9)
            cv.fill(ring(px_, y - 6 * s, 15 * s, 1.2) * 0 + ellipse(px_, y - 6 * s, 15 * s, 4.4 * s) * 0.25, INK, 0.5)
            cv.outline(plate, max(0.8, 1.6 * s))
            candle(cv, x, y - 2 * s, 70 * s, 9 * s, glow=0.45)
    # the cloche on its platter, steaming
    pcx, pcy = 300, 708
    platter = ellipse(pcx, pcy, 130, 26)
    cv.shadow(platter, 0, 6, 6, 0.5)
    cv.fill(platter, GOLD)
    cv.hatch(platter, 0.3 + 0.4 * lin(pcx - 130, 0, pcx + 130, 0), 90, 2.4, cross=False)
    cv.fill(ellipse(pcx, pcy - 3, 116, 19), GOLD_L, 0.6)
    cv.outline(platter, 2.0)
    dome_ = poly([(pcx - 112, pcy - 2)] + [(pcx + 112 * math.cos(a), pcy - 2 - 118 * math.sin(a))
                                          for a in np.linspace(math.pi, 0, 60)] + [(pcx + 112, pcy - 2)])
    lam = pillow(dome_, 30, light=(-0.6, -0.8), z=0.5)
    cv.fill(dome_, GOLD)
    cv.light(dome_ * lam ** 3, GOLD_L, 0.9)
    cv.hatch(dome_, 0.6 * (1 - lam) ** 1.3, 90, 2.4, phase=(X - pcx) / 2.4 + 0 * Y)
    hl = taper(spline([(pcx - 70, pcy - 40), (pcx - 60, pcy - 84), (pcx - 30, pcy - 108)], closed=False, n=8), 7, 3)
    cv.fill(hl, WHITE, 0.85)
    cv.fill(box(pcx, pcy - 8, 226, 8, 3), GOLD * 0.8)
    cv.outline(box(pcx, pcy - 8, 226, 8, 3), 1.4)
    cv.outline(dome_, 2.2)
    knob = U(circle(pcx, pcy - 132, 11), box(pcx, pcy - 121, 10, 8))
    cv.fill(knob, GOLD)
    cv.rim(knob, -0.6, -0.8, 1.4, GOLD_L, 1)
    cv.outline(knob, 1.6)
    # steam curling up from under the rim and from the knob
    for (x0, y0, amp, ph, ln, w) in ((pcx - 104, pcy - 14, 14, 0.0, 150, 7), (pcx + 106, pcy - 16, 12, 2.0, 140, 6),
                                     (pcx - 4, pcy - 146, 16, 1.0, 190, 8), (pcx + 22, pcy - 140, 10, 3.0, 120, 5)):
        pts = [(x0 + amp * math.sin(t * 4.5 + ph) * t, y0 - ln * t) for t in np.linspace(0, 1, 30)]
        sm = taper(pts, w * 1.6, 2.5)
        cv.light(ndimage.gaussian_filter(sm, 4 * K), BONE, 0.6)
        cv.fill(sm, BONE, 0.9)
        cv.fill(M(np.abs(sdf(sm)) - 0.5), INK, 0.35)
    # garlic bulbs at the front left
    for (gx, gy, gs, rot) in ((128, 742, 1.0, -8), (170, 750, 0.8, 12), (96, 756, 0.7, -25)):
        bulb = blob([(gx, gy - 40 * gs, 1), (gx + 12 * gs, gy - 22 * gs), (gx + 24 * gs, gy - 6 * gs),
                     (gx + 18 * gs, gy + 8 * gs), (gx, gy + 12 * gs), (gx - 18 * gs, gy + 8 * gs), (gx - 24 * gs, gy - 6 * gs),
                     (gx - 12 * gs, gy - 22 * gs)], n=10)
        cv.shadow(bulb, 3, 3, 2.5, 0.45)
        cv.fill(bulb, BONE)
        lamg = pillow(bulb, 8, (-0.6, -0.7))
        cv.hatch(bulb, 0.5 * (1 - lamg), 90, 2.0, cross=False)
        for k in (-0.55, 0.0, 0.55):
            pts = spline([(gx + k * 4 * gs, gy - 34 * gs), (gx + k * 22 * gs, gy - 8 * gs), (gx + k * 14 * gs, gy + 10 * gs)],
                         closed=False, n=8)
            cv.fill(stroke(pts, 1.2) * bulb, INK, 0.75)
        cv.glaze(bulb * smooth(gy - 30 * gs, gy + 10 * gs, Y) * lin(gx - 20, 0, gx + 20, 0), CRIM_L, 0.25)
        cv.outline(bulb, 1.6)
        for k in (-1, 0, 1):
            cv.fill(seg(gx + k * 3, gy + 11 * gs, gx + k * 6, gy + 16 * gs, 1.0), INK, 0.7)
    # a brass goblet at the front right
    gx, gy = 462, 752
    cup = poly(spline([(gx - 26, gy - 92, 1), (gx + 26, gy - 92, 1), (gx + 22, gy - 62), (gx + 8, gy - 46),
                       (gx - 8, gy - 46), (gx - 22, gy - 62)], n=10))
    stem = U(box(gx, gy - 28, 7, 40), ellipse(gx, gy - 30, 8, 5), ellipse(gx, gy - 4, 24, 6))
    gob = U(cup, stem)
    cv.shadow(gob, 4, 3, 3, 0.45)
    cv.fill(gob, GOLD)
    lamc = pillow(gob, 10, (-0.6, -0.6))
    cv.light(gob * lamc ** 3, GOLD_L, 0.8)
    cv.hatch(gob, 0.6 * (1 - lamc), 90, 2.2, cross=False)
    cv.fill(ellipse(gx, gy - 92, 26, 6), INK * 1.6)
    cv.fill(M(np.abs(np.hypot((X - gx) / 26, (Y - gy + 92) / 6) - 1) * 6 - 0.8), GOLD_L)
    cv.fill(seg(gx - 14, gy - 84, gx - 10, gy - 60, 3.0, 1.5), WHITE, 0.8)
    cv.outline(gob, 1.8)


# ================================================================ IV  The Crown
def crown_scene(cv):
    ccx, ccy = 300, 470
    cv.fill(np.ones((WH, WW), f32), INK * 1.8)
    cv.glaze(np.ones((WH, WW), f32), NIGHT_L, 0.6)
    # the rays: alternating gold wedges
    th = np.arctan2(Y - ccy, X - ccx)
    d = np.hypot(X - ccx, Y - ccy)
    nr = 40
    ph = (th / (2 * math.pi) * nr) % 1.0
    idx = np.floor(th / (2 * math.pi) * nr + nr) % 2
    wedge = M((np.abs(ph - 0.5) - np.where(idx == 0, 0.30, 0.16)) * d * 2 * math.pi / nr) * (d > 40)
    fade = smooth(470, 150, d)
    cv.fill(wedge * fade, GOLD, 0.9)
    cv.light(wedge * radial(ccx, ccy, 380), GOLD_L, 0.6)
    cv.hatch(wedge * fade, 0.3, 0, 2.6, cross=False)
    cv.hatch(np.ones((WH, WW), f32) * (1 - wedge), 0.35, 0, 3.0, cross=False)
    cv.light(radial(ccx, ccy - 20, 230) ** 2, GOLD_L, 0.55)
    # the laurel wreath
    R = 196
    for side in (-1, 1):
        a_s = np.linspace(math.radians(100), math.radians(250), 15)
        stem_pts = [(ccx + side * R * math.cos(math.pi - a) * -1, ccy + R * math.sin(a) * -1) for a in a_s]
        stem_pts = [(ccx - side * R * math.sin(t), ccy + R * math.cos(t)) for t in np.linspace(0.25, 2.75, 24)]
        cv.fill(taper(stem_pts, 5, 2.5), GOLD * 0.7)
        cv.outline(taper(stem_pts, 5, 2.5), 1.2)
        for i, t in enumerate(np.linspace(0.32, 2.72, 13)):
            px_, py_ = ccx - side * R * math.sin(t), ccy + R * math.cos(t)
            tx, ty = -side * math.cos(t), -math.sin(t)                     # tangent (toward the top)
            for o in (-1, 1):
                nx_, ny_ = -ty * o, tx * o
                lx_, ly_ = px_ + nx_ * 13 + tx * 12, py_ + ny_ * 13 + ty * 12
                ang = math.degrees(math.atan2(ny_ * 0.6 + ty, nx_ * 0.6 + tx))
                lf = ellipse(lx_, ly_, 18 * (1 - 0.25 * t / 3), 7.5 * (1 - 0.25 * t / 3), ang)
                cv.fill(lf, GOLD)
                cv.light(lf * lin(lx_ + 10, ly_ - 10, lx_ - 10, ly_ + 10), GOLD_L, 0.6)
                cv.hatch(lf, 0.35, ang + 30, 2.0, cross=False)
                cv.fill(seg(lx_ - 14 * math.cos(math.radians(ang)), ly_ - 14 * math.sin(math.radians(ang)),
                            lx_ + 14 * math.cos(math.radians(ang)), ly_ + 14 * math.sin(math.radians(ang)), 1.0) * lf,
                        INK, 0.7)
                cv.outline(lf, 1.4)
    # the cushion: crimson velvet, gold piping, tassels
    qx, qy = 300, 654
    cush = blob([(170, 616), (300, 600), (430, 616), (462, 650), (430, 704), (300, 716), (170, 704), (138, 650)], n=12)
    cv.shadow(cush, 0, 8, 8, 0.6)
    cv.fill(cush, CRIM)
    lamq = pillow(cush, 28, (-0.4, -0.9), z=0.5)
    cv.light(cush * lamq ** 2.5, CRIM_L * 1.3, 0.8)
    cv.hatch(cush, 0.65 * (1 - lamq), 0, 2.4)
    pip = M(np.abs(sdf(cush) + 3) - 1.6)
    cv.fill(pip, GOLD)
    cv.outline(cush, 2.0)
    for (tx_, ty_) in ((148, 652), (452, 652)):
        cv.fill(circle(tx_, ty_, 7), GOLD)
        tas = poly([(tx_ - 5, ty_ + 4), (tx_ + 5, ty_ + 4), (tx_ + 10, ty_ + 44), (tx_ - 10, ty_ + 44)])
        cv.fill(tas, GOLD)
        cv.hatch(tas, 0.55, 90, 1.8, cross=False)
        cv.outline(U(tas, circle(tx_, ty_, 7)), 1.4)
    # the prize rosette pinned to the cushion's front, tails hanging
    rx, ry = 300, 712
    for side in (-1, 1):
        tail = poly([(rx + side * 4, ry), (rx + side * 30, ry + 4), (rx + side * 44, ry + 132), (rx + side * 30, ry + 118, 1),
                     (rx + side * 20, ry + 136, 1)])
        cv.fill(tail, NIGHT)
        cv.light(tail * lin(rx + side * 44, 0, rx, 0), NIGHT_L, 0.6)
        cv.hatch(tail, 0.4, 90 - side * 8, 2.2, cross=False)
        cv.fill(M(np.abs(sdf(tail) + 2.6) - 0.9) * tail, GOLD)
        cv.outline(tail, 1.6)
    thr = np.arctan2(Y - ry, X - rx)
    rr_ = np.hypot(X - rx, Y - ry)
    ros = M(rr_ - 34 - 3.0 * np.cos(18 * thr))
    cv.shadow(ros, 2, 3, 2.5, 0.5)
    cv.fill(ros, NIGHT)
    cv.light(ros * (0.5 + 0.5 * np.cos(18 * thr)) * lin(rx + 30, ry + 30, rx - 30, ry - 30), NIGHT_L * 1.3, 0.8)
    cv.fill(M(np.abs(rr_ - 30) - 0.7) * ros, INK, 0.6)
    cv.outline(ros, 1.6)
    med = circle(rx, ry, 18)
    cv.fill(med, GOLD)
    cv.light(med * lin(rx + 14, ry + 14, rx - 14, ry - 14), GOLD_L, 0.8)
    cv.fill(ring(rx, ry, 13, 1.2), INK, 0.7)
    cv.fill(star4(rx, ry, 9, 0.3), GOLD_L)
    cv.outline(star4(rx, ry, 9, 0.3), 0.9, INK, 0.6)
    cv.outline(med, 1.6)
    # the thorned iron crown
    bx0, bx1, by_ = 196, 404, 604
    band = poly([(bx0, by_ - 50)] + [(x, by_ - 50 + 10 * (1 - ((x - 300) / 104) ** 2)) for x in np.linspace(bx0, bx1, 30)]
                + [(bx1, by_ - 50), (bx1 - 4, by_)] + [(x, by_ + 12 * (1 - ((x - 300) / 100) ** 2))
                                                        for x in np.linspace(bx1 - 4, bx0 + 4, 30)] + [(bx0 + 4, by_)])
    tines = []
    for i, x in enumerate(np.linspace(bx0 + 10, bx1 - 10, 7)):
        k = 1 - abs(i - 3) / 3
        h = 74 + 70 * k
        base_y = by_ - 46 + 10 * (1 - ((x - 300) / 104) ** 2)
        w = 13 + 5 * k
        tines.append(poly([(x - w, base_y + 4), (x - w * 0.35, base_y - h * 0.55), (x, base_y - h, 1),
                           (x + w * 0.35, base_y - h * 0.55), (x + w, base_y + 4)]))
        for j, (fy, sgn) in enumerate(((0.30, -1), (0.52, 1), (0.72, -1))):
            yb = base_y - h * fy
            xb = x + sgn * w * (0.6 - 0.45 * fy)
            tines.append(poly([(xb, yb + 4), (xb + sgn * 11, yb - 7), (xb, yb - 3)]))
    crown = U(band, *tines)
    cv.shadow(crown, 3, 5, 4, 0.6)
    lamc = pillow(crown, 6, (-0.6, -0.7))
    iron = PARCH * 0.42
    cv.fill(crown, iron)
    cv.light(crown * lamc ** 4, BONE, 0.85)
    cv.hatch(crown, 0.6 * (1 - lamc) + 0.1, 90, 2.2)
    cv.glaze(crown, NIGHT_L, 0.25)
    cv.outline(crown, 2.0)
    # a thorned vine twisting round the band, gems on the band
    vine = [(x, by_ - 22 + 12 * math.sin((x - bx0) / 208 * math.pi * 4)) for x in np.linspace(bx0 + 6, bx1 - 6, 60)]
    vm = taper(vine, 4, 4)
    cv.fill(vm, INK * 1.3)
    cv.rim(vm, -0.5, -0.8, 1.0, BONE, 0.8)
    for x in np.linspace(bx0 + 20, bx1 - 20, 9):
        y = by_ - 22 + 12 * math.sin((x - bx0) / 208 * math.pi * 4)
        sgn = 1 if int((x - bx0) / 23) % 2 else -1
        cv.fill(poly([(x - 3, y), (x + 3, y), (x + 1, y + sgn * 10)]), INK * 1.3)
    gem = U(ellipse(300, by_ - 22, 13, 16))
    cv.fill(gem, CRIM)
    cv.light(gem * radial(296, by_ - 28, 12), CRIM_L * 1.5, 1.0)
    cv.fill(circle(295, by_ - 29, 3), WHITE, 0.9)
    cv.outline(gem, 1.6)
    for x in (236, 364):
        sm_ = circle(x, by_ - 22 + 6, 6)
        cv.fill(sm_, GOLD)
        cv.rim(sm_, -0.6, -0.8, 1.2, GOLD_L, 1)
        cv.outline(sm_, 1.2)


# ================================================================ V  The Scholar
def scholar_scene(cv):
    # a dark study: panelled wall, an arched window with the moon, shelves
    cv.fill(np.ones((WH, WW), f32), PARCH * 0.5)
    cv.glaze(np.ones((WH, WW), f32), NIGHT_L, 0.55)
    cv.hatch(np.ones((WH, WW), f32), 0.5, 90, 3.2)
    win = U(box(300, 330, 170, 200), poly(spline([(215, 232, 1), (226, 180), (300, 124, 1), (374, 180), (385, 232, 1)],
                                                  closed=False, n=10)))
    cv.fill(M(np.abs(sdf(win)) - 8) * (1 - win), PARCH * 0.62)
    cv.hatch(M(np.abs(sdf(win)) - 8) * (1 - win), 0.45, 90, 2.4)
    cv.fill(win, NIGHT * 1.05)
    cv.light(win * lin(0, 430, 0, 130), NIGHT_L, 0.5)
    cv.hatch(win, 0.3, 0, 3.0, cross=False)
    engraved_moon(cv, 300, 250, 52, halo=0.35, craters=((-0.4, 0.2, 0.16), (0.3, -0.35, 0.12), (0.2, 0.4, 0.1)))
    cv.fill(U(box(300, 330, 4, 200), box(300, 330, 170, 4)) * win * (1 - circle(300, 250, 54)), INK * 1.5)
    cv.outline(win, 2.4)
    cv.outline(M(np.abs(sdf(win)) - 8) * (1 - win) + win, 1.4)
    for x in (120, 480):
        sh = box(x, 600, 120, 500)
        cv.fill(sh, PARCH * 0.35)
        for y in range(400, 800, 70):
            cv.fill(box(x, y, 130, 6), PARCH * 0.55)
            cv.outline(box(x, y, 130, 6), 1.0)
            rng = np.random.default_rng(int(x + y))
            xx_ = x - 58
            while xx_ < x + 52:
                w = rng.uniform(7, 13)
                h = rng.uniform(40, 60)
                bk = box(xx_ + w / 2, y - 3 - h / 2, w - 1, h)
                cv.fill(bk, [CRIM, NIGHT, PARCH * 0.6, GOLD * 0.6][int(rng.integers(0, 4))])
                cv.hatch(bk, 0.5, 90, 2.0, cross=False)
                cv.outline(bk, 0.8)
                xx_ += w
        cv.glaze(sh, INK, 0.45)
    # the desk
    desk = box(300, 860, 560, 200)
    cv.fill(desk, PARCH * 0.55)
    cv.glaze(desk, CRIM * 1.6, 0.6)
    cv.hatch(desk, 0.4 + 0.2 * lin(0, 760, 0, 900), 2, 2.6)
    cv.fill(box(300, 762, 560, 4), GOLD * 0.8, 0.8)
    cv.outline(desk, 1.6)
    # a candle on the left lights the scene warm
    cv.light(radial(108, 560, 360) ** 2, GOLD, 0.55)
    candle(cv, 108, 762, 160, 22, glow=0.8)
    # the stack of books, spines toward us
    books = [(150, 450, 706, 760, CRIM), (170, 436, 660, 706, NIGHT), (160, 424, 622, 660, PARCH * 0.85),
             (186, 410, 588, 622, CRIM * 0.8)]
    for (x0, x1, y0, y1, col) in books:
        bm = box((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, 5)
        cv.shadow(bm, 0, 3, 2, 0.5)
        cv.fill(bm, col)
        lamb = pillow(bm, 10, (-0.5, -0.8))
        cv.light(bm * lamb ** 3, BONE, 0.35)
        cv.hatch(bm, 0.5 * (1 - lamb) + 0.1 * smooth(y0, y1, Y), 0, 2.2, cross=False)
        for gx_ in (x0 + 22, x0 + 30, x1 - 30, x1 - 22):
            cv.fill(box(gx_, (y0 + y1) / 2, 2.6, y1 - y0 - 6), GOLD)
        lab = box((x0 + x1) / 2, (y0 + y1) / 2, 74, (y1 - y0) * 0.5, 2)
        cv.fill(lab, GOLD * 0.9 if col is not CRIM else BONE * 0.9)
        cv.fill(box((x0 + x1) / 2, (y0 + y1) / 2, 50, 1.6) * lab, INK, 0.7)
        cv.outline(lab, 1.0)
        cv.outline(bm, 1.6)
    # the inkwell and quill, right
    ix, iy = 486, 760
    pot = poly(spline([(ix - 30, iy, 1), (ix + 30, iy, 1), (ix + 32, iy - 22), (ix + 18, iy - 40), (ix - 18, iy - 40),
                       (ix - 32, iy - 22)], n=10))
    neck = box(ix, iy - 46, 22, 14, 2)
    well = U(pot, neck)
    cv.shadow(well, 4, 3, 3, 0.5)
    cv.fill(well, INK * 2.2)
    cv.glaze(well, NIGHT_L, 0.6)
    lamw = pillow(well, 10, (-0.6, -0.6))
    cv.light(well * lamw ** 4, NIGHT_L * 1.5, 0.9)
    cv.fill(seg(ix - 18, iy - 30, ix - 22, iy - 12, 3, 2), WHITE, 0.7)
    cv.fill(box(ix, iy - 52, 26, 4, 2), GOLD)
    cv.outline(well, 1.8)
    q = spline([(ix + 2, iy - 50), (ix + 14, iy - 120), (ix + 34, iy - 200), (ix + 60, iy - 268)], closed=False, n=12)
    vane = []
    for i, (x, y) in enumerate(q):
        t = i / (len(q) - 1)
        w = 18 * math.sin(math.pi * min(1, t * 1.2) ** 0.8) * (t > 0.25)
        vane.append((x, y, w))
    lvane = poly([(x - w, y + w * 0.3) for x, y, w in vane] + [(x + w * 0.6, y - w * 0.2) for x, y, w in vane][::-1])
    cv.fill(lvane, BONE)
    cv.hatch(lvane, 0.35, -60, 2.0, cross=False)
    for i in range(6, len(vane) - 1, 3):
        x, y, w = vane[i]
        cv.fill(seg(x, y, x - w * 0.9, y + w * 0.6, 1.0), INK, 0.7)
    cv.outline(lvane, 1.4)
    cv.fill(taper(q, 2.6, 1.0), INK)
    # the report card, sealed, lying in front
    rx, ry, rr = 262, 822, -4
    card = box(rx, ry, 220, 82, 2, rr)
    cv.shadow(card, 3, 4, 3, 0.55)
    cv.fill(card, BONE)
    cv.hatch(card, 0.1, rr, 2.2, cross=False)

    def W(u, v):
        th = math.radians(rr)
        return (rx + u * math.cos(th) - v * math.sin(th), ry + u * math.sin(th) + v * math.cos(th))
    cv.fill(box(*W(-40, -26), 120, 3, 1, rr), INK, 0.85)
    for v in (-12, 0, 12, 24):
        cv.fill(box(*W(-42, v), 116, 1.4, 0.7, rr), INK, 0.55)
        cv.fill(box(*W(34, v), 14, 1.4, 0.7, rr), INK, 0.55)
    gm = text_mask("A", 30, *W(52, -10), FONT_TITLE)
    cv.fill(gm, CRIM)
    cv.outline(card, 1.6)
    sx_, sy_ = W(84, 16)
    for side in (-1, 1):
        rib = poly([(sx_ - 4, sy_), (sx_ + 4, sy_), (sx_ + side * 14 + 4, sy_ + 38), (sx_ + side * 14, sy_ + 32),
                    (sx_ + side * 14 - 4, sy_ + 38)])
        cv.fill(rib, CRIM_L)
        cv.outline(rib, 1.2)
    th_ = np.arctan2(Y - sy_, X - sx_)
    seal = M(np.hypot(X - sx_, Y - sy_) - 17 - 1.6 * np.cos(11 * th_))
    cv.shadow(seal, 1.5, 2, 1.5, 0.5)
    cv.fill(seal, CRIM)
    lams = pillow(seal, 5, (-0.6, -0.7))
    cv.light(seal * lams ** 3, CRIM_L * 1.4, 0.9)
    cv.fill(ring(sx_, sy_, 10, 1.4), INK, 0.55)
    cv.fill(sub(circle(sx_ - 1, sy_, 6.5), circle(sx_ + 2.5, sy_ - 2, 5.5)), GOLD_L, 0.9)
    cv.outline(seal, 1.4)
    # the owl perched on top of the stack
    ox, oy = 300, 588
    body_ = blob([(ox, oy - 158), (ox + 34, oy - 156), (ox + 54, oy - 176, 1), (ox + 56, oy - 140), (ox + 62, oy - 96),
                  (ox + 60, oy - 40), (ox + 40, oy - 4), (ox, oy + 2), (ox - 40, oy - 4), (ox - 60, oy - 40),
                  (ox - 62, oy - 96), (ox - 56, oy - 140), (ox - 54, oy - 176, 1), (ox - 34, oy - 156)], n=12)
    cv.shadow(body_, 4, 4, 4, 0.55)
    cv.fill(body_, PARCH * 0.80)
    cv.glaze(body_, GOLD, 0.55)
    lamo = pillow(body_, 26, (-0.5, -0.8))
    cv.light(body_ * lamo ** 3, BONE, 0.5)
    cv.hatch(body_, 0.55 * (1 - lamo) + 0.05, 90, 2.4)
    # chest feathers: rows of little chevrons
    for row, y in enumerate(range(oy - 82, oy - 10, 11)):
        for x in np.arange(ox - 30 + (row % 2) * 7, ox + 31, 14):
            if (x - ox) ** 2 / 34 ** 2 + (y - (oy - 46)) ** 2 / 46 ** 2 < 1:
                cv.fill(stroke([(x - 4.5, y - 3), (x, y + 2), (x + 4.5, y - 3)], 1.3), INK, 0.8)
    # wings folded at the sides
    for side in (-1, 1):
        wing = blob([(ox + side * 42, oy - 120), (ox + side * 62, oy - 96), (ox + side * 64, oy - 40),
                     (ox + side * 46, oy + 4, 1), (ox + side * 36, oy - 40), (ox + side * 36, oy - 96)], n=10)
        cv.fill(wing, PARCH * 0.62)
        cv.glaze(wing, GOLD, 0.6)
        cv.hatch(wing, 0.55, 90 + side * 10, 2.2)
        for k, y in enumerate(range(oy - 90, oy - 10, 16)):
            cv.fill(stroke(spline([(ox + side * 38, y), (ox + side * 50, y + 8), (ox + side * 60, y + 4)], closed=False,
                                  n=6), 1.3) * wing, INK, 0.8)
        cv.outline(wing, 1.6)
    # the face: two pale discs, gold eyes, a hooked beak, a dark brow
    for side in (-1, 1):
        dx_ = ox + side * 24
        disc = circle(dx_, oy - 118, 27)
        cv.fill(disc, BONE)
        th2 = np.arctan2(Y - (oy - 118), X - dx_)
        cv.hatch(disc, 0.25 * smooth(12, 27, np.hypot(X - dx_, Y - (oy - 118))), 0, 2.0, cross=False,
                 phase=th2 / (2 * math.pi) * 40)
        cv.outline(disc, 1.4, INK, 0.7)
    for side in (-1, 1):
        dx_ = ox + side * 24
        eye = circle(dx_, oy - 120, 14.5)
        cv.fill(eye, GOLD)
        cv.light(eye * lin(dx_, oy - 108, dx_, oy - 132), GOLD_L, 0.8)
        cv.fill(circle(dx_ + side * 1, oy - 120, 7.5), INK)
        cv.fill(circle(dx_ - 3, oy - 124, 2.6), WHITE)
        cv.outline(eye, 1.8)
    brow = stroke([(ox - 50, oy - 146), (ox - 24, oy - 140), (ox, oy - 128), (ox + 24, oy - 140), (ox + 50, oy - 146)], 4)
    cv.fill(brow, INK * 1.5)
    beak = poly(spline([(ox - 7, oy - 112), (ox + 7, oy - 112), (ox + 3, oy - 94), (ox, oy - 88, 1), (ox - 3, oy - 94)],
                       n=8))
    cv.fill(beak, GOLD * 0.85)
    cv.outline(beak, 1.3)
    cv.outline(body_, 2.0)
    # talons gripping the top book
    for side in (-1, 1):
        for k in (-1, 0, 1):
            x = ox + side * 18 + k * 6
            cv.fill(seg(x, oy - 4, x + k * 2, oy + 6, 3.2, 1.6), GOLD * 0.8)
            cv.outline(seg(x, oy - 4, x + k * 2, oy + 6, 3.2, 1.6), 0.9)


# ================================================================ the back
def card_back():
    cv = Canvas(CRIM, 3)
    parchment(cv, 1.2)
    sd = card_sd()
    field = M(sd + 22)
    # crimson field with an ink ogee lattice and gold studs
    cx, cy = 300, 512
    u = (X - cx) / 50.0
    v = (Y - cy) / 70.0
    a = np.abs(((u + v) % 2.0) - 1.0)
    b = np.abs(((u - v) % 2.0) - 1.0)
    curve = 0.12 * np.sin((u + v) * math.pi) + 0.12 * np.sin((u - v) * math.pi)
    lat = M((np.minimum(np.abs(a - 0.5 + curve), np.abs(b - 0.5 - curve)) * 50 - 1.6))
    cv.hatch(field, 0.30, 45, 3.0, cross=False)
    cv.hatch(field, 0.30, -45, 3.0, cross=False)
    cv.fill(ndimage.maximum_filter(lat, 3) * field, INK, 0.9)
    cv.fill(lat * field, GOLD * 0.7, 0.75)
    nodes_u = np.round(u)
    nodes_v = np.round(v)
    on = ((nodes_u + nodes_v) % 2 == 0)
    dn = np.hypot((u - nodes_u) * 50, (v - nodes_v) * 70)
    stud = M(dn - 4.2) * on * field
    cv.fill(stud, GOLD)
    cv.fill(M(np.abs(dn - 4.2) - 0.6) * on * field, INK)
    cu = np.round(u - 0.5) + 0.5
    cvv = np.round(v - 0.5) + 0.5
    dq = np.hypot((u - cu) * 50, (v - cvv) * 70)
    cell_star = M(np.minimum(np.abs(u - cu) * 50 / 2.0 + np.abs(v - cvv) * 70, np.abs(v - cvv) * 70 / 2.0
                             + np.abs(u - cu) * 50) - 9) * field
    cv.fill(cell_star, CRIM_L, 0.85)
    cv.outline(cell_star, 1.0, INK, 0.8)
    # vignette into ink at the edges
    cv.glaze(field * smooth(0, -140, sd), INK, 0.0)
    cv.glaze(field * smooth(-120, -10, sd), INK, 0.4)
    # inner border: an ink band with a bone line
    ib = M(np.abs(sd + 34) - 6)
    cv.fill(ib, INK * 1.3)
    cv.fill(M(np.abs(sd + 34) - 0.9), GOLD, 0.9)
    # central medallion: a bone disc, an ink-blot eye, a crescent moon above
    R = 148
    med = circle(cx, cy, R + 18)
    cv.shadow(med, 3, 6, 8, 0.7)
    cv.fill(med, INK * 1.2)
    disc = circle(cx, cy, R)
    cv.fill(disc, BONE)
    cv.glaze(disc, GOLD_L, 0.35)
    cv.hatch(disc, 0.3 * smooth(R * 0.55, R, np.hypot(X - cx, Y - cy)), 0, 2.4, cross=False,
             phase=(R - np.hypot(X - cx, Y - cy)) / 2.4)
    # the blot: mirrored splashes, smoothed into a pool, with flung droplets
    rng = np.random.default_rng(99)
    ey0 = cy + 24
    blot = ellipse(cx, ey0, 80, 42)
    for i in range(34):
        ang = rng.uniform(0, 2 * math.pi)
        dd = rng.uniform(24, 100)
        x = abs(math.cos(ang)) * dd * 1.15
        y = math.sin(ang) * dd * 0.62
        r = rng.uniform(8, 22) * (1 - dd / 150)
        for sgn in (-1, 1):
            blot = np.maximum(blot, circle(cx + sgn * x, ey0 + y, r))
    for (x, ln, w) in ((22, 58, 9), (58, 46, 7), (92, 30, 5)):                      # drips running down
        for sgn in (-1, 1):
            blot = np.maximum(blot, seg(cx + sgn * x, ey0 + 20, cx + sgn * x, ey0 + 20 + ln, w, w * 0.75))
            blot = np.maximum(blot, circle(cx + sgn * x, ey0 + 20 + ln, w * 0.62))
    for i in range(12):
        dd = rng.uniform(104, 132)
        ang = rng.uniform(-2.4, 0.6)
        r = rng.uniform(2.5, 6.5)
        for sgn in (-1, 1):
            x, y = cx + sgn * math.cos(ang) * dd, ey0 + math.sin(ang) * dd * 0.72
            blot = np.maximum(blot, circle(x, y, r))
            blot = np.maximum(blot, seg(cx + sgn * math.cos(ang) * (dd - 22), ey0 + math.sin(ang) * (dd - 22) * 0.72,
                                        x, y, r * 0.7, r * 0.4))
    blot = smooth(0.4, 0.6, ndimage.gaussian_filter(blot, 3.0 * K)) * disc
    cv.fill(blot, INK)
    # the eye in the blot
    ex, ey = cx, cy + 24
    eye = M(np.maximum(np.abs(X - ex) / 56 + ((Y - ey) / 26) ** 2 * 0 - 1, 0) * 0 +
            (np.hypot((X - ex) / 54, (Y - ey) / 22 * (1 + 0.0)) - 1) * 20)
    lid = M((np.abs(Y - ey) - 22 * np.sqrt(np.clip(1 - ((X - ex) / 56) ** 2, 0, 1)) ** 1.15))
    cv.fill(lid, BONE)
    cv.hatch(lid, 0.28 * smooth(6, 22, np.abs(Y - ey)), 0, 2.0, cross=False)
    iris = circle(ex, ey, 18) * lid
    cv.fill(iris, CRIM)
    cv.light(iris * radial(ex - 4, ey - 6, 16), CRIM_L * 1.4, 0.8)
    cv.fill(M(np.abs(np.hypot(X - ex, Y - ey) - 18) - 0.8) * lid, INK)
    cv.fill(ellipse(ex, ey, 5, 9) * lid, INK)
    cv.fill(circle(ex - 6, ey - 7, 3.2) * lid, WHITE)
    cv.outline(lid, 2.2)
    for k in range(-4, 5):                                            # lashes on the upper lid
        x = ex + k * 11
        y = ey - 22 * math.sqrt(max(0, 1 - ((x - ex) / 56) ** 2)) ** 1.15
        cv.fill(seg(x, y, x + k * 2.2, y - 9 + abs(k) * 0.8, 2.0, 0.8), INK)
    # the crescent moon above, gold
    mc = sub(circle(cx, cy - 66, 38), circle(cx + 0, cy - 86, 36))
    mc = sub(circle(cx, cy - 64, 40), circle(cx, cy - 82, 37))
    cv.light(ndimage.gaussian_filter(mc, 6 * K) * disc, GOLD_L, 0.6)
    cv.fill(mc, GOLD)
    cv.light(mc * lin(0, cy - 40, 0, cy - 26), GOLD_L, 0.9)
    cv.hatch(mc, 0.3 * lin(0, cy - 24, 0, cy - 50), 0, 2.0, cross=False)
    cv.outline(mc, 1.8)
    for (x, y, r) in ((cx - 70, cy - 70, 7), (cx + 70, cy - 70, 7), (cx - 92, cy - 30, 4.5), (cx + 92, cy - 30, 4.5),
                      (cx, cy - 116, 6)):
        cv.fill(star4(x, y, r, 0.2), GOLD_L)
    cv.fill(ring(cx, cy, R, 2.4), INK)
    cv.fill(ring(cx, cy, R - 6, 1.0), INK, 0.7)
    # small crescents top and bottom, mirrored, on ink lozenges
    for sgn in (-1, 1):
        y = cy + sgn * 330
        loz = M(np.abs(X - cx) * 0.8 + np.abs(Y - y) - 34)
        cv.shadow(loz, 2, 3, 3, 0.5)
        cv.fill(loz, INK * 1.2)
        cv.fill(M(np.abs(np.abs(X - cx) * 0.8 + np.abs(Y - y) - 30) - 0.8), GOLD, 0.9)
        cm2 = sub(circle(cx, y + sgn * 2, 15), circle(cx, y - sgn * 6, 13.5))
        cv.fill(cm2, GOLD_L)
        cv.outline(cm2, 1.0)
    br = Brass()
    frame_brass(br, face=False)
    # brass filigree: a ring round the medallion and scroll corners on the inner border
    rr_ = np.hypot(X - cx, Y - cy)
    mring = M(np.abs(rr_ - (R + 12)) - 6)
    thm = np.arctan2(Y - cy, X - cx)
    br.add(mring, 1 + 5 * np.sqrt(np.clip(1 - ((rr_ - R - 12) / 6) ** 2, 0, 1)) + 1.2 * np.cos(36 * thm))
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        ccx_, ccy_ = cx + sx * 220, cy + sy * 428
        scroll = []
        for t in np.linspace(0, 3.6 * math.pi, 120):
            rad = 22 * math.exp(-t / 6.5)
            scroll.append((ccx_ + sx * rad * math.cos(t), ccy_ + sy * rad * math.sin(t)))
        sm = taper(scroll, 6.0, 2.4)
        arm1 = taper([(ccx_ + sx * 22, ccy_), (ccx_ + sx * 22, ccy_ - sy * 120)], 5, 2)
        arm2 = taper([(ccx_, ccy_ + sy * 22), (ccx_ - sx * 110, ccy_ + sy * 22)], 5, 2)
        fm = U(sm, arm1, arm2)
        fsd = sdf(fm)
        br.add(fm, 1 + 3.2 * dome(-fsd, 2.6))
        bd = circle(ccx_ + sx * 6, ccy_ + sy * 6, 6.5)
        br.add(bd, 3 + 5 * dome(6.5 - np.hypot(X - ccx_ - sx * 6, Y - ccy_ - sy * 6), 6.5))
        br.gem = np.maximum(br.gem, circle(ccx_ + sx * 6, ccy_ + sy * 6, 4.0))
    rgb_b, mb = br.render()
    cv.shadow(mb, 1.5, 2.5, 2.5, 0.6)
    cv.fill(mb, rgb_b)
    cv.fill(M(np.abs(sd + 0.9) - 0.9), INK, 0.8)
    return to_image(cv, M(sd))


CARDS = {           # name: (numeral, title, scene) -- in deck order for the contact sheet
    "CardBack": None,
    "TheTower": ("XVI", "THE TOWER", tower_scene),
    "TheFool": ("0", "THE FOOL", fool_scene),
    "TheMoon": ("XVIII", "THE MOON", moon_scene),
    "TheSeeker": ("IX", "THE SEEKER", seeker_scene),
    "TheFeast": ("III", "THE FEAST", feast_scene),
    "TheCrown": ("IV", "THE CROWN", crown_scene),
    "TheScholar": ("V", "THE SCHOLAR", scholar_scene),
}


def contact_sheet():
    """All eight at their in-game size (300 x 512) on dark ink, plus a 1:1 crop of two cards."""
    names = list(CARDS)
    cw, ch, gap = 300, 512, 28
    cols = 4
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cw + (cols + 1) * gap, rows * ch + (rows + 1) * gap), (16, 12, 18, 255))
    for i, n in enumerate(names):
        p = OUT / f"{n}.png"
        if not p.exists():
            continue
        im = Image.open(p).resize((cw, ch), Image.LANCZOS)
        x = gap + (i % cols) * (cw + gap)
        y = gap + (i // cols) * (ch + gap)
        sheet.alpha_composite(im, (x, y))
    sheet.convert("RGB").save(OUT / "contact_sheet.png", optimize=True)
    a, b = Image.open(OUT / "TheFool.png"), Image.open(OUT / "TheScholar.png")
    crop = Image.new("RGBA", (1200 + gap * 3, 560 + gap * 2), (16, 12, 18, 255))
    crop.alpha_composite(a.crop((0, 200, 600, 760)), (gap, gap))
    crop.alpha_composite(b.crop((0, 350, 600, 910)), (gap * 2 + 600, gap))
    crop.convert("RGB").save(OUT / "crop_1to1.png", optimize=True)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or list(CARDS)
    for n in names:
        if CARDS[n] is None:
            im = card_back()
        else:
            num, title, fn = CARDS[n]
            im = face(n, num, title, fn, 10 + list(CARDS).index(n))
        im.save(OUT / f"{n}.png", optimize=True)
        print("wrote", OUT / f"{n}.png", flush=True)
    contact_sheet()
    UPLOAD.mkdir(parents=True, exist_ok=True)
    for n in CARDS:
        if (OUT / f"{n}.png").exists():
            shutil.copyfile(OUT / f"{n}.png", UPLOAD / f"FortuneCard_{n}.png")
    print("contact sheet and upload copies written")


if __name__ == "__main__":
    main()
