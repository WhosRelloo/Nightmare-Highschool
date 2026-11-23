"""NH race transformations, Task 2 batch 1: Roblox-ready wing and horn meshes (Blender 5.2, headless).

E:/Blender/blender.exe -b --factory-startup -P form_models.py -- --out E:/NH-Work/forms [--only wings|horns] [--style nocturne]

WINGS: one FBX per style per side (NHWing_<Style>_<L|R>.fbx), a two-piece rig (the piece count the pipeline lessons
say imports cleanly): `<Style><L|R>Membrane` (membrane / feathers / mist / ice: tinted by the Wing palette) and
`<Style><L|R>Frame` (the bones, rim, spikes: tinted by the Bone finish), both skinned to one skeleton:
    Root (the shoulder-blade anchor, never animated) > Hum > Fore > D1a > D1b, ... D4a > D4b (3-digit styles stop at D3)
Bind pose = fully spread (fold 0, flap 0). Weights: inverse-distance to the bone segments, top 4, normalised; the
membrane's body edge rides Root. Ossuary's grave-cloth tatters go into the Membrane piece (tinted with it).
HORNS: one FBX per style (NHHorns_<Style>.fbx), static, import with rig OFF: `<Style>Horns`, `<Style>Tip`, and for
Sovereign `<Style>Halo` (spun by the client).
UVs are world-scaled (tileable maps from form_textures.py): 1 UV unit = TILE studs per material class.
Writes <out>/forms_fit.json: per file, the attach point, every piece's bounding-box centre relative to it in Roblox axes
(x right, y up, z back), tris, and the bone heads. Rig faces +Y here; the FBX axes map +Y to Roblox's front (-Z).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hqwing

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/forms"
ONLY = argv[argv.index("--only") + 1] if "--only" in argv else "all"
ONE = argv[argv.index("--style") + 1] if "--style" in argv else None
os.makedirs(os.path.join(OUT, "fbx"), exist_ok=True)

WING_ROOT_Y, WING_ROOT_Z, WING_ROOT_X = -0.5, 3.72, 0.42   # as in the approved concepts
TORSO_C = Vector((0, 0, 3.0))
HEAD_C = Vector((0, 0, 4.5))
TILE = {"membrane": 1.6, "feather": 1.2, "mist": 2.0, "ice": 1.0, "cloth": 0.8, "bone": 0.6, "horn": 0.5}
MEMBRANE_CLASS = {"nocturne": "membrane", "wyrm": "membrane", "tattered": "membrane", "fallen": "feather",
                  "ossuary": "cloth", "wraithveil": "mist", "rime": "ice"}
TRI_CAP = 20000


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_from(name, parts, subd=0):
    """parts: [(verts, faces, thick)] -> one object (solidified, applied; Catmull-Clark `subd` levels applied last)."""
    bm = bmesh.new()
    for verts, faces, thick in parts:
        me = bpy.data.meshes.new("_tmp")
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        if thick:
            ob = bpy.data.objects.new("_tmp", me)
            bpy.context.scene.collection.objects.link(ob)
            md = ob.modifiers.new("s", "SOLIDIFY"); md.thickness = thick; md.offset = 0.0
            dg = bpy.context.evaluated_depsgraph_get()
            me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            bm.from_mesh(me2)
            bpy.data.objects.remove(ob); bpy.data.meshes.remove(me2)
        else:
            bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if subd:
        md = ob.modifiers.new("sub", "SUBSURF"); md.levels = subd
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear(); old = ob.data; ob.data = me2; me2.name = name
        bpy.data.meshes.remove(old)
        for p in me2.polygons:
            p.use_smooth = True
    return ob


def world_uvs(ob, tile):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    me = ob.data
    uv = me.uv_layers.active.data
    a3 = a2 = 0.0
    for p in me.polygons:
        a3 += p.area
        li = list(p.loop_indices)
        for k in range(1, len(li) - 1):
            u0, u1, u2 = uv[li[0]].uv, uv[li[k]].uv, uv[li[k + 1]].uv
            a2 += abs((u1.x - u0.x) * (u2.y - u0.y) - (u2.x - u0.x) * (u1.y - u0.y)) / 2
    f = math.sqrt(a3 / max(a2, 1e-9)) / tile
    for l in uv:
        l.uv = l.uv * f


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab))))
    return (p - (a + ab * t)).length


def build_armature(name, bones):
    ad = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, ad)
    bpy.context.scene.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for bn, head, tail, parent in bones:
        b = ad.edit_bones.new(bn)
        b.head = head
        b.tail = tail if (tail - head).length > 1e-3 else head + Vector((0, 0, 0.05))
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]; b.use_connect = False
        eb[bn] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def skin(ob, arm, segs):
    """segs: [(bone, a, b)] world segments; inverse-distance^4 weights, top 4, normalised."""
    groups = {}
    for bn, _, _ in segs:
        if bn not in groups:
            groups[bn] = ob.vertex_groups.new(name=bn)
    worst = 0
    for v in ob.data.vertices:
        co = ob.matrix_world @ v.co
        best = {}
        for bn, a, b in segs:
            w = 1.0 / (seg_dist(co, a, b) + 0.03) ** 4
            best[bn] = max(best.get(bn, 0.0), w)
        items = sorted(best.items(), key=lambda t: -t[1])[:4]
        tot = sum(w for _, w in items)
        items = [(bn, w / tot) for bn, w in items if w / tot > 0.02]
        tot = sum(w for _, w in items)
        worst = max(worst, len(items))
        for bn, w in items:
            groups[bn].add([v.index], w / tot, "REPLACE")
    ob.parent = arm
    md = ob.modifiers.new("Armature", "ARMATURE"); md.object = arm
    return worst


def export(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH", "ARMATURE"},
                             apply_unit_scale=True, global_scale=0.01, axis_forward="-Z", axis_up="Y",
                             mesh_smooth_type="FACE", path_mode="STRIP", embed_textures=False,
                             add_leaf_bones=False, bake_anim=False, use_armature_deform_only=True)


def rbx(v):
    """Blender (rig faces +Y) -> Roblox axes (x right, y up, z back), as the FBX axes map them."""
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


def bbox_centre(ob):
    ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return sum(ws, Vector()) / 8


# ---------------------------------------------------------------- wings
def wing(style, side, fit):
    reset()
    sx = -1 if side == "L" else 1        # the rig faces +Y, so the character's right is +X (x stays x in Roblox)
    root = Vector((WING_ROOT_X * sx, WING_ROOT_Y, WING_ROOT_Z))
    W = hqwing.Wing(sx, root, size=1.0, style=style, seed=7 + sx)
    P = W.geom(0.0, 0.0, 0.0, 0.0)
    S = W.skeleton(0.0, 0.0, 0.0)
    cls = MEMBRANE_CLASS[style]
    thick = {"membrane": 0.014, "feathers": 0.008, "coverts": 0.008, "tatters": 0.01}
    mem_keys = {"membrane", "veins", "feathers", "coverts", "tatters", "wisps", "shards"}
    if style in ("wraithveil", "rime"):
        mem_keys.add("rim")
    mem_parts = [(p.v, p.f, thick.get(k, 0.0)) for k, p in P.items() if k in mem_keys]
    frame_parts = [(p.v, p.f, thick.get(k, 0.0)) for k, p in P.items() if k not in mem_keys]
    Name = style.capitalize()
    mem = mesh_from(f"{Name}{side}Membrane", mem_parts)
    frame = mesh_from(f"{Name}{side}Frame", frame_parts)
    world_uvs(mem, TILE[cls]); world_uvs(frame, TILE["bone"])

    R, E, Wr, Dg, body = S["R"], S["E"], S["W"], S["digits"], S["body"]
    bones = [("Root", R, R + Vector((0, 0, 0.15)), None),
             ("Hum", R, E, "Root"), ("Fore", E, Wr, "Hum")]
    segs = [("Root", body[0], body[-1]), ("Hum", R, E), ("Fore", E, Wr)]
    for k, (K, T) in enumerate(Dg):
        bones += [(f"D{k + 1}a", Wr, K, "Fore"), (f"D{k + 1}b", K, T, f"D{k + 1}a")]
        segs += [(f"D{k + 1}a", Wr, K), (f"D{k + 1}b", K, T)]
    arm = build_armature(f"{Name}{side}Wing", bones)
    worst = max(skin(mem, arm, segs), skin(frame, arm, segs))
    fname = f"NHWing_{Name}_{side}.fbx"
    export(os.path.join(OUT, "fbx", fname), [arm, mem, frame])
    attach = Vector((0, WING_ROOT_Y, WING_ROOT_Z))
    fit[fname] = {
        "kind": "wing", "style": Name, "side": side, "attach_from_torso": rbx(attach - TORSO_C),
        "pieces": {o.name: {"centre": rbx(bbox_centre(o) - attach), "tris": tris(o)} for o in (mem, frame)},
        "bones": {bn: rbx(h - attach) for bn, h, _, _ in bones}, "max_influences": worst,
        "tint": {mem.name: "WingPalette", frame.name: "WingFinish"},
        "maps": {mem.name: cls, frame.name: "bone"},
    }
    for o in (mem, frame):
        if tris(o) > TRI_CAP:
            print(f"!! {o.name} has {tris(o)} tris (cap {TRI_CAP})")
    print(f"wing {fname}: " + ", ".join(f"{o.name} {tris(o)}" for o in (mem, frame)) + f"; influences <= {worst}")


# ---------------------------------------------------------------- horns
def horn(kind, fit):
    reset()
    Name = kind.capitalize()
    objs = []
    for part, (v, f) in hqwing.horns(kind, HEAD_C).items():
        nm = {"horn": f"{Name}Horns", "tip": f"{Name}Tip", "halo": f"{Name}Halo"}[part]
        ob = mesh_from(nm, [(v, f, 0.0)], subd=1)
        world_uvs(ob, TILE["horn"])
        objs.append(ob)
    fname = f"NHHorns_{Name}.fbx"
    export(os.path.join(OUT, "fbx", fname), objs)
    fit[fname] = {"kind": "horns", "style": Name, "attach_from_head": [0, 0, 0],
                  "pieces": {o.name: {"centre": rbx(bbox_centre(o) - HEAD_C), "tris": tris(o)} for o in objs},
                  "tint": {o.name: ("HornTip" if o.name.endswith("Tip") else "HornFinish") for o in objs},
                  "maps": {o.name: "horn" for o in objs}}
    print(f"horns {fname}: " + ", ".join(f"{o.name} {tris(o)}" for o in objs))


fit_path = os.path.join(OUT, "forms_fit.json")
fit = json.load(open(fit_path)) if os.path.exists(fit_path) else {}
if ONLY in ("all", "wings"):
    for st in ([ONE] if ONE else list(hqwing.STYLES)):
        for side in ("L", "R"):
            wing(st, side, fit)
if ONLY in ("all", "horns"):
    for k in ([ONE] if ONE else ["ram", "demon", "wendigo", "thorn", "broken", "sovereign", "bull"]):
        horn(k, fit)
json.dump(fit, open(fit_path, "w"), indent=1)
print("wrote", fit_path)
