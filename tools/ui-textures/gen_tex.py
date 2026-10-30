"""Generate original gothic UI textures for the Nightmare Highschool UI kit.
All art is white/greyscale so Roblox ImageColor3 can tint it per theme."""
import math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
SS = 4  # supersample
rng = np.random.default_rng(7)
random.seed(7)


def value_noise(w, h, cell, seed):
    r = np.random.default_rng(seed)
    gw, gh = w // cell + 1, h // cell + 1
    g = r.random((gh, gw))
    g[:, -1] = g[:, 0]
    g[-1, :] = g[0, :]
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:h, :w] / 255.0


def fbm(w, h, seed, base=64, octaves=5):
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    cell = base
    for o in range(octaves):
        acc += value_noise(w, h, max(cell, 2), seed + o) * amp
        tot += amp
        amp *= 0.5
        cell //= 2
    return acc / tot


class Pen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("L", (w * SS, h * SS), 0)
        self.d = ImageDraw.Draw(self.im)

    def dot(self, x, y, r, v=255):
        x, y, r = x * SS, y * SS, max(r * SS, 0.5)
        self.d.ellipse((x - r, y - r, x + r, y + r), fill=v)

    def stroke(self, pts, w0, w1=None, v=255):
        if w1 is None:
            w1 = w0
        # resample densely
        dense = []
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            n = max(2, int(math.hypot(bx - ax, by - ay) * SS))
            for k in range(n):
                t = k / n
                dense.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        dense.append(pts[-1])
        N = len(dense)
        for i, (x, y) in enumerate(dense):
            t = i / max(N - 1, 1)
            self.dot(x, y, (w0 + (w1 - w0) * t) / 2, v)

    def line(self, a, b, w, v=255):
        self.stroke([a, b], w, w, v)

    def poly(self, pts, v=255):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=v)

    def result(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def spiral(cx, cy, r0, r1, a0, sweep, n=120):
    return [(cx + (r0 + (r1 - r0) * (i / n)) * math.cos(a0 + sweep * i / n),
             cy + (r0 + (r1 - r0) * (i / n)) * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]


def bezier(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def leaf(p, a, length, width):
    x, y = p
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    tip = (x + dx * length, y + dy * length)
    mid = (x + dx * length * 0.45, y + dy * length * 0.45)
    return [p, (mid[0] + nx * width, mid[1] + ny * width), tip, (mid[0] - nx * width, mid[1] - ny * width)]


def diamond(cx, cy, r):
    return [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]


def mirror_corners(corner_L, size):
    """corner_L: 'L' image of TL corner (size x size). returns 4 rotated copies as dict"""
    return {
        "tl": corner_L,
        "tr": corner_L.transpose(Image.FLIP_LEFT_RIGHT),
        "bl": corner_L.transpose(Image.FLIP_TOP_BOTTOM),
        "br": corner_L.transpose(Image.ROTATE_180),
    }


def wear(alpha_arr, seed, strength=0.55):
    n = fbm(alpha_arr.shape[1], alpha_arr.shape[0], seed, base=16, octaves=4)
    m = np.clip((n - 0.18) * 2.2, 0, 1)  # chipped patches
    m = 1 - strength * (1 - m)
    return alpha_arr * m


def to_rgba(alpha, seed, shade=0.25):
    """white art with grey shading variation"""
    h, w = alpha.shape
    n = fbm(w, h, seed + 100, base=8, octaves=3)
    lum = np.clip(1 - shade + shade * n * 1.4, 0, 1)
    rgb = (lum * 255).astype(np.uint8)
    a = np.clip(alpha, 0, 255).astype(np.uint8)
    return Image.merge("RGBA", [Image.fromarray(rgb)] * 3 + [Image.fromarray(a)])


# ---------------------------------------------------------------- ornate frame
def corner_ornament(C=128, outer=7, inner=17):
    p = Pen(C, C)
    # big C-scroll down the left side, curling into the panel
    p.stroke(bezier((inner, 108), (inner + 2, 86), (inner + 22, 80), (inner + 24, 66)), 2.2, 3.4)
    p.stroke(spiral(inner + 14, 62, 10, 2.5, 0.35, -math.pi * 1.7), 3.4, 1.6)
    p.dot(inner + 14 + 2.5 * math.cos(0.35 - math.pi * 1.7), 62 + 2.5 * math.sin(0.35 - math.pi * 1.7), 2.2)
    # mirrored scroll along top
    p.stroke(bezier((108, inner), (86, inner + 2), (80, inner + 22), (66, inner + 24)), 2.2, 3.4)
    p.stroke([(y, x) for x, y in spiral(inner + 14, 62, 10, 2.5, 0.35, -math.pi * 1.7)], 3.4, 1.6)
    p.dot(62 + 2.5 * math.sin(0.35 - math.pi * 1.7), inner + 14 + 2.5 * math.cos(0.35 - math.pi * 1.7), 2.2)
    # diagonal thorn / spearhead pointing inward
    p.stroke([(inner + 2, inner + 2), (50, 50)], 3.2, 1.2)
    p.poly(diamond(54, 54, 5.5))
    p.poly(leaf((34, 34), math.radians(20), 16, 3.5))
    p.poly(leaf((34, 34), math.radians(70), 16, 3.5))
    # small secondary curls hugging the inner line
    p.stroke(spiral(inner + 7, 36, 6, 1.5, -math.pi / 2, math.pi * 1.4), 1.8, 1.0)
    p.stroke([(y, x) for x, y in spiral(inner + 7, 36, 6, 1.5, -math.pi / 2, math.pi * 1.4)], 1.8, 1.0)
    # corner boss: diamond with pierced centre, on the outer line
    p.poly(diamond(outer + 3, outer + 3, 11))
    p.dot(outer + 3, outer + 3, 3.2, 0)
    # tiny thorns sticking outward from the outer line
    for t in (40, 78):
        p.poly([(t - 3, outer), (t, outer - 5), (t + 3, outer)])
        p.poly([(outer, t - 3), (outer - 5, t), (outer, t + 3)])
    # bead dots
    for t in (92, 100):
        p.dot(inner + 5, t, 1.4)
        p.dot(t, inner + 5, 1.4)
    return p.result()


def ornate_frame(S=512, C=128, outer=7, inner=17, name="frame_ornate", seed=1, wear_s=0.5):
    p = Pen(S, S)
    # outer heavy line + inner hairline, along every edge
    for (a, b) in [((outer, outer), (S - outer, outer)), ((outer, S - outer), (S - outer, S - outer)),
                   ((outer, outer), (outer, S - outer)), ((S - outer, outer), (S - outer, S - outer))]:
        p.line(a, b, 3.2)
    for (a, b) in [((inner, inner), (S - inner, inner)), ((inner, S - inner), (S - inner, S - inner)),
                   ((inner, inner), (inner, S - inner)), ((S - inner, inner), (S - inner, S - inner))]:
        p.line(a, b, 1.3)
    base = p.result()
    corners = mirror_corners(corner_ornament(C, outer, inner), C)
    for k, im in corners.items():
        x = 0 if k[1] == "l" else S - C
        y = 0 if k[0] == "t" else S - C
        region = base.crop((x, y, x + C, y + C))
        base.paste(Image.fromarray(np.maximum(np.asarray(region), np.asarray(im))), (x, y))
    a = np.asarray(base, np.float32)
    a = wear(a, seed, wear_s)
    # soft dark drop-shadow halo under the ornament so it reads on any bg
    img = to_rgba(a, seed)
    img.save(os.path.join(OUT, name + ".png"))
    return img


# ------------------------------------------------------------------ thin frame
def thin_frame(S=128, name="frame_thin", seed=3):
    p = Pen(S, S)
    o, i = 4, 9
    for (a, b) in [((o, o), (S - o, o)), ((o, S - o), (S - o, S - o)), ((o, o), (o, S - o)), ((S - o, o), (S - o, S - o))]:
        p.line(a, b, 2.0)
    for (a, b) in [((i, i), (S - i, i)), ((i, S - i), (S - i, S - i)), ((i, i), (i, S - i)), ((S - i, i), (S - i, S - i))]:
        p.line(a, b, 0.9)
    base = p.result()
    C = 32
    c = Pen(C, C)
    c.poly(diamond(o + 1, o + 1, 6.5))
    c.dot(o + 1, o + 1, 1.8, 0)
    c.stroke(spiral(i + 7, i + 7, 5.5, 1.2, math.pi * 1.25, math.pi * 1.5), 1.6, 0.8)
    c.poly([(20, o), (23, o - 3.5), (26, o)])
    c.poly([(o, 20), (o - 3.5, 23), (o, 26)])
    cs = mirror_corners(c.result(), C)
    for k, im in cs.items():
        x = 0 if k[1] == "l" else S - C
        y = 0 if k[0] == "t" else S - C
        region = base.crop((x, y, x + C, y + C))
        base.paste(Image.fromarray(np.maximum(np.asarray(region), np.asarray(im))), (x, y))
    a = wear(np.asarray(base, np.float32), seed, 0.35)
    img = to_rgba(a, seed, 0.2)
    img.save(os.path.join(OUT, name + ".png"))


# ----------------------------------------------------------------- bar frame
def bar_frame(W=1024, H=128, cap=160, name="bar_frame", seed=5):
    p = Pen(W, H)
    t, b = 34, H - 34
    # rails
    p.line((cap - 40, t), (W - cap + 40, t), 3.0)
    p.line((cap - 40, b), (W - cap + 40, b), 3.0)
    p.line((cap - 30, t + 7), (W - cap + 30, t + 7), 1.1)
    p.line((cap - 30, b - 7), (W - cap + 30, b - 7), 1.1)
    base = p.result()

    def capimg():
        c = Pen(cap, H)
        cy = H / 2
        # pointed finial
        c.poly([(6, cy), (30, cy - 14), (44, cy), (30, cy + 14)])
        c.dot(30, cy, 3.5, 0)
        c.line((44, cy), (70, cy), 2.4)
        # upper and lower curls springing from the finial
        c.stroke(bezier((60, cy), (70, cy - 30), (100, cy - 34), (120, t)), 3.0, 2.4)
        c.stroke(bezier((60, cy), (70, cy + 30), (100, cy + 34), (120, b)), 3.0, 2.4)
        c.stroke(spiral(80, cy - 22, 9, 2, math.pi * 0.6, math.pi * 1.6), 2.6, 1.2)
        c.stroke(spiral(80, cy + 22, 9, 2, -math.pi * 0.6, -math.pi * 1.6), 2.6, 1.2)
        # vertical end bar
        c.line((122, t - 6), (122, b + 6), 3.4)
        c.poly(diamond(122, t - 8, 5))
        c.poly(diamond(122, b + 8, 5))
        c.line((120, t), (cap, t), 3.0)
        c.line((120, b), (cap, b), 3.0)
        c.line((130, t + 7), (cap, t + 7), 1.1)
        c.line((130, b - 7), (cap, b - 7), 1.1)
        return c.result()

    L = capimg()
    for img_, x in ((L, 0), (L.transpose(Image.FLIP_LEFT_RIGHT), W - cap)):
        region = base.crop((x, 0, x + cap, H))
        base.paste(Image.fromarray(np.maximum(np.asarray(region), np.asarray(img_))), (x, 0))
    a = wear(np.asarray(base, np.float32), seed, 0.4)
    to_rgba(a, seed).save(os.path.join(OUT, name + ".png"))


# ---------------------------------------------------- orb ring (school clock)
def orb_ring(S=256, name="orb_ring", seed=9):
    p = Pen(S, S)
    c = S / 2
    R = 96
    # double ring
    p.stroke(spiral(c, c, R, R, 0, math.tau, 360), 5)
    p.stroke(spiral(c, c, R - 12, R - 12, 0, math.tau, 360), 1.6)
    # 12 hour ticks, roman-ish heavier at XII/III/VI/IX
    for h in range(12):
        a = h / 12 * math.tau - math.pi / 2
        big = h % 3 == 0
        r0, r1 = R - 11, R - (24 if big else 18)
        p.stroke([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))], 4 if big else 2)
        # outward spikes like a gothic sunburst / iron gate finials
        s0, s1 = R + 2, R + (24 if big else 13)
        if big:
            d = 0.07
            p.poly([(c + s0 * math.cos(a - d), c + s0 * math.sin(a - d)), (c + s1 * math.cos(a), c + s1 * math.sin(a)),
                    (c + s0 * math.cos(a + d), c + s0 * math.sin(a + d))])
            p.dot(c + (s1 + 4) * math.cos(a), c + (s1 + 4) * math.sin(a), 3)
        else:
            d = 0.04
            p.poly([(c + s0 * math.cos(a - d), c + s0 * math.sin(a - d)), (c + s1 * math.cos(a), c + s1 * math.sin(a)),
                    (c + s0 * math.cos(a + d), c + s0 * math.sin(a + d))])
    # small curls between the big spikes
    for q in range(4):
        a = q * math.pi / 2 + math.pi / 4 - math.pi / 2
        for sgn in (-1, 1):
            aa = a + sgn * 0.33
            px, py = c + (R + 9) * math.cos(aa), c + (R + 9) * math.sin(aa)
            p.stroke(spiral(px, py, 6, 1.5, aa + math.pi, sgn * math.pi * 1.4), 2, 1)
    a = wear(np.asarray(p.result(), np.float32), seed, 0.3)
    to_rgba(a, seed).save(os.path.join(OUT, name + ".png"))


def orb_fill(S=256, name="orb_fill", seed=11):
    """soft glassy disc, white, with highlight -> tint per use"""
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    c = S / 2
    r = np.hypot(x - c, y - c) / 84
    disc = np.clip((1 - r) * 40, 0, 1)
    shade = np.clip(1.05 - r * 0.75, 0, 1)
    n = fbm(S, S, seed, base=32, octaves=4)
    lum = shade * (0.65 + 0.45 * n)
    hl = np.exp(-(((x - c + 22) ** 2) / 900 + ((y - c + 34) ** 2) / 300)) * 0.6
    lum = np.clip(lum + hl, 0, 1)
    rgb = Image.fromarray((lum * 255).astype(np.uint8))
    Image.merge("RGBA", [rgb] * 3 + [Image.fromarray((disc * 255).astype(np.uint8))]).save(os.path.join(OUT, name + ".png"))


# ------------------------------------------------------------- wax seal gem
def wax_seal(S=96, name="seal", seed=13):
    p = Pen(S, S)
    c = S / 2
    pts = []
    r = random.Random(seed)
    for i in range(48):
        a = i / 48 * math.tau
        rr = 34 + r.uniform(-1.5, 1.5) + (4 if i % 6 == 0 else 0)
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    p.poly(pts)
    base = np.asarray(p.result(), np.float32) / 255
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.hypot(x - c, y - c)
    lum = 0.78 + 0.22 * np.clip(1 - d / 34, 0, 1)
    ring = np.exp(-((d - 22) ** 2) / 6)  # pressed inner ring
    lum -= ring * 0.35
    # pressed sigil: a cross-in-diamond (Priest) that also reads as a candle star
    q = Pen(S, S)
    q.poly(diamond(c, c, 12))
    q.poly(diamond(c, c, 7), 0)
    q.line((c, c - 17), (c, c + 17), 2.2)
    q.line((c - 17, c), (c + 17, c), 2.2)
    sig = np.asarray(q.result(), np.float32) / 255
    lum -= sig * 0.32
    hl = np.exp(-(((x - c + 11) ** 2) + ((y - c + 13) ** 2)) / 60) * 0.35
    lum = np.clip(lum + hl, 0, 1)
    rgb = Image.fromarray((lum * 255).astype(np.uint8))
    Image.merge("RGBA", [rgb] * 3 + [Image.fromarray((base * 255).astype(np.uint8))]).save(os.path.join(OUT, name + ".png"))


# ---------------------------------------------------------- cracked bell icon
def bell(S=256, name="bell", seed=17):
    p = Pen(S, S)
    c = S / 2
    left = bezier((c - 12, 44), (c - 52, 50), (c - 46, 140), (c - 86, 186), 80)
    right = [(2 * c - x, y) for x, y in reversed(left)]
    body = left + [(c - 92, 196), (c + 92, 196)] + right
    p.poly(body)
    # rim lip
    p.d.ellipse(((c - 98) * SS, 186 * SS, (c + 98) * SS, 206 * SS), fill=255)
    # crown + hanging loop
    p.d.ellipse(((c - 16) * SS, 22 * SS, (c + 16) * SS, 52 * SS), outline=255, width=7 * SS)
    # clapper
    p.dot(c, 222, 14)
    # carve: band lines + skull-like eye sockets (bell "watches" you)
    p.stroke(bezier((c - 66, 150), (c - 20, 160), (c + 20, 160), (c + 66, 150)), 3, 3, 0)
    p.stroke(bezier((c - 74, 170), (c - 20, 180), (c + 20, 180), (c + 74, 170)), 2, 2, 0)
    p.d.ellipse(((c - 34) * SS, 92 * SS, (c - 8) * SS, 120 * SS), fill=0)
    p.d.ellipse(((c + 8) * SS, 92 * SS, (c + 34) * SS, 120 * SS), fill=0)
    p.poly([(c, 122), (c - 6, 136), (c + 6, 136)], 0)
    # crack
    p.stroke([(c + 40, 196), (c + 32, 176), (c + 44, 160), (c + 30, 140), (c + 38, 124)], 4, 1.5, 0)
    a = wear(np.asarray(p.result(), np.float32), seed, 0.25)
    to_rgba(a, seed, 0.3).save(os.path.join(OUT, name + ".png"))


# --------------------------------------------------------------- panel bg
def panel_bg(S=512, name="panel_bg", seed=21):
    n = fbm(S, S, seed, base=128, octaves=6)
    fine = fbm(S, S, seed + 50, base=4, octaves=2)
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    # vignette
    dx, dy = (x - S / 2) / (S / 2), (y - S / 2) / (S / 2)
    v = np.clip(1 - (dx**2 + dy**2) ** 1.2 * 0.55, 0, 1)
    lum = 0.30 + 0.55 * n + 0.10 * fine
    lum *= v
    # chalk-eraser smudges: wide soft horizontal swipes
    sm = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(sm)
    r = random.Random(seed)
    for _ in range(9):
        cx, cy = r.uniform(0, S), r.uniform(0, S)
        w, h = r.uniform(120, 300), r.uniform(18, 46)
        d.ellipse((cx - w, cy - h, cx + w, cy + h), fill=r.randint(18, 40))
    sm = sm.filter(ImageFilter.GaussianBlur(18))
    lum += np.asarray(sm, np.float32) / 255 * 0.9
    # fine scratches
    sc = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(sc)
    for _ in range(70):
        x0, y0 = r.uniform(0, S), r.uniform(0, S)
        a = r.uniform(-0.4, 0.4) + (math.pi / 2 if r.random() < 0.3 else 0)
        L = r.uniform(10, 60)
        d.line((x0, y0, x0 + L * math.cos(a), y0 + L * math.sin(a)), fill=r.randint(40, 90), width=1)
    lum += np.asarray(sc.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255 * 0.35
    lum = np.clip(lum, 0, 1)
    Image.fromarray((lum * 255).astype(np.uint8)).convert("RGB").save(os.path.join(OUT, name + ".png"))


def bar_fill(W=512, H=64, name="bar_fill", seed=25):
    """horizontally tileable veined fill (blood / ink)"""
    n = fbm(W, H, seed, base=32, octaves=5)
    streak = fbm(W, H * 8, seed + 3, base=64, octaves=4)[::8, :]
    y = np.mgrid[0:H, 0:W][0].astype(np.float32)
    v = 1 - np.abs((y - H / 2) / (H / 2)) ** 2 * 0.55
    lum = (0.45 + 0.4 * n + 0.25 * streak) * v
    hl = np.exp(-((y - H * 0.28) ** 2) / 20) * 0.18
    lum = np.clip(lum + hl, 0, 1)
    Image.fromarray((lum * 255).astype(np.uint8)).convert("RGB").save(os.path.join(OUT, name + ".png"))


def divider(W=512, H=48, name="divider", seed=29):
    p = Pen(W, H)
    c, m = W / 2, H / 2
    p.stroke([(20, m), (c - 26, m)], 0.6, 2.4)
    p.stroke([(c + 26, m), (W - 20, m)], 2.4, 0.6)
    p.poly(diamond(c, m, 11))
    p.dot(c, m, 3, 0)
    p.poly(diamond(c - 22, m, 4.5))
    p.poly(diamond(c + 22, m, 4.5))
    p.stroke(spiral(c - 40, m - 8, 6, 1.4, math.pi / 2, math.pi * 1.4), 1.6, 0.8)
    p.stroke(spiral(c + 40, m - 8, 6, 1.4, math.pi / 2, -math.pi * 1.4), 1.6, 0.8)
    p.stroke(spiral(c - 40, m + 8, 6, 1.4, -math.pi / 2, -math.pi * 1.4), 1.6, 0.8)
    p.stroke(spiral(c + 40, m + 8, 6, 1.4, -math.pi / 2, math.pi * 1.4), 1.6, 0.8)
    a = wear(np.asarray(p.result(), np.float32), seed, 0.25)
    to_rgba(a, seed).save(os.path.join(OUT, name + ".png"))


def knob(S=64, name="knob", seed=31):
    p = Pen(S, S)
    c = S / 2
    p.poly(diamond(c, c, 24))
    p.poly(diamond(c, c, 15), 0)
    p.poly(diamond(c, c, 9))
    a = np.asarray(p.result(), np.float32)
    to_rgba(a, seed, 0.15).save(os.path.join(OUT, name + ".png"))


def soft_shadow(S=128, name="shadow", seed=0):
    """9-slice soft dark glow for drop shadows"""
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    e = 40
    dx = np.maximum(np.maximum(e - x, x - (S - 1 - e)), 0)
    dy = np.maximum(np.maximum(e - y, y - (S - 1 - e)), 0)
    d = np.hypot(dx, dy) / e
    a = np.clip(1 - d, 0, 1) ** 2
    Image.merge("RGBA", [Image.fromarray(np.zeros((S, S), np.uint8))] * 3 +
                [Image.fromarray((a * 255).astype(np.uint8))]).save(os.path.join(OUT, name + ".png"))


if __name__ == "__main__":
    ornate_frame()
    thin_frame()
    bar_frame()
    orb_ring()
    orb_fill()
    wax_seal()
    bell()
    panel_bg()
    bar_fill()
    divider()
    knob()
    soft_shadow()
    # contact sheet on dark bg for review
    files = ["frame_ornate", "frame_thin", "bar_frame", "orb_ring", "orb_fill", "seal", "bell", "panel_bg", "bar_fill", "divider", "knob", "shadow"]
    sheet = Image.new("RGBA", (1400, 900), (14, 12, 18, 255))
    x, y, rowh = 10, 10, 0
    for f in files:
        im = Image.open(os.path.join(OUT, f + ".png")).convert("RGBA")
        if im.width > 520:
            im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        if x + im.width > 1390:
            x, y, rowh = 10, y + rowh + 10, 0
        sheet.alpha_composite(im, (x, y))
        x += im.width + 10
        rowh = max(rowh, im.height)
    sheet.save(os.path.join(OUT, "_sheet.png"))
    print("ok")
