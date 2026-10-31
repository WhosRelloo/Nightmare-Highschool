"""Nightmare Highschool school props (Blender 5.x, run headless).

usage:
  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props.py -- <Prop> [--size 1024] [--samples 64]
  Props: StudentDesk, TeacherDesk, Chalkboard, Locker, HidingLocker   (or "all")

Each prop is modelled in studs (1 Blender unit = 1 stud), facing -Y (its front), base on the ground at the origin.
Pipeline per prop:
  1. build parts with bevels (wood, wrought iron, slate, brass, enamel...), source materials use the seamless
     PBR set in art/props/source (box-projected, so no UVs are needed for the look itself)
  2. join, apply modifiers, smart-UV a single atlas, bake colour (x ambient occlusion), normal, roughness,
     metalness into art/props/textures/<Prop>_{color,normal,rough,metal}.png
  3. export art/props/fbx/<Prop>.fbx (one mesh, one material) and render art/props/previews/<Prop>.png
In Roblox each prop is one MeshPart with a SurfaceAppearance (asset ids in art/props/props.json).
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
OUT_TEX = os.path.join(HERE, "textures")
OUT_FBX = os.path.join(HERE, "fbx")
OUT_PRE = os.path.join(HERE, "previews")
for d in (OUT_TEX, OUT_FBX, OUT_PRE):
    os.makedirs(d, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PROP = argv[0] if argv else "StudentDesk"
SIZE = int(argv[argv.index("--size") + 1]) if "--size" in argv else 1024
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64


# ------------------------------------------------------------------ scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    return sc


# ------------------------------------------------------------------ materials

_img_cache = {}


def _img(name):
    if name not in _img_cache:
        p = os.path.join(SRC, name)
        im = bpy.data.images.load(p)
        if not name.endswith("_color.png"):
            im.colorspace_settings.name = "Non-Color"
        _img_cache[name] = im
    return _img_cache[name]


def _tex(nt, set_name, kind, scale, x, y):
    """Box-projected image texture from art/props/source, in object space."""
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (x - 600, y)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (x - 400, y)
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage"); t.location = (x - 200, y)
    t.image = _img(f"{set_name}_{kind}.png")
    t.projection = "BOX"
    t.projection_blend = 0.25
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    return t


def _weather(nt, bs, col, rough, metal, normal, wear, wear_metal, dirt):
    """Bake-time weathering, fed into the Principled BSDF:
    edges (1 - dot(bevelled normal, true normal)): lighter wear, or bare metal showing through paint;
    crevices (1 - ambient occlusion): darker and rougher; the normal gets rounded edges (Bevel)."""
    L = nt.links.new
    def math(op, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    bev = nt.nodes.new("ShaderNodeBevel"); bev.inputs["Radius"].default_value = 0.035; bev.samples = 8
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    L(bev.outputs["Normal"], dot.inputs[0]); L(geo.outputs["Normal"], dot.inputs[1])
    edge = math("MULTIPLY", math("SUBTRACT", 1.0, dot.outputs["Value"]), 22.0, clamp=True)
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion"); ao.samples = 12; ao.only_local = True
    ao.inputs["Distance"].default_value = 0.2
    crev = math("MULTIPLY", math("SUBTRACT", 1.0, ao.outputs["AO"]), dirt, clamp=True)
    ew = math("MULTIPLY", edge, wear, clamp=True)
    # colour
    c1 = nt.nodes.new("ShaderNodeMix"); c1.data_type = "RGBA"; c1.blend_type = "MULTIPLY"
    L(crev, c1.inputs["Factor"]); L(col, c1.inputs[6]); c1.inputs[7].default_value = (0.38, 0.34, 0.3, 1)
    c2 = nt.nodes.new("ShaderNodeMix"); c2.data_type = "RGBA"
    if wear_metal:
        c2.blend_type = "MIX"; c2.inputs[7].default_value = (0.42, 0.42, 0.44, 1)
    else:
        c2.blend_type = "SCREEN"; c2.inputs[7].default_value = (0.32, 0.27, 0.22, 1)
    L(ew, c2.inputs["Factor"]); L(c1.outputs[2], c2.inputs[6])
    L(c2.outputs[2], bs.inputs["Base Color"])
    # roughness: dirtier in crevices, rubbed smoother on edges
    r = math("ADD", rough, math("MULTIPLY", crev, 0.25))
    r = math("SUBTRACT", r, math("MULTIPLY", ew, 0.3), clamp=True)
    L(r, bs.inputs["Roughness"])
    # metalness: bare metal on worn paint edges
    L(math("MAXIMUM", metal, ew) if wear_metal else metal, bs.inputs["Metallic"])
    # normal: rounded edges on top of the texture normal
    bn = nt.nodes.new("ShaderNodeBevel"); bn.inputs["Radius"].default_value = 0.018; bn.samples = 8
    if normal is not None:
        L(normal, bn.inputs["Normal"])
    L(bn.outputs["Normal"], bs.inputs["Normal"])


def material(name, set_name=None, tint=(1, 1, 1), scale=0.15, rough=None, metal=None, normal=0.8,
             base=None, rough_add=0.0, rough_mul=1.0, color_mul=1.0, wear=0.45, wear_metal=False, dirt=0.65):
    """A principled material. With set_name, colour/normal/rough/metal come from the seamless set, tinted.
    Every material gets bake-time weathering (edge wear, crevice dirt, rounded edges): see _weather."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location = (600, 0)
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    if set_name:
        c = _tex(nt, set_name, "color", scale, 0, 300)
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.location = (100, 300)
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(c.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (tint[0] * color_mul, tint[1] * color_mul, tint[2] * color_mul, 1)
        col = mix.outputs[2]
        n = _tex(nt, set_name, "normal", scale, 0, 0)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (100, 0)
        nm.inputs["Strength"].default_value = normal
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nrm = nm.outputs["Normal"]
        if rough is None:
            r = _tex(nt, set_name, "rough", scale, 0, -300)
            mt = nt.nodes.new("ShaderNodeMath"); mt.operation = "MULTIPLY_ADD"; mt.location = (100, -300)
            mt.inputs[1].default_value = rough_mul; mt.inputs[2].default_value = rough_add
            nt.links.new(r.outputs["Color"], mt.inputs[0])
            rgh = mt.outputs[0]
        else:
            rv = nt.nodes.new("ShaderNodeValue"); rv.outputs[0].default_value = rough
            rgh = rv.outputs[0]
        if metal is None:
            mm = _tex(nt, set_name, "metal", scale, 0, -600)
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(mm.outputs["Color"], sep.inputs["Color"])
            mtl = sep.outputs[0]
        else:
            mv = nt.nodes.new("ShaderNodeValue"); mv.outputs[0].default_value = metal
            mtl = mv.outputs[0]
    else:
        cv = nt.nodes.new("ShaderNodeRGB"); cv.outputs[0].default_value = (*(base or tint), 1)
        col = cv.outputs[0]
        rv = nt.nodes.new("ShaderNodeValue"); rv.outputs[0].default_value = 0.5 if rough is None else rough
        rgh = rv.outputs[0]
        mv = nt.nodes.new("ShaderNodeValue"); mv.outputs[0].default_value = 0.0 if metal is None else metal
        mtl = mv.outputs[0]
        # a little surface variation so flat materials aren't perfectly flat
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.location = (-300, -200)
        nz.inputs["Scale"].default_value = 18
        bump = nt.nodes.new("ShaderNodeBump"); bump.location = (0, -200)
        bump.inputs["Strength"].default_value = 0.08
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nrm = bump.outputs["Normal"]
    _weather(nt, bs, col, rgh, mtl, nrm, wear, wear_metal, dirt)
    return m


def palette():
    """The school's materials (style guide: candlelit oak, wrought iron, slate, brass, deep crimson enamel)."""
    return {
        "oak": material("Oak", "NH_DeskWood", tint=(0.62, 0.40, 0.24), scale=0.22, rough_add=0.05, wear=0.5),
        "oakdark": material("OakDark", "NH_DeskWood", tint=(0.36, 0.22, 0.13), scale=0.22, rough_add=0.08, wear=0.5),
        "iron": material("Iron", "NH_Iron", tint=(0.12, 0.115, 0.125), scale=0.45, rough_add=0.05, wear=0.55, wear_metal=True),
        "slate": material("Slate", "NH_Slate", tint=(0.32, 0.36, 0.34), scale=0.18, rough_mul=0.6, rough_add=0.35, normal=0.35, wear=0.2),
        "brass": material("Brass", "NH_Brass", tint=(1, 1, 1), scale=0.5, wear=0.35, dirt=0.8),
        "crimson": material("Crimson", "NH_PaintedMetal", tint=(0.24, 0.035, 0.05), scale=1.3, wear=0.7, wear_metal=True),
        "crimsonin": material("CrimsonIn", "NH_PaintedMetal", tint=(0.11, 0.02, 0.03), scale=0.65, rough_add=0.15, wear=0.3, wear_metal=True),
        "leatherdark": material("LeatherDark", "NH_Leather", tint=(0.17, 0.026, 0.036), scale=0.7, wear=0.4),
        "stone": material("Stone", "NH_Limestone", tint=(0.95, 0.93, 0.88), scale=0.28, wear=0.3, dirt=0.9),
        "stonedark": material("StoneDark", "NH_Limestone", tint=(0.6, 0.58, 0.55), scale=0.28, wear=0.25, dirt=0.9),
        "inkblue": material("InkBlue", "NH_Leather", tint=(0.12, 0.16, 0.36), scale=0.7, wear=0.4),
        "glassamber": material("GlassAmber", base=(0.55, 0.32, 0.08), rough=0.15, wear=0.0, dirt=0.3),
        "glassclear": material("GlassClear", base=(0.75, 0.8, 0.85), rough=0.05, wear=0.0, dirt=0.0),
        "paper": material("Paper", "NH_Paper", tint=(1, 1, 1), scale=0.5, wear=0.2, dirt=0.5),
        "brasssteel": material("Steel", base=(0.72, 0.72, 0.74), rough=0.22, metal=1.0, wear=0.3),
        "leather": material("Leather", "NH_Leather", tint=(0.26, 0.035, 0.05), scale=0.7, wear=0.45),
        "chalk": material("Chalk", base=(0.92, 0.91, 0.86), rough=0.95, wear=0.0, dirt=0.3),
        "felt": material("Felt", base=(0.10, 0.10, 0.11), rough=0.98, wear=0.0),
        "glass": material("Ink", base=(0.02, 0.02, 0.04), rough=0.08, wear=0.0, dirt=0.0),
    }


# ------------------------------------------------------------------ geometry helpers

PARTS = []
GROUP = "Main"
HINGES = {}      # group -> (hinge point, swing sign) for doors that open


def set_group(name, hinge=None, swing=-1):
    """Parts built after this belong to `name` (exported as its own mesh). A door group gives its hinge
    point (its origin in Roblox) and swing sign (-1 = hinge on the left, opens outward)."""
    global GROUP
    GROUP = name
    if hinge is not None:
        HINGES[name] = (Vector(hinge), swing)


def _finish(ob, mat, bevel, segments=2):
    ob.data.materials.append(mat)
    if bevel > 0:
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = segments
        b.limit_method = "ANGLE"
        b.harden_normals = True
    ob["nh_group"] = GROUP
    PARTS.append(ob)
    return ob


def box(name, size, loc, mat, bevel=0.02, rot=(0, 0, 0), segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, mat, bevel, segments)


def cyl(name, radius, depth, loc, mat, rot=(0, 0, 0), verts=24, bevel=0.01):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, mat, bevel)


def tube(name, points, radius, mat, closed=False, res=4, square=False, poly=False):
    """Wrought-iron bar along a path (list of (x,y,z)); smooth bezier (or straight poly segments),
    round or square profile."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    if poly:
        sp = cu.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for p, co in zip(sp.points, points):
            p.co = (co[0], co[1], co[2], 1)
    else:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for p, co in zip(sp.bezier_points, points):
            p.co = co
            p.handle_left_type = p.handle_right_type = "AUTO"
    sp.use_cyclic_u = closed
    if square:
        prof = bpy.data.curves.new(name + "_prof", "CURVE")
        ps = prof.splines.new("POLY")
        ps.points.add(3)
        r = radius
        for i, (x, y) in enumerate([(-r, -r), (r, -r), (r, r), (-r, r)]):
            ps.points[i].co = (x, y, 0, 1)
        ps.use_cyclic_u = True
        prof_ob = bpy.data.objects.new(name + "_prof", prof)
        bpy.context.collection.objects.link(prof_ob)
        cu.bevel_mode = "OBJECT"
        cu.bevel_object = prof_ob
    else:
        cu.bevel_mode = "ROUND"
        cu.bevel_depth = radius
        cu.bevel_resolution = 1
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    if square:
        bpy.data.objects.remove(prof_ob)
    return _finish(ob, mat, 0)


def arch_points(x, z0, z1, y_base, height, n=7):
    """Pointed (gothic) arch from (z0, y_base) to (z1, y_base), apex `height` above, in the X plane."""
    pts = []
    mid = (z0 + z1) / 2
    for i in range(n):
        t = i / (n - 1)
        z = z0 + (z1 - z0) * t
        k = 1 - abs(t - 0.5) * 2               # 0 at the feet, 1 at the apex
        y = y_base + height * math.sin(k * math.pi / 2) ** 0.75
        pts.append((x, z, y))
    return pts


def ring(name, center, radius, axis, mat, thick=0.03):
    """Circle of iron. axis: 'X' (ring in the YZ plane) or 'Y' (ring in the XZ plane)."""
    pts = []
    for i in range(8):
        a = i / 8 * 2 * math.pi
        if axis == "X":
            pts.append((center[0], center[1] + math.cos(a) * radius, center[2] + math.sin(a) * radius))
        elif axis == "Z":
            pts.append((center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius, center[2]))
        else:
            pts.append((center[0] + math.cos(a) * radius, center[1], center[2] + math.sin(a) * radius))
    return tube(name, pts, thick, mat, closed=True, res=2)


# Blender is Z-up; we model with Z = height. Front of every prop faces -Y.

# ------------------------------------------------------------------ props

def student_desk(M):
    """3 W x 2.5 H x 2 D: slanted oak lid with an inkwell, wrought-iron gothic side frames, book shelf."""
    W, D, H = 3.0, 2.0, 2.5
    top_h = 2.38
    # flat back strip with a pencil groove and an inkwell
    box("TopBack", (W, 0.42, 0.1), (0, D / 2 - 0.23, top_h + 0.07), M["oak"], bevel=0.025)
    box("Groove", (W * 0.7, 0.07, 0.03), (0, D / 2 - 0.30, top_h + 0.12), M["oakdark"], bevel=0.01)
    cyl("Inkwell", 0.085, 0.06, (W / 2 - 0.35, D / 2 - 0.2, top_h + 0.13), M["brass"], verts=20)
    cyl("Ink", 0.06, 0.02, (W / 2 - 0.35, D / 2 - 0.2, top_h + 0.155), M["glass"], verts=20, bevel=0)
    # slanted lid (front edge lower), with a lip at the front
    tilt = math.radians(9)
    lid_d = D - 0.44
    box("Lid", (W, lid_d, 0.09), (0, -0.21, top_h - 0.02), M["oak"], bevel=0.03, rot=(tilt, 0, 0))
    box("Lip", (W * 0.98, 0.05, 0.05), (0, -D / 2 + 0.1, top_h - 0.1), M["oakdark"], bevel=0.015)
    # book box under the lid
    box("Shelf", (W - 0.36, D - 0.4, 0.06), (0, 0.02, 1.95), M["oakdark"], bevel=0.015)
    box("ShelfBack", (W - 0.36, 0.05, 0.38), (0, D / 2 - 0.22, 2.12), M["oakdark"], bevel=0.012)
    box("ShelfSideL", (0.05, D - 0.4, 0.36), (-(W - 0.36) / 2, 0.02, 2.13), M["oakdark"], bevel=0.012)
    box("ShelfSideR", (0.05, D - 0.4, 0.36), ((W - 0.36) / 2, 0.02, 2.13), M["oakdark"], bevel=0.012)
    # wrought-iron side frames
    for side, x in (("L", -W / 2 + 0.16), ("R", W / 2 - 0.16)):
        zf, zb = -D / 2 + 0.22, D / 2 - 0.22
        tube(f"LegF{side}", [(x, zf, 0.05), (x, zf + 0.02, 1.0), (x, zf, 2.25)], 0.045, M["iron"])
        tube(f"LegB{side}", [(x, zb, 0.05), (x, zb - 0.02, 1.0), (x, zb, 2.25)], 0.045, M["iron"])
        tube(f"Arch{side}", arch_points(x, zf, zb, 1.65, 0.55), 0.035, M["iron"])
        tube(f"Rail{side}", [(x, zf, 0.45), (x, 0, 0.42), (x, zb, 0.45)], 0.03, M["iron"])
        ring(f"Rose{side}", (x, 0, 1.05), 0.26, "X", M["iron"], thick=0.028)
        for k, (dz, dy) in enumerate([(0, 0.26), (0, -0.26), (0.26, 0), (-0.26, 0)]):
            ring(f"Foil{side}{k}", (x, dz * 0.62, 1.05 + dy * 0.62), 0.1, "X", M["iron"], thick=0.02)
        # scrolled feet
        for z in (zf, zb):
            box(f"Foot{side}{z:+.1f}", (0.14, 0.34, 0.05), (x, z, 0.025), M["iron"], bevel=0.015)
    # front footrest between the frames
    tube("Footrest", [(-W / 2 + 0.16, -D / 2 + 0.22, 0.3), (0, -D / 2 + 0.19, 0.28), (W / 2 - 0.16, -D / 2 + 0.22, 0.3)], 0.03, M["iron"])
    return (W, D, H)


def chalkboard(M):
    """9 W x 4.6 H x 0.4 D wall board: slate in a carved oak frame with a gothic crest and a chalk tray."""
    W, H, D = 9.0, 4.2, 0.18
    y0 = 0.0
    box("Backing", (W, D, H), (0, 0.05, H / 2), M["oakdark"], bevel=0.02)
    box("Slate", (W - 0.7, 0.06, H - 0.75), (0, -0.07, H / 2 + 0.05), M["slate"], bevel=0.01)
    fw = 0.32
    box("FrameTop", (W + 0.2, 0.22, fw), (0, -0.08, H - fw / 2 + 0.05), M["oak"], bevel=0.05, segments=3)
    box("FrameBot", (W + 0.2, 0.22, fw), (0, -0.08, fw / 2 + 0.25), M["oak"], bevel=0.05, segments=3)
    box("FrameL", (fw, 0.22, H), (-W / 2 + fw / 2 - 0.05, -0.08, H / 2 + 0.05), M["oak"], bevel=0.05, segments=3)
    box("FrameR", (fw, 0.22, H), (W / 2 - fw / 2 + 0.05, -0.08, H / 2 + 0.05), M["oak"], bevel=0.05, segments=3)
    # inner bead
    box("BeadTop", (W - 0.66, 0.08, 0.05), (0, -0.12, H - 0.33), M["oakdark"], bevel=0.02)
    box("BeadBot", (W - 0.66, 0.08, 0.05), (0, -0.12, 0.43), M["oakdark"], bevel=0.02)
    # gothic crest: pointed arch pediment with a trefoil
    crest = [(-1.4, -0.08, H + 0.18), (-0.7, -0.08, H + 0.55), (0, -0.08, H + 0.95), (0.7, -0.08, H + 0.55), (1.4, -0.08, H + 0.18)]
    tube("CrestArch", crest, 0.09, M["oak"], square=True)
    box("CrestBase", (3.0, 0.2, 0.16), (0, -0.08, H + 0.2), M["oak"], bevel=0.04)
    for k, (cx, cz) in enumerate([(0, H + 0.66), (-0.2, H + 0.48), (0.2, H + 0.48)]):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.03, location=(cx, -0.14, cz), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.active_object
        t.name = f"Trefoil{k}"
        _finish(t, M["brass"], 0)
    # chalk tray, chalk and an eraser
    box("Tray", (W - 0.6, 0.42, 0.06), (0, -0.3, 0.32), M["oak"], bevel=0.02)
    box("TrayLip", (W - 0.6, 0.04, 0.09), (0, -0.5, 0.37), M["oakdark"], bevel=0.012)
    for k, x in enumerate([-2.6, -2.35, 1.9]):
        cyl(f"Chalk{k}", 0.035, 0.42, (x, -0.33, 0.39), M["chalk"], rot=(0, math.pi / 2, 0.15 * k), verts=10, bevel=0.005)
    box("EraserWood", (0.6, 0.2, 0.09), (2.8, -0.31, 0.41), M["oak"], bevel=0.02)
    box("EraserFelt", (0.58, 0.18, 0.05), (2.8, -0.31, 0.34), M["felt"], bevel=0.01)
    return (W + 0.2, 0.6, H + 0.95)


def teacher_desk(M):
    """7 W x 3 H x 3 D: heavy oak pedestal desk, crimson leather inset, brass pulls, lancet-arch panels."""
    W, D, H = 7.0, 3.0, 3.0
    box("Top", (W, D, 0.16), (0, 0, H - 0.08), M["oak"], bevel=0.05, segments=3)
    box("Leather", (W - 0.9, D - 0.9, 0.012), (0, 0.05, H + 0.003), M["leather"], bevel=0.004)
    pw = 1.9
    for side, x in (("L", -W / 2 + pw / 2 + 0.05), ("R", W / 2 - pw / 2 - 0.05)):
        box(f"Ped{side}", (pw, D - 0.2, H - 0.36), (x, 0, (H - 0.36) / 2 + 0.2), M["oak"], bevel=0.035)
        box(f"Plinth{side}", (pw + 0.08, D - 0.12, 0.2), (x, 0, 0.1), M["oakdark"], bevel=0.03)
        for k in range(3):
            z = 0.55 + k * 0.72
            box(f"Drawer{side}{k}", (pw - 0.22, 0.06, 0.6), (x, -D / 2 + 0.07, z), M["oak"], bevel=0.025)
            box(f"DrawerIn{side}{k}", (pw - 0.42, 0.03, 0.42), (x, -D / 2 + 0.035, z), M["oakdark"], bevel=0.012)
            cyl(f"Pull{side}{k}", 0.05, 0.12, (x, -D / 2 - 0.02, z), M["brass"], rot=(math.pi / 2, 0, 0), verts=16)
            box(f"Plate{side}{k}", (0.3, 0.015, 0.12), (x, -D / 2 + 0.035, z), M["brass"], bevel=0.005)
    # modesty panel with three lancet arches
    mw = W - 2 * pw - 0.1
    box("Modesty", (mw, 0.1, H - 0.7), (0, D / 2 - 0.3, (H - 0.7) / 2 + 0.45), M["oakdark"], bevel=0.02)
    for k in range(3):
        cx = -mw / 3 + k * mw / 3
        pts = [(cx - 0.42, D / 2 - 0.38, 0.75), (cx - 0.42, D / 2 - 0.38, 1.7), (cx, D / 2 - 0.38, 2.25), (cx + 0.42, D / 2 - 0.38, 1.7), (cx + 0.42, D / 2 - 0.38, 0.75)]
        tube(f"Lancet{k}", pts, 0.05, M["oak"], square=True)
    box("Apron", (mw, 0.12, 0.3), (0, -D / 2 + 0.12, H - 0.31), M["oak"], bevel=0.03)
    box("ApronDrawer", (mw * 0.6, 0.04, 0.18), (0, -D / 2 + 0.05, H - 0.31), M["oakdark"], bevel=0.012)
    cyl("ApronPull", 0.04, 0.1, (0, -D / 2 + 0.0, H - 0.31), M["brass"], rot=(math.pi / 2, 0, 0), verts=14)
    return (W, D, H)


def _quatrefoil(name, cx, y, cz, r, mat):
    ring(name, (cx, y, cz), r, "Y", mat, thick=0.022)
    for k, (dx, dz) in enumerate([(0, 1), (0, -1), (1, 0), (-1, 0)]):
        ring(f"{name}F{k}", (cx + dx * r * 0.55, y, cz + dz * r * 0.55), r * 0.42, "Y", mat, thick=0.016)


def _strap_hinge(name, x_from, x_to, y, z, mat):
    """Gothic iron strap hinge across the door face, ending in a pointed fleur."""
    box(name, (abs(x_to - x_from), 0.03, 0.14), ((x_from + x_to) / 2, y, z), mat, bevel=0.01)
    tip = x_to + (0.12 if x_to > x_from else -0.12)
    tube(name + "Fleur", [(x_to, y, z + 0.11), (tip, y, z), (x_to, y, z - 0.11)], 0.03, mat, poly=True)
    for k in range(4):
        xx = x_from + (x_to - x_from) * (0.15 + k * 0.25)
        cyl(f"{name}Rivet{k}", 0.026, 0.03, (xx, y - 0.018, z), mat, rot=(math.pi / 2, 0, 0), verts=8, bevel=0)


def _arch_loop(cx, yo, hw, z0, zs, za):
    """Closed pointed-arch outline: straight sides up to zs, two arcs meeting at the apex za."""
    pts = [(cx - hw, yo, z0), (cx - hw, yo, zs)]
    for tt in [i / 6 for i in range(1, 7)]:
        pts.append((cx - hw + hw * math.sin(tt * math.pi / 2) ** 0.9, yo, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    for tt in [i / 6 for i in range(5, -1, -1)]:
        pts.append((cx + hw - hw * math.sin(tt * math.pi / 2) ** 0.9, yo, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    pts.append((cx + hw, yo, z0))
    return pts


def locker(M, double=False):
    """Hallway locker 1.9 W x 7 H x 1.4 D (or a 3 x 7 x 3 double 'hiding' locker).
    Rigged: the body and each door are separate meshes; each door's origin sits on its hinge line
    (Controllers.World.LockerDoors swings them in Roblox). Crimson enamel steel, iron cornice and plinth,
    a real interior (shelf, hook, books, scarf), raised door panels with a pointed arch, a quatrefoil vent,
    a louvred vent, strap hinges, a lift latch with a hanging padlock, a nameplate holder and a number plate."""
    W, H, D = (3.0, 7.0, 3.0) if double else (1.9, 7.0, 1.4)
    t = 0.06                 # sheet thickness
    zb, zt = 0.32, H - 0.34  # opening bottom / top
    fx = W / 2 - 0.1         # front frame inner edge (x)
    yf = -D / 2              # front plane
    inner = M["crimsonin"]

    set_group("Body")
    # carcass: sides, back, floor, roof (hollow, so the interior shows when a door opens)
    for sx in (-1, 1):
        box(f"Side{sx}", (t, D, H - 0.3), (sx * (W / 2 - t / 2), 0, (H - 0.3) / 2 + 0.3), M["crimson"], bevel=0.015)
        pts = [(sx * (W / 2 + 0.005), -D / 2 + 0.18, 0.7), (sx * (W / 2 + 0.005), D / 2 - 0.18, 0.7),
               (sx * (W / 2 + 0.005), D / 2 - 0.18, H - 0.8), (sx * (W / 2 + 0.005), -D / 2 + 0.18, H - 0.8)]
        tube(f"SidePanel{sx}", pts, 0.03, M["iron"], square=True, closed=True, poly=True)
    box("Back", (W, t, H - 0.3), (0, D / 2 - t / 2, (H - 0.3) / 2 + 0.3), inner, bevel=0.01)
    box("Floor", (W - 2 * t, D - t, t), (0, 0, zb - t / 2), inner, bevel=0.005)
    box("Roof", (W - 2 * t, D - t, t), (0, 0, zt + t / 2), inner, bevel=0.005)
    # front frame around the opening
    box("StileL", (0.1, t, zt - zb), (-W / 2 + 0.05, yf + t / 2, (zb + zt) / 2), M["crimson"], bevel=0.01)
    box("StileR", (0.1, t, zt - zb), (W / 2 - 0.05, yf + t / 2, (zb + zt) / 2), M["crimson"], bevel=0.01)
    box("RailTop", (W, t, H - zt - 0.1), (0, yf + t / 2, zt + (H - zt - 0.1) / 2), M["crimson"], bevel=0.01)
    box("RailBot", (W, t, zb - 0.25), (0, yf + t / 2, 0.25 + (zb - 0.25) / 2), M["crimson"], bevel=0.01)
    if double:
        box("Mullion", (0.08, t, zt - zb), (0, yf + t / 2, (zb + zt) / 2), M["crimson"], bevel=0.01)
    # iron plinth on four feet, and a cornice with dentils and a crenellated crest
    box("Plinth", (W + 0.08, D + 0.06, 0.16), (0, 0, 0.17), M["iron"], bevel=0.025)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Foot{sx}{sy}", (0.16, 0.16, 0.1), (sx * (W / 2 - 0.05), sy * (D / 2 - 0.05), 0.05), M["iron"], bevel=0.02)
    box("Cornice", (W + 0.16, D + 0.14, 0.12), (0, 0, H - 0.04), M["iron"], bevel=0.035, segments=3)
    box("CorniceBase", (W + 0.06, D + 0.06, 0.06), (0, 0, H - 0.13), M["iron"], bevel=0.015)
    n_dent = int(W / 0.16)
    for k in range(n_dent):
        x = -W / 2 + 0.08 + k * (W - 0.16) / max(1, n_dent - 1)
        box(f"Dentil{k}", (0.07, 0.05, 0.07), (x, yf - 0.06, H - 0.17), M["iron"], bevel=0.008)
    n_cren = int(W / 0.38)
    for k in range(n_cren):
        x = -W / 2 + 0.16 + k * (W - 0.32) / max(1, n_cren - 1)
        for sy in (-1, 1):
            box(f"Merlon{k}{sy}", (0.16, 0.14, 0.16), (x, sy * (D / 2 + 0.0), H + 0.1), M["iron"], bevel=0.02)
    # interior: shelf, books, coat hook with a scarf
    box("Shelf", (W - 2 * t - 0.02, D - 0.12, 0.04), (0, 0.04, zt - 0.95), inner, bevel=0.008)
    for k, (x, h, c) in enumerate([(-W * 0.22, 0.42, M["oakdark"]), (-W * 0.22 + 0.13, 0.36, M["leather"]), (-W * 0.22 + 0.25, 0.4, M["oak"])]):
        box(f"Book{k}", (0.11, 0.6, h), (x, 0.1, zt - 0.93 + h / 2), c, bevel=0.012)
    hook_x = 0.0 if not double else -W / 4
    box("HookPlate", (0.12, 0.02, 0.18), (hook_x, D / 2 - t - 0.01, zt - 1.6), M["brass"], bevel=0.006)
    tube("Hook", [(hook_x, D / 2 - t - 0.02, zt - 1.55), (hook_x, D / 2 - t - 0.25, zt - 1.62), (hook_x, D / 2 - t - 0.28, zt - 1.48)], 0.025, M["brass"])
    box("Scarf", (0.22, 0.04, 1.2), (hook_x, D / 2 - t - 0.27, zt - 2.15), M["leather"], bevel=0.02)

    # doors
    doors = 2 if double else 1
    gap = 0.02
    mull = 0.08 if double else 0.0
    span = (2 * fx - mull) / doors
    for k in range(doors):
        left = (k == 0)
        x0 = -fx + k * (span + mull)   # door left edge
        x1 = x0 + span                 # door right edge
        hinge_x = x0 if left else x1
        set_group(f"Door{k}", hinge=(hinge_x, yf - 0.03, (zb + zt) / 2), swing=-1 if left else 1)
        cx = (x0 + x1) / 2
        dw = span - 2 * gap
        dh = zt - zb - 2 * gap
        yd = yf - 0.03
        box(f"Slab{k}", (dw, 0.05, dh), (cx, yd, (zb + zt) / 2), M["crimson"], bevel=0.015)
        yo = yd - 0.03
        # raised lower panel, and a double-moulded pointed arch above
        lo = [(cx - dw * 0.36, yo, zb + 0.35), (cx + dw * 0.36, yo, zb + 0.35), (cx + dw * 0.36, yo, zb + 1.65), (cx - dw * 0.36, yo, zb + 1.65)]
        tube(f"LowPanel{k}", lo, 0.032, M["iron"], square=True, closed=True, poly=True)
        for n, (inset, rr) in enumerate(((0.0, 0.032), (0.1, 0.018))):
            hw = dw * 0.36 - inset
            tube(f"Arch{k}{n}", _arch_loop(cx, yo, hw, zb + 2.0 + inset, zt - 1.75, zt - 0.95 - inset), rr, M["iron"], square=True, closed=True, poly=True)
        # quatrefoil vent inside the arch
        box(f"QuatroBack{k}", (0.5, 0.01, 0.5), (cx, yd - 0.026, zt - 1.45), M["iron"], bevel=0.005)
        _quatrefoil(f"Quatro{k}", cx, yo, zt - 1.45, 0.2, M["brass"])
        # louvred vent near the top
        box(f"VentFrame{k}", (dw * 0.66, 0.05, 0.62), (cx, yd - 0.02, zt - 0.45), M["iron"], bevel=0.012)
        for j in range(6):
            box(f"Louvre{k}{j}", (dw * 0.6, 0.06, 0.045), (cx, yd - 0.05, zt - 0.22 - j * 0.09), M["crimson"], bevel=0.01, rot=(math.radians(-38), 0, 0))
        # nameplate holder with a card, and a brass number plate
        box(f"CardHolder{k}", (dw * 0.42, 0.025, 0.2), (cx, yo - 0.005, zb + 1.85), M["brass"], bevel=0.008)
        box(f"Card{k}", (dw * 0.36, 0.01, 0.14), (cx, yo - 0.02, zb + 1.85), M["chalk"], bevel=0.003)
        box(f"Number{k}", (0.3, 0.02, 0.16), (cx, yo - 0.005, zt - 0.88), M["brass"], bevel=0.008)
        # strap hinges from the hinge side, with knuckles on the hinge line
        hs = x0 + 0.05 if left else x1 - 0.05
        he = x0 + dw * 0.55 if left else x1 - dw * 0.55
        for zz in (zb + 0.9, zt - 0.6):
            _strap_hinge(f"Strap{k}{zz:.0f}", hs, he, yo, zz, M["iron"])
            cyl(f"Knuckle{k}{zz:.0f}", 0.055, 0.42, (hinge_x, yd - 0.01, zz), M["iron"], verts=12)
        # lift latch on the opening side; the last door carries a hasp and a hanging padlock
        lx = x1 - 0.2 if left else x0 + 0.2
        lz = zb + 2.55
        box(f"LatchPlate{k}", (0.13, 0.025, 0.5), (lx, yo, lz), M["brass"], bevel=0.01)
        tube(f"Latch{k}", [(lx, yo - 0.02, lz - 0.16), (lx, yo - 0.16, lz - 0.05), (lx, yo - 0.16, lz + 0.1), (lx, yo - 0.02, lz + 0.2)], 0.022, M["brass"])
        if k == doors - 1:
            box(f"Hasp{k}", (0.07, 0.03, 0.22), (lx, yo - 0.02, lz - 0.42), M["iron"], bevel=0.008)
            box(f"LockBody{k}", (0.16, 0.07, 0.18), (lx, yo - 0.08, lz - 0.62), M["brass"], bevel=0.03, segments=3)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.014, location=(lx, yo - 0.08, lz - 0.51), rotation=(math.pi / 2, 0, 0))
            sh = bpy.context.active_object
            sh.name = f"Shackle{k}"
            _finish(sh, M["iron"], 0)
        # rivets along the opening edge
        ex = x1 - 0.06 if left else x0 + 0.06
        for j in range(7):
            zz = zb + 0.3 + j * (dh - 0.6) / 6
            cyl(f"Rivet{k}{j}", 0.026, 0.03, (ex, yd - 0.028, zz), M["iron"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0)
    set_group("Main")
    return (W + 0.16, D + 0.14, H + 0.14)


# ------------------------------------------------------------------ batch 2: chairs, lounge, vending, bin, altar, shelf, candelabra

def _legs4(prefix, w, d, h, r, mat, splay=0.0, square=True):
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * w / 2, sy * d / 2
            tube(f"{prefix}{sx}{sy}", [(x + sx * splay, y + sy * splay, 0.03), (x, y, h)], r, mat, square=square, poly=True)


def student_chair(M):
    """1.6 W x 1.6 D x 3.2 H: wrought-iron frame, oak seat and back panel, a pointed-arch iron back."""
    W, D, SH = 1.4, 1.3, 1.5
    _legs4("Leg", W - 0.1, D - 0.1, SH - 0.05, 0.04, M["iron"], splay=0.05)
    for sy in (-1, 1):
        tube(f"SideRail{sy}", [(-(W - 0.1) / 2, sy * (D - 0.1) / 2, 0.45), ((W - 0.1) / 2, sy * (D - 0.1) / 2, 0.45)], 0.025, M["iron"], poly=True)
    for sx in (-1, 1):
        tube(f"Stretch{sx}", [(sx * (W - 0.1) / 2, -(D - 0.1) / 2, 0.45), (sx * (W - 0.1) / 2, (D - 0.1) / 2, 0.45)], 0.025, M["iron"], poly=True)
    box("Seat", (W, D, 0.09), (0, 0, SH), M["oak"], bevel=0.025, segments=1)
    by = (D - 0.1) / 2
    for sx in (-1, 1):
        tube(f"Upright{sx}", [(sx * (W - 0.14) / 2, by, SH), (sx * (W - 0.14) / 2, by + 0.12, 3.1)], 0.035, M["iron"], square=True, poly=True)
    box("BackPanel", (W - 0.1, 0.07, 0.5), (0, by + 0.1, 2.75), M["oak"], bevel=0.02, segments=1, rot=(math.radians(-8), 0, 0))
    arch = [(-0.42, by + 0.05, SH + 0.1), (-0.42, by + 0.07, 2.2), (0, by + 0.08, 2.45), (0.42, by + 0.07, 2.2), (0.42, by + 0.05, SH + 0.1)]
    tube("BackArch", arch, 0.022, M["iron"], poly=True)
    return (W, D, 3.1)


def teacher_chair(M):
    """2.2 W x 2.1 D x 4.6 H: carved oak high-back armchair, crimson leather seat, lancet back, pointed crest."""
    W, D, SH = 2.0, 1.9, 1.55
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Leg{sx}{sy}", 0.09, SH - 0.1, (sx * (W / 2 - 0.12), sy * (D / 2 - 0.12), (SH - 0.1) / 2), M["oakdark"], verts=12)
            cyl(f"Foot{sx}{sy}", 0.12, 0.08, (sx * (W / 2 - 0.12), sy * (D / 2 - 0.12), 0.04), M["oakdark"], verts=12)
    box("SeatFrame", (W, D, 0.16), (0, 0, SH - 0.05), M["oak"], bevel=0.04, segments=2)
    box("Cushion", (W - 0.25, D - 0.3, 0.14), (0, -0.05, SH + 0.1), M["leather"], bevel=0.06, segments=3)
    by = D / 2 - 0.1
    box("BackFrameL", (0.14, 0.16, 2.9), (-W / 2 + 0.1, by, SH + 1.45), M["oak"], bevel=0.03)
    box("BackFrameR", (0.14, 0.16, 2.9), (W / 2 - 0.1, by, SH + 1.45), M["oak"], bevel=0.03)
    box("BackRail", (W - 0.2, 0.14, 0.16), (0, by, SH + 0.35), M["oak"], bevel=0.03)
    box("BackLeather", (W - 0.36, 0.06, 1.5), (0, by - 0.02, SH + 1.35), M["leather"], bevel=0.04, segments=2)
    for k, x in enumerate((-0.45, 0, 0.45)):
        tube(f"Lancet{k}", [(x - 0.14, by - 0.06, SH + 2.15), (x - 0.14, by - 0.06, SH + 2.55), (x, by - 0.06, SH + 2.8), (x + 0.14, by - 0.06, SH + 2.55), (x + 0.14, by - 0.06, SH + 2.15)], 0.035, M["oak"], square=True, poly=True)
    crest = [(-W / 2 + 0.1, by, SH + 2.9), (-0.5, by, SH + 3.0), (0, by, SH + 3.3), (0.5, by, SH + 3.0), (W / 2 - 0.1, by, SH + 2.9)]
    tube("Crest", crest, 0.07, M["oak"], square=True)
    cyl("Finial", 0.08, 0.25, (0, by, SH + 3.42), M["brass"], verts=10)
    for sx in (-1, 1):
        box(f"Arm{sx}", (0.18, D - 0.2, 0.12), (sx * (W / 2 - 0.05), -0.05, SH + 0.85), M["oak"], bevel=0.04)
        cyl(f"ArmPost{sx}", 0.06, 0.8, (sx * (W / 2 - 0.08), -D / 2 + 0.2, SH + 0.45), M["oakdark"], verts=10)
        cyl(f"Scroll{sx}", 0.1, 0.2, (sx * (W / 2 - 0.05), -D / 2 + 0.12, SH + 0.85), M["oak"], rot=(0, math.pi / 2, 0), verts=12)
    return (W + 0.1, D, SH + 3.55)


def _tufts(prefix, x0, x1, z0, z1, y, nx, nz, mat):
    for i in range(nx):
        for j in range(nz):
            x = x0 + (x1 - x0) * (i + 0.5) / nx + (0.5 * (x1 - x0) / nx if j % 2 else 0) * 0.0
            z = z0 + (z1 - z0) * (j + 0.5) / nz
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.035, location=(x, y, z))
            b = bpy.context.active_object
            b.name = f"{prefix}{i}{j}"
            _finish(b, mat, 0)


def armchair(M):
    """2.9 W x 2.7 D x 3.9 H: crimson leather wingback for the staff room, tufted back, rolled arms, oak bun feet."""
    W, D, SH = 2.7, 2.5, 1.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Bun{sx}{sy}", 0.12, 0.3, (sx * (W / 2 - 0.25), sy * (D / 2 - 0.25), 0.15), M["oakdark"], verts=12)
    box("Base", (W - 0.2, D - 0.1, 0.95), (0, 0, 0.3 + 0.475), M["leatherdark"], bevel=0.08, segments=3)
    box("Seat", (W - 0.9, D - 0.5, 0.35), (0, -0.15, SH - 0.05), M["leather"], bevel=0.12, segments=3)
    by = D / 2 - 0.25
    box("Back", (W - 0.6, 0.45, 2.3), (0, by, SH + 1.0), M["leather"], bevel=0.14, segments=3)
    _tufts("TuftB", -(W - 0.9) / 2, (W - 0.9) / 2, SH + 0.5, SH + 1.9, by - 0.23, 4, 4, M["leatherdark"])
    for sx in (-1, 1):
        box(f"Wing{sx}", (0.35, D - 0.6, 1.4), (sx * (W / 2 - 0.25), 0.1, SH + 1.25), M["leather"], bevel=0.12, segments=3)
        box(f"ArmBlock{sx}", (0.4, D - 0.3, 1.25), (sx * (W / 2 - 0.25), -0.05, SH - 0.1), M["leather"], bevel=0.1, segments=3)
        cyl(f"Roll{sx}", 0.24, D - 0.4, (sx * (W / 2 - 0.22), -0.05, SH + 0.55), M["leather"], rot=(math.pi / 2, 0, 0), verts=16)
        for k in range(6):
            cyl(f"Nail{sx}{k}", 0.025, 0.02, (sx * (W / 2 - 0.22), -D / 2 + 0.2 + k * (D - 0.5) / 5, SH + 0.3), M["brass"], rot=(0, math.pi / 2, 0), verts=8, bevel=0)
    return (W, D, SH + 2.15)


def sofa(M):
    """5.4 W x 2.7 D x 3.2 H: crimson chesterfield for the staff room: rolled arms level with the back, deep tufting."""
    W, D, SH = 5.2, 2.5, 1.4
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            if sx == 0 and sy == 1:
                continue
            cyl(f"Bun{sx}{sy}", 0.11, 0.28, (sx * (W / 2 - 0.3), sy * (D / 2 - 0.25), 0.14), M["oakdark"], verts=12)
    box("Base", (W - 0.2, D - 0.1, 0.95), (0, 0, 0.3 + 0.475), M["leatherdark"], bevel=0.08, segments=3)
    for k, x in enumerate((-(W - 1.2) / 4, (W - 1.2) / 4)):
        box(f"Cushion{k}", ((W - 1.2) / 2 - 0.05, D - 0.6, 0.35), (x, -0.15, SH - 0.05), M["leather"], bevel=0.12, segments=3)
    by = D / 2 - 0.25
    box("Back", (W - 0.3, 0.45, 1.45), (0, by, SH + 0.45), M["leather"], bevel=0.14, segments=3)
    cyl("BackRoll", 0.22, W - 0.4, (0, by - 0.02, SH + 1.18), M["leather"], rot=(0, math.pi / 2, 0), verts=16)
    _tufts("TuftB", -(W - 0.8) / 2, (W - 0.8) / 2, SH + 0.25, SH + 1.0, by - 0.23, 8, 2, M["leatherdark"])
    for sx in (-1, 1):
        box(f"ArmBlock{sx}", (0.42, D - 0.2, 1.5), (sx * (W / 2 - 0.26), 0, SH - 0.05), M["leather"], bevel=0.1, segments=3)
        cyl(f"Roll{sx}", 0.25, D - 0.3, (sx * (W / 2 - 0.2), 0, SH + 0.75), M["leather"], rot=(math.pi / 2, 0, 0), verts=16)
    return (W, D, SH + 1.4)


def vending_machine(M):
    """3.3 W x 2.7 D x 8 H gothic vending machine, rigged for a rattle animation.
    Pieces (each its own mesh):
      Body   iron cabinet, brass trim, pointed-arch crown with the school seal, keypad, coin slot, shelves
      Wares  the bottles and snacks (jitter on their own during a rattle)
      Flap   the delivery flap; its origin is on the top hinge edge (it clacks open about the X axis)
      Glass  the display pane (Roblox: Glass material, see-through)
      Glow   the sign and shelf lights (Roblox: Neon; they flicker during a rattle)"""
    W, D, H = 3.2, 2.6, 7.0
    gw, gx = W * 0.6, -W * 0.16
    yfront = -D / 2
    set_group("Body")
    box("Cabinet", (W, D, H - 0.3), (0, 0.05, (H - 0.3) / 2 + 0.3), M["iron"], bevel=0.05, segments=2)
    box("Plinth", (W + 0.1, D + 0.1, 0.3), (0, 0.05, 0.15), M["iron"], bevel=0.04)
    for sx in (-1, 1):
        # side panels with a raised arch moulding
        tube(f"SideArch{sx}", _arch_loop_x(sx * (W / 2 + 0.01), 0.05, 0.75, 1.0, 5.2, 6.1), 0.04, M["brass"], square=True, closed=True, poly=True)
        for z in (1.2, 3.5, 5.8):
            cyl(f"SideRivet{sx}{z:.0f}", 0.04, 0.04, (sx * (W / 2 + 0.02), -D / 2 + 0.2, z), M["brass"], rot=(0, math.pi / 2, 0), verts=8, bevel=0)
    # recessed display window with a brass frame and four shelves
    box("WindowBack", (gw, 0.04, 4.6), (gx, yfront + 0.45, 3.6), M["crimsonin"], bevel=0.01)
    for sx in (-1, 1):
        box(f"WindowSide{sx}", (0.04, 0.4, 4.6), (gx + sx * gw / 2, yfront + 0.25, 3.6), M["crimsonin"], bevel=0.005)
    tube("WindowFrame", [(gx - gw / 2 - 0.05, yfront - 0.01, 1.25), (gx + gw / 2 + 0.05, yfront - 0.01, 1.25), (gx + gw / 2 + 0.05, yfront - 0.01, 5.95), (gx - gw / 2 - 0.05, yfront - 0.01, 5.95)], 0.06, M["brass"], square=True, closed=True, poly=True)
    for j in range(4):
        box(f"Shelf{j}", (gw - 0.1, 0.36, 0.05), (gx, yfront + 0.27, 1.55 + j * 1.12), M["iron"], bevel=0.01)
        for i in range(5):
            tube(f"Coil{j}{i}", [(gx - gw / 2 + 0.2 + i * (gw - 0.4) / 4 + 0.1 * math.cos(t * 2.4), yfront + 0.3 + 0.12 * (t / 4), 1.62 + j * 1.12 + 0.1 * math.sin(t * 2.4)) for t in range(5)], 0.012, M["brass"])
    # control column
    cxp = W * 0.33
    box("Panel", (W * 0.26, 0.06, 4.2), (cxp, yfront - 0.01, 3.7), M["iron"], bevel=0.02)
    box("DisplayBezel", (0.7, 0.04, 0.38), (cxp, yfront - 0.04, 5.2), M["brass"], bevel=0.015)
    box("Display", (0.6, 0.03, 0.3), (cxp, yfront - 0.06, 5.2), M["inkblue"], bevel=0.01)
    for r in range(4):
        for c2 in range(3):
            box(f"Key{r}{c2}", (0.13, 0.04, 0.11), (cxp - 0.18 + c2 * 0.18, yfront - 0.06, 4.6 - r * 0.17), M["brass"], bevel=0.012, segments=1)
    box("CoinPlate", (0.32, 0.03, 0.42), (cxp, yfront - 0.05, 3.65), M["brass"], bevel=0.015)
    box("CoinSlot", (0.05, 0.02, 0.2), (cxp, yfront - 0.07, 3.7), M["iron"], bevel=0.005)
    box("ReturnCup", (0.4, 0.15, 0.25), (cxp, yfront - 0.06, 3.0), M["iron"], bevel=0.03)
    box("Lever", (0.06, 0.25, 0.06), (cxp + 0.25, yfront - 0.15, 4.0), M["brass"], bevel=0.015)
    box("FlapHole", (gw * 0.72, 0.05, 0.64), (gx, yfront + 0.0, 0.75), M["crimsonin"], bevel=0.01)
    box("FlapTrim", (gw * 0.76, 0.03, 0.08), (gx, yfront - 0.05, 1.11), M["brass"], bevel=0.01)
    # crown: pointed arch, quatrefoil seal and pinnacles
    box("Crown", (W + 0.15, D + 0.15, 0.2), (0, 0.05, H), M["iron"], bevel=0.05, segments=2)
    crest = [(-W / 2, yfront - 0.02, H + 0.1), (-0.8, yfront - 0.02, H + 0.45), (0, yfront - 0.02, H + 0.95), (0.8, yfront - 0.02, H + 0.45), (W / 2, yfront - 0.02, H + 0.1)]
    tube("CrownArch", crest, 0.08, M["iron"], square=True)
    _quatrefoil("Seal", 0, yfront - 0.08, H + 0.45, 0.2, M["brass"])
    for sx in (-1, 1):
        cyl(f"Pinnacle{sx}", 0.09, 0.6, (sx * (W / 2 - 0.05), yfront + 0.05, H + 0.35), M["iron"], verts=8)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.11, radius2=0.0, depth=0.35, location=(sx * (W / 2 - 0.05), yfront + 0.05, H + 0.82))
        c = bpy.context.active_object
        c.name = f"Spire{sx}"
        _finish(c, M["brass"], 0)

    set_group("Wares")
    for j in range(4):
        z = 1.55 + j * 1.12
        for i in range(5):
            x = gx - gw / 2 + 0.2 + i * (gw - 0.4) / 4
            if (i + j) % 2 == 0:
                c = [M["crimson"], M["glassamber"], M["inkblue"], M["glassamber"]][j]
                cyl(f"Bottle{j}{i}", 0.1, 0.55, (x, yfront + 0.3, z + 0.3), c, verts=10)
                cyl(f"Neck{j}{i}", 0.04, 0.18, (x, yfront + 0.3, z + 0.66), c, verts=8, bevel=0)
                cyl(f"Cap{j}{i}", 0.045, 0.04, (x, yfront + 0.3, z + 0.77), M["brass"], verts=8, bevel=0)
            else:
                c = [M["paper"], M["leather"], M["oak"], M["paper"]][j]
                box(f"Snack{j}{i}", (0.26, 0.12, 0.42), (x, yfront + 0.32, z + 0.24), c, bevel=0.015, segments=1)

    set_group("Flap", hinge=(gx, yfront - 0.03, 1.07), swing=1)
    box("FlapDoor", (gw * 0.7, 0.05, 0.6), (gx, yfront - 0.03, 0.77), M["iron"], bevel=0.02)
    box("FlapHandle", (0.4, 0.05, 0.05), (gx, yfront - 0.07, 0.55), M["brass"], bevel=0.015)

    set_group("Glass")
    box("GlassPane", (gw, 0.03, 4.6), (gx, yfront + 0.03, 3.6), M["glassclear"], bevel=0.005)
    set_group("Glow")
    box("Sign", (W * 0.8, 0.04, 0.45), (0, yfront - 0.03, 6.45), M["paper"], bevel=0.01)
    for j in range(4):
        box(f"ShelfLight{j}", (gw - 0.2, 0.03, 0.03), (gx, yfront + 0.43, 1.55 + j * 1.12 + 0.9), M["paper"], bevel=0.0)
    set_group("Main")
    return (W + 0.15, D + 0.15, H + 1.0)


def _arch_loop_x(x, cy, hw, z0, zs, za):
    """Pointed-arch outline in the YZ plane (on a side face at x), centred on y = cy."""
    pts = [(x, cy - hw, z0), (x, cy - hw, zs)]
    for tt in [i / 6 for i in range(1, 7)]:
        pts.append((x, cy - hw + hw * math.sin(tt * math.pi / 2) ** 0.9, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    for tt in [i / 6 for i in range(5, -1, -1)]:
        pts.append((x, cy + hw - hw * math.sin(tt * math.pi / 2) ** 0.9, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    pts.append((x, cy + hw, z0))
    return pts


def _column(prefix, x, y, z0, z1, r, mat, cap_mat=None):
    """Clustered gothic column: three shafts with a moulded base and capital."""
    cap_mat = cap_mat or mat
    for k, (dx, dy) in enumerate([(0, -r * 0.9), (-r * 0.8, r * 0.5), (r * 0.8, r * 0.5)]):
        cyl(f"{prefix}Shaft{k}", r * 0.55, z1 - z0 - 0.5, (x + dx, y + dy, (z0 + z1) / 2), mat, verts=10, bevel=0.005)
    cyl(f"{prefix}Base", r * 1.7, 0.18, (x, y, z0 + 0.09), mat, verts=12, bevel=0.03)
    cyl(f"{prefix}Base2", r * 1.45, 0.1, (x, y, z0 + 0.23), mat, verts=12, bevel=0.02)
    cyl(f"{prefix}Cap", r * 1.75, 0.16, (x, y, z1 - 0.08), cap_mat, verts=12, bevel=0.03)
    cyl(f"{prefix}Cap2", r * 1.4, 0.1, (x, y, z1 - 0.21), cap_mat, verts=12, bevel=0.02)


def _pinnacle(prefix, x, y, z, h, mat):
    """Crocketed pinnacle: square shaft, spire and little leaf crockets."""
    box(f"{prefix}Shaft", (0.28, 0.28, h * 0.45), (x, y, z + h * 0.225), mat, bevel=0.03)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.24, radius2=0.0, depth=h * 0.55, location=(x, y, z + h * 0.45 + h * 0.275), rotation=(0, 0, math.pi / 4))
    c = bpy.context.active_object
    c.name = f"{prefix}Spire"
    _finish(c, mat, 0.01)
    for k in range(3):
        zz = z + h * 0.55 + k * h * 0.13
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=3, radius=0.05, location=(x + sx * (0.17 - k * 0.04), y + sy * (0.17 - k * 0.04), zz))
            b = bpy.context.active_object
            b.name = f"{prefix}Crocket{k}{sx}{sy}"
            _finish(b, mat, 0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.08, location=(x, y, z + h + 0.04))
    f = bpy.context.active_object
    f.name = f"{prefix}Finial"
    _finish(f, mat, 0)


def _candlestick(prefix, x, y, z, h, mat):
    """Ornate brass candlestick: stepped foot, knopped stem, drip pan."""
    cyl(f"{prefix}Foot", 0.26, 0.06, (x, y, z + 0.03), mat, verts=16)
    cyl(f"{prefix}Foot2", 0.18, 0.08, (x, y, z + 0.1), mat, verts=16)
    cyl(f"{prefix}Stem", 0.045, h, (x, y, z + 0.14 + h / 2), mat, verts=10)
    for k, f in enumerate((0.3, 0.65)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=0.09, location=(x, y, z + 0.14 + h * f))
        b = bpy.context.active_object
        b.name = f"{prefix}Knop{k}"
        _finish(b, mat, 0)
    cyl(f"{prefix}Pan", 0.15, 0.04, (x, y, z + 0.16 + h), mat, verts=16)
    return z + 0.18 + h


def altar(M):
    """6.8 W x 3.6 D x 9.8 H: a carved stone altar with its reredos. Front: clustered corner columns,
    five trefoil-headed lancets with shafts, a carved rose in the centre, an inscription band, an ogee mensa.
    Behind: a stone reredos with three niches (a crimson-lit window in the centre), crocketed pinnacles and a
    traceried gable. On it: a gold-trimmed crimson cloth with tassels, two ornate candlesticks, a cluster of
    candles, a brass chalice, an open grimoire on a stand and a ritual dagger.
    Pieces: Altar; Glow (candle flames and the crimson window: Neon + light in Roblox)."""
    W, D, H = 6.0, 2.6, 3.3
    set_group("Altar")
    # three steps
    for k, (w, d, h) in enumerate([(W + 1.0, D + 1.2, 0.2), (W + 0.6, D + 0.8, 0.2), (W + 0.25, D + 0.4, 0.2)]):
        box(f"Step{k}", (w, d, h), (0, 0.05, 0.1 + k * 0.2), M["stone"], bevel=0.035)
    z0 = 0.6
    box("Block", (W - 0.5, D - 0.5, H - z0 - 0.35), (0, 0, z0 + (H - z0 - 0.35) / 2), M["stone"], bevel=0.02)
    # clustered corner columns
    for sx in (-1, 1):
        for sy in (-1, 1):
            _column(f"Col{sx}{sy}", sx * (W / 2 - 0.3), sy * (D / 2 - 0.3), z0, H - 0.35, 0.16, M["stone"], M["stonedark"])
    # front: five trefoil-headed lancets with inner shafts, a rose in the middle
    yf = -(D - 0.5) / 2 - 0.02
    for k in range(5):
        if k == 2:
            continue
        x = -W / 2 + 1.05 + k * (W - 2.1) / 4
        tube(f"Lancet{k}", _arch_loop(x, yf, 0.3, z0 + 0.25, H - 1.3, H - 0.75), 0.045, M["stonedark"], square=True, closed=True, poly=True)
        for t, (dx, dz) in enumerate([(0, H - 1.0), (-0.12, H - 1.15), (0.12, H - 1.15)]):
            bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=6, major_radius=0.08, minor_radius=0.018, location=(x + dx, yf - 0.02, dz), rotation=(math.pi / 2, 0, 0))
            tr = bpy.context.active_object
            tr.name = f"Trefoil{k}{t}"
            _finish(tr, M["stonedark"], 0)
        cyl(f"Shaft{k}", 0.035, H - 1.6 - z0, (x, yf - 0.03, z0 + 0.3 + (H - 1.6 - z0) / 2), M["stone"], verts=8, bevel=0)
        box(f"Recess{k}", (0.5, 0.02, H - 1.4 - z0), (x, yf + 0.03, z0 + 0.25 + (H - 1.4 - z0) / 2), M["stonedark"], bevel=0.005)
    # carved rose window relief in the centre
    rc = (0, yf - 0.02, z0 + (H - 0.35 - z0) / 2 + 0.1)
    ring("RoseOuter", rc, 0.62, "Y", M["stonedark"], thick=0.05)
    ring("RoseInner", rc, 0.22, "Y", M["stonedark"], thick=0.035)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        tube(f"RoseSpoke{k}", [(rc[0] + math.cos(a) * 0.22, rc[1], rc[2] + math.sin(a) * 0.22), (rc[0] + math.cos(a) * 0.6, rc[1], rc[2] + math.sin(a) * 0.6)], 0.025, M["stonedark"], poly=True)
        ring(f"RosePetal{k}", (rc[0] + math.cos(a + math.pi / 8) * 0.42, rc[1] - 0.01, rc[2] + math.sin(a + math.pi / 8) * 0.42), 0.09, "Y", M["stonedark"], thick=0.018)
    cyl("RoseBoss", 0.11, 0.08, (rc[0], rc[1] - 0.03, rc[2]), M["brass"], rot=(math.pi / 2, 0, 0), verts=12)
    # inscription band (raised glyphs) under the mensa
    box("Band", (W - 0.4, 0.08, 0.22), (0, yf - 0.02, H - 0.48), M["stonedark"], bevel=0.015)
    import random
    rnd = random.Random(13)
    x = -W / 2 + 0.45
    while x < W / 2 - 0.45:
        w = rnd.uniform(0.04, 0.09)
        box(f"Glyph{x:.2f}", (w, 0.03, rnd.uniform(0.08, 0.13)), (x, yf - 0.07, H - 0.48), M["stone"], bevel=0.004, segments=1)
        x += w + rnd.uniform(0.03, 0.07) + (0.14 if rnd.random() < 0.12 else 0)
    # ogee-moulded mensa
    box("MensaLow", (W - 0.2, D - 0.2, 0.1), (0, 0, H - 0.3), M["stone"], bevel=0.04, segments=2)
    box("Mensa", (W + 0.3, D + 0.15, 0.22), (0, 0, H - 0.12), M["stone"], bevel=0.06, segments=3)
    for k in range(5):
        cyl(f"Consecration{k}", 0.05, 0.01, (-2.4 + k * 1.2 if k != 2 else 0, -0.6, H + 0.0), M["stonedark"], verts=10, bevel=0)

    # reredos behind the altar (its own mesh: one altar would pass Roblox's 20k-triangle limit)
    set_group("Reredos")
    yb = D / 2 + 0.25
    RW, RH = W + 0.4, 9.2
    box("Reredos", (RW, 0.45, RH - H), (0, yb, H + (RH - H) / 2 - 0.3), M["stone"], bevel=0.04)
    for k, (x, w, top) in enumerate([(-2.05, 1.1, 6.6), (0, 1.5, 7.9), (2.05, 1.1, 6.6)]):
        box(f"Niche{k}", (w, 0.12, top - H - 0.4), (x, yb - 0.2, H + 0.2 + (top - H - 0.4) / 2 - 0.3), M["stonedark"], bevel=0.02)
        tube(f"NicheArch{k}", _arch_loop(x, yb - 0.27, w / 2 + 0.06, H - 0.1, top - 1.0, top - 0.1), 0.07, M["stone"], square=True, closed=True, poly=True)
        for sx in (-1, 1):
            cyl(f"NicheShaft{k}{sx}", 0.06, top - H - 1.2, (x + sx * (w / 2 + 0.06), yb - 0.3, H - 0.1 + (top - H - 1.2) / 2), M["stone"], verts=8)
    # statue plinths in the side niches, carved figures as simple hooded forms
    for k, x in enumerate((-2.05, 2.05)):
        box(f"Plinth{k}", (0.6, 0.35, 0.25), (x, yb - 0.3, H + 0.3), M["stone"], bevel=0.03)
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.32, radius2=0.12, depth=1.6, location=(x, yb - 0.32, H + 1.25))
        robe = bpy.context.active_object
        robe.name = f"Robe{k}"
        _finish(robe, M["stone"], 0.02)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.17, location=(x, yb - 0.34, H + 2.15))
        hood = bpy.context.active_object
        hood.name = f"Hood{k}"
        _finish(hood, M["stone"], 0)
    # gable with tracery and pinnacles
    gable = [(-RW / 2, yb - 0.05, RH - 0.3), (-1.5, yb - 0.05, RH + 0.7), (0, yb - 0.05, RH + 1.5), (1.5, yb - 0.05, RH + 0.7), (RW / 2, yb - 0.05, RH - 0.3)]
    tube("Gable", gable, 0.12, M["stone"], square=True)
    _quatrefoil("GableRose", 0, yb - 0.25, RH + 0.45, 0.32, M["stonedark"])
    for k, x in enumerate((-RW / 2, -1.0, 1.0, RW / 2)):
        _pinnacle(f"Pin{k}", x, yb - 0.1, RH - 0.4 if abs(x) > 2 else RH - 0.1, 1.6 if abs(x) > 2 else 1.1, M["stone"])
    box("ReredosCornice", (RW + 0.2, 0.6, 0.16), (0, yb, RH - 0.38), M["stone"], bevel=0.04)

    set_group("Altar")
    # altar cloth: top, front fall with gold trim, tassels
    box("ClothTop", (1.6, D + 0.2, 0.025), (0, 0, H + 0.015), M["leather"], bevel=0.006)
    box("ClothFront", (1.6, 0.025, 1.25), (0, -(D + 0.15) / 2 - 0.02, H - 0.6), M["leather"], bevel=0.006)
    box("ClothTrim", (1.62, 0.035, 0.08), (0, -(D + 0.15) / 2 - 0.03, H - 1.2), M["brass"], bevel=0.008)
    tube("ClothCross", [(0, -(D + 0.15) / 2 - 0.035, H - 0.35), (0, -(D + 0.15) / 2 - 0.035, H - 1.0)], 0.02, M["brass"], poly=True)
    tube("ClothCrossBar", [(-0.18, -(D + 0.15) / 2 - 0.035, H - 0.55), (0.18, -(D + 0.15) / 2 - 0.035, H - 0.55)], 0.02, M["brass"], poly=True)
    for k in range(7):
        x = -0.72 + k * 0.24
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.035, radius2=0.012, depth=0.14, location=(x, -(D + 0.15) / 2 - 0.03, H - 1.3), rotation=(math.pi, 0, 0))
        t = bpy.context.active_object
        t.name = f"Tassel{k}"
        _finish(t, M["brass"], 0)

    # candles, chalice, grimoire, dagger (their own mesh)
    set_group("Items")
    flames = []
    for k, x in enumerate((-2.5, 2.5)):
        top = _candlestick(f"Stick{k}", x, 0.4, H, 1.1, M["brass"])
        cyl(f"TallCandle{k}", 0.07, 0.75, (x, 0.4, top + 0.375), M["chalk"], verts=12)
        flames.append((x, 0.4, top + 0.75))
    for k, (x, y, h) in enumerate([(-1.6, 0.6, 0.55), (-1.35, 0.35, 0.35), (-1.85, 0.3, 0.45), (1.55, 0.55, 0.4)]):
        cyl(f"Stub{k}", 0.065, h, (x, y, H + h / 2), M["chalk"], verts=10)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.07, location=(x, y, H + 0.02))
        drip = bpy.context.active_object
        drip.name = f"Drip{k}"
        drip.scale = (1.4, 1.4, 0.35)
        _finish(drip, M["chalk"], 0)
        flames.append((x, y, H + h))
    cyl("ChaliceFoot", 0.2, 0.05, (1.05, 0.1, H + 0.03), M["brass"], verts=16)
    cyl("ChaliceStem", 0.045, 0.38, (1.05, 0.1, H + 0.24), M["brass"], verts=10)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=0.08, location=(1.05, 0.1, H + 0.3))
    kn = bpy.context.active_object
    kn.name = "ChaliceKnop"
    _finish(kn, M["brass"], 0)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.07, radius2=0.2, depth=0.32, location=(1.05, 0.1, H + 0.58))
    cup = bpy.context.active_object
    cup.name = "ChaliceCup"
    _finish(cup, M["brass"], 0.01)
    # grimoire on a slanted brass stand
    gx, gy = -0.05, 0.25
    box("StandBase", (0.9, 0.5, 0.06), (gx, gy, H + 0.05), M["brass"], bevel=0.015)
    box("StandBack", (0.9, 0.06, 0.4), (gx, gy + 0.2, H + 0.25), M["brass"], bevel=0.015, rot=(math.radians(-30), 0, 0))
    for sx in (-1, 1):
        box(f"Cover{sx}", (0.42, 0.04, 0.6), (gx + sx * 0.22, gy + 0.05, H + 0.38), M["leatherdark"], bevel=0.015, rot=(math.radians(-58), 0, sx * math.radians(6)))
        box(f"Pages{sx}", (0.38, 0.05, 0.55), (gx + sx * 0.2, gy + 0.02, H + 0.4), M["paper"], bevel=0.01, rot=(math.radians(-58), 0, sx * math.radians(10)))
    box("Ribbon", (0.03, 0.01, 0.4), (gx, gy - 0.12, H + 0.2), M["leather"], bevel=0.0)
    # ritual dagger lying on the cloth
    box("Blade", (0.7, 0.07, 0.015), (0.35, -0.55, H + 0.04), M["brasssteel"], bevel=0.008, rot=(0, 0, math.radians(18)))
    box("Guard", (0.06, 0.26, 0.05), (-0.03, -0.67, H + 0.05), M["brass"], bevel=0.012, rot=(0, 0, math.radians(18)))
    cyl("Grip", 0.035, 0.32, (-0.2, -0.73, H + 0.05), M["leatherdark"], rot=(0, math.pi / 2, math.radians(18)), verts=8)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.05, location=(-0.36, -0.78, H + 0.05))
    pm = bpy.context.active_object
    pm.name = "Pommel"
    _finish(pm, M["brass"], 0)

    set_group("Glow")
    for k, (x, y, z) in enumerate(flames):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.05, radius2=0.0, depth=0.18, location=(x, y, z + 0.1))
        f = bpy.context.active_object
        f.name = f"Flame{k}"
        _finish(f, M["paper"], 0)
    # the crimson-lit window at the back of the centre niche
    tube("WindowGlow", _arch_loop(0, yb - 0.27, 0.62, H + 0.6, 6.6, 7.6), 0.05, M["paper"], square=True, closed=True, poly=True)
    box("WindowPane", (1.2, 0.03, 3.4), (0, yb - 0.27, H + 2.3), M["paper"], bevel=0.0)
    set_group("Main")
    return (W + 1.0, D + 1.2, RH + 1.6)


def bookshelf(M):
    """6.3 W x 1.6 D x 8.5 H oak bookcase for the archive, rigged so its books can tumble off.
    Pieces: Case (the bookcase), and every book as its own mesh (Book1, Book2, ...), each with its origin at
    its centre, so the game can drop them one by one and put them back."""
    W, D, H = 6.0, 1.4, 7.6
    set_group("Case")
    box("SideL", (0.18, D, H), (-W / 2 + 0.09, 0, H / 2), M["oak"], bevel=0.03)
    box("SideR", (0.18, D, H), (W / 2 - 0.09, 0, H / 2), M["oak"], bevel=0.03)
    for sx in (-1, 1):
        tube(f"SidePanel{sx}", [(sx * (W / 2 + 0.005), -D / 2 + 0.2, 0.6), (sx * (W / 2 + 0.005), D / 2 - 0.2, 0.6), (sx * (W / 2 + 0.005), D / 2 - 0.2, H - 0.6), (sx * (W / 2 + 0.005), -D / 2 + 0.2, H - 0.6)], 0.03, M["oakdark"], square=True, closed=True, poly=True)
    box("Back", (W - 0.2, 0.06, H - 0.2), (0, D / 2 - 0.04, H / 2), M["oakdark"], bevel=0.01)
    box("Kick", (W, D + 0.05, 0.35), (0, -0.02, 0.175), M["oakdark"], bevel=0.03)
    box("Top", (W + 0.25, D + 0.2, 0.2), (0, -0.05, H + 0.05), M["oak"], bevel=0.05, segments=2)
    crest = [(-W / 2, -D / 2, H + 0.15), (-1.2, -D / 2, H + 0.45), (0, -D / 2, H + 0.9), (1.2, -D / 2, H + 0.45), (W / 2, -D / 2, H + 0.15)]
    tube("Crest", crest, 0.08, M["oak"], square=True)
    _quatrefoil("Seal", 0, -D / 2 - 0.03, H + 0.45, 0.17, M["brass"])
    shelf_z = [0.35 + j * (H - 0.5) / 4 for j in range(4)]
    for j, z0 in enumerate(shelf_z):
        box(f"Shelf{j}", (W - 0.36, D - 0.1, 0.1), (0, 0, z0), M["oak"], bevel=0.015)
        box(f"ShelfLip{j}", (W - 0.36, 0.05, 0.12), (0, -D / 2 + 0.07, z0 + 0.02), M["oakdark"], bevel=0.012)
    import random
    rnd = random.Random(7)
    cols = [M["leather"], M["oakdark"], M["inkblue"], M["leatherdark"], M["oak"], M["paper"]]
    n = 0
    for j, z0 in enumerate(shelf_z):
        x = -W / 2 + 0.25
        while x < W / 2 - 0.45:
            w = rnd.uniform(0.13, 0.26)
            h = rnd.uniform(0.85, 1.3)
            d = rnd.uniform(0.75, 0.95)
            lean = math.radians(rnd.choice([0, 0, 0, 0, 7, -5]))
            n += 1
            set_group(f"Book{n}")
            col = rnd.choice(cols)
            box(f"Book{n}", (w, d, h), (x + w / 2, -0.05, z0 + 0.05 + h / 2), col, bevel=0.015, segments=1, rot=(0, lean, 0))
            # a gold band on the spine
            box(f"Band{n}", (w + 0.005, 0.02, 0.05), (x + w / 2, -0.05 - d / 2 - 0.005, z0 + 0.05 + h * 0.8), M["brass"], bevel=0.004, segments=1, rot=(0, lean, 0))
            x += w + rnd.uniform(0.0, 0.03)
            if rnd.random() < 0.07:
                x += rnd.uniform(0.3, 0.5)
    set_group("Main")
    return (W + 0.25, D + 0.2, H + 0.9)


def trash_can(M):
    """1.7 W x 1.7 D x 2.6 H: wrought-iron wastebasket: banded rim and base, vertical bars, a quatrefoil band,
    crumpled paper inside."""
    R, H = 0.8, 2.5
    cyl("Base", R + 0.05, 0.14, (0, 0, 0.07), M["iron"], verts=24, bevel=0.03)
    cyl("Floor", R - 0.05, 0.05, (0, 0, 0.16), M["iron"], verts=24, bevel=0.005)
    n = 16
    for k in range(n):
        a = k / n * 2 * math.pi
        x, y = math.cos(a) * R, math.sin(a) * R
        tube(f"Bar{k}", [(x * 0.94, y * 0.94, 0.1), (x, y, H - 0.05)], 0.03, M["iron"], square=True, poly=True)
    ring("Rim", (0, 0, H), R + 0.02, "Z", M["iron"], thick=0.05)
    ring("Band", (0, 0, H * 0.55), R, "Z", M["iron"], thick=0.035)
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        x, y = math.cos(a) * (R + 0.03), math.sin(a) * (R + 0.03)
        bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=6, major_radius=0.16, minor_radius=0.025, location=(x, y, H * 0.55), rotation=(math.pi / 2, 0, a + math.pi / 2))
        t = bpy.context.active_object
        t.name = f"Medallion{k}"
        _finish(t, M["brass"], 0)
    for k, (x, y, z, r) in enumerate([(0.2, 0.1, H - 0.4, 0.3), (-0.25, -0.15, H - 0.45, 0.28), (0.05, -0.3, H - 0.3, 0.22)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x, y, z))
        p = bpy.context.active_object
        p.name = f"Paper{k}"
        _finish(p, M["paper"], 0)
    return (2 * R + 0.1, 2 * R + 0.1, H + 0.05)


def candelabra(M):
    """1.6 W x 1.6 D x 6.4 H: standing iron candelabrum: tripod feet, knotted column, three arms with drip pans
    and candles. Pieces: Candelabra; Glow (flames)."""
    H = 5.2
    set_group("Candelabra")
    for k in range(3):
        a = k / 3 * 2 * math.pi
        tube(f"FootLeg{k}", [(0, 0, 0.5), (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.2), (math.cos(a) * 0.65, math.sin(a) * 0.65, 0.03)], 0.04, M["iron"])
    tube("Column", [(0, 0, 0.45), (0, 0, H - 0.3)], 0.05, M["iron"], poly=True)
    for k, z in enumerate((1.4, 2.6, 3.8)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.11, location=(0, 0, z))
        kn = bpy.context.active_object
        kn.name = f"Knot{k}"
        _finish(kn, M["iron"], 0)
    tops = []
    for k, a in enumerate((math.pi, 0)):
        x = math.cos(a) * 0.6
        tube(f"Arm{k}", [(0, 0, H - 0.6), (x * 0.5, 0, H - 0.75), (x, 0, H - 0.45)], 0.035, M["iron"])
        tops.append((x, 0, H - 0.45))
    tops.append((0, 0, H - 0.3))
    flames = []
    for k, (x, y, z) in enumerate(tops):
        cyl(f"Pan{k}", 0.14, 0.04, (x, y, z), M["brass"], verts=14)
        h = 0.55 if k < 2 else 0.7
        cyl(f"Candle{k}", 0.07, h, (x, y, z + 0.02 + h / 2), M["chalk"], verts=12)
        flames.append((x, y, z + 0.02 + h))
    set_group("Glow")
    for k, (x, y, z) in enumerate(flames):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.045, radius2=0.0, depth=0.16, location=(x, y, z + 0.09))
        f = bpy.context.active_object
        f.name = f"Flame{k}"
        _finish(f, M["paper"], 0)
    set_group("Main")
    return (1.4, 1.4, H + 0.6)


BUILD = {
    "StudentDesk": student_desk,
    "TeacherDesk": teacher_desk,
    "Chalkboard": chalkboard,
    "Locker": lambda M: locker(M, False),
    "HidingLocker": lambda M: locker(M, True),
    "StudentChair": student_chair,
    "TeacherChair": teacher_chair,
    "Armchair": armchair,
    "Sofa": sofa,
    "VendingMachine": vending_machine,
    "TrashCan": trash_can,
    "Altar": altar,
    "Bookshelf": bookshelf,
    "Candelabra": candelabra,
}


# ------------------------------------------------------------------ bake + export

def join_parts(name):
    """Join parts per group. One group -> one object named `name`; otherwise `name`_`group` each.
    Door groups get their origin on the hinge line."""
    groups = {}
    for ob in PARTS:
        groups.setdefault(ob["nh_group"], []).append(ob)
    out = []
    for g, parts in groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for ob in parts:
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            for md in list(ob.modifiers):
                bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.context.view_layer.objects.active = parts[0]
        for ob in parts:
            ob.select_set(True)
        if len(parts) > 1:
            bpy.ops.object.join()
        ob = bpy.context.active_object
        ob.name = name if len(groups) == 1 else f"{name}_{g}"
        ob.data.name = ob.name
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        if g in HINGES:
            bpy.context.scene.cursor.location = HINGES[g][0]
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
            ob["nh_swing"] = HINGES[g][1]
        out.append(ob)
    return out


def bake_uv(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        me = ob.data
        uv = me.uv_layers.new(name="Bake")
        me.uv_layers.active = uv
        uv.active_render = True
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, area_weight=0.6)
    bpy.ops.uv.pack_islands(margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_all(objs, name):
    sc = bpy.context.scene
    imgs = {}
    for kind, cs in (("color", "sRGB"), ("ao", "Non-Color"), ("normal", "Non-Color"), ("rough", "Non-Color"), ("metal", "Non-Color")):
        im = bpy.data.images.new(f"{name}_{kind}", SIZE, SIZE, alpha=False, float_buffer=False)
        im.colorspace_settings.name = cs
        imgs[kind] = im
    mats = []
    for o in objs:
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
    targets = {}
    for m in mats:
        nt = m.node_tree
        t = nt.nodes.new("ShaderNodeTexImage")
        t.name = "BakeTarget"
        t.location = (300, -500)
        targets[m.name] = t

    def set_target(kind):
        for m in mats:
            t = targets[m.name]
            t.image = imgs[kind]
            for n in m.node_tree.nodes:
                n.select = False
            t.select = True
            m.node_tree.nodes.active = t

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bk = sc.render.bake
    bk.margin = 8
    bk.use_selected_to_active = False

    def bake_input(socket_name, kind):
        """Bake one Principled input as-is by routing it through an emission shader (EMIT bake).
        Used for Base Color (a DIFFUSE colour bake returns black for metals) and Metallic."""
        sc.cycles.samples = 16
        saved = []
        for m in mats:
            nt = m.node_tree
            bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
            em = nt.nodes.new("ShaderNodeEmission")
            src = bs.inputs[socket_name]
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
            nt.links.new(old, out.inputs["Surface"])
            nt.nodes.remove(em)

    bake_input("Base Color", "color")
    sc.cycles.samples = 16
    set_target("rough")
    bpy.ops.object.bake(type="ROUGHNESS")
    set_target("normal")
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    set_target("ao")
    sc.cycles.samples = SAMPLES
    bpy.ops.object.bake(type="AO")
    bake_input("Metallic", "metal")

    # colour x ambient occlusion (soft, so corners darken without going black)
    import numpy as np
    c = np.array(imgs["color"].pixels[:], dtype=np.float32).reshape(-1, 4)
    a = np.array(imgs["ao"].pixels[:], dtype=np.float32).reshape(-1, 4)
    k = 0.35 + 0.65 * a[:, :1]
    c[:, :3] *= k
    imgs["color"].pixels[:] = c.ravel()
    for kind in ("color", "normal", "rough", "metal"):
        im = imgs[kind]
        im.filepath_raw = os.path.join(OUT_TEX, f"{name}_{kind}.png")
        im.file_format = "PNG"
        im.save()
    return imgs


def final_material(objs, name, imgs):
    m = bpy.data.materials.new(f"NH_{name}")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    def tex(kind, nonc=True):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = imgs[kind]
        return t
    nt.links.new(tex("color").outputs["Color"], bs.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex("rough").outputs["Color"], bs.inputs["Roughness"])
    nt.links.new(tex("metal").outputs["Color"], bs.inputs["Metallic"])
    for ob in objs:
        ob.data.materials.clear()
        ob.data.materials.append(m)
        # keep only the bake UV, so the export has exactly one map
        for uv in list(ob.data.uv_layers):
            if uv.name != "Bake":
                ob.data.uv_layers.remove(uv)


def export(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT_FBX, f"{name}.fbx"), use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, global_scale=1.0, axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             path_mode="STRIP", embed_textures=False)


def preview(objs, name, dims, suffix=""):
    sc = bpy.context.scene
    sc.cycles.samples = 48
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.028, 0.045, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    size = max(dims)
    def light(kind, loc, energy, color, rot=None, s=2.0):
        L = bpy.data.lights.new(kind, kind)
        L.energy = energy
        L.color = color
        if kind == "AREA":
            L.size = s
        o = bpy.data.objects.new(kind, L)
        o.location = loc
        bpy.context.collection.objects.link(o)
        d = Vector((0, 0, dims[2] * 0.4)) - Vector(loc)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    light("AREA", (size * 1.2, -size * 1.4, size * 1.3), 400 * size, (1.0, 0.82, 0.6), s=size)        # warm candle key
    light("AREA", (-size * 1.4, -size * 0.6, size * 0.9), 160 * size, (0.55, 0.55, 0.9), s=size)        # blue-violet fill
    light("AREA", (0, size * 1.5, size * 1.4), 260 * size, (0.9, 0.3, 0.35), s=size)                    # crimson rim
    bpy.ops.mesh.primitive_plane_add(size=size * 6, location=(0, 0, 0))
    fl = bpy.context.active_object
    fm = material("Floor", "NH_Boards", tint=(0.3, 0.24, 0.2), scale=0.12)
    fl.data.materials.append(fm)
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    bpy.context.collection.objects.link(co)
    co.location = (size * 1.15, -size * 1.65, dims[2] * 0.95 + size * 0.35)
    target = Vector((0, 0, dims[2] * 0.42))
    co.rotation_euler = (target - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(OUT_PRE, f"{name}{suffix}.png")
    bpy.ops.render.render(write_still=True)


def run(name):
    global PARTS, GROUP, HINGES
    PARTS, GROUP, HINGES = [], "Main", {}
    reset()
    M = palette()
    dims = BUILD[name](M)
    objs = join_parts(name)
    bake_uv(objs)
    imgs = bake_all(objs, name)
    final_material(objs, name, imgs)
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    export(objs, name)
    preview(objs, name, dims)
    doors = [o for o in objs if "nh_swing" in o.keys()]
    if doors:
        for o in doors:
            o.rotation_euler[2] = math.radians(105) * o["nh_swing"]
        sc = bpy.context.scene
        sc.render.filepath = os.path.join(OUT_PRE, f"{name}_open.png")
        bpy.ops.render.render(write_still=True)
    print(f"[props] {name}: {tris} tris, pieces {[o.name for o in objs]}, dims {dims}")


if __name__ == "__main__":
    names = list(BUILD) if PROP == "all" else [PROP]
    for n in names:
        run(n)
