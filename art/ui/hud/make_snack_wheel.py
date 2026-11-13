"""PBR art for the snack wheel (Nightmare Highschool, inventory QOL 1.94), baked to images.

Owner (2026-11-12): "I want the wheel to have a completely original look, cool, on theme, and animated, with cool
markers for each item", then "Make the item box areas bigger" and "make it cooler and higher quality".

The Bell Wheel: a blackened, hammered iron ring with forged cusps and twelve gilt moon phases, a brass band engraved with
a rose vine, a turning band of inlaid runes, a stained-glass rose window lit from behind, a brass hub lettered
NIGHTMARE HIGH REFECTORY with a polished silver cloche (Best food), a blued-steel clock hand with gilt filigree, and a
brass rose socket for every snack. Separate glow layers let the game breathe light into it.

Same pipeline as the health bar, the posture rail and the kit (make_health_pbr.shade via make_kit_ui.lit), baked with
2x supersampling (geometry in 1024 "units", evaluated on a 2048 grid), with edge wear (polished ridges) and grime
(dark recesses) worked out from the height.

Pieces (art/ui/hud/out/wheel/, staged to art/group-upload/snack-wheel/):
  WheelRim.png        1024  the ring (the middle is clear)
  WheelRimGlow.png    1024  the moons and the vine's inlay as light only (pulses in game)
  WheelBand.png       1024  the rune band (turns slowly)
  WheelBandGlow.png   1024  the runes' inlay as light only (pulses in game)
  WheelDisc.png       1024  the rose window, a little see-through
  WheelRays.png       1024  light shafts through the window (white, alpha; tinted and turned in game)
  WheelHalo.png       1024  a candle aura round the outside (white, alpha; flickers in game; shown 1.3x the rim)
  WheelHub.png         512  the hub with the cloche (Best food)
  WheelHand.png       1024  the clock hand, pointing up from the middle
  WheelMarker.png      384  a snack's socket: a brass rose with a finial pointing out (up) and a big dark well
  WheelMarkerLit.png   384  the same, picked: gilt, an ember glow round the well
  WheelMarkerRim.png   384  greyscale: a thin ring inside the well (tinted with the rarity colour)
  WheelShade.png       384  the well's disc in black (the cooldown, cropped from the top as it drains)
  WheelSigil.png       512  a gilt ring of runes that spins behind the picked socket (white, alpha)
  WheelGlow.png        256  a soft glow (white, alpha; tinted)
  WheelEmber.png        64  an ember (white core, alpha; tinted) for the sparks that drift off the wheel
  preview_wheel.png         the pieces assembled (for review)

  python make_snack_wheel.py [rim band disc hub hand markers]
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as H
import make_kit_ui as K

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "wheel"
OUT.mkdir(parents=True, exist_ok=True)
f32 = np.float32
SS = 2  # supersampling

IRON = np.array([0.10, 0.095, 0.10], f32)
OXBLOOD = np.array([0.30, 0.04, 0.07], f32)
SILVER = np.array([0.82, 0.82, 0.84], f32)
BLUED = np.array([0.09, 0.12, 0.24], f32)
FONT = "C:/Windows/Fonts/georgiab.ttf"


# ================================================================ helpers (geometry in units, U units per canvas)
class Canvas:
    def __init__(self, U):
        self.U, self.N = U, U * SS
        yy, xx = K.grid(self.N, self.N)
        self.x, self.y = xx / SS, yy / SS
        self.c = U / 2
        self.r = np.hypot(self.x - self.c, self.y - self.c)
        self.th = np.arctan2(self.y - self.c, self.x - self.c)

    def mask(self, fn):
        return K.mask((self.N, self.N), lambda dr, s: fn(dr, s * SS))

    def inner(self, m):
        return K.inner(m) / SS

    def noise(self, sigma, seed):
        return K.noise((self.N, self.N), sigma * SS, seed)

    def maps(self, name, period, tint=(1, 1, 1)):
        col = K.tile_map(name, "color", (self.N, self.N), period * SS) * np.array(tint, f32)
        rough = K.tile_map(name, "rough", (self.N, self.N), period * SS)[..., 0]
        nrm = K.tile_map(name, "normal", (self.N, self.N), period * SS) * 2 - 1
        return col, rough, nrm

    def zeros(self, ch=None):
        return np.zeros((self.N, self.N) if ch is None else (self.N, self.N, ch), f32)


def angdist(th, a):
    return np.abs((th - a + math.pi) % (2 * math.pi) - math.pi)


def finish(cv, h, alb, rough, metal, detail=None, detail_k=0.25, emissive=None, strength=1 / 7.5, wear=1.0):
    """edge wear (polished, brighter ridges on metal) and grime (dark recesses), then the house shader"""
    hs = ndimage.gaussian_filter(h, 1.6 * SS)
    lap = ndimage.laplace(hs)
    lap = lap / (np.percentile(np.abs(lap), 99.5) + 1e-8)
    convex = np.clip(-lap, 0, 1) * wear
    concave = np.clip(lap, 0, 1)
    shiny = (metal > 0.5).astype(f32)
    alb = alb * (1 - 0.5 * concave[..., None]) + (convex * shiny)[..., None] * np.array([0.30, 0.26, 0.20], f32)
    rough = np.clip(rough - convex * shiny * 0.12 + concave * 0.18, 0.04, 1)
    return K.lit(h, alb.astype(f32), rough.astype(f32), metal.astype(f32), strength=strength, detail=detail,
                 detail_k=detail_k, emissive=emissive, ao_k=(10 * SS, 5 * SS))


def save(rgb, alpha, name, size):
    a = np.clip(alpha, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8), "RGBA")
    img = img.resize(size, Image.LANCZOS)
    img.save(OUT / name, optimize=True)
    print("  ", name, img.size)
    return img


def light_only(alpha, name, size):
    return save(np.ones(alpha.shape + (3,), f32), alpha, name, size)


def ring_text(cv, text, radius, size, start_deg=-90):
    """letters stood round a circle, tops outward; returns a mask"""
    im = Image.new("L", (cv.N, cv.N), 0)
    font = ImageFont.truetype(FONT, int(size * SS))
    n = len(text)
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        a = math.radians(start_deg + (i + 0.5) * 360 / n)
        g = Image.new("L", (int(size * 2 * SS), int(size * 2 * SS)), 0)
        ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=font, fill=255, anchor="mm")
        g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        px = (cv.c + radius * math.cos(a)) * SS - g.width / 2
        py = (cv.c + radius * math.sin(a)) * SS - g.height / 2
        im.paste(255, (int(px), int(py)), g)
    return np.array(im, f32) / 255


# ================================================================ the ring
def rim():
    cv = Canvas(1024)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c
    RI, RB, RO = 384, 432, 476  # inner edge, brass/iron seam, iron outer edge
    cusp = cv.zeros()
    for k in range(24):
        a = k * 2 * math.pi / 24
        da = angdist(th, a) * r
        t = np.clip((r - RO + 4) / 34, 0, 1)
        half = 22 * np.sqrt(np.clip(1 - t, 0, 1))
        cusp = np.maximum(cusp, ((da < half) & (r >= RO - 4) & (r < RO + 30)).astype(f32))
    body = ((r >= RI) & (r < RO)).astype(f32)
    # a gilt bead on every other cusp's point
    beads, db = cv.zeros(), cv.zeros()
    for k in range(0, 24, 2):
        a = k * 2 * math.pi / 24
        bx, by = c + (RO + 26) * math.cos(a), c + (RO + 26) * math.sin(a)
        d = np.hypot(x - bx, y - by)
        beads = np.maximum(beads, (d < 7).astype(f32))
        db = np.maximum(db, np.clip(7 - d, 0, None))
    shape = ndimage.gaussian_filter(np.clip(body + cusp + beads, 0, 1), 0.7 * SS)
    d_iron = np.clip(np.minimum(r - RB, RO - r), 0, None)
    d_brass = np.clip(np.minimum(r - RI, RB - r), 0, None)
    h = np.where(r >= RB, 0.30 + 0.10 * H.dome(d_iron, 18), 0.34 + 0.12 * H.dome(d_brass, 22))
    h += np.exp(-((r - (RI + 8)) / 2.6) ** 2) * 0.05
    h += np.exp(-((r - (RB - 8)) / 2.6) ** 2) * 0.05
    h -= np.exp(-((r - RB) / 1.8) ** 2) * 0.09
    h += (r >= RB) * 0.012 * cv.noise(2.5, 21)  # hammered iron
    dc = cv.inner(cusp)
    h = np.where(cusp > 0.5, np.maximum(h, 0.26 + 0.17 * H.dome(dc, 9)), h)
    h = np.where(beads > 0.5, np.maximum(h, 0.40 + 0.08 * H.dome(db, 7)), h)
    # the brass band's rose vine: a wavy stem with leaves at the crests, engraved
    rv = (RI + RB) / 2 + 7 * np.sin(th * 24)
    stem = np.abs(r - rv) < 1.6
    leaf = cv.zeros()
    for k in range(48):
        a = k * 2 * math.pi / 48 + math.pi / 48
        sgn = 1 if k % 2 == 0 else -1
        lr = (RI + RB) / 2 + sgn * 9
        lx, ly = c + lr * math.cos(a), c + lr * math.sin(a)
        u = (x - lx) * -math.sin(a) + (y - ly) * math.cos(a)
        v = (x - lx) * math.cos(a) + (y - ly) * math.sin(a)
        leaf = np.maximum(leaf, ((u / 7) ** 2 + (v / 3) ** 2 < 1).astype(f32))
    mid = (r > RI + 13) & (r < RB - 13)
    vine = (stem | (leaf > 0.5)) & mid
    h -= vine * 0.035
    deg = (np.degrees(th) + 450) % 360
    kd = np.abs(((deg + 15) % 30) - 15) * (math.pi / 180) * r
    h -= ((kd < 1.8) & (r > RI + 11) & (r < RI + 15)) * 0.03
    ic, irough, inrm = cv.maps("Iron", 320)
    bc, brough, bnrm = cv.maps("Brass", 300, (0.96, 0.86, 0.72))
    iron = (r >= RB) | (cusp > 0.5)
    alb = np.where(iron[..., None], ic * 0.18 + IRON * 0.85, bc * 0.8 + K.BRASS_OLD * 0.35)
    alb[vine] = alb[vine] * 0.35 + K.GILT * 0.45
    alb[beads > 0.5] = K.GILT
    rough = np.where(iron, np.clip(irough * 0.5 + 0.32, 0.2, 0.85), np.clip(brough * 0.55 + 0.12, 0.1, 0.7)).astype(f32)
    rough[vine] = 0.2
    metal = np.where(iron, 0.8, 0.95).astype(f32)
    metal[beads > 0.5] = 1.0
    detail = np.where(iron[..., None], inrm, bnrm)
    glow = cv.zeros()
    RM = (RB + RO) / 2
    for k in range(12):
        a = -math.pi / 2 + k * 2 * math.pi / 12
        mx, my = c + RM * math.cos(a), c + RM * math.sin(a)
        dm = np.hypot(x - mx, y - my)
        disc = dm < 12
        lit_frac = 1 - abs(k - 6) / 6
        off = (1 - lit_frac) * 24
        ux, uy = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        dark = np.hypot(x - (mx + ux * off), y - (my + uy * off)) < 12
        moon = disc & ~dark if k != 0 else np.zeros_like(disc)
        h -= disc * 0.05
        h += moon * (0.04 * H.dome(np.clip(12 - dm, 0, None), 6))
        h -= (np.abs(dm - 15) < 1.0) * 0.03
        alb[moon] = K.GILT * 0.95
        alb[disc & ~moon] *= 0.45
        rough[moon] = 0.14
        metal[moon] = 1.0
        glow = np.maximum(glow, moon.astype(f32))
        ra = a + math.pi / 12
        rx, ry = c + RM * math.cos(ra), c + RM * math.sin(ra)
        dr = np.hypot(x - rx, y - ry)
        riv = dr < 6.5
        h = np.where(riv, np.maximum(h, 0.42 + 0.08 * H.dome(np.clip(6.5 - dr, 0, None), 6.5)), h)
        alb[riv] = K.BRASS_OLD * 1.2
        rough[riv] = 0.22
        metal[riv] = 1.0
    rgb = finish(cv, h, alb, rough, metal, detail=detail, detail_k=0.3)
    save(rgb, shape, "WheelRim.png", (1024, 1024))
    g = ndimage.gaussian_filter(np.maximum(glow, vine.astype(f32) * 0.6), 3 * SS) * 1.6
    light_only(np.clip(g, 0, 1), "WheelRimGlow.png", (1024, 1024))


# ================================================================ the rune band
def band():
    cv = Canvas(1024)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c
    R0, R1 = 348, 380
    ring = ((r >= R0) & (r < R1)).astype(f32)
    d = np.clip(np.minimum(r - R0, R1 - r), 0, None)
    h = 0.28 + 0.07 * H.dome(d, 9)
    h += np.exp(-((r - (R0 + 4)) / 1.6) ** 2) * 0.025 + np.exp(-((r - (R1 - 4)) / 1.6) ** 2) * 0.025
    rm = (R0 + R1) / 2
    glyph = np.zeros(r.shape, bool)
    n = 40
    for k in range(n):
        a = k * 2 * math.pi / n
        gx, gy = c + rm * math.cos(a), c + rm * math.sin(a)
        dg = np.hypot(x - gx, y - gy)
        tx, ty = -math.sin(a), math.cos(a)
        along = (x - gx) * tx + (y - gy) * ty
        across = (x - gx) * math.cos(a) + (y - gy) * math.sin(a)
        kind = k % 5
        if kind == 0:  # a crescent
            ox, oy = gx + 4 * math.cos(a), gy + 4 * math.sin(a)
            glyph |= (dg < 8) & (np.hypot(x - ox, y - oy) >= 7)
        elif kind == 1:  # a dot in a ring
            glyph |= (dg < 2.6) | (np.abs(dg - 6.5) < 1.1)
        elif kind == 2:  # an eight-point star
            glyph |= ((np.abs(along) < 7) & (np.abs(across) < 1.3)) | ((np.abs(across) < 7) & (np.abs(along) < 1.3))
            glyph |= ((np.abs(along - across) < 1.3) | (np.abs(along + across) < 1.3)) & (dg < 5)
        elif kind == 3:  # a rune: a stave with two branches
            glyph |= (np.abs(along) < 1.3) & (np.abs(across) < 9)
            glyph |= (np.abs(across - along - 2) < 1.3) & (along > 0) & (along < 6)
            glyph |= (np.abs(across + along + 2) < 1.3) & (along < 0) & (along > -6)
        else:  # a bar
            glyph |= (np.abs(across) < 8) & (np.abs(along) < 1.6)
    glyph &= ring > 0.5
    h -= glyph * 0.05
    bc, brough, bnrm = cv.maps("Brass", 260, (0.96, 0.86, 0.72))
    alb = bc * 0.78 + K.BRASS_OLD * 0.35
    alb[glyph] = alb[glyph] * 0.3 + K.GILT * 0.35
    rough = np.clip(brough * 0.6 + 0.12, 0.1, 0.7)
    metal = np.full(r.shape, 0.95, f32)
    rgb = finish(cv, h, alb, rough, metal, detail=bnrm, detail_k=0.25)
    save(rgb, ndimage.gaussian_filter(ring, 0.6 * SS), "WheelBand.png", (1024, 1024))
    g = ndimage.gaussian_filter(glyph.astype(f32), 2.2 * SS) * 2.2
    light_only(np.clip(g, 0, 1), "WheelBandGlow.png", (1024, 1024))


# ================================================================ the rose window, its rays and the halo
def disc():
    cv = Canvas(1024)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c
    RD = 388
    inside = r < RD

    def line(m, w):
        return np.clip(w - m, 0, 1)

    lead = cv.zeros()
    for rr, w in ((346, 4.5), (210, 4.0), (104, 3.5)):
        lead = np.maximum(lead, line(np.abs(r - rr), w))
    n = 12
    pane = np.zeros(r.shape, np.int32)
    for k in range(n):
        a = k * 2 * math.pi / n
        perp = np.abs((x - c) * -math.sin(a) + (y - c) * math.cos(a))
        along = (x - c) * math.cos(a) + (y - c) * math.sin(a)
        lead = np.maximum(lead, line(perp, 3.4) * ((along > 104) & (along < 346)))
        a2 = a + math.pi / n
        u = (x - c) * math.cos(a2) + (y - c) * math.sin(a2)
        v = (x - c) * -math.sin(a2) + (y - c) * math.cos(a2)
        t = np.clip((u - 228) / 104, 0, 1)
        half = 31 * np.sqrt(np.clip(1 - t ** 2.2, 0, 1))
        lan = (u > 228) & (u < 332) & (np.abs(v) < half)
        inner_l = (u > 234) & (u < 326) & (np.abs(v) < half - 4)
        lead = np.maximum(lead, (lan & ~inner_l).astype(f32))
        pane[lan] = 3
        lead = np.maximum(lead, ((np.abs(v) < 1.6) & (u > 234) & (u < 300)).astype(f32))  # a mullion
        ox, oy = c + 160 * math.cos(a2), c + 160 * math.sin(a2)
        dd = np.hypot(x - ox, y - oy)
        lead = np.maximum(lead, line(np.abs(dd - 18), 2.4))
        pane[dd < 16] = 2
    lead *= inside
    sector = ((th + math.pi) / (2 * math.pi) * n * 2).astype(np.int32) % (2 * n)
    jitter = np.random.default_rng(7).uniform(0.75, 1.25, 2 * n).astype(f32)[sector]
    streak = cv.noise(28, 12)
    wave = cv.noise(9, 13)
    seeds = (cv.noise(0.8, 14) > 0.9).astype(f32)  # little bubbles in the glass
    deep = np.array([0.22, 0.03, 0.06], f32)
    wine = np.array([0.38, 0.06, 0.09], f32)
    amber = np.array([0.40, 0.19, 0.05], f32)
    violet = np.array([0.15, 0.06, 0.20], f32)
    alb = np.where((sector % 2 == 0)[..., None], deep, wine) * jitter[..., None]
    alb = np.where((pane == 2)[..., None], amber, alb)
    alb = np.where((pane == 3)[..., None], violet * 1.3, alb)
    alb = np.where((r < 104)[..., None], deep * 0.8, alb)
    alb = alb * (0.7 + 0.45 * streak[..., None] + 0.2 * wave[..., None]) * (1.1 - 0.45 * (r / RD)[..., None])
    alb = alb + seeds[..., None] * 0.08
    dl = cv.inner(lead > 0.5)
    alb = alb * (1 - lead[..., None]) + IRON * 0.9 * lead[..., None]
    h = 0.20 + 0.015 * wave + lead * (0.05 + 0.06 * H.dome(dl, 2.5))
    rough = np.where(lead > 0.3, 0.5, 0.06).astype(f32)
    metal = np.where(lead > 0.3, 0.6, 0.0).astype(f32)
    rgb = finish(cv, h, alb, rough, metal, strength=1 / 6, wear=0.6)
    glow = np.exp(-(r / 230) ** 2)[..., None] * np.array([0.32, 0.12, 0.04], f32)
    rgb = rgb + glow * (1 - lead[..., None])
    alpha = inside * (0.80 + 0.18 * lead)
    save(rgb, ndimage.gaussian_filter(alpha.astype(f32), 0.8 * SS), "WheelDisc.png", (1024, 1024))

    # light shafts: soft rays from the middle (turned slowly over the window in game)
    rays = cv.zeros()
    for k in range(12):
        a = k * 2 * math.pi / 12 + math.pi / 12
        w = 0.07 + 0.03 * (k % 3)
        rays = np.maximum(rays, np.exp(-(angdist(th, a) / w) ** 2))
    rays *= np.clip((r - 60) / 80, 0, 1) * np.clip((RD - r) / 120, 0, 1)
    light_only(np.clip(rays * 0.55, 0, 1), "WheelRays.png", (1024, 1024))

    # the halo: a candle aura with flame tongues round the outside (shown 1.3x the rim)
    rr = r * 1.3  # in rim units
    tongues = 0.6 + 0.4 * np.sin(th * 18 + 3 * cv.noise(20, 15)) * cv.noise(12, 16)
    aura = np.exp(-((rr - 470) / 36) ** 2) * tongues + np.exp(-((rr - 470) / 90) ** 2) * 0.35
    aura *= np.clip((rr - 380) / 40, 0, 1)
    light_only(np.clip(aura, 0, 1), "WheelHalo.png", (1024, 1024))


# ================================================================ the hub (Best food)
def hub():
    cv = Canvas(1024)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c
    R1, RT, R0 = 486, 412, 380  # outer rim, the lettered band's inner edge, recessed face
    body = (r < R1).astype(f32)
    h = 0.30 + 0.10 * H.dome(np.clip(R1 - r, 0, None), 26)
    knurl = (r > 470) & (r < R1)
    h += knurl * 0.025 * np.cos(th * 160)
    letters = ring_text(cv, "\u2022 NIGHTMARE HIGH \u2022 REFECTORY \u2022 BEST FOOD ", 442, 30)
    h -= letters * (r > RT) * 0.045
    h -= np.exp(-((r - RT) / 2) ** 2) * 0.05
    face = r < R0
    h -= face * 0.12
    bc, brough, bnrm = cv.maps("Brass", 300, (0.96, 0.86, 0.72))
    alb = bc * 0.8 + K.BRASS_OLD * 0.35
    alb[letters > 0.5] = alb[letters > 0.5] * 0.35
    alb[face] = alb[face] * 0.3 + K.INK * 0.6
    rough = np.where(face, 0.3, np.clip(brough * 0.6 + 0.1, 0.1, 0.7)).astype(f32)
    metal = np.where(face, 0.1, 0.95).astype(f32)
    for k in range(4):  # four gilt studs on the face's edge
        a = -math.pi / 4 + k * math.pi / 2
        sx, sy = c + 396 * math.cos(a), c + 396 * math.sin(a)
        ds = np.hypot(x - sx, y - sy)
        h = np.where(ds < 9, np.maximum(h, 0.42 + 0.08 * H.dome(np.clip(9 - ds, 0, None), 9)), h)
        alb[ds < 9] = K.GILT

    def cloche(dr, s):
        cx, base = c, c + 120
        dr.pieslice([(cx - 220) * s, (base - 220) * s, (cx + 220) * s, (base + 220) * s], 180, 360, fill=255)
        dr.ellipse([(cx - 30) * s, (base - 276) * s, (cx + 30) * s, (base - 214) * s], fill=255)
        dr.rounded_rectangle([(cx - 280) * s, (base - 4) * s, (cx + 280) * s, (base + 32) * s], radius=14 * s, fill=255)

    m = cv.mask(cloche)
    di = cv.inner(m)
    hc = 0.22 + 0.24 * H.dome(di, 70)
    roll = (np.abs(y - (c + 110)) < 9) & (m > 0.5)
    hc += roll * 0.03
    h = np.where(m > 0.5, h + hc * m, h)
    knob = (np.hypot(x - c, y - (c - 125)) < 30) & (m > 0.5)
    alb[m > 0.5] = SILVER
    alb[knob] = K.GILT
    rough[m > 0.5] = 0.08
    metal[m > 0.5] = 1.0
    cx2, cy2 = c - 80, c - 20
    cres = (np.hypot(x - cx2, y - cy2) < 30) & (np.hypot(x - cx2 - 12, y - cy2 + 4) >= 26) & (m > 0.5)
    h -= cres * 0.04
    rgb = finish(cv, h, alb, rough, metal, detail=bnrm, detail_k=0.2)
    save(rgb, ndimage.gaussian_filter(body, 0.7 * SS), "WheelHub.png", (512, 512))


# ================================================================ the clock hand
def hand():
    cv = Canvas(1024)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c

    def shaft(dr, s):
        dr.polygon([((c - 22) * s, (c - 60) * s), ((c + 22) * s, (c - 60) * s), ((c + 9) * s, (c - 300) * s), ((c - 9) * s, (c - 300) * s)], fill=255)
        dr.polygon([((c - 9) * s, (c - 330) * s), ((c + 9) * s, (c - 330) * s), ((c + 5) * s, (c - 392) * s), ((c - 5) * s, (c - 392) * s)], fill=255)
        dr.ellipse([(c - 34) * s, (c + 54) * s, (c + 34) * s, (c + 122) * s], fill=255)
        dr.polygon([((c - 11) * s, (c + 70) * s), ((c + 11) * s, (c + 70) * s), ((c + 11) * s, (c - 60) * s), ((c - 11) * s, (c - 60) * s)], fill=255)

    m = cv.mask(shaft)
    lx, ly = c, c - 315
    loop = np.abs(np.hypot(x - lx, y - ly) - 26) < 7
    for dx in (-24, 24):
        loop |= np.abs(np.hypot(x - lx - dx, y - ly + 6) - 15) < 6
    # filigree scrolls either side of the shaft near the collar
    scroll = np.zeros(r.shape, bool)
    for sgn in (-1, 1):
        sx, sy = c + sgn * 36, c - 110
        dsc = np.hypot(x - sx, y - sy)
        ang = np.arctan2(y - sy, x - sx)
        spiral = 22 - 3.2 * ((ang * sgn + math.pi) % (2 * math.pi))
        scroll |= (np.abs(dsc - spiral) < 3.2) & (dsc < 24)
    tx, ty = c, c - 432
    cres = (np.hypot(x - tx, y - ty) < 56) & (np.hypot(x - tx, y - ty - 26) >= 48)
    collar = np.hypot(x - c, y - c) < 40
    bead = np.hypot(x - c, y - (c - 200)) < 22
    m = np.clip(m + loop + scroll + cres + collar + bead, 0, 1)
    di = cv.inner(m)
    h = 0.24 + 0.14 * H.dome(di, 12)
    h += collar * (0.18 * H.dome(np.clip(40 - np.hypot(x - c, y - c), 0, None), 40))
    h += bead * (0.2 * H.dome(np.clip(22 - np.hypot(x - c, y - (c - 200)), 0, None), 22))
    h += (m > 0.5) * 0.04 * np.clip(1 - np.abs(x - c) / 14, 0, 1) * (y < c - 40)
    gilt = cres | loop | scroll
    edge = (di < 2.2) & (m > 0.5) & ~gilt & ~collar & ~bead
    alb = np.zeros(r.shape + (3,), f32) + BLUED
    alb[edge] = K.GILT * 0.8
    alb[gilt] = K.GILT
    alb[collar] = K.BRASS_OLD * 1.2
    alb[bead] = K.CRIMSON * 1.8
    rough = np.where(bead, 0.06, np.where(gilt | collar | edge, 0.15, 0.18)).astype(f32)
    metal = np.where(bead, 0.0, 1.0).astype(f32)
    rgb = finish(cv, h, alb, rough, metal, strength=1 / 6)
    sh = ndimage.gaussian_filter(np.roll(np.roll(m, 12 * SS, 0), 8 * SS, 1), 8 * SS) * 0.5
    a = np.clip(m + sh * (1 - m), 0, 1)
    rgb = rgb * m[..., None] / np.maximum(a[..., None], 1e-4)
    save(rgb, a, "WheelHand.png", (1024, 1024))


# ================================================================ the sockets, the sigil, glow and embers
def markers():
    cv = Canvas(512)
    x, y, r, th, c = cv.x, cv.y, cv.r, cv.th, cv.c
    RW, RF = 172, 204  # the well (big: the snack sits in it), the frame's outer radius
    cusp, gems, dg = cv.zeros(), cv.zeros(), cv.zeros()
    for k in range(8):
        a = -math.pi / 2 + k * 2 * math.pi / 8
        ox, oy = c + (RF - 6) * math.cos(a), c + (RF - 6) * math.sin(a)
        cusp = np.maximum(cusp, (np.hypot(x - ox, y - oy) < 24).astype(f32))
        if k != 0:  # a garnet at each cusp but the finial's
            gx, gy = c + (RF + 2) * math.cos(a), c + (RF + 2) * math.sin(a)
            d = np.hypot(x - gx, y - gy)
            gems = np.maximum(gems, (d < 7).astype(f32))
            dg = np.maximum(dg, np.clip(7 - d, 0, None))
    body = np.clip((r < RF).astype(f32) + cusp, 0, 1)

    def spike(dr, s):
        dr.polygon([((c - 26) * s, (c - RF - 4) * s), ((c + 26) * s, (c - RF - 4) * s), (c * s, (c - RF - 46) * s)], fill=255)
        dr.ellipse([(c - 12) * s, (c - RF - 50) * s, (c + 12) * s, (c - RF - 26) * s], fill=255)

    outer = np.clip(body + cv.mask(spike), 0, 1)
    well = (r < RW).astype(f32)
    df = cv.inner(outer)
    h = 0.30 + 0.14 * H.dome(df, 16)
    h += np.exp(-((r - (RW + 9)) / 2.6) ** 2) * 0.05      # the bead round the well
    h -= np.exp(-((r - (RW + 1)) / 1.5) ** 2) * 0.05      # a step down into it
    face = (r > RW + 15) & (r < RF - 6)
    h += face * 0.014 * (np.cos(th * 64) > 0.25)          # beading
    h -= face * (np.abs(np.sin(th * 16)) < 0.12) * 0.02   # engraved spokes
    h = np.where(gems > 0.5, np.maximum(h, 0.40 + 0.1 * H.dome(dg, 7)), h)
    h = np.where(well > 0.5, 0.15 + 0.01 * cv.noise(2, 5), h)
    bc, brough, bnrm = cv.maps("Brass", 220, (0.96, 0.86, 0.72))
    velvet = (K.INK * 0.7 + OXBLOOD * 0.3) * (1.0 + 0.6 * np.exp(-(r / 120) ** 2))[..., None]

    def bake(name, gilt):
        base = K.GILT if gilt else K.BRASS_OLD
        alb = bc * 0.8 + base * 0.38
        alb = np.where(well[..., None] > 0.5, velvet, alb)
        alb[gems > 0.5] = K.CRIMSON * 1.6
        rough = np.where(well > 0.5, 0.6, np.clip(brough * 0.5 + (0.05 if gilt else 0.13), 0.05, 0.6)).astype(f32)
        rough[gems > 0.5] = 0.06
        metal = np.where((well > 0.5) | (gems > 0.5), 0.0, 1.0).astype(f32)
        emis = None
        if gilt:
            e = np.exp(-((r - RW) / 7) ** 2) * (r > RW - 2) + 0.35 * np.exp(-(df / 10) ** 2) * (outer > 0.5)
            e = e + gems * 0.8
            emis = e[..., None] * np.array([1.3, 0.6, 0.16], f32)
        rgb = finish(cv, h, alb, rough, metal, detail=bnrm, detail_k=0.25, emissive=emis)
        save(rgb, ndimage.gaussian_filter(np.clip(outer + gems, 0, 1), 0.6 * SS), name, (384, 384))

    bake("WheelMarker.png", False)
    bake("WheelMarkerLit.png", True)
    light_only(np.exp(-((r - (RW - 6)) / 2.6) ** 2) * (r < RW), "WheelMarkerRim.png", (384, 384))
    save(np.zeros(r.shape + (3,), f32), well, "WheelShade.png", (384, 384))

    # the sigil: a gilt ring of runes and ticks that spins behind the picked socket
    sv = Canvas(512)
    sr, sth = sv.r, sv.th
    sig = np.exp(-((sr - 236) / 1.8) ** 2) + np.exp(-((sr - 214) / 1.2) ** 2) * 0.8
    deg = (np.degrees(sth) + 450) % 360
    kd = np.abs(((deg + 5) % 10) - 5) * (math.pi / 180) * sr
    sig = sig + ((kd < 1.4) & (sr > 216) & (sr < 234)).astype(f32) * 0.9
    for k in range(8):
        a = k * 2 * math.pi / 8
        px, py = sv.c + 225 * math.cos(a), sv.c + 225 * math.sin(a)
        d = np.hypot(sv.x - px, sv.y - py)
        sig = sig + (np.abs(d - 9) < 1.5).astype(f32) + (d < 3).astype(f32)
    light_only(np.clip(sig, 0, 1), "WheelSigil.png", (512, 512))

    gv = Canvas(256)
    light_only(np.exp(-(gv.r / 75) ** 2), "WheelGlow.png", (256, 256))
    ev = Canvas(64)
    light_only(np.clip(np.exp(-(ev.r / 6) ** 2) * 1.2 + np.exp(-(ev.r / 16) ** 2) * 0.45, 0, 1), "WheelEmber.png", (64, 64))


# ================================================================ preview
def preview(snacks=None, backdrop=(34, 30, 36, 255), name="preview_wheel.png"):
    """the wheel as the HUD shows it; snacks: a list of RGBA images to sit in the sockets"""
    W = 1000
    bg = Image.new("RGBA", (W, W), backdrop)

    def put(im, size, pos=(W // 2, W // 2), rot=0, tint=None, alpha=1.0):
        if isinstance(im, str):
            im = Image.open(OUT / im).convert("RGBA")
        im = im.resize((size, size), Image.LANCZOS)
        px = np.array(im, f32)
        if tint:
            px[..., :3] *= np.array(tint, f32) / 255
        px[..., 3] *= alpha
        im = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8), "RGBA")
        if rot:
            im = im.rotate(-rot, resample=Image.BICUBIC)
        bg.alpha_composite(im, (pos[0] - size // 2, pos[1] - size // 2))

    D = 760
    put("WheelHalo.png", int(D * 1.3), tint=(255, 150, 70), alpha=0.6)
    put("WheelDisc.png", D)
    put("WheelRays.png", D, rot=8, tint=(255, 190, 120), alpha=0.5)
    put("WheelBand.png", D, rot=12)
    put("WheelBandGlow.png", D, rot=12, tint=(255, 170, 80), alpha=0.6)
    put("WheelRim.png", D)
    put("WheelRimGlow.png", D, tint=(255, 190, 110), alpha=0.5)
    R = int(D * 0.335)
    n = 6
    pick = 1
    for k in range(n):
        a = -90 + k * 360 / n
        px_ = int(W / 2 + R * math.cos(math.radians(a)))
        py_ = int(W / 2 + R * math.sin(math.radians(a)))
        size = 190 if k == pick else 168
        if k == pick:
            put("WheelGlow.png", 300, (px_, py_), tint=(255, 160, 70), alpha=0.9)
            put("WheelSigil.png", 250, (px_, py_), rot=20, tint=(240, 200, 120), alpha=0.9)
        put("WheelMarkerLit.png" if k == pick else "WheelMarker.png", size, (px_, py_), rot=a + 90)
        put("WheelMarkerRim.png", size, (px_, py_), tint=(120, 190, 230) if k % 3 == 0 else (210, 200, 180))
        if snacks and k < len(snacks):
            put(snacks[k], int(size * 0.66), (px_, py_))
    put("WheelHand.png", 400, rot=-90 + pick * 360 / n + 90)  # the tip stops at the socket's edge
    put("WheelGlow.png", 260, tint=(255, 200, 120), alpha=0.35)
    put("WheelHub.png", 210)
    rng = np.random.default_rng(3)
    for _ in range(14):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(D * 0.5, D * 0.62)
        put("WheelEmber.png", int(rng.uniform(14, 26)), (int(W / 2 + rr * math.cos(a)), int(W / 2 + rr * math.sin(a))),
            tint=(255, 150, 60), alpha=rng.uniform(0.5, 1))
    bg.save(OUT / name)
    print("  ", name)
    return bg


if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    for fn in (rim, band, disc, hub, hand, markers):
        if not only or fn.__name__ in only:
            fn()
    preview()
