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

_PREV = {"torso": None, "neck": None}
def pose_key(k, t, base_y, extra_drop=0.0):
    tor = continuous(k["torso"], _PREV["torso"]); _PREV["torso"] = tor
    nek = continuous(k["neck"], _PREV["neck"]); _PREV["neck"] = nek
    # written within (-180, 180]: the same orientation (the tool measures turns between keys from orientations), and
    # within its +-360 limit even for a tumbling clip like the game's Knockback (about 1.9 turns)
    tor = [_wrap(a, 0) for a in tor]; nek = [_wrap(a, 0) for a in nek]
    return {"time": round(t, 3), "joints": {
        "Root": {"position": [0, round(k["root"]["y"] - base_y - extra_drop, 3), 0],
                 "rotation": [round(tor[0], 1), round(tor[1], 1), round(tor[2], 1)]},
        "Neck": {"rotation": [round(nek[0], 1), round(nek[1], 1), round(nek[2], 1)]},
        **{j: {"aim": vec(k["aims"][j])} for j in JOINTS}}}

def convert(name):
    spec = SPEC[name]
    src = SRC.get(spec["source"])
    if not src or "error" in src: src = SRC[spec["alt"]]
    keys = src["keys"]
    base_y = keys[0]["root"]["y"]
    si = strike_index(keys)
    a0, a1 = spec["phases"]["anticipation"]; s0, s1 = spec["phases"]["strike"]; e0, e1 = spec["phases"]["settle"]
    out = []
    pre = keys[:si]; post = keys[si:]
    for i, k in enumerate(pre):  # spread over the anticipation; the last pre key sits at the strike's start
        t = a0 + (s0 - a0) * (i / max(len(pre) - 1, 1))
        out.append(pose_key(k, t, base_y))
    for i, k in enumerate(post):  # the contact key at the strike's end, then the settle
        t = s1 + (e1 - s1) * (i / max(len(post) - 1, 1)) if i else s1
        drop = spec["drop"] if i == 0 and spec["contacts"] else (spec["drop"] * -0.15 if i == 1 and spec["contacts"] else 0.0)
        out.append(pose_key(k, t, base_y, drop))
    if spec.get("loop"):
        first = json.loads(json.dumps(out[0])); first["time"] = spec["length"]; out[-1:] = [out[-1], first] if out[-1]["time"] < spec["length"] else [first]
    elif out[-1]["time"] < spec["length"] - 1e-3:
        # keep the contact where it lands and hold the last pose to the end (a moving hold: animpro's life pass drifts it)
        hold = json.loads(json.dumps(out[-1])); hold.pop("markers", None); hold["time"] = spec["length"]
        hold["joints"]["Root"]["position"][1] = round(hold["joints"]["Root"]["position"][1] + (spec["drop"] if spec["contacts"] else 0), 3)
        out.append(hold)
    markers = [{"name": "Hit", "value": "contact"}]
    for c in spec["contacts"]:
        for k in out:
            if abs(k["time"] - c) < 1e-3: k["markers"] = markers
    return {"name": name, "rig": "R6", "loop": bool(spec.get("loop")), "priority": "Action",
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
