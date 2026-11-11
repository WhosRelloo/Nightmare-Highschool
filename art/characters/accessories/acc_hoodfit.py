"""TatteredHood: per-hair fits that also keep the scaled hood off the shoulders and out of the arms' swing.
Same search as acc_hairfit.py (the same candidates in the same order, the same hair-crossing test, the same +0.02
margin), plus: wherever the fitted hood is over the torso (|x| < 1, |y| < 0.66) it stays at z >= 1.065 (above the
torso top and every strap / sash / collar lying on it), and past the shoulder (|x| > 0.99) at z >= 1.215 (the top of
the arms' swing). Rewrites layout/TatteredHood.json hair_fit (fits that already pass are unchanged).
E:/Blender/blender.exe -b --factory-startup -P hood_fit.py"""
import bpy, json, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = "E:/Nightmare-Highschool/art/characters/accessories"
sys.path.insert(0, HERE)
import nh_acc as A
ROOT = "E:/NH-Work/acc"
IT, PN = "TatteredHood", "TatteredHood"
SEAT = 1.93

def tris_of(ob):
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
    v = [ob.matrix_world @ x.co for x in me.vertices]; t = [tuple(x.vertices) for x in me.loop_triangles]
    ev.to_mesh_clear(); return v, t

def in_body(p):
    if abs(p.x) <= 1.0 and abs(p.y) <= 0.5 and abs(p.z) <= 1.0:
        return True
    r = math.hypot(p.x, p.y)
    return 0.9 <= p.z <= 2.1 and r <= 0.6 - max(0.0, abs(p.z - 1.5) - 0.35)

def body_ok(vv):
    for p in vv:
        if abs(p.x) < 1.0 and abs(p.y) < 0.66 and p.z < 1.065:
            return False
        if abs(p.x) > 0.99 and p.z < 1.215 and abs(p.y) < 1.3:
            return False
    return True

bpy.ops.wm.read_factory_settings(use_empty=True)
hairs, free = {}, {}
for h in sorted(A._hair_attach()):
    ob = A.real_hair(h)
    if ob is None:
        continue
    v, t = tris_of(ob)
    hairs[h] = BVHTree.FromPolygons(v, t, epsilon=0.0)
    free[h] = [not in_body(sum((v[i] for i in tri), Vector()) / 3) for tri in t]
    bpy.data.objects.remove(ob)
lp = os.path.join(ROOT, "layout", f"{IT}.json")
lay = json.load(open(lp))
with bpy.data.libraries.load(os.path.join(ROOT, "blend", f"{IT}.blend"), link=False) as (src, dst):
    dst.objects = [PN]
ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob)
for md in list(ob.modifiers):
    ob.modifiers.remove(md)
ob.parent = None
v0, t = tris_of(ob)
cands = [(1.0 + 0.02 * i, 0.02 * j) for i in range(21) for j in range(16)]
cands.sort(key=lambda c: (c[0] - 1) + 1.5 * c[1])
piv = Vector((0, 0, SEAT))
old = lay["pieces"][PN].get("hair_fit", {})
fits = {}
for h, hb in hairs.items():
    found = None
    for k, dz in cands:
        kk = round(min(k + 0.02, 1.42), 3)
        vv = [piv + (p - piv) * kk + Vector((0, 0, dz)) for p in v0]
        if not body_ok(vv):
            continue
        vh = [piv + (p - piv) * k + Vector((0, 0, dz)) for p in v0]
        ov = BVHTree.FromPolygons(vh, t, epsilon=0.0).overlap(hb)
        if not any(free[h][j] for _, j in ov):
            found = [kk, round(dz, 3)]
            break
    fits[h] = found
    print("HOODFIT", h, "acc_hairfit:", old.get(h), "-> with the body limits:", found)
lay["pieces"][PN]["hair_fit"] = fits
json.dump(lay, open(lp, "w"), indent=1)
ok = [f for f in fits.values() if f]
print(f"HOODFIT {len(ok)}/{len(fits)} hairs fit; no fit: {', '.join(h for h, f in fits.items() if not f) or '-'}")
