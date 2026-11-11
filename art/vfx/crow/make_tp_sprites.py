"""Sprites for the teleport flocks (system Python: numpy + Pillow).

  python art/vfx/crow/make_tp_sprites.py [out_dir]

  NHTpFeather.png   512 x 512  one loose crow feather (a curved vane, rachis, barbs, a soft edge), dark grey on alpha,
                               tinted in Roblox (ParticleEmitter.Color)
  NHBatSigil.png    1024 x 1024 the owner's ground sigil, white on alpha (tinted crimson by Decal.Color3): two rings
                               of runic ticks, an inner band of original angular glyphs, six bats wheeling between the
                               rings and a crescent moon at the heart, with a soft glow behind every line
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/crow"
os.makedirs(OUT, exist_ok=True)


def feather(size=512):
    S = size
    y, x = np.mgrid[0:S, 0:S].astype(np.float32) / S
    # the feather runs bottom to top, curving a little to the right
    t = 1 - y                                   # 0 at the quill end, 1 at the tip
    cx = 0.5 + 0.06 * np.sin(t * math.pi * 0.9) - 0.03
    d = x - cx                                  # signed distance across
    # vane half-widths: wider on the trailing side, rounded tip, the downy base narrower
    wl = 0.16 * np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1) ** 0.55
    wr = 0.21 * np.clip(np.sin(np.clip(t, 0, 1) * math.pi), 0, 1) ** 0.5
    w = np.where(d < 0, wl, wr)
    inside = (np.abs(d) < w) & (t > 0.10) & (t < 0.97)
    u = np.abs(d) / np.maximum(w, 1e-3)         # 0 at the rachis, 1 at the edge
    barb = 0.5 + 0.5 * np.sin((t * 90 - u * 14 * np.sign(d)) * math.pi)
    # a couple of splits where barbs part
    split = (np.abs(np.sin(t * 17.0 + np.sign(d) * 1.3)) < 0.05) & (u > 0.35)
    edge = np.clip((1 - u) / 0.18, 0, 1)
    a = inside * edge * (0.75 + 0.25 * barb) * (1 - 0.8 * split)
    down = (t > 0.10) & (t < 0.28)              # fluffy afterfeather at the base
    a = np.where(down, a * (0.4 + 0.6 * barb), a)
    rachis = (np.abs(d) < 0.006 + 0.006 * (1 - t)) & (t > 0.0) & (t < 0.95)
    a = np.maximum(a, rachis * 1.0)
    shade = 38 + 30 * (1 - u) * inside + 25 * barb * inside + 60 * rachis
    rgb = np.clip(np.stack([shade, shade, shade * 1.12], axis=2), 0, 255)
    img = np.concatenate([rgb, np.clip(a, 0, 1)[:, :, None] * 255], axis=2).astype(np.uint8)
    im = Image.fromarray(img, "RGBA").filter(ImageFilter.GaussianBlur(0.6))
    p = os.path.join(OUT, "NHTpFeather.png")
    im.save(p)
    return p


def bat_glyph(draw, cx, cy, s, ang):
    """A bat silhouette, wings spread along the local x axis, head toward local -y; turned by ang."""
    ca, sa = math.cos(ang), math.sin(ang)

    def tf(pts):
        return [(cx + (px * ca - py * sa) * s, cy + (px * sa + py * ca) * s) for px, py in pts]
    wing = [(0.08, -0.12), (0.30, -0.30), (0.48, -0.38), (0.70, -0.30), (1.00, -0.20), (0.90, 0.04), (0.80, 0.16),
            (0.72, 0.04), (0.62, 0.10), (0.54, 0.26), (0.44, 0.12), (0.33, 0.16), (0.24, 0.30), (0.15, 0.16), (0.06, 0.20)]
    draw.polygon(tf(wing), fill=255)
    draw.polygon(tf([(-x, y) for x, y in wing]), fill=255)
    body = [(0.11 * math.cos(k / 16 * 2 * math.pi), 0.03 + 0.24 * math.sin(k / 16 * 2 * math.pi)) for k in range(16)]
    draw.polygon(tf(body), fill=255)
    head = [(0.085 * math.cos(k / 12 * 2 * math.pi), -0.22 + 0.08 * math.sin(k / 12 * 2 * math.pi)) for k in range(12)]
    draw.polygon(tf(head), fill=255)
    for sx in (-1, 1):
        draw.polygon(tf([(sx * 0.02, -0.27), (sx * 0.10, -0.42), (sx * 0.085, -0.24)]), fill=255)


def sigil(size=1024):
    S = size
    c = S / 2
    lines = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(lines)

    def ring(r, w):
        d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=w)

    ring(S * 0.485, 10)
    ring(S * 0.455, 4)
    ring(S * 0.36, 5)
    ring(S * 0.335, 3)
    ring(S * 0.20, 4)
    # outer band: runic ticks, every third a long one with a barb
    for k in range(72):
        a = k / 72 * 2 * math.pi
        r0, r1 = S * 0.458, S * (0.482 if k % 3 == 0 else 0.472)
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * r1, c + math.sin(a) * r1)], fill=255,
               width=4 if k % 3 == 0 else 3)
    # inner band: original angular glyphs (not any real script): each a short stem with one or two crossbars
    rnd = np.random.default_rng(11)
    for k in range(28):
        a = k / 28 * 2 * math.pi
        rm = S * 0.348
        tang = (-math.sin(a), math.cos(a))
        rad = (math.cos(a), math.sin(a))
        p0 = (c + rad[0] * (rm - 9), c + rad[1] * (rm - 9))
        p1 = (c + rad[0] * (rm + 9), c + rad[1] * (rm + 9))
        d.line([p0, p1], fill=255, width=3)
        for j in range(int(rnd.integers(1, 3))):
            f = rnd.uniform(-0.6, 0.6)
            q = (c + rad[0] * (rm + f * 9), c + rad[1] * (rm + f * 9))
            L = rnd.uniform(4, 8) * (1 if rnd.random() < 0.5 else -1)
            d.line([q, (q[0] + tang[0] * L + rad[0] * 3, q[1] + tang[1] * L + rad[1] * 3)], fill=255, width=3)
    # six bats wheeling between the rings, nose to tail round the circle
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.26
        r = S * 0.275
        bat_glyph(d, c + math.cos(a) * r, c + math.sin(a) * r, S * 0.075, a + math.pi / 2)
    # spokes between the inner ring and the bats' ring
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line([(c + math.cos(a) * S * 0.205, c + math.sin(a) * S * 0.205), (c + math.cos(a) * S * 0.225, c + math.sin(a) * S * 0.225)],
               fill=255, width=4)
    # the crescent moon at the heart
    moon = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(moon)
    R = S * 0.13
    md.ellipse([c - R, c - R, c + R, c + R], fill=255)
    md.ellipse([c - R + R * 0.45, c - R - R * 0.18, c + R + R * 0.45, c + R - R * 0.18], fill=0)
    lines = Image.fromarray(np.maximum(np.array(lines), np.array(moon)))
    a = np.array(lines, dtype=np.float32) / 255
    glow = np.array(lines.filter(ImageFilter.GaussianBlur(10)), dtype=np.float32) / 255
    halo = np.array(lines.filter(ImageFilter.GaussianBlur(28)), dtype=np.float32) / 255
    alpha = np.clip(a + glow * 0.9 + halo * 0.5, 0, 1)
    # a faint wash inside the outer ring so the sigil reads on any floor
    yy, xx = np.mgrid[0:S, 0:S]
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (S * 0.49)
    wash = np.clip(1 - rr, 0, 1) ** 0.6 * 0.10 * (rr < 1)
    alpha = np.clip(alpha + wash, 0, 1)
    # soft outer fade so no edge of the decal shows
    alpha *= np.clip((1.02 - rr) / 0.04, 0, 1)
    rgb = np.full((S, S, 3), 255, dtype=np.float32)
    img = np.concatenate([rgb, alpha[:, :, None] * 255], axis=2).astype(np.uint8)
    p = os.path.join(OUT, "NHBatSigil.png")
    Image.fromarray(img, "RGBA").save(p)
    return p


if __name__ == "__main__":
    print(feather())
    print(sigil())
