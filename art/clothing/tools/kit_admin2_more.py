"""Admin kit v2, outfits 2-8 (see kit_admin2.py for the shared helpers and outfit 1)."""
import numpy as np
from scipy import ndimage

import nhcloth
from nhcloth import R, TORSO_RING, ARM_FACES, ARM_UPS, ARM_DOWNS, rect_mask, shape
from pbr_cloth import Canvas, Mat, folds, dome, seam, topstitch, save, F32, YY, XX
from shirts_new import poly, lines, SLEEVE_END, mirror
from nhextra import crescent, ragged_y, damask_mask
from kit_common import face_phase
from kit_admin2 import (M, E, ring, text, neck, mats, stud, creases, crest, base_top, base_pants, boots, coat_tails,
                        CX, LEGS, FRONTS, BACKS, OUTERS, INNERS, LEG_UPS, CRIMSON, BRASS_C, SILVER_C)


def pants_hole(cv):
    hole = nhcloth.load("pants_jeans_a.png")[..., 3] == 0
    cv.clear(hole & (YY < 178))


# ================================================================== 2. Crimson haori over a black kimono
def haori(name="shirt_adm_crimson_haori.png", seed=5021):
    mt = mats(seed)
    cv = Canvas()
    base_top(cv, mt["satin"]((20, 18, 22), 1), mt["wool"](CRIMSON, 2))
    hole, dist = neck()
    cv.paint(np.clip(lines([(262, 74), (CX + 18, 160)], 6), 0, 1) * M(["T_F"]), mt["linen"]((226, 218, 200), 3), lift=0.5)
    cv.paint(np.clip(lines([(327, 74), (CX - 4, 152)], 8), 0, 1) * M(["T_F"]), mt["satin"]((26, 24, 28), 4), lift=0.8)
    folds(cv, M(["T_F"]) * ((XX > 252) & (XX < 337) & (YY > 150)), period=10, amp=0.35, seed=seed)
    hm = rect_mask(["T_R", "T_L", "T_B", "T_UP"]) | (rect_mask(["T_F"]) & ((XX < 252) | (XX > 337)))
    hm = (hm & ~hole).astype(F32)
    cv.paint(hm, mt["wool"](CRIMSON, 5), lift=0.9)
    folds(cv, hm * M(TORSO_RING), period=26, amp=0.7, wobble=5, seed=seed + 1)
    folds(cv, M(ARM_FACES), period=20, amp=0.6, wobble=6, seed=seed + 2)
    for x0 in (249, 340):
        cv.paint(lines([(x0, 74), (x0, 201)], 6) * M(["T_F"]), mt["satin"]((16, 14, 16), 6), lift=1.1)
    cv.paint(M(["T_UP"]) * (dist <= 7), mt["satin"]((16, 14, 16), 6), lift=1.0)
    # a band of brass-thread crescents and black stepped blocks along every hem of the haori
    for n in TORSO_RING + ARM_FACES:
        x, y, w, h = R[n]
        yb = 174 if n in TORSO_RING else 432
        okm = (hm if n in TORSO_RING else M([n])) * M([n])
        for k in range(2):
            cv.paint(crescent(x + w * (0.27 + 0.46 * k), yb + 7, 5, 2.5) * okm, mt["thread"](BRASS_C, 7), lift=0.35)
        ph = face_phase([n])
        tri = ((ph % 16) - 8) ** 2 * 0.5 < (YY - (yb + 16)) * 4
        blk = M([n]) * okm * (YY >= yb + 16) * tri * (YY < (201 if n in TORSO_RING else SLEEVE_END - 4))
        cv.paint(blk, mt["satin"]((18, 14, 18), 8), lift=0.2)
    obi = M(["T_F"]) * ((YY >= 164) & (YY <= 182) & (XX >= 252) & (XX <= 337))
    cv.paint(obi, mt["satin"]((40, 34, 44), 9), lift=0.9)
    cv.paint(lines([(253, 173), (336, 173)], 2), mt["thread"](BRASS_C, 10), lift=1.2)
    cv.paint(ring(CX, 173, 4.5, 2.0), mt["thread"](BRASS_C, 10), lift=1.5)
    cv.paint(np.clip(ring(491, 110, 15, 2.2) + crescent(491, 110, 9, 4), 0, 1), mt["thread"]((14, 12, 14), 11), lift=0.35)
    cv.paint(M(ARM_FACES) * ((YY >= 452) & (YY <= SLEEVE_END)), mt["satin"]((16, 14, 16), 12), lift=0.6)
    cv.clear(hole)
    return save(cv, name)


def hakama(name="pants_adm_hakama.png", seed=5031):
    mt = mats(seed)
    cv = Canvas()
    hem_y = 452
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | (rect_mask(LEGS) & (YY < hem_y)) | rect_mask(LEG_UPS + ["T_D"])
    cv.paint(m.astype(F32), mt["wool"]((32, 30, 36)), ride="flat")
    ph = face_phase(LEGS)
    pl = ((ph + 8) % 16) / 15.0
    cv.h = cv.h + M(LEGS) * (YY < hem_y) * (pl * 1.6 - 0.8)
    for yy in (181, 182, 188, 189):
        cv.paint(M(TORSO_RING) * (np.abs(YY - yy) < 0.6), mt["satin"](CRIMSON, 1), lift=0.4)
    cv.paint(np.clip(lines([(CX - 6, 190), (CX - 9, 214)], 3) + lines([(CX + 6, 190), (CX + 10, 212)], 3), 0, 1), mt["satin"](CRIMSON, 2), lift=0.8)
    for n in OUTERS:
        x, y, w, h = R[n]
        cv.clear(poly([(x + w / 2 - 1, 355), (x + w / 2 + 1, 355), (x + w / 2 + 3, 382), (x + w / 2 - 3, 382)]))
    boots(cv, mt, hem_y, leather=(18, 16, 18), heel=False)
    for n in FRONTS:
        x, y, w, h = R[n]
        seam(cv, [(x + w * 0.4, 464), (x + w * 0.4, 482)], 1, 0.6)
    for n in INNERS:
        x, y, w, h = R[n]
        for by in (458, 466):
            stud(cv, mt["brass"], x + w / 2, by, 1.4)
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 3. Exorcist
def exorcist_coat(name="shirt_adm_exorcist_coat.png", seed=5041):
    mt = mats(seed)
    cv = Canvas()
    base_top(cv, mt["wool"]((22, 20, 26)))
    hole, dist = neck()
    folds(cv, M(TORSO_RING) * (YY > 110), period=26, amp=0.55, seed=seed)
    col = np.clip(M(["T_UP"]) * (dist <= 11) + M(["T_F"]) * (dist <= 8), 0, 1)
    cv.paint(col, mt["wool"]((30, 28, 34), 1), lift=1.0)
    cv.paint(M(["T_UP"]) * ((dist > 10) & (dist <= 11.5)), mt["silver"], lift=1.1)
    pk = M(["T_F"]) * ((XX >= CX + 8) & (XX <= CX + 20) & (YY >= 84))
    cv.paint(pk, mt["wool"]((26, 24, 30), 2), lift=0.6)
    cv.paint(lines([(CX + 8, 84), (CX + 8, 201)], 1), mt["silver"], lift=0.8)
    for by in range(96, 196, 14):
        cl = np.clip(shape(lambda d: d.rounded_rectangle((CX + 9, by - 2, CX + 19, by + 2), 2, fill=255)), 0, 1)
        cv.paint(cl, mt["silver"], lift=1.0)
        dome(cv, cl, 0.6, blur=0.5)
    pts = [(262, 82), (266, 110), (276, 132), (CX, 140)]
    bone = Mat("linen", (228, 220, 196), 0.45, spec=0.3, seed=seed + 20)
    for i in range(20):
        t = i / 19
        k = min(int(t * 3), 2)
        a, b = pts[k], pts[k + 1]
        u = t * 3 - k
        stud(cv, bone, a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, 1.7, 1.0)
    cr = np.clip(shape(lambda d: (d.rectangle((CX - 1.5, 142, CX + 1.5, 162), fill=255), d.rectangle((CX - 6, 147, CX + 6, 150), fill=255))), 0, 1)
    cv.paint(cr, mt["brass"], lift=1.4)
    dome(cv, cr, 0.5, blur=0.5)
    sash = M(TORSO_RING) * ((YY >= 171) & (YY <= 182))
    cv.paint(sash, mt["satin"](CRIMSON, 3), lift=0.8)
    folds(cv, sash, period=7, amp=0.3, wobble=0.5, seed=seed + 3)
    x, y, w, h = R["T_L"]
    cv.paint(np.clip(lines([(x + 20, 182), (x + 16, 201)], 6) + lines([(x + 32, 182), (x + 36, 201)], 6), 0, 1), mt["satin"](CRIMSON, 3), lift=1.0)
    cv.paint(np.clip(ring(491, 126, 28, 2.0) + ring(491, 126, 22, 1.0), 0, 1), mt["thread"](SILVER_C, 4), lift=0.35)
    cr2 = np.clip(shape(lambda d: (d.rectangle((489, 104, 493, 150), fill=255), d.rectangle((477, 114, 505, 118), fill=255))), 0, 1)
    cv.paint(cr2, mt["thread"](SILVER_C, 4), lift=0.4)
    cv.paint(crescent(491, 166, 8, 4), mt["thread"](SILVER_C, 4), lift=0.35)
    seam(cv, [(491, 178), (491, 201)], 1, 0.5)
    cv.paint(M(ARM_FACES) * ((YY >= 443) & (YY <= 449)), mt["satin"](CRIMSON, 5), lift=0.5)
    cv.paint(M(ARM_FACES) * ((np.abs(YY - 442.5) < 0.7) | (np.abs(YY - 449.5) < 0.7)), mt["silver"], lift=0.7)
    cv.clear(hole)
    return save(cv, name)


def exorcist_trousers(name="pants_adm_exorcist_trousers.png", seed=5051):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((26, 24, 30)))
    coat_tails(cv, mt, mt["wool"]((22, 20, 26), 1), mt["silver"], 398, seed)
    cv.paint(M(TORSO_RING) * ((YY >= 178) & (YY <= 184)), mt["satin"](CRIMSON, 2), lift=0.7)
    boots(cv, mt, 418, buckles=3)
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 4. Reaper
def _wraps(cv, mt, mask, col, seed):
    cv.paint(mask, mt["linen"](col, seed), ride="flat")
    ph = face_phase(ARM_FACES)
    cv.h = cv.h + mask * 0.5 * np.sin(2 * np.pi * (YY + ph * 0.35) / 5)


def reaper_cloak(name="shirt_adm_reaper_cloak.png", seed=5061):
    mt = mats(seed)
    cv = Canvas()
    cloak = Mat("wool", (22, 20, 24), 0.9, spec=0.04, seed=seed, cloud=0.09)
    base_top(cv, cloak)
    hole, dist = neck()
    folds(cv, M(TORSO_RING + ARM_FACES), period=18, amp=0.9, wobble=6, seed=seed)
    flap = E(440, 30, 542, 130) * M(["T_B"])
    cv.paint(flap, cloak, lift=1.4)
    folds(cv, flap, period=12, amp=0.6, wobble=2, seed=seed + 1)
    cv.paint(flap * (YY <= 82), mt["velvet"](CRIMSON, 1), lift=1.2)
    cv.paint(M(["T_UP", "T_F"]) * (dist <= 8), mt["velvet"](CRIMSON, 1), lift=0.9)
    tunic = poly([(268, 84), (321, 84), (329, 201), (260, 201)]) * M(["T_F"])
    cv.paint(tunic, mt["linen"]((36, 34, 38), 2), ride="flat")
    for pts in ([(266, 82), (258, 201)], [(323, 82), (331, 201)]):
        cv.paint(lines(pts, 2), mt["velvet"](CRIMSON, 1), lift=1.0)
    strap = np.clip(lines([(268, 112), (321, 186)], 5), 0, 1) * M(["T_F"])
    cv.paint(strap, mt["leather"]((44, 30, 22), 3), lift=0.7)
    topstitch(cv, [(268, 110), (321, 184)], mt["thread"]((90, 70, 50), 4))
    sk = np.clip(E(CX - 6, 86, CX + 6, 97) + shape(lambda d: d.rectangle((CX - 3.5, 95, CX + 3.5, 101), fill=255)), 0, 1)
    cv.paint(sk, mt["brass"], lift=1.3)
    dome(cv, sk, 0.7, blur=0.7)
    for ex in (CX - 2.8, CX + 2.8):
        cv.paint(E(ex - 1.6, 89.5, ex + 1.6, 93), Mat("satin", (10, 8, 8), 0.5, seed=seed + 5), lift=0.6, ride="keep")
    for a, b in (((268, 96), (CX - 7, 93)), ((CX + 7, 93), (321, 96))):
        for i in range(6):
            t = i / 5
            cv.paint(ring(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 1.8, 0.9), mt["brass"], lift=1.2)
    e = ragged_y(440, 5, seed + 3, notches=0.1, depth=(4, 9))[XX]
    _wraps(cv, mt, M(ARM_FACES) * (YY > e) * (YY <= SLEEVE_END), (88, 80, 72), 6)
    cv.raise_(M(ARM_FACES) * (np.abs(YY - e) < 1.2), 0.5)
    cv.clear(hole)
    return save(cv, name)


def reaper_hem(name="pants_adm_reaper_hem.png", seed=5071):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((24, 22, 26)))
    cloak = Mat("wool", (22, 20, 24), 0.9, spec=0.04, seed=seed, cloud=0.09)
    coat_tails(cv, mt, cloak, mt["velvet"](CRIMSON, 1), 436, seed, ragged=7)
    _wraps(cv, mt, M(LEGS) * (YY >= 446), (80, 72, 66), 2)
    cv.paint(M(LEGS) * (YY >= 474), mt["leather"]((24, 18, 14), 3), ride="flat")
    cv.paint(M(ARM_DOWNS), mt["leather"]((24, 18, 14), 3), ride="flat")
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 5. Council Captain
def captain_coat(name="shirt_adm_council_captain.png", seed=5081):
    mt = mats(seed)
    cv = Canvas()
    base_top(cv, mt["wool"]((74, 11, 21)))
    hole, dist = neck()
    folds(cv, M(TORSO_RING) * (YY > 130), period=24, amp=0.55, seed=seed)
    cv.paint(poly([(270, 74), (319, 74), (CX, 132)]) * M(["T_F"]), mt["linen"]((232, 226, 212), 1), ride="flat")
    for i in range(6):
        y = 86 + i * 6
        wd = 6 + i * 1.3
        cv.paint(E(CX - wd, y - 3, CX + wd, y + 5), mt["satin"]((22, 18, 24), 2), lift=0.8 + i * 0.05)
    lap = [(270, 74), (CX - 1, 132), (284, 138), (252, 102), (256, 94), (250, 90), (258, 74)]
    for pts in (lap, mirror(lap)):
        cv.paint(poly(pts), mt["velvet"]((20, 16, 22), 3), lift=1.0)
        cv.paint(lines(pts[2:] + [pts[0]], 1), mt["brass"], lift=1.2)
    for k in range(3):
        cord = shape(lambda d: d.arc((236 + k * 3, 84 + k * 2, 284 - k * 2, 150 + k * 6), 20, 160, fill=255, width=2)) * M(["T_F"])
        cv.paint(cord, mt["brass"], lift=1.5 + k * 0.1)
        dome(cv, cord, 0.4, blur=0.4)
    cv.paint(lines([(240, 116), (240, 130)], 3), mt["brass"], lift=1.6)
    for by in (146, 166, 186):
        stud(cv, mt["brass"], CX - 6, by, 2.3)
    for n in ARM_UPS:
        x, y, w, h = R[n]
        ep = M([n]) * ((XX >= x + 12) & (XX <= x + w - 12))
        cv.paint(ep, mt["velvet"]((22, 18, 24), 4), lift=1.0)
        cv.paint(ep * ((np.abs(XX - (x + 12)) < 1) | (np.abs(XX - (x + w - 12)) < 1)), mt["brass"], lift=1.2)
        cv.paint(M([n]) * (YY >= y + h - 10) * ((XX >= x + 12) & (XX <= x + w - 12)) * ((XX % 2) == 0), mt["brass"], lift=1.3)
    for n in ["LA_F", "LA_L", "LA_B", "LA_R"]:
        cv.paint(M([n]) * ((YY >= 372) & (YY <= 386)), mt["satin"]((20, 16, 22), 5), lift=0.5)
        cv.paint(M([n]) * ((np.abs(YY - 373) < 0.8) | (np.abs(YY - 385) < 0.8)), mt["thread"](BRASS_C, 6), lift=0.15, ride="keep")
    x, y, w, h = R["LA_L"]
    cv.paint(text("COUNCIL", 8, (x + w / 2, 379.5)), mt["thread"]((236, 210, 140), 6), lift=0.2, ride="keep")
    crest(cv, mt, 491, 128, 30, 36, field=(20, 16, 22))
    seam(cv, [(491, 178), (491, 201)], 1, 0.5)
    cv.paint(M(ARM_FACES) * ((YY >= 440) & (YY <= SLEEVE_END)), mt["velvet"]((20, 16, 22), 7), lift=0.5)
    for yy in (441, 446):
        cv.paint(M(ARM_FACES) * (np.abs(YY - yy) < 0.7), mt["brass"], lift=0.7)
    cv.clear(hole)
    return save(cv, name)


def captain_slacks(name="pants_adm_captain_riding.png", seed=5091):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((26, 24, 30)))
    coat_tails(cv, mt, mt["wool"]((74, 11, 21), 1), mt["velvet"]((20, 16, 22), 2), 410, seed)
    for n in OUTERS:
        x, y, w, h = R[n]
        cv.paint(M([n]) * ((YY >= 410) & (YY < 430)) * (np.abs(XX - (x + w / 2)) <= 1), mt["satin"](CRIMSON, 3), lift=0.3)
    boots(cv, mt, 430, cuff=CRIMSON)
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 6. Shadow Ops
def shadow_ops(name="shirt_adm_shadow_ops.png", seed=5101):
    mt = mats(seed)
    cv = Canvas()
    shell = Mat("satin", (28, 28, 32), 0.5, spec=0.15, seed=seed, cloud=0.03)    # coated nylon
    base_top(cv, shell)
    hole, dist = neck()
    folds(cv, M(TORSO_RING + ARM_FACES), period=14, amp=0.45, wobble=3, seed=seed)
    col = np.clip(M(["T_UP"]) * (dist <= 12) + M(["T_F"]) * (dist <= 9), 0, 1)
    cv.paint(col, Mat("satin", (18, 18, 22), 0.55, spec=0.12, seed=seed + 1), lift=1.0)
    cv.paint(M(["T_UP"]) * ((dist > 11) & (dist <= 12.5)), mt["satin"](CRIMSON, 2), lift=1.1)
    zpath = [(CX + 10, 86), (CX - 6, 140), (CX - 6, 201)]
    cv.paint(np.clip(lines(zpath, 3), 0, 1), Mat("leather", (30, 26, 24), 0.6, seed=seed + 3), lift=0.6)
    cv.paint(np.clip(shape(lambda d: nhcloth.dashed_poly(d, zpath, on=1, off=1, fill=255)), 0, 1), mt["satin"]((150, 16, 28), 4), lift=0.8)
    web = Mat("knit", (14, 14, 16), 0.7, spec=0.05, seed=seed + 5)
    strap = np.clip(lines([(236, 84), (CX, 150)], 5) + lines([(353, 84), (CX, 150)], 5) + lines([(CX, 150), (CX, 201)], 5), 0, 1) * M(["T_F"])
    cv.paint(strap, web, lift=0.9)
    cv.paint(np.clip(shape(lambda d: d.rectangle((CX - 6, 145, CX + 6, 156), outline=255, width=2)), 0, 1), mt["brass"], lift=1.4)
    pk = M(["T_F"]) * ((XX >= 240) & (XX <= 262) & (YY >= 160) & (YY <= 186))
    cv.paint(pk, shell, lift=0.8)
    dome(cv, pk, 0.4, blur=1.5)
    cv.paint(pk * (YY <= 164), mt["satin"](CRIMSON, 6), lift=1.0)
    cv.paint(np.clip(lines([(440, 80), (542, 196)], 5) + lines([(542, 80), (440, 196)], 5), 0, 1) * M(["T_B"]), web, lift=0.9)
    cv.paint(text("NH-00", 10, (491, 100), "arialbd.ttf"), mt["satin"]((150, 16, 28), 7), lift=0.2, ride="keep")
    for n in ARM_FACES:
        for sy in (410, 428):
            cv.paint(M([n]) * ((YY >= sy) & (YY <= sy + 3)), web, lift=0.8)
    for n in OUTERS:
        x, y, w, h = R[n]
        for sy in (410, 428):
            cv.paint(np.clip(shape(lambda d: d.rectangle((x + w / 2 - 3, sy - 1, x + w / 2 + 3, sy + 4), outline=255)), 0, 1), mt["silver"], lift=1.2)
        cv.paint(M([n]) * ((YY >= 360) & (YY <= 400)) * (np.abs(XX - (x + w / 2)) <= 6), mt["satin"](CRIMSON, 8), lift=0.3)
    cv.paint(M(ARM_FACES) * ((YY >= 448) & (YY <= SLEEVE_END)), mt["knit"]((18, 18, 22), 9), lift=0.4)
    cv.clear(hole)
    return save(cv, name)


def shadow_cargo(name="pants_adm_shadow_cargo.png", seed=5111):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, Mat("linen", (34, 34, 38), 0.7, spec=0.06, seed=seed), leg_end=440)
    folds(cv, M(LEGS), period=16, amp=0.5, seed=seed)
    creases(cv, M(LEGS), 430, n=2, amp=0.5, spread=4)
    web = Mat("knit", (14, 14, 16), 0.7, spec=0.05, seed=seed + 5)
    for n in OUTERS:
        x, y, w, h = R[n]
        pk = M([n]) * ((XX >= x + 10) & (XX <= x + w - 10) & (YY >= 380) & (YY <= 408))
        cv.paint(pk, Mat("linen", (38, 38, 42), 0.7, seed=seed + 1), lift=0.8)
        dome(cv, pk, 0.5, blur=1.5)
        stud(cv, mt["brass"], x + w / 2, 384, 1.5)
    for n in LEGS:
        for sy in (372, 420):
            cv.paint(M([n]) * ((YY >= sy) & (YY <= sy + 3)), web, lift=0.8)
    for n in FRONTS:
        x, y, w, h = R[n]
        cv.paint(np.clip(shape(lambda d: d.rectangle((x + w / 2 - 3, 371, x + w / 2 + 3, 376), outline=255)), 0, 1), mt["silver"], lift=1.2)
    cv.paint(M(TORSO_RING) * ((YY >= 179) & (YY <= 188)), web, lift=0.7)
    cv.paint(np.clip(lines([(240, 192), (236, 214), (228, 230)], 3), 0, 1), mt["satin"](CRIMSON, 2), lift=1.0)
    boots(cv, mt, 440, leather=(14, 14, 16))
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 7. Midnight Lord
def tailcoat(name="shirt_adm_midnight_tailcoat.png", seed=5121):
    mt = mats(seed)
    cv = Canvas()
    base_top(cv, mt["velvet"]((26, 20, 30)))
    hole, dist = neck()
    folds(cv, M(TORSO_RING + ARM_FACES), period=22, amp=0.5, seed=seed)
    wc = poly([(256, 74), (333, 74), (337, 201), (252, 201)]) * M(["T_F"])
    cv.paint(wc, mt["satin"](CRIMSON, 1), ride="flat", lift=0.3)
    dm = damask_mask(16) * wc * (YY > 120)
    cv.raise_(dm, 0.35)
    cv.tint(dm, 1.25)
    cv.paint(poly([(272, 74), (317, 74), (CX, 120)]) * M(["T_F"]), mt["linen"]((234, 228, 214), 2), ride="flat")
    for i in range(6):
        y = 84 + i * 6
        wd = 6 + i * 1.3
        cv.paint(E(CX - wd, y - 3, CX + wd, y + 5), mt["linen"]((236, 230, 216), 3), lift=0.8 + i * 0.05)
    cv.paint(E(CX - 4.5, 77.5, CX + 4.5, 86.5), mt["brass"], lift=1.6)
    gem = E(CX - 3, 79, CX + 3, 85)
    cv.paint(gem, Mat("satin", (150, 10, 24), 0.08, spec=0.9, seed=seed + 4), lift=2.0)
    dome(cv, gem, 0.8, blur=0.5)
    for by in range(130, 196, 12):
        stud(cv, mt["brass"], CX, by, 1.6)
    for i in range(10):
        t = i / 9
        cv.paint(ring(CX + 2 + 30 * t, 150 + 8 * np.sin(np.pi * t), 1.6, 0.8), mt["brass"], lift=1.0)
    for pts in ([(256, 74), (252, 201)], [(333, 74), (337, 201)]):
        cv.paint(lines(pts, 3), mt["satin"]((40, 32, 44), 5), lift=0.9)
    cape = np.clip(M(["T_UP"]) * (dist > 6) + M(["T_B"]) * (YY <= 92), 0, 1)
    cv.paint(cape, mt["velvet"]((14, 10, 16), 6), lift=1.4)
    cv.paint(M(["T_B"]) * ((YY >= 90) & (YY <= 93)), mt["satin"](CRIMSON, 7), lift=1.5)
    cv.paint(M(["T_UP"]) * ((dist > 6) & (dist <= 8)), mt["satin"](CRIMSON, 7), lift=1.5)
    stud(cv, mt["brass"], 478, 176, 2.0)
    stud(cv, mt["brass"], 504, 176, 2.0)
    seam(cv, [(491, 176), (491, 201)], 1, 0.6)
    lace = Mat("lace", (236, 230, 216), 0.7, seed=seed + 8)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for sx in range(x, x + w, 8):
            cv.paint(E(sx - 1, 448, sx + 9, 462) * M([n]) * (YY <= SLEEVE_END), lace, lift=0.6)
    cv.clear(hole)
    return save(cv, name)


def tailcoat_tails(name="pants_adm_midnight_tails.png", seed=5131):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((30, 28, 34)))
    folds(cv, M(LEGS), period=18, amp=0.3, seed=seed)
    tail = (rect_mask(BACKS + ["T_B"]) & (YY >= 178)) & ((YY < 432) | rect_mask(["T_B"]))
    tail |= rect_mask(OUTERS + INNERS) & (YY < 420) & (face_phase(OUTERS + INNERS) > 40)
    tm = tail.astype(F32)
    cv.paint(tm, mt["velvet"]((26, 20, 30), 1), lift=0.8)
    folds(cv, tm * M(LEGS), period=14, amp=0.6, seed=seed + 1)
    cv.paint(M(BACKS) * (np.abs(YY - 430) < 0.8), mt["satin"](CRIMSON, 2), lift=1.0)
    boots(cv, mt, 432, cuff=CRIMSON)
    pants_hole(cv)
    return save(cv, name)


# ================================================================== 8. Duelist
def duelist(name="shirt_adm_duelist.png", seed=5141):
    mt = mats(seed)
    cv = Canvas()
    base_top(cv, mt["linen"]((36, 34, 40)), mt["wool"]((26, 24, 28), 1))
    hole, dist = neck()
    crop = 150
    jm = M(TORSO_RING + ["T_UP"]) * (YY <= crop) * (1 - M(["T_F"]) * (np.abs(XX - CX) < 4)) * (~hole)
    cv.paint(jm, mt["wool"]((26, 24, 28), 1), lift=0.8)
    cv.paint(M(TORSO_RING) * (np.abs(YY - crop) < 0.8), mt["brass"], lift=1.0)
    folds(cv, M(TORSO_RING) * (YY > crop), period=12, amp=0.4, seed=seed)
    col = np.clip(M(["T_UP"]) * (dist <= 10) + M(["T_F"]) * (dist <= 7), 0, 1)
    cv.paint(col, mt["wool"]((32, 28, 34), 2), lift=1.1)
    cv.paint(M(["T_UP"]) * ((dist > 9) & (dist <= 10.5)), mt["brass"], lift=1.2)
    for by in (96, 112, 128, 144):
        stud(cv, mt["brass"], CX - 6, by, 1.9)
        stud(cv, mt["brass"], CX + 6, by, 1.9)
        cv.paint(lines([(CX - 6, by), (CX + 6, by)], 1), mt["brass"], lift=1.0)
    arm = ["LA_UP", "LA_F", "LA_L", "LA_B", "LA_R"]
    cape = rect_mask([arm[0]]) | (rect_mask(arm[1:]) & (YY <= 400)) | (rect_mask(["T_L"]) & (YY <= 170))
    cape |= poly([(358, 74), (327, 74), (358, 140)]) > 0.5
    cape |= poly([(427, 74), (462, 74), (427, 150)]) > 0.5
    cm = cape.astype(F32)
    cv.paint(cm, mt["velvet"]((88, 12, 30), 3), lift=1.5)
    folds(cv, cm * M(TORSO_RING + ARM_FACES), period=16, amp=0.9, wobble=4, seed=seed + 1)
    hem = (ndimage.binary_dilation(cape, iterations=1) & ~cape & rect_mask(TORSO_RING + ARM_FACES)).astype(F32)
    cv.paint(hem, mt["brass"], lift=1.4)
    for pts in ([(231, 176), (358, 192)], [(231, 194), (358, 178)]):
        cv.paint(np.clip(lines(pts, 4), 0, 1) * M(["T_F"]), mt["leather"]((50, 34, 24), 4), lift=0.9)
    for n in ("T_R", "T_L", "T_B"):
        cv.paint(M([n]) * ((YY >= 180) & (YY <= 186)), mt["leather"]((50, 34, 24), 4), lift=0.9)
    cv.paint(np.clip(shape(lambda d: d.rectangle((CX - 5, 180, CX + 5, 189), outline=255, width=2)), 0, 1), mt["brass"], lift=1.4)
    cv.paint(M(ARM_FACES) * ((YY >= 430) & (YY <= SLEEVE_END)), mt["leather"]((18, 16, 18), 5), lift=0.7)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for sx in range(x + 8, x + w - 4, 12):
            stud(cv, mt["brass"], sx, 438, 1.4)
    cv.clear(hole)
    return save(cv, name)


def duelist_breeches(name="pants_adm_duelist_breeches.png", seed=5151):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((38, 36, 42)))
    folds(cv, M(LEGS) * (YY < 392), period=18, amp=0.4, seed=seed)
    for n in OUTERS:
        x, y, w, h = R[n]
        cv.paint(M([n]) * (YY < 392) * (np.abs(XX - (x + w / 2)) <= 1), mt["satin"](CRIMSON, 1), lift=0.3)
    cv.paint(M(TORSO_RING) * ((YY >= 180) & (YY <= 188)), mt["leather"]((50, 34, 24), 2), lift=0.8)
    boots(cv, mt, 392, buckles=2, cuff=(28, 24, 28))
    pants_hole(cv)
    return save(cv, name)


BUILDERS = {f.__name__: f for f in (haori, hakama, exorcist_coat, exorcist_trousers, reaper_cloak, reaper_hem,
                                    captain_coat, captain_slacks, shadow_ops, shadow_cargo, tailcoat, tailcoat_tails,
                                    duelist, duelist_breeches)}
