"""Pants: denim washes from the user's jeans, plus new trousers, shorts and a skirt."""
import numpy as np
from scipy import ndimage

from nhcloth import *  # noqa: F401,F403
from shirts_new import lines, poly, dash, button, rib_band

YY, XX = np.mgrid[0:H, 0:W]
CX = 294.5
LEGS = ARM_FACES          # same rects on the pants template
LEG_UPS = ARM_UPS
LEG_DOWNS = ARM_DOWNS
SHOE_TOP = 451            # the jeans' sneakers start on this row
FRONTS = ["RA_F", "LA_F"]
BACKS = ["RA_B", "LA_B"]
OUTERS = ["RA_R", "LA_L"]
INNERS = ["RA_L", "LA_R"]


def denim_zone(src):
    legs = rect_mask(LEGS) & (YY < SHOE_TOP)
    torso = rect_mask(TORSO_RING) & (src[..., 3] > 0) & (YY >= 178)
    return legs | rect_mask(LEG_UPS) | torso | rect_mask(["T_D"])


def ramp(L, stops):
    xs = [s[0] for s in stops]
    out = np.zeros(L.shape + (3,), np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(L, xs, [s[1][ch] for s in stops])
    return out


def denim_wash(src_name, name, stops, thread=None):
    c = load(src_name)
    z = denim_zone(c)
    L = c[..., :3].mean(-1) / 255.0
    new = ramp(L, stops)
    if thread is not None:
        th = z & (L > 0.80) & (sat(c) < 0.12)
        new[th] = thread
    c[z, :3] = new[z]
    return save_hq(c, name)


# ---------------------------------------------------------------- rips
def rip(c, cx, cy, w, h, seed):
    rng = np.random.default_rng(seed)
    e = ((XX - cx) / (w / 2)) ** 2 + ((YY - cy) / (h / 2)) ** 2
    jag = 1 + 0.35 * noise(H, W, seed, 1.0)
    hole = e < jag * 0.8
    fray = (e < jag * 1.25) & ~hole
    c[fray, :3] = np.clip(c[fray, :3] * 1.45 + 30, 0, 255)
    clear(c, hole)
    # white weft threads left across the hole
    for ty in range(int(cy - h / 2) + 1, int(cy + h / 2), 2):
        row = hole & (YY == ty) & (rng.random((H, W)) > 0.12)
        c[row, :3] = (236, 234, 226)
        c[row, 3] = 255
    shade(c, (ndimage.binary_dilation(fray, iterations=1) & ~fray & ~hole).astype(np.float32), 0.7)
    return c


def ripped_jeans(name="pants_jeans_ripped.png"):
    c = load("pants_jeans_a.png")
    z = denim_zone(c)
    # bleached knees
    glow = np.zeros((H, W), np.float32)
    for (x, y) in ((249, 410), (340, 414), (115, 410), (472, 414)):
        glow[y, x] = 1
    glow = ndimage.gaussian_filter(glow, 11)
    glow = glow / glow.max() * z
    c[..., :3] = np.clip(c[..., :3] * (1 + 0.35 * glow[..., None]), 0, 255)
    for args in ((249, 412, 30, 10, 1), (236, 380, 14, 5, 2), (341, 416, 28, 9, 3),
                 (357, 386, 12, 4, 4), (183, 398, 12, 5, 5), (402, 430, 10, 4, 6)):
        rip(c, *args)
    return save_hq(c, name)


# ---------------------------------------------------------------- trousers base
def pants_base(cloth, seed, tex=None, belt=(26, 20, 18), buckle=GOLD, crease=True, leg_end=SHOE_TOP, fly=True):
    c = blank((0, 0, 0), 255)                      # the sources use an opaque black margin
    hole = load("pants_jeans_a.png")[..., 3] == 0  # same see-through panel as the jeans
    tex = tex or {}
    names = TORSO_RING + ["T_D"] + LEGS + LEG_UPS
    d = fabric_detail(seed, **tex)
    col = tint(d, cloth)
    m = rect_mask(names)
    m &= ~(rect_mask(TORSO_RING) & (YY < 178))
    m &= ~(rect_mask(LEGS) & (YY >= leg_end))
    c[m, :3] = col[m]
    c[m, 3] = 255
    # belt with loops and a buckle
    if belt:
        bm = rect_mask(TORSO_RING) & (YY >= 181) & (YY <= 188)
        bd = fabric_detail(seed + 3, cloud=0.05, twill=0, grain=0.02)
        c[bm, :3] = tint(bd, belt)[bm]
        shade(c, (bm & ((YY == 181) | (YY == 188))).astype(np.float32), 0.5)
        for lx in (190, 250, 339, 392, 450, 491, 532):
            loop = rect_mask(TORSO_RING) & (XX >= lx) & (XX <= lx + 3) & (YY >= 179) & (YY <= 190)
            c[loop, :3] = col[loop] * 0.92
            shade(c, outline_of(loop, 1).astype(np.float32), 0.5)
        frame = (XX >= 287) & (XX <= 302) & (YY >= 180) & (YY <= 189)
        inner = (XX >= 290) & (XX <= 299) & (YY >= 183) & (YY <= 186)
        paint(c, (frame & ~inner).astype(np.float32), buckle)
        shade(c, outline_of(frame, 1).astype(np.float32), 0.5)
    # waistband seam, fly, pockets
    shade(c, (rect_mask(TORSO_RING) & (YY == 178)).astype(np.float32), 0.45)
    shade(c, (rect_mask(TORSO_RING) & (YY == 191)).astype(np.float32), 0.7)
    if fly:
        paint(c, lines([(CX, 191), (CX, 201)]), tuple(int(v * 0.45) for v in cloth))
        paint(c, dash([(CX + 5, 191), (CX + 5, 199), (CX, 201)], on=2, off=1), tuple(int(v * 0.6) for v in cloth))
        paint(c, lines([(246, 191), (238, 201)]) + lines([(343, 191), (351, 201)]), tuple(int(v * 0.4) for v in cloth))
    paint(c, lines([(446, 196), (470, 196)]) + lines([(512, 196), (536, 196)]), tuple(int(v * 0.4) for v in cloth))
    paint(c, lines([(CX, 204), (CX, 267)]), tuple(int(v * 0.5) for v in cloth))
    # legs: pressed crease, side seams, hem
    if crease:
        for n in FRONTS + BACKS:
            x, y, w, h = R[n]
            mx = x + w // 2
            cm = rect_mask([n]) & (YY < leg_end - 2)
            c[cm & (XX == mx), :3] = np.clip(c[cm & (XX == mx), :3] * 1.3 + 8, 0, 255)
            shade(c, (cm & (XX == mx + 1)).astype(np.float32), 0.75)
    for n in OUTERS + INNERS:
        x, y, w, h = R[n]
        paint(c, dash([(x + w // 2, y), (x + w // 2, leg_end - 3)], on=2, off=2), tuple(int(v * 0.55) for v in cloth))
    hem = rect_mask(LEGS) & (YY >= leg_end - 4) & (YY < leg_end)
    shade(c, hem.astype(np.float32), 0.85)
    shade(c, (rect_mask(LEGS) & (YY == leg_end - 1)).astype(np.float32), 0.45)
    clear(c, hole)
    return c


def school_shoes(c, seed=5, leather=(24, 22, 26)):
    m = rect_mask(LEGS) & (YY >= SHOE_TOP)
    d = fabric_detail(seed, cloud=0.06, twill=0, grain=0.02)
    c[m, :3] = tint(d, leather, 10)[m]
    c[m, 3] = 255
    for n in LEGS:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * 0.5)) / (w * 0.3)) ** 2 - ((YY - 462) / 4.0) ** 2) * rect_mask([n])
        c[..., :3] = np.clip(c[..., :3] + 46 * g[..., None], 0, 255)
    sole = rect_mask(LEGS) & (YY >= 478)
    c[sole, :3] = (38, 28, 22)
    shade(c, (rect_mask(LEGS) & (YY == 477)).astype(np.float32), 0.5)
    welt = rect_mask(LEGS) & (YY == 476)
    c[welt, :3] = (74, 58, 40)
    for n in FRONTS:
        x, y, w, h = R[n]
        mx = x + w / 2
        paint(c, poly([(mx - 9, SHOE_TOP), (mx + 9, SHOE_TOP), (mx + 7, 463), (mx - 7, 463)]), (14, 12, 14))
        for ly in range(SHOE_TOP + 2, 463, 3):
            paint(c, lines([(mx - 6, ly), (mx + 6, ly + 2)]) + lines([(mx + 6, ly), (mx - 6, ly + 2)]), (70, 68, 72))
        paint(c, dash([(x + 3, 469), (mx, 466), (x + w - 3, 469)], on=2, off=1), (60, 56, 58))
    shade(c, (rect_mask(LEGS) & (YY == SHOE_TOP)).astype(np.float32), 0.4)
    # sole underside
    dn = rect_mask(LEG_DOWNS)
    dd = fabric_detail(seed + 1, cloud=0.08, twill=0, grain=0.06)
    c[dn, :3] = tint(dd, (40, 32, 28), 10)[dn]
    c[dn, 3] = 255
    for n in LEG_DOWNS:
        x, y, w, h = R[n]
        paint(c, lines([(x, y + 42), (x + w, y + 42)], 2), (18, 14, 12))
    return c


def socks(c, y0, y1, col, bands=(), seed=7):
    rib_band(c, LEGS, y0, y1, col, stripes=bands, seed=seed)
    return c


def belt_shadow(c):
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(np.float32), dy=2, sigma=1.3, strength=0.5)
    return c


def trousers(name, cloth, seed, belt=(26, 20, 18), tex=None):
    c = pants_base(cloth, seed, tex=tex, belt=belt)
    belt_shadow(c)
    school_shoes(c)
    return save_hq(c, name)


def shorts(name="pants_shorts_khaki.png", cloth=(132, 122, 92), seed=61):
    c = pants_base(cloth, seed, tex=dict(cloud=0.045, twill=0.045), belt=(70, 44, 26), crease=False, leg_end=398)
    belt_shadow(c)
    # turned-up hem
    cuff = rect_mask(LEGS) & (YY >= 390) & (YY < 398)
    c[cuff, :3] = np.clip(c[cuff, :3] * 1.08, 0, 255)
    shade(c, (rect_mask(LEGS) & (YY == 390)).astype(np.float32), 0.5)
    clear(c, rect_mask(LEGS) & (YY >= 398) & (YY < 424))
    socks(c, 424, SHOE_TOP - 1, IVORY, bands=[(427, 429, CRIMSON), (431, 431, GOLD)])
    school_shoes(c)
    return save_hq(c, name)


# ---------------------------------------------------------------- skirt
def tartan(seed=0):
    crim, blk, gold, navy, cream = (136, 14, 24), (22, 16, 18), (190, 150, 62), (28, 30, 56), (220, 206, 176)
    sett = [(crim, 9), (blk, 4), (crim, 1), (gold, 1), (crim, 1), (blk, 4), (crim, 9), (navy, 3), (cream, 1), (navy, 3)]
    seq = []
    for col, n in sett + sett[::-1]:
        seq += [col] * n
    seq = np.array(seq, np.float32)
    warp = seq[XX % len(seq)]
    weft = seq[YY % len(seq)]
    twill = ((XX + YY) % 4) < 2
    col = np.where(twill[..., None], warp, weft) * 0.7 + (warp + weft) / 2 * 0.3
    d = fabric_detail(seed, cloud=0.06, twill=0.0, grain=0.03)
    return np.clip(col * d[..., None], 0, 255)


def skirt(name="pants_skirt_pleated_tartan.png", seed=71):
    c = blank((0, 0, 0), 255)
    hole = load("pants_jeans_a.png")[..., 3] == 0
    tt = tartan(seed)
    hem_y = 402
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(LEGS) & (YY < hem_y) | rect_mask(LEG_UPS) | rect_mask(["T_D"])
    c[m, :3] = tt[m]
    c[m, 3] = 255
    shade(c, rect_mask(["T_D"]).astype(np.float32), 0.55)      # inside of the skirt
    # pleats: each 8px pleat lit on one side, folded on the other
    ph = ((XX % 8) / 7.0)
    pleat = rect_mask(LEGS) & (YY < hem_y) | rect_mask(TORSO_RING) & (YY >= 190)
    fac = 0.82 + 0.32 * ph
    c[pleat, :3] = np.clip(c[pleat, :3] * fac[pleat, None], 0, 255)
    shade(c, (pleat & (XX % 8 == 0)).astype(np.float32), 0.55)
    # waistband
    wb = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 189)
    lift(c, wb.astype(np.float32), dy=2, sigma=1.3, strength=0.5)
    c[wb, :3] = tint(fabric_detail(seed + 1, cloud=0.05, twill=0.03), (24, 20, 24))[wb]
    shade(c, (wb & ((YY == 179) | (YY == 189))).astype(np.float32), 0.45)
    button(c, 392, 184, r=2.2)
    # hem with little notches at each fold
    hem = rect_mask(LEGS) & (YY >= hem_y - 3) & (YY < hem_y)
    c[hem, :3] = np.clip(c[hem, :3] * 0.85, 0, 255)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(np.float32), 0.35)
    notch = rect_mask(LEGS) & (YY == hem_y - 1) & (XX % 8 == 0)
    clear(c, notch)
    clear(c, rect_mask(LEGS) & (YY >= hem_y) & (YY < 418))
    socks(c, 418, SHOE_TOP - 1, (30, 28, 32), bands=[(421, 422, CRIMSON)])
    school_shoes(c)
    clear(c, hole)
    return save_hq(c, name)


def build():
    with supersample(4):
        return _build()


def _build():
    out = []
    out.append(denim_wash("pants_jeans_a.png", "pants_jeans_dark_indigo.png",
                          [(0, (6, 10, 22)), (0.55, (30, 44, 88)), (1.0, (120, 138, 184))], thread=(186, 140, 72)))
    out.append(denim_wash("pants_jeans_b.png", "pants_jeans_black.png",
                          [(0, (4, 4, 6)), (0.55, (36, 36, 40)), (1.0, (128, 128, 134))]))
    out.append(ripped_jeans())
    out.append(trousers("pants_slacks_charcoal.png", (52, 52, 56), 81, tex=dict(cloud=0.06, twill=0.05)))
    out.append(trousers("pants_trousers_khaki.png", KHAKI, 82, belt=(70, 44, 26), tex=dict(cloud=0.045, twill=0.045)))
    out.append(shorts())
    out.append(skirt())
    return out


if __name__ == "__main__":
    for f in build():
        print(f.name)
