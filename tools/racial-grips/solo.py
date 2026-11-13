"""One body alone at chosen times, seen from around its own facing (side / front / back / 3-4), for pose checks.
usage: python solo.py <clip> attacker|victim out.png yaw_deg t1 [t2 ...]   (yaw_deg = the direction the body faces)"""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "clips")
import duo  # noqa: E402
import pair  # noqa: E402
import rig  # noqa: E402

mod = __import__(sys.argv[1])
who, png, yaw = sys.argv[2], sys.argv[3], float(sys.argv[4])
times = [float(x) for x in sys.argv[5:]]
P = pair.Pair(mod.CLIP)
frames = P.bake(who)
views = [("side R", 90), ("front", 180), ("back", 0), ("3/4", 140)]
sheet = Image.new("RGB", (duo.CELL * len(views), duo.CELL * len(times)), duo.BG)
for r, t in enumerate(times):
    F = rig.fk(duo.frame_at(frames, t), P.bodies[who].hrp)
    c0 = F["Torso"][:3, 3]
    boxes = []
    for pn, M in F.items():
        M2 = M.copy()
        M2[0, 3] -= c0[0]
        M2[2, 3] -= c0[2]
        boxes.append((who, pn, pair._corners(M2, rig.SIZE[pn])))
        if pn == "Head":
            boxes.append(("face", "Nose", pair._corners(M2 @ rig.cf((0, 0, -0.62)), (0.45, 0.22, 0.3))))
    for c, (nm, vy) in enumerate(views):
        V = duo.view(vy - yaw, 6 if nm != "3/4" else 22)
        sheet.paste(duo.cell(boxes, V, f"{t:.2f}s {nm}", 0), (c * duo.CELL, r * duo.CELL))
sheet.save(png)
