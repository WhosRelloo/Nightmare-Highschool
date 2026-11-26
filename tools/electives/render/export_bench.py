"""Export the Anatomy bench as rigid props: Studio-ready pieces, FBX, PBR bakes and <Prop>_rigid.json.

Called from bench_scene.py in its export mode, after the rest-pose clip check passed (it exits 3 otherwise):

  blender -b --factory-startup -P tools/electives/render/bench_scene.py -- <maps> <repo>/art/props 1 export [Species]

Each source object goes to one piece of one prop by its base name (PIECES). A piece's objects are evaluated
(modifiers, curves), joined at world coordinates, decimated under the MeshPart triangle cap, UV-unwrapped and
baked to color/normal/rough/metal (emission trick for color and metal, so metals keep their colour).
Pieces whose name ends in Glow (Neon) or Glass (Glass) are not baked: stage/textures.lua's rules dress them.

Writes, per prop:
  art/props/fbx/Anat<Prop>.fbx                      plain meshes, no armature (Import as rig OFF)
  art/props/textures/Anat<Prop>_<Piece>_{color,normal,rough,metal}.png
  art/props/anim/Anat<Prop>_rigid.json              bones (head, parent, axis), pieces -> bone, centres, sizes,
                                                    mats, attach (Grip/Tip/Slot<n>/Seam<nn>), all in Blender m
and tools/electives/render/out/layout.json: every prop together (anatomy_layout.py makes the Luau module).
"""
import json
import math
import os
from fnmatch import fnmatch

import bpy
from mathutils import Vector

TRI_CAP = 19000
BIG = 1024
SMALL = 512

# (prop, pattern on the object's base name, piece, bone)
PIECES = [
    ("Frog", "FrogBody", "Body", "Body"), ("Frog", "Rivet", "Body", "Body"), ("Frog", "Hinge", "Body", "Body"),
    ("Frog", "Deck", "Mechanism", "Body"), ("Frog", "DeckScrew", "Mechanism", "Body"), ("Frog", "Brace", "Mechanism", "Body"),
    ("Frog", "Barrel", "Mechanism", "Body"), ("Frog", "Mainspring", "Mechanism", "Body"), ("Frog", "Pipe_Lung", "Mechanism", "Body"),
    ("Frog", "Cradle_Glow", "CradleGlow", "Body"), ("Frog", "Cradle_*", "Mechanism", "Body"),
    ("Frog", "FrogHead", "Head", "Body"), ("Frog", "Eye", "Head", "Body"), ("Frog", "Pupil", "Head", "Body"), ("Frog", "Collar", "Head", "Body"),
    ("Frog", "Leg", "Legs", "Body"), ("Frog", "LegJoint", "Legs", "Body"), ("Frog", "Foot", "Legs", "Body"),
    ("Frog", "Pin", "Legs", "Body"), ("Frog", "PinHead", "Legs", "Body"),
    ("Frog", "BellyPlate", "Plate", "PlateHinge"), ("Frog", "PlateRing", "Plate", "PlateHinge"), ("Frog", "PlateRivet", "Plate", "PlateHinge"),
    ("Frog", "Heart", "HeartPump", "HeartPump"), ("Frog", "HeartBand", "HeartPump", "HeartPump"),
    ("Frog", "HeartLug", "HeartPump", "HeartPump"), ("Frog", "HeartStub", "HeartPump", "HeartPump"),
    ("Frog", "Lung_*", "Lungs", "Lungs"),
    ("Frog", "Gear", "GearGut", "GearGut"), ("Frog", "Gear_Hub", "GearGut", "GearGut"), ("Frog", "Gear_Axle", "GearGut", "GearGut"),
    ("Frog", "FlagCog", "FlagCog", "FlagCog"), ("Frog", "FlagCog_Hub", "FlagCog", "FlagCog"),
    ("Frog", "KeyShaft", "SideKey", "SideKey"), ("Frog", "KeyBow", "SideKey", "SideKey"),
    ("BenchSet", "Desk", "Desk", "Root"), ("BenchSet", "Tray", "Tray", "Root"), ("BenchSet", "Wax", "Wax", "Root"),
    ("BenchSet", "Roll", "Roll", "Root"), ("BenchSet", "Slot", "Roll", "Root"),
    ("BenchSet", "CandleDish", "Candle", "Root"), ("BenchSet", "Candle", "Candle", "Root"), ("BenchSet", "Flame", "FlameGlow", "Root"),
]
TOOLS = {"PinKey": "Key", "Screwdriver": "Driver", "Loupe": "Loupe", "Scalpel": "Scalpel", "Tweezers": "Tweezers"}
# tool-local (unscaled, metres) grip and tip points; tools lie along their local +Y
TOOL_POINTS = {
    "Key": {"Grip": (0, 0.0, 0), "Tip": (0, 0.072, 0)},
    "Driver": {"Grip": (0, 0.04, 0), "Tip": (0, 0.153, 0)},
    "Loupe": {"Grip": (0, 0.025, 0), "Tip": (0, 0.095, 0)},
    "Scalpel": {"Grip": (0, 0.045, 0), "Tip": (0, 0.157, -0.002)},
    "Tweezers": {"Grip": (0, 0.062, 0), "Tip": (0, 0.1182, -0.0025)},
}
SLOT_X = (-0.3, -0.15, 0.0, 0.15, 0.3)
TOOL_ORDER = ("Key", "Driver", "Loupe", "Scalpel", "Tweezers")
# colour and Roblox material for the stand-ins the renderer builds until the meshes are imported
MAT_PROXY = {
    "Brass": ((0.86, 0.62, 0.3), "Metal"), "BrassDark": ((0.5, 0.36, 0.18), "Metal"), "Copper": ((0.8, 0.42, 0.28), "Metal"),
    "Steel": ((0.62, 0.62, 0.62), "Metal"), "SteelBright": ((0.78, 0.78, 0.8), "Metal"), "SteelKnurl": ((0.4, 0.4, 0.41), "DiamondPlate"),
    "Porcelain": ((0.93, 0.9, 0.84), "SmoothPlastic"), "Lacquer": ((0.25, 0.04, 0.04), "SmoothPlastic"),
    "Heart": ((0.6, 0.05, 0.06), "Glass"), "Glow": ((1.0, 0.85, 0.5), "Neon"), "Flame": ((1.0, 0.6, 0.2), "Neon"),
    "Pupil": ((0.02, 0.02, 0.02), "SmoothPlastic"), "LeatherDk": ((0.12, 0.07, 0.05), "Leather"), "Leather": ((0.25, 0.13, 0.08), "Leather"),
    "Rosewood": ((0.3, 0.12, 0.08), "Wood"), "Ebony": ((0.12, 0.09, 0.08), "Wood"), "Desk": ((0.38, 0.24, 0.16), "WoodPlanks"),
    "Iron": ((0.2, 0.19, 0.21), "Metal"), "Wax": ((0.35, 0.06, 0.05), "SmoothPlastic"), "Candle": ((0.85, 0.78, 0.62), "SmoothPlastic"),
    "Chalk": ((0.85, 0.72, 0.45), "Neon"), "Glass": ((0.92, 0.96, 1.0), "Glass"),
}


def base(o):
    return o.name.split(".")[0]


def tool_root(o):
    while o is not None:
        if base(o) in TOOLS and o.type == "EMPTY":
            return o
        o = o.parent
    return None


def assign(F):
    """object -> (prop, piece, bone) for every mesh/curve in the scene"""
    out = {}
    for o in bpy.context.scene.objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        r = tool_root(o)
        if r is not None:
            t = TOOLS[base(r)]
            piece = "LensGlass" if base(o) == "LP_Lens" else "Main"
            out[o] = ("Tool" + t, piece, "Root")
            continue
        b = base(o)
        if b == "Chalk":
            c = o.matrix_world.translation
            k = min(range(5), key=lambda i: abs(SLOT_X[i] - c.x))
            out[o] = ("BenchSet", f"Chalk{k + 1}Glow", "Root")
            continue
        if "__" in b:   # species_lib names: <Piece>__<part>
            pre = b.split("__")[0]
            out[o] = ("Frog", pre, F["bone_of"][pre])
            continue
        hit = None
        for prop, pat, piece, bone in PIECES:
            if b == pat or (("*" in pat) and fnmatch(b, pat)):
                hit = (prop, piece, bone)
                break
        if hit is None:
            print("UNASSIGNED", o.name)
            continue
        out[o] = hit
    return out


def make_piece(name, objs):
    dg = bpy.context.evaluated_depsgraph_get()
    made = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        if len(me.polygons) == 0:
            continue
        n = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(n)
        made.append(n)
    bpy.ops.object.select_all(action="DESELECT")
    for n in made:
        n.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    if len(made) > 1:
        bpy.ops.object.join()
    p = bpy.context.view_layer.objects.active
    p.name = name
    p.data.name = name
    for i, m in enumerate(p.data.materials):   # an object without a material: give it brass, so the bake covers it
        if m is None:
            p.data.materials[i] = bpy.data.materials["Brass"]
    if len(p.data.materials) == 0:
        p.data.materials.append(bpy.data.materials["Brass"])
    tris = sum(len(f.vertices) - 2 for f in p.data.polygons)
    if tris > TRI_CAP:
        d = p.modifiers.new("cap", "DECIMATE")
        d.ratio = TRI_CAP / tris * 0.97
        bpy.ops.object.modifier_apply(modifier=d.name)
        tris = sum(len(f.vertices) - 2 for f in p.data.polygons)
    return p, tris


def bounds(o):
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def dominant_mat(o):
    area = {}
    for f in o.data.polygons:
        m = o.data.materials[f.material_index] if f.material_index < len(o.data.materials) else None
        if m:
            k = m.name.split(".")[0]
            area[k] = area.get(k, 0) + f.area
    return max(area, key=area.get) if area else "Brass"


def _out_node(nt):
    for n in nt.nodes:
        if n.type == "OUTPUT_MATERIAL" and n.is_active_output:
            return n
    return [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]


def bake(p, size, tex_dir, stem):
    bpy.ops.object.select_all(action="DESELECT")
    p.select_set(True)
    bpy.context.view_layer.objects.active = p
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 2
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 6
    files = {}
    for kind in ("color", "rough", "normal", "metal"):
        img = bpy.data.images.new(f"{stem}_{kind}", size, size, alpha=False)
        if kind != "color":
            img.colorspace_settings.name = "Non-Color"
        undo = []
        for m in p.data.materials:
            nt = m.node_tree
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = img
            nt.nodes.active = t
            undo.append((nt, t, None))
            if kind in ("color", "metal"):
                bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
                sock = bsdf.inputs["Base Color" if kind == "color" else "Metallic"]
                em = nt.nodes.new("ShaderNodeEmission")
                if sock.links:
                    nt.links.new(sock.links[0].from_socket, em.inputs["Color"])
                else:
                    v = sock.default_value
                    em.inputs["Color"].default_value = (v[0], v[1], v[2], 1) if kind == "color" else (v, v, v, 1)
                out = _out_node(nt)
                old = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
                nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
                undo[-1] = (nt, t, (em, out, old))
        if kind in ("color", "metal"):
            bpy.ops.object.bake(type="EMIT")
        elif kind == "rough":
            bpy.ops.object.bake(type="ROUGHNESS")
        else:
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        for nt, t, extra in undo:
            if extra:
                em, out, old = extra
                if old is not None:
                    nt.links.new(old, out.inputs["Surface"])
                nt.nodes.remove(em)
            nt.nodes.remove(t)
        path = os.path.join(tex_dir, f"{stem}_{kind}.png")
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        files[kind] = os.path.relpath(path, os.path.dirname(os.path.dirname(tex_dir))).replace("\\", "/")
    return files


def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, apply_unit_scale=True, global_scale=1.0,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP", embed_textures=False,
                             add_leaf_bones=False, bake_anim=False)


def frog_bones(F):
    """bone heads (Blender m) and hinge/turn axes for the frog"""
    bc = F["body_centre"]
    piv = bpy.data.objects["PlatePivot"].matrix_world.translation

    def centre(pattern):
        pts = []
        for o in bpy.context.scene.objects:
            if o.type in ("MESH", "CURVE") and fnmatch(base(o), pattern):
                pts.append(o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8))
        return list(sum(pts, Vector()) / len(pts))
    return {
        "Root": {"head": [0, 0, 0], "parent": None},
        "Body": {"head": list(bc), "parent": "Root"},
        "PlateHinge": {"head": list(piv), "parent": "Body", "axis": [0, -1, 0]},
        "HeartPump": {"head": list(F["heart"]), "parent": "Body"},
        "Lungs": {"head": centre("Lung_Board"), "parent": "Body"},
        "GearGut": {"head": centre("Gear"), "parent": "Body"},
        "FlagCog": {"head": centre("FlagCog"), "parent": "Body"},
        "SideKey": {"head": centre("KeyShaft"), "parent": "Body", "axis": [1, 0, 0]},
    }


def run(F, art_dir, maps):
    art_dir = os.path.abspath(art_dir)
    fbx_dir = os.path.join(art_dir, "fbx")
    tex_dir = os.path.join(art_dir, "textures")
    anim_dir = os.path.join(art_dir, "anim")
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(here, "out"), exist_ok=True)
    species = F.get("species", "Frog")
    who = assign(F)
    groups = {}
    for o, (prop, piece, bone) in who.items():
        if prop == "Frog":
            prop = species
        groups.setdefault(prop, {}).setdefault(piece, {"bone": bone, "objs": []})["objs"].append(o)
    tool_roots = {TOOLS[base(o)]: o for o in bpy.context.scene.objects if o.type == "EMPTY" and base(o) in TOOLS}
    only = os.environ.get("ANAT_ONLY")  # e.g. "Frog" to re-export one prop
    layout = {}
    for prop, pieces in sorted(groups.items()):
        if only and prop not in only.split(","):
            continue
        name = "Anat" + prop
        made, rec = [], {"prop": name, "axes": "Blender (x right, y away from the student, z up), units = Blender m",
                         "pieces": {}, "centres": {}, "sizes": {}, "mats": {}, "tris": {}, "textures": {}, "attach": {}}
        for piece, g in sorted(pieces.items()):
            p, tris = make_piece(f"{name}_{piece}", g["objs"])
            lo, hi = bounds(p)
            rec["pieces"][p.name] = g["bone"]
            rec["centres"][p.name] = list((lo + hi) / 2)
            rec["sizes"][p.name] = list(hi - lo)
            rec["mats"][p.name] = dominant_mat(p)
            rec["tris"][p.name] = tris
            made.append(p)
            print("PIECE", p.name, tris, "tris")
        if prop == species:
            rec["bones"] = F["bone_heads"] if "bone_heads" in F else frog_bones(F)
            rec["attach"].update(F.get("attach", {}))
            pl = bpy.data.objects.get(f"{name}_Plate")
            plate = next(o for o in bpy.context.scene.objects if base(o) in ("BellyPlate", "Plate__dome"))
            plo, phi = bounds(plate)
            c, r = (plo + phi) / 2, (phi - plo) / 2
            for k in range(24):
                a = k * 2 * math.pi / 24
                rec["attach"][f"Seam{k + 1:02d}"] = {"bone": "PlateHinge", "pos": [c.x + r.x * math.cos(a), c.y + r.y * math.sin(a), c.z]}
            del pl
        elif prop.startswith("Tool"):
            t = prop[4:]
            rt = tool_roots[t]
            rec["bones"] = {"Root": {"head": list(rt.matrix_world.translation), "parent": None}}
            for k, v in TOOL_POINTS[t].items():
                rec["attach"][k] = {"bone": "Root", "pos": list(rt.matrix_world @ Vector(v))}
        else:
            rec["bones"] = {"Root": {"head": [0, 0, 0], "parent": None}}
            for i, t in enumerate(TOOL_ORDER):
                rt = tool_roots[t]
                rec["attach"][f"Slot{i + 1}"] = {"bone": "Root", "pos": list(rt.matrix_world.translation), "tool": t}
        for p in made:
            if p.name.endswith("Glow") or p.name.endswith("Glass"):
                continue
            big = max(rec["sizes"][p.name]) > 0.12
            rec["textures"][p.name] = bake(p, BIG if big else SMALL, tex_dir, p.name)
            print("BAKED", p.name)
        path = os.path.join(fbx_dir, f"{name}.fbx")
        export_fbx(made, path)
        print("EXPORT", path)
        with open(os.path.join(anim_dir, f"{name}_rigid.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
        layout[prop] = rec
    lp = os.path.join(here, "out", "layout.json")
    old = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
    old.update(layout)
    with open(lp, "w", encoding="utf-8") as fh:
        json.dump(old, fh, indent=1)
    print("LAYOUT", lp, sorted(old))
