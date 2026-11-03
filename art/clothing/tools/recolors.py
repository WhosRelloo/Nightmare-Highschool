"""Colourways built directly from the user's vest and polo templates."""
import numpy as np
from scipy import ndimage

from nhcloth import *  # noqa: F401,F403

MONO = SourceMonogram()


# ---------------------------------------------------------------- vest
def vest_parts():
    M = remove_magenta(load("shirt_maroon_vest_grey.png"))
    yy, xx = np.mgrid[0:H, 0:W]
    # take out the dark maroon NH so a fresh monogram can go on top
    mono = (xx >= 304) & (xx <= 341) & (yy >= 110) & (yy <= 142)
    mono_c = (322, 126)
    plain = (M[..., 0] > M[..., 1] + 40) & (vmax(M) > 70)
    fill_from_shift(M, mono, dy=-34, ref=plain)
    A = M[..., 3] > 0
    v = vmax(M)
    s = sat(M)
    r, g, b = M[..., 0], M[..., 1], M[..., 2]
    dark = A & (v < 36)
    gold = A & (r > b + 15) & (g > b + 10) & (g > 40)
    grey = A & (s < 0.18) & (v >= 36) & ~gold
    vest = A & ~dark & ~gold & ~grey & (r > g + 20)

    lab, n = ndimage.label(gold)
    neck = np.zeros_like(gold)
    hem = np.zeros_like(gold)
    arm = np.zeros_like(gold)
    for i in range(1, n + 1):
        comp = lab == i
        ys, xs = np.nonzero(comp)
        if ys.min() >= 175:
            hem |= comp
        elif xs.min() >= 262 and xs.max() <= 327:
            neck |= comp
        else:
            arm |= comp
    # the shirt seen inside the V
    vee = grey & (xx >= 262) & (xx <= 327) & (yy >= 74) & (yy < 118)
    sleeves = grey & ~vee
    return dict(src=M, dark=dark, neck=neck, hem=hem, arm=arm, vee=vee,
                sleeves=sleeves, vest=vest, mono_c=mono_c)


def make_vest(name, vest_col, shirt_col, vee_col=None, trim=None, arm_trim=None,
              mono=(MONO_FILL, MONO_EDGE), boost=16):
    p = vest_parts()
    c = p["src"].copy()
    src = p["src"]
    c = recolor(c, p["vest"], vest_col, boost) if vest_col else c
    out = c
    out[p["sleeves"], :3] = recolor(src, p["sleeves"], shirt_col, boost)[p["sleeves"], :3]
    vc = vee_col or shirt_col
    out[p["vee"], :3] = recolor(src, p["vee"], vc, boost)[p["vee"], :3]
    if trim:
        tm = p["neck"] | p["hem"]
        out[tm, :3] = recolor(src, tm, trim, 10)[tm, :3]
    at = arm_trim or trim
    if at:
        out[p["arm"], :3] = recolor(src, p["arm"], at, 10)[p["arm"], :3]
    if mono:
        MONO.paste(out, p["mono_c"][0], p["mono_c"][1], fill=mono[0], edge=mono[1])
    return save_hq(out, name)


# ---------------------------------------------------------------- polo
def polo_parts():
    P = load("shirt_maroon_polo_khaki.png")
    keep = rect_mask(ALL_REGIONS, pad=2)
    P = clear(P, ~keep)              # drops the stray note in the margin
    yy, xx = np.mgrid[0:H, 0:W]
    mono = (xx >= 311) & (xx <= 348) & (yy >= 103) & (yy <= 128)
    mono_c = (329, 115)
    plain = (P[..., 0] > P[..., 1] + 40) & (vmax(P) > 70)
    fill_from_shift(P, mono, dy=-30, ref=plain)
    A = P[..., 3] > 0
    v = vmax(P)
    s = sat(P)
    r, g, b = P[..., 0], P[..., 1], P[..., 2]
    dark = A & (v < 30)
    body = A & ~dark & (r > g + 25) & (r > b + 20)
    khaki = A & ~dark & (np.abs(r - g) < 16) & (g - b > 10) & (v > 60) & (s < 0.35)
    grey = A & ~dark & (s < 0.14) & (v >= 55) & ~khaki
    return dict(src=P, dark=dark, body=body, khaki=khaki, grey=grey, mono_c=mono_c)


def make_polo(name, body_col, collar_col=None, khaki_col=None, mono=(MONO_FILL, MONO_EDGE), boost=16, post=None):
    p = polo_parts()
    src = p["src"]
    out = recolor(src, p["body"], body_col, boost)
    if collar_col:
        out[p["grey"], :3] = recolor(src, p["grey"], collar_col, boost)[p["grey"], :3]
    if khaki_col:
        out[p["khaki"], :3] = recolor(src, p["khaki"], khaki_col, boost)[p["khaki"], :3]
    if mono:
        MONO.paste(out, p["mono_c"][0], p["mono_c"][1], fill=mono[0], edge=mono[1])
    if post:
        out = post(out, p)
    return save_hq(out, name)


def build():
    with supersample(4):
        return _build()


def _build():
    files = []
    files.append(make_vest("shirt_vest_navy_ivory.png", NAVY, IVORY))
    files.append(make_vest("shirt_vest_forest_cream.png", FOREST, CREAM))
    files.append(make_vest("shirt_vest_charcoal_crimson.png", CHARCOAL, CRIMSON, vee_col=WHITE_SHIRT))
    files.append(make_vest("shirt_vest_vigil_ivory_gold.png", IVORY, BLACK, vee_col=WHITE_SHIRT,
                           trim=CANDLE, mono=((52, 36, 14), CANDLE)))
    files.append(make_vest("shirt_vest_crimson_court.png", BLOOD, BLACK, vee_col=(40, 30, 32),
                           trim=(120, 18, 22), arm_trim=(70, 8, 12), mono=(MONO_FILL, (110, 10, 18))))
    files.append(make_polo("shirt_polo_navy_khaki.png", NAVY, collar_col=(206, 206, 210)))
    files.append(make_polo("shirt_polo_forest_khaki.png", FOREST, collar_col=CREAM))
    files.append(make_polo("shirt_polo_ivory_crimson.png", IVORY, collar_col=CRIMSON,
                           mono=((140, 14, 26), (70, 6, 12))))
    files.append(make_polo("shirt_polo_crimson_charcoal.png", CRIMSON, collar_col=(40, 40, 44),
                           khaki_col=(64, 64, 68)))
    return files


if __name__ == "__main__":
    for f in build():
        print(f.name)
