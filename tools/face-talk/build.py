"""FaceTalk art: the talking mouths and the expression lids, packed into band atlases for upload.

python build.py <outdir> <eyes_dir> <lids_dir>
  mouths: every expression x viseme (neutral's rest is the face's own mouth) x lips (m / f), drawn by gen_face.py's
          renderer (mock.py's talking set); each 1024 render's mouth band (rows Y0 .. Y0 + H, full width, so the
          face strips slice it the same way) is packed K to an atlas.
  lids:   each eye shape's squint lid (gen_lids.py) slid to two levels (Soft 0.25, Narrow 0.42 closed), clipped to the
          eye's own outline (male + female, base), so no lash line floats on the skin; packed the same way.
Writes <outdir>/atlas/talk_mouth_<n>.png, talk_lid_<n>.png and manifest.json:
  { Mouth = { Y0, H, Atlases = [file], Keys = { "<expr>/<vis>/<m|f>": [atlas, row] } }, Lid = { ... "<shape>/<level>" } }
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter

OUT, EYES, LIDS = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = ["mock.py", os.path.join(OUT, "work"), EYES, LIDS]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock as M

A = os.path.join(OUT, "atlas")
os.makedirs(A, exist_ok=True)
SHAPES = ["sharp", "hooded", "fierce", "doe", "sleepless", "cat", "gentle", "calm"]
LEVELS = {"Soft": 0.25, "Narrow": 0.42}


def band(imgs, pad=3):
    rows = np.zeros(1024, bool)
    for a in imgs:
        rows |= a[..., 3].max(1) > 0.004
    ys = np.nonzero(rows)[0]
    y0, y1 = max(0, int(ys.min()) - pad), min(1024, int(ys.max()) + 1 + pad)
    return y0, y1 - y0


def pack(items, prefix):
    """items: {key: rgba float 1024x1024} -> atlases; returns (Y0, H, files, keys)"""
    y0, h = band(list(items.values()))
    k = 1024 // h
    files, keys = [], {}
    cur, n = None, 0
    for i, (key, a) in enumerate(sorted(items.items())):
        if n % k == 0:
            if cur is not None:
                files.append(save(cur, prefix, len(files)))
            cur = np.zeros((1024, 1024, 4), np.float32)
        r = (n % k) * h
        cur[r:r + h] = a[y0:y0 + h]
        keys[key] = [len(files), r]
        n += 1
    files.append(save(cur, prefix, len(files)))
    return y0, h, files, keys


def save(a, prefix, i):
    name = f"{prefix}_{i}.png"
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(A, name), optimize=True)
    return name


if __name__ == "__main__":
    man = {}
    # ---- mouths
    mouths = {}
    for ex in M.EXPR:
        for v in M.VIS:
            if ex == "neutral" and v == "rest":
                continue
            for lips in (False, True):
                mouths[f"{ex}/{v}/{'f' if lips else 'm'}"] = M.mouth(ex, v, lips)
        print("mouths", ex, flush=True)
    y0, h, files, keys = pack(mouths, "talk_mouth")
    man["Mouth"] = {"Y0": y0, "H": h, "Atlases": files, "Keys": keys}
    print("mouth band", y0, h, "atlases", len(files), flush=True)
    # ---- lids
    lids = {}
    for sh in SHAPES:
        sq = M.rgba(os.path.join(LIDS, f"lids_{sh}_squint.png"))
        eye = np.zeros((1024, 1024), np.float32)
        for sx in "mf":
            for part in ("main", "iris"):
                p = os.path.join(EYES, f"eyes_{sh}_{sx}_base_{part}.png")
                if os.path.exists(p):
                    eye = np.maximum(eye, M.rgba(p)[..., 3])
        assert eye.max() > 0, sh
        eye = np.asarray(Image.fromarray((eye * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)), np.float32) / 255
        for lv, q in LEVELS.items():
            lid = np.roll(sq, -int(round((1 - q) * 46)), 0).copy()
            lid[..., 3] *= eye
            lids[f"{sh}/{lv}"] = lid
    y0, h, files, keys = pack(lids, "talk_lid")
    man["Lid"] = {"Y0": y0, "H": h, "Atlases": files, "Keys": keys}
    print("lid band", y0, h, "atlases", len(files), flush=True)
    # ---- the brows' pivot row (for turning a strip's brow slice about the brow, not the label's middle)
    main, iris, brow, _, _ = M.layers("f")
    ys = np.nonzero(brow[..., 3].max(1) > 0.02)[0]
    man["BrowY"] = int(round(float(ys.mean())))
    man["Expr"] = {k: {"Brow": v["brow"][0], "BrowAmt": v["brow"][1], "Squint": v["squint"]} for k, v in M.EXPR.items()}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print("ok", man["BrowY"])
