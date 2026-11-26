"""Clipping check: every pair of mesh objects whose surfaces intersect (BVH triangle overlap).
Tools count as one assembly each (their own parts may touch). Prints material, centre and size per hit."""
from fnmatch import fnmatch

import bpy
from mathutils.bvhtree import BVHTree

# intended joins: parts that are built into each other (seated, riveted, pinned, fused)
ALLOW = [
    ("FrogBody", "Rivet"), ("FrogBody", "Leg"), ("FrogBody", "FrogHead"), ("FrogBody", "Collar"), ("FrogBody", "KeyShaft"),
    ("FrogBody", "Hinge"), ("FrogBody", "Brace"), ("FrogBody", "Deck"),
    ("FrogHead", "Eye"), ("FrogHead", "Collar"), ("Eye", "Pupil"),
    ("Leg", "LegJoint"), ("Leg", "Foot"), ("Pin", "Foot"), ("Pin", "PinHead"), ("Pin", "Leg"), ("Hinge", "BellyPlate"), ("KeyShaft", "KeyBow"),
    ("Deck", "DeckScrew"), ("Deck", "Lung_Board"), ("Deck", "Gear_Axle"), ("Deck", "Barrel"), ("Deck", "Cradle_Post"),
    ("Gear", "Gear_Hub"), ("Gear", "Gear_Axle"), ("Gear_Hub", "Gear_Axle"),
    ("Lung_Board", "Lung_Pleat"), ("Lung_Pleat", "Lung_Pleat"), ("Lung_Port", "Lung_Pleat"), ("Lung_Port", "Lung_Board"),
    ("Pipe_Lung", "Lung_Board"), ("Pipe_Lung", "Cradle_Ring"), ("Cradle_*", "Cradle_*"),
    ("BellyPlate", "PlateRing"), ("BellyPlate", "PlateRivet"), ("PlateRing", "PlateRivet"),
    ("Heart", "HeartBand"), ("Heart", "HeartLug"), ("Heart", "HeartStub"),
    ("Candle", "CandleDish"), ("Candle", "Flame"),
    ("Wax", "Tray"), ("Roll", "Slot"), ("Chalk", "Slot"), ("Chalk", "Chalk"),
]


def base(o):
    return o.name.split(".")[0]


def allowed(a, b):
    x, y = base(a), base(b)
    return any((fnmatch(x, p) and fnmatch(y, q)) or (fnmatch(x, q) and fnmatch(y, p)) for p, q in ALLOW)


def root_of(o):
    while o.parent is not None:
        o = o.parent
    return o


def run(out_path):
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.context.scene.objects if o.type in ("MESH", "CURVE")]
    data = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        if me is None or len(me.polygons) == 0:
            ev.to_mesh_clear()
            continue
        mw = o.matrix_world
        verts = [mw @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False)
        xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
        lo = (min(xs), min(ys), min(zs)); hi = (max(xs), max(ys), max(zs))
        mat = o.active_material.name if o.active_material else "-"
        data.append((o, bvh, lo, hi, mat, root_of(o)))
        ev.to_mesh_clear()
    hits = []
    for i in range(len(data)):
        a = data[i]
        for j in range(i + 1, len(data)):
            b = data[j]
            if a[5] is b[5] and a[5].type == "EMPTY" and a[5].name.split(".")[0] in ("Screwdriver", "Tweezers", "Loupe", "PinKey", "Scalpel"):
                continue
            if allowed(a[0], b[0]):
                continue
            if any(a[3][k] < b[2][k] or b[3][k] < a[2][k] for k in range(3)):
                continue
            ov = a[1].overlap(b[1])
            if ov:
                hits.append((len(ov), a, b))

    def desc(d):
        o, _, lo, hi, mat, r = d
        c = tuple(round((lo[k] + hi[k]) / 2, 3) for k in range(3))
        s = tuple(round(hi[k] - lo[k], 3) for k in range(3))
        return f"{o.name}[{mat}] c={c} s={s}" + (f" <{r.name}>" if r is not o else "")

    with open(out_path, "w") as f:
        f.write(f"{len(data)} meshes, {len(hits)} intersecting pairs\n")
        for n, a, b in sorted(hits, key=lambda h: -h[0]):
            f.write(f"{n:5d}  {desc(a)}  X  {desc(b)}\n")
    print("CLIPCHECK", len(hits), out_path)
