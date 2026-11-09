"""Printed atlas for props batch 43, the gym kit. System Python (PIL + numpy):

  python art/props/gym_atlas.py

GymPrint  the five house crests (Crimson, Ravens, Rovers, Vigil, Wardens) on one shield shape, the Athletes' pennant, the school
          crest, a stopwatch dial, the coach's team sheet, a chalked lap slate, the house points header and its digit tiles, the
          archery target face, enamel signs (SWEATBOX, FIRST AID, HOUSE KIT), a thermometer scale, the fencing scoring dial

Writes art/props/textures/GymPrint_{color,gilt,height}.png (4096; bake sources only, not uploaded) and art/props/gym_atlas.json
(every region's UV rect, v up, and the shield outline the Blender side cuts its crests to). Uses dorm_atlas.py's Cell / Atlas
machinery. All names, text and designs are original.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dorm_atlas as D
from dorm_atlas import Cell, Atlas, crest, scribble, handwriting, swatch, seed_of, fleuron, rules, INK, CRIMSON, GILT, PARCH

HERE = D.HERE
D.FONTS.update({"blk": D.F + "ariblk.ttf", "cons": D.F + "consolab.ttf", "bahn": D.F + "bahnschrift.ttf", "impact": D.F + "impact.ttf"})
SS = D.SS
BONE = (214, 200, 168)
CHALK = (222, 220, 210)

# the shield, in units of its height (x across, y down from the top), shared with the Blender side
SHIELD = [(-0.42, 0.0), (0.42, 0.0), (0.42, 0.46), (0.36, 0.66), (0.24, 0.83), (0.0, 1.0), (-0.24, 0.83), (-0.36, 0.66), (-0.42, 0.46)]

HOUSES = {
    #          field              second (quarter)    charge colour     motto
    "Crimson": ((112, 14, 28), (60, 8, 16), GILT, "SANGUIS ET ROSA"),
    "Ravens": ((58, 30, 92), (30, 16, 52), (226, 220, 236), "NOX ALAS DAT"),
    "Rovers": ((30, 74, 44), (16, 40, 24), BONE, "ULTRA TUMULUM"),
    "Vigil": ((22, 24, 46), (12, 12, 26), GILT, "LUX IN TENEBRIS"),
    "Wardens": ((78, 80, 86), (128, 58, 28), (206, 206, 210), "FERRO CUSTODIMUS"),
}


def shield_pts(cx, top, h, k, inset=0.0):
    out = []
    for u, v in SHIELD:
        uu = u * (1 - inset * 2.2)
        vv = inset + v * (1 - inset * 2.1)
        out.append(((cx + uu * h) * k, (top + vv * h) * k))
    return out


# ------------------------------------------------------------------ the house charges (drawn in a box cx, cy, s)

def ch_rose(d, k, cx, cy, s):
    """A thorned rose: five round petals round a boss, a thorny stem with two leaves below."""
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        x, y, r = cx + math.cos(a) * s * 0.17, cy - s * 0.12 + math.sin(a) * s * 0.17, s * 0.15
        d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
    for i in range(5):
        a = -math.pi / 2 + (i + 0.5) * 2 * math.pi / 5
        d.line([(cx * k, (cy - s * 0.12) * k), ((cx + math.cos(a) * s * 0.33) * k, (cy - s * 0.12 + math.sin(a) * s * 0.33) * k)], fill=0,
               width=int(0.025 * s * k))
    r = s * 0.075
    d.ellipse([(cx - r) * k, (cy - s * 0.12 - r) * k, (cx + r) * k, (cy - s * 0.12 + r) * k], fill=0)
    r = s * 0.04
    d.ellipse([(cx - r) * k, (cy - s * 0.12 - r) * k, (cx + r) * k, (cy - s * 0.12 + r) * k], fill=255)
    d.line([(cx * k, (cy + 0.02 * s) * k), (cx * k, (cy + 0.42 * s) * k)], fill=255, width=int(0.045 * s * k))
    for j, sy in enumerate((0.12, 0.22, 0.32)):
        side = -1 if j % 2 else 1
        d.polygon([(cx * k, (cy + sy * s) * k), ((cx + side * 0.08 * s) * k, (cy + (sy - 0.03) * s) * k),
                   (cx * k, (cy + (sy + 0.03) * s) * k)], fill=255)
    for side, sy in ((-1, 0.18), (1, 0.28)):
        d.polygon([(cx * k, (cy + sy * s) * k), ((cx + side * 0.12 * s) * k, (cy + (sy - 0.09) * s) * k),
                   ((cx + side * 0.25 * s) * k, (cy + (sy - 0.06) * s) * k), ((cx + side * 0.13 * s) * k, (cy + (sy + 0.02) * s) * k)], fill=255)


def ch_raven(d, k, cx, cy, s):
    """A raven in profile with its wings raised."""
    P = [(-0.36, 0.05), (-0.2, -0.02), (-0.1, -0.1), (-0.04, -0.2), (0.02, -0.34), (0.12, -0.42), (0.1, -0.28), (0.2, -0.38), (0.22, -0.18),
         (0.16, -0.04), (0.24, 0.0), (0.34, -0.02), (0.42, 0.02), (0.32, 0.05), (0.24, 0.1), (0.14, 0.18), (0.08, 0.3), (0.0, 0.38),
         (-0.06, 0.3), (-0.02, 0.22), (-0.14, 0.14), (-0.3, 0.1)]
    d.polygon([((cx + u * s) * k, (cy + v * s) * k) for u, v in P], fill=255)
    r = 0.018 * s
    d.ellipse([(cx + 0.29 * s - r) * k, (cy + 0.0 * s - r) * k, (cx + 0.29 * s + r) * k, (cy + 0.0 * s + r) * k], fill=0)
    for u in (-0.04, 0.06):
        d.line([((cx + u * s) * k, (cy + 0.34 * s) * k), ((cx + (u - 0.03) * s) * k, (cy + 0.45 * s) * k)], fill=255, width=int(0.02 * s * k))


def ch_grave(d, k, cx, cy, s):
    """A grave cross on its mound with a ball at its foot."""
    w = 0.07 * s
    d.rectangle([(cx - w) * k, (cy - 0.4 * s) * k, (cx + w) * k, (cy + 0.25 * s) * k], fill=255)
    d.rectangle([(cx - 0.24 * s) * k, (cy - 0.24 * s) * k, (cx + 0.24 * s) * k, (cy - 0.12 * s) * k], fill=255)
    r = 0.13 * s
    d.ellipse([(cx - r) * k, (cy - 0.18 * s - r) * k, (cx + r) * k, (cy - 0.18 * s + r) * k], outline=255, width=int(0.04 * s * k))
    d.chord([(cx - 0.4 * s) * k, (cy + 0.2 * s) * k, (cx + 0.4 * s) * k, (cy + 0.5 * s) * k], 180, 360, fill=255)
    r = 0.09 * s
    bx, by = cx + 0.24 * s, cy + 0.2 * s
    d.ellipse([(bx - r) * k, (by - r) * k, (bx + r) * k, (by + r) * k], fill=255)
    d.line([((bx - r) * k, by * k), ((bx + r) * k, by * k)], fill=0, width=int(0.015 * s * k))
    d.arc([(bx - r * 0.5) * k, (by - r) * k, (bx + r * 0.5) * k, (by + r) * k], 0, 360, fill=0, width=int(0.015 * s * k))


def ch_candle(d, k, cx, cy, s):
    """A candle in a pricket holder, the flame with a halo of rays."""
    d.rectangle([(cx - 0.07 * s) * k, (cy - 0.12 * s) * k, (cx + 0.07 * s) * k, (cy + 0.3 * s) * k], fill=255)
    d.polygon([((cx - 0.26 * s) * k, (cy + 0.3 * s) * k), ((cx + 0.26 * s) * k, (cy + 0.3 * s) * k), ((cx + 0.1 * s) * k, (cy + 0.38 * s) * k),
               ((cx + 0.14 * s) * k, (cy + 0.46 * s) * k), ((cx - 0.14 * s) * k, (cy + 0.46 * s) * k), ((cx - 0.1 * s) * k, (cy + 0.38 * s) * k)], fill=255)
    d.polygon([(cx * k, (cy - 0.36 * s) * k), ((cx + 0.06 * s) * k, (cy - 0.22 * s) * k), (cx * k, (cy - 0.15 * s) * k),
               ((cx - 0.06 * s) * k, (cy - 0.22 * s) * k)], fill=255)
    for i in range(10):
        a = i * 2 * math.pi / 10
        x0, y0 = cx + math.cos(a) * 0.14 * s, cy - 0.24 * s + math.sin(a) * 0.14 * s
        x1, y1 = cx + math.cos(a) * 0.24 * s, cy - 0.24 * s + math.sin(a) * 0.24 * s
        d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=255, width=int(0.02 * s * k))


def ch_shield(d, k, cx, cy, s):
    """The Wardens' charge: a small studded heater shield crossed by two keys' wards."""
    pts = [(cx + u * s * 0.62, cy - 0.32 * s + v * s * 0.62) for u, v in SHIELD]
    d.polygon([(x * k, y * k) for x, y in pts], fill=255)
    pin = [(cx + u * s * 0.46, cy - 0.25 * s + v * s * 0.46) for u, v in SHIELD]
    d.polygon([(x * k, y * k) for x, y in pin], fill=0)
    d.rectangle([(cx - 0.035 * s) * k, (cy - 0.3 * s) * k, (cx + 0.035 * s) * k, (cy + 0.25 * s) * k], fill=255)
    d.rectangle([(cx - 0.2 * s) * k, (cy - 0.1 * s) * k, (cx + 0.2 * s) * k, (cy - 0.03 * s) * k], fill=255)
    for u, v in ((-0.14, -0.2), (0.14, -0.2), (-0.14, 0.08), (0.14, 0.08)):
        r = 0.03 * s
        d.ellipse([(cx + u * s - r) * k, (cy + v * s - r) * k, (cx + u * s + r) * k, (cy + v * s + r) * k], fill=255)


CHARGE = {"Crimson": ch_rose, "Ravens": ch_raven, "Rovers": ch_grave, "Vigil": ch_candle, "Wardens": ch_shield}


def house_crest(house):
    """The house shield filling the cell (the Blender side cuts the geometry to SHIELD): field per pale, a gilt rim, the charge and
    a motto scroll at the foot."""
    W, H = 420, 500
    field, second, chg, motto = HOUSES[house]
    c = Cell(W, H, field, grain=5, seed=seed_of(house))
    h = H
    c.shape(lambda d, k: d.polygon(shield_pts(W / 2, 0, h, k), fill=255), GILT)
    c.shape(lambda d, k: d.polygon(shield_pts(W / 2, 0, h, k, 0.035), fill=255), field, height=140)
    # per pale: the right half in the second colour (the Wardens' rust half, the darker field for the others)
    def half(d, k):
        m = Image.new("L", (W * k, H * k), 0)
        ImageDraw.Draw(m).polygon(shield_pts(W / 2, 0, h, k, 0.035), fill=255)
        d.bitmap((0, 0), m)
        d.rectangle([0, 0, W / 2 * k, H * k], fill=0)
    c.shape(half, second, height=140)
    c.shape(lambda d, k: d.line([(W / 2 * k, 0.14 * H * k), (W / 2 * k, 0.97 * H * k)], fill=255, width=int(5 * k)), GILT)
    c.shape(lambda d, k: CHARGE[house](d, k, W / 2, H * 0.42, H * 0.62), chg, height=180)
    c.text(motto, "pala", W / 2, H * 0.08 + 6, W * 0.62, 22, colour=GILT)
    return c


def pennant():
    """The Athletes' pennant: VARSITY in bone on their blue, a laurel, a crimson border."""
    W, H = 700, 260
    c = Cell(W, H, (36, 74, 128), grain=5, seed=4301)
    c.shape(lambda d, k: d.rectangle([8 * k, 8 * k, (W - 8) * k, (H - 8) * k], outline=255, width=int(10 * k)), (110, 16, 28))
    c.text("VARSITY", "blk", W / 2 + 70, H / 2 - 10, W - 280, 120, colour=(236, 228, 210))
    c.text("THE ATHLETES  -  NIGHTMARE HIGH", "pala", W / 2 + 40, H - 46, W - 260, 30, colour=GILT)

    def laurel(d, k):
        for side in (-1, 1):
            for i in range(6):
                a = math.pi / 2 + side * (0.4 + i * 0.32)
                x, y = 95 + math.cos(a) * 55, H / 2 + math.sin(a) * 55
                d.ellipse([(x - 13) * k, (y - 7) * k, (x + 13) * k, (y + 7) * k], fill=255)
    c.shape(laurel, GILT)
    return c


def school_crest():
    W, H = 400, 440
    c = Cell(W, H, (20, 18, 26), grain=3, seed=4302)
    crest(c, W / 2, H / 2, 380)
    return c


def stopwatch_dial():
    """A white enamel dial: 60 seconds in fifths, a minute sub-dial, the maker's name (invented), a hairline crack."""
    W = H = 700
    c = Cell(W, H, (232, 226, 210), grain=3, seed=4303, vignette=0.12)
    cx, cy, R = W / 2, H / 2, W / 2 - 6

    def ticks(d, k):
        for i in range(300):
            a = i / 300 * 2 * math.pi - math.pi / 2
            L = 34 if i % 25 == 0 else 20 if i % 5 == 0 else 9
            wd = 4.5 if i % 25 == 0 else 2.2 if i % 5 == 0 else 1.0
            r0, r1 = R - 18 - L, R - 18
            d.line([((cx + math.cos(a) * r0) * k, (cy + math.sin(a) * r0) * k), ((cx + math.cos(a) * r1) * k, (cy + math.sin(a) * r1) * k)],
                   fill=255, width=max(1, int(wd * k)))
    c.shape(ticks, INK)
    c.shape(lambda d, k: d.ellipse([(cx - R + 8) * k, (cy - R + 8) * k, (cx + R - 8) * k, (cy + R - 8) * k], outline=255, width=int(4 * k)), INK)
    for i in range(12):
        a = (i + 1) / 12 * 2 * math.pi - math.pi / 2
        r = R - 92
        col = CRIMSON if (i + 1) % 3 == 0 else INK
        c.text(str((i + 1) * 5), "pala", cx + math.cos(a) * r, cy + math.sin(a) * r, 70, 46, colour=col)
    sx, sy, sr = cx, cy + 128, 70
    c.shape(lambda d, k: d.ellipse([(sx - sr) * k, (sy - sr) * k, (sx + sr) * k, (sy + sr) * k], outline=255, width=int(3 * k)), INK)

    def sub(d, k):
        for i in range(30):
            a = i / 30 * 2 * math.pi - math.pi / 2
            L = 12 if i % 5 == 0 else 6
            d.line([((sx + math.cos(a) * (sr - L)) * k, (sy + math.sin(a) * (sr - L)) * k), ((sx + math.cos(a) * sr) * k, (sy + math.sin(a) * sr) * k)],
                   fill=255, width=int(2 * k))
    c.shape(sub, INK)
    c.text("GRAVESEND & THORNE", "pala", cx, cy - 120, 300, 26, colour=INK)
    c.text("split seconds", "palai", cx, cy - 88, 200, 22, colour=CRIMSON)
    c.shape(lambda d, k: d.line([((cx + 120) * k, (cy - 250) * k), ((cx + 165) * k, (cy - 170) * k), ((cx + 150) * k, (cy - 120) * k)],
                                fill=255, width=int(1.5 * k)), (150, 140, 120))
    return c


SHEET = [("1", "R. Thorne (capt.)", "Ravens"), ("2", "J. Blackwood", "Wardens"), ("3", "M. Okafor", "Rovers"), ("4", "S. Vance", "Crimson"),
         ("5", "T. Hale", "Vigil"), ("6", "E. Marlowe", "Ravens"), ("7", "D. Kerrigan", "Wardens"), ("8", "L. Ashdown", "Rovers"),
         ("9", "C. Mortimer", "Crimson"), ("10", "A. Grimsby", "Vigil"), ("11", "N. Fairweather", "Ravens")]


def team_sheet():
    W, H = 640, 860
    c = Cell(W, H, (232, 222, 196), grain=6, seed=4304, vignette=0.2, fibres=True)
    c.text("FIRST ELEVEN", "pala", W / 2, 60, 440, 46, colour=CRIMSON)
    c.text("v. St. Morrow's  -  Saturday, under the floodlamps", "palai", W / 2, 108, 560, 26, colour=INK)
    c.shape(lambda d, k: d.line([(40 * k, 140 * k), ((W - 40) * k, 140 * k)], fill=255, width=int(2.5 * k)), INK)
    for i, (n, name, house) in enumerate(SHEET):
        y = 186 + i * 52
        c.text(n, "hand", 70, y, 50, 36, colour=(28, 34, 78), anchor="rm")
        c.text(name, "hand", 96, y, 330, 36, colour=(28, 34, 78), anchor="lm")
        c.text(house, "hand", W - 60, y, 160, 30, colour=CRIMSON, anchor="rm")
    c.text("Reserves: Pike, Lowell", "hand", 60, 780, 400, 30, colour=(28, 34, 78), anchor="lm")
    scribble(c, W - 260, 820, 200, 34, (28, 34, 78), 4305)
    return c


def lap_slate():
    W, H = 640, 440
    c = Cell(W, H, (34, 40, 40), grain=10, seed=4306, vignette=0.15)
    g = random.Random(4306)
    c.text("LAPS", "printb", W / 2, 52, 200, 54, colour=CHALK)
    for i, name in enumerate(("Thorne", "Okafor", "Vance", "Hale")):
        y = 130 + i * 78
        c.text(name, "print", 40, y, 200, 40, colour=CHALK, anchor="lm")
        n = g.randint(7, 14)

        def tally(d, k, y=y, n=n):
            x = 270
            for j in range(n):
                if j % 5 == 4:
                    d.line([((x - 5 * 14 - 4) * k, (y + 18) * k), ((x - 6) * k, (y - 20) * k)], fill=255, width=int(4 * k))
                    x += 22
                else:
                    jx = g.uniform(-2, 2)
                    d.line([((x + jx) * k, (y - 22) * k), ((x - jx) * k, (y + 22) * k)], fill=255, width=int(4 * k))
                    x += 14
        c.shape(tally, CHALK)
    c.text("best: 4.12", "print", W - 120, H - 40, 200, 30, colour=CHALK)
    return c


def hp_header():
    W, H = 1500, 200
    c = Cell(W, H, (16, 15, 22), grain=3, seed=4307)
    rules(c, 10, GILT, 5)
    c.text("HOUSE  POINTS", "black", W / 2, H / 2 - 4, W - 380, 120, colour=GILT, bold=0.6)
    for x in (90, W - 90):
        fleuron(c, x, H / 2, 40)
    return c


def digit(n):
    W, H = 150, 200
    c = Cell(W, H, (18, 17, 20), grain=3, seed=4310 + n)
    c.shape(lambda d, k: d.line([(6 * k, H / 2 * k), ((W - 6) * k, H / 2 * k)], fill=255, width=int(3 * k)), (6, 6, 8))
    c.text(str(n), "pala", W / 2, H / 2 - 4, W - 30, H - 34, colour=(230, 222, 200))
    return c


def target_face():
    """A target face in the house colours: bone, ink, crimson, violet and a gilt gold, each band split by a fine line, a raven sigil
    in the gold, hits and a few torn holes."""
    W = H = 900
    c = Cell(W, H, (214, 202, 172), grain=6, seed=4320)
    cx, cy = W / 2, H / 2
    bands = [((214, 202, 172), 1.0), ((26, 24, 34), 0.8), ((120, 16, 30), 0.6), ((66, 34, 96), 0.4), (GILT, 0.2)]
    R = W / 2 - 4
    for col, f in bands:
        rr = R * f
        c.shape(lambda d, k, rr=rr: d.ellipse([(cx - rr) * k, (cy - rr) * k, (cx + rr) * k, (cy + rr) * k], fill=255), col if col != GILT else (196, 150, 64))
        rh = R * (f - 0.1)
        c.shape(lambda d, k, rr=rh: d.ellipse([(cx - rr) * k, (cy - rr) * k, (cx + rr) * k, (cy + rr) * k], outline=255, width=int(2 * k)),
                (150, 140, 120) if col != (214, 202, 172) else (60, 56, 60))
    c.shape(lambda d, k: ch_raven(d, k, cx, cy, 120), (26, 22, 30))
    g = random.Random(4321)

    def holes(d, k):
        for _ in range(26):
            a, r = g.uniform(0, 2 * math.pi), abs(g.gauss(0, R * 0.38))
            x, y, q = cx + math.cos(a) * r, cy + math.sin(a) * r, g.uniform(3, 6)
            d.ellipse([(x - q) * k, (y - q) * k, (x + q) * k, (y + q) * k], fill=255)
    c.shape(holes, (20, 16, 12), height=60)
    return c


def enamel_sign(key, lines, bg, fg, W=700, H=240):
    c = Cell(W, H, bg, grain=3, seed=seed_of(key), vignette=0.1)
    c.shape(lambda d, k: d.rounded_rectangle([10 * k, 10 * k, (W - 10) * k, (H - 10) * k], radius=int(26 * k), outline=255, width=int(7 * k)), fg)
    n = len(lines)
    for i, (txt, fk, size) in enumerate(lines):
        y = H / 2 + (i - (n - 1) / 2) * (H * 0.62 / max(1, n))
        c.text(txt, fk, W / 2, y, W - 90, size, colour=fg)
    # chips: rust at the corners and the screw holes
    g = random.Random(seed_of(key))

    def chips(d, k):
        for x, y in ((34, 34), (W - 34, 34), (34, H - 34), (W - 34, H - 34)):
            for _ in range(3):
                q = g.uniform(5, 13)
                ox, oy = g.uniform(-8, 8), g.uniform(-8, 8)
                d.ellipse([(x + ox - q) * k, (y + oy - q) * k, (x + ox + q) * k, (y + oy + q) * k], fill=255)
    c.shape(chips, (34, 28, 26), height=110)
    return c


def thermo_scale():
    W, H = 120, 620
    c = Cell(W, H, (226, 220, 204), grain=3, seed=4330)

    def sc(d, k):
        for i in range(0, 61):
            y = H - 40 - i * (H - 80) / 60
            L = 36 if i % 10 == 0 else 20 if i % 5 == 0 else 12
            d.line([(W - 18 - L) * k, y * k, (W - 18) * k, y * k], fill=255, width=int((2.5 if i % 10 == 0 else 1.3) * k))
    c.shape(sc, INK)
    for i in range(0, 61, 10):
        y = H - 40 - i * (H - 80) / 60
        c.text(str(60 + i * 2), "pala", 34, y, 50, 22, colour=INK)
    zone = H - 40 - 45 * (H - 80) / 60
    c.shape(lambda d, k: d.rectangle([(W - 16) * k, 40 * k, (W - 6) * k, zone * k], fill=255), CRIMSON)
    return c


def fencing_dial():
    W = H = 400
    c = Cell(W, H, (20, 19, 24), grain=2, seed=4340)
    c.text("TOUCHES", "pala", W / 2, 70, 220, 32, colour=GILT)
    for i in range(16):
        a = math.pi * (0.75 + i / 15 * 1.5)
        r = 140
        x, y = W / 2 + math.cos(a) * r, H / 2 + 20 + math.sin(a) * r
        c.shape(lambda d, k, x=x, y=y: d.ellipse([(x - 6) * k, (y - 6) * k, (x + 6) * k, (y + 6) * k], fill=255), (226, 218, 196))
    c.text("0 - 15", "pala", W / 2, H - 60, 120, 30, colour=(226, 218, 196))
    return c


def sauna_sign():
    return enamel_sign("Sauna", [("SWEATBOX", "blk", 92), ("ten minutes - then out", "palai", 36)], (18, 30, 34), (232, 222, 196))


def aid_sign():
    c = enamel_sign("Aid", [("FIRST  AID", "blk", 100), ("the Matron is in the east wing", "palai", 32)], (232, 224, 204), (120, 16, 28), W=760)
    return c


def kit_label():
    W, H = 600, 200
    c = Cell(W, H, (200, 184, 146), grain=9, seed=4350)
    c.shape(lambda d, k: d.rectangle([12 * k, 12 * k, (W - 12) * k, (H - 12) * k], outline=255, width=int(4 * k)), (54, 40, 30))
    m = c.fit("HOUSE KIT", "blk", W - 120, 92)
    c.stamp(m, W / 2, 80, (96, 14, 26))
    c.text("THE GYMNASIUM  -  RETURN AFTER MATCHES", "cons", W / 2, 154, W - 80, 26, colour=(46, 36, 30))
    return c


def pegboard_names():
    """The hook rail's brass name tags (five house abbreviations on bone)."""
    W, H = 900, 120
    c = Cell(W, H, (214, 202, 172), grain=4, seed=4360)
    for i, h in enumerate(HOUSES):
        x = 90 + i * 180
        c.text(h.upper(), "pala", x, H / 2, 160, 50, colour=HOUSES[h][0])
    return c


if __name__ == "__main__":
    a = Atlas("GymPrint")
    for h in HOUSES:
        a.put(f"Crest_{h}", house_crest(h), 1.0)
    a.put("School_Crest", school_crest(), 1.0)
    a.put("Pennant", pennant(), 1.0)
    a.put("Dial", stopwatch_dial(), 1.0)
    a.put("TeamSheet", team_sheet(), 1.0)
    a.put("LapSlate", lap_slate(), 1.0)
    a.put("HP_Header", hp_header(), 1.0)
    for n in range(10):
        a.put(f"Digit_{n}", digit(n), 0.8)
    a.put("Target", target_face(), 1.0)
    a.put("Sign_Sauna", sauna_sign(), 1.0)
    a.put("Sign_Aid", aid_sign(), 1.0)
    a.put("KitLabel", kit_label(), 1.0)
    a.put("Thermo", thermo_scale(), 1.0)
    a.put("FenceDial", fencing_dial(), 1.0)
    a.put("HookTags", pegboard_names(), 1.0)
    for name, col, gr, m in (("black", (16, 15, 18), 2, 0), ("paper", (232, 222, 196), 4, 0), ("bone", BONE, 4, 0), ("crimson", CRIMSON, 4, 0),
                             ("ink", INK, 3, 0), ("slate", (34, 40, 40), 8, 0), ("enamel", (232, 226, 210), 2, 0), ("gilt", GILT, 4, 235),
                             ("ravens", HOUSES["Ravens"][0], 3, 0), ("rovers", HOUSES["Rovers"][0], 3, 0), ("vigil", HOUSES["Vigil"][0], 3, 0),
                             ("wardens", HOUSES["Wardens"][0], 3, 0), ("rust", HOUSES["Wardens"][1], 5, 0), ("blue", (36, 74, 128), 3, 0),
                             ("teal", (18, 30, 34), 2, 0), ("label", (200, 184, 146), 8, 0)):
        a.put(f"Swatch_{name}", swatch(col, gr, seed_of(name), m))
    a.save()
    json.dump({"regions": {"GymPrint": a.reg}, "shield": SHIELD}, open(os.path.join(HERE, "gym_atlas.json"), "w"), indent=0)
