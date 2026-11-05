"""python face_preview.py out.png key:shape:set:mouth[:formface|mark] ..."""
import sys, os, numpy as np
from PIL import Image
TINT = {"base": (150, 98, 62), "vampire": (220, 34, 52), "vampire2": (220, 34, 52), "wolf": (236, 158, 40), "ghoul": (214, 220, 204), "ghoul2": (214, 220, 204), "wraith": (158, 220, 255)}
VEIN = {"vampire": (158, 10, 31), "vampire2": (158, 10, 31), "ghoul": (77, 13, 82), "ghoul2": (77, 13, 82)}
SKIN = (226, 190, 158)
def lay(c, p, tint=None):
    if not os.path.exists(p):
        return
    im = Image.open(p).convert("RGBA")
    if tint:
        a = np.array(im).astype(float); a[..., :3] *= np.array(tint) / 255; im = Image.fromarray(a.clip(0, 255).astype("uint8"))
    c.alpha_composite(im)
tiles = []
for spec in sys.argv[2:]:
    form, shape, st, mouth, *extra = spec.split(":")
    c = Image.new("RGBA", (1024, 1024), SKIN + (255,))
    for e in extra:
        lay(c, e)
    if form in VEIN:
        v = tuple(int(SKIN[i] * 0.5 + VEIN[form][i] * 0.5) for i in range(3))
        lay(c, f"eyes/eyes_{shape}_{st}_{form}_veins.png", v)
    lay(c, f"eyes/eyes_{shape}_{st}_{form}_iris.png", TINT[form])
    lay(c, f"eyes/eyes_{shape}_{st}_{form}_main.png")
    lay(c, f"faceparts/brow_arched_{shape}.png", (40, 30, 30))
    lay(c, f"faceparts/{mouth}.png")
    tiles.append(c.crop((40, 100, 984, 960)).resize((472, 430), Image.LANCZOS))
cols = min(3, len(tiles)); rows = (len(tiles) + cols - 1) // cols
s = Image.new("RGB", (472 * cols, 430 * rows))
for i, t in enumerate(tiles):
    s.paste(t.convert("RGB"), ((i % cols) * 472, (i // cols) * 430))
s.save(sys.argv[1])
