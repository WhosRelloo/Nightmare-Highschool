"""Proposal previews for the 1.71 gender kits: three schoolgirl outfits and one civilian outfit per gender.
    python art/clothing/tools/kit_preview.py
Writes variants/kits/*.png (585x559, seam-bled) and variants/kits/preview_sheet.png."""
import numpy as np
from scipy import ndimage

from kit_common import *  # noqa: F401,F403
from kit_common import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS, F32
from female import cable_knit
from pants import tartan
import nhcloth


# ================================================================== A. crest blazer & ribbon (school, F)
def girls_blazer(name="shirt_fs_crest_blazer.png", body=JET, piping=NH_CRIMSON, ribbon=(150, 16, 28), seed=3101, lapel=None, crest_field=None):
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.07, twill=0.06), sleeve_tex=dict(cloud=0.07, twill=0.06))
    hole, dist = neck_dist()
    blouse = blouse_fabric(seed + 1)
    # blouse in a short, high V (girls' blazers button higher than the boys')
    vee = poly([(262, 74), (327, 74), (CX, 132)])
    paint(c, vee, blouse)
    peter_pan_collar(c, dist, IVORY_B, seed=seed + 2)
    bow(c, CX, 101, w=11, h=6, col=ribbon, tails=16, seed=seed + 3)
    # short lapels with crimson piping
    lap = [(266, 74), (CX - 1, 130), (286, 132), (256, 104), (259, 97), (252, 94), (257, 74)]
    lap_col = fabric(seed + 4, lapel or tuple(min(255, int(v * 1.3) + 6) for v in body), cloud=0.05, twill=0.02)
    for pts in (lap, mirror(lap)):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.4, strength=0.6)
        paint(c, m, lap_col)
        paint(c, lines(pts[2:] + [pts[0]], 1), piping)
    # fitted waist: princess darts curving in toward the waist, front and back (inside the faces)
    for x0 in (252, 337, 452, 530):
        dart = lines([(x0, 120), (x0 + (3 if x0 < CX or 440 < x0 < 500 else -3), 162), (x0, 201)], 1)
        shade(c, dart * 0.8, 0.7)
        paint(c, np.roll(dart, 1, 1) * 0.5, lerp(body, (90, 86, 92), 0.6), 0.5)
    # front: two brass buttons at the waist, a curved cutaway hem
    paint(c, lines([(CX, 132), (CX, 186)]), (6, 4, 6))
    for by in (146, 166):
        brass_button(c, CX - 5, by)
    cut = poly([(CX - 1, 186), (CX + 1, 186), (CX + 16, 202), (CX - 16, 202)])
    paint(c, cut, blouse)
    shade(c, outline_of(cut > 0.5, 1).astype(F32), 0.5)
    # crest on the left breast, welt pockets low
    lift(c, shape(lambda d: d.rounded_rectangle((331, 108, 351, 132), 6, fill=255)), strength=0.5)
    crest(c, 341, 120, w=20, h=24, field=crest_field or piping, border=BRASS)
    for x0 in (241, 322):
        paint(c, lines([(x0, 176), (x0 + 26, 176)], 2), (8, 6, 8))
    # back: centre seam, half belt with two brass buttons
    paint(c, lines([(491, 74), (491, 201)]), (8, 6, 8))
    belt = (XX >= 468) & (XX <= 514) & (YY >= 170) & (YY <= 177)
    lift(c, belt.astype(F32), dy=2, strength=0.5)
    c[belt, :3] = lap_col[belt]
    brass_button(c, 472, 173, r=1.8)
    brass_button(c, 510, 173, r=1.8)
    # collar ring on the top face
    up = rect_mask(["T_UP"])
    ring = up & (dist > 6) & (dist <= 11)
    paint(c, ring.astype(F32), lap_col)
    paint(c, (up & (dist > 11) & (dist <= 12)).astype(F32), piping)
    # cuffs: crimson piping ring, blouse cuff, brass cuff buttons
    paint(c, (rect_mask(ARM_FACES) & (YY == 444)).astype(F32), piping)
    blouse_cuffs(c, IVORY_B, 452, seed + 5)
    for bx in (127, 134, 141, 446, 453, 460):
        brass_button(c, bx, 437, r=1.5)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def charcoal_pleats(name="pants_fs_charcoal_pleats.png", cloth=CHAR, seed=3111):
    hem_y = 404
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.05), hem_y, seed)
    pleats(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190)))
    waistband(c, JET, seed + 1)
    brass_button(c, 392, 184, r=2.0)
    # crimson and brass hem stripes
    for yy, col in ((hem_y - 10, NH_CRIMSON), (hem_y - 9, NH_CRIMSON), (hem_y - 6, BRASS)):
        paint(c, (rect_mask(LEGS) & (YY == yy)).astype(F32), col)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    hem_notches(c, hem_y)
    bare_legs(c, hem_y, 416)
    knee_socks(c, 416, JET, bands=[(419, 420, NH_CRIMSON), (422, 422, BRASS)], seed=seed + 2)
    mary_janes(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== B. vigil sweater vest (school, F, The Vigil)
def vigil_vest(name="shirt_fs_vigil_vest.png", yarn=(226, 218, 198), blouse=JET, seed=3121):
    c = base_shirt(blouse, blouse, seed, body_tex=dict(cloud=0.05, twill=0.03), sleeve_tex=dict(cloud=0.05, twill=0.03))
    hole, dist = neck_dist()
    # the vest: cable knit over the torso, a deep V at the front
    k, _gut = cable_knit2(seed + 1, yarn)
    vee = poly([(256, 74), (333, 74), (CX, 150)]) * rect_mask(["T_F"])
    vm = rect_mask(TORSO_RING + ["T_UP"]) & ~(vee > 0.5)
    vm &= ~((rect_mask(["T_R", "T_L"])) & (YY < 88))          # armholes cut in at the shoulder
    c[vm, :3] = k[vm]
    # V-neck rib with a candle-gold stripe; armhole rib
    ribv = np.clip(lines([(256, 74), (CX, 150), (333, 74)], 5) * rect_mask(["T_F"]), 0, 1)
    paint(c, ribv, (24, 22, 26))
    paint(c, np.clip(lines([(259, 74), (CX, 145), (330, 74)], 1) * rect_mask(["T_F"]), 0, 1), CANDLE_G)
    for n in ("T_R", "T_L"):
        x, y, w, h = R[n]
        rb = rect_mask([n]) & (YY >= 86) & (YY <= 90)
        c[rb, :3] = (24, 22, 26)
    # blouse: rounded ivory collar and black ribbon tie inside the V
    peter_pan_collar(c, dist, IVORY_B, seed=seed + 2)
    bow(c, CX, 102, w=9, h=5, col=(20, 18, 22), tails=22, seed=seed + 3)
    # an embroidered candle with a gold flame on the chest (The Vigil)
    cx, cy = 338, 124
    stick = (XX >= cx - 2) & (XX <= cx + 2) & (YY >= cy - 2) & (YY <= cy + 10)
    paint(c, stick.astype(F32), (240, 232, 214))
    shade(c, outline_of(stick, 1).astype(F32), 0.6)
    flame = shape(lambda d: d.polygon([(cx, cy - 12), (cx + 3, cy - 6), (cx + 2, cy - 3), (cx - 2, cy - 3), (cx - 3, cy - 6)], fill=255))
    glow(c, flame, (255, 190, 80), sigma=2.5, strength=0.5)
    paint(c, flame, CANDLE_G)
    # ribbed hem with a gold stripe
    rib_band(c, TORSO_RING, 186, 201, dark(yarn, 0.9), stripes=[(190, 190, CANDLE_G)], seed=seed + 4)
    # back: a small gold "V" under the collar
    paint(c, lines([(486, 84), (491, 92), (496, 84)], 1), CANDLE_G)
    blouse_cuffs(c, IVORY_B, 452, seed + 5)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


VIGIL_SETT = None


def vigil_tartan(seed=0):
    ivory, blk, gold, ash = (214, 206, 186), (20, 18, 20), (204, 160, 70), (120, 116, 112)
    sett = [(blk, 8), (ivory, 2), (blk, 2), (gold, 1), (blk, 6), (ash, 5), (blk, 2), (ivory, 1), (blk, 2)]
    return face_plaid(sett, seed, cloud=0.05, soft=0.35)


def vigil_skirt(name="pants_fs_vigil_tartan_tights.png", seed=3131):
    hem_y = 404
    c, hole = skirt_shell(vigil_tartan(seed), hem_y, seed)
    pleats(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190)))
    waistband(c, JET, seed + 1)
    brass_button(c, 392, 184, r=2.0)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    hem_notches(c, hem_y)
    tights(c, hem_y, SHOE_TOP, col=(26, 24, 30), seed=seed + 2)
    mary_janes(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== C. mourning pinafore (school, F)
def mourning_pinafore(name="shirt_fs_mourning_pinafore.png", wool=(26, 22, 26), blouse=IVORY_B, seed=3141):
    c = base_shirt(blouse, blouse, seed, body_tex=BLOUSE_TEX, sleeve_tex=BLOUSE_TEX)
    hole, dist = neck_dist()
    # puffed blouse sleeves gathered at the shoulder and above the cuff
    arms = rect_mask(ARM_FACES)
    ph = face_phase(ARM_FACES)
    gather = arms & ((YY < 392) | ((YY > 432) & (YY < 446)))
    fold = 1 + 0.12 * np.sin(2 * np.pi * (ph + 2) / 8 + 0.5 * np.sin(YY / 9))
    c[gather, :3] = np.clip(c[gather, :3] * fold[gather, None], 0, 255)
    shade(c, (arms & (YY >= 390) & (YY <= 392)).astype(F32), 0.75)
    # ruffled stand collar and a black velvet ribbon
    ring = rect_mask(["T_UP", "T_F"]) & (dist <= 5)
    paint(c, ring.astype(F32), LACE)
    scal = rect_mask(["T_F"]) & (dist > 5) & (dist <= 7) & (((XX // 3) % 2) == 0)
    paint(c, scal.astype(F32), LACE_EDGE)
    bow(c, CX, 84, w=8, h=4, col=(16, 14, 18), tails=12, seed=seed + 1)
    # the pinafore: square neckline, wide straps over the shoulders, crimson piping, brass buttons
    neck_y = 112
    pm = rect_mask(TORSO_RING) & (YY >= neck_y)
    straps = ((XX >= 248) & (XX <= 266) | (XX >= 323) & (XX <= 341)) & rect_mask(["T_F"]) & (YY < neck_y)
    back_straps = ((XX >= 444) & (XX <= 462) | (XX >= 520) & (XX <= 538)) & rect_mask(["T_B"]) & (YY < 120)
    side = rect_mask(["T_R", "T_L"]) & (YY >= 96)
    up_straps = rect_mask(["T_UP"]) & (((XX >= 248) & (XX <= 266)) | ((XX >= 323) & (XX <= 341)))
    pm = pm | straps | back_straps | side | up_straps
    pm &= ~(rect_mask(["T_B"]) & (YY < 120) & ~back_straps)
    lift(c, pm.astype(F32), dy=1, sigma=1.4, strength=0.5)
    w_tex = fabric(seed + 2, wool, cloud=0.07, twill=0.05)
    c[pm, :3] = w_tex[pm]
    paint(c, outline_of(pm & rect_mask(TORSO_RING), 1).astype(F32), NH_CRIMSON)
    for bx in (257, 332):
        brass_button(c, bx, neck_y + 5, r=2.2)
    # button placket down the front
    for by in range(130, 196, 14):
        brass_button(c, CX, by, r=1.6)
    soft_folds(c, rect_mask(TORSO_RING) & (YY >= 150), period=16, amp=0.06, seed=seed)
    # lace cuffs on the blouse
    scallops(c, ARM_FACES, 448, 462, clip_end=SLEEVE_END)
    paint(c, (arms & (YY == 447)).astype(F32), LACE_EDGE)
    hem_line(c, 201, TORSO_RING, 0.6)
    clear(c, hole)
    return save(c, name)


def pinafore_skirt_stockings(name="pants_fs_pinafore_stockings.png", wool=(26, 22, 26), seed=3151):
    hem_y = 410
    c, hole = skirt_shell(fabric(seed, wool, cloud=0.07, twill=0.05), hem_y, seed)
    soft_folds(c, rect_mask(LEGS) & (YY < hem_y), period=16, amp=0.09, seed=seed)
    # the pinafore continues from the top: no waistband, just a crimson-piped seam
    paint(c, (rect_mask(TORSO_RING) & (YY == 186)).astype(F32), NH_CRIMSON)
    paint(c, (rect_mask(LEGS) & (YY == hem_y - 7)).astype(F32), NH_CRIMSON)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    # over-the-knee stockings with a lace top, a band of skin above
    bare_legs(c, hem_y, 416)
    tights(c, 416, SHOE_TOP, col=(18, 16, 20), seed=seed + 2)
    scallops(c, LEGS, 414, 422, col=(30, 26, 32), edge=(70, 64, 72), step=8)
    mary_janes(c, platform=True)
    clear(c, hole)
    return save(c, name)


# ================================================================== D. civilian (F): wine velvet corset + sheer sleeves
def velvet_corset(name="shirt_cf_velvet_corset.png", velvet=WINE, seed=3201):
    c = blank()
    # sheer black mesh over the whole shirt: partly see-through so the skin shows
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    sheer_mesh(c, m, col=(10, 8, 12), alpha_hole=205, alpha_thread=246)
    hole, dist = neck_dist()
    # velvet corset: sweetheart neckline, boning, a brass busk at the front, lacing at the back
    top_edge = 118 - 9 * np.cos(np.clip((XX - CX) / 30.0, -1.6, 1.6) * 2)
    cm = rect_mask(TORSO_RING) & (YY >= np.where(rect_mask(["T_F"]), top_edge, 112))
    vt = fabric(seed + 1, velvet, cloud=0.08, twill=0.0, grain=0.04)
    lift(c, cm.astype(F32), dy=-2, sigma=1.5, strength=0.4)
    c[cm, :3] = vt[cm]
    c[cm, 3] = 255
    sheen(c, TORSO_RING, 0.32, width=0.16, y_max=202)
    ph = face_phase(TORSO_RING)
    bone = cm & (ph >= 2) & (ph <= 61) & (((ph + 7) % 14) == 0)
    paint(c, bone.astype(F32), dark(velvet, 0.55), 0.8)
    paint(c, outline_of(cm, 1).astype(F32), BRASS)
    for by in range(126, 198, 9):
        brass_button(c, CX, by, r=1.4)
    lacing(c, 491, 118, 198, gap=6, step=9, col=(20, 16, 20), eyelet=BRASS)
    # choker ribbon on the neck ring, lace cuffs
    paint(c, (rect_mask(["T_UP"]) & (dist <= 4)).astype(F32), (18, 14, 18))
    scallops(c, ARM_FACES, 446, 462, col=(26, 22, 28), edge=(64, 58, 66), clip_end=SLEEVE_END)
    clear(c, rect_mask(ARM_FACES) & (YY > SLEEVE_END))
    clear(c, hole)
    return save(c, name)


def flares_platforms(name="pants_cf_flares_platforms.png", denim=(28, 26, 32), seed=3211):
    from pants import pants_base
    c = pants_base(denim, seed, tex=dict(cloud=0.06, twill=0.08), belt=None, crease=False, leg_end=SHOE_TOP + 6)
    # high waist with a corset belt and brass rings
    belt = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 192)
    lift(c, belt.astype(F32), dy=2, sigma=1.3, strength=0.5)
    c[belt, :3] = fabric(seed + 1, WINE, cloud=0.06, twill=0.0)[belt]
    lacing(c, CX, 180, 192, gap=4, step=6, col=(20, 16, 20), eyelet=BRASS, width=1)
    # flared hem: the leg widens into a darker fold (shading toward the face edges, inside the faces)
    ph = face_phase(LEGS)
    flare = rect_mask(LEGS) & (YY > 420) & (YY < SHOE_TOP + 6)
    k = ((YY - 420) / 37.0).clip(0, 1)
    side = np.abs((ph - 31.5) / 32.0)
    c[flare, :3] = np.clip(c[flare, :3] * (1 - 0.18 * k * side ** 2)[flare, None], 0, 255)
    for n in FRONTS + BACKS:
        x, y, w, h = R[n]
        paint(c, dash([(x + 18, 430), (x + 14, SHOE_TOP + 3)], on=2, off=2), (90, 70, 40))
        paint(c, dash([(x + w - 18, 430), (x + w - 14, SHOE_TOP + 3)], on=2, off=2), (90, 70, 40))
    # platform boots under the hem
    combat_boots(c, SHOE_TOP + 6, seed + 3, leather=(18, 16, 18), laces=(18, 16, 18), sole_top=468)
    return save(c, name)


# ================================================================== E. civilian (M): wool overcoat + turtleneck
def overcoat(name="shirt_cm_wool_overcoat.png", wool=(30, 28, 32), knit=(58, 56, 62), lining=NH_CRIMSON, seed=3301):
    c = base_shirt(wool, wool, seed, body_tex=dict(cloud=0.08, twill=0.07), sleeve_tex=dict(cloud=0.08, twill=0.07))
    hole, dist = neck_dist()
    # turtleneck: ribbed roll collar on the top face and a ribbed panel down the front opening
    tn = (rect_mask(["T_UP"]) & (dist <= 9)) | (rect_mask(["T_F"]) & (dist <= 8))
    d = fabric_detail(seed + 1, cloud=0.04, twill=0.0, grain=0.03, rib=0.12, rib_period=2)
    c[tn, :3] = tint(d, knit)[tn]
    shade(c, (rect_mask(["T_UP", "T_F"]) & (dist > 8) & (dist <= 9)).astype(F32), 0.55)
    opening = poly([(270, 74), (319, 74), (309, 201), (280, 201)])
    paint(c, opening, tint(d, knit))
    # wide notch lapels with crimson satin showing at the underside
    lap = [(268, 74), (281, 201), (276, 201), (250, 116), (256, 106), (246, 100), (256, 74)]
    lap_col = fabric(seed + 2, tuple(min(255, int(v * 1.25) + 4) for v in wool), cloud=0.06, twill=0.04)
    for pts in (lap, mirror(lap)):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.5, strength=0.6)
        under = np.roll(m, 1 if pts[0][0] < CX else -1, 1) * (1 - m)
        paint(c, under, lining)
        paint(c, m, lap_col)
        paint(c, outline_of(m > 0.5, 1).astype(F32) * 0.8, (8, 6, 8))
    # double-breasted brass buttons, flap pockets, ticket pocket
    for by in (140, 168):
        for bx in (262, 327):
            brass_button(c, bx, by, r=2.2)
    for x0 in (236, 320):
        flap = poly([(x0, 180), (x0 + 32, 180), (x0 + 32, 188), (x0, 188)])
        lift(c, flap, dy=2, sigma=1.2, strength=0.55)
        paint(c, flap, lap_col)
    # back: centre seam, a crimson-lined vent showing at the hem
    paint(c, lines([(491, 74), (491, 201)]), (8, 6, 8))
    paint(c, poly([(489, 186), (493, 186), (495, 201), (487, 201)]), lining)
    # sleeves: cuff band with three buttons, turtleneck cuff peeking out
    cuff = rect_mask(ARM_FACES) & (YY >= 438) & (YY <= 443)
    shade(c, cuff.astype(F32), 0.85)
    for bx in (123, 130, 137, 450, 457, 464):
        brass_button(c, bx, 441, r=1.3)
    rib_band(c, ARM_FACES, 452, SLEEVE_END, knit, seed=seed + 3)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name, creases=True)


def trousers_chelsea(name="pants_cm_trousers_chelsea.png", cloth=(40, 40, 46), seed=3311):
    from pants import pants_base
    c = pants_base(cloth, seed, tex=dict(cloud=0.05, twill=0.07), belt=(20, 16, 16), buckle=BRASS, leg_end=438)
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(F32), dy=2, sigma=1.3, strength=0.5)
    # chelsea boots: black leather, elastic side gussets, pull tabs, a stacked heel
    m = rect_mask(LEGS) & (YY >= 438)
    lt = fabric(seed + 1, (20, 18, 20), cloud=0.05, twill=0.0, grain=0.015)
    c[m, :3] = lt[m]
    c[m, 3] = 255
    sheen(c, LEGS, 0.3, at=0.42, width=0.18, y_max=476)
    for n in OUTERS + INNERS:
        x, y, w, h = R[n]
        g = poly([(x + w / 2 - 8, 440), (x + w / 2 + 8, 440), (x + w / 2 + 4, 462), (x + w / 2 - 4, 462)])
        paint(c, g, (44, 42, 46))
        ph = face_phase([n])
        paint(c, g * ((ph % 2) == 0), (30, 28, 32))
    for n in BACKS:
        x, y, w, h = R[n]
        paint(c, poly([(x + w / 2 - 4, 438), (x + w / 2 + 4, 438), (x + w / 2 + 4, 446), (x + w / 2 - 4, 446)]), (58, 50, 44))
    sole = rect_mask(LEGS) & (YY >= 476)
    c[sole, :3] = (34, 24, 18)
    c[rect_mask(LEGS) & (YY == 476), :3] = (70, 56, 40)
    shade(c, (rect_mask(LEGS) & (YY == 438)).astype(F32), 0.5)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = (30, 22, 18)
    c[dn, 3] = 255
    return save(c, name)


PAIRS = [
    (girls_blazer, charcoal_pleats, "Crest Blazer & Ribbon", "Charcoal Pleats + Knee Socks"),
    (vigil_vest, vigil_skirt, "Vigil Sweater Vest", "Vigil Tartan + Tights"),
    (mourning_pinafore, pinafore_skirt_stockings, "Mourning Pinafore", "Pinafore Skirt + Stockings"),
    (velvet_corset, flares_platforms, "Wine Velvet Corset", "Corset-Belt Flares + Platforms"),
    (overcoat, trousers_chelsea, "Wool Overcoat + Turtleneck", "Wool Trousers + Chelsea Boots"),
]


def build():
    out = []
    with nhcloth.supersample(4):
        for s, p, a, b in PAIRS:
            out.append((s(), a))
            out.append((p(), b))
    return out


if __name__ == "__main__":
    import sheet
    res = build()
    items = []
    for i in range(0, len(res), 2):
        (sp, sl), (pp, pl) = res[i], res[i + 1]
        items.append((f"kits/{sp.name}", sl, f"kits/{pp.name}"))
        items.append((f"kits/{pp.name}", pl, f"kits/{sp.name}"))
    print(sheet.build(items, path=KIT / "preview_sheet.png", title="Nightmare Highschool - gender kits: proposal previews",
                      note="Schoolgirl kit (3 outfits) and civilian kit (1 female, 1 male). Each top shown with its matching bottom."))
