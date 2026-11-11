"""Admin kit v2 (1.71): 8 staff outfits drawn as PBR-style materials (pbr_cloth): wool twill, velvet, satin, leather,
brass, silver, embroidery, with draped folds, raised seams and domed hardware, baked per face.
Anime-inspired archetypes in Nightmare Highschool's own style (crimson #600E1A, black, brass); all original.
    python art/clothing/tools/kit_admin2.py [names...]
"""
import sys
import numpy as np
from scipy import ndimage

import nhcloth
from nhcloth import R, W, H, TORSO_RING, ARM_FACES, ARM_UPS, ARM_DOWNS, rect_mask, shape, font
from pbr_cloth import Canvas, Mat, folds, dome, seam, topstitch, save, F32, YY, XX
from shirts_new import poly, lines, polo_hole, SLEEVE_END, mirror
from nhextra import crescent, bat, ragged_y
from kit_common import face_phase

CX = 294.5
LEGS = ARM_FACES
FRONTS, BACKS, OUTERS, INNERS = ["RA_F", "LA_F"], ["RA_B", "LA_B"], ["RA_R", "LA_L"], ["RA_L", "LA_R"]
LEG_UPS = ARM_UPS
SHOE_TOP = 451

CRIMSON = (88, 12, 24)
BRASS_C = (196, 150, 72)
SILVER_C = (206, 206, 214)


def M(names):
    return rect_mask(names).astype(F32)


def E(x0, y0, x1, y1):
    return shape(lambda d: d.ellipse((x0, y0, x1, y1), fill=255))


def ring(cx, cy, r, w=1.5):
    return np.clip(E(cx - r, cy - r, cx + r, cy + r) - E(cx - r + w, cy - r + w, cx + r - w, cy + r - w), 0, 1)


def text(txt, size, xy, fname="georgiab.ttf"):
    f = font(size, name=fname)
    return shape(lambda d: d.text(xy, txt, font=f, fill=255, anchor="mm"))


def neck():
    hole, _ = polo_hole()
    return hole, ndimage.distance_transform_edt(~hole)


# ---------------------------------------------------------------- materials
def mats(seed):
    return dict(
        wool=lambda col, s=0: Mat("wool", col, 0.62, spec=0.1, seed=seed + s, cloud=0.05),
        velvet=lambda col, s=0: Mat("velvet", col, 0.95, spec=0.02, sheen=0.38, seed=seed + s, cloud=0.03),
        satin=lambda col, s=0: Mat("satin", col, 0.24, spec=0.35, seed=seed + s, cloud=0.02),
        leather=lambda col, s=0: Mat("leather", col, 0.42, spec=0.25, seed=seed + s, cloud=0.04),
        linen=lambda col, s=0: Mat("linen", col, 0.75, spec=0.04, seed=seed + s, cloud=0.02),
        knit=lambda col, s=0: Mat("knit", col, 0.9, spec=0.02, seed=seed + s, cloud=0.03),
        thread=lambda col, s=0: Mat("embroidery", col, 0.35, spec=0.3, seed=seed + s, cloud=0.01),
        brass=Mat("brass", BRASS_C, 0.3, metal=1.0, spec=0.6, seed=seed + 50, cloud=0.03),
        silver=Mat("silver", SILVER_C, 0.22, metal=1.0, spec=0.6, seed=seed + 51, cloud=0.02),
    )


def stud(cv, mat, x, y, r=2.2, lift=0.6):
    m = E(x - r, y - r, x + r, y + r)
    cv.paint(m, mat, lift=lift)
    dome(cv, m, 0.9, blur=0.6)


def creases(cv, mask, y0, n=3, amp=0.45, spread=5):
    """Horizontal bunching (elbows, knees, ankles)."""
    m = np.clip(np.asarray(mask, F32), 0, 1)
    env = np.exp(-((YY - y0) / (spread * n * 0.38)) ** 2)
    ph = face_phase(ARM_FACES)
    # bunched, uneven creases: they bend across the face and fade toward its sides
    bend = 2.2 * np.sin(2 * np.pi * ph / 64.0 + y0) + 1.2 * np.sin(2 * np.pi * ph / 23.0)
    wav = np.sin(2 * np.pi * (YY - y0 + bend) / spread)
    side = 0.55 + 0.45 * np.sin(np.pi * np.clip(ph, 0, 63) / 63.0)
    cv.h = cv.h + amp * 0.6 * env * wav * side * m


def shield(cx, cy, w, h, inset=0):
    def fn(d):
        x0, x1 = cx - w / 2 + inset, cx + w / 2 - inset
        y0, y1 = cy - h / 2 + inset, cy + h / 2 - inset
        mid = y0 + (y1 - y0) * 0.55
        pts = [(x0, y0), (x1, y0), (x1, mid)]
        for i in range(1, 9):
            a = i / 9
            pts.append((x1 - (x1 - cx) * a, mid + (y1 - mid) * np.sin(a * np.pi / 2)))
        for i in range(1, 9):
            a = i / 9
            pts.append((cx - (cx - x0) * a, y1 - (y1 - mid) * (1 - np.cos(a * np.pi / 2))))
        pts.append((x0, mid))
        d.polygon(pts, fill=255)
    return shape(fn)


def crest(cv, mt, cx, cy, w=20, h=24, field=CRIMSON, letters=(236, 226, 196)):
    outer, inner = shield(cx, cy, w, h), shield(cx, cy, w, h, inset=2)
    cv.paint(outer, mt["thread"](BRASS_C, 7), lift=0.5)
    cv.paint(inner, mt["thread"](field, 8), lift=0.45)
    f = font(max(8, int(h * 0.36)))
    lt = shape(lambda d: (d.text((cx - w * 0.16, cy - h * 0.02), "N", font=f, fill=255, anchor="mm"),
                          d.text((cx + w * 0.16, cy + h * 0.16), "H", font=f, fill=255, anchor="mm")))
    cv.paint(lt, mt["thread"](letters, 9), lift=0.25, ride="keep")


def base_top(cv, mat, sleeve_mat=None, sleeve_end=SLEEVE_END):
    cv.paint(M(TORSO_RING + ["T_UP"]), mat, ride="flat")
    sl = M(ARM_FACES + ARM_UPS) * ((YY <= sleeve_end) | rect_mask(ARM_UPS))
    cv.paint(sl, sleeve_mat or mat, ride="flat")
    return cv


def base_pants(cv, mat, leg_end=SHOE_TOP):
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | (rect_mask(LEGS) & (YY < leg_end)) | rect_mask(LEG_UPS + ["T_D"])
    cv.paint(m.astype(F32), mat, ride="flat")
    return cv


def boots(cv, mt, top, leather=(16, 14, 16), cuff=None, buckles=0, heel=True):
    m = M(LEGS) * (YY >= top)
    cv.paint(m, mt["leather"](leather, 30), ride="flat", lift=0.2)
    creases(cv, m, 466, n=2, amp=0.35, spread=4)
    if cuff:
        cv.paint(M(LEGS) * ((YY >= top) & (YY <= top + 5)), mt["leather"](cuff, 31), lift=0.5)
    for k in range(buckles):
        sy = top + 8 + k * 9
        cv.paint(M(LEGS) * ((YY >= sy) & (YY <= sy + 2)), mt["leather"](tuple(int(v * 0.7) for v in leather), 32), lift=0.4)
        for n in OUTERS:
            x, y, w, h = R[n]
            fr = np.clip(shape(lambda d: d.rectangle((x + w * 0.6 - 3, sy - 1, x + w * 0.6 + 3, sy + 3), outline=255, width=1)), 0, 1)
            cv.paint(fr, mt["silver"], lift=0.7)
    cv.paint(M(LEGS) * (YY >= 476), mt["leather"]((26, 18, 14), 33), ride="flat", lift=0.1)
    if heel:
        cv.paint(M(BACKS) * (YY >= 472), mt["leather"]((30, 20, 16), 34), ride="flat")
    cv.paint(M(ARM_DOWNS), mt["leather"]((22, 18, 16), 35), ride="flat")


def coat_tails(cv, mt, mat, lining_mat, hem_y, seed, open_front=True, ragged=0.0, lining_px=2):
    if ragged:
        e = ragged_y(hem_y, ragged, seed, notches=0.08, depth=(4, 10))[XX]
    else:
        e = hem_y
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | (rect_mask(LEGS) & (YY < e))
    if open_front:
        m &= ~(rect_mask(["RA_F"]) & (XX >= 268)) & ~(rect_mask(["LA_F"]) & (XX <= 320))
        m &= ~(rect_mask(["T_F"]) & (np.abs(XX - CX) < 6))
    m = m.astype(F32)
    cv.paint(m, mat, lift=0.6)
    folds(cv, m * M(LEGS), period=15, amp=0.75, wobble=3, seed=seed)
    if open_front:
        for x0 in (266, 321):
            cv.paint(M(LEGS) * (np.abs(XX - x0) < lining_px * 0.6 + 0.5) * (YY < hem_y), lining_mat, lift=0.5)
    # hem lip
    hem = M(LEGS) * (np.abs(YY - (e - 1)) < 1.0) * (m > 0)
    cv.raise_(hem, 0.4)
    return m


# ================================================================== 1. Night Warden
def warden_coat(name="shirt_adm_night_warden_coat.png", seed=5001):
    mt = mats(seed)
    cv = Canvas()
    wool = mt["wool"]((28, 26, 31))
    base_top(cv, wool)
    hole, dist = neck()
    # body: a soft vertical drape and elbow creases
    folds(cv, M(TORSO_RING) * (YY > 120), period=24, amp=0.6, wobble=4, seed=seed)
    # standing collar with a brass edge
    col = (M(["T_UP"]) * (dist <= 10)) + (M(["T_F"]) * (dist <= 7))
    cv.paint(np.clip(col, 0, 1), mt["wool"]((30, 26, 32), 1), lift=0.9)
    cv.paint(M(["T_UP"]) * ((dist > 9) & (dist <= 10.5)), mt["brass"], lift=1.0)
    # double-breasted plackets: crimson satin piping, two rows of brass buttons
    for x0 in (270, 319):
        cv.paint(lines([(x0, 84), (x0, 201)], 1), mt["satin"](CRIMSON, 2), lift=0.35)
    seam(cv, [(CX, 84), (CX, 201)], 1, 0.4)
    for by in range(100, 196, 18):
        stud(cv, mt["brass"], 262, by, 2.4)
        stud(cv, mt["brass"], 327, by, 2.4)
    # belt
    belt = M(TORSO_RING) * ((YY >= 167) & (YY <= 176))
    cv.paint(belt, mt["leather"]((14, 12, 14), 3), lift=0.7)
    topstitch(cv, [(165, 168), (555, 168)], mt["thread"]((60, 50, 40), 4))
    topstitch(cv, [(165, 175), (555, 175)], mt["thread"]((60, 50, 40), 4))
    buckle = np.clip(shape(lambda d: d.rectangle((CX - 7, 165, CX + 7, 178), outline=255, width=2)), 0, 1)
    cv.paint(buckle, mt["brass"], lift=1.1)
    # half cape over the shoulders: its own drape, a crimson lining lip at the hem, brass chain clasp
    cape = (rect_mask(["T_UP"] + ARM_UPS) | (rect_mask(TORSO_RING) & (YY <= 122)) | (rect_mask(ARM_FACES) & (YY <= 388)))
    cape &= ~(rect_mask(["T_F"]) & (np.abs(XX - CX) < 11)) & ~(hole)
    cape &= ~(rect_mask(["T_UP"]) & (dist <= 10.5))
    cm = cape.astype(F32)
    cv.paint(cm, mt["wool"]((44, 38, 50), 5), lift=1.2)
    folds(cv, cm * M(TORSO_RING + ARM_FACES), period=21, amp=0.9, wobble=5, seed=seed + 1)
    hem = (ndimage.binary_dilation(cape, iterations=2) & ~cape & rect_mask(TORSO_RING + ARM_FACES)).astype(F32)
    cv.paint(hem, mt["satin"](CRIMSON, 6), lift=0.9)
    for i in range(14):
        t = i / 13
        x = 262 + (327 - 262) * t
        y = 97 + 10 * np.sin(np.pi * t)
        lk = ring(x, y, 1.9, 1.0)
        cv.paint(lk, mt["brass"], lift=1.6)
    stud(cv, mt["brass"], 262, 96, 3.0, 1.5)
    stud(cv, mt["brass"], 327, 96, 3.0, 1.5)
    crest(cv, mt, 340, 110, 18, 22)
    # back: embroidered crimson crescent and a brass key under the cape, centre vent seam
    cv.paint(crescent(491, 152, 15, 7), mt["thread"](CRIMSON, 10), lift=0.35)
    key = np.clip(lines([(491, 140), (491, 168)], 2) + lines([(491, 167), (498, 167)], 2) + lines([(491, 161), (497, 161)], 2) + ring(491, 137, 3.5, 1.6), 0, 1)
    cv.paint(key, mt["thread"](BRASS_C, 11), lift=0.4)
    seam(cv, [(491, 178), (491, 201)], 1, 0.5)
    # sleeves: crimson velvet cuffs with brass buttons, armband
    cuff = M(ARM_FACES) * ((YY >= 438) & (YY <= SLEEVE_END))
    cv.paint(cuff, mt["velvet"](CRIMSON, 12), lift=0.5)
    cv.paint(M(ARM_FACES) * (np.abs(YY - 438) < 0.8), mt["brass"], lift=0.7)
    for n in OUTERS:
        x, y, w, h = R[n]
        for by in (446, 454):
            stud(cv, mt["brass"], x + w / 2, by, 1.7)
    for n in ["LA_F", "LA_L", "LA_B", "LA_R"]:
        cv.paint(M([n]) * ((YY >= 396) & (YY <= 410)), mt["satin"](CRIMSON, 13), lift=0.5)
        cv.paint(M([n]) * ((np.abs(YY - 397) < 0.8) | (np.abs(YY - 409) < 0.8)), mt["thread"](BRASS_C, 14), lift=0.15, ride="keep")
    x, y, w, h = R["LA_L"]
    cv.paint(text("WARDEN", 8, (x + w / 2, 403.5)), mt["thread"]((236, 210, 140), 15), lift=0.2, ride="keep")
    cv.clear(hole)
    return save(cv, name)


def warden_tails(name="pants_adm_night_warden_tails.png", seed=5011):
    mt = mats(seed)
    cv = Canvas()
    base_pants(cv, mt["wool"]((30, 28, 34)))
    folds(cv, M(LEGS), period=16, amp=0.3, seed=seed)
    coat_tails(cv, mt, mt["wool"]((22, 20, 25), 1), mt["satin"](CRIMSON, 2), 420, seed)
    cv.paint(M(TORSO_RING) * ((YY >= 178) & (YY <= 183)), mt["leather"]((14, 12, 14), 3), lift=0.7)
    boots(cv, mt, 424, cuff=(28, 24, 28))
    hole = nhcloth.load("pants_jeans_a.png")[..., 3] == 0
    cv.clear(hole & (YY < 178))
    return save(cv, name)


BUILDERS = {f.__name__: f for f in (warden_coat, warden_tails)}

if __name__ == "__main__":
    import kit_admin2_more
    BUILDERS.update(kit_admin2_more.BUILDERS)
    names = sys.argv[1:] or list(BUILDERS)
    with nhcloth.supersample(4):
        for n in names:
            print(BUILDERS[n]())
