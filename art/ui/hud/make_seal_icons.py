"""The seal-replacement icon set, stage 1 of 3: every design as relief + material maps for the Blender PBR render.

The kit's wax seal (Theme.Images.Seal) had become the icon for everything. It keeps its own job (the rarity gem on item
slots) and every other use gets its own icon here: notifications, the banners, the NPC quest markers, the arrival stamp,
the get-up dial, the discovery flag, the waypoint, the duel ring, the sports touch buttons, the report-card grade seal,
the allowance coin, the memory-card back, and the Hex Slash / Crypt Crush pieces.

Same pipeline as the training HUD: each design is drawn in 2D as a HEIGHT field with a MATERIAL id per pixel; stage 2
(blender_seal_icons_render.py) builds it as displaced geometry with full PBR shaders and the HUD lights; stage 3
(finish_seal_icons.py) bleeds the colour under the clear pixels, sizes them and writes art/group-upload-icons/.

    python make_seal_icons.py [Name ...]   ->  out/seal_icons/maps/<Name>_h.png (16-bit) _m.png _a.png, pieces.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as H
from make_app_icons import (M, box, circle, ring, seg, ellipse, poly, U, sub, text, smooth, sd_circle, xx, yy, bez,
                            ngon_facets)

HERE = Path(__file__).resolve().parent
MAPS = HERE / "out" / "seal_icons" / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
S = 1024
f32 = np.float32

# material ids (stage 2 has the shaders); 1-17 match the training HUD
MAT = {"none": 0, "brass": 1, "gilt": 2, "iron": 3, "ink": 4, "crimson_enamel": 5, "ivory": 6, "leather": 7,
       "leather_black": 8, "wax": 9, "wax_red": 10, "chalk": 11, "glass": 12, "flame": 13, "oak": 14, "sand": 15,
       "brass_old": 16, "steel": 17, "parchment": 18, "blue_enamel": 19, "green_enamel": 20, "gold_enamel": 21,
       "moon": 22, "moon_dark": 23, "moon_red": 24, "moon_blue": 25, "kraft": 26, "wax_white": 27, "bone": 28,
       "twine": 29, "silver": 30}


class P:
    """a relief: height, material id, alpha"""

    def __init__(self, seed, w=S, h=S):
        self.W, self.Hh = w, h
        self.h = np.zeros((h, w), f32)
        self.m = np.zeros((h, w), f32)
        self.a = np.zeros((h, w), f32)
        self.seed, self.k = seed, 0

    def noise(self, sigma):
        self.k += 1
        r = np.random.default_rng(self.seed * 1000 + self.k)
        n = ndimage.gaussian_filter(r.random((self.Hh, self.W)).astype(f32), sigma, mode="wrap")
        return (n - n.min()) / (n.max() - n.min() + 1e-6)

    def custom(self, mask, h, mat):
        self.h = self.h * (1 - mask) + h * mask
        self.m[mask > 0.5] = MAT[mat]
        self.a = np.maximum(self.a, mask)

    def part(self, mask, z=0.20, lift=0.16, bevel=26, mat="ivory", tex=0.010):
        d = (ndimage.distance_transform_edt(mask > 0.5) + (mask - 0.5) * (mask < 1)).astype(f32)
        h = z + lift * H.dome(d, bevel) + tex * self.noise(2.0) + tex * 1.6 * self.noise(14)
        self.custom(mask, h, mat)

    def flat(self, mask, z, mat, tex=0.004):
        """an inset enamel / face: flat with a soft meniscus at its edge"""
        d = ndimage.distance_transform_edt(mask > 0.5).astype(f32)
        self.custom(mask, z - 0.03 * np.clip(1 - d / 14, 0, 1) + tex * self.noise(8), mat)

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


PIECES = {}


def piece(name, out=512, kind="icon"):
    def deco(fn):
        def run():
            p = fn()
            hh = np.clip(p.h, 0, 1)
            Image.fromarray((hh * 65535).astype(np.uint16)).save(MAPS / f"{name}_h.png")
            Image.fromarray(p.m.astype(np.uint8)).save(MAPS / f"{name}_m.png")
            Image.fromarray((np.clip(p.a, 0, 1) * 255).astype(np.uint8)).save(MAPS / f"{name}_a.png")
            ids = sorted({int(v) for v in np.unique(p.m[p.a > 0.02])} - {0})
            (MAPS / f"{name}_ids.json").write_text(json.dumps(ids))
            print("  maps", name, ids)
            return {"name": name, "w": p.W, "h": p.Hh, "out": out, "kind": kind}
        PIECES[name] = run
        return run
    return deco


# ================================================================ shared shapes
C0 = 512


def arrow(x0, y0, x1, y1, w, head=2.6, hl=None):
    """a shaft from (x0, y0) to (x1, y1) with a triangular head at the end"""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    hl = hl or w * 2.2
    bx, by = x1 - ux * hl, y1 - uy * hl
    hw = w * head / 2
    tri = poly([(x1 + ux * 4, y1 + uy * 4), (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw)])
    return U(seg(x0, y0, bx + ux * 6, by + uy * 6, w), tri)


def polyline(pts, w):
    return U(*[seg(*pts[i], *pts[i + 1], w) for i in range(len(pts) - 1)])


def arrow_path(pts, w, head=2.6):
    return U(polyline(pts[:-1], w), arrow(*pts[-2], *pts[-1], w, head))


def check(cx, cy, s, w):
    return U(seg(cx - 0.55 * s, cy + 0.02 * s, cx - 0.15 * s, cy + 0.42 * s, w),
             seg(cx - 0.15 * s, cy + 0.42 * s, cx + 0.62 * s, cy - 0.45 * s, w))


def cross(cx, cy, s, w):
    return U(seg(cx - s, cy - s, cx + s, cy + s, w), seg(cx - s, cy + s, cx + s, cy - s, w))


def bang(cx, cy, s):
    """an exclamation mark: a tapered bar over a dot"""
    bar = poly([(cx - 0.20 * s, cy - 0.95 * s), (cx + 0.20 * s, cy - 0.95 * s), (cx + 0.10 * s, cy + 0.38 * s), (cx - 0.10 * s, cy + 0.38 * s)])
    bar = U(bar, circle(cx, cy - 0.95 * s + 0.0, 0.20 * s))
    return U(bar, circle(cx, cy + 0.78 * s, 0.17 * s))


def star(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n)
        rr = R if k % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return poly(pts)


def ngon(cx, cy, R, n, rot=-90):
    return poly([(cx + R * math.cos(math.radians(rot + k * 360 / n)), cy + R * math.sin(math.radians(rot + k * 360 / n))) for k in range(n)])


def shield_pts(cx, cy, w, h):
    top = cy - h * 0.5
    pts = [(cx - w / 2, top + 40), (cx - w / 2 + 40, top), (cx + w / 2 - 40, top), (cx + w / 2, top + 40)]
    pts += bez((cx + w / 2, top + 40), (cx + w / 2, top + h * 0.62), (cx + w * 0.22, top + h * 0.86), (cx, top + h))
    pts += bez((cx, top + h), (cx - w * 0.22, top + h * 0.86), (cx - w / 2, top + h * 0.62), (cx - w / 2, top + 40))
    return pts


def inset_pts(pts, cx, cy, k):
    return [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]


def rivets(p, cx, cy, r, n, size=12, mat="brass_old", z=0.34, phase=0.0):
    for k in range(n):
        a = phase + k * 2 * math.pi / n
        p.part(circle(cx + r * math.cos(a), cy + r * math.sin(a), size), z=z, lift=0.06, bevel=size, mat=mat, tex=0.002)


def medal(p, r=470, rim="brass", face="ink", rimw=58, face_z=0.24):
    """a round plaque: a domed metal rim round a flat enamel face"""
    p.part(circle(C0, C0, r), z=0.14, lift=0.18, bevel=34, mat=rim)
    p.groove(ring(C0, C0, r - 16, 4), 0.025)
    p.flat(circle(C0, C0, r - rimw), face_z, face)
    p.groove(ring(C0, C0, r - rimw - 12, 4), 0.02)


# ================================================================ notifications (the toast's icon, by kind)
@piece("NoteInfo", 256)
def note_info():
    p = P(101)
    medal(p, 470, "brass", "blue_enamel")
    p.part(circle(C0, 300, 66), z=0.30, lift=0.14, bevel=40, mat="ivory")
    stem = U(box(C0, 600, 124, 330, 26), box(476, 448, 150, 56, 18), box(C0, 768, 250, 60, 18))
    p.part(stem, z=0.30, lift=0.14, bevel=30, mat="ivory")
    return p


@piece("NoteGood", 256)
def note_good():
    p = P(102)
    sh = shield_pts(C0, 520, 800, 920)
    p.part(poly(sh), z=0.14, lift=0.18, bevel=34, mat="brass")
    p.flat(poly(inset_pts(sh, C0, 520, 0.86)), 0.24, "green_enamel")
    p.part(check(C0 + 10, 470, 330, 110), z=0.30, lift=0.16, bevel=34, mat="ivory")
    return p


@piece("NoteWarning", 256)
def note_warning():
    p = P(103)
    cy = 560
    tri = [(C0, cy - 470), (C0 + 480, cy + 360), (C0 - 480, cy + 360)]
    outer = ndimage.gaussian_filter(poly(tri), 14)
    outer = np.clip((outer - 0.5) * 6 + 0.5, 0, 1).astype(f32)        # softened corners
    p.part(outer, z=0.14, lift=0.18, bevel=34, mat="gilt")
    inner = poly(inset_pts(tri, C0, cy + 80, 0.74))
    inner = np.clip((ndimage.gaussian_filter(inner, 8) - 0.5) * 6 + 0.5, 0, 1).astype(f32)
    p.flat(inner, 0.24, "ink")
    p.part(bang(C0, cy + 40, 230), z=0.30, lift=0.16, bevel=30, mat="gilt")
    return p


@piece("NoteBad", 256)
def note_bad():
    p = P(104)
    p.part(ngon(C0, C0, 490, 8, -90 + 22.5), z=0.14, lift=0.18, bevel=34, mat="iron")
    p.flat(ngon(C0, C0, 410, 8, -90 + 22.5), 0.24, "crimson_enamel")
    p.part(cross(C0, C0, 190, 112), z=0.30, lift=0.16, bevel=34, mat="ivory")
    return p


@piece("NoteMilestone", 256)
def note_milestone():
    p = P(105)
    cy = 430
    for s in (-1, 1):   # two ribbon tails, notched
        x = C0 + s * 120
        tail = poly([(x - 90, cy + 180), (x + 90, cy + 180), (x + 70 + s * 60, 960), (x + s * 60, 890), (x - 70 + s * 60, 960)])
        p.part(tail, z=0.12, lift=0.08, bevel=16, mat="leather")
    r, th = np.hypot(xx - C0, yy - cy), np.arctan2(yy - cy, xx - C0)
    pleat = np.clip(400 + 26 * np.cos(th * 28) - r + 0.5, 0, 1).astype(f32)    # the pleated rosette
    p.part(pleat, z=0.16, lift=0.10, bevel=30, mat="leather")
    p.h += 0.03 * (0.5 + 0.5 * np.cos(th * 28)) * pleat
    p.part(circle(C0, cy, 290), z=0.26, lift=0.14, bevel=30, mat="gilt")
    p.groove(ring(C0, cy, 262, 5), 0.03)
    p.part(star(C0, cy + 6, 210, 86, 5), z=0.40, lift=0.12, bevel=30, mat="gilt")
    return p


# ================================================================ banners
def laurel(p, cx, cy, R, n=8, mat="gilt", a0=110, span=150, size=(34, 74)):
    for s in (-1, 1):
        for k in range(n):
            t = k / (n - 1)
            a = math.radians(a0 + t * span) if s < 0 else math.radians(180 - a0 - t * span)
            x, y = cx + R * math.cos(a), cy + R * math.sin(a)
            rot = math.degrees(a) + (90 if s < 0 else -90) + s * 32
            p.part(ellipse(x, y, size[0], size[1], rot), z=0.22, lift=0.12, bevel=22, mat=mat)
            ra = math.radians(rot + 90)
            p.groove(seg(x - 50 * math.cos(ra), y - 50 * math.sin(ra), x + 50 * math.cos(ra), y + 50 * math.sin(ra), 5), 0.03)
        stem = M(np.abs(sd_circle(cx, cy, R - 30)) - 8) * ((xx - cx) * s > 60) * (yy > cy - R * 0.85)
        p.part(stem, z=0.18, lift=0.05, bevel=6, mat="brass")


@piece("BannerLevelUp")
def banner_levelup():
    p = P(201)
    cy = 560
    laurel(p, C0, cy, 360, 8, a0=100, span=160)
    p.part(circle(C0, cy, 250), z=0.18, lift=0.16, bevel=28, mat="brass")
    p.flat(circle(C0, cy, 205), 0.26, "ivory")
    p.groove(ring(C0, cy, 190, 4), 0.02)
    chev = poly([(C0, 70), (C0 + 170, 220), (C0 + 110, 220), (C0, 140), (C0 - 110, 220), (C0 - 170, 220)])
    p.part(chev, z=0.26, lift=0.14, bevel=24, mat="gilt")
    chev2 = poly([(C0, 175), (C0 + 120, 280), (C0 + 70, 280), (C0, 228), (C0 - 70, 280), (C0 - 120, 280)])
    p.part(chev2, z=0.24, lift=0.12, bevel=20, mat="gilt")
    return p


@piece("BannerPurchase")
def banner_purchase():
    p = P(202)
    bx, by, bw, bh = 470, 590, 600, 520
    p.part(box(bx, by, bw, bh, 26), z=0.16, lift=0.12, bevel=40, mat="kraft")
    p.part(box(bx, by - bh / 2 + 50, bw + 30, 100, 20), z=0.24, lift=0.10, bevel=24, mat="kraft")   # the lid
    p.groove(seg(bx - bw / 2 - 10, by - bh / 2 + 100, bx + bw / 2 + 10, by - bh / 2 + 100, 6), 0.04)
    rib = U(box(bx, by, 90, bh + 10, 10), box(bx, by + 10, bw + 34, 80, 10))
    p.part(rib, z=0.30, lift=0.08, bevel=14, mat="crimson_enamel")
    for s in (-1, 1):   # the bow
        loop = sub(ellipse(bx + s * 120, by - bh / 2 - 40, 130, 80, s * 18), ellipse(bx + s * 120, by - bh / 2 - 40, 60, 28, s * 18))
        p.part(loop, z=0.36, lift=0.12, bevel=26, mat="crimson_enamel")
        p.part(poly([(bx, by - bh / 2 - 20), (bx + s * 70, by - bh / 2 + 120), (bx + s * 130, by - bh / 2 + 100)]), z=0.34, lift=0.06, bevel=12, mat="crimson_enamel")
    p.part(circle(bx, by - bh / 2 - 36, 48), z=0.42, lift=0.10, bevel=20, mat="crimson_enamel")
    # a gold coin tag on a twine loop, lower right
    p.part(seg(bx + 60, by - bh / 2 - 20, 820, 760, 12), z=0.40, lift=0.03, bevel=5, mat="twine")
    p.part(circle(820, 800, 150), z=0.40, lift=0.16, bevel=26, mat="gilt")
    p.groove(ring(820, 800, 128, 5), 0.04)
    p.emboss(text("¥", 200, 820, 808), 0.10, 10, mat="gilt")
    return p


@piece("BannerEvolved")
def banner_evolved():
    p = P(203)
    cy = 520
    for s in (-1, 1):
        for k in range(6):          # six feathers a side, fanned up and out
            a = math.radians(-70 + k * 20)
            L = 360 - k * 30
            x0, y0 = C0 + s * 110, cy + 40
            x1, y1 = x0 + s * L * math.cos(a), y0 + L * math.sin(a)
            rot = math.degrees(math.atan2(y1 - y0, (x1 - x0)))
            f = ellipse((x0 + x1) / 2, (y0 + y1) / 2, L / 2 + 30, 58 - k * 3, rot)
            p.part(f, z=0.16 + k * 0.01, lift=0.12, bevel=30, mat="bone")
            p.groove(seg(x0 + (x1 - x0) * 0.1, y0 + (y1 - y0) * 0.1, x1 - (x1 - x0) * 0.1, y1 - (y1 - y0) * 0.1, 6), 0.03)
    p.part(circle(C0, cy, 175), z=0.26, lift=0.14, bevel=24, mat="brass")
    rivets(p, C0, cy, 150, 12, 10, z=0.38)
    fac = ngon_facets(C0, cy, 130, 8, math.pi / 8)
    gem = np.clip(fac + 0.5, 0, 1).astype(f32)
    p.custom(gem, 0.40 + 0.0016 * np.clip(fac, 0, 90) + 0.12 * np.clip((np.clip(fac, 0, 90) - 55) / 35, 0, 1), "crimson_enamel")
    for s in (-1, 0, 1):            # a small crown of three points above
        x = C0 + s * 70
        hgt = 120 if s == 0 else 80
        p.part(poly([(x - 34, 340), (x + 34, 340), (x, 340 - hgt)]), z=0.24, lift=0.10, bevel=14, mat="gilt")
    p.part(box(C0, 345, 220, 30, 10), z=0.26, lift=0.06, bevel=10, mat="gilt")
    return p


def scroll(p, torn=False):
    sheet = box(C0, 525, 560, 600, 10)
    if torn:   # a ragged tear across the middle
        pts = [(180, 470)] + [(220 + k * 64, 470 + (40 if k % 2 else -40)) for k in range(10)] + [(860, 470)]
        gap = U(polyline(pts, 34))
        sheet = sub(sheet, gap)
    p.part(sheet, z=0.16, lift=0.06, bevel=30, mat="parchment")
    for y in (215, 835):
        p.part(box(C0, y, 650, 104, 52), z=0.20, lift=0.18, bevel=52, mat="parchment")
        p.groove(seg(200, y + 30, 824, y + 30, 5), 0.03)
        for x in (172, 852):
            p.part(circle(x, y, 46), z=0.30, lift=0.12, bevel=24, mat="brass")
    for k, y in enumerate(range(330, 740, 58)):
        L = 400 - (k % 3) * 70
        g = seg(C0 - 210, y, C0 - 210 + L, y, 10)
        p.groove(g * (1 - (torn and abs(y - 470) < 50)), 0.012)
        p.paint(g * (1 - (torn and abs(y - 470) < 50)), "ink")


@piece("BannerQuestNew")
def banner_quest_new():
    p = P(204)
    scroll(p)
    p.part(bang(C0, 520, 240), z=0.30, lift=0.16, bevel=30, mat="wax_red")
    return p


@piece("BannerQuestStep")
def banner_quest_step():
    p = P(205)
    scroll(p)
    for dx in (-90, 90):
        ch = poly([(C0 + dx - 120, 330), (C0 + dx - 40, 330), (C0 + dx + 140, 525), (C0 + dx - 40, 720), (C0 + dx - 120, 720), (C0 + dx + 60, 525)])
        p.part(ch, z=0.30, lift=0.14, bevel=24, mat="gilt")
    return p


@piece("BannerQuestDone")
def banner_quest_done():
    p = P(206)
    scroll(p)
    p.part(check(C0 + 20, 500, 300, 100), z=0.30, lift=0.16, bevel=30, mat="gilt")
    return p


@piece("BannerQuestFailed")
def banner_quest_failed():
    p = P(207)
    scroll(p, torn=True)
    p.part(cross(C0, 525, 170, 96), z=0.30, lift=0.16, bevel=30, mat="wax_red")
    return p


def moon(p, cx, cy, r, mat, craters=True, seed=0):
    p.part(circle(cx, cy, r), z=0.16, lift=0.20, bevel=int(r * 0.5), mat=mat)
    if craters:
        rng = np.random.default_rng(seed)
        for _ in range(8):
            a, d = rng.random() * 6.283, math.sqrt(rng.random()) * r * 0.72
            cr = 22 + rng.random() * 44
            x, y = cx + d * math.cos(a), cy + d * math.sin(a)
            bowl = np.clip(1 - np.hypot(xx - x, yy - y) / cr, 0, 1)            # a soft basin, no hard rim
            p.h -= 0.035 * smooth(0.0, 1.0, bowl) * circle(cx, cy, r)
            p.h += 0.008 * np.clip(1 - np.abs(np.hypot(xx - x, yy - y) - cr * 1.05) / (cr * 0.25), 0, 1) * circle(cx, cy, r)
        mare = ndimage.gaussian_filter(np.random.default_rng(seed + 9).random((S, S)).astype(f32), 40)
        mare = (mare - mare.min()) / (mare.max() - mare.min())
        p.h -= 0.02 * np.clip((mare - 0.55) * 4, 0, 1) * circle(cx, cy, r)


def twinkle(p, cx, cy, s, mat="gilt"):
    p.part(poly([(cx, cy - s), (cx + s * 0.22, cy - s * 0.22), (cx + s, cy), (cx + s * 0.22, cy + s * 0.22), (cx, cy + s),
                 (cx - s * 0.22, cy + s * 0.22), (cx - s, cy), (cx - s * 0.22, cy - s * 0.22)]), z=0.24, lift=0.10, bevel=int(s * 0.3), mat=mat)


@piece("BannerFullMoon")
def banner_full_moon():
    p = P(208)
    moon(p, 540, 470, 380, "moon", seed=3)
    # a bare branch across the lower left
    br = U(polyline([(40, 900), (220, 780), (380, 720), (520, 700)], 34), polyline([(220, 780), (300, 640), (330, 560)], 20),
           polyline([(380, 720), (470, 610)], 14), polyline([(300, 640), (240, 580)], 12), polyline([(140, 840), (120, 740)], 16))
    p.part(br, z=0.42, lift=0.10, bevel=12, mat="iron")
    return p


@piece("BannerNewMoon")
def banner_new_moon():
    p = P(209)
    moon(p, C0, C0, 380, "moon_dark", craters=False)
    cres = sub(circle(C0, C0, 380), circle(C0 + 70, C0 - 30, 372))
    p.emboss(cres, 0.04, 10, mat="moon")
    for x, y, s in ((170, 200, 60), (860, 260, 44), (820, 840, 70), (230, 820, 38)):
        twinkle(p, x, y, s, "gilt")
    return p


@piece("BannerCrimsonMoon")
def banner_crimson_moon():
    p = P(210)
    moon(p, C0, 480, 380, "moon_red", seed=5)
    for y, x0, x1, w in ((700, 120, 760, 46), (780, 300, 930, 40), (620, 560, 940, 30)):
        p.part(seg(x0, y, x1, y, w), z=0.44, lift=0.08, bevel=20, mat="iron")
    return p


@piece("BannerBlueMoon")
def banner_blue_moon():
    p = P(211)
    moon(p, C0, C0, 360, "moon_blue", seed=7)
    for x, y, s in ((150, 180, 52), (880, 230, 40), (860, 860, 60), (160, 850, 44)):
        twinkle(p, x, y, s, "steel")
    return p


@piece("BannerRecord")
def banner_record():
    p = P(212)
    bx, by, bw, bh = 490, 520, 600, 780
    p.part(box(bx + 34, by + 26, bw, bh, 20), z=0.12, lift=0.06, bevel=14, mat="ivory")       # the page block
    for k in range(6):
        p.groove(seg(bx + bw / 2 + 20, by - bh / 2 + 80 + k * 4, bx + bw / 2 + 20, by + bh / 2 - 40, 2), 0.004)
    p.part(box(bx, by, bw, bh, 24), z=0.20, lift=0.10, bevel=30, mat="leather")
    p.part(box(bx - bw / 2 + 40, by, 80, bh, 20), z=0.26, lift=0.08, bevel=20, mat="leather")  # the spine band
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = bx + sx * (bw / 2 - 50), by + sy * (bh / 2 - 50)
            corner = poly([(x + sx * 56, y + sy * 56), (x - sx * 70, y + sy * 56), (x + sx * 56, y - sy * 70)])
            p.part(corner, z=0.30, lift=0.06, bevel=10, mat="brass")
    p.part(box(bx + bw / 2 + 10, by, 120, 110, 18), z=0.34, lift=0.08, bevel=14, mat="brass")    # the clasp
    p.part(circle(bx + bw / 2 + 10, by, 26), z=0.42, lift=0.06, bevel=10, mat="brass_old")
    p.groove(box(bx + 20, by, bw - 170, bh - 170, 12) - box(bx + 20, by, bw - 190, bh - 190, 10), 0.03)
    p.part(arrow(bx + 20, by + 210, bx + 20, by - 230, 90, 2.8), z=0.30, lift=0.12, bevel=24, mat="gilt")
    return p


# ================================================================ NPC quest markers (over an NPC's head)
def marker(p, rim, face):
    sh = shield_pts(C0, 500, 760, 900)
    p.part(poly(sh), z=0.14, lift=0.18, bevel=34, mat=rim)
    p.flat(poly(inset_pts(sh, C0, 480, 0.84)), 0.24, face)
    p.part(box(C0, 50, 200, 60, 20), z=0.28, lift=0.06, bevel=14, mat=rim)    # the hanging ring's bar
    p.part(ring(C0, 34, 50, 22), z=0.30, lift=0.06, bevel=10, mat=rim)


@piece("NpcOffer", 256)
def npc_offer():
    p = P(301)
    marker(p, "gilt", "crimson_enamel")
    p.part(bang(C0, 470, 250), z=0.30, lift=0.16, bevel=30, mat="gilt")
    return p


@piece("NpcTurnIn", 256)
def npc_turnin():
    p = P(302)
    marker(p, "gilt", "ink")
    p.part(check(C0 + 20, 440, 300, 104), z=0.30, lift=0.16, bevel=32, mat="gilt")
    return p


@piece("NpcRetry", 256)
def npc_retry():
    p = P(303)
    marker(p, "brass_old", "ink")
    r, th = np.hypot(xx - C0, yy - 450), np.degrees(np.arctan2(yy - 450, xx - C0))
    arc = M(np.abs(r - 200) - 44) * ((th < 120) | (th > 175))
    a = math.radians(120)
    tx, ty = C0 + 200 * math.cos(a), 450 + 200 * math.sin(a)
    head = poly([(tx + 105 * math.cos(a), ty + 105 * math.sin(a)), (tx - 105 * math.cos(a), ty - 105 * math.sin(a)),
                 (tx + 130 * math.cos(a + math.pi / 2), ty + 130 * math.sin(a + math.pi / 2))])
    p.part(U(arc, head), z=0.30, lift=0.14, bevel=28, mat="brass")
    return p


@piece("NpcActive", 256)
def npc_active():
    p = P(304)
    marker(p, "iron", "ink")
    cy = 450
    for y in (cy - 230, cy + 230):
        p.part(box(C0, y, 300, 50, 16), z=0.32, lift=0.08, bevel=14, mat="brass")
    for x in (C0 - 120, C0 + 120):
        p.part(box(x, cy, 26, 460, 10), z=0.34, lift=0.06, bevel=10, mat="brass")
    glass = poly(bez((410, cy - 200), (410, cy - 70), (500, cy - 30), (500, cy)) + bez((500, cy), (500, cy + 30), (410, cy + 70), (410, cy + 200))
                 + [(614, cy + 200)] + bez((614, cy + 200), (614, cy + 70), (524, cy + 30), (524, cy)) + bez((524, cy), (524, cy - 30), (614, cy - 70), (614, cy - 200)))
    p.part(glass, z=0.24, lift=0.10, bevel=40, mat="glass")
    p.emboss(U(poly([(440, cy - 110), (584, cy - 110), (520, cy - 10), (504, cy - 10)]), poly([(430, cy + 196), (594, cy + 196), (550, cy + 120), (474, cy + 120)])), 0.05, 16, mat="sand")
    return p


# ================================================================ world
@piece("ArrivalCrest", 1024)
def arrival_crest():
    """the school gates under a moon, in a gilt ring: the stamp when you arrive"""
    p = P(401)
    p.part(ring(C0, C0, 462, 64), z=0.14, lift=0.18, bevel=30, mat="gilt")
    p.groove(ring(C0, C0, 462, 6), 0.03)
    rivets(p, C0, C0, 462, 24, 9, "brass_old", z=0.34)
    p.flat(circle(C0, C0, 428), 0.12, "ink", 0.003)
    # the arch and the gate posts
    gate = M(np.abs(sd_circle(C0, 470, 270)) - 16) * (yy < 470)
    p.part(gate, z=0.24, lift=0.08, bevel=10, mat="iron")
    for s in (-1, 1):
        p.part(box(C0 + s * 290, 650, 70, 420, 6), z=0.26, lift=0.10, bevel=14, mat="iron")
        p.part(box(C0 + s * 290, 432, 96, 40, 6), z=0.32, lift=0.06, bevel=10, mat="brass")
        p.part(circle(C0 + s * 290, 395, 34), z=0.32, lift=0.10, bevel=18, mat="brass")
    for k in range(-4, 5):          # bars with spear tips, rising to the middle
        x = C0 + k * 56
        top = 470 - math.sqrt(max(0, 270 ** 2 - (k * 56) ** 2)) + 40
        p.part(box(x, (top + 860) / 2, 16, 860 - top, 6), z=0.22, lift=0.06, bevel=6, mat="iron")
        p.part(poly([(x, top - 46), (x + 22, top), (x - 22, top)]), z=0.26, lift=0.06, bevel=8, mat="brass")
    for y in (620, 760):
        p.part(box(C0, y, 520, 20, 6), z=0.24, lift=0.06, bevel=6, mat="iron")
    p.part(box(C0, 866, 760, 26, 8), z=0.22, lift=0.06, bevel=8, mat="iron")
    cres = sub(circle(C0, 228, 92), circle(C0 + 40, 205, 82))
    p.part(cres, z=0.30, lift=0.12, bevel=24, mat="gilt")
    for x, y, s in ((C0 - 160, 200, 26), (C0 + 170, 240, 20), (C0 + 110, 150, 16)):
        twinkle(p, x, y, s, "gilt")
    return p


@piece("ClockDial")
def clock_dial():
    """the get-up dial on the floor (the game draws the hands)"""
    p = P(402)
    p.part(circle(C0, C0, 490), z=0.12, lift=0.16, bevel=30, mat="brass")
    p.groove(ring(C0, C0, 470, 5), 0.03)
    p.flat(circle(C0, C0, 440), 0.20, "ivory", 0.003)
    r, th = np.hypot(xx - C0, yy - C0), np.arctan2(yy - C0, xx - C0)
    deg = (np.degrees(th) + 360) % 360
    for step, r0, w in ((6, 400, 3.0), (30, 380, 7.0)):
        kk = np.abs(((deg + step / 2) % step) - step / 2) * (math.pi / 180) * r
        tick = np.clip(w - kk, 0, 1) * ((r > r0) & (r < 428))
        p.groove(tick, 0.01)
        p.paint(tick, "ink")
    p.groove(ring(C0, C0, 372, 3), 0.008)
    p.paint(ring(C0, C0, 372, 3), "ink")
    for k, num in enumerate(("XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI")):
        a = math.radians(-90 + k * 30)
        x, y = C0 + 300 * math.cos(a), C0 + 300 * math.sin(a)
        t = text(num, 66, x, y, rot=k * 30)
        p.groove(t, 0.012)
        p.paint(t, "ink")
    p.part(circle(C0, C0, 40), z=0.30, lift=0.08, bevel=16, mat="brass")
    return p


@piece("DiscoverFlag", 256)
def discover_flag():
    p = P(403)
    p.part(ellipse(470, 900, 300, 70), z=0.10, lift=0.08, bevel=30, mat="oak")
    p.part(box(330, 520, 40, 760, 18), z=0.24, lift=0.10, bevel=16, mat="brass")
    p.part(circle(330, 130, 42), z=0.30, lift=0.10, bevel=20, mat="gilt")
    top = bez((350, 170), (520, 120), (650, 230), (880, 190), 40)
    bot = bez((880, 520), (660, 560), (520, 450), (350, 500), 40)
    flag = poly(top + [(760, 355)] + bot)
    p.part(flag, z=0.20, lift=0.10, bevel=40, mat="leather")
    p.h += 0.05 * (0.5 + 0.5 * np.sin((xx - 350) / 90)) * flag
    p.part(star(560, 340, 70, 30, 5), z=0.34, lift=0.06, bevel=12, mat="gilt")
    return p


@piece("WaypointMark", 256)
def waypoint_mark():
    """the waypoint's marker: a pin with a clear ivory head (the game turns an arrow inside it)"""
    p = P(404)
    hx, hy, r = C0, 500, 330
    tail = poly([(hx - 190, hy + 270), (hx + 190, hy + 270), (hx, 1000)])
    p.part(U(circle(hx, hy, r + 60), tail), z=0.14, lift=0.18, bevel=34, mat="gilt")
    p.flat(circle(hx, hy, r), 0.24, "ivory", 0.003)
    p.groove(ring(hx, hy, r - 14, 4), 0.02)
    fac = ngon_facets(hx, 860, 44, 6, 0)
    p.custom(np.clip(fac + 0.5, 0, 1).astype(f32), 0.36 + 0.002 * np.clip(fac, 0, 40), "crimson_enamel")
    for k in range(4):
        a = math.radians(k * 90)
        x, y = hx + (r - 34) * math.cos(a), hy + (r - 34) * math.sin(a)
        p.groove(seg(x, y, hx + (r - 2) * math.cos(a), hy + (r - 2) * math.sin(a), 10), 0.015)
        p.paint(seg(x, y, hx + (r - 2) * math.cos(a), hy + (r - 2) * math.sin(a), 10), "brass_old")
    return p


@piece("DuelRing", 256)
def duel_ring():
    p = P(405)
    for s in (-1, 1):
        x0, y0, x1, y1 = C0 - s * 360, 880, C0 + s * 330, 140
        p.part(seg(x0 + s * 60, y0 - 64, x1, y1, 64), z=0.22, lift=0.12, bevel=16, mat="silver")
        p.groove(seg(x0 + s * 120, y0 - 126, x1 - s * 40, y1 + 42, 6), 0.03)
        gx, gy = x0 + s * 120, y0 - 130
        L = math.hypot(x1 - x0, y1 - y0)
        px, py = (y1 - y0) / L, -(x1 - x0) / L          # across the blade
        p.part(seg(gx - px * 110, gy - py * 110, gx + px * 110, gy + py * 110, 38), z=0.30, lift=0.10, bevel=12, mat="brass")
        p.part(seg(x0, y0, gx, gy, 44), z=0.28, lift=0.10, bevel=14, mat="leather_black")
        p.part(circle(x0, y0, 44), z=0.32, lift=0.10, bevel=18, mat="brass")
    return p


# ================================================================ sports touch buttons
SPORT_FACE = {"B": "crimson_enamel", "S": "green_enamel", "F": "oak"}
PY = 400   # the pictogram's centre (the button title sits in the lower band)


def sport_button(p, sport):
    p.part(circle(C0, C0, 490), z=0.12, lift=0.18, bevel=36, mat="brass")
    p.groove(ring(C0, C0, 470, 5), 0.025)
    rivets(p, C0, C0, 455, 16, 9, z=0.30, phase=math.pi / 16)
    p.flat(circle(C0, C0, 420), 0.22, SPORT_FACE[sport])
    p.groove(ring(C0, C0, 408, 4), 0.02)
    band = circle(C0, C0, 420) * (yy > 690)            # a darker band behind the title
    p.flat(band, 0.20, "ink")
    p.part(seg(150, 690, 874, 690, 10) * circle(C0, C0, 418), z=0.24, lift=0.04, bevel=5, mat="brass_old")


def basketball(p, cx, cy, r):
    p.part(circle(cx, cy, r), z=0.30, lift=0.16, bevel=int(r * 0.5), mat="ivory")
    sm = U(seg(cx - r, cy, cx + r, cy, 8), seg(cx, cy - r, cx, cy + r, 8),
           M(np.abs(sd_circle(cx - r * 1.25, cy, r * 0.95)) - 4) * circle(cx, cy, r),
           M(np.abs(sd_circle(cx + r * 1.25, cy, r * 0.95)) - 4) * circle(cx, cy, r))
    p.groove(sm * circle(cx, cy, r - 2), 0.03)
    p.paint(sm * circle(cx, cy, r - 2), "ink")


def soccerball(p, cx, cy, r):
    p.part(circle(cx, cy, r), z=0.30, lift=0.16, bevel=int(r * 0.5), mat="ivory")
    p.paint(ngon(cx, cy, r * 0.36, 5), "ink")
    for k in range(5):
        a = math.radians(-90 + k * 72)
        x, y = cx + r * 0.86 * math.cos(a), cy + r * 0.86 * math.sin(a)
        m = ngon(x, y, r * 0.30, 5, -90 + k * 72 + 36) * circle(cx, cy, r - 4)
        p.paint(m, "ink")
        p.groove(seg(cx + r * 0.36 * math.cos(a), cy + r * 0.36 * math.sin(a), x, y, 6) * circle(cx, cy, r - 4), 0.02)
    p.emboss(circle(cx, cy, r), 0.0, 1)


def football(p, cx, cy, rx, ry, rot):
    p.part(ellipse(cx, cy, rx, ry, rot), z=0.30, lift=0.16, bevel=int(ry * 0.6), mat="ivory")
    a = math.radians(rot)
    ux, uy = math.cos(a), math.sin(a)
    lace = seg(cx - ux * rx * 0.45, cy - uy * rx * 0.45, cx + ux * rx * 0.45, cy + uy * rx * 0.45, 12)
    for k in range(-3, 4):
        x, y = cx + ux * k * rx * 0.13, cy + uy * k * rx * 0.13
        lace = U(lace, seg(x - uy * 34, y + ux * 34, x + uy * 34, y - ux * 34, 10))
    p.part(lace, z=0.44, lift=0.03, bevel=4, mat="ink")
    for s in (-1, 1):
        x, y = cx + ux * rx * 0.72 * s, cy + uy * rx * 0.72 * s
        st = seg(x - uy * ry * 0.7, y + ux * ry * 0.7, x + uy * ry * 0.7, y - ux * ry * 0.7, 10) * ellipse(cx, cy, rx - 6, ry - 6, rot)
        p.groove(st, 0.02)
        p.paint(st, "ink")


def dotted(p, pts, r=14, step=56, mat="gilt"):
    path = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        for k in range(int(L // step) + 1):
            path.append((x0 + (x1 - x0) * k * step / L, y0 + (y1 - y0) * k * step / L))
    for x, y in path:
        p.part(circle(x, y, r), z=0.28, lift=0.06, bevel=r, mat=mat)


def pict(p, mask, mat="gilt", z=0.30):
    p.part(mask, z=z, lift=0.14, bevel=26, mat=mat)


def boot(cx, cy, s, flip=1, rot=0):
    """a football boot in profile, toe pointing +x (flip -1 points it -x)"""
    def X(u):
        return cx + flip * u * s

    upper = poly([(X(-0.50), cy - 0.62 * s), (X(-0.12), cy - 0.62 * s), (X(-0.04), cy - 0.12 * s), (X(0.40), cy - 0.02 * s),
                  (X(0.60), cy + 0.06 * s), (X(0.66), cy + 0.22 * s), (X(-0.56), cy + 0.22 * s), (X(-0.58), cy - 0.2 * s)])
    toe = ellipse(X(0.52), cy + 0.13 * s, 0.17 * s, 0.11 * s)
    sole = box(cx + flip * 0.04 * s, cy + 0.27 * s, 1.24 * s, 0.10 * s, 0.05 * s)
    studs = U(*[box(X(u), cy + 0.36 * s, 0.09 * s, 0.10 * s, 0.03 * s) for u in (-0.45, -0.25, 0.15, 0.40)])
    m = U(upper, toe, sole, studs)
    if rot:
        from make_app_icons import rotate
        m = rotate(m, rot, cx, cy)
    return m


def sport_piece(name, sport, fn):
    @piece(name)
    def run():
        p = P(500 + len(PIECES))
        sport_button(p, sport)
        fn(p)
        return p
    return run


def b_shoot(p):
    hx, hy = 680, 250
    p.part(ellipse(hx, hy, 130, 36), z=0.30, lift=0.06, bevel=10, mat="brass")
    p.recess(ellipse(hx, hy, 104, 20), 0.06, 8, mat="ink")
    for k in range(-2, 3):
        p.part(seg(hx + k * 44, hy + 30, hx + k * 30, hy + 150, 10), z=0.26, lift=0.03, bevel=4, mat="ivory")
    p.part(seg(hx - 100, hy + 100, hx + 100, hy + 100, 8), z=0.26, lift=0.03, bevel=4, mat="ivory")
    p.part(box(hx + 170, hy - 30, 24, 260, 6), z=0.26, lift=0.05, bevel=6, mat="iron")
    dotted(p, bez((380, 470), (380, 200), (520, 140), (620, 200), 9), 13, 52)
    basketball(p, 330, 540, 120)


def b_pass(p):
    basketball(p, 300, PY, 125)
    pict(p, arrow(470, PY, 800, PY, 70, 2.6))
    pict(p, seg(470, PY - 110, 640, PY - 110, 26), "brass_old", 0.26)
    pict(p, seg(470, PY + 110, 640, PY + 110, 26), "brass_old", 0.26)


def b_move(p):
    basketball(p, 280, 520, 110)
    pict(p, arrow_path([(400, 560), (520, 300), (640, 520), (800, 260)], 52, 2.8))


def b_euro(p):
    basketball(p, 770, 250, 100)
    from make_app_icons import rotate
    for x, y, rot in ((270, 560, -20), (470, 420, 25)):     # two shoe prints, stepping one way then the other
        foot = U(ellipse(x, y - 30, 44, 66), ellipse(x, y + 72, 34, 38))
        pict(p, rotate(foot, rot, x, y), "ivory", 0.30)
    pict(p, arrow_path([(330, 470), (420, 330), (540, 360), (650, 250)], 36, 3.0))


def s_kick(p):
    pict(p, boot(360, 420, 300, 1, -25), "ivory")
    soccerball(p, 720, 360, 120)
    for k in range(3):
        a = math.radians(-150 + k * 30)
        pict(p, seg(720 + 160 * math.cos(a + math.pi), 360 + 160 * math.sin(a + math.pi), 720 + 220 * math.cos(a + math.pi), 360 + 220 * math.sin(a + math.pi), 22), "gilt", 0.28)


def s_pass(p):
    soccerball(p, 280, 470, 110)
    pict(p, arrow(420, 470, 810, 470, 62, 2.6))
    pict(p, seg(170, 600, 850, 600, 20), "brass_old", 0.26)


def s_dribble(p):
    soccerball(p, 720, 470, 110)
    dotted(p, bez((170, 260), (330, 560), (430, 180), (580, 480), 12), 15, 58)
    pict(p, boot(260, 560, 170, 1, 0), "ivory")


def s_tackle(p):
    pict(p, boot(430, 560, 330, 1, 0), "ivory")
    for k in range(3):
        pict(p, seg(110, 470 + k * 50, 250 - k * 30, 470 + k * 50, 20), "brass_old", 0.26)
    soccerball(p, 760, 400, 105)
    pict(p, seg(150, 640, 870, 640, 18), "brass_old", 0.24)


def s_feint(p):
    soccerball(p, 280, 520, 105)
    r, th = np.hypot(xx - 560, yy - 380), np.degrees(np.arctan2(yy - 380, xx - 560))
    hook = M(np.abs(r - 150) - 26) * ((th > -180) & (th < 10)) * (yy < 400)
    pict(p, U(hook, seg(410, 380, 410, 560, 52) * (yy > 370)))
    pict(p, arrow(710, 380, 710, 600, 52, 2.8))


def s_rush(p):
    soccerball(p, 700, 420, 120)
    for k, (y, L) in enumerate(((300, 330), (420, 400), (540, 330))):
        pict(p, seg(540 - L, y, 540, y, 34 - k * 2), "gilt", 0.28)


def f_throw(p):
    football(p, 320, 500, 150, 92, -30)
    dotted(p, bez((440, 380), (520, 170), (700, 150), (800, 320), 10), 14, 54)
    pict(p, arrow(780, 300, 830, 400, 40, 2.8))


def f_dive(p):
    football(p, 640, 520, 140, 84, 15)
    pict(p, arrow_path([(170, 230), (360, 260), (480, 420)], 54, 2.8))
    pict(p, seg(160, 640, 860, 640, 18), "brass_old", 0.24)


def f_juke(p):
    football(p, 250, 520, 120, 74, -20)
    pict(p, arrow_path([(380, 560), (560, 560), (470, 300), (800, 300)], 52, 2.8))


def f_hit(p):
    hx, hy = 470, 420
    shell = sub(ellipse(hx, hy, 230, 200), box(hx + 210, hy + 150, 200, 200))
    p.part(shell, z=0.28, lift=0.16, bevel=60, mat="ivory")
    p.part(seg(hx - 60, hy - 190, hx - 60, hy + 160, 30) * shell, z=0.44, lift=0.04, bevel=8, mat="crimson_enamel")
    p.recess(ellipse(hx + 40, hy + 60, 50, 44), 0.08, 14, mat="ink")
    mask = U(seg(hx + 170, hy + 30, hx + 300, hy + 30, 22), seg(hx + 230, hy + 30, hx + 230, hy + 150, 22),
             seg(hx + 170, hy + 150, hx + 300, hy + 150, 22))
    p.part(mask, z=0.40, lift=0.08, bevel=10, mat="iron")
    for k in range(5):
        a = math.radians(-60 + k * 30)
        pict(p, seg(hx + 290 + 40 * math.cos(a), hy - 120 + 40 * math.sin(a), hx + 290 + 130 * math.cos(a), hy - 120 + 130 * math.sin(a), 24), "gilt", 0.28)


def f_snap(p):
    football(p, 560, 360, 150, 86, 0)
    pict(p, seg(150, 500, 870, 500, 18), "brass_old", 0.24)
    pict(p, arrow_path([(560, 470), (560, 590), (330, 590)], 50, 2.8))


SPORTS = [("SportShoot", "B", b_shoot), ("SportPass", "B", b_pass), ("SportMove", "B", b_move), ("SportEuro", "B", b_euro),
          ("SoccerKick", "S", s_kick), ("SoccerPass", "S", s_pass), ("SoccerDribble", "S", s_dribble),
          ("SoccerTackle", "S", s_tackle), ("SoccerFeint", "S", s_feint), ("SoccerRush", "S", s_rush),
          ("FootballThrow", "F", f_throw), ("FootballDive", "F", f_dive), ("FootballJuke", "F", f_juke),
          ("FootballHit", "F", f_hit), ("FootballSnap", "F", f_snap)]
for _n, _s, _f in SPORTS:
    sport_piece(_n, _s, _f)


# ================================================================ phone, activities, phone games
@piece("GradeSeal", 512, "grey")
def grade_seal():
    """the report-card grade seal: tinted in game, so it renders white wax; a smooth centre for the letter"""
    p = P(601)
    r, th = np.hypot(xx - C0, yy - C0), np.arctan2(yy - C0, xx - C0)
    rng = np.random.default_rng(11)
    edge = 440 + 14 * np.sin(5 * th + 1.1) + 8 * np.sin(11 * th + 0.3)
    for ang, size in ((0.9, 40), (2.9, 26), (4.6, 46)):
        d = np.angle(np.exp(1j * (th - ang)))
        edge += size * np.exp(-(d / 0.12) ** 2)
    blob = np.clip(edge - r + 0.5, 0, 1).astype(f32)
    p.part(blob, z=0.14, lift=0.20, bevel=60, mat="wax_white")
    p.recess(circle(C0, C0, 360), 0.10, 30)
    p.part(ring(C0, C0, 346, 22), z=0.26, lift=0.05, bevel=10, mat="wax_white")
    for s in (-1, 1):       # a laurel pressed in round the centre
        for k in range(9):
            a = math.radians(105 + k * 18) if s < 0 else math.radians(75 - k * 18)
            x, y = C0 + 300 * math.cos(a), C0 + 300 * math.sin(a)
            rot = math.degrees(a) + (90 if s < 0 else -90) + s * 35
            p.emboss(ellipse(x, y, 16, 38, rot), 0.04, 12)
    p.h += 0.04 * H.dome(ndimage.distance_transform_edt(circle(C0, C0, 230) > 0.5).astype(f32), 120) * circle(C0, C0, 230)
    p.m[p.a > 0.02] = MAT["wax_white"]
    return p


@piece("CoinYen")
def coin_yen():
    p = P(602)
    r, th = np.hypot(xx - C0, yy - C0), np.arctan2(yy - C0, xx - C0)
    p.part(circle(C0, C0, 470), z=0.14, lift=0.18, bevel=30, mat="gilt")
    p.h += 0.02 * (r > 440) * np.cos(th * 140) * circle(C0, C0, 470)
    p.groove(ring(C0, C0, 405, 8), 0.04)
    for k in range(48):
        a = k * 2 * math.pi / 48
        p.emboss(circle(C0 + 378 * math.cos(a), C0 + 378 * math.sin(a), 9), 0.04, 6)
    p.flat(circle(C0, C0, 350), 0.26, "gilt")
    p.emboss(text("¥", 520, C0, C0 + 14), 0.14, 14, mat="gilt")
    return p


def phase_shift(k, d):
    """moon k of 8 (0 new, 4 full): how far its shadow disc sits off it (0 = all shadow, +-d = none)"""
    return d * k / 4 if k <= 4 else -d * (8 - k) / 4


@piece("CardBack")
def card_back():
    """the face-down memory card: a ring of moon phases round a dark centre (the "?" sits in it)"""
    p = P(603)
    lz = poly([(C0, 30), (994, C0), (C0, 994), (30, C0)])
    p.part(lz, z=0.12, lift=0.14, bevel=30, mat="brass")
    p.flat(poly([(C0, 96), (928, C0), (C0, 928), (96, C0)]), 0.20, "crimson_enamel")
    p.part(ring(C0, C0, 300, 30), z=0.24, lift=0.06, bevel=10, mat="gilt")
    p.flat(circle(C0, C0, 230), 0.22, "ink")
    for k in range(8):
        a = math.radians(-90 + k * 45)
        x, y = C0 + 300 * math.cos(a), C0 + 300 * math.sin(a)
        p.part(circle(x, y, 44), z=0.30, lift=0.10, bevel=20, mat="moon")
        p.paint(circle(x, y, 44) * circle(x + phase_shift(k, 88), y, 44), "moon_dark")   # the shadowed part
    for a in (0, 90, 180, 270):
        x, y = C0 + 400 * math.cos(math.radians(a)), C0 + 400 * math.sin(math.radians(a))
        twinkle(p, x, y, 40, "gilt")
    return p


@piece("HexRelic")
def hex_relic():
    """Hex Slash: a cursed pocket watch (the relic that used to be the wax seal)"""
    p = P(604)
    cy = 560
    p.part(ring(C0, 128, 70, 30), z=0.24, lift=0.08, bevel=12, mat="gilt")
    p.part(box(C0, 190, 90, 70, 18), z=0.26, lift=0.10, bevel=18, mat="gilt")
    for k in range(5):
        p.groove(seg(C0 - 36 + k * 18, 160, C0 - 36 + k * 18, 220, 5), 0.03)
    p.part(circle(C0, cy, 380), z=0.14, lift=0.18, bevel=40, mat="gilt")
    p.groove(ring(C0, cy, 350, 6), 0.03)
    p.flat(circle(C0, cy, 320), 0.22, "ivory", 0.003)
    r, th = np.hypot(xx - C0, yy - cy), np.arctan2(yy - cy, xx - C0)
    deg = (np.degrees(th) + 360) % 360
    kk = np.abs(((deg + 15) % 30) - 15) * (math.pi / 180) * r
    tick = np.clip(9 - kk, 0, 1) * ((r > 250) & (r < 300))
    p.groove(tick, 0.01)
    p.paint(tick, "ink")
    p.part(seg(C0, cy, C0 + 120, cy - 150, 22), z=0.30, lift=0.04, bevel=6, mat="iron")
    p.part(seg(C0, cy, C0 - 60, cy + 200, 16), z=0.30, lift=0.04, bevel=6, mat="iron")
    p.part(circle(C0, cy, 30), z=0.34, lift=0.06, bevel=12, mat="brass")
    crack = polyline([(C0 + 170, cy - 220), (C0 + 120, cy - 120), (C0 + 180, cy - 40), (C0 + 130, cy + 60)], 8) * circle(C0, cy, 318)
    p.groove(crack, 0.03)
    p.paint(crack, "ink")
    return p


@piece("HexAltar", 512, "grey")
def hex_altar():
    """Hex Slash's altar: an engraved circle of moon phases, pressed faint into the dark (tinted in game)"""
    p = P(605)
    p.part(ring(C0, C0, 470, 30), z=0.18, lift=0.06, bevel=10, mat="wax_white")
    p.part(ring(C0, C0, 400, 14), z=0.16, lift=0.05, bevel=6, mat="wax_white")
    p.part(ring(C0, C0, 250, 12), z=0.16, lift=0.05, bevel=6, mat="wax_white")
    for k in range(8):
        a = math.radians(-90 + k * 45)
        x, y = C0 + 330 * math.cos(a), C0 + 330 * math.sin(a)
        dsk = circle(x, y, 48)
        lit = ring(x, y, 44, 8) if k == 0 else sub(dsk, circle(x + phase_shift(k, 96), y, 48))
        p.part(U(lit, ring(x, y, 46, 4)), z=0.18, lift=0.06, bevel=10, mat="wax_white")
    for k in range(3):
        a = math.radians(-90 + k * 120)
        b = math.radians(-90 + (k + 1) * 120)
        p.part(seg(C0 + 230 * math.cos(a), C0 + 230 * math.sin(a), C0 + 230 * math.cos(b), C0 + 230 * math.sin(b), 10), z=0.16, lift=0.04, bevel=5, mat="wax_white")
    fl = poly(bez((C0, 380), (C0 + 90, 470), (C0 + 80, 560), (C0, 600)) + bez((C0, 600), (C0 - 80, 560), (C0 - 90, 470), (C0, 380)))
    p.part(fl, z=0.18, lift=0.10, bevel=30, mat="wax_white")
    p.part(box(C0, 660, 90, 80, 10), z=0.18, lift=0.06, bevel=12, mat="wax_white")
    p.m[p.a > 0.02] = MAT["wax_white"]
    return p


@piece("CryptRune")
def crypt_rune():
    """Crypt Crush: the seal piece (a match of 5): an iron keystone with a burning sun rune"""
    p = P(606)
    p.part(ngon(C0, C0, 480, 6, 0), z=0.12, lift=0.18, bevel=40, mat="iron")
    p.groove(ngon(C0, C0, 440, 6, 0) - ngon(C0, C0, 432, 6, 0), 0.03)
    p.flat(ngon(C0, C0, 400, 6, 0), 0.22, "ink")
    for k in range(6):
        a = math.radians(k * 60)
        p.part(circle(C0 + 455 * math.cos(a), C0 + 455 * math.sin(a), 16), z=0.32, lift=0.06, bevel=12, mat="brass")
    p.part(star(C0, C0, 330, 150, 12, -90), z=0.26, lift=0.10, bevel=24, mat="gilt")
    p.part(circle(C0, C0, 160), z=0.32, lift=0.10, bevel=24, mat="brass")
    fac = ngon_facets(C0, C0, 115, 8, math.pi / 8)
    p.custom(np.clip(fac + 0.5, 0, 1).astype(f32), 0.42 + 0.0016 * np.clip(fac, 0, 80) + 0.10 * np.clip((np.clip(fac, 0, 80) - 50) / 30, 0, 1), "crimson_enamel")
    return p


if __name__ == "__main__":
    want = sys.argv[1:]
    listing = MAPS / "pieces.json"
    have = {p["name"]: p for p in json.loads(listing.read_text())} if listing.exists() else {}
    for n, fn in PIECES.items():
        if want and n not in want:
            continue
        have[n] = fn()
    listing.write_text(json.dumps([have[k] for k in PIECES if k in have], indent=1))
    print("pieces:", len(have))
