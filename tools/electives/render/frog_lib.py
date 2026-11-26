"""The Clockwork Frog: a hollow brass automaton (shell with real wall thickness, lacquered interior, mechanism deck).

build_frog(M, origin, plate_open_deg, heart_lifted, heart_z) -> dict: heart, lug (object), lug_centre, body_centre,
body_radii, interior (objects inside the shell), keep (objects never carved).
carve(F, objects) booleans the hollow out of anything that reaches into it (legs, head, key), so nothing shows inside.
Needs M: brass, brass_dark, steel, porcelain, lacquer, copper, leather_dk, heart, glow, pupil.
Units: metres. The frog lies on its back, head toward +Y. origin z = the surface it rests on. WALL = shell thickness.
Object names are stable (clipcheck's allowlist matches on them).
"""
import math

import bmesh
import bpy
from mathutils import Vector

col = bpy.context.scene.collection
WALL = 0.0045
LUG_R, LUG_r = 0.0055, 0.0032
M_ = {}


def _link(o):
    if o.name not in col.objects:
        col.objects.link(o)
    return o


def _smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def nm(o, name):
    o.name = name
    return o


def ellipsoid(name, loc, scale, mats, seg=96):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    for m in mats:
        o.data.materials.append(m)
    return _smooth(o)


def apply_mods(o):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def boolean(o, cutter, op="DIFFERENCE"):
    bo = o.modifiers.new("bool", "BOOLEAN")
    bo.operation = op
    bo.object = cutter
    bo.solver = "EXACT"
    apply_mods(o)


def cyl(name, loc, r, depth, mat, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = nm(bpy.context.active_object, name)
    o.data.materials.append(mat)
    b = o.modifiers.new("b", "BEVEL")
    b.width = min(r, depth) * 0.15
    b.segments = 2
    return o


def box(name, loc, size, mat, rot=(0, 0, 0), bevel=0.0006):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = nm(bpy.context.active_object, name)
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def sphere(name, loc, r, mat, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = nm(bpy.context.active_object, name)
    o.data.materials.append(mat)
    return _smooth(o)


def torus(name, loc, R, r, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=64, minor_segments=16)
    o = nm(bpy.context.active_object, name)
    o.data.materials.append(mat)
    return _smooth(o)


def tube(name, points, r, mat, res=6):
    cu = bpy.data.curves.new("tube", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = _link(bpy.data.objects.new(name, cu))
    o.data.materials.append(mat)
    return o


def gear(loc, R, thick, teeth, mat, phase=0.0):
    """A spur gear: trapezoid teeth, five spoke windows, hub and axle (axle runs down through the deck)."""
    bm = bmesh.new()
    pts = []
    n = teeth * 4
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        r = R * (1.0 if i % 4 in (1, 2) else 0.86)
        pts.append((math.cos(a) * r, math.sin(a) * r))
    top = [bm.verts.new((x, y, thick / 2)) for x, y in pts]
    bot = [bm.verts.new((x, y, -thick / 2)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for i in range(n):
        bm.faces.new((top[i], bot[i], bot[(i + 1) % n], top[(i + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("gear")
    bm.to_mesh(me)
    bm.free()
    o = _link(bpy.data.objects.new("Gear", me))
    o.location = loc
    o.data.materials.append(mat)
    for s in range(5):
        a = phase + s * 2 * math.pi / 5 + math.pi / 5
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=R * 0.2, depth=thick * 3,
                                            location=(loc[0] + math.cos(a) * R * 0.5, loc[1] + math.sin(a) * R * 0.5, loc[2]))
        c = bpy.context.active_object
        boolean(o, c)
        bpy.data.objects.remove(c)
    b = o.modifiers.new("b", "BEVEL")
    b.width = thick * 0.12
    b.segments = 2
    b.limit_method = "ANGLE"
    cyl("Gear_Hub", loc, R * 0.26, thick * 1.5, M_["brass_dark"])
    top_z = loc[2] + thick * 0.75
    cyl("Gear_Axle", (loc[0], loc[1], (top_z + loc[2] - 0.012) / 2), R * 0.08, top_z - (loc[2] - 0.012), M_["steel"])
    return o


def bellows(base, w, l, h, pleats, mats):
    """Leather bellows between two brass boards; the port pushes out of the front pleats."""
    bt = 0.0016
    x, y, z0 = base
    box("Lung_Board", (x, y, z0 + bt / 2), (w, l, bt), mats["brass"])
    box("Lung_Board", (x, y, z0 + h - bt / 2), (w, l, bt), mats["brass"])
    inner = h - 2 * bt
    for i in range(pleats):
        zc = z0 + bt + inner * (i + 0.5) / pleats
        k = 0.84 if i % 2 else 0.96
        box("Lung_Pleat", (x, y, zc), (w * k, l * k, inner / pleats * 0.999), mats["leather_dk"], bevel=0.0006)
    cyl("Lung_Port", (x, y + l * 0.42 + 0.003, z0 + h - bt - 0.0035), 0.0022, 0.006, mats["brass"], rot=(math.radians(90), 0, 0))
    return Vector((x, y, z0 + h))


def mainspring(centre, z, r0, r1, turns, mat):
    pts = []
    N = int(turns * 24)
    for i in range(N + 1):
        t = i / N
        a = t * turns * 2 * math.pi
        r = r0 + (r1 - r0) * t
        pts.append((centre[0] + math.cos(a) * r, centre[1] + math.sin(a) * r, z))
    cu = bpy.data.curves.new("spring", "CURVE")
    cu.dimensions = "3D"
    cu.extrude = 0.0009
    cu.bevel_depth = 0.0003
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    o = _link(bpy.data.objects.new("Mainspring", cu))
    o.data.materials.append(mat)
    return o


def build_frog(M, origin, plate_open_deg=110, heart_lifted=True, heart_z=None):
    M_.update(M)
    ox, oy, oz = origin
    BR = Vector((0.088, 0.112, 0.036))
    BC = Vector((ox, oy, oz + BR.z + 0.0004))  # rests on the surface, 0.4 mm clear
    TOP = BC.z + BR.z
    out = {"interior": [], "keep": []}

    # --- the hollow brass shell, cut open on the belly, lacquered inside
    body = ellipsoid("FrogBody", BC, BR, [M["brass"], M["lacquer"]])
    so = body.modifiers.new("shell", "SOLIDIFY")
    so.thickness = WALL
    so.offset = -1.0
    so.material_offset = 1
    so.use_even_offset = True
    apply_mods(body)
    cut = ellipsoid("Cut", (BC.x, BC.y, TOP + 0.004), (0.067, 0.088, 0.034), [M["brass"]])
    boolean(body, cut)
    bpy.data.objects.remove(cut)
    bv = body.modifiers.new("rim", "BEVEL")
    bv.width = 0.0012
    bv.segments = 3
    bv.limit_method = "ANGLE"
    bv.angle_limit = math.radians(40)
    body.modifiers.new("wn", "WEIGHTED_NORMAL")
    out["keep"].append(body)

    # rim rivets, centred on the outer surface just outside the opening
    for k in range(18):
        if k == 9:
            continue                           # the hinge sits here
        a = k * 2 * math.pi / 18
        u, v = math.cos(a) * 0.82, math.sin(a) * 0.86
        w = math.sqrt(max(0.0, 1 - u * u - v * v))
        sphere("Rivet", (BC.x + u * BR.x, BC.y + v * BR.y, BC.z + w * BR.z), 0.0028, M["brass_dark"], 16)

    # --- the mechanism inside
    before = set(bpy.data.objects.keys())
    IR = BR - Vector((WALL, WALL, WALL))       # inner wall radii
    DZ = BC.z - 0.016
    k = math.sqrt(1 - (0.016 / IR.z) ** 2)
    ellipsoid("Deck", (BC.x, BC.y, DZ), (IR.x * k - 0.002, IR.y * k - 0.002, 0.0018), [M["brass_dark"]], 64)  # seated in the wall
    dtop = DZ + 0.0018
    for x, y in ((-0.05, -0.06), (0.05, -0.06), (-0.05, 0.06), (0.05, 0.06)):
        sphere("DeckScrew", (BC.x + x, BC.y + y, dtop + 0.0004), 0.0018, M["steel"], 12)
    for y in (-0.074, 0.076):
        kk = math.sqrt(max(0.0, 1 - (y / IR.y) ** 2 - (0.008 / IR.z) ** 2))
        xe = IR.x * kk - 0.0015
        tube("Brace", [(BC.x - xe, BC.y + y, BC.z - 0.008), (BC.x, BC.y + y, BC.z + 0.006), (BC.x + xe, BC.y + y, BC.z - 0.008)], 0.0018, M["brass"])

    lungs = [bellows((BC.x + sx * 0.032, BC.y + 0.034, dtop), 0.028, 0.036, 0.018, 7, M) for sx in (-1, 1)]
    gz = dtop + 0.006
    gear((BC.x - 0.02, BC.y - 0.036, gz), 0.019, 0.0035, 16, M["brass"], 0.0)
    gear((BC.x + 0.0185, BC.y - 0.046, gz + 0.004), 0.0135, 0.0035, 12, M["brass_dark"], 0.13)
    gear((BC.x + 0.003, BC.y - 0.068, gz - 0.0025), 0.0085, 0.003, 9, M["brass"], 0.3)
    barrel_c = (BC.x + 0.042, BC.y - 0.012)
    cyl("Barrel", (*barrel_c, dtop + 0.00125), 0.0125, 0.0025, M["brass_dark"])
    mainspring(barrel_c, dtop + 0.0025 + 0.0016, 0.002, 0.011, 6, M["steel"])

    # the heart cradle: post, cup, ring, prongs, glow ring; copper pipes from the ring to the bellows boards
    HC = Vector((BC.x, BC.y, dtop + 0.02))
    cyl("Cradle_Post", (HC.x, HC.y, (dtop + HC.z - 0.002) / 2), 0.004, HC.z - 0.002 - dtop, M["brass_dark"])
    cyl("Cradle_Cup", (HC.x, HC.y, HC.z - 0.002), 0.0135, 0.002, M["brass_dark"])
    torus("Cradle_Ring", HC, 0.014, 0.0022, M["brass"])
    for a in (45, 135, 225, 315):
        aa = math.radians(a)
        tube("Cradle_Prong", [(HC.x + math.cos(aa) * 0.0155, HC.y + math.sin(aa) * 0.0155, HC.z),
                              (HC.x + math.cos(aa) * 0.0175, HC.y + math.sin(aa) * 0.0175, HC.z + 0.008)], 0.0011, M["brass"])
    torus("Cradle_Glow", (HC.x, HC.y, HC.z + 0.0045), 0.0105, 0.0006, M["glow"])
    for sx, lc in zip((-1, 1), lungs):
        tube("Pipe_Lung", [(HC.x + sx * 0.0175, HC.y + 0.004, HC.z),
                           (HC.x + sx * 0.025, HC.y + 0.02, lc.z + 0.012),
                           (lc.x, lc.y - 0.004, lc.z + 0.0024)], 0.0022, M["copper"])
    bpy.ops.object.light_add(type="POINT", location=(BC.x, BC.y + 0.01, dtop + 0.028))
    il = bpy.context.active_object
    il.data.energy = 0.12
    il.data.color = (1.0, 0.55, 0.3)
    il.data.shadow_soft_size = 0.01
    out["interior"] = [o for o in bpy.data.objects if o.name not in before]
    out["cradle"] = HC

    # --- the head (carved later), eyes, throat collar
    ellipsoid("FrogHead", (ox, oy + 0.13, oz + 0.0285), (0.064, 0.05, 0.028), [M["brass"]], 64)
    for sx in (-1, 1):
        sphere("Eye", (ox + sx * 0.042, oy + 0.155, oz + 0.05), 0.02, M["porcelain"], 32)
        sphere("Pupil", (ox + sx * 0.0465, oy + 0.163, oz + 0.0675), 0.0085, M["pupil"], 24)
    torus("Collar", (ox, oy + 0.1, oz + 0.05), 0.03, 0.005, M["brass_dark"], rot=(math.radians(80), 0, 0))

    # --- the belly plate: a closed porcelain dome, hinged on the -X rim and propped open like a lid
    RX, RZ = 0.059, 0.026                      # the rim of the opening at y = 0 (relative to BC)
    hinge = Vector((BC.x - RX, BC.y, BC.z + RZ))
    for y in (-0.03, 0.03):
        cyl("Hinge", (hinge.x, hinge.y + y, hinge.z), 0.0035, 0.016, M["brass"], rot=(math.radians(90), 0, 0))
    piv = _link(bpy.data.objects.new("PlatePivot", None))
    piv.location = hinge
    PX, PY, PT, PC = 0.062, 0.08, 0.011, 0.0115  # dome radii, thickness, centre height above the hinge
    pl = [ellipsoid("BellyPlate", (RX + 0.001, 0, PC), (PX, PY, PT), [M["porcelain"]], 96)]

    def dome_z(dx, dy):
        return PC + PT * math.sqrt(max(0.0, 1 - (dx / PX) ** 2 - (dy / PY) ** 2))
    ring = torus("PlateRing", (RX + 0.001, 0, dome_z(0.05, 0) + 0.0003), 1.0, 0.03, M["brass"])
    ring.scale = (0.05, 0.065, 0.025)
    pl.append(ring)
    for kq in range(12):
        a = kq * 2 * math.pi / 12
        dx, dy = math.cos(a) * 0.042, math.sin(a) * 0.056
        pl.append(sphere("PlateRivet", (RX + 0.001 + dx, dy, dome_z(dx, dy) + 0.0008), 0.002, M["brass_dark"], 12))
    for o in pl:
        o.parent = piv
    piv.rotation_euler = (0, -math.radians(plate_open_deg), 0)
    out["keep"] += pl

    # --- the heart-pump: one fused mesh, a brass band, copper stubs and a lifting lug
    hz = heart_z if heart_z is not None else (HC.z + 0.1 if heart_lifted else HC.z + 0.008)
    H = Vector((HC.x, HC.y, hz))
    lobes = [sphere("Heart", (H.x - 0.011, H.y, H.z), 0.0175, M["heart"], 32), sphere("Lobe", (H.x + 0.011, H.y, H.z), 0.0175, M["heart"], 32)]
    bpy.ops.mesh.primitive_cone_add(radius1=0.026, depth=0.036, location=(H.x, H.y, H.z - 0.022), rotation=(math.pi, 0, 0), vertices=48)
    cone = bpy.context.active_object
    heart = lobes[0]
    for o in (lobes[1], cone):
        boolean(heart, o, "UNION")
        bpy.data.objects.remove(o)
    _smooth(heart)
    heart.modifiers.new("wn", "WEIGHTED_NORMAL")
    band = torus("HeartBand", (H.x, H.y, H.z - 0.006), 0.0215, 0.0016, M["brass"])
    lc = Vector((H.x, H.y, H.z + 0.0215))
    lug = torus("HeartLug", lc, LUG_R, LUG_r, M["brass"], rot=(0, math.radians(90), 0))
    for sx in (-1, 1):
        tube("HeartStub", [(H.x + sx * 0.012, H.y, H.z + 0.013), (H.x + sx * 0.017, H.y + 0.004, H.z + 0.026)], 0.0022, M["copper"])
    bpy.ops.object.light_add(type="POINT", location=(H.x, H.y, H.z - 0.004))
    hl = bpy.context.active_object
    hl.data.energy = 1.2
    hl.data.color = (1.0, 0.22, 0.12)
    hl.data.shadow_soft_size = 0.02
    out["keep"] += [heart, band, lug]
    out["heart"] = H
    out["lug"] = lug
    out["lug_centre"] = lc
    out["body_centre"] = BC
    out["body_radii"] = BR
    return out


def carve(F, objects):
    """Boolean the hollow out of anything that reaches into it, so the inside stays clean."""
    BC, BR = F["body_centre"], F["body_radii"]
    hollow = ellipsoid("Hollow", BC, (BR.x - WALL + 0.0002, BR.y - WALL + 0.0002, BR.z - WALL + 0.0002), [M_["brass"]], 96)
    skip = set(o.name for o in F["interior"] + F["keep"]) | {"Hollow"}
    lo, hi = BC - BR, BC + BR
    carved = []
    bpy.context.view_layer.update()
    for o in list(objects):
        if o.name in skip or o.type not in ("MESH", "CURVE") or o.parent is not None:
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if any(max(w[i] for w in ws) < lo[i] or min(w[i] for w in ws) > hi[i] for i in range(3)):
            continue
        if o.type == "CURVE":
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.convert(target="MESH")
        boolean(o, hollow)
        carved.append(o.name)
    bpy.data.objects.remove(hollow)
    return carved
