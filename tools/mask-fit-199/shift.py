"""Move face masks down so their eye holes meet the painted eyes. Blender -b -P shift.py -- <src_root> <dst_root> <json shifts>"""
import bpy, json, os, sys
a = sys.argv[sys.argv.index("--") + 1:]
SRC, DST, SH = a[0], a[1], json.loads(a[2])
for it, dz in SH.items():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(SRC, "blend", it + ".blend"))
    lay = json.load(open(os.path.join(SRC, "layout", it + ".json")))
    moved = []
    for pn, e in lay["pieces"].items():
        if e.get("mount") != "Head":
            continue
        ob = bpy.data.objects.get(pn)
        if ob is None:
            continue
        if ob.parent is None:
            ob.location.z += dz
        moved.append(pn)
        rig = bpy.data.objects.get(pn + "Rig")
        if rig is not None and rig.parent is None:
            rig.location.z += dz
        e["fit"][1] = e["fit"][1] + dz
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DST, "blend", it + ".blend"), copy=True)
    json.dump(lay, open(os.path.join(DST, "layout", it + ".json"), "w"), indent=1)
    print("SHIFTED", it, dz, moved, flush=True)
