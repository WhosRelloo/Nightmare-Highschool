"""Extra drawing helpers for the civilian and transformation sets."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from nhcloth import *  # noqa: F401,F403
from shirts_new import lines, poly, dash, button, rib_band, polo_hole, SLEEVE_END

YY, XX = np.mgrid[0:H, 0:W]
CX = 294.5
LEGS = ARM_FACES
FRONTS = ["RA_F", "LA_F"]
BACKS = ["RA_B", "LA_B"]
OUTERS = ["RA_R", "LA_L"]
INNERS = ["RA_L", "LA_R"]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dark(col, f):
    return tuple(int(v * f) for v in col)


# ---------------------------------------------------------------- patterns
def plaid(sett, seed=0, cloud=0.06, soft=0.0):
    seq = []
    for col, n in list(sett) + list(sett)[::-1]:
        seq += [col] * n
    seq = np.array(seq, np.float32)
    warp = seq[XX % len(seq)]
    weft = seq[YY % len(seq)]
    tw = ((XX + YY) % 4) < 2
    col = np.where(tw[..., None], warp, weft) * 0.7 + (warp + weft) / 2 * 0.3
    if soft:
        col = ndimage.gaussian_filter(col, (soft, soft, 0))
    d = fabric_detail(seed, cloud=cloud, twill=0.0, grain=0.03)
    return np.clip(col * d[..., None], 0, 255)


_DAMASK = None


def damask_mask(tile=16):
    """Repeating quatrefoil-and-diamond brocade motif (1 where the motif is)."""
    global _DAMASK
    if _DAMASK is None:
        t = Image.new("L", (tile, tile), 0)
        d = ImageDraw.Draw(t)
        c = tile / 2
        for dx, dy in ((0, -3.5), (0, 3.5), (-3.5, 0), (3.5, 0)):
            d.ellipse((c + dx - 2.2, c + dy - 2.2, c + dx + 2.2, c + dy + 2.2), outline=255)
        d.polygon([(c, c - 1.5), (c + 1.5, c), (c, c + 1.5), (c - 1.5, c)], fill=255)
        for x, y in ((0, 0), (tile, 0), (0, tile), (tile, tile)):
            d.point((min(x, tile - 1), min(y, tile - 1)), fill=255)
        a = np.array(t, np.float32) / 255
        big = np.tile(a, (H // tile + 2, W // tile + 2))
        stag = np.roll(big, tile // 2, 1)
        rows = (np.arange(big.shape[0]) // tile) % 2 == 1
        big[rows] = stag[rows]
        _DAMASK = big[:H, :W]
    return _DAMASK


def damask(c, mask, factor=1.35):
    m = damask_mask() * mask
    c[..., :3] = np.clip(c[..., :3] * (1 + (factor - 1) * m[..., None]), 0, 255)
    return c


def sheen(c, names, amount=0.2, at=0.42, width=0.22, y_max=H):
    for n in names:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * at)) / (w * width)) ** 2) * (rect_mask([n]) & (YY < y_max)) * (c[..., 3] > 0)
        c[..., :3] = np.clip(c[..., :3] * (1 + amount * g[..., None]) + 10 * amount * g[..., None], 0, 255)
    return c


# ---------------------------------------------------------------- fur
def fur(dark_col, light_col, seed, angle=90, spread=14, length=(6, 12), density=0.12, mottle=0.5):
    """Hand-drawn fur: strokes in clumps, dark at the root and light at the tip,
    with a slowly turning direction so it reads as locks of hair."""
    rng = np.random.default_rng(seed)
    S2 = 2
    base = Image.new("RGB", (W * S2, H * S2), dark(dark_col, 0.7))
    d = ImageDraw.Draw(base)
    n = int(W * H * density)
    xs = rng.uniform(-4, W + 4, n)
    ys = rng.uniform(-10, H + 4, n)
    order = np.argsort(ys)
    clump = noise(H, W, seed + 3, 3.2)
    turn = noise(H, W, seed + 4, 14)
    for i in order:
        x, y = xs[i], ys[i]
        yi, xi = int(min(max(y, 0), H - 1)), int(min(max(x, 0), W - 1))
        t = float(np.clip(0.5 + 0.3 * mottle * clump[yi, xi] + 0.22 * (rng.random() - 0.5), 0, 1))
        a = np.deg2rad(angle + 22 * turn[yi, xi] + rng.normal(0, spread / 2))
        L = rng.uniform(*length)
        mx, my = x + np.cos(a) * L * 0.5, y + np.sin(a) * L * 0.5
        ex, ey = x + np.cos(a) * L, y + np.sin(a) * L
        d.line([(x * S2, y * S2), (mx * S2, my * S2)], fill=lerp(dark_col, light_col, max(0.0, t - 0.3)), width=S2)
        d.line([(mx * S2, my * S2), (ex * S2, ey * S2)], fill=lerp(dark_col, light_col, t), width=S2 - 1 or 1)
    return np.array(base.resize((W, H), Image.BOX), np.float32)


def claws(c, names, y_tip, n=4, length=9, col=(214, 204, 180), up=False):
    for nm in names:
        x, y, w, h = R[nm]
        step = w / (n + 1)
        for i in range(1, n + 1):
            cx = x + step * i
            if up:
                pts = [(cx - 2.5, y_tip + length), (cx + 2.5, y_tip + length), (cx + 0.5, y_tip)]
            else:
                pts = [(cx - 2.5, y_tip - length), (cx + 2.5, y_tip - length), (cx + 0.5, y_tip)]
            m = poly(pts)
            paint(c, ndimage.binary_dilation(m > 0.5, iterations=1).astype(np.float32), (14, 10, 8))
            paint(c, m, col)
            paint(c, lines([pts[0], pts[2]]), lerp(col, (255, 255, 255), 0.5))
    return c


# ---------------------------------------------------------------- edges
def ragged_y(base, amp, seed, notches=0.06, depth=(5, 12), smooth=3):
    """A torn edge: y position for every x column."""
    rng = np.random.default_rng(seed)
    wob = ndimage.gaussian_filter1d(rng.standard_normal(W), smooth)
    wob = wob / (np.abs(wob).max() + 1e-6)
    y = base + amp * wob
    x = 0
    while x < W:
        if rng.random() < notches:
            dpt = rng.uniform(*depth)
            wdt = rng.integers(3, 8)
            for k in range(-wdt, wdt + 1):
                if 0 <= x + k < W:
                    y[x + k] += dpt * (1 - abs(k) / (wdt + 1))
            x += wdt * 2
        x += 1
    return y


def torn_edge(c, region, edge_y, below_fill=None, fray=(232, 226, 210), seed=0, up=False):
    """Cut a garment along edge_y[x]; below (or above, if up) becomes below_fill or transparent."""
    e = edge_y[XX]
    cut = region & ((YY < e) if up else (YY > e))
    keep = region & ~cut
    if below_fill is None:
        clear(c, cut)
    else:
        c[cut, :3] = below_fill[cut]
        c[cut, 3] = 255
    rim = keep & (np.abs(YY - e) < 1.2)
    shade(c, rim.astype(np.float32), 0.45)
    rng = np.random.default_rng(seed)
    threads = keep & (np.abs(YY - e) < 3) & (rng.random((H, W)) < 0.12)
    c[threads, :3] = fray
    return c


def blob_holes(region, seed, thresh=1.4, sigma=4.5):
    n = noise(H, W, seed, sigma)
    return region & (n > thresh)


def glow(c, mask, color, sigma=3, strength=1.0, core=True):
    m = np.clip(mask.astype(np.float32), 0, 1)
    halo = ndimage.gaussian_filter(m, sigma)
    halo = halo / (halo.max() + 1e-6)
    vis = c[..., 3] > 0
    add = (np.array(color, np.float32) * strength) * halo[..., None] * vis[..., None]
    c[..., :3] = np.clip(c[..., :3] + add, 0, 255)
    if core:
        paint(c, m, lerp(color, (255, 255, 255), 0.45))
    return c


def chain(c, pts, col=GOLD, step=3.2):
    """Small alternating links along a polyline, with a soft shadow."""
    path = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = np.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / step))
        for i in range(k):
            t = i / k
            path.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    def links(grow):
        def fn(d):
            for i, (x, y) in enumerate(path):
                rx, ry = (1.6, 1.0) if i % 2 else (1.0, 1.6)
                d.ellipse((x - rx - grow, y - ry - grow, x + rx + grow, y + ry + grow), outline=255)
        return shape(fn)
    outer = links(0.8)
    lift(c, outer, strength=0.4)
    paint(c, outer, (14, 10, 8), 0.8)
    paint(c, links(0), col)
    return c


def stitches(c, pts, col=(20, 12, 10), cross=(236, 228, 210), every=4):
    paint(c, lines(pts, 1), col)
    for a, b in zip(pts[:-1], pts[1:]):
        L = np.hypot(b[0] - a[0], b[1] - a[1])
        nx, ny = -(b[1] - a[1]) / max(L, 1), (b[0] - a[0]) / max(L, 1)
        for i in range(1, int(L / every)):
            t = i * every / L
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            paint(c, lines([(x - nx * 2.5, y - ny * 2.5), (x + nx * 2.5, y + ny * 2.5)]), cross)
    return c


# ---------------------------------------------------------------- shapes
def arc_text(c, word, cx, cy, rad, span, size, col, stroke_col=None, distress=None):
    f = font(size)
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        ang = np.deg2rad(-span / 2 + span * i / max(1, len(word) - 1))
        x = cx + rad * np.sin(ang)
        y = cy - rad * np.cos(ang)
        layers = []
        if stroke_col is not None:
            layers.append((2, stroke_col))
        layers.append((0, col))
        for sw, lc in layers:
            t = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(t).text((size, size), ch, font=f, fill=255, anchor="mm", stroke_width=sw, stroke_fill=255)
            r = np.array(t.rotate(-np.rad2deg(ang), resample=Image.BICUBIC), np.float32) / 255
            m = np.zeros((H, W), np.float32)
            y0, x0 = int(y) - size, int(x) - size
            m[y0:y0 + size * 2, x0:x0 + size * 2] = r
            if distress is not None:
                m *= distress
            paint(c, m, lc)
    return c


def distress_mask(seed, keep=0.78):
    n = noise(H, W, seed, 1.1)
    return (n > -1.6 + (1 - keep) * 2.5).astype(np.float32)


def crescent(cx, cy, r, off, ang=-35):
    a = np.deg2rad(ang)
    ox, oy = off * np.cos(a), off * np.sin(a)
    outer = shape(lambda d: d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255))
    inner = shape(lambda d: d.ellipse((cx + ox - r * 0.86, cy + oy - r * 0.86, cx + ox + r * 0.86, cy + oy + r * 0.86), fill=255))
    return np.clip(outer - inner, 0, 1)


def bat(cx, cy, w):
    s = w / 1.0
    right = [(0.06, -0.08), (0.18, -0.2), (0.34, -0.24), (0.5, -0.12), (0.42, 0.0), (0.36, -0.03),
             (0.3, 0.07), (0.23, 0.01), (0.16, 0.11), (0.09, 0.04), (0.04, 0.16)]
    head = [(0.0, -0.06), (0.03, -0.17), (0.045, -0.08)]
    pts = [(-x, y) for x, y in head[::-1]] + [(x, y) for x, y in head] + right + [(0, 0.2)] + [(-x, y) for x, y in right[::-1]]
    return poly([(cx + x * s, cy + y * s) for x, y in pts])


def skull(c, cx, cy, s=1.0, bone=(226, 218, 196), ink=(20, 16, 18), distress=None):
    def m(fn):
        r = shape(fn)
        return r * distress if distress is not None else r
    E = lambda b: (cx + b[0] * s, cy + b[1] * s, cx + b[2] * s, cy + b[3] * s)
    head = m(lambda d: (d.ellipse(E((-15, -18, 15, 9)), fill=255), d.rounded_rectangle(E((-10, 2, 10, 15)), 3, fill=255)))
    paint(c, ndimage.binary_dilation(head > 0.5, iterations=1).astype(np.float32), ink)
    paint(c, head, bone)
    paint(c, m(lambda d: (d.ellipse(E((-11, -6, -2, 3)), fill=255), d.ellipse(E((2, -6, 11, 3)), fill=255))), ink)
    paint(c, m(lambda d: d.polygon([(cx - 2 * s, cy + 6 * s), (cx + 2 * s, cy + 6 * s), (cx, cy + 2 * s)], fill=255)), ink)
    paint(c, m(lambda d: [d.line([(cx + k * s, cy + 9 * s), (cx + k * s, cy + 14 * s)], fill=255) for k in (-6, -3, 0, 3, 6)]), ink)
    paint(c, m(lambda d: d.line([(cx - 9 * s, cy + 11 * s), (cx + 9 * s, cy + 11 * s)], fill=255)), ink)
    return c


def cross(c, cx, cy, w, h, bar, col=GOLD, edge=(60, 40, 14), fill=None):
    def fn(inset):
        def f(d):
            d.rectangle((cx - bar / 2 + inset, cy - h / 2 + inset, cx + bar / 2 - inset, cy + h / 2 - inset), fill=255)
            d.rectangle((cx - w / 2 + inset, cy - h * 0.22 - bar / 2 + inset, cx + w / 2 - inset, cy - h * 0.22 + bar / 2 - inset), fill=255)
        return shape(f)
    lift(c, fn(-1))
    paint(c, fn(-1), edge)
    paint(c, fn(0), col)
    if fill:
        paint(c, fn(1.5), fill)
    return c


def jabot(c, cx, top, n=5, col=IVORY):
    whole = shape(lambda d: [d.ellipse((cx - 6 - i * 1.3, top + i * 6 - 3, cx + 6 + i * 1.3, top + i * 6 + 5), fill=255) for i in range(n)])
    lift(c, whole, strength=0.5, sigma=1.3)
    for i in reversed(range(n)):
        y = top + i * 6
        w = 6 + i * 1.3
        m = shape(lambda d: d.ellipse((cx - w, y - 3, cx + w, y + 5), fill=255))
        paint(c, m, col)
        edge = shape(lambda d: d.arc((cx - w, y - 3, cx + w, y + 5), 10, 170, fill=255))
        paint(c, edge, dark(col, 0.55))
    return c


def brooch(c, cx, cy, gem=(170, 10, 24)):
    lift(c, shape(lambda d: d.ellipse((cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5), fill=255)))
    paint(c, shape(lambda d: d.ellipse((cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5), fill=255)), (20, 12, 8))
    paint(c, shape(lambda d: d.ellipse((cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5), fill=255)), GOLD)
    paint(c, shape(lambda d: d.ellipse((cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2), fill=255)), gem)
    paint(c, shape(lambda d: d.point((cx - 1, cy - 1), fill=255)), (255, 200, 200))
    return c


# ---------------------------------------------------------------- footwear
def combat_boots(c, top, seed=3, leather=(30, 26, 26), laces=CRIMSON, sole_top=474):
    m = rect_mask(LEGS) & (YY >= top)
    d = fabric_detail(seed, cloud=0.07, twill=0, grain=0.03)
    c[m, :3] = tint(d, leather, 10)[m]
    c[m, 3] = 255
    sheen(c, LEGS, 0.25, at=0.5, width=0.3, y_max=sole_top)
    collar = rect_mask(LEGS) & (YY >= top) & (YY <= top + 3)
    c[collar, :3] = np.clip(c[collar, :3] * 1.35 + 8, 0, 255)
    shade(c, (rect_mask(LEGS) & ((YY == top) | (YY == top + 4))).astype(np.float32), 0.4)
    for n in FRONTS:
        x, y, w, h = R[n]
        mx = x + w / 2
        tongue = (XX >= mx - 7) & (XX <= mx + 7) & (YY >= top + 4) & (YY <= 466)
        c[tongue, :3] = np.clip(c[tongue, :3] * 0.8, 0, 255)
        for ly in range(top + 6, 464, 4):
            paint(c, lines([(mx - 6, ly), (mx + 6, ly + 3)]) + lines([(mx + 6, ly), (mx - 6, ly + 3)]), laces)
            for ex in (mx - 7, mx + 7):
                paint(c, shape(lambda d: d.point((ex, ly), fill=255)), GOLD)
        paint(c, dash([(x + 3, 467), (mx, 464), (x + w - 3, 467)], on=2, off=1), dark(leather, 2.2))
    for n in OUTERS:
        x, y, w, h = R[n]
        sy = top + 10
        strap = rect_mask([n]) & (YY >= sy) & (YY <= sy + 3)
        c[strap, :3] = np.clip(c[strap, :3] * 0.7, 0, 255)
        bx = x + w * 0.6
        paint(c, shape(lambda d: d.rectangle((bx - 3, sy - 1, bx + 3, sy + 4), outline=255)), GOLD)
    sole = rect_mask(LEGS) & (YY >= sole_top)
    c[sole, :3] = (16, 14, 14)
    c[rect_mask(LEGS) & (YY == sole_top), :3] = (70, 64, 60)
    for n in LEGS:
        x, y, w, h = R[n]
        for tx in range(x + 2, x + w, 4):
            c[(YY >= 479) & (YY <= 482) & (XX == tx) & rect_mask([n]), :3] = (52, 48, 46)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = (18, 16, 16)
    c[dn, 3] = 255
    for n in ARM_DOWNS:
        x, y, w, h = R[n]
        for by in range(y + 4, y + h - 4, 9):
            for bx in range(x + 4, x + w - 4, 10):
                c[(YY >= by) & (YY < by + 5) & (XX >= bx) & (XX < bx + 7), :3] = (40, 36, 34)
    return c


def riding_boots(c, top, cuff=(110, 10, 20), seed=4, leather=(16, 14, 18)):
    m = rect_mask(LEGS) & (YY >= top)
    d = fabric_detail(seed, cloud=0.05, twill=0, grain=0.015)
    c[m, :3] = tint(d, leather, 8)[m]
    c[m, 3] = 255
    for n in LEGS:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * 0.38)) / (w * 0.12)) ** 2) * (rect_mask([n]) & (YY >= top) & (YY < 476))
        c[..., :3] = np.clip(c[..., :3] + 70 * g[..., None], 0, 255)
    band = rect_mask(LEGS) & (YY >= top) & (YY <= top + 6)
    c[band, :3] = tint(fabric_detail(seed + 1, cloud=0.05, twill=0), cuff, 8)[band]
    shade(c, (rect_mask(LEGS) & ((YY == top) | (YY == top + 7))).astype(np.float32), 0.35)
    for n in OUTERS:
        x, y, w, h = R[n]
        sy = top + 16
        strap = rect_mask([n]) & (YY >= sy) & (YY <= sy + 2)
        c[strap, :3] = dark(cuff, 0.8)
        bx = x + w * 0.62
        paint(c, shape(lambda d: d.rectangle((bx - 3, sy - 2, bx + 3, sy + 4), outline=255)), GOLD)
    sole = rect_mask(LEGS) & (YY >= 478)
    c[sole, :3] = (34, 22, 16)
    shade(c, (rect_mask(LEGS) & (YY == 477)).astype(np.float32), 0.4)
    for n in BACKS:
        heel = rect_mask([n]) & (YY >= 474)
        c[heel, :3] = (30, 20, 14)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = tint(fabric_detail(seed + 2, cloud=0.08, twill=0), (36, 24, 18), 6)[dn]
    c[dn, 3] = 255
    for n in ARM_DOWNS:
        x, y, w, h = R[n]
        paint(c, lines([(x, y + 42), (x + w, y + 42)], 2), (14, 10, 8))
    return c


def jeans_sneakers(c):
    J = load("pants_jeans_a.png")
    m = (rect_mask(LEGS) & (YY >= 451)) | rect_mask(ARM_DOWNS)
    c[m] = J[m]
    return c


def pants_shell(seed=0):
    """Opaque black margin and the see-through panel, as in the jeans."""
    c = blank((0, 0, 0), 255)
    hole = load("pants_jeans_a.png")[..., 3] == 0
    return c, hole
