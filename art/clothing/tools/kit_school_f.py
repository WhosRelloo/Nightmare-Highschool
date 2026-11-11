"""Schoolgirl kit (1.71): 12 tops + 10 bottoms for the Female bodies, in the school's crimson, black and brass.
    python art/clothing/tools/kit_school_f.py
Writes variants/kits/*.png (585x559, seam-bled; see kit_common for the clean-edge rules)."""
import numpy as np

from kit_common import *  # noqa: F401,F403
from kit_common import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS, F32
from kit_preview import (girls_blazer, charcoal_pleats, vigil_vest, vigil_skirt, mourning_pinafore,
                         pinafore_skirt_stockings, vigil_tartan)
from pants import tartan
import nhcloth

NAVY_K = (24, 30, 60)
FOREST_K = (26, 54, 38)
CREAM_K = (222, 208, 176)
INK_BLUE = (30, 36, 78)


def knit_plain(seed, col):
    """Fine knit: ribs laid out per face (never a dark rib on a face's first or last column)."""
    d = fabric_detail(seed, cloud=0.035, twill=0.0, grain=0.03)
    ph = face_phase(TORSO_RING + ARM_FACES + ["T_UP"] + ARM_UPS)
    w = np.full((H, W), 64)
    for n in TORSO_RING + ["T_UP"]:
        w[rect_mask([n])] = R[n][2]
    rib = (ph >= 1) & (ph % 2 == 1) & (ph < w - 1)
    d = d * (1 - 0.07 * rib)
    k = tint(d, col)
    return np.clip(k * (1 - 0.05 * ((YY % 3) == 0))[..., None], 0, 255)


# ------------------------------------------------------------------ generic pieces
def sweater_vest(name, yarn, trim, seed, ribbon=(150, 16, 28), blouse=IVORY_B, cable=False, crest_field=None):
    """Sweater vest over a long-sleeved blouse with a rounded collar and a ribbon bow."""
    c = base_shirt(blouse, blouse, seed, body_tex=BLOUSE_TEX, sleeve_tex=BLOUSE_TEX)
    hole, dist = neck_dist()
    k = cable_knit2(seed + 1, yarn)[0] if cable else knit_plain(seed + 1, yarn)
    vee = poly([(258, 74), (331, 74), (CX, 146)]) * rect_mask(["T_F"])
    vm = rect_mask(TORSO_RING + ["T_UP"]) & ~(vee > 0.5) & ~(rect_mask(["T_R", "T_L"]) & (YY < 88))
    lift(c, vm.astype(F32), dy=1, sigma=1.3, strength=0.35)
    c[vm, :3] = k[vm]
    ribv = np.clip(lines([(258, 74), (CX, 146), (331, 74)], 5) * rect_mask(["T_F"]), 0, 1)
    paint(c, ribv, knit_plain(seed + 2, dark(yarn, 0.85)))
    paint(c, np.clip(lines([(261, 74), (CX, 141), (328, 74)], 1) * rect_mask(["T_F"]), 0, 1), trim)
    for n in ("T_R", "T_L"):
        rb = rect_mask([n]) & (YY >= 86) & (YY <= 90)
        c[rb, :3] = knit_plain(seed + 3, dark(yarn, 0.85))[rb]
    peter_pan_collar(c, dist, blouse, seed=seed + 4)
    bow(c, CX, 102, w=10, h=5, col=ribbon, tails=18, seed=seed + 5)
    crest(c, 340, 124, w=16, h=20, field=crest_field or dark(yarn, 0.8), border=trim)
    rib_band(c, TORSO_RING, 186, 201, dark(yarn, 0.88), stripes=[(190, 190, trim)], seed=seed + 6)
    blouse_cuffs(c, blouse, 452, seed + 7)
    paint(c, (rect_mask(ARM_FACES) & (YY == 451)).astype(F32), dark(blouse, 0.75), 0.6)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def sheer_tights(c, y0, y1, col=(20, 18, 24), alpha=200, seed=0):
    m = rect_mask(LEGS) & (YY >= y0) & (YY < y1)
    t = fabric(seed, col, cloud=0.03, twill=0.0, grain=0.015)
    c[m, :3] = t[m]
    ph = face_phase(LEGS)
    # denser at the sides of each leg (sheer fabric reads darker where it wraps)
    side = np.abs((ph - 31.5) / 32.0)
    c[m, 3] = np.clip(alpha + 40 * side[m] ** 2, 0, 255)
    sheen(c, LEGS, 0.18, at=0.45, width=0.25, y_max=y1)
    return c


def pleat_skirt(name, tex, seed, hem_y=404, waist=JET, hem=(), leg=("socks", 416, JET, ()), shoes="mj", period=8):
    c, hole = skirt_shell(tex, hem_y, seed)
    pleats(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190)), period=period)
    waistband(c, waist, seed + 1)
    brass_button(c, 392, 184, r=2.0)
    for yy, col in hem:
        paint(c, (rect_mask(LEGS) & (YY == yy)).astype(F32), col)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    hem_notches(c, hem_y, period)
    kind = leg[0]
    if kind == "socks":
        _, top, col, bands = leg
        bare_legs(c, hem_y, top)
        knee_socks(c, top, col, bands=bands, seed=seed + 2)
    elif kind == "tights":
        tights(c, hem_y, SHOE_TOP, col=leg[1], seed=seed + 2)
    elif kind == "sheer":
        sheer_tights(c, hem_y, SHOE_TOP, col=leg[1], alpha=leg[2], seed=seed + 2)
    if shoes == "mj":
        mary_janes(c)
    elif shoes == "platform":
        mary_janes(c, platform=True)
    elif shoes == "boots":
        combat_boots(c, 440, seed + 3, leather=(20, 18, 20), laces=(20, 18, 20), sole_top=474)
    clear(c, hole)
    return save(c, name)


# ------------------------------------------------------------------ tops
def navy_vest():
    return sweater_vest("shirt_fs_navy_vest.png", NAVY_K, BRASS, 3401, crest_field=NH_CRIMSON)


def forest_vest():
    return sweater_vest("shirt_fs_forest_vest.png", FOREST_K, CREAM_K, 3411, ribbon=(20, 18, 22), crest_field=FOREST_K)


def crimson_court_blazer():
    return girls_blazer("shirt_fs_crimson_court_blazer.png", body=NH_CRIMSON, piping=(14, 12, 14), ribbon=(18, 14, 18),
                        seed=3421, lapel=(18, 14, 18), crest_field=(18, 14, 18))


def cropped_cardigan(name="shirt_fs_cropped_cardigan.png", knit=(58, 56, 62), blouse=IVORY_B, seed=3431):
    c = base_shirt(blouse, knit, seed, body_tex=BLOUSE_TEX, sleeve_tex=dict(cloud=0.03, twill=0.0, grain=0.03))
    hole, dist = neck_dist()
    k = knit_plain(seed + 1, knit)
    crop = 172
    cm = (rect_mask(TORSO_RING + ["T_UP"]) & (YY <= crop)) | rect_mask(ARM_FACES + ARM_UPS)
    open_v = poly([(262, 74), (327, 74), (CX + 4, crop + 1), (CX - 4, crop + 1)]) * rect_mask(["T_F"])
    cm &= ~(open_v > 0.5)
    cm &= ~(rect_mask(ARM_FACES) & (YY > SLEEVE_END))
    lift(c, cm.astype(F32), dy=2, sigma=1.4, strength=0.45)
    c[cm, :3] = k[cm]
    # button band and trim
    band = np.clip(lines([(262, 74), (CX - 3, crop)], 3) + lines([(327, 74), (CX + 3, crop)], 3), 0, 1) * rect_mask(["T_F"])
    paint(c, band, knit_plain(seed + 2, dark(knit, 0.8)))
    for by in (138, 154, 168):
        t = (by - 74) / (crop - 74)
        brass_button(c, 262 + (CX - 3 - 262) * t + 1, by, r=1.7)
    rib_band(c, TORSO_RING, crop - 8, crop, dark(knit, 0.85), stripes=[(crop - 5, crop - 5, NH_CRIMSON)], seed=seed + 3)
    # blouse below the cardigan: soft tuck folds
    soft_folds(c, rect_mask(TORSO_RING) & (YY > crop), period=12, amp=0.06, seed=seed)
    peter_pan_collar(c, dist, blouse, seed=seed + 4)
    bow(c, CX, 101, w=12, h=6, col=(150, 16, 28), tails=14, seed=seed + 5)
    crest(c, 340, 122, w=16, h=20, field=NH_CRIMSON, border=BRASS)
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(knit, 0.85), stripes=[(449, 449, NH_CRIMSON)], seed=seed + 6)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def choir_capelet(name="shirt_fs_choir_capelet.png", blouse=IVORY_B, cape=(20, 18, 22), seed=3441):
    c = base_shirt(blouse, blouse, seed, body_tex=BLOUSE_TEX, sleeve_tex=BLOUSE_TEX)
    hole, dist = neck_dist()
    # high ruffled collar
    ring = rect_mask(["T_UP", "T_F"]) & (dist <= 6)
    paint(c, ring.astype(F32), LACE)
    paint(c, (rect_mask(["T_F"]) & (dist > 6) & (dist <= 8) & (((XX // 3) % 2) == 0)).astype(F32), LACE_EDGE)
    # capelet: falls to y 138 at the front and sides, a little longer at the back, scalloped crimson hem
    edge_f = 136 + 4 * np.cos((XX - CX) / 64 * np.pi)
    cm = (rect_mask(["T_F"]) & (YY <= edge_f) & (dist > 8)) | (rect_mask(["T_R", "T_L"]) & (YY <= 138)) | \
         (rect_mask(["T_B"]) & (YY <= 144)) | (rect_mask(["T_UP"]) & (dist > 6)) | \
         (rect_mask(ARM_UPS)) | (rect_mask(ARM_FACES) & (YY <= 378))
    open_f = poly([(CX - 3, 96), (CX + 3, 96), (CX + 8, 141), (CX - 8, 141)]) * rect_mask(["T_F"])
    cm &= ~(open_f > 0.5)
    lift(c, cm.astype(F32), dy=2, sigma=1.6, strength=0.55)
    ct = fabric(seed + 1, cape, cloud=0.07, twill=0.05)
    c[cm, :3] = ct[cm]
    sheen(c, TORSO_RING, 0.12, width=0.2, y_max=146)
    hem = ndimage.binary_dilation(cm, iterations=1) & ~cm & rect_mask(TORSO_RING + ARM_FACES) & (YY > 120)
    paint(c, hem.astype(F32), NH_CRIMSON)
    # brass clasp chain across the opening, a small cross on the left breast of the cape
    brass_button(c, CX - 7, 104, r=2.4)
    brass_button(c, CX + 7, 104, r=2.4)
    chain(c, [(CX - 7, 106), (CX, 110), (CX + 7, 106)], BRASS)
    cross(c, 338, 118, 8, 12, 2, col=BRASS)
    bow(c, CX, 125, w=8, h=4, col=NH_CRIMSON, tails=14, seed=seed + 2)
    # blouse front: pin tucks; cuffs with lace
    for tx in (270, 278, 311, 319):
        shade(c, (rect_mask(["T_F"]) & (XX == tx) & (YY > 140) & (YY < 196)).astype(F32), 0.78)
    scallops(c, ARM_FACES, 448, 462, clip_end=SLEEVE_END)
    paint(c, (rect_mask(ARM_FACES) & (YY == 447)).astype(F32), LACE_EDGE)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def ink_club_blouse(name="shirt_fs_ink_club_blouse.png", body=(26, 24, 30), seed=3451):
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.03, twill=0.02, grain=0.02), sleeve_tex=dict(cloud=0.03, twill=0.02, grain=0.02))
    hole, dist = neck_dist()
    peter_pan_collar(c, dist, (36, 34, 42), edge=(120, 112, 140), seed=seed + 1)
    bow(c, CX, 101, w=12, h=6, col=INK_BLUE, tails=20, seed=seed + 2)
    # placket with jet buttons
    paint(c, lines([(CX, 112), (CX, 201)]), (8, 6, 10))
    for by in range(124, 200, 14):
        button(c, CX + 3, by, r=1.6, col=(60, 58, 70))
    # breast pocket with a brass-capped fountain pen and a quill emblem
    pk = (XX >= 320) & (XX <= 344) & (YY >= 126) & (YY <= 150)
    lift(c, pk.astype(F32), strength=0.35)
    paint(c, outline_of(pk, 1).astype(F32), (10, 8, 12))
    paint(c, lines([(337, 116), (337, 134)], 3), (16, 14, 26))
    paint(c, lines([(337, 116), (337, 120)], 3), BRASS)
    quill = shape(lambda d: d.polygon([(326, 142), (332, 128), (334, 129), (328, 143)], fill=255))
    paint(c, quill, (190, 186, 210))
    # sleeve garters (brass-buckled black bands) and ink-dark cuffs with a few drops of ink on the right cuff
    for n in ARM_FACES:
        g = rect_mask([n]) & (YY >= 400) & (YY <= 404)
        c[g, :3] = (10, 8, 10)
    for n in OUTERS:
        x, y, w, h = R[n]
        paint(c, shape(lambda d: d.rectangle((x + w / 2 - 3, 399, x + w / 2 + 3, 405), outline=255)), BRASS)
    cuff = rect_mask(ARM_FACES) & (YY >= 448) & (YY <= SLEEVE_END)
    c[cuff, :3] = fabric(seed + 3, INK_BLUE, cloud=0.04, twill=0.02)[cuff]
    shade(c, (rect_mask(ARM_FACES) & (YY == 448)).astype(F32), 0.5)
    rng = np.random.default_rng(seed)
    for _ in range(5):
        x, y = rng.uniform(155, 210), rng.uniform(436, 446)
        r = rng.uniform(1.2, 2.4)
        paint(c, shape(lambda d: d.ellipse((x - r, y - r, x + r, y + r), fill=255)), (20, 26, 70), 0.8)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def summer_blouse(name="shirt_fs_summer_blouse.png", blouse=IVORY_B, seed=3461):
    c = base_shirt(blouse, blouse, seed, body_tex=BLOUSE_TEX, sleeve_tex=BLOUSE_TEX, sleeve_end=398)
    hole, dist = neck_dist()
    arms = rect_mask(ARM_FACES)
    ph = face_phase(ARM_FACES)
    puff = arms & (YY < 398)
    fold = 1 + 0.13 * np.sin(2 * np.pi * (ph + 2) / 8 + 0.6 * np.sin(YY / 7))
    c[puff, :3] = np.clip(c[puff, :3] * fold[puff, None], 0, 255)
    band = arms & (YY >= 391) & (YY <= 397)
    c[band, :3] = fabric(seed + 1, blouse, **BLOUSE_TEX)[band]
    paint(c, (arms & (YY == 394)).astype(F32), (20, 18, 22))
    shade(c, (arms & (YY == 390)).astype(F32), 0.7)
    peter_pan_collar(c, dist, blouse, edge=(20, 18, 22), seed=seed + 2)
    bow(c, CX, 101, w=12, h=6, col=(150, 16, 28), tails=18, seed=seed + 3)
    pk = (XX >= 320) & (XX <= 344) & (YY >= 124) & (YY <= 148)
    lift(c, pk.astype(F32), strength=0.35)
    shade(c, outline_of(pk, 1).astype(F32), 0.5)
    crest(c, 332, 136, w=16, h=19, field=NH_CRIMSON, border=BRASS)
    for by in range(118, 200, 14):
        button(c, CX + 3, by, r=1.5, col=(230, 224, 210))
    soft_folds(c, rect_mask(TORSO_RING) & (YY > 160), period=12, amp=0.05, seed=seed)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=False)


def delinquent_long_blazer(name="shirt_fs_delinquent_long_blazer.png", body=(18, 16, 20), lining=NH_CRIMSON, seed=3471):
    """The sukeban look: an oversized black blazer worn open, crimson lining, sleeves pushed up, ribbon undone."""
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.08, twill=0.06), sleeve_tex=dict(cloud=0.08, twill=0.06), sleeve_end=428)
    hole, dist = neck_dist()
    # open front: blouse in a wide strip, crimson lining showing along both edges
    strip = poly([(270, 74), (319, 74), (325, 201), (264, 201)]) * rect_mask(["T_F"])
    paint(c, strip, blouse_fabric(seed + 1))
    lin = np.clip(lines([(268, 74), (262, 201)], 3) + lines([(321, 74), (327, 201)], 3), 0, 1) * rect_mask(["T_F"])
    paint(c, lin, fabric(seed + 2, lining, cloud=0.04, twill=0.0))
    lap = [(270, 74), (282, 128), (276, 130), (255, 100), (259, 94), (252, 90), (260, 74)]
    for pts in (lap, mirror(lap)):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.5, strength=0.6)
        paint(c, m, fabric(seed + 3, (30, 28, 34), cloud=0.05, twill=0.02))
    # undone ribbon hanging from the collar, an open top button
    rib = np.clip(lines([(CX - 2, 82), (CX - 5, 100), (CX - 3, 106)], 3) + lines([(CX + 2, 82), (CX + 6, 96)], 3), 0, 1)
    lift(c, rib, dy=1, sigma=1.0, strength=0.4)
    paint(c, rib, (150, 16, 28))
    paint(c, (rect_mask(["T_F"]) & (dist <= 3)).astype(F32), IVORY_B)
    # safety pins on the lapel, a big embroidered crimson crescent and bats on the back
    for px, py in ((262, 108), (266, 116)):
        paint(c, lines([(px, py), (px + 6, py + 2)], 1), (200, 200, 206))
    moon = crescent(491, 132, 26, 12)
    lift(c, moon, strength=0.4)
    paint(c, moon, (150, 16, 28))
    paint(c, outline_of(moon > 0.5, 1).astype(F32), BRASS)
    for bx, by, bw in ((462, 108, 14), (522, 102, 11), (512, 160, 9)):
        paint(c, bat(bx, by, bw), BRASS)
    paint(c, lines([(491, 166), (491, 201)]), (8, 6, 8))
    # pushed-up sleeves: bunched cuffs at the elbow, bare forearms below
    cuff = rect_mask(ARM_FACES) & (YY >= 414) & (YY <= 428)
    ph = face_phase(ARM_FACES)
    c[cuff, :3] = np.clip(c[cuff, :3] * (1 + 0.16 * np.sin(2 * np.pi * (ph + 3) / 9) * 0.8)[cuff, None], 0, 255)
    paint(c, (rect_mask(ARM_FACES) & (YY >= 425) & (YY <= 428)).astype(F32), fabric(seed + 4, lining, cloud=0.04, twill=0.0))
    shade(c, (rect_mask(ARM_FACES) & (YY == 414)).astype(F32), 0.6)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def crimson_jumper(name="shirt_fs_crimson_jumper.png", yarn=(112, 16, 28), seed=3481):
    c = blank()
    k = knit_plain(seed, yarn)
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    c[m, :3] = k[m]
    c[m, 3] = 255
    hole, dist = neck_dist()
    vee = poly([(262, 74), (327, 74), (CX, 130)]) * rect_mask(["T_F"])
    paint(c, vee, blouse_fabric(seed + 1))
    paint(c, np.clip(lines([(262, 74), (CX, 130), (327, 74)], 5) * rect_mask(["T_F"]), 0, 1), knit_plain(seed + 2, dark(yarn, 0.75)))
    paint(c, np.clip(lines([(265, 74), (CX, 125), (324, 74)], 1) * rect_mask(["T_F"]), 0, 1), (20, 16, 18))
    peter_pan_collar(c, dist, IVORY_B, seed=seed + 3)
    bow(c, CX, 101, w=9, h=5, col=(18, 14, 18), tails=16, seed=seed + 4)
    monogram(c, 340, 124, 16, fill=BRASS_HI, edge=BRASS)
    rib_band(c, TORSO_RING, 186, 201, dark(yarn, 0.82), seed=seed + 5)
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(yarn, 0.82), seed=seed + 6)
    clear(c, rect_mask(ARM_FACES) & (YY > SLEEVE_END))
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


# ------------------------------------------------------------------ bottoms
def court_pleats():
    return pleat_skirt("pants_fs_court_pleats_overknee.png", fabric(3501, NH_CRIMSON, cloud=0.06, twill=0.05), 3501,
                       hem=[(397, (14, 12, 14)), (398, (14, 12, 14)), (400, BRASS)],
                       leg=("socks", 410, JET, [(413, 414, NH_CRIMSON)]))


def navy_pleats():
    return pleat_skirt("pants_fs_navy_pleats.png", fabric(3511, NAVY_K, cloud=0.06, twill=0.05), 3511,
                       hem=[(397, IVORY_B), (400, IVORY_B)],
                       leg=("socks", 418, IVORY_B, [(421, 422, NAVY_K), (424, 424, NH_CRIMSON)]))


def forest_tartan_skirt():
    sett = [(FOREST_K, 9), ((16, 18, 16), 4), (CREAM_K, 1), ((16, 18, 16), 4), (FOREST_K, 3), (CANDLE_G, 1), (FOREST_K, 3), ((40, 34, 60), 4)]
    return pleat_skirt("pants_fs_forest_tartan.png", face_plaid(sett, 3521, cloud=0.05, soft=0.35), 3521,
                       leg=("socks", 418, (40, 38, 42), [(421, 422, CREAM_K)]))


def black_pleats_sheer():
    return pleat_skirt("pants_fs_black_pleats_sheer.png", fabric(3531, (24, 22, 26), cloud=0.06, twill=0.05), 3531,
                       hem=[(399, NH_CRIMSON)], leg=("sheer", (16, 14, 20), 212))


def crimson_tartan_tights():
    return pleat_skirt("pants_fs_crimson_tartan_tights.png", face_plaid(NH_TARTAN, 3541, cloud=0.06, soft=0.0), 3541, leg=("tights", (22, 20, 26)))


def chapel_midi(name="pants_fs_chapel_midi.png", cloth=(36, 34, 40), seed=3551):
    hem_y = 430
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.05), hem_y, seed)
    pleats(c, rect_mask(LEGS) & (YY < hem_y), period=16, lo=0.86, hi=1.1, fold=0.6)
    waistband(c, (18, 16, 20), seed + 1, 178, 192)
    for by in (182, 188):
        brass_button(c, CX - 6, by, r=1.7)
        brass_button(c, CX + 6, by, r=1.7)
    paint(c, (rect_mask(LEGS) & (YY == hem_y - 6)).astype(F32), NH_CRIMSON)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    tights(c, hem_y, SHOE_TOP, col=(20, 18, 24), seed=seed + 2)
    mary_janes(c)
    clear(c, hole)
    return save(c, name)


def delinquent_long_skirt(name="pants_fs_delinquent_long_skirt.png", cloth=(20, 18, 22), seed=3561):
    hem_y = 442
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.07, twill=0.05), hem_y, seed)
    pleats(c, rect_mask(LEGS) & (YY < hem_y), period=16, lo=0.84, hi=1.12, fold=0.55)
    waistband(c, (14, 12, 16), seed + 1)
    # crimson chain-stitch along the hem, a side slit on the left leg
    for n in LEGS:
        x, y, w, h = R[n]
        stitches(c, [(x + 1, hem_y - 6), (x + w - 2, hem_y - 6)], col=NH_CRIMSON, cross=NH_CRIMSON, every=3)
    x, y, w, h = R["LA_L"]
    clear(c, poly([(x + w / 2 - 1, 410), (x + w / 2 + 1, 410), (x + w / 2 + 5, hem_y), (x + w / 2 - 5, hem_y)]) > 0.5)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    combat_boots(c, hem_y, seed + 3, leather=(22, 20, 22), laces=NH_CRIMSON, sole_top=474)
    clear(c, hole)
    return save(c, name)


TOPS = [
    ("Crest Blazer & Ribbon", "crest-blazer", girls_blazer),
    ("Navy Sweater Vest", "navy-vest-f", navy_vest),
    ("Cropped Cardigan & Bow", "cropped-cardigan", cropped_cardigan),
    ("Vigil Sweater Vest", "vigil-vest-f", vigil_vest),
    ("Crimson Court Blazer", "crimson-court-blazer", crimson_court_blazer),
    ("Choir Blouse & Capelet", "choir-capelet", choir_capelet),
    ("Ink Club Blouse", "ink-club-blouse", ink_club_blouse),
    ("Mourning Pinafore", "mourning-pinafore", mourning_pinafore),
    ("Summer Blouse", "summer-blouse", summer_blouse),
    ("Forest Sweater Vest", "forest-vest-f", forest_vest),
    ("Delinquent Long Blazer", "delinquent-long-blazer", delinquent_long_blazer),
    ("Crimson V-Neck Jumper", "crimson-jumper", crimson_jumper),
]
BOTTOMS = [
    ("Charcoal Pleats + Knee Socks", "charcoal-pleats", charcoal_pleats),
    ("Vigil Tartan + Tights", "vigil-tartan", vigil_skirt),
    ("Crimson Court Pleats", "court-pleats", court_pleats),
    ("Navy Pleats + Ivory Socks", "navy-pleats", navy_pleats),
    ("Forest Tartan Skirt", "forest-tartan", forest_tartan_skirt),
    ("Black Pleats + Sheer Tights", "black-pleats-sheer", black_pleats_sheer),
    ("Pinafore Skirt + Stockings", "pinafore-stockings", pinafore_skirt_stockings),
    ("Long Delinquent Skirt + Boots", "delinquent-long-skirt", delinquent_long_skirt),
    ("Crimson Tartan + Tights", "crimson-tartan-tights", crimson_tartan_tights),
    ("Chapel Midi Skirt + Tights", "chapel-midi", chapel_midi),
]


def build():
    out = []
    with nhcloth.supersample(4):
        for label, key, fn in TOPS + BOTTOMS:
            out.append((fn(), label, key))
    return out


if __name__ == "__main__":
    for p, label, key in build():
        print(p.name, "|", label)
