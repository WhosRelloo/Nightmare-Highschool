"""NH transformation forms: wing and horn style libraries, customization grid and looping animations (Blender 5.2, headless).

E:/Blender/blender.exe -b --factory-startup -P forms_showcase.py -- --mode wings|horns|custom|anim [--style nocturne] --out <dir> [--quick]
"""
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nhfig import *          # noqa: F401,F403
import nhfig
import hqwing

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/ClaudeTemp/nhart/out/forms"
QUICK = "--quick" in argv
MODE = argv[argv.index("--mode") + 1] if "--mode" in argv else "wings"
STYLE = argv[argv.index("--style") + 1] if "--style" in argv else "nocturne"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
for k, c in {"Pale": (0.86, 0.78, 0.77), "Deep": (0.42, 0.28, 0.2), "Ash": (0.6, 0.62, 0.66), "Grave": (0.46, 0.51, 0.42), "Warm": (0.74, 0.55, 0.42)}.items():
    nhfig.SKIN[k] = node_mat("Skin" + k, c, rough=0.5, sss=0.25)[0]
M["blazer"] = node_mat("Blazer", (0.07, 0.06, 0.09), rough=0.7)[0]
EYE = decal_mat("EyeGlow", (1.0, 0.08, 0.1), (0.6, 0.0, 0.02), softness=0.1, rough=0.2, noise_scale=1, emit=(1, 0.08, 0.1), emit_str=8)


def figure(tag, body, gender, skin_key, x, rotz=180, wing=None, horn=None, wing_pose=(0.05, 14, 0, 0)):
    """wing = (style, palette, finish, size) ; horn = (kind, finish, tip)."""
    coll, o = load_rig(tag)
    arm = o["arm"]
    if body != "standard":
        swap_body(o, body, coll)
    skin(o, skin_key, top="blazer", legs="skirt" if gender == "F" else "trousers")
    bpy.context.view_layer.update()
    face(tag, o, "grim")
    for ob in sc.objects:
        if ob.name.startswith(f"{tag}Eye"):
            ob.data.materials.clear(); ob.data.materials.append(EYE)
    wings = []
    if wing:
        style, pal, fin, size = wing
        mats = hqwing.wing_mats(pal, fin, tag, style)
        for sx in (-1, 1):
            w = hqwing.Wing(sx, (0.42 * sx, -0.5, 3.72), size=size, style=style, seed=7 + sx)
            for ob in w.build(f"{tag}W{sx}", mats, mesh_obj, add_mods, pose=wing_pose):
                for c in list(ob.users_collection):
                    c.objects.unlink(ob)
                coll.objects.link(ob)
                copy_weights(ob, o["Torso"], arm)
            wings.append(w)
    if horn:
        kind, fin, tip = horn
        hm = hqwing.horn_mats(fin, tip, tag)
        for part, (v, f) in hqwing.horns(kind, Vector((0, 0, 4.5))).items():
            ob = mesh_obj(f"{tag}Horn_{part}", v, f, hm[part])
            add_mods(ob, subd=1)
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            coll.objects.link(ob)
            copy_weights(ob, o["Head"], arm)
    pose(arm, "R A", "X", 25); pose(arm, "R E", "X", 30); pose(arm, "R A", "Y", -8)
    pose(arm, "L A", "X", 15); pose(arm, "L E", "X", 40); pose(arm, "L A", "Y", 10)
    pose(arm, "Head", "X", 4)
    rest = arm.matrix_world.copy()
    base = arm.location.copy()
    arm.location = (base.x + x, base.y, base.z)
    arm.rotation_euler = (0, 0, math.radians(rotz))
    bpy.context.view_layer.update()
    return arm, rest, wings


def stage():
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
    m, nt, b = node_mat("Floor", (0.02, 0.018, 0.022), rough=0.6); add_bump(nt, b, 2.5, 0.2)
    bpy.context.active_object.data.materials.append(m)
    world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.007, 0.012, 1)
    cam_d = bpy.data.cameras.new("Cam"); cam = link(bpy.data.objects.new("Cam", cam_d)); sc.camera = cam
    return cam, cam_d


def rig_lights(prefix, target, k=1.0):
    t = Vector(target)
    def light(name, off, energy, color, size):
        L = bpy.data.lights.new(prefix + name, "AREA"); L.energy = energy * k; L.color = color; L.size = size
        ob = link(bpy.data.objects.new(prefix + name, L)); ob.location = t + Vector(off)
        ob.rotation_euler = (t - ob.location).to_track_quat("-Z", "Y").to_euler()
    light("Key", (7, 12, 7), 2600, (1.0, 0.88, 0.8), 6)
    light("Fill", (-10, 8, 2), 700, (0.55, 0.65, 1.0), 8)
    light("Back", (0, -10, 3), 1300, (1.0, 0.55, 0.5), 6)
    light("Top", (-4, -6, 11), 1600, (0.7, 0.8, 1.0), 4)


def cycles(samples):
    sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    grade()


def grade():
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass


def shoot(cam, cam_d, path, loc, aim, lens, w, h):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)


BODIES = [("muscular", "M", "Pale"), ("petite", "F", "Deep"), ("stocky", "M", "Ash"), ("curvy", "F", "Pale"),
          ("athletic", "M", "Grave"), ("toned", "F", "Warm"), ("heavy", "M", "Deep")]

if MODE == "wings":
    looks = [("nocturne", "Wine", "Obsidian", 1.2), ("wyrm", "Bloodstone" if False else "Wine", "Bloodstone", 1.15),
             ("tattered", "Ashen", "Bone", 1.2), ("fallen", "Raven", "Obsidian", 1.15), ("ossuary", "Wine", "Bone", 1.2),
             ("wraithveil", "Midnight", "Ivory", 1.2), ("rime", "Midnight", "Ivory", 1.15)]
    figs = []
    for i, (style, pal, fin, size) in enumerate(looks):
        b, g, sk = BODIES[i]
        x = i * 16.0
        arm, rest, _ = figure("ABCDEFG"[i], b, g, sk, x, rotz=180 + 28, wing=(style, pal, fin, size))
        figs.append((style, x))
        rig_lights(f"L{i}", (x, 0, 3.8))
    cam, cam_d = stage()
    cycles(24 if QUICK else 128)
    W = 640 if QUICK else 1300
    for style, x in figs:
        shoot(cam, cam_d, os.path.join(OUT, f"wing_{style}.png"), (x + 5.6, 9.2, 6.3), (x, -0.4, 4.1), 32, W, W)

elif MODE == "horns":
    kinds = [("ram", "Ivory", "Gilded"), ("demon", "Obsidian", "Bloodstone"), ("wendigo", "Bone", "Bone"), ("thorn", "Obsidian", "Obsidian"),
             ("broken", "Bloodstone", "Gilded"), ("sovereign", "Ivory", "Gilded"), ("bull", "Obsidian", "Ivory")]
    figs = []
    for i, (kind, fin, tip) in enumerate(kinds):
        b, g, sk = BODIES[i]
        x = i * 8.0
        arm, rest, _ = figure("ABCDEFG"[i], b, g, sk, x, rotz=-20, horn=(kind, fin, tip))
        head = arm.matrix_world @ rest.inverted() @ Vector((0, 0, 4.9))
        figs.append((kind, x, head))
        rig_lights(f"L{i}", tuple(head), k=0.35)
    cam, cam_d = stage()
    cycles(24 if QUICK else 128)
    W = 640 if QUICK else 1100
    for kind, x, head in figs:
        shoot(cam, cam_d, os.path.join(OUT, f"horn_{kind}.png"), head + Vector((4.6, 3.9, 1.2)), head + Vector((0, -0.2, 0.35)), 50, W, W)

elif MODE == "custom":
    # one style, the palette x finish options a player picks from, each on a different body
    opts = [("Wine", "Obsidian"), ("Midnight", "Gilded"), ("Ashen", "Bone"), ("Ember", "Obsidian"), ("Dove", "Ivory"), ("Raven", "Bloodstone")]
    figs = []
    for i, (pal, fin) in enumerate(opts):
        b, g, sk = BODIES[i]
        x = i * 16.0
        figure("ABCDEF"[i], b, g, sk, x, rotz=180 + 28, wing=(STYLE, pal, fin, 1.1))
        figs.append((pal, fin, x))
        rig_lights(f"L{i}", (x, 0, 3.8))
    cam, cam_d = stage()
    cycles(24 if QUICK else 112)
    W = 560 if QUICK else 1000
    for pal, fin, x in figs:
        shoot(cam, cam_d, os.path.join(OUT, f"custom_{STYLE}_{pal}_{fin}.png"), (x + 7.5, 12.0, 6.6), (x, 0, 3.9), 34, W, W)

elif MODE == "anim":
    N = 32
    pal, fin = {"fallen": ("Raven", "Obsidian"), "wraithveil": ("Midnight", "Ivory"), "rime": ("Midnight", "Ivory"),
                "ossuary": ("Wine", "Bone"), "tattered": ("Ashen", "Bone"), "wyrm": ("Wine", "Bloodstone")}.get(STYLE, ("Wine", "Obsidian"))
    arm, rest, wings = figure("A", "muscular", "M", "Pale", 0.0, rotz=180 + 30, wing=(STYLE, pal, fin, 1.2), horn=("demon", "Obsidian", "Bloodstone") if STYLE in ("nocturne", "wyrm") else None)

    def wpose(i):
        t = i / N
        flap = 34 * math.sin(2 * math.pi * t) + 6
        lag = -16 * math.sin(2 * math.pi * t - 0.9)
        fold = 0.12 + 0.18 * (0.5 - 0.5 * math.cos(2 * math.pi * t)) * (1 if math.sin(2 * math.pi * t) > 0 else 0.3)
        return (fold, flap, lag, t)
    frames = {}
    for w in wings:
        per = [w.frame_verts(wpose(i)) for i in range(N + 1)]
        for key, ob in w.objs.items():
            frames[ob] = [p[key] for p in per]
    hqwing.animate_shapes(frames, N + 1, start=1)
    for i in range(N + 1):
        arm.location.z = rest.translation.z + 0.12 * math.sin(2 * math.pi * i / N + math.pi)
        arm.keyframe_insert("location", index=2, frame=1 + i)
    sc.frame_start, sc.frame_end = 1, N
    sc.render.fps = 24
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = 16 if QUICK else 64
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    grade()
    cam, cam_d = stage()
    rig_lights("L", (0, 0, 3.8))
    cam.location = (6.2, 9.8, 6.0); cam_d.lens = 28
    cam.rotation_euler = (Vector((0, 0, 4.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    W = 640 if QUICK else 1280
    sc.render.resolution_x, sc.render.resolution_y = W, int(W * 9 / 16)
    d = os.path.join(OUT, f"anim_{STYLE}"); os.makedirs(d, exist_ok=True)
    sc.render.filepath = d + "/"
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
    print("ANIM DONE", d)
print("DONE")
