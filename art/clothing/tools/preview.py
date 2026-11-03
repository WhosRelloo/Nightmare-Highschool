"""Quick look: tile given variant files on a grey checkerboard."""
import sys
from PIL import Image
from nhcloth import OUT
names = sys.argv[2:]
out = sys.argv[1]
cols = min(3, len(names))
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGBA", (585 * cols, 559 * rows), (90, 90, 90, 255))
for i, n in enumerate(names):
    im = Image.open(OUT / n).convert("RGBA")
    bg = Image.new("RGBA", im.size, (70, 140, 200, 255))
    bg.alpha_composite(im)
    sheet.paste(bg, ((i % cols) * 585, (i // cols) * 559))
sheet.save(out)
