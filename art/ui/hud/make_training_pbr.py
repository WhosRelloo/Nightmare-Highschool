"""Training HUD art, stage 1 of 2: the designs as relief + material maps for the Blender PBR render.

Each piece is drawn in 2D (shapes from make_training_ui.py) as a HEIGHT field with a MATERIAL id per pixel. Stage 2
(blender_training_render.py, headless Blender + Cycles) builds every piece as real displaced geometry, gives each
material id a full PBR shader (brass, gilt, black iron, ink and crimson enamel, crimson and black leather, ivory, wax,
chalk, oak, glass, sand, candle flame), lights it with the HUD's warm key, cool fill and candle rim, renders it with
transparency, and stage 3 (finish_training_ui.py) bleeds the colour into the clear pixels (no dark fringes), sizes the
pieces and writes the upload folder.

    python make_training_pbr.py [Name ...]   ->  out/training/maps/<Name>_h.png (16-bit) _m.png _a.png _r.png, pieces.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as H
import make_app_icons as A
from make_app_icons import (M, box, circle, ring, seg, ellipse, poly, U, sub, text, inner_dist, smooth, sd_circle, xx, yy, bez)
from make_training_ui import limb, shield_pts, star_pts, GAUGE_MARK_R, RING_R

HERE = Path(__file__).resolve().parent
MAPS = HERE / "out" / "training" / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
S = A.S
f32 = np.float32

# material ids (stage 2 has the shaders)
MAT = {"none": 0, "brass": 1, "gilt": 2, "iron": 3, "ink": 4, "crimson_enamel": 5, "ivory": 6, "leather": 7,
       "leather_black": 8, "wax": 9, "wax_red": 10, "chalk": 11, "glass": 12, "flame": 13, "oak": 14, "sand": 15,
       "brass_old": 16, "steel": 17}


class P:
    """a relief: height, material id, alpha, a contact-shadow mask"""

    def __init__(self, seed, w=S, h=S):
        self.W, self.Hh = w, h
        self.h = np.zeros((h, w), f32)
        self.m = np.zeros((h, w), f32)
        self.a = np.zeros((h, w), f32)
        self.r = np.full((h, w), 0.5, f32)
        self.seed, self.k = seed, 0

    def noise(self, sigma):
        self.k += 1
        r = np.random.default_rng(self.seed * 1000 + self.k)
        n = ndimage.gaussian_filter(r.random((self.Hh, self.W)).astype(f32), sigma, mode="wrap")
        return (n - n.min()) / (n.max() - n.min() + 1e-6)

    def custom(self, mask, h, mat, rough=None):
        self.h = self.h * (1 - mask) + h * mask
        sel = mask > 0.5
        self.m[sel] = MAT[mat]
        if rough is not None:
            self.r = self.r * (1 - mask) + rough * mask
        self.a = np.maximum(self.a, mask)

    def part(self, mask, z=0.20, lift=0.16, bevel=26, mat="ivory", tex=0.010, rough=None):
        d = (ndimage.distance_transform_edt(mask > 0.5) + (mask - 0.5) * (mask < 1)).astype(f32)
        h = z + lift * H.dome(d, bevel) + tex * self.noise(2.0) + tex * 1.6 * self.noise(14)
        self.custom(mask, h, mat, rough)

    def groove(self, mask, depth=0.07):
        self.h -= mask * depth

    def emboss(self, mask, lift=0.08, bevel=8, mat=None):
        d = (ndimage.distance_transform_edt(mask > 0.5)).astype(f32)
        self.h += mask * lift * H.dome(d, bevel)
        if mat:
            self.m[mask > 0.5] = MAT[mat]

    def recess(self, mask, depth=0.10, bevel=8, mat=None):
        d = (ndimage.distance_transform_edt(mask > 0.5)).astype(f32)
        self.h -= mask * depth * H.dome(d, bevel)
        if mat:
            self.m[mask > 0.5] = MAT[mat]

    def paint(self, mask, mat):
        self.m[mask > 0.5] = MAT[mat]


def export(p, name, size, kind="icon", extra=None):
    MAPS.mkdir(parents=True, exist_ok=True)
    hh = np.clip(p.h, 0, 1)
    Image.fromarray((hh * 65535).astype(np.uint16)).save(MAPS / f"{name}_h.png")
    Image.fromarray(p.m.astype(np.uint8)).save(MAPS / f"{name}_m.png")
    Image.fromarray((np.clip(p.a, 0, 1) * 255).astype(np.uint8)).save(MAPS / f"{name}_a.png")
    Image.fromarray((np.clip(p.r, 0, 1) * 255).astype(np.uint8)).save(MAPS / f"{name}_r.png")
    info = {"name": name, "w": p.W, "h": p.Hh, "out": size, "kind": kind}
    if extra:
        info.update(extra)
    print("  maps", name, p.W, p.Hh)
    return info


def rough_edge(mask, p, k=0.4, sigma=2.2):
    n = p.noise(sigma)
    return np.clip((mask - 0.5 + (n - 0.5) * k) * 4 + 0.5, 0, 1) * (mask > 0.02)


R_ = lambda: np.hypot(xx - S / 2, yy - S / 2)
TH_ = lambda: np.arctan2(yy - S / 2, xx - S / 2)


# ================================================================ the gauge
def gauge():
    p = P(1)
    r, th = R_(), TH_()
    # bezel 440..500, knurled outer band, an engraved line, twelve rivets
    bez_m = np.clip(np.minimum(r - 440, 500 - r) + 0.5, 0, 1).astype(f32)
    d = np.clip(np.minimum(r - 440, 500 - r), 0, None)
    hb = 0.34 + 0.20 * H.dome(d, 26) + 0.03 * ((r > 482) & (r < 500)) * np.cos(th * 160)
    hb -= 0.05 * np.clip(1 - np.abs(r - 458) / 2.5, 0, 1)
    p.custom(bez_m, hb, "brass")
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        cx, cy = 512 + 470 * math.cos(a), 512 + 470 * math.sin(a)
        dd = np.hypot(xx - cx, yy - cy)
        m = np.clip(11.5 - dd, 0, 1)
        p.custom(m, 0.52 + 0.08 * np.sqrt(np.clip(1 - dd / 11, 0, 1)), "brass_old")
    # the face: ink enamel, with engraved brass guide rings and chalk ticks
    face = np.clip(440.5 - r, 0, 1).astype(f32)
    p.custom(face, 0.18 - 0.05 * np.clip(1 - (440 - r) / 18, 0, 1) + 0.004 * p.noise(6), "ink", 0.12)
    for rr, w in ((372, 2.6), (310, 2.0), (250, 1.6)):
        g = np.clip(1 - np.abs(r - rr) / w, 0, 1) * face
        p.groove(g, 0.012)
        p.paint(g, "brass_old")
    deg = (np.degrees(th) + 360) % 360
    for step, r0, w in ((7.5, 412, 2.4), (30, 394, 4.0)):
        kk = np.abs(((deg + step / 2) % step) - step / 2) * (math.pi / 180) * r
        tick = np.clip(w - kk, 0, 1) * ((r > r0) & (r < 430)) * face
        p.h += 0.01 * tick
        p.paint(tick, "chalk")
    # the crimson vignette near the rim is a separate enamel (stage 2 blends it by radius)
    # the MARK: a raised brass channel with a crimson enamel groove and a gilt hairline
    ch = np.clip(np.minimum(r - 170, 210 - r) + 0.5, 0, 1).astype(f32)
    dch = np.clip(np.minimum(r - 170, 210 - r), 0, None)
    hc = 0.27 + 0.10 * H.dome(dch, 9)
    p.custom(ch, hc, "brass")
    grv = np.clip(np.minimum(r - 182, 198 - r) + 0.5, 0, 1).astype(f32)
    p.groove(grv, 0.07)
    p.paint(grv, "crimson_enamel")
    hair = np.clip(1.6 - np.abs(r - GAUGE_MARK_R), 0, 1)
    p.paint(hair, "gilt")
    p.h += hair * 0.01
    # centre boss with an engraved quatrefoil
    boss = np.clip(118.5 - r, 0, 1).astype(f32)
    qa = np.abs(np.cos(2 * th))
    hbz = 0.32 + 0.12 * H.dome(np.clip(118 - r, 0, None), 30)
    hbz -= 0.03 * np.clip(1 - np.abs(r - (64 + 22 * qa)) / 3.0, 0, 1)
    hbz -= 0.025 * np.clip(1 - np.abs(r - 100) / 2.2, 0, 1)
    p.custom(boss, hbz, "brass")
    p.a = np.clip(500.5 - r, 0, 1).astype(f32)
    return export(p, "TrainGauge", 1024, "gauge")


def needle():
    """the gauge's needle: a blued-steel pointer with a gilt tip and a brass hub (points up; the HUD turns it)"""
    p = P(2)
    cx = cy = 512
    pts = [(cx, 96), (cx + 18, 150), (cx + 14, 470), (cx - 14, 470), (cx - 18, 150)]
    p.part(poly(pts), z=0.40, lift=0.10, bevel=10, mat="steel")
    p.part(poly([(cx, 80), (cx + 22, 150), (cx - 22, 150)]), z=0.44, lift=0.08, bevel=8, mat="gilt")
    p.part(poly([(cx - 40, 520), (cx + 40, 520), (cx + 22, 600), (cx - 22, 600)]), z=0.40, lift=0.08, bevel=10, mat="steel")
    p.part(circle(cx, cy, 62), z=0.46, lift=0.12, bevel=22, mat="brass")
    p.part(circle(cx, cy, 22), z=0.58, lift=0.06, bevel=10, mat="gilt")
    return export(p, "TrainNeedle", 512)


def rings():
    out = []
    r, th = R_(), TH_()
    # TrainRing: a gilt band (with a candle halo added in stage 3)
    p = P(3)
    p.part(ring(512, 512, RING_R, 38), z=0.2, lift=0.18, bevel=15, mat="gilt")
    p.groove(ring(512, 512, RING_R, 3), 0.03)
    out.append(export(p, "TrainRing", 512, "ring", {"halo": [255, 214, 130]}))
    # TrainRingHeavy: a thick brass band wrapped in crimson leather (the HOLD rep)
    p = P(4)
    p.part(ring(512, 512, RING_R - 6, 64), z=0.2, lift=0.20, bevel=20, mat="brass")
    wrap = ring(512, 512, RING_R - 6, 40) * (np.cos(th * 18) > -0.2)
    p.part(wrap, z=0.30, lift=0.10, bevel=8, mat="leather")
    out.append(export(p, "TrainRingHeavy", 512, "ring", {"halo": [230, 70, 70]}))
    # TrainRingFake: black iron cracked into seven shards
    p = P(5)
    band = ring(512, 512, RING_R, 38)
    n = 7
    seg_i = np.floor((th + math.pi) / (2 * math.pi) * n)
    frac = (th + math.pi) / (2 * math.pi) * n - seg_i
    jag = (A.blur_noise(3, 9) - 0.5) * 0.16
    gap = np.clip((np.minimum(frac + jag, 1 - frac + jag) - 0.06) * 60, 0, 1)
    p.part(band * gap, z=0.2, lift=0.14, bevel=12, mat="iron")
    p.groove(ring(512, 512, RING_R + 4, 3) * (A.blur_noise(5, 13) > 0.62), 0.06)
    out.append(export(p, "TrainRingFake", 512, "ring"))
    return out


# ================================================================ rep marks
def rate_good():
    p = P(10)
    m = rough_edge(U(seg(300, 540, 450, 700, 92), seg(450, 700, 760, 300, 92)), p, 0.5, 2.0)
    p.part(m, z=0.2, lift=0.08, bevel=10, mat="chalk", tex=0.03)
    return export(p, "TrainRateGood", 512)


def rate_great():
    p = P(11)
    cx = cy = 512
    p.part(poly([(cx, cy - 330), (cx + 250, cy), (cx, cy + 330), (cx - 250, cy)]), z=0.2, lift=0.24, bevel=60, mat="brass")
    p.recess(poly([(cx, cy - 180), (cx + 136, cy), (cx, cy + 180), (cx - 136, cy)]), 0.08, 10)
    p.emboss(poly([(cx, cy - 120), (cx + 90, cy), (cx, cy + 120), (cx - 90, cy)]), 0.14, 30, mat="gilt")
    return export(p, "TrainRateGreat", 512)


def rate_perfect():
    p = P(12)
    cx = cy = 512
    p.part(ring(cx, cy, 400, 46), z=0.18, lift=0.14, bevel=14, mat="brass")
    for k in range(24):
        a = k * math.pi / 12
        p.emboss(circle(cx + 400 * math.cos(a), cy + 400 * math.sin(a), 9), 0.05, 6, mat="gilt")
    p.part(poly(star_pts(cx, cy, 340, 140)), z=0.22, lift=0.22, bevel=40, mat="gilt")
    for k in range(8):
        a = math.radians(-90 + k * 45)
        p.groove(seg(cx, cy, cx + 320 * math.cos(a), cy + 320 * math.sin(a), 6), 0.035)
    p.part(circle(cx, cy, 70), z=0.42, lift=0.08, bevel=20, mat="crimson_enamel")
    p.emboss(circle(cx, cy, 30), 0.04, 12, mat="gilt")
    return export(p, "TrainRatePerfect", 512)


def rate_miss():
    p = P(13)
    m = rough_edge(U(seg(320, 320, 704, 704, 84), seg(704, 320, 320, 704, 84)), p, 0.55, 2.5)
    p.part(m, z=0.2, lift=0.07, bevel=10, mat="iron", tex=0.02)
    p.groove(U(seg(330, 330, 690, 690, 10), seg(690, 334, 334, 690, 10)), 0.05)
    return export(p, "TrainRateMiss", 512)


# ================================================================ area crests
def crest(seed):
    p = P(seed)
    p.part(poly(shield_pts(512, 512, 760, 900)), z=0.16, lift=0.14, bevel=30, mat="brass")
    inner = poly(shield_pts(512, 520, 640, 770))
    p.custom(inner, 0.24 + 0.012 * p.noise(10), "leather_black", 0.6)
    for k in range(12):   # stitching round the field
        pass
    return p


def icon_arms():
    p = crest(20)
    pts = [(240, 720)]
    pts += bez((240, 720), (400, 740), (560, 745), (650, 712))
    pts += bez((650, 712), (722, 690), (735, 610), (718, 528))
    pts += bez((718, 528), (706, 460), (704, 410), (714, 372))
    pts += bez((714, 372), (742, 340), (744, 262), (706, 226))
    pts += bez((706, 226), (650, 200), (596, 210), (578, 252))
    pts += bez((578, 252), (572, 300), (580, 340), (588, 372))
    pts += bez((588, 372), (574, 430), (566, 490), (560, 548))
    pts += bez((560, 548), (528, 470), (420, 444), (344, 486))
    pts += bez((344, 486), (290, 512), (246, 566), (240, 620))
    p.part(poly(pts), z=0.30, lift=0.22, bevel=40, mat="ivory")
    p.groove(M(np.abs(A.sd_ellipse(445, 600, 150, 92, -6)) - 4) * (yy > 600) * (xx > 330) * (xx < 575), 0.05)
    wrap = U(box(648, 410, 130, 44, 8, 1))
    p.part(wrap * poly(pts), z=0.48, lift=0.05, bevel=6, mat="leather")
    p.groove(U(seg(612, 226, 612, 300, 8), seg(652, 218, 652, 300, 8), seg(692, 226, 692, 300, 8)), 0.05)
    p.groove(seg(566, 560, 640, 690, 8), 0.05)
    return export(p, "TrainIconArms", 512)


def icon_torso():
    p = crest(21)
    cx = 512
    t = poly([(cx - 230, 250), (cx + 230, 250), (cx + 250, 300), (cx + 180, 700), (cx - 180, 700), (cx - 250, 300)])
    t = np.clip(ndimage.gaussian_filter(t, 6) * 1.6 - 0.3, 0, 1)
    p.part(t, z=0.30, lift=0.18, bevel=40, mat="ivory")
    for s in (-1, 1):
        p.emboss(ellipse(cx + s * 105, 365, 118, 70, s * 8), 0.07, 30)
        p.groove(seg(cx + s * 20, 300, cx + s * 210, 290, 9), 0.04)
    p.groove(seg(cx, 300, cx, 680, 10), 0.06)
    for k, y in enumerate((470, 545, 620)):
        p.groove(seg(cx - 110 + k * 8, y, cx + 110 - k * 8, y, 9), 0.05)
    for s in (-1, 1):
        p.groove(seg(cx + s * 135, 440, cx + s * 70, 690, 9), 0.05)
    p.part(box(cx, 720, 380, 60, 10), z=0.34, lift=0.08, bevel=10, mat="leather")
    p.part(box(cx, 720, 70, 52, 6), z=0.40, lift=0.06, bevel=8, mat="brass")
    p.recess(box(cx, 720, 34, 22, 4), 0.06, 4)
    return export(p, "TrainIconTorso", 512)


def icon_legs():
    p = crest(22)
    cx = 512
    p.part(box(cx, 270, 400, 90, 26), z=0.30, lift=0.12, bevel=24, mat="leather")
    for s in (-1, 1):
        x = cx + s * 98
        leg = U(limb(x, 300, x + s * 10, 520, 170, 50), limb(x + s * 10, 520, x + s * 4, 730, 140, 44))
        p.part(leg, z=0.30, lift=0.20, bevel=34, mat="ivory")
        p.emboss(ellipse(x + s * 6, 420, 66, 100, s * 3), 0.06, 30)
        p.emboss(circle(x + s * 8, 540, 34), 0.05, 14)
        p.groove(seg(x - s * 40, 330, x - s * 10, 500, 8), 0.05)
        p.part(box(x + s * 4, 770, 160, 80, 22), z=0.36, lift=0.08, bevel=14, mat="leather_black")
        p.groove(seg(x - 70 + s * 4, 750, x + 70 + s * 4, 750, 7), 0.04)
    return export(p, "TrainIconLegs", 512)


# ================================================================ station medallions
def medallion(seed):
    p = P(seed)
    cx = cy = 512
    p.part(circle(cx, cy, 470), z=0.16, lift=0.16, bevel=34, mat="brass")
    for k in range(36):
        a = k * math.pi / 18
        p.emboss(circle(cx + 440 * math.cos(a), cy + 440 * math.sin(a), 8), 0.05, 6, mat="brass_old")
    face = circle(cx, cy, 405)
    p.custom(face, 0.25 + 0.006 * p.noise(12), "ink", 0.18)
    p.groove(ring(cx, cy, 392, 6), 0.03)
    return p


def figure(p, parts):
    p.part(U(*parts), z=0.32, lift=0.18, bevel=22, mat="ivory")


def head(cx, cy, s=96):
    return box(cx, cy, s, s, s * 0.3)


def st_pushup():
    p = medallion(30)
    p.part(box(512, 700, 640, 34, 8), z=0.28, lift=0.06, bevel=8, mat="leather")
    figure(p, [limb(345, 545, 575, 585, 104, 20), limb(570, 590, 800, 655, 92, 18), limb(370, 545, 375, 680, 80, 16), head(282, 515, 100)])
    p.groove(seg(560, 568, 580, 610, 7), 0.04)
    p.paint(box(270, 508, 14, 14, 4), "ink")
    return export(p, "TrainStationPushUp", 512)


def st_pullup():
    p = medallion(31)
    p.part(box(512, 250, 560, 30, 12), z=0.36, lift=0.08, bevel=10, mat="iron")
    for x in (232, 792):
        p.part(box(x, 250, 40, 54, 10), z=0.4, lift=0.06, bevel=8, mat="brass")
    figure(p, [limb(452, 262, 470, 420, 76, 16), limb(572, 262, 554, 420, 76, 16), box(512, 500, 150, 200, 20),
               head(512, 345, 104), limb(476, 600, 470, 760, 72, 16), limb(548, 600, 570, 740, 72, 16)])
    p.paint(U(box(490, 340, 12, 12, 3), box(534, 340, 12, 12, 3)), "ink")
    p.groove(seg(512, 405, 512, 598, 7), 0.035)
    return export(p, "TrainStationPullUp", 512)


def st_situp():
    p = medallion(32)
    p.part(box(512, 700, 640, 34, 8), z=0.28, lift=0.06, bevel=8, mat="leather")
    figure(p, [limb(470, 640, 560, 470, 104, 20), limb(480, 650, 650, 540, 90, 18), limb(650, 540, 720, 670, 84, 16),
               head(590, 400, 100), limb(560, 460, 520, 380, 76, 16)])
    p.paint(box(612, 392, 14, 14, 4), "ink")
    return export(p, "TrainStationSitUp", 512)


def st_squat():
    p = medallion(33)
    p.part(box(512, 735, 560, 30, 8), z=0.28, lift=0.06, bevel=8, mat="oak")
    figure(p, [limb(470, 555, 520, 365, 112, 22), limb(460, 575, 610, 560, 96, 18), limb(610, 560, 600, 715, 86, 16),
               head(540, 290, 104), limb(520, 400, 700, 410, 76, 16)])
    p.paint(box(564, 284, 14, 14, 4), "ink")
    return export(p, "TrainStationSquat", 512)


# ================================================================ badges
def badge_streak():
    p = P(40)
    cx = 512
    for k in range(7):
        x, y = cx + (k - 3) * 96, 900
        p.part(poly([(x, y - 30), (x + 24, y), (x, y + 30), (x - 24, y)]), z=0.22, lift=0.1, bevel=12, mat="gilt")
    cand = box(cx, 590, 190, 380, 24)
    drips = U(*[box(cx + dx, 420 + l / 2, 30, l, 14) for dx, l in ((-70, 90), (-20, 50), (40, 120), (78, 70))])
    p.part(U(cand, drips), z=0.28, lift=0.16, bevel=36, mat="wax")
    p.part(ellipse(cx, 404, 92, 22), z=0.36, lift=0.04, bevel=10, mat="wax")
    p.part(seg(cx, 404, cx, 360, 12), z=0.42, lift=0.02, bevel=4, mat="iron")
    fl = poly(bez((cx, 150), (cx + 90, 250), (cx + 80, 330), (cx, 360)) + bez((cx, 360), (cx - 80, 330), (cx - 90, 250), (cx, 150)))
    p.part(fl, z=0.46, lift=0.14, bevel=40, mat="flame")
    p.part(box(cx, 810, 300, 50, 14), z=0.30, lift=0.06, bevel=10, mat="brass")
    return export(p, "TrainBadgeStreak", 512)


def badge_best():
    p = P(41)
    cx, cy = 512, 520
    for s in (-1, 1):
        for k in range(8):
            t = k / 7
            a = math.radians(110 + t * 150) if s < 0 else math.radians(70 - t * 150)
            x, y = cx + 330 * math.cos(a), cy + 330 * math.sin(a)
            rot = math.degrees(a) + (90 if s < 0 else -90) + s * 30
            p.part(ellipse(x, y, 34, 74, rot), z=0.22, lift=0.12, bevel=22, mat="gilt")
            p.groove(seg(*_leaf_axis(x, y, rot)), 0.03)
        p.part(M(np.abs(sd_circle(cx, cy, 300)) - 9) * ((xx - cx) * s > 40) * (yy > cy - 260), z=0.2, lift=0.05, bevel=6, mat="brass")
    p.part(poly(star_pts(cx, cy, 220, 92, 5)), z=0.30, lift=0.22, bevel=40, mat="gilt")
    p.part(box(cx, 890, 240, 60, 20), z=0.26, lift=0.08, bevel=14, mat="leather")
    for s in (-1, 1):
        p.part(poly([(cx + s * 60, 900), (cx + s * 150, 1000), (cx + s * 110, 900)]), z=0.24, lift=0.05, bevel=8, mat="leather")
    return export(p, "TrainBadgeBest", 512)


def _leaf_axis(x, y, rot):
    a = math.radians(rot + 90)
    return x - 55 * math.cos(a), y - 55 * math.sin(a), x + 55 * math.cos(a), y + 55 * math.sin(a), 5


def badge_daily():
    p = P(42)
    cx = 512
    for y in (190, 834):
        p.part(box(cx, y, 520, 64, 22), z=0.30, lift=0.10, bevel=16, mat="oak")
    for x in (300, 724):
        p.part(box(x, 512, 36, 600, 14), z=0.34, lift=0.08, bevel=12, mat="brass")
    glass = poly(bez((370, 230), (370, 420), (500, 470), (500, 512)) + bez((500, 512), (500, 560), (370, 600), (370, 794))
                 + [(654, 794)] + bez((654, 794), (654, 600), (524, 560), (524, 512)) + bez((524, 512), (524, 470), (654, 420), (654, 230)))
    p.part(glass, z=0.24, lift=0.10, bevel=40, mat="glass")
    p.emboss(U(poly([(410, 360), (614, 360), (522, 500), (502, 500)]), poly([(400, 790), (624, 790), (560, 700), (464, 700)]),
               seg(512, 500, 512, 700, 8)), 0.05, 20, mat="sand")
    return export(p, "TrainBadgeDaily", 512)


def icon_sore():
    p = P(43)
    cx = cy = 512
    p.part(circle(cx, cy, 300), z=0.2, lift=0.18, bevel=40, mat="wax_red")
    pts = [(cx - 40, cy - 300), (cx + 30, cy - 140), (cx - 50, cy - 40), (cx + 60, cy + 70), (cx - 10, cy + 170), (cx + 40, cy + 300)]
    cr = U(*[seg(*pts[i], *pts[i + 1], 30) for i in range(len(pts) - 1)])
    p.recess(cr * circle(cx, cy, 300), 0.16, 8, mat="ink")
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        p.part(seg(cx + 350 * math.cos(a), cy + 350 * math.sin(a), cx + 430 * math.cos(a), cy + 430 * math.sin(a), 30),
               z=0.2, lift=0.08, bevel=10, mat="wax_red")
    return export(p, "TrainIconSore", 512)


# ================================================================ animated parts
def gear():
    """the HOLD grind gear: a brass cog with six spokes (the HUD spins it while you grind)"""
    p = P(50)
    r, th = R_(), TH_()
    teeth = 16
    rr = 430 + 40 * np.clip(np.cos(th * teeth) * 2.2, -1, 1)
    cog = np.clip(rr - r + 0.5, 0, 1) * np.clip(r - 90 + 0.5, 0, 1)
    holes = np.zeros_like(r)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        holes = np.maximum(holes, ellipse(512 + 250 * math.cos(a), 512 + 250 * math.sin(a), 92, 64, math.degrees(a)))
    p.part(sub(cog, holes), z=0.2, lift=0.18, bevel=20, mat="brass")
    p.groove(ring(512, 512, 360, 5), 0.04)
    p.part(circle(512, 512, 120), z=0.36, lift=0.10, bevel=24, mat="brass_old")
    p.recess(circle(512, 512, 44), 0.12, 10, mat="iron")
    return export(p, "TrainGear", 256)


def plate():
    """the set plate: a 9-slice brass frame round an ink-enamel field (768 x 192; SliceCenter 64, 64, 704, 128)"""
    W, Hh = 1536, 384
    p = P(60, W, Hh)
    yy2, xx2 = np.mgrid[0:Hh, 0:W].astype(f32)

    def rbox(x0, y0, x1, y1, r):
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
        qx, qy = np.abs(xx2 - cx) - (w / 2 - r), np.abs(yy2 - cy) - (h / 2 - r)
        sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        return np.clip(0.5 - sd, 0, 1).astype(f32)
    outer, inner = rbox(6, 6, W - 6, Hh - 6, 44), rbox(52, 52, W - 52, Hh - 52, 18)
    frame = outer * (1 - inner)
    d = ndimage.distance_transform_edt(frame > 0.5).astype(f32)
    p.custom(frame, 0.30 + 0.16 * H.dome(d, 16) + 0.006 * p.noise(3), "brass")
    p.h -= 0.04 * np.clip(1 - np.abs(d - 23) / 2.0, 0, 1) * frame   # an engraved line round the frame
    p.custom(inner, 0.20 + 0.004 * p.noise(8) - 0.04 * np.clip(1 - ndimage.distance_transform_edt(inner > 0.5) / 14, 0, 1), "ink", 0.15)
    for x, y in ((30, 30), (W - 30, 30), (30, Hh - 30), (W - 30, Hh - 30)):
        dd = np.hypot(xx2 - x, yy2 - y)
        p.custom(np.clip(15.5 - dd, 0, 1), 0.46 + 0.1 * np.sqrt(np.clip(1 - dd / 15, 0, 1)), "brass_old")
    p.a = outer
    return export(p, "TrainPlate", [768, 192], "plate")


def keycap():
    """the input prompt's key cap: a 9-slice brass-rimmed black-iron cap (256 x 128; SliceCenter 40, 40, 216, 88)"""
    W, Hh = 512, 256
    p = P(61, W, Hh)
    yy2, xx2 = np.mgrid[0:Hh, 0:W].astype(f32)

    def rbox(x0, y0, x1, y1, r):
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
        qx, qy = np.abs(xx2 - cx) - (w / 2 - r), np.abs(yy2 - cy) - (h / 2 - r)
        sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        return np.clip(0.5 - sd, 0, 1).astype(f32)
    outer, inner = rbox(6, 6, W - 6, Hh - 6, 40), rbox(30, 30, W - 30, Hh - 34, 26)
    d = ndimage.distance_transform_edt(outer > 0.5).astype(f32)
    p.custom(outer, 0.26 + 0.12 * H.dome(d, 14), "brass")
    di = ndimage.distance_transform_edt(inner > 0.5).astype(f32)
    p.custom(inner, 0.34 + 0.10 * H.dome(di, 30) + 0.004 * p.noise(4), "iron", 0.4)
    p.a = outer
    return export(p, "TrainKey", [256, 128], "plate")


def bar_frame():
    """the next-change bar: a black-iron channel with brass end caps (1200 x 72, window x 36..1164, y 22..50)"""
    W, Hh = 2400, 144
    p = P(62, W, Hh)
    yy2, xx2 = np.mgrid[0:Hh, 0:W].astype(f32)

    def rbox(x0, y0, x1, y1, r):
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
        qx, qy = np.abs(xx2 - cx) - (w / 2 - r), np.abs(yy2 - cy) - (h / 2 - r)
        sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
        return np.clip(0.5 - sd, 0, 1).astype(f32)
    band = rbox(40, 26, W - 40, Hh - 26, 30)
    win = rbox(72, 44, W - 72, Hh - 44, 14)
    d = ndimage.distance_transform_edt((band * (1 - win)) > 0.5).astype(f32)
    p.custom(band * (1 - win), 0.30 + 0.12 * H.dome(d, 10) + 0.01 * p.noise(2), "iron", 0.45)
    for x in (56, W - 56):     # brass end caps, diamond knobs
        cap = rbox(x - 50, 8, x + 50, Hh - 8, 22)
        dc = ndimage.distance_transform_edt(cap > 0.5).astype(f32)
        p.custom(cap, 0.40 + 0.14 * H.dome(dc, 18), "brass")
        dia = poly_local(xx2, yy2, [(x, 30), (x + 26, Hh / 2), (x, Hh - 30), (x - 26, Hh / 2)])
        p.part(dia, z=0.56, lift=0.08, bevel=10, mat="gilt")
    for k in range(1, 10):  # brass ticks every tenth
        x = 72 + (W - 144) * k / 10
        t = rbox(x - 3, 30, x + 3, 44, 2) + rbox(x - 3, Hh - 44, x + 3, Hh - 30, 2)
        p.h += 0.04 * t
        p.paint(t, "brass")
    p.a = np.maximum(band, p.a)
    p.a = p.a * 1.0
    # the window stays clear (the fill shows through)
    p.a *= 1 - win
    return export(p, "TrainBarFrame", [1200, 72], "plate")


def poly_local(xx2, yy2, pts):
    from PIL import ImageDraw
    Hh, W = xx2.shape
    m = Image.new("L", (W * 3, Hh * 3), 0)
    ImageDraw.Draw(m).polygon([(x * 3, y * 3) for x, y in pts], fill=255)
    return np.array(m.resize((W, Hh), Image.BOX), f32) / 255.0


PIECES = {
    "TrainGauge": gauge, "TrainNeedle": needle, "rings": rings,
    "TrainRateGood": rate_good, "TrainRateGreat": rate_great, "TrainRatePerfect": rate_perfect, "TrainRateMiss": rate_miss,
    "TrainIconArms": icon_arms, "TrainIconTorso": icon_torso, "TrainIconLegs": icon_legs,
    "TrainStationPushUp": st_pushup, "TrainStationPullUp": st_pullup, "TrainStationSitUp": st_situp, "TrainStationSquat": st_squat,
    "TrainBadgeStreak": badge_streak, "TrainBadgeBest": badge_best, "TrainBadgeDaily": badge_daily, "TrainIconSore": icon_sore,
    "TrainGear": gear, "TrainPlate": plate, "TrainKey": keycap, "TrainBarFrame": bar_frame,
}

if __name__ == "__main__":
    want = sys.argv[1:]
    listing = MAPS / "pieces.json"
    have = {p["name"]: p for p in json.loads(listing.read_text())} if listing.exists() else {}
    for n, fn in PIECES.items():
        if want and n not in want:
            continue
        r = fn()
        for info in (r if isinstance(r, list) else [r]):
            have[info["name"]] = info
    listing.write_text(json.dumps(list(have.values()), indent=1))
    print("pieces:", len(have))
