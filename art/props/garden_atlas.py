"""The garden kit's painted maps (props batch 40, the courtyard / garden kit). Run with the system Python (PIL + numpy + scipy):

  python art/props/garden_atlas.py

NH_GardenLeaves    a 4 x 4 atlas of alpha-cut foliage sprites (2048; 512 a cell) for the kit's leaf cards: ivy, hedge leaves, yew,
                   willow, crimson roses, rose leaves (no blooms, for the modelled roses), wisteria, a fern frond, lavender, tall grass, bramble, crabapple,
                   nightshade, poppies, moonflowers and bare thorny twigs. The colour map carries the cut-out in its alpha
                   (Roblox SurfaceAppearance AlphaMode = Transparency); its colour is bled out past the edges so mip levels
                   don't fringe. Also _normal (OpenGL, green up), _rough and _metal (black).
NH_GardenBark      a seamless bark set (1024; furrowed grey-brown bark, lichen and moss), the trees' and the scarecrow's wood
                   (a bake source: box-projected like the school's other sets)
MoonRoundelInlay   the PathMoonRoundel's mosaic (2048, a square that the inlay disc fills): a crescent moon cradling the school
                   crest in slate, brass, limestone and a little crimson, a field of brass stars, a wave-scroll border. Laid
                   as tesserae with grout. _color, _normal, _rough, _metal.

Writes art/props/textures/<Name>_{color,normal,rough,metal}.png and art/props/garden_atlas.json (each sprite's UV rect
[u0, v0, u1, v1], v up as Blender reads images, and where its stem or base sits). Everything is original and procedural.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
A = 2048
CELL = 512


def srgb(c):
    return np.array(c, np.float32) / 255.0


class Canvas:
    """Colour, coverage, height and roughness layers; stamps are painted back to front."""

    def __init__(self, n):
        self.n = n
        self.C = np.zeros((n, n, 3), np.float32)
        self.A = np.zeros((n, n), np.float32)
        self.H = np.zeros((n, n), np.float32)
        self.R = np.full((n, n), 0.6, np.float32)
        self.M = np.zeros((n, n), np.float32)

    def put(self, y0, x0, mask, col, h, rough, metal=0.0):
        """Paint `mask` (h x w, 0..1) at pixel (y0, x0): colour col (h x w x 3 or 3), height h, roughness."""
        hh, ww = mask.shape
        y1, x1 = y0 + hh, x0 + ww
        cy0, cx0 = max(0, y0), max(0, x0)
        cy1, cx1 = min(self.n, y1), min(self.n, x1)
        if cy1 <= cy0 or cx1 <= cx0:
            return
        sl = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
        m = mask[sl]
        dst = (slice(cy0, cy1), slice(cx0, cx1))
        c = col[sl] if np.ndim(col) == 3 else np.broadcast_to(np.asarray(col, np.float32), m.shape + (3,))
        self.C[dst] = self.C[dst] * (1 - m[..., None]) + c * m[..., None]
        hv = h[sl] if np.ndim(h) == 2 else np.full(m.shape, h, np.float32)
        self.H[dst] = self.H[dst] * (1 - m) + hv * m
        self.R[dst] = self.R[dst] * (1 - m) + rough * m
        self.M[dst] = self.M[dst] * (1 - m) + metal * m
        self.A[dst] = np.maximum(self.A[dst], m)


# ------------------------------------------------------------------ stamps

def _grid(x0, y0, x1, y1):
    xs = np.arange(int(math.floor(x0)), int(math.ceil(x1)) + 1, dtype=np.float32)
    ys = np.arange(int(math.floor(y0)), int(math.ceil(y1)) + 1, dtype=np.float32)
    X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
    return int(xs[0]), int(ys[0]), X, Y


def blade(cv, ox, oy, bx, by, ang, L, W, colb, colt, shape="lance", z=0.5, serr=0.0, vein=0.25, rough=0.55, fold=0.3,
          curve=0.0, noise=0.08, rng=None):
    """A leaf or blade from its base (bx, by) (cell px; ox, oy the cell's corner) pointing at `ang` (radians, 0 = up the image),
    L long, W wide at its widest; curve bends it sideways (px at the tip)."""
    dx, dy = math.sin(ang), -math.cos(ang)
    px, py = -dy, dx
    ex, ey = bx + dx * L + px * curve, by + dy * L + py * curve
    pad = W + abs(curve) + 3
    gx, gy, X, Y = _grid(min(bx, ex) - pad + ox, min(by, ey) - pad + oy, max(bx, ex) + pad + ox, max(by, ey) + pad + oy)
    rx, ry = X - (bx + ox), Y - (by + oy)
    s = (rx * dx + ry * dy) / L
    sc = np.clip(s, 0, 1)
    t = rx * px + ry * py - curve * sc * sc
    if shape == "lance":
        w = W * np.clip(np.sin(np.pi * sc), 0, 1) ** 0.75 * (1 - 0.35 * sc)
    elif shape == "oval":
        w = W * np.sqrt(np.clip(np.sin(np.pi * sc), 0, 1)) * (1 - 0.15 * sc)
    elif shape == "strap":            # grass: broad at the base, tapering to a point
        w = W * np.clip(1 - sc, 0, 1) ** 0.6
    elif shape == "drop":             # rounded tip, pointed base (petals)
        w = W * np.sin(np.pi * np.clip(sc, 0, 1) * 0.5 + 0.0) ** 0.6 * np.clip(1.15 - sc, 0, 1) ** 0.25 * np.sqrt(np.clip(1 - sc, 0, 1)) * 1.4
    else:
        w = W * np.ones_like(sc)
    if serr:
        w = w * (1 - serr * np.abs(((s * L / max(3.0, W * 0.6)) % 1.0) - 0.5) * 2)
    inside = (w - np.abs(t))
    m = np.clip(inside + 0.5, 0, 1) * np.clip(s * L + 0.5, 0, 1) * np.clip((1 - s) * L + 0.5, 0, 1)
    if not m.any():
        return
    tn = np.clip(np.abs(t) / np.maximum(w, 0.5), 0, 1)
    k = sc[..., None]
    col = srgb(colb)[None, None, :] * (1 - k) + srgb(colt)[None, None, :] * k
    shade = 0.82 + 0.25 * (1 - tn) - 0.12 * (tn > 0.85)
    if rng is not None and noise:
        shade = shade * (1 + (rng.random(shade.shape).astype(np.float32) - 0.5) * noise)
    col = col * shade[..., None]
    if vein:
        v = np.clip(1.2 - np.abs(t) / 0.9, 0, 1) * (sc < 0.92)
        col = col * (1 - v[..., None] * 0.0) + (col * 0.6 + 0.4 * srgb((200, 210, 150))) * (v[..., None] * vein)
    h = z + (1 - tn ** 2) * 0.12 + tn * fold * 0.1 - (np.abs(t) < 0.8) * 0.03
    cv.put(gy, gx, m, col, h, rough)


def polar(cv, ox, oy, cx, cy, R, rfun, colc, cole, z=0.5, rough=0.5, dome=0.15, veins=0, vein_col=None, rot=0.0, metal=0.0, rng=None,
          noise=0.06):
    """A shape r(theta) round (cx, cy): ivy leaves, petals, berries. Colour runs from colc at the centre to cole at the edge."""
    gx, gy, X, Y = _grid(cx + ox - R - 2, cy + oy - R - 2, cx + ox + R + 2, cy + oy + R + 2)
    rx, ry = X - (cx + ox), Y - (cy + oy)
    rr = np.hypot(rx, ry)
    th = (np.arctan2(rx, -ry) - rot + np.pi) % (2 * np.pi) - np.pi
    edge = R * rfun(th)
    m = np.clip(edge - rr + 0.5, 0, 1)
    if not m.any():
        return
    k = np.clip(rr / np.maximum(edge, 0.5), 0, 1)
    col = srgb(colc)[None, None, :] * (1 - k[..., None]) + srgb(cole)[None, None, :] * k[..., None]
    if rng is not None and noise:
        col = col * (1 + (rng.random(k.shape).astype(np.float32)[..., None] - 0.5) * noise)
    if veins:
        a = (th * veins / (2 * np.pi)) % 1.0
        v = np.clip(1 - np.abs(a - 0.5) * 2 * rr / 1.2, 0, 1) * (k < 0.85)
        col = col * (1 - v[..., None] * 0.5) + srgb(vein_col or (170, 190, 130))[None, None, :] * v[..., None] * 0.5
    h = z + np.sqrt(np.clip(1 - k ** 2, 0, 1)) * dome
    cv.put(gy, gx, m, col, h, rough, metal)


def stem(cv, ox, oy, pts, w0, w1, col, z=0.3, rough=0.7, thorns=0, thorn_col=None, rng=None):
    """A stem along a polyline, w0 wide at its start tapering to w1."""
    n = len(pts) - 1
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        wa = w0 + (w1 - w0) * i / n
        wb = w0 + (w1 - w0) * (i + 1) / n
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 0.5:
            continue
        ang = math.atan2(x1 - x0, -(y1 - y0))
        blade(cv, ox, oy, x0, y0, ang, L + wb * 0.5, (wa + wb) / 4, col, col, shape="rect", z=z, vein=0, rough=rough, fold=0, rng=rng)
        if thorns and rng is not None:
            for _ in range(thorns):
                t = rng.random()
                tx, ty = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                side = 1 if rng.random() < 0.5 else -1
                blade(cv, ox, oy, tx, ty, ang + side * 1.1, wa * 1.6 + 3, wa * 0.45 + 1, thorn_col or col, (200, 170, 140), shape="strap",
                      z=z, vein=0, rough=0.5, rng=rng)


def curve_pts(p0, p1, p2, n=12):
    """A quadratic bezier from p0 through control p1 to p2."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def jit(c, rng, k=18):
    return tuple(max(0, min(255, v + rng.integers(-k, k + 1))) for v in c)


# ------------------------------------------------------------------ the sprites (each drawn in a 512 cell; (ox, oy) its corner)

GREENS = [(52, 84, 40), (44, 74, 36), (60, 94, 44), (38, 64, 32), (68, 100, 46)]


def ivy_leaf(cv, ox, oy, x, y, R, rot, rng, z):
    def rf(th):
        a = np.abs(th)
        lobes = np.maximum(np.maximum(np.exp(-a ** 2 / 0.16), 0.78 * np.exp(-(a - 1.15) ** 2 / 0.12)), 0.6 * np.exp(-(a - 2.05) ** 2 / 0.14))
        return 0.36 + 0.64 * lobes
    polar(cv, ox, oy, x, y, R, rf, jit((50, 84, 40), rng), jit((26, 48, 24), rng), z=z, rough=0.4, dome=0.1, veins=5,
          vein_col=(150, 170, 120), rot=rot, rng=rng)


def s_ivy(cv, ox, oy, rng):
    for _ in range(3):
        a = (rng.uniform(20, 480), 500)
        b = (rng.uniform(40, 470), rng.uniform(200, 320))
        c = (rng.uniform(20, 490), 10)
        pts = curve_pts(a, b, c, 14)
        stem(cv, ox, oy, pts, 5, 3, (70, 52, 36), z=0.2, rng=rng)
    for i in range(64):
        x, y = rng.uniform(40, 472), rng.uniform(40, 472)
        ivy_leaf(cv, ox, oy, x, y, rng.uniform(38, 56), rng.uniform(-0.9, 0.9) + (math.pi if rng.random() < 0.25 else 0), rng, 0.3 + i * 0.01)


def leafy_blob(cv, ox, oy, rng, n, cx, cy, R, L, W, greens, tips=None, shape="oval", serr=0.0, new=0.12):
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = R * math.sqrt(rng.random()) * (0.85 + 0.15 * math.sin(a * 5 + 1.3))
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        g = greens[rng.integers(len(greens))]
        if rng.random() < new:
            g = (g[0] + 30, g[1] + 34, g[2] + 6)
        tip = tips or (g[0] - 8, g[1] - 10, g[2] - 6)
        blade(cv, ox, oy, x, y, rng.uniform(0, 2 * math.pi), rng.uniform(L * 0.75, L * 1.25), W * rng.uniform(0.8, 1.2), jit(g, rng, 10), tip,
              shape=shape, z=0.2 + i / n * 0.6, serr=serr, vein=0.2, rough=0.68, rng=rng)


def s_hedge(cv, ox, oy, rng):
    for k in range(4):
        stem(cv, ox, oy, curve_pts((256, 500), (256 + rng.uniform(-150, 150), 330), (rng.uniform(80, 430), rng.uniform(90, 200)), 8), 5, 2,
             (60, 46, 34), z=0.1, rng=rng)
    leafy_blob(cv, ox, oy, rng, 620, 256, 256, 245, 30, 9, [(40, 70, 34), (34, 62, 30), (48, 80, 38), (30, 54, 28)], new=0.1)


def s_yew(cv, ox, oy, rng):
    for k in range(7):
        a0 = -1.1 + k * 0.37 + rng.uniform(-0.1, 0.1)
        L = rng.uniform(330, 470)
        p0 = (256 + rng.uniform(-20, 20), 505)
        p2 = (256 + math.sin(a0) * L, 505 - math.cos(a0) * L)
        p1 = ((p0[0] + p2[0]) / 2 + rng.uniform(-40, 40), (p0[1] + p2[1]) / 2)
        pts = curve_pts(p0, p1, p2, 18)
        stem(cv, ox, oy, pts, 4, 2, (78, 56, 40), z=0.2, rng=rng)
        for i in range(2, len(pts) - 1):
            x, y = pts[i]
            ang = math.atan2(pts[i + 1][0] - x, -(pts[i + 1][1] - y))
            for side in (-1, 1):
                for j in range(3):
                    blade(cv, ox, oy, x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), ang + side * rng.uniform(0.9, 1.4), rng.uniform(20, 30), 3.2,
                          jit((30, 58, 40), rng, 8), (22, 44, 32), shape="lance", z=0.3 + i * 0.01, vein=0.3, rough=0.45, rng=rng)


def s_willow(cv, ox, oy, rng):
    """Eight long thin fronds of willow hanging from the top edge, each a whippy stem of narrow leaves that get smaller and
    sparser to a fine point; lengths vary (a ragged hem); dark green leaves with some turned to show their silvery undersides."""
    for k in range(8):
        x0 = 36 + k * 62 + rng.uniform(-14, 14)
        L = rng.uniform(300, 505)
        sway = rng.uniform(-28, 28)
        pts = curve_pts((x0, 2), (x0 + sway * 0.4, L * 0.5), (x0 + sway, L), 26)
        stem(cv, ox, oy, pts, 2.2, 0.8, (88, 84, 50), z=0.2, rng=rng)
        for i in range(1, len(pts)):
            x, y = pts[i]
            t = i / (len(pts) - 1)
            size = 1.0 - 0.65 * t
            for j in range(2 if t < 0.8 else 1):
                side = 1 if (i + j) % 2 else -1
                silver = rng.random() < 0.28
                cb = jit((150, 162, 140), rng, 10) if silver else jit((44, 74, 36), rng, 10)
                ct = (130, 146, 126) if silver else (34, 62, 30)
                blade(cv, ox, oy, x + rng.uniform(-2, 2), y + rng.uniform(-6, 6), math.pi + side * rng.uniform(0.12, 0.42), rng.uniform(30, 44) * size, 3.4 * size + 0.6,
                      cb, ct, shape="lance", z=0.3 + k * 0.02 + i * 0.001, vein=0.25, rough=0.5 if not silver else 0.4, curve=rng.uniform(-6, 6), rng=rng)


def rose_leaves(cv, ox, oy, rng, n, greens):
    for i in range(n):
        x, y = rng.uniform(30, 482), rng.uniform(30, 482)
        a = rng.uniform(0, 2 * math.pi)
        stem(cv, ox, oy, [(x, y), (x + math.sin(a) * 50, y - math.cos(a) * 50)], 2.5, 2, (70, 50, 34), z=0.2 + i * 0.002, rng=rng)
        for j, (da, dl) in enumerate(((0, 50), (-0.8, 30), (0.8, 30), (-0.9, 12), (0.9, 12))):
            bx, by = x + math.sin(a) * dl, y - math.cos(a) * dl
            g = greens[rng.integers(len(greens))]
            blade(cv, ox, oy, bx, by, a + da, rng.uniform(32, 42), 12, jit(g, rng, 8), (g[0] - 10, g[1] - 14, g[2] - 6), shape="oval",
                  z=0.25 + i * 0.004, serr=0.35, vein=0.15, rough=0.65, rng=rng)


def rose_bloom(cv, ox, oy, x, y, R, outer, inner, rng, z):
    for ring in range(5):
        r = R * (1 - ring * 0.18)
        k = ring / 4
        c0 = tuple(int(outer[i] * (1 - k) + inner[i] * k) for i in range(3))
        c1 = tuple(int(v * 0.55) for v in c0)
        rot = rng.uniform(0, 6.28)
        npet = 5 if ring < 2 else 4

        def rf(th, npet=npet):
            return 0.78 + 0.22 * np.abs(np.cos(th * npet / 2))
        polar(cv, ox, oy, x, y, r, rf, c0, c1, z=z + ring * 0.04, rough=0.72, dome=0.12, rot=rot, rng=rng)
    polar(cv, ox, oy, x, y, R * 0.18, lambda th: 0.8 + 0.2 * np.cos(th * 3), tuple(int(v * 0.4) for v in inner), tuple(int(v * 0.25) for v in inner),
          z=z + 0.25, rough=0.6, dome=0.05, rng=rng)


def s_roses(cv, ox, oy, rng, outer, inner):
    leafy_blob(cv, ox, oy, rng, 260, 256, 256, 235, 34, 12, [(36, 64, 32), (30, 56, 28), (42, 72, 36)], serr=0.3, new=0.05)
    rose_leaves(cv, ox, oy, rng, 26, [(42, 74, 36), (36, 64, 32), (50, 82, 40)])
    for i in range(8):
        x, y = rng.uniform(70, 442), rng.uniform(70, 442)
        rose_bloom(cv, ox, oy, x, y, rng.uniform(46, 62), outer, inner, rng, 0.6 + i * 0.03)
    for i in range(7):      # buds: a closed bloom in green sepals
        x, y = rng.uniform(40, 472), rng.uniform(40, 472)
        a = rng.uniform(-0.6, 0.6)
        for da in (-0.5, 0.5):
            blade(cv, ox, oy, x, y + 8, a + da, 22, 5, (40, 70, 34), (54, 86, 40), shape="lance", z=0.55, vein=0, rough=0.6, rng=rng)
        blade(cv, ox, oy, x, y + 6, a, 26, 9, inner, outer, shape="oval", z=0.6, vein=0, rough=0.7, rng=rng)


def s_wisteria(cv, ox, oy, rng):
    for i in range(16):
        x, y = rng.uniform(10, 500), rng.uniform(0, 90)
        blade(cv, ox, oy, x, y, math.pi + rng.uniform(-1.2, 1.2), rng.uniform(34, 50), 9, jit((76, 108, 50), rng), (60, 92, 42), shape="lance",
              z=0.2, vein=0.3, rng=rng)
    for k in range(7):
        x0 = 40 + k * 72 + rng.uniform(-12, 12)
        L = rng.uniform(330, 470)
        sway = rng.uniform(-30, 30)
        stem(cv, ox, oy, curve_pts((x0, 4), (x0 + sway * 0.3, L * 0.5), (x0 + sway, L), 10), 3, 1.5, (88, 78, 60), z=0.25, rng=rng)
        nfl = 190
        for j in range(nfl):
            t = (j / nfl) ** 0.9
            yy = 20 + t * L
            wid = 40 * (1 - t) ** 0.8 + 6
            xx = x0 + sway * t * t + rng.uniform(-wid, wid) * 0.9
            top = (196, 168, 230)
            mid = (138, 96, 196)
            tip = (86, 52, 150)
            c = tuple(int(top[i] * (1 - t) ** 2 + mid[i] * 2 * t * (1 - t) + tip[i] * t * t) for i in range(3))
            polar(cv, ox, oy, xx, yy, rng.uniform(9, 13) * (1 - t * 0.45), lambda th: 0.72 + 0.28 * np.abs(np.cos(th)), jit(c, rng, 12),
                  tuple(int(v * 0.6) for v in c), z=0.35 + t * 0.2 + j * 0.001, rough=0.55, dome=0.08, rot=rng.uniform(0, 3), rng=rng)


def s_fern(cv, ox, oy, rng):
    pts = curve_pts((256, 508), (240, 260), (300, 14), 40)
    stem(cv, ox, oy, pts, 5, 1.5, (70, 88, 40), z=0.2, rng=rng)
    for i in range(3, len(pts) - 1, 2):
        x, y = pts[i]
        t = i / len(pts)
        ang = math.atan2(pts[i + 1][0] - x, -(pts[i + 1][1] - y))
        L = 140 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7 + 12
        for side in (-1, 1):
            blade(cv, ox, oy, x + side * 2, y, ang + side * (1.2 - t * 0.5), L, 10 * (1 - t * 0.5) + 3, jit((58, 104, 42), rng, 8), (46, 88, 34),
                  shape="lance", z=0.3 + i * 0.005, serr=0.7, vein=0.35, rough=0.5, curve=-side * L * 0.12, rng=rng)


def s_lavender(cv, ox, oy, rng):
    for k in range(22):
        a = rng.uniform(-0.45, 0.45)
        L = rng.uniform(330, 490)
        x0 = 256 + rng.uniform(-30, 30)
        ex, ey = x0 + math.sin(a) * L, 508 - math.cos(a) * L
        pts = curve_pts((x0, 508), ((x0 + ex) / 2 + rng.uniform(-20, 20), (508 + ey) / 2), (ex, ey), 10)
        stem(cv, ox, oy, pts, 2.6, 1.6, (110, 124, 92), z=0.2 + k * 0.01, rng=rng)
        for j in range(16):
            t = 0.62 + 0.38 * j / 15
            idx = min(len(pts) - 1, int(t * (len(pts) - 1)))
            x, y = pts[idx]
            for _ in range(3):
                polar(cv, ox, oy, x + rng.uniform(-7, 7), y + rng.uniform(-6, 6), rng.uniform(4, 6.5), lambda th: np.ones_like(th),
                      jit((132, 98, 196), rng, 14), (84, 58, 140), z=0.4 + k * 0.01, rough=0.6, dome=0.06, rng=rng)
    for k in range(18):
        blade(cv, ox, oy, 256 + rng.uniform(-60, 60), 508, rng.uniform(-0.9, 0.9), rng.uniform(70, 130), 4, (120, 136, 104), (100, 118, 88),
              shape="strap", z=0.5, vein=0.2, rng=rng)


def s_grass(cv, ox, oy, rng):
    for k in range(70):
        x0 = 256 + rng.normal(0, 70)
        a = rng.normal(0, 0.32)
        L = rng.uniform(220, 495)
        g = [(70, 104, 48), (84, 116, 52), (98, 112, 58), (120, 116, 66), (60, 92, 44)][rng.integers(5)]
        blade(cv, ox, oy, x0, 510, a, L, rng.uniform(5, 9), jit(g, rng, 10), (g[0] + 30, g[1] + 16, g[2] + 6), shape="strap", z=0.2 + k * 0.008,
              vein=0.25, rough=0.55, curve=rng.uniform(-60, 60), rng=rng)
    for k in range(7):
        a = rng.normal(0, 0.25)
        L = rng.uniform(380, 500)
        x0 = 256 + rng.normal(0, 50)
        ex, ey = x0 + math.sin(a) * L, 510 - math.cos(a) * L
        stem(cv, ox, oy, [(x0, 510), (ex, ey)], 2, 1.5, (130, 124, 80), z=0.8, rng=rng)
        for j in range(14):
            t = 0.8 + 0.2 * j / 13
            blade(cv, ox, oy, x0 + (ex - x0) * t, 510 + (ey - 510) * t, a + rng.uniform(-0.6, 0.6), 16, 3.5, (168, 152, 96), (196, 180, 120),
                  shape="oval", z=0.85, vein=0, rng=rng)


def s_bramble(cv, ox, oy, rng):
    for k in range(7):
        p0 = (rng.uniform(0, 512), 510)
        p1 = (rng.uniform(0, 512), rng.uniform(-60, 150))
        p2 = (rng.uniform(0, 512), rng.uniform(260, 510))
        pts = curve_pts(p0, p1, p2, 24)
        stem(cv, ox, oy, pts, 8, 4, (62, 30, 36), z=0.3 + k * 0.05, thorns=1, thorn_col=(120, 84, 70), rng=rng)
        for i in range(2, len(pts) - 1, 3):
            x, y = pts[i]
            a = rng.uniform(0, 6.28)
            for da in (0, -0.9, 0.9):
                blade(cv, ox, oy, x, y, a + da, rng.uniform(38, 52), 15, jit((50, 76, 38), rng), (64, 60, 40), shape="oval", z=0.35 + k * 0.05,
                      serr=0.4, vein=0.3, rough=0.5, rng=rng)
    for k in range(9):
        x, y = rng.uniform(40, 472), rng.uniform(40, 472)
        ripe = rng.random() < 0.7
        for j in range(14):
            a, r = rng.uniform(0, 6.28), rng.uniform(0, 11)
            c = (30, 14, 30) if ripe else (150, 30, 36)
            polar(cv, ox, oy, x + math.cos(a) * r, y + math.sin(a) * r, 6.5, lambda th: np.ones_like(th), (c[0] + 60, c[1] + 40, c[2] + 60), c,
                  z=0.7, rough=0.25, dome=0.15, rng=rng)


def s_crabapple(cv, ox, oy, rng):
    for k in range(5):
        p0 = (256 + rng.uniform(-60, 60), 512)
        p2 = (rng.uniform(20, 490), rng.uniform(20, 200))
        pts = curve_pts(p0, ((p0[0] + p2[0]) / 2 + rng.uniform(-80, 80), 300), p2, 14)
        stem(cv, ox, oy, pts, 7, 2.5, (66, 52, 44), z=0.2, rng=rng)
    leafy_blob(cv, ox, oy, rng, 160, 256, 240, 230, 46, 15, [(56, 86, 40), (48, 76, 36), (64, 92, 44)], serr=0.2)
    for k in range(14):
        x, y = rng.uniform(50, 462), rng.uniform(50, 462)
        stem(cv, ox, oy, [(x, y), (x + rng.uniform(-8, 8), y - 22)], 2, 1.5, (80, 64, 40), z=0.85, rng=rng)
        polar(cv, ox, oy, x, y, rng.uniform(11, 15), lambda th: 0.95 + 0.05 * np.cos(th * 5), (220, 70, 56), (110, 14, 20), z=0.9, rough=0.3,
              dome=0.2, rng=rng)
        polar(cv, ox, oy, x - 4, y - 4, 3, lambda th: np.ones_like(th), (255, 200, 180), (230, 120, 110), z=1.1, rough=0.2, dome=0.02, rng=rng)


def s_nightshade(cv, ox, oy, rng):
    for k in range(4):
        pts = curve_pts((rng.uniform(100, 400), 512), (rng.uniform(0, 512), 250), (rng.uniform(40, 470), rng.uniform(20, 120)), 14)
        stem(cv, ox, oy, pts, 5, 2.5, (70, 50, 70), z=0.2, rng=rng)
    for i in range(30):
        x, y = rng.uniform(30, 482), rng.uniform(30, 482)
        blade(cv, ox, oy, x, y, rng.uniform(0, 6.28), rng.uniform(56, 80), 22, jit((40, 66, 38), rng), (46, 44, 52), shape="oval", z=0.3 + i * 0.005,
              vein=0.35, rough=0.45, rng=rng)
    for k in range(8):
        x, y = rng.uniform(50, 462), rng.uniform(50, 462)
        for j in range(7):
            a, r = rng.uniform(0, 6.28), rng.uniform(0, 22)
            polar(cv, ox, oy, x + math.cos(a) * r, y + math.sin(a) * r, rng.uniform(8, 11), lambda th: np.ones_like(th), (150, 96, 190), (34, 10, 48),
                  z=0.7 + j * 0.01, rough=0.2, dome=0.2, rng=rng)
            polar(cv, ox, oy, x + math.cos(a) * r - 3, y + math.sin(a) * r - 3, 2.2, lambda th: np.ones_like(th), (240, 220, 255), (190, 160, 220),
                  z=0.95, rough=0.15, dome=0.02, rng=rng)
    for k in range(7):
        x, y = rng.uniform(40, 472), rng.uniform(40, 472)
        polar(cv, ox, oy, x, y, 16, lambda th: 0.45 + 0.55 * np.abs(np.cos(th * 2.5)) ** 2, (176, 120, 220), (110, 60, 170), z=0.8, rough=0.55,
              dome=0.06, rng=rng)
        polar(cv, ox, oy, x, y, 4.5, lambda th: np.ones_like(th), (240, 210, 80), (200, 150, 40), z=0.85, rough=0.5, dome=0.05, rng=rng)


def s_poppy(cv, ox, oy, rng):
    for k in range(14):
        blade(cv, ox, oy, 256 + rng.uniform(-90, 90), 510, rng.uniform(-1.0, 1.0), rng.uniform(90, 170), 14, (92, 116, 80), (80, 104, 70),
              shape="lance", z=0.2, serr=0.6, vein=0.3, rng=rng)
    heads = []
    for k in range(5):
        a = rng.uniform(-0.45, 0.45)
        L = rng.uniform(250, 420)
        x0 = 256 + rng.uniform(-50, 50)
        ex, ey = x0 + math.sin(a) * L, 510 - math.cos(a) * L
        pts = curve_pts((x0, 510), ((x0 + ex) / 2 + rng.uniform(-40, 40), (510 + ey) / 2), (ex, ey), 10)
        stem(cv, ox, oy, pts, 3.5, 2.5, (100, 120, 80), z=0.3, rng=rng)
        heads.append((ex, ey, k))
    for ex, ey, k in heads:
        if k == 4:   # a bud
            polar(cv, ox, oy, ex, ey, 14, lambda th: 0.8 + 0.2 * np.cos(th), (120, 136, 90), (80, 100, 64), z=0.6, rough=0.5, dome=0.15, rng=rng)
            continue
        R = rng.uniform(52, 70)
        rot = rng.uniform(0, 3)
        for p in range(4):
            polar(cv, ox, oy, ex, ey, R, lambda th, p=p: np.clip(np.cos((th - p * np.pi / 2) * 0.9), 0, 1) ** 0.5, (120, 8, 16), (204, 30, 32),
                  z=0.6 + p * 0.03, rough=0.6, dome=0.1, rot=rot, rng=rng)
        polar(cv, ox, oy, ex, ey, R * 0.32, lambda th: np.ones_like(th), (10, 8, 10), (34, 10, 14), z=0.8, rough=0.5, dome=0.08, rng=rng)
        for j in range(16):
            a = j / 16 * 6.28
            polar(cv, ox, oy, ex + math.cos(a) * R * 0.27, ey + math.sin(a) * R * 0.27, 2.5, lambda th: np.ones_like(th), (20, 20, 24), (8, 8, 10),
                  z=0.85, rough=0.4, dome=0.03, rng=rng)
        polar(cv, ox, oy, ex, ey, R * 0.13, lambda th: 0.85 + 0.15 * np.cos(th * 8), (100, 110, 90), (60, 70, 50), z=0.9, rough=0.5, dome=0.06, rng=rng)


def s_moonflower(cv, ox, oy, rng):
    for k in range(3):
        stem(cv, ox, oy, curve_pts((rng.uniform(0, 512), 512), (rng.uniform(0, 512), 256), (rng.uniform(0, 512), 0), 14), 4, 2.5, (70, 90, 52),
             z=0.2, rng=rng)
    for i in range(20):
        x, y = rng.uniform(30, 482), rng.uniform(30, 482)

        def heart(th):
            a = np.abs(th)
            return 0.45 + 0.55 * np.maximum(np.exp(-a ** 2 / 1.1), 0.8 * np.exp(-(a - 2.55) ** 2 / 0.2)) - 0.3 * np.exp(-(a - np.pi) ** 2 / 0.02)
        polar(cv, ox, oy, x, y, rng.uniform(40, 58), heart, jit((54, 86, 44), rng), (36, 62, 32), z=0.3 + i * 0.005, rough=0.45, dome=0.1, veins=7,
              vein_col=(110, 140, 90), rot=rng.uniform(0, 6.28) + math.pi, rng=rng)
    for k in range(5):
        x, y = rng.uniform(80, 432), rng.uniform(80, 432)
        R = rng.uniform(56, 72)
        rot = rng.uniform(0, 1.2)
        polar(cv, ox, oy, x, y, R, lambda th: 0.86 + 0.14 * np.cos(th * 5), (210, 220, 214), (238, 240, 234), z=0.7 + k * 0.02, rough=0.55,
              dome=0.06, veins=5, vein_col=(196, 210, 214), rot=rot, rng=rng)
        polar(cv, ox, oy, x, y, R * 0.35, lambda th: np.ones_like(th), (200, 214, 170), (226, 232, 214), z=0.78 + k * 0.02, rough=0.5, dome=0.06,
              rng=rng)


def s_twigs(cv, ox, oy, rng):
    def branch(x, y, ang, L, w, depth):
        ex, ey = x + math.sin(ang) * L, y - math.cos(ang) * L
        mid = ((x + ex) / 2 + rng.uniform(-L, L) * 0.12, (y + ey) / 2 + rng.uniform(-L, L) * 0.12)
        stem(cv, ox, oy, curve_pts((x, y), mid, (ex, ey), 6), w, w * 0.6, jit((62, 54, 50), rng, 8), z=0.2 + (4 - depth) * 0.1,
             thorns=1 if 0 < depth < 3 else 0, thorn_col=(96, 80, 70), rng=rng)
        if depth > 0:
            for _ in range(2):
                t = rng.uniform(0.45, 0.95)
                bx, by = x + (ex - x) * t, y + (ey - y) * t
                branch(bx, by, ang + rng.uniform(-0.8, 0.8), L * rng.uniform(0.45, 0.7), w * 0.65, depth - 1)
    for k in range(3):
        branch(256 + rng.uniform(-80, 80), 510, rng.uniform(-0.4, 0.4), rng.uniform(240, 300), 11, 3)


SPRITES = [
    ("ivy", s_ivy, "fill"), ("hedge", s_hedge, "fill"), ("yew", s_yew, "base"), ("willow", s_willow, "top"),
    ("rose_crimson", lambda cv, ox, oy, rng: s_roses(cv, ox, oy, rng, (176, 22, 36), (96, 6, 18)), "fill"),
    ("rose_leaves", lambda cv, ox, oy, rng: (leafy_blob(cv, ox, oy, rng, 300, 256, 256, 240, 34, 12, [(32, 58, 28), (26, 50, 24), (36, 64, 30)], serr=0.3,
                                                       new=0.0), rose_leaves(cv, ox, oy, rng, 30, [(36, 64, 30), (30, 56, 26), (40, 70, 32)])), "fill"),
    ("wisteria", s_wisteria, "top"), ("fern", s_fern, "base"), ("lavender", s_lavender, "base"), ("grass", s_grass, "base"),
    ("bramble", s_bramble, "fill"), ("crabapple", s_crabapple, "fill"), ("nightshade", s_nightshade, "fill"), ("poppy", s_poppy, "base"),
    ("moonflower", s_moonflower, "fill"), ("twigs", s_twigs, "base"),
]


def normal_from(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def bleed(C, Aa):
    """Fill the colour of every transparent pixel from its nearest painted one (no dark fringes when mips blend the edge)."""
    solid = Aa > 0.5
    if not solid.any():
        return C
    _, (iy, ix) = ndimage.distance_transform_edt(~solid, return_indices=True)
    out = C[iy, ix]
    return np.where((Aa > 0.02)[..., None], C / np.maximum(Aa, 1e-3)[..., None] * 1.0, out) * 1.0


def save_rgb(path, arr):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def leaves():
    cv = Canvas(A)
    regions = {}
    for k, (name, fn, anchor) in enumerate(SPRITES):
        col, row = k % 4, k // 4
        ox, oy = col * CELL, row * CELL
        rng = np.random.default_rng(4000 + k)
        sub = Canvas(CELL)
        fn(sub, 0, 0, rng)
        # keep a 4 px clear margin round the cell, so neighbours never bleed into a card
        m = np.ones((CELL, CELL), np.float32)
        m[:4, :] = m[-4:, :] = 0
        m[:, :4] = m[:, -4:] = 0
        cv.C[oy:oy + CELL, ox:ox + CELL] = sub.C
        cv.A[oy:oy + CELL, ox:ox + CELL] = sub.A * m
        cv.H[oy:oy + CELL, ox:ox + CELL] = sub.H
        cv.R[oy:oy + CELL, ox:ox + CELL] = np.where(sub.A > 0, sub.R, 0.6)
        regions[name] = {"uv": [col / 4, 1 - (row + 1) / 4, (col + 1) / 4, 1 - row / 4], "anchor": anchor, "index": k}
        print("sprite", name)
    # premultiplied colour -> straight, then bled out
    C = bleed(cv.C, cv.A)
    rgba = np.dstack([np.clip(C, 0, 1), cv.A])
    Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "NH_GardenLeaves_color.png"))
    H = ndimage.gaussian_filter(cv.H * cv.A, 0.8)
    save_rgb(os.path.join(OUT, "NH_GardenLeaves_normal.png"), normal_from(H * 26, 1.0))
    save_rgb(os.path.join(OUT, "NH_GardenLeaves_rough.png"), np.dstack([cv.R] * 3))
    save_rgb(os.path.join(OUT, "NH_GardenLeaves_metal.png"), np.zeros((A, A, 3), np.float32))
    return regions


# ------------------------------------------------------------------ bark (seamless, 1024)

def pnoise(n, sigma, seed, sx=1.0, sy=1.0):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, n)).astype(np.float32)
    fy = np.fft.fftfreq(n)[:, None] * sy
    fx = np.fft.fftfreq(n)[None, :] * sx
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * math.pi * sigma) ** 2 / 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g)).astype(np.float32)
    out -= out.min()
    return out / max(1e-6, out.max())


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bark():
    n = 1024
    warp = pnoise(n, 40, 1, 1, 0.25)
    X = (np.arange(n)[None, :] / n + (warp - 0.5) * 0.08) % 1.0
    ridge_n = pnoise(n, 7, 2, 1.0, 0.12)
    ridges = 1 - np.abs(np.sin((X * 18 + (ridge_n - 0.5) * 2.2) * math.pi))
    ridges = ridges ** 0.6
    cross = sm(0.72, 0.82, pnoise(n, 10, 3, 0.4, 1.0)) * 0.6
    h = ridges * (1 - cross * 0.5) + pnoise(n, 2, 4) * 0.15
    base = np.array([0.2, 0.17, 0.15], np.float32)
    tone = pnoise(n, 30, 5)
    col = base[None, None, :] * (0.55 + 0.8 * h[..., None]) * (0.85 + 0.3 * tone[..., None])
    lichen = sm(0.62, 0.72, pnoise(n, 18, 6)) * sm(0.4, 0.8, h)
    col = col * (1 - lichen[..., None] * 0.6) + np.array([0.42, 0.45, 0.36]) * lichen[..., None] * 0.6
    moss = sm(0.6, 0.75, pnoise(n, 26, 7)) * (1 - sm(0.3, 0.7, h))
    col = col * (1 - moss[..., None] * 0.7) + np.array([0.14, 0.2, 0.07]) * moss[..., None] * 0.7
    rough = 0.82 - h * 0.12 + moss * 0.1
    save_rgb(os.path.join(OUT, "NH_GardenBark_color.png"), col)
    save_rgb(os.path.join(OUT, "NH_GardenBark_normal.png"), normal_from(h, 9.0))
    save_rgb(os.path.join(OUT, "NH_GardenBark_rough.png"), np.dstack([rough] * 3))
    save_rgb(os.path.join(OUT, "NH_GardenBark_metal.png"), np.zeros((n, n, 3), np.float32))
    print("bark")


# ------------------------------------------------------------------ the moon roundel's mosaic

LIME, SLATE, BRASS, CRIMSON, MOON, INKS, VIOLET = 1, 2, 3, 4, 5, 6, 7
PAL = {LIME: ((196, 186, 160), 0.7, 0), SLATE: ((52, 58, 66), 0.5, 0), BRASS: ((196, 150, 76), 0.3, 1), CRIMSON: ((120, 18, 30), 0.45, 0),
       MOON: ((226, 222, 204), 0.55, 0), INKS: ((26, 28, 36), 0.45, 0), VIOLET: ((70, 46, 100), 0.5, 0)}


def mosaic():
    n = 2048
    S = 2
    im = Image.new("L", (n * S, n * S), LIME)
    d = ImageDraw.Draw(im)
    c = n * S / 2
    R = n * S / 2

    def P(u, v):          # u right, v down, both in units of the disc radius
        return (c + u * R, c + v * R)

    def circ(u, v, r, fill):
        d.ellipse([*P(u - r, v - r), *P(u + r, v + r)], fill=fill)

    circ(0, 0, 1.0, LIME)
    # the wave-scroll border: slate waves breaking on limestone
    pts = []
    for i in range(721):
        a = i / 720 * 2 * math.pi
        r = 0.935 + 0.035 * math.sin(a * 28) + 0.012 * math.sin(a * 56 + 1)
        pts.append(P(math.cos(a) * r, math.sin(a) * r))
    circ(0, 0, 1.0, SLATE)
    d.polygon(pts, fill=LIME)
    circ(0, 0, 0.9, BRASS)
    circ(0, 0, 0.88, VIOLET)
    circ(0, 0, 0.84, BRASS)
    circ(0, 0, 0.825, INKS)
    g = random.Random(40)
    # brass stars and limestone motes over the night field
    for k in range(46):
        while True:
            u, v = g.uniform(-0.78, 0.78), g.uniform(-0.78, 0.78)
            if math.hypot(u, v) < 0.76:
                break
        if k < 26:
            s = g.uniform(0.018, 0.04)
            m = 5 if k % 3 else 8
            st = []
            for j in range(m * 2):
                a = j / (m * 2) * 2 * math.pi
                rr = s if j % 2 == 0 else s * 0.42
                st.append(P(u + math.sin(a) * rr, v - math.cos(a) * rr))
            d.polygon(st, fill=BRASS)
        else:
            circ(u, v, g.uniform(0.006, 0.012), LIME if k % 2 else MOON)
    # a bold emblem that reads from far off: a big pale crescent (brass-edged) cradling a clean shield: a thick brass rim, a
    # limestone field, a broad slate cross and a single crimson heart-boss with a brass star in it
    circ(-0.1, 0.0, 0.74, BRASS)
    circ(-0.1, 0.0, 0.70, MOON)
    circ(0.12, -0.03, 0.64, BRASS)
    circ(0.12, -0.03, 0.61, INKS)
    s = 0.95
    ox, oy = 0.14, 0.02

    def Q(u, v):
        return P(ox + u * s, oy + v * s)
    sh = [(-0.34, -0.4), (0.34, -0.4), (0.34, 0.02), (0.27, 0.22), (0.14, 0.36), (0, 0.44), (-0.14, 0.36), (-0.27, 0.22), (-0.34, 0.02)]
    d.polygon([Q(u * 1.2, v * 1.14 - 0.005) for u, v in sh], fill=BRASS)
    d.polygon([Q(u, v) for u, v in sh], fill=LIME)
    d.rectangle([*Q(-0.075, -0.4), *Q(0.075, 0.44)], fill=SLATE)
    d.rectangle([*Q(-0.34, -0.14), *Q(0.34, -0.0)], fill=SLATE)
    cx_, cy_ = Q(0, -0.07)
    r = 0.12 * s * R
    d.ellipse([cx_ - r, cy_ - r, cx_ + r, cy_ + r], fill=BRASS)
    r2 = 0.095 * s * R
    d.ellipse([cx_ - r2, cy_ - r2, cx_ + r2, cy_ + r2], fill=CRIMSON)
    st = []
    for j in range(10):
        a = j / 10 * 2 * math.pi
        rr = 0.075 * s * R if j % 2 == 0 else 0.032 * s * R
        st.append((cx_ + math.sin(a) * rr, cy_ - math.cos(a) * rr))
    d.polygon(st, fill=BRASS)
    lab = np.array(im.resize((n, n), Image.NEAREST))
    # tesserae: a grid of small squares (rows staggered), each one colour (its centre's), a little tilted in tone, set in grout
    t = 13.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    row = np.floor(yy / t)
    xs = xx + (row % 2) * t * 0.5
    colm = np.floor(xs / t)
    fx, fy = xs / t - colm, yy / t - row
    cx = np.clip(((colm + 0.5) * t - (row % 2) * t * 0.5).astype(np.int64), 0, n - 1)
    cy = np.clip(((row + 0.5) * t).astype(np.int64), 0, n - 1)
    tl = lab[cy, cx]
    # where the design changes inside a tessera, follow the design (crisper outlines, like cut tesserae)
    tl = np.where(lab != tl, lab, tl)
    rng = np.random.default_rng(7)
    tone_tab = rng.random(1 << 16).astype(np.float32)
    tid = ((row.astype(np.int64) * 977 + colm.astype(np.int64) * 131) & 0xFFFF)
    tone = (tone_tab[tid] - 0.5) * 0.24
    gap = 0.09
    inside = sm(0.0, gap, fx) * sm(1.0, 1 - gap, fx) * sm(0.0, gap, fy) * sm(1.0, 1 - gap, fy)
    col = np.zeros((n, n, 3), np.float32)
    rough = np.zeros((n, n), np.float32)
    metal = np.zeros((n, n), np.float32)
    for k, (cc, rr, mm) in PAL.items():
        m = tl == k
        col[m] = np.array(cc, np.float32) / 255
        rough[m] = rr
        metal[m] = mm
    col = col * (1 + tone[..., None])
    grout = np.array([0.24, 0.22, 0.2], np.float32)
    col = col * inside[..., None] + grout * (1 - inside[..., None])
    wear = pnoise(n, 60, 9)
    col = col * (0.88 + 0.2 * wear[..., None])
    moss = sm(0.68, 0.8, pnoise(n, 30, 10)) * (1 - inside) * sm(0.6, 0.95, np.hypot(xx - n / 2, yy - n / 2) / (n / 2))
    col = col * (1 - moss[..., None]) + np.array([0.14, 0.2, 0.07]) * moss[..., None]
    rough = rough * inside + 0.9 * (1 - inside) + (wear - 0.5) * 0.1
    metal = metal * inside
    h = inside * (0.8 + tone * 0.5)
    save_rgb(os.path.join(OUT, "MoonRoundelInlay_color.png"), col)
    save_rgb(os.path.join(OUT, "MoonRoundelInlay_normal.png"), normal_from(ndimage.gaussian_filter(h, 0.7), 2.5))
    save_rgb(os.path.join(OUT, "MoonRoundelInlay_rough.png"), np.dstack([np.clip(rough, 0, 1)] * 3))
    save_rgb(os.path.join(OUT, "MoonRoundelInlay_metal.png"), np.dstack([metal] * 3))
    print("mosaic")


# ------------------------------------------------------------------ worn carvings for the flagstones (bake sources)

def runes():
    """NH_GardenRune0..3: white-on-clear carvings (512), cut into a flagstone by nh_props_batch40.carved: a crescent over three
    stars, a quatrefoil in a ring, an invented inscription (NOX SERVAT, "night keeps watch"), a bat-winged sigil. Worn: the
    strokes break up where the stone has weathered."""
    n, S = 512, 2
    rng = np.random.default_rng(99)
    wear = ndimage.gaussian_filter(rng.random((n, n)).astype(np.float32), 6)
    wear = (wear - wear.min()) / (wear.max() - wear.min())
    for k in range(4):
        im = Image.new("L", (n * S, n * S), 0)
        d = ImageDraw.Draw(im)
        c = n * S / 2
        W = int(14 * S)
        if k == 0:
            r = 150 * S
            d.ellipse([c - r, c - r - 60 * S, c + r, c + r - 60 * S], outline=255, width=W)
            d.ellipse([c - r * 0.55 + 70 * S, c - r - 100 * S, c + r * 1.2, c + r * 0.8 - 60 * S], fill=0)
            for i, x in enumerate((-110, 0, 110)):
                cx, cy = c + x * S, c + 150 * S
                pts = [(cx + math.sin(j / 5 * 2 * math.pi) * (40 if j % 2 == 0 else 16) * S,
                        cy - math.cos(j / 5 * 2 * math.pi) * (40 if j % 2 == 0 else 16) * S) for j in range(10)]
                pts = [(cx + math.sin(j / 10 * 2 * math.pi) * (42 if j % 2 == 0 else 16) * S, cy - math.cos(j / 10 * 2 * math.pi) * (42 if j % 2 == 0 else 16) * S) for j in range(10)]
                d.polygon(pts, outline=255, width=int(W * 0.7))
        elif k == 1:
            r = 200 * S
            d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=W)
            q = 70 * S
            for ox, oy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                d.ellipse([c + ox * q - q, c + oy * q - q, c + ox * q + q, c + oy * q + q], outline=255, width=W)
            d.line([(c, c - 190 * S), (c, c + 190 * S)], fill=255, width=int(W * 0.6))
            d.line([(c - 190 * S, c), (c + 190 * S, c)], fill=255, width=int(W * 0.6))
        elif k == 2:
            from PIL import ImageFont
            f = ImageFont.truetype("C:/Windows/Fonts/palab.ttf", 120 * S)
            for line, y in (("NOX", c - 130 * S), ("SERVAT", c + 20 * S)):
                w = d.textlength(line, font=f)
                d.text((c - w / 2, y), line, font=f, fill=255)
            d.line([(c - 210 * S, c + 190 * S), (c + 210 * S, c + 190 * S)], fill=255, width=int(W * 0.6))
        else:
            r = 60 * S
            d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=W)
            for sx in (-1, 1):
                pts = [(c + sx * 60 * S, c - 10 * S), (c + sx * 220 * S, c - 120 * S), (c + sx * 200 * S, c + 10 * S), (c + sx * 160 * S, c - 20 * S),
                       (c + sx * 140 * S, c + 50 * S), (c + sx * 100 * S, c + 10 * S), (c + sx * 70 * S, c + 40 * S)]
                d.line(pts + [pts[0]], fill=255, width=W, joint="curve")
            d.line([(c, c + 60 * S), (c, c + 200 * S)], fill=255, width=W)
        a = np.array(im.resize((n, n), Image.LANCZOS)).astype(np.float32) / 255
        a = a * np.clip((wear - 0.22) * 4, 0.15, 1.0)
        rgba = np.dstack([np.ones((n, n, 3), np.float32), a])
        Image.fromarray((rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"NH_GardenRune{k}.png"))
    print("runes")


if __name__ == "__main__":
    import sys
    want = set(sys.argv[1:]) or {"leaves", "bark", "mosaic", "runes"}
    if "leaves" in want:
        regions = leaves()
        json.dump({"leaves": regions}, open(os.path.join(HERE, "garden_atlas.json"), "w"), indent=1)
    if "bark" in want:
        bark()
    if "mosaic" in want:
        mosaic()
    if "runes" in want:
        runes()
