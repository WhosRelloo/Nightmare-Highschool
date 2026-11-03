"""Female outfits: seven top + bottom pairs drawn for the Female body, in the school's crimson, black,
gold, navy and violet. Four are school wear (owned through the School Store / enrolment), three are
civilian. Same quality pass as the other sets (nhcloth.finish)."""
import numpy as np
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import base_shirt, face_seams, hem_line, mirror
from recolors import MONO
from pants import pants_base, school_shoes, socks, LEG_UPS, SHOE_TOP

import nhcloth

F32 = np.float32
INK = (8, 6, 8)
NAVY_D = (22, 28, 56)
LACE = (238, 232, 218)
LACE_EDGE = (150, 142, 128)
VIOLET = (58, 28, 86)
TIGHTS = (30, 28, 34)

NO_CREASE = {"pants_f_sailor_skirt.png", "pants_f_chapel_skirt.png", "pants_f_pinafore_skirt.png",
             "pants_f_lolita_skirt.png", "pants_f_plaid_mini.png", "pants_f_cheer_skirt.png",
             "shirt_f_cheer_shell.png", "pants_f_gala_skirt.png", "shirt_f_gala_bodice.png"}


def save(c, name):
    return nhcloth.save(finish(c, creases=name not in NO_CREASE, seed=sum(map(ord, name))), name)


def fabric(seed, col, **tex):
    return tint(fabric_detail(seed, **(tex or dict(cloud=0.07, twill=0.04))), col)


def neck_dist():
    hole, _ = polo_hole()
    return hole, ndimage.distance_transform_edt(~hole)


def bow(c, cx, cy, w=10, h=6, col=CRIMSON, tails=12, seed=0):
    loops = poly([(cx, cy), (cx - w, cy - h), (cx - w - 1, cy + h)]) + poly([(cx, cy), (cx + w, cy - h), (cx + w + 1, cy + h)])
    tl = poly([(cx - 1, cy), (cx - 6, cy + tails), (cx - 2, cy + tails - 3), (cx + 1, cy)]) + \
        poly([(cx + 1, cy), (cx + 6, cy + tails), (cx + 2, cy + tails - 3), (cx - 1, cy)])
    m = np.clip(loops + tl, 0, 1)
    lift(c, m, dy=1, sigma=1.2, strength=0.5)
    paint(c, m, fabric(seed, col, cloud=0.05, twill=0.0))
    shade(c, outline_of(m > 0.5, 1).astype(F32), 0.4)
    k = shape(lambda d: d.ellipse((cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5), fill=255))
    paint(c, k, dark(col, 0.7))
    return c


def scallops(c, names, y0, y1, col=LACE, edge=LACE_EDGE, step=8, clip_end=None):
    """A row of lace scallops between y0 and y1 on each face."""
    for n in names:
        x, y, w, h = R[n]
        for sx in range(x, x + w, step):
            m = shape(lambda d: d.ellipse((sx - 1, y0, sx + step + 1, y1), fill=255)) * rect_mask([n])
            if clip_end is not None:
                m = m * (YY <= clip_end)
            paint(c, m, col)
            paint(c, shape(lambda d: d.arc((sx - 1, y0, sx + step + 1, y1), 20, 160, fill=255)) * rect_mask([n]), edge)
            dots = shape(lambda d: [d.point((sx + k, y1 - 3), fill=255) for k in range(1, step, 2)]) * rect_mask([n])
            paint(c, dots, edge, 0.7)
    return c


def lacing(c, cx, y0, y1, gap=6, step=8, col=CRIMSON, eyelet=GOLD, width=2):
    for y in range(y0, y1 - step + 1, step):
        lift(c, lines([(cx - gap, y), (cx + gap, y + step)], width) + lines([(cx + gap, y), (cx - gap, y + step)], width), strength=0.4)
        paint(c, lines([(cx - gap, y), (cx + gap, y + step)], width), col)
        paint(c, lines([(cx + gap, y), (cx - gap, y + step)], width), dark(col, 0.8))
    for y in range(y0, y1 + 1, step):
        for ex in (cx - gap, cx + gap):
            paint(c, shape(lambda d: d.ellipse((ex - 1.8, y - 1.8, ex + 1.8, y + 1.8), outline=255)), eyelet)
    return c


def pleated(c, mask, period=8, lo=0.82, hi=1.14):
    ph = (XX % period) / (period - 1.0)
    fac = lo + (hi - lo) * ph
    c[mask, :3] = np.clip(c[mask, :3] * fac[mask, None], 0, 255)
    shade(c, (mask & (XX % period == 0)).astype(F32), 0.55)
    return c


def skirt_shell(cloth_tex, hem_y, seed):
    """Opaque margin, see-through panel, skirt cloth from the waist to hem_y on every leg face."""
    c, hole = pants_shell(seed)
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | (rect_mask(LEGS) & (YY < hem_y)) | rect_mask(LEG_UPS) | rect_mask(["T_D"])
    c[m, :3] = cloth_tex[m]
    c[m, 3] = 255
    shade(c, rect_mask(["T_D"]).astype(F32), 0.55)
    return c, hole


def waistband(c, col, seed, y0=179, y1=189):
    wb = rect_mask(TORSO_RING) & (YY >= y0) & (YY <= y1)
    lift(c, wb.astype(F32), dy=2, sigma=1.3, strength=0.5)
    c[wb, :3] = fabric(seed, col, cloud=0.05, twill=0.03)[wb]
    shade(c, (wb & ((YY == y0) | (YY == y1))).astype(F32), 0.45)
    return wb


def bare_legs(c, y0, y1):
    clear(c, rect_mask(LEGS) & (YY >= y0) & (YY < y1))


def tights(c, y0, y1, col=TIGHTS, seed=0, sheer=0.0):
    m = rect_mask(LEGS) & (YY >= y0) & (YY < y1)
    t = fabric(seed, col, cloud=0.04, twill=0.0, grain=0.02)
    c[m, :3] = t[m]
    c[m, 3] = 255
    sheen(c, LEGS, 0.22, at=0.45, width=0.25, y_max=y1)
    return c


def stripes(c, y0, y1, a, b, period=6, seed=0):
    m = rect_mask(LEGS) & (YY >= y0) & (YY < y1)
    col = np.where((((YY - y0) // (period // 2)) % 2 == 0)[..., None], np.array(a, F32), np.array(b, F32))
    d = fabric_detail(seed, cloud=0.04, twill=0.0, grain=0.03)
    c[m, :3] = np.clip(col * d[..., None], 0, 255)[m]
    c[m, 3] = 255
    return c


def mary_janes(c, seed=5, strap_y=458, platform=False):
    school_shoes(c, seed)
    for n in FRONTS + OUTERS + INNERS:
        x, y, w, h = R[n]
        strap = rect_mask([n]) & (YY >= strap_y) & (YY <= strap_y + 2)
        c[strap, :3] = (10, 8, 10)
        if n in OUTERS:
            paint(c, shape(lambda d: d.ellipse((x + w * 0.55 - 2, strap_y - 1, x + w * 0.55 + 2, strap_y + 3), fill=255)), GOLD)
    if platform:
        sole = rect_mask(LEGS) & (YY >= 472)
        c[sole, :3] = (14, 12, 14)
        c[rect_mask(LEGS) & (YY == 472), :3] = (60, 56, 58)
    return c


# ================================================================== 1. sailor uniform (school)
def sailor_top(name="shirt_f_sailor_navy.png", blouse=IVORY, collar=NAVY_D, scarf=CRIMSON, seed=901):
    bt = dict(cloud=0.05, twill=0.03)
    c = base_shirt(blouse, blouse, seed, body_tex=bt, sleeve_tex=bt)
    hole, dist = neck_dist()
    navy = fabric(seed + 1, collar, cloud=0.06, twill=0.04)
    # the collar: wide flaps over the shoulders forming a V at the front, a square flap at the back
    lap = [(231, 74), (264, 74), (CX, 136), (CX, 150), (231, 98)]
    front = np.clip(poly(lap) + poly(mirror(lap)), 0, 1)
    sides = (rect_mask(["T_R", "T_L"]) & (YY <= 98)).astype(F32)
    back = (rect_mask(["T_B"]) & (YY <= 120)).astype(F32)
    top = (rect_mask(["T_UP"]) & ~hole).astype(F32)
    col_m = np.clip(front + sides + back + top, 0, 1)
    lift(c, col_m, dy=2, sigma=1.6, strength=0.5)
    paint(c, col_m, navy)
    # modesty panel inside the V with a small gold NH
    panel = poly([(266, 74), (323, 74), (CX, 133)])
    paint(c, panel, fabric(seed + 2, collar, cloud=0.05, twill=0.02))
    shade(c, outline_of(panel > 0.5, 1).astype(F32), 0.5)
    MONO.paste(c, CX, 92, fill=(226, 196, 120), edge=(90, 60, 20))
    # two ivory stripes along every collar edge
    for off in (3, 6):
        paint(c, lines([(231 + off * 0.2, 98 - off), (CX - off * 0.9, 150 - off * 1.6)]) +
              lines([(358 - off * 0.2, 98 - off), (CX + off * 0.9, 150 - off * 1.6)]), IVORY)
        paint(c, lines([(430, 120 - off), (551, 120 - off)]) + lines([(430 + off, 74), (430 + off, 120 - off)]) +
              lines([(551 - off, 74), (551 - off, 120 - off)]), IVORY)
        paint(c, (rect_mask(["T_R", "T_L"]) & (YY == 98 - off)).astype(F32), IVORY)
    shade(c, outline_of(col_m > 0.5, 1).astype(F32), 0.45)
    # crimson scarf knotted at the point of the V
    bow(c, CX, 142, w=11, h=6, col=scarf, tails=26, seed=seed + 3)
    # navy cuffs with two stripes, a breast pocket
    cuff = rect_mask(ARM_FACES) & (YY >= 438) & (YY <= SLEEVE_END)
    c[cuff, :3] = navy[cuff]
    for yy in (443, 447):
        paint(c, (rect_mask(ARM_FACES) & (YY == yy)).astype(F32), IVORY)
    shade(c, (rect_mask(ARM_FACES) & (YY == 438)).astype(F32), 0.4)
    pk = (XX >= 318) & (XX <= 338) & (YY >= 156) & (YY <= 174)
    lift(c, pk.astype(F32), strength=0.3)
    shade(c, outline_of(pk, 1).astype(F32), 0.45)
    hem_line(c, 199, TORSO_RING, 0.5)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def sailor_skirt(name="pants_f_sailor_skirt.png", cloth=NAVY_D, seed=911):
    hem_y = 404
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.04), hem_y, seed)
    pleated(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190)))
    waistband(c, cloth, seed + 1)
    button(c, 392, 184, r=2.2)
    for yy in (hem_y - 9, hem_y - 6):
        paint(c, (rect_mask(LEGS) & (YY == yy)).astype(F32), IVORY)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.35)
    clear(c, rect_mask(LEGS) & (YY == hem_y - 1) & (XX % 8 == 0))
    bare_legs(c, hem_y, 416)
    socks(c, 416, SHOE_TOP - 1, IVORY, bands=[(419, 420, NAVY_D), (422, 422, CRIMSON)], seed=seed + 2)
    school_shoes(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== 2. chapel blouse and corset (school)
def chapel_top(name="shirt_f_chapel_corset.png", blouse=IVORY, corset=(20, 16, 20), lace_col=CRIMSON, seed=921):
    bt = dict(cloud=0.05, twill=0.02)
    c = base_shirt(blouse, blouse, seed, body_tex=bt, sleeve_tex=bt)
    hole, dist = neck_dist()
    # puffed shoulders: gathered fullness at the top of the sleeves
    arms = rect_mask(ARM_FACES)
    puff = arms & (YY < 392)
    fold = 1 + 0.12 * np.sin(2 * np.pi * XX / 7 + 0.6 * np.sin(YY / 9))
    c[puff, :3] = np.clip(c[puff, :3] * fold[puff, None], 0, 255)
    shade(c, (arms & (YY >= 390) & (YY <= 393)).astype(F32), 0.7)
    c[rect_mask(ARM_UPS), :3] = np.clip(c[rect_mask(ARM_UPS), :3] * 1.06, 0, 255)
    # standing lace collar and a cameo
    ring = rect_mask(["T_UP", "T_F"]) & (dist <= 5)
    paint(c, ring.astype(F32), LACE)
    paint(c, (rect_mask(["T_UP", "T_F"]) & (dist > 5) & (dist <= 6) & ((XX + YY) % 2 == 0)).astype(F32), LACE_EDGE)
    brooch(c, CX, 86, gem=(40, 30, 60))
    # pin-tuck pleats down the blouse front
    for tx in (276, 284, 305, 313):
        shade(c, (rect_mask(["T_F"]) & (XX == tx) & (YY >= 92) & (YY < 124)).astype(F32), 0.75)
    # the corset: sweetheart top, boning, crimson lacing front and back
    top_edge = 124 - 8 * np.cos(np.clip((XX - CX) / 30.0, -1.6, 1.6) * 2)
    cm = rect_mask(TORSO_RING) & (YY >= np.where(rect_mask(["T_F"]), top_edge, 118))
    lift(c, cm.astype(F32), dy=-2, sigma=1.5, strength=0.45)
    tex = fabric(seed + 1, corset, cloud=0.06, twill=0.02)
    c[cm, :3] = tex[cm]
    sheen(c, TORSO_RING, 0.25, width=0.18, y_max=202)
    for n in TORSO_RING:
        x, y, w, h = R[n]
        for bx in range(x + 8, x + w - 4, 14):
            paint(c, (cm & (XX == bx)).astype(F32), dark(corset, 2.4), 0.8)
    paint(c, outline_of(cm, 1).astype(F32), GOLD)
    lacing(c, CX, 128, 198, gap=5, step=9, col=lace_col)
    lacing(c, 491, 124, 198, gap=6, step=9, col=lace_col)
    bow(c, 491, 192, w=8, h=5, col=lace_col, tails=8, seed=seed + 2)
    # lace cuffs
    scallops(c, ARM_FACES, 446, 462, clip_end=SLEEVE_END)
    paint(c, (arms & (YY == 445)).astype(F32), LACE_EDGE)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def chapel_skirt(name="pants_f_chapel_skirt.png", cloth=(22, 18, 22), ribbon=CRIMSON, seed=931):
    hem_y = 412
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.05), hem_y, seed)
    # high waist with a row of gold buttons, soft A-line folds
    folds = (rect_mask(LEGS) & (YY < hem_y))
    fac = 1 + 0.08 * np.sin(2 * np.pi * XX / 16 + 0.4 * np.sin(YY / 11))
    c[folds, :3] = np.clip(c[folds, :3] * fac[folds, None], 0, 255)
    waistband(c, dark(cloth, 0.8), seed + 1, 178, 192)
    for by in (182, 188):
        button(c, CX - 6, by, r=1.8)
        button(c, CX + 6, by, r=1.8)
    # crimson ribbon band near the hem, a bow on the left hip
    band = rect_mask(LEGS) & (YY >= hem_y - 12) & (YY <= hem_y - 7)
    c[band, :3] = fabric(seed + 2, ribbon, cloud=0.04, twill=0.0)[band]
    shade(c, (rect_mask(LEGS) & ((YY == hem_y - 13) | (YY == hem_y - 6))).astype(F32), 0.45)
    x, y, w, h = R["LA_L"]
    bow(c, x + w / 2, 364, w=9, h=5, col=ribbon, tails=14, seed=seed + 3)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    tights(c, hem_y, SHOE_TOP, seed=seed + 4)
    mary_janes(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== 3. crimson bolero and pinafore (school)
def bolero_top(name="shirt_f_bolero_pinafore.png", jacket=(120, 12, 22), blouse=WHITE_SHIRT, bib=(22, 18, 22), seed=941):
    c = base_shirt(blouse, jacket, seed, body_tex=dict(cloud=0.05, twill=0.03), sleeve_tex=dict(cloud=0.07, twill=0.05))
    hole, dist = neck_dist()
    # pinafore bib and straps over the blouse
    bibm = poly([(262, 132), (327, 132), (329, 201), (260, 201)])
    straps = poly([(262, 74), (271, 74), (271, 132), (262, 132)]) + poly([(318, 74), (327, 74), (327, 132), (318, 132)])
    cross_b = lines([(440, 201), (540, 120)], 9) + lines([(542, 201), (442, 120)], 9)
    pin = np.clip(bibm + straps + cross_b * rect_mask(["T_B"]), 0, 1)
    lift(c, pin, dy=1, sigma=1.3, strength=0.45)
    paint(c, pin, fabric(seed + 1, bib, cloud=0.06, twill=0.04))
    shade(c, outline_of(pin > 0.5, 1).astype(F32), 0.4)
    for bx, by in ((266, 136), (323, 136)):
        button(c, bx, by, r=2.2)
    crest(c, CX, 160, w=20, h=24)
    # the bolero: cropped, open at the front, curving away from the neck
    jac = fabric(seed + 2, jacket, cloud=0.07, twill=0.05)
    edge = 126
    jm = rect_mask(["T_UP"]) | (rect_mask(["T_R", "T_L", "T_B"]) & (YY <= edge))
    for pts in ([(231, 74), (252, 74), (246, 100), (238, edge), (231, edge)],):
        jm = jm | (poly(pts) > 0.5) | (poly(mirror(pts)) > 0.5)
    jm &= ~hole
    lift(c, jm.astype(F32), dy=2, sigma=1.5, strength=0.5)
    c[jm, :3] = jac[jm]
    c[jm, 3] = 255
    sheen(c, ["T_R", "T_L", "T_B"], 0.15, width=0.2, y_max=edge + 1)
    paint(c, outline_of(jm & rect_mask(TORSO_RING), 1).astype(F32), GOLD)
    # ribbon tie at the blouse collar
    paint(c, (rect_mask(["T_F"]) & (dist <= 3)).astype(F32), blouse)
    bow(c, CX, 84, w=8, h=4, col=CRIMSON, tails=10, seed=seed + 3)
    # blouse cuffs showing under the bolero sleeves
    cuff = rect_mask(ARM_FACES) & (YY >= 444) & (YY <= SLEEVE_END)
    c[cuff, :3] = fabric(seed + 4, blouse, cloud=0.04, twill=0.02)[cuff]
    paint(c, (rect_mask(ARM_FACES) & (YY == 443)).astype(F32), GOLD)
    for bx in (127, 140, 446, 459):
        button(c, bx, 436, r=1.6)
    hem_line(c, 201, TORSO_RING, 0.5)
    clear(c, hole)
    face_seams(c, 0.55)
    return save(c, name)


def pinafore_skirt(name="pants_f_pinafore_skirt.png", cloth=(22, 18, 22), piping=CRIMSON, seed=951):
    hem_y = 404
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.05), hem_y, seed)
    pleated(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 192)), period=16, lo=0.86, hi=1.1)
    waistband(c, cloth, seed + 1, 178, 191)
    for n in ("T_R", "T_L"):
        x, y, w, h = R[n]
        button(c, x + w / 2, 185, r=2.0)
    paint(c, (rect_mask(LEGS) & (YY == hem_y - 4)).astype(F32), piping)
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.4)
    bare_legs(c, hem_y, 414)
    socks(c, 414, SHOE_TOP - 1, (26, 24, 28), bands=[(417, 418, piping)], seed=seed + 2)
    mary_janes(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== 4. gothic lolita dress (civilian)
def lolita_top(name="shirt_f_lolita_bodice.png", body=(18, 14, 18), ribbon=CRIMSON, seed=961):
    vt = dict(cloud=0.06, twill=0.02, grain=0.03)
    c = base_shirt(body, body, seed, body_tex=vt, sleeve_tex=vt)
    hole, dist = neck_dist()
    # rounded lace collar
    for sx in (-1, 1):
        flap = shape(lambda d: d.ellipse((CX + sx * 14 - 17, 70, CX + sx * 14 + 17, 98), fill=255)) * rect_mask(["T_F"])
        lift(c, flap, dy=2, sigma=1.4, strength=0.5)
        paint(c, flap, LACE)
        paint(c, outline_of(flap > 0.5, 1).astype(F32), LACE_EDGE)
    paint(c, (rect_mask(["T_UP"]) & (dist <= 6)).astype(F32), LACE)
    # ribbon lacing down the bodice, a bow at the top
    lacing(c, CX, 104, 196, gap=6, step=10, col=ribbon, eyelet=(200, 190, 176))
    bow(c, CX, 101, w=10, h=6, col=ribbon, tails=12, seed=seed + 1)
    # princess seams with tiny lace trim
    for x0 in (258, 331):
        paint(c, lines([(x0, 100), (x0 + (6 if x0 < CX else -6), 201)]), (60, 56, 60))
    # puffed shoulders, bell sleeves with two tiers of lace
    arms = rect_mask(ARM_FACES)
    puff = arms & (YY < 388)
    fold = 1 + 0.14 * np.sin(2 * np.pi * XX / 8 + 0.5 * np.sin(YY / 9))
    c[puff, :3] = np.clip(c[puff, :3] * fold[puff, None], 0, 255)
    shade(c, (arms & (YY >= 386) & (YY <= 389)).astype(F32), 0.6)
    flare = arms & (YY >= 420)
    c[flare, :3] = np.clip(c[flare, :3] * (1 + 0.1 * np.sin(2 * np.pi * XX / 10))[flare, None], 0, 255)
    paint(c, (arms & (YY >= 426) & (YY <= 429)).astype(F32), ribbon)
    scallops(c, ARM_FACES, 430, 444)
    scallops(c, ARM_FACES, 444, 460, clip_end=SLEEVE_END)
    # big bow on the back
    bow(c, 491, 150, w=22, h=12, col=ribbon, tails=40, seed=seed + 2)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def lolita_skirt(name="pants_f_lolita_skirt.png", cloth=(18, 14, 18), ribbon=CRIMSON, seed=971):
    hem_y = 408
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.06, twill=0.02), hem_y, seed)
    # two tiers of ruffles, each with a ribbon band and a lace edge
    legs = rect_mask(LEGS) & (YY < hem_y)
    c[legs, :3] = np.clip(c[legs, :3] * (1 + 0.12 * np.sin(2 * np.pi * XX / 9))[legs, None], 0, 255)
    for ty in (378, 396):
        shade(c, (rect_mask(LEGS) & (YY >= ty - 3) & (YY < ty)).astype(F32), 0.75)
        band = rect_mask(LEGS) & (YY >= ty) & (YY <= ty + 3)
        c[band, :3] = fabric(seed + ty, ribbon, cloud=0.04, twill=0.0)[band]
    waistband(c, dark(cloth, 0.8), seed + 1, 179, 188)
    bow(c, CX, 186, w=8, h=4, col=ribbon, tails=8, seed=seed + 2)
    # petticoat lace peeking out at the hem
    scallops(c, LEGS, hem_y - 4, hem_y + 8)
    # striped stockings and platform Mary Janes
    stripes(c, hem_y + 8, SHOE_TOP, (16, 14, 18), (120, 12, 22), period=6, seed=seed + 3)
    mary_janes(c, platform=True)
    clear(c, hole)
    return save(c, name)


# ================================================================== 5. oversized cable knit (civilian)
def cable_knit(seed, col):
    base = tint(fabric_detail(seed, cloud=0.05, twill=0.0, grain=0.035), col)
    ph = XX % 22
    t = (ph - 9.5) / 5.5
    inside = np.abs(t) <= 1
    braid = 1 + 0.16 * np.cos(np.pi * t) * np.sign(np.sin(YY / 4.0 + np.where(t < 0, 0, np.pi)))
    gutter = (ph == 2) | (ph == 3) | (ph == 17) | (ph == 18)
    purl = 1 - 0.07 * (((XX + YY) % 3) == 0)
    f = np.where(inside, braid, purl) * np.where(gutter, 0.78, 1.0)
    return np.clip(base * f[..., None], 0, 255)


def knit_top(name="shirt_f_cable_knit.png", yarn=(222, 208, 182), seed=981):
    c = blank()
    k = cable_knit(seed, yarn)
    m = rect_mask(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    c[m, :3] = k[m]
    c[m, 3] = 255
    hole, dist = neck_dist()
    # slouchy ribbed neck, hem and long "sweater paw" cuffs over the hands
    ring = rect_mask(["T_UP", "T_F"]) & (dist <= 7)
    d = fabric_detail(seed + 1, cloud=0.04, twill=0.0, grain=0.03, rib=0.1, rib_period=2)
    c[ring, :3] = tint(d, dark(yarn, 0.94))[ring]
    shade(c, (rect_mask(["T_UP", "T_F"]) & (dist > 7) & (dist <= 8)).astype(F32), 0.6)
    rib_band(c, TORSO_RING, 186, 201, dark(yarn, 0.92), seed=seed + 2)
    rib_band(c, ARM_FACES, 448, 470, dark(yarn, 0.92), seed=seed + 3)
    clear(c, rect_mask(ARM_FACES) & (YY > 470))
    # a small embroidered crimson crescent and stars on the chest
    paint(c, crescent(318, 122, 8, 4), (150, 16, 28))
    for sx, sy in ((330, 112), (334, 128), (306, 112)):
        paint(c, shape(lambda d: d.polygon([(sx, sy - 2.5), (sx + 1, sy), (sx, sy + 2.5), (sx - 1, sy)], fill=255)), GOLD)
    # loose drape: soft folds across the body
    body = rect_mask(TORSO_RING)
    c[body, :3] = np.clip(c[body, :3] * (1 + 0.06 * np.sin(YY / 6.0 + XX / 19.0))[body, None], 0, 255)
    clear(c, hole)
    face_seams(c, 0.65)
    return save(c, name)


MINI_SETT = [((118, 12, 22), 6), ((22, 16, 18), 4), ((190, 150, 62), 1), ((22, 16, 18), 4), ((118, 12, 22), 2), ((28, 30, 56), 3)]


def plaid_mini(name="pants_f_plaid_mini.png", seed=991):
    hem_y = 394
    c, hole = skirt_shell(plaid(MINI_SETT, seed, cloud=0.06, soft=0.4), hem_y, seed)
    pleated(c, (rect_mask(LEGS) & (YY < hem_y)) | (rect_mask(TORSO_RING) & (YY >= 190)))
    waistband(c, (22, 16, 18), seed + 1)
    chain(c, [(238, 191), (264, 197), (CX, 199), (325, 197), (351, 191)], (196, 196, 200))
    shade(c, (rect_mask(LEGS) & (YY == hem_y - 1)).astype(F32), 0.35)
    clear(c, rect_mask(LEGS) & (YY == hem_y - 1) & (XX % 8 == 0))
    tights(c, hem_y, 448, seed=seed + 2)
    combat_boots(c, 448, seed + 3, laces=(120, 12, 22), sole_top=474)
    clear(c, hole)
    return save(c, name)


# ================================================================== 6. cheer uniform (school, athletics)
def cheer_top(name="shirt_f_cheer_shell.png", body=(128, 12, 24), stripe=(18, 14, 18), seed=1001):
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.05, twill=0.01, grain=0.03))
    clear(c, rect_mask(ARM_FACES + ARM_UPS))           # sleeveless: the arms show skin
    hole, dist = neck_dist()
    vee = poly([(278, 74), (311, 74), (CX, 104)])
    paint(c, (rect_mask(["T_F"]) & (dist <= 3)).astype(F32), stripe)
    clear(c, vee > 0.5)
    paint(c, lines([(278, 74), (CX, 104), (311, 74)], 2), GOLD)
    # chevron band across the chest, black side panels with gold piping
    for off, col in ((0, stripe), (8, GOLD), (11, stripe)):
        band = lines([(231, 112 + off), (CX, 146 + off), (358, 112 + off)], 4 if col != GOLD else 2)
        paint(c, band * rect_mask(["T_F"]), col)
    for n in ("T_R", "T_L"):
        x, y, w, h = R[n]
        side = rect_mask([n]) & (np.abs(XX - (x + w / 2)) <= 12)
        c[side, :3] = fabric(seed + 1, stripe, cloud=0.04, twill=0.0)[side]
        paint(c, (rect_mask([n]) & (np.abs(XX - (x + w / 2)) == 13)).astype(F32), GOLD)
    monogram(c, CX, 172, 30, fill=(236, 214, 150), edge=(110, 76, 24), outline=stripe)
    # back: arched NIGHTMARE over a big gold NH
    arc_text(c, "NIGHTMARE", 491, 150, 56, 70, 13, (236, 214, 150), stroke_col=stripe)
    monogram(c, 491, 156, 34, fill=(236, 214, 150), edge=(110, 76, 24), outline=stripe)
    paint(c, (rect_mask(TORSO_RING) & (YY >= 195)).astype(F32), stripe)
    paint(c, (rect_mask(TORSO_RING) & (YY == 194)).astype(F32), GOLD)
    clear(c, hole)
    face_seams(c, 0.6)
    return save(c, name)


def cheer_skirt(name="pants_f_cheer_skirt.png", cloth=(18, 14, 18), insert=(128, 12, 24), seed=1011):
    hem_y = 392
    c, hole = skirt_shell(fabric(seed, cloth, cloud=0.05, twill=0.02), hem_y, seed)
    legs = rect_mask(LEGS) & (YY < hem_y)
    # inverted crimson pleats every 16 px, opening toward the hem
    open_w = np.clip((YY - 360) / 32.0, 0, 1) * 4
    ins = legs & ((XX % 16) >= 16 - open_w) & (YY > 360)
    c[ins, :3] = fabric(seed + 1, insert, cloud=0.04, twill=0.0)[ins]
    pleated(c, legs, period=16, lo=0.86, hi=1.12)
    waistband(c, insert, seed + 2, 179, 186)
    paint(c, (rect_mask(LEGS) & (YY == hem_y - 3)).astype(F32), GOLD)
    bare_legs(c, hem_y, 438)
    socks(c, 438, SHOE_TOP - 1, IVORY, bands=[(441, 442, insert)], seed=seed + 3)
    jeans_sneakers(c)
    clear(c, hole)
    return save(c, name)


# ================================================================== 7. midnight gala gown (civilian)
def lace_net(seed):
    """Sheer black lace: a fine net with brocade flowers; everything else stays see-through."""
    net = (((XX + YY) % 5) == 0) | (((XX - YY) % 5) == 0)
    flowers = damask_mask(16) > 0.4
    rng = np.random.default_rng(seed)
    gaps = rng.random((H, W)) < 0.12
    return (net | ndimage.binary_dilation(flowers, iterations=1)) & ~gaps


def gala_top(name="shirt_f_gala_bodice.png", velvet=VIOLET, seed=1021):
    c = blank()
    vel = fabric(seed, velvet, cloud=0.08, twill=0.02, grain=0.03)
    # off the shoulder: the bodice starts at a sweetheart line, sheer lace sleeves
    top_edge = np.where(rect_mask(["T_F"]), 100 - 9 * np.cos(np.clip((XX - CX) / 30.0, -1.6, 1.6) * 2), 92)
    body = rect_mask(TORSO_RING) & (YY >= top_edge)
    c[body, :3] = vel[body]
    c[body, 3] = 255
    sheen(c, TORSO_RING, 0.32, width=0.18)
    paint(c, (body & (np.abs(YY - top_edge) < 1.2)).astype(F32), GOLD)
    # sheer sleeves: a translucent black base (it blends over the skin) under a fine net and lace flowers
    sleeve = rect_mask(ARM_FACES) & (YY <= SLEEVE_END)
    c[sleeve, :3] = (18, 14, 22)
    c[sleeve, 3] = 120
    net = ((((XX + YY) % 4) == 0) | (((XX - YY) % 4) == 0)) & sleeve
    c[net, :3] = (10, 8, 12)
    c[net, 3] = 210
    flowers = (damask_mask(16) > 0.4) & sleeve
    c[flowers, :3] = (8, 6, 10)
    c[flowers, 3] = 255
    cuff = rect_mask(ARM_FACES) & (YY >= 452) & (YY <= SLEEVE_END)
    c[cuff, :3] = vel[cuff]
    c[cuff, 3] = 255
    paint(c, (rect_mask(ARM_FACES) & (YY == 452)).astype(F32), GOLD)
    # crystal brooch at the neckline, gold boning, a chain belt at the waist
    brooch(c, CX, top_edge[110, int(CX)] + 8, gem=(170, 150, 230))
    for n in TORSO_RING:
        x, y, w, h = R[n]
        for bx in range(x + 10, x + w - 6, 18):
            paint(c, (body & (XX == bx) & (YY > 120)).astype(F32), dark(velvet, 1.8), 0.7)
    chain(c, [(231, 190), (262, 196), (CX, 199), (327, 196), (358, 190)], GOLD)
    lacing(c, 491, 100, 196, gap=7, step=10, col=GOLD, eyelet=(230, 200, 120), width=1)
    return save(c, name)


def gala_skirt(name="pants_f_gala_skirt.png", velvet=VIOLET, seed=1031):
    c, hole = pants_shell(seed)
    vel = fabric(seed, velvet, cloud=0.08, twill=0.02, grain=0.03)
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(LEGS) | rect_mask(LEG_UPS) | rect_mask(["T_D"]) | rect_mask(ARM_DOWNS)
    c[m, :3] = vel[m]
    c[m, 3] = 255
    shade(c, rect_mask(["T_D"] + ARM_DOWNS).astype(F32), 0.5)
    # floor-length velvet falling in deep folds, with a black lace overlay toward the hem
    legs = rect_mask(LEGS)
    fold = 1 + 0.16 * np.sin(2 * np.pi * XX / 12 + 1.2 * noise(H, W, seed + 1, 7))
    c[legs, :3] = np.clip(c[legs, :3] * fold[legs, None], 0, 255)
    sheen(c, LEGS, 0.25, width=0.16)
    over = lace_net(seed + 2) & legs & (YY >= 430 + 6 * np.sin(XX / 7.0))
    c[over, :3] = (12, 10, 14)
    scallops(c, LEGS, 470, 482, col=(14, 12, 16), edge=(60, 50, 70))
    paint(c, (legs & (YY == 469)).astype(F32), GOLD)
    waistband(c, dark(velvet, 0.75), seed + 3, 179, 186)
    clear(c, hole)
    return save(c, name)


PAIRS = [
    (sailor_top, sailor_skirt),
    (chapel_top, chapel_skirt),
    (bolero_top, pinafore_skirt),
    (lolita_top, lolita_skirt),
    (knit_top, plaid_mini),
    (cheer_top, cheer_skirt),
    (gala_top, gala_skirt),
]

# file -> (wardrobe name, id, school?)
CATALOG = {
    "shirt_f_sailor_navy.png": ("Sailor Uniform", "sailor-uniform", True),
    "pants_f_sailor_skirt.png": ("Sailor Skirt", "sailor-skirt", True),
    "shirt_f_chapel_corset.png": ("Chapel Blouse & Corset", "chapel-corset", True),
    "pants_f_chapel_skirt.png": ("Chapel Skirt + Tights", "chapel-skirt", True),
    "shirt_f_bolero_pinafore.png": ("Crimson Bolero & Pinafore", "bolero-pinafore", True),
    "pants_f_pinafore_skirt.png": ("Pinafore Skirt", "pinafore-skirt", True),
    "shirt_f_lolita_bodice.png": ("Gothic Lolita Dress", "lolita-dress", False),
    "pants_f_lolita_skirt.png": ("Lolita Skirt + Stockings", "lolita-skirt", False),
    "shirt_f_cable_knit.png": ("Oversized Cable Knit", "cable-knit", False),
    "pants_f_plaid_mini.png": ("Plaid Mini + Boots", "plaid-mini", False),
    "shirt_f_cheer_shell.png": ("NH Cheer Uniform", "cheer-uniform", True),
    "pants_f_cheer_skirt.png": ("Cheer Skirt", "cheer-skirt", True),
    "shirt_f_gala_bodice.png": ("Midnight Gala Gown", "gala-gown", False),
    "pants_f_gala_skirt.png": ("Gala Gown Skirt", "gala-skirt", False),
}


def build():
    out = []
    with nhcloth.supersample(4):
        for s, p in PAIRS:
            out += [s(), p()]
    return out


if __name__ == "__main__":
    for f in build():
        print(f.name)
