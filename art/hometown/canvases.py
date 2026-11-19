"""Small painted canvases for Wickfield props (art/props/textures/<name>_canvas.png, front-projected by nh_props CANVAS).

  WF_Biscuit     the kennel's name board: "BISCUIT" hand-lettered in white on a red-painted plank, two paw prints
  WF_Mailbox14   the mailbox's side: "14 ALDER LN" in stick-on hardware-store letters
  python art/hometown/canvases.py
"""
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


if __name__ == "__main__":
    biscuit()
    mailbox()
