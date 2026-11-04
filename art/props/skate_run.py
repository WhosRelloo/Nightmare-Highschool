"""Build one batch 18 skateboard like nh_props.py does, then also render its underside and print each piece's
Roblox-local origin (X = -(x - cx), Y = z - zmin, Z = y - cy):

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/skate_run.py -- SkateboardRavens --size 2048 --samples 64 --gpu
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402  (parses the same -- arguments)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

name = P.PROP
P.run(name)
objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(name)]
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector((min(lo[i], w[i]) for i in range(3)))
        hi = Vector((max(hi[i], w[i]) for i in range(3)))
cx, cy, zmin = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z
for o in sorted(objs, key=lambda o: o.name):
    p = o.matrix_world.translation
    print(f"[skate] {o.name} origin Roblox ({-(p.x - cx):.3f}, {p.z - zmin:.3f}, {p.y - cy:.3f})")
# the underside: turn the board over about its long axis, lift it, and render from the same camera
for o in objs:
    o.matrix_world = Matrix.Translation((0, 0, 0.75)) @ Matrix.Rotation(math.pi, 4, "X") @ o.matrix_world
sc = bpy.context.scene
sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}_bottom.png")
bpy.ops.render.render(write_still=True)
op = os.path.join(P.OUT_PRE, f"{name}_open.png")
if os.path.exists(op):
    os.remove(op)
