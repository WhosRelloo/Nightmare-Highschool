"""Anatomy elective: the bench HUD chrome (Nightmare Highschool), motif "the specimen chart".

Design: docs/superpowers/specs/2026-11-25-electives-anatomy-design.md (§5).
Baked with the house PBR shader (make_health_pbr.py): height field -> normals plus the school's seamless detail maps,
GGX + Lambert, warm key, cool fill, candle rim, AO. Text, organ outlines and the hold fill are live in game.

Pieces (art/ui/hud/out/anatomy/):
  AnatPlate.png      1000x140  blackened-iron title plate, brass bead, a loupe roundel on the left (9-slice 150..940)
  AnatProcedure.png   400x580  parchment procedure card on a brass tack, crimson rule under the title band
  AnatSpecimen.png    400x580  porcelain specimen card in a riveted brass frame, engraved hairline grid
  AnatSeal.png        240x240  oxblood wax seal pressed with the loupe (grade stamp; letter is live)
  AnatHold.png        180x180  the hold ring: a brass socket the wick-gold fill sweeps round
  AnatTag.png         128x52   a brass luggage tag with an eyelet (the 1-5 hotkey labels beside the tools)

  python make_anatomy_ui.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as P
import make_belltower as B

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "anatomy"
OUT.mkdir(parents=True, exist_ok=True)

dist, soft, mix = B.dist, B.soft, B.mix


def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def drop(rgb, alpha, off=(7, 5), blur=6, k=0.55):
    sh = ndimage.shift(ndimage.gaussian_filter(alpha, blur), off) * k
    out_a = np.clip(alpha + sh * (1 - alpha), 0, 1)
    return rgb * alpha[..., None] / np.maximum(out_a[..., None], 1e-3), out_a


def octagon(W, H, cut, inset=0):
    return P.polymask((W, H), [[(cut + inset, inset), (W - cut - inset, inset), (W - inset, cut + inset), (W - inset, H - cut - inset),
                                (W - cut - inset, H - inset), (cut + inset, H - inset), (inset, H - cut - inset), (inset, cut + inset)]])


def loupe_emblem(W, H, cx, cy, s):
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    R = np.hypot(XX - cx, YY - cy)
    ring = soft(((R > 0.42 * s) & (R < 0.6 * s)).astype(np.float32))
    lens = soft((R <= 0.42 * s).astype(np.float32))
    a = math.radians(45)
    u = (XX - cx) * math.cos(a) + (YY - cy) * math.sin(a)
    v = -(XX - cx) * math.sin(a) + (YY - cy) * math.cos(a)
    handle = soft(((u > 0.6 * s) & (u < 1.25 * s) & (np.abs(v) < 0.13 * s)).astype(np.float32))
    return ring, lens, handle


# ---------------------------------------------------------------- the title plate
def plate():
    W, H = 1000, 140
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = B.mats(W, H, 240)
    body = octagon(W, H, 20, 4)
    inner = octagon(W, H, 20, 15)
    bead = np.clip(body - inner, 0, 1)
    cx, cy = 74, H / 2
    R = np.hypot(XX - cx, YY - cy)
    roundel = soft((R <= 58).astype(np.float32))
    rrim = soft(((R > 49) & (R <= 58)).astype(np.float32))
    ring, lens, handle = loupe_emblem(W, H, cx - 6, cy - 6, 52)
    emb = np.clip(ring + handle, 0, 1) * roundel
    rivs = P.polymask((W, H), [], [(x - 6, y - 6, x + 6, y + 6) for x in (160, W - 30) for y in (30, H - 30)])
    Hf = body * 0.28 + (P.periodic_noise(H, W, 3, 7) * 0.01 if hasattr(P, "periodic_noise") else 0)
    Hf = np.maximum(Hf, bead * (0.5 + 0.35 * P.dome(dist(bead), 5)))
    Hf = np.maximum(Hf, roundel * (0.45 + 0.2 * P.dome(dist(roundel), 14)))
    Hf = np.maximum(Hf, rrim * (0.7 + 0.25 * P.dome(dist(rrim), 4)))
    Hf = Hf + emb * 0.12 + lens * roundel * 0.04
    Hf = np.maximum(Hf, rivs * (0.9 + 0.2 * P.dome(dist(rivs), 5)))
    isb = np.clip(bead + rivs + rrim + emb, 0, 1)
    albedo = mix(iron[0] * 0.42, brass[0], isb)
    albedo = mix(albedo, np.array([0.14, 0.2, 0.32]) * 0.6, lens * roundel * 0.8)   # a blued-glass lens
    albedo = mix(albedo, brass[0] * 0.6, roundel * (1 - isb) * (1 - lens) * 0.7)
    rough = mix(mix(iron[2], brass[2], isb), 0.08, lens * roundel)
    metal = mix(np.full((H, W), 0.7, np.float32), 1.0, isb)
    metal = mix(metal, 0.0, lens * roundel)
    N = P.normals_from(Hf, 22.0, mix(iron[1], brass[1], isb), 0.25)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 4, 2.0))
    alpha = np.clip(bead + rivs + inner * 0.9 + roundel, 0, 1)
    save(*drop(rgb, alpha), "AnatPlate.png")


# ---------------------------------------------------------------- the procedure card
def procedure():
    W, H = 400, 580
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    pap = B.paper_tex(W, H, 320, tint=(1.0, 0.91, 0.74))
    iron, brass = B.mats(W, H, 200)
    card = B.deckle(W, H, 14, 41, 2.4)
    rng = np.random.default_rng(5)
    fox = np.clip((ndimage.gaussian_filter(rng.standard_normal((H, W)), 16) - 0.02) * 6, 0, 1) * 0.22
    tack_c = (W / 2, 34)
    R = np.hypot(XX - tack_c[0], YY - tack_c[1])
    tack = soft((R <= 15).astype(np.float32))
    Hf = card * 0.25 - np.clip(1 - dist(card) / 12, 0, 1) * card * 0.05
    Hf = np.maximum(Hf, tack * (0.6 + 0.5 * P.dome(dist(tack), 13)))
    dimple = np.exp(-(((XX - tack_c[0]) / 26) ** 2 + ((YY - tack_c[1] - 4) / 20) ** 2)) * card * 0.04   # paper pulled by the pin
    Hf -= dimple
    rule = ((np.abs(YY - 108) < 1.4) & (XX > 36) & (XX < W - 36)).astype(np.float32)
    lines = (((YY - 150) % 46 < 1.0) & (YY > 140) & (YY < H - 40) & (XX > 36) & (XX < W - 36)).astype(np.float32) * 0.35
    albedo = pap[0] * (1 - fox[..., None]) + np.array([0.36, 0.22, 0.1]) * fox[..., None]
    edge = np.clip(1 - dist(card) / 14, 0, 1) * card
    albedo = albedo * (1 - edge[..., None] * 0.45)
    albedo = mix(albedo, np.array([0.42, 0.03, 0.04]), rule)
    albedo = mix(albedo, np.array([0.45, 0.38, 0.28]), lines)
    albedo = mix(albedo, brass[0], tack)
    rough = mix(pap[2], brass[2] * 0.7, tack)
    metal = mix(np.zeros((H, W), np.float32), 1.0, tack)
    N = P.normals_from(Hf, 18.0, mix(pap[1], brass[1], tack), 0.25)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 4, 2.0))
    save(*drop(rgb, np.clip(card + tack, 0, 1), (9, 6), 8), "AnatProcedure.png")


# ---------------------------------------------------------------- the specimen card (porcelain in a brass frame)
def specimen():
    W, H = 400, 580
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = B.mats(W, H, 200)
    frame = octagon(W, H, 26, 2)
    face = octagon(W, H, 22, 18)
    bezel = np.clip(frame - face, 0, 1)
    rivs = P.polymask((W, H), [], [(x - 7, y - 7, x + 7, y + 7) for x in (30, W - 30) for y in (30, H - 30)] +
                      [(W / 2 - 6, 4, W / 2 + 6, 16), (W / 2 - 6, H - 16, W / 2 + 6, H - 4)])
    grid = ((((XX - 18) % 24) < 0.9) | (((YY - 18) % 24) < 0.9)).astype(np.float32) * face
    title_rule = ((np.abs(YY - 116) < 1.2) & (XX > 40) & (XX < W - 40)).astype(np.float32)
    crackle = ndimage.gaussian_filter(np.random.default_rng(9).standard_normal((H, W)), 1.2)
    crackle = (np.abs(crackle) < 0.012).astype(np.float32) * face * 0.25
    Hf = frame * 0.3
    Hf = np.maximum(Hf, bezel * (0.55 + 0.35 * P.dome(dist(bezel), 7)))
    Hf = np.maximum(Hf, face * (0.42 + 0.04 * P.dome(dist(face), 30)))
    Hf -= (grid * 0.004 + title_rule * 0.006)
    Hf = np.maximum(Hf, rivs * (1.0 + 0.2 * P.dome(dist(rivs), 5)))
    porcelain = np.array([0.86, 0.83, 0.76])
    albedo = np.broadcast_to(porcelain, (H, W, 3)).copy()
    albedo = mix(albedo, np.array([0.55, 0.48, 0.38]), grid * 0.35)
    albedo = mix(albedo, np.array([0.42, 0.03, 0.04]), title_rule)
    albedo = mix(albedo, np.array([0.5, 0.42, 0.3]), crackle)
    isb = np.clip(bezel + rivs, 0, 1)
    albedo = mix(albedo, brass[0], isb)
    rough = mix(np.full((H, W), 0.14, np.float32), brass[2], isb)
    metal = mix(np.zeros((H, W), np.float32), 1.0, isb)
    N = P.normals_from(Hf, 20.0, brass[1], 0.2 * 1)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 4, 2.0))
    save(*drop(rgb, np.clip(frame + rivs, 0, 1)), "AnatSpecimen.png")


# ---------------------------------------------------------------- the grade seal
def seal():
    S = 240
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    rng = np.random.default_rng(3)
    ang = np.arctan2(YY - c, XX - c)
    wob = 1 + 0.05 * np.sin(ang * 7 + 0.5) + 0.03 * np.sin(ang * 13 + 2)
    R = np.hypot(XX - c, YY - c) / wob
    blob = soft((R <= 108).astype(np.float32), 1.2)
    well = soft((np.hypot(XX - c, YY - c) <= 76).astype(np.float32))
    ring_in = soft(((np.hypot(XX - c, YY - c) > 80) & (np.hypot(XX - c, YY - c) < 86)).astype(np.float32))
    ring, lens, handle = loupe_emblem(S, S, c - 18, c - 18, 30)
    emb = np.clip(ring + handle, 0, 1)
    Hf = blob * (0.3 + 0.35 * P.dome(dist(blob), 26))
    Hf -= well * 0.1
    Hf += ring_in * 0.05 + emb * 0.06
    Hf += ndimage.gaussian_filter(rng.standard_normal((S, S)), 3) * 0.006 * blob
    albedo = np.broadcast_to(np.array([0.19, 0.012, 0.02]), (S, S, 3)).copy()
    albedo = mix(albedo, np.array([0.2, 0.015, 0.02]), well * 0.5)
    rough = np.full((S, S), 0.3, np.float32)
    N = P.normals_from(Hf, 26.0)
    rgb = P.shade(albedo, N, rough, np.zeros((S, S), np.float32), P.ao_from(Hf, 4, 2.0))
    save(*drop(rgb, blob, (5, 4), 5, 0.5), "AnatSeal.png")


# ---------------------------------------------------------------- the hold ring
def hold():
    S = 180
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    iron, brass = B.mats(S, S, 180)
    R = np.hypot(XX - c, YY - c)
    outer = soft(((R > 62) & (R <= 76)).astype(np.float32))
    groove = soft(((R > 50) & (R <= 62)).astype(np.float32))
    inner = soft(((R > 44) & (R <= 50)).astype(np.float32))
    ticks = np.zeros_like(R)
    ang = (np.degrees(np.arctan2(YY - c, XX - c)) + 360) % 360
    ticks = ((ang % 30 < 2.2) & (R > 64) & (R < 74)).astype(np.float32)
    Hf = np.maximum(outer * (0.55 + 0.3 * P.dome(dist(outer), 5)), inner * (0.5 + 0.25 * P.dome(dist(inner), 3)))
    Hf = np.maximum(Hf, groove * 0.25) - ticks * 0.05
    isb = np.clip(outer + inner, 0, 1)
    albedo = mix(iron[0] * 0.35, brass[0], isb)
    rough = mix(iron[2], brass[2], isb)
    metal = mix(np.full((S, S), 0.7, np.float32), 1.0, isb)
    N = P.normals_from(Hf, 20.0, brass[1], 0.2)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 3, 2.0))
    save(*drop(rgb, np.clip(outer + groove + inner, 0, 1), (4, 3), 4), "AnatHold.png")


# ---------------------------------------------------------------- the hotkey tag
def tag():
    W, H = 128, 52
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = B.mats(W, H, 128)
    body = P.polymask((W, H), [[(18, 4), (W - 6, 4), (W - 2, 8), (W - 2, H - 8), (W - 6, H - 4), (18, H - 4), (3, H / 2)]])
    eye = soft((np.hypot(XX - 20, YY - H / 2) <= 6).astype(np.float32))
    eyering = soft(((np.hypot(XX - 20, YY - H / 2) > 6) & (np.hypot(XX - 20, YY - H / 2) <= 9)).astype(np.float32))
    border = np.clip(body - soft((dist(body) > 4).astype(np.float32)), 0, 1)
    Hf = body * (0.3 + 0.08 * P.dome(dist(body), 6)) + border * 0.05
    Hf = np.maximum(Hf, eyering * 0.5)
    albedo = brass[0] * 0.9
    N = P.normals_from(Hf, 16.0, brass[1], 0.25)
    rgb = P.shade(albedo, N, brass[2] * 0.9, np.ones((H, W), np.float32), P.ao_from(Hf, 2, 2.0))
    save(*drop(rgb, np.clip(body - eye, 0, 1), (3, 2), 3, 0.5), "AnatTag.png")


if __name__ == "__main__":
    for f in (plate, procedure, specimen, seal, hold, tag):
        f()
        print("ok", f.__name__)
