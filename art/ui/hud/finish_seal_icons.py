"""The seal-replacement icon set, stage 3 of 3: finish the Blender renders and write the upload folder.

- straight alpha with the colour bled out under the clear pixels (no dark fringes when Roblox filters them)
- resized with premultiplied alpha to each piece's game size
- "grey" pieces (the grade seal and the Hex Slash altar, which the game tints) become luminance, brightest at white
- writes art/group-upload-icons/NHIcon<Name>.png and out/seal_icons/contact.png

    python finish_seal_icons.py
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE / "out" / "seal_icons"
RENDER, MAPS, FINAL = ROOT / "render", ROOT / "maps", ROOT / "final"
FINAL.mkdir(parents=True, exist_ok=True)
UPLOAD = HERE.parents[1] / "group-upload-icons"
UPLOAD.mkdir(parents=True, exist_ok=True)
f32 = np.float32


# (bleed and resize_premul as in finish_training_ui.py)
def bleed(rgba, iters=24):
    """push colour outward from opaque pixels into transparent ones (alpha unchanged)"""
    rgb, a = rgba[..., :3].copy(), rgba[..., 3]
    known = a > 0.5
    acc_rgb = rgb * known[..., None]
    w = known.astype(f32)
    for _ in range(iters):
        if known.all():
            break
        s_rgb = ndimage.uniform_filter(acc_rgb, size=(3, 3, 1))
        s_w = ndimage.uniform_filter(w, size=3)
        grow = (~known) & (s_w > 1e-4)
        rgb[grow] = s_rgb[grow] / s_w[grow][:, None]
        known = known | grow
        acc_rgb = rgb * known[..., None]
        w = known.astype(f32)
    # semi-transparent edge pixels keep their own colour if they had enough coverage
    edge = (a > 0.02) & (a <= 0.5)
    mix = np.clip(a[edge] * 2, 0, 1)[:, None]
    rgb[edge] = rgba[..., :3][edge] * mix + rgb[edge] * (1 - mix)
    return np.dstack([rgb, a])


def resize_premul(rgba, size):
    pm = np.dstack([rgba[..., :3] * rgba[..., 3:4], rgba[..., 3:4]])
    chans = [np.array(Image.fromarray(pm[..., i]).resize(size, Image.LANCZOS), f32) for i in range(4)]
    out = np.dstack(chans)
    a = np.clip(out[..., 3], 0, 1)
    rgb = np.where(a[..., None] > 1e-4, out[..., :3] / np.maximum(a[..., None], 1e-4), 0)
    return np.dstack([np.clip(rgb, 0, 1), a])


def to_grey(rgba):
    lum = rgba[..., 0] * 0.2126 + rgba[..., 1] * 0.7152 + rgba[..., 2] * 0.0722
    a = rgba[..., 3]
    top = np.percentile(lum[a > 0.6], 99.5) if (a > 0.6).any() else 1.0
    lum = np.clip(lum / max(top, 1e-3), 0, 1)
    return np.dstack([lum, lum, lum, a])


def main():
    pieces = json.loads((MAPS / "pieces.json").read_text())
    done = []
    for info in pieces:
        n = info["name"]
        src = RENDER / f"{n}.png"
        if not src.exists():
            print("   missing render", n)
            continue
        rgba = np.array(Image.open(src).convert("RGBA"), f32) / 255.0
        if info.get("kind") == "grey":
            rgba = to_grey(rgba)
        rgba = bleed(rgba)
        size = (info["out"], info["out"])
        if size != (rgba.shape[1], rgba.shape[0]):
            rgba = resize_premul(rgba, size)
        rgba = bleed(rgba, 12)
        im = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        im.save(FINAL / f"{n}.png", optimize=True)
        shutil.copy(FINAL / f"{n}.png", UPLOAD / f"NHIcon{n}.png")
        done.append(n)
        print("  ", n, im.size)
    contact(done)


def contact(names):
    cols, cell = 8, 180
    rows = (len(names) + cols - 1) // cols
    im = Image.new("RGBA", (cols * cell, rows * (cell + 22)), (18, 15, 22, 255))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 12)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * (cell + 22)
        d.rounded_rectangle([x + 5, y + 5, x + cell - 5, y + cell - 5], 12, fill=(34, 29, 40, 255))
        p = Image.open(FINAL / f"{n}.png").convert("RGBA")
        p.thumbnail((cell - 24, cell - 24), Image.LANCZOS)
        im.alpha_composite(p, (x + (cell - p.width) // 2, y + (cell - p.height) // 2))
        d.text((x + cell / 2, y + cell + 3), n, font=f, fill=(228, 222, 208, 255), anchor="mt")
    im.save(ROOT / "contact.png")
    # the same set at game size, on the HUD's dark, to judge readability
    small = Image.new("RGBA", (len(names) * 34 + 8, 44), (14, 12, 18, 255))
    for i, n in enumerate(names):
        p = Image.open(FINAL / f"{n}.png").convert("RGBA").resize((28, 28), Image.LANCZOS)
        small.alpha_composite(p, (6 + i * 34, 8))
    small.save(ROOT / "contact_28px.png")
    print("wrote contact.png,", len(names), "pieces")


if __name__ == "__main__":
    main()
