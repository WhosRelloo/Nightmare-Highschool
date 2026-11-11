"""PBR HUD art for the everyday-carry kit (Nightmare Highschool), baked to images.

The same pipeline as the health bar and posture rail (make_health_pbr.shade: GGX specular, Lambert diffuse, the warm key,
cool fill and candle rim, an environment reflection, AO from the height, the school's PBR detail maps) and the same icon
family as the phone apps (make_app_icons.Icon: greyscale relief, tinted in game).

Pieces (art/ui/hud/out/kit/):
  CompassBezel.png   512   the brass hunter-case bezel seen from above: knurled rim, engraved degree ticks, four studs
                           (a crimson-enamel one at north). The middle is transparent: the dial card shows through.
  CompassFace.png    512   the dial card: ivory enamel printed with the rose, the degrees and N E S W (the 3D
                           compass's own dial print). The HUD turns it so N points to world north.
  CompassNeedle.png  512   the needle: crimson enamel north with a gilt edge, blued-steel south, a brass jewel hub.
                           The HUD turns it to the target.
  CompassGlass.png   512   the crystal: soft highlights and a rim shadow (drawn over the needle).
  KitPlate.png       768x160  an ink-enamel plate in a brass frame with corner rivets: the compass label, the chips
                           (9-slice: SliceCenter 84, 44, 684, 116).
  CardHud.png        840x220  the timetable card in hand: ivory card, crimson header band, gilt rule, brass corners,
                           a ribbon through an eyelet. The HUD writes the lines on it.
  MapSheet.png       2048x1280  the campus map's sheet: aged paper with deckled edges, fold creases, foxing, an inked
                           double border with crimson corner squares, a title cartouche, a compass rose and a scale
                           bar. The middle is left clear for the places the HUD draws.
  MapHatch.png       256   tile: ink hatching (buildings).      MapStipple.png  256  tile: grass stipple (fields)
  MapYou.png         256   the "you are here" mark: a crimson ink arrow in an ink ring (points up; the HUD turns it)
  MapPin.png         256   a brass map pin with a crimson glass head (its point at the bottom centre)
  Icon<Name>.png     256   chip icons, greyscale relief (tinted in game): Oil, Cup, Biscuit, Bandage, Pass, Flame,
                           Frost, Heart, Keys, Book
  FrostEdge.png      1024x576  frost ferns creeping in from the screen edges (white, alpha). InkEdge.png  ink bleed.
  preview_*.png            the pieces assembled like the HUD (for review)

  python make_kit_ui.py [piece ...]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import make_health_pbr as H

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "kit"
OUT.mkdir(parents=True, exist_ok=True)
PRINTS = Path("E:/NH-Work/qol/prints")
f32 = np.float32
FONT_B = "C:/Windows/Fonts/timesbd.ttf"
FONT_I = "C:/Windows/Fonts/georgiai.ttf"
FONT_G = "C:/Windows/Fonts/georgiab.ttf"


# ================================================================ helpers
def grid(w, h):
    return np.mgrid[0:h, 0:w].astype(f32)


def noise(shape, sigma, seed):
    r = np.random.default_rng(seed).standard_normal(shape).astype(f32)
    n = ndimage.gaussian_filter(r, sigma, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-8)


def inner(m):
    return ndimage.distance_transform_edt(m > 0.5).astype(f32)


def mask(size, fn, ss=3):
    """draw with fn(draw, scale) on a supersampled L image -> float mask"""
    w, h = size
    im = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(im), ss)
    return np.array(im.resize((w, h), Image.BOX), f32) / 255.0


def save(rgb, alpha, name, size=None):
    a = np.clip(alpha, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), "RGBA")
    if size:
        img = img.resize(size, Image.LANCZOS)
    img.save(OUT / name, optimize=True)
    print("  ", name, img.size)
    return img


def lit(height, albedo_srgb, rough, metal, strength=1 / 7.5, detail=None, detail_k=0.0, emissive=None, ao_k=(10, 5)):
    """shade a coloured height field (albedo in sRGB)"""
    S = max(height.shape)
    hh = ndimage.gaussian_filter(height, 0.8)
    N = H.normals_from(hh * S * 0.5, strength, detail, detail_k)
    ao = H.ao_from(hh, ao_k[0], ao_k[1]) * H.ao_from(hh, 3, 9)
    return H.shade(H.srgb_to_lin(np.clip(albedo_srgb, 0, 1)).astype(f32), N, np.clip(rough, 0.05, 1), np.clip(metal, 0, 1), ao, emissive)


def tile_map(name, kind, size, period):
    return H.load_map(name, kind, size, period)


BRASS = np.array([0.80, 0.60, 0.30], f32)
BRASS_OLD = np.array([0.62, 0.45, 0.22], f32)
GILT = np.array([0.93, 0.74, 0.36], f32)
IVORY = np.array([0.90, 0.85, 0.74], f32)
CRIMSON = np.array([0.42, 0.06, 0.10], f32)
INK = np.array([0.10, 0.08, 0.08], f32)
STEEL = np.array([0.16, 0.18, 0.24], f32)


def brass_maps(w, h, period=256, tint=(1, 1, 1)):
    col = tile_map("Brass", "color", (w, h), period)
    rough = tile_map("Brass", "rough", (w, h), period)[..., 0]
    nrm = tile_map("Brass", "normal", (w, h), period) * 2 - 1
    return col * np.array(tint, f32), rough, nrm


# ================================================================ the compass
def compass():
    S = 1024
    yy, xx = grid(S, S)
    cx = cy = S / 2
    r = np.hypot(xx - cx, yy - cy)
    th = np.arctan2(yy - cy, xx - cx)
    # ---- bezel
    R0, R1 = 372, 500
    ring = np.clip(np.minimum(r - R0, R1 - r) + 0.5, 0, 1).astype(f32)
    d = np.clip(np.minimum(r - R0, R1 - r), 0, None)
    h = 0.30 + 0.16 * H.dome(d, 30)
    knurl = (r > 468) & (r < 500)
    h += knurl * (0.035 * np.cos(th * 144)) * np.clip((r - 468) / 10, 0, 1)
    # the inner lip (where the crystal seats) steps down
    lip = (r > R0) & (r < 392)
    h -= lip * 0.07
    # engraved degree ticks on the bezel top
    deg = (np.degrees(th) + 450) % 360
    for step, r0, w in ((10, 408, 2.2), (30, 400, 3.2)):
        k = np.abs(((deg + step / 2) % step) - step / 2) * (math.pi / 180) * r
        tick = (k < w) & (r > r0) & (r < 452)
        h -= tick * 0.05
    # four studs, the north one crimson enamel
    alb = np.zeros((S, S, 3), f32)
    bc, brough, bn = brass_maps(S, S, 320, (1.02, 0.95, 0.85))
    alb[:] = bc * 0.9 + BRASS * 0.25
    rough = np.clip(brough * 0.7 + 0.08, 0.1, 0.8)
    metal = np.full((S, S), 0.92, f32)
    for k, a in enumerate((-90, 0, 90, 180)):
        ar = math.radians(a)
        sx, sy = cx + 432 * math.cos(ar), cy + 432 * math.sin(ar)
        rd = np.hypot(xx - sx, yy - sy)
        stud = np.clip(24 - rd, 0, 1)
        h = np.maximum(h, (0.42 + 0.14 * H.dome(np.clip(24 - rd, 0, None), 24)) * (rd < 24))
        if k == 0:
            gem = rd < 15
            alb[gem] = CRIMSON * 1.4
            rough[gem] = 0.12
            metal[gem] = 0.0
    alb[lip] *= 0.7
    rgb = lit(h, alb, rough, metal, detail=bn, detail_k=0.25)
    save(rgb, ring * (r > R0 - 1), "CompassBezel.png", (512, 512))

    # ---- dial card: the 3D compass's printed dial, as enamel with raised ink
    dial = Image.open(PRINTS / "compass_dial.png").convert("RGB").resize((2 * R0 + 12, 2 * R0 + 12), Image.LANCZOS)
    card = np.zeros((S, S, 3), f32) + IVORY
    o = int(cx - dial.size[0] / 2)
    card[o:o + dial.size[1], o:o + dial.size[0]] = np.array(dial, f32) / 255
    lum = card.mean(-1)
    inkm = np.clip((0.55 - lum) * 4, 0, 1)
    disc = np.clip(R0 + 6 - r, 0, 1)
    hd = 0.20 + 0.03 * H.dome(np.clip(R0 + 6 - r, 0, None), 60) + inkm * 0.012
    rgb = lit(hd, card, 0.32 - inkm * 0.1, np.zeros((S, S), f32), strength=1 / 5)
    save(rgb, disc, "CompassFace.png", (512, 512))

    # ---- needle (points up)
    def nd(dr, s):
        L = 330
        dr.polygon([(cx * s, (cy - L) * s), ((cx + 34) * s, cy * s), (cx * s, (cy + 12) * s), ((cx - 34) * s, cy * s)], fill=255)
    def sd(dr, s):
        L = 280
        dr.polygon([(cx * s, (cy + L) * s), ((cx + 30) * s, cy * s), (cx * s, (cy - 12) * s), ((cx - 30) * s, cy * s)], fill=255)
    north = mask((S, S), nd)
    south = mask((S, S), sd) * (1 - north)
    hub = (np.hypot(xx - cx, yy - cy) < 40).astype(f32)
    jewel = (np.hypot(xx - cx, yy - cy) < 20).astype(f32)
    hn = 0.25 + 0.10 * H.dome(inner(north), 18)
    # a ridge down the needle's spine
    hn += north * 0.05 * np.clip(1 - np.abs(xx - cx) / 30, 0, 1)
    hs = 0.24 + 0.09 * H.dome(inner(south), 16) + south * 0.04 * np.clip(1 - np.abs(xx - cx) / 26, 0, 1)
    hh = north * hn + south * hs
    hh = np.maximum(hh, hub * (0.40 + 0.12 * H.dome(np.clip(40 - np.hypot(xx - cx, yy - cy), 0, None), 40)))
    alb = np.zeros((S, S, 3), f32)
    edge = (inner(north) < 7) & (north > 0.5)
    alb[north > 0.5] = CRIMSON * 1.25
    alb[edge] = GILT
    alb[south > 0.5] = STEEL
    alb[hub > 0.5] = BRASS
    alb[jewel > 0.5] = CRIMSON * 1.6
    rough = np.where(north > 0.5, 0.14, np.where(south > 0.5, 0.28, 0.25)).astype(f32)
    rough[edge] = 0.2
    metal = np.where(south > 0.5, 0.9, 0.0).astype(f32)
    metal[edge] = 1.0
    metal[(hub > 0.5) & (jewel < 0.5)] = 1.0
    rgb = lit(hh, alb, rough, metal, strength=1 / 6)
    a = np.clip(north + south + hub, 0, 1)
    # a soft drop shadow under the needle so it lifts off the card
    sh = ndimage.gaussian_filter(np.roll(np.roll(a, 14, 0), 8, 1), 8) * 0.55
    out_a = np.clip(a + sh * (1 - a), 0, 1)
    out_rgb = rgb * a[..., None] / np.maximum(out_a[..., None], 1e-4)
    save(out_rgb, out_a, "CompassNeedle.png", (512, 512))

    # ---- crystal
    g = np.zeros((S, S), f32)
    rim = np.clip((r - (R0 - 40)) / 40, 0, 1) * (r < R0 + 4)
    spec = np.exp(-(((xx - cx + 140) / 120) ** 2 + ((yy - cy + 170) / 70) ** 2))
    arc = np.exp(-((r - (R0 - 30)) / 10) ** 2) * np.clip(-np.sin(th + 0.6), 0, 1)
    glow = np.clip(spec * 0.85 + arc * 0.5, 0, 1)
    rgb = np.dstack([np.ones((S, S), f32)] * 3)
    rgb[..., :] *= np.where(glow[..., None] > 0.02, 1.0, 0.0) + 0.0
    alpha = np.clip(glow * 0.75 + rim * 0.25, 0, 1) * (r < R0 + 4)
    rgb = np.where((rim[..., None] > glow[..., None]), np.array([0.02, 0.02, 0.03], f32), np.array([1, 0.97, 0.92], f32))
    save(rgb, alpha, "CompassGlass.png", (512, 512))


# ================================================================ the plate (9-slice) and the card
def plate():
    W, Hh = 1536, 320
    yy, xx = grid(W, Hh)
    def outer(dr, s):
        dr.polygon([(20 * s, 160 * s), (80 * s, 20 * s), ((W - 80) * s, 20 * s), ((W - 20) * s, 160 * s), ((W - 80) * s, 300 * s), (80 * s, 300 * s)], fill=255)
    def inn(dr, s):
        dr.polygon([(64 * s, 160 * s), (108 * s, 56 * s), ((W - 108) * s, 56 * s), ((W - 64) * s, 160 * s), ((W - 108) * s, 264 * s), (108 * s, 264 * s)], fill=255)
    mo, mi = mask((W, Hh), outer), mask((W, Hh), inn)
    frame = mo * (1 - mi)
    bc, brough, bn = brass_maps(W, Hh, 256, (1.0, 0.92, 0.8))
    h = frame * (0.30 + 0.14 * H.dome(inner(frame), 14)) + mi * (0.18 + 0.01 * noise((Hh, W), 3, 2))
    # a fine engraved line on the frame
    line = (np.abs(inner(mo) - 22) < 2.0) & (frame > 0.5)
    h -= line * 0.04
    alb = np.zeros((Hh, W, 3), f32)
    alb[:] = bc * 0.85
    enamel = mi > 0.5
    alb[enamel] = np.array([0.06, 0.05, 0.07], f32) + noise((Hh, W), 6, 5)[enamel][:, None] * 0.03
    rough = np.where(enamel, 0.22, np.clip(brough * 0.7 + 0.1, 0.1, 0.8)).astype(f32)
    metal = np.where(enamel, 0.0, 0.9).astype(f32)
    for x in (110, W - 110):
        for y in (40, Hh - 40):
            rd = np.hypot(xx - x, yy - y)
            h = np.maximum(h, (rd < 12) * (0.46 + 0.1 * H.dome(np.clip(12 - rd, 0, None), 12)))
    rgb = lit(h, alb, rough, metal, detail=bn, detail_k=0.2)
    save(rgb, mo, "KitPlate.png", (768, 160))


def card():
    W, Hh = 1680, 440
    yy, xx = grid(W, Hh)
    def body(dr, s):
        dr.rounded_rectangle((24 * s, 24 * s, (W - 90) * s, (Hh - 24) * s), radius=18 * s, fill=255)
    m = mask((W, Hh), body)
    pc = tile_map("Paper", "color", (W, Hh), 512)
    alb = pc * np.array([1.02, 0.96, 0.84], f32)
    h = m * (0.22 + 0.06 * H.dome(inner(m), 20) + 0.01 * noise((Hh, W), 2, 7))
    band = (yy > 24) & (yy < 118) & (m > 0.5)
    alb[band] = CRIMSON * 1.15 + noise((Hh, W), 4, 9)[band][:, None] * 0.04
    rule = (yy >= 118) & (yy < 128) & (m > 0.5)
    alb[rule] = GILT
    rough = np.where(band, 0.3, 0.75).astype(f32)
    metal = np.where(rule, 1.0, 0.0).astype(f32)
    h += rule * 0.02
    # brass corner guards
    for (x0, y0, sx, sy) in ((24, 24, 1, 1), (W - 90, 24, -1, 1), (24, Hh - 24, 1, -1), (W - 90, Hh - 24, -1, -1)):
        u, v = (xx - x0) * sx, (yy - y0) * sy
        tri = (u >= 0) & (v >= 0) & (u + v < 70)
        alb[tri] = BRASS
        h[tri] = 0.34 + 0.06 * np.clip((70 - (u + v))[tri] / 16, 0, 1)
        rough[tri] = 0.3
        metal[tri] = 1.0
    # the eyelet and a ribbon past the right edge
    ex, ey = W - 150, 72
    rd = np.hypot(xx - ex, yy - ey)
    eye = (rd < 18) & (rd > 9)
    alb[eye] = BRASS
    h[eye] = 0.36
    metal[eye] = 1.0
    def rib(dr, s):
        dr.polygon([((ex + 8) * s, (ey - 10) * s), ((W - 30) * s, 40 * s), ((W - 8) * s, 210 * s), ((W - 44) * s, 228 * s), ((W - 64) * s, 70 * s), ((ex + 4) * s, (ey + 10) * s)], fill=255)
    rm = mask((W, Hh), rib) * (1 - np.clip(m * (xx < W - 92), 0, 1) * 0)
    alb = alb * (1 - rm[..., None]) + (CRIMSON * 1.5) * rm[..., None]
    h = np.maximum(h, rm * (0.30 + 0.05 * H.dome(inner(rm), 6)))
    rough = rough * (1 - rm) + 0.35 * rm
    metal = metal * (1 - rm)
    a = np.clip(m + rm, 0, 1)
    rgb = lit(h, alb, rough, metal)
    save(rgb, a, "CardHud.png", (840, 220))


# ================================================================ the map sheet, tiles and marks
def map_sheet():
    W, Hh = 2048, 1280
    yy, xx = grid(W, Hh)
    rng = np.random.default_rng(3)
    # deckled edge: a rectangle eroded by noise
    e = np.minimum.reduce([xx, yy, W - 1 - xx, Hh - 1 - yy])
    edge_noise = noise((Hh, W), 6, 11) * 18 + noise((Hh, W), 30, 12) * 22
    sheet = np.clip((e - 10 - edge_noise) / 3, 0, 1)
    pc = tile_map("Paper", "color", (W, Hh), 768)
    alb = pc * np.array([1.04, 0.95, 0.78], f32)
    # foxing and tea stains (brown, never red)
    stains = np.zeros((Hh, W), f32)
    for _ in range(9):
        sx, sy, sr = rng.uniform(0, W), rng.uniform(0, Hh), rng.uniform(40, 160)
        rd = np.hypot(xx - sx, yy - sy) / sr
        stains += np.exp(-((rd - 1) / 0.08) ** 2) * 0.5 + np.exp(-rd ** 2 * 2) * 0.15
    fox = (noise((Hh, W), 1.5, 21) > 0.82) * noise((Hh, W), 8, 22)
    alb *= (1 - 0.18 * np.clip(stains, 0, 1))[..., None] * np.array([1, 0.97, 0.9], f32)
    alb *= (1 - 0.25 * fox)[..., None]
    # darker, browner toward the edges
    vig = np.clip(e / 160, 0, 1)
    alb *= (0.72 + 0.28 * vig)[..., None]
    # creases: three panels and a half fold
    h = 0.2 + 0.006 * noise((Hh, W), 1.2, 31) + 0.02 * noise((Hh, W), 40, 32)
    for x in (W / 3, 2 * W / 3):
        h -= 0.035 * np.exp(-((xx - x) / 5) ** 2)
        h += 0.012 * np.exp(-((xx - x - 14) / 18) ** 2)
    h -= 0.025 * np.exp(-((yy - Hh / 2) / 4) ** 2)
    h *= sheet
    # ink: the double border, crimson corner squares, the cartouche, the rose, the scale bar
    ink_im = Image.new("RGBA", (W * 2, Hh * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(ink_im)
    s = 2
    IK = (40, 30, 26, 255)
    CR = (110, 18, 30, 255)
    d.rectangle((70 * s, 70 * s, (W - 70) * s, (Hh - 70) * s), outline=IK, width=7 * s)
    d.rectangle((90 * s, 90 * s, (W - 90) * s, (Hh - 90) * s), outline=IK, width=2 * s)
    for x, y in ((70, 70), (W - 70, 70), (70, Hh - 70), (W - 70, Hh - 70)):
        d.rectangle(((x - 22) * s, (y - 22) * s, (x + 22) * s, (y + 22) * s), fill=CR, outline=IK, width=3 * s)
    # cartouche
    cx0, cy0, cw, ch = W / 2, 150, 720, 120
    d.rectangle(((cx0 - cw / 2) * s, (cy0 - ch / 2) * s, (cx0 + cw / 2) * s, (cy0 + ch / 2) * s), fill=(214, 196, 156, 235), outline=IK, width=4 * s)
    d.rectangle(((cx0 - cw / 2 + 10) * s, (cy0 - ch / 2 + 10) * s, (cx0 + cw / 2 - 10) * s, (cy0 + ch / 2 - 10) * s), outline=IK, width=1 * s)
    ft = ImageFont.truetype(FONT_B, 58 * s)
    fs = ImageFont.truetype(FONT_I, 30 * s)
    title = "CAMPUS  &  GROUNDS"
    d.text((cx0 * s, (cy0 - 14) * s), title, font=ft, fill=IK, anchor="mm")
    d.text((cx0 * s, (cy0 + 34) * s), "Nightmare High  \u00b7  for the use of students", font=fs, fill=(80, 64, 54, 255), anchor="mm")
    # rose (bottom right)
    rx, ry, R = W - 220, Hh - 230, 90
    for k in range(16):
        a = k * math.pi / 8
        L = R if k % 4 == 0 else (R * 0.6 if k % 2 == 0 else R * 0.36)
        wdt = R * (0.15 if k % 4 == 0 else 0.1)
        tip = (rx + L * math.sin(a), ry - L * math.cos(a))
        l = (rx + wdt * math.sin(a - math.pi / 2), ry - wdt * math.cos(a - math.pi / 2))
        r_ = (rx + wdt * math.sin(a + math.pi / 2), ry - wdt * math.cos(a + math.pi / 2))
        col = CR if k == 0 else IK
        d.polygon([(tip[0] * s, tip[1] * s), (l[0] * s, l[1] * s), (rx * s, ry * s)], fill=col)
        d.polygon([(tip[0] * s, tip[1] * s), (r_[0] * s, r_[1] * s), (rx * s, ry * s)], fill=(228, 212, 176, 255), outline=col)
    d.ellipse(((rx - R * 1.06) * s, (ry - R * 1.06) * s, (rx + R * 1.06) * s, (ry + R * 1.06) * s), outline=IK, width=3 * s)
    fr = ImageFont.truetype(FONT_G, 34 * s)
    for txt, a in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        ar = math.radians(a)
        d.text(((rx + R * 1.3 * math.sin(ar)) * s, (ry - R * 1.3 * math.cos(ar)) * s), txt, font=fr, fill=CR if txt == "N" else IK, anchor="mm")
    # scale bar (bottom left)
    bx, by = 170, Hh - 150
    d.rectangle((bx * s, by * s, (bx + 400) * s, (by + 16) * s), outline=IK, width=3 * s)
    for k in range(4):
        if k % 2 == 0:
            d.rectangle(((bx + k * 100) * s, by * s, (bx + k * 100 + 100) * s, (by + 16) * s), fill=IK)
    d.text(((bx + 200) * s, (by - 26) * s), "a hundred paces", font=fs, fill=(80, 64, 54, 255), anchor="mm")
    d.text(((W - 260) * s, 140 * s), "Curfew at nine.", font=fs, fill=(80, 64, 54, 230), anchor="mm")
    d.text(((W - 260) * s, 178 * s), "Keep to the paths.", font=fs, fill=(80, 64, 54, 230), anchor="mm")
    ink_im = ink_im.resize((W, Hh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
    ink = np.array(ink_im, f32) / 255
    ia = ink[..., 3]
    alb = alb * (1 - ia[..., None] * 0.95) + ink[..., :3] * ia[..., None] * 0.95
    h += ia * 0.006
    rgb = lit(h, alb, 0.82 - ia * 0.2, np.zeros((Hh, W), f32), strength=1 / 3)
    save(rgb, sheet, "MapSheet.png")


def map_tiles():
    S = 256
    yy, xx = grid(S, S)
    # hatching: diagonal ink lines (period 16 px at 45 deg), a little wobble
    u = (xx + yy) / math.sqrt(2)
    wob = (noise((S, S), 3, 41) - 0.5) * 2.0
    hatch = np.clip(1.6 - np.abs(((u + wob) % (16 / math.sqrt(2) * 1.0)) - 4), 0, 1)
    rgb = np.dstack([np.full((S, S), 0.16, f32), np.full((S, S), 0.12, f32), np.full((S, S), 0.10, f32)])
    save(rgb, hatch * 0.55, "MapHatch.png")
    # stipple: dots and tiny grass tufts (seamless: placed with wrap)
    im = Image.new("L", (S * 2, S * 2), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(9)
    for _ in range(170):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                X, Y = (x + ox) * 2, (y + oy) * 2
                if rng.random() < 0.75:
                    d.ellipse((X - 2.2, Y - 2.2, X + 2.2, Y + 2.2), fill=255)
                else:
                    for k in (-1, 0, 1):
                        d.line((X, Y, X + k * 4, Y - 9), fill=255, width=2)
    st = np.array(im.resize((S, S), Image.BOX), f32) / 255
    rgb = np.dstack([np.full((S, S), 0.20, f32), np.full((S, S), 0.24, f32), np.full((S, S), 0.14, f32)])
    save(rgb, st * 0.7, "MapStipple.png")


def map_marks():
    S = 512
    yy, xx = grid(S, S)
    c = S / 2
    # "you are here": a crimson ink arrowhead inside an ink ring, inked look (slightly uneven)
    def arrow(dr, s):
        dr.polygon([(c * s, 96 * s), ((c + 104) * s, 360 * s), (c * s, 300 * s), ((c - 104) * s, 360 * s)], fill=255)
    am = mask((S, S), arrow)
    rr = np.hypot(xx - c, yy - c)
    ring = np.clip(6 - np.abs(rr - 210), 0, 1)
    wob = 0.9 + 0.1 * noise((S, S), 4, 51)
    rgb = np.zeros((S, S, 3), f32)
    rgb[:] = np.array([0.43, 0.06, 0.10], f32)
    rgb = rgb * am[..., None] * wob[..., None] + np.array([0.15, 0.11, 0.10], f32) * (ring * (1 - am))[..., None]
    a = np.clip(am + ring, 0, 1) * (0.92 + 0.08 * noise((S, S), 2, 52))
    halo = ndimage.gaussian_filter(am, 14) * 0.5
    save(rgb, np.clip(a + halo * (1 - a) * 0.0, 0, 1), "MapYou.png", (256, 256))
    # the pin: brass shaft, crimson glass head, a soft shadow
    def shaft(dr, s):
        dr.polygon([((c - 9) * s, 250 * s), ((c + 9) * s, 250 * s), (c * s, 500 * s)], fill=255)
    sm = mask((S, S), shaft)
    hr = np.hypot(xx - c, yy - 190)
    head = np.clip(110 - hr, 0, 1)
    collar = np.clip(26 - np.hypot((xx - c) / 2.2, yy - 262), 0, 1) * (1 - head)
    h = sm * (0.25 + 0.06 * H.dome(inner(sm), 6)) + head * (0.3 + 0.5 * H.dome(np.clip(110 - hr, 0, None), 110))
    h = np.maximum(h, collar * 0.36)
    alb = np.zeros((S, S, 3), f32)
    alb[sm > 0.5] = BRASS
    alb[collar > 0.5] = BRASS_OLD
    alb[head > 0.5] = np.array([0.55, 0.06, 0.10], f32)
    rough = np.where(head > 0.5, 0.08, 0.3).astype(f32)
    metal = np.where(head > 0.5, 0.0, 1.0).astype(f32)
    rgb = lit(h, alb, rough, metal, strength=1 / 6)
    a = np.clip(sm + head + collar, 0, 1)
    sh = ndimage.gaussian_filter(np.roll(np.roll(head, 40, 0), 28, 1), 16) * 0.5
    oa = np.clip(a + sh * (1 - a), 0, 1)
    save(rgb * a[..., None] / np.maximum(oa[..., None], 1e-4), oa, "MapPin.png", (256, 256))


# ================================================================ chip icons (the phone-app icon family)
def icons(only=None):
    import make_app_icons as AI
    S = AI.S
    defs = {}

    def oil():
        ic = AI.Icon(1)
        # a lamp-oil drop with a highlight groove
        m = AI.U(AI.circle(512, 640, 240), AI.poly([(512, 110), (742, 575), (282, 575)]))
        ic.part(m, alb=AI.WAX, rough=0.2, bevel=60, lift=0.22)
        ic.groove(AI.seg(420, 520, 390, 680, 20), 0.05, 0.0)
        return ic

    def cup():
        ic = AI.Icon(2)
        body = AI.box(470, 560, 420, 380, 60)
        ic.part(body, alb=AI.PAPER, rough=0.3)
        ic.part(AI.ring(720, 560, 110, 34), alb=AI.PAPER, rough=0.3)
        ic.part(AI.box(470, 790, 560, 50, 25), alb=AI.BONE)
        for k, x in enumerate((380, 470, 560)):
            ic.ink(AI.seg(x, 320 - k % 2 * 20, x + 30, 160, 20))
        return ic

    def biscuit():
        ic = AI.Icon(3)
        ic.part(AI.circle(512, 512, 330), alb=AI.BONE, rough=0.7, bevel=50)
        for k in range(12):
            a = 2 * math.pi * k / 12
            ic.recess(AI.circle(512 + 250 * math.cos(a), 512 + 250 * math.sin(a), 30), 0.05)
        for x, y in ((420, 430), (600, 430), (512, 560), (420, 650), (600, 650)):
            ic.recess(AI.circle(x, y, 24), 0.06)
        return ic

    def bandage():
        ic = AI.Icon(4)
        ic.part(AI.box(512, 512, 760, 260, 120, 0.7), alb=AI.CLOTH, rough=0.8)
        ic.part(AI.box(512, 512, 260, 220, 30, 0.7), alb=AI.PAPER, rough=0.7)
        for dx in (-60, 0, 60):
            for dy in (-40, 40):
                c = AI.to_world(512, 512, 0.7, dx, dy)
                ic.recess(AI.circle(c[0], c[1], 14), 0.04)
        return ic

    def pas():
        ic = AI.Icon(5)
        arch = AI.U(AI.box(512, 560, 420, 420, 20), AI.circle(512, 380, 210))
        ic.part(arch, alb=AI.BRASS, metal=AI.MET, rough=0.3)
        ic.emboss(AI.text("P", 300, 512, 500), 0.06)
        for x in (420, 512, 604):
            ic.recess(AI.circle(x, 700, 28), 0.08)
        ic.part(AI.box(512, 880, 90, 140, 30), alb=AI.LEATHER)
        return ic

    def flame():
        ic = AI.Icon(6)
        pts = AI.bez((512, 110), (720, 380), (800, 600), (512, 900), 60)[:-1] + AI.bez((512, 900), (220, 620), (330, 440), (512, 110), 60)
        ic.part(AI.poly(pts), alb=AI.WAX, rough=0.4, bevel=60)
        inner_pts = AI.bez((512, 420), (620, 560), (640, 680), (512, 820), 40)[:-1] + AI.bez((512, 820), (390, 690), (410, 560), (512, 420), 40)
        ic.emboss(AI.poly(inner_pts), 0.08, alb=AI.PAPER)
        return ic

    def frost():
        ic = AI.Icon(7)
        arms = None
        for k in range(6):
            a = math.pi / 2 + k * math.pi / 3
            ex, ey = 512 + 380 * math.cos(a), 512 - 380 * math.sin(a)
            arm = AI.seg(512, 512, ex, ey, 46)
            for t in (0.45, 0.72):
                bx, by = 512 + 380 * t * math.cos(a), 512 - 380 * t * math.sin(a)
                for s_ in (-1, 1):
                    b = a + s_ * 0.8
                    arm = AI.U(arm, AI.seg(bx, by, bx + 120 * math.cos(b), by - 120 * math.sin(b), 34))
            arms = arm if arms is None else AI.U(arms, arm)
        ic.part(arms, alb=AI.PAPER, rough=0.15, bevel=18)
        return ic

    def heart():
        ic = AI.Icon(8)
        pts = AI.bez((512, 880), (180, 620), (120, 300), (330, 220), 50)[:-1] + AI.bez((330, 220), (440, 190), (500, 260), (512, 330), 30)[:-1] + \
            AI.bez((512, 330), (524, 260), (584, 190), (694, 220), 30)[:-1] + AI.bez((694, 220), (904, 300), (844, 620), (512, 880), 50)
        m = AI.poly(pts)
        crack = AI.U(AI.seg(512, 330, 470, 470, 26), AI.seg(470, 470, 560, 590, 26), AI.seg(560, 590, 500, 760, 26))
        ic.part(AI.sub(m, crack), alb=AI.WAX, rough=0.25, bevel=50)
        return ic

    def keys():
        ic = AI.Icon(9)
        ic.part(AI.ring(330, 330, 150, 44), alb=AI.IRON, metal=AI.MET, rough=0.35)
        for k, (ang, L) in enumerate(((0.75, 520), (1.05, 440))):
            x0, y0 = 330 + 150 * math.cos(ang), 330 + 150 * math.sin(ang)
            x1, y1 = x0 + L * math.cos(ang), y0 + L * math.sin(ang)
            key = AI.U(AI.seg(x0, y0, x1, y1, 40), AI.box(x1 - 60 * math.sin(ang), y1 + 40, 90, 70, 10, ang))
            ic.part(key, alb=AI.BRASS if k == 0 else AI.IRON, metal=AI.MET, rough=0.3, z=0.26 + 0.04 * k)
        return ic

    def book():
        ic = AI.Icon(10)
        ic.part(AI.box(512, 512, 560, 720, 30), alb=AI.LEATHER, rough=0.6)
        ic.part(AI.box(300, 512, 110, 720, 40), alb=AI.LEATHER * 0.8, rough=0.5)
        for y in (300, 512, 724):
            ic.emboss(AI.box(300, y, 120, 26, 10), 0.05, alb=AI.BRASS, metal=AI.MET)
        ic.part(AI.box(560, 420, 300, 200, 10), alb=AI.PAPER)
        return ic

    for name, fn in (("Oil", oil), ("Cup", cup), ("Biscuit", biscuit), ("Bandage", bandage), ("Pass", pas), ("Flame", flame),
                     ("Frost", frost), ("Heart", heart), ("Keys", keys), ("Book", book)):
        if only and name not in only:
            continue
        lum, a = fn().render()
        save(np.dstack([lum] * 3), a, f"Icon{name}.png", (256, 256))


# ================================================================ frost and ink at the screen edges
def edges():
    W, Hh = 1024, 576
    yy, xx = grid(W, Hh)
    e = np.minimum.reduce([xx / W, yy / Hh, 1 - xx / W, 1 - yy / Hh]) * 2   # 0 at the edge, 1 at the centre
    # frost: fern-like crystals from fbm ridges, thick at the edges, fading inward
    n1, n2, n3 = noise((Hh, W), 2.0, 61), noise((Hh, W), 6, 62), noise((Hh, W), 18, 63)
    ridge = 1 - np.abs(n2 * 2 - 1)
    fern = np.clip((ridge ** 6) * 1.6 + (1 - np.abs(n1 * 2 - 1)) ** 10 * 0.8, 0, 1)
    reach = np.clip(1 - e / (0.22 + 0.18 * n3), 0, 1) ** 1.4
    frost = np.clip(fern * reach * 1.3 + reach ** 3 * 0.35, 0, 1)
    sparkle = (noise((Hh, W), 0.7, 64) > 0.93) * reach
    rgb = np.dstack([0.86 + 0.1 * frost, 0.92 + 0.06 * frost, np.ones_like(frost)])
    save(rgb, np.clip(frost * 0.85 + sparkle * 0.6, 0, 1), "FrostEdge.png")
    # ink: turbulent dark bleed with feathered tendrils
    t = noise((Hh, W), 10, 71) * 0.6 + noise((Hh, W), 3, 72) * 0.4
    ink = np.clip(1 - e / (0.32 + 0.22 * t), 0, 1) ** 1.6
    rgb = np.dstack([np.full_like(ink, 0.03), np.full_like(ink, 0.02), np.full_like(ink, 0.04)])
    save(rgb, np.clip(ink * 0.95, 0, 1), "InkEdge.png")


# ================================================================ previews (assembled like the HUD)
def previews():
    bg = Image.new("RGBA", (900, 520), (16, 14, 20, 255))
    def put(name, size, pos, rot=0):
        im = Image.open(OUT / name).convert("RGBA").resize(size, Image.LANCZOS)
        if rot:
            im = im.rotate(rot, resample=Image.BICUBIC)
        bg.alpha_composite(im, pos)
    # compass at 260 px with a plate under it
    put("CompassFace.png", (260, 260), (82, 40), rot=-28)
    put("CompassNeedle.png", (260, 260), (82, 40), rot=-65)
    put("CompassGlass.png", (260, 260), (82, 40))
    put("CompassBezel.png", (260, 260), (82, 40))
    put("KitPlate.png", (340, 70), (42, 320))
    d = ImageDraw.Draw(bg)
    d.text((212, 355), "Chemistry \u00b7 Room 103  \u00b7  42 paces", font=ImageFont.truetype(FONT_G, 17), fill=(235, 205, 120), anchor="mm")
    put("CardHud.png", (420, 110), (440, 60))
    d.text((470, 78), "CLASS TIMETABLE", font=ImageFont.truetype(FONT_B, 20), fill=(240, 226, 196))
    d.text((470, 122), "Now  Period 2: Chemistry, Room 103 \u00b7 12 min", font=ImageFont.truetype(FONT_G, 15), fill=(40, 30, 26))
    d.text((470, 144), "Next  Break, the Commons at 09:45", font=ImageFont.truetype(FONT_G, 15), fill=(40, 30, 26))
    x = 440
    for k, n in enumerate(("Oil", "Cup", "Pass", "Flame", "Frost", "Heart")):
        put("KitPlate.png", (200, 42), (x if k < 3 else x, 200 + (k % 3) * 52 if k < 3 else 200 + (k % 3) * 52))
    xs = [(440, 200), (440, 252), (440, 304), (650, 200), (650, 252), (650, 304)]
    for (px, py), n, t, col in zip(xs, ("Oil", "Cup", "Pass", "Flame", "Frost", "Heart"),
                                  ("Oil 12:40", "3/4 cups of tea", "Hall pass 42 s", "Warmer lit", "Chilled", "Wounded"),
                                  ((235, 205, 120), (228, 222, 208), (235, 205, 120), (240, 160, 90), (170, 200, 235), (214, 46, 58))):
        put("KitPlate.png", (200, 42), (px, py))
        ic = Image.open(OUT / f"Icon{n}.png").convert("RGBA").resize((28, 28), Image.LANCZOS)
        tint = Image.new("RGBA", ic.size, col + (255,))
        tint.putalpha(ic.getchannel("A"))
        lum = ic.convert("L")
        tint = Image.composite(Image.merge("RGBA", [Image.eval(lum, lambda v, c=c: v * c // 255) for c in col] + [ic.getchannel("A")]), tint, ic.getchannel("A"))
        bg.alpha_composite(tint, (px + 22, py + 7))
        d.text((px + 58, py + 21), t, font=ImageFont.truetype(FONT_G, 15), fill=col, anchor="lm")
    bg.save(OUT / "preview_hud.png")
    # the map: sheet + places drawn like the HUD does
    sheet = Image.open(OUT / "MapSheet.png").convert("RGBA").resize((1024, 640), Image.LANCZOS)
    hatch = Image.open(OUT / "MapHatch.png").convert("RGBA").resize((96, 96))
    stip = Image.open(OUT / "MapStipple.png").convert("RGBA").resize((96, 96))
    dm = ImageDraw.Draw(sheet)
    places = [((300, 250, 560, 360), "School", "MAIN HALL"), ((560, 250, 640, 360), "School", "EAST WING"), ((320, 170, 420, 235), "Restricted", "ARCHIVE"),
              ((660, 160, 830, 300), "Sports", "NORTH FIELD"), ((170, 380, 330, 480), "Sports", "WEST PITCH"), ((700, 380, 820, 470), "Turf", "BACK LOT"),
              ((450, 410, 560, 470), "School", "COMMONS"), ((330, 300, 360, 330), "Class", "")]
    for (x0, y0, x1, y1), kind, name in places:
        fill = {"School": (196, 176, 140, 255), "Restricted": (186, 160, 132, 255), "Sports": (176, 184, 136, 255), "Turf": (206, 186, 156, 120), "Class": (210, 170, 90, 255)}[kind]
        dm.rectangle((x0, y0, x1, y1), fill=fill)
        tile = stip if kind == "Sports" else hatch
        for tx in range(x0, x1, 96):
            for ty in range(y0, y1, 96):
                cut = tile.crop((0, 0, min(96, x1 - tx), min(96, y1 - ty)))
                sheet.alpha_composite(cut, (tx, ty))
        out_col = (110, 18, 30) if kind in ("Turf", "Restricted") else ((176, 130, 40) if kind == "Class" else (40, 30, 26))
        dm.rectangle((x0, y0, x1, y1), outline=out_col, width=3)
        if name:
            dm.text(((x0 + x1) / 2, (y0 + y1) / 2), name, font=ImageFont.truetype(FONT_G, 15), fill=out_col, anchor="mm")
    you = Image.open(OUT / "MapYou.png").convert("RGBA").resize((40, 40)).rotate(-30, resample=Image.BICUBIC)
    sheet.alpha_composite(you, (480, 372))
    pin = Image.open(OUT / "MapPin.png").convert("RGBA").resize((46, 46))
    sheet.alpha_composite(pin, (740, 180))
    sheet.save(OUT / "preview_map.png")
    print("  previews written")


if __name__ == "__main__":
    want = [a for a in sys.argv[1:]]
    steps = {"compass": compass, "plate": plate, "card": card, "map": map_sheet, "tiles": map_tiles, "marks": map_marks,
             "icons": icons, "edges": edges, "preview": previews}
    for k, fn in steps.items():
        if not want or k in want:
            print(k)
            fn()
