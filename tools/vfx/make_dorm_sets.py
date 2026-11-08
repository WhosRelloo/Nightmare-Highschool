"""The dorm room kit's seamless 2048 PBR sets (props batch 34, the dorm kit), for its tiled shell pieces (world UVs, like
nh_props.TILED) and for a builder's own walls as MaterialVariants:

  NH_DormPlaster  dark, sooty lime plaster: trowel-smoothed plateaus, fine sand grain, soot mottling, a few hairline cracks
                  (walls above the wainscot, the ceiling, door and window reveals)          6 studs a tile
  NH_DormEnamel   crimson (#600E1A) enamel on cast iron, a fine orange-peel, chipped to the iron here and there (the
                  wainscot's panel fields)                                                    4 studs a tile
  NH_DormFloor    dark slate flags laid in a running bond, 2.5 studs square, worn smooth where walked, chipped arrises,
                  recessed dark joints (the floor)                                            5 studs a tile

usage: python tools/vfx/make_dorm_sets.py [outdir=art/props/textures] [size=2048]
Everything is periodic over the texture, so each set tiles in both directions. Writes <Set>_{color,normal,rough,metal}.png
(the plaster and the floor have no metal; their metal maps are black and stay out of the upload).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "props", "textures")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048


def pnoise(sigma, seed, sx=1.0, sy=1.0):
    """Periodic smooth noise 0..1: white noise low-passed in the frequency domain (sigma ~ feature size in px; sx / sy
    stretch it)."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((N, N)).astype(np.float32)
    fy = np.fft.fftfreq(N)[:, None] * sy
    fx = np.fft.fftfreq(N)[None, :] * sx
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * math.pi * sigma) ** 2 / 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * g)).astype(np.float32)
    out -= out.min()
    return out / max(1e-6, out.max())


def fbm(sigma, seed, octaves=5, sx=1.0, sy=1.0):
    out = np.zeros((N, N), np.float32)
    amp = tot = 0.0
    amp = 1.0
    for o in range(octaves):
        out += pnoise(max(0.7, sigma / 2 ** o), seed + o, sx, sy) * amp
        tot += amp
        amp *= 0.52
    out /= tot
    out -= out.min()
    return out / max(1e-6, out.max())


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def to_lin(c):
    c = np.asarray(c, np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def normal_from(h, strength):
    """Tangent-space normal (OpenGL, green up, as Blender bakes) from a periodic height field, wrapping at the edges."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def wrapped_lines(paths, width, seed=0):
    """A mask of polylines drawn at their wrapped copies, so cracks cross the tile edges seamlessly."""
    im = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(im)
    for item in paths:
        pts, wl = item if isinstance(item, tuple) else (item, width)
        for dx in (-N, 0, N):
            for dy in (-N, 0, N):
                p = [(x + dx, y + dy) for x, y in pts]
                for (x0, y0), (x1, y1), w in zip(p, p[1:], wl):
                    d.line((x0, y0, x1, y1), fill=255, width=max(1, int(round(w))))
    return np.asarray(im, np.float32) / 255


def crack_path(rng, x, y, steps, step, ang):
    pts = [(x, y)]
    widths = []
    for i in range(steps):
        ang += rng.normal(0, 0.35)
        x += math.cos(ang) * step
        y += math.sin(ang) * step
        pts.append((x, y))
        t = i / steps
        widths.append(2.6 * math.sin(math.pi * min(1.0, t * 1.2 + 0.05)) + 0.6)
    return pts, widths


def save(name, col_lin, nrm, rough, metal):
    Image.fromarray((to_srgb(col_lin) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f"{name}_color.png"))
    Image.fromarray((np.clip(nrm, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f"{name}_normal.png"))
    Image.fromarray((np.clip(rough, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(os.path.join(OUT, f"{name}_rough.png"))
    Image.fromarray((np.clip(metal, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(os.path.join(OUT, f"{name}_metal.png"))
    print(f"wrote {name}_{{color,normal,rough,metal}}.png ({N})")


# ------------------------------------------------------------------ plaster

def plaster():
    rng = np.random.default_rng(3401)
    k = N / 2048
    broad = fbm(420 * k, 10, 5)
    trowel_n = pnoise(70 * k, 20, sx=0.35, sy=1.0)               # long sweeps, wider than tall
    trowel_m = pnoise(40 * k, 21, sx=1.0, sy=0.45)
    plate = smooth(0.42, 0.62, trowel_n * 0.6 + trowel_m * 0.4)  # plateaus where the trowel smoothed it, ridges between
    sand = pnoise(1.1 * k, 30)
    mott_h = pnoise(24 * k, 33)
    pits = (pnoise(1.6 * k, 31) > 0.82).astype(np.float32) * pnoise(30 * k, 32)
    paths = []
    for _ in range(4):
        p, w = crack_path(rng, rng.uniform(0, N), rng.uniform(0, N), int(rng.integers(14, 26)), 22 * k, rng.uniform(0, 2 * math.pi))
        paths.append((p, [x * 0.8 * k for x in w]))
        for _b in range(int(rng.integers(0, 3))):
            j = int(rng.integers(2, len(p) - 1))
            q, wq = crack_path(rng, p[j][0], p[j][1], int(rng.integers(4, 10)), 16 * k, rng.uniform(0, 2 * math.pi))
            paths.append((q, [x * 0.55 * k for x in wq]))
    crack = wrapped_lines(paths, None)
    crack = np.asarray(Image.fromarray((crack * 255).astype(np.uint8)), np.float32) / 255
    h = 0.2 * broad + 0.12 * mott_h + 0.3 * plate + 0.08 * sand - 0.12 * pits - 0.35 * crack
    # colour: warm charcoal with a hint of plum, mottled with soot, paler where the trowel burnished it
    base = to_lin((62, 52, 56))
    mott = fbm(110 * k, 40, 5)                                    # mid-scale mottling (no big blotches: they show as a repeat)
    soot = fbm(220 * k, 41, 5, sx=1.0, sy=0.4)                    # soot settles in soft vertical drifts
    tone = 0.9 + 0.12 * (broad - 0.5) + 0.16 * (mott - 0.5) + 0.12 * plate + 0.08 * (sand - 0.5)
    col = base[None, None, :] * tone[..., None]
    col = col * (1 - 0.18 * smooth(0.35, 0.85, soot))[..., None]
    warm = smooth(0.5, 0.9, mott) * 0.15
    col = col * (1 - warm)[..., None] + to_lin((66, 50, 42))[None, None, :] * warm[..., None]
    col = col * (1 - 0.55 * crack)[..., None]
    rough = 0.9 - 0.08 * plate + 0.04 * (sand - 0.5) + 0.05 * crack
    save("NH_DormPlaster", col, normal_from(h, 6.0 * k), rough, np.zeros((N, N), np.float32))


# ------------------------------------------------------------------ crimson enamel on iron

def enamel():
    k = N / 2048
    peel = pnoise(3.0 * k, 50)
    peel2 = pnoise(9.0 * k, 51)
    broad = fbm(380 * k, 52, 4)
    chips_n = pnoise(14 * k, 53) * 0.65 + pnoise(60 * k, 54) * 0.35
    chip = smooth(0.735, 0.75, chips_n)                       # bare iron
    rim = smooth(0.70, 0.735, chips_n) * (1 - chip)          # the enamel's broken edge, a hair raised
    scratch_paths = []
    rng = np.random.default_rng(3402)
    for _ in range(18):
        x, y = rng.uniform(0, N), rng.uniform(0, N)
        a = rng.normal(0.25, 0.5)
        L = rng.uniform(40, 160) * k
        scratch_paths.append([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)])
    scr = wrapped_lines(scratch_paths, [1.2 * k])
    h = 0.05 * peel + 0.04 * peel2 + 0.6 * (1 - chip) + 0.1 * rim - 0.1 * scr
    red = to_lin((96, 14, 26))
    col = red[None, None, :] * (0.78 + 0.32 * broad + 0.06 * (peel2 - 0.5))[..., None]
    col = col * (1 - 0.3 * scr)[..., None]
    iron = to_lin((46, 44, 46))[None, None, :] * (0.8 + 0.4 * pnoise(2.0 * k, 55))[..., None]
    rust = to_lin((70, 40, 28))[None, None, :]
    edge_rust = smooth(0.0, 1.0, rim) * 0.5
    col = col * (1 - chip)[..., None] + iron * chip[..., None]
    col = col * (1 - edge_rust)[..., None] + rust * edge_rust[..., None]
    rough = 0.32 + 0.1 * broad + 0.05 * (peel - 0.5)
    rough = rough * (1 - chip) + 0.55 * chip + 0.15 * scr
    metal = chip * 0.9
    save("NH_DormEnamel", col, normal_from(h, 9.0 * k), rough, metal)


# ------------------------------------------------------------------ slate flags

def floor():
    k = N / 2048
    rng = np.random.default_rng(3403)
    flag = N // 2                       # 2 x 2 flags a tile, 2.5 studs each at 5 studs a tile
    joint = 11 * k                      # half the joint width (px)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    row = (yy // flag).astype(int)
    xo = (xx + (row % 2) * flag / 2) % N           # running bond: every other row half a flag along
    col_i = (xo // flag).astype(int)
    fid = row * 2 + col_i
    ux = xo % flag
    uy = yy % flag
    d_edge = np.minimum(np.minimum(ux, flag - ux), np.minimum(uy, flag - uy))   # px from the flag's edge
    wob = (pnoise(18 * k, 60) - 0.5) * 9 * k + (pnoise(4 * k, 61) - 0.5) * 3 * k
    chips = smooth(0.7, 0.85, pnoise(10 * k, 62)) * 14 * k                      # chipped arrises
    de = d_edge + wob - chips
    in_flag = smooth(joint - 1.5, joint + 1.5, de)
    bevel = np.clip((de - joint) / (16 * k), 0, 1) ** 0.6
    grain = fbm(160 * k, 63, 5)
    fine = pnoise(1.0 * k, 64)
    mid = pnoise(9 * k, 67)
    speck = smooth(0.8, 0.86, pnoise(2.2 * k, 68))                 # pale mica specks
    lam = pnoise(30 * k, 65, sx=1.0, sy=0.25)       # the slate's lamination, faint banding
    vein = 1 - np.abs(pnoise(70 * k, 69, sx=1.0, sy=0.3) - 0.5) * 2  # thin pale quartz veins, here and there
    vein = smooth(0.975, 0.996, vein) * smooth(0.55, 0.75, pnoise(220 * k, 70))
    wear = smooth(0.4, 0.8, fbm(300 * k, 66, 4))
    h = in_flag * (0.55 + 0.25 * bevel + 0.1 * grain + 0.05 * fine + 0.05 * mid + 0.04 * lam - 0.02 * vein) + (1 - in_flag) * (0.12 + 0.05 * fine)
    # each flag its own shade of dark slate (blue-grey to green-grey to near black)
    tones = [to_lin(c) for c in ((50, 53, 58), (44, 47, 50), (55, 56, 58), (40, 43, 44), (48, 50, 52), (37, 38, 42))]
    picks = rng.integers(0, len(tones), 4)
    lift = rng.uniform(0.86, 1.12, 4)
    col = np.zeros((N, N, 3), np.float32)
    for f in range(4):
        m = (fid == f)
        col[m] = tones[picks[f]] * lift[f]
    col *= (0.78 + 0.4 * grain + 0.1 * (fine - 0.5) + 0.12 * (mid - 0.5) + 0.12 * (lam - 0.5) + 0.18 * vein + 0.25 * speck)[..., None]
    col *= (1 + 0.12 * wear)[..., None]                       # walked paler and smoother
    dirt = (1 - bevel) * in_flag
    col *= (1 - 0.3 * dirt)[..., None]
    grout = to_lin((26, 23, 22))[None, None, :] * (0.8 + 0.4 * fine)[..., None]
    col = col * in_flag[..., None] + grout * (1 - in_flag)[..., None]
    rough = in_flag * (0.72 - 0.18 * wear + 0.06 * (fine - 0.5)) + (1 - in_flag) * 0.95
    save("NH_DormFloor", col, normal_from(h, 7.0 * k), rough, np.zeros((N, N), np.float32))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    plaster()
    enamel()
    floor()
