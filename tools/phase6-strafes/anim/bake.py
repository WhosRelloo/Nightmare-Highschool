"""phase6-strafes clip baker (R3 / R8). Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §2.

  python -X utf8 bake.py            reads recipes.json + src/*.json, writes out/<Name>.lua, out/manifest.json, REPORT.md

Clips are R6 KeyframeSequences extracted read-only from the FIER ANIMATIONS place (extract_fier.luau). Internally a clip
is a time array and, per joint, an (N, 4, 4) array of Motor6D Pose CFrames. Joint offsets (C0 / C1) are the standard R6
ones from tools/tutorial-anim/rigs.json (the FIER rigs use the same).
Torso pose space: X sideways, Y forward/back, Z up (RootJoint C0 maps pose Z to world Y).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RIGS = os.path.join(HERE, "..", "..", "tutorial-anim", "rigs.json")
JOINTS = ["Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg"]
MOTOR = {"Torso": "RootJoint", "Head": "Neck", "Left Arm": "Left Shoulder", "Right Arm": "Right Shoulder",
         "Left Leg": "Left Hip", "Right Leg": "Right Hip"}
WEIGHT = {"Torso": 2.0, "Head": 0.4, "Left Arm": 0.8, "Right Arm": 0.8, "Left Leg": 1.2, "Right Leg": 1.2}
PLACE_ID = 98950102230473


# ------------------------------------------------------------------ matrices

def M(c):
    """Roblox CFrame components (x, y, z, R00..R22) -> 4x4"""
    m = np.eye(4)
    m[:3, 3] = c[:3]
    m[:3, :3] = np.array(c[3:12], dtype=float).reshape(3, 3)
    return m


def comps(m):
    return [float(m[0, 3]), float(m[1, 3]), float(m[2, 3])] + [float(v) for v in m[:3, :3].reshape(-1)]


def inv(m):
    r = np.eye(4)
    r[:3, :3] = m[:3, :3].T
    r[:3, 3] = -m[:3, :3].T @ m[:3, 3]
    return r


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def mat(rx=0.0, ry=0.0, rz=0.0, pos=(0.0, 0.0, 0.0)):
    m = np.eye(4)
    m[:3, :3] = Rz(rz) @ Ry(ry) @ Rx(rx)
    m[:3, 3] = pos
    return m


def rot_angle(a, b):
    """the angle (radians) between two rotations (3x3 or 4x4)"""
    r = a[:3, :3].T @ b[:3, :3]
    return math.acos(max(-1.0, min(1.0, (np.trace(r) - 1) / 2)))


def rot_angle_deg(a, b):
    return math.degrees(rot_angle(a, b))


def mat_to_q(r):
    r = r[:3, :3]
    t = np.trace(r)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [(r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s, 0.25 * s]
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        q = [0.25 * s, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s, (r[2, 1] - r[1, 2]) / s]
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        q = [(r[0, 1] + r[1, 0]) / s, 0.25 * s, (r[1, 2] + r[2, 1]) / s, (r[0, 2] - r[2, 0]) / s]
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        q = [(r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, 0.25 * s, (r[1, 0] - r[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def q_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        r = a + (b - a) * t
        return r / np.linalg.norm(r)
    th = math.acos(min(1.0, d))
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


def interp(a, b, u):
    """blend two 4x4 poses: slerp the rotation, lerp the translation"""
    m = np.eye(4)
    m[:3, :3] = q_to_mat(slerp(mat_to_q(a), mat_to_q(b), u))
    m[:3, 3] = a[:3, 3] * (1 - u) + b[:3, 3] * u
    return m


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def _load_rig():
    r = json.load(open(RIGS, encoding="utf-8"))["R6Block"]["motors"]
    return {k: (M(v["C0"]), M(v["C1"])) for k, v in r.items()}


R6M = _load_rig()


# ------------------------------------------------------------------ the clip

class Clip:
    def __init__(self, name, t, P, loop=False, priority="Action"):
        self.name = name
        self.t = np.array(t, dtype=float)
        self.P = {j: np.array(v, dtype=float) for j, v in P.items()}
        self.loop = loop
        self.priority = priority

    @property
    def n(self):
        return len(self.t)

    def length(self):
        return float(self.t[-1] - self.t[0]) if self.n > 1 else 0.0

    def fps(self):
        return 1.0 / float(np.median(np.diff(self.t))) if self.n > 1 else 30.0

    def copy(self, name=None):
        return Clip(name or self.name, self.t.copy(), {j: v.copy() for j, v in self.P.items()}, self.loop, self.priority)

    def pose(self, j, i):
        return self.P[j][i] if j in self.P else np.eye(4)

    def sub(self, a, b, name=None):
        """frames a..b inclusive, retimed from 0"""
        c = Clip(name or self.name, self.t[a:b + 1] - self.t[a], {j: v[a:b + 1].copy() for j, v in self.P.items()},
                 self.loop, self.priority)
        return c


def torso_world(c, i):
    c0, c1 = R6M["RootJoint"]
    return c0 @ c.pose("Torso", i) @ inv(c1)


def joint_world(c, i, j, torso=None):
    torso = torso_world(c, i) if torso is None else torso
    c0, c1 = R6M[MOTOR[j]]
    return torso @ c0 @ c.pose(j, i) @ inv(c1)


def fk(c, i):
    """world transforms (root at the origin) of the torso, head and legs, plus the foot points lf / rf"""
    T = torso_world(c, i)
    out = {"Torso": T}
    for j in ("Head", "Left Leg", "Right Leg"):
        out[j] = joint_world(c, i, j, T)
    out["lf"] = (out["Left Leg"] @ np.array([0, -1.0, 0, 1]))[:3]
    out["rf"] = (out["Right Leg"] @ np.array([0, -1.0, 0, 1]))[:3]
    return out


def yaw_of_pose(m):
    v = m[:3, :3] @ np.array([1.0, 0.0, 0.0])
    return math.atan2(v[1], v[0])


def torso_yaw_deg(c, i):
    return math.degrees(yaw_of_pose(c.pose("Torso", i)))


def world_yaw(m):
    look = m[:3, :3] @ np.array([0.0, 0.0, -1.0])
    return math.atan2(-look[0], -look[2])


def head_yaw_deg(c, i):
    return math.degrees(world_yaw(fk(c, i)["Head"]))


def frame_distance(a, i, b, j):
    d = 0.0
    for k in set(a.P) & set(b.P):
        d += WEIGHT.get(k, 1.0) * rot_angle(a.P[k][i], b.P[k][j]) + float(np.linalg.norm(a.P[k][i][:3, 3] - b.P[k][j][:3, 3]))
    return d


def seam(c):
    return max(rot_angle_deg(c.P[j][0], c.P[j][-1]) for j in c.P)


# ------------------------------------------------------------------ measurements

def feet(c):
    return [(fk(c, i)["lf"], fk(c, i)["rf"]) for i in range(c.n)]


def lowest_foot(c):
    return min(min(l[1], r[1]) for l, r in feet(c))


def stance_speed(c):
    F = feet(c)
    dist, tt = 0.0, 0.0
    for i in range(1, c.n):
        li = 0 if F[i][0][1] < F[i][1][1] else 1
        lp = 0 if F[i - 1][0][1] < F[i - 1][1][1] else 1
        if li == lp:
            d = F[i][li] - F[i - 1][li]
            dist += math.hypot(d[0], d[2])
            tt += c.t[i] - c.t[i - 1]
    return dist / tt if tt > 0 else 0.0


def max_spread(c):
    return max(math.hypot(l[0] - r[0], l[2] - r[2]) for l, r in feet(c))


def stride(c):
    return 2 * max_spread(c) / max(c.length(), 1e-6)


def contact_phase(c):
    F = feet(c)
    for i in range(1, c.n):
        if F[i][0][1] < F[i][1][1] and not (F[i - 1][0][1] < F[i - 1][1][1]):
            return float((c.t[i] - c.t[0]) / max(c.length(), 1e-6)) % 1.0
    return 0.0


def _stance_runs(c, F, side, band=0.08):
    low = min(min(l[1], r[1]) for l, r in F)
    runs, cur = [], []
    for i in range(c.n):
        me, other = F[i][side], F[i][1 - side]
        if me[1] <= other[1] and me[1] <= low + band:
            cur.append(i)
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    return runs


def stance_jitter(c):
    """the largest horizontal deviation of a planted foot from a straight constant-speed line between its contact ends"""
    F = feet(c)
    worst = 0.0
    for side in (0, 1):
        for run in _stance_runs(c, F, side):
            s, e = run[0], run[-1]
            for i in run:
                u = (c.t[i] - c.t[s]) / max(c.t[e] - c.t[s], 1e-9)
                g = F[s][side] + (F[e][side] - F[s][side]) * u
                worst = max(worst, math.hypot(F[i][side][0] - g[0], F[i][side][2] - g[2]))
    return worst


def resample_at(c, j, t):
    i = int(np.searchsorted(c.t, t, side="right") - 1)
    i = max(0, min(c.n - 2, i))
    u = (t - c.t[i]) / max(c.t[i + 1] - c.t[i], 1e-9)
    return interp(c.P[j][i], c.P[j][i + 1], min(1.0, max(0.0, u)))


def max_joint_error(src, out):
    worst = 0.0
    for i in range(src.n):
        for j in src.P:
            if j in out.P:
                worst = max(worst, rot_angle_deg(src.P[j][i], resample_at(out, j, src.t[i] - src.t[0] + out.t[0])))
    return worst


def deepest_drop(c):
    return min(float(c.P["Torso"][i][2, 3]) for i in range(c.n)) if "Torso" in c.P else 0.0


# ------------------------------------------------------------------ transforms

def square_chest(c, keep_yaw=0.0):
    """remove the torso's yaw (to keep_yaw degrees); the legs keep their world rotation about their own pivots, the head
    turns to face forward; the arms ride with the torso"""
    out = c.copy()
    c0r, c1r = R6M["RootJoint"]
    for i in range(c.n):
        P = c.pose("Torso", i)
        q = yaw_of_pose(P)
        Pn = P.copy()
        Pn[:3, :3] = Rz(-q + math.radians(keep_yaw)) @ P[:3, :3]
        out.P["Torso"][i] = Pn
        Tw = (c0r @ P @ inv(c1r))[:3, :3]
        Tn = (c0r @ Pn @ inv(c1r))[:3, :3]
        for leg in ("Left Leg", "Right Leg"):
            if leg not in c.P:
                continue
            h0, h1 = R6M[MOTOR[leg]]
            L = c.P[leg][i]
            Lw = Tw @ h0[:3, :3] @ L[:3, :3] @ h1[:3, :3].T
            Ln = L.copy()
            Ln[:3, :3] = h0[:3, :3].T @ Tn.T @ Lw @ h1[:3, :3]
            out.P[leg][i] = Ln
        if "Head" in c.P:
            n0, n1 = R6M["Neck"]
            H = c.P["Head"][i]
            Hw = Tn @ n0[:3, :3] @ H[:3, :3] @ n1[:3, :3].T
            m = np.eye(4)
            m[:3, :3] = Hw
            Hw2 = Ry(-world_yaw(m)) @ Hw
            Hn = H.copy()
            Hn[:3, :3] = n0[:3, :3].T @ Tn.T @ Hw2 @ n1[:3, :3]
            out.P["Head"][i] = Hn
    return out


def foot_lock(c, band=0.08):
    """plant each stance foot: during a contact run its horizontal track is made a straight constant-speed line between
    the run's ends (the leg turns about its own pivot; its length is kept)"""
    out = c.copy()
    F = feet(c)
    for side, leg in ((0, "Left Leg"), (1, "Right Leg")):
        h0, h1 = R6M[MOTOR[leg]]
        for run in _stance_runs(c, F, side, band):
            s, e = run[0], run[-1]
            for i in run:
                u = (c.t[i] - c.t[s]) / max(c.t[e] - c.t[s], 1e-9)
                g = F[s][side] + (F[e][side] - F[s][side]) * u
                T = torso_world(out, i)
                L = out.P[leg][i]
                pivot = (T @ h0 @ np.block([[np.eye(3), L[:3, 3:4]], [np.zeros((1, 3)), np.ones((1, 1))]]))[:3, 3]
                f = F[i][side]
                v0 = f - pivot
                r = np.linalg.norm(v0)
                dx, dz = g[0] - pivot[0], g[2] - pivot[2]
                rem = r * r - dx * dx - dz * dz
                if rem <= 0:
                    continue
                v1 = np.array([dx, -math.sqrt(rem) if v0[1] < 0 else math.sqrt(rem), dz])
                a, b = v0 / r, v1 / np.linalg.norm(v1)
                ax = np.cross(a, b)
                sn, cs = np.linalg.norm(ax), float(np.dot(a, b))
                if sn < 1e-9:
                    continue
                k = ax / sn
                K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
                Rc = np.eye(3) + sn * K + (1 - cs) * (K @ K)
                Tr = T[:3, :3]
                Lw = Tr @ h0[:3, :3] @ L[:3, :3] @ h1[:3, :3].T
                Ln = L.copy()
                Ln[:3, :3] = h0[:3, :3].T @ Tr.T @ (Rc @ Lw) @ h1[:3, :3]
                out.P[leg][i] = Ln
    return out


def _band_run(c, drop_max):
    best, cur = [], []
    for i in range(c.n):
        if c.P["Torso"][i][2, 3] <= drop_max:
            cur.append(i)
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    if len(cur) > len(best):
        best = cur
    return best


def _make_loop(c, a, b, nb):
    seg = c.sub(a, b, c.name)
    n = seg.n
    for j in seg.P:
        for k in range(nb):
            idx = n - nb + k
            w = smoothstep((k + 1) / nb)
            seg.P[j][idx] = interp(seg.P[j][idx], c.P[j][a - nb + 1 + k], w)
    seg.loop = True
    return seg


def loop_cut(c, drop_max=-0.8, min_len=3.0, blend=0.3):
    run = _band_run(c, drop_max)
    if not run:
        raise ValueError("no frames in the drop band")
    nb = max(2, int(round(blend * c.fps())))
    lo, hi = run[0] + nb, run[-1]
    best = None
    for a in range(lo, hi + 1):
        for b in range(a + 1, hi + 1):
            if c.t[b] - c.t[a] < min_len:
                continue
            d = frame_distance(c, a, c, b)
            if best is None or d < best[0]:
                best = (d, a, b)
    if best is None:
        raise ValueError("no window of %.2f s inside the band" % min_len)
    _, a, b = best
    return _make_loop(c, a, b, nb), a, b


def _retime_ease(t, ease=0.2):
    """content time -> play time with a gentle start (motion speed ramps 0 -> 1 over `ease` seconds)"""
    out = []
    for c in t:
        out.append(math.sqrt(2 * ease * c) if c < ease / 2 else c + ease / 2)
    return np.array(out)


def split(c, a, b, blend=0.3, slow=1.15, ease=0.2):
    """Praying: Loop (a..b, seamless back to a), StandUp (from a's pose into b..end), KneelIn (the stand-up reversed,
    slower, eased in).
    Every switch is frame-identical: KneelIn ends on frame a, Loop starts and ends on a, StandUp starts on a."""
    nb = max(2, int(round(blend * c.fps())))
    loop = _make_loop(c, a, b, nb)
    # the stand-up leaves the loop from where the loop ends (frame a's pose) and eases into the source from frame b on,
    # so it starts on an identical frame without replaying the kneel
    stand = c.sub(b, c.n - 1)
    for j in stand.P:
        for k in range(min(nb, stand.n)):
            w = smoothstep(k / nb)
            stand.P[j][k] = interp(c.P[j][a], stand.P[j][k], w)
    stand.loop = False
    rev_P = {j: v[::-1].copy() for j, v in stand.P.items()}
    rev_t = (stand.t[-1] - stand.t[::-1]) * slow
    kneel = Clip(c.name, _retime_ease(rev_t, ease), rev_P)
    return {"KneelIn": kneel, "Loop": loop, "StandUp": stand}


def upper_body(c):
    out = c.copy()
    for j in ("Torso", "Left Leg", "Right Leg"):
        out.P.pop(j, None)
    return out


def scale(c, k):
    out = c.copy()
    for j in out.P:
        out.P[j][:, :3, 3] *= k
    return out


def strip_root(c, yaw=False, hz=10.0):
    """move the torso's horizontal travel (and, with yaw, its spin about the vertical) out of the clip into a carry
    curve [[t, dx, dz, dyaw_deg], ...] in root space (relative to the first frame), sampled at hz"""
    out = c.copy()
    c0r = R6M["RootJoint"][0][:3, :3]
    t0 = c.P["Torso"][0][:3, 3].copy()
    q0 = yaw_of_pose(c.P["Torso"][0])
    rows, prev_q, acc = [], q0, 0.0
    for i in range(c.n):
        P = c.P["Torso"][i]
        d = P[:3, 3] - t0
        w = c0r @ np.array([d[0], d[1], 0.0])
        q = yaw_of_pose(P)
        dq = math.atan2(math.sin(q - prev_q), math.cos(q - prev_q))
        acc += dq
        prev_q = q
        Pn = P.copy()
        Pn[0, 3], Pn[1, 3] = t0[0], t0[1]
        if yaw:
            Pn[:3, :3] = Rz(-acc) @ P[:3, :3]
        out.P["Torso"][i] = Pn
        rows.append([float(c.t[i] - c.t[0]), float(w[0]), float(w[2]), math.degrees(acc) if yaw else 0.0])
    step = 1.0 / hz
    carry, nxt = [], 0.0
    for r in rows:
        if r[0] + 1e-9 >= nxt:
            carry.append([round(v, 4) for v in r])
            nxt += step
    if carry[-1][0] != round(rows[-1][0], 4):
        carry.append([round(v, 4) for v in rows[-1]])
    return out, carry


def decimate(c, fps):
    L = c.length()
    t = list(np.arange(0.0, L, 1.0 / fps))
    if L - t[-1] > 1e-6:
        t.append(L)
    t = np.array(t)
    P = {j: np.array([resample_at(c, j, c.t[0] + x) for x in t]) for j in c.P}
    return Clip(c.name, t, P, c.loop, c.priority)


# ------------------------------------------------------------------ I/O

def to_json(c):
    return {"name": c.name, "loop": c.loop, "priority": c.priority,
            "frames": [{"t": float(c.t[i]), "poses": {j: {"cf": comps(c.P[j][i]), "w": 1} for j in c.P}} for i in range(c.n)]}


def from_json(d):
    frames = sorted(d["frames"], key=lambda f: f["t"])
    joints = [j for j in JOINTS if any(j in f["poses"] for f in frames)]
    t = [f["t"] for f in frames]
    P = {}
    for j in joints:
        arr, last = [], np.eye(4)
        for f in frames:
            p = f["poses"].get(j)
            if p is not None:
                last = M(p["cf"])
            arr.append(last)
        P[j] = np.array(arr)
    return Clip(d.get("name", "clip"), t, P, bool(d.get("loop", False)), d.get("priority", "Action"))


def r4(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def emit_lua(c, name, loop, priority, folder="NHGestures", publish="Gestures"):
    lines = []
    for i in range(c.n):
        parts = []
        for j in JOINTS:
            if j not in c.P:
                continue
            m = c.P[j][i]
            q = mat_to_q(m)
            parts.append(f"{j}=" + ",".join(r4(x) for x in [*q, *m[:3, 3]]))
        lines.append(r4(c.t[i] - c.t[0]) + ";" + ";".join(parts))
    data = "\n".join(lines)
    return f'''-- Generated by tools/phase6-strafes/anim/bake.py (R6). Builds {name} in ServerStorage.{folder} and a copy in
-- ServerStorage.NHPublish.{publish} (the owner publishes those to group 15981569). NH Combat Test only.
if game.PlaceId ~= {PLACE_ID} and game.PlaceId ~= 0 then return "REFUSED: not NH Combat Test (" .. game.PlaceId .. ")" end
local DATA = [==[
{data}
]==]
local PARENT = {{["Torso"]="HumanoidRootPart",["Head"]="Torso",["Left Arm"]="Torso",["Right Arm"]="Torso",["Left Leg"]="Torso",["Right Leg"]="Torso"}}
local seq = Instance.new("KeyframeSequence")
seq.Name = "{name}"
seq.Loop = {"true" if loop else "false"}
seq.Priority = Enum.AnimationPriority.{priority}
for line in string.gmatch(DATA, "[^\\n]+") do
	local t, rest = string.match(line, "^([^;]+);?(.*)$")
	local kf = Instance.new("Keyframe")
	kf.Time = tonumber(t)
	local poses = {{}}
	local function ensure(part)
		local p = poses[part]
		if p then return p end
		p = Instance.new("Pose")
		p.Name = part
		p.Weight = 0
		p.EasingStyle = Enum.PoseEasingStyle.Linear
		poses[part] = p
		local par = PARENT[part]
		p.Parent = if par then ensure(par) else kf
		return p
	end
	ensure("HumanoidRootPart")
	for part, vals in string.gmatch(rest, "([^=;]+)=([^;]+)") do
		local n = {{}}
		for v in string.gmatch(vals, "[^,]+") do table.insert(n, tonumber(v)) end
		local p = ensure(part)
		p.Weight = 1
		p.CFrame = CFrame.new(n[5] or 0, n[6] or 0, n[7] or 0, n[1], n[2], n[3], n[4])
	end
	kf.Parent = seq
end
local SS = game:GetService("ServerStorage")
local function folderAt(path)
	local node = SS
	for name in string.gmatch(path, "[^%.]+") do
		local nx = node:FindFirstChild(name)
		if not nx then nx = Instance.new("Folder") nx.Name = name nx.Parent = node end
		node = nx
	end
	return node
end
for _, path in {{ "{folder}", "NHPublish.{publish}" }} do
	local f = folderAt(path)
	local old = f:FindFirstChild(seq.Name)
	if old then old:Destroy() end
	seq:Clone().Parent = f
end
seq:Destroy()
return string.format("built {name} (%d keyframes, %.3f s)", #SS.{folder}:FindFirstChild("{name}"):GetKeyframes(), {c.length():.3f})
'''


# ------------------------------------------------------------------ main

def _src(name):
    return from_json(json.load(open(os.path.join(HERE, "src", name + ".json"), encoding="utf-8")))


def run_recipe(r):
    """-> list of (name, clip, meta)"""
    c = _src(r["src"])
    meta = {"src": r["src"]}
    outs = []
    pieces = None
    for op, kw in r.get("do", []):
        if op == "square_chest":
            c = square_chest(c, **kw)
        elif op == "foot_lock":
            c = foot_lock(c, **kw)
        elif op == "decimate":
            c = decimate(c, **kw)
        elif op == "upper_body":
            c = upper_body(c)
        elif op == "strip_root":
            c, carry = strip_root(c, **kw)
            meta["Carry"] = carry
        elif op == "loop_cut":
            lc, a, b = loop_cut(c, **kw)
            meta["window"] = [float(c.t[a]), float(c.t[b])]
            pieces = split(c, a, b, blend=kw.get("blend", 0.3))
            c = lc
        else:
            raise ValueError(op)
    buckets = r.get("buckets")
    if r.get("split"):
        bases = [(f'{r["name"]}{k}', pieces[k], k == "Loop") for k in ("KneelIn", "Loop", "StandUp")]
    else:
        bases = [(r["name"], c, r.get("loop", False))]
    for base, clip, loop in bases:
        if buckets:
            for b in buckets:
                outs.append((f"{base}_{b}", scale(clip, b / 100.0), dict(meta, loop=loop, bucket=b, base=base)))
        else:
            outs.append((base, clip, dict(meta, loop=loop, base=base)))
    return outs


def checks(name, clip, meta, recipe):
    res = {"seam": round(seam(clip), 2), "len": round(clip.length(), 3), "drop": round(deepest_drop(clip), 3)}
    ops = [o for o, _ in recipe.get("do", [])]
    ok = True
    if "square_chest" in ops:
        res["max_torso_yaw"] = round(max(abs(torso_yaw_deg(clip, i)) for i in range(clip.n)), 2)
        ok &= res["max_torso_yaw"] <= 1.0
        res["stride"] = round(stride(clip), 3)
        res["stance"] = round(stance_speed(clip), 3)   # the planted-foot ground speed at 1x: Config.Locomotion.Stride.Strafe
        res["jitter"] = round(stance_jitter(clip), 3)
        res["lowest_foot"] = round(lowest_foot(clip), 3)
        ok &= res["jitter"] <= 0.05 and res["lowest_foot"] >= -3.08
        res["contact_phase"] = round(contact_phase(clip), 3)
    if meta.get("loop") and not recipe.get("allow_seam"):
        ok &= res["seam"] <= 1.5
    if "upper_body" in ops:
        ok &= not any(j in clip.P for j in ("Torso", "Left Leg", "Right Leg"))
    if "strip_root" in ops and "Torso" in clip.P:
        tr = clip.P["Torso"][:, :2, 3]
        res["residual_travel"] = round(float(np.max(np.linalg.norm(tr - tr[0], axis=1))), 3)
        ok &= res["residual_travel"] < 0.05
    res["ok"] = bool(ok)
    return res


def main():
    recipes = json.load(open(os.path.join(HERE, "recipes.json"), encoding="utf-8"))
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    manifest, report, bad = {}, ["# phase6-strafes bake report", "", "Generated by `bake.py`. One row per baked piece.", "",
                                 "| Piece | Source | Len (s) | Loop | Priority | Seam (deg) | Drop | Extra | OK |",
                                 "|---|---|---|---|---|---|---|---|---|"], 0
    for r in recipes:
        for name, clip, meta in run_recipe(r):
            full = "NHG_" + name
            res = checks(full, clip, meta, r)
            pri = r.get("priority", "Action")
            open(os.path.join(HERE, "out", full + ".lua"), "w", encoding="utf-8", newline="\n").write(
                emit_lua(clip, full, meta["loop"], pri))
            entry = {"Studio": full, "Len": res["len"], "Loop": meta["loop"], "Priority": pri, "Src": r["src"]}
            for k in ("Carry", "bucket", "base", "window"):
                if k in meta:
                    entry[k] = meta[k]
            for k in ("stride", "stance", "contact_phase"):
                if k in res:
                    entry[k] = res[k]
            manifest[name] = entry
            extra = ", ".join(f"{k} {v}" for k, v in res.items() if k not in ("seam", "len", "drop", "ok"))
            report.append(f"| {full} | {r['src']} | {res['len']} | {meta['loop']} | {pri} | {res['seam']} | {res['drop']} | {extra} | {'yes' if res['ok'] else '**NO**'} |")
            bad += 0 if res["ok"] else 1
    json.dump(manifest, open(os.path.join(HERE, "out", "manifest.json"), "w", encoding="utf-8"), indent=1)
    report += ["", f"{len(manifest)} pieces, {bad} failing."]
    open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(report) + "\n")
    print(f"baked {len(manifest)} pieces, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
