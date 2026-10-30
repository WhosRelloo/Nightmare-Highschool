"""sheet.py out.png a.png b.png ... : half-size side-by-side contact sheet"""
import sys
from PIL import Image
out, names = sys.argv[1], sys.argv[2:]
ims = [Image.open(n) for n in names]
ims = [i.resize((i.width // 2, i.height // 2)) for i in ims]
s = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)))
x = 0
for i in ims:
    s.paste(i, (x, 0)); x += i.width
s.save(out)
