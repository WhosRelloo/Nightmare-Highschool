"""Everyday ghoul versions of the in-game school uniform (Ghoul race, Tier I look).

Same uniforms, same colours: just worn by something that climbed out of a grave.
Torn (tears show the ghoul's own skin), crudely re-stitched with cross-stitch,
grave dirt and damp tide-marks, frayed cuffs and hem, a little faded.

The four shirts are the in-game uniforms (Appearance.Uniforms 1-4), which are the
user's source files. The in-game trousers are pants_jeans_b with white sneakers
and a see-through upper torso; the sneakers are redrawn here.
"""
import numpy as np
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, LEGS, FRONTS, BACKS, OUTERS, INNERS
import nhcloth

F32 = np.float32
THREAD = (34, 28, 24)
DIRT = (74, 62, 46)
MUD = (58, 46, 32)

UNIFORMS = {
    "RedVest": ("shirt_maroon_vest_grey.png", "shirt_ghoul_uniform_red_vest.png", 901),
    "RedShirt": ("shirt_maroon_polo_khaki.png", "shirt_ghoul_uniform_red_shirt.png", 902),
    "BlackVest": ("shirt_black_red_vest.png", "shirt_ghoul_uniform_black_vest.png", 903),
    "BlackShirt": ("shirt_black_polo_khaki.png", "shirt_ghoul_uniform_black_shirt.png", 904),
}
PANTS_OUT = "pants_ghoul_uniform.png"


def save(c, name):
    return nhcloth.save(finish(c, creases=False, seed=sum(map(ord, name))), name)


# ---------------------------------------------------------------- wear and tear
def fade(c, m, amount=0.16):
    g = c[..., :3].mean(-1, keepdims=True)
    faded = c[..., :3] * (1 - amount) + g * amount
    faded = faded * 0.95 + 9
    c[m, :3] = np.clip(faded[m], 0, 255)
    return c


def damp_stains(c, m, seed, names=None, rise=(9, 18)):
    """Grave damp wicked up from the hem and cuffs, ending in an irregular
    tide-line, plus a couple of small splash marks."""
    rng = np.random.default_rng(seed)
    wob = ndimage.gaussian_filter1d(rng.standard_normal(W), 4)
    wob = (wob - wob.min()) / (np.ptp(wob) + 1e-6)
    wet = np.zeros((H, W), bool)
    for n in names or (TORSO_RING + ARM_FACES):
        x, y, w, h = R[n]
        for xx in range(x, x + w):
            col = np.nonzero(m[y:y + h, xx])[0]
            if len(col) == 0:
                continue
            bottom = y + col.max()
            tide = bottom - (rise[0] + (rise[1] - rise[0]) * wob[xx])
            wet[int(tide):bottom + 1, xx] = True
    splash = noise(H, W, seed + 1, 3.5) > 2.1
    wet = (wet | splash) & m
    shade(c, wet.astype(F32), 0.86)
    rim = ndimage.binary_dilation(wet, iterations=1) & ~wet & m
    shade(c, rim.astype(F32), 0.74)
    return c


def grave_dirt(c, m, seed, zones, amount=0.42):
    for i, z in enumerate(zones):
        if (m & z).any():
            scuffs(c, m & z, seed + 11 * i, amount=amount, color=DIRT, blobs=10, spread=4)
    specks = m & (noise(H, W, seed + 77, 0.7) > 2.4)
    c[specks, :3] = np.clip(c[specks, :3] * 0.55 + np.array(MUD, F32) * 0.45, 0, 255)
    return c


def fray_bottom(c, names, seed, max_cut=3, threads=0.3):
    """Ragged, frayed bottom edge on each face (sleeve cuffs, trouser hems)."""
    rng = np.random.default_rng(seed)
    for n in names:
        x, y, w, h = R[n]
        for xx in range(x, x + w):
            col = np.nonzero(c[y:y + h, xx, 3] > 0)[0]
            if len(col) == 0:
                continue
            bottom = y + col.max()
            cut = int(rng.integers(0, max_cut + 1))
            if cut:
                c[bottom - cut + 1:bottom + 1, xx, 3] = 0
                c[bottom - cut + 1:bottom + 1, xx, :3] = 255
            edge = bottom - cut
            c[edge, xx, :3] = np.clip(c[edge, xx, :3] * 0.6, 0, 255)
            if rng.random() < threads and edge + 4 < y + h:
                L = int(rng.integers(2, 6))
                base = c[edge - 2, xx, :3] * 0.85 + 18
                for k in range(1, L + 1):
                    if edge + k <= bottom + max_cut + 4 and edge + k < y + h:
                        c[edge + k, xx, :3] = np.clip(base, 0, 255)
                        c[edge + k, xx, 3] = 255
    return c


def fray_hem_torso(c, seed, rows=(198, 201)):
    rng = np.random.default_rng(seed)
    ring = rect_mask(TORSO_RING)
    for xx in np.unique(np.nonzero(ring)[1]):
        cut = int(rng.integers(0, 4))
        if cut and c[201, xx, 3] > 0:
            c[202 - cut:202, xx, 3] = 0
            c[202 - cut:202, xx, :3] = 255
            c[201 - cut, xx, :3] = np.clip(c[201 - cut, xx, :3] * 0.6, 0, 255)
    return c


def tear(c, p0, p1, seed, width=2.4):
    """An open ragged slit; the wearer's skin shows through."""
    rng = np.random.default_rng(seed)
    L = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
    nx, ny = -(p1[1] - p0[1]) / L, (p1[0] - p0[0]) / L
    k = max(4, int(L / 2))
    top, bot = [], []
    for i in range(k + 1):
        t = i / k
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        wv = width * np.sin(np.pi * t) ** 0.7 * (0.6 + 0.8 * rng.random())
        top.append((x + nx * wv, y + ny * wv))
        bot.append((x - nx * wv, y - ny * wv))
    m = poly(top + bot[::-1])
    hole = m > 0.5
    vis = c[..., 3] > 0
    rim = ndimage.binary_dilation(hole, iterations=1) & ~hole & vis
    shade(c, rim.astype(F32), 0.5)
    fr = ndimage.binary_dilation(hole, iterations=2) & ~ndimage.binary_dilation(hole, iterations=1) & vis
    fr &= np.random.default_rng(seed + 1).random((H, W)) < 0.35
    c[fr, :3] = np.clip(c[fr, :3] * 1.35 + 20, 0, 255)
    clear(c, hole & vis)
    return c


def cross_stitch(c, p0, p1, every=4.0, arm=2.2, thread=THREAD, closed=True):
    """Crude cross-stitch: an X every few pixels along a line.
    closed=True also draws the pulled-together seam underneath."""
    L = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    nx, ny = -uy, ux
    if closed:
        seam = lines([p0, p1], 1)
        shade(c, seam * (c[..., 3] > 0), 0.45)
        pucker = lines([p0, p1], 5) * (1 - seam)
        shade(c, pucker * (c[..., 3] > 0), 0.88)

    def xs(d):
        n = int(L / every)
        for i in range(1, n + 1):
            x, y = p0[0] + ux * i * every, p0[1] + uy * i * every
            a = (x + (ux + nx) * arm * 0.7, y + (uy + ny) * arm * 0.7)
            b = (x - (ux + nx) * arm * 0.7, y - (uy + ny) * arm * 0.7)
            e = (x + (ux - nx) * arm * 0.7, y + (uy - ny) * arm * 0.7)
            f = (x - (ux - nx) * arm * 0.7, y - (uy - ny) * arm * 0.7)
            d.line([a, b], fill=255, width=1)
            d.line([e, f], fill=255, width=1)
    m = shape(xs) * (c[..., 3] > 0)
    lift(c, m, strength=0.35, sigma=0.8)
    paint(c, m, thread)
    return c


# ---------------------------------------------------------------- shirts
def ghoul_shirt(key):
    src_name, out_name, seed = UNIFORMS[key]
    c = remove_magenta(load(src_name))
    clear(c, ~rect_mask(ALL_REGIONS, pad=2))          # drops the stray note on the polo
    vis = c[..., 3] > 0
    fabric = vis & rect_mask(TORSO_RING + ARM_FACES + ["T_UP"] + ARM_UPS + ["T_D"])
    fade(c, fabric)
    damp_stains(c, fabric, seed)
    zones = [rect_mask(TORSO_RING) & (YY > 160), rect_mask(ARM_FACES) & (YY > 425),
             rect_mask(ARM_FACES) & (YY > 390) & (YY < 412), rect_mask(["T_D"]),
             rect_mask(TORSO_RING) & (YY < 160)]
    grave_dirt(c, fabric, seed, zones)
    fray_bottom(c, ARM_FACES, seed)
    fray_hem_torso(c, seed + 1)
    # two open tears that show the ghoul's skin, three stitched shut
    rng = np.random.default_rng(seed)
    jit = lambda: rng.uniform(-3, 3)
    tear(c, (243 + jit(), 158 + jit()), (262 + jit(), 166 + jit()), seed + 2)
    tear(c, (448 + jit(), 112 + jit()), (462 + jit(), 128 + jit()), seed + 3, width=2.0)
    cross_stitch(c, (334 + jit(), 150), (350 + jit(), 176))
    cross_stitch(c, (226, 392 + jit()), (262, 400 + jit()))
    cross_stitch(c, (392, 96 + jit()), (404 + jit(), 128))
    # a sleeve re-sewn at the shoulder with big crude stitches
    cross_stitch(c, (309, 357), (370, 357), every=5.0, arm=2.6, closed=False)
    cross_stitch(c, (218, 357), (279, 357), every=5.0, arm=2.6, closed=False)
    return save(c, out_name)


# ---------------------------------------------------------------- sneakers
def white_sneakers(c, seed=5, top=451):
    m = rect_mask(LEGS) & (YY >= top)
    d = fabric_detail(seed, cloud=0.04, twill=0, grain=0.02)
    c[m, :3] = tint(d, (224, 224, 220), 8)[m]
    c[m, 3] = 255
    shade(c, (rect_mask(LEGS) & (YY == top)).astype(F32), 0.55)
    for n in LEGS:
        x, y, w, h = R[n]
        paint(c, dash([(x + 2, 470), (x + w * 0.5, 466), (x + w - 2, 470)], on=2, off=1) * rect_mask([n]), (170, 170, 168))
    for n in FRONTS:
        x, y, w, h = R[n]
        mx = x + w / 2
        tongue = (XX >= mx - 7) & (XX <= mx + 7) & (YY >= top + 1) & (YY <= 463)
        c[tongue, :3] = c[tongue, :3] * 0.92
        for ly in range(top + 3, 462, 3):
            paint(c, lines([(mx - 6, ly), (mx + 6, ly + 2)]) + lines([(mx + 6, ly), (mx - 6, ly + 2)]), (190, 190, 188))
            for ex in (mx - 7, mx + 7):
                paint(c, shape(lambda d: d.point((ex, ly), fill=255)), (90, 90, 92))
        paint(c, shape(lambda d: d.arc((x + 6, 466, x + w - 6, 482), 180, 360, fill=255)), (176, 176, 174))
    for n in OUTERS:
        x, y, w, h = R[n]
        paint(c, lines([(x + 10, 462), (x + w * 0.55, 470), (x + w - 8, 462)], 2), (186, 186, 184))
    sole = rect_mask(LEGS) & (YY >= 477)
    c[sole, :3] = (206, 206, 204)
    shade(c, (rect_mask(LEGS) & (YY == 477)).astype(F32), 0.75)
    for n in LEGS:
        x, y, w, h = R[n]
        c[(YY >= 479) & (XX % 4 == 0) & rect_mask([n]), :3] = (180, 180, 178)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = tint(fabric_detail(seed + 1, cloud=0.04, twill=0), (214, 214, 212), 6)[dn]
    c[dn, 3] = 255
    for n in ARM_DOWNS:
        x, y, w, h = R[n]
        cx = x + w / 2
        ring = shape(lambda d: [d.ellipse((cx - r, y + 22 - r, cx + r, y + 22 + r), outline=255) for r in range(4, 22, 3)])
        heel = shape(lambda d: [d.ellipse((cx - r, y + 52 - r, cx + r, y + 52 + r), outline=255) for r in range(3, 10, 3)])
        paint(c, np.clip(ring + heel, 0, 1) * rect_mask([n]), (176, 176, 174))
        for bx in (x + 3, x + w - 7):
            paint(c, shape(lambda d: d.rounded_rectangle((bx, y + 8, bx + 4, y + 40), 2, outline=255)), (176, 176, 174))
    return c


def ghoul_pants():
    c = load("pants_jeans_b.png")
    # match the in-game uniform trousers: see-through top and upper torso, white sneakers
    clear(c, rect_mask(["T_UP"]) | (rect_mask(TORSO_RING) & (YY < 180)))
    white_sneakers(c)
    seed = 905
    vis = c[..., 3] > 0
    denim = vis & ((rect_mask(LEGS) & (YY < 451)) | rect_mask(ARM_UPS) | (rect_mask(TORSO_RING) & (YY >= 180)) | rect_mask(["T_D"]))
    shoes = vis & ((rect_mask(LEGS) & (YY >= 451)) | rect_mask(ARM_DOWNS))
    fade(c, denim, 0.12)
    damp_stains(c, denim, seed, names=LEGS, rise=(14, 26))
    zones = [rect_mask(LEGS) & (YY > 420) & (YY < 451), rect_mask(FRONTS) & (YY > 395) & (YY < 420),
             rect_mask(["T_D"]), rect_mask(LEGS) & (YY < 395)]
    grave_dirt(c, denim, seed, zones, amount=0.45)
    # muddy sneakers: worst at the toe and sole
    scuffs(c, shoes, seed + 3, amount=0.55, color=MUD, blobs=26, spread=4)
    for n in LEGS:
        x, y, w, h = R[n]
        grad = np.clip((YY - 466) / 16.0, 0, 1) * rect_mask([n])
        c[..., :3] = c[..., :3] * (1 - 0.35 * grad[..., None]) + np.array(MUD, F32) * 0.35 * grad[..., None]
    scuffs(c, shoes & rect_mask(ARM_DOWNS), seed + 4, amount=0.5, color=MUD, blobs=14, spread=5)
    # frayed hems hanging over the sneakers
    rng = np.random.default_rng(seed)
    for n in LEGS:
        x, y, w, h = R[n]
        for xx in range(x, x + w):
            if rng.random() < 0.45:
                L = int(rng.integers(1, 5))
                col = c[448, xx, :3] * 0.9 + 10
                c[451:451 + L, xx, :3] = np.clip(col, 0, 255)
        shade(c, (rect_mask([n]) & (YY == 450)).astype(F32), 0.55)
    # a knee torn open, a stitched rip, a crude repair on the seat
    tear(c, (232, 414), (256, 418), seed + 5, width=2.6)
    tear(c, (330, 408), (348, 404), seed + 6, width=2.0)
    cross_stitch(c, (440, 380), (468, 392))
    cross_stitch(c, (160, 372), (172, 404))
    cross_stitch(c, (250, 214), (282, 222))
    return save(c, PANTS_OUT)


def build():
    out = []
    with nhcloth.supersample(4):
        for k in UNIFORMS:
            out.append(ghoul_shirt(k))
        out.append(ghoul_pants())
    return out


if __name__ == "__main__":
    for p in build():
        print(p.name)
