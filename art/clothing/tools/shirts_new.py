"""New shirt pieces drawn on the classic layout, in the style of the sources."""
import numpy as np
from scipy import ndimage

from nhcloth import *  # noqa: F401,F403
from recolors import MONO, polo_parts, vest_parts, make_polo

YY, XX = np.mgrid[0:H, 0:W]
CX = 294.5            # centre line of the torso front
SLEEVE_END = 460      # sources keep the sleeves opaque down to this row


def mirror(pts):
    return [(2 * CX - x, y) for x, y in pts]


def poly(pts):
    return shape(lambda d: d.polygon(pts, fill=255))


def lines(pts, width=1, closed=False):
    p = list(pts) + ([pts[0]] if closed else [])
    return shape(lambda d: d.line(p, fill=255, width=width))


def dash(pts, on=3, off=2):
    return shape(lambda d: dashed_poly(d, pts, on=on, off=off))


def button(c, x, y, r=2.6, col=GOLD):
    paint(c, shape(lambda d: d.ellipse((x - r - 1, y - r - 1, x + r + 1, y + r + 1), fill=255)), (14, 10, 8))
    paint(c, shape(lambda d: d.ellipse((x - r, y - r, x + r, y + r), fill=255)), col)
    paint(c, shape(lambda d: d.point((x - 1, y - 1), fill=255)), (250, 232, 170))


def base_shirt(body_col, sleeve_col, seed, body_tex=None, sleeve_tex=None, sleeve_end=SLEEVE_END):
    c = blank()
    fill_regions(c, TORSO_RING + ["T_UP"], body_col, seed, **(body_tex or {}))
    fill_regions(c, ARM_FACES + ARM_UPS, sleeve_col, seed + 5, **(sleeve_tex or {}))
    clear(c, rect_mask(ARM_FACES) & (YY > sleeve_end))
    return c


def polo_hole():
    P = load("shirt_maroon_polo_khaki.png")
    return hole_mask(P), P


def face_seams(c, factor=0.55):
    """No-op (2026-11-04). It used to darken the outermost pixel of every face, which
    showed in game as a dark border round each body part. Kept so callers still work."""
    return c
    m = np.zeros((H, W), bool)
    for n in TORSO_RING + ARM_FACES:
        x, y, w, h = R[n]
        m[y:y + h, x] = True
        m[y:y + h, x + w - 1] = True
    m &= c[..., 3] > 0
    return shade(c, m.astype(np.float32) * 0.6, factor)


def hem_line(c, y, names, factor=0.5):
    m = rect_mask(names) & (YY == y) & (c[..., 3] > 0)
    return shade(c, m.astype(np.float32), factor)


def rib_band(c, names, y0, y1, col, stripes=(), seed=0):
    """Ribbed knit band (vertical ribs) with optional horizontal stripe rows."""
    m = rect_mask(names) & (YY >= y0) & (YY <= y1)
    d = fabric_detail(seed, cloud=0.04, twill=0.0, grain=0.03, rib=0.09, rib_period=2)
    c[m, :3] = tint(d, col)[m]
    c[m, 3] = 255
    for (sy0, sy1, scol) in stripes:
        sm = rect_mask(names) & (YY >= sy0) & (YY <= sy1)
        c[sm, :3] = tint(d, scol)[sm]
    shade(c, (m & ((YY == y0) | (YY == y1))).astype(np.float32), 0.55)
    return c


# ================================================================== blazer
def blazer(name="shirt_blazer_black_crest.png", body=(24, 22, 26), piping=CRIMSON, tie=CRIMSON, seed=11):
    c = base_shirt(body, body, seed, body_tex=dict(cloud=0.07, twill=0.06), sleeve_tex=dict(cloud=0.07, twill=0.06))
    hole, P = polo_hole()
    pp = polo_parts()
    # white shirt V and the polo collar shape as a shirt collar
    vee = poly([(258, 74), (331, 74), (CX, 150)])
    shirt = tint(fabric_detail(seed + 1, cloud=0.05, twill=0.03), WHITE_SHIRT)
    paint(c, vee, shirt)
    collar = pp["grey"] & (YY <= 104) & rect_mask(["T_UP", "T_F"]) & ~((XX >= 283) & (XX <= 306) & (YY >= 84))
    paint(c, collar.astype(np.float32), recolor(pp["src"], collar, WHITE_SHIRT, 12)[..., :3])
    shade(c, outline_of(collar, 1).astype(np.float32), 0.45)
    # tie
    knot = poly([(289, 86), (300, 86), (298, 95), (291, 95)])
    blade = poly([(291, 95), (298, 95), (302, 134), (CX, 143), (287, 134)])
    tie_m = np.clip(knot + blade, 0, 1)
    lift(c, tie_m, dx=1, dy=1, sigma=1.2, strength=0.5)
    tie_col = tint(fabric_detail(seed + 2, cloud=0.05, twill=0.0), tie)
    paint(c, tie_m, tie_col)
    stripe = (((XX + YY) // 3) % 4 == 0).astype(np.float32) * blade
    paint(c, stripe, GOLD, 0.9)
    shade(c, outline_of(tie_m > 0.5, 1).astype(np.float32), 0.35)
    # lapels
    lap = [(262, 74), (CX, 146), (284, 146), (252, 100), (256, 93), (248, 90), (253, 74)]
    lap_col = tint(fabric_detail(seed + 3, cloud=0.05, twill=0.02), tuple(int(v * 1.25) + 6 for v in body))
    for pts in (lap, mirror(lap)):
        m = poly(pts)
        lift(c, m, dx=2 if pts[0][0] < CX else -2, dy=1, sigma=1.4, strength=0.6)
        paint(c, m, lap_col)
        paint(c, lines(pts[2:] + [pts[0]], 1), piping)
        paint(c, outline_of(m > 0.5, 1).astype(np.float32) * 0.9, (6, 4, 6))
    # front opening, buttons, pockets
    paint(c, lines([(CX, 146), (CX - 1, 190), (CX - 5, 201)]), (6, 4, 6))
    for by in (160, 180):
        button(c, CX - 5, by)
    paint(c, lines([(328, 139), (352, 137)], 2), (8, 6, 8))
    lift(c, shape(lambda d: d.rounded_rectangle((330, 114, 350, 138), 6, fill=255)), strength=0.5)
    crest(c, 340, 126, w=20, h=24)
    for x0 in (238, 315):
        flap = poly([(x0, 166), (x0 + 34, 166), (x0 + 34, 174), (x0, 174)])
        lift(c, flap, dy=2, sigma=1.2, strength=0.55)
        paint(c, flap, lap_col)
        paint(c, outline_of(flap > 0.5, 1).astype(np.float32), (6, 4, 6))
    # sides: pocket flaps continue, side seams
    paint(c, lines([(165, 166), (180, 166)]) + lines([(410, 166), (424, 166)]), (6, 4, 6))
    # back: centre seam and vent
    paint(c, lines([(491, 74), (491, 201)]), (8, 6, 8))
    paint(c, lines([(494, 178), (494, 201)]), (8, 6, 8))
    # collar ring on the top face
    up = rect_mask(["T_UP"])
    inner = (hole | collar) & up
    ring = ndimage.binary_dilation(inner, iterations=5) & ~inner & up
    paint(c, ring.astype(np.float32), lap_col)
    edge = ndimage.binary_dilation(ring | inner, iterations=1) & ~(ring | inner) & up
    paint(c, edge.astype(np.float32), piping)
    clear(c, hole)
    # cuffs: piping ring, shirt cuff, gold buttons on the back faces
    paint(c, (rect_mask(ARM_FACES) & (YY == 444)).astype(np.float32), piping)
    paint(c, (rect_mask(ARM_FACES) & (YY >= 455) & (YY <= SLEEVE_END)).astype(np.float32), shirt)
    for bx in (127, 134, 141, 446, 453, 460):
        button(c, bx, 436, r=1.6)
    hem_line(c, 201, TORSO_RING)
    face_seams(c)
    return save_hq(c, name)


# ================================================================== cardigan
def cardigan(name="shirt_cardigan_charcoal_crest.png", knit=(60, 60, 66), trim=GOLD, tie=CRIMSON, seed=21):
    p = vest_parts()
    src = p["src"]
    c = src.copy()
    knit_m = p["vest"] | p["sleeves"]
    c = recolor(c, p["vest"], knit, 14)
    c[p["sleeves"], :3] = recolor(src, p["sleeves"], knit, 14)[p["sleeves"], :3]
    c[p["vee"], :3] = recolor(src, p["vee"], WHITE_SHIRT, 12)[p["vee"], :3]
    tm = p["neck"] | p["hem"]
    c[tm, :3] = recolor(src, tm, trim, 10)[tm, :3]
    c[p["arm"], :3] = recolor(src, p["arm"], tuple(int(v * 0.86) for v in knit), 8)[p["arm"], :3]
    # knit ribs
    rib = 1 + 0.06 * np.sign(np.sin(2 * np.pi * XX / 3))
    c[knit_m, :3] = np.clip(c[knit_m, :3] * rib[knit_m, None], 0, 255)
    # tie inside the V
    tie_m = np.clip(poly([(290, 84), (299, 84), (297, 92), (292, 92)]) +
                    poly([(292, 92), (297, 92), (300, 118), (289, 118)]), 0, 1) * p["vee"]
    lift(c, tie_m, sigma=1.1, strength=0.45)
    paint(c, tie_m, tint(fabric_detail(seed, cloud=0.05, twill=0.0), tie))
    paint(c, (((XX + YY) // 3) % 4 == 0) * tie_m * (YY > 92), GOLD, 0.9)
    shade(c, outline_of(tie_m > 0.5, 1).astype(np.float32), 0.4)
    # button placket from the V point to the hem
    plack = (XX >= 290) & (XX <= 299) & (YY >= 113) & (YY <= 201)
    c[plack, :3] = np.clip(c[plack, :3] * 1.12, 0, 255)
    shade(c, (plack & ((XX == 290) | (XX == 299))).astype(np.float32), 0.45)
    for by in (124, 141, 158, 172, 192):
        button(c, CX, by, r=2.2)
    # patch pockets
    for x0 in (242, 320):
        m = (XX >= x0) & (XX <= x0 + 26) & (YY >= 148) & (YY <= 176)
        lift(c, m.astype(np.float32), dy=1, sigma=1.2, strength=0.4)
        shade(c, outline_of(m, 1).astype(np.float32), 0.5)
        paint(c, dash([(x0 + 2, 151), (x0 + 24, 151)]), tuple(int(v * 0.6) for v in knit))
    lift(c, shape(lambda d: d.rounded_rectangle((316, 120, 336, 144), 6, fill=255)), strength=0.5)
    crest(c, 326, 132, w=20, h=24)
    # ribbed cuffs with a gold stripe
    rib_band(c, ARM_FACES, 440, SLEEVE_END, tuple(int(v * 0.85) for v in knit), stripes=[(445, 446, trim)], seed=seed)
    face_seams(c, 0.7)
    return save_hq(c, name)


# ================================================================== varsity
def varsity(name="shirt_varsity_jacket.png", body=(26, 22, 26), sleeve=(132, 14, 24), gold=CANDLE, seed=31):
    leather = dict(cloud=0.06, twill=0.0, grain=0.015)
    c = base_shirt(body, sleeve, seed, body_tex=dict(cloud=0.11, twill=0.03, grain=0.05), sleeve_tex=leather)
    # soft leather shine down the middle of each sleeve face
    for n in ARM_FACES:
        x, y, w, h = R[n]
        g = np.exp(-((XX - (x + w * 0.45)) / (w * 0.22)) ** 2) * (rect_mask([n]) & (YY < 440))
        c[..., :3] = np.clip(c[..., :3] * (1 + 0.22 * g[..., None]), 0, 255)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    bands = [(2.5, body), (3.8, gold), (5.0, body), (6.2, sleeve), (8.0, body)]
    lo = 0
    for hi, col in bands:
        m = neck & (dist > lo) & (dist <= hi)
        paint(c, m.astype(np.float32), col)
        lo = hi
    shade(c, (neck & (dist > 7.2) & (dist <= 8.2)).astype(np.float32), 0.4)
    # snaps down the front
    paint(c, lines([(CX, 94), (CX, 186)]), (6, 4, 6))
    for by in (104, 122, 140, 158, 176):
        button(c, CX + 3, by, r=2.4, col=(196, 190, 176))
    # leather-trimmed slash pockets
    for pts in ([(244, 146), (254, 178)], [(345, 146), (335, 178)]):
        lift(c, lines(pts, 4), strength=0.5)
        paint(c, lines(pts, 4), sleeve)
        paint(c, lines(pts, 1), (8, 4, 6))
    # chenille NH patch on the wearer's left chest
    lift(c, text_mask("N", 26, (333 - 7.8, 120 - 6.8), fnt=font(26), stroke=4) + text_mask("H", 26, (333 + 7.8, 120 + 6.8), fnt=font(26), stroke=4), dx=1, dy=2, sigma=1.4, strength=0.55)
    monogram(c, 333, 120, 26, fill=gold, edge=sleeve, outline=IVORY)
    fuzz = np.clip(noise(H, W, seed + 7, 0.7), -1, 1) * 0.08
    patch = rect_mask(["T_F"]) & (XX > 308) & (YY < 150)
    c[patch, :3] = np.clip(c[patch, :3] * (1 + fuzz[patch, None]), 0, 255)
    # back: arched NIGHTMARE over a large NH
    f = font(13)
    word = "NIGHTMARE"
    bx, by, rad = 491, 166, 66
    for i, ch in enumerate(word):
        ang = np.deg2rad(-38 + 76 * i / (len(word) - 1))
        x = bx + rad * np.sin(ang)
        y = by - rad * np.cos(ang)
        from PIL import Image as _I, ImageDraw as _D
        tile = _I.new("L", (24, 24), 0)
        _D.Draw(tile).text((12, 12), ch, font=f, fill=255, anchor="mm", stroke_width=0)
        tile_s = _I.new("L", (24, 24), 0)
        _D.Draw(tile_s).text((12, 12), ch, font=f, fill=255, anchor="mm", stroke_width=2, stroke_fill=255)
        for t, col in ((tile_s, sleeve), (tile, gold)):
            r = np.array(t.rotate(-np.rad2deg(ang), resample=_I.BICUBIC), np.float32) / 255
            m = np.zeros((H, W), np.float32)
            m[int(y) - 12:int(y) + 12, int(x) - 12:int(x) + 12] = r
            paint(c, m, col)
    monogram(c, 491, 150, 38, fill=gold, edge=sleeve, outline=IVORY)
    # ribbed hem and cuffs
    stripes = [(190, 191, gold), (195, 196, sleeve)]
    rib_band(c, TORSO_RING, 186, 201, body, stripes=stripes, seed=seed)
    rib_band(c, ARM_FACES, 440, SLEEVE_END, body, stripes=[(445, 446, gold), (450, 451, sleeve)], seed=seed + 1)
    # (no dark outline round the arm tops: it showed as a border at the shoulder)
    clear(c, hole)
    face_seams(c)
    return save_hq(c, name)


# ================================================================== gym
def gym(name="shirt_gym_pe.png", body=IVORY, accent=CRIMSON, gold=GOLD, seed=41):
    jersey = dict(cloud=0.03, twill=0.02, grain=0.03)
    c = base_shirt(body, body, seed, body_tex=jersey, sleeve_tex=jersey, sleeve_end=398)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist > 0) & (dist <= 4.5)).astype(np.float32), accent)
    paint(c, (neck & (dist > 4.5) & (dist <= 5.5)).astype(np.float32), gold)
    shade(c, (neck & (dist > 5.5) & (dist <= 6.5)).astype(np.float32), 0.75)
    # side panels
    for x0 in (192, 388):
        m = rect_mask(["T_R", "T_L"]) & (XX >= x0) & (XX <= x0 + 8)
        paint(c, m.astype(np.float32), accent)
        paint(c, (rect_mask(["T_R", "T_L"]) & ((XX == x0 - 1) | (XX == x0 + 9))).astype(np.float32), gold)
    # short sleeves with a ribbed cuff
    rib_band(c, ARM_FACES, 390, 398, accent, stripes=[(392, 392, gold)], seed=seed)
    # chest print
    monogram(c, CX, 122, 36, fill=accent, edge=(70, 6, 12), shadow=False)
    paint(c, text_mask("A T H L E T I C S", 10, (CX, 160)), accent)
    # back print
    monogram(c, 491, 98, 16, fill=accent, edge=(70, 6, 12), shadow=False)
    paint(c, text_mask("PROPERTY OF", 9, (491, 140)), (70, 60, 56))
    paint(c, text_mask("N.H. ATHLETIC DEPT.", 9, (491, 152)), (70, 60, 56))
    paint(c, dash([(231, 196), (358, 196)]) + dash([(165, 196), (228, 196)]) + dash([(361, 196), (554, 196)]), (150, 144, 132))
    clear(c, hole)
    face_seams(c, 0.7)
    return save_hq(c, name)


# ================================================================== delinquent
def delinquent(name="shirt_polo_delinquent.png"):
    def post(c, p):
        seed = 51
        ring = rect_mask(TORSO_RING)
        # untuck: carry the shirt down over the tuck line and khaki strip
        low = ring & (YY >= 183)
        body_ref = p["body"] & ring & (YY < 180) & (YY > 120)
        fill_from_shift(c, low, dy=34, ref=body_ref, sigma=3)
        wob = ndimage.gaussian_filter1d(np.random.default_rng(seed).standard_normal(W), 3)
        wob = wob / (np.abs(wob).max() + 1e-6)
        hem = 195.5 + 2.5 * wob[XX]
        tail = np.exp(-((XX - 268) / 16.0) ** 2) * 4                     # one tail hangs lower
        hem = hem + tail
        below = ring & (YY > hem)
        band = ring & (YY > hem - 3) & (YY <= hem)
        c[band, :3] = np.clip(c[band, :3] * 1.18, 0, 255)
        shade(c, (ring & (np.abs(YY - hem) < 0.6)).astype(np.float32), 0.35)
        clear(c, below)
        clear(c, rect_mask(["T_D"]))
        # rolled sleeves: bunching, a rolled cuff, bare forearms
        arms = rect_mask(ARM_FACES)
        shade(c, (arms & (YY >= 396) & (YY < 404)).astype(np.float32), 0.8)
        cuff = arms & (YY >= 404) & (YY <= 416)
        c[cuff, :3] = np.clip(c[cuff, :3] * 1.25 + 6, 0, 255)
        for yl, f in ((404, 0.35), (409, 0.6), (412, 0.7), (416, 0.3)):
            shade(c, (arms & (YY == yl)).astype(np.float32), f)
        clear(c, arms & (YY > 416))
        # creases
        rng = np.random.default_rng(seed)
        for n in ARM_FACES:
            x, y, w, h = R[n]
            for _ in range(3):
                x0 = x + rng.integers(6, w - 12)
                y0 = rng.integers(366, 394)
                shade(c, lines([(x0, y0), (x0 + 8, y0 + rng.integers(-3, 4))]), 0.65)
        # open collar: buttons undone, undershirt showing, loose tie
        plack = (XX >= 283) & (XX <= 306) & (YY >= 84) & (YY <= 108) & ~p["grey"].astype(bool) | \
                ((XX >= 283) & (XX <= 306) & (YY >= 84) & (YY <= 108) & p["grey"] & (YY > 86))
        open_v = poly([(285, 86), (304, 86), (CX, 116)])
        paint(c, open_v, tint(fabric_detail(seed, cloud=0.04), (222, 216, 204)))
        shade(c, outline_of(open_v > 0.5, 1).astype(np.float32), 0.3)
        knot = poly([(284, 96), (293, 95), (292, 103), (285, 103)])
        blade = poly([(285, 103), (292, 103), (283, 142), (276, 146), (273, 139)])
        tie_m = np.clip(knot + blade, 0, 1)
        lift(c, tie_m, dx=1, dy=1, sigma=1.2, strength=0.5)
        paint(c, tie_m, tint(fabric_detail(seed + 1, cloud=0.05, twill=0), (20, 18, 22)))
        paint(c, (((XX - YY) // 3) % 4 == 0) * blade, CRIMSON, 0.9)
        shade(c, outline_of(tie_m > 0.5, 1).astype(np.float32), 0.3)
        # scuffs, a stitched tear, a faded monogram
        scuffs(c, ring & (c[..., 3] > 0), seed, amount=0.45, blobs=14, spread=3)
        scuffs(c, arms & (c[..., 3] > 0), seed + 1, amount=0.4, blobs=14, spread=3)
        paint(c, lines([(248, 160), (253, 166), (251, 172), (256, 178)], 2), (24, 6, 8))
        for sx, sy in ((247, 163), (250, 169), (252, 175)):
            paint(c, lines([(sx, sy), (sx + 6, sy - 1)]), (214, 206, 190))
        return c

    return make_polo(name, (104, 16, 20), collar_col=(196, 192, 182),
                     mono=((176, 160, 124), (110, 84, 40)), post=post)


def build():
    with supersample(4):
        return [blazer(), cardigan(), varsity(), gym(), delinquent()]


if __name__ == "__main__":
    for f in build():
        print(f.name)
