"""Re-project the written sky faces into equirect panoramas (Blender's world-texture convention) for preview_scene.py.

usage: python tools/sky-2360/equirect.py <outdir> [width=2048] [faces=art/group-upload-skies] [only=Night,...]
Samples NHSky<Set>_<Face>.png through make_skyboxes' measured Roblox face mapping, so the preview sees exactly the faces
that get uploaded (Roblox -Z = Blender +Y = the preview camera's forward).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTDIR = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
FACES_DIR = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "art", "group-upload-skies")
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else None
sys.argv = [sys.argv[0], FACES_DIR, "64"]   # make_skyboxes reads argv at import
sys.path.insert(0, os.path.join(ROOT, "tools", "vfx"))
import make_skyboxes as M  # noqa: E402


def dirs(w):
    """Blender equirect pixel -> Roblox sky direction (X right, Y up, -Z = Blender +Y)."""
    h = w // 2
    u = (np.arange(w) + 0.5) / w
    v = 1 - (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    phi = (0.5 - U) * 2 * math.pi
    th = (V - 0.5) * math.pi
    bx, by, bz = np.cos(phi) * np.cos(th), np.sin(phi) * np.cos(th), np.sin(th)
    return np.stack([bx, bz, -by], -1).astype(np.float32)


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    D = dirs(W)
    for name in M.SKIES:
        if ONLY and name not in ONLY:
            continue
        img = M.sample_cube(M.load_faces(name), D)
        Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUTDIR, f"{name}.png"))
        print(name, flush=True)
