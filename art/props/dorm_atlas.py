"""The dorm room kit's printed atlases (props batch 34, the dorm kit). Run with the system Python (PIL + numpy):

  python art/props/dorm_atlas.py

DormPrint  certificates (the crest, gilt rules, blackletter titles), the overdue notices, loose papers and a marked test,
           the pizza box print, three soda can wraps, the mug's wrap, the night seen through the dorm window, swatches
DormCloth  the clothes' flat patterns: a school blazer, a shirt, a sweater, trousers, a scarf, a tee, a tie

Writes art/props/textures/Dorm{Print,Cloth}_{color,gilt,height}.png (4096; gilt = the metal mask; height = a bump for raised
gilt and debossed lettering) and art/props/dorm_atlas.json: every region's UV rect [u0, v0, u1, v1] (v up, as Blender reads
images) and each garment's flat outline in studs. nh_props_batch34_dorm.py maps faces onto these regions (a "Spine" UV
layer, as the library kit does) and bakes them. Everything is drawn at twice the size and filtered down. All text is
original and family-friendly.
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
SS = 2
F = "C:/Windows/Fonts/"
FONTS = {"pala": F + "palab.ttf", "palar": F + "pala.ttf", "palai": F + "palai.ttf", "palabi": F + "palabi.ttf", "geo": F + "georgiab.ttf",
         "geor": F + "georgia.ttf", "black": F + "gothicg_.ttf", "script": F + "segoesc.ttf", "scriptb": F + "segoescb.ttf",
         "hand": F + "Inkfree.ttf", "print": F + "segoepr.ttf", "printb": F + "segoeprb.ttf", "type": F + "cour.ttf", "typeb": F + "courbd.ttf",
         "cam": F + "cambriab.ttf", "camr": F + "cambria.ttc"}
INK = (24, 22, 34)
CRIMSON = (96, 14, 26)
REDINK = (168, 24, 30)
GILT = (206, 164, 86)
PARCH = (226, 212, 176)
KRAFT = (168, 128, 86)


def seed_of(s):
    return zlib.crc32(s.encode()) & 0xFFFF


_fonts = {}


def font(key, size):
    k = (key, max(6, int(size)))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONTS[key], k[1])
    return _fonts[k]


class Packer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.x = self.y = self.row = 0

    def add(self, key, cw, ch, pad=8):
        cw, ch = int(cw), int(ch)
        if self.x + cw + pad > self.w:
            self.x, self.y, self.row = 0, self.y + self.row + pad, 0
        if self.y + ch + pad > self.h:
            raise RuntimeError(f"atlas full at {key}")
        r = (self.x + pad // 2, self.y + pad // 2, cw, ch)
        self.x += cw + pad
        self.row = max(self.row, ch)
        return r


class Atlas:
    def __init__(self, name, bg=(60, 50, 44)):
        self.name = name
        self.col = Image.new("RGB", (A, A), bg)
        self.met = Image.new("L", (A, A), 0)
        self.hgt = Image.new("L", (A, A), 128)
        self.pk = Packer(A, A)
        self.reg = {}

    def put(self, key, cell, scale=1.0):
        c, m, h = cell.done()
        if scale != 1.0:
            sz = (int(cell.w * scale), int(cell.h * scale))
            c, m, h = (im.resize(sz, Image.LANCZOS) for im in (c, m, h))
        w, hh = c.size
        r = self.pk.add(key, w, hh)
        x, y = r[0], r[1]
        self.col.paste(c, (x, y))
        self.met.paste(m, (x, y))
        self.hgt.paste(h, (x, y))
        self.reg[key] = [x / A, 1 - (y + hh) / A, (x + w) / A, 1 - y / A]

    def save(self):
        self.col.save(os.path.join(OUT, f"{self.name}_color.png"))
        self.met.save(os.path.join(OUT, f"{self.name}_gilt.png"))
        self.hgt.save(os.path.join(OUT, f"{self.name}_height.png"))
        print(f"[atlas] {self.name}: {len(self.reg)} regions, filled to y={self.pk.y + self.pk.row} of {A}")


class Cell:
    """One region, drawn at SS x its size: colour, metal mask, height (128 = flat). Coordinates are region pixels."""

    def __init__(self, w, h, bg, grain=6, seed=0, vignette=0.0, fibres=False):
        self.w, self.h = int(w), int(h)
        W, H = self.w * SS, self.h * SS
        g = np.random.default_rng(seed)
        a = np.empty((H, W, 3), np.float32)
        a[:] = bg
        if grain:
            a += g.normal(0, grain * 0.6, (H, W))[..., None]
            m = g.normal(128, 40, (max(2, H // 60), max(2, W // 60)))
            m = np.asarray(Image.fromarray(np.uint8(np.clip(m, 0, 255))).resize((W, H), Image.BICUBIC), np.float32) - 128
            a += (m * 0.011 * grain)[..., None]
        if vignette:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            d = np.maximum(np.abs(xx / W - 0.5), np.abs(yy / H - 0.5)) * 2
            a *= (1 - vignette * np.clip((d - 0.7) / 0.3, 0, 1) ** 2)[..., None]
        self.c = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
        if fibres:
            d = ImageDraw.Draw(self.c)
            for _ in range(int(W * H / 2500)):
                x, y = g.uniform(0, W), g.uniform(0, H)
                ang, L = g.uniform(0, math.pi), g.uniform(3, 10) * SS
                v = int(g.uniform(-14, 10))
                col = tuple(int(np.clip(b + v, 0, 255)) for b in bg)
                d.line((x, y, x + math.cos(ang) * L, y + math.sin(ang) * L), fill=col, width=1)
        self.m = Image.new("L", (W, H), 0)
        self.hh = Image.new("L", (W, H), 128)
        self.dc, self.dm, self.dh = ImageDraw.Draw(self.c), ImageDraw.Draw(self.m), ImageDraw.Draw(self.hh)

    # all coordinates in region px
    def S(self, *v):
        return [x * SS for x in v]

    def mask_text(self, s, fk, size, bold=0):
        f = font(fk, size * SS)
        l, t, r, b = f.getbbox(s)
        pad = int(4 * SS + bold * SS)
        im = Image.new("L", (r - l + 2 * pad, b - t + 2 * pad), 0)
        ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=255)
        if bold:
            im = im.filter(ImageFilter.MaxFilter(2 * int(bold * SS) + 1))
        return im

    def fit(self, s, fk, maxw, maxh, bold=0):
        size = maxh
        while size > 5:
            m = self.mask_text(s, fk, size, bold)
            if m.width <= maxw * SS and m.height <= maxh * SS * 1.25:
                return m
            size *= 0.95
        return self.mask_text(s, fk, 5, bold)

    def stamp(self, m, x, y, colour, metal=0, height=None, angle=0.0, anchor="mm", alpha=1.0):
        """Paste a mask with its anchor at (x, y) region px; gilt (colour GILT) gets a sheen and goes into metal / height."""
        if angle:
            m = m.rotate(angle, expand=True, resample=Image.BICUBIC)
        w, h = m.size
        px = int(x * SS - (w / 2 if anchor[0] == "m" else 0 if anchor[0] == "l" else w))
        py = int(y * SS - (h / 2 if anchor[1] == "m" else 0 if anchor[1] == "t" else h))
        if alpha < 1:
            m = m.point(lambda v: int(v * alpha))
        if colour == GILT:
            rim = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8 * SS)).point(lambda v: int(v * 0.5))
            self.c.paste(Image.new("RGB", m.size, (40, 26, 12)), (px + SS // 2, py + SS // 2), rim)
            t = np.linspace(0, 1, h)[:, None]
            hi, lo = np.array([240, 204, 124], np.float32), np.array([164, 120, 54], np.float32)
            sheen = np.clip(0.55 + 0.45 * np.cos((t - 0.3) * math.pi * 1.4), 0, 1)
            a = np.broadcast_to(lo + (hi - lo) * sheen[..., None], (h, w, 3)).copy()
            a += np.random.default_rng(px * 7 + py).normal(0, 8, (h, w))[..., None]
            self.c.paste(Image.fromarray(np.uint8(np.clip(a, 0, 255))), (px, py), m)
            self.m.paste(Image.new("L", m.size, 235), (px, py), m)
            self.hh.paste(Image.new("L", m.size, 176 if height is None else height), (px, py), m)
            return
        self.c.paste(Image.new("RGB", m.size, colour), (px, py), m)
        if metal:
            self.m.paste(Image.new("L", m.size, metal), (px, py), m)
        if height is not None:
            self.hh.paste(Image.new("L", m.size, height), (px, py), m)

    def text(self, s, fk, x, y, maxw, maxh, colour=INK, bold=0, metal=0, height=None, angle=0.0, anchor="mm", alpha=1.0):
        m = self.fit(s, fk, maxw, maxh, bold)
        self.stamp(m, x, y, colour, metal, height, angle, anchor, alpha)
        return m.width / SS, m.height / SS

    def shape(self, draw, colour, metal=0, height=None):
        """draw(ImageDraw, S) on a mask, then stamp it in colour."""
        m = Image.new("L", self.c.size, 0)
        draw(ImageDraw.Draw(m), SS)
        self.stamp(m, 0, 0, colour, metal, height, anchor="lt")

    def done(self):
        c = self.c.resize((self.w, self.h), Image.LANCZOS)
        m = self.m.resize((self.w, self.h), Image.LANCZOS)
        h = self.hh.filter(ImageFilter.GaussianBlur(0.8 * SS)).resize((self.w, self.h), Image.LANCZOS)
        return c, m, h


def scribble(cell, x, y, w, h, colour, seed, width=2.4):
    """An illegible signature: a run of cursive loops (a trochoid) that rises and falls, a capital's big first loop, an
    underline flourish."""
    g = random.Random(seed)
    pts = []
    n = 220
    loops = g.uniform(7, 10)
    for i in range(n):
        t = i / (n - 1)
        a = t * loops * 2 * math.pi
        amp = h * (0.45 + 0.35 * math.sin(t * 9 + seed)) * (1.6 if t < 0.12 else 1.0)
        r = w * 0.022
        pts.append((x + t * w * 0.85 + r * math.cos(a) * 1.4, y - amp * (0.5 + 0.5 * math.sin(a)) + h * 0.1 * math.sin(t * 3)))
    tail = [(x + w * 0.85, y), (x + w * 0.95, y + h * 0.15), (x + w * 0.55, y + h * 0.32), (x + w * 0.05, y + h * 0.22)]

    def dr(d, s):
        d.line([(px * s, py * s) for px, py in pts], fill=255, width=int(width * s), joint="curve")
        d.line([(px * s, py * s) for px, py in tail], fill=255, width=int(width * 0.8 * s), joint="curve")
    cell.shape(dr, colour)


# ------------------------------------------------------------------ the crest

def crest(cell, cx, cy, s):
    """The school crest as on the doormat and the tapestries: a gilt-rimmed shield quartered crimson and ink under a gilt cross,
    a crescent, a key, a raven's quatrefoil and a candle as the charges; s = its height in px."""
    def P(u, v):
        return ((cx + u * s) * SS, (cy + v * s) * SS)
    sh = [(-0.36, -0.42), (0.36, -0.42), (0.36, 0.02), (0.28, 0.24), (0.14, 0.38), (0, 0.46), (-0.14, 0.38), (-0.28, 0.24), (-0.36, 0.02)]
    big = [(u * 1.12, v * 1.08 + 0.0) for u, v in sh]
    cell.shape(lambda d, k: d.polygon([P(u, v) for u, v in big], fill=255), GILT)
    cell.shape(lambda d, k: d.polygon([P(u, v) for u, v in sh], fill=255), CRIMSON, height=150)
    # ink quarters (top right, bottom left)
    cell.shape(lambda d, k: d.polygon([P(0, -0.42), P(0.36, -0.42), P(0.36, -0.08), P(0, -0.08)], fill=255), (20, 22, 40), height=150)
    cell.shape(lambda d, k: d.polygon([P(0, -0.08), P(-0.36, -0.08), P(-0.36, 0.02), P(-0.28, 0.24), P(-0.14, 0.38), P(0, 0.46)], fill=255),
               (20, 22, 40), height=150)

    def cross(d, k):
        d.rectangle([*P(-0.025, -0.42), *P(0.025, 0.46)], fill=255)
        d.rectangle([*P(-0.36, -0.105), *P(0.36, -0.055)], fill=255)
    cell.shape(cross, GILT)

    def charges(d, k):
        # crescent (top left)
        cxp, cyp = P(-0.18, -0.25)
        r = 0.1 * s * SS
        d.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], fill=255)
        d.ellipse([cxp - r * 0.5, cyp - r * 1.05, cxp + r * 1.4, cyp + r * 0.85], fill=0)
        # key (top right)
        kx, ky = P(0.18, -0.25)
        rr = 0.05 * s * SS
        d.ellipse([kx - rr, ky - rr - 0.06 * s * SS, kx + rr, ky + rr - 0.06 * s * SS], outline=255, width=int(0.022 * s * SS))
        d.rectangle([kx - 0.012 * s * SS, ky - 0.02 * s * SS, kx + 0.012 * s * SS, ky + 0.13 * s * SS], fill=255)
        d.rectangle([kx, ky + 0.07 * s * SS, kx + 0.05 * s * SS, ky + 0.095 * s * SS], fill=255)
        d.rectangle([kx, ky + 0.11 * s * SS, kx + 0.04 * s * SS, ky + 0.13 * s * SS], fill=255)
        # quatrefoil (bottom left)
        qx, qy = P(-0.16, 0.12)
        q = 0.045 * s * SS
        for ox, oy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            d.ellipse([qx + ox * q - q, qy + oy * q - q, qx + ox * q + q, qy + oy * q + q], fill=255)
        # candle (bottom right)
        bx, by = P(0.16, 0.14)
        d.rectangle([bx - 0.025 * s * SS, by - 0.05 * s * SS, bx + 0.025 * s * SS, by + 0.12 * s * SS], fill=255)
        d.ellipse([bx - 0.02 * s * SS, by - 0.12 * s * SS, bx + 0.02 * s * SS, by - 0.06 * s * SS], fill=255)
    cell.shape(charges, GILT)


def fleuron(cell, cx, cy, r, colour=GILT, angle=0):
    def dr(d, k):
        for i in range(4):
            a = angle + i * math.pi / 2
            x, y = (cx + math.cos(a) * r * 0.55) * k, (cy + math.sin(a) * r * 0.55) * k
            q = r * 0.42 * k
            d.ellipse([x - q, y - q, x + q, y + q], fill=255)
        q = r * 0.3 * k
        d.ellipse([cx * k - q, cy * k - q, cx * k + q, cy * k + q], fill=0)
    cell.shape(dr, colour)


def rules(cell, inset, colour, width, metal_gilt=True):
    def dr(d, k):
        d.rectangle([inset * k, inset * k, (cell.w - inset) * k, (cell.h - inset) * k], outline=255, width=int(width * k))
    cell.shape(dr, colour)


# ------------------------------------------------------------------ certificates

CERTS = {
    "Cert_Honour": ("The Honour Roll", ["is entered upon the Honour Roll of the school", "for marks of the first rank in every subject",
                                        "this term"]),
    "Cert_Deans": ("The Dean's List", ["is named to the Dean's List", "for distinguished scholarship, diligence and good conduct",
                                       "this term"]),
    "Cert_Attend": ("Perfect Attendance", ["was present at every bell, every lesson, every day", "without one mark against the register",
                                           "this term"]),
}


def certificate(key, title, lines):
    W, H = 1500, 1100
    c = Cell(W, H, PARCH, grain=7, seed=seed_of(key), vignette=0.22, fibres=True)
    g = random.Random(seed_of(key))
    # foxing: a few faint brown spots
    def fox(d, k):
        for _ in range(14):
            x, y, r = g.uniform(60, W - 60), g.uniform(60, H - 60), g.uniform(3, 11)
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=255)
    c.shape(fox, (204, 180, 136))
    rules(c, 26, GILT, 9)
    rules(c, 46, CRIMSON, 3)
    rules(c, 56, GILT, 2)
    for x, y in ((46, 46), (W - 46, 46), (46, H - 46), (W - 46, H - 46)):
        fleuron(c, x, y, 26)
    crest(c, W / 2, 190, 210)
    c.text("NIGHTMARE  HIGH", "pala", W / 2, 330, 700, 50, colour=CRIMSON)
    c.text("per noctem ad lucem", "palai", W / 2, 378, 500, 34, colour=INK)
    c.text("Certificate of Merit", "black", W / 2, 470, 1180, 110, colour=INK, bold=1.6)
    c.text(title, "palabi", W / 2, 588, 900, 74, colour=CRIMSON)
    c.text("This is to certify that", "palai", W / 2, 668, 600, 40, colour=INK)
    c.shape(lambda d, k: d.line([(W * 0.26 * k, 742 * k), (W * 0.74 * k, 742 * k)], fill=255, width=int(2.5 * k)), INK)
    for i, ln in enumerate(lines):
        c.text(ln, "palar", W / 2, 792 + i * 46, 1100, 36, colour=INK)
    for sx, label, seed in ((-1, "Headmaster", 11), (1, "Dean of Studies", 12)):
        x = W / 2 + sx * 430
        scribble(c, x - 150, 975, 300, 48, (30, 34, 70), seed_of(key) + seed)
        c.shape(lambda d, k, x=x: d.line([((x - 175) * k, 1000 * k), ((x + 175) * k, 1000 * k)], fill=255, width=int(2 * k)), INK)
        c.text(label, "palai", x, 1030, 300, 30, colour=INK)
    return c


# ------------------------------------------------------------------ notices, papers, the marked test

def lined(c, x0, x1, y0, y1, step, colour=(150, 160, 190), margin=None):
    def dr(d, k):
        y = y0
        while y < y1:
            d.line([(x0 * k, y * k), (x1 * k, y * k)], fill=255, width=int(1.4 * k))
            y += step
        if margin:
            d.line([(margin * k, 0), (margin * k, c.h * k)], fill=0, width=1)
    c.shape(dr, colour)
    if margin:
        c.shape(lambda d, k: d.line([(margin * k, 0), (margin * k, c.h * k)], fill=255, width=int(1.6 * k)), (200, 110, 110))


def handwriting(c, lines, x, y0, step, size, colour=(28, 34, 78), fk="hand", maxw=None, angle=0.0):
    for i, ln in enumerate(lines):
        if not ln:
            continue
        c.text(ln, fk, x, y0 + i * step, maxw or c.w - x - 40, size, colour=colour, anchor="lm", angle=angle)


def notice_overdue():
    W, H = 700, 920
    c = Cell(W, H, (230, 224, 204), grain=5, seed=101, fibres=True)
    c.text("SCHOOL LIBRARY", "pala", W / 2, 70, 560, 50, colour=INK)
    c.shape(lambda d, k: d.line([(60 * k, 110 * k), ((W - 60) * k, 110 * k)], fill=255, width=int(3 * k)), INK)
    c.text("The following books are now overdue:", "palai", W / 2, 160, 600, 34)
    for i, t in enumerate(("Moonlight Botany", "The Raven's Almanac", "A History of the Institution", "Candles & Wax")):
        c.text(f"{i + 1}.  {t}", "palar", 90, 230 + i * 56, 560, 38, anchor="lm")
    c.text("Return them to the Circulation Desk at once.", "palai", W / 2, 500, 600, 32)
    c.text("A fine is charged for every day they are late.", "palai", W / 2, 545, 600, 30)
    c.text("by order of the Librarian", "palai", W / 2, 850, 400, 30)
    # the stamp, rubber red, a little patchy
    m = c.fit("OVERDUE", "pala", 600, 150, bold=1)
    box = Image.new("L", (m.width + 60 * SS, m.height + 50 * SS), 0)
    ImageDraw.Draw(box).rectangle([6 * SS, 6 * SS, box.width - 6 * SS, box.height - 6 * SS], outline=255, width=9 * SS)
    box.paste(m, (30 * SS, 25 * SS), m)
    patch = np.asarray(Image.fromarray(np.uint8(np.random.default_rng(5).uniform(0, 255, (box.height // 6 + 1, box.width // 6 + 1)))).resize(box.size, Image.BICUBIC))
    box = Image.fromarray(np.uint8(np.asarray(box) * np.clip(patch / 255 * 1.6, 0.45, 1.0)))
    c.stamp(box, W / 2, 700, (178, 26, 32), angle=-9)
    return c


def notice_final():
    W, H = 680, 900
    c = Cell(W, H, (236, 230, 212), grain=5, seed=102, fibres=True)
    def border(d, k):
        d.rectangle([18 * k, 18 * k, (W - 18) * k, (H - 18) * k], outline=255, width=int(14 * k))
    c.shape(border, (150, 20, 28))
    c.text("FINAL NOTICE", "pala", W / 2, 110, 580, 92, colour=(150, 20, 28))
    c.text("THE OFFICE", "pala", W / 2, 190, 300, 34, colour=INK)
    lines = ["Homework still not handed in:", "", "Alchemy - the copper essay", "History - chapter nine questions",
             "Astronomy - the star chart", "", "Hand it all in by Friday,", "or you will be kept in on Saturday."]
    for i, ln in enumerate(lines):
        if ln:
            c.text(ln, "palar" if i not in (0, 6, 7) else "palai", W / 2, 280 + i * 52, 580, 36)
    c.text("This is the last reminder.", "pala", W / 2, 760, 560, 40, colour=(150, 20, 28))
    return c


def marked_test():
    W, H = 700, 920
    c = Cell(W, H, (238, 234, 222), grain=4, seed=103, fibres=True)
    lined(c, 30, W - 30, 200, H - 40, 38, margin=90)
    c.text("Mid-term Test: History of the Institution", "pala", W / 2, 60, 620, 36)
    c.text("Name ______________   Form ____", "palar", 60, 120, 380, 28, anchor="lm")
    ans = ["1. The school was founded in", "   the year of the long winter", "2. The bell tower was built by", "   ... I forget",
           "3. Name the four houses", "   Ravens, Wardens, Vigil,", "   and the other one", "4. Why is the east wing shut?",
           "   nobody knows", "5. (no answer)"]
    for i, a in enumerate(ans):
        c.text(a, "hand", 110, 222 + i * 38, 520, 30, anchor="lm", colour=(30, 36, 80))
    # the teacher's red pen: crosses, the grade circled, SEE ME
    for i in (1, 3, 6, 8, 9):
        y = 222 + i * 38
        c.text("x", "hand", 640, y, 40, 40, colour=REDINK, anchor="mm")
    c.text("D-", "scriptb", 590, 150, 120, 100, colour=REDINK)
    c.shape(lambda d, k: d.ellipse([515 * k, 95 * k, 665 * k, 208 * k], outline=255, width=int(5 * k)), REDINK)
    c.text("SEE ME.", "scriptb", W / 2, 700, 520, 96, colour=REDINK, angle=4)
    c.text("- Mr. Hale", "script", W / 2 + 120, 800, 300, 56, colour=REDINK, angle=4)
    return c


def notice_detention():
    W, H = 640, 820
    c = Cell(W, H, (214, 224, 232), grain=5, seed=104, fibres=True)
    c.text("DETENTION SLIP", "pala", W / 2, 80, 560, 70, colour=INK)
    c.shape(lambda d, k: d.line([(50 * k, 130 * k), ((W - 50) * k, 130 * k)], fill=255, width=int(3 * k)), INK)
    rows = [("Name:", "______________"), ("Reason:", "late to class again"), ("", "(the fourth time)"), ("When:", "Thursday, after the bell"),
            ("Where:", "the old classroom, east wing"), ("Bring:", "a pen, and your manners")]
    for i, (a, b) in enumerate(rows):
        y = 200 + i * 70
        if a:
            c.text(a, "pala", 60, y, 160, 34, anchor="lm")
        c.text(b, "hand", 220, y, 380, 38, anchor="lm", colour=(30, 36, 80))
    scribble(c, 330, 690, 220, 40, (30, 36, 80), 41)
    c.text("signed", "palai", 260, 715, 100, 28)
    return c


def notice_warning():
    W, H = 660, 860
    c = Cell(W, H, (232, 222, 196), grain=5, seed=105, fibres=True)
    crest(c, W / 2, 110, 140)
    c.text("PROGRESS WARNING", "pala", W / 2, 235, 580, 56, colour=CRIMSON)
    lines = ["Your marks this term have fallen", "below the standard of the school.", "", "Your parents have been written to.",
             "", "Extra study in the library is advised,", "every evening until the next report."]
    for i, ln in enumerate(lines):
        if ln:
            c.text(ln, "palar", W / 2, 320 + i * 48, 580, 34)
    c.text("The Office", "palai", W / 2, 760, 300, 36)
    return c


def notice_seeme():
    W, H = 520, 380
    c = Cell(W, H, (240, 228, 150), grain=4, seed=106)    # a yellow note card
    c.text("SEE ME.", "scriptb", W / 2, 150, 440, 120, colour=REDINK, angle=3)
    c.text("- Mr. Hale", "script", W / 2 + 60, 280, 300, 66, colour=REDINK, angle=3)
    return c


def paper_notes():
    W, H = 700, 920
    c = Cell(W, H, (238, 236, 226), grain=4, seed=107, fibres=True)
    lined(c, 30, W - 30, 120, H - 40, 40, margin=90)
    c.text("Astronomy  -  ch. 4", "hand", 110, 70, 400, 44, anchor="lm", colour=(30, 36, 80))
    lines = ["the moon has eight phases", "new, crescent, quarter, gibbous...", "full moon = no lessons on the roof??",
             "", "the tower telescope - ask about it", "stars are older than the school", "(only just, says Mr. Hale)", "",
             "learn the constellations", "by Monday!!", "", "the Raven, the Key, the Lantern"]
    handwriting(c, lines, 110, 142, 40, 30)

    def doodle(d, k):
        cx, cy, r = 560 * k, 760 * k, 60 * k
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=int(3 * k))
        d.arc([cx - r * 0.6, cy - r, cx + r * 1.4, cy + r], 100, 260, fill=255, width=int(3 * k))
    c.shape(doodle, (30, 36, 80))
    return c


def paper_sums():
    W, H = 700, 920
    c = Cell(W, H, (236, 236, 232), grain=4, seed=108, fibres=True)

    def grid(d, k):
        for x in range(30, W, 34):
            d.line([(x * k, 0), (x * k, H * k)], fill=255, width=int(1 * k))
        for y in range(30, H, 34):
            d.line([(0, y * k), (W * k, y * k)], fill=255, width=int(1 * k))
    c.shape(grid, (170, 190, 205))
    c.text("Arithmetic - exercise 12", "hand", 60, 60, 500, 40, anchor="lm", colour=(30, 36, 80))
    sums = ["13 x 13 = 169", "144 / 12 = 12", "7 x 8 = 54", "  no, 56", "the clock strikes 12 at midnight",
            "how many times by dawn?", "  ... too many", "", "x + 3 = 9   so x = 6", "2x = 18   x = 9"]
    handwriting(c, sums, 70, 140, 52, 34)
    c.text("7/10", "scriptb", 560, 820, 180, 80, colour=REDINK, angle=-6)
    return c


def paper_essay():
    W, H = 700, 920
    c = Cell(W, H, (240, 236, 222), grain=4, seed=109, fibres=True)
    c.text("The Founding of the Institution", "typeb", W / 2, 70, 620, 34)
    c.text("an essay, 500 words", "type", W / 2, 110, 400, 26)
    body = ["Long ago, before the town had", "a name, a lantern was lit on the", "hill and never put out. Around",
            "it they built the first hall, and", "then the tower, and then the", "rest, one wing at a time. The",
            "founders wrote that the school", "should teach by night as well as", "by day, so that no student would", "ever be afraid of the dark.",
            "", "(to be continued)"]
    for i, ln in enumerate(body):
        if ln:
            c.text(ln, "type", 60, 170 + i * 50, 580, 30, anchor="lm")
    c.text("too short!", "script", 520, 800, 240, 50, colour=REDINK, angle=-8)
    c.shape(lambda d, k: d.line([(60 * k, 845 * k), (300 * k, 830 * k)], fill=255, width=int(3 * k)), REDINK)
    return c


def paper_doodle():
    W, H = 700, 920
    c = Cell(W, H, (236, 234, 222), grain=4, seed=110, fibres=True)
    lined(c, 30, W - 30, 120, H - 40, 40, margin=90)
    c.text("History - notes", "hand", 110, 70, 400, 40, anchor="lm", colour=(30, 36, 80))
    handwriting(c, ["the old wing was shut in...", "", "so boring", "so boring", "so boring"], 110, 142, 40, 30)

    def bats(d, k):
        g = random.Random(4)
        for _ in range(7):
            x, y, s = g.uniform(180, 580), g.uniform(420, 840), g.uniform(55, 95)
            pts = [(x - s, y), (x - s * 0.6, y - s * 0.35), (x - s * 0.3, y - s * 0.05), (x, y - s * 0.3), (x + s * 0.3, y - s * 0.05),
                   (x + s * 0.6, y - s * 0.35), (x + s, y), (x + s * 0.5, y + s * 0.1), (x, y + s * 0.25), (x - s * 0.5, y + s * 0.1)]
            d.line([(px * k, py * k) for px, py in pts + pts[:1]], fill=255, width=int(3 * k), joint="curve")
        cx, cy, r = 540 * k, 270 * k, 70 * k
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=int(3 * k))
    c.shape(bats, (30, 36, 80))
    return c


# ------------------------------------------------------------------ pizza box, cans, mug

def pizza_lid():
    W = H = 1000
    c = Cell(W, H, KRAFT, grain=9, seed=120, fibres=True)
    ink = (40, 18, 18)
    red = (150, 26, 30)

    def ring(d, k):
        d.ellipse([170 * k, 120 * k, 830 * k, 780 * k], outline=255, width=int(16 * k))
        d.ellipse([200 * k, 150 * k, 800 * k, 750 * k], outline=255, width=int(4 * k))
    c.shape(ring, red, height=110)

    def moon(d, k):
        cx, cy, r = 500 * k, 360 * k, 130 * k
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        d.ellipse([cx - r * 0.35, cy - r * 1.15, cx + r * 1.5, cy + r * 0.9], fill=0)
        # a slice of pizza tucked in the crescent's arms
        d.polygon([(cx + r * 0.05, cy - r * 0.25), (cx + r * 0.75, cy + r * 0.05), (cx + r * 0.1, cy + r * 0.6)], fill=255)
    c.shape(moon, ink, height=110)
    for x, y in ((560, 340), (530, 400), (590, 395)):
        c.shape(lambda d, k, x=x, y=y: d.ellipse([(x - 11) * k, (y - 11) * k, (x + 11) * k, (y + 11) * k], fill=255), KRAFT)
    c.text("MIDNIGHT", "pala", 500, 560, 560, 110, colour=red, height=110)
    c.text("PIZZA  CO.", "pala", 500, 655, 420, 64, colour=ink, height=110)
    c.text("hot to your door, long after dark", "palai", 500, 860, 760, 40, colour=ink, height=110)
    c.text("Old Town  -  open till the bell tolls three", "palar", 500, 920, 760, 30, colour=ink, height=110)
    return c


def pizza_side():
    W, H = 1600, 110
    c = Cell(W, H, KRAFT, grain=9, seed=121, fibres=True)
    for i in range(3):
        c.text("MIDNIGHT PIZZA CO.   HOT & FRESH", "pala", 270 + i * 530, H / 2, 500, 44, colour=(150, 26, 30), height=110)
    return c


def can_wrap(key, bg, fg, accent, name, sub, logo):
    W, H = 1100, 420
    c = Cell(W, H, bg, grain=2, seed=seed_of(key))

    def bands(d, k):
        d.rectangle([0, 0, W * k, 34 * k], fill=255)
        d.rectangle([0, (H - 34) * k, W * k, H * k], fill=255)
    c.shape(bands, (200, 200, 206), metal=230)                  # bare aluminium at the necks
    c.shape(lambda d, k: d.rectangle([0, 52 * k, W * k, 64 * k], fill=255), accent)
    c.shape(lambda d, k: d.rectangle([0, (H - 64) * k, W * k, (H - 52) * k], fill=255), accent)
    for x0 in (0, W / 2):
        c.text(name, "pala", x0 + W / 4, 190, W / 2 - 60, 110, colour=fg, bold=0.5)
        c.text(sub, "palai", x0 + W / 4, 290, W / 2 - 80, 40, colour=fg)
        logo(c, x0 + W / 4, 105, fg)
    return c


def logo_moon(c, x, y, col):
    def dr(d, k):
        r = 36 * k
        d.ellipse([x * k - r, y * k - r, x * k + r, y * k + r], fill=255)
        d.ellipse([x * k - r * 0.3, y * k - r * 1.1, x * k + r * 1.5, y * k + r * 0.9], fill=0)
    c.shape(dr, col)


def logo_bat(c, x, y, col):
    def dr(d, k):
        s = 60
        pts = [(-1, 0), (-0.62, -0.4), (-0.42, -0.1), (-0.18, -0.24), (-0.08, -0.5), (0, -0.3), (0.08, -0.5), (0.18, -0.24),
               (0.42, -0.1), (0.62, -0.4), (1, 0), (0.6, 0.12), (0.3, 0.05), (0, 0.4), (-0.3, 0.05), (-0.6, 0.12)]
        d.polygon([((x + u * s) * k, (y + v * s * 0.9) * k) for u, v in pts], fill=255)
    c.shape(dr, col)


def logo_star(c, x, y, col):
    def dr(d, k):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 40 if i % 2 == 0 else 17
            pts.append(((x + math.cos(a) * r) * k, (y + math.sin(a) * r) * k))
        d.polygon(pts, fill=255)
    c.shape(dr, col)


def mug_wrap():
    W, H = 1100, 380
    c = Cell(W, H, (100, 16, 28), grain=3, seed=130)
    for x in (W * 0.25, W * 0.75):
        crest(c, x, 170, 200)
    c.text("NIGHTMARE HIGH", "pala", W * 0.25, 320, 400, 36, colour=GILT)
    c.text("NIGHTMARE HIGH", "pala", W * 0.75, 320, 400, 36, colour=GILT)
    return c


def night_sky():
    W, H = 900, 1400
    c = Cell(W, H, (10, 12, 28), grain=0, seed=140)
    a = np.asarray(c.c, np.float32)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32) / SS
    t = yy / H
    top, low = np.array([6, 7, 18], np.float32), np.array([34, 30, 62], np.float32)
    a = top + (low - top) * (t ** 1.6)[..., None]
    mx, my, mr = W * 0.66, H * 0.28, 70
    d = np.hypot(xx - mx, yy - my)
    a += (np.array([60, 62, 90]) * np.exp(-((d - mr) / 260).clip(0) ** 1.2) * (d > mr))[..., None] if False else 0
    halo = np.exp(-np.clip(d - mr, 0, None) / 160) * (d > mr)
    a += np.array([70, 70, 96], np.float32) * halo[..., None] * 0.6
    g = np.random.default_rng(141)
    for _ in range(420):
        sx, sy = g.uniform(0, W), g.uniform(0, H * 0.75)
        b = g.uniform(90, 255) * (1 - sy / H)
        r = g.choice([0.8, 1.0, 1.4, 2.0], p=[0.5, 0.3, 0.15, 0.05])
        x0, x1 = int(max(0, (sx - 6) * SS)), int(min(a.shape[1], (sx + 6) * SS))
        y0, y1 = int(max(0, (sy - 6) * SS)), int(min(a.shape[0], (sy + 6) * SS))
        m = np.exp(-(((xx[y0:y1, x0:x1] - sx) ** 2 + (yy[y0:y1, x0:x1] - sy) ** 2) / (r * r)))
        a[y0:y1, x0:x1] += (b * m)[..., None] * np.array([0.9, 0.92, 1.0])
    # the moon: pale, a few seas
    md = d <= mr
    sea = np.asarray(Image.fromarray(np.uint8(g.uniform(0, 255, (24, 24)))).resize((a.shape[1], a.shape[0]), Image.BICUBIC), np.float32) / 255
    moon = np.array([226, 222, 200], np.float32) * (0.86 + 0.14 * sea)[..., None]
    a[md] = moon[md]
    c.c = Image.fromarray(np.uint8(np.clip(a, 0, 255)))
    c.dc = ImageDraw.Draw(c.c)

    # the grounds: the school's roofline and spires, trees, a lit window or two
    def skyline(d, k):
        g2 = random.Random(142)
        base = H * 0.8
        pts = [(0, H * k)]
        x = 0
        while x < W:
            w = g2.uniform(40, 120)
            hgt = g2.uniform(30, 110)
            pts += [(x * k, (base - hgt) * k), ((x + w) * k, (base - hgt) * k)]
            if g2.random() < 0.35:
                sx = x + w / 2
                pts.insert(-1, (sx * k - 12 * k, (base - hgt) * k))
                pts.insert(-1, (sx * k, (base - hgt - g2.uniform(90, 220)) * k))
                pts.insert(-1, (sx * k + 12 * k, (base - hgt) * k))
            x += w
        pts += [(W * k, H * k)]
        d.polygon(pts, fill=255)
        for _ in range(9):
            tx, tr = g2.uniform(0, W), g2.uniform(40, 90)
            ty = H * 0.86
            d.ellipse([(tx - tr) * k, (ty - tr * 1.3) * k, (tx + tr) * k, (ty + tr) * k], fill=255)
        d.rectangle([0, H * 0.88 * k, W * k, H * k], fill=255)
    c.shape(skyline, (6, 6, 12))
    g3 = random.Random(143)
    for _ in range(6):
        x, y = g3.uniform(60, W - 60), g3.uniform(H * 0.74, H * 0.79)
        c.shape(lambda d, k, x=x, y=y: d.rectangle([x * k, y * k, (x + 9) * k, (y + 14) * k], fill=255), (210, 150, 70))
    return c


def swatch(colour, grain=5, seed=0, metal=0):
    c = Cell(48, 48, colour, grain=grain, seed=seed)
    if metal:
        c.m = Image.new("L", c.c.size, metal)
    return c


# ------------------------------------------------------------------ garments (flat patterns, studs)

# each garment: outline polygon (x, y) in studs, flat, y along the body; the pattern is drawn over its bounding box
GARMENTS = {
    # a school blazer laid open across the shoulders: the front below y = 0, the back above, the sleeves across the shoulder line
    "Jacket": [(-1.0, -2.1), (1.0, -2.1), (1.0, -0.36), (2.15, -0.36), (2.15, 0.36), (1.0, 0.36), (1.0, 2.1), (-1.0, 2.1), (-1.0, 0.36),
               (-2.15, 0.36), (-2.15, -0.36), (-1.0, -0.36)],
    "Shirt": [(-0.85, -1.9), (0.85, -1.9), (0.85, -0.3), (1.85, -0.3), (1.85, 0.3), (0.85, 0.3), (0.85, 1.9), (-0.85, 1.9), (-0.85, 0.3),
              (-1.85, 0.3), (-1.85, -0.3), (-0.85, -0.3)],
    "Sweater": [(-0.9, -1.8), (0.9, -1.8), (0.9, -0.34), (1.95, -0.34), (1.95, 0.34), (0.9, 0.34), (0.9, 1.8), (-0.9, 1.8), (-0.9, 0.34),
                (-1.95, 0.34), (-1.95, -0.34), (-0.9, -0.34)],
    "Tee": [(-0.8, -1.5), (0.8, -1.5), (0.8, -0.3), (1.25, -0.3), (1.25, 0.3), (0.8, 0.3), (0.8, 1.5), (-0.8, 1.5), (-0.8, 0.3),
            (-1.25, 0.3), (-1.25, -0.3), (-0.8, -0.3)],
    # trousers flat, the legs apart a little
    "Trousers": [(-0.8, 1.5), (0.8, 1.5), (0.82, -1.7), (0.1, -1.7), (0.0, 0.6), (-0.1, -1.7), (-0.82, -1.7)],
    "Scarf": [(-0.26, -2.0), (0.26, -2.0), (0.26, 2.0), (-0.26, 2.0)],
    "Tie": [(-0.06, 1.25), (0.06, 1.25), (0.08, 0.6), (0.16, -1.1), (0.0, -1.3), (-0.16, -1.1), (-0.08, 0.6)],
}
PPS_CLOTH = 420     # pattern px per stud


def gbox(name):
    pts = GARMENTS[name]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def garment_cell(name, bg, grain=10, seed=0):
    x0, y0, x1, y1 = gbox(name)
    W, H = int((x1 - x0) * PPS_CLOTH), int((y1 - y0) * PPS_CLOTH)
    c = Cell(W, H, bg, grain=grain, seed=seed, fibres=True)

    def P(x, y):            # studs -> region px (image y down = the garment's +y up)
        return ((x - x0) * PPS_CLOTH, (y1 - y) * PPS_CLOTH)
    return c, P


def outline_band(c, P, name, colour, width):
    pts = GARMENTS[name]
    c.shape(lambda d, k: d.line([(P(*p)[0] * k, P(*p)[1] * k) for p in pts + pts[:1]], fill=255, width=int(width * k), joint="curve"), colour)


def dot(c, P, x, y, r, colour, metal=0, height=170):
    px, py = P(x, y)
    rr = r * PPS_CLOTH
    c.shape(lambda d, k: d.ellipse([(px - rr) * k, (py - rr) * k, (px + rr) * k, (py + rr) * k], fill=255), colour, metal, height)


def line(c, P, pts, colour, width, height=100):
    c.shape(lambda d, k: d.line([(P(*p)[0] * k, P(*p)[1] * k) for p in pts], fill=255, width=int(width * k), joint="curve"), colour, 0, height)


def jacket():
    c, P = garment_cell("Jacket", (26, 26, 36), grain=8, seed=201)
    outline_band(c, P, "Jacket", CRIMSON, 18)
    # the front: the opening, lapels, three brass buttons, two pocket flaps, the crest patch on the left breast
    line(c, P, [(0, -2.1), (0, -0.9)], (12, 12, 18), 4)
    line(c, P, [(-0.34, 0.0), (-0.1, -0.85), (0, -0.9)], CRIMSON, 9)
    line(c, P, [(0.34, 0.0), (0.1, -0.85), (0, -0.9)], CRIMSON, 9)
    line(c, P, [(-0.34, 0.0), (-0.55, -0.5), (-0.12, -0.85)], (14, 14, 20), 5)
    line(c, P, [(0.34, 0.0), (0.55, -0.5), (0.12, -0.85)], (14, 14, 20), 5)
    for y in (-1.05, -1.4, -1.75):
        dot(c, P, 0.1, y, 0.055, GILT)
    for sx in (-1, 1):
        line(c, P, [(sx * 0.3, -1.6), (sx * 0.85, -1.6)], (12, 12, 18), 6)
        line(c, P, [(sx * 0.3, -1.6), (sx * 0.3, -1.72), (sx * 0.85, -1.72), (sx * 0.85, -1.6)], CRIMSON, 3)
        # cuffs: two crimson rings and a brass button near each sleeve end
        for xx in (2.0, 1.9):
            line(c, P, [(sx * xx, -0.36), (sx * xx, 0.36)], CRIMSON, 5)
        dot(c, P, sx * 2.05, -0.2, 0.035, GILT)
    px, py = P(-0.6, -0.55)
    crest(c, px, py, 0.5 * PPS_CLOTH)
    # the back: the centre seam, the collar band across the shoulders
    line(c, P, [(0, 2.1), (0, 0.3)], (12, 12, 18), 4)
    line(c, P, [(-0.34, 0.0), (0.34, 0.0)], (14, 14, 20), 28)
    line(c, P, [(-0.34, 0.06), (0.34, 0.06)], CRIMSON, 4)
    return c


def shirt():
    c, P = garment_cell("Shirt", (222, 216, 200), grain=5, seed=202)
    x0, y0, x1, y1 = gbox("Shirt")

    def stripes(d, k):
        x = 0
        while x < c.w:
            d.line([(x * k, 0), (x * k, c.h * k)], fill=255, width=int(2 * k))
            x += 22
    c.shape(stripes, (168, 176, 200))
    outline_band(c, P, "Shirt", (196, 190, 176), 6)
    line(c, P, [(0.05, -1.9), (0.05, -0.15)], (200, 194, 180), 14)
    for y in (-0.4, -0.75, -1.1, -1.45, -1.8):
        dot(c, P, 0.05, y, 0.03, (236, 232, 222), height=160)
    line(c, P, [(-0.3, 0.0), (0.0, -0.2), (0.3, 0.0)], (190, 184, 170), 10)
    line(c, P, [(-0.6, -0.55), (-0.25, -0.55), (-0.25, -0.9), (-0.6, -0.9), (-0.6, -0.55)], (190, 184, 170), 3)
    for sx in (-1, 1):
        line(c, P, [(sx * 1.6, -0.3), (sx * 1.6, 0.3)], (196, 190, 176), 6)
    return c


def sweater():
    c, P = garment_cell("Sweater", (104, 18, 30), grain=6, seed=203)

    def ribs(d, k):                       # the knit: little chevrons in columns
        for x in range(0, c.w, 10):
            for y in range(0, c.h, 12):
                d.line([(x * k, y * k), ((x + 5) * k, (y + 6) * k), ((x + 10) * k, y * k)], fill=255, width=int(1.2 * k))
    c.shape(ribs, (80, 12, 22), height=104)
    for yy in (-1.6, -1.68):
        line(c, P, [(-0.9, yy), (0.9, yy)], (212, 196, 160), 10)
    for yy in (1.6, 1.68):
        line(c, P, [(-0.9, yy), (0.9, yy)], (212, 196, 160), 10)
    for sx in (-1, 1):
        line(c, P, [(sx * 1.78, -0.34), (sx * 1.78, 0.34)], (212, 196, 160), 10)
    line(c, P, [(-0.32, 0.0), (0.0, -0.3), (0.32, 0.0)], (212, 196, 160), 12)
    outline_band(c, P, "Sweater", (70, 10, 20), 10)
    return c


def tee():
    c, P = garment_cell("Tee", (34, 36, 48), grain=7, seed=204)
    outline_band(c, P, "Tee", (24, 24, 34), 6)
    px, py = P(0, -0.75)
    logo_moon(c, px - 40, py - 30, (210, 196, 160))
    logo_bat(c, px + 40, py + 20, (210, 196, 160))
    c.text("NH", "pala", px, py + 110, 200, 70, colour=(210, 196, 160))
    return c


def trousers():
    c, P = garment_cell("Trousers", (52, 52, 58), grain=8, seed=205)

    def herring(d, k):
        for y in range(0, c.h, 8):
            d.line([(0, y * k), (c.w * k, (y + 4) * k)], fill=255, width=int(1 * k))
    c.shape(herring, (44, 44, 50))
    outline_band(c, P, "Trousers", (36, 36, 40), 6)
    line(c, P, [(-0.8, 1.38), (0.8, 1.38)], (30, 30, 34), 8)
    for sx in (-1, 1):
        line(c, P, [(sx * 0.45, 1.3), (sx * 0.46, -1.7)], (66, 66, 74), 3)     # pressed creases
    dot(c, P, 0.0, 1.45, 0.04, (30, 30, 34))
    return c


def scarf():
    c, P = garment_cell("Scarf", CRIMSON, grain=8, seed=206)
    for i, yy in enumerate([y / 10 for y in range(-18, 19, 3)]):
        col = (22, 24, 44) if i % 2 == 0 else (206, 176, 104)
        line(c, P, [(-0.26, yy), (0.26, yy)], col, 22 if i % 2 == 0 else 8)

    def fringe(d, k):
        for x in range(0, c.w, 9):
            d.line([(x * k, 0), (x * k, 30 * k)], fill=255, width=int(3 * k))
            d.line([(x * k, (c.h - 30) * k), (x * k, c.h * k)], fill=255, width=int(3 * k))
    c.shape(fringe, (130, 30, 40))
    return c


def tie():
    c, P = garment_cell("Tie", CRIMSON, grain=5, seed=207)

    def stripes(d, k):
        for t in range(-60, c.w + c.h, 34):
            d.line([(t * k, 0), ((t - c.h) * k, c.h * k)], fill=255, width=int(7 * k))
    c.shape(stripes, (196, 156, 80))
    return c


# ------------------------------------------------------------------ main

if __name__ == "__main__":
    pr = Atlas("DormPrint")
    for k, (t, ls) in CERTS.items():
        pr.put(k, certificate(k, t, ls), 0.86)
    pr.put("Sky", night_sky(), 0.8)
    pr.put("Pizza_Lid", pizza_lid())
    for k, fn in (("Notice_Overdue", notice_overdue), ("Notice_Final", notice_final), ("Paper_Test", marked_test),
                  ("Notice_Detention", notice_detention), ("Notice_Warning", notice_warning), ("Paper_Notes", paper_notes),
                  ("Paper_Sums", paper_sums), ("Paper_Essay", paper_essay), ("Paper_Doodle", paper_doodle), ("Notice_SeeMe", notice_seeme)):
        pr.put(k, fn(), 0.82)
    pr.put("Can_Cola", can_wrap("Can_Cola", (120, 16, 26), (236, 224, 196), (206, 164, 86), "NOCTURNE", "cola  -  for late nights", logo_moon))
    pr.put("Can_Fizz", can_wrap("Can_Fizz", (24, 30, 64), (220, 214, 190), (110, 40, 70), "BATFIZZ", "elderberry & lime", logo_bat))
    pr.put("Can_Moon", can_wrap("Can_Moon", (214, 200, 164), (60, 20, 40), (96, 14, 26), "MOON SODA", "cream soda", logo_star))
    pr.put("Mug_Wrap", mug_wrap())
    pr.put("Pizza_Side", pizza_side())
    for name, col, g, m in (("paper", (232, 226, 206), 4, 0), ("kraft", KRAFT, 9, 0), ("kraftlt", (190, 154, 110), 8, 0), ("parch", PARCH, 6, 0),
                            ("gilt", GILT, 4, 235), ("alu", (196, 198, 204), 3, 235), ("crimson", CRIMSON, 4, 0), ("ink", INK, 3, 0),
                            ("cola", (120, 16, 26), 2, 0), ("fizz", (24, 30, 64), 2, 0), ("moon", (214, 200, 164), 2, 0), ("note", (240, 228, 150), 4, 0),
                            ("cork", (128, 88, 52), 10, 0), ("slip", (214, 224, 232), 4, 0)):
        pr.put(f"Swatch_{name}", swatch(col, g, seed_of(name), m))
    pr.save()

    cl = Atlas("DormCloth", bg=(40, 36, 40))
    for k, fn in (("Jacket", jacket), ("Shirt", shirt), ("Sweater", sweater), ("Tee", tee), ("Trousers", trousers), ("Scarf", scarf), ("Tie", tie)):
        cl.put(k, fn())
    cl.save()
    json.dump({"print": pr.reg, "cloth": cl.reg, "garments": GARMENTS}, open(os.path.join(HERE, "dorm_atlas.json"), "w"), indent=0)
