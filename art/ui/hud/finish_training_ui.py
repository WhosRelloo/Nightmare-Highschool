"""Training HUD art, stage 3 of 3: finish the Blender renders for the game and write the upload folder.

- straight alpha, with the colour bled out under the clear pixels (so Roblox's filtering never shows a dark fringe)
- resized with premultiplied alpha (no dark halos), to each piece's game size
- the rings get a soft candle halo; the animated extras are made here (they are pure light, no surfaces to light):
    TrainFlame.png     1024  a 4 x 4 flipbook (256 px frames) of a candle flame, flickering (the combo and streak flame)
    TrainBarFill.png   512 x 64  molten brass, tiling across (the next-change bar's pour; the HUD scrolls it)
    TrainMarkGlow.png  512  the mark's glow band (from make_training_ui.py)
- writes art/group-upload-training/ (only the files the game uses) and out/training/contact_pbr.png

    python finish_training_ui.py
"""
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = Path(__file__).resolve().parent
TR = HERE / "out" / "training"
RENDER, MAPS, FINAL = TR / "render", TR / "maps", TR / "final"
FINAL.mkdir(parents=True, exist_ok=True)
UPLOAD = HERE.parents[1] / "group-upload-training"
f32 = np.float32


def load_straight(path):
    im = Image.open(path)
    a = np.array(im.convert("RGBA"), f32) / 255.0
    if im.mode in ("I;16", "I;16B", "RGBA;16"):
        pass
    return a


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


def save(rgba, name):
    rgba = bleed(rgba, 12)
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    im.save(FINAL / f"{name}.png", optimize=True)
    shutil.copy(FINAL / f"{name}.png", UPLOAD / f"{name}.png")
    print("  ", name, im.size)


def halo(rgba, color, strength=0.55, sigma=14):
    a = rgba[..., 3]
    g = ndimage.gaussian_filter(a, sigma) * strength
    col = np.array(color, f32) / 255.0
    out_a = np.clip(a + g * (1 - a), 0, 1)
    rgb = (rgba[..., :3] * a[..., None] + col * (g * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([rgb, out_a])


def flame_sheet():
    N, S = 4, 256
    sheet = np.zeros((N * S, N * S, 4), f32)
    yy, xx = np.mgrid[0:S, 0:S].astype(f32)
    rng = np.random.default_rng(5)
    base = ndimage.gaussian_filter(rng.random((S * 2, S)).astype(f32), 9, mode="wrap")
    base = (base - base.min()) / (base.max() - base.min())
    for k in range(N * N):
        ph = k / (N * N) * 2 * math.pi
        # a teardrop, swaying and stretching with smooth noise, scrolling turbulence up through it
        sway = 7 * math.sin(ph) + 3 * math.sin(2 * ph + 1.3)
        tall = 1.0 + 0.10 * math.sin(ph * 2 + 0.7) + 0.05 * math.sin(ph * 3)
        v = (yy - 236) / (-190 * tall)            # 0 at the wick, 1 at the tip
        bend = sway * np.clip(v, 0, 1) ** 1.6
        u = (xx - 128 - bend) / 62
        width = np.clip(np.clip(np.sin(np.clip(v, 0, 1) * math.pi), 0, 1) ** 0.8 * (1 - 0.55 * np.clip(v, 0, 1)), 0, 1) + 0.0001
        shift = int(k / (N * N) * S * 2)
        turb = np.roll(base, -shift, axis=0)[:S]
        turb = ndimage.map_coordinates(turb, [yy, xx], order=1, mode="wrap")
        d = np.abs(u) / width + (turb - 0.5) * 0.45 * np.clip(v, 0, 1)
        body = np.clip(1 - d, 0, 1) * (v > -0.06) * (v < 1.05)
        body = body ** 0.7 * np.clip((1.05 - v) * 6, 0, 1) * np.clip((v + 0.06) * 12, 0, 1)
        core = np.clip(1 - np.hypot(u * 1.8, (v - 0.22) * 3.2), 0, 1) ** 1.5
        hot = np.clip(body * 0.85 + core * 0.6, 0, 1)
        r = np.clip(0.95 + 0.05 * hot, 0, 1)
        g = np.clip(0.38 + 0.55 * hot ** 1.2, 0, 1)
        b = np.clip(0.10 + 0.55 * core ** 2, 0, 1)
        blue = np.clip(1 - np.hypot(u * 2.2, (v - 0.03) * 9), 0, 1) * 0.5     # the blue root at the wick
        rgb = np.dstack([r * (1 - blue) + 0.45 * blue, g * (1 - blue) + 0.55 * blue, b * (1 - blue) + 0.95 * blue])
        a = np.clip(body * 1.15, 0, 1)
        gl = ndimage.gaussian_filter(a, 18) * 0.5
        a2 = np.clip(a + gl * (1 - a), 0, 1)
        rgb = (rgb * a[..., None] + np.array([1.0, 0.55, 0.2], f32) * (gl * (1 - a))[..., None]) / np.maximum(a2[..., None], 1e-4)
        y0, x0 = (k // N) * S, (k % N) * S
        sheet[y0:y0 + S, x0:x0 + S] = np.dstack([rgb, a2])
    save(sheet, "TrainFlame")


def bar_fill():
    W, Hh = 512, 64
    yy, xx = np.mgrid[0:Hh, 0:W].astype(f32)
    rng = np.random.default_rng(9)
    n = ndimage.gaussian_filter(rng.random((Hh, W)).astype(f32), (3, 22), mode="wrap")
    n = (n - n.min()) / (n.max() - n.min())
    streak = 0.5 + 0.5 * np.sin(xx / W * 2 * math.pi * 3 + n * 5)
    v = (yy - Hh / 2) / (Hh / 2)
    lens = np.clip(1 - v ** 2, 0, 1)              # a rounded, poured top
    heat = np.clip(0.35 + 0.45 * streak + 0.25 * n, 0, 1) * (0.55 + 0.45 * lens)
    hi = np.clip(1 - np.abs(v + 0.45) / 0.18, 0, 1) * 0.6          # the glossy skin
    r = np.clip(0.55 + 0.45 * heat + hi * 0.3, 0, 1)
    g = np.clip(0.28 + 0.52 * heat ** 1.3 + hi * 0.35, 0, 1)
    b = np.clip(0.06 + 0.25 * heat ** 3 + hi * 0.3, 0, 1)
    save(np.dstack([r, g, b, np.ones_like(r)]), "TrainBarFill")


def main():
    pieces = json.loads((MAPS / "pieces.json").read_text())
    for info in pieces:
        n = info["name"]
        src = RENDER / f"{n}.png"
        if not src.exists():
            print("   missing render", n)
            continue
        rgba = load_straight(src)
        if info["kind"] == "ring" and info.get("halo"):
            rgba = halo(rgba, info["halo"], 0.5, 12)
        out = info["out"]
        size = tuple(out) if isinstance(out, list) else (out, out)
        rgba = bleed(rgba)
        if size != (rgba.shape[1], rgba.shape[0]):
            rgba = resize_premul(rgba, size)
        save(rgba, n)
    shutil.copy(TR / "TrainMarkGlow.png", FINAL / "TrainMarkGlow.png")
    shutil.copy(TR / "TrainMarkGlow.png", UPLOAD / "TrainMarkGlow.png")
    flame_sheet()
    bar_fill()
    # only the final set in the upload folder
    keep = {p.name for p in FINAL.glob("*.png")}
    for p in UPLOAD.glob("*.png"):
        if p.name not in keep:
            p.unlink()
            print("   removed stale", p.name)
    contact()


def contact():
    names = sorted(p.stem for p in FINAL.glob("*.png"))
    cols, cell = 6, 200
    rows = (len(names) + cols - 1) // cols
    im = Image.new("RGBA", (cols * cell, rows * (cell + 24)), (18, 15, 22, 255))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 13)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * (cell + 24)
        d.rounded_rectangle([x + 6, y + 6, x + cell - 6, y + cell - 6], 12, fill=(34, 29, 40, 255))
        p = Image.open(FINAL / f"{n}.png").convert("RGBA")
        p.thumbnail((cell - 24, cell - 24), Image.LANCZOS)
        im.alpha_composite(p, (x + (cell - p.width) // 2, y + (cell - p.height) // 2))
        d.text((x + cell / 2, y + cell + 4), n.replace("Train", ""), font=f, fill=(228, 222, 208, 255), anchor="mt")
    im.save(TR / "contact_pbr.png")
    print("wrote contact_pbr.png")


if __name__ == "__main__":
    main()
