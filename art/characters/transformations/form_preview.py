"""Check sheet for baked form FBX: re-imports each file (proves the export), poses the wing bones (rest, half-fold, flap)
and renders back / side / 3-4 views with Workbench into one PNG per file.

E:/Blender/blender.exe -b --factory-startup -P form_preview.py -- --dir E:/NH-Work/forms [--match Nocturne]
"""
import bpy, math, os, sys
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DIR = argv[argv.index("--dir") + 1]
MATCH = argv[argv.index("--match") + 1] if "--match" in argv else ""
os.makedirs(os.path.join(DIR, "check"), exist_ok=True)

POSES = {  # bone -> (x, y, z) degrees, applied in pose mode
    "rest": {},
    "fold": {"Hum": (0, 0, 35), "Fore": (0, 0, -95), "D1a": (0, 0, -40), "D2a": (0, 0, -45), "D3a": (0, 0, -50), "D4a": (0, 0, -55)},
    "flap": {"Hum": (0, 40, 0), "Fore": (0, 15, 0), "D1b": (0, 20, 0), "D2b": (0, 20, 0), "D3b": (0, 20, 0), "D4b": (0, 20, 0)},
}
VIEWS = {"back": (0, -1, 0.15), "side": (1, 0, 0.1), "q34": (0.7, -0.7, 0.35)}   # camera direction from the target (Blender, after import)


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 12; sc.cycles.use_denoising = True
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.34, 0.38, 1)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    sc.render.resolution_x, sc.render.resolution_y = 420, 420
    sc.render.film_transparent = False
    return sc


def render_file(path):
    sc = setup()
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in sc.objects if o.type == "MESH"]
    arms = [o for o in sc.objects if o.type == "ARMATURE"]
    cols = [(0.35, 0.05, 0.08, 1), (0.85, 0.8, 0.7, 1), (0.6, 0.6, 0.65, 1)]
    for i, o in enumerate(meshes):
        m = bpy.data.materials.new(f"chk{i}"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = cols[i % 3]
        o.data.materials.clear(); o.data.materials.append(m)
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2; rad = (hi - lo).length * 0.75
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = rad * 2.0
    cam.data.clip_start = rad * 0.01; cam.data.clip_end = rad * 100   # the FBX round-trip lands at 1/100 size
    tiles = []
    base = os.path.splitext(os.path.basename(path))[0]
    for pn, pose in POSES.items():
        for a in arms:
            for pb in a.pose.bones:
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = Euler([math.radians(x) for x in pose.get(pb.name, (0, 0, 0))])
        bpy.context.view_layer.update()
        for vn, d in VIEWS.items():
            dv = Vector(d).normalized()
            cam.location = c + dv * rad * 4
            cam.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
            out = os.path.join(DIR, "check", f"_{base}_{pn}_{vn}.png")
            sc.render.filepath = out
            bpy.ops.render.render(write_still=True)
            tiles.append(out)
    # one sheet: rows = poses, cols = views
    imgs = [bpy.data.images.load(t) for t in tiles]
    w, h = imgs[0].size
    nc, nr = len(VIEWS), len(POSES)
    sheet = bpy.data.images.new(base, w * nc, h * nr)
    px = [0.0] * (w * nc * h * nr * 4)
    for k, im in enumerate(imgs):
        r, cc = divmod(k, nc); r = nr - 1 - r
        src = list(im.pixels)
        for y in range(h):
            row0 = ((r * h + y) * w * nc + cc * w) * 4
            px[row0:row0 + w * 4] = src[y * w * 4:(y + 1) * w * 4]
    sheet.pixels = px
    sheet.filepath_raw = os.path.join(DIR, "check", f"{base}.png"); sheet.file_format = "PNG"; sheet.save()
    for t in tiles:
        os.remove(t)
    print("sheet", sheet.filepath_raw)


for f in sorted(os.listdir(os.path.join(DIR, "fbx"))):
    if f.endswith(".fbx") and MATCH in f:
        render_file(os.path.join(DIR, "fbx", f))
