"""Talking faces mockup: mouth shapes (visemes) x expressions, drawn with the house mouth renderer (gen_face.py's
open x width grid, cel + PBR bake), composited on real NH eyes / brows / lids the way the game layers them.
Brow movement = each of the 12 face strips nudges its brow slice up or down (what the game can do per strip);
squint = the squint lid slid down over the eye by an amount (one lid image, offset).
usage: python mock.py <outdir> <eyes_dir> <lids_dir>
"""
import os, sys, types, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT, EYES, LIDS = sys.argv[1], sys.argv[2], sys.argv[3]
GEN = "E:/Nightmare-Highschool/tools/ui-textures"
sys.path.insert(0, GEN)
os.makedirs(OUT, exist_ok=True)
MOUTHDIR = os.path.join(OUT, "mouths")

# ---- the house renderer, with extra grid points injected into its SPEC table (the shipped mouths are untouched)
src = open(os.path.join(GEN, "gen_face.py"), encoding="utf-8").read()
src = src.replace('"cat": None, "fang"', '**EXTRA_SPEC, "cat": None, "fang"', 1)
src = src.replace('top, bot, W, h_bot = mouth_edges(open_, width, ex.get("asym", 0), ex.get("down", 0), 1.0, ex.get("wobble", 0))',
                  'top, bot, W, h_bot = mouth_edges(open_, width, ex.get("asym", 0), ex.get("down", 0), ex.get("wscale", 1.0), ex.get("wobble", 0))')
src = src.replace('top, bot, W, h_bot = mouth_edges(open_ * 1.35 + 0.04, width, ex.get("asym", 0), ex.get("down", 0), 1.0, ex.get("wobble", 0))',
                  'top, bot, W, h_bot = mouth_edges(open_ * 1.35 + 0.04, width, ex.get("asym", 0), ex.get("down", 0), ex.get("wscale", 1.0), ex.get("wobble", 0))')
assert src.count('ex.get("wscale", 1.0)') == 2
assert "**EXTRA_SPEC" in src
sys.argv = ["gen_face.py", MOUTHDIR, EYES]
G = types.ModuleType("gen_face_talk")
G.__file__ = os.path.join(GEN, "gen_face.py")
G.EXTRA_SPEC = {}
exec(compile(src, G.__file__, "exec"), G.__dict__)

# ---- the talking set
VIS = {   # viseme: (open, width, extras)  on the neutral face. Exaggerated (owner: "more exaggerated"): opens past
          # the everyday grid (open up to 1.3) and the talking mouth drawn bigger (wscale)
    "rest": None,                                  # the expression's own resting mouth
    "MBP": (0.0, -0.4, {"wscale": 0.9}),           # lips pressed in (m, b, p)
    "AI": (1.3, 0.35, {"wscale": 1.3}),            # jaw dropped wide open (a, i)
    "E": (0.7, 1.0, {"wscale": 1.35}),             # stretched wide, teeth (e)
    "O": (1.15, -0.85, {"wscale": 1.2}),           # big round (o)
    "UW": (0.55, -1.0, {"wscale": 0.95}),          # tight pucker (u, w, q)
    "FV": (0.24, 0.55, {"wscale": 1.2}),           # upper teeth on the lip (f, v)
    "L": (0.85, 0.1, {"wscale": 1.2}),             # open, tongue up (l, th)
    "CONS": (0.3, 0.8, {"wscale": 1.25}),          # teeth together, wide (s, t, d, k, g, n, ...)
}
EXPR = {   # mouth modifiers, rest mouth, brow move (texels: + = down), squint (0..1)
    "neutral":   dict(dw=0.0, down=0, asym=0, k=1.0, rest=(0.0, 0.0, {}), brow=("flat", 0), squint=0.0),
    "happy":     dict(dw=0.45, down=-1, asym=0, k=1.0, rest=(0.0, 1.0, {}), brow=("up", 5), squint=0.22),
    "angry":     dict(dw=-0.1, down=5, asym=0, k=0.95, rest=(0.0, 0.1, {"down": 9}), brow=("inner_down", 14), squint=0.38),
    "surprised": dict(dw=-0.35, down=0, asym=0, k=1.3, rest=(0.4, -0.7, {}), brow=("up", 16), squint=0.0),
    "worried":   dict(dw=-0.25, down=3, asym=0, k=0.85, rest=(0.0, -0.6, {"down": 4, "wobble": 1.3}), brow=("inner_up", 12), squint=0.08),
    "smug":      dict(dw=0.25, down=0, asym=6, k=0.8, rest=(0.0, 0.3, {"asym": 7}), brow=("one_up", 10), squint=0.42),
}


def spec_for(expr, vis):
    e = EXPR[expr]
    if vis == "rest":
        return e["rest"]
    o, w, ex = VIS[vis]
    ex = dict(ex)
    o = min(1.45, o * e["k"]) if o > 0 else 0.0
    w = float(np.clip(w + e["dw"] * (1 - 0.5 * max(0, -w)), -1, 1))
    if e["down"]:
        ex["down"] = ex.get("down", 0) + e["down"]
    if e["asym"]:
        ex["asym"] = ex.get("asym", 0) + e["asym"]
    return (o, w, ex)


MCACHE = {}


def mouth(expr, vis, lips):
    if (expr, vis, lips) in MCACHE:
        return MCACHE[(expr, vis, lips)]
    key = f"t_{expr}_{vis}"
    G.EXTRA_SPEC[key] = spec_for(expr, vis)
    out, _ = G.render_mouth(key, lips)
    MCACHE[(expr, vis, lips)] = out
    return out


# ---- the face layers
def rgba(p):
    return np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255


SKIN = np.array([0.93, 0.80, 0.70], np.float32)
HAIR = np.array([0.16, 0.11, 0.10], np.float32)
IRIS = np.array([0.62, 0.38, 0.20], np.float32)
SHAPE, BROW = "doe", "soft"
cache = {}


def layers(sex):
    if sex in cache:
        return cache[sex]
    main = rgba(os.path.join(EYES, f"eyes_{SHAPE}_{sex}_base_main.png"))
    iris = rgba(os.path.join(EYES, f"eyes_{SHAPE}_{sex}_base_iris.png"))
    xs, top, bottom, n = G.shape_fit(SHAPE)
    brow = G.render_brow(SHAPE, BROW, xs, top, 100)
    lid_sq = rgba(os.path.join(LIDS, f"lids_{SHAPE}_squint.png"))
    lid_bl = rgba(os.path.join(LIDS, f"lids_{SHAPE}_blink.png"))
    cache[sex] = (main, iris, brow, lid_sq, lid_bl)
    return cache[sex]


def squint_lid(sex, sq):
    key = ("sq", sex, round(sq, 2))
    if key not in cache:
        main, iris, brow, lid_sq, lid_bl = layers(sex)
        lid = np.roll(lid_sq, -int(round((1 - sq) * 46)), 0)
        from PIL import ImageFilter
        eye = np.maximum(main[..., 3], iris[..., 3])
        eye = np.asarray(Image.fromarray((eye * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) / 255
        lid = lid.copy()
        lid[..., 3] *= eye
        cache[key] = lid
    return cache[key]


def strip_cols(i):
    return int(round(i * 1024 / 12)), int(round((i + 1) * 1024 / 12))


def brow_dy(kind, amt, x):
    """the brow's vertical move (texels, + = down) at texel column x: a continuous curve"""
    d = abs(x - 512)
    inner = float(np.clip(1 - (d - 60) / 230, 0, 1))   # 1 at the brows' inner ends, 0 at the outer ends
    if kind == "flat":
        return 0.0
    if kind == "up":
        return -amt
    if kind == "inner_down":
        return amt * inner - amt * 0.3
    if kind == "inner_up":
        return -amt * inner + amt * 0.15
    if kind == "one_up":
        return -amt if x > 512 else 0.0
    return 0.0


def brow_layer(brow, kind, amt):
    """the brow as the 12 strips draw it: each strip's slice moved to the curve at its centre and turned to match the
    curve's slope there (GuiObject.Rotation), so the slices meet as one smooth brow"""
    out = np.zeros_like(brow)
    ys = np.nonzero(brow[..., 3].max(1) > 0.02)[0]
    cy = float(ys.mean()) if len(ys) else 400.0
    for i in range(12):
        u0, u1 = strip_cols(i)
        xc = (u0 + u1) / 2
        dy = brow_dy(kind, amt, xc)
        slope = (brow_dy(kind, amt, xc + 6) - brow_dy(kind, amt, xc - 6)) / 12
        ang = np.degrees(np.arctan(slope))
        im = Image.fromarray((brow * 255).astype(np.uint8), "RGBA")
        im = im.rotate(-ang, resample=Image.BICUBIC, center=(xc, cy), translate=(0, dy))
        a = np.asarray(im, np.float32) / 255
        out[:, u0:u1] = a[:, u0:u1]
    return out


def over(base, layer, tint=None, dy=0, cols=None):
    a = layer[..., 3:]
    rgb = layer[..., :3] if tint is None else layer[..., :3] * tint
    if dy:
        a = np.roll(a, dy, 0)
        rgb = np.roll(rgb, dy, 0)
    if cols is not None:
        m = np.zeros_like(a)
        m[:, cols[0]:cols[1]] = 1
        a = a * m
    return rgb * a + base * (1 - a)


def face(expr, vis, sex="f", blink=0.0, brow_amt=1.0, squint=None, lips=True):
    main, iris, brow, lid_sq, lid_bl = layers(sex)
    e = EXPR[expr]
    img = np.ones((1024, 1024, 3), np.float32) * SKIN
    img = over(img, iris, IRIS)
    img = over(img, main)
    sq = e["squint"] if squint is None else squint
    if blink > 0.5:
        img = over(img, lid_bl, SKIN)
    elif sq > 0:
        # a squint level baked offline: the squint lid slid up by (1 - squint), clipped to the eye's own shape
        img = over(img, squint_lid(sex, sq), SKIN)
    kind, amt = e["brow"]
    img = over(img, brow_layer(brow, kind, amt * brow_amt), HAIR)
    img = over(img, mouth(expr, vis, lips))
    return img


def crop(img, box=(120, 330, 904, 900), scale=0.42):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).crop(box)
    w, h = im.size
    return im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def font(sz):
    for f in ("C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def sheets():
    F, FS = font(26), font(18)
    VLABEL = {"rest": "rest", "MBP": "M B P", "AI": "A I", "E": "E", "O": "O", "UW": "U W Q", "FV": "F V", "L": "L TH",
              "CONS": "S T D K N..."}
    # sheet 1: the mouth set on the neutral face, close-up (mouth band), plain and fuller lips
    vis = list(VIS)
    cw, ch = 300, 170
    sheet = Image.new("RGB", (cw * len(vis), ch * 2 + 70), (16, 14, 20))
    d = ImageDraw.Draw(sheet)
    for j, v in enumerate(vis):
        for r, lips in enumerate((False, True)):
            img = face("neutral", v, "m" if not lips else "f", lips=lips)
            tile = crop(img, (362, 690, 662, 860), 1.0)
            sheet.paste(tile, (j * cw, 50 + r * ch))
        d.text((j * cw + 12, 10), VLABEL[v], font=F, fill=(232, 214, 190))
    sheet.save(os.path.join(OUT, "sheet_mouths.png"))
    # sheet 2: expressions (rows) x a few talking frames (columns), whole face
    cols = ["rest", "AI", "E", "O", "CONS", "MBP"]
    tw, th = 340, 250
    sheet = Image.new("RGB", (160 + tw * len(cols), 40 + th * len(EXPR)), (16, 14, 20))
    d = ImageDraw.Draw(sheet)
    for j, v in enumerate(cols):
        d.text((160 + j * tw + 12, 8), VLABEL[v], font=F, fill=(232, 214, 190))
    for r, ex in enumerate(EXPR):
        d.text((14, 40 + r * th + th // 2 - 14), ex.capitalize(), font=F, fill=(232, 214, 190))
        for j, v in enumerate(cols):
            sheet.paste(crop(face(ex, v, "f" if r % 2 else "m", lips=bool(r % 2))), (160 + j * tw + 4, 40 + r * th + 4))
    sheet.save(os.path.join(OUT, "sheet_expressions.png"))
    print("ok", OUT)


if __name__ == "__main__":
    sheets()
