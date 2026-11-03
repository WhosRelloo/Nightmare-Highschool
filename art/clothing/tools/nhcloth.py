"""Shared helpers for Nightmare Highschool classic clothing (585x559 templates).

Coordinates follow the classic Roblox shirt/pants template. Every rect is
(x, y, w, h) with x, y inclusive.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source"
OUT = ROOT / "variants"
W, H = 585, 559

R = {
    "T_UP": (231, 8, 128, 64), "T_F": (231, 74, 128, 128), "T_R": (165, 74, 64, 128),
    "T_L": (361, 74, 64, 128), "T_B": (427, 74, 128, 128), "T_D": (231, 204, 128, 64),
    # right arm / right leg (viewer's left on the sheet)
    "RA_L": (19, 355, 64, 128), "RA_B": (85, 355, 64, 128), "RA_R": (151, 355, 64, 128),
    "RA_F": (217, 355, 64, 128), "RA_UP": (217, 289, 64, 64), "RA_D": (217, 485, 64, 64),
    # left arm / left leg
    "LA_F": (308, 355, 64, 128), "LA_L": (374, 355, 64, 128), "LA_B": (440, 355, 64, 128),
    "LA_R": (506, 355, 64, 128), "LA_UP": (308, 289, 64, 64), "LA_D": (308, 485, 64, 64),
}
TORSO_RING = ["T_R", "T_F", "T_L", "T_B"]
ARM_FACES = ["RA_L", "RA_B", "RA_R", "RA_F", "LA_F", "LA_L", "LA_B", "LA_R"]
ARM_UPS = ["RA_UP", "LA_UP"]
ARM_DOWNS = ["RA_D", "LA_D"]
ALL_REGIONS = list(R)

# School palette
NAVY = (26, 34, 66)
FOREST = (28, 62, 40)
CHARCOAL = (54, 54, 58)
IVORY = (234, 228, 212)
CREAM = (226, 210, 176)
CRIMSON = (150, 16, 28)
BLOOD = (118, 6, 14)
MAROON = (92, 2, 6)
BLACK = (22, 18, 20)
GOLD = (186, 146, 64)
CANDLE = (214, 172, 78)
TRIM_OLIVE = (104, 88, 46)   # the dull gold of the source trim
KHAKI = (128, 122, 98)
WHITE_SHIRT = (226, 226, 222)
MONO_FILL = (238, 226, 188)
MONO_EDGE = (150, 112, 44)

FONT_DIR = Path("C:/Windows/Fonts")


def font(size, bold=True, name=None):
    name = name or ("georgiab.ttf" if bold else "georgia.ttf")
    return ImageFont.truetype(str(FONT_DIR / name), size)


YY, XX = np.mgrid[0:H, 0:W]

# ---------------------------------------------------------------- io
def load(name):
    return np.array(Image.open(SRC / name).convert("RGBA")).astype(np.float32)


def save(arr, name):
    OUT.mkdir(parents=True, exist_ok=True)
    a = np.clip(arr, 0, 255).astype(np.uint8)
    a[a[..., 3] == 0, :3] = 255
    img = Image.fromarray(a, "RGBA")
    assert img.size == (W, H), img.size
    img.save(OUT / name, optimize=True)
    return OUT / name


def blank(bg=(255, 255, 255), alpha=0):
    c = np.zeros((H, W, 4), np.float32)
    c[..., :3] = bg
    c[..., 3] = alpha
    return c


# ---------------------------------------------------------------- masks
def rect_mask(names, pad=0):
    m = np.zeros((H, W), bool)
    for n in names:
        x, y, w, h = R[n]
        m[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = True
    return m


SS = 1   # supersampling factor for shape(); >1 gives anti-aliased edges


class supersample:
    """with supersample(4): ... draws every shape() at 4x and averages down."""

    def __init__(self, n):
        self.n = n

    def __enter__(self):
        global SS
        self.prev, SS = SS, self.n

    def __exit__(self, *a):
        global SS
        SS = self.prev


class _ScaledDraw:
    """ImageDraw stand-in that takes 1x template coordinates and draws at SS x."""

    def __init__(self, d, s):
        self.d, self.s = d, s

    def _pts(self, xy):
        s = self.s
        if xy and not isinstance(xy[0], (tuple, list)):
            xy = list(zip(xy[0::2], xy[1::2]))
        return [(x * s + s / 2, y * s + s / 2) for x, y in xy]

    def _box(self, b):
        s = self.s
        if isinstance(b[0], (tuple, list)):
            b = (b[0][0], b[0][1], b[1][0], b[1][1])
        x0, y0, x1, y1 = b
        return (x0 * s, y0 * s, (x1 + 1) * s - 1, (y1 + 1) * s - 1)

    def _w(self, width):
        return max(1, int(round(width * self.s)))

    def polygon(self, xy, fill=None, outline=None, width=1):
        self.d.polygon(self._pts(xy), fill=fill, outline=outline, width=self._w(width))

    def line(self, xy, fill=None, width=1, joint=None):
        self.d.line(self._pts(xy), fill=fill, width=self._w(width), joint="curve" if width > 1 else None)

    def ellipse(self, b, fill=None, outline=None, width=1):
        self.d.ellipse(self._box(b), fill=fill, outline=outline, width=self._w(width))

    def rectangle(self, b, fill=None, outline=None, width=1):
        self.d.rectangle(self._box(b), fill=fill, outline=outline, width=self._w(width))

    def rounded_rectangle(self, b, radius=0, fill=None, outline=None, width=1):
        self.d.rounded_rectangle(self._box(b), radius * self.s, fill=fill, outline=outline, width=self._w(width))

    def arc(self, b, start, end, fill=None, width=1):
        self.d.arc(self._box(b), start, end, fill=fill, width=self._w(width))

    def point(self, xy, fill=None):
        for x, y in self._pts([xy] if not isinstance(xy, list) else xy):
            h = self.s / 2
            self.d.rectangle((x - h, y - h, x + h - 1, y + h - 1), fill=fill)

    def text(self, xy, txt, font=None, fill=None, anchor=None, stroke_width=0, stroke_fill=None):
        f = ImageFont.truetype(font.path, int(font.size * self.s))
        (x, y), = self._pts([xy])
        self.d.text((x, y), txt, font=f, fill=fill, anchor=anchor,
                    stroke_width=int(stroke_width * self.s), stroke_fill=stroke_fill)


def shape(fn):
    """Run fn(ImageDraw) on an L layer and return a float mask 0..1."""
    if SS == 1:
        m = Image.new("L", (W, H), 0)
        fn(ImageDraw.Draw(m))
        return np.array(m, np.float32) / 255.0
    big = Image.new("L", (W * SS, H * SS), 0)
    fn(_ScaledDraw(ImageDraw.Draw(big), SS))
    return np.array(big.resize((W, H), Image.BOX), np.float32) / 255.0


def vmax(a):
    return a[..., :3].max(-1)


def sat(a):
    mx = a[..., :3].max(-1)
    mn = a[..., :3].min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)


def hole_mask(src):
    """The neck hole (transparent) as a bool mask, from a source shirt."""
    region = np.zeros((H, W), bool)
    region[8:202, 231:359] = True
    tr = (src[..., 3] == 0) & region
    lab, _ = ndimage.label(tr)
    return lab == lab[40, 294]


# ---------------------------------------------------------------- texture
def noise(h, w, seed, sigma):
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal((h, w)), sigma, mode="wrap")
    return n / (n.std() + 1e-6)


def fabric_detail(seed=0, cloud=0.09, twill=0.045, grain=0.035, rib=0.0, rib_period=3, h=H, w=W):
    """Per-pixel brightness multiplier that mimics the hand-drawn source fabric:
    soft cloudy mottling, a fine diagonal twill and a little grain."""
    yy, xx = np.mgrid[0:h, 0:w]
    d = 1.0
    d = d + cloud * (0.65 * noise(h, w, seed, 9) + 0.35 * noise(h, w, seed + 1, 3.5))
    d = d + twill * np.sin(2 * np.pi * (xx + yy) / 3.3)
    d = d + grain * np.random.default_rng(seed + 2).standard_normal((h, w))
    if rib:
        d = d + rib * np.sign(np.sin(2 * np.pi * xx / rib_period))
    return d.astype(np.float32)


def tint(detail, color, boost=16):
    c = np.array(color, np.float32)
    out = detail[..., None] * c + (detail[..., None] - 1) * boost
    return np.clip(out, 0, 255)


def recolor(src, mask, color, boost=16, ref=None, lo=0.0, hi=2.2):
    """Recolor pixels under mask to color, keeping the source texture
    (brightness relative to the class median)."""
    v = vmax(src)
    med = ref if ref is not None else np.median(v[mask]) if mask.any() else 1
    d = np.clip(v / max(med, 1), lo, hi)
    out = src.copy()
    out[mask, :3] = tint(d, color, boost)[mask]
    return out


def paint(c, mask, color, alpha=1.0):
    """Alpha-composite a flat colour or an HxWx3 array through a float mask."""
    m = np.clip(mask * alpha, 0, 1)[..., None]
    col = np.broadcast_to(np.array(color, np.float32), c[..., :3].shape) if np.ndim(color) == 1 or isinstance(color, tuple) else color
    c[..., :3] = c[..., :3] * (1 - m) + col * m
    c[..., 3] = np.maximum(c[..., 3], m[..., 0] * 255)
    return c


def shade(c, mask, factor):
    """Multiply brightness under a float mask (factor<1 darkens)."""
    m = mask[..., None]
    c[..., :3] = c[..., :3] * (1 - m) + c[..., :3] * factor * m
    return c


def clear(c, mask):
    c[mask, 3] = 0
    c[mask, :3] = 255
    return c


def fill_regions(c, names, color, seed=0, **tex):
    m = rect_mask(names)
    d = fabric_detail(seed, **tex)
    col = tint(d, color)
    c[m, :3] = col[m]
    c[m, 3] = 255
    return c


# ---------------------------------------------------------------- drawing
def dashed(d, p0, p1, on=3, off=2, fill=255, width=1):
    x0, y0 = p0
    x1, y1 = p1
    L = max(abs(x1 - x0), abs(y1 - y0))
    if L == 0:
        return
    t = 0
    while t < L:
        a = t / L
        b = min(t + on, L) / L
        d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=fill, width=width)
        t += on + off


def dashed_poly(d, pts, **kw):
    for a, b in zip(pts[:-1], pts[1:]):
        dashed(d, a, b, **kw)


def outline_of(mask, width=1):
    """Pixels on the inner edge of a bool mask."""
    er = ndimage.binary_erosion(mask, iterations=width)
    return mask & ~er


def text_mask(txt, size, xy, anchor="mm", fnt=None, stroke=0):
    f = fnt or font(size)
    def fn(d):
        d.text(xy, txt, font=f, fill=255, anchor=anchor, stroke_width=stroke, stroke_fill=255)
    return shape(fn)


def monogram(c, cx, cy, size, fill=MONO_FILL, edge=MONO_EDGE, outline=None, shadow=True):
    """Draw the serif 'NH' monogram: N raised to the left, H dropped to the right."""
    f = font(size, name="georgiab.ttf")
    dx, dy = size * 0.30, size * 0.26
    def letters(stroke):
        def fn(d):
            d.text((cx - dx, cy - dy), "N", font=f, fill=255, anchor="mm", stroke_width=stroke, stroke_fill=255)
            d.text((cx + dx, cy + dy), "H", font=f, fill=255, anchor="mm", stroke_width=stroke, stroke_fill=255)
        return shape(fn)
    sw = max(1, size // 14)
    if outline is not None:
        paint(c, letters(sw * 2 + 1), outline)
    if shadow:
        sh = np.roll(np.roll(letters(sw), 1, 0), 1, 1)
        shade(c, sh, 0.45)
    paint(c, letters(sw), edge)
    paint(c, letters(0), fill)
    return c


class SourceMonogram:
    """The small hand-drawn NH taken from the user's black polo, re-tintable."""

    def __init__(self):
        k = load("shirt_black_polo_khaki.png")
        box = (306, 100, 350, 136)
        crop = k[box[1]:box[3], box[0]:box[2]]
        v = vmax(crop)
        alpha = np.clip((v - 14) / 40.0, 0, 1)
        lab, n = ndimage.label(alpha > 0.3)
        sizes = ndimage.sum(np.ones_like(alpha), lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, sz in enumerate(sizes) if sz >= 40])
        keep = ndimage.binary_dilation(keep, iterations=1)
        self.alpha = alpha * keep
        self.t = np.clip((v - 70) / 130.0, 0, 1)   # 0 = gold edge, 1 = cream fill
        self.h, self.w = v.shape

    def paste(self, c, cx, cy, fill=MONO_FILL, edge=MONO_EDGE, scale=1):
        a, t = self.alpha, self.t
        if scale != 1:
            a = ndimage.zoom(a, scale, order=1)
            t = ndimage.zoom(t, scale, order=1)
        h, w = a.shape
        x0, y0 = int(cx - w / 2), int(cy - h / 2)
        col = np.array(edge, np.float32) * (1 - t[..., None]) + np.array(fill, np.float32) * t[..., None]
        m = np.zeros((H, W), np.float32)
        full = np.zeros((H, W, 3), np.float32)
        m[y0:y0 + h, x0:x0 + w] = a
        full[y0:y0 + h, x0:x0 + w] = col
        return paint(c, m, full)


def crest(c, cx, cy, w=24, h=29, field=CRIMSON, border=GOLD, letters=MONO_FILL):
    """Small heraldic shield with NH, for blazers and cardigans."""
    def shield(inset):
        def fn(d):
            x0, x1 = cx - w / 2 + inset, cx + w / 2 - inset
            y0, y1 = cy - h / 2 + inset, cy + h / 2 - inset
            mid = y0 + (y1 - y0) * 0.55
            pts = [(x0, y0), (x1, y0), (x1, mid)]
            # rounded point at the bottom
            for i in range(1, 9):
                a = i / 9
                pts.append((x1 - (x1 - cx) * a, mid + (y1 - mid) * np.sin(a * np.pi / 2)))
            for i in range(1, 9):
                a = i / 9
                pts.append((cx - (cx - x0) * a, y1 - (y1 - mid) * (1 - np.cos(a * np.pi / 2))))
            pts.append((x0, mid))
            d.polygon(pts, fill=255)
        return shape(fn)
    paint(c, shield(-1), (12, 8, 8))
    paint(c, shield(0), border)
    shade(c, outline_of(shield(0) > 0.5, 1).astype(np.float32), 0.6)
    paint(c, shield(2), field)
    # chief bar
    bar = shield(2) * rect_box(cx - w, cy - h / 2, cx + w, cy - h / 2 + 7)
    paint(c, bar, tuple(int(v * 0.65) for v in field))
    f = font(max(8, int(h * 0.36)), name="georgiab.ttf")
    def lt(d):
        d.text((cx - w * 0.16, cy - h * 0.02), "N", font=f, fill=255, anchor="mm")
        d.text((cx + w * 0.16, cy + h * 0.16), "H", font=f, fill=255, anchor="mm")
    paint(c, shape(lt), letters)
    return c


def rect_box(x0, y0, x1, y1):
    m = np.zeros((H, W), np.float32)
    m[int(max(0, y0)):int(max(0, y1)), int(max(0, x0)):int(max(0, x1))] = 1
    return m


def fill_from_shift(c, mask, dy=0, dx=0, ref=None, sigma=4):
    """Cover pixels: local colour from the surrounding reference pixels
    (normalised blur) plus fine grain copied from a shifted spot."""
    ref = (~mask) if ref is None else (ref & ~mask)
    known = ref.astype(np.float32)
    den = np.maximum(ndimage.gaussian_filter(known, sigma), 1e-4)
    shifted = np.roll(np.roll(c, dy, 0), dx, 1)
    for ch in range(3):
        img = c[..., ch]
        low = ndimage.gaussian_filter(img * known, sigma) / den
        high = shifted[..., ch] - ndimage.gaussian_filter(shifted[..., ch], 1.5)
        c[..., ch] = np.where(mask, low + high, img)
    c[mask, 3] = 255
    return c


def remove_magenta(c):
    """Replace magenta template guide lines with their neighbours' colour."""
    mag = (c[..., 0] > 170) & (c[..., 1] < 90) & (c[..., 2] > 170) & (c[..., 3] > 0)
    mag = ndimage.binary_dilation(mag, iterations=1) & (c[..., 0] > c[..., 1] + 60) & (c[..., 2] > c[..., 1] + 60)
    known = ~mag
    rgb = c[..., :3].copy()
    alpha = c[..., 3].copy()
    for _ in range(6):
        if not mag.any():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros((H, W), np.float32)
        acca = np.zeros((H, W), np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * k[..., None]
            acca += np.roll(np.roll(alpha, dy, 0), dx, 1) * k
            cnt += k
        fillable = mag & (cnt > 0)
        rgb[fillable] = acc[fillable] / cnt[fillable, None]
        alpha[fillable] = acca[fillable] / cnt[fillable]
        known = known | fillable
        mag = mag & ~fillable
    c[..., :3] = rgb
    c[..., 3] = np.where(alpha > 127, 255, 0)
    c[c[..., 3] == 0, :3] = 255
    return c


def scuffs(c, mask, seed, amount=0.35, color=(58, 44, 30), blobs=9, spread=6):
    """Dirt smudges limited to a bool mask."""
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)
    ys, xs = np.nonzero(mask)
    for _ in range(blobs):
        i = rng.integers(len(ys))
        m[ys[i], xs[i]] = 1
    m = ndimage.gaussian_filter(m, spread)
    m = m / (m.max() + 1e-6)
    m = m * np.clip(0.6 + 0.6 * noise(H, W, seed + 9, 1.2), 0, 1)
    m = np.clip(m * 1.4, 0, 1) * amount * mask
    c[..., :3] = c[..., :3] * (1 - m[..., None]) + np.array(color, np.float32) * m[..., None]
    return c


# ---------------------------------------------------------------- quality pass
def lift(c, mask, dx=1, dy=1, sigma=1.0, strength=0.45):
    """Soft contact shadow under a raised detail (call before painting it)."""
    m = np.clip(np.asarray(mask, np.float32), 0, 1)
    sh = ndimage.gaussian_filter(np.roll(np.roll(m, dy, 0), dx, 1), sigma) * (1 - m)
    sh = np.clip(sh * 1.6, 0, 1) * (c[..., 3] > 0)
    return shade(c, sh, 1 - strength)


def finish(c, creases=True, seed=0):
    """Quality pass: rounded shading on every face, occlusion where the arms and
    legs press against the body, a touch of top light, and elbow/knee creases."""
    vis = c[..., 3] > 0
    f = np.ones((H, W), np.float32)
    for n in TORSO_RING + ARM_FACES:
        x, y, w, h = R[n]
        m = rect_mask([n])
        xr = (XX - (x + (w - 1) / 2)) / (w / 2)
        dx = np.maximum(np.minimum(XX - x, x + w - 1 - XX), 0).astype(np.float32)
        face = (1 - 0.08 * np.abs(xr) ** 2 - 0.16 * np.exp(-dx / 2.0)) * (1.05 - 0.09 * (YY - y) / h)
        if n in ("T_R", "T_L", "RA_L", "LA_R"):
            face = face * 0.9
        f = np.where(m, face, f)
    for n in ["T_UP", "T_D"] + ARM_UPS + ARM_DOWNS:
        x, y, w, h = R[n]
        m = rect_mask([n])
        d = np.maximum(np.minimum(np.minimum(XX - x, x + w - 1 - XX), np.minimum(YY - y, y + h - 1 - YY)), 0).astype(np.float32)
        f = np.where(m, 1 - 0.14 * np.exp(-d / 2.0), f)
    c[vis, :3] = np.clip(c[vis, :3] * f[vis, None], 0, 255)
    if creases:
        rng = np.random.default_rng(seed)
        for n in ARM_FACES:
            x, y, w, h = R[n]
            for _ in range(3):
                x0, y0, L = x + rng.uniform(4, w - 24), rng.uniform(392, 404), rng.uniform(12, 20)
                dk = shape(lambda d: d.arc((x0, y0, x0 + L, y0 + 5), 200, 340, fill=255)) * vis * rect_mask([n])
                lt = np.roll(dk, 1, 0) * (dk < 0.3)
                shade(c, dk, 0.7)
                c[..., :3] = np.clip(c[..., :3] + 16 * lt[..., None], 0, 255)
    return c



# uniform pieces whose sleeves/legs end near the elbow or knee, or that keep the
# source denim's own whiskering: no extra creases on these
UNIFORM_NO_CREASE = {
    "shirt_polo_delinquent.png", "shirt_gym_pe.png",
    "pants_jeans_dark_indigo.png", "pants_jeans_black.png", "pants_jeans_ripped.png",
    "pants_shorts_khaki.png", "pants_skirt_pleated_tartan.png",
}


def save_hq(c, name):
    """Quality pass, then save (used by the uniform set)."""
    return save(finish(c, creases=name not in UNIFORM_NO_CREASE, seed=sum(map(ord, name))), name)
