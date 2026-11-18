"""Settle a converted clip's feet on the floor with the animation tool as the judge.
usage: python -I ground_fix.py <Target>   (after convert.py; rewrites pose/<Target>.json)
Each round compiles the clip; where the tool reports a leg sinking at time t, a key is inserted at t (every joint
interpolated between its neighbours, the torso by its angles), with the root raised so the lowest body corner rests on
the floor (+0.05). Stops when ground contact passes (or after 10 rounds)."""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SK = r"C:/Users/Owner/.claude/skills/roblox-cinematic-animation/scripts/animpro.mjs"
import importlib.util
spec = importlib.util.spec_from_file_location("conv", os.path.join(HERE, "convert.py"))
T = sys.argv[1]
path = os.path.join(HERE, "pose", T + ".json")

def check():
    r = subprocess.run(["node", SK, path, "--grounded", "--settle", "light"], capture_output=True, text=True, encoding="utf-8")
    d = json.loads(r.stdout)
    ch = d.get("checks"); items = ch.values() if isinstance(ch, dict) else (ch or [])
    for v in items:
        if isinstance(v, dict) and v.get("id") == "groundContact" and v.get("status") == "fail":
            m = re.search(r"sinks ([\d.]+) studs into the ground at ([\d.]+) s", v.get("detail", ""))
            if m: return float(m.group(1)), float(m.group(2))
    return None

def lerp(a, b, u): return [a[i] + (b[i] - a[i]) * u for i in range(len(a))]
def norm(v):
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]

# the converter's grounding maths without re-running its main
src = open(os.path.join(HERE, "convert.py"), encoding="utf-8").read()
ns = {"__name__": "conv_lib", "__file__": os.path.join(HERE, "convert.py")}
exec(compile(src.split("os.makedirs(os.path.join(HERE, \"pose\"), exist_ok=True)")[0], "convert.py", "exec"), ns)
lowest_point = ns["lowest_point"]
JOINTS = ns["JOINTS"]

ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
for round_ in range(ROUNDS):
    hit = check()
    if not hit:
        print(T, "ground contact passes after", round_, "fix rounds"); break
    depth, t = hit
    # a planted leg (aimAt) is never fixed by lifting the body: that only stretches it out of reach
    doc = json.load(open(path, encoding="utf-8"))
    ks = doc["keyframes"]
    i1 = next((i for i, k in enumerate(ks) if k["time"] > t), None)
    if i1 is None:
        # in the tail the tool's settle pass adds after the last key: raise the last key
        if any("aimAt" in ks[-1]["joints"].get(j, {}) for j in ("LeftHip", "RightHip")):
            print(T, f"round {round_}: sink in the tail on a planted key ({depth}); left for review")
            break
        ks[-1]["joints"]["Root"]["position"][1] = round(ks[-1]["joints"]["Root"]["position"][1] + depth + 0.03, 3)
        print(T, f"round {round_}: raised the last key by {depth + 0.03:.2f} (tail at {t})")
        json.dump(doc, open(path, "w", encoding="utf-8"), indent=1)
        continue
    i0 = max(i1 - 1, 0)
    k0, k1 = ks[i0], ks[i1]
    planted = lambda k: any("aimAt" in k["joints"].get(j, {}) for j in ("LeftHip", "RightHip"))
    if abs(k0["time"] - t) < 0.02 or abs(k1["time"] - t) < 0.02:
        near = k0 if abs(k0["time"] - t) < abs(k1["time"] - t) else k1
        if planted(near):
            print(T, f"round {round_}: sink at {t} on a planted key ({depth}); left for review")
            break
        near["joints"]["Root"]["position"][1] = round(near["joints"]["Root"]["position"][1] + depth + 0.03, 3)
        print(T, f"round {round_}: raised the key at {near['time']} by {depth + 0.03:.2f}")
    else:
        u = (t - k0["time"]) / (k1["time"] - k0["time"])
        nk = {"time": round(t, 3), "joints": {}}
        tor = lerp(k0["joints"]["Root"]["rotation"], k1["joints"]["Root"]["rotation"], u)
        p0, p1 = k0["joints"]["Root"]["position"], k1["joints"]["Root"]["position"]
        nk["joints"]["Root"] = {"rotation": [round(x, 1) for x in tor], "position": [round(p0[0] + (p1[0] - p0[0]) * u, 3), 0, round(p0[2] + (p1[2] - p0[2]) * u, 3)]}
        nk["joints"]["Neck"] = {"rotation": [round(x, 1) for x in lerp(k0["joints"]["Neck"]["rotation"], k1["joints"]["Neck"]["rotation"], u)]}
        aims, fronts = {}, {}
        for j in JOINTS:
            if "aimAt" in k0["joints"][j] and "aimAt" in k1["joints"][j] and k0["joints"][j]["aimAt"] == k1["joints"][j]["aimAt"]:
                nk["joints"][j] = {"aimAt": list(k0["joints"][j]["aimAt"])}
                aims[j] = [0, -1, 0]; fronts[j] = [0, 0, 1]
                continue
            a0 = k0["joints"][j].get("aim") or [0, -1, 0]; a1 = k1["joints"][j].get("aim") or [0, -1, 0]
            a = norm(lerp(a0, a1, u))
            nk["joints"][j] = {"aim": [round(x, 3) for x in a]}
            if "bendToward" in k0["joints"][j] and "bendToward" in k1["joints"][j]:
                b = norm(lerp(k0["joints"][j]["bendToward"], k1["joints"][j]["bendToward"], u))
                nk["joints"][j]["bendToward"] = [round(x, 3) for x in b]
                fronts[j] = b
            else:
                fronts[j] = [0, 0, 1]
            aims[j] = a
        y = -3 - lowest_point(tor, aims, fronts) + 0.05
        nk["joints"]["Root"]["position"][1] = round(max(y, lerp([k0["joints"]["Root"]["position"][1]], [k1["joints"]["Root"]["position"][1]], u)[0] + depth + 0.03), 3)
        ks.insert(i1, nk)
        print(T, f"round {round_}: key added at {t} (sank {depth})")
    json.dump(doc, open(path, "w", encoding="utf-8"), indent=1)
else:
    print(T, "still sinking after", ROUNDS, "rounds")
