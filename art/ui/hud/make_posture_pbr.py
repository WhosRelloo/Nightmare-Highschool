"""PBR posture bar for the KitHud (Nightmare Highschool), baked to images, plus the design mockups.

Same pipeline and lights as make_health_pbr.py (it imports that script's shader), so the posture bar reads
as the same forged piece as the health bar: hammered iron, scratched brass, the school's PBR detail maps.

Pieces (art/ui/hud/out/posture/), sized for a 600 x 24 design-px bar that hangs under the 600 x 50 health bar:
  PostureFrame.png   2400x96   the rail: an iron band with brass beads, pointed ends that echo the health bar's
                               caps, smoked-glass gems in the ends and a brass saddle in the middle that cradles
                               the health orb. The window (x 150..2250, y 28..68) is transparent.
  PostureFill.png    512x64    the fill tile (tiles horizontally): greyscale molten brass with a bright meniscus.
                               The HUD tints it (candle gold, warming to ember near a break).
  PostureCracks2.png 1024x240  three crack stages for the right half of the window (centre -> end), 40 px rows,
                               then the same three turned 180 degrees for the left half. Dark cores with a warm
                               rim baked in (ImageColor3 stays white).
  PostureShards.png  512x128   four glass shards (128 px cells) for the guard-break shatter. Greyscale.
  mockup_*.png                 the design options beside the real health bar art (for the owner to choose)

  python make_posture_pbr.py            # art + mockups
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

OUT = HERE / "out" / "posture"
OUT.mkdir(parents=True, exist_ok=True)
HEALTH = HERE / "out" / "health_v2"
DOCS = HERE.parents[2] / "docs" / "img"


def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def dist(m):
    return ndimage.distance_transform_edt(m > 0.5)


# ---------------------------------------------------------------- frame (2400 x 96 = 600 x 24 at 4x)
WX0, WX1, WY0, WY1 = 150, 2250, 28, 68


def frame(saddle=True, name="PostureFrame.png"):
    W, H = 2400, 96
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron = hp.material("Iron", (W, H), 384, tint=(0.26, 0.25, 0.28), rough_mul=0.72)
    brass = hp.material("Brass", (W, H), 320, tint=(1.0, 0.86, 0.62), rough_mul=0.7, rough_add=-0.05)
    pm = hp.polymask
    outer = [(14, 48), (62, 8), (W - 62, 8), (W - 14, 48), (W - 62, 88), (62, 88)]
    body = pm((W, H), [outer])
    window = pm((W, H), [[(WX0, WY0), (WX1, WY0), (WX1, WY1), (WX0, WY1)]])
    band = np.clip(body - window, 0, 1)
    endL = pm((W, H), [[(14, 48), (62, 8), (WX0 + 4, 8), (WX0 + 4, 88), (62, 88)]])
    ends = np.clip(endL + endL[:, ::-1], 0, 1)
    bead_in = np.clip(pm((W, H), [[(WX0 - 6, WY0 - 6), (WX1 + 6, WY0 - 6), (WX1 + 6, WY1 + 6), (WX0 - 6, WY1 + 6)]]) - window, 0, 1)
    shrunk = pm((W, H), [[(24, 48), (66, 13), (W - 66, 13), (W - 24, 48), (W - 66, 83), (66, 83)]])
    bead_out = np.clip(body - shrunk, 0, 1)
    # rivets: one row centred on the thin bands is too cramped, so studs sit on the bead_out line every 240 px
    rivets = []
    for x in range(330, W - 300, 240):
        if saddle and abs(x - W / 2) < 300:
            continue
        rivets.append((x - 6, 12 - 6 + 6, x + 6, 12 + 6 + 6))
        rivets.append((x - 6, 84 - 6 - 6, x + 6, 84 + 6 - 6))
    riv = pm((W, H), [], rivets)
    # gem sockets on the end blocks (smoked glass: lit by the HUD's glow when a break is near)
    gems, rings = [], []
    for cx in (88, W - 88):
        rings.append((cx - 30, 18, cx + 30, 78))
        gems.append((cx - 20, 28, cx + 20, 68))
    ring = np.clip(pm((W, H), [], rings) - pm((W, H), [], gems), 0, 1)
    gem = pm((W, H), [], gems)
    spikes = pm((W, H), [[(0, 48), (22, 40), (34, 48), (22, 56)], [(W, 48), (W - 22, 40), (W - 34, 48), (W - 22, 56)]])
    sad = np.zeros((H, W), np.float32)
    if saddle:
        # a brass saddle under the orb: a trapezoid block with a round cut where the orb's lower edge rests
        sad = pm((W, H), [[(W / 2 - 184, 4), (W / 2 + 184, 4), (W / 2 + 150, 92), (W / 2 - 150, 92)]])
        cut = np.hypot(XX - W / 2, YY + 88) < 156
        sad = sad * (1 - cut)
        rivets += [(W / 2 - 136 - 7, 64 - 7, W / 2 - 136 + 7, 64 + 7), (W / 2 + 136 - 7, 64 - 7, W / 2 + 136 + 7, 64 + 7)]
        riv = pm((W, H), [], rivets)
    Hf = np.zeros((H, W), np.float32)
    Hf = np.maximum(Hf, band * (0.3 + 0.5 * hp.dome(dist(band), 8)))
    Hf = np.maximum(Hf, ends * (0.5 + 0.35 * hp.dome(dist(ends), 8)))
    Hf = np.maximum(Hf, bead_in * (0.62 + 0.25 * hp.dome(dist(bead_in), 3)))
    Hf = np.maximum(Hf, bead_out * (0.55 + 0.25 * hp.dome(dist(bead_out), 3)))
    Hf = np.maximum(Hf, riv * (0.7 + 0.35 * hp.dome(dist(riv), 5)))
    Hf = np.maximum(Hf, ring * (0.85 + 0.3 * hp.dome(dist(ring), 5)))
    Hf = np.maximum(Hf, spikes * (0.7 + 0.3 * hp.dome(dist(spikes), 4)))
    Hf = np.maximum(Hf, gem * (0.9 + 0.45 * hp.dome(dist(gem), 16)))
    if saddle:
        Hf = np.maximum(Hf, sad * (0.78 + 0.18 * hp.dome(dist(sad), 9)))
        Hf = np.maximum(Hf, riv * (0.7 + 0.35 * hp.dome(dist(riv), 5)))
    rng = np.random.default_rng(17)
    dents = ndimage.gaussian_filter(rng.standard_normal((H, W)), 2.4)
    Hf -= np.clip(dents, 0, None) * 0.05 * (band + ends) * (1 - np.clip(bead_in + bead_out + riv + sad, 0, 1))
    alpha = np.clip(body - window + spikes + sad, 0, 1)
    alpha = np.maximum(alpha, bead_in)
    is_brass = np.clip(bead_in + bead_out + riv + ring + spikes + sad, 0, 1)[..., None]
    is_gem = gem[..., None]
    albedo = iron[0] * (1 - is_brass) + brass[0] * is_brass
    rough = iron[2] * (1 - is_brass[..., 0]) + brass[2] * is_brass[..., 0]
    metal = 0.85 * (1 - is_brass[..., 0]) + is_brass[..., 0]
    detail = iron[1] * (1 - is_brass) + brass[1] * is_brass
    # smoked amber glass (the health bar's gems are crimson: these read as "guard", not "blood")
    albedo = albedo * (1 - is_gem) + np.array([0.16, 0.10, 0.04]) * is_gem
    rough = rough * (1 - gem) + 0.07 * gem
    metal = metal * (1 - gem)
    N = hp.normals_from(Hf, 30.0, detail, 0.35)
    ao = hp.ao_from(Hf, 5, 2.2)
    glow = np.zeros((H, W, 3), np.float32)
    for cx in (88, W - 88):
        r = np.hypot(XX - cx - 4, YY - 52)
        glow += (np.clip(1 - r / 18, 0, 1) ** 2)[..., None] * np.array([0.22, 0.12, 0.03]) * gem[..., None]
    rgb = hp.shade(albedo, N, rough, metal, ao, emissive=glow)
    sh = ndimage.gaussian_filter(np.clip(bead_in + sad, 0, 1), 4) * window * (1 - sad)
    rgb = rgb * (1 - sh[..., None])
    alpha = np.maximum(alpha, sh * 0.5)
    return save(rgb, alpha, name)


# ---------------------------------------------------------------- fill tile (greyscale molten brass)
def fill():
    W, H = 512, 64
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    t = YY / (H - 1)
    base = 0.58 + 0.3 * np.sin(np.pi * np.clip(t * 1.05, 0, 1)) - 0.28 * t ** 3
    flow = hp.periodic_noise(H, W, (3, 30), 21) * 0.07
    grain = np.abs(hp.periodic_noise(H, W, (2.5, 14), 22))
    grain = np.clip(1 - grain / 0.3, 0, 1) ** 2 * 0.1
    v = base + flow + grain
    v += np.exp(-((t - 0.2) / 0.07) ** 2) * 0.35       # bright band near the top
    v += np.exp(-((t - 0.05) / 0.03) ** 2) * 0.22      # meniscus
    v -= np.exp(-((t - 0.96) / 0.06) ** 2) * 0.32
    v = np.clip(v, 0, 1.25) / 1.25
    return save(np.dstack([v, v, v]), np.ones((H, W)), "PostureFill.png")


# ---------------------------------------------------------------- cracks (3 stages, one half of the window)
CRACK_W, CRACK_H = 1024, 40   # one row; it shows at 262 x 10 design px, so lines are drawn ~4x thick


def crack_paths(seed, n, x_from, x_to, branch_p, length):
    """Random forked fracture polylines in one CRACK_W x CRACK_H row (x: centre -> end of the half window)."""
    rng = np.random.default_rng(seed)
    H = CRACK_H
    paths = []
    for _ in range(n):
        x = rng.uniform(x_from, x_to)
        y = rng.uniform(H * 0.3, H * 0.7)
        ang = rng.uniform(-0.5, 0.5)
        pts = [(x, y)]
        L = rng.uniform(*length)
        step = 26
        travelled = 0
        while travelled < L:
            ang += rng.normal(0, 0.28)
            ang = float(np.clip(ang, -1.0, 1.0))
            x += math.cos(ang) * step
            y += math.sin(ang) * step * 0.6
            if y < 4 or y > H - 4:
                ang = -ang
                y = float(np.clip(y, 4, H - 4))
            pts.append((x, y))
            travelled += step
            if rng.random() < branch_p:
                bx, by, ba = x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
                bpts = [(bx, by)]
                for _ in range(rng.integers(1, 3)):
                    bx += math.cos(ba) * 18
                    by += math.sin(ba) * 10
                    by = float(np.clip(by, 3, H - 3))
                    bpts.append((bx, by))
                    ba += rng.normal(0, 0.25)
                paths.append((bpts, 3.2))
        paths.append((pts, 5.4))
    return paths


def cracks():
    CW, CH, SS = CRACK_W, CRACK_H, 4
    sheet = Image.new("RGBA", (CW, CH * 6), (0, 0, 0, 0))
    stages = [
        crack_paths(5, 1, 20, 120, 0.18, (220, 300)),
        crack_paths(6, 2, 300, 560, 0.18, (200, 300)),
        crack_paths(7, 3, 560, 960, 0.2, (150, 260)),
    ]
    for i, paths in enumerate(stages):
        core = Image.new("L", (CW * SS, CH * SS), 0)
        d = ImageDraw.Draw(core)
        for pts, w in paths:  # tapered: full width where the crack starts, a hairline at its tip
            for k in range(len(pts) - 1):
                ww = w * (1 - 0.7 * k / max(1, len(pts) - 1))
                d.line([(pts[k][0] * SS, pts[k][1] * SS), (pts[k + 1][0] * SS, pts[k + 1][1] * SS)], fill=255, width=max(1, int(ww * SS)))
                r = ww * SS / 2
                d.ellipse((pts[k + 1][0] * SS - r, pts[k + 1][1] * SS - r, pts[k + 1][0] * SS + r, pts[k + 1][1] * SS + r), fill=255)
        core = core.resize((CW, CH), Image.LANCZOS)
        a = np.array(core, np.float32) / 255.0
        # a bright chipped edge just below each fracture, and a soft dark bruise around it
        rim = np.clip(ndimage.shift(ndimage.gaussian_filter(a, 1.0), (3.0, 1.0)) - a, 0, 1)
        shadow = ndimage.gaussian_filter(a, 4.0)
        alpha = np.clip(a + rim * 0.85 + shadow * 0.4, 0, 1)
        dark = np.array([0.07, 0.025, 0.02])
        lite = np.array([1.0, 0.95, 0.8])
        w_rim = (rim * 0.85 / (alpha + 1e-6))[..., None]
        rgb = dark * (1 - w_rim) + lite * w_rim
        img = Image.fromarray(np.dstack([rgb * 255, alpha * 255]).astype(np.uint8), "RGBA")
        sheet.alpha_composite(img, (0, i * CH))
        # rows 3-5: the same stage turned 180 degrees for the left half (Roblox doesn't clip rotated GuiObjects)
        sheet.alpha_composite(img.rotate(180), (0, (i + 3) * CH))
    sheet.save(OUT / "PostureCracks2.png", optimize=True)
    return OUT / "PostureCracks2.png"


# ---------------------------------------------------------------- shards (4 glass splinters, 128 px cells)
def shards():
    S = 128
    sheet = np.zeros((S, S * 4, 4), np.float32)
    rng = np.random.default_rng(31)
    for k in range(4):
        n = rng.integers(3, 6)
        angs = np.sort(rng.uniform(0, 2 * np.pi, n))
        rad = rng.uniform(20, 56, n) * np.array([1.0 if j % 2 == 0 else 0.55 for j in range(n)])
        poly = [(S / 2 + math.cos(a) * r * 1.3, S / 2 + math.sin(a) * r * 0.75) for a, r in zip(angs, rad)]
        m = hp.polymask((S, S), [poly], ss=4)
        d = dist(m)
        h = hp.dome(d, 6) * m
        gy, gx = np.gradient(h)
        lit = np.clip(0.55 - gx * 6 - gy * 6, 0, 1)
        edge = np.clip(1 - d / 2.5, 0, 1) * m
        v = np.clip(lit * 0.7 + edge * 0.5 + 0.15, 0, 1)
        sheet[:, k * S:(k + 1) * S, 0:3] = v[..., None]
        sheet[:, k * S:(k + 1) * S, 3] = m * (0.55 + 0.45 * edge)
    Image.fromarray((sheet * 255).astype(np.uint8), "RGBA").save(OUT / "PostureShards.png", optimize=True)
    return OUT / "PostureShards.png"


# ================================================================ mockups
SC = 2  # mockups are drawn at 2x design px
BLOOD = (0x96, 0x16, 0x22)
GOLD = (0xEB, 0xCD, 0x78)
GOLD_DEEP = (0x96, 0x70, 0x32)
EMBER = (0xFF, 0x9A, 0x4A)
INK = (0x07, 0x06, 0x0A)
BONE = (0xE4, 0xDE, 0xD0)
CRIMSON = (0xC8, 0x28, 0x3C)


def tint(im, rgb, mul=1.0):
    a = np.array(im.convert("RGBA"), np.float32)
    a[..., :3] = np.clip(a[..., :3] * np.array(rgb, np.float32) / 255.0 * mul, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def font(size, bold=True):
    for f in ("C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/timesbd.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def glow_spot(size, rgb, strength=1.0, sigma=None):
    w, h = size
    YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((XX - w / 2) / (w / 2), (YY - h / 2) / (h / 2))
    a = np.clip(1 - r, 0, 1) ** 2 * strength
    img = np.dstack([np.full((h, w), c, np.float32) for c in rgb] + [a * 255])
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")


def tiled(tile, w, h):
    w = max(1, w)
    out = Image.new("RGBA", (w, max(1, h)))
    for x in range(0, w, tile.size[0]):
        out.alpha_composite(tile, (x, 0))
    return out


def health_bar(canvas, x, y, frac=0.82):
    """The real KitHud health bar (600 x 50) at (x, y) design px."""
    k = 50 / 64
    tx, ty, tw, th = 46 * k, 14 * k, 600 - 92 * k, 36 * k
    track = Image.new("RGBA", (int(tw * SC), int(th * SC)), (10, 6, 9, 255))
    ft = tint(Image.open(HEALTH / "fill.png"), BLOOD).resize((int(192 * k * SC), int(36 * k * SC)), Image.LANCZOS)
    fw = int(tw * SC * frac)
    track.alpha_composite(tiled(ft, fw, track.size[1]).crop((0, 0, fw, track.size[1])))
    canvas.alpha_composite(track, (int((x + tx) * SC), int((y + ty) * SC)))
    fr = Image.open(HEALTH / "frame.png").resize((600 * SC, 50 * SC), Image.LANCZOS)
    canvas.alpha_composite(fr, (x * SC, y * SC))
    o = 50 * 1.45
    cx, cy = (x + 300) * SC, (y + 25) * SC
    halo = glow_spot((int(o * 1.5 * SC), int(o * 1.5 * SC)), (0, 0, 0), 0.8)
    canvas.alpha_composite(halo, (int(cx - halo.size[0] / 2), int(cy - halo.size[1] / 2)))
    gl = tint(Image.open(HEALTH / "orb_glass.png"), (150, 34, 52), 1.6).resize((int(o * 0.74 * SC),) * 2, Image.LANCZOS)
    canvas.alpha_composite(gl, (int(cx - gl.size[0] / 2), int(cy - gl.size[1] / 2)))
    rg = Image.open(HEALTH / "orb_ring.png").resize((int(o * SC),) * 2, Image.LANCZOS)
    canvas.alpha_composite(rg, (int(cx - rg.size[0] / 2), int(cy - rg.size[1] / 2)))
    d = ImageDraw.Draw(canvas)
    f = font(int(50 * 0.33 * SC))
    d.text((cx, cy), f"{round(frac * 100)}%", font=f, fill=BONE, anchor="mm", stroke_width=2, stroke_fill=(20, 10, 12))


def hotbar(canvas, x, y):
    for i in range(6):
        sx = x + i * 80
        d = ImageDraw.Draw(canvas)
        d.rectangle([sx * SC, y * SC, (sx + 70) * SC, (y + 70) * SC], fill=(24, 20, 30, 235), outline=(110, 100, 112, 255), width=2)
        d.text(((sx + 6) * SC, (y + 4) * SC), str(i + 1), font=font(11 * SC, False), fill=(200, 190, 180))


def exp_strip(canvas, x, y, w):
    d = ImageDraw.Draw(canvas)
    d.rectangle([(x + 46) * SC, (y + 8) * SC, (x + w) * SC, (y + 10) * SC], fill=(7, 6, 10, 170))
    d.rectangle([(x + 46) * SC, (y + 8) * SC, (x + 46 + (w - 46) * 0.4) * SC, (y + 10) * SC], fill=GOLD + (150,))
    d.text(((x + 12) * SC, (y + 9) * SC), "IV", font=font(14 * SC), fill=GOLD + (150,), anchor="lm")


def posture_rail(canvas, x, y, frac, state, centre_out=True, frame_img=None):
    """The posture rail (600 x 24) at (x, y). state: calm | warn | broken."""
    fx0, fx1 = WX0 / 4, WX1 / 4           # window, design px (37.5 .. 562.5)
    fy0, fy1 = WY0 / 4, WY1 / 4           # 7 .. 17
    wh = fy1 - fy0
    col = GOLD if state == "calm" else (255, 176, 96) if state == "warn" else (255, 240, 220)
    if state == "calm":
        col = tuple(int(a + (b - a) * frac * 0.5) for a, b in zip(GOLD, EMBER))
    tile = tint(Image.open(OUT / "PostureFill.png"), col, 1.05).resize((int(128 * SC), int(wh * SC)), Image.LANCZOS)
    track = Image.new("RGBA", (int((fx1 - fx0) * SC), int(wh * SC)), (12, 8, 8, 255))
    tw = track.size[0]
    cr = Image.open(OUT / "PostureCracks2.png")
    stages = 0 if frac < 0.4 else 1 if frac < 0.65 else 2 if frac < 0.85 else 3
    if centre_out:
        half = tw / 2
        sad = 44 * SC                       # the saddle hides the middle +-44 px
        reach = int(sad + (half - sad) * frac) if state != "broken" else 0
        for side in ((-1, 1) if reach > 0 else ()):
            seg = tiled(tile, reach, track.size[1]).crop((0, 0, reach, track.size[1]))
            if side > 0:
                track.alpha_composite(seg, (int(half), 0))
            else:
                track.alpha_composite(seg.transpose(Image.FLIP_LEFT_RIGHT), (int(half - reach), 0))
        # cracks, clipped to the filled part
        for s in range(stages if reach > 0 else 0):
            c = cr.crop((0, s * CRACK_H, CRACK_W, (s + 1) * CRACK_H)).resize((int(half), track.size[1]), Image.LANCZOS)
            cm = Image.new("RGBA", c.size)
            cm.alpha_composite(c.crop((0, 0, reach, c.size[1])))
            track.alpha_composite(cm, (int(half), 0))
            track.alpha_composite(cm.rotate(180), (0, 0))
    else:
        reach = int(tw * frac) if state != "broken" else 0
        if reach > 0:
            track.alpha_composite(tiled(tile, reach, track.size[1]).crop((0, 0, reach, track.size[1])))
        for s in range(stages if reach > 0 else 0):
            c = cr.crop((0, s * CRACK_H, CRACK_W, (s + 1) * CRACK_H)).resize((tw, track.size[1]), Image.LANCZOS)
            cm = Image.new("RGBA", c.size)
            cm.alpha_composite(c.crop((0, 0, reach, c.size[1])))
            track.alpha_composite(cm)
    canvas.alpha_composite(track, (int((x + fx0) * SC), int((y + fy0) * SC)))
    fr = Image.open(frame_img or OUT / "PostureFrame.png").resize((600 * SC, 24 * SC), Image.LANCZOS)
    canvas.alpha_composite(fr, (x * SC, y * SC))
    if state in ("warn", "broken"):
        for gx in (x + 22, x + 578):
            g = glow_spot((40 * SC, 40 * SC), (255, 150, 60), 0.9 if state == "warn" else 1.0)
            canvas.alpha_composite(g, (int(gx * SC - g.size[0] / 2), int((y + 12) * SC - g.size[1] / 2)))


def broken_fx(canvas, x, y, w=600, h=24, centre_text=True):
    # white-gold flash over the rail, shards flying, the engraved GUARD / BROKEN words
    fl = glow_spot((int(w * 1.1 * SC), int(h * 3.2 * SC)), (255, 200, 140), 0.55)
    canvas.alpha_composite(fl, (int((x + w / 2) * SC - fl.size[0] / 2), int((y + h / 2) * SC - fl.size[1] / 2)))
    sh = Image.open(OUT / "PostureShards.png")
    rng = np.random.default_rng(3)
    for i in range(14):
        c = sh.crop(((i % 4) * 128, 0, (i % 4 + 1) * 128, 128))
        s = int(rng.uniform(16, 30) * SC)
        c = tint(c, (255, 226, 170)).resize((s, s), Image.LANCZOS).rotate(rng.uniform(0, 360), expand=True)
        px = x + rng.uniform(40, w - 40)
        py = y + h / 2 + rng.choice([-1, 1]) * rng.uniform(10, 34)
        canvas.alpha_composite(c, (int(px * SC - c.size[0] / 2), int(py * SC - c.size[1] / 2)))
    d = ImageDraw.Draw(canvas)
    f = font(17 * SC)
    if centre_text:
        d.text(((x + 300 - 104) * SC, (y + h / 2) * SC), "GUARD", font=f, fill=(240, 72, 84), anchor="rm", stroke_width=3, stroke_fill=(20, 4, 8))
        d.text(((x + 300 + 104) * SC, (y + h / 2) * SC), "BROKEN", font=f, fill=(240, 72, 84), anchor="lm", stroke_width=3, stroke_fill=(20, 4, 8))
    else:
        d.text(((x + 300) * SC, (y + h / 2) * SC), "GUARD BROKEN", font=f, fill=(240, 72, 84), anchor="mm", stroke_width=3, stroke_fill=(20, 4, 8))


def inlaid(canvas, x, y, frac, state):
    """Option C: posture lives inside the health frame's two iron bands (molten threads from the ends to the orb)."""
    col = GOLD if state == "calm" else (255, 170, 90) if state == "warn" else (255, 240, 220)
    d = ImageDraw.Draw(canvas)
    for gy in (9, 41):
        y0 = (y + gy) * SC
        reach = (300 - 52) * (frac if state != "broken" else 1)
        for side in (-1, 1):
            xa = x + 300 + side * (300 - 40)
            xb = xa - side * reach
            lo, hi = sorted((xa, xb))
            d.rectangle([lo * SC, y0 - 2 * SC, hi * SC, y0 + 2 * SC], fill=col + (255,))
    if state != "calm":
        g = glow_spot((640 * SC, 70 * SC), (255, 150, 60), 0.35 if state == "warn" else 0.8)
        canvas.alpha_composite(g, (int((x + 300) * SC - g.size[0] / 2), int((y + 25) * SC - g.size[1] / 2)))


def backdrop(w, h):
    src = None
    for name in ("garden-courtyard-night.jpg", "entrance-kit-night.jpg", "library-kit-night.jpg"):
        if (DOCS / name).exists():
            src = Image.open(DOCS / name).convert("RGB")
            break
    if src is None:
        return Image.new("RGBA", (w, h), (18, 14, 20, 255))
    s = max(w / src.size[0], h / src.size[1])
    src = src.resize((int(src.size[0] * s) + 1, int(src.size[1] * s) + 1), Image.LANCZOS)
    left = (src.size[0] - w) // 2
    src = src.crop((left, src.size[1] - h, left + w, src.size[1])).filter(ImageFilter.GaussianBlur(3))
    dark = Image.new("RGB", src.size, (8, 6, 10))
    return Image.blend(src, dark, 0.45).convert("RGBA")


def hud_scene(option, frac, state):
    """One HUD 'Bottom' frame (900 x 176 design px) with posture drawn per option."""
    W, H = 980, 250
    c = backdrop(W * SC, H * SC)
    bx, by = 40, 50                      # Bottom frame origin inside the panel
    if option == "B":                    # crown rail above: the health bar and everything below shift down 26
        by += 22
    hb_x, hb_y = bx + 150, by + 10
    health_bar(c, hb_x, hb_y)
    if option == "A":
        posture_rail(c, hb_x, hb_y + 47, frac, state, centre_out=True)
        health_bar_orb_over(c, hb_x, hb_y)
        exp_strip(c, hb_x + 30, hb_y + 72, 540)
        if state == "broken":
            broken_fx(c, hb_x, hb_y + 47)
    elif option == "B":
        posture_rail(c, hb_x, hb_y - 23, frac, state, centre_out=False, frame_img=OUT / "_frame_plain.png")
        exp_strip(c, hb_x + 30, hb_y + 51, 540)
        if state == "broken":
            broken_fx(c, hb_x, hb_y - 23, centre_text=False)
    else:
        inlaid(c, hb_x, hb_y, frac, state)
        health_bar_orb_over(c, hb_x, hb_y)
        exp_strip(c, hb_x + 30, hb_y + 51, 540)
        if state == "broken":
            broken_fx(c, hb_x, hb_y + 13, centre_text=True)
    hotbar(c, bx + 450 - 235, by + 106)
    return c


def health_bar_orb_over(c, x, y):
    """Redraw the orb on top (the orb sits over the posture rail's saddle in the real HUD too)."""
    o = 50 * 1.45
    cx, cy = (x + 300) * SC, (y + 25) * SC
    gl = tint(Image.open(HEALTH / "orb_glass.png"), (150, 34, 52), 1.6).resize((int(o * 0.74 * SC),) * 2, Image.LANCZOS)
    c.alpha_composite(gl, (int(cx - gl.size[0] / 2), int(cy - gl.size[1] / 2)))
    rg = Image.open(HEALTH / "orb_ring.png").resize((int(o * SC),) * 2, Image.LANCZOS)
    c.alpha_composite(rg, (int(cx - rg.size[0] / 2), int(cy - rg.size[1] / 2)))
    ImageDraw.Draw(c).text((cx, cy), "82%", font=font(int(50 * 0.33 * SC)), fill=BONE, anchor="mm", stroke_width=2, stroke_fill=(20, 10, 12))


def mockups():
    frame(saddle=False, name="_frame_plain.png")
    titles = {
        "A": "A  Twin Rail (recommended): a slim forged rail hung under the health bar; posture spreads out from the orb",
        "B": "B  Crown Rail: the same rail above the health bar, filling left to right like health",
        "C": "C  Inlaid: no new bar; posture glows along the health frame's own iron bands, ends to orb",
    }
    states = [(0.35, "calm", "35%: calm"), (0.88, "warn", "88%: cracking, ends glow (pulse)"), (1.0, "broken", "guard break: the fill shatters off, the rail reads GUARD BROKEN")]
    sheets = []
    for opt in "ABC":
        row = [hud_scene(opt, f, s) for f, s, _ in states]
        w, h = row[0].size
        sheet = Image.new("RGBA", (w * 3 + 40, h + 90), (14, 11, 16, 255))
        d = ImageDraw.Draw(sheet)
        d.text((20, 16), titles[opt], font=font(30), fill=GOLD)
        for i, im in enumerate(row):
            sheet.alpha_composite(im, (10 + i * (w + 10), 70))
            d.text((10 + i * (w + 10) + 16, 70 + 14), states[i][2], font=font(24, False), fill=BONE)
        sheet.save(OUT / f"mockup_{opt}.png")
        sheets.append(sheet)
    W = sheets[0].size[0]
    allsheet = Image.new("RGBA", (W, sum(s.size[1] for s in sheets)), (14, 11, 16, 255))
    yy = 0
    for s in sheets:
        allsheet.alpha_composite(s, (0, yy))
        yy += s.size[1]
    allsheet.convert("RGB").save(OUT / "mockup_all.jpg", quality=90)
    allsheet.resize((W // 2, allsheet.size[1] // 2), Image.LANCZOS).convert("RGB").save(OUT / "mockup_all_half.jpg", quality=90)


if __name__ == "__main__":
    for p in (frame(), fill(), cracks(), shards()):
        print(p)
    mockups()
    print(OUT / "mockup_all.jpg")
