"""Measure dark borders at the seams of every 585x559 template.

For each limb/torso face: the outermost pixel ring vs the pixels 3-6 px inside.
Reports how much darker the edge is (0 = same, 0.5 = half as bright) and what the
margin around the faces holds (transparent, black, ...).
    python Clothing/tools/seam_audit.py [files...]
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from nhcloth import R, TORSO_RING, ARM_FACES, W, H, OUT

FACES = TORSO_RING + ARM_FACES + ["T_UP", "T_D", "RA_UP", "LA_UP", "RA_D", "LA_D"]


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def face_masks():
    inside = np.zeros((H, W), bool)
    for n in FACES:
        x, y, w, h = R[n]
        inside[y:y + h, x:x + w] = True
    return inside


def audit(path):
    a = np.array(Image.open(path).convert("RGBA")).astype(np.float32)
    L = lum(a)
    vis = a[..., 3] > 127
    rows = []
    for n in TORSO_RING + ARM_FACES:   # the faces whose side edges meet another face
        x, y, w, h = R[n]
        for side, edge_cols, in_cols in (("L", [x], range(x + 3, x + 7)), ("R", [x + w - 1], range(x + w - 7, x + w - 3))):
            e = np.zeros((H, W), bool); e[y:y + h, edge_cols] = True
            i = np.zeros((H, W), bool); i[y:y + h, list(in_cols)] = True
            e &= vis; i &= vis
            if e.sum() < 20 or i.sum() < 20:
                continue
            le, li = L[e].mean(), L[i].mean()
            rows.append((n + side, le, li))
    drops = [(1 - le / max(li, 1)) for _, le, li in rows]
    inner = np.mean([li for _, _, li in rows]) if rows else 0
    # visibility score: darkening x brightness of the cloth (a dark seam on black cloth can't be seen)
    score = float(np.mean(drops) * inner) if rows else 0
    inside = face_masks()
    m = ~inside
    ma = a[m]
    trans = (ma[:, 3] < 128).mean()
    blackop = ((ma[:, 3] >= 128) & (lum(ma) < 30)).mean()
    return dict(file=Path(path).name, edge_drop=float(np.mean(drops)) if rows else 0, worst=float(max(drops)) if rows else 0,
                cloth_lum=float(inner), score=score, margin_transparent=float(trans), margin_black=float(blackop))


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(str(p) for p in OUT.glob("*.png") if not p.name.startswith(("_", "contact", "studio")))
    res = sorted((audit(f) for f in files), key=lambda r: -r["score"])
    print(f"{'file':42} {'drop':>5} {'worst':>5} {'lum':>5} {'score':>6} {'m_tr':>5} {'m_blk':>5}")
    for r in res:
        print(f"{r['file']:42} {r['edge_drop']:5.2f} {r['worst']:5.2f} {r['cloth_lum']:5.0f} {r['score']:6.1f} {r['margin_transparent']:5.2f} {r['margin_black']:5.2f}")
