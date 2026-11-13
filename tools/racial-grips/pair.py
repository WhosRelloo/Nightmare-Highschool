"""Paired R6 clips: an attacker and a victim authored in one shared space, with hands kept on the other body.

A clip file (clips/<name>.py) defines CLIP = {
    "name": "GripVampire", "length": 3.0, "offset": {"p": [x, y, z], "yaw": deg},   # victim HRP in attacker HRP space
    "markers": [(t, "Bite"), ...],                                                    # on the attacker clip
    "attacker": [key, ...], "victim": [key, ...],
}
key = {"t": 0.4, "stop": True|False|[joints], "Root": {"p": [...], "r": [...]}, "<Joint>": [x, y, z] | reach}
reach = {"reach": ("victim"|"attacker"|"self", "<Part>", [x, y, z] in that part's local space), "twist": deg}
A joint reached in two neighbouring keys with the same target is re-solved every frame (the hand stays put on
the body however either one moves). A joint left out of a key keeps easing toward its next key.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

import rig

HERE = os.path.dirname(os.path.abspath(__file__))
ANIMPRO = os.path.expanduser("~/.claude/skills/roblox-cinematic-animation/scripts/animpro.mjs")
REST = {"Root": {"p": [0, 0, 0], "r": [0, 0, 0]}, "Neck": [0, 0, 0], "RightShoulder": [0, 0, 0],
        "LeftShoulder": [0, 0, 0], "RightHip": [0, 0, 0], "LeftHip": [0, 0, 0]}
ORDER = ["Root", "Neck", "RightHip", "LeftHip", "RightShoulder", "LeftShoulder"]


def is_reach(v):
    return isinstance(v, dict) and "reach" in v


def is_plant(v):
    """{"plant": 4x4 world frame of the limb's part, "id": name}: the limb stays exactly there (tucked kneel legs)."""
    return isinstance(v, dict) and "plant" in v


def keeps(spec):
    """Specs whose limbs keep an exact place and are not smoothed / floor-turned."""
    return is_plant(spec) or (is_reach(spec) and spec["reach"][0] != "world")


def mode_of(key, joint):
    s = key.get("stop", False)
    if s is True or (isinstance(s, (list, tuple)) and joint in s):
        return "stop"
    return "auto"


class Body:
    def __init__(self, name, keys, hrp):
        self.name, self.hrp = name, hrp
        self.keys = sorted(keys, key=lambda k: k["t"])
        if self.keys[0]["t"] != 0:
            raise ValueError(f"{name}: first key must be at t=0")
        for j in ORDER:  # every joint starts keyed (rest if not given)
            self.keys[0].setdefault(j, REST[j] if j != "Root" else dict(REST["Root"]))
        self.tracks = {j: [(k["t"], k[j], mode_of(k, j)) for k in self.keys if j in k] for j in ORDER}
        self.cache = {}


class Pair:
    def __init__(self, clip):
        self.clip = clip
        off = clip["offset"]
        self.vhrp = rig.cf(off["p"], rig.ry(math.radians(off.get("yaw", 0))))
        self.bodies = {"attacker": Body("attacker", clip["attacker"], np.eye(4)),
                       "victim": Body("victim", clip["victim"], self.vhrp)}
        self.errors = []
        self.smooth = clip.get("smooth", 1.2)
        if self.smooth:
            for b in self.bodies.values():
                self._smooth_roots(b)

    # -------------------------------------------------- evaluation
    def target_world(self, who, target, t, own_pose):
        body, part, local = target
        if body == "world":
            return np.asarray(local, float)
        if body == "self":
            parts = rig.fk(own_pose, self.bodies[who].hrp)
        elif part in ("Torso", "Head"):
            other = self.bodies[body]
            p = {"Root": self.root_at(other, t)}
            p["Neck"] = self.joint_at(body, "Neck", t, p)
            for j in ORDER[2:]:
                p[j] = np.eye(3)
            parts = rig.fk(p, other.hrp)
        else:
            if who == "attacker":
                raise ValueError("attacker may only reach the victim's Torso or Head")
            parts = rig.fk(self.pose(body, t), self.bodies[body].hrp)
        return rig.xf(parts[part], local)

    def resolve(self, who, spec, t, pose, joint):
        """World target for a reach spec; with "slide": [dx,dy,dz] the point moves along that local segment
        (s in -1..1) to where the rigid limb actually reaches."""
        body = self.bodies[who]
        tgt = spec["reach"]
        slide = spec.get("slide")
        if not slide:
            return self.target_world(who, tgt, t, pose)
        torso = body.hrp @ rig.cf(pose["Root"]["p"], pose["Root"]["R"])
        piv = rig.xf(torso, rig.PIVOT[joint])
        reach = float(np.linalg.norm(rig.END[joint]))
        best, bw = None, None
        for n in range(-10, 11):
            s = n / 10
            loc = [tgt[2][i] + s * slide[i] for i in range(3)]
            w = self.target_world(who, (tgt[0], tgt[1], loc), t, pose)
            d = abs(float(np.linalg.norm(w - piv)) - reach)
            if best is None or d < best - 1e-4:
                best, bw = d, w
        return bw

    def root_at(self, body, t):
        key = ("root", round(t, 5))
        if key in body.cache:
            return body.cache[key]
        tr = body.tracks["Root"]
        pk = [(k[0], np.asarray(k[1]["p"], float), k[2]) for k in tr]
        qs, prev = [], None
        for k in tr:
            q = rig.mat2q(rig.euler(k[1]["r"]))
            q = q if prev is None else rig.qalign(q, prev)
            prev = q
            qs.append((k[0], q, k[2]))
        p = rig.hermite(pk, t, lambda a, b: a)
        q = rig.hermite(qs, t, lambda a, b: a)
        body.cache[key] = {"p": p, "R": rig.q2mat(q)}
        return body.cache[key]

    def key_value(self, who, joint, idx):
        body = self.bodies[who]
        tk, spec, _ = body.tracks[joint][idx]
        if is_plant(spec):
            return self.plant_at(who, joint, idx)[0]
        if not is_reach(spec):
            return rig.euler(spec)
        ck = (joint, idx)
        if ck not in body.cache:
            pose = self.partial_pose(who, tk, joint)
            tw = self.resolve(who, spec, tk, pose, joint)
            R, err = rig.solve_reach(pose, joint, tw, body.hrp, spec.get("twist"), self.ref_rot(who, joint, tk))
            body.cache[ck] = R
        return body.cache[ck]

    def ref_rot(self, who, joint, t):
        """Twist reference for a reach: the latest plain (non-reach) key at or before t, else the next one, else rest."""
        tr = self.bodies[who].tracks[joint]
        plain = [k for k in tr if not is_reach(k[1]) and not is_plant(k[1])]
        before = [k for k in plain if k[0] <= t + 1e-9]
        k = before[-1] if before else (plain[0] if plain else None)
        return rig.euler(k[1]) if k else np.eye(3)

    def held(self, tr, i):
        a = tr[i]
        b = tr[i + 1] if i + 1 < len(tr) else None
        if is_plant(a[1]):
            return b is None or (is_plant(b[1]) and a[1]["id"] == b[1]["id"])
        return is_reach(a[1]) and (b is None or (is_reach(b[1]) and a[1]["reach"] == b[1]["reach"]))

    def plant_at(self, who, joint, idx):
        """(R, off) of a plant key at its own time."""
        body = self.bodies[who]
        ck = ("plant", joint, idx)
        if ck not in body.cache:
            tk, spec, _ = body.tracks[joint][idx]
            pose = self.partial_pose(who, tk, joint)
            body.cache[ck] = rig.plant_solve(pose, joint, spec["plant"], body.hrp)
        return body.cache[ck]

    def off_at(self, who, joint, t, i):
        """Tuck offset between keys: eased from one key's offset to the next (0 for ordinary keys)."""
        tr = self.bodies[who].tracks[joint]
        oa = self.plant_at(who, joint, i)[1] if is_plant(tr[i][1]) else np.zeros(3)
        if i + 1 >= len(tr) or t <= tr[i][0]:
            return oa
        ob = self.plant_at(who, joint, i + 1)[1] if is_plant(tr[i + 1][1]) else np.zeros(3)
        k = min(1.0, max(0.0, (t - tr[i][0]) / max(1e-6, tr[i + 1][0] - tr[i][0])))
        k = k * k * (3 - 2 * k)
        return oa + (ob - oa) * k

    def joint_at(self, who, joint, t, pose_so_far):
        body = self.bodies[who]
        tr = body.tracks[joint]
        i = max([n for n, k in enumerate(tr) if k[0] <= t + 1e-9] or [0])
        if self.held(tr, i) and is_plant(tr[i][1]):
            R, off = rig.plant_solve(pose_so_far, joint, tr[i][1]["plant"], body.hrp)
            pose_so_far[joint + "_off"] = off
            return R
        if any(is_plant(k[1]) for k in tr):
            pose_so_far[joint + "_off"] = self.off_at(who, joint, t, i)
        if self.held(tr, i):
            tw = self.resolve(who, tr[i][1], t, pose_so_far, joint)
            R, _ = rig.solve_reach(pose_so_far, joint, tw, body.hrp, tr[i][1].get("twist"), self.ref_rot(who, joint, tr[i][0]))
            return R
        ck = ("q", joint)
        if ck not in body.cache:
            vals, prev = [], None
            for n in range(len(tr)):
                q = rig.mat2q(self.key_value(who, joint, n))
                q = q if prev is None else rig.qalign(q, prev)
                prev = q
                vals.append((tr[n][0], q, tr[n][2]))
            body.cache[ck] = vals
        return rig.q2mat(rig.hermite(body.cache[ck], t, lambda x, y: x))

    def partial_pose(self, who, t, upto):
        body = self.bodies[who]
        pose = {"Root": self.root_at(body, t)}
        for j in ORDER[1:]:
            if j == upto:
                break
            pose[j] = self.joint_at(who, j, t, pose)
        for j in ORDER[1:]:
            pose.setdefault(j, np.eye(3))
        return pose

    def pose(self, who, t):
        body = self.bodies[who]
        pose = {"Root": self.root_at(body, t)}
        for j in ORDER[1:]:
            pose[j] = self.joint_at(who, j, t, pose)
        return pose

    def _gauss(self, arr, sigma):
        """Gaussian blur along axis 0 (frames), edges held, first/last frame kept exact."""
        n = len(arr)
        r = int(max(1, round(sigma * 3)))
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
        k /= k.sum()
        pad = np.concatenate([np.repeat(arr[:1], r, 0), arr, np.repeat(arr[-1:], r, 0)])
        out = np.stack([np.tensordot(k, pad[i:i + 2 * r + 1], axes=(0, 0)) for i in range(n)])
        out[0], out[-1] = arr[0], arr[-1]
        return out

    def _smooth_roots(self, body):
        n = int(round(self.clip["length"] * rig.FPS))
        ts = [f / rig.FPS for f in range(n + 1)]
        raw = [self.root_at(body, t) for t in ts]
        P = np.array([r["p"] for r in raw], float)
        Q, prev = [], None
        for r in raw:
            q = rig.mat2q(r["R"])
            q = q if prev is None else rig.qalign(q, prev)
            prev = q
            Q.append(q)
        P = self._gauss(P, self.smooth)
        Q = self._gauss(np.array(Q), self.smooth)
        for i, t in enumerate(ts):
            body.cache[("root", round(t, 5))] = {"p": P[i], "R": rig.q2mat(Q[i] / np.linalg.norm(Q[i]))}

    # -------------------------------------------------- bake + report
    def bake(self, who):
        n = int(round(self.clip["length"] * rig.FPS))
        frames = []
        for f in range(n + 1):
            t = f / rig.FPS
            frames.append((t, self.pose(who, t)))
        if not self.smooth:
            return self._floor(who, frames)
        body = self.bodies[who]
        for joint in ORDER[1:]:
            tr = body.tracks[joint]
            held = []
            for t, _ in frames:
                i = max([n2 for n2, k in enumerate(tr) if k[0] <= t + 1e-9] or [0])
                held.append(self.held(tr, i))
            Q, prev = [], None
            for t, pose in frames:
                q = rig.mat2q(pose[joint])
                q = q if prev is None else rig.qalign(q, prev)
                prev = q
                Q.append(q)
            S = self._gauss(np.array(Q), max(0.8, self.smooth * 0.8))
            for i, (t, pose) in enumerate(frames):
                if not held[i]:
                    pose[joint] = rig.q2mat(S[i] / np.linalg.norm(S[i]))
        frames = self._floor(who, frames)
        for joint in ("RightHip", "LeftHip", "RightShoulder", "LeftShoulder"):
            tr = body.tracks[joint]
            Q, prev, keep = [], None, []
            for t, pose in frames:
                i = max([n2 for n2, k in enumerate(tr) if k[0] <= t + 1e-9] or [0])
                keep.append(self.held(tr, i) and keeps(tr[i][1]))
                q = rig.mat2q(pose[joint])
                q = q if prev is None else rig.qalign(q, prev)
                prev = q
                Q.append(q)
            S = self._gauss(np.array(Q), 1.0)
            for i, (t, pose) in enumerate(frames):
                if not keep[i]:
                    pose[joint] = rig.q2mat(S[i] / np.linalg.norm(S[i]))
        return self._floor(who, frames)

    def _floor(self, who, frames, floor=-3.0, tol=0.04):
        """Nothing goes through the floor: lift the body if the torso/head sink, then turn any sinking limb (that
        isn't holding a contact) by the smallest rotation that clears the floor."""
        if self.clip.get("floor") is False:
            return frames
        body = self.bodies[who]
        hrp = body.hrp
        axes = [np.array(a, float) for a in ([1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0])]
        last_axis = {}

        def low(part, pose):
            F = rig.fk(pose, hrp)[part]
            return min(c[1] for c in _corners(F, rig.SIZE[part]))

        def rot(axis, deg):
            a = np.radians(deg)
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K

        for t, pose in frames:
            # 1) torso / head below the floor: raise the whole body
            dip = min(low("Torso", pose), low("Head", pose))
            if dip < floor - tol:
                p = np.array(pose["Root"]["p"], float)
                p[1] += floor - dip
                pose["Root"] = {"p": p, "R": pose["Root"]["R"]}
            # 2) limbs: smallest turn at the joint that clears the floor
            for joint in ("RightHip", "LeftHip", "RightShoulder", "LeftShoulder"):
                tr = body.tracks[joint]
                i = max([n for n, k in enumerate(tr) if k[0] <= t + 1e-9] or [0])
                if self.held(tr, i) and keeps(tr[i][1]):
                    continue  # a hand on the other body keeps its contact; planted kneel legs are exact
                part = rig.PART_OF[joint]
                if low(part, pose) >= floor - tol:
                    continue
                R0 = pose[joint]
                best, best_low, best_ax = None, None, None
                order = sorted(range(len(axes)), key=lambda k: 0 if last_axis.get(joint) == k else 1)
                for deg in range(3, 151, 3):
                    for k in order:
                        pose[joint] = rot(axes[k], deg) @ R0
                        l = low(part, pose)
                        if best_low is None or l > best_low:
                            best_low, best_ax = l, k
                        if l >= floor - tol:
                            best = pose[joint]
                            last_axis[joint] = k
                            break
                    if best is not None:
                        break
                pose[joint] = best if best is not None else R0
        return frames

    def contact_report(self, who, frames):
        body = self.bodies[who]
        rows = []
        for t, pose in frames:
            for joint in ORDER[1:]:
                tr = body.tracks[joint]
                i = max([n for n, k in enumerate(tr) if k[0] <= t + 1e-6] or [0])
                if is_plant(tr[i][1]):
                    continue
                if self.held(tr, i) or (is_reach(tr[i][1]) and abs(tr[i][0] - t) < 1e-6):
                    tw = self.resolve(who, tr[i][1], t, pose, joint)
                    torso = body.hrp @ rig.cf(pose["Root"]["p"], pose["Root"]["R"])
                    piv = rig.xf(torso, rig.PIVOT[joint])
                    signed = float(np.linalg.norm(tw - piv)) - float(np.linalg.norm(rig.END[joint]))
                    rows.append((round(t, 3), joint, tr[i][1]["reach"][1], round(signed, 3)))
        return rows

    def to_animpro(self, who, frames, name, markers=()):
        kfs = []
        mk = {}
        for t, m in markers:
            mk.setdefault(int(round(t * rig.FPS)), []).append({"name": m})
        for f, (t, pose) in enumerate(frames):
            j = {"Root": {"position": [round(float(v), 4) for v in pose["Root"]["p"]],
                          "rotation": [round(v, 3) for v in rig.to_euler(pose["Root"]["R"])]}}
            for jn in ORDER[1:]:
                j[jn] = {"rotation": [round(v, 3) for v in rig.to_euler(pose[jn])]}
            kf = {"time": round(t, 4), "joints": j}
            if f in mk:
                kf["markers"] = mk[f]
            kfs.append(kf)
        return {"name": name, "rig": "R6", "priority": "Action4", "easing": {"style": "Linear"}, "keyframes": kfs}


def _corners(frame, size):
    sx, sy, sz = (s / 2 for s in size)
    return [rig.xf(frame, (x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]


def build(clip_name, preview_dir, life=0.35):
    sys.path.insert(0, os.path.join(HERE, "clips"))
    mod = __import__(clip_name)
    clip = mod.CLIP
    pair = Pair(clip)
    out = {}
    os.makedirs(preview_dir, exist_ok=True)
    for who in ("attacker", "victim"):
        if who == "attacker" and clip.get("external_attacker"):
            continue
        frames = pair.bake(who)
        name = clip["name"] + ("" if who == "attacker" else "Victim")
        data = pair.to_animpro(who, frames, name, clip.get("markers", []) if who == "attacker" else clip.get("victim_markers", []))
        jpath = os.path.join(preview_dir, name + ".json")
        with open(jpath, "w") as fh:
            json.dump(data, fh)
        tuck = {}
        for f, (t, pose) in enumerate(frames):
            row = {}
            for j in ("RightHip", "LeftHip"):
                off = pose.get(j + "_off")
                if off is not None and float(np.linalg.norm(off)) > 1e-4:
                    row[rig.PART_OF[j]] = [round(float(v), 4) for v in rig.pose_offset(j, off)]
            if row:
                tuck[str(f)] = row
        tpath = os.path.join(preview_dir, name + ".tuck.json")
        if tuck:
            with open(tpath, "w") as fh:
                json.dump(tuck, fh)
        elif os.path.exists(tpath):
            os.remove(tpath)
        rep = pair.contact_report(who, frames)
        ground = []
        for t, pose in frames:
            fr = rig.fk(pose, pair.bodies[who].hrp)
            low = min(c[1] for pn, f in fr.items() for c in _corners(f, rig.SIZE[pn]))
            legs = min(c[1] for pn in ("Right Leg", "Left Leg") for c in _corners(fr[pn], rig.SIZE[pn]))
            ground.append((round(t, 2), round(low, 2), round(legs, 2)))
        sinks = [g for g in ground if g[1] < -3.12]
        floats = [g for g in ground if g[2] > -2.9] if who == "attacker" else []
        worst = sorted(rep, key=lambda r: -abs(r[3]))[:6]
        args = ["node", ANIMPRO, jpath, "--no-spline", "--overlap", "off", "--life", str(life),
                "--sheet", os.path.join(preview_dir, name + "_sheet.png"),
                "--graph", os.path.join(preview_dir, name + "_graph.png"),
                "--trails", os.path.join(preview_dir, name + "_trails.png"),
                "--out", os.path.join(preview_dir, name + ".lua"), "--json", os.path.join(preview_dir, name + "_report.json")]
        if who == "attacker" and clip.get("grounded", True):
            args.append("--grounded")
        waive = clip.get("waive_" + who)
        if waive:
            args += ["--waive", waive]
        r = subprocess.run(args, capture_output=True, text=True)
        lp = os.path.join(preview_dir, name + ".lua")
        if os.path.exists(lp):
            lua = open(lp).read().replace('FindFirstChild("Animations")', 'FindFirstChild("NH_GripAnims")').replace('folder.Name = "Animations"', 'folder.Name = "NH_GripAnims"')
            open(lp, "w").write(lua)
        try:
            res = json.loads(r.stdout)
        except Exception:
            res = {"raw": r.stdout[-800:], "err": r.stderr[-800:]}
        out[who] = {"exit": r.returncode, "failing": res.get("failing"),
                    "lint": [(l.get("id"), l.get("level"), l.get("message", "")[:140]) for l in res.get("lint", [])][:8] if isinstance(res.get("lint"), list) else res.get("lint"),
                    "contact_worst": worst, "frames": len(frames),
                    "sinks": sinks[:6], "n_sinks": len(sinks), "floats": floats[:6], "n_floats": len(floats)}
    return out


if __name__ == "__main__":
    res = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out"))
    for who, v in res.items():
        print(who, "exit", v["exit"], "failing", v["failing"])
        print("  contact worst:", v["contact_worst"][:4])
        print("  sinks", v["n_sinks"], v["sinks"][:3], "floats", v["n_floats"], v["floats"][:3])
        for l in (v["lint"] or [])[:6]:
            print("  lint:", l)
