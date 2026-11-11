"""Civilian kit (1.71): everyday clothes per gender, 6 tops + 6 bottoms each, candlelit gothic palette.
    python art/clothing/tools/kit_civilian.py
Writes variants/kits/*.png (585x559, seam-bled; see kit_common for the clean-edge rules)."""
import numpy as np

from kit_common import *  # noqa: F401,F403
from kit_common import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS, F32
from kit_preview import velvet_corset, flares_platforms, overcoat, trousers_chelsea
from kit_school_f import knit_plain, sheer_tights
from pants import pants_base, rip, tartan
import nhcloth

LEATHER = dict(cloud=0.06, twill=0.0, grain=0.015)
DENIM = dict(cloud=0.06, twill=0.09, grain=0.03)


def leather_shine(c, names, y_max=SLEEVE_END, amt=0.22):
    for n in names:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * 0.45)) / (w * 0.2)) ** 2) * (rect_mask([n]) & (YY < y_max))
        c[..., :3] = np.clip(c[..., :3] * (1 + amt * g[..., None]), 0, 255)


def zip_line(c, pts, col=BRASS, teeth=(30, 26, 22)):
    paint(c, lines(pts, 3), teeth)
    paint(c, dash(pts, on=1, off=1), col)


def sneakers(c, top=448, canvas=(22, 20, 24), sole=(222, 216, 204), seed=0, high=False):
    m = rect_mask(LEGS) & (YY >= top)
    c[m, :3] = fabric(seed, canvas, cloud=0.04, twill=0.05)[m]
    c[m, 3] = 255
    sm = rect_mask(LEGS) & (YY >= 470)
    c[sm, :3] = fabric(seed + 1, sole, cloud=0.03, twill=0.0)[sm]
    paint(c, (rect_mask(LEGS) & (YY == 470)).astype(F32), dark(sole, 0.7))
    paint(c, (rect_mask(LEGS) & (YY == 476)).astype(F32), dark(sole, 0.8))
    for n in FRONTS:
        x, y, w, h = R[n]
        mx = x + w / 2
        paint(c, poly([(mx - 7, top + 2), (mx + 7, top + 2), (mx + 6, 466), (mx - 6, 466)]), dark(canvas, 0.7))
        for ly in range(top + 5, 465, 5):
            paint(c, lines([(mx - 5, ly), (mx + 5, ly)]), (150, 144, 136))
            for ex in (mx - 6, mx + 6):
                paint(c, shape(lambda d: d.point((ex, ly), fill=255)), (180, 176, 168))
        paint(c, shape(lambda d: d.ellipse((x + 6, 462, x + w - 6, 474), fill=255)) * (YY >= 466), dark(sole, 0.95))
    if high:
        for n in OUTERS + INNERS:
            x, y, w, h = R[n]
            paint(c, shape(lambda d: d.ellipse((x + w / 2 - 6, top + 6, x + w / 2 + 6, top + 18), outline=255, width=2)), sole)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = fabric(seed + 2, dark(sole, 0.8), cloud=0.05, twill=0.0)[dn]
    c[dn, 3] = 255
    return c


def loafers(c, top=456, leather=(18, 14, 14), seed=0):
    m = rect_mask(LEGS) & (YY >= top)
    c[m, :3] = fabric(seed, leather, **LEATHER)[m]
    c[m, 3] = 255
    sheen(c, LEGS, 0.35, at=0.45, width=0.16, y_max=478)
    for n in FRONTS:
        x, y, w, h = R[n]
        strap = (XX >= x + 12) & (XX <= x + w - 12) & (YY >= top + 6) & (YY <= top + 9)
        c[strap, :3] = dark(leather, 0.6)
        brass_button(c, x + w / 2, top + 7.5, r=1.6)
    sole = rect_mask(LEGS) & (YY >= 478)
    c[sole, :3] = (46, 30, 20)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = (40, 28, 20)
    c[dn, 3] = 255
    return c


# ================================================================== female tops
def moto_cami(name="shirt_cf_moto_cami.png", hide=(20, 18, 22), cami=WINE, seed=3601):
    c = base_shirt(cami, hide, seed, body_tex=dict(cloud=0.05, twill=0.0, grain=0.03), sleeve_tex=LEATHER)
    hole, dist = neck_dist()
    # lace cami: scalloped neckline over the collarbones (skin above), lace texture
    cami_top = 104
    lace = ((((XX // 4) + (YY // 4)) % 2) == 0) & (((XX + YY) % 3) != 0)
    m = rect_mask(TORSO_RING) & (YY >= cami_top)
    c[m & lace, :3] = np.clip(c[m & lace, :3] * 0.7, 0, 255)
    clear(c, rect_mask(["T_F"]) & (YY < cami_top) & (dist > 0))
    scallops(c, ["T_F"], cami_top - 3, cami_top + 5, col=dark(cami, 0.8), edge=(20, 10, 14), step=8)
    # cropped leather jacket: open, ends at y 160, asymmetric brass zip, notched collar, studs
    crop = 160
    jm = (rect_mask(["T_R", "T_L", "T_B", "T_UP"]) & (YY <= crop)) | (rect_mask(["T_UP"]))
    for pts in ([(231, 74), (262, 74), (256, 120), (250, crop), (231, crop)],):
        jm = jm | (poly(pts) > 0.5) | (poly(mirror(pts)) > 0.5)
    jm &= ~hole
    lift(c, jm.astype(F32), dy=2, sigma=1.5, strength=0.5)
    jt = fabric(seed + 1, hide, **LEATHER)
    c[jm, :3] = jt[jm]
    c[jm, 3] = 255
    leather_shine(c, ["T_R", "T_L", "T_B"], y_max=crop + 1, amt=0.18)
    lap = [(240, 74), (262, 74), (258, 102), (248, 108), (244, 100)]
    for pts in (lap, mirror(lap)):
        mm = poly(pts)
        lift(c, mm, dy=1, strength=0.5)
        paint(c, mm, fabric(seed + 2, (30, 28, 32), **LEATHER))
        for sx, sy in pts[1:3]:
            paint(c, shape(lambda d: d.ellipse((sx - 1.3, sy + 2, sx + 1.3, sy + 4.6), fill=255)), (200, 200, 206))
    zip_line(c, [(252, 112), (248, crop)])
    zip_line(c, [(337, 112), (341, crop)])
    rib = rect_mask(["T_R", "T_L", "T_B"]) & (YY >= crop - 5) & (YY <= crop)
    c[rib, :3] = np.clip(c[rib, :3] * 0.8, 0, 255)
    # back: quilted shoulder yoke
    yoke = rect_mask(["T_B"]) & (YY <= 100)
    q = yoke & ((((XX - 427) + (YY - 74)) % 8 == 0) | (((XX - 427) - (YY - 74)) % 8 == 0))
    shade(c, q.astype(F32), 0.75)
    # zipped cuffs
    for n in ARM_FACES:
        x, y, w, h = R[n]
        if n in OUTERS:
            zip_line(c, [(x + w / 2, 436), (x + w / 2, SLEEVE_END)])
    leather_shine(c, ARM_FACES)
    clear(c, hole)
    return save(c, name)


def moon_sweater(name="shirt_cf_moon_sweater.png", yarn=(44, 42, 48), seed=3611):
    c = blank()
    k = knit_plain(seed, yarn)
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    c[m, :3] = k[m]
    c[m, 3] = 255
    hole, dist = neck_dist()
    # off the shoulder: the top face and shoulder tops are bare, a wide ribbed neckline crosses the chest
    neck_y = 92
    clear(c, rect_mask(["T_UP"]) | rect_mask(ARM_UPS))
    clear(c, rect_mask(TORSO_RING) & (YY < neck_y))
    clear(c, rect_mask(ARM_FACES) & (YY < 366))
    rib_band(c, TORSO_RING, neck_y, neck_y + 7, dark(yarn, 0.82), seed=seed + 1)
    rib_band(c, ARM_FACES, 366, 372, dark(yarn, 0.82), seed=seed + 2)
    # big cream crescent with stars on the chest, a small one on the back
    moon = crescent(CX + 4, 140, 22, 11)
    paint(c, moon, (224, 212, 186))
    paint(c, outline_of(moon > 0.5, 1).astype(F32), BRASS)
    for sx, sy, r in ((262, 120, 3), (270, 168, 2.2), (326, 112, 2.4), (330, 178, 2.0), (252, 146, 1.8)):
        paint(c, shape(lambda d: d.polygon([(sx, sy - r * 1.6), (sx + r * 0.5, sy), (sx, sy + r * 1.6), (sx - r * 0.5, sy)], fill=255)), BRASS_HI)
        paint(c, shape(lambda d: d.polygon([(sx - r * 1.6, sy), (sx, sy - r * 0.5), (sx + r * 1.6, sy), (sx, sy + r * 0.5)], fill=255)), BRASS_HI)
    paint(c, crescent(491, 130, 9, 4), (224, 212, 186))
    # slouchy body, long sweater-paw cuffs
    body = rect_mask(TORSO_RING)
    c[body, :3] = np.clip(c[body, :3] * (1 + 0.05 * np.sin(YY / 6.0 + XX / 19.0))[body, None], 0, 255)
    rib_band(c, TORSO_RING, 186, 201, dark(yarn, 0.85), seed=seed + 3)
    rib_band(c, ARM_FACES, 448, 470, dark(yarn, 0.85), seed=seed + 4)
    clear(c, rect_mask(ARM_FACES) & (YY > 470))
    clear(c, hole)
    return save(c, name)


def lace_blouse(name="shirt_cf_lace_blouse.png", body=(20, 18, 22), seed=3621):
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.03, twill=0.0, grain=0.02), sleeve_tex=dict(cloud=0.03, twill=0.0, grain=0.02))
    hole, dist = neck_dist()
    # sheer lace sleeves (a floral net), opaque bodice
    arms = rect_mask(ARM_FACES + ARM_UPS)
    sheer_mesh(c, arms, col=(12, 10, 14), alpha_hole=200, alpha_thread=244)
    dm = damask_mask(16) > 0.5
    c[arms & dm, 3] = 245
    # leg-of-mutton puff at the shoulder
    puff = rect_mask(ARM_FACES) & (YY < 392)
    c[puff, 3] = 245
    ph = face_phase(ARM_FACES)
    c[puff, :3] = np.clip(c[puff, :3] * (1 + 0.14 * np.sin(2 * np.pi * (ph + 2) / 8))[puff, None], 0, 255)
    # high neck with a ruffle, jabot, crimson cameo
    ring = rect_mask(["T_UP", "T_F"]) & (dist <= 6)
    paint(c, ring.astype(F32), (30, 28, 32))
    paint(c, (rect_mask(["T_F"]) & (dist > 6) & (dist <= 8) & (((XX // 3) % 2) == 0)).astype(F32), (60, 56, 62))
    jabot(c, CX, 90, n=5, col=(36, 32, 38))
    brooch(c, CX, 88, gem=(130, 12, 26))
    damask(c, rect_mask(TORSO_RING) & (YY > 120), 1.25)
    for by in range(130, 200, 12):
        button(c, CX, by, r=1.4, col=(60, 56, 64))
    scallops(c, ARM_FACES, 446, 462, col=(24, 22, 26), edge=(60, 56, 62), clip_end=SLEEVE_END)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name)


def cropped_hoodie(name="shirt_cf_cropped_hoodie.png", body=(110, 16, 28), lining=(18, 14, 18), seed=3631):
    fleece = dict(cloud=0.06, twill=0.02, grain=0.04)
    c = base_shirt(body, body, seed, body_tex=fleece, sleeve_tex=fleece)
    hole, dist = neck_dist()
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 3)).astype(F32), lining)
    shade(c, (neck & (dist > 3) & (dist <= 9)).astype(F32), 0.85)
    flap = shape(lambda d: d.ellipse((445, 36, 537, 116), fill=255)) * rect_mask(["T_B"])
    lift(c, flap, dy=2, sigma=1.5, strength=0.5)
    paint(c, (flap > 0.5) & (YY <= 77), lining)
    for x0, x1, y1 in ((287, 284, 120), (302, 305, 116)):
        paint(c, lines([(x0, 88), (x1, y1)], 2), (20, 16, 18))
        paint(c, lines([(x1, y1 - 3), (x1, y1 + 1)], 2), BRASS)
    # cropped at y 176: a ribbed band, bare midriff below it (the pants' waistband starts at 178)
    crop = 176
    rib_band(c, TORSO_RING, crop - 9, crop, dark(body, 0.8), seed=seed + 1)
    clear(c, rect_mask(TORSO_RING) & (YY > crop))
    # a black bat across the chest, "NIGHTMARE" small on the back
    paint(c, bat(CX, 132, 46), (18, 14, 18))
    paint(c, text_mask("N I G H T M A R E", 9, (491, 150)), (18, 14, 18))
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(body, 0.8), seed=seed + 2)
    clear(c, hole)
    return save(c, name)


def duster_slip(name="shirt_cf_duster_slip.png", knit=(70, 64, 66), slip=WINE, seed=3641):
    c = base_shirt(knit, knit, seed)
    k = knit_plain(seed, knit)
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    c[m, :3] = k[m]
    hole, dist = neck_dist()
    # satin slip in the open front, with thin straps and lace edge
    strip = poly([(266, 74), (323, 74), (329, 201), (260, 201)]) * rect_mask(["T_F"])
    st = fabric(seed + 1, slip, cloud=0.04, twill=0.0, grain=0.02)
    paint(c, strip, st)
    neck_line = 108
    clear(c, (strip > 0.5) & (YY < neck_line))
    for sx in (276, 313):
        paint(c, lines([(sx, 74), (sx, neck_line)], 2) * rect_mask(["T_F"]), dark(slip, 0.8))
    scallops(c, ["T_F"], neck_line - 2, neck_line + 4, col=(30, 14, 20), edge=(14, 8, 10), step=6)
    sheen(c, ["T_F"], 0.25, at=0.5, width=0.12, y_max=202)
    # long shawl edges of the duster, a tie belt, patch pockets
    edges = np.clip(lines([(266, 74), (260, 201)], 6) + lines([(323, 74), (329, 201)], 6), 0, 1) * rect_mask(["T_F"])
    lift(c, edges, dy=1, strength=0.45)
    paint(c, edges, knit_plain(seed + 2, dark(knit, 0.85)))
    belt = rect_mask(["T_R", "T_L", "T_B"]) & (YY >= 170) & (YY <= 176)
    c[belt, :3] = knit_plain(seed + 3, dark(knit, 0.8))[belt]
    for x0 in (236, 328):
        pk = (XX >= x0) & (XX <= x0 + 22) & (YY >= 176) & (YY <= 198)
        lift(c, pk.astype(F32), strength=0.35)
        shade(c, outline_of(pk, 1).astype(F32), 0.6)
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(knit, 0.85), seed=seed + 4)
    clear(c, hole)
    return save(c, name)


# ================================================================== female bottoms
def skirt_with(c, hole, name, hem_y, legs, boots=None, seed=0):
    return c


def velvet_midi(name="pants_cf_velvet_midi.png", velvet=WINE, seed=3701):
    hem_y = 432
    c, hole = skirt_shell(fabric(seed, velvet, cloud=0.08, twill=0.0, grain=0.04), hem_y, seed)
    soft_folds(c, rect_mask(LEGS) & (YY < hem_y), period=16, amp=0.12, seed=seed)
    sheen(c, LEGS, 0.2, at=0.4, width=0.12, y_max=hem_y)
    waistband(c, (18, 14, 18), seed + 1, 178, 188)
    brass_button(c, 392, 183, r=2.0)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    bare_legs(c, hem_y, 436)
    combat_boots(c, 436, seed + 2, leather=(18, 16, 18), laces=(18, 16, 18), sole_top=470)
    clear(c, hole)
    return save(c, name)


def leather_mini(name="pants_cf_leather_mini.png", hide=(18, 16, 20), seed=3711):
    hem_y = 392
    c, hole = skirt_shell(fabric(seed, hide, **LEATHER), hem_y, seed)
    leather_shine(c, LEGS, y_max=hem_y, amt=0.25)
    waistband(c, (12, 10, 12), seed + 1)
    zip_line(c, [(CX, 182), (CX, 201)])
    for n in FRONTS:
        x, y, w, h = R[n]
        zip_line(c, [(x + w - 10, 360), (x + w - 10, hem_y - 2)])
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    tights(c, hem_y, SHOE_TOP, col=(18, 16, 20), seed=seed + 2)
    for args in ((240, 412, 12, 7, 1), (356, 426, 10, 6, 2), (110, 418, 11, 6, 3), (470, 410, 9, 5, 4), (180, 432, 8, 5, 5)):
        rip(c, *args)
    combat_boots(c, 446, seed + 3, leather=(16, 14, 16), laces=NH_CRIMSON, sole_top=472)
    clear(c, hole)
    return save(c, name)


def wide_leg(name="pants_cf_wide_leg.png", cloth=(34, 32, 38), seed=3721):
    c = pants_base(cloth, seed, tex=dict(cloud=0.05, twill=0.06), belt=None, crease=True, leg_end=474)
    hw = rect_mask(TORSO_RING) & (YY >= 178) & (YY <= 192)
    lift(c, hw.astype(F32), dy=2, sigma=1.3, strength=0.5)
    for by in (182, 188):
        brass_button(c, CX - 6, by, r=1.7)
        brass_button(c, CX + 6, by, r=1.7)
    soft_folds(c, rect_mask(LEGS) & (YY > 400), period=16, amp=0.08, seed=seed)
    # pointed heeled boots just showing under the wide hem
    m = rect_mask(LEGS) & (YY >= 474)
    c[m, :3] = fabric(seed + 1, (16, 14, 16), **LEATHER)[m]
    c[m, 3] = 255
    for n in BACKS:
        x, y, w, h = R[n]
        c[rect_mask([n]) & (YY >= 476) & (XX >= x + w / 2 - 5) & (XX <= x + w / 2 + 5), :3] = (40, 32, 26)
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = (24, 20, 20)
    c[dn, 3] = 255
    return save(c, name)


def skater_thighhighs(name="pants_cf_skater_thighhighs.png", seed=3731):
    hem_y = 392
    sett = [(NH_CRIMSON, 8), ((16, 12, 14), 5), (BRASS, 1), ((16, 12, 14), 5), (NH_CRIMSON, 3), ((40, 36, 40), 2)]
    c, hole = skirt_shell(face_plaid(sett, seed, cloud=0.05, soft=0.35), hem_y, seed)
    soft_folds(c, rect_mask(LEGS) & (YY < hem_y), period=12, amp=0.14, seed=seed)
    waistband(c, (16, 12, 14), seed + 1)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    bare_legs(c, hem_y, 404)
    tights(c, 404, SHOE_TOP, col=(16, 14, 18), seed=seed + 2)
    for yy in (406, 407):
        paint(c, (rect_mask(LEGS) & (YY == yy)).astype(F32), NH_CRIMSON)
    mary_janes(c, platform=True)
    clear(c, hole)
    return save(c, name)


def lace_maxi(name="pants_cf_lace_maxi.png", cloth=(20, 18, 22), seed=3741):
    hem_y = 470
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.03), hem_y, seed)
    soft_folds(c, rect_mask(LEGS) & (YY < hem_y), period=16, amp=0.1, seed=seed)
    waistband(c, (14, 12, 14), seed + 1)
    chain(c, [(238, 192), (264, 197), (CX, 199), (325, 197), (351, 192)], BRASS)
    band = rect_mask(LEGS) & (YY >= 446) & (YY < hem_y)
    c[band, :3] = fabric(seed + 2, (26, 24, 28), cloud=0.03, twill=0.0)[band]
    damask(c, band, 1.4)
    scallops(c, LEGS, 440, 448, col=(30, 28, 32), edge=(70, 64, 72), step=8)
    scallops(c, LEGS, 462, 470, col=(30, 28, 32), edge=(70, 64, 72), step=8, clip_end=469)
    m = rect_mask(LEGS) & (YY >= hem_y)
    c[m, :3] = fabric(seed + 3, (16, 14, 16), **LEATHER)[m]
    c[m, 3] = 255
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = (22, 18, 18)
    c[dn, 3] = 255
    clear(c, hole)
    return save(c, name)


# ================================================================== male tops
def satin_bomber(name="shirt_cm_satin_bomber.png", satin=(104, 14, 26), seed=3801):
    st = dict(cloud=0.04, twill=0.0, grain=0.02)
    c = base_shirt(satin, satin, seed, body_tex=st, sleeve_tex=st)
    leather_shine(c, TORSO_RING + ARM_FACES, amt=0.3)
    hole, dist = neck_dist()
    rib = rect_mask(["T_UP", "T_F"]) & (dist <= 7)
    c[rib, :3] = knit_plain(seed + 1, (20, 18, 20))[rib]
    paint(c, (rect_mask(["T_UP", "T_F"]) & (dist > 3) & (dist <= 4)).astype(F32), BRASS)
    zip_line(c, [(CX, 80), (CX, 201)])
    for pts in ([(246, 140), (254, 176)], [(343, 140), (335, 176)]):
        paint(c, lines(pts, 3), (20, 18, 20))
    # embroidered moth: small on the chest, large on the back
    def moth(cx, cy, s):
        wing = [(0, 0), (-0.9, -0.7), (-1.15, -0.2), (-0.8, 0.15), (-0.95, 0.65), (-0.35, 0.5), (0, 0.15)]
        L = poly([(cx + x * s, cy + y * s) for x, y in wing])
        Rw = poly([(cx - x * s, cy + y * s) for x, y in wing])
        m = np.clip(L + Rw, 0, 1)
        lift(c, m, strength=0.4)
        paint(c, m, (214, 200, 170))
        for sgn in (-1, 1):
            paint(c, shape(lambda d: d.ellipse((cx + sgn * 0.62 * s - 0.18 * s, cy - 0.32 * s, cx + sgn * 0.62 * s + 0.18 * s, cy + 0.04 * s), fill=255)), BRASS)
            paint(c, lines([(cx, cy - 0.1 * s), (cx + sgn * 0.3 * s, cy - 0.75 * s)], 1), (30, 24, 20))
        paint(c, shape(lambda d: d.ellipse((cx - 0.12 * s, cy - 0.35 * s, cx + 0.12 * s, cy + 0.55 * s), fill=255)), (40, 30, 24))
        paint(c, outline_of(m > 0.5, 1).astype(F32), BRASS)
    moth(334, 118, 11)
    moth(491, 132, 34)
    rib_band(c, TORSO_RING, 186, 201, (20, 18, 20), stripes=[(191, 192, BRASS)], seed=seed + 2)
    rib_band(c, ARM_FACES, 444, SLEEVE_END, (20, 18, 20), stripes=[(449, 450, BRASS)], seed=seed + 3)
    clear(c, hole)
    return save(c, name)


def denim_jacket_hoodie(name="shirt_cm_denim_hoodie.png", denim=(30, 30, 36), hood=(52, 50, 56), seed=3811):
    c = base_shirt(denim, denim, seed, body_tex=DENIM, sleeve_tex=DENIM)
    hole, dist = neck_dist()
    fleece = fabric(seed + 1, hood, cloud=0.06, twill=0.02, grain=0.04)
    hm = (rect_mask(["T_UP"]) & (dist <= 14)) | (poly([(268, 74), (321, 74), (315, 201), (274, 201)]) * rect_mask(["T_F"]) > 0.5)
    c[hm, :3] = fleece[hm]
    flap = shape(lambda d: d.ellipse((447, 40, 535, 118), fill=255)) * rect_mask(["T_B"])
    lift(c, flap, dy=2, sigma=1.5, strength=0.5)
    paint(c, flap, fleece)
    for x0 in (285, 304):
        paint(c, lines([(x0, 86), (x0, 118)], 2), (210, 202, 188))
    # jacket: front edges, chest flap pockets, brass shank buttons, contrast stitching
    stitch = (150, 112, 52)
    for pts in ([(268, 74), (274, 201)], [(321, 74), (315, 201)]):
        paint(c, lines(pts, 2), dark(denim, 0.6))
        paint(c, dash([(pts[0][0] + (3 if pts[0][0] < CX else -3), pts[0][1]), (pts[1][0] + (3 if pts[0][0] < CX else -3), pts[1][1])], 2, 2), stitch)
    for x0 in (238, 324):
        flap2 = poly([(x0, 112), (x0 + 26, 112), (x0 + 26, 120), (x0 + 13, 124), (x0, 120)])
        lift(c, flap2, dy=1, strength=0.5)
        paint(c, outline_of(flap2 > 0.5, 1).astype(F32), stitch)
        brass_button(c, x0 + 13, 119, r=1.8)
    paint(c, dash([(231, 104), (264, 104)], 2, 2) + dash([(325, 104), (358, 104)], 2, 2), stitch)
    for by in (110, 140, 170):
        brass_button(c, 271, by, r=2.0)
    # patches: a crescent on the right chest, NH on the left sleeve
    paint(c, shape(lambda d: d.ellipse((246, 146, 262, 162), fill=255)), (20, 18, 22))
    paint(c, crescent(254, 154, 6, 3), BRASS_HI)
    x, y, w, h = R["LA_L"]
    paint(c, shape(lambda d: d.rounded_rectangle((x + 18, 372, x + w - 18, 392), 3, fill=255)), NH_CRIMSON)
    monogram(c, x + w / 2, 382, 12, fill=BRASS_HI, edge=BRASS)
    rib_band(c, TORSO_RING, 192, 201, dark(denim, 0.9), seed=seed + 2)
    cuff = rect_mask(ARM_FACES) & (YY >= 446) & (YY <= SLEEVE_END)
    shade(c, (rect_mask(ARM_FACES) & (YY == 446)).astype(F32), 0.6)
    paint(c, (rect_mask(ARM_FACES) & (YY == 450)).astype(F32) * 0.6, stitch)
    clear(c, hole)
    return save(c, name, creases=True)


def henley_suspenders(name="shirt_cm_henley_suspenders.png", knit=(196, 184, 160), seed=3821):
    c = base_shirt(knit, knit, seed, sleeve_end=430)
    waffle = tint(fabric_detail(seed, cloud=0.03, twill=0.0, grain=0.03), knit)
    wf = 1 - 0.08 * (((XX % 4) == 0) | ((YY % 4) == 0))
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS) & (c[..., 3] > 0)
    c[m, :3] = np.clip(waffle * wf[..., None], 0, 255)[m]
    hole, dist = neck_dist()
    rib = rect_mask(["T_UP", "T_F"]) & (dist <= 4)
    c[rib, :3] = knit_plain(seed + 1, dark(knit, 0.9))[rib]
    plk = (XX >= CX - 5) & (XX <= CX + 5) & (YY >= 74) & (YY <= 120)
    lift(c, plk.astype(F32), strength=0.3)
    shade(c, outline_of(plk, 1).astype(F32), 0.7)
    for by in (86, 98, 110):
        button(c, CX, by, r=1.7, col=(70, 56, 40))
    # pushed-up sleeves
    cuff = rect_mask(ARM_FACES) & (YY >= 418) & (YY <= 430)
    ph = face_phase(ARM_FACES)
    c[cuff, :3] = np.clip(c[cuff, :3] * (1 + 0.15 * np.sin(2 * np.pi * (ph + 3) / 9) * 0.8)[cuff, None], 0, 255)
    # suspenders: two straps front, a Y at the back, brass clips at the waist
    strap = (18, 16, 18)
    sm = np.clip(lines([(256, 74), (260, 201)], 6) + lines([(333, 74), (329, 201)], 6) +
                 lines([(452, 74), (491, 150)], 6) + lines([(530, 74), (491, 150)], 6) + lines([(491, 150), (491, 201)], 6), 0, 1)
    sm = sm * rect_mask(TORSO_RING + ["T_UP"])
    up = rect_mask(["T_UP"]) & ((np.abs(XX - 258) <= 3) | (np.abs(XX - 331) <= 3))
    sm = np.clip(sm + up, 0, 1)
    lift(c, sm, dy=1, strength=0.5)
    paint(c, sm, fabric(seed + 2, strap, cloud=0.03, twill=0.04))
    paint(c, outline_of(sm > 0.5, 1).astype(F32), NH_CRIMSON, 0.7)
    for cx in (260, 329, 491):
        paint(c, shape(lambda d: d.rectangle((cx - 4, 192, cx + 4, 200), fill=255)), BRASS)
        shade(c, outline_of(shape(lambda d: d.rectangle((cx - 4, 192, cx + 4, 200), fill=255)) > 0.5, 1).astype(F32), 0.5)
    hem_line(c, 201, TORSO_RING)
    clear(c, hole)
    return save(c, name)


def shawl_cardigan(name="shirt_cm_shawl_cardigan.png", knit=(62, 58, 60), shirt=IVORY_B, seed=3831):
    c = base_shirt(knit, knit, seed)
    k = cable_knit2(seed, knit, period=16, twist=10)[0]
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS) & (c[..., 3] > 0)
    c[m, :3] = k[m]
    hole, dist = neck_dist()
    vee = poly([(260, 74), (329, 74), (CX, 156)]) * rect_mask(["T_F"])
    paint(c, vee, blouse_fabric(seed + 1, shirt))
    # shirt collar points and a slim black tie
    for pts in ([(266, 74), (CX - 2, 92), (280, 96)], [(323, 74), (CX + 2, 92), (309, 96)]):
        paint(c, poly(pts), blouse_fabric(seed + 2, shirt))
        shade(c, outline_of(poly(pts) > 0.5, 1).astype(F32), 0.55)
    tie = poly([(291, 90), (298, 90), (300, 150), (CX, 156), (289, 150)])
    paint(c, tie, fabric(seed + 3, (18, 16, 18), cloud=0.03, twill=0.04))
    # thick shawl collar rolling round the V
    sc = np.clip(lines([(258, 74), (CX - 2, 158)], 9) + lines([(331, 74), (CX + 2, 158)], 9), 0, 1) * rect_mask(["T_F"])
    ring = (rect_mask(["T_UP"]) & (dist > 0) & (dist <= 10)).astype(F32)
    scm = np.clip(sc + ring, 0, 1)
    lift(c, scm, dy=2, sigma=1.6, strength=0.55)
    paint(c, scm, knit_plain(seed + 4, dark(knit, 1.1)))
    # leather toggle buttons
    for by in (166, 186):
        paint(c, shape(lambda d: d.ellipse((CX - 4, by - 2, CX + 4, by + 2), fill=255)), (70, 46, 30))
    for x0 in (238, 324):
        pk = (XX >= x0) & (XX <= x0 + 26) & (YY >= 168) & (YY <= 194)
        lift(c, pk.astype(F32), strength=0.35)
        shade(c, outline_of(pk, 1).astype(F32), 0.6)
    rib_band(c, TORSO_RING, 194, 201, dark(knit, 0.88), seed=seed + 5)
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(knit, 0.88), seed=seed + 6)
    clear(c, hole)
    return save(c, name)


def track_jacket(name="shirt_cm_track_jacket.png", body=(20, 18, 22), stripe=NH_CRIMSON, seed=3841):
    tt = dict(cloud=0.03, twill=0.0, grain=0.02)
    c = base_shirt(body, body, seed, body_tex=tt, sleeve_tex=tt)
    leather_shine(c, TORSO_RING + ARM_FACES, amt=0.12)
    hole, dist = neck_dist()
    stand = rect_mask(["T_UP", "T_F"]) & (dist <= 8)
    c[stand, :3] = fabric(seed + 1, body, **tt)[stand]
    paint(c, (rect_mask(["T_UP", "T_F"]) & (dist > 6) & (dist <= 7)).astype(F32), stripe)
    zip_line(c, [(CX, 80), (CX, 201)], col=(200, 200, 206))
    # two crimson stripes with a brass pinline down the outer sleeves and the torso sides
    for n in OUTERS + ["T_R", "T_L"]:
        x, y, w, h = R[n]
        y0 = 355 if n in OUTERS else 74
        y1 = SLEEVE_END - 10 if n in OUTERS else 190
        for sx, col, wd in ((x + w / 2 - 9, stripe, 5), (x + w / 2 - 2, BRASS, 1), (x + w / 2 + 5, stripe, 5)):
            sm = rect_mask([n]) & (XX >= sx) & (XX < sx + wd) & (YY >= y0) & (YY <= y1)
            c[sm, :3] = fabric(seed + 2, col, **tt)[sm]
    monogram(c, 338, 118, 15, fill=BRASS_HI, edge=BRASS)
    paint(c, text_mask("N H   A T H L E T I C S", 8, (491, 100)), BRASS_HI)
    rib_band(c, TORSO_RING, 190, 201, body, stripes=[(194, 195, stripe)], seed=seed + 3)
    rib_band(c, ARM_FACES, 448, SLEEVE_END, body, stripes=[(452, 453, stripe)], seed=seed + 4)
    clear(c, hole)
    return save(c, name)


# ================================================================== male bottoms
def dark_jeans_hightops(name="pants_cm_dark_jeans_hightops.png", denim=(26, 30, 46), seed=3901):
    c = pants_base(denim, seed, tex=DENIM, belt=(18, 14, 14), buckle=BRASS, crease=False, leg_end=440)
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(F32), dy=2, sigma=1.3, strength=0.5)
    for n in FRONTS + BACKS:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * 0.5)) / (w * 0.22)) ** 2 - ((YY - 410) / 16.0) ** 2) * rect_mask([n])
        c[..., :3] = np.clip(c[..., :3] * (1 + 0.25 * g[..., None]), 0, 255)
    for n in OUTERS + INNERS:
        x, y, w, h = R[n]
        paint(c, dash([(x + w / 2 + 2, 355), (x + w / 2 + 2, 438)], on=2, off=2), (150, 112, 52))
    sneakers(c, 440, canvas=(18, 16, 20), seed=seed + 1, high=True)
    return save(c, name)


def track_pants(name="pants_cm_track_pants.png", body=(20, 18, 22), stripe=NH_CRIMSON, seed=3911):
    tt = dict(cloud=0.03, twill=0.0, grain=0.02)
    c = pants_base(body, seed, tex=tt, belt=None, crease=False, leg_end=448, fly=False)
    rib_band(c, TORSO_RING, 178, 190, body, seed=seed + 1)
    for x0 in (285, 304):
        paint(c, lines([(x0, 190), (x0 - 1, 204)], 2), (210, 202, 188))
    for n in OUTERS:
        x, y, w, h = R[n]
        for sx, col, wd in ((x + w / 2 - 9, stripe, 5), (x + w / 2 - 2, BRASS, 1), (x + w / 2 + 5, stripe, 5)):
            sm = rect_mask([n]) & (XX >= sx) & (XX < sx + wd) & (YY < 440)
            c[sm, :3] = fabric(seed + 2, col, **tt)[sm]
    rib_band(c, LEGS, 440, 448, body, seed=seed + 3)
    sneakers(c, 448, canvas=(20, 18, 22), seed=seed + 4)
    return save(c, name)


def chinos_loafers(name="pants_cm_chinos_loafers.png", cloth=(84, 76, 62), seed=3921):
    c = pants_base(cloth, seed, tex=dict(cloud=0.04, twill=0.07), belt=(40, 26, 18), buckle=BRASS, leg_end=448)
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(F32), dy=2, sigma=1.3, strength=0.5)
    cuff = rect_mask(LEGS) & (YY >= 442) & (YY < 448)
    c[cuff, :3] = np.clip(c[cuff, :3] * 1.06, 0, 255)
    shade(c, (rect_mask(LEGS) & (YY == 442)).astype(F32), 0.6)
    bare_legs(c, 448, 456)
    loafers(c, 456, seed=seed + 1)
    return save(c, name)


def ripped_black_jeans(name="pants_cm_ripped_black_boots.png", denim=(26, 24, 28), seed=3931):
    c = pants_base(denim, seed, tex=DENIM, belt=(14, 12, 14), buckle=(190, 190, 196), crease=False, leg_end=444)
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(F32), dy=2, sigma=1.3, strength=0.5)
    for args in ((249, 412, 26, 9, 11), (341, 418, 22, 8, 12), (236, 386, 12, 4, 13), (115, 410, 14, 5, 14), (472, 414, 12, 5, 15)):
        rip(c, *args)
    chain(c, [(343, 192), (356, 206), (362, 222)], (196, 196, 202))
    combat_boots(c, 444, seed + 1, leather=(18, 16, 18), laces=(18, 16, 18), sole_top=474)
    return save(c, name)


def cargo_shorts(name="pants_cm_cargo_shorts.png", cloth=(44, 44, 46), seed=3941):
    c = pants_base(cloth, seed, tex=dict(cloud=0.05, twill=0.05), belt=(20, 16, 16), buckle=BRASS, crease=False, leg_end=402)
    lift(c, (rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 190)).astype(F32), dy=2, sigma=1.3, strength=0.5)
    for n in OUTERS:
        x, y, w, h = R[n]
        pk = (XX >= x + 10) & (XX <= x + w - 10) & (YY >= 368) & (YY <= 394) & rect_mask([n])
        lift(c, pk.astype(F32), strength=0.4)
        shade(c, outline_of(pk, 1).astype(F32), 0.6)
        flap = (XX >= x + 9) & (XX <= x + w - 9) & (YY >= 366) & (YY <= 373) & rect_mask([n])
        c[flap, :3] = np.clip(c[flap, :3] * 1.1, 0, 255)
        shade(c, outline_of(flap, 1).astype(F32), 0.6)
        brass_button(c, x + w / 2, 370, r=1.4)
    bare_legs(c, 402, 424)
    knee_socks(c, 424, (20, 18, 22), bands=[(427, 428, NH_CRIMSON)], seed=seed + 1)
    sneakers(c, 448, canvas=(20, 18, 22), seed=seed + 2)
    return save(c, name)


FEMALE_TOPS = [
    ("Wine Velvet Corset", "velvet-corset", velvet_corset),
    ("Cropped Moto Jacket & Lace Cami", "moto-cami", moto_cami),
    ("Off-Shoulder Moon Sweater", "moon-sweater", moon_sweater),
    ("Victorian Lace Blouse", "lace-blouse", lace_blouse),
    ("Cropped Crimson Hoodie", "cropped-hoodie", cropped_hoodie),
    ("Long Duster & Slip Top", "duster-slip", duster_slip),
]
FEMALE_BOTTOMS = [
    ("Corset-Belt Flares + Platforms", "corset-flares", flares_platforms),
    ("Velvet Midi Skirt + Boots", "velvet-midi", velvet_midi),
    ("Leather Mini + Ripped Tights", "leather-mini", leather_mini),
    ("Wide-Leg Trousers", "wide-leg-trousers", wide_leg),
    ("Tartan Skater + Thigh-Highs", "skater-thighhighs", skater_thighhighs),
    ("Lace-Hem Maxi Skirt", "lace-maxi", lace_maxi),
]
MALE_TOPS = [
    ("Wool Overcoat + Turtleneck", "wool-overcoat", overcoat),
    ("Crimson Satin Bomber", "satin-bomber", satin_bomber),
    ("Denim Jacket + Hoodie", "denim-hoodie", denim_jacket_hoodie),
    ("Henley + Brass Suspenders", "henley-suspenders", henley_suspenders),
    ("Shawl Cardigan + Tie", "shawl-cardigan", shawl_cardigan),
    ("Track Jacket", "track-jacket", track_jacket),
]
MALE_BOTTOMS = [
    ("Wool Trousers + Chelsea Boots", "trousers-chelsea", trousers_chelsea),
    ("Dark Jeans + High-Tops", "dark-jeans-hightops", dark_jeans_hightops),
    ("Track Pants + Sneakers", "track-pants", track_pants),
    ("Chinos + Loafers", "chinos-loafers", chinos_loafers),
    ("Ripped Black Jeans + Boots", "ripped-black-boots", ripped_black_jeans),
    ("Cargo Shorts + Socks", "cargo-shorts", cargo_shorts),
]


def build():
    out = []
    with nhcloth.supersample(4):
        for label, key, fn in FEMALE_TOPS + FEMALE_BOTTOMS + MALE_TOPS + MALE_BOTTOMS:
            out.append((fn(), label, key))
    return out


if __name__ == "__main__":
    for p, label, key in build():
        print(p.name, "|", label)
