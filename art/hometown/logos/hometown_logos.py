"""Wickfield logos and signs for the tutorial (docs/expansion/15-Tutorial-The-Last-Normal-Night.md §3). All original.

Each logo is drawn at 4x and averaged down, as layers: a mask, a fill (flat, gradient or texture), and a height value
(for the relief bake on the sign props). Out: art/hometown/logos/out/<Name>_color.png (RGBA) and <Name>_height.png
(16-bit grey), plus a contact sheet. Fonts: open-licence only (Chela One, Luckiest Guy, Balthazar, Aladin: SIL OFL /
Apache) and Georgia.

  python art/hometown/logos/hometown_logos.py [Name ...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
UF = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
FONTS = {
    "chela": os.path.join(UF, "ChelaOne-Regular.ttf"),
    "lucky": os.path.join(UF, "LuckiestGuy-Regular.ttf"),
    "balth": os.path.join(UF, "Balthazar-Regular.ttf"),
    "aladin": os.path.join(UF, "aladin.regular.ttf"),
    "georgia": "C:/Windows/Fonts/georgia.ttf",
    "georgiab": "C:/Windows/Fonts/georgiab.ttf",
    "georgiai": "C:/Windows/Fonts/georgiai.ttf",
}
SS = 4


def font(name, px):
    return ImageFont.truetype(FONTS[name], int(px * SS))


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


class Logo:
    """a canvas of W x H final pixels (drawn at SS x)"""

    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.W, self.H = w * SS, h * SS
        self.col = np.zeros((self.H, self.W, 3), np.float32)
        self.a = np.zeros((self.H, self.W), np.float32)
        self.ht = np.zeros((self.H, self.W), np.float32)
        self.yy, self.xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)

    # ---- masks (coordinates in final pixels)
    def m(self, fn):
        im = Image.new("L", (self.W, self.H), 0)
        fn(ImageDraw.Draw(im), SS)
        return np.asarray(im, np.float32) / 255.0

    def poly(self, pts):
        return self.m(lambda d, s: d.polygon([(x * s, y * s) for x, y in pts], fill=255))

    def ellipse(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        return self.m(lambda d, s: d.ellipse(((cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s), fill=255))

    def rrect(self, x0, y0, x1, y1, r):
        return self.m(lambda d, s: d.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), r * s, fill=255))

    def line(self, pts, w, joint="curve"):
        return self.m(lambda d, s: d.line([(x * s, y * s) for x, y in pts], fill=255, width=max(1, int(w * s)), joint=joint))

    def stroke_round(self, pts, w):
        """a polyline with round caps and joins"""
        def f(d, s):
            P = [(x * s, y * s) for x, y in pts]
            d.line(P, fill=255, width=int(w * s))
            for x, y in P:
                d.ellipse((x - w * s / 2, y - w * s / 2, x + w * s / 2, y + w * s / 2), fill=255)
        return self.m(f)

    def text(self, s_, fname, px, cx, cy, anchor="mm", spacing=0):
        f = font(fname, px)

        def g(d, s):
            if spacing:
                # tracked letters, centred
                widths = [d.textlength(ch, font=f) for ch in s_]
                tot = sum(widths) + spacing * s * (len(s_) - 1)
                x = cx * s - tot / 2
                for ch, wd in zip(s_, widths):
                    d.text((x + wd / 2, cy * s), ch, font=f, fill=255, anchor="mm")
                    x += wd + spacing * s
            else:
                d.text((cx * s, cy * s), s_, font=f, fill=255, anchor=anchor)
        return self.m(g)

    def arc_text(self, s_, fname, px, cx, cy, r, a_mid=-90, spacing=1.0, inside=False):
        """letters on a circle (degrees, -90 = top); inside=True reads along the bottom"""
        f = font(fname, px)
        out = np.zeros((self.H, self.W), np.float32)
        tmp = ImageDraw.Draw(Image.new("L", (8, 8)))
        widths = [tmp.textlength(ch, font=f) / SS * spacing for ch in s_]
        total = sum(widths)
        ang = total / r  # radians
        a = math.radians(a_mid) + (ang / 2 if inside else -ang / 2)
        for ch, wd in zip(s_, widths):
            step = wd / r
            a_c = a + (-step / 2 if inside else step / 2)
            x, y = cx + r * math.cos(a_c), cy + r * math.sin(a_c)
            g = Image.new("L", (int(px * 3 * SS), int(px * 3 * SS)), 0)
            ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=255, anchor="mm")
            rot = -math.degrees(a_c) - 90 if not inside else -math.degrees(a_c) + 90
            g = g.rotate(rot, resample=Image.BICUBIC)
            ga = np.asarray(g, np.float32) / 255.0
            x0, y0 = int(x * SS - g.width / 2), int(y * SS - g.height / 2)
            sx0, sy0 = max(0, -x0), max(0, -y0)
            dx0, dy0 = max(0, x0), max(0, y0)
            dx1, dy1 = min(self.W, x0 + g.width), min(self.H, y0 + g.height)
            if dx1 > dx0 and dy1 > dy0:
                sub = ga[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
                out[dy0:dy1, dx0:dx1] = np.maximum(out[dy0:dy1, dx0:dx1], sub)
            a += -step if inside else step
        return out

    # ---- paint
    def paint(self, mask, color, height=None, alpha=1.0, hmode="max"):
        """color: hex, (r,g,b), or an HxWx3 array"""
        c = rgb(color) if isinstance(color, str) else np.asarray(color, np.float32)
        k = np.clip(mask * alpha, 0, 1)
        if c.ndim == 1:
            self.col = self.col * (1 - k[..., None]) + c[None, None, :] * k[..., None]
        else:
            self.col = self.col * (1 - k[..., None]) + c * k[..., None]
        self.a = np.maximum(self.a, k)
        if height is not None:
            hv = height(self) if callable(height) else height
            if hmode == "max":
                self.ht = np.where(k > 0.5, np.maximum(self.ht, hv), self.ht)
            elif hmode == "set":
                self.ht = self.ht * (1 - k) + hv * k
            elif hmode == "add":
                self.ht = self.ht + hv * k
        return self

    def vgrad(self, top, bot, y0, y1):
        t = np.clip((self.yy / SS - y0) / max(1e-6, y1 - y0), 0, 1)[..., None]
        return rgb(top) * (1 - t) + rgb(bot) * t

    def rgrad(self, inner, outer, cx, cy, r):
        t = np.clip(np.hypot(self.xx / SS - cx, self.yy / SS - cy) / r, 0, 1)[..., None]
        return rgb(inner) * (1 - t) + rgb(outer) * t

    def grain(self, mask, amount=0.06, scale=2.0, seed=0):
        rng = np.random.default_rng(seed)
        n = ndimage.gaussian_filter(rng.standard_normal((self.H, self.W)).astype(np.float32), scale * SS)
        n /= (np.abs(n).max() + 1e-6)
        self.col = self.col * (1 + amount * n[..., None] * mask[..., None])
        return self

    def shade(self, mask, light=(-1, -1), strength=0.35, blur=3.0):
        """a soft bevel: lighter toward the light, darker away, inside the mask"""
        h = ndimage.gaussian_filter(mask, blur * SS)
        gy, gx = np.gradient(h)
        lx, ly = light
        d = -(gx * lx + gy * ly)
        d /= (np.abs(d).max() + 1e-6)
        self.col = self.col * (1 + strength * d[..., None] * mask[..., None])
        return self

    def glow(self, mask, color, radius, strength=1.0):
        g = ndimage.gaussian_filter(mask, radius * SS)
        g = np.clip(g / (g.max() + 1e-6) * strength, 0, 1)
        c = rgb(color)
        k = g * (1 - mask)
        self.col = self.col * (1 - k[..., None]) + c * k[..., None]
        self.a = np.maximum(self.a, k)
        return self

    # ---- helpers
    @staticmethod
    def grow(mask, px):
        ys, xs = np.nonzero(mask > 0.5) if px >= 0 else np.nonzero(mask > 0.5)
        if len(ys) == 0:
            return np.zeros_like(mask)
        pad = int(abs(px) * SS) + 4
        y0, y1 = max(0, ys.min() - pad), min(mask.shape[0], ys.max() + pad + 1)
        x0, x1 = max(0, xs.min() - pad), min(mask.shape[1], xs.max() + pad + 1)
        out = np.zeros_like(mask)
        out[y0:y1, x0:x1] = Logo._grow_full(mask[y0:y1, x0:x1], px)
        return out

    @staticmethod
    def _grow_full(mask, px):
        if px >= 0:
            return np.clip(ndimage.gaussian_filter((ndimage.distance_transform_edt(mask < 0.5) <= px * SS).astype(np.float32), 0.6), 0, 1)
        return np.clip(ndimage.gaussian_filter((ndimage.distance_transform_edt(mask >= 0.5) > -px * SS).astype(np.float32), 0.6), 0, 1)

    def outline(self, mask, px):
        return np.clip(self.grow(mask, px) - (mask > 0.5), 0, 1)

    def save(self):
        def down(a):
            if a.ndim == 2:
                return a.reshape(self.h, SS, self.w, SS).mean((1, 3))
            return a.reshape(self.h, SS, self.w, SS, a.shape[2]).mean((1, 3))
        col = down(self.col * self.a[..., None])
        al = down(self.a)
        col = np.where(al[..., None] > 1e-4, col / np.maximum(al[..., None], 1e-4), 0)
        rgba = np.dstack([np.clip(col, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, f"{self.name}_color.png"), optimize=True)
        ht = down(ndimage.gaussian_filter(self.ht, 0.8 * SS))
        ht = np.clip(ht / max(1e-6, self.ht.max()), 0, 1)
        Image.fromarray((ht * 65535).astype(np.uint16)).save(os.path.join(OUT, f"{self.name}_height.png"))
        return os.path.join(OUT, f"{self.name}_color.png")


LOGOS = {}


def logo(fn):
    LOGOS[fn.__name__] = fn
    return fn


# ================================================================== the town crest
def oak_leaf(L, cx, cy, s, rot=0.0):
    """an oak leaf built from rounded lobes either side of a midrib, pointing up (s = half length); returns (leaf, veins)"""
    c, sn = math.cos(rot), math.sin(rot)

    def P(x, y):
        return (cx + x * c - y * sn, cy + x * sn + y * c)
    leaf = np.zeros((L.H, L.W), np.float32)
    # the blade's core
    core = []
    for i in range(61):
        t = i / 60
        y = s * 0.8 - 1.75 * s * t
        w = s * 0.2 * math.sin(math.pi * min(1, t * 1.02)) + 0.02 * s
        core.append((w, y))
    leaf = np.maximum(leaf, L.poly([P(x, y) for x, y in core] + [P(-x, y) for x, y in reversed(core)]))
    # lobes: four pairs, biggest in the middle, offset left/right
    lobes = [(0.55, 0.20), (0.2, 0.28), (-0.15, 0.3), (-0.5, 0.22), (-0.78, 0.13)]
    veins = []
    for k, (ty, r) in enumerate(lobes):
        for side in (-1, 1):
            off = 0.06 * side * (1 if k % 2 else -1)
            lx, ly = side * (r * 0.95) * s, (ty + off) * s
            pts = []
            for j in range(48):
                a = 2 * math.pi * j / 48
                pts.append(P(lx + r * s * 0.95 * math.cos(a), ly + r * s * 0.78 * math.sin(a)))
            leaf = np.maximum(leaf, L.poly(pts))
            veins.append([P(0, ly + 0.12 * s), P(lx * 1.05, ly)])
    # the stem
    stem = L.stroke_round([P(0, s * 0.75), P(0.05 * s, s * 1.05)], 0.06 * s)
    rib = L.stroke_round([P(0, s * 0.95), P(0, -s * 0.9)], 0.035 * s)
    vm = np.zeros_like(leaf)
    for v in veins:
        vm = np.maximum(vm, L.stroke_round(v, 0.022 * s))
    return np.clip(leaf, 0, 1), np.clip(stem, 0, 1), np.clip(rib + vm, 0, 1)


@logo
def WickfieldCrest():
    L = Logo("WickfieldCrest", 1024, 1024)
    cx = 512
    # the shield: a heater with a rounded base
    sh = [(cx - 300, 170), (cx + 300, 170), (cx + 300, 470)]
    for i in range(1, 40):
        a = math.pi * i / 40
        sh.append((cx + 300 * math.cos(a * 0.5) if False else cx + 300 - 300 * (1 - math.cos(a / 2)) * 1.0, 470 + 300 * math.sin(a / 2) * 1.0))
    sh = [(cx - 300, 170), (cx + 300, 170), (cx + 300, 500)]
    for i in range(1, 60):
        t = i / 60
        x = cx + 300 * math.cos(math.pi * t / 2)
        y = 500 + 330 * math.sin(math.pi * t / 2)
        sh.append((x - 0 if t < 1 else x, y))
    sh = [(cx - 300, 170), (cx + 300, 170), (cx + 300, 480)]
    for i in range(1, 61):  # right side curving to the point
        t = i / 60
        sh.append((cx + 300 * (1 - t) ** 1.0 * math.cos(t * 0.6), 480 + 360 * math.sin(t * math.pi / 2)))
    left = [(2 * cx - x, y) for x, y in reversed(sh[2:])]
    shield = L.poly(sh + left)
    rim = L.outline(shield, 22)
    L.paint(L.grow(shield, 34), "#2a1a10", height=0.55)                       # dark outer edge
    L.paint(rim, L.vgrad("#e8c87a", "#8a6428", 150, 860), height=0.8)          # gilt rim
    L.shade(rim, strength=0.45, blur=4)
    field = shield
    L.paint(field, L.vgrad("#4f6b3a", "#2c3e22", 170, 840), height=0.45)       # moss green field
    L.grain(field, 0.08, 3, seed=1)
    # a cream chevron band across it
    chev = L.poly([(cx - 300, 520), (cx, 400), (cx + 300, 520), (cx + 300, 590), (cx, 470), (cx - 300, 590)]) * field
    L.paint(L.grow(chev, 6) * field, "#c99a44", height=0.52)
    L.paint(chev, "#efe2c4", height=0.55)
    L.shade(chev, strength=0.25)
    # the oak leaf (upper left) and the lantern (upper right)
    leaf, stem, veins = oak_leaf(L, cx - 135, 300, 115, rot=-0.4)
    L.paint(L.grow(np.maximum(leaf, stem), 6), "#2a1a10", height=0.6)
    L.paint(stem, "#7a3412", height=0.66)
    L.paint(leaf, L.vgrad("#e39a34", "#a2481a", 190, 410), height=0.7)
    L.shade(leaf, strength=0.35, blur=5)
    L.paint(veins * leaf, "#8a3a14", height=0.66, alpha=0.85)
    # lantern
    lx, ly = cx + 135, 300
    body = L.poly([(lx - 48, ly - 40), (lx + 48, ly - 40), (lx + 38, ly + 70), (lx - 38, ly + 70)])
    cap = L.poly([(lx - 60, ly - 40), (lx, ly - 95), (lx + 60, ly - 40)])
    ring = L.ellipse(lx, ly - 108, 16) - L.ellipse(lx, ly - 108, 8)
    base = L.rrect(lx - 50, ly + 66, lx + 50, ly + 86, 6)
    L.glow(body, "#ffd27a", 30, 0.9)
    for m_ in (cap, np.clip(ring, 0, 1), base):
        L.paint(L.grow(m_, 5), "#2a1a10", height=0.6)
        L.paint(m_, "#3a3430", height=0.75)
        L.shade(m_, strength=0.5)
    L.paint(L.grow(body, 5), "#2a1a10", height=0.6)
    L.paint(body, L.rgrad("#fff4cf", "#f0a032", lx, ly + 15, 70), height=0.68)
    flame = L.poly([(lx, ly - 22), (lx + 16, ly + 18), (lx, ly + 40), (lx - 16, ly + 18)])
    L.paint(flame, "#fffdf0", height=0.7)
    for bx in (lx - 16, lx + 16):
        L.paint(L.line([(bx, ly - 40), (bx * 1.0 + (bx - lx) * -0.2, ly + 70)], 6), "#3a3430", height=0.72)
    # an acorn at the bottom
    ax, ay = cx, 680
    nut = L.ellipse(ax, ay + 20, 42, 52)
    capm = L.poly([(ax - 56, ay - 2), (ax + 56, ay - 2), (ax + 46, ay - 34), (ax, ay - 52), (ax - 46, ay - 34)])
    L.paint(L.grow(nut + capm, 6), "#2a1a10", height=0.6)
    L.paint(nut, L.vgrad("#c88a3e", "#7a4a1c", ay - 30, ay + 70), height=0.7)
    L.shade(nut, strength=0.5)
    L.paint(capm, "#5a3a1e", height=0.74)
    for k in range(7):  # cap cross-hatch
        L.paint(L.line([(ax - 50 + k * 16, ay - 4), (ax - 30 + k * 16, ay - 40)], 3) * capm, "#3a2412")
    L.paint(L.line([(ax, ay - 52), (ax + 8, ay - 72)], 7), "#3a2412", height=0.7)
    # the banner across the bottom
    by = 850
    band = L.poly([(cx - 380, by - 50), (cx - 200, by - 20), (cx, by - 10), (cx + 200, by - 20), (cx + 380, by - 50),
                   (cx + 380, by + 40), (cx + 200, by + 70), (cx, by + 80), (cx - 200, by + 70), (cx - 380, by + 40)])
    tails = [L.poly([(cx - 380, by - 40), (cx - 470, by - 20), (cx - 430, by + 10), (cx - 470, by + 50), (cx - 380, by + 40)]),
             L.poly([(cx + 380, by - 40), (cx + 470, by - 20), (cx + 430, by + 10), (cx + 470, by + 50), (cx + 380, by + 40)])]
    for t_ in tails:
        L.paint(L.grow(t_, 6), "#2a1a10", height=0.55)
        L.paint(t_, "#c9b48a", height=0.6)
        L.shade(t_, strength=0.4)
    L.paint(L.grow(band, 7), "#2a1a10", height=0.65)
    L.paint(band, L.vgrad("#f6ead0", "#d9c69c", by - 50, by + 80), height=0.7)
    L.shade(band, light=(0, -1), strength=0.3, blur=8)
    txt = L.arc_text("WICKFIELD", "georgiab", 70, cx, by + 1500, 1480, a_mid=-90, spacing=1.12)
    L.paint(txt, "#4a2a14", height=0.82)
    # the top scroll: EST. 1851
    top = L.text("EST. 1851", "georgiab", 46, cx, 125, spacing=6)
    L.paint(L.grow(top, 4), "#2a1a10", height=0.5)
    L.paint(top, "#e8c87a", height=0.6)
    for sx in (-1, 1):
        star = L.poly([(cx + sx * 200 + 18 * math.cos(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45),
                        125 - 18 * math.sin(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45)) for k in range(10)])
        L.paint(star, "#e8c87a", height=0.6)
    return L


# ================================================================== Wickfield Junior High "Wicks"
@logo
def WicksMascot():
    L = Logo("WicksMascot", 1024, 1024)
    cx = 512
    GREEN, GOLD, CREAM, INK = "#1f4a32", "#e3b23c", "#f4ead2", "#14110f"
    # a round badge
    disc = L.ellipse(cx, 512, 470)
    L.paint(disc, INK, height=0.4)
    L.paint(L.ellipse(cx, 512, 450), GOLD, height=0.5)
    L.shade(L.ellipse(cx, 512, 450) - L.ellipse(cx, 512, 410), strength=0.5)
    inner = L.ellipse(cx, 512, 410)
    L.paint(inner, L.rgrad("#2f6b47", GREEN, cx, 420, 420), height=0.45)
    L.grain(inner, 0.05, 2, seed=2)
    L.paint(L.ellipse(cx, 512, 404) - L.ellipse(cx, 512, 396), GOLD, height=0.5)
    # the arched name and the bottom line
    top = L.arc_text("WICKFIELD JR. HIGH", "lucky", 62, cx, 512, 340, a_mid=-90, spacing=1.06)
    bot = L.arc_text("GO  WICKS!", "lucky", 66, cx, 512, 340, a_mid=90, spacing=1.12, inside=True)
    for t_ in (top, bot):
        L.paint(L.grow(t_, 5), INK, height=0.6)
        L.paint(t_, CREAM, height=0.7)
    # the candle: a chunky cream cylinder with wax drips over the rim, school-green bands
    c0, c1 = 560, 742
    candle = L.rrect(cx - 96, c0, cx + 96, c1, 20)
    L.paint(L.grow(candle, 9), INK, height=0.7)
    cyl = 1 - np.clip(np.abs(L.xx / SS - cx) / 96, 0, 1) ** 2            # cylinder shading across
    base = L.vgrad("#fff8ea", "#ead8b4", c0, c1) * (0.78 + 0.22 * np.sqrt(cyl))[..., None]
    L.paint(candle, base, height=0.78)
    for sy in (650, 690):
        band = L.rrect(cx - 96, sy, cx + 96, sy + 16, 3) * candle
        L.paint(band, L.vgrad("#2f6b47", "#1a3d29", sy, sy + 16) * (0.75 + 0.25 * np.sqrt(cyl))[..., None], height=0.79)
    # the melted top and its drips (brighter wax, outlined so they read)
    top = L.ellipse(cx, c0 + 6, 96, 18)
    drips = [(-70, 70, 13), (-22, 40, 11), (30, 92, 14), (74, 52, 11)]
    wax = top.copy()
    for dx, ln, w in drips:
        wax = np.maximum(wax, L.rrect(cx + dx - w, c0, cx + dx + w, c0 + ln, w))
    wax *= np.clip(L.grow(candle, 1), 0, 1)
    L.paint(L.outline(wax, 3) * candle, "#c9b48c", height=0.8)
    L.paint(wax, L.vgrad("#ffffff", "#f6ead2", c0, c0 + 100), height=0.83)
    L.shade(wax, light=(-1, -1), strength=0.25, blur=4)
    L.paint(L.ellipse(cx, c0 + 6, 74, 10), "#efe0c0", height=0.8)     # the dip round the wick
    # the wick
    L.paint(L.stroke_round([(cx, c0 + 4), (cx + 3, c0 - 26)], 9), INK, height=0.85)
    # the flame: a teardrop, point up, with a licking curl; a hot core
    def tear(cx_, cy_, w, h, lean=0.0, n=160):
        P = []
        for i in range(n + 1):
            t = 2 * math.pi * i / n
            x = w * math.sin(t) * math.sin(t / 2) ** 1.6
            y = -h * math.cos(t) * (1.0 if math.cos(t) > 0 else 0.55)
            x += lean * (h - y) / (2 * h) * w * (1 if math.cos(t) > 0 else 0) * 0.0
            P.append((cx_ + x + lean * max(0, math.cos(t)) * 30, cy_ + y))
        return L.poly(P)
    flame = np.clip(tear(cx, 400, 120, 150, lean=0.6) + L.ellipse(cx, 455, 95, 80), 0, 1)
    L.glow(flame, "#ffcf5a", 46, 0.8)
    L.paint(L.grow(flame, 9), INK, height=0.8)
    L.paint(flame, L.vgrad("#fff6c2", "#f0761a", 250, 540), height=0.88)
    L.shade(flame, light=(-1, -1), strength=0.18, blur=10)
    inner = np.clip(tear(cx, 440, 70, 90, lean=0.4) + L.ellipse(cx, 470, 60, 50), 0, 1)
    L.paint(inner, L.vgrad("#fffbe6", "#ffd16a", 350, 520), alpha=0.9)
    # face: determined brows, eyes with highlights, a big grin
    for sx in (-1, 1):
        L.paint(L.ellipse(cx + sx * 34, 462, 14, 19), INK, height=0.92)
        L.paint(L.ellipse(cx + sx * 34 + 4, 455, 5), "#ffffff")
        L.paint(L.poly([(cx + sx * 12, 434), (cx + sx * 58, 418), (cx + sx * 60, 430), (cx + sx * 14, 446)]), INK, height=0.93)
    L.paint(L.m(lambda d, s: d.chord(((cx - 42) * s, 478 * s, (cx + 42) * s, 534 * s), 0, 180, fill=255)), INK, height=0.9)
    L.paint(L.m(lambda d, s: d.chord(((cx - 32) * s, 492 * s, (cx + 32) * s, 528 * s), 0, 180, fill=255)), "#c8321e")
    L.paint(L.rrect(cx - 30, 507, cx + 30, 515, 2), "#ffffff")       # teeth
    # two little stars either side
    for sx in (-1, 1):
        st = L.poly([(cx + sx * 260 + 26 * math.cos(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.42),
                      540 - 26 * math.sin(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.42)) for k in range(10)])
        L.paint(L.grow(st, 4), INK, height=0.6)
        L.paint(st, GOLD, height=0.7)
    return L


# ================================================================== Moonpie Diner (neon)
@logo
def MoonpieDiner():
    L = Logo("MoonpieDiner", 1536, 768)
    TEAL, PINK, CHROME = "#4ff0e0", "#ff5fa8", "#c9ced6"
    # the backing board: a chrome-rimmed rounded panel, deep navy
    board = L.rrect(40, 60, 1496, 708, 90)
    L.paint(L.grow(board, 10), "#0b0c12", height=0.3)
    L.paint(board - L.grow(board, -18), L.vgrad("#f2f4f8", "#7b818c", 60, 708), height=0.6)
    L.shade(board - L.grow(board, -18), strength=0.6, blur=4)
    inner = L.grow(board, -18)
    L.paint(inner, L.vgrad("#1a1d36", "#0d0e1c", 60, 708), height=0.35)
    L.grain(inner, 0.05, 1.5, seed=3)

    def neon(mask, color, w_glow=26):
        tube = mask
        L.glow(tube, color, w_glow, 0.85)
        L.paint(tube, color, height=0.7)
        core = L.grow(tube, -2.2)
        L.paint(core, "#ffffff", alpha=0.75, height=0.75)

    # the crescent moon biting a pie slice (left)
    mx, my = 300, 384
    moon = L.ellipse(mx, my, 190) - L.ellipse(mx + 90, my - 50, 165)
    moon = np.clip(moon, 0, 1)
    moon_line = L.outline(moon, 9) * (1 - L.grow(moon, -1))
    moon_line = np.clip(L.grow(moon, 5) - L.grow(moon, -5), 0, 1)
    neon(moon_line, TEAL)
    # the moon's sleepy eye and smile
    neon(L.stroke_round([(mx - 120, my - 30), (mx - 95, my - 22), (mx - 70, my - 30)], 8), TEAL, 14)
    # the pie slice with a bite taken out of it
    px, py = mx + 110, my + 40
    slice_ = L.poly([(px - 60, py - 10), (px + 170, py - 90), (px + 170, py + 40), (px - 60, py + 40)])
    bite = L.ellipse(px - 62, py + 6, 26) + L.ellipse(px - 40, py - 22, 22)
    slice_ = np.clip(slice_ - bite, 0, 1)
    sl_line = np.clip(L.grow(slice_, 5) - L.grow(slice_, -5), 0, 1)
    neon(sl_line, PINK)
    neon(L.stroke_round([(px + 150, py - 70), (px + 150, py + 22)], 7), PINK, 14)      # the crust edge
    neon(L.stroke_round([(mx - 132, my + 40), (mx - 112, my + 58), (mx - 86, my + 60)], 8), TEAL, 14)   # the moon's smile
    for k in range(3):                                                                  # steam
        x0 = px + 60 + k * 40
        neon(L.stroke_round([(x0, py - 110), (x0 + 12, py - 135), (x0, py - 160), (x0 + 12, py - 185)], 7), "#ffffff", 12)
    # "Moonpie" in a script, and DINER under it in spaced block caps
    word = L.text("Moonpie", "chela", 250, 1010, 300)
    neon(np.clip(L.grow(word, 4) - L.grow(word, -4), 0, 1), PINK, 30)
    diner = L.text("D I N E R", "lucky", 120, 1010, 530, spacing=10)
    neon(np.clip(L.grow(diner, 3) - L.grow(diner, -3), 0, 1), TEAL, 24)
    # "OPEN LATE" small at the bottom right, and dots along the top
    neon(np.clip(L.grow(L.text("OPEN LATE", "lucky", 44, 1300, 640, spacing=4), 2) - L.grow(L.text("OPEN LATE", "lucky", 44, 1300, 640, spacing=4), -2), 0, 1), "#ffd24f", 14)
    for k in range(18):
        L.paint(L.ellipse(140 + k * 70, 100, 7), "#ffe9a8", height=0.7)
        L.glow(L.ellipse(140 + k * 70, 100, 7), "#ffd24f", 8, 0.6)
    return L


# ================================================================== Wick & Sons Hardware (gold leaf on glass + board)
@logo
def WickSonsHardware():
    L = Logo("WickSonsHardware", 1536, 512)
    board = L.rrect(20, 30, 1516, 482, 24)
    L.paint(L.grow(board, 8), "#1b120c", height=0.3)
    L.paint(board, L.vgrad("#2e5a3c", "#1d3a27", 30, 482), height=0.4)       # painted green board
    L.grain(board, 0.10, 6, seed=4)
    for k in range(5):                                                       # board planks
        y = 30 + k * 90
        L.paint(L.line([(20, y), (1516, y)], 3) * board, "#13261a", height=0.36)
    trim = board - L.grow(board, -22)
    L.paint(trim, L.vgrad("#f0dc9a", "#8f6a26", 30, 482), height=0.55)
    L.shade(trim, strength=0.5, blur=3)
    GOLD = L.vgrad("#fff0b8", "#b8862e", 60, 450)
    title = L.arc_text("WICK & SONS", "georgiab", 124, 768, 2420, 2200, a_mid=-90, spacing=1.08)
    L.paint(L.grow(title, 6), "#0e1a12", height=0.5)
    L.paint(title, GOLD, height=0.8)
    L.shade(title, strength=0.55, blur=2)
    sub = L.text("HARDWARE  \u00b7  TOOLS  \u00b7  KEYS CUT", "balth", 58, 768, 360, spacing=3)
    L.paint(L.grow(sub, 3), "#0e1a12", height=0.5)
    L.paint(sub, "#f2e6c4", height=0.65)
    est = L.text("EST. 1902", "georgiai", 40, 768, 430)
    L.paint(est, "#e3c272", height=0.6)
    # crossed hammer and saw either side
    for sx in (-1, 1):
        ox = 768 + sx * 625
        hammer = L.rrect(ox - 7, 175, ox + 7, 375, 5)
        head = L.rrect(ox - 44, 165, ox + 44, 199, 7)
        claw = L.poly([(ox + 44, 170), (ox + 70, 156), (ox + 62, 182), (ox + 44, 194)])
        tool = np.clip(hammer + head + claw, 0, 1)
        c, s = math.cos(sx * 0.5), math.sin(sx * 0.5)
        im = Image.fromarray((tool * 255).astype(np.uint8)).rotate(math.degrees(sx * 0.5), center=(ox * SS, 275 * SS), resample=Image.BICUBIC)
        tool = np.asarray(im, np.float32) / 255
        L.paint(L.grow(tool, 4), "#0e1a12", height=0.5)
        L.paint(tool, GOLD, height=0.75)
        L.shade(tool, strength=0.5, blur=2)
    return L


def star(L, cx, cy, r, k=0.42, n=5, rot=0.0):
    return L.poly([(cx + r * (1 if i % 2 == 0 else k) * math.cos(-math.pi / 2 + rot + i * math.pi / n),
                    cy + r * (1 if i % 2 == 0 else k) * math.sin(-math.pi / 2 + rot + i * math.pi / n)) for i in range(2 * n)])


def mirror_pts(pts, cx):
    return [(2 * cx - x, y) for x, y in reversed(pts)]


# ================================================================== Pembrook Prep Pumas
@logo
def PembrookPumas():
    L = Logo("PembrookPumas", 1024, 1024)
    cx = 512
    PUR, PUR2, SIL, INK, CREAM = "#4a2470", "#6e3aa0", "#d7dbe2", "#120c18", "#f1e9dc"
    sh = [(cx, 70), (cx + 360, 160), (cx + 340, 560), (cx + 200, 820), (cx, 950)]
    shield = L.poly(sh + mirror_pts(sh[1:-1], cx))
    L.paint(L.grow(shield, 30), INK, height=0.4)
    rim = L.grow(shield, 18)
    L.paint(rim, L.vgrad("#f4f6fa", "#8a909c", 70, 950), height=0.6)
    L.shade(np.clip(rim - shield, 0, 1), strength=0.5, blur=4)
    L.paint(shield, L.vgrad(PUR2, "#2a1242", 70, 950), height=0.45)
    L.grain(shield, 0.05, 2, seed=5)
    band = L.poly([(cx - 330, 165), (cx + 330, 165), (cx + 325, 248), (cx - 325, 248)]) * shield
    L.paint(band, L.vgrad("#eef0f4", "#9aa0aa", 165, 248), height=0.6)
    L.paint(L.text("PEMBROOK PREP", "lucky", 62, cx, 210, spacing=4), PUR, height=0.7)
    # the puma head: faceted, front on, snarling
    hy = 560
    TAN, TAN2, TAN3 = "#c8913f", "#e0b064", "#9a6528"
    head = L.poly([(cx - 190, hy - 120), (cx - 120, hy - 190), (cx, hy - 205), (cx + 120, hy - 190), (cx + 190, hy - 120),
                   (cx + 215, hy - 10), (cx + 170, hy + 110), (cx + 80, hy + 185), (cx, hy + 205), (cx - 80, hy + 185),
                   (cx - 170, hy + 110), (cx - 215, hy - 10)])
    for sx in (-1, 1):
        e = L.poly([(cx + sx * 115, hy - 175), (cx + sx * 215, hy - 285), (cx + sx * 205, hy - 115)])
        L.paint(L.grow(e, 9), INK, height=0.7)
        L.paint(e, TAN3, height=0.75)
        L.paint(L.poly([(cx + sx * 140, hy - 175), (cx + sx * 200, hy - 250), (cx + sx * 193, hy - 145)]), "#5a2c1c", height=0.72)
    L.paint(L.grow(head, 10), INK, height=0.72)
    L.paint(head, TAN, height=0.8)
    for pts, col in (
        ([(cx - 120, hy - 190), (cx, hy - 205), (cx + 120, hy - 190), (cx + 60, hy - 60), (cx, hy - 40), (cx - 60, hy - 60)], TAN2),
        ([(cx - 190, hy - 120), (cx - 120, hy - 190), (cx - 60, hy - 60), (cx - 120, hy + 10), (cx - 215, hy - 10)], TAN3),
        ([(cx + 190, hy - 120), (cx + 120, hy - 190), (cx + 60, hy - 60), (cx + 120, hy + 10), (cx + 215, hy - 10)], TAN3),
        ([(cx - 215, hy - 10), (cx - 120, hy + 10), (cx - 90, hy + 120), (cx - 170, hy + 110)], TAN2),
        ([(cx + 215, hy - 10), (cx + 120, hy + 10), (cx + 90, hy + 120), (cx + 170, hy + 110)], TAN2),
    ):
        L.paint(L.poly(pts) * head, col, height=0.82)
    muz = L.poly([(cx - 110, hy + 20), (cx, hy - 10), (cx + 110, hy + 20), (cx + 120, hy + 110), (cx + 60, hy + 180),
                  (cx, hy + 195), (cx - 60, hy + 180), (cx - 120, hy + 110)])
    L.paint(muz, CREAM, height=0.85)
    L.shade(muz, strength=0.25, blur=6)
    nose = L.poly([(cx - 42, hy + 18), (cx + 42, hy + 18), (cx, hy + 62)])
    L.paint(L.grow(nose, 4), INK, height=0.9)
    L.paint(nose, "#3a2228", height=0.92)
    mouth = L.poly([(cx - 85, hy + 95), (cx, hy + 80), (cx + 85, hy + 95), (cx + 55, hy + 170), (cx, hy + 182), (cx - 55, hy + 170)])
    L.paint(L.grow(mouth, 5), INK, height=0.86)
    L.paint(mouth, "#5a1426", height=0.84)
    L.paint(L.ellipse(cx, hy + 150, 30, 18) * mouth, "#c04060", height=0.85)
    for sx in (-1, 1):
        L.paint(L.poly([(cx + sx * 62, hy + 92), (cx + sx * 34, hy + 90), (cx + sx * 50, hy + 142)]), "#fbf6ee", height=0.9)
        L.paint(L.poly([(cx + sx * 46, hy + 172), (cx + sx * 24, hy + 176), (cx + sx * 38, hy + 138)]), "#fbf6ee", height=0.9)
    L.paint(L.stroke_round([(cx, hy + 62), (cx, hy + 82)], 6), INK)
    for sx in (-1, 1):
        eye = L.poly([(cx + sx * 40, hy - 40), (cx + sx * 130, hy - 70), (cx + sx * 115, hy - 25), (cx + sx * 55, hy - 12)])
        L.paint(L.grow(eye, 6), INK, height=0.86)
        L.paint(eye, L.vgrad("#e8f070", "#7fb030", hy - 70, hy - 12), height=0.88)
        L.paint(L.ellipse(cx + sx * 88, hy - 40, 7, 22) * eye, INK, height=0.9)
        L.paint(L.poly([(cx + sx * 25, hy - 62), (cx + sx * 140, hy - 102), (cx + sx * 140, hy - 84), (cx + sx * 40, hy - 46)]), "#3a2414", height=0.9)
        for k in range(3):
            L.paint(L.ellipse(cx + sx * (60 + k * 18), hy + 60 + (k % 2) * 12, 4), "#8a6a4a", height=0.86)
    rib = L.poly([(cx - 300, 790), (cx + 300, 790), (cx + 280, 880), (cx - 280, 880)])
    L.paint(L.grow(rib, 8), INK, height=0.7)
    L.paint(rib, L.vgrad("#eef0f4", "#9aa0aa", 790, 880), height=0.75)
    word = L.text("PUMAS", "lucky", 96, cx, 838, spacing=10)
    L.paint(L.grow(word, 4), INK, height=0.8)
    L.paint(word, PUR, height=0.85)
    for sx in (-1, 1):
        st = star(L, cx + sx * 300, 360, 24)
        L.paint(L.grow(st, 4), INK, height=0.6)
        L.paint(st, SIL, height=0.7)
    return L


# ================================================================== Reel Time Video (lightbox)
@logo
def ReelTimeVideo():
    L = Logo("ReelTimeVideo", 1536, 512)
    RED, INK = "#e8402e", "#0c0d14"
    box = L.rrect(20, 20, 1516, 492, 30)
    L.paint(L.grow(box, 6), INK, height=0.3)
    L.paint(box, L.vgrad("#2a56d6", "#14287a", 20, 492), height=0.4)
    L.col += (np.exp(-((L.xx / SS - 768) ** 2 / 600 ** 2 + (L.yy / SS - 256) ** 2 / 260 ** 2)) * 50)[..., None] * box[..., None]
    trim = np.clip(box - L.grow(box, -14), 0, 1)
    L.paint(trim, L.vgrad("#e9edf5", "#7c8494", 20, 492), height=0.55)
    rx, ry, rr = 250, 256, 170
    reel = L.ellipse(rx, ry, rr)
    L.paint(L.grow(reel, 8), INK, height=0.6)
    L.paint(reel, L.vgrad("#f2f4f8", "#a4aab6", ry - rr, ry + rr), height=0.7)
    L.shade(reel, strength=0.4, blur=6)
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        L.paint(L.ellipse(rx + 92 * math.cos(a), ry + 92 * math.sin(a), 38), "#20263a", height=0.5)
    L.paint(L.ellipse(rx, ry, 34), "#20263a", height=0.6)
    for k in range(12):
        a = k * math.pi / 6
        L.paint(L.stroke_round([(rx + 148 * math.cos(a), ry + 148 * math.sin(a)), (rx + 160 * math.cos(a), ry + 160 * math.sin(a))], 6), INK, height=0.75)
    L.paint(L.stroke_round([(rx, ry), (rx + 70, ry - 70)], 12), RED, height=0.8)
    L.paint(L.stroke_round([(rx, ry), (rx + 25, ry - 120)], 9), INK, height=0.8)
    L.paint(L.ellipse(rx, ry, 16), RED, height=0.82)
    # REEL TIME, chunky with an offset shadow and a white outline; VIDEO RENTALS under it
    word = L.text("REEL TIME", "lucky", 190, 960, 200, spacing=6)
    L.paint(np.roll(np.roll(L.grow(word, 10), 10 * SS, 0), 8 * SS, 1) * box, INK, height=0.6)
    L.paint(L.grow(word, 10), INK, height=0.7)
    L.paint(L.grow(word, 5), "#ffffff", height=0.75)
    L.paint(word, L.vgrad("#fff59a", "#ffb21e", 120, 280), height=0.85)
    L.shade(word, strength=0.3, blur=3)
    vid = L.text("VIDEO  ·  RENTALS", "lucky", 70, 960, 345, spacing=8)
    L.paint(L.grow(vid, 5), INK, height=0.7)
    L.paint(vid, "#ffffff", height=0.8)
    # a film strip along the bottom
    strip = L.rrect(470, 405, 1450, 465, 4)
    L.paint(strip, "#15161c", height=0.6)
    for k in range(40):
        x = 480 + k * 24.5
        L.paint(L.rrect(x, 412, x + 12, 420, 2) + L.rrect(x, 450, x + 12, 458, 2), "#e8e8e8", height=0.62)
    return L


# ================================================================== Suds Laundromat
@logo
def SudsLaundromat():
    L = Logo("SudsLaundromat", 1536, 512)
    INK = "#123c3a"
    board = L.rrect(20, 20, 1516, 492, 200)
    L.paint(L.grow(board, 8), "#0d2a28", height=0.3)
    L.paint(board, L.vgrad("#d9f6ee", "#8fd3c1", 20, 492), height=0.4)
    ring = np.clip(board - L.grow(board, -16), 0, 1)
    L.paint(ring, L.vgrad("#ffffff", "#b7c2c8", 20, 492), height=0.55)
    L.shade(ring, strength=0.4, blur=3)
    wx, wy = 260, 256
    door = L.ellipse(wx, wy, 165)
    L.paint(L.grow(door, 8), INK, height=0.6)
    L.paint(door, L.vgrad("#f4f7fa", "#8e98a4", wy - 165, wy + 165), height=0.7)
    L.shade(door, strength=0.4, blur=5)
    glass = L.ellipse(wx, wy, 120)
    L.paint(glass, L.rgrad("#bfe9ff", "#3a86b8", wx - 30, wy - 40, 160), height=0.6)
    wave = L.poly([(wx - 120 + i * 6, wy + 20 + 14 * math.sin(i * 0.35)) for i in range(41)] + [(wx + 120, wy + 130), (wx - 120, wy + 130)]) * glass
    L.paint(wave, "#5fb3e0", height=0.62)
    L.paint(L.m(lambda d, s: d.arc(((wx - 95) * s, (wy - 95) * s, (wx + 95) * s, (wy + 95) * s), 200, 250, fill=255, width=int(12 * s))), "#ffffff", alpha=0.8)
    rng = np.random.default_rng(7)
    for k in range(12):
        bx, by, br = wx + 150 + rng.uniform(0, 200), wy + 70 - rng.uniform(0, 170), rng.uniform(14, 38)
        bub = L.ellipse(bx, by, br)
        L.paint(L.outline(bub, 3), INK, alpha=0.55)
        L.paint(bub, L.rgrad("#ffffff", "#bdeee0", bx - br * 0.4, by - br * 0.4, br * 1.6), alpha=0.85, height=0.7)
        L.paint(L.ellipse(bx - br * 0.35, by - br * 0.35, br * 0.22), "#ffffff", height=0.75)
    word = L.text("Suds", "chela", 250, 940, 210)
    L.paint(L.grow(word, 12), INK, height=0.7)
    L.paint(L.grow(word, 6), "#ffffff", height=0.75)
    L.paint(word, L.vgrad("#4fc7a8", "#1f8a72", 90, 320), height=0.85)
    L.shade(word, strength=0.35, blur=3)
    sub = L.text("LAUNDROMAT  ·  OPEN 24 HRS", "lucky", 56, 960, 400, spacing=5)
    L.paint(L.grow(sub, 4), "#ffffff", height=0.7)
    L.paint(sub, INK, height=0.8)
    return L


# ================================================================== The Wickfield Gazette (masthead on newsprint)
@logo
def WickfieldGazette():
    L = Logo("WickfieldGazette", 2048, 512)
    INK, PAPER = "#1a1612", "#efe8d6"
    page = L.rrect(0, 0, 2048, 512, 2)
    L.paint(page, PAPER, height=0.2)
    L.grain(page, 0.05, 1.2, seed=8)
    L.paint(np.clip(L.rrect(40, 40, 2008, 48, 0) + L.rrect(40, 56, 2008, 60, 0), 0, 1), INK, height=0.3)
    L.paint(np.clip(L.rrect(40, 452, 2008, 456, 0) + L.rrect(40, 464, 2008, 472, 0), 0, 1), INK, height=0.3)
    L.paint(L.text("The Wickfield Gazette", "balth", 168, 1024, 245), INK, height=0.6)
    L.paint(L.text("ALL THE NEWS THAT FITS, AND SOME THAT DOESN’T", "georgia", 32, 1024, 400, spacing=4), INK, height=0.5)
    L.paint(L.text("EST. 1851", "georgiab", 30, 170, 95), INK, height=0.5)
    L.paint(L.text("FIVE CENTS", "georgiab", 30, 1878, 95), INK, height=0.5)
    for sx in (-1, 1):
        x = 1024 + sx * 905
        L.paint(np.clip(L.ellipse(x, 250, 70) - L.ellipse(x, 250, 62), 0, 1), INK, height=0.5)
        L.paint(L.poly([(x - 22, 228), (x + 22, 228), (x + 17, 285), (x - 17, 285)]), INK, height=0.55)
        L.paint(L.poly([(x - 9, 240), (x + 9, 240), (x + 7, 274), (x - 7, 274)]), PAPER)
        L.paint(L.poly([(x - 28, 228), (x, 200), (x + 28, 228)]), INK, height=0.55)
    return L


# ================================================================== The Founder's plaque (cast bronze)
@logo
def FounderPlaque():
    L = Logo("FounderPlaque", 1024, 640)
    INK = "#1c140c"
    plate = L.rrect(20, 20, 1004, 620, 40)
    L.paint(L.grow(plate, 6), INK, height=0.3)
    L.paint(plate, L.vgrad("#b98a4a", "#6a4620", 20, 620), height=0.5)
    L.grain(plate, 0.12, 2.5, seed=9)
    rim = np.clip(plate - L.grow(plate, -26), 0, 1)
    L.paint(rim, L.vgrad("#e2b56c", "#8a5e2a", 20, 620), height=0.75)
    L.shade(rim, strength=0.5, blur=4)
    for x, y in ((70, 70), (954, 70), (70, 570), (954, 570)):
        b = L.ellipse(x, y, 20)
        L.paint(b, "#d8a860", height=0.85)
        L.shade(b, strength=0.6, blur=2)
    raised = np.zeros((L.H, L.W), np.float32)
    lines = [("JOSIAH WICK", "georgiab", 74, 140, 8), ("1803  –  1871", "georgia", 40, 215, 6),
             ("FOUNDER OF WICKFIELD", "balth", 46, 300, 4),
             ("Who never once broke a rule,", "georgiai", 44, 400, 0), ("and wished you wouldn’t either.", "georgiai", 44, 455, 0),
             ("ERECTED BY GRATEFUL CITIZENS, 1901", "balth", 30, 545, 3)]
    for t_, f_, px, y, sp in lines:
        raised = np.maximum(raised, L.text(t_, f_, px, 512, y, spacing=sp))
    raised = np.maximum(raised, L.rrect(300, 340, 724, 346, 2))
    L.paint(L.grow(raised, 3), "#3a2410", height=0.6)
    L.paint(raised, L.vgrad("#f0c47c", "#a87436", 100, 560), height=0.9)
    L.shade(raised, strength=0.55, blur=1.5)
    patina = np.clip(ndimage.gaussian_filter(np.clip(L.grow(raised, 5) - raised, 0, 1), 3 * SS) * 1.5, 0, 1) * plate
    L.paint(patina, "#4f8a72", alpha=0.22)
    return L


# ================================================================== the admission envelope's wax crest (new, not the UI Seal)
@logo
def AdmissionWax():
    L = Logo("AdmissionWax", 768, 768)
    cx = cy = 384
    pts = []
    rng = np.random.default_rng(11)
    nlo = rng.uniform(0, 2 * math.pi, 6)
    for i in range(240):
        a = 2 * math.pi * i / 240
        r = 300 + sum(14 * math.sin(a * (k + 3) + nlo[k]) for k in range(6))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    blob = L.poly(pts)
    L.paint(blob, L.rgrad("#b01a2c", "#5a0812", cx - 60, cy - 80, 360), height=0.45)
    L.shade(blob, strength=0.45, blur=20)
    disc = L.ellipse(cx, cy, 230)
    L.paint(disc, L.rgrad("#8a1020", "#5c0812", cx, cy, 240), height=0.35)
    L.shade(disc, light=(1, 1), strength=0.4, blur=6)
    L.paint(np.clip(L.ellipse(cx, cy, 214) - L.ellipse(cx, cy, 200), 0, 1), "#b52236", height=0.55)
    raised = np.zeros((L.H, L.W), np.float32)
    # a crescent below, cradling a proper bell (crown, waist, flared lip), stars above
    raised = np.maximum(raised, np.clip(L.ellipse(cx, cy + 20, 120) - L.ellipse(cx, cy - 4, 116), 0, 1) * (L.yy / SS > cy + 40))
    prof = []
    for i in range(81):
        t = i / 80                                    # 0 crown top -> 1 lip
        y = cy - 125 + 175 * t
        if t < 0.18:
            w = 58 * math.sqrt(max(0.0, 1 - ((0.18 - t) / 0.18) ** 2))
        else:
            u = (t - 0.18) / 0.82
            w = 58 - 10 * math.sin(math.pi * min(1, u * 1.4)) * (u < 0.72) + 52 * max(0, u - 0.62) ** 1.5 * 4.0
        prof.append((cx + w, y))
    raised = np.maximum(raised, L.poly(prof + [(2 * cx - x, y) for x, y in reversed(prof)]))
    raised = np.maximum(raised, L.rrect(cx - 112, cy + 44, cx + 112, cy + 56, 6))           # the lip band
    raised = np.maximum(raised, np.clip(L.ellipse(cx, cy - 140, 18) - L.ellipse(cx, cy - 140, 9), 0, 1))
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.42
        if k == 2:
            continue
        raised = np.maximum(raised, star(L, cx + 165 * math.cos(a), cy - 10 + 165 * math.sin(a), 11))
    raised = np.maximum(raised, L.arc_text("NOCTE  DISCIMUS", "georgiab", 32, cx, cy, 178, a_mid=90, spacing=1.15, inside=True))
    L.paint(raised, L.vgrad("#e0485c", "#9a1428", cy - 200, cy + 200), height=0.7)
    L.shade(raised, strength=0.5, blur=2)
    L.paint(L.ellipse(cx, cy + 66, 16), "#e0485c", height=0.72)
    L.paint(ndimage.gaussian_filter(L.ellipse(cx - 130, cy - 170, 70, 26), 12 * SS), "#ffffff", alpha=0.35)
    return L


def sheet(names):
    ims = [Image.open(os.path.join(OUT, f"{n}_color.png")).convert("RGBA") for n in names]
    h = 360
    ims = [i.resize((int(i.width * h / i.height), h), Image.LANCZOS) for i in ims]
    W = sum(i.width for i in ims) + 20 * (len(ims) + 1)
    s = Image.new("RGBA", (W, h + 40), (58, 52, 60, 255))
    x = 20
    for i in ims:
        s.alpha_composite(i, (x, 20))
        x += i.width + 20
    p = os.path.join(OUT, "_sheet.png")
    s.convert("RGB").save(p)
    return p


if __name__ == "__main__":
    names = sys.argv[1:] or list(LOGOS)
    for n in names:
        LOGOS[n]().save()
        print("ok", n)
    print(sheet(names))
