"""The Standing Path uniform variants (2.34, docs/expansion/14-Progression-and-Identity.md §6.1): three school shirts
earned at path tiers, drawn on the classic layout in the style of the uniform set (shirts_new.py, recolors.py).

  shirt_path_rolled_sleeves.png   Social 3 (Popular): the navy vest uniform worn easy, sleeves rolled to the elbow
                                  (bunched cuffs, bare forearms), the tie neat.
  shirt_path_loose_tie.png        Combat 3 (Enforcer): the charcoal vest with the collar undone, the tie pulled loose
                                  and askew, a few scuffs on the knuckle side of the sleeves.
  shirt_path_worn_blazer.png      Supernatural 3 (Initiated): the crest blazer, old and well travelled: faded at the
                                  seams and shoulders, leather elbow patches, frayed cuffs, a darned tear, tarnished
                                  buttons, a faint candle-wax spot.

  python pathwear.py      (writes into ../variants; contact sheet: python sheet.py is unchanged)
"""
import numpy as np
from PIL import Image
from scipy import ndimage

from nhcloth import *  # noqa: F401,F403
import shirts_new as SN

YY, XX = np.mgrid[0:H, 0:W]
CX = SN.CX


def from_variant(name):
    return np.array(Image.open(OUT / name).convert("RGBA")).astype(np.float32)


def roll_sleeves(c, seed, top=398):
    """bunching above the roll, a rolled cuff, bare forearms below (the skin shows through)"""
    arms = rect_mask(ARM_FACES)
    shade(c, (arms & (YY >= top - 8) & (YY < top)).astype(np.float32), 0.8)
    cuff = arms & (YY >= top) & (YY <= top + 13)
    c[cuff, :3] = np.clip(c[cuff, :3] * 1.22 + 8, 0, 255)
    for yl, f in ((top, 0.35), (top + 5, 0.6), (top + 9, 0.7), (top + 13, 0.3)):
        shade(c, (arms & (YY == yl)).astype(np.float32), f)
    clear(c, arms & (YY > top + 13))
    rng = np.random.default_rng(seed)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for _ in range(3):
            x0 = x + rng.integers(6, w - 12)
            y0 = rng.integers(366, top - 6)
            shade(c, SN.lines([(x0, y0), (x0 + 8, y0 + rng.integers(-3, 4))]), 0.66)
    return c


def open_collar_loose_tie(c, seed, shirt_col=(226, 220, 208), tie_col=(22, 20, 24), stripe=CRIMSON):
    """repaint the V with shirt, undo the top button and hang the tie loose and to one side"""
    vee = SN.poly([(258, 74), (331, 74), (CX, 150)])
    paint(c, vee, tint(fabric_detail(seed, cloud=0.05, twill=0.03), shirt_col))
    shade(c, SN.outline_of(vee > 0.5, 1).astype(np.float32), 0.45)
    open_v = SN.poly([(284, 76), (305, 76), (CX, 108)])
    paint(c, open_v, tint(fabric_detail(seed + 1, cloud=0.04), (238, 228, 214)))          # the undershirt
    shade(c, SN.outline_of(open_v > 0.5, 1).astype(np.float32), 0.35)
    for pts in ([(270, 76), (284, 76), (290, 92), (276, 90)], SN.mirror([(270, 76), (284, 76), (290, 92), (276, 90)])):
        m = SN.poly(pts)                                                                 # collar points, sprung open
        lift(c, m, dx=1, dy=1, sigma=1.1, strength=0.45)
        paint(c, m, tint(fabric_detail(seed + 2, cloud=0.04), shirt_col))
        shade(c, SN.outline_of(m > 0.5, 1).astype(np.float32), 0.4)
    knot = SN.poly([(283, 99), (292, 98), (291, 106), (284, 106)])
    blade = SN.poly([(284, 106), (291, 106), (281, 144), (274, 148), (271, 141)])
    tie_m = np.clip(knot + blade, 0, 1)
    lift(c, tie_m, dx=1, dy=1, sigma=1.2, strength=0.5)
    paint(c, tie_m, tint(fabric_detail(seed + 3, cloud=0.05, twill=0), tie_col))
    paint(c, (((XX - YY) // 3) % 4 == 0) * blade, stripe, 0.9)
    shade(c, SN.outline_of(tie_m > 0.5, 1).astype(np.float32), 0.3)
    return c


def rolled_sleeves(name="shirt_path_rolled_sleeves.png"):
    c = from_variant("shirt_vest_navy_ivory.png")
    roll_sleeves(c, 61)
    return save_hq(c, name)


def loose_tie(name="shirt_path_loose_tie.png"):
    c = from_variant("shirt_vest_charcoal_crimson.png")
    open_collar_loose_tie(c, 71)
    arms = rect_mask(ARM_FACES)
    scuffs(c, arms & (YY > 420) & (c[..., 3] > 0), 72, amount=0.35, blobs=10, spread=3)
    return save_hq(c, name)


def worn_blazer(name="shirt_path_worn_blazer.png"):
    SN.blazer(name="_tmp_blazer.png", body=(34, 30, 34), piping=(110, 30, 34), tie=(96, 18, 24), seed=81)
    c = from_variant("_tmp_blazer.png")
    (OUT / "_tmp_blazer.png").unlink()
    ring, arms = rect_mask(TORSO_RING + ["T_UP"]), rect_mask(ARM_FACES + ARM_UPS)
    vis = c[..., 3] > 0
    # fading: lighter, greyer at the shoulders and the seams, a little all over
    rng = np.random.default_rng(81)
    fade = ndimage.gaussian_filter(rng.random((H, W)), 9)
    fade = (fade - fade.min()) / (np.ptp(fade) + 1e-6)
    shoulders = np.zeros((H, W), np.float32)
    for n in ("T_UP", "RA_UP", "LA_UP"):
        x, y, w, h = R[n]
        shoulders[y:y + h, x:x + w] = 1
    shoulders[74:92, 165:555] = 0.6
    k = (0.18 * fade + 0.22 * shoulders)[..., None] * vis[..., None]
    grey = c[..., :3].mean(-1, keepdims=True)
    c[..., :3] = c[..., :3] * (1 - k) + (grey * 1.35 + 18) * k
    # leather elbow patches on the back faces of both sleeves
    for n in ("RA_B", "LA_B"):
        x, y, w, h = R[n]
        patch = shape(lambda d, x=x, y=y, w=w: d.ellipse((x + w * 0.22, y + 34, x + w * 0.78, y + 74), fill=255))
        lift(c, patch, dx=1, dy=1, sigma=1.2, strength=0.55)
        paint(c, patch, tint(fabric_detail(82, cloud=0.12, twill=0.0, grain=0.08), (78, 46, 30)))
        paint(c, SN.dash(SN_ellipse(x + w * 0.22 + 3, y + 37, x + w * 0.78 - 3, y + 71), on=2, off=2), (170, 140, 96), 0.9)
    # frayed cuffs: a ragged lower edge with loose threads
    cuff_edge = 444
    wob = ndimage.gaussian_filter1d(rng.standard_normal(W), 1.2)
    edge = cuff_edge + 2 + 2.5 * wob[XX]
    lost = rect_mask(ARM_FACES) & (YY > edge) & (YY < cuff_edge + 9)
    shade(c, lost.astype(np.float32), 0.55)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for _ in range(4):
            x0 = x + rng.integers(4, w - 4)
            paint(c, SN.lines([(x0, cuff_edge + 2), (x0 + rng.integers(-2, 3), cuff_edge + 7)]), (140, 128, 120), 0.8)
    # a darned tear on the left front, a wax spot on the right
    paint(c, SN.lines([(252, 150), (257, 158), (255, 166), (260, 172)], 2), (14, 10, 12))
    for sx, sy in ((250, 152), (253, 158), (255, 164), (257, 170)):
        paint(c, SN.lines([(sx, sy), (sx + 7, sy - 1)]), (150, 132, 104))
    wax = shape(lambda d: d.ellipse((318, 180, 326, 186), fill=255))
    paint(c, wax, (212, 196, 160), 0.7)
    # tarnish the gold buttons a little
    gold = (c[..., 0] > 150) & (c[..., 1] > 110) & (c[..., 2] < 110) & vis
    c[gold, :3] = c[gold, :3] * 0.72 + np.array([20, 18, 6], np.float32)
    return save_hq(c, name)


def SN_ellipse(x0, y0, x1, y1, n=28):
    import math
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]


def build():
    with supersample(4):
        return [rolled_sleeves(), loose_tie(), worn_blazer()]


if __name__ == "__main__":
    for f in build():
        print(f.name)
