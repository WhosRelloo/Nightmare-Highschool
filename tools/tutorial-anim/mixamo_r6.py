"""RoMixamo clip -> R6 KeyframeSequence, a straight port of the plugin's Convert2R6 (same template rigs, same offsets).

  python mixamo_r6.py <RoMixamo.rbxm> <out.rbxmx> "<Name>|<id or exact catalog name>[|inplace][|loop]" ...

Also writes <out>.poses.json: each clip's R6 joint rotations at every frame (for transition matching).
"""
import base64, json, math, os, re, sys, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxm_peek as RP  # noqa: E402

RIGS = json.load(open(os.path.join(HERE, "rigs.json")))
KEYMAP = {"HRP": "HumanoidRootPart", "LT": "LowerTorso", "UT": "UpperTorso", "H": "Head",
          "LUA": "LeftUpperArm", "LLA": "LeftLowerArm", "LH": "LeftHand", "RUA": "RightUpperArm", "RLA": "RightLowerArm", "RH": "RightHand",
          "LUL": "LeftUpperLeg", "LLL": "LeftLowerLeg", "LF": "LeftFoot", "RUL": "RightUpperLeg", "RLL": "RightLowerLeg", "RF": "RightFoot"}


def M(c):
    """Roblox CFrame components (x,y,z,R00..R22) -> 4x4"""
    m = np.eye(4)
    m[:3, 3] = c[:3]
    m[:3, :3] = np.array(c[3:12], dtype=float).reshape(3, 3)
    return m


def inv(m):
    r = np.eye(4)
    r[:3, :3] = m[:3, :3].T
    r[:3, 3] = -m[:3, :3].T @ m[:3, 3]
    return r


def comps(m):
    return [m[0, 3], m[1, 3], m[2, 3]] + list(m[:3, :3].reshape(-1))


R15, R6 = RIGS["R15Block"], RIGS["R6Block"]
R15_MOTOR = {v["Part1"]: (k, v) for k, v in R15["motors"].items()}       # part -> (motor name, motor)
R15_ORDER = ["LowerTorso", "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm",
             "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]
R6M = {k: (M(v["C0"]), M(v["C1"])) for k, v in R6["motors"].items()}
R6_HRP = M(R6["parts"]["HumanoidRootPart"])
R6_TORSO = M(R6["parts"]["Torso"])
R15_HRP = M(R15["parts"]["HumanoidRootPart"])
LIMBS = [("Head", "LowerHead", "Neck", (0, 0, 0)), ("Left Arm", "LeftLowerArm", "Left Shoulder", (0, 0.2, 0)),
         ("Right Arm", "RightLowerArm", "Right Shoulder", (0, 0.224, 0)), ("Left Leg", "LeftLowerLeg", "Left Hip", (0, 0.201, 0)),
         ("Right Leg", "RightLowerLeg", "Right Hip", (0, 0.201, 0))]


def r15_world(pose):
    """pose: R15 part -> 4x4 pose CFrame. World CFrames of every R15 part (C0' = C0 * pose; part1 = part0 * C0' * C1^-1)"""
    w = {"HumanoidRootPart": R15_HRP}
    for part in R15_ORDER:
        _, mo = R15_MOTOR[part]
        c0 = M(mo["C0"]) @ pose.get(part, np.eye(4))
        w[part] = w[mo["Part0"]] @ c0 @ inv(M(mo["C1"]))
    return w


def to_r6(w):
    def conv(r15cf, motor, torso_cf, offset):
        tw = R6_HRP @ inv(R15_HRP) @ r15cf
        tw = tw.copy()
        tw[:3, 3] += np.array(offset)
        c0, c1 = R6M[motor]
        return inv(torso_cf @ c0) @ tw @ c1, tw
    out = {}
    out["Torso"], torso_w = conv(w["UpperTorso"], "RootJoint", R6_TORSO, (0, -0.2, 0))
    for limb, src, motor, off in LIMBS:
        src = "Head" if limb == "Head" else src
        out[limb], _ = conv(w[src], motor, torso_w, off)
    return out


def load_anim(rbxm, key, cat):
    ids = {x["Id"]: x for x in cat}
    if key not in ids:
        hits = [x for x in cat if x["Name"].lower() == key.lower() or (x["Name"] + " | " + x.get("Desc", "")).lower() == key.lower()]
        if not hits:
            raise SystemExit(f"no clip {key!r}")
        key = hits[0]["Id"]
    s = rbxm[key].decode()
    body = re.search(r"\[(=*)\[(.*)\]\1\]", s, re.S).group(2).strip()
    return key, json.loads(zlib.decompress(base64.b64decode(body + "=" * (-len(body) % 4))))


def convert(d, inplace=False, plugin_parity=False):
    frames = []
    for kf in d["kfs"]:
        pose = {KEYMAP[k]: M([float(x) for x in v]) for k, v in kf["kf"].items() if k in KEYMAP and k != "HRP"}
        frames.append((float(kf["t"]), to_r6(r15_world(pose))))
    # Torso pose space (under the R6 RootJoint): X sideways, Y forward/back, Z up.
    if plugin_parity:                                        # the plugin's own output keeps the torso centred sideways
        for _, f in frames:
            f["Torso"][0, 3] = 0.0
    if inplace and frames:                                   # drop the torso's horizontal travel (keep the bob)
        x0, y0 = frames[0][1]["Torso"][0, 3], frames[0][1]["Torso"][1, 3]
        for _, f in frames:
            f["Torso"][0, 3], f["Torso"][1, 3] = x0, y0
    return frames


def fmt(v):
    return f"{v:.5f}".rstrip("0").rstrip(".") if abs(v) > 1e-7 else "0"


def cf_xml(name, m):
    c = comps(m)
    tags = ["X", "Y", "Z", "R00", "R01", "R02", "R10", "R11", "R12", "R20", "R21", "R22"]
    return f'<CoordinateFrame name="{name}">' + "".join(f"<{t}>{fmt(v)}</{t}>" for t, v in zip(tags, c)) + "</CoordinateFrame>"


def pose_xml(name, m, kids=""):
    return (f'<Item class="Pose"><Properties><string name="Name">{name}</string>{cf_xml("CFrame", m)}'
            f'<token name="EasingDirection">0</token><token name="EasingStyle">0</token><float name="Weight">1</float></Properties>{kids}</Item>')


def kfs_xml(name, frames, loop):
    out = [f'<Item class="KeyframeSequence"><Properties><string name="Name">{name}</string><bool name="Loop">{"true" if loop else "false"}</bool>'
           f'<token name="Priority">2</token></Properties>']
    for t, f in frames:
        limbs = "".join(pose_xml(l, f[l]) for l in ("Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg"))
        out.append(f'<Item class="Keyframe"><Properties><string name="Name">Keyframe</string><float name="Time">{fmt(t)}</float></Properties>'
                   + pose_xml("HumanoidRootPart", np.eye(4), pose_xml("Torso", f["Torso"], limbs)) + "</Item>")
    out.append("</Item>")
    return "".join(out)


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    classes, ic, names, sp, parent = RP.main(src)
    rbxm = {names[r]: p["Source"] for r, p in sp.items() if "Source" in p and names.get(parent.get(r)) == "AnimData"}
    cat = [x for x in json.load(open(os.path.join(HERE, "mixamo_catalog.json"), encoding="utf-8")) if x["Type"] == "Motion"]
    items, poses = [], {}
    for spec in sys.argv[3:]:
        parts = spec.split("|")
        name, key, flags = parts[0], parts[1], set(parts[2:])
        cid, d = load_anim(rbxm, key, cat)
        frames = convert(d, inplace="inplace" in flags)
        items.append(kfs_xml(name, frames, "loop" in flags))
        poses[name] = {"id": cid, "length": frames[-1][0], "frames": [{"t": t, **{k: comps(v) for k, v in f.items()}} for t, f in frames]}
        print(f"{name}: {len(frames)} frames, {frames[-1][0]:.2f}s")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4"><Item class="Folder"><Properties><string name="Name">'
                 + os.path.splitext(os.path.basename(out))[0] + "</string></Properties>" + "".join(items) + "</Item></roblox>")
    json.dump(poses, open(out + ".poses.json", "w"), indent=0)
