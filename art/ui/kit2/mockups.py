"""Nightmare Highschool UI mock-ups v2 (for approval, not in the game).

Composed from the PBR UI kit2 pieces rendered at 2x (art/ui/kit2/out@2x) and the PBR school crest
(art/logo/out/nh_logo_pbr.png), over a blurred daytime game backdrop. Output 3840x2160 (layout is written in
1920x1080 units and scaled by S).

A layout checker runs on every screen: every element is registered in a scope (panel, card, row...). Siblings
in a scope may not overlap and must sit inside the scope's content area; any violation fails the build.

usage: python art/ui/kit2/mockups.py [backdrop.jpg]   -> art/ui/kit2/mockups/*.png
"""
import contextlib
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "out@2x") if os.path.isfile(os.path.join(HERE, "out@2x", "crest.png")) else os.path.join(HERE, "out")
KS = 2.0 if KIT.endswith("@2x") else 1.0          # kit art scale
OUT = os.path.join(HERE, "mockups")
os.makedirs(OUT, exist_ok=True)
CREST = os.path.join(HERE, "..", "..", "logo", "out", "nh_logo_pbr.png")
BG = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/mock_bg.jpg"
S = 2                     # output scale
W, H = 1920, 1080         # layout units

FONTS = "C:/Windows/Fonts/"
_fc = {}
def F(size, kind="r"):
    key = (size, kind)
    if key not in _fc:
        name = {"r": "georgia.ttf", "b": "georgiab.ttf", "i": "georgiai.ttf", "bi": "georgiaz.ttf", "sym": "seguisym.ttf"}[kind]
        _fc[key] = ImageFont.truetype(FONTS + name, int(size * S))
    return _fc[key]

BONE = (234, 224, 204)
DIM = (168, 156, 140)
FAINT = (118, 108, 100)
GOLD = (222, 180, 98)
CRIMSON = (204, 40, 52)
GOOD = (140, 210, 140)
BAD = (230, 116, 104)
RAR = {"Common": (176, 172, 164), "Uncommon": (108, 182, 116), "Rare": (92, 152, 228), "Epic": (174, 108, 228),
       "Legendary": (236, 174, 66), "Mythic": (226, 58, 68)}
RACE = {"Vampire": (214, 52, 64), "Human": (218, 184, 112), "Werewolf": (214, 134, 62), "Ghoul": (134, 176, 124)}

_cache = {}
def piece(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(KIT, name + ".png")).convert("RGBA")
    return _cache[name]


def nine(img, w, h, m):
    iw, ih = img.size
    out = Image.new("RGBA", (w, h))
    m = min(m, w // 2, h // 2)
    for sx0, sx1, dx0, dx1 in ((0, m, 0, m), (m, iw - m, m, w - m), (iw - m, iw, w - m, w)):
        for sy0, sy1, dy0, dy1 in ((0, m, 0, m), (m, ih - m, m, h - m), (ih - m, ih, h - m, h)):
            if dx1 > dx0 and dy1 > dy0:
                out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS), (dx0, dy0))
    return out


def hnine(img, w, h, m):
    sc = h / img.height
    im2 = img.resize((max(1, int(img.width * sc)), h), Image.LANCZOS)
    mm = max(1, min(int(m * sc), w // 2))
    out = Image.new("RGBA", (w, h))
    out.paste(im2.crop((0, 0, mm, h)), (0, 0))
    out.paste(im2.crop((im2.width - mm, 0, im2.width, h)), (w - mm, 0))
    out.paste(im2.crop((mm, 0, im2.width - mm, h)).resize((max(1, w - 2 * mm), h), Image.LANCZOS), (mm, 0))
    return out


def tint(img, col, amt=0.5):
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    gray = rgb.convert("L")
    colored = Image.merge("RGB", [gray.point(lambda v, c=c: min(255, int(v * c / 150))) for c in col])
    return Image.merge("RGBA", (*Image.blend(rgb, colored, amt).split(), a))


class LayoutError(Exception):
    pass


class Canvas:
    def __init__(self, name, dim=0.55):
        self.name = name
        self.im = self._backdrop(dim)
        self.d = ImageDraw.Draw(self.im)
        self.scopes = [("screen", (16, 16, W - 16, H - 16), [])]
        self.errors = []

    @contextlib.contextmanager
    def scope(self, name, inner):
        self.scopes.append((name, inner, []))
        try:
            yield
        finally:
            self.scopes.pop()

    def reg(self, box, label, overlay=False):
        x0, y0, x1, y1 = box
        name, inner, items = self.scopes[-1]
        tol = 1
        if x0 < inner[0] - tol or y0 < inner[1] - tol or x1 > inner[2] + tol or y1 > inner[3] + tol:
            self.errors.append(f"{self.name}: '{label}' {tuple(int(v) for v in box)} spills out of {name} {tuple(int(v) for v in inner)}")
        if not overlay:
            G = 4   # minimum breathing room between siblings
            for (b, l) in items:
                if x0 < b[2] + G and b[0] < x1 + G and y0 < b[3] + G and b[1] < y1 + G:
                    self.errors.append(f"{self.name}: '{label}' overlaps '{l}' in {name}")
            items.append((box, label))

    def _backdrop(self, dim):
        bg = Image.open(BG).convert("RGB")
        PW, PH = W * S, H * S
        sc = max(PW / bg.width, PH / bg.height)
        bg = bg.resize((int(bg.width * sc) + 1, int(bg.height * sc) + 1), Image.LANCZOS)
        bg = bg.crop(((bg.width - PW) // 2, (bg.height - PH) // 2, (bg.width - PW) // 2 + PW, (bg.height - PH) // 2 + PH))
        bg = bg.filter(ImageFilter.GaussianBlur(7 * S))
        bg = Image.blend(bg, Image.new("RGB", (PW, PH), (8, 5, 10)), dim)
        v = Image.new("L", (PW // 8, PH // 8), 0)
        ImageDraw.Draw(v).ellipse((-PW // 20, -PH // 18, PW // 8 + PW // 20, PH // 8 + PH // 18), fill=255)
        v = v.filter(ImageFilter.GaussianBlur(20)).resize((PW, PH), Image.LANCZOS)
        return Image.composite(bg, Image.new("RGB", (PW, PH), (0, 0, 0)), v).convert("RGBA")

    def paste(self, img, x, y, alpha=1.0):
        if alpha < 1:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        self.im.alpha_composite(img, (int(x * S), int(y * S)))

    def shadow(self, x, y, w, h, spread=26, alpha=170, dy=16):
        pad = spread * 3
        sh = Image.new("RGBA", (int((w + pad * 2) * S), int((h + pad * 2) * S)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad * S, pad * S, (pad + w) * S, (pad + h) * S), radius=24 * S, fill=(0, 0, 0, alpha))
        self.paste(sh.filter(ImageFilter.GaussianBlur(spread * S)), x - pad, y - pad + dy)

    def text(self, x, y, s, size=24, kind="r", fill=BONE, anchor="la", label=None, overlay=False, track=0):
        f = F(size, kind)
        if track:
            # manual letter-spacing: lay the glyphs out one by one (Georgia has no thin space)
            sp = size * 0.14 * track * S
            widths = [self.d.textlength(ch, font=f) for ch in s]
            total = sum(widths) + sp * (len(s) - 1)
            va = "l" + anchor[1]
            ref = self.d.textbbox((0, 0), s, font=f, anchor=va)
            x0p = x * S - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
            px = x0p
            for ch, cw in zip(s, widths):
                self.d.text((px + 2 * S, y * S + 2 * S), ch, font=f, fill=(0, 0, 0, 210), anchor=va)
                self.d.text((px, y * S), ch, font=f, fill=fill, anchor=va)
                px += cw + sp
            box = (x0p / S, (y * S + ref[1]) / S, (x0p + total) / S, (y * S + ref[3]) / S)
            self.reg(box, label or s[:24], overlay)
            return box
        bb = self.d.textbbox((x * S, y * S), s, font=f, anchor=anchor)
        self.d.text((x * S + 2 * S, y * S + 2 * S), s, font=f, fill=(0, 0, 0, 210), anchor=anchor)
        self.d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)
        box = (bb[0] / S, bb[1] / S, bb[2] / S, bb[3] / S)
        self.reg(box, label or s[:24], overlay)
        return box

    def glyph(self, x, y, ch, size, fill=BONE, glow=None, label="glyph", overlay=True):
        if glow:
            r = size * 0.9
            g = Image.new("RGBA", (int(r * 4 * S), int(r * 4 * S)), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse((r * S, r * S, 3 * r * S, 3 * r * S), fill=glow + (120,))
            self.paste(g.filter(ImageFilter.GaussianBlur(r * 0.6 * S)), x - 2 * r, y - 2 * r)
        f = F(size, "sym")
        self.d.text((x * S + 2 * S, y * S + 3 * S), ch, font=f, fill=(0, 0, 0, 200), anchor="mm")
        self.d.text((x * S, y * S), ch, font=f, fill=fill, anchor="mm")
        bb = self.d.textbbox((x * S, y * S), ch, font=f, anchor="mm")
        self.reg((bb[0] / S, bb[1] / S, bb[2] / S, bb[3] / S), label, overlay)

    def panel(self, x, y, w, h, label="panel"):
        self.shadow(x + 40, y + 40, w - 80, h - 80, 40, 200, 24)
        self.paste(nine(piece("panel"), int(w * S), int(h * S), int(110 * KS)), x, y)
        self.reg((x + 40, y + 40, x + w - 40, y + h - 40), label)
        return (x + 148, y + 142, x + w - 148, y + h - 142)  # clear of the frame, trim and stitched seam (~125 in)

    def card(self, x, y, w, h, col=None, amt=0.4, label="card"):
        self.shadow(x + 20, y + 20, w - 40, h - 40, 18, 160, 10)
        c = nine(piece("card"), int(w * S), int(h * S), int(64 * KS))
        self.paste(tint(c, col, amt) if col else c, x, y)
        self.reg((x + 18, y + 18, x + w - 18, y + h - 18), label)
        return (x + 58, y + 50, x + w - 58, y + h - 48)      # clear of the card's trim

    def row(self, x, y, w, h, label="row"):
        self.paste(hnine(piece("row"), int(w * S), int(h * S), int(70 * KS)), x, y)
        self.reg((x + 8, y, x + w - 8, y + h), label)
        return (x + 34, y + 8, x + w - 62, y + h - 8)      # keep clear of the iron end caps

    def well(self, x, y, w, h, label="well"):
        im = Image.new("RGBA", (int(w * S), int(h * S)), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=14 * S, fill=(14, 9, 11, 235))
        inner = Image.new("L", im.size, 0)
        ImageDraw.Draw(inner).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=14 * S, outline=255, width=int(18 * S))
        inner = inner.filter(ImageFilter.GaussianBlur(10 * S))
        im = Image.alpha_composite(im, Image.merge("RGBA", (*[Image.new("L", im.size, 0)] * 3, inner.point(lambda v: v // 2))))
        ImageDraw.Draw(im).rounded_rectangle((2 * S, 2 * S, w * S - 3 * S, h * S - 3 * S), radius=13 * S, outline=(150, 112, 62, 200), width=max(1, int(1.5 * S)))
        self.paste(im, x, y)
        self.reg((x, y, x + w, y + h), label)
        return (x + 14, y + 14, x + w - 14, y + h - 14)

    def slot(self, x, y, s, col=None, label="slot"):
        sl = piece("slot").resize((int(s * S), int(s * S)), Image.LANCZOS)
        self.paste(tint(sl, col, 0.32) if col else sl, x, y)
        self.reg((x, y, x + s, y + s), label)

    def button(self, x, y, w, h, label, size=22, col=GOLD):
        self.paste(hnine(piece("button"), int(w * S), int(h * 1.2 * S), int(60 * KS)), x, y - h * 0.1)
        self.reg((x, y, x + w, y + h), "button " + label)
        with self.scope("button " + label, (x + 10, y + 4, x + w - 10, y + h - 4)):
            self.text(x + w / 2, y + h / 2, label, size, "b", col, "mm", label="btn-text " + label)

    def chip(self, x, y, key, desc):
        f = F(16, "b")
        kw = self.d.textlength(key, font=f) / S + 18
        self.d.rounded_rectangle((x * S, y * S, (x + kw) * S, (y + 28) * S), radius=6 * S, fill=(20, 14, 16), outline=GOLD, width=max(1, int(1.2 * S)))
        self.d.text(((x + kw / 2) * S, (y + 14) * S), key, font=f, fill=GOLD, anchor="mm")
        self.reg((x, y, x + kw, y + 28), "chip " + key)
        b = self.text(x + kw + 10, y + 14, desc, 16, "r", DIM, "lm", label="chip-desc " + desc)
        return b[2]

    def bar(self, x, y, w, h, frac, col, ticks=10, label="bar"):
        d = self.d
        d.rounded_rectangle(((x - 2) * S, (y - 2) * S, (x + w + 2) * S, (y + h + 2) * S), radius=(h / 2 + 2) * S, fill=(8, 6, 8))
        d.rounded_rectangle((x * S, y * S, (x + w) * S, (y + h) * S), radius=h / 2 * S, fill=(28, 16, 20))
        if frac > 0:
            fw = max(h, w * frac)
            grad = Image.new("RGBA", (int(fw * S), int(h * S)))
            gd = ImageDraw.Draw(grad)
            for i in range(int(h * S)):
                t = i / max(1, h * S - 1)
                gd.line((0, i, fw * S, i), fill=tuple(min(255, int(v * (1.3 - 0.6 * t))) for v in col) + (255,))
            m = Image.new("L", grad.size, 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, grad.width - 1, grad.height - 1), radius=h / 2 * S, fill=255)
            grad.putalpha(m)
            self.paste(grad, x, y)
        for k in range(1, ticks):
            tx = x + w * k / ticks
            d.line((tx * S, (y + 1) * S, tx * S, (y + h - 1) * S), fill=(0, 0, 0, 110), width=max(1, int(S)))
        self.reg((x - 2, y - 2, x + w + 2, y + h + 2), label)

    def divider(self, x0, x1, y, glyph="☾", label="divider"):
        d = self.d
        mid = (x0 + x1) / 2
        for xa, xb in ((x0, mid - 22), (mid + 22, x1)):
            d.line((xa * S, y * S, xb * S, y * S), fill=(120, 30, 38), width=int(2 * S))
            d.line((xa * S, (y + 3) * S, xb * S, (y + 3) * S), fill=(70, 50, 30), width=max(1, int(S)))
        d.polygon([((mid - 14) * S, y * S), (mid * S, (y - 10) * S), ((mid + 14) * S, y * S), (mid * S, (y + 10) * S)], fill=(150, 112, 62))
        self.reg((x0, y - 12, x1, y + 12), label)
        self.glyph(mid, y, glyph, 12, (40, 10, 14), label="divider glyph")

    def crest(self, x, y, s, label="crest"):
        c = Image.open(CREST).convert("RGBA")
        hh = s * c.height / c.width
        self.paste(c.resize((int(s * S), int(hh * S)), Image.LANCZOS), x, y)
        self.reg((x, y, x + s, y + hh), label)
        return hh

    def header(self, inner, title, sub, right=None):
        x0, y0, x1, _ = inner
        self.crest(x0, y0, 112)
        self.text(x0 + 140, y0 + 6, title, 46, "b", GOLD, track=2, label="title")
        self.text(x0 + 142, y0 + 66, sub, 20, "i", DIM, label="subtitle")
        self.slot(x1 - 56, y0, 56, label="close")
        self.glyph(x1 - 28, y0 + 28, "✕", 24, BAD, label="close glyph")
        if right:
            self.text(x1 - 76, y0 + 104, right, 24, "b", GOLD, "rb", label="header right")
        self.divider(x0 + 140, x1, y0 + 128, label="header divider")
        return y0 + 140

    def footer(self, inner, chips, right=None):
        x0, _, x1, y1 = inner
        x = x0
        for k, dsc in chips:
            x = self.chip(x, y1 - 30, k, dsc) + 26
        if right:
            self.text(x1, y1 - 16, right, 20, "b", GOLD, "rm", label="footer right")

    def save(self):
        if self.errors:
            raise LayoutError("\n".join(self.errors))
        p = os.path.join(OUT, self.name + ".png")
        self.im.convert("RGB").save(p, optimize=True)
        print("[mock]", p)


# ------------------------------------------------------------------ screens

def party():
    c = Canvas("party")
    inner = c.panel(110, 24, 1030, 1032)
    with c.scope("party panel", inner):
        top = c.header(inner, "STUDY GROUP", "Up to four students share EXP from every fight", "3 / 4")
        x0, _, x1, y1 = inner
        wi = c.well(x0, top + 6, x1 - x0, 4 * 116 + 20, "member list")
        with c.scope("member list", wi):
            members = [("Rin Kurosawa", "Vampire", 22, 0.86, 0.55, True, "🦇"), ("Kaito Mori", "Werewolf", 18, 0.42, 0.9, False, "☾"),
                       ("You", "Human", 14, 1.0, 0.3, False, "✝")]
            ry = wi[1]
            for name, race, lv, hp, post, lead, g in members:
                ri = c.row(wi[0], ry, wi[2] - wi[0], 108, "row " + name)
                with c.scope("row " + name, ri):
                    c.slot(ri[0], ri[1] + 2, 86, RACE[race], "portrait")
                    c.glyph(ri[0] + 43, ri[1] + 45, g, 40, RACE[race], glow=RACE[race])
                    nb = c.text(ri[0] + 104, ri[1] + 10, name, 26, "b", BONE, label="name")
                    if lead:
                        c.glyph(nb[2] + 22, ri[1] + 30, "♛", 24, GOLD, label="crown", overlay=False)
                    c.text(ri[0] + 108, ri[1] + 56, f"{race.upper()}  ·  LV {lv}", 17, "b", RACE[race], label="race")
                    bx = ri[0] + 380
                    c.text(bx, ri[1] + 4, "HEALTH", 13, "b", DIM, label="hp label")
                    c.bar(bx, ri[1] + 24, 130, 14, hp, (200, 42, 54), label="hp")
                    c.text(bx, ri[1] + 46, "POSTURE", 13, "b", DIM, label="post label")
                    c.bar(bx, ri[1] + 66, 130, 10, post, (222, 180, 98), label="post")
                    if name != "You":
                        c.slot(ri[2] - 58, ri[1] + 16, 56, label="kick")
                        c.glyph(ri[2] - 30, ri[1] + 44, "⛓", 24, FAINT, label="kick glyph")
                ry += 116
            ri = c.row(wi[0], ry, wi[2] - wi[0], 108, "row invite")
            with c.scope("row invite", ri):
                c.slot(ri[0], ri[1] + 2, 86, label="empty portrait")
                c.glyph(ri[0] + 43, ri[1] + 45, "✚", 32, FAINT)
                c.text(ri[0] + 108, ri[1] + 30, "Invite a classmate…", 26, "i", FAINT, label="invite hint")
        by = wi[3] + 26
        c.button(x0, by, 240, 64, "INVITE")
        c.button(x0 + 260, by, 240, 64, "LEAVE", col=BAD)
        c.text(x1, by + 32, "Shared EXP  +10%", 22, "b", GOLD, "rm", label="bonus")
        c.footer(inner, [("P", "Close"), ("Click", "Inspect member")])
    ci = c.card(1190, 90, 620, 360, label="invite card")
    with c.scope("invite card", ci):
        c.slot(ci[0], ci[1] + 6, 96, RACE["Ghoul"], "invite portrait")
        c.glyph(ci[0] + 48, ci[1] + 54, "💀", 44, RACE["Ghoul"], glow=RACE["Ghoul"])
        c.text(ci[0] + 120, ci[1] + 6, "GROUP INVITE", 17, "b", CRIMSON, track=1, label="kicker")
        c.text(ci[0] + 120, ci[1] + 36, "Sora Hayashi", 30, "b", BONE, label="who")
        c.text(ci[0] + 120, ci[1] + 78, "Ghoul  ·  LV 20", 18, "b", RACE["Ghoul"], label="who race")
        c.text(ci[0], ci[1] + 126, "wants you in their Study Group", 20, "i", DIM, label="msg")
        c.bar(ci[0] + 3, ci[1] + 166, ci[2] - ci[0] - 6, 8, 0.62, (222, 180, 98), ticks=1, label="timer")
        c.button(ci[0], ci[3] - 64, 240, 60, "ACCEPT", 21)
        c.button(ci[2] - 240, ci[3] - 64, 240, 60, "DECLINE", 21, BAD)
    c.save()


ITEMS = [("🎭", "Fox Mask", "Rare"), ("⚔", "Training Katana", "Common"), ("🎩", "Gravedigger Hat", "Uncommon"),
         ("💍", "Signet of Night", "Epic"), ("🗡", "Silver Letter Opener", "Rare"), ("⚗", "Blood Tonic", "Common"),
         ("📜", "Detention Slip", "Common"), ("🔮", "Scrying Marble", "Legendary"), ("🕯", "Vigil Candle", "Uncommon"),
         ("⛓", "Chain Belt", "Uncommon"), ("🗝", "Archive Key", "Epic"), ("👁", "Third Eye Pin", "Mythic"),
         ("⌛", "Hourglass Charm", "Rare"), ("☠", "Skull Ring", "Common"), ("✝", "Rosary", "Uncommon"),
         ("⚜", "Prefect Badge", "Rare"), ("🦇", "Bat Brooch", "Common"), ("❤", "Locket", "Epic")]


def inventory():
    c = Canvas("inventory")
    inner = c.panel(80, 20, 1760, 1040)
    with c.scope("locker panel", inner):
        top = c.header(inner, "LOCKER", "Everything you carry. Gear stats are capped so nobody's broken")
        x0, _, x1, y1 = inner
        for i, t in enumerate(["ALL", "GEAR", "WEAPONS", "TONICS", "QUEST"]):
            c.button(x0 + i * 154, top + 8, 144, 52, t, 17, GOLD if i == 1 else DIM)
        s, gap = 98, 10
        gw = c.well(x0, top + 82, 7 * s + 6 * gap + 28, 4 * s + 3 * gap + 28, "grid well")
        with c.scope("grid well", gw):
            for i in range(28):
                sx, sy = gw[0] + (i % 7) * (s + gap), gw[1] + (i // 7) * (s + gap)
                if i < len(ITEMS):
                    g, n, r = ITEMS[i]
                    c.slot(sx, sy, s, RAR[r], "slot " + n)
                    c.glyph(sx + s / 2, sy + s / 2, g, 42, RAR[r] if r != "Common" else BONE,
                            glow=RAR[r] if r in ("Legendary", "Mythic", "Epic") else None)
                    c.d.polygon([((sx + s - 32) * S, (sy + 12) * S), ((sx + s - 12) * S, (sy + 12) * S), ((sx + s - 12) * S, (sy + 32) * S)], fill=RAR[r])
                    if n == "Blood Tonic":
                        c.text(sx + s - 14, sy + s - 12, "x3", 17, "b", BONE, "rs", overlay=True, label="stack")
                    if i == 0:
                        c.d.rounded_rectangle(((sx - 3) * S, (sy - 3) * S, (sx + s + 3) * S, (sy + s + 3) * S), radius=10 * S, outline=GOLD, width=int(3 * S))
                else:
                    c.slot(sx, sy, s, label=f"empty {i}")
        c.text(x0, gw[3] + 34, "¥ 1,240", 30, "b", GOLD, "lm", label="yen")
        c.text(gw[2], gw[3] + 34, "18 / 28 slots", 22, "r", DIM, "rm", label="capacity")
        di = c.card(gw[2] + 36, top + 8, x1 - gw[2] - 36, y1 - top - 58, RAR["Rare"], 0.25, "detail card")
        with c.scope("detail card", di):
            c.slot(di[0], di[1], 150, RAR["Rare"], "detail slot")
            c.glyph(di[0] + 75, di[1] + 75, "🎭", 68, RAR["Rare"], glow=RAR["Rare"])
            c.text(di[0] + 170, di[1] + 8, "RARE  ·  FACE", 17, "b", RAR["Rare"], track=1, label="rarity")
            c.text(di[0] + 170, di[1] + 40, "Fox Mask", 40, "b", BONE, label="item name")
            c.text(di[0] + 170, di[1] + 96, "Found in a gear chest", 19, "i", DIM, label="source")
            c.divider(di[0], di[2], di[1] + 182, "✦", label="detail divider")
            for i, (k, v, col) in enumerate([("Night Power", "+1.6%", GOOD), ("Stealth", "−0.8%", BAD), ("Combat EXP", "+2.0%", GOOD)]):
                yy = di[1] + 206 + i * 42
                c.text(di[0], yy, k, 23, "r", BONE, label="stat " + k)
                c.text(di[2], yy, v, 23, "b", col, "ra", label="val " + k)
            c.text(di[0], di[1] + 338, "\u201cIt grins whether you do or not.\u201d", 18, "i", DIM, label="flavour")
            c.button(di[0], di[3] - 66, 220, 62, "EQUIP")
            c.button(di[2] - 200, di[3] - 66, 200, 62, "DROP", col=BAD)
        c.footer(inner, [("TAB", "Close"), ("E", "Equip"), ("Q", "Drop"), ("Shift", "Compare")])
    c.save()


def notices():
    c = Canvas("notices", dim=0.35)
    ri = c.row(330, 30, 1260, 130, "event banner")
    with c.scope("event banner", ri):
        c.text(960, ri[1] + 38, "THE BLOOD MOON RISES", 40, "b", (244, 96, 96), "mm", track=2, label="event title")
        c.text(960, ri[1] + 86, "Supernatural powers +25% until dawn", 20, "i", BONE, "mm", label="event sub")
    lx, ly, lw, lh = 640, 210, 640, 660
    glow = Image.new("RGBA", (int((lw + 400) * S), int((lh + 400) * S)), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((140 * S, 140 * S, (lw + 260) * S, (lh + 260) * S), fill=RAR["Legendary"] + (150,))
    c.paste(glow.filter(ImageFilter.GaussianBlur(90 * S)), lx - 200, ly - 200)
    li = c.card(lx, ly, lw, lh, RAR["Legendary"], 0.42, "loot card")
    with c.scope("loot card", li):
        mid = (li[0] + li[2]) / 2
        c.text(mid, li[1] + 14, "GEAR CHEST", 19, "b", DIM, "mm", track=2, label="loot kicker")
        c.slot(mid - 115, li[1] + 44, 230, RAR["Legendary"], "loot slot")
        c.glyph(mid, li[1] + 159, "⌛", 110, RAR["Legendary"], glow=RAR["Legendary"])
        c.text(mid, li[1] + 314, "LEGENDARY", 25, "b", RAR["Legendary"], "mm", track=2, label="loot rarity")
        c.text(mid, li[1] + 358, "Crimson Pocket Watch", 38, "b", BONE, "mm", label="loot name")
        c.text(mid, li[1] + 404, "+3.0% Night Power   ·   +1.5% All EXP", 21, "r", GOOD, "mm", label="loot stats")
        c.text(mid, li[1] + 440, "New! Added to your Locker", 18, "i", DIM, "mm", label="loot note")
        c.button(mid - 130, li[3] - 66, 260, 62, "TAKE IT")
    toasts = [("GROUP INVITE", "Sora Hayashi wants you in their group", "💀", RACE["Ghoul"], True),
              ("TRADE REQUEST", "Kaito Mori offers a trade", "⚜", GOLD, True),
              ("DETENTION", "A Watcher saw you fight in the hall", "👁", CRIMSON, False)]
    for i, (k, msg, g, col, act) in enumerate(toasts):
        ti = c.card(1330, 200 + i * 220, 540, 204, label="toast " + k)
        with c.scope("toast " + k, ti):
            c.slot(ti[0], ti[1] + 4, 84, col, "toast icon")
            c.glyph(ti[0] + 42, ti[1] + 46, g, 38, col, glow=col)
            c.text(ti[0] + 102, ti[1] + 2, k, 16, "b", col, track=1, label="toast kicker")
            c.text(ti[0] + 102, ti[1] + 30, msg, 18, "r", BONE, label="toast msg")
            if act:
                bw = (ti[2] - ti[0] - 102 - 16) / 2
                c.button(ti[0] + 102, ti[3] - 48, bw, 44, "ACCEPT", 17)
                c.button(ti[0] + 102 + bw + 16, ti[3] - 48, bw, 44, "DECLINE", 17, BAD)
            else:
                c.text(ti[0] + 102, ti[1] + 70, "Report to Room 104 after class", 17, "i", DIM, label="toast note")
    with c.scope("ticker", (90, 880, 620, 1060)):
        for i, (s, col) in enumerate([("+85 EXP  ·  Combat", GOOD), ("¥ +30", GOLD), ("Gang Leader defeated", BONE)]):
            c.text(110, 896 + i * 50, s, 28, "b", col, label="ticker " + s)
    c.save()


def auction():
    c = Canvas("auction")
    inner = c.panel(70, 16, 1780, 1048)
    with c.scope("auction panel", inner):
        top = c.header(inner, "THE UNDERCROFT", "Student auction house. Bids are final; 5% goes to the Bursar")
        x0, _, x1, y1 = inner
        sw = c.well(x0, top + 8, 560, 58, "search")
        with c.scope("search", sw):
            c.text(sw[0] + 10, sw[1] + 15, "Search items…", 21, "i", FAINT, "lm", label="search hint")
            c.glyph(sw[2] - 18, sw[1] + 15, "👁", 22, DIM, label="search icon")
        for i, (lab, col) in enumerate([("Rare+", RAR["Rare"]), ("Epic+", RAR["Epic"]), ("Legendary", RAR["Legendary"]), ("Ending soon", BONE)]):
            c.button(x0 + 590 + i * 176, top + 8, 164, 58, lab, 18, col)
        lw = c.well(x0, top + 84, x1 - x0, 5 * 84 + 62, "listings")
        with c.scope("listings", lw):
            for k, cx in [("ITEM", lw[0] + 110), ("SELLER", lw[0] + 600), ("ENDS", lw[0] + 790), ("TOP BID", lw[0] + 950), ("BUYOUT", lw[0] + 1100)]:
                c.text(cx, lw[1] + 4, k, 15, "b", DIM, track=1, label="col " + k)
            rows = [("🔮", "Scrying Marble", "Legendary", "Rin K.", "12m", "¥ 8,400", "¥ 12,000"),
                    ("💍", "Signet of Night", "Epic", "Kaito M.", "41m", "¥ 3,150", "¥ 4,500"),
                    ("🗝", "Archive Key", "Epic", "Mina S.", "1h 20m", "¥ 2,900", "—"),
                    ("🎭", "Fox Mask", "Rare", "Sora H.", "2h 05m", "¥ 980", "¥ 1,400"),
                    ("⌛", "Hourglass Charm", "Rare", "Haru T.", "3h", "¥ 760", "¥ 1,100")]
            for i, (g, n, r, s, t, bid, buy) in enumerate(rows):
                ri = c.row(lw[0], lw[1] + 38 + i * 84, lw[2] - lw[0], 78, "row " + n)
                with c.scope("row " + n, ri):
                    c.slot(ri[0], ri[1] + 1, 60, RAR[r], "icon")
                    c.glyph(ri[0] + 30, ri[1] + 31, g, 28, RAR[r], glow=RAR[r] if r == "Legendary" else None)
                    c.text(lw[0] + 110, ri[1] + 6, n, 23, "b", BONE, label="name")
                    c.text(lw[0] + 110, ri[1] + 38, r.upper(), 14, "b", RAR[r], track=1, label="rarity")
                    c.text(lw[0] + 600, ri[1] + 20, s, 20, "r", BONE, label="seller")
                    c.text(lw[0] + 790, ri[1] + 20, t, 20, "b", BAD if i < 2 else BONE, label="ends")
                    c.text(lw[0] + 950, ri[1] + 18, bid, 22, "b", GOLD, label="bid")
                    c.text(lw[0] + 1100, ri[1] + 18, buy, 22, "r", BONE, label="buyout")
                    c.button(ri[2] - 140, ri[1] + 6, 136, 50, "BID", 19)
        c.button(x0, lw[3] + 20, 290, 52, "POST LISTING", 20)
        c.text(x1, lw[3] + 46, "Your listings: 2 active   ·   ¥ 1,240", 21, "r", DIM, "rm", label="your listings")
        c.chip(x0 + 320, lw[3] + 32, "H", "Close")
    c.save()


def store():
    c = Canvas("store")
    inner = c.panel(100, 30, 1720, 1020)
    with c.scope("store panel", inner):
        top = c.header(inner, "THE COMMISSARY", "Support the school. Nothing here makes you unbeatable")
        x0, _, x1, y1 = inner
        for i, t in enumerate(["FEATURED", "PASSES", "YEN", "COSMETICS"]):
            c.button(x0 + i * 206, top + 8, 194, 56, t, 18, GOLD if i == 0 else DIM)
        c.text(x1, top + 36, "Cosmetic or convenience only. Combat stats can't be bought.", 17, "i", FAINT, "rm", label="note")
        offers = [("⚜", "Yen Pouch", "¥ 5,000", "R$ 99", "Common", None),
                  ("⚜", "Yen Chest", "¥ 30,000  +10% bonus", "R$ 449", "Rare", "BEST VALUE"),
                  ("🔮", "Lineage Reroll  x3", "Spin your bloodline again", "R$ 149", "Epic", None),
                  ("📜", "Extra Character Slot", "A whole new student file", "R$ 199", "Uncommon", None),
                  ("♛", "Prefect Pass", "+10% EXP · name colour", "R$ 399", "Legendary", "POPULAR"),
                  ("🦇", "Blood Moon Cape", "Cosmetic · animated sway", "R$ 249", "Mythic", "NEW")]
        gap = 26
        cw = (x1 - x0 - 2 * gap) / 3
        chh = (y1 - (top + 84) - gap) / 2
        for i, (g, n, sub, price, r, tag) in enumerate(offers):
            cx = x0 + (i % 3) * (cw + gap)
            cy = top + 84 + (i // 3) * (chh + gap)
            ci = c.card(cx, cy, cw, chh, RAR[r], 0.32, "offer " + n)
            with c.scope("offer " + n, ci):
                c.slot(ci[0], ci[1], 86, RAR[r], "offer icon")
                c.glyph(ci[0] + 43, ci[1] + 43, g, 40, RAR[r], glow=RAR[r])
                c.text(ci[0] + 100, ci[1] + 2, n, 20, "b", BONE, label="offer name")
                c.text(ci[0] + 100, ci[1] + 34, sub, 14, "i", DIM, label="offer sub")
                if tag:
                    c.text(ci[0] + 100, ci[1] + 60, tag, 13, "b", CRIMSON, track=1, label="tag")
                c.button(ci[2] - 170, ci[3] - 48, 170, 46, price, 21)
        pass
    c.save()


def skilltree():
    c = Canvas("skilltree")
    inner = c.panel(100, 30, 1720, 1020)
    with c.scope("tree panel", inner):
        top = c.header(inner, "CURRICULUM", "Spend study points. Each branch caps at 10", "4 POINTS")
        x0, _, x1, y1 = inner
        tw = c.well(x0, top + 8, 980, y1 - top - 72, "tree well")
        branches = [("BODY", (206, 64, 64), ["⚔", "❤", "⛨", "⚡", "✦"], 3), ("MIND", (116, 136, 226), ["👁", "📜", "⌛", "🔮", "✦"], 1),
                    ("BLOOD", (180, 34, 64), ["🦇", "☾", "⛧", "☠", "✦"], 2)]
        node = piece("node")
        with c.scope("tree well", tw):
            colw = (tw[2] - tw[0]) / 3
            step = (tw[3] - tw[1] - 60) / 5
            s = min(96, step - 16)
            for bi, (name, col, glyphs, learned) in enumerate(branches):
                bx = tw[0] + colw * (bi + 0.5)
                c.text(bx, tw[1] + 16, name, 28, "b", col, "mm", track=2, label="branch " + name)
                for k, g in enumerate(glyphs):
                    ny = tw[1] + 48 + k * step
                    state = "learned" if k < learned else ("open" if k == learned else "locked")
                    if k > 0:
                        c.d.line((bx * S, (ny - step + s) * S, bx * S, ny * S), fill=col if state != "locked" else (84, 80, 90), width=int(5 * S))
                    n = node.resize((int(s * S), int(s * S)), Image.LANCZOS)
                    if state != "locked":
                        n = tint(n, col, 0.55 if state == "learned" else 0.3)
                    if state == "learned":
                        gl = Image.new("RGBA", (int(s * 2 * S), int(s * 2 * S)))
                        ImageDraw.Draw(gl).ellipse((s * 0.5 * S, s * 0.5 * S, s * 1.5 * S, s * 1.5 * S), fill=col + (100,))
                        c.paste(gl.filter(ImageFilter.GaussianBlur(s * 0.25 * S)), bx - s, ny - s / 2)
                    c.paste(n, bx - s / 2, ny, 1.0 if state != "locked" else 0.5)
                    c.reg((bx - s / 2, ny, bx + s / 2, ny + s), f"node {name} {k}")
                    c.glyph(bx, ny + s / 2, g, int(s * 0.34), BONE if state != "locked" else FAINT, label="node glyph")
                    if state == "open":
                        c.d.ellipse(((bx + s * 0.32) * S, (ny + 2) * S, (bx + s * 0.32 + 18) * S, (ny + 20) * S), fill=GOLD)
        di = c.card(tw[2] + 34, top + 8, x1 - tw[2] - 34, 600, (206, 64, 64), 0.22, "skill detail")
        with c.scope("skill detail", di):
            c.text(di[0], di[1] + 6, "BODY  ·  TIER 4", 16, "b", (226, 96, 96), track=1, label="tier")
            c.text(di[0], di[1] + 36, "Second Wind", 30, "b", BONE, label="skill name")
            c.divider(di[0], di[2], di[1] + 104, "✦", label="skill divider")
            for i, line in enumerate(["Once per fight, falling under", "25% health restores 15", "posture and grants 2s of", "+20% move speed."]):
                c.text(di[0], di[1] + 132 + i * 30, line, 18, "r", DIM, label=f"desc {i}")
            c.text(di[0], di[1] + 270, "Requires  Iron Skin", 18, "i", FAINT, label="req")
            c.text(di[0], di[1] + 304, "Cost  1 point", 20, "b", GOLD, label="cost")
            c.button(di[0], di[3] - 68, di[2] - di[0], 64, "LEARN")
        c.footer(inner, [("K", "Close"), ("Click", "Select"), ("R", "Respec (¥ 500)")])
    c.save()


if __name__ == "__main__":
    only = sys.argv[2:] if len(sys.argv) > 2 else None
    failed = []
    for fn in (party, inventory, notices, auction, store, skilltree):
        if only and fn.__name__ not in only:
            continue
        try:
            fn()
        except LayoutError as e:
            failed.append(str(e))
    if failed:
        print("LAYOUT PROBLEMS:\n" + "\n".join(failed))
        sys.exit(1)
    print("all screens pass the layout check")
