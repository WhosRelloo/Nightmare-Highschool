"""
Nightmare High brows + mouths - separate face layers that fit the painted eyes (gen_eyes.py).

Brows: 8 styles, fitted per eye shape. Each brow is placed so its lower edge clears the highest lash /
       wing / crease of EVERY variant of that shape (male, female, all transformation forms) by BROW_GAP.
       Greyscale (light) so the game can tint it with Decal.Color3 (hair colour).
       -> brow_<style>_<shape>.png
Mouths: 8 styles x (m = plain, f = fuller tinted lips) + 4 transformation mouths. Untinted.
       -> mouth_<style>_<m|f>.png, mouth_<form>.png
Every output is checked against the eye renders: no brow or mouth pixel may touch an eye pixel.

usage: python gen_face.py <outdir> <eyes_render_dir>
"""
import glob, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_eyes as E   # shape geometry (corners) + stroke helpers

OUT, EYES = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
S, N = 4, 1024
BROW_GAP = 14
MOUTH_GAP = 24
INK = np.array([0.07, 0.05, 0.08], np.float32)

class Canvas:
    def __init__(self, x0, y0, w, h, scale=1.0, centre=(512, 0)):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.k, self.c = scale, np.array(centre, float)   # geometry is drawn scaled about `centre`
        self.sh = (h * S, w * S)
        yy, xx = (np.mgrid[0:self.sh[0], 0:self.sh[1]].astype(np.float32) + 0.5) / S
        self.X, self.Y = xx + x0, yy + y0
        self.rgb = np.zeros(self.sh + (3,), np.float32)
        self.a = np.zeros(self.sh, np.float32)

    def mask(self, polys):
        im = Image.new("L", (self.sh[1], self.sh[0]), 0)
        dr = ImageDraw.Draw(im)
        for p in polys:
            q = (np.asarray(p, float) - self.c) * self.k + self.c
            dr.polygon([((float(x) - self.x0) * S, (float(y) - self.y0) * S) for x, y in q], fill=255)
        return np.asarray(im, np.float32) / 255.0

    def ell(self, cx, cy, rx, ry, soft=0.7):
        cx, cy = (np.array([cx, cy], float) - self.c) * self.k + self.c
        rx, ry = rx * self.k, ry * self.k
        u, v = (self.X - cx) / rx, (self.Y - cy) / ry
        r = np.sqrt(u * u + v * v)
        return np.clip((1 - r) * min(rx, ry) / soft + 0.5, 0, 1)

    def over(self, rgb, a):
        a = np.clip(a, 0, 1)
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), self.sh + (3,))
        oa = a + self.a * (1 - a)
        self.rgb = (rgb * a[..., None] + self.rgb * (self.a * (1 - a))[..., None]) / np.maximum(oa[..., None], 1e-6)
        self.a = oa

    def save(self, name):
        def down(x):
            if x.ndim == 2:
                return x.reshape(self.h, S, self.w, S).mean((1, 3))
            return x.reshape(self.h, S, self.w, S, x.shape[2]).mean((1, 3))
        rd, ad = down(self.rgb * self.a[..., None]), down(self.a)
        rd = rd / np.maximum(ad[..., None], 1e-6)
        out = np.zeros((N, N, 4), np.float32)
        out[self.y0:self.y0 + self.h, self.x0:self.x0 + self.w] = np.dstack([np.clip(rd, 0, 1), np.clip(ad, 0, 1)])
        Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, name), optimize=True)
        return out

def blur(a, sigma):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma * S)), np.float32) / 255.0

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

stroke, mirror, normals = E.stroke, E.mirror, E.normals

# ------------------------------------------------------------------ eye fit data
def shape_fit(shape):
    tops, bottom = [], 0.0
    for f in glob.glob(os.path.join(EYES, "tiles", f"{shape}_*_fit.json")):
        d = json.load(open(f))
        tops.append(np.array([np.nan if v is None else v for v in d["top"]], float))
        bottom = max(bottom, d["bottom"])
        x0 = d["x0"]
    top = np.nanmin(np.vstack(tops), 0)
    xs = x0 + np.arange(len(top)) + 0.5
    ok = ~np.isnan(top)
    # beyond the lashes, hold the nearest lash height (brows overhang the outer corner)
    top = np.interp(xs, xs[ok], top[ok])
    return xs, top, bottom, len(tops)

# ------------------------------------------------------------------ brows
BROWS = {
    "straight": dict(arch=5, peak=.5, sharp=False, tilt=0, thick=13, lift=4),
    "arched":   dict(arch=20, peak=.55, sharp=False, tilt=0, thick=12, lift=2),
    "angled":   dict(arch=17, peak=.66, sharp=True, tilt=2, thick=13, lift=2),
    "soft":     dict(arch=11, peak=.5, sharp=False, tilt=0, thick=10, lift=6, softedge=True),
    "thick":    dict(arch=9, peak=.5, sharp=False, tilt=0, thick=20, lift=2),
    "thin":     dict(arch=15, peak=.55, sharp=False, tilt=0, thick=6, lift=6),
    "furrowed": dict(arch=4, peak=.6, sharp=False, tilt=15, thick=15, lift=0),
    "raised":   dict(arch=7, peak=.4, sharp=False, tilt=-16, thick=11, lift=8),
    # thicker styles
    "bold":     dict(arch=13, peak=.58, sharp=False, tilt=2, thick=25, lift=2),
    "heavy":    dict(arch=4, peak=.5, sharp=False, tilt=5, thick=30, lift=0),
    "bushy":    dict(arch=8, peak=.5, sharp=False, tilt=0, thick=26, lift=4, bushy=True),
    # 2026-11-01: more range in thickness and arch (owner request)
    "sleek":    dict(arch=24, peak=.6, sharp=False, tilt=0, thick=7, lift=4),
    "flatthick": dict(arch=2, peak=.5, sharp=False, tilt=2, thick=22, lift=1),
    "higharch": dict(arch=28, peak=.58, sharp=False, tilt=0, thick=17, lift=1),
    "sharparch": dict(arch=22, peak=.7, sharp=True, tilt=0, thick=9, lift=3),
    "worried":  dict(arch=9, peak=.42, sharp=False, tilt=-12, thick=11, lift=5),
    "angry":    dict(arch=3, peak=.62, sharp=True, tilt=22, thick=16, lift=0),
    "feathered": dict(arch=12, peak=.52, sharp=False, tilt=0, thick=17, lift=3, softedge=True),
    "wisp":     dict(arch=10, peak=.5, sharp=False, tilt=0, thick=4, lift=7),
    "tapered":  dict(arch=15, peak=.62, sharp=False, tilt=1, thick=14, lift=3),
    "rounded":  dict(arch=17, peak=.5, sharp=False, tilt=0, thick=13, lift=3),
}
BROW_LABEL = dict(straight="Straight", arched="Arched", angled="Angled", soft="Soft", thick="Thick", thin="Thin",
                  furrowed="Furrowed", raised="Raised", bold="Bold", heavy="Heavy", bushy="Bushy",
                  sleek="Sleek", flatthick="Flat Thick", higharch="High Arch", sharparch="Sharp Arch", worried="Worried",
                  angry="Angry", feathered="Feathered", wisp="Wisp", tapered="Tapered", rounded="Rounded")

def brow_profile(t, soft):
    p = (0.72 + 0.28 * smooth(0.0, 0.22, t)) * (1 - 0.86 * smooth(0.5, 1.0, t))
    if soft:
        p = p * (0.85 + 0.15 * np.sin(np.pi * np.clip(t, 0, 1)))
    return p

def brow_line(shape, style, xs_fit, top_fit):
    st, b = E.STYLES[shape], BROWS[style]
    I, O = np.array(st["I"], float), np.array(st["O"], float)
    t = np.linspace(0, 1, 140)
    x = (I[0] + 14) + ((O[0] - 30) - (I[0] + 14)) * t
    a = math.log(0.5) / math.log(b["peak"])
    if b["sharp"]:
        bump = 1 - np.abs(t ** a * 2 - 1) ** 1.15
    else:
        bump = np.sin(np.pi * t ** a) ** 0.9
    y0 = -b["arch"] * bump + b["tilt"] * (1 - t) + (O[1] - I[1]) * 0.35 * t
    w = b["thick"] * brow_profile(t, b.get("softedge", False))
    clear = np.interp(x, xs_fit, top_fit)
    Y = float(np.min(clear - BROW_GAP - b["lift"] - w / 2 - y0))
    return np.stack([x, Y + y0], 1), w

def render_brow(shape, style, xs_fit, top_fit, seed):
    rng = np.random.default_rng(seed)
    C = Canvas(64, 150, 896, 460)
    B, w = brow_line(shape, style, xs_fit, top_fit)
    b = BROWS[style]
    prof = lambda q: brow_profile(q, b.get("softedge", False))
    hairs, bases = [], []
    for side in (0, 1):
        P = B if side == 0 else mirror(B)
        bases.append(stroke(P, b["thick"], prof))
        nP, dP = normals(P)
        if nP[:, 1].mean() > 0:
            nP = -nP
        n = int(70 * b["thick"] / 13 * (1.6 if b.get("bushy") else 1.0)) + 30
        spread = 0.62 if b.get("bushy") else 0.42   # bushy hairs stray past the edge
        for _ in range(n):
            tt = rng.uniform(0.0, 0.97)
            k = int(tt * (len(P) - 1))
            across = rng.uniform(-spread, spread) * w[k]
            base = P[k] + nP[k] * across
            ang = 1.0 - 0.85 * tt   # hairs stand up at the inner end, lie flat toward the tail
            along = dP[k]
            dirv = along * math.cos(ang) + nP[k] * math.sin(ang)
            ln = rng.uniform(8, 15) * (0.6 + 0.4 * b["thick"] / 13)
            hairs.append(stroke(np.linspace(base, base + dirv * ln, 8), rng.uniform(1.6, 2.4), lambda q: np.clip(1 - q, 0, 1) ** 0.7))
    base_m = C.mask(bases)
    hair_m = C.mask(hairs)
    if b.get("softedge"):
        base_m = np.clip(blur(base_m, 1.2) * 1.15, 0, 1)
    alpha = np.clip(base_m * 0.9 + hair_m * 0.55 * (1 - base_m * 0.5), 0, 1)
    tone = 0.80 + 0.2 * hair_m - 0.12 * blur(base_m, 2.5) * (1 - hair_m)
    # inner ends a touch lighter/softer like real brows
    inner = np.exp(-((np.minimum(np.abs(C.X - B[0, 0]), np.abs(C.X - (N - B[0, 0])))) / 18) ** 2)
    alpha = alpha * (1 - 0.25 * inner)
    C.over(np.repeat(np.clip(tone, 0, 1)[..., None], 3, 2), alpha)
    return C.save(f"brow_{style}_{shape}.png")

# ------------------------------------------------------------------ mouths
MCY = 772      # mouth centre line (classic face proportions)
MOUTH_SCALE = 2.8
DARK = np.array([0.30, 0.07, 0.10], np.float32)
TEETH = np.array([0.96, 0.95, 0.91], np.float32)
TONGUE = np.array([0.72, 0.30, 0.34], np.float32)
LIP = np.array([0.70, 0.34, 0.38], np.float32)

def curve(w, k, cy, n=80, skew=0.0, lift=0.0):
    t = np.linspace(0, 1, n)
    x = 512 - w / 2 + w * t
    y = cy + k * np.sin(np.pi * t) - skew * t ** 2 + lift * (1 - np.sin(np.pi * t))
    return np.stack([x, y], 1)

def line_prof(q):
    return np.clip(np.sin(np.pi * np.clip(q, 0, 1)) ** 0.45 * (0.55 + 0.45 * np.sin(np.pi * q)), 0, 1)

LINE = np.array([0.24, 0.08, 0.10], np.float32)       # wine-black line art (Nightmare High)
MAROON = np.array([0.47, 0.11, 0.16], np.float32)     # mouth interior
MAROON_DEEP = np.array([0.30, 0.06, 0.10], np.float32)
ROSE = np.array([0.88, 0.46, 0.50], np.float32)       # tongue
WHITE = np.array([0.97, 0.95, 0.94], np.float32)      # teeth
SHADOW = np.array([0.52, 0.27, 0.30], np.float32)     # soft lower-lip shadow
LIPTINT = np.array([0.86, 0.44, 0.50], np.float32)

def mouth_edges(open_, width, asym=0.0, down=0.0, wscale=1.0, wobble=0.0, n=120):
    """Upper and lower lip edges for a mouth at (open 0..1, width -1 round .. 1 wide smile)."""
    s = (width + 1) / 2
    W = (20 + 9 * width + 3 * open_) * wscale
    t = np.linspace(0, 1, n)
    x = 512 - W + 2 * W * t
    bump = np.sin(np.pi * t)
    lift = 6.5 * max(width, 0) * (1 - open_ * 0.45)
    shape_y = -lift * (1 - bump) + down * (1 - bump) - asym * t ** 2 + wobble * np.sin(3 * np.pi * t)
    h_top = open_ * (11 * (1 - s) + 2.5 * s)
    h_bot = open_ * (13 * (1 - s) + 22 * s)
    p_round = 0.9 - 0.45 * (1 - s)          # round mouths get blunt, oval corners
    top = MCY - h_top * bump ** p_round + shape_y + 1.5 * bump * (1 - open_)
    bot = MCY + h_bot * bump ** (0.8 if s > 0.5 else p_round + 0.1) + shape_y + 1.5 * bump * (1 - open_)
    return np.stack([x, top], 1), np.stack([x, bot], 1), W, h_bot

def render_mouth(style, full_lips, form=None, seed=1):
    """Cel-shaded anime mouths in the NH palette (modelled on an open x width mouth grid)."""
    rng = np.random.default_rng(seed)
    k = MOUTH_SCALE
    C = Canvas(224, 680, 576, 230, scale=k, centre=(512, MCY))
    sy = lambda y: (y - MCY) * k + MCY
    line_polys, thin_polys = [], []

    def edge_stroke(pts, w, ends=0.25):
        return stroke(pts, w, lambda q: np.clip(np.sin(np.pi * np.clip(q, 0, 1)) ** 0.45 * (1 - ends) + ends, 0, 1))

    def poly_between(a, b):
        return np.vstack([a, b[::-1]])

    def cel_mouth(top, bot, h_bot, teeth=True, lower_teeth=False, lens=False, tongue_on=True, dark=False):
        shape = poly_between(top, bot)
        m = C.mask([shape])
        if lens:   # mostly-closed smile: a lens of teeth with a thin gum line at the bottom
            C.over(WHITE, m)
            gum = poly_between(bot - [0, 2.0], bot)
            C.over(MAROON, C.mask([gum]) * m)
            C.over(np.array([0.82, 0.8, 0.84], np.float32), C.mask([poly_between(top, top + [0, 1.4])]) * m * 0.5)
            return shape, m
        C.over(MAROON_DEEP if dark else MAROON, m)
        # soft depth at the back of the mouth
        y0, y1 = sy(top[:, 1].min()), sy(bot[:, 1].max())
        g = np.clip((C.Y - y0) / max(y1 - y0, 1), 0, 1)
        C.over(MAROON_DEEP, m * np.clip(1 - g * 2.2, 0, 1) * 0.45)
        if tongue_on and h_bot > 4:
            ty = top[:, 1] + (bot[:, 1] - top[:, 1]) * 0.56
            ty = np.maximum(ty, bot[:, 1] - h_bot * 0.62)
            tong = poly_between(np.stack([top[:, 0], ty], 1), bot + [0, 2])
            tm = C.mask([tong]) * m
            C.over(ROSE, tm)
            C.over(np.ones(3, np.float32), C.ell(512 - 6, float(ty.mean()) + 3.5, 6, 1.6, soft=1.6) * tm * 0.22)
        if teeth:
            bump = np.sin(np.pi * np.linspace(0, 1, len(top))) ** 0.6
            depth = (1.3 + 3.0 * min(h_bot / 20, 1)) * bump
            band = poly_between(top, top + np.stack([np.zeros_like(depth), depth], 1))
            bm = C.mask([band]) * m
            C.over(WHITE, bm)
        if lower_teeth:
            bump = np.sin(np.pi * np.linspace(0, 1, len(bot))) ** 0.7
            lb = poly_between(bot - np.stack([np.zeros_like(bump), 2.4 * bump], 1), bot)
            C.over(WHITE, C.mask([lb]) * m)
        return shape, m

    def outline(top, bot, wt=2.5, wb=1.9):
        line_polys.append(edge_stroke(top, wt, 0.18))
        line_polys.append(edge_stroke(bot, wb, 0.18))

    def closed(line, w=2.8):
        line_polys.append(edge_stroke(line, w, 0.22))

    def lower_shadow(y, W):
        C.over(SHADOW, C.ell(512, y, W * 0.42, 2.0, soft=2.6) * 0.34)

    def lips(top, bot, W):
        if not full_lips:
            return
        yb = float(bot[:, 1].max())
        C.over(LIPTINT, C.ell(512, yb + 3.2, W * 0.5, 3.6, soft=2.2) * 0.42)
        C.over(np.ones(3, np.float32), C.ell(512 - 4, yb + 2.6, 4.5, 1.1, soft=1.2) * 0.5)
        C.over(LIPTINT, C.ell(512, float(top[:, 1].min()) - 1.8, W * 0.46, 1.6, soft=1.6) * 0.3)

    def fang(x, y, h=8, w=4.6):
        tip = np.array([x + 0.4, y + h])
        poly = np.array([[x - w / 2, y], [x + w / 2, y], tip])
        C.over(WHITE, C.mask([poly]))
        thin_polys.append(edge_stroke(np.vstack([poly, poly[:1]]), 1.2, 1.0))
        return tip

    def zigzag(top, bot, n, up_depth, low_depth, m, canines=()):
        xs = np.linspace(top[0, 0], top[-1, 0], n + 1)
        for i in range(n):
            xa, xb = xs[i], xs[i + 1]
            xc = (xa + xb) / 2
            yu = float(np.interp(xc, top[:, 0], top[:, 1]))
            yl = float(np.interp(xc, bot[:, 0], bot[:, 1]))
            gap = yl - yu
            du = up_depth * (1.9 if i in canines else 1.0)
            C.over(WHITE, C.mask([np.array([[xa, yu - 1], [xb, yu - 1], [xc, yu + min(du, gap * 0.7)]])]) * m)
            if low_depth:
                dl = low_depth * (1.7 if i in canines else 1.0)
                C.over(WHITE, C.mask([np.array([[xa, yl + 1], [xb, yl + 1], [xc, yl - min(dl, gap * 0.6)]])]) * m)

    # ---------------------------------------------------------------- base styles
    SPEC = {   # style: (open, width, extras)
        "neutral": (0.0, 0.0, {}), "smile": (0.0, 1.0, {}), "flat": (0.0, -1.0, {}), "smirk": (0.0, 0.3, {"asym": 7}),
        "hint": (0.1, 0.25, {}), "grin": (0.25, 1.0, {}), "small": (0.25, 0.0, {}), "ooh": (0.6, -1.0, {}),
        "open": (0.6, 0.0, {}), "talk": (0.5, 0.2, {}), "laugh": (1.0, 1.0, {}), "shout": (1.0, -0.4, {}),
        "pout": (0.1, -0.6, {}), "frown": (0.0, -0.2, {"down": 6}), "scowl": (0.0, 0.1, {"down": 9}),
        "sulk": (0.0, -0.6, {"down": 4, "wobble": 1.3}), "grimace": (0.22, 0.5, {"down": 5}),
        "cat": None, "fang": (0.0, 0.8, {}), "shark": (0.35, 0.9, {}),
    }
    if form is None:
        if style == "cat":   # ":3"
            t = np.linspace(0, 1, 70)
            wv = np.stack([512 - 20 + 40 * t, MCY + 5.5 * np.abs(np.sin(np.pi * 2 * t)) - 2], 1)
            closed(wv, 2.6)
            lower_shadow(MCY + 8, 18)
            if full_lips:
                C.over(LIPTINT, C.ell(512, MCY + 7, 10, 3, soft=2) * 0.4)
        else:
            open_, width, ex = SPEC[style]
            top, bot, W, h_bot = mouth_edges(open_, width, ex.get("asym", 0), ex.get("down", 0), 1.0, ex.get("wobble", 0))
            if open_ < 0.02:
                closed((top + bot) / 2, 3.0 if style == "scowl" else 2.8)
                if style == "scowl":
                    for end, sg in ((top[0], -1), (top[-1], 1)):
                        crease = np.array([end + [sg * 4.5 * q, 0.6 + 6.5 * q ** 1.3] for q in np.linspace(0, 1, 8)])
                        thin_polys.append(stroke(crease, 1.7, lambda q: np.clip(1 - q, 0, 1) ** 0.8))
                if style == "fang":
                    y = float(np.interp(512 + 9, top[:, 0], top[:, 1]))
                    fang(512 + 9, y + 0.6, 6.5, 4.2)
                lower_shadow(float(bot[:, 1].max()) + 6.5, W)
            else:
                lens = (open_ <= 0.3 and width > 0.1 and style != "shark")
                if lens:
                    top, bot, W, h_bot = mouth_edges(open_ * 1.35 + 0.04, width, ex.get("asym", 0), ex.get("down", 0), 1.0, ex.get("wobble", 0))
                shape, m = cel_mouth(top, bot, h_bot, teeth=not lens, lower_teeth=(open_ >= 0.55 and width >= -0.2), lens=lens,
                                     tongue_on=style not in ("shark",))
                if style == "shark":
                    zigzag(top, bot, 8, 4.5, 3.8, m)
                if style == "grimace":   # teeth meeting + separations
                    mid = (top + bot) / 2
                    thin_polys.append(edge_stroke(mid, 1.0, 1.0))
                    for i in range(1, 6):
                        x = top[0, 0] + (top[-1, 0] - top[0, 0]) * i / 6
                        yt = float(np.interp(x, top[:, 0], top[:, 1]))
                        yb = float(np.interp(x, bot[:, 0], bot[:, 1]))
                        thin_polys.append(edge_stroke(np.linspace([x, yt + 0.8], [x, yb - 0.8], 5), 0.8, 1.0))
                if lens:
                    outline(top, bot, 1.9, 1.5)
                else:
                    outline(top, bot)
                lower_shadow(float(bot[:, 1].max()) + 6.0, W)
            lips(top, bot, W)
    else:
        if form == "vampire":
            top, bot, W, h_bot = mouth_edges(0.26, 0.55)
            cel_mouth(top, bot, h_bot, lens=True)
            tips = []
            for fx in (-9, 9):
                y = float(np.interp(512 + fx, bot[:, 0], bot[:, 1]))
                tips.append(fang(512 + fx, y - 1.2, 10, 5.0))
            C.over(np.array([0.66, 0.03, 0.1], np.float32), C.ell(tips[1][0] + 0.3, tips[1][1] + 2.6, 1.9, 2.6, soft=0.9))
            C.over(np.ones(3, np.float32), C.ell(tips[1][0] - 0.3, tips[1][1] + 1.8, 0.6, 0.8, soft=0.5) * 0.8)
            outline(top, bot, 1.9, 1.5)
            lower_shadow(float(bot[:, 1].max()) + 7, W)
        elif form == "wolf":
            top, bot, W, h_bot = mouth_edges(0.8, 0.5)
            top = top - np.stack([np.zeros(len(top)), 2.5 * np.sin(np.pi * np.linspace(0, 1, len(top)))], 1)   # lip curled up
            _, m = cel_mouth(top, bot, h_bot, teeth=False, tongue_on=True, dark=True)
            C.over(np.array([0.72, 0.28, 0.34], np.float32), C.mask([poly_between(top, top + [0, 2.6])]) * m)   # gums
            zigzag(top + [0, 2.2], bot, 9, 5.2, 4.2, m, canines=(1, 7))
            outline(top, bot, 2.9, 2.2)
            for sg in (-1, 1):   # snarl wrinkles
                for j in range(2):
                    b0 = np.array([512 + sg * (10 + j * 8), float(top[:, 1].min()) - 5 - j * 2.5])
                    thin_polys.append(edge_stroke(np.array([b0 + [sg * 5 * q, -4.5 * q + 2.5 * q * q] for q in np.linspace(0, 1, 8)]), 1.5, 0.2))
            lower_shadow(float(bot[:, 1].max()) + 6, W)
        elif form == "ghoul":
            top, bot, W, h_bot = mouth_edges(0.3, 1.0, wscale=1.55)
            _, m = cel_mouth(top, bot, h_bot, teeth=False, tongue_on=False, dark=True)
            zigzag(top, bot, 13, 5.0, 4.4, m)
            outline(top, bot, 2.4, 2.0)
            for end, sg in ((top[0], -1), (top[-1], 1)):   # split corners + cross stitches
                split = np.array([end + [sg * 13 * q, -6 * q * q] for q in np.linspace(0, 1, 12)])
                line_polys.append(edge_stroke(split, 2.2, 0.25))
                for j in range(3):
                    c = end + [sg * (3.5 + j * 4), -1.2 - j * 1.1]
                    thin_polys.append(edge_stroke(np.linspace(c + [-1.8, -3], c + [1.8, 3], 5), 1.1, 1.0))
                    thin_polys.append(edge_stroke(np.linspace(c + [1.8, -3], c + [-1.8, 3], 5), 1.1, 1.0))
            lower_shadow(float(bot[:, 1].max()) + 6, W)
        elif form == "wraith":
            top, bot, W, h_bot = mouth_edges(1.0, -1.0)
            hol = C.mask([poly_between(top, bot)])
            for j in range(3):   # smoky wisps
                w_ = C.ell(512 + rng.uniform(-3, 3), float(bot[:, 1].max()) + 5 + j * 7, 4.2 - j * 1.0, 6.5, soft=6)
                C.over(np.array([0.1, 0.1, 0.17], np.float32), w_ * (0.22 - j * 0.06))
            C.over(np.array([0.78, 0.9, 1.0], np.float32), np.clip(blur(hol, 5) - hol, 0, 1) * 0.6)
            y0 = sy(float(top[:, 1].min()))
            g = np.clip((C.Y - y0) / (30 * k), 0, 1)[..., None]
            C.over(np.array([0.02, 0.02, 0.05], np.float32) * (1 - g) + np.array([0.14, 0.14, 0.24], np.float32) * g, hol)
            line_polys.append(edge_stroke(np.vstack([top, bot[::-1], top[:1]]), 1.6, 1.0))

    if line_polys:
        C.over(LINE, C.mask(line_polys))
    if thin_polys:
        C.over(LINE, C.mask(thin_polys) * 0.85)
    key = f"mouth_{form}.png" if form else f"mouth_{style}_{'f' if full_lips else 'm'}.png"
    return C.save(key), key

MOUTHS = ["neutral", "smile", "flat", "smirk", "hint", "grin", "small", "ooh", "open", "talk", "laugh", "shout", "pout",
          "frown", "scowl", "sulk", "grimace", "cat", "fang", "shark"]
MOUTH_LABEL = dict(neutral="Neutral", smile="Smile", flat="Flat", smirk="Smirk", hint="Hint", grin="Grin", small="Small",
                   ooh="Ooh", open="Open", talk="Talk", laugh="Laugh", shout="Shout", pout="Pout", frown="Frown",
                   scowl="Scowl", sulk="Sulk", grimace="Grimace", cat="Cat", fang="Fang", shark="Shark")
MFORMS = ["vampire", "wolf", "ghoul", "wraith"]

def eye_alpha(name):
    a = np.asarray(Image.open(os.path.join(EYES, f"eyes_{name}_main.png")), np.float32)[..., 3] / 255
    vp = os.path.join(EYES, f"eyes_{name}_veins.png")
    if os.path.exists(vp):
        a = np.maximum(a, np.asarray(Image.open(vp), np.float32)[..., 3] / 255)
    return a

if __name__ == "__main__":
    report = []
    shapes = list(E.STYLES)
    eye_names = {sh: sorted(os.path.basename(f)[5:-9] for f in glob.glob(os.path.join(EYES, f"eyes_{sh}_*_main.png"))) for sh in shapes}
    lowest = 0.0
    for k, sh in enumerate(shapes if not os.environ.get("MOUTHS_ONLY") else []):
        if not eye_names[sh]:
            print("skip (no eye renders)", sh)
            continue
        xs, top, bottom, n = shape_fit(sh)
        lowest = max(lowest, bottom)
        eyes_solid = np.max([eye_alpha(nm) for nm in eye_names[sh]], 0) > 0.8
        near = np.asarray(Image.fromarray((eyes_solid * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) > 0
        for j, style in enumerate(BROWS):
            if os.environ.get("NEW_BROWS") and style not in os.environ["NEW_BROWS"].split(","):
                continue
            out = render_brow(sh, style, xs, top, 100 + k * 13 + j)
            bad = int(((out[..., 3] > 0.08) & near).sum())
            if bad:
                report.append(f"BROW OVERLAP {style}_{sh}: {bad}px")
        print("brows ok", sh, "variants", n, flush=True)
    if os.environ.get("NEW_BROWS"):
        print("\n".join(report) if report else "NO OVERLAPS")
        print("done (new brows only)")
        sys.exit(0)
    # (the per-mouth pixel check below is the real guarantee; this is just an early warning)
    if MCY - 20 * MOUTH_SCALE - MOUTH_GAP < lowest:
        report.append(f"MOUTH MAY BE TOO HIGH: lowest eye pixel {lowest:.0f}")
    all_solid = None
    for sh in shapes:
        for nm in eye_names[sh]:
            a = eye_alpha(nm) > 0.05
            all_solid = a if all_solid is None else (all_solid | a)
    for style in MOUTHS:
        for full in (False, True):
            out, key = render_mouth(style, full)
            bad = int(((out[..., 3] > 0.05) & all_solid).sum())
            if bad:
                report.append(f"MOUTH OVERLAP {key}: {bad}px")
    for form in MFORMS:
        out, key = render_mouth(None, False, form)
        bad = int(((out[..., 3] > 0.05) & all_solid).sum())
        if bad:
            report.append(f"MOUTH OVERLAP {key}: {bad}px")
    print("lowest eye pixel", round(lowest, 1))
    print("\n".join(report) if report else "NO OVERLAPS")
    json.dump({"brows": BROW_LABEL, "mouths": MOUTH_LABEL, "mforms": MFORMS}, open(os.path.join(OUT, "labels.json"), "w"))
    print("done")
