"""Props batch 29 (the soft furnishings and tapestry kit): the woven maps, painted in numpy / PIL.

Every textile here is an original design in the Institution's colours (crimson #600E1A, ink, bone, gold, soot, moss,
plum), drawn as flat colour, then *woven*:
  pile    a knotted rug: the design sampled to a grid of knots (one colour each, from the rug's palette, so curves step like
          a real hand-knotted rug), dyed a touch unevenly (abrash bands), each knot a little dome of pile, worn where feet go
  tiles   the carpet tiles: the same pile, drawn and noised seamlessly so the tiles butt edge to edge
  coir    a doormat: coarse bristle tufts, the letters dyed in
  loop    a cotton bath mat: dense round loops
  tapestry  (tapestry_weave.py) ribbed weft-faced weaving with hatched shading and gilt thread

Each textile writes textures/<Name>_{color,normal,rough}.png (and _metal when it has gilt thread). The foot of each map is
a 32 px swatch band: fringe wool on the left, the backing / binding colour on the right; nh_props_batch29.textile_uv
maps the fringe, the edges and the back onto it. The design fills the rest.

The upholstery sets the sofas are baked from (source_fabric/NH_<Set>_{color,normal,rough}.png, seamless, 1024) are made
here too: velvet, two damasks, a regency stripe and a small tapestry weave.

  python art/props/weave_textiles.py [names...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
FAB = os.path.join(HERE, "source_fabric")
os.makedirs(FAB, exist_ok=True)
sys.path.insert(0, HERE)
import window_shapes as WS  # noqa: E402

SW = 32          # the swatch band at the foot of every textile map (px)
FONT = "C:/Windows/Fonts/gothice_.ttf"

from weave_dyes import C  # noqa: E402  (the Institution's dyes)


# ------------------------------------------------------------------ noise (periodic, so every map can tile)

def pnoise(h, w, sigma, seed=0):
    """Periodic smooth noise (0..1): white noise low-passed in the frequency domain; sigma ~ feature size in px."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h, w)).astype(np.float32)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * math.pi * sigma) ** 2 / 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * g)).astype(np.float32)
    out -= out.min()
    return out / max(1e-6, out.max())


def fbm(h, w, sigma, octaves=4, seed=0):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += pnoise(h, w, max(0.6, sigma / 2 ** o), seed + o) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def height_to_normal(h, strength):
    """A tangent-space normal map (OpenGL, green up, as Blender bakes them) from a height field (0..1)."""
    gy, gx = np.gradient(h.astype(np.float32))
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (n * 0.5 + 0.5)


def save(name, color, normal, rough, metal=None, folder=OUT):
    def wr(a, kind, mode="RGB"):
        a = np.clip(a, 0, 1)
        if a.ndim == 2:
            a = np.dstack([a, a, a])
        Image.fromarray((a * 255 + 0.5).astype(np.uint8), mode).save(os.path.join(folder, f"{name}_{kind}.png"))
    wr(color, "color")
    wr(normal, "normal")
    wr(rough, "rough")
    if metal is not None and metal.max() > 0.02:
        wr(metal, "metal")
    else:
        p = os.path.join(folder, f"{name}_metal.png")
        if os.path.exists(p):
            os.remove(p)
    print(f"[weave] {name} {color.shape[1]}x{color.shape[0]}")


# ------------------------------------------------------------------ drawing

class Canvas:
    """A flat colour design in px (y down). Drawn with exact dye colours; .seamless draws every shape at its wrapped
    copies too, so a tile repeats with no seam."""

    def __init__(self, w, h, fill, seamless=False):
        self.w, self.h = w, h
        f = C[fill] if isinstance(fill, str) else tuple(fill)
        self.im = Image.new("RGB", (w, h), f)
        self.d = ImageDraw.Draw(self.im)
        self.seamless = seamless
        self.used = {f}

    def _c(self, c):
        c = C[c] if isinstance(c, str) else tuple(int(v) for v in c)
        self.used.add(c)
        return c

    def palette(self):
        """Every dye this design used: the rug's knot colours."""
        return sorted(self.used)

    def _offs(self):
        if not self.seamless:
            return [(0, 0)]
        return [(dx, dy) for dx in (-self.w, 0, self.w) for dy in (-self.h, 0, self.h)]

    def poly(self, pts, col, outline=None, width=0):
        col = self._c(col)
        oc = self._c(outline) if outline else None
        for dx, dy in self._offs():
            p = [(x + dx, y + dy) for x, y in pts]
            self.d.polygon(p, fill=col)
            if oc:
                self.d.line(p + [p[0]], fill=oc, width=max(1, int(round(width))), joint="curve")

    def line(self, pts, col, width):
        col = self._c(col)
        for dx, dy in self._offs():
            p = [(x + dx, y + dy) for x, y in pts]
            self.d.line(p, fill=col, width=int(width), joint="curve")
            r = width / 2
            for x, y in (p[0], p[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def circle(self, cx, cy, r, col, outline=None, width=0):
        self.poly(circle(cx, cy, r), col, outline, width)

    def ring(self, cx, cy, r, width, col, n=96):
        self.line(circle(cx, cy, r, n) + [circle(cx, cy, r, n)[0]], col, width)

    def rect(self, x0, y0, x1, y1, col):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col)

    def text(self, xy, s, size, col, anchor="mm", font=FONT):
        f = ImageFont.truetype(font, int(size))
        col = self._c(col)
        for dx, dy in self._offs():
            self.d.text((xy[0] + dx, xy[1] + dy), s, font=f, fill=col, anchor=anchor)

    def array(self):
        return np.asarray(self.im, np.float32) / 255


def circle(cx, cy, r, n=72, a0=0.0, ry=None):
    ry = r if ry is None else ry
    return [(cx + math.cos(a0 + i / n * 2 * math.pi) * r, cy + math.sin(a0 + i / n * 2 * math.pi) * ry) for i in range(n)]


def foil(cx, cy, r, lobes=4, k=0.46, a0=-math.pi / 2, n=96):
    return [(x, y) for x, y in WS.foil_outline(cx, cy, r, lobes, n=n, a0=a0, k=k)]


def lobed(cx, cy, rx, ry, lobes, depth=0.08, n=240, a0=-math.pi / 2):
    """A lobed medallion (rosette) outline: an ellipse with `lobes` scallops."""
    pts = []
    for i in range(n):
        a = a0 + i / n * 2 * math.pi
        s = 1 - depth + depth * abs(math.cos(a * lobes / 2)) ** 0.5
        pts.append((cx + math.cos(a) * rx * s, cy + math.sin(a) * ry * s))
    return pts


def crescent(cx, cy, r, tilt=0.0, shift=0.4, bite=0.9):
    return [(x, cy - (z - cy)) for x, z in WS.crescent(cx, cy, r, shift=shift, n=48, tilt=tilt, bite=bite)]


def star(cx, cy, r, pts=4, inner=0.38, a0=-math.pi / 2):
    out = []
    for i in range(pts * 2):
        a = a0 + i * math.pi / pts
        rr = r if i % 2 == 0 else r * inner
        out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return out


def diamond(cx, cy, rx, ry):
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def mirror_x(pts, cx):
    """A symmetric outline from its right half (top to bottom, x >= cx)."""
    return pts + [(2 * cx - x, y) for x, y in reversed(pts)]


def leaf(x0, y0, x1, y1, w, n=12):
    """A pointed leaf from (x0, y0) to (x1, y1), w wide at its middle."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    a = [(x0 + dx * t + nx * w / 2 * math.sin(math.pi * t), y0 + dy * t + ny * w / 2 * math.sin(math.pi * t)) for t in [i / n for i in range(n + 1)]]
    b = [(x0 + dx * t - nx * w / 2 * math.sin(math.pi * t), y0 + dy * t - ny * w / 2 * math.sin(math.pi * t)) for t in [i / n for i in range(n, -1, -1)]]
    return a + b[1:-1]


def key_shape(cv, cx, cy, s, col, ring_col=None):
    """The school's key, upright (bow at the top): a quatrefoil bow, a shaft and a two-step bit."""
    cv.poly(foil(cx, cy - 0.32 * s, 0.2 * s, 4, k=0.5), col)
    cv.circle(cx, cy - 0.32 * s, 0.07 * s, ring_col or "ink")
    cv.rect(cx - 0.035 * s, cy - 0.14 * s, cx + 0.035 * s, cy + 0.42 * s, col)
    cv.rect(cx + 0.035 * s, cy + 0.22 * s, cx + 0.16 * s, cy + 0.3 * s, col)
    cv.rect(cx + 0.035 * s, cy + 0.34 * s, cx + 0.13 * s, cy + 0.42 * s, col)
    cv.rect(cx - 0.08 * s, cy - 0.1 * s, cx + 0.08 * s, cy - 0.06 * s, col)


def shield_pts(cx, cy, s):
    return [(cx - 0.3 * s, cy - 0.36 * s), (cx + 0.3 * s, cy - 0.36 * s), (cx + 0.3 * s, cy), (cx + 0.2 * s, cy + 0.24 * s), (cx, cy + 0.38 * s),
            (cx - 0.2 * s, cy + 0.24 * s), (cx - 0.3 * s, cy)]


def crest(cv, cx, cy, s, field="crimson", rim="gold", charge="gold"):
    """The school crest: a crimson shield, a gilt rim, a gilt quatrefoil over a key, a crescent in chief."""
    cv.poly(shield_pts(cx, cy, s * 1.08), rim)
    cv.poly(shield_pts(cx, cy, s), field)
    cv.poly(foil(cx, cy + 0.04 * s, 0.16 * s, 4), charge)
    cv.circle(cx, cy + 0.04 * s, 0.05 * s, field)
    cv.poly(crescent(cx, cy - 0.22 * s, 0.075 * s, tilt=math.pi / 2), charge)


def band(path, w0, w1):
    """A tapered band along a path (a stroke w0 wide at its start, w1 at its end) as one outline."""
    n = len(path)
    left, right = [], []
    for i, (x, y) in enumerate(path):
        ax, ay = path[max(i - 1, 0)]
        bx, by = path[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x - dy / L * w, y + dx / L * w))
        right.append((x + dy / L * w, y - dx / L * w))
    return left + list(reversed(right))


def damask_motif(cv, cx, cy, s, col, accent=None):
    """A symmetric damask flower, s high: an ogee bud cupped by two C-scrolls that curl to a berry, acanthus sprays and
    berries above, a vase foot with falling leaves below. Every part is drawn on both sides of cx."""
    a = accent or col
    P = lambda u, v: (cx + u * s, cy + v * s)
    bud = [(0, -0.46), (0.05, -0.36), (0.1, -0.24), (0.12, -0.12), (0.1, -0.02), (0.05, 0.05), (0, 0.07)]
    cv.poly([P(u, v) for u, v in bud] + [P(-u, v) for u, v in reversed(bud)], col)
    slit = [(0, -0.34), (0.035, -0.22), (0.04, -0.1), (0, -0.04)]
    cv.poly([P(u, v) for u, v in slit] + [P(-u, v) for u, v in reversed(slit)], a)
    for sx in (-1, 1):
        # the C-scroll: from the bud's foot up, out, round and down, tightening to a berry
        path = []
        for i in range(40):
            t = i / 39
            ang = math.radians(-160 + 285 * t)
            r = 0.14 - 0.07 * t
            path.append(P(sx * (0.17 + math.cos(ang) * r), 0.13 + math.sin(ang) * r))
        cv.poly(band(path, 0.065 * s, 0.018 * s), col)
        ex, ey = path[-1]
        cv.circle(ex, ey, 0.03 * s, a)
        # acanthus sprays and berries above
        cv.poly(leaf(*P(sx * 0.05, -0.12), *P(sx * 0.27, -0.33), 0.06 * s), col)
        cv.poly(leaf(*P(sx * 0.03, -0.3), *P(sx * 0.13, -0.47), 0.045 * s), col)
        cv.circle(*P(sx * 0.3, -0.36), 0.028 * s, a)
        cv.circle(*P(sx * 0.155, -0.5), 0.022 * s, a)
        # falling leaves from the vase
        cv.poly(leaf(*P(sx * 0.04, 0.3), *P(sx * 0.24, 0.44), 0.05 * s), col)
    # the vase: a stem, a knop, a spreading foot
    cv.poly([P(-0.035, 0.03), P(0.035, 0.03), P(0.03, 0.28), P(-0.03, 0.28)], col)
    cv.poly(diamond(*P(0, 0.2), 0.06 * s, 0.05 * s), col)
    cv.poly(diamond(*P(0, 0.2), 0.025 * s, 0.022 * s), a)
    cv.poly([P(-0.04, 0.28), P(0.04, 0.28), P(0.13, 0.42), P(0.13, 0.46), P(-0.13, 0.46), P(-0.13, 0.42)], col)


# ------------------------------------------------------------------ the weaves

def _nearest(arr, pal):
    """Each pixel to the nearest dye in pal (list of sRGB 0..255)."""
    p = np.array(pal, np.float32) / 255
    d = ((arr[..., None, :] - p[None, None]) ** 2).sum(-1)
    return p[d.argmin(-1)]


def pile(design, pal, knot=4, worn=0.0, seed=0, foundation="bone", tile=False, abrash=0.05):
    """A knotted pile from a flat design (H, W, 3 float): returns colour, height, roughness at the design's size."""
    H, W, _ = design.shape
    kh, kw = H // knot, W // knot
    small = np.asarray(Image.fromarray((design * 255).astype(np.uint8)).resize((kw, kh), Image.BOX), np.float32) / 255
    small = _nearest(small, pal)
    rng = np.random.default_rng(seed)
    # dye lots: each row of knots a touch lighter or darker, drifting along the row (abrash)
    rows = pnoise(kh, kw, kw / 6, seed + 1)
    rowband = (pnoise(kh, 1, 6, seed + 2) - 0.5) * 2
    small = small * (1 + abrash * (rowband * 0.7 + (rows - 0.5)))[..., None]
    small = small * (1 + rng.normal(0, 0.03, (kh, kw, 1)).astype(np.float32))
    col = np.repeat(np.repeat(small, knot, 0), knot, 1)
    col = np.pad(col, ((0, H - col.shape[0]), (0, W - col.shape[1]), (0, 0)), mode="edge")
    # each knot a soft dome of pile, plus fine fibre noise
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = (xx % knot + 0.5) / knot - 0.5
    v = (yy % knot + 0.5) / knot - 0.5
    dome = np.clip(1 - (u * u + v * v) * 2.6, 0, 1) ** 0.6
    fib = pnoise(H, W, 0.8, seed + 3)
    hgt = 0.55 * dome + 0.45 * fib
    # wear: feet rub the pile flat and paler down the middle and in patches; heavy wear shows the knotted foundation
    rough = 0.93 + 0.05 * (fib - 0.5)
    if worn > 0:
        # feet rub the pile down the middle and in patches: shorter, paler, a little shinier; where it is worn through,
        # the knots' roots show as rows of dark tufts between the pale weft of the foundation
        cx = np.abs(xx / W - 0.5) * 2
        cy = np.abs(yy / H - 0.5) * 2
        path = np.clip(1 - np.maximum(cx * 0.85, cy * 0.7), 0, 1)
        blot = fbm(H, W, W / 14, 5, seed + 4)
        wear = np.clip((path * 0.75 + blot - 0.82) * 2.6 * worn, 0, 1)
        grey = col.mean(2, keepdims=True)
        col = col * (1 - 0.3 * wear[..., None]) + (col * 0.6 + grey * 0.55 + 0.03) * 0.3 * wear[..., None]
        bare = np.clip((wear - 0.8) * 8, 0, 1) * (fib > 0.35)
        f = np.array(C[foundation], np.float32) / 255
        weft = ((yy % knot) < 1.3)
        roots = col * 0.55
        bare_col = np.where(weft[..., None], f * 0.62 + col * 0.15, roots * 0.85)
        col = col * (1 - bare[..., None]) + bare_col * bare[..., None]
        hgt = hgt * (1 - 0.55 * wear) * (1 - 0.5 * bare) + 0.25 * bare * weft
        rough = rough - 0.07 * wear
    col = col * (0.84 + 0.2 * hgt[..., None])
    col = np.asarray(Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45)), np.float32) / 255
    return col, hgt, rough


def coir(design, seed=0):
    """A coir doormat: tufts of stiff fibre on a grid, the design dyed into them."""
    H, W, _ = design.shape
    rng = np.random.default_rng(seed)
    base = np.array((150, 104, 60), np.float32) / 255
    fib = Image.new("L", (W, H), 128)
    d = ImageDraw.Draw(fib)
    for _ in range(int(W * H / 22)):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        a = rng.normal(math.pi / 2, 0.5)
        L = rng.uniform(4, 13)
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], fill=int(rng.uniform(40, 230)), width=1)
    f = np.asarray(fib, np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tuft = (np.sin(xx / 9 * math.pi) ** 2) * (np.sin(yy / 9 * math.pi) ** 2)
    hgt = 0.6 * f + 0.4 * tuft
    dye = design.mean(2)
    dyed = smooth(0.55, 0.3, dye)        # dark parts of the design are dyed into the coir
    col = base[None, None] * (0.72 + 0.55 * f[..., None]) * (0.85 + 0.2 * tuft[..., None])
    ink = np.array((30, 20, 14), np.float32) / 255
    bleed = np.asarray(Image.fromarray((dyed * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    bleed = np.clip(bleed * (0.75 + 0.5 * f), 0, 1)
    col = col * (1 - bleed[..., None] * 0.92) + ink * (0.6 + 0.8 * f[..., None]) * bleed[..., None] * 0.92
    rough = np.full((H, W), 0.97, np.float32)
    return col, hgt, rough


def loops(design, seed=0):
    """Cotton loop pile (a bath mat): dense round loops, soft and bright."""
    H, W, _ = design.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    p = 7.0
    off = (np.floor(yy / p) % 2) * p / 2
    u = ((xx + off) % p) / p - 0.5
    v = (yy % p) / p - 0.5
    r = np.sqrt(u * u + v * v)
    loop = np.clip(1 - np.abs(r - 0.3) * 6, 0, 1)
    fib = pnoise(H, W, 0.9, seed)
    hgt = 0.7 * loop + 0.3 * fib
    col = design * (0.8 + 0.25 * hgt[..., None])
    return col, hgt, np.full((H, W), 0.95, np.float32)


# ------------------------------------------------------------------ layout into the final map

def swatches(w, fringe, backing, seed=0):
    """The 32 px band: twisted fringe wool on the left half, the binding / backing on the right."""
    rng = np.random.default_rng(seed)
    band = np.zeros((SW, w, 3), np.float32)
    hgt = np.zeros((SW, w), np.float32)
    xx = np.arange(w)[None, :].repeat(SW, 0).astype(np.float32)
    yy = np.arange(SW)[:, None].repeat(w, 1).astype(np.float32)
    twist = 0.5 + 0.5 * np.sin((xx * 0.9 + yy * 0.6))
    fr = np.array(C[fringe], np.float32) / 255
    bk = np.array(C[backing], np.float32) / 255
    left = xx < w / 2
    var = 1 + rng.normal(0, 0.04, (SW, w)).astype(np.float32)
    band[left] = (fr * (0.82 + 0.22 * twist[..., None]) * var[..., None])[left]
    rib = 0.5 + 0.5 * np.sin(yy * math.pi / 2)
    band[~left] = (bk * (0.85 + 0.18 * rib[..., None]) * var[..., None])[~left]
    hgt[left] = twist[left]
    hgt[~left] = rib[~left] * 0.6
    return band, hgt


def finish(name, col, hgt, rough, size, fringe="cream", backing="bone", strength=5.0, metal=None, band=True):
    """Fit the woven design to the map size (W, H) (the band at the foot), the normal map from the height, and save."""
    W, H = size
    Hd = H - (SW if band else 0)
    def fit(a, mode=Image.LANCZOS):
        if a.ndim == 2:
            im = Image.fromarray(np.clip(a * 65535, 0, 65535).astype(np.uint16)) if False else Image.fromarray(a.astype(np.float32), "F")
            return np.asarray(im.resize((W, Hd), Image.BILINEAR), np.float32)
        return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W, Hd), mode), np.float32) / 255
    sx, sy = W / col.shape[1], Hd / col.shape[0]
    c, h, r = fit(col), fit(hgt), fit(rough)
    m = fit(metal) if metal is not None else None
    if band:
        bc, bh = swatches(W, fringe, backing)
        c = np.concatenate([c, bc], 0)
        h = np.concatenate([h, bh], 0)
        r = np.concatenate([r, np.full((SW, W), 0.94, np.float32)], 0)
        if m is not None:
            m = np.concatenate([m, np.zeros((SW, W), np.float32)], 0)
    # the normal from the height at the final size: the slope is scaled back for a stretched axis
    gy, gx = np.gradient(h)
    n = np.dstack([-gx * strength * sx ** -0.0, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    save(name, c, n * 0.5 + 0.5, r, m)


def px(studs_w, studs_d, long=2048):
    """Design canvas size in px for a rug studs_w x studs_d (the long side `long` px)."""
    k = long / max(studs_w, studs_d)
    return int(round(studs_w * k)), int(round(studs_d * k))


# ================================================================== the rugs

import weave_motifs as M  # noqa: E402  (the motifs draw on this module's Canvas)

def _rose_border(cv, x0, y0, x1, y1, w, seed=0):
    """A border band of a thorned rose stem meandering along it (horizontal or vertical)."""
    horiz = abs(x1 - x0) > abs(y1 - y0)
    L = abs(x1 - x0) if horiz else abs(y1 - y0)
    n = max(2, int(round(L / 260)))
    pts = []
    for i in range(n * 24 + 1):
        t = i / (n * 24)
        off = math.sin(t * n * math.pi * 2) * w * 0.18
        pts.append((x0 + t * L, (y0 + y1) / 2 + off) if horiz else ((x0 + x1) / 2 + off, y0 + t * L))
    M.rose_spray(cv, pts, w * 0.06, "mossdk", "crimson", "crimsondk", "rose", "moss", "mossdk", every=24, r=w * 0.19)


def moth_medallion_rug():
    W, H = px(12, 8)
    cv = Canvas(W, H, "crimsondk")
    cv.rect(0, 0, W, H, "bone")
    b0, bw, g = 18, 150, 26
    cv.rect(b0, b0, W - b0, H - b0, "ink")
    for (x0, y0, x1, y1) in ((b0, b0, W - b0, b0 + g), (b0, H - b0 - g, W - b0, H - b0)):
        _guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 36)
    for (x0, y0, x1, y1) in ((b0, b0 + g, b0 + g, H - b0 - g), (W - b0 - g, b0 + g, W - b0, H - b0 - g)):
        _guard(cv, x0, y0, x1, y1, "bone", "crimson", "teeth", 36)
    m0, m1 = b0 + g, b0 + g + bw
    for y in (m0, H - m1):
        _rose_border(cv, m1, y, W - m1, y + bw, bw)
    for x in (m0, W - m1):
        _rose_border(cv, x, m1, x + bw, H - m1, bw)
    for x, y in ((m0, m0), (W - m1, m0), (m0, H - m1), (W - m1, H - m1)):
        cv.rect(x, y, x + bw, y + bw, "ink")
        M.eye(cv, x + bw / 2, y + bw / 2, bw * 0.8, "bone", "crimsonlt", "soot")
    f0 = m1
    cv.rect(f0, f0, W - f0, H - f0, "gold")
    f0 += 14
    cv.rect(f0, f0, W - f0, H - f0, "crimson")
    cx, cy = W / 2, H / 2
    # the field: keys and four-point stars on a diamond grid
    sp = 120
    for i in range(-10, 11):
        for j in range(-6, 7):
            x, y = cx + i * sp, cy + j * sp * 0.8
            if not (f0 + 50 < x < W - f0 - 50 and f0 + 50 < y < H - f0 - 50):
                continue
            if (i + j) % 2 == 0:
                key_shape(cv, x, y, 76, "crimsondk", "crimson")
            else:
                cv.poly(star(x, y, 16, 4), "golddk")
    # the corners: cobwebs strung across them, a spider dropping from each
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = f0 if sx < 0 else W - f0
        y = f0 if sy < 0 else H - f0
        a0 = {(-1, -1): 0.0, (1, -1): math.pi / 2, (1, 1): math.pi, (-1, 1): -math.pi / 2}[(sx, sy)]
        M.web(cv, x, y, 360, "bone", 7, spokes=6, rings=6, a0=a0, span=math.pi / 2)
        sxp, syp = x - sx * 230, y - sy * 150
        cv.line([(sxp, y - sy * 10), (sxp, syp - 30)], "bone", 4)
        M.spider(cv, sxp, syp, 70, "soot", "crimsonlt", thread=False)
    # the medallion: an ink rosette, bats circling it, a crimson foil, the moth on a crescent
    cv.poly(lobed(cx, cy, 430, 310, 16, 0.07), "bone")
    cv.poly(lobed(cx, cy, 408, 290, 16, 0.07), "ink")
    for k in range(10):
        a = k / 10 * 2 * math.pi
        bx, by = cx + math.cos(a) * 325, cy + math.sin(a) * 225
        M.bat(cv, bx, by, 150, "crimsonlt", "gold", tilt=a + math.pi / 2)
    for sy in (-1, 1):
        py_ = cy + sy * 370
        cv.poly(lobed(cx, py_, 100, 70, 6, 0.12), "bone")
        cv.poly(lobed(cx, py_, 86, 58, 6, 0.12), "ink")
        M.eye(cv, cx, py_, 120, "bone", "gold", "soot", lashes=False)
    cv.poly(foil(cx, cy, 240, 8, k=0.3), "bone")
    cv.poly(foil(cx, cy, 222, 8, k=0.3), "crimson")
    cv.poly(crescent(cx, cy + 40, 200, tilt=math.pi / 2, shift=0.62, bite=0.86), "gold")
    M.moth(cv, cx, cy - 20, 410, "bone", "plum", "gold", "crimsonlt")
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.35, seed=2901)
    finish("MothMedallionRug", col, hgt, rough, (2048, 1536), backing="ink")


def watching_runner():
    W, H = px(18, 4)
    cv = Canvas(W, H, "ink")
    cv.rect(0, 0, W, H, "bone")
    b = 14
    cv.rect(b, b, W - b, H - b, "crimsondk")
    t = 40
    for y0, flip in ((b, 1), (H - b - t, -1)):
        cv.rect(b, y0, W - b, y0 + t, "soot")
        n = int((W - 2 * b) / 46)
        for k in range(n):
            x = b + k * (W - 2 * b) / n
            if flip > 0:
                cv.rect(x + 6, y0 + 8, x + 28, y0 + t, "bone")
                cv.rect(x, y0 + 26, x + 46, y0 + t, "bone")
            else:
                cv.rect(x + 6, y0, x + 28, y0 + t - 8, "bone")
                cv.rect(x, y0, x + 46, y0 + t - 26, "bone")
    f0 = b + t + 8
    cv.rect(b, f0, W - b, H - f0, "gold")
    cv.rect(b, f0 + 8, W - b, H - f0 - 8, "ink")
    cy = H / 2
    n = 6
    step = (W - 2 * b) / n
    hh = (H - 2 * f0 - 16) / 2 - 8
    for k in range(n):
        x = b + (k + 0.5) * step
        cv.poly(diamond(x, cy, step * 0.42, hh), "bone")
        cv.poly(diamond(x, cy, step * 0.42 - 16, hh - 12), "crimson")
        cv.poly(diamond(x, cy, step * 0.42 - 34, hh - 26), "ink")
        M.eye(cv, x, cy, step * 0.42, "bone", "crimsonlt" if k % 2 else "gold", "soot")
        M.bat(cv, x + step * 0.5, cy, step * 0.3, "crimsonlt", "gold", tilt=0.25 if k % 2 else -0.25)
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.5, seed=2902)
    finish("WatchingRunner", col, hgt, rough, (2048, 512), backing="soot")


def thorn_rose_rug():
    W = H = 2048
    cv = Canvas(W, H, "soot")
    c = W / 2
    R = W / 2 - 4
    cv.circle(c, c, R, "bone")
    cv.circle(c, c, R - 16, "ink")
    for k in range(16):
        a = k / 16 * 2 * math.pi - math.pi / 2
        x, y = c + math.cos(a) * (R - 82), c + math.sin(a) * (R - 82)
        if k % 2 == 0:
            M.bat(cv, x, y, 190, "crimsonlt", "gold", tilt=a + math.pi / 2)
        else:
            cv.poly(crescent(x, y, 30, tilt=a + math.pi, shift=0.42), "bone")
    cv.ring(c, c, R - 150, 14, "bone")
    cv.circle(c, c, R - 158, "crimsondk")
    r1 = R - 170
    for k in range(12):
        a = k / 12 * 2 * math.pi - math.pi / 2
        hx, hy = c + math.cos(a) * r1 * 0.8, c + math.sin(a) * r1 * 0.8
        cv.poly(leaf(c + math.cos(a) * r1 * 0.3, c + math.sin(a) * r1 * 0.3, c + math.cos(a) * r1 * 0.97, c + math.sin(a) * r1 * 0.97, r1 * 0.26), "bone")
        cv.poly(leaf(c + math.cos(a) * r1 * 0.34, c + math.sin(a) * r1 * 0.34, c + math.cos(a) * r1 * 0.9, c + math.sin(a) * r1 * 0.9, r1 * 0.2), "ink")
        M.rose(cv, hx, hy, r1 * 0.075, "crimson", "crimsondk", "rose", a0=a)
        b = a + math.pi / 12
        cv.poly(star(c + math.cos(b) * r1 * 0.88, c + math.sin(b) * r1 * 0.88, r1 * 0.05, 4), "gold")
        M.eye(cv, c + math.cos(a) * r1 * 0.56, c + math.sin(a) * r1 * 0.56, r1 * 0.13, "bone", "gold", "soot", lashes=False) if k % 3 == 0 else None
    # a thorn wreath round a great rose
    wr = r1 * 0.36
    cv.circle(c, c, wr + 30, "ink")
    pts = [(c + math.cos(t) * wr * (1 + 0.04 * math.sin(t * 9)), c + math.sin(t) * wr * (1 + 0.04 * math.sin(t * 9))) for t in [i / 180 * 2 * math.pi for i in range(181)]]
    M.thorn_vine(cv, pts, 16, "mossdk", every=6, thorn=1.9)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        M.rose_leaf(cv, c + math.cos(a) * wr, c + math.sin(a) * wr, c + math.cos(a + 0.35) * wr * 1.12, c + math.sin(a + 0.35) * wr * 1.12, 40, "moss", "mossdk")
    M.rose(cv, c, c, wr * 0.72, "crimson", "crimsondk", "rose")
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.25, seed=2903)
    finish("ThornRoseRug", col, hgt, rough, (2048, 2048), backing="bone")


def raven_hearth_rug():
    W, H = px(7, 3.5)
    cv = Canvas(W, H, "soot")
    cx, cy = W / 2, 0
    R = W / 2
    def half(r):
        return [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in [i / 96 * math.pi for i in range(97)]]
    cv.poly(half(R - 2), "bone")
    cv.poly(half(R - 16), "ink")
    for k in range(17):
        a = (k + 0.5) / 17 * math.pi
        tip = (cx + math.cos(a) * (R - 26), cy + math.sin(a) * (R - 26))
        base = (cx + math.cos(a) * (R - 108), cy + math.sin(a) * (R - 108))
        mid = (cx + math.cos(a) * (R - 64), cy + math.sin(a) * (R - 64))
        cv.poly(leaf(base[0], base[1], tip[0], tip[1], 46), "amber")
        cv.poly(leaf(base[0], base[1], (mid[0] + tip[0]) / 2, (mid[1] + tip[1]) / 2, 22), "gold")
    cv.poly(half(R - 120), "bone")
    cv.poly(half(R - 134), "crimsondk")
    n = 18
    for k in range(n):
        a0, a1 = k / n * math.pi, (k + 1) / n * math.pi
        r0, r1 = 180, R - 150
        cv.poly([(cx + math.cos(a0) * r0, cy + math.sin(a0) * r0), (cx + math.cos(a0) * r1, cy + math.sin(a0) * r1),
                 (cx + math.cos(a1) * r1, cy + math.sin(a1) * r1), (cx + math.cos(a1) * r0, cy + math.sin(a1) * r0)],
                "crimson" if k % 2 else "crimsondk")
        am = (a0 + a1) / 2
        cv.poly(leaf(cx + math.cos(am) * 560, cy + math.sin(am) * 560, cx + math.cos(am) * (R - 190), cy + math.sin(am) * (R - 190), 40),
                "amber" if k % 2 else "crimsonlt")
    cv.poly(half(196), "bone")
    cv.poly(half(176), "gold")
    # the raven, rising from the fire with its wings spread over the rays
    M.raven(cv, cx, 420, 560, "soot", "gold", "inklt")
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.3, seed=2905)
    finish("RavenHearthRug", col, hgt, rough, (2048, 1024), backing="bone")


def bat_damask_rug():
    W, H = px(9, 6)
    cv = Canvas(W, H, "plum")
    cv.rect(0, 0, W, H, "bonedk")
    cv.rect(22, 22, W - 22, H - 22, "plum")
    cv.rect(64, 64, W - 64, H - 64, "bonedk")
    cv.rect(78, 78, W - 78, H - 78, "plum")
    for i in range(10):
        x = 78 + (i + 0.5) * (W - 156) / 10
        M.bat(cv, x, 43, 60, "plumlt")
        M.bat(cv, x, H - 43, 60, "plumlt")
    for j in range(6):
        y = 78 + (j + 0.5) * (H - 156) / 6
        cv.poly(foil(43, y, 14, 4), "plumlt")
        cv.poly(foil(W - 43, y, 14, 4), "plumlt")
    # rows of damask flowers, rows of bats flying between them (the bat rows half a step across)
    for j in range(5):
        y = 250 + j * 252
        for i in range(6):
            x = 230 + i * 318
            if j % 2:
                if x + 159 < W - 150:
                    M.bat(cv, x + 159, y, 200, "bonedk", "plumlt", tilt=0.15 * (1 if i % 2 else -1))
            else:
                damask_motif(cv, x, y, 250, "bonedk", "plumlt")
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.85, seed=2906, foundation="cream")
    finish("BatDamaskRugWorn", col, hgt, rough, (2048, 1536), backing="plum")


def doormat(text=True):
    W, H = px(4, 2.4)
    cv = Canvas(W, H, (255, 255, 255))
    b = 54
    cv.d.rectangle([b, b, W - b, H - b], outline=(0, 0, 0), width=26)
    cv.d.rectangle([b + 48, b + 48, W - b - 48, H - b - 48], outline=(0, 0, 0), width=8)
    if text:
        cv.text((W / 2, H / 2 + 60), "Nightmare High", 168, (0, 0, 0))
        M.bat(cv, W / 2, H / 2 - 260, 360, (0, 0, 0))
        for sx in (-1, 1):
            cv.poly(crescent(W / 2 + sx * 640, H / 2 - 270, 60, tilt=0 if sx < 0 else math.pi), (0, 0, 0))
    else:
        cv.poly(shield_pts(W / 2, H / 2, 820), (0, 0, 0))
        cv.poly(shield_pts(W / 2, H / 2, 760), (255, 255, 255))
        key_shape(cv, W / 2, H / 2 + 20, 520, (0, 0, 0), (255, 255, 255))
        for sx in (-1, 1):
            M.bat(cv, W / 2 + sx * 640, H / 2 - 120, 320, (0, 0, 0), tilt=sx * 0.2)
            cv.poly(crescent(W / 2 + sx * 640, H / 2 + 180, 80, tilt=0 if sx < 0 else math.pi), (0, 0, 0))
    col, hgt, rough = coir(cv.array(), seed=2907 + int(text))
    finish("Doormat" if text else "DoormatCrest", col, hgt, rough, (2048, 1024), fringe="bonedk", backing="soot", strength=7.0)


def carpet_damask():
    def draw(cv):
        cv.rect(0, 0, 2048, 2048, "crimsondk")
        for i in range(2):
            for j in range(2):
                damask_motif(cv, 512 + i * 1024, 512 + j * 1024, 820, "crimson", "crimsonlt")
                M.bat(cv, i * 1024, j * 1024, 300, "crimson", "crimsonlt")
    _tile("CarpetDamask", draw, ["crimsondk", "crimson", "crimsonlt"], 2911, "crimsondk")


def carpet_web():
    def draw(cv):
        cv.rect(0, 0, 2048, 2048, "soot")
        for i in range(2):
            for j in range(2):
                M.web(cv, i * 1024 + (512 if j % 2 else 0), j * 1024, 620, (92, 86, 88), 8, spokes=10, rings=9, a0=0.3 * j, dew=(150, 140, 130))
        for (x, y) in ((560, 520), (1500, 1540)):
            M.spider(cv, x, y, 150, "bonedk", "crimsonlt")
        for (x, y) in ((1540, 480), (470, 1560)):
            M.moth(cv, x, y, 240, "bonedk", "plum", "gold", "crimsonlt")
    _tile("CarpetWeb", draw, ["soot", "sootlt", "bonedk", "crimsonlt"], 2912, "soot")


def carpet_harlequin():
    def draw(cv):
        cv.rect(0, 0, 2048, 2048, "soot")
        s = 512
        for i in range(5):
            for j in range(5):
                cv.poly(diamond(i * s + s / 2, j * s + s / 2, s / 2, s / 2), "crimsondk")
        for i in range(9):
            cv.line([(i * 256 - 1024, 0), (i * 256 + 1024, 2048)], "bonedk", 8)
            cv.line([(i * 256 + 1024, 0), (i * 256 - 1024, 2048)], "bonedk", 8)
        for i in range(4):
            for j in range(4):
                M.eye(cv, i * s + s / 2, j * s + s / 2, 150, "bonedk", "gold", "soot", lashes=False)
                cv.poly(star(i * s, j * s, 40, 4), "gold")
    _tile("CarpetHarlequin", draw, ["soot", "crimsondk", "bonedk", "gold"], 2913, "soot")


def carpet_moth():
    def draw(cv):
        cv.rect(0, 0, 2048, 2048, "mossdk")
        for i in range(4):
            for j in range(4):
                x = i * 512 + (256 if j % 2 else 0)
                y = j * 512 + 256
                M.moth(cv, x, y, 360, "mosslt", "moss", "bonedk", "crimsondk")
                cv.poly(star(x + 256, y, 26, 4), "mosslt")
    _tile("CarpetMoth", draw, ["mossdk", "moss", "mosslt", "bonedk"], 2914, "mossdk")




def _border_vine(cv, x0, y0, x1, y1, w, ground, vine, flower, leafc, period=150):
    """A border band from (x0, y0) to (x1, y1) (horizontal or vertical) w wide: a meandering vine with alternate
    trefoil flowers and leaves on a ground colour."""
    horiz = abs(y1 - y0) < abs(x1 - x0)
    L = abs(x1 - x0) if horiz else abs(y1 - y0)
    n = max(2, int(round(L / period)))
    step = L / n
    pts = []
    for i in range(n * 16 + 1):
        t = i / 16
        a = t * step
        off = math.sin(t * math.pi) * w * 0.22
        pts.append((x0 + a, (y0 + y1) / 2 + off) if horiz else ((x0 + x1) / 2 + off, y0 + a))
    cv.line(pts, vine, max(6, w * 0.07))
    for k in range(n):
        a = (k + 0.5) * step
        side = 1 if k % 2 else -1
        if horiz:
            px_, py_ = x0 + a, (y0 + y1) / 2 - side * w * 0.2
            cv.poly(foil(px_, py_, w * 0.2, 3, k=0.5, a0=-math.pi / 2 if side > 0 else math.pi / 2), flower)
            cv.circle(px_, py_, w * 0.06, vine)
            lx = x0 + a - step * 0.5
            cv.poly(leaf(lx, (y0 + y1) / 2, lx + step * 0.22, (y0 + y1) / 2 + side * w * 0.3, w * 0.12), leafc)
        else:
            px_, py_ = (x0 + x1) / 2 - side * w * 0.2, y0 + a
            cv.poly(foil(px_, py_, w * 0.2, 3, k=0.5, a0=0 if side < 0 else math.pi), flower)
            cv.circle(px_, py_, w * 0.06, vine)
            ly = y0 + a - step * 0.5
            cv.poly(leaf((x0 + x1) / 2, ly, (x0 + x1) / 2 + side * w * 0.3, ly + step * 0.22, w * 0.12), leafc)


def _guard(cv, x0, y0, x1, y1, ground, mark, kind="dots", every=40):
    """A narrow guard stripe with dots or reciprocal teeth."""
    cv.rect(x0, y0, x1, y1, ground)
    horiz = (x1 - x0) > (y1 - y0)
    L = (x1 - x0) if horiz else (y1 - y0)
    t = (y1 - y0) if horiz else (x1 - x0)
    n = max(1, int(L / every))
    for k in range(n):
        a = (k + 0.5) * L / n
        if kind == "dots":
            cx, cy = (x0 + a, (y0 + y1) / 2) if horiz else ((x0 + x1) / 2, y0 + a)
            cv.poly(diamond(cx, cy, t * 0.3, t * 0.3), mark)
        else:
            s = L / n
            if horiz:
                cv.poly([(x0 + a - s / 2, y1), (x0 + a, y0), (x0 + a + s / 2, y1)], mark)
            else:
                cv.poly([(x1, y0 + a - s / 2), (x0, y0 + a), (x1, y0 + a + s / 2)], mark)


def _frame_bands(cv, inset, bands):
    """Concentric rectangular bands from the edge in: bands = [(width, fn(x0, y0, x1, y1, w) or colour)]."""
    W, H = cv.w, cv.h
    d = inset
    for w, what in bands:
        if isinstance(what, str):
            cv.rect(d, d, W - d, H - d, what)
        else:
            what(d, w)
        d += w
    return d





def star_chart_rug():
    W = H = 2048
    cv = Canvas(W, H, "soot")
    c = W / 2
    R = W / 2
    oct_ = [(c + math.cos(math.pi / 8 + k * math.pi / 4) * R / math.cos(math.pi / 8), c + math.sin(math.pi / 8 + k * math.pi / 4) * R / math.cos(math.pi / 8)) for k in range(8)]
    def octo(r):
        return [(c + math.cos(math.pi / 8 + k * math.pi / 4) * r / math.cos(math.pi / 8), c + math.sin(math.pi / 8 + k * math.pi / 4) * r / math.cos(math.pi / 8)) for k in range(8)]
    cv.poly(octo(R - 2), "bone")
    cv.poly(octo(R - 18), "crimsondk")
    # an arcade of trefoil-headed arches round the border
    r_in = R - 170
    for k in range(8):
        a0, a1 = math.pi / 8 + k * math.pi / 4, math.pi / 8 + (k + 1) * math.pi / 4
        p0 = (c + math.cos(a0) * (R - 18) / math.cos(math.pi / 8), c + math.sin(a0) * (R - 18) / math.cos(math.pi / 8))
        p1 = (c + math.cos(a1) * (R - 18) / math.cos(math.pi / 8), c + math.sin(a1) * (R - 18) / math.cos(math.pi / 8))
        ex, ey = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(ex, ey)
        ux, uy = ex / L, ey / L
        nx, ny = -uy, ux
        if (c - p0[0]) * nx + (c - p0[1]) * ny < 0:
            nx, ny = -nx, -ny
        m = 7
        for i in range(m):
            t = (i + 0.5) / m
            bx, by = p0[0] + ex * t + nx * 40, p0[1] + ey * t + ny * 40
            w = L / m * 0.36
            arch = [(bx - ux * w, by - uy * w), (bx + ux * w, by + uy * w)]
            top = [(bx + ux * w * math.cos(s * math.pi) + nx * (70 + w * 0.9 * math.sin(s * math.pi)), by + uy * w * math.cos(s * math.pi) + ny * (70 + w * 0.9 * math.sin(s * math.pi)))
                   for s in [j / 12 for j in range(13)]]
            cv.poly(arch + top, "bone")
            cv.poly(foil(bx + nx * 70, by + ny * 70, w * 0.55, 3, a0=math.atan2(ny, nx)), "crimson")
    cv.poly(octo(r_in + 14), "gold")
    cv.poly(octo(r_in), "ink")
    # the sky: stars, constellation lines and a ring of moon phases round a great crescent
    rng = np.random.default_rng(2904)
    for _ in range(260):
        a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(0, r_in - 30) ** 1.0
        x, y = c + math.cos(a) * rr, c + math.sin(a) * rr
        cv.circle(x, y, rng.choice([4, 5, 7]), "bonedk" if rng.random() < 0.7 else "bone")
    for k in range(5):
        a0 = k / 5 * 2 * math.pi + 0.4
        pts = []
        for j in range(5):
            a = a0 + rng.uniform(-0.25, 0.25)
            rr = rng.uniform(r_in * 0.62, r_in * 0.9)
            pts.append((c + math.cos(a + j * 0.09) * rr, c + math.sin(a + j * 0.09) * rr))
        cv.line(pts, "bonedk", 6)
        for x, y in pts:
            cv.poly(star(x, y, 22, 4), "gold")
    rp = r_in * 0.48
    cv.ring(c, c, rp, 8, "bonedk")
    for k in range(8):
        a = k / 8 * 2 * math.pi - math.pi / 2
        x, y = c + math.cos(a) * rp, c + math.sin(a) * rp
        # the phases round the ring: new (k = 0), waxing, full (k = 4), waning; the shadow is a disc slid off the moon
        cv.circle(x, y, 52, "bone" if k else "inklt")
        if k not in (0, 4):
            off = 104 * (k / 4 if k < 4 else (8 - k) / 4)
            cv.circle(x + (-off if k < 4 else off), y, 50, "ink")
        cv.ring(x, y, 54, 6, "gold")
    cv.circle(c, c, 230, "inklt")
    cv.poly(crescent(c, c, 200, tilt=math.pi * 0.2, shift=0.36), "gold")
    cv.poly(star(c + 70, c - 30, 40, 4), "bone")
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=3, worn=0.2, seed=2904)
    finish("StarChartRug", col, hgt, rough, (2048, 2048), backing="bone")





def bath_mat():
    W, H = px(3.2, 2.0)
    cv = Canvas(W, H, "cream")
    for k in range(6):
        y = 120 + k * 46
        cv.rect(0, y, W, y + 22, "navy" if k % 2 == 0 else "cream")
        cv.rect(0, H - y - 22, W, H - y, "navy" if k % 2 == 0 else "cream")
    crest(cv, W / 2, H / 2, 440, field="crimson", rim="navy", charge="cream")
    col, hgt, rough = loops(cv.array(), seed=2908)
    finish("BathMat", col, hgt, rough, (2048, 1280), fringe="cream", backing="cream", strength=4.0)


# ------------------------------------------------------------------ carpet tiles (seamless, 8 x 8 studs each)

def _tile(name, draw, pal, seed, backing):
    cv = Canvas(2048, 2048, pal[0], seamless=True)
    draw(cv)
    col, hgt, rough = pile(cv.array(), cv.palette(), knot=4, worn=0.0, seed=seed, abrash=0.025)
    finish(name, col, hgt, rough, (2048, 2048), backing=backing, band=True)






# ------------------------------------------------------------------ the upholstery sets (seamless, neutral, tinted in Blender)

def _fabric(name, lum, rough, hgt, strength=3.0):
    n = height_to_normal(hgt, strength)
    save(name, np.dstack([lum] * 3), n, rough, None, folder=FAB)


def fab_velvet():
    N = 1024
    crush = fbm(N, N, 90, 4, 3101)
    fine = pnoise(N, N, 0.7, 3102)
    lum = 0.8 + 0.2 * smooth(0.35, 0.75, crush) + 0.04 * (fine - 0.5)
    _fabric("NH_Velvet", lum, 0.88 - 0.08 * crush, 0.4 * crush + 0.6 * fine, 1.5)


def _damask_tile(draw):
    cv = Canvas(1024, 1024, (0, 0, 0), seamless=True)
    draw(cv)
    m = cv.array()[..., 0]
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    yy, xx = np.mgrid[0:1024, 0:1024].astype(np.float32)
    satin = 0.5 + 0.5 * np.sin((xx + yy * 3) * math.pi / 2.5)      # warp-faced satin shine on the figure
    twill = 0.5 + 0.5 * np.sin((xx * 2 - yy) * math.pi / 3.0)      # the ground's twill
    fine = pnoise(1024, 1024, 0.7, 3103)
    lum = 0.74 + 0.22 * m + 0.03 * (fine - 0.5)
    rough = 0.82 - 0.36 * m
    hgt = m * 0.5 + 0.25 * (satin * m + twill * (1 - m)) + 0.1 * fine
    return lum, rough, hgt


def fab_damask():
    def draw(cv):
        damask_motif(cv, 256, 256, 420, (255, 255, 255))
        damask_motif(cv, 768, 768, 420, (255, 255, 255))
        cv.poly(foil(768, 256, 60, 4), (255, 255, 255))
        cv.poly(foil(256, 768, 60, 4), (255, 255, 255))
    _fabric("NH_Damask", *_damask_tile(draw), 2.5)


def fab_damask_bat():
    def draw(cv):
        M.bat(cv, 256, 300, 400, (255, 255, 255))
        M.bat(cv, 768, 812, 400, (255, 255, 255))
        cv.poly(crescent(768, 290, 70, tilt=0.4), (255, 255, 255))
        cv.poly(crescent(256, 800, 70, tilt=0.4), (255, 255, 255))
    _fabric("NH_DamaskBat", *_damask_tile(draw), 2.5)


def fab_damask_fleur():
    def draw(cv):
        for i in range(2):
            for j in range(2):
                x, y = 256 + i * 512, 256 + j * 512
                cv.poly(foil(x, y, 150, 4, k=0.5), (255, 255, 255))
                cv.poly(foil(x, y, 90, 4, k=0.5), (0, 0, 0))
                cv.poly(star(x, y, 50, 4), (255, 255, 255))
                cv.poly(star(i * 512, j * 512, 70, 4, 0.3), (255, 255, 255))
    _fabric("NH_DamaskFleur", *_damask_tile(draw), 2.5)


def fab_stripe():
    """A regency stripe, already coloured (tint it white): crimson satin, a gilt pinstripe, ink ground."""
    N = 1024
    xx = np.mgrid[0:N, 0:N][1].astype(np.float32)
    u = (xx % 256) / 256
    cr = np.array(C["crimson"], np.float32) / 255
    ink = np.array(C["ink"], np.float32) / 255
    gold = np.array(C["gold"], np.float32) / 255
    col = np.zeros((N, N, 3), np.float32)
    band = (u < 0.42)[..., None]
    pin = ((np.abs(u - 0.5) < 0.02) | (np.abs(u - 0.92) < 0.02))[..., None]
    col[:] = ink
    col = np.where(band, cr * 1.6, col)
    col = np.where(pin, gold * 1.1, col)
    fine = pnoise(N, N, 0.7, 3104)
    col = col * (0.95 + 0.08 * fine[..., None])
    sat = 0.5 + 0.5 * np.sin(np.mgrid[0:N, 0:N][0] * math.pi / 2.5)
    rough = np.where(band[..., 0], 0.45, 0.8) - 0.1 * pin[..., 0]
    hgt = 0.4 * sat * band[..., 0] + 0.2 * fine
    save("NH_Stripe", col, height_to_normal(hgt, 2.0), rough, None, folder=FAB)


def fab_tapestry():
    """A small tapestry weave for cushions (coloured): millefleur sprigs on ink, woven ribs."""
    cv = Canvas(1024, 1024, "ink", seamless=True)
    rng = np.random.default_rng(3105)
    for _ in range(46):
        x, y = rng.uniform(0, 1024), rng.uniform(0, 1024)
        c = ["crimsonlt", "bone", "gold", "rose"][rng.integers(0, 4)]
        cv.line([(x, y + 40), (x, y)], "moss", 7)
        cv.poly(leaf(x, y + 30, x - 30, y + 10, 14), "mosslt")
        cv.poly(leaf(x, y + 30, x + 30, y + 14, 14), "mosslt")
        cv.poly(foil(x, y - 6, 22, 5, k=0.5), c)
        cv.circle(x, y - 6, 6, "gold")
    col = cv.array()
    yy = np.mgrid[0:1024, 0:1024][0].astype(np.float32)
    rib = np.sin((yy % 6) / 6 * math.pi) ** 0.7
    fine = pnoise(1024, 1024, 0.7, 3106)
    col = col * (0.82 + 0.2 * rib[..., None]) * (0.96 + 0.08 * fine[..., None])
    save("NH_TapestryWeave", col, height_to_normal(rib * 0.7 + 0.3 * fine, 3.0), np.full((1024, 1024), 0.9, np.float32), None, folder=FAB)


JOBS = {
    "MothMedallionRug": moth_medallion_rug, "WatchingRunner": watching_runner, "ThornRoseRug": thorn_rose_rug,
    "StarChartRug": star_chart_rug, "RavenHearthRug": raven_hearth_rug, "BatDamaskRugWorn": bat_damask_rug,
    "Doormat": lambda: doormat(True), "DoormatCrest": lambda: doormat(False), "BathMat": bath_mat,
    "CarpetDamask": carpet_damask, "CarpetWeb": carpet_web, "CarpetHarlequin": carpet_harlequin, "CarpetMoth": carpet_moth,
    "fabrics": lambda: [f() for f in (fab_velvet, fab_damask, fab_damask_bat, fab_stripe, fab_tapestry)],
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    for n in names:
        JOBS[n]()
