"""Head pieces at every hair's fit against the admin capes (the clearance check tests hats at rest only).

E:/Blender/blender.exe -b --factory-startup -P acc_hatcapes.py -- [--root E:/NH-Work/acc] [--items Hats,...]

A head piece is worn scaled by k about the headband centre (0, 0, SEAT) and lifted by dz for each hair
(layout hair_fit, from acc_hairfit.py). For every head piece, every hair it fits and every cape, the piece is moved to
that fit and tested for crossing triangles against the cape at rest. Prints, per piece and cape, the hairs that cross:
a pair with any crossing needs a conflict (or a better fit).
"""
import bpy, json, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
ONLY = argv[argv.index("--items") + 1].split(",") if "--items" in argv else None
import acc_check as C   # mesh_tris, tri_bvh

SEAT = 1.93
bpy.ops.wm.read_factory_settings(use_empty=True)
capes = {}
for key in ("WardenMantle", "ReaperShroud", "DuelistCape", "CaptainGreatcape", "MidnightCollar"):
    bp = f"E:/NH-Work/capes/{key}.blend"
    if not os.path.exists(bp):
        continue
    with bpy.data.libraries.load(bp, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n == "CapeBody"]
    ob = dst.objects[0]
    bpy.context.scene.collection.objects.link(ob)
    for md in list(ob.modifiers):
        ob.modifiers.remove(md)
    ob.parent = None
    v, t = C.mesh_tris(ob)
    capes[key] = C.tri_bvh(v, t)
    bpy.data.objects.remove(ob)
items = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, "layout")) if f.endswith(".json") and not f.endswith(".extra.json"))
if ONLY:
    items = [i for i in items if i in ONLY]
for it in items:
    lay = json.load(open(os.path.join(ROOT, "layout", f"{it}.json")))
    heads = {n: e for n, e in lay["pieces"].items() if e["mount"] == "Head" and e.get("hair_fit")}
    if not heads:
        continue
    with bpy.data.libraries.load(os.path.join(ROOT, "blend", f"{it}.blend"), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in heads]
    for ob in dst.objects:
        if ob is None:
            continue
        bpy.context.scene.collection.objects.link(ob)
        v0, t = C.mesh_tris(ob)
        fits = heads[ob.name]["hair_fit"]
        piv = Vector((0, 0, SEAT))
        seen = {}
        for (k, dz) in sorted({tuple(f) for f in fits.values() if f}):
            vv = [piv + (p - piv) * k + Vector((0, 0, dz)) for p in v0]
            tree = C.tri_bvh(vv, t)
            for ck, ct in capes.items():
                if tree.overlap(ct):
                    seen.setdefault(ck, set()).add((k, dz))
        for ck, fset in seen.items():
            hairs = [h for h, f in fits.items() if f and tuple(f) in fset]
            print(f"HATCAPE {it}/{ob.name} x {ck}: {len(hairs)} hairs ({', '.join(sorted(hairs)[:5])}{'...' if len(hairs) > 5 else ''})")
        print(f"HATCAPE {it}/{ob.name}: checked {len({tuple(f) for f in fits.values() if f})} fits x {len(capes)} capes")
        bpy.data.objects.remove(ob)
print("HATCAPE done")
