"""Transformation variants of every everyday piece of clothing (2026-11-04).

When a character transforms (character attribute Transformation), the game used to swap
whatever they wore for one fixed form outfit. This makes a transformed copy of EACH
wardrobe piece instead, so a student keeps their own outfit, changed by the form:

  Vampire  colours deepen to velvet and wine, a crimson silk collar and cuffs with gold edges,
           a bat on the back; pants get a silk side stripe (no blood: Roblox moderates it)
  Wolf     sleeves and trouser legs burst into fur below a ragged tear, claws and paws,
           rips and back slashes showing fur, grime
  Ghoul    grave-rotted: drained and dirt-stained, holes and frayed cuffs show grey skin,
           bony knuckles or bare toes, cross-stitched repairs
  Wraith   the colour drains cold, sleeves, hems and legs dissolve into void and mist with a
           spectral rim, glowing cracks and a sigil on the back
  Priest   sanctified: a warm gold grade, a white stole with gold crosses, gold cuff and hem
           bands, a radiant cross on the back

Every variant keeps the piece's own design, see-through parts and neck hole, and is saved
through nhcloth.save (seam bleed, no dark face borders).

    python Clothing/tools/form_variants.py            # everything
    python Clothing/tools/form_variants.py wolf ghoul # some forms only
Output: Clothing/variants/forms/<form>/<piece>.png and Clothing/variants/forms/manifest.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import lines, poly
from forms import SPECTRAL, VOID, wolf_fur, ghoul_skin, rot_edges, wisps, sigil, paw_pads, stole
import nhcloth

F32 = np.float32
VAR = nhcloth.OUT
SRC = nhcloth.SRC
DEST = VAR / "forms"
FORMS = ["Vampire", "Wolf", "Ghoul", "Wraith", "Priest"]

# every everyday piece in Appearance (Uniforms, BottomsList, RaceUniforms.Ghoul), by the
# template id the game wears it with -> its finished PNG. The five originals are the owner's
# own catalog templates (Clothing/source).
SHIRTS = {
    "shirt_vest_navy_ivory.png": None, "shirt_vest_forest_cream.png": None, "shirt_vest_charcoal_crimson.png": None,
    "shirt_vest_vigil_ivory_gold.png": None, "shirt_vest_crimson_court.png": None, "shirt_polo_navy_khaki.png": None,
    "shirt_polo_forest_khaki.png": None, "shirt_polo_ivory_crimson.png": None, "shirt_polo_crimson_charcoal.png": None,
    "shirt_polo_delinquent.png": None, "shirt_blazer_black_crest.png": None, "shirt_cardigan_charcoal_crest.png": None,
    "shirt_varsity_jacket.png": None, "shirt_gym_pe.png": None,
    "shirt_civ_hoodie_blood_moon.png": None, "shirt_civ_leather_jacket.png": None, "shirt_civ_flannel_open.png": None,
    "shirt_civ_victorian_waistcoat.png": None, "shirt_civ_hussar_coat.png": None, "shirt_civ_tee_the_hollow.png": None,
    "shirt_f_sailor_navy.png": None, "shirt_f_chapel_corset.png": None, "shirt_f_bolero_pinafore.png": None,
    "shirt_f_cheer_shell.png": None, "shirt_f_lolita_bodice.png": None, "shirt_f_cable_knit.png": None,
    "shirt_f_gala_bodice.png": None,
    "shirt_ghoul_uniform_red_vest.png": None, "shirt_ghoul_uniform_red_shirt.png": None,
    "shirt_ghoul_uniform_black_vest.png": None, "shirt_ghoul_uniform_black_shirt.png": None,
    # owner originals: in-game id -> source file
    "orig_red_vest.png": ("11092306245", "shirt_maroon_vest_grey.png"),
    "orig_red_shirt.png": ("11092301473", "shirt_maroon_polo_khaki.png"),
    "orig_black_vest.png": ("11092309131", "shirt_black_red_vest.png"),
    "orig_black_shirt.png": ("11092303922", "shirt_black_polo_khaki.png"),
}
PANTS = {
    "pants_jeans_dark_indigo.png": None, "pants_jeans_black.png": None, "pants_jeans_ripped.png": None,
    "pants_slacks_charcoal.png": None, "pants_trousers_khaki.png": None, "pants_shorts_khaki.png": None,
    "pants_skirt_pleated_tartan.png": None,
    "pants_civ_cargo_boots.png": None, "pants_civ_black_jeans_boots.png": None, "pants_civ_joggers_stripe.png": None,
    "pants_civ_pinstripe_riding_boots.png": None, "pants_civ_skirt_fishnet.png": None,
    "pants_f_sailor_skirt.png": None, "pants_f_chapel_skirt.png": None, "pants_f_pinafore_skirt.png": None,
    "pants_f_cheer_skirt.png": None, "pants_f_lolita_skirt.png": None, "pants_f_plaid_mini.png": None,
    "pants_f_gala_skirt.png": None, "pants_ghoul_uniform.png": None,
    "orig_uniform_pants.png": ("11092315741", "pants_jeans_b.png"),
}

ARMS = rect_mask(ARM_FACES)
TORSO = rect_mask(TORSO_RING)
WAIST = TORSO & (YY >= 178)


def seed_of(name, form):
    return (sum(map(ord, name)) * 31 + sum(map(ord, form)) * 7) % 100000


def load_piece(name):
    spec = SHIRTS.get(name) or PANTS.get(name)
    if spec:
        c = np.array(Image.open(SRC / spec[1]).convert("RGBA")).astype(F32)
        c = remove_magenta(c)
        # the polo's hand-written note on the back is not part of the design
        return c
    return np.array(Image.open(VAR / name).convert("RGBA")).astype(F32)


def neck_hole(c):
    """The piece's own neck opening (transparent, touching the top face), as a bool mask."""
    region = rect_mask(["T_UP", "T_F", "T_B", "T_R", "T_L"])
    tr = (c[..., 3] == 0) & region
    lab, n = ndimage.label(tr)
    if n == 0:
        return tr
    ids = np.unique(lab[rect_mask(["T_UP"]) & tr])
    return np.isin(lab, ids[ids > 0])


def grade(c, vis, mul=(1, 1, 1), sat=1.0, lift_=0.0, toward=None, amt=0.0):
    rgb = c[..., :3]
    g = rgb.mean(-1, keepdims=True)
    out = g + (rgb - g) * sat
    out = out * np.array(mul, F32) + lift_
    if toward is not None:
        out = out * (1 - amt) + np.array(toward, F32) * amt
    c[vis, :3] = np.clip(out, 0, 255)[vis]
    return c


def opaque_limb_rows(c, region):
    """Lowest y that still has cloth on each limb face (sleeve or leg end)."""
    vis = (c[..., 3] > 0) & region
    ys = np.where(vis.any(1))[0]
    return (ys.min(), ys.max()) if len(ys) else (None, None)


def tear_line(base, amp, seed, notches=0.12, depth=(6, 16)):
    return ragged_y(base, amp, seed, notches=notches, depth=depth)


def finish_overlay(c, before, name, folder):
    """Quality-pass shading on the newly painted pixels only, then save (seam bleed)."""
    changed = (np.abs(c - before).sum(-1) > 6) & (c[..., 3] > 0)
    probe = np.full_like(c, 255.0)
    probe[..., 3] = c[..., 3]
    f = finish(probe, creases=False)[..., :3] / 255.0
    c[changed, :3] = np.clip(c[changed, :3] * f[changed], 0, 255)
    sub = DEST / folder
    sub.mkdir(parents=True, exist_ok=True)
    prev = nhcloth.OUT
    nhcloth.OUT = sub
    try:
        return nhcloth.save(c, name)
    finally:
        nhcloth.OUT = prev


# ================================================================== VAMPIRE
SILK = (150, 16, 28)
WINE = (52, 6, 14)


def vampire(c, kind, seed):
    vis = c[..., 3] > 0
    # deepen to velvet: darker, richer, shadows pulled toward wine
    v = c[..., :3].max(-1, keepdims=True) / 255.0
    deep = c[..., :3] * 0.78
    deep = deep * (0.55 + 0.45 * v) + np.array(WINE, F32) * (1 - v) * 0.55
    c[vis, :3] = np.clip(deep, 0, 255)[vis]
    silk = tint(fabric_detail(seed + 1, cloud=0.05, twill=0, grain=0.015), SILK, 10)
    rng = np.random.default_rng(seed)
    if kind == "shirt":
        hole = neck_hole(c)
        if hole.any():
            dist = ndimage.distance_transform_edt(~hole)
            neck = rect_mask(["T_UP", "T_F", "T_B", "T_R", "T_L"]) & vis
            paint(c, (neck & (dist <= 3)).astype(F32), silk)
            paint(c, (neck & (dist > 3) & (dist <= 4)).astype(F32), GOLD)
        # crimson silk turn-back cuffs with gold edges, where the sleeve is long enough
        lo = opaque_limb_rows(c, ARMS & (YY > 420))[1]
        if lo is not None and lo >= 440:
            cuff = ARMS & vis & (YY >= lo - 13) & (YY <= lo - 2)
            c[cuff, :3] = silk[cuff]
            paint(c, (ARMS & vis & ((YY == lo - 14) | (YY == lo - 1))).astype(F32), GOLD)
        # a bat on the back, crimson with a gold rim
        b = bat(491, 132, 56) * vis
        paint(c, ndimage.binary_dilation(b > 0.5, iterations=1).astype(F32) * vis, GOLD)
        paint(c, b, (120, 6, 18))
    else:
        # a silk stripe down the outer seam of each leg, gold-edged
        for n in OUTERS:
            x, y, w, h = R[n]
            mx = x + w // 2
            m = rect_mask([n]) & vis & (np.abs(XX - mx) <= 2)
            c[m, :3] = silk[m]
            paint(c, (rect_mask([n]) & vis & (np.abs(XX - mx) == 3)).astype(F32), GOLD)
        wb = WAIST & vis & (YY >= 179) & (YY <= 181)
        c[wb, :3] = silk[wb]
    return c


# ================================================================== WOLF
def wolf(c, kind, seed):
    coat = wolf_fur(seed)
    rng = np.random.default_rng(seed)
    vis0 = c[..., 3] > 0
    if kind == "shirt":
        edge = tear_line(rng.uniform(398, 414), 6, seed, notches=0.1, depth=(6, 16))
        limb = ARMS
        hands = ["RA_D", "LA_D"]
    else:
        edge = tear_line(rng.uniform(432, 446), 7, seed, notches=0.12, depth=(6, 18))
        limb = rect_mask(LEGS)
        hands = ["RA_D", "LA_D"]
    below = limb & (YY > edge[XX])
    # the limb bursts into fur below the tear (bare skin too: the wolf is furred all over)
    c[below, :3] = coat[below]
    c[below, 3] = 255
    keep = limb & ~below & vis0
    rim = keep & (np.abs(YY - edge[XX]) < 1.2)
    shade(c, rim.astype(F32), 0.45)
    fray = keep & (np.abs(YY - edge[XX]) < 3) & (rng.random((H, W)) < 0.18)
    c[fray, :3] = (232, 226, 212)
    hm = rect_mask(hands)
    c[hm, :3] = coat[hm]
    c[hm, 3] = 255
    if kind == "shirt":
        shade(c, (ARMS & (YY >= 462)).astype(F32), 0.7)
        claws(c, ["RA_F", "LA_F", "RA_R", "LA_L", "RA_L", "LA_R"], 482, n=4, length=9)
        rips = blob_holes((TORSO | (ARMS & ~below)) & vis0, seed + 6, thresh=1.85, sigma=4)
        slash = np.zeros((H, W), bool)
        for k in range(3):
            x0 = 452 + k * 15
            slash |= (poly([(x0, 92), (x0 + 6, 92), (x0 + 38, 176), (x0 + 30, 178)]) > 0.5) & \
                (noise(H, W, seed + 10 + k, 1.2) > -1.2)
        slash &= vis0
        hole = neck_hole(c)
        if hole.any():
            dist = ndimage.distance_transform_edt(~hole)
            chest = fur((80, 70, 60), (214, 200, 174), seed + 1, angle=96, length=(6, 11), mottle=0.8)
            mane = rect_mask(["T_UP", "T_F", "T_B", "T_R", "T_L"]) & (dist <= 6) & vis0
            c[mane, :3] = chest[mane]
    else:
        paw_pads(c, hands)
        claws(c, FRONTS, 482, n=4, length=8)
        rips = blob_holes((rect_mask(LEGS) & ~below | WAIST) & vis0, seed + 6, thresh=1.9, sigma=4)
        slash = np.zeros((H, W), bool)
    burst = rips | slash
    shade(c, (ndimage.binary_dilation(burst, iterations=1) & ~burst & vis0).astype(F32), 0.5)
    c[burst, :3] = coat[burst]
    grime = (c[..., 3] > 0) & ~below & ~burst
    scuffs(c, grime, seed + 7, amount=0.4, color=(70, 56, 40), blobs=22, spread=5)
    return c


# ================================================================== GHOUL
def ghoul(c, kind, seed):
    skin = ghoul_skin(seed)
    rng = np.random.default_rng(seed)
    vis0 = c[..., 3] > 0
    # drained and grave-stained
    grade(c, vis0, mul=(0.86, 0.9, 0.8), sat=0.55, toward=(70, 74, 52), amt=0.16)
    limb = ARMS if kind == "shirt" else rect_mask(LEGS)
    lo = opaque_limb_rows(c, limb)[1]
    base_y = (lo - 16) if lo is not None else 440
    edge = tear_line(base_y, 4, seed, notches=0.14, depth=(4, 10))
    below = limb & (YY > edge[XX]) & vis0
    c[below, :3] = skin[below]
    holes = blob_holes((TORSO | limb | WAIST) & vis0 & ~below, seed + 1, thresh=2.0, sigma=5)
    if kind == "pants":
        holes &= (rect_mask(LEGS) | WAIST)
    c[holes, :3] = skin[holes]
    cloth = vis0 & ~below & ~holes
    rot_edges(c, cloth, seed)
    scuffs(c, cloth, seed + 3, amount=0.55, color=(52, 42, 28), blobs=34, spread=5)
    mould = (noise(H, W, seed + 4, 1.1) > 2.2) & cloth
    c[mould, :3] = c[mould, :3] * 0.6 + np.array((90, 110, 60), F32) * 0.4
    if kind == "shirt":
        for n in ARM_FACES:
            x, y, w, h = R[n]
            if not (vis0 & rect_mask([n]) & (YY > 466)).any():
                continue
            for kx in range(x + 8, x + w - 4, 12):
                paint(c, shape(lambda d: d.ellipse((kx - 2, 468, kx + 2, 472), fill=255)) * vis0, (200, 194, 168))
                paint(c, lines([(kx, 479), (kx, 482)], 2) * vis0, (36, 28, 24))
        stitches(c, [(468, 150), (486, 140), (506, 150)])
        stitches(c, [(252, 120), (262, 134)])
    else:
        for n in FRONTS:
            x, y, w, h = R[n]
            if not (vis0 & rect_mask([n]) & (YY > 470)).any():
                continue
            for k, tx in enumerate(range(x + 8, x + w - 6, 11)):
                paint(c, shape(lambda d: d.ellipse((tx, 472, tx + 8, 482), fill=255)) * vis0, (150, 156, 132))
                paint(c, shape(lambda d: d.arc((tx, 472, tx + 8, 482), 200, 340, fill=255)) * vis0, (60, 58, 46))
        stitches(c, [(30, 400), (46, 392), (60, 404)])
    return c


# ================================================================== WRAITH
def wraith(c, kind, seed):
    vis0 = c[..., 3] > 0
    g = c[..., :3].mean(-1, keepdims=True)
    cold = np.clip(g * np.array((0.78, 0.92, 1.05), F32) * 0.88, 0, 255)
    c[vis0, :3] = cold[vis0]
    rng = np.random.default_rng(seed)
    limb = ARMS if kind == "shirt" else rect_mask(LEGS)
    edge = tear_line(rng.uniform(418, 430) if kind == "shirt" else rng.uniform(438, 450), 7, seed,
                     notches=0.16, depth=(6, 18))
    below = limb & (YY > edge[XX])
    c[below, :3] = VOID
    c[below, 3] = 255
    wisps(c, below, seed, int(edge.mean()), length=26, n_per=9)
    glow(c, (limb & (np.abs(YY - edge[XX]) < 1.0) & vis0).astype(F32), SPECTRAL, sigma=3.5, strength=0.35, core=False)
    if kind == "shirt":
        hem = ragged_y(194, 4, seed + 1, notches=0.2, depth=(3, 7))
        gone = TORSO & (YY > hem[XX]) & vis0
        c[gone, :3] = VOID
        wisps(c, gone, seed + 2, 194, length=8, n_per=8)
        glow(c, sigil(491, 140, 20) * 0.85 * vis0, SPECTRAL, sigma=4, strength=0.7)
        cracks = [[(250, 100), (258, 118), (254, 134)], [(170, 120), (184, 140)], [(400, 110), (392, 136)]]
    else:
        cracks = [[(240, 186), (250, 196)], [(40, 380), (48, 400), (44, 414)], [(330, 372), (340, 396)]]
    for pts in cracks:
        glow(c, lines(pts) * (c[..., 3] > 0), SPECTRAL, sigma=1.6, strength=0.55)
    frost = (noise(H, W, seed + 5, 0.8) > 2.5) & vis0 & ~below
    c[frost, :3] = np.clip(c[frost, :3] * 0.5 + np.array((200, 236, 250), F32) * 0.5, 0, 255)
    return c


# ================================================================== PRIEST
def priest(c, kind, seed):
    vis0 = c[..., 3] > 0
    grade(c, vis0, mul=(1.02, 1.0, 0.94), sat=0.85, lift_=4, toward=(214, 186, 120), amt=0.1)
    if kind == "shirt":
        hole = neck_hole(c)
        # a white stole over the shoulders, hanging down the front
        top = 74
        if hole.any():
            ys = np.where((hole & rect_mask(["T_F"])).any(1))[0]
            top = (ys.max() + 2) if len(ys) else 74
        for x0 in (CX - 26, CX + 14):
            stole(c, int(x0), int(x0 + 12), 74, 201, step=24, start=top + 14)
        glow(c, shape(lambda d: d.ellipse((471, 112, 511, 168), fill=255)) * 0.5 * vis0, (255, 226, 150), sigma=6, strength=0.45, core=False)
        cross(c, 491, 140, 22, 40, 6, fill=(255, 238, 190))
        lo = opaque_limb_rows(c, ARMS & (YY > 420))[1]
        if lo is not None and lo >= 430:
            paint(c, (ARMS & vis0 & ((YY == lo - 4) | (YY == lo - 6))).astype(F32), GOLD)
        paint(c, (TORSO & vis0 & ((YY == 198) | (YY == 196))).astype(F32), GOLD)
    else:
        lo = opaque_limb_rows(c, rect_mask(LEGS) & (YY < 470))[1]
        if lo is not None:
            band = rect_mask(LEGS) & vis0 & (YY >= lo - 8) & (YY <= lo - 5)
            paint(c, band.astype(F32), GOLD)
        for n in OUTERS:
            x, y, w, h = R[n]
            cross(c, x + w / 2, 392, 10, 16, 3)
        paint(c, (WAIST & vis0 & (YY == 180)).astype(F32), GOLD)
    return c


TRANSFORMS = {"Vampire": vampire, "Wolf": wolf, "Ghoul": ghoul, "Wraith": wraith, "Priest": priest}


def build(forms=FORMS):
    out = {}
    with nhcloth.supersample(4):
        for table, kind in ((SHIRTS, "shirt"), (PANTS, "pants")):
            for name in table:
                base = load_piece(name)
                keep_clear = (base[..., 3] == 0) & (rect_mask(["T_UP", "T_F", "T_B", "T_R", "T_L", "T_D"])
                                                    if kind == "shirt" else rect_mask(["T_UP"]) | (TORSO & (YY < 178)))
                for form in forms:
                    c = base.copy()
                    TRANSFORMS[form](c, kind, seed_of(name, form))
                    if kind == "pants":         # the torso above the waistband sits under the shirt: leave it as it was
                        hidden = rect_mask(["T_UP"]) | (TORSO & (YY < 178))
                        c[hidden] = base[hidden]
                    clear(c, keep_clear)       # neck hole and see-through torso stay see-through
                    p = finish_overlay(c, base, name, form.lower())
                    out.setdefault(name, {})[form] = f"{form.lower()}/{p.name}"
                print("ok", name, flush=True)
    return out


if __name__ == "__main__":
    forms = [f.capitalize() for f in sys.argv[1:]] or FORMS
    res = build(forms)
    # the manifest is rebuilt from what is on disk, so per-form runs can go in parallel
    man = {}
    for f in FORMS:
        for p in sorted((DEST / f.lower()).glob("*.png")) if (DEST / f.lower()).exists() else []:
            man.setdefault(p.name, {})[f] = f"{f.lower()}/{p.name}"
    (DEST / "manifest.json").write_text(json.dumps(man, indent=1))
    print(len(res), "pieces x", len(forms), "forms")
