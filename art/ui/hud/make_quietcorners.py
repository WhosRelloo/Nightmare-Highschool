"""Quiet Corners: concept art for the whole-screen UI layout (Nightmare Highschool).

Design: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md.
Baked with the same PBR shader as Thornrose and the Bell Tower (make_health_pbr.py): height field -> normals plus the
school's seamless detail maps (art/props/source), GGX + Lambert, warm key, cool fill, candle rim, AO.

Every frame is blackened iron. The trim (bezels, beads, pins, rivets, gems) and the paper change with the player's
Lineage race ("Bloodline trims"); each race is its own bake, not a tint, so the metal keeps its specular colour.
Danger crimson is NOT a trim: it stays the same for every race.

Production resolution: 2x design px (design px = a 1920x1080 screen), at most 2048 px a side.

Pieces (art/ui/hud/out/quietcorners/), all original:
  Slip<Race>.png        800x160   event slip (toast): deckled paper, a trim pin, a ruled line; the text and icon are live
  PromptCap<Race>.png   256x256   in-world key-cap: iron cap, trim bezel, recessed face for the live key name
  PromptCapFill.png     256x256   greyscale hold fill (tinted candle-gold, wiped by HoldDuration)
  PromptTag<Race>.png   640x128   the paper tag that unrolls beside the nearest prompt (live action text)
  PromptPip<Race>.png    96x96    the dim pip on prompts that are not the nearest
  PlateTrim<Race>.png  1200x400   the Bell Tower plate with that race's trim (9-slice, centre 120..1080 x 120..280)
  SkipRing<Race>.png    256x256   hold-to-skip ring for cinematics; SkipRingFill.png is its greyscale fill
  Book.png             2048x1164  the open book every menu opens in: leather boards, two paper pages, iron corner
                                  guards with brass trim, a crimson ribbon; page text is live
  BookCorner<Race>.png  320x320   the corner guard with that race's trim (laid over Book's corners in game)
  BookTab.png / BookTabOn.png 400x160  leather index tabs down the right page edge
  CompassStrip<Race>.png 1200x112 the compass strip (keeps today's top-centre strip format; faded ends)
  CompassLubber<Race>.png 96x120  the centre pointer; CompassTicks.png 600x48 greyscale tick tile (30 degrees)
  _sheet.png, _races.png          preview sheets

  python make_quietcorners.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import make_health_pbr as P

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "quietcorners"
OUT.mkdir(parents=True, exist_ok=True)

RACES = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]

# Bloodline trims. metal: Brass maps re-tinted (tint, rough_mul, rough_add); gem: glass colour (linear);
# paper: tint of the Paper maps; extra: "verdigris" patches or "hammer" dimples.
TRIMS = {
    "Human":    dict(tint=(1.0, 0.84, 0.58), rm=0.62, ra=-0.06, gem=(0.55, 0.02, 0.04), paper=(1.0, 0.93, 0.78), extra=None),
    "Priest":   dict(tint=(0.96, 0.95, 0.92), rm=0.45, ra=-0.04, gem=(0.06, 0.2, 0.7), paper=(1.0, 0.98, 0.93), extra="gilt"),
    "Vampire":  dict(tint=(0.5, 0.5, 0.56), rm=0.42, ra=-0.02, gem=(0.32, 0.0, 0.05), paper=(0.98, 0.88, 0.8), extra="oxblood"),
    "Werewolf": dict(tint=(0.96, 0.52, 0.34), rm=0.75, ra=0.0, gem=(0.95, 0.42, 0.04), paper=(0.92, 0.78, 0.58), extra="hammer"),
    "Ghoul":    dict(tint=(0.78, 0.6, 0.36), rm=0.8, ra=0.04, gem=(0.4, 0.68, 0.22), paper=(0.92, 0.86, 0.6), extra="verdigris"),
    "Wraith":   dict(tint=(0.72, 0.76, 0.84), rm=0.95, ra=0.08, gem=(0.42, 0.68, 0.98), paper=(0.82, 0.83, 0.85), extra="frost"),
}


# ---------------------------------------------------------------- helpers
def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def save_grey(v, alpha, name):
    save(np.dstack([v, v, v]), alpha, name)


def dist(m):
    return ndimage.distance_transform_edt(m > 0.5).astype(np.float32)


def soft(m, s=0.8):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float32), s), 0, 1)


def mix(a, b, m):
    if isinstance(a, np.ndarray) and a.ndim == 3:
        m = m[..., None]
    elif isinstance(b, np.ndarray) and b.ndim == 3:
        m = m[..., None]
    return a * (1 - m) + b * m


def grid(W, H):
    return np.mgrid[0:H, 0:W].astype(np.float32)


def noise(W, H, sigma, seed):
    n = ndimage.gaussian_filter(np.random.default_rng(seed).standard_normal((H, W)), sigma)
    return n / (np.abs(n).max() + 1e-6)


def rrect(W, H, x0, y0, x1, y1, r, ss=2):
    im = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(im).rounded_rectangle((x0 * ss, y0 * ss, x1 * ss, y1 * ss), radius=r * ss, fill=255)
    return np.array(im.resize((W, H), Image.BOX), np.float32) / 255.0


def disc(W, H, cx, cy, r):
    YY, XX = grid(W, H)
    return soft(np.hypot(XX - cx, YY - cy) <= r, 0.7)


def ring(W, H, cx, cy, r0, r1):
    YY, XX = grid(W, H)
    R = np.hypot(XX - cx, YY - cy)
    return soft((R >= r0) & (R <= r1), 0.7)


def iron_mat(W, H, period=256):
    return P.material("Iron", (W, H), period, tint=(0.22, 0.21, 0.24), rough_mul=0.8)


def trim_mat(race, W, H, period=256):
    """(albedo, normal, rough, metal, height_add) for a race's trim metal."""
    t = TRIMS[race]
    col, nrm, rough, met = P.material("Brass", (W, H), period, tint=t["tint"], rough_mul=t["rm"], rough_add=t["ra"])
    if race != "Human":
        # the brass map's own yellow would win over the tint: rebuild the colour from its luminance
        lum = col.mean(-1, keepdims=True)
        col = lum / (lum.mean() + 1e-6) * 0.6 * P.srgb_to_lin(np.array(t["tint"], np.float32))
    hadd = np.zeros((H, W), np.float32)
    ex = t["extra"]
    if ex == "verdigris":
        patch = np.clip(noise(W, H, 10, 7) * 2.2 + 0.1, 0, 1)
        col = mix(col, np.array([0.08, 0.26, 0.2]), patch * 0.85)
        rough = mix(rough, 0.85, patch)
        met = mix(met, 0.1, patch)
    elif ex == "hammer":
        YY, XX = grid(W, H)
        rng = np.random.default_rng(3)
        d = np.zeros((H, W), np.float32)
        for _ in range(int(W * H / 260)):
            cx, cy, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 9)
            y0, y1, x0, x1 = int(max(cy - r, 0)), int(min(cy + r + 1, H)), int(max(cx - r, 0)), int(min(cx + r + 1, W))
            if y1 <= y0 or x1 <= x0:
                continue
            sub = 1 - np.hypot(XX[y0:y1, x0:x1] - cx, YY[y0:y1, x0:x1] - cy) / r
            d[y0:y1, x0:x1] = np.maximum(d[y0:y1, x0:x1], np.clip(sub, 0, 1))
        hadd = -d * 0.05
    elif ex == "frost":
        fr = np.clip(noise(W, H, 2.5, 11) * 2.5, 0, 1)
        col = mix(col, np.array([0.75, 0.82, 0.9]), fr * 0.35)
        rough = np.clip(rough + fr * 0.2, 0.04, 1)
    elif ex == "gilt":
        leaf = np.clip(noise(W, H, 6, 5) * 2.0 - 0.3, 0, 1)
        col = mix(col, np.array([1.0, 0.76, 0.36]), leaf * 0.55)
    return col, nrm, rough, met, hadd


def paper_mat(race, W, H, period=300, seed=0):
    """Procedural albedo (no tiled motifs on big sheets) over the Paper map's fibre normals."""
    _, nrm, _, _ = P.material("Paper", (W, H), period, metal=0.0)
    base = P.srgb_to_lin(np.array(TRIMS[race]["paper"], np.float32) * 0.88)
    v = 0.86 + 0.08 * noise(W, H, max(W, H) / 14, 100 + seed) + 0.04 * noise(W, H, 5, 101 + seed) \
        + 0.025 * noise(W, H, 1.0, 102 + seed)
    stain = np.clip(noise(W, H, max(W, H) / 30, 103 + seed) * 3 - 1.6, 0, 1)
    col = base * v[..., None]
    col = mix(col, base * np.array([0.62, 0.48, 0.32]), stain * 0.45)
    rough = np.full((H, W), 0.88, np.float32)
    return col, nrm, rough, np.zeros((H, W), np.float32)


def deckle(W, H, inset, seed, amp=3.0):
    YY, XX = grid(W, H)
    n = noise(W, H, 2.0, seed) * amp * 3
    d = np.minimum(np.minimum(XX - inset, W - 1 - inset - XX), np.minimum(YY - inset, H - 1 - inset - YY))
    return soft((d + n > 0).astype(np.float32), 0.6)


def gem_layer(race, mask, Hf, emis_k=0.18):
    """A glass cabochon: dome height, glossy, the race's colour, a little inner glow."""
    g = np.array(TRIMS[race]["gem"], np.float32)
    dome = P.dome(dist(mask), max(2.0, float(np.sqrt(mask.sum() / np.pi)) * 0.9))
    return np.maximum(Hf, mask * (0.85 + 0.35 * dome)), g, dome[..., None] * g * emis_k * mask[..., None]


class Layers:
    """Paint materials into one image by mask, then shade once."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.alb = np.zeros((H, W, 3), np.float32)
        self.nrm = np.zeros((H, W, 3), np.float32)
        self.nrm[..., 2] = 1
        self.rough = np.full((H, W), 0.6, np.float32)
        self.metal = np.zeros((H, W), np.float32)
        self.Hf = np.zeros((H, W), np.float32)
        self.emis = np.zeros((H, W, 3), np.float32)
        self.alpha = np.zeros((H, W), np.float32)

    def paint(self, mask, mat, height=None, alb_mul=1.0):
        col, nrm, rough, met = mat[:4]
        self.alb = mix(self.alb, col * alb_mul, mask)
        self.nrm = mix(self.nrm, nrm, mask)
        self.rough = mix(self.rough, rough, mask)
        self.metal = mix(self.metal, met, mask)
        if height is not None:
            self.Hf = self.Hf * (1 - mask) + height * mask
        self.alpha = np.maximum(self.alpha, mask)

    def gem(self, race, mask):
        self.Hf, g, e = gem_layer(race, mask, self.Hf)
        self.alb = mix(self.alb, np.broadcast_to(g, self.alb.shape), mask)
        self.rough = mix(self.rough, 0.08, mask)
        self.metal = mix(self.metal, 0.0, mask)
        self.emis += e
        self.alpha = np.maximum(self.alpha, mask)

    def render(self, strength=20.0, detail_k=0.25, ao=(3, 2.0)):
        N = P.normals_from(self.Hf, strength, self.nrm, detail_k)
        return P.shade(self.alb, N, self.rough, self.metal, P.ao_from(self.Hf, *ao), emissive=self.emis)


# ---------------------------------------------------------------- slips (event toasts)
def slip(race):
    W, H = 800, 160
    YY, XX = grid(W, H)
    L = Layers(W, H)
    pap = paper_mat(race, W, H, 320)
    m = deckle(W, H, 8, 41 + RACES.index(race), 2.5)
    # a slight curl: the right end lifts
    Hf_p = 0.25 + 0.06 * (XX / W) ** 3 + noise(W, H, 8, 9) * 0.012
    L.paint(m, pap, Hf_p)
    edge = np.clip(1 - dist(m) / 14, 0, 1) * m
    L.alb *= (1 - edge[..., None] * 0.3)
    if TRIMS[race]["extra"] == "oxblood":
        L.alb = mix(L.alb, np.array([0.18, 0.01, 0.02]), np.clip(1 - dist(m) / 7, 0, 1) * m * 0.8)
    rule = ((np.abs(YY - 128) < 1.3) & (XX > 120) & (XX < W - 30)).astype(np.float32)
    L.alb = mix(L.alb, np.array([0.32, 0.05, 0.05]), soft(rule, 0.5) * 0.55)
    # the pin: a trim-metal domed head with a gem, through the slip at the left
    tm = trim_mat(race, W, H, 160)
    head = disc(W, H, 58, 80, 30)
    L.paint(head, tm, 0.7 + 0.4 * P.dome(dist(head), 14) + tm[4])
    L.gem(race, disc(W, H, 58, 80, 12))
    rgb = L.render(18.0)
    # cast shadow under the slip
    sh = soft(np.roll(np.roll(m, 6, 0), 4, 1), 6) * 0.55
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    rgb = mix(np.zeros_like(rgb), rgb, np.where(a > 0, L.alpha / np.maximum(a, 1e-4), 0))
    save(rgb, a, f"Slip{race}.png")


# ---------------------------------------------------------------- prompts
def prompt_cap(race):
    S = 256
    L = Layers(S, S)
    iron = iron_mat(S, S, 200)
    body = rrect(S, S, 26, 26, S - 26, S - 26, 46)
    face = rrect(S, S, 58, 58, S - 58, S - 58, 26)
    bez = np.clip(body - rrect(S, S, 40, 40, S - 40, S - 40, 36), 0, 1)
    Hb = 0.45 + 0.3 * P.dome(dist(body), 26)
    L.paint(body, iron, Hb, 0.9)
    L.paint(face, iron, 0.5 - 0.06 * P.dome(dist(face), 14), 0.55)       # recessed, darker face for the live key
    tm = trim_mat(race, S, S, 180)
    L.paint(bez, tm, 0.78 + 0.25 * P.dome(dist(bez), 7) + tm[4])
    for cx, cy in ((44, 44), (S - 44, 44), (44, S - 44), (S - 44, S - 44)):
        r = disc(S, S, cx, cy, 7)
        L.paint(r, tm, 0.95 + 0.2 * P.dome(dist(r), 5))
    rgb = L.render(22.0)
    sh = soft(np.roll(body, 8, 0), 7) * 0.6
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    rgb = rgb * (L.alpha / np.maximum(a, 1e-4))[..., None]
    save(rgb, a, f"PromptCap{race}.png")


def prompt_cap_fill():
    S = 256
    face = rrect(S, S, 58, 58, S - 58, S - 58, 26)
    YY, XX = grid(S, S)
    glow = np.clip(1 - np.hypot(XX - S / 2, YY - S / 2 - 18) / 120, 0, 1) ** 0.6
    save_grey(0.55 + 0.45 * glow, face * 0.92, "PromptCapFill.png")


def prompt_tag(race):
    W, H = 640, 128
    YY, XX = grid(W, H)
    L = Layers(W, H)
    pap = paper_mat(race, W, H, 260)
    shape = P.polymask((W, H), [[(44, 10), (W - 14, 10), (W - 14, H - 10), (44, H - 10), (8, H / 2)]])
    shape = np.clip(shape * deckle(W, H, 0, 61, 1.5) + shape * (XX < 60), 0, 1) * shape
    roll = np.clip((XX - (W - 60)) / 46, 0, 1)                      # the unrolled end still curls
    Hf = 0.25 + roll ** 2 * 0.25 + noise(W, H, 6, 3) * 0.01
    L.paint(shape, pap, Hf)
    L.alb *= (1 - roll[..., None] * 0.22 * shape[..., None])
    hole = disc(W, H, 40, H / 2, 9)
    tm = trim_mat(race, W, H, 120)
    eye = ring(W, H, 40, H / 2, 9, 16)
    L.paint(eye, tm, 0.6 + 0.3 * P.dome(dist(eye), 4))
    rgb = L.render(16.0)
    sh = soft(np.roll(shape, 5, 0), 5) * 0.5
    al = np.clip(L.alpha - hole, 0, 1)
    a = np.clip(al + sh * (1 - al) * (1 - hole), 0, 1)
    rgb = rgb * (al / np.maximum(a, 1e-4))[..., None]
    save(rgb, a, f"PromptTag{race}.png")


def prompt_pip(race):
    S = 96
    L = Layers(S, S)
    tm = trim_mat(race, S, S, 96)
    r = ring(S, S, S / 2, S / 2, 20, 30)
    L.paint(r, tm, 0.6 + 0.3 * P.dome(dist(r), 5))
    L.gem(race, disc(S, S, S / 2, S / 2, 16))
    rgb = L.render(16.0)
    save(rgb, L.alpha * 0.95, f"PromptPip{race}.png")


# ---------------------------------------------------------------- the Bell Tower plate, per race
def plate_trim(race):
    W, H = 1200, 400
    L = Layers(W, H)
    iron = iron_mat(W, H, 300)
    cut = 44
    body = P.polymask((W, H), [[(cut, 8), (W - cut, 8), (W - 8, cut), (W - 8, H - cut), (W - cut, H - 8), (cut, H - 8), (8, H - cut), (8, cut)]])
    c2 = cut + 20
    inner = P.polymask((W, H), [[(c2, 32), (W - c2, 32), (W - 32, c2), (W - 32, H - c2), (W - c2, H - 32), (c2, H - 32), (32, H - c2), (32, c2)]])
    bead = np.clip(body - inner, 0, 1)
    L.paint(inner, iron, 0.3 + noise(W, H, 12, 2) * 0.01, 0.5)
    L.alpha = inner * 0.86
    tm = trim_mat(race, W, H, 300)
    L.paint(bead, tm, 0.55 + 0.35 * P.dome(dist(bead), 10) + tm[4])
    for x in (62, W - 62):
        for y in (62, H - 62):
            L.paint(disc(W, H, x, y, 14), tm, 0.95 + 0.2 * P.dome(dist(disc(W, H, x, y, 14)), 9))
    L.gem(race, disc(W, H, W / 2, 20, 13))      # a cabochon set in the top bead
    rgb = L.render(22.0, ao=(6, 2.0))
    save(rgb, L.alpha, f"PlateTrim{race}.png")


# ---------------------------------------------------------------- skip ring
def skip_ring(race):
    S = 256
    L = Layers(S, S)
    iron = iron_mat(S, S, 200)
    track = ring(S, S, S / 2, S / 2, 84, 110)
    L.paint(track, iron, 0.35, 0.6)
    tm = trim_mat(race, S, S, 160)
    for r0, r1 in ((76, 84), (110, 120)):
        b = ring(S, S, S / 2, S / 2, r0, r1)
        L.paint(b, tm, 0.6 + 0.3 * P.dome(dist(b), 4) + tm[4])
    rgb = L.render(18.0)
    save(rgb, L.alpha, f"SkipRing{race}.png")


def skip_ring_fill():
    S = 256
    t = ring(S, S, S / 2, S / 2, 86, 108)
    YY, XX = grid(S, S)
    R = np.hypot(XX - S / 2, YY - S / 2)
    v = 0.7 + 0.3 * np.cos((R - 97) / 11 * np.pi / 2)
    save_grey(np.clip(v, 0, 1), t, "SkipRingFill.png")


# ---------------------------------------------------------------- the open book
def book(race="Human"):
    W, H = 2048, 1164
    YY, XX = grid(W, H)
    L = Layers(W, H)
    leather = P.material("Leather", (W, H), 420, tint=(0.15, 0.05, 0.04), rough_mul=0.85)
    cover = rrect(W, H, 10, 10, W - 10, H - 10, 28)
    gx = W / 2
    # boards: leather, a blind-tooled border groove
    groove = np.clip(rrect(W, H, 34, 34, W - 34, H - 34, 18) - rrect(W, H, 40, 40, W - 40, H - 40, 14), 0, 1)
    Hc = 0.2 + 0.08 * P.dome(dist(cover), 30) - groove * 0.06 + noise(W, H, 3, 17) * 0.006
    L.paint(cover, leather, Hc)
    L.paint(groove * 0.85, trim_mat(race, W, H, 300), 0.16)
    # page block edges (the stack seen at the outer and bottom edges)
    block = rrect(W, H, 78, 70, W - 78, H - 60, 10)
    stripes = 0.5 + 0.5 * np.sin(YY * 1.7) * 0.4
    pages_edge = P.material("Paper", (W, H), 300, tint=(0.82, 0.74, 0.6), metal=0.0)
    L.paint(block, (pages_edge[0] * stripes[..., None], pages_edge[1], pages_edge[2], pages_edge[3]), 0.3)
    # the two pages: each bows up away from the gutter
    pap = paper_mat(race, W, H, 380)
    pap = (pap[0] * np.array([1.12, 1.0, 0.82]) * 1.12,) + pap[1:]
    left = rrect(W, H, 96, 80, gx - 6, H - 80, 8)
    right = rrect(W, H, gx + 6, 80, W - 96, H - 80, 8)
    pages = np.clip(left + right, 0, 1)
    u = np.abs(XX - gx) / (gx - 96)
    bow = np.sin(np.clip(u, 0, 1) * np.pi * 0.5) ** 0.45
    Hp = 0.34 + 0.12 * bow - 0.05 * np.clip(u - 0.92, 0, 1) * 12 + noise(W, H, 10, 23) * 0.006
    L.paint(pages, pap, Hp)
    gutter = np.exp(-((XX - gx) / 46) ** 2)
    L.alb *= (1 - (gutter * 0.6 * pages)[..., None])
    age = np.clip(1 - np.maximum(dist(left), dist(right)) / 110, 0, 1) ** 2 * pages
    L.alb = mix(L.alb, L.alb * np.array([0.5, 0.33, 0.18]), age * 0.75)
    # faint headline rules on each page (live text sits on them)
    for x0 in (170, gx + 90):
        r = ((np.abs(YY - 190) < 1.4) & (XX > x0) & (XX < x0 + gx - 260)).astype(np.float32)
        L.alb = mix(L.alb, np.array([0.3, 0.05, 0.05]), soft(r, 0.5) * 0.5 * pages)
    # the crimson ribbon (danger crimson is house-wide, not a trim)
    rx = gx + 110
    rib = P.polymask((W, H), [[(rx - 18, 0), (rx + 18, 0), (rx + 18, H + 30), (rx, H + 6), (rx - 18, H + 30)]])
    rib = rib * (YY < H - 4)
    silk = P.material("Leather", (W, H), 200, tint=(0.62, 0.02, 0.05), rough_mul=0.5)
    sheen = 0.85 + 0.15 * np.cos((XX - rx) / 18 * np.pi)
    L.paint(rib, (silk[0] * sheen[..., None], silk[1], silk[2], silk[3]), 0.52 + 0.04 * np.cos((XX - rx) / 18 * np.pi / 2))
    # iron corner guards with trim rivets
    iron = iron_mat(W, H, 260)
    tm = trim_mat(race, W, H, 260)
    for cx, cy, sx, sy in ((10, 10, 1, 1), (W - 10, 10, -1, 1), (10, H - 10, 1, -1), (W - 10, H - 10, -1, -1)):
        tri = P.polymask((W, H), [[(cx, cy), (cx + sx * 170, cy), (cx, cy + sy * 170)]])
        tri = tri * cover
        edge = np.clip(tri - P.polymask((W, H), [[(cx + sx * 12, cy + sy * 12), (cx + sx * 140, cy + sy * 12), (cx + sx * 12, cy + sy * 140)]]), 0, 1) * tri
        L.paint(tri, iron, 0.6 + 0.12 * P.dome(dist(tri), 20), 0.95)
        L.paint(edge, tm, 0.7 + 0.15 * P.dome(dist(edge), 5) + tm[4])
        for k in (0.22, 0.5):
            rv = disc(W, H, cx + sx * 170 * k, cy + sy * 40, 9) + disc(W, H, cx + sx * 40, cy + sy * 170 * k, 9)
            rv = np.clip(rv, 0, 1)
            L.paint(rv, tm, 0.85 + 0.15 * P.dome(dist(rv), 6))
    rgb = L.render(16.0, 0.2, ao=(8, 1.6))
    save(rgb, L.alpha, "Book.png" if race == "Human" else f"Book{race}.png")


def book_corner(race):
    S = 320
    L = Layers(S, S)
    iron = iron_mat(S, S, 200)
    tm = trim_mat(race, S, S, 200)
    tri = P.polymask((S, S), [[(8, 8), (300, 8), (8, 300)]])
    inner = P.polymask((S, S), [[(28, 28), (250, 28), (28, 250)]])
    edge = np.clip(tri - inner, 0, 1)
    L.paint(tri, iron, 0.6 + 0.15 * P.dome(dist(tri), 30), 0.95)
    L.paint(edge, tm, 0.72 + 0.18 * P.dome(dist(edge), 8) + tm[4])
    for x, y in ((70, 34), (160, 34), (34, 70), (34, 160)):
        rv = disc(S, S, x, y, 12)
        L.paint(rv, tm, 0.9 + 0.2 * P.dome(dist(rv), 8))
    L.gem(race, disc(S, S, 92, 92, 26))
    rgb = L.render(20.0)
    save(rgb, L.alpha, f"BookCorner{race}.png")


def book_tab(on):
    W, H = 400, 160
    L = Layers(W, H)
    tint = (0.62, 0.03, 0.06) if on else (0.22, 0.12, 0.1)
    lea = P.material("Leather", (W, H), 200, tint=tint, rough_mul=0.85)
    tab = rrect(W, H, -40, 14, W - 10, H - 14, 30)
    stitch = np.clip(rrect(W, H, -40, 30, W - 26, H - 30, 18) - rrect(W, H, -40, 33, W - 29, H - 33, 16), 0, 1)
    YY, XX = grid(W, H)
    dash = ((XX.astype(int) // 10 + YY.astype(int) // 10) % 2 == 0).astype(np.float32)
    L.paint(tab, lea, 0.4 + 0.15 * P.dome(dist(tab), 16))
    L.alb = mix(L.alb, np.array([0.62, 0.48, 0.3]) if on else np.array([0.4, 0.3, 0.2]), stitch * dash * 0.8)
    rgb = L.render(16.0)
    save(rgb, L.alpha, "BookTabOn.png" if on else "BookTab.png")


# ---------------------------------------------------------------- compass strip (keeps the in-game strip format)
def compass_strip(race):
    """The slim strip across the top centre: an iron channel with trim beads, ends fading out (Gui.Compass)."""
    W, H = 1200, 112
    YY, XX = grid(W, H)
    L = Layers(W, H)
    iron = iron_mat(W, H, 240)
    chan = rrect(W, H, 0, 18, W, H - 18, 8)
    L.paint(chan, iron, 0.3 - 0.04 * np.exp(-((YY - H / 2) / 18) ** 2) + noise(W, H, 6, 4) * 0.01, 0.7)
    tm = trim_mat(race, W, H, 200)
    for yc in (14, H - 14):
        b = soft(np.abs(YY - yc) <= 5, 0.7)
        L.paint(b, tm, 0.55 + 0.3 * np.sqrt(np.clip(1 - ((YY - yc) / 5.5) ** 2, 0, 1)) + tm[4])
    rgb = L.render(20.0)
    u = np.abs(XX - W / 2) / (W / 2)
    fade = np.clip((1 - u) / 0.22, 0, 1) ** 1.5           # faded ends, as today
    save(rgb, L.alpha * np.where(chan > 0.5, 0.9, 1.0) * fade, f"CompassStrip{race}.png")


def compass_lubber(race):
    """The centre mark: a trim-metal pointer with the race's gem, hung over the strip's top bead."""
    W, H = 96, 120
    L = Layers(W, H)
    tm = trim_mat(race, W, H, 96)
    tri = P.polymask((W, H), [[(14, 10), (82, 10), (48, 104)]])
    L.paint(tri, tm, 0.5 + 0.35 * P.dome(dist(tri), 10) + tm[4])
    L.gem(race, disc(W, H, 48, 36, 13))
    rgb = L.render(18.0)
    save(rgb, L.alpha, f"CompassLubber{race}.png")


def compass_ticks():
    """Greyscale engraved ticks, tileable: 600 px = 30 degrees at 2x (a major tick at 0, a minor at 15)."""
    W, H = 600, 48
    YY, XX = grid(W, H)
    t = np.zeros((H, W), np.float32)
    for x, h, wd in ((0, 30, 3.0), (W, 30, 3.0), (W / 2, 18, 2.0), (W / 4, 8, 1.4), (3 * W / 4, 8, 1.4)):
        t = np.maximum(t, soft((np.abs(XX - x) <= wd) & (np.abs(YY - H / 2) <= h / 2), 0.6))
    save_grey(np.full((H, W), 0.92, np.float32), t, "CompassTicks.png")


# ---------------------------------------------------------------- previews
def sheet(names, path, W=2000, fit=(440, 300), bg=(16, 14, 20, 255)):
    canvas = Image.new("RGBA", (W, 4000), bg)
    x = y = 16
    rh = 0
    for n in names:
        im = Image.open(OUT / f"{n}.png")
        im.thumbnail(fit)
        if x + im.width > W:
            x = 16
            y += rh + 16
            rh = 0
        canvas.alpha_composite(im, (x, y))
        x += im.width + 16
        rh = max(rh, im.height)
    canvas.crop((0, 0, W, y + rh + 16)).save(OUT / path)


if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    run = (lambda k: not only or k in only)
    for r in RACES:
        if run("slip"): slip(r)
        if run("prompt"): prompt_cap(r); prompt_tag(r); prompt_pip(r)
        if run("plate"): plate_trim(r)
        if run("skip"): skip_ring(r)
        if run("corner"): book_corner(r)
        if run("compass"): compass_strip(r); compass_lubber(r)
        print("race", r, flush=True)
    if run("prompt"): prompt_cap_fill()
    if run("skip"): skip_ring_fill()
    if run("compass"): compass_ticks()
    if run("book"): book("Human"); book_tab(False); book_tab(True)
    sheet(["Book", "BookTab", "BookTabOn", "PromptCapHuman", "PromptCapFill", "PromptTagHuman", "PromptPipHuman",
           "SlipHuman", "PlateTrimHuman", "CompassStripHuman", "CompassLubberHuman", "CompassTicks", "SkipRingHuman", "SkipRingFill", "BookCornerHuman"], "_sheet.png", fit=(900, 520))
    rows = []
    for r in RACES:
        rows += [f"CompassStrip{r}", f"PlateTrim{r}", f"PromptCap{r}", f"PromptPip{r}", f"Slip{r}", f"BookCorner{r}"]
    sheet(rows, "_races.png", W=2100, fit=(560, 200))
    print("ok", OUT)
