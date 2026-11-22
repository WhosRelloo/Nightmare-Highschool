"""Grade the Blender previews like Roblox (exposure, ColorCorrection, Bloom), label them, and build the review sheets.

usage: python tools/sky-2360/post.py <raw dir from preview_scene.py> [out=docs/img/sky-2360]
Writes <name>.jpg per variant, Sky2360_Autumn.jpg (times of day + the 2.16 night), Sky2360_Moons.jpg (moons + storm)
and Sky2360_Events.jpg (the event seasons).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "img", "sky-2360")


def font(n):
    try:
        return ImageFont.truetype("georgia.ttf", n)
    except OSError:
        return ImageFont.load_default(size=n)


def grade(src, p):
    im = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255
    im = np.clip(im ** 2.2 * (2 ** p["ex"]), 0, None) ** (1 / 2.2)
    im = im + p["gb"]
    im = (im - 0.5) * (1 + p["con"]) + 0.5
    l = (im * [0.299, 0.587, 0.114]).sum(-1, keepdims=True)
    im = l + (im - l) * (1 + p["sat"])
    im = np.clip(im * (np.array(p["tint"]) / 255), 0, 1)
    br = np.clip((im.max(-1, keepdims=True) - 0.78) / 0.22, 0, 1) * im
    g = np.asarray(Image.fromarray((br * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
    im = np.clip(im + g * p["bloom"] * 1.6, 0, 1)
    out = Image.fromarray((im * 255 + 0.5).astype(np.uint8))
    ImageDraw.Draw(out).text((18, 14), p["title"], font=font(26), fill=(228, 222, 208), stroke_width=3, stroke_fill=(7, 6, 10))
    return out


def sheet(names, path, cols=3, w=640):
    ims = [Image.open(os.path.join(OUT, f"{n}.jpg")).resize((w, w * 9 // 16), Image.LANCZOS) for n in names]
    h = w * 9 // 16
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * w + (cols + 1) * 6, rows * h + (rows + 1) * 6), (7, 6, 10))
    for i, im in enumerate(ims):
        sh.paste(im, (6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 6)))
    sh.save(path, quality=88)
    print(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    P = json.load(open(os.path.join(RAW, "variants.json")))
    done = []
    for n, p in P.items():
        src = os.path.join(RAW, f"{n}_raw.png")
        if os.path.exists(src):
            grade(src, p).save(os.path.join(OUT, f"{n}.jpg"), quality=88)
            done.append(n)
    sheet([n for n in done if n.startswith("A")], os.path.join(OUT, "Sky2360_Autumn.jpg"))
    sheet([n for n in done if n.startswith("B")], os.path.join(OUT, "Sky2360_Moons.jpg"))
    sheet([n for n in done if n.startswith("C")], os.path.join(OUT, "Sky2360_Events.jpg"))
