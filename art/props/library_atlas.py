"""The library kit's printed atlas (props batch 30): book spines with gilt titles, plaques, labels, newspapers, a map, a
ledger, open-book pages, plain swatches, and the terrestrial globe's map. Run with the system Python (PIL + numpy):

  python art/props/library_atlas.py

Writes art/props/textures/LibraryAtlas_{color,gilt,height}.png (4096, sRGB colour; gilt = the metal mask; height = raised
bands and debossed lettering for a bump), LibraryGlobe_color.png (2048 x 1024, equirectangular) and
art/props/library_atlas.json: every region's UV rect [u0, v0, u1, v1] (v up, as Blender reads images) and every book
design's spine size in studs. nh_props_batch30.py maps faces onto these regions (a "Spine" UV layer) and bakes them.

Spine cells: the cell's long axis is the spine's height, its left edge the spine's top, image-up the book's right side, so a
title drawn left to right reads top to bottom on the spine (the English way). All titles are original and family-friendly.
"""
import json
import math
import os
import random
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
A = 4096
PPS = 430                      # atlas pixels per stud on a spine
F = "C:/Windows/Fonts/"
FONTS = {"pala": F + "palab.ttf", "geo": F + "georgiab.ttf", "cam": F + "cambriab.ttf", "con": F + "constanb.ttf",
         "palai": F + "palabi.ttf", "times": F + "timesbd.ttf", "hand": F + "Inkfree.ttf", "plain": F + "pala.ttf", "geoi": F + "georgiai.ttf"}

GILT = (206, 164, 86)
GILT_DK = (150, 112, 52)
INK = (22, 22, 34)
LEATHERS = {   # name: sRGB
    "oxblood": (82, 20, 26), "crimson": (96, 14, 26), "ink": (30, 38, 74), "green": (24, 52, 34), "black": (24, 22, 26),
    "vellum": (194, 178, 146), "calf": (92, 56, 32), "plum": (62, 24, 50), "teal": (20, 54, 58), "tan": (138, 96, 56),
    "slate": (54, 58, 64), "bone": (214, 202, 172),
}
PAPERS = {"paper": (214, 200, 166), "aged": (190, 168, 120), "giltedge": (196, 156, 80), "parch": (222, 208, 172)}

rnd = random.Random(3001)


# ------------------------------------------------------------------ packing

class Packer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.x = self.y = self.row = 0
        self.rects = {}

    def add(self, key, cw, ch, pad=6):
        cw, ch = int(cw), int(ch)
        if self.x + cw + pad > self.w:
            self.x, self.y, self.row = 0, self.y + self.row + pad, 0
        if self.y + ch > self.h:
            raise RuntimeError(f"atlas full at {key}")
        r = (self.x + pad // 2, self.y + pad // 2, cw, ch)
        self.x += cw + pad
        self.row = max(self.row, ch)
        self.rects[key] = r
        return r


SS = 2           # everything is drawn at twice the atlas size and filtered down: smooth lettering, crisp fine rules
COL = Image.new("RGB", (A * SS, A * SS), (40, 30, 26))
MET = Image.new("L", (A * SS, A * SS), 0)
HGT = Image.new("L", (A * SS, A * SS), 128)
REG = {}          # key -> [u0, v0, u1, v1]
BOOKS = []        # book designs


class SDraw:
    """ImageDraw in atlas (native) pixels on a supersampled image: coordinates and widths are scaled by SS, after an
    optional origin shift (ox, oy) for drawing into a cell-sized mask with atlas coordinates."""
    def __init__(self, img, ox=0, oy=0):
        self.d, self.ox, self.oy = ImageDraw.Draw(img), ox, oy

    def _s(self, c):
        if all(isinstance(v, (int, float)) for v in c):
            return tuple((v - (self.ox if i % 2 == 0 else self.oy)) * SS for i, v in enumerate(c))
        return [self._s(v) for v in c]

    def __getattr__(self, name):
        fn = getattr(self.d, name)

        def call(xy, *a, **kw):
            if name in ("line", "arc") or "outline" in kw:
                kw["width"] = max(1, int(round(kw.get("width", 1) * SS)))
            return fn(self._s(xy), *a, **kw)
        return call


dc, dm, dh = SDraw(COL), SDraw(MET), SDraw(HGT)


class TM:
    """A text or shape mask at SS resolution; width / height are in atlas pixels."""
    def __init__(self, img):
        self.img = img

    width = property(lambda s: s.img.width / SS)
    height = property(lambda s: s.img.height / SS)

    def rotate(self, a, expand=True):
        return TM(self.img.rotate(a, expand=expand, resample=Image.BICUBIC))


def uv(r):
    x, y, w, h = r
    return [x / A, 1 - (y + h) / A, (x + w) / A, 1 - y / A]


def seed_of(s):
    return zlib.crc32(s.encode()) & 0xFFFF


def leather(W, H, base, seed, amount=7, pebble=True):
    """A supersampled leather surface (W x H atlas px): fine pebble grain, soft mottling, a few pale scuffs."""
    w, h = max(1, int(W * SS)), max(1, int(H * SS))
    g = np.random.default_rng(seed)
    a = np.empty((h, w, 3), np.float32)
    a[:] = base
    if pebble:
        n = Image.fromarray(np.uint8(np.clip(g.normal(128, 60, (h, w)), 0, 255))).filter(ImageFilter.GaussianBlur(0.9 * SS))
        a += ((np.asarray(n).astype(np.float32) - 128) * amount / 30)[..., None]
    a += g.normal(0, amount * 0.35, (h, w))[..., None]
    m = g.normal(128, 40, (max(2, h // 40), max(2, w // 40)))
    m = np.asarray(Image.fromarray(np.uint8(np.clip(m, 0, 255))).resize((w, h), Image.BICUBIC)).astype(np.float32) - 128
    a += (m * 0.03 * amount)[..., None]
    img = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    d = ImageDraw.Draw(img)
    for _ in range(int(W * H / 9000) + 1):
        x, y = g.uniform(0, w), g.uniform(0, h)
        L, ang = g.uniform(4, 16) * SS, g.uniform(0, math.pi)
        c = tuple(int(min(255, v * 1.35 + 14)) for v in base)
        d.line((x, y, x + math.cos(ang) * L, y + math.sin(ang) * L), fill=c, width=1)
    return img


def grain(img, amount=10, seed=0):
    """Fine grain on a plain (paper, card) surface already at SS resolution."""
    a = np.asarray(img).astype(np.float32)
    g = np.random.default_rng(seed)
    a += g.normal(0, amount * 0.6, a.shape[:2])[..., None]
    m = g.normal(128, 40, (max(2, a.shape[0] // 48), max(2, a.shape[1] // 48)))
    m = np.asarray(Image.fromarray(np.uint8(np.clip(m, 0, 255))).resize((a.shape[1], a.shape[0]), Image.BICUBIC)).astype(np.float32) - 128
    a += (m * 0.02 * amount)[..., None]
    return Image.fromarray(np.uint8(np.clip(a, 0, 255)))


def plain(W, H, colour, amount, seed):
    return grain(Image.new("RGB", (max(1, int(W * SS)), max(1, int(H * SS))), colour), amount=amount, seed=seed)


def paste_at(img, x, y):
    COL.paste(img, (int(round(x * SS)), int(round(y * SS))))


_fonts = {}


def font(key, size):
    k = (key, max(6, int(size)))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONTS[key], k[1])
    return _fonts[k]


def text_img(s, fk, size):
    f = font(fk, size * SS)
    l, t, r, b = f.getbbox(s)
    im = Image.new("L", (r - l + 4 * SS, b - t + 4 * SS), 0)
    ImageDraw.Draw(im).text((2 * SS - l, 2 * SS - t), s, font=f, fill=255)
    return TM(im)


def fit_text(s, fk, box_w, box_h, start=None):
    size = start or box_h
    while size > 5:
        m = text_img(s, fk, size)
        if m.width <= box_w and m.height <= box_h:
            return m
        size *= 0.94
    return text_img(s, fk, 5)


def gilt_fill(w, h, seed):
    """Tooled gold leaf: a soft light-to-dark sheen, fine flecks, and a few worn pinholes (returned as colour, alpha)."""
    g = np.random.default_rng(seed)
    t = np.linspace(0, 1, h)[:, None]
    hi, lo = np.array([238, 200, 118], np.float32), np.array([168, 124, 56], np.float32)
    sheen = 0.55 + 0.45 * np.cos((t - 0.3) * math.pi * 1.4)
    a = lo + (hi - lo) * np.clip(sheen, 0, 1)[..., None]
    a = np.broadcast_to(a, (h, w, 3)).copy()
    a += g.normal(0, 9, (h, w))[..., None]
    wear = Image.fromarray(np.uint8(np.clip(g.normal(128, 70, (max(2, h // 3), max(2, w // 3))), 0, 255))).resize((w, h), Image.BICUBIC)
    alpha = np.where(np.asarray(wear) > 222, 0.35, 1.0).astype(np.float32)
    return Image.fromarray(np.uint8(np.clip(a, 0, 255))), alpha


def stamp(mask, x, y, colour, metal=255, height=None, region=None):
    """Paste a mask (TM) at atlas (x, y). Gilt is tooled: pressed into the leather with a dark rim, then gold leaf with a sheen
    and a little wear; it also goes into the metal mask and the height map (debossed)."""
    if region is not None:
        x, y = region[0] + x, region[1] + y
    m = mask.img
    px, py = int(round(x * SS)), int(round(y * SS))
    if colour == GILT:
        rim = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8 * SS))
        rim = rim.point(lambda v: int(v * 0.55))
        COL.paste(Image.new("RGB", m.size, (14, 8, 6)), (px + SS // 2, py + SS // 2), rim)
        fill, alpha = gilt_fill(m.width, m.height, seed=(px * 7 + py) & 0xFFFFFF)
        ma = Image.fromarray(np.uint8(np.asarray(m).astype(np.float32) * alpha))
        COL.paste(fill, (px, py), ma)
        if metal:
            MET.paste(Image.new("L", m.size, metal), (px, py), ma)
        HGT.paste(Image.new("L", m.size, 92 if height is None else height), (px, py), m)
        return
    COL.paste(Image.new("RGB", m.size, colour), (px, py), m)
    if metal:
        MET.paste(Image.new("L", m.size, metal), (px, py), m)
    HGT.paste(Image.new("L", m.size, 96 if height is None else height), (px, py), m)


class Cell:
    """A cell-sized mask to draw gilt (or ink) rules into with atlas coordinates; stamped in one go at the end."""
    def __init__(self, r):
        self.r = r
        self.img = Image.new("L", (int(r[2] * SS), int(r[3] * SS)), 0)
        self.d = SDraw(self.img, r[0], r[1])

    def stamp(self, colour, metal=255, height=None):
        stamp(TM(self.img), self.r[0], self.r[1], colour, metal, height)


# ------------------------------------------------------------------ book designs

TITLES = [
    "A History of the Institution", "Moonlight Botany", "The Raven's Almanac", "Candles & Wax", "Night Garden Herbal",
    "Common Spirits", "Tables of the Tides", "Clockwork", "The Quiet Corridor", "Latin for Beginners", "A Grammar of Shadows",
    "Old Maps of the Moor", "Star Charts", "Bells & Chimes", "The Ghost Who Read", "Verses at Dusk", "Collected Riddles",
    "Owls of the North", "Iron & Brass", "A Field Guide to Bats", "Mushrooms of the Wood", "Lantern Lore", "The Ink Club",
    "Hymns for Evensong", "The Fencing Manual", "Manners for Students", "Rules of the Library", "The Crimson Moon",
    "The Blue Moon", "Geometry", "Arithmetic", "Algebra II", "Chemistry", "Astronomy", "Natural History", "Poetry",
    "Folk Tales", "Mysteries", "Philosophy", "Music Theory", "Drawing", "Cartography", "Weather Signs", "Gardening",
    "Old Recipes", "Knots & Rope", "Ciphers", "Wolves of the Moor", "The Hollow Hill", "Sleepwalkers", "The Midnight Bell",
    "Founders' Day", "School Songs", "Gargoyles", "Stonework", "Stained Glass", "Weaving", "Reading Tea Leaves",
    "Chess Openings", "Puzzles", "Sea Stories", "Ghost Ships", "Haunted Inns", "The Long Night", "Frost & Fog",
    "The Clock Tower", "Lost Languages", "Moths", "Ravens & Rooks", "The Lamplighter", "Secret Passages", "Old Ballads",
    "The Moor at Dusk", "Physics", "Biology", "Geography", "Rhetoric", "Logic", "The Library Cat", "Inkwells",
    "The Bell Ringer", "Book of Hours", "The Glass Garden", "Candlelight Tales", "The Owl Prefect",
]
SETS = [("Encyclopaedia", 12, "oxblood", 0.22, 1.28), ("Annals", 8, "ink", 0.2, 1.12), ("Bestiary", 6, "green", 0.24, 1.05),
        ("Herbarium", 5, "calf", 0.26, 1.18), ("Almanac", 6, "black", 0.16, 0.95), ("Lexicon", 4, "crimson", 0.3, 1.3)]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
EMBLEMS = ["star", "crescent", "key", "foil", "none", "none"]
TFONTS = ["pala", "geo", "cam", "con", "times", "palai"]


def emblem(d, kind, cx, cy, r):
    """A small tooled emblem drawn into a gilt mask (d draws 255 = gilt)."""
    if kind == "star":
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.42
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=255)
    elif kind == "crescent":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        d.ellipse((cx - r + r * 0.55, cy - r - r * 0.25, cx + r + r * 0.55, cy + r - r * 0.25), fill=0)
    elif kind == "key":
        lw = max(1.5, r * 0.2)
        d.ellipse((cx - r * 1.0, cy - r * 0.5, cx - r * 0.1, cy + r * 0.5), outline=255, width=lw)
        d.line((cx - r * 0.1, cy, cx + r * 1.1, cy), fill=255, width=lw)
        d.line((cx + r * 0.7, cy, cx + r * 0.7, cy + r * 0.45), fill=255, width=lw)
        d.line((cx + r * 1.0, cy, cx + r * 1.0, cy + r * 0.45), fill=255, width=lw)
    elif kind == "foil":
        for a in range(4):
            ang = a * math.pi / 2
            ox, oy = cx + math.cos(ang) * r * 0.5, cy + math.sin(ang) * r * 0.5
            d.ellipse((ox - r * 0.48, oy - r * 0.48, ox + r * 0.48, oy + r * 0.48), outline=255, width=max(1.2, r * 0.15))
    return kind


def fleuron(d, cx, cy, r):
    """A tiny tooled ornament for an empty panel: a diamond with four dots."""
    d.polygon([(cx - r, cy), (cx, cy - r * 0.6), (cx + r, cy), (cx, cy + r * 0.6)], fill=255)
    for dx, dy in ((-1.5, 0), (1.5, 0), (0, -1.1), (0, 1.1)):
        q = r * 0.2
        d.ellipse((cx + dx * r - q, cy + dy * r - q, cx + dx * r + q, cy + dy * r + q), fill=255)


def draw_spine(key, w, h, leather_name, title, vol=None, style=None, seed=0, fk=None):
    """One spine cell: (h * PPS) x (w * PPS) atlas px; drawn at SS."""
    cw, ch = h * PPS, w * PPS
    r = PK.add(key, cw, ch)
    x0, y0, W, H = r
    base = LEATHERS[leather_name]
    light = leather_name in ("vellum", "bone", "tan")
    cell = leather(W, H, base, seed, amount=5 if light else 7)
    a = np.asarray(cell).astype(np.float32)
    rh, rw = a.shape[:2]
    v = np.linspace(-1, 1, rh)[:, None]
    u = np.linspace(0, 1, rw)[None, :]
    a *= (0.74 + 0.34 * (1 - v ** 2))[..., None]                                     # the rounded spine
    a *= (1 - 0.22 * np.exp(-u / 0.025) - 0.22 * np.exp(-(1 - u) / 0.025))[..., None]  # darker, handled head and tail
    rub = np.exp(-(1 - np.abs(v)) / 0.05) * 0.18                                      # rubbed pale along the joints
    a += (rub * 90)[..., None]
    if light:                                                                           # old foxing on vellum
        g = np.random.default_rng(seed + 1)
        f = np.asarray(Image.fromarray(np.uint8(np.clip(g.normal(128, 60, (max(2, rh // 16), max(2, rw // 16))), 0, 255)))
                       .resize((rw, rh), Image.BICUBIC)).astype(np.float32)
        a *= (1 - np.clip((f - 160) / 400, 0, 0.12))[..., None]
    paste_at(Image.fromarray(np.uint8(np.clip(a, 0, 255))), x0, y0)
    HGT.paste(Image.new("L", (int(W * SS), int(H * SS)), 128), (int(x0 * SS), int(y0 * SS)))
    lr = random.Random(seed)
    style = style or lr.choice(["bands", "bands", "label", "plain", "panel"])
    tcol, tmet = (INK, 0) if light and lr.random() < 0.6 else (GILT, 255)
    G = Cell(r)                       # all of the spine's rules, borders and ornaments, tooled together
    gd = G.d
    # head and tail fillets: a thick rule between two hairlines
    for t0 in (0.045, 0.955):
        for off, wd in ((-0.012, 0.8), (0.0, 2.2), (0.012, 0.8)):
            xx = x0 + (t0 + off * (1 if t0 < 0.5 else -1)) * W
            gd.line((xx, y0 + 2, xx, y0 + H - 2), fill=255, width=wd)
    # raised bands across the spine
    nb = {"bands": lr.choice([4, 5]), "label": 4, "panel": 2, "plain": 0}[style]
    band_u = [0.16 + k * (0.7 / max(1, nb - 1)) for k in range(nb)]
    dotted = lr.random() < 0.5
    long_ = bool(title) and len(title) >= (10 if style == "label" else 12)
    if style in ("bands", "label") and len(band_u) >= 2:
        ta, tb = band_u[0], band_u[min(2, len(band_u) - 1)] if long_ else band_u[1]
    else:
        ta, tb = 0.13, 0.78
    for t in band_u:
        if ta + 0.01 < t < tb - 0.01:
            continue                  # no band across the title
        xx = x0 + t * W
        bw = max(4.0, W * 0.017)
        steps = int(bw * 2 * SS)
        for i in range(steps + 1):
            o = -bw + i / SS
            f = 1 - abs(o) / bw
            cc = tuple(int(min(255, c * (0.5 + 0.8 * f) + 26 * f ** 6)) for c in base)
            dc.line((xx + o, y0, xx + o, y0 + H), fill=cc, width=1 / SS)
            dh.line((xx + o, y0, xx + o, y0 + H), fill=int(128 + 95 * f), width=1 / SS)
        for s_ in (-bw - 2.2, bw + 2.2):
            gd.line((xx + s_, y0 + 3, xx + s_, y0 + H - 3), fill=255, width=1.1)
        if dotted:
            for j in range(int(H / 6)):
                yy = y0 + 4 + j * 6
                gd.ellipse((xx - 1.1, yy - 1.1, xx + 1.1, yy + 1.1), fill=255)
    # the title area: between bands 0 and 1 (label / bands styles; two panels for a long title), or most of the spine
    tx0, tx1 = x0 + ta * W + 8, x0 + tb * W - 8
    if style == "label":
        lab = LEATHERS["black"] if leather_name not in ("black", "slate") else LEATHERS["crimson"]
        paste_at(leather(tx1 - tx0, H * 0.72, lab, seed + 7, amount=4), tx0, y0 + H * 0.14)
        dh.rectangle((tx0, y0 + H * 0.14, tx1, y0 + H * 0.86), fill=146)
        gd.rectangle((tx0 + 3, y0 + H * 0.14 + 3, tx1 - 3, y0 + H * 0.86 - 3), outline=255, width=1.6)
        gd.rectangle((tx0 + 6, y0 + H * 0.14 + 6, tx1 - 6, y0 + H * 0.86 - 6), outline=255, width=0.7)
        tcol, tmet = GILT, 255
    if style == "panel":
        gd.rectangle((tx0 - 4, y0 + 6, tx1 + 4, y0 + H - 7), outline=255, width=2.2)
        gd.rectangle((tx0 - 1, y0 + 9, tx1 + 1, y0 + H - 10), outline=255, width=0.8)
        for cx_, cy_ in ((tx0 + 3, y0 + 15), (tx1 - 3, y0 + 15), (tx0 + 3, y0 + H - 16), (tx1 - 3, y0 + H - 16)):
            fleuron(gd, cx_, cy_, 3.2)
    fk = fk or lr.choice(TFONTS)
    if title:
        bw_, bh_ = tx1 - tx0 - 10, H * (0.56 if style == "label" else 0.62)
        if w >= 0.27 and len(title) <= 9:
            # a short title across the spine (reads left to right with the book standing): rotated in the cell
            m = fit_text(title, fk, bh_, (tx1 - tx0) * 0.8).rotate(90, expand=True)
        else:
            m = fit_text(title, fk, bw_, bh_)
        stamp(m, (tx0 + tx1) / 2 - m.width / 2, y0 + H / 2 - m.height / 2, tcol, tmet)
    used = {0} if style in ("bands", "label") else set(range(len(band_u)))
    if style in ("bands", "label") and long_:
        used.add(1)
    if vol:
        cx = x0 + ((band_u[-2] + band_u[-1]) / 2 if len(band_u) >= 3 else 0.86) * W
        m = fit_text(vol, "pala", W * 0.09, H * 0.55).rotate(90, expand=True) if len(vol) <= 4 else fit_text(vol, "pala", W * 0.12, H * 0.5)
        stamp(m, cx - m.width / 2, y0 + H / 2 - m.height / 2, tcol, tmet)
        used.add(len(band_u) - 2)
    else:
        em = lr.choice(EMBLEMS)
        if em != "none" and len(band_u) >= 3:
            cx = x0 + (band_u[-2] + band_u[-1]) / 2 * W
            emblem(gd, em, cx, y0 + H / 2, min(H * 0.26, W * 0.035))
            used.add(len(band_u) - 2)
    # a little fleuron in every empty panel between bands
    if tmet:
        for k in range(len(band_u) - 1):
            if k not in used:
                fleuron(gd, x0 + (band_u[k] + band_u[k + 1]) / 2 * W, y0 + H / 2, min(H * 0.16, 7))
    G.stamp(tcol, tmet)
    REG[key] = uv(r)


PK = Packer(A, A)


def make_books():
    """Collect every design, then draw them narrowest-last so the atlas rows pack tightly."""
    specs = []
    k = 0
    for name, n, leather, w, h in SETS:          # the matching sets first (Encyclopaedia I-XII and friends)
        fk = rnd.choice(TFONTS[:4])
        for i in range(n):
            specs.append(dict(key=f"Book{k:03d}", w=w, h=h, leather=leather, title=name, vol=ROMAN[i], style="bands", seed=100 + k, fk=fk,
                              set=name, paper="giltedge" if leather in ("oxblood", "crimson") else "paper"))
            k += 1
    for t in TITLES:
        leather = rnd.choice(list(LEATHERS))
        w = round(rnd.choice([0.13, 0.15, 0.17, 0.19, 0.21, 0.24, 0.27, 0.3]), 2)
        h = round(rnd.uniform(0.82, 1.32), 2)
        if len(t) > 16:
            w, h = max(w, 0.17), max(h, 1.05)
        specs.append(dict(key=f"Book{k:03d}", w=w, h=h, leather=leather, title=t, vol=None, style=None, seed=500 + k, fk=None, set=None,
                          paper=rnd.choice(["paper", "aged", "paper", "giltedge"])))
        k += 1
    for i in range(16):                          # a few plain (untitled) old volumes
        leather = rnd.choice(["calf", "black", "oxblood", "slate", "tan", "plum"])
        w, h = round(rnd.uniform(0.14, 0.3), 2), round(rnd.uniform(0.85, 1.25), 2)
        specs.append(dict(key=f"Book{k:03d}", w=w, h=h, leather=leather, title=None, vol=None, style=rnd.choice(["bands", "plain", "panel"]),
                          seed=900 + k, fk=None, set=None, paper="aged"))
        k += 1
    for sp in sorted(specs, key=lambda d: -d["w"]):
        draw_spine(sp["key"], sp["w"], sp["h"], sp["leather"], sp["title"], vol=sp["vol"], style=sp["style"], seed=sp["seed"], fk=sp["fk"])
    for sp in specs:
        BOOKS.append({"key": sp["key"], "w": sp["w"], "h": sp["h"], "leather": sp["leather"], "set": sp["set"], "paper": sp["paper"]})


# ------------------------------------------------------------------ swatches, plaques, labels

def make_swatches():
    for name, c in list(LEATHERS.items()) + list(PAPERS.items()) + [("gilt", GILT), ("inkblack", INK), ("cardwhite", (226, 216, 190))]:
        r = PK.add(f"Swatch_{name}", 40, 40)
        paste_at(plain(r[2], r[3], c, 4, seed_of(name)), r[0], r[1])
        if name in ("gilt", "giltedge"):
            dm.rectangle((r[0], r[1], r[0] + r[2], r[1] + r[3]), fill=255)
        REG[f"Swatch_{name}"] = uv(r)


def plaque(key, text, w_px, h_px, bg, fg, fk="pala", metal=True, border=True, sub=None):
    r = PK.add(key, w_px, h_px)
    x0, y0, W, H = r
    if bg[0] + bg[1] + bg[2] < 330:
        paste_at(leather(W, H, bg, seed_of(key), amount=4), x0, y0)
    else:
        paste_at(plain(W, H, bg, 5, seed_of(key)), x0, y0)
    if border:
        G = Cell(r)
        G.d.rectangle((x0 + 6, y0 + 6, x0 + W - 7, y0 + H - 7), outline=255, width=max(2.0, H / 30))
        G.d.rectangle((x0 + 13, y0 + 13, x0 + W - 14, y0 + H - 14), outline=255, width=max(0.8, H / 110))
        for cx_, cy_ in ((x0 + 13, y0 + H / 2), (x0 + W - 14, y0 + H / 2)):
            fleuron(G.d, cx_, cy_, H * 0.06)
        G.stamp(fg, 255 if metal else 0, height=170 if metal else 96)
    hh = H * (0.5 if sub else 0.62)
    m = fit_text(text, fk, W - 50, int(hh))
    stamp(m, x0 + W / 2 - m.width / 2, y0 + (H * (0.42 if sub else 0.5)) - m.height / 2, fg, 255 if metal else 0, height=170 if metal else 96)
    if sub:
        m2 = fit_text(sub, "palai", W - 80, int(H * 0.2))
        stamp(m2, x0 + W / 2 - m2.width / 2, y0 + H * 0.78 - m2.height / 2, fg, 255 if metal else 0, height=170 if metal else 96)
    REG[key] = uv(r)


def make_plaques():
    cats = ["HISTORY", "ASTRONOMY", "BOTANY", "POETRY", "ALCHEMY", "MAPS & CHARTS", "LANGUAGES", "MATHEMATICS", "FOLKLORE", "MUSIC"]
    for c in cats:
        plaque(f"Cat_{c}", c, 620, 150, (24, 20, 20), GILT)
    plaque("Plaque_RESTRICTED", "RESTRICTED", 760, 190, (96, 14, 26), GILT, sub="by order of the Librarian")
    plaque("Plaque_RETURNS", "RETURNS", 620, 180, (24, 20, 20), GILT, sub="books only, please")
    plaque("Plaque_QUIET", "QUIET PLEASE", 620, 150, (214, 202, 172), INK, metal=False)
    plaque("Plaque_LIBRARIAN", "LIBRARIAN", 560, 140, (24, 20, 20), GILT)
    plaque("Plaque_CATALOGUE", "CATALOGUE", 560, 140, (24, 20, 20), GILT)
    plaque("Plaque_MAPS", "PLANS & MAPS", 560, 140, (24, 20, 20), GILT)
    plaque("Plaque_PAPERS", "NEWSPAPERS", 560, 140, (24, 20, 20), GILT)
    plaque("Plaque_FORBIDDEN", "DO NOT OPEN", 520, 140, (214, 202, 172), (96, 14, 26), metal=False)
    # card-catalogue drawer labels: little white cards with ink letters
    ranges = ["A", "B", "C", "D", "E", "F", "G", "H", "I-J", "K", "L", "M", "N", "O", "P", "Q-R", "S", "T", "U-V", "W", "X-Z",
              "Ab-Al", "Am-Az", "Ba-Be", "Bi-Bz", "Ca-Ch", "Ci-Cz", "Da-Dz", "Ea-Ez", "Fa-Fz"]
    for i, t in enumerate(ranges):
        plaque(f"Drawer_{i}", t, 150, 80, (226, 216, 190), INK, fk="geo", metal=False, border=False)
    # tiny spine labels for the scroll tags
    for i, t in enumerate(["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]):
        plaque(f"Tag_{i}", t, 90, 90, (214, 202, 172), INK, fk="pala", metal=False, border=False)


# ------------------------------------------------------------------ printed sheets

def greek(d, x0, y0, x1, y1, line_h, ink=INK, rng=None, para=6, fill=0.9):
    """Lines of tiny 'text' (word blocks) for page bodies: illegible at a distance, like real print."""
    rng = rng or random.Random(1)
    y = y0
    n = 0
    while y + line_h * 0.6 < y1:
        x = x0 + (line_h * 1.5 if n % para == 0 else 0)
        end = x1 if (n % para) != para - 1 else x0 + (x1 - x0) * rng.uniform(0.3, 0.8)
        while x < end:
            wl = rng.uniform(1.2, 6.0) * line_h * 0.5
            if x + wl > end:
                break
            d.rectangle((x, y + line_h * 0.25, x + wl, y + line_h * 0.62), fill=ink)
            x += wl + line_h * 0.35
        y += line_h
        n += 1


def sheet(key, W, H, bg=(222, 208, 172)):
    r = PK.add(key, W, H)
    paste_at(plain(W, H, bg, 5, seed_of(key)), r[0], r[1])
    REG[key] = uv(r)
    return r


def put_text(r, s, fk, cx, cy, maxw, maxh, colour=INK, metal=0):
    m = fit_text(s, fk, int(maxw), int(maxh))
    stamp(m, r[0] + cx - m.width / 2, r[1] + cy - m.height / 2, colour, metal)


def make_newspapers():
    heads = [("MIDNIGHT BELL RINGS TWICE", "Students report a second chime at a quarter past twelve"),
             ("BLUE MOON TONIGHT", "The Astronomy Club invites all to the tower roof"),
             ("CHOIR WINS THE CUP", "Evensong singers bring the silver home again")]
    for i, (h, sub) in enumerate(heads):
        r = sheet(f"News_{i}", 560, 760, (214, 206, 186))
        x0, y0 = r[0], r[1]
        put_text(r, "The Nightmare Herald", "pala", 280, 52, 500, 70)
        dc.line((x0 + 24, y0 + 96, x0 + 536, y0 + 96), fill=INK, width=3)
        dc.line((x0 + 24, y0 + 102, x0 + 536, y0 + 102), fill=INK, width=1)
        put_text(r, "Vol. XIII  ·  Price one penny  ·  Evening Edition", "plain", 280, 116, 480, 18)
        put_text(r, h, "times", 280, 170, 510, 64)
        put_text(r, sub, "geoi", 280, 222, 500, 24)
        # a picture box and columns
        rr = random.Random(40 + i)
        dc.rectangle((x0 + 30, y0 + 250, x0 + 300, y0 + 440), fill=(160, 150, 128), outline=INK, width=2)
        if i == 1:
            dc.ellipse((x0 + 120, y0 + 290, x0 + 210, y0 + 380), fill=(200, 208, 226))
        elif i == 0:
            dc.polygon([(x0 + 165, y0 + 270), (x0 + 120, y0 + 340), (x0 + 210, y0 + 340)], fill=INK)
            dc.rectangle((x0 + 140, y0 + 340, x0 + 190, y0 + 430), fill=INK)
        else:
            for k in range(5):
                dc.ellipse((x0 + 60 + k * 45, y0 + 330, x0 + 95 + k * 45, y0 + 365), fill=INK)
                dc.rectangle((x0 + 63 + k * 45, y0 + 365, x0 + 92 + k * 45, y0 + 430), fill=INK)
        for cx0, cy0, cx1 in ((316, 250, 536), (30, 456, 270), (290, 456, 536)):
            greek(dc, x0 + cx0, y0 + cy0, x0 + cx1, y0 + 730, 13, rng=rr)


def make_ledger():
    r = sheet("Ledger", 760, 540, (226, 214, 182))
    x0, y0 = r[0], r[1]
    put_text(r, "Borrowed & Returned", "palai", 380, 34, 520, 40)
    for k in range(14):
        y = y0 + 80 + k * 32
        dc.line((x0 + 20, y, x0 + 740, y), fill=(120, 130, 160), width=1)
    for xx in (200, 470, 610):
        dc.line((x0 + xx, y0 + 60, x0 + xx, y0 + 520), fill=(150, 40, 50), width=2)
    for i, (n, b, d) in enumerate([("R. Vale", "Moon Tables", "13th"), ("E. Thorne", "A Field Guide to Bats", "14th"),
                                   ("M. Ashby", "The Hollow Hill", "15th"), ("J. Crane", "Latin for Beginners", "15th"),
                                   ("S. Blackwood", "Star Charts", "18th"), ("T. Moss", "Ghost Ships", "19th"),
                                   ("A. Finch", "Owls of the North", "20th"), ("L. Grey", "Ciphers", "21st"),
                                   ("P. Hale", "Old Ballads", "21st"), ("C. Wren", "Clockwork", "22nd")]):
        y = 66 + i * 32 + 16
        put_text(r, n, "hand", 108, y, 170, 26)
        put_text(r, b, "hand", 335, y, 250, 26)
        put_text(r, d, "hand", 540, y, 110, 26)
        if i < 7:
            put_text(r, "returned", "hand", 675, y, 120, 24, colour=(110, 20, 30))


def make_pages():
    # spread 1: on the phases of the moon
    r = sheet("Pages_Moon", 1000, 680)
    x0, y0 = r[0], r[1]
    dc.line((x0 + 500, y0, x0 + 500, y0 + 680), fill=(170, 150, 110), width=4)
    put_text(r, "On the Phases of the Moon", "palai", 250, 60, 400, 46)
    for k in range(8):
        cx, cy, rr = x0 + 80 + (k % 4) * 115, y0 + 150 + (k // 4) * 120, 38
        dc.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(232, 224, 196), outline=INK, width=2)
        ph = (k / 8) * 2 * math.pi
        off = math.cos(ph) * rr
        if k != 0:
            box_ = (cx - rr, cy - rr, cx + rr, cy + rr)
            if k < 4:
                dc.pieslice(box_, 90, 270, fill=INK)
            elif k > 4:
                dc.pieslice(box_, -90, 90, fill=INK)
            else:
                dc.ellipse(box_, fill=(232, 224, 196), outline=INK, width=2)
            dc.ellipse((cx - abs(off), cy - rr, cx + abs(off), cy + rr), fill=INK if k in (1, 7, 2, 6) and abs(off) > 3 else (232, 224, 196))
        dc.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=INK, width=2)
    greek(dc, x0 + 50, y0 + 360, x0 + 460, y0 + 640, 18, rng=random.Random(5))
    put_text(r, "The Blue Moon", "palai", 750, 60, 380, 44)
    dc.ellipse((x0 + 650, y0 + 100, x0 + 850, y0 + 300), fill=(150, 170, 210), outline=INK, width=3)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        dc.ellipse((x0 + 750 + math.cos(a) * 60 - 12, y0 + 200 + math.sin(a) * 50 - 9, x0 + 750 + math.cos(a) * 60 + 12, y0 + 200 + math.sin(a) * 50 + 9),
                   outline=(90, 100, 140), width=2)
    greek(dc, x0 + 540, y0 + 330, x0 + 950, y0 + 640, 18, rng=random.Random(6))
    stamp(fit_text("~ 13 ~", "palai", 80, 24), x0 + 230, y0 + 645, INK, 0)
    # spread 2: a bestiary page with a raven
    r = sheet("Pages_Raven", 1000, 680)
    x0, y0 = r[0], r[1]
    dc.line((x0 + 500, y0, x0 + 500, y0 + 680), fill=(170, 150, 110), width=4)
    put_text(r, "Bestiary: the Raven", "palai", 250, 60, 420, 46)
    rv = [(170, 360), (210, 300), (250, 270), (300, 262), (330, 230), (360, 228), (392, 238), (360, 252), (340, 270), (360, 330),
          (340, 400), (300, 440), (380, 520), (330, 520), (270, 460), (230, 450), (190, 470), (200, 430), (180, 400)]
    dc.polygon([(x0 + a, y0 + b) for a, b in rv], fill=INK)
    dc.ellipse((x0 + 340, y0 + 236, x0 + 350, y0 + 246), fill=(222, 208, 172))
    dc.line((x0 + 150, y0 + 525, x0 + 420, y0 + 525), fill=INK, width=4)
    greek(dc, x0 + 540, y0 + 110, x0 + 950, y0 + 640, 18, rng=random.Random(7))
    dc.rectangle((x0 + 540, y0 + 110, x0 + 600, y0 + 170), fill=(96, 14, 26))
    put_text(r, "R", "pala", 570, 140, 50, 50, colour=GILT, metal=255)
    # spread 3: library rules
    r = sheet("Pages_Rules", 1000, 680)
    x0, y0 = r[0], r[1]
    dc.line((x0 + 500, y0, x0 + 500, y0 + 680), fill=(170, 150, 110), width=4)
    put_text(r, "Rules of the Library", "palai", 250, 60, 420, 46)
    for i, t in enumerate(["I. Silence in the stacks.", "II. No candles near the shelves.", "III. Return books by the bell.",
                           "IV. Mind the ladders.", "V. Never open the locked case.", "VI. Feed nothing that asks."]):
        put_text(r, t, "geoi", 250, 140 + i * 72, 420, 34)
    greek(dc, x0 + 540, y0 + 90, x0 + 950, y0 + 640, 18, rng=random.Random(8))


def make_map():
    r = sheet("Map_Moor", 1100, 760, (214, 196, 150))
    x0, y0 = r[0], r[1]
    rr = random.Random(77)
    # coastline: a wobbly closed outline
    cx, cy = x0 + 560, y0 + 400
    pts = []
    for k in range(90):
        a = k / 90 * 2 * math.pi
        rad = 300 + 60 * math.sin(a * 3 + 1) + 30 * math.sin(a * 7) + rr.uniform(-12, 12)
        pts.append((cx + math.cos(a) * rad * 1.35, cy + math.sin(a) * rad * 0.9))
    dc.polygon(pts, fill=(196, 176, 128), outline=INK)
    for k in range(len(pts)):
        dc.line((pts[k], pts[(k + 1) % len(pts)]), fill=INK, width=3)
    # hills, trees, a river, the school
    for k in range(26):
        hx, hy = cx + rr.uniform(-330, 330), cy + rr.uniform(-200, 200)
        dc.arc((hx - 18, hy - 12, hx + 18, hy + 12), 180, 360, fill=INK, width=2)
    for k in range(30):
        tx, ty = cx + rr.uniform(-300, -60), cy + rr.uniform(20, 200)
        dc.polygon([(tx, ty - 14), (tx - 8, ty + 6), (tx + 8, ty + 6)], outline=INK)
    dc.line([(cx + 380, cy - 220), (cx + 200, cy - 120), (cx + 120, cy - 20), (cx + 60, cy + 110), (cx - 40, cy + 230)], fill=(60, 80, 120), width=5)
    dc.rectangle((cx - 30, cy - 70, cx + 30, cy - 20), outline=INK, width=3)
    dc.polygon([(cx - 36, cy - 70), (cx, cy - 110), (cx + 36, cy - 70)], outline=INK)
    put_text(r, "The Institution", "palai", 560, 400 - 150, 220, 28)
    put_text(r, "The Moor", "palai", 460, 560, 220, 34)
    put_text(r, "Raven Wood", "palai", 360, 470, 200, 26)
    put_text(r, "A Plan of the Moor & the School", "pala", 550, 50, 700, 46)
    # compass rose
    rx, ry = x0 + 960, y0 + 640
    for a in range(8):
        ang = a * math.pi / 4
        L = 70 if a % 2 == 0 else 38
        dc.polygon([(rx, ry), (rx + math.cos(ang + 0.2) * 14, ry + math.sin(ang + 0.2) * 14), (rx + math.cos(ang) * L, ry + math.sin(ang) * L)],
                   fill=(96, 14, 26) if a % 2 == 0 else INK)
    put_text(r, "N", "pala", 960, 640 - 92, 30, 30)
    dc.rectangle((x0 + 10, y0 + 10, x0 + 1090, y0 + 750), outline=INK, width=4)


def make_cards():
    r = sheet("Card", 320, 200, (226, 216, 190))
    x0, y0 = r[0], r[1]
    for k in range(6):
        dc.line((x0 + 12, y0 + 52 + k * 24, x0 + 308, y0 + 52 + k * 24), fill=(130, 150, 190), width=1)
    dc.line((x0 + 12, y0 + 40, x0 + 308, y0 + 40), fill=(170, 40, 50), width=2)
    put_text(r, "Moonlight Botany", "hand", 160, 22, 280, 30)
    put_text(r, "shelf 7  ·  row C", "hand", 160, 66, 240, 22)
    dc.ellipse((x0 + 150, y0 + 170, x0 + 170, y0 + 190), fill=(120, 110, 90))


def make_scroll():
    r = sheet("Scroll", 600, 300, (214, 196, 150))
    greek(dc, r[0] + 40, r[1] + 40, r[0] + 560, r[1] + 270, 16, rng=random.Random(9))


def make_globe():
    """An invented world (not Earth): bone continents with ink coasts on an ink-teal sea, a graticule, a cartouche.
    4096 x 2048, drawn at twice that and filtered down."""
    W, H = 8192, 4096
    g = np.random.default_rng(3030)

    def fbm(oct_=7):
        acc = np.zeros((H, W), np.float32)
        amp, tot = 1.0, 0.0
        for o in range(oct_):
            n = 4 * 2 ** o
            base = g.normal(0, 1, (n // 2 + 1, n + 1)).astype(np.float32)
            base[:, -1] = base[:, 0]                      # wraps round the globe
            acc += np.asarray(Image.fromarray(base).resize((W, H), Image.BICUBIC)) * amp
            tot += amp
            amp *= 0.5
        return acc / tot
    f = fbm()
    lat = np.linspace(-1, 1, H)[:, None]
    hgt = f - 0.25 * lat ** 2
    land = hgt > 0.22
    sea = np.array([34, 62, 72], np.float32)
    bone = np.array([206, 190, 150], np.float32)
    img = np.where(land[..., None], bone, sea)
    img -= np.where(land, np.clip((hgt - 0.3) * 160, 0, 40), 0)[..., None]          # hill shading inland
    img -= np.where(~land, np.clip((0.22 - hgt) * 120, 0, 18), 0)[..., None]        # deeper sea further out
    img += g.normal(0, 4, img.shape[:2])[..., None]
    im = Image.fromarray(np.uint8(np.clip(img, 0, 255)))
    landm = Image.fromarray(np.uint8(land * 255))
    edges = landm.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
    shore = landm.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(6))
    im.paste(Image.new("RGB", (W, H), (60, 92, 100)), (0, 0), Image.fromarray(np.uint8(np.asarray(shore) * (1 - land) * 0.5)))
    im.paste(Image.new("RGB", (W, H), (30, 24, 22)), (0, 0), edges)
    d = ImageDraw.Draw(im)
    for k in range(1, 12):
        y = int(k / 12 * H)
        d.line((0, y, W, y), fill=(170, 140, 80), width=2 if k != 6 else 6)
    for k in range(24):
        x = int(k / 24 * W)
        d.line((x, 0, x, H), fill=(170, 140, 80), width=2)

    def gtext(s, fk, size):
        f = ImageFont.truetype(FONTS[fk], size)
        l, t, r, b = f.getbbox(s)
        m = Image.new("L", (r - l + 8, b - t + 8), 0)
        ImageDraw.Draw(m).text((4 - l, 4 - t), s, font=f, fill=255)
        return m
    placed = []
    sea_m = ~np.asarray(landm.filter(ImageFilter.MaxFilter(41))).astype(bool)
    for name in ("MARE NOCTIS", "THE PALE SEA", "OCEANUS CORVUS", "THE STILL WATERS"):
        m = gtext(name, "palai", 136)
        best = None
        for y in range(900, H - 900, 160):
            for x in range(200, W - m.width - 200, 160):
                if not sea_m[y:y + m.height:8, x:x + m.width:8].all():
                    continue
                dmin = min([abs(x - px) + abs(y - py) for px, py in placed] + [9e9])
                score = dmin - abs(y - H / 2) * 0.6
                if best is None or score > best[0]:
                    best = (score, x, y)
        if best:
            im.paste(Image.new("RGB", m.size, (190, 170, 120)), (best[1], best[2]), m)
            placed.append((best[1], best[2]))
    # the cartouche, in open sea too
    cw_, ch_ = 1300, 420
    spot = None
    for y in range(1200, H - 1200, 120):
        for x in range(300, W - cw_ - 300, 120):
            if sea_m[y:y + ch_:10, x:x + cw_:10].all() and all(abs(x - px) + abs(y - py) > 1400 for px, py in placed):
                spot = (x, y)
                break
        if spot:
            break
    if spot:
        x, y = spot
        d.rectangle((x, y, x + cw_, y + ch_), fill=(206, 190, 150), outline=(30, 24, 22), width=16)
        d.rectangle((x + 40, y + 40, x + cw_ - 40, y + ch_ - 40), outline=(30, 24, 22), width=4)
        size = 136
        m = gtext("ORBIS NOCTURNUS", "pala", size)
        while m.width > cw_ - 160:
            size -= 6
            m = gtext("ORBIS NOCTURNUS", "pala", size)
        im.paste(Image.new("RGB", m.size, (30, 24, 22)), (x + cw_ // 2 - m.width // 2, y + ch_ // 2 - m.height // 2), m)
    im.resize((4096, 2048), Image.LANCZOS).save(os.path.join(OUT, "LibraryGlobe_color.png"))


if __name__ == "__main__":
    make_books()
    make_map()
    make_newspapers()
    make_pages()
    make_ledger()
    make_scroll()
    make_cards()
    make_plaques()
    make_swatches()
    # filtered down from the supersampled canvases
    COL.resize((A, A), Image.LANCZOS).save(os.path.join(OUT, "LibraryAtlas_color.png"))
    MET.resize((A, A), Image.LANCZOS).save(os.path.join(OUT, "LibraryAtlas_gilt.png"))
    HGT.filter(ImageFilter.GaussianBlur(0.8 * SS)).resize((A, A), Image.LANCZOS).save(os.path.join(OUT, "LibraryAtlas_height.png"))
    make_globe()
    json.dump({"regions": REG, "books": BOOKS, "pps": PPS, "size": A}, open(os.path.join(HERE, "library_atlas.json"), "w"), indent=0)
    print(f"{len(BOOKS)} books, {len(REG)} regions, atlas filled to y={PK.y + PK.row} of {A}")
