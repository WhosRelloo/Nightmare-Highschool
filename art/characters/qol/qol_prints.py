"""Printed art for the QOL items kit (system Python + PIL): the paper and dial faces that get baked into each item's atlas.

python qol_prints.py [--out E:/NH-Work/qol/prints]

  map_print.png        the folding campus map's inside (3 panels, 2400 x 1600): an inked plan of the campus
  map_cover.png        its folded cover (800 x 1600)
  timetable_print.png  the class timetable card (1400 x 900), the real bell times from Config.SchoolSchedule
  compass_dial.png     the pocket compass's bone dial (1024 round)
  thermos_label.png    the flask's wrap label (1600 x 520)
  tin_lid.png          the biscuit tin's lid (1024 round)  tin_band.png  its side band (2048 x 256)
  book_cover.png       the library book's cover plate (700 x 900), book_spine.png (220 x 900)
  library_card.png     the borrowing card in its pocket (600 x 900)
  key_tag.png          the bone key tag (400 x 600)
All names, places and brands are invented (the game's own places). No blood, no real logos.
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

argv = sys.argv[1:]
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/qol/prints"
os.makedirs(OUT, exist_ok=True)
F = "C:/Windows/Fonts/"
INK = (34, 26, 24)
INK_SOFT = (70, 56, 48)
CRIMSON = (96, 14, 26)        # #600E1A
GILT = (196, 154, 78)
R = random.Random(7)


def font(name, size):
    return ImageFont.truetype(F + name, size)


SERIF, SERIF_B, SERIF_I, SERIF_BI = "georgia.ttf", "georgiab.ttf", "georgiai.ttf", "georgiaz.ttf"
TIMES_B = "timesbd.ttf"


def paper(w, h, base=(226, 212, 178), grain=10, stains=3, edge=0.35, seed=1):
    """aged paper: fibre noise, a few tea-brown stains (never red), darker edges"""
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), base)
    noise = Image.effect_noise((w, h), grain * 6).convert("L")
    noise = noise.filter(ImageFilter.GaussianBlur(0.8))
    im = Image.composite(Image.new("RGB", (w, h), tuple(int(c * 0.93) for c in base)), im, noise.point(lambda v: int(v * 0.35)))
    big = Image.effect_noise((w // 8, h // 8), 60).convert("L").resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    im = Image.composite(Image.new("RGB", (w, h), tuple(int(c * 0.88) for c in base)), im, big.point(lambda v: int(max(0, v - 110) * 0.9)))
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(stains):
        cx, cy, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(min(w, h) // 14, min(w, h) // 6)
        for k in range(6):
            rr = r * (1 - k * 0.12)
            d.ellipse((cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8), outline=(120, 86, 46, 26), width=max(2, r // 30))
        d.ellipse((cx - r * 0.8, cy - r * 0.6, cx + r * 0.8, cy + r * 0.6), fill=(150, 112, 62, 14))
    # vignette edges
    vg = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vg)
    m = int(min(w, h) * 0.06)
    vd.rectangle((m, m, w - m, h - m), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(m * 0.9))
    dark = Image.new("RGB", (w, h), tuple(int(c * (1 - edge)) for c in base))
    im = Image.composite(im, dark, vg)
    return im


def text_c(d, xy, s, f, fill, anchor="mm", spacing=0):
    if spacing:
        # letter-spaced caps
        total = sum(d.textlength(ch, font=f) for ch in s) + spacing * (len(s) - 1)
        x = xy[0] - total / 2 if anchor[0] == "m" else xy[0]
        for ch in s:
            d.text((x, xy[1]), ch, font=f, fill=fill, anchor="l" + anchor[1])
            x += d.textlength(ch, font=f) + spacing
        return
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def hatch(d, box, step=10, fill=INK_SOFT + (120,), w=2, ang=45):
    x0, y0, x1, y1 = box
    L = (x1 - x0) + (y1 - y0)
    for k in range(-int(L), int(L), step):
        if ang == 45:
            a, b = (x0 + k, y0), (x0 + k + (y1 - y0), y1)
        else:
            a, b = (x0 + k, y1), (x0 + k + (y1 - y0), y0)
        d.line([a, b], fill=fill, width=w)


def clip_box(img, box, fn):
    """draw with fn(draw) clipped to box"""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    img.alpha_composite(layer)


def rose(d, cx, cy, r, ink=INK, accent=CRIMSON, labels=True, f=None):
    for k in range(16):
        a = k * math.pi / 8
        L = r if k % 4 == 0 else (r * 0.62 if k % 2 == 0 else r * 0.38)
        wdt = r * (0.16 if k % 4 == 0 else 0.11)
        tip = (cx + L * math.sin(a), cy - L * math.cos(a))
        l = (cx + wdt * math.sin(a - math.pi / 2), cy - wdt * math.cos(a - math.pi / 2))
        rr = (cx + wdt * math.sin(a + math.pi / 2), cy - wdt * math.cos(a + math.pi / 2))
        col = accent if k == 0 else ink
        d.polygon([tip, l, (cx, cy)], fill=col)
        d.polygon([tip, rr, (cx, cy)], fill=(*[min(255, int(c * 1.0 + 150)) for c in col[:3]], 255) if k % 4 == 0 else (225, 210, 178), outline=col)
    d.ellipse((cx - r * 0.09, cy - r * 0.09, cx + r * 0.09, cy + r * 0.09), fill=GILT, outline=ink, width=2)
    d.ellipse((cx - r * 1.05, cy - r * 1.05, cx + r * 1.05, cy + r * 1.05), outline=ink, width=3)
    if labels and f:
        for s, a in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
            ar = math.radians(a)
            d.text((cx + r * 1.22 * math.sin(ar), cy - r * 1.22 * math.cos(ar)), s, font=f, fill=accent if s == "N" else ink, anchor="mm")


def crest(d, cx, cy, s, ink=INK, fill=CRIMSON, gilt=GILT):
    """the invented school crest: a pointed shield, a crescent over a candle, a key across"""
    pts = [(cx - s, cy - s * 1.05), (cx + s, cy - s * 1.05), (cx + s, cy + s * 0.15)]
    for k in range(13):
        t = k / 12
        pts.append((cx + s * (1 - t) * math.cos(t * math.pi / 2) ** 0.6, cy + s * 0.15 + s * 1.05 * math.sin(t * math.pi / 2)))
    pts += [(cx - x + cx, y) for x, y in reversed(pts[3:])]
    pts = [(x if i < 3 else x, y) for i, (x, y) in enumerate(pts)]
    left = [(2 * cx - x, y) for x, y in pts[3:16]]
    shield = pts[:3] + pts[3:16] + list(reversed(left))
    d.polygon(shield, fill=fill, outline=ink)
    d.line(shield + [shield[0]], fill=gilt, width=max(2, int(s * 0.06)))
    # candle + flame
    d.rectangle((cx - s * 0.12, cy - s * 0.1, cx + s * 0.12, cy + s * 0.6), fill=(232, 220, 190))
    d.ellipse((cx - s * 0.1, cy - s * 0.42, cx + s * 0.1, cy - s * 0.12), fill=gilt)
    # crescent
    d.ellipse((cx - s * 0.55, cy - s * 0.95, cx - s * 0.05, cy - s * 0.45), fill=gilt)
    d.ellipse((cx - s * 0.45, cy - s * 1.0, cx + s * 0.02, cy - s * 0.52), fill=fill)
    # key across
    d.line((cx - s * 0.7, cy + s * 0.35, cx + s * 0.6, cy + s * 0.35), fill=gilt, width=max(2, int(s * 0.08)))
    d.ellipse((cx + s * 0.5, cy + s * 0.22, cx + s * 0.78, cy + s * 0.5), outline=gilt, width=max(2, int(s * 0.07)))
    d.rectangle((cx - s * 0.7, cy + s * 0.35, cx - s * 0.6, cy + s * 0.55), fill=gilt)
    d.rectangle((cx - s * 0.52, cy + s * 0.35, cx - s * 0.44, cy + s * 0.5), fill=gilt)


# ---------------------------------------------------------------- the campus map
def campus_map():
    W, H = 2400, 1600
    im = paper(W, H, base=(228, 214, 180), stains=4, seed=11).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    # fold creases (three panels, one horizontal fold)
    for x in (W // 3, 2 * W // 3):
        d.line((x, 0, x, H), fill=(150, 128, 92, 90), width=5)
        d.line((x + 4, 0, x + 4, H), fill=(255, 248, 230, 70), width=3)
    d.line((0, H // 2, W, H // 2), fill=(150, 128, 92, 70), width=4)
    d.line((0, H // 2 + 4, W, H // 2 + 4), fill=(255, 248, 230, 60), width=2)
    # border
    d.rectangle((40, 40, W - 40, H - 40), outline=INK, width=6)
    d.rectangle((58, 58, W - 58, H - 58), outline=INK, width=2)
    for x, y in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
        d.rectangle((x - 22, y - 22, x + 22, y + 22), fill=CRIMSON, outline=INK, width=3)
    # title cartouche
    fT = font(TIMES_B, 70); fS = font(SERIF_I, 38)
    d.rectangle((W / 2 - 560, 82, W / 2 + 560, 232), fill=(214, 196, 156, 255), outline=INK, width=4)
    text_c(d, (W / 2, 138), "NIGHTMARE HIGH", fT, INK, spacing=14)
    text_c(d, (W / 2, 200), "Campus & Grounds  ·  for the use of students", fS, INK_SOFT)
    crest(d, W / 2 - 640, 158, 62)
    crest(d, W / 2 + 640, 158, 62)
    fL = font(SERIF_B, 34); fl = font(SERIF, 26); fI = font(SERIF_I, 26)

    def bldg(box, name, sub=None, fill=(196, 176, 140, 255), hatch_it=True, red=False):
        x0, y0, x1, y1 = box
        d.rectangle((x0 + 10, y0 + 10, x1 + 10, y1 + 10), fill=(90, 70, 50, 70))
        d.rectangle(box, fill=fill, outline=INK, width=5)
        if hatch_it:
            clip_box(im, (x0 + 4, y0 + 4, x1 - 4, y1 - 4), lambda dd: hatch(dd, box, 14, (60, 44, 34, 60), 2))
        d2 = ImageDraw.Draw(im, "RGBA")
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        d2.rectangle((cx - d2.textlength(name, font=fL) / 2 - 14, cy - 26 - (16 if sub else 0), cx + d2.textlength(name, font=fL) / 2 + 14, cy + 22 - (16 if sub else 0)), fill=(232, 220, 190, 235))
        d2.text((cx, cy - (16 if sub else 0)), name, font=fL, fill=CRIMSON if red else INK, anchor="mm")
        if sub:
            d2.text((cx, cy + 26), sub, font=fI, fill=INK_SOFT, anchor="mm")

    # paths (gravel walks) first
    for pts, w in ((((300, 1000), (900, 1000), (1200, 900), (1700, 900), (2150, 820)), 34),
                   (((1200, 900), (1200, 1420)), 30), (((900, 1000), (760, 1420)), 26),
                   (((1700, 900), (1880, 560), (1900, 330)), 26), (((520, 760), (520, 1000)), 22)):
        d.line(pts, fill=(176, 156, 120, 255), width=w, joint="curve")
        d.line(pts, fill=(140, 118, 86, 255), width=3)
    # the main school
    bldg((760, 560, 1640, 840), "THE MAIN HALL", "Rooms 101 - 106 · Office")
    bldg((1640, 560, 1880, 840), "EAST WING", None)
    bldg((560, 600, 760, 800), "STAFF", "no students", red=True)
    bldg((900, 300, 1160, 520), "THE ARCHIVE", "Library", fill=(186, 168, 136, 255))
    bldg((1240, 330, 1460, 520), "CHAPEL", None)
    bldg((300, 300, 700, 520), "DORMITORY", "West Wing")
    bldg((1960, 330, 2280, 600), "GYMNASIUM", None)
    bldg((1040, 1060, 1360, 1220), "THE COMMONS", None, hatch_it=False, fill=(206, 190, 154, 255))
    bldg((1500, 1040, 1780, 1220), "INK STUDIO", None)
    bldg((130, 1080, 430, 1260), "BOILER YARD", "out of bounds", red=True)
    # fields (open ground: stippled)
    for box, name in (((1960, 1000, 2290, 1420), "NORTH FIELD"), ((1900, 80 + 600, 2290, 960), "PRACTICE LANES"),
                      ((480, 1280, 960, 1500), "WEST PITCH")):
        d.rectangle(box, fill=(196, 196, 150, 255), outline=INK, width=4)
        x0, y0, x1, y1 = box
        for _ in range(420):
            x, y = R.randint(x0 + 8, x1 - 8), R.randint(y0 + 8, y1 - 8)
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(90, 96, 60, 140))
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), name, font=fL, fill=INK, anchor="mm")
    # turf (ringed in crimson dashes)
    for box, name, sub in (((1450, 1270, 1840, 1480), "THE BACK LOT", "Delinquent turf"),
                           ((90, 560, 470, 760), "THE DEN", "Pack turf"),
                           ((1720, 230, 1940, 470), "CRIMSON PARLOR", None)):
        x0, y0, x1, y1 = box
        for k in range(0, int((x1 - x0) * 2 + (y1 - y0) * 2), 34):
            per = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
            # walk the perimeter
            t = k
            for a, b in zip(per, per[1:]):
                L = abs(b[0] - a[0]) + abs(b[1] - a[1])
                if t <= L:
                    px = a[0] + (b[0] - a[0]) * t / L; py = a[1] + (b[1] - a[1]) * t / L
                    qx = a[0] + (b[0] - a[0]) * min(L, t + 18) / L; qy = a[1] + (b[1] - a[1]) * min(L, t + 18) / L
                    d.line((px, py, qx, qy), fill=CRIMSON, width=6)
                    break
                t -= L
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 - (14 if sub else 0)), name, font=fL, fill=CRIMSON, anchor="mm")
        if sub:
            d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 24), sub, font=fI, fill=CRIMSON, anchor="mm")
    # the woods at the west edge: little inked trees
    for _ in range(90):
        x, y = R.randint(70, 260), R.randint(820, 1060) if R.random() < 0.5 else R.randint(1280, 1520)
        d.polygon([(x, y - 26), (x - 14, y + 8), (x + 14, y + 8)], fill=(60, 72, 52, 230), outline=INK)
        d.line((x, y + 8, x, y + 16), fill=INK, width=3)
    d.text((180, 1210 + 290), "WEST EDGE · wolves", font=fI, fill=CRIMSON, anchor="mm")
    # the ring (a circle by the commons)
    d.ellipse((1180 - 70, 1300 - 70, 1180 + 70, 1300 + 70), outline=INK, width=6)
    d.ellipse((1180 - 52, 1300 - 52, 1180 + 52, 1300 + 52), outline=INK_SOFT, width=2)
    d.text((1180, 1300), "THE RING", font=fl, fill=INK, anchor="mm")
    # the rose and the legend
    # the rose: north points to the right of the sheet (the pitch is west, the north field east)
    rl = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    rose(ImageDraw.Draw(rl), 180, 180, 78, labels=False)
    rl = rl.rotate(-90, resample=Image.BICUBIC)
    im.alpha_composite(rl, (2, 4))
    d = ImageDraw.Draw(im, "RGBA")
    fR = font(SERIF_B, 32)
    for s_, (dx, dy) in (("N", (1, 0)), ("E", (0, 1)), ("S", (-1, 0)), ("W", (0, -1))):
        d.text((182 + 98 * dx, 184 + 98 * dy), s_, font=fR, fill=CRIMSON if s_ == "N" else INK, anchor="mm")
    # "you are here" pin (printed, generic: at the commons)
    px, py = 1200, 980
    d.ellipse((px - 34, py - 34, px + 34, py + 34), outline=CRIMSON, width=6)
    d.ellipse((px - 12, py - 12, px + 12, py + 12), fill=CRIMSON)
    d.text((px + 50, py - 8), "you are here", font=font(SERIF_BI, 32), fill=CRIMSON, anchor="lm")
    # scale bar
    d.rectangle((560, 1530 - 2, 960, 1530 + 12), outline=INK, width=3)
    for k in range(4):
        if k % 2 == 0:
            d.rectangle((560 + k * 100, 1530 - 2, 660 + k * 100, 1542), fill=INK)
    d.text((760, 1508), "a hundred paces", font=fI, fill=INK_SOFT, anchor="mm")
    # a hand-written note and the rule
    d.text((2120, 160), "Curfew at nine.", font=font(SERIF_BI, 30), fill=INK_SOFT, anchor="mm")
    d.text((2120, 196), "Keep to the paths.", font=font(SERIF_BI, 30), fill=INK_SOFT, anchor="mm")
    im = im.convert("RGB").filter(ImageFilter.GaussianBlur(0.6))
    im.save(os.path.join(OUT, "map_print.png"))
    # the outside cover: crimson board with the crest and a gilt title
    cv = paper(800, 1600, base=(98, 18, 28), grain=6, stains=1, edge=0.45, seed=5).convert("RGBA")
    d = ImageDraw.Draw(cv, "RGBA")
    d.rectangle((40, 40, 760, 1560), outline=GILT, width=6)
    d.rectangle((60, 60, 740, 1540), outline=GILT, width=2)
    crest(d, 400, 560, 150, ink=(40, 20, 10), fill=(70, 10, 18), gilt=GILT)
    text_c(d, (400, 880), "CAMPUS", font(TIMES_B, 96), GILT, spacing=10)
    text_c(d, (400, 990), "MAP", font(TIMES_B, 96), GILT, spacing=10)
    text_c(d, (400, 1100), "Nightmare High", font(SERIF_I, 52), GILT)
    cv.convert("RGB").save(os.path.join(OUT, "map_cover.png"))


# ---------------------------------------------------------------- the timetable card
SCHEDULE = [("08:00", "Homeroom", "Room 101"), ("08:20", "Mathematics", "Room 102"), ("09:05", "Chemistry", "Room 103"),
            ("09:45", "Break", "the Commons"), ("10:00", "English", "Room 104"), ("10:45", "History", "Room 105"),
            ("11:25", "Lunch", "the Commons"), ("12:00", "Lessons end", "")]


def timetable():
    W, H = 1400, 900
    im = paper(W, H, base=(236, 226, 200), stains=1, edge=0.2, seed=3).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0, 0, W, 150), fill=CRIMSON)
    d.rectangle((0, 150, W, 160), fill=GILT)
    crest(d, 100, 78, 52, ink=(40, 20, 10), fill=(70, 10, 18))
    text_c(d, (W / 2 + 40, 60), "CLASS TIMETABLE", font(TIMES_B, 64), (240, 226, 196), spacing=8)
    text_c(d, (W / 2 + 40, 118), "Nightmare High  ·  Monday to Friday", font(SERIF_I, 34), (236, 210, 170))
    d.rectangle((40, 190, W - 40, H - 40), outline=INK, width=4)
    rows = len(SCHEDULE)
    top, bot = 250, H - 60
    rh = (bot - top) / rows
    d.text((80, 220), "BELL", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="lm")
    d.text((330, 220), "LESSON", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="lm")
    d.text((960, 220), "ROOM", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="lm")
    for i, (t, lesson, room) in enumerate(SCHEDULE):
        y = top + i * rh
        if i % 2 == 0:
            d.rectangle((44, y, W - 44, y + rh), fill=(214, 198, 160, 120))
        d.line((44, y, W - 44, y), fill=(120, 100, 80, 160), width=2)
        light = lesson in ("Break", "Lunch", "Lessons end")
        d.text((80, y + rh / 2), t, font=font(TIMES_B, 46), fill=CRIMSON if not light else INK_SOFT, anchor="lm")
        d.text((330, y + rh / 2), lesson, font=font(SERIF_B if not light else SERIF_I, 46), fill=INK if not light else INK_SOFT, anchor="lm")
        d.text((960, y + rh / 2), room, font=font(SERIF, 42), fill=INK, anchor="lm")
    d.line((300, 200, 300, H - 44), fill=(120, 100, 80, 160), width=2)
    d.line((930, 200, 930, H - 44), fill=(120, 100, 80, 160), width=2)
    im.convert("RGB").filter(ImageFilter.GaussianBlur(0.5)).save(os.path.join(OUT, "timetable_print.png"))


# ---------------------------------------------------------------- the compass dial
def compass_dial():
    S = 1024
    im = paper(S, S, base=(226, 214, 186), grain=6, stains=0, edge=0.25, seed=8).convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    c = S / 2
    for k in range(360):
        a = math.radians(k)
        L = 60 if k % 30 == 0 else (36 if k % 10 == 0 else (22 if k % 5 == 0 else 12))
        r0 = 470
        d.line((c + r0 * math.sin(a), c - r0 * math.cos(a), c + (r0 - L) * math.sin(a), c - (r0 - L) * math.cos(a)),
               fill=INK, width=5 if k % 30 == 0 else 2)
    d.ellipse((c - 482, c - 482, c + 482, c + 482), outline=INK, width=8)
    d.ellipse((c - 400, c - 400, c + 400, c + 400), outline=INK, width=3)
    fN = font(TIMES_B, 96)
    for s, a in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        ar = math.radians(a)
        d.text((c + 330 * math.sin(ar), c - 330 * math.cos(ar)), s, font=fN, fill=CRIMSON if s == "N" else INK, anchor="mm")
    f2 = font(SERIF, 34)
    for a in range(30, 360, 30):
        if a % 90:
            ar = math.radians(a)
            d.text((c + 360 * math.sin(ar), c - 360 * math.cos(ar)), str(a), font=f2, fill=INK_SOFT, anchor="mm")
    rose(d, c, c, 250, labels=False)
    d.text((c, c + 150), "NIGHTMARE HIGH", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="mm")
    im.convert("RGB").filter(ImageFilter.GaussianBlur(0.5)).save(os.path.join(OUT, "compass_dial.png"))


# ---------------------------------------------------------------- the flask label, the biscuit tin
def thermos_label():
    W, H = 1600, 520
    im = Image.new("RGBA", (W, H), (20, 18, 22, 255))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0, 40, W, H - 40), fill=CRIMSON)
    d.rectangle((0, 40, W, 56), fill=GILT); d.rectangle((0, H - 56, W, H - 40), fill=GILT)
    # front panel (centred on u = 0.25 so it faces out of the hand)
    cx = W * 0.25
    d.ellipse((cx - 230, 90, cx + 230, H - 90), fill=(236, 222, 190), outline=GILT, width=8)
    text_c(d, (cx, 175), "THE WICK", font(TIMES_B, 54), INK, spacing=6)
    text_c(d, (cx, 232), "&", font(SERIF_I, 40), CRIMSON)
    text_c(d, (cx, 290), "KETTLE", font(TIMES_B, 54), INK, spacing=6)
    text_c(d, (cx, 350), "hot all night", font(SERIF_I, 34), INK_SOFT)
    # a steaming cup motif on the back half
    bx = W * 0.75
    d.rectangle((bx - 70, 200, bx + 70, 320), fill=(236, 222, 190))
    d.ellipse((bx + 50, 225, bx + 110, 290), outline=(236, 222, 190), width=14)
    d.rectangle((bx - 110, 320, bx + 110, 334), fill=(236, 222, 190))
    for k in (-40, 0, 40):
        d.arc((bx + k - 24, 110, bx + k + 24, 190), 200, 340, fill=(236, 222, 190), width=8)
    im.convert("RGB").save(os.path.join(OUT, "thermos_label.png"))


def tin():
    S = 1024
    im = Image.new("RGBA", (S, S), (90, 12, 24, 255))
    noise = Image.effect_noise((S, S), 20).convert("L").filter(ImageFilter.GaussianBlur(1))
    im = Image.composite(Image.new("RGBA", (S, S), (78, 10, 20, 255)), im, noise.point(lambda v: int(v * 0.4)))
    d = ImageDraw.Draw(im, "RGBA")
    c = S / 2
    d.ellipse((24, 24, S - 24, S - 24), outline=GILT, width=18)
    d.ellipse((70, 70, S - 70, S - 70), outline=GILT, width=5)
    for k in range(24):     # gothic scallop border
        a = 2 * math.pi * k / 24
        x, y = c + 400 * math.cos(a), c + 400 * math.sin(a)
        d.ellipse((x - 26, y - 26, x + 26, y + 26), outline=GILT, width=5)
    d.ellipse((c - 300, c - 300, c + 300, c + 300), fill=(26, 18, 22, 255), outline=GILT, width=10)
    text_c(d, (c, c - 140), "MORROW & VANE", font(TIMES_B, 44), GILT, spacing=3)
    text_c(d, (c, c - 40), "Midnight", font(SERIF_BI, 92), (236, 222, 190))
    text_c(d, (c, c + 60), "Biscuits", font(SERIF_BI, 92), (236, 222, 190))
    text_c(d, (c, c + 170), "baked by candlelight", font(SERIF_I, 38), GILT)
    # a small crescent moon at the top of the medallion
    d.ellipse((c - 40, c - 268, c + 40, c - 188), fill=GILT)
    d.ellipse((c - 22, c - 278, c + 52, c - 200), fill=(26, 18, 22, 255))
    im.convert("RGB").save(os.path.join(OUT, "tin_lid.png"))
    W, H = 2048, 256
    b = Image.new("RGBA", (W, H), (90, 12, 24, 255))
    d = ImageDraw.Draw(b, "RGBA")
    d.rectangle((0, 18, W, 34), fill=GILT); d.rectangle((0, H - 34, W, H - 18), fill=GILT)
    for k in range(0, W, 128):     # pointed arches
        d.arc((k + 10, 60, k + 118, 260), 180, 360, fill=GILT, width=6)
        d.line((k + 64, 60 + 4, k + 64, 200), fill=GILT, width=3)
    for k in range(4):
        text_c(d, (W * (k + 0.5) / 4, 160), "MIDNIGHT BISCUITS", font(TIMES_B, 40), (236, 222, 190), spacing=3)
    b.convert("RGB").save(os.path.join(OUT, "tin_band.png"))


# ---------------------------------------------------------------- the library book and card, the key tag
def book():
    W, H = 700, 900
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    # cover plate: a bone label in a gilt frame with the Archive's stamp
    d.rectangle((0, 0, W, H), fill=(30, 40, 58, 255))
    cl = paper(W, H, base=(32, 44, 64), grain=8, stains=0, edge=0.3, seed=21).convert("RGBA")
    im.alpha_composite(cl)
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((40, 40, W - 40, H - 40), outline=GILT, width=6)
    d.rectangle((140, 190, W - 140, 560), fill=(226, 212, 180), outline=GILT, width=6)
    text_c(d, (W / 2, 260), "A HISTORY", font(TIMES_B, 46), INK, spacing=3)
    text_c(d, (W / 2, 320), "of the", font(SERIF_I, 36), INK_SOFT)
    text_c(d, (W / 2, 380), "NIGHT", font(TIMES_B, 52), INK, spacing=4)
    text_c(d, (W / 2, 440), "SCHOOLS", font(TIMES_B, 52), INK, spacing=4)
    text_c(d, (W / 2, 510), "Vol. III", font(SERIF_I, 32), CRIMSON)
    d.ellipse((W / 2 - 110, 620, W / 2 + 110, 840), outline=GILT, width=5)
    text_c(d, (W / 2, 700), "THE", font(SERIF_B, 28), GILT, spacing=4)
    text_c(d, (W / 2, 740), "ARCHIVE", font(SERIF_B, 34), GILT, spacing=4)
    text_c(d, (W / 2, 784), "No. 4471", font(SERIF_I, 26), GILT)
    im.convert("RGB").save(os.path.join(OUT, "book_cover.png"))
    sp = paper(220, 900, base=(32, 44, 64), grain=8, stains=0, edge=0.3, seed=22).convert("RGBA")
    d = ImageDraw.Draw(sp, "RGBA")
    for y in (60, 120, 780, 840):
        d.rectangle((10, y, 210, y + 10), fill=GILT)
    d.rectangle((26, 240, 194, 520), fill=(226, 212, 180), outline=GILT, width=4)
    for k, s in enumerate(("HIST.", "OF THE", "NIGHT", "SCHOOLS")):
        text_c(d, (110, 290 + k * 62), s, font(TIMES_B, 34 if k != 1 else 26), INK)
    d.rectangle((40, 620, 180, 700), fill=(226, 212, 180))
    text_c(d, (110, 660), "942.3", font(SERIF_B, 34), INK)
    sp.convert("RGB").save(os.path.join(OUT, "book_spine.png"))
    # the borrowing card
    W, H = 600, 900
    c = paper(W, H, base=(232, 222, 196), stains=0, edge=0.15, seed=9).convert("RGBA")
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle((0, 0, W, 120), fill=CRIMSON)
    text_c(d, (W / 2, 46), "LIBRARY CARD", font(TIMES_B, 48), (240, 226, 196), spacing=4)
    text_c(d, (W / 2, 96), "The Archive · Nightmare High", font(SERIF_I, 28), (236, 210, 170))
    d.text((40, 170), "DATE DUE", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="lm")
    d.text((330, 170), "BORROWER", font=font(SERIF_B, 30), fill=INK_SOFT, anchor="lm")
    for k in range(9):
        y = 210 + k * 72
        d.line((30, y, W - 30, y), fill=(120, 100, 80, 180), width=2)
        if k < 4:
            d.text((44, y + 38), ("OCT 14", "OCT 30", "NOV 06", "NOV 13")[k], font=font(TIMES_B, 36), fill=(110, 20, 32, 220), anchor="lm")
            d.text((330, y + 38), ("E. Harlow", "R. Pike", "M. Danby", "")[k], font=font(SERIF_I, 34), fill=(30, 30, 70, 220), anchor="lm")
    d.line((310, 150, 310, H - 30), fill=(120, 100, 80, 180), width=2)
    c.convert("RGB").save(os.path.join(OUT, "library_card.png"))


def key_tag():
    W, H = 400, 600
    t = paper(W, H, base=(214, 200, 168), grain=10, stains=0, edge=0.2, seed=4).convert("RGBA")
    d = ImageDraw.Draw(t, "RGBA")
    d.rectangle((24, 24, W - 24, H - 24), outline=INK, width=6)
    text_c(d, (W / 2, 150), "DORM", font(TIMES_B, 80), INK, spacing=6)
    text_c(d, (W / 2, 250), "West Wing", font(SERIF_I, 46), INK_SOFT)
    text_c(d, (W / 2, 380), "No.", font(SERIF_I, 52), CRIMSON)
    text_c(d, (W / 2, 470), "13", font(TIMES_B, 120), CRIMSON)
    t.convert("RGB").save(os.path.join(OUT, "key_tag.png"))


if __name__ == "__main__":
    campus_map(); timetable(); compass_dial(); thermos_label(); tin(); book(); key_tag()
    print("prints ->", OUT, sorted(os.listdir(OUT)))
