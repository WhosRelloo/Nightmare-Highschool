"""Clearance of every QOL kit item in its hold pose on every body type (the 12 the game has).

E:/Blender/blender.exe -b --factory-startup -P qol_bodies.py -- [Item,Item...] [--json E:/NH-Work/qol/bodies.json]
Opens each item's saved scene (E:/NH-Work/qol/blend/<Item>.blend: the item placed at the hand), swaps the mannequin for
each body type posed the same way, and reports per body: intersecting triangle pairs, the deepest item vertex inside
any part, and the gap to the holding hand. Fails: any clip (> 0.003 or a crossing triangle), or a hover over 0.06.
"""
import bpy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTJ = argv[argv.index("--json") + 1] if "--json" in argv else "E:/NH-Work/qol/bodies.json"
sys.argv += ["--out", "E:/NH-Work/qol"]
import nh_qol as Q   # noqa: E402
A = Q.A

want = [a for a in argv if not a.startswith("--") and (argv.index(a) == 0 or not argv[argv.index(a) - 1].startswith("--"))]
items = want[0].split(",") if want else list(Q.ITEMS)
report, fails, fits = {}, [], {}
for key in items:
    path = os.path.join(Q.OUT, "blend", f"{key}.blend")
    if not os.path.exists(path):
        continue
    hold = Q.ITEMS[key]["hold"]
    report[key] = {}
    for body in A.BODY_IDS:
        bpy.ops.wm.open_mainfile(filepath=path)
        A._bodies.clear(); A._bvh_cache.clear()
        for o in list(bpy.data.objects):
            if o.get("nh_mannequin"):
                bpy.data.objects.remove(o)
        objs = {o.name: o for o in bpy.data.objects if o.type == "MESH" and o.get("nh_piece")}
        if not objs:   # joined pieces keep the piece name as the object name
            objs = {o.name: o for o in bpy.data.objects if o.type == "MESH" and not o.get("nh_stage") and not o.get("nh_mannequin")}
        man, parts = Q.posed_mannequin({} if "worn" in hold else hold, body)
        grip = "none" if "worn" in hold else hold.get("grip", "RightArm")
        # the body's fit: slide the item (out along the hand, or off the leg) until it touches without clipping
        from mathutils import Vector
        if "worn" in hold:
            mv = Q.rest_on(objs, parts, [hold["worn"]], hold.get("rest", (0, -1, 0)))
            fit = A.to_rbx(mv)
        else:
            Mr = Q.arm_matrix("R", *hold["r"])
            hands = ["RightArm"] + (["LeftArm"] if hold.get("l") else [])
            nr = Mr.to_3x3() @ Vector((0, 0, -1))
            if hold.get("l"):
                nr = (nr + Q.arm_matrix("L", *hold["l"]).to_3x3() @ Vector((0, 0, -1))).normalized()
            mv = Q.rest_on(objs, parts, hands, hold.get("push", nr))
            fit = A.to_rbx(Mr.to_3x3().inverted() @ mv)
        fits.setdefault(key, {})[body] = [round(v, 4) for v in fit]
        rep, fl = Q.clearance(objs, parts, grip_part=grip, also=hold.get("touch", ()))
        # bigger hands may leave a little air on slimmer bodies: a hover up to 0.06 is fine there
        fl = [f for f in fl if not (f.startswith("hovers") and float(f.split()[1]) <= 0.06)]
        report[key][body] = dict(fails=fl, hand=rep.get(grip, {}))
        if fl:
            fails.append(f"{key} on {body}: {fl}")
        print(f"[bodies] {key:12s} {body:9s} {'OK' if not fl else fl}")
json.dump(dict(report=report, fails=fails, fits=fits), open(OUTJ, "w"), indent=1)
print("[bodies] FAILS:", len(fails))
for f in fails:
    print("   ", f)
