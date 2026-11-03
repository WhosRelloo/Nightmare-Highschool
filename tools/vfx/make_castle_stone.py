"""NH_CastleStone: a seamless 2048 PBR wall set matching the courtyard castle stone (props batch 8).

usage: python tools/vfx/make_castle_stone.py [outdir=art/props/textures] [size=2048]

Starts from the NH_Limestone set (art/props/source_2k, made by make_pbr_materials.py), tints it to the batch-8 CastleStone
(linear tint 0.27, 0.285, 0.265): the arch wall's own weathered stone, no block joints (the owner's pick), with tileable
grime and moss mottling, so a builder can put the same stone on his own
walls (a MaterialVariant, StudsPerTile 8) and on the cloister arch's wall piece (CloisterArch_Wall, UVs at 8 studs a tile).
Everything is periodic over the texture, so it tiles in both directions.
Writes NH_CastleStone_color.png, _normal.png, _rough.png, _metal.png.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "art", "props", "source_2k")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "props", "textures")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
TINT = np.array([0.27, 0.285, 0.265])
MOSS = np.array([0.035, 0.06, 0.028])


def load(kind):
    im = Image.open(os.path.join(SRC, f"NH_Limestone_{kind}.png")).convert("RGB")
    if im.size != (N, N):
        im = im.resize((N, N), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def periodic(seed, octaves=5, base=3):
    """Smooth tileable noise in 0..1: sums of sines with integer frequencies over the texture."""
    rnd = np.random.default_rng(seed)
    y, x = np.mgrid[0:N, 0:N].astype(np.float32) / N * 2 * np.pi
    f = np.zeros((N, N), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        k = base * 2 ** o
        for _ in range(4):
            fx, fy = rnd.integers(-k, k + 1), rnd.integers(-k, k + 1)
            if fx == 0 and fy == 0:
                fx = k
            f += amp * np.sin(fx * x + fy * y + rnd.uniform(0, 2 * np.pi))
            total += amp
        amp *= 0.55
    return (f / total) * 0.5 + 0.5


col = to_lin(load("color"))
grime = periodic(11)
moss = np.clip((periodic(23, octaves=4, base=2) - 0.6) * 3.0, 0, 1) ** 1.5
lin = col * TINT * (0.78 + 0.44 * grime[..., None])
lin = lin * (1 - 0.55 * moss[..., None]) + MOSS * 0.55 * moss[..., None]
Image.fromarray((to_srgb(lin) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, "NH_CastleStone_color.png"))

nrm = Image.open(os.path.join(SRC, "NH_Limestone_normal.png")).convert("RGB")
if nrm.size != (N, N):
    nrm = nrm.resize((N, N), Image.LANCZOS)
nrm.save(os.path.join(OUT, "NH_CastleStone_normal.png"))

rough = load("rough")[..., 0]
rough = np.clip(rough * 0.9 + 0.12 + 0.1 * moss, 0, 1)
Image.fromarray((rough * 255 + 0.5).astype(np.uint8), "L").save(os.path.join(OUT, "NH_CastleStone_rough.png"))
Image.fromarray(np.zeros((N, N), np.uint8), "L").save(os.path.join(OUT, "NH_CastleStone_metal.png"))
print("wrote NH_CastleStone_{color,normal,rough,metal}.png to", OUT)
