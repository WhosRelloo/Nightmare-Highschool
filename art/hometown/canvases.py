"""Small painted canvases for Wickfield props (art/props/textures/<name>_canvas.png, front-projected by nh_props CANVAS).

  WF_Biscuit     the kennel's name board: "BISCUIT" hand-lettered in white on a red-painted plank, two paw prints
  WF_Mailbox14   the mailbox's side: "14 ALDER LN" in stick-on hardware-store letters
  python art/hometown/canvases.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos"))
import hometown_logos as H  # noqa: E402

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "props", "textures"))


def save(L, name):
    L.name = name
    p = L.save()
    im = Image.open(p).convert("RGB")
    im.save(os.path.join(OUT, f"{name}_canvas.png"))
    print("ok", name)


def biscuit():
    L = H.Logo("WF_Biscuit", 1024, 256)
    board = L.rrect(0, 0, 1024, 256, 6)
    L.paint(board, L.vgrad("#a8382a", "#7c2418", 0, 256))
    L.grain(board, 0.18, 1.0, seed=21)
    for k in range(3):                                      # plank grain lines
        L.paint(L.line([(0, 60 + k * 70 + 6 * (k % 2)), (1024, 66 + k * 70)], 2) * board, "#5e1a10", alpha=0.5)
    word = L.text("BISCUIT", "lucky", 150, 512, 138, spacing=10)
    wob = np.roll(word, 2 * H.SS, 1) * 0.0
    L.paint(word, "#f6efe2")
    L.grain(word, 0.12, 0.6, seed=22)                       # brushy
    for sx in (-1, 1):
        x = 512 + sx * 420
        L.paint(L.ellipse(x, 150, 34, 30), "#f6efe2")
        for k, (dx, dy) in enumerate(((-30, -40), (-10, -58), (12, -58), (32, -40))):
            L.paint(L.ellipse(x + dx, 150 + dy, 11, 14), "#f6efe2")
    # nail heads at the ends
    for x in (24, 1000):
        for y in (40, 216):
            L.paint(L.ellipse(x, y, 7), "#3a3430")
    save(L, "WF_Biscuit")


def mailbox():
    L = H.Logo("WF_Mailbox14", 1024, 384)
    plate = L.rrect(0, 0, 1024, 384, 4)
    L.paint(plate, L.vgrad("#2e4a6e", "#1e3352", 0, 384))     # the box's navy enamel
    L.grain(plate, 0.05, 1.5, seed=23)
    for t, px, y, sp in (("14", 190, 150, 12), ("ALDER LN", 96, 300, 10)):
        m = L.text(t, "georgiab", px, 512, y, spacing=sp)
        L.paint(L.grow(m, 5), "#111111", alpha=0.6)
        L.paint(m, L.vgrad("#fff2c0", "#d8a840", y - px / 2, y + px / 2))
        L.shade(m, strength=0.4, blur=1.5)
    save(L, "WF_Mailbox14")


def pennant():
    """a felt Wicks pennant: green triangle, gold edge, the candle mascot and WICKS"""
    L = H.Logo("WF_Pennant", 1024, 384)
    tri = L.poly([(0, 0), (1024, 192), (0, 384)])
    L.paint(L.rrect(0, 0, 1024, 384, 0), "#3a2a20")                     # the wall behind shows at the tip (cropped later)
    L.paint(tri, L.vgrad("#2f6b47", "#1a3d29", 0, 384))
    L.grain(tri, 0.1, 0.8, seed=31)
    L.paint(L.rrect(0, 0, 90, 384, 0), "#e3b23c")
    word = L.text("WICKS", "lucky", 150, 470, 200, spacing=8)
    L.paint(L.grow(word, 6), "#14110f")
    L.paint(word, "#f4ead2")
    fl = L.poly([(190, 90), (230, 170), (190, 210), (150, 170)])
    L.paint(L.grow(fl, 4), "#14110f")
    L.paint(fl, "#f0a032")
    L.paint(L.rrect(160, 210, 220, 300, 6), "#f4ead2")
    save(L, "WF_Pennant")


def band_poster():
    """THE GRAVEYARD SHIFT, live at the Grange Hall: a screen-printed gig poster, two colours on cream"""
    L = H.Logo("WF_PosterBand", 512, 768)
    pg = L.rrect(0, 0, 512, 768, 0)
    L.paint(pg, "#efe4cc")
    L.grain(pg, 0.08, 1.0, seed=32)
    moon = L.ellipse(256, 300, 170)
    L.paint(moon, "#e86a3a")
    # a guitar headstock silhouette against the moon, a row of headstones below
    neck = L.poly([(240, 520), (272, 520), (282, 170), (230, 170)])
    head = L.poly([(222, 175), (290, 175), (300, 100), (256, 70), (212, 100)])
    L.paint(np.clip(neck + head, 0, 1), "#2a1e2e")
    for k in range(6):
        for sx in (-1, 1):
            L.paint(L.ellipse(256 + sx * 52, 110 + k * 14, 8, 5), "#efe4cc")
    for i, x in enumerate(range(40, 500, 72)):
        hgt = 50 + (i % 3) * 18
        L.paint(L.rrect(x, 560 - hgt, x + 46, 560, 20), "#2a1e2e")
    L.paint(L.rrect(0, 556, 512, 768, 0), "#2a1e2e")
    for t, f, px, y in (("THE GRAVEYARD", "lucky", 56, 610), ("SHIFT", "lucky", 70, 668), ("LIVE AT THE GRANGE HALL  ·  SAT 9PM", "georgiab", 18, 728)):
        L.paint(L.text(t, f, px, 256, y, spacing=3), "#efe4cc")
    save(L, "WF_PosterBand")


def moon_poster():
    """a lunar calendar: eight moon phases on navy, gold type"""
    L = H.Logo("WF_PosterMoon", 512, 768)
    pg = L.rrect(0, 0, 512, 768, 0)
    L.paint(pg, L.vgrad("#1c2448", "#0c1024", 0, 768))
    rng = np.random.default_rng(33)
    for _ in range(140):
        x, y, r = rng.uniform(0, 512), rng.uniform(0, 768), rng.uniform(0.6, 2.2)
        L.paint(L.ellipse(x, y, r), "#f4ecd0", alpha=rng.uniform(0.4, 1))
    L.paint(L.text("LUNAR", "georgiab", 64, 256, 90, spacing=10), "#e3c272")
    L.paint(L.text("CALENDAR", "georgia", 30, 256, 140, spacing=8), "#e3c272")
    for i in range(8):
        cx, cy = 150 + (i % 2) * 212, 230 + (i // 2) * 130
        disc = L.ellipse(cx, cy, 50)
        L.paint(disc, "#2a3258")
        ph = i / 8.0
        nx = (L.xx / H.SS - cx) / 50.0
        ny = (L.yy / H.SS - cy) / 50.0
        edge = np.sqrt(np.clip(1 - ny ** 2, 0, 1))
        c_ = math.cos(2 * math.pi * ph)
        if ph <= 0.5:
            side = nx > c_ * edge
        else:
            side = nx < -c_ * edge
        lit = disc * side.astype(np.float32)
        L.paint(lit, L.rgrad("#fff6dc", "#d8c9a0", cx - 15, cy - 15, 60))
        L.paint(np.clip(L.ellipse(cx, cy, 52) - disc, 0, 1), "#e3c272", alpha=0.7)
    save(L, "WF_PosterMoon")


def clock():
    """the alarm clock's face: red LED 11:58, a little PM dot and the alarm bell icon"""
    L = H.Logo("WF_Clock1158", 512, 256)
    pg = L.rrect(0, 0, 512, 256, 20)
    L.paint(pg, "#0a0808")
    L.glow(L.text("11:58", "lucky", 170, 250, 136, spacing=10), "#ff2a1a", 16, 0.6)
    L.paint(L.text("11:58", "lucky", 170, 250, 136, spacing=10), "#ff3a22")
    L.paint(L.ellipse(470, 190, 10), "#ff3a22")
    L.paint(L.text("PM", "georgiab", 22, 470, 160), "#a02018")
    save(L, "WF_Clock1158")


if __name__ == "__main__":
    import math
    globals()["math"] = math
    names = sys.argv[1:]
    for fn in (biscuit, mailbox, pennant, band_poster, moon_poster, clock):
        if not names or fn.__name__ in names:
            fn()
