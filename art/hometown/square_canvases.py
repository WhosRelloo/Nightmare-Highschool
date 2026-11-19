"""Wickfield Square canvases (PBR, via posters_hq.save): the church clock's dial.

  WF_ClockDial   cream enamel, a gilt chapter ring, black Roman numerals, minute ticks, "WICKFIELD · 1851"
  python art/hometown/square_canvases.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posters_hq as Q  # noqa: E402
H = Q.H
Q.PBR["WF_ClockDial"] = dict(rough=0.25, ink_rough=0.35, ink_lift=0.25, strength=3.0, gilt=True)


def dial():
    L = H.Logo("WF_ClockDial", 1024, 1024)
    c = 512
    L.paint(L.rrect(0, 0, 1024, 1024, 0), "#2a2622")                    # the stone behind (cropped by the round mesh)
    L.paint(L.ellipse(c, c, 505), L.vgrad("#f4d892", "#9a7432", 0, 1024))
    L.shade(np.clip(L.ellipse(c, c, 505) - L.ellipse(c, c, 470), 0, 1), strength=0.5, blur=4)
    face = L.ellipse(c, c, 470)
    L.paint(face, L.rgrad("#fbf5e6", "#e8dcc0", c - 80, c - 80, 520))
    L.col *= (1 + 0.03 * Q.noise(L, 30, 300)[..., None] * face[..., None])
    for r_, w_ in ((430, 3), (380, 3)):                                  # the chapter ring
        L.paint(np.clip(L.ellipse(c, c, r_ + w_) - L.ellipse(c, c, r_ - w_), 0, 1), "#1a1612")
    for k in range(60):
        a = 2 * math.pi * k / 60
        r0, r1 = (382, 428) if k % 5 == 0 else (400, 428)
        L.paint(L.stroke_round([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + r1 * math.sin(a), c - r1 * math.cos(a))], 7 if k % 5 == 0 else 3), "#1a1612")
    numerals = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for k, n in enumerate(numerals):
        a = 2 * math.pi * k / 12
        x, y = c + 320 * math.sin(a), c - 320 * math.cos(a)
        g = L.text(n, "georgiab", 64, 0, 0)
        # draw each numeral upright at its place (simple: text centred at the point)
        L.paint(L.text(n, "georgiab", 60, x, y), "#1a1612")
    L.paint(L.text("WICKFIELD", "georgiab", 34, c, c - 150, spacing=8), "#1a1612")
    L.paint(L.text("1851", "georgiab", 30, c, c + 150, spacing=8), "#1a1612")
    L.paint(L.ellipse(c, c, 30), L.vgrad("#f4d892", "#9a7432", c - 30, c + 30))
    Q.save(L, "WF_ClockDial")


Q.PBR["WF_ThePlan"] = dict(rough=0.85, ink_rough=0.6, ink_lift=0.35, strength=3.0)


def the_plan():
    """THE PLAN: lined notebook paper torn from a spiral pad, marker doodles of the five pranks, numbered, a big title,
    'tonight. 12:00. DON'T get caught.' Taped to a lamp post in the square"""
    L = H.Logo("WF_ThePlan", 1024, 1408)
    W, Hh = 1024, 1408
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#f6f2e6")
    Q.fibres(L, 400, 0.04)
    for y in range(160, Hh - 20, 44):                                   # the blue rules and the red margin
        L.paint(L.rrect(0, y, W, y + 2, 0), "#9cb8d8", alpha=0.7)
    L.paint(L.rrect(110, 0, 113, Hh, 0), "#e07a7a", alpha=0.8)
    for k in range(14):                                                  # the torn spiral edge
        L.paint(L.ellipse(40 + k * 72, 18, 12, 10), "#d8d2c0")
    INK = "#1a1a24"

    def marker(pts, w=7, col=INK, seed=0):
        m = L.stroke_round(pts, w)
        L.paint(m * (Q.noise(L, 0.5, seed) > -0.5), col, alpha=0.95)
    L.paint(L.text("THE PLAN", "lucky", 120, W / 2 + 40, 95, spacing=6), INK)
    marker([(300, 150), (840, 150)], 8, "#c8201a", 401)
    cells = [(310, 330), (720, 330), (310, 720), (720, 720), (515, 1000)]
    labels = ["HALL OF FAME", "THE STATUE", "CHET'S TRUCK", "THE PUMA", "ASHBY HOUSE"]
    for i, ((cx, cy), lab) in enumerate(zip(cells, labels)):
        L.paint(L.text(str(i + 1), "lucky", 54, cx - 160, cy - 140), "#c8201a")
        L.paint(L.text(lab, "chela", 36, cx + 10, cy + 150), INK)
        if i == 0:     # the hall-of-fame board with a name crossed out and "ME" written over it
            marker([(cx - 120, cy - 90), (cx + 120, cy - 90), (cx + 120, cy + 80), (cx - 120, cy + 80), (cx - 120, cy - 90)], 6, INK, 410)
            for k in range(4):
                marker([(cx - 90, cy - 50 + k * 34), (cx + 60, cy - 50 + k * 34)], 4, INK, 411 + k)
            marker([(cx - 95, cy - 50), (cx + 70, cy - 30)], 6, "#c8201a", 415)
            L.paint(L.text("ME!!", "chela", 40, cx + 80, cy - 60), "#c8201a")
        if i == 1:     # a stick-figure horse and rider with a cone on his head
            marker([(cx - 90, cy + 70), (cx - 70, cy), (cx + 60, cy), (cx + 80, cy + 70)], 6, INK, 420)
            marker([(cx + 60, cy), (cx + 100, cy - 50), (cx + 125, cy - 40)], 6, INK, 421)
            marker([(cx, cy), (cx, cy - 80)], 6, INK, 422)
            L.paint(L.ellipse(cx, cy - 100, 20), INK)
            L.paint(L.poly([(cx - 22, cy - 115), (cx + 22, cy - 115), (cx, cy - 175)]), "#f07a1a")
            marker([(cx - 40, cy - 60), (cx - 80, cy - 130)], 5, INK, 423)
            for k in range(3):
                marker([(cx - 80 + k * 40, cy - 130), (cx - 60 + k * 30, cy + 40)], 3, "#9a9a9a", 424 + k)
        if i == 2:     # a pickup truck, flat tyres, a goose looking furious
            marker([(cx - 130, cy + 30), (cx - 130, cy - 20), (cx - 40, cy - 20), (cx - 20, cy - 70), (cx + 40, cy - 70), (cx + 60, cy - 20),
                    (cx + 130, cy - 20), (cx + 130, cy + 30), (cx - 130, cy + 30)], 6, INK, 430)
            for x in (cx - 80, cx + 80):
                L.paint(L.ellipse(x, cy + 45, 28, 16), INK)
            marker([(cx + 150, cy + 60), (cx + 150, cy - 10), (cx + 175, cy - 40)], 6, INK, 431)
            L.paint(L.ellipse(cx + 150, cy + 70, 30, 20), INK)
            marker([(cx + 170, cy - 45), (cx + 200, cy - 48)], 5, "#f07a1a", 432)
            L.paint(L.text("!!", "lucky", 40, cx + 200, cy - 90), "#c8201a")
        if i == 3:     # the puma mascot head, with a big arrow "GRAB"
            L.paint(np.clip(L.ellipse(cx, cy, 80) - L.ellipse(cx, cy, 72), 0, 1), INK)
            for sx in (-1, 1):
                marker([(cx + sx * 50, cy - 60), (cx + sx * 70, cy - 110), (cx + sx * 20, cy - 75)], 6, INK, 440 + sx)
                L.paint(L.ellipse(cx + sx * 28, cy - 15, 9), INK)
            marker([(cx - 30, cy + 35), (cx, cy + 50), (cx + 30, cy + 35)], 5, INK, 443)
            marker([(cx - 180, cy + 110), (cx - 90, cy + 60)], 6, "#c8201a", 444)
            L.paint(L.text("GRAB", "chela", 32, cx - 170, cy + 140), "#c8201a")
        if i == 4:     # a crooked house with a spooky face in the window and a ghost doodle
            marker([(cx - 110, cy + 80), (cx - 110, cy - 30), (cx - 10, cy - 120), (cx + 100, cy - 25), (cx + 110, cy + 80), (cx - 110, cy + 80)], 6, INK, 450)
            L.paint(L.rrect(cx - 30, cy - 10, cx + 30, cy + 50, 4), INK)
            for sx in (-1, 1):
                L.paint(L.ellipse(cx + sx * 12, cy + 10, 5), "#f6f2e6")
            marker([(cx + 150, cy - 60), (cx + 140, cy - 120), (cx + 180, cy - 140), (cx + 210, cy - 100), (cx + 200, cy - 50), (cx + 185, cy - 65), (cx + 170, cy - 48), (cx + 150, cy - 60)], 5, INK, 451)
            L.paint(L.text("??", "lucky", 40, cx + 250, cy - 110), INK)
    L.paint(L.text("tonight.  12:00.", "chela", 54, W / 2 + 40, Hh - 150), INK)
    L.paint(L.text("DON'T get caught.", "chela", 54, W / 2 + 40, Hh - 85), "#c8201a")
    marker([(390, Hh - 60), (660, Hh - 56)], 5, "#c8201a", 460)
    Q.age_paper(L, 470, folds=((0.5, "h"), (0.5, "v")), tape=True)
    Q.save(L, "WF_ThePlan")


if __name__ == "__main__":
    import sys as _s
    want = _s.argv[1:]
    for fn in (dial, the_plan):
        if not want or fn.__name__ in want:
            fn()
