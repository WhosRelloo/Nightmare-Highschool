"""Tier-up (evolution) VFX sprites for Nightmare Highschool (numpy + Pillow, no Blender needed).

usage: python make_evolve_sprites.py [outdir]   (default: art/vfx/evolve/sprites)

White / greyscale art on transparent backgrounds (tinted per race in Roblox), drawn at 2x and downsampled,
every edge fading to zero alpha before the image edge (style guide: soft-edge pass).
  evo_sigil_<Race>.png   1024  the ground sigil circle for each race (rings, rune band, race motif, soft glow)
  evo_claws.png          512   three ragged claw slashes (Werewolf)
  evo_streak.png         256x64  a hot spark streak, for velocity-aligned particles
  evo_spore.png          128   a soft bokeh spore (Ghoul) / mote
  evo_frost_2x2.png      512   four six-fold frost crystals (Wraith), Grid2x2 flipbook
  evo_godray.png         256x1024  a soft vertical light shaft for Beams (Priest, Human)
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "sprites")
os.makedirs(OUT, exist_ok=True)


def finish(line_img: Image.Image, size, glow=6, glow_gain=0.9, core_gain=1.0, vignette=True):
    """line art (L, 2x) -> RGBA white sprite with a soft glow, downsampled to `size`."""
    a = np.asarray(line_img, dtype=np.float32) / 255.0
    g1 = np.asarray(line_img.filter(ImageFilter.GaussianBlur(glow)), dtype=np.float32) / 255.0
    g2 = np.asarray(line_img.filter(ImageFilter.GaussianBlur(glow * 3)), dtype=np.float32) / 255.0
    alpha = np.clip(a * core_gain + g1 * glow_gain * 1.4 + g2 * glow_gain * 0.9, 0, 1)
    if vignette:
        h, w = alpha.shape
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        alpha *= np.clip((1.0 - r) / 0.06, 0, 1)
    rgba = np.zeros(alpha.shape + (4,), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (alpha * 255).astype(np.uint8)
    im = Image.fromarray(rgba, "RGBA")
    return im.resize(size, Image.LANCZOS)


# ------------------------------------------------------------------ sigils

def polar(c, r, a):
    return (c + math.cos(a) * r, c + math.sin(a) * r)


def ring(d, c, r, w):
    d.ellipse((c - r, c - r, c + r, c + r), outline=255, width=w)


def ticks(d, c, r0, r1, n, w, every=1, long_extra=0):
    for i in range(n):
        a = i / n * math.tau
        e = long_extra if i % every == 0 else 0
        d.line([polar(c, r0 - e, a), polar(c, r1, a)], fill=255, width=w)


def rune_band(d, c, r_in, r_out, n, w, seed):
    """A band of procedural runes: each cell gets 2-4 strokes on a 3x3 lattice."""
    rng = random.Random(seed)
    for i in range(n):
        a0 = (i + 0.15) / n * math.tau
        a1 = (i + 0.85) / n * math.tau
        pts = []
        for gy in range(3):
            for gx in range(3):
                a = a0 + (a1 - a0) * gx / 2
                r = r_in + (r_out - r_in) * gy / 2
                pts.append(polar(c, r, a))
        for _ in range(rng.randint(2, 4)):
            p, q = rng.sample(range(9), 2)
            d.line([pts[p], pts[q]], fill=255, width=w)
        if rng.random() < 0.35:
            p = pts[rng.randrange(9)]
            d.ellipse((p[0] - w * 1.5, p[1] - w * 1.5, p[0] + w * 1.5, p[1] + w * 1.5), fill=255)


def base_sigil(d, c, R, seed, runes=24):
    ring(d, c, R * 0.97, 10)
    ring(d, c, R * 0.92, 4)
    ticks(d, c, R * 0.86, R * 0.91, 96, 3, every=8, long_extra=R * 0.025)
    rune_band(d, c, R * 0.72, R * 0.83, runes, 5, seed)
    ring(d, c, R * 0.69, 6)


def star(d, c, r, points, step, w, rot=0.0):
    pts = [polar(c, r, rot + i / points * math.tau) for i in range(points)]
    for i in range(points):
        d.line([pts[i], pts[(i + step) % points]], fill=255, width=w)


def drop(d, cx, cy, s, ang):
    """a blood drop pointing outward along ang"""
    pts = []
    for k in range(40):
        t = k / 39 * math.tau
        x = math.sin(t) * s * (1 - math.cos(t)) * 0.5
        y = -math.cos(t) * s
        rx = x * math.cos(ang) - y * math.sin(ang)
        ry = x * math.sin(ang) + y * math.cos(ang)
        pts.append((cx + rx, cy + ry))
    d.polygon(pts, fill=255)


def sigil(race, N=2048):
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    c = N / 2
    R = N * 0.47
    seed = sum(map(ord, race))
    base_sigil(d, c, R, seed)
    if race == "Vampire":
        star(d, c, R * 0.66, 8, 3, 6, rot=math.pi / 8)
        ring(d, c, R * 0.36, 5)
        for i in range(4):
            a = i / 4 * math.tau - math.pi / 2
            x, y = polar(c, R * 0.52, a)
            drop(d, x, y, R * 0.07, a + math.pi)
        # a pair of fangs under an arched lip
        d.arc((c - R * 0.2, c - R * 0.22, c + R * 0.2, c + R * 0.06), 200, 340, fill=255, width=7)
        for sgn in (-1, 1):
            x = c + sgn * R * 0.1
            d.polygon([(x - R * 0.045, c - R * 0.12), (x + R * 0.045, c - R * 0.12), (x + sgn * R * 0.01, c + R * 0.16)], fill=255)
    elif race == "Werewolf":
        for i in range(12):  # moon phases
            a = i / 12 * math.tau - math.pi / 2
            x, y = polar(c, R * 0.57, a)
            r = R * 0.06
            d.ellipse((x - r, y - r, x + r, y + r), outline=255, width=4)
            ph = math.cos(i / 12 * math.tau)
            d.ellipse((x - r * abs(ph), y - r, x + r * abs(ph), y + r), fill=255 if ph > 0 else 0, outline=255, width=3)
        ring(d, c, R * 0.46, 5)
        for k in (-1, 0, 1):  # claw marks
            off = k * R * 0.1
            d.line([(c + off - R * 0.12, c - R * 0.28), (c + off + R * 0.1, c + R * 0.28)], fill=255, width=14)
    elif race == "Ghoul":
        for i in range(28):  # teeth
            a = i / 28 * math.tau
            p1, p2 = polar(c, R * 0.66, a - 0.07), polar(c, R * 0.66, a + 0.07)
            tip = polar(c, R * 0.53, a)
            d.polygon([p1, p2, tip], outline=255, fill=0)
            d.line([p1, tip, p2], fill=255, width=4)
        star(d, c, R * 0.44, 6, 2, 6)
        ring(d, c, R * 0.18, 6)
        d.ellipse((c - R * 0.05, c - R * 0.05, c + R * 0.05, c + R * 0.05), fill=255)
    elif race == "Wraith":
        for arm in range(3):  # triple spiral
            pts = []
            for k in range(260):
                t = k / 259
                a = arm / 3 * math.tau + t * math.tau * 1.4
                r = R * (0.05 + 0.58 * t)
                pts.append(polar(c, r, a))
            d.line(pts, fill=255, width=7, joint="curve")
        for i in range(9):
            a = i / 9 * math.tau
            x, y = polar(c, R * 0.6, a)
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=255)
    elif race == "Human":
        for i in range(8):  # compass rose
            a = i / 8 * math.tau - math.pi / 2
            L = R * (0.64 if i % 2 == 0 else 0.4)
            w = R * (0.07 if i % 2 == 0 else 0.05)
            tip = polar(c, L, a)
            l1 = polar(c, w, a - math.pi / 2)
            l2 = polar(c, w, a + math.pi / 2)
            d.polygon([l1, tip, l2], outline=255)
            d.line([l1, tip, l2], fill=255, width=6)
            d.line([(c, c), tip], fill=255, width=3)
        ring(d, c, R * 0.3, 5)
        ring(d, c, R * 0.12, 8)
    elif race == "Priest":
        for i in range(36):  # sunburst
            a = i / 36 * math.tau
            r0, r1 = R * 0.3, R * (0.66 if i % 3 == 0 else 0.55)
            d.line([polar(c, r0, a), polar(c, r1, a)], fill=255, width=7 if i % 3 == 0 else 3)
        ring(d, c, R * 0.28, 6)
        w = R * 0.045
        d.rectangle((c - w, c - R * 0.22, c + w, c + R * 0.22), fill=255)
        d.rectangle((c - R * 0.14, c - R * 0.1 - w, c + R * 0.14, c - R * 0.1 + w), fill=255)
    return finish(img, (1024, 1024), glow=7, glow_gain=0.75)


# ------------------------------------------------------------------ other sprites

def claws():
    N = 1024
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    rng = random.Random(3)
    for k in range(3):
        x0 = N * (0.3 + k * 0.18)
        pts_l, pts_r = [], []
        for i in range(60):
            t = i / 59
            x = x0 + (t - 0.5) * N * 0.22 + math.sin(t * 3) * 10
            y = N * 0.12 + t * N * 0.76
            w = math.sin(t * math.pi) ** 0.8 * N * 0.03 * (1 + rng.uniform(-0.25, 0.25))
            pts_l.append((x - w, y))
            pts_r.append((x + w, y))
        d.polygon(pts_l + pts_r[::-1], fill=255)
    return finish(img, (512, 512), glow=10, glow_gain=0.7)


def streak():
    W, H = 512, 128
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = xx / W
    y = (yy - H / 2) / (H / 2)
    body = np.exp(-(y ** 2) / (0.02 + 0.06 * x)) * np.clip(x * 1.2, 0, 1) * np.clip((1 - x) / 0.08, 0, 1)
    head = np.exp(-(((x - 0.9) / 0.06) ** 2 + (y / 0.25) ** 2))
    a = np.clip(body * 0.85 + head, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").resize((256, 64), Image.LANCZOS)


def spore():
    N = 256
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    r = np.hypot(xx - N / 2, yy - N / 2) / (N / 2)
    disc = np.clip((0.78 - r) / 0.06, 0, 1) * 0.35
    rim = np.exp(-((r - 0.74) / 0.05) ** 2) * 0.75
    core = np.exp(-(r / 0.25) ** 2) * 0.5
    a = np.clip(disc + rim + core, 0, 1) * np.clip((1 - r) / 0.12, 0, 1)
    rgba = np.zeros((N, N, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").resize((128, 128), Image.LANCZOS)


def frost():
    N = 1024
    sheet = Image.new("L", (N, N), 0)
    for cell in range(4):
        cx = (cell % 2) * N / 2 + N / 4
        cy = (cell // 2) * N / 2 + N / 4
        d = ImageDraw.Draw(sheet)
        rng = random.Random(40 + cell)
        L = N * 0.2
        for arm in range(6):
            a = arm / 6 * math.tau + cell * 0.2
            tip = (cx + math.cos(a) * L, cy + math.sin(a) * L)
            d.line([(cx, cy), tip], fill=255, width=7)
            for b in range(1, 4):
                t = b / 4
                bx, by = cx + math.cos(a) * L * t, cy + math.sin(a) * L * t
                bl = L * (0.32 - t * 0.06) * rng.uniform(0.7, 1.1)
                for s in (-1, 1):
                    ba = a + s * math.radians(55)
                    d.line([(bx, by), (bx + math.cos(ba) * bl, by + math.sin(ba) * bl)], fill=255, width=5)
        d.regular_polygon((cx, cy, L * 0.18), 6, outline=255, width=5)
    # glow per cell, and fade inside each cell
    im = finish(sheet, (512, 512), glow=6, glow_gain=0.6, vignette=False)
    a = np.asarray(im).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cxg = (xx % (w // 2)) - w / 4
    cyg = (yy % (h // 2)) - h / 4
    r = np.hypot(cxg, cyg) / (w / 4)
    a[..., 3] = (a[..., 3] * np.clip((1 - r) / 0.12, 0, 1)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def godray():
    W, H = 256, 1024
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xx - W / 2) / (W / 2)
    y = yy / H
    rng = np.random.default_rng(5)
    streaks = np.zeros(W, np.float32)
    for _ in range(14):
        c = rng.uniform(-0.7, 0.7)
        s = rng.uniform(0.03, 0.12)
        streaks += np.exp(-((x[0] - c) / s) ** 2) * rng.uniform(0.3, 1.0)
    streaks /= streaks.max()
    shaft = np.exp(-(x / 0.55) ** 2) * (0.55 + 0.45 * streaks[None, :])
    fade = np.clip(y / 0.12, 0, 1) * np.clip((1 - y) / 0.45, 0, 1)
    a = np.clip(shaft * fade, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    for race in ("Vampire", "Werewolf", "Ghoul", "Wraith", "Human", "Priest"):
        sigil(race).save(os.path.join(OUT, f"evo_sigil_{race}.png"))
        print("sigil", race)
    claws().save(os.path.join(OUT, "evo_claws.png"))
    streak().save(os.path.join(OUT, "evo_streak.png"))
    spore().save(os.path.join(OUT, "evo_spore.png"))
    frost().save(os.path.join(OUT, "evo_frost_2x2.png"))
    godray().save(os.path.join(OUT, "evo_godray.png"))
    print("done", OUT)
