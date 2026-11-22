"""Dialogue, all-new art: the calling card, the inked ribbon and the reply tabs (Nightmare Highschool).

Design: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md, section "Dialogue".
Same PBR shader as the rest of the kit (make_health_pbr.py, helpers from make_quietcorners.py). 2x design px, at most
2048 a side. No words are baked: names, lines and replies are live text.

Pieces (art/ui/hud/out/dialogue/):
  CallingCard<Race>.png  1040x240  the speaker's card: blackened iron, trim bead, a socket for the seal
  Crest<Clique>.png       512x512  the speaker's clique crest: a cameo of coloured enamel, a beaded metal rim and a
                                   raised emblem (Ink: nib and drop, Vigil: lantern, Court: fanged chalice, Athletes:
                                   laurel and star, Delinquents: broken padlock, Pack: paw, Ordinary: key, Choir: haloed cross,
                                   Unaffiliated: a blank shield on a bare, unenamelled field, for anyone with no clique)
  CrestFlip<Clique>.png  1024x1024 the crest's idle light-catch: a 4x4 flipbook of 256 px frames, frame 0 at rest,
                                   played at 15 fps (spec, "Crest animation")
  Ribbon.png             2048x280  the torn parchment ribbon the line is inked on (9-slice: centre 240..1808)
  ReplyTab<Race>.png     1000x128  a reply: iron tab, trim edge, a key-cap socket at the left
  ReplyTabOn<Race>.png   1000x128  the selected reply: crimson velvet inlay, warmer trim
  Tone<Kind>.png           96x96   tone marks in relief: Kind (candle), Sly (mask), Threat (dagger), Ask (quill)
  Nib.png                  96x96   the quill nib that bobs when a line has finished typing
  _sheet.png, _crests.png (all crests large, at the in-game 94 px and at the phone's 56 px)
  docs/superpowers/mockups/2026-11-21-quietcorners/11-crests-idle.{gif,mp4}, 12-dialogue-crest-entrance.{gif,mp4}

  python make_dialogue_ui.py            everything
  python make_dialogue_ui.py crests     the static crests and the sheets only
  python make_dialogue_ui.py anim       the flipbooks and the animation previews only
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
CRESTS = {   # clique: (enamel colour or None for a bare field, metal tint, metal roughness, emblem)
    "Ink":         ((0.05, 0.07, 0.24), (1.0, 0.84, 0.58), 0.55, "nib"),
    "Vigil":       ((0.03, 0.06, 0.16), (0.92, 0.93, 0.96), 0.45, "lantern"),
    "Court":       ((0.32, 0.01, 0.03), (1.0, 0.8, 0.45), 0.4, "chalice"),
    "Athletes":    ((0.04, 0.16, 0.07), (0.86, 0.6, 0.36), 0.6, "laurel"),
    "Delinquents": ((0.24, 0.08, 0.03), (0.55, 0.56, 0.6), 0.5, "padlock"),
    "Pack":        ((0.05, 0.05, 0.05), (0.9, 0.86, 0.76), 0.8, "paw"),
    "Ordinary":    ((0.1, 0.12, 0.14), (0.74, 0.76, 0.8), 0.6, "key"),
    "Choir":       ((0.5, 0.46, 0.38), (1.0, 0.82, 0.48), 0.4, "halo"),
    # anyone with no clique (staff, townsfolk, new students): no enamel was ever poured. The engine-turned field is
    # left bare and oxidised, and the emblem is a blank, unmarked shield in plain iron-pewter. No colour, no arms.
    "Unaffiliated": (None, (0.7, 0.68, 0.64), 0.5, "shield"),
}


def _metal(W, H, tint, rough):
    col, nrm, r, met = P.material("Brass", (W, H), 256, tint=(1, 1, 1), rough_mul=rough)
    lum = col.mean(-1, keepdims=True)
    col = lum / (lum.mean() + 1e-6) * 0.62 * P.srgb_to_lin(np.array(tint, np.float32))
    return col, nrm, r, met


def _shield(S, c, top=126, half=106, shoulder=246, tip=394):
    """A heater shield: a straight top with rounded corners, straight flanks, flanks curving to the point."""
    pts = [(c - half + 10, top), (c + half - 10, top), (c + half - 3, top + 3), (c + half, top + 10)]
    n = 24
    for i in range(n + 1):   # right flank: shoulder -> tip, a quadratic curve that stays full, never a V
        s = i / n
        p0, p1, p2 = np.array([c + half, shoulder]), np.array([c + half, shoulder + 108]), np.array([c, tip])
        q = (1 - s) ** 2 * p0 + 2 * (1 - s) * s * p1 + s ** 2 * p2
        pts.append((float(q[0]), float(q[1])))
    for x, y in reversed(pts[4:-1]):
        pts.append((2 * c - x, y))
    pts += [(c - half, top + 10), (c - half + 3, top + 3)]
    return Q.P.polymask((S, S), [pts])


def _emblem(kind, S, parts=None):
    """The raised emblem mask. `parts` (a dict) collects the pieces the idle animation lights in turn."""
    parts = {} if parts is None else parts
    c = S / 2
    pm = Q.P.polymask
    if kind == "nib":
        m = pm((S, S), [[(c, 400), (c - 92, 236), (c - 70, 120), (c + 70, 120), (c + 92, 236)]])
        m = np.clip(m - disc(S, S, c, 238, 18) - pm((S, S), [[(c - 4, 250), (c + 4, 250), (c + 2, 392), (c - 2, 392)]]), 0, 1)
        drop = np.clip(disc(S, S, c - 120, 360, 30) + pm((S, S), [[(c - 120, 296), (c - 146, 350), (c - 94, 350)]]), 0, 1)
        parts.update(body=m, drop=drop)
        return np.clip(m + drop, 0, 1)
    if kind == "lantern":
        body = pm((S, S), [[(c - 60, 170), (c + 60, 170), (c + 76, 350), (c - 76, 350)]])
        win = pm((S, S), [[(c - 36, 196), (c + 36, 196), (c + 46, 324), (c - 46, 324)]])
        top = pm((S, S), [[(c - 70, 150), (c + 70, 150), (c, 96)]]) + ring(S, S, c, 82, 12, 22)
        base = pm((S, S), [[(c - 90, 350), (c + 90, 350), (c + 90, 372), (c - 90, 372)]])
        flame = np.clip(disc(S, S, c, 280, 22) + pm((S, S), [[(c - 18, 272), (c + 18, 272), (c, 220)]]), 0, 1)
        parts.update(flame=flame, window=np.clip(win - flame, 0, 1))
        return np.clip(body - win + top + base + flame, 0, 1)
    if kind == "chalice":
        cup = pm((S, S), [[(c - 100, 140), (c + 100, 140), (c + 70, 250), (c + 20, 280), (c - 20, 280), (c - 70, 250)]])
        stem = pm((S, S), [[(c - 14, 280), (c + 14, 280), (c + 14, 350), (c - 14, 350)]])
        foot = pm((S, S), [[(c - 80, 350), (c + 80, 350), (c + 60, 380), (c - 60, 380)]])
        drop = np.clip(disc(S, S, c, 96, 20) + pm((S, S), [[(c - 18, 92), (c + 18, 92), (c, 50)]]), 0, 1)
        lip = pm((S, S), [[(c - 110, 132), (c + 110, 132), (c + 104, 148), (c - 104, 148)]])
        parts.update(drop=drop, body=np.clip(cup + lip + stem + foot, 0, 1))
        return np.clip(cup + lip + stem + foot + drop, 0, 1)
    if kind == "laurel":
        YY, XX = grid(S, S)
        m = np.zeros((S, S), np.float32)
        leaves = []
        for deg in range(130, 411, 20):
            if abs(((deg - 270 + 180) % 360) - 180) < 50:
                continue
            a = np.radians(deg)
            px, py = c + 140 * np.cos(a), 262 + 140 * np.sin(a)
            ang = a + np.pi / 2 + 0.35
            u = (XX - px) * np.cos(ang) + (YY - py) * np.sin(ang)
            v = -(XX - px) * np.sin(ang) + (YY - py) * np.cos(ang)
            leaf = soft((u / 34) ** 2 + (v / 14) ** 2 <= 1, 0.7)
            leaves.append((py, leaf))
            m = np.maximum(m, leaf)
        branch = ring(S, S, c, 262, 116, 124) * (YY > 180)
        m = np.maximum(m, branch)
        star = pm((S, S), [[(c + 70 * np.sin(np.radians(k * 36)) * (1 if k % 2 == 0 else 0.42),
                             262 - 70 * np.cos(np.radians(k * 36)) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]])
        parts.update(leaves=leaves, star=star, branch=branch)
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
        pad = soft(((XX - c) / 84) ** 2 + ((YY - 316) / 66) ** 2 <= 1, 0.7)
        m = np.maximum(m, pad)
        toes = []
        for dx, dy in ((-118, 216), (-48, 160), (48, 160), (118, 216)):
            toe = soft(((XX - c - dx) / 34) ** 2 + ((YY - dy) / 44) ** 2 <= 1, 0.7)
            toes.append(toe)
            m = np.maximum(m, toe)
        parts.update(pad=pad, toes=toes)
        return m
    if kind == "key":
        bow = ring(S, S, c - 90, c, 34, 62)
        shaft = pm((S, S), [[(c - 32, c - 12), (c + 140, c - 12), (c + 140, c + 12), (c - 32, c + 12)]])
        teeth = pm((S, S), [[(c + 80, c + 12), (c + 100, c + 12), (c + 100, c + 52), (c + 80, c + 52)],
                            [(c + 116, c + 12), (c + 140, c + 12), (c + 140, c + 40), (c + 116, c + 40)]])
        return np.clip(bow + shaft + teeth, 0, 1)
    if kind == "shield":
        sh = soft(_shield(S, c), 0.7)
        d = dist(sh)
        face = soft(d > 20, 0.7)          # the blank field, sunk inside a raised border
        parts.update(shield=sh, face=face, border=np.clip(sh - face, 0, 1), sdist=d)
        return sh
    # halo: a cross inside a ring
    cross = pm((S, S), [[(c - 18, 130), (c + 18, 130), (c + 18, 390), (c - 18, 390)],
                        [(c - 80, 200), (c + 80, 200), (c + 80, 236), (c - 80, 236)]])
    halo = ring(S, S, c, 218, 92, 108)
    parts.update(cross=cross, halo=halo)
    return np.clip(cross + halo, 0, 1)


CREST_LOOK = dict(strength=26.0, detail_k=0.25, ao=(5, 2.5))


def _build_crest(clique):
    """Paint one crest into Layers. Returns (L, ctx); ctx holds the masks the animation needs."""
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
    if enamel is None:
        # no enamel: the bare, engine-turned plate, darkened by age and matte, so the polished emblem stands off it
        bare = _metal(S, S, tint, 1.0)
        bare = (bare[0], bare[1], np.clip(bare[2] * 1.25 + 0.15, 0.04, 1), bare[3])
        L.paint(field, bare, 0.3 + 0.06 * P.dome(dist(field), 200), 0.24)
        th = np.arctan2(YY - c, XX - c)
        rose = np.cos(R * 1.1 + 2.2 * np.sin(th * 36))      # a guilloche rosette, cut deeper than under enamel
        L.Hf += field * 0.0045 * rose
    else:
        en = (np.broadcast_to(P.srgb_to_lin(np.array(enamel, np.float32)), (S, S, 3)).copy(),
              np.dstack([np.zeros((S, S)), np.zeros((S, S)), np.ones((S, S))]).astype(np.float32),
              np.full((S, S), 0.12, np.float32), np.zeros((S, S), np.float32))
        L.paint(field, en, 0.3 + 0.1 * P.dome(dist(field), 200))
        # guilloche: fine engraved rings under the enamel catch the light
        L.Hf += field * 0.004 * np.cos(R * 0.9)
    L.paint(rim, met, 0.62 + 0.18 * P.dome(dist(rim), 12))
    L.Hf += beads * 0.05
    parts = {}
    em = _emblem(kind, S, parts) * soft(R < 200, 0.8)
    if kind == "shield":
        polished = _metal(S, S, tint, 0.42)
        b, f, d = parts["border"], parts["face"], parts["sdist"]
        L.paint(em, polished, 0.5 + 0.2 * P.dome(d, 10), 1.2)                   # the raised border, rounded
        # the blank face: a gentle convex plate a step below the border, with a fine chamfer where they meet
        fd = dist(f)
        L.Hf = L.Hf * (1 - f) + (0.5 + 0.03 + 0.14 * P.dome(fd, 90) - 0.03 * np.exp(-fd / 2.5)) * f
        L.alb = mix(L.alb, L.alb * 0.95, f)
        L.rough = mix(L.rough, L.rough * 0.7, f)          # the blank face is the best-polished part
    else:
        L.paint(em, met, 0.48 + 0.22 * P.dome(dist(em), 9))
    ctx = dict(S=S, c=c, XX=XX, YY=YY, R=R, rim=rim, field=field, em=em, parts=parts, kind=kind)
    return L, ctx


def _crest_alpha(L, R, rgb):
    sh = soft(np.roll(np.roll(soft(R <= 250, 0.8), 10, 0), 6, 1), 8) * 0.6
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    return rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a


def crest(clique):
    L, ctx = _build_crest(clique)
    rgb = L.render(CREST_LOOK["strength"], CREST_LOOK["detail_k"], ao=CREST_LOOK["ao"])
    Q.save(*_crest_alpha(L, ctx["R"], rgb), f"Crest{clique}.png")


# ---------------------------------------------------------------- crest idle animation (flipbook sheets)
# Each crest gets a 4x4 flipbook, 256 px frames, 1024 x 1024 (CrestFlip<Clique>.png). Frame 0 is the crest at rest
# (identical to Crest<Clique>.png, downscaled); frames 1..15 are one "catch of the light" that starts and ends dark,
# so frame 15 -> frame 0 never pops. Played at 15 fps (one second), then held on frame 0 for a few seconds.
FLIP_N, FLIP_FS, FLIP_FPS = 16, 256, 15
GLINT_L = P.normalize(np.array([-0.18, -0.24, 1.0]))     # a small, near-frontal light: flat tops flash as it passes


def _band(p, s, w):
    return np.exp(-((p - s) / w) ** 2)


def _pulse(t, t0, w):
    return float(np.exp(-((t - t0) / w) ** 2))


def _lerp(a, b, t):
    return a + (b - a) * np.clip(t, 0, 1)


def _event(clique, t, ctx):
    """The glint weight map and the extra emission for time t in (0, 1) of the light-catch."""
    XX, YY, c, em, rim, field, P_ = ctx["XX"], ctx["YY"], ctx["c"], ctx["em"], ctx["rim"], ctx["field"], ctx["parts"]
    u, v = (XX - c) / 220.0, (YY - c) / 220.0
    env = float(np.sin(np.pi * t)) ** 1.5   # fades in and out, so frame 15 -> frame 0 never pops
    S = ctx["S"]
    emis = np.zeros((S, S, 3), np.float32)
    W = np.zeros((S, S), np.float32)
    if clique == "Ink":             # the light runs down the nib to its tip, then the ink drop glimmers wet
        W += P_["body"] * _band(v, _lerp(-1.5, 0.95, t / 0.72), 0.2)
        W += P_["drop"] * _pulse(t, 0.8, 0.09) * 1.5
        W += field * _band(v, _lerp(-1.5, 0.95, t / 0.72), 0.25) * 0.15
    elif clique == "Vigil":         # the flame gutters up and settles; its warmth fills the lantern's window
        f = (0.75 + 0.25 * np.sin(t * 38.0) * np.sin(t * 17.0)) * float(np.sin(np.pi * t)) ** 1.2
        emis += P_["flame"][..., None] * np.array([1.6, 0.8, 0.22], np.float32) * f
        glow = soft(P_["flame"], 22) * P_["window"]
        emis += (glow / max(glow.max(), 1e-4))[..., None] * np.array([0.9, 0.42, 0.1], np.float32) * f * 0.55
        W += em * _band((u + v) * 0.7, _lerp(-1.0, 1.0, t), 0.22) * 0.55
    elif clique == "Court":         # the blood drop flashes, then the light pours down the chalice
        W += P_["drop"] * _pulse(t, 0.2, 0.09) * 1.5
        W += P_["body"] * _band(v, _lerp(-0.7, 0.9, (t - 0.22) / 0.7), 0.2)
    elif clique == "Athletes":      # the laurel catches the light leaf by leaf, bottom to top, then the star
        leaves = sorted(P_["leaves"], key=lambda e: -e[0])
        ys = sorted({round(y) for y, _ in leaves}, reverse=True)
        for y, leaf in leaves:
            k = ys.index(round(y))
            W += leaf * _pulse(t, 0.1 + 0.55 * k / max(len(ys) - 1, 1), 0.075)
        W += P_["branch"] * _band(-v, _lerp(-0.9, 0.6, t / 0.7), 0.3) * 0.4
        W += P_["star"] * _pulse(t, 0.82, 0.08) * 1.3
    elif clique == "Delinquents":   # a hard glint slides along the crack and over the shackle
        W += em * _band((u - v) * 0.7, _lerp(-1.0, 1.0, t), 0.17)
    elif clique == "Pack":          # moonlight crosses the toes one by one, then settles on the pad
        for k, toe in enumerate(P_["toes"]):
            W += toe * _pulse(t, 0.18 + 0.13 * k, 0.08)
        W += P_["pad"] * _pulse(t, 0.76, 0.11) * 0.9
    elif clique == "Ordinary":      # the light runs the key from bow to teeth
        W += em * _band(u, _lerp(-1.0, 1.0, t), 0.17)
    elif clique == "Choir":         # a light travels once round the halo, then down the cross
        th = np.arctan2(YY - (c - 38), XX - c)
        a0 = -np.pi / 2 + 2 * np.pi * min(t / 0.7, 1.0)
        d = np.angle(np.exp(1j * (th - a0)))
        W += P_["halo"] * np.exp(-(d / 0.45) ** 2) * 1.7 * float(np.clip((0.76 - t) / 0.14, 0, 1))
        W += P_["cross"] * _band(v, _lerp(-1.0, 0.8, (t - 0.62) / 0.36), 0.22)
    else:                           # Unaffiliated: one slow, wide sheen across the blank shield, like a mirror
        sweep = _band((u + 0.6 * v) / 1.17, _lerp(-1.75, 1.75, t), 0.3)
        W += P_["face"] * sweep * 1.1 + P_["border"] * sweep * 0.8
        W += rim * _band((u + 0.6 * v) / 1.17, _lerp(-1.75, 1.75, t), 0.3) * 0.25
    return W * env, emis * env


def _inv_tonemap(rgb):
    y = np.clip(P.srgb_to_lin(np.clip(rgb, 0, 1)), 0, 1.17)
    return y / (1.18 - y)


def _tonemap(x):
    return P.lin_to_srgb(x / (1 + x) * 1.18)


def crest_frames(clique, n=FLIP_N, fs=FLIP_FS, intensity=None):
    """Return the n frames (PIL RGBA, fs px) of a crest's light-catch; frame 0 is the crest at rest."""
    L, ctx = _build_crest(clique)
    rgb = L.render(CREST_LOOK["strength"], CREST_LOOK["detail_k"], ao=CREST_LOOK["ao"])
    base = _inv_tonemap(rgb)
    # the glint reads the shape, not the grain: a near-smooth normal and a blurred roughness, so it travels as a clean
    # streak instead of flashing in blotches where the metal's texture is rough
    N = P.normals_from(L.Hf, CREST_LOOK["strength"], L.nrm, 0.05)
    V = np.array([0.0, 0.0, 1.0])
    Hh = P.normalize(GLINT_L + V)
    NdotL = np.clip((N * GLINT_L).sum(-1), 0, 1)
    NdotH = np.clip((N * Hh).sum(-1), 0, 1)
    NdotV = np.clip(N[..., 2], 1e-3, 1)
    from scipy.ndimage import gaussian_filter
    a = np.clip(gaussian_filter(L.rough, 6) * 0.5, 0.06, 1) ** 2
    D = np.minimum(a ** 2 / (np.pi * (NdotH ** 2 * (a ** 2 - 1) + 1) ** 2 + 1e-8), 30.0)
    F0 = 0.04 * (1 - L.metal[..., None]) + L.alb * L.metal[..., None]
    spec = (D * NdotL / (4 * NdotV + 1e-3))[..., None] * F0 * P.ao_from(L.Hf, *CREST_LOOK["ao"])[..., None]
    # normalise so every crest's brightest glint lands at the same strength whatever its metal's roughness
    ref = np.percentile(spec.mean(-1)[(ctx["em"] > 0.5) | (ctx["rim"] > 0.5)], 97)
    spec = np.minimum(spec / max(ref, 1e-6), 1.6) * np.array([1.0, 0.93, 0.82], np.float32)
    k = intensity if intensity is not None else 3.0
    out = []
    for i in range(n):
        if i == 0:
            f = rgb
        else:
            W, emis = _event(clique, i / n, ctx)
            f = _tonemap(base + spec * (W[..., None] * k) + emis)
        col, al = _crest_alpha(L, ctx["R"], f)
        img = Image.fromarray(np.dstack([np.clip(col, 0, 1) * 255, np.clip(al, 0, 1) * 255]).astype(np.uint8), "RGBA")
        out.append(img.resize((fs, fs), Image.LANCZOS) if fs != ctx["S"] else img)
    return out


def crest_flipbook(clique):
    frames = crest_frames(clique)
    cols = 4
    sheet_ = Image.new("RGBA", (cols * FLIP_FS, ((len(frames) + cols - 1) // cols) * FLIP_FS), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet_.paste(f, ((i % cols) * FLIP_FS, (i // cols) * FLIP_FS))
    sheet_.save(OUT / f"CrestFlip{clique}.png", optimize=True)
    return frames


def crests_sheet():
    """All crests side by side: large, then at the in-game size (94 px at 1080p) and the phone size (56 px)."""
    names = list(CRESTS)
    big, gap = 300, 20
    Wd = gap + len(names) * (big + gap)
    canvas = Image.new("RGBA", (Wd, big + 2 * gap + 94 + gap + 56 + gap), (16, 14, 20, 255))
    for i, n in enumerate(names):
        im = Image.open(OUT / f"Crest{n}.png")
        x = gap + i * (big + gap)
        canvas.alpha_composite(im.resize((big, big), Image.LANCZOS), (x, gap))
        canvas.alpha_composite(im.resize((94, 94), Image.LANCZOS), (x + (big - 94) // 2, big + 2 * gap))
        canvas.alpha_composite(im.resize((56, 56), Image.LANCZOS), (x + (big - 56) // 2, big + 3 * gap + 94))
    canvas.save(OUT / "_crests.png")


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


# ---------------------------------------------------------------- animation previews (GIF + MP4 into the mockups)
MOCK = HERE.parents[2] / "docs" / "superpowers" / "mockups" / "2026-11-21-quietcorners"


def _ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def _write_anim(frames, name, fps, gif_scale=1.0):
    """Write a GIF and an MP4 of RGB frames into the mockup folder (frames are kept on E: for ffmpeg)."""
    import shutil
    import subprocess
    import tempfile
    MOCK.mkdir(parents=True, exist_ok=True)
    gif = frames if gif_scale == 1.0 else [f.resize((round(f.width * gif_scale), round(f.height * gif_scale)), Image.LANCZOS)
                                           for f in frames]
    gif[0].save(MOCK / f"{name}.gif", save_all=True, append_images=gif[1:], duration=round(1000 / fps), loop=0,
                   optimize=True, disposal=1)
    ff = shutil.which("ffmpeg")
    if not ff:
        return
    tmp = Path(tempfile.mkdtemp(dir="E:/NH-tmp" if Path("E:/").exists() else None))
    for i, f in enumerate(frames):
        f.save(tmp / f"f{i:04d}.png")
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "f%04d.png"),
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    str(MOCK / f"{name}.mp4")], check=True)
    shutil.rmtree(tmp, ignore_errors=True)


def preview_idle(all_frames, secs=7.0, size=200):
    """All crests idling in a 3 x 3 grid; each catches the light at its own moment, as in game."""
    fps = FLIP_FPS
    n_out = round(secs * fps)
    names = list(all_frames)
    gap = 24
    cols = 3
    rows = (len(names) + cols - 1) // cols
    W, H = gap + cols * (size + gap), gap + rows * (size + gap)
    small = {n: [f.resize((size, size), Image.LANCZOS) for f in fr] for n, fr in all_frames.items()}
    starts = {n: 0.35 + 0.66 * i for i, n in enumerate(names)}      # staggered like the in-game random idle
    out = []
    for k in range(n_out):
        tsec = k / fps
        cv = Image.new("RGBA", (W, H), (16, 14, 20, 255))
        for i, n in enumerate(names):
            j = round((tsec - starts[n]) * fps)
            fi = j if 1 <= j < FLIP_N else 0
            cv.alpha_composite(small[n][fi], (gap + (i % cols) * (size + gap), gap + (i // cols) * (size + gap)))
        out.append(cv.convert("RGB"))
    _write_anim(out, "11-crests-idle", fps, gif_scale=0.6)


def preview_entrance(frames, race="Human", name="WENDELL PRICE", sub="Custodian · staff", clique="Unaffiliated"):
    """The dialogue card arriving: the card fades in, the crest presses into its socket, then catches the light."""
    import make_quietcorners_mockups as M
    fps, k = 30, 2                      # 30 fps preview at 2x design px (the in-game crest is 94 design px)
    W, H = 660 * k, 200 * k
    card = Image.open(OUT / f"CallingCard{race}.png").resize((520 * k, 120 * k), Image.LANCZOS)
    cx, cy = 60 * k, 40 * k
    sx, sy, sd = cx + 60 * k, cy + 60 * k, 94 * k
    big = [f.resize((sd, sd), Image.LANCZOS) for f in frames]
    out = []
    total = 3.4
    for i in range(round(total * fps)):
        t = i / fps
        cv = Image.new("RGBA", (W, H), (20, 17, 24, 255))
        ca = _ease_out(t / 0.18)
        if ca > 0:
            c2 = card.copy()
            c2.putalpha(c2.getchannel("A").point(lambda v: round(v * ca)))
            cv.alpha_composite(c2, (cx - round((1 - ca) * 12 * k), cy))
        # the crest: drops in large and faint over 0.2 s, presses to 96 % and settles back (0.12 s), then the glint
        tc = t - 0.12
        if tc > 0:
            if tc < 0.2:
                e = _ease_out(tc / 0.2)
                sc, al = 1.18 - 0.18 * e, e
            elif tc < 0.32:
                p = (tc - 0.2) / 0.12
                sc, al = 1.0 - 0.04 * np.sin(np.pi * p), 1.0
            else:
                sc, al = 1.0, 1.0
            g = round((tc - 0.32) * FLIP_FPS)
            fi = g if 1 <= g < FLIP_N else 0
            im = big[fi]
            d = max(2, round(sd * sc))
            im = im.resize((d, d), Image.LANCZOS)
            if al < 1:
                im.putalpha(im.getchannel("A").point(lambda v: round(v * al)))
            cv.alpha_composite(im, (sx - d // 2, sy - d // 2))
        ta = _ease_out((t - 0.2) / 0.25)
        if ta > 0:
            from PIL import ImageDraw
            dr = ImageDraw.Draw(cv)
            fx = cx + round(235 * 520 / 1040 * k) + 8 * k
            dr.text((fx, cy + 44 * k), name, font=M.font(24 * k, "b"), anchor="lm",
                    fill=tuple(round(c_ * ta + 20 * (1 - ta)) for c_ in M.BONE))
            dr.text((fx, cy + 89 * k), sub, font=M.font(20 * k), anchor="lm",
                    fill=tuple(round(c_ * ta + 20 * (1 - ta)) for c_ in M.DIM))
        out.append(cv.convert("RGB"))
    _write_anim(out, "12-dialogue-crest-entrance", fps, gif_scale=0.5)


if __name__ == "__main__":
    import sys
    args = set(sys.argv[1:])
    if not args or "art" in args:
        for r in RACES:
            calling_card(r)
            reply_tab(r, False)
            reply_tab(r, True)
        ribbon()
        for k in ("Kind", "Sly", "Threat", "Ask"):
            tone(k)
        nib()
    if not args or "art" in args or "crests" in args:
        for cl in CRESTS:
            crest(cl)
            print("crest", cl, flush=True)
        crests_sheet()
        sheet()
    if not args or "anim" in args:
        flips = {}
        for cl in CRESTS:
            flips[cl] = crest_flipbook(cl)
            print("flipbook", cl, flush=True)
        preview_idle(flips)
        preview_entrance(flips["Unaffiliated"])
    print("ok", OUT)
