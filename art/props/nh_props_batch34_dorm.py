"""Props batch 34, the dorm room kit (2026-11-06) for nh_props.py (design: docs/superpowers/specs/2026-11-06-homes-interiors-design.md,
sections 2 and 4). Every student's private dorm room, built from one furniture set with tidy-to-messy variants and
state-only extras, so the room can follow the student's report card (A spotless, B tidy, C lived-in, D slipping, F a wreck).
The Institution's look: cast iron, black marble, crimson enamel (#600E1A), brass and gilt, ink, bone, wax and paper; wood
only in the books and as dark ebonised accents. Messy means clutter, dust, dead leaves and mess, never anything gory.

(The module is named _dorm: nh_props_batch34.py is the beasts kit, made the day before under the same number.)

Furniture
  DormBed / DormBedUnmade     a cast-iron single bed, gothic head and foot rails, brass knobs; a crimson damask blanket
                              with a bone satin binding (cloth-simulated, tucked over the mattress) and a bone pillow /
                              the same frame with the blanket dragged half onto the floor, the sheet rumpled, the pillow askew
  DormDesk                    a writing desk on cast-iron gothic trestles, an ebonised top with a crimson leather inset, a
                              shallow drawer with a brass bail pull, a hutch of pigeonholes with papers, letters and an inkwell
  DormChair                   an iron desk chair with a pointed back, a crimson leather seat pad (seat top 1.7)
  DormWardrobe / DormWardrobeOpen  tall, ebonised panels on an iron frame, crimson enamel inserts, brass strap hinges /
                              the right door hanging open, clothes on hangers inside, more spilling out onto the floor
  DormShelfFull / DormShelfSparse / DormShelfEmpty  a wall bookshelf on iron brackets, library-atlas books / gaps and a
                              toppled book / no books, dust on every ledge and a cobweb
  DormPlantHealthy / DormPlantWilting / DormPlantDead  a fern in a brass pot on an iron stand
  DormDeskLamp                a brass desk lamp (Glow: the bulb)
  DormCeilingLight            an iron pendant with a frosted globe (Glass) round a bulb (Glow)
  DormRug                     a woven 6 x 4 rug with the crest (dorm_weave.py; not baked)
State extras
  CertificateHonourRoll, CertificateDeansList, CertificatePerfectAttendance   gilt-framed, printed (dorm_atlas.py), a wax seal
  TrophyShelf                 a black marble shelf on iron brackets, a brass TROPHIES plaque, four velvet spots on top
  JacketOnChair, ClothesOnChair   cloth draped on DormChair (built in the chair's frame: put them at the chair's pivot)
  DormBookStack               books stacked for the desk (named Dorm..: BookStack is batch 4's)
  CoffeeCup                   a crimson crested mug of coffee, a drip down its side and a coffee ring beside it
  PaperScatter                loose papers and two balled-up sheets on the floor
  ClothesPile                 clothes in a heap on the floor
  PizzaBoxes                  three boxes stacked and one open with crusts in it
  OverdueNotices              a cork board of pinned notices: OVERDUE, FINAL NOTICE, a test marked SEE ME. - Mr. Hale ...
  EmptyCans                   crushed soda cans
Room shell (the big faces tiled with seamless sets and world UVs, nh_props.TILED; make them with
tools/vfx/make_dorm_sets.py)
  DormWall, DormWallWindow, DormWallDoor   10 x 12 walls: dark plaster (NH_DormPlaster, 5 studs a tile) over a wainscot of
                              crimson enamel fields (NH_DormEnamel, 5) in iron frames, a black marble skirting and a
                              brass-capped rail; the window wall has a pointed twin-light window (Glass) and the night beyond
                              it (Sky, a separate piece), the door wall a 5 x 8 doorway for the door kit
  DormFloor                   10 x 10 dark slate flags (NH_DormFloor, 5)
  DormCeiling                 10 x 10 plaster, a moulded cornice and a ceiling rose
  RoomNumberPlate / RoomNumberPlateBlank   a brass door plate, 101 raised on it / blank (for a SurfaceGui number)

Front faces -Y, Z is up, the origin is at the bottom centre. Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish, _gable
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _solid
from nh_props_batch9 import foil, wax_mat
from nh_props_batch10 import gilt
from nh_props_batch5 import marble
from nh_props_batch24 import _text, iron_fine, _fine
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = "C:/Windows/Fonts/palab.ttf"

DA = json.load(open(os.path.join(P.HERE, "dorm_atlas.json")))
for _k, _v in DA["print"].items():
    B30.REG["DP_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_DP_" + _k[7:]] = _v
for _k, _v in DA["cloth"].items():
    B30.REG["DC_" + _k] = _v
GARM = DA["garments"]


# ------------------------------------------------------------------ materials

def uv_fabric(name, set_name, tint, scale, band=None, normal=0.6, rough_add=0.0):
    """A woven fabric set (batch 29's source_fabric) through the cloth's flat "Spine" UV (studs), so the pattern follows the
    folds; band = a binding colour mixed in where the "nh_band" attribute is 1."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Flat"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    L(uvn.outputs["UV"], mp.inputs["Vector"])

    def tex(kind):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(B29.FAB, f"{set_name}_{kind}.png"), check_existing=True)
        if kind != "color":
            t.image.colorspace_settings.name = "Non-Color"
        L(mp.outputs["Vector"], t.inputs["Vector"])
        return t.outputs["Color"]
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    L(tex("color"), mix.inputs[6])
    mix.inputs[7].default_value = (*tint, 1)
    col = mix.outputs[2]
    if band:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "nh_band"
        bm_ = nt.nodes.new("ShaderNodeMix")
        bm_.data_type = "RGBA"
        L(at.outputs["Fac"], bm_.inputs["Factor"])
        L(col, bm_.inputs[6])
        bm_.inputs[7].default_value = (*band, 1)
        col = bm_.outputs[2]
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal
    L(tex("normal"), nm.inputs["Color"])
    r = nt.nodes.new("ShaderNodeMath")
    r.operation = "ADD"
    r.use_clamp = True
    L(tex("rough"), r.inputs[0])
    r.inputs[1].default_value = rough_add
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, col, r.outputs[0], mv.outputs[0], nm.outputs["Normal"], 0.0, False, 0.7)
    return m


def attr_mat(name, rough=0.6, bump=0.15):
    """Colour from the "nh_col" vertex colours (leaves: green to yellow to brown along each frond), a soft noise over it."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "nh_col"
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 14.0
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY_ADD"
    L(nz.outputs["Fac"], mx.inputs[0])
    mx.inputs[1].default_value = 0.35
    mx.inputs[2].default_value = 0.82
    cm = nt.nodes.new("ShaderNodeMix")
    cm.data_type = "RGBA"
    cm.blend_type = "MULTIPLY"
    cm.inputs["Factor"].default_value = 1.0
    L(at.outputs["Color"], cm.inputs[6])
    L(mx.outputs[0], cm.inputs[7])
    vein = nt.nodes.new("ShaderNodeTexWave")
    vein.inputs["Scale"].default_value = 40.0
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    L(vein.outputs["Fac"], bp.inputs["Height"])
    rv = nt.nodes.new("ShaderNodeValue")
    rv.outputs[0].default_value = rough
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, cm.outputs[2], rv.outputs[0], mv.outputs[0], bp.outputs["Normal"], 0.0, False, 0.5)
    return m


def kit(M):
    crim = (0.117, 0.0045, 0.0103)
    return {
        "iron": M["iron"],
        "ironf": iron_fine(),
        "brass": material("DormBrass", "NH_Brass", tint=(1, 1, 1), scale=0.5, wear=0.18, dirt=0.45),
        # polished brass for the hand-sized pieces (the school's brass set reads as blotches at this scale)
        "brassf": material("DormBrassFine", base=(0.8, 0.57, 0.28), rough=0.27, metal=1.0, wear=0.3, dirt=0.65),
        "gilt": gilt(),
        # the wainscot's own crimson enamel set (tools/vfx/make_dorm_sets.py), so the furniture matches the walls
        "enamel": material("DormEnamelPaint", os.path.join(P.OUT_TEX, "NH_DormEnamel"), tint=(1.0, 1.0, 1.0), scale=0.45, normal=0.6, wear=0.12,
                           wear_metal=True),
        "ebony": material("DormEbony", "NH_DeskWood", tint=(0.06, 0.047, 0.044), scale=0.3, rough_add=0.02, wear=0.35),
        "leather": material("DormLeather", "NH_Leather", tint=(crim[0] * 1.6, crim[1] * 1.6, crim[2] * 1.6), scale=1.6, normal=0.45, wear=0.25, dirt=0.7),
        "marble": marble("DormMarble", base=(0.024, 0.022, 0.026), vein=(0.16, 0.15, 0.15), scale=1.3, width=0.022, distortion=9.0),
        "paper": M["paper"],
        "glass": M["glassclear"],
        "ink": M["glass"],
        "wax": wax_mat(),
        "sealwax": flat("SealWax", (0.16, 0.012, 0.02), 0.35, dirt=0.5),
        "velvet": flat("DormVelvet", (0.075, 0.006, 0.012), 0.95, dirt=0.6),
        "bone": flat("DormBone", (0.62, 0.57, 0.46), 0.6, dirt=0.6),
        "linen": B24.cloth("DormLinen", (0.6, 0.56, 0.47), rough=0.85, weave=0.008),
        "print": B30.atlas_mat("DormPrintMat", "DormPrint", rough=0.72, leather=0.05, wear=0.04, dirt=0.45),
        "cloth": B30.atlas_mat("DormClothMat", "DormCloth", rough=0.9, leather=0.3, wear=0.0, dirt=0.45),
        "plaster": material("CornicePlaster", "NH_Limestone", tint=(0.075, 0.062, 0.066), scale=0.4, rough_add=0.1, wear=0.2, dirt=0.9),
    }


# ------------------------------------------------------------------ mesh helpers

def seg_arc(hw, zs, rise, n=14):
    """A low segmental arc from (-hw, zs) over a crown `rise` above to (hw, zs), as (x, z), left to right (for heads too
    wide for a pointed arch)."""
    R = (hw * hw + rise * rise) / (2 * rise)
    zc = zs + rise - R
    a = math.asin(hw / R)
    return [(R * math.sin(-a + 2 * a * i / n), zc + R * math.cos(-a + 2 * a * i / n)) for i in range(n + 1)]


def mesh_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def region_uv(key, s, t):
    u0, v0, u1, v1 = B30.REG[key]
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


def swatch_uv(key):
    u0, v0, u1, v1 = B30.REG[f"Swatch_{key}"]
    return ((u0 + u1) / 2, (v0 + v1) / 2)


def pbox(name, size, loc, mat, faces, k=2.0, mtx=None):
    """A box whose faces are printed: faces maps 'top', 'bottom', 'front' (-Y), 'back', 'left' (-X), 'right' to an atlas
    region key (the whole region across the face) or 'Swatch_<x>' / 'sw:<x>' for a plain swatch; missing faces use
    faces['else']."""
    w, d, h = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h))
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    for f in bm.faces:
        n = f.normal
        side = ("top" if n.z > 0.5 else "bottom" if n.z < -0.5 else "front" if n.y < -0.5 else "back" if n.y > 0.5 else
                "left" if n.x < -0.5 else "right")
        key = faces.get(side, faces.get("else"))
        if key.startswith("sw:"):
            uvp = swatch_uv(key[3:])
            for lp in f.loops:
                lp[uvl].uv = uvp
            f[kl] = 0.4
            continue
        for lp in f.loops:
            x, y, z = lp.vert.co
            if side in ("top", "bottom"):
                s, t = x / w + 0.5, (y / d + 0.5) if side == "top" else (0.5 - y / d)
            elif side in ("front", "back"):
                s, t = (x / w + 0.5) if side == "front" else (0.5 - x / w), z / h + 0.5
            else:
                s, t = (0.5 - y / d) if side == "left" else (y / d + 0.5), z / h + 0.5
            lp[uvl].uv = region_uv(key, s, t)
        f[kl] = k
    ob = mesh_obj(name, bm, mat)
    ob.matrix_world = (mtx or Matrix.Identity(4)) @ Matrix.Translation(loc)
    return ob


def sheet(name, key, w, h, mtx, mat, curl=0.0, lift=0.0, nu=8, nv=10, thick=0.008, k=2.2, rnd=None):
    """A loose sheet of paper w x h lying in its XY plane (the print up, its top edge at +y), curling up at its edges by
    `curl` and its corner by `lift`, then placed by mtx."""
    rnd = rnd or random.Random(1)
    ph = rnd.uniform(0, 6.28)

    def fn(s, t):
        x, y = (s - 0.5) * w, (t - 0.5) * h
        z = curl * ((2 * s - 1) ** 2 + 0.4 * (2 * t - 1) ** 2) + lift * max(0.0, s + t - 1.3) ** 2 * 3
        z += 0.01 * math.sin(s * 5 + ph) * math.sin(t * 4)
        return (x, y, z)
    s = _mark()
    B30.leaf_sheet(name, key, fn, nu, nv, (0, 0, 1, 1), mat, thick=thick, k=k)
    _xform(s, mtx)


def wall_sheet(name, key, w, h, mtx, mat, curl=0.03, nu=6, nv=8, k=2.2, rnd=None):
    """A sheet pinned to a board: in the XZ plane facing -Y, its corners curling off the board (toward -Y)."""
    rnd = rnd or random.Random(2)
    a, b = rnd.uniform(0.5, 1.5), rnd.uniform(0.5, 1.5)

    def fn(s, t):
        x, z = (s - 0.5) * w, (t - 0.5) * h
        y = -curl * (a * max(0.0, abs(2 * s - 1) - 0.4) ** 2 * (0.4 + t) + b * max(0.0, 0.6 - t) ** 2)
        return (x, y - 0.006, z)
    s = _mark()
    B30.leaf_sheet(name, key, fn, nu, nv, (0, 0, 1, 1), mat, thick=0.006, k=k)
    _xform(s, mtx)


def pin(name, loc, K, col="brass"):
    x, y, z = loc
    cyl(name + "Head", 0.045, 0.03, (x, y - 0.025, z), K[col], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.008)
    cyl(name + "Neck", 0.018, 0.03, (x, y - 0.005, z), K["brass"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)


def moulding_loop(name, hw, hd, prof, mat):
    """A mitred moulding round a rectangle (half sizes hw, hd at inset 0): prof = [(inset, z), ...] from one edge of the
    profile to the other; the faces turned to look into the rectangle and down."""
    bm = bmesh.new()
    rings = []
    for d, z in prof:
        a, b = hw - d, hd - d
        rings.append([bm.verts.new(p) for p in ((-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z))])
    for A, B in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            f = bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        want = Vector((-c.x, -c.y, 0)).normalized() + Vector((0, 0, -0.7))
        if f.normal.dot(want) < 0:
            f.normal_flip()
    return mesh_obj(name, bm, mat)


# ------------------------------------------------------------------ cloth: garments and the simulation

def grid_cloth(name, poly, h, mat, mtx, key=None, crumple=0.0, seed=0, band=None, flat_uv=1.0):
    """A cloth sheet: a grid (spacing h) of the quads whose centres fall inside poly (x, y studs), its "Spine" UV onto the
    garment's DormCloth region (key) and a "Flat" UV in studs x flat_uv (for woven sets); band(x, y) -> 0..1 the
    "nh_band" attribute. crumple displaces it before it falls, so it lands in folds. Placed by mtx."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    nx, ny = max(2, int(round((x1 - x0) / h))), max(2, int(round((y1 - y0) / h)))
    hx, hy = (x1 - x0) / nx, (y1 - y0) / ny
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(6)]
    fr = [rnd.uniform(1.2, 2.6) for _ in range(6)]
    bm = bmesh.new()
    vid = {}

    def vert(i, j):
        if (i, j) not in vid:
            x, y = x0 + i * hx, y0 + j * hy
            z = 0.0
            if crumple:
                z = crumple * (math.sin(x * fr[0] + ph[0]) * math.sin(y * fr[1] + ph[1]) + 0.6 * math.sin(x * fr[2] * 1.7 + y * fr[3] + ph[2])
                               + 0.4 * math.sin(y * fr[4] * 2.1 + ph[3]))
            vid[(i, j)] = bm.verts.new((x, y, z))
        return vid[(i, j)]
    for i in range(nx):
        for j in range(ny):
            cx, cy = x0 + (i + 0.5) * hx, y0 + (j + 0.5) * hy
            if WS.inside((cx, cy), poly):
                bm.faces.new((vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)))
    uvs = bm.loops.layers.uv.new("Spine")
    uvf = bm.loops.layers.uv.new("Flat")
    for f in bm.faces:
        f.smooth = True
        for lp in f.loops:
            x, y = x0 + (lp.vert.co.x - x0), lp.vert.co.y
            s, t = (lp.vert.co.x - x0) / (x1 - x0), (lp.vert.co.y - y0) / (y1 - y0)
            lp[uvs].uv = region_uv(key, s, t) if key else (0.5, 0.5)
            lp[uvf].uv = (lp.vert.co.x * flat_uv, lp.vert.co.y * flat_uv)
    if band:
        bl = bm.verts.layers.float.new("nh_band")
        for v in bm.verts:
            v[bl] = band(v.co.x, v.co.y)
    ob = mesh_obj(name, bm, mat)
    ob.matrix_world = mtx
    return ob


def garment(name, key, mtx, K, h=0.09, crumple=0.0, seed=0):
    return grid_cloth(name, GARM[key], h, K["cloth"], mtx, key="DC_" + key, crumple=crumple, seed=seed)


def collider_copies(objs):
    out = []
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in objs:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        c = bpy.data.objects.new(ob.name + "_col", me)
        bpy.context.collection.objects.link(c)
        c.matrix_world = ob.matrix_world.copy()
        out.append(c)
    return out


def floor_collider(size=40.0, z=-0.23):
    """The floor for the cloth: a plane with a deep collision shell (simulate gives FloorCol 0.25), set down so the cloth
    comes to rest just on z = 0; a thin one lets falling cloth tunnel through."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = bpy.data.meshes.new("FloorCol")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("FloorCol", me)
    bpy.context.collection.objects.link(ob)
    ob.location.z = z
    return ob


def simulate(cloths, colliders, frames=50, gravity=-28.0, mass=0.25, stiff=12.0, bend=0.4, dist=0.018, pin=None, friction=6.0, shrink=0.0,
             keep_colliders=False):
    """Drop the cloth objects onto the colliders (temporary objects) and bake the drape into their meshes. pin = a vertex
    group name holding pinned vertices."""
    sc = bpy.context.scene
    sc.gravity = (0, 0, gravity)
    for c in colliders:
        c.modifiers.new("Collision", "COLLISION")
        c.collision.thickness_outer = 0.25 if c.name.startswith("FloorCol") else 0.04
        c.collision.cloth_friction = friction
    rest = {ob.name: [(ob.data.vertices[e.vertices[0]].co - ob.data.vertices[e.vertices[1]].co).length for e in ob.data.edges] for ob in cloths}
    for ob in cloths:
        md = ob.modifiers.new("Cloth", "CLOTH")
        st = md.settings
        st.quality = 7
        st.mass = mass
        st.tension_stiffness = st.compression_stiffness = st.shear_stiffness = stiff
        st.bending_stiffness = bend
        st.air_damping = 5.0
        if shrink:
            st.shrink_min = shrink
        if pin:
            st.vertex_group_mass = pin
        cs = md.collision_settings
        cs.distance_min = dist
        cs.collision_quality = 3
        cs.use_self_collision = True
        cs.self_distance_min = 0.012
        md.point_cache.frame_start = 1
        md.point_cache.frame_end = frames
    for ob in cloths:
        ob.modifiers["Cloth"].point_cache.frame_end = frames
    sc.frame_start, sc.frame_end = 1, frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in cloths:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        old = ob.data
        ob.modifiers.clear()
        ob.data = me
        bpy.data.meshes.remove(old)
        despike(ob, rest[ob.name])
    if not keep_colliders:
        for c in colliders:
            bpy.data.objects.remove(c)
    sc.gravity = (0, 0, -9.81)


def despike(ob, rest, k=1.45, it=30):
    """Cloth the solver flung out (edges stretched well past their woven length; a drape stretches them a few percent) is
    pulled back to its neighbours, round by round; what is still stretched is cut away (a small hole reads better than a
    spike), and nothing stays under the floor."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.edges.ensure_lookup_table()
    R = {e: rest[e.index] for e in bm.edges if e.index < len(rest)}

    def long(e):
        return e.calc_length() > k * R.get(e, 1e9)
    moved = 0
    for _ in range(it):
        bad = {v for e in bm.edges if long(e) for v in e.verts}
        if not bad:
            break
        for v in bad:
            nb = [e.other_vert(v).co.copy() for e in v.link_edges if not long(e) and e.other_vert(v) not in bad]
            if not nb:
                nb = [e.other_vert(v).co.copy() for e in v.link_edges]
            v.co = v.co * 0.3 + (sum(nb, Vector()) / len(nb)) * 0.7
            moved += 1
    bad = [f for f in bm.faces if any(e.calc_length() > (k + 0.4) * R.get(e, 1e9) for e in f.edges)]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context="FACES")
    mw = ob.matrix_world
    inv = mw.inverted()
    for v in bm.verts:
        w = mw @ v.co
        if w.z < 0.012:
            w.z = 0.012
            v.co = inv @ w
    bm.to_mesh(ob.data)
    bm.free()
    if moved or bad:
        print(f"[props] despiked {ob.name}: {moved} moves, {len(bad)} faces cut")


def join_cloth(obs, name):
    """Join several cloth pieces into one object, so a single simulation lets them fall on each other through the solver's
    self-collision (cloth falling on a copy of other cloth as a collider is unstable and flies apart)."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    group = obs[0]["nh_group"]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    ob["nh_group"] = group
    P.PARTS[:] = [o for o in P.PARTS if _alive(o)]
    if ob not in P.PARTS:
        P.PARTS.append(ob)
    return ob


def _alive(o):
    try:
        o.name
        return True
    except ReferenceError:
        return False


def finish_cloth(obs, thick=0.022):
    for ob in obs:
        md = ob.modifiers.new("Solid", "SOLIDIFY")
        md.thickness = thick
        md.offset = 0
        md.use_even_offset = True
        md.use_rim = False
        for p in ob.data.polygons:
            p.use_smooth = True


def build_aside(fn, *a, **kw):
    """Build parts with fn, take them back out of the prop (to use as colliders) and return them."""
    s = _mark()
    fn(*a, **kw)
    objs = P.PARTS[s:]
    del P.PARTS[s:]
    return objs


def drop_aside(objs):
    for o in objs:
        bpy.data.objects.remove(o)


# ================================================================== the bed

BED_W, BED_L, MAT_TOP = 4.0, 8.0, 1.84


def bed_frame(K):
    ir, br = K["iron"], K["brass"]
    hx, hy = BED_W / 2 - 0.1, BED_L / 2 - 0.1
    for sy, top in ((1, 4.5), (-1, 3.2)):
        for sx in (-1, 1):
            x, y = sx * hx, sy * hy
            cyl(f"Post{sx}{sy}", 0.075, top, (x, y, top / 2), ir, verts=14, bevel=0.01)
            cyl(f"Foot{sx}{sy}", 0.11, 0.1, (x, y, 0.05), ir, verts=14, bevel=0.02)
            for z in (1.12, top - 0.9):
                cyl(f"Collar{sx}{sy}{z:.1f}", 0.095, 0.08, (x, y, z), br, verts=14, bevel=0.015)
            cyl(f"KnobNeck{sx}{sy}", 0.06, 0.08, (x, y, top + 0.04), br, verts=12, bevel=0.01)
            sphere(f"Knob{sx}{sy}", 0.14, (x, y, top + 0.18), br, seg=16, rings=8)
            sphere(f"KnobTip{sx}{sy}", 0.05, (x, y, top + 0.33), br, seg=10, rings=5)
        y = sy * hy
        # the end: a pointed top rail, a straight lower rail, spindles, a brass quatrefoil roundel at the middle
        za = top - 0.25 if sy > 0 else top - 0.15
        zs = za - 0.55
        arch = [(x, y, z) for x, z in seg_arc(hx, zs, za - zs, 16)]
        tube(f"TopRail{sy}", arch, 0.045, ir, poly=True)
        z_low = 1.12 if sy < 0 else 2.0
        tube(f"MidRail{sy}", [(-hx, y, z_low), (hx, y, z_low)], 0.04, ir, poly=True)
        tube(f"LowRail{sy}", [(-hx, y, 0.85), (hx, y, 0.85)], 0.035, ir, poly=True)
        pts = seg_arc(hx, zs, za - zs, 60)
        def top_at(x):
            best = min(pts, key=lambda p: abs(p[0] - x))
            return best[1]
        n = 9
        for i in range(n):
            x = -hx + (i + 1) * 2 * hx / (n + 1)
            if abs(x) < 0.45:
                continue
            tube(f"Spindle{sy}{i}", [(x, y, z_low), (x, y, top_at(x))], 0.022, ir, poly=True)
        zc = (z_low + za) / 2 + 0.1
        hoop(f"Roundel{sy}", (0, y, zc), 0.42, "Y", ir, thick=0.035)
        foil(f"RoundelFoil{sy}", 0, y, zc, 0.36, br, lobes=4, thick=0.022)
        sphere(f"RoundelBoss{sy}", 0.07, (0, y, zc), br, seg=12, rings=6)
        tube(f"RoundelUp{sy}", [(0, y, zc + 0.42), (0, y, za)], 0.022, ir, poly=True)
        tube(f"RoundelDn{sy}", [(0, y, zc - 0.42), (0, y, z_low)], 0.022, ir, poly=True)
        for sx in (-1, 1):
            tube(f"Scroll{sy}{sx}", [(sx * 0.42, y, zc), (sx * 0.55, y, zc - 0.2), (sx * 0.5, y, zc - 0.4), (sx * 0.4, y, zc - 0.35)], 0.018, ir)
    for sx in (-1, 1):
        box(f"SideRail{sx}", (0.07, 2 * hy, 0.24), (sx * hx, 0, 1.0), ir, bevel=0.015)
        box(f"SideLip{sx}", (0.2, 2 * hy - 0.1, 0.04), (sx * (hx - 0.1), 0, 0.9), ir, bevel=0.01)
    for k in range(7):
        y = -hy + (k + 0.5) * 2 * hy / 7
        box(f"Slat{k}", (2 * hx - 0.1, 0.18, 0.04), (0, y, 1.1), ir, bevel=0.008)


def mattress(K):
    return B29.cushion("Mattress", (BED_W - 0.32, BED_L - 0.36, 0.72), (0, 0, MAT_TOP - 0.36), K["linen"], e=(0.25, 0.12), cuts=7,
                       piping=K["linen"], pipe_r=0.03)


def blanket_band(L, W):
    def f(x, y):
        return 1.0 if (y > L / 2 - 0.32) or abs(abs(x) - W / 2) < 0.06 or abs(y + L / 2) < 0.06 else 0.0
    return f


def dorm_bed(M, unmade=False):
    K = kit(M)
    rnd = random.Random(3401 + unmade)
    bed_frame(K)
    mat_ob = mattress(K)
    blank = uv_fabric("BlanketDamask", "NH_Damask", (0.15, 0.01, 0.018), 0.95, band=(0.55, 0.47, 0.34))
    sheet_m = uv_fabric("SheetLinen", "NH_Velvet", (0.6, 0.56, 0.48), 0.6, normal=0.25, rough_add=0.1)
    cols = collider_copies([o for o in P.PARTS if o.name.startswith(("Post", "SideRail", "TopRail", "MidRail", "Knob"))] + [mat_ob])
    floor = floor_collider()
    if not unmade:
        pil = B29.cushion("Pillow", (2.7, 1.2, 0.46), (0, BED_L / 2 - 0.95, MAT_TOP + 0.2), K["linen"], e=(0.55, 0.35), cuts=6, puff=0.25)
        bw, bl = 5.5, 6.0
        bk = grid_cloth("Blanket", [(-bw / 2, -bl / 2), (bw / 2, -bl / 2), (bw / 2, bl / 2), (-bw / 2, bl / 2)], 0.14, blank,
                        T(0, -BED_L / 2 + 0.25 + bl / 2, MAT_TOP + 0.3), band=blanket_band(bl, bw))
        simulate([bk], cols + [floor], frames=60, mass=0.4, stiff=6.0, bend=0.2, friction=10.0)
        finish_cloth([bk], 0.03)
    else:
        pil = B29.cushion("Pillow", (2.7, 1.2, 0.46), (0, 0, 0), K["linen"], e=(0.55, 0.35), cuts=6, puff=0.25)
        pil.matrix_world = T(-0.55, BED_L / 2 - 1.0, MAT_TOP + 0.32) @ RZ(24 * DEG) @ RX(-28 * DEG)
        cols2 = cols + collider_copies([pil]) + [floor]
        sw, sl = 3.9, 4.2
        sh = grid_cloth("Sheet", [(-sw / 2, -sl / 2), (sw / 2, -sl / 2), (sw / 2, sl / 2), (-sw / 2, sl / 2)], 0.15, sheet_m,
                        T(0.2, 0.2, MAT_TOP + 0.75) @ RZ(-8 * DEG), crumple=0.22, seed=7)
        bw, bl = 4.9, 6.0
        bk = grid_cloth("Blanket", [(-bw / 2, -bl / 2), (bw / 2, -bl / 2), (bw / 2, bl / 2), (-bw / 2, bl / 2)], 0.14, blank,
                        T(1.0, -0.9, MAT_TOP + 1.2) @ RZ(14 * DEG) @ RY(-8 * DEG), crumple=0.25, seed=11, band=blanket_band(bl, bw))
        both = join_cloth([sh, bk], "Bedding")
        simulate([both], cols2, frames=70, mass=0.3, stiff=6.0, bend=0.25, friction=14.0)
        finish_cloth([both], 0.025)
    return _dims()


# ================================================================== desk and chair

DESK_W, DESK_D, DESK_TOP = 4.6, 2.2, 2.95


def iron_trestle(prefix, x, d, h, K):
    ir = K["iron"]
    for sy in (-1, 1):
        box(f"{prefix}Leg{sy}", (0.12, 0.12, h), (x, sy * (d / 2 - 0.12), h / 2), ir, bevel=0.015)
        box(f"{prefix}Shoe{sy}", (0.2, 0.34, 0.08), (x, sy * (d / 2 - 0.16), 0.04), ir, bevel=0.02)
    hw = d / 2 - 0.12
    arch = [(x, y, z) for y, z in seg_arc(hw, h - 0.62, 0.5, 12)]
    tube(f"{prefix}Arch", arch, 0.035, ir, poly=True)
    tube(f"{prefix}Stretch", [(x, -hw, 0.45), (x, hw, 0.45)], 0.04, ir, poly=True)
    hoop(f"{prefix}Ring", (x, 0, 1.25), 0.32, "X", ir, thick=0.03)
    for sy in (-1, 1):
        tube(f"{prefix}Brace{sy}", [(x, sy * 0.32 * 0.7, 1.25 + 0.32 * 0.7), (x, sy * hw, h - 0.75)], 0.025, ir, poly=True)
        tube(f"{prefix}BraceL{sy}", [(x, sy * 0.32 * 0.7, 1.25 - 0.32 * 0.7), (x, sy * hw, 0.45)], 0.025, ir, poly=True)


def dorm_desk(M):
    K = kit(M)
    K30 = B30.mats(M)
    rnd = random.Random(3410)
    W, D, H = DESK_W, DESK_D, DESK_TOP
    for sx in (-1, 1):
        iron_trestle(f"Tr{sx}", sx * (W / 2 - 0.3), D, H - 0.12, K)
    tube("LongStretch", [(-(W / 2 - 0.3), 0.6, 0.45), (W / 2 - 0.3, 0.6, 0.45)], 0.045, K["iron"], poly=True)
    box("Top", (W, D, 0.12), (0, 0, H - 0.06), K["ebony"], bevel=0.03)
    box("Inset", (W - 0.6, D - 0.75, 0.012), (0, -0.18, H + 0.004), K["leather"], bevel=0.0)
    tube("Bead", [(x, y, H - 0.06) for x, y in ((-W / 2 - 0.005, -D / 2 - 0.005), (W / 2 + 0.005, -D / 2 - 0.005), (W / 2 + 0.005, D / 2 + 0.005),
                                              (-W / 2 - 0.005, D / 2 + 0.005))], 0.018, K["brass"], closed=True, poly=True)
    # the apron and a shallow drawer (the knee room under it stays clear)
    box("ApronBack", (W - 0.7, 0.08, 0.3), (0, D / 2 - 0.1, H - 0.27), K["ebony"], bevel=0.015)
    for sx in (-1, 1):
        box(f"ApronSide{sx}", (0.08, D - 0.3, 0.3), (sx * (W / 2 - 0.42), 0, H - 0.27), K["ebony"], bevel=0.015)
    box("ApronFront", (W - 0.7, 0.08, 0.2), (0, -D / 2 + 0.12, H - 0.22), K["ebony"], bevel=0.015)
    box("Drawer", (1.7, 0.06, 0.16), (0, -D / 2 + 0.07, H - 0.21), K["ebony"], bevel=0.012)
    box("DrawerPanel", (1.45, 0.012, 0.09), (0, -D / 2 + 0.035, H - 0.21), K["enamel"], bevel=0.0)
    for sx in (-1, 1):
        cyl(f"PullRose{sx}", 0.035, 0.02, (sx * 0.2, -D / 2 + 0.025, H - 0.2), K["brass"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.006)
    tube("Pull", [(-0.2, -D / 2 + 0.01, H - 0.19), (-0.16, -D / 2 - 0.05, H - 0.25), (0.16, -D / 2 - 0.05, H - 0.25), (0.2, -D / 2 + 0.01, H - 0.19)],
         0.012, K["brass"])
    # the hutch: an ebonised case of pigeonholes on the back of the top, iron straps at its corners, a pointed crest
    hd, hy, z0, hh = 0.62, D / 2 - 0.31, H, 2.2
    hw = W - 0.3
    box("HutchBack", (hw, 0.05, hh), (0, D / 2 - 0.025, z0 + hh / 2), K["ebony"], bevel=0.01)
    box("HutchTop", (hw + 0.12, hd + 0.1, 0.1), (0, hy - 0.03, z0 + hh + 0.05), K["ebony"], bevel=0.025)
    box("HutchCornice", (hw + 0.2, hd + 0.16, 0.06), (0, hy - 0.05, z0 + hh + 0.13), K["iron"], bevel=0.015)
    cols = 6
    cw = (hw - 0.08) / cols
    for i in range(cols + 1):
        x = -hw / 2 + 0.04 + i * cw
        box(f"Div{i}", (0.05 if 0 < i < cols else 0.08, hd, hh), (x, hy, z0 + hh / 2), K["ebony"], bevel=0.01)
    for z in (z0 + 0.03, z0 + 1.07, z0 + hh - 0.05):
        box(f"HShelf{z:.2f}", (hw, hd, 0.05), (0, hy, z), K["ebony"], bevel=0.008)
    for sx in (-1, 1):
        x = sx * (hw / 2 + 0.005)
        for z in (z0 + 0.15, z0 + hh - 0.15):
            box(f"Strap{sx}{z:.1f}", (0.03, hd * 0.8, 0.09), (x, hy, z), K["iron"], bevel=0.01)
            for yy in (hy - 0.2, hy + 0.2):
                sphere(f"Rivet{sx}{z:.1f}{yy:.1f}", 0.018, (x + sx * 0.02, yy, z), K["brass"], seg=8, rings=4)
    # pointed arch fronts on the top row of holes
    for i in range(cols):
        cx = -hw / 2 + 0.04 + (i + 0.5) * cw
        arch = [(cx + x, hy - hd / 2 - 0.01, z) for x, z in WS.pointed(cw / 2 - 0.03, z0 + hh - 0.5, z0 + hh - 0.1, 8)]
        tube(f"HoleArch{i}", arch, 0.018, K["iron"], poly=True)
    _gable("Crest", 0, hy - hd / 2 + 0.08, 0.6, z0 + hh + 0.16, z0 + hh + 0.75, 0.08, K["ebony"], K["iron"], edge=0.025)
    foil("CrestFoil", 0, hy - hd / 2 + 0.03, z0 + hh + 0.36, 0.13, K["brass"], lobes=4, thick=0.014)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.07, (sx * (hw / 2 + 0.05), hy - 0.03, z0 + hh + 0.24), K["brass"], seg=12, rings=6)
    # the holes' contents: letters, rolled papers, a few books, an inkwell, a candle stub
    yb = hy - hd / 2 + 0.06
    for i in range(cols):
        cx = -hw / 2 + 0.04 + (i + 0.5) * cw
        for row, zb in enumerate((z0 + 0.055, z0 + 1.095)):
            kind = (i * 2 + row * 3) % 5
            if kind == 0:
                for k in range(rnd.randint(3, 6)):
                    box(f"Letter{i}{row}{k}", (cw - 0.16, 0.42, 0.012), (cx + rnd.uniform(-0.03, 0.03), hy + rnd.uniform(-0.04, 0.02), zb + 0.008 + k * 0.014),
                        K["paper"], bevel=0.0, rot=(0, 0, rnd.uniform(-0.08, 0.08)))
            elif kind == 1:
                for k in range(3):
                    cyl(f"Roll{i}{row}{k}", 0.055, hd - 0.1, (cx - 0.12 + k * 0.12, hy, zb + 0.055 + (0.1 if k == 1 else 0)), K["paper"], rot=(math.pi / 2, 0, 0),
                        verts=12, bevel=0.0)
            elif kind == 2 and row == 0:
                B30.fill_row(f"Bk{i}", cx - cw / 2 + 0.06, cx + cw / 2 - 0.06, zb, yb, hd - 0.15, 0.95, rnd, K30, p_set=0.0, p_flat=0.0, p_lean=0.0,
                             p_gap=0.0)
            elif kind in (3, 4):
                for k in range(rnd.randint(2, 4)):
                    box(f"Env{i}{row}{k}", (cw - 0.2, 0.012, 0.32), (cx + rnd.uniform(-0.04, 0.04), hy - 0.05 + k * 0.05, zb + 0.16), K["paper"], bevel=0.0,
                        rot=(rnd.uniform(-0.15, 0.05), 0, 0))
    lathe("Inkwell", [(0, 0), (0.1, 0), (0.11, 0.02), (0.11, 0.1), (0.07, 0.13), (0.04, 0.14), (0.04, 0.17), (0, 0.17)], K["ink"], seg=18,
          loc=(1.35, 0.35, H))
    hoop("InkCollar", (1.35, 0.35, H + 0.16), 0.042, "Z", K["brass"], thick=0.01)
    quill = flat("Quill", (0.86, 0.84, 0.78), 0.7)
    tube("QuillShaft", [(1.35, 0.35, H + 0.1), (1.45, 0.42, H + 0.4), (1.58, 0.5, H + 0.7)], 0.008, quill)
    strip("QuillVane", [(1.4, 0.38, H + 0.26), (1.49, 0.44, H + 0.5), (1.58, 0.5, H + 0.7)], 0.09, (0.6, -0.8, 0), quill, thick=0.005)
    return _dims()


CHAIR_SEAT = 1.7


def chair_parts(K):
    ir, br = K["iron"], K["brass"]
    W, D, ST = 1.9, 1.9, CHAIR_SEAT
    zs = ST - 0.2
    yb = D / 2 - 0.12
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.1)
        box(f"LegF{sx}", (0.09, 0.09, zs), (x, -D / 2 + 0.12, zs / 2), ir, bevel=0.012)
        tube(f"LegB{sx}", [(x, yb + 0.12, 0.0), (x, yb, zs), (x, yb + 0.05, 3.3), (x, yb + 0.12, 4.0)], 0.05, ir, square=True, poly=True)
        sphere(f"Finial{sx}", 0.085, (x, yb + 0.12, 4.08), br, seg=12, rings=6)
        tube(f"SideRail{sx}", [(x, -D / 2 + 0.12, zs - 0.06), (x, yb, zs - 0.06)], 0.035, ir, square=True, poly=True)
        tube(f"Stretch{sx}", [(x, -D / 2 + 0.12, 0.45), (x, yb + 0.07, 0.45)], 0.025, ir, poly=True)
        for z in (0.06,):
            cyl(f"Toe{sx}", 0.07, 0.04, (x, -D / 2 + 0.12, 0.02), ir, verts=12, bevel=0.01)
    tube("FrontRail", [(-(W / 2 - 0.1), -D / 2 + 0.12, zs - 0.06), (W / 2 - 0.1, -D / 2 + 0.12, zs - 0.06)], 0.035, ir, square=True, poly=True)
    tube("BackRail", [(-(W / 2 - 0.1), yb, zs - 0.06), (W / 2 - 0.1, yb, zs - 0.06)], 0.035, ir, square=True, poly=True)
    tube("XStretch", [(-(W / 2 - 0.1), 0.0, 0.45), (W / 2 - 0.1, 0.0, 0.45)], 0.025, ir, poly=True)
    box("SeatPan", (W - 0.1, D - 0.1, 0.05), (0, 0, zs - 0.01), ir, bevel=0.01)
    B29.cushion("SeatPad", (W - 0.12, D - 0.2, 0.2), (0, -0.03, zs + 0.1), K["leather"], e=(0.35, 0.2), cuts=6, piping=K["brass"], pipe_r=0.014)
    # the back: a pointed iron arch between the posts, a leather back pad, a quatrefoil in the arch
    hw = W / 2 - 0.1
    y = yb + 0.06
    tube("BackArch", [(x, y + 0.03 * (z - 3.3), z) for x, z in WS.pointed(hw, 3.15, 4.08, 14)], 0.04, ir, poly=True)
    tube("BackRailLow", [(-hw, yb + 0.02, 2.2), (hw, yb + 0.02, 2.2)], 0.035, ir, square=True, poly=True)
    tube("BackRailHigh", [(-hw, yb + 0.05, 3.3), (hw, yb + 0.05, 3.3)], 0.035, ir, square=True, poly=True)
    B29.cushion("BackPad", (W - 0.45, 0.12, 0.85), (0, yb - 0.02, 2.72), K["leather"], e=(0.4, 0.25), cuts=5, rot=(-3 * DEG, 0, 0), piping=K["brass"],
                pipe_r=0.012)
    hoop("BackRing", (0, yb + 0.07, 3.62), 0.2, "Y", ir, thick=0.025)
    foil("BackFoil", 0, yb + 0.05, 3.62, 0.17, br, lobes=4, thick=0.014)
    for sx in (-1, 1):
        tube(f"BackStrut{sx}", [(sx * 0.2, yb + 0.07, 3.62), (sx * (hw - 0.02), yb + 0.06, 3.62)], 0.02, ir, poly=True)


def dorm_chair(M):
    K = kit(M)
    chair_parts(K)
    return _dims()


def proxy_box(name, size, loc, bevel=0.05):
    """A rounded box for the cloth to fall on (a smooth proxy collides far more reliably than the real thin bars)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = ob.modifiers.new("B", "BEVEL")
        md.width = bevel
        md.segments = 3
        bpy.ops.object.modifier_apply(modifier="B")
    return ob


def chair_colliders(K):
    """DormChair as smooth proxies: the back (a slab up to the arch's top, rounded), the finials, the seat, the legs."""
    yb = 1.9 / 2 - 0.12
    cols = [proxy_box("ColBack", (1.86, 0.2, 2.15), (0, yb + 0.04, 1.95 + 1.075), 0.09),
            proxy_box("ColSeat", (1.9, 1.85, 0.32), (0, -0.03, 1.55), 0.06)]
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(sx * 0.85, yb + 0.12, 4.08), segments=12, ring_count=6)
        cols.append(bpy.context.active_object)
        cols.append(proxy_box(f"ColLegF{sx}", (0.1, 0.1, 1.5), (sx * 0.85, -0.83, 0.75), 0.02))
        cols.append(proxy_box(f"ColLegB{sx}", (0.1, 0.1, 1.5), (sx * 0.85, yb + 0.1, 0.75), 0.02))
    return cols


def jacket_on_chair(M):
    K = kit(M)
    cols = chair_colliders(K) + [floor_collider()]
    yb = 1.9 / 2 - 0.12 + 0.07
    # the blazer laid across the back's top, its shoulders on the arch, the front over the seat side, the back behind
    jk = garment("Jacket", "Jacket", T(0.12, yb, 4.4) @ RZ(7 * DEG), K, h=0.08, crumple=0.06, seed=3)
    simulate([jk], cols, frames=60, mass=0.4, stiff=9.0, bend=0.6, friction=12.0)
    finish_cloth([jk], 0.03)
    return _dims()


def clothes_on_chair(M):
    K = kit(M)
    cols = chair_colliders(K) + [floor_collider()]
    yb = 1.9 / 2 - 0.12 + 0.07
    # the sweater over the back (on its own, as the blazer is), then the trousers and the shirt in a heap on the seat
    sw = garment("Sweater", "Sweater", T(-0.1, yb, 4.4) @ RZ(-6 * DEG), K, h=0.09, crumple=0.06, seed=5)
    simulate([sw], chair_colliders(K) + [floor_collider()], frames=60, mass=0.4, stiff=9.0, bend=0.6, friction=12.0)
    tr = garment("Trousers", "Trousers", T(-0.1, -0.2, 2.2) @ RZ(80 * DEG), K, h=0.1, crumple=0.12, seed=6)
    sh = garment("Shirt", "Shirt", T(0.15, 0.0, 2.6) @ RZ(-30 * DEG), K, h=0.1, crumple=0.14, seed=7)
    pile = join_cloth([tr, sh], "Clothes")
    simulate([pile], cols, frames=60, mass=0.3, stiff=7.0, bend=0.4, friction=12.0)
    finish_cloth([sw, pile], 0.025)
    return _dims()


# ================================================================== wardrobe

WR_W, WR_D, WR_H = 4.4, 2.2, 7.8


def wardrobe_door(prefix, hx, s, K, dw, z0, z1, y0):
    """A door from its hinge at x = hx, extending toward s (+1 right, -1 left), its front face at y0 - t."""
    t = 0.12
    yc = y0 - t / 2
    X = lambda u: hx + s * u
    st, rl = 0.24, 0.28
    box(f"{prefix}StileH", (st, t, z1 - z0), (X(st / 2), yc, (z0 + z1) / 2), K["ebony"], bevel=0.02)
    box(f"{prefix}StileF", (st, t, z1 - z0), (X(dw - st / 2), yc, (z0 + z1) / 2), K["ebony"], bevel=0.02)
    for nm, z, hgt in (("Top", z1 - rl / 2, rl), ("Mid", z0 + 2.3, 0.22), ("Bot", z0 + rl / 2 + 0.05, rl + 0.1)):
        box(f"{prefix}Rail{nm}", (dw - 2 * st + 0.02, t, hgt), (X(dw / 2), yc, z), K["ebony"], bevel=0.02)
    hw = dw / 2 - st
    cx = X(dw / 2)
    # the upper insert: a pointed panel of crimson enamel framed in an iron bead; the lower one square
    up = WS.arch(hw, z0 + 2.41, z1 - rl - 1.05, z1 - rl - 0.02, 12, cx=cx)
    B20.tprism(f"{prefix}PanelUp", WS.ccw(up), yc, t * 0.6, K["enamel"])
    box(f"{prefix}FillUpL", (0.01, 0.01, 0.01), (cx, yc, z0 + 2.5), K["ebony"], bevel=0.0)
    for side in (-1, 1):
        # spandrels above the pointed head filled with ebony
        if side < 0:
            pts = [(cx - hw, z1 - rl - 1.05)] + [(cx + x, z) for x, z in WS.pointed(hw, z1 - rl - 1.05, z1 - rl - 0.02, 12) if x <= 0] + [(cx, z1 - rl), (cx - hw, z1 - rl)]
        else:
            pts = [(cx, z1 - rl - 0.02)] + [(cx + x, z) for x, z in WS.pointed(hw, z1 - rl - 1.05, z1 - rl - 0.02, 12) if x > 0] + [(cx + hw, z1 - rl), (cx, z1 - rl)]
        B20.tprism(f"{prefix}Spandrel{side}", WS.ccw(pts), yc, t, K["ebony"])
    tube(f"{prefix}BeadUp", [(x, y0 - t - 0.005, z) for x, z in up] + [(up[0][0], y0 - t - 0.005, up[0][1])], 0.022, K["iron"], square=True, poly=True)
    lo = WS.rect(hw, z0 + 0.38, z0 + 2.19, cx=cx)
    B20.tprism(f"{prefix}PanelLo", WS.ccw(lo), yc, t * 0.6, K["enamel"])
    tube(f"{prefix}BeadLo", [(x, y0 - t - 0.005, z) for x, z in lo] + [(lo[0][0], y0 - t - 0.005, lo[0][1])], 0.022, K["iron"], square=True, poly=True)
    foil(f"{prefix}Foil", cx, y0 - t - 0.01, z0 + 1.28, 0.26, K["brass"], lobes=4, thick=0.016)
    foil(f"{prefix}FoilUp", cx, y0 - t - 0.01, z1 - rl - 0.55, 0.18, K["brass"], lobes=3, thick=0.014)
    # brass strap hinges on the hinge stile, a bar handle on the free stile
    for z in (z0 + 0.6, (z0 + z1) / 2, z1 - 0.6):
        box(f"{prefix}Strap{z:.1f}", (0.55, 0.02, 0.1), (X(0.3), y0 - t - 0.012, z), K["brass"], bevel=0.008)
        sphere(f"{prefix}StrapEnd{z:.1f}", 0.06, (X(0.58), y0 - t - 0.012, z), K["brass"], seg=10, rings=5, scale=(1, 0.35, 1))
        cyl(f"{prefix}Knuckle{z:.1f}", 0.04, 0.34, (X(-0.01), y0 - t + 0.02, z), K["brass"], verts=10, bevel=0.008)
    hz = z0 + 3.2
    for z in (hz - 0.35, hz + 0.35):
        cyl(f"{prefix}HandlePost{z:.1f}", 0.022, 0.1, (X(dw - 0.14), y0 - t - 0.05, z), K["brass"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)
    cyl(f"{prefix}Handle", 0.028, 0.86, (X(dw - 0.14), y0 - t - 0.1, hz), K["brass"], verts=10, bevel=0.01)


def wardrobe(M, open_=False):
    K = kit(M)
    W, D, H = WR_W, WR_D, WR_H
    rnd = random.Random(3420)
    zb, zt = 0.45, 7.25
    box("Plinth", (W + 0.08, D + 0.04, zb), (0, 0.0, zb / 2), K["iron"], bevel=0.03)
    box("PlinthMould", (W + 0.16, D + 0.1, 0.08), (0, 0.0, zb - 0.02), K["ebony"], bevel=0.02)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.14, D, zt - zb), (sx * (W / 2 - 0.07), 0, (zb + zt) / 2), K["ebony"], bevel=0.02)
        xo = sx * (W / 2 + 0.003)
        tube(f"SidePanel{sx}", [(xo, -D / 2 + 0.3, zb + 0.4), (xo, D / 2 - 0.3, zb + 0.4), (xo, D / 2 - 0.3, zt - 0.4), (xo, -D / 2 + 0.3, zt - 0.4)],
             0.025, K["iron"], square=True, closed=True, poly=True)
        box(f"SideInset{sx}", (0.012, D - 0.7, zt - zb - 0.9), (xo, 0, (zb + zt) / 2), K["enamel"], bevel=0.0)
        tube(f"Corner{sx}", [(sx * W / 2, -D / 2 - 0.0, zb), (sx * W / 2, -D / 2, zt)], 0.05, K["iron"], square=True, poly=True)
        for z in (zb + 0.4, (zb + zt) / 2, zt - 0.4):
            sphere(f"CornerRivet{sx}{z:.1f}", 0.03, (sx * (W / 2 + 0.05), -D / 2 - 0.0, z), K["brass"], seg=8, rings=4)
    box("Back", (W - 0.28, 0.06, zt - zb), (0, D / 2 - 0.03, (zb + zt) / 2), K["ebony"], bevel=0.0)
    box("Bottom", (W - 0.28, D - 0.1, 0.1), (0, 0.0, zb + 0.05), K["ebony"], bevel=0.0)
    box("TopBoard", (W, D, 0.1), (0, 0, zt + 0.05), K["ebony"], bevel=0.015)
    box("Mould", (W + 0.16, D + 0.08, 0.1), (0, -0.0, zt + 0.15), K["iron"], bevel=0.02)
    box("Cornice", (W + 0.34, D + 0.18, 0.16), (0, -0.02, zt + 0.28), K["ebony"], bevel=0.03)
    _gable("Crest", 0, -D / 2 + 0.06, 1.0, zt + 0.36, zt + 1.1, 0.1, K["ebony"], K["iron"], edge=0.03)
    foil("CrestFoil", 0, -D / 2, zt + 0.62, 0.17, K["brass"], lobes=4, thick=0.016)
    sphere("CrestFinial", 0.06, (0, -D / 2 + 0.06, zt + 1.15), K["brass"], seg=10, rings=5)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.09, (sx * (W / 2 + 0.08), -D / 2 + 0.02, zt + 0.45), K["brass"], seg=12, rings=6)
    dw = (W - 0.28) / 2 - 0.01
    z0, z1, y0 = zb + 0.12, zt - 0.05, -D / 2 + 0.02
    wardrobe_door("DoorL", -W / 2 + 0.14, 1, K, dw, z0, z1, y0)
    box("Escutcheon", (0.12, 0.015, 0.2), (-W / 2 + 0.14 + dw - 0.13, y0 - 0.13, z0 + 2.75), K["brass"], bevel=0.01)
    box("Keyhole", (0.025, 0.02, 0.07), (-W / 2 + 0.14 + dw - 0.13, y0 - 0.135, z0 + 2.74), K["ink"], bevel=0.0)
    s = _mark()
    wardrobe_door("DoorR", W / 2 - 0.14, -1, K, dw, z0, z1, y0)
    if not open_:
        return _dims()
    hx, hy = W / 2 - 0.14, y0 - 0.12
    _xform(s, T(hx, hy, 0) @ RZ(100 * DEG) @ T(-hx, -hy, 0))
    # inside: a dark enamel back, a hat shelf, a brass rail with hangers and clothes
    box("InBack", (W - 0.3, 0.02, zt - zb - 0.2), (0, D / 2 - 0.07, (zb + zt) / 2), material("DormInside", "NH_PaintedMetal", tint=(0.09, 0.012, 0.02),
                                                                                             scale=1.0, rough_add=0.15, wear=0.2, wear_metal=True), bevel=0.0)
    box("HatShelf", (W - 0.28, D - 0.2, 0.06), (0, 0.05, 6.35), K["ebony"], bevel=0.01)
    rail_z = 6.05
    tube("Rail", [(-W / 2 + 0.14, 0.0, rail_z), (W / 2 - 0.14, 0.0, rail_z)], 0.03, K["brass"], poly=True)
    for sx in (-1, 1):
        cyl(f"RailCup{sx}", 0.06, 0.03, (sx * (W / 2 - 0.15), 0.0, rail_z), K["brass"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.005)
    # a hat box and a folded jumper on the shelf
    cyl("HatBox", 0.45, 0.45, (-1.1, 0.1, 6.38 + 0.225), material("HatBox", "NH_Paper", tint=(0.2, 0.05, 0.06), scale=0.8), verts=24, bevel=0.02)
    hoop("HatBoxBand", (-1.1, 0.1, 6.5), 0.455, "Z", K["gilt"], thick=0.012)
    hangs = []
    for k, (x, key) in enumerate(((0.45, "Shirt"), (1.25, "Sweater"))):
        tube(f"Hook{k}", [(x, 0.0, rail_z - 0.12), (x, 0.0, rail_z + 0.06), (x, 0.06, rail_z + 0.1), (x, 0.08, rail_z + 0.02)], 0.012, K["brass"])
        tube(f"Hanger{k}", [(x, -0.75, rail_z - 0.45), (x, 0.0, rail_z - 0.15), (x, 0.75, rail_z - 0.45), (x, -0.75, rail_z - 0.45)], 0.018, K["brass"],
             poly=True)
        hangs.append((x, key))
    cloths = []
    set_group("Clothes")
    for k, (x, key) in enumerate(hangs):
        g = garment(f"Hang{k}", key, T(x, 0.0, rail_z - 0.42) @ RZ(90 * DEG), K, h=0.11, seed=20 + k)
        vg = g.vertex_groups.new(name="Pin")
        hw_ = 0.72
        idx = [v.index for v in g.data.vertices if abs(v.co.y) < 0.07 and abs(v.co.x) < hw_]
        vg.add(idx, 1.0, "REPLACE")
        cloths.append(g)
    # a dress form under each (removed after), so the halves hang either side of it
    forms = []
    for x, _ in hangs:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.0, rail_z - 1.6))
        f = bpy.context.active_object
        f.scale = (0.12, 1.3, 2.3)
        bpy.ops.object.transform_apply(scale=True)
        forms.append(f)
    simulate(cloths, forms, frames=40, mass=0.25, stiff=10.0, bend=0.5, pin="Pin")
    # clothes spilling out over the sill onto the floor
    fixed = [o for o in P.PARTS if o.name.startswith(("Bottom", "Plinth", "Side", "Back", "DoorL", "DoorR"))]
    cols = collider_copies(fixed) + [floor_collider()]
    spill = []
    # (dropped clear of everything, in front of the open right door, the scarf trailing in over the sill)
    for k, (key, mtx) in enumerate((("Trousers", T(1.0, -2.3, 0.7) @ RZ(-70 * DEG)),
                                    ("Sweater", T(0.8, -2.1, 1.1) @ RZ(25 * DEG)),
                                    ("Tee", T(1.2, -2.6, 1.45) @ RZ(110 * DEG)),
                                    ("Scarf", T(1.05, -1.3, 1.0) @ RZ(8 * DEG)))):
        spill.append(garment(f"Spill{k}", key, mtx, K, h=0.11, crumple=0.15, seed=30 + k))
    heap = join_cloth(spill, "Spill")
    simulate([heap], cols, frames=65, mass=0.3, stiff=8.0, bend=0.4, friction=10.0)
    finish_cloth(cloths + [heap], 0.025)
    set_group("Main")
    return _dims()


# ================================================================== shelves

SH_W, SH_D, SH_H = 4.8, 1.1, 4.8
SH_ROWS = (0.25, 1.75, 3.25)


def shelf_case(K):
    W, D = SH_W, SH_D
    yb = D / 2
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.05)
        # cast-iron side frames: two uprights, a pointed head, a quatrefoil between them
        for yy in (-D / 2 + 0.08, D / 2 - 0.08):
            tube(f"Up{sx}{yy:.1f}", [(x, yy, 0.12), (x, yy, SH_H - 0.45)], 0.045, K["iron"], square=True, poly=True)
        tube(f"Head{sx}", [(x, y, z) for y, z in WS.pointed(D / 2 - 0.08, SH_H - 0.52, SH_H, 10)], 0.04, K["iron"], poly=True)
        hoop(f"SideRing{sx}", (x, 0, 2.5), 0.3, "X", K["iron"], thick=0.028)
        sphere(f"SideBoss{sx}", 0.06, (x + sx * 0.03, 0, 2.5), K["brass"], seg=10, rings=5)
        sphere(f"Finial{sx}", 0.07, (x, 0, SH_H + 0.06), K["brass"], seg=10, rings=5)
        for z in (1.0, 2.5, 4.0):
            tube(f"Tie{sx}{z}", [(x, -D / 2 + 0.08, z), (x, D / 2 - 0.08, z)], 0.025, K["iron"], poly=True)
        # a scroll bracket under the bottom board, against the wall
        tube(f"Bracket{sx}", [(x * 0.82, yb - 0.04, 0.12), (x * 0.82, yb - 0.04, -0.0), (x * 0.82, -D / 2 + 0.15, 0.12)], 0.035, K["iron"], poly=True)
    box("Back", (W - 0.14, 0.05, SH_H - 0.5), (0, yb - 0.035, (SH_H - 0.5) / 2 + 0.2), K["ebony"], bevel=0.0)
    for i, z in enumerate(SH_ROWS):
        box(f"Board{i}", (W - 0.02, D, 0.1), (0, 0, z - 0.05), K["ebony"], bevel=0.02)
        box(f"Lip{i}", (W - 0.02, 0.04, 0.13), (0, -D / 2 - 0.01, z - 0.04), K["iron"], bevel=0.01)
        tube(f"LipBead{i}", [(-W / 2 + 0.02, -D / 2 - 0.035, z + 0.02), (W / 2 - 0.02, -D / 2 - 0.035, z + 0.02)], 0.012, K["brass"], poly=True)
    box("TopBoard", (W + 0.1, D + 0.06, 0.1), (0, -0.0, SH_H - 0.4), K["ebony"], bevel=0.025)
    box("TopIron", (W + 0.16, D + 0.1, 0.05), (0, -0.0, SH_H - 0.33), K["iron"], bevel=0.012)
    _gable("Crest", 0, -D / 2 + 0.12, 0.7, SH_H - 0.3, SH_H + 0.25, 0.08, K["ebony"], K["iron"], edge=0.025)
    foil("CrestFoil", 0, -D / 2 + 0.07, SH_H - 0.06, 0.12, K["brass"], lobes=4, thick=0.012)


def dorm_shelf(M, state):
    K = kit(M)
    K30 = B30.mats(M)
    rnd = random.Random(3430 + state)
    shelf_case(K)
    W, D = SH_W, SH_D
    x0, x1 = -W / 2 + 0.16, W / 2 - 0.16
    tops = [SH_ROWS[0], SH_ROWS[1], SH_ROWS[2]]
    hmax = [SH_ROWS[1] - SH_ROWS[0] - 0.17, SH_ROWS[2] - SH_ROWS[1] - 0.17, SH_H - 0.45 - SH_ROWS[2] - 0.05]
    yf = -D / 2 + 0.1
    if state == 0:
        for i, z in enumerate(tops):
            B30.fill_row(f"R{i}", x0, x1, z, yf, D - 0.25, hmax[i], rnd, K30, p_gap=0.03, p_lean=0.06)
    elif state == 1:
        B30.fill_row("R0", x0, x0 + 1.6, tops[0], yf, D - 0.25, hmax[0], rnd, K30, p_gap=0.2, p_lean=0.3, p_set=0.0)
        B30.fill_row("R0b", x1 - 1.0, x1, tops[0], yf, D - 0.25, hmax[0], rnd, K30, p_gap=0.1, p_lean=0.0, p_set=0.0)
        B30.fill_row("R1", x0 + 0.6, x0 + 1.9, tops[1], yf, D - 0.25, hmax[1], rnd, K30, p_gap=0.25, p_lean=0.3, p_set=0.0)
        # a toppled book lying across the gap, and one fallen flat on its face
        d = rnd.choice(B30._fits(1.0))
        B30.book("Toppled", d, d["h"] * 0.72, T(0.6, yf + d["h"] * 0.36 + 0.05, tops[1] + d["w"] / 2 + 0.003) @ RZ(-12 * DEG) @ RY(-90 * DEG) @ T(0, 0, 0),
                 K30["atlas"])
        B30.flat_stack("Pile", 1.4, 0.0, tops[2], 2, rnd, K30, yaw=8 * DEG)
        B30.fill_row("R2", x1 - 0.9, x1, tops[2], yf, D - 0.25, hmax[2], rnd, K30, p_gap=0.0, p_lean=0.0, p_set=0.0)
    else:
        d = rnd.choice(B30._fits(0.9))
        B30.book("Last", d, d["h"] * 0.72, T(-1.2, yf + d["h"] * 0.36 + 0.1, tops[0] + d["w"] / 2 + 0.003) @ RZ(6 * DEG) @ RY(-90 * DEG), K30["atlas"])
        B30.web("WebA", (W / 2 - 0.1, D / 2 - 0.06, tops[2] + hmax[2] + 0.05), (-1, 0, 0), (0, 0, -1), 0.7, K30, rnd, spokes=6, rings=6, sag=0.1)
        B30.web("WebB", (-W / 2 + 0.1, D / 2 - 0.06, tops[1] - 0.02 + hmax[1] + 0.1), (1, -0.2, 0), (0, -0.3, -1), 0.45, K30, rnd, spokes=5, rings=4, sag=0.08)
        for k in range(4):
            x = rnd.uniform(x0, x1)
            tube(f"Strand{k}", [(x, -D / 2 + 0.02, tops[k % 3] - 0.06), (x + 0.02, -D / 2 + 0.01, tops[k % 3] - 0.06 - rnd.uniform(0.25, 0.6))], 0.0045,
                 K30["web"], square=True, poly=True)
        B30.dustify(0.85)
    if state == 1:
        B30.dustify(0.35)
    return _dims()


# ================================================================== the fern

FERN = {   # state: count, pitch range, droop, colours (base, mid, tip), pinna width, missing pinnae, curl
    "healthy": (19, (28, 66), 0.5, ((0.02, 0.06, 0.016), (0.035, 0.12, 0.03), (0.06, 0.17, 0.045)), 1.0, 0.0, 0.0),
    "wilting": (14, (18, 45), 0.85, ((0.03, 0.07, 0.018), (0.12, 0.12, 0.03), (0.2, 0.13, 0.04)), 0.85, 0.15, 0.25),
    "dead": (11, (22, 42), 1.35, ((0.09, 0.06, 0.03), (0.13, 0.085, 0.045), (0.1, 0.07, 0.04)), 0.45, 0.4, 0.7),
}


def frond(name, base, yaw, pitch, L, droop, cols, rnd, mat, width=1.0, missing=0.0, curl=0.0, n=17, rim=None):
    up = Vector((0, 0, 1))
    d0 = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
    side0 = Vector((-math.sin(yaw), math.cos(yaw), 0))
    pts = []
    m = 24
    p = Vector(base)
    d = d0.copy()
    for i in range(m + 1):
        pts.append(p.copy())
        t = i / m
        # gravity pulls the direction down, more toward the tip; a dead frond curls under
        d = (d - up * (droop * 0.13 * (0.4 + t)) - up * curl * 0.12 * t * t).normalized()
        p = p + d * (L / m)
        if rim is not None:
            # never through the pot: inside its radius a frond stays above the rim (it arches over and hangs outside)
            rr, rz = rim
            if math.hypot(p.x, p.y) < rr + 0.05 and p.z < rz + 0.04:
                p.z = rz + 0.04
                if d.z < 0:
                    d = Vector((d.x, d.y, 0.05)).normalized()
    bm = bmesh.new()
    col = bm.loops.layers.color.new("nh_col")

    def colour(t):
        a, b, c = cols
        if t < 0.5:
            k = t / 0.5
            return [a[j] + (b[j] - a[j]) * k for j in range(3)]
        k = (t - 0.5) / 0.5
        return [b[j] + (c[j] - b[j]) * k for j in range(3)]

    def face(vs, ts):
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for lp, t in zip(f.loops, ts):
            cc = colour(t)
            lp[col] = (*[min(1.0, v * rnd.uniform(0.9, 1.1)) for v in cc], 1.0)
    # the stem: a thin ribbon
    rib = []
    for i, q in enumerate(pts):
        t = i / m
        tg = (pts[min(i + 1, m)] - pts[max(i - 1, 0)]).normalized()
        sd = tg.cross(up).normalized() if abs(tg.z) < 0.98 else side0
        w = 0.025 * (1 - 0.7 * t)
        rib.append((bm.verts.new(q - sd * w), bm.verts.new(q + sd * w), t))
    for (a0, a1, ta), (b0, b1, tb) in zip(rib, rib[1:]):
        face((a0, b0, b1, a1), (ta, tb, tb, ta))
    # the pinnae, alternating a little up the stem, longest a third of the way up
    for i in range(2, m):
        t = i / m
        q = pts[i]
        tg = (pts[i + 1] - pts[i - 1]).normalized()
        sd = tg.cross(up).normalized() if abs(tg.z) < 0.98 else side0
        nrm = sd.cross(tg).normalized()
        if nrm.z < 0:
            nrm = -nrm
        size = L * 0.2 * math.sin(math.pi * min(1.0, 0.12 + t * 0.95)) ** 0.9 * (1.15 - 0.4 * t)
        for s in (-1, 1):
            if rnd.random() < missing:
                continue
            dirp = (tg * 0.5 + sd * s * 1.0 - nrm * (0.25 + 0.5 * droop * t)).normalized()
            wv = dirp.cross(nrm).normalized()
            l = size * rnd.uniform(0.85, 1.05)
            w = l * 0.17 * width
            r0 = q + tg * 0.004 * s
            a = r0 + dirp * l * 0.25 + wv * w * 0.9
            b = r0 + dirp * l * 0.7 + wv * w * 0.65
            tip = r0 + dirp * l + nrm * (-0.02 * l)
            b2 = r0 + dirp * l * 0.7 - wv * w * 0.65
            a2 = r0 + dirp * l * 0.25 - wv * w * 0.9
            if curl > 0.3:
                # shrivelled: the tips roll under
                tip = tip - nrm * l * 0.25 * curl
                b, b2 = b - nrm * l * 0.1 * curl, b2 - nrm * l * 0.1 * curl
            vs = [bm.verts.new(v) for v in (r0, a, b, tip, b2, a2)]
            tt = min(1.0, t + 0.15)
            face(vs, (t, tt, tt, min(1.0, tt + 0.1), tt, tt))
    ob = mesh_obj(name, bm, mat)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    _solid(ob, 0.006).modifiers["Solid"].use_rim = False
    return ob


def plant_stand(K):
    ir = K["iron"]
    hoop("TopRing", (0, 0, 1.5), 0.42, "Z", ir, thick=0.035)
    hoop("MidRing", (0, 0, 0.55), 0.38, "Z", ir, thick=0.028)
    cyl("Tray", 0.4, 0.04, (0, 0, 1.49), ir, verts=24, bevel=0.01)
    for k in range(3):
        a = k / 3 * 2 * math.pi + 0.3
        c, s = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.42, s * 0.42, 1.5), (c * 0.4, s * 0.4, 1.0), (c * 0.38, s * 0.38, 0.55), (c * 0.48, s * 0.48, 0.2), (c * 0.62, s * 0.62, 0.05)],
             0.035, ir, square=True)
        tube(f"Toe{k}", [(c * 0.62, s * 0.62, 0.05), (c * 0.72, s * 0.72, 0.03), (c * 0.74, s * 0.74, 0.1), (c * 0.68, s * 0.68, 0.12)], 0.025, ir)
        tube(f"Scroll{k}", [(c * 0.4, s * 0.4, 1.4), (c * 0.55, s * 0.55, 1.3), (c * 0.56, s * 0.56, 1.12), (c * 0.45, s * 0.45, 1.1)], 0.02, ir)
        sphere(f"Ball{k}", 0.045, (c * 0.42, s * 0.42, 1.54), K["brass"], seg=10, rings=5)


def dorm_plant(M, state):
    K = kit(M)
    rnd = random.Random({"healthy": 3440, "wilting": 3441, "dead": 3442}[state])
    plant_stand(K)
    z0 = 1.51
    lathe("Pot", [(0, 0), (0.27, 0), (0.29, 0.04), (0.26, 0.09), (0.33, 0.2), (0.42, 0.55), (0.47, 0.71), (0.51, 0.75), (0.51, 0.8), (0.46, 0.8),
                  (0.45, 0.73), (0, 0.73)], K["brass"], seg=36, loc=(0, 0, z0))
    hoop("PotBand", (0, 0, z0 + 0.42), 0.405, "Z", K["brass"], thick=0.018)
    for sx in (-1, 1):
        hoop(f"PotRing{sx}", (sx * 0.47, 0, z0 + 0.52), 0.09, "Y", K["brass"], thick=0.014)
        sphere(f"PotBoss{sx}", 0.05, (sx * 0.45, 0, z0 + 0.6), K["brass"], seg=10, rings=5)
    dry = state == "dead"
    soil = material("Soil", "NH_Limestone", tint=(0.13, 0.095, 0.065) if dry else (0.05, 0.036, 0.026), scale=3.0, rough_add=0.25 if dry else 0.1,
                    wear=0.0, dirt=0.9)
    cyl("Soil", 0.45, 0.03, (0, 0, z0 + 0.72), soil, verts=32, bevel=0.0)
    count, (p0, p1), droop, cols, width, missing, curl = FERN[state]
    leaves = attr_mat("FernLeaf", rough=0.5 if state == "healthy" else 0.75)
    base = Vector((0, 0, z0 + 0.74))
    for k in range(count):
        yaw = k / count * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        pitch = rnd.uniform(p0, p1) * DEG
        L = rnd.uniform(1.6, 2.3) * (0.9 if state == "dead" else 1.0)
        off = Vector((math.cos(yaw), math.sin(yaw), 0)) * rnd.uniform(0.02, 0.12)
        frond(f"Frond{k}", base + off, yaw, pitch, L, droop * rnd.uniform(0.8, 1.2), cols, rnd, leaves, width=width, missing=missing, curl=curl,
              rim=(0.51, z0 + 0.8))
    # young fiddleheads in the healthy one, fallen leaflets round the others
    if state == "healthy":
        for k in range(3):
            a = k * 2.1 + 0.4
            c = base + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 0))
            tube(f"Fiddle{k}", [tuple(c), tuple(c + Vector((0, 0, 0.3))), tuple(c + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.42))),
                                tuple(c + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.36)))], 0.018, flat("Fiddle", (0.05, 0.13, 0.035), 0.5))
    else:
        nf = 9 if state == "wilting" else 22
        dead_m = flat("FallenLeaf", (0.16, 0.1, 0.045) if state == "dead" else (0.22, 0.17, 0.05), 0.85)
        for k in range(nf):
            r = rnd.uniform(0.2, 1.3)
            a = rnd.uniform(0, 2 * math.pi)
            on_tray = rnd.random() < 0.25
            z = (1.515 if on_tray else 0.005) + k * 0.0005
            r = r * 0.35 if on_tray else r
            ln = rnd.uniform(0.12, 0.22)
            x, y = math.cos(a) * r, math.sin(a) * r
            yaw = rnd.uniform(0, 6.28)
            pts = [(x, y, z), (x + math.cos(yaw) * ln * 0.5 - math.sin(yaw) * ln * 0.12, y + math.sin(yaw) * ln * 0.5 + math.cos(yaw) * ln * 0.12, z + 0.01),
                   (x + math.cos(yaw) * ln, y + math.sin(yaw) * ln, z + 0.02)]
            strip(f"Fallen{k}", pts, ln * 0.3, (-math.sin(yaw), math.cos(yaw), 0), dead_m, thick=0.004, it=1)
    return _dims()


# ================================================================== lamps

def desk_lamp(M):
    K = kit(M)
    br = K["brassf"]
    lathe("Base", [(0, 0), (0.38, 0), (0.4, 0.03), (0.36, 0.07), (0.22, 0.12), (0.12, 0.16), (0.1, 0.2), (0, 0.2)], br, seg=32)
    hoop("BaseBead", (0, 0, 0.05), 0.385, "Z", br, thick=0.012)
    cyl("Switch", 0.04, 0.05, (0.22, -0.16, 0.12), K["ink"], verts=10, bevel=0.008)
    tube("Post", [(0, 0, 0.18), (0, 0, 1.05)], 0.035, br, poly=True)
    sphere("Elbow", 0.07, (0, 0, 1.08), br, seg=14, rings=7)
    cyl("ElbowNut", 0.045, 0.16, (0, 0, 1.08), br, rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    tube("Arm", [(0, 0, 1.08), (0, -0.55, 1.62)], 0.03, br, poly=True)
    sphere("Wrist", 0.06, (0, -0.55, 1.62), br, seg=12, rings=6)
    # the shade: a brass bell, tilted to throw the light down onto the desk in front
    s = _mark()
    lathe("Shade", [(0.0, 0.4), (0.07, 0.4), (0.09, 0.35), (0.13, 0.27), (0.22, 0.13), (0.29, 0.03), (0.3, 0.0), (0.285, 0.0), (0.27, 0.025), (0.2, 0.12),
                    (0.115, 0.26), (0.075, 0.34), (0.0, 0.355)], br, seg=36)
    hoop("ShadeRim", (0, 0, 0.005), 0.297, "Z", br, thick=0.012)
    cyl("Socket", 0.042, 0.1, (0, 0, 0.29), K["ink"], verts=12, bevel=0.01)
    set_group("Glow")
    sphere("Bulb", 0.075, (0, 0, 0.19), K["paper"], seg=14, rings=8, scale=(1, 1, 1.25))
    set_group("Main")
    _xform(s, T(0, -0.6, 1.3) @ RX(-28 * DEG))
    tube("Chain", [(0.12, -0.72, 1.38), (0.13, -0.76, 1.12)], 0.006, br, poly=True)
    sphere("ChainPull", 0.022, (0.13, -0.76, 1.1), br, seg=8, rings=4)
    return _dims()


def ceiling_light(M):
    K = kit(M)
    ir, br = K["iron"], K["brass"]
    top = 2.75
    lathe("Canopy", [(0, top - 0.2), (0.12, top - 0.2), (0.3, top - 0.12), (0.38, top - 0.04), (0.38, top), (0, top)], ir, seg=28)
    hoop("CanopyBead", (0, 0, top - 0.05), 0.375, "Z", br, thick=0.012)
    s = _mark()
    B30.chain("Chain", [(0, 0, top - 0.2), (0, 0, 1.32)], ir, r=0.05, thick=0.012)
    cyl("Stem", 0.035, 0.12, (0, 0, 1.28), br, verts=12, bevel=0.01)
    # the gallery: an iron crown holding the globe's neck, little pointed leaves round it
    hoop("Gallery", (0, 0, 1.17), 0.25, "Z", ir, thick=0.03)
    hoop("GalleryLow", (0, 0, 1.08), 0.22, "Z", ir, thick=0.022)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        c, sn = math.cos(a), math.sin(a)
        tube(f"Leaf{k}", [(c * 0.25, sn * 0.25, 1.17), (c * 0.3, sn * 0.3, 1.27), (c * 0.27, sn * 0.27, 1.36)], 0.018, ir, square=True)
        tube(f"Strut{k}", [(c * 0.22, sn * 0.22, 1.08), (c * 0.25, sn * 0.25, 1.17)], 0.014, ir, poly=True)
    tube("Spokes", [(-0.25, 0, 1.17), (0.25, 0, 1.17)], 0.015, ir, poly=True)
    cyl("Socket", 0.06, 0.16, (0, 0, 1.0), br, verts=14, bevel=0.01)
    set_group("Glass")
    lathe("Globe", [(0.0, 0.09), (0.16, 0.1), (0.34, 0.2), (0.46, 0.38), (0.5, 0.58), (0.46, 0.78), (0.34, 0.95), (0.21, 1.06), (0.2, 1.12), (0.18, 1.12),
                    (0.19, 1.06), (0.32, 0.94), (0.44, 0.78), (0.48, 0.58), (0.44, 0.39), (0.32, 0.22), (0.15, 0.12), (0.0, 0.11)], K["bone"], seg=32)
    set_group("Glow")
    sphere("Bulb", 0.13, (0, 0, 0.75), K["paper"], seg=14, rings=8, scale=(1, 1, 1.25))
    set_group("Main")
    lathe("Finial", [(0, 0.0), (0.04, 0.0), (0.06, 0.04), (0.05, 0.08), (0.03, 0.1), (0, 0.1)], br, seg=14)
    return _dims()


# ================================================================== state extras

def certificate(M, key, seed):
    K = kit(M)
    rnd = random.Random(seed)
    pw, ph = 1.95, 1.43
    fw = 0.17
    zc = ph / 2 + fw + 0.02
    # the gilt frame: a moulded section mitred round the print (back on the wall at y = 0)
    prof = [(0.0, 0.0), (0.0, -0.05), (0.03, -0.09), (0.07, -0.11), (0.11, -0.1), (0.14, -0.07), (0.15, -0.05), (0.17, -0.04), (0.17, -0.02)]
    hw, hh = pw / 2 + fw, ph / 2 + fw
    bm = bmesh.new()
    rings = []
    for d, y in prof:
        a, b = hw - d, hh - d
        rings.append([bm.verts.new((x, y, z + zc)) for x, z in ((-a, -b), (a, -b), (a, b), (-a, b))])
    nseg = len(rings) - 1
    for si, (A, B) in enumerate(zip(rings, rings[1:])):
        for i in range(4):
            j = (i + 1) % 4
            f = bm.faces.new((A[i], A[j], B[j], B[i]))
            c = f.calc_center_median()
            rx, rz = c.x / hw, (c.z - zc) / hh
            radial = Vector((math.copysign(1, rx), 0, 0)) if abs(rx) > abs(rz) else Vector((0, 0, math.copysign(1, rz)))
            want = radial if si == 0 else -radial if si == nseg - 1 else Vector((0, -1, 0))
            f.normal_update()
            if f.normal.dot(want) < 0:
                f.normal_flip()
    fr = mesh_obj("Frame", bm, K["gilt"])
    fr.modifiers.new("Tri", "TRIANGULATE")
    box("FrameBack", (2 * hw - 0.02, 0.02, 2 * hh - 0.02), (0, -0.01, zc), K["ebony"], bevel=0.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"Corner{sx}{sz}", sx * (hw - 0.085), -0.122, zc + sz * (hh - 0.085), 0.06, K["gilt"], lobes=4, thick=0.012)
    box("Mat", (pw + 0.04, 0.012, ph + 0.04), (0, -0.03, zc), K["velvet"], bevel=0.0)
    B30.plate("Print", "DP_" + key, pw, ph, 0.01, T(0, -0.04, zc), K["print"], edge="DP_parch", k=3.4)
    # the wax seal and its ribbon tails at the foot of the print, between the signatures
    zs = zc - ph / 2 + 0.13
    for sx in (-1, 1):
        box(f"Ribbon{sx}", (0.06, 0.006, 0.22), (sx * 0.06, -0.05, zs - 0.1), material(f"Ribbon{sx}", "NH_Leather", tint=(0.16, 0.012, 0.022), scale=4.0,
                                                                                       normal=0.2, rough_add=0.2, wear=0.0), bevel=0.0, rot=(0, sx * 0.35, 0))
    lathe("Seal", [(0, 0), (0.08, 0), (0.088, 0.01), (0.084, 0.022), (0.066, 0.027), (0.0, 0.025)], K["sealwax"], seg=24, jitter=(0.06, seed),
          loc=(0, 0, 0))
    seal = P.PARTS[-1]
    seal.matrix_world = T(0, -0.05, zs) @ RX(math.pi / 2)
    hoop("SealRing", (0, -0.078, zs), 0.052, "Y", K["sealwax"], thick=0.008)
    B20.tprism("SealMoon", WS.crescent(0.0, zs, 0.034, shift=0.4, tilt=0.6), -0.078, 0.008, K["sealwax"])
    _fine(0.5)
    return _dims()


TROPHY_SPOTS = [(-2.25, -0.05), (-0.75, -0.05), (0.75, -0.05), (2.25, -0.05)]
TROPHY_TOP = 1.0


def trophy_shelf(M):
    K = kit(M)
    W, D = 6.0, 1.1
    zt = TROPHY_TOP - 0.03
    box("Board", (W, D, 0.16), (0, 0, zt - 0.08), K["marble"], bevel=0.03)
    box("BoardEdge", (W + 0.04, 0.05, 0.05), (0, -D / 2 - 0.01, zt - 0.13), K["brass"], bevel=0.01)
    box("Fascia", (W - 0.2, 0.08, 0.42), (0, -D / 2 + 0.06, zt - 0.37), K["iron"], bevel=0.015)
    box("WallStrip", (W - 0.2, 0.06, 0.5), (0, D / 2 - 0.03, zt - 0.41), K["iron"], bevel=0.01)
    # the plaque: brass, a raised border and raised letters
    pw, ph, zc = 2.0, 0.32, zt - 0.37
    box("Plaque", (pw, 0.03, ph), (0, -D / 2 + 0.005, zc), K["brassf"], bevel=0.008)
    tube("PlaqueBorder", [(-pw / 2 + 0.04, -D / 2 - 0.012, zc - ph / 2 + 0.04), (pw / 2 - 0.04, -D / 2 - 0.012, zc - ph / 2 + 0.04),
                          (pw / 2 - 0.04, -D / 2 - 0.012, zc + ph / 2 - 0.04), (-pw / 2 + 0.04, -D / 2 - 0.012, zc + ph / 2 - 0.04)], 0.008, K["gilt"], square=True,
         closed=True, poly=True)
    _text("Word", "TROPHIES", FONT, K["gilt"], lambda x, y, h: (x, -D / 2 - 0.01 - h, zc + y), fit=(pw - 0.3, ph - 0.12), depth=0.012, res=4)
    for sx in (-1, 1):
        sphere(f"Screw{sx}", 0.022, (sx * (pw / 2 - 0.08), -D / 2 - 0.012, zc), K["iron"], seg=8, rings=4, scale=(1, 0.5, 1))
    # scroll brackets under it
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.7)
        tube(f"Bracket{sx}", [(x, D / 2 - 0.05, zt - 0.66), (x, D / 2 - 0.05, 0.0), (x, D / 2 - 0.25, 0.06), (x, -D / 2 + 0.25, zt - 0.17)], 0.04, K["iron"],
             square=True, poly=True)
        tube(f"BracketScroll{sx}", [(x, D / 2 - 0.1, 0.3), (x, D / 2 - 0.45, 0.32), (x, D / 2 - 0.5, 0.58), (x, D / 2 - 0.35, 0.6)], 0.025, K["iron"])
    # four spots for the beast trophies: velvet pads in brass rings, evenly spaced
    for k, (x, y) in enumerate(TROPHY_SPOTS):
        cyl(f"Pad{k}", 0.34, 0.03, (x, y, zt + 0.015), K["velvet"], verts=32, bevel=0.008)
        hoop(f"PadRing{k}", (x, y, zt + 0.015), 0.35, "Z", K["brass"], thick=0.014)
    return _dims()


def book_stack(M):
    K30 = B30.mats(M)
    rnd = random.Random(3450)
    B30.flat_stack("S", 0, 0, 0.0, 5, rnd, K30, yaw=-8 * DEG, jitter=9, hmax=1.15)
    return _dims()


def coffee_cup(M):
    K = kit(M)
    r, h = 0.2, 0.42
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    seg, rings = 32, 8
    vs = [[bm.verts.new((math.cos(a) * r * (1 - 0.04 * (1 - z / h)), math.sin(a) * r * (1 - 0.04 * (1 - z / h)), z))
           for a in [i / seg * 2 * math.pi for i in range(seg)]] for z in [h * j / rings for j in range(rings + 1)]]
    for j in range(rings):
        for i in range(seg):
            a, b = vs[j][i], vs[j][(i + 1) % seg]
            c, d = vs[j + 1][(i + 1) % seg], vs[j + 1][i]
            f = bm.faces.new((a, b, c, d))
            f.smooth = True
            f[kl] = 2.0
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = region_uv("DP_Mug_Wrap", ii / seg, 0.05 + 0.9 * jj / rings)
    mesh_obj("MugSide", bm, K["print"])
    glaze = flat("MugGlaze", (0.13, 0.016, 0.026), 0.15)
    inner = flat("MugInner", (0.7, 0.66, 0.58), 0.15)
    lathe("MugBottom", [(0, 0), (0.192, 0), (0.192, 0.02), (0, 0.02)], glaze, seg=32)
    lathe("MugRim", [(0.178, h - 0.06), (0.178, h - 0.005), (0.2, h - 0.005), (0.2, h + 0.005), (0.19, h + 0.012), (0.17, h + 0.005), (0.17, 0.03), (0, 0.03)],
          inner, seg=32)
    coffee = flat("Coffee", (0.03, 0.012, 0.006), 0.06)
    cyl("Coffee", 0.172, 0.01, (0, 0, h - 0.07), coffee, verts=32, bevel=0.0)
    tube("Handle", [(0.19, 0, h - 0.08), (0.31, 0, h - 0.1), (0.33, 0, h * 0.5), (0.3, 0, 0.12), (0.19, 0, 0.1)], 0.03, glaze)
    tube("Drip", [(-0.03, -0.205, h + 0.003), (-0.025, -0.206, h - 0.08), (-0.028, -0.205, h - 0.16)], 0.006, coffee)
    sphere("DripEnd", 0.009, (-0.028, -0.205, h - 0.165), coffee, seg=8, rings=4)
    # the coffee ring beside it, a faint stain on whatever it stands on
    ring = flat("CoffeeRing", (0.16, 0.085, 0.04), 0.35)
    bm = bmesh.new()
    n = 48
    inner, outer = [], []
    for i in range(n + 1):
        a = i / n * 2 * math.pi * 0.86 + 0.4
        w = 0.016 + 0.01 * math.sin(a * 2.3) ** 2
        r = 0.19 * (1 + 0.03 * math.sin(a * 3))
        inner.append(bm.verts.new((0.55 + math.cos(a) * (r - w), -0.1 + math.sin(a) * (r - w), 0.003)))
        outer.append(bm.verts.new((0.55 + math.cos(a) * r, -0.1 + math.sin(a) * r, 0.003)))
    for i in range(n):
        bm.faces.new((inner[i], outer[i], outer[i + 1], inner[i + 1]))
    mesh_obj("Ring", bm, ring)
    _fine(0.35)
    return _dims()


def paper_scatter(M):
    K = kit(M)
    rnd = random.Random(3460)
    keys = ["Paper_Notes", "Paper_Sums", "Paper_Essay", "Paper_Doodle", "Paper_Test", "Paper_Notes", "Notice_Warning"]
    spots = [(-1.2, 0.4, 20), (-0.3, 0.9, -35), (0.5, 0.2, 10), (1.3, 0.6, 50), (-0.6, -0.5, -10), (0.9, -0.6, 75), (0.1, -0.1, -60)]
    for k, (key, (x, y, a)) in enumerate(zip(keys, spots)):
        sheet(f"Sheet{k}", "DP_" + key, 0.76, 1.0, T(x, y, 0.004 + k * 0.0045) @ RZ(a * DEG), K["print"], curl=rnd.uniform(0.01, 0.04),
              lift=rnd.uniform(0.0, 0.025), rnd=rnd)
    for k, (x, y) in enumerate(((1.6, -0.2), (-1.5, -0.4))):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.17)
        uvl = bm.loops.layers.uv.new("Spine")
        g = random.Random(k)
        for v in bm.verts:
            v.co *= 1 + g.uniform(-0.25, 0.2)
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.3, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        for f in bm.faces:
            for lp in f.loops:
                c = lp.vert.co.normalized()
                lp[uvl].uv = region_uv("DP_Paper_Notes", 0.5 + math.atan2(c.y, c.x) / (2 * math.pi), 0.5 + c.z * 0.45)
        ob = mesh_obj(f"Ball{k}", bm, K["print"])
        ob.location = (x, y, 0.14)
    return _dims()


def clothes_pile(M):
    K = kit(M)
    floor = floor_collider()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, -0.15), segments=16, ring_count=8)
    dome = bpy.context.active_object
    dome.scale = (0.75, 0.6, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    out = []
    for k, (key, mtx) in enumerate((("Trousers", T(0.1, 0.1, 0.9) @ RZ(30 * DEG)), ("Sweater", T(-0.2, 0.0, 1.35) @ RZ(-50 * DEG)),
                                    ("Shirt", T(0.3, -0.2, 1.8) @ RZ(100 * DEG)), ("Tee", T(-0.4, 0.3, 2.25) @ RZ(15 * DEG)),
                                    ("Scarf", T(0.2, 0.1, 2.65) @ RZ(-20 * DEG)))):
        out.append(garment(f"G{k}", key, mtx, K, h=0.1, crumple=0.2, seed=40 + k))
    pile = join_cloth(out, "Pile")
    simulate([pile], [floor, dome], frames=70, mass=0.3, stiff=7.0, bend=0.35, friction=12.0)
    finish_cloth([pile], 0.022)
    return _dims()


def pizza_boxes(M):
    K = kit(M)
    rnd = random.Random(3470)
    w, h = 1.55, 0.2
    faces = {"top": "DP_Pizza_Lid", "front": "DP_Pizza_Side", "back": "DP_Pizza_Side", "left": "DP_Pizza_Side", "right": "DP_Pizza_Side", "bottom": "sw:DP_kraft"}
    z = 0.0
    for k, (dx, dy, a) in enumerate(((0.0, 0.0, 4), (0.05, -0.04, -7), (-0.06, 0.03, 12))):
        pbox(f"Box{k}", (w, w, h), (0, 0, 0), K["print"], faces, k=1.6, mtx=T(-0.9 + dx, 0.2 + dy, z + h / 2) @ RZ(a * DEG))
        z += h + 0.004
    # the open one: its tray, the lid up at the back (print outward), a paper liner, crusts left in it
    ox, oy = 1.0, -0.3
    s = _mark()
    t = 0.02
    kraft_in = {"else": "sw:DP_kraftlt"}
    pbox("TrayBase", (w, w, t), (0, 0, t / 2), K["print"], {"else": "sw:DP_kraftlt", "bottom": "sw:DP_kraft"}, k=1.0)
    for nm, sz, loc in (("TrayF", (w, t, h), (0, -w / 2 + t / 2, h / 2)), ("TrayB", (w, t, h), (0, w / 2 - t / 2, h / 2)),
                        ("TrayL", (t, w, h), (-w / 2 + t / 2, 0, h / 2)), ("TrayR", (t, w, h), (w / 2 - t / 2, 0, h / 2))):
        f = dict(kraft_in)
        side = {"TrayF": "front", "TrayB": "back", "TrayL": "left", "TrayR": "right"}[nm]
        f[side] = "DP_Pizza_Side"
        pbox(nm, sz, loc, K["print"], f, k=1.2)
    lid = pbox("Lid", (w, w, t), (0, 0, 0), K["print"], {"top": "DP_Pizza_Lid", "bottom": "sw:DP_kraftlt", "else": "sw:DP_kraft"}, k=1.6)
    lid.matrix_world = T(0, w / 2, h) @ RX(-105 * DEG) @ T(0, -w / 2, t / 2)
    box("Liner", (w - 0.12, w - 0.12, 0.006), (0.0, 0.0, t + 0.004), material("Liner", "NH_Paper", tint=(0.92, 0.88, 0.78), scale=0.6, wear=0.0), bevel=0.0)
    crust = material("Crust", "NH_Limestone", tint=(0.5, 0.27, 0.1), scale=2.5, rough_add=0.15, wear=0.3, dirt=0.9)
    for k in range(3):
        a0 = rnd.uniform(0, 6.28)
        cx, cy = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)
        pts = []
        for i in range(7):
            a = a0 + i / 6 * 1.1
            rr = 0.42 + 0.02 * math.sin(i * 2.3)
            pts.append((cx + math.cos(a) * rr * 0.6, cy + math.sin(a) * rr * 0.6, t + 0.04 + 0.006 * math.sin(i * 1.7)))
        tube(f"Crust{k}", pts, 0.045, crust)
        P.PARTS[-1].scale = (1, 1, 0.75)
    for k in range(8):
        sphere(f"Crumb{k}", rnd.uniform(0.012, 0.025), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), t + 0.012), crust, seg=6, rings=3)
    _xform(s, T(ox, oy, 0) @ RZ(-18 * DEG))
    return _dims()


def overdue_notices(M):
    K = kit(M)
    rnd = random.Random(3480)
    W, H = 3.6, 2.6
    zc = H / 2 + 0.1
    cork = material("Cork", "NH_Limestone", tint=(0.36, 0.22, 0.11), scale=1.6, normal=1.4, rough_add=0.2, wear=0.0, dirt=0.8)
    box("Cork", (W, 0.08, H), (0, -0.04, zc), cork, bevel=0.0)
    for nm, sz, loc in (("FrameT", (W + 0.24, 0.12, 0.12), (0, -0.06, zc + H / 2 + 0.06)), ("FrameB", (W + 0.24, 0.12, 0.12), (0, -0.06, zc - H / 2 - 0.06)),
                        ("FrameL", (0.12, 0.12, H), (-W / 2 - 0.06, -0.06, zc)), ("FrameR", (0.12, 0.12, H), (W / 2 + 0.06, -0.06, zc))):
        box(nm, sz, loc, K["iron"], bevel=0.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(f"Cap{sx}{sz}", (0.2, 0.03, 0.2), (sx * (W / 2 + 0.06), -0.13, zc + sz * (H / 2 + 0.06)), K["brass"], bevel=0.015)
            sphere(f"CapBoss{sx}{sz}", 0.04, (sx * (W / 2 + 0.06), -0.145, zc + sz * (H / 2 + 0.06)), K["brass"], seg=8, rings=4)
    box("Plate", (0.9, 0.02, 0.16), (0, -0.13, zc + H / 2 + 0.06), K["brass"], bevel=0.01)
    _text("PlateWord", "NOTICES", FONT, K["gilt"], lambda x, y, h: (x, -0.14 - h, zc + H / 2 + 0.06 + y), fit=(0.7, 0.1), depth=0.006, res=3)
    yb = -0.08
    layout = [("Notice_Overdue", 0.78, 1.03, -1.25, 0.2, -4, "crimson"), ("Notice_Final", 0.76, 1.0, -0.35, 0.25, 3, "brass"),
              ("Paper_Test", 0.76, 1.0, 0.6, 0.15, -2, "brass"), ("Notice_Detention", 0.66, 0.85, 1.35, 0.35, 6, "crimson"),
              ("Notice_Warning", 0.7, 0.91, -0.85, -0.55, 5, "brass"), ("Notice_SeeMe", 0.62, 0.45, 0.85, -0.6, -8, "crimson"),
              ("Notice_Overdue", 0.6, 0.79, 1.4, -0.65, 9, "brass")]
    K["crimson"] = flat("PinRed", (0.2, 0.012, 0.02), 0.3)
    for k, (key, w, h, x, z, a, pc) in enumerate(layout):
        y = yb - 0.008 * (k + 1)
        wall_sheet(f"N{k}", "DP_" + key, w, h, T(x, y, zc + z) @ RY(a * DEG), K["print"], curl=rnd.uniform(0.02, 0.05), rnd=rnd)
        tx = x + math.sin(a * DEG) * h * 0.45
        tz = zc + z + math.cos(a * DEG) * h * 0.45
        pin(f"Pin{k}", (tx, y - 0.01, tz), K, pc)
    _fine(0.6)
    return _dims()


def can(name, key, K, mtx, crush=0.0, seed=0):
    r, h = 0.12, 0.43
    rnd = random.Random(seed)
    seg, rows = 28, 12
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]

    def prof(z):
        t = z / h
        rr = r
        if t < 0.06:
            rr = r * (0.82 + 0.18 * t / 0.06)
        elif t > 0.88:
            rr = r * (1 - 0.22 * (t - 0.88) / 0.12)
        return rr

    def P_(a, z):
        rr = prof(z)
        t = z / h
        if crush:
            # buckled: squashed down, folds round the waist, pinched flat one way
            zz = z * (1 - crush * 0.55) + crush * 0.03 * math.sin(a * 3 + ph[0]) * math.sin(t * math.pi)
            fold = 1 + crush * 0.25 * math.sin(a * 5 + ph[1]) * math.sin(t * math.pi * 3 + ph[2])
            pinch = 1 - crush * 0.45 * math.sin(t * math.pi) * abs(math.cos(a + ph[3]))
            return Vector((math.cos(a) * rr * fold * pinch, math.sin(a) * rr * fold, zz))
        return Vector((math.cos(a) * rr, math.sin(a) * rr, z))
    grid = [[bm.verts.new(P_(i / seg * 2 * math.pi, h * j / rows)) for i in range(seg)] for j in range(rows + 1)]
    for j in range(rows):
        for i in range(seg):
            f = bm.faces.new((grid[j][i], grid[j][(i + 1) % seg], grid[j + 1][(i + 1) % seg], grid[j + 1][i]))
            f.smooth = True
            f[kl] = 1.8
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = region_uv(key, ii / seg, jj / rows)
    alu = swatch_uv("DP_alu")
    for ring, z in ((grid[0], 0), (grid[rows], h)):
        c = bm.verts.new(P_(0, z) * 0 + Vector((0, 0, ring[0].co.z if crush == 0 else sum(v.co.z for v in ring) / seg)))
        for i in range(seg):
            vs = (ring[i], ring[(i + 1) % seg], c) if z > 0 else (ring[(i + 1) % seg], ring[i], c)
            f = bm.faces.new(vs)
            f[kl] = 0.5
            for lp in f.loops:
                lp[uvl].uv = alu
    ob = mesh_obj(name, bm, K["print"])
    ob.matrix_world = mtx
    return ob


def empty_cans(M):
    K = kit(M)
    can("CanA", "DP_Can_Cola", K, T(-0.5, 0.1, 0), crush=0.85, seed=1)
    can("CanB", "DP_Can_Fizz", K, T(0.15, 0.35, 0.12) @ RX(math.pi / 2) @ RZ(0.4), crush=0.3, seed=2)
    can("CanC", "DP_Can_Moon", K, T(0.55, -0.25, 0), crush=0.0, seed=3)
    can("CanD", "DP_Can_Cola", K, T(-0.1, -0.4, 0.11) @ RZ(1.2) @ RX(math.pi / 2), crush=0.65, seed=4)
    for k, (x, y) in enumerate(((0.55, -0.25),)):
        box(f"Tab{k}", (0.05, 0.08, 0.006), (x, y - 0.02, 0.432), material("Tab", base=(0.7, 0.7, 0.72), rough=0.25, metal=1.0), bevel=0.0)
    _fine(0.35)
    return _dims()


# ================================================================== the room shell

WALL_W, WALL_H, WALL_T = 10.0, 12.0, 0.5
WAIN = 3.95                     # the rail's top
DOOR_HW, DOOR_H = 2.5, 8.0
WIN = dict(hw=1.35, z0=4.6, zs=8.3, za=10.0, ohw=2.05, oz0=4.3, oz1=10.7)


def wainscot(K, segments):
    """The wainscot along the wall's face (y = -WALL_T/2), over x ranges [(x0, x1), ...]: a black marble skirting, crimson
    enamel fields (the Panel piece, tiled) in iron stiles and rails, an iron rail with a brass cap."""
    yf = -WALL_T / 2
    for k, (x0, x1) in enumerate(segments):
        w, cx = x1 - x0, (x0 + x1) / 2
        set_group("Panel")
        box(f"Field{k}", (w, 0.04, 3.1), (cx, yf - 0.02, 0.5 + 1.55), K["iron"], bevel=0.0)
        set_group("Main")
        box(f"Skirt{k}", (w, 0.16, 0.5), (cx, yf - 0.08, 0.25), K["marble"], bevel=0.02)
        box(f"SkirtTop{k}", (w, 0.19, 0.06), (cx, yf - 0.095, 0.5), K["marble"], bevel=0.015)
        box(f"RailLow{k}", (w, 0.07, 0.24), (cx, yf - 0.075, 0.65), K["iron"], bevel=0.012)
        box(f"RailHigh{k}", (w, 0.07, 0.24), (cx, yf - 0.075, 3.48), K["iron"], bevel=0.012)
        box(f"Rail{k}", (w, 0.2, 0.3), (cx, yf - 0.1, 3.75), K["iron"], bevel=0.02)
        box(f"RailCap{k}", (w, 0.24, 0.06), (cx, yf - 0.12, WAIN - 0.03), K["brass"], bevel=0.015)
        tube(f"RailBead{k}", [(x0, yf - 0.205, 3.62), (x1, yf - 0.205, 3.62)], 0.018, K["brass"], poly=True)
        n = max(1, int(round(w / 2.5)))
        pw = w / n
        for i in range(n + 1):
            x = x0 + i * pw
            sw = 0.22
            xs = min(max(x, x0 + sw / 2), x1 - sw / 2)
            box(f"Stile{k}{i}", (sw, 0.07, 2.59), (xs, yf - 0.075, 2.065), K["iron"], bevel=0.012)
        for i in range(n):
            a, b = x0 + i * pw + 0.11 + 0.08, x0 + (i + 1) * pw - 0.11 - 0.08
            z0, z1 = 0.77 + 0.08, 3.36 - 0.08
            tube(f"Bead{k}{i}", [(a, yf - 0.045, z0), (b, yf - 0.045, z0), (b, yf - 0.045, z1), (a, yf - 0.045, z1)], 0.022, K["iron"], square=True, closed=True,
                 poly=True)
            foil(f"Boss{k}{i}", (a + b) / 2, yf - 0.05, z1 - 0.25, 0.1, K["brass"], lobes=4, thick=0.012)


def plaster_box(name, x0, x1, z0, z1, mat):
    set_group("Plaster")
    box(name, (x1 - x0, WALL_T, z1 - z0), ((x0 + x1) / 2, 0, (z0 + z1) / 2), mat, bevel=0.0)
    set_group("Main")


def dorm_wall(M, kind="plain"):
    K = kit(M)
    W, H = WALL_W, WALL_H
    pm = K["plaster"]
    if kind == "plain":
        plaster_box("Wall", -W / 2, W / 2, 0, H, pm)
        wainscot(K, [(-W / 2, W / 2)])
    elif kind == "door":
        plaster_box("WallL", -W / 2, -DOOR_HW, 0, H, pm)
        plaster_box("WallR", DOOR_HW, W / 2, 0, H, pm)
        plaster_box("Lintel", -DOOR_HW, DOOR_HW, DOOR_H, H, pm)
        wainscot(K, [(-W / 2, -DOOR_HW), (DOOR_HW, W / 2)])
        # an iron edge round the opening, where the door kit's frame meets the plaster
        for sx in (-1, 1):
            box(f"Jamb{sx}", (0.06, WALL_T + 0.06, DOOR_H), (sx * (DOOR_HW + 0.03), 0, DOOR_H / 2), K["iron"], bevel=0.01)
        box("Head", (2 * DOOR_HW + 0.12, WALL_T + 0.06, 0.06), (0, 0, DOOR_H + 0.03), K["iron"], bevel=0.01)
    else:
        w = WIN
        plaster_box("WallL", -W / 2, -w["ohw"], 0, H, pm)
        plaster_box("WallR", w["ohw"], W / 2, 0, H, pm)
        plaster_box("Below", -w["ohw"], w["ohw"], 0, w["oz0"], pm)
        plaster_box("Above", -w["ohw"], w["ohw"], w["oz1"], H, pm)
        wainscot(K, [(-W / 2, W / 2)])
        stone = soot_stone_mat()
        dark = soot_stone_mat(dark=True)
        hw, z0, zs, za = w["hw"], w["z0"], w["zs"], w["za"]
        oh, o0, o1 = w["ohw"], w["oz0"], w["oz1"]
        arch = WS.pointed(hw, zs, za, 16)
        left = [p for p in arch if p[0] <= 0]
        right = [p for p in arch if p[0] >= 0]
        polyL = [(-oh, o0), (0, o0), (0, z0), (-hw, z0)] + left + [(0, o1), (-oh, o1)]
        polyR = [(0, o0), (oh, o0), (oh, o1), (0, o1)] + list(reversed(right)) + [(hw, z0), (0, z0)]
        for nm, poly in (("SurroundL", polyL), ("SurroundR", polyR)):
            B20.tprism(nm, WS.ccw([(round(x, 5), round(z, 5)) for x, z in poly]), 0.0, WALL_T + 0.16, dark)
        # a chamfered reveal of paler stone round the opening, set back from the face
        rev = [(x, z) for x, z in WS.arch(hw + 0.12, z0, zs, za + 0.12, 16)]
        tube("Reveal", [(x, -WALL_T / 2 - 0.09, z) for x, z in rev[1:]] + [(rev[0][0], -WALL_T / 2 - 0.09, rev[0][1])], 0.07, stone, square=True, poly=True)
        # a hood moulding over the arch inside, a deep sill, a central iron mullion, diamond leading, the glass
        hood = [(x * 1.18, -WALL_T / 2 - 0.12, zs + (z - zs) * 1.12) for x, z in arch]
        tube("Hood", [(-hw * 1.18 - 0.25, -WALL_T / 2 - 0.12, zs - 0.05)] + hood + [(hw * 1.18 + 0.25, -WALL_T / 2 - 0.12, zs - 0.05)], 0.07, dark,
             square=True, poly=True)
        for sx in (-1, 1):
            box(f"Stop{sx}", (0.22, 0.2, 0.3), (sx * (hw * 1.18 + 0.3), -WALL_T / 2 - 0.12, zs - 0.15), dark, bevel=0.04)
        box("Sill", (2 * hw + 0.9, WALL_T + 0.5, 0.14), (0, -0.2, z0 - 0.07), dark, bevel=0.03)
        box("SillCorbel", (2 * hw + 0.5, 0.2, 0.2), (0, -WALL_T / 2 - 0.25, z0 - 0.24), dark, bevel=0.03)
        op = WS.arch(hw, z0, zs, za, 16)
        box("Mullion", (0.1, 0.12, zs - z0 + 0.6), (0, 0.0, (z0 + zs + 0.6) / 2), K["iron"], bevel=0.015)
        for z in (5.8, 7.0):
            box(f"Transom{z}", (2 * hw, 0.06, 0.05), (0, 0.0, z), K["iron"], bevel=0.008)
        for k, ((ax, az), (bx, bz)) in enumerate(WS.lattice_lines(op, 0.42, "diamond")):
            tube(f"Came{k}", [(ax, -0.035, az), (bx, -0.035, bz)], 0.012, K["ironf"], square=True, poly=True)
        foil("TopFoil", 0, -0.05, za - 0.6, 0.28, K["iron"], lobes=4, thick=0.02)
        tube("Frame", [(x, -0.04, z) for x, z in op] + [(op[0][0], -0.04, op[0][1])], 0.03, K["iron"], square=True, poly=True)
        set_group("Glass")
        B20.tprism("Pane", WS.ccw(op), 0.0, 0.02, K["glass"])
        set_group("Sky")
        B30.plate("Night", "DP_Sky", 2 * hw + 0.6, za - z0 + 0.5, 0.02, T(0, 0.55, (z0 + za) / 2), K["print"], edge="DP_ink", k=1.4)
        set_group("Main")
    return _dims()


def soot_stone_mat(dark=False):
    from nh_props_batch12 import soot_stone
    return soot_stone("DormStoneDk" if dark else "DormStone", (0.09, 0.095, 0.088) if dark else (0.15, 0.158, 0.148))


def dorm_floor(M):
    set_group("Main")
    box("Floor", (10.0, 10.0, 0.3), (0, 0, 0.15), M["stone"], bevel=0.0)
    return _dims()


def dorm_ceiling(M):
    K = kit(M)
    S = 10.0
    drop = 0.6
    set_group("Plaster")
    box("Slab", (S, S, 0.3), (0, 0, drop + 0.15), K["plaster"], bevel=0.0)
    set_group("Main")
    prof = [(0.66, drop), (0.62, drop - 0.03), (0.56, drop - 0.03), (0.54, drop - 0.07), (0.5, drop - 0.09), (0.46, drop - 0.1)]
    for k in range(9):
        a = k / 8 * math.pi / 2
        prof.append((0.06 + 0.4 * (1 - math.sin(a)), 0.1 + 0.4 * (1 - math.cos(a))))
    prof += [(0.05, 0.08), (0.03, 0.06), (0.03, 0.03), (0.0, 0.02), (0.0, 0.0)]
    moulding_loop("Cornice", S / 2, S / 2, prof, K["plaster"])
    hw = S / 2 - 0.5
    tube("Bead", [(-hw, -hw, drop - 0.085), (hw, -hw, drop - 0.085), (hw, hw, drop - 0.085), (-hw, hw, drop - 0.085)], 0.022, K["gilt"], closed=True, poly=True)
    hw = S / 2 - 0.035
    tube("Fillet", [(-hw, -hw, 0.045), (hw, -hw, 0.045), (hw, hw, 0.045), (-hw, hw, 0.045)], 0.015, K["gilt"], closed=True, poly=True)
    # the ceiling rose for the pendant
    lathe("Rose", [(0, drop - 0.3), (0.12, drop - 0.3), (0.16, drop - 0.26), (0.2, drop - 0.24), (0.35, drop - 0.2), (0.5, drop - 0.12), (0.62, drop - 0.1),
                   (0.75, drop - 0.06), (0.85, drop - 0.04), (0.95, drop - 0.02), (0.98, drop)], K["plaster"], seg=48)
    hoop("RoseRing", (0, 0, drop - 0.105), 0.62, "Z", K["gilt"], thick=0.02)
    hoop("RoseRingIn", (0, 0, drop - 0.235), 0.21, "Z", K["gilt"], thick=0.015)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        sphere(f"RoseBead{k}", 0.045, (math.cos(a) * 0.42, math.sin(a) * 0.42, drop - 0.17), K["gilt"], seg=8, rings=4)
    return _dims()


def room_plate(M, blank=False):
    K = kit(M)
    w, h, t = 1.2, 0.6, 0.06
    zc = h / 2
    box("Plate", (w, t, h), (0, -t / 2, zc), K["brassf"], bevel=0.02)
    tube("Border", [(-w / 2 + 0.06, -t - 0.004, zc - h / 2 + 0.06), (w / 2 - 0.06, -t - 0.004, zc - h / 2 + 0.06), (w / 2 - 0.06, -t - 0.004, zc + h / 2 - 0.06),
                    (-w / 2 + 0.06, -t - 0.004, zc + h / 2 - 0.06)], 0.012, K["gilt"], square=True, closed=True, poly=True)
    for sx in (-1, 1):
        sphere(f"Screw{sx}", 0.03, (sx * (w / 2 - 0.035), -t - 0.0, zc), K["ironf"], seg=10, rings=5, scale=(1, 0.45, 1))
        box(f"Slot{sx}", (0.04, 0.01, 0.008), (sx * (w / 2 - 0.035), -t - 0.013, zc), K["ink"], bevel=0.0)
    if not blank:
        _text("Number", "101", FONT, K["gilt"], lambda x, y, hh: (x, -t - hh, zc + y), fit=(w - 0.4, h - 0.22), depth=0.02, res=5)
    _fine(0.4)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "DormBed": lambda M: dorm_bed(M, False),
    "DormBedUnmade": lambda M: dorm_bed(M, True),
    "DormDesk": dorm_desk,
    "DormChair": dorm_chair,
    "DormWardrobe": lambda M: wardrobe(M, False),
    "DormWardrobeOpen": lambda M: wardrobe(M, True),
    "DormShelfFull": lambda M: dorm_shelf(M, 0),
    "DormShelfSparse": lambda M: dorm_shelf(M, 1),
    "DormShelfEmpty": lambda M: dorm_shelf(M, 2),
    "DormPlantHealthy": lambda M: dorm_plant(M, "healthy"),
    "DormPlantWilting": lambda M: dorm_plant(M, "wilting"),
    "DormPlantDead": lambda M: dorm_plant(M, "dead"),
    "DormDeskLamp": desk_lamp,
    "DormCeilingLight": ceiling_light,
    "DormRug": lambda M: B29.rug("DormRug", 6, 4),
    "CertificateHonourRoll": lambda M: certificate(M, "Cert_Honour", 1),
    "CertificateDeansList": lambda M: certificate(M, "Cert_Deans", 2),
    "CertificatePerfectAttendance": lambda M: certificate(M, "Cert_Attend", 3),
    "TrophyShelf": trophy_shelf,
    "JacketOnChair": jacket_on_chair,
    "DormBookStack": book_stack,
    "CoffeeCup": coffee_cup,
    "ClothesOnChair": clothes_on_chair,
    "PaperScatter": paper_scatter,
    "ClothesPile": clothes_pile,
    "PizzaBoxes": pizza_boxes,
    "OverdueNotices": overdue_notices,
    "EmptyCans": empty_cans,
    "DormWall": lambda M: dorm_wall(M, "plain"),
    "DormWallWindow": lambda M: dorm_wall(M, "window"),
    "DormWallDoor": lambda M: dorm_wall(M, "door"),
    "DormFloor": dorm_floor,
    "DormCeiling": dorm_ceiling,
    "RoomNumberPlate": lambda M: room_plate(M, False),
    "RoomNumberPlateBlank": lambda M: room_plate(M, True),
}
P.BUILD.update(BUILDERS)
for _n in ("DormWall", "DormWallWindow", "DormWallDoor"):
    P.TILED[f"{_n}_Plaster"] = ("NH_DormPlaster", 5.0)
    P.TILED[f"{_n}_Panel"] = ("NH_DormEnamel", 5.0)
P.TILED["DormFloor"] = ("NH_DormFloor", 5.0)
P.TILED["DormCeiling_Plaster"] = ("NH_DormPlaster", 5.0)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"DormDeskLamp": 1.3, "DormCeilingLight": 1.3, "CertificateHonourRoll": 1.25, "CertificateDeansList": 1.25,
                      "CertificatePerfectAttendance": 1.25, "RoomNumberPlate": 1.4, "RoomNumberPlateBlank": 1.4, "DormBookStack": 1.4,
                      "TrophyShelf": 1.0, "DormFloor": 1.0, "DormCeiling": 1.0})
B24.SMALL.update({"CoffeeCup": 1.6, "EmptyCans": 1.5, "PaperScatter": 1.05, "PizzaBoxes": 1.15, "DormBookStack": 1.6})
