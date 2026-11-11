"""Health bar v3: three design concepts with their variants, baked like the other HUD art (make_health_pbr's shader).

Every concept keeps the current outer size (600 x 50 design px) and the orb in the middle, so the 1.74.0 posture
rail still hangs under it. Each is shown with seven variants:
  Human (default) | Vampire | Wolf | Ghoul | Wraith   (the transformation forms, colours from UI.Appearance / Lineage)
  Low health (18%) | Downed (5%)
Output: art/ui/hud/out/health_v3/concept_<A|B|C>.png and health-v3-options.jpg (all three).

  A  Votive    the current iron-and-brass frame, refined; the orb becomes a brass lantern with a candle flame inside
               that burns tall at full health and gutters as you weaken; the fill is blood-glass with a wax-drip edge
  B  Chapel    a new frame of gothic lancet windows: the bar is stained glass in leaded panes behind iron mullions
               and cusped arches, and the orb is a rose window
  C  Ivory     a carved ivory band with brass edging and engraved ink scrollwork; the orb is a pressed wax seal

  python make_health_v3_concepts.py
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("hp", HERE / "make_health_pbr.py")
hp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hp)
_spec2 = importlib.util.spec_from_file_location("pp", HERE / "make_posture_pbr.py")
pp = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(pp)

OUT = HERE / "out" / "health_v3"
OUT.mkdir(parents=True, exist_ok=True)
HEALTH = HERE / "out" / "health_v2"
POSTURE = HERE / "out" / "posture"
DOCS = HERE.parents[2] / "docs" / "img"
SC = 2
W4, H4 = 2400, 200                 # frames are baked at 4x (600 x 50)
WX0, WX1, WY0, WY1 = 150, 2250, 52, 148

VARIANTS = [  # name, fill colour, accent (gems, flame, glass), health shown
    ("Human", (150, 22, 34), (200, 40, 60), 0.82),
    ("Vampire", (120, 8, 26), (220, 34, 52), 0.82),
    ("Wolf", (150, 70, 20), (236, 158, 40), 0.82),
    ("Ghoul", (92, 104, 74), (170, 200, 150), 0.82),
    ("Wraith", (70, 110, 150), (158, 220, 255), 0.82),
    ("Low health", (150, 22, 34), (255, 90, 70), 0.18),
    ("Downed", (70, 60, 62), (255, 120, 60), 0.05),
]


def font(size, bold=True):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf", size)
    except OSError:
        return ImageFont.load_default()


def tint(im, rgb, mul=1.0):
    a = np.array(im.convert("RGBA"), np.float32)
    a[..., :3] = np.clip(a[..., :3] * np.array(rgb, np.float32) / 255.0 * mul, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def dist(m):
    return ndimage.distance_transform_edt(m > 0.5)


def to_img(rgb, alpha):
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(alpha, 0, 1) * 255]).astype(np.uint8), "RGBA")


def glow(size, rgb, strength=1.0, power=2.0):
    w, h = size
    YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((XX - w / 2) / (w / 2), (YY - h / 2) / (h / 2))
    a = np.clip(1 - r, 0, 1) ** power * strength
    return Image.fromarray(np.clip(np.dstack([np.full((h, w), c, np.float32) for c in rgb] + [a * 255]), 0, 255).astype(np.uint8), "RGBA")


# ================================================================ shared pieces
def mats(W, H):
    iron = hp.material("Iron", (W, H), 384, tint=(0.26, 0.25, 0.28), rough_mul=0.72)
    brass = hp.material("Brass", (W, H), 320, tint=(1.0, 0.86, 0.62), rough_mul=0.7, rough_add=-0.05)
    return iron, brass


def outer_masks():
    pm = hp.polymask
    outer = [(6, 100), (70, 20), (W4 - 70, 20), (W4 - 6, 100), (W4 - 70, 180), (70, 180)]
    body = pm((W4, H4), [outer])
    window = pm((W4, H4), [[(WX0, WY0), (WX1, WY0), (WX1, WY1), (WX0, WY1)]])
    return body, window


def gem_sockets():
    pm = hp.polymask
    gems, rings = [], []
    for cx in (92, W4 - 92):
        rings.append((cx - 40, 60, cx + 40, 140))
        gems.append((cx - 27, 73, cx + 27, 127))
    ring = np.clip(pm((W4, H4), [], rings) - pm((W4, H4), [], gems), 0, 1)
    gem = pm((W4, H4), [], gems)
    return ring, gem


# ================================================================ A: Votive (current frame, lantern orb, wax edge)
def frame_A():
    return Image.open(HEALTH / "frame.png").convert("RGBA")


def gem_overlay(accent, strength=0.8):
    """Re-glaze the end gems in the variant's colour (in game: a tinted glass ImageLabel over each socket)."""
    S = 64
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    r = np.hypot(XX - c, YY - c) / 27
    m = np.clip((1 - r) * 27 / 1.2, 0, 1)
    z = np.sqrt(np.clip(1 - r ** 2, 0, 1))
    acc = np.array(accent, np.float32) / 255
    lum = 0.35 + 0.55 * z + np.exp(-(((XX - c + 8) / 9) ** 2 + ((YY - c + 9) / 7) ** 2)) * 0.9
    lum += np.exp(-(((XX - c) / 14) ** 2 + ((YY - c - 10) / 8) ** 2)) * 0.4   # inner glow from below
    rgb = np.clip(acc[None, None, :] * lum[..., None] * strength + np.exp(-(((XX - c + 8) / 5) ** 2 + ((YY - c + 9) / 4) ** 2))[..., None] * 0.8, 0, 1)
    disk = to_img(rgb, m)
    img = Image.new("RGBA", (W4, H4))
    for cx in (92, W4 - 92):
        img.alpha_composite(disk, (cx - S // 2, 100 - S // 2))
    return img


def flame(size, accent, height=1.0, ember=False):
    """A candle flame: a round-bottomed teardrop with a white-hot core and a coloured skirt; `height` 0..1 shrinks it."""
    S = size
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    cx, wick = S / 2, S * 0.70
    acc = np.array(accent, np.float32) / 255
    out = Image.new("RGBA", (S, S))
    if ember:
        r = np.hypot(XX - cx, YY - wick)
        e = np.clip(1 - r / (S * 0.07), 0, 1) ** 1.5
        out.alpha_composite(glow((S, S), accent, 0.22, 3))
        out.alpha_composite(to_img(acc[None, None, :] * 1.2 * e[..., None] + e[..., None] ** 3 * 0.5, e))
        return out
    h = S * (0.16 + 0.42 * height)            # wick to tip
    rb = S * (0.055 + 0.065 * height)          # radius of the round bottom
    yb = wick - rb * 0.6                       # centre of the round bottom
    t = np.clip((yb - YY) / (h - rb), 0, 1)    # 0 at the bulb, 1 at the tip
    half = np.where(YY > yb, np.sqrt(np.clip(rb ** 2 - (YY - yb) ** 2, 0, None)), rb * (1 - t) ** 1.6)
    half = np.where((YY < yb) & (t >= 1), 0, half)
    d = np.abs(XX - cx) / (half + 1e-3)
    m = np.clip((1 - d) * half / 1.5, 0, 1)
    core = np.clip(1 - d * 1.5, 0, 1) * np.clip(1 - t * 1.25, 0, 1) * (YY < wick)
    blue = np.clip(1 - np.abs(YY - (yb + rb * 0.7)) / (rb * 0.5), 0, 1) * (d < 0.9) * 0.35
    rgb = acc[None, None, :] * (0.75 + 0.5 * t[..., None]) * m[..., None]
    rgb = rgb * (1 - core[..., None]) + np.array([1.0, 0.96, 0.86]) * core[..., None]
    rgb = rgb * (1 - blue[..., None]) + np.array([0.35, 0.45, 0.9]) * blue[..., None]
    out.alpha_composite(glow((S, S), accent, 0.30 * (0.4 + height), 2.6))
    out.alpha_composite(to_img(np.clip(rgb, 0, 1), np.clip(m, 0, 1)))
    return out


def orb_A(accent, health, state):
    S = 512
    out = Image.new("RGBA", (S, S))
    glass = tint(Image.open(HEALTH / "orb_glass.png"), (40, 30, 34), 1.3)      # smoked lantern glass
    out.alpha_composite(glass)
    fl = flame(S, accent, height=1.0 if health > 0.5 else 0.35 if health > 0.1 else 0.1, ember=state == "Downed")
    out.alpha_composite(fl)
    # brass lantern cage: four curved ribs over the glass
    cage = Image.new("L", (S * 2, S * 2), 0)
    d = ImageDraw.Draw(cage)
    for x in (0.30, 0.43, 0.57, 0.70):
        bow = (x - 0.5) * 0.35
        pts = [((x + bow * math.sin(math.pi * k / 20)) * S * 2, (0.12 + 0.76 * k / 20) * S * 2) for k in range(21)]
        d.line(pts, fill=255, width=14)
    d.line([(0.22 * S * 2, 0.5 * S * 2), (0.78 * S * 2, 0.5 * S * 2)], fill=0, width=1)
    cage = np.array(cage.resize((S, S), Image.LANCZOS), np.float32) / 255
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    inside = (np.hypot(XX - S / 2, YY - S / 2) < 186).astype(np.float32)
    cage *= inside
    _, brass = mats(S, S)
    Hf = cage * (0.6 + 0.4 * hp.dome(dist(cage), 5))
    N = hp.normals_from(Hf, 26.0, brass[1], 0.3)
    rgb = hp.shade(brass[0], N, brass[2], np.ones((S, S)), hp.ao_from(Hf, 4, 2.0))
    out.alpha_composite(to_img(rgb, cage))
    out.alpha_composite(Image.open(HEALTH / "orb_ring.png").convert("RGBA"))
    return out


def fill_A(color):
    return tint(Image.open(HEALTH / "fill.png"), color, 1.05)


# ================================================================ B: Chapel (lancet stained glass)
def frame_B():
    W, H = W4, H4
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = mats(W, H)
    pm = hp.polymask
    body, window = outer_masks()
    band = np.clip(body - window, 0, 1)
    ring, gem = gem_sockets()
    # mullions: 6 panes a side, each with a cusped pointed arch in the top band and a sill in the bottom one
    mull = np.zeros((H, W), np.float32)
    arches = np.zeros((H, W), np.float32)
    half_l = (W / 2 - 230) - WX0
    xs = []
    for side in (-1, 1):
        for k in range(7):
            x = (WX0 + half_l * k / 6) if side < 0 else (W / 2 + 230 + half_l * k / 6)
            xs.append(x)
    for x in xs:
        mull = np.maximum(mull, (np.abs(XX - x) < 5).astype(np.float32) * ((YY >= WY0 - 2) & (YY <= WY1 + 2)))
    xs_sorted = sorted(xs)
    for a, b in zip(xs_sorted[:-1], xs_sorted[1:]):
        if b - a > 400:
            continue
        mid, half = (a + b) / 2, (b - a) / 2
        # pointed arch outline hanging just inside the window top
        for t in np.linspace(0, 1, 240):
            for s in (-1, 1):
                ang = t * math.pi / 2
                px = mid + s * half * (1 - math.sin(ang)) * 0.98
                py = WY0 + 34 - 34 * math.sin(ang) ** 0.6 * 1.0
                arches[int(np.clip(py, 0, H - 1)) - 3:int(np.clip(py, 0, H - 1)) + 4, int(px) - 3:int(px) + 4] = 1
    arches = ndimage.gaussian_filter(arches, 0.8) * window
    # the arches' spandrels (above the arch curve) are solid iron tracery
    span = np.zeros((H, W), np.float32)
    for a, b in zip(xs_sorted[:-1], xs_sorted[1:]):
        if b - a > 400:
            continue
        mid, half = (a + b) / 2, (b - a) / 2
        u = np.clip(np.abs(XX - mid) / half, 0, 1)
        curve = WY0 + 34 - 34 * np.clip(1 - u, 0, 1) ** 0.6
        span = np.maximum(span, ((YY < curve) & (np.abs(XX - mid) < half)).astype(np.float32))
    span *= window
    tracery = np.clip(mull + arches + span, 0, 1)
    collar = pm((W, H), [[(W / 2 - 230, 14), (W / 2 + 230, 14), (W / 2 + 180, 58), (W / 2 - 180, 58)],
                         [(W / 2 - 180, 142), (W / 2 + 180, 142), (W / 2 + 230, 186), (W / 2 - 230, 186)]])
    bead_in = np.clip(pm((W, H), [[(WX0 - 7, WY0 - 7), (WX1 + 7, WY0 - 7), (WX1 + 7, WY1 + 7), (WX0 - 7, WY1 + 7)]]) - window, 0, 1)
    spikes = pm((W, H), [[(0, 100), (26, 88), (40, 100), (26, 112)], [(W, 100), (W - 26, 88), (W - 40, 100), (W - 26, 112)]])
    Hf = band * (0.3 + 0.5 * hp.dome(dist(band), 13))
    Hf = np.maximum(Hf, tracery * (0.5 + 0.3 * hp.dome(dist(tracery), 3)))
    Hf = np.maximum(Hf, bead_in * (0.62 + 0.25 * hp.dome(dist(bead_in), 4)))
    Hf = np.maximum(Hf, collar * (0.75 + 0.2 * hp.dome(dist(collar), 8)))
    Hf = np.maximum(Hf, ring * (0.85 + 0.3 * hp.dome(dist(ring), 6)))
    Hf = np.maximum(Hf, spikes * (0.7 + 0.3 * hp.dome(dist(spikes), 5)))
    Hf = np.maximum(Hf, gem * (0.9 + 0.5 * hp.dome(dist(gem), 22)))
    # engraved quatrefoils on the band, a chapel motif, every 300 px
    quat = np.zeros((H, W), np.float32)
    for x in range(300, W - 250, 300):
        if abs(x - W / 2) < 300:
            continue
        for y in (34, 166):
            for dx, dy in ((7, 0), (-7, 0), (0, 7), (0, -7)):
                quat = np.maximum(quat, np.clip(1 - np.hypot(XX - x - dx, YY - y - dy) / 7, 0, 1))
    Hf -= quat * band * 0.12
    is_brass = np.clip(bead_in + collar + ring + spikes, 0, 1)[..., None]
    albedo = iron[0] * (1 - is_brass) + brass[0] * is_brass
    rough = iron[2] * (1 - is_brass[..., 0]) + brass[2] * is_brass[..., 0]
    metal = 0.85 * (1 - is_brass[..., 0]) + is_brass[..., 0]
    detail = iron[1] * (1 - is_brass) + brass[1] * is_brass
    albedo = albedo * (1 - gem[..., None]) + np.array([0.30, 0.30, 0.32]) * gem[..., None]   # clear glass: tinted in game
    rough = rough * (1 - gem) + 0.07 * gem
    metal = metal * (1 - gem)
    N = hp.normals_from(Hf, 34.0, detail, 0.35)
    rgb = hp.shade(albedo, N, rough, metal, hp.ao_from(Hf, 6, 2.2))
    alpha = np.clip(band + tracery + spikes, 0, 1)
    alpha = np.maximum(alpha, bead_in)
    return to_img(rgb, alpha)


def stained_tile(color, W=600, H=112, seed=4):
    """Leaded stained glass: Voronoi cells shaded with a little hue/brightness variety, dark lead lines."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform((0, 0), (W, H), (110, 2))
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    best = np.full((H, W), 1e9, np.float32)
    second = np.full((H, W), 1e9, np.float32)
    idx = np.zeros((H, W), np.int32)
    for i, (px, py) in enumerate(pts):
        for ox in (-W, 0, W):
            d = np.hypot(XX - px - ox, YY - py)
            nb = d < best
            second = np.where(nb, best, np.minimum(second, d))
            idx = np.where(nb, i, idx)
            best = np.where(nb, d, best)
    lead = np.clip(1 - (second - best) / 2.6, 0, 1)
    shade = rng.uniform(0.75, 1.2, len(pts))[idx] * (1 - 0.25 * np.clip(best / 30, 0, 1))
    hue = rng.uniform(-0.12, 0.12, (len(pts), 3))[idx]
    base = np.array(color, np.float32) / 255
    v = 0.55 + 0.4 * np.sin(np.pi * np.clip(YY / H * 1.05, 0, 1)) + np.exp(-((YY / H - 0.22) / 0.08) ** 2) * 0.25
    rgb = np.clip(base[None, None, :] * (1 + hue) * shade[..., None] * v[..., None] * 1.6, 0, 1)
    rgb = rgb * (1 - lead[..., None] * 0.9)
    return to_img(rgb, np.ones((H, W)))


def orb_B(accent, health, state):
    S = 512
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = S / 2
    r = np.hypot(XX - c, YY - c)
    ang = np.arctan2(YY - c, XX - c)
    acc = np.array(accent, np.float32) / 255
    glassm = (r < 186).astype(np.float32)
    petal = 0.6 + 0.4 * np.cos(ang * 8) ** 2
    lit = 0.3 if state == "Downed" else (0.55 if health < 0.25 else 1.0)
    rgb = acc[None, None, :] * (0.35 + 0.65 * petal[..., None]) * (1.15 - r[..., None] / 260) * lit
    # tracery: an inner ring, 8 spokes, 8 cusps
    trac = np.zeros((S, S), np.float32)
    trac = np.maximum(trac, np.clip(1 - np.abs(r - 70) / 7, 0, 1))
    trac = np.maximum(trac, np.clip(1 - np.abs(r - 150) / 6, 0, 1))
    for k in range(8):
        a = k * math.pi / 4
        dx, dy = math.cos(a), math.sin(a)
        proj = (XX - c) * dx + (YY - c) * dy
        perp = np.abs(-(XX - c) * dy + (YY - c) * dx)
        trac = np.maximum(trac, np.clip(1 - perp / 6, 0, 1) * (proj > 70) * (proj < 186))
        cx, cy = c + dx * 150 * math.cos(math.pi / 8) * 0 + math.cos(a + math.pi / 8) * 112, c + math.sin(a + math.pi / 8) * 112
        trac = np.maximum(trac, np.clip(1 - np.abs(np.hypot(XX - cx, YY - cy) - 30) / 5, 0, 1))
    trac *= glassm
    iron, _ = mats(S, S)
    Hf = trac * (0.6 + 0.4 * hp.dome(dist(trac), 4))
    N = hp.normals_from(Hf, 24.0, iron[1], 0.3)
    trgb = hp.shade(iron[0], N, iron[2], np.full((S, S), 0.85), hp.ao_from(Hf, 4, 2.0))
    out = to_img(rgb * glassm[..., None], glassm)
    out.alpha_composite(to_img(trgb, trac))
    out.alpha_composite(Image.open(HEALTH / "orb_ring.png").convert("RGBA"))
    return out


# ================================================================ C: Ivory (carved bone band, wax-seal orb)
def frame_C():
    W, H = W4, H4
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = mats(W, H)
    pm = hp.polymask
    body, window = outer_masks()
    band = np.clip(body - window, 0, 1)
    ring, gem = gem_sockets()
    bead_in = np.clip(pm((W, H), [[(WX0 - 7, WY0 - 7), (WX1 + 7, WY0 - 7), (WX1 + 7, WY1 + 7), (WX0 - 7, WY1 + 7)]]) - window, 0, 1)
    shrunk = pm((W, H), [[(18, 100), (76, 28), (W - 76, 28), (W - 18, 100), (W - 76, 172), (76, 172)]])
    bead_out = np.clip(body - shrunk, 0, 1)
    collar = pm((W, H), [[(W / 2 - 210, 14), (W / 2 + 210, 14), (W / 2 + 170, 58), (W / 2 - 170, 58)],
                         [(W / 2 - 170, 142), (W / 2 + 170, 142), (W / 2 + 210, 186), (W / 2 - 210, 186)]])
    spikes = pm((W, H), [[(0, 100), (30, 80), (48, 100), (30, 120)], [(W, 100), (W - 30, 80), (W - 48, 100), (W - 30, 120)]])
    # engraved scrollwork: a running vine of S-curves along each band, filled with ink
    eng = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(eng)
    for y0 in (36, 164):
        pts = []
        for x in range(WX0 + 10, WX1 - 10, 4):
            if abs(x - W / 2) < 220:
                if pts:
                    d.line(pts, fill=255, width=6)
                    pts = []
                continue
            pts.append((x * 2, (y0 + 6 * math.sin(x / 38.0)) * 2))
        if pts:
            d.line(pts, fill=255, width=6)
        for x in range(WX0 + 40, WX1 - 40, 76):
            if abs(x - W / 2) < 240:
                continue
            yy = y0 + 6 * math.sin(x / 38.0)
            s = 1 if math.cos(x / 38.0) > 0 else -1
            d.arc(((x - 14) * 2, (yy - 14 * s - 7) * 2, (x + 14) * 2, (yy - 14 * s + 7 + 14) * 2), 0, 360, fill=255, width=5)
    eng = np.array(eng.resize((W, H), Image.LANCZOS), np.float32) / 255 * band * (1 - bead_out)
    Hf = band * (0.35 + 0.45 * hp.dome(dist(band), 13)) - eng * 0.14
    Hf = np.maximum(Hf, bead_in * (0.62 + 0.25 * hp.dome(dist(bead_in), 4)))
    Hf = np.maximum(Hf, bead_out * (0.55 + 0.25 * hp.dome(dist(bead_out), 4)))
    Hf = np.maximum(Hf, collar * (0.75 + 0.2 * hp.dome(dist(collar), 8)))
    Hf = np.maximum(Hf, ring * (0.85 + 0.3 * hp.dome(dist(ring), 6)))
    Hf = np.maximum(Hf, spikes * (0.7 + 0.3 * hp.dome(dist(spikes), 5)))
    Hf = np.maximum(Hf, gem * (0.9 + 0.5 * hp.dome(dist(gem), 22)))
    rng = np.random.default_rng(9)
    grain = ndimage.gaussian_filter(rng.standard_normal((H, W)), (1.2, 18))
    ivory = np.dstack([np.full((H, W), c, np.float32) for c in (0.72, 0.66, 0.54)]) * (1 + grain[..., None] * 0.08)
    ivory = ivory * (1 - eng[..., None] * 0.92)                    # ink in the engraving
    is_brass = np.clip(bead_in + bead_out + collar + ring + spikes, 0, 1)[..., None]
    albedo = hp.srgb_to_lin(ivory) * (1 - is_brass) + brass[0] * is_brass
    rough = 0.42 * (1 - is_brass[..., 0]) + brass[2] * is_brass[..., 0] + eng * 0.3
    metal = is_brass[..., 0]
    detail = brass[1] * is_brass
    albedo = albedo * (1 - gem[..., None]) + np.array([0.30, 0.30, 0.32]) * gem[..., None]
    rough = rough * (1 - gem) + 0.07 * gem
    metal = metal * (1 - gem)
    N = hp.normals_from(Hf, 34.0, detail, 0.35)
    rgb = hp.shade(albedo, N, rough, metal, hp.ao_from(Hf, 6, 2.2))
    alpha = np.maximum(np.clip(body - window + spikes, 0, 1), bead_in)
    return to_img(rgb, alpha)


def orb_C(accent, health, state):
    """A pressed wax seal: an irregular disc with a raised rim and a sunken field (the % is stamped into it)."""
    S = 512
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = S / 2
    ang = np.arctan2(YY - c, XX - c)
    r = np.hypot(XX - c, YY - c)
    edge = 212 + 10 * np.sin(ang * 5 + 1) + 7 * np.sin(ang * 9 + 2) + 5 * np.sin(ang * 14)
    m = np.clip((edge - r) / 2.5, 0, 1)
    rim = np.exp(-((r - edge * 0.78) / 16) ** 2)
    Hf = m * (0.45 + 0.35 * hp.dome(dist(m), 30)) + rim * 0.18 - (r < edge * 0.66) * 0.12 * m
    N = hp.normals_from(ndimage.gaussian_filter(Hf, 1.2), 30.0)
    acc = np.array(accent, np.float32) / 255
    wax = hp.srgb_to_lin(acc * (0.5 if state == "Downed" else 0.8))
    albedo = np.broadcast_to(wax, (S, S, 3)).copy()
    rgb = hp.shade(albedo, N, np.full((S, S), 0.32), np.zeros((S, S)), hp.ao_from(Hf, 6, 2.0))
    return to_img(rgb, m)


def fill_C(color):
    """Wine with ink marbling (greyscale, tinted)."""
    W, H = 768, 144
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    t = YY / (H - 1)
    swirl = hp.periodic_noise(H, W, (4, 30), 13)
    marb = np.abs(np.sin(XX / 45 + swirl * 2.2))
    v = 0.55 + 0.28 * np.sin(np.pi * np.clip(t * 1.1, 0, 1)) - marb ** 6 * 0.25
    v += np.exp(-((t - 0.2) / 0.07) ** 2) * 0.3
    v -= np.exp(-((t - 0.97) / 0.05) ** 2) * 0.3
    v = np.clip(v, 0, 1.2) / 1.2
    return tint(to_img(np.dstack([v, v, v]), np.ones((H, W))), color, 1.05)


# ================================================================ assembly
def tiled(tile, w, h):
    out = Image.new("RGBA", (max(1, w), max(1, h)))
    for x in range(0, w, tile.size[0]):
        out.alpha_composite(tile, (x, 0))
    return out


def bar(concept, variant, frames):
    name, fill_col, accent, health = variant
    state = name if name in ("Low health", "Downed") else "Form"
    k = 50 / 64
    W, H = 600 * SC, 50 * SC
    canvas = Image.new("RGBA", (W + 40 * SC, H + 40 * SC))
    ox, oy = 20 * SC, 12 * SC
    tx, ty, tw, th = 46 * k, 14 * k, 600 - 92 * k, 36 * k
    track = Image.new("RGBA", (int(tw * SC), int(th * SC)), (10, 6, 9, 255))
    fw = int(track.size[0] * health)
    if concept == "B":
        tile = stained_tile(fill_col).resize((int(300 * SC), int(th * SC)), Image.LANCZOS)
    elif concept == "C":
        tile = fill_C(fill_col).resize((int(192 * k * SC), int(th * SC)), Image.LANCZOS)
    else:
        tile = fill_A(fill_col).resize((int(192 * k * SC), int(th * SC)), Image.LANCZOS)
    if fw > 0:
        track.alpha_composite(tiled(tile, fw, track.size[1]).crop((0, 0, fw, track.size[1])))
        if concept == "A" and 2 < fw < track.size[0] - 2:     # wax-drip leading edge
            d = ImageDraw.Draw(track)
            d.rectangle([fw - 3 * SC, 0, fw, track.size[1]], fill=tuple(int(min(255, c * 1.6)) for c in fill_col) + (255,))
            for yy, ln in ((0.2, 5), (0.55, 8), (0.8, 4)):
                d.ellipse([fw - 2 * SC, int(track.size[1] * yy), fw + int(ln * SC * 0.5), int(track.size[1] * yy) + 3 * SC], fill=tuple(int(min(255, c * 1.4)) for c in fill_col) + (255,))
    if state == "Downed":
        track = Image.blend(track, Image.new("RGBA", track.size, (24, 20, 22, 255)), 0.35)
    canvas.alpha_composite(track, (int(ox + tx * SC), int(oy + ty * SC)))
    fr = frames[concept].resize((W, H), Image.LANCZOS)
    canvas.alpha_composite(fr, (ox, oy))
    gems = gem_overlay(accent, 0.95 if state != "Downed" else 0.4).resize((W, H), Image.LANCZOS)
    canvas.alpha_composite(gems, (ox, oy))
    o = int(50 * 1.45 * SC)
    orb = {"A": orb_A, "B": orb_B, "C": orb_C}[concept](accent, health, state).resize((o, o), Image.LANCZOS)
    cx, cy = ox + W // 2, oy + H // 2
    sh = glow((int(o * 1.4), int(o * 1.4)), (0, 0, 0), 0.7)
    canvas.alpha_composite(sh, (cx - sh.size[0] // 2, cy - sh.size[1] // 2))
    canvas.alpha_composite(orb, (cx - o // 2, cy - o // 2))
    if state == "Low health":
        vig = glow((W + 30 * SC, H + 26 * SC), (255, 60, 50), 0.28, 1.0)
        canvas.alpha_composite(vig, (ox - 15 * SC, oy - 13 * SC))
    d = ImageDraw.Draw(canvas)
    pct = f"{round(health * 100)}%"
    if concept == "C":   # stamped into the seal: dark, embossed
        d.text((cx, cy + 1), pct, font=font(int(17 * SC)), fill=(255, 230, 210, 90), anchor="mm")
        d.text((cx, cy), pct, font=font(int(17 * SC)), fill=(40, 10, 12), anchor="mm")
    else:
        d.text((cx, cy), pct, font=font(int(17 * SC)), fill=(228, 222, 208), anchor="mm", stroke_width=2, stroke_fill=(20, 10, 12))
    return canvas


def with_rail(barimg):
    """The bar with the 1.74.0 posture rail hung under it (posture 35%), for context."""
    W, H = barimg.size
    c = Image.new("RGBA", (W, H + 26 * SC))
    rail_y = 12 + 45   # bar top (12) + BAR_H - 5, design px
    tmp = Image.new("RGBA", (W, H + 26 * SC))
    pp.SC = SC
    pp.GOLD, pp.EMBER = (226, 168, 72), (255, 122, 46)   # the rail's in-game brass / ember (KitHud BRASS, EMBER)
    pp.posture_rail(tmp, 20, rail_y, 0.35, "calm", centre_out=True, frame_img=POSTURE / "PostureFrame.png")
    c.alpha_composite(tmp)
    c.alpha_composite(barimg)
    return c


def backdrop(w, h):
    for name in ("library-kit-night.jpg", "garden-courtyard-night.jpg"):
        if (DOCS / name).exists():
            src = Image.open(DOCS / name).convert("RGB")
            s = max(w / src.size[0], h / src.size[1])
            src = src.resize((int(src.size[0] * s) + 1, int(src.size[1] * s) + 1), Image.LANCZOS)
            src = src.crop((0, src.size[1] - h, w, src.size[1])).filter(ImageFilter.GaussianBlur(4))
            return Image.blend(src, Image.new("RGB", src.size, (8, 6, 10)), 0.5).convert("RGBA")
    return Image.new("RGBA", (w, h), (16, 12, 18, 255))


TITLES = {
    "A": ("A  Votive", "The current iron and brass frame, refined. The orb becomes a brass lantern whose candle burns tall at full health and gutters as you weaken. Blood-glass fill with a wax-drip edge."),
    "B": ("B  Chapel", "A new frame of gothic lancet windows: health is stained glass in leaded panes behind iron arches. The orb is a rose window."),
    "C": ("C  Ivory", "A carved ivory band with brass edging and ink-filled scrollwork. The orb is a pressed wax seal with the % stamped in."),
}


def concept_sheet(concept, frames):
    cells = [with_rail(bar(concept, v, frames)) for v in VARIANTS]
    cw, ch = cells[0].size
    cols = 2
    rows = math.ceil(len(cells) / cols)
    pad = 16
    sheet = Image.new("RGBA", (cols * (cw + pad) + pad, 110 + rows * (ch + 40)), (14, 11, 16, 255))
    bg = backdrop(sheet.size[0], sheet.size[1] - 100)
    sheet.alpha_composite(bg, (0, 100))
    d = ImageDraw.Draw(sheet)
    t, sub = TITLES[concept]
    d.text((pad, 12), t, font=font(34), fill=(235, 205, 120))
    d.text((pad, 58), sub, font=font(20, False), fill=(214, 206, 196))
    for i, (cell, v) in enumerate(zip(cells, VARIANTS)):
        x = pad + (i % cols) * (cw + pad)
        y = 110 + (i // cols) * (ch + 40)
        d.text((x + 20, y + 4), v[0], font=font(22), fill=(235, 205, 120))
        sheet.alpha_composite(cell, (x, y + 30))
    sheet.save(OUT / f"concept_{concept}.png")
    return sheet


if __name__ == "__main__":
    frames = {"A": frame_A(), "B": frame_B(), "C": frame_C()}
    for k, f in frames.items():
        f.save(OUT / f"frame_{k}.png")
    sheets = [concept_sheet(c, frames) for c in "ABC"]
    W = max(s.size[0] for s in sheets)
    allsheet = Image.new("RGB", (W, sum(s.size[1] for s in sheets)), (14, 11, 16))
    y = 0
    for s in sheets:
        allsheet.paste(s.convert("RGB"), (0, y))
        y += s.size[1]
    allsheet.save(OUT / "health-v3-options.jpg", quality=90)
    print(OUT / "health-v3-options.jpg", allsheet.size)
