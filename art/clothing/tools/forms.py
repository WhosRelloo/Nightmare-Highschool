"""Transformation outfits: one shirt + pants pair per form (Vampire, Wolf, Ghoul, Wraith)
plus Priest vestments. Names match the character attribute `Transformation`."""
import numpy as np
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import base_shirt, face_seams, hem_line
from recolors import MONO, polo_parts, vest_parts
from pants import pants_base, school_shoes


import nhcloth

NO_CREASE = {"shirt_form_wolf.png", "pants_form_wolf.png", "shirt_form_ghoul.png", "pants_form_ghoul.png"}


def save(c, name):
    """Every piece in this set goes through the quality pass before saving."""
    return nhcloth.save(finish(c, creases=name not in NO_CREASE, seed=sum(map(ord, name))), name)

INK = (8, 6, 8)
VELVET = (26, 14, 22)
SILK = (150, 16, 28)
SPECTRAL = (150, 236, 220)
VOID = (6, 4, 10)
F32 = np.float32


def all_shirt():
    return rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)


def pants_cloth_zone():
    return (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(LEGS) | rect_mask(ARM_UPS) | rect_mask(["T_D"])


# ================================================================== VAMPIRE
def vampire_shirt(name="shirt_form_vampire_noble.png", seed=401):
    vt = dict(cloud=0.08, twill=0.02, grain=0.03)
    c = base_shirt(VELVET, VELVET, seed, body_tex=vt, sleeve_tex=vt)
    sheen(c, TORSO_RING + ARM_FACES, 0.28, width=0.2)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    # tall collar: crimson silk facing, velvet outside, gold edge
    silk = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), SILK, 10)
    paint(c, (neck & (dist <= 4)).astype(F32), silk)
    paint(c, (neck & (dist > 4) & (dist <= 10)).astype(F32), tint(fabric_detail(seed + 2, cloud=0.06, twill=0), (16, 8, 14)))
    paint(c, (neck & (dist > 10) & (dist <= 11)).astype(F32), GOLD)
    # brocade waistcoat in the opening
    wc = poly([(256, 74), (333, 74), (318, 201), (271, 201)])
    paint(c, wc, tint(fabric_detail(seed + 3, cloud=0.06, twill=0.02), (104, 8, 18)))
    damask(c, wc > 0.5, 0.7)
    for by in range(128, 200, 14):
        button(c, CX, by, r=2.2)
    jabot(c, CX, 88, n=6)
    brooch(c, CX, 90)
    # a single blood drip off the lace
    paint(c, lines([(300, 114), (300, 122)], 2), (150, 8, 18))
    paint(c, shape(lambda d: d.ellipse((298, 121, 302, 126), fill=255)), (150, 8, 18))
    # crimson silk lapels with gold piping and filigree dots
    lap = [(256, 74), (266, 74), (280, 150), (271, 162), (242, 108), (250, 90)]
    for pts in (lap, [(2 * CX - x, y) for x, y in lap]):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.5, strength=0.6)
        paint(c, m, silk)
        paint(c, lines(pts + [pts[0]]), GOLD)
        paint(c, (outline_of(ndimage.binary_erosion(m > 0.5, iterations=2), 1) & ((XX + YY) % 3 == 0)).astype(F32), (214, 174, 90))
    for x0 in (271, 318):
        paint(c, lines([(x0, 162), (x0, 201)]), GOLD)
    # waist seam with two buttons at the back, gold bat on the back
    paint(c, lines([(427, 176), (554, 176)]), INK)
    for bx in (482, 500):
        button(c, bx, 176, r=2.2)
    b = bat(491, 124, 84)
    lift(c, b, dy=2, sigma=1.5, strength=0.5)
    paint(c, ndimage.binary_dilation(b > 0.5, iterations=1).astype(F32), GOLD)
    paint(c, b, (96, 6, 16))
    paint(c, (outline_of(ndimage.binary_erosion(b > 0.5, iterations=3), 1) & ((XX + YY) % 2 == 0)).astype(F32), (196, 150, 70))
    paint(c, lines([(491, 74), (491, 104)]) + lines([(491, 150), (491, 176)]), INK)
    # cuffs: crimson silk turn-backs, gold buttons, lace ruffles
    cuff = rect_mask(ARM_FACES) & (YY >= 428) & (YY <= 446)
    c[cuff, :3] = silk[cuff]
    paint(c, (rect_mask(ARM_FACES) & ((YY == 427) | (YY == 447))).astype(F32), GOLD)
    for bx in (126, 136, 449, 459):
        button(c, bx, 437, r=1.8)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for sx in range(x, x + w, 8):
            m = shape(lambda d: d.ellipse((sx - 1, 446, sx + 9, 462), fill=255)) * rect_mask([n]) * (YY <= SLEEVE_END) * (YY >= 448)
            paint(c, m, (236, 230, 216))
            paint(c, shape(lambda d: d.arc((sx - 1, 446, sx + 9, 462), 20, 160, fill=255)) * rect_mask([n]), (140, 132, 120))
    clear(c, hole)
    face_seams(c, 0.5)
    return save(c, name)


def vampire_pants(name="pants_form_vampire_noble.png", seed=411):
    c = pants_base((20, 16, 20), seed, tex=dict(cloud=0.06, twill=0.04), belt=None, crease=True, leg_end=412)
    wb = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 188)
    c[wb, :3] = np.clip(c[wb, :3] * 0.8, 0, 255)
    for bx in (262, 327, 470, 512):
        button(c, bx, 184, r=1.8)
    for n in OUTERS:
        x, y, w, h = R[n]
        mx = x + w // 2
        s = rect_mask([n]) & (np.abs(XX - mx) <= 2) & (YY < 412)
        c[s, :3] = SILK
        paint(c, (rect_mask([n]) & (np.abs(XX - mx) == 3) & (YY < 412)).astype(F32), GOLD)
    # frock-coat tails over the backs of the legs
    vel = tint(fabric_detail(seed + 1, cloud=0.08, twill=0.02), VELVET)
    for n, inner_right in (("RA_B", False), ("LA_B", True)):
        x, y, w, h = R[n]
        if inner_right:
            pts = [(x, y), (x + w, y), (x + w - 6, y + 58), (x + 10, y + 70), (x, y + 64)]
        else:
            pts = [(x, y), (x + w, y), (x + w, y + 64), (x + w - 10, y + 70), (x + 6, y + 58)]
        m = poly(pts)
        lift(c, m, dy=2, sigma=1.5, strength=0.5)
        paint(c, m, vel)
        paint(c, lines(pts + [pts[0]]), GOLD)
        edge_x = x + w - 1 if inner_right is False else x
        paint(c, (rect_mask([n]) & (np.abs(XX - (x + w - 2 if not inner_right else x + 1)) <= 1) & (YY < y + 62)).astype(F32), SILK)
    for n in ("RA_R", "LA_L"):
        x, y, w, h = R[n]
        m = poly([(x, y), (x + w, y), (x + w, y + 30), (x, y + 40)] if n == "RA_R" else [(x, y), (x + w, y), (x + w, y + 40), (x, y + 30)])
        paint(c, m, vel)
        paint(c, lines([(x, y + (40 if n == "RA_R" else 30)), (x + w, y + (30 if n == "RA_R" else 40))]), GOLD)
    riding_boots(c, 412, cuff=(110, 10, 20))
    return save(c, name)


# ================================================================== WOLF
def wolf_fur(seed):
    return fur((30, 26, 26), (150, 134, 114), seed, angle=90, mottle=1.0)


def wolf_shirt(name="shirt_form_wolf.png", seed=501):
    c = blank()
    coat = wolf_fur(seed)
    chest = fur((80, 70, 60), (214, 200, 174), seed + 1, angle=96, length=(6, 11), mottle=0.8)
    m = all_shirt()
    c[m, :3] = coat[m]
    c[m, 3] = 255
    shade(c, (rect_mask(ARM_FACES) & (YY >= 462)).astype(F32), 0.7)
    hole, _ = polo_hole()
    pp = polo_parts()
    shirt = tint(fabric_detail(seed + 2, cloud=0.1, twill=0.03), (198, 190, 174))
    s_edge = ragged_y(386, 6, seed, notches=0.09, depth=(6, 16))
    t_edge = ragged_y(172, 7, seed + 1, notches=0.12, depth=(8, 22))
    sm = (rect_mask(TORSO_RING) & (YY <= t_edge[XX])) | rect_mask(["T_UP"]) | rect_mask(ARM_UPS) | \
         (rect_mask(ARM_FACES) & (YY <= s_edge[XX]))
    wob = 3 * noise(H, W, seed + 4, 2)
    open_c = rect_mask(["T_F"]) & (YY > 84) & (np.abs(XX - CX - 2 * np.sin(YY / 6)) < 9 + (YY - 74) * 0.42 + wob)
    slash = np.zeros((H, W), bool)
    for k in range(3):
        x0 = 452 + k * 15
        pts = [(x0, 92), (x0 + 6, 92), (x0 + 38, 176), (x0 + 30, 178)]
        slash |= (poly(pts) > 0.5) & (noise(H, W, seed + 10 + k, 1.2) > -1.2)
    side = (poly([(372, 120), (378, 118), (410, 160), (404, 163)]) > 0.5)
    sm &= ~open_c & ~slash & ~side & ~blob_holes(rect_mask(TORSO_RING + ARM_FACES), seed + 6, thresh=1.6, sigma=4)
    lift(c, sm.astype(F32), dy=2, sigma=1.6, strength=0.55)
    c[sm, :3] = shirt[sm]
    c[open_c, :3] = chest[open_c]
    collar = pp["grey"] & (YY <= 104) & rect_mask(["T_UP", "T_F"]) & ~((XX >= 283) & (XX <= 306) & (YY >= 84))
    paint(c, (collar & ~open_c).astype(F32), (232, 228, 218))
    shade(c, outline_of(collar & ~open_c, 1).astype(F32), 0.4)
    dist = ndimage.distance_transform_edt(~hole)
    mane = rect_mask(["T_UP", "T_F"]) & (dist <= 7)
    c[mane, :3] = chest[mane]
    edge = outline_of(sm, 1)
    shade(c, edge.astype(F32), 0.45)
    rng = np.random.default_rng(seed)
    fray = ndimage.binary_dilation(edge, iterations=2) & ~sm & all_shirt() & (rng.random((H, W)) < 0.18)
    c[fray, :3] = (236, 232, 222)
    # grime, sweat and blood on what's left of the shirt
    scuffs(c, sm, seed + 7, amount=0.45, color=(70, 56, 40), blobs=26, spread=5)
    spat = (noise(H, W, seed + 8, 0.9) > 2.3) & sm & (np.hypot(XX - 300, YY - 110) < 40)
    c[ndimage.binary_dilation(spat, iterations=1), :3] = (110, 8, 16)
    # torn crimson tie hanging loose, blood-flecked scratches
    knot = poly([(308, 92), (316, 94), (314, 101), (307, 100)])
    blade = poly([(307, 100), (314, 101), (322, 120), (318, 126), (321, 130), (313, 128), (309, 124)])
    tie = np.clip(knot + blade, 0, 1)
    lift(c, tie, dx=2, dy=1, sigma=1.3, strength=0.55)
    paint(c, tie, tint(fabric_detail(seed + 5, cloud=0.05, twill=0), CRIMSON))
    shade(c, outline_of(tie > 0.5, 1).astype(F32), 0.35)
    for k in range(3):
        paint(c, lines([(246 + k * 5, 150), (256 + k * 5, 172)]), (120, 8, 16), 0.85)
    claws(c, ["RA_F", "LA_F", "RA_R", "LA_L", "RA_L", "LA_R"], 482, n=4, length=9)
    clear(c, hole)
    face_seams(c, 0.7)
    return save(c, name)


def paw_pads(c, names):
    for n in names:
        x, y, w, h = R[n]
        pad = shape(lambda d: d.ellipse((x + 16, y + 30, x + 48, y + 54), fill=255))
        paint(c, pad, (34, 26, 26))
        for tx in (x + 8, x + 21, x + 34, x + 47):
            paint(c, shape(lambda d: d.ellipse((tx, y + 10, tx + 10, y + 24), fill=255)), (34, 26, 26))
            paint(c, poly([(tx + 3, y + 10), (tx + 7, y + 10), (tx + 5, y + 3)]), (214, 204, 180))


def wolf_pants(name="pants_form_wolf.png", seed=511):
    c, hole = pants_shell()
    coat = wolf_fur(seed)
    z = pants_cloth_zone() | rect_mask(ARM_DOWNS)
    c[z, :3] = coat[z]
    c[z, 3] = 255
    cloth = tint(fabric_detail(seed + 1, cloud=0.07, twill=0.05), (44, 44, 48))
    edge = ragged_y(410, 9, seed, notches=0.1, depth=(6, 18))
    tm = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(["T_D"]) | rect_mask(ARM_UPS) | (rect_mask(LEGS) & (YY <= edge[XX]))
    tm &= ~blob_holes(rect_mask(LEGS), seed + 2, thresh=1.55, sigma=4)
    c[tm, :3] = cloth[tm]
    e = outline_of(tm, 1)
    shade(c, e.astype(F32), 0.45)
    rng = np.random.default_rng(seed)
    fray = ndimage.binary_dilation(e, iterations=2) & ~tm & rect_mask(LEGS) & (rng.random((H, W)) < 0.15)
    c[fray, :3] = (90, 90, 96)
    belt = rect_mask(TORSO_RING) & (YY >= 181) & (YY <= 188) & ~((XX >= 398) & (XX <= 404))
    c[belt, :3] = (26, 20, 18)
    shade(c, outline_of(belt, 1).astype(F32), 0.5)
    paint(c, shape(lambda d: d.rectangle((287, 180, 302, 189), outline=255)), GOLD)
    shade(c, (rect_mask(LEGS) & (YY >= 460)).astype(F32), 0.65)
    claws(c, FRONTS + OUTERS, 482, n=3, length=8)
    paw_pads(c, ARM_DOWNS)
    clear(c, hole)
    return save(c, name)


# ================================================================== GHOUL
def ghoul_skin(seed, base=(124, 134, 110)):
    s = tint(fabric_detail(seed, cloud=0.14, twill=0.0, grain=0.05), base)
    br = np.clip(noise(H, W, seed + 5, 7) - 0.7, 0, 1)[..., None] * 0.6
    s = s * (1 - br) + np.array((84, 70, 96), F32) * br
    v = np.abs(noise(H, W, seed + 6, 2.2))
    vm = ((v < 0.08) & (noise(H, W, seed + 7, 8) > 0.1)).astype(F32)[..., None] * 0.7
    s = s * (1 - vm) + np.array((60, 74, 60), F32) * vm
    return np.clip(s, 0, 255)


def rot_edges(c, gm, seed, fray_col=(150, 140, 116)):
    e = outline_of(gm, 1)   # torn edges inside a face only (outline_of skips face edges)
    shade(c, e.astype(F32), 0.4)
    rng = np.random.default_rng(seed)
    f = ndimage.binary_dilation(e, iterations=2) & ~gm & (c[..., 3] > 0) & (rng.random((H, W)) < 0.14)
    c[f, :3] = fray_col
    return c


def ghoul_shirt(name="shirt_form_ghoul.png", seed=601):
    p = vest_parts()
    src = p["src"]
    g = recolor(src.copy(), p["vest"], (62, 24, 26), 8)
    g[p["sleeves"], :3] = recolor(src, p["sleeves"], (126, 120, 100), 8)[p["sleeves"], :3]
    g[p["vee"], :3] = recolor(src, p["vee"], (140, 132, 112), 8)[p["vee"], :3]
    tm = p["neck"] | p["hem"] | p["arm"]
    g[tm, :3] = recolor(src, tm, (84, 72, 44), 6)[tm, :3]
    MONO.paste(g, p["mono_c"][0], p["mono_c"][1], fill=(150, 140, 110), edge=(80, 70, 40))
    scuffs(g, g[..., 3] > 0, seed, amount=0.55, color=(52, 42, 28), blobs=34, spread=5)
    c = blank()
    skin = ghoul_skin(seed)
    m = all_shirt()
    c[m, :3] = skin[m]
    c[m, 3] = 255
    s_edge = ragged_y(406, 7, seed, notches=0.1, depth=(6, 16))
    holes = blob_holes(rect_mask(TORSO_RING + ARM_FACES), seed + 1, thresh=1.3, sigma=4)
    rib = (XX - 330) ** 2 / 20.0 ** 2 + (YY - 161) ** 2 / 21.0 ** 2 < 1 + 0.25 * noise(H, W, seed + 2, 1.5)
    gm = (g[..., 3] > 0) & ~holes & ~(rect_mask(ARM_FACES) & (YY > s_edge[XX])) & ~rib
    lift(c, gm.astype(F32), dy=1, sigma=1.3, strength=0.45)
    c[gm, :3] = g[gm, :3]
    rot_edges(c, gm, seed)
    # opened ribcage
    cav = rib & rect_mask(["T_F"])
    depth = np.clip(((XX - 330) ** 2 / 20.0 ** 2 + (YY - 161) ** 2 / 21.0 ** 2), 0, 1)
    c[cav, :3] = (np.array((14, 2, 4), F32) * (1 - depth[..., None]) + np.array((60, 10, 14), F32) * depth[..., None])[cav]
    for k, ry in enumerate((147, 155, 163, 171, 179)):
        arc = shape(lambda d: d.arc((306, ry - 5, 356, ry + 9), 200, 340, fill=255, width=1)) * cav
        paint(c, np.roll(arc, 1, 0) * cav, (40, 30, 24))
        paint(c, arc, (186, 174, 144))
    paint(c, lines([(312, 140), (312, 184)], 2) * cav, (170, 160, 132))
    flesh = ndimage.binary_dilation(cav, iterations=2) & ~cav & (c[..., 3] > 0)
    c[flesh, :3] = (104, 28, 30)
    glow(c, cav.astype(F32) * 0.4, (70, 140, 50), sigma=3, strength=0.12, core=False)
    shade(c, outline_of(cav, 1).astype(F32), 0.3)
    # stitched wounds, bony hands, moss
    stitches(c, [(232, 432), (250, 440), (268, 436)])
    stitches(c, [(176, 104), (190, 126), (186, 146)])
    stitches(c, [(468, 150), (486, 140), (506, 150)])
    shade(c, (rect_mask(ARM_FACES) & (YY >= 464)).astype(F32), 0.75)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for kx in range(x + 8, x + w - 4, 12):
            paint(c, shape(lambda d: d.ellipse((kx - 2, 468, kx + 2, 472), fill=255)), (200, 194, 168))
            paint(c, lines([(kx, 479), (kx, 482)], 2), (36, 28, 24))
    moss = (noise(H, W, seed + 9, 1.3) > 2.0) & (YY > 150) & (c[..., 3] > 0) & rect_mask(TORSO_RING)
    moss = ndimage.binary_dilation(moss, iterations=1)
    c[moss, :3] = (46, 66, 32)
    hole = hole_mask(load("shirt_maroon_vest_grey.png"))
    clear(c, hole)
    return save(c, name)


def ghoul_pants(name="pants_form_ghoul.png", seed=611):
    c, hole = pants_shell()
    skin = ghoul_skin(seed)
    z = pants_cloth_zone()
    c[z, :3] = skin[z]
    c[z, 3] = 255
    cloth = tint(fabric_detail(seed + 1, cloud=0.12, twill=0.04), (58, 54, 54))
    edge = ragged_y(430, 9, seed, notches=0.12, depth=(8, 20))
    tm = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(["T_D"]) | rect_mask(ARM_UPS) | (rect_mask(LEGS) & (YY <= edge[XX]))
    tm &= ~blob_holes(rect_mask(LEGS), seed + 2, thresh=1.35, sigma=4)
    c[tm, :3] = cloth[tm]
    scuffs(c, tm, seed, amount=0.55, color=(48, 38, 24), blobs=30, spread=5)
    rot_edges(c, tm, seed, fray_col=(110, 104, 96))
    # rope belt
    rope = rect_mask(TORSO_RING) & (YY >= 181) & (YY <= 187)
    c[rope, :3] = np.where(((XX + YY) % 4 < 2)[rope][:, None], (122, 102, 70), (84, 68, 44))
    shade(c, outline_of(rope, 1).astype(F32), 0.5)
    paint(c, shape(lambda d: d.ellipse((296, 180, 306, 190), fill=255)), (110, 92, 62))
    paint(c, lines([(298, 189), (295, 201)], 2) + lines([(304, 189), (308, 200)], 2), (110, 92, 62))
    # grave dirt toward the feet
    for n in LEGS:
        x, y, w, h = R[n]
        grad = np.clip((YY - 430) / 50.0, 0, 1) * rect_mask([n])
        c[..., :3] = c[..., :3] * (1 - 0.45 * grad[..., None]) + np.array((40, 30, 20), F32) * 0.45 * grad[..., None]
    stitches(c, [(100, 446), (118, 452), (134, 446)])
    # bony bare feet
    for n in FRONTS:
        x, y, w, h = R[n]
        for i in range(5):
            tx = x + 6 + i * 11.5
            t = shape(lambda d: d.ellipse((tx, 470, tx + 10, 482), fill=255))
            shade(c, outline_of(t > 0.5, 1).astype(F32), 0.45)
            paint(c, shape(lambda d: d.rectangle((tx + 3, 477, tx + 7, 481), fill=255)), (40, 32, 26))
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = skin[dn] * 0.55
    c[dn, 3] = 255
    clear(c, hole)
    return save(c, name)


# ================================================================== WRAITH
def robe_tex(seed):
    r = tint(fabric_detail(seed, cloud=0.12, twill=0.02, grain=0.04), (22, 20, 30))
    fold = 1 + 0.14 * np.sin(2 * np.pi * XX / 9 + 1.5 * noise(H, W, seed + 1, 6))
    strip = np.where(((XX // 7) % 3) == 0, 0.78, 1.0)
    return np.clip(r * (fold * strip)[..., None], 0, 255)


def wisps(c, zone, seed, top, length=24, n_per=6):
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), F32)
    ys, xs = np.nonzero(zone)
    if len(xs) == 0:
        return c
    for _ in range(int(len(np.unique(xs)) / 64 * n_per) + 4):
        x = rng.choice(xs)
        y0 = rng.integers(top - 2, top + 6)
        L = rng.integers(length // 2, length)
        for k in range(L):
            yy = y0 + k
            if 0 <= yy < H:
                m[yy, int(x + 2 * np.sin(k / 4 + x))] = 1 - k / L
    m = ndimage.gaussian_filter(m, 0.8) * zone
    m = m / (m.max() + 1e-6)
    c[..., :3] = np.clip(c[..., :3] + np.array(SPECTRAL, F32) * 0.85 * m[..., None], 0, 255)
    return c


def sigil(cx, cy, r):
    def fn(d):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255)
        d.ellipse((cx - r * 0.74, cy - r * 0.74, cx + r * 0.74, cy + r * 0.74), outline=255)
        pts = [(cx + r * 0.72 * np.sin(a), cy + r * 0.72 * np.cos(a)) for a in np.deg2rad([180, 300, 60])]
        d.polygon(pts, outline=255)
        for a in np.deg2rad(np.arange(0, 360, 45)):
            x0, y0 = cx + r * 1.1 * np.sin(a), cy + r * 1.1 * np.cos(a)
            x1, y1 = cx + r * 1.32 * np.sin(a), cy + r * 1.32 * np.cos(a)
            d.line([(x0, y0), (x1, y1)], fill=255)
        d.ellipse((cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5), fill=255)
    return shape(fn)


def wraith_shirt(name="shirt_form_wraith.png", seed=701):
    c = blank()
    robe = robe_tex(seed)
    m = all_shirt()
    c[m, :3] = robe[m]
    c[m, 3] = 255
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    hood = neck & (dist <= 7)
    f = np.clip(dist / 7.0, 0.08, 1)
    c[hood, :3] = c[hood, :3] * f[hood, None]
    rim = neck & (dist > 7) & (dist <= 9)
    c[rim, :3] = np.clip(c[rim, :3] * 1.4, 0, 255)
    runes = neck & (dist > 9.2) & (dist <= 10.4) & ((np.arctan2(YY - 50, XX - CX) * 12).astype(int) % 3 == 0)
    peak = poly([(456, 74), (526, 74), (491, 124)])
    c[peak > 0.5, :3] = np.clip(c[peak > 0.5, :3] * 1.18, 0, 255)
    shade(c, outline_of(peak > 0.5, 1).astype(F32), 0.35)
    # sleeves dissolve into void and mist
    edge = ragged_y(462, 7, seed, notches=0.16, depth=(6, 18))
    below = rect_mask(ARM_FACES) & (YY > edge[XX])
    c[below, :3] = VOID
    wisps(c, below, seed, 462, length=20, n_per=8)
    hems = rect_mask(ARM_FACES) & (np.abs(YY - edge[XX]) < 1.0)
    # sigil, chains and rune bands
    sg = sigil(CX, 132, 15)
    glow(c, sg, SPECTRAL, sigma=3, strength=0.9)
    glow(c, runes.astype(F32), SPECTRAL, sigma=2, strength=0.5)
    glow(c, hems.astype(F32), SPECTRAL, sigma=3.5, strength=0.35, core=False)
    band = (rect_mask(ARM_FACES) & (YY == 440) & ((XX % 4) != 0)).astype(F32)
    glow(c, band, SPECTRAL, sigma=1.5, strength=0.5)
    dim = (96, 150, 146)
    chain(c, [(231, 160), (262, 176), (CX, 184), (327, 176), (358, 160)], dim)
    chain(c, [(165, 168), (228, 160)], dim)
    chain(c, [(361, 160), (424, 168)], dim)
    chain(c, [(427, 168), (491, 188), (554, 168)], dim)
    sig2 = sigil(491, 148, 22)
    glow(c, sig2 * 0.8, SPECTRAL, sigma=4, strength=0.7)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def wraith_pants(name="pants_form_wraith.png", seed=711):
    c, hole = pants_shell()
    robe = robe_tex(seed)
    z = pants_cloth_zone()
    c[z, :3] = robe[z]
    c[z, 3] = 255
    edge = ragged_y(444, 10, seed, notches=0.2, depth=(8, 24))
    below = rect_mask(LEGS) & (YY > edge[XX])
    c[below, :3] = VOID
    wisps(c, below, seed, 446, length=30, n_per=10)
    glow(c, (rect_mask(LEGS) & (np.abs(YY - edge[XX]) < 1.0)).astype(F32), SPECTRAL, sigma=3.5, strength=0.35, core=False)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = VOID
    for n in ARM_DOWNS:
        x, y, w, h = R[n]
        g = np.exp(-(((XX - x - w / 2) ** 2 + (YY - y - h / 2) ** 2) / 300.0)) * rect_mask([n])
        c[..., :3] = np.clip(c[..., :3] + np.array(SPECTRAL, F32) * 0.35 * g[..., None], 0, 255)
    cord = rect_mask(TORSO_RING) & (YY >= 182) & (YY <= 185)
    c[cord, :3] = (88, 96, 104)
    knot = shape(lambda d: d.ellipse((297, 180, 305, 188), fill=255))
    glow(c, knot, SPECTRAL, sigma=2, strength=0.6)
    glow(c, lines([(299, 188), (296, 201)]) + lines([(303, 188), (306, 200)]), SPECTRAL, sigma=1.5, strength=0.4)
    for n in FRONTS:
        x, y, w, h = R[n]
        glow(c, sigil(x + w / 2, 396, 9) * 0.6, SPECTRAL, sigma=2, strength=0.45)
    clear(c, hole)
    return save(c, name)


# ================================================================== PRIEST
def stole(c, x0, x1, y0, y1, step=22, start=None):
    m = (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1) & (c[..., 3] > 0)
    lift(c, m.astype(F32), dx=1, dy=1, sigma=1.4, strength=0.5)
    c[m, :3] = tint(fabric_detail(9, cloud=0.04, twill=0.02), (234, 226, 206))[m]
    paint(c, (m & ((XX == x0) | (XX == x1))).astype(F32), GOLD)
    paint(c, (m & ((XX == x0 + 1) | (XX == x1 - 1))).astype(F32), (150, 112, 44))
    cx = (x0 + x1) / 2
    for cy in range(int(start or y0 + 12), y1 - 6, step):
        cross(c, cx, cy, 7, 11, 2.2)
    return c


def priest_shirt(name="shirt_form_priest_vestments.png", seed=801):
    ct = dict(cloud=0.07, twill=0.04)
    c = base_shirt((20, 18, 22), (20, 18, 22), seed, body_tex=ct, sleeve_tex=ct)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 4)).astype(F32), (12, 10, 12))
    paint(c, shape(lambda d: d.rectangle((290, 84, 299, 90), fill=255)), (242, 240, 234))
    paint(c, lines([(CX, 92), (CX, 201)]), (110, 10, 20))
    for by in range(94, 200, 7):
        paint(c, shape(lambda d: d.ellipse((CX - 1.5, by - 1.5, CX + 1.5, by + 1.5), fill=255)), (150, 16, 28))
    stole(c, 260, 272, 74, 201)
    stole(c, 317, 329, 74, 201)
    stole(c, 260, 272, 8, 71, start=999)
    stole(c, 317, 329, 8, 71, start=999)
    # pectoral cross on a chain
    chain(c, [(276, 90), (CX, 116)], GOLD, step=2.6)
    chain(c, [(313, 90), (CX, 116)], GOLD, step=2.6)
    cross(c, CX, 128, 12, 20, 3.2)
    brooch(c, CX, 124)
    # back: radiant gold cross with a soft holy glow
    rays = shape(lambda d: [d.line([(491, 132), (491 + 46 * np.cos(a), 132 + 46 * np.sin(a))], fill=255)
                            for a in np.deg2rad(np.arange(0, 360, 15))])
    rays *= (np.hypot(XX - 491, YY - 132) > 18)
    paint(c, rays * rect_mask(["T_B"]), (150, 112, 44), 0.8)
    big = np.zeros((H, W), F32)
    cross(c, 491, 138, 38, 64, 9, fill=(234, 226, 206))
    glow(c, shape(lambda d: d.ellipse((471, 108, 511, 148), fill=255)) * 0.5, (200, 160, 70), sigma=8, strength=0.35, core=False)
    # wide cuffs: ivory band, gold edges, crimson piping
    cuff = rect_mask(ARM_FACES) & (YY >= 440) & (YY <= 452)
    c[cuff, :3] = tint(fabric_detail(seed + 2, cloud=0.04), (234, 226, 206))[cuff]
    paint(c, (rect_mask(ARM_FACES) & ((YY == 439) | (YY == 453))).astype(F32), GOLD)
    paint(c, (rect_mask(ARM_FACES) & (YY == 454)).astype(F32), (150, 16, 28))
    for n in ARM_FACES:
        x, y, w, h = R[n]
        cross(c, x + w / 2, 446, 6, 9, 2)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def priest_pants(name="pants_form_priest_cassock.png", seed=811):
    c = pants_base((20, 18, 22), seed, tex=dict(cloud=0.07, twill=0.04), belt=None, crease=False, leg_end=451, fly=False)
    sash = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 192)
    c[sash, :3] = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), (150, 16, 28), 10)[sash]
    sheen(c, TORSO_RING, 0.2)
    shade(c, (rect_mask(TORSO_RING) & ((YY == 179) | (YY == 192))).astype(F32), 0.4)
    # sash ends hanging down the left side and leg, with gold fringe
    for n, y0, y1 in (("T_L", 179, 201), ("LA_L", 355, 404)):
        x, y, w, h = R[n]
        m = rect_mask([n]) & (XX >= x + 20) & (XX <= x + 40) & (YY >= y0) & (YY <= y1)
        c[m, :3] = tint(fabric_detail(seed + 2, cloud=0.05, twill=0), (150, 16, 28), 10)[m]
        shade(c, outline_of(m, 1).astype(F32), 0.5)
    x, y, w, h = R["LA_L"]
    fr = (XX >= x + 20) & (XX <= x + 40) & (YY > 404) & (YY <= 412) & (XX % 2 == 0)
    c[fr, :3] = GOLD
    # stole ends over the front of each leg
    for n, sx in (("RA_F", 236), ("LA_F", 340)):
        stole(c, sx, sx + 12, 355, 428, step=30, start=410)
        fr = (XX >= sx) & (XX <= sx + 12) & (YY > 428) & (YY <= 436) & (XX % 2 == 0)
        c[fr, :3] = GOLD
    # cassock buttons down the opening between the legs, gold hem band
    for n, bx in (("RA_F", 277), ("LA_F", 311)):
        for by in range(358, 448, 7):
            paint(c, shape(lambda d: d.ellipse((bx - 1.5, by - 1.5, bx + 1.5, by + 1.5), fill=255)), (150, 16, 28))
    band = rect_mask(LEGS) & (YY >= 442) & (YY <= 447)
    c[band, :3] = GOLD
    shade(c, (rect_mask(LEGS) & ((YY == 441) | (YY == 448))).astype(F32), 0.5)
    school_shoes(c)
    return save(c, name)


PAIRS = [
    (vampire_shirt, vampire_pants),
    (wolf_shirt, wolf_pants),
    (ghoul_shirt, ghoul_pants),
    (wraith_shirt, wraith_pants),
    (priest_shirt, priest_pants),
]


def build():
    out = []
    with nhcloth.supersample(4):
        for s, p in PAIRS:
            out += [s(), p()]
    return out


if __name__ == "__main__":
    for f in build():
        print(f.name)
