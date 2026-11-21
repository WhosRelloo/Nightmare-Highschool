"""The Bell Tower: concept art for the notoriety (Bells), clock, discipline and quest HUD (Nightmare Highschool).

Design: docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md (direction A).
Baked with the same PBR shader as the Thornrose health bar (make_health_pbr.py): height field -> normals plus the
school's seamless detail maps (art/props/source), GGX + Lambert, warm key, cool fill, candle rim, AO.

Pieces (art/ui/hud/out/belltower/), all original:
  Dial.png          640x640  cast-brass day dial; the rim is today's timetable (crimson enamel class periods, brass
                             breaks, a blackened-iron curfew band with stars); a window for the moon icon
  DialHand.png      640x640  the brass hand (points up; rotated in game)
  BellHollow.png    256x256  a bell that isn't sure who you are (blackened iron, brass lip)
  BellTarnished.png 256x256  a partial description (verdigris brass)
  BellLit.png       256x256  seen (hot polished brass with a candle glow at the mouth)
  BellGlow.png      256x256  greyscale halo behind a lit bell
  BellRail.png     1400x220  the forged arm the five bells hang from, with a wall plate and scroll
  Note*.png         200x200  witness-note tokens: Face, Outfit, Form, Clique, Weapon, Companion
  Seal.png          256x256  greyscale wax conduct seal (tinted per level in game); SealBroken.png for Suspension
  Slip.png          420x150  a detention slip (paper, red rule, brass eyelet); text is live
  LeadCard.png     1000x300  the parchment lead card in its brass hinge clip, with a crimson ribbon
  PipEmpty / PipFang 96x96   quest progress pips
  TowerPlate.png    600x200  blackened-iron plate with a brass bead (9-slice, centre 60..540 x 60..140)
  Candle.png        128x192  a search-ring candle for the map (and direction C's candelabra)
  Seal<Level>.png            Seal tinted per level, for the mockups only

  python make_belltower.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import make_health_pbr as P

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "belltower"
OUT.mkdir(parents=True, exist_ok=True)


def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def dist(m):
    return ndimage.distance_transform_edt(m > 0.5).astype(np.float32)


def soft(m, s=0.8):
    return np.clip(ndimage.gaussian_filter(m, s), 0, 1)


def mats(W, H, period=256):
    iron = P.material("Iron", (W, H), period, tint=(0.24, 0.23, 0.26), rough_mul=0.75)
    brass = P.material("Brass", (W, H), period, tint=(1.0, 0.84, 0.58), rough_mul=0.62, rough_add=-0.06)
    return iron, brass


def mix(a, b, m):
    m = m[..., None] if a.ndim == 3 else m
    return a * (1 - m) + b * m


def line_mask(size, segs, width, ss=2):
    w, h = size
    im = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    for seg in segs:
        d.line([(x * ss, y * ss) for x, y in seg], fill=255, width=int(width * ss), joint="curve")
    return np.array(im.resize((w, h), Image.BOX), np.float32) / 255.0


def arc_mask(size, cx, cy, r0, r1, a0, a1):
    """Annular sector; angles in degrees, 0 = up, clockwise."""
    w, h = size
    YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
    R = np.hypot(XX - cx, YY - cy)
    A = (np.degrees(np.arctan2(XX - cx, -(YY - cy))) + 360) % 360
    a0 %= 360
    a1 %= 360
    inang = (A >= a0) & (A <= a1) if a0 <= a1 else (A >= a0) | (A <= a1)
    m = ((R >= r0) & (R <= r1) & inang).astype(np.float32)
    return soft(m, 0.7)


# ---------------------------------------------------------------- the dial
SEGMENTS = [  # (start h, end h, kind) from Config.SchoolSchedule.Segments
    (0, 6, "curfew"), (6, 7.5, "plain"), (7.5, 8, "plain"),
    (8, 8 + 20 / 60, "class"), (8 + 20 / 60, 9, "class"), (9, 9 + 5 / 60, "brass"),
    (9 + 5 / 60, 9.75, "class"), (9.75, 10, "brass"), (10, 10 + 40 / 60, "class"),
    (10 + 40 / 60, 10.75, "brass"), (10.75, 11 + 25 / 60, "class"), (11 + 25 / 60, 12, "brass"),
    (12, 17, "plain"), (17, 21, "plain"), (21, 22, "plain"), (22, 24, "curfew"),
]


def hour_angle(h):
    return (h / 24.0) * 360 + 180  # midnight at the bottom, noon at the top


def dial():
    S = 640
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    R = np.hypot(XX - c, YY - c)
    A = (np.degrees(np.arctan2(XX - c, -(YY - c))) + 360) % 360
    iron, brass = mats(S, S, 320)
    Hf = np.zeros((S, S), np.float32)
    # outer bezel: knurled brass
    bezel = soft(((R >= 292) & (R <= 316)).astype(np.float32))
    knurl = 0.5 + 0.5 * np.cos(np.radians(A) * 120)
    Hf = np.maximum(Hf, bezel * (0.55 + 0.35 * P.dome(dist(bezel), 9) + 0.05 * knurl))
    # timetable channel (recessed) with enamel arcs
    chan = soft(((R >= 250) & (R < 292)).astype(np.float32))
    Hf = np.maximum(Hf, chan * 0.32)
    cls = np.zeros((S, S), np.float32)
    brs = np.zeros((S, S), np.float32)
    cur = np.zeros((S, S), np.float32)
    for h0, h1, kind in SEGMENTS:
        a0, a1 = hour_angle(h0), hour_angle(h1)
        if kind == "class":
            cls = np.maximum(cls, arc_mask((S, S), c, c, 256, 287, a0 + 0.45, a1 - 0.45))
        elif kind == "brass":
            brs = np.maximum(brs, arc_mask((S, S), c, c, 258, 285, a0 + 0.2, a1 - 0.2))
        elif kind == "curfew":
            cur = np.maximum(cur, arc_mask((S, S), c, c, 254, 289, a0, a1))
    Hf = np.maximum(Hf, cls * (0.42 + 0.06 * P.dome(dist(cls), 5)))
    Hf = np.maximum(Hf, brs * (0.5 + 0.1 * P.dome(dist(brs), 4)))
    Hf = np.maximum(Hf, cur * 0.4)
    # stars punched into the curfew band
    rng = np.random.default_rng(11)
    stars = []
    for _ in range(60):
        hh = rng.uniform(22.1, 29.9) % 24
        rr = rng.uniform(260, 283)
        ang = math.radians(hour_angle(hh))
        x, y = c + rr * math.sin(ang), c - rr * math.cos(ang)
        s = rng.choice([1.4, 1.8, 2.4])
        stars.append((x - s, y - s, x + s, y + s))
    star = P.polymask((S, S), [], stars) * cur
    # hour ring: brass with 24 ticks
    ring = soft(((R >= 236) & (R < 250)).astype(np.float32))
    Hf = np.maximum(Hf, ring * (0.6 + 0.2 * P.dome(dist(ring), 5)))
    ticks = []
    for i in range(24):
        ang = math.radians(hour_angle(i))
        big = i % 6 == 0
        r0, r1 = (206, 236) if big else (220, 236)
        wdt = 4.2 if big else 2.2
        ux, uy = math.sin(ang), -math.cos(ang)
        px, py = -uy, ux
        ticks.append([(c + ux * r0 + px * wdt, c + uy * r0 + py * wdt), (c + ux * r1 + px * wdt, c + uy * r1 + py * wdt),
                      (c + ux * r1 - px * wdt, c + uy * r1 - py * wdt), (c + ux * r0 - px * wdt, c + uy * r0 - py * wdt)])
    # lozenge markers at 0/6/12/18
    for i in (0, 6, 12, 18):
        ang = math.radians(hour_angle(i))
        ux, uy = math.sin(ang), -math.cos(ang)
        px, py = -uy, ux
        m0, m1 = 182, 204
        mid = (m0 + m1) / 2
        ticks.append([(c + ux * m0, c + uy * m0), (c + ux * mid + px * 7, c + uy * mid + py * 7),
                      (c + ux * m1, c + uy * m1), (c + ux * mid - px * 7, c + uy * mid - py * 7)])
    tick = P.polymask((S, S), ticks)
    # a raised sun at noon (top) and a crescent at midnight (bottom) on the face
    sx, sy = c, c - 160
    rays = []
    for k in range(12):
        a = k * math.pi / 6
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        rays.append([(sx + ux * 17 + px * 3, sy + uy * 17 + py * 3), (sx + ux * 26, sy + uy * 26),
                     (sx + ux * 17 - px * 3, sy + uy * 17 - py * 3)])
    sun = np.clip(P.polymask((S, S), rays, [(sx - 13, sy - 13, sx + 13, sy + 13)]), 0, 1)
    mx, my = c, c + 160
    cres = np.clip(P.polymask((S, S), [], [(mx - 16, my - 16, mx + 16, my + 16)])
                   - P.polymask((S, S), [], [(mx - 9, my - 20, mx + 19, my + 10)]), 0, 1)
    emblem = np.clip(sun + cres, 0, 1) * (R < 236)
    # face: blued iron with an engraved star chart
    face = soft((R < 236).astype(np.float32))
    Hf = np.maximum(Hf, face * 0.25)
    Hf = np.maximum(Hf, tick * (0.5 + 0.15 * P.dome(dist(tick), 3)))
    Hf = np.maximum(Hf, emblem * (0.42 + 0.15 * P.dome(dist(emblem), 4)))
    eng = np.zeros((S, S), np.float32)
    for rr in (128, 170):
        eng = np.maximum(eng, np.exp(-((R - rr) / 0.9) ** 2))
    # constellation: dots joined by fine lines
    pts = [(c + 140 * math.sin(math.radians(a)), c - 140 * math.cos(math.radians(a)) * 0.92) for a in (300, 322, 338, 352)]
    pts2 = [(c + 150 * math.sin(math.radians(a)), c - 150 * math.cos(math.radians(a))) for a in (40, 58, 70, 84, 98)]
    lines = line_mask((S, S), [pts, pts2], 1.2)
    dots = P.polymask((S, S), [], [(x - 3, y - 3, x + 3, y + 3) for x, y in pts + pts2])
    eng = np.clip(eng + lines * 0.8, 0, 1) * face * (R > 112)
    Hf -= eng * 0.05
    Hf = np.maximum(Hf, dots * face * 0.32)
    # moon window: brass bead, transparent centre
    bead = soft(((R >= 96) & (R <= 112)).astype(np.float32))
    Hf = np.maximum(Hf, bead * (0.55 + 0.35 * P.dome(dist(bead), 6)))
    hole = soft((R < 96).astype(np.float32), 0.6)
    # four rivets on the bezel
    riv = P.polymask((S, S), [], [(c + 304 * math.sin(math.radians(a)) - 6, c - 304 * math.cos(math.radians(a)) - 6,
                                   c + 304 * math.sin(math.radians(a)) + 6, c - 304 * math.cos(math.radians(a)) + 6)
                                  for a in (45, 135, 225, 315)])
    Hf = np.maximum(Hf, riv * (0.95 + 0.2 * P.dome(dist(riv), 5)))
    dents = ndimage.gaussian_filter(rng.standard_normal((S, S)), 2.5)
    Hf -= np.clip(dents, 0, None) * 0.03 * face
    # materials
    is_brass = np.clip(bezel + brs + ring + tick + bead + riv + dots * face + emblem, 0, 1)
    enamel = cls
    albedo = mix(iron[0] * 0.75, brass[0], is_brass)
    albedo = mix(albedo, np.array([0.30, 0.012, 0.025]), enamel)            # crimson enamel
    albedo = mix(albedo, np.array([0.012, 0.012, 0.018]), cur * (1 - star))  # blackened iron
    albedo = mix(albedo, np.array([0.9, 0.82, 0.62]), star)                 # silvered stars
    albedo = mix(albedo, np.array([0.035, 0.04, 0.06]), face * (1 - is_brass) * (1 - eng))  # blued face
    albedo = mix(albedo, np.array([0.55, 0.45, 0.3]), eng * 0.6)            # brass-filled engraving
    rough = mix(iron[2], brass[2], is_brass)
    rough = mix(rough, 0.12, enamel)
    rough = mix(rough, 0.55, cur)
    metal = mix(np.full((S, S), 0.85, np.float32), np.ones((S, S), np.float32), is_brass)
    metal = mix(metal, 0.0, enamel)
    detail = mix(iron[1], brass[1], is_brass)
    N = P.normals_from(Hf, 30.0, detail, 0.25)
    ao = P.ao_from(Hf, 5, 2.4)
    rgb = P.shade(albedo, N, rough, metal, ao)
    alpha = np.clip(soft((R <= 317).astype(np.float32)) - hole, 0, 1)
    save(rgb, alpha, "Dial.png")

    # the hand
    Hh = np.zeros((S, S), np.float32)
    shaft = P.polymask((S, S), [[(c - 5, c + 20), (c - 2.5, c - 232), (c, c - 268), (c + 2.5, c - 232), (c + 5, c + 20)]])
    lozenge = P.polymask((S, S), [[(c, c - 252), (c + 12, c - 222), (c, c - 196), (c - 12, c - 222)]])
    lhole = P.polymask((S, S), [[(c, c - 240), (c + 5, c - 222), (c, c - 206), (c - 5, c - 222)]])
    crescent = np.clip(P.polymask((S, S), [], [(c - 26, c + 22, c + 26, c + 74)]) -
                       P.polymask((S, S), [], [(c - 22, c + 14, c + 22, c + 58)]), 0, 1)
    boss = P.polymask((S, S), [], [(c - 16, c - 16, c + 16, c + 16)])
    hand = np.clip(shaft + lozenge - lhole + crescent + boss, 0, 1)
    Hh = np.maximum(Hh, hand * (0.5 + 0.4 * P.dome(dist(hand), 4)))
    Hh = np.maximum(Hh, boss * (0.9 + 0.3 * P.dome(dist(boss), 9)))
    alb = brass[0] * 1.05
    N = P.normals_from(Hh, 28.0, brass[1], 0.2)
    rgb = P.shade(alb, N, brass[2] * 0.8, np.ones((S, S), np.float32), P.ao_from(Hh, 3, 2))
    sh = ndimage.shift(ndimage.gaussian_filter(hand, 4), (6, 5)) * 0.55
    rgb = rgb * hand[..., None]
    alpha = np.clip(hand + sh * (1 - hand), 0, 1)
    rgb = rgb / np.maximum(alpha[..., None], 1e-3) * hand[..., None]
    save(rgb, alpha, "DialHand.png")


# ---------------------------------------------------------------- bells
BELL_PROFILE = [(44, 22), (52, 40), (62, 54), (78, 62), (104, 65), (140, 69), (166, 76), (188, 88), (204, 99),
                (214, 104), (220, 101), (224, 94)]


def bell(kind):
    S = 256
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    ys = np.array([p[0] for p in BELL_PROFILE], np.float32)
    ws = np.array([p[1] for p in BELL_PROFILE], np.float32)
    halfw = np.interp(YY[:, 0], ys, ws)
    halfw[(YY[:, 0] < ys[0]) | (YY[:, 0] > ys[-1])] = 0
    dx = (XX - c) / np.maximum(halfw[:, None], 1)
    body = soft(((np.abs(dx) <= 1) & (halfw[:, None] > 0)).astype(np.float32), 0.7)
    cyl = np.sqrt(np.clip(1 - dx ** 2, 0, 1))
    Hf = body * (0.3 + 0.6 * cyl)
    # shoulder dome
    top = np.clip(1 - (YY - 44) / 30, 0, 1) * body
    Hf += top * 0.1
    # lip and the waist bands
    lip = body * ((YY >= 204) & (YY <= 224))
    Hf += lip * 0.12 * cyl
    for gy in (118, 132, 196):
        Hf -= body * np.exp(-((YY - gy) / 1.4) ** 2) * 0.08
    band = body * ((YY > 120) & (YY < 130))
    # crown loop and clapper
    loop = np.clip(P.polymask((S, S), [], [(c - 20, 8, c + 20, 50)]) - P.polymask((S, S), [], [(c - 10, 18, c + 10, 40)]), 0, 1)
    loop *= (YY < 46)
    Hf = np.maximum(Hf, loop * (0.4 + 0.4 * P.dome(dist(loop), 5)))
    clap = P.polymask((S, S), [], [(c - 12, 220, c + 12, 244)])
    Hf = np.maximum(Hf, clap * (0.2 + 0.4 * P.dome(dist(clap), 8)))
    # an engraved crescent on the waist
    cres = np.clip(P.polymask((S, S), [], [(c - 15, 146, c + 15, 176)]) - P.polymask((S, S), [], [(c - 9, 142, c + 17, 170)]), 0, 1)
    Hf += cres * 0.05
    rng = np.random.default_rng(3)
    iron, brass = mats(S, S, 200)
    detail = brass[1]
    if kind == "Hollow":
        albedo = iron[0] * 0.55
        rough = iron[2]
        metal = np.full((S, S), 0.8, np.float32)
        rimb = np.clip(lip + loop * 0.0 + cres, 0, 1)
        albedo = mix(albedo, brass[0] * 0.8, rimb)
        rough = mix(rough, brass[2], rimb)
        metal = mix(metal, 1.0, rimb)
        emis = None
        detail = iron[1]
    elif kind == "Tarnished":
        n = ndimage.gaussian_filter(rng.standard_normal((S, S)), 6)
        n = np.clip((n - n.min()) / (np.ptp(n) + 1e-6), 0, 1)
        grime = np.clip((n - 0.35) * 2.2, 0, 1) * (1 - cyl * 0.5)
        grime = np.clip(grime + ndimage.gaussian_filter((Hf < 0.45).astype(np.float32), 3) * 0.6, 0, 1)
        verd = np.array([0.10, 0.22, 0.17])
        albedo = mix(brass[0] * 0.7, verd, grime)
        rough = mix(brass[2] + 0.15, 0.85, grime)
        metal = mix(np.ones((S, S), np.float32), 0.15, grime)
        emis = None
    else:  # Lit
        albedo = brass[0] * 1.12
        rough = brass[2] * 0.55
        metal = np.ones((S, S), np.float32)
        mouth = np.exp(-(((XX - c) / 70) ** 2 + ((YY - 226) / 14) ** 2))
        inner = np.exp(-(((XX - c) / 48) ** 2 + ((YY - 200) / 50) ** 2)) * body
        emis = (mouth[..., None] * np.array([1.4, 0.75, 0.25]) * 0.9 + inner[..., None] * np.array([0.5, 0.28, 0.08]) * 0.6)
    N = P.normals_from(Hf, 26.0, detail, 0.22)
    ao = P.ao_from(Hf, 4, 2.0)
    rgb = P.shade(albedo, N, rough, metal, ao, emissive=emis)
    alpha = np.clip(body + loop + clap, 0, 1)
    if kind == "Lit":
        rim = np.clip(body - ndimage.binary_erosion(body > 0.5, iterations=3), 0, 1)
        rgb = rgb + rim[..., None] * np.array([0.25, 0.14, 0.04])
    save(rgb, alpha, f"Bell{kind}.png")


def bell_glow():
    S = 256
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    g = np.exp(-(((XX - 128) / 86) ** 2 + ((YY - 150) / 98) ** 2))
    g = g ** 1.6
    save(np.ones((S, S, 3)), g, "BellGlow.png")


# ---------------------------------------------------------------- bell rail
def rail():
    W, H = 1400, 220
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = mats(W, H, 320)
    Hf = np.zeros((H, W), np.float32)
    bar = P.polymask((W, H), [[(40, 32), (1290, 32), (1290, 66), (40, 66)]])
    Hf = np.maximum(Hf, bar * (0.35 + 0.45 * P.dome(dist(bar), 11)))
    twist = 0.5 + 0.5 * np.sin((XX - YY * 1.2) / 9.0)
    Hf += bar * twist * 0.06 * ((XX > 90) & (XX < 1240))
    # wall plate (right) with a scroll bracket
    plate = P.polymask((W, H), [[(1290, 10), (1380, 10), (1392, 30), (1392, 190), (1380, 210), (1290, 210), (1278, 190), (1278, 30)]])
    Hf = np.maximum(Hf, plate * (0.4 + 0.3 * P.dome(dist(plate), 10)))
    scroll_pts = []
    for t in np.linspace(0, 4.2 * math.pi, 200):
        r = 54 * math.exp(-0.16 * t)
        scroll_pts.append((1230 + r * math.cos(t + math.pi / 2) * 0.9 - 0, 118 + r * math.sin(t + math.pi / 2) * -1))
    brace = line_mask((W, H), [[(1278, 180), (1180, 60)], scroll_pts], 9)
    Hf = np.maximum(Hf, brace * (0.35 + 0.35 * P.dome(dist(brace), 5)))
    # finial on the free end: a brass spearhead
    fin = P.polymask((W, H), [[(2, 49), (36, 22), (56, 49), (36, 76)]])
    collar = P.polymask((W, H), [[(50, 24), (70, 24), (70, 74), (50, 74)]])
    # brass collars and five hooks (hooks at x = 150 + i*230 approx)
    hooks = []
    cols = []
    for i in range(5):
        x = 150 + i * 240
        cols.append([(x - 18, 26), (x + 18, 26), (x + 18, 72), (x - 18, 72)])
        hooks.append([(x, 66), (x, 104), (x - 12, 116), (x - 18, 104)])
    col = P.polymask((W, H), cols)
    hook = line_mask((W, H), hooks, 8)
    Hf = np.maximum(Hf, np.clip(col + collar, 0, 1) * (0.75 + 0.2 * P.dome(dist(np.clip(col + collar, 0, 1)), 5)))
    Hf = np.maximum(Hf, hook * (0.5 + 0.3 * P.dome(dist(hook), 3)))
    Hf = np.maximum(Hf, fin * (0.7 + 0.3 * P.dome(dist(fin), 8)))
    rivs = P.polymask((W, H), [], [(1335 - 8, y - 8, 1335 + 8, y + 8) for y in (34, 186)])
    Hf = np.maximum(Hf, rivs * (0.9 + 0.2 * P.dome(dist(rivs), 6)))
    gem = P.polymask((W, H), [], [(1335 - 18, 92, 1335 + 18, 128)])
    Hf = np.maximum(Hf, gem * (0.8 + 0.5 * P.dome(dist(gem), 14)))
    is_brass = np.clip(col + collar + fin + rivs + hook * 0.0, 0, 1)
    albedo = mix(iron[0], brass[0], is_brass)
    albedo = mix(albedo, np.array([0.4, 0.012, 0.03]), gem)
    rough = mix(mix(iron[2], brass[2], is_brass), 0.08, gem)
    metal = mix(mix(np.full((H, W), 0.85, np.float32), 1.0, is_brass), 0.0, gem)
    N = P.normals_from(Hf, 30.0, mix(iron[1], brass[1], is_brass), 0.3)
    glow = (np.clip(1 - np.hypot(XX - 1341, YY - 114) / 16, 0, 1) ** 2)[..., None] * np.array([0.5, 0.04, 0.05]) * gem[..., None]
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 5, 2.2), emissive=glow)
    alpha = np.clip(bar + plate + brace + fin + col + collar + hook + rivs + gem, 0, 1)
    save(rgb, alpha, "BellRail.png")


# ---------------------------------------------------------------- witness-note tokens
def _icon(name, S=200):
    c = S / 2
    polys, ells, lines, holes = [], [], [], []
    if name == "Face":       # a half mask
        ells.append((c - 44, c - 34, c + 44, c + 40))
        holes += [(c - 30, c - 12, c - 8, c + 4), (c + 8, c - 12, c + 30, c + 4)]
        polys.append([(c - 44, c - 4), (c - 62, c - 22), (c - 40, c - 16)])
        polys.append([(c + 44, c - 4), (c + 62, c - 22), (c + 40, c - 16)])
    elif name == "Outfit":   # collar and tie
        polys += [[(c - 46, c - 40), (c - 6, c - 30), (c - 14, c - 4)], [(c + 46, c - 40), (c + 6, c - 30), (c + 14, c - 4)],
                  [(c - 9, c - 32), (c + 9, c - 32), (c + 7, c - 16), (c - 7, c - 16)],
                  [(c - 7, c - 16), (c + 7, c - 16), (c + 16, c + 34), (c, c + 52), (c - 16, c + 34)]]
    elif name == "Form":     # a fang and three claw rakes
        polys += [[(c - 40, c - 46), (c - 6, c - 46), (c - 18, c + 30)],
                  [(c + 2, c - 44), (c + 14, c - 44), (c + 6, c - 6)]]
        for k in range(3):
            x = c + 18 + k * 13
            polys.append([(x, c - 18), (x + 7, c - 18), (x - 8, c + 46), (x - 12, c + 44)])
    elif name == "Clique":   # a rosette with tails
        ells.append((c - 34, c - 50, c + 34, c + 18))
        holes.append((c - 14, c - 30, c + 14, c - 2))
        polys += [[(c - 22, c + 6), (c - 4, c + 10), (c - 18, c + 54), (c - 30, c + 40)],
                  [(c + 22, c + 6), (c + 4, c + 10), (c + 18, c + 54), (c + 30, c + 40)]]
    elif name == "Weapon":   # a dagger, point down-left
        ang = math.radians(-45)
        def rot(x, y):
            return (c + x * math.cos(ang) - y * math.sin(ang), c + x * math.sin(ang) + y * math.cos(ang))
        polys.append([rot(-9, -8), rot(9, -8), rot(0, 62)])
        polys.append([rot(-30, -14), rot(30, -14), rot(30, -6), rot(-30, -6)])
        polys.append([rot(-6, -14), rot(6, -14), rot(5, -46), rot(-5, -46)])
        x0, y0 = rot(0, -54)
        ells.append((x0 - 10, y0 - 10, x0 + 10, y0 + 10))
    elif name == "Companion":  # two busts
        for dx, s in ((-18, 1.0), (20, 0.85)):
            ells.append((c + dx - 16 * s, c - 44 * s, c + dx + 16 * s, c - 12 * s))
            polys.append([(c + dx - 34 * s, c + 46), (c + dx - 26 * s, c - 4 * s), (c + dx, c - 10 * s),
                          (c + dx + 26 * s, c - 4 * s), (c + dx + 34 * s, c + 46)])
    m = P.polymask((S, S), polys, ells)
    if holes:
        m = np.clip(m - P.polymask((S, S), [], holes), 0, 1)
    return m


def note(name):
    S = 200
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    R = np.hypot(XX - c, YY - c)
    iron, brass = mats(S, S, 180)
    coin = soft((R <= 92).astype(np.float32))
    rim = soft(((R >= 80) & (R <= 92)).astype(np.float32))
    field = soft((R < 80).astype(np.float32))
    icon = _icon(name, S) * field
    rng = np.random.default_rng(5)
    stip = ndimage.gaussian_filter(rng.standard_normal((S, S)), 0.8)
    Hf = coin * 0.3
    Hf = np.maximum(Hf, rim * (0.55 + 0.3 * P.dome(dist(rim), 5)))
    Hf -= field * 0.05 + field * np.clip(stip, 0, None) * 0.015
    Hf = np.maximum(Hf, icon * (0.38 + 0.18 * P.dome(dist(icon), 5)))
    beads = P.polymask((S, S), [], [(c + 86 * math.cos(t) - 2.6, c + 86 * math.sin(t) - 2.6, c + 86 * math.cos(t) + 2.6, c + 86 * math.sin(t) + 2.6)
                                    for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
    Hf = np.maximum(Hf, beads * rim * (0.95 + 0.1 * P.dome(dist(beads), 2)))
    albedo = mix(brass[0] * 0.95, np.array([0.012, 0.009, 0.01]), field * (1 - icon))
    albedo = mix(albedo, brass[0] * 1.15, icon)
    rough = mix(brass[2], 0.85, field * (1 - icon))
    rough = mix(rough, brass[2] * 0.6, icon)
    metal = mix(np.ones((S, S), np.float32), 0.3, field * (1 - icon))
    N = P.normals_from(Hf, 22.0, brass[1], 0.2)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 3, 2.4))
    save(rgb, coin, f"Note{name}.png")


# ---------------------------------------------------------------- wax seal
def seal(broken=False):
    S = 256
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    A = np.arctan2(YY - c, XX - c)
    R = np.hypot(XX - c, YY - c)
    rng = np.random.default_rng(9)
    wob = sum(rng.uniform(1, 4) * np.sin(k * A + rng.uniform(0, 6)) for k in (3, 5, 7, 11))
    blob = soft((R <= 104 + wob).astype(np.float32), 1.0)
    rim = soft(((R >= 70) & (R <= 76)).astype(np.float32))
    Hf = blob * (0.35 + 0.45 * P.dome(dist(blob), 26))
    Hf -= rim * 0.08
    inner = soft((R < 70).astype(np.float32))
    Hf -= inner * 0.12
    # embossed bell sigil (the school bell)
    sig = []
    prof = [(-44, 10), (-36, 20), (-26, 26), (0, 28), (20, 34), (30, 42), (36, 40)]
    pts = [(c + w, c + y) for y, w in prof] + [(c - w, c + y) for y, w in reversed(prof)]
    sig.append(pts)
    bellm = P.polymask((S, S), sig, [(c - 7, c + 34, c + 7, c + 48), (c - 7, c - 56, c + 7, c - 42)])
    Hf += bellm * inner * (0.1 + 0.08 * P.dome(dist(bellm), 6))
    # little stars round the inner ring
    st = P.polymask((S, S), [], [(c + 58 * math.cos(t) - 2.5, c + 58 * math.sin(t) - 2.5, c + 58 * math.cos(t) + 2.5, c + 58 * math.sin(t) + 2.5)
                                 for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
    Hf += st * inner * 0.08
    alpha = blob
    if broken:
        crack = line_mask((S, S), [[(c - 8, c - 110), (c + 6, c - 50), (c - 10, c - 8), (c + 12, c + 40), (c - 2, c + 110)]], 5)
        alpha = np.clip(blob - crack, 0, 1)
        Hf -= ndimage.gaussian_filter(crack, 3) * 0.2
    albedo = np.full((S, S, 3), 0.62, np.float32)
    N = P.normals_from(Hf, 24.0)
    rgb = P.shade(albedo, N, np.full((S, S), 0.32, np.float32), np.zeros((S, S), np.float32), P.ao_from(Hf, 4, 2.0))
    name = "SealBroken.png" if broken else "Seal.png"
    save(rgb, alpha, name)
    return rgb, alpha


def seal_tints(rgb, alpha, broken_rgb, broken_alpha):
    tints = {"Warning": (1.0, 0.66, 0.28), "Detention": (0.86, 0.12, 0.16), "Probation": (0.42, 0.06, 0.1),
             "Clear": (0.86, 0.74, 0.46)}
    for k, t in tints.items():
        save(rgb * np.array(t), alpha, f"Seal{k}.png")
    save(broken_rgb * np.array((0.2, 0.17, 0.19)), broken_alpha, "SealSuspension.png")


# ---------------------------------------------------------------- paper pieces
def paper_tex(W, H, period=300, tint=(1.0, 0.93, 0.78)):
    return P.material("Paper", (W, H), period, tint=tint, rough_mul=1.0, metal=0.0)


def deckle(W, H, inset, seed, amp=3.0):
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(rng.standard_normal((H, W)), 2.0) * amp * 3
    d = np.minimum(np.minimum(XX - inset, W - 1 - inset - XX), np.minimum(YY - inset, H - 1 - inset - YY))
    return soft((d + n > 0).astype(np.float32), 0.6)


def slip():
    W, H = 420, 150
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    pap = paper_tex(W, H, 260)
    m = deckle(W, H, 6, 21)
    iron, brass = mats(W, H, 160)
    eye = soft(((np.hypot(XX - 40, YY - 75) <= 16) & (np.hypot(XX - 40, YY - 75) >= 8)).astype(np.float32))
    holem = soft((np.hypot(XX - 40, YY - 75) < 8).astype(np.float32))
    Hf = m * 0.3 + ndimage.gaussian_filter(np.random.default_rng(4).standard_normal((H, W)), 6) * 0.02 * m
    Hf = np.maximum(Hf, eye * (0.6 + 0.3 * P.dome(dist(eye), 4)))
    rule = ((np.abs(YY - 30) < 1.4) | (np.abs(YY - 122) < 1.4)) & (XX > 72) & (XX < W - 20)
    perf = (np.abs(XX - 72) < 1.2) & ((YY.astype(int) // 6) % 2 == 0) & (YY > 14) & (YY < H - 14)
    albedo = mix(pap[0], np.array([0.45, 0.03, 0.04]), rule.astype(np.float32) * 0.9)
    albedo = mix(albedo, np.array([0.3, 0.22, 0.15]), perf.astype(np.float32) * 0.8)
    edge = np.clip(1 - dist(m) / 10, 0, 1) * m
    albedo = albedo * (1 - edge[..., None] * 0.35)
    albedo = mix(albedo, brass[0], eye)
    rough = mix(pap[2], brass[2], eye)
    metal = mix(np.zeros((H, W), np.float32), 1.0, eye)
    N = P.normals_from(Hf, 18.0, mix(pap[1], brass[1], eye), 0.25)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 3, 2.0))
    save(rgb, np.clip(m - holem, 0, 1), "Slip.png")


def lead_card():
    W, H = 1000, 300
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    pap = paper_tex(W, H, 340, tint=(1.0, 0.9, 0.72))
    iron, brass = mats(W, H, 260)
    card = deckle(W, H, 0, 31, 2.0) * ((XX > 40) & (XX < W - 12) & (YY > 26) & (YY < H - 10))
    card = soft(card.astype(np.float32), 0.7)
    # foxing and a tea stain
    rng = np.random.default_rng(12)
    fox = ndimage.gaussian_filter(rng.standard_normal((H, W)), 14)
    fox = np.clip((fox - 0.02) * 6, 0, 1) * 0.25
    stain = np.exp(-((np.hypot(XX - 820, YY - 210) - 54) / 5) ** 2) * 0.25
    # brass hinge clip on the left with a rod collar, ribbon on the right
    clip = P.polymask((W, H), [[(10, 18), (118, 18), (128, 30), (128, 110), (118, 122), (10, 122), (2, 110), (2, 30)]])
    clip_in = P.polymask((W, H), [[(22, 32), (108, 32), (114, 40), (114, 100), (108, 108), (22, 108), (16, 100), (16, 40)]])
    knuckles = P.polymask((W, H), [], [(30 + k * 22 - 9, 6, 30 + k * 22 + 9, 30) for k in range(4)])
    rivs = P.polymask((W, H), [], [(x - 6, y - 6, x + 6, y + 6) for x in (26, 104) for y in (46, 94)])
    ribbon = P.polymask((W, H), [[(900, 0), (944, 0), (944, 300), (922, 276), (900, 300)]])
    Hf = card * (0.25 + 0.03 * fox)
    edge = np.clip(1 - dist(card) / 14, 0, 1) * card
    Hf -= edge * 0.05
    clipm = np.clip(clip + knuckles, 0, 1)
    Hf = np.maximum(Hf, clipm * (0.55 + 0.3 * P.dome(dist(clipm), 8)))
    Hf -= clip_in * 0.06
    Hf = np.maximum(Hf, rivs * (0.95 + 0.2 * P.dome(dist(rivs), 5)))
    Hf = np.maximum(Hf, ribbon * (0.45 + 0.03 * np.sin(XX / 3.0)))
    albedo = pap[0] * (1 - fox[..., None]) + np.array([0.35, 0.22, 0.1]) * fox[..., None]
    albedo = albedo * (1 - stain[..., None]) + np.array([0.4, 0.25, 0.12]) * stain[..., None]
    albedo = albedo * (1 - edge[..., None] * 0.45)
    # a crimson rule under the title band
    rule = ((np.abs(YY - 96) < 1.3) & (XX > 150) & (XX < 880)).astype(np.float32)
    albedo = mix(albedo, np.array([0.42, 0.03, 0.04]), rule)
    isb = np.clip(clipm + rivs, 0, 1)
    albedo = mix(albedo, brass[0], isb)
    albedo = mix(albedo, np.array([0.28, 0.01, 0.025]), ribbon)
    rough = mix(mix(pap[2], brass[2], isb), 0.4, ribbon)
    metal = mix(np.zeros((H, W), np.float32), 1.0, isb)
    N = P.normals_from(Hf, 20.0, mix(pap[1], brass[1], isb), 0.25)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 5, 2.2))
    alpha = np.clip(card + clipm + rivs + ribbon, 0, 1)
    sh = ndimage.shift(ndimage.gaussian_filter(alpha, 7), (8, 6)) * 0.6
    out_a = np.clip(alpha + sh * (1 - alpha), 0, 1)
    rgb = rgb * alpha[..., None] / np.maximum(out_a[..., None], 1e-3)
    save(rgb, out_a, "LeadCard.png")


def pips():
    S = 96
    c = S / 2
    YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
    R = np.hypot(XX - c, YY - c)
    iron, brass = mats(S, S, 96)
    sock = soft((R <= 40).astype(np.float32))
    rim = soft(((R >= 32) & (R <= 40)).astype(np.float32))
    fang = P.polymask((S, S), [[(c - 16, c - 22), (c + 16, c - 22), (c + 10, c - 4), (c + 1, c + 26), (c - 4, c - 2)]])
    for filled in (False, True):
        Hf = sock * 0.3
        Hf = np.maximum(Hf, rim * (0.55 + 0.3 * P.dome(dist(rim), 4)))
        Hf -= (sock - rim).clip(0, 1) * 0.1
        albedo = mix(iron[0] * 0.7, brass[0], rim)
        rough = mix(iron[2], brass[2], rim)
        metal = mix(np.full((S, S), 0.8, np.float32), 1.0, rim)
        emis = None
        if filled:
            Hf = np.maximum(Hf, fang * (0.3 + 0.35 * P.dome(dist(fang), 6)))
            albedo = mix(albedo, np.array([0.82, 0.76, 0.62]), fang)
            rough = mix(rough, 0.18, fang)
            metal = mix(metal, 0.0, fang)
            tip = np.exp(-(((XX - c) / 4) ** 2 + ((YY - (c + 20)) / 6) ** 2)) * fang
            albedo = mix(albedo, np.array([0.5, 0.02, 0.04]), tip)
        N = P.normals_from(Hf, 18.0, brass[1], 0.15)
        rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 2, 2.0), emissive=emis)
        save(rgb, sock, "PipFang.png" if filled else "PipEmpty.png")


def tower_plate():
    W, H = 600, 200
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    iron, brass = mats(W, H, 220)
    cut = 22
    body = P.polymask((W, H), [[(cut, 4), (W - cut, 4), (W - 4, cut), (W - 4, H - cut), (W - cut, H - 4), (cut, H - 4), (4, H - cut), (4, cut)]])
    inner = P.polymask((W, H), [[(cut + 10, 16), (W - cut - 10, 16), (W - 16, cut + 10), (W - 16, H - cut - 10), (W - cut - 10, H - 16),
                                 (cut + 10, H - 16), (16, H - cut - 10), (16, cut + 10)]])
    bead = np.clip(body - inner, 0, 1)
    Hf = body * 0.3
    Hf = np.maximum(Hf, bead * (0.5 + 0.35 * P.dome(dist(bead), 5)))
    corners = P.polymask((W, H), [], [(x - 7, y - 7, x + 7, y + 7) for x in (30, W - 30) for y in (30, H - 30)])
    Hf = np.maximum(Hf, corners * (0.9 + 0.2 * P.dome(dist(corners), 5)))
    albedo = mix(iron[0] * 0.5, brass[0] * 0.95, np.clip(bead + corners, 0, 1))
    rough = mix(iron[2], brass[2], np.clip(bead + corners, 0, 1))
    metal = mix(np.full((H, W), 0.7, np.float32), 1.0, np.clip(bead + corners, 0, 1))
    N = P.normals_from(Hf, 22.0, mix(iron[1], brass[1], bead), 0.25)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 4, 2.0))
    alpha = np.clip(bead + corners + inner * 0.82, 0, 1)
    save(rgb, alpha, "TowerPlate.png")


def candle():
    W, H = 128, 192
    YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
    c = W / 2
    iron, brass = mats(W, H, 128)
    wax = P.polymask((W, H), [[(c - 16, 92), (c + 16, 96), (c + 16, 160), (c - 16, 160)]], [(c - 16, 86, c - 2, 100)])
    drip = P.polymask((W, H), [[(c + 6, 96), (c + 12, 96), (c + 11, 124), (c + 7, 124)]], [(c + 5, 118, c + 13, 128)])
    dish = P.polymask((W, H), [], [(c - 40, 152, c + 40, 176)])
    flame_d = np.hypot((XX - c) / 9, (YY - 70) / 22)
    flame = np.exp(-flame_d ** 2 * 2.2)
    core = np.exp(-(((XX - c) / 4) ** 2 + ((YY - 80) / 8) ** 2))
    waxm = np.clip(wax + drip, 0, 1)
    Hf = waxm * (0.3 + 0.4 * P.dome(dist(waxm), 9))
    Hf = np.maximum(Hf, dish * (0.4 + 0.3 * P.dome(dist(dish), 6)))
    albedo = mix(brass[0], np.array([0.78, 0.7, 0.56]), waxm)
    rough = mix(brass[2], 0.45, waxm)
    metal = mix(np.ones((H, W), np.float32), 0.0, waxm)
    glow_wax = np.exp(-((YY - 92) / 22) ** 2) * waxm
    emis = glow_wax[..., None] * np.array([0.5, 0.26, 0.08])
    N = P.normals_from(Hf, 18.0, brass[1], 0.2)
    rgb = P.shade(albedo, N, rough, metal, P.ao_from(Hf, 3, 2.0), emissive=emis)
    fl = np.clip(flame[..., None] * np.array([1.0, 0.62, 0.2]) * 1.4 + core[..., None] * np.array([1.0, 0.95, 0.8]), 0, 1)
    fa = np.clip(flame * 1.2, 0, 1)
    halo = np.exp(-(((XX - c) / 40) ** 2 + ((YY - 76) / 44) ** 2)) * 0.35
    base_a = np.clip(waxm + dish, 0, 1)
    rgb = mix(rgb, fl, fa * (1 - base_a))
    a = np.clip(base_a + fa + halo * (1 - base_a), 0, 1)
    rgb = mix(rgb, np.array([1.0, 0.62, 0.25]), halo * (1 - base_a) * (1 - fa))
    save(rgb, a, "Candle.png")


def preview():
    names = ["Dial", "DialHand", "BellHollow", "BellTarnished", "BellLit", "BellRail", "NoteFace", "NoteOutfit", "NoteForm",
             "NoteClique", "NoteWeapon", "NoteCompanion", "SealWarning", "SealDetention", "SealProbation", "SealSuspension",
             "Slip", "LeadCard", "PipEmpty", "PipFang", "TowerPlate", "Candle"]
    W = 1800
    sheet = Image.new("RGBA", (W, 1200), (16, 14, 20, 255))
    x = y = 10
    rh = 0
    for n in names:
        im = Image.open(OUT / f"{n}.png")
        im.thumbnail((420, 300))
        if x + im.width > W:
            x = 10
            y += rh + 12
            rh = 0
        sheet.alpha_composite(im, (x, y))
        x += im.width + 12
        rh = max(rh, im.height)
    sheet = sheet.crop((0, 0, W, y + rh + 10))
    sheet.save(OUT / "_sheet.png")


R1_PIECES = ["Dial", "DialHand", "TowerPlate", "Seal", "SealBroken", "Slip", "LeadCard", "PipEmpty", "PipFang"]


def export_r1():
    dest = HERE.parents[1] / "group-upload-belltower"
    dest.mkdir(parents=True, exist_ok=True)
    for n in R1_PIECES:
        Image.open(OUT / f"{n}.png").save(dest / f"Bt{n}.png", optimize=True)
    print("exported", len(R1_PIECES), "to", dest)


if __name__ == "__main__":
    dial()
    for k in ("Hollow", "Tarnished", "Lit"):
        bell(k)
    bell_glow()
    rail()
    for n in ("Face", "Outfit", "Form", "Clique", "Weapon", "Companion"):
        note(n)
    rgb, a = seal()
    brgb, ba = seal(broken=True)
    seal_tints(rgb, a, brgb, ba)
    slip()
    lead_card()
    pips()
    tower_plate()
    candle()
    preview()
    export_r1()
    print("ok", OUT)
