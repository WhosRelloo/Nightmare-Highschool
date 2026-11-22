"""Compact review sheet of every sky set: the 360 panorama strip of each NHSky<Set>_preview.png, two columns.

usage: python tools/sky-2360/contact_sheet.py [preview=art/skies-preview] [out=<preview>/NHSkies_Sheet.jpg]
Run tools/vfx/make_skyboxes.py first (it writes the per-set previews and seams.txt).
"""
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PREVIEW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "skies-preview")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PREVIEW, "NHSkies_Sheet.jpg")
ORDER = ["Dawn", "Day", "Dusk", "Night", "NightNew", "NightCrimson", "NightBlue", "Storm",
         "WinterDay", "WinterDusk", "WinterNight", "SpringDay", "SpringDusk", "SpringNight",
         "SummerDay", "SummerDusk", "SummerNight", "NightmareDusk", "NightmareNight"]
W, H, GAP = 1080, 270, 6
names = [n for n in ORDER if os.path.exists(os.path.join(PREVIEW, f"NHSky{n}_preview.png"))]
rows = (len(names) + 1) // 2
sheet = Image.new("RGB", (2 * W + 3 * GAP, rows * (H + GAP) + GAP), (7, 6, 10))
for i, n in enumerate(names):
    im = Image.open(os.path.join(PREVIEW, f"NHSky{n}_preview.png")).convert("RGB")
    pano = im.crop((0, 0, 1440, 360)).resize((W, H), Image.LANCZOS)
    sheet.paste(pano, (GAP + (i % 2) * (W + GAP), GAP + (i // 2) * (H + GAP)))
sheet.save(OUT, quality=90)
print(OUT)
