"""Front/back mock-ups of transformation variants: python preview_forms.py <dest_dir> <out.png> shirt.png pants.png [...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from sheet import figure
from nhcloth import font

dest, out, pieces = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
forms = ["base", "vampire", "wolf", "ghoul", "wraith", "priest"]
VAR = Path(__file__).resolve().parents[1] / "variants"
pairs = list(zip(pieces[0::2], pieces[1::2]))
cw, ch = 260, 190
sheet = Image.new("RGBA", (cw * len(forms) + 20, ch * len(pairs) + 50), (18, 14, 16, 255))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(forms):
    d.text((20 + i * cw + cw // 2, 24), f, font=font(16), fill=(200, 170, 100, 255), anchor="mm")
def get(f, n):
    if f == "base":
        p = VAR / n
        if not p.exists():
            import form_variants as fv
            import numpy as np
            return Image.fromarray(np.clip(fv.load_piece(n), 0, 255).astype("uint8"), "RGBA")
        return Image.open(p).convert("RGBA")
    return Image.open(dest / f / n).convert("RGBA")
for j, (s, p) in enumerate(pairs):
    for i, f in enumerate(forms):
        sh, pa = get(f, s), get(f, p)
        for k, back in enumerate((False, True)):
            fg = figure(sh, pa, back).resize((112, 140), Image.NEAREST)
            sheet.alpha_composite(fg, (20 + i * cw + k * 122, 45 + j * ch))
sheet.convert("RGB").save(out)
