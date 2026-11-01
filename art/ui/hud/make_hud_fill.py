"""HUD fill + crack overlays (numpy + Pillow). Greyscale/white so Roblox tints them per bar.

usage: python art/ui/hud/make_hud_fill.py
  out/hud_fill.png    512x64   seamless leather with stitched chevrons (scrolls sideways in the bar = animated)
  out/hud_cracks.png  2400x360 branching ink cracks spreading in from both ends (pulses in at low health)
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def fill():
    W, H = 512, 64
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(3)
    # leather grain (periodic noise)
    g = np.zeros((H, W), np.float32)
    for k, amp in ((8, 0.5), (16, 0.3), (32, 0.2)):
        ph = rng.uniform(0, math.tau, 4)
        g += amp * (np.sin(xx / W * math.tau * k + ph[0]) * np.sin(yy / H * math.tau * (k // 4 or 1) + ph[1]))
    g = (g - g.min()) / (g.max() - g.min())
    # chevrons: period 64 px across, pointing right
    period = 64
    u = ((xx + np.abs(yy - H / 2) * 1.0) % period) / period
    stripe = np.clip(1 - np.abs(u - 0.5) * 6, 0, 1)        # embossed chevron ridge
    stitch = ((xx.astype(int) + np.abs(yy - H / 2).astype(int)) % period < 3) & ((yy.astype(int) % 6) < 3)
    lum = 0.62 + 0.18 * g - 0.22 * stripe + 0.18 * (1 - u) * 0.3
    lum = np.where(stitch, 0.95, lum)
    # rounded top light, darker bottom (the tube reads as round)
    shade = 0.75 + 0.35 * np.cos((yy / H - 0.38) * math.pi)
    lum = np.clip(lum * shade, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = (lum * 255).astype(np.uint8)
    rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "hud_fill.png"))


def cracks():
    W, H = 2400, 360
    img = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(img)
    rng = random.Random(9)

    def branch(x, y, ang, length, width, depth):
        pts = [(x, y)]
        for _ in range(int(length / 14)):
            ang += rng.uniform(-0.45, 0.45)
            x += math.cos(ang) * 14
            y += math.sin(ang) * 14
            pts.append((x, y))
            if depth > 0 and rng.random() < 0.08:
                branch(x, y, ang + rng.choice((-1, 1)) * rng.uniform(0.6, 1.2), length * 0.45, max(1, width * 0.6), depth - 1)
        for i in range(len(pts) - 1):
            w = max(1, int(width * (1 - i / len(pts))))
            d.line([pts[i], pts[i + 1]], fill=255, width=w)

    for side in (0, 1):
        x0 = 120 if side == 0 else W * 2 - 120
        for k in range(9):
            y0 = H + rng.uniform(-H * 0.5, H * 0.5)
            ang = (0 if side == 0 else math.pi) + rng.uniform(-1.1, 1.1)
            branch(x0, y0, ang, rng.uniform(260, 620), rng.uniform(5, 9), 3)
    glow = img.filter(ImageFilter.GaussianBlur(10))
    a = np.clip(np.asarray(img, np.float32) / 255 + np.asarray(glow, np.float32) / 255 * 0.9, 0, 1)
    rgba = np.zeros(a.shape + (4,), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "hud_cracks.png"))


fill()
cracks()
print("done")
