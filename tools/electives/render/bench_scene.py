"""Concept render of the Anatomy bench (Clockwork Frog, level 1, lifting the heart-pump).

blender -b -P bench_scene.py -- <maps_dir> <out.png> [samples]
Materials use the school's seamless PBR sets (art/props/source/NH_<Set>_{color,normal,rough,metal}.png).
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
MAPS, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 96
MODE = argv[3] if len(argv) > 3 else ""
REST = MODE in ("export", "restcheck")   # the game's rest pose: plate shut, organs seated, every tool in its slot

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mats_lib  # noqa: E402
import tools_lib as T  # noqa: E402

M = mats_lib.make(MAPS)
M["wood"] = M["rosewood"]


# ------------------------------------------------------------------ helpers
def put(obj, mat, smooth=True):
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    if smooth and hasattr(obj.data, "polygons"):
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def sphere(loc, scale, mat, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    return put(o, mat)


def cyl(loc, r, depth, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    return put(bpy.context.active_object, mat, smooth=False)


def box(loc, size, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    if bevel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 3
    return put(o, mat, smooth=False)


def torus(loc, R, r, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=R, minor_radius=r, rotation=rot,
                                     major_segments=64, minor_segments=16)
    return put(bpy.context.active_object, mat)


def tube(points, r, mat):
    cu = bpy.data.curves.new("tube", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 6
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new("tube", cu)
    col.objects.link(o)
    o.data.materials.append(mat)
    return o


def gear(loc, R, thick, teeth, mat, rot_z=0.0):
    parts = [cyl(loc, R, thick, mat)]
    for k in range(teeth):
        a = rot_z + k * 2 * math.pi / teeth
        parts.append(box((loc[0] + math.cos(a) * R, loc[1] + math.sin(a) * R, loc[2]),
                         (R * 0.28, R * 0.22, thick), mat, rot=(0, 0, a)))
    parts.append(cyl((loc[0], loc[1], loc[2] + thick * 0.4), R * 0.25, thick * 1.2, M["steel"]))
    return parts


# ------------------------------------------------------------------ the desk and tray
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.05, 0))
desk = put(bpy.context.active_object, M["desk"], False)
desk.name = "Desk"
desk.scale = (2.4, 1.8, 1)
bpy.ops.object.transform_apply(scale=True)

box((0, 0.05, 0.0162), (0.60, 0.44, 0.032), M["iron"], bevel=0.008).name = "Tray"
box((0, 0.05, 0.03), (0.55, 0.39, 0.006), M["wax"], bevel=0.004).name = "Wax"   # sunk into the tray, top at 0.033

TZ = 0.034  # rest height on the wax (1 mm clear)

# ------------------------------------------------------------------ the frog (hollow automaton, frog_lib)
import frog_lib  # noqa: E402
FY = 0.06
HZ = TZ + 0.17
SPECIES = argv[4] if len(argv) > 4 else "Frog"
if SPECIES == "Frog":
    FROG = frog_lib.build_frog(M, (0, FY, TZ), plate_open_deg=95, heart_lifted=True, heart_z=HZ, rest=REST)

    # legs (brass tubes with joints), splayed and pinned; they start inside the shell and are carved flush
    LEGS = [
        [(0.06, FY + 0.07, TZ + 0.03), (0.13, FY + 0.12, TZ + 0.02), (0.17, FY + 0.17, TZ + 0.012)],
        [(0.065, FY - 0.07, TZ + 0.03), (0.15, FY - 0.09, TZ + 0.02), (0.12, FY - 0.15, TZ + 0.016), (0.2, FY - 0.18, TZ + 0.012)],
    ]
    for sx in (-1, 1):
        for leg in LEGS:
            pts = [(sx * p[0], p[1], p[2]) for p in leg]
            tube(pts, 0.011, M["brass"]).name = "Leg"
            for p in pts[1:-1]:
                sphere(p, (0.015,) * 3, M["brass_dark"], 24).name = "LegJoint"
            fx, fy, fz = pts[-1]
            sphere((fx, fy, fz), (0.024, 0.02, 0.006), M["brass"], 32).name = "Foot"
            cyl((fx, fy, fz + 0.03), 0.0018, 0.06, M["steel"]).name = "Pin"
            sphere((fx, fy, fz + 0.062), (0.007,) * 3, M["porcelain"], 24).name = "PinHead"

    # the key in its side, unwound: shaft through the wall, bow ring on its end
    cyl((0.115, FY - 0.01, TZ + 0.03), 0.004, 0.07, M["brass"], rot=(0, math.radians(90), 0)).name = "KeyShaft"
    torus((0.15, FY - 0.01, TZ + 0.03 + 0.014), 0.014, 0.004, M["brass"], rot=(0, math.radians(90), 0)).name = "KeyBow"

    carved = frog_lib.carve(FROG, list(bpy.data.objects))
    print("CARVED", carved)
else:   # the Raven or the Wyvern (species_lib), rest pose; opened for the close-up render
    import species_lib  # noqa: E402
    FROG = getattr(species_lib, "build_" + SPECIES.lower())(M, (0, FY, TZ))
    if not REST:
        bpy.data.objects["PlatePivot"].rotation_euler = (0, -math.radians(95), 0)
    print("CARVED", FROG["carved"])


def rest_on(rootobj, z):
    """Drop a tool so its lowest point sits at z."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = 1e9
    for o in rootobj.children_recursive:
        if o.type not in ("MESH", "CURVE"):
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            lo = min(lo, (mw @ v.co).z)
        ev.to_mesh_clear()
    rootobj.location.z += z - lo
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ the tool roll and tools
RY = -0.335
box((0, RY, 0.0032), (0.86, 0.30, 0.006), M["leather"], bevel=0.003).name = "Roll"
for k, x in enumerate((-0.3, -0.15, 0.0, 0.15, 0.3)):
    box((x, RY, 0.0067), (0.12, 0.27, 0.002), M["leather_dk"]).name = "Slot"
SLOT_TOP = 0.0077
# empty slots for the screwdriver (put down on the table) and the tweezers (in hand): chalk outlines
for x in ((-0.3, -0.15, 0.0, 0.15, 0.3) if (REST or SPECIES != "Frog") else (-0.15, 0.3)):
    for dx, dy, w, h in ((0, 0.125, 0.1, 0.002), (0, -0.125, 0.1, 0.002), (0.05, 0, 0.002, 0.25), (-0.05, 0, 0.002, 0.25)):
        box((x + dx, RY + dy, SLOT_TOP + 0.0005), (w, h, 0.001), M["chalk"]).name = "Chalk"

rest_on(T.build_pinkey(M, (-0.3, RY - 0.05, 0.05), (0, 0, 0)), SLOT_TOP + 0.0003)
rest_on(T.build_loupe(M, (0.0, RY - 0.105, 0.05), (0, 0, 0)), SLOT_TOP + 0.0003)
rest_on(T.build_scalpel(M, (0.15, RY - 0.125, 0.05), (0, 0, 0)), SLOT_TOP + 0.0003)
if REST or SPECIES != "Frog":   # the screwdriver and the tweezers in slots 2 and 5 (hotkey order: Key, Driver, Loupe, Scalpel, Tweezers)
    rest_on(T.build_screwdriver(M, (-0.15, RY - 0.122, 0.05), (0, 0, 0)), SLOT_TOP + 0.0003)
    rest_on(T.build_tweezers(M, (0.3, RY - 0.096, 0.05), (0, 0, 0), gap=0.006), SLOT_TOP + 0.0003)
# the screwdriver, put down on the desk beside the tray
if not (REST or SPECIES != "Frog"):
  rest_on(T.build_screwdriver(M, (0.36, -0.12, 0.05), (0, 0, math.radians(-32))), 0.0003)

# the tweezers in hand: heel toward camera-right, tips pinching the heart-pump's lug from either side
def _in_hand():
  lug, lc = FROG["lug"], FROG["lug_centre"]
  P = lc + Vector((0, 0, frog_lib.LUG_R))           # the top of the lug ring (its centreline)
  dirv = -Vector((0.2, -0.07, 0.08)).normalized()  # from the heel down to the tips
  q = dirv.to_track_quat("Y", "Z")
  ax = q @ Vector((1, 0, 0))                       # the axis the arms close along
  lug.rotation_mode = "QUATERNION"
  lug.rotation_quaternion = ax.to_track_quat("Z", "Y")   # the lug ring lies between the arms
  TIP = Vector((0, 0.1182, -0.0025))               # tweezers-local pinch point (u = 0.985)
  INNER = frog_lib.LUG_r + 0.0003                  # each arm's inner face this far from the ring's plane
  gap = (INNER / T.SCALE - 0.001727) / 0.4903
  tw = T.build_tweezers(M, (0, 0, 0), (0, 0, 0), gap=gap)
  tw.rotation_mode = "QUATERNION"
  tw.rotation_quaternion = q
  tw.location = P - q @ (TIP * T.SCALE)

if not (REST or SPECIES != "Frog"):
    _in_hand()

# a candle at the desk corner
cyl((-0.62, 0.36, 0.0042), 0.06, 0.008, M["brass"], verts=48).name = "CandleDish"
cyl((-0.62, 0.36, 0.068), 0.03, 0.12, M["candle"], verts=32).name = "Candle"
sphere((-0.62, 0.36, 0.148), (0.009, 0.009, 0.022), M["flame"], 24).name = "Flame"
bpy.ops.object.light_add(type="POINT", location=(-0.62, 0.36, 0.17))
cl = bpy.context.active_object
cl.data.energy = 5
cl.data.color = (1.0, 0.6, 0.3)
cl.data.shadow_soft_size = 0.02

# ------------------------------------------------------------------ lights, camera
bpy.ops.object.light_add(type="SPOT", location=(-0.32, -0.28, 1.25))
key = bpy.context.active_object
key.data.energy = 38
key.data.spot_size = math.radians(56)
key.data.spot_blend = 0.7
key.data.shadow_soft_size = 0.12
key.data.color = (1.0, 0.84, 0.66)
d = Vector((0, -0.05, 0)) - key.location
key.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(0.5, 0.8, 0.5))
rim = bpy.context.active_object
rim.data.energy = 7
rim.data.size = 0.8
rim.data.color = (0.5, 0.6, 1.0)
rim.rotation_euler = (math.radians(-60), math.radians(25), 0)
bpy.ops.object.light_add(type="AREA", location=(0.0, -0.9, 0.6))
fill = bpy.context.active_object
fill.data.energy = 2.5
fill.data.size = 1.0
fill.data.color = (1.0, 0.7, 0.45)
fill.rotation_euler = (math.radians(55), 0, 0)

world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.005, 0.008, 1)
scene.world = world

bpy.ops.object.camera_add(location=(0, -0.74, 0.7))
cam = bpy.context.active_object
cam.data.lens = 33
look = Vector((0, -0.07, 0.0)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = (Vector((0, FY, TZ + 0.06)) - cam.location).length
cam.data.dof.aperture_fstop = 5.6
scene.camera = cam
if len(argv) > 3 and argv[3] == "close":
    BCv = FROG["body_centre"]
    cam.location = (BCv.x + 0.07, BCv.y - 0.2, BCv.z + 0.24)
    cam.data.lens = 50
    cam.rotation_euler = (Vector((BCv.x, BCv.y + 0.005, BCv.z - 0.005)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = (BCv - cam.location).length
    cam.data.dof.aperture_fstop = 9.0

if MODE in ("export", "restcheck"):
    import clipcheck
    n = clipcheck.run(OUT if MODE == "restcheck" else os.path.join(os.path.dirname(os.path.abspath(__file__)), "clip_report_rest.txt"))
    if MODE == "export":
        if n:
            raise SystemExit(3)
        import export_bench
        export_bench.run(FROG, OUT, MAPS)
    raise SystemExit(0)
if len(argv) > 3 and argv[3] == "check":
    import clipcheck
    clipcheck.run(OUT)
    raise SystemExit(0)
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
