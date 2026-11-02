"""Nightmare Highschool UI mock-ups (for approval, not in the game): composed from the PBR UI kit2 pieces
(art/ui/kit2/out) and the PBR school crest (art/logo/out/nh_logo_pbr.png) over a daytime game backdrop.

usage: python art/ui/kit2/mockups.py [backdrop.jpg]   -> art/ui/kit2/mockups/*.png (1920x1080)
Screens: party, inventory, notices, auction, store, skilltree.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "out")
OUT = os.path.join(HERE, "mockups")
os.makedirs(OUT, exist_ok=True)
CREST = os.path.join(HERE, "..", "..", "logo", "out", "nh_logo_pbr.png")
BG = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/mock_bg.jpg"
W, H = 1920, 1080

FONTS = "C:/Windows/Fonts/"
def F(size, kind="r"):
    name = {"r": "georgia.ttf", "b": "georgiab.ttf", "i": "georgiai.ttf", "bi": "georgiaz.ttf", "sym": "seguisym.ttf"}[kind]
    return ImageFont.truetype(FONTS + name, size)

BONE = (232, 222, 200)
DIM = (160, 148, 132)
FAINT = (110, 100, 92)
GOLD = (214, 172, 92)
CRIMSON = (196, 36, 48)
RAR = {"Common": (170, 168, 160), "Uncommon": (102, 176, 112), "Rare": (86, 146, 222), "Epic": (168, 102, 222),
       "Legendary": (232, 170, 64), "Mythic": (222, 54, 64)}
RACE = {"Vampire": (210, 48, 60), "Human": (214, 180, 110), "Werewolf": (210, 130, 60), "Ghoul": (130, 170, 120),
        "Wraith": (150, 170, 220), "Priest": (240, 220, 150)}

_cache = {}
def piece(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(KIT, name + ".png")).convert("RGBA")
    return _cache[name]


def nine(img, w, h, m):
    """nine-slice: keep m-pixel corners, stretch edges and centre."""
    iw, ih = img.size
    out = Image.new("RGBA", (w, h))
    xs = [(0, m, 0, m), (m, iw - m, m, w - m), (iw - m, iw, w - m, w)]
    ys = [(0, m, 0, m), (m, ih - m, m, h - m), (ih - m, ih, h - m, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if dx1 <= dx0 or dy1 <= dy0:
                continue
            out.paste(img.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS), (dx0, dy0))
    return out


def hnine(img, w, h, m):
    """scale to height h, then stretch only the middle horizontally (keeps the end caps and rivets round)."""
    sc = h / img.height
    im2 = img.resize((max(1, int(img.width * sc)), h), Image.LANCZOS)
    mm = max(1, int(m * sc))
    out = Image.new("RGBA", (w, h))
    out.paste(im2.crop((0, 0, mm, h)), (0, 0))
    out.paste(im2.crop((im2.width - mm, 0, im2.width, h)), (w - mm, 0))
    out.paste(im2.crop((mm, 0, im2.width - mm, h)).resize((max(1, w - 2 * mm), h), Image.LANCZOS), (mm, 0))
    return out


def tint(img, col, amt=0.55):
    """push a neutral piece toward a colour (rarity / branch), keeping its shading."""
    r, g, b, a = img.split()
    gray = Image.merge("RGB", (r, g, b)).convert("L")
    col_img = Image.new("RGB", img.size, col)
    shaded = Image.composite(col_img, Image.new("RGB", img.size, (0, 0, 0)), gray).convert("RGB")
    mixed = Image.blend(Image.merge("RGB", (r, g, b)), Image.eval(shaded, lambda v: min(255, int(v * 1.6))), amt)
    return Image.merge("RGBA", (*mixed.split(), a))


def backdrop(dim=0.55, blur=6):
    bg = Image.open(BG).convert("RGB")
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(blur))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (8, 5, 10)), dim)
    # vignette
    v = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(v)
    for i in range(40):
        dv.rectangle((i * 12, i * 7, W - i * 12, H - i * 7), fill=int(i * 6.3))
    v = v.filter(ImageFilter.GaussianBlur(80))
    bg = Image.composite(bg, Image.new("RGB", (W, H), (0, 0, 0)), v)
    return bg.convert("RGBA")


class Canvas:
    def __init__(self, dim=0.55):
        self.im = backdrop(dim)
        self.d = ImageDraw.Draw(self.im)

    def paste(self, img, xy, alpha=1.0):
        if alpha < 1:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        self.im.alpha_composite(img, (int(xy[0]), int(xy[1])))

    def text(self, xy, s, size=24, kind="r", fill=BONE, anchor="la", shadow=True, spacing=0):
        f = F(size, kind)
        if spacing:
            s = (" " * spacing).join(s) if spacing > 0 else s
        if shadow:
            self.d.text((xy[0] + 2, xy[1] + 2), s, font=f, fill=(0, 0, 0, 200), anchor=anchor)
        self.d.text(xy, s, font=f, fill=fill, anchor=anchor)

    def glyph(self, xy, ch, size, fill=BONE, anchor="mm"):
        self.d.text((xy[0] + 2, xy[1] + 2), ch, font=F(size, "sym"), fill=(0, 0, 0, 180), anchor=anchor)
        self.d.text(xy, ch, font=F(size, "sym"), fill=fill, anchor=anchor)

    def panel(self, x, y, w, h):
        self.paste(nine(piece("panel"), w, h, 110), (x, y))

    def card(self, x, y, w, h, col=None, amt=0.45):
        c = nine(piece("card"), w, h, 70)
        self.paste(tint(c, col, amt) if col else c, (x, y))

    def row(self, x, y, w, h=92):
        self.paste(hnine(piece("row"), w, h, 70), (x, y))

    def slot(self, x, y, s, col=None):
        sl = piece("slot").resize((s, s), Image.LANCZOS)
        self.paste(tint(sl, col, 0.35) if col else sl, (x, y))

    def button(self, x, y, w, h, label, size=24, col=GOLD):
        self.paste(hnine(piece("button"), w, int(h * 1.25), 60), (x, y - int(h * 0.125)))
        self.text((x + w / 2, y + h / 2), label, size, "b", col, "mm")

    def bar(self, x, y, w, h, frac, col, track=(24, 14, 18)):
        self.d.rounded_rectangle((x - 2, y - 2, x + w + 2, y + h + 2), radius=h // 2 + 2, fill=(10, 8, 10))
        self.d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=track)
        if frac > 0:
            fw = max(h, int(w * frac))
            grad = Image.new("RGBA", (fw, h))
            gd = ImageDraw.Draw(grad)
            for i in range(h):
                t = i / max(1, h - 1)
                c = tuple(int(v * (1.25 - 0.55 * t)) for v in col)
                gd.line((0, i, fw, i), fill=tuple(min(255, v) for v in c) + (255,))
            m = Image.new("L", (fw, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, fw - 1, h - 1), radius=h // 2, fill=255)
            grad.putalpha(m)
            self.paste(grad, (x, y))

    def crest(self, x, y, s):
        c = Image.open(CREST).convert("RGBA")
        c = c.resize((s, int(s * c.height / c.width)), Image.LANCZOS)
        self.paste(c, (x, y))
        return c.height

    def title(self, x, y, s, sub=None):
        self.text((x, y), s, 44, "b", GOLD, spacing=1)
        if sub:
            self.text((x + 2, y + 56), sub, 20, "i", DIM)
        self.d.line((x, y + (88 if sub else 60), x + 420, y + (88 if sub else 60)), fill=CRIMSON, width=2)

    def save(self, name):
        p = os.path.join(OUT, name)
        self.im.convert("RGB").save(p, quality=92)
        print("[mock]", p)


# ------------------------------------------------------------------ screens

def party():
    c = Canvas()
    x, y, w, h = 150, 120, 900, 840
    c.panel(x, y, w, h)
    c.crest(x + 60, y + 70, 120)
    c.title(x + 200, y + 80, "STUDY GROUP", "Up to four students share EXP from every fight")
    c.text((x + w - 70, y + 92), "3 / 4", 30, "b", BONE, "ra")
    members = [("Rin Kurosawa", "Vampire", 22, 0.86, 0.55, True), ("Kaito Mori", "Werewolf", 18, 0.42, 0.9, False),
               ("You", "Human", 14, 1.0, 0.3, False)]
    ry = y + 210
    for name, race, lv, hp, post, lead in members:
        c.row(x + 60, ry, w - 120, 104)
        c.slot(x + 92, ry + 8, 88, RACE[race])
        c.glyph((x + 136, ry + 52), {"Vampire": "🦇", "Werewolf": "☾", "Human": "✝"}[race], 40, RACE[race])
        c.text((x + 200, ry + 18), name, 28, "b", BONE)
        if lead:
            c.glyph((x + 200 + F(28, "b").getlength(name) + 24, ry + 34), "♛", 26, GOLD)
        c.text((x + 200, ry + 56), race.upper() + "   ·   LV " + str(lv), 18, "b", RACE[race])
        c.text((x + 520, ry + 20), "HEALTH", 14, "b", DIM)
        c.bar(x + 520, ry + 40, 230, 14, hp, (196, 40, 52))
        c.text((x + 520, ry + 62), "POSTURE", 14, "b", DIM)
        c.bar(x + 520, ry + 80, 230, 10, post, (214, 172, 92))
        if name != "You":
            c.glyph((x + w - 100, ry + 52), "✚" if False else "⛓", 26, FAINT)
        ry += 112
    c.row(x + 60, ry, w - 120, 104)
    c.slot(x + 92, ry + 8, 88)
    c.glyph((x + 136, ry + 52), "✚", 34, FAINT)
    c.text((x + 200, ry + 36), "Invite a classmate…", 26, "i", FAINT)
    c.button(x + 70, y + h - 150, 250, 70, "INVITE")
    c.button(x + 340, y + h - 150, 250, 70, "LEAVE", col=(220, 120, 110))
    c.text((x + w - 80, y + h - 126), "Shared EXP  +10%", 22, "b", GOLD, "ra")
    # incoming invite toast
    tx, ty = 1180, 170
    c.card(tx, ty, 600, 330)
    c.slot(tx + 40, ty + 50, 92, RACE["Ghoul"])
    c.glyph((tx + 86, ty + 96), "💀", 42, RACE["Ghoul"])
    c.text((tx + 160, ty + 46), "GROUP INVITE", 18, "b", CRIMSON, spacing=1)
    c.text((tx + 160, ty + 76), "Sora Hayashi", 28, "b", BONE)
    c.text((tx + 160, ty + 112), "wants you in their Study Group", 20, "i", DIM)
    c.bar(tx + 40, ty + 166, 520, 8, 0.62, (214, 172, 92))
    c.button(tx + 60, ty + 210, 220, 64, "ACCEPT", 22)
    c.button(tx + 310, ty + 210, 220, 64, "DECLINE", 22, (220, 120, 110))
    c.save("party.jpg")


ITEMS = [("🎭", "Fox Mask", "Rare"), ("⚔", "Training Katana", "Common"), ("🎩", "Gravedigger Hat", "Uncommon"),
         ("💍", "Signet of Night", "Epic"), ("🗡", "Silver Letter Opener", "Rare"), ("⚗", "Blood Tonic", "Common"),
         ("📜", "Detention Slip", "Common"), ("🔮", "Scrying Marble", "Legendary"), ("🕯", "Vigil Candle", "Uncommon"),
         ("⛓", "Chain Belt", "Uncommon"), ("🗝", "Archive Key", "Epic"), ("👁", "Third Eye Pin", "Mythic"),
         ("⌛", "Hourglass Charm", "Rare"), ("☠", "Skull Ring", "Common"), ("✝", "Rosary", "Uncommon"),
         ("⚜", "Prefect Badge", "Rare"), ("🦇", "Bat Brooch", "Common"), ("❤", "Locket", "Epic")]


def inventory():
    c = Canvas()
    x, y, w, h = 160, 110, 1600, 860
    c.panel(x, y, w, h)
    c.crest(x + 60, y + 60, 110)
    c.title(x + 190, y + 70, "LOCKER", "Everything you carry. Gear stats are capped so nobody's broken")
    tabs = ["ALL", "GEAR", "WEAPONS", "TONICS", "QUEST"]
    for i, t in enumerate(tabs):
        c.button(x + 80 + i * 166, y + 205, 156, 56, t, 18, GOLD if i == 1 else DIM)
    gx, gy, s, gap = x + 80, y + 290, 104, 14
    sel = 0
    for i in range(28):
        col, row = i % 7, i // 7
        sx, sy = gx + col * (s + gap), gy + row * (s + gap)
        if i < len(ITEMS):
            g, n, r = ITEMS[i]
            c.slot(sx, sy, s, RAR[r])
            c.glyph((sx + s / 2, sy + s / 2 - 2), g, 46, RAR[r] if r != "Common" else BONE)
            c.d.polygon([(sx + s - 30, sy + 12), (sx + s - 14, sy + 12), (sx + s - 14, sy + 28)], fill=RAR[r])
            if i == 5:
                c.text((sx + s - 14, sy + s - 14), "x3", 18, "b", BONE, "rs")
            if i == sel:
                c.d.rounded_rectangle((sx - 4, sy - 4, sx + s + 4, sy + s + 4), radius=10, outline=GOLD, width=3)
        else:
            c.slot(sx, sy, s)
    c.text((gx, y + h - 100), "¥ 1,240", 30, "b", GOLD)
    c.text((gx + 7 * (s + gap) - gap, y + h - 96), "18 / 28 slots", 24, "r", DIM, "ra")
    # detail card
    dx, dy, dw, dh = x + 1010, y + 200, 510, 600
    c.card(dx, dy, dw, dh, RAR["Rare"], 0.3)
    c.slot(dx + 40, dy + 50, 150, RAR["Rare"])
    c.glyph((dx + 115, dy + 125), "🎭", 70, RAR["Rare"])
    c.text((dx + 215, dy + 60), "RARE  ·  FACE", 18, "b", RAR["Rare"], spacing=1)
    c.text((dx + 215, dy + 92), "Fox Mask", 40, "b", BONE)
    c.text((dx + 215, dy + 146), "Found in a gear chest", 20, "i", DIM)
    c.d.line((dx + 40, dy + 230, dx + dw - 40, dy + 230), fill=(90, 40, 44), width=2)
    stats = [("Night Power", "+1.6%", (130, 200, 130)), ("Stealth", "−0.8%", (220, 110, 100)), ("Combat EXP", "+2.0%", (130, 200, 130))]
    for i, (k, v, col) in enumerate(stats):
        c.text((dx + 50, dy + 260 + i * 46), k, 24, "r", BONE)
        c.text((dx + dw - 50, dy + 260 + i * 46), v, 24, "b", col, "ra")
    c.text((dx + 50, dy + 410), "\u201cIt grins whether you do or not.\u201d", 20, "i", DIM)
    c.button(dx + 40, dy + dh - 120, 210, 72, "EQUIP")
    c.button(dx + 270, dy + dh - 120, 200, 72, "DROP", col=(220, 120, 110))
    c.save("inventory.jpg")


def notices():
    c = Canvas(dim=0.35)
    # top banner (world event)
    c.row(360, 60, 1200, 120)
    c.text((960, 104), "THE BLOOD MOON RISES", 40, "b", (240, 90, 90), "mm", spacing=1)
    c.text((960, 146), "Supernatural powers +25% until dawn", 20, "i", BONE, "mm")
    # loot reveal, centre
    lx, ly, lw, lh = 660, 260, 600, 560
    glow = Image.new("RGBA", (lw + 400, lh + 400), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((120, 120, lw + 280, lh + 280), fill=RAR["Legendary"] + (150,))
    c.paste(glow.filter(ImageFilter.GaussianBlur(90)), (lx - 200, ly - 200))
    c.card(lx, ly, lw, lh, RAR["Legendary"], 0.45)
    c.text((lx + lw / 2, ly + 60), "GEAR CHEST", 20, "b", DIM, "mm", spacing=1)
    c.slot(lx + lw / 2 - 110, ly + 100, 220, RAR["Legendary"])
    c.glyph((lx + lw / 2, ly + 208), "⌛", 110, RAR["Legendary"])
    c.text((lx + lw / 2, ly + 360), "LEGENDARY", 26, "b", RAR["Legendary"], "mm", spacing=2)
    c.text((lx + lw / 2, ly + 402), "Crimson Pocket Watch", 38, "b", BONE, "mm")
    c.text((lx + lw / 2, ly + 448), "+3.0% Night Power   ·   +1.5% All EXP", 22, "r", (150, 210, 150), "mm")
    c.button(lx + lw / 2 - 130, ly + lh - 112, 260, 64, "TAKE IT")
    # stacked toasts, right
    tx = 1380
    toasts = [("GROUP INVITE", "Sora Hayashi wants you in their group", "💀", RACE["Ghoul"], True),
              ("TRADE REQUEST", "Kaito Mori offers a trade", "⚖", GOLD, True),
              ("DETENTION", "A Watcher saw you fight in the hall", "👁", CRIMSON, False)]
    for i, (k, msg, g, col, act) in enumerate(toasts):
        ty = 220 + i * 200
        c.card(tx, ty, 480, 185)
        c.slot(tx + 28, ty + 40, 84, col)
        c.glyph((tx + 70, ty + 82), g if g != "⚖" else "⚜", 38, col)
        c.text((tx + 130, ty + 38), k, 16, "b", col, spacing=1)
        c.text((tx + 130, ty + 64), msg, 18, "r", BONE)
        if act:
            c.button(tx + 130, ty + 104, 150, 46, "ACCEPT", 17)
            c.button(tx + 292, ty + 104, 150, 46, "DECLINE", 17, (220, 120, 110))
        else:
            c.text((tx + 130, ty + 108), "Report to Room 104 after class", 17, "i", DIM)
    # reward ticker, bottom left
    for i, (s, col) in enumerate([("+85 EXP  ·  Combat", (150, 210, 150)), ("¥ +30", GOLD), ("Gang Leader defeated", BONE)]):
        c.text((120, 820 + i * 44), s, 28, "b", col)
    c.save("notices.jpg")


def auction():
    c = Canvas()
    x, y, w, h = 110, 90, 1700, 900
    c.panel(x, y, w, h)
    c.crest(x + 60, y + 55, 110)
    c.title(x + 190, y + 65, "THE UNDERCROFT", "Student auction house. Bids are final; 5% goes to the Bursar")
    # search + filters
    c.d.rounded_rectangle((x + 80, y + 197, x + 640, y + 257), radius=10, fill=(12, 9, 12), outline=(120, 92, 56), width=2)
    c.d.rounded_rectangle((x + 84, y + 201, x + 636, y + 253), radius=8, outline=(40, 30, 32), width=2)
    c.text((x + 110, y + 227), "Search items…", 22, "i", FAINT, "lm")
    c.glyph((x + 610, y + 227), "👁", 24, DIM)
    for i, r in enumerate(["Rare+", "Epic+", "Legendary"]):
        c.button(x + 670 + i * 170, y + 195, 160, 64, r, 18, RAR[r.rstrip("+")])
    c.button(x + 1190, y + 195, 220, 64, "ENDING SOON", 18, BONE)
    # header
    cols = [("ITEM", x + 210), ("SELLER", x + 720), ("ENDS", x + 960), ("TOP BID", x + 1130), ("BUYOUT", x + 1300)]
    for k, cx in cols:
        c.text((cx, y + 290), k, 16, "b", DIM, spacing=1)
    rows = [("🔮", "Scrying Marble", "Legendary", "Rin K.", "12m", "¥ 8,400", "¥ 12,000"),
            ("💍", "Signet of Night", "Epic", "Kaito M.", "41m", "¥ 3,150", "¥ 4,500"),
            ("🗝", "Archive Key", "Epic", "Mina S.", "1h 20m", "¥ 2,900", "—"),
            ("🎭", "Fox Mask", "Rare", "Sora H.", "2h 05m", "¥ 980", "¥ 1,400"),
            ("⌛", "Hourglass Charm", "Rare", "Haru T.", "3h", "¥ 760", "¥ 1,100")]
    for i, (g, n, r, s, t, bid, buy) in enumerate(rows):
        ry = y + 320 + i * 92
        c.row(x + 80, ry, 1540, 84)
        c.slot(x + 108, ry + 6, 72, RAR[r])
        c.glyph((x + 144, ry + 42), g, 32, RAR[r])
        c.text((x + 210, ry + 18), n, 24, "b", BONE)
        c.text((x + 210, ry + 50), r.upper(), 14, "b", RAR[r], spacing=1)
        c.text((x + 720, ry + 30), s, 20, "r", BONE)
        c.text((x + 960, ry + 30), t, 20, "b", (230, 120, 100) if i < 2 else BONE)
        c.text((x + 1130, ry + 30), bid, 22, "b", GOLD)
        c.text((x + 1300, ry + 30), buy, 22, "r", BONE)
        c.button(x + 1440, ry + 12, 150, 60, "BID", 20)
    c.button(x + 90, y + h - 140, 300, 70, "POST LISTING")
    c.text((x + w - 90, y + h - 116), "Your listings: 2 active   ·   ¥ 1,240", 22, "r", DIM, "ra")
    c.save("auction.jpg")


def store():
    c = Canvas()
    x, y, w, h = 130, 80, 1660, 920
    c.panel(x, y, w, h)
    c.crest(x + 60, y + 50, 120)
    c.title(x + 200, y + 65, "THE COMMISSARY", "Support the school. Nothing here makes you unbeatable")
    for i, t in enumerate(["FEATURED", "PASSES", "YEN", "COSMETICS"]):
        c.button(x + 80 + i * 210, y + 200, 200, 60, t, 19, GOLD if i == 0 else DIM)
    offers = [("⚜", "Yen Pouch", "¥ 5,000", "R$ 99", "Common", None),
              ("💰", "Yen Chest", "¥ 30,000  +10% bonus", "R$ 449", "Rare", "BEST VALUE"),
              ("🔮", "Lineage Reroll  x3", "Spin your bloodline again", "R$ 149", "Epic", None),
              ("📜", "Extra Character Slot", "A whole new student file", "R$ 199", "Uncommon", None),
              ("♛", "Prefect Pass", "+10% EXP  ·  name colour  ·  daily ¥", "R$ 399", "Legendary", "POPULAR"),
              ("🦇", "Blood Moon Cape", "Cosmetic  ·  animated sway", "R$ 249", "Mythic", "NEW")]
    cw, ch, gap = 490, 262, 24
    for i, (g, n, sub, price, r, tag) in enumerate(offers):
        cx = x + 80 + (i % 3) * (cw + gap)
        cy = y + 290 + (i // 3) * (ch + gap)
        c.card(cx, cy, cw, ch, RAR[r], 0.35)
        c.slot(cx + 36, cy + 50, 130, RAR[r])
        c.glyph((cx + 101, cy + 115), g if g != "💰" else "⚜", 62, RAR[r])
        c.text((cx + 190, cy + 58), n, 28, "b", BONE)
        c.text((cx + 190, cy + 100), sub, 18, "i", DIM)
        if tag:
            c.text((cx + 190, cy + 140), tag, 16, "b", CRIMSON, spacing=1)
        c.button(cx + 190, cy + ch - 96, 240, 62, price, 24, GOLD)
    c.text((x + w - 90, y + 300 - 60), "Cosmetic or convenience only. Combat stats can't be bought.", 18, "i", FAINT, "ra")
    c.save("store.jpg")


def skilltree():
    c = Canvas()
    x, y, w, h = 120, 80, 1680, 920
    c.panel(x, y, w, h)
    c.crest(x + 60, y + 50, 110)
    c.title(x + 190, y + 60, "CURRICULUM", "Spend study points. Each branch caps at 10")
    c.text((x + w - 80, y + 80), "4 POINTS", 34, "b", GOLD, "ra")
    branches = [("BODY", (200, 60, 60), ["⚔", "❤", "⛨", "⚡", "✦"]), ("MIND", (110, 130, 220), ["👁", "📜", "⌛", "🔮", "✦"]),
                ("BLOOD", (170, 30, 60), ["🦇", "☾", "⛧", "☠", "✦"])]
    node = piece("node")
    for bi, (name, col, glyphs) in enumerate(branches):
        bx = x + 230 + bi * 380
        c.text((bx, y + 200), name, 30, "b", col, "mm", spacing=2)
        prev = None
        for k, g in enumerate(glyphs):
            ny = y + 245 + k * 112
            state = "learned" if k < [3, 1, 2][bi] else ("open" if k == [3, 1, 2][bi] else "locked")
            if prev:
                c.d.line((bx, prev + 50, bx, ny + 10), fill=(90, 86, 96) if state == "locked" else col, width=5)
            s = 100
            n = node.resize((s, s), Image.LANCZOS)
            if state != "locked":
                n = tint(n, col, 0.55 if state == "learned" else 0.3)
            c.paste(n, (bx - s / 2, ny), 1.0 if state != "locked" else 0.55)
            if state == "learned":
                glow = Image.new("RGBA", (200, 200)); ImageDraw.Draw(glow).ellipse((40, 40, 160, 160), fill=col + (90,))
                c.paste(glow.filter(ImageFilter.GaussianBlur(25)), (bx - 100, ny - 45))
            c.glyph((bx, ny + s / 2), g, 36, BONE if state != "locked" else FAINT)
            if state == "open":
                c.d.ellipse((bx + 34, ny + 4, bx + 54, ny + 24), fill=GOLD)
            prev = ny + 60
    # detail
    dx, dy = x + 1220, y + 200
    c.card(dx, dy, 400, 560, (200, 60, 60), 0.25)
    c.text((dx + 40, dy + 50), "BODY  ·  TIER 4", 16, "b", (220, 90, 90), spacing=1)
    c.text((dx + 40, dy + 80), "Second Wind", 34, "b", BONE)
    for i, line in enumerate(["Once per fight, dropping under", "25% health restores 15 posture", "and grants 2s of +20% speed."]):
        c.text((dx + 40, dy + 150 + i * 32), line, 20, "r", DIM)
    c.text((dx + 40, dy + 280), "Requires  Iron Skin", 18, "i", FAINT)
    c.text((dx + 40, dy + 312), "Cost  1 point", 20, "b", GOLD)
    c.button(dx + 40, dy + 440, 320, 76, "LEARN")
    c.save("skilltree.jpg")


if __name__ == "__main__":
    for fn in (party, inventory, notices, auction, store, skilltree):
        fn()
