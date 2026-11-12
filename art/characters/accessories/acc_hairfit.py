"""Per-hair fits for the head pieces: no hair strand may pass through a hat, a veil or a mask.

E:/Blender/blender.exe -b --factory-startup -P acc_hairfit.py -- [--root E:/NH-Work/acc] [--items Hats,Masks]

For every head piece (layout mount Head) and every rigged hair the barber sells (E:/NH-Work/hair_rigged, worn at its
in-game size), finds the cheapest fit with no triangle of the hair crossing the piece:
  hats and veils   a uniform scale k (1.00 .. 1.40) about the headband centre (0, 0, SEAT) and a lift dz (0 .. 0.30)
  masks            a radial scale k (1.00 .. 1.12) about the head's axis, no lift (the eye holes stay on the eyes)
then adds a margin (k + 0.02) for strands that sway under a brim. Hair inside a crown is hidden and allowed; hair that
pokes through is not. No fit within the limits -> null: the Wardrobe and the server don't let that hair wear it.
Writes layout/<Item>.json pieces[<piece>]["hair_fit"] = { <RigSource>: [k, dz] | null } and prints a table.
"""
import bpy, json, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
ONLY = argv[argv.index("--items") + 1].split(",") if "--items" in argv else None
SEAT = 1.93
MASKS = {"LaceMask", "LaceMaskTrim", "BoneMask", "GiltMask",   # Kit A
         "KintsugiMask", "WatchMask", "FoxMask", "WolfMask", "GrilleMask", "WaxMask", "MothMask", "DominoMask"}   # Kit C


def tris_of(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    v = [ob.matrix_world @ x.co for x in me.vertices]
    t = [tuple(x.vertices) for x in me.loop_triangles]
    ev.to_mesh_clear()
    return v, t


def main():
    import nh_acc as A
    bpy.ops.wm.read_factory_settings(use_empty=True)
    hairs, hair_free = {}, {}

    def in_body(p):
        """inside the R6 torso or head (a strand that already sinks into the body there is the hair's own clip:
        a piece lying on that surface doesn't make it any worse)"""
        if abs(p.x) <= 1.0 and abs(p.y) <= 0.5 and abs(p.z) <= 1.0:
            return True
        r = math.hypot(p.x, p.y)
        return 0.9 <= p.z <= 2.1 and r <= 0.6 - max(0.0, abs(p.z - 1.5) - 0.35)
    for h in sorted(A._hair_attach()):
        ob = A.real_hair(h)
        if ob is None:
            continue
        v, t = tris_of(ob)
        hairs[h] = BVHTree.FromPolygons(v, t, epsilon=0.0)
        hair_free[h] = [not in_body(sum((v[i] for i in tri), Vector()) / 3) for tri in t]
        bpy.data.objects.remove(ob)
    print("HAIRFIT hairs", len(hairs))
    items = sorted(f[:-5] for f in os.listdir(os.path.join(ROOT, "layout")) if f.endswith(".json"))
    if ONLY:
        items = [i for i in items if i in ONLY]
    for it in items:
        lp = os.path.join(ROOT, "layout", f"{it}.json")
        lay = json.load(open(lp))
        heads = list(lay["pieces"])   # head pieces get a fit; any other piece is either clear of a hair or not
        if not heads:
            continue
        for pn in heads:
            with bpy.data.libraries.load(os.path.join(ROOT, "blend", f"{it}.blend"), link=False) as (src, dst):
                dst.objects = [pn]
            ob = dst.objects[0]
            bpy.context.scene.collection.objects.link(ob)
            for md in list(ob.modifiers):
                ob.modifiers.remove(md)
            ob.parent = None
            v0, t = tris_of(ob)
            bpy.data.objects.remove(ob)
            is_mask = pn in MASKS
            on_head = lay["pieces"][pn]["mount"] == "Head"
            if not on_head:
                cands = [(1.0, 0.0)]   # torso and limb pieces can't move: they're compatible with a hair or not
            elif is_mask:
                cands = [(k, 0.0) for k in [1.0 + 0.01 * i for i in range(13)]]
            else:
                cands = [(1.0 + 0.02 * i, 0.02 * j) for i in range(21) for j in range(16)]
                cands.sort(key=lambda c: (c[0] - 1) + 1.5 * c[1])
            piv = Vector((0, 0, SEAT))
            fits = {}
            for h, hb in hairs.items():
                found = None
                for k, dz in cands:
                    if is_mask:
                        vv = [Vector((p.x * k, p.y * k, p.z)) for p in v0]
                    else:
                        vv = [piv + (p - piv) * k + Vector((0, 0, dz)) for p in v0]
                    ov = BVHTree.FromPolygons(vv, t, epsilon=0.0).overlap(hb)
                    free = hair_free[h]
                    if not any(free[j] for _, j in ov):
                        found = (round(min(k + 0.02, 1.42 if not is_mask else 1.14), 3) if on_head else 1.0, round(dz, 3))
                        break
                fits[h] = list(found) if found else None
            lay["pieces"][pn]["hair_fit"] = fits
            ok = [f for f in fits.values() if f]
            print(f"HAIRFIT {it}/{pn}: {len(ok)}/{len(fits)} hairs fit; k {min((f[0] for f in ok), default=0):.2f}.."
                  f"{max((f[0] for f in ok), default=0):.2f}, lift up to {max((f[1] for f in ok), default=0):.2f}; "
                  f"no fit: {', '.join(h for h, f in fits.items() if not f) or '-'}")
        json.dump(lay, open(lp, "w"), indent=1)


if __name__ == "__main__":
    main()
