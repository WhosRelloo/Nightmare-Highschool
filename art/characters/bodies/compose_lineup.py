"""Lays out renders/lineup_male.png and lineup_female.png from the Blender renders (system Python + Pillow)."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "E:/NH-Work/bodytypes"


def sheet(cols, out, title, sub):
    R = os.path.join(out, "renders")
    s = 0.42
    tw, th = int(700 * s), int(1000 * s)
    top, left = 150, 90
    W, H = left + tw * len(cols) + 20, top + th * 3 + 20
    img = Image.new("RGB", (W, H), (14, 13, 18))
    d = ImageDraw.Draw(img)
    try:
        F = ImageFont.truetype("georgiab.ttf", 34); f2 = ImageFont.truetype("georgia.ttf", 19); f3 = ImageFont.truetype("georgiab.ttf", 21)
    except OSError:
        F = f2 = f3 = ImageFont.load_default()
    d.text((W // 2, 34), title, fill=(226, 214, 190), font=F, anchor="mm")
    d.text((W // 2, 74), sub, fill=(150, 140, 128), font=f2, anchor="mm")
    for ci, (key, name, note) in enumerate(cols):
        cx = left + ci * tw + tw // 2
        d.text((cx, top - 46), name, fill=(226, 196, 140) if ci == 0 else (226, 214, 190), font=f3, anchor="mm")
        d.text((cx, top - 20), note, fill=(150, 140, 128), font=f2, anchor="mm")
        for vi, v in enumerate(("front", "side", "back")):
            p = os.path.join(R, f"{key}_{v}.png")
            if os.path.exists(p):
                img.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (left + ci * tw, top + vi * th))
    for vi, v in enumerate(("FRONT", "SIDE", "BACK")):
        d.text((left // 2, top + vi * th + th // 2), v, fill=(160, 150, 136), font=f2, anchor="mm")
    path = os.path.join(R, f"lineup_{title.split()[0].lower()}.png")
    img.save(path)
    return path



cols = json.load(open(os.path.join(OUT, "renders", "lineup_cols.json")))
sub = "Same head, height, joints and animations; widths inside the R6 boxes; side views hide the near arm"
print(sheet(cols["male"], OUT, "Male body types", sub))
print(sheet(cols["female"], OUT, "Female body types", sub))
