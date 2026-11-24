"""The Headmaster's Console: 3D-rendered UI pieces (Blender 5.2, headless).
E:/Blender/blender.exe -b --factory-startup -P admin_console_render.py -- <out dir> [--quick] [--only name,name]

Each piece is modelled (bevelled iron plates, brass mouldings, rivets, gem-set gothic bosses, velvet insets), textured with the
school's own maps (art/props/source NH_Iron / NH_Brass / NH_Leather), lit like the rest of the HUD (warm key upper-left, cool fill,
low candle rim) and rendered top-down, orthographic, on a transparent film, at 2x design px.
Pieces: Frame (1600x900), Card / CardHot (380x168), Tab / TabOn (150x44), Tile (150x56), Row / RowOn (292x70),
Chip / ChipOn / ChipDanger (120x34), Medal (60x60), HoldRing (44x44), Crest (64x72), Search (290x40), Feed (774x120), Side (394x744).
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "E:/ClaudeTemp/nhchk/admin/pieces"
QUICK = "--quick" in argv
ONLY = None
if "--only" in argv:
    ONLY = set(argv[argv.index("--only") + 1].split(","))
os.makedirs(OUT, exist_ok=True)
SRC = "E:/NH-main/art/props/source/"
S = 0.01  # 1 design px = 0.01 m
PXSCALE = 2  # render at 2x design px

# ---------------------------------------------------------------- scene
_mats = {}

def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.materials, bpy.data.worlds):
        for d in list(coll):
            coll.remove(d)
    _mats.clear()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24 if QUICK else 96
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    # The camera looks straight down, so a flat top mirrors the zenith and a bevel tilted by t mirrors the sky at
    # elevation 90 - 2t. Zenith: a medium warm (flat brass reads as brass, its texture shows); a bright warm ring at
    # 30-60 degrees (the bevels catch it); dark below. Brighter toward the upper-left (-X, +Y), the HUD's key side.
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.004, 0.004, 0.005, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.3, 0.27, 0.23, 1)
    for pos, c in ((0.3, (0.03, 0.026, 0.024)), (0.5, (1.0, 0.86, 0.66)), (0.82, (0.95, 0.8, 0.6)), (0.93, (0.3, 0.27, 0.23))):
        e = cr.elements.new(pos); e.color = (*c, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    side = nt.nodes.new("ShaderNodeMath"); side.operation = "SUBTRACT"          # y - x: +1.4 upper-left
    nt.links.new(sep.outputs["Y"], side.inputs[0]); nt.links.new(sep.outputs["X"], side.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath"); gain.operation = "MULTIPLY_ADD"
    gain.inputs[1].default_value = 0.4; gain.inputs[2].default_value = 1.0; gain.use_clamp = False
    nt.links.new(side.outputs[0], gain.inputs[0])
    gmax = nt.nodes.new("ShaderNodeMath"); gmax.operation = "MAXIMUM"; gmax.inputs[1].default_value = 0.35
    nt.links.new(gain.outputs[0], gmax.inputs[0])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    for k in ("X", "Y", "Z"):
        nt.links.new(gmax.outputs[0], cmb.inputs[k])
    nt.links.new(ramp.outputs["Color"], mul.inputs["A"]); nt.links.new(cmb.outputs[0], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], bg.inputs[0])
    bg.inputs[1].default_value = 1.6
    return sc


def lights():
    """Suns, so every piece (a 0.4 m chip to the 16 m frame) gets the same light: a warm key from the upper-left, a
    cool fill from the lower-right, a low candle rim from below that warms the lower bevels."""
    def sun(name, frm, strength, col, angle):
        d = bpy.data.lights.new(name, "SUN")
        d.energy = strength
        d.color = col
        d.angle = math.radians(angle)
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.rotation_euler = (-Vector(frm)).to_track_quat("-Z", "Y").to_euler()
    sun("Key", (-1.0, 1.0, 1.5), 3.2, (1.0, 0.86, 0.68), 8)
    sun("Fill", (1.0, -0.8, 1.2), 0.7, (0.62, 0.7, 1.0), 20)
    sun("Candle", (0.1, -1.0, 0.35), 0.9, (1.0, 0.55, 0.25), 15)


def camera(w, h):
    cam = bpy.data.cameras.new("Cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(w, h) * S
    o = bpy.data.objects.new("Cam", cam)
    o.location = (0, 0, 10)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    r = bpy.context.scene.render
    r.resolution_x = int(w * PXSCALE)
    r.resolution_y = int(h * PXSCALE)
    r.resolution_percentage = 100


# ---------------------------------------------------------------- materials


def tex_mat(name, maps, tint=(1, 1, 1), rough_mul=1.0, rough_add=0.0, metal=None, scale=4.0, emission=None, normal_k=1.0, tex_k=1.0):
    """tex_k: how much of the map's colour shows (the rest is a flat mid grey), so the tint, not the map's blotches,
    sets the colour."""
    key = (name, tint, rough_mul, rough_add, metal, scale, emission, tex_k)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N = nt.nodes
    L = nt.links
    bsdf = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(kind, non_color):
        t = N.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(SRC + f"NH_{maps}_{kind}.png", check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        t.projection = "BOX"
        t.projection_blend = 0.3
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    c = img("color", False)
    soft = N.new("ShaderNodeMix")
    soft.data_type = "RGBA"
    soft.inputs["Factor"].default_value = tex_k
    soft.inputs["A"].default_value = (0.62, 0.62, 0.62, 1)
    L.new(c.outputs["Color"], soft.inputs["B"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    L.new(soft.outputs["Result"], mix.inputs["A"])
    mix.inputs["B"].default_value = (*tint, 1)
    L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    r = img("rough", True)
    rm = N.new("ShaderNodeMath")
    rm.operation = "MULTIPLY_ADD"
    rm.inputs[1].default_value = rough_mul
    rm.inputs[2].default_value = rough_add
    L.new(r.outputs["Color"], rm.inputs[0])
    L.new(rm.outputs[0], bsdf.inputs["Roughness"])
    if metal is None:
        mt = img("metal", True)
        L.new(mt.outputs["Color"], bsdf.inputs["Metallic"])
    else:
        bsdf.inputs["Metallic"].default_value = metal
    n = img("normal", True)
    nm = N.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal_k
    L.new(n.outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emission[1]
    _mats[key] = m
    return m


def flat_mat(name, col, rough=0.4, metal=0.0, emission=None, transmission=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
        b.inputs["IOR"].default_value = 1.6
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emission:
        b.inputs["Emission Color"].default_value = (*emission[0], 1)
        b.inputs["Emission Strength"].default_value = emission[1]
    return m


# dark iron (the mockup's (34, 30, 36)): half-metal iron mirrored the warm zenith and read as taupe
def IRON(): return tex_mat("Iron", "Iron", tint=(0.075, 0.066, 0.082), rough_mul=0.75, rough_add=0.26, metal=0.25, scale=3.0, tex_k=0.45)
def IRON_DARK(): return tex_mat("IronDark", "Iron", tint=(0.034, 0.029, 0.037), rough_mul=0.7, rough_add=0.3, metal=0.15, scale=2.2, tex_k=0.45)
def BRASS(): return tex_mat("Brass", "Brass", tint=(1.12, 0.74, 0.36), rough_mul=0.4, rough_add=0.1, metal=1.0, scale=2.5, normal_k=0.5, tex_k=0.55)
def BRASS_POL(): return tex_mat("BrassPol", "Brass", tint=(1.24, 0.86, 0.44), rough_mul=0.25, rough_add=0.05, metal=1.0, scale=2.5, normal_k=0.35, tex_k=0.45)


def velvet(name, base, sheen_tint):
    """Crushed velvet: a deep red base, a strong pale-red sheen at grazing angles, the leather map's normal as the nap."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = SHEEN_W.get(name, 0.6)
    b.inputs["Sheen Roughness"].default_value = 0.4
    b.inputs["Sheen Tint"].default_value = (*sheen_tint, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.0, 3.0, 3.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(SRC + "NH_Leather_normal.png", check_existing=True)
    t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6
    nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    # a soft crush: darker and lighter patches in the pile
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.4; nz.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["Factor"].default_value = 0.0
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.65
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], mx.inputs["Factor"])
    mx.inputs["A"].default_value = (base[0] * 0.85, base[1] * 0.85, base[2] * 0.85, 1)
    mx.inputs["B"].default_value = (base[0] * 1.12, base[1] * 1.12, base[2] * 1.12, 1)
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    return m


# deep wine (owner: the red read pink): a dark plum-red pile and a low wine sheen, not a pale-red one
SHEEN_W = {"Velvet": 0.4, "VelvetHot": 0.55}
def VELVET(): return velvet("Velvet", (0.042, 0.002, 0.011), (0.42, 0.06, 0.13))
def VELVET_HOT(): return velvet("VelvetHot", (0.075, 0.004, 0.018), (0.62, 0.12, 0.2))
def LEATHER(): return tex_mat("Leather", "Leather", tint=(0.036, 0.018, 0.017), rough_mul=0.7, rough_add=0.2, metal=0.0, scale=4.0)
def ENAMEL(): return flat_mat("Enamel", (0.018, 0.014, 0.018), rough=0.22, coat=0.6)
def CRIMSON(): return flat_mat("Crimson", (0.2, 0.004, 0.014), rough=0.32, coat=0.45)
def RUBY(): return flat_mat("Ruby", (0.55, 0.0, 0.03), rough=0.05, transmission=0.6, emission=((0.6, 0.02, 0.04), 0.6))


# ---------------------------------------------------------------- geometry helpers
def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def rrect_mesh(name, w, h, r, depth, z=0.0, bevel=0.0, segs=6):
    """A rounded-rectangle slab, centred, w/h/r/depth in design px; top at z + depth."""
    bm = bmesh.new()
    pts = []
    r = min(r, w / 2 - 0.01, h / 2 - 0.01)
    for cx, cy, a0 in [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)]:
        for k in range(segs + 1):
            a = math.radians(a0 + 90 * k / segs)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    vb = [bm.verts.new(((x) * S, (y) * S, z * S)) for x, y in pts]
    vt = [bm.verts.new(((x) * S, (y) * S, (z + depth) * S)) for x, y in pts]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    n = len(pts)
    for i in range(n):
        bm.faces.new([vb[i], vb[(i + 1) % n], vt[(i + 1) % n], vt[i]])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if bevel > 0:
        md = o.modifiers.new("B", "BEVEL")
        md.width = bevel * S
        md.segments = 4 if QUICK else 6
        md.limit_method = "ANGLE"
        md.profile = 0.6
    for p in me.polygons:
        p.use_smooth = True
    return o


def ring(name, w, h, r, band, depth, z, bevel):
    """A rounded-rectangle moulding ring: outer slab minus inner slab."""
    outer = rrect_mesh(name, w, h, r, depth, z, 0)
    inner = rrect_mesh(name + "_cut", w - band * 2, h - band * 2, max(r - band, 0.5), depth + 4, z - 2, 0)
    md = outer.modifiers.new("Cut", "BOOLEAN")
    md.object = inner
    md.operation = "DIFFERENCE"
    md.solver = "EXACT"
    bpy.context.view_layer.objects.active = outer
    bpy.ops.object.modifier_apply(modifier="Cut")
    bpy.data.objects.remove(inner)
    if bevel > 0:
        b = outer.modifiers.new("B", "BEVEL")
        b.width = bevel * S
        b.segments = 4 if QUICK else 8
        b.limit_method = "ANGLE"
        b.profile = 0.7
    for p in outer.data.polygons:
        p.use_smooth = True
    return outer


def sphere(name, x, y, z, r, mat, flat=0.55):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r * S, location=(x * S, y * S, z * S))
    o = bpy.context.object
    o.name = name
    o.scale.z = flat
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def cyl(name, x, y, z, r, d, mat, verts=32, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * S, depth=d * S, location=(x * S, y * S, (z + d / 2) * S))
    o = bpy.context.object
    o.name = name
    if bevel:
        b = o.modifiers.new("B", "BEVEL")
        b.width = bevel * S
        b.segments = 4
        b.limit_method = "ANGLE"
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def mat_of(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)
    return o


def rivets(w, h, inset, z, r, step, mat):
    xs = int((w - 2 * inset) // step)
    ys = int((h - 2 * inset) // step)
    for i in range(xs + 1):
        x = -w / 2 + inset + i * (w - 2 * inset) / max(xs, 1)
        sphere("Rv", x, h / 2 - inset, z, r, mat)
        sphere("Rv", x, -h / 2 + inset, z, r, mat)
    for j in range(1, ys):
        y = -h / 2 + inset + j * (h - 2 * inset) / max(ys, 1)
        sphere("Rv", -w / 2 + inset, y, z, r, mat)
        sphere("Rv", w / 2 - inset, y, z, r, mat)


def quatrefoil_boss(x, y, z, r, gem=True):
    """A gothic quatrefoil boss: four brass lobes round a ruby."""
    for a in range(4):
        ang = math.radians(45 + a * 90)
        cyl("Lobe", x + math.cos(ang) * r * 0.42, y + math.sin(ang) * r * 0.42, z, r * 0.5, 3, BRASS(), bevel=1.2)
    cyl("BossCore", x, y, z, r * 0.62, 4.5, BRASS_POL(), bevel=1.5)
    if gem:
        sphere("Gem", x, y, z + 4.5, r * 0.34, RUBY(), flat=0.6)


def pinnacle(x, y, z, h, w):
    """A small gothic pinnacle seen from above: a pointed brass leaf with a ridge (reads as cresting)."""
    bm = bmesh.new()
    pts = [(0, h), (w * 0.5, h * 0.25), (w * 0.32, 0), (-w * 0.32, 0), (-w * 0.5, h * 0.25)]
    vb = [bm.verts.new(((x + px) * S, (y + py) * S, z * S)) for px, py in pts]
    vt = [bm.verts.new(((x + px * 0.8) * S, (y + py * 0.9) * S, (z + 3) * S)) for px, py in pts]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    for i in range(5):
        bm.faces.new([vb[i], vb[(i + 1) % 5], vt[(i + 1) % 5], vt[i]])
    me = bpy.data.meshes.new("Pin")
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new("Pin", me))
    b = o.modifiers.new("B", "BEVEL")
    b.width = 0.8 * S
    b.segments = 3
    o.data.materials.append(BRASS())
    return o


def render(name):
    bpy.context.scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)


def piece(name, w, h, build):
    if ONLY and name not in ONLY:
        return
    reset()
    lights()
    camera(w, h)
    build(w, h)
    render(name)


# ---------------------------------------------------------------- pieces
def b_frame(w, h):
    W, H = w - 8, h - 8
    mat_of(rrect_mesh("Plate", W, H, 26, 6, 0, bevel=3), IRON())
    mat_of(rrect_mesh("Field", W - 60, H - 60, 14, 1.5, 6, bevel=0.8), IRON_DARK())
    mat_of(ring("Moulding", W - 22, H - 22, 22, 12, 7, 8, 3), BRASS())
    mat_of(ring("Inner", W - 64, H - 64, 14, 4, 3, 10, 1.2), BRASS())
    rivets(W - 22, H - 22, 6, 15, 3.2, 64, BRASS_POL())
    for sx in (-1, 1):
        for sy in (-1, 1):
            quatrefoil_boss(sx * (W / 2 - 24), sy * (H / 2 - 24), 14, 26)
    # cresting along the top: a row of pinnacles either side of the crest seat
    for i in range(-9, 10):
        if abs(i) < 2:
            continue
        pinnacle(i * 34, H / 2 - 14, 15, 18, 16)
    mat_of(rrect_mesh("CrestSeat", 120, 60, 18, 4, 14, bevel=2), BRASS())


def b_side(w, h):
    mat_of(rrect_mesh("Plate", w - 6, h - 6, 16, 5, 0, bevel=2.5), IRON())
    mat_of(rrect_mesh("Field", w - 30, h - 30, 10, 1.5, 5, bevel=0.8), IRON_DARK())
    mat_of(ring("Mould", w - 14, h - 14, 14, 6, 5, 6, 2), BRASS())
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere("Rv", sx * (w / 2 - 16), sy * (h / 2 - 16), 12, 4.5, BRASS_POL())


def b_card(w, h, hot=False):
    mat_of(rrect_mesh("Plate", w - 6, h - 6, 12, 5, 0, bevel=2.5), IRON())
    mat_of(rrect_mesh("Velvet", w - 26, h - 26, 8, 2, 5, bevel=1.2), VELVET_HOT() if hot else VELVET())
    mat_of(ring("Mould", w - 14, h - 14, 10, 5, 4, 7, 1.8), BRASS_POL() if hot else BRASS())
    # corner brackets
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 16), sy * (h / 2 - 16)
            o = rrect_mesh("BrkH", 26, 6, 2, 3, 10, bevel=1)
            o.location = ((x - sx * 8) * S, y * S, 0)
            mat_of(o, BRASS())
            o = rrect_mesh("BrkV", 6, 26, 2, 3, 10, bevel=1)
            o.location = (x * S, (y - sy * 8) * S, 0)
            mat_of(o, BRASS())
            sphere("Rv", x, y, 13, 3.4, BRASS_POL())
    # the medallion socket (the icon medal sits here in the mockup)
    # a shallow iron well with a thin brass lip, sitting in the velvet
    sx_, sy_ = -w / 2 + 38, h / 2 - 38
    cyl("Socket", sx_, sy_, 5, 27, 2.6, IRON_DARK(), bevel=0.8)
    lip = mat_of(ring("SocketLip", 58, 58, 29, 3, 2, 6.5, 0.8), BRASS())
    lip.location = (sx_ * S, sy_ * S, 0)


def b_tab(w, h, on=False):
    mat_of(rrect_mesh("Plate", w - 4, h - 4, 8, 6, 0, bevel=2), BRASS_POL() if on else IRON())
    mat_of(ring("Mould", w - 8, h - 8, 7, 3, 3, 6, 1), BRASS())
    if on:
        sphere("Gem", 0, -h / 2 + 3, 8, 4, RUBY())


def b_tile(w, h):
    mat_of(rrect_mesh("Plate", w - 4, h - 4, 8, 5, 0, bevel=1.8), IRON_DARK())
    mat_of(ring("Mould", w - 6, h - 6, 7, 3, 3, 5, 1), BRASS())


def b_row(w, h, on=False):
    mat_of(rrect_mesh("Plate", w - 4, h - 4, 8, 5, 0, bevel=1.8), VELVET_HOT() if on else LEATHER())
    mat_of(ring("Mould", w - 6, h - 6, 7, 3, 3, 5, 1), BRASS_POL() if on else BRASS())
    cyl("Portrait", -w / 2 + 33, 0, 4, 24, 3, IRON_DARK(), bevel=1)
    mat_of(ring("PRing", 52, 52, 26, 4, 3, 6, 1), BRASS())
    bpy.data.objects["PRing"].location.x = (-w / 2 + 33) * S


def b_chip(w, h, kind="off"):
    face = {"off": ENAMEL(), "on": BRASS_POL(), "danger": CRIMSON()}[kind]
    mat_of(rrect_mesh("Pill", w - 4, h - 4, (h - 4) / 2, 4, 0, bevel=1.5), face)
    mat_of(ring("Rim", w - 4, h - 4, (h - 4) / 2, 2.2, 2, 4, 0.8), BRASS())


def b_medal(w, h):
    cyl("Disc", 0, 0, 0, w / 2 - 3, 4, BRASS(), verts=48, bevel=1.5)
    mat_of(ring("Rim", w - 6, w - 6, w / 2 - 3, 4, 2.5, 4, 1), BRASS_POL())
    cyl("Face", 0, 0, 3, w / 2 - 9, 2, IRON_DARK(), verts=48, bevel=0.8)


def b_hold(w, h):
    mat_of(ring("Iron", w - 4, h - 4, (w - 4) / 2, 7, 4, 0, 1.2), IRON())
    mat_of(ring("Inlay", w - 10, h - 10, (w - 10) / 2, 3, 2, 3, 0.6), CRIMSON())


def b_crest(w, h):
    bm = bmesh.new()
    pts = [(-w / 2 + 4, h / 2 - 4), (w / 2 - 4, h / 2 - 4), (w / 2 - 4, -h * 0.05), (0, -h / 2 + 3), (-w / 2 + 4, -h * 0.05)]
    vb = [bm.verts.new((x * S, y * S, 0)) for x, y in pts]
    vt = [bm.verts.new((x * S, y * S, 6 * S)) for x, y in pts]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    for i in range(5):
        bm.faces.new([vb[i], vb[(i + 1) % 5], vt[(i + 1) % 5], vt[i]])
    me = bpy.data.meshes.new("Shield")
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new("Shield", me))
    b = o.modifiers.new("B", "BEVEL")
    b.width = 2.2 * S
    b.segments = 6
    o.data.materials.append(CRIMSON())
    rim = o.copy()
    rim.data = o.data.copy()
    link(rim)
    rim.scale = (1.0, 1.0, 0.7)
    rim.location.z = -0.5 * S
    s = rim.modifiers.new("Sol", "SOLIDIFY")
    s.thickness = 3 * S
    mat_of(rim, BRASS())
    sphere("Gem", 0, 4, 7, 7, RUBY())


def b_search(w, h):
    mat_of(rrect_mesh("Well", w - 4, h - 4, (h - 4) / 2, 3, 0, bevel=1.2), ENAMEL())
    mat_of(ring("Rim", w - 4, h - 4, (h - 4) / 2, 3, 2.5, 3, 0.8), BRASS())


def b_feed(w, h):
    mat_of(rrect_mesh("Plate", w - 4, h - 4, 10, 5, 0, bevel=1.8), IRON_DARK())
    mat_of(ring("Mould", w - 8, h - 8, 9, 3, 3, 5, 1), BRASS())


piece("Frame", 1600, 900, b_frame)
piece("Side", 394, 744, b_side)
piece("Rail", 320, 744, b_side)
piece("Card", 380, 168, lambda w, h: b_card(w, h, False))
piece("CardHot", 380, 168, lambda w, h: b_card(w, h, True))
piece("CardShort", 380, 138, lambda w, h: b_card(w, h, False))
piece("CardShortHot", 380, 138, lambda w, h: b_card(w, h, True))
piece("Tab", 150, 44, lambda w, h: b_tab(w, h, False))
piece("TabOn", 150, 44, lambda w, h: b_tab(w, h, True))
piece("Tile", 150, 56, b_tile)
piece("Row", 292, 70, lambda w, h: b_row(w, h, False))
piece("RowOn", 292, 70, lambda w, h: b_row(w, h, True))
piece("Chip", 120, 34, lambda w, h: b_chip(w, h, "off"))
piece("ChipOn", 120, 34, lambda w, h: b_chip(w, h, "on"))
piece("ChipDanger", 120, 34, lambda w, h: b_chip(w, h, "danger"))
piece("Medal", 60, 60, b_medal)
piece("HoldRing", 44, 44, b_hold)
piece("Crest", 64, 72, b_crest)
piece("Search", 290, 40, b_search)
piece("Feed", 774, 120, b_feed)
print("PIECES DONE")
