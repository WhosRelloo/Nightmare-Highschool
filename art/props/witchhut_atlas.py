"""Printed atlas for props batch 47, the witch hut kit. System Python (PIL + numpy):

  python art/props/witchhut_atlas.py

WitchPrint  the hand-written jar and bottle labels (torn parchment tags on string), the open spellbook's two pages (a moon
            circle and a chant, a pressed leaf), four loose spell notes (a moon calendar, a remedy, a toadstool study, a
            list of chores), ten stitched spellbook spines, the patchwork quilt (moons and stars embroidered on the patches),
            the braided rag rug's coils, the painted hex sign for the door, six burnt sigils for the charm tags

Writes art/props/textures/WitchPrint_{color,gilt,height}.png (4096; bake sources only, not uploaded) and
art/props/witchhut_atlas.json (every region's UV rect, v up). Uses dorm_atlas.py's Cell / Atlas machinery. All text and
designs are original.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dorm_atlas as D
from dorm_atlas import Cell, Atlas, swatch, seed_of, INK

HERE = D.HERE
SS = D.SS
PARCH = (206, 188, 146)
PARCH2 = (190, 168, 122)
BROWN = (70, 44, 26)
SEPIA = (64, 38, 22)
GREEN_INK = (34, 58, 30)
VIOLET_INK = (62, 30, 80)
RUST = (120, 46, 24)
WAX = (112, 18, 24)


def burnt_edges(c, amount=0.28, seed=0, col=(52, 34, 18)):
    """Darken a cell toward its ragged edge (old paper, scorched at the rim)."""
    W, H = c.c.size
    g = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)) / (min(W, H) * 0.5)
    n = g.normal(0, 1, (max(2, H // 24), max(2, W // 24)))
    n = np.asarray(Image.fromarray(np.uint8(np.clip(n * 40 + 128, 0, 255))).resize((W, H), Image.BICUBIC), np.float32) / 255 - 0.5
    k = np.clip((amount - d + n * 0.12) / amount, 0, 1) ** 1.6
    a = np.asarray(c.c, np.float32)
    a = a * (1 - k[..., None] * 0.75) + np.array(col, np.float32) * (k[..., None] * 0.75)
    c.c = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    c.dc = ImageDraw.Draw(c.c)


def stains(c, n, seed, col=(150, 120, 80), rmax=60):
    g = random.Random(seed)
    for _ in range(n):
        x, y, r = g.uniform(0, c.w), g.uniform(0, c.h), g.uniform(rmax * 0.3, rmax)

        def dr(d, k, x=x, y=y, r=r):
            d.ellipse([(x - r) * k, (y - r * 0.8) * k, (x + r) * k, (y + r * 0.8) * k], outline=255, width=int(3 * k))
        c.shape(dr, col)


def moon(d, k, x, y, r, phase=0.55, fill=255):
    """A crescent: a disc with a second disc cut out (phase 0 = full, 1 = thin)."""
    d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=fill)
    if phase > 0:
        o = r * (2 - phase * 1.4)
        d.ellipse([(x - r + o * 0.5) * k, (y - r * 1.05) * k, (x + r + o * 0.5) * k, (y + r * 1.05) * k], fill=0)


def star(d, k, x, y, r, n=5, fill=255):
    pts = []
    for i in range(n * 2):
        a = -math.pi / 2 + i * math.pi / n
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(((x + math.cos(a) * rr) * k, (y + math.sin(a) * rr) * k))
    d.polygon(pts, fill=fill)


# ------------------------------------------------------------------ jar labels

LABELS = [
    ("Moonwort", "pick at the full"), ("Wolfsbane", "gloves!!"), ("Black Salt", "for the doorstep"), ("Moon Dew", "Midsummer"),
    ("Toadstool", "not for supper"), ("Crow Quills", "from Old Corvin"), ("Mandrake", "keep him lidded"), ("Hemlock", "NOT for tea"),
    ("Willow Bark", "aches & fevers"), ("Elderflower", "cordial"), ("Fen Moss", "damp it weekly"), ("Dried Moths", "for the lamp"),
    ("Spider Silk", "spun Tuesday"), ("Hag Stones", "holes all through"), ("Thistle Seed", "sow at dusk"), ("Rue", "bitter, keep dry"),
]


def jar_label(i):
    name, note = LABELS[i]
    W, H = 300, 200
    g = random.Random(470 + i)
    tone = PARCH if i % 3 else PARCH2
    c = Cell(W, H, tone, grain=10, seed=4700 + i, fibres=True)
    stains(c, 2, 4710 + i, col=(tone[0] - 40, tone[1] - 42, tone[2] - 40), rmax=50)
    burnt_edges(c, 0.22, 4720 + i)
    ink = (SEPIA, INK, GREEN_INK, VIOLET_INK)[i % 4]
    fk = ("hand", "print", "script", "hand")[i % 4]
    c.text(name, fk, W / 2 + g.uniform(-8, 8), 78, W - 46, 66, colour=ink, angle=g.uniform(-5, 5))
    c.text(note, "hand", W / 2 + g.uniform(-10, 10), 146, W - 80, 30, colour=(ink[0] + 30, ink[1] + 24, ink[2] + 20), angle=g.uniform(-4, 4))
    # a doodle in a corner: a moon, a star or a little leaf
    x, y = (34, 34) if i % 2 else (W - 34, 36)
    if i % 3 == 0:
        c.shape(lambda d, k: moon(d, k, x, y, 16, 0.6), ink)
    elif i % 3 == 1:
        c.shape(lambda d, k: star(d, k, x, y, 15), ink)
    else:
        c.shape(lambda d, k: d.ellipse([(x - 8) * k, (y - 16) * k, (x + 8) * k, (y + 16) * k], outline=255, width=int(3 * k)), ink)
    # the string hole
    c.shape(lambda d, k: d.ellipse([(W / 2 - 9) * k, 10 * k, (W / 2 + 9) * k, 28 * k], fill=255), (40, 28, 16), height=90)
    return c


# ------------------------------------------------------------------ the spellbook's pages

def page_cell(seed, W=700, H=900):
    c = Cell(W, H, (214, 196, 154), grain=9, seed=seed, fibres=True)
    stains(c, 3, seed + 1, col=(176, 150, 108), rmax=90)
    burnt_edges(c, 0.16, seed + 2, col=(120, 90, 56))
    return c


def page_left():
    c = page_cell(4730)
    W, H = c.w, c.h
    cx, cy = W / 2, 330
    # the moon circle: two rings, eight phases round, a five-point star inside
    c.shape(lambda d, k: d.ellipse([(cx - 250) * k, (cy - 250) * k, (cx + 250) * k, (cy + 250) * k], outline=255, width=int(5 * k)), SEPIA)
    c.shape(lambda d, k: d.ellipse([(cx - 205) * k, (cy - 205) * k, (cx + 205) * k, (cy + 205) * k], outline=255, width=int(3 * k)), SEPIA)

    def phases(d, k):
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4
            x, y = cx + math.cos(a) * 228, cy + math.sin(a) * 228
            if i == 0:
                d.ellipse([(x - 16) * k, (y - 16) * k, (x + 16) * k, (y + 16) * k], fill=255)
            elif i == 4:
                d.ellipse([(x - 16) * k, (y - 16) * k, (x + 16) * k, (y + 16) * k], outline=255, width=int(3 * k))
            else:
                moon(d, k, x, y, 16, 0.25 + abs(i - 4) * 0.12)
    c.shape(phases, SEPIA)

    def rays(d, k):      # an eight-rayed compass of the hours round the moon
        for i in range(16):
            a = -math.pi / 2 + i * math.pi / 8
            r0, r1 = 70, (190 if i % 2 == 0 else 130)
            d.line([((cx + math.cos(a) * r0) * k, (cy + math.sin(a) * r0) * k), ((cx + math.cos(a) * r1) * k, (cy + math.sin(a) * r1) * k)],
                   fill=255, width=int((4 if i % 2 == 0 else 2.5) * k))
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4 + math.pi / 8
            star(d, k, cx + math.cos(a) * 160, cy + math.sin(a) * 160, 12)
    c.shape(rays, VIOLET_INK)
    c.shape(lambda d, k: moon(d, k, cx, cy, 46, 0.5), VIOLET_INK)
    g = random.Random(4731)
    lines = ["By the waning of the moon,", "by the root and by the rune,", "what was lost come home to me,",
             "as I will, so mote it be."]
    for i, ln in enumerate(lines):
        c.text(ln, "script", W / 2 + g.uniform(-6, 6), 640 + i * 52, W - 110, 40, colour=SEPIA, angle=g.uniform(-1.5, 1.5))
    c.text("~ a finding charm ~", "hand", W / 2, 860, 300, 30, colour=RUST)
    return c


def page_right():
    c = page_cell(4740)
    W, H = c.w, c.h
    c.text("Moonwort & Rue", "print", W / 2, 70, W - 160, 52, colour=GREEN_INK)
    # a pressed leaf drawn in green ink: a midrib and veins, a lobed outline
    lx, ly = W / 2, 330

    def leaf(d, k):
        pts = []
        for i in range(41):
            t = i / 40 * 2 * math.pi
            r = 160 * (0.55 + 0.45 * abs(math.sin(t))) * (1 + 0.08 * math.sin(t * 9))
            pts.append(((lx + math.sin(t) * r * 0.55) * k, (ly - math.cos(t) * r) * k))
        d.line(pts, fill=255, width=int(4 * k), joint="curve")
        d.line([(lx * k, (ly + 220) * k), (lx * k, (ly - 150) * k)], fill=255, width=int(4 * k))
        for j in range(6):
            yy = ly + 100 - j * 45
            for s in (-1, 1):
                d.line([(lx * k, yy * k), ((lx + s * (70 - j * 6)) * k, (yy - 40) * k)], fill=255, width=int(3 * k))
    c.shape(leaf, GREEN_INK)
    g = random.Random(4741)
    lines = ["Gather three sprigs at dusk,", "bruise in the stone mortar,", "steep nine breaths in moon dew.",
             "Stir sunwise - never widdershins!", "Keep the cat out of the pot."]
    for i, ln in enumerate(lines):
        c.text(ln, "hand", 60, 590 + i * 50, W - 120, 36, colour=SEPIA, anchor="lm", angle=g.uniform(-1.2, 1.2))
    c.text("p. 113", "hand", W - 90, 862, 100, 26, colour=SEPIA)
    return c


# ------------------------------------------------------------------ loose notes

def note_calendar():
    c = page_cell(4750, 600, 800)
    c.text("The Moons of the Year", "print", 300, 64, 520, 46, colour=SEPIA)
    names = ["Wolf", "Snow", "Worm", "Seed", "Hare", "Rose", "Hay", "Grain", "Harvest", "Hunter", "Raven", "Long Night"]

    def grid(d, k):
        for i in range(12):
            x, y = 70 + (i % 3) * 185, 170 + (i // 3) * 150
            moon(d, k, x, y, 24, 0.15 + (i % 6) * 0.13)
    c.shape(grid, VIOLET_INK)
    for i, n in enumerate(names):
        x, y = 70 + (i % 3) * 185, 170 + (i // 3) * 150
        c.text(n, "hand", x + 34, y, 120, 30, colour=SEPIA, anchor="lm")
    return c


def note_remedy():
    c = page_cell(4760, 600, 800)
    c.text("For the Hiccups", "script", 300, 70, 500, 52, colour=SEPIA)
    lines = ["three crow quills, crossed", "a pinch of black salt", "hold breath & count", "backwards from thirteen",
             "if that fails - fright", "(ask the cat)"]
    g = random.Random(4761)
    for i, ln in enumerate(lines):
        c.text(ln, "hand", 70, 170 + i * 74, 470, 40, colour=(INK, SEPIA)[i % 2], anchor="lm", angle=g.uniform(-2, 2))

    def quills(d, k):
        for s in (-1, 1):
            d.line([((300 - s * 120) * k, 640 * k), ((300 + s * 120) * k, 760 * k)], fill=255, width=int(5 * k))
    c.shape(quills, INK)
    return c


def note_toadstool():
    c = page_cell(4770, 600, 800)
    cx = 300

    def toad(d, k):
        d.chord([(cx - 190) * k, 140 * k, (cx + 190) * k, 470 * k], 180, 360, fill=255)
        d.polygon([((cx - 60) * k, 300 * k), ((cx + 60) * k, 300 * k), ((cx + 80) * k, 640 * k), ((cx - 80) * k, 640 * k)], fill=255)
    c.shape(toad, (150, 30, 30))

    def spots(d, k):
        for x, y, r in ((cx - 100, 230, 22), (cx + 20, 190, 26), (cx + 120, 250, 18), (cx - 30, 260, 14), (cx + 70, 290, 12)):
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
    c.shape(spots, (230, 220, 196))
    c.shape(lambda d, k: d.polygon([((cx - 60) * k, 300 * k), ((cx + 60) * k, 300 * k), ((cx + 80) * k, 640 * k), ((cx - 80) * k, 640 * k)],
                                   fill=255), (210, 196, 160))
    c.text("Fly Agaric - LOOK, never eat", "hand", cx, 700, 540, 40, colour=SEPIA)
    c.text("grows in rings. bad luck to step in.", "hand", cx, 750, 540, 30, colour=SEPIA)
    return c


def note_chores():
    c = page_cell(4780, 600, 800)
    c.text("To Do", "print", 300, 70, 300, 56, colour=INK)
    lines = ["- feed Soot (fish, NOT the newts)", "- patch the thatch", "- sweep the ring", "- return Mrs. Hob's kettle",
             "- dry the moonwort", "- sharpen sickle", "- stir the pot!!"]
    g = random.Random(4781)
    for i, ln in enumerate(lines):
        c.text(ln, "hand", 50, 160 + i * 82, 500, 38, colour=SEPIA, anchor="lm", angle=g.uniform(-2, 2))

    def ticks(d, k):
        for i in (1, 4):
            y = 160 + i * 82
            d.line([(40 * k, y * k), (540 * k, (y - 4) * k)], fill=255, width=int(3 * k))
    c.shape(ticks, RUST)
    return c


# ------------------------------------------------------------------ spellbook spines

SPINES = [((60, 34, 22), "Herbal"), ((34, 42, 28), "Of Moons"), ((52, 24, 46), "Hexes"), ((82, 58, 34), "Charms II"),
          ((30, 28, 36), "Familiars"), ((90, 30, 24), "Cures"), ((44, 54, 50), "Weather"), ((70, 52, 40), "Dreams"),
          ((24, 22, 20), "Shadows"), ((96, 76, 50), "Recipes")]


def spine(i):
    col, title = SPINES[i]
    W, H = 160, 800
    c = Cell(W, H, col, grain=12, seed=4790 + i, vignette=0.35)
    # raised cords across the spine and a stitched seam
    for y in (110, 300, 500, 690):
        c.shape(lambda d, k, y=y: d.rectangle([0, (y - 12) * k, W * k, (y + 12) * k], fill=255), tuple(min(255, v + 22) for v in col), height=190)
    c.shape(lambda d, k: d.line([(W / 2 * k, 0), (W / 2 * k, H * k)], fill=255, width=int(2 * k)), (34, 26, 18))
    m = c.fit(title, ("hand", "print", "script")[i % 3], H - 300, 74)
    m = m.rotate(90, expand=True, resample=Image.BICUBIC)
    c.stamp(m, W / 2, H / 2 + 6, (214, 198, 160), height=150)
    if i % 3 == 0:
        c.shape(lambda d, k: moon(d, k, W / 2, 60, 22, 0.5), (200, 170, 100), height=170)
    return c


# ------------------------------------------------------------------ the quilt

def quilt():
    W = H = 1400
    c = Cell(W, H, (40, 30, 30), grain=4, seed=4800)
    g = random.Random(4801)
    cols = [(96, 22, 30), (58, 30, 78), (52, 66, 36), (150, 110, 48), (34, 44, 74), (110, 78, 60), (70, 20, 46), (130, 120, 96),
            (40, 52, 46), (84, 40, 22)]
    n = 7
    step = W / n
    for i in range(n):
        for j in range(n):
            x0, y0 = i * step, j * step
            jit = [g.uniform(-14, 14) for _ in range(8)]
            poly = [(x0 + jit[0], y0 + jit[1]), (x0 + step + jit[2], y0 + jit[3]), (x0 + step + jit[4], y0 + step + jit[5]),
                    (x0 + jit[6], y0 + step + jit[7])]
            col = cols[g.randrange(len(cols))]
            c.shape(lambda d, k, poly=poly: d.polygon([(x * k, y * k) for x, y in poly], fill=255), col, height=140)
            # cloth pattern on some patches: stripes, dots, checks
            kind = g.randrange(5)
            lt = tuple(min(255, v + 46) for v in col)
            cx, cy = x0 + step / 2, y0 + step / 2
            if kind == 0:
                def dr(d, k, x0=x0, y0=y0):
                    for t in range(0, int(step), 22):
                        d.line([((x0 + t) * k, (y0 + 8) * k), ((x0 + t) * k, (y0 + step - 8) * k)], fill=255, width=int(6 * k))
                c.shape(dr, lt, height=140)
            elif kind == 1:
                def dr(d, k, x0=x0, y0=y0):
                    for a in range(14, int(step) - 8, 30):
                        for b in range(14, int(step) - 8, 30):
                            d.ellipse([(x0 + a - 5) * k, (y0 + b - 5) * k, (x0 + a + 5) * k, (y0 + b + 5) * k], fill=255)
                c.shape(dr, lt, height=140)
            elif kind == 2:
                def dr(d, k, x0=x0, y0=y0):
                    for a in range(0, int(step), 40):
                        for b in range(0, int(step), 40):
                            if (a // 40 + b // 40) % 2 == 0:
                                d.rectangle([(x0 + a + 6) * k, (y0 + b + 6) * k, (x0 + a + 40) * k, (y0 + b + 40) * k], fill=255)
                c.shape(dr, lt, height=140)
            elif kind == 3:      # an embroidered moon or star in bone thread
                if g.random() < 0.5:
                    c.shape(lambda d, k, cx=cx, cy=cy: moon(d, k, cx, cy, step * 0.26, 0.55), (214, 200, 160), height=170)
                else:
                    c.shape(lambda d, k, cx=cx, cy=cy: star(d, k, cx, cy, step * 0.28), (214, 200, 160), height=170)
            # running stitches round the patch
            def stitch(d, k, poly=poly):
                for a, b in zip(poly, poly[1:] + poly[:1]):
                    L = math.hypot(b[0] - a[0], b[1] - a[1])
                    m = int(L / 18)
                    for s in range(m):
                        if s % 2:
                            continue
                        t0, t1 = s / m, (s + 0.6) / m
                        p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
                        p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
                        # inset the stitches 8 px toward the patch centre
                        q0 = [p0[0] + (cx - p0[0]) * 0.06, p0[1] + (cy - p0[1]) * 0.06]
                        q1 = [p1[0] + (cx - p1[0]) * 0.06, p1[1] + (cy - p1[1]) * 0.06]
                        d.line([(q0[0] * k, q0[1] * k), (q1[0] * k, q1[1] * k)], fill=255, width=int(3 * k))
            c.shape(stitch, (210, 196, 160), height=165)
    return c


# ------------------------------------------------------------------ the braided rag rug

def rug():
    """Concentric braided coils (u across the rug's length, v across its width; the oval's rim on the cell edge): each coil
    a three-strand braid shown as chevrons, the strands in faded rag colours, the colours changing every few coils."""
    W, H = 1400, 1000
    c = Cell(W, H, (60, 46, 36), grain=4, seed=4810)
    g = random.Random(4811)
    rags = [(110, 40, 38), (60, 48, 80), (78, 92, 60), (150, 128, 92), (46, 56, 80), (128, 76, 46), (90, 70, 60), (170, 150, 120),
            (70, 30, 50)]
    n = 16
    cx, cy = W / 2, H / 2
    a, b = W / 2, H / 2
    band = []
    for r in range(n):
        if r % 3 == 0:
            band = [rags[g.randrange(len(rags))] for _ in range(3)]
        k0 = 1 - r / n
        k1 = 1 - (r + 1) / n
        # chevrons round the ring
        m = int(80 * k0) + 12
        for s in range(m):
            t0 = s / m * 2 * math.pi
            t1 = (s + 1) / m * 2 * math.pi
            tm = (t0 + t1) / 2
            col = band[s % 3]
            pts = [(cx + math.cos(t0) * a * k0, cy + math.sin(t0) * b * k0),
                   (cx + math.cos(tm) * a * (k0 + k1) / 2 * 1.0, cy + math.sin(tm) * b * (k0 + k1) / 2),
                   (cx + math.cos(t0) * a * k1, cy + math.sin(t0) * b * k1),
                   (cx + math.cos(t1) * a * k1, cy + math.sin(t1) * b * k1),
                   (cx + math.cos(t1 + (t1 - t0) * 0.5) * a * (k0 + k1) / 2, cy + math.sin(t1 + (t1 - t0) * 0.5) * b * (k0 + k1) / 2),
                   (cx + math.cos(t1) * a * k0, cy + math.sin(t1) * b * k0)]
            c.shape(lambda d, k, pts=pts: d.polygon([(x * k, y * k) for x, y in pts], fill=255), col, height=150)
        # the groove between coils
        def gr(d, k, k1=k1):
            d.ellipse([(cx - a * k1) * k, (cy - b * k1) * k, (cx + a * k1) * k, (cy + b * k1) * k], outline=255, width=int(4 * k))
        c.shape(gr, (30, 22, 18), height=60)
    return c


# ------------------------------------------------------------------ the door's hex sign and the charm sigils

def hex_sign():
    W = H = 500
    c = Cell(W, H, (36, 28, 22), grain=6, seed=4820)
    cx = cy = W / 2
    c.shape(lambda d, k: d.ellipse([10 * k, 10 * k, (W - 10) * k, (H - 10) * k], fill=255), (148, 118, 74), height=150)
    c.shape(lambda d, k: d.ellipse([34 * k, 34 * k, (W - 34) * k, (H - 34) * k], outline=255, width=int(8 * k)), (92, 22, 30), height=170)

    def rosette(d, k):
        for i in range(6):
            a = i * math.pi / 3
            x, y = cx + math.cos(a) * 95, cy + math.sin(a) * 95
            d.ellipse([(x - 95) * k, (y - 95) * k, (x + 95) * k, (y + 95) * k], outline=255, width=int(6 * k))
    c.shape(rosette, (40, 30, 54), height=170)
    c.shape(lambda d, k: moon(d, k, cx, cy, 50, 0.5), (220, 200, 150), height=180)

    def dots(d, k):
        for i in range(12):
            a = i * math.pi / 6 + math.pi / 12
            x, y = cx + math.cos(a) * 196, cy + math.sin(a) * 196
            d.ellipse([(x - 9) * k, (y - 9) * k, (x + 9) * k, (y + 9) * k], fill=255)
    c.shape(dots, (220, 200, 150), height=170)
    return c


def sigil(i):
    W = H = 200
    c = Cell(W, H, (128, 94, 60), grain=10, seed=4830 + i)
    burnt_edges(c, 0.3, 4835 + i, col=(40, 26, 14))
    cx = cy = 100
    col = (34, 22, 14)

    def dr(d, k):
        w = int(9 * k)
        if i == 0:      # an eye-less moon over three dots
            moon(d, k, cx, cy - 20, 42, 0.5)
            for x in (70, 100, 130):
                d.ellipse([(x - 8) * k, 150 * k, (x + 8) * k, 166 * k], fill=255)
        elif i == 1:    # a star in a ring of dots
            d.ellipse([28 * k, 28 * k, 172 * k, 172 * k], outline=255, width=w)
            star(d, k, cx, cy, 46)
        elif i == 2:    # a triple spiral
            for j in range(3):
                a0 = j * 2 * math.pi / 3
                pts = []
                for s in range(40):
                    t = s / 39
                    a = a0 + t * 4.5
                    r = 8 + t * 52
                    pts.append(((cx + math.cos(a) * r) * k, (cy + math.sin(a) * r) * k))
                d.line(pts, fill=255, width=int(7 * k), joint="curve")
        elif i == 3:    # a crossed sigil with forked ends
            d.line([(cx * k, 30 * k), (cx * k, 170 * k)], fill=255, width=w)
            d.line([(40 * k, 90 * k), (160 * k, 90 * k)], fill=255, width=w)
            for s in (-1, 1):
                d.line([(cx * k, 170 * k), ((cx + s * 30) * k, 140 * k)], fill=255, width=w)
                d.line([((cx + s * 60) * k, 90 * k), ((cx + s * 60) * k, 60 * k)], fill=255, width=w)
        elif i == 4:    # an acorn
            d.ellipse([60 * k, 70 * k, 140 * k, 170 * k], fill=255)
            d.chord([50 * k, 40 * k, 150 * k, 110 * k], 180, 360, fill=255)
            d.line([(cx * k, 40 * k), ((cx + 12) * k, 20 * k)], fill=255, width=int(7 * k))
        else:           # a triquetra of three overlapping rings
            for j in range(3):
                a = -math.pi / 2 + j * 2 * math.pi / 3
                x, y = cx + math.cos(a) * 30, cy + math.sin(a) * 30
                d.ellipse([(x - 46) * k, (y - 46) * k, (x + 46) * k, (y + 46) * k], outline=255, width=int(7 * k))
    c.shape(dr, col, height=70)
    return c


if __name__ == "__main__":
    a = Atlas("WitchPrint", bg=(54, 40, 30))
    a.put("Quilt", quilt(), 1.0)
    a.put("Rug", rug(), 1.0)
    a.put("PageL", page_left(), 1.0)
    a.put("PageR", page_right(), 1.0)
    for i, fn in enumerate((note_calendar, note_remedy, note_toadstool, note_chores)):
        a.put(f"Note{i}", fn(), 1.0)
    for i in range(len(SPINES)):
        a.put(f"Spine{i}", spine(i), 1.0)
    for i in range(len(LABELS)):
        a.put(f"Label{i}", jar_label(i), 1.0)
    a.put("HexSign", hex_sign(), 1.0)
    for i in range(6):
        a.put(f"Sigil{i}", sigil(i), 1.0)
    for name, col, gr in (("parch", PARCH, 8), ("ink", (24, 22, 30), 3), ("wood", (128, 94, 60), 10), ("leather", (60, 34, 22), 10),
                          ("thread", (210, 196, 160), 4), ("wax", WAX, 4), ("page", (214, 196, 154), 6), ("black", (20, 18, 18), 2),
                          ("bone", (200, 186, 150), 5)):
        a.put(f"Swatch_{name}", swatch(col, gr, seed_of(name)))
    a.save()
    json.dump({"regions": {"WitchPrint": a.reg}}, open(os.path.join(HERE, "witchhut_atlas.json"), "w"), indent=0)
