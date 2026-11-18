"""PBR art for Night FM (Nightmare Highschool 2.30), baked to images.

Owner (2026-11-18): remake the Night FM app "more like this [a Spotify-style home / library / now playing] but with our
theme", then "make the app design wayy higher quality and create UNIQUE designs that fit the app ... PBR textures, easy
to read text/icons/symbols", and "try not to use that seal icon anymore".

The look, "The Midnight Wireless": a 1920s gothic radio set in the school's dress. Black amethyst lacquer, hammered
gilt-brass bezels and rims, glowing amethyst enamel for whatever is active, and bold embossed icons cut for this app
(thick strokes, big counters, so they read at phone size). Every cover is a unique painted plate with a lit emblem.

Same pipeline as the kit (make_kit_ui.lit -> make_health_pbr.shade: GGX, a warm key, a cool fill, a candle rim, an
environment reflection, AO from the height).

Pieces (art/ui/hud/out/nightfm/, staged to art/group-upload-nightfm/):
  FmBackdrop.png      720x1440  the app's wall: amethyst-black lacquer, a violet glow at the top, faint gilt deco rays
  FmCard.png           192      9-slice card (slice 44): lacquer with a gilt bevel rim
  FmChip.png / FmChipOn.png  192x64  9-slice pills (slice 30): lacquer with a gilt rim / amethyst enamel, lit
  FmKnob.png / FmKnobOn.png  192  round buttons: a lacquer dome in a hammered gilt bezel / an amethyst cabochon, lit
  FmTabBar.png        512x128   9-slice pill (slice 60): black glass with a gilt rim and a top highlight
  FmOnAir.png         256x72    the ON AIR lamp: crimson enamel with a glow (the text is drawn in game)
  FmBanner.png        1024x480  "Tonight": a bell tower with a wireless mast under the moon, radio rings in the sky
  FmCoverFrame.png     512      a gilt frame for the big cover (the middle clear)
  FmCover01..12.png    512      covers: Crescent, Raven, RoseWindow, Bell, Candle, Key, Rose, Moth, Dial, Organ,
                                Quill, Lantern
  FmIcon<Name>.png     256      white embossed icons (tinted in game): Play, Pause, Prev, Next, Loop, Queue, Heart,
                                HeartFull, Search, Bell, Home, Library, Station, Back, Plus, Volume
  preview_nightfm.png           every piece laid out like the app (for review)

  python make_nightfm_ui.py [backdrop card chips knobs tabbar onair banner frame covers icons preview]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import make_health_pbr as H
import make_kit_ui as K

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "nightfm"
OUT.mkdir(parents=True, exist_ok=True)
f32 = np.float32
FONT_T = "C:/Windows/Fonts/georgiab.ttf"

LACQUER = np.array([0.075, 0.05, 0.10], f32)
AMETHYST = np.array([0.50, 0.24, 0.86], f32)
AMETHYST_DEEP = np.array([0.22, 0.08, 0.42], f32)
GILT = np.array([0.93, 0.74, 0.36], f32)
CRIMSON = np.array([0.66, 0.08, 0.14], f32)
IRON = np.array([0.13, 0.12, 0.15], f32)


# ================================================================ helpers
def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), "RGBA")
    img.save(OUT / name, optimize=True)
    print("  ", name, img.size)
    return img


def rrect(w, h, r, inset=0):
    return K.mask((w, h), lambda d, s: d.rounded_rectangle([inset * s, inset * s, (w - inset) * s - 1, (h - inset) * s - 1], r * s, fill=255))


def ellipse(w, h, inset=0):
    return K.mask((w, h), lambda d, s: d.ellipse([inset * s, inset * s, (w - inset) * s - 1, (h - inset) * s - 1], fill=255))


def bevel(m, px):
    return H.dome(K.inner(m), px)


def gilt_maps(w, h, seed=3):
    """hammered gilt: colour variation, rough 0.22..0.38, a fine hammer-dent height"""
    n = K.noise((h, w), 1.6, seed)
    n2 = K.noise((h, w), 6, seed + 1)
    col = GILT[None, None, :] * (0.82 + 0.28 * n2[..., None])
    rough = 0.22 + 0.16 * n
    dents = (K.noise((h, w), 2.2, seed + 2) - 0.5) * 0.04
    return col.astype(f32), rough.astype(f32), dents.astype(f32)


def lacquer_maps(w, h, base=LACQUER, seed=7):
    n = K.noise((h, w), 30, seed)
    col = base[None, None, :] * (0.85 + 0.35 * n[..., None])
    rough = 0.16 + 0.10 * K.noise((h, w), 2, seed + 1)
    return col.astype(f32), rough.astype(f32)


def comp(dst_rgb, dst_a, src_rgb, src_a):
    """'over' composite of straight-alpha layers"""
    a = src_a + dst_a * (1 - src_a)
    rgb = (src_rgb * src_a[..., None] + dst_rgb * dst_a[..., None] * (1 - src_a[..., None])) / np.maximum(a, 1e-6)[..., None]
    return rgb, a


def glow(m, sigma, color, k=1.0):
    g = ndimage.gaussian_filter(m.astype(f32), sigma)
    g = g / (g.max() + 1e-6)
    return color[None, None, :] * g[..., None] * k, g


# ================================================================ backdrop
def backdrop():
    w, h = 720, 1440
    y, x = K.grid(w, h)
    col, rough = lacquer_maps(w, h, np.array([0.055, 0.035, 0.08], f32), 11)
    velvet = (K.noise((h, w), 0.8, 12) - 0.5) * 0.012
    height = velvet
    # faint gilt art-deco rays from the top centre, engraved
    ang = np.arctan2(x - w / 2, y + 120)
    rays = (np.abs(np.sin(ang * 26)) > 0.985).astype(f32) * K.smooth(0, 1, 1 - y / (h * 0.45)) if hasattr(K, "smooth") else (np.abs(np.sin(ang * 26)) > 0.985).astype(f32) * np.clip(1 - y / (h * 0.45), 0, 1)
    rays = ndimage.gaussian_filter(rays, 0.7)
    height = height - rays * 0.01
    col = col * (1 - rays[..., None] * 0.2) + GILT[None, None, :] * rays[..., None] * 0.35
    metal = rays * 0.8
    rgb = K.lit(height, col, rough, metal, strength=1 / 4)
    # a violet glow at the top, a crimson ember at the bottom
    top = np.exp(-(((x - w * 0.5) / (w * 0.7)) ** 2 + ((y - h * 0.05) / (h * 0.32)) ** 2))
    bot = np.exp(-(((x - w * 0.2) / (w * 0.6)) ** 2 + ((y - h * 1.02) / (h * 0.22)) ** 2))
    rgb = rgb + np.array([0.30, 0.12, 0.55], f32) * top[..., None] * 0.55 + np.array([0.35, 0.04, 0.08], f32) * bot[..., None] * 0.35
    vign = np.clip(1 - 0.55 * (((x - w / 2) / (w * 0.75)) ** 2 + ((y - h / 2) / (h * 0.75)) ** 2), 0.35, 1)
    save(rgb * vign[..., None], np.ones((h, w), f32), "FmBackdrop.png")


# ================================================================ card / chips / tab bar
def framed_pill(w, h, r, fill_col, fill_rough, fill_metal, rim=4, emissive_inner=None, gloss=True, seed=1):
    outer = rrect(w, h, r, 1)
    inn = rrect(w, h, r - rim, rim + 1)
    gcol, grough, dents = gilt_maps(w, h, seed)
    rim_m = np.clip(outer - inn, 0, 1)
    height = bevel(outer, rim + 2) * 0.35 + dents * rim_m - bevel(inn, 3) * 0.05 + bevel(inn, max(6, h // 5)) * 0.10 * inn
    col = gcol * rim_m[..., None] + fill_col * (1 - rim_m[..., None])
    rough = grough * rim_m + fill_rough * (1 - rim_m)
    metal = rim_m * 0.95 + fill_metal * (1 - rim_m)
    em = None
    if emissive_inner is not None:
        em = emissive_inner[None, None, :] * ndimage.gaussian_filter(inn, max(2, h / 6))[..., None] * 0.6
    rgb = K.lit(height, col, rough, metal, strength=1 / 5, emissive=em)
    if gloss:  # a soft top highlight on the glaze
        y, x = K.grid(w, h)
        hl = np.clip(1 - y / (h * 0.5), 0, 1) ** 2 * inn * 0.10
        rgb = rgb + hl[..., None]
    return rgb, outer


def card():
    col, rough = lacquer_maps(192, 192, np.array([0.07, 0.045, 0.10], f32), 21)
    rgb, a = framed_pill(192, 192, 36, col, rough, np.zeros((192, 192), f32), rim=3, seed=22)
    save(rgb, a * 0.97, "FmCard.png")


def chips():
    w, h = 192, 64
    col, rough = lacquer_maps(w, h, np.array([0.09, 0.06, 0.12], f32), 31)
    rgb, a = framed_pill(w, h, 30, col, rough, np.zeros((h, w), f32), rim=3, seed=32)
    save(rgb, a, "FmChip.png")
    col2 = np.broadcast_to(AMETHYST, (h, w, 3)).astype(f32) * (0.85 + 0.25 * K.noise((h, w), 8, 33)[..., None])
    rgb2, a2 = framed_pill(w, h, 30, col2, np.full((h, w), 0.10, f32), np.zeros((h, w), f32), rim=3, emissive_inner=np.array([0.35, 0.15, 0.6], f32), seed=34)
    save(rgb2, a2, "FmChipOn.png")


def tabbar():
    w, h = 512, 128
    col, rough = lacquer_maps(w, h, np.array([0.05, 0.035, 0.07], f32), 41)
    rgb, a = framed_pill(w, h, 60, col, rough * 0.6, np.zeros((h, w), f32), rim=4, seed=42)
    save(rgb, a * 0.96, "FmTabBar.png")


def onair():
    w, h = 256, 72
    col = np.broadcast_to(CRIMSON, (h, w, 3)).astype(f32) * (0.9 + 0.2 * K.noise((h, w), 6, 51)[..., None])
    rgb, a = framed_pill(w, h, 34, col, np.full((h, w), 0.12, f32), np.zeros((h, w), f32), rim=3, emissive_inner=np.array([0.7, 0.08, 0.1], f32), seed=52)
    save(rgb, a, "FmOnAir.png")


# ================================================================ knobs
def knob(on):
    s = 192
    y, x = K.grid(s, s)
    r = np.hypot(x - s / 2 + 0.5, y - s / 2 + 0.5)
    outer = np.clip(s / 2 - 2 - r, 0, 1)
    inner = np.clip(s / 2 - 16 - r, 0, 1)
    ring = np.clip(outer - inner, 0, 1)
    gcol, grough, dents = gilt_maps(s, s, 61 + on)
    knurl = (np.sin(np.arctan2(y - s / 2, x - s / 2) * 48) * 0.5 + 0.5) * np.clip((r - (s / 2 - 10)) / 6, 0, 1) * 0.02
    height = H.dome(K.inner(outer), 10) * 0.30 + dents * ring + knurl * ring
    if on:
        body = AMETHYST
        height = height + H.dome(K.inner(inner), s / 2 - 16) * 0.32 * inner
        frough, fmetal = 0.06, 0.0
        em = np.array([0.32, 0.12, 0.6], f32)[None, None, :] * ndimage.gaussian_filter(inner, 16)[..., None] * 0.55
    else:
        body = np.array([0.08, 0.055, 0.11], f32)
        height = height + H.dome(K.inner(inner), 22) * 0.10 * inner
        frough, fmetal, em = 0.18, 0.0, None
    col = gcol * ring[..., None] + body[None, None, :] * (1 - ring[..., None])
    rough = grough * ring + frough * (1 - ring)
    metal = ring * 0.95 + fmetal * (1 - ring)
    rgb = K.lit(height, col, rough, metal, strength=1 / 5, emissive=em)
    save(rgb, outer, "FmKnobOn.png" if on else "FmKnob.png")


def knobs():
    knob(False)
    knob(True)


# ================================================================ icons (white embossed; tinted in game)
def icon_mask(name):
    s = 256

    def m(fn):
        return K.mask((s, s), fn, ss=4)

    W = 22  # stroke weight for line icons (thick: they must read at 22 px)
    if name == "Play":
        return m(lambda d, k: d.polygon([(86 * k, 58 * k), (86 * k, 198 * k), (200 * k, 128 * k)], fill=255))
    if name == "Pause":
        return m(lambda d, k: (d.rounded_rectangle([70 * k, 60 * k, 112 * k, 196 * k], 10 * k, fill=255), d.rounded_rectangle([144 * k, 60 * k, 186 * k, 196 * k], 10 * k, fill=255)))
    if name in ("Prev", "Next"):
        def f(d, k):
            d.rounded_rectangle([48 * k, 66 * k, 72 * k, 190 * k], 8 * k, fill=255)
            d.polygon([(206 * k, 66 * k), (206 * k, 190 * k), (124 * k, 128 * k)], fill=255)
            d.polygon([(134 * k, 66 * k), (134 * k, 190 * k), (76 * k, 128 * k)], fill=255)
        a = m(f)
        return a[:, ::-1].copy() if name == "Next" else a
    if name == "Loop":
        def f(d, k):
            d.arc([56 * k, 56 * k, 200 * k, 200 * k], 200, 520 - 40, fill=255, width=W * k)
            d.polygon([(150 * k, 26 * k), (204 * k, 62 * k), (142 * k, 94 * k)], fill=255)
        return m(f)
    if name == "Queue":
        def f(d, k):
            for i, yy in enumerate((68, 116, 164)):
                d.rounded_rectangle([40 * k, (yy - 11) * k, (150 if i == 2 else 214) * k, (yy + 11) * k], 10 * k, fill=255)
            d.polygon([(172 * k, 144 * k), (172 * k, 204 * k), (220 * k, 174 * k)], fill=255)
        return m(f)
    if name in ("Heart", "HeartFull"):
        def heart(d, k, inset):
            d.ellipse([(36 + inset) * k, (54 + inset) * k, (132 - inset * 0.2) * k, (150 - inset) * k], fill=255)
            d.ellipse([(124 + inset * 0.2) * k, (54 + inset) * k, (220 - inset) * k, (150 - inset) * k], fill=255)
            d.polygon([((42 + inset) * k, (116) * k), ((214 - inset) * k, (116) * k), (128 * k, (214 - inset * 1.4) * k)], fill=255)
        full = m(lambda d, k: heart(d, k, 0))
        if name == "HeartFull":
            return full
        hole = m(lambda d, k: heart(d, k, W))
        return np.clip(full - hole, 0, 1)
    if name == "Search":
        def f(d, k):
            d.ellipse([40 * k, 40 * k, 164 * k, 164 * k], outline=255, width=W * k)
            d.line([(150 * k, 150 * k), (214 * k, 214 * k)], fill=255, width=(W + 8) * k)
        return m(f)
    if name == "Bell":
        def f(d, k):
            d.pieslice([56 * k, 40 * k, 200 * k, 184 * k], 180, 360, fill=255)
            d.polygon([(56 * k, 112 * k), (200 * k, 112 * k), (220 * k, 184 * k), (36 * k, 184 * k)], fill=255)
            d.ellipse([106 * k, 184 * k, 150 * k, 228 * k], fill=255)
            d.rounded_rectangle([118 * k, 24 * k, 138 * k, 50 * k], 8 * k, fill=255)
        return m(f)
    if name == "Home":
        def f(d, k):
            d.polygon([(128 * k, 34 * k), (226 * k, 122 * k), (198 * k, 122 * k), (198 * k, 216 * k), (58 * k, 216 * k), (58 * k, 122 * k), (30 * k, 122 * k)], fill=255)
        a = m(f)
        door = m(lambda d, k: (d.rounded_rectangle([106 * k, 146 * k, 150 * k, 216 * k], 20 * k, fill=255)))  # a gothic arch door
        return np.clip(a - door, 0, 1)
    if name == "Library":  # two eighth notes, beamed
        def f(d, k):
            d.ellipse([40 * k, 160 * k, 104 * k, 214 * k], fill=255)
            d.ellipse([146 * k, 136 * k, 210 * k, 190 * k], fill=255)
            d.rectangle([84 * k, 54 * k, 104 * k, 190 * k], fill=255)
            d.rectangle([190 * k, 36 * k, 210 * k, 166 * k], fill=255)
            d.polygon([(84 * k, 54 * k), (210 * k, 30 * k), (210 * k, 68 * k), (84 * k, 92 * k)], fill=255)
        return m(f)
    if name == "Station":  # a wireless mast with radio rings
        def f(d, k):
            d.polygon([(128 * k, 92 * k), (172 * k, 226 * k), (150 * k, 226 * k), (128 * k, 156 * k), (106 * k, 226 * k), (84 * k, 226 * k)], fill=255)
            d.ellipse([110 * k, 74 * k, 146 * k, 110 * k], fill=255)
            for rr in (46, 84):
                d.arc([(128 - rr) * k, (92 - rr) * k, (128 + rr) * k, (92 + rr) * k], 200, 250, fill=255, width=16 * k)
                d.arc([(128 - rr) * k, (92 - rr) * k, (128 + rr) * k, (92 + rr) * k], 290, 340, fill=255, width=16 * k)
        return m(f)
    if name == "Back":
        return m(lambda d, k: d.line([(160 * k, 44 * k), (82 * k, 128 * k), (160 * k, 212 * k)], fill=255, width=(W + 6) * k, joint="curve"))
    if name == "Plus":
        return m(lambda d, k: (d.rounded_rectangle([114 * k, 40 * k, 142 * k, 216 * k], 12 * k, fill=255), d.rounded_rectangle([40 * k, 114 * k, 216 * k, 142 * k], 12 * k, fill=255)))
    if name == "Volume":
        def f(d, k):
            d.polygon([(36 * k, 98 * k), (82 * k, 98 * k), (136 * k, 48 * k), (136 * k, 208 * k), (82 * k, 158 * k), (36 * k, 158 * k)], fill=255)
            d.arc([96 * k, 74 * k, 196 * k, 182 * k], 300, 60, fill=255, width=16 * k)
            d.arc([96 * k, 34 * k, 236 * k, 222 * k], 300, 60, fill=255, width=16 * k)
        return m(f)
    raise ValueError(name)


ICONS = ["Play", "Pause", "Prev", "Next", "Loop", "Queue", "Heart", "HeartFull", "Search", "Bell", "Home", "Library",
         "Station", "Back", "Plus", "Volume"]


def icons():
    for name in ICONS:
        a = icon_mask(name)
        # a rounded emboss, a crisp edge line, a soft dark outline under it so it reads on any fill
        height = H.dome(K.inner(a), 7) * 0.30
        alb = np.full(a.shape + (3,), 0.93, f32)
        rgb = K.lit(height, alb, np.full(a.shape, 0.35, f32), np.zeros(a.shape, f32), strength=1 / 3.2, ao_k=(6, 3))
        lum = (rgb @ np.array([0.3, 0.59, 0.11], f32))
        # bright (the game multiplies by the tint): 0.72..1.0, the relief kept as a gentle shade
        lum = np.clip(0.90 + (lum - lum[a > 0.5].mean()) * 0.6, 0.72, 1.0) if (a > 0.5).any() else lum
        out_rgb = np.repeat(lum[..., None], 3, -1)
        shadow = ndimage.gaussian_filter(a, 5) * 0.55
        rgb2, a2 = comp(np.zeros_like(out_rgb), shadow, out_rgb, a)
        save(rgb2, a2, f"FmIcon{name}.png")


# ================================================================ cover frame
def frame():
    s = 512
    outer = rrect(s, s, 64, 2)
    inn = rrect(s, s, 52, 16)
    ring = np.clip(outer - inn, 0, 1)
    gcol, grough, dents = gilt_maps(s, s, 71)
    y, x = K.grid(s, s)
    # a beaded line round the middle of the rim
    t = np.arctan2(y - s / 2, x - s / 2)
    beads = (np.cos(t * 60) * 0.5 + 0.5) ** 6 * np.clip(1 - np.abs(K.inner(outer) - 8) / 3, 0, 1) * 0.05
    height = H.dome(K.inner(outer), 9) * 0.30 * ring + dents * ring + beads * ring
    rgb = K.lit(height, gcol, grough, np.full((s, s), 0.95, f32), strength=1 / 5)
    save(rgb, ring, "FmCoverFrame.png")


# ================================================================ covers
COVERS = [
    ("Crescent", (0.18, 0.10, 0.42), (0.04, 0.02, 0.10), "brass"),
    ("Raven", (0.40, 0.08, 0.14), (0.06, 0.02, 0.05), "iron"),
    ("RoseWindow", (0.12, 0.10, 0.38), (0.30, 0.05, 0.22), "glass"),
    ("Bell", (0.30, 0.16, 0.06), (0.06, 0.03, 0.04), "brass"),
    ("Candle", (0.36, 0.18, 0.06), (0.05, 0.02, 0.06), "wax"),
    ("Key", (0.10, 0.20, 0.30), (0.03, 0.04, 0.08), "brass"),
    ("Rose", (0.42, 0.04, 0.10), (0.08, 0.01, 0.04), "enamel"),
    ("Moth", (0.20, 0.22, 0.36), (0.05, 0.04, 0.10), "silver"),
    ("Dial", (0.24, 0.10, 0.40), (0.06, 0.03, 0.10), "brass"),
    ("Organ", (0.22, 0.06, 0.30), (0.04, 0.02, 0.06), "silver"),
    ("Quill", (0.14, 0.24, 0.24), (0.03, 0.05, 0.06), "brass"),
    ("Lantern", (0.40, 0.22, 0.08), (0.08, 0.03, 0.03), "brass"),
]


def emblem_mask(name, s):
    def m(fn):
        return K.mask((s, s), fn, ss=3)
    c = s / 2
    if name == "Crescent":
        a = m(lambda d, k: d.ellipse([(c - 150) * k, (c - 150) * k, (c + 150) * k, (c + 150) * k], fill=255))
        b = m(lambda d, k: d.ellipse([(c - 90) * k, (c - 175) * k, (c + 190) * k, (c + 105) * k], fill=255))
        stars = m(lambda d, k: [d.regular_polygon(((c + dx) * k, (c + dy) * k, r * k), 4, rotation=45, fill=255) for dx, dy, r in ((70, -60, 26), (120, 40, 16), (40, 30, 12))])
        return np.clip(np.clip(a - b, 0, 1) + stars, 0, 1)
    if name == "Raven":
        pts = [(110, 300), (170, 230), (250, 200), (320, 150), (360, 158), (330, 182), (380, 190), (300, 230), (340, 300), (260, 270), (220, 330), (190, 300)]
        a = m(lambda d, k: d.polygon([(x * k, y * k) for x, y in pts], fill=255))
        moon = m(lambda d, k: d.ellipse([140 * k, 80 * k, 380 * k, 320 * k], outline=255, width=14 * k))
        return np.clip(a + moon * 0.9, 0, 1)
    if name == "RoseWindow":
        def f(d, k):
            d.ellipse([(c - 170) * k, (c - 170) * k, (c + 170) * k, (c + 170) * k], outline=255, width=22 * k)
            d.ellipse([(c - 46) * k, (c - 46) * k, (c + 46) * k, (c + 46) * k], outline=255, width=16 * k)
            for i in range(12):
                t = i * math.pi / 6
                d.line([((c + math.cos(t) * 46) * k, (c + math.sin(t) * 46) * k), ((c + math.cos(t) * 160) * k, (c + math.sin(t) * 160) * k)], fill=255, width=12 * k)
                cx, cy = c + math.cos(t + math.pi / 12) * 112, c + math.sin(t + math.pi / 12) * 112
                d.ellipse([(cx - 22) * k, (cy - 22) * k, (cx + 22) * k, (cy + 22) * k], outline=255, width=9 * k)
        return m(f)
    if name == "Bell":
        def f(d, k):
            d.pieslice([(c - 110) * k, (c - 170) * k, (c + 110) * k, (c + 50) * k], 180, 360, fill=255)
            d.polygon([((c - 110) * k, (c - 60) * k), ((c + 110) * k, (c - 60) * k), ((c + 160) * k, (c + 110) * k), ((c - 160) * k, (c + 110) * k)], fill=255)
            d.ellipse([(c - 34) * k, (c + 110) * k, (c + 34) * k, (c + 178) * k], fill=255)
            d.rounded_rectangle([(c - 26) * k, (c - 210) * k, (c + 26) * k, (c - 160) * k], 10 * k, fill=255)
        return m(f)
    if name == "Candle":
        def f(d, k):
            d.rounded_rectangle([(c - 52) * k, (c - 40) * k, (c + 52) * k, (c + 190) * k], 14 * k, fill=255)
            d.ellipse([(c - 130) * k, (c + 160) * k, (c + 130) * k, (c + 214) * k], fill=255)
            d.polygon([((c - 6) * k, (c - 40) * k), ((c + 6) * k, (c - 40) * k), ((c + 3) * k, (c - 60) * k), ((c - 3) * k, (c - 60) * k)], fill=255)
        return m(f)
    if name == "Key":
        def f(d, k):
            d.ellipse([(c - 170) * k, (c - 70) * k, (c - 30) * k, (c + 70) * k], outline=255, width=30 * k)
            d.rectangle([(c - 40) * k, (c - 16) * k, (c + 180) * k, (c + 16) * k], fill=255)
            d.rectangle([(c + 110) * k, (c + 10) * k, (c + 136) * k, (c + 70) * k], fill=255)
            d.rectangle([(c + 150) * k, (c + 10) * k, (c + 176) * k, (c + 50) * k], fill=255)
        return m(f)
    if name == "Rose":
        def f(d, k):
            for i, r in enumerate((150, 112, 76, 42)):
                for j in range(5):
                    t = j * 2 * math.pi / 5 + i * 0.6
                    cx, cy = c + math.cos(t) * r * 0.42, c - 20 + math.sin(t) * r * 0.42
                    d.ellipse([(cx - r * 0.55) * k, (cy - r * 0.55) * k, (cx + r * 0.55) * k, (cy + r * 0.55) * k], outline=255, width=10 * k)
            d.line([(c * k, (c + 110) * k), ((c - 20) * k, (c + 220) * k)], fill=255, width=16 * k)
        return m(f)
    if name == "Moth":
        def f(d, k):
            for sgn in (-1, 1):
                d.polygon([(c * k, (c - 40) * k), ((c + sgn * 200) * k, (c - 120) * k), ((c + sgn * 170) * k, (c + 20) * k), (c * k, (c + 10) * k)], fill=255)
                d.polygon([(c * k, (c + 10) * k), ((c + sgn * 140) * k, (c + 40) * k), ((c + sgn * 100) * k, (c + 150) * k), (c * k, (c + 60) * k)], fill=255)
            d.ellipse([(c - 20) * k, (c - 80) * k, (c + 20) * k, (c + 110) * k], fill=255)
        a = m(f)
        eyes = m(lambda d, k: [d.ellipse([(c + sgn * 110 - 26) * k, (c - 76) * k, (c + sgn * 110 + 26) * k, (c - 24) * k], fill=255) for sgn in (-1, 1)])
        return np.clip(a - eyes * 0.75, 0, 1)
    if name == "Dial":
        def f(d, k):
            d.ellipse([(c - 180) * k, (c - 180) * k, (c + 180) * k, (c + 180) * k], outline=255, width=20 * k)
            for i in range(25):
                t = math.pi * (0.85 + i * 1.3 / 24)
                r1 = 150 if i % 4 else 130
                d.line([((c + math.cos(t) * r1) * k, (c + math.sin(t) * r1) * k), ((c + math.cos(t) * 166) * k, (c + math.sin(t) * 166) * k)], fill=255, width=(8 if i % 4 else 12) * k)
            d.line([(c * k, c * k), ((c + math.cos(-0.9) * 150) * k, (c + math.sin(-0.9) * 150) * k)], fill=255, width=14 * k)
            d.ellipse([(c - 30) * k, (c - 30) * k, (c + 30) * k, (c + 30) * k], fill=255)
        return m(f)
    if name == "Organ":
        def f(d, k):
            hs = (220, 290, 340, 380, 340, 290, 220)
            for i, hh in enumerate(hs):
                x0 = c - 196 + i * 56
                d.rounded_rectangle([x0 * k, (c + 190 - hh) * k, (x0 + 44) * k, (c + 190) * k], 20 * k, fill=255)
            d.rectangle([(c - 210) * k, (c + 180) * k, (c + 210) * k, (c + 214) * k], fill=255)
        a = m(f)
        mouths = m(lambda d, k: [d.polygon([((c - 196 + i * 56 + 8) * k, (c + 120) * k), ((c - 196 + i * 56 + 36) * k, (c + 120) * k), ((c - 196 + i * 56 + 22) * k, (c + 100) * k)], fill=255) for i in range(7)])
        return np.clip(a - mouths, 0, 1)
    if name == "Quill":
        def f(d, k):
            d.polygon([((c + 170) * k, (c - 200) * k), ((c + 60) * k, (c - 60) * k), ((c - 80) * k, (c + 120) * k), ((c - 40) * k, (c + 40) * k), ((c + 40) * k, (c - 100) * k)], fill=255)
            d.polygon([((c + 170) * k, (c - 200) * k), ((c + 110) * k, (c - 30) * k), ((c - 60) * k, (c + 130) * k)], fill=255)
            d.line([((c - 70) * k, (c + 130) * k), ((c - 150) * k, (c + 210) * k)], fill=255, width=12 * k)
            d.ellipse([(c - 200) * k, (c + 150) * k, (c - 90) * k, (c + 214) * k], fill=255)
        return m(f)
    if name == "Lantern":
        def f(d, k):
            d.polygon([((c - 110) * k, (c - 110) * k), ((c + 110) * k, (c - 110) * k), ((c + 90) * k, (c + 150) * k), ((c - 90) * k, (c + 150) * k)], outline=255, width=20 * k)
            d.polygon([(c * k, (c - 200) * k), ((c + 130) * k, (c - 110) * k), ((c - 130) * k, (c - 110) * k)], fill=255)
            d.rectangle([(c - 120) * k, (c + 150) * k, (c + 120) * k, (c + 186) * k], fill=255)
            d.arc([(c - 40) * k, (c - 260) * k, (c + 40) * k, (c - 180) * k], 180, 360, fill=255, width=14 * k)
            for sgn in (-1, 1):
                d.line([((c + sgn * 36) * k, (c - 110) * k), ((c + sgn * 30) * k, (c + 150) * k)], fill=255, width=10 * k)
        return m(f)
    raise ValueError(name)


def emblem_material(kind, s, seed):
    n = K.noise((s, s), 5, seed)
    if kind == "brass":
        col, rough, dents = gilt_maps(s, s, seed)
        return col, rough, np.full((s, s), 0.95, f32), dents
    if kind == "silver":
        col = np.array([0.80, 0.80, 0.86], f32)[None, None, :] * (0.85 + 0.2 * n[..., None])
        return col.astype(f32), 0.2 + 0.1 * n, np.full((s, s), 0.95, f32), (n - 0.5) * 0.02
    if kind == "iron":
        col = np.array([0.10, 0.10, 0.12], f32)[None, None, :] * (0.8 + 0.4 * n[..., None])
        return col.astype(f32), 0.35 + 0.2 * n, np.full((s, s), 0.7, f32), (n - 0.5) * 0.05
    if kind == "enamel":
        col = np.array([0.75, 0.06, 0.12], f32)[None, None, :] * (0.85 + 0.25 * n[..., None])
        return col.astype(f32), 0.08 + 0.05 * n, np.zeros((s, s), f32), (n - 0.5) * 0.01
    if kind == "glass":
        col = np.array([0.50, 0.30, 0.95], f32)[None, None, :] * (0.8 + 0.3 * n[..., None])
        return col.astype(f32), np.full((s, s), 0.06, f32), np.zeros((s, s), f32), np.zeros((s, s), f32)
    if kind == "wax":
        col = np.array([0.90, 0.84, 0.70], f32)[None, None, :] * (0.9 + 0.1 * n[..., None])
        return col.astype(f32), np.full((s, s), 0.5, f32), np.zeros((s, s), f32), (n - 0.5) * 0.01
    raise ValueError(kind)


def covers():
    s = 512
    y, x = K.grid(s, s)
    for i, (name, top, bot, kind) in enumerate(COVERS):
        top, bot = np.array(top, f32), np.array(bot, f32)
        # the painted plate: a diagonal gradient, a soft light behind the emblem, a fine canvas grain, a pattern
        t = np.clip((x * 0.35 + y) / (s * 1.35), 0, 1)[..., None]
        bg = top * (1 - t) + bot * t
        halo = np.exp(-(((x - s / 2) / (s * 0.38)) ** 2 + ((y - s * 0.46) / (s * 0.38)) ** 2))[..., None]
        bg = bg + (top * 1.6 + 0.04) * halo * 0.6
        pat_kind = i % 3
        if pat_kind == 0:  # stars
            r = np.random.default_rng(100 + i)
            st = np.zeros((s, s), f32)
            for _ in range(70):
                px, py = r.integers(0, s, 2)
                st[py, px] = r.random() * 1.0
            st = ndimage.gaussian_filter(st, 1.1) * 9
            bg = bg + st[..., None] * 0.6
        elif pat_kind == 1:  # deco rays
            ang = np.arctan2(x - s / 2, y - s * 0.46)
            rays = (np.sin(ang * 18) * 0.5 + 0.5) ** 8
            bg = bg * (1 + rays[..., None] * 0.18)
        else:  # stained-glass lattice
            lat = (np.abs(np.sin((x + y) / 26)) < 0.08) | (np.abs(np.sin((x - y) / 26)) < 0.08)
            bg = bg * (1 - ndimage.gaussian_filter(lat.astype(f32), 0.8)[..., None] * 0.35)
        grain = (K.noise((s, s), 0.7, 200 + i) - 0.5)[..., None] * 0.05
        bg = np.clip(bg + grain, 0, 1)
        vign = np.clip(1 - 0.6 * (((x - s / 2) / (s * 0.7)) ** 2 + ((y - s / 2) / (s * 0.7)) ** 2), 0.3, 1)
        bg = bg * vign[..., None]
        # the emblem, lit
        em = emblem_mask(name, s)
        col, rough, metal, dents = emblem_material(kind, s, 300 + i)
        height = H.dome(K.inner(em), 9) * 0.32 + dents * em
        emis = None
        if name == "Candle":  # the flame
            fl = K.mask((s, s), lambda d, k: d.ellipse([(s / 2 - 22) * k, (s / 2 - 150) * k, (s / 2 + 22) * k, (s / 2 - 66) * k], fill=255), ss=3)
            fl_rgb, fl_a = glow(fl, 18, np.array([1.0, 0.62, 0.22], f32), 1.4)
            bg = np.clip(bg + fl_rgb * 0.9, 0, 1)
            bg = bg * (1 - fl[..., None]) + np.array([1.0, 0.9, 0.6], f32) * fl[..., None]
        if name == "Lantern":
            light = K.mask((s, s), lambda d, k: d.polygon([((s / 2 - 90) * k, (s / 2 - 100) * k), ((s / 2 + 90) * k, (s / 2 - 100) * k), ((s / 2 + 72) * k, (s / 2 + 140) * k), ((s / 2 - 72) * k, (s / 2 + 140) * k)], fill=255), ss=3)
            lr, _ = glow(light, 30, np.array([1.0, 0.7, 0.3], f32), 1.0)
            bg = np.clip(bg + lr * 0.8 + light[..., None] * np.array([0.6, 0.4, 0.15], f32), 0, 1)
        if kind == "glass":
            emis = np.array([0.35, 0.18, 0.7], f32)[None, None, :] * em[..., None] * 0.6
        lit = K.lit(height, col, rough, metal, strength=1 / 5, emissive=emis)
        shadow = ndimage.shift(ndimage.gaussian_filter(em, 8), (10, 6)) * 0.7
        rgb = bg * (1 - shadow[..., None])
        rgb = rgb * (1 - em[..., None]) + lit * em[..., None]
        # a fine bevelled edge to the plate (the in-game corner rounds it)
        save(rgb, np.ones((s, s), f32), f"FmCover{i + 1:02d}.png")


# ================================================================ banner
def banner():
    w, h = 1024, 480
    y, x = K.grid(w, h)
    t = (y / h)[..., None]
    sky = np.array([0.20, 0.08, 0.38], f32) * (1 - t) + np.array([0.36, 0.05, 0.12], f32) * t
    # the moon, glowing, top right
    mx, my, mr = w * 0.655, h * 0.30, 84
    md = np.hypot(x - mx, y - my)
    moon = np.clip(mr - md, 0, 1)
    halo = np.exp(-((md - mr).clip(0) / 120) ** 2) * (1 - moon)
    rings = sum(np.clip(1 - np.abs(md - r) / 3.0, 0, 1) * np.exp(-((md - mr) / 300)) for r in (170, 230, 300, 380))
    sky = sky + np.array([0.70, 0.55, 0.95], f32) * halo[..., None] * 0.45 + np.array([0.75, 0.6, 1.0], f32) * rings[..., None] * 0.35
    rng = np.random.default_rng(7)
    st = np.zeros((h, w), f32)
    for _ in range(140):
        px, py = rng.integers(0, w), rng.integers(0, int(h * 0.7))
        st[py, px] = rng.random()
    sky = sky + ndimage.gaussian_filter(st, 1.0)[..., None] * 5
    # the moon's face, lit PBR (a pitted pale disc)
    mcol = np.array([0.92, 0.88, 0.80], f32)[None, None, :] * (0.8 + 0.25 * K.noise((h, w), 6, 8)[..., None])
    mheight = H.dome(K.inner(moon), mr) * 0.5 - (K.noise((h, w), 3, 9) ** 3) * 0.06 * moon
    mlit = K.lit(mheight, mcol, np.full((h, w), 0.8, f32), np.zeros((h, w), f32), strength=1 / 4)
    sky = sky * (1 - moon[..., None]) + (mlit * 0.7 + 0.3) * moon[..., None]
    # the tower: a gothic bell tower in stone with a brass wireless mast
    def tower(d, k):
        bx = w * 0.84
        d.rectangle([(bx - 90) * k, 250 * k, (bx + 90) * k, h * k], fill=255)
        d.polygon([((bx - 110) * k, 255 * k), ((bx + 110) * k, 255 * k), (bx * k, 120 * k)], fill=255)
        d.rectangle([(bx - 130) * k, 380 * k, (bx + 130) * k, h * k], fill=255)
        for sgn in (-1, 1):
            d.polygon([((bx + sgn * 130) * k, 380 * k), ((bx + sgn * 150) * k, 380 * k), ((bx + sgn * 140) * k, 330 * k)], fill=255)
    tm = K.mask((w, h), tower, ss=2)
    win = K.mask((w, h), lambda d, k: (d.rounded_rectangle([(w * 0.84 - 30) * k, 280 * k, (w * 0.84 + 30) * k, 360 * k], 30 * k, fill=255)), ss=2)
    mast = K.mask((w, h), lambda d, k: (d.polygon([(w * 0.84 * k, 18 * k), ((w * 0.84 + 30) * k, 130 * k), ((w * 0.84 - 30) * k, 130 * k)], outline=255, width=8 * k),
                                        d.line([(w * 0.84 * k, 18 * k), (w * 0.84 * k, 130 * k)], fill=255, width=6 * k),
                                        d.ellipse([(w * 0.84 - 12) * k, 6 * k, (w * 0.84 + 12) * k, 30 * k], fill=255)), ss=2)
    stone_col = np.array([0.16, 0.13, 0.20], f32)[None, None, :] * (0.7 + 0.5 * K.noise((h, w), 2.5, 10)[..., None])
    bricks = ((np.abs(np.sin(y / 9)) < 0.12) | (np.abs(np.sin((x + (np.floor(y / 28) % 2) * 20) / 20)) < 0.08)).astype(f32)
    theight = H.dome(K.inner(tm), 8) * 0.25 - bricks * 0.02 * tm
    tlit = K.lit(theight, stone_col, np.full((h, w), 0.7, f32), np.zeros((h, w), f32), strength=1 / 4)
    gcol, grough, dents = gilt_maps(w, h, 12)
    mlit2 = K.lit(H.dome(K.inner(mast), 3) * 0.2, gcol, grough, np.full((h, w), 0.95, f32), strength=1 / 4)
    out = sky * (1 - tm[..., None]) + tlit * tm[..., None]
    wglow, _ = glow(win, 14, np.array([1.0, 0.7, 0.3], f32), 1.2)
    out = out + wglow * 0.8
    out = out * (1 - win[..., None]) + np.array([1.0, 0.82, 0.45], f32) * win[..., None]
    out = out * (1 - mast[..., None]) + mlit2 * mast[..., None]
    # radio rings from the mast tip
    md2 = np.hypot(x - w * 0.84, y - 18)
    rr = sum(np.clip(1 - np.abs(md2 - r) / 2.5, 0, 1) * (y < 160) * np.exp(-r / 160) for r in (40, 70, 104))
    out = out + np.array([0.85, 0.7, 1.0], f32) * rr[..., None] * 0.9
    # darken the left for the text that sits there in game
    shade = np.clip(1 - x / (w * 0.6), 0, 1) ** 1.5 * 0.35
    out = np.clip(out * (1 - shade[..., None]), 0, 1)
    save(out, np.ones((h, w), f32), "FmBanner.png")


# ================================================================ preview
def preview():
    P = lambda n: Image.open(OUT / n).convert("RGBA")
    W, Hh = 1180, 1500
    sheet = Image.new("RGBA", (W, Hh), (14, 10, 18, 255))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT_T, 22)
    small = ImageFont.truetype(FONT_T, 15)
    # a phone mock: backdrop, banner, two cards with covers, chips, tab bar
    ph = P("FmBackdrop.png").resize((360, 720))
    sheet.paste(ph, (20, 20), ph)
    d.text((40, 70), "Good evening, Ren", fill=(235, 220, 200), font=font)
    for i, (lab, on) in enumerate((("All", True), ("Recent", False), ("Saved", False), ("Station", False))):
        c = P("FmChipOn.png" if on else "FmChip.png").resize((76, 26))
        sheet.paste(c, (40 + i * 80, 112), c)
        d.text((40 + i * 80 + 38, 125), lab, fill=(255, 255, 255) if on else (200, 190, 210), font=small, anchor="mm")
    b = P("FmBanner.png").resize((320, 150))
    mb = Image.new("L", b.size, 0)
    ImageDraw.Draw(mb).rounded_rectangle([0, 0, 319, 149], 18, fill=255)
    sheet.paste(b, (40, 150), mb)
    d.text((56, 166), "Midnight Broadcast", fill=(255, 245, 230), font=font)
    for i in range(3):
        card = P("FmCard.png").resize((320, 64))
        sheet.paste(card, (40, 320 + i * 72), card)
        cv = P(f"FmCover{i + 1:02d}.png").resize((48, 48))
        mm = Image.new("L", (48, 48), 0)
        ImageDraw.Draw(mm).rounded_rectangle([0, 0, 47, 47], 10, fill=255)
        sheet.paste(cv, (48, 328 + i * 72), mm)
        d.text((108, 334 + i * 72), ["Moonlit Hymn", "Raven at the Window", "Rose of Glass"][i], fill=(240, 228, 210), font=small)
        d.text((108, 354 + i * 72), "Night FM", fill=(170, 160, 185), font=small)
        k = P("FmKnob.png").resize((40, 40))
        sheet.paste(k, (312, 332 + i * 72), k)
        ic = P("FmIconPlay.png").resize((22, 22))
        tint = Image.new("RGBA", ic.size, (236, 200, 120, 255))
        tint.putalpha(ic.getchannel("A"))
        sheet.paste(Image.composite(Image.blend(tint, ic, 0.25), ic, ic.getchannel("A")), (321, 341 + i * 72), ic)
    tb = P("FmTabBar.png").resize((220, 56))
    sheet.paste(tb, (90, 660), tb)
    for i, n in enumerate(("Home", "Library", "Station")):
        k = P("FmKnobOn.png" if i == 0 else "FmKnob.png").resize((44, 44))
        sheet.paste(k, (110 + i * 64, 666), k)
        ic = P(f"FmIcon{n}.png").resize((22, 22))
        sheet.paste(ic, (121 + i * 64, 677), ic)
    # the covers
    d.text((420, 24), "Covers", fill=(214, 178, 112), font=font)
    for i in range(12):
        cv = P(f"FmCover{i + 1:02d}.png").resize((180, 180))
        mm = Image.new("L", (180, 180), 0)
        ImageDraw.Draw(mm).rounded_rectangle([0, 0, 179, 179], 26, fill=255)
        sheet.paste(cv, (420 + (i % 4) * 188, 60 + (i // 4) * 188), mm)
        d.text((420 + (i % 4) * 188 + 6, 60 + (i // 4) * 188 + 160), COVERS[i][0], fill=(240, 230, 220), font=small)
    # the now-playing cover with its frame
    big = P("FmCover01.png").resize((240, 240))
    mm = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(mm).rounded_rectangle([0, 0, 239, 239], 30, fill=255)
    sheet.paste(big, (60, 760), mm)
    fr = P("FmCoverFrame.png").resize((240, 240))
    sheet.paste(fr, (60, 760), fr)
    on = P("FmOnAir.png").resize((128, 36))
    sheet.paste(on, (420, 640), on)
    d.text((484, 658), "ON AIR", fill=(255, 240, 230), font=small, anchor="mm")
    # the icons, gold on lacquer and white on amethyst
    d.text((420, 700), "Icons", fill=(214, 178, 112), font=font)
    for i, n in enumerate(ICONS):
        ic = P(f"FmIcon{n}.png").resize((64, 64))
        for row, (bgcol, tint) in enumerate((((22, 14, 30), (236, 200, 120)), ((110, 50, 190), (255, 255, 255)))):
            x0, y0 = 420 + (i % 8) * 90, 740 + (i // 8) * 90 + row * 190
            d.rounded_rectangle([x0, y0, x0 + 80, y0 + 80], 16, fill=bgcol)
            t = Image.new("RGBA", ic.size, tint + (255,))
            g = ic.convert("L")
            t.putalpha(ic.getchannel("A"))
            lum = Image.merge("RGBA", [Image.eval(g, lambda v, c=c: int(v * c / 255)) for c in tint] + [ic.getchannel("A")])
            sheet.paste(lum, (x0 + 8, y0 + 8), lum)
            if row == 0:
                d.text((x0 + 40, y0 + 86), n, fill=(170, 160, 185), font=ImageFont.truetype(FONT_T, 11), anchor="mt")
    for n, pos in (("FmKnob.png", (360, 1030)), ("FmKnobOn.png", (440, 1030))):
        k = P(n).resize((72, 72))
        sheet.paste(k, pos, k)
    sheet.convert("RGB").save(OUT / "preview_nightfm.png")
    print("   preview_nightfm.png")


ALL = {"backdrop": backdrop, "card": card, "chips": chips, "knobs": knobs, "tabbar": tabbar, "onair": onair,
       "banner": banner, "frame": frame, "covers": covers, "icons": icons, "preview": preview}

if __name__ == "__main__":
    want = sys.argv[1:] or list(ALL)
    for k in want:
        print(k)
        ALL[k]()
