"""Preview renders of the admin capes on a plain R6 mannequin (Cycles, CPU).

E:/Blender/blender.exe -b E:/NH-Work/capes/<Set>.blend -P cape_preview.py -- --key <Set> [--maps DIR] [--swing 0.6]
  [--female] [--res 700] [--samples 48]
Writes E:/NH-Work/capes/renders/<Set>[_swing][_f]_<view>.png. --swing poses each chain bone the way CapeSway does at
that swing (rotation about the torso's right axis, (depth - 1) * 0.12 per bone), to check the weights.
"""
import bpy, math, os, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
KEY = argv[argv.index("--key") + 1]
MAPS = argv[argv.index("--maps") + 1] if "--maps" in argv else None
SWING = float(argv[argv.index("--swing") + 1]) if "--swing" in argv else 0.0
FEMALE = "--female" in argv
RES = int(argv[argv.index("--res") + 1]) if "--res" in argv else 700
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 48
VIEWS = argv[argv.index("--views") + 1].split(",") if "--views" in argv else ["front34", "back", "side", "back34"]
OUT = "E:/NH-Work/capes/renders"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
ob = bpy.data.objects["CapeBody"]
arm = bpy.data.objects[f"{KEY}Rig"]


def mat(name, rgb, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def box(name, size, loc, m, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    md = o.modifiers.new("b", "BEVEL"); md.width = bevel; md.segments = 3
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


skin = mat("Skin", (0.62, 0.45, 0.36), 0.55)
cloth = mat("Coat", (0.035, 0.032, 0.04), 0.8)
trous = mat("Trousers", (0.025, 0.024, 0.03), 0.8)
box("Torso", (2, 1, 2), (0, 0, 0), cloth)
if FEMALE:  # a soft bust and hips, inside the torso box like the game's female body
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(0.34, -0.32, 0.35))
    s = bpy.context.object; s.scale = (1, 0.5, 0.8); s.data.materials.append(cloth)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(-0.34, -0.32, 0.35))
    s = bpy.context.object; s.scale = (1, 0.5, 0.8); s.data.materials.append(cloth)
for sx in (1, -1):
    box("Arm", (1, 1, 2), (sx * 1.5, 0, 0), cloth)
    box("Leg", (1, 1, 2), (sx * 0.5, 0, -2), trous)
bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.2, location=(0, 0, 1.5), vertices=32)
hd = bpy.context.object
md = hd.modifiers.new("b", "BEVEL"); md.width = 0.25; md.segments = 4
hd.data.materials.append(skin)
for p in hd.data.polygons:
    p.use_smooth = True
# hair cap so the collar/hood reads against something dark
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.66, location=(0, 0.06, 1.72))
hr = bpy.context.object; hr.scale = (1, 1, 0.75); hr.data.materials.append(mat("Hair", (0.02, 0.018, 0.02), 0.5))

# cape material
cm = bpy.data.materials.new("CapePBR")
cm.use_nodes = True
nt = cm.node_tree
bs = nt.nodes["Principled BSDF"]
if MAPS:
    def img(kind, non_color):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(MAPS, f"NHCape_{KEY}_{kind}.png"))
        if non_color:
            n.image.colorspace_settings.name = "Non-Color"
        return n
    c = img("color", False); nt.links.new(c.outputs["Color"], bs.inputs["Base Color"])
    r = img("roughness", True); nt.links.new(r.outputs["Color"], bs.inputs["Roughness"])
    mt = img("metalness", True); nt.links.new(mt.outputs["Color"], bs.inputs["Metallic"])
    n = img("normal", True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
else:
    bs.inputs["Base Color"].default_value = (0.35, 0.05, 0.08, 1)
    bs.inputs["Roughness"].default_value = 0.7
ob.data.materials.clear()
ob.data.materials.append(cm)

# CapeSway's pose: each chain bone (depth >= 2) about the torso right axis, -(depth-1)*0.12*swing (back)
if SWING:
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    right = Vector((-1, 0, 0))  # Roblox +X (character's right) = Blender -X
    for pb in arm.pose.bones:
        depth, p = 0, pb.parent
        while p:
            depth += 1; p = p.parent
        if depth < 2:
            continue
        ang = -(depth - 1) * 0.12 * SWING  # SIGN = -1: swings back, away from the body
        rest = pb.bone.matrix_local.to_3x3()
        axis = rest.inverted() @ right
        pb.rotation_mode = "AXIS_ANGLE"
        pb.rotation_axis_angle = (ang, *axis)
    bpy.ops.object.mode_set(mode="OBJECT")

# light and world
w = bpy.data.worlds.new("W"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.011, 0.016, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
for loc, energy, col, size in (((4, -6, 5), 900, (1.0, 0.82, 0.62), 3), ((-5, 5, 3), 700, (0.6, 0.66, 1.0), 3),
                               ((0, 6, 6), 500, (1.0, 0.9, 0.8), 4), ((-5, -4, -1), 200, (1, 0.8, 0.7), 4)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.object; L.data.energy = energy; L.data.color = col; L.data.size = size
    L.rotation_euler = (Vector((0, 0, -0.3)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -3.0))
bpy.context.object.data.materials.append(mat("Floor", (0.03, 0.028, 0.03), 0.9))

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * 1.15)
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 70
VIEW = {"front34": (5.5, -9.5, 2.2), "back": (0, 11, 1.8), "side": (11, 0.6, 1.4), "back34": (-7, 8.5, 3.0),
        "top": (0.01, 2.5, 10), "front": (0, -11, 1.6)}
tag = ("_swing" if SWING else "") + ("_f" if FEMALE else "")
for v in VIEWS:
    cam.location = VIEW[v]
    cam.rotation_euler = (Vector((0, 0, -0.35)) - Vector(VIEW[v])).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"{KEY}{tag}_{v}.png")
    bpy.ops.render.render(write_still=True)
print("[preview] done", KEY)
