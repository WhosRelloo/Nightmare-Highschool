"""Measured source clip -> R6 pose JSON for animpro.
usage: python -I convert.py <Target> | --raw <SourceName>
Retimes the source's keys onto the target's phases: the source's fastest segment (largest summed aim change per second)
becomes the strike; keys before it spread over the anticipation, keys after it over the settle. Aims are kept as
measured (R15 elbows and knees already folded in). The root drops by `drop` studs at each contact and recovers with a
small overshoot. Legs whose foot was at the floor in the source are marked `grounded` through animpro's flag."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, "source", "_all.json"), encoding="utf-8"))
SPEC = json.load(open(os.path.join(HERE, "clips.json"), encoding="utf-8"))
JOINTS = ["LeftShoulder", "RightShoulder", "LeftHip", "RightHip"]


# Euler continuity: every orientation has two XYZ readings, (x, y, z) and (x + 180, 180 - y, z + 180); a key takes the
# reading (each angle unwrapped by +-360) nearest the previous key's, so a turn never jumps half a circle between keys
def _wrap(a, ref):
    while a - ref > 180: a -= 360
    while a - ref < -180: a += 360
    return a
def continuous(e, prev):
    p, y, r = e["pitch"], e["yaw"], e["roll"]
    if prev is None: return [p, y, r]
    best = None
    for cand in ((p, y, r), (p + 180, 180 - y, r + 180)):
        c = [_wrap(cand[i], prev[i]) for i in range(3)]
        d = sum(abs(c[i] - prev[i]) for i in range(3))
        if best is None or d < best[0]: best = (d, c)
    return best[1]


# ---- R6 forward kinematics (the tool's rig): grounding and key-pose thinning ----
def _mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def _mv(A, v): return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]
def rot_xyz(deg):  # CFrame.Angles(x, y, z) = Rx * Ry * Rz
    x, y, z = [math.radians(a) for a in deg]
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]; Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]; Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _mm(_mm(Rx, Ry), Rz)
# the animation tool's own R6 geometry (animpro R6_RIG): each joint sits on the torso's edge, and the limb hangs half a stud
# to one side of it. A leg's sole is 2 studs down the leg and 0.5 inward (2.06 from the hip: the tool's reach); an arm's end
# is 1.5 down and 0.5 outward.
PIVOT = {"LeftShoulder": (-1, 0.5, 0), "RightShoulder": (1, 0.5, 0), "LeftHip": (-1, -1, 0), "RightHip": (1, -1, 0)}
LIMB = {"LeftShoulder": (1.5, -0.5), "RightShoulder": (1.5, 0.5), "LeftHip": (2.0, 0.5), "RightHip": (2.0, -0.5)}  # (down, sideways x)
REACH = 2.06
CORNERS = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-0.5, 0.5)] + [(0, 2.0, 0)]
def _norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]
def _cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def lowest_point(torso_deg, aims, fronts=None):
    """Lowest body point (studs, root at 0): the torso's corners, the head's top, and each limb as the 1 x 2 x 1 block it is:
    the four corners of its far end (the sole of a leg), oriented by the limb's measured front face. Standing straight,
    the soles are at -3."""
    R = rot_xyz(torso_deg)
    pts = [_mv(R, list(p)) for p in CORNERS]
    for j, piv in PIVOT.items():
        a = aims[j]  # the tool's axes: x right, y up, z forward (= Roblox -Z)
        d = _norm([a[0], a[1], -a[2]])
        f = (fronts or {}).get(j) or [0, 0, 1]
        if abs(sum(f[i] * [d[0], d[1], -d[2]][i] for i in range(3))) > 0.98: f = [1, 0, 0]
        f = [f[0], f[1], -f[2]]
        f = _norm([f[i] - sum(f[k] * d[k] for k in range(3)) * d[i] for i in range(3)])  # perpendicular to the limb
        s = _cross(d, f)
        down, side = LIMB[j]
        sx = _norm([1 - d[0] * d[0], -d[0] * d[1], -d[0] * d[2]])  # the torso's x, square to the limb: the limb's own x
        end = [piv[i] + down * d[i] + side * sx[i] for i in range(3)]
        for u in (-0.5, 0.5):
            for w in (-0.5, 0.5):
                pts.append(_mv(R, [end[i] + u * s[i] + w * f[i] for i in range(3)]))
    return min(p[1] for p in pts)

def thin(keys, eps=0.12):
    """Ramer-Douglas-Peucker over the whole pose (aims, torso angles / 90, root height): keeps the key poses of a baked
    clip, drops the in-betweens the tool's spline recreates."""
    def v(k):
        out = []
        for j in JOINTS: out += [k["aims"][j]["x"], k["aims"][j]["y"], k["aims"][j]["z"]]
        out += [k["torso"]["pitch"] / 90, k["torso"]["yaw"] / 90, k["torso"]["roll"] / 90, k["root"]["y"]]
        return out
    def rec(i0, i1):
        if i1 <= i0 + 1: return []
        t0, t1 = keys[i0]["t"], keys[i1]["t"]
        a, b = v(keys[i0]), v(keys[i1])
        best, bi = -1, None
        for i in range(i0 + 1, i1):
            u = (keys[i]["t"] - t0) / max(t1 - t0, 1e-6)
            lerp = [a[n] + (b[n] - a[n]) * u for n in range(len(a))]
            d = math.dist(lerp, v(keys[i]))
            if d > best: best, bi = d, i
        if best < eps: return []
        return rec(i0, bi) + [bi] + rec(bi, i1)
    idx = [0] + rec(0, len(keys) - 1) + [len(keys) - 1]
    return [keys[i] for i in idx]

def vec(a): return [round(a["x"], 3), round(a["y"], 3), round(a["z"], 3)]
def change(k0, k1):
    return sum(math.dist(vec(k0["aims"][j]), vec(k1["aims"][j])) for j in JOINTS)

def strike_index(keys):
    best, bi = -1, 1
    for i in range(1, len(keys)):
        dt = max(keys[i]["t"] - keys[i - 1]["t"], 1e-3)
        v = change(keys[i - 1], keys[i]) / dt
        if v > best: best, bi = v, i
    return bi  # the key that ends the fastest segment = contact pose


def clamp_hips(k, limit=148.0):
    """A hip never folds past the tool's 150 degree limit (the ghoul's crouched start): the aim is turned back toward
    straight down until it is 148 degrees from it, keeping its direction around the hip."""
    k = json.loads(json.dumps(k))
    for j in ("LeftHip", "RightHip"):
        a = k["aims"][j]
        ang = math.degrees(math.acos(max(-1.0, min(1.0, -a["y"]))))
        if ang > limit:
            h = math.hypot(a["x"], a["z"]) or 1.0
            r = math.radians(limit)
            a["x"], a["z"], a["y"] = a["x"] / h * math.sin(r), a["z"] / h * math.sin(r), -math.cos(r)
    return k


_BASE = {"root": None, "scale": 1.0}
def _travel(k, axis):
    b = _BASE["root"] or k["root"]
    return max(-1.5, min(1.5, (k["root"][axis] - b[axis]) * _BASE["scale"]))



def _alerp(a, b, u):  # an angle the short way round
    d = (b - a + 180) % 360 - 180
    return a + d * u

def densify(out, step=1 / 15):
    """In-between keys every `step` s (the root's height is then computed at each by the planting pass, so the spline
    between keys can't dip a planted rigid leg into the floor)."""
    res = [out[0]]
    for k1 in out[1:]:
        k0 = res[-1]
        gap = k1["time"] - k0["time"]
        n = int(gap / step)
        for i in range(1, n + 1):
            u = i / (n + 1)
            J0, J1 = k0["joints"], k1["joints"]
            nk = {"time": round(k0["time"] + gap * u, 3), "joints": {
                "Root": {"position": [round(J0["Root"]["position"][a] + (J1["Root"]["position"][a] - J0["Root"]["position"][a]) * u, 3) for a in range(3)],
                         "rotation": [round(_alerp(J0["Root"]["rotation"][a], J1["Root"]["rotation"][a], u), 1) for a in range(3)]},
                "Neck": {"rotation": [round(_alerp(J0["Neck"]["rotation"][a], J1["Neck"]["rotation"][a], u), 1) for a in range(3)]}}}
            for j in JOINTS:
                a0, a1 = J0[j]["aim"], J1[j]["aim"]
                m = _norm([a0[x] + (a1[x] - a0[x]) * u for x in range(3)])
                nk["joints"][j] = {"aim": [round(v, 3) for v in m]}
                if "bendToward" in J0[j] and "bendToward" in J1[j]:
                    b = _norm([J0[j]["bendToward"][x] + (J1[j]["bendToward"][x] - J0[j]["bendToward"][x]) * u for x in range(3)])
                    nk["joints"][j]["bendToward"] = [round(v, 3) for v in b]
            res.append(nk)
        res.append(k1)
    return res

def plant_pass(out, lift=0.2):
    """Pin planted feet (the owner's rule: planted feet don't slide). A foot whose sole is within `lift` of the floor is
    pinned to the point where it touched down, for as long as it stays down: the key aims it with `aimAt` at that point
    (the same point on consecutive keys plants it; the tool re-solves it every 1/30 s), and the root's height is set so the
    supporting leg (2 studs, rigid) reaches its point exactly. A foot that can't reach its point lifts and steps."""
    pins = {"LeftHip": None, "RightHip": None}
    for k in out:
        J = k["joints"]
        tor = J["Root"]["rotation"]
        R = rot_xyz(tor)
        rx, ry, rz = J["Root"]["position"]
        needs = []
        for leg in ("LeftHip", "RightHip"):
            if "aim" not in J[leg]:
                continue
            piv = _mv(R, list(PIVOT[leg]))
            a = J[leg]["aim"]
            d = _norm([a[0], a[1], -a[2]])
            down, side = LIMB[leg]
            sx = _norm([1 - d[0] * d[0], -d[0] * d[1], -d[0] * d[2]])
            endL = [down * d[i] + side * sx[i] for i in range(3)]
            eW = _mv(R, endL)
            sole = [rx + piv[0] + eW[0], ry + piv[1] + eW[1], rz + piv[2] + eW[2]]
            down = sole[1] - (-3) < lift
            if not down:
                pins[leg] = None
                continue
            if pins[leg] is None:
                pins[leg] = (sole[0], sole[2])
            px, pz = pins[leg]
            hx, hz = rx + piv[0], rz + piv[2]
            dh = math.hypot(px - hx, pz - hz)
            reach = REACH - 0.03  # the sole passes 0.03 beyond its point: inside the tool's 0.1 ground limit
            if dh >= reach - 0.02:  # out of reach: this foot lifts here and steps
                pins[leg] = None
                continue
            hip_y = -3 + math.sqrt(reach * reach - dh * dh)
            needs.append((leg, hip_y - piv[1], px, pz))
        if needs:
            y = min(n[1] for n in needs)  # the supporting leg's height: no leg is asked to reach beyond its length
            J["Root"]["position"][1] = round(y, 3)
            for leg, req, px, pz in needs:
                if req > y + 0.04:
                    # the torso tilts: this hip sits too low for its foot to stay down without passing into the floor.
                    # The weight is on the other leg, so this foot lifts: its leg swings up just clear of the floor, and it
                    # plants again (at its new spot) when it comes back down
                    pins[leg] = None
                    J[leg] = {"aim": lift_clear(J, leg, R, [rx, y, rz])}
                    continue
                # the tool's axes: right, up, forward (Roblox -Z)
                J[leg] = {"aimAt": [round(px, 3), -3, round(-pz, 3)]}
    return out

def lift_clear(J, leg, R, root, clear=0.04):
    """The leg's aim turned forward and up, in 3 degree steps, until its sole is `clear` above the floor."""
    a = J[leg]["aim"]
    d = _norm([a[0], a[1], -a[2]])
    piv = _mv(R, list(PIVOT[leg]))
    down, side = LIMB[leg]
    for _ in range(40):
        sx = _norm([1 - d[0] * d[0], -d[0] * d[1], -d[0] * d[2]])
        eW = _mv(R, [down * d[i] + side * sx[i] for i in range(3)])
        lowest = root[1] + piv[1] + eW[1] - 0.5 * abs(math.sin(math.acos(max(-1, min(1, -d[1])))))
        if lowest >= -3 + clear: break
        # rotate about the torso's x axis toward forward (Roblox -Z): the knee-less leg swings up in front
        ang = math.radians(3)
        y_, z_ = d[1], d[2]
        d = _norm([d[0], y_ * math.cos(ang) + z_ * math.sin(ang), -y_ * math.sin(ang) + z_ * math.cos(ang)])
    return [round(d[0], 3), round(d[1], 3), round(-d[2], 3)]

_PREV = {"torso": None, "neck": None}
def pose_key(k, t, base_y, extra_drop=0.0):
    tor = continuous(k["torso"], _PREV["torso"]); _PREV["torso"] = tor
    nek = continuous(k["neck"], _PREV["neck"]); _PREV["neck"] = nek
    # written within (-180, 180]: the same orientation (the tool measures turns between keys from orientations), and
    # within its +-360 limit even for a tumbling clip like the game's Knockback (about 1.9 turns)
    tor = [_wrap(a, 0) for a in tor]; nek = [_wrap(a, 0) for a in nek]
    k = clamp_hips(k)
    return {"time": round(t, 3), "joints": {
        # resting on the floor: the lowest corner of the body at -3 (+0.05 so the spline between keys never dips in)
        # the source's own travel (weight leads: the body commits toward the strike), scaled from a tall R15 creature to R6
        "Root": {"position": [round(_travel(k, "x"), 3), round(-3 - lowest_point(tor, {j: vec(k["aims"][j]) for j in JOINTS},
                                                       {j: vec(k["fronts"][j]) for j in JOINTS}) + 0.05, 3), round(_travel(k, "z"), 3)],
                 "rotation": [round(tor[0], 1), round(tor[1], 1), round(tor[2], 1)]},
        "Neck": {"rotation": [round(nek[0], 1), round(nek[1], 1), round(nek[2], 1)]},
        # an arm keeps the source's twist (its front face); a leg uses the tool's default (a folded leg's twist counted
        # against the hip's 150 degree limit)
        **{j: {"aim": vec(k["aims"][j]),
               **({"bendToward": vec(k["fronts"][j])} if "Shoulder" in j else {})} for j in JOINTS}}}

def convert(name):
    spec = SPEC[name]
    src = SRC.get(spec["source"])
    if not src or "error" in src: src = SRC[spec["alt"]]
    keys = src["keys"]
    if len(keys) > 10: keys = thin(keys)
    if spec.get("plantLegs"):
        # a tug of war plants the feet: each key's legs hold this share of the first key's stance
        w = spec["plantLegs"]
        keys = json.loads(json.dumps(keys))
        for k in keys:
            for j in ("LeftHip", "RightHip"):
                a, b = k["aims"][j], keys[0]["aims"][j]
                m = [a[c2] * (1 - w) + b[c2] * w for c2 in "xyz"]
                n = math.sqrt(sum(x * x for x in m)) or 1.0
                k["aims"][j] = {"x": m[0] / n, "y": m[1] / n, "z": m[2] / n}
    base_y = keys[0]["root"]["y"]
    _BASE["root"] = keys[0]["root"]
    _BASE["scale"] = (0.6 if src["rig"].startswith("R15") else 1.0) * spec.get("travel", 1.0)  # ghoul / stalker ~8 studs tall to R6's 5
    si = strike_index(keys)
    a0, a1 = spec["phases"]["anticipation"]; s0, s1 = spec["phases"]["strike"]; e0, e1 = spec["phases"]["settle"]
    out = []
    pre = keys[:si]; post = keys[si:]
    for i, k in enumerate(pre):  # spread over the anticipation; the last pre key sits at the strike's start
        t = a0 + (s0 - a0) * (i / max(len(pre) - 1, 1))
        out.append(pose_key(k, t, base_y))
    for i, k in enumerate(post):  # the contact key at the strike's end, then the settle
        t = s1 + (e1 - s1) * (i / max(len(post) - 1, 1)) if i else s1
        out.append(pose_key(k, t, base_y))
    if spec.get("loop"):
        first = json.loads(json.dumps(out[0])); first["time"] = spec["length"]; out[-1:] = [out[-1], first] if out[-1]["time"] < spec["length"] else [first]
    elif out[-1]["time"] < spec["length"] - 1e-3:
        # keep the contact where it lands and hold the last pose to the end (a moving hold: animpro's life pass drifts it)
        hold = json.loads(json.dumps(out[-1])); hold.pop("markers", None); hold["time"] = spec["length"]
        out.append(hold)
    out = plant_pass(out)  # (densify() tried: more planted keys let the tool's spline and overlap passes sink rigid legs)
    markers = [{"name": "Hit", "value": "contact"}]
    for c in spec["contacts"]:
        for k in out:
            if abs(k["time"] - c) < 1e-3: k["markers"] = markers
    # never both sides on the same frames: the left arm and leg trail the right by a few frames (the house rule)
    return {"name": name, "rig": "R6", "loop": bool(spec.get("loop")), "priority": "Action",
            "pro": {"overlap": {"LeftShoulder": 3, "LeftHip": 2}},
            "easing": {"style": "CubicV2", "direction": "InOut"}, "keyframes": out}

def raw(source):
    keys = SRC[source]["keys"]; base_y = keys[0]["root"]["y"]
    return {"name": "_raw_" + source, "rig": "R6", "keyframes": [pose_key(k, k["t"], base_y) for k in keys]}

os.makedirs(os.path.join(HERE, "pose"), exist_ok=True)
if sys.argv[1] == "--raw":
    doc = raw(sys.argv[2]); path = os.path.join(HERE, "pose", "_raw_" + sys.argv[2] + ".json")
else:
    doc = convert(sys.argv[1]); path = os.path.join(HERE, "pose", sys.argv[1] + ".json")
json.dump(doc, open(path, "w", encoding="utf-8"), indent=1)
print("wrote", path, len(doc["keyframes"]), "keys")
