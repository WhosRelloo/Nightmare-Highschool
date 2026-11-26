"""The Clockwork Raven and the Clockwork Wyvern: hollow brass automata built like frog_lib.build_frog (rest pose).

build_raven(M, origin) / build_wyvern(M, origin) -> dict like build_frog's (body_centre, body_radii, interior, keep)
plus species, bone_of (piece -> bone), bone_heads (bone -> head, parent, axis) and attach (extra points).
Object names are "<Piece>__<part>": the export groups by <Piece>; clipcheck lets parts of one piece touch.
Units: metres. The animal lies on its back, head toward +Y; origin z = the surface it rests on.
Organs follow Config.Anatomy: Raven HeartPump, Lungs, VoiceBox, WingSpring, FlagCog;
Wyvern FireGland (glass bulb + ember, mounted forward), HeartA, HeartB, Lungs, GearGut, FlagCog.
"""
import math

import bpy
from mathutils import Matrix, Vector

import frog_lib as FL

WALL = FL.WALL
HS = 0.5          # seated heart-pumps are half size (the frog's rest pose)
RR = 0.017        # heart cradle ring radius


def _rename(before, prefix):
    for o in bpy.data.objects:
        if o.name not in before and "__" not in o.name and o.type in ("MESH", "CURVE"):
            o.name = f"{prefix}__{o.name.split('.')[0].lower()}"


def named(prefix, fn, *a, **k):
    before = set(bpy.data.objects.keys())
    r = fn(*a, **k)
    _rename(before, prefix)
    return r


def taper_x(o, BC, BR, k):
    """narrow the body toward the tail (-Y): x scaled by 1 - k t^2, t = how far past the centre toward the tail"""
    if not k:
        return
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        t = max(0.0, -(w.y - BC.y) / BR.y)
        w.x = BC.x + (w.x - BC.x) * (1 - k * t * t)
        v.co = o.matrix_world.inverted() @ w


def rim(BR, C, zc):
    """where the opening cut (radii C, centre zc above BC) meets the outer shell in the y = 0 slice"""
    lo, hi = 0.0, math.pi / 2
    for _ in range(60):
        t = (lo + hi) / 2
        x, z = BR.x * math.cos(t), BR.z * math.sin(t)
        f = (x / C.x) ** 2 + ((z - zc) / C.z) ** 2
        if f > 1:
            lo = t
        else:
            hi = t
    return BR.x * math.cos(lo), BR.z * math.sin(lo)


def shell(M, BC, BR, C, ratio, taper, oy=0.0):
    TOP = BC.z + BR.z
    body = FL.ellipsoid("Body__shell", BC, BR, [M["brass"], M["lacquer"]])
    taper_x(body, BC, BR, taper)
    so = body.modifiers.new("shell", "SOLIDIFY")
    so.thickness = WALL
    so.offset = -1.0
    so.material_offset = 1
    so.use_even_offset = True
    FL.apply_mods(body)
    cut = FL.ellipsoid("Cut", (BC.x, BC.y + oy, TOP + 0.004), C, [M["brass"]])
    FL.boolean(body, cut)
    bpy.data.objects.remove(cut)
    bv = body.modifiers.new("rim", "BEVEL")
    bv.width = 0.0012
    bv.segments = 3
    bv.limit_method = "ANGLE"
    bv.angle_limit = math.radians(40)
    body.modifiers.new("wn", "WEIGHTED_NORMAL")
    rx, rz = rim(BR, C, BR.z + 0.004)
    RX, RZ = rx - 0.002, rz - 0.0005
    hinge = Vector((BC.x - RX, BC.y + oy, BC.z + RZ))
    for y in (-0.03, 0.03):
        FL.cyl("Body__hinge", (hinge.x, hinge.y + y, hinge.z), 0.0035, 0.016, M["brass"], rot=(math.radians(90), 0, 0))
    # rim rivets just outside the opening (skipping the hinge side)
    for k in range(20):
        a = k * 2 * math.pi / 20
        if abs(math.cos(a) + 1) < 0.08:
            continue
        u, v = math.cos(a) * (C.x / BR.x + 0.1), math.sin(a) * (C.y / BR.y + 0.08)
        if u * u + v * v >= 0.97:
            continue
        w = math.sqrt(max(0.0, 1 - u * u - v * v))
        p = Vector((BC.x + u * BR.x, BC.y + oy + v * BR.y, BC.z + w * BR.z))
        tt = max(0.0, -(p.y - BC.y) / BR.y)
        p.x = BC.x + (p.x - BC.x) * (1 - taper * tt * tt)
        FL.sphere("Body__rivet", p, 0.0028, M["brass_dark"], 16)
    # the belly plate: a porcelain dome hinged on the -X rim, shut
    piv = FL._link(bpy.data.objects.new("PlatePivot", None))
    piv.location = hinge
    PX = RX + 0.003
    PY, PT, PC = PX * ratio, 0.011, 0.0115
    pl = [FL.ellipsoid("Plate__dome", (RX + 0.001, 0, PC), (PX, PY, PT), [M["porcelain"]], 96)]

    def dome_z(dx, dy):
        return PC + PT * math.sqrt(max(0.0, 1 - (dx / PX) ** 2 - (dy / PY) ** 2))
    ring = FL.torus("Plate__ring", (RX + 0.001, 0, dome_z(0.05, 0) + 0.0003), 1.0, 0.03, M["brass"])
    ring.scale = (0.05 * PX / 0.062, 0.065 * PY / 0.08, 0.025)
    pl.append(ring)
    for kq in range(12):
        a = kq * 2 * math.pi / 12
        dx, dy = math.cos(a) * PX * 0.68, math.sin(a) * PY * 0.7
        pl.append(FL.sphere("Plate__rivet", (RX + 0.001 + dx, dy, dome_z(dx, dy) + 0.0008), 0.002, M["brass_dark"], 12))
    for o in pl:
        o.parent = piv
    return body, hinge, piv, pl, (RX, RZ, PX, PY, PT, PC)


def deck(M, BC, BR, taper, braces_y):
    IR = BR - Vector((WALL, WALL, WALL))
    DZ = BC.z - 0.016
    k = math.sqrt(1 - (0.016 / IR.z) ** 2)
    d = FL.ellipsoid("Mechanism__deck", (BC.x, BC.y, DZ), (IR.x * k - 0.002, IR.y * k - 0.002, 0.0018), [M["brass_dark"]], 64)
    taper_x(d, BC, BR, taper)
    dtop = DZ + 0.0018
    for y in braces_y:
        kk = math.sqrt(max(0.0, 1 - (y / IR.y) ** 2 - (0.008 / IR.z) ** 2))
        t = max(0.0, -y / BR.y)
        xe = (IR.x * kk - 0.0015) * (1 - taper * t * t)
        FL.tube("Mechanism__brace", [(BC.x - xe, BC.y + y, BC.z - 0.008), (BC.x, BC.y + y, BC.z + 0.006), (BC.x + xe, BC.y + y, BC.z - 0.008)], 0.0018, M["brass"])
    return dtop


def heart(M, prefix, HC, dtop):
    """a low cradle on the deck (Mechanism) and a half-size heart-pump seated in it (prefix); returns the heart centre"""
    FL.cyl("Mechanism__cradle_cup", (HC.x, HC.y, dtop + 0.001), 0.0135, 0.002, M["brass_dark"])
    for a in (0, 120, 240):
        aa = math.radians(a + 90)
        FL.tube("Mechanism__cradle_strut", [(HC.x + math.cos(aa) * 0.0128, HC.y + math.sin(aa) * 0.0128, dtop + 0.0016),
                                            (HC.x + math.cos(aa) * RR, HC.y + math.sin(aa) * RR, HC.z - 0.0016)], 0.0009, M["brass"])
    FL.torus("Mechanism__cradle_ring", HC, RR, 0.0022, M["brass"])
    for a in (45, 135, 225, 315):
        aa = math.radians(a)
        FL.tube("Mechanism__cradle_prong", [(HC.x + math.cos(aa) * (RR + 0.0015), HC.y + math.sin(aa) * (RR + 0.0015), HC.z),
                                            (HC.x + math.cos(aa) * (RR + 0.0035), HC.y + math.sin(aa) * (RR + 0.0035), HC.z + 0.008)], 0.0011, M["brass"])
    FL.torus("CradleGlow__ring", (HC.x, HC.y, dtop + 0.0029), 0.0105, 0.0006, M["glow"])
    H = Vector((HC.x, HC.y, dtop + 0.0023 + 0.04 * HS))
    lobes = [FL.sphere(f"{prefix}__heart", (H.x - 0.011, H.y, H.z), 0.0175, M["heart"], 32), FL.sphere("Lobe", (H.x + 0.011, H.y, H.z), 0.0175, M["heart"], 32)]
    bpy.ops.mesh.primitive_cone_add(radius1=0.026, depth=0.036, location=(H.x, H.y, H.z - 0.022), rotation=(math.pi, 0, 0), vertices=48)
    cone = bpy.context.active_object
    h = lobes[0]
    for o in (lobes[1], cone):
        FL.boolean(h, o, "UNION")
        bpy.data.objects.remove(o)
    FL._smooth(h)
    parts = [h, FL.torus(f"{prefix}__band", (H.x, H.y, H.z - 0.006), 0.0215, 0.0016, M["brass"]),
             FL.torus(f"{prefix}__lug", (H.x, H.y, H.z + 0.0215), FL.LUG_R, FL.LUG_r, M["brass"], rot=(0, math.radians(90), 0))]
    for sx in (-1, 1):
        parts.append(FL.tube(f"{prefix}__stub", [(H.x + sx * 0.012, H.y, H.z + 0.013), (H.x + sx * 0.017, H.y + 0.004, H.z + 0.026)], 0.0022, M["copper"]))
    K = Matrix.Translation(H) @ Matrix.Scale(HS, 4) @ Matrix.Translation(-H)
    bpy.context.view_layer.update()
    for o in parts:
        o.matrix_world = K @ o.matrix_world
    return H


def lungs(M, BC, dtop, dx, dy, w, l, h):
    pts = []
    for sx in (-1, 1):
        top = named("Lungs", FL.bellows, (BC.x + sx * dx, BC.y + dy, dtop), w, l, h, 6, M)
        pts.append(top)
    return pts


def flag_cog(M, BC, dtop, dx, dy):
    before = set(bpy.data.objects.keys())
    FL.gear((BC.x + dx, BC.y + dy, dtop + 0.0003 + 0.00125), 0.0075, 0.0025, 10, M["brass"], 0.2)
    for o in list(bpy.data.objects):
        if o.name not in before:
            b = o.name.split(".")[0]
            if b == "Gear_Axle":
                bpy.data.objects.remove(o)
            elif b in ("Gear", "Gear_Hub"):
                o.name = "FlagCog__cog" if b == "Gear" else "FlagCog__hub"


def barrel(M, BC, dtop, dx, dy):
    c = (BC.x + dx, BC.y + dy)
    FL.cyl("Mechanism__barrel", (*c, dtop + 0.00125), 0.0125, 0.0025, M["brass_dark"])
    before = set(bpy.data.objects.keys())
    FL.mainspring(c, dtop + 0.0025 + 0.0016, 0.002, 0.011, 6, M["steel"])
    _rename(before, "Mechanism")


def eyes(M, head_c, dx, dy, dz, r):
    for sx in (-1, 1):
        e = Vector((head_c.x + sx * dx, head_c.y + dy, head_c.z + dz))
        FL.sphere("Head__eye", e, r, M["porcelain"], 32)
        out = Vector((sx * 0.35, 0.3, 0.88)).normalized()
        FL.sphere("Head__pupil", e + out * r * 0.62, r * 0.42, M["pupil"], 24)


def carve(F, BC, BR, taper):
    hollow = FL.ellipsoid("Hollow", BC, (BR.x - WALL + 0.0002, BR.y - WALL + 0.0002, BR.z - WALL + 0.0002), [FL.M_["brass"]], 96)
    taper_x(hollow, BC, BR, taper)
    keep = set(o.name for o in F["interior"] + F["keep"]) | {"Hollow"}
    lo, hi = BC - BR, BC + BR
    carved = []
    bpy.context.view_layer.update()
    for o in list(bpy.data.objects):
        if o.name in keep or o.type not in ("MESH", "CURVE") or o.parent is not None:
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if any(max(w[i] for w in ws) < lo[i] or min(w[i] for w in ws) > hi[i] for i in range(3)):
            continue
        if o.type == "CURVE":
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.convert(target="MESH")
        FL.boolean(o, hollow)
        carved.append(o.name)
    bpy.data.objects.remove(hollow)
    return carved


def _centre(prefix):
    pts = []
    for o in bpy.context.scene.objects:
        if o.type in ("MESH", "CURVE") and o.name.split("__")[0] == prefix:
            pts.append(o.matrix_world @ (sum((Vector(c) for c in o.bound_box), Vector()) / 8))
    return sum(pts, Vector()) / len(pts)


def _finish(F, organs, extra_bones=()):
    bc = F["body_centre"]
    piv = bpy.data.objects["PlatePivot"].matrix_world.translation
    heads = {"Root": {"head": [0, 0, 0], "parent": None}, "Body": {"head": list(bc), "parent": "Root"},
             "PlateHinge": {"head": list(piv), "parent": "Body", "axis": [0, -1, 0]}}
    for o in organs + list(extra_bones):
        heads[o] = {"head": list(_centre(o)), "parent": "Body"}
    heads["SideKey"] = {"head": list(_centre("SideKey")), "parent": "Body", "axis": F["key_axis"]}
    F["bone_heads"] = heads
    bone_of = {"Body": "Body", "Mechanism": "Body", "Head": "Body", "Limbs": "Body", "Tail": "Body", "CradleGlow": "Body",
               "Plate": "PlateHinge", "SideKey": "SideKey"}
    for o in organs + list(extra_bones):
        bone_of[o] = o
    bone_of.update(F.get("bone_extra", {}))
    F["bone_of"] = bone_of


def build_raven(M, origin):
    FL.M_.update(M)
    ox, oy, oz = origin
    BR = Vector((0.075, 0.13, 0.04))
    BC = Vector((ox, oy, oz + BR.z + 0.0004))
    TAPER = 0.38
    F = {"species": "Raven", "interior": [], "keep": [], "body_centre": BC, "body_radii": BR, "attach": {}}
    body, hinge, piv, pl, dims = shell(M, BC, BR, Vector((0.056, 0.092, 0.034)), 1.6, TAPER)
    F["keep"] += [body] + pl
    before = set(bpy.data.objects.keys())
    dtop = deck(M, BC, BR, TAPER, (-0.09, 0.104))
    HC = Vector((BC.x, BC.y + 0.006, dtop + 0.02))
    F["heart"] = heart(M, "HeartPump", HC, dtop)
    lungs(M, BC, dtop, 0.031, 0.047, 0.024, 0.03, 0.016)
    # the voice-box: a small brass reed organ near the throat
    vb = Vector((BC.x, BC.y + 0.083, dtop))
    FL.box("VoiceBox__case", (vb.x, vb.y, vb.z + 0.0053), (0.032, 0.014, 0.01), M["brass_dark"], bevel=0.0008)
    for i, hh in enumerate((0.009, 0.013, 0.016, 0.013, 0.009)):
        x = vb.x - 0.012 + i * 0.006
        FL.cyl("VoiceBox__pipe", (x, vb.y, vb.z + 0.0103 + hh / 2), 0.0019, hh, M["brass"], verts=24)
        FL.cyl("VoiceBox__lip", (x, vb.y - 0.0019, vb.z + 0.0103 + hh * 0.3), 0.0009, 0.0012, M["steel"], rot=(math.radians(90), 0, 0), verts=12)
    # the wing spring: a steel coil across the body near the tail, between two brass posts
    ws = Vector((BC.x, BC.y - 0.052, dtop + 0.0095))
    pts = []
    N = 9 * 16
    for i in range(N + 1):
        t = i / N
        a = t * 9 * 2 * math.pi
        pts.append((ws.x - 0.022 + 0.044 * t, ws.y + math.cos(a) * 0.0062, ws.z + math.sin(a) * 0.0062))
    cu = bpy.data.curves.new("coil", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0011
    cu.bevel_resolution = 3
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    co = FL._link(bpy.data.objects.new("WingSpring__coil", cu))
    co.data.materials.append(M["steel"])
    for sx in (-1, 1):
        FL.box("WingSpring__post", (ws.x + sx * 0.0255, ws.y, dtop + 0.0063), (0.004, 0.006, 0.0122), M["brass"], bevel=0.0005)
    barrel(M, BC, dtop, 0.043, -0.012)
    flag_cog(M, BC, dtop, -0.042, -0.012)
    bpy.ops.object.light_add(type="POINT", location=(BC.x, BC.y + 0.01, dtop + 0.028))
    bpy.context.active_object.data.energy = 0.12
    F["interior"] = [o for o in bpy.data.objects if o.name not in before]

    # head with a steel beak, porcelain eyes
    hc = Vector((ox, oy + 0.152, oz + 0.0366))   # resting 0.6 mm over the wax
    FL.sphere("Head__skull", hc, 0.036, M["brass"], 64)
    bpy.ops.mesh.primitive_cone_add(radius1=0.013, radius2=0.0006, depth=0.062, location=(hc.x, hc.y + 0.058, hc.z - 0.004),
                                    rotation=(math.radians(-90), 0, 0), vertices=48)
    beak = bpy.context.active_object
    beak.name = "Head__beak"
    beak.data.materials.append(M["steel_dark"])
    eyes(M, hc, 0.024, 0.016, 0.018, 0.011)
    FL.torus("Head__collar", (ox, oy + 0.122, oz + 0.04), 0.03, 0.005, M["brass_dark"], rot=(math.radians(80), 0, 0))
    # folded wings against the sides, each held by two screwed wing plates
    wy = BC.y + 0.02
    plates = 0
    for sx in (-1, 1):
        cx = BC.x + sx * (BR.x + 0.0035)
        w = FL.ellipsoid("Limbs__wing", (cx, wy, BC.z + 0.002), (0.0105, 0.095, 0.029), [M["brass_dark"]], 64)
        w.rotation_euler = (0, sx * math.radians(-8), 0)
        for dyw in (-0.04, 0.03):
            plates += 1
            sx_out = cx + sx * (0.0105 * math.sqrt(1 - (dyw / 0.095) ** 2) + 0.0006)
            FL.box(f"WingPlate{plates}__plate", (sx_out, wy + dyw, BC.z + 0.002), (0.003, 0.03, 0.02), M["brass"], bevel=0.0006)
            FL.cyl(f"WingPlate{plates}__screw", (sx_out + sx * 0.0019, wy + dyw, BC.z + 0.002), 0.0028, 0.0016, M["steel"],
                   rot=(0, math.radians(90), 0), verts=24)
            FL.box(f"WingPlate{plates}__slot", (sx_out + sx * 0.0027, wy + dyw, BC.z + 0.002), (0.0006, 0.0042, 0.0007), M["pupil"])
            F["attach"][f"WingPlate{plates}"] = {"bone": f"WingPlate{plates}", "pos": [sx_out + sx * 0.0027, wy + dyw, BC.z + 0.002]}
    # tail feathers fanned on the wax
    for k, a in enumerate((-22, 0, 22)):
        t = FL.ellipsoid("Tail__feather", (BC.x + math.sin(math.radians(a)) * 0.05, BC.y - BR.y - 0.025, oz + 0.0035),
                         (0.014, 0.05, 0.003), [M["brass_dark"]], 32)
        t.rotation_euler = (0, 0, math.radians(-a))
    # the key at the tail end, above the feathers
    kz = BC.z + 0.016
    ky = BC.y - BR.y * math.sqrt(1 - (0.016 / BR.z) ** 2)
    FL.cyl("SideKey__shaft", (BC.x, ky - 0.022, kz), 0.004, 0.07, M["brass"], rot=(math.radians(90), 0, 0))
    FL.torus("SideKey__bow", (BC.x, ky - 0.057, kz + 0.014), 0.014, 0.004, M["brass"], rot=(math.radians(90), 0, 0))
    F["key_axis"] = [0, -1, 0]
    F["carved"] = carve(F, BC, BR, TAPER)
    _finish(F, ["HeartPump", "Lungs", "VoiceBox", "WingSpring", "FlagCog"], [f"WingPlate{i}" for i in range(1, 5)])
    return F


def build_wyvern(M, origin):
    FL.M_.update(M)
    ox, oy, oz = origin
    BR = Vector((0.078, 0.17, 0.042))
    BC = Vector((ox, oy, oz + BR.z + 0.0004))
    F = {"species": "Wyvern", "interior": [], "keep": [], "body_centre": BC, "body_radii": BR, "attach": {},
         "bone_extra": {"FireGlandGlass": "FireGland", "FireGlandGlow": "FireGland"}}
    body, hinge, piv, pl, dims = shell(M, BC, BR, Vector((0.06, 0.128, 0.036)), 1.8, 0.0)
    RX, RZ, PX, PY, PT, PC = dims
    F["keep"] += [body] + pl
    # the hidden seam: a hairline groove on the plate's free edge (the Inspect step)
    cx = hinge.x + RX + 0.001 + PX * 0.9
    F["attach"]["HiddenSeam"] = {"bone": "PlateHinge", "pos": [cx, BC.y, hinge.z + PC]}
    before = set(bpy.data.objects.keys())
    dtop = deck(M, BC, BR, 0.0, (-0.138, 0.138))
    F["heart"] = heart(M, "HeartA", Vector((BC.x, BC.y + 0.05, dtop + 0.02)), dtop)
    heart(M, "HeartB", Vector((BC.x, BC.y - 0.02, dtop + 0.02)), dtop)
    lungs(M, BC, dtop, 0.037, 0.015, 0.022, 0.03, 0.016)
    # the fire-gland, mounted forward: a brass cap and collar round a glass bulb with an ember inside
    fg = Vector((BC.x, BC.y + 0.108, dtop + 0.0185))
    FL.cyl("FireGland__foot", (fg.x, fg.y, dtop + 0.0006 + 0.0012), 0.009, 0.0024, M["brass_dark"])
    FL.cyl("FireGland__stem", (fg.x, fg.y, dtop + 0.0036 + 0.0025), 0.0028, 0.005, M["brass"])
    FL.sphere("FireGlandGlass__bulb", fg, 0.0125, M["glass"], 48)
    FL.sphere("FireGlandGlow__ember", fg, 0.0062, M["flame"], 24)
    FL.torus("FireGland__collar", (fg.x, fg.y, fg.z - 0.0085), 0.0095, 0.0016, M["brass"])
    FL.cyl("FireGland__cap", (fg.x, fg.y, fg.z + 0.0134), 0.0045, 0.0026, M["brass_dark"])
    # gear-gut toward the tail (the frog's three gears, axles through the deck)
    gz = dtop + 0.006
    before_g = set(bpy.data.objects.keys())
    for (dx, dy, R, t, n, m, ph) in ((-0.02, -0.078, 0.019, 0.0035, 16, "brass", 0.0), (0.0185, -0.088, 0.0135, 0.0035, 12, "brass_dark", 0.13),
                                     (0.003, -0.11, 0.0085, 0.003, 9, "brass", 0.3)):
        FL.gear((BC.x + dx, BC.y + dy, gz + (0.004 if R == 0.0135 else (-0.0025 if R == 0.0085 else 0))), R, t, n, M[m], ph)
    _rename(before_g, "GearGut")
    barrel(M, BC, dtop, 0.047, -0.045)
    flag_cog(M, BC, dtop, -0.046, -0.042)
    bpy.ops.object.light_add(type="POINT", location=(fg.x, fg.y, fg.z))
    bpy.context.active_object.data.energy = 0.3
    F["interior"] = [o for o in bpy.data.objects if o.name not in before]

    # long head with horns and eyes, on a neck
    hc = Vector((ox, oy + 0.215, oz + 0.034))
    FL.ellipsoid("Head__skull", hc, (0.036, 0.058, 0.028), [M["brass"]], 64)
    FL.tube("Head__neck", [(ox, oy + 0.15, oz + 0.04), (ox, oy + 0.18, oz + 0.037), (ox, oy + 0.2, oz + 0.035)], 0.017, M["brass_dark"])
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(radius1=0.0065, radius2=0.0005, depth=0.04, location=(hc.x + sx * 0.02, hc.y - 0.045, hc.z + 0.018),
                                        rotation=(math.radians(-60), sx * math.radians(18), 0), vertices=32)
        h = bpy.context.active_object
        h.name = "Head__horn"
        h.data.materials.append(M["steel_dark"])
        FL._smooth(h)
    eyes(M, hc, 0.024, 0.022, 0.012, 0.0095)
    # folded bat wings: a membrane and three ribs per side
    wy = BC.y + 0.06
    for sx in (-1, 1):
        cx = BC.x + sx * (BR.x * math.sqrt(1 - (0.06 / BR.y) ** 2) + 0.004)
        FL.ellipsoid("Limbs__membrane", (cx, wy, BC.z + 0.003), (0.0085, 0.085, 0.028), [M["leather_dk"]], 64)
        for k, dz in enumerate((-0.012, 0.0, 0.012)):
            FL.tube("Limbs__rib", [(cx + sx * 0.007, wy + 0.075, BC.z + 0.003 + dz * 0.4), (cx + sx * 0.0092, wy, BC.z + 0.003 + dz),
                                   (cx + sx * 0.006, wy - 0.07, BC.z + 0.003 + dz * 0.6)], 0.0017, M["brass"])
    # the tail: out of the rump, down to the wax and coiled there
    pts = [(BC.x, BC.y - 0.15, BC.z - 0.012), (BC.x + 0.004, BC.y - 0.19, oz + 0.016), (BC.x + 0.012, BC.y - 0.22, oz + 0.0085)]
    cc = Vector((BC.x + 0.05, BC.y - 0.235, oz + 0.0085))
    a0 = math.atan2(pts[-1][1] - cc.y, pts[-1][0] - cc.x)
    r0 = (Vector(pts[-1][:2]) - cc.xy).length
    for i in range(1, 22):
        t = i / 21
        a = a0 - t * 1.4 * 2 * math.pi
        r = r0 * (1 - 0.55 * t)
        pts.append((cc.x + math.cos(a) * r, cc.y + math.sin(a) * r, oz + 0.0085))
    FL.tube("Tail__coil", pts, 0.008, M["brass_dark"], res=6)
    # the key on the +X side, behind the wing
    ky = BC.y - 0.07
    kx = BC.x + BR.x * math.sqrt(1 - (0.07 / BR.y) ** 2 - (0.01 / BR.z) ** 2)
    FL.cyl("SideKey__shaft", (kx + 0.025, ky, BC.z + 0.01), 0.004, 0.07, M["brass"], rot=(0, math.radians(90), 0))
    FL.torus("SideKey__bow", (kx + 0.06, ky, BC.z + 0.024), 0.014, 0.004, M["brass"], rot=(0, math.radians(90), 0))
    F["key_axis"] = [1, 0, 0]
    F["carved"] = carve(F, BC, BR, 0.0)
    _finish(F, ["FireGland", "HeartA", "HeartB", "Lungs", "GearGut", "FlagCog"])
    return F
