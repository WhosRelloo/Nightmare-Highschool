"""High-quality bedroom canvases for the tutorial (replace the first drafts in canvases.py; same output names, so the
WFBedroom prop picks them up): art/props/textures/<name>_canvas.png. Drawn at 2x and filtered down.

  WF_PosterBand   THE GRAVEYARD SHIFT gig poster: a two-colour screen print (orange and aubergine on cream) with halftone
                  shading, a little misregistration, a full guitar against a halftone moon, bats, a crowd with raised hands,
                  the support act and "tickets at Reel Time Video"; aged paper: fibres, fold creases, worn corners, tape
  WF_PosterMoon   a lunar calendar: eight cratered, shaded moons with their phase names, constellation lines, a gilt border
  WF_Pennant      a felt Wicks pennant: fibre texture, stitched edges, raised appliqué letters with stitching, the candle
                  mascot, a gold header strip with grommets (triangular: the prop is cut to the triangle)
  WF_Clock1158    the alarm clock's face: seven-segment red LEDs (unlit segments faintly visible), PM and alarm dots, glass glare

  python art/hometown/posters_hq.py [name ...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos"))
import hometown_logos as H  # noqa: E402

H.SS = 2
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "props", "textures"))


# per-canvas surface: base roughness, roughness where there's ink, how far ink stands off the paper, felt-like fuzz,
# relief strength (normal map), and whether gold-coloured areas are gilt foil (metal)
PBR = {
    "WF_PosterBand": dict(rough=0.86, ink_rough=0.62, ink_lift=0.3, strength=3.0),
    "WF_PosterMoon": dict(rough=0.55, ink_rough=0.45, ink_lift=0.12, strength=2.5, gilt=True),
    "WF_Pennant": dict(rough=0.95, ink_rough=0.95, ink_lift=0.0, fuzz=1.0, strength=4.0),
    "WF_Clock1158": dict(rough=0.06, ink_rough=0.06, ink_lift=0.0, strength=0.5),
    "WF_Cereal": dict(rough=0.32, ink_rough=0.28, ink_lift=0.06, strength=2.0),
    "WF_Gazette": dict(rough=0.92, ink_rough=0.8, ink_lift=0.18, strength=3.0),
    "WF_Envelope": dict(rough=0.72, ink_rough=0.6, ink_lift=0.1, strength=3.5, gilt=True),
    "WF_Brochure": dict(rough=0.25, ink_rough=0.22, ink_lift=0.04, strength=1.8),
    "WF_Calendar": dict(rough=0.6, ink_rough=0.5, ink_lift=0.12, strength=2.5),
    "WF_DadMug": dict(rough=0.12, ink_rough=0.1, ink_lift=0.05, strength=1.5),
    "WF_FridgeArt": dict(rough=0.88, ink_rough=0.55, ink_lift=0.4, strength=3.5),
}


def _down(L, a):
    if a.ndim == 2:
        return a.reshape(L.h, H.SS, L.w, H.SS).mean((1, 3))
    return a.reshape(L.h, H.SS, L.w, H.SS, a.shape[2]).mean((1, 3))


def save(L, name):
    """the colour map, then the PBR maps from what the canvas is made of (PBR[name]): <name>_canvas_normal.png (OpenGL,
    as Roblox), _canvas_rough.png, _canvas_metal.png"""
    L.name = name
    p = L.save()
    Image.open(p).convert("RGB").save(os.path.join(OUT, f"{name}_canvas.png"))
    cfg = dict(rough=0.8, ink_rough=0.7, ink_lift=0.2, fuzz=0.0, strength=2.5, gilt=False)
    cfg.update(PBR.get(name, {}))
    col = _down(L, L.col)
    lum = (col @ np.array([0.299, 0.587, 0.114], np.float32)) / 255.0
    paper = np.percentile(lum, 85)
    ink = np.clip((paper - lum) / max(0.15, paper), 0, 1)              # how much ink (or dark paint) covers each pixel
    rng = np.random.default_rng(sum(map(ord, name)))
    fib = ndimage.gaussian_filter(rng.standard_normal(lum.shape).astype(np.float32), (0.5, 1.6))
    fib /= np.abs(fib).max() + 1e-6
    hgt = 0.12 * fib + cfg["ink_lift"] * ndimage.gaussian_filter(ink, 0.7)
    if cfg["fuzz"]:
        fz = ndimage.gaussian_filter(rng.standard_normal(lum.shape).astype(np.float32), 0.6)
        hgt += cfg["fuzz"] * 0.25 * fz / (np.abs(fz).max() + 1e-6)
    for attr, k in (("crease_h", -0.9), ("extra_h", 1.0)):
        v = getattr(L, attr, None)
        if v is not None:
            hgt += k * _down(L, v)
    gy, gx = np.gradient(hgt)
    st = cfg["strength"]
    nx, ny, nz = -gx * st, gy * st, np.ones_like(hgt)                  # rows go down; v goes up (OpenGL)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
    rough = cfg["rough"] + (cfg["ink_rough"] - cfg["rough"]) * ink
    metal = np.zeros_like(lum)
    if cfg["gilt"]:
        r_, g_, b_ = col[..., 0], col[..., 1], col[..., 2]
        gold = ((r_ > 150) & (g_ > 105) & (b_ < g_ * 0.78) & (r_ - b_ > 70)).astype(np.float32)
        metal = ndimage.gaussian_filter(gold, 0.6)
        rough = rough * (1 - metal) + 0.3 * metal
    ro = getattr(L, "rough_over", None)
    if ro is not None:
        m_, v_ = ro
        m_ = _down(L, m_)
        rough = rough * (1 - m_) + v_ * m_
    u8 = lambda a: np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(u8(nrm), "RGB").save(os.path.join(OUT, f"{name}_canvas_normal.png"))
    Image.fromarray(u8(np.clip(rough, 0, 1)), "L").save(os.path.join(OUT, f"{name}_canvas_rough.png"))
    Image.fromarray(u8(np.clip(metal, 0, 1)), "L").save(os.path.join(OUT, f"{name}_canvas_metal.png"))
    print("ok", name, "(+ normal, rough, metal)")


def noise(L, scale, seed):
    """smooth noise in -1..1 at a feature size of `scale` final pixels"""
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal((L.H, L.W)).astype(np.float32), scale * H.SS)
    return n / (np.abs(n).max() + 1e-6)


def fibres(L, seed, amount=0.07):
    """paper: fine fibres (streaky noise), a soft mottle"""
    rng = np.random.default_rng(seed)
    f = ndimage.gaussian_filter(rng.standard_normal((L.H, L.W)).astype(np.float32), (0.6 * H.SS, 3.0 * H.SS))
    f /= np.abs(f).max() + 1e-6
    m = noise(L, 40, seed + 1)
    L.col *= (1 + amount * f[..., None] + 0.05 * m[..., None])


def age_paper(L, seed, folds=((0.5, "v"),), tape=True):
    """fold creases (a light ridge beside a dark valley), yellowed and worn edges and corners, tape at the top corners"""
    w, h = L.w, L.h
    x, y = L.xx / H.SS, L.yy / H.SS
    for t, d in folds:
        p = (x - t * w) if d == "v" else (y - t * h)
        crease = np.exp(-(p / 1.2) ** 2)
        side = np.exp(-((p - 3) / 3.0) ** 2)
        L.col *= (1 - 0.18 * crease[..., None] + 0.06 * side[..., None])
        L.crease_h = (getattr(L, "crease_h", 0) + crease - 0.3 * side).astype(np.float32)
    edge = np.minimum(np.minimum(x, w - x), np.minimum(y, h - y))
    yel = np.exp(-edge / 30.0)
    L.col = L.col * (1 - 0.25 * yel[..., None]) + np.array([196, 168, 112], np.float32) * 0.25 * yel[..., None]
    rng = np.random.default_rng(seed)
    wear = (noise(L, 1.2, seed + 2) > 0.45) & (edge < 3 + 5 * (noise(L, 25, seed + 3) + 1))
    L.col = np.where(wear[..., None], L.col * 0.7 + np.array([235, 225, 200], np.float32) * 0.3, L.col)
    if tape:
        for cx, cy, a in ((40, 26, -0.5), (w - 40, 26, 0.45)):
            ca, sa = math.cos(a), math.sin(a)
            pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca) for u, v in ((-60, -18), (60, -18), (60, 18), (-60, 18))]
            m = L.poly(pts)
            L.paint(m, "#efe3b8", alpha=0.55)
            L.col *= (1 + 0.04 * noise(L, 2, seed + 4)[..., None] * m[..., None])


def halftone(L, shade, mask, color, cell=7, angle=0.4):
    """screen-print halftone: dots of `color` sized by shade (0..1) inside mask"""
    x, y = L.xx / H.SS, L.yy / H.SS
    ca, sa = math.cos(angle), math.sin(angle)
    u, v = x * ca + y * sa, -x * sa + y * ca
    du, dv = (u % cell) - cell / 2, (v % cell) - cell / 2
    r = np.hypot(du, dv)
    rad = np.sqrt(np.clip(shade, 0, 1)) * cell * 0.62
    dots = np.clip(rad - r + 0.5, 0, 1) * mask
    L.paint(dots, color)


def ink(L, mask, color, seed, reg=(0, 0)):
    """a screen-printed flat: slightly offset (misregistration), the ink a touch uneven"""
    m = np.roll(np.roll(mask, int(reg[1] * H.SS), 0), int(reg[0] * H.SS), 1)
    c = H.rgb(color)
    k = m * (0.9 + 0.1 * (noise(L, 1.5, seed) > -0.6))
    L.col = L.col * (1 - k[..., None] * 0.92) + c * k[..., None] * 0.92
    L.a = np.maximum(L.a, m)


# ================================================================== the gig poster
def band_poster():
    L = H.Logo("WF_PosterBand", 1024, 1536)
    W, Hh = 1024, 1536
    CREAM, ORANGE, AUB = "#efe2c4", "#e2622e", "#2b1d33"
    page = L.rrect(0, 0, W, Hh, 0)
    L.paint(page, CREAM)
    fibres(L, 40)
    cx, cy = 512, 560
    moon = L.ellipse(cx, cy, 330)
    # the moon: flat orange with a halftone shadow toward the lower right and halftone craters
    ink(L, moon, ORANGE, 41)
    xx, yy = L.xx / H.SS, L.yy / H.SS
    shade = np.clip(((xx - cx) * 0.6 + (yy - cy) * 0.8) / 330 * 0.9, 0, 1)
    for (kx, ky, kr) in ((-120, -90, 60), (90, -150, 40), (140, 60, 75), (-60, 140, 50), (-180, 60, 30), (40, 20, 26)):
        d = np.hypot(xx - cx - kx, yy - cy - ky) / kr
        shade = np.maximum(shade, np.clip(1 - d, 0, 1) * 0.55)
    halftone(L, shade, moon, "#b8401c", cell=8, angle=0.3)
    # bats crossing the moon
    rng = np.random.default_rng(42)
    for i in range(7):
        bx, by, s = cx + rng.uniform(-300, 300), cy + rng.uniform(-300, -60), rng.uniform(16, 30)
        wing = [(bx, by)]
        for k in range(7):
            t = k / 6
            wing.append((bx - s * (0.3 + 2.0 * t), by - s * 0.6 * math.sin(math.pi * t) + s * 0.25 * (k % 2)))
        wing2 = [(2 * bx - x_, y_) for x_, y_ in reversed(wing[1:])]
        ink(L, L.poly(wing + wing2) + L.ellipse(bx, by + s * 0.1, s * 0.22, s * 0.32), AUB, 43 + i, reg=(1, 1))
    # the guitar: body, neck, headstock with tuners, strings, a pickguard
    neck = L.poly([(498, 980), (526, 980), (532, 360), (492, 360)])
    head = L.poly([(484, 366), (540, 366), (552, 250), (512, 214), (472, 250)])
    body = np.clip(L.ellipse(512, 1080, 150, 130) + L.ellipse(512, 940, 112, 100), 0, 1)
    waist = np.clip(L.ellipse(370, 1000, 40, 50) + L.ellipse(654, 1000, 40, 50), 0, 1)
    gtr = np.clip(neck + head + body - waist, 0, 1)
    ink(L, gtr, AUB, 44, reg=(2, 1))
    hole = L.ellipse(512, 1000, 46)
    L.paint(hole, CREAM)
    L.paint(np.clip(L.ellipse(512, 1000, 56) - L.ellipse(512, 1000, 50), 0, 1), CREAM)
    for k in range(6):
        sx = 503 + k * 3.6
        L.paint(L.line([(sx, 380), (sx + (k - 2.5) * 0.6, 1130)], 0.8), CREAM, alpha=0.8)
        for side in (-1, 1):
            if (k < 3) == (side < 0):
                L.paint(L.ellipse(512 + side * 46, 262 + (k % 3) * 28, 9, 6), CREAM)
    for f_ in range(9):
        L.paint(L.line([(494, 420 + f_ * 62), (530, 420 + f_ * 62)], 1.2), CREAM, alpha=0.6)
    L.paint(L.rrect(470, 1110, 554, 1124, 4), CREAM)            # the bridge
    # the crowd: heads and raised hands along the bottom of the art
    crowd = np.zeros((L.H, L.W), np.float32)
    for i in range(16):
        x0 = 20 + i * 64 + rng.uniform(-10, 10)
        hy = 1180 + rng.uniform(-20, 20)
        crowd = np.maximum(crowd, L.ellipse(x0, hy, 30, 34))
        crowd = np.maximum(crowd, L.rrect(x0 - 40, hy + 20, x0 + 40, 1300, 26))
        if rng.random() < 0.55:
            ax = x0 + rng.uniform(-20, 20)
            crowd = np.maximum(crowd, L.stroke_round([(x0 + 18, hy + 30), (ax + 26, hy - 80), (ax + 30, hy - 110)], 14))
            for fgr in range(3):
                crowd = np.maximum(crowd, L.stroke_round([(ax + 30, hy - 110), (ax + 22 + fgr * 8, hy - 132)], 6))
    ink(L, crowd, AUB, 45, reg=(2, 1))
    # the text band
    band = L.rrect(0, 1290, W, Hh, 0)
    ink(L, band, AUB, 46)
    for t, f, px, y, sp, col in (("THE GRAVEYARD", "lucky", 100, 1356, 6, CREAM), ("SHIFT", "lucky", 140, 1436, 20, ORANGE),
                                 ("with special guests THE NOCTURNES", "georgiai", 30, 1496, 0, CREAM)):
        ink(L, L.text(t, f, px, W / 2, y, spacing=sp), col, 47, reg=(1, 0) if col == ORANGE else (0, 0))
    # the top line and the side strip
    for t, y in (("LIVE AT THE GRANGE HALL", 60), ("SATURDAY · 9 PM · ALL AGES", 110)):
        ink(L, L.text(t, "georgiab", 36, W / 2, y, spacing=6), AUB, 48)
    ink(L, L.text("TICKETS $5 AT REEL TIME VIDEO", "lucky", 26, W / 2, 158, spacing=4), ORANGE, 49, reg=(1, 1))
    # a printer's frame line
    L.paint(np.clip(L.rrect(14, 14, W - 14, Hh - 14, 0) - L.rrect(20, 20, W - 20, Hh - 20, 0), 0, 1), AUB, alpha=0.7)
    age_paper(L, 50, folds=((0.5, "v"), (0.5, "h")))
    save(L, "WF_PosterBand")


# ================================================================== the lunar calendar
def crater_moon(L, cx, cy, r, seed):
    """a lit full-moon colour field (maria, craters with bright rims, limb darkening) over the disc; returns colour"""
    x, y = (L.xx / H.SS - cx) / r, (L.yy / H.SS - cy) / r
    d = np.hypot(x, y)
    base = np.array([238, 232, 212], np.float32)
    maria = (noise(L, r * 0.35, seed) + 0.4 * noise(L, r * 0.12, seed + 1))
    tone = 1 - 0.22 * np.clip(maria, 0, 1)
    rng = np.random.default_rng(seed)
    for _ in range(22):
        kx, ky, kr = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), rng.uniform(0.04, 0.16)
        dd = np.hypot(x - kx, y - ky) / kr
        tone = tone - 0.14 * np.clip(1 - dd, 0, 1) ** 0.5 * (dd < 1)
        rim = np.exp(-((dd - 1.0) / 0.18) ** 2) * (((x - kx) * -0.6 + (y - ky) * -0.8) > 0)
        tone = tone + 0.1 * rim
    limb = np.sqrt(np.clip(1 - d ** 2, 0, 1)) ** 0.35
    tone = tone * (0.55 + 0.45 * limb) * (1 + 0.04 * noise(L, 1.2, seed + 3))
    return base * tone[..., None]


def moon_poster():
    L = H.Logo("WF_PosterMoon", 1024, 1536)
    W, Hh = 1024, 1536
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, L.vgrad("#1e2850", "#0a0e22", 0, Hh))
    L.col *= (1 + 0.05 * noise(L, 60, 60)[..., None])
    rng = np.random.default_rng(61)
    for _ in range(420):
        x, y, r = rng.uniform(0, W), rng.uniform(0, Hh), rng.uniform(0.5, 2.4)
        L.paint(L.ellipse(x, y, r), "#f6eed6", alpha=rng.uniform(0.3, 1))
    # constellation lines (the Plough-ish dipper and a W), faint gold
    for pts in (((120, 1290), (190, 1260), (250, 1275), (300, 1310), (330, 1370), (420, 1360), (430, 1300)),
                ((700, 1290), (760, 1350), (810, 1300), (860, 1360), (920, 1305))):
        L.paint(L.line(list(pts), 1.6), "#d8b86a", alpha=0.45)
        for p_ in pts:
            L.paint(L.ellipse(p_[0], p_[1], 4), "#fff4d0")
            L.glow(L.ellipse(p_[0], p_[1], 4), "#fff4d0", 4, 0.5)
    # the gilt border with corner stars
    frame = np.clip(L.rrect(30, 30, W - 30, Hh - 30, 10) - L.rrect(40, 40, W - 40, Hh - 40, 8), 0, 1)
    frame2 = np.clip(L.rrect(52, 52, W - 52, Hh - 52, 6) - L.rrect(55, 55, W - 55, Hh - 55, 6), 0, 1)
    L.paint(frame, L.vgrad("#f4d892", "#9a7432", 0, Hh))
    L.paint(frame2, "#c9a35a", alpha=0.8)
    for x, y in ((46, 46), (W - 46, 46), (46, Hh - 46), (W - 46, Hh - 46)):
        L.paint(H.star(L, x, y, 16), "#f4d892")
    L.paint(L.text("LUNAR", "georgiab", 120, W / 2, 170, spacing=18), L.vgrad("#fbe6a8", "#b8893a", 110, 230))
    L.paint(L.text("CALENDAR", "georgia", 52, W / 2, 260, spacing=16), "#d8b86a")
    L.paint(L.line([(300, 300), (724, 300)], 2), "#d8b86a", alpha=0.7)
    names = ["NEW MOON", "WAXING CRESCENT", "FIRST QUARTER", "WAXING GIBBOUS", "FULL MOON", "WANING GIBBOUS", "LAST QUARTER", "WANING CRESCENT"]
    R = 78
    for i in range(8):
        cx, cy = 290 + (i % 2) * 444, 420 + (i // 2) * 228
        disc = L.ellipse(cx, cy, R)
        lit_col = crater_moon(L, cx, cy, R, 70 + i)
        nx, ny = (L.xx / H.SS - cx) / R, (L.yy / H.SS - cy) / R
        edge = np.sqrt(np.clip(1 - ny ** 2, 0, 1))
        ph = i / 8.0
        c_ = math.cos(2 * math.pi * ph)
        term = np.where(ph <= 0.5, nx - c_ * edge, -c_ * edge - nx) if False else (nx - c_ * edge if ph <= 0.5 else -c_ * edge - nx)
        lit = np.clip(term * R / 3 + 0.5, 0, 1) * disc                    # a soft terminator
        earth = lit_col * np.array([0.16, 0.18, 0.28], np.float32)         # earthshine on the dark side
        col = earth * (1 - lit[..., None]) + lit_col * lit[..., None]
        L.glow(disc * (0.3 + 0.7 * lit.mean() / max(1e-6, disc.mean())), "#f6eed6", 14, 0.35)
        L.paint(disc, col)
        L.paint(L.text(names[i], "georgiab", 21, cx, cy + R + 30, spacing=3), "#d8b86a")
    L.paint(L.text("WICKFIELD ALMANAC CO.  ·  KEEP AN EYE ON THE SKY", "georgia", 20, W / 2, Hh - 80, spacing=3), "#a88c50")
    fibres(L, 62, amount=0.03)
    age_paper(L, 63, folds=(), tape=True)
    save(L, "WF_PosterMoon")


# ================================================================== the felt pennant
def pennant():
    L = H.Logo("WF_Pennant", 2048, 768)
    W, Hh = 2048, 768
    tri = L.poly([(150, 0), (W, Hh / 2), (150, Hh)])
    L.paint(L.rrect(0, 0, W, Hh, 0), "#1a3d29")                        # (outside the triangle: cut off by the mesh)
    L.paint(tri, L.vgrad("#2f7049", "#1d4430", 0, Hh))
    # felt: fuzzy fibres everywhere, slightly brighter on top
    rng = np.random.default_rng(80)
    fz = ndimage.gaussian_filter(rng.standard_normal((L.H, L.W)).astype(np.float32), 0.8 * H.SS)
    fz /= np.abs(fz).max()
    L.col *= (1 + 0.16 * fz[..., None] + 0.05 * noise(L, 30, 81)[..., None])
    # the stitched edge: a dashed cream line just inside the triangle edges
    inner = L.grow(tri, -16)
    edge_line = np.clip(L.grow(inner, 2) - inner, 0, 1)
    x, y = L.xx / H.SS, L.yy / H.SS
    dash = ((x + y * 0.3) % 22 < 12).astype(np.float32)
    L.paint(edge_line * dash, "#efe2c4")
    # the header strip: gold felt with two brass grommets
    head = L.rrect(0, 0, 170, Hh, 0)
    L.paint(head, L.vgrad("#f0c24a", "#c99428", 0, Hh))
    L.col *= (1 + 0.14 * fz[..., None] * head[..., None])
    L.paint(L.line([(160, 0), (160, Hh)], 3) * ((y % 22) < 12), "#7a5a18")
    for gy in (110, Hh - 110):
        ring = np.clip(L.ellipse(85, gy, 30) - L.ellipse(85, gy, 16), 0, 1)
        L.paint(ring, L.vgrad("#fff0b0", "#9a7020", gy - 30, gy + 30))
        L.shade(ring, strength=0.5, blur=2)
        L.paint(L.ellipse(85, gy, 16), "#1a120c")
    # appliqué letters: cream felt cut out, a drop shadow, stitched round the edge
    word = L.text("WICKS", "lucky", 330, 1020, 400, spacing=24)
    sh = np.roll(np.roll(word, 6 * H.SS, 0), 6 * H.SS, 1)
    L.paint(sh * tri, "#0e2418", alpha=0.6)
    L.paint(L.grow(word, 8), "#e3b23c")
    L.paint(word, "#f6ecd4")
    L.col *= (1 + 0.12 * fz[..., None] * L.grow(word, 8)[..., None])
    st = np.clip(L.grow(word, -5) - L.grow(word, -7), 0, 1) * dash
    L.paint(st, "#c8b48a")
    L.extra_h = 0.6 * L.grow(word, 8) + 0.3 * word - 0.25 * st + 0.4 * head
    # the candle mascot (small): flame with a face, a cream candle with a green band
    cx, cy = 380, 400
    cand = L.rrect(cx - 50, cy + 10, cx + 50, cy + 170, 12)
    L.paint(L.grow(cand, 6), "#14110f")
    L.paint(cand, "#f6ecd4")
    L.paint(L.rrect(cx - 50, cy + 110, cx + 50, cy + 126, 2), "#2f7049")
    fl = []
    for i in range(121):
        t = 2 * math.pi * i / 120
        fl.append((cx + 92 * math.sin(t) * math.sin(t / 2) ** 1.3, cy - 30 - 120 * math.cos(t) * (1.0 if math.cos(t) > 0 else 0.5)))
    flame = np.clip(L.poly(fl) + L.ellipse(cx, cy - 22, 66, 54), 0, 1)
    L.paint(L.grow(flame, 6), "#14110f")
    L.paint(flame, L.vgrad("#fff3b0", "#f07a1a", cy - 160, cy + 20))
    for sx in (-1, 1):
        L.paint(L.ellipse(cx + sx * 18, cy - 30, 7, 10), "#14110f")
        L.paint(L.poly([(cx + sx * 6, cy - 50), (cx + sx * 32, cy - 58), (cx + sx * 32, cy - 51), (cx + sx * 8, cy - 43)]), "#14110f")
    L.paint(L.m(lambda d, s: d.chord(((cx - 22) * s, (cy - 22) * s, (cx + 22) * s, (cy + 6) * s), 0, 180, fill=255)), "#14110f")
    save(L, "WF_Pennant")


# ================================================================== the alarm clock face
SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcfgd"}


def seven_seg(L, ch, x, y, w, h, t):
    """one digit's segment masks (lit, all) with slanted, pointed segments; x, y the top left"""
    sl = 0.12 * w

    def hseg(yy):
        return L.poly([(x + t * 0.6 - sl * yy / h, y + yy), (x + t - sl * yy / h, y + yy - t / 2), (x + w - t - sl * yy / h, y + yy - t / 2),
                       (x + w - t * 0.6 - sl * yy / h, y + yy), (x + w - t - sl * yy / h, y + yy + t / 2), (x + t - sl * yy / h, y + yy + t / 2)])

    def vseg(xx, y0, y1):
        return L.poly([(xx - sl * y0 / h, y + y0 + t * 0.6), (xx + t / 2 - sl * (y0 + t) / h, y + y0 + t), (xx + t / 2 - sl * (y1 - t) / h, y + y1 - t),
                       (xx - sl * y1 / h, y + y1 - t * 0.6), (xx - t / 2 - sl * (y1 - t) / h, y + y1 - t), (xx - t / 2 - sl * (y0 + t) / h, y + y0 + t)])
    segs = {"a": hseg(t / 2), "g": hseg(h / 2), "d": hseg(h - t / 2),
            "f": vseg(x + t / 2, 0, h / 2), "b": vseg(x + w - t / 2, 0, h / 2), "e": vseg(x + t / 2, h / 2, h), "c": vseg(x + w - t / 2, h / 2, h)}
    lit = np.zeros((L.H, L.W), np.float32)
    allm = np.zeros((L.H, L.W), np.float32)
    for k, m in segs.items():
        allm = np.maximum(allm, m)
        if k in SEG.get(ch, ""):
            lit = np.maximum(lit, m)
    return lit, allm


def clock():
    L = H.Logo("WF_Clock1158", 1024, 512)
    face = L.rrect(0, 0, 1024, 512, 40)
    L.paint(face, L.vgrad("#140a0a", "#060404", 0, 512))
    L.col *= (1 + 0.04 * noise(L, 1, 90)[..., None])
    lit_all = np.zeros((L.H, L.W), np.float32)
    off_all = np.zeros((L.H, L.W), np.float32)
    for ch, x in zip("1158", (60, 250, 530, 720)):
        lit, allm = seven_seg(L, ch, x, 110, 160, 290, 34)
        lit_all = np.maximum(lit_all, lit)
        off_all = np.maximum(off_all, allm)
    L.paint(np.clip(off_all - lit_all, 0, 1), "#2a0c08")
    colon = L.ellipse(470, 200, 15) + L.ellipse(460, 320, 15)
    L.glow(np.clip(lit_all + colon, 0, 1), "#ff2a14", 22, 0.7)
    L.paint(lit_all + 0, "#ff3a1e")
    L.paint(np.clip(colon, 0, 1), "#ff3a1e")
    L.paint(L.grow(lit_all, -4), "#ffb090", alpha=0.6)
    for t, y, on in (("PM", 160, True), ("ALARM", 300, True)):
        L.paint(L.ellipse(930, y, 12), "#ff3a1e" if on else "#2a0c08")
        L.glow(L.ellipse(930, y, 12), "#ff2a14", 10, 0.6)
        L.paint(L.text(t, "georgiab", 22, 930, y + 34), "#a8301c")
    # the glass: a soft diagonal glare and a thin top highlight
    x_, y_ = L.xx / H.SS, L.yy / H.SS
    glare = np.clip(1 - np.abs((x_ * 0.5 + y_) - 260) / 120, 0, 1) * 0.12 * (y_ < 300)
    L.col = L.col * (1 - glare[..., None]) + 255 * glare[..., None]
    L.paint(L.rrect(40, 14, 984, 22, 4), "#ffffff", alpha=0.15)
    save(L, "WF_Clock1158")


if __name__ == "__main__":
    want = sys.argv[1:]
    for fn in (band_poster, moon_poster, pennant, clock):
        if not want or fn.__name__ in want:
            fn()
