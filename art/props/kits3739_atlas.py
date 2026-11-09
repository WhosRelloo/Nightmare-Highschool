"""Printed atlases for props batches 37 (detention), 38 (electives) and 39 (dorm house). System Python (PIL + numpy):

  python art/props/kits3739_atlas.py

DetentionPrint  the lines on the chalkboard ("I will not talk in class." in chalk), pages of lines, the detention register,
                the rules of the school, the CONFISCATED label, three comics, two phone screens, playing cards
ElectivesPrint  plant markers, the sewing machine's gilt decals, six fabric prints for the bolts, darkroom prints and tray labels,
                the pegboard of the tool wall (holes and painted tool outlines), the costume tabard
DormHousePrint  the resident adviser's sign-in book, the washing machine panel, fridge stickers and a note, the television's
                screen, shower tiles, the hoop's backboard, perfume labels, the ping-pong net

Writes art/props/textures/<Atlas>_{color,gilt,height}.png (4096) and art/props/kits3739_atlas.json (every region's UV rect, v up,
plus the tool wall's layout in studs). Uses dorm_atlas.py's Cell / Atlas machinery. All text, names and designs are original.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dorm_atlas as D
from dorm_atlas import Cell, Atlas, crest, scribble, lined, handwriting, swatch, seed_of, fleuron, rules, INK, CRIMSON, REDINK, GILT, PARCH

HERE = D.HERE
D.FONTS.update({"sym": D.F + "seguisym.ttf", "impact": D.F + "impact.ttf", "bahn": D.F + "bahnschrift.ttf", "cons": D.F + "consolab.ttf",
                "ui": D.F + "segoeuib.ttf", "uir": D.F + "segoeui.ttf", "comic": D.F + "comicbd.ttf", "blk": D.F + "ariblk.ttf"})
SS = D.SS
BLUEINK = (28, 34, 78)
PENCIL = (70, 70, 76)
BONE = (214, 200, 168)


def noise(w, h, cell, seed, lo=0.0, hi=1.0):
    g = np.random.default_rng(seed)
    m = g.uniform(0, 255, (max(2, h // cell), max(2, w // cell)))
    a = np.asarray(Image.fromarray(np.uint8(m)).resize((w, h), Image.BICUBIC), np.float32) / 255
    return lo + (hi - lo) * a


def chalky(m, seed, keep=0.75):
    """Break a text mask up like chalk on slate: a fine grain knocked out of the strokes, a little softer at the edges."""
    a = np.asarray(m, np.float32)
    g = np.random.default_rng(seed)
    grain = g.uniform(0, 1, a.shape)
    streak = noise(a.shape[1], a.shape[0], 5, seed + 1)
    k = np.clip((grain * 0.6 + streak * 0.6) - (1 - keep) + 0.25, 0, 1)
    return Image.fromarray(np.uint8(np.clip(a * k, 0, 255))).filter(ImageFilter.GaussianBlur(0.6))


def shapes(c, colour, fn, height=None, metal=0):
    c.shape(lambda d, k: fn(d, k), colour, metal=metal, height=height)


# ================================================================== batch 37: detention

LINE = "I will not talk in class."


def lines_board():
    """The slate covered in lines: the same sentence row after row in a schoolchild's chalk, sloping a little, the last rows
    hurried, an old smear of eraser through the slate."""
    W, H = 2000, 1150
    c = Cell(W, H, (34, 42, 40), grain=10, seed=3701, vignette=0.15)
    g = random.Random(3701)
    # old chalk ghosts and eraser smears
    for _ in range(9):
        x, y = g.uniform(0, W), g.uniform(0, H)
        rw, rh = g.uniform(160, 420), g.uniform(40, 90)
        m = Image.new("L", (W * SS, H * SS), 0)
        ImageDraw.Draw(m).ellipse([(x - rw) * SS, (y - rh) * SS, (x + rw) * SS, (y + rh) * SS], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(30 * SS)).point(lambda v: int(v * 0.16))
        c.stamp(m, 0, 0, (150, 160, 154), anchor="lt")
    rows = 13
    for i in range(rows):
        y = 70 + i * (H - 120) / rows
        x = 70 + g.uniform(-14, 14)
        size = 78 + g.uniform(-4, 4)
        fk = "hand" if i < 9 else "print"
        m = c.fit(LINE + "   " + LINE, fk, W - 150 - g.uniform(0, 60), size, bold=0.7)
        m = chalky(m, 3701 + i, keep=0.8 if i < 10 else 0.65)
        c.stamp(m, x, y + 30, (226, 228, 218), anchor="lm", angle=g.uniform(-0.9, 0.5))
    # a tally of how many done, top right, and the teacher's note
    c.text("x 26", "hand", W - 90, 50, 130, 50, colour=(230, 226, 206))
    return c


def lines_page(seed, rows=22, messy=0.0):
    W, H = 700, 920
    c = Cell(W, H, (236, 232, 218), grain=4, seed=seed, fibres=True)
    lined(c, 26, W - 26, 110, H - 30, 36, margin=86)
    g = random.Random(seed)
    c.text("Lines - Room 106", "hand", 110, 62, 360, 40, colour=BLUEINK, anchor="lm")
    c.text("x100", "hand", W - 90, 62, 120, 40, colour=REDINK)
    for i in range(rows):
        y = 110 + 36 * (i + 1) - 13
        if y > H - 40:
            break
        ang = g.uniform(-0.6, 0.6) + messy * g.uniform(-1.5, 1.5)
        c.text(LINE, "hand", 100 + g.uniform(-4, 6), y, W - 150 - messy * g.uniform(0, 80), 30, colour=PENCIL if seed % 2 else BLUEINK,
               anchor="lm", angle=ang)
    return c


REGISTER = [("Mon", "T. Ashgrove", "Talking in the corridor", "3.40", "5.00"), ("Mon", "R. Vale", "Late to Latin (again)", "3.40", "5.00"),
            ("Tue", "J. Morrow", "Skateboard in the hall", "3.40", "4.30"), ("Tue", "E. Finch", "Phone in class", "3.40", "5.00"),
            ("Wed", "P. Crane", "No homework", "3.40", "4.45"), ("Wed", "T. Ashgrove", "Talking in class", "3.40", "5.00"),
            ("Thu", "M. Holloway", "Out after curfew", "3.40", "5.30"), ("Thu", "S. Blackwood", "Soda in the library", "3.40", "4.30"),
            ("Fri", "R. Vale", "Running on the stairs", "3.40", "4.30"), ("Fri", "D. Quill", "Passing notes", "3.40", "4.45"),
            ("Fri", "J. Morrow", "Skateboard in the hall", "3.40", "5.00")]


def ledger_page(seed, entries, left=True):
    W, H = 700, 920
    c = Cell(W, H, (228, 216, 186), grain=6, seed=seed, vignette=0.18, fibres=True)
    if left:
        c.text("DETENTION REGISTER", "pala", W / 2, 46, 560, 40, colour=CRIMSON)
    else:
        c.text("Room 106  -  Supervisor: Mr. Hale", "palai", W / 2, 46, 560, 30, colour=INK)
    cols = [30, 108, 270, 520, 600, 670]
    heads = ["Day", "Name", "Offence", "In", "Out"]

    def grid(d, k):
        d.line([(30 * k, 84 * k), (670 * k, 84 * k)], fill=255, width=int(3 * k))
        d.line([(30 * k, 118 * k), (670 * k, 118 * k)], fill=255, width=int(2 * k))
        y = 118
        while y < H - 30:
            y += 52
            d.line([(30 * k, y * k), (670 * k, y * k)], fill=255, width=int(1.2 * k))
        for x in cols:
            d.line([(x * k, 84 * k), (x * k, (H - 30) * k)], fill=255, width=int(1.5 * k))
    c.shape(grid, (120, 60, 60))
    for i, h in enumerate(heads):
        c.text(h, "pala", (cols[i] + cols[i + 1]) / 2, 101, cols[i + 1] - cols[i] - 8, 24, colour=INK)
    g = random.Random(seed)
    for r, (day, name, why, tin, tout) in enumerate(entries):
        y = 118 + 52 * r + 30
        col = BLUEINK if g.random() > 0.3 else (20, 20, 24)
        for i, s in enumerate((day, name, why, tin, tout)):
            c.text(s, "hand", cols[i] + 6, y, cols[i + 1] - cols[i] - 12, 28, colour=col, anchor="lm", angle=g.uniform(-1.2, 1.2))
    return c


RULES = ["Silence in the corridors.", "No running on the stairs.", "Phones stay in your locker during lessons.",
         "No skateboards inside the school buildings.", "Be in your house before the curfew bell.", "The east wing is out of bounds.",
         "Wear your uniform in full at all times.", "Treat the library's books with care.", "Respect the staff, your fellow students and the school.",
         "Lights out at the midnight bell."]


def rules_board():
    W, H = 1100, 1500
    c = Cell(W, H, PARCH, grain=7, seed=3710, vignette=0.24, fibres=True)
    rules(c, 22, GILT, 8)
    rules(c, 40, CRIMSON, 3)
    for x, y in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
        fleuron(c, x, y, 22)
    crest(c, W / 2, 170, 200)
    c.text("NIGHTMARE  HIGH", "pala", W / 2, 305, 600, 44, colour=CRIMSON)
    c.text("The Rules of the School", "black", W / 2, 400, 920, 96, colour=INK, bold=1.2)
    c.shape(lambda d, k: d.line([(W * 0.2 * k, 470 * k), (W * 0.8 * k, 470 * k)], fill=255, width=int(3 * k)), CRIMSON)
    for i, r in enumerate(RULES):
        y = 540 + i * 74
        c.text(f"{i + 1}.", "pala", 120, y, 70, 46, colour=CRIMSON, anchor="rm")
        c.text(r, "palar", 140, y, W - 240, 42, colour=INK, anchor="lm")
    c.text("By order of the Headmaster", "palai", W / 2, 1310, 500, 34, colour=INK)
    scribble(c, W / 2 - 150, 1390, 300, 50, (30, 34, 70), 3711)
    c.shape(lambda d, k: d.line([((W / 2 - 180) * k, 1410 * k), ((W / 2 + 180) * k, 1410 * k)], fill=255, width=int(2 * k)), INK)
    return c


def confiscated():
    W, H = 1000, 280
    c = Cell(W, H, (196, 178, 140), grain=10, seed=3712)
    m = c.fit("CONFISCATED", "blk", W - 120, 160)
    a = np.asarray(m, np.float32) * noise(m.width, m.height, 7, 3712, 0.55, 1.15)
    m = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    c.stamp(m, W / 2, 120, (118, 18, 26))
    c.text("PROPERTY OF THE OFFICE  -  ROOM 106", "cons", W / 2, 236, 760, 34, colour=(40, 30, 26))
    return c


def comic(seed, title, sub, num, bg, band, figure):
    W, H = 500, 760
    c = Cell(W, H, bg, grain=8, seed=seed)
    # art: a gradient sky, a big moon, the figure
    sky = np.zeros((H * SS, W * SS, 3), np.float32)
    t = np.linspace(0, 1, H * SS)[:, None, None]
    top, bot = np.array(bg, np.float32), np.array(band, np.float32) * 0.5
    sky[:] = top * (1 - t) + bot * t
    c.c.paste(Image.fromarray(np.uint8(sky)), (0, 0))
    c.shape(lambda d, k: d.ellipse([260 * k, 200 * k, 470 * k, 410 * k], fill=255), (236, 226, 190))
    figure(c, W, H)
    # the masthead
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 150 * k], fill=255), band)
    c.text(title, "impact", W / 2, 72, W - 40, 110, colour=(250, 238, 200))
    c.shape(lambda d, k: d.rectangle([14 * k, 160 * k, 110 * k, 220 * k], fill=255), (250, 238, 200))
    c.text(f"No. {num}", "impact", 62, 190, 84, 40, colour=(20, 18, 24))
    c.shape(lambda d, k: d.rectangle([0, (H - 90) * k, W * k, H * k], fill=255), (250, 238, 200))
    c.text(sub, "comic", W / 2, H - 45, W - 40, 44, colour=band)
    return c


def fig_raven(c, W, H):
    def dr(d, k):
        pts = [(250, 470), (150, 430), (40, 470), (150, 470), (90, 520), (210, 500), (250, 560), (290, 500), (410, 520), (350, 470),
               (460, 470), (350, 430)]
        d.polygon([(x * k, y * k) for x, y in pts], fill=255)
        d.ellipse([228 * k, 430 * k, 272 * k, 474 * k], fill=255)
        d.polygon([(250 * k, 560 * k), (230 * k, 640 * k), (270 * k, 640 * k)], fill=255)
    c.shape(dr, (16, 14, 20))
    c.shape(lambda d, k: d.rectangle([0, 600 * k, W * k, 670 * k], fill=255), (30, 26, 34))


def fig_ghoul(c, W, H):
    def dr(d, k):
        for i, x in enumerate((110, 250, 390)):
            d.ellipse([(x - 60) * k, (420 - i % 2 * 20) * k, (x + 60) * k, (540 - i % 2 * 20) * k], fill=255)
            d.rectangle([(x - 60) * k, (480 - i % 2 * 20) * k, (x + 60) * k, 670 * k], fill=255)
            for j in range(4):
                d.polygon([((x - 60 + j * 30) * k, 670 * k), ((x - 45 + j * 30) * k, 640 * k), ((x - 30 + j * 30) * k, 670 * k)], fill=0)
    c.shape(dr, (196, 210, 200))

    def eyes(d, k):
        for i, x in enumerate((110, 250, 390)):
            for dx in (-22, 22):
                d.ellipse([(x + dx - 11) * k, (470 - i % 2 * 20) * k, (x + dx + 11) * k, (494 - i % 2 * 20) * k], fill=255)
    c.shape(eyes, (20, 20, 30))


def fig_wolf(c, W, H):
    def dr(d, k):
        pts = [(120, 670), (150, 520), (190, 470), (200, 400), (230, 440), (260, 420), (270, 360), (300, 430), (340, 470), (330, 540),
               (380, 670)]
        d.polygon([(x * k, y * k) for x, y in pts], fill=255)
        d.polygon([(40 * k, 670 * k), (W * k, 600 * k), (W * k, 670 * k)], fill=255)
    c.shape(dr, (22, 18, 30))
    c.shape(lambda d, k: d.ellipse([276 * k, 446 * k, 290 * k, 458 * k], fill=255), (240, 60, 40))


def phone_lock():
    W, H = 300, 620
    c = Cell(W, H, (16, 14, 26), grain=3, seed=3720)
    a = np.zeros((H * SS, W * SS, 3), np.float32)
    t = np.linspace(0, 1, H * SS)[:, None, None]
    a[:] = np.array([36, 20, 52], np.float32) * (1 - t) + np.array([8, 6, 14], np.float32) * t
    c.c.paste(Image.fromarray(np.uint8(a)), (0, 0))
    c.shape(lambda d, k: (d.ellipse([170 * k, 300 * k, 270 * k, 400 * k], fill=255), d.ellipse([150 * k, 290 * k, 245 * k, 385 * k], fill=0)),
            (232, 220, 190))
    c.text("11:47", "uir", W / 2, 110, 220, 80, colour=(236, 232, 240))
    c.text("Thursday", "uir", W / 2, 165, 160, 26, colour=(200, 196, 210))
    c.shape(lambda d, k: d.rounded_rectangle([20 * k, 450 * k, (W - 20) * k, 530 * k], 16 * k, fill=255), (60, 54, 74))
    c.text("Mum: where are you??", "uir", W / 2, 490, 240, 24, colour=(236, 232, 240))
    return c


def phone_apps():
    W, H = 300, 620
    c = Cell(W, H, (20, 20, 28), grain=3, seed=3721)
    g = random.Random(3721)
    cols = [(150, 30, 40), (40, 90, 140), (200, 150, 60), (60, 120, 70), (120, 60, 140), (220, 220, 210), (30, 30, 30), (180, 80, 40)]
    for r in range(5):
        for q in range(4):
            x, y = 30 + q * 64, 90 + r * 80
            col = g.choice(cols)
            c.shape(lambda d, k, x=x, y=y: d.rounded_rectangle([x * k, y * k, (x + 48) * k, (y + 48) * k], 12 * k, fill=255), col)
    c.text("9:12", "uir", 40, 30, 80, 24, colour=(230, 230, 236))

    def crack(d, k):
        for _ in range(9):
            x, y = 210, 160
            a = g.uniform(0, 6.28)
            for _ in range(6):
                nx, ny = x + math.cos(a) * g.uniform(20, 60), y + math.sin(a) * g.uniform(20, 60)
                d.line([(x * k, y * k), (nx * k, ny * k)], fill=255, width=int(1.6 * k))
                x, y, a = nx, ny, a + g.uniform(-0.6, 0.6)
    c.shape(crack, (236, 236, 240))
    return c


def card(kind):
    W, H = 250, 350
    if kind == "back":
        c = Cell(W, H, (240, 236, 226), grain=2, seed=3730)
        c.shape(lambda d, k: d.rounded_rectangle([12 * k, 12 * k, (W - 12) * k, (H - 12) * k], 10 * k, fill=255), (120, 18, 30))

        def lat(d, k):
            for i in range(-12, 24):
                d.line([((12 + i * 24) * k, 12 * k), ((12 + i * 24 + 330) * k, (H - 12) * k)], fill=255, width=int(2 * k))
                d.line([((12 + i * 24) * k, (H - 12) * k), ((12 + i * 24 + 330) * k, 12 * k)], fill=255, width=int(2 * k))
        m = Image.new("L", (W * SS, H * SS), 0)
        lat(ImageDraw.Draw(m), SS)
        clip = Image.new("L", (W * SS, H * SS), 0)
        ImageDraw.Draw(clip).rectangle([22 * SS, 22 * SS, (W - 22) * SS, (H - 22) * SS], fill=255)
        m = Image.fromarray(np.minimum(np.asarray(m), np.asarray(clip)))
        c.stamp(m, 0, 0, (206, 164, 86), anchor="lt")
        return c
    c = Cell(W, H, (244, 240, 230), grain=2, seed=seed_of(kind))
    rank, suit, col = {"ace": ("A", "♠", (20, 20, 24)), "queen": ("Q", "♥", (170, 20, 30)), "seven": ("7", "♣", (20, 20, 24))}[kind]
    c.text(rank, "pala", 34, 40, 50, 46, colour=col)
    c.text(suit, "sym", 34, 82, 40, 36, colour=col)
    c.text(rank, "pala", W - 34, H - 40, 50, 46, colour=col, angle=180)
    c.text(suit, "sym", W - 34, H - 82, 40, 36, colour=col, angle=180)
    if kind == "queen":
        c.shape(lambda d, k: d.rectangle([60 * k, 70 * k, (W - 60) * k, (H - 70) * k], outline=255, width=int(3 * k)), col)
        c.text("Q", "black", W / 2, H / 2, 110, 150, colour=col)
    else:
        c.text(suit, "sym", W / 2, H / 2, 150, 170 if kind == "ace" else 110, colour=col)
    return c


# ================================================================== batch 38: electives

HERBS = ["Sage", "Thyme", "Rosemary", "Mint", "Moonwort", "Lavender", "Rue", "Feverfew"]


def plant_label(name):
    W, H = 240, 80
    c = Cell(W, H, (222, 214, 190), grain=5, seed=seed_of(name))
    c.text(name, "hand", W / 2, H / 2, W - 30, 54, colour=(30, 30, 34))
    return c


def machine_decal():
    """The sewing machine's arm: black japanning with gilt scrollwork and the maker's name."""
    W, H = 1000, 300
    c = Cell(W, H, (14, 13, 16), grain=3, seed=3801)

    def scroll(d, k):
        for sx in (-1, 1):
            cx = W / 2 + sx * 360
            for i in range(5):
                r = 30 + i * 18
                d.arc([(cx - r) * k, (150 - r) * k, (cx + r) * k, (150 + r) * k], 200 if sx < 0 else -20, 340 if sx < 0 else 160, fill=255,
                      width=int(4 * k))
            for j in range(6):
                x = W / 2 + sx * (120 + j * 32)
                d.ellipse([(x - 7) * k, (60 - 7) * k, (x + 7) * k, (60 + 7) * k], fill=255)
                d.ellipse([(x - 7) * k, (240 - 7) * k, (x + 7) * k, (240 + 7) * k], fill=255)
        d.rectangle([20 * k, 18 * k, (W - 20) * k, 24 * k], fill=255)
        d.rectangle([20 * k, (H - 24) * k, (W - 20) * k, (H - 18) * k], fill=255)
    c.shape(scroll, GILT)
    c.text("RAVENSWORTH", "pala", W / 2, 150, 520, 90, colour=GILT)
    return c


def fabric(name):
    W = H = 512
    g = random.Random(seed_of(name))
    if name == "Plaid":
        c = Cell(W, H, (96, 14, 26), grain=6, seed=1)

        def dr(d, k):
            for i in range(0, W, 128):
                d.rectangle([(i + 20) * k, 0, (i + 60) * k, H * k], fill=255)
                d.rectangle([0, (i + 20) * k, W * k, (i + 60) * k], fill=255)
        c.shape(dr, (24, 22, 40))

        def thin(d, k):
            for i in range(0, W, 128):
                d.rectangle([(i + 92) * k, 0, (i + 96) * k, H * k], fill=255)
                d.rectangle([0, (i + 92) * k, W * k, (i + 96) * k], fill=255)
        c.shape(thin, (200, 170, 100))
    elif name == "Pinstripe":
        c = Cell(W, H, (26, 26, 34), grain=5, seed=2)
        c.shape(lambda d, k: [d.rectangle([i * k, 0, (i + 3) * k, H * k], fill=255) for i in range(0, W, 32)], (170, 168, 176))
    elif name == "Check":
        c = Cell(W, H, (214, 204, 182), grain=5, seed=3)
        c.shape(lambda d, k: [d.rectangle([x * k, y * k, (x + 32) * k, (y + 32) * k], fill=255) for x in range(0, W, 64) for y in range(0, H, 64)]
                + [d.rectangle([x * k, y * k, (x + 32) * k, (y + 32) * k], fill=255) for x in range(32, W, 64) for y in range(32, H, 64)],
                (30, 28, 34))
    elif name == "Dots":
        c = Cell(W, H, (34, 52, 46), grain=5, seed=4)
        c.shape(lambda d, k: [d.ellipse([(x - 9) * k, (y - 9) * k, (x + 9) * k, (y + 9) * k], fill=255)
                              for x in range(32, W, 64) for y in range(32, H, 64)] +
                [d.ellipse([(x - 9) * k, (y - 9) * k, (x + 9) * k, (y + 9) * k], fill=255) for x in range(0, W + 1, 64) for y in range(0, H + 1, 64)],
                (226, 214, 180))
    elif name == "Moths":
        c = Cell(W, H, (58, 26, 56), grain=5, seed=5)

        def moths(d, k):
            for x in range(64, W, 128):
                for y in range(64, H, 128):
                    ox = 64 if (y // 128) % 2 else 0
                    cx = (x + ox) % W
                    for sx in (-1, 1):
                        d.polygon([(cx * k, y * k), ((cx + sx * 34) * k, (y - 22) * k), ((cx + sx * 30) * k, (y + 4) * k),
                                   ((cx + sx * 20) * k, (y + 22) * k)], fill=255)
                    d.ellipse([(cx - 4) * k, (y - 14) * k, (cx + 4) * k, (y + 18) * k], fill=255)
        c.shape(moths, (196, 168, 110))
    else:  # Ticking
        c = Cell(W, H, (222, 214, 194), grain=5, seed=6)
        c.shape(lambda d, k: [d.rectangle([i * k, 0, (i + 14) * k, H * k], fill=255) for i in range(0, W, 48)], (96, 14, 26))
    return c


def photo(kind):
    """A gelatin print: a soft greyscale scene in a white border, faintly warm."""
    W, H = 400, 500
    c = Cell(W, H, (236, 234, 226), grain=2, seed=seed_of(kind))
    iw, ih = W - 40, H - 40
    im = Image.new("L", (iw * SS, ih * SS), 0)
    a = np.zeros((ih * SS, iw * SS), np.float32)
    t = np.linspace(0, 1, ih * SS)[:, None]
    a[:] = 190 * (1 - t) + 60 * t
    im = Image.fromarray(np.uint8(a))
    d = ImageDraw.Draw(im)
    k = SS
    if kind == "Tower":
        d.polygon([(150 * k, ih * k), (150 * k, 160 * k), (180 * k, 60 * k), (210 * k, 160 * k), (210 * k, ih * k)], fill=24)
        d.rectangle([0, 330 * k, iw * k, ih * k], fill=30)
        for x in (40, 100, 260, 310):
            d.polygon([(x * k, 330 * k), ((x + 20) * k, 280 * k), ((x + 40) * k, 330 * k)], fill=30)
        d.rectangle([172 * k, 190 * k, 188 * k, 220 * k], fill=220)
    elif kind == "Raven":
        d.line([(0, 330 * k), (iw * k, 300 * k)], fill=30, width=12 * k)
        d.ellipse([140 * k, 200 * k, 230 * k, 310 * k], fill=20)
        d.ellipse([200 * k, 170 * k, 250 * k, 220 * k], fill=20)
        d.polygon([(245 * k, 190 * k), (290 * k, 200 * k), (245 * k, 206 * k)], fill=20)
        d.polygon([(150 * k, 290 * k), (90 * k, 330 * k), (160 * k, 310 * k)], fill=20)
    elif kind == "Tree":
        d.ellipse([230 * k, 60 * k, 320 * k, 150 * k], fill=235)
        d.rectangle([0, 380 * k, iw * k, ih * k], fill=40)

        def branch(x, y, a, L, w, n):
            if n == 0 or L < 6:
                return
            nx, ny = x + math.cos(a) * L, y - math.sin(a) * L
            d.line([(x * k, y * k), (nx * k, ny * k)], fill=26, width=max(1, int(w * k)))
            branch(nx, ny, a + 0.45, L * 0.72, w * 0.68, n - 1)
            branch(nx, ny, a - 0.4, L * 0.7, w * 0.68, n - 1)
        branch(170, 390, math.pi / 2, 110, 18, 7)
    else:  # Face: a school portrait
        d.rectangle([0, 0, iw * k, ih * k], fill=150)
        d.ellipse([120 * k, 90 * k, 240 * k, 240 * k], fill=200)
        d.polygon([(60 * k, ih * k), (90 * k, 300 * k), (180 * k, 260 * k), (270 * k, 300 * k), (300 * k, ih * k)], fill=40)
        d.polygon([(165 * k, 270 * k), (180 * k, 340 * k), (195 * k, 270 * k)], fill=210)
        d.ellipse([110 * k, 70 * k, 250 * k, 150 * k], fill=40)
    im = im.filter(ImageFilter.GaussianBlur(2.2 * SS))
    g = np.asarray(im, np.float32)[..., None]
    sep = np.concatenate([g * 1.0, g * 0.95, g * 0.86], axis=2)
    sep += np.random.default_rng(seed_of(kind)).normal(0, 5, sep.shape[:2])[..., None]
    c.c.paste(Image.fromarray(np.uint8(np.clip(sep, 0, 255))), (20 * SS, 20 * SS))
    return c


def tray_label(word, col):
    W, H = 360, 110
    c = Cell(W, H, (230, 224, 206), grain=4, seed=seed_of(word))
    c.shape(lambda d, k: d.rectangle([8 * k, 8 * k, (W - 8) * k, (H - 8) * k], outline=255, width=int(5 * k)), col)
    c.text(word, "pala", W / 2, H / 2, W - 60, 60, colour=col)
    return c


# the tool wall: board 6.0 x 3.6 studs; each tool (kind, cx, cz, length, angle deg, present) in studs from the board's centre
TOOLS = [("saw", -2.05, 0.75, 1.7, 0, True), ("saw", -2.05, -0.35, 1.4, 0, False), ("hammer", -0.75, 1.05, 0.95, 90, True),
         ("mallet", -0.25, 1.05, 0.9, 90, True), ("square", 0.45, 0.95, 0.9, 0, True), ("brace", 1.55, 0.85, 1.1, 0, True),
         ("chisel", -0.95, -0.45, 0.75, 90, True), ("chisel", -0.7, -0.45, 0.75, 90, True), ("chisel", -0.45, -0.45, 0.75, 90, False),
         ("chisel", -0.2, -0.45, 0.7, 90, True), ("clamp", 0.55, -0.55, 0.8, 0, True), ("clamp", 1.25, -0.55, 0.8, 0, False),
         ("plane", 2.15, -0.6, 0.85, 0, True), ("rasp", 2.45, 0.85, 0.95, 90, True)]
BOARD_W, BOARD_H = 6.0, 3.6


def tool_outline(d, k, kind, cx, cy, L, ang, ppu):
    """Draw a tool's silhouette (pixel centre cx, cy, length L studs) for the painted outline."""
    def P(u, v):
        a = math.radians(ang)
        x, y = u * math.cos(a) - v * math.sin(a), u * math.sin(a) + v * math.cos(a)
        return ((cx + x * ppu) * k, (cy - y * ppu) * k)

    def poly(pts):
        d.polygon([P(u, v) for u, v in pts], fill=255)
    h = L / 2
    if kind == "saw":
        poly([(-h, 0.12), (h * 0.55, 0.16), (h * 0.55, -0.22), (-h, -0.06)])
        poly([(h * 0.5, 0.2), (h, 0.2), (h, -0.26), (h * 0.5, -0.26)])
    elif kind in ("hammer", "mallet"):
        poly([(-h, -0.04), (h * 0.6, -0.04), (h * 0.6, 0.04), (-h, 0.04)])
        w = 0.2 if kind == "hammer" else 0.16
        poly([(h * 0.55, -w), (h, -w), (h, w), (h * 0.55, w)] if kind == "mallet" else [(h * 0.6, -0.22), (h * 0.85, -0.22), (h * 0.85, 0.22), (h * 0.6, 0.22)])
    elif kind == "square":
        poly([(-h, 0.4), (-h + 0.12, 0.4), (-h + 0.12, -0.4), (-h, -0.4)])
        poly([(-h, -0.4), (h, -0.4), (h, -0.3), (-h, -0.3)])
    elif kind == "brace":
        pts = [(-h, 0), (-h * 0.6, 0), (-h * 0.5, 0.3), (h * 0.3, 0.3), (h * 0.4, 0), (h, 0)]
        for a, b in zip(pts, pts[1:]):
            d.line([P(*a), P(*b)], fill=255, width=int(0.07 * ppu * k))
        d.ellipse([P(-h - 0.08, 0.1)[0], P(-h - 0.08, 0.1)[1], P(-h + 0.12, -0.1)[0], P(-h + 0.12, -0.1)[1]], fill=255)
    elif kind == "chisel":
        poly([(-h, -0.03), (h * 0.1, -0.03), (h * 0.1, 0.03), (-h, 0.03)])
        poly([(h * 0.1, -0.05), (h, -0.05), (h, 0.05), (h * 0.1, 0.05)])
    elif kind == "clamp":
        poly([(-h, 0.3), (h, 0.3), (h, 0.2), (-h, 0.2)])
        poly([(-h, 0.3), (-h + 0.1, 0.3), (-h + 0.1, -0.3), (-h, -0.3)])
        poly([(h - 0.1, 0.3), (h, 0.3), (h, -0.1), (h - 0.1, -0.1)])
        poly([(-h, -0.3), (-h + 0.35, -0.3), (-h + 0.35, -0.2), (-h, -0.2)])
    elif kind == "plane":
        poly([(-h, -0.12), (h, -0.12), (h * 0.8, 0.1), (-h * 0.8, 0.1)])
        poly([(-h * 0.2, 0.1), (h * 0.2, 0.1), (h * 0.1, 0.28), (-h * 0.3, 0.28)])
    elif kind == "rasp":
        poly([(-h, -0.04), (h * 0.3, -0.04), (h * 0.3, 0.04), (-h, 0.04)])
        poly([(h * 0.3, -0.06), (h, -0.03), (h, 0.03), (h * 0.3, 0.06)])


def pegboard():
    W, H = 1600, 960
    ppu = W / BOARD_W
    c = Cell(W, H, (52, 36, 26), grain=9, seed=3810)
    # the outlines, a little wider than the tools, painted bone
    m = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    for kind, x, z, L, ang, _ in TOOLS:
        tool_outline(d, SS, kind, W / 2 + x * ppu, H / 2 - z * ppu, L, ang, ppu)
    grow = m.filter(ImageFilter.MaxFilter(2 * int(6 * SS) + 1))
    edge = Image.fromarray(np.uint8(np.clip(np.asarray(grow, np.int16) - np.asarray(m.filter(ImageFilter.MaxFilter(2 * int(2 * SS) + 1)), np.int16), 0, 255)))
    fill = m.point(lambda v: int(v * 0.35))
    c.stamp(fill, 0, 0, (226, 214, 186), anchor="lt")
    c.stamp(edge, 0, 0, (236, 226, 200), anchor="lt")

    def holes(d, k):
        step = ppu / 4
        y = step / 2
        while y < H:
            x = step / 2
            while x < W:
                d.ellipse([(x - 5) * k, (y - 5) * k, (x + 5) * k, (y + 5) * k], fill=255)
                x += step
            y += step
    c.shape(holes, (14, 10, 8), height=40)
    return c


def tabard():
    """The armour tabard's flat pattern (its outline is the costume rack's TABARD polygon): crimson, a gilt border, a gilt key."""
    W, H = 600, 1000
    c = Cell(W, H, (110, 16, 28), grain=10, seed=3820)
    c.shape(lambda d, k: d.rectangle([14 * k, 14 * k, (W - 14) * k, (H - 14) * k], outline=255, width=int(22 * k)), GILT)

    def key(d, k):
        cx = W / 2
        d.ellipse([(cx - 80) * k, 240 * k, (cx + 80) * k, 400 * k], outline=255, width=int(26 * k))
        d.rectangle([(cx - 16) * k, 390 * k, (cx + 16) * k, 760 * k], fill=255)
        d.rectangle([cx * k, 640 * k, (cx + 90) * k, 680 * k], fill=255)
        d.rectangle([cx * k, 710 * k, (cx + 70) * k, 750 * k], fill=255)
    c.shape(key, GILT)
    return c


def bricks():
    """Kiln firebrick: buff-to-soot bricks in running bond, pale mortar, scorched toward the top."""
    W = H = 1024
    c = Cell(W, H, (150, 138, 120), grain=6, seed=3830)
    g = random.Random(3830)
    bw, bh = 128, 56
    for r in range(H // bh + 1):
        off = (r % 2) * bw / 2
        for q in range(-1, W // bw + 1):
            x0, y0 = q * bw + off, r * bh
            soot = max(0.0, 1 - y0 / H * 1.6)
            base = (176 + g.uniform(-14, 10), 140 + g.uniform(-12, 8), 100 + g.uniform(-10, 8))
            col = tuple(int(v * (1 - 0.6 * soot) + 20 * soot) for v in base)
            c.shape(lambda d, k, x0=x0, y0=y0: d.rectangle([(x0 + 4) * k, (y0 + 4) * k, (x0 + bw - 4) * k, (y0 + bh - 4) * k], fill=255), col, height=160)
    return c


# ================================================================== batch 39: dorm house

SIGNIN = [("7.10", "Wren Holloway", "212", "out - library"), ("7.25", "Theo Ashgrove", "118", "out - town"),
          ("8.02", "Mara Finch", "204", "back"), ("8.15", "Jude Morrow", "121", "out - skate park"), ("8.40", "Theo Ashgrove", "118", "back"),
          ("9.05", "Iris Crane", "209", "visitor: sister"), ("9.30", "Jude Morrow", "121", "back (late!)"), ("9.58", "Wren Holloway", "212", "back"),
          ("10.20", "Sol Blackwood", "126", "out - kitchen?"), ("10.31", "Sol Blackwood", "126", "back")]


def signin_page(seed, entries, left):
    W, H = 700, 920
    c = Cell(W, H, (232, 224, 200), grain=5, seed=seed, vignette=0.15, fibres=True)
    c.text("RESIDENCE SIGN-IN" if left else "Thursday", "pala" if left else "palai", W / 2, 46, 560, 38, colour=CRIMSON if left else INK)
    cols = [30, 120, 330, 420, 670]

    def grid(d, k):
        d.line([(30 * k, 84 * k), (670 * k, 84 * k)], fill=255, width=int(3 * k))
        y = 118
        d.line([(30 * k, y * k), (670 * k, y * k)], fill=255, width=int(2 * k))
        while y < H - 30:
            y += 66
            d.line([(30 * k, y * k), (670 * k, y * k)], fill=255, width=int(1.2 * k))
        for x in cols:
            d.line([(x * k, 84 * k), (x * k, (H - 30) * k)], fill=255, width=int(1.5 * k))
    c.shape(grid, (60, 70, 110))
    for i, h in enumerate(("Time", "Name", "Room", "Where")):
        c.text(h, "pala", (cols[i] + cols[i + 1]) / 2, 101, cols[i + 1] - cols[i] - 8, 24, colour=INK)
    g = random.Random(seed)
    for r, row in enumerate(entries):
        y = 118 + 66 * r + 36
        col = g.choice([BLUEINK, (20, 20, 24), (90, 20, 60)])
        for i, s in enumerate(row):
            c.text(s, "hand", cols[i] + 8, y, cols[i + 1] - cols[i] - 14, 30, colour=col, anchor="lm", angle=g.uniform(-1.5, 1.5))
    return c


def washer_panel():
    W, H = 900, 220
    c = Cell(W, H, (20, 18, 22), grain=3, seed=3901)
    rules(c, 8, GILT, 4)
    c.text("RAVENWASH", "pala", 170, 70, 260, 60, colour=GILT)
    c.text("No. 9  -  automatic", "palai", 170, 140, 240, 30, colour=(200, 190, 170))
    labels = ["COTTON", "WOOL", "SILK", "RINSE", "SPIN", "DRAIN"]
    cx, cy = 520, 110
    for i, s in enumerate(labels):
        a = math.radians(150 + i * 48)
        c.text(s, "pala", cx + math.cos(a) * 92, cy - math.sin(a) * 78, 90, 20, colour=(220, 210, 190))
    for i, s in enumerate(("30", "40", "60", "90")):
        a = math.radians(140 - i * 34)
        c.text(s, "pala", 770 + math.cos(a) * 70, 110 - math.sin(a) * 66, 40, 22, colour=(220, 210, 190))
    c.text("TEMP", "pala", 770, 190, 80, 20, colour=GILT)
    return c


def sticker(kind):
    W = H = 220
    c = Cell(W, H, (238, 232, 216), grain=3, seed=seed_of(kind))
    if kind == "Bat":
        c.shape(lambda d, k: d.ellipse([10 * k, 10 * k, 210 * k, 210 * k], fill=255), (96, 14, 26))

        def bat(d, k):
            pts = [(110, 90), (80, 70), (30, 80), (50, 100), (40, 125), (75, 115), (110, 140), (145, 115), (180, 125), (170, 100), (190, 80),
                   (140, 70)]
            d.polygon([(x * k, y * k) for x, y in pts], fill=255)
            d.polygon([(98 * k, 82 * k), (102 * k, 64 * k), (110 * k, 80 * k), (118 * k, 64 * k), (122 * k, 82 * k)], fill=255)
        c.shape(bat, (20, 18, 24))
        c.text("NIGHT OWL", "impact", 110, 175, 150, 34, colour=(236, 226, 200))
    elif kind == "Moon":
        c.shape(lambda d, k: d.rounded_rectangle([6 * k, 6 * k, 214 * k, 214 * k], 30 * k, fill=255), (24, 26, 56))
        c.shape(lambda d, k: (d.ellipse([60 * k, 40 * k, 170 * k, 150 * k], fill=255), d.ellipse([40 * k, 30 * k, 140 * k, 130 * k], fill=0)),
                (236, 220, 170))
        c.text("MOON SODA", "impact", 110, 185, 180, 34, colour=(236, 220, 170))
    elif kind == "Skull":
        c.shape(lambda d, k: d.ellipse([10 * k, 10 * k, 210 * k, 210 * k], fill=255), (20, 20, 22))
        c.shape(lambda d, k: (d.ellipse([60 * k, 45 * k, 160 * k, 140 * k], fill=255), d.rectangle([80 * k, 120 * k, 140 * k, 170 * k], fill=255)),
                (226, 216, 190))
        c.shape(lambda d, k: (d.ellipse([78 * k, 80 * k, 104 * k, 108 * k], fill=255), d.ellipse([116 * k, 80 * k, 142 * k, 108 * k], fill=255),
                              [d.rectangle([(88 + i * 14) * k, 150 * k, (92 + i * 14) * k, 170 * k], fill=255) for i in range(4)]), (20, 20, 22))
    else:  # Note: a fridge note
        c = Cell(W, H, (240, 228, 150), grain=4, seed=3905)
        handwriting(c, ["LABEL YOUR", "FOOD!!", "- the RA"], 24, 50, 54, 40, colour=(30, 30, 40))
    return c


def tv_screen():
    """CRYPT CRAWLER's title screen on a modern 16:9 panel: a violet night over a crimson-lit crypt, the title in crimson."""
    W, H = 960, 540
    c = Cell(W, H, (16, 8, 30), grain=2, seed=3910)
    sky = np.zeros((H * SS, W * SS, 3), np.float32)
    t = np.linspace(0, 1, H * SS)[:, None, None]
    sky[:] = np.array([20, 8, 40], np.float32) * (1 - t) + np.array([90, 20, 70], np.float32) * t
    c.c.paste(Image.fromarray(np.uint8(sky)), (0, 0))
    g = random.Random(3910)
    c.shape(lambda d, k: [d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
                          for x, y, r in [(g.uniform(0, W), g.uniform(0, 260), g.uniform(1, 2.6)) for _ in range(90)]], (230, 220, 255))
    c.shape(lambda d, k: d.ellipse([820 * k, 30 * k, 920 * k, 130 * k], fill=255), (236, 214, 230))
    c.shape(lambda d, k: d.ellipse([805 * k, 18 * k, 895 * k, 112 * k], fill=255), (36, 12, 56))
    glow = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(glow).ellipse([260 * SS, 300 * SS, 700 * SS, 620 * SS], fill=255)
    c.stamp(glow.filter(ImageFilter.GaussianBlur(60 * SS)).point(lambda v: int(v * 0.6)), 0, 0, (200, 30, 50), anchor="lt")

    def crypt(d, k):
        base = 470
        for x0, w, h in ((200, 110, 170), (310, 340, 120), (650, 110, 170), (440, 80, 250)):
            d.rectangle([x0 * k, (base - h) * k, (x0 + w) * k, base * k], fill=255)
            d.polygon([(x0 * k, (base - h) * k), ((x0 + w / 2) * k, (base - h - w * 0.6) * k), ((x0 + w) * k, (base - h) * k)], fill=255)
        d.rectangle([0, base * k, W * k, H * k], fill=255)
    c.shape(crypt, (24, 10, 34))
    c.shape(lambda d, k: [d.rounded_rectangle([x * k, y * k, (x + 16) * k, (y + 30) * k], 8 * k, fill=255) for x, y in ((245, 370), (695, 370), (472, 300))],
            (255, 120, 90))
    c.text("CRYPT CRAWLER", "blk", W / 2 - 40, 150, 660, 100, colour=(230, 36, 56))
    c.text("PRESS ANY BUTTON", "ui", W / 2, 510, 360, 30, colour=(236, 226, 255))
    return c


def tiles(kind):
    if kind == "Wall":
        W, H, n, rows = 600, 1500, 6, 15
        c = Cell(W, H, (150, 142, 128), grain=3, seed=3920)
        t = W / n
        g = random.Random(3920)
        for r in range(rows):
            for q in range(n):
                band = r == 9
                o = g.uniform(-7, 5)
                col = (96, 14, 26) if band else tuple(int(v + o) for v in (222, 214, 194))
                if r == 8 or r == 10:
                    col = (24, 22, 26)
                x0, y0 = q * t, H - (r + 1) * t
                hh, yy = t, y0
                c.shape(lambda d, k, x0=x0, yy=yy, hh=hh: d.rounded_rectangle([(x0 + 3) * k, (yy + 3) * k, (x0 + t - 3) * k, (yy + hh - 3) * k], 4 * k,
                                                                             fill=255), col, height=150)
        return c
    W = H = 600
    c = Cell(W, H, (60, 58, 56), grain=3, seed=3921)
    t = W / 10
    for r in range(10):
        for q in range(10):
            col = (226, 220, 204) if (r + q) % 2 else (22, 20, 24)
            c.shape(lambda d, k, r=r, q=q: d.rectangle([(q * t + 2) * k, (r * t + 2) * k, ((q + 1) * t - 2) * k, ((r + 1) * t - 2) * k], fill=255), col,
                    height=150)
    return c


def backboard():
    W, H = 600, 400
    c = Cell(W, H, (226, 218, 198), grain=4, seed=3930)
    c.shape(lambda d, k: d.rectangle([10 * k, 10 * k, (W - 10) * k, (H - 10) * k], outline=255, width=int(16 * k)), (96, 14, 26))
    c.shape(lambda d, k: d.rectangle([200 * k, 170 * k, 400 * k, 320 * k], outline=255, width=int(12 * k)), (96, 14, 26))
    crest(c, W / 2, 90, 100)
    return c


def perfume_label(name, sub, bg, fg):
    W, H = 300, 220
    c = Cell(W, H, bg, grain=3, seed=seed_of(name))
    c.shape(lambda d, k: d.rectangle([10 * k, 10 * k, (W - 10) * k, (H - 10) * k], outline=255, width=int(4 * k)), fg)
    c.text(name, "palabi", W / 2, 90, W - 50, 64, colour=fg)
    c.text(sub, "palai", W / 2, 160, W - 70, 30, colour=fg)
    return c


def pp_net():
    W, H = 1000, 120
    c = Cell(W, H, (16, 16, 18), grain=2, seed=3940)
    c.shape(lambda d, k: [d.line([(x * k, 16 * k), (x * k, H * k)], fill=255, width=int(2 * k)) for x in range(0, W, 14)] +
            [d.line([(0, y * k), (W * k, y * k)], fill=255, width=int(2 * k)) for y in range(16, H, 14)], (120, 118, 112))
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 16 * k], fill=255), (236, 232, 220))
    return c


def makeup_lid():
    W, H = 400, 260
    c = Cell(W, H, (22, 18, 22), grain=2, seed=3950)
    rules(c, 12, GILT, 4)
    c.text("MOTH & MIRROR", "pala", W / 2, 110, 320, 48, colour=GILT)
    c.text("eye colours", "palai", W / 2, 170, 200, 30, colour=GILT)
    return c


# ================================================================== write

if __name__ == "__main__":
    reg = {}
    a = Atlas("DetentionPrint")
    a.put("Lines_Board", lines_board(), 1.0)
    a.put("Lines_Page1", lines_page(3702), 0.8)
    a.put("Lines_Page2", lines_page(3703, messy=0.6), 0.8)
    a.put("Ledger_L", ledger_page(3704, REGISTER[:7], True), 0.85)
    a.put("Ledger_R", ledger_page(3705, REGISTER[7:], False), 0.85)
    a.put("Rules", rules_board(), 0.9)
    a.put("Confiscated", confiscated(), 0.8)
    a.put("Comic_1", comic(3706, "NIGHT RAVEN", "the wings of midnight", 12, (40, 30, 70), (150, 20, 30), fig_raven), 0.8)
    a.put("Comic_2", comic(3707, "GHOUL SCHOOL", "detention never ends", 3, (30, 60, 50), (200, 120, 30), fig_ghoul), 0.8)
    a.put("Comic_3", comic(3708, "MOON WOLF", "the howl returns", 27, (60, 40, 30), (30, 60, 120), fig_wolf), 0.8)
    a.put("Phone_Lock", phone_lock(), 1.0)
    a.put("Phone_Apps", phone_apps(), 1.0)
    for k in ("back", "ace", "queen", "seven"):
        a.put(f"Card_{k}", card(k), 0.8)
    for name, col, gr, m in (("slate", (34, 42, 40), 8, 0), ("paper", (236, 232, 218), 4, 0), ("ledger", (228, 216, 186), 5, 0),
                             ("crimson", CRIMSON, 4, 0), ("ink", INK, 3, 0), ("bone", BONE, 4, 0), ("kraft", D.KRAFT, 8, 0),
                             ("black", (14, 14, 16), 2, 0), ("cardwhite", (244, 240, 230), 2, 0), ("pageedge", (220, 212, 190), 6, 0),
                             ("newsprint", (214, 206, 180), 6, 0), ("label", (196, 178, 140), 8, 0)):
        a.put(f"Swatch_{name}", swatch(col, gr, seed_of(name), m))
    a.save()
    reg["DetentionPrint"] = a.reg

    e = Atlas("ElectivesPrint")
    e.put("Pegboard", pegboard(), 1.0)
    e.put("Machine_Decal", machine_decal(), 0.8)
    e.put("Tabard", tabard(), 0.7)
    for n in ("Plaid", "Pinstripe", "Check", "Dots", "Moths", "Ticking"):
        e.put(f"Fabric_{n}", fabric(n), 0.75)
    for n in ("Tower", "Raven", "Tree", "Face"):
        e.put(f"Photo_{n}", photo(n), 0.75)
    for w, col in (("DEVELOPER", (30, 40, 90)), ("STOP BATH", (150, 20, 30)), ("FIXER", (30, 80, 50))):
        e.put(f"Tray_{w.split()[0]}", tray_label(w, col), 0.7)
    for h in HERBS:
        e.put(f"Herb_{h}", plant_label(h), 0.8)
    e.put("Bricks", bricks(), 0.9)
    for name, col, gr, m in (("black", (14, 13, 16), 2, 0), ("paper", (236, 234, 226), 3, 0), ("bone", BONE, 4, 0), ("crimson", CRIMSON, 4, 0),
                             ("board", (52, 36, 26), 8, 0), ("label", (222, 214, 190), 4, 0), ("gilt", GILT, 4, 235)):
        e.put(f"Swatch_{name}", swatch(col, gr, seed_of(name), m))
    e.save()
    reg["ElectivesPrint"] = e.reg

    h = Atlas("DormHousePrint")
    h.put("Tiles_Wall", tiles("Wall"), 0.9)
    h.put("Tiles_Floor", tiles("Floor"), 0.8)
    h.put("SignIn_L", signin_page(3902, SIGNIN[:6], True), 0.85)
    h.put("SignIn_R", signin_page(3903, SIGNIN[6:], False), 0.85)
    h.put("TV_Screen", tv_screen(), 1.0)
    h.put("Washer_Panel", washer_panel(), 0.8)
    h.put("Backboard", backboard(), 0.8)
    h.put("PP_Net", pp_net(), 0.8)
    h.put("Makeup_Lid", makeup_lid(), 0.7)
    for k in ("Bat", "Moon", "Skull", "Note"):
        h.put(f"Sticker_{k}", sticker(k), 0.7)
    for name, sub, bg, fg in (("Nocturne", "eau de nuit", (24, 20, 30), GILT), ("Velvet Rose", "parfum", (110, 16, 28), (240, 226, 200)),
                              ("Moonmilk", "body mist", (226, 220, 206), (60, 40, 70))):
        h.put(f"Perfume_{name.split()[0]}", perfume_label(name, sub, bg, fg), 0.7)
    for name, col, gr, m in (("black", (16, 16, 18), 2, 0), ("paper", (232, 224, 200), 4, 0), ("bone", BONE, 4, 0), ("crimson", CRIMSON, 4, 0),
                             ("grout", (150, 142, 128), 3, 0), ("screen", (12, 10, 26), 2, 0), ("note", (240, 228, 150), 4, 0)):
        h.put(f"Swatch_{name}", swatch(col, gr, seed_of(name), m))
    h.save()
    reg["DormHousePrint"] = h.reg

    json.dump({"regions": reg, "tools": TOOLS, "board": [BOARD_W, BOARD_H]}, open(os.path.join(HERE, "kits3739_atlas.json"), "w"), indent=0)
