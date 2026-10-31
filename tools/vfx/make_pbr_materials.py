"""Seamless PBR surface materials for the school (numpy + Pillow, no Blender needed).

usage: python make_pbr_materials.py <outdir> [size=1024] [only these, e.g. leather brass]

Writes, for each material, four 8-bit PNG maps that tile seamlessly in both directions:
  <name>_color.png      albedo, kept light and fairly neutral: Roblox multiplies it by the part's Color
  <name>_normal.png     tangent-space normal map, OpenGL convention (green = up), as Roblox expects
  <name>_rough.png      roughness (white = rough)
  <name>_metal.png      metalness (white = metal)

Materials (Roblox MaterialVariant name -> base material, suggested StudsPerTile):
  NH_Linoleum      CeramicTiles  6   worn classroom vinyl tiles: two-tone checker, speckle, grime at the grout, wax sheen
  NH_Boards        WoodPlanks    12  scuffed hallway floorboards: staggered planks, grain, gaps, a worn centre path
  NH_DeskWood      Wood          8   varnished desk/furniture wood: fine straight grain, satin, small dents and pen scratches
  NH_PaintedMetal  Metal         6   chipped enamel steel: orange-peel paint, chips and scratches showing bare metal
  NH_Slate         Slate         10  layered cleft slate: stepped layers, cool grey with mineral tints, polished edges
  NH_Leather       (props)           pebbled leather with creases and worn sheen (tinted per prop)
  NH_Brass         (props)           brushed brass with green-brown patina, pits and scratches
  NH_Limestone     (props)           carved limestone: pores, chisel marks, stains
  NH_Iron          (props)           hammered wrought iron: dimples, raised rims, rust
  NH_Paper         (props)           aged paper: fibres, foxing

Everything tiles because every noise and pattern uses integer periods over the texture.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "pbr_out"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ noise (periodic)

def _smooth(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def vnoise(px, py, seed):
    """Value noise with px x py cells over the texture; wraps at the edges."""
    r = np.random.default_rng(seed)
    g = r.random((py, px))
    x = np.arange(N) * px / N
    y = np.arange(N) * py / N
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = _smooth(x - x0)[None, :]
    fy = _smooth(y - y0)[:, None]
    x1 = (x0 + 1) % px
    y1 = (y0 + 1) % py
    a = g[y0][:, x0]
    b = g[y0][:, x1]
    c = g[y1][:, x0]
    d = g[y1][:, x1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(px, py, octaves, seed, gain=0.5):
    total = np.zeros((N, N))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        total += vnoise(px * 2 ** o, py * 2 ** o, seed + o * 97) * amp
        norm += amp
        amp *= gain
    return total / norm


def warp(img, dx, dy):
    """Sample img at (x + dx, y + dy) pixels with wrap-around (domain warp)."""
    yy, xx = np.mgrid[0:N, 0:N]
    xs = (xx + dx).astype(int) % N
    ys = (yy + dy).astype(int) % N
    return img[ys, xs]


def blur(a, radius):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    # wrap: tile 3x3, blur, crop the centre so the blur also wraps
    big = Image.new("L", (N * 3, N * 3))
    for i in range(3):
        for j in range(3):
            big.paste(im, (i * N, j * N))
    big = big.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(big.crop((N, N, 2 * N, 2 * N)), dtype=np.float32) / 255


def lines(count, length, width, seed, angle_jitter=math.pi, base_angle=0.0):
    """Thin random strokes (scratches) drawn with wrap-around. Returns a 0..1 mask."""
    r = np.random.default_rng(seed)
    big = Image.new("L", (N * 3, N * 3), 0)
    d = ImageDraw.Draw(big)
    for _ in range(count):
        x, y = r.random() * N, r.random() * N
        a = base_angle + (r.random() - 0.5) * angle_jitter
        L = length * (0.4 + r.random())
        pts = []
        for k in range(8):  # slightly curved stroke
            t = k / 7
            a2 = a + math.sin(t * 3 + r.random()) * 0.15
            pts.append((x + math.cos(a2) * L * t, y + math.sin(a2) * L * t))
        w = max(1, int(width * (0.5 + r.random())))
        for ox in (0, N, 2 * N):
            for oy in (0, N, 2 * N):
                d.line([(px + ox, py + oy) for px, py in pts], fill=int(140 + r.random() * 115), width=w)
    m = big.crop((N, N, 2 * N, 2 * N))
    # fold the 3x3 copies back into one tile
    acc = np.zeros((N, N), np.float32)
    arr = np.asarray(big, dtype=np.float32) / 255
    for i in range(3):
        for j in range(3):
            acc = np.maximum(acc, arr[j * N:(j + 1) * N, i * N:(i + 1) * N])
    return acc


def normal_from_height(h, strength):
    dhdu = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dhdv = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5   # rows go down; v goes up (OpenGL)
    nx, ny, nz = -dhdu * strength, -dhdv * strength, np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5


def save(name, color, height, strength, rough, metal):
    def u8(a):
        return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(u8(color), "RGB").save(os.path.join(OUT, f"{name}_color.png"))
    Image.fromarray(u8(normal_from_height(height, strength)), "RGB").save(os.path.join(OUT, f"{name}_normal.png"))
    Image.fromarray(u8(rough), "L").save(os.path.join(OUT, f"{name}_rough.png"))
    Image.fromarray(u8(metal), "L").save(os.path.join(OUT, f"{name}_metal.png"))
    print("wrote", name)


def rgb(r, g, b):
    return np.array([r, g, b], np.float32) / 255


yy, xx = np.mgrid[0:N, 0:N] / N

# ------------------------------------------------------------------ 1. linoleum tiles
def linoleum():
    T = 4                                  # tiles across the texture
    cell = N // T
    tx, ty = (np.arange(N) // cell)[None, :], (np.arange(N) // cell)[:, None]
    fx, fy = (np.arange(N) % cell)[None, :], (np.arange(N) % cell)[:, None]
    edge = np.minimum(np.minimum(fx, cell - 1 - fx), np.minimum(fy, cell - 1 - fy)).astype(np.float32)
    grout = (edge < 2.5).astype(np.float32)
    bevel = np.clip(edge / 6, 0, 1)
    checker = ((tx + ty) % 2).astype(np.float32)
    r = np.random.default_rng(3)
    tone = r.uniform(-0.025, 0.025, (T, T))[ty % T, tx % T]
    speck = fbm(N // 8, N // 8, 2, 11)                      # vinyl speckle
    speck = (speck > 0.62).astype(np.float32) * 0.06 - (speck < 0.3).astype(np.float32) * 0.04
    mottle = fbm(16, 16, 4, 21) - 0.5
    grime = fbm(4, 4, 5, 31)
    near_grout = 1 - np.clip(edge / 22, 0, 1)
    scuff = blur(lines(70, N * 0.06, 2, 41), 1.2)
    base = 0.86 - 0.07 * checker + tone + speck + mottle * 0.05
    dirt = np.clip(near_grout * 0.45 + (grime - 0.5) * 0.35 + scuff * 0.35, 0, 1)
    lum = base * (1 - 0.28 * dirt)
    lum = lum * (1 - grout) + 0.38 * grout
    col = lum[..., None] * rgb(232, 234, 238)[None, None, :] / rgb(232, 234, 238).max()
    height = bevel * 0.9 + (fbm(64, 64, 2, 51) - 0.5) * 0.03 - scuff * 0.06
    rough = np.clip(0.3 + dirt * 0.32 + (mottle * 0.08) + scuff * 0.15, 0, 1) * (1 - grout) + 0.85 * grout
    save("NH_Linoleum", col, height, 5.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ wood grain helper
def grain(rows_period, seed, fine=1.0):
    """Wood grain running along U: long streaks plus warped growth rings."""
    streak = fbm(2, int(96 * fine), 5, seed)                       # long thin streaks across V
    warpv = (fbm(4, 4, 3, seed + 5) - 0.5) * N * 0.06
    ringsrc = warp(fbm(1, int(rows_period), 3, seed + 9), np.zeros((N, N)), warpv)
    rings = 0.5 + 0.5 * np.sin(ringsrc * 2 * math.pi * 6)
    return streak, rings


# ------------------------------------------------------------------ 2. floorboards
def boards():
    R = 6                                   # planks stacked along V
    rowh = N // R
    row = (np.arange(N) // rowh)[:, None] * np.ones((1, N), int)
    fy = (np.arange(N) % rowh)[:, None].astype(np.float32)
    r = np.random.default_rng(7)
    seams = {k: sorted(r.random(2)) for k in range(R)}
    seg = np.zeros((N, N), int)
    seamdist = np.full((N, N), 1e9, np.float32)
    for k in range(R):
        rows = slice(k * rowh, (k + 1) * rowh)
        u = np.arange(N) / N
        s0, s1 = seams[k]
        segrow = ((u >= s0) & (u < s1)).astype(int)        # wraps: [s1,1)+[0,s0) is one board
        seg[rows, :] = segrow[None, :] + k * 2
        d = np.minimum.reduce([np.abs(u - s0), np.abs(u - s1), 1 - np.abs(u - s0), 1 - np.abs(u - s1)]) * N
        seamdist[rows, :] = d[None, :]
    gap_v = np.minimum(fy, rowh - 1 - fy)
    gap = ((gap_v < 2.0) | (seamdist < 1.6)).astype(np.float32)
    plank_tone = r.uniform(-0.09, 0.07, R * 2)[seg]
    plank_hue = r.uniform(-0.03, 0.03, R * 2)[seg]
    streak, rings = grain(R * 2, 61)
    knots = np.clip((fbm(6, 6, 3, 71) - 0.78) * 6, 0, 1)
    wear = np.clip((1 - np.abs(yy - 0.5) * 2.2) * 0.6 + (fbm(3, 3, 4, 81) - 0.5) * 0.6, 0, 1)
    scr = blur(lines(90, N * 0.08, 2, 91, angle_jitter=0.5), 0.8)
    lum = 0.74 + plank_tone + (streak - 0.5) * 0.22 + (rings - 0.5) * 0.08 - knots * 0.25 + wear * 0.06 + scr * 0.05
    col = np.stack([lum * (1.0 + plank_hue), lum * 0.80, lum * 0.60], -1)
    col = col * (1 - gap[..., None]) + 0.12 * gap[..., None]
    cup = 1 - (np.abs(fy - rowh / 2) / (rowh / 2)) ** 4 * 0.25
    height = cup * (1 - gap) - gap * 0.6 + (streak - 0.5) * 0.12 + (rings - 0.5) * 0.05 - scr * 0.05
    rough = np.clip(0.52 + (streak - 0.5) * 0.15 + wear * 0.18 + scr * 0.1, 0, 1) * (1 - gap) + 0.9 * gap
    save("NH_Boards", np.clip(col, 0, 1), height, 4.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ 3. desk wood
def deskwood():
    streak, rings = grain(10, 111, fine=1.4)
    pores = (fbm(4, 256, 2, 121) > 0.68).astype(np.float32)
    dents = np.clip((fbm(12, 12, 3, 131) - 0.8) * 5, 0, 1)
    pen = blur(lines(28, N * 0.12, 1, 141), 0.6)
    lum = 0.80 + (streak - 0.5) * 0.26 + (rings - 0.5) * 0.1 - pores * 0.06 - dents * 0.05
    col = np.stack([lum, lum * 0.80, lum * 0.62], -1)
    col = col * (1 - pen[..., None] * 0.35) + pen[..., None] * 0.35 * rgb(70, 76, 110)
    height = (streak - 0.5) * 0.15 + (rings - 0.5) * 0.06 - pores * 0.06 - dents * 0.35 - pen * 0.08
    rough = np.clip(0.36 + (streak - 0.5) * 0.08 + pores * 0.15 + pen * 0.1, 0, 1)
    save("NH_DeskWood", np.clip(col, 0, 1), height, 3.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ 4. painted metal
def paintedmetal():
    peel = fbm(48, 48, 3, 201)                                   # orange-peel enamel
    chipsrc = fbm(10, 10, 5, 211)
    chip = np.clip((chipsrc - 0.74) * 25, 0, 1)
    chip_edge = np.clip((chipsrc - 0.715) * 25, 0, 1) - chip
    scr = blur(lines(120, N * 0.07, 1, 221), 0.7)
    bare = np.clip(chip + scr * 0.9, 0, 1)
    rust = np.clip((fbm(20, 20, 3, 231) - 0.6) * 4, 0, 1) * chip
    grime = fbm(3, 3, 4, 241)
    paint = 0.86 + (peel - 0.5) * 0.04 - (grime - 0.5) * 0.08
    col = paint[..., None] * rgb(236, 238, 240)[None, None, :]
    metal_col = (0.58 + (fbm(64, 64, 2, 251) - 0.5) * 0.1)[..., None] * np.ones(3)
    rust_col = rgb(120, 70, 45)[None, None, :] * np.ones((N, N, 1))
    col = col * (1 - bare[..., None]) + metal_col * bare[..., None]
    col = col * (1 - rust[..., None] * 0.7) + rust_col * rust[..., None] * 0.7
    col = col * (1 - chip_edge[..., None] * 0.35)
    height = (peel - 0.5) * 0.04 - chip * 0.5 - scr * 0.15 + chip_edge * 0.1
    rough = np.clip(0.42 + (peel - 0.5) * 0.06 + (grime - 0.5) * 0.12, 0, 1) * (1 - bare) + (0.32 + rust * 0.5) * bare
    metal = np.clip(bare * (1 - rust), 0, 1)
    save("NH_PaintedMetal", np.clip(col, 0, 1), height, 6.0, rough, metal)


# ------------------------------------------------------------------ 5. slate
def slate():
    layers = fbm(2, 12, 4, 301) * 0.75 + fbm(6, 6, 4, 311) * 0.25
    steps = np.floor(layers * 7) / 7
    h = steps * 0.75 + layers * 0.25
    cracks = blur(lines(40, N * 0.2, 1, 321, angle_jitter=0.6), 0.6)
    tint = fbm(3, 3, 3, 331)
    # darker where one layer steps down to the next, lighter on the raised layer lips
    step_edge = np.clip(np.abs(steps - np.roll(steps, 2, 0)) * 7, 0, 1)
    lip = np.clip((steps - np.roll(steps, -2, 0)) * 7, 0, 1)
    lum = 0.42 + (h - 0.5) * 0.25 + (fbm(64, 64, 2, 341) - 0.5) * 0.05 - cracks * 0.15 - step_edge * 0.12 + lip * 0.08
    col = np.stack([lum * (0.92 + tint * 0.06), lum * (0.96 + (1 - tint) * 0.04), lum * 1.06], -1)
    rough = np.clip(0.78 - (h - 0.5) * 0.35 + cracks * 0.15, 0, 1)
    save("NH_Slate", np.clip(col, 0, 1), h - cracks * 0.2, 9.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ cellular (Worley) noise, periodic

def worley(cells, seed):
    """Distance to the nearest jittered point (F1) and the second nearest (F2), cells x cells over the texture;
    wraps at the edges. Returns (f1, f2) in cell units."""
    r = np.random.default_rng(seed)
    jx = r.random((cells, cells))
    jy = r.random((cells, cells))
    x = (np.arange(N) * cells / N)[None, :].repeat(N, 0)
    y = (np.arange(N) * cells / N)[:, None].repeat(N, 1)
    ci = np.floor(x).astype(int)
    cj = np.floor(y).astype(int)
    d1 = np.full((N, N), 9.0)
    d2 = np.full((N, N), 9.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ni = (ci + di) % cells
            nj = (cj + dj) % cells
            px = ci + di + jx[nj, ni]
            py = cj + dj + jy[nj, ni]
            d = np.sqrt((x - px) ** 2 + (y - py) ** 2)
            d2 = np.where(d < d1, d1, np.minimum(d2, d))
            d1 = np.minimum(d1, d)
    return d1, d2


# ------------------------------------------------------------------ 6. leather
def leather():
    f1, f2 = worley(64, 401)
    pebble = np.clip(1 - f1 * 1.15, 0, 1) ** 1.5                    # rounded pebbles
    seams = np.clip(1 - (f2 - f1) * 6, 0, 1)                         # valleys between pebbles
    crease_src = fbm(3, 3, 4, 411)
    creases = np.clip(1 - np.abs(crease_src - 0.5) * 22, 0, 1) * (fbm(6, 6, 3, 421) > 0.45)
    wear = fbm(4, 4, 4, 431)
    h = pebble * 0.6 - seams * 0.25 - creases * 0.5
    lum = 0.82 + (pebble - 0.5) * 0.06 - seams * 0.1 - creases * 0.12 + (wear - 0.5) * 0.1
    col = lum[..., None] * np.ones(3)
    rough = np.clip(0.55 - pebble * 0.18 + seams * 0.15 + creases * 0.1 - (wear - 0.5) * 0.15, 0, 1)
    save("NH_Leather", np.clip(col, 0, 1), h, 7.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ 7. tarnished brass
def brass():
    brushed = fbm(1, 256, 3, 501)                                   # fine streaks along U
    patina = np.clip((fbm(5, 5, 5, 511) - 0.58) * 4, 0, 1)
    pits = np.clip((fbm(48, 48, 2, 521) - 0.8) * 6, 0, 1)
    scr = blur(lines(90, N * 0.06, 1, 531), 0.6)
    base = rgb(222, 172, 92)
    dark = rgb(120, 86, 44)
    green = rgb(70, 92, 66)
    col = base[None, None, :] * (0.92 + (brushed - 0.5)[..., None] * 0.12)
    col = col * (1 - patina[..., None] * 0.55) + (dark * 0.6 + green * 0.4)[None, None, :] * patina[..., None] * 0.55
    col = col * (1 - pits[..., None] * 0.4)
    col = col + scr[..., None] * 0.08
    h = (brushed - 0.5) * 0.05 - pits * 0.3 - scr * 0.1 - patina * 0.05
    rough = np.clip(0.26 + (brushed - 0.5) * 0.08 + patina * 0.45 + pits * 0.2 - scr * 0.05, 0, 1)
    metal = np.clip(1 - patina * 0.75, 0, 1)
    save("NH_Brass", np.clip(col, 0, 1), h, 4.0, rough, metal)


# ------------------------------------------------------------------ 8. limestone
def limestone():
    f1, f2 = worley(96, 601)
    pores = np.clip(0.18 - f1, 0, 1) * 6                              # small dark pits
    chisel = fbm(1, 24, 4, 611)                                       # tool marks across V
    big = fbm(3, 3, 5, 621)
    stain = np.clip((fbm(4, 4, 5, 631) - 0.55) * 3, 0, 1)
    grain_n = fbm(64, 64, 2, 641)
    lum = 0.84 + (big - 0.5) * 0.12 + (grain_n - 0.5) * 0.06 - pores * 0.25 - stain * 0.18 + (chisel - 0.5) * 0.05
    col = np.stack([lum * 1.0, lum * 0.97, lum * 0.92], -1)
    h = (big - 0.5) * 0.3 + (chisel - 0.5) * 0.35 + (grain_n - 0.5) * 0.1 - pores * 0.5
    rough = np.clip(0.82 + (grain_n - 0.5) * 0.1 + pores * 0.1 - stain * 0.08, 0, 1)
    save("NH_Limestone", np.clip(col, 0, 1), h, 5.0, rough, np.zeros((N, N)))


# ------------------------------------------------------------------ 9. hammered wrought iron
def iron():
    f1, f2 = worley(28, 701)
    dimple = (f1 ** 2) * 1.2                                         # hammer dimples (low centre, raised rims)
    rims = np.clip(1 - (f2 - f1) * 5, 0, 1)
    rust = np.clip((fbm(6, 6, 5, 711) - 0.66) * 4, 0, 1)
    scale_n = fbm(48, 48, 2, 721)
    lum = 0.55 + (scale_n - 0.5) * 0.08 + rims * 0.05 - dimple * 0.05
    col = lum[..., None] * np.ones(3)
    rust_c = rgb(120, 62, 34)
    col = col * (1 - rust[..., None] * 0.6) + rust_c[None, None, :] * rust[..., None] * 0.6
    h = dimple * 0.8 + rims * 0.2 + (scale_n - 0.5) * 0.08 + rust * 0.1
    rough = np.clip(0.48 + (scale_n - 0.5) * 0.1 + rust * 0.4 - rims * 0.12, 0, 1)
    metal = np.clip(0.75 - rust * 0.7, 0, 1)
    save("NH_Iron", np.clip(col, 0, 1), h, 4.0, rough, metal)


# ------------------------------------------------------------------ 10. aged paper
def paper():
    fibres = fbm(8, 160, 2, 801) * 0.5 + fbm(160, 8, 2, 811) * 0.5
    foxing = np.clip((fbm(10, 10, 4, 821) - 0.66) * 5, 0, 1)
    age = fbm(3, 3, 4, 831)
    lum = 0.9 + (fibres - 0.5) * 0.06 - foxing * 0.18 - (age - 0.5) * 0.08
    col = np.stack([lum, lum * 0.95, lum * 0.82], -1)
    h = (fibres - 0.5) * 0.2 + (age - 0.5) * 0.1
    rough = np.clip(0.88 + (fibres - 0.5) * 0.05, 0, 1)
    save("NH_Paper", np.clip(col, 0, 1), h, 2.0, rough, np.zeros((N, N)))


if __name__ == "__main__":
    only = sys.argv[3:] if len(sys.argv) > 3 else None
    for f in (linoleum, boards, deskwood, paintedmetal, slate, leather, brass, limestone, iron, paper):
        if not only or f.__name__ in only:
            f()
