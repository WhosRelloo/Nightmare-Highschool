"""Big front/back mock-ups of outfit pairs for review: python kit_mock.py out.png top1.png:bot1.png ..."""
import sys
from PIL import Image, ImageDraw
from sheet import figure, BG
from nhcloth import OUT, font
pairs = [a.split(":") for a in sys.argv[2:]]
cols = 4
cw, ch = 560, 400
rows = (len(pairs) + cols - 1) // cols
im = Image.new("RGBA", (cols * cw, rows * ch), BG)
d = ImageDraw.Draw(im)
for i, (t, b) in enumerate(pairs):
    s = Image.open(OUT / "kits" / t).convert("RGBA"); p = Image.open(OUT / "kits" / b).convert("RGBA")
    x0, y0 = (i % cols) * cw, (i // cols) * ch
    for j, back in enumerate((False, True)):
        im.alpha_composite(figure(s, p, back).resize((256, 320), Image.LANCZOS), (x0 + 12 + j * 270, y0 + 10))
    d.text((x0 + 14, y0 + 340), t.replace(".png", ""), font=font(15), fill=(236, 226, 200))
    d.text((x0 + 14, y0 + 362), b.replace(".png", ""), font=font(13, bold=False), fill=(180, 170, 150))
im.convert("RGB").save(sys.argv[1], quality=92)
