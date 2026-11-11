"""Write ReplicatedStorage.Config.KitHolds (Luau) from the QOL kit's Blender layouts (E:/NH-Work/qol/layout/*.json).

python qol_holds.py [--out E:/NH-Work/qol/src/Config.KitHolds.luau]
Per item: R / L = shoulder (pitch, yaw) in degrees, Grip = the item's CFrame in the right arm's frame (12 numbers, the
item origin = the grip point), Pieces = each MeshPart's kind, size and bbox centre in item space (Roblox axes; the
importer centres every mesh on its box), Glow colour. Worn items (the keys) give Worn = the R6 part and character-space
centres (the rest nudge included).
"""
import json, os, sys

LAY = "E:/NH-Work/qol/layout"
argv = sys.argv[1:]
OUTP = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/qol/src/Config.KitHolds.luau"
ORDER = ["Lantern", "CampusMap", "Compass", "Umbrella", "Timetable", "KeyRing", "HallPass", "LibraryBook", "Thermos",
         "SnackTin", "FirstAid", "HandWarmer"]


def n(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def arr(a):
    return "{ " + ", ".join(n(float(x)) for x in a) + " }"


BODIES = json.load(open("E:/NH-Work/qol/bodies.json")).get("fits", {}) if os.path.exists("E:/NH-Work/qol/bodies.json") else {}
lines = ["--[[",
         "\tKit holds (generated: art/characters/qol/qol_holds.py from the Blender layouts; do not edit by hand).",
         "\tR / L = shoulder pitch, yaw (degrees) for Services.Features.Kit's pose; Grip = the item in the right arm's frame;",
         "\tPieces = each MeshPart's kind, size and centre in item space (Roblox axes). Worn = the R6 part it rides.",
         "\tFit = per body type (UI.Appearance.Bodies ids): the nudge that rests it on that body's hand (in the arm's frame),",
         "\tor off that body's leg (the keys), measured by qol_bodies.py; the game scales it with the character.",
         "]]", "return {"]
for key in ORDER:
    p = os.path.join(LAY, f"{key}.json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    h = d.get("hold", {})
    parts = [f"\t{key} = {{"]
    if "worn" in h:
        parts.append(f"\t\tWorn = `{h['worn']}`;")
        rest = h.get("rested", [0, 0, 0])
    else:
        rest = [0, 0, 0]
        parts.append(f"\t\tR = {arr(h['r'])};")
        if h.get("l"):
            parts.append(f"\t\tL = {arr(h['l'])};")
        parts.append(f"\t\tGrip = {arr(h['grip_in_arm'])};")
    fits = BODIES.get(key, {})
    nz = {b: v for b, v in fits.items() if b != "standard" and any(abs(x) > 1e-4 for x in v)}
    if nz:
        parts.append("\t\tFit = { " + "; ".join(f"{b} = {arr(v)}" for b, v in sorted(nz.items())) + " };")
    parts.append(f"\t\tTris = {d['tris']};")
    parts.append("\t\tPieces = {")
    for name, pc in d["pieces"].items():
        c = [pc["centre"][i] + rest[i] for i in range(3)]
        extra = f"; Glow = {arr(pc['glow'])}" if pc.get("glow") else ""
        parts.append(f"\t\t\t{name} = {{ Kind = `{pc['kind']}`; Size = {arr(pc['size'])}; Centre = {arr(c)}{extra} }};")
    parts.append("\t\t};")
    parts.append("\t};")
    lines += parts
lines.append("}")
open(OUTP, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print(OUTP, sum(1 for k in ORDER if os.path.exists(os.path.join(LAY, f'{k}.json'))), "items")
