"""Civilian (off-duty) clothes: gothic Victorian-academy-at-night streetwear."""
import numpy as np
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import base_shirt, face_seams, hem_line
from recolors import MONO, polo_parts, vest_parts
from pants import pants_base


import nhcloth

NO_CREASE = {"shirt_civ_flannel_open.png", "pants_civ_skirt_fishnet.png", "shirt_civ_tee_the_hollow.png"}


def save(c, name):
    """Every piece in this set goes through the quality pass before saving."""
    return nhcloth.save(finish(c, creases=name not in NO_CREASE, seed=sum(map(ord, name))), name)

OXBLOOD = (74, 10, 16)
INK = (8, 6, 8)


# ================================================================== hoodie
def hoodie(name="shirt_civ_hoodie_blood_moon.png", body=(34, 30, 34), lining=(118, 12, 22), seed=101):
    fleece = dict(cloud=0.08, twill=0.02, grain=0.045)
    c = base_shirt(body, body, seed, body_tex=fleece, sleeve_tex=fleece)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 3)).astype(np.float32), lining)
    shade(c, (neck & (dist > 3) & (dist <= 4)).astype(np.float32), 0.35)
    shade(c, (neck & (dist > 4) & (dist <= 10)).astype(np.float32), 0.85)
    paint(c, (neck & (dist > 10) & (dist <= 11)).astype(np.float32), dark(body, 1.5), 0.7)
    # hood lying on the back
    flap = shape(lambda d: d.ellipse((445, 36, 537, 116), fill=255)) * rect_mask(["T_B"])
    lift(c, flap, dy=2, sigma=1.5, strength=0.5)
    c[flap > 0.5, :3] = np.clip(c[flap > 0.5, :3] * 1.12, 0, 255)
    paint(c, (flap > 0.5) & (YY <= 77), lining)
    shade(c, outline_of(flap > 0.5, 1).astype(np.float32), 0.3)
    paint(c, dash([(491, 78), (491, 112)], 2, 2), dark(body, 0.55))
    # drawstrings
    for x0, x1, y1 in ((287, 284, 122), (302, 305, 117)):
        paint(c, lines([(x0, 88), (x1, y1)], 2), (220, 212, 196))
        paint(c, lines([(x1, y1 - 3), (x1, y1 + 1)], 2), GOLD)
        paint(c, shape(lambda d: d.ellipse((x0 - 2, 86, x0 + 2, 90), outline=255)), GOLD)
    # kangaroo pocket
    pk = [(252, 150), (337, 150), (347, 186), (242, 186)]
    pm = poly(pk)
    lift(c, pm, dy=1, sigma=1.2, strength=0.4)
    shade(c, outline_of(pm > 0.5, 1).astype(np.float32), 0.35)
    paint(c, dash([(254, 153), (335, 153)], 2, 2), dark(body, 0.5))
    for a, b in (((253, 152), (244, 182)), ((336, 152), (345, 182))):
        paint(c, lines([a, b], 2), dark(body, 0.45))
    # blood moon print on the chest, large distressed one on the back
    ds = distress_mask(seed, 0.8)
    moon = crescent(CX, 118, 11, 6)
    paint(c, moon * ds, GOLD)
    for dx, dl in ((-4, 7), (0, 11), (4, 5)):
        paint(c, lines([(CX + dx, 127), (CX + dx, 127 + dl)], 2) * ds, (150, 14, 26))
        paint(c, shape(lambda d: d.ellipse((CX + dx - 1.5, 126 + dl, CX + dx + 1.5, 130 + dl), fill=255)) * ds, (150, 14, 26))
    paint(c, text_mask("AFTER  DARK", 8, (CX, 152)) * distress_mask(seed + 3, 0.95), (206, 196, 172))
    big = crescent(491, 132, 28, 13)
    paint(c, big * distress_mask(seed + 1, 0.7), GOLD)
    paint(c, text_mask("N I G H T M A R E", 10, (491, 178)) * distress_mask(seed + 2, 0.93), (206, 196, 172))
    rib_band(c, TORSO_RING, 186, 201, dark(body, 0.85), seed=seed)
    rib_band(c, ARM_FACES, 446, SLEEVE_END, dark(body, 0.85), seed=seed + 1)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


# ================================================================== leather jacket
def leather_jacket(name="shirt_civ_leather_jacket.png", hide=(22, 19, 22), tee=(116, 12, 22), seed=111):
    lt = dict(cloud=0.06, twill=0.0, grain=0.015)
    c = base_shirt(hide, hide, seed, body_tex=lt, sleeve_tex=lt)
    sheen(c, TORSO_RING + ARM_FACES, 0.35, width=0.18)
    rng = np.random.default_rng(seed)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for _ in range(4):
            yy = rng.integers(392, 412)
            x0 = x + rng.integers(4, w - 20)
            paint(c, lines([(x0, yy), (x0 + 8, yy + rng.integers(-2, 3)), (x0 + 15, yy)]), (70, 66, 72), 0.8)
    hole, _ = polo_hole()
    tee_m = poly([(268, 74), (321, 74), (316, 201), (273, 201)])
    paint(c, tee_m, tint(fabric_detail(seed + 1, cloud=0.05, twill=0.02), tee))
    dist = ndimage.distance_transform_edt(~hole)
    paint(c, (rect_mask(["T_UP", "T_F"]) & (dist <= 3) & (tee_m > 0.5)).astype(np.float32), dark(tee, 0.7))
    # tee print: small gold NH
    MONO.paste(c, CX, 128, fill=(226, 196, 120), edge=(90, 60, 20))
    lap = [(252, 74), (268, 74), (282, 118), (273, 148), (246, 104), (253, 96), (246, 88)]
    for pts in (lap, [(2 * CX - x, y) for x, y in lap]):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.4, strength=0.55)
        paint(c, m, tint(fabric_detail(seed + 2, cloud=0.05, twill=0), dark(hide, 1.5)))
        shade(c, outline_of(m > 0.5, 1).astype(np.float32), 0.25)
    for sx in (250, 2 * CX - 250):
        button(c, sx, 98, r=1.8, col=(206, 190, 150))
    # zip teeth down both front edges and on the pockets / cuffs
    def zip_line(a, b, w=2):
        paint(c, lines([a, b], w + 2), INK)
        z = lines([a, b], w) * ((YY + XX) % 2 == 0)
        paint(c, z, GOLD)
    zip_line((273, 148), (275, 201))
    zip_line((2 * CX - 273, 148), (2 * CX - 275, 201))
    zip_line((240, 154), (258, 142))
    zip_line((2 * CX - 240, 154), (2 * CX - 258, 142))
    for zx in (141, 446):
        zip_line((zx, 428), (zx, 458))
    # belt at the hem
    belt = rect_mask(TORSO_RING) & (YY >= 189) & (YY <= 196)
    c[belt, :3] = np.clip(c[belt, :3] * 1.25, 0, 255)
    shade(c, (rect_mask(TORSO_RING) & ((YY == 188) | (YY == 197))).astype(np.float32), 0.3)
    paint(c, shape(lambda d: d.rectangle((243, 187, 252, 198), outline=255)), GOLD)
    # epaulettes on the shoulders
    for ex in (236, 343):
        m = (XX >= ex) & (XX <= ex + 10) & (YY >= 12) & (YY <= 66)
        c[m, :3] = np.clip(c[m, :3] * 1.3 + 4, 0, 255)
        shade(c, outline_of(m, 1).astype(np.float32), 0.3)
        button(c, ex + 5, 61, r=1.8, col=(206, 190, 150))
    # back yoke and panel seams
    paint(c, lines([(427, 100), (554, 100)]), INK)
    paint(c, dash([(427, 103), (554, 103)], 2, 2), (60, 56, 60))
    paint(c, lines([(462, 100), (466, 201)]) + lines([(520, 100), (516, 201)]), INK)
    hem_line(c, 201, TORSO_RING, 0.3)
    clear(c, hole)
    face_seams(c, 0.5)
    return save(c, name)


# ================================================================== flannel
FLANNEL = [((118, 12, 22), 8), ((22, 16, 18), 6), ((118, 12, 22), 2), ((22, 16, 18), 2), ((190, 150, 62), 1), ((22, 16, 18), 2)]


def flannel(name="shirt_civ_flannel_open.png", seed=121):
    c = blank()
    pl = plaid(FLANNEL, seed, cloud=0.07, soft=0.6)
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    c[m, :3] = pl[m]
    c[m, 3] = 255
    hole, P = polo_hole()
    pp = polo_parts()
    tee_m = poly([(268, 74), (321, 74), (318, 201), (271, 201)])
    paint(c, tee_m, tint(fabric_detail(seed + 1, cloud=0.04, twill=0.02), (26, 24, 28)))
    paint(c, crescent(CX, 128, 8, 4) * distress_mask(seed, 0.8), (200, 170, 100))
    collar = pp["grey"] & (YY <= 104) & rect_mask(["T_UP", "T_F"]) & ~((XX >= 283) & (XX <= 306) & (YY >= 84))
    c[collar, :3] = np.clip(pl[collar] * 0.92, 0, 255)
    c[collar, 3] = 255
    shade(c, outline_of(collar, 1).astype(np.float32), 0.3)
    paint(c, lines([(268, 92), (271, 201)]) + lines([(321, 92), (318, 201)]), INK)
    for by in range(104, 200, 16):
        button(c, 265, by, r=1.5, col=(214, 206, 188))
        paint(c, lines([(322, by), (326, by)]), INK)
    for x0 in (242, 325):
        pk = (XX >= x0) & (XX <= x0 + 22) & (YY >= 102) & (YY <= 126)
        lift(c, pk.astype(np.float32), strength=0.35)
        shade(c, outline_of(pk, 1).astype(np.float32), 0.35)
        shade(c, ((XX >= x0) & (XX <= x0 + 22) & (YY == 109)).astype(np.float32), 0.45)
        button(c, x0 + 11, 106, r=1.4, col=(214, 206, 188))
    # rolled sleeves
    arms = rect_mask(ARM_FACES)
    shade(c, (arms & (YY >= 396) & (YY < 404)).astype(np.float32), 0.8)
    cuff = arms & (YY >= 404) & (YY <= 416)
    c[cuff, :3] = np.clip(c[cuff, :3] * 1.2 + 8, 0, 255)
    for yl, f in ((404, 0.35), (409, 0.6), (416, 0.3)):
        shade(c, (arms & (YY == yl)).astype(np.float32), f)
    clear(c, arms & (YY > 416))
    # curved shirttail hem, shorter at the sides
    hem = np.full(W, 199.0)
    for n in ("T_R", "T_L"):
        x, y, w, h = R[n]
        xs = np.arange(x, x + w)
        hem[xs] = 192 + 6 * np.abs((xs - (x + w / 2)) / (w / 2))
    torn_edge(c, rect_mask(TORSO_RING), hem, fray=(150, 30, 36), seed=seed)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


# ================================================================== waistcoat
def waistcoat(name="shirt_civ_victorian_waistcoat.png", coat=(28, 22, 28), satin=(124, 12, 24), seed=131):
    p = vest_parts()
    src = p["src"]
    c = recolor(src.copy(), p["vest"], coat, 12)
    damask(c, p["vest"], 1.45)
    c[p["sleeves"], :3] = recolor(src, p["sleeves"], IVORY, 12)[p["sleeves"], :3]
    c[p["vee"], :3] = recolor(src, p["vee"], IVORY, 12)[p["vee"], :3]
    tm = p["neck"] | p["hem"] | p["arm"]
    c[tm, :3] = recolor(src, tm, GOLD, 10)[tm, :3]
    # crimson satin back with a half belt
    back = p["vest"] & rect_mask(["T_B"])
    c[back, :3] = tint(fabric_detail(seed, cloud=0.05, twill=0.0, grain=0.015), satin, 10)[back]
    sheen(c, ["T_B"], 0.25, width=0.2)
    strap = rect_mask(["T_B"]) & (XX >= 466) & (XX <= 516) & (YY >= 166) & (YY <= 171)
    c[strap, :3] = dark(satin, 0.7)
    shade(c, outline_of(strap, 1).astype(np.float32), 0.4)
    paint(c, shape(lambda d: d.rectangle((488, 164, 495, 173), outline=255)), GOLD)
    # billowy poet sleeves with lace cuffs
    arms = rect_mask(ARM_FACES) & (c[..., 3] > 0)
    fold = 1 + 0.13 * np.sin(2 * np.pi * XX / 11 + 0.7 * np.sin(YY / 13))
    c[arms, :3] = np.clip(c[arms, :3] * fold[arms, None], 0, 255)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for sx in range(x, x + w, 8):
            m = shape(lambda d: d.ellipse((sx - 1, 446, sx + 9, 462), fill=255)) * rect_mask([n]) * (YY <= SLEEVE_END)
            paint(c, m, (242, 238, 226))
            paint(c, shape(lambda d: d.arc((sx - 1, 446, sx + 9, 462), 20, 160, fill=255)) * rect_mask([n]), (150, 144, 130))
    paint(c, (rect_mask(ARM_FACES) & (YY == 445)).astype(np.float32), (150, 144, 130))
    # cravat, ruby brooch, buttons, watch chain
    jabot(c, CX, 88, n=5)
    brooch(c, CX, 90)
    paint(c, lines([(CX, 114), (CX, 201)]), INK)
    for by in (124, 138, 152, 166, 180):
        button(c, CX + 3, by, r=2.2)
    for x0 in (244, 322):
        paint(c, lines([(x0, 160), (x0 + 22, 160)], 2), INK)
    chain(c, [(CX + 3, 152), (310, 160), (322, 162), (332, 160)], GOLD)
    clear(c, rect_mask(["T_D"]))
    return save(c, name)


# ================================================================== hussar greatcoat
def greatcoat(name="shirt_civ_hussar_coat.png", wool=OXBLOOD, braid=GOLD, seed=141):
    wt = dict(cloud=0.09, twill=0.05)
    c = base_shirt(wool, wool, seed, body_tex=wt, sleeve_tex=wt)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 6)).astype(np.float32), tint(fabric_detail(seed + 1, cloud=0.05, twill=0), (20, 14, 18)))
    paint(c, (neck & (dist > 6) & (dist <= 7)).astype(np.float32), braid)
    paint(c, lines([(CX, 90), (CX, 201)]), INK)
    for by in (102, 120, 138, 156, 174):
        w = 30 - (by - 102) * 0.12
        lift(c, lines([(CX - w, by), (CX + w, by)], 2), strength=0.5)
        paint(c, lines([(CX - w, by), (CX + w, by)], 2), braid)
        for lx in (CX - w - 3.5, CX + w + 3.5):
            paint(c, shape(lambda d: d.ellipse((lx - 3.5, by - 3, lx + 3.5, by + 3), outline=255)), braid)
        for lx in (CX - w * 0.5, CX + w * 0.5):
            paint(c, shape(lambda d: d.ellipse((lx - 2, by - 2.5, lx + 2, by + 2.5), outline=255)), braid)
        button(c, CX, by, r=2.4)
    paint(c, (rect_mask(TORSO_RING) & (YY == 199)).astype(np.float32), braid)
    # shoulder cords
    for ex in (236, 342):
        m = (XX >= ex) & (XX <= ex + 11) & (YY >= 14) & (YY <= 68)
        paint(c, (m & (((XX + YY) // 2) % 2 == 0)).astype(np.float32), braid)
        paint(c, (m & (((XX + YY) // 2) % 2 == 1)).astype(np.float32), dark(braid, 0.6))
        shade(c, outline_of(m, 1).astype(np.float32), 0.3)
    # black velvet cuffs with an Austrian knot
    cuff = rect_mask(ARM_FACES) & (YY >= 432) & (YY <= SLEEVE_END)
    c[cuff, :3] = tint(fabric_detail(seed + 2, cloud=0.05, twill=0), (20, 14, 18))[cuff]
    paint(c, (rect_mask(ARM_FACES) & (YY == 432)).astype(np.float32), braid)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        mx = x + w / 2
        paint(c, lines([(x + 10, 431), (mx, 410), (x + w - 10, 431)]), braid)
        paint(c, shape(lambda d: d.ellipse((mx - 3, 404, mx + 3, 411), outline=255)), braid)
    # back braid
    for pts in ([(462, 78), (472, 140), (480, 196)], [(520, 78), (510, 140), (502, 196)]):
        paint(c, lines(pts), braid)
    for lx in (480, 502):
        paint(c, shape(lambda d: d.ellipse((lx - 3, 193, lx + 3, 199), outline=255)), braid)
    paint(c, lines([(491, 170), (491, 201)]), INK)
    clear(c, hole)
    face_seams(c)
    return save(c, name)


# ================================================================== band tee
def band_tee(name="shirt_civ_tee_the_hollow.png", body=(24, 22, 26), seed=151):
    jt = dict(cloud=0.04, twill=0.02, grain=0.035)
    c = base_shirt(body, body, seed, body_tex=jt, sleeve_tex=jt, sleeve_end=398)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 4)).astype(np.float32), dark(body, 1.4))
    shade(c, (neck & (dist > 4) & (dist <= 5)).astype(np.float32), 0.5)
    rib_band(c, ARM_FACES, 392, 398, dark(body, 1.2), seed=seed)
    ds = distress_mask(seed, 0.72)
    bone = (226, 218, 196)
    paint(c, crescent(CX, 130, 22, 10, ang=200) * ds, (150, 14, 26))
    skull(c, CX, 130, 1.05, bone=bone, distress=ds)
    arc_text(c, "THE HOLLOW", CX, 166, 68, 74, 12, bone, distress=distress_mask(seed + 4, 0.93))
    paint(c, text_mask("NIGHT  TOUR  '26", 9, (CX, 168)) * distress_mask(seed + 5, 0.95), (186, 30, 40))
    # back: tour dates at the school's own haunts
    ds2 = distress_mask(seed + 1, 0.95)
    paint(c, text_mask("THE HOLLOW", 12, (491, 92)) * ds2, bone)
    dates = [("10.13", "THE ARCHIVE"), ("10.17", "BOILER YARD"), ("10.21", "BELL TOWER"),
             ("10.26", "THE CHAPEL"), ("10.31", "BENEATH")]
    for i, (dte, place) in enumerate(dates):
        y = 114 + i * 14
        paint(c, text_mask(dte, 8, (448, y), anchor="lm") * ds2, (186, 30, 40))
        paint(c, text_mask(place, 8, (476, y), anchor="lm") * ds2, bone)
    paint(c, dash([(231, 197), (358, 197)]) + dash([(165, 197), (228, 197)]) + dash([(361, 197), (554, 197)]), dark(body, 2.0))
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


# ================================================================== pants
def cargo(name="pants_civ_cargo_boots.png", cloth=(38, 38, 40), seed=161):
    c = pants_base(cloth, seed, tex=dict(cloud=0.07, twill=0.05), belt=(110, 12, 22), crease=False, leg_end=422)
    for n in OUTERS:
        x, y, w, h = R[n]
        pk = rect_mask([n]) & (XX >= x + 10) & (XX <= x + w - 10) & (YY >= 378) & (YY <= 410)
        lift(c, pk.astype(np.float32), dy=2, sigma=1.4, strength=0.45)
        c[pk, :3] = np.clip(c[pk, :3] * 1.08, 0, 255)
        shade(c, outline_of(pk, 1).astype(np.float32), 0.4)
        flap = rect_mask([n]) & (XX >= x + 9) & (XX <= x + w - 9) & (YY >= 376) & (YY <= 384)
        c[flap, :3] = np.clip(c[flap, :3] * 0.85, 0, 255)
        shade(c, outline_of(flap, 1).astype(np.float32), 0.35)
        button(c, x + w / 2, 382, r=1.8)
        paint(c, dash([(x + w / 2, 386), (x + w / 2, 408)], 2, 2), dark(cloth, 0.55))
    for n in FRONTS:
        x, y, w, h = R[n]
        paint(c, dash([(x, 396), (x + w, 396)], 2, 1) + dash([(x, 404), (x + w, 404)], 2, 1), dark(cloth, 0.55))
    rng = np.random.default_rng(seed)
    for n in LEGS:
        x, y, w, h = R[n]
        for _ in range(3):
            yy = rng.integers(412, 420)
            x0 = x + rng.integers(2, w - 20)
            shade(c, lines([(x0, yy), (x0 + 9, yy + 2), (x0 + 18, yy)]), 0.55)
    combat_boots(c, 422, seed)
    return save(c, name)


def jeans_boots(name="pants_civ_black_jeans_boots.png", seed=171):
    c = load("pants_jeans_b.png")
    from pants import denim_zone, ramp
    z = denim_zone(c)
    L = c[..., :3].mean(-1) / 255.0
    c[z, :3] = ramp(L, [(0, (4, 4, 6)), (0.55, (34, 32, 36)), (1.0, (120, 116, 122))])[z]
    rng = np.random.default_rng(seed)
    for n in LEGS:
        x, y, w, h = R[n]
        for _ in range(3):
            yy = rng.integers(416, 426)
            x0 = x + rng.integers(2, w - 20)
            shade(c, lines([(x0, yy), (x0 + 9, yy + 2), (x0 + 18, yy)]), 0.5)
    combat_boots(c, 426, seed, laces=(40, 36, 36))
    chain(c, [(206, 356), (200, 372), (186, 384), (170, 380), (158, 366), (156, 356)], (196, 196, 200))
    return save(c, name)


def joggers(name="pants_civ_joggers_stripe.png", cloth=(40, 36, 42), stripe=(130, 14, 26), seed=181):
    c = pants_base(cloth, seed, tex=dict(cloud=0.05, twill=0.01, grain=0.03), belt=None, crease=False, leg_end=451, fly=False)
    rib_band(c, TORSO_RING, 179, 191, dark(cloth, 0.85), seed=seed)
    for x0, x1 in ((290, 287), (299, 302)):
        paint(c, lines([(x0, 186), (x1, 200)], 2), (222, 214, 198))
        paint(c, lines([(x1, 198), (x1, 201)], 2), GOLD)
    for n in OUTERS:
        x, y, w, h = R[n]
        mx = x + w // 2
        s = rect_mask([n]) & (XX >= mx - 3) & (XX <= mx + 3) & (YY < 440)
        paint(c, s.astype(np.float32), stripe)
        paint(c, (rect_mask([n]) & ((XX == mx - 4) | (XX == mx + 4)) & (YY < 440)).astype(np.float32), GOLD)
    for n in ("T_R", "T_L"):
        x, y, w, h = R[n]
        mx = x + w // 2
        s = rect_mask([n]) & (XX >= mx - 3) & (XX <= mx + 3) & (YY >= 191)
        paint(c, s.astype(np.float32), stripe)
    rib_band(c, LEGS, 440, 450, dark(cloth, 0.85), seed=seed + 1)
    jeans_sneakers(c)
    return save(c, name)


def pinstripe(name="pants_civ_pinstripe_riding_boots.png", cloth=(30, 30, 36), seed=191):
    c = pants_base(cloth, seed, tex=dict(cloud=0.05, twill=0.03), belt=(20, 16, 18), crease=True, leg_end=410)
    fab = (c[..., 3] > 0) & ((rect_mask(LEGS) & (YY < 410)) | (rect_mask(TORSO_RING) & (YY >= 189)) | rect_mask(["T_D"]))
    pin = fab & (XX % 6 == 0)
    c[pin, :3] = np.clip(c[pin, :3] * 1.45 + 12, 0, 255)
    riding_boots(c, 410)
    return save(c, name)


def fishnet_skirt(name="pants_civ_skirt_fishnet.png", cloth=(24, 22, 26), seed=201):
    c, hole = pants_shell()
    hem_y = 400
    tex = tint(fabric_detail(seed, cloud=0.06, twill=0.03), cloth)
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | (rect_mask(LEGS) & (YY < hem_y)) | rect_mask(ARM_UPS) | rect_mask(["T_D"])
    c[m, :3] = tex[m]
    c[m, 3] = 255
    shade(c, rect_mask(["T_D"]).astype(np.float32), 0.6)
    pleat = (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190))
    fac = 0.8 + 0.4 * ((XX % 8) / 7.0)
    c[pleat, :3] = np.clip(c[pleat, :3] * fac[pleat, None], 0, 255)
    shade(c, (pleat & (XX % 8 == 0)).astype(np.float32), 0.5)
    paint(c, (rect_mask(LEGS) & (YY >= hem_y - 5) & (YY <= hem_y - 4)).astype(np.float32), CRIMSON)
    wb = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 189)
    c[wb, :3] = tint(fabric_detail(seed + 1, cloud=0.05), (16, 14, 16))[wb]
    shade(c, (wb & ((YY == 179) | (YY == 189))).astype(np.float32), 0.4)
    chain(c, [(238, 190), (262, 197), (CX, 200), (327, 197), (351, 190)], GOLD)
    chain(c, [(428, 191), (491, 199), (554, 191)], GOLD)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(np.float32), 0.35)
    clear(c, rect_mask(LEGS) & (YY == hem_y - 1) & (XX % 8 == 0))
    # fishnet: diamond net over bare skin
    net_zone = rect_mask(LEGS) & (YY >= hem_y) & (YY < 432)
    clear(c, net_zone)
    net = net_zone & ((((XX + YY) % 6) == 0) | (((XX - YY) % 6) == 0))
    c[net, :3] = (14, 12, 14)
    c[net, 3] = 255
    band = rect_mask(LEGS) & (YY >= hem_y) & (YY <= hem_y + 3)
    c[band, :3] = (14, 12, 14)
    c[band, 3] = 255
    combat_boots(c, 432, seed, laces=CRIMSON, sole_top=470)
    clear(c, hole)
    return save(c, name)


SHIRTS = [hoodie, leather_jacket, flannel, waistcoat, greatcoat, band_tee]
PANTS = [cargo, jeans_boots, joggers, pinstripe, fishnet_skirt]


def build():
    with nhcloth.supersample(4):
        return [f() for f in SHIRTS + PANTS]


if __name__ == "__main__":
    for f in build():
        print(f.name)
