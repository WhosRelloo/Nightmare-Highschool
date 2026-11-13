"""The game's own fist clips as poses: the baseline every new fist move starts from and ends on.

ref/*.txt are the live clips exported to body space (see README): one line per keyframe,
`t;Root=x,y,z|rx,ry,rz;Neck=..;RightShoulder=..;RightShoulder_o=x,y,z;...` (XYZ Euler degrees, the racial grips
generator's convention: x right, y up, z back; Root -x leans forward; shoulder/hip +x swings the limb forward).
`<Joint>_o` is the limb's Pose position (its slide off the socket, in the joint's own space): the owner's fist clips
pull the arms in ~1.2 studs and tuck the legs (Moon-style fake elbows and knees), so new clips carry the same offsets
or every seam would jump by a stud.
"""
import copy
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RG = os.path.join(os.path.dirname(HERE), "racial-grips")
for p in (os.path.join(HERE, "clips"), RG, os.path.join(RG, "clips")):
    if p not in sys.path:
        sys.path.insert(0, p)

import rig  # noqa: E402

JOINTS = ["Neck", "RightShoulder", "LeftShoulder", "RightHip", "LeftHip"]
LIMBS = ["RightShoulder", "LeftShoulder", "RightHip", "LeftHip"]
ZERO = {j: [0.0, 0.0, 0.0] for j in LIMBS}
# the R6 limb joints' C0 turn (about Y): a Pose position in joint space -> torso space
_C0Y = {"RightShoulder": 90, "LeftShoulder": -90, "RightHip": 90, "LeftHip": -90}
# animpro's groundContact check can't see limb slides (and the baseline breaks it), so the fist clips waive it;
# grounding is done here, with the slides (plant)
WAIVE = "groundContact"
_cache = {}


def torso_off(joint, o):
    return rig.ry(math.radians(_C0Y[joint])) @ np.asarray(o, float)


def load(name):
    if name in _cache:
        return _cache[name]
    keys = []
    for line in open(os.path.join(HERE, "ref", name + ".txt"), encoding="utf-8"):
        line = line.split("  #")[0].split("  ~")[0].strip()
        if not line or line.startswith("@"):
            continue
        if "truncated" in line:
            break  # a long looping clip (idle, block) can come back cut off from Studio: its start is all we use
        t, *parts = line.split(";")
        k = {"t": round(float(t), 4), "_o": {}}
        for p in parts:
            if "=" not in p:
                continue
            j, v = p.split("=", 1)
            if j == "Root":
                pos, rot = v.split("|")
                k["Root"] = {"p": [float(x) for x in pos.split(",")], "r": [float(x) for x in rot.split(",")]}
            elif j.endswith("_o"):
                k["_o"][j[:-2]] = [float(x) for x in v.split(",")]
            else:
                k[j] = [float(x) for x in v.split(",")]
        keys.append(k)
    _cache[name] = keys
    return keys


def pose(name, t):
    """The clip's full pose at time t (its latest key at or before t), with its limb slides in "_o"."""
    out = {"_o": copy.deepcopy(ZERO)}
    for k in load(name):
        if k["t"] > t + 1e-6:
            break
        for j, v in k.items():
            if j == "t":
                continue
            if j == "_o":
                # a key lists the slides it has; a limb keyed without one is back on its socket
                for lj in LIMBS:
                    if lj in k:
                        out["_o"][lj] = list(v.get(lj, [0.0, 0.0, 0.0]))
            else:
                out[j] = copy.deepcopy(v)
    return out


def frames_of(root, joints, offs):
    m = {"Root": {"p": np.array(root["p"], float), "R": rig.euler(root["r"])}}
    for j in JOINTS:
        m[j] = rig.euler(joints.get(j, [0, 0, 0]))
    for j in LIMBS:
        m[j + "_off"] = torso_off(j, (offs or ZERO).get(j, [0, 0, 0]))
    return rig.fk(m, np.eye(4))


def sole(root, joints, offs):
    fr = frames_of(root, joints, offs)
    lo = 1e9
    for pn in ("Right Leg", "Left Leg"):
        sx, sy, sz = (s / 2 for s in rig.SIZE[pn])
        for x in (-sx, sx):
            for y in (-sy, sy):
                for z in (-sz, sz):
                    lo = min(lo, rig.xf(fr[pn], (x, y, z))[1])
    return lo


def plant(root, joints, offs, ground):
    d = ground - sole(root, joints, offs)
    return {"p": [root["p"][0], root["p"][1] + d, root["p"][2]], "r": root["r"]}


def key(t, base, root=None, ground=False, offs=None, **joints):
    """A full key at time t: `base` (a pose dict) with `root` ({"p":..., "r":...}, either part), limb slides `offs`
    ({joint: [x, y, z]}) and joints replaced. ground=True re-plants: the lower sole at the idle's sole height."""
    k = {"t": t}
    for j, v in copy.deepcopy(base).items():
        k[j] = v
    k.setdefault("_o", copy.deepcopy(ZERO))
    if root:
        r = k.get("Root", {"p": [0, 0, 0], "r": [0, 0, 0]})
        k["Root"] = {"p": list(root.get("p", r["p"])), "r": list(root.get("r", r["r"]))}
    for j, v in (offs or {}).items():
        k["_o"][j] = list(v)
    for j, v in joints.items():
        k[j] = list(v)
    if ground:
        k["Root"] = plant(k["Root"], {j: k[j] for j in JOINTS}, k["_o"], SOLE)
    return k


def blend(a, b, w, weights=None):
    """Pose between a and b: each joint slerped by w (or weights[joint]); Root position and limb slides lerped. For
    breakdowns that unwind out of a baseline pose instead of snapping to the next key."""
    out = {"_o": {}}
    for j in ["Root"] + JOINTS:
        wj = (weights or {}).get(j, w)
        if j == "Root":
            ra, rb = rig.mat2q(rig.euler(a["Root"]["r"])), rig.mat2q(rig.euler(b["Root"]["r"]))
            p = [pa + (pb - pa) * wj for pa, pb in zip(a["Root"]["p"], b["Root"]["p"])]
        else:
            ra, rb = rig.mat2q(rig.euler(a[j])), rig.mat2q(rig.euler(b[j]))
        if float(np.dot(ra, rb)) < 0:
            rb = -rb
        th = np.arccos(min(1.0, float(np.dot(ra, rb))))
        q = ra if th < 1e-6 else (np.sin((1 - wj) * th) * ra + np.sin(wj * th) * rb) / np.sin(th)
        e = rig.to_euler(rig.q2mat(q / np.linalg.norm(q)))
        out[j] = {"p": p, "r": e} if j == "Root" else e
    for j in LIMBS:
        wj = (weights or {}).get(j, w)
        oa = (a.get("_o") or ZERO).get(j, [0, 0, 0])
        ob = (b.get("_o") or ZERO).get(j, [0, 0, 0])
        out["_o"][j] = [x + (y - x) * wj for x, y in zip(oa, ob)]
    return out


def split(keys):
    """Generator keys (rotations only) and the limb-slide track [(t, {joint: [x, y, z]})] baked separately (bake_offs)."""
    gen, offs = [], []
    for k in keys:
        gen.append({j: v for j, v in k.items() if j != "_o"})
        offs.append((k["t"], copy.deepcopy(k.get("_o", ZERO))))
    return gen, offs


def _pchip(ts, ys, t):
    """Monotone cubic (Fritsch-Carlson) through (ts, ys) at t: eases like the rotation splines, never overshoots."""
    n = len(ts)
    if t <= ts[0]:
        return ys[0]
    if t >= ts[-1]:
        return ys[-1]
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = max(j for j in range(n - 1) if ts[j] <= t)
    s = (t - ts[i]) / h[i]
    h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


def bake_offs(offs, length, fps=30):
    """Per-frame limb slides {frame: {part: [x, y, z]}} (Pose positions), for pack.py."""
    ts = [t for t, _ in offs]
    out = {}
    for f in range(int(round(length * fps)) + 1):
        t = f / fps
        row = {}
        for j in LIMBS:
            row[rig.PART_OF[j]] = [round(_pchip(ts, [o[j][c] for _, o in offs], t), 4) for c in range(3)]
        out[str(f)] = row
    return out


IDLE = pose("Idle", 0.0)
# the idle's own sole height, slides included: new keys are planted here so the body keeps the clips' height
SOLE = sole(IDLE["Root"], {j: IDLE[j] for j in JOINTS}, IDLE["_o"])


def slide(joint, x, y, z):
    """A limb slide given in torso space (x right, y up, z back), as the joint-space Pose position the clips store."""
    return [round(float(v), 4) for v in rig.ry(math.radians(_C0Y[joint])).T @ np.array([x, y, z], float)]


def offs(right=None, left=None, rleg=None, lleg=None):
    """Limb slides for a key from torso-space triples; a limb left out keeps the idle's slide."""
    o = copy.deepcopy(IDLE["_o"])
    for j, v in (("RightShoulder", right), ("LeftShoulder", left), ("RightHip", rleg), ("LeftHip", lleg)):
        if v is not None:
            o[j] = slide(j, *v)
    return o
