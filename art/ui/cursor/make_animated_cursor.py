"""Animated Nightmare Highschool cursor: one 512x512 sprite sheet of 64 px frames (8 x 8).

  rows 0-1  idle  (16)  the crimson gem breathes; a gold glint runs down the rim, then rests
  rows 2-3  hover (16)  the gem turns gold and glows; a four-point spark twinkles at the tip
  row  4    click (8)   a quick press toward the tip and a crimson ink ripple
  rows 5-6  busy  (16)  a ring of eight gold beads turns beside the arrow

The arrow keeps the static cursor's look (ink-black body, gold rim, crimson gem) and adds a dark outer
outline so it reads on bright screens too. Hotspot: the tip, at (14, 12) in every 64 px frame (the margin
leaves room for the click ripple and the hover spark).
Drawn at 4x and averaged down for smooth edges.

  python make_animated_cursor.py            -> NHCursorAnim.png (+ NHCursorAnim_preview.png)
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
F = 64            # frame size
S = 4             # supersampling
TIP = (14.0, 12.0)
# classic pointer, relative to the tip (frame px)
ARROW = [(0, 0), (0, 40), (10, 31), (17, 46), (24, 43), (17, 28), (30, 28)]
GEM = (8.2, 16.5, 3.5)      # cx, cy, r (frame px, relative to the tip)

INK_TOP, INK_BOT = np.array((32, 24, 34), float), np.array((12, 9, 14), float)
GOLD_D, GOLD_L = np.array((122, 86, 30), float), np.array((240, 204, 120), float)
CRIMSON, CRIMSON_L = np.array((150, 14, 30), float), np.array((255, 96, 110), float)
GEM_GOLD, GEM_GOLD_L = np.array((214, 160, 56), float), np.array((255, 236, 170), float)
OUTLINE = np.array((6, 4, 8), float)


def pts(scale=1.0, dx=0.0, dy=0.0):
    tx, ty = TIP
    return [((tx + x * scale + dx) * S, (ty + y * scale + dy) * S) for x, y in ARROW]


def mask_poly(p, width=None):
    m = Image.new("L", (F * S, F * S), 0)
    d = ImageDraw.Draw(m)
    if width is None:
        d.polygon(p, fill=255)
    else:
        d.line(p + [p[0]], fill=255, width=int(width * S), joint="curve")
        for x, y in p:
            r = width * S / 2
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return np.array(m, float) / 255


def mask_circle(cx, cy, r):
    m = Image.new("L", (F * S, F * S), 0)
    ImageDraw.Draw(m).ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=255)
    return np.array(m, float) / 255


def mask_ring(cx, cy, r, w):
    m = Image.new("L", (F * S, F * S), 0)
    ImageDraw.Draw(m).ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=255, width=max(1, int(w * S)))
    return np.array(m, float) / 255


YY, XX = np.mgrid[0:F * S, 0:F * S] / S


def over(rgb, a, col, m):
    """Composite colour col (rgb or HxWx3) through mask m onto (rgb, a)."""
    m = np.clip(m, 0, 1)[..., None]
    col = np.broadcast_to(np.asarray(col, float), rgb.shape)
    rgb[:] = rgb * (1 - m) + col * m
    a[:] = a + (1 - a) * m[..., 0]


def glow(m, sigma):
    from scipy import ndimage
    g = ndimage.gaussian_filter(m, sigma * S)
    return g / (g.max() + 1e-6)


def arrow(rgb, a, scale=1.0, rim_boost=None, gem_col=(CRIMSON, CRIMSON_L), gem_glow=0.0, glow_col=CRIMSON_L):
    p = pts(scale)
    body = mask_poly(p)
    outline = mask_poly(p, width=3.6)
    rim = np.clip(mask_poly(p, width=2.0) - mask_poly([(x, y) for x, y in p], width=0.4) * 0, 0, 1)
    over(rgb, a, OUTLINE, outline * 0.9)
    # gold rim: dark at the bottom, light toward the tip, plus an optional moving glint
    t = np.clip((YY - TIP[1]) / 46.0, 0, 1)[..., None]
    gold = GOLD_L * (1 - t) + GOLD_D * t
    if rim_boost is not None:
        gold = np.clip(gold + rim_boost[..., None] * 140, 0, 255)
    over(rgb, a, gold, rim)
    # ink body with a soft vertical gradient and a faint crimson inner line
    inner = mask_poly(pts(scale * 0.86, dx=1.6 * scale, dy=3.2 * scale))
    ink = INK_TOP * (1 - t) + INK_BOT * t
    over(rgb, a, ink, inner)
    edge = np.clip(inner - mask_poly(pts(scale * 0.80, dx=2.2 * scale, dy=4.4 * scale)), 0, 1)
    over(rgb, a, CRIMSON * 0.7, edge * 0.55)
    # the gem
    gx, gy, gr = TIP[0] + GEM[0] * scale, TIP[1] + GEM[1] * scale, GEM[2] * scale
    if gem_glow > 0:
        halo = glow(mask_circle(gx, gy, gr), 2.4)
        over(rgb, a, glow_col, halo * gem_glow)
    gm = mask_circle(gx, gy, gr)
    d = np.clip(np.hypot(XX - (gx - gr * 0.35), YY - (gy - gr * 0.35)) / (gr * 1.4), 0, 1)[..., None]
    over(rgb, a, gem_col[1] * (1 - d) + gem_col[0] * d, gm)
    over(rgb, a, OUTLINE, np.clip(mask_ring(gx, gy, gr, 0.7), 0, 1) * 0.8)
    over(rgb, a, (255, 245, 240), mask_circle(gx - gr * 0.38, gy - gr * 0.42, gr * 0.28) * 0.9)
    return rim


def spark(rgb, a, cx, cy, size, rot, alpha):
    if alpha <= 0:
        return
    m = Image.new("L", (F * S, F * S), 0)
    d = ImageDraw.Draw(m)
    for k in range(4):
        ang = rot + k * math.pi / 2
        x1, y1 = cx + math.cos(ang) * size, cy + math.sin(ang) * size
        lx, ly = cx + math.cos(ang + math.pi / 2) * size * 0.22, cy + math.sin(ang + math.pi / 2) * size * 0.22
        rx, ry = cx + math.cos(ang - math.pi / 2) * size * 0.22, cy + math.sin(ang - math.pi / 2) * size * 0.22
        d.polygon([(x1 * S, y1 * S), (lx * S, ly * S), (rx * S, ry * S)], fill=255)
    sm = np.array(m, float) / 255
    over(rgb, a, GEM_GOLD_L, glow(sm, 1.2) * 0.6 * alpha)
    over(rgb, a, (255, 250, 230), sm * alpha)


def frame(kind, i, n):
    rgb = np.zeros((F * S, F * S, 3))
    a = np.zeros((F * S, F * S))
    t = i / n
    if kind == "idle":
        breathe = 0.5 + 0.5 * math.sin(2 * math.pi * t)
        # glint sweeps down the rim during the first 40% of the loop, then rests
        g = None
        if t < 0.4:
            s = -10 + (t / 0.4) * 90
            g = np.exp(-(((XX + YY * 0.55) - s) / 4.0) ** 2)
        arrow(rgb, a, rim_boost=g, gem_glow=0.25 + 0.45 * breathe)
    elif kind == "hover":
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t)
        g = np.exp(-(((XX + YY * 0.55) - (-10 + t * 90)) / 5.0) ** 2) * 0.6
        arrow(rgb, a, rim_boost=g, gem_col=(GEM_GOLD, GEM_GOLD_L), gem_glow=0.55 + 0.35 * pulse, glow_col=GEM_GOLD_L)
        spark(rgb, a, TIP[0] - 0.5, TIP[1] - 0.5, 3.0 + 2.2 * pulse, t * math.pi, 0.55 + 0.45 * pulse)
    elif kind == "click":
        k = i / (n - 1)
        press = 1 - 0.12 * math.sin(min(1, k * 2.2) * math.pi)
        rr = 2.5 + k * 10.5
        ring = mask_ring(TIP[0], TIP[1], rr, 2.2 * (1 - k) + 0.6)
        over(rgb, a, CRIMSON_L, glow(ring, 0.6) * (1 - k) * 0.6)
        over(rgb, a, CRIMSON, ring * (1 - k))
        arrow(rgb, a, scale=press, gem_glow=0.7 * (1 - k), glow_col=CRIMSON_L)
    elif kind == "busy":
        arrow(rgb, a, gem_glow=0.35)
        cx, cy, R = TIP[0] + 31, TIP[1] + 40, 7.0
        for b in range(8):
            ang = 2 * math.pi * (b / 8 + t)
            lead = (b / 8) % 1.0
            bright = 0.25 + 0.75 * lead
            bx, by = cx + math.cos(ang) * R, cy + math.sin(ang) * R
            over(rgb, a, OUTLINE, mask_circle(bx, by, 2.4) * 0.9)
            over(rgb, a, GOLD_D * (1 - bright) + GOLD_L * bright, mask_circle(bx, by, 1.8))
    # premultiplied composite -> straight alpha, downsample
    out = np.zeros((F * S, F * S, 4))
    out[..., :3] = rgb
    out[..., 3] = a * 255
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    # average in premultiplied space so edges don't fringe
    pm = np.array(img, float)
    pm[..., :3] *= pm[..., 3:4] / 255
    small = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize((F, F), Image.BOX)
    sm = np.array(small, float)
    al = np.maximum(sm[..., 3:4], 1)
    sm[..., :3] = np.clip(sm[..., :3] * 255 / al, 0, 255)
    return Image.fromarray(sm.astype(np.uint8), "RGBA")


LAYOUT = [("idle", 16, 0), ("hover", 16, 2), ("click", 8, 4), ("busy", 16, 5)]


def build():
    sheet = Image.new("RGBA", (F * 8, F * 8), (0, 0, 0, 0))
    for kind, n, row in LAYOUT:
        for i in range(n):
            fr = frame(kind, i, n)
            sheet.paste(fr, ((i % 8) * F, (row + i // 8) * F))
    out = HERE / "NHCursorAnim.png"
    sheet.save(out, optimize=True)
    # preview on light and dark backgrounds
    pv = Image.new("RGBA", (F * 8 * 2 + 20, F * 8), (30, 26, 34, 255))
    light = Image.new("RGBA", (F * 8, F * 8), (226, 222, 214, 255))
    light.alpha_composite(sheet)
    dark = Image.new("RGBA", (F * 8, F * 8), (24, 20, 28, 255))
    dark.alpha_composite(sheet)
    pv.paste(dark, (0, 0))
    pv.paste(light, (F * 8 + 20, 0))
    pv.save(HERE / "NHCursorAnim_preview.png")
    return out


if __name__ == "__main__":
    print(build())
