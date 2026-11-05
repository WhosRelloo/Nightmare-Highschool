"""PBR phone-app icons for the Nightmare Highschool phone (Theme.Images.IconApp*), baked to images.

One family with IconReport (make_report_icon.py): every icon is a height field with per-pixel albedo / roughness /
metalness, lit once in full PBR by make_health_pbr.shade (GGX specular, Lambert diffuse, a warm key, a cool fill, a candle
rim, an environment reflection, AO from the height), then reduced to luminance with alpha. The game tints them with
ImageColor3 (pale gold / bone on an ink tile), so the art is GREYSCALE and all tonal contrast comes from the relief and
from albedo (bone paper and wax light, ink and recesses dark).

Shared rules so the family matches IconReport: the main body sits at height 0.20 with a 0.16 rounded bevel over ~26 px
(at the 1024 work size), parts laid on top cast a soft contact shadow, inked marks are raised 0.035 + 0.075 over 7 px
with albedo 0.20, engraved lines are 12 px grooves 0.07 deep, the work size is 1024 saved at 512 and 256.

    python make_app_icons.py             # all fourteen
    python make_app_icons.py Wisp Hex    # just some (name without the IconApp prefix)
Writes art/ui/hud/out/app_icons/<Name>.png (512), <Name>_256.png and contact_sheet.png (all fifteen with IconReport,
tinted pale gold on dark ink tiles at 60 px and 128 px, laid out like the phone's home screen).
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as H

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "app_icons"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = HERE / "out" / "report_icon" / "IconReport.png"
S = 1024                      # work size; saved at 512 (and 256)
SS = 3                        # supersampling for PIL-drawn masks
FONT = "C:/Windows/Fonts/georgiab.ttf"
f32 = np.float32

yy, xx = np.mgrid[0:S, 0:S].astype(f32)

# albedo palette (greyscale; the game tints)
PAPER, BONE, WAX, INK = 0.86, 0.80, 0.70, 0.20
LEATHER, STONE, IRON, BRASS, CLOTH = 0.52, 0.72, 0.62, 0.82, 0.78
MET = 0.3                     # brass and iron: part metal, so they keep a diffuse body under the reflection


# ============================================================ helpers (same as make_report_icon.py)
def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def blur_noise(sigma, seed):
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.random((S, S)).astype(f32), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def draw(fn):
    """Draw with PIL at SS x and box-filter down: an anti-aliased 0..1 mask."""
    m = Image.new("L", (S * SS, S * SS), 0)
    fn(ImageDraw.Draw(m), SS)
    return np.array(m.resize((S, S), Image.BOX), f32) / 255.0


def inner_dist(m):
    return (ndimage.distance_transform_edt(m > 0.5) + (m - 0.5) * (m < 1)).astype(f32)


def rotate(a, deg, cx, cy):
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    dx, dy = xx - cx, yy - cy
    sx = c * dx + s * dy + cx
    sy = -s * dx + c * dy + cy
    return ndimage.map_coordinates(a, [sy, sx], order=1, mode="constant", cval=0.0).astype(f32)


# ============================================================ shapes (all in 1024 px work space)
def M(sd):
    """Signed distance (negative inside) -> anti-aliased mask."""
    return np.clip(0.5 - sd, 0, 1).astype(f32)


def local(cx, cy, rot=0.0):
    """Local coordinates of every pixel for a shape centred at (cx, cy), turned `rot` degrees (clockwise on screen)."""
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    dx, dy = xx - cx, yy - cy
    return c * dx + s * dy, -s * dx + c * dy


def to_world(cx, cy, rot, u, v):
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    return cx + c * u - s * v, cy + s * u + c * v


def sd_circle(cx, cy, r):
    return np.hypot(xx - cx, yy - cy) - r


def circle(cx, cy, r):
    return M(sd_circle(cx, cy, r))


def ring(cx, cy, r, w):
    return M(np.abs(sd_circle(cx, cy, r)) - w / 2)


def sd_box(cx, cy, w, h, r=0.0, rot=0.0):
    u, v = local(cx, cy, rot)
    qx, qy = np.abs(u) - (w / 2 - r), np.abs(v) - (h / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def box(cx, cy, w, h, r=0.0, rot=0.0):
    return M(sd_box(cx, cy, w, h, r, rot))


def sd_ellipse(cx, cy, rx, ry, rot=0.0):
    u, v = local(cx, cy, rot)
    k = np.hypot(u / rx, v / ry) + 1e-6
    g = np.hypot(u / (rx * rx), v / (ry * ry)) / k + 1e-6
    return (k - 1) / g


def ellipse(cx, cy, rx, ry, rot=0.0):
    return M(sd_ellipse(cx, cy, rx, ry, rot))


def sd_seg(x0, y0, x1, y1):
    px, py = xx - x0, yy - y0
    dx, dy = x1 - x0, y1 - y0
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
    return np.hypot(px - t * dx, py - t * dy)


def seg(x0, y0, x1, y1, w):
    return M(sd_seg(x0, y0, x1, y1) - w / 2)


def poly(pts):
    return draw(lambda d, k: d.polygon([(x * k, y * k) for x, y in pts], fill=255))


def text(s, size, cx, cy, rot=0.0):
    font = ImageFont.truetype(FONT, int(size * SS))
    m = draw(lambda d, k: d.text((cx * k, cy * k), s, font=font, fill=255, anchor="mm"))
    return rotate(m, rot, cx, cy) if rot else m


def U(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = np.maximum(out, m)
    return out


def sub(a, *bs):
    for b in bs:
        a = a * (1 - b)
    return a


def bez(p0, p1, p2, p3, n=48):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, f32) for p in (p0, p1, p2, p3))
    pts = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(p) for p in pts]


def ngon_facets(cx, cy, R, n, rot0=0.0):
    """Distance inside a regular n-gon to its nearest edge (per facet planes): for faceted gems."""
    best = None
    ap = R * math.cos(math.pi / n)
    for k in range(n):
        a = rot0 + (k + 0.5) * 2 * math.pi / n
        d = ap - ((xx - cx) * math.cos(a) + (yy - cy) * math.sin(a))
        best = d if best is None else np.minimum(best, d)
    return best


# ============================================================ the icon: layered relief, then shaded
class Icon:
    def __init__(self, seed):
        self.h = np.zeros((S, S), f32)
        self.alb = np.full((S, S), 0.8, f32)
        self.rough = np.full((S, S), 0.55, f32)
        self.metal = np.zeros((S, S), f32)
        self.alpha = np.zeros((S, S), f32)
        self.cast = np.zeros((S, S), f32)
        self.seed, self.k = seed, 0

    def noise(self, sigma):
        self.k += 1
        return blur_noise(sigma, self.seed * 1000 + self.k)

    def custom(self, m, h, alb, rough, metal=0.0, cast=True):
        """Lay a part with its own height map on top of what's there (with a contact shadow on what's below)."""
        if cast:
            sh = ndimage.gaussian_filter(np.roll(np.roll(m, 10, 0), 6, 1), 9)
            self.cast = np.maximum(self.cast * (1 - m), sh * (1 - m) * np.clip(self.alpha * 4, 0, 1))
        else:
            self.cast *= 1 - m
        self.h = self.h * (1 - m) + h * m
        self.alb = self.alb * (1 - m) + alb * m
        self.rough = self.rough * (1 - m) + rough * m
        self.metal = self.metal * (1 - m) + metal * m
        self.alpha = np.maximum(self.alpha, m)

    def part(self, m, z=0.20, lift=0.16, bevel=26, alb=PAPER, rough=0.55, metal=0.0, cast=True, tex=0.012,
             mottle=0.07):
        h = z + lift * H.dome(inner_dist(m), bevel) + tex * self.noise(2.0) + tex * 1.6 * self.noise(14)
        a = alb * (1 - mottle + mottle * self.noise(3)) if mottle else alb
        self.custom(m, h, a, rough, metal, cast)

    def groove(self, m, depth=0.07, dark=0.10):
        self.h -= m * depth
        self.alb *= 1 - dark * m

    def emboss(self, m, lift=0.08, bevel=8, alb=None, rough=None, metal=None):
        self.h += m * lift * H.dome(inner_dist(m), bevel)
        self._mat(m, alb, rough, metal)

    def recess(self, m, depth=0.10, bevel=8, alb=None, rough=None, metal=None):
        self.h -= m * depth * H.dome(inner_dist(m), bevel)
        self._mat(m, alb, rough, metal)

    def ink(self, m):
        self.h += m * (0.035 + 0.075 * H.dome(inner_dist(m), 7))
        self._mat(m, INK, 0.35, 0.0)

    def _mat(self, m, alb, rough, metal):
        if alb is not None:
            self.alb = self.alb * (1 - m) + alb * m
        if rough is not None:
            self.rough = self.rough * (1 - m) + rough * m
        if metal is not None:
            self.metal = self.metal * (1 - m) + metal * m

    def render(self):
        height = ndimage.gaussian_filter(self.h, 0.8)
        alb = H.srgb_to_lin(np.dstack([np.clip(self.alb, 0, 1)] * 3).astype(f32))
        micro = np.dstack([self.noise(1.5) - 0.5, self.noise(1.5) - 0.5, np.zeros((S, S), f32)]).astype(f32)
        N = H.normals_from(height * S * 0.5, 1.0 / 7.5, micro, 0.25)
        ao = H.ao_from(height, 10, 5) * H.ao_from(height, 3, 9)
        ao *= 1 - 0.8 * self.cast
        rgb = H.shade(alb, N, np.clip(self.rough, 0.06, 1), np.clip(self.metal, 0, 1), ao)
        lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.55 + rgb[..., 2] * 0.15
        return np.clip((lum - 0.04) * 1.25, 0, 1), np.clip(self.alpha, 0, 1)


def wax_seal(ic, cx, cy, r, z=0.42, lobes=12, alb=WAX):
    """The kit's wax seal, small: scalloped rim, raised lip, a pressed stamp with a ring and the diamond emblem."""
    X, Y = (xx - cx) / r, (yy - cy) / r
    R = np.hypot(X, Y)
    TH = np.arctan2(Y, X)
    inside = R / (1.0 + 0.045 * np.cos(lobes * TH))
    m = smooth(1.0, 1.0 - 1.6 / r, inside)
    to_edge = np.clip(1 - inside, 0, 1)
    h = H.dome(np.clip(to_edge * 4, 0, 1), 1.0) * 0.36 + ic.noise(10) * 0.02
    h += 0.10 * np.exp(-((to_edge - 0.11) / 0.045) ** 2)
    stamp = smooth(0.72, 0.68, R)
    h -= 0.10 * stamp
    h += 0.09 * np.exp(-((R - 0.62) / 0.03) ** 2) * stamp
    diam = np.abs(X) + np.abs(Y)
    h += smooth(0.06, 0.025, np.abs(diam - 0.40)) * 0.09 * stamp
    h += H.dome(np.clip((0.22 - diam) / 0.22, 0, 1), 1.0) * 0.10
    ic.custom(m, z + h, alb * (0.92 + 0.08 * ic.noise(3)), 0.2, 0.0)
    return m


# ============================================================ the fourteen icons
def bell_pts(cx, cy, s, rot=0.0):
    """A school bell outline (unit height ~ s): crown, shoulders, flared lip."""
    left, right = [], []
    for t in np.linspace(0, 1, 30):
        v = -0.36 + 0.70 * t
        w = 0.20 + 0.10 * t + 0.22 * t ** 5
        left.append((-w, v))
        right.append((w, v))
    pts = [(-0.10, -0.42), (0.10, -0.42)] + right + [(0.52, 0.38), (-0.52, 0.38)] + left[::-1]
    return [to_world(cx, cy, rot, u * s, v * s) for u, v in pts]


def bell(cx, cy, s, rot=0.0):
    body = poly(bell_pts(cx, cy, s, rot))
    crown = M(np.abs(sd_circle(*to_world(cx, cy, rot, 0, -0.50 * s), 0.08 * s)) - 0.035 * s)
    clap = circle(*to_world(cx, cy, rot, 0, 0.48 * s), 0.085 * s)
    return U(body, crown, clap)


def gazette():
    ic = Icon(1)
    ic.part(box(560, 470, 590, 700, 10, 7), z=0.12, alb=PAPER * 0.88)               # the sheet behind
    cx, cy, rot = 494, 536, -5
    front = box(cx, cy, 600, 720, 10, rot)
    ic.part(front)
    W = lambda u, v: to_world(cx, cy, rot, u, v)
    rules = U(box(*W(0, -305), 520, 14, 7, rot), box(*W(0, -150), 520, 14, 7, rot))
    title = U(box(*W(-170, -228), 150, 40, 20, rot), box(*W(170, -228), 150, 40, 20, rot),
              bell(*W(0, -230), 140, rot))
    head = box(*W(0, -92), 520, 46, 23, rot)
    pic = box(*W(-128, 38), 264, 176, 8, rot)
    moon = sub(circle(*W(-170, 10), 46), circle(*W(-150, -2), 42))
    pic = sub(pic, moon)
    lines = U(*[box(*W(146, v), 228, 26, 13, rot) for v in (-28, 26, 80, 126)])
    lines = U(lines, *[box(*W(-20 if v == 250 else 0, v), 480 if v == 250 else 520, 26, 13, rot) for v in (196, 250)])
    ic.ink(U(rules, title, head, pic, lines))
    return ic


def timetable():
    ic = Icon(2)
    cx, cy, R = 512, 584, 330
    ic.part(ring(cx, 150, 60, 30), z=0.20, lift=0.14, bevel=14, alb=BRASS, rough=0.32, metal=MET)   # the bow
    stem = U(box(cx, 226, 74, 62, 12), box(cx, 262, 40, 40, 6))
    ic.part(stem, z=0.22, lift=0.12, bevel=12, alb=BRASS, rough=0.35, metal=MET)
    for x in (-24, -8, 8, 24):
        ic.groove(box(cx + x, 226, 6, 50, 3), 0.05)
    ic.part(circle(cx, cy, R), alb=BRASS, rough=0.32, metal=MET, bevel=40, lift=0.2)               # the case
    ic.groove(ring(cx, cy, R - 62, 10))
    ic.emboss(U(*[circle(cx + (R - 30) * math.cos(t), cy + (R - 30) * math.sin(t), 9)
                  for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]), 0.05, 8)
    face = circle(cx, cy, R - 72)
    ic.custom(face, 0.26 + 0.01 * ic.noise(14), PAPER * (0.94 + 0.06 * ic.noise(3)), 0.6, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - face, 8, 0), 5, 1), 8) * face)
    marks = []
    for i, numeral in ((0, "XII"), (3, "III"), (6, "VI"), (9, "IX")):
        a = i * math.pi / 6 - math.pi / 2
        marks.append(text(numeral, 84 if i else 76, cx + math.cos(a) * 178, cy + math.sin(a) * 178 + 4))
    for i in range(12):
        if i % 3:
            a = i * math.pi / 6 - math.pi / 2
            c, s = math.cos(a), math.sin(a)
            marks.append(seg(cx + c * 180, cy + s * 180, cx + c * 216, cy + s * 216, 20))
    ic.ink(U(*marks))
    hands = []
    for ang, ln, w in ((-55, 150, 34), (60, 226, 24)):                           # ten past ten (hour, minute)
        ux, uy = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
        tipx, tipy = cx + ux * ln, cy + uy * ln
        hands.append(seg(cx, cy, cx + ux * (ln - 40), cy + uy * (ln - 40), w))
        px, py = -uy, ux
        bx, by = cx + ux * (ln - 64), cy + uy * (ln - 64)
        hands.append(poly([(bx + px * w * 0.95, by + py * w * 0.95), (tipx, tipy), (bx - px * w * 0.95, by - py * w * 0.95),
                           (cx + ux * (ln - 90), cy + uy * (ln - 90))]))
    hm = U(*hands)
    ic.custom(hm, ic.h + (0.06 + 0.06 * H.dome(inner_dist(hm), 7)) * hm, INK, 0.3, 0.0)
    ic.part(circle(cx, cy, 34), z=0.40, lift=0.08, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    return ic


def study_group():
    ic = Icon(3)
    # bottom book: spine facing us, with raised bands and a title label
    b1 = box(486, 800, 690, 130, 22)
    ic.part(b1, alb=LEATHER, lift=0.2, bevel=48, tex=0.018)
    gilt = U(*[box(x, 800, 22, 124, 6) for x in (200, 236, 736, 772)])
    ic.emboss(gilt, 0.07, 8, alb=BRASS, rough=0.3, metal=MET)
    ic.ink(box(486, 800, 250, 46, 10))
    ic.emboss(box(486, 800, 210, 12, 6), 0.03, 4, alb=BRASS, rough=0.3)
    # middle book: the page edge facing us, between the covers
    b2 = box(508, 666, 610, 132, 18, -2)
    ic.part(b2, z=0.24, alb=LEATHER * 1.1, lift=0.18, bevel=30, tex=0.018)
    pages = box(520, 666, 560, 84, 6, -2)
    ic.recess(pages, 0.03, 6, alb=PAPER, rough=0.7)
    for v in (-22, 0, 22):
        ic.groove(seg(*to_world(520, 666, -2, -270, v), *to_world(520, 666, -2, 272, v), 5), 0.03, 0.12)
    # top book: spine again, tilted the other way
    b3 = box(452, 530, 520, 118, 20, 4)
    ic.part(b3, z=0.28, alb=LEATHER * 0.9, lift=0.2, bevel=46, tex=0.018)
    ic.emboss(U(*[box(*to_world(452, 530, 4, u, 0), 20, 112, 6, 4) for u in (-206, -174, 174, 206)]), 0.07, 8,
              alb=BRASS, rough=0.3, metal=MET)
    ic.ink(box(452, 530, 200, 42, 10, 4))
    # the candle on a brass dish, standing on the top book
    ic.part(ellipse(664, 464, 118, 30), z=0.40, lift=0.1, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    candle = U(box(664, 330, 116, 250, 14), ellipse(664, 210, 58, 16))
    drip = U(seg(626, 212, 626, 290, 26), circle(626, 292, 15))
    ic.part(U(candle, drip), z=0.44, lift=0.14, bevel=22, alb=PAPER, rough=0.4)
    ic.ink(seg(664, 206, 664, 176, 12))
    flame = poly(bez((664, 70), (700, 120), (720, 186), (664, 186)) + bez((664, 186), (608, 186), (628, 120), (664, 70)))
    ic.part(flame, z=0.50, lift=0.14, bevel=30, alb=1.0, rough=0.25, cast=False)
    ic.recess(poly(bez((664, 128), (680, 150), (686, 176), (664, 176)) + bez((664, 176), (642, 176), (648, 150), (664, 128))),
              0.04, 10, alb=0.7)
    return ic


def cliques():
    ic = Icon(4)
    bx, by = 512, 900
    tips = [(232, 196), (512, 120), (792, 196)]
    for tx, ty in tips:
        ic.part(seg(bx, by, tx, ty, 32), z=0.18, lift=0.12, bevel=12, alb=IRON, rough=0.4, metal=MET)
    # the side pennants, streaming outward
    for (tx, ty), side, emb in ((tips[0], -1, "moon"), (tips[2], 1, "quat")):
        dx, dy = (tx - bx), (ty - by)
        L = math.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        nx, ny = -dy * side * -1, dx * side * -1
        if nx * side < 0:
            nx, ny = -nx, -ny
        p1 = (tx - dx * 40, ty - dy * 40)
        p2 = (tx - dx * 330, ty - dy * 330)
        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        tip = (mid[0] + nx * 300 - dx * 60, mid[1] + ny * 300 - dy * 60)
        flag = poly(bez(p1, (p1[0] + nx * 120, p1[1] + ny * 120 - 20), (tip[0] - nx * 80, tip[1] - 10), tip)
                    + bez(tip, (tip[0] - nx * 90, tip[1] + 30), (p2[0] + nx * 120, p2[1] + ny * 120 + 10), p2))
        ic.part(flag, z=0.26, lift=0.14, bevel=20, alb=CLOTH, rough=0.7)
        ic.groove(sub(edge_line(flag, 24), edge_line(flag, 14)), 0.04)
        ex, ey = mid[0] + nx * 105 - dx * 10, mid[1] + ny * 105 - dy * 10
        if emb == "moon":
            e = sub(circle(ex, ey, 48), circle(ex + 22 * side * -1, ey - 14, 42))
        else:
            e = U(*[circle(ex + 22 * math.cos(b), ey + 22 * math.sin(b), 22) for b in np.arange(4) * math.pi / 2])
        ic.ink(e)
    # the middle gonfalon on a crossbar
    ic.part(seg(372, 214, 652, 214, 24), z=0.30, lift=0.12, bevel=10, alb=IRON, rough=0.4, metal=MET)
    ban = poly([(394, 226), (630, 226), (630, 560)] + bez((630, 560), (580, 530), (540, 520), (512, 500))
               + bez((512, 500), (484, 520), (444, 530), (394, 560)))
    ic.part(ban, z=0.30, lift=0.14, bevel=20, alb=CLOTH, rough=0.7)
    ic.groove(sub(edge_line(ban, 26), edge_line(ban, 16)), 0.04)
    d = np.abs(xx - 512) + np.abs(yy - 360)
    ic.ink(U(M(np.abs(d - 74) - 14), M(d - 34)))
    # the brass band gathering the poles and the finials
    ic.part(box(512, 790, 110, 54, 14), z=0.34, lift=0.12, bevel=14, alb=BRASS, rough=0.3, metal=MET)
    for tx, ty in tips:
        ic.part(circle(tx, ty, 30), z=0.34, lift=0.12, bevel=16, alb=BRASS, rough=0.3, metal=MET)
    ic.part(circle(372, 214, 20), z=0.38, lift=0.1, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    ic.part(circle(652, 214, 20), z=0.38, lift=0.1, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    return ic


def texts():
    ic = Icon(5)
    cx, cy, rot = 512, 548, -6
    W = lambda u, v: to_world(cx, cy, rot, u, v)
    env = box(cx, cy, 800, 540, 18, rot)
    ic.part(env)
    # the bottom folds: two grooves meeting under the flap
    for u0 in (-390, 390):
        ic.groove(seg(*W(u0, 255), *W(u0 * 0.25, 30), 12))
    flap = poly([W(-400, -270), W(400, -270), W(0, 60)])
    ic.part(sub(flap, 1 - env), z=0.30, lift=0.10, bevel=18, alb=PAPER * 0.96)
    wax_seal(ic, *W(0, 40), 140)
    return ic


def style():
    ic = Icon(6)
    hx, hy, rot = 424, 380, -25
    A = lambda u, v: to_world(hx, hy, rot, u, v)
    rx, ry = 228, 268
    # the handle: collar, shaft with bands, end knob
    ic.part(seg(*A(0, ry - 10), *A(0, ry + 290), 70), z=0.20, lift=0.14, bevel=20, alb=BRASS, rough=0.3, metal=MET)
    for v in (ry + 110, ry + 200):
        ic.part(box(*A(0, v), 104, 34, 14, rot), z=0.30, lift=0.1, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    ic.part(circle(*A(0, ry + 300), 54), z=0.30, lift=0.12, bevel=24, alb=BRASS, rough=0.3, metal=MET)
    ic.part(box(*A(0, ry + 12), 130, 54, 20, rot), z=0.30, lift=0.1, bevel=14, alb=BRASS, rough=0.3, metal=MET)
    # the frame with a finial, and a bead course
    fin = U(circle(*A(0, -ry - 30), 34), circle(*A(-40, -ry - 2), 26), circle(*A(40, -ry - 2), 26))
    ic.part(fin, z=0.24, lift=0.12, bevel=14, alb=BRASS, rough=0.3, metal=MET)
    frame = ellipse(hx, hy, rx, ry, rot)
    ic.part(frame, z=0.24, alb=BRASS, rough=0.3, metal=MET, bevel=26)
    beads = []
    for k in range(28):
        t = k / 28 * 2 * math.pi
        beads.append(circle(*A((rx - 26) * math.cos(t), (ry - 26) * math.sin(t)), 11))
    ic.emboss(U(*beads), 0.06, 10)
    glass = ellipse(hx, hy, rx - 54, ry - 54, rot)
    ic.custom(glass, 0.30 + 0.03 * H.dome(inner_dist(glass), 40), 0.30, 0.06, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - glass, 10, 0), 6, 1), 9) * glass)
    u, v = local(hx, hy, rot)
    streak = (smooth(30, 20, np.abs(u * 0.7 + v * 0.7 + 60)) + smooth(14, 8, np.abs(u * 0.7 + v * 0.7 - 40)) * 0.8)
    ic._mat(streak * glass, 0.95, 0.1, None)
    return ic


def options():
    ic = Icon(7)
    cx, cy = 512, 512
    n, root, tip = 10, 352, 430
    pts = []
    for th in np.linspace(0, 2 * math.pi, 2000, endpoint=False):
        f = (th * n / (2 * math.pi) + 0.17) % 1
        if f < 0.30:
            r = tip
        elif f < 0.42:
            r = tip - (tip - root) * (f - 0.30) / 0.12
        elif f < 0.88:
            r = root
        else:
            r = root + (tip - root) * (f - 0.88) / 0.12
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    gear = poly(pts)
    holes = [circle(cx, cy, 78)]
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        hw, uS, u0, u1 = 50, 262, 182, 318
        loc = [(u0, -hw), (uS, -hw)]
        for ph in np.linspace(0, math.pi / 3, 14):
            loc.append((uS + (u1 - uS) * math.sin(ph) / math.sin(math.pi / 3), hw - 2 * hw * math.cos(ph)))
        for ph in np.linspace(math.pi / 3, 0, 14):
            loc.append((uS + (u1 - uS) * math.sin(ph) / math.sin(math.pi / 3), -hw + 2 * hw * math.cos(ph)))
        loc += [(uS, hw), (u0, hw)]
        ca, sa = math.cos(a), math.sin(a)
        holes.append(poly([(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in loc]))
    body = sub(gear, *holes)
    ic.part(body, alb=IRON, rough=0.38, metal=MET, bevel=24)
    ic.part(sub(ring(cx, cy, 128, 92), holes[0]), z=0.30, lift=0.14, bevel=22, alb=IRON * 1.1, rough=0.32, metal=MET)
    ic.emboss(U(*[circle(cx + 128 * math.cos(t), cy + 128 * math.sin(t), 13)
                  for t in np.linspace(0, 2 * math.pi, 6, endpoint=False)]), 0.07, 10, alb=BRASS)
    ic.groove(ring(cx, cy, 340, 12))
    return ic


def wisp():
    ic = Icon(8)
    # wings, behind the flame: three swept feathers a side, each with a vein
    for side in (-1, 1):
        ox, oy = 512 + side * 160, 580
        for k, (ang, ln) in enumerate(((-18, 230), (-40, 215), (-62, 180))):
            a = math.radians(ang)
            dx, dy = math.cos(a) * side, math.sin(a)
            ex, ey = ox + dx * ln, oy + dy * ln
            f = ellipse((ox + ex) / 2, (oy + ey) / 2, ln * 0.55, 46, math.degrees(math.atan2(dy, dx)))
            ic.part(f, z=0.16 + 0.03 * k, lift=0.14, bevel=26, alb=BONE, rough=0.45)
            ic.groove(seg(ox + dx * ln * 0.2, oy + dy * ln * 0.2, ox + dx * ln * 0.88, oy + dy * ln * 0.88, 8) * f, 0.04)
    # the flame: a round belly drawn up into a tip that curls right, with one tongue on the left
    path = (bez((512, 812), (620, 812), (702, 730), (702, 620)) + bez((702, 620), (702, 470), (600, 410), (594, 300))
            + bez((594, 300), (588, 220), (612, 160), (660, 104)) + bez((660, 104), (540, 150), (470, 236), (470, 330))
            + bez((470, 330), (440, 300), (404, 262), (386, 196)) + bez((386, 196), (326, 330), (322, 470), (322, 620))
            + bez((322, 620), (322, 730), (404, 812), (512, 812)))
    flame = poly(path)
    ic.part(flame, z=0.22, lift=0.22, bevel=80, alb=1.0, rough=0.3)
    # an engraved inner flame line, the eyes
    core = poly(bez((512, 760), (590, 760), (640, 704), (640, 630)) + bez((640, 630), (640, 540), (580, 500), (560, 420))
                + bez((560, 420), (500, 470), (384, 540), (384, 630)) + bez((384, 630), (384, 704), (434, 760), (512, 760)))
    ic.groove(edge_line(core, 10), 0.06, 0.06)
    ic.recess(U(ellipse(458, 640, 30, 44, -8), ellipse(566, 640, 30, 44, 8)), 0.10, 14, alb=INK, rough=0.3)
    for (sx, sy, r) in ((770, 250, 36), (262, 300, 26), (720, 120, 20)):
        d = np.abs(xx - sx) + np.abs(yy - sy)
        ic.part(M((d - r) * 0.7), z=0.2, lift=0.12, bevel=10, alb=1.0, rough=0.3)
    return ic


def edge_line(m, w):
    """A line of width w just inside the edge of a mask (for engraved outlines)."""
    d = inner_dist(m)
    return (smooth(0, 1.5, d) * smooth(w + 1.5, w, d)).astype(f32)


RUNES = [
    [((0, -.5), (0, .5)), ((0, -.15), (.3, -.45))],
    [((0, -.5), (0, .5)), ((0, -.45), (.28, -.15)), ((.28, -.15), (0, .1))],
    [((-.25, -.5), (.25, .5)), ((.25, -.5), (-.25, .5))],
    [((-.22, .5), (0, -.5)), ((0, -.5), (.22, .5))],
    [((0, -.5), (0, .5)), ((0, 0), (.28, -.32)), ((0, 0), (-.28, -.32))],
    [((-.2, -.5), (-.2, .5)), ((.2, -.5), (.2, .5)), ((-.2, -.35), (.2, .05))],
    [((0, -.5), (.26, 0)), ((.26, 0), (0, .5)), ((0, .5), (-.26, 0)), ((-.26, 0), (0, -.5))],
    [((0, -.5), (0, .5)), ((-.26, -.5), (0, -.2)), ((.26, -.5), (0, -.2))],
]


def hex_slash():
    ic = Icon(9)
    cx, cy = 512, 512
    # the slash first, so the circle can be cut around it
    p0, p1, p2 = np.array((880, 150.)), np.array((640, 600.)), np.array((150, 880.))
    outer, inner = [], []
    for t in np.linspace(0, 1, 80):
        p = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
        d = 2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)
        nrm = np.array((-d[1], d[0])) / (np.linalg.norm(d) + 1e-6)
        w = 62 * math.sin(math.pi * t) ** 0.8
        outer.append(tuple(p + nrm * w))
        inner.append(tuple(p - nrm * w * 0.25))
    slash = poly(outer + inner[::-1])
    gap = M(ndimage.distance_transform_edt(slash < 0.5) - 26)
    band = sub(M(np.maximum(np.hypot(xx - cx, yy - cy) - 410, 300 - np.hypot(xx - cx, yy - cy))), gap)
    ic.part(band, alb=STONE, rough=0.55, bevel=22)
    ic.groove(sub(U(ring(cx, cy, 392, 8), ring(cx, cy, 318, 8)), gap), 0.05)
    glyphs = []
    for i, g in enumerate(RUNES):
        th = i * math.pi / 4 + math.pi / 8 - math.pi / 2
        ca, sa = math.cos(th), math.sin(th)
        Hg = 74
        for (ax, ay), (bx, by) in g:
            P = lambda gx, gy: (cx + (355 - gy * Hg) * ca - gx * Hg * sa, cy + (355 - gy * Hg) * sa + gx * Hg * ca)
            glyphs.append(seg(*P(ax, ay), *P(bx, by), 20))
    ic.ink(U(*glyphs) * band)
    inner_ring = sub(ring(cx, cy, 236, 34), gap)
    ic.part(inner_ring, z=0.20, lift=0.14, bevel=14, alb=STONE, rough=0.55)
    d = np.abs(xx - cx) + np.abs(yy - cy)
    ic.part(sub(circle(cx, cy, 120), gap), z=0.20, lift=0.18, bevel=40, alb=STONE * 0.95, rough=0.5)
    ic.ink(sub(ring(cx, cy, 70, 18), gap))
    ic.part(slash, z=0.34, lift=0.18, bevel=40, alb=1.0, rough=0.18)
    return ic


def crypt():
    ic = Icon(10)
    stone = U(box(512, 560, 500, 420, 8), circle(512, 360, 250))
    stone = stone * (yy > 100)
    ic.part(stone, alb=STONE, rough=0.75, tex=0.02, bevel=26)
    border = M(np.abs(np.minimum(sd_box(512, 560, 420, 340, 4), sd_circle(512, 360, 210)) * 1.0) - 6)
    border *= (yy < 742)
    ic.groove(border, 0.07)
    cross = U(seg(512, 268, 512, 600, 54), seg(424, 380, 600, 380, 54))
    ic.recess(cross, 0.12, 10, alb=STONE * 0.55)
    ic.part(box(512, 800, 660, 92, 14), z=0.22, lift=0.14, bevel=20, alb=STONE * 0.9, rough=0.75, tex=0.02)
    # three gems in front: round (octagon), diamond, square
    for (gx, gy, R, n, r0) in ((300, 830, 98, 8, math.pi / 8), (512, 846, 118, 4, 0.0), (724, 830, 96, 4, math.pi / 4)):
        fac = ngon_facets(gx, gy, R, n, r0)
        m = M(-fac)
        ap = R * math.cos(math.pi / n)
        t = np.clip(fac / (ap * 0.5), 0, 1)
        h = 0.42 + 0.26 * t
        alb = 0.30 + 0.5 * smooth(0.97, 1.0, t)
        ic.custom(m, h, alb, 0.07, 0.0)
        ic.groove(M(np.abs(fac - ap * 0.5) - 2.5) * m, 0.0, -0.6)
    return ic


def wallet():
    ic = Icon(11)
    pouch = poly(bez((262, 360), (150, 520), (170, 880), (470, 880)) + bez((470, 880), (770, 880), (790, 520), (678, 360)))
    ic.part(pouch, alb=LEATHER * 1.05, rough=0.6, tex=0.022, lift=0.22, bevel=110)
    pd = inner_dist(pouch)
    stitch = smooth(7, 3, np.abs(pd - 40)) * (yy > 400) * (np.sin(np.arctan2(yy - 600, xx - 470) * 64) > -0.2)
    ic.groove(stitch, 0.05, 0.25)
    for x0, x1 in ((380, 340), (470, 470), (560, 600)):
        ic.groove(seg(x0, 380, x1, 470, 10), 0.05)
    ic.part(seg(250, 360, 690, 360, 52), z=0.30, lift=0.12, bevel=16, alb=BRASS, rough=0.3, metal=MET)
    for x in (434, 506):
        ic.part(circle(x, 296, 40), z=0.34, lift=0.14, bevel=24, alb=BRASS, rough=0.3, metal=MET)
    # coins: one behind, one in front with the yen mark
    ic.part(circle(790, 640, 150), z=0.34, lift=0.12, bevel=18, alb=BRASS * 0.9, rough=0.3, metal=MET)
    ic.groove(ring(790, 640, 122, 10))
    ic.part(circle(716, 740, 190), z=0.40, lift=0.14, bevel=22, alb=BRASS, rough=0.3, metal=MET)
    ic.groove(ring(716, 740, 156, 12))
    ic.emboss(text("\u00a5", 250, 716, 740), 0.09, 8, alb=0.42)
    return ic


def radio():
    ic = Icon(12)
    cx, spring, sq = 512, 470, 0.72

    def arch_sd(half, inset):
        """Pointed arch (two circles, squashed) over a box; signed distance-ish."""
        rr = half * 1.4
        oy = (yy - spring) / sq
        a = np.hypot(xx - (cx - half + rr), oy) - (rr - inset)
        b = np.hypot(xx - (cx + half - rr), oy) - (rr - inset)
        top = np.maximum(a, b)
        top = np.where(yy < spring, top, -1e3)
        side = np.maximum(np.abs(xx - cx) - (half - inset), -1e3)
        return np.where(yy < spring, top, side)

    cab = M(np.maximum(arch_sd(300, 0), yy - 880))
    ic.part(cab, alb=LEATHER * 1.1, rough=0.5, tex=0.02)
    grille = M(np.maximum(arch_sd(300, 64), yy - 620))
    ic.recess(grille, 0.06, 8, alb=LEATHER)
    slots = (smooth(4, -4, np.abs(((xx - cx + 37) % 74) - 37) - 18)) * grille * M(np.maximum(arch_sd(300, 86), yy - 598))
    ic.recess(slots, 0.12, 6, alb=0.12, rough=0.6)
    ic.part(circle(cx, 728, 76), z=0.34, lift=0.08, bevel=14, alb=BRASS, rough=0.3, metal=MET)
    dial = circle(cx, 728, 56)
    ic.custom(dial, 0.36 + 0 * dial, PAPER, 0.6, 0.0, cast=False)
    ic.ink(U(seg(cx, 744, cx + 34, 690, 12), *[seg(cx + 44 * math.cos(a), 728 + 44 * math.sin(a), cx + 52 * math.cos(a),
                                                    728 + 52 * math.sin(a), 8) for a in np.linspace(-2.6, -0.5, 6)]))
    for x in (340, 684):
        ic.part(circle(x, 790, 50), z=0.34, lift=0.12, bevel=20, alb=BRASS, rough=0.3, metal=MET)
        ic.groove(ring(x, 790, 26, 8), 0.04)
    ic.part(box(cx, 900, 680, 56, 16), z=0.24, lift=0.12, bevel=16, alb=LEATHER * 0.9, rough=0.5)
    return ic


PROFILE = [(0.0, -0.62), (0.22, -0.56), (0.38, -0.40), (0.44, -0.20), (0.46, -0.10), (0.60, 0.06), (0.48, 0.12),
           (0.50, 0.18), (0.45, 0.23), (0.49, 0.29), (0.43, 0.40), (0.32, 0.48), (0.24, 0.52), (0.22, 0.76),
           (0.42, 0.92), (0.60, 1.12), (0.70, 1.7), (-0.70, 1.7), (-0.56, 1.06), (-0.30, 0.86), (-0.22, 0.62),
           (-0.30, 0.38), (-0.46, 0.08), (-0.44, -0.32), (-0.26, -0.56)]


def chaikin(pts, n=3):
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            p, q = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            out += [tuple(0.75 * p + 0.25 * q), tuple(0.25 * p + 0.75 * q)]
        pts = out
    return pts


def profile(cx, cy, s, face):
    """A cameo profile (head, neck and shoulders) facing right (face=1) or left (face=-1)."""
    return poly([(cx + face * u * s, cy + v * s) for u, v in chaikin(PROFILE)])


def contacts():
    ic = Icon(13)
    for (cx, cy, rx, ry, face, z) in ((388, 404, 222, 284, 1, 0.20), (642, 612, 236, 300, -1, 0.30)):
        frame = ellipse(cx, cy, rx, ry)
        ic.part(frame, z=z, alb=BRASS, rough=0.3, metal=MET, bevel=24)
        ic.emboss(U(*[circle(cx + (rx - 22) * math.cos(t), cy + (ry - 22) * math.sin(t), 10)
                      for t in np.linspace(0, 2 * math.pi, 30, endpoint=False)]), 0.06, 9)
        inner = ellipse(cx, cy, rx - 46, ry - 46)
        ic.custom(inner, z + 0.05 + 0.0 * inner, 0.30, 0.45, 0.0, cast=False)
        ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - inner, 9, 0), 5, 1), 8) * inner)
        s = ry * 0.62
        hx, hy = cx - face * 22, cy - ry * 0.26
        b = profile(hx, hy, s, face)
        if face > 0:                                     # hair up in a bun, tied with a ribbon
            b = U(b, circle(hx - 0.50 * s, hy - 0.40 * s, 0.25 * s))
        b *= inner
        ic.custom(b, z + 0.07 + 0.14 * H.dome(inner_dist(b), 30), BONE * 1.08, 0.45, 0.0, cast=True)
        if face > 0:
            ic.groove(seg(hx - 0.30 * s, hy - 0.52 * s, hx - 0.30 * s - 0.06 * s, hy - 0.16 * s, 9) * b, 0.05)
            ic.groove(edge_line(circle(hx - 0.50 * s, hy - 0.40 * s, 0.15 * s), 7) * b, 0.04)
        else:                                            # a blazer collar and a combed hairline
            ic.groove(U(seg(hx + face * 0.22 * s, hy + 0.80 * s, hx + face * 0.02 * s, hy + 1.18 * s, 10),
                        seg(hx - face * 0.26 * s, hy + 0.86 * s, hx + face * 0.02 * s, hy + 1.18 * s, 10)) * b, 0.06)
            ic.groove(poly_line([(hx + face * 0.36 * u * s, hy + v * s) for u, v in
                                 ((1.0, -0.42), (0.4, -0.30), (-0.3, -0.22), (-0.9, -0.05), (-1.1, 0.25))], 9) * b, 0.05)
    return ic


def poly_line(pts, w):
    return U(*[seg(*pts[i], *pts[i + 1], w) for i in range(len(pts) - 1)])


def camera():
    ic = Icon(14)
    ic.part(box(384, 300, 230, 120, 22), z=0.20, alb=BRASS, rough=0.3, metal=MET, bevel=18)        # viewfinder
    ic.recess(box(384, 296, 130, 52, 10), 0.08, 6, alb=0.15, rough=0.1)
    ic.part(U(box(700, 318, 36, 60, 8), ellipse(700, 290, 46, 18)), z=0.20, lift=0.12, bevel=12, alb=BRASS, rough=0.3,
            metal=MET)
    bodym = box(512, 590, 780, 480, 44)
    ic.part(bodym, alb=LEATHER, rough=0.7, tex=0.02)
    ic.part(box(512, 386, 780, 72, 30) * bodym, z=0.30, lift=0.08, bevel=12, alb=BRASS, rough=0.3, metal=MET, cast=True)
    stitch = M(np.abs(sd_box(512, 622, 724, 368, 24)) - 5) * (np.sin(xx * 0.31) + np.sin(yy * 0.31) > -0.6)
    ic.groove(stitch, 0.04, 0.25)                                                   # a stitched leather seam
    ic.part(circle(232, 480, 52), z=0.34, lift=0.08, bevel=10, alb=BRASS, rough=0.3, metal=MET)
    ic.recess(circle(232, 480, 34), 0.08, 8, alb=0.16, rough=0.1)
    ic.part(circle(560, 620, 210), z=0.32, lift=0.12, bevel=20, alb=BRASS, rough=0.3, metal=MET)
    ic.groove(ring(560, 620, 178, 12))
    ic.groove(U(*[seg(560 + 186 * math.cos(t), 620 + 186 * math.sin(t), 560 + 204 * math.cos(t), 620 + 204 * math.sin(t), 7)
                  for t in np.linspace(0, 2 * math.pi, 36, endpoint=False)]), 0.04)
    ic.part(circle(560, 620, 150), z=0.40, lift=0.1, bevel=16, alb=IRON, rough=0.35, metal=MET)
    glass = circle(560, 620, 104)
    ic.custom(glass, 0.42 + 0.06 * H.dome(inner_dist(glass), 60), 0.16, 0.05, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - glass, 9, 0), 5, 1), 8) * glass)
    ic.emboss(ellipse(518, 576, 34, 22, -40), 0.03, 10, alb=1.0, rough=0.1)
    ic.emboss(circle(612, 668, 12), 0.02, 6, alb=0.8, rough=0.1)
    return ic


ICONS = {
    "IconAppGazette": gazette, "IconAppTimetable": timetable, "IconAppGroup": study_group,
    "IconAppCliques": cliques, "IconAppTexts": texts, "IconAppStyle": style, "IconAppOptions": options,
    "IconAppWisp": wisp, "IconAppHex": hex_slash, "IconAppCrypt": crypt, "IconAppWallet": wallet,
    "IconAppRadio": radio, "IconAppContacts": contacts, "IconAppCamera": camera,
}
LABELS = {
    "IconReport": "Report Card", "IconAppGazette": "Midnight Bell", "IconAppTimetable": "Timetable",
    "IconAppGroup": "Study Group", "IconAppCliques": "Cliques", "IconAppTexts": "Texts", "IconAppStyle": "Style",
    "IconAppOptions": "Options", "IconAppWisp": "Wisp Flight", "IconAppHex": "Hex Slash", "IconAppCrypt": "Crypt Crush",
    "IconAppWallet": "Wallet", "IconAppRadio": "Night FM", "IconAppContacts": "Classmates", "IconAppCamera": "Camera",
}


def save(lum, alpha, name):
    a = np.dstack([lum, lum, lum, alpha]) * 255
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    big = im.resize((512, 512), Image.LANCZOS)
    big.save(OUT / f"{name}.png", optimize=True)
    im.resize((256, 256), Image.LANCZOS).save(OUT / f"{name}_256.png", optimize=True)
    return big


# ============================================================ contact sheet: the phone home screen
GOLD = np.array((232, 214, 168), f32) / 255
INKBG = (22, 19, 27, 255)
TILE = (36, 31, 42, 255)


def tile(im, size, inset=0.14):
    t = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(t).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=TILE,
                                        outline=(70, 60, 70, 255), width=max(1, size // 60))
    a = np.array(im.convert("RGBA"), f32)
    a[..., :3] *= GOLD
    ic = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    n = round(size * (1 - 2 * inset))
    ic = ic.resize((n, n), Image.LANCZOS)
    t.alpha_composite(ic, ((size - n) // 2, (size - n) // 2))
    return t


def contact_sheet():
    names = ["IconReport"] + list(ICONS)
    ims = {}
    for n in names:
        p = REPORT if n == "IconReport" else OUT / f"{n}.png"
        if p.exists():
            ims[n] = Image.open(p).convert("RGBA")
    try:
        lf = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
        lf2 = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
        hf = ImageFont.truetype(FONT, 18)
    except OSError:
        lf = lf2 = hf = ImageFont.load_default()
    cols = 4
    # left: a phone screen at 60 px; right: the same grid at 128 px
    t1, g1, lh1 = 60, 26, 18
    pw = cols * t1 + (cols + 1) * g1
    rows = math.ceil(len(names) / cols)
    ph = 60 + rows * (t1 + lh1 + 22) + 40
    t2, g2, lh2 = 128, 28, 22
    w2 = cols * t2 + (cols + 1) * g2
    h2 = 60 + rows * (t2 + lh2 + 20) + 20
    W = 40 + pw + 60 + w2 + 40
    Hh = max(ph, h2) + 60
    sheet = Image.new("RGBA", (W, Hh), (12, 10, 15, 255))
    d = ImageDraw.Draw(sheet)
    # phone body
    px0, py0 = 40, 50
    d.rounded_rectangle((px0 - 10, py0 - 10, px0 + pw + 10, py0 + ph + 10), radius=44, fill=(30, 26, 32, 255))
    d.rounded_rectangle((px0, py0, px0 + pw, py0 + ph), radius=36, fill=INKBG)
    d.text((px0 + pw / 2, py0 + 26), "11:58 PM", fill=(200, 190, 170, 255), font=lf, anchor="mm")
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x = px0 + g1 + c * (t1 + g1)
        y = py0 + 56 + r * (t1 + lh1 + 22)
        if n in ims:
            sheet.alpha_composite(tile(ims[n], t1), (x, y))
        d.text((x + t1 / 2, y + t1 + 10), LABELS[n], fill=(200, 190, 170, 255), font=lf2, anchor="mm")
    d.text((px0 + pw / 2, Hh - 24), "60 px tiles", fill=(150, 140, 130, 255), font=lf, anchor="mm")
    x2 = px0 + pw + 60
    d.text((x2 + w2 / 2, 30), "128 px tiles", fill=(150, 140, 130, 255), font=hf, anchor="mm")
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x = x2 + g2 + c * (t2 + g2)
        y = 60 + r * (t2 + lh2 + 20)
        if n in ims:
            sheet.alpha_composite(tile(ims[n], t2), (x, y))
        d.text((x + t2 / 2, y + t2 + 12), LABELS[n], fill=(200, 190, 170, 255), font=lf, anchor="mm")
    sheet.save(OUT / "contact_sheet.png")
    return OUT / "contact_sheet.png"


if __name__ == "__main__":
    want = sys.argv[1:]
    for name, fn in ICONS.items():
        if want and name.replace("IconApp", "") not in want and name not in want:
            continue
        lum, alpha = fn().render()
        save(lum, alpha, name)
        print("wrote", OUT / f"{name}.png")
    print("wrote", contact_sheet())
