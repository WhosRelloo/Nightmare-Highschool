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


# ---------------------------------------------------------------- planted legs (no floating / jutting legs)
def foot(x, z, slide=0.7, y=GROUND):
    """A leg whose sole stays on a fixed floor point (attacker space), sliding along z to its exact reach."""
    return {"reach": ("world", None, [x, y, z]), "slide": [0, 0, slide]}


# The kneel = the game's own crouch (ReplicatedStorage.Assets.Animations...Movement.Crouch, rbxassetid://139672322709288,
# the 171-key "Crouch idle" in NH Combat Test's Workspace), frame 0, evaluated on a default R6 rig, part frames relative
# to a STANDING HRP (the crouch never changes HipHeight). Owner's ground logic, as in the crouch and the "Kneel Example"
# model: the HRP stays at standing height; the torso drops (0.9) and leans in; the front leg stands near vertical a
# stud ahead; the back leg slants back and out and its knee/shin presses ~0.4 into the floor so it reads as resting
# on it. Legs slide off their sockets (Pose translation) to fake the folded knee. Native front leg = LEFT.
CROUCH_TORSO = ((0.0, -0.904, -0.086), (-27.49, -21.89, -3.41))
CROUCH_FRONT = ((-0.500, -2.138, -1.199), (5.05, 0.0, 0.0))        # Left Leg
CROUCH_BACK = ((0.713, -2.231, 0.154), (-57.71, -41.82, -14.67))    # Right Leg
_MIRROR = np.diag([-1.0, 1.0, 1.0, 1.0])


def _crouch(part, front):
    p, r = {"torso": CROUCH_TORSO, "front": CROUCH_FRONT, "back": CROUCH_BACK}[part]
    M = rig.cf(p, rig.euler(r))
    return _MIRROR @ M @ _MIRROR if front == "RightHip" else M  # right foot ahead = the crouch mirrored


def kneel_anchor(x, z, yaw_deg=0.0):
    """The standing HRP the crouch is played on, at (x, z) facing yaw_deg (attacker space)."""
    return rig.cf((x, 0.0, z), rig.ry(math.radians(yaw_deg)))


def kneel_legs(x, z, yaw_deg=0.0, front="LeftHip", kid="kneel"):
    """Both legs planted exactly as the game's crouch, for a crouch played at (x, z, yaw). The legs stay put in the
    world while the torso leans/turns (the generator re-solves rotation + tuck every frame)."""
    A = kneel_anchor(x, z, yaw_deg)
    back = "LeftHip" if front == "RightHip" else "RightHip"
    return {front: {"plant": A @ _crouch("front", front), "id": kid},
            back: {"plant": A @ _crouch("back", front), "id": kid}}


def kneel_root(x, z, yaw_deg=0.0, lean=0.0, turn=0.0, roll=0.0, front="LeftHip", sink=0.0):
    """Torso of the crouch at (x, z, yaw), with extra lean (negative = further forward) / turn / roll about its hip
    line, so the tucked legs stay attached however it bends. sink lowers the hips onto the planted legs (weight
    committing into a strike); the legs' tuck takes it up."""
    A = kneel_anchor(x, z, yaw_deg)
    T = _crouch("torso", front)
    hip = rig.xf(T, (0, -1.0, 0)) - np.array([0, sink, 0])
    Rn = rig.ry(math.radians(turn)) @ rig.rx(math.radians(lean)) @ rig.rz(math.radians(roll)) @ T[:3, :3]
    pn = hip - Rn @ np.array([0, -1.0, 0])
    W = A @ rig.cf(pn, Rn)
    return {"p": [round(float(v), 4) for v in W[:3, 3]], "r": [round(float(v), 3) for v in rig.to_euler(W[:3, :3])]}


def kneel_fit(x, z, yaw_deg, joint, target, turn=0.0, roll=0.0, rng=(-25.0, 15.0), front="LeftHip", sink=0.0):
    """Crouch root leaning (extra, within rng) just enough that `joint`'s hand reaches `target` (attacker space)."""
    lo, hi = rng

    def gap(v):
        return abs(reach_gap(kneel_root(x, z, yaw_deg, max(lo, min(hi, v)), turn, roll, front, sink), {}, joint, target))
    best = min((lo + (hi - lo) * n / 80 for n in range(81)), key=gap)
    step = (hi - lo) / 80
    for _ in range(20):
        best = max(lo, min(hi, min((best - step, best, best + step), key=gap)))
        step /= 2
    out = kneel_root(x, z, yaw_deg, best, turn, roll, front, sink)
    out["_lean"] = best  # the extra lean that was needed (callers may add to it)
    return out


def stand_legs(cx, cz, yaw_deg=0.0, stance=0.6, spread=0.35):
    """Both soles planted, feet slightly apart and staggered."""
    import math as _m
    a = _m.radians(yaw_deg)

    def w(dx, dz):
        return [cx + dx * _m.cos(a) + dz * _m.sin(a), GROUND, cz - dx * _m.sin(a) + dz * _m.cos(a)]
    return {"RightHip": {"reach": ("world", None, w(stance, -spread)), "slide": [0.2, 0, 0.3]},
            "LeftHip": {"reach": ("world", None, w(-stance, spread)), "slide": [0.2, 0, 0.3]}}


def root_for_legs(root, legs, lo=-2.4, hi=0.6):
    """Root height so the first leg in `legs` reaches its floor point exactly (the other slides)."""
    j = next(iter(legs))
    tgt = legs[j]["reach"][2]
    return fit(root, {}, j, tgt, vary="y", lo=lo, hi=hi)


def heels(offset, lie_root, slide_axis, slide=0.9, lift=0.42):
    """Heel points on the floor where the lying body's feet rest, as world reach specs for both hips: the legs stay
    stretched along the floor while the chest arches or lifts. slide_axis: attacker-space direction of the body."""
    out = {}
    for j, part in (("RightHip", "Right Leg"), ("LeftHip", "Left Leg")):
        p = part_point(offset, lie_root, {}, part, (0, -1.0, 0))
        out[j] = {"reach": ("world", None, [float(p[0]), GROUND + lift, float(p[2])]),
                  "slide": [slide_axis[0] * slide, 0, slide_axis[2] * slide]}
    return out


# ---------------------------------------------------------------- heads that look at what the body is doing
def look(body, part, local=(0, 0, 0), tilt=(0, 0, 0)):
    """Neck spec: aim the face at a point on the other body ("victim"/"attacker", "Torso" or "Head") with an
    expressive tilt on top (degrees: x = nod up, y = turn left, z = roll). Solved every frame by pair.py."""
    return {"look": (body, part, list(local)), "tilt": list(tilt)}


def set_necks(keys, table):
    """Put the neck spec table[t] on the key at time t (the key must exist)."""
    for t, spec in table.items():
        k = next((k for k in keys if abs(k["t"] - t) < 1e-6), None)
        if k is None:
            raise ValueError(f"no key at t={t}")
        k["Neck"] = spec
