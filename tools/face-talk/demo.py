"""Talking demo GIF + the sheets. python demo.py <outdir> <eyes_dir> <lids_dir>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock as M

CPS = 14.0   # letters per second (about the chat bubble pace)


def visemes(text):
    """text -> [(viseme, seconds)]: the same rules the game would use"""
    t = text.lower()
    out, i = [], 0
    step = 1 / CPS
    while i < len(t):
        c = t[i]
        two = t[i:i + 2]
        if t[i:i + 3] == "...":
            out.append(("rest", 0.6)); i += 3; continue
        if two in ("th",):
            out.append(("L", step)); i += 2; continue
        if two in ("oo", "ou", "ew"):
            out.append(("UW", step * 1.6)); i += 2; continue
        if two in ("ee", "ea"):
            out.append(("E", step * 1.6)); i += 2; continue
        if c in "ai":
            out.append(("AI", step * 1.4))
        elif c == "e":
            out.append(("E", step * 1.3))
        elif c == "o":
            out.append(("O", step * 1.4))
        elif c in "uwq":
            out.append(("UW", step * 1.2))
        elif c == "y":
            out.append(("E" if (i + 1 == len(t) or not t[i + 1].isalpha()) else "CONS", step))
        elif c in "mbp":
            out.append(("MBP", step))
        elif c in "fv":
            out.append(("FV", step))
        elif c == "l":
            out.append(("L", step))
        elif c.isalpha():
            out.append(("CONS", step * 0.8))
        elif c == " ":
            out.append(("rest", step * 0.6))
        elif c in ",;:":
            out.append(("rest", 0.22))
        elif c in ".!?":
            out.append(("rest", 0.32))
        elif c == "'":
            pass
        i += 1
    merged = []
    for v, d in out:
        if merged and merged[-1][0] == v:
            merged[-1] = (v, merged[-1][1] + d * 0.6)
        else:
            merged.append((v, d))
    return merged + [("rest", 0.6)]


LINES = [("neutral", "m", "Hey... you're the new kid, right?"),
         ("happy", "f", "Welcome to Nightmare High!"),
         ("angry", "m", "Get out of my way."),
         ("surprised", "f", "Wait, what?!"),
         ("worried", "m", "I don't think we should be here..."),
         ("smug", "f", "Told you so.")]
FPS = 20
FC = {}


def frame(expr, vis, sex, blink, brow_amt):
    key = (expr, vis, sex, blink, brow_amt)
    if key not in FC:
        FC[key] = M.crop(M.face(expr, vis, sex, blink=1.0 if blink else 0.0, brow_amt=brow_amt, lips=(sex == "f")), scale=0.5)
    return FC[key]


if __name__ == "__main__":
    M.sheets()
    F = M.font(22)
    frames = []
    t_blink = 1.2
    t = 0.0
    for expr, sex, text in LINES:
        seq = visemes(text)
        emph = 1.25 if text.rstrip(".").endswith(("!", "?")) else 1.0
        total = sum(d for _, d in seq)
        clock = 0.0
        for v, d in seq:
            n = max(1, int(round(d * FPS)))
            for k in range(n):
                blink = (t % 2.8) > 2.8 - 0.12
                late = clock > total * 0.55
                img = frame(expr, v, sex, blink, emph if late else 1.0).copy()
                W, H = img.size
                cv = Image.new("RGB", (W, H + 56), (16, 14, 20))
                cv.paste(img, (0, 0))
                d_ = ImageDraw.Draw(cv)
                d_.rounded_rectangle((10, H + 8, W - 10, H + 48), radius=10, fill=(236, 226, 210))
                d_.text((20, H + 16), text, font=F, fill=(30, 20, 28))
                d_.text((W - 120, 8), expr, font=F, fill=(90, 70, 80))
                frames.append(cv)
                t += 1 / FPS
                clock += 1 / FPS
    frames[0].save(os.path.join(M.OUT, "talk_demo.gif"), save_all=True, append_images=frames[1:], duration=int(1000 / FPS), loop=0, optimize=True)
    print("gif frames", len(frames))
