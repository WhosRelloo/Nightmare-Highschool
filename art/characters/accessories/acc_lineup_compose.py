"""compose a body-type lineup (acc_lineup.py's tiles) into one labelled image: python acc_lineup_compose.py <tiles.json> <out.jpg> [title]"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
tiles = json.load(open(sys.argv[1]))
title = sys.argv[3] if len(sys.argv) > 3 else ""
NAMES = {"standard": "Standard", "female": "Female", "lean": "Lean", "athletic": "Athletic", "muscular": "Muscular",
         "stocky": "Stocky", "heavy": "Heavy", "petite": "Petite", "toned": "Toned", "curvy": "Curvy", "strong": "Strong", "plus": "Plus"}
ims = [(b, Image.open(p).convert("RGB")) for b, p in tiles]
w, h = ims[0][1].size
cols = 6
rows = (len(ims) + cols - 1) // cols
top = 44 if title else 0
o = Image.new("RGB", (cols * w, rows * (h + 26) + top), (12, 11, 15))
d = ImageDraw.Draw(o)
f = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 18)
ft = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 24)
if title:
    d.text((10, 8), title, fill=(214, 182, 120), font=ft)
for i, (b, im) in enumerate(ims):
    x, y = (i % cols) * w, top + (i // cols) * (h + 26)
    o.paste(im, (x, y))
    d.text((x + w // 2, y + h + 3), NAMES.get(b, b), fill=(200, 190, 170), font=f, anchor="ma")
o.save(sys.argv[2], quality=90)
print(sys.argv[2], o.size)
