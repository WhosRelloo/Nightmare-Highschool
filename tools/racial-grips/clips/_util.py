"""Helpers for writing clips: plant feet, put a head on a point, find where the other body is."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rig  # noqa: E402

GROUND = -3.0


def offset_cf(offset):
    return rig.cf(offset["p"], rig.ry(math.radians(offset.get("yaw", 0))))


def pose_of(root, joints=None):
    joints = joints or {}
    p = {"Root": {"p": np.asarray(root["p"], float), "R": rig.euler(root["r"])}}
    for j in rig.LIMBS:
        p[j] = rig.euler(joints.get(j, [0, 0, 0]))
    return p


def corners(frame, size):
    sx, sy, sz = (s / 2 for s in size)
    return [rig.xf(frame, (x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]


def lowest(root, joints, hrp=None, parts=("Right Leg", "Left Leg", "Torso", "Right Arm", "Left Arm", "Head")):
    fr = rig.fk(pose_of(root, joints), hrp)
    return min(c[1] for p in parts for c in corners(fr[p], rig.SIZE[p]))


def plant(root, joints, hrp=None, parts=("Right Leg", "Left Leg"), ground=GROUND):
    """Return root with p.y shifted so the lowest corner of `parts` rests on the ground."""
    low = lowest(root, joints, hrp, parts)
    dy = ground - low
    hy = 0 if hrp is None else 0
    return {"p": [root["p"][0], root["p"][1] + dy + hy, root["p"][2]], "r": root["r"]}


def part_point(offset, root, joints, part, local):
    """World (attacker-space) point on another body's part, for that body at `root`/`joints`."""
    fr = rig.fk(pose_of(root, joints), offset_cf(offset) if offset else None)
    return rig.xf(fr[part], local)


def root_for_head(target, root_r, neck=(0, 0, 0)):
    """Root p (attacker space) that puts this body's head centre on `target`."""
    R = rig.euler(root_r)
    head_local = np.asarray(rig.PIVOT["Neck"]) + rig.euler(neck) @ np.asarray(rig.CENTRE["Neck"])
    return list(np.asarray(target) - R @ head_local)


def r(v, n=3):
    return [round(float(x), n) for x in v]


def reach_gap(root, joints, joint, target, hrp=None):
    """|pivot - target| - limb reach for `joint` (0 = the hand/foot sits exactly on target)."""
    fr_torso = (hrp if hrp is not None else np.eye(4)) @ rig.cf(root["p"], rig.euler(root["r"]))
    piv = rig.xf(fr_torso, rig.PIVOT[joint])
    return float(np.linalg.norm(np.asarray(target) - piv) - np.linalg.norm(rig.END[joint]))


def fit(root, joints, joint, target, vary="y", lo=-2.0, hi=2.0, hrp=None, plant_parts=None):
    """Shift root along `vary` ('x'|'y'|'z' position, or 'lean' = root rotation x in degrees) until the limb reaches
    `target` exactly. With plant_parts, the root is re-planted on the ground after every step (vary must not be 'y')."""
    import copy

    def at(v):
        rr = copy.deepcopy(root)
        if vary == "lean":
            rr["r"] = [v, rr["r"][1], rr["r"][2]]
        else:
            rr["p"] = list(rr["p"])
            rr["p"]["xyz".index(vary)] = v
        if plant_parts:
            rr = plant(rr, joints, parts=plant_parts)
        return rr

    best = None
    for n in range(81):
        v = lo + (hi - lo) * n / 80
        g = abs(reach_gap(at(v), joints, joint, target, hrp))
        if best is None or g < best[0]:
            best = (g, v)
    v0 = best[1]
    step = (hi - lo) / 80
    for _ in range(30):
        cands = [v0 - step, v0, v0 + step]
        v0 = min(cands, key=lambda v: abs(reach_gap(at(v), joints, joint, target, hrp)))
        step /= 2
    out = at(v0)
    out["p"] = [round(float(x), 3) for x in out["p"]]
    out["r"] = [round(float(x), 2) for x in out["r"]]
    return out


def body_point(keys, offset, t, part, local):
    """World point on a Torso/Head of a keyed body at time t (root + neck only, exactly as the baker interpolates)."""
    import pair as _pair
    P = _pair.Pair({"name": "_probe", "length": 1, "offset": offset or {"p": [0, 0, 0]},
                    "attacker": [{"t": 0.0}], "victim": [dict(k) for k in keys]})
    who = "victim"
    return P.target_world("attacker", (who, part, local), t, None)


def fit2(root, joints, a_joint, a_target, b_joint, b_target, a_vary="y", b_vary="lean", a_rng=(-2, 1), b_rng=(-60, 20),
         plant_parts=None, iters=6):
    """Alternate two 1-D fits so two limbs reach two targets (e.g. a knee on the chest and a hand on the collar)."""
    cur = root
    for _ in range(iters):
        cur = fit(cur, joints, a_joint, a_target, vary=a_vary, lo=a_rng[0], hi=a_rng[1])
        cur = fit(cur, joints, b_joint, b_target, vary=b_vary, lo=b_rng[0], hi=b_rng[1], plant_parts=plant_parts)
    return cur
