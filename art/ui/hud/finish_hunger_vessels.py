"""Hunger vessels (Hunger 1.0), stage 2 of 2: from the Blender renders to the upload set (system Python + Pillow).

  python finish_hunger_vessels.py
  in:  art/ui/hud/out/hunger/render/<Race>_{empty,full,mask}.png, Plate.png   (blender_hunger_vessels.py)
  out: art/group-upload-hunger/Hunger<Race>{Back,Fill,Glow}.png, HungerFrost.png, HungerPlate.png, HungerSplash.png,
       HungerMote.png, and art/ui/hud/out/hunger/layout.json (the crop's aspect and where the contents sit, for
       Config.Body.ArtFill / ArtAspect)

Every race is cut to the same frame (the union of all the vessels plus a margin), so the HUD lays them out alike.
  Back:  the vessel spent.
  Fill:  the brimming render, kept only where the contents are (its alpha times the mask's): the HUD shows it up to the
         level over Back.
  Glow:  white, the contents' shape blurred wide; the HUD tints it with the race colour.
  Frost: white-blue rime and hairline cracks over the glass, thickest at the edges (shared by every race).
Edges are bled and the images resized premultiplied, so nothing gets a dark fringe.
"""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
RENDER = HERE / "out" / "hunger" / "render"
OUTDIR = HERE.parent.parent / "group-upload-hunger"
OUTDIR.mkdir(parents=True, exist_ok=True)
RACES = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]
MARGIN = 10      # render px around the union
SCALE = 0.5      # render -> upload


def load(name):
    return Image.open(RENDER / name).convert("RGBA")


def premul_resize(im, size):
    """resize with premultiplied alpha (no dark fringe)"""
    r, g, b, a = im.split()
    pr = ImageChops.multiply(r, a)
    pg = ImageChops.multiply(g, a)
    pb = ImageChops.multiply(b, a)
    pr, pg, pb, a2 = (c.resize(size, Image.LANCZOS) for c in (pr, pg, pb, a))
    out = []
    ap = a2.load()
    for c in (pr, pg, pb):
        px = c.load()
        w, h = c.size
        for y in range(h):
            for x in range(w):
                av = ap[x, y]
                px[x, y] = min(255, int(px[x, y] * 255 / av)) if av > 0 else 0
        out.append(c)
    return Image.merge("RGBA", (*out, a2))


def bleed(im, rounds=6):
    """push edge colours out under the transparent pixels"""
    base = im.copy()
    rgb = Image.new("RGBA", im.size, (0, 0, 0, 0))
    rgb.paste(im, (0, 0))
    for _ in range(rounds):
        grown = rgb.filter(ImageFilter.MaxFilter(3))
        mask = rgb.split()[3].point(lambda v: 255 if v == 0 else 0)
        rgb = Image.composite(grown, rgb, mask)
    r, g, b, _ = rgb.split()
    return Image.merge("RGBA", (r, g, b, base.split()[3]))


def bbox_union(images):
    box = None
    for im in images:
        b = im.split()[3].point(lambda v: 255 if v > 6 else 0).getbbox()
        if b is None:
            continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def save(im, name):
    im.save(OUTDIR / name, optimize=True)
    print("wrote", name, im.size)


def main():
    renders = {r: {s: load(f"{r}_{s}.png") for s in ("empty", "full", "mask")} for r in RACES}
    W, H = renders["Human"]["empty"].size
    box = bbox_union([renders[r][s] for r in RACES for s in ("empty", "full")])
    box = (max(0, box[0] - MARGIN), max(0, box[1] - MARGIN), min(W, box[2] + MARGIN), min(H, box[3] + MARGIN))
    cw, ch = box[2] - box[0], box[3] - box[1]
    out_size = (round(cw * SCALE), round(ch * SCALE))
    # where the contents sit (the union of the masks), as fractions of the crop
    cbox = bbox_union([renders[r]["mask"] for r in ("Human", "Priest")])
    fill = {
        "Left": round((cbox[0] - box[0]) / cw, 4), "Right": round((cbox[2] - box[0]) / cw, 4),
        "Top": round((cbox[1] - box[1]) / ch, 4), "Bottom": round((cbox[3] - box[1]) / ch, 4),
    }
    for race in RACES:
        R = renders[race]
        empty = R["empty"].crop(box)
        full = R["full"].crop(box)
        mask = R["mask"].crop(box).split()[3]
        fa = ImageChops.multiply(full.split()[3], mask)
        fr, fg, fb, _ = full.split()
        fillim = Image.merge("RGBA", (fr, fg, fb, fa))
        save(premul_resize(bleed(empty), out_size), f"Hunger{race}Back.png")
        save(premul_resize(bleed(fillim), out_size), f"Hunger{race}Fill.png")
        # the halo: the contents' shape, blurred wide, white (tinted in the HUD)
        g = mask.resize(out_size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
        g = g.point(lambda v: min(255, int(v * 1.6)))
        glow = Image.merge("RGBA", (Image.new("L", out_size, 255),) * 3 + (g,))
        save(glow, f"Hunger{race}Glow.png")
    # frost: rime from the glass edges inward, with hairline cracks (shared)
    rnd = random.Random(11)
    gw, gh = out_size
    jar = Image.new("L", out_size, 0)
    jd = ImageDraw.Draw(jar)
    x0, x1 = fill["Left"] * gw - 6, fill["Right"] * gw + 6
    y0, y1 = fill["Top"] * gh - 8, fill["Bottom"] * gh + 6
    jd.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=255)
    edge = Image.new("L", out_size, 0)
    ed = ImageDraw.Draw(edge)
    for _ in range(900):     # crystals clustered at the jar's rim
        side = rnd.random()
        t = rnd.random()
        if side < 0.35:
            x, y = x0 + rnd.expovariate(1 / 7), y0 + t * (y1 - y0)
        elif side < 0.7:
            x, y = x1 - rnd.expovariate(1 / 7), y0 + t * (y1 - y0)
        else:
            x, y = x0 + t * (x1 - x0), y1 - rnd.expovariate(1 / 9)
        r = rnd.uniform(0.6, 2.4)
        a = rnd.randint(90, 220)
        ed.ellipse((x - r, y - r, x + r, y + r), fill=a)
        # a feathered spike
        ang = rnd.uniform(0, math.tau)
        ln = rnd.uniform(2, 7)
        ed.line((x, y, x + math.cos(ang) * ln, y + math.sin(ang) * ln), fill=a // 2, width=1)
    for _ in range(9):       # hairline cracks
        x, y = rnd.uniform(x0, x1), rnd.choice((y0 + 4, y1 - 4))
        ang = rnd.uniform(-math.pi, math.pi)
        for _ in range(rnd.randint(4, 8)):
            ln = rnd.uniform(4, 10)
            nx, ny = x + math.cos(ang) * ln, y + math.sin(ang) * ln
            ed.line((x, y, nx, ny), fill=200, width=1)
            x, y = nx, ny
            ang += rnd.uniform(-0.9, 0.9)
    frost_a = ImageChops.multiply(edge.filter(ImageFilter.GaussianBlur(0.6)), jar)
    haze = jar.filter(ImageFilter.GaussianBlur(4)).point(lambda v: v // 6)
    frost_a = ImageChops.lighter(frost_a, haze)
    frost = Image.merge("RGBA", (Image.new("L", out_size, 228), Image.new("L", out_size, 240), Image.new("L", out_size, 255), frost_a))
    save(frost, "HungerFrost.png")
    # the plate, cropped
    plate = load("Plate.png")
    pb = plate.split()[3].point(lambda v: 255 if v > 6 else 0).getbbox()
    plate = plate.crop((pb[0] - 4, pb[1] - 4, pb[2] + 4, pb[3] + 4))
    plate = premul_resize(bleed(plate), (plate.width // 2, plate.height // 2))
    save(plate, "HungerPlate.png")
    # splash ring and mote
    S = 256
    ring = Image.new("L", (S, S), 0)
    rd = ImageDraw.Draw(ring)
    rd.ellipse((24, 24, S - 24, S - 24), outline=255, width=14)
    ring = ring.filter(ImageFilter.GaussianBlur(5))
    save(Image.merge("RGBA", (Image.new("L", (S, S), 255),) * 3 + (ring,)), "HungerSplash.png")
    M = 64
    mote = Image.new("L", (M, M), 0)
    ImageDraw.Draw(mote).ellipse((20, 20, M - 20, M - 20), fill=255)
    mote = mote.filter(ImageFilter.GaussianBlur(6)).point(lambda v: min(255, v * 2))
    save(Image.merge("RGBA", (Image.new("L", (M, M), 255),) * 3 + (mote,)), "HungerMote.png")
    layout = {"Crop": box, "Size": out_size, "Aspect": round(out_size[0] / out_size[1], 4), "Fill": fill,
              "PlateSize": plate.size, "PlateSlice": [36, 30, plate.width - 36, plate.height - 30]}
    (HERE / "out" / "hunger" / "layout.json").write_text(json.dumps(layout, indent=2))
    print(json.dumps(layout))


if __name__ == "__main__":
    main()
