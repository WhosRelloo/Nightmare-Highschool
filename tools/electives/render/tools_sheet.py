"""Close-up of the five Anatomy tools on the leather roll.  blender -b -P tools_sheet.py -- <maps> <out.png> [samples]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
MAPS, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
import mats_lib  # noqa: E402
import tools_lib as T  # noqa: E402

scene = bpy.context.scene
M = mats_lib.make(MAPS)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
roll = bpy.context.active_object
roll.scale = (0.9, 0.36, 1)
bpy.ops.object.transform_apply(scale=True)
roll.data.materials.append(M["leather"])
for x in (-0.32, -0.16, 0.0, 0.16, 0.32):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, 0, 0.0008))
    s = bpy.context.active_object
    s.scale = (0.12, 0.28, 1)
    bpy.ops.object.transform_apply(scale=True)
    s.data.materials.append(M["leather_dk"])

def rest_on(r, z):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = 1e9
    for o in r.children_recursive:
        if o.type in ("MESH", "CURVE"):
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            lo = min([lo] + [(o.matrix_world @ v.co).z for v in me.vertices])
            ev.to_mesh_clear()
    r.location.z += z - lo
    bpy.context.view_layer.update()


Z = 0.0011   # just above the slot surface
rest_on(T.build_pinkey(M, (-0.32, -0.06, 0.03), (0, 0, 0)), Z)
rest_on(T.build_screwdriver(M, (-0.16, -0.125, 0.03), (0, 0, 0)), Z)
rest_on(T.build_tweezers(M, (0.0, -0.095, 0.03), (0, math.radians(35), 0), gap=0.014), Z)
rest_on(T.build_loupe(M, (0.16, -0.115, 0.03), (0, 0, 0)), Z)
rest_on(T.build_scalpel(M, (0.32, -0.12, 0.03), (0, 0, 0)), Z)
if len(argv) > 3 and argv[3] == "check":
    import clipcheck
    clipcheck.run(OUT)
    raise SystemExit(0)

bpy.ops.object.light_add(type="AREA", location=(-0.35, -0.3, 0.6))
k = bpy.context.active_object
k.data.energy = 22
k.data.size = 0.5
k.data.color = (1.0, 0.86, 0.7)
k.rotation_euler = (Vector((0, 0, 0)) - k.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(0.45, 0.4, 0.35))
r = bpy.context.active_object
r.data.energy = 10
r.data.size = 0.6
r.data.color = (0.55, 0.65, 1.0)
r.rotation_euler = (Vector((0, 0, 0)) - r.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(0.0, 0.0, 0.8))
t = bpy.context.active_object
t.data.energy = 6
t.data.size = 1.2

w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.016, 0.014, 1)
scene.world = w

bpy.ops.object.camera_add(location=(0, -0.42, 0.62))
cam = bpy.context.active_object
cam.data.lens = 32
cam.rotation_euler = (Vector((0, -0.005, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 700
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
