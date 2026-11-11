"""Nightmare Highschool: 3D accessories for the R6 body (Kit A, player accessories; Kit B, the admin regalia).

Headless:
  E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- <Item>[,<Item>...]|batch1|all [--size 2048] [--samples 64]
        [--gpu] [--nobake] [--norender] [--views front34,side,back,front] [--res 900]

Every item is one or more PIECES (one MeshPart each). A piece rides one R6 part (its MOUNT: Head, Torso, RightArm,
LeftArm, RightLeg, LeftLeg) and is modelled in CHARACTER SPACE: studs, the 2 x 2 x 1 torso centred at the origin,
head part centre (0, 0, 1.5), arms at x = +-1.5, legs at (+-0.5, 0, -2). Blender -Y is the character's front, +X the
character's LEFT, +Z up (Roblox part space = (-x, z, y) from the part's centre; the importer maps -Y to the front).

Per item (OUT = E:/NH-Work/acc):
  fbx/NHAcc_<Item>.fbx       every piece (+ an armature per rigged piece), global_scale 0.01 (Roblox reads cm)
  maps/NHAcc_<Item>_{color,normal,roughness,metalness}.png   one 2048 atlas shared by the item's baked pieces
  layout/<Item>.json         per piece: mount, fit (bbox centre in mount space, Roblox axes), size, tris, glow colour,
                             bones (Roblox mount space), body fit (depth scale per body type)
  renders/<Item>_<view>[_f].png   on the R6 mannequin (and the Female body with _f), plus <Item>_solo.png
The R6 heads, torsos and limbs of every body type are read from E:/NH-Work/bodytypes/NHBodyTypes.blend and
E:/NH-Work/femalebody/NHFemaleBody.blend (part-local meshes), for the fit table and the Female renders.

Rigs follow the cape layout so the sway controllers read them the same way: Root (depth 0) > H<n> (depth 1, never
moved) > C<n>_<k> (depth 2+). At most 4 weights a vertex.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(REPO, "art", "props", "source_2k")
FONTS = "C:/Windows/Fonts"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/acc"
SIZE = int(argv[argv.index("--size") + 1]) if "--size" in argv else 2048
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
GPU = "--gpu" in argv
BAKE = "--nobake" not in argv
RENDER = "--norender" not in argv
RES = int(argv[argv.index("--res") + 1]) if "--res" in argv else 900
VIEWS = argv[argv.index("--views") + 1].split(",") if "--views" in argv else ["front34", "front", "side", "back", "close"]
FEMALE_TOO = "--nofemale" not in argv
for d in ("fbx", "maps", "layout", "renders", "blend"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
BODY_BLEND = "E:/NH-Work/bodytypes/NHBodyTypes.blend"
FEM_BLEND = "E:/NH-Work/femalebody/NHFemaleBody.blend"
BODY_IDS = ["standard", "female", "lean", "athletic", "muscular", "stocky", "heavy", "petite", "toned", "curvy", "strong", "plus"]
MOUNT_CENTRE = {"Torso": Vector((0, 0, 0)), "Head": Vector((0, 0, 1.5)), "RightArm": Vector((-1.5, 0, 0)),
                "LeftArm": Vector((1.5, 0, 0)), "RightLeg": Vector((-0.5, 0, -2)), "LeftLeg": Vector((0.5, 0, -2))}


def to_rbx(v):
    return [-v.x, v.z, v.y]


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


# ================================================================== scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    if GPU:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type == kind]
            if gpus:
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                break
    sc.cycles.samples = SAMPLES
    global PARTS, PIECE, PIECES, _img_cache
    PARTS, PIECE, PIECES, _img_cache = [], None, {}, {}
    _bodies.clear(); _bvh_cache.clear(); _head_cache.clear()
    return sc


# ================================================================== materials
_img_cache = {}


def _img(name):
    if name not in _img_cache:
        im = bpy.data.images.load(os.path.join(SRC, name))
        if not name.endswith("_color.png"):
            im.colorspace_settings.name = "Non-Color"
        _img_cache[name] = im
    return _img_cache[name]


class NT:
    """small node-tree builder"""

    def __init__(self, m):
        self.nt = m.node_tree
        self.L = self.nt.links.new

    def node(self, kind, **kw):
        n = self.nt.nodes.new(kind)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def math(self, op, a, b=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.L(v, n.inputs[i])
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        for sock, v in ((n.inputs["Factor"], fac), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v[:3], 1) if len(v) == 3 else v
            else:
                self.L(v, sock)
        return n.outputs[2]

    def coord(self, scale, space="Object"):
        tc = self.node("ShaderNodeTexCoord")
        mp = self.node("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
        self.L(tc.outputs[space], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def tex(self, set_name, kind, scale):
        t = self.node("ShaderNodeTexImage", projection="BOX", projection_blend=0.25)
        t.image = _img(f"{set_name}_{kind}.png")
        self.L(self.coord(scale), t.inputs["Vector"])
        return t


def _weather(T, bs, col, rough, metal, normal, wear, wear_metal, dirt, edge_r=0.012):
    """bake-time weathering (the props' recipe, scaled for small accessories): rubbed edges, crevice dirt, rounded edges"""
    bev = T.node("ShaderNodeBevel", samples=8); bev.inputs["Radius"].default_value = edge_r * 1.6
    geo = T.node("ShaderNodeNewGeometry")
    dot = T.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
    T.L(bev.outputs["Normal"], dot.inputs[0]); T.L(geo.outputs["Normal"], dot.inputs[1])
    edge = T.math("MULTIPLY", T.math("SUBTRACT", 1.0, dot.outputs["Value"]), 22.0, clamp=True)
    ao = T.node("ShaderNodeAmbientOcclusion", samples=12, only_local=True); ao.inputs["Distance"].default_value = 0.06
    crev = T.math("MULTIPLY", T.math("SUBTRACT", 1.0, ao.outputs["AO"]), dirt, clamp=True)
    ew = T.math("MULTIPLY", edge, wear, clamp=True)
    c1 = T.mix(crev, col, (0.36, 0.32, 0.29), "MULTIPLY")
    c2 = T.mix(ew, c1, (0.62, 0.58, 0.52) if wear_metal else (0.30, 0.26, 0.22), "MIX" if wear_metal else "SCREEN")
    T.L(c2, bs.inputs["Base Color"])
    r = T.math("ADD", rough, T.math("MULTIPLY", crev, 0.22))
    r = T.math("SUBTRACT", r, T.math("MULTIPLY", ew, 0.28), clamp=True)
    T.L(r, bs.inputs["Roughness"])
    T.L(T.math("MAXIMUM", metal, ew) if wear_metal else metal, bs.inputs["Metallic"])
    bn = T.node("ShaderNodeBevel", samples=8); bn.inputs["Radius"].default_value = edge_r
    if normal is not None:
        T.L(normal, bn.inputs["Normal"])
    T.L(bn.outputs["Normal"], bs.inputs["Normal"])


def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    for n in list(m.node_tree.nodes):
        m.node_tree.nodes.remove(n)
    T = NT(m)
    out = T.node("ShaderNodeOutputMaterial")
    bs = T.node("ShaderNodeBsdfPrincipled")
    T.L(bs.outputs["BSDF"], out.inputs["Surface"])
    return m, T, bs


def _val(T, v):
    n = T.node("ShaderNodeValue"); n.outputs[0].default_value = v
    return n.outputs[0]


def _rgb(T, c):
    n = T.node("ShaderNodeRGB"); n.outputs[0].default_value = (*c, 1)
    return n.outputs[0]


def mat_set(name, set_name, tint=(1, 1, 1), scale=1.0, rough=None, metal=None, normal=0.7, rough_add=0.0, rough_mul=1.0,
            wear=0.35, wear_metal=False, dirt=0.6, edge_r=0.012):
    """a material from one of the props' 2048 seamless PBR sets, box-projected in object space, tinted"""
    m, T, bs = _base(name)
    c = T.tex(set_name, "color", scale)
    col = T.mix(1.0, c.outputs["Color"], tint, "MULTIPLY")
    n = T.tex(set_name, "normal", scale)
    nm = T.node("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = normal
    T.L(n.outputs["Color"], nm.inputs["Color"])
    if rough is None:
        r = T.tex(set_name, "rough", scale)
        rgh = T.math("MULTIPLY_ADD", r.outputs["Color"], rough_mul)
        rgh.node.inputs[2].default_value = rough_add
    else:
        rgh = _val(T, rough)
    if metal is None:
        mm = T.tex(set_name, "metal", scale)
        sep = T.node("ShaderNodeSeparateColor"); T.L(mm.outputs["Color"], sep.inputs["Color"])
        mtl = sep.outputs[0]
    else:
        mtl = _val(T, metal)
    _weather(T, bs, col, rgh, mtl, nm.outputs["Normal"], wear, wear_metal, dirt, edge_r)
    return m


def mat_flat(name, rgb, rough=0.5, metal=0.0, noise=40.0, bump=0.05, wear=0.3, wear_metal=False, dirt=0.5,
             vary=0.06, edge_r=0.010, sheen=0.0, coat=0.0):
    """a plain material with a fine surface noise and colour variation (enamel, porcelain, bone, silk, paint)"""
    m, T, bs = _base(name)
    v = T.coord(noise)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    T.L(v, nz.inputs["Vector"])
    col = T.mix(vary, _rgb(T, rgb), nz.outputs["Color"], "OVERLAY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
    T.L(nz.outputs["Fac"], bp.inputs["Height"])
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.12))
    if sheen:
        bs.inputs["Sheen Weight"].default_value = sheen
    if coat:
        bs.inputs["Coat Weight"].default_value = coat
    _weather(T, bs, col, r, _val(T, metal), bp.outputs["Normal"], wear, wear_metal, dirt, edge_r)
    return m


def mat_metal(name, rgb, rough=0.32, scratch=0.5, wear=0.45, dirt=0.75, tarnish=(0.18, 0.15, 0.10)):
    """polished metal (brass, gold, silver, blackened steel): brushed micro-scratches, tarnish in the crevices"""
    m, T, bs = _base(name)
    v = T.coord((60.0, 60.0, 600.0))
    wv = T.node("ShaderNodeTexNoise"); wv.inputs["Scale"].default_value = 1.0; wv.inputs["Detail"].default_value = 3
    T.L(v, wv.inputs["Vector"])
    v2 = T.coord(30.0)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    T.L(v2, nz.inputs["Vector"])
    tarn = T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.45), 2.2, clamp=True)
    col = T.mix(T.math("MULTIPLY", tarn, 0.35), _rgb(T, rgb), tarnish, "MIX")
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", wv.outputs["Fac"], 0.5), 0.25 * scratch))
    r = T.math("ADD", r, T.math("MULTIPLY", tarn, 0.15))
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.04 * scratch; bp.inputs["Distance"].default_value = 0.005
    T.L(wv.outputs["Fac"], bp.inputs["Height"])
    _weather(T, bs, col, r, _val(T, 1.0), bp.outputs["Normal"], wear, True, dirt, 0.008)
    return m


def mat_cloth(name, rgb, weave=220.0, rough=0.82, sheen=0.35, bump=0.12, twill=True, vary=0.08, wear=0.15, dirt=0.45,
              stripe=None):
    """woven cloth: a twill or plain weave as bump and colour, fibre noise; stripe=(rgb, period, width, angle_deg)
    adds woven stripes (a school tie's diagonal bars)"""
    m, T, bs = _base(name)
    tc = T.node("ShaderNodeTexCoord")
    mp = T.node("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (weave, weave, weave)
    if twill:
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
    T.L(tc.outputs["Object"], mp.inputs["Vector"])
    wa = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wa.inputs["Scale"].default_value = 1.0; wa.inputs["Distortion"].default_value = 0.6; wa.inputs["Detail"].default_value = 2
    T.L(mp.outputs["Vector"], wa.inputs["Vector"])
    wb = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
    wb.inputs["Scale"].default_value = 1.0; wb.inputs["Distortion"].default_value = 0.6
    T.L(mp.outputs["Vector"], wb.inputs["Vector"])
    w = T.math("MAXIMUM", wa.outputs["Fac"], T.math("MULTIPLY", wb.outputs["Fac"], 0.6))
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 10
    T.L(T.coord(25.0), nz.inputs["Vector"])
    base = _rgb(T, rgb)
    if stripe:
        s_rgb, period, width, ang = stripe
        mp2 = T.node("ShaderNodeMapping")
        mp2.inputs["Rotation"].default_value = (0, math.radians(ang), 0)
        T.L(tc.outputs["Object"], mp2.inputs["Vector"])
        sep = T.node("ShaderNodeSeparateXYZ"); T.L(mp2.outputs["Vector"], sep.inputs["Vector"])
        fr = T.math("FRACT", T.math("DIVIDE", sep.outputs["X"], period))
        band = T.math("LESS_THAN", fr, width / period)
        base = T.mix(band, base, s_rgb, "MIX")
    col = T.mix(vary, base, nz.outputs["Color"], "OVERLAY")
    col = T.mix(T.math("MULTIPLY", w, 0.18), col, (0, 0, 0), "MULTIPLY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.004
    T.L(w, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = sheen
    bs.inputs["Sheen Roughness"].default_value = 0.4
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.1))
    _weather(T, bs, col, r, _val(T, 0.0), bp.outputs["Normal"], wear, False, dirt, 0.006)
    return m


def mat_velvet(name, rgb, rough=0.7, sheen=1.0):
    """velvet: crushed pile (large soft noise in colour and normal), strong sheen"""
    m, T, bs = _base(name)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 4
    nz.inputs["Distortion"].default_value = 1.4
    T.L(T.coord(5.0), nz.inputs["Vector"])
    fine = T.node("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 1.0; fine.inputs["Detail"].default_value = 12
    T.L(T.coord(300.0), fine.inputs["Vector"])
    col = T.mix(T.math("MULTIPLY", nz.outputs["Fac"], 0.55), _rgb(T, rgb), tuple(c * 1.9 for c in rgb), "MIX")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08
    T.L(T.math("ADD", nz.outputs["Fac"], T.math("MULTIPLY", fine.outputs["Fac"], 0.3)), bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = sheen
    bs.inputs["Sheen Tint"].default_value = (*[min(1, c * 3 + 0.2) for c in rgb], 1)
    _weather(T, bs, col, _val(T, rough), _val(T, 0.0), bp.outputs["Normal"], 0.1, False, 0.4, 0.006)
    return m


def mat_leather(name, tint, scale=2.2, rough_add=0.0, wear=0.5):
    return mat_set(name, "NH_Leather", tint=tint, scale=scale, normal=0.55, rough_add=rough_add, wear=wear, dirt=0.6,
                   edge_r=0.010)


def mat_glow(name, rgb, strength=6.0):
    """a Glow piece's preview material (Neon in Roblox); never baked"""
    m, T, bs = _base(name)
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Emission Color"].default_value = (*rgb, 1)
    bs.inputs["Emission Strength"].default_value = strength
    m["nh_glow"] = list(rgb)
    return m


def mat_engraved(name, base_mat_fn, text_img=None):
    return base_mat_fn(name)


def palette():
    """shared accessory materials (the Institution look: brass, black iron, crimson #600E1A, bone, ink, wax)"""
    C = (0.38, 0.055, 0.10)  # #600E1A in linear-ish terms, a touch lifted for cloth
    return {
        "brass": mat_metal("Brass", (0.78, 0.56, 0.26), rough=0.30),
        "brassold": mat_metal("BrassOld", (0.62, 0.43, 0.20), rough=0.42, tarnish=(0.12, 0.10, 0.06)),
        "gold": mat_metal("Gold", (0.95, 0.70, 0.30), rough=0.22, scratch=0.3, wear=0.3),
        "silver": mat_metal("Silver", (0.86, 0.86, 0.88), rough=0.24, tarnish=(0.20, 0.19, 0.20)),
        "steel": mat_metal("SteelBlack", (0.10, 0.10, 0.11), rough=0.38, tarnish=(0.05, 0.045, 0.04), wear=0.6),
        "iron": mat_set("Iron", "NH_Iron", tint=(0.12, 0.115, 0.125), scale=1.6, wear=0.5, wear_metal=True),
        "crimson_enamel": mat_flat("CrimsonEnamel", (0.30, 0.025, 0.05), rough=0.12, coat=0.6, noise=80, bump=0.01, vary=0.04, wear=0.1),
        "black_enamel": mat_flat("BlackEnamel", (0.015, 0.014, 0.018), rough=0.12, coat=0.6, noise=80, bump=0.01, vary=0.03, wear=0.1),
        "bone": mat_flat("Bone", (0.78, 0.72, 0.60), rough=0.55, noise=60, bump=0.12, vary=0.12, wear=0.25, dirt=0.9),
        "porcelain": mat_flat("Porcelain", (0.90, 0.89, 0.86), rough=0.14, coat=0.5, noise=40, bump=0.01, vary=0.03, wear=0.05, dirt=0.6),
        "wax": mat_flat("Wax", (0.85, 0.80, 0.68), rough=0.45, noise=30, bump=0.06, vary=0.06, wear=0.0),
        "crimson_silk": mat_cloth("CrimsonSilk", (0.19, 0.018, 0.035), weave=420, rough=0.42, sheen=0.25, bump=0.05, twill=False),
        "black_wool": mat_cloth("BlackWool", (0.028, 0.026, 0.032), weave=260, rough=0.88, sheen=0.4, bump=0.14),
        "white_linen": mat_cloth("WhiteLinen", (0.80, 0.78, 0.73), weave=300, rough=0.85, sheen=0.25, bump=0.08, twill=False),
        "black_velvet": mat_velvet("BlackVelvet", (0.022, 0.018, 0.026)),
        "crimson_velvet": mat_velvet("CrimsonVelvet", (0.22, 0.02, 0.04)),
        "leather_oxblood": mat_leather("LeatherOxblood", (0.30, 0.07, 0.06)),
        "leather_black": mat_leather("LeatherBlack", (0.07, 0.065, 0.07)),
        "leather_brown": mat_leather("LeatherBrown", (0.30, 0.16, 0.08)),
        "paper": mat_set("Paper", "NH_Paper", tint=(0.95, 0.90, 0.78), scale=3.0, wear=0.2, dirt=0.6),
        "glass": mat_flat("GlassDark", (0.05, 0.05, 0.07), rough=0.05, noise=10, bump=0.0, vary=0.0, wear=0.0),
    }


# ================================================================== geometry
PARTS = []
PIECE = None
PIECES = {}   # name -> dict(mount, kind, glow, rig)


def piece(name, mount="Torso", kind="Main", glow=None, rig=None, sway=None, alpha=None, uv=None, keepout=None, lock=None):
    """start a piece: parts built after this join into one MeshPart `name` riding `mount`.
    kind Main (in the baked atlas) | Glow (Neon, colour `glow`) | Alpha (its own RGBA texture `alpha` = a PNG path,
    UVs from `uv(obj)`; SurfaceAppearance AlphaMode Transparency in Roblox: veils, lace).
    rig = a function(piece_obj) -> (armature, bones); sway = the AccessorySway profile (Flutter, Loops, Pendulum,
    BackHang, Tails)"""
    global PIECE
    PIECE = name
    PIECES[name] = dict(mount=mount, kind=kind, glow=glow, rig=rig, sway=sway, alpha=alpha, uv=uv, keepout=keepout, lock=lock)
    return name


def _finish(ob, mat, bevel=0.0, segments=2, smooth_angle=None):
    if mat is not None:
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL"); b.width = bevel; b.segments = segments
        b.limit_method = "ANGLE"; b.harden_normals = False
    ob["nh_piece"] = PIECE
    if smooth_angle is not None:
        ob["nh_smooth"] = smooth_angle
    PARTS.append(ob)
    return ob


def _new_obj(name, me):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mesh_from(name, verts, faces, mat, bevel=0.0, smooth_all=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth_all
    return _finish(_new_obj(name, me), mat, bevel)


def box(name, size, loc, mat, bevel=0.01, rot=(0, 0, 0), segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _finish(ob, mat, bevel, segments)


def cyl(name, r, depth, loc, mat, rot=(0, 0, 0), verts=24, bevel=0.006, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=verts)
    ob = bpy.context.object; ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return _finish(ob, mat, bevel)


def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=16, rings=10, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=rings, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    for p in ob.data.polygons:
        p.use_smooth = True
    return _finish(ob, mat)


def torus(name, R, r, loc, mat, rot=(0, 0, 0), major=24, minor=8, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=major, minor_segments=minor)
    ob = bpy.context.object; ob.name = name; ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    for p in ob.data.polygons:
        p.use_smooth = True
    return _finish(ob, mat)


def tube(name, points, radius, mat, res=6, closed=False, taper=None, square=False, twist=0.0, poly=False):
    """a swept tube along points (a poly line, Catmull-smoothed by the curve). square=True gives a 4-sided bar with
    outward normals (the fixed profile; never the props' inverted one)"""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY" if (square or poly) else "NURBS")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1)
    if not (square or poly):
        sp.order_u = min(4, len(points)); sp.use_endpoint_u = True
    sp.use_cyclic_u = closed
    if square:
        prof = bpy.data.curves.new(name + "_p", "CURVE"); prof.dimensions = "2D"
        ps = prof.splines.new("POLY"); ps.points.add(3)
        for p, co in zip(ps.points, [(-1, -1), (1, -1), (1, 1), (-1, 1)]):   # counter-clockwise: outward normals
            p.co = (co[0] * radius, co[1] * radius, 0, 1)
        ps.use_cyclic_u = True
        po = _new_obj(name + "_prof", prof)
        cu.bevel_mode = "OBJECT"; cu.bevel_object = po
    else:
        cu.bevel_depth = radius; cu.bevel_resolution = max(1, res // 4 - 1)
    cu.resolution_u = res
    cu.use_fill_caps = True
    ob = _new_obj(name, cu)
    if taper is not None:
        for i, p in enumerate(sp.points):
            p.radius = taper(i / max(1, len(points) - 1))
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object
    if square:
        bpy.data.objects.remove(bpy.data.objects[name + "_prof"])
    for p in ob.data.polygons:
        p.use_smooth = not square
    return _finish(ob, mat)


def lathe(name, profile, loc, mat, seg=32, axis="Z", rot=(0, 0, 0), scale=(1, 1, 1), smooth_all=True):
    """revolve (radius, height) profile points about the axis"""
    verts, faces = [], []
    n = len(profile)
    for s in range(seg):
        a = 2 * math.pi * s / seg
        for r, h in profile:
            verts.append(Vector((r * math.cos(a) * scale[0], r * math.sin(a) * scale[1], h * scale[2])))
    for s in range(seg):
        s2 = (s + 1) % seg
        for k in range(n - 1):
            faces.append([s * n + k, s2 * n + k, s2 * n + k + 1, s * n + k + 1])
    R = Euler(rot).to_matrix()
    verts = [R @ v + Vector(loc) for v in verts]
    ob = mesh_from(name, verts, faces, mat, smooth_all=smooth_all)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def extrude_poly(name, pts2d, depth, mat, frame=None, bevel=0.004, segments=2, holes=()):
    """a flat outline (x, z) extruded along -Y by depth (front face toward -Y), placed by `frame` (a Matrix)"""
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in pts2d]
    f = bm.faces.new(vs)
    bmesh.ops.reverse_faces(bm, faces=[f]) if f.normal.y > 0 else None
    for h in holes:
        hv = [bm.verts.new((x, 0, z)) for x, z in h]
        for i in range(len(hv)):
            bm.edges.new((hv[i], hv[(i + 1) % len(hv)]))
    if holes:
        bmesh.ops.triangle_fill(bm, use_beauty=True, edges=bm.edges)
        for fc in list(bm.faces):
            c = fc.calc_center_median()
            if any(_inside((c.x, c.z), h) for h in holes):
                bm.faces.remove(fc)
    faces = list(bm.faces)
    r = bmesh.ops.extrude_face_region(bm, geom=faces)
    nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, -depth, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = _new_obj(name, me)
    if frame is not None:
        ob.matrix_world = frame
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for p in ob.data.polygons:
        p.use_smooth = False
    return _finish(ob, mat, bevel, segments)


def _inside(p, poly):
    x, y = p; c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


def circle_pts(cx, cz, r, n=24, a0=0.0, a1=2 * math.pi, sx=1.0):
    return [(cx + r * math.cos(lerp(a0, a1, i / n)) * sx, cz + r * math.sin(lerp(a0, a1, i / n))) for i in range(n)]


def text_mesh(name, s, size, mat, frame, font="georgiab.ttf", depth=0.006, align="CENTER", spacing=1.0, bevel=0.0):
    """raised text: a font curve extruded (front toward -Y once placed by frame: the text lies in X/Z)"""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = s
    cu.font = bpy.data.fonts.load(os.path.join(FONTS, font), check_existing=True)
    cu.size = size; cu.extrude = depth / 2; cu.bevel_depth = bevel; cu.bevel_resolution = 0; cu.resolution_u = 3
    cu.align_x = align; cu.align_y = "CENTER"; cu.space_character = spacing
    ob = _new_obj(name, cu)
    ob.rotation_euler = (math.radians(90), 0, 0)   # lie in X/Z, facing -Y
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object
    ob.matrix_world = frame @ ob.matrix_world
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons:
        p.use_smooth = False
    return _finish(ob, mat)


def surface(name, G, thick, mat, smooth_all=True, caps=True):
    """a cloth / strap panel from a mid-surface grid G[i][j] (i across, j along), given real thickness (both shells +
    rims). thick may be a function (i/nu, j/nv) -> thickness."""
    nu, nv = len(G) - 1, len(G[0]) - 1
    N = []
    for i in range(nu + 1):
        col = []
        for j in range(nv + 1):
            du = G[min(i + 1, nu)][j] - G[max(i - 1, 0)][j]
            dv = G[i][min(j + 1, nv)] - G[i][max(j - 1, 0)]
            n = du.cross(dv)
            col.append(n.normalized() if n.length > 1e-9 else Vector((0, -1, 0)))
        N.append(col)
    verts, faces = [], []
    idx = {}
    for s, sign in (("o", 1), ("i", -1)):
        for i in range(nu + 1):
            for j in range(nv + 1):
                t = thick(i / nu, j / nv) if callable(thick) else thick
                idx[(s, i, j)] = len(verts)
                verts.append(G[i][j] + N[i][j] * (sign * t / 2))
    for i in range(nu):
        for j in range(nv):
            faces.append([idx[("o", i, j)], idx[("o", i + 1, j)], idx[("o", i + 1, j + 1)], idx[("o", i, j + 1)]])
            faces.append([idx[("i", i, j)], idx[("i", i, j + 1)], idx[("i", i + 1, j + 1)], idx[("i", i + 1, j)]])
    if caps:
        for i in range(nu):
            for j in (0, nv):
                a, b = (idx[("o", i, j)], idx[("o", i + 1, j)]), (idx[("i", i, j)], idx[("i", i + 1, j)])
                faces.append([a[0], b[0], b[1], a[1]] if j == 0 else [a[0], a[1], b[1], b[0]])
        for j in range(nv):
            for i in (0, nu):
                a, b = (idx[("o", i, j)], idx[("o", i, j + 1)]), (idx[("i", i, j)], idx[("i", i, j + 1)])
                faces.append([a[0], a[1], b[1], b[0]] if i == 0 else [a[0], b[0], b[1], a[1]])
    ob = mesh_from(name, verts, faces, mat, smooth_all=smooth_all)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def chain(name, points, link_r, mat, wire=None, twist=True):
    """a chain of oval links along a poly line; alternate links turn 90 degrees"""
    wire = wire or link_r * 0.28
    pts = [Vector(p) for p in points]
    total = sum((b - a).length for a, b in zip(pts, pts[1:]))
    step = link_r * 1.55
    n = max(2, int(total / step))
    obs = []

    def at(d):
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if d <= L:
                return a + (b - a) * (d / L), (b - a).normalized()
            d -= L
        return pts[-1], (pts[-1] - pts[-2]).normalized()
    for k in range(n):
        p, t = at(k * total / (n - 1) if n > 1 else 0)
        q = t.to_track_quat("Z", "Y")
        bpy.ops.mesh.primitive_torus_add(major_radius=link_r * 0.62, minor_radius=wire, major_segments=10, minor_segments=5)
        ob = bpy.context.object
        ob.scale = (0.62, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        rot = q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(90), 4, "Y") @ \
            Matrix.Rotation(math.radians(90 if (twist and k % 2) else 0), 4, "X")
        ob.matrix_world = Matrix.Translation(p) @ rot
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obs.append(ob)
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    return _finish(ob, mat)


def mirror_x(ob, name=None):
    """a mirrored copy across the character's centre plane (x -> -x)"""
    me = ob.data.copy()
    o2 = _new_obj(name or ob.name + "_m", me)
    o2.matrix_world = ob.matrix_world.copy()
    for md in ob.modifiers:
        n = o2.modifiers.new(md.name, md.type)
        for attr in ("width", "segments", "limit_method"):
            if hasattr(md, attr):
                setattr(n, attr, getattr(md, attr))
    o2.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    o2.data.flip_normals()
    o2["nh_piece"] = ob["nh_piece"]
    PARTS.append(o2)
    return o2


# ================================================================== bodies (fit table, renders)
_bodies = {}


def load_bodies():
    """part-local meshes of every body type: {body_id: {part: obj}}; standard = plain R6 boxes"""
    if _bodies:
        return _bodies
    names = []
    with bpy.data.libraries.load(BODY_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("NHBody_")]
        names += dst.objects
    with bpy.data.libraries.load(FEM_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("NHFem_")]
    col = bpy.data.collections.new("NHBodies")
    bpy.context.scene.collection.children.link(col)
    for ob in list(bpy.data.objects):
        nm = ob.name
        if nm.startswith("NHBody_"):
            _, bid, part = nm.split("_", 2)
        elif nm.startswith("NHFem_"):
            bid, part = "female", nm.split("_", 1)[1]
        else:
            continue
        col.objects.link(ob)
        ob.hide_render = True; ob.hide_viewport = True
        _bodies.setdefault(bid, {})[part] = ob
    return _bodies


def _bvh(ob):
    me = ob.data
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])


def body_depth(bid, part, x, z, side):
    """the body's surface depth (|y|) in part-local space at (x, z) on the front (side -1) or back (+1)"""
    if bid == "standard":
        return 0.5
    ob = load_bodies().get(bid, {}).get(part)
    if ob is None:
        return 0.5
    key = (bid, part)
    if key not in _bvh_cache:
        _bvh_cache[key] = _bvh(ob)
    t = _bvh_cache[key]
    o = Vector((x, side * 3.0, z))
    hit = t.ray_cast(o, Vector((0, -side, 0)), 6.0)
    if hit[0] is None:
        return None
    return abs(hit[0].y)


_bvh_cache = {}


def fit_table(obj, mount):
    """per body type, the depth scale (about the part's centre plane) that keeps this piece just clear of that body:
    s = max over the piece's contact vertices of (D_body + clearance) / |y|, clearance = min(the standard clearance,
    0.02). Head pieces return {} (every body shares the head)."""
    if mount == "Head":
        return {}
    c = MOUNT_CENTRE[mount]
    hw = 1.0 if mount == "Torso" else 0.5
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co - c for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    contact = []
    for p in pts:
        if abs(p.x) > hw * 0.98 or abs(p.z) > 0.98 or abs(p.y) < 0.05:
            continue
        side = -1 if p.y < 0 else 1
        clear = abs(p.y) - 0.5
        if clear < 0.12:
            contact.append((p, side, max(0.004, min(clear, 0.02))))
    if not contact:
        return {}
    random.seed(7)
    if len(contact) > 400:
        contact = random.sample(contact, 400)
    # the head (shared by every body): pieces near it may not be pulled into it by a smaller depth scale
    head_pts = [p for p in pts if p.z + c.z > 0.82 and abs(p.y) > 0.05] if mount == "Torso" else []
    hbvh = _head_bvh() if head_pts else None

    def head_need(s):
        for p in head_pts:
            q = Vector((p.x, p.y * s, p.z)) + c
            hit = hbvh.find_nearest(q, 0.3)
            if hit[0] is not None and (q - hit[0]).dot(hit[1]) < 0.004:
                return False
        return True
    out = {}
    for bid in BODY_IDS:
        if bid == "standard":
            continue
        s_need = 0.0
        for p, side, cl in contact:
            d = body_depth(bid, mount, p.x, p.z, side)
            if d is None:
                continue
            s_need = max(s_need, (d + cl) / abs(p.y))
        sv = min(1.45, max(0.8, s_need)) if s_need > 0 else 1.0
        while head_pts and sv < 1.45 and not head_need(sv):
            sv += 0.01
        out[bid] = round(sv, 3)
    return out


_head_cache = []


def _head_bvh():
    if not _head_cache:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.2, location=(0, 0, 1.5), vertices=40)
        hd = bpy.context.object
        md = hd.modifiers.new("b", "BEVEL"); md.width = 0.25; md.segments = 5
        dg = bpy.context.evaluated_depsgraph_get()
        me = hd.evaluated_get(dg).to_mesh()
        t = BVHTree.FromPolygons([v.co + hd.location for v in me.vertices], [list(p.vertices) for p in me.polygons])
        hd.evaluated_get(dg).to_mesh_clear()
        bpy.data.objects.remove(hd)
        _head_cache.append(t)
    return _head_cache[0]


# ================================================================== finish: join, bake, rig, export
def join_pieces():
    groups = {}
    for ob in PARTS:
        groups.setdefault(ob["nh_piece"], []).append(ob)
    out = {}
    for name, parts in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for ob in parts:
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            for md in list(ob.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=md.name)
                except RuntimeError:
                    ob.modifiers.remove(md)
        for ob in parts:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        if len(parts) > 1:
            bpy.ops.object.join()
        ob = bpy.context.active_object
        ob.name = name; ob.data.name = name
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(38))
        out[name] = ob
    return out


def bake_uv(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        me = ob.data
        for uv in list(me.uv_layers):
            me.uv_layers.remove(uv)
        uv = me.uv_layers.new(name="Bake")
        me.uv_layers.active = uv
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58), island_margin=0.004, area_weight=0.6)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=8 / SIZE, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_all(objs, key):
    sc = bpy.context.scene
    imgs = {}
    for kind, cs in (("color", "sRGB"), ("ao", "Non-Color"), ("normal", "Non-Color"), ("roughness", "Non-Color"),
                     ("metalness", "Non-Color"), ("emissive", "Non-Color")):
        im = bpy.data.images.new(f"{key}_{kind}", SIZE, SIZE, alpha=False, float_buffer=False)
        im.colorspace_settings.name = cs
        imgs[kind] = im
    mats = []
    for o in objs:
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
    targets = {}
    for m in mats:
        t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.name = "BakeTarget"
        targets[m.name] = t

    def set_target(kind):
        for m in mats:
            t = targets[m.name]; t.image = imgs[kind]
            for n in m.node_tree.nodes:
                n.select = False
            t.select = True; m.node_tree.nodes.active = t
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bk = sc.render.bake
    bk.margin = 16; bk.use_selected_to_active = False
    half = max(16, SAMPLES // 2)

    def bake_input(sock, kind):
        sc.cycles.samples = half
        saved = []
        for m in mats:
            nt = m.node_tree
            bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            em = nt.nodes.new("ShaderNodeEmission")
            src = bs.inputs[sock]
            if src.is_linked:
                nt.links.new(src.links[0].from_socket, em.inputs["Color"])
            else:
                v = src.default_value
                em.inputs["Color"].default_value = (v[0], v[1], v[2], 1) if hasattr(v, "__len__") else (v, v, v, 1)
            old = out.inputs["Surface"].links[0].from_socket
            nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
            saved.append((nt, out, old, em))
        set_target(kind)
        bpy.ops.object.bake(type="EMIT")
        for nt, out, old, em in saved:
            nt.links.new(old, out.inputs["Surface"]); nt.nodes.remove(em)
    bake_input("Base Color", "color")
    sc.cycles.samples = half
    set_target("roughness"); bpy.ops.object.bake(type="ROUGHNESS")
    set_target("normal"); bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    sc.world = sc.world or bpy.data.worlds.new("BakeW")
    sc.world.light_settings.distance = 0.12
    sc.cycles.samples = SAMPLES
    set_target("ao"); bpy.ops.object.bake(type="AO")
    bake_input("Metallic", "metalness")
    glowing = [m for m in mats if "nh_glow" in m.keys()]
    if glowing:
        # emissive mask: white on glow materials (their Emission Strength > 0), black elsewhere
        sc.cycles.samples = half
        saved = []
        for m in mats:
            nt = m.node_tree
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (1, 1, 1, 1) if "nh_glow" in m.keys() else (0, 0, 0, 1)
            old = out.inputs["Surface"].links[0].from_socket
            nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
            saved.append((nt, out, old, em))
        set_target("emissive"); bpy.ops.object.bake(type="EMIT")
        for nt, out, old, em in saved:
            nt.links.new(old, out.inputs["Surface"]); nt.nodes.remove(em)
    import numpy as np
    c = np.array(imgs["color"].pixels[:], dtype=np.float32).reshape(-1, 4)
    a = np.array(imgs["ao"].pixels[:], dtype=np.float32).reshape(-1, 4)
    k = (0.42 + 0.58 * a[:, :1])
    if glowing:   # no AO darkening on glowing pixels
        e = np.array(imgs["emissive"].pixels[:], dtype=np.float32).reshape(-1, 4)[:, :1]
        k = k * (1 - e) + e
    c[:, :3] *= k
    imgs["color"].pixels[:] = c.ravel()
    for kind in ("color", "normal", "roughness", "metalness") + (("emissive",) if glowing else ()):
        im = imgs[kind]
        im.filepath_raw = os.path.join(OUT, "maps", f"NHAcc_{key}_{kind}.png")
        im.file_format = "PNG"; im.save()
    return imgs


def load_maps(key):
    imgs = {}
    for kind in ("color", "normal", "roughness", "metalness", "emissive"):
        p = os.path.join(OUT, "maps", f"NHAcc_{key}_{kind}.png")
        if os.path.exists(p):
            im = bpy.data.images.load(p)
            if kind != "color":
                im.colorspace_settings.name = "Non-Color"
            imgs[kind] = im
    return imgs if len(imgs) >= 4 else None


def alpha_material(ob, path):
    """an Alpha piece's preview material: its RGBA texture (colour + cut-out), as Roblox shows it"""
    m = bpy.data.materials.new(f"Alpha_{ob.name}")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], bs.inputs["Alpha"])
    bs.inputs["Roughness"].default_value = 0.6
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    ob.data.materials.clear(); ob.data.materials.append(m)
    for uv in list(ob.data.uv_layers):
        if uv.name != "Bake":
            ob.data.uv_layers.remove(uv)


def uv_cylinder(axis_c=(0, 0, 1.5), studs_per_tile=0.5):
    """UVs wrapped round the head's vertical axis, `studs_per_tile` studs to one texture repeat (tiled nets)"""
    def f(ob):
        me = ob.data
        for uv in list(me.uv_layers):
            me.uv_layers.remove(uv)
        uv = me.uv_layers.new(name="Bake")
        c = Vector(axis_c)
        for li, loop in enumerate(me.loops):
            co = ob.matrix_world @ me.vertices[loop.vertex_index].co - c
            a = math.atan2(co.x, -co.y)
            r = math.hypot(co.x, co.y)
            uv.data[li].uv = (a * max(r, 0.3) / studs_per_tile, co.z / studs_per_tile)
    return f


def uv_front(x0, x1, z0, z1):
    """UVs projected from the front over the box x0..x1, z0..z1 (one image across a mask)"""
    def f(ob):
        me = ob.data
        for uv in list(me.uv_layers):
            me.uv_layers.remove(uv)
        uv = me.uv_layers.new(name="Bake")
        for li, loop in enumerate(me.loops):
            co = ob.matrix_world @ me.vertices[loop.vertex_index].co
            uv.data[li].uv = ((co.x - x0) / (x1 - x0), (co.z - z0) / (z1 - z0))
    return f


def final_material(objs, key, imgs):
    m = bpy.data.materials.new(f"NHAcc_{key}")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    def tex(kind):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = imgs[kind]
        return t
    nt.links.new(tex("color").outputs["Color"], bs.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex("roughness").outputs["Color"], bs.inputs["Roughness"])
    nt.links.new(tex("metalness").outputs["Color"], bs.inputs["Metallic"])
    if "emissive" in imgs:   # preview what Roblox shows: colour x mask x EmissiveStrength
        e = tex("emissive")
        nt.links.new(tex("color").outputs["Color"], bs.inputs["Emission Color"])
        mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = GLOW_PREVIEW
        nt.links.new(e.outputs["Color"], mm.inputs[0])
        nt.links.new(mm.outputs[0], bs.inputs["Emission Strength"])
    for ob in objs:
        ob.data.materials.clear(); ob.data.materials.append(m)


GLOW_PREVIEW = 4.0
MANNEQUIN_HAIR = False   # headwear batches turn the cap on


# ---------- rigs
def make_rig(ob, bones, weight_fn):
    """bones: [(name, head, tail, parent)], weight_fn(co) -> {bone: w}. Parents the mesh to a new armature."""
    arm_d = bpy.data.armatures.new(f"{ob.name}Rig")
    arm = _new_obj(f"{ob.name}Rig", arm_d)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, head, tail, parent in bones:
        b = arm_d.edit_bones.new(name)
        b.head = head
        b.tail = tail if (Vector(tail) - Vector(head)).length > 1e-3 else Vector(head) + Vector((0, 0, -0.05))
        if parent:
            b.parent = eb[parent]
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    groups = {name: ob.vertex_groups.new(name=name) for name, *_ in bones}
    worst = 0
    for v in ob.data.vertices:
        w = weight_fn(ob.matrix_world @ v.co)
        items = sorted(((b, x) for b, x in w.items() if x > 1e-4), key=lambda t: -t[1])[:4]
        worst = max(worst, len(items))
        tot = sum(x for _, x in items) or 1.0
        for b, x in items:
            groups[b].add([v.index], x / tot, "REPLACE")
    ob.parent = arm
    md = ob.modifiers.new("Armature", "ARMATURE"); md.object = arm
    return arm


def chain_rig(ob, root, cols, falloff=0.9, rigid_above=None):
    """CapeSway-style rig from columns of joint points: cols = [[p0 (hinge), p1, ..., pk], ...] in character space.
    Root at `root`; H<n> at p0 (fixed); C<n>_<k> from p(k) to p(k+1). Each vertex is weighted to the nearest column's
    segments by distance along the column (smooth across neighbouring joints)."""
    bones = [("Root", Vector(root), Vector(root) + Vector((0, 0, 0.08)), None)]
    segs = []
    for n, col in enumerate(cols):
        col = [Vector(p) for p in col]
        bones.append((f"H{n}", col[0], col[0] + (col[1] - col[0]) * 0.25, "Root"))
        parent = f"H{n}"
        for k in range(len(col) - 1):
            nm = f"C{n}_{k + 1}"
            bones.append((nm, col[k], col[k + 1], parent))
            segs.append((nm, col[k], col[k + 1], n, k))
            parent = nm

    def wfn(co):
        if rigid_above is not None and co.z > rigid_above:
            return {"Root": 1.0}
        best = {}
        # nearest column by horizontal distance to its polyline
        dists = []
        for n, col in enumerate(cols):
            col = [Vector(p) for p in col]
            dmin = min(_seg_dist(co, a, b)[0] for a, b in zip(col, col[1:]))
            dists.append((dmin, n))
        dists.sort()
        use = [dists[0]] + ([dists[1]] if len(dists) > 1 and dists[1][0] < dists[0][0] * 1.6 + 0.05 else [])
        tot_c = 0
        for d, n in use:
            cw = 1.0 / (d + 0.05) ** 2
            tot_c += cw
            col = [Vector(p) for p in cols[n]]
            # position along the column -> weights on the two nearest segments
            seg_d = [(_seg_dist(co, a, b), k) for k, (a, b) in enumerate(zip(col, col[1:]))]
            (dd, t), k = min(seg_d, key=lambda s: s[0][0])
            names = [f"C{n}_{k + 1}"]
            ws = [1.0]
            if t < 0.35 and k > 0:
                f = 0.5 - t / 0.7
                names, ws = [f"C{n}_{k}", f"C{n}_{k + 1}"], [f, 1 - f]
            elif t < 0.35 and k == 0:
                f = (0.35 - t) / 0.35 * falloff
                names, ws = [f"H{n}", f"C{n}_1"], [f, 1 - f]
            elif t > 0.65 and k + 1 < len(col) - 1:
                f = (t - 0.65) / 0.7
                names, ws = [f"C{n}_{k + 1}", f"C{n}_{k + 2}"], [1 - f, f]
            for nm, x in zip(names, ws):
                best[nm] = best.get(nm, 0) + x * cw
        return {k: v / tot_c for k, v in best.items()}
    return make_rig(ob, bones, wfn), bones


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab))))
    return (p - (a + ab * t)).length, t


def pendulum_rig(ob, pivot, links, rigid_below=None):
    """a hanging thing (watch, lantern, grimoire): Root at the pivot, H0 fixed, C0_1..k down the hang (links = joint
    points below the pivot); everything below the last joint rides the last bone; everything above the pivot (straps,
    hooks, belts) stays on Root"""
    return chain_rig(ob, pivot, [[pivot] + list(links)], rigid_above=Vector(pivot).z + 0.01)


def export_fbx(key, objs, arms):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    for a in arms:
        a.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", f"NHAcc_{key}.fbx"), use_selection=True,
                             object_types={"MESH", "ARMATURE"}, apply_unit_scale=True, global_scale=0.01,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP",
                             embed_textures=False, add_leaf_bones=False, bake_anim=False, use_armature_deform_only=True)


# ================================================================== previews
def _pm(name, rgb, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


HAIR_DIR = "E:/NH-Work/hair_rigged"
TEX_DIR = "E:/NH-Work/acc/maps"   # the generated alpha textures (acc_textures.py)


def _hair_offsets():
    """head centre relative to each rigged hair's bounding-box centre (the hair FBX's own frame), from the hair rig report"""
    out = {}
    try:
        import re
        for line in open(os.path.join(HAIR_DIR, "rig_report.txt"), encoding="utf-8"):
            m = re.match(r"(\w+): head from '.*' at \(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", line)
            if m:
                out[m.group(1)] = tuple(float(m.group(k)) for k in (2, 3, 4))
    except OSError:
        pass
    return out


HAIR_ATTACH = os.path.join(HERE, "hair_attach.txt")   # from NH Combat Test: each catalog hair's Handle.HairAttachment


def _hair_attach():
    out = {}
    if os.path.exists(HAIR_ATTACH):
        for line in open(HAIR_ATTACH, encoding="utf-8"):
            parts = line.strip().split("|")
            if len(parts) == 4:
                out[parts[0]] = ([float(x) for x in parts[1].split(",")], [float(x) for x in parts[2].split(",")],
                                 [float(x) for x in parts[3].split(",")])
    return out


def _rbx_rot(rx, ry, rz):
    """Roblox CFrame.fromOrientation(rx, ry, rz) (degrees): applied Y, then X, then Z  ->  R = Ry * Rx * Rz"""
    def R(axis, a):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        if axis == "X":
            return Matrix(((1, 0, 0), (0, c, -s_), (0, s_, c)))
        if axis == "Y":
            return Matrix(((c, 0, s_), (0, 1, 0), (-s_, 0, c)))
        return Matrix(((c, -s_, 0), (s_, c, 0), (0, 0, 1)))
    return R("Y", ry) @ R("X", rx) @ R("Z", rz)


def real_hair(name):
    """one of the game's rigged hairs on the nominal head exactly as the game wears it: the Accessory weld puts
    Handle = Head.HairAttachment (0, 0.6, 0) * Handle.HairAttachment:Inverse(), the catalog hair at 0.88 of its size
    (UI.Appearance HAIR_FIT) on the 0.9-scale player head, i.e. 0.88 / 0.9 on the nominal head. The FBX imports into
    Blender as (-x, z, y) of the Roblox handle frame."""
    att = _hair_attach().get(name)
    path = os.path.join(HAIR_DIR, f"{name}.fbx")
    if att is None or not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    mesh = next(o for o in new if o.type == "MESH")
    mw = mesh.matrix_world.copy()
    mesh.parent = None
    mesh.matrix_world = mw
    mesh.modifiers.clear()
    for o in new:
        if o is not mesh:
            bpy.data.objects.remove(o)
    me = mesh.data
    me.transform(mesh.matrix_world)
    mesh.matrix_world = Matrix()
    pts = [v.co.copy() for v in me.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2
    k = 0.88 / 0.9
    pos, ori, _ = att
    Ra = _rbx_rot(*ori)
    a = Vector(pos) * k
    head_att = Vector((0, 0.6, 0))
    for v in me.vertices:
        q = v.co - c
        pr = Vector((-q.x, q.z, q.y)) * k                 # Blender (as imported) -> the Roblox handle frame
        w = head_att + Ra.transposed() @ (pr - a)         # Handle frame -> head frame (Roblox)
        v.co = Vector((-w.x, w.z, w.y + 1.5))             # Roblox head frame -> character space (Blender)
    me.update()
    me.materials.clear(); me.materials.append(_pm("Hair", (0.035, 0.028, 0.03), 0.42))
    mesh["nh_mannequin"] = True
    return mesh


def mannequin(body="standard", hidden=()):
    """the R6 body at character space; standard = bevelled boxes, else the body type's part meshes"""
    skin = _pm("Skin", (0.62, 0.45, 0.36), 0.55)
    coat = _pm("Coat", (0.045, 0.042, 0.05), 0.85)
    shirt = _pm("Shirt", (0.035, 0.033, 0.04), 0.85)
    trous = _pm("Trousers", (0.028, 0.027, 0.032), 0.85)
    made = []
    parts = {"Torso": (Vector((0, 0, 0)), coat), "LeftArm": (Vector((1.5, 0, 0)), shirt),
             "RightArm": (Vector((-1.5, 0, 0)), shirt), "LeftLeg": (Vector((0.5, 0, -2)), trous),
             "RightLeg": (Vector((-0.5, 0, -2)), trous)}
    B = load_bodies() if body != "standard" else {}
    for part, (loc, m) in parts.items():
        if part in hidden:
            continue
        if body == "standard":
            sz = (2, 1, 2) if part == "Torso" else (1, 1, 2)
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
            o = bpy.context.object; o.scale = sz
            bpy.ops.object.transform_apply(scale=True)
            md = o.modifiers.new("b", "BEVEL"); md.width = 0.05; md.segments = 3
        else:
            src = B[body][part]
            o = _new_obj(f"M_{part}", src.data.copy())
            o.location = loc
        o.data.materials.clear(); o.data.materials.append(m)
        for p in o.data.polygons:
            p.use_smooth = True
        o["nh_mannequin"] = True
        made.append(o)
    if "Head" not in hidden:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.2, location=(0, 0, 1.5), vertices=40)
        hd = bpy.context.object
        md = hd.modifiers.new("b", "BEVEL"); md.width = 0.25; md.segments = 5
        hd.data.materials.append(skin)
        for p in hd.data.polygons:
            p.use_smooth = True
        hd["nh_mannequin"] = True
        made.append(hd)
        if not MANNEQUIN_HAIR:
            return made
        if isinstance(MANNEQUIN_HAIR, dict):
            h = real_hair(MANNEQUIN_HAIR.get("female" if body != "standard" and body in ("female", "petite", "toned", "curvy", "strong", "plus") else "male"))
            if h is not None:
                made.append(h)
                return made
        prof = [(0.0, 2.17), (0.30, 2.165), (0.52, 2.13), (0.635, 2.03), (0.66, 1.90), (0.655, 1.75), (0.645, 1.55),
                (0.63, 1.30)]
        verts, faces = [], []
        seg = 48
        for s_ in range(seg):
            a = 2 * math.pi * s_ / seg
            front = max(0.0, -math.sin(a))     # 1 at the face (-Y)
            low = lerp(1.30, 1.86, front ** 0.7)   # the hair line: low at the back, a fringe over the brow
            for r, h in prof:
                h2 = max(h, low) if h < 2.0 else h
                verts.append(Vector((r * math.cos(a), r * math.sin(a) * 1.0, h2)))
        n = len(prof)
        for s_ in range(seg):
            s2 = (s_ + 1) % seg
            for k in range(n - 1):
                faces.append([s_ * n + k, s2 * n + k, s2 * n + k + 1, s_ * n + k + 1])
        me = bpy.data.meshes.new("HairM"); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
        hr = _new_obj("Hair", me)
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        hr.data.materials.append(_pm("Hair", (0.03, 0.025, 0.028), 0.42))
        for p in hr.data.polygons:
            p.use_smooth = True
        hr["nh_mannequin"] = True
        made.append(hr)
        return made
        # a short dark hair cap: the top of a sphere, with a fringe line above the face
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.655, location=(0, 0.03, 1.56), segments=40, ring_count=20)
        hr = bpy.context.object; hr.scale = (1, 1, 0.92)
        bpy.ops.object.transform_apply(scale=True)
        bm = bmesh.new(); bm.from_mesh(hr.data)
        cut = [v for v in bm.verts if v.co.z < (0.46 if v.co.y < -0.3 else 0.34 if v.co.y < 0.05 else 0.10 if v.co.y < 0.35 else -0.25)]
        bmesh.ops.delete(bm, geom=cut, context="VERTS")
        bm.to_mesh(hr.data); bm.free()
        hr.data.materials.append(_pm("Hair", (0.02, 0.018, 0.022), 0.45))
        for p in hr.data.polygons:
            p.use_smooth = True
        hr["nh_mannequin"] = True
        made.append(hr)
    return made


def stage():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("W"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.011, 0.016, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    for loc, energy, col, size in (((4, -6, 5), 900, (1.0, 0.82, 0.62), 3), ((-5, 5, 3), 650, (0.6, 0.66, 1.0), 3),
                                   ((0, 6, 6), 450, (1.0, 0.6, 0.55), 4), ((-5, -4, -1), 220, (1, 0.8, 0.7), 4)):
        L = bpy.data.lights.new("L", "AREA"); L.energy = energy; L.color = col; L.size = size
        o = _new_obj("L", L); o.location = loc
        o.rotation_euler = (Vector((0, 0, -0.3)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -3.0))
    fl = bpy.context.object; fl.data.materials.append(_pm("Floor", (0.03, 0.028, 0.03), 0.9))
    fl["nh_stage"] = True
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    cam = _new_obj("Cam", bpy.data.cameras.new("Cam")); sc.camera = cam
    cam.data.lens = 70
    return cam


VIEW = {"front34": (5.5, -9.5, 2.2), "front": (0, -11, 1.6), "side": (11, 0.6, 1.4), "side_r": (-11, 0.6, 1.4),
        "back": (0, 11, 1.8), "back34": (-7, 8.5, 3.0), "top": (0.01, 2.5, 10)}


def shoot(cam, path, view, target=(0, 0, -0.35), lens=70, res=None, aspect=1.15):
    sc = bpy.context.scene
    r = res or RES
    sc.render.resolution_x = r; sc.render.resolution_y = int(r * aspect)
    cam.data.lens = lens
    loc = Vector(VIEW[view]) if isinstance(view, str) else Vector(view)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - loc).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def preview_glow(objs):
    for name, ob in objs.items():
        spec = PIECES.get(name, {})
        if spec.get("kind") == "Glow":
            ob.data.materials.clear(); ob.data.materials.append(mat_glow("G_" + name, spec["glow"], 5.0))


def pose_swing(arms, swing):
    """CapeSway's back swing, (depth-1)*0.12*swing about the right axis, on every chain bone (weight check)"""
    for arm in arms:
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="POSE")
        right = Vector((-1, 0, 0))
        for pb in arm.pose.bones:
            depth, p = 0, pb.parent
            while p:
                depth += 1; p = p.parent
            if depth < 2:
                continue
            rest = pb.bone.matrix_local.to_3x3()
            axis = rest.inverted() @ right
            pb.rotation_mode = "AXIS_ANGLE"
            pb.rotation_axis_angle = (-(depth - 1) * 0.12 * swing, *axis)
        bpy.ops.object.mode_set(mode="OBJECT")


# ================================================================== the run
ITEMS = {}   # key -> dict(name, build, views, solo_target, solo_dist, notes)


def item(key, name, views=None, focus=(0, 0, -0.35), solo=None, female=True, lens=50, render=None,
         close=((3.2, -6.0, 1.6), (0, 0, 0.3), 115), each=False, mirror=False):
    """render(objs, cam) -> extra shots after the standard ones (lineups, close-ups)"""
    def deco(fn):
        ITEMS[key] = dict(name=name, build=fn, views=views, focus=focus, solo=solo, female=female, lens=lens,
                          render=render, close=close, each=each, mirror=mirror)
        return fn
    return deco


def run(key):
    spec = ITEMS[key]
    reset()
    M = palette()
    extra = spec["build"](M) or {}
    if spec.get("mirror"):   # built on the character's left (+X), worn on the right: mirror every part across x = 0
        for ob in PARTS:
            bpy.context.view_layer.objects.active = ob
            for md in list(ob.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=md.name)
                except RuntimeError:
                    ob.modifiers.remove(md)
            ob.data.transform(ob.matrix_world)
            ob.matrix_world = Matrix()
            ob.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
            ob.data.flip_normals()
    objs = join_pieces()
    baked = [o for n, o in objs.items() if PIECES[n]["kind"] == "Main"]
    info = {}
    # fit table before rigging (rest pose, world space)
    for n, o in objs.items():
        info[n] = dict(fit_body=fit_table(o, PIECES[n]["mount"]))
    for n, o in objs.items():
        p = PIECES[n]
        if p["kind"] == "Alpha":
            p["uv"](o)
            alpha_material(o, p["alpha"])
    imgs = None
    if baked:
        # alternative variants (each = ...) are worn one at a time: bake each apart from the others, so no piece's
        # ambient occlusion or shading picks up the shadow of a variant that's never worn with it
        moved = []
        if spec.get("each"):
            groups = spec["each"] if isinstance(spec["each"], dict) else {n: [n] for n in objs}
            for gi, (g, names) in enumerate(groups.items()):
                for n in names:
                    if n in objs:
                        objs[n].location.x += 12.0 * gi
                        moved.append((objs[n], 12.0 * gi))
            bpy.context.view_layer.update()
        bake_uv(baked)
        imgs = bake_all(baked, key) if BAKE else load_maps(key)
        for ob, dx in moved:
            ob.location.x -= dx
        bpy.context.view_layer.update()
        if imgs:
            final_material(baked, key, imgs)
    arms = []
    layout = dict(key=key, name=spec["name"], atlas=SIZE, pieces={}, notes=extra.get("notes", ""))
    for n, o in objs.items():
        p = PIECES[n]
        me = o.data
        pts = [o.matrix_world @ v.co for v in me.vertices]
        lo = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
        hi = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
        centre = (lo + hi) / 2
        c = MOUNT_CENTRE[p["mount"]]
        tris = sum(len(f.vertices) - 2 for f in me.polygons)
        ent = dict(mount=p["mount"], kind=p["kind"], tris=tris, fit=to_rbx(centre - c),
                   size=[hi.x - lo.x, hi.z - lo.z, hi.y - lo.y], fit_body=info[n]["fit_body"])
        if p["kind"] == "Glow":
            ent["glow"] = [round(x, 3) for x in p["glow"]]
        if p.get("sway"):
            ent["sway"] = p["sway"]
        if p.get("keepout"):
            ent["keepout"] = to_rbx(Vector(p["keepout"]))   # toward the body, in the mount's Roblox axes
        if p.get("lock"):
            ent["lock"] = p["lock"]   # "X": bends only about the side axis (fore and aft); "Z": only about the depth axis (flat, side to side)
        if p["kind"] == "Alpha":
            ent["alpha_tex"] = os.path.basename(p["alpha"])
        if p["rig"]:
            arm, bones = p["rig"](o)
            arms.append(arm)
            ent["bones"] = [dict(name=b[0], head=to_rbx(Vector(b[1]) - c), parent=b[3]) for b in bones]
        if max(ent["size"]) > 20.4:
            print(f"[acc] WARNING {n} over the import cap: {ent['size']}")
        layout["pieces"][n] = ent
    layout["tris"] = sum(e["tris"] for e in layout["pieces"].values())
    for k, v in extra.items():
        if k != "notes":
            layout[k] = v
    with open(os.path.join(OUT, "layout", f"{key}.json"), "w") as fh:
        json.dump(layout, fh, indent=1)
    export_fbx(key, list(objs.values()), arms)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "blend", f"{key}.blend"))
    print(f"[acc] {key}: {layout['tris']} tris, pieces " +
          ", ".join(f"{n}({e['mount']},{e['tris']})" for n, e in layout["pieces"].items()))
    if RENDER:
        render_item(key, objs, arms, spec, layout)


def body_fit_pose(objs, layout, bid):
    """scale each piece's depth about its mount's centre plane by the body's fit (what the game does per body)"""
    saved = []
    for n, ob in objs.items():
        e = layout["pieces"][n]
        s = e["fit_body"].get(bid, 1.0) if bid != "standard" else 1.0
        tgt = ob.parent if ob.parent is not None else ob
        saved.append((tgt, tgt.matrix_world.copy()))
        c = MOUNT_CENTRE[e["mount"]]
        S = Matrix.Translation(c) @ Matrix.Diagonal((1, s, 1, 1)) @ Matrix.Translation(-c)
        tgt.matrix_world = S @ tgt.matrix_world
    return saved


def render_item(key, objs, arms, spec, layout):
    preview_glow(objs)
    if spec.get("each") and spec.get("render"):
        cam0 = bpy.context.scene.camera or stage()
        spec["render"](objs, cam0, [])
    if spec.get("each") and len(objs) > 1:
        # each piece (or each group of pieces, each = {variant: [pieces]}) is its own wardrobe item: render it alone,
        # as <key>-<variant>
        groups = spec["each"] if isinstance(spec["each"], dict) else {n: [n] for n in objs}
        for g, names in groups.items():
            for m, o in objs.items():
                o.hide_render = m not in names
                if o.parent is not None:
                    o.parent.hide_render = m not in names
            sub = dict(spec); sub["each"] = False
            _render_one(f"{key}-{g}", objs, [a for a in arms if any(a.name.startswith(n) for n in names)], sub, layout)
        return
    _render_one(key, objs, arms, spec, layout)


def _render_one(key, objs, arms, spec, layout):
    cam = bpy.context.scene.camera or stage()
    views = spec["views"] or VIEWS
    man = mannequin("standard")
    for v in views:
        if v == "close":
            loc, tgt, lens = spec["close"]
            shoot(cam, os.path.join(OUT, "renders", f"{key}_close.png"), loc, target=tgt, lens=lens)
        else:
            shoot(cam, os.path.join(OUT, "renders", f"{key}_{v}.png"), v, target=(0, 0, -0.5), lens=spec["lens"])
    if spec.get("render"):
        spec["render"](objs, cam, man)
    if spec.get("solo"):
        for o in man:
            o.hide_render = True
        loc, tgt, lens = spec["solo"]
        shoot(cam, os.path.join(OUT, "renders", f"{key}_solo.png"), loc, target=tgt, lens=lens, aspect=0.8)
    for o in man:
        bpy.data.objects.remove(o)
    if spec.get("female") and FEMALE_TOO:
        man = mannequin("female")
        saved = body_fit_pose(objs, layout, "female")
        for v in ("front34", "side"):
            shoot(cam, os.path.join(OUT, "renders", f"{key}_{v}_f.png"), v, target=(0, 0, -0.5), lens=spec["lens"])
        loc, tgt, lens = spec["close"]
        shoot(cam, os.path.join(OUT, "renders", f"{key}_close_f.png"), loc, target=tgt, lens=lens)
        for t, mw in saved:
            t.matrix_world = mw
        for o in man:
            bpy.data.objects.remove(o)
    if arms:
        man = mannequin("standard")
        pose_swing(arms, 0.8)
        shoot(cam, os.path.join(OUT, "renders", f"{key}_swing_side.png"), "side", target=(0, 0, -0.5), lens=spec["lens"])
        pose_swing(arms, 0.0)
        for o in man:
            bpy.data.objects.remove(o)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    import importlib
    sys.modules.setdefault("nh_acc", sys.modules[__name__])
    for fn in sorted(os.listdir(HERE), key=lambda f: (len(f), f)):
        if fn.startswith("nh_acc_batch") and fn.endswith(".py"):
            importlib.import_module(fn[:-3])
    targets = [a for a in argv if not a.startswith("--") and (argv.index(a) == 0 or not argv[argv.index(a) - 1].startswith("--"))]
    want = targets[0].split(",") if targets else []
    keys = []
    for w in want:
        if w == "all":
            keys += list(ITEMS)
        elif w.startswith("batch"):
            keys += [k for k, s in ITEMS.items() if s["build"].__module__.endswith(w)]
        else:
            keys.append(w)
    for k in keys:
        run(k)
