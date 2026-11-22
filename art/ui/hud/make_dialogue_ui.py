"""Dialogue, all-new art: the calling card, the inked ribbon and the reply tabs (Nightmare Highschool).

Design: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md, section "Dialogue".
Same PBR shader as the rest of the kit (make_health_pbr.py, helpers from make_quietcorners.py). 2x design px, at most
2048 a side. No words are baked: names, lines and replies are live text.

Pieces (art/ui/hud/out/dialogue/):
  CallingCard<Race>.png  1040x240  the speaker's card: blackened iron, trim bead, a socket for the seal
  Crest<Clique>.png       512x512  the speaker's clique crest: a cameo of coloured enamel, a beaded metal rim and a
                                   raised emblem (Ink: nib and drop, Vigil: lantern, Court: fanged chalice, Athletes:
                                   laurel and star, Delinquents: broken padlock, Pack: paw, Ordinary: key, Choir: haloed cross)
  Ribbon.png             2048x280  the torn parchment ribbon the line is inked on (9-slice: centre 240..1808)
  ReplyTab<Race>.png     1000x128  a reply: iron tab, trim edge, a key-cap socket at the left
  ReplyTabOn<Race>.png   1000x128  the selected reply: crimson velvet inlay, warmer trim
  Tone<Kind>.png           96x96   tone marks in relief: Kind (candle), Sly (mask), Threat (dagger), Ask (quill)
  Nib.png                  96x96   the quill nib that bobs when a line has finished typing
  _sheet.png

  python make_dialogue_ui.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

import make_health_pbr as P
import make_quietcorners as Q
from make_quietcorners import Layers, disc, dist, grid, mix, noise, rrect, ring, soft, trim_mat, iron_mat

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "dialogue"
OUT.mkdir(parents=True, exist_ok=True)
Q.OUT = OUT
RACES = Q.RACES


def shadowed(L, shape, name, k=0.6, off=(8, 6), blur=7, emboss=18.0):
    rgb = L.render(emboss)
    sh = soft(np.roll(np.roll(shape, off[0], 0), off[1], 1), blur) * k
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    Q.save(rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a, name)


def calling_card(race):
    W, H = 1040, 240
    L = Layers(W, H)
    iron = iron_mat(W, H, 260)
    tm = trim_mat(race, W, H, 260)
    cx = cy = 120
    body = Q.P.polymask((W, H), [[(120, 14), (W - 40, 14), (W - 10, H / 2), (W - 40, H - 14), (120, H - 14)]],
                        [(6, 6, 234, 234)])
    face = Q.P.polymask((W, H), [[(230, 34), (W - 52, 34), (W - 30, H / 2), (W - 52, H - 34), (230, H - 34)]])
    L.paint(body, iron, 0.42 + 0.18 * P.dome(dist(body), 22), 0.85)
    L.paint(face, iron, 0.36 - 0.03 * P.dome(dist(face), 20), 0.55)
    bead = np.clip(body - Q.P.polymask((W, H), [[(128, 24), (W - 46, 24), (W - 20, H / 2), (W - 46, H - 24), (128, H - 24)]],
                                       [(16, 16, 224, 224)]), 0, 1)
    L.paint(bead, tm, 0.7 + 0.2 * P.dome(dist(bead), 5) + tm[4])
    sock = disc(W, H, cx, cy, 92)
    L.paint(sock, iron, 0.3 - 0.08 * P.dome(dist(sock), 30), 0.5)       # recess the seal sits in
    rim = ring(W, H, cx, cy, 92, 102)
    L.paint(rim, tm, 0.75 + 0.2 * P.dome(dist(rim), 4))
    YY, XX = grid(W, H)
    rule = ((np.abs(YY - 150) < 1.4) & (XX > 250) & (XX < W - 80)).astype(np.float32)
    L.alb = mix(L.alb, np.array([0.55, 0.06, 0.07]), soft(rule, 0.5) * 0.8)
    shadowed(L, np.clip(body, 0, 1), f"CallingCard{race}.png")


def ribbon():
    W, H = 2048, 280
    L = Layers(W, H)
    YY, XX = grid(W, H)
    # torn top and bottom, curled ends
    def edge(seed):
        from scipy.ndimage import gaussian_filter1d
        rng = np.random.default_rng(seed)
        big = gaussian_filter1d(rng.standard_normal(W), 14)
        fine = gaussian_filter1d(rng.standard_normal(W), 1.6)
        return 9 * big / np.abs(big).max() + 2.2 * fine / np.abs(fine).max()
    top = 44 + edge(71)
    bot = H - 44 + edge(72)
    shape = ((YY > top[None, :]) & (YY < bot[None, :]) & (XX > 30) & (XX < W - 30)).astype(np.float32)
    shape = soft(shape, 0.7)
    pap = Q.paper_mat("Human", W, H, 340, seed=73)
    u = np.clip(np.minimum(XX - 30, W - 30 - XX) / 160, 0, 1)
    curl = (1 - u) ** 2
    Hf = 0.3 + curl * 0.28 + noise(W, H, 12, 74) * 0.01
    L.paint(shape, pap, Hf)
    burn = np.clip(1 - dist(shape) / 26, 0, 1) ** 1.5 * shape
    L.alb = mix(L.alb, L.alb * np.array([0.42, 0.26, 0.14]), burn * 0.85)
    L.alb *= (1 - curl[..., None] * 0.35 * shape[..., None])
    shadowed(L, shape, "Ribbon.png", k=0.7, off=(10, 0), blur=10, emboss=14.0)


def reply_tab(race, on):
    W, H = 1000, 128
    L = Layers(W, H)
    iron = iron_mat(W, H, 220)
    tm = trim_mat(race, W, H, 220)
    body = Q.P.polymask((W, H), [[(10, 8), (W - 40, 8), (W - 8, H / 2), (W - 40, H - 8), (10, H - 8)]])
    inlay = Q.P.polymask((W, H), [[(132, 24), (W - 52, 24), (W - 30, H / 2), (W - 52, H - 24), (132, H - 24)]])
    L.paint(body, iron, 0.42 + 0.16 * P.dome(dist(body), 16), 0.9 if on else 0.75)
    if on:
        vel = P.material("Leather", (W, H), 160, tint=(0.5, 0.02, 0.05), rough_mul=0.95)
        L.paint(inlay, vel, 0.36 - 0.02 * P.dome(dist(inlay), 12))
    else:
        L.paint(inlay, iron, 0.36 - 0.02 * P.dome(dist(inlay), 12), 0.5)
    edge = np.clip(body - Q.P.polymask((W, H), [[(16, 14), (W - 44, 14), (W - 16, H / 2), (W - 44, H - 14), (16, H - 14)]]), 0, 1)
    L.paint(edge, tm, 0.7 + 0.2 * P.dome(dist(edge), 4) + tm[4], 1.15 if on else 0.9)
    sock = rrect(W, H, 26, 20, 114, H - 20, 14)
    L.paint(sock, iron, 0.32, 0.45)
    if on:
        L.emis += (np.exp(-((np.arange(W)[None, :] - 70) / 60.0) ** 2) * sock)[..., None] * np.array([0.35, 0.2, 0.06])
    shadowed(L, body, f"ReplyTab{'On' if on else ''}{race}.png", k=0.55, off=(6, 4), blur=5)


def tone(kind):
    S = 96
    L = Layers(S, S)
    tm = trim_mat("Human", S, S, 96)
    c = S / 2
    if kind == "Kind":   # a candle
        m = np.clip(Q.P.polymask((S, S), [[(40, 44), (56, 44), (56, 84), (40, 84)]]) +
                    Q.P.polymask((S, S), [], [(42, 16, 54, 40)]), 0, 1)
    elif kind == "Sly":  # a half mask
        m = Q.P.polymask((S, S), [[(12, 38), (84, 38), (78, 58), (56, 64), (48, 56), (40, 64), (18, 58)]])
        m = np.clip(m - Q.P.polymask((S, S), [], [(24, 42, 40, 54), (56, 42, 72, 54)]), 0, 1)
    elif kind == "Threat":  # a dagger
        m = np.clip(Q.P.polymask((S, S), [[(46, 8), (52, 8), (54, 60), (44, 60)]]) +
                    Q.P.polymask((S, S), [[(30, 60), (68, 60), (68, 66), (30, 66)]]) +
                    Q.P.polymask((S, S), [[(45, 66), (53, 66), (53, 86), (45, 86)]]), 0, 1)
    else:  # Ask: a quill
        m = np.clip(Q.P.polymask((S, S), [[(70, 8), (80, 14), (36, 76), (28, 84), (30, 72)]]) +
                    Q.P.polymask((S, S), [[(22, 80), (32, 80), (20, 92)]]), 0, 1)
    m = soft(m, 0.6)
    L.paint(m, tm, 0.5 + 0.4 * P.dome(dist(m), 4) + tm[4])
    shadowed(L, m, f"Tone{kind}.png", k=0.7, off=(3, 2), blur=2, emboss=16.0)


def nib():
    S = 96
    L = Layers(S, S)
    tm = trim_mat("Human", S, S, 96)
    m = Q.P.polymask((S, S), [[(48, 86), (28, 40), (34, 14), (62, 14), (68, 40)]])
    slit = soft((np.abs(grid(S, S)[1] - 48) < 1.2) & (grid(S, S)[0] > 44), 0.4)
    hole = disc(S, S, 48, 44, 5)
    L.paint(m, tm, 0.5 + 0.35 * P.dome(dist(m), 8) + tm[4])
    L.Hf -= (slit + hole) * 0.2
    L.alpha = np.clip(L.alpha - hole - slit * 0.6, 0, 1)
    shadowed(L, m, "Nib.png", k=0.6, off=(3, 2), blur=2)


# ---------------------------------------------------------------- clique crests (replace the wax seal on the card)
CRESTS = {   # clique: (enamel colour, metal tint, metal roughness, emblem)
    "Ink":         ((0.05, 0.07, 0.24), (1.0, 0.84, 0.58), 0.55, "nib"),
    "Vigil":       ((0.03, 0.06, 0.16), (0.92, 0.93, 0.96), 0.45, "lantern"),
    "Court":       ((0.32, 0.01, 0.03), (1.0, 0.8, 0.45), 0.4, "chalice"),
    "Athletes":    ((0.04, 0.16, 0.07), (0.86, 0.6, 0.36), 0.6, "laurel"),
    "Delinquents": ((0.24, 0.08, 0.03), (0.55, 0.56, 0.6), 0.5, "padlock"),
    "Pack":        ((0.05, 0.05, 0.05), (0.9, 0.86, 0.76), 0.8, "paw"),
    "Ordinary":    ((0.1, 0.12, 0.14), (0.74, 0.76, 0.8), 0.6, "key"),
    "Choir":       ((0.5, 0.46, 0.38), (1.0, 0.82, 0.48), 0.4, "halo"),
}


def _metal(W, H, tint, rough):
    col, nrm, r, met = P.material("Brass", (W, H), 256, tint=(1, 1, 1), rough_mul=rough)
    lum = col.mean(-1, keepdims=True)
    col = lum / (lum.mean() + 1e-6) * 0.62 * P.srgb_to_lin(np.array(tint, np.float32))
    return col, nrm, r, met


def _emblem(kind, S):
    c = S / 2
    pm = Q.P.polymask
    if kind == "nib":
        m = pm((S, S), [[(c, 400), (c - 92, 236), (c - 70, 120), (c + 70, 120), (c + 92, 236)]])
        m = np.clip(m - disc(S, S, c, 238, 18) - pm((S, S), [[(c - 4, 250), (c + 4, 250), (c + 2, 392), (c - 2, 392)]]), 0, 1)
        drop = np.clip(disc(S, S, c - 120, 360, 30) + pm((S, S), [[(c - 120, 296), (c - 146, 350), (c - 94, 350)]]), 0, 1)
        return np.clip(m + drop, 0, 1)
    if kind == "lantern":
        body = pm((S, S), [[(c - 60, 170), (c + 60, 170), (c + 76, 350), (c - 76, 350)]])
        win = pm((S, S), [[(c - 36, 196), (c + 36, 196), (c + 46, 324), (c - 46, 324)]])
        top = pm((S, S), [[(c - 70, 150), (c + 70, 150), (c, 96)]]) + ring(S, S, c, 82, 12, 22)
        base = pm((S, S), [[(c - 90, 350), (c + 90, 350), (c + 90, 372), (c - 90, 372)]])
        flame = np.clip(disc(S, S, c, 280, 22) + pm((S, S), [[(c - 18, 272), (c + 18, 272), (c, 220)]]), 0, 1)
        return np.clip(body - win + top + base + flame, 0, 1)
    if kind == "chalice":
        cup = pm((S, S), [[(c - 100, 140), (c + 100, 140), (c + 70, 250), (c + 20, 280), (c - 20, 280), (c - 70, 250)]])
        stem = pm((S, S), [[(c - 14, 280), (c + 14, 280), (c + 14, 350), (c - 14, 350)]])
        foot = pm((S, S), [[(c - 80, 350), (c + 80, 350), (c + 60, 380), (c - 60, 380)]])
        drop = np.clip(disc(S, S, c, 96, 20) + pm((S, S), [[(c - 18, 92), (c + 18, 92), (c, 50)]]), 0, 1)
        lip = pm((S, S), [[(c - 110, 132), (c + 110, 132), (c + 104, 148), (c - 104, 148)]])
        return np.clip(cup + lip + stem + foot + drop, 0, 1)
    if kind == "laurel":
        YY, XX = grid(S, S)
        m = np.zeros((S, S), np.float32)
        for deg in range(130, 411, 20):
            if abs(((deg - 270 + 180) % 360) - 180) < 50:
                continue
            a = np.radians(deg)
            px, py = c + 140 * np.cos(a), 262 + 140 * np.sin(a)
            ang = a + np.pi / 2 + 0.35
            u = (XX - px) * np.cos(ang) + (YY - py) * np.sin(ang)
            v = -(XX - px) * np.sin(ang) + (YY - py) * np.cos(ang)
            m = np.maximum(m, soft((u / 34) ** 2 + (v / 14) ** 2 <= 1, 0.7))
        m = np.maximum(m, ring(S, S, c, 262, 116, 124) * (YY > 180))
        star = pm((S, S), [[(c + 70 * np.sin(np.radians(k * 36)) * (1 if k % 2 == 0 else 0.42),
                             262 - 70 * np.cos(np.radians(k * 36)) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]])
        return np.clip(m + star, 0, 1)
    if kind == "padlock":
        body = Q.rrect(S, S, c - 96, 220, c + 96, 380, 24)
        shackle = ring(S, S, c, 220, 52, 76) * (grid(S, S)[0] < 220)
        gap = pm((S, S), [[(c + 20, 130), (c + 90, 150), (c + 80, 200), (c + 30, 190)]])
        hole = np.clip(disc(S, S, c, 286, 18) + pm((S, S), [[(c - 8, 290), (c + 8, 290), (c + 12, 338), (c - 12, 338)]]), 0, 1)
        crack = pm((S, S), [[(c - 96, 300), (c - 30, 270), (c - 40, 300), (c - 96, 320)]])
        return np.clip(body - hole - crack + shackle - gap, 0, 1)
    if kind == "paw":
        m = np.zeros((S, S), np.float32)
        YY, XX = grid(S, S)
        m = np.maximum(m, soft(((XX - c) / 84) ** 2 + ((YY - 316) / 66) ** 2 <= 1, 0.7))
        for dx, dy in ((-118, 216), (-48, 160), (48, 160), (118, 216)):
            m = np.maximum(m, soft(((XX - c - dx) / 34) ** 2 + ((YY - dy) / 44) ** 2 <= 1, 0.7))
        return m
    if kind == "key":
        bow = ring(S, S, c - 90, c, 34, 62)
        shaft = pm((S, S), [[(c - 32, c - 12), (c + 140, c - 12), (c + 140, c + 12), (c - 32, c + 12)]])
        teeth = pm((S, S), [[(c + 80, c + 12), (c + 100, c + 12), (c + 100, c + 52), (c + 80, c + 52)],
                            [(c + 116, c + 12), (c + 140, c + 12), (c + 140, c + 40), (c + 116, c + 40)]])
        return np.clip(bow + shaft + teeth, 0, 1)
    # halo: a cross inside a ring
    cross = pm((S, S), [[(c - 18, 130), (c + 18, 130), (c + 18, 390), (c - 18, 390)],
                        [(c - 80, 200), (c + 80, 200), (c + 80, 236), (c - 80, 236)]])
    return np.clip(cross + ring(S, S, c, 218, 92, 108), 0, 1)


def crest(clique):
    S = 512
    c = S / 2
    enamel, tint, rough, kind = CRESTS[clique]
    YY, XX = grid(S, S)
    R = np.hypot(XX - c, YY - c)
    L = Layers(S, S)
    met = _metal(S, S, tint, rough)
    rim = soft((R <= 250) & (R >= 214), 0.8)
    beads = soft((0.5 + 0.5 * np.cos(np.arctan2(YY - c, XX - c) * 40)) > 0.55, 0.8) * soft((R >= 226) & (R <= 240), 0.8)
    field = soft(R < 214, 0.8)
    en = (np.broadcast_to(P.srgb_to_lin(np.array(enamel, np.float32)), (S, S, 3)).copy(),
          np.dstack([np.zeros((S, S)), np.zeros((S, S)), np.ones((S, S))]).astype(np.float32),
          np.full((S, S), 0.12, np.float32), np.zeros((S, S), np.float32))
    L.paint(field, en, 0.3 + 0.1 * P.dome(dist(field), 200))
    # guilloche: fine engraved rings under the enamel catch the light
    L.Hf += field * 0.004 * np.cos(R * 0.9)
    L.paint(rim, met, 0.62 + 0.18 * P.dome(dist(rim), 12))
    L.Hf += beads * 0.05
    em = _emblem(kind, S) * soft(R < 200, 0.8)
    L.paint(em, met, 0.48 + 0.22 * P.dome(dist(em), 9))
    rgb = L.render(26.0, 0.25, ao=(5, 2.5))
    sh = soft(np.roll(np.roll(soft(R <= 250, 0.8), 10, 0), 6, 1), 8) * 0.6
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    Q.save(rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a, f"Crest{clique}.png")


def sheet():
    names = ["CallingCardHuman"] + [f"Crest{c}" for c in CRESTS] + [ "Ribbon", "ReplyTabHuman", "ReplyTabOnHuman", "ToneKind", "ToneSly",
             "ToneThreat", "ToneAsk", "Nib", "CallingCardVampire", "ReplyTabOnWraith"]
    Wd = 2100
    canvas = Image.new("RGBA", (Wd, 3000), (16, 14, 20, 255))
    x = y = 16
    rh = 0
    for n in names:
        im = Image.open(OUT / f"{n}.png")
        im.thumbnail((2000, 300) if n == "Ribbon" else (700, 300))
        if x + im.width > Wd:
            x, y, rh = 16, y + rh + 16, 0
        canvas.alpha_composite(im, (x, y))
        x += im.width + 16
        rh = max(rh, im.height)
    canvas.crop((0, 0, Wd, y + rh + 16)).save(OUT / "_sheet.png")


if __name__ == "__main__":
    for r in RACES:
        calling_card(r)
        reply_tab(r, False)
        reply_tab(r, True)
    for cl in CRESTS:
        crest(cl)
        print("crest", cl, flush=True)
    ribbon()
    for k in ("Kind", "Sly", "Threat", "Ask"):
        tone(k)
    nib()
    sheet()
    print("ok", OUT)
