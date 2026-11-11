"""Contact sheets for the QOL kit renders (system Python + PIL).

python qol_sheet.py [Item,Item...] [--out sheet.jpg] [--h 520]
One row per item: its hero, close / pov and solo renders, labelled.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

R = "E:/NH-Work/qol/renders"
argv = sys.argv[1:]
OUTP = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(R, "_sheet.jpg")
H = int(argv[argv.index("--h") + 1]) if "--h" in argv else 520
names = [a for a in argv if not a.startswith("--") and (argv.index(a) == 0 or not argv[argv.index(a) - 1].startswith("--"))]
ITEMS = names[0].split(",") if names else ["Lantern", "CampusMap", "Compass", "Umbrella", "Timetable", "KeyRing", "HallPass",
                                           "LibraryBook", "Thermos", "SnackTin", "FirstAid", "HandWarmer"]
rows = []
f = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 26)
for it in ITEMS:
    ims = []
    for v in ("hero", "close", "pov", "solo"):
        p = os.path.join(R, f"{it}_{v}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            ims.append(im.resize((int(im.width * H / im.height), H)))
    if not ims:
        continue
    row = Image.new("RGB", (sum(i.width for i in ims) + 8 * (len(ims) - 1), H), (12, 11, 14))
    x = 0
    for i in ims:
        row.paste(i, (x, 0)); x += i.width + 8
    ImageDraw.Draw(row).text((14, 10), it, font=f, fill=(236, 214, 160))
    rows.append(row)
W = max(r.width for r in rows)
sheet = Image.new("RGB", (W, sum(r.height for r in rows) + 8 * (len(rows) - 1)), (12, 11, 14))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height + 8
sheet.save(OUTP, quality=90)
print(OUTP, sheet.size)
