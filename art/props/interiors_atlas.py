"""Printed atlas for props batch 45, the interiors kit (shop, bookshop and cafe interiors). System Python (PIL + numpy):

  python art/props/interiors_atlas.py

InteriorsPrint  the general store's names and signs (MORROW & VANE, Purveyors of Sundries), the OPEN / CLOSED faces, the brass
                yard rule, the till's keys, flags and plate, the scales dial, the shop's crimson wrapping paper, price tickets, the
                apothecary drawer labels and header, sweet-jar labels, postcards and pamphlets, sack and crate stencils, tin labels,
                the bookseller's (LANTERNLIGHT BOOKS) new-release covers, header cards, the staff-picks card and the bargain slate,
                the cafe's (THE WICK & KETTLE) name and jar labels, and plain swatches.

Writes art/props/textures/InteriorsPrint_{color,gilt,height}.png (4096; bake sources only, not uploaded) and
art/props/interiors_atlas.json (every region's UV rect, v up). Uses dorm_atlas.py's Cell / Atlas machinery. All names, text and
designs are invented.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import dorm_atlas as D
from dorm_atlas import Cell, Atlas, swatch, seed_of, fleuron, rules, handwriting, INK, CRIMSON, GILT, PARCH, KRAFT

HERE = D.HERE
D.FONTS.update({"blk": D.F + "ariblk.ttf", "cons": D.F + "consolab.ttf", "bahn": D.F + "bahnschrift.ttf", "impact": D.F + "impact.ttf"})
SS = D.SS
BONE = (214, 200, 168)
CHALK = (222, 220, 210)
ENAMEL = (232, 224, 204)
NIGHT = (16, 18, 34)
VIOLET = (78, 40, 110)

SHOP = "MORROW & VANE"
BOOKS = "LANTERNLIGHT BOOKS"
CAFE = "The Wick & Kettle"


# ------------------------------------------------------------------ small drawing helpers

def poly(c, pts, colour, height=None, metal=0):
    c.shape(lambda d, k: d.polygon([(x * k, y * k) for x, y in pts], fill=255), colour, metal=metal, height=height)


def disc(c, x, y, r, colour, height=None, outline=0):
    if outline:
        c.shape(lambda d, k: d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], outline=255, width=int(outline * k)), colour,
                height=height)
    else:
        c.shape(lambda d, k: d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255), colour, height=height)


def frame(c, inset, colour, width, radius=0):
    if radius:
        c.shape(lambda d, k: d.rounded_rectangle([inset * k, inset * k, (c.w - inset) * k, (c.h - inset) * k], radius=int(radius * k), outline=255,
                                                 width=int(width * k)), colour)
    else:
        rules(c, inset, colour, width)


def crescent(c, x, y, r, colour, bg, turn=0.45):
    disc(c, x, y, r, colour)
    disc(c, x + r * turn, y - r * 0.2, r * 0.86, bg)


def bat(c, x, y, s, colour):
    P = [(-1.0, -0.1), (-0.75, -0.35), (-0.55, -0.18), (-0.35, -0.32), (-0.2, -0.12), (-0.1, -0.3), (0, -0.18), (0.1, -0.3), (0.2, -0.12),
         (0.35, -0.32), (0.55, -0.18), (0.75, -0.35), (1.0, -0.1), (0.7, 0.0), (0.5, 0.15), (0.3, 0.02), (0.12, 0.2), (0, 0.1),
         (-0.12, 0.2), (-0.3, 0.02), (-0.5, 0.15), (-0.7, 0.0)]
    poly(c, [(x + u * s, y + v * s) for u, v in P], colour)


def key_glyph(c, x, y, s, colour):
    def dr(d, k):
        r = s * 0.22
        d.ellipse([(x - r) * k, (y - s * 0.5 - r) * k, (x + r) * k, (y - s * 0.5 + r) * k], outline=255, width=int(s * 0.08 * k))
        d.rectangle([(x - s * 0.04) * k, (y - s * 0.3) * k, (x + s * 0.04) * k, (y + s * 0.5) * k], fill=255)
        d.rectangle([x * k, (y + s * 0.26) * k, (x + s * 0.2) * k, (y + s * 0.34) * k], fill=255)
        d.rectangle([x * k, (y + s * 0.4) * k, (x + s * 0.15) * k, (y + s * 0.5) * k], fill=255)
    c.shape(dr, colour)


def candle_glyph(c, x, y, s, colour, flame=(236, 170, 70)):
    c.shape(lambda d, k: d.rectangle([(x - s * 0.1) * k, (y - s * 0.2) * k, (x + s * 0.1) * k, (y + s * 0.5) * k], fill=255), colour)
    poly(c, [(x, y - s * 0.55), (x + s * 0.08, y - s * 0.32), (x, y - s * 0.24), (x - s * 0.08, y - s * 0.32)], flame)


def raven(c, x, y, s, colour):
    P = [(-0.5, 0.1), (-0.3, 0.0), (-0.15, -0.12), (0.0, -0.2), (0.12, -0.32), (0.24, -0.34), (0.34, -0.3), (0.46, -0.3), (0.34, -0.24),
         (0.3, -0.14), (0.22, 0.04), (0.1, 0.18), (0.0, 0.24), (0.04, 0.4), (-0.04, 0.4), (-0.06, 0.26), (-0.2, 0.24), (-0.5, 0.3), (-0.62, 0.32),
         (-0.44, 0.18)]
    poly(c, [(x + u * s, y + v * s) for u, v in P], colour)


def stencil(c, s, fk, x, y, maxw, maxh, colour, seed):
    """Stencilled lettering: the bridges cut across each letter, sprayed edges, a little overspray."""
    m = c.fit(s, fk, maxw, maxh)
    w, h = m.size
    d = ImageDraw.Draw(m)
    g = random.Random(seed)
    # horizontal bridge through the middle and short vertical bridges at the letter gaps
    d.rectangle([0, int(h * 0.49), w, int(h * 0.49 + max(2, h * 0.045))], fill=0)
    a = np.asarray(m, np.float32)
    a = np.asarray(Image.fromarray(np.uint8(a)).filter(ImageFilter.GaussianBlur(1.2 * SS)), np.float32)
    noise = np.random.default_rng(seed).uniform(-60, 60, a.shape)
    a = np.clip((a + noise - 90) * 2.2, 0, 255)
    spray = Image.fromarray(np.uint8(a)).filter(ImageFilter.GaussianBlur(4 * SS)).point(lambda v: int(v * 0.18))
    c.stamp(spray, x, y, colour)
    c.stamp(Image.fromarray(np.uint8(a)), x, y, colour, alpha=0.9 + g.uniform(-0.05, 0.05))


def grad(c, top, low, power=1.4):
    a = np.asarray(c.c, np.float32)
    t = (np.arange(a.shape[0], dtype=np.float32) / a.shape[0]) ** power
    t = np.broadcast_to(t[:, None], a.shape[:2])
    a = np.array(top, np.float32) + (np.array(low, np.float32) - np.array(top, np.float32)) * t[..., None]
    a += np.random.default_rng(int(sum(top)) + 7).normal(0, 3, a.shape[:2])[..., None]
    c.c = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    c.dc = ImageDraw.Draw(c.c)


def stars(c, n, seed, ymax=0.6, colour=(230, 230, 240)):
    g = random.Random(seed)
    for _ in range(n):
        x, y, r = g.uniform(0, c.w), g.uniform(0, c.h * ymax), g.choice([0.8, 1.0, 1.4, 2.0])
        disc(c, x, y, r, colour)


# ------------------------------------------------------------------ the general store

def shop_sign():
    """The hanging shop board: MORROW & VANE in gilt on crimson, a key and crescent emblem, the line under it."""
    W, H = 1600, 380
    c = Cell(W, H, (92, 12, 24), grain=4, seed=4501, vignette=0.18)
    frame(c, 14, GILT, 6)
    frame(c, 30, (40, 6, 12), 3)
    c.text(SHOP, "pala", W / 2, 150, W - 560, 150, colour=GILT)
    c.text("PURVEYORS OF SUNDRIES  -  ESTABLISHED 1851", "pala", W / 2, 292, W - 520, 46, colour=GILT)
    for sx in (-1, 1):
        x = W / 2 + sx * (W / 2 - 120)
        disc(c, x, H / 2, 82, GILT)
        disc(c, x, H / 2, 70, (30, 6, 12))
        crescent(c, x - 6, H / 2 + 4, 50, GILT, (30, 6, 12))
        key_glyph(c, x + 18, H / 2 + 6, 70, GILT)
    return c


def open_sign(closed=False, k=2.0):
    """The door sign's faces, at twice the usual cell size (the sign is most of its prop's map)."""
    W, H = 520 * k, 300 * k
    bg, fg = ((22, 20, 30), ENAMEL) if closed else ((112, 14, 28), ENAMEL)
    c = Cell(W, H, bg, grain=3, seed=4502 + closed, vignette=0.12)
    frame(c, 12 * k, fg, 6 * k, radius=30 * k)
    c.text("CLOSED" if closed else "OPEN", "blk", W / 2, 128 * k, W - 90 * k, 120 * k, colour=fg)
    c.text("back at dusk" if closed else "do come in", "palai", W / 2, 228 * k, W - 200 * k, 46 * k, colour=GILT)
    if closed:
        crescent(c, 62 * k, 62 * k, 22 * k, GILT, bg)
    else:
        candle_glyph(c, 62 * k, 70 * k, 60 * k, GILT)
    return c


def yard_rule():
    """The brass yard rule set into the counter's front edge: 36 inches, eighths, numbers every inch."""
    W, H = 2400, 90
    c = Cell(W, H, (170, 128, 60), grain=4, seed=4503)

    def ticks(d, k):
        for i in range(36 * 8 + 1):
            x = 20 + i * (W - 40) / (36 * 8)
            L = 46 if i % 8 == 0 else 30 if i % 4 == 0 else 20 if i % 2 == 0 else 12
            d.line([x * k, 4 * k, x * k, (4 + L) * k], fill=255, width=int((3 if i % 8 == 0 else 1.6) * k))
    c.shape(ticks, (40, 26, 12), height=90)
    for i in range(1, 36):
        x = 20 + i * 8 * (W - 40) / (36 * 8)
        c.text(str(i), "pala", x + 10, 70, 30, 22, colour=(40, 26, 12), height=100, anchor="lm")
    return c


def monogram():
    """The M & V monogram for the counter's end panel: gilt in a ring of quatrefoils on crimson."""
    W = H = 360
    c = Cell(W, H, (92, 12, 24), grain=4, seed=4504, vignette=0.2)
    disc(c, W / 2, H / 2, 150, GILT, outline=8)
    disc(c, W / 2, H / 2, 128, GILT, outline=2)
    for i in range(8):
        a = i * math.pi / 4
        fleuron(c, W / 2 + math.cos(a) * 139, H / 2 + math.sin(a) * 139, 14)
    c.text("M", "pala", W / 2 - 46, H / 2 - 4, 90, 110, colour=GILT)
    c.text("V", "pala", W / 2 + 50, H / 2 - 4, 90, 110, colour=GILT)
    c.text("&", "palai", W / 2 + 2, H / 2 + 34, 40, 44, colour=(232, 210, 150))
    crescent(c, W / 2, H / 2 - 82, 18, GILT, (92, 12, 24))
    return c


def gate_plate():
    W, H = 560, 110
    c = Cell(W, H, (20, 18, 24), grain=2, seed=4505)
    frame(c, 8, GILT, 4)
    c.text("PROPRIETOR ONLY", "pala", W / 2, H / 2, W - 70, 56, colour=GILT)
    return c


def till_flags():
    """The register's sale flags behind the crest window: white enamel flags, YEN 4 50 popped up."""
    W, H = 640, 170
    c = Cell(W, H, (16, 15, 18), grain=2, seed=4506)
    for i, t in enumerate(("¥", "4", "50")):
        x = 110 + i * 210
        c.shape(lambda d, k, x=x: d.rounded_rectangle([(x - 80) * k, 18 * k, (x + 80) * k, (H - 18) * k], radius=int(14 * k), fill=255), ENAMEL)
        c.text(t, "blk", x, H / 2, 140, 108, colour=(20, 18, 24))
    return c


def till_plate():
    W, H = 640, 96
    c = Cell(W, H, (150, 108, 46), grain=4, seed=4507)
    frame(c, 6, (60, 38, 16), 3)
    c.text("AMOUNT  PURCHASED", "pala", W / 2, H / 2, W - 60, 48, colour=(40, 22, 10), height=100)
    return c


def till_maker():
    W, H = 600, 90
    c = Cell(W, H, (150, 108, 46), grain=4, seed=4517)
    c.text("VESPER - CROSS  REGISTER  CO.", "pala", W / 2, H / 2, W - 40, 44, colour=(40, 22, 10), height=100)
    return c


KEYS = ("1", "2", "5", "10", "20", "50", "100", "500", "NS")


def till_key(t):
    W = H = 140
    c = Cell(W, H, (30, 28, 30), grain=2, seed=seed_of("key" + t))
    disc(c, W / 2, H / 2, 64, (214, 204, 178))
    disc(c, W / 2, H / 2, 64, (150, 108, 46), outline=7)
    c.text("NO SALE" if t == "NS" else t, "blk", W / 2, H / 2 + 2, 90 if t != "NS" else 104, 56 if len(t) < 3 else 40,
           colour=(112, 14, 28) if t in ("NS", "100", "500") else (20, 18, 24))
    return c


def scales_dial():
    W = H = 460
    c = Cell(W, H, ENAMEL, grain=3, seed=4508, vignette=0.2)
    disc(c, W / 2, H / 2, 222, (150, 108, 46), outline=10)

    def sc(d, k):
        for i in range(0, 41):
            a = math.pi * (0.8 + i / 40 * 1.4)
            r0 = 186 if i % 5 else 168
            d.line([(W / 2 + math.cos(a) * r0) * k, (H / 2 + math.sin(a) * r0) * k, (W / 2 + math.cos(a) * 206) * k, (H / 2 + math.sin(a) * 206) * k],
                   fill=255, width=int((4 if i % 5 == 0 else 2) * k))
    c.shape(sc, INK)
    for i in range(0, 9):
        a = math.pi * (0.8 + i * 5 / 40 * 1.4)
        c.text(str(i), "pala", W / 2 + math.cos(a) * 140, H / 2 + math.sin(a) * 140, 40, 34, colour=INK)
    c.text("TRUE MEASURE", "pala", W / 2, H / 2 + 62, 150, 24, colour=CRIMSON)
    c.text("lbs", "palai", W / 2, H / 2 + 98, 60, 22, colour=INK)
    c.text(SHOP, "pala", W / 2, H / 2 - 70, 200, 22, colour=INK)
    return c


def wrap_paper():
    """The shop's wrapping paper: deep crimson with a gilt diaper of crescents, keys and quatrefoils."""
    W = H = 600
    c = Cell(W, H, (100, 16, 28), grain=5, seed=4509, fibres=True)
    for j in range(5):
        for i in range(5):
            x, y = 60 + i * 120 + (60 if j % 2 else 0), 60 + j * 120
            if (i + j) % 2:
                crescent(c, x % W, y, 22, (200, 160, 90), (100, 16, 28))
            else:
                fleuron(c, x % W, y, 20, (200, 160, 90))
    return c


PRICES = ("¥ 3", "¥ 12", "¥ 7", "¥ 25", "¥ 1", "¥ 40", "¥ 5", "¥ 9")


def ticket(t, i):
    W, H = 200, 120
    c = Cell(W, H, BONE if i % 3 else ENAMEL, grain=4, seed=4510 + i)
    frame(c, 7, CRIMSON, 3)
    c.text(t, "pala", W / 2, H / 2 - 8, W - 40, 62, colour=INK)
    c.text("each" if i % 2 else "the lb", "palai", W / 2, H - 26, 100, 22, colour=CRIMSON)
    return c


APO = ("RAD. VALER.", "FOL. MENTH.", "SEM. ANISI", "CORT. CINN.", "FLOR. LAVAND.", "PULV. OSSIS", "RAD. MANDRAG.", "HERB. ABSINTH.",
       "SAL AMMON.", "GUM. ARAB.", "FOL. SALVIAE", "SEM. PAPAV.", "BACC. JUNIP.", "CERA ALBA", "SULPHUR", "MYRRHA",
       "CAMPHORA", "LAP. LUNAE", "RAD. ZINGIB.", "FOL. HEDERAE", "CORT. SALIC.", "FLOR. SAMBUC.", "PULV. NOCTIS", "SEM. FENIC.")


def apo_label(t, i):
    W, H = 240, 96
    c = Cell(W, H, PARCH, grain=5, seed=4520 + i, vignette=0.25)
    frame(c, 6, INK, 2)
    c.text(t, "pala", W / 2, H / 2 - 6, W - 30, 40, colour=INK)
    c.text(f"No. {i + 1:02d}", "palai", W / 2, H - 18, 60, 16, colour=CRIMSON)
    return c


def apo_header():
    W, H = 1500, 170
    c = Cell(W, H, (16, 15, 18), grain=2, seed=4530)
    frame(c, 10, GILT, 5)
    c.text("APOTHECARY", "pala", W / 2, 74, W - 300, 90, colour=GILT)
    c.text("simples  -  tinctures  -  remedies for the night", "palai", W / 2, 136, W - 500, 34, colour=(200, 180, 140))
    for sx in (-1, 1):
        fleuron(c, W / 2 + sx * (W / 2 - 80), H / 2, 40)
    return c


SWEETS = (("BAT DROPS", (60, 20, 70)), ("HUMBUGS", (30, 30, 34)), ("SHERBET MOONS", (150, 120, 40)), ("LIQUORICE BONES", (20, 18, 24)),
          ("VIOLET CREAMS", (80, 40, 110)), ("ACID TEARS", (40, 90, 60)), ("CINDER TOFFEE", (140, 70, 20)), ("MINT GHOSTS", (40, 90, 100)))


def sweet_label(t, col, i):
    W, H = 320, 220
    c = Cell(W, H, ENAMEL, grain=4, seed=4540 + i, vignette=0.15)
    c.shape(lambda d, k: d.ellipse([10 * k, 10 * k, (W - 10) * k, (H - 10) * k], fill=255), col)
    c.shape(lambda d, k: d.ellipse([22 * k, 22 * k, (W - 22) * k, (H - 22) * k], fill=255), ENAMEL)
    c.shape(lambda d, k: d.ellipse([30 * k, 30 * k, (W - 30) * k, (H - 30) * k], outline=255, width=int(3 * k)), GILT)
    words = t.split(" ")
    if len(words) == 1:
        c.text(t, "pala", W / 2, H / 2, W - 90, 56, colour=col)
    else:
        c.text(words[0], "pala", W / 2, H / 2 - 22, W - 100, 44, colour=col)
        c.text(" ".join(words[1:]), "pala", W / 2, H / 2 + 24, W - 100, 40, colour=col)
    c.text("2 oz  ¥ 1", "palai", W / 2, H - 46, 100, 20, colour=CRIMSON)
    return c


def banner(text, W=1100, H=170, bg=(92, 12, 24), sub=None, seed=4550):
    c = Cell(W, H, bg, grain=3, seed=seed, vignette=0.15)
    frame(c, 9, GILT, 5)
    if sub:
        c.text(text, "pala", W / 2, H * 0.4, W - 160, H * 0.48, colour=GILT)
        c.text(sub, "palai", W / 2, H * 0.78, W - 260, H * 0.2, colour=(226, 200, 150))
    else:
        c.text(text, "pala", W / 2, H / 2, W - 160, H * 0.56, colour=GILT)
    for sx in (-1, 1):
        fleuron(c, W / 2 + sx * (W / 2 - 50), H / 2, 24)
    return c


# ------------------------------------------------------------------ postcards and pamphlets

def postcard(kind, i):
    W, H = 320, 210
    c = Cell(W, H, NIGHT, grain=0, seed=4560 + i)
    pal = [((10, 12, 30), (60, 46, 90)), ((14, 10, 22), (110, 40, 50)), ((8, 16, 30), (40, 70, 90)), ((12, 12, 20), (70, 60, 100))][i % 4]
    grad(c, *pal)
    stars(c, 40, 4560 + i)
    sil = (8, 8, 14)
    if kind == "school":
        disc(c, 240, 60, 26, (230, 226, 200))
        pts = [(0, 210), (0, 150), (40, 150), (40, 110), (60, 80), (80, 110), (80, 150), (120, 150), (120, 70), (134, 30), (148, 70), (148, 150),
               (200, 150), (200, 120), (240, 120), (240, 150), (320, 150), (320, 210)]
        poly(c, pts, sil)
        for x, y in ((60, 125), (130, 100), (220, 135), (100, 165)):
            c.shape(lambda d, k, x=x, y=y: d.rectangle([x * k, y * k, (x + 6) * k, (y + 10) * k], fill=255), (230, 160, 70))
        title = "Greetings from the Institution"
    elif kind == "bell":
        disc(c, 90, 70, 34, (236, 220, 190))
        poly(c, [(150, 210), (150, 90), (170, 60), (180, 20), (190, 60), (210, 90), (210, 210)], sil)
        disc(c, 180, 105, 12, (200, 150, 70))
        bat(c, 70, 130, 18, sil)
        bat(c, 250, 50, 12, sil)
        title = "The Bell Tower by Night"
    elif kind == "lake":
        disc(c, 160, 70, 30, (230, 226, 210))
        c.shape(lambda d, k: d.rectangle([0, 140 * k, W * k, H * k], fill=255), (20, 26, 44))
        for j in range(6):
            y = 150 + j * 9
            c.shape(lambda d, k, y=y, j=j: d.line([(150 - 18 + j * 2) * k, y * k, (170 + 18 - j * 2) * k, y * k], fill=255, width=int(2 * k)),
                    (200, 200, 190))
        poly(c, [(0, 140), (0, 110), (30, 100), (60, 120), (90, 112), (110, 140)], sil)
        poly(c, [(220, 140), (240, 105), (260, 115), (290, 96), (320, 110), (320, 140)], sil)
        title = "Moonrise on Blackwater"
    elif kind == "raven":
        disc(c, 220, 80, 50, (220, 210, 190))
        c.shape(lambda d, k: d.line([0, 160 * k, 200 * k, 140 * k, 320 * k, 150 * k], fill=255, width=int(8 * k)), sil)
        raven(c, 160, 116, 90, sil)
        title = "A Raven's Welcome"
    elif kind == "street":
        disc(c, 60, 50, 18, (230, 226, 200))
        poly(c, [(0, 210), (0, 100), (30, 80), (60, 100), (60, 120), (100, 120), (100, 90), (130, 70), (160, 90), (160, 210)], sil)
        poly(c, [(190, 210), (190, 95), (225, 70), (260, 95), (260, 110), (320, 110), (320, 210)], sil)
        for x in (175, 300):
            c.shape(lambda d, k, x=x: d.rectangle([(x - 2) * k, 120 * k, (x + 2) * k, 200 * k], fill=255), sil)
            disc(c, x, 118, 7, (240, 180, 80))
        for x, y in ((20, 130), (110, 140), (205, 120), (280, 140)):
            c.shape(lambda d, k, x=x, y=y: d.rectangle([x * k, y * k, (x + 10) * k, (y + 14) * k], fill=255), (220, 150, 60))
        title = "Lamplight on the High Street"
    elif kind == "gargoyle":
        disc(c, 80, 60, 28, (230, 220, 200))
        poly(c, [(130, 210), (130, 150), (150, 120), (180, 100), (210, 96), (240, 110), (250, 90), (262, 112), (280, 130), (250, 140), (230, 150),
                 (260, 170), (320, 170), (320, 210)], sil)
        disc(c, 222, 112, 4, (220, 90, 40))
        title = "The Old Watchers"
    elif kind == "chapel":
        disc(c, 260, 50, 22, (230, 226, 200))
        poly(c, [(80, 210), (80, 120), (130, 80), (150, 20), (170, 80), (220, 120), (220, 210)], sil)
        c.shape(lambda d, k: d.ellipse([140 * k, 120 * k, 160 * k, 140 * k], fill=255), (190, 60, 70))
        poly(c, [(140, 210), (140, 170), (150, 158), (160, 170), (160, 210)], (210, 150, 70))
        title = "Evensong at the Chapel"
    else:   # the moon and bats
        disc(c, 160, 100, 70, (236, 228, 200))
        for x, y, s in ((120, 80, 22), (200, 110, 16), (160, 60, 12), (90, 140, 14), (240, 70, 10)):
            bat(c, x, y, s, sil)
        title = "Full Moon Over the Hollow"
    c.shape(lambda d, k: d.rectangle([0, (H - 34) * k, W * k, H * k], fill=255), (226, 214, 184))
    c.text(title, "palai", W / 2, H - 17, W - 30, 22, colour=CRIMSON)
    frame(c, 3, (226, 214, 184), 6)
    return c


PAMPHLETS = (("THE NIGHT OMNIBUS", "times & stops", (30, 34, 60)), ("A WALK THROUGH", "the old crypts", (60, 14, 22)),
             ("CURFEW", "a notice to visitors", (22, 20, 26)), ("THE HARVEST FAIR", "lanterns at dusk", (70, 50, 20)))


def pamphlet(t, sub, col, i):
    W, H = 220, 320
    c = Cell(W, H, PARCH, grain=6, seed=4570 + i, vignette=0.2, fibres=True)
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 110 * k], fill=255), col)
    c.text(t, "pala", W / 2, 56, W - 30, 40, colour=ENAMEL)
    c.text(sub, "palai", W / 2, 140, W - 40, 28, colour=col)
    if i == 0:
        for j in range(6):
            c.text(f"{7 + j}.{(j * 25) % 60:02d}  ...........  stop {j + 1}", "type", W / 2, 180 + j * 20, W - 40, 14, colour=INK)
    else:
        for j in range(7):
            c.shape(lambda d, k, j=j: d.line([20 * k, (180 + j * 18) * k, (W - 20 - (j % 3) * 20) * k, (180 + j * 18) * k], fill=255,
                                             width=int(2 * k)), (90, 84, 78))
    candle_glyph(c, W / 2, H - 30, 34, col)
    return c


# ------------------------------------------------------------------ stock: sacks, crates and tins

SACKS = (("FINE FLOUR", "No. 2  -  MILLED", (40, 30, 24)), ("ROLLED OATS", "MORROW & VANE", (90, 20, 26)), ("COFFEE", "DARK ROAST BEANS", (40, 28, 20)),
         ("SEA SALT", "COARSE", (30, 40, 60)), ("BROWN SUGAR", "1 CWT", (90, 20, 26)))


def sack_print(t, sub, col, i):
    W, H = 420, 420
    c = Cell(W, H, (156, 132, 96), grain=12, seed=4580 + i, fibres=True)
    disc(c, W / 2, H / 2, 170, col, outline=10)
    stencil(c, t, "impact", W / 2, H / 2 - 30, 300, 90, col, 4580 + i)
    stencil(c, sub, "bahn", W / 2, H / 2 + 60, 260, 40, col, 4590 + i)
    c.text("M & V", "pala", W / 2, H / 2 + 130, 90, 30, colour=col, alpha=0.8)
    return c


CRATES = (("TALLOW CANDLES", "12 DOZ  -  KEEP COOL"), ("LAMP OIL", "THIS WAY UP"), ("INK", "48 BOTTLES  -  FRAGILE"), ("SAFETY MATCHES", "KEEP DRY"),
          ("CARBOLIC SOAP", "6 GROSS"), ("MORROW & VANE", "HANDLE WITH CARE"))


def crate_stencil(t, sub, i):
    W, H = 520, 260
    c = Cell(W, H, (128, 96, 62), grain=0, seed=4600 + i)
    g = np.random.default_rng(4600 + i)
    a = np.zeros((c.h * SS, c.w * SS, 3), np.float32)
    a[:] = (128, 96, 62)
    grain = np.asarray(Image.fromarray(np.uint8(np.clip(g.normal(128, 40, (c.h * SS // 3, 6)), 0, 255))).resize((c.w * SS, c.h * SS), Image.BICUBIC),
                       np.float32) - 128
    fine = g.normal(0, 6, (c.h * SS, 1))
    a += (grain * 0.35 + fine)[..., None]
    c.c = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    c.dc = ImageDraw.Draw(c.c)
    for j in (1, 2):
        c.shape(lambda d, k, j=j: d.line([0, (H * j / 3) * k, W * k, (H * j / 3) * k], fill=255, width=int(3 * k)), (60, 42, 26), height=90)
    ink = (26, 20, 18) if i % 2 == 0 else (100, 18, 26)
    stencil(c, t, "impact", W / 2, H * 0.4, W - 70, 96, ink, 4600 + i)
    stencil(c, sub, "bahn", W / 2, H * 0.76, W - 120, 40, ink, 4610 + i)
    if "UP" in sub:
        poly(c, [(14, 70), (32, 40), (50, 70), (39, 70), (39, 110), (25, 110), (25, 70)], ink)
    return c


TINS = (("BLACK TEA", "No. 7  -  SMOKED", (24, 22, 28), GILT), ("BOOT BLACKING", "the darkest shine", (110, 16, 28), ENAMEL),
        ("CANDLE WAX", "white  -  pure", (230, 220, 196), CRIMSON), ("LAMP WICKS", "cotton  -  twelve", (30, 40, 60), GILT),
        ("BISCUITS", "assorted", (100, 16, 28), GILT), ("MUSTARD", "fine powder", (170, 130, 40), (30, 20, 16)),
        ("COCOA", "for the cold nights", (50, 30, 22), GILT))


def tin_label(t, sub, bg, fg, i):
    W, H = 520, 170
    c = Cell(W, H, bg, grain=3, seed=4620 + i, vignette=0.1)
    for y in (12, H - 18):
        c.shape(lambda d, k, y=y: d.rectangle([0, y * k, W * k, (y + 6) * k], fill=255), fg)
    c.text(t, "pala", W / 2, H / 2 - 12, W - 120, 60, colour=fg)
    c.text(sub, "palai", W / 2, H / 2 + 38, W - 200, 26, colour=fg)
    fleuron(c, 50, H / 2, 20, fg)
    fleuron(c, W - 50, H / 2, 20, fg)
    return c


# ------------------------------------------------------------------ the bookshop

COVERS = (("THE LANTERN BELOW", "Ottoline Marsh", (70, 12, 22), "lantern"), ("RAVENS OF GREYHALLOW", "Silas Wren", (20, 22, 36), "raven"),
          ("A GRAMMAR OF SHADOWS", "E. M. Thistlewood", (36, 24, 50), "moon"), ("THE NIGHT MATRON", "Agatha Pell", (24, 36, 30), "candle"),
          ("SALT & BONE", "Morwenna Hale", (200, 190, 168), "key"), ("THE BELL TOLLS THRICE", "Jasper Crane", (50, 36, 20), "bell"),
          ("INK IN THE WATER", "Rosalind Vey", (14, 30, 50), "drop"), ("THE LAST VIGIL", "Cornelius Black", (16, 15, 18), "eye"),
          ("WHAT THE OWLS KEPT", "Hester Lowe", (60, 46, 30), "owl"), ("ONE HUNDRED CANDLES", "Ida Morrow", (92, 12, 24), "candles"))


def cover(t, author, bg, motif, i):
    W, H = 300, 440
    light = sum(bg) > 400
    fg = (70, 12, 22) if light else GILT
    c = Cell(W, H, bg, grain=5, seed=4630 + i, vignette=0.25)
    frame(c, 12, fg, 4)
    frame(c, 22, fg, 1.5)
    words = t.split(" ")
    mid = (len(words) + 1) // 2
    l1, l2 = " ".join(words[:mid]), " ".join(words[mid:])
    c.text(l1, "pala", W / 2, 70, W - 60, 44, colour=fg)
    c.text(l2, "pala", W / 2, 116, W - 60, 44, colour=fg)
    cx, cy = W / 2, 250
    mc = fg
    if motif == "lantern":
        poly(c, [(cx - 40, cy - 40), (cx + 40, cy - 40), (cx + 30, cy + 50), (cx - 30, cy + 50)], mc)
        poly(c, [(cx - 30, cy - 30), (cx + 30, cy - 30), (cx + 22, cy + 40), (cx - 22, cy + 40)], (240, 180, 80))
        disc(c, cx, cy - 58, 14, mc, outline=4)
        poly(c, [(cx, cy - 10), (cx + 10, cy + 12), (cx, cy + 26), (cx - 10, cy + 12)], (255, 240, 200))
    elif motif == "raven":
        raven(c, cx, cy, 150, mc)
    elif motif == "moon":
        crescent(c, cx, cy, 64, mc, bg)
        stars(c, 0, 1)
        for a in range(7):
            disc(c, cx - 90 + a * 30, cy + 90 + (a % 2) * 10, 3, mc)
    elif motif == "candle":
        candle_glyph(c, cx, cy + 10, 150, mc)
    elif motif == "key":
        key_glyph(c, cx, cy, 160, mc)
    elif motif == "bell":
        poly(c, [(cx - 15, cy - 70), (cx + 15, cy - 70), (cx + 30, cy - 40), (cx + 40, cy + 30), (cx + 60, cy + 50), (cx - 60, cy + 50), (cx - 40, cy + 30),
                 (cx - 30, cy - 40)], mc)
        disc(c, cx, cy + 62, 12, mc)
    elif motif == "drop":
        poly(c, [(cx, cy - 80)] + [(cx + math.sin(a / 10 * math.pi) * 50, cy + 10 - math.cos(a / 10 * math.pi) * 50) for a in range(-7, 8)], mc)
    elif motif == "eye":
        c.shape(lambda d, k: d.ellipse([(cx - 80) * k, (cy - 36) * k, (cx + 80) * k, (cy + 36) * k], outline=255, width=int(6 * k)), mc)
        disc(c, cx, cy, 26, mc)
        disc(c, cx, cy, 10, bg)
    elif motif == "owl":
        poly(c, [(cx - 50, cy - 60), (cx - 30, cy - 40), (cx + 30, cy - 40), (cx + 50, cy - 60), (cx + 50, cy + 40), (cx, cy + 80), (cx - 50, cy + 40)], mc)
        for sx in (-1, 1):
            disc(c, cx + sx * 22, cy - 14, 16, bg)
            disc(c, cx + sx * 22, cy - 14, 6, mc)
    else:
        for a in range(5):
            candle_glyph(c, cx - 80 + a * 40, cy + 20 - (abs(a - 2) * -10), 80, mc)
    c.text(author.upper(), "pala", W / 2, H - 56, W - 80, 24, colour=fg)
    return c


def staff_picks():
    W, H = 520, 720
    c = Cell(W, H, PARCH, grain=6, seed=4650, vignette=0.22, fibres=True)
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 130 * k], fill=255), (92, 12, 24))
    c.text("STAFF PICKS", "pala", W / 2, 62, W - 80, 70, colour=GILT)
    c.text("chosen by the night shift", "palai", W / 2, 112, W - 200, 22, colour=(226, 200, 150))
    lines = [("The Lantern Below", "- Ottoline Marsh"), ("could not put it down,", "read it by one candle - Edith"), "",
             ("Ravens of Greyhallow", "- Silas Wren"), ("the twist in chapter nine!", "do not peek - Bram"), "",
             ("A Grammar of Shadows", "- E. M. Thistlewood"), ("for anyone who studies late", "- Mr. Ash")]
    y = 180
    for ln in lines:
        if not ln:
            y += 26
            continue
        a, b = ln
        bold = ln[0][0].isupper() and ln[1].startswith("-")
        if bold:
            c.text(a, "pala", 40, y, W - 80, 34, colour=INK, anchor="lm")
            c.text(b, "palai", W - 40, y + 32, W - 120, 22, colour=CRIMSON, anchor="rm")
            y += 72
        else:
            handwriting(c, [a, b], 50, y, 36, 30, colour=(28, 34, 78))
            y += 78
    for x, y in ((30, 150), (W - 30, 150)):
        disc(c, x, y, 9, (150, 108, 46))
    return c


def bargain_slate():
    W, H = 520, 340
    c = Cell(W, H, (30, 34, 34), grain=8, seed=4660, vignette=0.2)
    g = random.Random(4661)
    for _ in range(30):
        x, y = g.uniform(0, W), g.uniform(0, H)
        c.shape(lambda d, k, x=x, y=y: d.line([x * k, y * k, (x + g.uniform(20, 80)) * k, (y + g.uniform(-6, 6)) * k], fill=255, width=int(8 * k)),
                (52, 56, 56))
    c.text("BARGAINS", "printb", W / 2, 80, W - 80, 80, colour=CHALK)
    c.text("3 for 10 ¥", "printb", W / 2, 180, W - 160, 70, colour=(226, 190, 190))
    c.text("all sales final - no ghosts refunded", "print", W / 2, 270, W - 60, 28, colour=CHALK)
    return c


# ------------------------------------------------------------------ the cafe

def cafe_name():
    W, H = 1400, 300
    c = Cell(W, H, (16, 15, 18), grain=2, seed=4670)
    c.text(CAFE, "scriptb", W / 2, H / 2 - 20, W - 200, 170, colour=GILT)
    c.text("COFFEE  -  CHOCOLATE  -  TEA  -  OPEN TILL THE CANDLES GUTTER", "pala", W / 2, H - 50, W - 300, 30, colour=(200, 180, 140))
    return c


CAFEJARS = (("COFFEE", (30, 22, 18)), ("CHOCOLATE", (70, 30, 20)), ("LOOSE TEA", (24, 40, 30)), ("SUGAR", (92, 12, 24)), ("COCOA", (50, 30, 22)),
            ("BISCOTTI", (90, 60, 30)))


def cafe_jar(t, col, i):
    W, H = 300, 200
    c = Cell(W, H, ENAMEL, grain=3, seed=4680 + i)
    c.shape(lambda d, k: d.rectangle([0, 0, W * k, 34 * k], fill=255), col)
    c.shape(lambda d, k: d.rectangle([0, (H - 34) * k, W * k, H * k], fill=255), col)
    c.text(t, "pala", W / 2, H / 2, W - 50, 54, colour=col)
    return c


def bell_card():
    W, H = 380, 160
    c = Cell(W, H, ENAMEL, grain=3, seed=4690)
    frame(c, 8, CRIMSON, 4)
    c.text("RING FOR SERVICE", "pala", W / 2, 64, W - 50, 46, colour=CRIMSON)
    c.text("once will do", "palai", W / 2, 118, W - 160, 26, colour=INK)
    return c


def book_plate():
    W, H = 1100, 160
    c = Cell(W, H, (16, 15, 18), grain=2, seed=4691)
    frame(c, 9, GILT, 4)
    c.text(BOOKS, "pala", W / 2, 70, W - 180, 76, colour=GILT)
    c.text("new  -  used  -  rare  -  read by lamplight", "palai", W / 2, 128, W - 400, 26, colour=(200, 180, 140))
    candle_glyph(c, 60, 86, 70, GILT)
    candle_glyph(c, W - 60, 86, 70, GILT)
    return c


class Sorted:
    """Collects the cells, then packs them tallest first (the shelf packer wastes less room)."""

    def __init__(self, name):
        self.a = Atlas(name)
        self.cells = []

    def put(self, key, cell, scale=1.0):
        self.cells.append((key, cell, scale))

    def save(self):
        for key, cell, scale in sorted(self.cells, key=lambda t: (-t[1].h * t[2], -t[1].w)):
            self.a.put(key, cell, scale)
        self.a.save()
        self.reg = self.a.reg


if __name__ == "__main__":
    a = Sorted("InteriorsPrint")
    a.put("ShopSign", shop_sign())
    a.put("Open", open_sign(False))
    a.put("Closed", open_sign(True))
    a.put("Rule", yard_rule())
    a.put("Monogram", monogram())
    a.put("GatePlate", gate_plate())
    a.put("TillFlags", till_flags())
    a.put("TillPlate", till_plate())
    a.put("TillMaker", till_maker())
    for t in KEYS:
        a.put(f"Key_{t}", till_key(t))
    a.put("ScaleDial", scales_dial())
    a.put("WrapPaper", wrap_paper())
    for i, t in enumerate(PRICES):
        a.put(f"Ticket_{i}", ticket(t, i))
    for i, t in enumerate(APO):
        a.put(f"Apo_{i}", apo_label(t, i))
    a.put("ApoHeader", apo_header())
    for i, (t, col) in enumerate(SWEETS):
        a.put(f"Sweet_{i}", sweet_label(t, col, i))
    a.put("SweetHeader", banner("CONFECTIONS", sub="sweets for the long night", seed=4551))
    a.put("PostHeader", banner("POSTCARDS", W=600, H=150, bg=(20, 18, 24), sub="one yen each", seed=4552))
    a.put("NewHeader", banner("NEW THIS MOON", W=800, H=200, sub="just in from the presses", seed=4553))
    a.put("BookPlate", book_plate())
    for i, k in enumerate(("school", "bell", "lake", "raven", "street", "gargoyle", "chapel", "moon")):
        a.put(f"Post_{i}", postcard(k, i))
    for i, (t, s, col) in enumerate(PAMPHLETS):
        a.put(f"Pamph_{i}", pamphlet(t, s, col, i))
    for i, (t, s, col) in enumerate(SACKS):
        a.put(f"Sack_{i}", sack_print(t, s, col, i))
    for i, (t, s) in enumerate(CRATES):
        a.put(f"Crate_{i}", crate_stencil(t, s, i))
    for i, (t, s, bg, fg) in enumerate(TINS):
        a.put(f"Tin_{i}", tin_label(t, s, bg, fg, i))
    for i, (t, au, bg, mo) in enumerate(COVERS):
        a.put(f"Cover_{i}", cover(t, au, bg, mo, i))
    a.put("StaffPicks", staff_picks())
    a.put("Bargain", bargain_slate())
    a.put("CafeName", cafe_name())
    for i, (t, col) in enumerate(CAFEJARS):
        a.put(f"CafeJar_{i}", cafe_jar(t, col, i))
    a.put("BellCard", bell_card())
    for name, col, gr, m in (("black", (16, 15, 18), 2, 0), ("paper", (232, 222, 196), 4, 0), ("bone", BONE, 4, 0), ("crimson", (92, 12, 24), 4, 0),
                             ("ink", INK, 3, 0), ("enamel", ENAMEL, 2, 0), ("gilt", GILT, 4, 235), ("brass", (150, 108, 46), 4, 200),
                             ("kraft", KRAFT, 8, 0), ("parch", PARCH, 6, 0), ("hessian", (156, 132, 96), 12, 0), ("crate", (128, 96, 62), 8, 0),
                             ("slate", (30, 34, 34), 8, 0), ("night", NIGHT, 3, 0)):
        a.put(f"Swatch_{name}", swatch(col, gr, seed_of(name), m))
    a.save()
    json.dump({"regions": {"InteriorsPrint": a.reg}}, open(os.path.join(HERE, "interiors_atlas.json"), "w"), indent=0)
