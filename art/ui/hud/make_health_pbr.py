"""PBR health bar for the KitHud (Nightmare Highschool), baked to images.

Roblox UI can't light textures live, so each piece is lit here once: a height field and material mask are
built in 2D, normals come from the height plus the school's seamless PBR detail normals (art/props/source),
and every pixel is shaded with GGX specular + Lambert diffuse from albedo / roughness / metalness maps,
a warm key light from the top-left, a cool fill, a candle rim from below and a simple environment
reflection for the metals. Ambient occlusion comes from the height field.

Pieces (art/ui/hud/out/health_v2/):
  frame.png   2400x200  the whole bar frame for a 600x50 bar (12:1): hammered iron bands with scratched-brass
                        beads and rivets, pointed gothic end pieces with a brass spike and a crimson gem, brass
                        collars where the orb sits. The window (where the fill shows) is transparent.
  fill.png     768x144  the fill tile (192:36, tiles horizontally): greyscale blood-glass with veins, bubbles
                        and a glassy highlight. The HUD tints it (crimson; other colours for other states).
  orb_ring.png 512x512  the orb's ring: brass with a raised bead, rivets and four quatrefoil studs
  orb_glass.png 512x512 the orb's glass: a glossy greyscale sphere (tinted by the HUD)
  preview.png           the pieces assembled over a dark backdrop

  python make_health_pbr.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "props" / "source"
OUT = HERE / "out" / "health_v2"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- material maps
def load_map(name, kind, size, period):
    """A seamless map resampled so one repeat spans `period` px, tiled over `size` (w, h)."""
    im = Image.open(SRC / f"NH_{name}_{kind}.png").convert("RGB").resize((period, period), Image.LANCZOS)
    a = np.array(im, np.float32) / 255.0
    w, h = size
    reps = (h // period + 1, w // period + 1, 1)
    return np.tile(a, reps)[:h, :w]


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def material(name, size, period, tint=(1, 1, 1), rough_mul=1.0, rough_add=0.0, metal=None):
    col = srgb_to_lin(load_map(name, "color", size, period)) * np.array(tint, np.float32)
    nrm = load_map(name, "normal", size, period) * 2 - 1
    rough = np.clip(load_map(name, "rough", size, period)[..., 0] * rough_mul + rough_add, 0.04, 1)
    met = load_map(name, "metal", size, period)[..., 0] if metal is None else np.full(size[::-1], metal, np.float32)
    return col, nrm, rough, met


# ---------------------------------------------------------------- shading
def normalize(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-8)


LIGHTS = [  # direction to the light (x right, y DOWN, z toward the viewer), colour, intensity
    (normalize(np.array([-0.55, -0.65, 0.55])), np.array([1.0, 0.9, 0.78]), 3.4),
    (normalize(np.array([0.6, 0.35, 0.7])), np.array([0.55, 0.62, 0.9]), 0.7),
    (normalize(np.array([0.0, 0.95, 0.3])), np.array([1.0, 0.55, 0.28]), 0.8),
]


def shade(albedo, N, rough, metal, ao, emissive=None):
    V = np.array([0.0, 0.0, 1.0])
    NdotV = np.clip(N[..., 2], 1e-3, 1)
    F0 = 0.04 * (1 - metal[..., None]) + albedo * metal[..., None]
    a = np.clip(rough, 0.04, 1) ** 2
    out = np.zeros_like(albedo)
    for L, col, inten in LIGHTS:
        Hh = normalize(L + V)
        NdotL = np.clip((N * L).sum(-1), 0, 1)
        NdotH = np.clip((N * Hh).sum(-1), 0, 1)
        VdotH = np.clip((V * Hh).sum(-1), 0, 1)
        D = a ** 2 / (np.pi * (NdotH ** 2 * (a ** 2 - 1) + 1) ** 2 + 1e-8)
        k = (rough + 1) ** 2 / 8
        G = (NdotL / (NdotL * (1 - k) + k + 1e-8)) * (NdotV / (NdotV * (1 - k) + k + 1e-8))
        F = F0 + (1 - F0) * ((1 - VdotH) ** 5)[..., None]
        spec = (D * G)[..., None] * F / (4 * NdotL[..., None] * NdotV[..., None] + 1e-4)
        diff = (1 - metal[..., None]) * albedo / np.pi * (1 - F)
        out += (diff + spec) * (NdotL[..., None] * col * inten)
    # environment: a warm ceiling, a dark floor, reflected per pixel
    R = 2 * NdotV[..., None] * N - V
    up = np.clip(-R[..., 1] * 0.5 + 0.5, 0, 1)[..., None]
    env = np.array([0.05, 0.04, 0.05]) * (1 - up) + np.array([0.95, 0.78, 0.58]) * up
    Fv = F0 + (1 - F0) * ((1 - NdotV) ** 5)[..., None]
    out += env * Fv * (1 - 0.75 * rough[..., None]) * 0.9
    out += albedo * 0.06 * (1 - metal[..., None] * 0.6)
    out *= ao[..., None]
    if emissive is not None:
        out += emissive
    out = out / (1 + out) * 1.18     # gentle filmic roll-off
    return lin_to_srgb(out)


def normals_from(Hf, strength, detail=None, detail_k=0.0):
    gy, gx = np.gradient(Hf)
    N = np.dstack([-gx * strength, -gy * strength, np.ones_like(Hf)])
    if detail is not None:
        dn = detail.copy()
        dn[..., 1] = -dn[..., 1]      # OpenGL green is +up; our y runs down
        N[..., :2] += dn[..., :2] * detail_k
    return normalize(N)


def ao_from(Hf, sigma, k):
    blur = ndimage.gaussian_filter(Hf, sigma)
    return np.clip(1 - np.clip(blur - Hf, 0, None) * k, 0.35, 1)


def dome(mask_dist, r):
    t = np.clip(mask_dist / r, 0, 1)
    return np.sqrt(1 - (1 - t) ** 2)


def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def polymask(size, polys, ellipses=(), ss=2):
    w, h = size
    m = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    for (x0, y0, x1, y1) in ellipses:
        d.ellipse((x0 * ss, y0 * ss, x1 * ss, y1 * ss), fill=255)
    return np.array(m.resize((w, h), Image.BOX), np.float32) / 255.0


# ---------------------------------------------------------------- frame
def frame():
    W, H = 2400, 200
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron = material("Iron", (W, H), 384, tint=(0.26, 0.25, 0.28), rough_mul=0.72)
    brass = material("Brass", (W, H), 320, tint=(1.0, 0.86, 0.62), rough_mul=0.7, rough_add=-0.05)
    # --- shapes (window x 150..2250, y 52..148)
    wx0, wx1, wy0, wy1 = 150, 2250, 52, 148
    outer = [(6, 100), (70, 20), (W - 70, 20), (W - 6, 100), (W - 70, 180), (70, 180)]
    body = polymask((W, H), [outer])
    window = polymask((W, H), [[(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)]])
    band = np.clip(body - window, 0, 1)
    # end blocks (ornate iron) and the window's inner brass bead
    endL = polymask((W, H), [[(6, 100), (70, 20), (wx0 + 6, 20), (wx0 + 6, 180), (70, 180)]])
    endR = endL[:, ::-1]
    ends = np.clip(endL + endR, 0, 1)
    bead_in = np.clip(polymask((W, H), [[(wx0 - 7, wy0 - 7), (wx1 + 7, wy0 - 7), (wx1 + 7, wy1 + 7), (wx0 - 7, wy1 + 7)]]) - window, 0, 1)
    outer_shrunk = polymask((W, H), [[(18, 100), (76, 28), (W - 76, 28), (W - 18, 100), (W - 76, 172), (76, 172)]])
    bead_out = np.clip(body - outer_shrunk, 0, 1)
    # rivets along the bands (skipping the orb collar), brass collars above/below the orb
    rivets = []
    for x in range(260, W - 240, 170):
        if abs(x - W / 2) < 230:
            continue
        for y in (36, 164):
            rivets.append((x - 7, y - 7, x + 7, y + 7))
    riv = polymask((W, H), [], rivets)
    collar = polymask((W, H), [[(W / 2 - 210, 14), (W / 2 + 210, 14), (W / 2 + 170, 58), (W / 2 - 170, 58)],
                               [(W / 2 - 170, 142), (W / 2 + 170, 142), (W / 2 + 210, 186), (W / 2 - 210, 186)]])
    # gem sockets on the end blocks, and brass spikes at the tips
    gems, rings = [], []
    for cx in (92, W - 92):
        rings.append((cx - 40, 60, cx + 40, 140))
        gems.append((cx - 27, 73, cx + 27, 127))
    ring = np.clip(polymask((W, H), [], rings) - polymask((W, H), [], gems), 0, 1)
    gem = polymask((W, H), [], gems)
    spikes = polymask((W, H), [[(0, 100), (26, 88), (40, 100), (26, 112)], [(W, 100), (W - 26, 88), (W - 40, 100), (W - 26, 112)]])
    # --- height field
    def dist(m):
        return ndimage.distance_transform_edt(m > 0.5)
    Hf = np.zeros((H, W), np.float32)
    # band: convex across its width
    Hf = np.maximum(Hf, band * (0.3 + 0.5 * dome(dist(band), 13)))
    # an engraved groove along the middle of each band
    for gy0 in (36, 164):
        Hf -= band * np.exp(-((YY - gy0) / 1.6) ** 2) * 0.12 * ((XX > wx0) & (XX < wx1))
    Hf = np.maximum(Hf, ends * (0.5 + 0.35 * dome(dist(ends), 10)))
    Hf = np.maximum(Hf, bead_in * (0.62 + 0.25 * dome(dist(bead_in), 4)))
    Hf = np.maximum(Hf, bead_out * (0.55 + 0.25 * dome(dist(bead_out), 4)))
    Hf = np.maximum(Hf, collar * (0.75 + 0.2 * dome(dist(collar), 8)))
    Hf = np.maximum(Hf, ring * (0.85 + 0.3 * dome(dist(ring), 6)))
    Hf = np.maximum(Hf, riv * (0.7 + 0.35 * dome(dist(riv), 6)))
    Hf = np.maximum(Hf, spikes * (0.7 + 0.3 * dome(dist(spikes), 5)))
    Hf = np.maximum(Hf, gem * (0.9 + 0.5 * dome(dist(gem), 22)))
    # hammered dents on the iron band
    rng = np.random.default_rng(7)
    dents = ndimage.gaussian_filter(rng.standard_normal((H, W)), 3.0)
    Hf -= np.clip(dents, 0, None) * 0.05 * (band + ends) * (1 - np.clip(bead_in + bead_out + riv + collar, 0, 1))
    alpha = np.clip(body - window + spikes, 0, 1)
    alpha = np.maximum(alpha, bead_in)   # the inner bead slightly overlaps the window edge
    # --- materials per pixel
    is_brass = np.clip(bead_in + bead_out + riv + collar + ring + spikes, 0, 1)[..., None]
    is_gem = gem[..., None]
    albedo = iron[0] * (1 - is_brass) + brass[0] * is_brass
    rough = iron[2] * (1 - is_brass[..., 0]) + brass[2] * is_brass[..., 0]
    metal = np.clip(iron[3] * 0.0 + 0.85, 0, 1) * (1 - is_brass[..., 0]) + 1.0 * is_brass[..., 0]
    detail = iron[1] * (1 - is_brass) + brass[1] * is_brass
    albedo = albedo * (1 - is_gem) + np.array([0.42, 0.012, 0.03]) * is_gem
    rough = rough * (1 - gem) + 0.07 * gem
    metal = metal * (1 - gem)
    # gothic tracery engraved on the end blocks (a pointed arch outline), filled darker
    for cx, flip in ((92, 1), (W - 92, -1)):
        pass
    N = normals_from(Hf, 34.0, detail, 0.35)
    ao = ao_from(Hf, 6, 2.2)
    # crimson gem: an inner glow
    gd = np.hypot(XX[..., None] * 0 + XX[..., None] - 0, 0)[..., 0] * 0
    glow = np.zeros((H, W, 3), np.float32)
    for cx in (92, W - 92):
        r = np.hypot(XX - cx - 6, YY - 106)
        glow += (np.clip(1 - r / 24, 0, 1) ** 2)[..., None] * np.array([0.5, 0.04, 0.05]) * gem[..., None]
    rgb = shade(albedo, N, rough, metal, ao, emissive=glow)
    # a soft contact shadow on the fill under the inner bead (drawn inside the window, partly transparent)
    sh = ndimage.gaussian_filter(np.clip(bead_in, 0, 1), 5) * window
    rgb = rgb * (1 - sh[..., None]) + 0 * sh[..., None]
    alpha = np.maximum(alpha, sh * 0.55)
    return save(rgb, alpha, "frame.png")


# ---------------------------------------------------------------- fill (greyscale, tinted in game)
def periodic_noise(h, w, sigma, seed):
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal((h, w)), sigma, mode="wrap")
    return n / (n.std() + 1e-6)


def fill():
    W, H = 768, 144
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    t = YY / (H - 1)
    # glass depth: brighter through the middle, darker at the bottom
    base = 0.62 + 0.25 * np.sin(np.pi * np.clip(t * 1.1, 0, 1)) - 0.25 * t ** 3
    veins = np.abs(periodic_noise(H, W, (6, 26), 3))
    veins = np.clip(1 - veins / 0.35, 0, 1) ** 2
    swirl = periodic_noise(H, W, (10, 40), 4) * 0.08
    v = base + swirl - veins * 0.22
    # small bubbles
    rng = np.random.default_rng(11)
    for _ in range(26):
        cx, cy, r = rng.uniform(0, W), rng.uniform(H * 0.25, H * 0.9), rng.uniform(1.5, 4)
        for ox in (-W, 0, W):
            d = np.hypot(XX - cx - ox, YY - cy)
            v += np.clip(1 - np.abs(d - r) / 1.2, 0, 1) * 0.18
            v -= np.clip(1 - d / r, 0, 1) * 0.06
    # glassy highlight band near the top, a thin bright meniscus, shadowed lower edge
    v += np.exp(-((t - 0.22) / 0.07) ** 2) * 0.32
    v += np.exp(-((t - 0.06) / 0.025) ** 2) * 0.2
    v -= np.exp(-((t - 0.97) / 0.05) ** 2) * 0.3
    v = np.clip(v, 0, 1.25)
    rgb = np.dstack([v, v, v]) / 1.25
    return save(rgb, np.ones((H, W)), "fill.png")


# ---------------------------------------------------------------- orb ring and glass
def orb_ring():
    S = 512
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    r = np.hypot(XX - c, YY - c)
    brass = material("Brass", (S, S), 256, tint=(1.0, 0.86, 0.62), rough_mul=0.7, rough_add=-0.05)
    iron = material("Iron", (S, S), 256, tint=(0.26, 0.25, 0.28), rough_mul=0.72)
    ring = ((r >= 178) & (r <= 252)).astype(np.float32)
    ring = ndimage.gaussian_filter(ring, 0.8)
    # profile: an outer brass bead, an iron channel, an inner brass bead
    prof = np.where(r > 236, 0.6 + 0.35 * np.sqrt(np.clip(1 - ((r - 244) / 8) ** 2, 0, 1)),
           np.where(r < 194, 0.6 + 0.35 * np.sqrt(np.clip(1 - ((r - 186) / 8) ** 2, 0, 1)),
                    0.45 + 0.12 * np.sin(np.pi * np.clip((r - 194) / 42, 0, 1))))
    Hf = prof * ring
    is_brass = ((r > 236) | (r < 194)).astype(np.float32)
    # rivets and four quatrefoil studs in the channel
    ang = np.arctan2(YY - c, XX - c)
    studs = np.zeros((S, S), np.float32)
    for k in range(12):
        a = k / 12 * 2 * np.pi
        px, py = c + np.cos(a) * 215, c + np.sin(a) * 215
        big = k % 3 == 0
        rr = 13 if big else 6
        d = np.hypot(XX - px, YY - py)
        studs = np.maximum(studs, np.clip(1 - d / rr, 0, 1))
        if big:
            for j in range(4):
                b = a + j * np.pi / 2
                d2 = np.hypot(XX - (px + np.cos(b) * 9), YY - (py + np.sin(b) * 9))
                studs = np.maximum(studs, np.clip(1 - d2 / 7, 0, 1))
    stud_h = np.sqrt(np.clip(studs, 0, 1)) * 0.45
    Hf = np.maximum(Hf, (0.55 + stud_h) * (studs > 0.01))
    is_brass = np.clip(is_brass + (studs > 0.01), 0, 1)[..., None]
    albedo = iron[0] * (1 - is_brass) + brass[0] * is_brass
    rough = iron[2] * (1 - is_brass[..., 0]) + brass[2] * is_brass[..., 0]
    metal = 0.85 * (1 - is_brass[..., 0]) + is_brass[..., 0]
    detail = iron[1] * (1 - is_brass) + brass[1] * is_brass
    N = normals_from(Hf, 30.0, detail, 0.3)
    ao = ao_from(Hf, 5, 2.0)
    rgb = shade(albedo, N, rough, metal, ao)
    alpha = np.clip(ring + (studs > 0.01), 0, 1)
    return save(rgb, alpha, "orb_ring.png")


def orb_glass():
    S = 512
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    c = (S - 1) / 2
    R = 250.0
    r = np.hypot(XX - c, YY - c) / R
    inside = r < 1
    z = np.sqrt(np.clip(1 - r ** 2, 0, 1))
    N = normalize(np.dstack([(XX - c) / R, (YY - c) / R, z]))
    L = normalize(np.array([-0.5, -0.6, 0.62]))
    ndl = np.clip((N * L).sum(-1), 0, 1)
    v = 0.35 + 0.25 * ndl
    # glass: a dark rim (Fresnel), a bright inner glow from below, a sharp top-left highlight
    v -= (1 - z) ** 2 * 0.35
    v += np.exp(-(((XX - c) / R) ** 2 + ((YY - c - R * 0.45) / R) ** 2) / 0.12) * 0.35
    hl = np.exp(-(((XX - c + R * 0.38) / R) ** 2 + ((YY - c + R * 0.42) / R) ** 2) / 0.012)
    v += hl * 0.65
    swirl = periodic_noise(S, S, 18, 5) * 0.04
    v = np.clip(v + swirl, 0, 1)
    edge = np.clip((1 - r) * R / 1.5, 0, 1)
    return save(np.dstack([v, v, v]), edge * inside, "orb_glass.png")


def preview(paths):
    fr = Image.open(paths["frame"]).convert("RGBA")
    W, H = fr.size
    bg = Image.new("RGBA", (W + 80, H + 200), (22, 18, 24, 255))
    track = Image.new("RGBA", (int(2112), int(112)), (10, 6, 9, 255))
    fill_t = Image.open(paths["fill"]).convert("RGBA")
    tinted = Image.new("RGBA", fill_t.size)
    a = np.array(fill_t, np.float32)
    a[..., :3] *= np.array([150, 18, 30], np.float32) / 255.0
    tinted = Image.fromarray(a.astype(np.uint8), "RGBA").resize((int(768 * 112 / 144), 112))
    filled = Image.new("RGBA", track.size)
    for x in range(0, int(track.size[0] * 0.72), tinted.size[0]):
        filled.alpha_composite(tinted, (x, 0))
    filled = filled.crop((0, 0, int(track.size[0] * 0.72), 112))
    track.alpha_composite(filled)
    bg.alpha_composite(track, (40 + 144, 100 + 44))
    bg.alpha_composite(fr, (40, 100))
    ring = Image.open(paths["orb_ring"]).convert("RGBA").resize((290, 290))
    glass = Image.open(paths["orb_glass"]).convert("RGBA").resize((214, 214))
    ga = np.array(glass, np.float32)
    ga[..., :3] *= np.array([96, 26, 40], np.float32) / 255.0 * 1.6
    glass = Image.fromarray(np.clip(ga, 0, 255).astype(np.uint8), "RGBA")
    cx, cy = 40 + W // 2, 100 + H // 2
    bg.alpha_composite(glass, (cx - 107, cy - 107))
    bg.alpha_composite(ring, (cx - 145, cy - 145))
    bg.save(OUT / "preview.png")
    small = bg.resize((bg.size[0] // 2, bg.size[1] // 2), Image.LANCZOS)
    small.save(OUT / "preview_half.png")


if __name__ == "__main__":
    paths = {"frame": frame(), "fill": fill(), "orb_ring": orb_ring(), "orb_glass": orb_glass()}
    preview(paths)
    for k, p in paths.items():
        print(k, p)
