"""Seamless 2048 roof sets for the roof kit (props batch 28): the big roof planes are tiled with these instead of baked into
each prop's atlas, so they stay sharp however large the roof is.

usage: python tools/vfx/make_roof_tiles.py [outdir=art/props/textures] [size=2048]

  NH_RoofSlate    rectangular slates, 6 studs a tile: 10 courses of 0.6, six slates a course, staggered; cool blue,
                  purple and green-grey slates, chipped corners, cleft layers, worn butts, rain streaks, a little lichen
  NH_RoofMoss     the same slates gone over to moss: cushions along the butts and joints, lichen, heavier grime
  NH_RoofScale    fish-scale slates, 4 studs a tile: 8 courses of 0.5, five round-butted slates a course
  NH_RoofCrimson  the same fish scales in deep crimson glaze (#600E1A), glossy, the glaze worn thin at the edges
  NH_RoofCopper   standing-seam copper gone to verdigris, 6 studs a tile: seams every 1.5, cross welts, bronze showing
                  through in streaks (metal where the copper shows)
  NH_RoofLead     lead sheet, 6 studs a tile: wood rolls every 2, drips every 3, white bloom and rain streaks

In every set u runs along the eaves and v up the slope (the courses lie along u, the butts at the bottom of each course).
Everything is periodic over the texture, so it tiles both ways. The metal maps of the slate and glaze sets are all black
(Roblox drops those, so they are not uploaded).
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "props", "textures")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None

# pixel grids: u to the right, v up the slope (image rows run down, so v = N - 1 - row)
_row, _col = np.mgrid[0:N, 0:N].astype(np.float32)
U = _col / N
V = (N - 1 - _row) / N


def _smooth(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def vnoise(px, py, seed):
    """Value noise with px x py cells over the texture (py cells up v); wraps."""
    r = np.random.default_rng(seed)
    g = r.random((py, px)).astype(np.float32)
    x = U * px
    y = V * py
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = _smooth(x - x0)
    fy = _smooth(y - y0)
    x0 %= px
    y0 %= py
    x1 = (x0 + 1) % px
    y1 = (y0 + 1) % py
    a, b, c, d = g[y0, x0], g[y0, x1], g[y1, x0], g[y1, x1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(px, py, octaves, seed, gain=0.5):
    tot = np.zeros((N, N), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        tot += vnoise(px * 2 ** o, py * 2 ** o, seed + o * 131) * amp
        norm += amp
        amp *= gain
    return tot / norm


def wblur(a, radius):
    """Gaussian blur with wrap-around (float in, float out)."""
    f = np.fft.fftfreq(N)
    g = np.exp(-2 * (np.pi * radius) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))   # a Gaussian in frequency: it wraps
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def normal_from_height(h, strength):
    dhdu = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dhdv = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5   # rows go down; v goes up (OpenGL, as Roblox)
    nx, ny, nz = -dhdu * strength, -dhdv * strength, np.ones_like(h)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5


def save(name, lin_color, height_studs, tile, rough, metal, boost=1.6):
    def u8(a):
        return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(u8(to_srgb(lin_color)), "RGB").save(os.path.join(OUT, f"{name}_color.png"))
    # heights are in studs: a slope of dh/dpx * px-per-stud, a little exaggerated so it reads in Roblox's lighting
    Image.fromarray(u8(normal_from_height(height_studs, N / tile * boost)), "RGB").save(os.path.join(OUT, f"{name}_normal.png"))
    Image.fromarray(u8(rough), "L").save(os.path.join(OUT, f"{name}_rough.png"))
    Image.fromarray(u8(metal), "L").save(os.path.join(OUT, f"{name}_metal.png"))
    print("wrote", name)


# ------------------------------------------------------------------ rectangular slates

def slate_layout(tile=6.0, courses=10, per=6, seed=2801):
    """Which slate each pixel shows: course k, slate j, local fu (0..1 across), dv (studs up from its butt), and the
    per-slate random draws. Slates hang a little low at random, and some lose a bottom corner (the slate below shows)."""
    rnd = np.random.default_rng(seed)
    e = tile / courses
    w = tile / per
    drop = rnd.uniform(0.0, 0.05, (courses, per)).astype(np.float32)          # how far each slate's butt hangs low
    chip = rnd.random((courses, per, 2)).astype(np.float32)                    # corner chips (left, right)
    vs, us = V * tile, U * tile
    k0 = np.floor(vs / e).astype(int)
    dv0 = vs - k0 * e

    def slate_at(k):
        kk = k % courses
        uu = us + (kk % 2) * 0.5 * w
        j = np.floor(uu / w).astype(int)
        fu = uu / w - j
        return kk, j % per, fu
    kA, jA, fuA = slate_at(k0 + 1)               # the slate above may hang down into this course
    hang = (e - dv0) < drop[kA, jA]
    kB, jB, fuB = slate_at(k0)
    k = np.where(hang, kA, kB)
    j = np.where(hang, jA, jB)
    fu = np.where(hang, fuA, fuB)
    dv = np.where(hang, dv0 - e, dv0) + drop[k, j]      # studs above this slate's own butt
    # chipped bottom corners: a triangle off the corner shows the slate beneath, a shade lower
    c = 0.16
    left = (chip[k, j, 0] < 0.22) & (fu * w + dv < c)
    right = (chip[k, j, 1] < 0.22) & ((1 - fu) * w + dv < c)
    under = left | right
    return dict(e=e, w=w, k=k, j=j, fu=fu, dv=dv, under=under, rnd=rnd, courses=courses, per=per, tile=tile)


def slate_set(name, mossy=False):
    L = slate_layout()
    e, w, k, j, fu, dv, under = L["e"], L["w"], L["k"], L["j"], L["fu"], L["dv"], L["under"]
    rnd = np.random.default_rng(2802)
    C, S = L["courses"], L["per"]
    tone = rnd.uniform(0.72, 1.28, (C, S)).astype(np.float32)
    hue = rnd.integers(0, 3, (C, S))
    tilt = rnd.uniform(-0.012, 0.012, (C, S)).astype(np.float32)
    pal = np.array([[0.052, 0.058, 0.07], [0.058, 0.054, 0.066], [0.053, 0.059, 0.06]], np.float32)
    base = pal[hue[k, j]] * tone[k, j][..., None]
    cleft = fbm(18, 60, 5, 11, gain=0.6)             # cleft layering runs along the slate
    fine = fbm(128, 128, 3, 12)
    grain = fbm(40, 300, 2, 18)                      # fine split lines along the cleavage
    # height (studs): each slate tapers up toward its butt; joints and chips drop under
    gap = 0.018 / w
    joint = (fu < gap) | (fu > 1 - gap)
    h = 0.042 * (1 - np.clip(dv / e, 0, 1.2)) + tilt[k, j] * (fu - 0.5) + (cleft - 0.5) * 0.01 + (fine - 0.5) * 0.003 + (grain - 0.5) * 0.004
    h = np.where(joint, -0.012, h)
    h = np.where(under, -0.018 + (cleft - 0.5) * 0.004, h)
    h = wblur(h, 1.3)
    col = base * (0.8 + 0.4 * cleft[..., None]) * (0.9 + 0.2 * fine[..., None]) * (0.92 + 0.16 * grain[..., None])
    butt = smoothstep(0.05, 0.0, dv)                 # worn, paler butts catch the light
    col = col * (1 + 0.3 * butt[..., None])
    shade = smoothstep(e * 0.55, e, dv)              # tucked under the next course: darker
    col = col * (1 - 0.35 * shade[..., None])
    cast = smoothstep(e - 0.07, e - 0.005, dv)       # the shadow under the next course's butt
    col = col * (1 - 0.55 * cast[..., None])
    streak = fbm(30, 2, 3, 13)
    col = col * (0.8 + 0.4 * streak[..., None])
    col = np.where(joint[..., None], np.array([0.01, 0.011, 0.012], np.float32), col)
    col = np.where(under[..., None], col * 0.45, col)
    rough = 0.6 + (fine - 0.5) * 0.16 + (cleft - 0.5) * 0.1 - 0.06 * butt
    rough = np.where(joint | under, 0.9, rough)
    lich = wblur(smoothstep(0.8, 0.88, fbm(40, 40, 3, 14)) * (~joint), 1.5)
    lich_col = np.array([0.12, 0.125, 0.095], np.float32)
    amt = 0.3 if not mossy else 0.75
    col = col * (1 - amt * lich[..., None]) + lich_col * amt * lich[..., None]
    if mossy:
        # moss collects along the butts and joints and in big damp patches; raised cushions
        patch = smoothstep(0.5, 0.68, fbm(6, 6, 4, 15))
        along = np.maximum(smoothstep(e * 0.6, e * 0.95, dv), joint.astype(np.float32))
        tuft = fbm(90, 90, 3, 16)
        m = np.clip(along * 0.7 + patch * 0.7, 0, 1) * smoothstep(0.45, 0.7, tuft * 0.6 + patch * 0.5 + along * 0.2)
        m = wblur(m, 2.0)
        green = np.array([0.03, 0.058, 0.018], np.float32)
        yel = np.array([0.075, 0.09, 0.022], np.float32)
        mc = green * (1 - tuft[..., None]) + yel * tuft[..., None]
        col = col * (1 - m[..., None]) + mc * (0.7 + 0.6 * fine[..., None]) * m[..., None]
        h = h + m * (0.02 + 0.03 * tuft)
        rough = rough * (1 - m) + 0.95 * m
        orange = smoothstep(0.84, 0.9, fbm(36, 36, 3, 17)) * (1 - m)
        col = col * (1 - 0.8 * orange[..., None]) + np.array([0.2, 0.09, 0.02], np.float32) * 0.8 * orange[..., None]
        col = col * (0.85 + 0.15 * streak[..., None])
    save(name, col, h, L["tile"], np.clip(rough, 0, 1), np.zeros((N, N), np.float32))


# ------------------------------------------------------------------ fish scales (slate and crimson glaze)

def scale_layout(tile=4.0, courses=8, per=5):
    e = tile / courses
    w = tile / per
    r = w / 2
    vs, us = V * tile, U * tile
    k0 = np.floor(vs / e).astype(int)
    best_k = np.full((N, N), -10, int)
    best_j = np.zeros((N, N), int)
    best_dv = np.zeros((N, N), np.float32)
    best_dx = np.zeros((N, N), np.float32)
    for dk in (-1, 0, 1):                  # the topmost slate whose rounded butt lies below the point
        k = k0 + dk
        uu = us + (k % 2) * 0.5 * w
        j = np.floor(uu / w).astype(int)
        dx = (uu - (j + 0.5) * w)
        edge = k * e + (r - np.sqrt(np.maximum(r * r - dx * dx, 0)))
        ok = vs >= edge
        sel = ok & (k > best_k)
        best_k = np.where(sel, k, best_k)
        best_j = np.where(sel, j, best_j)
        best_dv = np.where(sel, vs - edge, best_dv)
        best_dx = np.where(sel, dx, best_dx)
    return dict(e=e, w=w, r=r, k=best_k % courses, j=best_j % per, dv=best_dv, dx=best_dx, courses=courses, per=per, tile=tile)


def scale_set(name, crimson=False):
    L = scale_layout()
    e, w, r, k, j, dv, dx = L["e"], L["w"], L["r"], L["k"], L["j"], L["dv"], L["dx"]
    C, S = L["courses"], L["per"]
    rnd = np.random.default_rng(2803 if not crimson else 2804)
    tone = rnd.uniform(0.75, 1.25, (C, S)).astype(np.float32)
    hue = rnd.integers(0, 3, (C, S))
    fine = fbm(64, 64, 3, 21)
    cleft = fbm(20, 50, 5, 22, gain=0.6)
    span = e + r
    h = 0.034 * (1 - np.clip(dv / span, 0, 1.0)) + (cleft - 0.5) * (0.006 if not crimson else 0.002) + (fine - 0.5) * 0.002
    # a tiny gap where two scales of one course meet
    side = np.abs(dx) > (r - 0.012)
    h = np.where(side, -0.01, h)
    h = wblur(h, 1.2)
    edge = smoothstep(0.045, 0.0, dv)
    shade = smoothstep(span * 0.45, span * 0.9, dv)
    streak = fbm(26, 2, 3, 23)
    if not crimson:
        pal = np.array([[0.046, 0.052, 0.066], [0.056, 0.047, 0.06], [0.047, 0.056, 0.052]], np.float32)
        col = pal[hue[k, j]] * tone[k, j][..., None] * (0.8 + 0.4 * cleft[..., None]) * (0.9 + 0.2 * fine[..., None])
        col = col * (1 + 0.32 * edge[..., None]) * (1 - 0.38 * shade[..., None]) * (0.8 + 0.4 * streak[..., None])
        rough = 0.6 + (fine - 0.5) * 0.16 - 0.05 * edge
        lich = wblur(smoothstep(0.82, 0.89, fbm(40, 40, 3, 24)), 1.5)
        col = col * (1 - 0.3 * lich[..., None]) + np.array([0.12, 0.125, 0.095], np.float32) * 0.3 * lich[..., None]
        metal = np.zeros((N, N), np.float32)
    else:
        # #600E1A is linear (0.117, 0.0087, 0.0103); a darker oxblood and a browner kiln shade among them
        pal = np.array([[0.117, 0.0087, 0.0103], [0.075, 0.006, 0.0078], [0.092, 0.011, 0.0095]], np.float32)
        col = pal[hue[k, j]] * tone[k, j][..., None] * (0.92 + 0.16 * fine[..., None])
        thin = np.array([0.2, 0.04, 0.03], np.float32)        # the glaze worn thin at the round butts
        col = col * (1 - 0.55 * edge[..., None]) + thin * 0.55 * edge[..., None]
        col = col * (1 - 0.5 * shade[..., None]) * (0.85 + 0.3 * streak[..., None])
        craze = smoothstep(0.62, 0.7, fbm(120, 120, 2, 25))
        col = col * (1 - 0.15 * craze[..., None])
        wear = smoothstep(0.66, 0.78, fbm(14, 14, 4, 26))
        rough = 0.24 + 0.06 * fine + 0.35 * wear + 0.3 * shade + 0.2 * edge
        metal = np.zeros((N, N), np.float32)
    col = np.where(side[..., None], col * 0.25, col)
    rough = np.where(side, 0.9, rough)
    save(name, col, h, L["tile"], np.clip(rough, 0, 1), metal)


# ------------------------------------------------------------------ copper and lead

def copper_set(name, tile=6.0):
    us, vs = U * tile, V * tile
    pan = 1.5
    p = us / pan - np.floor(us / pan)               # 0..1 across a pan
    dseam = np.abs(p - 0.5 * 0 - 0.0)
    dseam = np.minimum(p, 1 - p) * pan              # studs from the nearest seam
    seam = np.clip(1 - dseam / 0.045, 0, 1)
    seam = np.sqrt(seam)
    pi = np.floor(us / pan).astype(int)
    welt_off = (pi % 2) * 1.5
    wv = (vs + welt_off) % 3.0
    welt = smoothstep(0.03, 0.0, np.minimum(wv, 3.0 - wv))
    wave = fbm(8, 3, 3, 31)
    h = 0.05 * seam + 0.006 * welt + (wave - 0.5) * 0.012 * (1 - seam) + (fbm(80, 80, 2, 32) - 0.5) * 0.002
    h = wblur(h, 1.0)
    patina = fbm(10, 10, 5, 33)
    streak = fbm(36, 2, 4, 34)
    bare = wblur(smoothstep(0.8, 0.92, streak * 0.7 + (1 - patina) * 0.5), 2.5) * (1 - 0.7 * seam)
    pale = np.array([0.1, 0.24, 0.18], np.float32)
    teal = np.array([0.03, 0.1, 0.08], np.float32)
    bronze = np.array([0.075, 0.045, 0.028], np.float32)        # dark weathered bronze-brown, never red
    pv = patina[..., None]
    col = teal * (1 - pv) + pale * pv
    col = col * (1 + 0.25 * seam[..., None]) * (0.75 + 0.5 * fbm(60, 60, 3, 35)[..., None]) * (0.8 + 0.4 * streak[..., None])
    col = col * (1 - bare[..., None]) + bronze * (0.7 + 0.6 * streak[..., None]) * bare[..., None]
    col = col * (1 - 0.25 * welt[..., None])
    metal = 0.85 * bare
    rough = 0.78 * (1 - bare) + 0.42 * bare
    save(name, col, h, tile, np.clip(rough, 0, 1), np.clip(metal, 0, 1))


def lead_set(name, tile=6.0):
    us, vs = U * tile, V * tile
    bay = 2.0
    p = us / bay - np.floor(us / bay)
    d = np.minimum(p, 1 - p) * bay
    roll = np.sqrt(np.clip(1 - (d / 0.075) ** 2, 0, 1))
    bi = np.floor(us / bay).astype(int)
    dv = (vs + (bi % 2) * 1.5) % 3.0
    drip = smoothstep(0.0, 0.05, dv) * 0.02           # each sheet laps over the one below: a small step at the drip
    sag = fbm(6, 4, 3, 41)
    h = 0.06 * roll + drip + (sag - 0.5) * 0.01 * (1 - roll) + (fbm(90, 90, 2, 42) - 0.5) * 0.002
    h = wblur(h, 1.0)
    grey = np.array([0.08, 0.085, 0.092], np.float32)
    bloom = wblur(smoothstep(0.6, 0.8, fbm(12, 12, 5, 43)), 3.0) * 0.6 + 0.35 * roll * smoothstep(0.5, 0.7, fbm(30, 30, 3, 44))
    bloom = np.clip(bloom, 0, 1)
    streak = fbm(40, 2, 4, 45)
    col = grey * (0.8 + 0.4 * fbm(50, 50, 3, 46)[..., None]) * (0.75 + 0.5 * streak[..., None])
    col = col * (1 - bloom[..., None] * 0.6) + np.array([0.2, 0.205, 0.195], np.float32) * bloom[..., None] * 0.6
    col = col * (1 - 0.35 * smoothstep(0.05, 0.0, dv)[..., None])
    metal = 0.35 * (1 - bloom)
    rough = 0.58 + 0.3 * bloom + 0.06 * streak
    save(name, col, h, tile, np.clip(rough, 0, 1), np.clip(metal, 0, 1))


SETS = {
    "NH_RoofSlate": lambda: slate_set("NH_RoofSlate"),
    "NH_RoofMoss": lambda: slate_set("NH_RoofMoss", mossy=True),
    "NH_RoofScale": lambda: scale_set("NH_RoofScale"),
    "NH_RoofCrimson": lambda: scale_set("NH_RoofCrimson", crimson=True),
    "NH_RoofCopper": lambda: copper_set("NH_RoofCopper"),
    "NH_RoofLead": lambda: lead_set("NH_RoofLead"),
}
# studs per tile, for the props' UVs (art/props/nh_props_batch28.py reads the same numbers)
TILE = {"NH_RoofSlate": 6.0, "NH_RoofMoss": 6.0, "NH_RoofScale": 4.0, "NH_RoofCrimson": 4.0, "NH_RoofCopper": 6.0, "NH_RoofLead": 6.0}

if __name__ == "__main__":
    for n, f in SETS.items():
        if ONLY and n not in ONLY:
            continue
        f()
