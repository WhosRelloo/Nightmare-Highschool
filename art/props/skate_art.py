"""Deck graphics for the props batch 18 skateboards (run with plain Python + Pillow, before the Blender bake):

    python art/props/skate_art.py

Writes art/props/source_skate/<Board>_bottom.png (the deck graphic) and <Board>_grip.png (black griptape with a cut-out
sigil), drawn 2048 x 512 and saved stretched to 2048 x 2048 (see main), long axis along x with the nose on the RIGHT (Blender +x). Everything is drawn on an upright
portrait canvas (deck width x deck length, top = nose) and turned, so the art runs along the board like a real deck.
Original artwork, symbols only (no words).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "source_skate")
W, H = 512, 2048          # portrait: deck width x deck length, top = nose
GOLD = (214, 172, 92)
BONE = (226, 214, 188)
INK = (14, 12, 18)


def grad(top, bottom):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = abs(y / (H - 1) - 0.5) * 2          # dark at both ends
        for x in range(W):
            e = abs(x / (W - 1) - 0.5) * 2
            k = 1 - 0.35 * e * e
            c = [int((top[i] * (1 - t) + bottom[i] * t) * k) for i in range(3)]
            px[x, y] = tuple(c)
    return im


def grain(im, amount=10, seed=1):
    rnd = random.Random(seed)
    n = Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).convert("L")
    n = n.point(lambda v: 128 + (v - 128) * amount // 40)
    return Image.composite(im, Image.blend(im, Image.merge("RGB", (n, n, n)), 0.0), Image.new("L", (W, H), 255)).point(lambda v: v) \
        if amount == 0 else Image.blend(im, Image.merge("RGB", (n, n, n)), amount / 255)


def outline(d, col, inset=18, width=5):
    """A pinstripe following the deck outline (round nose and tail)."""
    r = W // 2 - inset
    d.rounded_rectangle((inset, inset, W - inset, H - inset), radius=r, outline=col, width=width)


def arches(d, y0, col, n=4, h=90, flip=False):
    """A row of gothic lancets (tracery band) across the deck at y0."""
    w = (W - 120) / n
    for i in range(n):
        x0 = 60 + i * w
        x1 = x0 + w - 10
        cx = (x0 + x1) / 2
        if not flip:
            pts = [(x0, y0 + h), (x0, y0 + h * 0.45), (cx, y0), (x1, y0 + h * 0.45), (x1, y0 + h)]
        else:
            pts = [(x0, y0 - h), (x0, y0 - h * 0.45), (cx, y0), (x1, y0 - h * 0.45), (x1, y0 - h)]
        d.line(pts, fill=col, width=4)


def star(d, cx, cy, r, col, n=4):
    pts = []
    for i in range(n * 2):
        a = i * math.pi / n - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.3
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=col)


def stars(d, col, seed, count=26, y_range=(120, H - 120)):
    rnd = random.Random(seed)
    for _ in range(count):
        star(d, rnd.uniform(50, W - 50), rnd.uniform(*y_range), rnd.uniform(5, 12), col)


def poly(d, pts, cx, cy, s, col, flipx=False):
    d.polygon([(cx + (-x if flipx else x) * s, cy + y * s) for x, y in pts], fill=col)


# ------------------------------------------------------------------ emblems (drawn around (cx, cy), unit ~ 1 = 100 px)
RAVEN = [(-1.6, 0.2), (-1.0, -0.1), (-0.5, -0.6), (0.1, -0.85), (0.55, -1.35), (0.9, -1.45), (1.35, -1.3), (1.6, -1.15),
         (1.25, -1.05), (1.15, -0.8), (1.0, -0.3), (0.8, 0.3), (0.5, 0.75), (0.7, 1.05), (0.3, 0.95), (0.15, 1.35),
         (-0.1, 0.95), (-0.5, 1.0), (-0.9, 1.7), (-1.0, 1.15), (-1.35, 0.85)]


def raven(d, cx, cy, s, col, eye):
    poly(d, RAVEN, cx, cy, s, col)
    d.ellipse((cx + 1.0 * s - 8, cy - 1.22 * s - 8, cx + 1.0 * s + 8, cy - 1.22 * s + 8), fill=eye)


def cross(d, cx, cy, s, col, ring):
    d.ellipse((cx - 0.9 * s, cy - 1.5 * s, cx + 0.9 * s, cy - 0.3 * s), outline=ring, width=int(0.16 * s))
    d.rectangle((cx - 0.18 * s, cy - 2.2 * s, cx + 0.18 * s, cy + 1.6 * s), fill=col)
    d.rectangle((cx - 1.1 * s, cy - 1.08 * s, cx + 1.1 * s, cy - 0.72 * s), fill=col)


def ball(d, cx, cy, r, base, patch):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=base, outline=patch, width=6)
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        px, py = cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62
        pts = [(px + math.cos(a + j * 2 * math.pi / 5) * r * 0.22, py + math.sin(a + j * 2 * math.pi / 5) * r * 0.22) for j in range(5)]
        d.polygon(pts, fill=patch)
    pts = [(cx + math.cos(j * 2 * math.pi / 5 - math.pi / 2) * r * 0.24, cy + math.sin(j * 2 * math.pi / 5 - math.pi / 2) * r * 0.24) for j in range(5)]
    d.polygon(pts, fill=patch)


def shield(d, cx, cy, s, fill, rim):
    pts = [(-1.3, -1.6), (1.3, -1.6), (1.3, 0.1), (0.9, 1.0), (0, 1.8), (-0.9, 1.0), (-1.3, 0.1)]
    poly(d, [(x * 1.12, y * 1.08) for x, y in pts], cx, cy, s, rim)
    poly(d, pts, cx, cy, s, fill)


def candle(d, cx, cy, s, wax, flame, gold, core=(255, 240, 190)):
    for k in range(12):                                     # halo rays
        a = k * math.pi / 6
        d.line((cx + math.cos(a) * 0.9 * s, cy - 2.2 * s + math.sin(a) * 0.9 * s,
                cx + math.cos(a) * 1.6 * s, cy - 2.2 * s + math.sin(a) * 1.6 * s), fill=gold, width=6)
    d.rectangle((cx - 0.45 * s, cy - 1.4 * s, cx + 0.45 * s, cy + 2.0 * s), fill=wax)
    d.polygon([(cx - 0.45 * s, cy - 1.4 * s), (cx - 0.2 * s, cy - 1.0 * s), (cx - 0.3 * s, cy - 0.5 * s), (cx - 0.45 * s, cy - 0.7 * s)], fill=wax)
    d.polygon([(cx, cy - 3.0 * s), (cx + 0.35 * s, cy - 2.2 * s), (cx, cy - 1.6 * s), (cx - 0.35 * s, cy - 2.2 * s)], fill=flame)
    d.polygon([(cx, cy - 2.55 * s), (cx + 0.15 * s, cy - 2.1 * s), (cx, cy - 1.8 * s), (cx - 0.15 * s, cy - 2.1 * s)], fill=core)
    d.rectangle((cx - 0.8 * s, cy + 2.0 * s, cx + 0.8 * s, cy + 2.3 * s), fill=gold)
    d.rectangle((cx - 0.5 * s, cy + 2.3 * s, cx + 0.5 * s, cy + 2.9 * s), fill=gold)


def rose(d, cx, cy, s, petal, dark, stem, thorn):
    d.line((cx, cy + 0.8 * s, cx + 0.15 * s, cy + 6.0 * s), fill=stem, width=int(0.18 * s))
    for k in range(6):                                      # thorns along the stem
        ty = cy + (1.4 + k * 0.75) * s
        sx = 1 if k % 2 else -1
        d.polygon([(cx + sx * 0.08 * s, ty), (cx + sx * 0.45 * s, ty - 0.25 * s), (cx + sx * 0.08 * s, ty - 0.18 * s)], fill=thorn)
    for k, (lx, ly) in enumerate(((-0.9, 2.6), (0.9, 3.6))):  # leaves
        sx = -1 if lx < 0 else 1
        d.polygon([(cx, cy + ly * s), (cx + sx * 0.6 * s, cy + (ly - 0.5) * s), (cx + sx * 1.1 * s, cy + (ly - 0.2) * s),
                   (cx + sx * 0.6 * s, cy + (ly + 0.15) * s)], fill=stem)
    def petal_at(dist, a, rl, rw, fill, line):
        px, py = cx + math.cos(a) * dist * s, cy + math.sin(a) * dist * s * 0.92
        pts = []
        for i in range(28):
            t = i / 28 * 2 * math.pi
            ex, ey = math.cos(t) * rl * s, math.sin(t) * rw * s
            pts.append((px + ex * math.cos(a) - ey * math.sin(a), py + ex * math.sin(a) + ey * math.cos(a)))
        d.polygon(pts, fill=fill, outline=line)
        d.line(pts + [pts[0]], fill=line, width=5)
    shade = tuple(int(c * 0.75) for c in petal)
    for k in range(7):                                      # the outer ring of petals
        petal_at(0.72, k * 2 * math.pi / 7 + 0.2, 0.62, 0.48, petal, dark)
    for k in range(5):                                      # the inner ring, darker, offset
        petal_at(0.38, k * 2 * math.pi / 5 + 0.6, 0.45, 0.34, shade, dark)
    d.ellipse((cx - 0.32 * s, cy - 0.3 * s, cx + 0.32 * s, cy + 0.3 * s), fill=petal, outline=dark, width=5)
    for k, r in enumerate((0.26, 0.17, 0.09)):              # the bud's spiral
        d.arc((cx - r * s, cy - r * s, cx + r * s, cy + r * s), 40 + k * 120, 300 + k * 120, fill=dark, width=5)


def school(d, base_y, col, win):
    """The school on its hill: a silhouette across the deck at base_y (towers, spires, lit windows)."""
    d.pieslice((-300, base_y - 140, W + 300, base_y + 600), 180, 360, fill=col)
    blocks = [(70, 230, 150), (150, 360, 330), (330, 170, 450)]
    for x0, h, x1 in [(b[0], b[1], b[2]) for b in blocks]:
        d.rectangle((x0, base_y - h - 60, x1, base_y), fill=col)
    for x, h in ((110, 330), (250, 470), (390, 290)):
        d.polygon([(x - 30, base_y - h), (x, base_y - h - 120), (x + 30, base_y - h)], fill=col)
        d.rectangle((x - 30, base_y - h, x + 30, base_y - 100), fill=col)
    rnd = random.Random(7)
    for _ in range(14):
        x = rnd.uniform(80, 440)
        y = rnd.uniform(base_y - 300, base_y - 80)
        d.rectangle((x, y, x + 10, y + 16), fill=win)


def bat(d, cx, cy, s, col):
    pts = [(-1.0, 0), (-0.6, -0.25), (-0.35, 0.05), (-0.15, -0.15), (0, 0.0), (0.15, -0.15), (0.35, 0.05), (0.6, -0.25), (1.0, 0),
           (0.55, 0.15), (0.3, 0.35), (0, 0.2), (-0.3, 0.35), (-0.55, 0.15)]
    poly(d, pts, cx, cy, s, col)


def hand(d, cx, cy, s, bone, line):
    """A skeleton hand reaching toward the nose: palm bones, then three-joint fingers."""
    def b(x0, y0, x1, y1, w):
        d.line((x0, y0, x1, y1), fill=line, width=int(w + 8))
        d.line((x0, y0, x1, y1), fill=bone, width=int(w))
        for x, y in ((x0, y0), (x1, y1)):
            d.ellipse((x - w * 0.6, y - w * 0.6, x + w * 0.6, y + w * 0.6), fill=bone, outline=line, width=3)
    d.ellipse((cx - 0.9 * s, cy + 1.2 * s, cx + 0.9 * s, cy + 2.4 * s), fill=bone, outline=line, width=4)     # carpals
    b(cx, cy + 2.4 * s, cx, cy + 4.8 * s, 0.42 * s)                                                          # radius
    for k, ang in enumerate((-0.5, -0.17, 0.12, 0.42)):
        x0, y0 = cx + math.sin(ang) * 0.6 * s, cy + 1.3 * s
        pts = [(x0, y0)]
        for j, ln in enumerate((1.0, 0.75, 0.55, 0.45)):
            x, y = pts[-1]
            a = ang * (1 + j * 0.25)
            pts.append((x + math.sin(a) * ln * s, y - math.cos(a) * ln * s * (1.15 if k in (1, 2) else 1.0)))
        for p, q in zip(pts, pts[1:]):
            b(p[0], p[1], q[0], q[1], 0.2 * s)
    x0, y0 = cx - 0.8 * s, cy + 1.7 * s                                                                      # thumb
    b(x0, y0, x0 - 0.7 * s, y0 - 0.6 * s, 0.22 * s)
    b(x0 - 0.7 * s, y0 - 0.6 * s, x0 - 1.0 * s, y0 - 1.25 * s, 0.2 * s)


def gargoyle(d, cx, cy, s, stone, dark, eye):
    poly(d, [(-1.5, -0.4), (-2.2, -2.2), (-1.0, -1.1), (1.0, -1.1), (2.2, -2.2), (1.5, -0.4)], cx, cy, s, dark)   # horns
    d.ellipse((cx - 1.55 * s, cy - 1.4 * s, cx + 1.55 * s, cy + 1.6 * s), fill=stone, outline=dark, width=8)       # head
    poly(d, [(-1.5, -0.2), (-2.3, -0.7), (-1.9, 0.3)], cx, cy, s, stone)                                        # ears
    poly(d, [(1.5, -0.2), (2.3, -0.7), (1.9, 0.3)], cx, cy, s, stone)
    d.polygon([(cx - 1.1 * s, cy - 0.6 * s), (cx - 0.25 * s, cy - 0.25 * s), (cx - 0.95 * s, cy - 0.05 * s)], fill=dark)   # brow
    d.polygon([(cx + 1.1 * s, cy - 0.6 * s), (cx + 0.25 * s, cy - 0.25 * s), (cx + 0.95 * s, cy - 0.05 * s)], fill=dark)
    for sx in (-1, 1):
        d.ellipse((cx + sx * 0.65 * s - 0.2 * s, cy - 0.38 * s, cx + sx * 0.65 * s + 0.2 * s, cy - 0.05 * s), fill=eye)
    d.polygon([(cx - 0.2 * s, cy - 0.1 * s), (cx + 0.2 * s, cy - 0.1 * s), (cx + 0.3 * s, cy + 0.45 * s), (cx - 0.3 * s, cy + 0.45 * s)], fill=dark)  # snout
    d.chord((cx - 1.0 * s, cy + 0.2 * s, cx + 1.0 * s, cy + 1.35 * s), 0, 180, fill=dark)                       # grin
    for k in range(7):
        x = cx - 0.85 * s + k * 0.283 * s
        d.polygon([(x, cy + 0.78 * s), (x + 0.28 * s, cy + 0.78 * s), (x + 0.14 * s, cy + 1.08 * s)], fill=BONE)
    for sx in (-1, 1):
        d.polygon([(cx + sx * 0.75 * s, cy + 0.78 * s), (cx + sx * 0.55 * s, cy + 0.78 * s), (cx + sx * 0.66 * s, cy + 1.3 * s)], fill=BONE)


def crest(d, cx, cy, s, gold, red, ink):
    shield(d, cx, cy, s, ink, gold)
    for qx, qy, col in ((-0.6, -0.85, red), (0.6, 0.35, red)):
        d.rectangle((cx + (qx - 0.55) * s, cy + (qy - 0.6) * s, cx + (qx + 0.55) * s, cy + (qy + 0.6) * s), fill=col)
    d.line((cx, cy - 1.6 * s, cx, cy + 1.75 * s), fill=gold, width=8)
    d.line((cx - 1.3 * s, cy - 0.25 * s, cx + 1.3 * s, cy - 0.25 * s), fill=gold, width=8)
    raven(d, cx - 0.62 * s, cy - 0.8 * s, 0.3 * s, gold, red)                                                    # raven
    d.ellipse((cx + 0.3 * s, cy - 1.3 * s, cx + 0.95 * s, cy - 0.45 * s), fill=gold)                              # moon
    d.ellipse((cx + 0.48 * s, cy - 1.38 * s, cx + 1.1 * s, cy - 0.55 * s), fill=ink)
    d.ellipse((cx - 0.85 * s, cy + 0.0 * s, cx - 0.45 * s, cy + 0.4 * s), outline=gold, width=7)                  # key
    d.line((cx - 0.65 * s, cy + 0.4 * s, cx - 0.65 * s, cy + 1.15 * s), fill=gold, width=7)
    d.line((cx - 0.65 * s, cy + 0.95 * s, cx - 0.42 * s, cy + 0.95 * s), fill=gold, width=7)
    candle(d, cx + 0.62 * s, cy + 0.6 * s, 0.17 * s, BONE, (255, 170, 80), gold)                                 # candle
    for sx in (-1, 1):                                                                                          # crossed quills
        d.line((cx + sx * 1.9 * s, cy + 2.4 * s, cx - sx * 1.6 * s, cy - 2.4 * s), fill=gold, width=7)


# ------------------------------------------------------------------ boards
def board_ravens():
    im = grad((58, 26, 78), (12, 8, 18))
    d = ImageDraw.Draw(im)
    d.ellipse((W / 2 - 220, 560, W / 2 + 220, 1000), fill=(176, 158, 196))
    stars(d, (190, 170, 220), 3)
    d.line((40, 1180, W - 40, 1140), fill=INK, width=22)                  # the branch
    raven(d, W / 2 - 10, 930, 140, INK, (200, 40, 60))
    arches(d, 150, (150, 110, 190)); arches(d, H - 150, (150, 110, 190), flip=True)
    outline(d, (150, 110, 190))
    return im, (150, 110, 190), (160, 130, 200)


def board_rovers():
    im = grad((32, 64, 44), (10, 20, 14))
    d = ImageDraw.Draw(im)
    cross(d, W / 2, 980, 140, (180, 190, 170), (120, 160, 120))
    ball(d, W / 2, 1420, 120, BONE, INK)
    for k in range(5):                                                   # headstones at the tail
        x = 70 + k * 92
        d.rounded_rectangle((x, H - 330, x + 60, H - 230), radius=28, fill=(90, 110, 96))
    arches(d, 150, (120, 170, 120)); arches(d, H - 150, (120, 170, 120), flip=True)
    outline(d, (120, 170, 120))
    return im, (120, 170, 120), (150, 190, 150)


def board_wardens():
    im = grad((96, 98, 104), (34, 34, 38))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    for _ in range(40):                                                  # rust streaks
        x = rnd.uniform(30, W - 30); y = rnd.uniform(100, H - 300)
        d.line((x, y, x + rnd.uniform(-6, 6), y + rnd.uniform(80, 260)), fill=(120, 58, 30), width=int(rnd.uniform(3, 9)))
    shield(d, W / 2, 1020, 150, (60, 62, 68), (150, 70, 36))
    d.line((W / 2 - 150, 860, W / 2 + 150, 1180), fill=(150, 70, 36), width=24)
    d.line((W / 2 + 150, 860, W / 2 - 150, 1180), fill=(150, 70, 36), width=24)
    for k in range(14):                                                  # rivets round the shield
        a = k / 14 * 2 * math.pi
        d.ellipse((W / 2 + math.cos(a) * 170 - 9, 1020 + math.sin(a) * 230 - 9, W / 2 + math.cos(a) * 170 + 9, 1020 + math.sin(a) * 230 + 9), fill=(190, 190, 196))
    for y in range(120, H - 100, 64):                                    # chain border
        for x in (34, W - 34):
            d.ellipse((x - 12, y, x + 12, y + 46), outline=(150, 150, 156), width=6)
    outline(d, (150, 70, 36))
    return im, (150, 70, 36), (130, 130, 136)


def board_vigil():
    im = grad((16, 20, 52), (6, 6, 16))
    d = ImageDraw.Draw(im)
    stars(d, GOLD, 9, count=34)
    candle(d, W / 2, 1060, 120, BONE, (255, 160, 70), GOLD)
    arches(d, 150, GOLD); arches(d, H - 150, GOLD, flip=True)
    outline(d, GOLD)
    return im, GOLD, GOLD


def board_crimson():
    im = grad((120, 14, 24), (30, 4, 8))
    d = ImageDraw.Draw(im)
    for y in range(140, H - 120, 120):                                   # thorn vine border
        for x, s in ((40, 1), (W - 40, -1)):
            d.arc((x - 40, y, x + 40, y + 120), 270 if s > 0 else 90, 90 if s > 0 else 270, fill=GOLD, width=5)
            d.polygon([(x, y + 60), (x + s * 26, y + 48), (x, y + 72)], fill=GOLD)
    rose(d, W / 2, 680, 150, (186, 20, 40), (90, 6, 16), (30, 50, 26), (20, 30, 16))
    outline(d, GOLD)
    return im, GOLD, (200, 40, 60)


def board_moonlit():
    im = grad((26, 34, 78), (6, 8, 22))
    d = ImageDraw.Draw(im)
    stars(d, (220, 220, 240), 11, count=30, y_range=(100, 1300))
    d.ellipse((W / 2 - 200, 420, W / 2 + 200, 820), fill=(236, 230, 210))
    d.ellipse((W / 2 - 60, 520, W / 2 + 10, 580), fill=(214, 208, 190))
    d.ellipse((W / 2 + 40, 660, W / 2 + 120, 720), fill=(214, 208, 190))
    for k, (x, y, s) in enumerate(((140, 980, 70), (360, 1080, 55), (250, 1200, 45))):
        bat(d, x, y, s, INK)
    school(d, H - 330, (10, 10, 16), (255, 190, 110))
    outline(d, (170, 170, 210))
    return im, (170, 170, 210), (190, 190, 220)


def board_bone():
    im = grad((228, 218, 194), (170, 158, 132))
    d = ImageDraw.Draw(im)
    rnd = random.Random(13)
    for _ in range(22):                                                  # hairline cracks
        x, y = rnd.uniform(40, W - 40), rnd.uniform(100, H - 100)
        pts = [(x, y)]
        for _ in range(4):
            x += rnd.uniform(-30, 30); y += rnd.uniform(20, 60)
            pts.append((x, y))
        d.line(pts, fill=(140, 128, 104), width=2)
    hand(d, W / 2, 760, 150, BONE, INK)
    arches(d, 150, INK); arches(d, H - 150, INK, flip=True)
    outline(d, INK)
    return im, INK, (120, 108, 90)


def board_gargoyle():
    base = Image.effect_noise((W, H), 60).convert("L").filter(ImageFilter.GaussianBlur(2))
    im = Image.merge("RGB", [base.point(lambda v, k=k: int(60 + v * 0.45 * k)) for k in (1.0, 1.0, 0.95)])
    d = ImageDraw.Draw(im)
    rnd = random.Random(17)
    for y in range(0, H, 128):                                           # ashlar joints
        d.line((0, y, W, y), fill=(50, 50, 52), width=4)
        off = 0 if (y // 128) % 2 else 128
        for x in range(off, W, 256):
            d.line((x, y, x, y + 128), fill=(50, 50, 52), width=4)
    gargoyle(d, W / 2, 1000, 120, (150, 148, 140), (40, 40, 44), (255, 140, 40))
    outline(d, (210, 120, 40))
    return im, (210, 120, 40), (150, 148, 140)


def board_headmaster():
    im = grad((26, 24, 30), (6, 6, 8))
    d = ImageDraw.Draw(im)
    for inset in (22, 40):
        d.rounded_rectangle((inset, inset, W - inset, H - inset), radius=W // 2 - inset, outline=GOLD, width=4)
    crest(d, W / 2, 1010, 140, GOLD, (130, 16, 28), (16, 14, 20))
    arches(d, 170, GOLD); arches(d, H - 170, GOLD, flip=True)
    for y in (420, H - 420):                                             # gilt quatrefoils
        for k in range(4):
            a = k * math.pi / 2
            d.ellipse((W / 2 + math.cos(a) * 26 - 24, y + math.sin(a) * 26 - 24, W / 2 + math.cos(a) * 26 + 24, y + math.sin(a) * 26 + 24), outline=GOLD, width=5)
    return im, GOLD, GOLD


BOARDS = {
    "SkateboardRavens": board_ravens, "SkateboardRovers": board_rovers, "SkateboardWardens": board_wardens,
    "SkateboardVigil": board_vigil, "SkateboardCrimson": board_crimson, "SkateboardMoonlit": board_moonlit,
    "SkateboardBone": board_bone, "SkateboardGargoyle": board_gargoyle, "SkateboardHeadmaster": board_headmaster,
}


def grip(sigil_fn, accent, gilt_edge, seed):
    """Black griptape (grit noise) with the board's sigil cut out near the nose and tail, slightly lighter."""
    n = Image.effect_noise((W, H), 80).convert("L")
    im = Image.merge("RGB", [n.point(lambda v: int(12 + v * 0.09))] * 3)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    sigil_fn(md, W / 2, 330)
    sigil_fn(md, W / 2, H - 330)
    lighter = Image.merge("RGB", [n.point(lambda v, c=c: int(26 + v * 0.1 + c * 0.08)) for c in accent])
    im = Image.composite(lighter, im, mask)
    d = ImageDraw.Draw(im)
    if gilt_edge:
        d.rounded_rectangle((14, 14, W - 14, H - 14), radius=W // 2 - 14, outline=GOLD, width=5)
    return im


SIGILS = {
    "SkateboardRavens": lambda d, x, y: raven(d, x, y, 60, 255, 255),
    "SkateboardRovers": lambda d, x, y: cross(d, x, y + 40, 55, 255, 255),
    "SkateboardWardens": lambda d, x, y: shield(d, x, y, 60, 255, 255),
    "SkateboardVigil": lambda d, x, y: candle(d, x, y + 40, 40, 255, 255, 255, core=0),
    "SkateboardCrimson": lambda d, x, y: [d.ellipse((x - 60, y - 55, x + 60, y + 55), fill=255), d.ellipse((x - 30, y - 28, x + 30, y + 28), fill=0)],
    "SkateboardMoonlit": lambda d, x, y: [d.ellipse((x - 70, y - 70, x + 70, y + 70), fill=255), d.ellipse((x - 30, y - 80, x + 100, y + 60), fill=0)],
    "SkateboardBone": lambda d, x, y: [d.ellipse((x - 70, y - 30, x - 20, y + 20), fill=255), d.ellipse((x + 20, y - 30, x + 70, y + 20), fill=255),
                                       d.rectangle((x - 45, y - 10, x + 45, y + 10), fill=255)],
    "SkateboardGargoyle": lambda d, x, y: [d.polygon([(x - 80, y + 40), (x - 110, y - 60), (x - 30, y), (x + 30, y), (x + 110, y - 60), (x + 80, y + 40)], fill=255)],
    "SkateboardHeadmaster": lambda d, x, y: shield(d, x, y, 55, 255, 255),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, (name, fn) in enumerate(BOARDS.items()):
        im, accent, edge = fn()
        im = Image.blend(im, Image.effect_noise((W, H), 30).convert("RGB"), 0.04)    # a little paint grain
        bottom = im.rotate(-90, expand=True)            # portrait top (nose) -> landscape right
        bottom = ImageOps.flip(bottom)                  # seen from below, so it reads the right way round
        # saved square: Blender's smart UV project corrects for a non-square image in the material and would squash
        # the deck's islands (the art is mapped in object space, so the stretch is undone on the board)
        bottom.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, f"{name}_bottom.png"))
        g = grip(SIGILS[name], accent, name == "SkateboardHeadmaster", i).rotate(-90, expand=True)
        g.resize((2048, 2048), Image.LANCZOS).save(os.path.join(OUT, f"{name}_grip.png"))
        with open(os.path.join(OUT, f"{name}_edge.txt"), "w") as f:
            f.write("%d %d %d\n" % tuple(edge))
        print(name)


if __name__ == "__main__":
    main()
