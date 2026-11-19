"""The Ashby House canvases (PBR via posters_hq.save).

  WF_PortraitAshby       old Mrs Ashby in oils, 1890s: a dark varnished ground, a high-collared black dress with a cameo,
                         grey hair in a bun, a long pale face, thin pressed lips, crackle in the varnish. The eye whites are
                         painted; the irises are separate rigged pieces on the prop (they follow you)
  WF_PortraitAshbySmile  the same, smiling: a thin, far-too-wide smile (the game swaps the canvas when you look back)
  WF_Condemned           the council's notice nailed to the door: CONDEMNED, UNSAFE STRUCTURE, KEEP OUT, by order of the
                         Wickfield Building Inspector, 1987, faded and rain-streaked

  python art/hometown/ashby_canvases.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posters_hq as Q  # noqa: E402
H = Q.H
Q.PBR["WF_PortraitAshby"] = dict(rough=0.3, ink_rough=0.35, ink_lift=0.25, strength=3.0)
Q.PBR["WF_PortraitAshbySmile"] = Q.PBR["WF_PortraitAshby"]
Q.PBR["WF_Condemned"] = dict(rough=0.85, ink_rough=0.7, ink_lift=0.15, strength=2.5)

EYES = ((-62, 395), (62, 395))      # eye centres on the 768 x 1024 canvas, relative to x = 384


def portrait(smile=False):
    L = H.Logo("WF_PortraitAshbySmile" if smile else "WF_PortraitAshby", 768, 1024)
    W, Hh, cx = 768, 1024, 384
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, L.rgrad("#4a3a28", "#120c08", cx - 60, 380, 620))       # a warm dark ground, lighter behind the head
    def brush(mask, a, b, seed, scale=6):
        """painterly fill: two tones mixed by directional brush noise"""
        n = Q.noise(L, scale, seed) * 0.5 + 0.5
        st = Q.noise(L, 1.2, seed + 1)
        col = H.rgb(a) * (1 - n[..., None]) + H.rgb(b) * n[..., None]
        col *= (1 + 0.06 * st[..., None])
        L.col = L.col * (1 - mask[..., None]) + col * mask[..., None]
        L.a = np.maximum(L.a, mask)
    # the dress: shoulders and a high collar, a cameo at the throat
    dress = L.poly([(40, 1024), (60, 800), (170, 700), (300, 655), (468, 655), (598, 700), (708, 800), (728, 1024)])
    brush(dress, "#0c0a0c", "#2a2228", 300, 10)
    collar = L.poly([(318, 660), (450, 660), (440, 560), (328, 560)])
    brush(collar, "#141014", "#2e2830", 301, 4)
    for k in range(6):
        L.paint(L.rrect(322, 568 + k * 16, 446, 571 + k * 16, 1), "#3a3238", alpha=0.6)
    cam = L.ellipse(cx, 690, 38, 48)
    L.paint(L.grow(cam, 5), "#b8893a")
    brush(cam, "#e8d8c8", "#c8a890", 302, 3)
    L.paint(L.ellipse(cx + 4, 680, 14, 22), "#d8c0a8")
    # the neck and the face: a long pale oval, painterly shadow down the right side
    neck = L.rrect(cx - 48, 470, cx + 48, 600, 30)
    brush(neck, "#c8a88c", "#8a6a54", 303, 5)
    face = L.ellipse(cx, 390, 125, 160)
    brush(face, "#e2c4a6", "#b08868", 304, 7)
    shadow = np.clip((L.xx / H.SS - (cx + 20)) / 110, 0, 1) * face
    L.col = L.col * (1 - 0.35 * shadow[..., None])
    # the hair: grey, swept up into a bun on top
    hair = np.clip(L.ellipse(cx, 300, 140, 110) - L.ellipse(cx, 360, 118, 120), 0, 1) + L.ellipse(cx, 205, 70, 52)
    brush(np.clip(hair, 0, 1), "#8a8680", "#c8c4bc", 305, 3)
    for k in range(8):                                          # strands
        a_ = math.pi * (0.15 + 0.7 * k / 7)
        L.paint(L.stroke_round([(cx + 125 * math.cos(a_ + math.pi), 330 - 60 * math.sin(a_)), (cx, 250)], 2), "#6a6660", alpha=0.6)
    # the features: hollow eyes (whites painted, the irises are on the prop), a long nose, thin lips
    for dx, ey in EYES:
        sock = L.ellipse(cx + dx, ey, 44, 26)
        L.paint(L.grow(sock, 6), "#8a6450", alpha=0.6)
        L.paint(sock, "#e8e0d0")
        L.paint(np.clip(L.ellipse(cx + dx, ey - 6, 46, 26) - L.ellipse(cx + dx, ey + 8, 46, 28), 0, 1), "#6a4434", alpha=0.85)   # heavy lids
        L.paint(L.stroke_round([(cx + dx - 46, ey - 44), (cx + dx + 40, ey - 52)], 7), "#6a6460")                                # brows
    L.paint(L.stroke_round([(cx + 4, 410), (cx + 10, 470), (cx - 8, 482)], 6), "#9a7058", alpha=0.8)
    if smile:
        mouth = L.m(lambda d, s: d.chord(((cx - 92) * s, 448 * s, (cx + 92) * s, 522 * s), 0, 180, fill=255))
        L.paint(mouth, "#3a1410")
        for k in range(9):                                      # small, even teeth
            L.paint(L.rrect(cx - 72 + k * 16, 486, cx - 60 + k * 16, 499, 3), "#e8dcc4")
        L.paint(L.stroke_round([(cx - 96, 484), (cx - 50, 486), (cx, 487), (cx + 50, 486), (cx + 96, 484)], 4), "#7a3a30")
    else:
        L.paint(L.stroke_round([(cx - 45, 520), (cx, 516), (cx + 45, 520)], 6), "#7a3a30")
    # varnish: yellowed, a crackle network, darker toward the edges
    L.col = L.col * np.array([1.0, 0.94, 0.78], np.float32)
    cr = np.abs(Q.noise(L, 5, 310)) < 0.006
    L.col = np.where(cr[..., None], L.col * 0.86, L.col)
    x, y = L.xx / H.SS / W - 0.5, L.yy / H.SS / Hh - 0.5
    L.col *= (1 - 0.6 * np.clip(np.hypot(x, y) - 0.25, 0, 1))[..., None]
    L.crease_h = cr.astype(np.float32) * 0.8
    Q.save(L, L.name)


def condemned():
    L = H.Logo("WF_Condemned", 768, 1024)
    W, Hh = 768, 1024
    pg = L.rrect(0, 0, W, Hh, 0)
    L.paint(pg, "#f0ead2")
    Q.fibres(L, 320, 0.05)
    L.paint(L.rrect(30, 30, W - 30, 200, 0), "#b8201a")
    L.paint(L.text("CONDEMNED", "georgiab", 82, W / 2, 118, spacing=4), "#f6efe0")
    for t, f, px, y in (("UNSAFE STRUCTURE", "georgiab", 54, 290), ("KEEP OUT", "georgiab", 80, 400), ("This building has been found unfit", "georgia", 30, 520),
                        ("for human occupancy. Entry is", "georgia", 30, 560), ("prohibited by order of the", "georgia", 30, 600),
                        ("Wickfield Building Inspector.", "georgia", 30, 640), ("No. 1987-0413", "georgiab", 30, 760),
                        ("ALSO: PLEASE STOP KNOCKING", "georgiai", 26, 900)):
        L.paint(L.text(t, f, px, W / 2, y, spacing=2), "#1a1612")
    L.paint(L.stroke_round([(200, 830), (260, 800), (330, 840), (420, 800), (520, 830)], 4), "#1a2a6a")   # a signature
    # rain streaks, rust from the nails, fading
    for k in range(18):
        x = 40 + k * 40 + (k * 37) % 23
        L.paint(L.rrect(x, 0, x + 6, Hh, 3), "#9a8a6a", alpha=0.12)
    for x, y in ((50, 50), (W - 50, 50), (50, Hh - 50), (W - 50, Hh - 50)):
        L.paint(L.ellipse(x, y + 30, 14, 60), "#8a4a1a", alpha=0.5)
        L.paint(L.ellipse(x, y, 10), "#3a2a20")
    L.col = L.col * 0.92 + 18
    Q.age_paper(L, 321, folds=(), tape=False)
    Q.save(L, "WF_Condemned")


if __name__ == "__main__":
    portrait(False)
    portrait(True)
    condemned()
