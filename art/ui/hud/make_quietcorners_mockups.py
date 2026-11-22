"""Quiet Corners: full-screen mockups of the whole UI in each state (for approval, not in the game).

Composed only from baked PBR pieces: the Bell Tower set (out/belltower), Thornrose (out/thornrose), the kit HUD icons
(out/kit), kit2 slots (art/ui/kit2/out@2x) and the new sets (out/quietcorners, out/evidence, out/dialogue), over the
repo's own in-game screenshots (docs/img). Layout is in 1920x1080 design px drawn at 2x (3840x2160). The phone is
844x390 points at 3x, with the kit's phone scales (0.62; the Bell Tower 0.5).

THE FIT CHECK. Every text is placed in a content box measured from its art, and the build fails when:
  - a text is under 20 design px (the house rule),
  - a text leaves its box (clips its UI),
  - two texts overlap,
  - a text partly overlaps a UI piece it does not sit on (runs through other UI).

  python make_quietcorners_mockups.py   -> docs/superpowers/mockups/2026-11-21-quietcorners/*.jpg
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BT = HERE / "out" / "belltower"
if not BT.exists():   # out/belltower is not tracked; the R1 mockup folder carries the same art
    BT = ROOT / "docs" / "superpowers" / "mockups" / "2026-11-20-belltower" / "art"
QC = HERE / "out" / "quietcorners"
EV = HERE / "out" / "evidence"
DL = HERE / "out" / "dialogue"
TR = HERE / "out" / "thornrose"
KIT = HERE / "out" / "kit"
K2 = ROOT / "art" / "ui" / "kit2" / "out@2x"
IMG = ROOT / "docs" / "img"
OUT = ROOT / "docs" / "superpowers" / "mockups" / "2026-11-21-quietcorners"
OUT.mkdir(parents=True, exist_ok=True)

BONE = (236, 226, 206)
DIM = (200, 188, 168)
GOLD = (230, 190, 108)
AMBER = (238, 154, 64)
CRIMSON = (220, 52, 62)
INK = (40, 22, 16)
INK_DIM = (92, 62, 46)
INK_RED = (130, 18, 24)
CHALK = (226, 222, 210)

FONTS = "C:/Windows/Fonts/"
_fc = {}


def font(px, kind="r"):
    key = (round(px * 4) / 4, kind)
    if key not in _fc:
        name = {"r": "georgia.ttf", "b": "georgiab.ttf", "i": "georgiai.ttf", "bi": "georgiaz.ttf"}[kind]
        _fc[key] = ImageFont.truetype(FONTS + name, max(6, round(px)))
    return _fc[key]


_pc = {}


def load(path):
    if path not in _pc:
        _pc[path] = Image.open(path).convert("RGBA")
    return _pc[path]


class FitError(Exception):
    pass


class Screen:
    """A canvas in layout units (design px, or phone points); s = output px per unit; k = kit text scale."""

    def __init__(self, bg, w=1920, h=1080, s=2.0, k=1.0, name="screen"):
        self.w, self.h, self.s, self.k, self.name = w, h, s, k, name
        self.im = bg.convert("RGBA").resize((round(w * s), round(h * s)), Image.LANCZOS)
        self.texts = []     # (label, bbox px)
        self.solids = []    # (label, bbox px)
        self.errors = []

    def P(self, v):
        return round(v * self.s)

    # -- images
    def _reg(self, im, ox, oy, label, solid):
        if not solid:
            return
        bb = im.getchannel("A").point(lambda v: 255 if v > 60 else 0).getbbox()
        if bb:
            self.solids.append((label, (ox + bb[0], oy + bb[1], ox + bb[2], oy + bb[3])))

    def put(self, img, x, y, w, h=None, alpha=1.0, rot=0.0, solid=True, label=None):
        if not isinstance(img, Image.Image):
            label = label or Path(img).stem
            img = load(img)
        if h is None:
            h = w * img.height / img.width
        im = img.resize((max(1, self.P(w)), max(1, self.P(h))), Image.LANCZOS)
        if rot:
            im = im.rotate(-rot, resample=Image.BICUBIC, expand=True)
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        ox = self.P(x) - (im.width - self.P(w)) // 2
        oy = self.P(y) - (im.height - self.P(h)) // 2
        self.im.alpha_composite(im, (ox, oy))
        self._reg(im, ox, oy, label or "image", solid and alpha > 0.2)
        return h

    def nine(self, img, x, y, w, h, src, dst, alpha=1.0, solid=True, label=None):
        """9-slice: src = corner size in the art (px), dst = corner size on screen (units)."""
        label = label or Path(img).stem
        img = load(img)
        W, H = img.width, img.height
        out = Image.new("RGBA", (self.P(w), self.P(h)))
        d = self.P(dst)
        xs = [(0, src, 0, d), (src, W - src, d, self.P(w) - d), (W - src, W, self.P(w) - d, self.P(w))]
        ys = [(0, src, 0, d), (src, H - src, d, self.P(h) - d), (H - src, H, self.P(h) - d, self.P(h))]
        for sx0, sx1, dx0, dx1 in xs:
            for sy0, sy1, dy0, dy1 in ys:
                if dx1 > dx0 and dy1 > dy0:
                    out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS), (dx0, dy0))
        if alpha < 1:
            out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
        self.im.alpha_composite(out, (self.P(x), self.P(y)))
        self._reg(out, self.P(x), self.P(y), label, solid and alpha > 0.2)

    # -- text
    def text(self, x, y, s, px, col=BONE, kind="r", anchor="la", alpha=1.0, box=None, shadow=True, k=None, label=None):
        k = self.k if k is None else k
        if px < 20:
            self.errors.append(f"[{self.name}] text under 20 design px ({px}): {s!r}")
        f = font(px * k * self.s, kind)
        pos = (self.P(x), self.P(y))
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bb = d.textbbox(pos, s, font=f, anchor=anchor)
        if shadow:
            sh = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((pos[0] + self.P(1.5), pos[1] + self.P(2)), s, font=f, fill=(0, 0, 0, int(230 * alpha)), anchor=anchor)
            self.im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(self.P(2))))
        d.text(pos, s, font=f, fill=col + (int(255 * alpha),), anchor=anchor)
        self.im.alpha_composite(layer)
        tag = label or s
        if box is not None:
            bx = tuple(self.P(v) for v in box)
            if bb[0] < bx[0] - 1 or bb[1] < bx[1] - 1 or bb[2] > bx[2] + 1 or bb[3] > bx[3] + 1:
                self.errors.append(f"[{self.name}] text leaves its box: {tag!r} ink {bb} box {bx}")
        if alpha > 0.2:
            self.texts.append((tag, bb))
        return (bb[2] - bb[0]) / self.s

    def wrap(self, s, px, width, kind="r"):
        f = font(px * self.k * self.s, kind)
        lines, cur = [], ""
        for w_ in s.split():
            t = (cur + " " + w_).strip()
            if f.getlength(t) / self.s > width and cur:
                lines.append(cur)
                cur = w_
            else:
                cur = t
        lines.append(cur)
        return lines

    def para(self, x, y, s, px, width, lh, col=INK, kind="r", box=None, **kw):
        """Wrapped text, first line centred on y; returns the y of the line after the last."""
        lines = self.wrap(s, px, width, kind)
        for i, l in enumerate(lines):
            self.text(x, y + i * lh, l, px, col, kind, "lm", box=box, **kw)
        return y + len(lines) * lh

    # -- plain shapes (not registered: annotation, fills, threads)
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=2, dash=None, radius=0):
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        box = (self.P(x0), self.P(y0), self.P(x1), self.P(y1))
        if dash and outline:
            if fill:
                d.rectangle(box, fill=fill)
            on, off = self.P(dash[0]), self.P(dash[1])
            for (ax, ay, bx, by) in ((box[0], box[1], box[2], box[1]), (box[2], box[1], box[2], box[3]),
                                     (box[2], box[3], box[0], box[3]), (box[0], box[3], box[0], box[1])):
                L = math.hypot(bx - ax, by - ay)
                t = 0
                while t < L:
                    t2 = min(t + on, L)
                    d.line((ax + (bx - ax) * t / L, ay + (by - ay) * t / L, ax + (bx - ax) * t2 / L, ay + (by - ay) * t2 / L),
                           fill=outline, width=max(1, self.P(width)))
                    t += on + off
        else:
            d.rounded_rectangle(box, radius=self.P(radius), fill=fill, outline=outline, width=max(1, self.P(width)) if outline else 0)
        self.im.alpha_composite(layer)

    def thread(self, a, b, sag=24, col=(170, 20, 30), width=3.0):
        pts = []
        for i in range(41):
            t = i / 40
            pts.append((self.P(a[0] + (b[0] - a[0]) * t), self.P(a[1] + (b[1] - a[1]) * t + sag * math.sin(math.pi * t))))
        sh = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).line([(p[0] + self.P(3), p[1] + self.P(4)) for p in pts], fill=(0, 0, 0, 150), width=self.P(width), joint="curve")
        self.im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(self.P(2))))
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.line(pts, fill=col + (255,), width=self.P(width), joint="curve")
        d.line([(p[0], p[1] - self.P(0.8)) for p in pts], fill=(230, 90, 90, 120), width=max(1, self.P(width * 0.3)), joint="curve")
        self.im.alpha_composite(layer)

    def glow(self, x0, y0, x1, y1, col=(240, 190, 90), a=170, blur=10):
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle((self.P(x0), self.P(y0), self.P(x1), self.P(y1)), radius=self.P(10),
                                                outline=col + (a,), width=self.P(6))
        self.im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(self.P(blur / 2))))

    # -- the check
    def check(self):
        def inter(a, b):
            return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))

        def contains(o, i):
            return o[0] <= i[0] + 1 and o[1] <= i[1] + 1 and o[2] >= i[2] - 1 and o[3] >= i[3] - 1

        T = self.texts
        for i in range(len(T)):
            for j in range(i + 1, len(T)):
                if inter(T[i][1], T[j][1]) > 0:
                    self.errors.append(f"[{self.name}] texts overlap: {T[i][0]!r} / {T[j][0]!r}")
            for lab, sb in self.solids:
                if inter(T[i][1], sb) > 0 and not contains(sb, T[i][1]):
                    self.errors.append(f"[{self.name}] text runs through UI: {T[i][0]!r} over {lab}")
        if self.errors:
            raise FitError("\n".join(self.errors))

    def save(self, name, q=90):
        self.check()
        self.im.convert("RGB").save(OUT / name, quality=q, subsampling=0)
        print(f"  {name}: {len(self.texts)} texts fit, {len(self.solids)} pieces checked")
        return OUT / name


# ---------------------------------------------------------------- backgrounds
def bg(name, grade=None, blur=0, dark=1.0, crop=None):
    im = Image.open(IMG / name).convert("RGB")
    if crop:
        W, H = im.size
        tw = H * crop
        if tw <= W:
            x0 = (W - tw) / 2
            im = im.crop((int(x0), 0, int(x0 + tw), H))
        else:
            th = W / crop
            y0 = (H - th) / 2
            im = im.crop((0, int(y0), W, int(y0 + th)))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if grade == "night":
        r, g, b = im.split()
        im = Image.merge("RGB", (r.point(lambda v: int(v * 0.92)), g.point(lambda v: int(v * 0.97)), b.point(lambda v: min(255, int(v * 1.08)))))
    elif grade == "cine":
        im = ImageEnhance.Color(im).enhance(0.8)
        r, g, b = im.split()
        im = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.04 + 4))), g, b.point(lambda v: min(255, int(v * 1.1 + 6)))))
        im = ImageEnhance.Contrast(im).enhance(1.12)
    if dark != 1.0:
        im = ImageEnhance.Brightness(im).enhance(dark)
    return im.filter(ImageFilter.UnsharpMask(2, 60, 2)) if not blur else im


def vignette(scr, k=0.55):
    W, H = scr.im.size
    m = Image.radial_gradient("L").resize((W, H)).point(lambda v: int(min(255, max(0, (v - 90) * 1.6)) * k))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(m)
    scr.im.alpha_composite(black)


# ---------------------------------------------------------------- HUD pieces
def top_bar(scr, x, y, alpha=1.0, items=("Menu", "Chat", "Students"), k=1.0):
    w, h = 340 * k, 56 * k
    scr.nine(QC / "PlateTrimHuman.png", x, y, w, h, 120, 22 * k, alpha, label="TopBar")
    box = (x + 14 * k, y + 10 * k, x + w - 14 * k, y + h - 10 * k)
    cx = x + 26 * k
    for it in items:
        cx += scr.text(cx, y + h / 2, it, 20, DIM, anchor="lm", alpha=alpha, box=box) + 24 * k


def compass(scr, cx=960, y=8, alpha=1.0, facing=20.0, k=1.0, readout="Room 104 · Chemistry · 18 studs", race="Human"):
    """Today's strip format (Gui.Compass), new art: letters, 15-degree ticks, place icons, the tracked objective."""
    W, H = 560 * k, 52 * k
    x0 = cx - W / 2
    scr.put(QC / f"CompassStrip{race}.png", x0, y, W, H, alpha, label="CompassStrip")
    ppd = W / 150.0                                   # 150 degrees across the strip
    chan = (x0 + 24 * k, y + 8.4 * k, x0 + W - 24 * k, y + 43.6 * k)
    marks = {0: ("N", CRIMSON, 24, "b"), 90: ("E", BONE, 24, "b"), 180: ("S", BONE, 24, "b"), 270: ("W", BONE, 24, "b"),
             45: ("NE", DIM, 20, "r"), 135: ("SE", DIM, 20, "r"), 225: ("SW", DIM, 20, "r"), 315: ("NW", DIM, 20, "r")}
    used = []

    def fade_at(bx):
        return max(0.0, min(1.0, (W / 2 - abs(bx - cx)) / (0.22 * W / 2)))

    for brg, (s, col, px, kind) in marks.items():
        bx = cx + ((brg - facing + 180) % 360 - 180) * ppd
        if chan[0] + 20 * k < bx < chan[2] - 20 * k and abs(bx - cx) > 22 * k:
            scr.text(bx, y + H / 2, s, px, col, kind, "mm", alpha=alpha * fade_at(bx), box=chan, k=k)
            used.append(bx)
    bx = cx + ((35 - facing + 180) % 360 - 180) * ppd           # a classroom (quill/book icon)
    scr.put(KIT / "IconBook.png", bx - 12 * k, y + H / 2 - 12 * k, 24 * k, 24 * k, alpha, label="place icon")
    used.append(bx)
    ox = cx + ((-40 - facing + 180) % 360 - 180) * ppd          # the tracked objective, gold
    scr.put(QC / f"PromptPip{race}.png", ox - 13 * k, y + H / 2 - 13 * k, 26 * k, 26 * k, alpha, label="objective")
    used.append(ox)
    for b in range(0, 360, 15):
        bx = cx + ((b - facing + 180) % 360 - 180) * ppd
        if chan[0] < bx < chan[2] and all(abs(bx - u) > 16 * k for u in used) and abs(bx - cx) > 10 * k:
            hh = (9 if b % 45 else 13) * k
            scr.rect(bx - 0.8 * k, y + H / 2 - hh / 2, bx + 0.8 * k, y + H / 2 + hh / 2, fill=(220, 200, 160, int(200 * fade_at(bx) * alpha)))
    scr.put(QC / f"CompassLubber{race}.png", cx - 10 * k, y - 4 * k, 20 * k, 25 * k, alpha, label="lubber")
    if readout:
        scr.text(cx, y + H + 16 * k, readout, 20, DIM, anchor="mm", alpha=alpha * 0.95, k=k)


def slip(scr, x, y, title, sub, race="Human", alpha=1.0, k=1.0):
    w, h = 400 * k, 80 * k
    scr.put(QC / f"Slip{race}.png", x, y, w, h, alpha, label="Slip")
    box = (x + 0.14 * w, y + 0.06 * h, x + 0.97 * w, y + 0.78 * h)
    scr.text(x + 0.16 * w, y + 20 * k, title, 22, INK, "b", "lm", alpha=alpha, shadow=False, box=box, k=k)
    scr.text(x + 0.16 * w, y + 46 * k, sub, 20, INK_DIM, "r", "lm", alpha=alpha, shadow=False, box=box, k=k)


def dial(scr, x, y, size=176, hour=9.2, alpha=1.0):
    scr.put(BT / "Dial.png", x, y, size, size, alpha)
    scr.put(BT / "DialHand.png", x, y, size, size, alpha, rot=hour / 24 * 360 + 180, solid=False)


def lead_card(scr, x, y, w, title, objective=None, pips=None, journal=False, alpha=1.0, k=1.0, race="Human"):
    """LeadCard art 1000x300: title band (150..880, 30..92), body (150..880, 102..282)."""
    h = w * 0.3
    scr.put(BT / "LeadCard.png", x, y, w, h, alpha, label=f"LeadCard {title}")
    tb = (x + 0.15 * w, y + 0.1 * h, x + 0.88 * w, y + 0.307 * h)
    bb = (x + 0.15 * w, y + 0.34 * h, x + 0.88 * w, y + 0.94 * h)
    scr.text(tb[0] + 3 * k, (tb[1] + tb[3]) / 2, title, 24, INK, "b", "lm", alpha=alpha, shadow=False, box=tb, k=k)
    if objective:
        scr.text(bb[0], bb[1] + 0.13 * h, objective, 20, INK_DIM, "r", "lm", alpha=alpha, shadow=False, box=bb, k=k)
    if pips:
        ps = 0.2 * h
        py = bb[3] - ps - 0.06 * h
        for i in range(pips[1]):
            scr.put(BT / ("PipFang.png" if i < pips[0] else "PipEmpty.png"), bb[0] + i * ps * 1.12, py, ps, ps, alpha, label="pip")
        tx = bb[0] + pips[1] * ps * 1.12 + 6 * k
        scr.text(tx, py + ps / 2, f"{pips[0]} / {pips[1]}", 20, INK_DIM, anchor="lm", alpha=alpha, shadow=False, box=bb, k=k)
        if journal:
            cs = ps * 1.3
            jx = bb[0] + 0.5 * (bb[2] - bb[0])
            cy = py + ps / 2 - cs / 2
            scr.put(QC / f"PromptCap{race}.png", jx, cy, cs, cs, alpha, label="J cap")
            scr.text(jx + cs / 2, cy + cs / 2, "J", 20, GOLD, "b", "mm", alpha=alpha, k=k,
                     box=(jx + 0.1 * cs, cy + 0.1 * cs, jx + 0.9 * cs, cy + 0.9 * cs))
            scr.text(jx + cs + 6 * k, py + ps / 2, "Journal", 20, INK, anchor="lm", alpha=alpha, shadow=False, box=bb, k=k)


def tower(scr, alpha=1.0, dial_alpha=None, fold=False, bells=0, state="Lit", lead=True, seal=None, status=None,
          report=None, hour=9.2, lines=("Tue  9:12 AM", "Period 2 · ends 9:45", "Now: Chemistry · R104"), race="Human"):
    """The Bell Tower cluster, top-right (R1 layout), 470 design px wide."""
    X1 = 1920 - 30
    dial(scr, X1 - 176, 24, 176, hour, alpha if dial_alpha is None else dial_alpha)
    if not fold:
        x, y, w, h = X1 - 176 - 10 - 300, 52, 300, 124
        scr.nine(QC / f"PlateTrim{race}.png", x, y, w, h, 120, 30, alpha, label="TowerPlate")
        box = (x + 18, y + 18, x + w - 18, y + h - 18)
        scr.text(x + 24, y + 38, lines[0], 28, BONE, "b", "lm", alpha=alpha, box=box)
        scr.text(x + 24, y + 70, lines[1], 20, DIM, "r", "lm", alpha=alpha, box=box)
        scr.text(x + 24, y + 94, lines[2], 20, GOLD, "r", "lm", alpha=alpha, box=box)
    y = 214
    if bells:
        rw = 470
        scr.put(BT / "BellRail.png", X1 - rw, y, rw, rw * 220 / 1400, alpha)
        hooks = [0.128, 0.29, 0.46, 0.628, 0.795]
        for i in range(bells):
            hx = X1 - rw + rw * hooks[i]
            art = {"Hollow": "BellHollow", "Tarnished": "BellTarnished", "Lit": "BellLit", "Search": "BellLit"}[state]
            if state == "Lit":
                scr.put(BT / "BellGlow.png", hx - 46, y + 18, 92, 92, alpha * 0.55, solid=False)
            scr.put(BT / f"{art}.png", hx - 30, y + 30, 60, 60, alpha)
        y += 104
        if status:
            scr.text(X1, y + 10, status[0], 20, CRIMSON, "b", "rm", alpha=alpha)
            scr.text(X1, y + 38, status[1], 20, BONE, "r", "rm", alpha=alpha)
            y += 52
        if report:
            scr.text(X1, y + 10, report, 20, AMBER, "r", "rm", alpha=alpha)
            y += 30
        y += 10
    if seal and not fold:
        scr.put(BT / f"Seal{seal[0]}.png", X1 - 64, y, 64, 64, alpha)
        scr.text(X1 - 78, y + 18, seal[1], 22, AMBER, "b", "rm", alpha=alpha)
        scr.text(X1 - 78, y + 46, seal[2], 20, DIM, "r", "rm", alpha=alpha)
        y += 80
    if lead and not fold:
        lead_card(scr, X1 - 470, y, 470, "The Missing Hymnal", "Search the chapel organ loft", (1, 3), True, alpha)


def vitals(scr, health=1.0, posture=0.0, alpha=1.0, form=(180, 18, 34), cx=960, y=905, hotbar=True, hb_alpha=None,
           posture_alpha=None, scale=1.0, k=None):
    """Thornrose health + posture briar + hotbar, bottom-centre."""
    W = 600 * scale
    x = cx - W / 2
    vel = load(TR / "ThornVelvet.png")
    v = Image.blend(vel, Image.new("RGBA", vel.size, form + (255,)), 0.75)
    win_x, win_w = x + 37.5 * scale, 525 * scale
    scr.rect(win_x, y + 15 * scale, win_x + win_w, y + 35 * scale, fill=(10, 4, 6, int(235 * alpha)))
    if health > 0:
        scr.put(v, win_x, y + 15 * scale, win_w * health, 20 * scale, alpha, solid=False)
    scr.put(TR / "ThornFrame.png", x, y - 15 * scale, W, 75 * scale, alpha, solid=False)
    pa = alpha if posture_alpha is None else posture_alpha
    py = y + 47 * scale
    if posture > 0:
        half = 300 * scale * posture
        scr.rect(cx - half, py + 7 * scale, cx + half, py + 17 * scale, fill=(232, 150, 52, int(235 * pa)) if posture < 0.8 else (240, 92, 40, int(240 * pa)))
    scr.put(TR / "PostureBriar.png", x, py, W, 24 * scale, pa, solid=False)
    r = 72.5 * scale
    glass = load(TR / "ThornGlass.png")
    g = Image.new("RGBA", glass.size, form + (255,))
    g.putalpha(glass.getchannel("A"))
    scr.put(Image.blend(g, glass, 0.35), cx - r * 0.3, y + 25 * scale - r * 0.3, r * 0.6, r * 0.6, alpha, solid=False)
    scr.put(TR / "ThornRose.png", cx - r / 2, y + 25 * scale - r / 2, r, r, alpha, label="ThornRose")
    scr.text(cx, y + 25 * scale, f"{round(health * 100)}%", 20, BONE, "b", "mm", alpha=alpha, k=k,
             box=(cx - r / 2, y + 25 * scale - r / 2, cx + r / 2, y + 25 * scale + r / 2))
    if hotbar:
        ha = alpha if hb_alpha is None else hb_alpha
        n, sz, gap = 9, 54 * scale, 6 * scale
        hx = cx - (n * sz + (n - 1) * gap) / 2
        hy = py + 34 * scale
        icons = ["IconBook", "IconCup", "IconKeys", "IconFlame", "IconBandage", None, None, None, None]
        for i in range(n):
            sx = hx + i * (sz + gap)
            scr.put(K2 / "slot.png", sx, hy, sz, sz, ha * (1 if i < 5 else 0.75), label=f"slot{i + 1}")
            if icons[i]:
                scr.put(KIT / f"{icons[i]}.png", sx + sz * 0.4, hy + sz * 0.4, sz * 0.52, sz * 0.52, ha, label=icons[i])
            if scale >= 1:
                scr.text(sx + 7, hy + 6, str(i + 1), 20, GOLD if i == 0 else DIM, "b", "la", alpha=ha * 0.95,
                         box=(sx, hy, sx + sz, hy + sz))


def health_line(scr, health=1.0, alpha=1.0):
    x0, x1 = 960 - 262, 960 + 262
    scr.rect(x0, 1040, x1, 1044, fill=(20, 8, 10, int(200 * alpha)))
    scr.rect(x0, 1040, x0 + (x1 - x0) * health, 1044, fill=(196, 26, 40, int(240 * alpha)))


def prompt(scr, x, y, key, action, obj, race="Human", k=1.0):
    c = 56 * k
    tw, th = 320 * k, 64 * k
    tx, ty = x + c - 6 * k, y + (c - th) / 2
    scr.put(QC / f"PromptTag{race}.png", tx, ty, tw, th, label="PromptTag")
    scr.put(QC / f"PromptCap{race}.png", x, y, c, c, label="PromptCap")
    scr.text(x + c / 2, y + c / 2, key, 22 if len(key) == 1 else 20, GOLD, "b", "mm",
             box=(x + 0.12 * c, y + 0.15 * c, x + 0.88 * c, y + 0.85 * c), k=k)
    box = (tx + 0.11 * tw, ty + 0.08 * th, tx + 0.9 * tw, ty + 0.92 * th)
    scr.text(box[0] + 4 * k, ty + 21 * k, action, 22, INK, "b", "lm", shadow=False, box=box, k=k)
    scr.text(box[0] + 4 * k, ty + 45 * k, obj, 20, INK_DIM, "r", "lm", shadow=False, box=box, k=k)


def pip(scr, x, y, race="Human", size=26):
    scr.put(QC / f"PromptPip{race}.png", x - size / 2, y - size / 2, size, size, 0.85)


def keycap(scr, x, y, key, label, col=INK, size=40, shadow=False, box=None, race="Human"):
    scr.put(QC / f"PromptCap{race}.png", x, y, size, size, label=f"cap {key}")
    scr.text(x + size / 2, y + size / 2, key, 20, GOLD, "b", "mm",
             box=(x + 0.1 * size, y + 0.12 * size, x + 0.9 * size, y + 0.88 * size))
    return size + 8 + scr.text(x + size + 8, y + size / 2, label, 20, col, "r", "lm", shadow=shadow, box=box) + 26


# ---------------------------------------------------------------- the HUD screens
def explore(mode):
    scr = Screen(bg("signs50-corridor.jpg", "night"), name=f"explore-{mode}")
    ghost = 0.35
    if mode == "ghost":
        top_bar(scr, 16, 10, ghost)
        compass(scr, alpha=ghost)
        slip(scr, 24, 80, "Text from Odette Marsh", "\"Library, after the bell?\"")    # woke: full
        tower(scr, alpha=ghost)
        vitals(scr, 1.0, 0.0, alpha=ghost)
    else:
        dial(scr, 1920 - 30 - 176, 24, 176, 9.2, 0.9)
        health_line(scr, 1.0, 0.8)
        slip(scr, 24, 16, "Text from Odette Marsh", "\"Library, after the bell?\"")
    prompt(scr, 452, 520, "E", "Open", "Mathematics · Room 12")
    pip(scr, 1112, 690)
    return scr.save(f"01-explore-{mode}.jpg")


def combat():
    scr = Screen(bg("gates51-lane.jpg", "night", dark=0.95), name="combat")
    top_bar(scr, 16, 10, 0.35)
    compass(scr, alpha=0.35, readout=None)
    scr.put(QC / "SlipHuman.png", 24, 80, 220, 44, 0.8, label="queued slips")
    scr.text(24 + 0.16 * 220, 80 + 19, "2 waiting", 20, INK, "b", "lm", alpha=0.85, shadow=False,
             box=(24 + 0.14 * 220, 80 + 2, 24 + 0.97 * 220, 80 + 0.8 * 44))
    tower(scr, fold=True, bells=3, state="Lit", lead=False,
          status=("NAMED", "Mr. Hale sees you · the Gate Lane"), report="Odette Marsh is going to tell Mr. Hale")
    vitals(scr, 0.62, 0.86)
    vignette(scr, 0.35)
    return scr.save("02-combat.jpg")


def cut():
    scr = Screen(bg("garden-courtyard-night.jpg", "cine"), name="cut")
    vignette(scr, 0.6)
    scr.text(960, 950, "Okay. Quiet. Very quiet.", 26, BONE, "i", "mm")
    scr.text(960, 988, "You", 20, DIM, "r", "mm")
    x, y, s = 1920 - 120, 1080 - 120, 72
    scr.put(QC / "SkipRingHuman.png", x, y, s, s)
    fill = load(QC / "SkipRingFill.png").copy()
    w, h = fill.size
    mask = Image.new("L", fill.size, 0)
    ImageDraw.Draw(mask).pieslice((0, 0, w, h), -90, -90 + 360 * 0.4, fill=255)
    col = Image.new("RGBA", fill.size, (232, 176, 80, 255))
    col.putalpha(Image.composite(fill.getchannel("A"), Image.new("L", fill.size, 0), mask))
    scr.put(col, x, y, s, s, solid=False)
    scr.text(x + s / 2, y + s / 2, "E", 22, GOLD, "b", "mm", box=(x + 18, y + 18, x + s - 18, y + s - 18))
    scr.text(x - 14, y + s / 2, "Hold to skip", 20, DIM, "r", "rm")
    return scr.save("03-seamless-cut.jpg")


def menu():
    scr = Screen(bg("secret53-library.jpg", blur=14, dark=0.42), name="menu-book")
    bx, by, bw, bh = 50, 68, 1660, 943
    f = bw / 2048
    scr.put(QC / "Book.png", bx, by, bw, bh)
    left = (bx + 110 * f, by + 96 * f, bx + 1000 * f, by + 1068 * f)
    right = (bx + 1170 * f, by + 96 * f, bx + 1938 * f, by + 1068 * f)
    for i, t in enumerate(["Journal", "Almanac", "Ledger", "Record", "Settings"]):
        ty = by + 120 + i * 92
        scr.put(QC / ("BookTabOn.png" if i == 0 else "BookTab.png"), bx + bw - 24, ty, 150, 60, label=f"tab {t}")
        tb = (bx + bw + 2, ty + 6, bx + bw - 24 + 140, ty + 54)
        scr.text(bx + bw + 6, ty + 30, t, 20, BONE if i == 0 else DIM, "b" if i == 0 else "r", "lm", box=tb)
    lx = left[0] + 6
    scr.text(lx, left[1] + 40, "THE JOURNAL", 34, INK, "b", "lm", shadow=False, box=left)
    scr.text(lx, left[1] + 84, "Leads you are following", 20, INK_DIM, "i", "lm", shadow=False, box=left)
    leads = [("The Missing Hymnal", "Tracked · 1 of 3 clues", True), ("Whispers in Room 106", "Talk to the custodian", False),
             ("A Debt to the Court", "¥40 owed by Friday", False), ("The Bell That Rang Twice", "New", False)]
    for i, (t, s, on) in enumerate(leads):
        lead_card(scr, left[0] - 4, left[1] + 112 + i * 164, 520, t, s, alpha=1.0 if on else 0.88)
    rx = right[0] + 6
    scr.text(rx, right[1] + 40, "The Missing Hymnal", 32, INK, "b", "lm", shadow=False, box=right)
    scr.text(rx, right[1] + 84, "Started Tuesday · from Sister Agathe", 20, INK_DIM, "i", "lm", shadow=False, box=right)
    yb = scr.para(rx, right[1] + 140, "The chapel's hymnal went missing the night the bell rang twice. Sister Agathe "
                  "thinks a student took it up to the organ loft.", 22, right[2] - rx - 20, 34, INK, box=right, shadow=False)
    scr.text(rx, yb + 10, "Next: Search the organ loft.", 22, INK_RED, "b", "lm", shadow=False, box=right)
    for i in range(3):
        scr.put(BT / ("PipFang.png" if i < 1 else "PipEmpty.png"), rx + i * 52, yb + 44, 46, 46, label="pip")
    scr.text(rx + 170, yb + 67, "1 of 3 clues", 20, INK_DIM, "r", "lm", shadow=False, box=right)
    sx, sy = rx, yb + 120
    scr.put(BT / "Slip.png", sx, sy, 420, 150, label="Slip")
    sb = (sx + 0.2 * 420, sy + 0.24 * 150, sx + 0.95 * 420, sy + 0.78 * 150)
    scr.text(sb[0] + 4, sy + 60, "Detention owed", 22, INK, "b", "lm", shadow=False, box=sb)
    scr.text(sb[0] + 4, sy + 92, "Room 106, after class", 20, INK_DIM, "r", "lm", shadow=False, box=sb)
    x, fy = rx, right[3] - 60
    for key, lab in (("LB", "Tab"), ("RB", "Tab"), ("A", "Track"), ("B", "Close")):
        x += keycap(scr, x, fy, key, lab, box=right)
    return scr.save("04-menu-book.jpg")


def phone():
    k = 0.62
    scr = Screen(bg("signs50-corridor.jpg", "night", crop=844 / 390), w=844, h=390, s=3.0, k=k, name="phone")
    top_bar(scr, 10, 6, 0.6, ("Menu", "Chat", "Journal"), k=k)
    compass(scr, cx=422, y=6, alpha=0.6, k=k, readout=None)
    slip(scr, 10, 50, "Text from Odette Marsh", "\"Library, after the bell?\"", k=k)
    kb = 0.5
    X1 = 844 - 12
    dial(scr, X1 - 140 * kb, 6, 140 * kb, 9.2, 0.6)
    x, y, w, h = X1 - 140 * kb - 6 - 300 * kb, 14, 300 * kb, 124 * kb
    scr.nine(QC / "PlateTrimHuman.png", x, y, w, h, 120, 30 * kb, 0.6, label="TowerPlate")
    box = (x + 18 * kb, y + 18 * kb, x + w - 18 * kb, y + h - 18 * kb)
    scr.text(x + 24 * kb, y + 38 * kb, "Tue  9:12 AM", 28, BONE, "b", "lm", alpha=0.6, box=box, k=kb)
    scr.text(x + 24 * kb, y + 70 * kb, "Period 2 · ends 9:45", 20, DIM, "r", "lm", alpha=0.6, box=box, k=kb)
    scr.text(x + 24 * kb, y + 94 * kb, "Now: Chemistry", 20, GOLD, "r", "lm", alpha=0.6, box=box, k=kb)
    lead_card(scr, X1 - 470 * kb, 6 + 140 * kb + 8, 470 * kb, "The Missing Hymnal", alpha=0.6, k=kb)
    # touch arcs: jump 70 pt; inner arc r 84 (180, 135, 90 deg); outer r 150 (172, 145, 118, 91)
    jx, jy = 844 - 50, 390 - 50
    orbs = [("JUMP", 0, 0, 70)]
    for lab, th in (("STRIKE", 180), ("BLOCK", 135), ("DODGE", 90)):
        orbs.append((lab, 84 * math.cos(math.radians(th)), -84 * math.sin(math.radians(th)), 60))
    for lab, th in (("HEAVY", 172), ("RUN", 145), ("CROUCH", 118), ("DRAW", 91)):
        orbs.append((lab, 150 * math.cos(math.radians(th)), -150 * math.sin(math.radians(th)), 64))
    for lab, dx, dy, d in orbs:
        cx, cy = jx + dx, jy + dy
        scr.rect(cx - d / 2 + 4, cy - d / 2 + 4, cx + d / 2 - 4, cy + d / 2 - 4, fill=(18, 12, 16, 190), radius=d / 2)
        scr.put(QC / "SkipRingHuman.png", cx - d / 2, cy - d / 2, d, d, 0.95, label=f"orb {lab}")
        scr.text(cx, cy, lab, 20, BONE, "r", "mm", box=(cx - d * 0.45, cy - d * 0.3, cx + d * 0.45, cy + d * 0.3))
    vitals(scr, 0.88, 0.2, alpha=0.6, cx=300, y=298, scale=k, k=k)
    prompt(scr, 236, 196, "TAP", "Open", "Mathematics · Room 12", k=k)
    return scr.save("05-phone.jpg")


def zones():
    scr = Screen(bg("signs50-corridor.jpg", "night", dark=0.45), name="zones-pc")
    Z = [((16, 4, 470, 330), (90, 170, 230), "TOP-LEFT", ["top bar", "event slips (max 3)"]),
         ((680, 4, 1240, 100), (150, 220, 170), "TOP-CENTRE", ["compass strip (today's format)"]),
         ((1390, 4, 1904, 640), (226, 186, 104), "TOP-RIGHT · BELL TOWER", ["dial · bells · seal · lead"]),
         ((640, 880, 1280, 1072), (214, 44, 56), "BOTTOM-CENTRE", ["Thornrose · posture · hotbar"]),
         ((480, 216, 1440, 864), (236, 226, 206), "CENTRE CLEAR", ["no HUD, ever", "only in-world prompts"])]
    for (x0, y0, x1, y1), col, title, lines in Z:
        scr.rect(x0, y0, x1, y1, fill=col + (34,), outline=col + (230,), width=3, dash=(14, 10) if title == "CENTRE CLEAR" else None)
        box = (x0, y0, x1, y1)
        scr.text(x0 + 16, y0 + 22, title, 22, col, "b", "lm", box=box)
        for i, l in enumerate(lines):
            scr.text(x0 + 16, y0 + 52 + i * 28, l, 20, BONE, "r", "lm", box=box)
    scr.rect(96, 54, 1824, 1026, outline=(140, 220, 160, 220), width=2, dash=(6, 8))
    scr.text(1810, 1004, "console title-safe 90%", 20, (150, 230, 170), "r", "rm")
    return scr.save("00-zones-pc-console.jpg")


def zones_phone():
    k = 0.62
    scr = Screen(bg("signs50-corridor.jpg", "night", crop=844 / 390, dark=0.45), w=844, h=390, s=3.0, k=k, name="zones-phone")
    Z = [((6, 4, 236, 130), (90, 170, 230), "top bar · slips (max 2)"),
         ((246, 4, 598, 48), (150, 220, 170), "compass strip"),
         ((604, 4, 838, 150), (226, 186, 104), "Bell Tower at 0.5"),
         ((40, 286, 580, 386), (214, 44, 56), "vitals + hotbar"),
         ((610, 160, 840, 386), (150, 120, 220), "touch arcs"),
         ((210, 140, 570, 278), (236, 226, 206), "centre clear")]
    for (x0, y0, x1, y1), col, title in Z:
        scr.rect(x0, y0, x1, y1, fill=col + (34,), outline=col + (230,), width=1.2, dash=(5, 4) if title == "centre clear" else None)
        scr.text(x0 + 6, y0 + 12, title, 20, col, "b", "lm", box=(x0, y0, x1, y1))
    return scr.save("00-zones-phone.jpg")


def races():
    names = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]
    notes = ["warm brass · crimson wax", "gilt silver · holy-blue enamel", "blackened silver · garnet",
             "hammered copper · amber", "verdigris bronze · bone-green", "frosted pewter · pale-blue glass"]
    scr = Screen(Image.new("RGB", (10, 10), (14, 12, 18)), name="races")
    for i, (n, note) in enumerate(zip(names, notes)):
        col, row = i % 3, i // 3
        x, y = 40 + col * 626, 40 + row * 520
        scr.rect(x, y, x + 600, y + 494, fill=(24, 20, 28, 255), radius=10)
        scr.text(x + 24, y + 30, n.upper(), 28, BONE, "b", "lm")
        scr.text(x + 24, y + 66, note, 20, DIM, "i", "lm")
        scr.nine(QC / f"PlateTrim{n}.png", x + 24, y + 96, 340, 100, 120, 26, label="plate")
        pb = (x + 24 + 16, y + 96 + 14, x + 364 - 16, y + 196 - 14)
        scr.text(x + 48, y + 128, "Tue  9:12 AM", 28, BONE, "b", "lm", box=pb)
        scr.text(x + 48, y + 164, "Now: Chemistry", 20, GOLD, "r", "lm", box=pb)
        scr.put(QC / f"PromptCap{n}.png", x + 400, y + 100, 64, 64, label="cap")
        scr.text(x + 432, y + 132, "E", 24, GOLD, "b", "mm", box=(x + 412, y + 112, x + 452, y + 152))
        scr.put(QC / f"PromptPip{n}.png", x + 490, y + 114, 36, 36)
        scr.put(QC / f"BookCorner{n}.png", x + 474, y + 176, 100, 100)
        slip(scr, x + 24, y + 214, "Rumour going round", "about the Ink Club", race=n)
        scr.put(QC / f"CompassStrip{n}.png", x + 24, y + 316, 420, 39)
        scr.put(QC / f"CompassLubber{n}.png", x + 226, y + 312, 16, 20)
        scr.put(EV / f"Tack{n}.png", x + 470, y + 300, 44, 44)
        scr.put(QC / f"SkipRing{n}.png", x + 524, y + 296, 52, 52)
        scr.text(x + 24, y + 400, "Danger crimson is the same", 20, (210, 110, 110), "i", "lm")
        scr.text(x + 24, y + 430, "for every race.", 20, (210, 110, 110), "i", "lm")
    return scr.save("06-bloodline-trims.jpg")


# ---------------------------------------------------------------- the Evidence Wall
CASE_Q = "Where is Mira Holt's original record kept?"
CARD_W, CARD_H = 220, 300
PHOTO_DESK = ("classroom-corner.jpg", 0.42, 0.45, 0.22)


def _photo(spec):
    ph = Image.open(IMG / spec[0]).convert("RGB")
    W, H = ph.size
    cw, ch = W * spec[3], W * spec[3] * 175 / 190
    ph = ImageEnhance.Color(ph.crop((int(W * spec[1]), int(H * spec[2]), int(W * spec[1] + cw), int(H * spec[2] + ch)))).enhance(0.3)
    r, g, b = ph.split()
    return Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.08 + 10))), g, b.point(lambda v: int(v * 0.85)))).convert("RGBA")


def card(scr, kind, x, y, title, where, quote=None, photo=None, tack="Human"):
    """A clue card. Its kind shows as shape AND word. Boxes are measured from each card's art (440x600)."""
    w, h = CARD_W, CARD_H
    if kind == "Photo":
        if photo:
            scr.put(_photo(photo), x + 15, y + 15, 190, 175, solid=False)
        scr.put(EV / "CardPhoto.png", x, y, w, h, label=f"card {title}")
        box = (x + 14, y + 196, x + 206, y + 292)
        scr.text(x + 18, y + 212, "PHOTO", 20, INK_RED, "b", "lm", shadow=False, box=box)
        scr.para(x + 18, y + 242, title, 22, 186, 28, INK, kind="b", box=box, shadow=False)
        scr.text(x + 18, y + 272, where, 20, INK_DIM, "r", "lm", shadow=False, box=box)
    else:
        art = {"Note": "CardNote", "Record": "CardRecord", "Object": "CardObject"}[kind]
        scr.put(EV / f"{art}.png", x, y, w, h, label=f"card {title}")
        box = {"Note": (x + 38, y + 24, x + 210, y + 292), "Record": (x + 12, y + 8, x + 205, y + 292),
               "Object": (x + 12, y + 48, x + 208, y + 292)}[kind]
        tx = box[0] + 4
        ty = box[1] + 20
        scr.text(tx, ty, kind.upper(), 20, INK_RED, "b", "lm", shadow=False, box=box)
        ty2 = scr.para(tx, ty + 32, title, 22, box[2] - tx - 4, 28, INK, kind="b", box=box, shadow=False)
        ny = scr.para(tx, ty2, where, 20, box[2] - tx - 4, 26, INK_DIM, box=box, shadow=False)
        if quote:
            scr.para(tx, ny + 14, quote, 20, box[2] - tx - 4, 26, INK, kind="i", box=box, shadow=False)
    scr.put(EV / f"Tack{tack}.png", x + w / 2 - 15, y - 12, 30, 30, label="tack")
    return (x + w / 2, y + 3)


def missing(scr, x, y, title, where):
    scr.put(EV / "CardMissing.png", x, y, CARD_W, CARD_H, label="missing")
    box = (x + 14, y + 14, x + CARD_W - 14, y + CARD_H - 14)
    scr.text(x + CARD_W / 2, y + 56, "Not found yet", 22, CHALK, "b", "mm", box=box)
    scr.para(x + 26, y + 96, title, 20, CARD_W - 52, 26, CHALK, box=box)
    scr.para(x + 26, y + 150, f"Somewhere in {where}.", 20, CARD_W - 52, 26, DIM, kind="i", box=box)
    keycap(scr, x + 26, y + 226, "X", "Mark it", col=CHALK, size=40, shadow=True, box=box)


def mini(scr, kind, x, y, w=120, h=164, photo=None, alpha=1.0, lift=False):
    """A pinned copy of a clue inside a slot (no text: the thread names it)."""
    if lift:
        scr.rect(x + 10, y + 14, x + w + 10, y + h + 14, fill=(0, 0, 0, 90), radius=6)
    if kind == "Photo" and photo:
        scr.put(_photo(photo), x + w * 15 / 220, y + h * 15 / 300, w * 190 / 220, h * 175 / 300, alpha, solid=False)
    art = {"Photo": "CardPhoto", "Note": "CardNote", "Record": "CardRecord", "Object": "CardObject"}[kind]
    scr.put(EV / f"{art}.png", x, y, w, h, alpha, label="mini card")


def sheet(scr, x, y, ask, w=720, h=252):
    scr.put(EV / "QuestionSheet.png", x, y, w, h, label=f"sheet: {ask}")
    qb = (x + 22, y + 4, x + w - 22, y + 0.195 * h)
    scr.text(x + 28, (y + 4 + y + 0.195 * h) / 2, ask, 24, INK, "b", "lm", shadow=False, box=qb)
    return (x + 30, y + 0.24 * h, x + w - 24, y + h - 12)      # the body box


def slot_at(scr, x, y, w=120, h=164, glow=False):
    if glow:
        scr.glow(x - 4, y - 4, x + w + 4, y + h + 4)
    scr.put(EV / "Slot.png", x, y, w, h, label="slot")


def wall_base(name, clues, answered):
    scr = Screen(Image.new("RGB", (10, 10), (8, 6, 8)), name=name)
    scr.put(EV / "Wall.png", 0, 0, 1920, 1080, label="Wall")
    cork = (60, 60, 1860, 1020)
    scr.put(EV / "CasePlateHuman.png", 560, 70, 800, 100, label="CasePlate")
    face = (560 + 800 * 64 / 1600, 70 + 100 * 26 / 200, 560 + 800 * 1536 / 1600, 70 + 100 * 174 / 200)
    scr.text(960, 120, CASE_Q, 28, (44, 26, 12), "b", "mm", shadow=False, box=face)
    scr.text(92, 104, "CASE 01", 22, GOLD, "b", "lm", box=cork)
    scr.text(92, 134, "The Empty Desk", 20, BONE, "r", "lm", box=cork)
    scr.text(1830, 104, clues, 22, BONE, "b", "rm", box=cork)
    scr.text(1830, 134, answered, 20, DIM, "r", "rm", box=cork)
    frame_b = (60, 1022, 1860, 1078)
    x = 96
    for key, lab in (("A", "Pick up / pin"), ("X", "Inspect"), ("B", "Close")):
        x += keycap(scr, x, 1030, key, lab, col=BONE, size=40, shadow=True, box=frame_b)
    return scr


def wall_cards(scr):
    a = card(scr, "Note", 100, 230, "The locker note", "Locker 113", "\"Before they finish erasing her.\"")
    b = card(scr, "Photo", 370, 230, "Carved initials", "Room 102, back row", photo=PHOTO_DESK)
    c = card(scr, "Record", 100, 590, "The register", "Room 101", "Line 14 scraped clean.")
    return a, b, c


def evidence_wall():
    scr = wall_base("evidence-wall", "Clues 3 of 4", "Answered 1 of 2")
    a, b, c = wall_cards(scr)
    missing(scr, 370, 590, "A borrowing card", "the Library Archive")
    X = 1110
    body = sheet(scr, X, 190, "What is happening to Mira?")
    s1, s2 = (body[0], body[1] + 6), (body[0] + 134, body[1] + 6)
    slot_at(scr, *s1)
    slot_at(scr, *s2)
    mini(scr, "Photo", *s1, photo=PHOTO_DESK)
    mini(scr, "Record", *s2)
    scr.put(BT / "SealDetention.png", body[0] + 272, body[1] + 2, 56, 56, label="seal")
    scr.text(body[0] + 340, body[1] + 30, "Answered", 22, INK_RED, "b", "lm", shadow=False, box=body)
    scr.para(body[0] + 272, body[1] + 82, "Someone is erasing Mira Holt, and she knew it was coming.", 20,
             body[2] - body[0] - 282, 26, INK, kind="i", box=body, shadow=False)
    body = sheet(scr, X, 454, "Where did the original register go?")
    t1, t2 = (body[0], body[1] + 6), (body[0] + 134, body[1] + 6)
    slot_at(scr, *t1)
    slot_at(scr, *t2)
    mini(scr, "Record", *t1)
    scr.text(t2[0] + 60, t2[1] + 82, "?", 40, CHALK, "b", "mm", box=(t2[0] + 20, t2[1] + 20, t2[0] + 100, t2[1] + 144))
    scr.para(body[0] + 272, body[1] + 20, "1 of 2 pinned. The other clue is still out there: try where the school keeps its books.",
             20, body[2] - body[0] - 282, 26, INK, box=body, shadow=False)
    body = sheet(scr, X, 718, "Who else knew? (bonus)")
    u1, u2 = (body[0], body[1] + 6), (body[0] + 134, body[1] + 6)
    slot_at(scr, *u1, glow=True)
    slot_at(scr, *u2)
    scr.para(body[0] + 272, body[1] + 20, "Drop a clue on the question it answers. A wrong one slides back with a hint.",
             20, body[2] - body[0] - 282, 26, INK_DIM, box=body, shadow=False)
    scr.thread((b[0], b[1] + 2), (s1[0] + 60, s1[1] + 8), sag=40)
    scr.thread((c[0], c[1] + 2), (s2[0] + 60, s2[1] + 150), sag=40)
    scr.thread((c[0], c[1] + 2), (t1[0] + 60, t1[1] + 8), sag=30)
    mini(scr, "Note", u1[0] + 16, u1[1] - 18, lift=True)
    for p in (s1, t1):
        scr.put(EV / "TackHuman.png", p[0] + 45, p[1] - 8, 30, 30, label="tack")
    scr.put(EV / "TackHuman.png", s2[0] + 45, s2[1] + 134, 30, 30, label="tack")
    return scr.save("07-evidence-wall.jpg")


def evidence_answer(solved=False):
    scr = wall_base("evidence-solved" if solved else "evidence-answer", "Clues 4 of 4", "Answered 2 of 2")
    wall_cards(scr)
    card(scr, "Record", 370, 590, "A borrowing card", "The Library Archive", "Returned to Records.")
    X = 1110
    for i, (ask, ins) in enumerate((("What is happening to Mira?", "Someone is erasing Mira Holt."),
                                    ("Where did the original register go?", "Back to the Records Office."))):
        body = sheet(scr, X, 190 + i * 170, ask, h=160)
        scr.put(BT / "SealDetention.png", body[0], body[1] + 2, 44, 44, label="seal")
        scr.para(body[0] + 56, body[1] + 24, ins, 20, body[2] - body[0] - 66, 26, INK, kind="i", box=body, shadow=False)
    if not solved:
        scr.text(X + 6, 540, "Your answer", 24, BONE, "b", "lm")
        scr.text(X + 6, 572, "Pick the place your clues point to.", 20, DIM, "i", "lm")
        for i, o in enumerate(["The Library Archive", "The Records Office", "The Boiler Yard", "Room 102"]):
            x = X + (i % 2) * 366
            y = 604 + (i // 2) * 186
            if i == 1:
                scr.glow(x - 4, y - 4, x + 344, y + 174)
            scr.put(EV / "AnswerCardHuman.png", x, y, 340, 170, label=f"answer {o}")
            scr.text(x + 170, y + 85, o, 22, INK, "b", "mm", shadow=False,
                     box=(x + 0.12 * 340, y + 0.2 * 170, x + 0.88 * 340, y + 0.8 * 170))
            if i == 1:
                scr.put(EV / "TackHuman.png", x + 155, y - 12, 30, 30, label="tack")
        return scr.save("08-evidence-answer.jpg")
    x, y = X + 120, 530
    scr.put(EV / "AnswerCardHuman.png", x, y, 480, 240, label="answer")
    scr.text(x + 240, y + 120, "The Records Office", 30, INK, "b", "mm", shadow=False,
             box=(x + 0.12 * 480, y + 0.2 * 240, x + 0.88 * 480, y + 0.8 * 240))
    st = Image.new("RGBA", (960, 360), (0, 0, 0, 0))
    ink = load(EV / "StampInk.png").resize((960, 360), Image.LANCZOS)
    col = Image.new("RGBA", ink.size, (176, 20, 30, 255))
    col.putalpha(ink.getchannel("A"))
    st.alpha_composite(col)
    d = ImageDraw.Draw(st)
    f = font(150, "b")
    bb = d.textbbox((480, 180), "SOLVED", font=f, anchor="mm")
    if not (bb[0] > 80 and bb[2] < 880 and bb[1] > 70 and bb[3] < 290):
        raise FitError("[evidence-solved] the stamp word leaves the stamp")
    d.text((480, 180), "SOLVED", font=f, fill=(176, 20, 30, 235), anchor="mm")
    scr.put(st, X + 150, 786, 420, 157, rot=-6, label="stamp")
    tb = (X, 960, X + 720, 1018)
    scr.para(X + 10, 976, "The originals never leave the Records Office, and it's locked after hours.", 20, 700, 26,
             BONE, kind="i", box=tb)
    scr.text(X + 10, 1004, "Reward: ¥25 · Trust · Academics", 20, GOLD, "b", "lm", box=tb)
    return scr.save("09-evidence-solved.jpg")


# ---------------------------------------------------------------- dialogue
def dialogue():
    scr = Screen(bg("lounge-corner.jpg", "night", dark=0.8), name="dialogue")
    vignette(scr, 0.5)
    scr.rect(0, 0, 1920, 36, fill=(0, 0, 0, 255))          # the talk cinematic's thin bars (NHTalkBars)
    scr.rect(0, 1044, 1920, 1080, fill=(0, 0, 0, 255))
    rx, ry, rw, rh = 110, 830, 1100, 150
    scr.put(DL / "Ribbon.png", rx, ry, rw, rh, label="Ribbon")
    rb = (rx + 0.1 * rw, ry + 0.2 * rh, rx + 0.9 * rw, ry + 0.8 * rh)
    line = "You came back. Nobody comes back after their first night in Room 106."
    width = 0.74 * rw
    lines = scr.wrap(line, 24, width)
    y0 = ry + rh / 2 - (len(lines) - 1) * 17
    scr.para(rx + 0.12 * rw, y0, line, 24, width, 34, INK, box=rb, shadow=False)
    lw = font(24 * scr.s).getlength(lines[-1]) / scr.s
    scr.put(DL / "Nib.png", rx + 0.12 * rw + lw + 12, y0 + (len(lines) - 1) * 34 - 14, 28, 28, label="nib")
    cx, cy, cw, ch = 120, 708, 520, 120
    scr.put(DL / "CallingCardHuman.png", cx, cy, cw, ch, label="CallingCard")
    sx, sy, sr = cx + 60, cy + 60, 47
    scr.put(DL / "CrestInk.png", sx - sr, sy - sr, 2 * sr, 2 * sr, label="clique crest")   # the Ink Club
    fb = (cx + 235 * cw / 1040, cy + 34 * ch / 240, cx + 988 * cw / 1040, cy + 206 * ch / 240)
    scr.text(fb[0] + 8, cy + 44, "ODETTE MARSH", 24, BONE, "b", "lm", box=fb)
    scr.text(fb[0] + 8, cy + 89, "The Ink Club · second year", 20, DIM, "r", "lm", box=fb)
    replies = [("What happened in Room 106?", "Ask"), ("Maybe you could show me around?", "Kind"),
               ("Pay her ¥10 to keep quiet", "Sly"), ("Stay out of my way.", "Threat")]
    tx, tw, th = 1330, 540, 69
    for i, (t, tone) in enumerate(replies):
        ty = 690 + i * 78
        on = i == 0
        scr.put(DL / f"ReplyTab{'On' if on else ''}Human.png", tx, ty, tw, th, label=f"reply {i + 1}")
        sock = (tx + 26 / 1000 * tw, ty + 20 / 128 * th, tx + 114 / 1000 * tw, ty + 108 / 128 * th)
        scr.text((sock[0] + sock[2]) / 2, ty + th / 2, str(i + 1), 22, INK if on else GOLD, "b", "mm", box=sock)
        ib = (tx + 132 / 1000 * tw, ty + 24 / 128 * th, tx + 948 / 1000 * tw, ty + 104 / 128 * th)
        scr.text(ib[0] + 10, ty + th / 2, t, 22, BONE if on else DIM, "b" if on else "r", "lm", box=ib)
        scr.put(DL / f"Tone{tone}.png", ib[2] - 40, ty + th / 2 - 16, 32, 32, label=f"tone {tone}")
    scr.text(1870, 1018, "1-4 reply · click the line to skip · walk away to leave", 20, DIM, "r", "rm")
    return scr.save("10-dialogue.jpg")


def overview(paths):
    thumbs = [Image.open(p).convert("RGB") for p in paths]
    W = 1920
    tw = (W - 30) // 2
    rows = [t.resize((tw, round(tw * t.height / t.width)), Image.LANCZOS) for t in thumbs]
    H = 10 + sum(max(rows[i].height, rows[i + 1].height if i + 1 < len(rows) else 0) + 10 for i in range(0, len(rows), 2))
    out = Image.new("RGB", (W, H), (14, 12, 18))
    y = 10
    for i in range(0, len(rows), 2):
        out.paste(rows[i], (10, y))
        if i + 1 < len(rows):
            out.paste(rows[i + 1], (20 + tw, y))
        y += max(rows[i].height, rows[i + 1].height if i + 1 < len(rows) else 0) + 10
    out.save(OUT / "overview.jpg", quality=88)


if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    fns = {"zones": zones, "zones_phone": zones_phone, "ghost": lambda: explore("ghost"), "vanish": lambda: explore("vanish"),
           "combat": combat, "cut": cut, "menu": menu, "phone": phone, "races": races, "wall": evidence_wall,
           "answer": lambda: evidence_answer(False), "solved": lambda: evidence_answer(True), "dialogue": dialogue}
    ps, failed = [], []
    for key, fn in fns.items():
        if only and key not in only:
            continue
        try:
            ps.append(fn())
        except FitError as e:
            failed.append(str(e))
    if failed:
        print("FIT CHECK FAILED\n" + "\n".join(failed))
        sys.exit(1)
    if not only:
        overview(ps)
    print("ok", OUT)
