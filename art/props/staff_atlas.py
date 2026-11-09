"""Printed atlas for props batches 35 (the Teachers' Lounge kit) and 36 (the School prop kit). Run with the system Python
(PIL + numpy):

  python art/props/staff_atlas.py

StaffPrint  the chalked duty rota and its name tags, the gradebook's pages, exercise book covers and marked sheets, playing
            cards, the dartboard face and its chalk score slate, staff mug wraps, the biscuit barrel's wrap, the wall map (an
            invented country), a student's slate of sums, sheet music, a blotter, specimen jar labels, the fire bucket wrap,
            the dunce cap, the metronome's scale, swatches

Writes art/props/textures/StaffPrint_{color,gilt,height}.png (4096) and art/props/staff_atlas.json (every region's UV rect
[u0, v0, u1, v1], v up). Built on dorm_atlas.py's Cell / Atlas machinery. Every word and name is invented (the school, the
staff, the students, the map's places); nothing is copied from a real source.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dorm_atlas as D
from dorm_atlas import Cell, Atlas, INK, CRIMSON, REDINK, GILT, PARCH, seed_of, crest, fleuron, rules, lined, scribble

HERE = os.path.dirname(os.path.abspath(__file__))
CHALK = (226, 224, 212)
SLATE = (38, 42, 44)
BONE = (214, 202, 172)
STAFF = ["Mr. Hale", "Miss Vane", "Dr. Crowe", "Mrs. Ashby", "Mr. Thorne", "Mr. Graves"]
PUPILS = ["Ashworth, E.", "Blackwood, T.", "Corvin, M.", "Darrow, L.", "Everleigh, R.", "Fenwick, J.", "Grimsby, A.", "Holloway, S.",
          "Ingram, P.", "Jessop, C.", "Kestrel, N.", "Lowther, B.", "Marsh, D.", "Nightingale, F.", "Orme, H.", "Penhallow, G."]


def chalk_text(c, s, fk, x, y, maxw, maxh, colour=CHALK, angle=0.0, anchor="mm", alpha=0.9, seed=0):
    """Chalk lettering: the glyph mask broken up by grain so the strokes look dragged."""
    m = c.fit(s, fk, maxw, maxh)
    g = np.random.default_rng(seed + len(s))
    a = np.asarray(m, np.float32)
    n = g.uniform(0.35, 1.0, a.shape).astype(np.float32)
    streak = np.asarray(Image.fromarray(np.uint8(g.uniform(0, 255, (max(2, a.shape[0] // 3), max(2, a.shape[1] // 18))))).resize(
        (a.shape[1], a.shape[0]), Image.BICUBIC), np.float32) / 255
    a = a * n * (0.55 + 0.45 * streak)
    c.stamp(Image.fromarray(np.uint8(np.clip(a, 0, 255))), x, y, colour, angle=angle, anchor=anchor, alpha=alpha)


def chalk_line(c, pts, width=3, alpha=0.75, colour=CHALK):
    def dr(d, k):
        d.line([(x * k, y * k) for x, y in pts], fill=int(255 * alpha), width=int(width * k))
    m = Image.new("L", c.c.size, 0)
    dr(ImageDraw.Draw(m), D.SS)
    a = np.asarray(m, np.float32) * np.random.default_rng(len(pts)).uniform(0.4, 1.0, (m.height, m.width))
    c.stamp(Image.fromarray(np.uint8(a)), 0, 0, colour, anchor="lt")


def slate_cell(w, h, seed):
    c = Cell(w, h, SLATE, grain=7, seed=seed)
    g = np.random.default_rng(seed)
    # old chalk wiped off: soft pale clouds
    m = np.zeros((c.h * D.SS, c.w * D.SS), np.float32)
    im = Image.fromarray(np.uint8(g.uniform(0, 255, (6, 9)))).resize((m.shape[1], m.shape[0]), Image.BICUBIC)
    m = np.clip((np.asarray(im, np.float32) - 120) * 0.5, 0, 60)
    c.stamp(Image.fromarray(np.uint8(m)), 0, 0, (150, 152, 150), anchor="lt")
    return c


# ------------------------------------------------------------------ batch 35: the lounge

ROTA_DUTIES = ["Gate", "Corridors", "Refectory", "Chapel", "Night Study", "Dormitories"]
ROTA = [["Hale", "Vane", "Crowe", "Ashby", "Thorne"],
        ["Vane", "Thorne", "Hale", "Graves", "Crowe"],
        ["Crowe", "Ashby", "Graves", "Hale", "Vane"],
        ["Graves", "Hale", "Vane", "Thorne", "Ashby"],
        ["Ashby", "Crowe", "Thorne", "Vane", "Hale"],
        ["Thorne", "Graves", "Ashby", "Crowe", "Graves"]]


def rota():
    W, H = 1500, 1000
    c = slate_cell(W, H, 3501)
    chalk_text(c, "STAFF DUTY ROTA", "printb", W / 2, 62, 900, 70, seed=1)
    chalk_text(c, "Michaelmas term  -  week 7", "print", W / 2, 120, 600, 34, alpha=0.7, seed=2)
    x0, xs = 70, [70, 380, 600, 820, 1040, 1260, 1440]
    y0, rh = 170, 120
    chalk_line(c, [(x0, y0 + 70), (W - 60, y0 + 70)], 4)
    chalk_line(c, [(x0, y0 + 70 + 3), (W - 60, y0 + 70 + 4)], 2, 0.5)
    for i in range(1, 6):
        chalk_line(c, [(xs[i] - 12, y0 + 10), (xs[i] - 10 + (i % 2) * 3, H - 50)], 3, 0.6)
    chalk_text(c, "DUTY", "printb", (xs[0] + xs[1]) / 2 - 20, y0 + 36, 220, 50, seed=3)
    for i, d in enumerate(("MON", "TUE", "WED", "THU", "FRI")):
        chalk_text(c, d, "printb", (xs[i + 1] + xs[i + 2]) / 2 - 10, y0 + 36, 180, 50, seed=10 + i)
    for r, duty in enumerate(ROTA_DUTIES):
        y = y0 + 70 + rh * (r + 0.5) + 6
        chalk_text(c, duty, "print", x0 + 8, y, 280, 46, anchor="lm", seed=20 + r)
        for i, n in enumerate(ROTA[r]):
            chalk_text(c, n, "hand", (xs[i + 1] + xs[i + 2]) / 2 - 10, y + random.Random(r * 7 + i).uniform(-6, 6), 190, 50,
                       angle=random.Random(r * 3 + i).uniform(-3, 3), seed=30 + r * 5 + i)
        if r < 5:
            chalk_line(c, [(x0, y0 + 70 + rh * (r + 1) + 4), (W - 60, y0 + 70 + rh * (r + 1) + 6)], 2, 0.35)
    # a struck-out swap and a note
    chalk_line(c, [(xs[3] + 20, y0 + 70 + rh * 5.5 + 6), (xs[4] - 40, y0 + 70 + rh * 5.5 - 4)], 4, 0.85)
    return c


def tag(name, seed):
    W, H = 360, 150
    c = Cell(W, H, BONE, grain=5, seed=seed, vignette=0.2, fibres=True)
    rules(c, 10, CRIMSON, 4)
    c.shape(lambda d, k: d.ellipse([(24 - 11) * k, (H / 2 - 11) * k, (24 + 11) * k, (H / 2 + 11) * k], fill=255), (60, 50, 40))
    c.text(name, "pala", W / 2 + 16, H / 2, W - 90, 66, colour=INK)
    return c


def ledger(side):
    W, H = 900, 1200
    c = Cell(W, H, (232, 222, 196), grain=5, seed=3510 + side, vignette=0.18, fibres=True)
    g = random.Random(3511 + side)
    # ruled rows (blue) and column rules (crimson double)
    lined(c, 30, W - 30, 170, H - 40, 52, colour=(140, 156, 190))
    cols = [40, 340, 430, 520, 610, 700, 790, W - 30] if side == 0 else [40, 130, 220, 310, 400, 490, 600, W - 30]
    for x in cols[1:-1]:
        c.shape(lambda d, k, x=x: d.line([(x * k, 120 * k), (x * k, (H - 40) * k)], fill=255, width=int(2 * k)), (170, 40, 46))
        c.shape(lambda d, k, x=x: d.line([((x + 5) * k, 120 * k), ((x + 5) * k, (H - 40) * k)], fill=255, width=int(1 * k)), (170, 40, 46))
    c.shape(lambda d, k: d.line([(30 * k, 166 * k), ((W - 30) * k, 166 * k)], fill=255, width=int(3 * k)), (170, 40, 46))
    if side == 0:
        c.text("FORM IV  -  LATIN & HISTORY", "pala", W / 2, 50, 760, 44, colour=INK)
        heads = ["Pupil", "I", "II", "III", "IV", "V", "VI"]
    else:
        c.text("Michaelmas Term", "palai", W / 2, 50, 600, 44, colour=INK)
        heads = ["VII", "VIII", "IX", "X", "Exam", "Total", "Remarks"]
    for i, h in enumerate(heads):
        c.text(h, "palab" if False else "pala", (cols[i] + cols[i + 1]) / 2, 140, cols[i + 1] - cols[i] - 10, 32, colour=INK)
    for r in range(len(PUPILS) + 4):
        y = 170 + 52 * r + 28
        if y > H - 60:
            break
        if r >= len(PUPILS):
            continue
        if side == 0:
            c.text(PUPILS[r], "hand", cols[0] + 10, y, cols[1] - cols[0] - 20, 34, colour=(28, 34, 78), anchor="lm")
            marks = cols[1:-1]
        else:
            marks = cols[:4]
        for i, x in enumerate(marks):
            v = g.randint(3, 10)
            red = v <= 4
            c.text(str(v), "hand", (x + (cols[cols.index(x) + 1])) / 2, y, 60, 34, colour=REDINK if red else (28, 34, 78))
        if side == 1:
            c.text(str(g.randint(28, 96)), "hand", (cols[4] + cols[5]) / 2, y, 70, 34, colour=(28, 34, 78))
            c.text(str(g.randint(60, 180)), "hand", (cols[5] + cols[6]) / 2, y, 90, 34, colour=(28, 34, 78))
            rem = g.choice(["Good", "Diligent", "Must try harder", "Satisfactory", "Late twice", "Excellent", "Inattentive", "", ""])
            if rem:
                c.text(rem, "hand", cols[6] + 10, y, cols[7] - cols[6] - 20, 30, colour=REDINK if "harder" in rem or "Late" in rem or "Inatt" in rem
                       else (28, 34, 78), anchor="lm")
    return c


def exercise_cover(key, bg, fg, subject, name, seed):
    W, H = 620, 820
    c = Cell(W, H, bg, grain=8, seed=seed, vignette=0.25)
    rules(c, 22, fg, 3)
    crest(c, W / 2, 130, 140)
    c.text("NIGHTMARE HIGH", "pala", W / 2, 228, 420, 34, colour=fg)
    c.text("EXERCISE BOOK", "pala", W / 2, 285, 480, 46, colour=fg)
    c.shape(lambda d, k: d.rectangle([90 * k, 360 * k, (W - 90) * k, 660 * k], fill=255), (234, 226, 204))
    c.shape(lambda d, k: d.rectangle([90 * k, 360 * k, (W - 90) * k, 660 * k], outline=255, width=int(3 * k)), fg)
    for i, (lab, val) in enumerate((("Name", name), ("Form", "IV"), ("Subject", subject))):
        y = 420 + i * 90
        c.text(lab, "palai", 110, y, 140, 30, colour=INK, anchor="lm")
        c.shape(lambda d, k, y=y: d.line([(230 * k, (y + 18) * k), ((W - 110) * k, (y + 18) * k)], fill=255, width=int(2 * k)), INK)
        c.text(val, "hand", 240, y - 2, W - 360, 44, colour=(28, 34, 78), anchor="lm")
    return c


def marked_sheet(key, seed, lines, grade, comment):
    W, H = 700, 920
    c = Cell(W, H, (238, 234, 222), grain=4, seed=seed, fibres=True)
    lined(c, 30, W - 30, 150, H - 40, 40, margin=90)
    g = random.Random(seed)
    for i, ln in enumerate(lines):
        y = 170 + i * 40
        c.text(ln, "hand", 110, y, 520, 30, anchor="lm", colour=(30, 36, 80))
        if g.random() < 0.55:
            # a red tick
            c.shape(lambda d, k, y=y: d.line([(620 * k, y * k), (632 * k, (y + 12) * k), (656 * k, (y - 16) * k)], fill=255, width=int(4 * k)),
                    REDINK)
    c.text(grade, "scriptb", 590, 80, 130, 90, colour=REDINK)
    c.shape(lambda d, k: d.ellipse([520 * k, 30 * k, 660 * k, 132 * k], outline=255, width=int(5 * k)), REDINK)
    c.text(comment, "script", W / 2, H - 120, 560, 56, colour=REDINK, angle=3)
    return c


def suit(d, k, kind, x, y, s):
    """A playing-card suit shape centred at (x, y), s px tall."""
    X = lambda u: (x + u * s) * k
    Y = lambda v: (y + v * s) * k
    if kind == "D":
        d.polygon([(X(0), Y(-0.5)), (X(0.36), Y(0)), (X(0), Y(0.5)), (X(-0.36), Y(0))], fill=255)
    elif kind == "H":
        r = 0.24
        d.ellipse([X(-0.48), Y(-0.42), X(-0.48 + 2 * r), Y(-0.42 + 2 * r)], fill=255)
        d.ellipse([X(0.0), Y(-0.42), X(0.48), Y(-0.42 + 2 * r)], fill=255)
        d.polygon([(X(-0.47), Y(-0.12)), (X(0.47), Y(-0.12)), (X(0), Y(0.46))], fill=255)
    elif kind == "S":
        r = 0.22
        d.ellipse([X(-0.46), Y(-0.08), X(-0.46 + 2 * r), Y(-0.08 + 2 * r)], fill=255)
        d.ellipse([X(0.02), Y(-0.08), X(0.46), Y(-0.08 + 2 * r)], fill=255)
        d.polygon([(X(-0.45), Y(0.12)), (X(0.45), Y(0.12)), (X(0), Y(-0.5))], fill=255)
        d.polygon([(X(0), Y(0.1)), (X(0.14), Y(0.5)), (X(-0.14), Y(0.5))], fill=255)
    else:  # clubs
        r = 0.18
        for u, v in ((0, -0.3), (-0.22, 0.04), (0.22, 0.04)):
            d.ellipse([X(u - r), Y(v - r), X(u + r), Y(v + r)], fill=255)
        d.polygon([(X(0), Y(-0.05)), (X(0.13), Y(0.5)), (X(-0.13), Y(0.5))], fill=255)


PIPS = {1: [(0.5, 0.5)], 3: [(0.5, 0.2), (0.5, 0.5), (0.5, 0.8)], 5: [(0.3, 0.2), (0.7, 0.2), (0.5, 0.5), (0.3, 0.8), (0.7, 0.8)],
        7: [(0.3, 0.2), (0.7, 0.2), (0.5, 0.35), (0.3, 0.5), (0.7, 0.5), (0.3, 0.8), (0.7, 0.8)],
        9: [(0.3, 0.18), (0.7, 0.18), (0.3, 0.39), (0.7, 0.39), (0.5, 0.5), (0.3, 0.61), (0.7, 0.61), (0.3, 0.82), (0.7, 0.82)],
        10: [(0.3, 0.16), (0.7, 0.16), (0.5, 0.29), (0.3, 0.4), (0.7, 0.4), (0.3, 0.6), (0.7, 0.6), (0.5, 0.71), (0.3, 0.84), (0.7, 0.84)]}


def card(rank, kind):
    W, H = 250, 350
    c = Cell(W, H, (236, 230, 214), grain=3, seed=seed_of(f"{rank}{kind}"))
    col = (150, 18, 30) if kind in "HD" else (20, 20, 28)
    c.shape(lambda d, k: d.rectangle([8 * k, 8 * k, (W - 8) * k, (H - 8) * k], outline=255, width=int(2 * k)), (180, 160, 120))
    lab = {1: "A"}.get(rank, str(rank))
    for (x, y, a) in ((26, 34, 0), (W - 26, H - 34, 180)):
        c.text(lab, "geo", x, y, 40, 36, colour=col, angle=a)
        c.shape(lambda d, k, x=x, y=y, a=a: suit(d, k, kind, x, y + (26 if a == 0 else -26), 22), col)
    big = 70 if rank == 1 else 44
    for u, v in PIPS[rank]:
        c.shape(lambda d, k, u=u, v=v: suit(d, k, kind, 40 + u * (W - 80), 40 + v * (H - 80), big), col)
    return c


def card_back():
    W, H = 250, 350
    c = Cell(W, H, (120, 16, 28), grain=4, seed=3520)
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, H * k], fill=255), (236, 230, 214))
    c.shape(lambda d, k: d.rectangle([12 * k, 12 * k, (W - 12) * k, (H - 12) * k], fill=255), (110, 14, 26))

    def lattice(d, k):
        for i in range(-20, 30):
            x = i * 22
            d.line([(x * k, 12 * k), ((x + H) * k, (H + 12) * k)], fill=255, width=int(1.5 * k))
            d.line([((x + H) * k, 12 * k), (x * k, (H + 12) * k)], fill=255, width=int(1.5 * k))
    c.shape(lattice, (150, 40, 50))
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 12 * k], fill=255), (236, 230, 214))
    c.shape(lambda d, k: d.rectangle([0, (H - 12) * k, W * k, H * k], fill=255), (236, 230, 214))
    c.shape(lambda d, k: d.rectangle([0, 0, 12 * k, H * k], fill=255), (236, 230, 214))
    c.shape(lambda d, k: d.rectangle([(W - 12) * k, 0, W * k, H * k], fill=255), (236, 230, 214))
    rules(c, 20, GILT, 2)
    crest(c, W / 2, H / 2, 120)
    return c


DART_ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]


def dartboard():
    W = 1024
    c = Cell(W, W, (16, 14, 16), grain=4, seed=3530)
    cx = cy = W / 2
    R = W / 2 - 4
    # radii as fractions of the scoring circle (double ring outer edge at 0.76 R)
    rs = 0.76 * R
    rad = {"dbl_o": rs, "dbl_i": rs * 0.94, "tr_o": rs * 0.63, "tr_i": rs * 0.57, "bull_o": rs * 0.094, "bull_i": rs * 0.037}
    sisal_a, sisal_b = (24, 22, 24), (214, 198, 160)
    ring_a, ring_b = (150, 18, 30), (24, 66, 48)

    def wedge(d, k, r0, r1, a0, a1):
        pts = []
        for i in range(9):
            a = a0 + (a1 - a0) * i / 8
            pts.append(((cx + math.cos(a) * r1) * k, (cy + math.sin(a) * r1) * k))
        for i in range(8, -1, -1):
            a = a0 + (a1 - a0) * i / 8
            pts.append(((cx + math.cos(a) * r0) * k, (cy + math.sin(a) * r0) * k))
        d.polygon(pts, fill=255)
    for i in range(20):
        a0 = -math.pi / 2 + (i - 0.5) * 2 * math.pi / 20
        a1 = a0 + 2 * math.pi / 20
        base = sisal_a if i % 2 == 0 else sisal_b
        ring = ring_a if i % 2 == 0 else ring_b
        c.shape(lambda d, k: wedge(d, k, rad["bull_o"], rad["dbl_o"], a0, a1), base)
        c.shape(lambda d, k: wedge(d, k, rad["tr_i"], rad["tr_o"], a0, a1), ring)
        c.shape(lambda d, k: wedge(d, k, rad["dbl_i"], rad["dbl_o"], a0, a1), ring)
    c.shape(lambda d, k: d.ellipse([(cx - rad["bull_o"]) * k, (cy - rad["bull_o"]) * k, (cx + rad["bull_o"]) * k, (cy + rad["bull_o"]) * k], fill=255),
            ring_b)
    c.shape(lambda d, k: d.ellipse([(cx - rad["bull_i"]) * k, (cy - rad["bull_i"]) * k, (cx + rad["bull_i"]) * k, (cy + rad["bull_i"]) * k], fill=255),
            ring_a)

    # the wire spider (silver: metal mask)
    def wires(d, k):
        for r in (rad["dbl_o"], rad["dbl_i"], rad["tr_o"], rad["tr_i"], rad["bull_o"], rad["bull_i"]):
            d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], outline=255, width=int(2.4 * k))
        for i in range(20):
            a = -math.pi / 2 + (i - 0.5) * 2 * math.pi / 20
            d.line([((cx + math.cos(a) * rad["bull_o"]) * k, (cy + math.sin(a) * rad["bull_o"]) * k),
                    ((cx + math.cos(a) * rad["dbl_o"]) * k, (cy + math.sin(a) * rad["dbl_o"]) * k)], fill=255, width=int(2.4 * k))
    c.shape(wires, (200, 200, 204), metal=230, height=170)
    for i, n in enumerate(DART_ORDER):
        a = -math.pi / 2 + i * 2 * math.pi / 20
        r = rs + (R - rs) * 0.5
        c.text(str(n), "geo", cx + math.cos(a) * r, cy + math.sin(a) * r, 90, 64, colour=(222, 214, 196), angle=-math.degrees(a) - 90,
               metal=200, height=175)
    # a few old dart holes
    g = np.random.default_rng(3531)
    def holes(d, k):
        for _ in range(260):
            a, rr = g.uniform(0, 6.283), rs * math.sqrt(g.uniform(0.0, 1.0))
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            d.ellipse([(x - 1.6) * k, (y - 1.6) * k, (x + 1.6) * k, (y + 1.6) * k], fill=255)
    c.shape(holes, (10, 8, 8), height=90)
    return c


def score_slate():
    W, H = 520, 760
    c = slate_cell(W, H, 3532)
    chalk_text(c, "501", "printb", W / 2, 60, 200, 70, seed=40)
    chalk_line(c, [(40, 108), (W - 40, 110)], 4)
    chalk_line(c, [(W / 2, 112), (W / 2 + 3, H - 40)], 3)
    chalk_text(c, "HALE", "printb", W / 4, 150, 200, 48, seed=41)
    chalk_text(c, "CROWE", "printb", 3 * W / 4, 150, 200, 48, seed=42)
    a, b = 501, 501
    g = random.Random(3533)
    for i in range(9):
        a -= g.choice([26, 41, 45, 60, 81, 100, 57, 22])
        b -= g.choice([26, 41, 45, 60, 85, 100, 33, 18])
        y = 220 + i * 58
        chalk_text(c, str(max(a, 0)), "hand", W / 4, y, 160, 46, alpha=0.8, seed=50 + i)
        chalk_text(c, str(max(b, 0)), "hand", 3 * W / 4, y, 160, 46, alpha=0.8, seed=60 + i)
        if i < 8:
            chalk_line(c, [(W / 4 - 50, y + 5), (W / 4 + 50, y - 3)], 3, 0.6)
            chalk_line(c, [(3 * W / 4 - 50, y + 3), (3 * W / 4 + 50, y - 4)], 3, 0.6)
    return c


def mug_wrap(key, bg, fg, kind):
    W, H = 900, 300
    c = Cell(W, H, bg, grain=3, seed=seed_of(key))
    if kind == "crest":
        crest(c, W * 0.25, H / 2, 200)
        crest(c, W * 0.75, H / 2, 200)
    elif kind == "staff":
        c.shape(lambda d, k: d.rectangle([0, 30 * k, W * k, 40 * k], fill=255), GILT)
        c.shape(lambda d, k: d.rectangle([0, (H - 40) * k, W * k, (H - 30) * k], fill=255), GILT)
        c.text("STAFF", "pala", W * 0.25, H / 2, 300, 110, colour=GILT)
        c.text("STAFF", "pala", W * 0.75, H / 2, 300, 110, colour=GILT)
    elif kind == "stripe":
        for y0, y1 in ((40, 70), (90, 100), (H - 100, H - 90), (H - 70, H - 40)):
            c.shape(lambda d, k, y0=y0, y1=y1: d.rectangle([0, y0 * k, W * k, y1 * k], fill=255), fg)
    elif kind == "raven":
        for x in (W * 0.25, W * 0.75):
            def raven(d, k, x=x):
                y = H / 2
                d.ellipse([(x - 60) * k, (y - 30) * k, (x + 50) * k, (y + 34) * k], fill=255)
                d.ellipse([(x + 30) * k, (y - 64) * k, (x + 80) * k, (y - 14) * k], fill=255)
                d.polygon([((x + 76) * k, (y - 46) * k), ((x + 110) * k, (y - 36) * k), ((x + 76) * k, (y - 30) * k)], fill=255)
                d.polygon([((x - 50) * k, (y + 10) * k), ((x - 120) * k, (y + 40) * k), ((x - 40) * k, (y + 30) * k)], fill=255)
                d.line([((x - 6) * k, (y + 30) * k), ((x - 10) * k, (y + 70) * k)], fill=255, width=int(5 * k))
                d.line([((x + 14) * k, (y + 30) * k), ((x + 12) * k, (y + 70) * k)], fill=255, width=int(5 * k))
            c.shape(raven, fg)
    elif kind == "moon":
        g = random.Random(5)
        def moons(d, k):
            for i in range(10):
                x, y, r = 40 + i * 88 + g.uniform(-10, 10), g.uniform(70, H - 70), g.uniform(18, 30)
                d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
        c.shape(moons, fg)
        g = random.Random(5)
        def bite(d, k):
            for i in range(10):
                x, y, r = 40 + i * 88 + g.uniform(-10, 10), g.uniform(70, H - 70), g.uniform(18, 30)
                d.ellipse([(x - r * 0.5) * k, (y - r * 1.05) * k, (x + r * 1.4) * k, (y + r * 0.85) * k], fill=255)
        c.shape(bite, bg)
    return c


def barrel_wrap():
    W, H = 1200, 460
    c = Cell(W, H, (222, 212, 186), grain=4, seed=3540)
    for y0, y1, col in ((20, 34, GILT), (44, 70, CRIMSON), (H - 70, H - 44, CRIMSON), (H - 34, H - 20, GILT)):
        c.shape(lambda d, k, y0=y0, y1=y1: d.rectangle([0, y0 * k, W * k, y1 * k], fill=255), col)
    for i in range(4):
        x = (i + 0.5) * W / 4
        if i % 2 == 0:
            crest(c, x, H / 2, 210)
        else:
            c.text("BISCUITS", "pala", x, H / 2, 250, 70, colour=CRIMSON)
            fleuron(c, x - 110, H / 2 + 70, 16, CRIMSON)
            fleuron(c, x + 110, H / 2 + 70, 16, CRIMSON)
    return c


# ------------------------------------------------------------------ batch 36: the school

MAP_PLACES = [("Ravenmoor", 0.28, 0.3), ("The Ashen Wold", 0.55, 0.22), ("Hollowmere", 0.42, 0.55), ("Candlefall", 0.7, 0.48),
              ("Vigil Sound", 0.16, 0.62), ("Mortlake Bay", 0.62, 0.78), ("Gloamwood", 0.36, 0.76), ("Saint Wren's", 0.8, 0.3)]


def wall_map():
    W, H = 1700, 1150
    c = Cell(W, H, (214, 196, 152), grain=7, seed=3601, vignette=0.35, fibres=True)
    g = np.random.default_rng(3602)
    # land: smooth noise thresholded, pushed down toward the edges so it is one big island with a few smaller ones
    n = np.zeros((H // 2, W // 2), np.float32)
    for o, amp in ((6, 1.0), (12, 0.5), (24, 0.25), (48, 0.12)):
        lo = g.uniform(0, 1, (max(2, int(o * H / W)), o)).astype(np.float32)
        n += amp * np.asarray(Image.fromarray(np.uint8(lo * 255)).resize((W // 2, H // 2), Image.BICUBIC), np.float32) / 255
    yy, xx = np.mgrid[0:H // 2, 0:W // 2].astype(np.float32)
    d = np.hypot((xx / (W / 2) - 0.48) * 1.25, (yy / (H / 2) - 0.52) * 1.5)
    n = n / 1.87 - d * 0.75
    land = n > 0.08
    lm = Image.fromarray(np.uint8(land * 255)).resize((W * D.SS, H * D.SS), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    lm = lm.point(lambda v: 255 if v > 128 else 0)
    # sea hatching: lines round the coast
    coast = lm.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(6))
    for i, rad in enumerate((18, 34, 52)):
        ring_ = lm.filter(ImageFilter.MaxFilter(2 * rad + 1))
        edge = np.asarray(ring_.filter(ImageFilter.FIND_EDGES), np.float32)
        c.stamp(Image.fromarray(np.uint8(np.clip(edge * (0.6 - i * 0.15), 0, 255))), 0, 0, (120, 104, 82), anchor="lt")
    c.stamp(lm, 0, 0, (200, 182, 136), anchor="lt")
    edge = lm.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
    c.stamp(edge, 0, 0, (60, 44, 32), anchor="lt")
    la = np.asarray(lm) > 128
    rnd = random.Random(3603)

    def on_land(x, y):
        X, Y = int(x * D.SS), int(y * D.SS)
        return 0 <= X < la.shape[1] and 0 <= Y < la.shape[0] and la[Y, X]
    # mountains, forests
    def mountains(d, k):
        for _ in range(400):
            x, y = rnd.uniform(0.3, 0.75) * W, rnd.uniform(0.12, 0.45) * H
            if not on_land(x, y) or rnd.random() < 0.6:
                continue
            s = rnd.uniform(12, 22)
            d.line([((x - s) * k, (y + s * 0.6) * k), (x * k, (y - s * 0.7) * k), ((x + s) * k, (y + s * 0.6) * k)], fill=255, width=int(2 * k))
    c.shape(mountains, (70, 50, 36))

    def trees(d, k):
        for _ in range(700):
            x, y = rnd.uniform(0.2, 0.5) * W, rnd.uniform(0.6, 0.9) * H
            if not on_land(x, y) or rnd.random() < 0.5:
                continue
            r = rnd.uniform(4, 7)
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], outline=255, width=int(1.6 * k))
            d.line([(x * k, (y + r) * k), (x * k, (y + r + 5) * k)], fill=255, width=int(1.6 * k))
    c.shape(trees, (60, 70, 44))

    # rivers: random walks from the mountains to the sea
    def rivers(d, k):
        for s in range(4):
            x, y = rnd.uniform(0.38, 0.65) * W, rnd.uniform(0.28, 0.4) * H
            pts = [(x, y)]
            ang = rnd.uniform(1.2, 2.0)
            for _ in range(200):
                ang += rnd.uniform(-0.35, 0.35)
                x, y = x + math.cos(ang) * 6, y + math.sin(ang) * 6
                pts.append((x, y))
                if not on_land(x, y):
                    break
            d.line([(px * k, py * k) for px, py in pts], fill=255, width=int(2.4 * k))
    c.shape(rivers, (70, 86, 110))
    # towns and labels
    for name, u, v in MAP_PLACES:
        x, y = u * W, v * H
        c.shape(lambda d, k, x=x, y=y: d.ellipse([(x - 7) * k, (y - 7) * k, (x + 7) * k, (y + 7) * k], fill=255), CRIMSON)
        c.text(name, "palai", x, y + 28, 300, 34, colour=(50, 36, 28))
    # the school: a crest on the lake shore
    crest(c, 0.5 * W, 0.42 * H, 70)
    c.text("Nightmare High", "pala", 0.5 * W, 0.42 * H + 52, 260, 30, colour=CRIMSON)
    # the title cartouche and a compass rose
    c.shape(lambda d, k: d.rectangle([40 * k, 40 * k, 560 * k, 170 * k], fill=255), (226, 210, 168))
    c.shape(lambda d, k: d.rectangle([40 * k, 40 * k, 560 * k, 170 * k], outline=255, width=int(4 * k)), (60, 44, 32))
    c.shape(lambda d, k: d.rectangle([50 * k, 50 * k, 550 * k, 160 * k], outline=255, width=int(1.5 * k)), (60, 44, 32))
    c.text("The Nocturne Reaches", "palabi", 300, 92, 480, 60, colour=(40, 28, 24))
    c.text("a map for the use of the school", "palai", 300, 140, 420, 26, colour=(60, 44, 32))
    cx, cy, r = W - 170, H - 170, 110

    def rose(d, k):
        for i in range(8):
            a = i * math.pi / 4 - math.pi / 2
            L = r if i % 2 == 0 else r * 0.55
            w = 0.2
            d.polygon([((cx + math.cos(a) * L) * k, (cy + math.sin(a) * L) * k), ((cx + math.cos(a + w) * 18) * k, (cy + math.sin(a + w) * 18) * k),
                       (cx * k, cy * k), ((cx + math.cos(a - w) * 18) * k, (cy + math.sin(a - w) * 18) * k)], fill=255)
        d.ellipse([(cx - r * 0.7) * k, (cy - r * 0.7) * k, (cx + r * 0.7) * k, (cy + r * 0.7) * k], outline=255, width=int(2 * k))
    c.shape(rose, (60, 44, 32))
    c.text("N", "pala", cx, cy - r - 24, 40, 40, colour=CRIMSON)
    # a sea serpent (just humps) and a ship-free sea label
    c.text("The Grey Water", "palai", 0.12 * W, 0.2 * H, 300, 40, colour=(70, 60, 50), angle=12)
    c.text("Mare Tenebrarum", "palai", 0.82 * W, 0.68 * H, 300, 40, colour=(70, 60, 50), angle=-8)
    for i in range(3):
        x = 0.85 * W + i * 40
        c.shape(lambda d, k, x=x: d.arc([(x - 18) * k, (0.86 * H - 18) * k, (x + 18) * k, (0.86 * H + 18) * k], 180, 360, fill=255, width=int(4 * k)),
                (60, 50, 44))
    rules(c, 14, (60, 44, 32), 4)
    return c


def slate_sums():
    W, H = 640, 480
    c = slate_cell(W, H, 3610)
    lines = ["7 x 8 = 56", "9 x 6 = 54", "12 x 4 = 48", "144 / 12 = 12"]
    for i, s in enumerate(lines):
        chalk_text(c, s, "hand", 60, 70 + i * 92, 520, 66, anchor="lm", seed=70 + i, angle=random.Random(i).uniform(-2, 2))
    chalk_text(c, "E. Ashworth", "hand", W - 40, H - 40, 260, 40, anchor="rm", alpha=0.6, seed=80)
    return c


def music(key, seed, title):
    W, H = 700, 920
    c = Cell(W, H, (232, 222, 196), grain=4, seed=seed, vignette=0.2, fibres=True)
    g = random.Random(seed)
    if title:
        c.text(title, "palabi", W / 2, 54, 520, 50, colour=INK)
        c.text("for the school pianoforte  -  A. Vane", "palai", W / 2, 100, 520, 26, colour=INK)
    y = 150 if title else 70
    while y + 60 < H - 30:
        def staff(d, k, y=y):
            for i in range(5):
                d.line([(40 * k, (y + i * 12) * k), ((W - 40) * k, (y + i * 12) * k)], fill=255, width=int(1.3 * k))
            d.line([(40 * k, y * k), (40 * k, (y + 48) * k)], fill=255, width=int(2 * k))
            d.line([((W - 40) * k, y * k), ((W - 40) * k, (y + 48) * k)], fill=255, width=int(2 * k))
            for bx in (220, 400, 580):
                d.line([(bx * k, y * k), (bx * k, (y + 48) * k)], fill=255, width=int(1.5 * k))
        c.shape(staff, INK)

        def notes(d, k, y=y):
            x = 80
            while x < W - 60:
                if x in range(210, 232) or x in range(390, 412) or x in range(570, 592):
                    x += 24
                    continue
                p = g.randint(-2, 10)
                ny = y + 48 - p * 6
                d.ellipse([(x - 7) * k, (ny - 5) * k, (x + 7) * k, (ny + 5) * k], fill=255)
                up = p < 4
                sx = x + 6 if up else x - 6
                d.line([(sx * k, ny * k), (sx * k, (ny - 36 if up else ny + 36) * k)], fill=255, width=int(1.6 * k))
                for lp in range(-2, p - 9, -2) if p < -1 else []:
                    pass
                x += g.choice([22, 26, 30, 44])
        c.shape(notes, INK)
        y += 96
    return c


def blotter():
    W, H = 900, 560
    c = Cell(W, H, (34, 70, 52), grain=6, seed=3620)
    g = random.Random(3621)
    # mirrored handwriting picked up by the blotting paper, and a few ink blots
    for i in range(7):
        s = g.choice(["Dear Headmaster", "per noctem ad lucem", "the third of the month", "yours faithfully", "kindly see me",
                      "Form IV detention list", "returned with thanks"])
        m = c.fit(s, "script", 520, 36).transpose(Image.FLIP_LEFT_RIGHT)
        c.stamp(m, g.uniform(220, 680), 60 + i * 66, (18, 28, 40), angle=g.uniform(-6, 6), alpha=0.55)

    def blots(d, k):
        for _ in range(6):
            x, y = g.uniform(80, W - 80), g.uniform(80, H - 80)
            r = g.uniform(8, 26)
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
            for _ in range(5):
                a, dd = g.uniform(0, 6.28), g.uniform(r, r * 2)
                rr = g.uniform(2, 6)
                d.ellipse([(x + math.cos(a) * dd - rr) * k, (y + math.sin(a) * dd - rr) * k, (x + math.cos(a) * dd + rr) * k,
                           (y + math.sin(a) * dd + rr) * k], fill=255)
    c.shape(blots, (10, 14, 26))
    return c


def jar_label(key, latin, english, seed):
    W, H = 420, 260
    c = Cell(W, H, (226, 214, 180), grain=5, seed=seed, vignette=0.25, fibres=True)
    rules(c, 12, INK, 3)
    rules(c, 22, INK, 1)
    c.text(latin, "palabi", W / 2, 95, W - 70, 52, colour=INK)
    c.text(english, "palai", W / 2, 160, W - 90, 34, colour=(60, 44, 32))
    c.text(f"No. {seed % 97 + 3}", "hand", W / 2, 212, 160, 30, colour=(28, 34, 78))
    return c


def bucket_wrap():
    W, H = 1000, 340
    c = Cell(W, H, (110, 14, 26), grain=4, seed=3630)
    for y0, y1 in ((16, 26), (H - 26, H - 16)):
        c.shape(lambda d, k, y0=y0, y1=y1: d.rectangle([0, y0 * k, W * k, y1 * k], fill=255), GILT)
    for x in (W * 0.25, W * 0.75):
        c.text("FIRE", "pala", x, H / 2, 300, 150, colour=GILT)
    return c


def dunce():
    W, H = 900, 700
    c = Cell(W, H, (226, 218, 196), grain=6, seed=3640, fibres=True)
    g = random.Random(3641)

    def stars(d, k):
        for _ in range(26):
            x, y, r = g.uniform(30, W - 30), g.uniform(20, H - 30), g.uniform(10, 20)
            pts = []
            for i in range(10):
                a = -math.pi / 2 + i * math.pi / 5
                rr = r if i % 2 == 0 else r * 0.45
                pts.append(((x + math.cos(a) * rr) * k, (y + math.sin(a) * rr) * k))
            d.polygon(pts, fill=255)
    c.shape(stars, (40, 40, 70))
    for x in (W * 0.25, W * 0.75):
        c.shape(lambda d, k, x=x: d.ellipse([(x - 120) * k, (H * 0.62 - 120) * k, (x + 120) * k, (H * 0.62 + 120) * k], fill=255), (234, 228, 210))
        c.text("D", "pala", x, H * 0.62, 200, 200, colour=INK)
    return c


def metro_scale():
    W, H = 160, 760
    c = Cell(W, H, (196, 158, 92), grain=3, seed=3650)
    c.m = Image.new("L", c.c.size, 220)
    tempi = [("Largo", 40), ("Lento", 52), ("Adagio", 66), ("Andante", 80), ("Moderato", 100), ("Allegro", 126), ("Vivace", 152), ("Presto", 184),
             ("", 208)]
    for i, (t, bpm) in enumerate(tempi):
        y = H - 40 - i * (H - 80) / (len(tempi) - 1)
        c.shape(lambda d, k, y=y: d.line([(10 * k, y * k), (40 * k, y * k)], fill=255, width=int(2 * k)), (40, 26, 14))
        c.text(str(bpm), "geo", 64, y, 50, 26, colour=(40, 26, 14), anchor="lm")
        if t:
            c.text(t, "palai", 120, y - 22, 80, 18, colour=(40, 26, 14))
    return c


def swatch(colour, grain=5, seed=0, metal=0):
    c = Cell(48, 48, colour, grain=grain, seed=seed)
    if metal:
        c.m = Image.new("L", c.c.size, metal)
    return c


# ------------------------------------------------------------------ main

if __name__ == "__main__":
    pr = Atlas("StaffPrint")
    pr.put("Map", wall_map(), 0.9)
    pr.put("Rota", rota(), 0.9)
    pr.put("Ledger_L", ledger(0), 0.8)
    pr.put("Ledger_R", ledger(1), 0.8)
    pr.put("Dartboard", dartboard(), 0.8)
    pr.put("Score", score_slate(), 0.7)
    for k, bg, fg, subj, nm, sd in (("Ex_Crimson", (118, 18, 30), (226, 200, 140), "Latin", "T. Blackwood", 1),
                                    ("Ex_Ink", (30, 36, 64), (214, 198, 160), "History", "M. Corvin", 2),
                                    ("Ex_Kraft", (168, 128, 86), (60, 30, 22), "Arithmetic", "R. Everleigh", 3)):
        pr.put(k, exercise_cover(k, bg, fg, subj, nm, 3550 + sd), 0.6)
    pr.put("Sheet_A", marked_sheet("Sheet_A", 3560, ["The founding of the school", "took place in the year of the", "long winter, when the bell",
                                                       "tower was raised by the first", "Headmaster and his wardens.", "The east wing was closed",
                                                       "after the great storm.", "", "Dates to learn:", "the bell, the lantern, the gate"], "B+", "Good work."), 0.62)
    pr.put("Sheet_B", marked_sheet("Sheet_B", 3561, ["1.  48 + 37 = 85", "2.  96 - 58 = 38", "3.  12 x 11 = 132", "4.  7 x 9 = 63",
                                                       "5.  144 / 12 = 12", "6.  3/4 of 60 = 45", "7.  1/3 of 27 = 8", "8.  15 x 15 = 225"], "7/8",
                                    "Check no. 7"), 0.62)
    pr.put("Sheet_C", marked_sheet("Sheet_C", 3562, ["amo, amas, amat", "amamus, amatis, amant", "", "moneo, mones, monet",
                                                       "monemus, monetis, monent", "", "rego, regis, regit"], "A-", "Neatly done."), 0.62)
    pr.put("Music_A", music("Music_A", 3660, "Nocturne in Ash"), 0.62)
    pr.put("Music_B", music("Music_B", 3661, None), 0.62)
    pr.put("Barrel", barrel_wrap(), 0.7)
    pr.put("Blotter", blotter(), 0.6)
    pr.put("Bucket", bucket_wrap(), 0.6)
    pr.put("Dunce", dunce(), 0.6)
    pr.put("Slate", slate_sums(), 0.7)
    for k, bg, fg, kind in (("Mug_Crest", (222, 212, 188), CRIMSON, "crest"), ("Mug_Staff", (110, 14, 26), GILT, "staff"),
                            ("Mug_Stripe", (222, 212, 188), CRIMSON, "stripe"), ("Mug_Raven", (26, 28, 40), (214, 202, 172), "raven"),
                            ("Mug_Moon", (30, 40, 72), (226, 214, 170), "moon")):
        pr.put(k, mug_wrap(k, bg, fg, kind), 0.55)
    for i, n in enumerate(STAFF):
        pr.put(f"Tag_{i}", tag(n, 3570 + i), 0.6)
    for k, la, en, sd in (("Jar_0", "Rana nocturna", "the night frog", 3670), ("Jar_1", "Hippocampus minor", "a little sea-horse", 3671),
                          ("Jar_2", "Scarabaeus niger", "black beetles", 3672), ("Jar_3", "Mandragora radix", "mandrake root", 3673),
                          ("Jar_4", "Octopoda pallida", "a pale octopus", 3674), ("Jar_5", "Filix umbrosa", "shade fern", 3675)):
        pr.put(k, jar_label(k, la, en, sd), 0.5)
    pr.put("Card_Back", card_back(), 0.7)
    for r, s in ((1, "S"), (7, "H"), (10, "D"), (3, "C"), (9, "S"), (5, "H")):
        pr.put(f"Card_{r}{s}", card(r, s), 0.7)
    pr.put("Metro", metro_scale(), 0.7)
    for name, col, g, m in (("paper", (232, 226, 206), 4, 0), ("bone", BONE, 5, 0), ("chalk", CHALK, 6, 0), ("slate", SLATE, 6, 0),
                            ("crimson", CRIMSON, 4, 0), ("ink", INK, 3, 0), ("kraft", (168, 128, 86), 9, 0), ("gilt", GILT, 4, 235),
                            ("card", (236, 230, 214), 3, 0), ("parch", PARCH, 6, 0), ("excrim", (118, 18, 30), 6, 0), ("exink", (30, 36, 64), 6, 0),
                            ("map", (200, 182, 136), 6, 0), ("blotter", (34, 70, 52), 6, 0), ("mugbone", (222, 212, 188), 3, 0),
                            ("mugcrim", (110, 14, 26), 3, 0), ("mugink", (26, 28, 40), 3, 0), ("mugblue", (30, 40, 72), 3, 0), ("dart", (16, 14, 16), 4, 0)):
        pr.put(f"Swatch_{name}", swatch(col, g, seed_of(name), m))
    pr.save()
    json.dump({"print": pr.reg}, open(os.path.join(HERE, "staff_atlas.json"), "w"), indent=0)
