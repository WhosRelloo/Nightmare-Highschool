"""Nightmare High eyelid overlays for blinking / squinting (one decal per eye shape and state).

Each shape's real lid curves come from gen_eyes.STYLES (lid geometry doesn't change with sex or form).
  lids_<shape>_blink.png   the whole opening covered with skin + a closed lash line low on the eye
  lids_<shape>_squint.png  the upper ~45% covered + a lash line along the new lid edge
White where skin goes (the game tints it with Decal.Color3 = the character's skin colour) and near-black
lashes (stay dark under the tint). 1024x1024 RGBA, 4x supersampled. Decal ZIndex 3, over the eye layers.
usage: python gen_lids.py <outdir>
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else "lids"
sys.argv = [sys.argv[0], os.path.join(OUT, "_scratch")]   # gen_eyes reads argv[1] as its own outdir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_eyes as E  # noqa: E402

os.makedirs(OUT, exist_ok=True)
N, S = 1024, 4
INK = (18, 13, 20)


def poly(dr, pts, fill):
    dr.polygon([(float(x) * S, float(y) * S) for x, y in pts], fill=fill)


def stroke(dr, pts, w0, w1, fill):
    """a tapered stroke: thicker in the middle, thin at both ends"""
    n = len(pts)
    for i in range(n - 1):
        t = i / (n - 1)
        w = w0 + (w1 - w0) * np.sin(np.pi * t) ** 0.8
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        dr.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=fill, width=max(1, int(w * S)))
        dr.ellipse([(x1 - w / 2) * S, (y1 - w / 2) * S, (x1 + w / 2) * S, (y1 + w / 2) * S], fill=fill)


def render(shape, state):
    st = E.STYLES[shape]
    im = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0))
    skin = Image.new("L", (N * S, N * S), 0)
    lash = Image.new("L", (N * S, N * S), 0)
    ds, dl = ImageDraw.Draw(skin), ImageDraw.Draw(lash)
    for side in (0, 1):
        U, L = E.eye_geometry(st, side)
        # pad the lid a few px past the opening so the eye art never peeks around the edge
        Up = U.copy(); Up[:, 1] -= 4
        Lp = L.copy(); Lp[:, 1] += 5
        if state == "blink":
            poly(ds, np.vstack([Up, Lp[::-1]]), 255)
            edge = U + (L - U) * 0.78                     # the closed lid line sits low on the eye
            stroke(dl, edge, 3, 11, 255)
            # a few short lashes dropping from the closed line toward the outer corner
            for t in (0.62, 0.74, 0.86, 0.96):
                k = int(t * (len(edge) - 1))
                x, y = edge[k]
                dx = 1 if (st["O"][0] < st["I"][0]) == (side == 0) else -1
                dl.line([(x * S, y * S), ((x + dx * 6 * t) * S, (y + 9 + 5 * t) * S)], fill=255, width=int(2.6 * S))
        else:
            edge = U + (L - U) * 0.45
            poly(ds, np.vstack([Up, edge[::-1]]), 255)
            stroke(dl, edge, 3, 10, 255)
    sk = np.asarray(skin, np.float32) / 255
    la = np.asarray(lash, np.float32) / 255
    rgb = np.ones((N * S, N * S, 3), np.float32)
    ink = np.array(INK, np.float32) / 255
    rgb = rgb * (1 - la[..., None]) + ink * la[..., None]
    a = np.clip(np.maximum(sk, la), 0, 1)
    out = np.dstack([rgb, a]).reshape(N, S, N, S, 4).mean((1, 3))
    # un-premultiply the box filter so edges don't go grey
    rgbo = out[..., :3] / np.maximum(out[..., 3:], 1e-4)
    rgbo = np.where(out[..., 3:] > 1e-4, rgbo, 1.0)
    img = np.dstack([np.clip(rgbo, 0, 1), out[..., 3]])
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"lids_{shape}_{state}.png"), optimize=True)


if __name__ == "__main__":
    for sh in E.STYLES:
        for state in ("blink", "squint"):
            render(sh, state)
            print("ok", sh, state, flush=True)
    print("done")
