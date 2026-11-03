"""More transformation outfits.

WITH the uniform: a transformed school top per form, worn over the student's own uniform bottoms
(Appearance.Forms[x].UniformOutfit, used when you transform while wearing a school top):
  Vampire  the black blazer: tall silk collar, jabot and ruby brooch, a velvet cape over the back
  Wolf     the charcoal vest torn open by fur, sleeves ripped off, claws
  Ghoul    the ghoul race uniform, ribcage opened, bony hands through the frayed cuffs
  Wraith   the charcoal cardigan going spectral: sleeves dissolve into mist, glowing sigil and runes

WITHOUT the uniform, female body (Appearance.Forms[x].FemaleOutfit):
  Vampire  Countess gown: Medici lace collar, crimson silk corset, slashed puff sleeves, floor-length skirt
  Wraith   Banshee shroud: tattered pale grave-dress dissolving into mist
"""
import numpy as np
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import base_shirt, face_seams, hem_line, mirror
from pants import LEG_UPS
import forms
from forms import (VELVET, SILK, SPECTRAL, VOID, all_shirt, pants_cloth_zone, wolf_fur, ghoul_skin,
                   rot_edges, robe_tex, wisps, sigil)
from female import scallops, lacing, bow, fabric, LACE, LACE_EDGE

import nhcloth

F32 = np.float32
INK = (8, 6, 8)


def base(name):
    """A finished uniform piece from variants/ (already quality-passed)."""
    return np.array(Image.open(nhcloth.OUT / name).convert("RGBA")).astype(F32)


def save_overlay(c, before, name):
    """Quality-pass shading on the newly painted pixels only (the uniform underneath is already shaded)."""
    changed = (np.abs(c - before).sum(-1) > 6) & (c[..., 3] > 0)
    probe = np.full_like(c, 255.0)
    probe[..., 3] = c[..., 3]
    f = finish(probe, creases=False)[..., :3] / 255.0
    c[changed, :3] = np.clip(c[changed, :3] * f[changed], 0, 255)
    return nhcloth.save(c, name)


def save_full(c, name):
    return nhcloth.save(finish(c, creases=False, seed=sum(map(ord, name))), name)


# ================================================================== WITH the uniform
def uniform_vampire(name="shirt_form_uniform_vampire.png", seed=1101):
    c = base("shirt_blazer_black_crest.png")
    before = c.copy()
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    # the tie gives way to a lace jabot and a ruby brooch
    shirt = tint(fabric_detail(seed, cloud=0.05, twill=0.03), WHITE_SHIRT)
    paint(c, poly([(285, 84), (305, 84), (306, 146), (283, 146)]), shirt)
    jabot(c, CX, 90, n=6)
    brooch(c, CX, 90)
    paint(c, lines([(300, 116), (300, 126)], 2), (150, 8, 18))
    paint(c, shape(lambda d: d.ellipse((298, 125, 302, 130), fill=255)), (150, 8, 18))
    # a tall standing collar: crimson silk facing, velvet outside, gold edge
    silk = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), SILK, 10)
    neck = rect_mask(["T_UP", "T_F"])
    paint(c, (neck & (dist <= 4)).astype(F32), silk)
    paint(c, (neck & (dist > 4) & (dist <= 9)).astype(F32), tint(fabric_detail(seed + 2, cloud=0.06, twill=0), (16, 8, 14)))
    paint(c, (neck & (dist > 9) & (dist <= 10)).astype(F32), GOLD)
    # a velvet cape over the back, wrapping the sides, crimson lining at the edges, chain clasp at the front
    vel = tint(fabric_detail(seed + 3, cloud=0.08, twill=0.02), VELVET)
    cape = rect_mask(["T_B"]) | (rect_mask(["T_R"]) & (XX <= 180)) | (rect_mask(["T_L"]) & (XX >= 410)) | \
        (rect_mask(["T_UP"]) & (YY <= 30) & ~hole)
    lift(c, cape.astype(F32), dx=0, dy=2, sigma=1.6, strength=0.5)
    c[cape, :3] = vel[cape]
    fold = 1 + 0.14 * np.sin(2 * np.pi * XX / 14 + 0.8 * np.sin(YY / 17))
    c[cape, :3] = np.clip(c[cape, :3] * fold[cape, None], 0, 255)
    sheen(c, ["T_B"], 0.25, width=0.2)
    lining = (rect_mask(["T_R"]) & (XX >= 177) & (XX <= 180)) | (rect_mask(["T_L"]) & (XX >= 410) & (XX <= 413))
    c[lining, :3] = silk[lining]
    paint(c, (cape & rect_mask(["T_B"]) & (YY >= 198)).astype(F32), GOLD)
    b = bat(491, 120, 70)
    paint(c, ndimage.binary_dilation(b > 0.5, iterations=1).astype(F32), GOLD)
    paint(c, b, (96, 6, 16))
    chain(c, [(238, 78), (262, 84), (CX, 86), (327, 84), (351, 78)], GOLD)
    # crimson silk turn-back cuffs
    cuff = rect_mask(ARM_FACES) & (YY >= 438) & (YY <= 452)
    c[cuff, :3] = silk[cuff]
    paint(c, (rect_mask(ARM_FACES) & ((YY == 437) | (YY == 453))).astype(F32), GOLD)
    clear(c, hole)
    return save_overlay(c, before, name)


def uniform_wolf(name="shirt_form_uniform_wolf.png", seed=1111):
    c = base("shirt_vest_charcoal_crimson.png")
    before = c.copy()
    coat = wolf_fur(seed)
    chest = fur((80, 70, 60), (214, 200, 174), seed + 1, angle=96, length=(6, 11), mottle=0.8)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    # sleeves ripped off below the elbow: furred forearms and claws
    s_edge = ragged_y(400, 6, seed, notches=0.1, depth=(6, 16))
    arms = rect_mask(ARM_FACES)
    below = arms & (YY > s_edge[XX])
    c[below, :3] = coat[below]
    c[below, 3] = 255
    shade(c, (arms & (YY >= 462)).astype(F32), 0.7)
    edge = arms & (np.abs(YY - s_edge[XX]) < 1.2)
    shade(c, edge.astype(F32), 0.4)
    rng = np.random.default_rng(seed)
    fray = arms & (np.abs(YY - s_edge[XX]) < 3) & (YY < s_edge[XX]) & (rng.random((H, W)) < 0.18)
    c[fray, :3] = (236, 232, 222)
    claws(c, ["RA_F", "LA_F", "RA_R", "LA_L", "RA_L", "LA_R"], 482, n=4, length=9)
    # the vest bursts open at the chest; fur through rips on the body and a slashed back
    wob = 3 * noise(H, W, seed + 4, 2)
    open_c = rect_mask(["T_F"]) & (YY > 90) & (np.abs(XX - CX - 2 * np.sin(YY / 6)) < 7 + (YY - 74) * 0.32 + wob)
    rips = blob_holes(rect_mask(TORSO_RING + ["RA_F", "LA_F"]) & ~below, seed + 6, thresh=1.75, sigma=4)
    slash = np.zeros((H, W), bool)
    for k in range(3):
        x0 = 452 + k * 15
        slash |= (poly([(x0, 92), (x0 + 6, 92), (x0 + 38, 176), (x0 + 30, 178)]) > 0.5) & (noise(H, W, seed + 10 + k, 1.2) > -1.2)
    burst = open_c | rips | slash
    shade(c, ndimage.binary_dilation(burst, iterations=1).astype(F32) * ~burst, 0.45)
    c[burst, :3] = np.where(open_c[burst][:, None], chest[burst], coat[burst])
    mane = rect_mask(["T_UP", "T_F"]) & (dist <= 7)
    c[mane, :3] = chest[mane]
    scuffs(c, (c[..., 3] > 0) & ~burst & ~below, seed + 7, amount=0.4, color=(70, 56, 40), blobs=24, spread=5)
    spat = (noise(H, W, seed + 8, 0.9) > 2.4) & (np.hypot(XX - 300, YY - 120) < 40)
    c[ndimage.binary_dilation(spat, iterations=1) & (c[..., 3] > 0), :3] = (110, 8, 16)
    clear(c, hole)
    return save_overlay(c, before, name)


def uniform_ghoul(name="shirt_form_uniform_ghoul.png", seed=1121):
    c = base("shirt_ghoul_uniform_black_vest.png")
    before = c.copy()
    skin = ghoul_skin(seed)
    # the cuffs give way: bony grey hands and wrists
    s_edge = ragged_y(430, 6, seed, notches=0.1, depth=(6, 14))
    arms = rect_mask(ARM_FACES)
    below = arms & (YY > s_edge[XX])
    c[below, :3] = skin[below]
    c[below, 3] = 255
    rot_edges(c, (c[..., 3] > 0) & ~below, seed)
    for n in ARM_FACES:
        x, y, w, h = R[n]
        for kx in range(x + 8, x + w - 4, 12):
            paint(c, shape(lambda d: d.ellipse((kx - 2, 468, kx + 2, 472), fill=255)), (200, 194, 168))
            paint(c, lines([(kx, 479), (kx, 482)], 2), (36, 28, 24))
    # rotted holes show grey skin; the chest is opened onto the ribcage
    holes = blob_holes(rect_mask(TORSO_RING + ARM_FACES) & ~below, seed + 1, thresh=2.05, sigma=5.5)
    c[holes, :3] = skin[holes]
    rib = (XX - 330) ** 2 / 20.0 ** 2 + (YY - 161) ** 2 / 21.0 ** 2 < 1 + 0.25 * noise(H, W, seed + 2, 1.5)
    cav = rib & rect_mask(["T_F"])
    depth = np.clip(((XX - 330) ** 2 / 20.0 ** 2 + (YY - 161) ** 2 / 21.0 ** 2), 0, 1)
    c[cav, :3] = (np.array((14, 2, 4), F32) * (1 - depth[..., None]) + np.array((60, 10, 14), F32) * depth[..., None])[cav]
    for ry in (147, 155, 163, 171, 179):
        arc = shape(lambda d: d.arc((306, ry - 5, 356, ry + 9), 200, 340, fill=255, width=1)) * cav
        paint(c, np.roll(arc, 1, 0) * cav, (40, 30, 24))
        paint(c, arc, (186, 174, 144))
    flesh = ndimage.binary_dilation(cav, iterations=2) & ~cav & (c[..., 3] > 0)
    c[flesh, :3] = (104, 28, 30)
    glow(c, cav.astype(F32) * 0.4, (70, 140, 50), sigma=3, strength=0.12, core=False)
    stitches(c, [(468, 150), (486, 140), (506, 150)])
    hole = hole_mask(load("shirt_maroon_vest_grey.png"))
    clear(c, hole)
    return save_overlay(c, before, name)


def uniform_wraith(name="shirt_form_uniform_wraith.png", seed=1131):
    c = base("shirt_cardigan_charcoal_crest.png")
    before = c.copy()
    vis = c[..., 3] > 0
    # the colour drains out: desaturated, cold, a little see-through
    g = c[..., :3].mean(-1, keepdims=True)
    cold = np.clip(g * np.array((0.78, 0.92, 1.05), F32) * 0.85, 0, 255)
    c[vis, :3] = cold[vis]
    # sleeves dissolve into void and mist below the elbow
    edge = ragged_y(420, 7, seed, notches=0.16, depth=(6, 18))
    below = rect_mask(ARM_FACES) & (YY > edge[XX])
    c[below, :3] = VOID
    c[below, 3] = 255
    wisps(c, below, seed, 420, length=26, n_per=9)
    glow(c, (rect_mask(ARM_FACES) & (np.abs(YY - edge[XX]) < 1.0)).astype(F32), SPECTRAL, sigma=3.5, strength=0.35, core=False)
    # the hem frays into wisps too
    hem = ragged_y(194, 4, seed + 1, notches=0.2, depth=(3, 7))
    gone = rect_mask(TORSO_RING) & (YY > hem[XX])
    c[gone, :3] = VOID
    wisps(c, gone, seed + 2, 194, length=8, n_per=8)
    # the crest burns spectral, a sigil on the back, glowing cracks
    glow(c, shape(lambda d: d.ellipse((330, 114, 350, 140), fill=255)) * 0.6, SPECTRAL, sigma=3, strength=0.6, core=False)
    sg = sigil(491, 140, 22)
    glow(c, sg * 0.85, SPECTRAL, sigma=4, strength=0.75)
    for pts in ([(250, 100), (258, 118), (254, 134)], [(170, 120), (184, 140)], [(400, 110), (392, 136)]):
        glow(c, lines(pts), SPECTRAL, sigma=1.6, strength=0.55)
    chain(c, [(231, 170), (262, 182), (CX, 188), (327, 182), (358, 170)], (96, 150, 146))
    hole, _ = polo_hole()
    clear(c, hole)
    return save_overlay(c, before, name)


# ================================================================== WITHOUT the uniform (female body)
def countess_shirt(name="shirt_form_vampire_countess.png", seed=1201):
    vt = dict(cloud=0.08, twill=0.02, grain=0.03)
    c = base_shirt(VELVET, VELVET, seed, body_tex=vt, sleeve_tex=vt)
    sheen(c, TORSO_RING + ARM_FACES, 0.28, width=0.2)
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    silk = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), SILK, 10)
    # Medici collar: a fan of black lace standing behind the head (the back half of the top face)
    fan = rect_mask(["T_UP"]) & (YY <= 40) & ~hole
    c[fan, :3] = (14, 8, 12)
    ang = np.arctan2(YY - 44, XX - CX)
    ribs = fan & ((np.abs(((ang * 14 / np.pi) % 1) - 0.5) < 0.12))
    paint(c, ribs.astype(F32), GOLD)
    lacey = fan & ((((XX + YY) % 4) == 0) | (((XX - YY) % 4) == 0))
    c[lacey, :3] = (40, 12, 20)
    paint(c, (rect_mask(["T_UP"]) & (np.abs(YY - 40) < 1)).astype(F32), GOLD)
    # crimson silk corset with gold boning, a deep lace V and a bat brooch
    cm = poly([(250, 96), (339, 96), (325, 201), (264, 201)])
    lift(c, cm, dy=1, sigma=1.4, strength=0.5)
    paint(c, cm, silk)
    damask(c, cm > 0.5, 0.78)
    for bx in (262, 276, 313, 327):
        paint(c, lines([(bx, 104), (bx + (2 if bx > CX else -2), 199)]) * cm, GOLD, 0.7)
    paint(c, lines([(250, 96), (264, 201)]) + lines([(339, 96), (325, 201)]), GOLD)
    vee = poly([(268, 96), (321, 96), (CX, 140)])
    paint(c, vee, (14, 8, 12))
    paint(c, ((vee > 0.5) & ((((XX + YY) % 4) == 0) | (((XX - YY) % 4) == 0))).astype(F32), (60, 16, 26))
    b = bat(CX, 104, 26)
    paint(c, ndimage.binary_dilation(b > 0.5, iterations=1).astype(F32), GOLD)
    paint(c, b, (120, 6, 18))
    brooch(c, CX, 112)
    lacing(c, 491, 104, 196, gap=6, step=10, col=SILK, eyelet=GOLD)
    # slashed puff sleeves: crimson silk showing through black velvet slits, lace cuffs
    arms = rect_mask(ARM_FACES)
    puff = arms & (YY < 396)
    slits = puff & ((XX % 10) >= 7)
    c[slits, :3] = silk[slits]
    shade(c, (puff & ((XX % 10) == 6)).astype(F32), 0.5)
    shade(c, (arms & (YY >= 394) & (YY <= 397)).astype(F32), 0.5)
    paint(c, (arms & (YY == 396)).astype(F32), GOLD)
    scallops(c, ARM_FACES, 446, 462, clip_end=SLEEVE_END)
    # a single blood drip from the corner of the collar
    paint(c, lines([(306, 98), (306, 108)], 2), (150, 8, 18))
    paint(c, shape(lambda d: d.ellipse((304, 107, 308, 112), fill=255)), (150, 8, 18))
    clear(c, hole)
    face_seams(c, 0.5)
    return save_full(c, name)


def countess_pants(name="pants_form_vampire_countess.png", seed=1211):
    c, hole = pants_shell(seed)
    vel = tint(fabric_detail(seed, cloud=0.08, twill=0.02), VELVET)
    silk = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), SILK, 10)
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(LEGS) | rect_mask(LEG_UPS) | rect_mask(["T_D"]) | rect_mask(ARM_DOWNS)
    c[m, :3] = vel[m]
    c[m, 3] = 255
    shade(c, rect_mask(["T_D"] + ARM_DOWNS).astype(F32), 0.5)
    legs = rect_mask(LEGS)
    fold = 1 + 0.16 * np.sin(2 * np.pi * XX / 12 + 1.2 * noise(H, W, seed + 2, 7))
    c[legs, :3] = np.clip(c[legs, :3] * fold[legs, None], 0, 255)
    sheen(c, LEGS, 0.25, width=0.16)
    # a crimson silk underskirt shows down the front, trimmed in gold
    for n in FRONTS:
        x, y, w, h = R[n]
        panel = rect_mask([n]) & (np.abs(XX - (x + w / 2)) <= 16 + (YY - 355) * 0.06)
        c[panel, :3] = silk[panel]
        damask(c, panel, 0.8)
        paint(c, (outline_of(panel, 1)).astype(F32), GOLD)
    paint(c, (legs & (YY == 470)).astype(F32), GOLD)
    scallops(c, LEGS, 471, 482, col=(14, 10, 14), edge=(70, 20, 30))
    # blood soaking up from the hem
    for n in LEGS:
        x, y, w, h = R[n]
        grad = np.clip((YY - 446) / 28.0, 0, 1) * rect_mask([n]) * (noise(H, W, seed + 5, 3) > -0.4)
        c[..., :3] = c[..., :3] * (1 - 0.35 * grad[..., None]) + np.array((90, 4, 12), F32) * 0.35 * grad[..., None]
    wb = rect_mask(TORSO_RING) & (YY >= 179) & (YY <= 187)
    c[wb, :3] = silk[wb]
    paint(c, (rect_mask(TORSO_RING) & ((YY == 178) | (YY == 188))).astype(F32), GOLD)
    clear(c, hole)
    return save_full(c, name)


BANSHEE = (128, 140, 150)


def banshee_tex(seed):
    r = tint(fabric_detail(seed, cloud=0.14, twill=0.0, grain=0.05), BANSHEE)
    fold = 1 + 0.14 * np.sin(2 * np.pi * XX / 9 + 1.5 * noise(H, W, seed + 1, 6))
    stain = np.clip(noise(H, W, seed + 2, 5) - 0.8, 0, 1)[..., None] * 0.5
    r = r * fold[..., None] * (1 - stain) + np.array((60, 66, 70), F32) * stain
    return np.clip(r, 0, 255)


def banshee_shirt(name="shirt_form_wraith_banshee.png", seed=1301):
    c = blank()
    t = banshee_tex(seed)
    m = all_shirt()
    c[m, :3] = t[m]
    c[m, 3] = 255
    hole, _ = polo_hole()
    dist = ndimage.distance_transform_edt(~hole)
    neck = rect_mask(["T_UP", "T_F"])
    hood = neck & (dist <= 8)
    c[hood, :3] = c[hood, :3] * np.clip(dist / 8.0, 0.1, 1)[hood, None]
    # tattered holes through to the void, long torn sleeves dissolving into mist
    holes = blob_holes(rect_mask(TORSO_RING + ARM_FACES), seed + 3, thresh=2.1, sigma=5.5)
    c[holes, :3] = VOID
    rot_edges(c, (c[..., 3] > 0) & ~holes, seed, fray_col=(190, 200, 205))
    edge = ragged_y(452, 9, seed, notches=0.2, depth=(8, 22))
    below = rect_mask(ARM_FACES) & (YY > edge[XX])
    c[below, :3] = VOID
    wisps(c, below, seed, 452, length=24, n_per=10)
    glow(c, (rect_mask(ARM_FACES) & (np.abs(YY - edge[XX]) < 1.0)).astype(F32), SPECTRAL, sigma=3.5, strength=0.4, core=False)
    # a glowing sigil at the heart, a wail of runes round the collar, grave chains
    glow(c, sigil(CX, 128, 14), SPECTRAL, sigma=3, strength=0.9)
    runes = neck & (dist > 9) & (dist <= 10.5) & ((np.arctan2(YY - 50, XX - CX) * 12).astype(int) % 3 == 0)
    glow(c, runes.astype(F32), SPECTRAL, sigma=2, strength=0.55)
    chain(c, [(231, 176), (262, 188), (CX, 192), (327, 188), (358, 176)], (110, 150, 150))
    glow(c, sigil(491, 150, 20) * 0.8, SPECTRAL, sigma=4, strength=0.7)
    clear(c, hole)
    face_seams(c, 0.6)
    return save_full(c, name)


def banshee_pants(name="pants_form_wraith_banshee.png", seed=1311):
    c, hole = pants_shell(seed)
    t = banshee_tex(seed)
    z = pants_cloth_zone()
    c[z, :3] = t[z]
    c[z, 3] = 255
    # a long shredded grave-dress that dissolves from mid-shin
    edge = ragged_y(424, 14, seed, notches=0.25, depth=(10, 30))
    below = rect_mask(LEGS) & (YY > edge[XX])
    c[below, :3] = VOID
    wisps(c, below, seed, 428, length=34, n_per=12)
    glow(c, (rect_mask(LEGS) & (np.abs(YY - edge[XX]) < 1.0)).astype(F32), SPECTRAL, sigma=3.5, strength=0.4, core=False)
    holes = blob_holes(rect_mask(LEGS) & ~below, seed + 2, thresh=2.1, sigma=5.5)
    c[holes, :3] = VOID
    dn = rect_mask(ARM_DOWNS)
    c[dn, :3] = VOID
    cord = rect_mask(TORSO_RING) & (YY >= 182) & (YY <= 185)
    c[cord, :3] = (150, 160, 168)
    glow(c, shape(lambda d: d.ellipse((297, 180, 305, 188), fill=255)), SPECTRAL, sigma=2, strength=0.6)
    clear(c, hole)
    return save_full(c, name)


UNIFORM_TOPS = [uniform_vampire, uniform_wolf, uniform_ghoul, uniform_wraith]
FEMALE_PAIRS = [(countess_shirt, countess_pants), (banshee_shirt, banshee_pants)]

CATALOG = {
    "shirt_form_uniform_vampire.png": ("Vampire (in uniform)", "Vampire", "UniformOutfit"),
    "shirt_form_uniform_wolf.png": ("Wolf (in uniform)", "Wolf", "UniformOutfit"),
    "shirt_form_uniform_ghoul.png": ("Ghoul (in uniform)", "Ghoul", "UniformOutfit"),
    "shirt_form_uniform_wraith.png": ("Wraith (in uniform)", "Wraith", "UniformOutfit"),
    "shirt_form_vampire_countess.png": ("Vampire Countess", "Vampire", "FemaleOutfit"),
    "pants_form_vampire_countess.png": ("Vampire Countess gown", "Vampire", "FemaleOutfit"),
    "shirt_form_wraith_banshee.png": ("Wraith Banshee", "Wraith", "FemaleOutfit"),
    "pants_form_wraith_banshee.png": ("Wraith Banshee shroud", "Wraith", "FemaleOutfit"),
}


def build():
    out = []
    with nhcloth.supersample(4):
        for f in UNIFORM_TOPS:
            out.append(f())
        for s, p in FEMALE_PAIRS:
            out += [s(), p()]
    return out


if __name__ == "__main__":
    for f in build():
        print(f.name)
