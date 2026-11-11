"""Contact sheets of the accessory renders (E:/NH-Work/acc/renders).

python acc_sheet.py <out.jpg> <Item>[,<Item>] [--views front34,side,back,close] [--h 420] [--titles]
Each item is one row: its views side by side, labelled with the item's name (from layout/<Item>.json).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

R = sys.argv[sys.argv.index("--root") + 1] + "/renders" if "--root" in sys.argv else "E:/NH-Work/acc/renders"
L = sys.argv[sys.argv.index("--root") + 1] + "/layout" if "--root" in sys.argv else "E:/NH-Work/acc/layout"
args = sys.argv[1:]
out = args[0]
items = args[1].split(",")
views = args[args.index("--views") + 1].split(",") if "--views" in args else ["front34", "side", "back", "close"]
H = int(args[args.index("--h") + 1]) if "--h" in args else 420
try:
    font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 26)
    small = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 18)
except OSError:
    font = small = ImageFont.load_default()
rows = []
for it in items:
    ims = []
    for v in views:
        p = os.path.join(R, f"{it}_{v}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
            ims.append(im)
    if not ims:
        continue
    name, tris = it, ""
    lp = os.path.join(L, f"{it}.json")
    if os.path.exists(lp):
        d = json.load(open(lp))
        name, tris = d.get("name", it), f"{d.get('tris', 0):,} tris"
    w = sum(i.width for i in ims) + 8 * (len(ims) - 1)
    row = Image.new("RGB", (w, H + 44), (16, 14, 20))
    dr = ImageDraw.Draw(row)
    dr.text((10, 8), name, fill=(214, 182, 120), font=font)
    dr.text((w - 10, 12), tris, fill=(150, 140, 130), font=small, anchor="ra")
    x = 0
    for i in ims:
        row.paste(i, (x, 44)); x += i.width + 8
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new("RGB", (W, sum(r.height for r in rows) + 6 * len(rows)), (10, 9, 13))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height + 6
sheet.save(out, quality=90)
print(out, sheet.size)
