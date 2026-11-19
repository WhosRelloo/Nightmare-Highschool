"""PBR art for the Permanent Record (Nightmare Highschool 2.32, the M menu), baked to images.

Owner (2026-11-18): "Make the M menu with completely unique and new ui and icons. Same quality as the other stuff.
PBR, high quality", "It should be organized and easy to understand as well", "I want it to look wayyy higher quality
and ON THEME", "And make it animated. And make different variants based on ur race".

The look, "The Permanent Record": the school's own dossier on you, a bound gothic ledger. The cover depends on your
race; the pages, tabs, medals and icons are shared:
  Human     oxblood leather, gilt tooling, iron corner guards, a candle emblem
  Priest    ivory vellum, gilt tooling with a sunburst, brass corners, a halo emblem
  Vampire   black leather with a crimson velvet inlay, blackened-silver tooling, garnet-set corners, a bat emblem
  Werewolf  rough brown hide with claw gouges, iron tooling, bone corners, a full-moon emblem
  Ghoul     grave-green leather with crackle, verdigris bronze tooling, bone corners, a skull emblem
  Wraith    ash-blue leather, pale silver tooling that glows faintly, silver corners, a hooded emblem
Pages are aged parchment (foxing, darker toward the edges, a crimson double margin rule); each section has its own
leather index tab in a jewel colour with gilt edging; honours are struck gilt medals with crimson enamel, the ones
still to earn blind-tooled into the page, the secret ones in a black-edged envelope tied with string (no wax seal: the
owner retired the Seal icon). Text is dark sepia ink on parchment, gilt on leather.

Materials are the school's PBR sets (art/props/source NH_Leather / Brass / Iron / Paper: colour, normal, roughness)
lit by the kit's pipeline (make_kit_ui.lit -> make_health_pbr.shade: GGX, a warm key, a cool fill, a candle rim, an
environment reflection, AO from the height).

Pieces (art/ui/hud/out/record/, staged to art/group-upload-record/):
  RecCover<Race>.png    1600x950  the dossier cover per race (stretched to the panel; 6)
  RecPlate<Race>.png    640x110   9-slice (slice 48) the title nameplate in the race's metal (6)
  RecPage.png           768       9-slice (slice 80) a parchment page; the margin rule sits in the left slice
  RecTab<Section>.png / RecTabOn<Section>.png  360x92  9-slice (slice 40) leather index tabs (9 sections x 2)
  RecCard.png           320       9-slice (slice 56) a parchment card with gilt corner brackets
  RecButton.png / RecButtonOn.png  224x72  9-slice (slice 34) crimson enamel in a gilt rim / pressed
  RecInk.png            224x72    9-slice (slice 34) a black lacquer pill in a gilt rim (secondary buttons)
  RecStamp.png          320x110   9-slice (slice 36) a crimson rubber-stamp frame (EARNED, ON FILE)
  RecMedal.png          256       a struck gilt medal, crimson enamel ring, a black-and-crimson grosgrain ribbon
  RecMedalDim.png       256       a medal still to earn: blind-tooled into the parchment
  RecEnvelope.png       256       a secret honour: a black-edged envelope tied with crimson string round a gilt button
  RecPip.png / RecPipOn.png  64   a tier pip: a debossed ring / a gilt rivet
  RecClose.png          128       an iron ring with a gilt boss (the X icon sits on it)
  RecGlint.png          256x64    a soft diagonal light streak (animated across gilt in game)
  RecIcon<Name>.png     256       white embossed icons (tinted in game): Student, Academics, Attendance, Athletics,
                                  Combat, Factions, Paths, Honours, Entries, Might, Grit, Wits, Social, Supernatural,
                                  Story, Secret, Close, Plus, Check, and Race<Race> (6)
  preview_record.png / preview_record_covers.png   the menu laid out, and all six covers (for review)

  python make_record_ui.py [covers plates page tabs card buttons ink stamp medals envelope pips close glint icons preview]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as H
import make_kit_ui as K

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "record"
OUT.mkdir(parents=True, exist_ok=True)
f32 = np.float32
FONT_T = "C:/Windows/Fonts/georgiab.ttf"
FONT_TYPE = "C:/Windows/Fonts/courbd.ttf"

PARCH = np.array([0.90, 0.80, 0.62], f32)
SEPIA = np.array([0.24, 0.15, 0.09], f32)
CRIMSON = np.array([0.48, 0.05, 0.09], f32)
RED_INK = np.array([0.60, 0.08, 0.10], f32)
GILT_TINT = (1.18, 1.0, 0.62)

# section tab colours (deep jewel tones; the gilt edging stays gold)
SECTIONS = {
    "Student": (0.20, 0.26, 0.42), "Academics": (0.14, 0.32, 0.20), "Attendance": (0.52, 0.36, 0.12),
    "Athletics": (0.08, 0.30, 0.32), "Combat": (0.46, 0.06, 0.08), "Factions": (0.30, 0.13, 0.42),
    "Paths": (0.46, 0.32, 0.12), "Honours": (0.40, 0.18, 0.06), "Entries": (0.22, 0.21, 0.25),
}

# race covers: leather tint, grain scale, tooling metal, corner kind, extra, stitch colour, emblem
RACES = {
    "Human": dict(leather=(0.32, 0.09, 0.08), grain=1.0, tool="gilt", corner="iron", extra=None, stitch=(0.55, 0.40, 0.20)),
    "Priest": dict(leather=(0.92, 0.86, 0.74), grain=0.7, tool="gilt", corner="brass", extra="halo", stitch=(0.62, 0.10, 0.12)),
    "Vampire": dict(leather=(0.09, 0.05, 0.06), grain=0.8, tool="silver", corner="garnet", extra="velvet", stitch=(0.50, 0.06, 0.10)),
    "Werewolf": dict(leather=(0.40, 0.25, 0.14), grain=1.7, tool="iron", corner="bone", extra="claws", stitch=(0.30, 0.22, 0.14)),
    "Ghoul": dict(leather=(0.15, 0.19, 0.12), grain=1.2, tool="verdigris", corner="bone", extra="cracks", stitch=(0.36, 0.40, 0.26)),
    "Wraith": dict(leather=(0.18, 0.21, 0.27), grain=0.8, tool="palesilver", corner="silver", extra="glow", stitch=(0.55, 0.66, 0.80)),
}
METALS = {  # (material, tint, rough add, metal)
    "gilt": ("Brass", GILT_TINT, -0.05, 0.95), "brass": ("Brass", (1.0, 0.95, 0.85), 0.0, 0.95),
    "silver": ("Iron", (0.80, 0.80, 0.84), -0.15, 0.95), "palesilver": ("Iron", (1.10, 1.18, 1.32), -0.2, 0.95),
    "iron": ("Iron", (0.62, 0.62, 0.66), 0.05, 0.9), "verdigris": ("Brass", (0.55, 0.85, 0.66), 0.15, 0.6),
}


# ================================================================ helpers
def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), "RGBA")
    img.save(OUT / name, optimize=True)
    print("  ", name, img.size)
    return img


def rrect(w, h, r, inset=0):
    return K.mask((w, h), lambda d, s: d.rounded_rectangle([inset * s, inset * s, (w - inset) * s - 1, (h - inset) * s - 1], r * s, fill=255))


def comp(dst_rgb, dst_a, src_rgb, src_a):
    a = src_a + dst_a * (1 - src_a)
    rgb = (src_rgb * src_a[..., None] + dst_rgb * dst_a[..., None] * (1 - src_a[..., None])) / np.maximum(a, 1e-6)[..., None]
    return rgb, a


def shadow_of(m, sigma, k, dx=0, dy=0):
    s = ndimage.gaussian_filter(m.astype(f32), sigma) * k
    return ndimage.shift(s, (dy, dx), order=1, mode="constant")


def bevel(m, px):
    return H.dome(K.inner(m), px)


def mat(name, w, h, period, tint=(1, 1, 1)):
    """a PBR set tiled over w x h: sRGB albedo, a tangent normal (for detail), roughness"""
    col = K.tile_map(name, "color", (w, h), period) * np.array(tint, f32)
    nrm = K.tile_map(name, "normal", (w, h), period) * 2 - 1
    rough = K.tile_map(name, "rough", (w, h), period)[..., 0]
    return col.astype(f32), nrm.astype(f32), rough.astype(f32)


def metal_maps(kind, w, h, period=256):
    name, tint, radd, metal = METALS[kind]
    col, nrm, rough = mat(name, w, h, period, tint)
    return col, nrm, np.clip(rough + radd, 0.08, 1), metal


def leather_maps(w, h, tint, grain, seed):
    # two tilings at unrelated scales, offset, blended by low-frequency noise: no visible repeat
    P1, P2 = int(900 / grain), int(1310 / grain)
    c1, n1, r1 = mat("Leather", w + P1, h + P1, P1, (1, 1, 1))
    c2, n2, r2 = mat("Leather", w + P2, h + P2, P2, (1, 1, 1))
    o1, o2 = (seed * 37) % P1, (seed * 53) % P2
    c1, n1, r1 = c1[o1:o1 + h, o1:o1 + w], n1[o1:o1 + h, o1:o1 + w], r1[o1:o1 + h, o1:o1 + w]
    c2, n2, r2 = c2[o2:o2 + h, o2:o2 + w][:, ::-1], n2[o2:o2 + h, o2:o2 + w][:, ::-1] * np.array([-1, 1, 1], f32), r2[o2:o2 + h, o2:o2 + w][:, ::-1]
    t = np.clip((K.noise((h, w), 90, seed + 5) - 0.5) * 3 + 0.5, 0, 1)
    col = c1 * (1 - t[..., None]) + c2 * t[..., None]
    nrm = n1 * (1 - t[..., None]) + n2 * t[..., None]
    rough = r1 * (1 - t) + r2 * t
    lum = col @ np.array([0.3, 0.59, 0.11], f32)
    mott = K.noise((h, w), 60, seed)
    alb = (lum / max(1e-6, lum.mean()))[..., None] * np.array(tint, f32) * (0.88 + 0.24 * mott[..., None])
    return alb.astype(f32), nrm, np.clip(rough * 0.9 + 0.08, 0.2, 0.9)


def parchment_maps(w, h, seed, period=768):
    col, nrm, rough = mat("Paper", w, h, period, (1.02, 0.92, 0.72))
    y, x = K.grid(w, h)
    rng = np.random.default_rng(seed)
    stains = np.zeros((h, w), f32)
    for _ in range(max(2, (w * h) // 90000)):
        sx, sy, sr = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(30, 120)
        rd = np.hypot(x - sx, y - sy) / sr
        stains += np.exp(-((rd - 1) / 0.08) ** 2) * 0.35 + np.exp(-rd ** 2 * 2) * 0.10
    fox = (K.noise((h, w), 1.4, seed + 1) > 0.84) * K.noise((h, w), 6, seed + 2)
    col = col * (1 - 0.14 * np.clip(stains, 0, 1))[..., None] * np.array([1, 0.96, 0.88], f32)
    col = col * (1 - 0.22 * fox)[..., None]
    return col.astype(f32), nrm, rough


def draw_mask(w, h, fn, ss=4):
    return K.mask((w, h), fn, ss=ss)


# ================================================================ race emblems (masks; also exported as icons)
def emblem_mask(race, s=256):
    def m(fn):
        return draw_mask(s, s, fn)
    if race == "Human":  # a candle with a flame and a drip
        a = m(lambda d, k: (d.rounded_rectangle([96 * k, 100 * k, 160 * k, 232 * k], 10 * k, fill=255),
                            d.polygon([(128 * k, 18 * k), (150 * k, 62 * k), (142 * k, 86 * k), (114 * k, 86 * k), (106 * k, 62 * k)], fill=255),
                            d.rounded_rectangle([82 * k, 222 * k, 174 * k, 240 * k], 8 * k, fill=255)))
        wick = m(lambda d, k: d.rectangle([125 * k, 86 * k, 131 * k, 100 * k], fill=255))
        return np.clip(a + wick, 0, 1)
    if race == "Priest":  # a halo over a sunburst
        def f(d, k):
            d.ellipse([58 * k, 30 * k, 198 * k, 78 * k], outline=255, width=16 * k)
            for i in range(12):
                t = math.pi * (i / 11)
                d.line([(128 * k, 150 * k), ((128 + math.cos(t) * 104) * k, (150 - math.sin(t) * 64 - 0) * k)], fill=255, width=10 * k)
            d.ellipse([92 * k, 114 * k, 164 * k, 186 * k], fill=255)
            d.rectangle([40 * k, 196 * k, 216 * k, 214 * k], fill=255)
        return m(f)
    if race == "Vampire":  # a bat, wings spread
        def f(d, k):
            d.polygon([(128 * k, 96 * k), (100 * k, 84 * k), (60 * k, 70 * k), (12 * k, 92 * k), (30 * k, 110 * k), (34 * k, 140 * k),
                       (60 * k, 132 * k), (78 * k, 160 * k), (100 * k, 146 * k), (128 * k, 186 * k), (156 * k, 146 * k), (178 * k, 160 * k),
                       (196 * k, 132 * k), (222 * k, 140 * k), (226 * k, 110 * k), (244 * k, 92 * k), (196 * k, 70 * k), (156 * k, 84 * k)], fill=255)
            d.polygon([(110 * k, 92 * k), (114 * k, 66 * k), (124 * k, 84 * k), (132 * k, 84 * k), (142 * k, 66 * k), (146 * k, 92 * k)], fill=255)
        return m(f)
    if race == "Werewolf":  # a full moon raked by three claws
        moon = m(lambda d, k: d.ellipse([30 * k, 30 * k, 226 * k, 226 * k], fill=255))
        claws = m(lambda d, k: [d.line([((70 + i * 42) * k, 40 * k), ((110 + i * 42) * k, 220 * k)], fill=255, width=14 * k) for i in range(3)])
        return np.clip(moon - claws, 0, 1)
    if race == "Ghoul":  # a skull
        def f(d, k):
            d.ellipse([46 * k, 26 * k, 210 * k, 180 * k], fill=255)
            d.rounded_rectangle([82 * k, 150 * k, 174 * k, 222 * k], 16 * k, fill=255)
        a = m(f)
        holes = m(lambda d, k: (d.ellipse([74 * k, 86 * k, 120 * k, 136 * k], fill=255), d.ellipse([136 * k, 86 * k, 182 * k, 136 * k], fill=255),
                                d.polygon([(128 * k, 140 * k), (116 * k, 166 * k), (140 * k, 166 * k)], fill=255),
                                [d.rectangle([(98 + i * 22) * k, 188 * k, (106 + i * 22) * k, 222 * k], fill=255) for i in range(3)]))
        return np.clip(a - holes, 0, 1)
    if race == "Wraith":  # a hooded figure fading into wisps
        def f(d, k):
            d.pieslice([54 * k, 20 * k, 202 * k, 168 * k], 180, 360, fill=255)
            d.polygon([(54 * k, 94 * k), (202 * k, 94 * k), (226 * k, 196 * k), (196 * k, 176 * k), (170 * k, 230 * k), (142 * k, 186 * k),
                       (114 * k, 236 * k), (86 * k, 182 * k), (58 * k, 222 * k), (30 * k, 196 * k)], fill=255)
        a = m(f)
        face = m(lambda d, k: d.ellipse([92 * k, 70 * k, 164 * k, 150 * k], fill=255))
        eyes = m(lambda d, k: (d.ellipse([104 * k, 98 * k, 120 * k, 112 * k], fill=255), d.ellipse([136 * k, 98 * k, 152 * k, 112 * k], fill=255)))
        return np.clip(a - face + eyes, 0, 1)
    raise ValueError(race)


def fleuron(d, k, cx, cy, sx, sy, size):
    """a tooled corner curl: two scrolls and a leaf, pointing into the corner (sx, sy = +-1)"""
    def P(x, y):
        return ((cx + sx * x) * k, (cy + sy * y) * k)
    r = size
    w = max(2, int(size / 9)) * k
    d.arc([min(P(0, 0)[0], P(r, r)[0]), min(P(0, 0)[1], P(r, r)[1]), max(P(0, 0)[0], P(r, r)[0]), max(P(0, 0)[1], P(r, r)[1])],
          0, 360, fill=255, width=w)
    d.line([P(r * 0.5, r * 1.0), P(r * 0.5, r * 2.2)], fill=255, width=w)
    d.line([P(r * 1.0, r * 0.5), P(r * 2.2, r * 0.5)], fill=255, width=w)
    d.ellipse([min(P(r * 2.1, r * 0.3)[0], P(r * 2.6, r * 0.7)[0]), min(P(r * 2.1, r * 0.3)[1], P(r * 2.6, r * 0.7)[1]),
               max(P(r * 2.1, r * 0.3)[0], P(r * 2.6, r * 0.7)[0]), max(P(r * 2.1, r * 0.3)[1], P(r * 2.6, r * 0.7)[1])], fill=255)
    d.ellipse([min(P(r * 0.3, r * 2.1)[0], P(r * 0.7, r * 2.6)[0]), min(P(r * 0.3, r * 2.1)[1], P(r * 0.7, r * 2.6)[1]),
               max(P(r * 0.3, r * 2.1)[0], P(r * 0.7, r * 2.6)[0]), max(P(r * 0.3, r * 2.1)[1], P(r * 0.7, r * 2.6)[1])], fill=255)


# ================================================================ covers (one per race)
def cover(race):
    R = RACES[race]
    w, h = 1600, 950
    y, x = K.grid(w, h)
    body = rrect(w, h, 34, 4)
    alb, nrm, rough = leather_maps(w, h, R["leather"], R["grain"], hash(race) % 997)
    metal = np.zeros((h, w), f32)
    height = bevel(body, 26) * 0.10  # a padded board
    em = np.zeros((h, w, 3), f32)
    # the tooling: a double fillet, a top band rule under the title, corner fleurons, the race emblem
    tool = draw_mask(w, h, lambda d, k: (
        d.rounded_rectangle([46 * k, 46 * k, (w - 46) * k, (h - 46) * k], 20 * k, outline=255, width=5 * k),
        d.rounded_rectangle([60 * k, 60 * k, (w - 60) * k, (h - 60) * k], 14 * k, outline=255, width=2 * k),
        d.line([(60 * k, 156 * k), ((w - 60) * k, 156 * k)], fill=255, width=2 * k),
        d.line([(60 * k, 164 * k), ((w - 60) * k, 164 * k)], fill=255, width=4 * k),
        [fleuron(d, k, cx, cy, sx, sy, 22) for cx, cy, sx, sy in ((72, 176, 1, 1), (w - 72, 176, -1, 1), (72, h - 72, 1, -1), (w - 72, h - 72, -1, -1))]), ss=3)
    emb = np.zeros((h, w), f32)
    e = emblem_mask(race, 256)
    e = np.array(Image.fromarray((e * 255).astype(np.uint8)).resize((112, 112), Image.LANCZOS), f32) / 255
    ex, ey = w - 300, 30
    emb[ey:ey + 112, ex:ex + 112] = e
    if R["extra"] == "halo":  # tooled rays round the emblem
        rays = draw_mask(w, h, lambda d, k: [d.line([((ex + 56) * k, (ey + 56) * k), ((ex + 56 + math.cos(t) * 90) * k, (ey + 56 + math.sin(t) * 90) * k)], fill=255, width=2 * k)
                                             for t in np.linspace(0, 2 * math.pi, 28, endpoint=False)], ss=2)
        tool = np.clip(tool + rays * (1 - ndimage.binary_dilation(e > 0.1, iterations=1).astype(f32) if False else rays), 0, 1)
    tool = np.clip(tool + emb, 0, 1) * body
    if R["extra"] == "velvet":  # a crimson velvet inlay inside the inner fillet
        inlay = rrect(w, h, 12, 66) * (1 - draw_mask(w, h, lambda d, k: d.rectangle([60 * k, 0, (w - 60) * k, 172 * k], fill=255), ss=2))
        vel = np.array([0.30, 0.02, 0.06], f32) * (0.8 + 0.4 * K.noise((h, w), 2, 31)[..., None])
        alb = alb * (1 - inlay[..., None]) + vel * inlay[..., None]
        rough = rough * (1 - inlay) + 0.95 * inlay
        height = height - inlay * 0.01 + bevel(inlay, 4) * 0.01
    if R["extra"] == "claws":  # three claw gouges across the board, twice
        gouge = draw_mask(w, h, lambda d, k: [d.line([((w - 520 + i * 46) * k, 240 * k), ((w - 300 + i * 46) * k, 640 * k)], fill=255, width=12 * k) for i in range(3)]
                          + [d.line([((260 + i * 40) * k, 560 * k), ((420 + i * 40) * k, 880 * k)], fill=255, width=10 * k) for i in range(3)], ss=2)
        gouge = ndimage.gaussian_filter(gouge, 1.5) * body
        height = height - gouge * 0.05
        alb = alb * (1 - gouge[..., None] * 0.35) + np.array([0.62, 0.48, 0.34], f32) * gouge[..., None] * 0.35
    if R["extra"] == "cracks":  # crackle in the old leather
        n = K.noise((h, w), 6, 77)
        cr = np.clip(1 - np.abs(n - 0.5) * 60, 0, 1) * (K.noise((h, w), 40, 78) > 0.4) * body
        height = height - cr * 0.01
        alb = alb * (1 + cr[..., None] * 0.5)
    # the tooled lines: pressed in, then filled with the race's metal
    mcol, mnrm, mrough, mmetal = metal_maps(R["tool"], w, h, 300)
    height = height - tool * 0.012 + bevel((tool > 0.5).astype(f32), 2) * 0.004
    alb = alb * (1 - tool[..., None]) + mcol * tool[..., None]
    rough = rough * (1 - tool) + mrough * tool
    metal = metal * (1 - tool) + mmetal * tool
    if R["extra"] == "glow":
        em = em + np.array([0.35, 0.55, 0.9], f32) * ndimage.gaussian_filter(tool, 3)[..., None] * 0.45
    # stitching just inside the edge
    stitch = draw_mask(w, h, lambda d, k: [d.line([(xx * k, 24 * k), ((xx + 14) * k, 24 * k)], fill=255, width=4 * k) for xx in range(40, w - 40, 24)]
                       + [d.line([(xx * k, (h - 24) * k), ((xx + 14) * k, (h - 24) * k)], fill=255, width=4 * k) for xx in range(40, w - 40, 24)]
                       + [d.line([(24 * k, yy * k), (24 * k, (yy + 14) * k)], fill=255, width=4 * k) for yy in range(40, h - 40, 24)]
                       + [d.line([((w - 24) * k, yy * k), ((w - 24) * k, (yy + 14) * k)], fill=255, width=4 * k) for yy in range(40, h - 40, 24)], ss=2)
    height = height + stitch * 0.01
    alb = alb * (1 - stitch[..., None]) + np.array(R["stitch"], f32) * stitch[..., None]
    # corner guards
    S = 132
    guard = draw_mask(w, h, lambda d, k: (d.polygon([(4 * k, 4 * k), (S * k, 4 * k), (4 * k, S * k)], fill=255),
                                          d.polygon([((w - 4) * k, 4 * k), ((w - S) * k, 4 * k), ((w - 4) * k, S * k)], fill=255),
                                          d.polygon([(4 * k, (h - 4) * k), (S * k, (h - 4) * k), (4 * k, (h - S) * k)], fill=255),
                                          d.polygon([((w - 4) * k, (h - 4) * k), ((w - S) * k, (h - 4) * k), ((w - 4) * k, (h - S) * k)], fill=255)), ss=3) * body
    rivets = np.zeros((h, w), f32)
    for cx, cy in ((34, 34), (34, 84), (84, 34), (w - 34, 34), (w - 34, 84), (w - 84, 34), (34, h - 34), (34, h - 84), (84, h - 34), (w - 34, h - 34), (w - 34, h - 84), (w - 84, h - 34)):
        rr = np.hypot(x - cx, y - cy)
        rivets = np.maximum(rivets, np.clip(9 - rr, 0, 1))
    kind = R["corner"]
    if kind == "bone":
        gcol = np.array([0.86, 0.80, 0.66], f32) * (0.85 + 0.25 * K.noise((h, w), 3, 91)[..., None])
        grough, gmetal = 0.45, 0.0
    else:
        gcol, _, grough_m, gmetal = metal_maps({"iron": "iron", "brass": "brass", "silver": "silver", "garnet": "silver"}[kind], w, h, 200)
        grough = grough_m
    height = height + bevel(guard, 8) * 0.10 * guard + H.dome(K.inner(rivets), 8) * 0.12 * rivets
    gm = np.clip(guard + rivets, 0, 1)
    alb = alb * (1 - gm[..., None]) + gcol * gm[..., None]
    rough = rough * (1 - gm) + (grough if np.ndim(grough) else grough) * gm
    metal = metal * (1 - gm) + gmetal * gm
    if kind == "garnet":  # a garnet cabochon set in each guard
        gem = np.zeros((h, w), f32)
        for cx, cy in ((58, 58), (w - 58, 58), (58, h - 58), (w - 58, h - 58)):
            gem = np.maximum(gem, np.clip(14 - np.hypot(x - cx, y - cy), 0, 1))
        height = height + H.dome(K.inner(gem), 14) * 0.18 * gem
        alb = alb * (1 - gem[..., None]) + np.array([0.55, 0.03, 0.08], f32) * gem[..., None]
        rough = rough * (1 - gem) + 0.05 * gem
        metal = metal * (1 - gem)
        em = em + np.array([0.5, 0.02, 0.05], f32) * ndimage.gaussian_filter(gem, 4)[..., None] * 0.6
    rgb = K.lit(height, alb, rough, metal, strength=1 / 5, detail=nrm, detail_k=0.55 * R["grain"], emissive=em)
    vign = np.clip(1 - 0.38 * (((x - w / 2) / (w * 0.7)) ** 2 + ((y - h / 2) / (h * 0.7)) ** 2), 0.55, 1)
    save(rgb * vign[..., None], body, f"RecCover{race}.png")


def covers():
    for race in RACES:
        cover(race)


def plate(race):
    R = RACES[race]
    w, h = 640, 110
    m = rrect(w, h, 10, 4)
    inner = rrect(w, h, 6, 14)
    col, nrm, rough, metal = metal_maps(R["tool"] if R["tool"] != "verdigris" else "brass", w, h, 220)
    if R["tool"] == "verdigris":
        col = col * np.array([0.75, 0.95, 0.80], f32)
    y, x = K.grid(w, h)
    screws = np.zeros((h, w), f32)
    slot = np.zeros((h, w), f32)
    for cx in (28, w - 28):
        rr = np.hypot(x - cx, y - h / 2)
        screws = np.maximum(screws, np.clip(10 - rr, 0, 1))
        slot = np.maximum(slot, (np.abs(x - cx) < 1.6) * (rr < 8))
    line = np.clip(inner - rrect(w, h, 5, 16), 0, 1)
    height = bevel(m, 10) * 0.25 - line * 0.01 + H.dome(K.inner(screws), 10) * 0.12 * screws - slot * 0.03
    rgb = K.lit(height, col, rough, np.full((h, w), metal, f32), strength=1 / 5, detail=nrm, detail_k=0.3)
    sh = shadow_of(m, 4, 0.55, 1, 3)
    save(*comp(np.zeros_like(rgb), sh, rgb, m), f"RecPlate{race}.png")


def plates():
    for race in RACES:
        plate(race)


# ================================================================ the parchment page (9-slice, slice 80)
def page():
    s = 768
    y, x = K.grid(s, s)
    e = np.minimum.reduce([x, y, s - 1 - x, s - 1 - y])
    deckle = K.noise((s, s), 5, 121) * 6 + K.noise((s, s), 24, 122) * 6
    sheet = np.clip((e - 8 - deckle) / 2.5, 0, 1)
    col, nrm, rough = parchment_maps(s, s, 123)
    col = col * (0.70 + 0.30 * np.clip(e / 70, 0, 1))[..., None] * np.array([1, 0.97, 0.92], f32)
    # a crimson double margin rule inside the left slice; a sepia head rule inside the top slice
    margin = np.exp(-((x - 58) / 1.1) ** 2) + np.exp(-((x - 64) / 0.8) ** 2) * 0.8
    head = np.exp(-((y - 66) / 0.9) ** 2) * (x > 70) * (x < s - 24)
    col = col * (1 - margin[..., None] * 0.6) + CRIMSON * margin[..., None] * 0.6
    col = col * (1 - head[..., None] * 0.4) + SEPIA * head[..., None] * 0.4
    height = (K.noise((s, s), 1.5, 124) - 0.5) * 0.004 + bevel(sheet, 10) * 0.01
    rgb = K.lit(height, col, rough, np.zeros((s, s), f32), strength=1 / 6, detail=nrm, detail_k=0.25)
    lum = rgb @ np.array([0.3, 0.59, 0.11], f32)
    rgb = rgb * (0.86 / max(1e-6, float(np.percentile(lum[sheet > 0.5], 70))))
    sh = shadow_of(sheet, 9, 0.6, 3, 6)
    save(*comp(np.zeros_like(rgb), sh, rgb, sheet), "RecPage.png")


# ================================================================ leather index tabs (9-slice, slice 40)
def tab(section, on):
    w, h = 360, 92
    y, x = K.grid(w, h)
    m = draw_mask(w, h, lambda d, k: (d.rounded_rectangle([0, 6 * k, (w - 6) * k, (h - 8) * k], 30 * k, fill=255),
                                       d.rectangle([0, 6 * k, 44 * k, (h - 8) * k], fill=255)))
    c = np.array(SECTIONS[section], f32) * (1.25 if on else 1.0)
    alb, nrm, rough = leather_maps(w, h, c, 1.4, 131)
    edge = np.clip(m - draw_mask(w, h, lambda d, k: (d.rounded_rectangle([0, 14 * k, (w - 14) * k, (h - 16) * k], 22 * k, fill=255),
                                                     d.rectangle([0, 14 * k, 44 * k, (h - 16) * k], fill=255))), 0, 1)
    fillet = np.clip(edge - np.clip(edge - draw_mask(w, h, lambda d, k: (d.rounded_rectangle([0, 10 * k, (w - 10) * k, (h - 12) * k], 26 * k, outline=255, width=3 * k))), 0, 1), 0, 1)
    gcol, gnrm, grough, gmetal = metal_maps("gilt", w, h, 160)
    height = bevel(m, 9) * 0.08 - fillet * 0.008
    alb = alb * (1 - fillet[..., None]) + gcol * fillet[..., None]
    rough = rough * (1 - fillet) + grough * fillet
    metal = fillet * gmetal
    stitch = draw_mask(w, h, lambda d, k: [d.line([(xx * k, 20 * k), ((xx + 9) * k, 20 * k)], fill=255, width=3 * k) for xx in range(56, w - 48, 16)]
                       + [d.line([(xx * k, (h - 22) * k), ((xx + 9) * k, (h - 22) * k)], fill=255, width=3 * k) for xx in range(56, w - 48, 16)], ss=2) * m
    alb = alb * (1 - stitch[..., None]) + np.array([0.78, 0.62, 0.34], f32) * stitch[..., None]
    height = height + stitch * 0.006
    if on:  # a gilt cap on the round end
        cap = np.clip(14 - np.hypot(x - (w - 40), y - h / 2 + 1), 0, 1)
        height = height + H.dome(K.inner(cap), 12) * 0.14 * cap
        alb = alb * (1 - cap[..., None]) + gcol * cap[..., None]
        rough = rough * (1 - cap) + grough * cap
        metal = np.maximum(metal, cap * gmetal)
    rgb = K.lit(height, alb, rough, metal, strength=1 / 5, detail=nrm, detail_k=0.5)
    sh = shadow_of(m, 6 if on else 3, 0.6 if on else 0.4, 2, 4)
    save(*comp(np.zeros_like(rgb), sh, rgb, m), f"RecTab{'On' if on else ''}{section}.png")


def tabs():
    for sec in SECTIONS:
        tab(sec, False)
        tab(sec, True)


# ================================================================ card, buttons, stamp
def card():
    s = 320
    y, x = K.grid(s, s)
    m = rrect(s, s, 8, 8)
    col, nrm, rough = parchment_maps(s, s, 151, 512)
    e = K.inner(m)
    col = col * (0.85 + 0.15 * np.clip(e / 30, 0, 1))[..., None]
    border = np.clip(m - rrect(s, s, 6, 14), 0, 1) * 0 + (np.abs(e - 14) < 0.9) * 1.0
    col = col * (1 - border[..., None] * 0.5) + SEPIA * border[..., None] * 0.5
    brackets = draw_mask(s, s, lambda d, k: [d.line(pts, fill=255, width=7 * k) for pts in (
        [(14 * k, 50 * k), (14 * k, 14 * k), (50 * k, 14 * k)], [((s - 50) * k, 14 * k), ((s - 14) * k, 14 * k), ((s - 14) * k, 50 * k)],
        [(14 * k, (s - 50) * k), (14 * k, (s - 14) * k), (50 * k, (s - 14) * k)], [((s - 50) * k, (s - 14) * k), ((s - 14) * k, (s - 14) * k), ((s - 14) * k, (s - 50) * k)])])
    gcol, _, grough, gmetal = metal_maps("gilt", s, s, 160)
    height = bevel(m, 5) * 0.02 + H.dome(K.inner(brackets), 3) * 0.1 * brackets
    col = col * (1 - brackets[..., None]) + gcol * brackets[..., None]
    rough = rough * (1 - brackets) + grough * brackets
    rgb = K.lit(height, col, rough, brackets * gmetal, strength=1 / 6, detail=nrm, detail_k=0.25)
    lum = rgb @ np.array([0.3, 0.59, 0.11], f32)
    paper = (m > 0.5) & (brackets < 0.1)
    rgb = rgb * (0.88 / max(1e-6, float(np.percentile(lum[paper], 65))))
    sh = shadow_of(m, 6, 0.5, 2, 4)
    save(*comp(np.zeros_like(rgb), sh, rgb, m), "RecCard.png")


def pill(w, h, fill_col, fill_rough, emissive_k, seed, pressed=False):
    outer = rrect(w, h, h // 2 - 2, 2)
    inn = rrect(w, h, h // 2 - 8, 8)
    rim = np.clip(outer - inn, 0, 1)
    gcol, gnrm, grough, gmetal = metal_maps("gilt", w, h, 160)
    y, x = K.grid(w, h)
    dome = bevel(inn, h // 3) * (0.16 if not pressed else -0.06) * inn
    height = bevel(outer, 6) * 0.22 * rim + dome
    col = gcol * rim[..., None] + fill_col * (1 - rim[..., None])
    rough = grough * rim + fill_rough * (1 - rim)
    metal = rim * gmetal
    em = fill_col * ndimage.gaussian_filter(inn, h / 5)[..., None] * emissive_k
    rgb = K.lit(height, col, rough, metal, strength=1 / 5, detail=gnrm, detail_k=(0.2 * rim)[..., None], emissive=em)
    if not pressed:
        rgb = rgb + (np.clip(1 - y / (h * 0.5), 0, 1) ** 2 * inn * 0.10)[..., None]
    sh = shadow_of(outer, 4 if not pressed else 2, 0.55, 0, 3 if not pressed else 1)
    return comp(np.zeros_like(rgb), sh, rgb, outer)


def buttons():
    w, h = 224, 72
    c = np.broadcast_to(CRIMSON * 1.25, (h, w, 3)).astype(f32) * (0.9 + 0.2 * K.noise((h, w), 6, 171)[..., None])
    save(*pill(w, h, c, np.full((h, w), 0.12, f32), 0.35, 171), "RecButton.png")
    save(*pill(w, h, c * 0.7, np.full((h, w), 0.18, f32), 0.15, 172, pressed=True), "RecButtonOn.png")


def ink_pill():
    w, h = 224, 72
    c = np.broadcast_to(np.array([0.06, 0.045, 0.05], f32), (h, w, 3)).astype(f32) * (0.85 + 0.3 * K.noise((h, w), 20, 181)[..., None])
    save(*pill(w, h, c, np.full((h, w), 0.14, f32), 0.0, 181), "RecInk.png")


def stamp():
    w, h = 320, 110
    outer = rrect(w, h, 14, 6)
    inner = rrect(w, h, 10, 17)
    ring = np.clip(outer - inner, 0, 1)
    grit = K.noise((h, w), 1.3, 161)
    ink = ring * np.clip(0.5 + grit * 0.8, 0, 1) * (K.noise((h, w), 10, 162) > 0.16)
    rgb = np.broadcast_to(RED_INK, (h, w, 3)).astype(f32) * (0.85 + 0.25 * grit[..., None])
    save(rgb, ink * 0.92, "RecStamp.png")


# ================================================================ medals, envelope, pips, close, glint
def medals():
    s = 256
    y, x = K.grid(s, s)
    cx, cy = s / 2, s * 0.61
    r = np.hypot(x - cx, y - cy)
    R = s * 0.33
    disc = np.clip(R - r, 0, 1)
    enamel = np.clip(R - 8 - r, 0, 1) - np.clip(R - 20 - r, 0, 1)
    field = np.clip(R - 20 - r, 0, 1)
    t = np.arctan2(y - cy, x - cx)
    gcol, gnrm, grough, gmetal = metal_maps("gilt", s, s, 128)
    beads = (np.cos(t * 48) * 0.5 + 0.5) ** 4 * np.clip(disc - np.clip(R - 7 - r, 0, 1), 0, 1) * 0.05
    burst = (np.cos(t * 28) * 0.5 + 0.5) * np.clip((r - R * 0.42) / (R * 0.25), 0, 1) * field * 0.012
    rib = draw_mask(s, s, lambda d, k: d.polygon([(74 * k, 0), (182 * k, 0), (154 * k, 112 * k), (128 * k, 94 * k), (102 * k, 112 * k)], fill=255))
    rib = rib * (1 - disc)
    stripes = ((np.abs(x - s / 2) % 26) < 8).astype(f32)
    rcol = (np.array([0.05, 0.04, 0.05], f32) * (1 - stripes[..., None]) + CRIMSON * 1.2 * stripes[..., None])
    groove = (np.sin(y * 1.7) * 0.5 + 0.5) * 0.003
    height = bevel(disc, 10) * 0.30 + beads + burst - enamel * 0.015 + (groove + bevel(rib, 3) * 0.04) * rib
    col = gcol * disc[..., None] + rcol * (1 - disc[..., None])
    col = col * (1 - enamel[..., None]) + CRIMSON * 1.4 * enamel[..., None]
    rough = grough * disc * (1 - enamel) + 0.08 * enamel + 0.6 * rib
    metal = gmetal * disc * (1 - enamel)
    rgb = K.lit(height, col, rough, metal, strength=1 / 5, detail=gnrm, detail_k=(0.25 * disc)[..., None])
    a = np.clip(disc + rib, 0, 1)
    sh = shadow_of(a, 5, 0.55, 2, 4)
    save(*comp(np.zeros_like(rgb), sh, rgb, a), "RecMedal.png")
    # still to earn: blind-tooled into parchment (a debossed ring and ribbon outline, no colour of its own)
    ring = (np.exp(-((r - R) / 1.8) ** 2) + np.exp(-((r - (R - 14)) / 1.3) ** 2) * 0.7)
    ribline = draw_mask(s, s, lambda d, k: d.line([(74 * k, 0), (102 * k, 112 * k), (128 * k, 94 * k), (154 * k, 112 * k), (182 * k, 0)], fill=255, width=4 * k)) * (1 - disc)
    deb = np.clip(ring + ribline, 0, 1)
    pc = np.broadcast_to(PARCH, (s, s, 3)).astype(f32)
    rgb2 = K.lit(-deb * 0.03, pc, np.full((s, s), 0.8, f32), np.zeros((s, s), f32), strength=1 / 4)
    dark = np.clip(1 - (rgb2 @ np.array([0.3, 0.59, 0.11], f32)) / 0.75, 0, 1)
    save(np.broadcast_to(SEPIA, (s, s, 3)).astype(f32), np.clip(deb * 0.55 + dark * deb * 0.5, 0, 1), "RecMedalDim.png")


def envelope():
    s = 256
    y, x = K.grid(s, s)
    body = draw_mask(s, s, lambda d, k: d.rounded_rectangle([8 * k, 44 * k, 248 * k, 214 * k], 8 * k, fill=255))
    border = np.clip(body - draw_mask(s, s, lambda d, k: d.rounded_rectangle([18 * k, 54 * k, 238 * k, 204 * k], 4 * k, fill=255)), 0, 1)
    flap = draw_mask(s, s, lambda d, k: d.polygon([(8 * k, 46 * k), (248 * k, 46 * k), (128 * k, 140 * k)], fill=255))
    flapline = draw_mask(s, s, lambda d, k: d.line([(8 * k, 46 * k), (128 * k, 140 * k), (248 * k, 46 * k)], fill=255, width=8 * k)) * body
    col, nrm, rough = parchment_maps(s, s, 201, 384)
    col = col * (1 - flap[..., None] * 0.06)
    blk = np.clip(border + flapline, 0, 1)
    col = col * (1 - blk[..., None]) + np.array([0.05, 0.04, 0.05], f32) * blk[..., None]
    r = np.hypot(x - 128, y - 140)
    btn = np.clip(16 - r, 0, 1)
    gcol, _, grough, gmetal = metal_maps("gilt", s, s, 128)
    string = draw_mask(s, s, lambda d, k: (d.line([(112 * k, 132 * k), (146 * k, 150 * k), (114 * k, 152 * k), (144 * k, 130 * k)], fill=255, width=4 * k),
                                            d.line([(132 * k, 154 * k), (154 * k, 196 * k), (146 * k, 214 * k)], fill=255, width=4 * k)))
    col = col * (1 - btn[..., None]) + gcol * btn[..., None]
    col = col * (1 - string[..., None]) + CRIMSON * 1.3 * string[..., None]
    height = bevel(body, 5) * 0.03 + bevel(flap, 4) * 0.03 * flap + H.dome(K.inner(btn), 14) * 0.2 * btn + string * 0.02
    rough = rough * (1 - btn) + grough * btn
    rgb = K.lit(height, col, rough, btn * gmetal, strength=1 / 5, detail=nrm, detail_k=0.2)
    a = np.clip(body + btn, 0, 1)
    sh = shadow_of(a, 5, 0.5, 2, 4)
    save(*comp(np.zeros_like(rgb), sh, rgb, a), "RecEnvelope.png")


def pips():
    s = 64
    y, x = K.grid(s, s)
    r = np.hypot(x - s / 2 + 0.5, y - s / 2 + 0.5)
    ring = np.clip(20 - r, 0, 1) - np.clip(14 - r, 0, 1)
    rgb = K.lit(-ring * 0.04, np.broadcast_to(PARCH, (s, s, 3)).astype(f32), np.full((s, s), 0.8, f32), np.zeros((s, s), f32), strength=1 / 4)
    save(np.broadcast_to(SEPIA, (s, s, 3)).astype(f32), np.clip(ring, 0, 1) * 0.7, "RecPip.png")
    disc = np.clip(22 - r, 0, 1)
    gcol, gnrm, grough, gmetal = metal_maps("gilt", s, s, 64)
    rgb2 = K.lit(H.dome(K.inner(disc), 20) * 0.35, gcol, grough, disc * gmetal, strength=1 / 4)
    sh = shadow_of(disc, 2, 0.5, 1, 2)
    save(*comp(np.zeros_like(rgb2), sh, rgb2, disc), "RecPipOn.png")


def close():
    s = 128
    y, x = K.grid(s, s)
    r = np.hypot(x - s / 2 + 0.5, y - s / 2 + 0.5)
    disc = np.clip(s / 2 - 4 - r, 0, 1)
    ring = disc - np.clip(s / 2 - 16 - r, 0, 1)
    icol, inrm, irough, imetal = metal_maps("iron", s, s, 128)
    gcol, gnrm, grough, gmetal = metal_maps("gilt", s, s, 128)
    boss = np.clip(s / 2 - 16 - r, 0, 1)
    col = icol * ring[..., None] + gcol * boss[..., None]
    rough = irough * ring + grough * boss
    height = H.dome(K.inner(disc), 12) * 0.25 + H.dome(K.inner(boss), 30) * 0.15 * boss
    rgb = K.lit(height, col, rough, ring * imetal + boss * gmetal, strength=1 / 4, detail=gnrm, detail_k=0.2)
    sh = shadow_of(disc, 4, 0.55, 1, 3)
    save(*comp(np.zeros_like(rgb), sh, rgb, disc), "RecClose.png")


def glint():
    w, h = 256, 64
    y, x = K.grid(w, h)
    d = (x - w / 2) + (y - h / 2) * 0.6
    a = np.exp(-(d / 22) ** 2) * 0.85 + np.exp(-(d / 5) ** 2) * 0.4
    save(np.ones((h, w, 3), f32) * np.array([1.0, 0.95, 0.82], f32), np.clip(a, 0, 1), "RecGlint.png")


# ================================================================ icons (white embossed; tinted in game)
def icon_mask(name):
    s = 256

    def m(fn):
        return K.mask((s, s), fn, ss=4)

    W = 22
    if name == "Student":  # a head and shoulders in a frame-less bust
        return m(lambda d, k: (d.ellipse([84 * k, 34 * k, 172 * k, 122 * k], fill=255),
                               d.pieslice([40 * k, 128 * k, 216 * k, 300 * k], 180, 360, fill=255)))
    if name == "Academics":  # an open book
        def f(d, k):
            d.polygon([(24 * k, 70 * k), (120 * k, 86 * k), (120 * k, 210 * k), (24 * k, 192 * k)], fill=255)
            d.polygon([(136 * k, 86 * k), (232 * k, 70 * k), (232 * k, 192 * k), (136 * k, 210 * k)], fill=255)
        a = m(f)
        lines = m(lambda d, k: [d.line([(44 * k, (102 + i * 26) * k), (102 * k, (112 + i * 26) * k)], fill=255, width=8 * k) for i in range(3)]
                  + [d.line([(154 * k, (112 + i * 26) * k), (212 * k, (102 + i * 26) * k)], fill=255, width=8 * k) for i in range(3)])
        return np.clip(a - lines * 0.85, 0, 1)
    if name == "Attendance":  # a clock face with hands (the register's bell time)
        def f(d, k):
            d.ellipse([34 * k, 34 * k, 222 * k, 222 * k], outline=255, width=W * k)
            d.line([(128 * k, 128 * k), (128 * k, 70 * k)], fill=255, width=(W - 2) * k)
            d.line([(128 * k, 128 * k), (172 * k, 152 * k)], fill=255, width=(W - 2) * k)
            d.ellipse([114 * k, 114 * k, 142 * k, 142 * k], fill=255)
        return m(f)
    if name == "Athletics":  # a pennant on a pole
        return m(lambda d, k: (d.rounded_rectangle([46 * k, 26 * k, 66 * k, 232 * k], 8 * k, fill=255),
                               d.polygon([(66 * k, 34 * k), (222 * k, 84 * k), (66 * k, 136 * k)], fill=255)))
    if name == "Combat":  # a raised fist (four knuckles and a thumb)
        def f(d, k):
            for i in range(4):
                d.rounded_rectangle([(52 + i * 40) * k, 52 * k, (88 + i * 40) * k, 132 * k], 16 * k, fill=255)
            d.rounded_rectangle([52 * k, 104 * k, 208 * k, 214 * k], 30 * k, fill=255)
            d.rounded_rectangle([28 * k, 120 * k, 112 * k, 160 * k], 18 * k, fill=255)
        return m(f)
    if name == "Factions":  # two crossed banners
        def f(d, k):
            d.line([(54 * k, 226 * k), (176 * k, 30 * k)], fill=255, width=16 * k)
            d.line([(202 * k, 226 * k), (80 * k, 30 * k)], fill=255, width=16 * k)
            d.polygon([(170 * k, 40 * k), (232 * k, 66 * k), (190 * k, 104 * k), (150 * k, 72 * k)], fill=255)
            d.polygon([(86 * k, 40 * k), (24 * k, 66 * k), (66 * k, 104 * k), (106 * k, 72 * k)], fill=255)
        return m(f)
    if name == "Paths":  # a signpost with two arms
        return m(lambda d, k: (d.rounded_rectangle([116 * k, 30 * k, 140 * k, 230 * k], 8 * k, fill=255),
                               d.polygon([(140 * k, 54 * k), (214 * k, 54 * k), (236 * k, 80 * k), (214 * k, 106 * k), (140 * k, 106 * k)], fill=255),
                               d.polygon([(116 * k, 120 * k), (42 * k, 120 * k), (20 * k, 146 * k), (42 * k, 172 * k), (116 * k, 172 * k)], fill=255)))
    if name == "Honours":  # a medal on a V ribbon
        return m(lambda d, k: (d.polygon([(78 * k, 22 * k), (124 * k, 22 * k), (140 * k, 104 * k), (96 * k, 104 * k)], fill=255),
                               d.polygon([(178 * k, 22 * k), (132 * k, 22 * k), (116 * k, 104 * k), (160 * k, 104 * k)], fill=255),
                               d.ellipse([66 * k, 106 * k, 190 * k, 230 * k], fill=255)))
    if name == "Entries":  # a notebook with a pen across it
        def f(d, k):
            d.rounded_rectangle([46 * k, 30 * k, 190 * k, 226 * k], 12 * k, fill=255)
        a = m(f)
        cut = m(lambda d, k: [d.line([(78 * k, (78 + i * 34) * k), (164 * k, (78 + i * 34) * k)], fill=255, width=9 * k) for i in range(4)]
                + [d.rounded_rectangle([46 * k, 30 * k, 64 * k, 226 * k], 4 * k, fill=255)])
        pen = m(lambda d, k: d.line([(150 * k, 214 * k), (232 * k, 98 * k)], fill=255, width=20 * k))
        return np.clip(np.clip(a - cut * 0.85, 0, 1) + pen, 0, 1)
    if name == "Might":  # a hammer
        return m(lambda d, k: (d.rounded_rectangle([46 * k, 40 * k, 210 * k, 104 * k], 14 * k, fill=255),
                               d.rounded_rectangle([114 * k, 96 * k, 142 * k, 230 * k], 10 * k, fill=255)))
    if name == "Grit":  # a heater shield
        return m(lambda d, k: d.polygon([(44 * k, 40 * k), (212 * k, 40 * k), (212 * k, 120 * k), (128 * k, 228 * k), (44 * k, 120 * k)], fill=255))
    if name == "Wits":  # an eye
        def f(d, k):
            d.ellipse([22 * k, 70 * k, 234 * k, 186 * k], fill=255)
        a = m(f)
        iris = m(lambda d, k: d.ellipse([92 * k, 92 * k, 164 * k, 164 * k], fill=255))
        pupil = m(lambda d, k: d.ellipse([112 * k, 112 * k, 144 * k, 144 * k], fill=255))
        ring = m(lambda d, k: d.ellipse([62 * k, 86 * k, 194 * k, 170 * k], fill=255))
        return np.clip(a - ring + iris - pupil, 0, 1)
    if name == "Social":  # two figures
        def f(d, k):
            d.ellipse([46 * k, 46 * k, 110 * k, 110 * k], fill=255)
            d.pieslice([18 * k, 118 * k, 138 * k, 250 * k], 180, 360, fill=255)
            d.ellipse([146 * k, 46 * k, 210 * k, 110 * k], fill=255)
            d.pieslice([118 * k, 118 * k, 238 * k, 250 * k], 180, 360, fill=255)
        return m(f)
    if name == "Supernatural":  # a crescent moon with an eye-like star
        a = m(lambda d, k: d.ellipse([34 * k, 30 * k, 226 * k, 222 * k], fill=255))
        b = m(lambda d, k: d.ellipse([92 * k, 10 * k, 262 * k, 180 * k], fill=255))
        star = m(lambda d, k: d.polygon([(176 * k, 150 * k), (186 * k, 178 * k), (214 * k, 186 * k), (186 * k, 196 * k), (176 * k, 224 * k), (166 * k, 196 * k), (138 * k, 186 * k), (166 * k, 178 * k)], fill=255))
        return np.clip(a - b, 0, 1) + star * (1 - np.clip(a - b, 0, 1))
    if name == "Story":  # a quill
        def f(d, k):
            d.polygon([(214 * k, 26 * k), (232 * k, 44 * k), (110 * k, 176 * k), (78 * k, 150 * k)], fill=255)
            d.polygon([(214 * k, 26 * k), (150 * k, 52 * k), (90 * k, 140 * k)], fill=255)
            d.line([(92 * k, 166 * k), (36 * k, 226 * k)], fill=255, width=12 * k)
        return m(f)
    if name == "Secret":  # a padlock
        def f(d, k):
            d.arc([74 * k, 30 * k, 182 * k, 138 * k], 180, 360, fill=255, width=W * k)
            d.line([(85 * k, 84 * k), (85 * k, 120 * k)], fill=255, width=W * k)
            d.line([(171 * k, 84 * k), (171 * k, 120 * k)], fill=255, width=W * k)
            d.rounded_rectangle([50 * k, 112 * k, 206 * k, 228 * k], 18 * k, fill=255)
        a = m(f)
        hole = m(lambda d, k: (d.ellipse([114 * k, 144 * k, 142 * k, 172 * k], fill=255), d.rectangle([122 * k, 160 * k, 134 * k, 200 * k], fill=255)))
        return np.clip(a - hole, 0, 1)
    if name == "Close":
        return m(lambda d, k: (d.line([(64 * k, 64 * k), (192 * k, 192 * k)], fill=255, width=(W + 6) * k), d.line([(192 * k, 64 * k), (64 * k, 192 * k)], fill=255, width=(W + 6) * k)))
    if name == "Plus":
        return m(lambda d, k: (d.rounded_rectangle([114 * k, 40 * k, 142 * k, 216 * k], 12 * k, fill=255), d.rounded_rectangle([40 * k, 114 * k, 216 * k, 142 * k], 12 * k, fill=255)))
    if name == "Check":
        return m(lambda d, k: d.line([(46 * k, 134 * k), (104 * k, 192 * k), (214 * k, 70 * k)], fill=255, width=(W + 8) * k, joint="curve"))
    raise ValueError(name)


ICONS = ["Student", "Academics", "Attendance", "Athletics", "Combat", "Factions", "Paths", "Honours", "Entries",
         "Might", "Grit", "Wits", "Social", "Supernatural", "Story", "Secret", "Close", "Plus", "Check"]


def icons():
    for name in ICONS + [f"Race{r}" for r in RACES]:
        a = emblem_mask(name[4:]) if name.startswith("Race") else icon_mask(name)
        height = H.dome(K.inner(a), 7) * 0.30
        alb = np.full(a.shape + (3,), 0.93, f32)
        rgb = K.lit(height, alb, np.full(a.shape, 0.35, f32), np.zeros(a.shape, f32), strength=1 / 3.2, ao_k=(6, 3))
        lum = rgb @ np.array([0.3, 0.59, 0.11], f32)
        lum = np.clip(0.90 + (lum - lum[a > 0.5].mean()) * 0.6, 0.72, 1.0) if (a > 0.5).any() else lum
        out_rgb = np.repeat(lum[..., None], 3, -1)
        shadow = ndimage.gaussian_filter(a, 5) * 0.45
        rgb2, a2 = comp(np.zeros_like(out_rgb), shadow, out_rgb, a)
        save(rgb2, a2, f"RecIcon{name}.png")




# ================================================================ previews
def _tint(im, c):
    arr = np.asarray(im).astype(f32) / 255
    arr[..., :3] *= np.array(c, f32)
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA")


def _menu(race, scale=1.0):
    def load(n):
        return Image.open(OUT / n).convert("RGBA")
    W_, H_ = 1500, 900
    bg = Image.new("RGBA", (W_, H_), (14, 10, 14, 255))
    bg.alpha_composite(load(f"RecCover{race}.png").resize((1440, 855)), (30, 22))
    pl = load(f"RecPlate{race}.png").resize((470, 80))
    bg.alpha_composite(pl, (92, 60))
    d = ImageDraw.Draw(bg)
    ink = (34, 22, 14, 255)
    d.text((126, 78), "PERMANENT RECORD", font=ImageFont.truetype(FONT_TYPE, 34), fill=(30, 22, 16, 255) if race != "Vampire" else (230, 230, 236, 255))
    for i, name in enumerate(SECTIONS):
        on = name == "Honours"
        t = load(f"RecTab{'On' if on else ''}{name}.png").resize((250, 64))
        bg.alpha_composite(t, (76 if not on else 92, 196 + i * 70))
        ic = _tint(load(f"RecIcon{name}.png").resize((34, 34)), (1.0, 0.86, 0.55))
        bg.alpha_composite(ic, (98 if not on else 114, 211 + i * 70))
        d.text((142 if not on else 158, 212 + i * 70), name, font=ImageFont.truetype(FONT_T, 23), fill=(250, 236, 205, 255))
    bg.alpha_composite(load("RecPage.png").resize((1060, 680)), (346, 180))
    d.text((440, 212), "Honours", font=ImageFont.truetype(FONT_T, 38), fill=ink)
    d.text((442, 260), "What the school has recognised you for. 9 of 30 earned.", font=ImageFont.truetype(FONT_T, 19), fill=(92, 66, 46, 255))
    d.text((442, 312), "ACADEMICS", font=ImageFont.truetype(FONT_T, 18), fill=(120, 20, 26, 255))
    for j, nm in enumerate(["RecMedal.png", "RecMedal.png", "RecMedalDim.png", "RecMedalDim.png", "RecEnvelope.png"]):
        md = load(nm).resize((128, 128))
        X = 440 + j * 186
        bg.alpha_composite(md, (X, 340))
        if nm == "RecMedal.png":
            bg.alpha_composite(_tint(load(["RecIconAcademics.png", "RecIconAttendance.png"][j]).resize((42, 42)), (0.36, 0.22, 0.08)), (X + 43, 340 + 58))
        label = ["First Pass", "Present", "Mastery", "Honor Roll", "Sealed"][j]
        d.text((X + 4, 474), label, font=ImageFont.truetype(FONT_T, 18), fill=ink)
    st = load("RecStamp.png").resize((150, 52))
    bg.alpha_composite(st, (446, 506))
    d.text((476, 518), "EARNED", font=ImageFont.truetype(FONT_TYPE, 22), fill=(150, 20, 26, 255))
    cd = load("RecCard.png").resize((330, 220))
    bg.alpha_composite(cd, (446, 590))
    d.text((476, 616), "Academic", font=ImageFont.truetype(FONT_T, 24), fill=ink)
    d.text((476, 650), "Honor Student", font=ImageFont.truetype(FONT_T, 20), fill=(120, 20, 26, 255))
    for k2 in range(4):
        bg.alpha_composite(load("RecPipOn.png" if k2 < 3 else "RecPip.png").resize((26, 26)), (478 + k2 * 32, 690))
    d.text((476, 730), "Next: Academic Elite", font=ImageFont.truetype(FONT_T, 17), fill=(92, 66, 46, 255))
    bg.alpha_composite(load("RecButton.png").resize((170, 56)), (1180, 760))
    d.text((1222, 774), "Equip", font=ImageFont.truetype(FONT_T, 22), fill=(255, 240, 220, 255))
    bg.alpha_composite(load("RecInk.png").resize((170, 56)), (990, 760))
    d.text((1036, 774), "Filter", font=ImageFont.truetype(FONT_T, 22), fill=(240, 220, 170, 255))
    bg.alpha_composite(load("RecClose.png").resize((60, 60)), (1400, 40))
    bg.alpha_composite(_tint(load("RecIconClose.png").resize((30, 30)), (0.2, 0.12, 0.05)), (1415, 55))
    return bg


def preview():
    _menu("Human").save(HERE / "preview_record.png")
    sheet = Image.new("RGBA", (1500, 900), (14, 10, 14, 255))
    for i, race in enumerate(RACES):
        c = Image.open(OUT / f"RecCover{race}.png").convert("RGBA").resize((480, 285))
        X, Y = 10 + (i % 3) * 495, 20 + (i // 3) * 440
        sheet.alpha_composite(c, (X, Y))
        sheet.alpha_composite(Image.open(OUT / f"RecPlate{race}.png").convert("RGBA").resize((200, 34)), (X + 20, Y + 14))
        ImageDraw.Draw(sheet).text((X + 6, Y + 300), race, font=ImageFont.truetype(FONT_T, 30), fill=(235, 220, 190, 255))
        ic = _tint(Image.open(OUT / f"RecIconRace{race}.png").convert("RGBA").resize((60, 60)), (0.95, 0.85, 0.6))
        sheet.alpha_composite(ic, (X + 140, Y + 296))
    for i, name in enumerate(ICONS):
        ic = _tint(Image.open(OUT / f"RecIcon{name}.png").convert("RGBA").resize((44, 44)), (0.95, 0.85, 0.6))
        sheet.alpha_composite(ic, (20 + i * 76, 800))
    sheet.save(HERE / "preview_record_covers.png")
    print("   preview_record.png, preview_record_covers.png")


ALL = {"covers": covers, "plates": plates, "page": page, "tabs": tabs, "card": card, "buttons": buttons, "ink": ink_pill,
       "stamp": stamp, "medals": medals, "envelope": envelope, "pips": pips, "close": close, "glint": glint,
       "icons": icons, "preview": preview}

if __name__ == "__main__":
    for n in (sys.argv[1:] or list(ALL)):
        print(n)
        ALL[n]()
