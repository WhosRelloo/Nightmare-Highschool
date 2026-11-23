"""The Evidence Wall: concept art for the redesigned investigation board (Nightmare Highschool).

Design: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md, section "The Evidence Wall".
Same PBR shader as Thornrose / the Bell Tower / Quiet Corners (make_health_pbr.py, helpers from make_quietcorners.py).
Production resolution 2x design px, at most 2048 a side. No words are baked into any piece: every word is live text.

Pieces (art/ui/hud/out/evidence/):
  Wall.png              2048x1152  cork board in a blackened-iron frame with brass trim and corner rosettes
                                   (concept; in game it's WallFrame 9-slice + a Cork tile, split from this bake)
  Cork.png               512x512   the cork, tileable
  CasePlate<Race>.png   1600x200   the plate the case's big question is engraved on (trim metal face, iron rim)
  CardPhoto.png          440x600   a photograph clue (live photo shows through the window), caption strip below
  CardNote.png           440x600   a torn notebook page
  CardRecord.png         440x600   an index card from the school records
  CardObject.png         440x600   a manila evidence tag with a brass eyelet
  CardMissing.png        440x600   chalk outline of a clue not found yet (greyscale; tinted chalk)
  Tack<Race>.png          96x96    push pin: a glass head in the race's gem colour on a trim collar
  Thread.png             512x24    greyscale twisted thread (tinted danger crimson, tiled and rotated in game)
  Slot.png               440x600   iron bracket corners where a clue is pinned to a question
  QuestionSheet.png     1440x560   the ruled sheet each small question is written on
  AnswerCard<Race>.png   720x360   a final-answer card with trim corners
  Lens<Race>.png         640x640   a magnifier that floats over the card you are reading
  StampInk.png           640x240   greyscale rubber-stamp frame (tinted crimson; the word inside is live)
  _sheet.png

  python make_evidence_wall.py
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import make_health_pbr as P
import make_quietcorners as Q
from make_quietcorners import Layers, disc, dist, grid, mix, noise, rrect, ring, soft, trim_mat, iron_mat

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
Q.OUT = OUT   # Q.save writes here

RACES = Q.RACES


def save(rgb, a, name):
    return Q.save(rgb, a, name)


def cork_mat(W, H, seed=0):
    """Procedural cork: granules of three sizes, dark flecks, old pin holes."""
    g1 = noise(W, H, 1.0, 300 + seed)
    g2 = noise(W, H, 2.6, 301 + seed)
    g3 = noise(W, H, 9.0, 302 + seed)
    Hf = 0.22 + 0.025 * g1 + 0.03 * g2 + 0.02 * g3
    base = P.srgb_to_lin(np.array([0.5, 0.33, 0.19], np.float32))
    v = 0.78 + 0.18 * g2 + 0.1 * g1 + 0.12 * g3
    col = base * v[..., None]
    fleck = np.clip(g1 * 3 - 2.2, 0, 1)
    col = mix(col, base * 0.35, fleck)
    rng = np.random.default_rng(310 + seed)
    holes = np.zeros((H, W), np.float32)
    YY, XX = grid(W, H)
    for _ in range(int(W * H / 9000)):
        cx, cy = rng.uniform(0, W), rng.uniform(0, H)
        y0, y1, x0, x1 = int(max(cy - 3, 0)), int(min(cy + 4, H)), int(max(cx - 3, 0)), int(min(cx + 4, W))
        holes[y0:y1, x0:x1] = np.maximum(holes[y0:y1, x0:x1], (np.hypot(XX[y0:y1, x0:x1] - cx, YY[y0:y1, x0:x1] - cy) < 1.8))
    col = mix(col, base * 0.18, holes)
    Hf -= holes * 0.04
    nrm = np.zeros((H, W, 3), np.float32)
    nrm[..., 2] = 1
    return (col, nrm, np.full((H, W), 0.92, np.float32), np.zeros((H, W), np.float32)), Hf


def cork_tile():
    S = 512
    L = Layers(S, S)
    mat, Hf = cork_mat(S, S, 7)
    # make it tile: blend with a half-shifted copy across the seams
    YY, XX = grid(S, S)
    w = np.minimum(np.minimum(XX, S - 1 - XX), np.minimum(YY, S - 1 - YY)) / 40
    w = np.clip(w, 0, 1)
    sh = lambda a: np.roll(np.roll(a, S // 2, 0), S // 2, 1)
    col = mix(sh(mat[0]), mat[0], w)
    Hf = sh(Hf) * (1 - w) + Hf * w
    L.paint(np.ones((S, S), np.float32), (col,) + mat[1:], Hf)
    save(L.render(14.0, 0.0, ao=(2, 3.0)), L.alpha, "Cork.png")


def wall(race="Human"):
    W, H = 2048, 1152
    YY, XX = grid(W, H)
    L = Layers(W, H)
    F = 64
    board = rrect(W, H, F, F, W - F, H - F, 6)
    mat, Hf = cork_mat(W, H, 1)
    L.paint(np.ones((H, W), np.float32) * board, mat, Hf)
    # inner shadow of the frame on the cork
    inner = np.clip(1 - dist(board) / 40, 0, 1) ** 2 * board
    L.alb *= (1 - inner[..., None] * 0.6)
    iron = iron_mat(W, H, 300)
    frame = np.clip(rrect(W, H, 0, 0, W, H, 18) - board, 0, 1)
    fd = dist(frame)
    L.paint(frame, iron, 0.45 + 0.2 * P.dome(fd, 26), 0.9)
    tm = trim_mat(race, W, H, 300)
    for a, b in ((8, 16), (F - 16, F - 8)):
        bead = np.clip(rrect(W, H, a, a, W - a, H - a, 14) - rrect(W, H, b, b, W - b, H - b, 10), 0, 1)
        L.paint(bead, tm, 0.7 + 0.15 * P.dome(dist(bead), 4) + tm[4])
    for cx, cy in ((F / 2, F / 2), (W - F / 2, F / 2), (F / 2, H - F / 2), (W - F / 2, H - F / 2)):
        ro = disc(W, H, cx, cy, 40)
        petals = soft((0.5 + 0.5 * np.cos(np.arctan2(YY - cy, XX - cx) * 8)) * ro > 0.35, 0.8) * ro
        L.paint(ro, iron, 0.75 + 0.2 * P.dome(dist(ro), 14))
        L.paint(petals, tm, 0.85 + 0.15 * P.dome(dist(petals), 5))
        L.gem(race, disc(W, H, cx, cy, 13))
    rgb = L.render(18.0, 0.15, ao=(6, 2.0))
    save(rgb, L.alpha, "Wall.png" if race == "Human" else f"Wall{race}.png")


def case_plate(race):
    W, H = 1600, 200
    L = Layers(W, H)
    iron = iron_mat(W, H, 260)
    tm = trim_mat(race, W, H, 320)
    body = Q.P.polymask((W, H), [[(40, 6), (W - 40, 6), (W - 6, H / 2), (W - 40, H - 6), (40, H - 6), (6, H / 2)]])
    face = Q.P.polymask((W, H), [[(64, 26), (W - 64, 26), (W - 30, H / 2), (W - 64, H - 26), (64, H - 26), (30, H / 2)]])
    L.paint(body, iron, 0.4 + 0.15 * P.dome(dist(body), 18), 0.9)
    L.paint(face, tm, 0.62 + 0.04 * P.dome(dist(face), 30) + tm[4])
    L.rough = mix(L.rough, np.clip(L.rough * 0.8, 0.04, 1), face)            # brushed, a little brighter
    for x in (88, W - 88):
        sc = disc(W, H, x, H / 2, 16)
        L.paint(sc, iron, 0.9 + 0.2 * P.dome(dist(sc), 10))
        YY, XX = grid(W, H)
        slot = soft((np.abs((XX - x) - (YY - H / 2)) < 2.5) & (np.hypot(XX - x, YY - H / 2) < 12), 0.5)
        L.Hf -= slot * 0.08
    rgb = L.render(20.0, 0.3)
    sh = soft(np.roll(body, 8, 0), 7) * 0.6
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    save(rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a, f"CasePlate{race}.png")


def _card_out(L, shape, name, emboss=16.0):
    rgb = L.render(emboss)
    sh = soft(np.roll(np.roll(shape, 10, 0), 6, 1), 9) * 0.65
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    save(rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a, name)


def card_photo():
    W, H = 440, 600
    L = Layers(W, H)
    YY, XX = grid(W, H)
    shape = rrect(W, H, 8, 8, W - 8, H - 8, 4)
    pap = Q.paper_mat("Priest", W, H, 260, seed=5)                   # bright photo-card stock
    win = rrect(W, H, 30, 30, W - 30, 380, 2)
    L.paint(shape, pap, 0.3 + noise(W, H, 6, 3) * 0.006)
    L.Hf -= win * 0.04
    rgb = L.render(14.0)
    alpha = np.clip(L.alpha - win, 0, 1)                             # the live photo shows through
    gloss = np.clip(1 - np.abs((XX - YY * 0.6) - 120) / 70, 0, 1) * win * 0.12
    rgb = mix(rgb, np.ones_like(rgb), gloss)
    alpha = np.maximum(alpha, gloss)
    sh = soft(np.roll(np.roll(shape, 10, 0), 6, 1), 9) * 0.65 * (1 - win)
    a = np.clip(alpha + sh * (1 - alpha), 0, 1)
    save(rgb * (alpha / np.maximum(a, 1e-4))[..., None], a, "CardPhoto.png")


def card_note():
    W, H = 440, 600
    L = Layers(W, H)
    YY, XX = grid(W, H)
    torn = 18 + 6 * noise(W, H, 3, 8)[0] * 3
    shape = ((YY > torn[None, :]) & (XX > 10) & (XX < W - 10) & (YY < H - 10)).astype(np.float32)
    shape = soft(shape, 0.6)
    pap = Q.paper_mat("Human", W, H, 260, seed=9)
    L.paint(shape, pap, 0.3 + noise(W, H, 10, 4) * 0.01)
    lines = ((((YY - 70) % 40) < 1.6) & (YY > 70)).astype(np.float32)
    margin = (np.abs(XX - 64) < 1.4).astype(np.float32)
    L.alb = mix(L.alb, np.array([0.22, 0.32, 0.6]), soft(lines, 0.5) * 0.35 * shape)
    L.alb = mix(L.alb, np.array([0.55, 0.05, 0.06]), soft(margin, 0.5) * 0.6 * shape)
    _card_out(L, shape, "CardNote.png")


def card_record():
    W, H = 440, 600
    L = Layers(W, H)
    YY, XX = grid(W, H)
    shape = Q.P.polymask((W, H), [[(10, 10), (W - 60, 10), (W - 10, 60), (W - 10, H - 10), (10, H - 10)]])
    pap = Q.paper_mat("Werewolf", W, H, 260, seed=11)
    L.paint(shape, pap, 0.3)
    head = ((np.abs(YY - 96) < 2.0) & (XX > 24) & (XX < W - 24)).astype(np.float32)
    lines = ((((YY - 136) % 38) < 1.3) & (YY > 136) & (XX > 24) & (XX < W - 24)).astype(np.float32)
    L.alb = mix(L.alb, np.array([0.5, 0.04, 0.05]), soft(head, 0.5) * 0.75 * shape)
    L.alb = mix(L.alb, np.array([0.2, 0.3, 0.55]), soft(lines, 0.5) * 0.28 * shape)
    _card_out(L, shape, "CardRecord.png")


def card_object():
    W, H = 440, 600
    L = Layers(W, H)
    shape = Q.P.polymask((W, H), [[(80, 10), (W - 80, 10), (W - 10, 80), (W - 10, H - 10), (10, H - 10), (10, 80)]])
    man = Q.paper_mat("Werewolf", W, H, 220, seed=13)
    man = (man[0] * np.array([1.05, 0.9, 0.62]),) + man[1:]
    hole = disc(W, H, W / 2, 64, 14)
    L.paint(shape, man, 0.32)
    tm = trim_mat("Human", W, H, 120)
    eye = ring(W, H, W / 2, 64, 14, 26)
    L.paint(eye, tm, 0.6 + 0.3 * P.dome(dist(eye), 5))
    rgb = L.render(16.0)
    al = np.clip(L.alpha - hole, 0, 1)
    sh = soft(np.roll(np.roll(shape, 10, 0), 6, 1), 9) * 0.65 * (1 - hole)
    a = np.clip(al + sh * (1 - al), 0, 1)
    save(rgb * (al / np.maximum(a, 1e-4))[..., None], a, "CardObject.png")


def card_missing():
    W, H = 440, 600
    YY, XX = grid(W, H)
    box = np.clip(rrect(W, H, 16, 16, W - 16, H - 16, 8) - rrect(W, H, 22, 22, W - 22, H - 22, 6), 0, 1)
    per = ((XX + YY).astype(int) // 26) % 2 == 0
    grit = np.clip(0.55 + noise(W, H, 0.8, 40) * 0.6, 0, 1)
    a = box * per * grit
    smudge = rrect(W, H, 30, 30, W - 30, H - 30, 8) * np.clip(0.06 + noise(W, H, 18, 41) * 0.05, 0, 1)
    Q.save_grey(np.full((H, W), 0.95, np.float32), np.clip(a + smudge, 0, 1), "CardMissing.png")


def tack(race):
    S = 96
    L = Layers(S, S)
    tm = trim_mat(race, S, S, 96)
    col = disc(S, S, S / 2, S / 2, 30)
    L.paint(col, tm, 0.5 + 0.2 * P.dome(dist(col), 8) + tm[4])
    L.gem(race, disc(S, S, S / 2 - 2, S / 2 - 3, 22))
    rgb = L.render(16.0)
    sh = soft(np.roll(np.roll(disc(S, S, S / 2, S / 2, 28), 7, 0), 5, 1), 4) * 0.6
    a = np.clip(L.alpha + sh * (1 - L.alpha), 0, 1)
    save(rgb * (L.alpha / np.maximum(a, 1e-4))[..., None], a, f"Tack{race}.png")


def thread():
    W, H = 512, 24
    YY, XX = grid(W, H)
    twist = 0.5 + 0.5 * np.cos((XX * 0.35) + (YY - H / 2) * 0.9)
    body = soft(np.abs(YY - H / 2) <= 4.5, 0.8)
    v = 0.55 + 0.45 * twist
    Q.save_grey(v.astype(np.float32), body, "Thread.png")


def slot():
    W, H = 440, 600
    L = Layers(W, H)
    iron = iron_mat(W, H, 200)
    br = np.zeros((H, W), np.float32)
    for (x, y, sx, sy) in ((14, 14, 1, 1), (W - 14, 14, -1, 1), (14, H - 14, 1, -1), (W - 14, H - 14, -1, -1)):
        arm1 = Q.P.polymask((W, H), [[(x, y), (x + sx * 90, y), (x + sx * 90, y + sy * 16), (x, y + sy * 16)]])
        arm2 = Q.P.polymask((W, H), [[(x, y), (x + sx * 16, y), (x + sx * 16, y + sy * 90), (x, y + sy * 90)]])
        br = np.maximum(br, np.maximum(arm1, arm2))
    L.paint(br, iron, 0.55 + 0.2 * P.dome(dist(br), 6), 1.1)
    tm = trim_mat("Human", W, H, 160)
    for (x, y) in ((30, 30), (W - 30, 30), (30, H - 30), (W - 30, H - 30)):
        r = disc(W, H, x, y, 6)
        L.paint(r, tm, 0.85 + 0.2 * P.dome(dist(r), 4))
    rgb = L.render(18.0)
    # a faint chalked well inside, so an empty slot reads as "put a clue here"
    well = rrect(W, H, 36, 36, W - 36, H - 36, 10) * 0.16
    a = np.maximum(L.alpha, well)
    rgb = mix(np.full_like(rgb, 0.85), rgb, L.alpha / np.maximum(a, 1e-4))
    save(rgb, a, "Slot.png")


def question_sheet():
    W, H = 1440, 560
    L = Layers(W, H)
    YY, XX = grid(W, H)
    m = Q.deckle(W, H, 10, 77, 2.0)
    pap = Q.paper_mat("Human", W, H, 360, seed=21)
    L.paint(m, pap, 0.28 + noise(W, H, 14, 5) * 0.01)
    rule = ((np.abs(YY - 112) < 1.6) & (XX > 40) & (XX < W - 40)).astype(np.float32)
    L.alb = mix(L.alb, np.array([0.42, 0.04, 0.05]), soft(rule, 0.5) * 0.7)
    edge = np.clip(1 - dist(m) / 18, 0, 1) * m
    L.alb = mix(L.alb, L.alb * np.array([0.55, 0.38, 0.22]), edge * 0.6)
    _card_out(L, m, "QuestionSheet.png", 14.0)


def answer_card(race):
    W, H = 720, 360
    L = Layers(W, H)
    shape = rrect(W, H, 10, 10, W - 10, H - 10, 10)
    L.paint(shape, Q.paper_mat(race, W, H, 300, seed=31), 0.3)
    tm = trim_mat(race, W, H, 200)
    for (x, y, sx, sy) in ((10, 10, 1, 1), (W - 10, 10, -1, 1), (10, H - 10, 1, -1), (W - 10, H - 10, -1, -1)):
        tri = Q.P.polymask((W, H), [[(x, y), (x + sx * 70, y), (x, y + sy * 70)]]) * shape
        L.paint(tri, tm, 0.6 + 0.2 * P.dome(dist(tri), 8) + tm[4])
    _card_out(L, shape, f"AnswerCard{race}.png")


def lens(race):
    S = 640
    L = Layers(S, S)
    YY, XX = grid(S, S)
    cx, cy, r = 260, 260, 220
    tm = trim_mat(race, S, S, 260)
    rim = ring(S, S, cx, cy, r - 18, r + 6)
    handle = Q.P.polymask((S, S), [[(cx + 150, cy + 175), (cx + 175, cy + 150), (S - 20, S - 60), (S - 60, S - 20)]])
    lea = P.material("Leather", (S, S), 200, tint=(0.12, 0.05, 0.04), rough_mul=0.8)
    L.paint(handle, lea, 0.5 + 0.3 * P.dome(dist(handle), 14))
    L.paint(rim, tm, 0.7 + 0.25 * P.dome(dist(rim), 10) + tm[4])
    rgb = L.render(20.0)
    glass = disc(S, S, cx, cy, r - 18)
    hl = np.clip(1 - np.hypot(XX - (cx - 90), YY - (cy - 100)) / 120, 0, 1) ** 2 * 0.5
    a = np.maximum(L.alpha, glass * 0.08 + hl * glass)
    rgb = mix(np.ones_like(rgb), rgb, L.alpha / np.maximum(a, 1e-4))
    save(rgb, a, f"Lens{race}.png")


def stamp_ink():
    W, H = 640, 240
    YY, XX = grid(W, H)
    outer = np.clip(rrect(W, H, 12, 12, W - 12, H - 12, 16) - rrect(W, H, 26, 26, W - 26, H - 26, 10), 0, 1)
    inner = np.clip(rrect(W, H, 36, 36, W - 36, H - 36, 8) - rrect(W, H, 42, 42, W - 42, H - 42, 6), 0, 1)
    ink = np.clip(noise(W, H, 1.2, 50) * 1.4 + 0.75, 0, 1) * np.clip(noise(W, H, 14, 51) * 1.2 + 0.8, 0, 1)
    Q.save_grey(np.full((H, W), 0.95, np.float32), np.clip((outer + inner) * ink, 0, 1), "StampInk.png")


def sheet():
    names = ["Wall", "CasePlateHuman", "CardPhoto", "CardNote", "CardRecord", "CardObject", "CardMissing", "Slot",
             "QuestionSheet", "AnswerCardHuman", "LensHuman", "StampInk", "TackHuman", "Thread"]
    Wd = 2000
    canvas = Image.new("RGBA", (Wd, 4000), (40, 30, 26, 255))
    x = y = 16
    rh = 0
    for n in names:
        im = Image.open(OUT / f"{n}.png")
        im.thumbnail((900, 520) if n in ("Wall", "QuestionSheet", "CasePlateHuman") else (300, 300))
        if x + im.width > Wd:
            x, y, rh = 16, y + rh + 16, 0
        canvas.alpha_composite(im, (x, y))
        x += im.width + 16
        rh = max(rh, im.height)
    canvas.crop((0, 0, Wd, y + rh + 16)).save(OUT / "_sheet.png")


if __name__ == "__main__":
    cork_tile()
    wall("Human")
    for r in RACES:
        case_plate(r)
        tack(r)
        answer_card(r)
        lens(r)
        print("race", r, flush=True)
    card_photo()
    card_note()
    card_record()
    card_object()
    card_missing()
    thread()
    slot()
    question_sheet()
    stamp_ink()
    sheet()
    print("ok", OUT)
