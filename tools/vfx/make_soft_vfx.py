"""Soft-edged VFX textures for the main menu and the loading screen (numpy + Pillow, no Blender).

usage: python make_soft_vfx.py <outdir> [path/to/nh_shards_2x2.png]

  nh_wisp2_v.png       crimson-ring tendril (Beam) texture: 9 twisting filaments + a hot core + fine fibres.
                       Tiles seamlessly along the beam; alpha falls to exactly zero at both side edges, so beams
                       never show straight cut-off lines. Saved rotated (256 x 1024): Roblox Beams run the image's
                       vertical axis along the beam.
  nh_shards2_2x2.png   the 2x2 crystal-shard flipbook with every sprite faded out before its cell edge
                       (the original sprites crossed the cell borders, so particles showed sliced edges).
  nh_load_grain.png    film-grain tile for the loading screen (white specks on transparent).
"""
import os
import sys

import numpy as np
from PIL import Image

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(11)

# ---------------------------------------------------------------- tendril
W, H = 1024, 256
x = np.arange(W)[None, :] / W        # along the beam (integer frequencies only -> tiles)
y = np.linspace(-1, 1, H)[:, None]    # across the beam


def periodic_curve(n_waves, amp):
    c = np.zeros((1, W))
    for _ in range(n_waves):
        f = rng.integers(1, 7)
        c += rng.uniform(0.3, 1) * np.sin(2 * np.pi * f * x + rng.uniform(0, 6.28))
    return c / n_waves * amp


def periodic_noise(octaves=5):
    n = np.zeros((H, W))
    for o in range(octaves):
        fx = 2 ** (o + 2)
        for _ in range(3):
            n += np.sin(2 * np.pi * fx * x + rng.uniform(0, 6.28) + rng.uniform(1, 4) * (o + 1) * y * 3) / (o + 1)
    return (n - n.min()) / (n.max() - n.min())


env = np.clip(1 - y ** 2, 0, 1) ** 3          # zero at the side edges
a = np.zeros((H, W))
for _ in range(9):
    c = periodic_curve(3, rng.uniform(0.15, 0.5))
    a += rng.uniform(0.35, 1.0) * np.exp(-((y - c) / rng.uniform(0.025, 0.09)) ** 2)
core = np.exp(-(y / 0.18) ** 2) * (0.55 + 0.45 * np.sin(2 * np.pi * 3 * x + 1.3) ** 2)
a = (a * 0.7 + core * 0.8) * (0.55 + 0.6 * periodic_noise())
a = np.clip(a * env, 0, None)
a = np.clip(a / np.percentile(a, 99.7), 0, 1) ** 1.15
white = np.ones((H, W, 3)) * 255
img = Image.fromarray(np.dstack([white, a * 255]).astype(np.uint8), "RGBA")
img.transpose(Image.Transpose.ROTATE_90).save(os.path.join(out, "nh_wisp2_v.png"))

# ---------------------------------------------------------------- shards: fade inside each cell
shards = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "nh_shards_2x2.png")
if os.path.exists(shards):
    im = np.array(Image.open(shards).convert("RGBA")).astype(float)
    h, w = im.shape[:2]
    ch, cw = h // 2, w // 2
    yy, xx = np.mgrid[0:ch, 0:cw]
    d = np.minimum.reduce([xx, cw - 1 - xx, yy, ch - 1 - yy]) / (cw / 2)
    m = np.clip(d / 0.28, 0, 1)
    m = m * m * (3 - 2 * m)
    for r in range(2):
        for c in range(2):
            im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, 3] *= m
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(out, "nh_shards2_2x2.png"))

# ---------------------------------------------------------------- film grain
g = 256
noise = np.random.default_rng(3).random((g, g))
tile = np.zeros((g, g, 4), np.uint8)
tile[..., :3] = 255
tile[..., 3] = (np.clip((noise - 0.5) * 2, 0, 1) ** 3 * 255).astype(np.uint8)
Image.fromarray(tile, "RGBA").save(os.path.join(out, "nh_load_grain.png"))
print("done:", out)
