"""Builds renders/compare_sheet.png (Standard | Current | New, front / side / back) and renders/uv_check.png."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

R = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/femalebody/renders"
try:
    F = ImageFont.truetype("georgiab.ttf", 34); f2 = ImageFont.truetype("georgia.ttf", 24)
except OSError:
    F = f2 = ImageFont.load_default()


def sheet(cols, views, name, title, sub=None):
    tiles = [[Image.open(os.path.join(R, f"{c}_{v}.png")).convert("RGB") if os.path.exists(os.path.join(R, f"{c}_{v}.png")) else None
              for v in views] for c, _ in cols]
    w, h = 700, 1000
    s = 0.62
    tw, th = int(w * s), int(h * s)
    top, left = 120, 120
    W, H = left + tw * len(cols) + 20, top + th * len(views) + 30
    img = Image.new("RGB", (W, H), (14, 13, 18))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 34), title, fill=(226, 214, 190), font=F, anchor="mm")
    if sub:
        d.text((W // 2, 74), sub, fill=(150, 140, 128), font=f2, anchor="mm")
    for ci, (c, label) in enumerate(cols):
        d.text((left + ci * tw + tw // 2, top - 14), label, fill=(210, 196, 170), font=f2, anchor="mm")
        for vi, v in enumerate(views):
            t = tiles[ci][vi]
            if t is None:
                continue
            img.paste(t.resize((tw, th), Image.LANCZOS), (left + ci * tw, top + vi * th))
    for vi, v in enumerate(views):
        d.text((left // 2, top + vi * th + th // 2), v.upper(), fill=(160, 150, 136), font=f2, anchor="mm")
    img.save(os.path.join(R, name))
    print("wrote", os.path.join(R, name))


sheet([("standard", "Standard R6"), ("current", "Current Female torso"), ("new", "New Female body")],
      ["front", "side", "back"], "compare_sheet.png", "Nightmare Highschool: Female body proposal",
      "All parts stay inside the R6 Torso (2x2x1) and limb (1x2x1) boxes; head unchanged")
sheet([("newatlas", "New body + atlas"), ("curatlas", "Current torso + atlas")],
      ["front", "side", "back"], "uv_check.png", "Clothing UV check",
      "Labels: T/RA/LA/RL/LL - F front, B back, R right, L left; arrows point up the body")
