"""Racial-grip finisher VFX textures for Nightmare Highschool (numpy + Pillow + scipy, no Blender, offline).

usage:  python make_grip_sprites.py                 render everything, then the contact sheet
        python make_grip_sprites.py claw_slash ash  render only these (names below, with or without "grip_")
        python make_grip_sprites.py --sheet         rebuild previews/contact_sheet.png from the files on disk
        python make_grip_sprites.py --list          list the names

Style (docs/VFX-Design-Bible.md): soft edges, every sprite fades to zero alpha before its cell edge, white art is
tinted in Roblox (Color), the dark ink / shadow art bakes a near-black RGB. Fields are drawn at 2x and box-filtered
down. Beam textures run along the image's VERTICAL axis, tile seamlessly along it (integer frequencies and FFT noise
only) and have alpha exactly zero at both side edges. Every seed is fixed, so re-renders are byte-stable.
No blood or gore anywhere (moderation rule): no red liquid, droplets, splatter, wounds or flesh.

  grip_priest_runes.png       1024      holy floor seal: rings, invented liturgical glyph band, cross star, filigree
  grip_lifethread_v.png       256x1024  Beam: braided luminous life thread (strands + soft core)
  grip_ink_smoke_4x4.png      1024      Flipbook 4x4: boiling black ink-smoke puff (baked near-black)
  grip_ink_tendril_v.png      256x1024  Beam: thorned, wispy clawing ink tendril (baked near-black)
  grip_claw_slash.png         1024      three curved claw-rake slash smears (hot core, glow, motion smear)
  grip_slash_spark_2x2.png    512       Flipbook 2x2: silver impact spark popping and fading
  grip_frost_floor.png        1024      frost bloom of branching ice dendrites, seen from above
  grip_grave_cracks.png       1024      radial cracked-stone decal, dark grey-black (baked)
  grip_grave_cracks_glow.png  1024      the crack channels as a white mask, for a green glow overlay
  grip_ash_4x4.png            1024      Flipbook 4x4: an ash flake cluster crumbling into drifting flecks
  grip_gold_dust_2x2.png      512       Flipbook 2x2: twinkling holy motes with 4-point glints
  grip_soul_streak_v.png      256x1024  Beam: spectral spiral streak with abstract ghostly smears
  grip_shockwave.png          1024      soft dust/air ground ring (thick leading edge, wispy trail)
  grip_moon_halo.png          1024      pale full moon with soft craters, halo and faint rays (baked cool white)
  grip_demon_shape.png        1024      abstract shadow-demon silhouette torn upward into smoke (baked near-black)
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(HERE, "previews")
TAU = math.tau

# =================================================================== helpers


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def pnoise(h, w, beta=1.0, seed=0, aniso=(1.0, 1.0), hi=None, lo=None):
    """Periodic (tileable on both axes) 1/f^beta noise, zero mean, unit std. Frequencies in cycles per tile.
    aniso=(ax, ay) weights the x / y frequencies: ay > 1 stretches features along y."""
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft2(rng.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.rfftfreq(w)[None, :] * w
    f = np.sqrt((fx * aniso[0]) ** 2 + (fy * aniso[1]) ** 2)
    f[0, 0] = 1.0
    amp = f ** (-beta)
    amp[0, 0] = 0.0
    if hi:
        amp *= np.exp(-((f / hi) ** 2))
    if lo:
        amp *= sstep(lo * 0.5, lo, f)
    n = np.fft.irfft2(spec * amp, s=(h, w))
    return (n - n.mean()) / (n.std() + 1e-12)


def samp(field, rows, cols, order=1):
    """sample a periodic field at fractional (row, col) pixel coordinates, wrapping."""
    rows, cols = np.broadcast_arrays(rows, cols)
    return ndimage.map_coordinates(field, [rows, cols], order=order, mode="grid-wrap")


def down(a, f):
    """box-filter downsample by an integer factor (works for HxW and HxWxC)."""
    if f == 1:
        return a
    h, w = a.shape[:2]
    return a.reshape(h // f, f, w // f, f, *a.shape[2:]).mean(axis=(1, 3))


def grid(n, m=None):
    """pixel-centre coordinates in [-1, 1]: returns (x, y) arrays shaped (m, n)."""
    m = m or n
    y, x = np.mgrid[0:m, 0:n].astype(np.float64)
    return (x + 0.5) / n * 2 - 1, (y + 0.5) / m * 2 - 1


def blur(a, s, wrap_rows=False):
    if s <= 0:
        return a
    mode = ("wrap", "constant") if wrap_rows else "constant"
    return ndimage.gaussian_filter(a, s, mode=mode)


def over(dst_c, dst_a, src_c, src_a):
    """premultiplied-free 'over' compositing for straight colour layers. c: HxWx3, a: HxW."""
    out_a = src_a + dst_a * (1 - src_a)
    num = src_c * src_a[..., None] + dst_c * (dst_a * (1 - src_a))[..., None]
    out_c = np.where(out_a[..., None] > 1e-4, num / np.maximum(out_a, 1e-6)[..., None], src_c)
    return np.clip(out_c, 0, 1), out_a


def catmull(pts, n_per=24):
    """Catmull-Rom spline through control points -> dense polyline (Nx2)."""
    p = np.asarray(pts, float)
    p = np.vstack([p[0] * 2 - p[1], p, p[-1] * 2 - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n_per):
            t = k / n_per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def stroke(d, pts, w0, w1=None, fill=255, power=1.0):
    """stamp a smooth tapered stroke (diameter w0 -> w1) along a polyline onto an ImageDraw."""
    pts = np.asarray(pts, float)
    w1 = w0 if w1 is None else w1
    seg = np.hypot(*np.diff(pts, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1]
    if L <= 0:
        return
    s = 0.0
    while s <= L:
        t = s / L
        w = w0 + (w1 - w0) * (t ** power)
        x = np.interp(s, cum, pts[:, 0])
        y = np.interp(s, cum, pts[:, 1])
        r = max(w / 2, 0.5)
        f = fill(t) if callable(fill) else fill
        d.ellipse((x - r, y - r, x + r, y + r), fill=int(f))
        s += max(0.5, 0.28 * w)


def L2f(img):
    return np.asarray(img, dtype=np.float64) / 255.0


def cell_fade(n, r0=0.80, r1=0.96):
    """radial fade inside a square cell: 1 inside r0, 0 beyond r1 (r = 1 at the cell edge midpoints)."""
    x, y = grid(n)
    return sstep(r1, r0, np.hypot(x, y))


def edge_fade(n, m=None, margin=0.03):
    """box fade: zero at the image border, 1 beyond `margin` (fraction of size)."""
    x, y = grid(n, m)
    d = np.minimum(1 - np.abs(x), 1 - np.abs(y)) / 2
    return sstep(0.0, margin, d)


def assemble(cells, g):
    """list of g*g (rgb, a) cells -> one sheet (rgb, a)."""
    c = cells[0][1].shape[0]
    rgb = np.zeros((c * g, c * g, 3))
    a = np.zeros((c * g, c * g))
    for i, (cr, ca) in enumerate(cells):
        r, k = divmod(i, g)
        a[r * c:(r + 1) * c, k * c:(k + 1) * c] = ca
        rgb[r * c:(r + 1) * c, k * c:(k + 1) * c] = cr if cr is not None else 1.0
    return rgb, a


def to_image(rgb, a):
    a = np.clip(a, 0, 1)
    if rgb is None:
        rgb = np.ones(a.shape + (3,))
    rgb = np.broadcast_to(np.asarray(rgb, float), a.shape + (3,))
    out = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255])
    return Image.fromarray(np.round(out).astype(np.uint8), "RGBA")


def norm_pct(a, pct=99.8, gain=1.0):
    return np.clip(a / (np.percentile(a, pct) + 1e-9) * gain, 0, 1)


# =================================================================== 1. priest runes (holy floor seal)


def make_glyph(rng):
    """an invented gothic-liturgical glyph in unit space (u in [-0.5,0.5] across, v in [0,1] up).
    returns strokes [(pts, weight)], fills [polygon], dots [(u, v, r)]."""
    strokes, fills, dots = [], [], []

    def lozenge(u, v, s):
        fills.append([(u, v - s), (u + s * 0.6, v), (u, v + s), (u - s * 0.6, v)])

    nst = rng.choice([1, 1, 2, 2, 3])
    xs = {1: [0.0], 2: [-0.2, 0.2], 3: [-0.3, 0.0, 0.3]}[nst]
    tops = []
    for x in xs:
        x += rng.uniform(-0.04, 0.04)
        v0, v1 = rng.uniform(0.04, 0.16), rng.uniform(0.70, 0.86)
        strokes.append(([(x, v0), (x, v1)], "H"))
        tops.append((x, v1))
        k = rng.random()
        if k < 0.38:
            lozenge(x, v1 + 0.08, 0.075)
        elif k < 0.62:
            strokes.append(([(x - 0.13, v1 - 0.06), (x + 0.13, v1 - 0.06)], "L"))
        elif k < 0.82:
            for du, dv in ((0, 0.11), (-0.08, 0.04), (0.08, 0.04)):
                dots.append((x + du, v1 + dv, 0.034))
        # blackletter foot: a slanted hairline serif
        if rng.random() < 0.6:
            strokes.append(([(x, v0), (x + rng.choice([-1, 1]) * 0.12, v0 - 0.05)], "L"))
    for _ in range(rng.randint(1, 2) if nst > 1 else rng.randint(2, 3)):
        k = rng.random()
        if k < 0.26:
            v = rng.choice([0.34, 0.46, 0.58])
            strokes.append(([(-0.32, v), (0.32, v)], "L"))
        elif k < 0.46:
            s = rng.choice([-1, 1])
            strokes.append(([(-0.3 * s, 0.18), (0.3 * s, 0.72)], "L"))
        elif k < 0.64:  # hook / bowl
            cu, cv, rr = rng.choice([-0.12, 0.12]), rng.uniform(0.28, 0.5), rng.uniform(0.13, 0.19)
            a0 = rng.choice([0.0, math.pi])
            pts = [(cu + math.cos(a0 + i / 15 * math.pi) * rr, cv + math.sin(a0 + i / 15 * math.pi) * rr * 1.2) for i in range(16)]
            strokes.append((pts, "M"))
        elif k < 0.8:  # chevron
            v = rng.uniform(0.4, 0.62)
            strokes.append(([(-0.3, v), (0.0, v + 0.14), (0.3, v)], "L"))
        elif k < 0.92:  # little cross beside
            u = rng.choice([-0.36, 0.36])
            strokes.append(([(u, 0.36), (u, 0.62)], "L"))
            strokes.append(([(u - 0.08, 0.53), (u + 0.08, 0.53)], "L"))
        else:
            dots.append((rng.choice([-0.32, 0.32]), 0.5, 0.04))
    return strokes, fills, dots


def r_priest_runes():
    N = 2048
    c = N / 2
    R = N * 0.455
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    rng = random.Random(1717)

    def P(r, a):
        return (c + math.cos(a) * r, c + math.sin(a) * r)

    def circ(r, w, fill=255):
        d.ellipse((c - r, c - r, c + r, c + r), outline=fill, width=w)

    # --- outer border: hairline, bold ring, bead band, hairline pair
    circ(R * 1.0, 3)
    circ(R * 0.978, 9)
    nb = 96
    for i in range(nb):
        a = (i + 0.5) / nb * TAU
        if i % 2 == 0:
            p0, p1 = P(R * 0.915, a), P(R * 0.958, a)
            q0, q1 = P(R * 0.9365, a - 0.0075), P(R * 0.9365, a + 0.0075)
            d.polygon([p0, q0, p1, q1], fill=255)
        else:
            x, y = P(R * 0.9365, a)
            d.ellipse((x - 4.5, y - 4.5, x + 4.5, y + 4.5), fill=255)
    circ(R * 0.897, 3)
    circ(R * 0.883, 2)

    # --- glyph band (bent along the ring, 'up' faces outward), lozenge dividers every 4 glyphs
    r_in, gh = R * 0.745, R * 0.115
    n_gl = 36
    gw = TAU * (r_in + gh / 2) / n_gl * 0.66
    W = {"H": 9, "M": 6, "L": 4}
    for i in range(n_gl):
        ac = (i + 0.5) / n_gl * TAU
        strokes, fills, dots = make_glyph(rng)

        def mp(u, v, ac=ac):
            rr = r_in + v * gh
            return P(rr, ac + u * gw / rr)

        def dense(pts):
            out = []
            for (u0, v0), (u1, v1) in zip(pts[:-1], pts[1:]):
                for k in range(10):
                    t = k / 10
                    out.append((u0 + (u1 - u0) * t, v0 + (v1 - v0) * t))
            out.append(pts[-1])
            return out

        for pts, wt in strokes:
            d.line([mp(u, v) for u, v in dense(pts)], fill=255, width=W[wt], joint="curve")
        for poly in fills:
            d.polygon([mp(u, v) for u, v in poly], fill=255)
        for u, v, rr in dots:
            x, y = mp(u, v)
            s = rr * gh
            d.ellipse((x - s, y - s, x + s, y + s), fill=255)
        if i % 3 == 2:  # divider between glyph groups
            a = (i + 1) / n_gl * TAU
            x, y = P(r_in + gh * 0.5, a)
            p = [P(r_in + gh * 0.5 - 16, a), P(r_in + gh * 0.5, a + 0.006), P(r_in + gh * 0.5 + 16, a), P(r_in + gh * 0.5, a - 0.006)]
            d.polygon(p, fill=255)
    circ(R * 0.728, 6)
    circ(R * 0.712, 2)

    # --- tracery: an interlaced chain of 16 circles (gothic rosette), inner hairline + dotted ring
    nt, rc, rr = 16, R * 0.59, R * 0.112
    for i in range(nt):
        x, y = P(rc, i / nt * TAU)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=255, width=3)
        x2, y2 = P(rc, (i + 0.5) / nt * TAU)
        d.ellipse((x2 - 5, y2 - 5, x2 + 5, y2 + 5), fill=255)
    circ(R * 0.465, 5)
    for i in range(120):
        x, y = P(R * 0.445, i / 120 * TAU)
        d.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=255)

    # --- filigree: alternating quatrefoils and lozenge-in-vesica inside the tracery circles, tiny crosses between
    for i in range(nt):
        a = i / nt * TAU
        x, y = P(rc, a)
        if i % 2 == 0:
            q = rr * 0.36
            for k in range(4):
                b = a + k * math.pi / 2 + math.pi / 4
                qx, qy = x + math.cos(b) * q, y + math.sin(b) * q
                d.ellipse((qx - q, qy - q, qx + q, qy + q), outline=255, width=2)
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=255)
        else:
            ux, uy = math.cos(a), math.sin(a)
            vx, vy = -uy, ux
            s_ = rr * 0.62
            d.polygon([(x + ux * s_, y + uy * s_), (x + vx * s_ * 0.38, y + vy * s_ * 0.38),
                       (x - ux * s_, y - uy * s_), (x - vx * s_ * 0.38, y - vy * s_ * 0.38)], outline=255, width=3)
            s2 = s_ * 0.45
            d.polygon([(x + ux * s2, y + uy * s2), (x + vx * s2 * 0.4, y + vy * s2 * 0.4),
                       (x - ux * s2, y - uy * s2), (x - vx * s2 * 0.4, y - vy * s2 * 0.4)], fill=255)
        bx, by = P(R * 0.69, (i + 0.5) / nt * TAU)
        d.line([(bx - 7, by), (bx + 7, by)], fill=255, width=3)
        d.line([(bx, by - 7), (bx, by + 7)], fill=255, width=3)

    # --- cross-shaped star: diagonal minor points behind, then the four long arms (knock-out + outline + facets)
    def star_arm(a, L, half_a, inner):
        tip = P(L, a)
        v1 = P(inner, a - half_a)
        v2 = P(inner, a + half_a)
        side1, side2 = [], []
        for k in range(16):
            t = k / 15
            for (vx, vy), side, sgn in ((v1, side1, -1), (v2, side2, 1)):
                x = vx + (tip[0] - vx) * t
                y = vy + (tip[1] - vy) * t
                # bow inward toward the arm axis -> concave, blade-like sides
                ax, ay = P(inner * 0.5 + (L - inner * 0.5) * t, a)
                k_in = 0.28 * math.sin(math.pi * t)
                side.append((x + (ax - x) * k_in, y + (ay - y) * k_in))
        return side1, side2, tip

    def draw_star(arms, inner, w_out, facet=(95, 40)):
        polys = []
        for a, L in arms:
            s1, s2, tip = star_arm(a, L, math.pi / 4, inner)
            poly = [(c, c)] + s1 + s2[::-1]
            d.polygon(poly, fill=0)
            d.polygon([(c, c)] + s1 + [tip], fill=facet[0])
            d.polygon([(c, c)] + s2 + [tip], fill=facet[1])
            polys.append((s1, s2, tip))
        for s1, s2, tip in polys:
            d.line(s1 + [tip] + s2[::-1], fill=255, width=w_out, joint="curve")
            d.line([(c, c), tip], fill=255, width=3)

    up = -math.pi / 2
    draw_star([(up + math.pi / 4 + q * math.pi / 2, R * 0.36) for q in range(4)], R * 0.07, 4, facet=(55, 18))
    draw_star([(up, R * 0.70), (up + math.pi, R * 0.70), (up + math.pi / 2, R * 0.56), (up - math.pi / 2, R * 0.56)], R * 0.105, 7, facet=(120, 45))

    # --- centre: ringed medallion with a cross pattee
    rr = R * 0.095
    d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=0, outline=255, width=6)
    rr2 = R * 0.075
    d.ellipse((c - rr2, c - rr2, c + rr2, c + rr2), outline=255, width=2)
    for q in range(4):
        a = q * math.pi / 2
        n0, w0, n1, w1 = R * 0.012, 0.35, R * 0.066, 0.42
        d.polygon([P(n0, a - w0), P(n1, a - w1), P(n1, a + w1), P(n0, a + w0)], fill=255)
    d.ellipse((c - 10, c - 10, c + 10, c + 10), fill=255)

    line = L2f(img)
    g1 = blur(line, 5)
    g2 = blur(line, 18)
    g3 = blur(line, 60)
    a = line * 0.95 + g1 * 0.9 + g2 * 0.55 + g3 * 0.5
    x, y = grid(N)
    r = np.hypot(x, y)
    a += 0.10 * np.exp(-((r / 0.75) ** 2)) + 0.12 * np.exp(-((r / 0.12) ** 2))
    a = np.clip(a, 0, 1) * sstep(0.985, 0.94, r)
    return {"grip_priest_runes": (None, down(a, 2))}


# =================================================================== beams (vertical axis = along the beam)

BH, BW = 2048, 512  # 2x of 1024 x 256


def beam_axes():
    Y = (np.arange(BH)[:, None] + 0.5) / BH  # along, periodic 0..1
    X = (np.arange(BW)[None, :] + 0.5) / BW * 2 - 1  # across, -1..1
    return Y, X


def periodic_curve(Y, rng, terms, amp, fmax=4):
    """x(Y) = sum of integer-frequency sines (tiles) and its derivative d x / d Y."""
    x = np.zeros_like(Y)
    dx = np.zeros_like(Y)
    tot = 0
    for _ in range(terms):
        f = rng.integers(1, fmax + 1)
        A = rng.uniform(0.4, 1.0) / f ** 0.6
        ph = rng.uniform(0, TAU)
        x += A * np.sin(TAU * f * Y + ph)
        dx += A * TAU * f * np.cos(TAU * f * Y + ph)
        tot += A
    return x / tot * amp, dx / tot * amp


def curve_dist(X, xc, dxc):
    """perpendicular distance (in across units) to a curve x = xc(Y), correcting for slope in pixel space."""
    slope_px = dxc * (BW / 2) / BH
    return (X - xc) / np.sqrt(1 + slope_px ** 2)


def side_env(X, p=2.0):
    return np.clip(1 - X ** 2, 0, 1) ** p


def finish_beam(a, rgb=None):
    a = down(a, 2)
    if rgb is not None and np.ndim(rgb) == 3:
        rgb = down(rgb, 2)
    a[:, :2] = 0.0
    a[:, -2:] = 0.0
    return rgb, a


def r_lifethread():
    Y, X = beam_axes()
    rng = np.random.default_rng(404)
    acc = np.zeros((BH, BW))
    fib_n = pnoise(1024, 128, beta=1.1, seed=405, aniso=(1.0, 5.0))  # strands along the thread
    # three braided main strands, each a rope of 4 fibres; depth = over/under in the braid
    f = 3
    for k in range(3):
        ph = k * TAU / 3
        th = TAU * f * Y + ph
        xc = 0.34 * np.sin(th) + 0.03 * np.sin(TAU * 6 * Y + k)
        dxc = 0.34 * TAU * f * np.cos(th) + 0.03 * TAU * 6 * np.cos(TAU * 6 * Y + k)
        depth = (np.cos(th) + 1) / 2  # 1 = front
        bright = 0.35 + 0.65 * depth ** 1.4
        for j in range(4):
            off = 0.022 * np.sin(TAU * 9 * Y + j * TAU / 4 + k)
            dd = curve_dist(X, xc + off, dxc)
            w = 0.010 + 0.006 * depth
            acc += np.exp(-((dd / w) ** 2)) * bright * 0.55
        dd = curve_dist(X, xc, dxc)
        acc += np.exp(-((dd / (0.07 + 0.03 * depth)) ** 2)) * bright * 0.22  # strand halo
    # loose fine filaments drifting around the braid
    for k in range(9):
        xc, dxc = periodic_curve(Y, rng, 3, rng.uniform(0.2, 0.55), fmax=5)
        dd = curve_dist(X, xc, dxc)
        mod = 0.5 + 0.5 * np.sin(TAU * rng.integers(1, 4) * Y + rng.uniform(0, TAU))
        acc += np.exp(-((dd / rng.uniform(0.004, 0.008)) ** 2)) * rng.uniform(0.18, 0.4) * mod
    # soft core, pulsing, with fibre texture
    fib = samp(fib_n, Y * 1024 + 0 * X, (X + 1) / 2 * 128 * 3)
    core = np.exp(-((X / 0.16) ** 2)) * (0.6 + 0.4 * np.sin(TAU * 2 * Y + 0.7) ** 2)
    acc += core * (0.45 + 0.18 * fib) + np.exp(-((X / 0.035) ** 2)) * 0.35
    acc += np.exp(-((X / 0.42) ** 2)) * 0.10
    # beads of light travelling along the strands (periodic positions)
    beads = np.zeros((BH, BW))
    for k in range(3):
        ph = k * TAU / 3
        for b in range(4):
            yb = (b + 0.25 * k + rng.uniform(0, 0.2)) / 4
            th = TAU * f * yb + ph
            xb = 0.34 * np.sin(th)
            dy = ((Y - yb + 0.5) % 1 - 0.5) * BH
            dx = (X - xb) * BW / 2
            beads += np.exp(-(dx ** 2 + dy ** 2) / (2 * 7.0 ** 2)) * (0.6 + 0.4 * np.cos(th))
            beads += np.exp(-(dx ** 2 + dy ** 2) / (2 * 22.0 ** 2)) * 0.25
    acc += beads * 0.9
    a = norm_pct(acc, 99.5, 1.0) ** 1.05 * side_env(X, 2.5)
    return {"grip_lifethread_v": finish_beam(a)}


def r_ink_tendril():
    Y, X = beam_axes()
    rng = np.random.default_rng(616)
    ink = np.array([0.035, 0.028, 0.050])
    # stem centreline and width (periodic)
    xc, dxc = periodic_curve(Y, rng, 3, 0.16, fmax=3)
    dd = curve_dist(X, xc, dxc)
    w = 0.085 + 0.035 * np.sin(TAU * 2 * Y + 1.1) + 0.015 * np.sin(TAU * 5 * Y)
    en = pnoise(1024, 256, beta=1.4, seed=617, aniso=(1.0, 2.5))
    edge_n = samp(en, Y * 1024, (X + 1) / 2 * 256)
    body = sstep(1.08, 0.72, np.abs(dd) / w + 0.22 * edge_n)
    # thorns: hooked spikes, drawn tiled (each drawn at y-H, y, y+H)
    timg = Image.new("L", (BW, BH), 0)
    td = ImageDraw.Draw(timg)
    n_th = 9
    xcs = xc[:, 0]
    ws = w[:, 0]
    for j in range(n_th):
        yb = (j + rng.uniform(-0.2, 0.2)) / n_th
        side = 1 if j % 2 == 0 else -1
        if rng.random() < 0.25:
            side = -side
        row = int(yb * BH) % BH
        bx = (xcs[row] + side * ws[row] * 0.75 + 1) / 2 * BW
        L = rng.uniform(0.22, 0.34) * BW
        ang0 = math.radians(rng.uniform(25, 45))  # angle from the axis, pointing "up" the beam (-y)
        pts = []
        for k in range(20):
            t = k / 19
            ang = ang0 + t * 0.9  # hook: curls further outward toward the tip
            px_ = bx + side * math.sin(ang0 + 0.5 * t * 0.9) * L * t
            py_ = row * 1.0 - math.cos(ang0 + 0.5 * t * 0.9) * L * t * 1.1
            pts.append((px_, py_))
        for off in (-BH, 0, BH):
            p = [(x_, y_ + off) for x_, y_ in pts]
            stroke(td, p, rng.uniform(34, 46), 1.5, power=0.8)
            # small secondary barbs
            if rng.random() < 0.7:
                i0 = rng.integers(5, 11)
                bpx, bpy = p[i0]
                bl = L * 0.3
                q = [(bpx, bpy), (bpx + side * bl * 0.5, bpy - bl * 0.25), (bpx + side * bl * 0.8, bpy - bl * 0.7)]
                stroke(td, catmull(q, 8), 12, 1.0)
    thorns = blur(L2f(timg), 1.5, wrap_rows=True)
    tn = samp(en, Y * 1024 + 300, (X + 1) / 2 * 256 * 2)
    thorns = sstep(0.25, 0.75, thorns + 0.12 * tn)
    solid = np.maximum(body, thorns)
    # wisps: smoke fibres trailing off the tendril, stretched along the beam
    wn = pnoise(1024, 256, beta=1.2, seed=618, aniso=(1.0, 7.0))
    wn2 = pnoise(1024, 256, beta=1.6, seed=619, aniso=(1.0, 3.0))
    wy = Y * 1024 + 18 * samp(wn2, Y * 1024, (X + 1) / 2 * 256)
    wisp = samp(wn, wy, (X + 1) / 2 * 256 + 20 * samp(wn2, Y * 1024 + 500, (X + 1) / 2 * 256))
    ridge = (1 - np.abs(np.tanh(wisp * 1.2))) ** 5
    near = np.exp(-np.maximum(np.abs(dd) - w, 0) / 0.16)
    wisps = ridge * near * 0.75 + np.exp(-np.maximum(np.abs(dd) - w, 0) / 0.07) * 0.35
    a = np.maximum(solid, np.clip(wisps, 0, 1) * (1 - solid * 0.5))
    a = np.clip(a, 0, 1) * side_env(X, 2.0)
    # colour: near-black ink, a faint cool sheen on the thin / edge parts so it reads on dark scenes
    inner = blur(solid, 6, wrap_rows=True)
    sheen = np.clip(1 - inner, 0, 1) * 0.10 + (1 - solid) * 0.05
    rgb = ink[None, None, :] + sheen[..., None] * np.array([0.85, 0.85, 1.0])
    return {"grip_ink_tendril_v": finish_beam(a, rgb)}


def r_soul_streak():
    Y, X = beam_axes()
    rng = np.random.default_rng(777)
    acc = np.zeros((BH, BW))
    fn = pnoise(1024, 256, beta=1.0, seed=778, aniso=(1.0, 6.0))
    wn = pnoise(512, 128, beta=2.0, seed=779)
    # spiral ribbons
    f = 2
    for k in range(3):
        ph = k * TAU / 3 + 0.4
        th = TAU * f * Y + ph
        xc = 0.40 * np.sin(th)
        dxc = 0.40 * TAU * f * np.cos(th)
        depth = (np.cos(th) + 1) / 2
        dd = curve_dist(X, xc, dxc)
        wid = 0.035 + 0.075 * depth
        u = dd / wid
        fib = samp(fn, Y * 1024 * 1.0 + k * 300, (u + 4) / 8 * 256 * 0.5 + k * 40)
        rib = np.exp(-(u ** 2)) * (0.55 + 0.45 * np.tanh(fib * 1.3)) + np.exp(-((u / 0.18) ** 2)) * 0.35 * depth
        acc += rib * (0.25 + 0.75 * depth ** 1.3)
    # ghostly smears: abstract oval heads with hollow 'eyes' and a stretched 'mouth', comet-smeared down the beam
    for y0, x0, s in ((0.20, -0.12, 1.0), (0.68, 0.14, 0.85)):
        dy = ((Y - y0 + 0.5) % 1 - 0.5) * BH / 2  # 1x px
        dx = (X - x0) * BW / 4  # 1x px
        wr = 1024 * ((Y - y0) % 1.0)
        dx = dx + 7 * samp(wn, wr * 0.5 + 0 * X, (X + 1) * 64)
        dy = dy + 9 * samp(wn, wr * 0.5 + 200 + 0 * X, (X + 1) * 64 + 50)
        dyp = np.maximum(dy, 0)
        head = np.exp(-((dx / (34 * s + 0.10 * dyp)) ** 2)) * np.exp(-((np.minimum(dy, 0) / (44 * s)) ** 2)) * np.exp(-dyp / (210 * s))
        eyes = np.exp(-(((np.abs(dx) - 13 * s) / (6.5 * s)) ** 2) - (((dy + 14 * s) / (9 * s)) ** 2))
        mouth = np.exp(-((dx / (6.5 * s)) ** 2) - (((dy - 20 * s) / (17 * s)) ** 2))
        ghost = head * (1 - 0.9 * eyes) * (1 - 0.75 * mouth)
        ghost += np.exp(-((dx / (60 * s)) ** 2) - ((dy - 40) / (160 * s)) ** 2) * 0.12
        acc += ghost * 0.95
    # core column + fine streaking wisps
    st = samp(fn, Y * 1024 + 700, (X + 1) / 2 * 256 * 2)
    acc += np.exp(-((X / 0.22) ** 2)) * (0.22 + 0.12 * st) + np.exp(-((X / 0.5) ** 2)) * 0.08
    acc += np.clip(st - 1.0, 0, None) * 0.25 * np.exp(-((X / 0.45) ** 2))
    a = norm_pct(acc, 99.6, 1.0) ** 1.1 * side_env(X, 2.5)
    return {"grip_soul_streak_v": finish_beam(a)}


# =================================================================== 3. ink smoke flipbook


def r_ink_smoke(seed=61):
    C, S = 256, 2
    n = C * S
    px, py = grid(n)
    to = lambda v: (v + 1) / 2 * 256  # noqa: E731
    nW1 = pnoise(256, 256, beta=2.4, seed=seed - 4)
    nW2 = pnoise(256, 256, beta=2.4, seed=seed - 3)
    nB = pnoise(256, 256, beta=1.9, seed=seed - 2)  # billow lumps
    nD = pnoise(256, 256, beta=1.4, seed=seed + 1)  # finer boil
    nR = pnoise(256, 256, beta=2.1, seed=seed - 1)  # smooth field for ridged tendrils
    nE = pnoise(256, 256, beta=1.6, seed=seed + 2)  # dissolve erosion
    rng = np.random.default_rng(seed)
    K = 7
    la = np.linspace(0, TAU, K, endpoint=False) + rng.uniform(-0.3, 0.3, K)
    ld = rng.uniform(0.5, 1.0, K)
    ls = rng.uniform(0.75, 1.1, K)
    # curl vortices around the rim: they wind the edge into curling tendrils as the puff grows
    vort = [((k + rng.uniform(-0.2, 0.2)) / 6 * TAU, rng.uniform(0.45, 0.6), (1 if k % 2 else -1) * rng.uniform(0.9, 1.5)) for k in range(6)]
    fade = cell_fade(n, 0.80, 0.97)
    ink = np.array([0.028, 0.022, 0.042])
    cells = []
    for i in range(16):
        t = i / 15
        e = 1 - (1 - t) ** 2.2
        zoom = 0.95  # puff fills ~75% of the cell at its biggest
        qx, qy = px * zoom, py * zoom + 0.04 * e  # the whole puff drifts up a little
        for va, vr, w in vort:
            vx, vy = math.cos(va) * vr * (0.55 + 0.45 * e), math.sin(va) * vr * (0.55 + 0.45 * e)
            dx, dy = qx - vx, qy - vy
            ang = w * e * np.exp(-(dx * dx + dy * dy) / 0.045)
            ca, sa = np.cos(ang), np.sin(ang)
            qx, qy = vx + dx * ca - dy * sa, vy + dx * sa + dy * ca
        amp = 0.03 + 0.07 * e
        sh = 18 * t
        qx = qx + amp * samp(nW1, to(qy) * 0.9 + sh, to(qx) * 0.9)
        qy = qy + amp * samp(nW2, to(qy) * 0.9, to(qx) * 0.9 - sh)
        D = np.zeros_like(px)
        for k in range(K):
            cx = math.cos(la[k]) * 0.30 * ld[k] * (0.3 + 0.7 * e)
            cy = math.sin(la[k]) * 0.28 * ld[k] * (0.3 + 0.7 * e)
            r = (0.17 + 0.17 * e) * ls[k]
            D += np.exp(-((qx - cx) ** 2 + (qy - cy) ** 2) / r ** 2)
        D += np.exp(-(qx ** 2 + qy ** 2) / (0.24 + 0.16 * e) ** 2)
        D = 1 - np.exp(-1.4 * D)  # bounded 0..1, rounded union
        lump = samp(nB, to(qy) * 2.2 + 9 * t, to(qx) * 2.2)
        boil = samp(nD, to(qy) * 3.0 - 14 * t, to(qx) * 3.0)
        F = D + 0.17 * lump + 0.05 * boil
        edge = 0.45
        body = sstep(edge - 0.08, edge + 0.10, F)
        # tendrils: thin ridges of a smooth field, only in a band just outside the body
        rid = (1 - np.abs(np.tanh(samp(nR, to(qy) * 1.3, to(qx) * 1.3 + 6 * t) * 2.2))) ** 14
        band = sstep(edge - 0.30, edge - 0.02, F) * (1 - body)
        tend = rid * band * (0.4 + 0.6 * e)
        a = np.clip(body + tend * 0.85, 0, 1)
        # dissolve: erosion eats holes from the thin parts inward, and the whole puff thins out
        er = np.clip(samp(nE, to(qy) * 2.2 + 20 * t, to(qx) * 2.2) * 0.3 + 0.5, 0, 1)
        thr = -0.25 + 1.30 * sstep(0.22, 1.0, t) ** 1.3
        a *= sstep(thr - 0.12, thr + 0.12, er * 0.65 + F * 0.55)
        a *= 1 - 0.55 * sstep(0.45, 1.0, t)
        # keep the puff centred in its cell (the low-frequency warp otherwise drifts it sideways)
        cy_, cx_ = ndimage.center_of_mass(body)
        sh_y, sh_x = n / 2 - cy_ - 0.04 * e * n / 2, n / 2 - cx_
        a = ndimage.shift(a, (sh_y, sh_x), order=1, mode="constant")
        F = ndimage.shift(F, (sh_y, sh_x), order=1, mode="constant")
        body = ndimage.shift(body, (sh_y, sh_x), order=1, mode="constant")
        boil = ndimage.shift(boil, (sh_y, sh_x), order=1, mode="constant")
        a *= fade
        # shading: deep ink inside; billow tops catch a faint cool light (from above), thin edges lighter
        Fb = blur(F, 3)
        gy, gx = np.gradient(Fb)
        light = np.clip(-(gy * 0.8 + gx * 0.35) * 40, 0, 1) * body
        dens = sstep(0.3, 0.95, blur(body, 5))
        v = (1 - dens) * 0.07 + light * 0.05 + 0.012 * boil
        rgb = ink[None, None, :] + v[..., None] * np.array([0.9, 0.9, 1.0])
        cells.append((down(rgb, S), down(a, S)))
    return {"grip_ink_smoke_4x4": assemble(cells, 4)}


# =================================================================== 5. claw slash


def r_claw_slash():
    N = 2048
    x, y = grid(N)
    rot = math.radians(-24)
    u = x * math.cos(rot) - y * math.sin(rot)
    v = x * math.sin(rot) + y * math.cos(rot)
    Cu, Cv = 0.0, 1.30
    du, dv = u - Cu, v - Cv
    r = np.hypot(du, dv)
    th = np.arctan2(dv, du)  # -pi/2 at the top of the arcs
    sn = pnoise(256, 1024, beta=0.9, seed=55, aniso=(1.0, 0.08))  # streaks running along the arc
    A = np.ones_like(x)
    # (radius, start angle, end angle, max half-width): middle claw longest, the set staggered like a raking hand
    claws = [(1.00, -0.62, 0.58, 0.044), (1.15, -0.66, 0.64, 0.052), (1.30, -0.58, 0.56, 0.044)]
    for k, (R, a0, a1, W) in enumerate(claws):
        t = (th - (-math.pi / 2 + a0)) / (a1 - a0)  # 0 trailing end -> 1 leading tip
        tc = np.clip(t, 0, 1)
        w = W * np.sin(np.pi * tc) ** 0.8 * (0.40 + 0.60 * tc ** 0.7) + 1e-4
        d = r - R
        live = sstep(0.0, 0.06, t) * sstep(1.0, 0.95, t)
        s_out, s_in = w * 0.50, w * 1.30
        body = np.where(d > 0, np.exp(-((d / s_out) ** 2)), np.exp(-((d / s_in) ** 2))) * live
        core = np.exp(-(((d + 0.12 * w) / (0.20 * w)) ** 2)) * live * sstep(0.04, 0.3, t)
        glow = np.exp(-((d / (w * 3.0 + 0.012)) ** 2)) * live * 0.28
        # motion smear: streaky trail fading out behind the trailing end, and on the inside of each crescent
        tw = W * (0.7 + 0.8 * np.clip(-t, 0, 1))
        smear_live = sstep(-0.16, 0.04, t) * sstep(0.75, 0.2, t)
        st = samp(sn, (r / 2.0) * 256 * 6 + k * 50, (th / TAU) * 1024)
        streak = np.clip(0.5 + 0.5 * np.tanh(st * 1.6), 0, 1)
        smear = np.exp(-(((d + 0.35 * W) / tw) ** 2)) * smear_live * streak * 0.55
        a = np.clip(core + body * 0.62 + glow + smear, 0, 1)
        A *= 1 - a
    # faint swept-air sheet across the whole rake, streaked
    R0, R1 = claws[0][0] - 0.06, claws[-1][0] + 0.03
    t = (th - (-math.pi / 2 - 0.62)) / 1.22
    band = sstep(R0 - 0.05, R0 + 0.04, r) * sstep(R1 + 0.04, R1 - 0.05, r) * sstep(-0.1, 0.25, t) * sstep(0.95, 0.55, t)
    st2 = samp(sn, (r / 2.0) * 256 * 3 + 400, (th / TAU) * 1024 * 0.5)
    A *= 1 - band * np.clip(0.5 + 0.5 * np.tanh(st2 * 1.2), 0, 1) * 0.16
    A = 1 - A
    # centre the artwork in the frame, then fade before the edge
    cy, cx = ndimage.center_of_mass(A)
    A = ndimage.shift(A, (N / 2 - cy, N / 2 - cx), order=1, mode="constant")
    A *= sstep(1.0, 0.92, np.hypot(x, y)) * edge_fade(N, margin=0.03)
    return {"grip_claw_slash": (None, down(np.clip(A, 0, 1), 2))}


# =================================================================== 6. slash spark flipbook


def r_slash_spark():
    C, S = 256, 2
    n = C * S
    x, y = grid(n)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    rng = np.random.default_rng(66)
    NR = 18
    ang = rng.uniform(0, TAU, NR)
    ang[:4] = np.array([0.0, 0.5, 1.0, 1.5]) * math.pi + math.radians(30)  # four main flare rays (an X)
    lens = rng.uniform(0.35, 0.75, NR)
    lens[:4] = 0.92
    wids = rng.uniform(0.008, 0.016, NR)
    wids[:4] = 0.014
    sparks = [(rng.uniform(0, TAU), rng.uniform(0.25, 0.5), rng.uniform(0.6, 1.0)) for _ in range(14)]
    fade = cell_fade(n, 0.80, 0.97)

    def ray(a0, L, w, r0=0.0, r1=None):
        dlt = np.angle(np.exp(1j * (th - a0)))
        along = r * np.cos(dlt)
        perp = r * np.sin(dlt)
        ww = w * np.clip(1 - along / max(L, 1e-3), 0.05, 1)
        prof = sstep(-0.02, 0.04, along) * np.exp(-((np.maximum(along, 0) / L) ** 2) * 2.2)
        if r1 is not None:
            prof = sstep(r0 - 0.04, r0 + 0.02, along) * sstep(r1 + 0.04, r1 - 0.02, along)
        return np.exp(-((perp / ww) ** 2)) * prof * (along > -0.02)

    cells = []
    for f in range(4):
        a = np.zeros((n, n))
        if f == 0:  # pop
            a += np.exp(-((r / 0.07) ** 2)) * 1.0 + np.exp(-((r / 0.20) ** 2)) * 0.45
            for j in range(NR):
                a += ray(ang[j], lens[j] * 0.45, wids[j] * 1.1) * (1.0 if j < 4 else 0.6)
        elif f == 1:  # peak
            a += np.exp(-((r / 0.10) ** 2)) * 1.0 + np.exp(-((r / 0.30) ** 2)) * 0.45
            for j in range(NR):
                a += ray(ang[j], lens[j], wids[j]) * (1.0 if j < 4 else 0.75)
            a += np.exp(-(((r - 0.32) / 0.02) ** 2)) * 0.35
        elif f == 2:  # rays break into flying streaks
            a += np.exp(-((r / 0.09) ** 2)) * 0.55 + np.exp(-((r / 0.28) ** 2)) * 0.22
            for j in range(NR):
                L = lens[j]
                a += ray(ang[j], L * 1.1, wids[j] * 0.8, L * 0.45, L * 0.95) * (0.8 if j < 4 else 0.55)
            for sa, sr, sb in sparks:
                rr_ = sr * 1.25
                a += ray(sa, 1.0, 0.010, rr_ - 0.06, rr_ + 0.02) * sb * 0.8
            a += np.exp(-(((r - 0.55) / 0.035) ** 2)) * 0.16
        else:  # dissipating
            a += np.exp(-((r / 0.14) ** 2)) * 0.16 + np.exp(-((r / 0.05) ** 2)) * 0.18
            for sa, sr, sb in sparks:
                rr_ = min(sr * 1.6, 0.74)
                a += ray(sa, 1.0, 0.008, rr_ - 0.035, rr_ + 0.01) * sb * 0.55
            a += np.exp(-(((r - 0.70) / 0.05) ** 2)) * 0.06
        a = np.clip(a, 0, 1) * fade
        cells.append((None, down(a, S)))
    return {"grip_slash_spark_2x2": assemble(cells, 2)}


# =================================================================== 7. frost floor


def r_frost_floor():
    N = 2048
    c = N / 2
    R = N * 0.5
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    rng = random.Random(2323)

    def grow(x, y, ang, length, w0, depth, val, t_start=0.10):
        step = 4.0 if depth == 0 else 3.0
        nsteps = max(2, int(length / step))
        sp = (30, 15, 9)[min(depth, 2)]
        s_since = rng.uniform(0, sp)
        curl = rng.uniform(-0.003, 0.003) * (1 + depth)
        for k in range(nsteps):
            t = k / nsteps
            w = w0 * (1 - t) ** 0.8 + 1.0
            ang += curl + rng.gauss(0, (0.022, 0.035, 0.05)[min(depth, 2)])
            nx, ny = x + math.cos(ang) * step, y + math.sin(ang) * step
            if math.hypot(nx - c, ny - c) > R * 0.93:
                return
            d.line([(x, y), (nx, ny)], fill=int(val * (0.7 + 0.3 * (1 - t))), width=max(1, int(round(w))))
            x, y = nx, ny
            s_since += step
            if depth < 2 and s_since >= sp and (t_start if depth == 0 else 0.05) < t < 0.95:
                s_since = rng.uniform(-0.3, 0.1) * sp
                rem = length * (1 - t)
                base = min(rem * (0.34 if depth == 0 else 0.42), (110, 40)[depth])
                for sgn in (-1, 1):
                    if rng.random() < (0.85 if depth == 0 else 0.55):
                        bl = base * rng.uniform(0.6, 1.0)
                        if bl > 7:
                            grow(x, y, ang + sgn * math.radians(rng.uniform(54, 64)), bl, w * 0.5, depth + 1, val * 0.85)

    n_main = 17
    for i in range(n_main):
        a = i / n_main * TAU + rng.uniform(-0.08, 0.08)
        L = R * rng.uniform(0.66, 0.86)
        grow(c + math.cos(a) * 16, c + math.sin(a) * 16, a, L, 8, 0, 255, t_start=0.16)
    for i in range(n_main):  # shorter arms seeded part-way out, between the main ones
        a = (i + 0.5) / n_main * TAU + rng.uniform(-0.06, 0.06)
        r0 = R * rng.uniform(0.30, 0.42)
        L = R * rng.uniform(0.25, 0.42)
        grow(c + math.cos(a) * r0, c + math.sin(a) * r0, a + rng.uniform(-0.08, 0.08), L, 5, 0, 200, t_start=0.05)
    # hexagonal nucleus plate
    for rr, w in ((R * 0.065, 6), (R * 0.04, 3)):
        pts = [(c + math.cos(j / 6 * TAU + 0.3) * rr, c + math.sin(j / 6 * TAU + 0.3) * rr) for j in range(7)]
        d.line(pts, fill=255, width=w, joint="curve")
    for j in range(6):
        aj = j / 6 * TAU + 0.3
        d.line([(c, c), (c + math.cos(aj) * R * 0.065, c + math.sin(aj) * R * 0.065)], fill=230, width=3)

    line = L2f(img)
    x, y = grid(N)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    gn = np.kron(pnoise(1024, 1024, beta=0.4, seed=24), np.ones((2, 2)))
    grains = np.clip(gn - 2.0, 0, None)
    hz = ndimage.zoom(pnoise(512, 512, beta=1.6, seed=25), 4, order=1)
    dens = np.exp(-((r / 0.5) ** 2))
    haze = (0.055 + 0.035 * hz) * dens + np.exp(-((r / 0.09) ** 2)) * 0.18
    e = line * 1.1 + blur(line, 2.0) * 0.45 + blur(line, 9) * 0.22 + blur(line, 32) * 0.12
    e += blur(grains, 0.8) * dens * 0.5 + np.clip(haze, 0, 1)
    a = 1 - np.exp(-2.2 * e)  # soft saturation keeps the dense centre from turning into a flat blob
    a = a / (1 - math.exp(-2.2))
    rim = 0.80 + 0.05 * np.sin(5 * th + 0.4) * np.sin(3 * th + 1.2) + 0.03 * np.sin(11 * th)
    a = np.clip(a, 0, 1) * sstep(rim + 0.08, rim - 0.16, r) * sstep(0.97, 0.92, r)
    return {"grip_frost_floor": (None, down(a, 2))}


# =================================================================== 8. grave cracks (+ glow mask)


def r_grave_cracks():
    N = 2048
    c = N / 2
    R = N * 0.47
    rng = random.Random(808)
    paths = []  # (pts, widths)
    mains = []  # main radial crack polylines, for the ring cracks to bridge

    def walk(x, y, ang, length, w0, depth, keep=None):
        pts, ws = [(x, y)], [w0]
        base = ang
        dev = 0.0
        trav = 0.0
        while trav < length:
            seg = rng.uniform(22, 52)
            dev = float(np.clip(dev * 0.25 + rng.gauss(0, 0.34), -0.7, 0.7))
            ang = base + dev
            x, y = x + math.cos(ang) * seg, y + math.sin(ang) * seg
            if math.hypot(x - c, y - c) > R * 0.95:
                break
            trav += seg
            t = min(trav / length, 1.0)
            w = w0 * (1 - t) ** 0.7 + 1.6
            pts.append((x, y))
            ws.append(w)
            if depth < 2 and rng.random() < (0.16 if depth == 0 else 0.08) and t < 0.8:
                sgn = rng.choice([-1, 1])
                walk(x, y, ang + sgn * rng.uniform(0.4, 0.9), (length - trav) * rng.uniform(0.3, 0.6), w * 0.55, depth + 1)
        paths.append((pts, ws))
        if keep is not None:
            keep.append(pts)

    n_main = 10
    for i in range(n_main):
        a = i / n_main * TAU + rng.uniform(-0.2, 0.2)
        walk(c + math.cos(a) * R * 0.06, c + math.sin(a) * R * 0.06, a, R * rng.uniform(0.66, 0.9), 24, 0, keep=mains)

    def at_radius(poly, rad):
        for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
            r0, r1 = math.hypot(x0 - c, y0 - c), math.hypot(x1 - c, y1 - c)
            if (r0 - rad) * (r1 - rad) <= 0 and r0 != r1:
                t = (rad - r0) / (r1 - r0)
                return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
        return None

    # spider-web ring cracks: near-straight kinked chords bridging neighbouring radial cracks
    for rad, wr, pskip in ((0.20, 8, 0.35), (0.34, 7, 0.45), (0.50, 6, 0.6), (0.68, 5, 0.75)):
        for i in range(n_main):
            if rng.random() < pskip:
                continue
            rr = rad * R * rng.uniform(0.9, 1.1)
            p0, p1 = at_radius(mains[i], rr), at_radius(mains[(i + 1) % n_main], rr * rng.uniform(0.92, 1.08))
            if p0 is None or p1 is None:
                continue
            nk = rng.randint(3, 5)
            pts = [p0]
            for k in range(1, nk):
                t = k / nk
                mx, my = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
                ox, oy = mx - c, my - c
                ol = math.hypot(ox, oy) + 1e-6
                b = rr * 0.05 + rng.gauss(0, 12)
                pts.append((mx + ox / ol * b + rng.gauss(0, 9), my + oy / ol * b + rng.gauss(0, 9)))
            pts.append(p1)
            ws = [wr * (0.5 + 0.5 * math.sin(math.pi * k / nk)) + 1.4 for k in range(nk + 1)]
            paths.append((pts, ws))
    # crushed centre: short dense fractures
    for i in range(26):
        a = rng.uniform(0, TAU)
        walk(c + math.cos(a) * 8, c + math.sin(a) * 8, a, R * rng.uniform(0.06, 0.17), 9, 2)

    def draw(scale, minw, val_fn):
        img = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(img)
        for pts, ws in paths:
            for (x0, y0), (x1, y1), w0, w1 in zip(pts[:-1], pts[1:], ws[:-1], ws[1:]):
                v = val_fn(math.hypot(x0 - c, y0 - c) / R)
                stroke(d, [(x0, y0), (x1, y1)], max(w0 * scale, minw), max(w1 * scale, minw), fill=v)
        return L2f(img)

    M = draw(1.0, 2.0, lambda rr: 255)
    ch = draw(0.38, 1.4, lambda rr: 255 * (0.35 + 0.65 * math.exp(-rr / 0.45)))
    x, y = grid(N)
    r = np.hypot(x, y)
    fade = sstep(0.97, 0.86, r)
    rough = ndimage.zoom(pnoise(512, 512, beta=1.5, seed=809), 4, order=1)
    # crack decal: darkened ground halo, chipped lighter lips, near-black crack interiors, crushed pit
    Mb = blur(M, 1.6)
    halo = np.clip(np.clip(blur(M, 22) * 1.5 + np.exp(-((r / 0.13) ** 2)) * 0.6, 0, 1) * (0.7 + 0.3 * rough), 0, 1)
    lip = np.clip(np.clip(blur(M, 5) * 1.7 - Mb, 0, 1) * (0.6 + 0.4 * rough), 0, 1)
    rgb = np.zeros((N, N, 3))
    al = np.zeros((N, N))
    rgb, al = over(rgb, al, np.full((N, N, 3), 0.06), halo * 0.50)
    rgb, al = over(rgb, al, np.full((N, N, 3), 0.33), lip * 0.55)
    rgb, al = over(rgb, al, np.full((N, N, 3), 0.02), np.clip(Mb * 1.2, 0, 1))
    al *= fade
    # glow channels: thin hot line in the crack, soft bloom around it, brighter toward the centre
    g = ch * 1.0 + blur(ch, 4) * 0.9 + blur(ch, 14) * 0.5 + blur(ch, 40) * 0.25
    g += np.exp(-((r / 0.07) ** 2)) * 0.5
    g = np.clip(g, 0, 1) * fade
    return {"grip_grave_cracks": (down(rgb, 2), down(al, 2)), "grip_grave_cracks_glow": (None, down(g, 2))}


# =================================================================== 9. ash flipbook


def r_ash():
    C, S = 256, 2
    n = C * S
    px, py = grid(n)
    r = np.hypot(px, py)
    th = np.arctan2(py, px)
    rng = np.random.default_rng(909)
    # irregular flake cluster
    Rb = 0.50 * (1 + 0.16 * np.sin(3 * th + 0.5) + 0.09 * np.sin(5 * th + 2.0) + 0.05 * np.sin(9 * th + 1.0))
    blob = sstep(Rb + 0.01, Rb - 0.01, r)
    seeds = []
    while len(seeds) < 58:
        p = rng.uniform(-0.62, 0.62, 2)
        pr, pt = math.hypot(*p), math.atan2(p[1], p[0])
        rb = 0.50 * (1 + 0.16 * math.sin(3 * pt + 0.5) + 0.09 * math.sin(5 * pt + 2.0) + 0.05 * math.sin(9 * pt + 1.0))
        if pr < rb * 0.95:
            seeds.append(p)
    seeds = np.array(seeds)
    tree = cKDTree(seeds)
    pts = np.stack([px.ravel(), py.ravel()], 1)
    dd, ii = tree.query(pts, k=2)
    lab = ii[:, 0].reshape(n, n)
    gapd = (dd[:, 1] - dd[:, 0]).reshape(n, n)
    gap = sstep(0.004, 0.016, gapd)
    tex = pnoise(256, 256, beta=1.1, seed=910)
    tex = ndimage.zoom(tex, 2, order=1)
    E = pnoise(256, 256, beta=1.3, seed=911)
    E = ndimage.zoom(E, 2, order=1)
    E = (E - E.min()) / (E.max() - E.min())
    flakes = []
    for k in range(len(seeds)):
        m = (lab == k) * blob * gap
        if m.max() <= 0:
            continue
        val = rng.uniform(0.62, 1.0)
        cy, cx = ndimage.center_of_mass(m)
        dirv = np.array([cx - n / 2, cy - n / 2])
        dist = np.linalg.norm(dirv) / (n / 2)
        dirv = dirv / (np.linalg.norm(dirv) + 1e-6) + rng.normal(0, 0.35, 2)
        flakes.append(dict(
            m=m, val=val, c=(cy, cx), dir=dirv, speed=rng.uniform(0.6, 1.1),
            spin=rng.uniform(-1, 1) * math.radians(110), tb=float(np.clip(0.30 * (1 - dist / 0.5) + rng.uniform(0, 0.18), 0, 0.5)),
            eoff=rng.uniform(-0.15, 0.15)))
    fade = cell_fade(n, 0.82, 0.97)
    cells = []
    for f in range(16):
        t = f / 15
        acc_c = np.zeros((n, n))
        acc_a = np.zeros((n, n))
        dust = np.zeros((n, n))
        for fl in flakes:
            tau = max(0.0, (t - fl["tb"]) / (1 - fl["tb"]))
            e = -0.08 + 1.0 * tau ** 1.3 + fl["eoff"] * tau
            src_a = fl["m"] * sstep(e - 0.06, e + 0.08, E)
            if src_a.max() < 0.01:
                continue
            src_v = fl["val"] * (0.80 + 0.12 * tex) + 0.15 * (1 - sstep(0.1, 0.5, src_a))
            disp = fl["dir"] * fl["speed"] * (tau ** 1.25) * 0.20 * n / 2
            disp = disp + np.array([0.0, -0.16 * tau * n / 2])
            disp[0] += math.sin(tau * 5 + fl["spin"]) * 0.02 * n / 2 * tau
            sc = 1 - 0.35 * tau
            ang = fl["spin"] * tau
            ca, sa = math.cos(ang), math.sin(ang)
            # output (row, col) -> input: rotate/scale about the moved centre
            M = np.array([[ca, -sa], [sa, ca]]) / sc
            cin = np.array(fl["c"])
            cout = cin + np.array([disp[1], disp[0]])
            off = cin - M @ cout
            ta = ndimage.affine_transform(src_a, M, off, order=1, mode="constant")
            tv = ndimage.affine_transform(src_v * src_a, M, off, order=1, mode="constant")
            acc_c = tv + acc_c * (1 - ta)
            acc_a = ta + acc_a * (1 - ta)
            # flecks shed along the path
            if tau > 0:
                for _ in range(int(10 * min(tau * 3, 1))):
                    back = rng.uniform(0.0, 1.0) * tau
                    pos = cin + np.array([disp[1], disp[0]]) * (back / max(tau, 1e-3)) + rng.normal(0, 7, 2)
                    pos[0] += rng.uniform(0, 26) * tau  # flecks lag below (the flake drifts up)
                    yy_, xx_ = int(pos[0]), int(pos[1])
                    if 0 <= yy_ < n and 0 <= xx_ < n:
                        dust[yy_, xx_] += rng.uniform(0.4, 1.0) * (1 - tau) ** 0.6
        specks = np.clip(blur(dust, 1.1) * 7.0, 0, 0.9)
        a = np.clip(acc_a + specks * (1 - acc_a), 0, 1)
        v = (acc_c + specks * 0.85 * (1 - acc_a)) / np.maximum(a, 1e-6)
        a = a * (1 - 0.15 * t) * fade
        rgb = np.repeat(np.clip(v, 0, 1)[..., None], 3, axis=2)
        cells.append((down(rgb, S), down(a, S)))
    return {"grip_ash_4x4": assemble(cells, 4)}


# =================================================================== 10. gold dust flipbook


def r_gold_dust():
    C, S = 256, 2
    n = C * S
    x, y = grid(n)
    rng = np.random.default_rng(1010)
    M = 26
    rr = np.sqrt(rng.uniform(0, 1, M)) * 0.62
    aa = rng.uniform(0, TAU, M)
    mx, my = rr * np.cos(aa), rr * np.sin(aa)
    vx, vy = rng.normal(0, 0.012, M), rng.uniform(-0.035, -0.01, M)
    size = rng.uniform(0.008, 0.020, M)
    phase = rng.uniform(0, 1, M)
    star = rng.random(M) < 0.35
    star[np.argmax(size)] = True
    glen = rng.uniform(0.14, 0.28, M)
    fade = cell_fade(n, 0.80, 0.97)
    cells = []
    for f in range(4):
        a = np.zeros((n, n))
        for i in range(M):
            b = 0.5 + 0.5 * math.cos(TAU * (f / 4 + phase[i]))
            b = 0.15 + 0.85 * b ** 1.5
            cx, cy = mx[i] + vx[i] * f, my[i] + vy[i] * f
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            a += np.exp(-d2 / size[i] ** 2) * b + np.exp(-d2 / (size[i] * 4) ** 2) * 0.25 * b
            if star[i]:
                g = b ** 2
                L = glen[i] * (0.6 + 0.4 * b)
                w = 0.0045
                a += (np.exp(-((dy / w) ** 2)) * np.exp(-np.abs(dx) / (L * 0.35)) + np.exp(-((dx / w) ** 2)) * np.exp(-np.abs(dy) / (L * 0.35))) * g * 0.9
                du, dv = (dx + dy) / math.sqrt(2), (dx - dy) / math.sqrt(2)
                a += (np.exp(-((dv / w) ** 2)) * np.exp(-np.abs(du) / (L * 0.12)) + np.exp(-((du / w) ** 2)) * np.exp(-np.abs(dv) / (L * 0.12))) * g * 0.35
        a += np.exp(-((np.hypot(x, y) / 0.5) ** 2)) * 0.05
        a = np.clip(a, 0, 1) * fade
        cells.append((None, down(a, S)))
    return {"grip_gold_dust_2x2": assemble(cells, 2)}


# =================================================================== 12. shockwave


def r_shockwave():
    N = 2048
    x, y = grid(N)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    tc = (th / TAU % 1.0) * 2048  # angular column in polar noise
    rrow = r / 1.5 * 256
    streak = pnoise(256, 2048, beta=1.0, seed=1212, aniso=(1.0, 7.0))  # radial streaks
    clump = pnoise(256, 2048, beta=1.6, seed=1213, aniso=(1.0, 0.6))
    clump2 = pnoise(256, 2048, beta=1.3, seed=1214, aniso=(1.0, 0.8))
    st = samp(streak, rrow, tc)
    cl = samp(clump, rrow * 1.0, tc)
    cl2 = samp(clump2, rrow * 2.0, tc * 2.0)
    ang = lambda a: sum(np.sin(f * a + p) / f ** 0.7 for f, p in ((3, 0.3), (5, 1.7), (8, 2.9), (13, 0.8), (21, 2.2)))  # noqa: E731
    RL = 0.80 + 0.012 * ang(th) + 0.012 * cl
    thick = 0.085 * (1 + 0.40 * np.tanh(cl2))
    dd = RL - r
    front = np.exp(-((np.minimum(dd, 0) / 0.020) ** 2))
    band = np.where(dd >= 0, np.exp(-np.maximum(dd, 0) / thick), front)
    billow = np.clip(0.72 + 0.30 * cl2 + 0.12 * cl, 0.2, 1.2)
    ws = np.clip(0.5 + 0.5 * np.tanh(st * 1.4), 0, 1)
    tail = np.exp(-np.maximum(dd, 0) / 0.13) * (dd > 0) * ws ** 2 * 0.30
    wisps = np.exp(-np.maximum(dd, 0) / 0.11) * (dd > 0) * (ws ** 4) * 0.40
    lip = np.exp(-(((dd - 0.012) / 0.010) ** 2)) * 0.25 * billow
    a = band * billow * 0.9 + np.maximum(tail, wisps) * (1 - band * 0.6) + lip
    a = np.clip(a, 0, 1) * sstep(0.42, 0.70, r) * sstep(0.975, 0.90, r)
    return {"grip_shockwave": (None, down(a, 2))}


# =================================================================== 13. moon halo


def r_moon_halo():
    N = 2048
    x, y = grid(N)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    Rm = 0.34
    pxl = 2.0 / N
    rng = np.random.default_rng(1313)
    inside = np.clip(1 - (r / Rm) ** 2, 0, 1)
    mu = np.sqrt(inside)
    # surface: soft maria + grain + craters
    mar = pnoise(512, 512, beta=2.6, seed=1314)
    mar = ndimage.zoom(mar, 4, order=1)
    maria = sstep(0.1, 1.0, mar)
    grain = ndimage.zoom(pnoise(1024, 1024, beta=0.9, seed=1315), 2, order=1)
    shade = 1.0 - 0.17 * maria + 0.025 * grain
    lx, ly = -0.6, -0.8  # light from the upper left
    for _ in range(46):
        cr = rng.uniform(0.012, 0.055) * (1 if rng.random() < 0.85 else 1.6)
        pr = Rm * math.sqrt(rng.uniform(0, 0.85))
        pa = rng.uniform(0, TAU)
        cx, cy = pr * math.cos(pa), pr * math.sin(pa)
        # foreshortening near the limb
        k = 1 - (pr / Rm) ** 2 * 0.6
        dx = (x - cx)
        dy = (y - cy)
        radial = np.array([cx, cy]) / (pr + 1e-6)
        along = dx * radial[0] + dy * radial[1]
        perp = -dx * radial[1] + dy * radial[0]
        q = np.hypot(along / k, perp) / cr
        if q.min() > 1.6:
            continue
        bowl = np.exp(-(q / 0.75) ** 4)
        side = (dx * lx + dy * ly) / (cr + 1e-9)
        rim = np.exp(-(((q - 1.0) / 0.18) ** 2))
        shade += -0.10 * bowl * (1 + 0.6 * np.clip(-side, -1, 1)) + 0.07 * rim * np.clip(0.5 + 0.6 * side, 0, 1.2)
    limb = 0.72 + 0.28 * mu ** 0.6
    disc_v = np.clip(shade * limb, 0, 1.1)
    disc_a = sstep(Rm + pxl * 1.5, Rm - pxl * 1.5, r)
    disc_rgb = disc_v[..., None] * np.array([0.92, 0.95, 1.0])
    # halo + faint radiating rays + a thin far ice ring
    rays_n = pnoise(64, 1024, beta=0.8, seed=1316, aniso=(1.0, 6.0))
    rays = samp(rays_n, r * 20, (th / TAU % 1) * 1024)
    rays = np.clip(0.5 + 0.5 * np.tanh(rays * 1.3), 0, 1) ** 2
    out = np.maximum(r - Rm, 0)
    halo = 0.70 * np.exp(-out / 0.045) + 0.34 * np.exp(-out / 0.16) + 0.12 * np.exp(-out / 0.35)
    halo += rays * np.exp(-out / 0.30) * 0.22
    halo += np.exp(-(((r - 0.78) / 0.018) ** 2)) * 0.07
    halo_a = np.clip(halo, 0, 1) * sstep(0.985, 0.88, r)
    halo_rgb = np.ones((N, N, 3)) * np.array([0.82, 0.89, 1.0])
    rgb, a = over(np.zeros((N, N, 3)), np.zeros((N, N)), halo_rgb, halo_a)
    rgb, a = over(rgb, a, disc_rgb, disc_a)
    return {"grip_moon_halo": (down(rgb, 2), down(a, 2))}


# =================================================================== 14. demon shape


def r_demon_shape():
    N = 2048
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    cx = N / 2
    rng = random.Random(1414)
    # hunched torso, tapering into a smoke column
    torso = [(cx - 70, 860), (cx + 70, 860), (cx + 190, 900), (cx + 300, 960), (cx + 330, 1040), (cx + 270, 1150),
             (cx + 210, 1300), (cx + 170, 1480), (cx + 120, 1680), (cx, 1800), (cx - 120, 1680), (cx - 170, 1480),
             (cx - 210, 1300), (cx - 270, 1150), (cx - 330, 1040), (cx - 300, 960), (cx - 190, 900)]
    d.polygon(torso, fill=255)
    # head, sunk low between the shoulders, with a long pointed jaw
    d.ellipse((cx - 118, 600, cx + 118, 860), fill=255)
    d.polygon([(cx - 112, 760), (cx + 112, 760), (cx + 62, 900), (cx, 975), (cx - 62, 900)], fill=255)
    # horns: sweep out and up, curling inward at the tips
    for s in (-1, 1):
        j = rng.uniform(-10, 10)
        ctrl = [(cx + s * 60, 650), (cx + s * 160, 590 + j), (cx + s * 250, 500), (cx + s * 285, 390 + j), (cx + s * 260, 290), (cx + s * 205, 250)]
        stroke(d, catmull(ctrl, 30), 92, 4, power=0.8)
        ctrl2 = [(cx + s * 100, 735), (cx + s * 175, 715), (cx + s * 225, 670), (cx + s * 240, 625)]
        stroke(d, catmull(ctrl2, 20), 40, 3, power=0.9)
    # arms: elbows flung out low, forearms rising, hands open at head height with hooked claws curling in
    for s, lift in ((-1, 0), (1, -30)):
        arm = [(cx + s * 280, 1000), (cx + s * 470, 1060), (cx + s * 610, 1010 + lift / 2), (cx + s * 680, 860 + lift), (cx + s * 700, 720 + lift)]
        stroke(d, catmull(arm, 30), 140, 66, power=0.7)
        hx, hy = cx + s * 705, 680 + lift
        d.ellipse((hx - 62, hy - 62, hx + 62, hy + 62), fill=255)
        for fi, fa in enumerate((-160, -128, -100, -72, -40)):
            a = math.radians(fa) if s > 0 else math.pi - math.radians(fa)
            L = (230, 300, 330, 300, 200)[fi]
            bx, by = hx + math.cos(a) * 48, hy + math.sin(a) * 48
            hook = -s * 1.05 * (1 if fi < 4 else -0.6)  # fingers curl toward the head, thumb the other way
            pts = [(bx, by)]
            for k in range(1, 6):
                t = k / 5
                aa = a + hook * t ** 1.8
                pts.append((pts[-1][0] + math.cos(aa) * L / 5, pts[-1][1] + math.sin(aa) * L / 5))
            stroke(d, catmull(pts, 14), 44 if fi < 4 else 38, 2, power=1.15)
    m = down(blur(L2f(img), 3), 2)  # 1024
    n = 1024
    x, y = grid(n)
    yu = (y + 1) / 2  # 0 top .. 1 bottom
    nA = pnoise(512, 512, beta=2.0, seed=1415)
    nB = pnoise(512, 512, beta=2.0, seed=1416)
    nS = pnoise(512, 512, beta=1.3, seed=1417, aniso=(1.0, 6.0))  # vertical smoke strands
    nE = pnoise(512, 512, beta=1.3, seed=1418)
    to = lambda v: (v + 1) / 2 * 512  # noqa: E731
    low = sstep(0.55, 0.95, yu)
    wx = samp(nA, to(y), to(x), order=3) * (4 + 34 * low)
    wy = samp(nB, to(y), to(x), order=3) * (5 + 30 * low)
    rows = (y + 1) / 2 * n - 0.5 + wy
    cols = (x + 1) / 2 * n - 0.5 + wx * (1 + 1.5 * low)
    mw = ndimage.map_coordinates(m, [rows, cols], order=1, mode="constant")
    edge_n = samp(nE, to(y) * 2.0, to(x) * 2.0, order=3)
    a = sstep(0.20, 0.62, mw + 0.10 * edge_n * sstep(0.02, 0.25, mw))
    # torn upward: thin strands of shadow drawn up off the crown, horns and claws
    # (exponential upward smear, bottom-to-top recursion: no hard ends), broken into thin strands
    strands = np.clip(0.5 + 0.5 * np.tanh(samp(nS, to(y) * 0.5, to(x) * 3.0, order=3) * 2.0), 0, 1) ** 4
    sm = a.copy()
    for row in range(n - 2, -1, -1):
        sm[row] = np.maximum(sm[row], sm[row + 1] * 0.982)
    tears = blur(np.clip(sm - a, 0, 1) * strands, 1.2) * 0.55 * (1 - low)
    # dissolve the lower body into curling smoke (isotropic, swirled noise: rising smoke, not drips)
    nC = pnoise(512, 512, beta=1.7, seed=1419)
    sx = to(x) * 1.6 + 14 * samp(nA, to(y) * 2, to(x) * 2, order=3)
    sy = to(y) * 1.6 + 14 * samp(nB, to(y) * 2, to(x) * 2, order=3)
    smoke = np.clip(0.5 + 0.32 * samp(nC, sy, sx, order=3), 0, 1)
    dis = sstep(0.60, 0.90, yu)
    keep = sstep(dis * 0.95 - 0.12, dis * 0.95 + 0.12, smoke)
    a = a * ((1 - dis) + dis * keep) * (1 - 0.5 * dis)
    a = np.clip(a + tears, 0, 1)
    # hollow, slanted eye slits
    for s in (-1, 1):
        ex, ey = s * 0.085, -0.255
        ux = (x - ex) * math.cos(s * 0.42) + (y - ey) * math.sin(s * 0.42)
        uy = -(x - ex) * math.sin(s * 0.42) + (y - ey) * math.cos(s * 0.42)
        eye = np.exp(-((ux / 0.036) ** 2) - ((uy / 0.010) ** 2))
        a *= 1 - 0.92 * eye
    a *= edge_fade(n, margin=0.035) * sstep(0.985, 0.90, yu)
    inner = sstep(0.2, 0.9, blur(a, 7))
    rgb = (0.025 + 0.085 * (1 - inner))[..., None] * np.array([0.95, 0.88, 1.15])
    return {"grip_demon_shape": (rgb, a)}


# =================================================================== registry, checks, sheet, json

RENDER = {
    "priest_runes": r_priest_runes,
    "lifethread_v": r_lifethread,
    "ink_smoke_4x4": r_ink_smoke,
    "ink_tendril_v": r_ink_tendril,
    "claw_slash": r_claw_slash,
    "slash_spark_2x2": r_slash_spark,
    "frost_floor": r_frost_floor,
    "grave_cracks": r_grave_cracks,
    "ash_4x4": r_ash,
    "gold_dust_2x2": r_gold_dust,
    "soul_streak_v": r_soul_streak,
    "shockwave": r_shockwave,
    "moon_halo": r_moon_halo,
    "demon_shape": r_demon_shape,
}

INFO = {
    "grip_priest_runes": dict(kind="decal", size=[1024, 1024], tint="#EBCD78", purpose="Priest finisher: holy seal circle on the floor (rings, invented liturgical glyph band, cross-shaped star, filigree).", usage="Decal (Face Top) or SurfaceGui ImageLabel on a thin flat part under the target; tint via Color3; spin slowly; tween Transparency in/out."),
    "grip_lifethread_v": dict(kind="beam", size=[256, 1024], tint="#F4D6DE", purpose="Life-drain thread: braided luminous strands + soft core between grabber and victim.", usage="Beam.Texture, TextureMode Wrap (or Stretch), TextureLength 4-8, TextureSpeed 1-2, LightEmission 1, Width 0.4-1.2, Color tint; tiles along the beam, alpha 0 at both sides."),
    "grip_ink_smoke_4x4": dict(kind="flipbook", size=[1024, 1024], layout="Grid4x4", tint=None, baked="near-black RGB", purpose="Boiling black ink-smoke puff that billows and dissolves (16 frames).", usage="ParticleEmitter FlipbookLayout Grid4x4, FlipbookMode OneShot, Lifetime 0.8-1.4, Color white (art is baked dark), LightEmission 0, LightInfluence 0-0.3, Size 2-6, Rotation random."),
    "grip_ink_tendril_v": dict(kind="beam", size=[256, 1024], tint=None, baked="near-black RGB", purpose="Clawing dark ink tendril with hooked thorns and smoke wisps.", usage="Beam.Texture, TextureMode Wrap, TextureLength 3-6, TextureSpeed 0.5-1.5, Color white (baked dark), LightEmission 0, Width 0.8-2, CurveSize0/1 for a reaching arc; alpha 0 at both sides."),
    "grip_claw_slash": dict(kind="sprite", size=[1024, 1024], tint="#DDE3EE", purpose="Werewolf finisher: three curved claw-rake slash smears (hot core, glow, motion smear).", usage="ParticleEmitter single burst (Rate 0, Emit 1), Lifetime 0.2-0.35, Size 5-9 shrinking/stretching, LightEmission 1, Orientation FacingCamera or VelocityPerpendicular; or a BillboardGui ImageLabel tweened."),
    "grip_slash_spark_2x2": dict(kind="flipbook", size=[512, 512], layout="Grid2x2", tint="#DDE3EE", purpose="Silver impact spark/flare popping and fading (4 frames).", usage="ParticleEmitter FlipbookLayout Grid2x2, FlipbookMode OneShot, Lifetime 0.15-0.3, Emit 1-3, Size 2-4, LightEmission 1, random Rotation."),
    "grip_frost_floor": dict(kind="decal", size=[1024, 1024], tint="#BFE6FF", purpose="Wraith finisher: circular frost bloom with branching ice dendrites, seen from above.", usage="Decal (Face Top) on a thin flat part, grow by tweening the part Size from 0.2x to 1x, then fade Transparency; Color tint."),
    "grip_grave_cracks": dict(kind="decal", size=[1024, 1024], tint=None, baked="dark grey-black RGB", purpose="Ghoul finisher: radial cracked-stone fracture decal.", usage="Decal (Face Top) on a thin flat part, Color white (baked dark); stack grip_grave_cracks_glow on a second decal just above it."),
    "grip_grave_cracks_glow": dict(kind="decal", size=[1024, 1024], tint="#8FBF6A", purpose="Glow channels inside the grave cracks (white mask, same layout as grip_grave_cracks).", usage="Second Decal on a part 0.01 stud above the cracks decal, Color #8FBF6A, pulse Transparency 0.2-0.6; same size and position as the cracks."),
    "grip_ash_4x4": dict(kind="flipbook", size=[1024, 1024], layout="Grid4x4", tint="#BDB8B0", purpose="Ash flake cluster crumbling apart into drifting flecks (16 frames).", usage="ParticleEmitter FlipbookLayout Grid4x4, FlipbookMode OneShot, Lifetime 1-2, Size 1-3, Acceleration slightly up, LightEmission 0, Color tint."),
    "grip_gold_dust_2x2": dict(kind="flipbook", size=[512, 512], layout="Grid2x2", tint="#EBCD78", purpose="Twinkling holy motes with tiny 4-point star glints (4 looping frames).", usage="ParticleEmitter FlipbookLayout Grid2x2, FlipbookMode Loop, FlipbookFramerate 6-10, Lifetime 1-2, Size 1.5-3, LightEmission 1, Color tint."),
    "grip_soul_streak_v": dict(kind="beam", size=[256, 1024], tint="#AAD8FF", purpose="Spectral spiralling soul streak with abstract ghostly smears.", usage="Beam.Texture, TextureMode Wrap, TextureLength 6-10, TextureSpeed 1.5-3, LightEmission 1, Width 1-2.5, Color tint; alpha 0 at both sides."),
    "grip_shockwave": dict(kind="decal", size=[1024, 1024], tint="#CFC8BA", purpose="Soft dust/air shockwave ring (thick leading edge, wispy trailing inside) for an expanding ground ring.", usage="Decal (Face Top) on a thin flat part; tween Size up 4-6x over 0.4-0.7 s (Quint Out) while Transparency goes 0.2 -> 1."),
    "grip_moon_halo": dict(kind="sprite", size=[1024, 1024], tint=None, baked="pale cool white RGB", purpose="Pale full moon disc with soft craters, a halo and faint radiating rays.", usage="BillboardGui ImageLabel or ParticleEmitter (Emit 1, long Lifetime), Color white (baked), LightEmission 0.3-1; fade in behind the finisher."),
    "grip_demon_shape": dict(kind="sprite", size=[1024, 1024], tint=None, baked="near-black RGB", purpose="Abstract shadow-demon silhouette (horned smoky head, clawed reaching arms) torn upward, dissolving into smoke.", usage="ParticleEmitter (Emit 1, Lifetime 0.8-1.5, Size 8-14 growing, Acceleration up, Transparency 1 -> 0.1 -> 1) or a BillboardGui ImageLabel; Color white (baked dark), LightEmission 0."),
}


def check(name, img):
    a = np.asarray(img)[..., 3].astype(int)
    h, w = a.shape
    info = INFO[name]
    msg = []
    if info["kind"] == "beam":
        msg.append(f"side cols max a={max(a[:, :2].max(), a[:, -2:].max())}")
        seam = np.abs(a[0] - a[-1]).mean()
        adj = np.abs(np.diff(a, axis=0)).mean()
        msg.append(f"seam {seam:.2f} vs adjacent-row {adj:.2f}")
    else:
        g = {"Grid4x4": 4, "Grid2x2": 2}.get(info.get("layout"), 1)
        cw = w // g
        worst = 0
        for k in range(g + 1):
            for off in (-2, -1, 0, 1):
                p = k * cw + off
                if 0 <= p < w:
                    worst = max(worst, a[:, p].max(), a[p, :].max())
        msg.append(f"cell-edge max a={worst}")
    return ", ".join(msg)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def preview_tile(name, box, bg=(44, 44, 50)):
    """composite one texture (tinted if white art) over the background, fitted into box (w, h)."""
    im = Image.open(os.path.join(HERE, name + ".png")).convert("RGBA")
    arr = np.asarray(im).astype(float) / 255
    tint = INFO[name].get("tint")
    rgb = arr[..., :3] * (hexrgb(tint) if tint else 1.0)
    a = arr[..., 3:4]
    bgc = np.array(bg) / 255
    out = rgb * a + bgc * (1 - a)
    tile = Image.fromarray(np.round(out * 255).astype(np.uint8), "RGB")
    if INFO[name]["kind"] == "beam":  # show 3 repeats, rotated so the beam runs left-right (shows seams)
        rep = Image.new("RGB", (tile.width, tile.height * 3))
        for k in range(3):
            rep.paste(tile, (0, k * tile.height))
        tile = rep.transpose(Image.Transpose.ROTATE_90)
    tile.thumbnail(box, Image.LANCZOS)
    return tile


def contact_sheet():
    os.makedirs(PREV, exist_ok=True)
    cell = 340
    cols = 5
    squares = [k for k, v in INFO.items() if v["kind"] != "beam"]
    beams = [k for k, v in INFO.items() if v["kind"] == "beam"]
    rows = math.ceil((len(squares) + 1) / cols)
    bh = 150
    Wd = cols * cell
    Ht = rows * (cell + 24) + len(beams) * (bh + 24) + 10
    sheet = Image.new("RGB", (Wd, Ht), (30, 30, 34))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    items = squares + ["__composite__"]
    for i, nm in enumerate(items):
        r, k = divmod(i, cols)
        x0, y0 = k * cell, r * (cell + 24)
        if nm == "__composite__":
            base = preview_tile("grip_grave_cracks", (cell - 12, cell - 12))
            gl = Image.open(os.path.join(HERE, "grip_grave_cracks_glow.png")).convert("RGBA").resize(base.size, Image.LANCZOS)
            ga = np.asarray(gl).astype(float)[..., 3:4] / 255 * 0.85
            out = np.asarray(base).astype(float) / 255 * (1 - ga) + hexrgb("#8FBF6A") * ga
            tile = Image.fromarray(np.round(np.clip(out, 0, 1) * 255).astype(np.uint8))
            label = "cracks + glow (composite)"
        else:
            tile = preview_tile(nm, (cell - 12, cell - 12))
            label = nm
        sheet.paste(tile, (x0 + (cell - tile.width) // 2, y0 + 6))
        d.text((x0 + 8, y0 + cell + 2), label, fill=(200, 200, 205), font=font)
    y = rows * (cell + 24) + 4
    for nm in beams:
        tile = preview_tile(nm, (Wd - 20, bh))
        sheet.paste(tile, (10, y))
        d.text((12, y + tile.height + 2), nm + "  (3 tiles, beam axis left-right)", fill=(200, 200, 205), font=font)
        y += bh + 24
    path = os.path.join(PREV, "contact_sheet.png")
    sheet.save(path)
    print("sheet:", path)


def write_json():
    data = {"_note": "Racial-grip finisher textures from make_grip_sprites.py (offline numpy render). White art is tinted in Roblox via Color; 'baked' entries carry their own RGB and should use Color white. Fill in the ids after upload.", "files": {}}
    for nm, v in INFO.items():
        e = {"file": nm + ".png", "id": None}
        e.update({k: v[k] for k in v})
        data["files"][nm] = e
    with open(os.path.join(HERE, "sprites.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def main(argv):
    if "--list" in argv:
        print("\n".join(RENDER))
        return
    if "--sheet" in argv:
        contact_sheet()
        return
    names = [a.replace("grip_", "") for a in argv if not a.startswith("-")] or list(RENDER)
    for nm in names:
        if nm == "grave_cracks_glow":
            nm = "grave_cracks"
        if nm not in RENDER:
            raise SystemExit(f"unknown name {nm!r}; use --list")
        out = RENDER[nm]()
        for fname, (rgb, a) in out.items():
            img = to_image(rgb, a)
            img.save(os.path.join(HERE, fname + ".png"), optimize=True)
            print(f"{fname}.png {img.size}  {check(fname, img)}")
    write_json()
    if all(os.path.exists(os.path.join(HERE, k + ".png")) for k in INFO):
        contact_sheet()


if __name__ == "__main__":
    main(sys.argv[1:])
