"""PBR wax seal for the UI kit (Theme.Images.Seal), baked to an image.

The kit tints the seal everywhere it's used (gold on the arrival and region cards, crimson for danger, rarity colours on
gems, the touch buttons), so it stays GREYSCALE: the shading is done in full PBR (make_health_pbr.shade: GGX specular,
Lambert diffuse, a warm key, a cool fill, a candle rim, an environment reflection, AO from the height), then reduced
to luminance, and ImageColor3 colours it in game.

The design keeps the old seal's read: a hand-pressed wax blob with a scalloped, dripping edge and a raised lip where the
stamp pushed the wax out; inside it, the pressed stamp: a bevelled border ring, a ring of clock ticks (long at the
quarters), and the school's diamond-cross emblem with a pearl at its heart and small quatrefoils on the diagonals.

    python make_seal_pbr.py
Writes art/ui/hud/out/seal_v2/seal.png (512), seal_256.png and preview.png (gold / crimson / white tints).
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as H

OUT = Path(__file__).resolve().parent / "out" / "seal_v2"
OUT.mkdir(parents=True, exist_ok=True)
S = 1024                       # work size; saved at 512 (and 256)
rng = np.random.default_rng(7)

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
X = (xx + 0.5) / S * 2 - 1     # -1..1
Y = (yy + 0.5) / S * 2 - 1
R = np.hypot(X, Y)
TH = np.arctan2(Y, X)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def angular_noise(k, amp, seed):
    """A smooth random wobble around the circle (periodic in angle)."""
    r = np.random.default_rng(seed)
    out = np.zeros_like(TH)
    for n in range(1, k + 1):
        out += r.normal() / n * np.sin(n * TH + r.random() * 6.283)
    return out * amp


def blur_noise(sigma, seed):
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.random((S, S)).astype(np.float32), sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


# ---------- the wax blob ----------
edge = 0.88 + 0.028 * np.sin(9 * TH + 0.4) + angular_noise(14, 0.012, 3)
for ang, size in ((0.6, 0.07), (2.4, 0.05), (4.1, 0.08), (5.5, 0.045)):      # drips pushed out past the edge
    d = np.angle(np.exp(1j * (TH - ang)))
    edge += size * np.exp(-(d / 0.09) ** 2)
inside = R / edge                                       # < 1 inside the wax
alpha = smooth(1.0, 0.985, inside)                       # anti-aliased outline (~1.5 px)
to_edge = (1 - inside)                                   # 0 at the edge, 1 at the centre
lump = blur_noise(18, 11) * 0.06 + blur_noise(5, 12) * 0.015
wax = H.dome(np.clip(to_edge * 6, 0, 1), 1.0) * 0.55 + lump
lip = 0.16 * np.exp(-((to_edge - 0.085) / 0.035) ** 2)   # raised lip where the stamp pushed the wax out

# ---------- the pressed stamp ----------
STAMP = 0.64
stamp = smooth(STAMP + 0.012, STAMP - 0.012, R)          # the pressed disc
press = -0.24 * stamp
border = 0.13 * np.exp(-((R - (STAMP - 0.045)) / 0.012) ** 2) * stamp + 0.06 * np.exp(-((R - (STAMP - 0.09)) / 0.006) ** 2)
# ticks: 12, long at the quarters
ticks = np.zeros_like(R)
for i in range(12):
    a = i * math.pi / 6
    long = i % 3 == 0
    r0, r1 = (0.40, 0.53) if long else (0.46, 0.53)
    w = 0.018 if long else 0.011
    ux, uy = math.cos(a), math.sin(a)
    along = X * ux + Y * uy
    across = np.abs(-X * uy + Y * ux)
    t = smooth(w, w * 0.4, across) * smooth(r0 - 0.005, r0 + 0.005, along) * smooth(r1 + 0.005, r1 - 0.005, along)
    ticks = np.maximum(ticks, t * (0.12 if long else 0.08))
# the diamond-cross emblem
diam = np.abs(X) + np.abs(Y)
outer_d = smooth(0.012, 0.0, np.abs(diam - 0.22)) * 0.12
inner_d = smooth(0.010, 0.0, np.abs(diam - 0.13)) * 0.09
cross = np.maximum(smooth(0.016, 0.006, np.abs(X)) * smooth(0.36, 0.34, np.abs(Y)),
                   smooth(0.016, 0.006, np.abs(Y)) * smooth(0.36, 0.34, np.abs(X))) * 0.08
cross *= smooth(0.12, 0.14, diam) + smooth(0.24, 0.22, diam) * 0       # the bars run outside the inner diamond
pearl = H.dome(np.clip((0.06 - R) / 0.06, 0, 1), 1.0) * 0.12
quat = np.zeros_like(R)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    cx_, cy_ = 0.30 * math.cos(a), 0.30 * math.sin(a)
    for j in range(4):
        b = j * math.pi / 2
        px, py = cx_ + 0.022 * math.cos(b), cy_ + 0.022 * math.sin(b)
        quat = np.maximum(quat, H.dome(np.clip((0.024 - np.hypot(X - px, Y - py)) / 0.024, 0, 1), 1.0) * 0.06)
emblem = (ticks + outer_d + inner_d + cross + pearl + quat) * stamp * 1.6

height = (wax + lip + press + border + emblem) * alpha
height = ndimage.gaussian_filter(height, 0.8)

# ---------- materials (greyscale: the kit tints it) ----------
raised = np.clip((border + emblem) * 8, 0, 1)
albedo = np.full((S, S, 3), 0.78, np.float32)
albedo *= (0.9 + 0.1 * blur_noise(3, 21))[..., None]                       # wax mottling
albedo = H.srgb_to_lin(albedo)
rough = np.clip(0.24 - raised * 0.1 + (blur_noise(6, 22) - 0.5) * 0.1 + (1 - stamp) * 0.04, 0.08, 1)
metal = np.zeros((S, S), np.float32)
micro = np.dstack([(blur_noise(1.5, 31) - 0.5), (blur_noise(1.5, 32) - 0.5), np.zeros((S, S))]).astype(np.float32)
N = H.normals_from(height * S * 0.5, 1.0 / 7.5, micro, 0.35)
ao = H.ao_from(height, 10, 5) * H.ao_from(height, 3, 9)
rgb = H.shade(albedo, N, rough, metal, ao)
lum = (rgb[..., 0] * 0.3 + rgb[..., 1] * 0.55 + rgb[..., 2] * 0.15)
lum = np.clip((lum - 0.04) * 1.25, 0, 1)    # bright enough that a tint reads true, with deep shadows


def save(img, size, name):
    a = np.dstack([img, img, img, alpha]) * 255
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
    im.save(OUT / name, optimize=True)
    return im


big = save(lum, 512, "seal.png")
save(lum, 256, "seal_256.png")

# preview: the seal as the game tints it (gold, crimson, white) over the HUD's dark ground
bg = Image.new("RGBA", (3 * 300, 300), (18, 16, 24, 255))
for i, tint in enumerate(((228, 186, 110), (190, 40, 56), (240, 238, 232))):
    t = np.array(big, np.float32)
    t[..., :3] *= np.array(tint, np.float32) / 255
    im = Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA").resize((256, 256), Image.LANCZOS)
    bg.alpha_composite(im, (i * 300 + 22, 22))
bg.save(OUT / "preview.png")
print("wrote", OUT / "seal.png", OUT / "preview.png")
