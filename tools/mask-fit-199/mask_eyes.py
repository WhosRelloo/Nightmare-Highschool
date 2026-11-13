"""Where are each face piece's eye holes? Front projection of the piece (as worn: its layout fit on the standard head),
rasterised at 2 mm; around each eye (x = +-0.205) the uncovered cells inside the mask's outline are the hole.
E:/Blender/blender.exe -b --factory-startup -P mask_eyes.py -- out.json
Prints, per piece: the hole centres (Roblox head space, y up from the head centre) or "no hole".
"""
import bpy, json, os, sys, math
from mathutils import Vector

ROOT = "E:/NH-Work/acc"
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "mask_eyes.json"
res = {}
for f in sorted(os.listdir(os.path.join(ROOT, "layout"))):
    if not f.endswith(".json") or f.endswith(".extra.json"):
        continue
    lay = json.load(open(os.path.join(ROOT, "layout", f)))
    it = f[:-5]
    for pn, e in lay.get("pieces", {}).items():
        if e.get("mount") != "Head":
            continue
        bp = os.path.join(ROOT, "blend", f"{it}.blend")
        if not os.path.exists(bp):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        with bpy.data.libraries.load(bp, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n == pn]
        if not dst.objects:
            continue
        ob = dst.objects[0]
        bpy.context.scene.collection.objects.link(ob)
        for md in list(ob.modifiers):
            if md.type == "ARMATURE":
                ob.modifiers.remove(md)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        M = ob.matrix_world
        V = [M @ v.co for v in me.vertices]
        # Blender: x right, y depth (front = -y), z up; head centre (0, 0, 1.5). Only the front half (y < 0).
        tris = [[V[i] for i in t.vertices] for t in me.loop_triangles]
        ev.to_mesh_clear()
        cell = 0.004
        xs, zs = (-0.55, 0.55), (1.0, 2.0)
        nx, nz = int((xs[1] - xs[0]) / cell), int((zs[1] - zs[0]) / cell)
        cov = bytearray(nx * nz)
        for T in tris:
            if all(p.y > 0.05 for p in T):
                continue
            minx = max(0, int((min(p.x for p in T) - xs[0]) / cell)); maxx = min(nx - 1, int((max(p.x for p in T) - xs[0]) / cell))
            minz = max(0, int((min(p.z for p in T) - zs[0]) / cell)); maxz = min(nz - 1, int((max(p.z for p in T) - zs[0]) / cell))
            (a, b, c) = [(p.x, p.z) for p in T]
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            for ix in range(minx, maxx + 1):
                x = xs[0] + (ix + 0.5) * cell
                for iz in range(minz, maxz + 1):
                    z = zs[0] + (iz + 0.5) * cell
                    l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (z - c[1])) / den
                    l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (z - c[1])) / den
                    if l1 >= 0 and l2 >= 0 and l1 + l2 <= 1:
                        cov[iz * nx + ix] = 1
        holes = []
        for sx in (-1, 1):
            # flood the uncovered region from the expected eye centre, if it's enclosed by the mask in a box round it
            best = None
            for zc in [1.50 + 0.01 * k for k in range(-6, 16)]:
                ix, iz = int((sx * 0.205 - xs[0]) / cell), int((zc - zs[0]) / cell)
                if cov[iz * nx + ix]:
                    continue
                seen, stack, cells, open_ = set(), [(ix, iz)], [], False
                while stack and len(cells) < 6000:
                    i, k = stack.pop()
                    if (i, k) in seen or not (0 <= i < nx and 0 <= k < nz) or cov[k * nx + i]:
                        continue
                    seen.add((i, k)); cells.append((i, k))
                    if abs(xs[0] + i * cell - sx * 0.205) > 0.22 or abs(zs[0] + k * cell - 1.55) > 0.25:
                        open_ = True
                        break
                    stack += [(i + 1, k), (i - 1, k), (i, k + 1), (i, k - 1)]
                if not open_ and cells:
                    cxm = sum(xs[0] + (i + 0.5) * cell for i, _ in cells) / len(cells)
                    czm = sum(zs[0] + (k + 0.5) * cell for _, k in cells) / len(cells)
                    best = (round(cxm, 4), round(czm - 1.5, 4), len(cells))
                    break
            holes.append(best)
        res[f"{it}/{pn}"] = {"fit": e.get("fit"), "holes": holes}
        print("MASKEYES", it, pn, holes, flush=True)
json.dump(res, open(OUT, "w"), indent=1)
