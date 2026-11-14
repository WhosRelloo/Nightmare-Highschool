"""The shop icon set, stage 1 of 3: every developer product, gamepass and the subscription as relief + material maps.

Owner (2026-11-13): "I want the products to be cheaper ... Rerolls should be super cheap. Create designs for all of
them on theme and their prices." docs/Monetization-Concepts.md has the product list and prices.

Same pipeline as the seal-replacement icons (make_seal_icons.py): each design is a 2D HEIGHT field with a MATERIAL id
per pixel; stage 2 (blender_shop_icons_render.py) renders it as displaced PBR geometry, stage 3 (finish_shop_icons.py)
cleans the edges and writes art/group-upload-shop/NHShop<Name>.png at 512 px.

Every icon sits on a round medallion (Roblox crops gamepass icons to a circle; developer products show square, so the
medallion reads the same in both). The face colour says the family at a glance:
  spins and identity   ink face, gilt rim          personal effects   oak face, brass rim
  wardrobe             crimson face, gilt rim       moments            midnight-blue face, silver rim
  passes               ink face, gilt rim + laurel  the subscription   ink face, silver rim + laurel
A small brass plate at the foot of a pack's medallion carries its count ("x5").

    python make_shop_icons.py [Name ...]   ->  out/shop_icons/maps/<Name>_h.png (16-bit) _m.png _a.png, pieces.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as H
from make_app_icons import (M, box, circle, ring, seg, ellipse, poly, U, sub, text, sd_circle, xx, yy, bez,
                            ngon_facets)
from make_seal_icons import P, MAT, star, ngon, shield_pts, inset_pts, rivets, laurel, polyline, arrow

HERE = Path(__file__).resolve().parent
MAPS = HERE / "out" / "shop_icons" / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
f32 = np.float32
C0 = 512

PIECES = {}


def piece(name, out=512):
    def deco(fn):
        def run():
            p = fn()
            Image.fromarray((np.clip(p.h, 0, 1) * 65535).astype(np.uint16)).save(MAPS / f"{name}_h.png")
            Image.fromarray(p.m.astype(np.uint8)).save(MAPS / f"{name}_m.png")
            Image.fromarray((np.clip(p.a, 0, 1) * 255).astype(np.uint8)).save(MAPS / f"{name}_a.png")
            ids = sorted({int(v) for v in np.unique(p.m[p.a > 0.02])} - {0})
            (MAPS / f"{name}_ids.json").write_text(json.dumps(ids))
            print("  maps", name, ids)
            return {"name": name, "w": p.W, "h": p.Hh, "out": out, "kind": "icon"}
        PIECES[name] = run
        return run
    return deco


# ================================================================ the medallion every icon sits on
FAMILY = {
    "spin": ("gilt", "ink"), "wardrobe": ("gilt", "crimson_enamel"), "effects": ("brass", "oak"),
    "moment": ("silver", "blue_enamel"), "pass": ("gilt", "ink"), "society": ("silver", "ink"),
}


def medallion(p, family, wreath=False):
    rim, face = FAMILY[family]
    R = 400 if wreath else 470
    if wreath:   # passes: a gilt laurel round the medallion
        laurel(p, C0, C0, 446, 7, mat="gilt", a0=104, span=118, size=(30, 64))   # two branches, open at the top
    p.part(circle(C0, C0, R), z=0.10, lift=0.16, bevel=32, mat=rim)
    p.groove(ring(C0, C0, R - 16, 4), 0.022)
    p.flat(circle(C0, C0, R - 52), 0.18, face)
    p.groove(ring(C0, C0, R - 64, 3), 0.016)
    return R


def count_plate(p, label, y=842, w=None):
    """the brass plate at the foot that carries a pack size: raised ivory letters with a dark ink outline round them"""
    w = w or (150 + 52 * len(label))
    p.part(box(C0, y, w, 116, 42), z=0.34, lift=0.08, bevel=20, mat="brass")
    p.groove(box(C0, y, w - 22, 94, 34) - box(C0, y, w - 30, 86, 30), 0.012)
    t = text(label, 84, C0, y + 4)
    outline = np.clip(ndimage.grey_dilation(t, size=(15, 15)) - t, 0, 1).astype(f32)
    p.recess(outline, 0.03, 4, mat="ink")                 # the outline: a dark inked groove round every letter
    p.emboss(t, 0.11, 7, mat="ivory")                     # the letters themselves, raised and bevelled


def reroll_arrows(p, cx, cy, r, w=26, mat="gilt", z=0.30):
    """two curved arrows chasing each other round a circle: the reroll mark"""
    for a0 in (200, 20):
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(a0, a0 + 125, 8)]
        p.part(polyline(pts, w), z=z, lift=0.06, bevel=10, mat=mat)
        a1 = math.radians(a0 + 125)
        tx, ty = cx + r * math.cos(a1), cy + r * math.sin(a1)
        dx, dy = -math.sin(a1), math.cos(a1)
        head = poly([(tx + dx * 46, ty + dy * 46), (tx - dy * 34 - dx * 6, ty + dx * 34 - dy * 6), (tx + dy * 34 - dx * 6, ty - dx * 34 - dy * 6)])
        p.part(head, z=z, lift=0.06, bevel=10, mat=mat)


def gem(p, cx, cy, R, n=8, mat="crimson_enamel", z=0.36, rot=math.pi / 8):
    fac = ngon_facets(cx, cy, R, n, rot)
    g = np.clip(fac + 0.5, 0, 1).astype(f32)
    p.custom(g, z + 0.0016 * np.clip(fac, 0, 90) + 0.10 * np.clip((np.clip(fac, 0, 90) - 50) / 40, 0, 1), mat)


def crescent(cx, cy, r, off=0.42, ang=-35):
    a = math.radians(ang)
    return sub(circle(cx, cy, r), circle(cx + r * off * math.cos(a), cy + r * off * math.sin(a), r * 0.9))


def bat(cx, cy, s):
    """a bat silhouette, wings spread"""
    body = U(ellipse(cx, cy, 0.16 * s, 0.30 * s), circle(cx, cy - 0.30 * s, 0.13 * s),
             poly([(cx - 0.12 * s, cy - 0.36 * s), (cx - 0.08 * s, cy - 0.56 * s), (cx - 0.02 * s, cy - 0.40 * s)]),
             poly([(cx + 0.12 * s, cy - 0.36 * s), (cx + 0.08 * s, cy - 0.56 * s), (cx + 0.02 * s, cy - 0.40 * s)]))
    wings = []
    for sg in (-1, 1):
        pts = [(cx + sg * 0.10 * s, cy - 0.20 * s), (cx + sg * 0.55 * s, cy - 0.45 * s), (cx + sg * 1.00 * s, cy - 0.30 * s),
               (cx + sg * 0.86 * s, cy + 0.02 * s), (cx + sg * 0.70 * s, cy - 0.06 * s), (cx + sg * 0.56 * s, cy + 0.14 * s),
               (cx + sg * 0.40 * s, cy + 0.04 * s), (cx + sg * 0.24 * s, cy + 0.22 * s), (cx + sg * 0.10 * s, cy + 0.10 * s)]
        wings.append(poly(pts))
    return U(body, *wings)


# ================================================================ spins and identity
def crest_shield(p, cx, cy, w, h, face="crimson_enamel", z=0.26):
    sh = shield_pts(cx, cy, w, h)
    p.part(poly(sh), z=z, lift=0.12, bevel=22, mat="gilt")
    p.flat(poly(inset_pts(sh, cx, cy, 0.80)), z + 0.06, face)
    # a chevron and three stars: an original clan device
    p.part(poly([(cx - w * 0.30, cy + h * 0.06), (cx, cy - h * 0.16), (cx + w * 0.30, cy + h * 0.06), (cx + w * 0.30, cy + h * 0.20),
                 (cx, cy - h * 0.02), (cx - w * 0.30, cy + h * 0.20)]), z=z + 0.10, lift=0.05, bevel=8, mat="gilt")
    for dx, dy in ((-0.18, -0.28), (0.18, -0.28), (0, 0.26)):
        p.part(star(cx + w * dx, cy + h * dy, w * 0.08, w * 0.035), z=z + 0.10, lift=0.05, bevel=6, mat="gilt")


def clan_icon(n, seed):
    p = P(seed)
    medallion(p, "spin")
    if n == 1:
        crest_shield(p, C0, 470, 330, 400)
    else:
        offs = [(-130, 30, "blue_enamel"), (130, 30, "green_enamel"), (0, -10, "crimson_enamel")] if n >= 5 else []
        for dx, dy, face in offs:
            crest_shield(p, C0 + dx, 470 + dy, 270, 330, face=face, z=0.22 if dx else 0.30)
        if n >= 15:
            for k, (dx, face) in enumerate(((-240, "gold_enamel"), (240, "crimson_enamel"))):
                crest_shield(p, C0 + dx, 520, 200, 250, face=face, z=0.18)
    reroll_arrows(p, C0, 470, 300, 22)
    count_plate(p, f"x{n}")
    return p


@piece("ClanSpins1")
def clan1(): return clan_icon(1, 1001)


@piece("ClanSpins5")
def clan5(): return clan_icon(5, 1002)


@piece("ClanSpins15")
def clan15(): return clan_icon(15, 1003)


def height_icon(n, seed):
    p = P(seed)
    medallion(p, "spin")
    # a brass measuring rod with notches, a silhouette beside it, arrows up and down
    p.part(box(420, 470, 70, 560, 14), z=0.26, lift=0.08, bevel=14, mat="brass")
    for k in range(15):
        y = 210 + k * 37
        L = 34 if k % 4 == 0 else 20
        p.groove(box(420 + 35 - L / 2, y, L, 7, 2), 0.05)
    fig = U(circle(600, 285, 54), box(600, 440, 120, 210, 46), box(568, 610, 44, 170, 18), box(632, 610, 44, 170, 18))
    p.part(fig, z=0.24, lift=0.12, bevel=24, mat="ivory")
    p.part(arrow(720, 470, 720, 220, 26), z=0.30, lift=0.06, bevel=10, mat="gilt")
    p.part(arrow(720, 470, 720, 720, 26), z=0.30, lift=0.06, bevel=10, mat="gilt")
    count_plate(p, f"x{n}")
    return p


@piece("HeightSpins3")
def height3(): return height_icon(3, 1011)


@piece("HeightSpins10")
def height10(): return height_icon(10, 1012)


def race_icon(n, seed):
    p = P(seed)
    medallion(p, "spin")
    # the bloodline: a crescent moon cradling a crimson gem, six small race marks round it
    p.part(crescent(C0, 460, 250, 0.38, -40), z=0.24, lift=0.14, bevel=26, mat="moon")
    p.part(circle(C0 + 30, 470, 120), z=0.28, lift=0.10, bevel=22, mat="brass")
    gem(p, C0 + 30, 470, 96)
    marks = ["moon", "silver", "gilt", "bone", "wax_red", "blue_enamel"]
    for k, mat in enumerate(marks):
        a = math.radians(-90 + k * 60)
        p.part(circle(C0 + 330 * math.cos(a), 470 + 330 * math.sin(a) * 0.86, 30), z=0.30, lift=0.08, bevel=14, mat=mat)
    count_plate(p, f"x{n}")
    return p


@piece("RaceSpins3")
def race3(): return race_icon(3, 1021)


@piece("RaceSpins10")
def race10(): return race_icon(10, 1022)


def variant_icon(n, seed):
    p = P(seed)
    medallion(p, "spin")
    # one gem split three ways: the same race, another variant
    for k, (mat, dx) in enumerate((("blue_enamel", -150), ("crimson_enamel", 150), ("gold_enamel", 0))):
        p.part(circle(C0 + dx, 470 - (40 if dx == 0 else -40), 120), z=0.22 + 0.02 * k, lift=0.10, bevel=22, mat="brass")
        gem(p, C0 + dx, 470 - (40 if dx == 0 else -40), 96, 6, mat=mat, z=0.30 + 0.02 * k, rot=0)
    reroll_arrows(p, C0, 470, 300, 22)
    count_plate(p, f"x{n}")
    return p


@piece("VariantSpins3")
def variant3(): return variant_icon(3, 1031)


@piece("VariantSpins10")
def variant10(): return variant_icon(10, 1032)


def tarot(p, cx, cy, w, h, rot, mat_face="parchment", z=0.24, glyph=True):
    card = box(cx, cy, w, h, 22, rot)
    p.part(card, z=z, lift=0.06, bevel=12, mat="gilt")
    p.flat(box(cx, cy, w - 36, h - 36, 14, rot), z + 0.05, mat_face)
    if glyph:
        p.part(star(cx, cy - 10, w * 0.26, w * 0.11, 8, rot=-90 + rot), z=z + 0.10, lift=0.05, bevel=8, mat="gilt")
        p.part(crescent(cx, cy + h * 0.28, w * 0.12, 0.5, -90), z=z + 0.10, lift=0.04, bevel=6, mat="ink")


def trait_icon(n, seed):
    p = P(seed)
    medallion(p, "spin")
    tarot(p, C0 - 150, 470, 210, 330, -14, z=0.20)
    tarot(p, C0 + 150, 470, 210, 330, 14, z=0.22)
    tarot(p, C0, 450, 230, 360, 0, mat_face="ivory", z=0.28)
    count_plate(p, f"x{n}")
    return p


@piece("TraitSpins5")
def trait5(): return trait_icon(5, 1041)


@piece("TraitSpins15")
def trait15(): return trait_icon(15, 1042)


@piece("BloodlineBundle")
def bloodline_bundle():
    p = P(1051)
    medallion(p, "spin")
    p.part(crescent(C0 - 120, 420, 190, 0.38, -40), z=0.22, lift=0.12, bevel=22, mat="moon")
    gem(p, C0 - 100, 430, 74)
    tarot(p, C0 + 160, 430, 190, 300, 12, z=0.24)
    for k, mat in enumerate(("blue_enamel", "gold_enamel")):
        gem(p, C0 - 170 + k * 140, 640, 60, 6, mat=mat, z=0.30, rot=0)
    count_plate(p, "BUNDLE", y=846)
    return p


@piece("IdentityBundle")
def identity_bundle():
    p = P(1052)
    medallion(p, "spin")
    crest_shield(p, C0 - 110, 450, 280, 340)
    p.part(box(C0 + 170, 450, 64, 480, 12), z=0.26, lift=0.08, bevel=12, mat="brass")
    for k in range(12):
        L = 30 if k % 4 == 0 else 18
        p.groove(box(C0 + 170 + 32 - L / 2, 236 + k * 39, L, 7, 2), 0.05)
    count_plate(p, "BUNDLE", y=846)
    return p


@piece("NameChange")
def name_change():
    p = P(1061)
    medallion(p, "spin")
    # the school register: an open ledger, a quill across it, a crimson wax seal
    for sg in (-1, 1):
        pg = poly([(C0, 330), (C0 + sg * 300, 300), (C0 + sg * 300, 650), (C0, 690)])
        p.part(pg, z=0.22, lift=0.06, bevel=12, mat="parchment")
        for k in range(5):
            y = 380 + k * 52
            p.groove(seg(C0 + sg * 40, y + 6, C0 + sg * 250, y - 6, 5), 0.02)
    p.groove(seg(C0, 330, C0, 690, 8), 0.05)
    quill = poly([(330, 780), (360, 760), (760, 250), (800, 210), (790, 260), (400, 790)])
    p.part(quill, z=0.32, lift=0.10, bevel=18, mat="bone")
    p.groove(seg(350, 775, 780, 240, 6), 0.03)
    p.part(circle(700, 640, 78), z=0.34, lift=0.10, bevel=22, mat="wax_red")
    p.emboss(star(700, 640, 42, 18, 5), 0.05, 6)
    return p


# ================================================================ wardrobe
def cape(p, cx, cy, w, h, shell="leather_black", lining="crimson_enamel", collar="gilt", hem="straight"):
    top = cy - h / 2
    pts = [(cx - w * 0.22, top), (cx + w * 0.22, top)]
    pts += bez((cx + w * 0.22, top), (cx + w * 0.40, top + h * 0.3), (cx + w * 0.55, top + h * 0.7), (cx + w * 0.5, top + h))
    if hem == "bat":
        for k in range(4, -1, -1):
            x = cx - w * 0.5 + k * w * 0.25
            pts.append((x, top + h - (0 if k % 2 == 0 else h * 0.10)))
    elif hem == "torn":
        for k in range(8, -1, -1):
            x = cx - w * 0.5 + k * w / 8
            pts.append((x, top + h - (h * 0.07 if k % 2 else 0)))
    else:
        pts += bez((cx + w * 0.5, top + h), (cx + w * 0.2, top + h * 1.04), (cx - w * 0.2, top + h * 1.04), (cx - w * 0.5, top + h))
    pts += bez((cx - w * 0.5, top + h), (cx - w * 0.55, top + h * 0.7), (cx - w * 0.40, top + h * 0.3), (cx - w * 0.22, top))
    m = poly(pts)
    p.part(m, z=0.22, lift=0.12, bevel=30, mat=shell)
    for k in (-2, -1, 0, 1, 2):    # folds
        x0 = cx + k * w * 0.09
        p.groove(seg(x0, top + h * 0.18, x0 + k * w * 0.07, top + h * 0.92, 10), 0.035)
    lin = poly([(cx - w * 0.16, top + 10), (cx + w * 0.16, top + 10), (cx + w * 0.10, top + h * 0.55), (cx - w * 0.10, top + h * 0.55)])
    p.flat(lin, 0.26, lining)
    p.part(box(cx, top + 8, w * 0.56, 60, 26), z=0.34, lift=0.08, bevel=16, mat=collar)
    return m


@piece("CapeVamp")
def cape_vamp():
    p = P(2001)
    medallion(p, "wardrobe")
    cape(p, C0, 520, 560, 560, shell="leather_black", lining="crimson_enamel", collar="silver", hem="bat")
    for sg in (-1, 1):   # the tall collar points
        p.part(poly([(C0 + sg * 150, 270), (C0 + sg * 230, 150), (C0 + sg * 80, 240)]), z=0.36, lift=0.08, bevel=14, mat="leather_black")
    p.part(circle(C0, 250, 30), z=0.42, lift=0.08, bevel=12, mat="wax_red")
    return p


@piece("CapeRogue")
def cape_rogue():
    p = P(2002)
    medallion(p, "wardrobe")
    cape(p, C0, 530, 540, 540, shell="leather", lining="leather_black", collar="brass")
    hood = sub(ellipse(C0, 250, 170, 120), ellipse(C0, 290, 110, 80))
    p.part(hood, z=0.36, lift=0.10, bevel=22, mat="leather")
    p.part(circle(C0, 300, 26), z=0.42, lift=0.06, bevel=10, mat="brass")
    return p


@piece("CapeFur")
def cape_fur():
    p = P(2003)
    medallion(p, "wardrobe")
    cape(p, C0, 540, 560, 520, shell="oak", lining="leather", collar="bone")
    fur = U(*[circle(C0 - 230 + k * 46, 290 + 12 * math.sin(k * 1.7), 44) for k in range(11)])
    p.part(fur, z=0.36, lift=0.12, bevel=30, mat="ivory")
    p.h += 0.04 * p.noise(3) * fur
    return p


@piece("CloakRavenfeather")
def cloak_raven():
    p = P(2011)
    medallion(p, "wardrobe")
    m = cape(p, C0, 520, 560, 560, shell="leather_black", lining="ink", collar="silver", hem="torn")
    for k in range(9):     # feather tips along the hem
        x = C0 - 240 + k * 60
        p.part(ellipse(x, 770, 24, 70, 8 * (k - 4)), z=0.30, lift=0.08, bevel=14, mat="leather_black")
        p.groove(seg(x, 720, x, 820, 4), 0.02)
    p.part(bat(C0, 250, 90), z=0.40, lift=0.06, bevel=10, mat="silver")
    return p


@piece("CloakMoonlit")
def cloak_moonlit():
    p = P(2012)
    medallion(p, "wardrobe")
    cape(p, C0, 520, 560, 560, shell="blue_enamel", lining="silver", collar="silver")
    p.part(crescent(C0, 255, 46, 0.4, -40), z=0.42, lift=0.08, bevel=12, mat="moon")
    for k in range(7):
        a = k * 0.9
        p.part(star(C0 - 180 + k * 60, 480 + 120 * math.sin(a), 16, 7, 4), z=0.30, lift=0.04, bevel=5, mat="silver")
    return p


@piece("CloakAshen")
def cloak_ashen():
    p = P(2013)
    medallion(p, "wardrobe")
    cape(p, C0, 520, 560, 560, shell="iron", lining="leather", collar="brass")
    p.h += 0.03 * p.noise(2) * (p.m == MAT["iron"])
    p.part(circle(C0, 255, 44), z=0.42, lift=0.08, bevel=14, mat="brass")
    p.groove(ring(C0, 255, 28, 6), 0.04)
    return p


def hanger(p, cy=230):
    p.part(seg(C0, cy - 70, C0, cy - 20, 12), z=0.34, lift=0.04, bevel=6, mat="brass")
    p.part(sub(circle(C0 + 18, cy - 90, 30), circle(C0 + 18, cy - 90, 16), box(C0 + 30, cy - 70, 40, 30)), z=0.34, lift=0.04, bevel=6, mat="brass")
    p.part(poly([(C0, cy - 24), (C0 + 230, cy + 50), (C0 + 220, cy + 70), (C0, cy + 4), (C0 - 220, cy + 70), (C0 - 230, cy + 50)]), z=0.32, lift=0.05, bevel=8, mat="brass")


def coat(p, body="ink", lapel="crimson_enamel", trim="gilt", buttons="gilt", long=False):
    cy = 520
    h = 520 if long else 460
    pts = [(C0 - 200, 260), (C0 - 70, 240), (C0, 330), (C0 + 70, 240), (C0 + 200, 260), (C0 + 230, 260 + h), (C0 - 230, 260 + h)]
    p.part(poly(pts), z=0.22, lift=0.10, bevel=26, mat=body)
    for sg in (-1, 1):
        p.part(poly([(C0 + sg * 70, 240), (C0, 330), (C0 + sg * 30, 520), (C0 + sg * 110, 330)]), z=0.30, lift=0.06, bevel=12, mat=lapel)
    p.groove(seg(C0, 330, C0, 260 + h, 6), 0.03)
    for k in range(3):
        p.part(circle(C0 + 26, 560 + k * 70, 16), z=0.34, lift=0.05, bevel=8, mat=buttons)
    p.part(box(C0 - 120, 420, 80, 12, 4), z=0.30, lift=0.03, bevel=4, mat=trim)


@piece("OutfitMidnightPrefect")
def outfit_prefect():
    p = P(2021)
    medallion(p, "wardrobe")
    hanger(p)
    coat(p, body="ink", lapel="leather_black", trim="gilt", buttons="gilt")
    p.part(shield_pts and poly(shield_pts(C0 - 120, 380, 70, 84)), z=0.34, lift=0.05, bevel=8, mat="gilt")
    return p


@piece("OutfitCrimsonGala")
def outfit_gala():
    p = P(2022)
    medallion(p, "wardrobe")
    hanger(p)
    coat(p, body="leather", lapel="leather_black", trim="gilt", buttons="gilt", long=True)
    p.part(bat(C0, 360, 60), z=0.36, lift=0.04, bevel=6, mat="gilt")
    return p


@piece("OutfitGraveyardFormal")
def outfit_graveyard():
    p = P(2023)
    medallion(p, "wardrobe")
    hanger(p)
    coat(p, body="iron", lapel="ink", trim="silver", buttons="bone")
    p.part(poly([(C0 - 40, 330), (C0 + 40, 330), (C0 + 24, 400), (C0 - 24, 400)]), z=0.36, lift=0.04, bevel=6, mat="crimson_enamel")
    return p


@piece("EyeGlowTint")
def eye_glow():
    p = P(2031)
    medallion(p, "wardrobe")
    eye = poly(bez((240, 470), (380, 300), (644, 300), (784, 470)) + bez((784, 470), (644, 640), (380, 640), (240, 470)))
    p.part(eye, z=0.22, lift=0.10, bevel=26, mat="ivory")
    p.flat(circle(C0, 470, 130), 0.30, "ink")
    p.custom(circle(C0, 470, 100), 0.34 + 0.0 * xx, "flame")      # the glowing iris (emissive)
    p.flat(circle(C0, 470, 42), 0.36, "ink")
    p.part(circle(C0 + 40, 430, 16), z=0.40, lift=0.03, bevel=6, mat="glass")
    for k in range(5):   # tint swatches below
        mats = ("crimson_enamel", "gold_enamel", "blue_enamel", "green_enamel", "silver")
        p.part(circle(C0 - 160 + k * 80, 720, 30), z=0.30, lift=0.08, bevel=14, mat=mats[k])
    return p


# ================================================================ personal effects
def deck(p, face="crimson_enamel", trim="iron", trail=None):
    rot = -32
    if trail:
        for k in range(5):
            p.part(ellipse(C0 - 230 + k * 30, 620 + k * 26, 70 - k * 10, 18, rot), z=0.20, lift=0.04, bevel=8, mat=trail)
    board = box(C0, 460, 640, 200, 100, rot)
    p.part(board, z=0.24, lift=0.10, bevel=30, mat=face)
    p.groove(box(C0, 460, 600, 160, 80, rot) - box(C0, 460, 588, 148, 74, rot), 0.02)
    for d in (-210, 210):
        a = math.radians(rot)
        x, y = C0 + d * math.cos(a), 460 + d * math.sin(a)
        for s in (-1, 1):
            p.part(circle(x - s * 70 * math.sin(a), y + s * 70 * math.cos(a), 34), z=0.32, lift=0.08, bevel=14, mat=trim)
    return board


@piece("DeckHellfire")
def deck_hellfire():
    p = P(3001)
    medallion(p, "effects")
    deck(p, face="crimson_enamel", trim="iron", trail="flame")
    p.part(star(C0, 460, 60, 24, 6), z=0.36, lift=0.04, bevel=6, mat="gilt")
    return p


@piece("DeckMoonwake")
def deck_moonwake():
    p = P(3002)
    medallion(p, "effects")
    deck(p, face="blue_enamel", trim="silver", trail="moon")
    p.part(crescent(C0, 460, 60, 0.4, -40), z=0.36, lift=0.04, bevel=6, mat="moon")
    return p


@piece("DeckBoneRail")
def deck_bonerail():
    p = P(3003)
    medallion(p, "effects")
    deck(p, face="bone", trim="brass")
    a = math.radians(-32)
    for k in range(-4, 5):
        x, y = C0 + k * 56 * math.cos(a), 460 + k * 56 * math.sin(a)
        p.groove(seg(x - 60 * math.sin(a) * -1, y - 60 * math.cos(a), x + 60 * math.sin(a) * -1, y + 60 * math.cos(a), 10), 0.03)
    return p


@piece("LunchboxCoffin")
def lunch_coffin():
    p = P(3011)
    medallion(p, "effects")
    pts = [(C0 - 110, 230), (C0 + 110, 230), (C0 + 210, 360), (C0 + 140, 760), (C0 - 140, 760), (C0 - 210, 360)]
    p.part(poly(pts), z=0.22, lift=0.12, bevel=26, mat="leather_black")
    p.flat(poly(inset_pts(pts, C0, 480, 0.84)), 0.30, "oak")
    p.part(box(C0, 260, 160, 40, 12), z=0.36, lift=0.06, bevel=10, mat="brass")    # the handle
    p.part(box(C0, 470, 60, 90, 10), z=0.36, lift=0.06, bevel=10, mat="brass")     # the latch
    p.part(crescent(C0, 610, 40, 0.4, -40), z=0.36, lift=0.04, bevel=6, mat="gilt")
    return p


@piece("LunchboxBatTin")
def lunch_bat():
    p = P(3012)
    medallion(p, "effects")
    p.part(box(C0, 520, 520, 380, 50), z=0.22, lift=0.12, bevel=30, mat="iron")
    p.part(sub(box(C0, 300, 220, 110, 40), box(C0, 320, 150, 80, 24)), z=0.30, lift=0.06, bevel=12, mat="iron")
    p.part(bat(C0, 530, 170), z=0.32, lift=0.06, bevel=8, mat="silver")
    return p


@piece("LunchboxCrimsonBento")
def lunch_bento():
    p = P(3013)
    medallion(p, "effects")
    p.part(box(C0, 500, 540, 420, 40), z=0.22, lift=0.12, bevel=30, mat="crimson_enamel")
    p.groove(box(C0, 500, 500, 380, 30) - box(C0, 500, 490, 370, 26), 0.03)
    p.part(box(C0, 500, 540, 50, 10), z=0.32, lift=0.05, bevel=8, mat="gilt")
    p.part(box(C0, 500, 50, 420, 10), z=0.32, lift=0.05, bevel=8, mat="gilt")
    p.part(circle(C0, 500, 56), z=0.38, lift=0.06, bevel=14, mat="gilt")
    return p


@piece("LanternCrimsonGlass")
def lantern():
    p = P(3021)
    medallion(p, "effects")
    p.part(sub(circle(C0, 220, 60), circle(C0, 220, 36)), z=0.32, lift=0.05, bevel=8, mat="iron")
    p.part(poly([(C0 - 120, 330), (C0 + 120, 330), (C0 + 60, 260), (C0 - 60, 260)]), z=0.30, lift=0.08, bevel=14, mat="iron")
    p.flat(box(C0, 500, 200, 300, 20), 0.26, "crimson_enamel")
    p.custom(ellipse(C0, 520, 34, 70), 0.34 + 0 * xx, "flame")
    for sg in (-1, 1):
        p.part(box(C0 + sg * 110, 500, 24, 330, 6), z=0.32, lift=0.06, bevel=8, mat="iron")
    p.part(box(C0, 340, 260, 30, 8), z=0.32, lift=0.05, bevel=8, mat="iron")
    p.part(box(C0, 680, 280, 50, 14), z=0.32, lift=0.06, bevel=12, mat="iron")
    return p


@piece("UmbrellaBatWing")
def umbrella():
    p = P(3022)
    medallion(p, "effects")
    canopy = sub(poly(bez((200, 470), (240, 220), (784, 220), (824, 470)) + [(824, 470)] +
                      [(824 - k * 78, 470 - (30 if k % 2 else 0)) for k in range(1, 8)] + [(200, 470)]),
                 circle(-100, -100, 1))
    p.part(canopy, z=0.24, lift=0.14, bevel=30, mat="leather_black")
    for k in range(1, 4):
        p.groove(seg(C0, 250, 200 + k * 156, 470, 6), 0.04)
    p.part(seg(C0, 250, C0, 760, 18), z=0.30, lift=0.04, bevel=8, mat="silver")
    p.part(sub(circle(C0 - 50, 760, 50), circle(C0 - 50, 760, 30), box(C0 - 50, 730, 120, 60)), z=0.30, lift=0.04, bevel=8, mat="silver")
    return p


@piece("ThermosRaven")
def thermos():
    p = P(3023)
    medallion(p, "effects")
    p.part(box(C0, 520, 220, 460, 60), z=0.22, lift=0.12, bevel=30, mat="ink")
    p.part(box(C0, 270, 240, 90, 24), z=0.30, lift=0.08, bevel=14, mat="silver")
    p.part(box(C0, 760, 240, 40, 14), z=0.30, lift=0.05, bevel=10, mat="silver")
    raven = U(ellipse(C0, 520, 60, 90, 20), circle(C0 - 30, 440, 36), poly([(C0 - 60, 430), (C0 - 110, 440), (C0 - 60, 450)]),
              poly([(C0 + 30, 560), (C0 + 90, 650), (C0 + 40, 600)]))
    p.part(raven, z=0.30, lift=0.05, bevel=8, mat="silver")
    return p


def phone(p, screen="moon_dark"):
    p.part(box(C0, 480, 330, 600, 50), z=0.22, lift=0.10, bevel=26, mat="leather_black")
    p.flat(box(C0, 470, 280, 500, 26), 0.30, screen)
    p.part(circle(C0, 745, 18), z=0.32, lift=0.03, bevel=8, mat="silver")


@piece("PhoneWallpapers")
def phone_wall():
    p = P(3031)
    medallion(p, "effects")
    phone(p, "blue_enamel")
    p.part(crescent(C0, 400, 90, 0.4, -40), z=0.36, lift=0.04, bevel=8, mat="moon")
    for k in range(6):
        p.part(star(C0 - 90 + (k * 53) % 180, 560 + (k * 37) % 120, 14, 6, 4), z=0.34, lift=0.03, bevel=4, mat="silver")
    return p


@piece("PhoneCase")
def phone_case():
    p = P(3032)
    medallion(p, "effects")
    p.part(box(C0, 480, 330, 600, 50), z=0.22, lift=0.10, bevel=26, mat="crimson_enamel")
    p.groove(box(C0, 480, 290, 560, 40) - box(C0, 480, 280, 550, 36), 0.03)
    crest_shield(p, C0, 480, 170, 210, face="ink", z=0.30)
    p.part(box(C0 - 90, 230, 90, 90, 22), z=0.30, lift=0.05, bevel=10, mat="iron")
    return p


@piece("PhoneRingtones")
def phone_ring():
    p = P(3033)
    medallion(p, "effects")
    bell = poly(bez((C0 - 170, 640), (C0 - 150, 380), (C0 - 120, 270), (C0, 260)) + bez((C0, 260), (C0 + 120, 270), (C0 + 150, 380), (C0 + 170, 640)))
    p.part(bell, z=0.24, lift=0.14, bevel=30, mat="brass")
    p.part(box(C0, 650, 400, 50, 22), z=0.30, lift=0.06, bevel=12, mat="brass")
    p.part(circle(C0, 710, 40), z=0.32, lift=0.06, bevel=14, mat="brass")
    for k in range(3):
        for sg in (-1, 1):
            r = 230 + k * 50
            pts = [(C0 + sg * r * math.cos(math.radians(a)), 470 + r * math.sin(math.radians(a))) for a in range(-35, 36, 7)]
            if sg < 0:
                pts = [(2 * C0 - x, y) for x, y in pts]
            p.part(polyline(pts, 14), z=0.30, lift=0.03, bevel=6, mat="gilt")
    return p


@piece("DecorGothicStudy")
def decor_study():
    p = P(3041)
    medallion(p, "effects")
    p.part(box(C0, 640, 560, 50, 10), z=0.24, lift=0.06, bevel=10, mat="oak")
    for sg in (-1, 1):
        p.part(box(C0 + sg * 240, 730, 40, 140, 8), z=0.22, lift=0.05, bevel=8, mat="oak")
    for k, (mat, hgt) in enumerate((("leather", 200), ("ink", 170), ("leather_black", 220), ("green_enamel", 180))):
        p.part(box(C0 - 200 + k * 50, 615 - hgt / 2, 44, hgt, 6), z=0.26, lift=0.06, bevel=8, mat=mat)
    p.part(box(C0 + 160, 580, 50, 90, 10), z=0.28, lift=0.06, bevel=10, mat="wax")
    p.custom(ellipse(C0 + 160, 510, 16, 30), 0.34 + 0 * xx, "flame")
    return p


@piece("DecorMoonlitLoft")
def decor_loft():
    p = P(3042)
    medallion(p, "effects")
    arch = U(box(C0, 540, 360, 360, 10), circle(C0, 360, 180))
    p.part(arch, z=0.20, lift=0.10, bevel=24, mat="iron")
    inner = U(box(C0, 540, 300, 320, 8), circle(C0, 360, 150))
    p.flat(inner, 0.26, "blue_enamel")
    p.part(seg(C0, 210, C0, 700, 16), z=0.30, lift=0.04, bevel=6, mat="iron")
    p.part(seg(C0 - 150, 470, C0 + 150, 470, 16), z=0.30, lift=0.04, bevel=6, mat="iron")
    p.part(circle(C0 + 70, 350, 54), z=0.32, lift=0.06, bevel=14, mat="moon")
    return p


@piece("DecorCrimsonCourt")
def decor_court():
    p = P(3043)
    medallion(p, "effects")
    back = poly(bez((C0 - 170, 600), (C0 - 200, 300), (C0 - 120, 200), (C0, 220)) + bez((C0, 220), (C0 + 120, 200), (C0 + 200, 300), (C0 + 170, 600)))
    p.part(back, z=0.22, lift=0.12, bevel=30, mat="gilt")
    p.flat(poly(inset_pts(bez((C0 - 170, 600), (C0 - 200, 300), (C0 - 120, 200), (C0, 220)) + bez((C0, 220), (C0 + 120, 200), (C0 + 200, 300), (C0 + 170, 600)), C0, 420, 0.82)), 0.30, "crimson_enamel")
    for k in range(3):
        for j in range(3):
            p.part(circle(C0 - 70 + k * 70, 320 + j * 90, 10), z=0.34, lift=0.03, bevel=5, mat="gilt")
    p.part(box(C0, 640, 440, 90, 30), z=0.26, lift=0.10, bevel=24, mat="crimson_enamel")
    for sg in (-1, 1):
        p.part(box(C0 + sg * 190, 740, 30, 120, 10), z=0.24, lift=0.05, bevel=8, mat="gilt")
    return p


@piece("GearTint")
def gear_tint():
    p = P(3051)
    medallion(p, "effects")
    fist = U(box(C0 - 40, 460, 300, 260, 90), box(C0 + 120, 520, 120, 150, 50))
    p.part(fist, z=0.24, lift=0.12, bevel=40, mat="ivory")
    for k in range(4):
        p.part(box(C0 - 40, 360 + k * 62, 320, 44, 16), z=0.30, lift=0.06, bevel=14, mat="leather")
    for k, mat in enumerate(("crimson_enamel", "gold_enamel", "blue_enamel", "green_enamel")):
        p.part(circle(C0 - 150 + k * 100, 740, 34), z=0.30, lift=0.08, bevel=14, mat=mat)
    return p


# ================================================================ moments
def tower(p):
    t = U(box(C0, 740, 160, 260, 4), poly([(C0 - 100, 610), (C0, 470), (C0 + 100, 610)]))
    p.part(t, z=0.22, lift=0.06, bevel=10, mat="iron")
    p.part(box(C0, 690, 50, 70, 25), z=0.28, lift=0.03, bevel=6, mat="flame")


@piece("MomentLanternRelease")
def moment_lanterns():
    p = P(4001)
    medallion(p, "moment")
    for k, (x, y, s) in enumerate(((C0 - 170, 520, 1.0), (C0, 380, 1.2), (C0 + 180, 520, 1.0), (C0 - 90, 680, 0.8), (C0 + 100, 690, 0.8), (C0 + 60, 250, 0.7))):
        body = box(x, y, 110 * s, 140 * s, 34 * s)
        p.part(body, z=0.24 + 0.02 * k, lift=0.08, bevel=20, mat="parchment")
        p.custom(ellipse(x, y + 10 * s, 30 * s, 44 * s), 0.30 + 0.02 * k + 0 * xx, "flame")
    return p


@piece("MomentCrimsonFireworks")
def moment_fireworks():
    p = P(4002)
    medallion(p, "moment")
    for (cx, cy, r, mat) in ((C0 - 140, 330, 130, "crimson_enamel"), (C0 + 150, 300, 110, "gold_enamel"), (C0 + 20, 480, 90, "crimson_enamel")):
        for k in range(12):
            a = math.radians(k * 30)
            p.part(seg(cx + 0.3 * r * math.cos(a), cy + 0.3 * r * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a), 14), z=0.30, lift=0.05, bevel=6, mat=mat)
            p.part(circle(cx + r * math.cos(a), cy + r * math.sin(a), 12), z=0.32, lift=0.05, bevel=6, mat="gilt")
    tower(p)
    return p


@piece("MomentShoutout")
def moment_shoutout():
    p = P(4003)
    medallion(p, "moment")
    scroll = U(box(C0 + 40, 520, 420, 240, 20), circle(C0 - 170, 520, 70), circle(C0 + 250, 520, 70))
    p.part(scroll, z=0.22, lift=0.10, bevel=24, mat="parchment")
    for k in range(4):
        p.groove(seg(C0 - 100, 450 + k * 46, C0 + 190, 450 + k * 46, 8), 0.03)
    bell = poly(bez((C0 - 90, 380), (C0 - 80, 250), (C0 - 50, 200), (C0, 200)) + bez((C0, 200), (C0 + 50, 200), (C0 + 80, 250), (C0 + 90, 380)))
    p.part(bell, z=0.32, lift=0.12, bevel=24, mat="brass")
    p.part(circle(C0, 395, 22), z=0.36, lift=0.05, bevel=8, mat="brass")
    return p


# ================================================================ gamepasses (laurel wreath round the medallion)
@piece("PassExtraStudents")
def pass_students():
    p = P(5001)
    medallion(p, "pass", wreath=True)
    for k, (x, mat) in enumerate(((C0 - 130, "silver"), (C0 + 130, "gilt"))):
        p.part(box(x, 640, 170, 70, 14), z=0.26, lift=0.08, bevel=16, mat="iron")    # the plinths of the slot picker
        fig = U(circle(x, 370, 52), box(x, 500, 120, 190, 46))
        p.part(fig, z=0.30, lift=0.12, bevel=26, mat=mat)
    count_plate(p, "+2", y=760, w=150)
    return p


@piece("PassTailor")
def pass_tailor():
    p = P(5002)
    medallion(p, "pass", wreath=True)
    pivot = (C0, 470)
    for sg in (-1, 1):   # two tapered steel blades crossing at the pivot, ring handles below
        a = math.radians(-90 + sg * 22)
        tip = (C0 + 300 * math.cos(a), 470 + 300 * math.sin(a))
        nx, ny = -math.sin(a), math.cos(a)
        blade = poly([(C0 + nx * 26, 470 + ny * 26), (tip[0], tip[1]), (C0 - nx * 26, 470 - ny * 26)])
        p.part(blade, z=0.30 + 0.02 * (sg > 0), lift=0.08, bevel=10, mat="steel")
        ha = math.radians(90 - sg * 26)
        hx, hy = C0 + 170 * math.cos(ha), 470 + 170 * math.sin(ha)
        p.part(seg(C0, 470, hx, hy, 30), z=0.30, lift=0.06, bevel=10, mat="gilt")
        p.part(sub(circle(hx, hy + 40, 64), circle(hx, hy + 40, 38)), z=0.30, lift=0.08, bevel=12, mat="gilt")
    p.part(circle(C0, 470, 24), z=0.38, lift=0.05, bevel=8, mat="brass")
    tape = [(C0 - 300 + k * 30, 300 + 50 * math.sin(k * 0.55)) for k in range(21)]
    p.part(polyline(tape, 28), z=0.24, lift=0.04, bevel=8, mat="gold_enamel")
    for k in range(0, 21, 2):
        x, y = tape[k]
        p.groove(seg(x, y - 10, x, y + 4, 4), 0.03)
    return p


@piece("PassCollectorsDorm")
def pass_dorm():
    p = P(5003)
    medallion(p, "pass", wreath=True)
    for y in (420, 620):
        p.part(box(C0, y, 480, 30, 8), z=0.24, lift=0.05, bevel=8, mat="oak")
    for k in range(4):    # trophies on the shelves (a skull is out: crests, cups and fangs)
        x = C0 - 165 + k * 110
        p.part(poly([(x - 34, 405), (x + 34, 405), (x + 46, 330), (x - 46, 330)]), z=0.28, lift=0.08, bevel=12, mat="gilt")
        p.part(box(x, 300, 90, 20, 8), z=0.28, lift=0.04, bevel=6, mat="gilt")
        crest_shield(p, x, 545, 80, 100, face=("crimson_enamel", "blue_enamel", "green_enamel", "gold_enamel")[k], z=0.26)
    key = U(sub(circle(C0 - 90, 720, 40), circle(C0 - 90, 720, 22)), box(C0 + 20, 720, 190, 22, 6), box(C0 + 90, 742, 22, 40, 4), box(C0 + 50, 742, 22, 30, 4))
    p.part(key, z=0.30, lift=0.06, bevel=8, mat="brass")
    return p


@piece("PassGothicEmotes")
def pass_emotes():
    p = P(5004)
    medallion(p, "pass", wreath=True)
    # two masquerade masks: one smiling (ivory), one sorrowful (crimson), on a gilt ribbon
    def mask(cx, cy, rot, mat, happy):
        face = ellipse(cx, cy, 120, 150, rot)
        p.part(face, z=0.26, lift=0.14, bevel=36, mat=mat)
        r = math.radians(rot)
        def at(dx, dy):
            return cx + dx * math.cos(r) - dy * math.sin(r), cy + dx * math.sin(r) + dy * math.cos(r)
        for sg in (-1, 1):
            ex, ey = at(sg * 48, -40)
            p.recess(ellipse(ex, ey, 30, 18, rot + sg * (12 if happy else -12)), 0.10, 8, mat="ink")
        mx, my = at(0, 70)
        mouth = sub(ellipse(mx, my - (0 if happy else -30), 60, 40, rot), ellipse(mx, my - (22 if happy else -8), 64, 36, rot))
        p.recess(mouth, 0.08, 6, mat="ink")
    mask(C0 - 110, 470, -14, "crimson_enamel", False)
    mask(C0 + 110, 450, 12, "ivory", True)
    ribbon = [(C0 - 280 + k * 28, 640 + 30 * math.sin(k * 0.6)) for k in range(21)]
    p.part(polyline(ribbon, 22), z=0.32, lift=0.04, bevel=8, mat="gilt")
    return p


@piece("PassGramophone")
def pass_gramophone():
    p = P(5005)
    medallion(p, "pass", wreath=True)
    p.part(box(C0 - 40, 640, 300, 140, 16), z=0.24, lift=0.10, bevel=24, mat="oak")
    p.part(ellipse(C0 - 40, 560, 160, 30), z=0.30, lift=0.04, bevel=8, mat="ink")
    p.part(seg(C0 - 20, 560, C0 + 80, 420, 22), z=0.32, lift=0.04, bevel=8, mat="brass")
    horn = poly(bez((C0 + 60, 440), (C0 + 120, 380), (C0 + 160, 260), (C0 + 260, 200)) + [(C0 + 300, 330)] +
                bez((C0 + 300, 330), (C0 + 230, 340), (C0 + 150, 400), (C0 + 90, 460)))
    p.part(horn, z=0.30, lift=0.14, bevel=30, mat="gilt")
    p.flat(ellipse(C0 + 280, 265, 30, 70, -30), 0.40, "ink")
    for k in range(2):   # notes
        x = C0 - 200 + k * 90
        p.part(U(circle(x, 360 + k * 30, 22), seg(x + 18, 360 + k * 30, x + 18, 260 + k * 30, 10)), z=0.32, lift=0.04, bevel=6, mat="gilt")
    return p


@piece("PassPrefectsSeal")
def pass_prefect():
    p = P(5006)
    medallion(p, "pass", wreath=True)
    blob = circle(C0, 480, 210)
    th = np.arctan2(yy - 480, xx - C0)
    blob = np.clip(210 + 14 * np.cos(th * 9) - np.hypot(xx - C0, yy - 480) + 0.5, 0, 1).astype(f32)    # a wax puddle
    p.part(blob, z=0.24, lift=0.14, bevel=40, mat="wax_red")
    p.recess(circle(C0, 480, 150), 0.06, 20)
    for sg in (-1, 0, 1):    # a crown over a crescent: the Prefect's mark
        x = C0 + sg * 60
        hgt = 90 if sg == 0 else 60
        p.emboss(poly([(x - 26, 440), (x + 26, 440), (x, 440 - hgt)]), 0.06, 8)
    p.emboss(box(C0, 450, 170, 26, 8), 0.06, 8)
    p.emboss(crescent(C0, 540, 50, 0.4, -90), 0.06, 8)
    for sg in (-1, 1):   # ribbon tails
        p.part(poly([(C0 + sg * 60, 650), (C0 + sg * 150, 650), (C0 + sg * 190, 800), (C0 + sg * 140, 770), (C0 + sg * 100, 800)]), z=0.20, lift=0.06, bevel=12, mat="leather")
    return p


@piece("NightSociety")
def night_society():
    p = P(6001)
    medallion(p, "society", wreath=True)
    p.part(crescent(C0, 450, 230, 0.42, -40), z=0.24, lift=0.14, bevel=26, mat="moon")
    raven = U(ellipse(C0 + 30, 470, 90, 130, 25), circle(C0 - 20, 350, 56), poly([(C0 - 70, 340), (C0 - 150, 360), (C0 - 70, 380)]),
              poly([(C0 + 70, 540), (C0 + 170, 680), (C0 + 90, 610)]), poly([(C0 + 60, 420), (C0 + 220, 380), (C0 + 120, 500)]))
    p.part(raven, z=0.32, lift=0.10, bevel=18, mat="leather_black")
    p.part(circle(C0 - 30, 345, 10), z=0.40, lift=0.02, bevel=4, mat="gilt")
    p.part(U(sub(circle(C0 - 30, 690, 40), circle(C0 - 30, 690, 22)), box(C0 + 50, 690, 140, 22, 6), box(C0 + 100, 710, 22, 40, 4)), z=0.34, lift=0.05, bevel=8, mat="silver")
    return p


if __name__ == "__main__":
    want = sys.argv[1:]
    info = []
    for name, fn in PIECES.items():
        if want and name not in want:
            continue
        info.append(fn())
    old = {}
    pj = MAPS / "pieces.json"
    if pj.exists() and want:
        old = {d["name"]: d for d in json.loads(pj.read_text())}
    for d in info:
        old[d["name"]] = d
    pj.write_text(json.dumps(list(old.values()), indent=1))
    print(len(info), "pieces ->", MAPS)
