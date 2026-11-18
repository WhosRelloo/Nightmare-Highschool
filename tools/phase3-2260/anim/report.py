"""Write REPORT.md: each target's source clip, measured numbers and retimed keys. usage: python -I report.py"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, "source", "_all.json"), encoding="utf-8"))
SPEC = json.load(open(os.path.join(HERE, "clips.json"), encoding="utf-8"))
J = ["LeftShoulder", "RightShoulder", "LeftHip", "RightHip"]

def swing(a):  # degrees forward of straight down (+ forward)
    return math.degrees(math.atan2(a["z"], -a["y"]))

def change(k0, k1):
    return sum(math.dist([k0["aims"][j][c] for c in "xyz"], [k1["aims"][j][c] for c in "xyz"]) for j in J)

lines = ["# Animation sourcing report (2.26.0, the Strikethrough)", "",
         "The owner's rule: reuse existing clips, and where none fits, derive from measured related clips.", "",
         "- **Measured by** `extract.luau`: forward kinematics on each clip's own rig. The R15 ghoul and stalker use",
         "  AnimationConstraints; the R6 clips use the AI rig.",
         "- **Converted by** `convert.py`:",
         "  - R15 arms aim shoulder to wrist and legs hip to ankle, so the elbow and knee fold into the R6 aim.",
         "  - Euler XYZ, as the tool applies `rotation`, with the reading nearest the previous key.",
         "  - Weight-0 placeholder poses are skipped.",
         "  - The source's fastest segment becomes the strike, retimed to the house-style phases.", "",
         "**Sign check:** the game's Knockback, converted raw and drawn by the animation tool, matches the real clip played on",
         "an R6 dummy at 0.17 s: head to the character's right, body rolled flat, limbs up and to the right. The Knockback is",
         "a real tumble of about 1.9 turns, in steps of 84 to 117 degrees between keys.", ""]
for name, spec in SPEC.items():
    src_name = spec["source"] if spec["source"] in SRC and "error" not in SRC[spec["source"]] else spec.get("alt")
    s = SRC[src_name]
    keys = s["keys"]
    best, si = -1, 1
    for i in range(1, len(keys)):
        dt = max(keys[i]["t"] - keys[i - 1]["t"], 1e-3)
        v = change(keys[i - 1], keys[i]) / dt
        if v > best: best, si = v, i
    pitch = [k["torso"]["pitch"] for k in keys]
    root_y = [k["root"]["y"] for k in keys]
    sw = {j: (round(min(swing(k["aims"][j]) for k in keys)), round(max(swing(k["aims"][j]) for k in keys))) for j in J}
    pose = json.load(open(os.path.join(HERE, "pose", f"{name}.json"), encoding="utf-8"))
    times = [k["time"] for k in pose["keyframes"]]
    src_times = ", ".join(f"{k['t']:.2f}" for k in keys[:14]) + (" ..." if len(keys) > 14 else "")
    lines += [f"## {name}", "",
              f"- **Source:** `{src_name}` ({s['rig']}, {s['length']:.2f} s, {len(keys)} keys)"
              + (f"; {', '.join(spec['blend'])} as reference" if spec.get("blend") else ""),
              f"- **Source key times:** {src_times}",
              f"- **Detected strike:** key {si} (t {keys[si]['t']:.2f} s; aim change {best:.1f} per s)",
              f"- **Target:** {spec['length']} s; anticipation {spec['phases']['anticipation']}, strike {spec['phases']['strike']}, "
              f"settle {spec['phases']['settle']}; contacts {spec['contacts']}; root drop {spec['drop']} studs"
              + ("; loop" if spec.get("loop") else ""),
              f"- **Measured:** torso pitch {min(pitch):.0f} to {max(pitch):.0f} degrees; root travel {max(root_y) - min(root_y):.2f} studs",
              "- **Limb swing** (degrees forward of straight down, min / max): "
              + "; ".join(f"{j} {a} / {b}" for j, (a, b) in sw.items()),
              f"- **Retimed keys:** {', '.join(str(t) for t in times[:14])}{' ...' if len(times) > 14 else ''}", ""]
open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="").write("\n".join(lines))
print("REPORT.md:", len(SPEC), "clips")
