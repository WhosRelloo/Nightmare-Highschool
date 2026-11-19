"""The Wickfield logos (art/hometown/logos/out/<Logo>_color.png + _height.png) as PBR sign canvases for the props pipeline:
art/props/textures/<Canvas>_canvas.png (+ _canvas_normal, _canvas_rough, _canvas_metal; _canvas_emissive for neon).

  python art/hometown/logo_canvases.py
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "logos", "out")
OUT = os.path.abspath(os.path.join(HERE, "..", "props", "textures"))

# canvas name: (logo, background behind any transparency, base roughness, relief strength, gilt metal?, neon emissive?)
SIGNS = {
    "WF_SignMoonpie": ("MoonpieDiner", (12, 13, 22), 0.35, 4.0, False, True),
    "WF_SignHardware": ("WickSonsHardware", (20, 40, 28), 0.55, 6.0, True, False),
    "WF_SignVideo": ("ReelTimeVideo", (20, 36, 110), 0.3, 4.0, False, True),
    "WF_SignSuds": ("SudsLaundromat", (180, 225, 210), 0.35, 4.0, False, False),
    "WF_SignGazette": ("WickfieldGazette", (236, 228, 208), 0.8, 2.5, False, False),
    "WF_PlaqueFounder": ("FounderPlaque", (90, 60, 30), 0.4, 7.0, True, False),
    "WF_CrestTown": ("WickfieldCrest", (40, 60, 34), 0.5, 5.0, True, False),
    "WF_CrestWicks": ("WicksMascot", (30, 70, 45), 0.5, 4.0, False, False),
    "WF_CrestPumas": ("PembrookPumas", (70, 36, 112), 0.4, 4.0, False, False),
}


def u8(a):
    return np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)


for name, (logo, bg, rough0, strength, gilt, neon) in SIGNS.items():
    rgba = np.asarray(Image.open(os.path.join(LOG, f"{logo}_color.png")).convert("RGBA"), np.float32) / 255.0
    h = np.asarray(Image.open(os.path.join(LOG, f"{logo}_height.png")), np.float32) / 65535.0
    a = rgba[..., 3:4]
    col = rgba[..., :3] * a + np.array(bg, np.float32)[None, None, :] / 255.0 * (1 - a)
    Image.fromarray(u8(col), "RGB").save(os.path.join(OUT, f"{name}_canvas.png"))
    hh = ndimage.gaussian_filter(h, 0.8)
    gy, gx = np.gradient(hh)
    nx, ny, nz = -gx * strength * 40, gy * strength * 40, np.ones_like(hh)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    Image.fromarray(u8(np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5), "RGB").save(os.path.join(OUT, f"{name}_canvas_normal.png"))
    r_, g_, b_ = col[..., 0], col[..., 1], col[..., 2]
    metal = np.zeros_like(r_)
    rough = np.full_like(r_, rough0) - 0.15 * hh
    if gilt:
        gold = ((r_ > 0.6) & (g_ > 0.42) & (b_ < g_ * 0.8) & (r_ - b_ > 0.25)).astype(np.float32)
        metal = ndimage.gaussian_filter(gold, 0.8)
        rough = rough * (1 - metal) + 0.28 * metal
    Image.fromarray(u8(np.clip(rough, 0, 1)), "L").save(os.path.join(OUT, f"{name}_canvas_rough.png"))
    Image.fromarray(u8(metal), "L").save(os.path.join(OUT, f"{name}_canvas_metal.png"))
    if neon:
        lum = col.max(-1)
        sat = lum - col.min(-1)
        em = np.clip((lum - 0.55) * 3, 0, 1) * np.clip(sat * 2 + (lum > 0.92), 0, 1)
        Image.fromarray(u8(ndimage.gaussian_filter(em, 0.6)), "L").save(os.path.join(OUT, f"{name}_canvas_emissive.png"))
    print("ok", name)
