"""Seamless 2048 sets for Wickfield, the tutorial's hometown (docs/expansion/15-Tutorial-The-Last-Normal-Night.md), made like
the roof kit's sets (tools/vfx/make_roof_tiles.py, whose noise and save helpers this uses). Big surfaces (house walls,
roofs, the street) carry world-scaled UVs and these sets, so they stay sharp at any size.

usage: python tools/vfx/make_hometown_tiles.py [outdir=art/props/textures] [size=2048] [Set,Set]

  WF_ClapCream, WF_ClapSage, WF_ClapButter, WF_ClapBlue
                painted lap siding, 8 studs a tile: 16 boards of 0.5, each lapped over the one below (a shadow line
                under every butt), board-end joints staggered, faint wood grain through the paint, nail heads, a few
                flakes of paint gone to grey wood, a little grime
  WF_Shingle    three-tab asphalt shingles, 6 studs a tile: 12 courses of 0.5, strips 3 studs long with two tab slots,
                granules, weathered charcoal-brown, strips of slightly different tone
  WF_Brick      running-bond red brick, 6 studs a tile: 22 courses, 8 bricks a course, recessed mortar, tone and soot
  WF_Sidewalk   concrete slabs, 8 studs a tile (2 x 2 slabs of 4), tooled joints, broom finish, hairline cracks,
                damp patches, a scatter of orange leaves
  WF_Road       wet asphalt, 12 studs a tile: aggregate, tar-patched cracks, damp sheen in the low spots

u runs along the wall or the eaves, v up (siding and shingle courses lie along u). Everything tiles both ways.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_roof_tiles as R  # noqa: E402  (reads outdir/size from argv the same way)

N, U, V = R.N, R.U, R.V
fbm, wblur, smoothstep, save = R.fbm, R.wblur, R.smoothstep, R.save
ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 else None


def lin(rgb):
    """sRGB 0-255 to linear"""
    c = np.array(rgb, np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


# ------------------------------------------------------------------ painted clapboard siding

def clapboard(name, paint, seed):
    tile, courses = 8.0, 16
    e = tile / courses
    rnd = np.random.default_rng(seed)
    vs, us = V * tile, U * tile
    k = np.floor(vs / e).astype(int) % courses
    dv = vs - np.floor(vs / e) * e                       # studs above this board's butt (bottom edge)
    # board-end joints: two per course at random u, staggered
    joints = rnd.uniform(0, tile, (courses, 2)).astype(np.float32)
    dj = np.minimum(np.abs(((us - joints[k, 0] + tile / 2) % tile) - tile / 2), np.abs(((us - joints[k, 1] + tile / 2) % tile) - tile / 2))
    seg = (us > joints[k, 0]).astype(int) + (us > joints[k, 1]).astype(int)
    tone = rnd.uniform(0.94, 1.06, (courses, 3)).astype(np.float32)
    t = tone[k, seg % 3]
    grain = fbm(6, 160, 4, seed + 1, gain=0.55)          # long grain along the boards
    fine = fbm(220, 220, 3, seed + 2)
    # height: each board tapers from its thick butt (0.05) up to thin under the next board; joints and the lap groove
    h = 0.05 * (1 - np.clip(dv / e, 0, 1)) + (grain - 0.5) * 0.004 + (fine - 0.5) * 0.0015
    h = np.where(dj < 0.012, h - 0.006, h)
    h = R.wblur(h, 0.9)
    base = lin(paint) * t[..., None]
    col = base * (0.94 + 0.08 * grain[..., None]) * (0.97 + 0.06 * fine[..., None])
    # the lap shadow: dark right under each butt, the butt edge itself catching light
    shadow = smoothstep(e - 0.07, e - 0.004, dv)          # the next board's butt overhangs the top of this one
    col = col * (1 - 0.6 * shadow[..., None])
    lit = smoothstep(0.03, 0.0, dv)
    col = col * (1 + 0.18 * lit[..., None])
    col = np.where((dj < 0.01)[..., None], col * 0.55, col)
    # peeling: small flakes of paint gone, grey weathered wood under them, a raised paint edge round each
    flake_n = fbm(30, 30, 4, seed + 3)
    flake = smoothstep(0.835, 0.85, flake_n) * smoothstep(0.02, 0.08, dv)
    wood = lin((128, 118, 104)) * (0.8 + 0.4 * grain[..., None])
    col = col * (1 - flake[..., None]) + wood * flake[..., None]
    h = h - flake * 0.003
    # nail heads near the bottom of every board, every 1.33 studs (on studs), a touch of rust
    nu = (us + (k % 2) * 0.66) % 1.333
    nail = ((nu - 0.66) ** 2 + (dv - 0.07) ** 2) < 0.012 ** 2
    col = np.where(nail[..., None], col * 0.6 + lin((92, 60, 40)) * 0.4, col)
    h = np.where(nail, h + 0.002, h)
    # grime: a soft wash darker in the lap shadows and in patches; a few drip streaks
    grime = smoothstep(0.55, 0.85, fbm(5, 5, 4, seed + 4))
    drip = smoothstep(0.7, 0.9, fbm(60, 3, 3, seed + 5))
    col = col * (1 - 0.12 * grime[..., None] - 0.08 * drip[..., None])
    rough = 0.62 + (fine - 0.5) * 0.12 + 0.2 * flake + 0.1 * shadow
    save(name, col, h, tile, np.clip(rough, 0, 1), np.zeros((N, N), np.float32), boost=1.4)


# ------------------------------------------------------------------ three-tab asphalt shingles

def shingle(name="WF_Shingle", seed=5101):
    tile, courses, per = 6.0, 12, 2
    e, w = tile / courses, tile / per
    rnd = np.random.default_rng(seed)
    vs, us = V * tile, U * tile
    k = np.floor(vs / e).astype(int) % courses
    dv = vs - np.floor(vs / e) * e
    uu = us + (k % 2) * (w / 6) + (k % 3) * (w / 3)       # strips offset course to course
    j = np.floor(uu / w).astype(int) % per
    fu = (uu / w) % 1.0
    tone = rnd.uniform(0.82, 1.18, (courses, per)).astype(np.float32)
    hue = rnd.integers(0, 3, (courses, per))
    pal = np.array([lin((52, 48, 46)), lin((60, 52, 44)), lin((46, 46, 50))], np.float32)
    base = pal[hue[k, j]] * tone[k, j][..., None]
    gran = fbm(400, 400, 2, seed + 1)
    blot = fbm(12, 12, 4, seed + 2)
    # tab slots: two narrow cut-outs per strip in the exposed lower half, and the strip ends
    slot = ((((fu * 3) % 1.0) < 0.018) | (((fu * 3) % 1.0) > 0.982)) & (dv < e * 0.6)
    end = (fu < 0.004) | (fu > 0.996)
    h = 0.03 * (1 - np.clip(dv / e, 0, 1)) + (gran - 0.5) * 0.003
    h = np.where(slot | end, -0.01, h)
    h = R.wblur(h, 0.8)
    col = base * (0.75 + 0.5 * gran[..., None]) * (0.9 + 0.2 * blot[..., None])
    shadow = smoothstep(e - 0.05, e - 0.004, dv)
    col = col * (1 - 0.6 * shadow[..., None])
    col = np.where((slot | end)[..., None], col * 0.35, col)
    algae = smoothstep(0.62, 0.8, fbm(8, 30, 3, seed + 3))     # faint streaks of roof algae
    col = col * (1 - 0.18 * algae[..., None])
    leaf = smoothstep(0.93, 0.95, fbm(24, 24, 3, seed + 4))   # a few stuck leaves
    col = col * (1 - leaf[..., None]) + lin((176, 92, 32)) * leaf[..., None]
    rough = np.clip(0.86 + (gran - 0.5) * 0.1 - 0.15 * leaf, 0, 1)
    save(name, col, h, tile, rough, np.zeros((N, N), np.float32), boost=1.5)


# ------------------------------------------------------------------ red brick

def brick(name="WF_Brick", seed=5201):
    tile, courses, per = 6.0, 22, 8
    e, w = tile / courses, tile / per
    rnd = np.random.default_rng(seed)
    vs, us = V * tile, U * tile
    k = np.floor(vs / e).astype(int) % courses
    dv = vs - np.floor(vs / e) * e
    uu = us + (k % 2) * w / 2
    j = np.floor(uu / w).astype(int) % per
    fu = (uu / w) % 1.0
    m = 0.028
    mortar = (dv < m) | (fu * w < m * 0.6) | ((1 - fu) * w < m * 0.6)
    tone = rnd.uniform(0.8, 1.2, (courses, per)).astype(np.float32)
    hue = rnd.integers(0, 4, (courses, per))
    pal = np.array([lin((150, 62, 44)), lin((130, 52, 40)), lin((166, 78, 52)), lin((112, 48, 40))], np.float32)
    base = pal[hue[k, j]] * tone[k, j][..., None]
    pits = fbm(160, 160, 3, seed + 1)
    face = fbm(20, 20, 3, seed + 2)
    col = base * (0.82 + 0.36 * pits[..., None]) * (0.9 + 0.2 * face[..., None])
    burnt = smoothstep(0.75, 0.9, fbm(30, 30, 2, seed + 3))
    col = col * (1 - 0.35 * burnt[..., None])
    mort = lin((176, 168, 152)) * (0.75 + 0.3 * pits[..., None])
    col = np.where(mortar[..., None], mort, col)
    soot = smoothstep(0.5, 0.8, fbm(4, 4, 4, seed + 4))
    col = col * (1 - 0.25 * soot[..., None])
    edge = np.minimum(np.minimum(dv - m, e - dv), np.minimum(fu * w, (1 - fu) * w))
    h = np.where(mortar, -0.015, 0.0 + 0.004 * smoothstep(0.0, 0.02, edge) + (pits - 0.5) * 0.004)
    h = R.wblur(h, 1.0)
    rough = np.where(mortar, 0.95, 0.78 + (pits - 0.5) * 0.15)
    save(name, col, h, tile, np.clip(rough, 0, 1), np.zeros((N, N), np.float32), boost=1.4)


# ------------------------------------------------------------------ concrete sidewalk

def sidewalk(name="WF_Sidewalk", seed=5301):
    tile, slab = 8.0, 4.0
    vs, us = V * tile, U * tile
    fx, fy = (us % slab), (vs % slab)
    jd = np.minimum(np.minimum(fx, slab - fx), np.minimum(fy, slab - fy))
    joint = jd < 0.035
    broom = fbm(4, 600, 2, seed + 1)                    # broom finish across the slab
    fine = fbm(300, 300, 3, seed + 2)
    blot = fbm(6, 6, 4, seed + 3)
    tone = np.random.default_rng(seed).uniform(0.92, 1.08, (2, 2)).astype(np.float32)
    ti = tone[(np.floor(vs / slab).astype(int) % 2), (np.floor(us / slab).astype(int) % 2)]
    base = lin((170, 166, 158)) * ti[..., None]
    col = base * (0.88 + 0.12 * broom[..., None]) * (0.85 + 0.3 * fine[..., None]) * (0.85 + 0.25 * blot[..., None])
    damp = smoothstep(0.6, 0.8, fbm(5, 5, 4, seed + 4))
    col = col * (1 - 0.25 * damp[..., None])
    # hairline cracks: ridges of a noise field
    cr = np.abs(fbm(5, 5, 3, seed + 5) - 0.5)
    crack = (cr < 0.0035) & (smoothstep(0.6, 0.72, fbm(3, 3, 2, seed + 6)) > 0.5)
    col = np.where(crack[..., None], col * 0.4, col)
    col = np.where(joint[..., None], col * 0.45, col)
    # leaves: orange and brown, a few
    lf = fbm(26, 26, 3, seed + 7)
    leaf = smoothstep(0.86, 0.875, lf)
    lcol = np.where((fbm(70, 70, 1, seed + 8) > 0.5)[..., None], lin((196, 104, 34)), lin((138, 70, 30)))
    col = col * (1 - leaf[..., None]) + lcol * leaf[..., None]
    h = np.where(joint, -0.02, (fine - 0.5) * 0.003 + (broom - 0.5) * 0.002) - crack * 0.004 + leaf * 0.004
    h = R.wblur(h, 1.0)
    rough = np.clip(0.88 - 0.35 * damp + (fine - 0.5) * 0.1 - 0.1 * leaf, 0, 1)
    save(name, col, h, tile, rough, np.zeros((N, N), np.float32), boost=1.3)


# ------------------------------------------------------------------ wet asphalt

def road(name="WF_Road", seed=5401):
    tile = 12.0
    agg = fbm(500, 500, 2, seed + 1)
    fine = fbm(120, 120, 3, seed + 2)
    blot = fbm(4, 4, 5, seed + 3)
    col = lin((44, 44, 48)) * (0.7 + 0.6 * agg[..., None]) * (0.85 + 0.3 * fine[..., None]) * (0.8 + 0.35 * blot[..., None])
    stone = smoothstep(0.8, 0.86, agg)
    col = col * (1 - 0.5 * stone[..., None]) + lin((120, 116, 110)) * 0.5 * stone[..., None]
    cr = np.abs(fbm(4, 4, 3, seed + 4) - 0.5)
    tar = (cr < 0.004) & (smoothstep(0.55, 0.7, fbm(2, 2, 2, seed + 5)) > 0.5)
    tar = R.wblur(tar.astype(np.float32), 0.8) > 0.35
    col = np.where(tar[..., None], lin((20, 20, 22)), col)
    wet = smoothstep(0.45, 0.7, blot)
    col = col * (1 - 0.3 * wet[..., None])
    h = (agg - 0.5) * 0.006 + (fine - 0.5) * 0.004 - wet * 0.004 + tar * 0.002
    h = R.wblur(h, 0.8)
    rough = np.clip(0.8 - 0.62 * wet + (agg - 0.5) * 0.1 - 0.3 * tar, 0.05, 1)
    save(name, col, h, tile, rough, np.zeros((N, N), np.float32), boost=1.2)


# ------------------------------------------------------------------ interiors

def wallpaper(name="WF_Wallpaper", seed=5501, base_rgb=(104, 128, 150), cream_rgb=(228, 216, 190), floral=False):
    """dusty blue (or rose), cream pinstripes in pairs, a tiny cream crescent-and-star sprig between them (the rose
    variant adds a five-petal flower under each moon); 4 studs a tile"""
    tile = 4.0
    us, vs = U * tile, V * tile
    paper = fbm(200, 200, 2, seed + 1)
    blot = fbm(6, 6, 3, seed + 2)
    base = lin(base_rgb) * (0.94 + 0.08 * paper[..., None]) * (0.95 + 0.08 * blot[..., None])
    sp = 0.5                                     # stripe pairs every half stud
    f = us % sp
    stripe = (np.abs(f - 0.04) < 0.012) | (np.abs(f - 0.08) < 0.006)
    cream = lin(cream_rgb)
    col = np.where(stripe[..., None], cream * (0.95 + 0.05 * paper[..., None]), base)
    # sprigs: a crescent and a little star in every cell between the stripe pairs (alternate columns offset half a stud)
    col_i = np.floor(us / sp).astype(int)
    lx = us % sp
    ly = (vs + 0.5 * (col_i % 2)) % 1.0
    dx, dy = lx - 0.29, ly - 0.5
    moon = ((dx ** 2 + dy ** 2) < 0.06 ** 2) & (((dx - 0.025) ** 2 + (dy - 0.015) ** 2) > 0.05 ** 2)
    sx, sy = dx - 0.075, dy - 0.075
    r = np.hypot(sx, sy)
    a = np.arctan2(sy, sx)
    star = r < 0.034 * (0.4 + 0.6 * np.abs(np.cos(2.5 * a)) ** 3)
    sprig = moon | star
    if floral:
        fx, fy = dx + 0.02, dy + 0.2
        fr = np.hypot(fx, fy)
        fa = np.arctan2(fy, fx)
        petals = fr < 0.045 * (0.55 + 0.45 * np.abs(np.cos(2.5 * fa)))
        centre = fr < 0.012
        stem = (np.abs(fx + 0.0) < 0.004) & (fy > 0.04) & (fy < 0.12)
        sprig = sprig | (petals & ~centre) | stem
        col = np.where(centre[..., None], lin((214, 168, 96)), col)
    col = np.where(sprig[..., None], cream * 0.95, col)
    # age: faint yellowing near the top and bottom of the tile is unwanted (tiles); keep it even, a few scuffs
    scuff = smoothstep(0.82, 0.9, fbm(20, 20, 3, seed + 3))
    col = col * (1 - 0.08 * scuff[..., None])
    h = (paper - 0.5) * 0.001 + stripe * 0.0006 + sprig * 0.0008
    rough = np.clip(0.85 - 0.1 * stripe, 0, 1)
    save(name, col, h, tile, rough, np.zeros((N, N), np.float32), boost=1.0)


def floor_oak(name="WF_FloorOak", seed=5601):
    """honey oak boards, 0.6 wide, random lengths, satin finish worn in places; 6 studs a tile"""
    tile, rows = 6.0, 10
    w = tile / rows
    rnd = np.random.default_rng(seed)
    us, vs = U * tile, V * tile
    k = np.floor(vs / w).astype(int) % rows
    dv = vs - np.floor(vs / w) * w
    cuts = np.sort(rnd.uniform(0, tile, (rows, 2)), 1).astype(np.float32)
    seg = (us > cuts[k, 0]).astype(int) + (us > cuts[k, 1]).astype(int)
    dj = np.minimum(np.abs(((us - cuts[k, 0] + tile / 2) % tile) - tile / 2), np.abs(((us - cuts[k, 1] + tile / 2) % tile) - tile / 2))
    tone = rnd.uniform(0.85, 1.15, (rows, 3)).astype(np.float32)
    t = tone[k, seg % 3]
    grain = fbm(3, 120, 5, seed + 1, gain=0.6)
    rays = fbm(40, 300, 2, seed + 2)
    base = lin((178, 124, 70)) * t[..., None]
    col = base * (0.78 + 0.4 * grain[..., None]) * (0.95 + 0.1 * rays[..., None])
    seam = (dv < 0.012) | (dv > w - 0.012) | (dj < 0.01)
    col = np.where(seam[..., None], col * 0.35, col)
    wear = smoothstep(0.55, 0.8, fbm(4, 4, 4, seed + 3))
    col = col * (1 + 0.1 * wear[..., None])
    h = (grain - 0.5) * 0.002 - seam * 0.006
    rough = np.clip(0.38 + 0.25 * wear + (grain - 0.5) * 0.1 + 0.4 * seam, 0, 1)
    save(name, col, h, tile, rough, np.zeros((N, N), np.float32), boost=1.0)


SETS = {
    "WF_Wallpaper": wallpaper,
    "WF_WallpaperRose": lambda: wallpaper("WF_WallpaperRose", 5502, base_rgb=(190, 142, 150), cream_rgb=(244, 230, 214), floral=True),
    "WF_FloorOak": floor_oak,
    "WF_ClapCream": lambda: clapboard("WF_ClapCream", (232, 220, 196), 5001),
    "WF_ClapSage": lambda: clapboard("WF_ClapSage", (150, 168, 140), 5002),
    "WF_ClapButter": lambda: clapboard("WF_ClapButter", (228, 202, 130), 5003),
    "WF_ClapBlue": lambda: clapboard("WF_ClapBlue", (122, 146, 170), 5004),
    "WF_Shingle": shingle,
    "WF_Brick": brick,
    "WF_Sidewalk": sidewalk,
    "WF_Road": road,
}

if __name__ == "__main__":
    for n, f in SETS.items():
        if ONLY is None or n in ONLY:
            f()
