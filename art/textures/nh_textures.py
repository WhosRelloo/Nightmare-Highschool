"""Nightmare Highschool tileable PBR texture sets (2026-11-03), for the builder.

Original textures made from scratch in the style of the owner's reference screenshots (a gritty Japanese school
town at night): nothing is copied from another game. Everything is procedural and periodic by construction
(the noise lattices and patterns wrap), so every map tiles seamlessly.

Run (no Blender UI needed; numpy ships with Blender):
    "E:/Blender/blender.exe" -b --factory-startup --python art/textures/nh_textures.py -- [names...]
Writes 2048 px masters to art/textures/_master/<Name>/ (local, not in git) and 1024 px game copies (Roblox caps
images at 1024) to art/textures/<Name>/<Name>_{color,normal,rough,metal}.png, plus art/textures/_sheet.png.
Every set gets the same finishing pass (write -> finish): cavity shading from the height map baked into the colour
(Roblox materials have no AO slot), grunge (packed dirt, grime, drips, dust, scuffs; amount per set in GRUNGE),
worn high edges, a micro-detail layer in the normals, and roughness that rises in the dirt.
Normal maps are OpenGL style (green = up), which is what Roblox expects.
"""
import math
import os
import sys

import numpy as np

try:
    import bpy
except ImportError:  # pragma: no cover
    bpy = None

N = 2048
OUT = os.path.dirname(os.path.abspath(__file__))
_u = (np.arange(N, dtype=np.float32) + 0.5) / N
U, V = np.meshgrid(_u, _u)          # V grows down the image


# ---------- periodic noise ----------

def vnoise(rng, cx, cy=None):
    """Smooth value noise on a cx x cy lattice that wraps (0..1)."""
    cy = cy or cx
    g = rng.random((cy, cx)).astype(np.float32)
    x = np.arange(N, dtype=np.float32) * cx / N
    y = np.arange(N, dtype=np.float32) * cy / N
    x0 = np.floor(x).astype(np.int64); fx = x - x0; x1 = (x0 + 1) % cx; x0 %= cx
    y0 = np.floor(y).astype(np.int64); fy = y - y0; y1 = (y0 + 1) % cy; y0 %= cy
    sx = fx * fx * (3 - 2 * fx)
    sy = fy * fy * (3 - 2 * fy)
    a = g[np.ix_(y0, x0)]; b = g[np.ix_(y0, x1)]; c = g[np.ix_(y1, x0)]; d = g[np.ix_(y1, x1)]
    top = a + (b - a) * sx[None, :]
    bot = c + (d - c) * sx[None, :]
    return top + (bot - top) * sy[:, None]


def pnoise_at(rng, X, Y, cx, cy=None):
    """Periodic gradient (Perlin) noise at UV coordinates X, Y (any shape, wrapped to 0..1) on a cx x cy lattice.
    Smooth and free of the blocky look value noise has. Returns about 0..1 (centred on 0.5)."""
    cy = cy or cx
    ang = rng.random((cy, cx)).astype(np.float32) * (2 * math.pi)
    gx, gy = np.cos(ang), np.sin(ang)
    x = (X % 1.0) * cx
    y = (Y % 1.0) * cy
    x0 = np.floor(x).astype(np.int64); fx = (x - x0).astype(np.float32)
    y0 = np.floor(y).astype(np.int64); fy = (y - y0).astype(np.float32)
    x0 %= cx; y0 %= cy
    x1, y1 = (x0 + 1) % cx, (y0 + 1) % cy

    def dot(ix, iy, dx, dy):
        return gx[iy, ix] * dx + gy[iy, ix] * dy
    n00 = dot(x0, y0, fx, fy); n10 = dot(x1, y0, fx - 1, fy)
    n01 = dot(x0, y1, fx, fy - 1); n11 = dot(x1, y1, fx - 1, fy - 1)
    u = fx * fx * fx * (fx * (fx * 6 - 15) + 10)      # quintic fade
    v = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    nx0 = n00 + (n10 - n00) * u
    nx1 = n01 + (n11 - n01) * u
    return 0.5 + (nx0 + (nx1 - nx0) * v) * 0.9


def fbm_at(rng, X, Y, cx, cy=None, octaves=5, gain=0.5, lac=2):
    cy = cy or cx
    out = np.zeros(np.shape(X), np.float32)
    amp, norm = 1.0, 0.0
    for i in range(octaves):
        fx, fy = cx * lac ** i, cy * lac ** i
        if fx > N or fy > N:
            break
        out += pnoise_at(rng, X, Y, fx, fy) * amp
        norm += amp
        amp *= gain
    return out / norm


def fbm(rng, cx, cy=None, octaves=5, gain=0.5):
    """Fractal gradient noise over the whole tile (0..1, wraps)."""
    return fbm_at(rng, U, V, cx, cy, octaves, gain)


def warped(rng, cx, amount, octaves=6, wcx=None):
    """Domain-warped fbm: noise bent by noise, for organic shapes (veins, moss, stains, folds)."""
    wcx = wcx or max(2, cx // 2)
    wx = fbm_at(rng, U, V, wcx, wcx, 4) - 0.5
    wy = fbm_at(rng, U + 0.37, V + 0.71, wcx, wcx, 4) - 0.5
    return fbm_at(rng, U + wx * amount, V + wy * amount, cx, cx, octaves)


def voronoi(rng, cx, cy=None, jitter=0.9, jx=None, jy=None):
    """Periodic Voronoi on a cx x cy cell grid: F1, F2 (in cell units of x) and the nearest cell id."""
    cy = cy or cx
    if jx is None:
        jx = 0.5 + (rng.random((cy, cx)) - 0.5) * jitter
        jy = 0.5 + (rng.random((cy, cx)) - 0.5) * jitter
    X, Y = U * cx, V * cy
    ix, iy = np.floor(X).astype(np.int64), np.floor(Y).astype(np.int64)
    f1 = np.full((N, N), 1e9, np.float32); f2 = np.full((N, N), 1e9, np.float32)
    ids = np.zeros((N, N), np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = (ix + dx) % cx, (iy + dy) % cy
            px = ix + dx + jx[ny, nx]
            py = iy + dy + jy[ny, nx]
            d = np.hypot((X - px) / cx, (Y - py) / cy) * cx      # measured in UV space (cells may not be square)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            ids = np.where(closer, ny * cx + nx, ids)
            f1 = np.where(closer, d, f1)
    return f1, f2, ids


def cellrand(rng, n, ids):
    t = rng.random(n).astype(np.float32)
    return t[ids % n]


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = t[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def rgb(*c):
    return np.array(c, np.float32)


def tint(base, var):
    """A colour image from a base colour (r, g, b) and a -1..1 variation map."""
    return np.clip(base[None, None, :] * (1 + var[..., None]), 0, 1)


def scratches(rng, count, length, width, angle=None, spread=math.pi):
    """Thin random scratch lines that wrap around the tile (0..1 strength)."""
    out = np.zeros((N, N), np.float32)
    for _ in range(count):
        cx, cy = rng.random() * N, rng.random() * N
        a = (angle if angle is not None else rng.random() * math.pi) + (rng.random() - 0.5) * spread
        L = length * (0.4 + rng.random())
        x0, y0 = cx - math.cos(a) * L / 2, cy - math.sin(a) * L / 2
        x1, y1 = cx + math.cos(a) * L / 2, cy + math.sin(a) * L / 2
        lo_x, hi_x = int(min(x0, x1) - 3), int(max(x0, x1) + 3)
        lo_y, hi_y = int(min(y0, y1) - 3), int(max(y0, y1) + 3)
        xs = np.arange(lo_x, hi_x + 1); ys = np.arange(lo_y, hi_y + 1)
        PX, PY = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
        dx, dy = x1 - x0, y1 - y0
        l2 = dx * dx + dy * dy + 1e-6
        t = np.clip(((PX - x0) * dx + (PY - y0) * dy) / l2, 0, 1)
        d = np.hypot(PX - (x0 + dx * t), PY - (y0 + dy * t))
        s = np.clip(1 - d / width, 0, 1) * (0.5 + 0.5 * rng.random())
        rows, cols = ys % N, xs % N
        out[np.ix_(rows, cols)] = np.maximum(out[np.ix_(rows, cols)], s)
    return out


# ---------- writing ----------

def normal_from(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5       # up the image
    n = np.dstack([-gx * strength * N / 256, -gy * strength * N / 256, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def save(path, arr, size=None):
    size = size or N
    if arr.ndim == 2:
        arr = np.dstack([arr, arr, arr])
    rgba = np.dstack([np.clip(arr, 0, 1), np.ones((size, size), np.float32)])[::-1].astype(np.float32)
    img = bpy.data.images.new(os.path.basename(path), size, size, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def blur(a, sigma):
    """A periodic gaussian blur (FFT): the texture wraps, so the blur does too."""
    f = np.fft.fftfreq(N).astype(np.float32)
    k = np.exp(-2 * (math.pi ** 2) * (sigma ** 2) * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k)).astype(np.float32)


def finish(color, height, rough, rng, cavity=0.6, micro=0.035, grunge=1.0):
    """Depth, detail and grunge for every set:
    - cavity shading (dark in the grooves) and a little highlight on worn high edges
    - grime: dirt packed into the cavities, warped blotches, vertical rain and drip streaks, dust specks, light scuffs
    - roughness that rises where the dirt sits, and a micro-detail layer in the height for the normals
    grunge scales the dirt (0 = clean, 1 = the default, more = filthier)."""
    h = height + (fbm(rng, 128, 128, 3) - 0.5) * micro
    cav = np.clip((blur(h, 6) - h) * 6 + (blur(h, 24) - h) * 2.5, 0, 1)
    peak = np.clip((h - blur(h, 6)) * 5, 0, 1)
    col = color * (1 - cav[..., None] * cavity)
    if grunge > 0:
        g = grunge
        dirt = rgb(0.13, 0.10, 0.07)
        blotch = smooth(0.52, 0.78, warped(rng, 5, 0.8, 6)) * g
        drips = smooth(0.56, 0.74, fbm_at(rng, U, V, 56, 3, 5)) * smooth(0.45, 0.7, fbm(rng, 4, 4, 4)) * g
        packed = np.clip(cav * 1.1, 0, 1) * g
        dust = smooth(0.79, 0.84, pnoise_at(rng, U, V, 520)) * smooth(0.4, 0.7, fbm(rng, 8, 8, 3)) * g   # round specks
        scuff = scratches(rng, int(140 * g) + 1, 26, 1.0) * g
        col = mix(col, dirt, np.clip(blotch * 0.45 + packed * 0.3, 0, 1))
        col = mix(col, rgb(0.08, 0.07, 0.06), np.clip(drips * 0.45, 0, 1))
        col = mix(col, rgb(0.55, 0.52, 0.47), np.clip(dust * 0.35 + scuff * 0.22, 0, 1))
        col = col * (1 + peak[..., None] * 0.14 * g)          # worn, polished high edges
        rough = rough + blotch * 0.18 + drips * 0.1 + packed * 0.12 - peak * 0.05 * g
        h = h - blotch * 0.02 - scuff * 0.01
    col = np.clip(col * ALBEDO, 0, 1)
    r = np.clip(rough + cav * 0.12 + (fbm(rng, 96, 96, 3) - 0.5) * 0.08, 0.02, 1)
    return col, h, r


ALBEDO = 0.88    # every colour map a touch darker, to sit at the props' brightness under the same lights
GRUNGE = {"BloodMarble": 0.35, "StainedGlass": 0.45, "CrimsonVelvet": 0.4, "SnowGround": 0.25, "DamaskWallpaper": 0.75,
          "CheckerMarble": 0.8, "QuatrefoilTile": 0.85, "DirtyTile": 1.4, "Concrete": 1.3, "DarkPlaster": 1.2,
          "PaintedMetal": 1.2, "OldBoards": 1.3, "Cobblestone": 1.2, "GothicStone": 1.2, "MossyFlagstone": 1.1}


def write(name, color, height, rough, metal, strength, rng=None, cavity=0.6):
    rng = rng or np.random.default_rng(len(name))
    color, height, rough = finish(color, height, rough, rng, cavity, grunge=GRUNGE.get(name, 1.0))
    nrm = normal_from(height, strength)
    maps = {"color": color, "normal": nrm, "rough": rough, "metal": metal}
    # the 2048 masters (local only: rebuilt by this script) and the 1024 game copies (Roblox caps images at 1024)
    master = os.path.join(OUT, "_master", name)
    game = os.path.join(OUT, name)
    os.makedirs(master, exist_ok=True)
    os.makedirs(game, exist_ok=True)
    for kind, arr in maps.items():
        save(os.path.join(master, f"{name}_{kind}.png"), arr)
        half = half_size(arr, kind == "normal")
        save(os.path.join(game, f"{name}_{kind}.png"), half, half.shape[0])
    print("wrote", name)
    return color


def half_size(arr, is_normal):
    """A clean 2x box downsample (normals are re-normalised)."""
    a = arr if arr.ndim == 3 else arr[..., None]
    h = (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) * 0.25
    if is_normal:
        v = h * 2 - 1
        v /= np.linalg.norm(v, axis=2, keepdims=True)
        h = v * 0.5 + 0.5
    return h if arr.ndim == 3 else h[..., 0]


# ---------- the sets ----------

def grain(rng, along, across, freq, wobble):
    """Wood grain: rings across the board, bent by noise along it."""
    n = fbm(rng, 4, 32, 5)
    w = np.sin((across * freq + n * wobble) * math.pi * 2)
    fine = fbm(rng, 8, 128, 3)
    return 0.5 + 0.3 * w + 0.2 * (fine - 0.5) * 2


def ParquetWood(rng):
    """Warm orange parquet: 4 x 4 blocks of three strips each, alternating direction (basket weave)."""
    B = 4
    bx, by = np.floor(U * B), np.floor(V * B)
    fu, fv = U * B - bx, V * B - by
    flip = ((bx + by) % 2) == 1
    along, across = np.where(flip, fu, fv), np.where(flip, fv, fu)
    strip = np.floor(across * 3)
    sa = across * 3 - strip
    sid = (by * B + bx) * 3 + strip
    tone = (rng.random(64).astype(np.float32)[sid.astype(np.int64) % 64] - 0.5) * 0.35
    g1 = grain(rng, along, across, 9, 2.5)
    g2 = grain(rng, across, along, 9, 2.5)
    g = np.where(flip, g1, g2)
    groove = np.maximum(1 - smooth(0.0, 0.035, sa) * smooth(1.0, 0.965, sa), 0)
    edge = 1 - smooth(0.0, 0.012, fu) * smooth(1.0, 0.988, fu) * smooth(0.0, 0.012, fv) * smooth(1.0, 0.988, fv)
    gap = np.clip(groove + edge, 0, 1)
    wear = fbm(rng, 6, 6, 4)
    base = rgb(0.62, 0.34, 0.16)
    col = tint(base, tone + (g - 0.5) * 0.45 + (wear - 0.5) * 0.25)
    col = mix(col, rgb(0.16, 0.08, 0.04), gap * 0.85)
    pores = smooth(0.82, 0.95, fbm(rng, 64, 512, 2)) * (1 - gap)
    col = mix(col, rgb(0.25, 0.12, 0.05), pores * 0.35)
    h = g * 0.25 + (1 - gap) * 0.75 - pores * 0.04
    rough = np.clip(0.42 + (g - 0.5) * 0.15 + gap * 0.4 + (wear - 0.5) * 0.2, 0, 1)
    return write("ParquetWood", col, h, rough, np.zeros_like(h), 3)


def FloorPlanks(rng):
    """Worn classroom floorboards: six rows of long planks with staggered ends, dark gaps and scuffs."""
    R = 6
    row = np.floor(V * R)
    off = rng.random(R).astype(np.float32)[row.astype(np.int64) % R]
    x = (U + off) % 1.0
    seg = np.floor(x * 2)
    fx = x * 2 - seg
    fv = V * R - row
    pid = (row * 2 + seg).astype(np.int64)
    tone = (rng.random(64).astype(np.float32)[pid % 64] - 0.5) * 0.4
    n = fbm(rng, 2, 48, 5)
    g = 0.5 + 0.35 * np.sin((fv * 6 + n * 3) * math.pi * 2) * (fbm(rng, 8, 8, 3) * 0.6 + 0.4)
    gap = 1 - smooth(0.0, 0.02, fv) * smooth(1.0, 0.98, fv) * smooth(0.0, 0.006, fx) * smooth(1.0, 0.994, fx)
    dirt = fbm(rng, 5, 5, 5)
    scuff = scratches(rng, 220, 70, 1.4, angle=0, spread=0.3)
    col = tint(rgb(0.46, 0.30, 0.18), tone + (g - 0.5) * 0.4 + (dirt - 0.5) * 0.5)
    col = mix(col, rgb(0.70, 0.55, 0.40), scuff * 0.35)
    col = mix(col, rgb(0.10, 0.06, 0.04), gap * 0.9)
    h = g * 0.2 + (1 - gap) * 0.8 - scuff * 0.05
    rough = np.clip(0.55 + (dirt - 0.5) * 0.3 + gap * 0.3 - scuff * 0.1, 0, 1)
    return write("FloorPlanks", col, h, rough, np.zeros_like(h), 3)


def bricks(rows, cols, mortar, rng, chip=0.0):
    r = np.floor(V * rows)
    shift = (r % 2) * 0.5
    x = U * cols + shift
    c = np.floor(x)
    fx, fy = x - c, V * rows - r
    bid = (r * cols + (c % cols)).astype(np.int64)
    if chip > 0:
        e = (fbm(rng, 32, 32, 3) - 0.5) * chip
        fx, fy = fx + e, fy + e
    mx = mortar * cols / rows
    inside = smooth(0, mortar, fy) * smooth(1, 1 - mortar, fy) * smooth(0, mx, fx) * smooth(1, 1 - mx, fx)
    return inside, bid, fx, fy


def RedBrick(rng):
    """Dark maroon brick in running bond, slightly lighter mortar, weathered faces."""
    inside, bid, fx, fy = bricks(8, 4, 0.06, rng, chip=0.04)
    tone = (rng.random(64).astype(np.float32)[bid % 64] - 0.5) * 0.35
    face = fbm(rng, 16, 16, 5)
    col = tint(rgb(0.30, 0.15, 0.14), tone + (face - 0.5) * 0.5)
    mortar = tint(rgb(0.36, 0.28, 0.26), (fbm(rng, 32, 32, 3) - 0.5) * 0.4)
    rim = inside * (1 - smooth(0.25, 0.85, inside))
    col = mix(col, rgb(0.42, 0.26, 0.23), rim * 0.5)
    col = mix(mortar, col, inside)
    soot = smooth(0.55, 0.85, fbm(rng, 3, 3, 5))
    col = mix(col, rgb(0.10, 0.07, 0.07), soot * 0.35)
    h = inside * (0.7 + face * 0.3)
    rough = np.clip(0.75 + (face - 0.5) * 0.2 + (1 - inside) * 0.15, 0, 1)
    return write("RedBrick", col, h, rough, np.zeros_like(h), 6)


def StoneBlock(rng):
    """Grey-blue cut stone blocks with chipped edges (the low walls along the streets)."""
    inside, bid, fx, fy = bricks(6, 3, 0.035, rng, chip=0.06)
    tone = (rng.random(64).astype(np.float32)[bid % 64] - 0.5) * 0.25
    face = fbm(rng, 12, 12, 6)
    col = tint(rgb(0.33, 0.34, 0.38), tone + (face - 0.5) * 0.45)
    col = mix(rgb(0.16, 0.16, 0.18), col, inside)
    h = inside * (0.75 + face * 0.25)
    rough = np.clip(0.8 + (face - 0.5) * 0.2, 0, 1)
    return write("StoneBlock", col, h, rough, np.zeros_like(h), 6)


def Cobblestone(rng):
    """Small dark granite setts, squarish and packed tight (the town's old streets)."""
    f1, f2, ids = voronoi(rng, 22, jitter=0.3)
    e = f2 - f1
    dome = smooth(0.0, 0.3, e)
    tone = (cellrand(rng, 1024, ids) - 0.5) * 0.45
    face = fbm(rng, 24, 24, 4)
    col = tint(rgb(0.25, 0.25, 0.28), tone + (face - 0.5) * 0.4)
    col = mix(rgb(0.07, 0.07, 0.08), col, smooth(0.04, 0.12, e))
    h = dome * 0.85 + face * 0.15
    rough = np.clip(0.6 + (face - 0.5) * 0.3 + (1 - dome) * 0.3, 0, 1)
    return write("Cobblestone", col, h, rough, np.zeros_like(h), 7)


def HexTile(rng):
    """Red-brown hexagonal pavers with thin pale grout and speckle (the shopping street)."""
    cx, cy = 5, 6
    # every other row shifted half a cell: the centres sit on a hex lattice
    jx = np.zeros((cy, cx)) + np.where((np.arange(cy) % 2)[:, None] == 1, 0.0, 0.5)
    jy = np.full((cy, cx), 0.5)
    f1, f2, ids = voronoi(rng, cx, cy, jx=jx, jy=jy)
    e = f2 - f1
    inside = smooth(0.03, 0.07, e)
    tone = (cellrand(rng, 64, ids) - 0.5) * 0.2
    spk = smooth(0.76, 0.8, pnoise_at(rng, U, V, 300)) * 0.15
    face = fbm(rng, 16, 16, 5)
    col = tint(rgb(0.44, 0.18, 0.15), tone + (face - 0.5) * 0.35 - spk)
    col = mix(rgb(0.62, 0.50, 0.47), col, inside)
    h = inside * (0.8 + face * 0.2)
    rough = np.clip(0.55 + (face - 0.5) * 0.25 + (1 - inside) * 0.25, 0, 1)
    return write("HexTile", col, h, rough, np.zeros_like(h), 5)


def Pavers(rng):
    """Big square grey stone pavers, a little uneven, hairline cracks."""
    S = 4
    fx, fy = U * S - np.floor(U * S), V * S - np.floor(V * S)
    pid = (np.floor(V * S) * S + np.floor(U * S)).astype(np.int64)
    inside = smooth(0, 0.015, fx) * smooth(1, 0.985, fx) * smooth(0, 0.015, fy) * smooth(1, 0.985, fy)
    tone = (rng.random(64).astype(np.float32)[pid % 64] - 0.5) * 0.18
    face = fbm(rng, 10, 10, 6)
    f1, f2, _ = voronoi(rng, 7, jitter=1.0)
    crack = (1 - smooth(0.0, 0.025, f2 - f1)) * (fbm(rng, 6, 6, 3) > 0.55)
    col = tint(rgb(0.44, 0.44, 0.47), tone + (face - 0.5) * 0.35)
    col = mix(col, rgb(0.18, 0.18, 0.2), crack * 0.6)
    col = mix(rgb(0.2, 0.2, 0.22), col, inside)
    h = inside * (0.85 + face * 0.15) - crack * 0.1
    rough = np.clip(0.6 + (face - 0.5) * 0.3, 0, 1)
    return write("Pavers", col, h, rough, np.zeros_like(h), 5)


def Concrete(rng):
    """Warm grey poured concrete: pits, dirt stains, a few cracks (the band's practice space)."""
    face = fbm(rng, 6, 6, 7)
    stain = smooth(0.55, 0.8, fbm(rng, 3, 3, 5))
    pits = smooth(0.74, 0.82, pnoise_at(rng, U, V, 200)) * 0.6
    f1, f2, _ = voronoi(rng, 5, jitter=1.0)
    crack = (1 - smooth(0.0, 0.012, f2 - f1)) * (fbm(rng, 4, 4, 3) > 0.6)
    col = tint(rgb(0.56, 0.53, 0.49), (face - 0.5) * 0.35)
    col = mix(col, rgb(0.36, 0.31, 0.25), stain * 0.6)
    col = mix(col, rgb(0.28, 0.26, 0.24), np.clip(pits + crack, 0, 1) * 0.7)
    h = face * 0.3 + 0.7 - pits * 0.3 - crack * 0.3
    rough = np.clip(0.8 + (face - 0.5) * 0.15 - stain * 0.15, 0, 1)
    return write("Concrete", col, h, rough, np.zeros_like(h), 4)


def PaintedMetal(rng):
    """Maroon-painted steel, scratched and chipped down to bare metal at the wear (girders, railings)."""
    face = fbm(rng, 8, 8, 6)
    sc = scratches(rng, 900, 46, 1.6)
    chip = smooth(0.7, 0.78, fbm(rng, 10, 10, 5)) * smooth(0.5, 0.7, fbm(rng, 3, 3, 3))
    bare = np.clip(sc * 1.0 + chip, 0, 1)
    col = tint(rgb(0.36, 0.11, 0.15), (face - 0.5) * 0.3)
    col = mix(col, rgb(0.68, 0.64, 0.64), bare)
    rust = chip * smooth(0.45, 0.7, fbm(rng, 24, 24, 4))
    col = mix(col, rgb(0.42, 0.20, 0.09), rust * 0.8)
    h = 0.8 - bare * 0.25 + face * 0.05 - rust * 0.05
    rough = np.clip(0.45 + (face - 0.5) * 0.2 - bare * 0.15, 0, 1)
    metal = np.clip(bare * 0.9 - rust * 0.8, 0, 1)
    rough = np.clip(rough + rust * 0.4, 0, 1)
    return write("PaintedMetal", col, h, rough, metal, 4)


def DirtyTile(rng):
    """Old white square wall tiles: rusty grout, grime, chips and the odd missing tile (the derelict washroom)."""
    T = 8
    fx, fy = U * T - np.floor(U * T), V * T - np.floor(V * T)
    tid = (np.floor(V * T) * T + np.floor(U * T)).astype(np.int64)
    inside = smooth(0, 0.05, fx) * smooth(1, 0.95, fx) * smooth(0, 0.05, fy) * smooth(1, 0.95, fy)
    missing = (rng.random(T * T).astype(np.float32)[tid % (T * T)] > 0.93).astype(np.float32)
    grime = fbm(rng, 4, 4, 6)
    col = tint(rgb(0.86, 0.85, 0.80), (grime - 0.5) * 0.25)
    col = mix(col, rgb(0.55, 0.42, 0.30), smooth(0.6, 0.85, grime) * 0.5)
    col = mix(tint(rgb(0.50, 0.38, 0.27), (fbm(rng, 48, 48, 3) - 0.5) * 0.5), col, inside)
    col = mix(col, rgb(0.07, 0.08, 0.1), missing * inside)
    h = inside * (1 - missing * 0.7) + grime * 0.05
    rough = np.clip(0.2 + (1 - inside) * 0.6 + missing * 0.6 + smooth(0.6, 0.85, grime) * 0.3, 0, 1)
    return write("DirtyTile", col, h, rough, np.zeros_like(h), 5)


def DarkPlaster(rng):
    """Near-black blue plaster scuffed with pale scratches (the alley and stairwell walls)."""
    face = fbm(rng, 5, 5, 7)
    sc = scratches(rng, 300, 30, 1.1)
    blot = smooth(0.5, 0.9, fbm(rng, 6, 6, 7))
    col = tint(rgb(0.09, 0.10, 0.14), (face - 0.5) * 0.6)
    col = mix(col, rgb(0.18, 0.19, 0.23), blot * 0.6)
    col = mix(col, rgb(0.62, 0.62, 0.66), sc * 0.55)
    h = face * 0.4 + 0.6 - sc * 0.1
    rough = np.clip(0.82 + (face - 0.5) * 0.15, 0, 1)
    return write("DarkPlaster", col, h, rough, np.zeros_like(h), 3)


def CheckerMarble(rng):
    """Cream and dark-brown checkered marble with veins, a little worn (the live-house stage)."""
    T = 4
    cell = ((np.floor(U * T) + np.floor(V * T)) % 2).astype(np.float32)
    fx, fy = U * T - np.floor(U * T), V * T - np.floor(V * T)
    seam = 1 - smooth(0, 0.01, fx) * smooth(1, 0.99, fx) * smooth(0, 0.01, fy) * smooth(1, 0.99, fy)
    n = fbm(rng, 4, 4, 6)
    vein = 1 - smooth(0.0, 0.06, np.abs(np.sin((U * 3 + V * 2 + n * 2.5) * math.pi * 2)))
    light = tint(rgb(0.80, 0.70, 0.58), (n - 0.5) * 0.25)
    dark = tint(rgb(0.22, 0.15, 0.13), (n - 0.5) * 0.5)
    col = mix(light, dark, cell)
    col = mix(col, np.where(cell[..., None] > 0.5, rgb(0.42, 0.33, 0.28), rgb(0.55, 0.45, 0.38)), vein * 0.5)
    wear = smooth(0.55, 0.8, fbm(rng, 3, 3, 5))
    col = mix(col, rgb(0.35, 0.28, 0.22), wear * 0.3)
    col = mix(col, rgb(0.1, 0.08, 0.07), seam * 0.8)
    h = 1 - seam * 0.6
    rough = np.clip(0.22 + wear * 0.35 + seam * 0.4, 0, 1)
    return write("CheckerMarble", col, h, rough, np.zeros_like(h), 4)


def OldBoards(rng):
    """Weathered vertical boards, some painted faded blue, peeling (the boarded-up corner under the stairs)."""
    C = 8
    col_i = np.floor(U * C)
    fx = U * C - col_i
    bid = col_i.astype(np.int64)
    paint = (rng.random(C).astype(np.float32)[bid % C] > 0.65).astype(np.float32)
    tone = (rng.random(C).astype(np.float32)[bid % C] - 0.5) * 0.5
    n = fbm(rng, 48, 2, 5)
    g = 0.5 + 0.35 * np.sin((fx * 5 + n * 3) * math.pi * 2)
    gap = 1 - smooth(0, 0.04, fx) * smooth(1, 0.96, fx)
    peel = smooth(0.45, 0.55, fbm(rng, 12, 12, 5))
    wood = tint(rgb(0.30, 0.22, 0.15), tone + (g - 0.5) * 0.5)
    blue = tint(rgb(0.20, 0.38, 0.60), (n - 0.5) * 0.4)
    col = mix(wood, blue, paint * peel)
    col = mix(col, rgb(0.05, 0.04, 0.04), gap * 0.9)
    h = (1 - gap) * (0.7 + g * 0.2 + paint * peel * 0.1)
    rough = np.clip(0.75 - paint * peel * 0.2 + gap * 0.2, 0, 1)
    return write("OldBoards", col, h, rough, np.zeros_like(h), 4)


def SnowGround(rng):
    """Packed snow drifts: soft, bright, faint blue in the hollows."""
    face = fbm(rng, 4, 4, 7)
    sparkle = smooth(0.8, 0.84, pnoise_at(rng, U, V, 600))
    col = tint(rgb(0.86, 0.89, 0.94), (face - 0.5) * 0.12)
    col = mix(col, rgb(0.70, 0.76, 0.88), smooth(0.55, 0.3, face) * 0.5)
    col = np.clip(col + sparkle[..., None] * 0.06, 0, 1)
    h = face
    rough = np.clip(0.7 - sparkle * 0.4, 0, 1)
    return write("SnowGround", col, h, rough, np.zeros_like(h), 3)


# ---------- the gothic sets (Nightmare High's own: crimson, gold, black oak, old stone) ----------

def DamaskWallpaper(rng):
    """Deep crimson wallpaper, classic damask: a fine wavy gold ogee lattice with a small six-petal bloom and a pearl in
    every diamond, faded and grimy with age, the gold printed slightly raised."""
    C, R = 4, 3
    a, b = U * C + V * R, U * C - V * R                # a diamond lattice that wraps (C, R are whole numbers)
    wa = a + 0.13 * np.sin(b * math.pi * 2)              # bend the lines into ogees
    wb = b + 0.13 * np.sin(a * math.pi * 2)
    da, db = np.abs(wa - np.round(wa)), np.abs(wb - np.round(wb))
    lattice = np.maximum(smooth(0.035, 0.018, da), smooth(0.035, 0.018, db))
    # inside each diamond: a small bloom (six petals) with a pearl, and four leaf dots toward the corners
    la, lb = (a - np.floor(a)) - 0.5, (b - np.floor(b)) - 0.5
    rr = np.hypot(la, lb)
    th = np.arctan2(lb, la)
    petals = smooth(0.2, 0.17, rr / (0.65 + 0.35 * np.abs(np.cos(th * 3))))
    hollow = smooth(0.09, 0.07, rr / (0.65 + 0.35 * np.abs(np.cos(th * 3))))
    pearl = smooth(0.045, 0.03, rr)
    leaves = smooth(0.05, 0.035, np.hypot(np.abs(la) - 0.3, lb)) + smooth(0.05, 0.035, np.hypot(la, np.abs(lb) - 0.3))
    motif = np.clip(lattice + np.clip(petals - hollow, 0, 1) + pearl + leaves * 0.9, 0, 1)
    age = warped(rng, 4, 0.6, 6)
    fade = smooth(0.4, 0.75, age)
    ground = tint(rgb(0.24, 0.035, 0.055), (fbm(rng, 64, 64, 3) - 0.5) * 0.3 + (age - 0.5) * 0.4)
    gold = tint(rgb(0.60, 0.45, 0.21), (fbm(rng, 48, 48, 3) - 0.5) * 0.4)
    col = mix(ground, gold, motif * (1 - fade * 0.45))
    col = mix(col, rgb(0.12, 0.05, 0.04), smooth(0.62, 0.85, age) * 0.35)
    h = 0.5 + motif * 0.2 + (fbm(rng, 256, 256, 2) - 0.5) * 0.05
    rough = np.clip(0.8 - motif * 0.35, 0, 1)
    metal = motif * 0.35 * (1 - fade * 0.5)
    return write("DamaskWallpaper", col, h, rough, metal, 2, rng, cavity=0.35)


def CrimsonVelvet(rng):
    """Crimson velvet: a fine pile weave, soft crushed folds and a sheen that shifts across it (curtains, seats)."""
    weave = 0.5 + 0.25 * np.sin(U * N * 0.9) * np.sin(V * N * 0.9)
    folds = warped(rng, 3, 0.8, 5)
    crush = warped(rng, 10, 0.4, 5)
    tone = (folds - 0.5) * 0.9 + (crush - 0.5) * 0.4
    col = tint(rgb(0.42, 0.04, 0.07), tone)
    col = mix(col, rgb(0.62, 0.12, 0.16), smooth(0.6, 0.85, folds) * 0.35)
    h = folds * 0.6 + crush * 0.25 + weave * 0.15
    rough = np.clip(0.88 - smooth(0.55, 0.8, crush) * 0.25, 0, 1)
    return write("CrimsonVelvet", col, h, rough, np.zeros_like(h), 3, rng, cavity=0.5)


def GothicStone(rng):
    """Aged cathedral limestone ashlar: pale grey-beige blocks, moss in the joints, dark rain streaks down the face."""
    inside, bid, fx, fy = bricks(4, 2, 0.03, rng, chip=0.07)
    tone = (rng.random(64).astype(np.float32)[bid % 64] - 0.5) * 0.22
    face = warped(rng, 10, 0.3, 7)
    pores = smooth(0.62, 0.75, pnoise_at(rng, U, V, 220)) * 0.5
    streak = smooth(0.55, 0.75, fbm_at(rng, U, V, 40, 3, 5)) * smooth(0.3, 0.7, fbm(rng, 4, 4, 3))
    col = tint(rgb(0.58, 0.55, 0.49), tone + (face - 0.5) * 0.4 - pores * 0.3)
    col = mix(col, rgb(0.20, 0.20, 0.19), streak * 0.55)
    moss = smooth(0.45, 0.62, warped(rng, 16, 0.5, 5)) * (1 - inside)
    mortar = tint(rgb(0.34, 0.33, 0.30), (fbm(rng, 48, 48, 3) - 0.5) * 0.4)
    col = mix(mortar, col, inside)
    col = mix(col, rgb(0.20, 0.28, 0.12), np.clip(moss + (1 - inside) * 0.25, 0, 1) * 0.75)
    h = inside * (0.78 + face * 0.22) - pores * 0.04
    rough = np.clip(0.82 + (face - 0.5) * 0.15 - streak * 0.1, 0, 1)
    return write("GothicStone", col, h, rough, np.zeros_like(h), 7, rng)


def WroughtIron(rng):
    """Black wrought-iron lattice: diamond bars with rivets at every cross, over a dark backing plate, a little rust."""
    D = 6
    a, b = (U + V) * D, (U - V) * D
    da = np.abs(a - np.round(a)); db = np.abs(b - np.round(b))
    bar = np.maximum(smooth(0.09, 0.05, da), smooth(0.09, 0.05, db))
    cx_, cy_ = U * D * 2, V * D * 2
    rx, ry = cx_ - np.round(cx_), cy_ - np.round(cy_)
    rivet_on = ((np.round(cx_) + np.round(cy_)) % 2) == 0
    rivet = smooth(0.16, 0.10, np.hypot(rx, ry)) * rivet_on
    face = fbm(rng, 12, 12, 6)
    rust = smooth(0.55, 0.72, warped(rng, 12, 0.5, 5))
    plate = tint(rgb(0.05, 0.05, 0.06), (face - 0.5) * 0.4)
    iron = tint(rgb(0.16, 0.16, 0.17), (face - 0.5) * 0.5)
    col = mix(plate, iron, np.clip(bar + rivet, 0, 1))
    col = mix(col, rgb(0.35, 0.16, 0.08), rust * np.clip(bar + rivet, 0, 1) * 0.55)
    h = 0.2 + bar * 0.5 + rivet * 0.3 + face * 0.04
    rough = np.clip(0.55 + rust * 0.35 - bar * 0.15, 0, 1)
    metal = np.clip((bar + rivet) * (1 - rust) * 0.85, 0, 1)
    return write("WroughtIron", col, h, rough, metal, 5, rng)


def StainedGlass(rng):
    """Leaded stained glass: jewel-coloured panes (crimson, sapphire, amber, violet, emerald) in black lead came."""
    f1, f2, ids = voronoi(rng, 9, jitter=0.9)
    e = f2 - f1
    lead = 1 - smooth(0.03, 0.06, e)
    palette = np.array([[0.62, 0.05, 0.10], [0.08, 0.16, 0.55], [0.85, 0.55, 0.12], [0.36, 0.10, 0.48],
                        [0.07, 0.40, 0.22], [0.55, 0.04, 0.06], [0.10, 0.26, 0.62]], np.float32)
    pick = (cellrand(rng, 512, ids) * len(palette)).astype(np.int64) % len(palette)
    pane = palette[pick]
    ripple = warped(rng, 14, 0.5, 5)
    pane = np.clip(pane * (0.75 + ripple[..., None] * 0.55 + (smooth(0.0, 0.35, e) * 0.25)[..., None]), 0, 1)
    col = mix(pane, rgb(0.05, 0.05, 0.06), lead)
    h = (1 - lead) * (0.6 + ripple * 0.2) + lead * 0.9
    rough = np.clip(0.08 + ripple * 0.1 + lead * 0.6, 0, 1)
    metal = lead * 0.6
    return write("StainedGlass", col, h, rough, metal, 4, rng, cavity=0.3)


def BloodMarble(rng):
    """Polished black marble shot through with crimson veins and the odd gold fleck."""
    base = warped(rng, 3, 1.1, 7)
    v1 = 1 - smooth(0.0, 0.045, np.abs(np.sin((base * 3.2 + U * 0.7) * math.pi * 2)))
    v2 = 1 - smooth(0.0, 0.02, np.abs(np.sin((warped(rng, 5, 0.9, 6) * 4.5) * math.pi * 2)))
    fleck = smooth(0.8, 0.84, pnoise_at(rng, U, V, 640)) * smooth(0.5, 0.7, fbm(rng, 6, 6, 3))
    col = tint(rgb(0.05, 0.045, 0.05), (base - 0.5) * 0.6)
    col = mix(col, rgb(0.48, 0.04, 0.07), v1 * 0.85)
    col = mix(col, rgb(0.30, 0.03, 0.05), v2 * 0.6)
    col = mix(col, rgb(0.75, 0.58, 0.28), fleck)
    h = 0.6 + (base - 0.5) * 0.04
    rough = np.clip(0.07 + v1 * 0.05 + (fbm(rng, 24, 24, 3) - 0.5) * 0.06, 0, 1)
    metal = fleck * 0.9
    return write("BloodMarble", col, h, rough, metal, 1, rng, cavity=0.2)


def GothicOakPanel(rng):
    """Dark oak wainscot: two raised, bevelled panels a row in a moulded frame, with long grain."""
    cx_, cy_ = 2, 2
    px, py = U * cx_ - np.floor(U * cx_), V * cy_ - np.floor(V * cy_)
    # frame 0..0.12, bevel 0.12..0.2, raised field inside
    d = np.minimum(np.minimum(px, 1 - px), np.minimum(py, 1 - py))
    frame_groove = smooth(0.105, 0.115, d) * smooth(0.13, 0.12, d)
    bevel = smooth(0.12, 0.2, d)
    n = fbm_at(rng, U, V, 3, 40, 6)
    g = 0.5 + 0.35 * np.sin((U * 30 + n * 4) * math.pi * 2) * 0.6 + (fbm_at(rng, U, V, 6, 120, 3) - 0.5) * 0.5
    col = tint(rgb(0.20, 0.11, 0.06), (g - 0.5) * 0.6 + (fbm(rng, 4, 4, 4) - 0.5) * 0.3)
    col = mix(col, rgb(0.08, 0.04, 0.02), frame_groove * 0.8)
    h = 0.4 + bevel * 0.35 - frame_groove * 0.25 + g * 0.03
    rough = np.clip(0.45 + (g - 0.5) * 0.2 + frame_groove * 0.3, 0, 1)
    return write("GothicOakPanel", col, h, rough, np.zeros_like(h), 5, rng)


def RuneSlate(rng):
    """Dark slate slabs carved with runes; the carvings hold a faint crimson glow (ritual floors, the Archive)."""
    S = 3
    sx, sy = U * S - np.floor(U * S), V * S - np.floor(V * S)
    sid = (np.floor(V * S) * S + np.floor(U * S)).astype(np.int64)
    inside = smooth(0, 0.015, sx) * smooth(1, 0.985, sx) * smooth(0, 0.015, sy) * smooth(1, 0.985, sy)
    layers = fbm_at(rng, U, V, 4, 16, 6)                # slate splits in layers
    face = warped(rng, 8, 0.4, 6)
    # a rune in the middle of each slab: strokes drawn from a small random set of lines
    rune = np.zeros((N, N), np.float32)
    lx, ly = sx - 0.5, sy - 0.5
    strokes = [((-0.18, -0.25), (-0.18, 0.25)), ((0.18, -0.25), (0.18, 0.25)), ((-0.18, -0.25), (0.18, 0.05)),
               ((-0.18, 0.05), (0.18, -0.25)), ((-0.18, 0.25), (0.18, 0.25)), ((0.0, -0.3), (0.0, 0.3)),
               ((-0.2, 0.0), (0.2, 0.0)), ((-0.18, -0.25), (0.18, 0.25)), ((-0.18, 0.25), (0.18, -0.25))]
    pick = rng.random((S * S, len(strokes))) < 0.42
    for k, ((x0, y0), (x1, y1)) in enumerate(strokes):
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((lx - x0) * dx + (ly - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        dist = np.hypot(lx - (x0 + dx * t), ly - (y0 + dy * t))
        on = pick[sid % (S * S), k]
        rune = np.maximum(rune, smooth(0.022, 0.012, dist) * on)
    ring = smooth(0.012, 0.006, np.abs(np.hypot(lx, ly) - 0.38))
    carve = np.clip(rune + ring, 0, 1) * inside
    col = tint(rgb(0.13, 0.14, 0.16), (layers - 0.5) * 0.5 + (face - 0.5) * 0.3)
    col = mix(rgb(0.04, 0.04, 0.05), col, inside)
    col = mix(col, rgb(0.55, 0.06, 0.08), carve * 0.9)
    h = inside * (0.8 + layers * 0.1) - carve * 0.3
    rough = np.clip(0.7 + (layers - 0.5) * 0.3 - carve * 0.3, 0, 1)
    return write("RuneSlate", col, h, rough, np.zeros_like(h), 6, rng, cavity=0.45)


def MossyFlagstone(rng):
    """Irregular grey flagstones set in earth, moss creeping up from the joints (the old courtyard paths)."""
    f1, f2, ids = voronoi(rng, 6, jitter=0.95)
    e = f2 - f1
    inside = smooth(0.04, 0.1, e)
    tone = (cellrand(rng, 64, ids) - 0.5) * 0.3
    face = warped(rng, 12, 0.35, 7)
    moss_n = warped(rng, 20, 0.6, 5)
    moss = smooth(0.35, 0.6, moss_n * (1 - smooth(0.04, 0.22, e)) + (1 - inside) * 0.6)
    col = tint(rgb(0.42, 0.42, 0.40), tone + (face - 0.5) * 0.4)
    col = mix(tint(rgb(0.16, 0.12, 0.08), (face - 0.5) * 0.5), col, inside)
    col = mix(col, tint(rgb(0.21, 0.30, 0.11), (moss_n - 0.5) * 0.6), moss * 0.85)
    h = inside * (0.75 + face * 0.25) + moss * 0.05
    rough = np.clip(0.75 + moss * 0.15 + (face - 0.5) * 0.15, 0, 1)
    return write("MossyFlagstone", col, h, rough, np.zeros_like(h), 6, rng)


def QuatrefoilTile(rng):
    """Gothic cathedral floor: cream tiles inlaid with black quatrefoils and small crimson diamonds between them."""
    T = 4
    lx, ly = (U * T - np.floor(U * T)) * 2 - 1, (V * T - np.floor(V * T)) * 2 - 1
    rr = np.hypot(lx, ly)
    th = np.arctan2(ly, lx)
    foil = smooth(0.66, 0.6, rr / (0.75 + 0.25 * np.abs(np.cos(th * 2))))       # four lobes
    foil_inner = smooth(0.33, 0.28, rr / (0.75 + 0.25 * np.abs(np.cos(th * 2))))
    corner = smooth(0.24, 0.2, np.abs(np.abs(lx) - 1) + np.abs(np.abs(ly) - 1))   # diamonds at the tile corners
    seam = 1 - smooth(0.97, 0.985, np.maximum(np.abs(lx), np.abs(ly)))
    worn = warped(rng, 4, 0.7, 6)
    cream = tint(rgb(0.80, 0.74, 0.62), (worn - 0.5) * 0.3)
    col = mix(cream, rgb(0.06, 0.05, 0.05), np.clip(foil - foil_inner, 0, 1))
    col = mix(col, rgb(0.50, 0.06, 0.08), foil_inner * 0.9)
    col = mix(col, rgb(0.50, 0.06, 0.08), corner)
    col = mix(col, rgb(0.33, 0.27, 0.22), smooth(0.6, 0.85, worn) * 0.35)
    col = mix(col, rgb(0.18, 0.15, 0.12), (1 - seam) * 0.8)
    h = 0.7 + seam * 0.2 - (1 - seam) * 0.2
    rough = np.clip(0.3 + smooth(0.55, 0.85, worn) * 0.35 + (1 - seam) * 0.4, 0, 1)
    return write("QuatrefoilTile", col, h, rough, np.zeros_like(h), 3, rng, cavity=0.4)


SETS = [ParquetWood, FloorPlanks, RedBrick, StoneBlock, Cobblestone, HexTile, Pavers, Concrete,
        PaintedMetal, DirtyTile, DarkPlaster, CheckerMarble, OldBoards, SnowGround,
        DamaskWallpaper, CrimsonVelvet, GothicStone, WroughtIron, StainedGlass, BloodMarble, GothicOakPanel,
        RuneSlate, MossyFlagstone, QuatrefoilTile]


def sheet(colors):
    """A contact sheet of the colour maps (4 across, 256 px each, each repeated 2 x 2 to show the tiling)."""
    cols, tile = 4, 256
    rows = math.ceil(len(colors) / cols)
    out = np.full((rows * tile, cols * tile, 3), 0.06, np.float32)
    for i, c in enumerate(colors):
        small = c[::N // 128, ::N // 128]       # 128 px
        rep = np.tile(small, (2, 2, 1))          # 256 px, 2 x 2: seams would show here
        r, k = divmod(i, cols)
        out[r * tile:(r + 1) * tile, k * tile:(k + 1) * tile] = rep
    H, W = out.shape[:2]
    rgba = np.dstack([out, np.ones((H, W), np.float32)])[::-1].astype(np.float32)
    img = bpy.data.images.new("_sheet", W, H, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = os.path.join(OUT, "_sheet.png")
    img.file_format = 'PNG'
    img.save()
    print("wrote _sheet.png")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    want = set(argv)
    colors = []
    for i, fn in enumerate(SETS):
        if want and fn.__name__ not in want:
            continue
        rng = np.random.default_rng(1000 + i)
        colors.append(fn(rng))
    if not want:
        sheet(colors)


if __name__ == "__main__":
    main()
