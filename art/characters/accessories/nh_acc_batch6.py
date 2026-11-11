"""Accessories batch 6: civilian (Kit A 25-28).

  PocketWatch    a brass hunter-case pocket watch (engine-turned lid round a crescent-and-star cartouche, reeded band,
                 knurled crown, bow) on a short fob chain from a stitched leather fob tab at the right front of the
                 waist. It swings flat on the belly (Pendulum, lock "Z": side to side, never toward the body) and hangs
                 above the striding leg's reach (the leg's top corner rises out of the lower front to about z -0.75)
  Umbrellas      a lace parasol and a crook-handle umbrella (two items, one atlas), carried CLOSED in the right hand,
                 hanging like a cane (an open canopy would sweep through the head and hats as the arm swings). Held,
                 rigid; the tips stop short of the ground
  CandleLantern  a small wrought-iron and glass candle lantern held by its ring in the right hand: gothic lancet frets
                 over lit glass (emissive: the candle's glow and silhouette on the panes, glowing roof vents), a real
                 candle and flame inside (emissive); swings from the ring (Pendulum, never toward the leg). The game
                 adds a flickering light at the flame (layout/CandleLantern.extra.json)
  Scarves        long chunky knitted scarves wrapped once round the neck, both tails down the front (Tails, fore and
                 aft only, never toward the chest): crimson-and-black stripes and a soft grey-violet (two items, one
                 model, baked apart). The knit is real stockinette relief in the bake, driven by a per-vertex stitch
                 attribute ('knit': rows along the scarf, columns across it)
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch6 --gpu
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, crescent, rbox_sdf

HALF_PI = math.pi / 2


# ================================================================== shared helpers
def _mr(T, x, a, b, smooth_=True):
    """Map Range (clamped): a -> 0, b -> 1 (a > b inverts)"""
    if a > b:
        return T.math("SUBTRACT", 1.0, _mr(T, x, b, a, smooth_))
    n = T.node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP" if smooth_ else "LINEAR", clamp=True)
    n.inputs["From Min"].default_value = a
    n.inputs["From Max"].default_value = b
    T.L(x, n.inputs["Value"])
    return n.outputs["Result"]


def _pos(T, minus=(0, 0, 0)):
    """world position minus a point, as (x, y, z) sockets"""
    geo = T.node("ShaderNodeNewGeometry")
    vs = T.node("ShaderNodeVectorMath", operation="SUBTRACT")
    T.L(geo.outputs["Position"], vs.inputs[0]); vs.inputs[1].default_value = tuple(minus)
    sp = T.node("ShaderNodeSeparateXYZ"); T.L(vs.outputs["Vector"], sp.inputs["Vector"])
    return sp.outputs["X"], sp.outputs["Y"], sp.outputs["Z"]


def set_attr(ob, name, fn, kind="FLOAT_VECTOR"):
    """a per-vertex attribute from fn(index, world co)"""
    me = ob.data
    at = me.attributes.get(name) or me.attributes.new(name, kind, "POINT")
    W = ob.matrix_world
    for i, v in enumerate(me.vertices):
        val = fn(i, W @ v.co)
        if kind == "FLOAT_VECTOR":
            at.data[i].vector = val
        else:
            at.data[i].value = val


def star_pts(n, r1, r2, a0=HALF_PI, cx=0.0, cz=0.0):
    return [(cx + (r1 if i % 2 == 0 else r2) * math.cos(a0 + math.pi * i / n),
             cz + (r1 if i % 2 == 0 else r2) * math.sin(a0 + math.pi * i / n)) for i in range(2 * n)]


def lancet(xc, zb, zs, w):
    """a pointed (equilateral) gothic arch window outline: sides from zb to the springing zs, apex above"""
    R = w
    pts = [(xc - w / 2, zb), (xc + w / 2, zb), (xc + w / 2, zs)]
    for i in range(1, 8):   # right arc, centred on the left springer
        a = math.radians(60) * i / 8
        pts.append((xc - w / 2 + R * math.cos(a), zs + R * math.sin(a)))
    pts.append((xc, zs + R * math.sin(math.radians(60))))
    for i in range(7, 0, -1):   # left arc, centred on the right springer
        a = math.radians(60) * i / 8
        pts.append((xc + w / 2 - R * math.cos(a), zs + R * math.sin(a)))
    pts.append((xc - w / 2, zs))
    return ccw(pts)


def mesh_grid(name, P, mat, close_u=False, close_v=False, smooth_all=True):
    """a quad mesh from a point grid P[k][l]; close_u / close_v join the last row / column back to the first by
    DUPLICATED seam vertices (so per-vertex attributes can run on across the seam). Faces point outward when P runs
    counter-clockwise round the tube's centre as l grows."""
    K, L = len(P), len(P[0])
    verts = [P[k][l] for k in range(K) for l in range(L)]
    faces = []
    for k in range(K - 1):
        for l in range(L - 1):
            a, b, c, d = k * L + l, (k + 1) * L + l, (k + 1) * L + l + 1, k * L + l + 1
            faces.append([a, b, c, d])
    return A.mesh_from(name, verts, faces, mat, smooth_all=smooth_all)


def orient_out(ob, centre_fn):
    """flip the mesh if its faces point toward centre_fn(face centre) (the tube's axis)"""
    me = ob.data
    s = 0.0
    for p in me.polygons:
        c = p.center
        s += p.normal.dot(c - centre_fn(c))
    if s < 0:
        me.flip_normals()


def make_rig_idx(ob, bones, weight_fn):
    """nh_acc.make_rig with weight_fn(vertex index, world co) -> {bone: w}"""
    arm_d = bpy.data.armatures.new(f"{ob.name}Rig")
    arm = A._new_obj(f"{ob.name}Rig", arm_d)
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
    for v in ob.data.vertices:
        w = weight_fn(v.index, ob.matrix_world @ v.co)
        items = sorted(((b, x) for b, x in w.items() if x > 1e-4), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in items) or 1.0
        for b, x in items:
            groups[b].add([v.index], x / tot, "REPLACE")
    ob.parent = arm
    md = ob.modifiers.new("Armature", "ARMATURE"); md.object = arm
    return arm


def column_weights(co, n, col, hinge_z=None, falloff=0.9):
    """chain_rig's weighting of a point along ONE column (H<n>, C<n>_k)"""
    col = [Vector(p) for p in col]
    if hinge_z is not None and co.z >= hinge_z:
        return {f"H{n}": 1.0}
    seg_d = [(A._seg_dist(co, a, b), k) for k, (a, b) in enumerate(zip(col, col[1:]))]
    (dd, t), k = min(seg_d, key=lambda s: s[0][0])
    if t < 0.35 and k > 0:
        f = 0.5 - t / 0.7
        return {f"C{n}_{k}": f, f"C{n}_{k + 1}": 1 - f}
    if t < 0.35 and k == 0:
        f = (0.35 - t) / 0.35 * falloff
        return {f"H{n}": f, f"C{n}_1": 1 - f}
    if t > 0.65 and k + 1 < len(col) - 1:
        f = (t - 0.65) / 0.7
        return {f"C{n}_{k + 1}": 1 - f, f"C{n}_{k + 2}": f}
    return {f"C{n}_{k + 1}": 1.0}


def chain_bones(root, cols):
    bones = [("Root", Vector(root), Vector(root) + Vector((0, 0, 0.08)), None)]
    for n, col in enumerate(cols):
        col = [Vector(p) for p in col]
        bones.append((f"H{n}", col[0], col[0] + (col[1] - col[0]) * 0.25, "Root"))
        parent = f"H{n}"
        for k in range(len(col) - 1):
            nm = f"C{n}_{k + 1}"
            bones.append((nm, col[k], col[k + 1], parent))
            parent = nm
    return bones


def fine_chain(name, a, b, link_len, wire, mat):
    """a straight run of interlocking oval links from a to b: one link every 0.72 link lengths (each link threads its
    neighbours), alternate links turned 90 degrees"""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, math.ceil(d.length / (0.72 * link_len)) + 1)
    q = d.normalized().to_track_quat("Z", "Y")
    obs = []
    for k in range(n):
        p = a.lerp(b, k / (n - 1))
        bpy.ops.mesh.primitive_torus_add(major_radius=link_len * 0.5 - wire, minor_radius=wire, major_segments=10, minor_segments=5)
        ob = bpy.context.object
        ob.scale = (0.58, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        rot = q.to_matrix().to_4x4() @ Matrix.Rotation(HALF_PI, 4, "Y") @ Matrix.Rotation(HALF_PI if k % 2 else 0.0, 4, "X")
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
    return A._finish(ob, mat)


def extrude_holed(name, pts2d, depth, mat, frame_m, holes, bevel=0.0015, segments=1):
    """nh_acc.extrude_poly for an outline WITH holes that stay open (extrude_poly keeps the outline's own n-gon over the
    holes): the outline and the holes are triangle-filled together, the triangles inside the holes dropped, then the
    plate extruded along -Y and placed by frame_m"""
    bm = bmesh.new()
    loops = [pts2d] + list(holes)
    for lp in loops:
        vs = [bm.verts.new((x, 0, z)) for x, z in lp]
        for i in range(len(vs)):
            bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    bmesh.ops.triangle_fill(bm, use_beauty=True, edges=list(bm.edges))
    for fc in list(bm.faces):
        c = fc.calc_center_median()
        if any(A._inside((c.x, c.z), h) for h in holes) or not A._inside((c.x, c.z), pts2d):
            bm.faces.remove(fc)
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    nv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, -depth, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = A._new_obj(name, me)
    ob.data.transform(frame_m)
    for p in ob.data.polygons:
        p.use_smooth = False
    return A._finish(ob, mat, bevel, segments)


# ================================================================== materials
def mat_knit(name, rgb, stripe=None, rough=0.92, sheen=0.75, heather=0.14, fuzz_rgb=None):
    """chunky stockinette knit driven by the mesh's 'knit' attribute (x: rows along the scarf, y: stitch columns across
    it): rows of V stitches in the bump (two rounded yarn legs a stitch, a valley between them, a seam between the
    columns), yarn shading and wool fuzz in the colour. stripe = (rgb2, period, rows2): rows2 of every `period` rows in
    a second colour (the colour change follows the stitch rows, as knitted stripes do)"""
    m, T, bs = A._base(name)
    at = T.node("ShaderNodeAttribute"); at.attribute_name = "knit"; at.attribute_type = "GEOMETRY"
    sep = T.node("ShaderNodeSeparateXYZ"); T.L(at.outputs["Vector"], sep.inputs["Vector"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    afv = T.math("ABSOLUTE", T.math("SUBTRACT", T.math("FRACT", v), 0.5))
    c = T.math("ADD", u, T.math("MULTIPLY", afv, 0.95))           # the V: rows dip toward the column's centre
    fc = T.math("FRACT", c)
    leg = T.math("POWER", T.math("MAXIMUM", T.math("SINE", T.math("MULTIPLY", fc, math.pi)), 0.0), 0.6)
    valley = _mr(T, afv, 0.0, 0.11)
    seam = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", _mr(T, afv, 0.36, 0.5), 0.6))
    h = T.math("MULTIPLY", T.math("MULTIPLY", leg, T.math("ADD", 0.25, T.math("MULTIPLY", valley, 0.75))), seam)
    fz = T.node("ShaderNodeTexNoise"); fz.inputs["Scale"].default_value = 1.0; fz.inputs["Detail"].default_value = 10
    T.L(T.coord(520.0), fz.inputs["Vector"])
    ply = T.node("ShaderNodeTexNoise"); ply.inputs["Scale"].default_value = 1.0; ply.inputs["Detail"].default_value = 3
    T.L(T.coord(60.0), ply.inputs["Vector"])
    base = A._rgb(T, rgb)
    if stripe:
        rgb2, period, rows2 = stripe
        band = T.math("LESS_THAN", T.math("MODULO", T.math("FLOOR", T.math("ADD", c, 1000.0)), period), rows2)
        base = T.mix(band, base, rgb2)
    col = T.mix(heather, base, ply.outputs["Color"], "OVERLAY")
    lite = T.mix(1.0, col, (1.55, 1.55, 1.55), "MULTIPLY")
    col = T.mix(T.math("MULTIPLY", fz.outputs["Fac"], 0.25), col, lite, "MIX")
    shade = T.math("ADD", 0.38, T.math("MULTIPLY", h, 0.62))
    col = T.mix(1.0, col, shade, "MULTIPLY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.7; bp.inputs["Distance"].default_value = 0.014
    T.L(T.math("ADD", h, T.math("MULTIPLY", fz.outputs["Fac"], 0.22)), bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = sheen
    bs.inputs["Sheen Roughness"].default_value = 0.5
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", fz.outputs["Fac"], 0.5), 0.08))
    A._weather(T, bs, col, r, A._val(T, 0.0), bp.outputs["Normal"], 0.03, False, 0.55, 0.006)
    return m


def mat_watch_brass(name, C, y_lid, rgb=(0.80, 0.58, 0.27)):
    """the watch case's brass: polished, with the lid's engine turning (a barleycorn guilloche in a ring round the
    cartouche), a coin-reeded band, tarnish in the cuts. C = the watch's axis (x, z used), y_lid = the lid seam"""
    m, T, bs = A._base(name)
    dx, py, dz = _pos(T, (C[0], 0.0, C[2]))
    r = T.math("SQRT", T.math("ADD", T.math("MULTIPLY", dx, dx), T.math("MULTIPLY", dz, dz)))
    ang = T.math("ARCTAN2", dz, dx)
    g1 = T.math("SINE", T.math("ADD", T.math("MULTIPLY", ang, 28.0), T.math("MULTIPLY", r, 190.0)))
    g2 = T.math("SINE", T.math("SUBTRACT", T.math("MULTIPLY", ang, 28.0), T.math("MULTIPLY", r, 190.0)))
    guil = T.math("MULTIPLY", T.math("MULTIPLY", T.math("ADD", g1, 1.0), T.math("ADD", g2, 1.0)), 0.25)
    lid = _mr(T, py, y_lid + 0.002, y_lid - 0.003)
    zone = T.math("MULTIPLY", _mr(T, r, 0.033, 0.038), _mr(T, r, 0.083, 0.078))
    engr = T.math("MULTIPLY", T.math("MULTIPLY", lid, zone), guil)
    rings = T.math("MULTIPLY", T.math("MULTIPLY", lid, _mr(T, r, 0.088, 0.092)),
                   T.math("MULTIPLY", _mr(T, r, 0.099, 0.095), 0.8))   # a polished double rule outside the guilloche
    reed = T.math("MULTIPLY", T.math("MULTIPLY", T.math("SUBTRACT", 1.0, lid), _mr(T, r, 0.100, 0.105)),
                  T.math("ADD", 0.5, T.math("MULTIPLY", T.math("SINE", T.math("MULTIPLY", ang, 150.0)), 0.5)))
    wv = T.node("ShaderNodeTexNoise"); wv.inputs["Scale"].default_value = 1.0; wv.inputs["Detail"].default_value = 3
    T.L(T.coord((70.0, 70.0, 700.0)), wv.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    T.L(T.coord(40.0), nz.inputs["Vector"])
    tarn = T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.45), 2.0, clamp=True)
    cut = T.math("SUBTRACT", 1.0, engr)   # the bottoms of the cuts
    col = T.mix(T.math("MULTIPLY", tarn, 0.3), A._rgb(T, rgb), (0.16, 0.12, 0.07), "MIX")
    col = T.mix(T.math("MULTIPLY", T.math("MULTIPLY", cut, T.math("MULTIPLY", lid, zone)), 0.55), col, (0.30, 0.21, 0.09), "MIX")
    rgh = T.math("ADD", 0.24, T.math("MULTIPLY", T.math("SUBTRACT", wv.outputs["Fac"], 0.5), 0.10))
    rgh = T.math("ADD", rgh, T.math("MULTIPLY", T.math("ADD", tarn, T.math("MULTIPLY", cut, T.math("MULTIPLY", lid, zone))), 0.14))
    hgt = T.math("ADD", T.math("ADD", T.math("MULTIPLY", engr, 1.0), T.math("MULTIPLY", rings, 0.6)),
                 T.math("ADD", T.math("MULTIPLY", reed, 0.8), T.math("MULTIPLY", wv.outputs["Fac"], 0.08)))
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.45; bp.inputs["Distance"].default_value = 0.0025
    T.L(hgt, bp.inputs["Height"])
    A._weather(T, bs, col, rgh, A._val(T, 1.0), bp.outputs["Normal"], 0.45, True, 0.8, 0.005)
    return m


def mat_lace(name, rgb, ground=(0.014, 0.012, 0.017), scale=1.0):
    """machine lace laid over dark silk: a fine hexagonal net (Voronoi cell edges), rosettes and dots (a coarser
    Voronoi), the holes showing the dark ground. World coordinates (it is baked)"""
    m, T, bs = A._base(name)
    geo = T.node("ShaderNodeNewGeometry")
    vn = T.node("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE"); vn.inputs["Scale"].default_value = 85.0 * scale
    T.L(geo.outputs["Position"], vn.inputs["Vector"])
    net = _mr(T, vn.outputs["Distance"], 0.07, 0.03)
    vm = T.node("ShaderNodeTexVoronoi", feature="F1"); vm.inputs["Scale"].default_value = 16.0 * scale
    vm.inputs["Randomness"].default_value = 0.35
    T.L(geo.outputs["Position"], vm.inputs["Vector"])
    d = vm.outputs["Distance"]
    ring = _mr(T, T.math("ABSOLUTE", T.math("SUBTRACT", d, 0.30)), 0.06, 0.025)
    dot = _mr(T, d, 0.13, 0.08)
    petal = T.math("MULTIPLY", _mr(T, d, 0.26, 0.18), _mr(T, d, 0.12, 0.17))
    thread = T.math("MAXIMUM", T.math("MAXIMUM", net, ring), T.math("MAXIMUM", dot, T.math("MULTIPLY", petal, 0.85)))
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    T.L(T.coord(300.0), nz.inputs["Vector"])
    col = T.mix(thread, ground, rgb)
    col = T.mix(0.08, col, nz.outputs["Color"], "OVERLAY")
    r = T.math("ADD", 0.38, T.math("MULTIPLY", thread, 0.42))
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.003
    T.L(thread, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 0.4
    A._weather(T, bs, col, r, A._val(T, 0.0), bp.outputs["Normal"], 0.02, False, 0.4, 0.004)
    return m


def mat_litglass(name, flame, core=(1.0, 0.70, 0.34), rim=(0.40, 0.13, 0.03), soot=(0.20, 0.07, 0.02)):
    """the lantern's glass, lit from within: an emissive pane (Roblox SurfaceAppearance is opaque) showing the flame's
    halo, the candle's shadow below it, soot at the top and seedy bubbles; brightest level with the flame"""
    m, T, bs = A._base(name)
    dx, dy, dz = _pos(T, flame)
    h = T.math("MINIMUM", T.math("ABSOLUTE", dx), T.math("ABSOLUTE", dy))    # across the pane (front panes x, side y)
    d = T.math("SQRT", T.math("ADD", T.math("MULTIPLY", h, h), T.math("MULTIPLY", T.math("MULTIPLY", dz, dz), 0.55)))
    halo = _mr(T, d, 0.17, 0.012)
    col = T.mix(halo, rim, core)
    cand = T.math("MULTIPLY", _mr(T, h, 0.05, 0.034), _mr(T, dz, -0.035, -0.06))   # the candle's shadow
    col = T.mix(T.math("MULTIPLY", cand, 0.55), col, (0.30, 0.10, 0.025))
    top = _mr(T, dz, 0.10, 0.16)                                                   # soot under the roof
    col = T.mix(T.math("MULTIPLY", top, 0.7), col, soot)
    vb = T.node("ShaderNodeTexVoronoi", feature="F1"); vb.inputs["Scale"].default_value = 140.0
    geo = T.node("ShaderNodeNewGeometry"); T.L(geo.outputs["Position"], vb.inputs["Vector"])
    bub = _mr(T, vb.outputs["Distance"], 0.16, 0.08)
    col = T.mix(T.math("MULTIPLY", bub, 0.35), col, core, "SCREEN")
    T.L(col, bs.inputs["Base Color"])
    T.L(col, bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 4.0
    bs.inputs["Roughness"].default_value = 0.08
    m["nh_glow"] = list(core)
    return m


# ================================================================== 25. the pocket watch
WATCH_X = -0.50            # the right front of the waist (the left hip belongs to the sheathed katana)
WATCH_Z = -0.602           # the case centre: its bottom (-0.707) stays above the striding leg's front corner
WATCH_BACK = -0.5015       # the case back, on the belly
WATCH_R = 0.105
CLASP = Vector((WATCH_X, -0.5255, -0.345))


def _watch_rig(ob):
    return A.pendulum_rig(ob, CLASP, [Vector((WATCH_X, -0.5445, -0.474)), Vector((WATCH_X, -0.5445, WATCH_Z - WATCH_R))])


@item("PocketWatch", "Brass pocket watch", views=["front34", "front", "side_r", "close"],
      close=((-1.9, -4.3, -0.25), (WATCH_X, -0.55, -0.48), 125))
def build_watch(M):
    C = Vector((WATCH_X, WATCH_BACK, WATCH_Z))
    y_lid = WATCH_BACK - 0.051
    brass = mat_watch_brass("WatchBrass", C, y_lid)
    bright = A.mat_metal("WatchGilt", (0.92, 0.70, 0.34), rough=0.20, scratch=0.25, wear=0.3)
    chainm = A.mat_metal("FobChain", (0.74, 0.54, 0.25), rough=0.28, scratch=0.4)
    fob = A.mat_leather("FobLeather", (0.11, 0.035, 0.035), scale=3.0, wear=0.55)
    thread = A.mat_flat("FobThread", (0.62, 0.52, 0.36), rough=0.8, noise=300, bump=0.2, vary=0.1, wear=0.0)
    piece("PocketWatch", "Torso", rig=_watch_rig, sway="Pendulum", keepout=(0, 1, 0), lock="Z")
    # the hunter case: domed back, reeded band, the lid seam, the domed engine-turned lid (lathe about the watch's axis)
    prof = [(0.0, 0.0), (0.03, 0.0008), (0.06, 0.003), (0.085, 0.008), (0.099, 0.014), (0.1045, 0.022), (0.105, 0.030),
            (0.105, 0.046), (0.106, 0.0475), (0.1015, 0.0505), (0.104, 0.0525), (0.104, 0.058), (0.099, 0.066),
            (0.088, 0.0735), (0.068, 0.0795), (0.045, 0.083), (0.02, 0.0846), (0.0, 0.085)]
    A.lathe("WatchCase", prof, C, brass, seg=56, rot=(HALF_PI, 0, 0))
    y_front = WATCH_BACK - 0.085
    # the lid's cartouche: a raised oval with the school's crescent and star
    F = frame((WATCH_X, y_front + 0.0015, WATCH_Z))
    oval = [(0.033 * math.cos(2 * math.pi * i / 28), 0.039 * math.sin(2 * math.pi * i / 28)) for i in range(28)]
    extrude_holed("WatchCartouche", ccw(oval), 0.004, bright, F, [ccw(offset_poly(oval, 0.004))[::-1]], bevel=0.0012)
    A.extrude_poly("WatchMoon", crescent(-0.004, -0.004, 0.021, 0.010, 0.006, 0.017), 0.006, bright, F, bevel=0.0, segments=1)
    A.extrude_poly("WatchStar", ccw(star_pts(5, 0.0085, 0.0036, cx=0.012, cz=0.014)), 0.0065, bright, F, bevel=0.0, segments=1)
    # beads round the guilloche, on the dome
    for k in range(18):
        a = 2 * math.pi * k / 18
        rr = 0.0905
        hh = 0.0735 - (rr - 0.088) * 0.3
        A.sphere(f"WatchBead{k}", 0.0042, (WATCH_X + rr * math.cos(a), WATCH_BACK - hh - 0.0025, WATCH_Z + rr * math.sin(a)),
                 bright, seg=6, rings=3)
    # the lid hinge (character's right, the viewer's left) and the lid's catch lip
    A.cyl("WatchHinge", 0.0085, 0.064, (WATCH_X - 0.1045, y_lid + 0.001, WATCH_Z), brass, verts=10, bevel=0.0015)
    for dz in (-0.011, 0.011):
        A.cyl(f"WatchKnuckle{dz}", 0.0092, 0.004, (WATCH_X - 0.1045, y_lid + 0.001, WATCH_Z + dz), bright, verts=10, bevel=0.0)
    A.box("WatchCatch", (0.010, 0.007, 0.022), (WATCH_X + 0.106, y_lid - 0.001, WATCH_Z), bright, bevel=0.002)
    # pendant, knurled crown, bow
    yc = WATCH_BACK - 0.044
    top = WATCH_Z + WATCH_R
    A.cyl("WatchNeck", 0.0115, 0.020, (WATCH_X, yc, top + 0.006), brass, verts=14)
    knurl = star_pts(14, 0.0205, 0.0182)
    A.extrude_poly("WatchCrown", ccw(knurl), 0.022, bright, frame((WATCH_X, yc, top + 0.014), (-HALF_PI, 0, 0)),
                   bevel=0.0, segments=1)
    A.sphere("WatchCrownCap", 0.0175, (WATCH_X, yc, top + 0.036), bright, scale=(1, 1, 0.45), seg=14, rings=6)
    bc = Vector((WATCH_X, yc, top + 0.030))
    arc = [tuple(bc + Vector((0.033 * math.cos(math.radians(a)), 0, 0.033 * math.sin(math.radians(a)))))
           for a in range(-28, 210, 8)]
    A.tube("WatchBow", arc, 0.0068, brass, res=8, poly=True)
    A.cyl("WatchBowPin", 0.0042, 0.062, (WATCH_X, yc, top + 0.0145), bright, rot=(0, HALF_PI, 0), verts=8, bevel=0.0)
    for s in (-1, 1):
        A.sphere(f"WatchBowPivot{s}", 0.0085, (WATCH_X + s * 0.0285, yc, top + 0.0145), bright, seg=8, rings=6)
    # the fob: a stitched oxblood leather tab clipped over the waistband, a brass snap, a D-ring, a bolt-ring clasp, chain
    tab = ccw([(-0.032, 0.055), (0.032, 0.055), (0.032, -0.030), (0.0, -0.052), (-0.032, -0.030)])
    Ft = frame((WATCH_X, -0.5025, -0.255))
    A.extrude_poly("FobTab", tab, 0.010, fob, Ft, bevel=0.002, segments=1)
    st = offset_poly(tab, 0.0075)
    A.tube("FobStitch", [tuple(Ft @ Vector((x, -0.0105, z))) for x, z in st] + [tuple(Ft @ Vector((st[0][0], -0.0105, st[0][1])))],
           0.0018, thread, res=3, poly=True)
    A.cyl("FobFold", 0.0075, 0.066, (WATCH_X, -0.5085, -0.199), fob, rot=(0, HALF_PI, 0), verts=12)
    A.sphere("FobSnap", 0.0115, (WATCH_X, -0.5135, -0.226), brass, scale=(1, 0.45, 1), seg=14, rings=8)
    A.torus("FobRing", 0.0185, 0.0052, (WATCH_X, -0.516, -0.318), brass, rot=(HALF_PI, 0, 0), major=16, minor=6)
    A.torus("FobClasp", 0.0155, 0.0050, (CLASP.x, CLASP.y, CLASP.z), bright, rot=(0, HALF_PI, 0), major=16, minor=6)
    A.sphere("FobTrigger", 0.0048, (WATCH_X - 0.011, CLASP.y, CLASP.z + 0.015), bright, seg=8, rings=5)
    fine_chain("WatchChain", (WATCH_X, -0.5295, CLASP.z - 0.012), (WATCH_X, -0.5365, top + 0.066), 0.024, 0.0042, chainm)
    return dict(notes="a brass hunter-case pocket watch: engine-turned lid round a crescent-and-star cartouche, reeded "
                      "band, knurled crown and bow, on a short fob chain from a stitched oxblood fob tab at the right "
                      "front of the waist; swings flat on the belly (lock Z) on a 2-bone chain")


# ================================================================== 26. parasol and crook umbrella
HAND_X = -1.5


def furled(name, x, y, z0, z1, rmax, gores, mat, twist=1.4, seg=48, rows=34, shaft=0.013, fat=0.16, taper=0.85):
    """a furled canopy: silk gathered round the shaft in `gores` folds, spiralled by `twist`, fat just below the rib tips
    (the top, z0, toward the handle) and tapering to the top notch (z1, toward the tip). Returns radius(t, theta)."""
    def rad(t, th):
        r = lerp(0.50, 1.0, smooth(0.0, fat, t)) * lerp(1.0, 0.16, ((t - fat) / (1 - fat)) ** taper if t > fat else 0.0) * rmax
        amp = 0.17 * smooth(0.0, 0.08, t) * (1 - smooth(0.88, 1.0, t))
        s = math.cos(gores * (th + twist * t))
        ridge = math.copysign(abs(s) ** 0.55, s)
        return r * (1 + 0.5 * amp * ridge)
    P = []
    for j in range(rows + 1):
        t = j / rows
        z = lerp(z0, z1, t)
        P.append([Vector((x + rad(t, th) * math.cos(th), y + rad(t, th) * math.sin(th), z))
                  for th in (2 * math.pi * s / seg for s in range(seg + 1))])
    lip = [Vector((x + shaft * math.cos(th), y + shaft * math.sin(th), z0 + 0.006)) for th in (2 * math.pi * s / seg for s in range(seg + 1))]
    end = [Vector((x + shaft * 0.8 * math.cos(th), y + shaft * 0.8 * math.sin(th), z1 - 0.004)) for th in (2 * math.pi * s / seg for s in range(seg + 1))]
    ob = mesh_grid(name, [lip] + P + [end], mat)
    orient_out(ob, lambda c: Vector((x, y, c.z)))
    return rad


def ruffle(name, x, y, z0, z1, r0, r1, n, mat, scallops=None, samples=96, rows=4, amp=0.014, thick=0.0035):
    """a gathered lace ruffle round the canopy: from radius r0 at z0 flaring to r1 at z1, gathered in n ruffles, the
    lower edge scalloped"""
    scallops = scallops or n * 2
    G = []
    for i in range(samples + 1):
        th = 2 * math.pi * i / samples
        col = []
        for j in range(rows + 1):
            t = j / rows
            r = lerp(r0, r1, t ** 0.8) + amp * math.sin(n * th) * t
            z = lerp(z0, z1, t) + (0.010 * abs(math.sin(scallops * th / 2)) * smooth(0.6, 1.0, t))
            col.append(Vector((x + r * math.cos(th), y + r * math.sin(th), z)))
        G.append(col)
    return A.surface(name, G, thick, mat, caps=False)


@item("Umbrellas", "Lace parasol and crook umbrella", views=["front34", "front", "side_r", "back", "close"],
      close=((-4.8, -5.2, -1.0), (HAND_X, 0, -1.75), 62), each=True)
def build_umbrellas(M):
    silk = A.mat_cloth("UmbrellaSilk", (0.016, 0.015, 0.019), weave=520, rough=0.38, sheen=0.55, bump=0.04, twill=True)
    psilk = A.mat_cloth("ParasolSilk", (0.030, 0.012, 0.040), weave=600, rough=0.34, sheen=0.7, bump=0.03, twill=False)
    lace = mat_lace("ParasolLace", (0.84, 0.81, 0.72), ground=(0.030, 0.012, 0.040))
    satin = A.mat_cloth("ParasolSatin", (0.20, 0.06, 0.32), weave=700, rough=0.28, sheen=0.6, bump=0.02, twill=False)
    wood = A.mat_set("CrookWood", "NH_DeskWood", tint=(0.42, 0.24, 0.15), scale=5.0, wear=0.35, dirt=0.5)
    ebony = A.mat_flat("Ebony", (0.022, 0.016, 0.014), rough=0.22, noise=120, bump=0.02, vary=0.05, wear=0.2, coat=0.4)
    strapl = A.mat_leather("UmbrellaStrap", (0.05, 0.045, 0.05), scale=3.5)

    # ---- the crook umbrella: a black silk canopy furled with its strap and button, a dark wood crook, silver collar,
    # steel ferrule; the crook hooked under the hand, the tip 0.14 off the ground
    piece("CrookUmbrella", "RightArm")
    x, y = HAND_X, 0.0
    R, rt = 0.088, 0.029
    zc = -1.0 - 0.006 - rt - R
    pts = [(x, 0.088 + R * math.cos(math.radians(a)), zc + R * math.sin(math.radians(a))) for a in range(-64, 181, 7)]
    pts = pts[::-1]   # from the front (the shaft) over the top to the curled end behind
    A.tube("CrookHandle", [(x, 0.0, -1.30)] + [(x, 0.0, zc - 0.06)] + pts, rt, wood, res=12, poly=True,
           taper=lambda t: lerp(1.04, 0.86, smooth(0.5, 1.0, t)))
    end = Vector(pts[-1])
    A.sphere("CrookEnd", rt * 0.92, end + Vector((0, -0.004, -0.004)), wood, seg=12, rings=8)
    A.lathe("CrookCollar", [(0.0, 0.0), (0.033, 0.0), (0.036, 0.008), (0.033, 0.016), (0.036, 0.026), (0.034, 0.036),
                            (0.0, 0.036)], (x, y, -1.318), M["silver"], seg=24)
    A.cyl("CrookShaft", 0.012, 0.10, (x, y, -1.36), M["steel"], verts=12)
    z0, z1 = -1.40, -2.585
    rad = furled("CrookCanopy", x, y, z0, z1, 0.088, 8, silk, twist=1.3, seg=48, rows=34, fat=0.10, taper=1.15)
    for k in range(8):   # the rib tips, gathered round the top of the furl
        th = 2 * math.pi * k / 8 + 0.35
        rr = rad(0.02, th) * 0.92
        A.cyl(f"CrookTip{k}", 0.0062, 0.026, (x + rr * math.cos(th), y + rr * math.sin(th), z0 + 0.008), M["steel"],
              verts=6, r2=0.0038, bevel=0.0)
    A.cyl("CrookRunner", 0.019, 0.022, (x, y, z0 + 0.018), M["steel"], verts=14)
    ts = 0.42
    zs = lerp(z0, z1, ts)
    rb = max(rad(ts, 2 * math.pi * s / 64) for s in range(64)) + 0.003
    A.lathe("CrookStrap", [(rb - 0.004, 0.019), (rb + 0.005, 0.016), (rb + 0.006, -0.016), (rb - 0.004, -0.019)],
            (x, y, zs), strapl, seg=40)
    A.sphere("CrookButton", 0.014, (x, y - rb - 0.008, zs), M["silver"], scale=(1, 0.45, 1), seg=12, rings=8)
    A.extrude_poly("CrookStrapEnd", ccw([(-0.02, 0.016), (0.02, 0.016), (0.03, 0.0), (0.02, -0.016), (-0.02, -0.016)]),
                   0.007, strapl, frame((x, y - rb - 0.0005, zs)), bevel=0.0015, segments=1)
    A.lathe("CrookFerrule", [(0.0, 0.0), (0.0145, 0.0), (0.012, -0.12), (0.0095, -0.24), (0.011, -0.25), (0.011, -0.262),
                             (0.0, -0.266)], (x, y, z1 + 0.006), M["steel"], seg=14)

    # ---- the lace parasol: a black-violet silk canopy furled under two tiers of ivory lace ruffles, a violet satin bow,
    # a carved bone crook with a gilt collar and a silk tassel, an ebony shaft and a bone finial
    piece("LaceParasol", "RightArm")
    R, rt = 0.062, 0.020
    zc = -1.0 - 0.006 - rt - R
    pts = [(x, 0.062 + R * math.cos(math.radians(a)), zc + R * math.sin(math.radians(a))) for a in range(-70, 181, 7)]
    pts = pts[::-1]
    A.tube("ParasolHandle", [(x, 0.0, -1.19), (x, 0.0, zc - 0.03)] + pts, rt, M["bone"], res=10, poly=True,
           taper=lambda t: lerp(1.0, 0.8, smooth(0.4, 1.0, t)))
    A.sphere("ParasolHandleEnd", rt * 0.95, Vector(pts[-1]) + Vector((0, -0.002, -0.004)), M["gold"], seg=12, rings=8)
    for k, z in enumerate((zc - 0.006, zc - 0.022)):   # carved rings on the bone grip
        A.torus(f"ParasolGripRing{k}", rt * 1.02, 0.0045, (x, 0.0, z), M["bone"], major=16, minor=5)
    A.lathe("ParasolCollar", [(0.0, 0.0), (0.024, 0.0), (0.028, 0.010), (0.022, 0.02), (0.027, 0.034), (0.021, 0.046),
                              (0.0, 0.046)], (x, y, -1.235), M["gold"], seg=24)
    A.cyl("ParasolShaft", 0.0105, 0.25, (x, y, -1.355), ebony, verts=12)
    # the tassel: a silk cord from the collar to a tassel hanging on the outer side
    A.tube("TasselCord", [(x - 0.022, 0.0, -1.205), (x - 0.045, 0.0, -1.235), (x - 0.050, 0.0, -1.27)], 0.004, satin, res=4)
    A.sphere("TasselHead", 0.014, (x - 0.050, 0.0, -1.278), satin, scale=(1, 1, 1.25), seg=12, rings=8)
    G = []
    for i in range(25):
        th = 2 * math.pi * i / 24
        col = []
        for j in range(5):
            t = j / 4
            rr = lerp(0.010, 0.020, t) * (1 + 0.25 * abs(math.sin(6 * th)) * t)
            col.append(Vector((x - 0.050 + rr * math.cos(th), rr * math.sin(th), lerp(-1.283, -1.375, t))))
        G.append(col)
    A.surface("TasselSkirt", G, 0.003, satin, caps=False)
    z0, z1 = -1.47, -2.29
    rad = furled("ParasolCanopy", x, y, z0, z1, 0.068, 10, psilk, twist=0.9, seg=44, rows=24, fat=0.10, taper=1.25)
    ruffle("ParasolRuffleTop", x, y, z0 + 0.012, z0 - 0.10, 0.034, 0.122, 13, lace, samples=84, rows=4, amp=0.013)
    zr = lerp(z0, z1, 0.30)
    rr0 = max(rad(0.30, 2 * math.pi * s / 64) for s in range(64))
    ruffle("ParasolRuffleMid", x, y, zr + 0.01, zr - 0.075, rr0 + 0.002, rr0 + 0.058, 12, lace, samples=72, rows=3, amp=0.010)
    A.cyl("ParasolRunner", 0.017, 0.02, (x, y, z0 + 0.016), M["gold"], verts=14)
    # the satin bow tied round the furl
    tb = 0.55
    zb = lerp(z0, z1, tb)
    rb = max(rad(tb, 2 * math.pi * s / 64) for s in range(64)) + 0.002
    A.lathe("ParasolBowBand", [(rb - 0.003, 0.012), (rb + 0.004, 0.010), (rb + 0.004, -0.010), (rb - 0.003, -0.012)],
            (x, y, zb), satin, seg=36)
    yb = y - rb - 0.012
    for s in (-1, 1):
        A.sphere(f"ParasolBowLoop{s}", 0.03, (x + s * 0.030, yb - 0.002, zb + 0.004), satin, scale=(1.15, 0.38, 0.62), seg=14, rings=8)
        A.extrude_poly(f"ParasolBowTail{s}", ccw([(-0.013, 0.0), (0.013, 0.0), (0.017, -0.11), (0.0, -0.092), (-0.017, -0.11)]),
                       0.005, satin, frame((x + s * 0.012, yb + 0.006, zb - 0.008), (0, math.radians(s * 14), 0)), bevel=0.0015, segments=1)
    A.sphere("ParasolBowKnot", 0.014, (x, yb - 0.006, zb), satin, scale=(1, 0.75, 1.1), seg=12, rings=8)
    A.lathe("ParasolFerrule", [(0.0, 0.0), (0.011, 0.0), (0.0085, -0.13), (0.0075, -0.18), (0.0, -0.185)],
            (x, y, z1 + 0.006), M["gold"], seg=12)
    A.sphere("ParasolFinial", 0.0135, (x, y, z1 - 0.185), M["bone"], scale=(1, 1, 1.3), seg=12, rings=8)
    return dict(notes="carried closed in the right hand like a cane (an open canopy would sweep through the head and "
                      "hats as the arm swings): a black silk umbrella with a dark wood crook, silver collar, strap and "
                      "steel ferrule; a black-violet silk parasol under two tiers of ivory lace, a violet satin bow, a "
                      "carved bone crook with a gilt collar and a silk tassel")


# ================================================================== 27. the candle lantern
LX, LY = HAND_X, 0.0
FLAME = Vector((LX, LY, -1.452))
L_PIVOT = Vector((LX, LY, -1.125))


def _lantern_rig(ob):
    return A.pendulum_rig(ob, L_PIVOT, [Vector((LX, LY, -1.27)), Vector((LX, LY, -1.685))])


def _lantern_render(objs, cam, man):
    A.shoot(cam, f"{A.OUT}/renders/CandleLantern_lit.png", (-3.2, -3.6, -0.9), target=(LX, 0, -1.42), lens=110)


@item("CandleLantern", "Candle lantern", views=["front34", "front", "side_r", "close"],
      close=((-3.9, -4.4, -0.7), (LX, 0, -1.38), 92), render=_lantern_render)
def build_lantern(M):
    iron = A.mat_set("LanternIron", "NH_Iron", tint=(0.085, 0.08, 0.088), scale=2.2, wear=0.55, wear_metal=True, dirt=0.8)
    brass = M["brassold"]
    glass = mat_litglass("LanternGlass", tuple(FLAME))
    flame = A.mat_glow("LanternFlame", (1.0, 0.58, 0.20))
    vent = A.mat_glow("LanternVent", (0.95, 0.42, 0.10))
    wax = A.mat_flat("LanternWax", (0.86, 0.80, 0.66), rough=0.42, noise=40, bump=0.05, vary=0.06, wear=0.0, dirt=0.7)
    soot = A.mat_flat("Wick", (0.02, 0.018, 0.016), rough=0.9, noise=80)
    piece("CandleLantern", "RightArm", rig=_lantern_rig, sway="Pendulum", keepout=(1, 0, 0))
    # the ring (held in the hand) and the eye it hangs from
    A.torus("LanternRing", 0.050, 0.011, (LX, LY, -1.0 - 0.004 - 0.061), iron, rot=(HALF_PI, 0, 0), major=28, minor=8)
    A.torus("LanternEye", 0.017, 0.0058, (LX, LY, -1.128), iron, rot=(0, HALF_PI, 0), major=14, minor=6)
    A.lathe("LanternFinial", [(0.0, 0.0), (0.007, -0.004), (0.013, -0.012), (0.009, -0.020), (0.017, -0.028), (0.020, -0.036),
                              (0.0, -0.038)], (LX, LY, -1.142), brass, seg=16)
    # chimney with glowing vent slots, the square pyramid roof with corner crockets
    A.cyl("LanternChimney", 0.034, 0.032, (LX, LY, -1.195), iron, verts=20)
    A.lathe("LanternChimCap", [(0.0, 0.0), (0.040, 0.0), (0.044, 0.006), (0.0, 0.006)], (LX, LY, -1.182), iron, seg=20)
    for k in range(8):
        a = 2 * math.pi * k / 8
        A.box(f"LanternVent{k}", (0.012, 0.006, 0.016), (LX + 0.0335 * math.cos(a), LY + 0.0335 * math.sin(a), -1.196), vent,
              bevel=0.0, rot=(0, 0, a + HALF_PI))
    s2 = math.sqrt(2)
    A.lathe("LanternRoof", [(0.034 * s2, 0.0), (0.10 * s2, -0.040), (0.160 * s2, -0.066), (0.176 * s2, -0.072),
                            (0.178 * s2, -0.080), (0.0, -0.080)], (LX, LY, -1.208), iron, seg=4, rot=(0, 0, math.radians(45)),
            smooth_all=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            A.cyl(f"LanternCrocket{sx}{sy}", 0.009, 0.05, (LX + sx * 0.168, LY + sy * 0.168, -1.262), iron, verts=8, r2=0.0, bevel=0.0,
                  rot=(sy * math.radians(-35), sx * math.radians(35), 0))
    A.box("LanternTopPlate", (0.34, 0.34, 0.020), (LX, LY, -1.296), iron, bevel=0.005)
    # posts, glass, gothic frets
    zt, zb = -1.306, -1.606
    zm = (zt + zb) / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            A.box(f"LanternPost{sx}{sy}", (0.026, 0.026, zt - zb + 0.01), (LX + sx * 0.143, LY + sy * 0.143, zm), iron, bevel=0.004)
            for z in (zt + 0.006, zb - 0.006):
                A.sphere(f"LanternKnob{sx}{sy}{z}", 0.017, (LX + sx * 0.143, LY + sy * 0.143, z), iron, seg=8, rings=5)
    A.box("LanternGlassF", (0.272, 0.006, zt - zb), (LX, LY - 0.137, zm), glass, bevel=0.0)
    A.box("LanternGlassB", (0.272, 0.006, zt - zb), (LX, LY + 0.137, zm), glass, bevel=0.0)
    A.box("LanternGlassL", (0.006, 0.272, zt - zb), (LX + 0.137, LY, zm), glass, bevel=0.0)
    A.box("LanternGlassR", (0.006, 0.272, zt - zb), (LX - 0.137, LY, zm), glass, bevel=0.0)
    hh = (zt - zb) / 2
    outer = ccw([(-0.131, -hh), (0.131, -hh), (0.131, hh), (-0.131, hh)])
    holes = [lancet(-0.058, -hh + 0.030, 0.035, 0.092)[::-1], lancet(0.058, -hh + 0.030, 0.035, 0.092)[::-1],
             ccw(A.circle_pts(0, 0.112, 0.019, 16))[::-1]]
    for k, (dx, dy, a) in enumerate(((0, -1, 0.0), (1, 0, HALF_PI), (0, 1, math.pi), (-1, 0, -HALF_PI))):
        extrude_holed(f"LanternFret{k}", outer, 0.007, iron, frame((LX + dx * 0.1405, LY + dy * 0.1405, zm), (0, 0, a)), holes)
    # the door: hinge knuckles on the front left post, a latch hook on the right
    for dz in (0.09, -0.09):
        A.cyl(f"LanternHinge{dz}", 0.008, 0.04, (LX + 0.128, LY - 0.155, zm + dz), brass, verts=8, bevel=0.0015)
    A.box("LanternLatch", (0.03, 0.008, 0.012), (LX - 0.118, LY - 0.152, zm), brass, bevel=0.002)
    A.sphere("LanternLatchKnob", 0.0075, (LX - 0.104, LY - 0.158, zm), brass, seg=8, rings=6)
    A.box("LanternBotPlate", (0.34, 0.34, 0.022), (LX, LY, -1.617), iron, bevel=0.005)
    A.box("LanternPlinth", (0.29, 0.29, 0.024), (LX, LY, -1.640), iron, bevel=0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            A.sphere(f"LanternFoot{sx}{sy}", 0.019, (LX + sx * 0.118, LY + sy * 0.118, -1.664), brass, seg=8, rings=5)
    # inside: a dish, the candle (melted crown, two drips), the wick, the flame
    A.lathe("LanternDish", [(0.0, 0.0), (0.052, 0.0), (0.058, 0.012), (0.050, 0.014), (0.0, 0.014)], (LX, LY, -1.606), brass, seg=24)
    A.lathe("LanternCandle", [(0.0, 0.0), (0.033, 0.0), (0.033, 0.094), (0.030, 0.103), (0.014, 0.098), (0.004, 0.101),
                              (0.0, 0.101)], (LX, LY, -1.593), wax, seg=20)
    for k, (a, l) in enumerate(((0.6, 0.05), (2.7, 0.035))):
        A.sphere(f"LanternDrip{k}", 0.008, (LX + 0.033 * math.cos(a), LY + 0.033 * math.sin(a), -1.497 - l / 2), wax,
                 scale=(1, 1, l / 0.016 * 0.9), seg=8, rings=6)
    A.cyl("LanternWick", 0.0028, 0.022, (LX, LY, -1.485), soot, verts=6, bevel=0.0)
    A.lathe("LanternFlameMesh", [(0.0, 0.0), (0.010, 0.006), (0.0155, 0.020), (0.0125, 0.040), (0.006, 0.062), (0.0, 0.076)],
            (LX, LY, -1.482), flame, seg=16)
    return dict(notes="a wrought-iron candle lantern with gothic lancet frets over lit glass, glowing roof vents, a "
                      "candle and flame inside; held by its ring, swings on a 2-bone chain from the ring (never toward "
                      "the leg)", glow=[1.0, 0.58, 0.20])


# ================================================================== 28. the knitted scarves
ROW, COLW = 0.028, 0.034      # a chunky stitch: row height, column width (studs)
RING_K, RING_L = 120, 16


def head_sdf(p):
    """the R6 head: a 0.6-radius cylinder z 0.9..2.1 with 0.25 rounded edges (analytic; the mesh lies inside it)"""
    qx, qz = math.hypot(p.x, p.y) - 0.35, abs(p.z - 1.5) - 0.35
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - 0.25


def torso_sdf(p):
    return rbox_sdf(p, (1.0, 0.5, 1.0), 0.002)


RING_A, RING_B = 0.076, 0.061   # the roll's radial and vertical half-sizes: low and wide, under the hair
RING_RLIM = 0.72                  # never further out than this from the neck (it rises over the shoulders instead)
RING_ZFRONT, RING_ZBACK = 0.955, 0.83


def _ring_section(th):
    """the roll's cross-section at angle th: radial and vertical half-sizes (chunky lumps), tilt (the wrap's twist)"""
    a = RING_A * (1 + 0.05 * math.sin(3 * th + 0.7) + 0.03 * math.sin(7 * th + 2.0))
    b = RING_B * (1 + 0.06 * math.sin(2 * th + 1.9) + 0.03 * math.sin(5 * th))
    tilt = 0.16 * math.sin(2 * th + 0.5)
    return a, b, tilt


def _sec_pt(c, u, th, phi, a, b, tilt):
    """a point on the cross-section ellipse (phi round it), rotated by tilt in the (radial, up) plane, with a crease
    spiralling round the roll where the scarf folds over itself"""
    lr, lz = a * math.cos(phi), b * math.sin(phi)
    crease = 1 - 0.10 * math.exp(-(((phi - 1.3 * th) + math.pi) % (2 * math.pi) - math.pi) ** 2 / 0.08)
    lr, lz = lr * crease, lz * crease
    ct, st = math.cos(tilt), math.sin(tilt)
    rr, zz = lr * ct - lz * st, lr * st + lz * ct
    return c + u * rr + Vector((0, 0, zz))


def _ring_ok(r, z, th):
    u = Vector((math.cos(th), math.sin(th), 0))
    a, b, tilt = _ring_section(th)
    c = Vector((u.x * r, u.y * r, z))
    for k in range(24):
        p = _sec_pt(c, u, th, 2 * math.pi * k / 24, a, b, tilt)
        if head_sdf(p) < 0.012 or torso_sdf(p) < 0.005:
            return False
        # the left shoulder carries the sashes' and bag straps' tops (x 0.69.., z to 1.06): ride above them there
        if p.x > 0.66 and p.z < 1.043:
            return False
    return True


def ring_centreline():
    """per angle round the neck: the roll's centre (radius, height) as low and close as the head and the torso allow:
    it rests on the shoulders at the sides, rolls over the torso's front edge in front of the throat (where the head
    overhangs the torso) and drapes low over the upper back behind, under the nape's hair"""
    out = []
    for k in range(RING_K):
        th = HALF_PI + 2 * math.pi * k / RING_K
        sn = math.sin(th)
        zt = lerp(lerp(1.0, RING_ZFRONT, max(0.0, -sn) ** 3), RING_ZBACK, max(0.0, sn) ** 1.0)
        best = None
        for dz in [0.004 * i for i in range(80)]:
            for r in [0.50 + 0.003 * i for i in range(int((RING_RLIM - 0.50) / 0.003) + 1)]:
                if _ring_ok(r, zt + dz, th):
                    best = (r, zt + dz)
                    break
            if best:
                break
        out.append(best)
    # smooth round the loop, then push out again wherever smoothing pulled it in
    sm = []
    for k in range(RING_K):
        w = [out[(k + d) % RING_K] for d in (-3, -2, -1, 0, 1, 2, 3)]
        ws = (1, 2, 3, 4, 3, 2, 1)
        sm.append([sum(x[0] * q for x, q in zip(w, ws)) / 16, sum(x[1] * q for x, q in zip(w, ws)) / 16])
    for k in range(RING_K):
        th = HALF_PI + 2 * math.pi * k / RING_K
        if _ring_ok(sm[k][0], sm[k][1], th):
            continue
        cands = sorted(((0.002 * i, 0.003 * j) for i in range(25) for j in range(30)), key=lambda c: c[0] + c[1])
        for dr, dz in cands:
            if _ring_ok(sm[k][0] + dr, sm[k][1] + dz, th):
                sm[k] = [sm[k][0] + dr, sm[k][1] + dz]
                break
    return sm


def build_ring(name, mat, part_tag=0.0):
    cl = ring_centreline()
    P, CEN = [], []
    for k in range(RING_K + 1):
        kk = k % RING_K
        th = HALF_PI + 2 * math.pi * k / RING_K
        r, z = cl[kk]
        u = Vector((math.cos(th), math.sin(th), 0))
        a, b, tilt = _ring_section(th)
        c = Vector((u.x * r, u.y * r, z))
        CEN.append(c)
        P.append([_sec_pt(c, u, th, 2 * math.pi * l / RING_L, a, b, tilt) for l in range(RING_L + 1)])
    ob = mesh_grid(name, P, mat)
    # outward faces: compare with the nearest centreline point
    orient_out(ob, lambda q: min(CEN, key=lambda c: (c - q).length_squared))
    # knit coordinates: rows along the loop (a whole number of stripe periods round it), columns round the roll
    L = sum((CEN[k + 1] - CEN[k]).length for k in range(RING_K))
    rows = max(10, round(L / ROW / 10) * 10)
    cols = max(8, round(math.pi * (RING_A + RING_B) / COLW))
    s_at = [0.0]
    for k in range(RING_K):
        s_at.append(s_at[-1] + (CEN[k + 1] - CEN[k]).length)
    nl = RING_L + 1
    set_attr(ob, "knit", lambda i, co: (s_at[i // nl] / L * rows, (i % nl) / RING_L * cols, 0.0))
    set_attr(ob, "nh_part", lambda i, co: part_tag, kind="FLOAT")
    return ob, cl


SCARF_TAILS = [   # x centre, y centre, width, top z, bottom z (the long tail behind, the short one over it)
    dict(x=-0.132, y=-0.597, w=0.23, z0=0.93, z1=-0.615, nv=44),
    dict(x=0.043, y=-0.650, w=0.23, z0=0.93, z1=-0.300, nv=36),
]
TAIL_T = 0.048
FRINGE = 0.095


def tail_joints(t):
    zs = [t["z0"] - 0.03] + [lerp(t["z0"] - 0.03, t["z1"] - FRINGE, k / 4) for k in range(1, 5)]
    return [Vector((t["x"], t["y"], z)) for z in zs]


def build_tail(name, t, mat, tag, phase=0.0):
    nu, nv = 6, t["nv"]
    G = []
    for i in range(nu + 1):
        uu = i / nu - 0.5
        col = []
        for j in range(nv + 1):
            s = j / nv
            z = lerp(t["z0"], t["z1"], s)
            w = lerp(t["w"] * 0.72, t["w"], smooth(0.0, 0.16, s))
            x = t["x"] + uu * w + 0.007 * math.sin(2 * math.pi * (1.3 * s) + phase) * smooth(0.1, 0.4, s)
            y = t["y"] - 0.004 * math.cos(math.pi * uu) - 0.005 * (2 * abs(uu)) ** 3
            col.append(Vector((x, y, z)))
        G.append(col)
    ob = A.surface(name, G, TAIL_T, mat)
    Lz = t["z0"] - t["z1"]
    n = (nu + 1) * (nv + 1)
    cols = t["w"] / COLW

    def knit(i, co):
        k = i % n
        ii, jj = k // (nv + 1), k % (nv + 1)
        return ((jj / nv) * Lz / ROW + 7.0 * tag, ii / nu * cols, 0.0)
    set_attr(ob, "knit", knit)
    set_attr(ob, "nh_part", lambda i, co: float(tag), kind="FLOAT")
    # the fringe: twisted yarn tassels along the end
    rnd = random.Random(11 + tag)
    for k in range(6):
        uu = (k + 0.5) / 6 - 0.5
        x0 = t["x"] + uu * t["w"] * 0.92
        z0 = t["z1"] + 0.012
        ln = FRINGE * (0.86 + 0.14 * rnd.random())
        jit = rnd.uniform(-0.006, 0.006)
        pts = [(x0 + uu * 0.024 * q * q + jit * q, t["y"] - 0.003 * q, z0 - ln * q) for q in (0.0, 0.3, 0.6, 0.85, 1.0)]
        fr = A.tube(f"{name}Fringe{k}", pts, 0.0105, mat, res=4, poly=True, taper=lambda q: lerp(1.0, 0.62, q))
        set_attr(fr, "knit", lambda i, co: ((co.z * 90.0) % 1000.0, math.atan2(co.y - t["y"], co.x - x0) / math.pi * 2 + co.z * 40, 0.0))
        set_attr(fr, "nh_part", lambda i, co: float(tag), kind="FLOAT")
    return ob


def _scarf_rig(ob):
    cols = [tail_joints(t) for t in SCARF_TAILS]
    bones = chain_bones((0, 0, 1.0), cols)
    part = ob.data.attributes["nh_part"]
    tags = [int(round(part.data[i].value)) for i in range(len(ob.data.vertices))]

    def wfn(i, co):
        tag = tags[i]
        if tag <= 0:
            return {"Root": 1.0}
        n = tag - 1
        return column_weights(co, n, cols[n], hinge_z=cols[n][0].z + 0.001)
    return make_rig_idx(ob, bones, wfn), bones


SCARVES = [
    ("ScarfStripe", "crimson-and-black stripes", dict(rgb=(0.205, 0.016, 0.034), stripe=((0.010, 0.009, 0.011), 10, 4))),
    ("ScarfViolet", "soft grey-violet", dict(rgb=(0.20, 0.155, 0.285), heather=0.18)),
]


@item("Scarves", "Long knitted scarves", close=((2.5, -5.4, 1.5), (0, 0, 0.55), 72), each=True)
def build_scarves(M):
    for key, label, kw in SCARVES:
        mat = mat_knit(f"Knit_{key}", **kw)
        piece(key, "Torso", rig=_scarf_rig, sway="Tails", keepout=(0, 1, 0), lock="X")
        build_ring(f"{key}Ring", mat)
        for n, t in enumerate(SCARF_TAILS):
            build_tail(f"{key}Tail{n}", t, mat, n + 1, phase=0.9 * n)
    return dict(notes="long chunky knitted scarves wrapped once round the neck, both tails down the front: crimson-and-"
                      "black stripes, and a soft grey-violet; the tails swing fore and aft on 4-bone chains (Tails), "
                      "never toward the chest; stockinette relief baked from a per-vertex stitch attribute")
