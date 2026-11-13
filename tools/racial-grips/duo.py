"""Render both rigs of a baked grip together (flat-shaded boxes, painter's sort) at chosen times.
usage: python duo.py <clip> out.png [t1 t2 ...]   (default: 8 evenly spaced times)
Two rows: side view (perpendicular to the attack line, from the attacker's right) and a high 3/4 view.
Red = attacker, grey = victim (head darker). Needs numpy + Pillow."""
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "clips")
import pair  # noqa: E402
import rig  # noqa: E402

FACES = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
COL = {"attacker": np.array([200, 52, 62]), "victim": np.array([210, 210, 220]), "face": np.array([255, 205, 40])}
CELL, SCALE = 300, 34  # pixels per cell, pixels per stud
BG, FLOOR = (27, 29, 36), (58, 60, 72)


def view(yaw, pitch):
    y, p = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(y), 0, -np.sin(y)], [0, 1, 0], [np.sin(y), 0, np.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    return Rx @ Ry


def frame_at(frames, t):
    return min(frames, key=lambda f: abs(f[0] - t))[1]


def cell(boxes, V, label, cx):
    im = Image.new("RGB", (CELL, CELL), BG)
    d = ImageDraw.Draw(im)
    o = np.array([CELL / 2 - cx * SCALE, CELL * 0.58])

    def px(P):
        return [(float(o[0] + p[0] * SCALE), float(o[1] - p[1] * SCALE)) for p in P]

    fl = np.array([[-5, -3, -7], [5, -3, -7], [5, -3, 4], [-5, -3, 4]], float)
    d.polygon(px((V @ fl.T).T), fill=FLOOR)
    light = np.array([0.4, 0.8, 0.45])
    light /= np.linalg.norm(light)
    faces = []
    for who, pn, corners in boxes:
        C = np.array(corners)
        centre = C.mean(0)
        for f in FACES:
            q = C[list(f)]
            n = np.cross(q[1] - q[0], q[3] - q[0])
            n /= max(1e-9, np.linalg.norm(n))
            if np.dot(n, q.mean(0) - centre) < 0:
                n = -n
            if (V @ n)[2] <= 0:
                continue
            P = (V @ q.T).T
            shade = 0.45 + 0.55 * max(0.0, float(np.dot(n, light)))
            base = COL[who] * (0.7 if pn == "Head" else 1.0)
            faces.append((P[:, 2].mean(), px(P), tuple(int(v) for v in np.clip(base * shade, 0, 255))))
    for _, poly, col in sorted(faces, key=lambda f: f[0]):
        d.polygon(poly, fill=col, outline=(15, 15, 18))
    d.text((6, 4), label, fill=(200, 200, 200))
    return im


def main():
    clip_name, png = sys.argv[1], sys.argv[2]
    mod = __import__(clip_name)
    P = pair.Pair(mod.CLIP)
    baked = {}
    for who in ("attacker", "victim"):
        if who == "attacker" and mod.CLIP.get("external_attacker"):
            continue
        baked[who] = P.bake(who)
    length = mod.CLIP["length"]
    times = [float(x) for x in sys.argv[3:]] or list(np.round(np.linspace(0, length, 8), 2))
    views = [("side", view(90, 0), 1.2), ("3/4", view(40, 30), 0.8)]
    sheet = Image.new("RGB", (CELL * len(times), CELL * len(views)), BG)
    for r, (vname, V, cx) in enumerate(views):
        for c, t in enumerate(times):
            boxes = []
            for who, frames in baked.items():
                for pn, M in rig.fk(frame_at(frames, t), P.bodies[who].hrp).items():
                    boxes.append((who, pn, pair._corners(M, rig.SIZE[pn])))
                    if pn == "Head":  # a nose, so the gaze shows
                        boxes.append(("face", "Nose", pair._corners(M @ rig.cf((0, 0, -0.62)), (0.45, 0.22, 0.3))))
            sheet.paste(cell(boxes, V, f"{t:.2f}s {vname}", cx), (c * CELL, r * CELL))
    sheet.save(png)


if __name__ == "__main__":
    main()
