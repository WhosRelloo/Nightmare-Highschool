"""Shared helpers for NH concept renders (split from injury_concepts.py): scene reset, PBR materials, BVH fitting,
sculpted patches, wraps, tubes, weight copying, the PaintRigV3 loader and the body-type swap."""

import bpy, bmesh, math, os, sys, random
from mathutils import noise as mnoise
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/ClaudeTemp/nhart/out"
QUICK = "--quick" in argv
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else ["lineup", "close"]
os.makedirs(OUT, exist_ok=True)
RIG = "E:/Blender Shit/CHARACTER SHIT/PaintRigV3.blend"
BODIES = "E:/NH-Work/bodytypes/NHBodyTypes.blend"
random.seed(7)

PARTS = {"Torso": "Torso", "RArm": "Mendula6", "LArm": "Mendula8", "RLeg": "Mendula5", "LLeg": "Left Leg", "Head": "Idarkgames9"}
BT_PART = {"Torso": "Torso", "RArm": "RightArm", "LArm": "LeftArm", "RLeg": "RightLeg", "LLeg": "LeftLeg"}
CENTRE = {"Torso": (0, 0, 3), "RArm": (1.5, 0, 3), "LArm": (-1.5, 0, 3), "RLeg": (0.5, 0, 1), "LLeg": (-0.5, 0, 1)}

# ---------------------------------------------------------------- scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
sc = bpy.context.scene


# ---------------------------------------------------------------- materials
def node_mat(name, base, rough=0.6, metal=0.0, sss=0.0, emit=None, emit_str=0.0, alpha=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.15, 0.08)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m, nt, b


def add_bump(nt, b, scale, strength, kind="noise", detail=6.0, dist=0.02):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if kind == "noise":
        t = nt.nodes.new("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        out = t.outputs["Fac"]
    else:
        t = nt.nodes.new("ShaderNodeTexWave")
        t.inputs["Scale"].default_value = scale
        t.inputs["Distortion"].default_value = 1.5
        out = t.outputs["Fac"]
    nt.links.new(tc.outputs["Object"], t.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    nt.links.new(out, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return t, bp


def gauze_mat(name="Gauze", tint=(0.93, 0.91, 0.85)):
    m, nt, b = node_mat(name, tint, rough=0.85, sss=0.15)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.wave_type = "BANDS"; w1.bands_direction = "X"; w1.inputs["Scale"].default_value = 160
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.wave_type = "BANDS"; w2.bands_direction = "Y"; w2.inputs["Scale"].default_value = 160
    for w in (w1, w2):
        w.inputs["Distortion"].default_value = 0.4
        nt.links.new(tc.outputs["UV"], w.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(w1.outputs["Fac"], mul.inputs[0]); nt.links.new(w2.outputs["Fac"], mul.inputs[1])
    crepe = nt.nodes.new("ShaderNodeTexNoise"); crepe.inputs["Scale"].default_value = 18; crepe.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], crepe.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
    nt.links.new(mul.outputs[0], add.inputs[0]); nt.links.new(crepe.outputs["Fac"], add.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.45; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(add.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    # a little age: warmer in the folds (noise -> colour ramp)
    dirt = nt.nodes.new("ShaderNodeTexNoise"); dirt.inputs["Scale"].default_value = 3.5
    nt.links.new(tc.outputs["Object"], dirt.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (tint[0] * 0.9, tint[1] * 0.86, tint[2] * 0.76, 1)
    ramp.color_ramp.elements[1].color = (*tint, 1)
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.65
    nt.links.new(dirt.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def decal_mat(name, inner, outer, softness=0.5, rough=0.6, noise_scale=9.0, emit=None, emit_str=0.0, metal=0.0):
    """Skin marks on a patch: colour and alpha from a radial gradient broken up by noise (UVs: 0..1 over the patch)."""
    m, nt, b = node_mat(name, inner, rough=rough, metal=metal, emit=emit, emit_str=emit_str)
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeVectorMath"); sep.operation = "SUBTRACT"; sep.inputs[1].default_value = (0.5, 0.5, 0)
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    nt.links.new(sep.outputs[0], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 5
    nt.links.new(tc.outputs["UV"], nz.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMath"); mix.operation = "MULTIPLY_ADD"
    nt.links.new(nz.outputs["Fac"], mix.inputs[0]); mix.inputs[1].default_value = 0.22; nt.links.new(ln.outputs["Value"], mix.inputs[2])
    a = nt.nodes.new("ShaderNodeMapRange")
    a.inputs["From Min"].default_value = 0.5; a.inputs["From Max"].default_value = 0.5 - 0.45 * softness
    nt.links.new(mix.outputs[0], a.inputs["Value"])
    nt.links.new(a.outputs["Result"], b.inputs["Alpha"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*outer, 1); ramp.color_ramp.elements[1].color = (*inner, 1)
    ramp.color_ramp.elements[0].position = 0.2; ramp.color_ramp.elements[1].position = 0.85
    nt.links.new(a.outputs["Result"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


M = {}
M["gauze"] = gauze_mat()
M["pad"] = gauze_mat("Pad", (0.97, 0.96, 0.93))
m, nt, b = node_mat("Plaster", (0.86, 0.84, 0.79), rough=0.9, sss=0.05)
add_bump(nt, b, 55, 0.35, detail=10)
M["plaster"] = m
m, nt, b = node_mat("Sling", (0.22, 0.04, 0.06), rough=0.8, sss=0.05)
add_bump(nt, b, 260, 0.25, kind="wave")
M["sling"] = m
m, nt, b = node_mat("SlingHem", (0.12, 0.02, 0.03), rough=0.75)
M["hem"] = m
m, nt, b = node_mat("Wood", (0.33, 0.2, 0.11), rough=0.55)
t, bp = add_bump(nt, b, 6, 0.25, kind="wave")
t.wave_type = "BANDS"; t.bands_direction = "Z"; t.inputs["Distortion"].default_value = 6
M["wood"] = m
m, nt, b = node_mat("Leather", (0.12, 0.07, 0.045), rough=0.45)
add_bump(nt, b, 120, 0.3)
M["leather"] = m
M["brass"] = node_mat("Brass", (0.75, 0.55, 0.25), rough=0.3, metal=1.0)[0]
M["tape"] = node_mat("Tape", (0.9, 0.86, 0.76), rough=0.65)[0]
M["thread"] = node_mat("Thread", (0.05, 0.04, 0.05), rough=0.5)[0]
M["shirt"] = node_mat("Shirt", (0.88, 0.87, 0.84), rough=0.75, sss=0.05)[0]
M["trousers"] = node_mat("Trousers", (0.06, 0.06, 0.08), rough=0.7)[0]
M["skirt"] = node_mat("Skirt", (0.18, 0.04, 0.06), rough=0.7)[0]
m, nt, b = node_mat("Ice", (0.75, 0.88, 1.0), rough=0.08)
b.inputs["Transmission Weight"].default_value = 0.85
b.inputs["IOR"].default_value = 1.31
b.inputs["Emission Color"].default_value = (0.55, 0.8, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.4
M["ice"] = m
m, nt, b = node_mat("Silver", (0.92, 0.93, 0.97), rough=0.18, metal=1.0, emit=(0.75, 0.85, 1.0), emit_str=2.5)
M["silver"] = m
M["eyes"] = node_mat("Eyes", (0.02, 0.02, 0.025), rough=0.3)[0]
M["eye_decal"] = decal_mat("EyeDecal", (0.015, 0.012, 0.015), (0.015, 0.012, 0.015), softness=0.08, rough=0.25, noise_scale=1.0)
M["bruise"] = decal_mat("Bruise", (0.28, 0.1, 0.22), (0.55, 0.45, 0.2), softness=0.8)
M["welt"] = node_mat("Welt", (0.42, 0.12, 0.14), rough=0.45, sss=0.2)[0]
M["welt_halo"] = decal_mat("WeltHalo", (0.62, 0.25, 0.25), (0.7, 0.45, 0.4), softness=0.9, noise_scale=6)
M["bite_halo"] = decal_mat("BiteHalo", (0.42, 0.14, 0.24), (0.6, 0.4, 0.42), softness=0.9)
M["puncture"] = node_mat("Puncture", (0.16, 0.03, 0.05), rough=0.35)[0]
M["frost"] = decal_mat("Frostbite", (0.78, 0.88, 0.98), (0.55, 0.62, 0.78), softness=0.7, rough=0.3, noise_scale=14,
                       emit=(0.6, 0.8, 1.0), emit_str=0.15)
M["sear"] = decal_mat("Seared", (0.16, 0.16, 0.18), (0.35, 0.37, 0.33), softness=0.85, rough=0.5, noise_scale=12)
M["scrape"] = decal_mat("Scrape", (0.58, 0.26, 0.22), (0.7, 0.45, 0.38), softness=0.6, noise_scale=30)
M["scar_line"] = node_mat("Seam", (0.38, 0.16, 0.18), rough=0.4)[0]
SKIN = {
    "A": node_mat("SkinA", (0.78, 0.56, 0.42), rough=0.5, sss=0.25)[0],
    "B": node_mat("SkinB", (0.42, 0.26, 0.17), rough=0.5, sss=0.25)[0],
    "C": node_mat("SkinC", (0.42, 0.48, 0.38), rough=0.55, sss=0.2)[0],
}


# ---------------------------------------------------------------- helpers
def link(o, coll=None):
    (coll or sc.collection).objects.link(o)
    return o


def mesh_obj(name, verts, faces, mat=None, smooth=True, uvs=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    if uvs is not None:
        uvl = me.uv_layers.new()
        for poly in me.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices):
                uvl.data[li].uv = uvs[vi]
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = link(bpy.data.objects.new(name, me))
    if mat:
        o.data.materials.append(mat)
    return o


def add_mods(o, thick=0.0, subd=1):
    if thick:
        s = o.modifiers.new("solid", "SOLIDIFY"); s.thickness = thick; s.offset = 1.0
    if subd:
        s = o.modifiers.new("sub", "SUBSURF"); s.levels = subd; s.render_levels = subd + 1
    return o


def eval_bvh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    mw = o.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys)


def surf(bvh, origin, direction):
    hit = bvh.ray_cast(origin, direction, 20)
    return hit[0], hit[1]


def ring_point(bvh, centre, d, z, off):
    o = Vector((centre[0], centre[1], z)) + d * 4
    loc, nrm = surf(bvh, o, -d)
    if loc is None:
        loc = Vector((centre[0], centre[1], z)) + d * 0.5
    return loc + d * off


def fray(v, amt):
    return v + Vector((random.uniform(-amt, amt), random.uniform(-amt, amt), random.uniform(-amt, amt)))


def gauze_wrap(name, bvh, centre, z0, z1, turns, width, off=0.025, layer=0.012, phase=0.0, mat=None, steps_per_turn=56):
    """A crepe bandage wound up a limb or torso: a helical ribbon raycast onto the real surface; each turn sits a little
    further out than the one before so the overlaps read; three verts across with a soft bulge in the middle."""
    steps = int(turns * steps_per_turn)
    verts, faces, uvs = [], [], []
    for k in range(steps + 1):
        t = k / steps
        ang = phase + 2 * math.pi * turns * t
        d = Vector((math.cos(ang), math.sin(ang), 0))
        zc = z0 + (z1 - z0) * t
        o = off + layer * turns * t
        taper = min(1.0, t * steps / 6, (1 - t) * steps / 10 + 0.35)
        w = width * taper
        for j, (dz, bulge) in enumerate(((-0.5, 0.0), (0.0, 0.006), (0.5, 0.0))):
            p = ring_point(bvh, centre, d, zc + dz * w, o + bulge)
            if j != 1:
                p = fray(p, 0.0025)
            verts.append(p)
            uvs.append((t * turns * 6.0, j * 0.5))
    for k in range(steps):
        a = k * 3
        faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    ob = mesh_obj(name, verts, faces, mat or M["gauze"], uvs=uvs)
    return add_mods(ob, thick=0.012, subd=1)


def surface_patch(name, bvh, centre, normal, up, size, mat, res=14, off=0.004, aspect=1.0, height=0.0, rough=0.0, rough_scale=8.0, subd=1):
    """A thin decal patch laid on the body: a grid in the tangent plane, each point raycast back onto the surface."""
    n = normal.normalized()
    u = up.cross(n).normalized() if abs(up.dot(n)) < 0.99 else Vector((1, 0, 0))
    v = n.cross(u).normalized()
    verts, faces, uvs = [], [], []
    for i in range(res + 1):
        for j in range(res + 1):
            a, b2 = i / res - 0.5, j / res - 0.5
            p = centre + u * a * size + v * b2 * size * aspect
            loc, nrm = surf(bvh, p + n * 1.5, -n)
            if loc is None:
                loc, nrm = p, n
            # SCULPTED (owner 2026-11-23: injuries are sculpted, not painted): a swelling dome that falls to 0 at the
            # patch edge, broken up by noise relief (blisters, crust, grain); the colour rides on top of the relief
            r = min(1.0, math.sqrt((2 * a) ** 2 + (2 * b2) ** 2))
            dome = max(0.0, 1 - r * r) ** 2
            n_ = mnoise.noise(loc * rough_scale) if rough else 0.0
            h = height * dome * (1 + rough * n_) + (abs(n_) * rough * height * 0.5 * dome if rough else 0)
            verts.append(loc + nrm * (off + max(0.0, h)))
            uvs.append((i / res, j / res))
    for i in range(res):
        for j in range(res):
            a = i * (res + 1) + j
            faces.append((a, a + res + 1, a + res + 2, a + 1))
    ob = mesh_obj(name, verts, faces, mat, uvs=uvs)
    if height and subd:
        add_mods(ob, subd=subd)
    return ob


def tube(name, pts, radius, mat, flat=1.0, res=8, closed_ends=True, subd=1):
    """A thin tube along points (welts, stitches, sigil strokes); flat < 1 squashes it against the skin (normal = side 2)."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = res // 2
    curve.use_fill_caps = closed_ends
    sp = curve.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        r = p[1] if isinstance(p, tuple) and len(p) == 2 and isinstance(p[1], float) else 1.0
        co = p[0] if isinstance(p, tuple) and len(p) == 2 and isinstance(p[1], float) else p
        sp.points[i].co = (*co, 1)
        sp.points[i].radius = r
    o = link(bpy.data.objects.new(name, curve))
    o.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o.select_set(False)
    if flat != 1.0:
        pass
    if subd:
        add_mods(o, subd=subd)
    return o


def project(bvh, p, d, off):
    loc, nrm = surf(bvh, p - d * 2.0, d)
    if loc is None:
        return p
    return loc - d * off


def copy_weights(item, part, arm):
    """Each vertex of a piece takes the skin weights of the nearest body vertex, then an Armature modifier: the piece
    bends with the pose exactly like the body under it (the in-game version welds per part instead)."""
    me = part.data
    kd = KDTree(len(me.vertices))
    mw = part.matrix_world
    for i, v in enumerate(me.vertices):
        kd.insert(mw @ v.co, i)
    kd.balance()
    names = {g.index: g.name for g in part.vertex_groups}
    groups = {}
    imw = item.matrix_world
    for v in item.data.vertices:
        _, idx, _ = kd.find(imw @ v.co)
        for g in me.vertices[idx].groups:
            nm = names[g.group]
            if nm not in groups:
                groups[nm] = item.vertex_groups.new(name=nm)
            groups[nm].add([v.index], g.weight, "REPLACE")
    mod = item.modifiers.new("arm", "ARMATURE")
    mod.object = arm
    # the Armature modifier first, before solidify / subsurf
    while item.modifiers[0].name != "arm":
        bpy.ops.object.modifier_move_up({"object": item}, modifier="arm") if False else item.modifiers.move(len(item.modifiers) - 1, 0)
    item.parent = arm
    item.matrix_parent_inverse = arm.matrix_world.inverted()


# ---------------------------------------------------------------- figures
def load_rig(tag):
    with bpy.data.libraries.load(RIG, link=False) as (src, dst):
        dst.objects = ["RoBone"] + list(PARTS.values())
    coll = bpy.data.collections.new("Fig" + tag)
    sc.collection.children.link(coll)
    objs = {}
    for o in dst.objects:
        coll.objects.link(o)
    for key, nm in PARTS.items():
        objs[key] = next(o for o in dst.objects if o.name.split(".")[0] == nm)
    objs["arm"] = next(o for o in dst.objects if o.name.split(".")[0] == "RoBone")
    return coll, objs


def swap_body(objs, body, coll):
    names = [f"NHBody_{body}_{p}" for p in BT_PART.values()]
    with bpy.data.libraries.load(BODIES, link=False) as (src, dst):
        dst.objects = names
    for key, p in BT_PART.items():
        o = next(x for x in dst.objects if x.name.startswith(f"NHBody_{body}_{p}"))
        coll.objects.link(o)
        o.rotation_euler = (0, 0, math.pi)   # built facing -Y; the rig faces +Y
        o.location = CENTRE[key]
        o.scale = (1, 1, 1)
        bpy.context.view_layer.update()
        old = objs[key]
        copy_weights(o, old, objs["arm"])
        old.hide_render = True
        old.hide_viewport = True
        objs[key] = o


def face(tag, objs, mood):
    head = objs["Head"]
    bvh = eval_bvh(head)
    hc = Vector((0, 0, 4.52))
    items = []
    for sx in (-1, 1):
        p = project(bvh, hc + Vector((0.2 * sx, 0, 0.08)), Vector((0, -1, 0)), 0.004)
        e = surface_patch(f"{tag}Eye{sx}", bvh, p, Vector((0, 1, 0)), Vector((0, 0, 1)), 0.1, M["eye_decal"], res=8, aspect=1.5)
        items.append(e)
        # brows: a short tilted tube (worried for the hurt)
        lift = 0.035 if mood == "hurt" else 0.0
        b0 = project(bvh, hc + Vector((0.3 * sx, 0, 0.21 - lift)), Vector((0, -1, 0)), 0.01)
        b1 = project(bvh, hc + Vector((0.11 * sx, 0, 0.24 + lift)), Vector((0, -1, 0)), 0.01)
        items.append(tube(f"{tag}Brow{sx}", [b0, b1], 0.016, M["eyes"], subd=0))
    m0 = project(bvh, hc + Vector((-0.12, 0, -0.17)), Vector((0, -1, 0)), 0.008)
    mm = project(bvh, hc + Vector((0, 0, -0.13 if mood == "hurt" else -0.15)), Vector((0, -1, 0)), 0.008)
    m1 = project(bvh, hc + Vector((0.12, 0, -0.17)), Vector((0, -1, 0)), 0.008)
    items.append(tube(f"{tag}Mouth", [m0, mm, m1], 0.014, M["eyes"], subd=0))
    for it in items:
        copy_weights(it, head, objs["arm"])


def skin(objs, tag, top=None, legs="trousers"):
    for key in ("Head", "Torso", "RArm", "LArm", "RLeg", "LLeg"):
        o = objs[key]
        o.data = o.data.copy()
        o.data.materials.clear()
        mat = SKIN[tag]
        if key in ("RLeg", "LLeg"):
            mat = M[legs]
        if key == "Torso" and top:
            mat = M[top]
        o.data.materials.append(mat)


def pose(arm, bone, axis, deg):
    if "--nopose" in argv:
        return
    pb = arm.pose.bones[bone]
    pb.rotation_mode = "XYZ"
    e = list(pb.rotation_euler)
    e["XYZ".index(axis)] += math.radians(deg)
    pb.rotation_euler = e


def bone_world(arm, bone):
    pb = arm.pose.bones[bone]
    return arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail


