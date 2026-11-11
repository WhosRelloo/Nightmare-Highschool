"""Training minigame HUD art (Nightmare Highschool), baked to images. All original.

Same pipeline as the phone icons and the kit HUD (make_health_pbr.shade: GGX specular, Lambert diffuse, the warm key,
cool fill and candle rim, an environment reflection, AO from the height). Greyscale pieces are tinted in game with
ImageColor3; the gauge is baked in colour (brass, black iron, crimson enamel).

Pieces (art/ui/hud/out/training/, and copied to art/group-upload-training/ for the group bulk import):
  TrainGauge.png        1024  the brass pressure gauge: a knurled brass bezel with twelve rivets, an ink-enamel face with
                              engraved guide rings and chalk ticks, the MARK (a raised brass channel with a crimson enamel
                              groove at r = 190/1024), and a brass centre boss. The area icon sits on the boss.
  TrainMarkGlow.png      512  a soft glow band at the mark's radius (flashes on a hit, tinted by the rating)
  TrainRing.png          512  the shrinking ring: a raised candle-gold band at r = 470/1024 of the sprite with a soft halo
  TrainRingFake.png      512  the feint: the same ring cracked into seven shards (let it pass)
  TrainRateGood/Great/Perfect/Miss.png  512  the rep marks: a chalk tick, a faceted brass diamond, a ringed eight-point
                              star, a scratched cross
  TrainIconArms/Torso/Legs.png  512  the area crests: a gothic shield with a flexed arm, a torso, a pair of legs
  TrainStationPushUp/PullUp/SitUp/Squat.png  512  the station medallions: an R6 student in the pose, on a brass medallion
  TrainBadgeStreak/Best/Daily.png  512  a church candle in a ring of seven day pips; a laurel wreath round a star; an
                              hourglass
  TrainIconSore.png      512  a cracked disc with ache lines (soreness)
  preview_hud.png       1920x1080  the HUD mockup;  contact_training.png  every piece on ink tiles

  python make_training_ui.py [Name ...]
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import make_health_pbr as H
import make_app_icons as A
from make_app_icons import (Icon, M, box, circle, ring, seg, ellipse, poly, U, sub, text, inner_dist, smooth,
                            sd_circle, xx, yy, bez, PAPER, BONE, WAX, INK, LEATHER, STONE, IRON, BRASS, CLOTH, MET)

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "training"
OUT.mkdir(parents=True, exist_ok=True)
UPLOAD = HERE.parents[1] / "group-upload-training"
UPLOAD.mkdir(parents=True, exist_ok=True)
S = A.S
f32 = np.float32
FONT_T = "C:/Windows/Fonts/timesbd.ttf"
FONT_G = "C:/Windows/Fonts/georgiab.ttf"

GAUGE_MARK_R = 190      # mark radius at 1024 (the UI reads 190/1024 of the gauge size)
GAUGE_START_R = 430     # where the ring starts (just inside the bezel)
RING_R = 470            # the ring's radius in its own 1024 sprite


def save_grey(lum, alpha, name, size=512):
    a = np.dstack([lum, lum, lum, alpha]) * 255
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
    im.save(OUT / f"{name}.png", optimize=True)
    pass  # (the upload folder now holds the Blender PBR set: finish_training_ui.py)
    print("  ", name, im.size)
    return im


def save_rgba(rgb, alpha, name, size=None):
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(alpha, 0, 1) * 255]).astype(np.uint8), "RGBA")
    if size:
        img = img.resize(size, Image.LANCZOS)
    img.save(OUT / f"{name}.png", optimize=True)
    pass  # (the upload folder now holds the Blender PBR set: finish_training_ui.py)
    print("  ", name, img.size)
    return img


def limb(x0, y0, x1, y1, w, r=None):
    """an R6 block limb from (x0, y0) to (x1, y1): a rounded box along the segment"""
    L = math.hypot(x1 - x0, y1 - y0)
    rot = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return box((x0 + x1) / 2, (y0 + y1) / 2, L + w * 0.15, w, w * 0.22 if r is None else r, rot)


def rough_stroke(m, ic, k=0.35, sigma=2.2):
    """chalk: eat the edges of a mask with noise"""
    n = ic.noise(sigma)
    return np.clip((m - 0.5 + (n - 0.5) * k) * 4 + 0.5, 0, 1) * (m > 0.02)


# ================================================================ the gauge (colour)
def gauge():
    yyl, xxl = yy, xx
    cx = cy = S / 2
    r = np.hypot(xxl - cx, yyl - cy)
    th = np.arctan2(yyl - cy, xxl - cx)
    h = np.zeros((S, S), f32)
    alb = np.zeros((S, S, 3), f32)
    rough = np.full((S, S), 0.5, f32)
    metal = np.zeros((S, S), f32)
    emis = np.zeros((S, S, 3), f32)
    bcol, bn, brough, _ = H.material("Brass", (S, S), 320, (1.0, 0.92, 0.80))
    icol, inrm, irough, _ = H.material("Iron", (S, S), 300, (0.55, 0.52, 0.56))
    brass_alb = H.lin_to_srgb(bcol) * 0.55 + np.array([0.80, 0.60, 0.30], f32) * 0.45
    # bezel 440..500: domed, knurled outer edge, an engraved line, twelve rivets
    bez_m = np.clip(np.minimum(r - 440, 500 - r) + 0.5, 0, 1).astype(f32)
    d = np.clip(np.minimum(r - 440, 500 - r), 0, None)
    hb = 0.32 + 0.18 * H.dome(d, 26)
    kn = (r > 482) & (r < 500)
    hb += kn * 0.03 * np.cos(th * 160)
    hb -= 0.05 * np.clip(1 - np.abs(r - 458) / 2.5, 0, 1)
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        rx, ry = cx + 470 * math.cos(a), cy + 470 * math.sin(a)
        dd = np.hypot(xxl - rx, yyl - ry)
        rv = np.clip(1 - dd / 11, 0, 1)
        hb += 0.10 * np.sqrt(rv)
    h = h * (1 - bez_m) + hb * bez_m
    alb = alb * (1 - bez_m[..., None]) + brass_alb * bez_m[..., None]
    rough = rough * (1 - bez_m) + np.clip(brough * 0.8, 0.18, 0.6) * bez_m
    metal = metal * (1 - bez_m) + 0.9 * bez_m
    # the face r < 440: ink enamel with a crimson vignette near the rim
    face = np.clip(440.5 - r, 0, 1).astype(f32)
    vign = np.clip((r - 250) / 190, 0, 1) ** 2
    ink = np.array([0.055, 0.045, 0.06], f32)
    crim = np.array([0.38, 0.055, 0.10], f32)      # #600E1A
    fa = ink[None, None, :] * (1 - vign[..., None] * 0.6) + crim[None, None, :] * (vign[..., None] * 0.42)
    fn = A.blur_noise(6, 41)
    fa *= (0.92 + 0.12 * fn)[..., None]
    hf = 0.18 - 0.03 * np.clip((440 - r) / 40, 0, 1) * 0 + 0.006 * fn
    # inner lip shadow under the bezel
    hf -= 0.05 * np.clip(1 - (440 - r) / 18, 0, 1)
    h = h * (1 - face) + hf * face
    alb = alb * (1 - face[..., None]) + fa * face[..., None]
    rough = rough * (1 - face) + 0.28 * face
    metal = metal * (1 - face) + 0.0 * face
    # engraved guide rings (faint brass inlay) and chalk ticks at 400..428
    for rr, w in ((372, 2.6), (310, 2.0), (250, 1.6)):
        g = np.clip(1 - np.abs(r - rr) / w, 0, 1) * face
        h -= 0.012 * g
        alb = alb * (1 - g[..., None] * 0.55) + np.array([0.55, 0.42, 0.22], f32) * (g[..., None] * 0.55)
    deg = (np.degrees(th) + 360) % 360
    for step, r0, w, k in ((7.5, 412, 2.2, 0.55), (30, 396, 3.6, 0.9)):
        kk = np.abs(((deg + step / 2) % step) - step / 2) * (math.pi / 180) * r
        tick = np.clip(w - kk, 0, 1) * ((r > r0) & (r < 430)) * face
        alb = alb * (1 - tick[..., None] * k) + np.array([0.86, 0.86, 0.80], f32) * (tick[..., None] * k)
        h += 0.008 * tick
    # the MARK: a raised brass channel 172..208 with a crimson enamel groove 184..196 and a gilt hairline at 190
    ch = np.clip(np.minimum(r - 170, 210 - r) + 0.5, 0, 1).astype(f32)
    dch = np.clip(np.minimum(r - 170, 210 - r), 0, None)
    hc = 0.26 + 0.10 * H.dome(dch, 9)
    grv = np.clip(np.minimum(r - 182, 198 - r) + 0.5, 0, 1).astype(f32)
    hc -= 0.07 * grv
    h = h * (1 - ch) + hc * ch
    alb = alb * (1 - ch[..., None]) + brass_alb * ch[..., None]
    rough = rough * (1 - ch) + 0.24 * ch
    metal = metal * (1 - ch) + 0.92 * ch
    alb = alb * (1 - grv[..., None]) + np.array([0.42, 0.04, 0.08], f32) * grv[..., None]
    rough = rough * (1 - grv) + 0.18 * grv
    metal = metal * (1 - grv)
    hair = np.clip(1.2 - np.abs(r - GAUGE_MARK_R), 0, 1)
    emis += hair[..., None] * np.array([0.55, 0.40, 0.14], f32)
    # centre boss r < 118 with an engraved quatrefoil
    boss = np.clip(118.5 - r, 0, 1).astype(f32)
    hbz = 0.30 + 0.12 * H.dome(np.clip(118 - r, 0, None), 30)
    qa = np.abs(np.cos(2 * th))
    qf = np.clip(1 - np.abs(r - (64 + 22 * qa)) / 3.0, 0, 1)
    hbz -= 0.03 * qf
    hbz -= 0.025 * np.clip(1 - np.abs(r - 100) / 2.2, 0, 1)
    h = h * (1 - boss) + hbz * boss
    balb = brass_alb * 0.78
    alb = alb * (1 - boss[..., None]) + balb * boss[..., None]
    rough = rough * (1 - boss) + 0.36 * boss
    metal = metal * (1 - boss) + 0.9 * boss
    alpha = np.clip(500.5 - r, 0, 1).astype(f32)
    hh = ndimage.gaussian_filter(h, 0.8)
    N = H.normals_from(hh * S * 0.5, 1 / 7.5, bn, 0.18)
    ao = H.ao_from(hh, 10, 5) * H.ao_from(hh, 3, 9)
    rgb = H.shade(H.srgb_to_lin(np.clip(alb, 0, 1)).astype(f32), N, np.clip(rough, 0.05, 1), np.clip(metal, 0, 1), ao,
                  H.srgb_to_lin(emis))
    return save_rgba(rgb, alpha, "TrainGauge", (1024, 1024))


def mark_glow():
    r = np.hypot(xx - S / 2, yy - S / 2)
    g = np.exp(-((r - GAUGE_MARK_R) / 26) ** 2) + 0.35 * np.exp(-((r - GAUGE_MARK_R) / 70) ** 2)
    g = np.clip(g, 0, 1) * np.clip((500 - r) / 40, 0, 1)
    return save_grey(np.ones((S, S), f32), g.astype(f32), "TrainMarkGlow")


def ring_sprite(fake=False):
    ic = Icon(71 if fake else 70)
    cx = cy = S / 2
    band = ring(cx, cy, RING_R, 38)
    if fake:
        r = np.hypot(xx - cx, yy - cy)
        th = np.arctan2(yy - cy, xx - cx)
        n = 7
        seg_i = np.floor((th + math.pi) / (2 * math.pi) * n)
        frac = (th + math.pi) / (2 * math.pi) * n - seg_i
        # jagged gaps: each crack offset by a little noise along the radius
        jag = (A.blur_noise(3, 9) - 0.5) * 0.16
        gap = np.clip((np.minimum(frac + jag, 1 - frac + jag) - 0.06) * 60, 0, 1)
        band = band * gap
        # hairline cracks across the shards
        cr = ring(cx, cy, RING_R + 4, 3) * (A.blur_noise(5, 13) > 0.62)
        ic.part(band, z=0.2, lift=0.14, bevel=12, alb=0.62, rough=0.5, metal=0.2)
        ic.groove(cr, 0.06, 0.4)
        lum, alpha = ic.render()
    else:
        ic.part(band, z=0.2, lift=0.16, bevel=14, alb=0.95, rough=0.3, metal=MET)
        lum, alpha = ic.render()
        r = np.hypot(xx - cx, yy - cy)
        halo = np.exp(-((r - RING_R) / 22) ** 2) * 0.55
        lum = np.maximum(lum, (halo > alpha) * 0.95 + lum * (halo <= alpha))
        alpha = np.maximum(alpha, halo)
    return save_grey(lum, alpha, "TrainRingFake" if fake else "TrainRing")


# ================================================================ rep marks
def rate_good():
    ic = Icon(80)
    m = U(seg(300, 540, 450, 700, 92), seg(450, 700, 760, 300, 92))
    m = rough_stroke(m, ic, 0.5, 2.0)
    ic.part(m, z=0.2, lift=0.08, bevel=10, alb=0.92, rough=0.85, mottle=0.18)
    return ic


def rate_great():
    ic = Icon(81)
    cx, cy = 512, 512
    dia = poly([(cx, cy - 330), (cx + 250, cy), (cx, cy + 330), (cx - 250, cy)])
    ic.part(dia, z=0.2, lift=0.24, bevel=60, alb=BRASS, rough=0.28, metal=MET)
    inner = poly([(cx, cy - 180), (cx + 136, cy), (cx, cy + 180), (cx - 136, cy)])
    ic.recess(inner, 0.08, 10)
    ic.emboss(poly([(cx, cy - 120), (cx + 90, cy), (cx, cy + 120), (cx - 90, cy)]), 0.12, 30, alb=0.96, rough=0.22)
    ic.groove(U(seg(cx, cy - 320, cx, cy - 190, 8), seg(cx, cy + 190, cx, cy + 320, 8)), 0.04)
    return ic


def star_pts(cx, cy, R, r, n=8, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n)
        rr = R if k % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def rate_perfect():
    ic = Icon(82)
    cx, cy = 512, 512
    ic.part(ring(cx, cy, 400, 46), z=0.18, lift=0.14, bevel=14, alb=BRASS, rough=0.3, metal=MET)
    for k in range(24):
        a = k * math.pi / 12
        ic.emboss(circle(cx + 400 * math.cos(a), cy + 400 * math.sin(a), 9), 0.05, 6)
    st = poly(star_pts(cx, cy, 340, 140))
    ic.part(st, z=0.22, lift=0.22, bevel=40, alb=0.97, rough=0.22, metal=MET)
    # facet ridges along each point
    for k in range(8):
        a = math.radians(-90 + k * 45)
        ic.groove(seg(cx, cy, cx + 320 * math.cos(a), cy + 320 * math.sin(a), 6), 0.035, 0.18)
    ic.part(circle(cx, cy, 70), z=0.42, lift=0.08, bevel=20, alb=0.85, rough=0.26, metal=MET)
    return ic


def rate_miss():
    ic = Icon(83)
    m = U(seg(320, 320, 704, 704, 84), seg(704, 320, 320, 704, 84))
    m = rough_stroke(m, ic, 0.55, 2.5)
    ic.part(m, z=0.2, lift=0.07, bevel=10, alb=0.80, rough=0.8, mottle=0.2)
    ic.groove(U(seg(330, 330, 690, 690, 10), seg(690, 334, 334, 690, 10)), 0.05, 0.3)
    return ic


# ================================================================ area crests
def shield_pts(cx, cy, w, h):
    top = cy - h * 0.5
    pts = [(cx - w / 2, top + 40), (cx - w / 2 + 40, top)]
    pts += [(cx + w / 2 - 40, top), (cx + w / 2, top + 40)]
    pts += bez((cx + w / 2, top + 40), (cx + w / 2, top + h * 0.62), (cx + w * 0.22, top + h * 0.86), (cx, top + h))
    pts += bez((cx, top + h), (cx - w * 0.22, top + h * 0.86), (cx - w / 2, top + h * 0.62), (cx - w / 2, top + 40))
    return pts


def crest(seed):
    ic = Icon(seed)
    sh = poly(shield_pts(512, 512, 760, 900))
    ic.part(sh, z=0.16, lift=0.14, bevel=30, alb=BRASS, rough=0.32, metal=MET)
    inner = poly(shield_pts(512, 520, 640, 770))
    ic.custom(inner, 0.24 + 0.012 * ic.noise(10), 0.30 * (0.9 + 0.1 * ic.noise(3)), 0.55, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - inner, 8, 0), 5, 1), 8) * inner)
    for k in range(8):
        y = 140 + k * 20
    return ic


def icon_arms():
    ic = crest(90)
    # a flexed arm in one outline: shoulder at the left, the bicep's peak, the elbow, the forearm up, the fist
    pts = [(240, 720)]
    pts += bez((240, 720), (400, 740), (560, 745), (650, 712))
    pts += bez((650, 712), (722, 690), (735, 610), (718, 528))
    pts += bez((718, 528), (706, 460), (704, 410), (714, 372))
    pts += bez((714, 372), (742, 340), (744, 262), (706, 226))
    pts += bez((706, 226), (650, 200), (596, 210), (578, 252))
    pts += bez((578, 252), (572, 300), (580, 340), (588, 372))
    pts += bez((588, 372), (574, 430), (566, 490), (560, 548))
    pts += bez((560, 548), (528, 470), (420, 444), (344, 486))
    pts += bez((344, 486), (290, 512), (246, 566), (240, 620))
    arm = poly(pts)
    ic.part(arm, z=0.30, lift=0.20, bevel=40, alb=BONE, rough=0.5)
    ic.groove(M(np.abs(A.sd_ellipse(445, 600, 150, 92, -6)) - 4) * (yy > 600) * (xx > 330) * (xx < 575), 0.05, 0.14)  # under the bicep
    ic.groove(U(seg(584, 392, 712, 396, 9), seg(580, 424, 708, 428, 9)), 0.06, 0.25)   # the leather wrap
    ic.groove(U(seg(612, 226, 612, 300, 8), seg(652, 218, 652, 300, 8), seg(692, 226, 692, 300, 8)), 0.05, 0.15)  # knuckles
    ic.groove(seg(566, 560, 640, 690, 8), 0.05, 0.12)  # the elbow crease
    return ic


def icon_torso():
    ic = crest(91)
    cx = 512
    t = poly([(cx - 230, 250), (cx + 230, 250), (cx + 250, 300), (cx + 180, 700), (cx - 180, 700), (cx - 250, 300)])
    t = np.clip(ndimage.gaussian_filter(t, 6) * 1.6 - 0.3, 0, 1)
    ic.part(t, z=0.30, lift=0.18, bevel=40, alb=BONE, rough=0.5)
    # pecs
    for s in (-1, 1):
        ic.emboss(ellipse(cx + s * 105, 365, 118, 70, s * 8), 0.07, 30)
        ic.groove(seg(cx + s * 20, 300, cx + s * 210, 290, 9), 0.04, 0.12)   # collarbone
    ic.groove(seg(cx, 300, cx, 680, 10), 0.06, 0.16)
    # abs: three rows
    for k, y in enumerate((470, 545, 620)):
        ic.groove(seg(cx - 110 + k * 8, y, cx + 110 - k * 8, y, 9), 0.05, 0.14)
    for s in (-1, 1):
        ic.groove(seg(cx + s * 135, 440, cx + s * 70, 690, 9), 0.05, 0.14)     # V-lines
    belt = box(cx, 720, 380, 60, 10)
    ic.part(belt, z=0.34, lift=0.08, bevel=10, alb=LEATHER, rough=0.6)
    ic.part(box(cx, 720, 70, 52, 6), z=0.40, lift=0.06, bevel=8, alb=BRASS, rough=0.3, metal=MET)
    ic.recess(box(cx, 720, 34, 22, 4), 0.06, 4)
    return ic


def icon_legs():
    ic = crest(92)
    cx = 512
    hips = box(cx, 270, 400, 90, 26)
    ic.part(hips, z=0.30, lift=0.12, bevel=24, alb=LEATHER, rough=0.6)
    for s in (-1, 1):
        x = cx + s * 98
        leg = U(limb(x, 300, x + s * 10, 520, 170, 50), limb(x + s * 10, 520, x + s * 4, 730, 140, 44))
        ic.part(leg, z=0.30, lift=0.20, bevel=34, alb=BONE, rough=0.5)
        ic.emboss(ellipse(x + s * 6, 420, 66, 100, s * 3), 0.06, 30)            # quad
        ic.emboss(circle(x + s * 8, 540, 34), 0.05, 14)                         # kneecap
        ic.groove(seg(x - s * 40, 330, x - s * 10, 500, 8), 0.05, 0.12)
        boot = box(x + s * 4, 770, 160, 80, 22)
        ic.part(boot, z=0.36, lift=0.08, bevel=14, alb=0.28, rough=0.45)
        ic.groove(seg(x - 70 + s * 4, 750, x + 70 + s * 4, 750, 7), 0.04, 0.2)
    return ic


# ================================================================ station medallions (an R6 student in the pose)
def medallion(seed):
    ic = Icon(seed)
    cx = cy = 512
    ic.part(circle(cx, cy, 470), z=0.16, lift=0.16, bevel=34, alb=BRASS, rough=0.32, metal=MET)
    for k in range(36):
        a = k * math.pi / 18
        ic.emboss(circle(cx + 440 * math.cos(a), cy + 440 * math.sin(a), 8), 0.05, 6)
    face = circle(cx, cy, 405)
    ic.custom(face, 0.25 + 0.012 * ic.noise(12), 0.26 * (0.9 + 0.1 * ic.noise(3)), 0.6, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - face, 9, 0), 6, 1), 9) * face)
    ic.groove(ring(cx, cy, 392, 6), 0.03, 0.1)
    return ic


def figure(ic, parts, alb=PAPER):
    m = U(*parts)
    ic.part(m, z=0.32, lift=0.18, bevel=22, alb=alb, rough=0.5)
    return m


def head(cx, cy, s=96):
    return box(cx, cy, s, s, s * 0.3)


def st_pushup():
    ic = medallion(100)
    floor = box(512, 700, 640, 34, 8)
    ic.part(floor, z=0.28, lift=0.06, bevel=8, alb=0.55, rough=0.7)   # the mat
    ic.groove(U(seg(220, 700, 800, 700, 5)), 0.02, 0.1)
    # body: shoulders at (360, 520), hips at (590, 580), feet at (790, 660)
    torso = limb(345, 545, 575, 585, 104, 20)
    legs = limb(570, 590, 800, 655, 92, 18)
    armA = limb(370, 545, 375, 680, 80, 16)
    hd = head(282, 515, 100)
    figure(ic, [torso, legs, armA, hd])
    ic.groove(seg(560, 568, 580, 610, 7), 0.04, 0.15)
    ic.ink(box(270, 508, 14, 14, 4))
    return ic


def st_pullup():
    ic = medallion(101)
    ic.part(box(512, 250, 560, 30, 12), z=0.36, lift=0.08, bevel=10, alb=0.42, rough=0.35, metal=MET)   # the bar
    for x in (232, 792):
        ic.part(box(x, 250, 40, 54, 10), z=0.4, lift=0.06, bevel=8, alb=BRASS, rough=0.3, metal=MET)
    armL = limb(452, 262, 470, 420, 76, 16)
    armR = limb(572, 262, 554, 420, 76, 16)
    torso = box(512, 500, 150, 200, 20)
    hd = head(512, 345, 104)
    legL = limb(476, 600, 470, 760, 72, 16)
    legR = limb(548, 600, 570, 740, 72, 16)
    figure(ic, [armL, armR, torso, hd, legL, legR])
    ic.ink(U(box(490, 340, 12, 12, 3), box(534, 340, 12, 12, 3)))
    ic.groove(seg(512, 405, 512, 598, 7), 0.035, 0.12)
    return ic


def st_situp():
    ic = medallion(102)
    ic.part(box(512, 700, 640, 34, 8), z=0.28, lift=0.06, bevel=8, alb=0.55, rough=0.7)
    # hips on the mat at (470, 650), torso up and back toward the knees, knees up at (640, 520), feet at (720, 670)
    torso = limb(470, 640, 560, 470, 104, 20)
    thigh = limb(480, 650, 650, 540, 90, 18)
    shin = limb(650, 540, 720, 670, 84, 16)
    hd = head(590, 400, 100)
    arm = limb(560, 460, 520, 380, 76, 16)
    figure(ic, [torso, thigh, shin, hd, arm])
    ic.ink(box(612, 392, 14, 14, 4))
    return ic


def st_squat():
    ic = medallion(103)
    ic.part(box(512, 735, 560, 30, 8), z=0.28, lift=0.06, bevel=8, alb=0.55, rough=0.7)
    # a deep squat: hips back at (470, 560), knees at (600, 560), feet under the knees
    torso = limb(470, 555, 520, 365, 112, 22)
    thigh = limb(460, 575, 610, 560, 96, 18)
    shin = limb(610, 560, 600, 715, 86, 16)
    hd = head(540, 290, 104)
    arm = limb(520, 400, 700, 410, 76, 16)
    figure(ic, [torso, thigh, shin, hd, arm])
    ic.ink(box(564, 284, 14, 14, 4))
    return ic


# ================================================================ badges
def badge_streak():
    ic = Icon(110)
    cx = 512
    for k in range(7):
        x, y = cx + (k - 3) * 96, 900
        dia = poly([(x, y - 30), (x + 24, y), (x, y + 30), (x - 24, y)])
        ic.part(dia, z=0.22, lift=0.1, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    # the candle with drips
    cand = box(cx, 590, 190, 380, 24)
    drips = U(*[box(cx + dx, 420 + l / 2, 30, l, 14) for dx, l in ((-70, 90), (-20, 50), (40, 120), (78, 70))])
    ic.part(U(cand, drips), z=0.28, lift=0.16, bevel=36, alb=0.88, rough=0.42, mottle=0.1)
    ic.part(ellipse(cx, 404, 92, 22), z=0.36, lift=0.04, bevel=10, alb=0.84, rough=0.4)
    ic.part(seg(cx, 404, cx, 360, 12), z=0.42, lift=0.02, bevel=4, alb=0.2, rough=0.6)
    fl = poly(bez((cx, 150), (cx + 90, 250), (cx + 80, 330), (cx, 360)) + bez((cx, 360), (cx - 80, 330), (cx - 90, 250), (cx, 150)))
    ic.part(fl, z=0.46, lift=0.14, bevel=40, alb=1.0, rough=0.25)
    ic.recess(ellipse(cx, 300, 26, 44), 0.05, 12)
    ic.part(box(cx, 810, 300, 50, 14), z=0.30, lift=0.06, bevel=10, alb=BRASS, rough=0.32, metal=MET)   # the dish
    return ic


def badge_best():
    ic = Icon(111)
    cx, cy = 512, 520
    for s in (-1, 1):
        for k in range(8):
            t = k / 7
            a = math.radians(110 + t * 150) if s < 0 else math.radians(70 - t * 150)
            x, y = cx + 330 * math.cos(a), cy + 330 * math.sin(a)
            rot = math.degrees(a) + (90 if s < 0 else -90) + s * 30
            ic.part(ellipse(x, y, 34, 74, rot), z=0.22, lift=0.12, bevel=22, alb=BRASS, rough=0.3, metal=MET)
        ic.part(M(np.abs(sd_circle(cx, cy, 300)) - 9) * ((xx - cx) * s > 40) * (yy > cy - 260), z=0.2, lift=0.05,
                bevel=6, alb=BRASS, rough=0.35, metal=MET)
    ic.part(poly(star_pts(cx, cy, 220, 92, 5)), z=0.30, lift=0.22, bevel=40, alb=0.98, rough=0.22, metal=MET)
    ic.part(box(cx, 890, 240, 60, 20), z=0.26, lift=0.08, bevel=14, alb=0.45, rough=0.5)    # ribbon tie
    for s in (-1, 1):
        ic.part(poly([(cx + s * 60, 900), (cx + s * 150, 1000), (cx + s * 110, 900)]), z=0.24, lift=0.05, bevel=8, alb=0.45, rough=0.5)
    return ic


def badge_daily():
    ic = Icon(112)
    cx = 512
    for y in (190, 834):
        ic.part(box(cx, y, 520, 64, 22), z=0.30, lift=0.10, bevel=16, alb=0.45, rough=0.5)        # oak caps
    for x in (300, 724):
        ic.part(box(x, 512, 36, 600, 14), z=0.34, lift=0.08, bevel=12, alb=BRASS, rough=0.3, metal=MET)
    glass = poly(bez((370, 230), (370, 420), (500, 470), (500, 512)) + bez((500, 512), (500, 560), (370, 600), (370, 794))
                 + [(654, 794)] + bez((654, 794), (654, 600), (524, 560), (524, 512)) + bez((524, 512), (524, 470), (654, 420), (654, 230)))
    ic.part(glass, z=0.24, lift=0.10, bevel=40, alb=0.75, rough=0.12)
    sand_top = poly([(410, 360), (614, 360), (522, 500), (502, 500)])
    sand_bot = poly([(400, 790), (624, 790), (560, 700), (464, 700)])
    ic.emboss(U(sand_top, sand_bot), 0.05, 20, alb=0.95, rough=0.7)
    ic.emboss(seg(512, 500, 512, 700, 8), 0.03, 4, alb=0.95)
    return ic


def icon_sore():
    ic = Icon(113)
    cx = cy = 512
    ic.part(circle(cx, cy, 300), z=0.2, lift=0.18, bevel=40, alb=BONE, rough=0.5)
    pts = [(cx - 40, cy - 300), (cx + 30, cy - 140), (cx - 50, cy - 40), (cx + 60, cy + 70), (cx - 10, cy + 170), (cx + 40, cy + 300)]
    cr = U(*[seg(*pts[i], *pts[i + 1], 30) for i in range(len(pts) - 1)])
    ic.recess(cr * circle(cx, cy, 300), 0.16, 8, alb=0.2)
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        ic.part(seg(cx + 350 * math.cos(a), cy + 350 * math.sin(a), cx + 430 * math.cos(a), cy + 430 * math.sin(a), 30),
                z=0.2, lift=0.08, bevel=10, alb=0.9, rough=0.5)
    return ic


GREY = {
    "TrainRateGood": rate_good, "TrainRateGreat": rate_great, "TrainRatePerfect": rate_perfect, "TrainRateMiss": rate_miss,
    "TrainIconArms": icon_arms, "TrainIconTorso": icon_torso, "TrainIconLegs": icon_legs,
    "TrainStationPushUp": st_pushup, "TrainStationPullUp": st_pullup, "TrainStationSitUp": st_situp, "TrainStationSquat": st_squat,
    "TrainBadgeStreak": badge_streak, "TrainBadgeBest": badge_best, "TrainBadgeDaily": badge_daily, "TrainIconSore": icon_sore,
}

TINT = {
    "TrainRateGood": (222, 224, 214), "TrainRateGreat": (226, 176, 92), "TrainRatePerfect": (240, 214, 130),
    "TrainRateMiss": (150, 142, 138), "TrainBadgeStreak": (235, 205, 120), "TrainBadgeBest": (235, 205, 120),
    "TrainBadgeDaily": (222, 224, 214), "TrainIconSore": (200, 92, 92),
}


def tinted(name, size):
    im = Image.open(OUT / f"{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    c = TINT.get(name, (232, 214, 168))
    a = np.array(im, f32) / 255
    rgb = a[..., :3] * np.array(c, f32)
    return Image.fromarray(np.dstack([rgb, a[..., 3:] * 255]).astype(np.uint8), "RGBA")


def contact():
    names = ["TrainGauge", "TrainRing", "TrainRingFake", "TrainMarkGlow"] + list(GREY)
    cols, cell = 5, 220
    rows = (len(names) + cols - 1) // cols
    im = Image.new("RGBA", (cols * cell, rows * (cell + 26)), (18, 15, 22, 255))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT_G, 14)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * (cell + 26)
        d.rounded_rectangle([x + 8, y + 8, x + cell - 8, y + cell - 8], 14, fill=(34, 29, 40, 255))
        if n == "TrainGauge":
            p = Image.open(OUT / f"{n}.png").convert("RGBA").resize((cell - 30, cell - 30), Image.LANCZOS)
        elif n in ("TrainRing", "TrainRingFake", "TrainMarkGlow"):
            p = Image.open(OUT / f"{n}.png").convert("RGBA").resize((cell - 30, cell - 30), Image.LANCZOS)
            a = np.array(p, f32) / 255
            col = (235, 205, 120) if n != "TrainRingFake" else (150, 142, 138)
            p = Image.fromarray(np.dstack([a[..., :3] * np.array(col, f32), a[..., 3:] * 255]).astype(np.uint8), "RGBA")
        else:
            p = tinted(n, cell - 30)
        im.alpha_composite(p, (x + 15, y + 15))
        d.text((x + cell / 2, y + cell + 6), n.replace("Train", ""), font=f, fill=(228, 222, 208, 255), anchor="mt")
    im.save(OUT / "contact_training.png")
    print("wrote contact sheet")


# ================================================================ the HUD mockup (for the design note)
def mockup():
    W, Hh = 1920, 1080
    bg = Image.new("RGBA", (W, Hh), (20, 16, 20, 255))
    src = HERE.parents[1].parent / "docs" / "img" / "training-gym-backdrop.jpg"
    if src.exists():
        bg = Image.open(src).convert("RGBA").resize((W, Hh), Image.LANCZOS)
    else:
        g = np.zeros((Hh, W, 3), f32)
        yy2, xx2 = np.mgrid[0:Hh, 0:W].astype(f32)
        v = np.clip(1 - np.hypot((xx2 - 700) / 1300, (yy2 - 500) / 900), 0, 1)
        g[:] = np.array([0.07, 0.055, 0.06])
        g += v[..., None] * np.array([0.22, 0.15, 0.09])
        bg = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    fT = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 30)
    fB = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 22)
    fBig = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 64)
    fS = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 18)
    gold, bone, crim = (235, 205, 120, 255), (228, 222, 208, 255), (200, 40, 60, 255)
    # header plate (top centre)
    hx, hy, hw, hh = W // 2 - 330, 34, 660, 92
    d.rounded_rectangle([hx, hy, hx + hw, hy + hh], 12, fill=(14, 12, 18, 225), outline=(150, 112, 50, 255), width=3)
    st = tinted("TrainStationPushUp", 76)
    bg.alpha_composite(st, (hx + 10, hy + 8))
    d.text((hx + 100, hy + 14), "PUSH-UPS", font=fT, fill=gold)
    d.text((hx + 100, hy + 54), "Arms  Lv 6  ·  Set 2", font=fB, fill=bone)
    d.text((hx + hw - 20, hy + 18), "Rep 9 / 16", font=fT, fill=bone, anchor="ra")
    for i, (n, label) in enumerate((("TrainBadgeStreak", "4 days"), ("TrainBadgeDaily", "Fresh ×2"))):
        b = tinted(n, 34)
        bx = hx + hw - 250 + i * 130
        bg.alpha_composite(b, (bx, hy + 52))
        d.text((bx + 38, hy + 56), label, font=fS, fill=bone)
    # gauge (right of centre)
    G = 380
    gx, gy = int(W * 0.70 - G / 2), int(Hh * 0.52 - G / 2)
    gauge_im = Image.open(OUT / "TrainGauge.png").convert("RGBA").resize((G, G), Image.LANCZOS)
    bg.alpha_composite(gauge_im, (gx, gy))
    icon = tinted("TrainIconArms", int(G * 0.2))
    bg.alpha_composite(icon, (gx + G // 2 - int(G * 0.1), gy + G // 2 - int(G * 0.1)))
    # the ring on its way in (r = 0.30 G) and the fake far out
    def ring_at(name, radius, col):
        size = int(radius / (RING_R / 1024))
        p = Image.open(OUT / f"{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
        a = np.array(p, f32) / 255
        p = Image.fromarray(np.dstack([a[..., :3] * np.array(col, f32), a[..., 3:] * 255]).astype(np.uint8), "RGBA")
        bg.alpha_composite(p, (gx + G // 2 - size // 2, gy + G // 2 - size // 2))
    ring_at("TrainRing", 0.27 * G, (235, 205, 120))
    # rating pop at the mark
    pm = tinted("TrainRatePerfect", 70)
    bg.alpha_composite(pm, (gx + G + 10, gy + 40))
    d.text((gx + G + 90, gy + 54), "PERFECT", font=fT, fill=gold)
    d.text((gx + G // 2, gy - 70), "×12", font=fBig, fill=gold, anchor="mm")
    d.text((gx + G // 2, gy - 26), "COMBO", font=fS, fill=bone, anchor="mm")
    # the key prompt under the gauge
    kx, ky = gx + G // 2, gy + G + 46
    d.rounded_rectangle([kx - 120, ky - 30, kx + 120, ky + 30], 10, fill=(36, 32, 42, 240), outline=(150, 112, 50, 255), width=3)
    d.text((kx, ky), "SPACE  ·  Ⓐ  ·  TAP", font=fB, fill=bone, anchor="mm")
    # the next-change bar (bottom left of the gauge)
    bx, by, bw = W // 2 - 300, 188, 600
    d.rounded_rectangle([bx, by, bx + bw, by + 26], 8, fill=(7, 6, 10, 235), outline=(150, 144, 158, 255), width=2)
    d.rounded_rectangle([bx + 3, by + 3, bx + 3 + int((bw - 6) * 0.64), by + 23], 6, fill=(200, 160, 80, 255))
    ai = tinted("TrainIconArms", 44)
    bg.alpha_composite(ai, (bx - 54, by - 10))
    d.text((bx, by - 34), "ARMS  ·  next change in ~31 reps  (Athletic)", font=fB, fill=bone)
    d.text((bx + bw, by + 34), "+6% Might at Lv 6", font=fS, fill=(150, 142, 138, 255), anchor="ra")
    # soreness chip
    so = tinted("TrainIconSore", 34)
    bg.alpha_composite(so, (bx + bw + 14, by - 4))
    d.text((bx + bw + 52, by), "Sore 20%", font=fS, fill=(214, 120, 120, 255))
    # tutorial hint strip
    d.text((gx + G // 2, gy + G + 110), "Press on the brass mark  ·  let cracked rings pass  ·  HOLD: keep holding",
           font=fS, fill=(150, 142, 138, 255), anchor="mm")
    bg.convert("RGB").save(OUT / "preview_hud.png", quality=92)
    print("wrote preview_hud.png")


if __name__ == "__main__":
    want = sys.argv[1:]
    if not want or "TrainGauge" in want:
        gauge()
    if not want or "TrainMarkGlow" in want:
        mark_glow()
    if not want or "TrainRing" in want:
        ring_sprite(False)
    if not want or "TrainRingFake" in want:
        ring_sprite(True)
    for n, fn in GREY.items():
        if want and n not in want:
            continue
        lum, alpha = fn().render()
        save_grey(lum, alpha, n)
    contact()
    mockup()
