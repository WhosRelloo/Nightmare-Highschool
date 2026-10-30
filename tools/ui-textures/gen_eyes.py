"""
Nightmare High painted eyes v2 - original art for classic Roblox heads. 8 distinct eye shapes.

Per style, two 1024x1024 RGBA decals (Decal.ZIndex 1 then 2 on the head's Front face):
  eyes_<id>_iris.png  greyscale iris, clipped to the eye opening (tinted in game by Decal.Color3)
  eyes_<id>_main.png  sclera with an iris hole, lid shadow, tear duct, limbal ring, pupil,
                      highlights, lash band + lash clusters, crease, lower line, brow
Rendered 4x supersampled, box-filtered down. Usage: python gen_eyes2.py <outdir>
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "eyes2"
ONLY = sys.argv[2].split(",") if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)
S, N = 4, 1024
CX0, CY0, CW, CH = 64, 320, 896, 440          # eye band in final px
SH = (CH * S, CW * S)
YY, XX = (np.mgrid[0:SH[0], 0:SH[1]].astype(np.float32) + 0.5) / S
XX += CX0
YY += CY0

INK = np.array([0.07, 0.05, 0.08], np.float32)
BROW_GAP = 12  # px between the brow's lower edge and the highest lash / wing / crease
CHECK_PAIRS = [("brow", "eye"), ("brow", "low"), ("brow", "bags"), ("fur", "eye"), ("corner", "eye"),
               ("corner", "low"), ("bags", "low"), ("bags", "eye"), ("veins", "low"), ("veins", "bags"),
               ("veins", "eye"), ("veins", "corner")]
SHADE = np.array([0.20, 0.14, 0.26], np.float32)

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def lid(I, O, h, peak=0.5, flat=1.0, n=200):
    """lid curve inner->outer; h>0 bulges up, h<0 down; peak = where the bulge tops out"""
    t = np.linspace(0, 1, n)
    a = math.log(0.5) / math.log(peak)
    bump = np.sin(np.pi * t ** a) ** flat
    x = I[0] + (O[0] - I[0]) * t
    y = I[1] + (O[1] - I[1]) * t - h * bump
    return np.stack([x, y], 1)

def mirror(p):
    p = np.array(p, float).copy()
    p[:, 0] = N - p[:, 0]
    return p

def normals(p):
    d = np.gradient(p, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    return np.stack([-d[:, 1], d[:, 0]], 1), d

def stroke(p, width, prof):
    p = np.asarray(p, float)
    t = np.linspace(0, 1, len(p))
    w = width * prof(t)
    nr, _ = normals(p)
    return np.vstack([p + nr * w[:, None] / 2, (p - nr * w[:, None] / 2)[::-1]])

def taper(t):
    return np.sin(np.pi * np.clip(t, 0, 1)) ** 0.6

def mask(polys):
    im = Image.new("L", (SH[1], SH[0]), 0)
    dr = ImageDraw.Draw(im)
    for p in polys:
        dr.polygon([((float(x) - CX0) * S, (float(y) - CY0) * S) for x, y in p], fill=255)
    return np.asarray(im, np.float32) / 255.0

def blur(a, sigma):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma * S)), np.float32) / 255.0

def shift(a, dy):
    k = int(round(dy * S))
    out = np.zeros_like(a)
    if k > 0:
        out[k:] = a[:-k]
    else:
        out[:] = a
    return out

def ell(cx, cy, rx, ry, rot=0.0, soft=0.7):
    c, s = math.cos(rot), math.sin(rot)
    dx, dy = XX - cx, YY - cy
    u = (dx * c + dy * s) / rx
    v = (-dx * s + dy * c) / ry
    r = np.sqrt(u * u + v * v)
    return np.clip((1 - r) * min(rx, ry) / soft + 0.5, 0, 1)

def down(a):
    if a.ndim == 2:
        return a.reshape(CH, S, CW, S).mean((1, 3))
    return a.reshape(CH, S, CW, S, a.shape[2]).mean((1, 3))

# ------------------------------------------------------------------ styles (left eye, final px)
D = dict
STYLES = {
    "sharp": D(I=(464, 540), O=(186, 506), up=(70, .45, .9), lo=(44, .55, 1.1), r=78, idy=-4,
               lash=(4, 17), wing=(30, 12), spikes=[(.72, 16), (.86, 22), (.98, 26)], lower_from=.25,
               brow=(70, 76, 10)),
    "hooded": D(I=(464, 534), O=(184, 528), up=(48, .5, .55), lo=(46, .5, 1.0), r=80, idy=-8,
                lash=(6, 18), wing=(18, 0), spikes=[(.9, 12)], lower_from=.3, crease=16,
                brow=(50, 54, 4)),
    "fierce": D(I=(468, 548), O=(176, 486), up=(38, .5, .8), lo=(30, .5, .9), r=72, idy=0,
                lash=(6, 20), wing=(40, 18), spikes=[(.8, 14), (.95, 18)], lower_from=.2,
                brow=(34, 74, 2)),
    "doe": D(I=(460, 528), O=(196, 516), up=(100, .5, .9), lo=(72, .5, 1.0), r=92, idy=0,
             lash=(4, 14), wing=(14, 6), spikes=[(.55, 12), (.7, 16), (.84, 20), (.96, 22)], lower_from=.35,
             lowlash=[.55, .7, .85], brow=(112, 104, 10)),
    "sleepless": D(I=(462, 530), O=(186, 540), up=(54, .45, .7), lo=(42, .5, 1.0), r=62, idy=2,
                   lash=(4, 13), wing=(12, -4), spikes=[], lower_from=.15, crease=14,
                   bags=[(14, .8), (26, .62)], brow=(60, 60, 6)),
    "cat": D(I=(466, 556), O=(174, 474), up=(64, .35, .8), lo=(34, .6, 1.1), r=76, idy=0, slit=True,
             lash=(5, 19), wing=(46, 26), spikes=[(.85, 18), (.97, 24)], lower_from=.3,
             brow=(70, 80, 8)),
    "gentle": D(I=(460, 512), O=(188, 548), up=(74, .4, 1.0), lo=(40, .5, 1.0), r=82, idy=0,
                lash=(4, 13), wing=(10, -10), spikes=[(.7, 12), (.85, 15)], lower_from=.3, crease=18,
                brow=(104, 66, 8)),
    "calm": D(I=(462, 526), O=(182, 506), up=(44, .5, .45), lo=(32, .5, .9), r=74, idy=-2,
              lash=(7, 15), wing=(20, 6), spikes=[], lower_from=.3, brow=(58, 62, 2)),
}
LABELS = dict(sharp="Sharp", hooded="Hooded", fierce="Fierce", doe="Doe", sleepless="Sleepless",
              cat="Cat", gentle="Gentle", calm="Calm")

def eye_geometry(st, side):
    I, O = st["I"], st["O"]
    U = lid(I, O, *st["up"])
    L = lid(I, O, -st["lo"][0], st["lo"][1], st["lo"][2])
    if side:
        U, L = mirror(U), mirror(L)
    return U, L

def col_interp(curve, xs):
    o = np.argsort(curve[:, 0])
    return np.interp(xs, curve[o, 0], curve[o, 1], left=np.nan, right=np.nan)

FORMS = ["base", "vampire", "wolf", "ghoul", "wraith", "vampire2", "ghoul2"]  # *2 = second stage: jet-black sclera

def variant(st, female, form="base"):
    """female: full lash fan, bigger wing, lower lashes, finer arched brow.
    form (transformation): vampire - thin slit pupil, glowing iris, red bloom, veins, under-eye shadow
                           wolf    - huge amber iris, small pupil, yellowed sclera, scowl brow, fur tufts
                           ghoul   - milky iris, pinprick pupil, bloodshot, sunken socket, skin veins
                           wraith  - blank glowing eyes, no pupil, pale halo"""
    st = dict(st)
    if female:
        w_in, w_out = st["lash"]
        st["lash"] = (w_in + 1.5, w_out + 4)
        wl, lift = st["wing"]
        st["wing"] = (max(wl, 10) + 16, lift + 7)
        st["spikes"] = [(.46, 12), (.58, 16), (.69, 20), (.8, 24), (.9, 27), (.99, 30)]
        st["lowlash"] = sorted(set(list(st.get("lowlash", [])) + [.62, .76, .9]))
        gi, go, arch = st["brow"]
        st["brow"] = (gi + 4, go + 4, arch + 8)
        st["brow_w"] = 9
        st["r"] = st["r"] * 1.04
    if form.endswith("2"):
        st["black"] = True   # second transformation stage
        form = form[:-1]
    st["form"] = form
    if form == "vampire":
        wl, lift = st["wing"]
        st["wing"] = (wl + 8, lift + 4)
    elif form == "wolf":
        st["r"] = st["r"] * 1.24
        gi, go, arch = st["brow"]
        st["brow"] = (max(gi - 10, 34), go + 12, -4)   # low, scowling
        st["brow_w"] = 18
        w_in, w_out = st["lash"]
        st["lash"] = (w_in + 2, w_out + 3)
    elif form == "ghoul":
        st["r"] = st["r"] * 0.96
    elif form == "wraith":
        st["r"] = st["r"] * 1.08
    return st

def walk(rng, p, heading, length, steps=6, wiggle=0.55):
    pts = [np.array(p, float)]
    h = heading
    for _ in range(steps):
        h += rng.uniform(-wiggle, wiggle)
        pts.append(pts[-1] + np.array([math.cos(h), math.sin(h)]) * length / steps)
    pts = np.array(pts)
    # smooth with a fine resample
    t = np.linspace(0, 1, len(pts))
    tt = np.linspace(0, 1, 40)
    return np.stack([np.interp(tt, t, pts[:, 0]), np.interp(tt, t, pts[:, 1])], 1)

def vein_tree(rng, start, heading, length, width, depth=2, wiggle=0.2):
    """A long, smoothly snaking vein that tapers to a hair-thin tip, with a few forks."""
    trunk = walk(rng, start, heading, length, 12, wiggle)
    polys = [stroke(trunk, width, lambda q: (np.clip(1 - q, 0, 1) ** 0.9) * np.clip(q * 10, 0, 1) ** 0.35 + 0.06 * (q < 0.98))]
    if depth > 0:
        for _ in range(rng.integers(1, 3) if depth > 1 else rng.integers(0, 2)):
            at = rng.uniform(0.3, 0.65)
            k = int(at * (len(trunk) - 1))
            d = trunk[min(k + 2, len(trunk) - 1)] - trunk[k]
            h = math.atan2(d[1], d[0]) + rng.choice([-1, 1]) * rng.uniform(0.35, 0.75)
            polys += vein_tree(rng, trunk[k], h, length * (1 - at) * rng.uniform(0.6, 0.85),
                               width * (1 - at * 0.7) * 0.62, depth - 1, wiggle + 0.05)
    return polys

def render(sid, st, seed):
    rng = np.random.default_rng(seed)
    form = st.get("form", "base")
    scl_veins = []      # red veins inside the eye white
    skin_veins = []     # dark veins on the skin (ghoul / vampire) - filled from accepted vein_trees
    vein_trees = []     # candidate trees: (side, corner?, polys, wanted per side)
    fur_polys = []      # wolf tufts
    tops = []           # per-column top of the lash work, per side (for brow fitting)
    G = {k: [] for k in ("eye", "low", "bags", "brow", "fur", "corner", "veins")}  # feature groups (overlap checks)
    def add(group, poly):
        G[group].append(poly)
        (fur_polys if group in ("fur", "corner") else ink_polys).append(poly)
    main_rgb = np.zeros(SH + (3,), np.float32)
    main_a = np.zeros(SH, np.float32)

    def over(rgb, a):
        nonlocal main_rgb, main_a
        a = np.clip(a, 0, 1)
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), SH + (3,))
        oa = a + main_a * (1 - a)
        main_rgb = (rgb * a[..., None] + main_rgb * (main_a * (1 - a))[..., None]) / np.maximum(oa[..., None], 1e-6)
        main_a = oa

    vein_g = np.zeros(SH, np.float32)   # separate greyscale vein layer (game tints it from the skin colour)
    vein_a = np.zeros(SH, np.float32)

    def vover(grey, a):
        nonlocal vein_g, vein_a
        a = np.clip(a, 0, 1)
        oa = a + vein_a * (1 - a)
        vein_g = (grey * a + vein_g * vein_a * (1 - a)) / np.maximum(oa, 1e-6)
        vein_a = oa

    iris_rgb = np.zeros(SH, np.float32)
    iris_a = np.zeros(SH, np.float32)
    ink_polys = []
    shadow_polys = []
    sclera_layers = []

    for side in (0, 1):
        U, L = eye_geometry(st, side)
        opening = mask([np.vstack([U, L[::-1]])])
        I = np.array(st["I"], float)
        O = np.array(st["O"], float)
        if side:
            I[0], O[0] = N - I[0], N - O[0]

        # ---- per-pixel eye coordinates
        xs = XX[0]
        up = col_interp(U, xs)
        lo = col_interp(L, xs)
        up = np.nan_to_num(up, nan=0.0)[None, :]
        lo = np.nan_to_num(lo, nan=1.0)[None, :]
        v = np.clip((YY - up) / np.maximum(lo - up, 1e-3), 0, 1)           # 0 at upper lid, 1 at lower
        u = np.clip((XX - I[0]) / (O[0] - I[0]), 0, 1)                      # 0 inner, 1 outer

        # ---- sclera
        tone = 0.95 - 0.34 * np.exp(-v * 4.2) - 0.16 * np.abs(u - 0.5) ** 2.6 * 8 * 0.18 - 0.05 * v ** 4
        scl = np.stack([tone * 0.95, tone * 0.94, tone * 0.99], -1)
        # tear duct (caruncle) at the inner corner
        inward = 1 if side == 0 else -1
        car = ell(I[0] - inward * 13, I[1] + 3, 13, 8) * opening
        scl = scl * (1 - car[..., None] * 0.85) + np.array([0.86, 0.6, 0.62], np.float32) * car[..., None] * 0.85
        if form == "vampire":
            scl = scl * np.array([0.9, 0.84, 0.88], np.float32)
        elif form == "wolf":
            scl = scl * np.array([0.95, 0.86, 0.62], np.float32)
        elif form == "ghoul":
            scl = scl * np.array([0.9, 0.76, 0.76], np.float32)
        elif form == "wraith":
            scl = np.clip(scl * np.array([0.92, 1.0, 1.08], np.float32) + 0.06, 0, 1)
        if st.get("black"):
            # jet-black sclera with a faint wet sheen under the lid; the tear duct goes dark crimson
            sheen = 0.035 + 0.05 * np.exp(-v * 3.0) * (1 - np.abs(u - 0.5) * 1.6).clip(0, 1)
            scl = np.stack([sheen * 1.0, sheen * 0.9, sheen * 1.1], -1).astype(np.float32)
            car_b = ell(I[0] - inward * 13, I[1] + 3, 13, 8) * opening
            scl = scl * (1 - car_b[..., None] * 0.8) + np.array([0.3, 0.05, 0.08], np.float32) * car_b[..., None] * 0.8
        if form in ("vampire", "ghoul") and not st.get("black"):
            # bloodshot: a reddish blush toward the corners and branching red veins reaching for the iris
            corner = np.clip(np.abs(u - 0.5) * 2, 0, 1) ** 1.6 * opening
            blush = np.array([0.98, 0.72, 0.72] if form == "ghoul" else [0.96, 0.78, 0.8], np.float32)
            scl = scl * (1 - corner[..., None] * (1 - blush))
            nv = 3 if form == "vampire" else 5
            for end, base_dir in ((I, 0.0 if side == 0 else math.pi), (O, math.pi if side == 0 else 0.0)):
                for _ in range(nv):
                    yv = end[1] + rng.uniform(-16, 16)
                    toward = base_dir + rng.uniform(-0.45, 0.45)
                    scl_veins += vein_tree(rng, (end[0], yv), toward, rng.uniform(55, 95), rng.uniform(2.8, 3.8), 2, 0.3)
        if form in ("ghoul", "vampire"):
            # veins creeping out of the eye onto the skin, mostly from the outer corner and below
            n_corner, n_below = (5, 6) if form == "ghoul" else (2, 3)
            want_c, want_b = n_corner, n_below
            n_corner, n_below = int(n_corner * 1.8 + 1), int(n_below * 1.8 + 1)   # extra candidates (some get rejected)
            for k in range(n_corner + n_below):
                if k < n_corner:
                    # spread the corner veins along the outer corner and the outer third of the lower lid
                    tt = rng.uniform(0.82, 1.0)
                    base_pt = L[int(tt * (len(L) - 1))] if tt < 0.97 else O
                    out_x = -1 if side == 0 else 1
                    start = base_pt + np.array([out_x * (6 + st["wing"][0] * 0.25 + (14 if st.get("lowlash") else 0)), rng.uniform(10, 20) + (6 if st.get("lowlash") else 0)])
                    dl = rng.uniform(0.15, 1.05)
                    hd = (math.pi - dl) if side == 0 else dl
                else:
                    tt = rng.uniform(0.35, 0.95)
                    clear = 7 + (22 if st.get("lowlash") else 0) + (max(g for g, _ in st["bags"]) + 8 if st.get("bags") else 0)
                    start = L[int(tt * (len(L) - 1))] + np.array([0, clear])
                    hd = math.pi / 2 + rng.uniform(-0.7, 0.7)
                ln_ = (rng.uniform(70, 105) if k < n_corner else rng.uniform(50, 82)) * (1 if form == "ghoul" else 0.75)
                tree = vein_tree(rng, start, hd, ln_, rng.uniform(5.5, 7.0) if form == "ghoul" else rng.uniform(4.0, 5.2), 2)
                vein_trees.append((side, k < n_corner, tree, want_c if k < n_corner else want_b))
        sclera_layers.append((scl, opening))

        # ---- iris placement
        ix = I[0] + (O[0] - I[0]) * 0.47
        uy = float(col_interp(U, np.array([ix]))[0])
        ly = float(col_interp(L, np.array([ix]))[0])
        iy = (uy + ly) / 2 + st["idy"]
        r = st["r"]
        dx, dy = (XX - ix) / r, (YY - iy) / r
        rr = np.sqrt(dx * dx + dy * dy)
        ang = np.arctan2(dy, dx)
        disc = np.clip((1 - rr) * r / 0.8 + 0.5, 0, 1)
        disc_big = np.clip((1 + 3.0 / r - rr) * r / 0.8 + 0.5, 0, 1)

        # iris tone (greyscale, tinted in game)
        fib = np.zeros_like(rr)
        for k, amp in ((23, .5), (37, .35), (53, .3), (71, .22), (97, .18), (131, .12)):
            ph = rng.uniform(0, 2 * np.pi)
            fib += amp * np.sin(k * ang + ph + 2.4 * rr * rng.uniform(-1, 1))
        fib = fib / 1.67
        t_iris = (0.66
                  + 0.30 * smooth(-0.2, 0.85, dy) * smooth(0.3, 0.6, rr)          # lower glow
                  - 0.20 * smooth(0.1, -0.9, dy)                                   # top darker
                  + 0.14 * np.exp(-((rr - 0.47) / 0.07) ** 2)                      # collarette
                  + 0.12 * fib * smooth(0.36, 0.56, rr) * (1 - smooth(0.85, 1.0, rr))
                  - 0.28 * smooth(0.76, 1.0, rr))
        if form == "vampire":
            t_iris = t_iris + 0.16 + 0.32 * np.exp(-((rr - 0.2) / 0.1) ** 2)
        elif form == "wolf":
            t_iris = t_iris + 0.12 + 0.2 * fib * smooth(0.2, 0.5, rr) + 0.25 * np.exp(-((rr - 0.3) / 0.14) ** 2)
        elif form == "ghoul":
            t_iris = 0.78 + 0.06 * fib + 0.12 * (1 - rr) - 0.12 * smooth(0.8, 1.0, rr)
        elif form == "wraith":
            t_iris = 0.82 + 0.18 * np.exp(-rr * 2.2)
        t_iris = np.clip(t_iris, 0, 1)
        a_i = disc_big * opening
        iris_rgb = np.where(a_i > iris_a, t_iris, iris_rgb)
        iris_a = np.maximum(iris_a, a_i)

        # ---- main layer pieces that sit over the iris
        st_side = dict(ix=ix, iy=iy, r=r, rr=rr, dx=dx, dy=dy, disc=disc, opening=opening, v=v)
        sclera_layers[-1] = (scl, opening, st_side)

        # ---- lines
        nU, dU = normals(U)
        if nU[:, 1].mean() > 0:
            nU = -nU
        t = np.linspace(0, 1, len(U))
        w_in, w_out = st["lash"]
        th = (w_in + (w_out - w_in) * t ** 1.3) * np.clip(t * 9, 0, 1) ** 0.6
        band = np.vstack([U - nU * 1.5, (U + nU * th[:, None])[::-1]])
        eye0 = len(G["eye"])
        add("eye", band)
        shadow_polys.append(band)
        # wing past the outer corner
        wl, lift = st["wing"]
        if wl > 0:
            tang = dU[-1] / np.linalg.norm(dU[-1])
            p0 = U[-1] + nU[-1] * th[-1] * 0.45
            p1 = p0 + tang * wl * 0.55 + np.array([0, -lift * 0.4])
            p2 = p0 + tang * wl + np.array([0, -lift])
            wing = np.array([p0 + (p1 - p0) * s + (p2 - p0) * s * s * 0.0 for s in np.linspace(0, 1, 2)])
            pts = np.array([p0 * (1 - s) ** 2 + 2 * p1 * s * (1 - s) + p2 * s * s for s in np.linspace(0, 1, 30)])
            add("eye", stroke(pts, th[-1] * 1.05, lambda q: np.clip(1 - q, 0, 1) ** 0.75))
        # lash clusters
        for (tt, ln) in st["spikes"]:
            k = int(tt * (len(U) - 1))
            base = U[k] + nU[k] * th[k] * 0.8
            outward = dU[k]
            dirv = nU[k] * 0.6 + outward * 0.8
            dirv /= np.linalg.norm(dirv)
            mid = base + dirv * ln * 0.55 + outward * ln * 0.1
            tip = base + dirv * ln + outward * ln * 0.25
            pts = np.array([base * (1 - s) ** 2 + 2 * mid * s * (1 - s) + tip * s * s for s in np.linspace(0, 1, 20)])
            add("eye", stroke(pts, 6.5, lambda q: np.clip(1 - q, 0, 1) ** 0.9))
        # lower lid line (outer part strong, inner hint)
        lf = st["lower_from"]
        n0 = int(lf * (len(L) - 1))
        add("low", stroke(L[n0:], 4.8, lambda q: np.clip(np.sin(np.pi * q) ** 0.5 * (0.4 + 0.6 * q), 0, 1)))
        add("low", stroke(L[: int(len(L) * 0.1)], 2.6, taper))
        for tt in st.get("lowlash", []):
            k = int(tt * (len(L) - 1))
            nL, dL = normals(L)
            if nL[k, 1] < 0:
                nL = -nL
            base = L[k] + nL[k] * 1.5
            tip = base + (nL[k] * 0.8 + dL[k] * 0.5) * 13
            add("low", stroke(np.linspace(base, tip, 10), 4.2, lambda q: np.clip(1 - q, 0, 1)))
        # crease (double lid line)
        if "crease" in st:
            g = st["crease"]
            ts = slice(int(len(U) * 0.18), int(len(U) * 0.92))
            cr = U[ts] + nU[ts] * (th[ts, None] + g * (0.6 + 0.4 * np.sin(np.pi * t[ts, None])))
            add("eye", stroke(cr, 3.6, lambda q: np.sin(np.pi * q) ** 0.9))
        # tired bags
        for (gap, span) in st.get("bags", []):
            nL, _ = normals(L)
            if nL[:, 1].mean() < 0:
                nL = -nL
            a0, a1 = int(len(L) * (0.5 - span / 2)), int(len(L) * (0.5 + span / 2))
            bg = L[a0:a1] + nL[a0:a1] * (gap + (16 if st.get("lowlash") else 0))  # clear of lower lashes
            add("bags", stroke(bg, 3.4, lambda q: np.sin(np.pi * q) ** 1.1))
        # brows are a separate layer now (gen_face.py); record how high the lash work reaches
        em = mask(G["eye"][eye0:])
        hit = em > 0.02
        has = hit.reshape(SH[0], CW, S).any(2).any(0)
        topc = CY0 + hit.reshape(SH[0], CW, S).any(2).argmax(0) / S
        tops.append(np.where(has, topc, np.nan))

    # ---- compose main layer
    eye_open = np.clip(sum(o for _, o, _ in sclera_layers), 0, 1)
    outside = 1 - eye_open
    # skin effects around the eye (drawn first; they live outside the opening)
    if form == "vampire":
        under = np.clip(shift(blur(eye_open, 10), 14) - eye_open, 0, 1)
        over(SHADE, under * 0.55)
    elif form == "ghoul":
        socket = np.clip(blur(eye_open, 20) * 1.9, 0, 1) * outside
        over(np.array([0.13, 0.07, 0.13], np.float32), socket * 0.72)
    elif form == "wolf":
        socket = np.clip(blur(eye_open, 12) * 1.4, 0, 1) * outside
        over(np.array([0.18, 0.12, 0.08], np.float32), socket * 0.35)
    elif form == "wraith":
        halo = np.clip(blur(eye_open, 14) * 1.5, 0, 1) * outside
        over(np.array([0.74, 0.9, 1.0], np.float32), halo * 0.62)
    if vein_trees:
        prot = blur(mask(G["eye"] + G["low"] + G["bags"]), 1.6) > 0.01
        kept = {}
        for side_, corner_, tree, want in vein_trees:
            key_ = (side_, corner_)
            if kept.get(key_, 0) >= want:
                continue
            tm = mask(tree) > 0.3
            if (tm & prot).any():
                continue
            kept[key_] = kept.get(key_, 0) + 1
            skin_veins += tree
            G["veins"] += tree
    # shaded skin veins: bruise halo, dark body, a lit top edge and a deeper core
    if form in ("ghoul", "vampire") and skin_veins:
        keep_off = np.clip(blur(mask(ink_polys + fur_polys), 2.5) * 6, 0, 1)
        vm = mask(skin_veins) * outside * (1 - keep_off)
        g = form == "ghoul"
        vover(0.72, np.clip(blur(vm, 6) * 1.6, 0, 1) * outside * (1 - keep_off) * (0.6 if g else 0.45))  # bruise
        vover(0.46, vm * (0.97 if g else 0.92))                                                        # vein body
        lit = np.clip(vm - shift(vm, 1.4), 0, 1)                                                      # raised: lit top edge
        vover(1.0, lit * 0.55)
        core = np.clip(vm * 2 - 1, 0, 1)
        vover(0.24, np.clip(blur(core, 0.4) - lit, 0, 1) * 0.5)                                        # deep core
    for scl, opening, s in sclera_layers:
        a = opening * (1 - s["disc"])
        over(scl, a)
    if scl_veins:
        vm = mask(scl_veins)
        for scl, opening, s in sclera_layers:
            vv = vm * opening * (1 - s["disc"])
            over(np.array([0.9, 0.3, 0.32], np.float32), np.clip(blur(vv, 2.2) * 1.3, 0, 1) * opening * (1 - s["disc"]) * 0.22)
            over(np.array([0.66, 0.04, 0.1], np.float32), vv * (0.85 if form == "vampire" else 0.95))
    lash_m = mask(shadow_polys)
    for scl, opening, s in sclera_layers:
        rr, dy, disc, v = s["rr"], s["dy"], s["disc"], s["v"]
        iris_here = disc * opening
        # lid shadow across the iris top
        over(SHADE, iris_here * (0.2 if form == "wraith" else 0.62) * np.exp(-v * 3.2))
        # limbal ring
        lim = {"ghoul": 0.35, "wraith": 0.15}.get(form, 0.92)
        over(INK, np.clip(smooth(0.80, 0.985, rr) * lim, 0, 1) * np.clip((1.03 - rr) * s["r"] / 0.8, 0, 1) * opening)
        # pupil
        ix, iy, r = s["ix"], s["iy"], s["r"]
        pm = None
        if form == "vampire":
            # blade-shaped slit: parabolic width so both tips come to a point
            u_, v_ = (XX - ix) / r, (YY - iy) / r
            H_ = 0.82
            halfw = 0.1 * np.clip(1 - (v_ / H_) ** 2, 0, 1)
            pm = np.clip((halfw - np.abs(u_)) * r / 0.6 + 0.5, 0, 1) * (np.abs(v_) < H_)
            # sigil ring + fine spokes through the red iris (drawn before the pupil so it sits on top)
            ang_ = np.arctan2(v_, u_)
            ring_ = np.exp(-((rr - 0.6) / 0.022) ** 2)
            spoke_px = np.abs(np.sin(ang_ * 8)) / 8 * rr * r
            spokes_ = np.clip(1.3 - spoke_px / 1.1, 0, 1) * smooth(0.62, 0.68, rr) * (1 - smooth(0.86, 0.93, rr))
            over(np.array([0.28, 0.02, 0.06], np.float32), np.clip(ring_ * 0.75 + spokes_ * 0.45, 0, 1) * disc * opening)
            # hot rim hugging the slit
            halfw2 = (0.1 + 0.07) * np.clip(1 - (v_ / (H_ + 0.08)) ** 2, 0, 1)
            rim_ = np.clip((halfw2 - np.abs(u_)) * r / 0.9 + 0.5, 0, 1) * (np.abs(v_) < H_ + 0.08)
            over(np.array([1.0, 0.52, 0.46], np.float32), np.clip(rim_ - pm, 0, 1) * 0.8 * opening)
            over(np.array([1.0, 0.25, 0.25], np.float32), np.clip(blur(rim_, 3) - rim_, 0, 1) * 0.55 * disc * opening)
        elif form == "wolf":
            # feral pupil: a ragged edge, a hot gold rim and a starburst through the amber
            u_, v_ = (XX - ix) / r, (YY - iy) / r
            ang_ = np.arctan2(v_, u_)
            ph_ = rng.uniform(0, 6.28)
            edge = 0.25 + 0.03 * np.sin(9 * ang_ + ph_) + 0.018 * np.sin(23 * ang_ + 2 * ph_) + 0.02 * np.abs(np.sin(ang_ * 2))
            burst_px = np.abs(np.sin(ang_ * 7 + ph_)) / 7 * rr * r
            burst = np.clip(1.4 - burst_px / (0.9 + 2.2 * (1 - rr)), 0, 1) * smooth(edge + 0.02, edge + 0.08, rr) * (1 - smooth(0.6, 0.86, rr))
            over(np.array([1.0, 0.8, 0.32], np.float32), burst * 0.45 * disc * opening)
            rim_ = np.clip((edge + 0.07 - rr) * r / 0.9 + 0.5, 0, 1)
            over(np.array([1.0, 0.88, 0.5], np.float32), np.clip(blur(rim_, 2.5) * 1.2, 0, 1) * 0.6 * disc * opening)
            pm = np.clip((edge - rr) * r / 0.6 + 0.5, 0, 1)
        elif form == "ghoul":
            pm = ell(ix, iy, r * 0.085, r * 0.085)
        elif form == "wraith":
            over(np.ones(3, np.float32), ell(ix, iy, r * 0.55, r * 0.55, soft=12) * 0.7 * opening)
        elif st.get("slit"):
            pm = ell(ix, iy, r * 0.13, r * 0.72)
        else:
            pm = ell(ix, iy + r * 0.03, r * 0.40, r * 0.43)
        if pm is not None:
            over(np.array([0.04, 0.02, 0.04], np.float32), pm * opening)
            # soft ring around the pupil
            if form not in ("vampire", "wolf"):
                over(INK, (ell(ix, iy, r * 0.56, r * 0.58, soft=6) - pm).clip(0, 1) * (0.08 if form == "ghoul" else 0.18) * opening)
        if form == "vampire":
            bloom = np.clip(blur(disc, 7) - disc, 0, 1) * opening
            over(np.array([0.86, 0.1, 0.16], np.float32), bloom * 0.5)
    # lash cast shadow (onto eye only)
    over(SHADE, shift(blur(lash_m, 4.5), 4) * eye_open * 0.5)
    for idx, (scl, opening, s) in enumerate(sclera_layers):
        r, ix, iy, rr, dy = s["r"], s["ix"], s["iy"], s["rr"], s["dy"]
        outward = -1 if idx == 0 else 1
        # glossy highlights
        h1 = ell(ix + outward * r * 0.30, iy - r * 0.36, r * 0.22, r * 0.15, rot=outward * 0.55)
        h2 = ell(ix - outward * r * 0.30, iy + r * 0.34, r * 0.075, r * 0.065)
        h3 = ell(ix + outward * r * 0.02, iy - r * 0.46, r * 0.06, r * 0.05)
        arc = np.exp(-((rr - 0.80) / 0.05) ** 2) * smooth(0.25, 0.75, dy) * smooth(0, 0.6, -outward * s["dx"])
        over(np.ones(3, np.float32), np.clip(h1 * 0.96 + h2 * 0.9 + h3 * 0.7, 0, 1) * opening)
        over(np.ones(3, np.float32), arc * 0.32 * opening)
    # line work with a faint brush grain
    lines = mask(ink_polys + fur_polys)
    grain = blur(rng.random(SH).astype(np.float32), 0.5)
    over(INK, np.clip(lines * (0.93 + 0.14 * grain), 0, 1))

    # ---- overlap report: line groups that should never touch (2 px tolerance)
    report = []
    gm = {k: (mask(v) if v else None) for k, v in G.items()}
    for a_, b_ in CHECK_PAIRS:
        if gm[a_] is None or gm[b_] is None:
            continue
        near = blur(gm[b_], 0.5) > 0.02
        px = float(((gm[a_] > 0.5) & near).sum()) / (S * S)
        if px > 1.0:
            report.append(f"{a_}/{b_}:{px:.0f}px")
    render.report = report
    t2 = np.fmin(tops[0], tops[1]) if len(tops) == 2 else tops[0]
    render.top = [None if np.isnan(v) else round(float(v), 1) for v in t2]
    # lowest drawn pixel of the main layer (for mouth fitting)
    rows = np.where((np.maximum(main_a, vein_a) > 0.05).any(1))[0]
    render.bottom = float(CY0 + rows.max() / S) if len(rows) else 0.0

    def save(rgb, a, name):
        if rgb.ndim == 2:
            rgb = np.repeat(rgb[..., None], 3, 2)
        rd = down(rgb * a[..., None])
        ad = down(a)
        rd = rd / np.maximum(ad[..., None], 1e-6)
        band = np.dstack([np.clip(rd, 0, 1), np.clip(ad, 0, 1)])
        out = np.zeros((N, N, 4), np.float32)
        out[CY0:CY0 + CH, CX0:CX0 + CW] = band
        Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, name), optimize=True)
        return out

    i_out = save(iris_rgb, iris_a, f"eyes_{sid}_iris.png")
    m_out = save(main_rgb, main_a, f"eyes_{sid}_main.png")
    v_out = save(vein_g, vein_a, f"eyes_{sid}_veins.png") if vein_a.max() > 0.01 else None
    return i_out, m_out, v_out

VEIN_TINT = {"ghoul": (0.3, 0.05, 0.32), "vampire": (0.62, 0.04, 0.12)}   # mixed VEIN_MIX into the skin colour in game
VEIN_MIX = 0.5

def composite(i_out, m_out, skin, tint, v_out=None, vform=None):
    b = np.ones((N, N, 3), np.float32) * np.array(skin, np.float32)
    if v_out is not None:
        vt = np.array(skin, np.float32) * (1 - VEIN_MIX) + np.array(VEIN_TINT[vform], np.float32) * VEIN_MIX
        va = v_out[..., 3:]
        b = v_out[..., :3] * vt * va + b * (1 - va)
    ia = i_out[..., 3:]
    b = i_out[..., :3] * np.array(tint, np.float32) * ia + b * (1 - ia)
    ma = m_out[..., 3:]
    return m_out[..., :3] * ma + b * (1 - ma)

FORM_TINT = {"vampire": (0.86, 0.13, 0.2), "wolf": (0.92, 0.62, 0.16), "ghoul": (0.84, 0.86, 0.8), "wraith": (0.62, 0.86, 1.0),
             "vampire2": (0.86, 0.13, 0.2), "ghoul2": (0.84, 0.86, 0.8)}
BASE_TINTS = [(0.59, 0.38, 0.24), (0.49, 0.67, 0.84), (0.59, 0.50, 0.27), (0.38, 0.53, 0.35),
              (0.50, 0.38, 0.65), (0.84, 0.61, 0.20), (0.59, 0.38, 0.24), (0.59, 0.61, 0.65)]
SKIN = (0.88, 0.74, 0.62)

def job(args):
    k, sid, female, form = args
    st = variant(STYLES[sid], female, form)
    name = f"{sid}_{'f' if female else 'm'}_{form}"
    seed = 11 + k * 7 + (3 if female else 0) + FORMS.index(form) * 101
    global OUTNAME
    i_out, m_out, v_out = render(name, st, seed)
    if render.report:
        print("OVERLAP", name, " ".join(render.report), flush=True)
    tint = FORM_TINT.get(form, BASE_TINTS[k])
    img = composite(i_out, m_out, SKIN, tint, v_out, st["form"])
    tile = (img[CY0 + 40:CY0 + CH - 60, 112:912] * 255).astype(np.uint8)
    Image.fromarray(tile).save(os.path.join(OUT, "tiles", name + ".png"))
    import json as _json
    _json.dump({"x0": CX0, "top": render.top, "bottom": render.bottom}, open(os.path.join(OUT, "tiles", name + "_fit.json"), "w"))
    return name

if __name__ == "__main__":
    from multiprocessing import Pool
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    forms = sys.argv[3].split(",") if len(sys.argv) > 3 else FORMS
    sexes = [False, True]
    jobs = []
    for k, sid in enumerate(STYLES):
        if ONLY and sid not in ONLY:
            continue
        for female in sexes:
            for form in forms:
                jobs.append((k, sid, female, form))
    workers = int(os.environ.get("EYE_WORKERS", "6"))
    with Pool(workers) as pool:
        for name in pool.imap_unordered(job, jobs):
            print("ok", name, flush=True)
    # contact sheets: one per form (rows = shapes, columns = male | female)
    for form in forms:
        rows = [sid for sid in STYLES if not ONLY or sid in ONLY]
        sheet = Image.new("RGB", (1600, 340 * len(rows)), (16, 14, 20))
        for r_, sid in enumerate(rows):
            for c_, sx in enumerate("mf"):
                pth = os.path.join(OUT, "tiles", f"{sid}_{sx}_{form}.png")
                if os.path.exists(pth):
                    sheet.paste(Image.open(pth), (c_ * 800, r_ * 340))
        sheet.save(os.path.join(OUT, f"sheet_{form}.png"))
    print("done", flush=True)
