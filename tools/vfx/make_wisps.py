"""Night cloud-wisp textures for the SkyMotion Beams (sky-2360 spec section 4).

usage: python tools/vfx/make_wisps.py [outdir=art/group-upload-skies]
Writes NHWisp_A.png and NHWisp_B.png: 1024x256 white RGBA, tiling left-right (the noise is sampled on a circle in U), soft
at the top and bottom so a Beam's edges never show. Beam.Color tints them (the DayCycle key's cloud colour).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "art", "group-upload-skies")
sys.argv = [sys.argv[0], OUT, "64"]  # make_skyboxes reads argv at import
sys.path.insert(0, HERE)
import make_skyboxes as M  # noqa: E402

W, H = 1024, 256


def wisp(seed, stretch, cover, soft, streak):
    u = (np.arange(W) + 0.5) / W * 2 * math.pi
    v = (np.arange(H) + 0.5) / H
    U, V = np.meshgrid(u, v)
    r = 0.9 * stretch
    P = np.stack([np.cos(U) * r, np.sin(U) * r, V * 6.0], -1).astype(np.float32)
    warp = np.stack([M.fbm3(P * 0.6, 3, seed + 1), M.fbm3(P * 0.6 + 5.3, 3, seed + 2), np.zeros_like(U)], -1)
    P2 = P + (warp - 0.5) * 1.4
    d = M.fbm3(P2 * np.array([1.0, 1.0, streak], np.float32), 5, seed)
    a = M.ss(1 - cover, 1 - cover + soft, d)
    band = np.sin(np.pi * V) ** 1.6                          # fade to nothing at the top and bottom edges
    a = a * band
    shade = 0.72 + 0.28 * M.ss(0.3, 0.8, d)                  # brighter cores, slightly dimmer edges
    rgb = np.clip(shade, 0, 1)
    img = np.dstack([rgb, rgb, rgb, np.clip(a, 0, 1)])
    return Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    wisp(301, 1.0, 0.5, 0.34, 1.6).save(os.path.join(OUT, "NHWisp_A.png"), optimize=True)
    wisp(307, 1.5, 0.44, 0.34, 2.0).save(os.path.join(OUT, "NHWisp_B.png"), optimize=True)
    print("NHWisp_A.png NHWisp_B.png ->", os.path.abspath(OUT))
