"""Comparison renders for the feminine R6 body: Standard R6 | current Female torso | new body.
Called from nh_female_body.py with --render. Writes renders/*.png and renders/compare_sheet.png."""
import bpy, bmesh, math, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
REF = "E:/NH-Work/femalebody/ref_48112070.json"   # Roblox's Girl torso (the game's current Female torso)


def srgb(c):
    return tuple(((x / 255) ** 2.2) for x in c) + (1.0,)


def mat(name, rgb=None, image=None, rough=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image)
        tex.interpolation = "Closest"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = srgb(rgb)
    return m


def box(name, sx, sy, sz, bevel=0.035):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sz; v.co.z *= sy      # Roblox (x, y, z) -> Blender (x, z-depth, y-up)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("bev", "BEVEL"); mod.width = bevel; mod.segments = 3
    for p in me.polygons:
        p.use_smooth = True
    return ob


def head(name):
    # classic R6 head: a rounded cylinder about 1.2 studs across
    R, H, r = 0.6, 1.2, 0.26
    prof = []
    for k in range(7):
        a = math.radians(-90 + 90 * k / 6)
        prof.append((R - r + r * math.cos(a), -H / 2 + r + r * math.sin(a)))
    for k in range(7):
        a = math.radians(90 * k / 6)
        prof.append((R - r + r * math.cos(a), H / 2 - r + r * math.sin(a)))
    prof = [(0.0, -H / 2)] + prof + [(0.0, H / 2)]
    seg = 48
    bm = bmesh.new()
    rings = []
    for (rad, h) in prof:
        rings.append([bm.verts.new((rad * math.cos(2 * math.pi * i / seg), rad * math.sin(2 * math.pi * i / seg), h)) for i in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            try:
                bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def ref_torso(name):
    d = json.load(open(REF))
    me = bpy.data.meshes.new(name)
    verts = [(v[0], -v[2], v[1]) for v in d["V"]]
    me.from_pydata(verts, [], [tuple(f) for f in d["F"]])
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = (d["V"][vi][3], 1 - d["V"][vi][4])
    # flip the winding if the normals point inward (Roblox and Blender may disagree)
    me.update()
    out = sum(p.normal.dot(p.center) for p in me.polygons)
    if out < 0:
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def place(ob, x, y, ox):
    ob.location = (ox + x, 0.0, y)


def figure(kind, parts, ox, skin, label):
    objs = []
    h = head(f"{label}_Head"); place(h, 0, 1.5, ox); objs.append(h)
    if kind == "standard":
        t = box(f"{label}_Torso", 2, 2, 1)
    elif kind == "current":
        t = ref_torso(f"{label}_Torso")
    else:
        t = parts["NHFem_Torso"].copy(); t.data = parts["NHFem_Torso"].data.copy(); bpy.context.scene.collection.objects.link(t)
    place(t, 0, 0, ox); objs.append(t)
    for nm, x, y in (("RightArm", 1.5, 0), ("LeftArm", -1.5, 0), ("RightLeg", 0.5, -2), ("LeftLeg", -0.5, -2)):
        if kind == "new":
            src = parts["NHFem_" + nm]
            o = src.copy(); o.data = src.data.copy(); bpy.context.scene.collection.objects.link(o)
        else:
            o = box(f"{label}_{nm}", 1, 2, 1)
        place(o, x, y, ox); objs.append(o)
    for o in objs:
        o.data.materials.clear(); o.data.materials.append(skin)
    return objs


def setup_scene():
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.resolution_x, sc.render.resolution_y = 700, 1000
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    w = bpy.data.worlds.new("W"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.045, 0.045, 0.055, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    for nm, loc, rot, en, sz in (("Key", (3, 6, 6), (math.radians(55), 0, math.radians(150)), 900, 4),
                                  ("Fill", (-5, 4, 2), (math.radians(75), 0, math.radians(-130)), 350, 5),
                                  ("Rim", (0, -6, 5), (math.radians(-55), 0, 0), 700, 4),
                                  ("Back", (0, -6, 2), (math.radians(-80), 0, 0), 200, 6)):
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = en; ld.size = sz
        lo = bpy.data.objects.new(nm, ld); lo.location = loc; lo.rotation_euler = rot
        sc.collection.objects.link(lo)
    cd = bpy.data.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 6.6
    cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    return sc, cam


def shoot(sc, cam, ox, view, path):
    # front: camera on Blender +y (the character's front), side: on +x (character's right), back: on -y
    tgt = (ox, 0, -0.5)
    if view == "front":
        cam.location = (ox, 12, -0.5); cam.rotation_euler = (math.radians(90), 0, math.radians(180))
    elif view == "back":
        cam.location = (ox, -12, -0.5); cam.rotation_euler = (math.radians(90), 0, 0)
    else:
        cam.location = (ox + 12, 0, -0.5); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    # lights follow the view so every shot is lit from the camera side
    for nm in ("Key", "Fill", "Rim", "Back"):
        lo = bpy.data.objects[nm]
        base = {"Key": (3, 6, 6), "Fill": (-5, 4, 2), "Rim": (0, -6, 5), "Back": (0, -6, 2)}[nm]
        x, y, z = base
        if view == "back":
            x, y = -x, -y
        elif view == "side":
            x, y = y, -x
        lo.location = (ox + x, y, z)
        d = (tgt[0] - lo.location.x, tgt[1] - lo.location.y, tgt[2] - lo.location.z)
        lo.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def run(parts, out):
    sc, cam = setup_scene()
    rd = os.path.join(out, "renders")
    skin = mat("Skin", (234, 190, 160))
    atl = mat("Atlas", image=os.path.join(HERE, "atlas_check.png"), rough=0.8)
    for p in parts.values():
        p.hide_render = True
    figs = {"standard": -12, "current": 0, "new": 12, "newatlas": 24, "curatlas": 36}
    objs = {
        "standard": figure("standard", parts, figs["standard"], skin, "Std"),
        "current": figure("current", parts, figs["current"], skin, "Cur"),
        "new": figure("new", parts, figs["new"], skin, "New"),
        "newatlas": figure("new", parts, figs["newatlas"], atl, "NewA"),
        "curatlas": figure("current", parts, figs["curatlas"], atl, "CurA"),
    }
    for o in objs["newatlas"][:1] + objs["curatlas"][:1]:
        o.data.materials.clear(); o.data.materials.append(skin)   # heads stay skin
    for o in objs["curatlas"][2:]:
        o.data.materials.clear(); o.data.materials.append(skin)   # standard limbs have no atlas UVs
    shots = []
    for key in ("standard", "current", "new", "newatlas", "curatlas"):
        for k2, lst in objs.items():          # one figure per shot (side cameras would sit inside a neighbour)
            for o in lst:
                o.hide_render = k2 != key
        for view in ("front", "side", "back"):
            objs[key][2].hide_render = view == "side"   # the near (right) arm would hide the torso profile
            p = os.path.join(rd, f"{key}_{view}.png")
            shoot(sc, cam, figs[key], view, p)
            shots.append(p)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "NHFemaleBody_compare.blend"))
    return shots
