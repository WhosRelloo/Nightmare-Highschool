"""Lay out a prop's clip frames (rendered by props batch 49's clip_strips) as previews/<Prop>_clips.png: one row per clip
(start, middle, end), the clip's name on the left. python art/hometown/clip_sheet.py <Prop> [...]"""
import glob, os, re, sys
from PIL import Image, ImageDraw, ImageFont
PRE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "props", "previews")
for prop in sys.argv[1:]:
    rows = {}
    for f in glob.glob(os.path.join(PRE, f"_clip_{prop}_*_*.png")):
        m = re.match(rf"_clip_{prop}_(.+)_(\d)\.png", os.path.basename(f))
        rows.setdefault(m.group(1), {})[int(m.group(2))] = f
    if not rows:
        continue
    th = 300
    first = Image.open(next(iter(next(iter(rows.values())).values())))
    tw = int(first.width * th / first.height)
    sheet = Image.new("RGB", (220 + 3 * (tw + 6), len(rows) * (th + 6)), (24, 22, 28))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 22)
    for r, (clip, fr) in enumerate(sorted(rows.items())):
        d.text((12, r * (th + 6) + th / 2 - 12), clip, fill=(230, 220, 200), font=font)
        for k in range(3):
            if k in fr:
                sheet.paste(Image.open(fr[k]).convert("RGB").resize((tw, th)), (220 + k * (tw + 6), r * (th + 6)))
    out = os.path.join(PRE, f"{prop}_clips.png")
    sheet.save(out)
    print(out)
