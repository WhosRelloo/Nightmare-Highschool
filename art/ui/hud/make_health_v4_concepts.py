"""Health bar v4: three all-new designs (not variations of the 1.13.0 frame), baked with make_health_pbr's shader.

Owner: "completely revamp the current health bar with a completely new and cooler and on theme design".
Each keeps the bar's 600 design-px width and its centre, so the 1.74.0 posture rail can still hang under it, but the
silhouette, the material and the centrepiece are new. Each is shown full (82%), low (18%), downed (5%) and in the four
transformation forms (Vampire, Wolf, Ghoul, Wraith), with the posture rail under it.

  A  Vigil      a wrought-iron candelabrum: ten wax candles stand on the bar, one per 10% of health, and snuff out
                from the right as you're hurt; iron scroll ends; a quatrefoil medallion of crimson glass holds the %
  B  Reliquary  a sealed blood reliquary: a long glass vial in a brass cage with clawed finials, the blood sloshing
                inside it; a gothic lancet spire rises from the middle holding a ruby with the %
  C  Thornrose  a briar of black iron: two thorned vines twist along the bar (brass-tipped thorns), rosebud ends,
                crimson velvet for the fill and an iron rose at the centre with the % in its glass heart

Output: art/ui/hud/out/health_v4/concept_<A|B|C>.png and health-v4-options.jpg.
  python make_health_v4_concepts.py
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hp = _load("hp", "make_health_pbr.py")
pp = _load("pp", "make_posture_pbr.py")
v3 = _load("v3", "make_health_v3_concepts.py")
font, tint, glow, to_img, tiled, flame, backdrop = v3.font, v3.tint, v3.glow, v3.to_img, v3.tiled, v3.flame, v3.backdrop

OUT = HERE / "out" / "health_v4"
OUT.mkdir(parents=True, exist_ok=True)
HEALTH = HERE / "out" / "health_v2"
POSTURE = HERE / "out" / "posture"
SC = 2           # mockups at 2x design px
W4 = 2400        # art is built at 4x design px (600 wide)

STATES = [  # label, health, fill colour, accent (glass / flame / gems), state
    ("Full health", 0.82, (150, 22, 34), (210, 44, 60), "full"),
    ("Low health", 0.18, (150, 22, 34), (255, 96, 70), "low"),
    ("Downed", 0.05, (70, 60, 62), (255, 120, 60), "downed"),
    ("Vampire form", 0.82, (118, 8, 24), (220, 34, 52), "full"),
    ("Wolf form", 0.82, (150, 72, 20), (236, 158, 40), "full"),
    ("Ghoul form", 0.82, (92, 104, 74), (176, 206, 156), "full"),
    ("Wraith form", 0.82, (70, 112, 152), (158, 220, 255), "full"),
]


# ================================================================ building blocks
def mask(W, H, draw_fn, ss=3):
    """Antialiased mask: draw_fn(draw, s) draws in 4x coords multiplied by s."""
    im = Image.new("L", (W * ss, H * ss), 0)
    draw_fn(ImageDraw.Draw(im), ss)
    return np.array(im.resize((W, H), Image.LANCZOS), np.float32) / 255.0


def dist(m):
    return ndimage.distance_transform_edt(m > 0.5)


def bake(W, H, layers, seed=3, dents=0.04):
    """layers: [(mask, base_height, dome_amp, dome_radius, material)], painter order. Returns RGBA image."""
    iron = hp.material("Iron", (W, H), 384, tint=(0.26, 0.25, 0.28), rough_mul=0.72)
    brass = hp.material("Brass", (W, H), 320, tint=(1.0, 0.86, 0.62), rough_mul=0.7, rough_add=-0.05)
    blackiron = hp.material("Iron", (W, H), 300, tint=(0.11, 0.105, 0.12), rough_mul=0.8)
    rng = np.random.default_rng(seed)
    grain = ndimage.gaussian_filter(rng.standard_normal((H, W)), (1.5, 10))
    wax_alb = hp.srgb_to_lin(np.dstack([np.full((H, W), c, np.float32) for c in (0.86, 0.80, 0.68)]) * (1 + grain[..., None] * 0.04))
    MAT = {
        "iron": (iron[0], iron[2], np.full((H, W), 0.85, np.float32), iron[1]),
        "blackiron": (blackiron[0], blackiron[2], np.full((H, W), 0.8, np.float32), blackiron[1]),
        "brass": (brass[0], brass[2], np.ones((H, W), np.float32), brass[1]),
        "wax": (wax_alb, np.full((H, W), 0.5, np.float32), np.zeros((H, W), np.float32), np.zeros((H, W, 3), np.float32)),
        "dark": (np.full((H, W, 3), 0.02, np.float32), np.full((H, W), 0.3, np.float32), np.zeros((H, W), np.float32), np.zeros((H, W, 3), np.float32)),
    }
    Hf = np.zeros((H, W), np.float32)
    alb = np.zeros((H, W, 3), np.float32)
    rough = np.ones((H, W), np.float32)
    met = np.zeros((H, W), np.float32)
    det = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    for m, h0, amp, r, key in layers:
        if m.max() <= 0:
            continue
        hl = m * (h0 + amp * hp.dome(dist(m), r))
        Hf = np.where(m > 0.02, np.maximum(Hf, hl), Hf)
        a, ro, mt, dn = MAT[key]
        w = m[..., None]
        alb = alb * (1 - w) + a * w
        rough = rough * (1 - m) + ro * m
        met = met * (1 - m) + mt * m
        det = det * (1 - w) + dn * w
        alpha = np.maximum(alpha, m)
    d = ndimage.gaussian_filter(rng.standard_normal((H, W)), 2.6)
    Hf -= np.clip(d, 0, None) * dents * alpha
    N = hp.normals_from(Hf, 30.0, det, 0.35)
    rgb = hp.shade(alb, N, rough, met, hp.ao_from(Hf, 6, 2.2))
    return to_img(rgb, alpha)


def glass_disc(S, accent, lit=1.0):
    """A domed crimson (accent) glass cabochon, S px, glossy, lit from inside."""
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    r = np.hypot(XX - c, YY - c) / (S / 2)
    m = np.clip((1 - r) * S / 3, 0, 1)
    z = np.sqrt(np.clip(1 - r ** 2, 0, 1))
    acc = np.array(accent, np.float32) / 255
    lum = (0.18 + 0.45 * z ** 1.5) * lit + np.exp(-(((XX - c) / (S * 0.28)) ** 2 + ((YY - c - S * 0.2) / (S * 0.2)) ** 2)) * 0.55 * lit
    sw = hp.periodic_noise(S, S, S / 18, 5) * 0.06
    rgb = acc[None, None, :] * (lum + sw)[..., None]
    hl = np.exp(-(((XX - c + S * 0.18) / (S * 0.11)) ** 2 + ((YY - c + S * 0.2) / (S * 0.07)) ** 2))
    rgb = rgb + hl[..., None] * 0.85
    rim = np.clip(1 - np.abs(r - 0.93) / 0.07, 0, 1) * 0.25
    rgb = rgb * (1 - rim[..., None])
    return to_img(np.clip(rgb, 0, 1), m)


def pct_text(img, cx, cy, value, size, dark=False):
    d = ImageDraw.Draw(img)
    t = f"{round(value * 100)}%"
    if dark:
        d.text((cx, cy), t, font=font(size), fill=(36, 8, 10), anchor="mm")
    else:
        d.text((cx, cy), t, font=font(size), fill=(240, 232, 218), anchor="mm", stroke_width=max(2, size // 9), stroke_fill=(24, 8, 10))


def blood_tile(color, W, H):
    return tint(Image.open(HEALTH / "fill.png"), color, 1.05).resize((max(1, int(W)), max(1, int(H))), Image.LANCZOS)


def velvet_tile(color, W=512, H=96):
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    t = YY / (H - 1)
    pile = hp.periodic_noise(H, W, (1.2, 3), 41) * 0.05
    fold = np.sin(XX / W * 2 * np.pi * 3 + hp.periodic_noise(H, W, (20, 60), 42) * 0.8) * 0.09
    v = 0.5 + 0.3 * np.sin(np.pi * t) + fold + pile + np.exp(-((t - 0.3) / 0.12) ** 2) * 0.18
    v = np.clip(v, 0, 1)
    return tint(to_img(np.dstack([v, v, v]), np.ones((H, W))), color, 1.15)


# ================================================================ A: Vigil (candelabrum)
A_H, A_CY = 300, 214                 # canvas height, bar centre (4x)
A_WIN = (150, 2250, A_CY - 40, A_CY + 40)
A_CANDLES = [x for x in np.linspace(250, 1010, 5)] + [W4 - x for x in np.linspace(1010, 250, 5)]   # left to right
A_CANDLE_H = [86, 70, 94, 78, 64, 64, 78, 94, 70, 86]
A_FLAME = {  # candle flame by form accent (the plain states burn candle-gold)
    (220, 34, 52): (236, 40, 60), (236, 158, 40): (255, 168, 50), (176, 206, 156): (150, 230, 140), (158, 220, 255): (150, 210, 255),
}


def frame_A():
    W, H, cy = W4, A_H, A_CY
    x0, x1, y0, y1 = A_WIN

    def rail(d, s):
        d.rounded_rectangle((120 * s, (cy - 70) * s, (W - 120) * s, (cy + 70) * s), radius=30 * s, fill=255)

    def window(d, s):
        d.rectangle((x0 * s, y0 * s, x1 * s, y1 * s), fill=255)

    def bead(d, s):
        d.rectangle(((x0 - 9) * s, (y0 - 9) * s, (x1 + 9) * s, (y1 + 9) * s), fill=255)
        d.rectangle((x0 * s, y0 * s, x1 * s, y1 * s), fill=0)

    def scrolls(d, s):  # iron scroll curls at both ends, and a drip-pan lip under the rail
        for side in (-1, 1):
            cx = 96 if side < 0 else W - 96
            pts = []
            for k in range(200):
                a = k / 199 * 2.6 * math.pi
                r = 74 - 56 * k / 199
                pts.append(((cx + side * (r * math.cos(a + math.pi / 2 * (1 - side)))) * s, (cy + r * math.sin(a) * 1.05) * s))
            d.line(pts, fill=255, width=int(13 * s), joint="curve")
            d.ellipse(((cx - 14) * s, (cy - 14) * s, (cx + 14) * s, (cy + 14) * s), fill=255)

    def cups(d, s):  # brass drip cups the candles stand in, on the rail's top edge
        for x in A_CANDLES:
            d.polygon([((x - 30) * s, (cy - 74) * s), ((x + 30) * s, (cy - 74) * s), ((x + 20) * s, (cy - 58) * s), ((x - 20) * s, (cy - 58) * s)], fill=255)
            d.ellipse(((x - 34) * s, (cy - 84) * s, (x + 34) * s, (cy - 70) * s), fill=255)

    def rivets(d, s):
        for x in range(300, W - 280, 190):
            if abs(x - W / 2) < 230:
                continue
            d.ellipse(((x - 7) * s, (cy + 52) * s, (x + 7) * s, (cy + 66) * s), fill=255)

    def medal(d, s):  # quatrefoil medallion: four lobes and a round centre
        cx = W / 2
        for dx, dy in ((0, -72), (0, 72), (-72, 0), (72, 0)):
            d.ellipse(((cx + dx - 78) * s, (cy + dy - 78) * s, (cx + dx + 78) * s, (cy + dy + 78) * s), fill=255)

    def medal_edge(d, s):  # a brass bead around each lobe
        cx = W / 2
        for dx, dy in ((0, -72), (0, 72), (-72, 0), (72, 0)):
            d.ellipse(((cx + dx - 78) * s, (cy + dy - 78) * s, (cx + dx + 78) * s, (cy + dy + 78) * s), outline=255, width=int(9 * s))

    def medal_rim(d, s):
        cx = W / 2
        d.ellipse(((cx - 112) * s, (cy - 112) * s, (cx + 112) * s, (cy + 112) * s), fill=255)
        d.ellipse(((cx - 96) * s, (cy - 96) * s, (cx + 96) * s, (cy + 96) * s), fill=0)

    win = mask(W, H, window)
    layers = [
        (np.clip(mask(W, H, rail) - win, 0, 1), 0.3, 0.45, 16, "blackiron"),
        (mask(W, H, scrolls), 0.45, 0.4, 9, "blackiron"),
        (mask(W, H, bead), 0.6, 0.25, 4, "brass"),
        (mask(W, H, rivets), 0.65, 0.3, 6, "brass"),
        (mask(W, H, cups), 0.55, 0.35, 8, "brass"),
        (mask(W, H, medal), 0.75, 0.35, 22, "blackiron"),
        (mask(W, H, medal_edge) * (1 - mask(W, H, lambda d, s: d.ellipse(((W / 2 - 100) * s, (cy - 100) * s, (W / 2 + 100) * s, (cy + 100) * s), fill=255))), 0.9, 0.2, 4, "brass"),
        (mask(W, H, medal_rim), 0.95, 0.3, 6, "brass"),
    ]
    return bake(W, H, layers, seed=11)


_CANDLE_BODY = {}


def candle(height, lit, accent, state, idx):
    """One wax candle (4x px), with drips; lit/unlit flame; a smoke wisp on a just-snuffed one."""
    w, h = 40, int(height)
    W, H = 120, h + 140
    cx = W / 2

    def body(d, s):
        d.rounded_rectangle(((cx - w / 2) * s, (H - h) * s, (cx + w / 2) * s, (H + 10) * s), radius=8 * s, fill=255)
        rng = np.random.default_rng(idx + 3)
        for _ in range(3):  # wax drips
            x = cx + rng.uniform(-w / 2 + 4, w / 2 - 4)
            ln = rng.uniform(14, h * 0.6)
            d.rounded_rectangle(((x - 4) * s, (H - h - 2) * s, (x + 4) * s, (H - h + ln) * s), radius=4 * s, fill=255)
        d.ellipse(((cx - w / 2 - 2) * s, (H - h - 8) * s, (cx + w / 2 + 2) * s, (H - h + 8) * s), fill=255)

    if idx not in _CANDLE_BODY:
        _CANDLE_BODY[idx] = bake(W, H, [(mask(W, H, body), 0.4, 0.5, 12, "wax")], seed=idx, dents=0.01)
    img = _CANDLE_BODY[idx]
    out = Image.new("RGBA", (W, H))
    out.alpha_composite(img)
    d = ImageDraw.Draw(out)
    d.line([(cx, H - h - 4), (cx + 1, H - h - 16)], fill=(30, 22, 18, 255), width=4)   # wick
    if lit:
        fl = flame(160, accent, height=1.0 if state == "full" else 0.5)
        out.alpha_composite(fl, (int(cx - 80), int(H - h - 122)))
    return out


def smoke(W=120, H=160, seed=1):
    rng = np.random.default_rng(seed)
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    t = 1 - YY / H
    path = W / 2 + np.sin(YY / 18 + seed) * 10 * t
    a = np.clip(1 - np.abs(XX - path) / (4 + 14 * t), 0, 1) * np.clip(1 - t, 0, 1) ** 0.5 * 0.35
    return to_img(np.full((H, W, 3), 0.75, np.float32), a)


def render_A(frame, health, fill, accent, state):
    W, H, cy = W4, A_H, A_CY
    x0, x1, y0, y1 = A_WIN
    out = Image.new("RGBA", (W, H))
    track = Image.new("RGBA", (x1 - x0, y1 - y0), (10, 6, 9, 255))
    fw = int((x1 - x0) * health)
    if fw > 0:
        tile = blood_tile(fill, 300, y1 - y0)
        track.alpha_composite(tiled(tile, fw, y1 - y0).crop((0, 0, fw, y1 - y0)))
    out.alpha_composite(track, (x0, y0))
    out.alpha_composite(frame)
    lit_n = math.ceil(health * 10 - 1e-6) if state != "downed" else 0
    flame_col = A_FLAME.get(tuple(accent), (255, 176, 80))
    for i, x in enumerate(A_CANDLES):
        c = candle(A_CANDLE_H[i], i < lit_n, flame_col, state, i)
        out.alpha_composite(c, (int(x - 60), int(cy - 76 - c.size[1] + 10)))
        if i == lit_n and state != "full":
            sm = smoke(seed=i)
            out.alpha_composite(sm, (int(x - 60), int(cy - 76 - A_CANDLE_H[i] - 150)))
    g = glass_disc(192, accent, 0.35 if state == "downed" else 1.0)
    out.alpha_composite(g, (W // 2 - 96, cy - 96))
    pct_text(out, W // 2, cy, health, 70)
    return out


# ================================================================ B: Reliquary (vial in a brass cage)
B_H, B_CY = 360, 236
B_TUBE = (120, 2280, B_CY - 60, B_CY + 60)


def spire_pts(cx, cy, inset):
    """A gothic lancet: two arcs meeting in a point, on straight sides down to a tapered foot."""
    half = 132 - inset
    R = 2 * half
    spring = cy - 30
    pts = []
    for k in range(41):   # left side: an arc centred on the right springing point
        a = math.radians(180 - 60 * k / 40)
        pts.append((cx + half + R * math.cos(a), spring - R * math.sin(a) * 0.62))
    for k in range(41):   # right side: an arc centred on the left springing point
        a = math.radians(60 - 60 * k / 40)
        pts.append((cx - half + R * math.cos(a), spring - R * math.sin(a) * 0.62))
    pts += [(cx + half, cy + 96 - inset), (cx + 58, cy + 128 - inset), (cx - 58, cy + 128 - inset), (cx - half, cy + 96 - inset)]
    return pts


def frame_B():
    W, H, cy = W4, B_H, B_CY
    tx0, tx1, ty0, ty1 = B_TUBE

    def bands(d, s):
        for x in (340, 620, 900):
            for xx in (x, W - x):
                d.rounded_rectangle(((xx - 16) * s, (cy - 74) * s, (xx + 16) * s, (cy + 74) * s), radius=10 * s, fill=255)

    def rods(d, s):
        d.rounded_rectangle((200 * s, (cy - 76) * s, (W - 200) * s, (cy - 64) * s), radius=6 * s, fill=255)
        d.rounded_rectangle((200 * s, (cy + 64) * s, (W - 200) * s, (cy + 76) * s), radius=6 * s, fill=255)

    def finials(d, s):  # end caps with three claws gripping the vial, and a spike
        for side in (-1, 1):
            ex = 0 if side < 0 else W

            def X(v):
                return (ex - v if side > 0 else ex + v) * s
            d.polygon([(X(4), cy * s), (X(70), (cy - 30) * s), (X(70), (cy + 30) * s)], fill=255)
            d.rounded_rectangle((min(X(60), X(200)), (cy - 82) * s, max(X(60), X(200)), (cy + 82) * s), radius=26 * s, fill=255)
            for dy in (-62, 0, 62):
                d.polygon([(X(190), (cy + dy - 14) * s), (X(290), (cy + dy * 0.9 - 4) * s), (X(300), (cy + dy * 0.9 + 6) * s), (X(190), (cy + dy + 14) * s)], fill=255)

    def finial_ring(d, s):
        for side in (-1, 1):
            cx = 128 if side < 0 else W - 128
            d.ellipse(((cx - 34) * s, (cy - 34) * s, (cx + 34) * s, (cy + 34) * s), fill=255)

    def spire(d, s):  # gothic lancet spire: a pointed arch frame rising above the vial
        cx = W / 2
        d.polygon([(p[0] * s, p[1] * s) for p in spire_pts(cx, cy, 0)], fill=255)
        top = min(p[1] for p in spire_pts(cx, cy, 0))
        d.polygon([((cx - 14) * s, (top + 14) * s), (cx * s, (top - 34) * s), ((cx + 14) * s, (top + 14) * s)], fill=255)   # finial

    def spire_in(d, s):
        cx = W / 2
        d.ellipse(((cx - 98) * s, (cy - 98) * s, (cx + 98) * s, (cy + 98) * s), fill=255)

    def crockets(d, s):  # little brass leaves along the spire's two arcs
        pts = spire_pts(W / 2, cy, -8)
        for i in (10, 22, 34, 47, 59, 71):
            px, py = pts[i]
            d.ellipse(((px - 12) * s, (py - 12) * s, (px + 12) * s, (py + 12) * s), fill=255)

    def spire_edge(d, s):
        pts = spire_pts(W / 2, cy, 3)
        d.line([(p[0] * s, p[1] * s) for p in pts + pts[:1]], fill=255, width=int(10 * s))

    def ring(d, s):
        cx = W / 2
        d.ellipse(((cx - 110) * s, (cy - 110) * s, (cx + 110) * s, (cy + 110) * s), fill=255)
        d.ellipse(((cx - 96) * s, (cy - 96) * s, (cx + 96) * s, (cy + 96) * s), fill=0)

    sp = np.clip(mask(W, H, spire) - mask(W, H, spire_in), 0, 1)
    layers = [
        (mask(W, H, rods), 0.5, 0.3, 5, "brass"),
        (mask(W, H, bands), 0.6, 0.35, 10, "brass"),
        (mask(W, H, finials), 0.55, 0.4, 14, "brass"),
        (mask(W, H, finial_ring), 0.85, 0.3, 8, "iron"),
        (sp, 0.6, 0.4, 14, "iron"),
        (mask(W, H, spire_edge), 0.85, 0.2, 4, "brass"),
        (mask(W, H, crockets), 0.8, 0.3, 6, "brass"),
        (mask(W, H, ring), 0.95, 0.3, 6, "brass"),
    ]
    return bake(W, H, layers, seed=21)


def tube_mask(W, H):
    tx0, tx1, ty0, ty1 = B_TUBE
    return mask(W, H, lambda d, s: d.rounded_rectangle((tx0 * s, ty0 * s, tx1 * s, ty1 * s), radius=(ty1 - ty0) / 2 * s, fill=255))


def render_B(frame, health, fill, accent, state):
    W, H, cy = W4, B_H, B_CY
    tx0, tx1, ty0, ty1 = B_TUBE
    out = Image.new("RGBA", (W, H))
    tm = tube_mask(W, H)
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    # the vial: dark smoked glass inside, then the blood up to the health mark (with a bright meniscus edge)
    inside = to_img(np.full((H, W, 3), [0.04, 0.025, 0.03], np.float32), tm * 0.92)
    out.alpha_composite(inside)
    fx = tx0 + (tx1 - tx0) * health
    tile = blood_tile(fill, 300, ty1 - ty0)
    liquid = Image.new("RGBA", (W, H))
    if health > 0:
        liquid.alpha_composite(tiled(tile, int(fx - tx0), ty1 - ty0), (tx0, ty0))
        lm = np.clip((fx - XX) / 2, 0, 1) * tm
        la = np.array(liquid, np.float32)
        la[..., 3] *= lm
        edge = np.exp(-((XX - fx) / 4) ** 2) * tm * (health < 0.995)
        la[..., :3] += edge[..., None] * np.array(fill, np.float32) * 0.8
        out.alpha_composite(Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA"))
    # glass: a top highlight streak and a soft rim, over the liquid
    t = (YY - ty0) / (ty1 - ty0)
    hl = (np.exp(-((t - 0.2) / 0.06) ** 2) * 0.45 + np.exp(-((t - 0.85) / 0.05) ** 2) * 0.12) * tm
    rim = np.clip(tm - ndimage.gaussian_filter(tm, 5) * 0.9, 0, 1) * 0.6 + (tm - ndimage.binary_erosion(tm > 0.5, iterations=5)) * 0.25
    out.alpha_composite(to_img(np.ones((H, W, 3), np.float32) * 0.95, np.clip(hl + rim, 0, 1)))
    out.alpha_composite(frame)
    g = glass_disc(192, accent, 0.35 if state == "downed" else 1.0)
    out.alpha_composite(g, (W // 2 - 96, cy - 96))
    pct_text(out, W // 2, cy, health, 70)
    return out


# ================================================================ C: Thornrose (iron briar)
C_H, C_CY = 300, 160
C_WIN = (150, 2250, C_CY - 40, C_CY + 40)


def frame_C():
    W, H, cy = W4, C_H, C_CY
    x0, x1, y0, y1 = C_WIN

    def vines(d, s):
        for base, sgn in ((y0 - 26, -1), (y1 + 26, 1)):
            for ph in (0, math.pi):
                pts = []
                for x in range(110, W - 110, 6):
                    if abs(x - W / 2) < 150:
                        if pts:
                            d.line(pts, fill=255, width=int(13 * s), joint="curve")
                            pts = []
                        continue
                    pts.append((x * s, (base + 9 * math.sin(x / 70 + ph)) * s))
                if pts:
                    d.line(pts, fill=255, width=int(13 * s), joint="curve")

    def thorns(d, s):
        tips = []
        for base, sgn in ((y0 - 22, -1), (y1 + 22, 1)):
            for j, x in enumerate(range(230, W - 230, 120)):
                if abs(x - W / 2) < 210:
                    continue
                y = base + 10 * math.sin(x / 90)
                lean = 1 if j % 2 == 0 else -1     # hooked thorns, leaning alternately
                d.polygon([((x - 16) * s, y * s), ((x + 16) * s, y * s), ((x + lean * 26) * s, (y + sgn * 36) * s)], fill=255)
        return tips

    def tips_mask(d, s):
        for base, sgn in ((y0 - 22, -1), (y1 + 22, 1)):
            for j, x in enumerate(range(230, W - 230, 120)):
                if abs(x - W / 2) < 210:
                    continue
                y = base + 10 * math.sin(x / 90)
                lean = 1 if j % 2 == 0 else -1
                tx, ty = x + lean * 26, y + sgn * 36
                mx, my = tx * 0.6 + x * 0.4, ty * 0.6 + y * 0.4
                d.polygon([((mx - 7) * s, my * s), ((mx + 7) * s, my * s), (tx * s, ty * s)], fill=255)

    def bead(d, s):
        d.rectangle(((x0 - 10) * s, (y0 - 10) * s, (x1 + 10) * s, (y1 + 10) * s), fill=255)
        d.rectangle((x0 * s, y0 * s, x1 * s, y1 * s), fill=0)

    def buds(d, s):  # rosebud ends: a closed teardrop bud pointing outward, cupped by two sepals
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            pts = []
            for k in range(61):
                t = k / 60 * 2 * math.pi
                # teardrop: round at the bar end, pointed outward
                x = 70 * (1 - math.cos(t))
                y = 50 * math.sin(t) * (1 - x / 150)
                pts.append(((bx + side * x) * s, (cy + y) * s))
            d.polygon(pts, fill=255)
            for dy in (-1, 1):   # sepals
                d.polygon([(bx * s, (cy + dy * 26) * s), ((bx + side * 78) * s, (cy + dy * 50) * s), ((bx + side * 44) * s, (cy + dy * 14) * s)], fill=255)

    def bud_lines(d, s):  # the petals' folded edges spiralling into the bud
        for side in (-1, 1):
            bx = 150 if side < 0 else W - 150
            for ox, r in ((34, 30), (68, 20)):
                cx = bx + side * ox
                if side < 0:
                    d.arc(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), 100, 260, fill=255, width=int(6 * s))
                else:
                    d.arc(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), -80, 80, fill=255, width=int(6 * s))

    def rose(d, s):  # an iron rose: three rings of petals around a round centre
        cx = W / 2
        for ring, (n, rad, pr) in enumerate(((7, 126, 52), (6, 98, 46), (5, 72, 40))):
            for k in range(n):
                a = k / n * 2 * math.pi + ring * 0.4
                px, py = cx + math.cos(a) * rad * 0.62, cy + math.sin(a) * rad * 0.62
                d.ellipse(((px - pr) * s, (py - pr) * s, (px + pr) * s, (py + pr) * s), fill=255)

    def rose_edges(d, s):
        cx = W / 2
        for ring, (n, rad, pr) in enumerate(((7, 126, 52), (6, 98, 46), (5, 72, 40))):
            for k in range(n):
                a = k / n * 2 * math.pi + ring * 0.4
                px, py = cx + math.cos(a) * rad * 0.62, cy + math.sin(a) * rad * 0.62
                d.arc(((px - pr) * s, (py - pr) * s, (px + pr) * s, (py + pr) * s), math.degrees(a) - 80, math.degrees(a) + 80, fill=255, width=int(8 * s))

    win = mask(W, H, lambda d, s: d.rectangle((x0 * s, y0 * s, x1 * s, y1 * s), fill=255))
    backing = mask(W, H, lambda d, s: d.rectangle((140 * s, (y0 - 6) * s, (W - 140) * s, (y1 + 6) * s), fill=255))
    rose_m = mask(W, H, rose)
    core = mask(W, H, lambda d, s: d.ellipse(((W / 2 - 92) * s, (cy - 92) * s, (W / 2 + 92) * s, (cy + 92) * s), fill=255))
    layers = [
        (np.clip(backing - win, 0, 1), 0.25, 0.2, 8, "blackiron"),
        (mask(W, H, vines), 0.5, 0.45, 8, "blackiron"),
        (mask(W, H, thorns), 0.5, 0.35, 5, "blackiron"),
        (mask(W, H, tips_mask), 0.7, 0.2, 3, "brass"),
        (mask(W, H, bead), 0.55, 0.25, 4, "brass"),
        (mask(W, H, buds), 0.5, 0.5, 26, "blackiron"),
        (mask(W, H, bud_lines), 0.75, 0.1, 2, "brass"),
        (np.clip(rose_m - core * 0.0, 0, 1), 0.6, 0.45, 18, "blackiron"),
        (mask(W, H, rose_edges) * rose_m, 0.98, 0.12, 3, "brass"),
    ]
    return bake(W, H, layers, seed=31)


def render_C(frame, health, fill, accent, state):
    W, H, cy = W4, C_H, C_CY
    x0, x1, y0, y1 = C_WIN
    out = Image.new("RGBA", (W, H))
    track = Image.new("RGBA", (x1 - x0, y1 - y0), (8, 5, 7, 255))
    fw = int((x1 - x0) * health)
    if fw > 0:
        tile = velvet_tile(fill).resize((512, y1 - y0), Image.LANCZOS)
        track.alpha_composite(tiled(tile, fw, y1 - y0).crop((0, 0, fw, y1 - y0)))
    out.alpha_composite(track, (x0, y0))
    out.alpha_composite(frame)
    g = glass_disc(176, accent, 0.35 if state == "downed" else 1.0)
    out.alpha_composite(g, (W // 2 - 88, cy - 88))
    pct_text(out, W // 2, cy, health, 64)
    return out


# ================================================================ sheets
CONCEPTS = {
    "A": ("A  Vigil", "A wrought-iron candelabrum. Ten wax candles stand on the bar, one per 10% of health, and snuff out from the right as you're hurt (a wisp of smoke rises off the last). Crimson-glass quatrefoil medallion.", frame_A, render_A, A_CY, 70),
    "B": ("B  Reliquary", "A sealed blood reliquary. The blood fills a long glass vial held in a brass cage with clawed finials. A gothic lancet spire rises from the middle and holds a ruby with the %.", frame_B, render_B, B_CY, 76),
    "C": ("C  Thornrose", "A briar of black iron. Two thorned vines (brass-tipped thorns) twist along the bar, closed rosebuds at the ends, crimson velvet for the fill and an iron rose at the centre.", frame_C, render_C, C_CY, 40 + 44),
}


def cell(concept, frame, st):
    title, sub, _, render, cy, below = CONCEPTS[concept]
    label, health, fill, accent, state = st
    art = render(frame, health, fill, accent, state)
    Wd, Hd = 600, art.size[1] / 4
    bar = art.resize((Wd * SC, int(Hd * SC)), Image.LANCZOS)
    margin = 20
    rail_y = int(round(cy / 4 + below / 4 - 2))   # the rail box top: 2 px under the bar art
    total_h = int(max(Hd, rail_y + 24) + 12)
    c = Image.new("RGBA", ((Wd + margin * 2) * SC, total_h * SC))
    if state == "low":
        c.alpha_composite(glow((c.size[0], c.size[1]), (255, 60, 50), 0.22, 1.0))
    pp.SC = SC
    pp.GOLD, pp.EMBER = (226, 168, 72), (255, 122, 46)
    pp.posture_rail(c, margin, rail_y, 0.35, "calm", centre_out=True, frame_img=POSTURE / "PostureFrame.png")
    c.alpha_composite(bar, (margin * SC, 0))
    return c


def sheet(concept):
    title, sub, frame_fn, *_ = CONCEPTS[concept]
    frame = frame_fn()
    frame.save(OUT / f"frame_{concept}.png")
    cells = [cell(concept, frame, st) for st in STATES]
    cw = cells[0].size[0]
    ch = max(c.size[1] for c in cells)
    cols, pad = 2, 16
    rows = math.ceil(len(cells) / cols)
    out = Image.new("RGBA", (cols * (cw + pad) + pad, 110 + rows * (ch + 36)), (14, 11, 16, 255))
    out.alpha_composite(backdrop(out.size[0], out.size[1] - 100), (0, 100))
    d = ImageDraw.Draw(out)
    d.text((pad, 12), title, font=font(34), fill=(235, 205, 120))
    d.text((pad, 58), sub, font=font(19, False), fill=(214, 206, 196))
    for i, (c, st) in enumerate(zip(cells, STATES)):
        x = pad + (i % cols) * (cw + pad)
        y = 110 + (i // cols) * (ch + 36)
        d.text((x + 20, y + 2), st[0], font=font(22), fill=(235, 205, 120))
        out.alpha_composite(c, (x, y + 28))
    out.save(OUT / f"concept_{concept}.png")
    return out


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "ABC"
    sheets = [sheet(c) for c in which]
    if which == "ABC":
        W = max(s.size[0] for s in sheets)
        allsheet = Image.new("RGB", (W, sum(s.size[1] for s in sheets)), (14, 11, 16))
        y = 0
        for s in sheets:
            allsheet.paste(s.convert("RGB"), (0, y))
            y += s.size[1]
        allsheet.save(OUT / "health-v4-options.jpg", quality=90)
        print(OUT / "health-v4-options.jpg", allsheet.size)
