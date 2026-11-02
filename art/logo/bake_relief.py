"""Bake the Nightmare High logo into a height map + material ids for the Blender relief (nh_logo_pbr.py).

usage: python bake_relief.py [scale]   -> art/logo/build/height.npy, matid.npy, lum.npy, preview_height.png
Layers (back to front): wings + scrollwork (pillowed edges, red trims embossed), the shield plate, its icons,
the spike, the ribbon, the lettering. Material ids: 0 black iron, 1 crimson enamel, 2 silver (lettering / glints).
"""
import os
import sys

import cv2
import numpy as np

from regions import RIBBON, SHIELD, SPIKE

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)
S = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0

src = cv2.imread(os.path.join(HERE, "source.png"), cv2.IMREAD_UNCHANGED)
im = cv2.resize(src, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
h, w = im.shape[:2]
a = cv2.GaussianBlur(im[..., 3].astype(np.float32) / 255, (0, 0), 0.6 * S)
b, g, r = [im[..., i].astype(np.float32) for i in range(3)]
sil = (a > 0.5).astype(np.uint8)


def poly(pts):
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts) * S).astype(np.int32)], 1)
    return m & sil


def pillow(mask, px):
    """0 at the mask edge rising to 1 at px pixels in: a rounded bevel."""
    d = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip(d / (px * S), 0, 1)
    return np.sin(t * np.pi / 2)


lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
red = ((r > 110) & (r > g * 2.0) & (r > b * 2.0)).astype(np.uint8) & sil
white = ((r > 165) & (g > 165) & (b > 165)).astype(np.uint8) & sil
sat = (np.max(im[..., :3], 2).astype(np.float32) - np.min(im[..., :3], 2)) / 255
light = ((lum > 0.34) & (sat < 0.3)).astype(np.uint8) & sil                  # the silver lettering incl. its shading
light = cv2.morphologyEx(light, cv2.MORPH_CLOSE, np.ones((int(2 * S), int(2 * S)), np.uint8))
nL, labL, stL, _ = cv2.connectedComponentsWithStats(light, 8)
for i in range(1, nL):
    if stL[i, cv2.CC_STAT_AREA] < 30 * S * S:
        light[labL == i] = 0
shield, ribbon, spike = poly(SHIELD), poly(RIBBON), poly(SPIKE)
# the lettering overhangs the banner edges in the art: letters near the banner count as banner
ribbon = ribbon | (white & cv2.dilate(ribbon, np.ones((int(14 * S), int(14 * S)), np.uint8)))
ribbon = cv2.morphologyEx(ribbon, cv2.MORPH_CLOSE, np.ones((int(3 * S), int(3 * S)), np.uint8)) & sil
red_o = (cv2.GaussianBlur(red.astype(np.float32), (0, 0), 0.9 * S) > 0.5).astype(np.uint8)   # smooth trims, no pixel noise

H = 0.05 * sil + 0.10 * pillow(sil, 7)                                  # wings / scrolls body
H += 0.02 * pillow(red_o & (1 - shield) & (1 - ribbon), 1.2)           # red trims and scroll beads stand proud
H += 0.20 * pillow(shield, 5)                                           # the shield plate
H += 0.012 * pillow(red_o & shield, 0.8)                                # quartered icons / frame lines
H += 0.14 * pillow(spike & (1 - ribbon), 3)
H += 0.34 * pillow(ribbon, 5)                                           # banner in front
H += 0.035 * pillow(light & ribbon, 0.8)                                # raised lettering
hp = lum - cv2.GaussianBlur(lum, (0, 0), 3 * S)                         # fine sculpt detail from the art
H += 0.004 * hp * sil
H = cv2.GaussianBlur(H.astype(np.float32), (0, 0), 0.35 * S) * sil

mat = np.zeros((h, w), np.uint8)
mat[red.astype(bool)] = 1
mat[white.astype(bool)] = 2
# keep isolated specular glints on black parts iron, not silver: silver only where it's lettering or a big highlight
small_white = white & (1 - ribbon)
n, lab, stats, _ = cv2.connectedComponentsWithStats(small_white, 8)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] < 40 * S * S:
        mat[lab == i] = 0

# PBR maps: albedo = the art with its painted highlights tamed (the renderer relights it), plus metal / rough
hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2HSV).astype(np.float32)
v = hsv[..., 2] / 255
hsv[..., 2] = np.clip(0.06 + 0.9 * v, 0, 1) * 255
alb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
let = cv2.GaussianBlur((light & ribbon).astype(np.float32), (0, 0), 0.5 * S)[..., None]
alb = (alb * (1 - let) + np.array([228, 226, 222], np.float32) * let).astype(np.uint8)   # clean silver lettering
redness = np.clip((r - np.maximum(g, b)) / 120, 0, 1) * sil
silv = cv2.GaussianBlur((light & ribbon).astype(np.float32), (0, 0), 0.6 * S)
metal = np.clip(0.25 + 0.15 * redness + 0.75 * silv, 0, 1)
rough = np.clip(0.55 - 0.3 * redness - 0.35 * silv, 0.08, 1)
pack = np.dstack([rough, metal, redness]) * 255                               # B,G,R in cv2 order -> R=redness G=metal B=rough
alpha = (sil * 255).astype(np.uint8)
cv2.imwrite(os.path.join(OUT, "albedo.png"), np.dstack([alb, alpha]))
cv2.imwrite(os.path.join(OUT, "maskpack.png"), pack.astype(np.uint8))
np.save(os.path.join(OUT, "height.npy"), H.astype(np.float32))
np.save(os.path.join(OUT, "matid.npy"), mat)
np.save(os.path.join(OUT, "lum.npy"), lum.astype(np.float32))
np.save(os.path.join(OUT, "sil.npy"), sil)
cv2.imwrite(os.path.join(OUT, "preview_height.png"), (H / max(H.max(), 1e-6) * 255).astype(np.uint8))
print("baked", w, h, "max height", float(H.max()))
