"""Props batch 53, the secret passages kit (2026-11-11), for nh_props.py: vents, crawl ducts, hidden doors, tunnels and the
triggers that open them, in the school's look (weathered limestone, sooty brick, black riveted iron, brass, crimson #600E1A,
candlelight, moss). Wood only for the boards and the stage deck. Every name and word is invented.

Vents     VentWallLow (Grate0 lift-off), VentWallHigh (Grate0 hinged), VentCeiling (Grate0 drops down), VentFloor (Grate0 lift-off)
Ducts     DuctStraight, DuctCorner, DuctTee, DuctRiser, DuctEndCap (Door0), DuctDamaged
Doors     BookcaseSecretDoor (Door0), FireplacePassage (Slide0), TapestryPassage (Cloth0), SlidingWallPanel (Slide0, Boss0),
          TrapdoorLadder (Door0)
Stair     SecretSpiralStair (Main, Upper, Head; Wall, UpperWall, HeadWall tiled)
Tunnels   TunnelStraight, TunnelCurve, TunnelJunction, TunnelSteps, TunnelDeadEnd (Grate0); Wall (and Floor) tiled
Other     StageCrawlspace (Door0), BoardedPassage (Board0..8)
Triggers  SconceLever (Lever0, Lever0Glow), LooseBrick (Brick0), TiltingBust (Bust0)

SIZING (measured 2026-11-11, E:/NH-Work/props53/logs/crouch.txt): the tallest character (7'0", Height v2 1.22: torso 2.21 x 2.41,
legs 2.61) is 6.12 tall standing; crouched (Crouch / CrouchWalk keyframes) at most 5.24 tall, 4.87 wide and 4.86 deep. With
0.35 for hair, every crawl way is 5.6 wide x 6.0 tall clear (DUCT_W x DUCT_H), every vent you can enter opens at least that, and
the standing passages are 6.4 wide and 7.8 high at the crown (tunnels), 7.5 headroom on the stair.

GRID: ducts are 8-stud modules along Y with their joint planes at y = +-4 (flanges flush on the plane), origin on the INSIDE
floor at the cell centre (the outside bottom is 0.30 lower). Tunnels are 8-stud modules too, origin on the walking floor at the
cell centre, the shell 8 wide; the curve fills a 2 x 2 block of cells (origin at the block's centre). Wall pieces have their back
on y = 0, through-wall pieces (doors) their origin on the wall's centre line. Opening pieces: the FBX origin is the hinge or the
slide origin; the rig is written to art/props/secret_batch53.json (kind, hinge, axis, signed angle, slide) on every build.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, set_group, material
from nh_props_batch3 import sphere, cone, flame
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch9 import foil
import nh_props_batch24 as B24
import nh_props_batch25 as B25
import nh_props_batch30 as B30
import nh_props_batch40 as B40
import nh_props_batch41 as B41
import nh_props_batch43 as B43

DEG = math.pi / 180
PI = math.pi
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T

DUCT_W, DUCT_H = 5.6, 6.0      # crawl clear (7'0" crouched 4.87 x 5.24, + hair, + margin)
DA = DUCT_W / 2                 # duct inner half width
DT = 0.1                        # duct sheet
FL = 0.2                        # flange lip outside the sheet
TA, TS, TC = 3.2, 4.6, 7.8      # tunnel inner half width, springing, crown
TW, TTOP, TBOT = 4.0, 8.6, -0.4  # tunnel shell half width, top, floor slab bottom
RIG = {}
JOINTS = {}                     # prop -> [(name, origin, inward normal)] joint planes checked by run53 --joints


def _rig(prop, piece, kind, hinge, angle=0.0, axis=(0, 0, 1), slide=(0, 0, 0)):
    RIG.setdefault(prop, {})[f"{prop}_{piece}"] = {"kind": kind, "hinge": [round(v, 4) for v in hinge], "axis": list(axis),
                                                   "angle": angle, "slide": [round(v, 4) for v in slide]}


def _write_rig():
    path = os.path.join(P.HERE, "secret_batch53.json")
    old = {}
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf-8"))
        except ValueError:
            old = {}
    old.update(RIG)
    json.dump(old, open(path, "w", encoding="utf-8"), indent=1)


def opening(prop, name, kind, hinge, angle=0.0, axis=(0, 0, 1), slide=(0, 0, 0)):
    """Start an opening piece: its group, its FBX origin (the hinge / slide origin) and its rig entry."""
    set_group(name, hinge=hinge, swing=0)
    _rig(prop, name, kind, hinge, angle, axis, slide)


# ------------------------------------------------------------------ materials

def masonry(name, bw, rh, c1, c2, mortar, grit="NH_Limestone", mortar_w=0.024, bumpk=0.6, moss=0.0, uv="Brk"):
    """Brick or ashlar courses from the piece's own "Brk" UV (studs: u along the run, v up the wall / round the vault), so the
    courses follow a vault's curve; gritty colour from a seamless set, the same bake-time weathering as every material."""
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
    uvn.uv_map = uv
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(uvn.outputs["UV"], sep.inputs["Vector"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    L(sep.outputs["X"], comb.inputs["X"])
    L(sep.outputs["Y"], comb.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.5, 2
    br.squash, br.squash_frequency = 1.0, 1
    L(comb.outputs["Vector"], br.inputs["Vector"])
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = mortar_w
    br.inputs["Mortar Smooth"].default_value = 0.2
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = rh
    gr = P._tex(nt, grit, "color", 0.5, 0, 300)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.9
    L(br.outputs["Color"], mix.inputs[6]); L(gr.outputs["Color"], mix.inputs[7])
    rgh = nt.nodes.new("ShaderNodeMath"); rgh.operation = "MULTIPLY_ADD"
    L(br.outputs["Fac"], rgh.inputs[0]); rgh.inputs[1].default_value = 0.08; rgh.inputs[2].default_value = 0.84
    mv = nt.nodes.new("ShaderNodeValue"); mv.outputs[0].default_value = 0.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = bumpk
    bump.inputs["Distance"].default_value = 0.035
    L(br.outputs["Fac"], bump.inputs["Height"])
    nrm = P._tex(nt, grit, "normal", 0.5, 0, -300)
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6
    L(nrm.outputs["Color"], nm.inputs["Color"]); L(nm.outputs["Normal"], bump.inputs["Normal"])
    P._weather(nt, bs, mix.outputs[2], rgh.outputs[0], mv.outputs[0], bump.outputs["Normal"], 0.25, False, 0.95)
    if moss:
        B40.mossy(m, moss, scale=1.2, low=0.9)
    return m


def kit(M):
    K = B43.kit(M)
    K25 = B25.kit(M)
    K.update({k: K25[k] for k in ("st", "dk", "hollow", "rust", "moss")})
    K.update({
        "brick": masonry("SecretBrick", 0.56, 0.24, (0.115, 0.04, 0.03), (0.08, 0.032, 0.027), (0.17, 0.16, 0.14), moss=0.35),
        "brickdk": masonry("SecretBrickSoot", 0.56, 0.24, (0.07, 0.03, 0.026), (0.05, 0.025, 0.022), (0.1, 0.095, 0.085)),
        "ashlar": masonry("SecretAshlar", 1.35, 0.62, (0.5, 0.48, 0.44), (0.42, 0.4, 0.37), (0.24, 0.23, 0.21), mortar_w=0.012, bumpk=0.4,
                          moss=0.25),
        "lime": B40.mossy(material("SecretLime", "NH_Limestone", tint=(0.72, 0.7, 0.64), scale=0.3, wear=0.4, dirt=1.0), 0.3, low=0.6),
        "limedk": material("SecretLimeDark", "NH_Limestone", tint=(0.42, 0.4, 0.37), scale=0.3, wear=0.3, dirt=1.0),
        "duct": B40.mossy(material("DuctIron", "NH_Iron", tint=(0.12, 0.112, 0.108), scale=0.9, rough_add=0.1, wear=0.55, wear_metal=True,
                                   dirt=1.0), 0.32, scale=1.1, col=(0.14, 0.055, 0.02), low=0.35),
        "ductin": material("DuctIronInside", "NH_Iron", tint=(0.07, 0.066, 0.064), scale=0.9, rough_add=0.15, wear=0.3, wear_metal=True, dirt=1.0),
        "rustd": flat("DuctRust", (0.1, 0.042, 0.02), 0.92, metal=0.1, wear=0.2, dirt=0.9),
        "plank": material("SecretPlank", "NH_Boards", tint=(0.42, 0.34, 0.26), scale=0.22, rough_add=0.1, wear=0.5, dirt=0.95),
        "plankdk": material("SecretPlankDark", "NH_Boards", tint=(0.24, 0.19, 0.15), scale=0.22, rough_add=0.1, wear=0.5, dirt=0.95),
        "ash": flat("ColdAsh", (0.16, 0.155, 0.15), 0.98, dirt=0.7),
        "char": flat("Charcoal", (0.025, 0.022, 0.02), 0.85, dirt=0.4),
        "soot": material("SecretSoot", "NH_Limestone", tint=(0.08, 0.075, 0.07), scale=0.4, wear=0.15, dirt=1.0),
        "velvet": B24.cloth("StageVelvet", (0.19, 0.012, 0.026), rough=0.9, weave=0.006),
        "gloom": flat("PassageGloom", (0.006, 0.006, 0.008), 1.0, dirt=0.0),
        "water": flat("Puddle", (0.02, 0.025, 0.03), 0.04, dirt=0.0),
        "chalkm": flat("ChalkMark", (0.82, 0.8, 0.74), 0.95, dirt=0.2),
        "glow": flat("CandleGlow", (1.0, 0.62, 0.3), 0.5),
        "crimson": material("SecretCrimson", base=(0.2, 0.014, 0.026), rough=0.3, wear=0.3, wear_metal=True, dirt=0.6),
    })
    return K


# ------------------------------------------------------------------ geometry helpers

def bm_obj(name, bm, mat, smooth=False):
    me = bpy.data.meshes.new(name)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0)


def sq_bar(name, pts, r, mat):
    """A square iron bar along a polyline. The profile is wound [(-r,-r),(-r,r),(r,r),(r,-r)] (the square-bar audit fix), so the
    side faces point OUT (nh_props.tube(square=True) made them inside-out before the fix); run53 --normals checks one."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co[0], co[1], co[2], 1)
    prof = bpy.data.curves.new(name + "_prof", "CURVE")
    ps = prof.splines.new("POLY")
    ps.points.add(3)
    for i, (x, y) in enumerate([(-r, -r), (-r, r), (r, r), (r, -r)]):
        ps.points[i].co = (x, y, 0, 1)
    ps.use_cyclic_u = True
    po = bpy.data.objects.new(name + "_prof", prof)
    bpy.context.collection.objects.link(po)
    cu.bevel_mode = "OBJECT"
    cu.bevel_object = po
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    bpy.data.objects.remove(po)
    ob["nh_sqbar"] = len(pts)
    return P._finish(ob, mat, 0)


def rtube(name, pts, r, mat, poly=True):
    return P.tube(name, pts, r, mat, poly=poly)


def orient(bm, target):
    """Flip every face whose normal points away from target(centre) (a point the face should look toward)."""
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector(target(c)) - c) < 0:
            f.normal_flip()


def orient_out(bm, source):
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(c - Vector(source(c))) < 0:
            f.normal_flip()


def grid_surface(name, rows, mat, uvs, target=None, away=None, smooth=True):
    """A quad surface from rows of points (each row the same length), with the "Brk" UV per vertex (uvs: rows of (u, v))."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Brk")
    vs = [[bm.verts.new(tuple(p)) for p in row] for row in rows]
    for a in range(len(rows) - 1):
        for i in range(len(rows[a]) - 1):
            q = (vs[a][i], vs[a][i + 1], vs[a + 1][i + 1], vs[a + 1][i])
            if len({id(v) for v in q}) < 3:
                continue
            ij = ((a, i), (a, i + 1), (a + 1, i + 1), (a + 1, i))
            try:
                f = bm.faces.new(q)
            except ValueError:
                continue
            for lp, (r_, c_) in zip(f.loops, ij):
                lp[uvl].uv = uvs[r_][c_]
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    if target:
        orient(bm, target)
    if away:
        orient_out(bm, away)
    return bm_obj(name, bm, mat, smooth)


def poly_face(name, polys, mat, normal, uvfn=None, thick=0.0):
    """Flat (possibly concave) polygons of 3D points facing `normal`, triangulated with mathutils' polyfill (robust for any
    simple polygon; bmesh's ear clip cut chords across concave arcs); optional "Brk" UV uvfn(point)."""
    from mathutils.geometry import tessellate_polygon
    nv = Vector(normal).normalized()
    ax = Vector((1, 0, 0)) if abs(nv.x) < 0.9 else Vector((0, 1, 0))
    e1 = nv.cross(ax).normalized()
    e2 = nv.cross(e1)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Brk")
    for poly in polys:
        P3 = [Vector(p) for p in poly]
        vs = [bm.verts.new(tuple(p)) for p in P3]
        tris = tessellate_polygon([[(p.dot(e1), p.dot(e2), 0.0) for p in P3]])
        for t in tris:
            try:
                f = bm.faces.new([vs[i] for i in t])
            except ValueError:
                continue
            if f.normal.dot(nv) < 0:
                f.normal_flip()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if uvfn:
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = uvfn(lp.vert.co)
    ob = bm_obj(name, bm, mat)
    if thick:
        md = ob.modifiers.new("Solid", "SOLIDIFY")
        md.thickness = thick
        md.offset = 1
    return ob


def plen(prof):
    out = [0.0]
    for a, b in zip(prof, prof[1:]):
        out.append(out[-1] + math.dist(a, b))
    return out


def sweep(name, prof, frames, mat, curv=0.0, target=None, away=None, closed=False):
    """A cross-section prof [(x, z)] swept through frames [(origin, side, up, t)]: x along side, z along up, t the length along the
    path; "Brk" UV = (t * (1 - x * curv), profile length). target / away orient the faces (toward / away from a point fn)."""
    pr = list(prof) + ([prof[0]] if closed else [])
    L = plen(pr)
    rows, uvs = [], []
    for o, s, u, t in frames:
        rows.append([Vector(o) + Vector(s) * x + Vector(u) * z for x, z in pr])
        uvs.append([(t * (1 - x * curv), L[i]) for i, (x, z) in enumerate(pr)])
    return grid_surface(name, rows, mat, uvs, target=target, away=away)


def frames_line(p0, p1, n, up=(0, 0, 1)):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    Lh = Vector((d.x, d.y, 0)).length
    dh = Vector((d.x, d.y, 0)).normalized()
    s = dh.cross(Vector(up)).normalized()
    return [(p0 + d * (i / n), s, Vector(up), Lh * i / n) for i in range(n + 1)]


def frames_arc(c, R, a0, a1, n, z=0.0):
    """Frames along a circle about c (x, y) from angle a0 to a1 (radians), side pointing to the centre when a1 < a0."""
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        o = Vector((c[0] + R * math.cos(a), c[1] + R * math.sin(a), z))
        tang = Vector((-math.sin(a), math.cos(a), 0)) * (1 if a1 > a0 else -1)
        s = tang.cross(Vector((0, 0, 1))).normalized()
        out.append((o, s, Vector((0, 0, 1)), R * abs(a - a0)))
    return out


def vault_prof(a=TA, hs=TS, n=20, z0=0.0):
    """Tunnel inner section from the right foot (a, z0) up the wall, over the round vault, down to the left foot."""
    pts = [(a, z0), (a, hs)]
    for i in range(1, n):
        th = PI * i / n
        pts.append((a * math.cos(th), hs + a * math.sin(th)))
    pts += [(-a, hs), (-a, z0)]
    return pts


def vault_z(x, a=TA, hs=TS):
    return hs + math.sqrt(max(0.0, a * a - x * x))


def end_ring(name, mtx, mat, bottom=TBOT, top=TTOP, hw=TW, a=TA, hs=TS, z_open=TBOT, n=20, uv=True):
    """The flush end of a tunnel shell: the shell rectangle less the vault opening (down to z_open), in a plane: local (x, z)
    -> mtx @ (x, 0, z); local -Y is the outward normal."""
    half = []
    for sgn in (1, -1):
        pts = [(sgn * a, z_open), (sgn * hw, bottom), (sgn * hw, top), (0, top), (0, hs + a)]
        arc = [(sgn * a * math.cos(PI / 2 * (1 - i / n)), hs + a * math.sin(PI / 2 * (1 - i / n))) for i in range(1, n + 1)]
        pts = [(sgn * a, z_open), (sgn * hw, bottom), (sgn * hw, top), (0, top)] + [(0, hs + a)] + arc[:-1] + [(sgn * a, hs)]
        pts[1] = (sgn * hw, bottom)
        half.append([mtx @ Vector((x, 0, z)) for x, z in pts])
    nrm = (mtx.to_3x3() @ Vector((0, -1, 0)))
    return poly_face(name, half, mat, nrm, uvfn=(lambda co: (co.x + co.y, co.z)) if uv else None)


def rivet_row(prefix, p0, p1, n, normal, mat, r=0.03):
    p0, p1, nv = Vector(p0), Vector(p1), Vector(normal).normalized()
    q = Vector((0, 0, 1)).rotation_difference(nv)
    for i in range(n):
        p = p0 + (p1 - p0) * (i / max(1, n - 1))
        ob = sphere(f"{prefix}{i}", r, tuple(p), mat, seg=6, rings=3, scale=(1, 1, 0.55))
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = q


def label(name, text, mat, cx, y, cz, w, h, depth=0.012):
    return B43.label(name, text, mat, cx, y, cz, w, h, depth=depth)


def moss_tufts(prefix, pts, K, rnd, size=0.1):
    from nh_props_batch8 import _moss
    _moss(prefix, pts, K["moss"], rnd, size=size)


# ------------------------------------------------------------------ crawl ducts (riveted sheet iron)

def flange(prefix, K, mtx, lip=FL, t=0.12, rivets=True):
    """An angle-iron joint frame round the duct, its face on the local plane y = 0, the frame into local +Y (into the piece)."""
    s = _mark()
    o = DA + DT
    iron = K["iron"]
    W = 2 * (o + lip)
    box(f"{prefix}Top", (W, t, lip), (0, t / 2, DUCT_H + DT + lip / 2), iron, bevel=0.02)
    box(f"{prefix}Bot", (W, t, lip), (0, t / 2, -DT - lip / 2), iron, bevel=0.02)
    for sx in (-1, 1):
        box(f"{prefix}Side{sx}", (lip, t, DUCT_H + 2 * DT), (sx * (o + lip / 2), t / 2, DUCT_H / 2), iron, bevel=0.02)
    if rivets:
        for sx in (-1, 1):
            rivet_row(f"{prefix}RvS{sx}", (sx * (o + lip + 0.005), t * 0.5, 0.4), (sx * (o + lip + 0.005), t * 0.5, DUCT_H - 0.4), 9, (sx, 0, 0), iron,
                      r=0.035)
        for sz, z in ((1, DUCT_H + DT + lip + 0.005), (-1, -DT - lip - 0.005)):
            rivet_row(f"{prefix}RvZ{sz}", (-o + 0.4, t * 0.5, z), (o - 0.4, t * 0.5, z), 8, (0, 0, sz), iron, r=0.035)
    _xform(s, mtx)


def duct_box(prefix, K, y0, y1, skip=(), hole=None):
    """Straight duct walls between y0 and y1: floor, roof and sides (skip: 'L', 'R', 'F', 'C'); inner faces at x = +-DA, z = 0
    and DUCT_H. hole: (side, ya, yb) leaves that side's wall out between ya and yb."""
    L = y1 - y0
    yc = (y0 + y1) / 2
    m, mi = K["duct"], K["ductin"]
    if "F" not in skip:
        box(f"{prefix}Floor", (2 * DA, L, DT), (0, yc, -DT / 2), mi, bevel=0.01)
    if "C" not in skip:
        box(f"{prefix}Roof", (2 * DA, L, DT), (0, yc, DUCT_H + DT / 2), m, bevel=0.01)
    for sx, k in ((-1, "L"), (1, "R")):
        if k in skip:
            continue
        spans = [(y0, y1)]
        if hole and hole[0] == k:
            spans = [(y0, hole[1]), (hole[2], y1)]
        for j, (a, b) in enumerate(spans):
            if b - a > 1e-3:
                box(f"{prefix}Side{k}{j}", (DT, b - a, DUCT_H + 2 * DT), (sx * (DA + DT / 2), (a + b) / 2, DUCT_H / 2), m, bevel=0.01)


def seam(prefix, K, y, mtx=None, rivets=True):
    """A riveted lap strip round the duct at y (a sheet joint)."""
    s = _mark()
    o = DA + DT
    m = K["duct"]
    box(f"{prefix}T", (2 * o + 0.06, 0.3, 0.03), (0, y, DUCT_H + DT + 0.015), m, bevel=0.008)
    box(f"{prefix}B", (2 * o + 0.06, 0.3, 0.03), (0, y, -DT - 0.015), m, bevel=0.008)
    for sx in (-1, 1):
        box(f"{prefix}S{sx}", (0.03, 0.3, DUCT_H + 2 * DT), (sx * (o + 0.015), y, DUCT_H / 2), m, bevel=0.008)
        if rivets:
            rivet_row(f"{prefix}R{sx}", (sx * (o + 0.03), y, 0.5), (sx * (o + 0.03), y, DUCT_H - 0.5), 7, (sx, 0, 0), K["iron"], r=0.028)
    if rivets:
        rivet_row(f"{prefix}RT", (-o + 0.5, y, DUCT_H + DT + 0.03), (o - 0.5, y, DUCT_H + DT + 0.03), 7, (0, 0, 1), K["iron"], r=0.028)
    if mtx is not None:
        _xform(s, mtx)


def plate(prefix, K, text, x, y, z, face=(1, 0, 0), w=1.1, h=0.42):
    """A brass maker's / duct number plate with raised letters, on a face looking along face (+X or -X or -Y)."""
    s = _mark()
    box(f"{prefix}", (w, 0.04, h), (0, 0.02, 0), K["brass"], bevel=0.012)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cyl(f"{prefix}Screw{sx}{sz}", 0.03, 0.02, (sx * (w / 2 - 0.07), -0.005, sz * (h / 2 - 0.07)), K["brass"], rot=(PI / 2, 0, 0), verts=8,
                bevel=0.0)
    label(f"{prefix}Txt", text, K["brass"], 0, 0.0, 0, w - 0.22, h - 0.16, depth=0.012)
    yaw = math.atan2(face[0], -face[1])
    _xform(s, T(x, y, z) @ RZ(yaw))


def duct_dust(prefix, K, rnd, y0, y1, n=4):
    """Grime on the duct floor: a few dust drifts along the walls and rust flakes."""
    for i in range(n):
        sx = rnd.choice((-1, 1))
        y = rnd.uniform(y0 + 1.5, y1 - 1.5)
        lathe(f"{prefix}Drift{i}", [(0, 0), (0.5, 0), (0.3, 0.035), (0, 0.05)], K["ash"], seg=12, loc=(sx * (DA - 0.5), y, 0.0),
              scale=(1.0, rnd.uniform(1.6, 2.6)))
    for i in range(n * 2):
        box(f"{prefix}Flake{i}", (rnd.uniform(0.08, 0.2), rnd.uniform(0.06, 0.15), 0.012), (rnd.uniform(-DA + 0.4, DA - 0.4), rnd.uniform(y0 + 0.3, y1 - 0.3), 0.006),
            K["rustd"], bevel=0.0, rot=(0, 0, rnd.uniform(0, PI)))


def duct_straight(M):
    """An 8-stud crawl duct of riveted black sheet iron (5.6 x 6.0 clear), angle-iron flanges flush on its joint planes, a lap
    seam with rivets, a bolted inspection plate and a brass number plate, grime and rust on the floor inside."""
    K = kit(M)
    rnd = random.Random(5301)
    duct_box("D", K, -4, 4)
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(0, 4, 0) @ RZ(PI))
    seam("Seam", K, 0.0)
    # a bolted inspection plate on the right side, and the duct's number
    box("Insp", (0.05, 1.6, 1.3), (DA + DT + 0.025, 2.0, 3.2), K["duct"], bevel=0.015)
    for j, (dy, dz) in enumerate(((-0.65, -0.5), (0.65, -0.5), (-0.65, 0.5), (0.65, 0.5))):
        cyl(f"InspBolt{j}", 0.05, 0.05, (DA + DT + 0.07, 2.0 + dy, 3.2 + dz), K["iron"], rot=(0, PI / 2, 0), verts=6, bevel=0.0)
    plate("NumPlate", K, "DUCT 7", DA + DT, -2.0, 4.4, face=(1, 0, 0))
    duct_dust("Dust", K, rnd, -4, 4)
    JOINTS["DuctStraight"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0))]
    return _dims()


def duct_corner(M):
    """A mitred 90-degree elbow in five gores (centreline radius 4) inside one cell: in at y = -4 heading +Y, out at x = +4
    heading +X; flanges on both joint planes, riveted mitre seams, a scorched patch where a lamp once stood."""
    K = kit(M)
    rnd = random.Random(5302)
    inner = [(DA, 0), (DA, DUCT_H), (-DA, DUCT_H), (-DA, 0)]
    outer = [(DA + DT, -DT), (DA + DT, DUCT_H + DT), (-DA - DT, DUCT_H + DT), (-DA - DT, -DT)]
    c = (4.0, -4.0)
    n = 5
    fr = frames_arc(c, 4.0, PI, PI / 2, n)
    # frames_arc gives side pointing at the centre for a1 < a0; the profile's +x is toward the centre (the inside of the bend)
    for k in range(n):
        f2 = [fr[k], fr[k + 1]]
        sweep(f"In{k}", inner, f2, K["ductin"], closed=True, target=lambda p, k=k: (p.x * 0 + (c[0] - 4.0 * math.cos(PI - (k + 0.5) * PI / 2 / n)),
                                                                                  c[1] + 4.0 * math.sin(PI - (k + 0.5) * PI / 2 / n), DUCT_H / 2))
        sweep(f"Out{k}", outer, f2, K["duct"], closed=True, away=lambda p, k=k: ((c[0] - 4.0 * math.cos(PI - (k + 0.5) * PI / 2 / n)),
                                                                                 c[1] + 4.0 * math.sin(PI - (k + 0.5) * PI / 2 / n), DUCT_H / 2))
    for k in range(1, n):
        o, s, u, t = fr[k]
        seam(f"Mitre{k}", K, 0.0, mtx=Matrix.Translation(o) @ RZ(math.atan2(s.y, s.x)), rivets=k % 2 == 1)
    # the sheet's cut ends, closed between the inner and outer skins
    o_ = DA + DT
    bands = [[(-o_, -DT), (o_, -DT), (DA, 0), (-DA, 0)], [(o_, -DT), (o_, DUCT_H + DT), (DA, DUCT_H), (DA, 0)],
             [(o_, DUCT_H + DT), (-o_, DUCT_H + DT), (-DA, DUCT_H), (DA, DUCT_H)], [(-o_, DUCT_H + DT), (-o_, -DT), (-DA, 0), (-DA, DUCT_H)]]
    for k, (f, sgn) in enumerate(((fr[0], -1), (fr[-1], 1))):
        o, s, u, t = f
        tang = u.cross(s)
        poly_face(f"Cut{k}", [[o + s * x + u * z for x, z in bd] for bd in bands], K["duct"], tang * sgn)
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(4, 0, 0) @ RZ(PI / 2))
    # soot from an old lamp on the outer curve, a dropped candle stub
    lathe("Stub", [(0, 0), (0.07, 0), (0.07, 0.18), (0.05, 0.2), (0, 0.2)], K["wax"], seg=10, loc=(0.9, 0.4, 0.0))
    for i in range(5):
        box(f"Flake{i}", (rnd.uniform(0.08, 0.2), rnd.uniform(0.06, 0.15), 0.012), (rnd.uniform(0.5, 2.5), rnd.uniform(-2.5, -0.5), 0.006), K["rustd"],
            bevel=0.0, rot=(0, 0, rnd.uniform(0, PI)))
    JOINTS["DuctCorner"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (4, 0, 0), (-1, 0, 0))]
    return _dims()


def duct_tee(M):
    """A T: the run along Y with a branch out of the right side to x = +4, all three ends flanged on the grid; a brass
    direction plate (CHAPEL / LIBRARY, invented) on the junction and a riveted gusset over the branch."""
    K = kit(M)
    rnd = random.Random(5303)
    duct_box("D", K, -4, 4, hole=("R", -DA - DT, DA + DT))
    # the branch stub, x from the run's side out to the joint plane at x = 4
    x0 = DA
    Lb = 4 - x0
    box("BFloor", (Lb, 2 * DA, DT), (x0 + Lb / 2, 0, -DT / 2), K["ductin"], bevel=0.01)
    box("BRoof", (Lb, 2 * DA, DT), (x0 + Lb / 2, 0, DUCT_H + DT / 2), K["duct"], bevel=0.01)
    for sy in (-1, 1):
        box(f"BSide{sy}", (Lb, DT, DUCT_H + 2 * DT), (x0 + Lb / 2, sy * (DA + DT / 2), DUCT_H / 2), K["duct"], bevel=0.01)
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(0, 4, 0) @ RZ(PI))
    flange("FC", K, T(4, 0, 0) @ RZ(PI / 2))
    for sz, z in ((1, DUCT_H + DT + 0.015), (-1, -DT - 0.015)):
        box(f"Gusset{sz}", (1.2, 2 * DA + 1.0, 0.03), (DA + 0.4, 0, z), K["duct"], bevel=0.008)
    plate("Dir", K, "CHAPEL  >", -DA, 0.0, 4.6, face=(1, 0, 0), w=1.6)
    plate("Dir2", K, "<  LIBRARY", -DA, 0.0, 4.0, face=(1, 0, 0), w=1.6)
    duct_dust("Dust", K, rnd, -4, 4, n=3)
    JOINTS["DuctTee"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0)), ("C", (4, 0, 0), (-1, 0, 0))]
    return _dims()


def duct_riser(M):
    """A riser shaft up one storey (8): in at the bottom from y = -4, out at the top to y = +4 (its inside floor 8 up), iron
    ladder rungs up the side wall, stiffening bands, a hand-painted UP arrow."""
    K = kit(M)
    m, mi, iron = K["duct"], K["ductin"], K["iron"]
    S = DA                    # shaft inner half size
    ZT = 8 + DUCT_H           # the shaft's inner top (the upper duct's roof)
    o = S + DT
    box("Floor", (2 * S, 2 * S, DT), (0, 0, -DT / 2), mi, bevel=0.01)
    box("Roof", (2 * S, 2 * S, DT), (0, 0, ZT + DT / 2), m, bevel=0.01)
    for sx in (-1, 1):
        box(f"Side{sx}", (DT, 2 * o, ZT + 2 * DT), (sx * (S + DT / 2), 0, ZT / 2), m, bevel=0.01)
    # -Y wall above the bottom opening, +Y wall below the top opening
    box("WallF", (2 * S, DT, ZT - DUCT_H + DT), (0, -S - DT / 2, DUCT_H + (ZT - DUCT_H + DT) / 2), m, bevel=0.01)
    box("WallB", (2 * S, DT, 8 + DT), (0, S + DT / 2, (8 + DT) / 2 - DT), m, bevel=0.01)
    # the stubs to the joint planes
    for k, (ya, yb, zb) in enumerate(((-4, -S - DT, 0.0), (S + DT, 4, 8.0))):
        Lb = yb - ya
        yc = (ya + yb) / 2
        box(f"StubFloor{k}", (2 * S, Lb, DT), (0, yc, zb - DT / 2), mi, bevel=0.01)
        box(f"StubRoof{k}", (2 * S, Lb, DT), (0, yc, zb + DUCT_H + DT / 2), m, bevel=0.01)
        for sx in (-1, 1):
            box(f"StubSide{k}{sx}", (DT, Lb, DUCT_H + 2 * DT), (sx * (S + DT / 2), yc, zb + DUCT_H / 2), m, bevel=0.01)
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(0, 4, 8.0) @ RZ(PI))
    # stiffening bands round the shaft
    for j, z in enumerate((3.0, 7.0, 11.0)):
        for sx in (-1, 1):
            box(f"BandX{j}{sx}", (0.05, 2 * o + 0.1, 0.22), (sx * (o + 0.025), 0, z), iron, bevel=0.01)
        for sy in (-1, 1):
            if (sy < 0 and z < DUCT_H) or (sy > 0 and z > 8):
                continue
            box(f"BandY{j}{sy}", (2 * o, 0.05, 0.22), (0, sy * (o + 0.025), z), iron, bevel=0.01)
    # ladder rungs on the -X wall inside (staples standing off the wall)
    for i in range(16):
        z = 0.8 + i * 0.8
        sq_bar(f"Rung{i}", [(-S, -1.0, z - 0.05), (-S + 0.35, -1.0, z), (-S + 0.35, 1.0, z), (-S, 1.0, z - 0.05)], 0.035, iron)
    # a painted arrow on the inside of the +X wall
    for j, pts in enumerate(([(S - 0.004, 0.0, 2.2), (S - 0.004, 0.0, 3.6)], [(S - 0.004, -0.35, 3.2), (S - 0.004, 0.0, 3.6), (S - 0.004, 0.35, 3.2)])):
        rtube(f"Arrow{j}", pts, 0.035, K["chalkm"])
    JOINTS["DuctRiser"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 8), (0, -1, 0))]
    return _dims()


def duct_end_cap(M):
    """A blanking end for a duct run: a 1.4 deep riveted box with a flange on its joint plane (the ORIGIN is the joint plane's
    centre on the inside floor) and a small hinged spy hatch (Door0, 1.2 x 0.8, not a way through) with a louvred cover."""
    K = kit(M)
    m, mi, iron = K["duct"], K["ductin"], K["iron"]
    D = 1.4
    duct_box("D", K, 0.0, D)
    flange("F", K, T(0, 0, 0))
    # the end plate with a hatch hole (four plates round the hole)
    yE = D + DT / 2
    hx0, hx1, hz0, hz1 = -0.6, 0.6, 3.2, 4.0
    for k, (x0, x1, z0, z1) in enumerate(((-DA - DT, DA + DT, -DT, hz0), (-DA - DT, DA + DT, hz1, DUCT_H + DT), (-DA - DT, hx0, hz0, hz1), (hx1, DA + DT, hz0, hz1))):
        box(f"End{k}", (x1 - x0, DT, z1 - z0), ((x0 + x1) / 2, yE, (z0 + z1) / 2), m, bevel=0.0)
    for sz in (-1, 1):
        box(f"EndRib{sz}", (2 * DA + 0.2, 0.05, 0.2), (0, D + DT + 0.025, DUCT_H / 2 + sz * 2.0), iron, bevel=0.01)
    rivet_row("EndRv", (-DA + 0.3, D + DT + 0.01, DUCT_H - 0.25), (DA - 0.3, D + DT + 0.01, DUCT_H - 0.25), 10, (0, 1, 0), iron)
    rivet_row("EndRv2", (-DA + 0.3, D + DT + 0.01, 0.25), (DA - 0.3, D + DT + 0.01, 0.25), 10, (0, 1, 0), iron)
    # the spy hatch, hinged on its top edge, opening outward (+Y, away from the duct)
    hinge = (0.0, D + DT + 0.02, hz1 + 0.06)
    opening("DuctEndCap", "Door0", "hatch", hinge, angle=-95, axis=(1, 0, 0))
    box("Hatch", (1.36, 0.05, 0.96), (0, D + DT + 0.045, (hz0 + hz1) / 2), m, bevel=0.012)
    for i in range(4):
        box(f"Louvre{i}", (1.1, 0.12, 0.04), (0, D + DT + 0.09, hz0 + 0.18 + i * 0.16), iron, bevel=0.005, rot=(-0.6, 0, 0))
    cyl("Knuckle", 0.04, 1.0, (0, D + DT + 0.02, hz1 + 0.06), iron, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
    hoop("Pull", (0, D + DT + 0.1, hz0 + 0.02), 0.07, "Y", K["brass"], thick=0.012)
    set_group("Main")
    JOINTS["DuctEndCap"] = [("A", (0, 0, 0), (0, 1, 0))]
    return _dims()


def duct_damaged(M):
    """A straight duct rusted through: the right side eaten away in a ragged hole the full height (5.5 wide), its edges peeled
    outward in bent flaps, the roof sagging on a snapped seam, rust scale and flakes on the floor and below the hole."""
    K = kit(M)
    rnd = random.Random(5306)
    m, mi, iron, rs = K["duct"], K["ductin"], K["iron"], K["rustd"]
    duct_box("D", K, -4, 4, skip=("R",))
    # the right wall as a U: the hole open to the roof seam, its ragged edge kept outside the clear 5.5 x 6.0
    hw = 2.75
    edge = []
    for i in range(15):
        t = i / 14
        z = DUCT_H + DT - t * (DUCT_H + DT - 0.25)
        edge.append((hw + rnd.uniform(0.05, 0.4), z))
    bot = [(hw * (1 - 2 * i / 12), 0.12 + rnd.uniform(0.0, 0.12)) for i in range(13)]
    left = [(-hw - rnd.uniform(0.05, 0.4), 0.25 + (DUCT_H + DT - 0.25) * i / 14) for i in range(15)]
    outline = [(-4, -DT), (4, -DT), (4, DUCT_H + DT)] + edge + bot[1:-1] + left + [(-4, DUCT_H + DT)]
    x = DA + DT / 2
    poly_face("WallR", [[(x - DT / 2, y, z) for y, z in outline]], m, (1, 0, 0), thick=DT)
    # bent flaps peeled outward from the hole's edges (outside x = DA + DT, never into the duct)
    for i in range(5):
        z = 1.0 + i * 1.05
        sgn = 1 if i % 2 else -1
        yb = sgn * (hw + 0.25)
        L = rnd.uniform(0.35, 0.6)
        s_ = _mark()
        hh = rnd.uniform(0.45, 0.7)
        prism(f"Flap{i}", [(0.0, -hh / 2), (L * 0.55, -hh * 0.4), (L, -hh * 0.05), (L * 0.7, hh * 0.25), (L * 0.35, hh * 0.45), (0.0, hh / 2)], 0.0,
              0.025, m, bevel=0.004)
        # hinged on the wall's outer face just outside the ragged edge, peeled out and back over the hole
        _xform(s_, T(DA + DT + 0.016, sgn * (hw + 0.43), z) @ RZ(-sgn * 0.55) @ RX(rnd.uniform(-0.15, 0.15)))
    # the sagging roof: a cracked seam with a drooping plate edge over the hole (above the clear height)
    box("RoofCrack", (0.6, 5.6, 0.04), (DA + DT - 0.15, 0, DUCT_H + DT + 0.02), rs, bevel=0.005, rot=(0.0, 0.06, 0))
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(0, 4, 0) @ RZ(PI))
    seam("SeamA", K, -3.4)
    seam("SeamB", K, 3.4)
    # rust scale inside and fallen outside the hole
    for i in range(14):
        xx = rnd.uniform(-DA + 0.3, DA + 0.6)
        box(f"Scale{i}", (rnd.uniform(0.1, 0.32), rnd.uniform(0.08, 0.25), 0.015), (min(xx, DA - 0.2), rnd.uniform(-3.5, 3.5), 0.008), rs, bevel=0.0,
            rot=(0, 0, rnd.uniform(0, PI)))
    for i in range(6):
        lathe(f"RustHeap{i}", [(0, 0), (0.3, 0), (0.15, 0.06), (0, 0.08)], rs, seg=10, loc=(rnd.uniform(-DA + 0.6, DA - 0.6), rnd.uniform(-3, 3), 0.0),
              scale=(1, rnd.uniform(1, 1.8)))
    JOINTS["DuctDamaged"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0))]
    return _dims()


# ------------------------------------------------------------------ vents

def surround(prefix, K, hw, z0, z1, w=0.75, d=0.3, mat=None, y=0.0, head=0.85, key=True):
    """A chamfered limestone architrave round a rectangular opening (hw half width, z0 to z1), on a wall face at y, projecting d."""
    mat = mat or K["lime"]
    for sx in (-1, 1):
        box(f"{prefix}Jamb{sx}", (w, d, z1 - z0 + head), (sx * (hw + w / 2), y - d / 2, z0 + (z1 - z0 + head) / 2), mat, bevel=0.05)
    box(f"{prefix}Head", (2 * hw, d, head), (0, y - d / 2, z1 + head / 2), mat, bevel=0.05)
    if key:
        box(f"{prefix}Key", (0.7, d + 0.1, head + 0.2), (0, y - d / 2 - 0.05, z1 + head / 2 + 0.05), mat, bevel=0.05)


def louvre_grate(prefix, K, w, h, n=12, frame=0.18, t=0.12):
    """A cast-iron louvred grille w x h, built at the origin with its back on y = 0 (front toward -Y), bottom at z = 0."""
    iron = K["iron"]
    for sx in (-1, 1):
        box(f"{prefix}Stile{sx}", (frame, t, h), (sx * (w / 2 - frame / 2), -t / 2, h / 2), iron, bevel=0.02)
    for k, z in enumerate((frame / 2, h - frame / 2)):
        box(f"{prefix}Rail{k}", (w - 2 * frame, t, frame), (0, -t / 2, z), iron, bevel=0.02)
    box(f"{prefix}Mid", (0.12, t * 0.8, h - 2 * frame), (0, -t / 2, h / 2), iron, bevel=0.015)
    span = h - 2 * frame
    for i in range(n):
        z = frame + span * (i + 0.5) / n
        box(f"{prefix}Blade{i}", (w - 2 * frame, 0.035, span / n * 1.25), (0, -t / 2, z), iron, bevel=0.006, rot=(-0.75, 0, 0))


def vent_wall_low(M):
    """A floor-level wall vent you can crawl into (5.6 x 6.0 clear): a chamfered limestone architrave with a keystone and the
    heating maker's cast plate (MORROW & SONS, invented), a cast-iron louvred grille (Grate0) that lifts off its two brass
    wing bolts, and a sheet-iron throat into the wall ending in a duct flange (a DuctStraight bolts to it at y = +1.0)."""
    K = kit(M)
    rnd = random.Random(5311)
    hw = DA
    surround("S", K, hw, 0.0, DUCT_H, w=0.8, d=0.32, key=False)
    box("Sill", (2 * hw + 1.9, 0.5, 0.18), (0, -0.25, 0.09), K["limedk"], bevel=0.04)
    plate("Maker", K, "MORROW & SONS 1879", 0, -0.32, DUCT_H + 0.45, face=(0, -1, 0), w=2.2, h=0.36)
    # the throat: sheet iron inside the wall, y 0 .. 1.0, with a flange on its far end (into +Y)
    s = _mark()
    duct_box("Thr", K, -1.0, 0.0)
    _xform(s, T(0, 1.0, 0))
    flange("F", K, T(0, 1.0, 0) @ RZ(PI))
    box("Gloom", (2 * DA, 0.02, DUCT_H), (0, 0.98, DUCT_H / 2), K["gloom"], bevel=0.0)
    # the grille rests against the architrave's face, hung on two bolts: lift-off (its origin at its bottom centre)
    y0 = -0.32
    opening("VentWallLow", "Grate0", "lift", (0.0, y0, 0.18), slide=(0.0, -1.4, -0.18))
    s = _mark()
    louvre_grate("G", K, 2 * hw + 0.5, DUCT_H + 0.25, n=14)
    for sx in (-1, 1):
        cyl(f"Wing{sx}", 0.06, 0.12, (sx * (hw - 0.1), -0.18, DUCT_H - 0.25), K["brass"], rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
        box(f"WingEar{sx}", (0.32, 0.04, 0.08), (sx * (hw - 0.1), -0.25, DUCT_H - 0.25), K["brass"], bevel=0.01)
        tube_h = [(sx * 0.9, -0.12, 0.5), (sx * 0.9, -0.3, 0.55), (sx * 0.9, -0.3, 0.95), (sx * 0.9, -0.12, 1.0)]
        rtube(f"Lift{sx}", tube_h, 0.03, K["iron"])
    _xform(s, T(0, y0, 0.18))
    set_group("Main")
    moss_tufts("Moss", [(-hw - 1.0, -0.45, 0.2), (hw + 0.95, -0.42, 0.2)], K, rnd)
    return _dims()


def gothic_grille(prefix, K, w, h, bars=9, t=0.14):
    """A wrought-iron grille of square bars w x h (bottom at z = 0, centred, plane y = -t/2): stiles, rails, uprights with
    quatrefoil rings between two rails."""
    iron = K["iron"]
    r = 0.06
    y = -t / 2
    for sx in (-1, 1):
        sq_bar(f"{prefix}Stile{sx}", [(sx * (w / 2 - r), y, r), (sx * (w / 2 - r), y, h - r)], r, iron)
    for k, z in enumerate((r, h * 0.32, h * 0.68, h - r)):
        sq_bar(f"{prefix}Rail{k}", [(-w / 2 + r, y, z), (w / 2 - r, y, z)], r * (1.0 if k in (0, 3) else 0.8), iron)
    for i in range(bars):
        x = -w / 2 + w * (i + 1) / (bars + 1)
        sq_bar(f"{prefix}Bar{i}", [(x, y, r), (x, y, h - r)], 0.04, iron)
    for i in range(bars + 1):
        x = -w / 2 + w * (i + 0.5) / (bars + 1)
        hoop(f"{prefix}Ring{i}", (x, y, h * 0.5), min(0.2, w / (bars + 1) * 0.45), "Y", iron, thick=0.022)


def vent_wall_high(M):
    """A high wall vent (bottom suggested 7.5 up) you can climb into: a gothic limestone hood with a pointed tympanum of blind
    tracery over a 5.6 x 6.0 opening, a moulded corbel ledge to stand on, iron climbing staples down the wall below, and a
    hinged wrought-iron grille (Grate0) that swings out on its left side, its hasp hanging open."""
    K = kit(M)
    rnd = random.Random(5312)
    hw = DA
    st, sd = K["lime"], K["limedk"]
    surround("S", K, hw, 0.0, DUCT_H, w=0.7, d=0.36, head=0.6)
    # the pointed hood over the head: a tympanum with a sunk quatrefoil
    z1 = DUCT_H + 0.6
    arch = B43.arch_xz(-hw - 0.7, hw + 0.7, z1, 3.4, n=14)
    prism("Tympanum", arch, -0.18, 0.36, st)
    hood = [(x, -0.4, z + 0.12) for x, z in B43.arch_xz(-hw - 0.85, hw + 0.85, z1 - 0.05, 3.6, n=16)]
    rtube("HoodMould", hood, 0.09, st)
    foil("Foil", 0, -0.37, z1 + 1.0, 0.55, sd, lobes=4, thick=0.05)
    # the ledge (corbel) under the opening, and staples down the wall
    box("Ledge", (2 * hw + 1.8, 1.0, 0.25), (0, -0.5, -0.125), st, bevel=0.05)
    for sx in (-1, 0, 1):
        prism(f"Corbel{sx}", [(0.0, -0.25), (-0.9, -0.25), (-0.9, -0.5), (-0.35, -0.95), (0.0, -0.95)], sx * 2.2, 0.5, sd, plane="YZ", bevel=0.03)
    for i in range(4):
        z = -1.2 - i * 0.9
        sq_bar(f"Staple{i}", [(-0.45, 0.0, z), (-0.45, -0.32, z), (0.45, -0.32, z), (0.45, 0.0, z)], 0.035, K["iron"])
    # throat and flange as on the low vent
    s = _mark()
    duct_box("Thr", K, -1.0, 0.0)
    _xform(s, T(0, 1.0, 0))
    flange("F", K, T(0, 1.0, 0) @ RZ(PI))
    box("Gloom", (2 * DA, 0.02, DUCT_H), (0, 0.98, DUCT_H / 2), K["gloom"], bevel=0.0)
    # the grille, hinged at its left edge in front of the architrave; it swings out toward -Y
    y0 = -0.36
    xh = -hw - 0.2
    opening("VentWallHigh", "Grate0", "swing", (xh, y0 - 0.07, 0.0), angle=-110)
    s = _mark()
    gothic_grille("G", K, 2 * hw + 0.4, DUCT_H + 0.3, bars=9)
    for j, z in enumerate((0.8, DUCT_H - 0.6)):
        cyl(f"Knuckle{j}", 0.07, 0.5, (-hw - 0.2, -0.07, z), K["iron"], verts=10, bevel=0.0)
    box("Hasp", (0.5, 0.04, 0.12), (hw + 0.35, -0.12, DUCT_H / 2), K["iron"], bevel=0.01)
    _xform(s, T(0, y0, -0.15))
    set_group("Main")
    for j, z in enumerate((0.8, DUCT_H - 0.6)):
        box(f"Pintle{j}", (0.3, 0.1, 0.16), (-hw - 0.45, y0 + 0.05, z - 0.15 - 0.33), K["iron"], bevel=0.01)
    hoop("Staple", (hw + 0.85, y0 - 0.05, DUCT_H / 2 - 0.15), 0.08, "Z", K["iron"], thick=0.02)
    # an open padlock hanging on the staple
    s = _mark()
    box("LockBody", (0.24, 0.1, 0.28), (0, 0, -0.2), K["brass"], bevel=0.03)
    rtube("LockShackle", [(-0.07, 0, -0.06), (-0.07, 0, 0.12), (0.0, 0, 0.18), (0.07, 0, 0.12)], 0.02, K["steel"], poly=False)
    _xform(s, T(hw + 0.85, y0 - 0.18, DUCT_H / 2 - 0.2) @ RZ(0.4))
    moss_tufts("Moss", [(-hw - 1.0, -0.98, 0.02), (hw + 0.9, -0.95, 0.02)], K, rnd, size=0.08)
    return _dims()


def vent_ceiling(M):
    """A ceiling vent you can climb up through, built as a duct module (snaps into the duct runs) whose floor opens onto the
    room below: a 5.6 x 5.6 hole, a plaster ceiling rose with a ring of acanthus beads round a cast-iron register (Grate0)
    hinged on its -Y edge that drops down. The room's ceiling surface goes 0.30 under the duct's origin."""
    K = kit(M)
    rnd = random.Random(5313)
    m, mi, iron = K["duct"], K["ductin"], K["iron"]
    y0h, y1h = -3.7, 1.9           # the hole along Y (5.6), leaving 2.1 of floor to stand on at the +Y end
    duct_box("D", K, -4, 4, skip=("F",))
    box("FloorA", (2 * DA, y0h + 4, DT), (0, (-4 + y0h) / 2, -DT / 2), mi, bevel=0.01)
    box("FloorB", (2 * DA, 4 - y1h, DT), (0, (y1h + 4) / 2, -DT / 2), mi, bevel=0.01)
    flange("FA", K, T(0, -4, 0))
    flange("FB", K, T(0, 4, 0) @ RZ(PI))
    # the collar through the ceiling (-0.10 .. -0.30) round the hole
    yc = (y0h + y1h) / 2
    for sx in (-1, 1):
        box(f"CollarX{sx}", (DT, y1h - y0h, 0.2), (sx * (DA - DT / 2), yc, -0.2), m, bevel=0.0)
    for k, y in enumerate((y0h + DT / 2, y1h - DT / 2)):
        box(f"CollarY{k}", (2 * DA - 2 * DT, DT, 0.2), (0, y, -0.2), m, bevel=0.0)
    # the plaster rose under the ceiling plane
    zc = -0.3
    pl = K["plaster"]
    lathe("Rose", [(4.0, 0.0), (4.6, 0.0), (4.62, -0.05), (4.5, -0.12), (4.25, -0.16), (4.05, -0.22), (3.98, -0.22), (3.98, 0.0)], pl, seg=72,
                 loc=(0, yc, zc))
    for i in range(36):
        a = i / 36 * 2 * PI
        sphere(f"Bead{i}", 0.08, (math.cos(a) * 4.35, yc + math.sin(a) * 4.35, zc - 0.16), pl, seg=8, rings=4)
    # a flat plaster bed between the hole and the rose ring
    bed_out = [(math.cos(i / 48 * 2 * PI) * 4.0, math.sin(i / 48 * 2 * PI) * 4.0) for i in range(48)]
    bm = bmesh.new()
    outer = [bm.verts.new((x, yc + y, zc - 0.04)) for x, y in bed_out]
    sq = []
    for i in range(48):
        a = i / 48 * 2 * PI
        c, s_ = math.cos(a), math.sin(a)
        k = DA / max(abs(c), abs(s_))
        sq.append(bm.verts.new((c * k, yc + s_ * k, zc - 0.04)))
    for i in range(48):
        j = (i + 1) % 48
        bm.faces.new((sq[i], sq[j], outer[j], outer[i]))
    for f in bm.faces:
        if f.normal.z > 0:
            f.normal_flip()
    bm_obj("Bed", bm, pl)
    # the register: hinged on its -Y edge, drops down (rotates about +X by -100: the free +Y edge swings down)
    hz = zc - 0.06
    opening("VentCeiling", "Grate0", "hatch", (0.0, yc - DA - 0.12, hz), angle=-100, axis=(1, 0, 0))
    G = 2 * DA + 0.24
    r = 0.06
    for sy in (-1, 1):
        sq_bar(f"GFrameY{sy}", [(-G / 2, yc + sy * (G / 2 - r), hz - r), (G / 2, yc + sy * (G / 2 - r), hz - r)], r, iron)
    for sx in (-1, 1):
        sq_bar(f"GFrameX{sx}", [(sx * (G / 2 - r), yc - G / 2 + 2 * r, hz - r), (sx * (G / 2 - r), yc + G / 2 - 2 * r, hz - r)], r, iron)
    for k, f in enumerate((0.33, 0.66)):
        h = G / 2 * f
        pts = [(-h, yc - h, hz - 0.05), (h, yc - h, hz - 0.05), (h, yc + h, hz - 0.05), (-h, yc + h, hz - 0.05), (-h, yc - h, hz - 0.05)]
        sq_bar(f"GSq{k}", pts, 0.035, iron)
    for k, (dx, dy) in enumerate(((1, 1), (1, -1))):
        sq_bar(f"GDiag{k}", [(-dx * (G / 2 - 0.12), yc - dy * (G / 2 - 0.12), hz - 0.05), (dx * (G / 2 - 0.12), yc + dy * (G / 2 - 0.12), hz - 0.05)], 0.035, iron)
    for k in range(2):
        a = [(0, yc - G / 2 + 0.1, hz - 0.05), (0, yc + G / 2 - 0.1, hz - 0.05)] if k == 0 else [(-G / 2 + 0.1, yc, hz - 0.05), (G / 2 - 0.1, yc, hz - 0.05)]
        sq_bar(f"GCross{k}", a, 0.035, iron)
    lathe("GBoss", [(0, 0), (0.3, 0), (0.32, -0.05), (0.18, -0.12), (0, -0.14)], K["brass"], seg=20, loc=(0, yc, hz - 0.03))
    for k, x in enumerate((-1.6, 1.6)):
        cyl(f"GKnuckle{k}", 0.05, 0.4, (x, yc - DA - 0.12, hz), iron, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
    hoop("GPull", (0, yc + G / 2 - 0.3, hz - 0.14), 0.09, "X", K["brass"], thick=0.015)
    set_group("Main")
    duct_dust("Dust", K, rnd, y1h, 4, n=2)
    JOINTS["VentCeiling"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0))]
    return _dims()


def vent_floor(M):
    """A floor vent you can drop into: a heavy cast-iron bar grating (Grate0, lift-off) in a limestone kerb flush with the
    floor (origin at floor level), over a brick-lined shaft 8 deep with iron rungs, opening at the bottom onto a duct joint at
    y = +4 (the lower duct's inside floor 8.0 below)."""
    K = kit(M)
    rnd = random.Random(5314)
    S = DA
    D = 8.0
    br, iron = K["brickdk"], K["iron"]
    # kerb round the opening, flush with the floor (top at z = 0)
    for k, (cx, cy, w, d) in enumerate(((0, -S - 0.35, 2 * S + 1.4, 0.7), (0, S + 0.35, 2 * S + 1.4, 0.7), (-S - 0.35, 0, 0.7, 2 * S), (S + 0.35, 0, 0.7, 2 * S))):
        box(f"Kerb{k}", (w, d, 0.4), (cx, cy, -0.2), K["lime"], bevel=0.04)
    # the grate's rebate: a ledge inside the kerb, 0.12 down
    for k, (cx, cy, w, d) in enumerate(((0, -S + 0.06, 2 * S, 0.12), (0, S - 0.06, 2 * S, 0.12), (-S + 0.06, 0, 0.12, 2 * S - 0.24), (S - 0.06, 0, 0.12, 2 * S - 0.24))):
        box(f"Ledge{k}", (w, d, 0.1), (cx, cy, -0.32), iron, bevel=0.01)
    # the brick shaft walls (inner faces at +-S), the -Y side down to the bottom, the +Y side open at the bottom (the duct)
    def wall(name, x0, x1, y, z0, z1, nrm):
        rows = [[(x0, y, z0), (x1, y, z0)], [(x0, y, z1), (x1, y, z1)]]
        uvs = [[(x0, z0), (x1, z0)], [(x0, z1), (x1, z1)]]
        return grid_surface(name, rows, br, uvs, target=lambda p, n=nrm: (p.x + n[0], p.y + n[1], p.z))
    wall("WallF", -S, S, -S, -D, -0.4, (0, 1))
    wall("WallB", -S, S, S, -D + DUCT_H + DT, -0.4, (0, -1))
    for sx in (-1, 1):
        rows = [[(sx * S, -S, -D), (sx * S, S, -D)], [(sx * S, -S, -0.4), (sx * S, S, -0.4)]]
        grid_surface(f"WallX{sx}", rows, br, [[(-S, -D), (S, -D)], [(-S, -0.4), (S, -0.4)]], target=lambda p, sx=sx: (p.x - sx, p.y, p.z))
    box("ShaftFloor", (2 * S, 2 * S, DT), (0, 0, -D - DT / 2), K["limedk"], bevel=0.01)
    # stub into the duct and its flange (into +Y)
    s = _mark()
    duct_box("Stub", K, S, 4.0, skip=("F",))
    box("StubFloor", (2 * S, 4 - S, DT), (0, (S + 4) / 2, -DT / 2), K["ductin"], bevel=0.01)
    _xform(s, T(0, 0, -D))
    flange("F", K, T(0, 4, -D) @ RZ(PI))
    # rungs on the -Y wall
    for i in range(9):
        z = -D + 0.9 + i * 0.8
        sq_bar(f"Rung{i}", [(-0.8, -S, z - 0.04), (-0.8, -S + 0.34, z), (0.8, -S + 0.34, z), (0.8, -S, z - 0.04)], 0.035, iron)
    # outer shell of the shaft (tiled castle stone)
    set_group("Wall")
    for sx in (-1, 1):
        box(f"ShellX{sx}", (0.3, 2 * S + 1.4, D - 0.4), (sx * (S + 0.55), 0, -0.4 - (D - 0.4) / 2), K["stone"], bevel=0.0)
    box("ShellF", (2 * S + 0.8, 0.3, D - 0.4), (0, -S - 0.55, -0.4 - (D - 0.4) / 2), K["stone"], bevel=0.0)
    box("ShellB", (2 * S + 0.8, 0.3, D - 0.4 - DUCT_H - 0.4), (0, S + 0.55, -0.4 - (D - 0.4 - DUCT_H - 0.4) / 2), K["stone"], bevel=0.0)
    # the grating: lift-off, its origin at its centre on the ledge
    opening("VentFloor", "Grate0", "lift", (0.0, 0.0, -0.27), slide=(0.0, -6.4, 0.27))
    G = 2 * S - 0.04
    for sx in (-1, 1):
        box(f"GFrX{sx}", (0.16, G, 0.24), (sx * (G / 2 - 0.08), 0, -0.15), iron, bevel=0.02)
    for sy in (-1, 1):
        box(f"GFrY{sy}", (G - 0.32, 0.16, 0.24), (0, sy * (G / 2 - 0.08), -0.15), iron, bevel=0.02)
    for i in range(13):
        x = -G / 2 + 0.16 + (G - 0.32) * (i + 0.5) / 13
        box(f"GBar{i}", (0.09, G - 0.32, 0.22), (x, 0, -0.15), iron, bevel=0.012)
    for j in (-1, 1):
        box(f"GTie{j}", (G - 0.32, 0.08, 0.08), (0, j * 1.2, -0.23), iron, bevel=0.01)
    set_group("Main")
    moss_tufts("Moss", [(-S - 0.6, -S - 0.55, 0.0), (S + 0.6, S + 0.5, 0.0)], K, rnd, size=0.08)
    JOINTS["VentFloor"] = [("A", (0, 4, -D), (0, -1, 0))]
    return _dims()


# ------------------------------------------------------------------ tunnels (brick barrel vault, limestone ribs)

def strip_between(name, A, B, mat, normal_target=None):
    """Quads between two point lists of the same length (a flat annulus or a rib's side)."""
    rows = [A, B]
    uvs = [[(p[0] + p[1], p[2]) for p in A], [(p[0] + p[1], p[2]) for p in B]]
    return grid_surface(name, rows, mat, uvs, target=normal_target)


def end_ring2(name, mtx, mat, z_open=TBOT, bottom=TBOT, top=TTOP, hw=TW, n=10):
    """The flush end of a tunnel shell (the rectangle less the vault opening down to z_open), in the plane local y = 0 of mtx,
    facing local -Y."""
    polys = []
    for sgn in (1, -1):
        pts = [(sgn * TA, z_open), (sgn * hw, bottom), (sgn * hw, top), (0.0, top), (0.0, TS + TA)]
        for j in range(1, n):
            th = PI / 2 * (1 - j / n)
            pts.append((sgn * TA * math.cos(th), TS + TA * math.sin(th)))
        pts.append((sgn * TA, TS))
        polys.append([mtx @ Vector((x, 0, z)) for x, z in pts])
    return poly_face(name, polys, mat, mtx.to_3x3() @ Vector((0, -1, 0)))


def tunnel_ribs(prefix, K, frames_in, frames_out, centre_fn, z0=0.0):
    """Half-ribs of dressed limestone at both ends (0.25 along the run, 0.1 proud of the brick), so two modules make one rib.
    Each frame list runs from the joint plane into the piece."""
    rp = vault_prof(TA - 0.1, TS, z0=z0)
    vp = vault_prof(TA, TS, z0=z0)
    for k, fr in enumerate((frames_in, frames_out)):
        sweep(f"{prefix}{k}", rp, fr, K["lime"], target=centre_fn)
        o0, s0, u0, _ = fr[0]
        o1, s1, u1, _ = fr[-1]
        A = [o1 + s1 * x + u1 * z for x, z in vp]
        B = [o1 + s1 * x + u1 * z for x, z in rp]
        strip_between(f"{prefix}{k}Side", A, B, K["lime"], normal_target=lambda p, d=(o1 - o0): p + d)
        A0 = [o0 + s0 * x + u0 * z for x, z in vp]
        B0 = [o0 + s0 * x + u0 * z for x, z in rp]
        strip_between(f"{prefix}{k}End", A0, B0, K["lime"], normal_target=lambda p, d=(o1 - o0): p - d)


def tunnel_floor(name, K, frames, centre=None):
    """The walking floor slab (tiled: Floor), z -0.4 .. 0, between the walls, swept with the run, closed at both ends."""
    prof = [(TA, 0.0), (-TA, 0.0), (-TA, TBOT), (TA, TBOT)]
    ob = sweep(name, prof, frames, K["stone"], closed=True, away=centre)
    mid = frames[len(frames) // 2][0]
    for k, fr in enumerate((frames[0], frames[-1])):
        o, s, u, t = fr
        poly_face(f"{name}End{k}", [[o + s * x + u * z for x, z in prof]], K["stone"], o - mid)
    return ob


def lantern(prefix, K, x, y, z, side=1):
    """An iron cage lantern on a wall bracket (wall at x, the bracket out along -side * X), a candle inside (Glow flame)."""
    iron = K["iron"]
    box(f"{prefix}Plate", (0.06, 0.4, 0.7), (x - side * 0.03, y, z), iron, bevel=0.015)
    xo = x - side * 0.75
    rtube(f"{prefix}Arm", [(x - side * 0.05, y, z + 0.1), (x - side * 0.4, y, z + 0.16), (xo, y, z + 0.1)], 0.035, iron, poly=False)
    rtube(f"{prefix}Brace", [(x - side * 0.05, y, z - 0.25), (x - side * 0.45, y, z + 0.1)], 0.025, iron)
    cz = z - 0.95
    box(f"{prefix}Base", (0.36, 0.36, 0.06), (xo, y, cz), iron, bevel=0.01)
    lathe(f"{prefix}Roof", [(0, 0), (0.26, 0), (0.12, 0.18), (0.03, 0.3), (0, 0.32)], iron, seg=4, loc=(xo, y, cz + 0.6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            sq_bar(f"{prefix}Post{sx}{sy}", [(xo + sx * 0.16, y + sy * 0.16, cz + 0.03), (xo + sx * 0.16, y + sy * 0.16, cz + 0.6)], 0.018, iron)
    rtube(f"{prefix}Hang", [(xo, y, cz + 0.9), (xo, y, cz + 1.06)], 0.014, iron)
    lathe(f"{prefix}Candle", [(0, 0), (0.05, 0), (0.05, 0.22), (0.035, 0.24), (0, 0.24)], K["wax"], seg=10, loc=(xo, y, cz + 0.03))
    set_group("Glow")
    flame(f"{prefix}Flame", (xo, y, cz + 0.27), h=0.12)
    set_group("Main")


def tunnel_straight(M):
    """An 8-stud brick barrel-vault tunnel (6.4 wide, 7.8 to the crown), dressed limestone half-ribs at both ends that make one
    rib with the next module, an iron cage lantern on the left wall (Glow), an iron ring staple, a fallen brick and a puddle;
    the shell tiled castle stone outside (Wall), the floor tiled flags (Floor)."""
    K = kit(M)
    centre = lambda p: (0, p.y, TS)
    sweep("Vault", vault_prof(), frames_line((0, -3.75, 0), (0, 3.75, 0), 15), K["brick"], target=centre)
    tunnel_ribs("Rib", K, frames_line((0, -4, 0), (0, -3.75, 0), 1), frames_line((0, 4, 0), (0, 3.75, 0), 1), centre)
    lantern("Lamp", K, -TA, 0.0, 4.4, side=-1)
    hoop("Staple", (TA - 0.18, -1.8, 3.4), 0.16, "X", K["iron"], thick=0.025)
    cyl("StapleRose", 0.1, 0.06, (TA - 0.03, -1.8, 3.56), K["iron"], rot=(0, PI / 2, 0), verts=10, bevel=0.0)
    box("FallenBrick", (0.5, 0.24, 0.22), (1.4, 1.6, 0.11), K["brickdk"], bevel=0.03, rot=(0, 0, 0.6))
    cyl("Puddle", 1.0, 0.01, (-0.9, -1.2, 0.005), K["water"], verts=24, bevel=0.0).scale = (1.0, 1.7, 1.0)
    set_group("Floor")
    tunnel_floor("Floor", K, frames_line((0, -4, 0), (0, 4, 0), 2), centre=lambda p: (0, 0, -0.2))
    set_group("Wall")
    sweep("Shell", [(-TW, TBOT), (-TW, TTOP), (TW, TTOP), (TW, TBOT)], frames_line((0, -4, 0), (0, 4, 0), 4), K["stone"],
          away=lambda p: (0, p.y, 3.0))
    end_ring2("EndA", T(0, -4, 0), K["stone"])
    end_ring2("EndB", T(0, 4, 0) @ RZ(PI), K["stone"])
    set_group("Main")
    JOINTS["TunnelStraight"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0))]
    return _dims()


def tunnel_curve(M):
    """A quarter-turn of the vault on a 12-stud centreline radius, filling a 2 x 2 block of cells: in at (-4, -8) heading +Y,
    out at (8, 4) heading +X (origin at the block's centre, so both ends sit on the 8-grid). A limestone corbel with three
    guttered candles on the outer wall (Glow)."""
    K = kit(M)
    c = (8.0, -8.0)
    R = 12.0
    da = 0.25 / R

    def ctr(p):
        v = Vector((p.x - c[0], p.y - c[1])).normalized() * R
        return (c[0] + v.x, c[1] + v.y, TS)
    sweep("Vault", vault_prof(), frames_arc(c, R, PI - da, PI / 2 + da, 22), K["brick"], curv=1 / R, target=ctr)
    tunnel_ribs("Rib", K, frames_arc(c, R, PI, PI - da, 1), frames_arc(c, R, PI / 2, PI / 2 + da, 1), ctr)
    # the candle corbel on the outer wall at mid-bend (the outer wall is at radius R + TA)
    am = 3 * PI / 4
    ow = Vector((c[0] + (R + TA) * math.cos(am), c[1] + (R + TA) * math.sin(am), 0))
    yaw = math.atan2(-math.cos(am), math.sin(am))      # local -Y -> the inward direction
    s = _mark()
    prism("Corbel", [(0.0, 3.2), (0.0, 2.5), (-0.25, 2.55), (-0.55, 2.85), (-0.62, 3.2)], 0.0, 1.3, K["lime"], plane="YZ", bevel=0.02)
    cs = ((-0.4, 0.42), (0.0, 0.6), (0.4, 0.3))
    for j, (dx, h) in enumerate(cs):
        lathe(f"Candle{j}", [(0, 0), (0.07, 0), (0.075, h * 0.6), (0.065, h), (0, h)], K["wax"], seg=12, loc=(dx, -0.34, 3.2))
        lathe(f"Drip{j}", [(0, 0), (0.13, 0), (0.1, 0.03), (0, 0.04)], K["wax"], seg=12, loc=(dx, -0.34, 3.2))
    set_group("Glow")
    for j, (dx, h) in enumerate(cs):
        flame(f"Flame{j}", (dx, -0.34, 3.2 + h + 0.02), h=0.1)
    set_group("Main")
    _xform(s, Matrix.Translation(ow) @ RZ(yaw))
    set_group("Floor")
    tunnel_floor("Floor", K, frames_arc(c, R, PI, PI / 2, 12), centre=lambda p: (ctr(p)[0], ctr(p)[1], -0.2))
    set_group("Wall")
    sweep("Shell", [(-TW, TBOT), (-TW, TTOP), (TW, TTOP), (TW, TBOT)], frames_arc(c, R, PI, PI / 2, 24), K["stone"],
          away=lambda p: (ctr(p)[0], ctr(p)[1], 3.0))
    end_ring2("EndA", T(-4, -8, 0), K["stone"])
    end_ring2("EndB", T(8, 4, 0) @ RZ(PI / 2), K["stone"])
    set_group("Main")
    JOINTS["TunnelCurve"] = [("A", (-4, -8, 0), (0, 1, 0)), ("B", (8, 4, 0), (-1, 0, 0))]
    return _dims()


def chalk(prefix, K, strokes, mtx, r=0.022):
    """Chalk strokes [(x, z)] on a plane facing local -Y, placed by mtx."""
    s = _mark()
    for i, st in enumerate(strokes):
        rtube(f"{prefix}{i}", [(x, 0.0, z) for x, z in st], r, K["chalkm"])
    _xform(s, mtx)


def tunnel_junction(M):
    """A T-junction: the run along Y and a branch to x = +4, the two barrel vaults meeting in true groins (their edges on the
    diagonals), a carved limestone boss where the groins cross, half-ribs on all three ends, chalked arrows and an invented
    sign on the wall."""
    K = kit(M)
    r, hs = TA, TS
    br = K["brick"]
    ts = [-3.75] + [round(-3.6 + 0.4 * i, 4) for i in range(19)] + [3.75]
    m = 12
    rows, uvs = [], []
    for y in ts:
        rows.append([(r * math.cos(PI / 2 + PI / 2 * j / m), y, hs + r * math.sin(PI / 2 + PI / 2 * j / m)) for j in range(m + 1)])
        uvs.append([(y, hs + r * PI / 2 + r * PI / 2 * j / m) for j in range(m + 1)])
    grid_surface("VaultL", rows, br, uvs, target=lambda p: (0, p.y, hs))
    rows, uvs = [], []
    for y in ts:
        th0 = math.acos(min(abs(y), r) / r)
        ths = [th0 + (PI / 2 - th0) * j / m for j in range(m + 1)]
        rows.append([(r * math.cos(th), y, hs + r * math.sin(th)) for th in ths])
        uvs.append([(y, hs + r * th) for th in ths])
    grid_surface("VaultR", rows, br, uvs, target=lambda p: (0, p.y, hs))
    rows, uvs = [], []
    for x in [t for t in ts if t >= 0]:
        ph0 = math.acos(min(x, r) / r)
        phs = [ph0 + (PI - 2 * ph0) * j / (2 * m) for j in range(2 * m + 1)]
        rows.append([(x, r * math.cos(ph), hs + r * math.sin(ph)) for ph in phs])
        uvs.append([(x, hs + r * ph) for ph in phs])
    grid_surface("VaultB", rows, br, uvs, target=lambda p: (p.x, 0, hs))

    def wall(name, pts, tgt):
        rows_ = [[(p[0], p[1], 0.0) for p in pts], [(p[0], p[1], hs) for p in pts]]
        uvs_ = [[(p[0] + p[1], 0.0) for p in pts], [(p[0] + p[1], hs) for p in pts]]
        return grid_surface(name, rows_, br, uvs_, target=tgt)
    wall("WallL", [(-r, -3.75), (-r, 3.75)], lambda p: (0, p.y, p.z))
    for sy in (-1, 1):
        wall(f"WallR{sy}", [(r, sy * 3.75), (r, sy * r)], lambda p: (0, p.y, p.z))
        wall(f"WallB{sy}", [(r, sy * r), (3.75, sy * r)], lambda p: (p.x, 0, p.z))
    tunnel_ribs("RibA", K, frames_line((0, -4, 0), (0, -3.75, 0), 1), frames_line((0, 4, 0), (0, 3.75, 0), 1), lambda p: (0, p.y, hs))
    fc = frames_line((4, 0, 0), (3.75, 0, 0), 1)
    rp, vp = vault_prof(TA - 0.1, TS), vault_prof(TA, TS)
    sweep("RibC", rp, fc, K["lime"], target=lambda p: (p.x, 0, hs))
    for k, fr in enumerate((fc[0], fc[-1])):
        o, s_, u_, _ = fr
        strip_between(f"RibC{k}", [o + s_ * x + u_ * z for x, z in vp], [o + s_ * x + u_ * z for x, z in rp], K["lime"],
                      normal_target=lambda p, k=k: p + Vector((1 if k == 0 else -1, 0, 0)))
    lathe("Boss", [(0, 0), (0.42, 0), (0.45, -0.08), (0.3, -0.2), (0.12, -0.3), (0, -0.32)], K["lime"], seg=20, loc=(0, 0, hs + r + 0.01))
    foil("BossFoil", 0, 0, hs + r - 0.33, 0.16, K["limedk"], lobes=4, thick=0.03)
    chalk("Arrow", K, [[(-0.9, 3.0), (0.9, 3.0)], [(0.5, 3.35), (0.9, 3.0), (0.5, 2.65)]], T(-r + 0.03, 1.2, 0) @ RZ(-PI / 2))
    chalk("Mark", K, [[(-0.4, 4.0), (0.0, 3.4), (0.4, 4.0)], [(-0.3, 3.6), (0.3, 3.6)], [(-0.45, 3.2), (0.45, 3.2)]], T(-r + 0.03, -1.4, 0) @ RZ(-PI / 2))
    set_group("Floor")
    box("Floor", (2 * r, 8, 0.4), (0, 0, -0.2), K["stone"], bevel=0.0)
    box("FloorB", (4 - r, 2 * r, 0.4), (r + (4 - r) / 2, 0, -0.2), K["stone"], bevel=0.0)
    set_group("Wall")
    poly_face("ShellTop", [[(-TW, -4, TTOP), (TW, -4, TTOP), (TW, 4, TTOP), (-TW, 4, TTOP)]], K["stone"], (0, 0, 1))
    poly_face("ShellL", [[(-TW, -4, TBOT), (-TW, 4, TBOT), (-TW, 4, TTOP), (-TW, -4, TTOP)]], K["stone"], (-1, 0, 0))
    end_ring2("EndA", T(0, -4, 0), K["stone"])
    end_ring2("EndB", T(0, 4, 0) @ RZ(PI), K["stone"])
    end_ring2("EndC", T(4, 0, 0) @ RZ(PI / 2), K["stone"])
    set_group("Main")
    JOINTS["TunnelJunction"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, 0), (0, -1, 0)), ("C", (4, 0, 0), (-1, 0, 0))]
    return _dims()


def tunnel_steps(M):
    """Steps down a half-storey (4) in one module: a level threshold flush with the module behind, eight limestone steps,
    the vault raking down with them, an iron handrail on brackets; the far end is on the grid 4 lower."""
    K = kit(M)
    n = 8
    y0 = -3.5
    run = (4 - y0) / n
    zf = lambda y: -0.5 * (y + 4)

    def fr(y, t=None):
        return (Vector((0, y, zf(y))), Vector((1, 0, 0)), Vector((0, 0, 1)), (y + 4) if t is None else t)
    centre = lambda p: (0, p.y, zf(p.y) + TS)
    ys = [-3.75] + [-3.5 + 0.5 * i for i in range(15)] + [3.75]
    sweep("Vault", vault_prof(z0=-1.2), [fr(y) for y in ys], K["brick"], target=centre)
    tunnel_ribs("Rib", K, [fr(-4), fr(-3.75)], [fr(4), fr(3.75)], centre, z0=-0.6)
    # the rib feet go down to the steps as well
    box("Threshold", (2 * TA, 4 + y0, 0.4), (0, (-4 + y0) / 2, -0.2), K["lime"], bevel=0.02)
    for k in range(n):
        top = -0.5 * (k + 1)
        ya = y0 + k * run
        box(f"Step{k}", (2 * TA, run, 1.0), (0, ya + run / 2, top - 0.5), K["lime"], bevel=0.03)
    xr = -TA + 0.28
    pts = []
    for i in range(5):
        y = -3.4 + i * 1.7
        z = zf(y) + 3.0
        pts.append((xr, y, z))
        rtube(f"Bracket{i}", [(-TA, y, z - 0.25), (xr - 0.1, y, z - 0.2), (xr, y, z - 0.05)], 0.03, K["iron"])
    rtube("Rail", pts, 0.05, K["iron"])
    set_group("Wall")
    sweep("Shell", [(-TW, -1.6), (-TW, TTOP), (TW, TTOP), (TW, -1.6)], [fr(-4 + i) for i in range(9)], K["stone"],
          away=lambda p: (0, p.y, zf(p.y) + 3.0))
    end_ring2("EndA", T(0, -4, 0), K["stone"], bottom=-1.6)
    end_ring2("EndB", T(0, 4, -4) @ RZ(PI), K["stone"], bottom=-1.6 + 0.0, z_open=-1.0)
    set_group("Main")
    JOINTS["TunnelSteps"] = [("A", (0, -4, 0), (0, 1, 0)), ("B", (0, 4, -4), (0, -1, 0))]
    return _dims()


def tunnel_dead_end(M):
    """A tunnel ending in a brick wall with an iron grate at floor level (Grate0, hinged on the left, 5.6 x 6.0 clear: a
    DuctStraight bolts on behind at y = +4), a limestone frame round it, a cast-iron floor drain, a chain and an open padlock."""
    K = kit(M)
    yE = 3.4
    centre = lambda p: (0, p.y, TS)
    sweep("Vault", vault_prof(), frames_line((0, -3.75, 0), (0, yE, 0), 14), K["brick"], target=centre)
    rp, vp = vault_prof(TA - 0.1, TS), vault_prof(TA, TS)
    sweep("RibA", rp, frames_line((0, -4, 0), (0, -3.75, 0), 1), K["lime"], target=centre)
    for k, (yy, d) in enumerate(((-3.75, 1), (-4.0, -1))):
        o = Vector((0, yy, 0))
        strip_between(f"RibA{k}", [o + Vector((x, 0, z)) for x, z in vp], [o + Vector((x, 0, z)) for x, z in rp], K["lime"],
                      normal_target=lambda p, d=d: p + Vector((0, d, 0)))
    hw = DA
    outline = [(-TA, 0.0), (-hw - 0.5, 0.0), (-hw - 0.5, DUCT_H + 0.6), (hw + 0.5, DUCT_H + 0.6), (hw + 0.5, 0.0), (TA, 0.0), (TA, TS)]
    for i in range(1, 20):
        th = PI * i / 20
        outline.append((TA * math.cos(th), TS + TA * math.sin(th)))
    outline.append((-TA, TS))
    poly_face("EndWall", [[(x, yE, z) for x, z in outline]], K["brick"], (0, -1, 0), uvfn=lambda co: (co.x, co.z))
    st = K["lime"]
    for sx in (-1, 1):
        box(f"Jamb{sx}", (0.5, 4 - yE, DUCT_H + 0.6), (sx * (hw + 0.25), yE + (4 - yE) / 2, (DUCT_H + 0.6) / 2), st, bevel=0.03)
    box("Lintel", (2 * hw, 4 - yE, 0.6), (0, yE + (4 - yE) / 2, DUCT_H + 0.3), st, bevel=0.03)
    box("Sill", (2 * hw, 4 - yE, 0.1), (0, yE + (4 - yE) / 2, -0.05), st, bevel=0.01)
    box("DrainFrame", (1.1, 1.1, 0.04), (0, 1.6, 0.02), K["iron"], bevel=0.01)
    for i in range(6):
        box(f"DrainBar{i}", (0.08, 0.9, 0.05), (-0.4 + i * 0.16, 1.6, 0.025), K["iron"], bevel=0.005)
    cyl("Puddle", 1.0, 0.01, (0.6, 0.6, 0.005), K["water"], verts=24, bevel=0.0).scale = (1.5, 1.0, 1.0)
    # the grate: square bars, riveted flats, hinged on the left, swings toward the tunnel (-Y)
    y0 = yE - 0.12
    opening("TunnelDeadEnd", "Grate0", "swing", (-hw, y0, 0.05), angle=-100)
    s = _mark()
    G = 2 * hw
    for sx in (-1, 1):
        sq_bar(f"GStile{sx}", [(sx * (G / 2 - 0.07), 0, 0.05), (sx * (G / 2 - 0.07), 0, DUCT_H - 0.02)], 0.07, K["iron"])
    for k, z in enumerate((0.25, DUCT_H / 2, DUCT_H - 0.2)):
        box(f"GFlat{k}", (G - 0.28, 0.09, 0.2), (0, 0, z), K["iron"], bevel=0.01)
        rivet_row(f"GRv{k}", (-G / 2 + 0.4, -0.05, z), (G / 2 - 0.4, -0.05, z), 10, (0, -1, 0), K["iron"], r=0.03)
    for i in range(10):
        x = -G / 2 + G * (i + 1) / 11
        sq_bar(f"GBar{i}", [(x, 0, 0.05), (x, 0, DUCT_H - 0.02)], 0.045, K["iron"])
    box("GHasp", (0.4, 0.05, 0.12), (G / 2 + 0.1, -0.06, DUCT_H / 2 + 0.4), K["iron"], bevel=0.01)
    _xform(s, T(0, y0, 0))
    set_group("Main")
    for j, z in enumerate((0.8, DUCT_H - 0.8)):
        box(f"Pintle{j}", (0.2, 0.2, 0.2), (-hw - 0.1, y0 - 0.06, z - 0.22), K["iron"], bevel=0.01)
    B43.chain("Chain", [(hw + 0.6, yE - 0.12, 3.4), (hw + 0.62, yE - 0.3, 1.8), (hw + 0.7, yE - 0.4, 0.08), (hw + 1.4, yE - 0.6, 0.08)], K["iron"],
              r=0.06, thick=0.014)
    hoop("ChainStaple", (hw + 0.6, yE - 0.05, 3.5), 0.08, "X", K["iron"], thick=0.018)
    box("Lock", (0.26, 0.12, 0.3), (hw + 1.6, yE - 0.62, 0.15), K["brass"], bevel=0.03, rot=(0, 0, 0.5))
    set_group("Floor")
    tunnel_floor("Floor", K, frames_line((0, -4, 0), (0, yE, 0), 2), centre=lambda p: (0, -0.3, -0.2))
    set_group("Wall")
    sweep("Shell", [(-TW, TBOT), (-TW, TTOP), (TW, TTOP), (TW, TBOT)], frames_line((0, -4, 0), (0, 4, 0), 4), K["stone"], away=lambda p: (0, p.y, 3.0))
    end_ring2("EndA", T(0, -4, 0), K["stone"])
    back = [(-TW, TBOT), (-hw, TBOT), (-hw, 0.0), (-hw, DUCT_H), (hw, DUCT_H), (hw, 0.0), (hw, TBOT), (TW, TBOT), (TW, TTOP), (-TW, TTOP)]
    poly_face("Back", [[(x, 4.0, z) for x, z in back]], K["stone"], (0, 1, 0))
    set_group("Main")
    JOINTS["TunnelDeadEnd"] = [("A", (0, -4, 0), (0, 1, 0))]
    return _dims()


# ------------------------------------------------------------------ hidden doors

def books_row(prefix, K, rnd, x0, x1, y_front, d, z, top, leathers, gilt, skip=None):
    """A row of leather-bound books standing on a shelf at z, spines on y_front (facing -Y), up to `top`."""
    x = x0
    k = 0
    while x < x1 - 0.12:
        w = rnd.uniform(0.09, 0.17)
        if x + w > x1:
            break
        h = min(top - z - 0.06, rnd.uniform(0.75, 1.15))
        lean = 0.0 if rnd.random() > 0.1 or x + w + 0.12 > x1 else rnd.uniform(0.08, 0.2)
        if skip and skip[0] <= x <= skip[1]:
            x = skip[1] + 0.01
            continue
        dd = rnd.uniform(d * 0.82, d)
        box(f"{prefix}{k}", (w, dd, h), (x + w / 2, y_front + dd / 2, z + h / 2), leathers[rnd.randrange(len(leathers))], bevel=0.008, segments=1,
            rot=(0, lean, 0))
        if rnd.random() < 0.5:
            box(f"{prefix}{k}Band", (w + 0.004, 0.01, 0.025), (x + w / 2, y_front - 0.003, z + h * 0.82), gilt, bevel=0.0, segments=1, rot=(0, lean, 0))
        x += w + (0.05 if lean else 0.006)
        k += 1


def bookcase_secret_door(M):
    """A hidden door in the library wall: a black cast-iron gothic press of leather books in a pointed limestone frame with
    crocketed pinnacles; the whole press (Door0) swings out on a hidden pivot at its right front edge when the crimson book
    on the third shelf is tipped. A gilt raven bookend; behind, a riveted iron back with a pull ring. Wall 1.0 thick."""
    K = kit(M)
    rnd = random.Random(5331)
    st, sd, iron, gl = K["lime"], K["limedk"], K["iron"], K["gilt"]
    HW, ZD = 2.0, 7.8           # opening half width, height
    WY = 0.5                    # half the wall thickness
    # the frame through the wall: jambs, a head with a pointed arch panel and pinnacles
    for sx in (-1, 1):
        box(f"Jamb{sx}", (0.7, 2 * WY + 0.2, ZD + 0.6), (sx * (HW + 0.35), 0.0, (ZD + 0.6) / 2), st, bevel=0.04)
        box(f"Plinth{sx}", (0.86, 2 * WY + 0.36, 0.5), (sx * (HW + 0.35), 0.0, 0.25), sd, bevel=0.04)
        lathe(f"Pinnacle{sx}", [(0, 0), (0.3, 0), (0.3, 0.1), (0.22, 0.14), (0.22, 0.7), (0.26, 0.76), (0.14, 1.1), (0.05, 1.5), (0, 1.62)], st, seg=4,
              loc=(sx * (HW + 0.35), -WY - 0.1, ZD + 0.6))
    box("Head", (2 * HW, 2 * WY + 0.2, 0.6), (0, 0.0, ZD + 0.3), st, bevel=0.04)
    arch = B43.arch_xz(-HW - 0.7, HW + 0.7, ZD + 0.6, 2.5, n=14)
    prism("Gable", arch, -WY - 0.02, 0.2, st)
    foil("GableFoil", 0, -WY - 0.14, ZD + 1.5, 0.45, sd, lobes=3, thick=0.04)
    rtube("GableMould", [(x, -WY - 0.14, z + 0.06) for x, z in B43.arch_xz(-HW - 0.75, HW + 0.75, ZD + 0.56, 2.62, n=16)], 0.06, st)
    # the leaf: a cast-iron press 0.9 deep, its front 0.1 proud of the wall face, pivoting at its right front edge
    D = 0.9
    yf = -WY - 0.1
    xh = HW - 0.02
    opening("BookcaseSecretDoor", "Door0", "swing", (xh, yf, 0.02), angle=80)
    W, H = 2 * HW - 0.04, ZD - 0.04
    x0, x1 = -HW + 0.02, HW - 0.02
    for sx in (-1, 1):
        box(f"Side{sx}", (0.14, D, H), (sx * (W / 2 - 0.07), yf + D / 2, 0.02 + H / 2), iron, bevel=0.015)
        for i in range(7):
            sphere(f"SideStud{sx}{i}", 0.035, (sx * (W / 2 - 0.07), yf - 0.005, 0.5 + i * 1.1), K["brass"], seg=8, rings=4, scale=(1, 0.6, 1))
    box("Plinth", (W, D, 0.32), (0, yf + D / 2, 0.18), iron, bevel=0.015)
    box("Cornice", (W + 0.08, D + 0.06, 0.18), (0, yf + D / 2 - 0.03, 0.02 + H - 0.09), iron, bevel=0.03)
    for i in range(6):
        x = x0 + 0.3 + i * (W - 0.6) / 5
        prism(f"Crest{i}", [(x - 0.2, H + 0.02), (x + 0.2, H + 0.02), (x + 0.12, H + 0.14), (x, H + 0.32), (x - 0.12, H + 0.14)], yf + D / 2, 0.06, iron)
    box("Back", (W - 0.28, 0.08, H - 0.5), (0, yf + D - 0.04, 0.02 + H / 2), iron, bevel=0.01)
    leathers = [B24.leather(f"SecretLeather{i}", c) for i, c in
                enumerate(((0.2, 0.03, 0.04), (0.05, 0.06, 0.16), (0.04, 0.08, 0.05), (0.3, 0.2, 0.09), (0.09, 0.05, 0.03), (0.46, 0.4, 0.3)))]
    shelves = [0.34, 1.82, 3.3, 4.78, 6.26]
    for j, z in enumerate(shelves):
        box(f"Shelf{j}", (W - 0.28, D - 0.1, 0.08), (0, yf + D / 2 + 0.01, z + 0.04), iron, bevel=0.01)
        rtube(f"Rail{j}", [(x0 + 0.16, yf + 0.03, z + 0.2), (x1 - 0.16, yf + 0.03, z + 0.2)], 0.018, K["brass"])
        top = (shelves[j + 1] if j + 1 < len(shelves) else H - 0.16)
        skip = (-0.95, -0.15) if j == 2 else ((0.7, 1.4) if j == 3 else None)
        books_row(f"Book{j}_", K, rnd, x0 + 0.16, x1 - 0.16, yf + 0.06, D - 0.2, z + 0.08, top, leathers, gl, skip=skip)
    # the trigger: a crimson book tipped forward on the third shelf, a gilt raven on its spine
    z = shelves[2] + 0.08
    box("TriggerBook", (0.2, 0.62, 1.05), (-0.55, yf + 0.36, z + 0.5), K["leather"], bevel=0.012, rot=(-0.32, 0, 0))
    box("TriggerBand", (0.205, 0.01, 0.04), (-0.55, yf + 0.04, z + 0.85), gl, bevel=0.0, rot=(-0.32, 0, 0))
    for k, dx in enumerate((-0.82, -0.28)):
        box(f"Prop{k}", (0.15, 0.6, 0.95), (dx + (-0.03 if k == 0 else 0.03), yf + 0.38, z + 0.475), leathers[k], bevel=0.008, segments=1)
    # the raven bookend on the fourth shelf
    from nh_props_batch9 import raven
    raven("Raven", (1.05, yf + 0.4, shelves[3] + 0.08), -PI / 2, 2.2, gl, K["iron"])
    # the secret side: rivetted plate, braces and a pull ring
    yb = yf + D
    for k, (a, b) in enumerate((((x0 + 0.3, 0.6), (x1 - 0.3, H - 0.6)), ((x0 + 0.3, H - 0.6), (x1 - 0.3, 0.6)))):
        sq_bar(f"Brace{k}", [(a[0], yb + 0.05, a[1]), (b[0], yb + 0.05, b[1])], 0.04, iron)
    rivet_row("BackRv", (x0 + 0.25, yb + 0.005, 0.5), (x0 + 0.25, yb + 0.005, H - 0.5), 9, (0, 1, 0), iron)
    rivet_row("BackRv2", (x1 - 0.25, yb + 0.005, 0.5), (x1 - 0.25, yb + 0.005, H - 0.5), 9, (0, 1, 0), iron)
    hoop("PullRing", (x0 + 0.5, yb + 0.12, 3.6), 0.15, "Y", iron, thick=0.022)
    cyl("PullRose", 0.08, 0.06, (x0 + 0.5, yb + 0.03, 3.75), iron, rot=(PI / 2, 0, 0), verts=12, bevel=0.0)
    cyl("Pivot", 0.06, 0.12, (xh - 0.1, yf + 0.1, H + 0.08), iron, verts=10, bevel=0.0)
    set_group("Main")
    return _dims()


def fireplace_passage(M):
    """A walk-in hearth whose cast-iron fireback (Slide0) sinks into a slot under the hearth, opening a crawl way
    (5.6 x 6.0) through the back of the firebox to a duct flange at y = +3.4. A cold hearth: clustered limestone jambs, a
    four-centred arch with a frieze of quatrefoils and a shield, a deep mantel shelf, sooty brick, firedogs, raked ash."""
    K = kit(M)
    rnd = random.Random(5332)
    st, sd, iron = K["lime"], K["limedk"], K["iron"]
    HX, ZS, ZA = 3.7, 6.2, 7.0        # mouth half width, arch springing, arch apex
    yF = -1.4                         # the chimneypiece's front
    yB = 2.0                          # the firebox back (the fireback's face)
    # jambs: a pier each side with three colonnettes on a plinth, capitals
    for sx in (-1, 1):
        xc = sx * (HX + 0.75)
        box(f"Pier{sx}", (1.5, -yF + 0.2, ZA + 0.6), (xc, (yF - 0.2) / 2 + 0.1, (ZA + 0.6) / 2), st, bevel=0.04)
        box(f"Base{sx}", (1.7, -yF + 0.4, 0.6), (xc, (yF - 0.4) / 2 + 0.1, 0.3), sd, bevel=0.04)
        for k, dx in enumerate((-0.42, 0.0, 0.42)):
            cyl(f"Col{sx}{k}", 0.17, ZS - 0.9, (xc + dx, yF - 0.1, 0.6 + (ZS - 0.9) / 2), st, verts=16, bevel=0.01)
            lathe(f"Cap{sx}{k}", [(0, 0), (0.18, 0), (0.24, 0.12), (0.3, 0.26), (0.3, 0.3), (0, 0.3)], st, seg=16, loc=(xc + dx, yF - 0.1, ZS - 0.3))
    # the lintel with the four-centred arch cut out of it (front face polygon, extruded)
    arch = []
    for i in range(17):
        t = i / 16
        x = -HX + 2 * HX * t
        k = 1 - abs(t - 0.5) * 2
        arch.append((x, ZS + (ZA - ZS) * math.sin(k * PI / 2) ** 0.6))
    lint = [(-HX - 1.45, ZS), (-HX - 1.45, ZA + 1.6), (HX + 1.45, ZA + 1.6), (HX + 1.45, ZS)] + list(reversed(arch))
    prism("Lintel", lint, (yF + 0.0) / 2, -yF, st)
    for i in range(7):
        x = -HX + 0.6 + i * (2 * HX - 1.2) / 6
        if i == 3:
            continue
        foil(f"Frieze{i}", x, yF - 0.02, ZA + 0.85, 0.28, sd, lobes=4, thick=0.04)
    shield = [(-0.55, ZA + 1.45), (0.55, ZA + 1.45), (0.55, ZA + 0.85), (0.0, ZA + 0.25), (-0.55, ZA + 0.85)]
    prism("Shield", shield, yF - 0.05, 0.1, sd)
    prism("ShieldField", [(x * 0.82, ZA + 0.85 + (z - ZA - 0.85) * 0.82) for x, z in shield], yF - 0.11, 0.04, K["crimson"])
    rtube("ShieldKey", [(0, yF - 0.14, ZA + 1.25), (0, yF - 0.14, ZA + 0.55)], 0.035, K["gilt"])
    hoop("ShieldBow", (0, yF - 0.14, ZA + 1.3), 0.09, "Y", K["gilt"], thick=0.02)
    # the mantel shelf and a short overmantel of blind lancets
    box("Mantel", (2 * HX + 3.6, -yF + 0.6, 0.3), (0, (yF - 0.6) / 2 + 0.1, ZA + 1.75), st, bevel=0.05)
    box("MantelBed", (2 * HX + 3.0, -yF + 0.2, 0.18), (0, (yF - 0.2) / 2 + 0.1, ZA + 1.51), sd, bevel=0.03)
    box("Over", (2 * HX + 2.4, 0.4, 1.9), (0, -0.2, ZA + 1.9 + 0.95), st, bevel=0.04)
    for i in range(5):
        x = -HX + 0.3 + i * (2 * HX - 0.6) / 4
        prism(f"Lancet{i}", [(x - 0.35, ZA + 2.15)] + [(px, pz) for px, pz in B43.arch_xz(x - 0.35, x + 0.35, ZA + 3.1, 0.55, n=8)] +
              [(x + 0.35, ZA + 2.15)], -0.43, 0.06, sd)
    # the firebox: sooty brick sides, a soot ceiling, a raised hearth stone
    bk = K["brickdk"]
    for sx in (-1, 1):
        rows = [[(sx * HX, yF + 0.2, 0.0), (sx * HX, yB, 0.0)], [(sx * HX, yF + 0.2, ZS), (sx * HX, yB, ZS)]]
        grid_surface(f"Cheek{sx}", rows, bk, [[(yF, 0), (yB, 0)], [(yF, ZS), (yB, ZS)]], target=lambda p: (0, p.y, p.z))
    box("Throat", (2 * HX, yB - yF - 0.2, 0.3), (0, (yF + 0.2 + yB) / 2, ZS + 0.15 + 0.0), K["soot"], bevel=0.0)
    box("Hearth", (2 * HX + 3.0, 1.6, 0.1), (0, yF - 0.8, 0.05), sd, bevel=0.02)
    box("HearthIn", (2 * HX, yB - yF, 0.02), (0, (yF + yB) / 2, 0.01), K["soot"], bevel=0.0)
    # firedogs at the cheeks (outside the clear 5.6), cold ash and charred ends raked to the left
    for sx in (-1, 1):
        x = sx * (HX - 0.4)
        sq_bar(f"DogBar{sx}", [(x, -0.6, 0.35), (x, 1.2, 0.35)], 0.05, iron)
        sq_bar(f"DogPost{sx}", [(x, -0.6, 0.02), (x, -0.6, 1.5)], 0.06, iron)
        sphere(f"DogBall{sx}", 0.16, (x, -0.6, 1.62), K["brass"], seg=12, rings=6)
        sq_bar(f"DogFoot{sx}", [(x - 0.3, -0.6, 0.03), (x, -0.6, 0.25), (x + 0.3, -0.6, 0.03)], 0.04, iron)
    for i in range(3):
        cyl(f"Log{i}", 0.16 - 0.02 * i, 1.1, (-HX + 0.45, 0.2 + i * 0.36, 0.19 + (0.0 if i != 1 else 0.0)), K["char"], rot=(PI / 2, 0, 0.1 * i), verts=10,
            bevel=0.02)
    for i in range(5):
        lathe(f"Ash{i}", [(0, 0), (0.45, 0), (0.25, 0.05), (0, 0.07)], K["ash"], seg=12, loc=(rnd.uniform(-2.2, 2.2), rnd.uniform(-0.6, 1.6), 0.02),
              scale=(rnd.uniform(1.0, 1.8), 1))
    # behind the fireback: the crawl throat (brick) to the duct flange at y = yB + 0.2 + 1.2
    yT = yB + 0.2
    yE = yT + 1.2
    for sx in (-1, 1):
        box(f"ThroatSide{sx}", (0.4, yE - yT, DUCT_H + 0.4), (sx * (DA + 0.2), (yT + yE) / 2, DUCT_H / 2 + 0.1), bk, bevel=0.0)
    box("ThroatTop", (2 * DA, yE - yT, 0.4), (0, (yT + yE) / 2, DUCT_H + 0.2), bk, bevel=0.0)
    box("ThroatFloor", (2 * DA, yE - yT, 0.1), (0, (yT + yE) / 2, -0.05), K["limedk"], bevel=0.0)
    flange("F", K, T(0, yE, 0) @ RZ(PI))
    # the slot under the hearth the fireback sinks into, iron guide channels at its sides, brick behind the cheeks
    SD = ZS + 0.4
    box("SlotFront", (2 * HX, 0.1, SD), (0, yB - 0.05, -SD / 2), bk, bevel=0.0)
    box("SlotBack", (2 * HX, 0.1, SD - 0.1), (0, yB + 0.25, -0.1 - (SD - 0.1) / 2), bk, bevel=0.0)
    box("SlotFloor", (2 * HX, 0.2, 0.1), (0, yB + 0.1, -SD + 0.05), bk, bevel=0.0)
    for sx in (-1, 1):
        box(f"Channel{sx}", (0.1, 0.36, ZS + SD), (sx * (HX + 0.05), yB + 0.1, (ZS - SD) / 2), iron, bevel=0.01)
        box(f"BackFill{sx}", (HX - DA - 0.4, 0.15, ZS + 0.3), (sx * (DA + 0.4 + (HX - DA - 0.4) / 2), yB + 0.275, (ZS + 0.3) / 2), bk, bevel=0.0)
    # the fireback: a cast plate with a raised border, an arched panel and a relief of a raven over crossed keys, 1688
    opening("FireplacePassage", "Slide0", "slide", (0.0, yB, 0.0), slide=(0, 0, -(ZS + 0.1)))
    FW, FH = 2 * HX - 0.02, ZS + 0.04
    box("Back", (FW, 0.2, FH), (0, yB + 0.1, FH / 2), iron, bevel=0.02)
    for sx in (-1, 1):
        box(f"BorderV{sx}", (0.18, 0.06, FH - 0.2), (sx * (FW / 2 - 0.15), yB - 0.03, FH / 2), iron, bevel=0.015)
    for k, z in enumerate((0.12, FH - 0.12)):
        box(f"BorderH{k}", (FW - 0.2, 0.06, 0.18), (0, yB - 0.03, z), iron, bevel=0.015)
    panel = [(-1.8, 0.8)] + B43.arch_xz(-1.8, 1.8, 4.2, 1.4, n=14) + [(1.8, 0.8)]
    rtube("PanelEdge", [(x, yB - 0.03, z) for x, z in panel] + [(-1.8, yB - 0.03, 0.8)], 0.05, iron)
    from nh_props_batch9 import raven
    raven("Raven", (0, yB - 0.12, 3.6), -PI / 2, 4.0, iron, iron)
    for k, (a, b) in enumerate((((-1.0, 1.4), (1.0, 3.0)), ((1.0, 1.4), (-1.0, 3.0)))):
        sq_bar(f"Key{k}", [(a[0], yB - 0.06, a[1]), (b[0], yB - 0.06, b[1])], 0.06, iron)
        hoop(f"KeyBow{k}", (b[0] * 1.08, yB - 0.06, b[1] + 0.12), 0.16, "Y", iron, thick=0.04)
    label("Date", "1688", iron, 0, yB - 0.03, 1.05, 1.1, 0.34, depth=0.04)
    set_group("Main")
    return _dims()


def tapestry_mat(name, W, H):
    """A woven hanging from the cloth's own "Brk" UV (studs): a crimson ground, a gilt diamond trellis with bone quatrefoil
    dots, an ink border with a gilt line, a fine rib; all invented."""
    m = flat(name, (0.16, 0.012, 0.026), 0.9, dirt=0.55)
    nt = m.node_tree
    L = nt.links.new

    def op(o, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = o
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Brk"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(uvn.outputs["UV"], sep.inputs["Vector"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    s = 1.1
    a = op("DIVIDE", op("ADD", u, v), s)
    b = op("DIVIDE", op("SUBTRACT", u, v), s)
    fa = op("ABSOLUTE", op("SUBTRACT", op("FRACT", a), 0.5))
    fb = op("ABSOLUTE", op("SUBTRACT", op("FRACT", b), 0.5))
    line = op("GREATER_THAN", op("MAXIMUM", fa, fb), 0.465)
    dot = op("LESS_THAN", op("ADD", op("POWER", fa, 2.0), op("POWER", fb, 2.0)), 0.012)
    edge = op("MINIMUM", op("MINIMUM", u, op("SUBTRACT", W, u)), op("MINIMUM", v, op("SUBTRACT", H, v)))
    border = op("LESS_THAN", edge, 0.55)
    gline = op("MULTIPLY", op("GREATER_THAN", edge, 0.38), op("LESS_THAN", edge, 0.46))
    inner = op("SUBTRACT", 1.0, border, clamp=True)
    gold = op("MAXIMUM", op("MULTIPLY", line, inner), gline)
    bone = op("MULTIPLY", dot, inner)
    src = next(n for n in nt.nodes if n.type == "RGB")
    old = [lk.to_socket for lk in src.outputs[0].links]
    for lk in list(src.outputs[0].links):
        nt.links.remove(lk)

    def mix(fac, c0, c1):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        L(fac, n.inputs[0])
        if isinstance(c0, tuple):
            n.inputs[6].default_value = (*c0, 1)
        else:
            L(c0, n.inputs[6])
        n.inputs[7].default_value = (*c1, 1)
        return n.outputs[2]
    col = mix(border, src.outputs[0], (0.018, 0.016, 0.03))
    col = mix(bone, col, (0.62, 0.56, 0.44))
    col = mix(gold, col, (0.55, 0.37, 0.12))
    # the fine weave rib
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.bands_direction = "X"; w1.inputs["Scale"].default_value = 60.0
    L(uvn.outputs["UV"], w1.inputs["Vector"])
    for to in old:
        L(col, to)
    B24._bump(m, w1.outputs["Fac"], 0.004, 0.5)
    return m


def cloth_sheet(name, W, ztop, zbot, y0, mat, nx=34, nz=36, fold=0.07, thick=0.04):
    """A hanging cloth W wide from ztop to zbot, soft vertical folds deeper toward the hem, the "Brk" UV in studs."""
    rows, uvs = [], []
    for j in range(nz + 1):
        t = j / nz
        z = ztop - t * (ztop - zbot)
        row, uv = [], []
        for i in range(nx + 1):
            q = i / nx
            x = -W / 2 + W * q
            y = y0 - fold * (0.5 + 0.5 * math.sin(q * 2 * PI * 4.5 + 0.6)) * (0.3 + 0.7 * t) - 0.015 * math.sin(q * 41) * t
            row.append((x, y, z))
            uv.append((W * q, z - zbot))
        rows.append(row)
        uvs.append(uv)
    ob = grid_surface(name, rows, mat, uvs, target=lambda p: (p.x, p.y - 1.0, p.z))
    md = ob.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = thick
    md.offset = 1.0
    return ob


def tapestry_passage(M):
    """A pointed limestone archway (4.4 wide, 7.9 high) through a 1.0 wall, hidden behind a woven hanging (Cloth0) on a gilt
    rod with fleur finials: the cloth swings out from the rod like the art kit's tapestries to let you through. Crimson ground,
    gilt trellis, bone quatrefoils, ink border, a fringe of tassels."""
    K = kit(M)
    st, sd = K["lime"], K["limedk"]
    HW, ZS, RISE = 2.2, 6.0, 1.9
    WY = 0.5
    arch = B43.arch_xz(-HW, HW, ZS, RISE, n=16)
    outer = B43.arch_xz(-HW - 0.7, HW + 0.7, ZS, RISE + 0.75, n=16)
    face = [(-HW - 0.7, 0.0), (-HW, 0.0)] + arch + [(HW, 0.0), (HW + 0.7, 0.0)] + list(reversed(outer))
    prism("Surround", face, 0.0, 2 * WY + 0.16, st)
    for sy in (-1, 1):
        rtube(f"Mould{sy}", [(x, sy * (WY + 0.1), z) for x, z in B43.arch_xz(-HW - 0.35, HW + 0.35, ZS, RISE + 0.37, n=18)], 0.07, sd)
    # the rod on brackets above the arch, 0.55 out from the wall face
    ZR = ZS + RISE + 1.2
    yR = -WY - 0.55
    for sx in (-1, 1):
        box(f"BracketPlate{sx}", (0.3, 0.05, 0.5), (sx * 2.9, -WY - 0.025, ZR), K["iron"], bevel=0.012)
        rtube(f"Bracket{sx}", [(sx * 2.9, -WY - 0.04, ZR - 0.15), (sx * 2.9, yR + 0.1, ZR - 0.1), (sx * 2.9, yR, ZR)], 0.035, K["iron"], poly=False)
    rtube("Rod", [(-3.35, yR, ZR), (3.35, yR, ZR)], 0.06, K["gilt"])
    for sx in (-1, 1):
        lathe(f"Finial{sx}", [(0, 0), (0.09, 0), (0.12, 0.08), (0.07, 0.16), (0.12, 0.28), (0.0, 0.42)], K["gilt"], seg=12, loc=(0, 0, 0))
        ob = P.PARTS[-1]
        ob.matrix_world = T(sx * 3.35, yR, ZR) @ RY(sx * PI / 2) @ ob.matrix_world
    # the cloth: hinged on the rod line (axis X), swings its hem out toward the front
    W = 6.0
    ZT = ZR - 0.12
    opening("TapestryPassage", "Cloth0", "swingcloth", (0.0, yR, ZR), angle=-55, axis=(1, 0, 0))
    for i in range(14):
        x = -W / 2 + 0.2 + i * (W - 0.4) / 13
        hoop(f"Ring{i}", (x, yR, ZR - 0.02), 0.09, "X", K["gilt"], thick=0.015)
    cl = tapestry_mat("PassageTapestry", W, ZT - 0.1)
    cloth_sheet("Cloth", W, ZT, 0.1, yR - 0.02, cl)
    for i in range(16):
        x = -W / 2 + 0.2 + i * (W - 0.4) / 15
        B41.tassel(f"Tassel{i}", x, yR - 0.1, 0.42, K["gilt"], s=0.8)
    set_group("Main")
    return _dims()


def sliding_wall_panel(M):
    """A limestone wall of blind lancet panels (1.0 thick) whose centre panel (Slide0, 3.6 x 8.0) slides to the right into a
    pocket behind the right-hand panel; the trigger is the carved rose boss (Boss0) on the left panel, which presses in."""
    K = kit(M)
    st, sd, gl = K["lime"], K["limedk"], K["gilt"]
    WY = 0.5
    BW, ZH = 3.6, 8.0             # a bay's panel width, height
    yF = -WY - 0.3                # the arcade's front (0.3 proud of the wall's face)
    bays = (-1, 0, 1)
    # the arcade: shafts between bays, a moulded head with gables over each panel, a plinth
    for k, x in enumerate((-1.5 * BW - 0.25, -0.5 * BW - 0.25, 0.5 * BW + 0.25, 1.5 * BW + 0.25)):
        box(f"Shaft{k}", (0.5, 0.36, ZH + 0.5), (x, yF + 0.18, (ZH + 0.5) / 2), st, bevel=0.04)
        cyl(f"Colonette{k}", 0.12, ZH - 0.8, (x, yF - 0.06, 0.4 + (ZH - 0.8) / 2), st, verts=12, bevel=0.01)
    box("Plinth", (3 * BW + 2.0, 0.5, 0.4), (0, yF + 0.2, 0.2), sd, bevel=0.03)
    box("Head", (3 * BW + 2.0, 0.4, 1.4), (0, yF + 0.2, ZH + 0.5 + 0.7), st, bevel=0.04)
    for i, bx in enumerate(bays):
        x = bx * (BW + 0.5)
        prism(f"Gable{i}", [(x - BW / 2, ZH + 0.5)] + B43.arch_xz(x - BW / 2, x + BW / 2, ZH + 0.5, 1.2, n=10)[1:-1] + [(x + BW / 2, ZH + 0.5)],
              yF - 0.04, 0.08, sd)
    # side panels (fixed) with a sunk lancet each; the pocket behind the right one
    for i, bx in enumerate((-1, 1)):
        x = bx * (BW + 0.5)
        box(f"Panel{i}", (BW, 0.3, ZH - 0.4), (x, yF + 0.15 + 0.0, 0.4 + (ZH - 0.4) / 2), st, bevel=0.02)
        lan = [(x - 1.2, 1.0)] + B43.arch_xz(x - 1.2, x + 1.2, ZH - 2.2, 1.3, n=10)[1:-1] + [(x + 1.2, 1.0)]
        prism(f"Lancet{i}", lan, yF - 0.02, 0.04, sd)
    box("PocketBack", (BW + 0.5, 0.1, ZH), (BW + 0.5, yF + 0.6 + 0.05, ZH / 2), sd, bevel=0.0)
    box("PocketTop", (2 * BW + 0.6, 0.3, 0.1), (BW / 2 + 0.3, yF + 0.45, ZH + 0.05), K["iron"], bevel=0.01)
    box("Track", (2 * BW + 0.6, 0.3, 0.06), (BW / 2 + 0.3, yF + 0.45, 0.03), K["iron"], bevel=0.01)
    # the reveal of the passage behind the centre panel
    for sx in (-1, 1):
        box(f"Reveal{sx}", (0.1, 2 * WY, ZH), (sx * (BW / 2 + 0.05), 0.0, ZH / 2), sd, bevel=0.0)
    box("RevealHead", (BW, 2 * WY, 0.1), (0, 0.0, ZH + 0.05), sd, bevel=0.0)
    # the boss on the left panel: a carved rose that presses in 0.1 (Boss0)
    xb = -(BW + 0.5)
    opening("SlidingWallPanel", "Boss0", "press", (xb, yF - 0.02, 4.3), slide=(0, 0.1, 0))
    lathe("Boss", [(0, 0), (0.32, 0), (0.33, 0.06), (0.24, 0.14), (0.1, 0.2), (0, 0.21)], st, seg=20, loc=(0, 0, 0))
    ob = P.PARTS[-1]
    ob.matrix_world = T(xb, yF - 0.02, 4.3) @ RX(PI / 2) @ ob.matrix_world
    foil("BossFoil", xb, yF - 0.22, 4.3, 0.15, sd, lobes=5, thick=0.03)
    # the sliding panel: 0.3 thick behind the arcade face, a sunk lancet with a trefoil head and a gilt-lined quatrefoil
    opening("SlidingWallPanel", "Slide0", "slide", (0.0, yF + 0.3, 0.06), slide=(BW + 0.5, 0, 0))
    box("Leaf", (BW, 0.3, ZH - 0.12), (0, yF + 0.45, 0.06 + (ZH - 0.12) / 2), st, bevel=0.02)
    lan = [(-1.2, 1.0)] + B43.arch_xz(-1.2, 1.2, ZH - 2.2, 1.3, n=10)[1:-1] + [(1.2, 1.0)]
    prism("LeafLancet", lan, yF + 0.28, 0.04, sd)
    foil("LeafFoil", 0, yF + 0.26, ZH - 1.7, 0.42, gl, lobes=4, thick=0.03)
    box("LeafPull", (0.08, 0.06, 0.5), (BW / 2 - 0.3, yF + 0.27, 3.8), K["iron"], bevel=0.01)
    set_group("Main")
    return _dims()


def trapdoor_ladder(M):
    """A hidden trapdoor flush with a flagstone floor (origin at floor level): three flags set in an iron tray (Door0, hinged
    on its +Y edge, lifts up), a recessed ring, then a limestone-lined shaft 9 deep with an iron ladder down the +Y wall to an
    arched doorway at the bottom (-Y side, 4.4 x 7.2)."""
    K = kit(M)
    rnd = random.Random(5335)
    S = DA
    D = 9.0
    st, sd, iron, ash = K["lime"], K["limedk"], K["iron"], K["ashlar"]
    # the floor patch round the opening (flush, z -0.3 .. 0): nine flags round the hole
    for k, (cx, cy, w, d) in enumerate(((0, -S - 1.0, 2 * S + 4.0, 2.0), (0, S + 1.0, 2 * S + 4.0, 2.0), (-S - 1.0, 0, 2.0, 2 * S), (S + 1.0, 0, 2.0, 2 * S))):
        box(f"Flag{k}", (w - 0.04, d - 0.04, 0.3), (cx, cy, -0.15), st, bevel=0.03)
    for sx in (-1, 1):
        box(f"FrameX{sx}", (0.08, 2 * S, 0.3), (sx * (S - 0.04), 0, -0.15), iron, bevel=0.01)
    for sy in (-1, 1):
        box(f"FrameY{sy}", (2 * S - 0.16, 0.08, 0.3), (0, sy * (S - 0.04), -0.15), iron, bevel=0.01)
    # the shaft: ashlar walls (inner faces at +-S), the -Y wall with the arched doorway at the bottom
    def wall(name, pts, z0, z1, tgt):
        rows = [[(p[0], p[1], z0) for p in pts], [(p[0], p[1], z1) for p in pts]]
        uvs = [[(p[0] + p[1], z0) for p in pts], [(p[0] + p[1], z1) for p in pts]]
        return grid_surface(name, rows, ash, uvs, target=tgt)
    wall("WallB", [(-S, S), (S, S)], -D, -0.3, lambda p: (p.x, 0, p.z))
    for sx in (-1, 1):
        wall(f"WallX{sx}", [(sx * S, -S), (sx * S, S)], -D, -0.3, lambda p: (0, p.y, p.z))
    dw, dz = 2.2, -D + 6.0
    door = [(-S, -D), (-dw, -D), (-dw, dz)] + [(x, z) for x, z in B43.arch_xz(-dw, dw, dz, 1.2, n=12)[1:-1]] + [(dw, dz), (dw, -D), (S, -D), (S, -0.3), (-S, -0.3)]
    poly_face("WallF", [[(x, -S, z) for x, z in door]], ash, (0, 1, 0), uvfn=lambda co: (co.x, co.z))
    vou = [(x, z) for x, z in B43.arch_xz(-dw - 0.4, dw + 0.4, dz, 1.6, n=12)]
    rtube("DoorMould", [(x, -S + 0.06, z) for x, z in vou], 0.08, st)
    box("ShaftFloor", (2 * S, 2 * S + 1.0, 0.3), (0, -0.5, -D - 0.15), sd, bevel=0.02)
    # the ladder: iron stiles on brackets, round rungs
    yl = S - 0.45
    for sx in (-1, 1):
        sq_bar(f"Stile{sx}", [(sx * 0.9, yl, -D + 0.02), (sx * 0.9, yl, -0.36)], 0.05, iron)
        for j, z in enumerate((-D + 2.0, -4.5, -1.2)):
            sq_bar(f"Stay{sx}{j}", [(sx * 0.9, yl, z), (sx * 0.9, S, z)], 0.035, iron)
    for i in range(11):
        z = -D + 0.6 + i * 0.75
        rtube(f"Rung{i}", [(-0.9, yl, z), (0.9, yl, z)], 0.035, iron)
    # the outer shell of the shaft (tiled castle stone)
    set_group("Wall")
    for sx in (-1, 1):
        box(f"ShellX{sx}", (0.3, 2 * S + 0.6, D - 0.3), (sx * (S + 0.15), 0, -0.3 - (D - 0.3) / 2), K["stone"], bevel=0.0)
    box("ShellB", (2 * S, 0.3, D - 0.3), (0, S + 0.15, -0.3 - (D - 0.3) / 2), K["stone"], bevel=0.0)
    box("ShellF", (2 * S, 0.3, D - 0.3 - 7.6), (0, -S - 0.15, -0.3 - (D - 0.3 - 7.6) / 2), K["stone"], bevel=0.0)
    # the hatch: three flags in an iron tray, hinged on its +Y edge, lifts up (about +X by -100)
    opening("TrapdoorLadder", "Door0", "hatch", (0.0, S - 0.08, 0.0), angle=-100, axis=(1, 0, 0))
    HS = S - 0.1
    box("Tray", (2 * HS, 2 * HS, 0.06), (0, 0, -0.27), iron, bevel=0.01)
    for sx in (-1, 1):
        box(f"TrayX{sx}", (0.05, 2 * HS, 0.24), (sx * (HS - 0.025), 0, -0.12), iron, bevel=0.005)
    for sy in (-1, 1):
        box(f"TrayY{sy}", (2 * HS - 0.1, 0.05, 0.24), (0, sy * (HS - 0.025), -0.12), iron, bevel=0.005)
    for k in range(3):
        w = (2 * HS - 0.14) / 3
        box(f"HFlag{k}", (w - 0.03, 2 * HS - 0.14, 0.22), (-HS + 0.07 + w * (k + 0.5), 0, -0.11), st, bevel=0.03)
    cyl("RingCup", 0.2, 0.06, (0, -HS + 0.55, -0.03), K["soot"], verts=16, bevel=0.0)
    hoop("Ring", (0, -HS + 0.55, -0.03), 0.15, "Z", iron, thick=0.02)
    for sx in (-1, 1):
        cyl(f"Knuckle{sx}", 0.06, 0.6, (sx * 1.6, S - 0.08, -0.04), iron, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
        box(f"Strap{sx}", (0.18, 1.5, 0.03), (sx * 1.6, S - 0.85, -0.315), iron, bevel=0.005)
    set_group("Main")
    moss_tufts("Moss", [(-S - 1.9, -S - 1.8, 0.0), (S + 1.7, S + 1.9, 0.0)], K, rnd, size=0.07)
    return _dims()


# ------------------------------------------------------------------ the hidden spiral stair

SR_IN, SR_OUT, SR_NEW = 5.0, 5.6, 0.5   # shaft inner / outer radius, newel radius
A0 = -65.0                              # the first tread's start angle (degrees; the doorway is at -90)


def _ring_wall(name, r, z0, z1, mat, inward, gaps=(), seg=72, tiled=False):
    """A cylinder wall at radius r from z0 to z1 (Brk UV: arc length, z), facing in or out, leaving angular gaps
    [(a0, a1, ztop)] (degrees) open below ztop."""
    angs = sorted(set([360.0 * i / seg - 180.0 for i in range(seg + 1)] + [g[0] for g in gaps] + [g[1] for g in gaps]))
    zs = sorted(set([z0, z1] + [g[2] for g in gaps if z0 < g[2] < z1]))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Brk")
    for ia in range(len(angs) - 1):
        a, b = angs[ia], angs[ia + 1]
        am = (a + b) / 2
        for iz in range(len(zs) - 1):
            za, zb = zs[iz], zs[iz + 1]
            if any(g[0] <= am <= g[1] and zb <= g[2] + 1e-6 for g in gaps):
                continue
            pts = [(a, za), (b, za), (b, zb), (a, zb)]
            vs = [bm.verts.new((r * math.cos(x * DEG), r * math.sin(x * DEG), z)) for x, z in pts]
            f = bm.faces.new(vs)
            for lp, (x, z) in zip(f.loops, pts):
                lp[uvl].uv = (r * x * DEG, z)
            c = f.calc_center_median()
            want = Vector((-c.x, -c.y, 0)) if inward else Vector((c.x, c.y, 0))
            if f.normal.dot(want) < 0:
                f.normal_flip()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return bm_obj(name, bm, mat, smooth=True)


def _annulus(name, r0, r1, a0, a1, z, mat, up=True, n=None):
    n = n or max(2, int(abs(a1 - a0) / 5))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Brk")
    for i in range(n):
        a, b = (a0 + (a1 - a0) * i / n) * DEG, (a0 + (a1 - a0) * (i + 1) / n) * DEG
        pts = [(r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a)), (r1 * math.cos(b), r1 * math.sin(b)), (r0 * math.cos(b), r0 * math.sin(b))]
        f = bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts])
        for lp, (x, y) in zip(f.loops, pts):
            lp[uvl].uv = (x, y)
        if (f.normal.z > 0) != up:
            f.normal_flip()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return bm_obj(name, bm, mat)


def _tread(name, a0, a1, ztop, mat, t=0.5):
    """A wedge tread from the newel to the wall between angles a0..a1 (degrees), ztop - t .. ztop, a rounded nosing line."""
    n = 4
    bm = bmesh.new()
    rows = []
    for zz in (ztop - t, ztop):
        ring_ = []
        for r in (SR_NEW, SR_IN - 0.02):
            for i in range(n + 1):
                a = (a0 + (a1 - a0) * i / n) * DEG
                ring_.append(bm.verts.new((r * math.cos(a), r * math.sin(a), zz)))
        rows.append(ring_)
    lo, hi = rows
    m = n + 1
    def q(*v):
        return bm.faces.new(v)
    for i in range(n):
        q(lo[i], lo[i + 1], lo[m + i + 1], lo[m + i])
        q(hi[i], hi[m + i], hi[m + i + 1], hi[i + 1])
        q(lo[i], hi[i], hi[i + 1], lo[i + 1])
        q(lo[m + i], lo[m + i + 1], hi[m + i + 1], hi[m + i])
    q(lo[0], lo[m], hi[m], hi[0])
    q(lo[n], hi[n], hi[m + n], lo[m + n])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = bm_obj(name, bm, mat)
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = 0.03
    b.segments = 2
    b.limit_method = "ANGLE"
    return ob


def _stair_turn(prefix, K, z0, k0=0):
    """Sixteen treads making one full turn of 8 from z0 (each 0.5 rise, 22.5 degrees, overlapping the next by 4)."""
    for k in range(16):
        a = A0 + 22.5 * k
        _tread(f"{prefix}{k}", a, a + 26.5, z0 + 0.5 * (k + 1), K["lime"])


def _rail_turn(prefix, K, z0):
    pts = []
    for i in range(33):
        a = (A0 + 11.25 * i) * DEG
        pts.append((4.72 * math.cos(a), 4.72 * math.sin(a), z0 + 0.25 * i + 3.2))
    rtube(f"{prefix}Rail", pts, 0.045, K["iron"])
    for j in range(4):
        i = 4 + 8 * j
        a = (A0 + 11.25 * i) * DEG
        z = z0 + 0.25 * i + 3.2
        rtube(f"{prefix}Bracket{j}", [(SR_IN * math.cos(a), SR_IN * math.sin(a), z - 0.25), (4.72 * math.cos(a), 4.72 * math.sin(a), z - 0.04)], 0.03, K["iron"])


def secret_spiral_stair(M):
    """A hidden stair in a round limestone shaft (11.2 across): a newel and sixteen wedge treads to each full turn of 8 (7.5
    headroom), an iron rail on the wall, a candle in a wall niche (Glow). Three pieces, each under 20.48: Main (0..8, the way
    in at the bottom, front -Y), Upper (8..16, one more turn, can be repeated 8 higher each time) and Head (16..24, the landing
    and the way out, also facing -Y, under a ribbed ceiling); their outer shells are Wall, UpperWall and HeadWall (tiled)."""
    K = kit(M)
    ash, st, sd = K["ashlar"], K["lime"], K["limedk"]
    door = (-111.0, -69.0)
    # Main: floor, newel, treads, wall with the doorway (6.8 high under a lintel), rail
    _annulus("Floor", SR_NEW, SR_IN, -180, 180, 0.0, sd, n=72)
    cyl("Newel", SR_NEW, 8.0, (0, 0, 4.0), st, verts=24, bevel=0.0)
    hoop("NewelRope", (0, 0, 0.3), SR_NEW + 0.04, "Z", st, thick=0.06)
    _stair_turn("Tread", K, 0.0)
    _ring_wall("WallIn", SR_IN, 0.0, 8.0, ash, True, gaps=[(door[0], door[1], 6.8)])
    _rail_turn("R0", K, 0.0)
    # the doorway: jambs and lintel through the wall thickness
    for k, a in enumerate(door):
        x, y = math.cos(a * DEG), math.sin(a * DEG)
        box(f"DoorJamb{k}", (0.3, SR_OUT - SR_IN + 0.06, 6.8), ((SR_IN + SR_OUT) / 2 * x, (SR_IN + SR_OUT) / 2 * y, 3.4), st, bevel=0.02,
            rot=(0, 0, a * DEG + PI / 2))
    am = (door[0] + door[1]) / 2 * DEG
    box("DoorLintel", (3.9, SR_OUT - SR_IN + 0.06, 0.5), ((SR_IN + SR_OUT) / 2 * math.cos(am), (SR_IN + SR_OUT) / 2 * math.sin(am), 7.05), st, bevel=0.03,
        rot=(0, 0, am + PI / 2))
    set_group("Wall")
    _ring_wall("Shell", SR_OUT, -0.4, 8.0, K["stone"], False, gaps=[(door[0], door[1], 6.8)])
    _annulus("ShellBottom", SR_IN, SR_OUT, -180, 180, -0.4, K["stone"], up=False, n=72)
    # Upper: one more turn
    set_group("Upper")
    cyl("NewelU", SR_NEW, 8.0, (0, 0, 12.0), st, verts=24, bevel=0.0)
    hoop("NewelRopeU", (0, 0, 8.0), SR_NEW + 0.04, "Z", st, thick=0.06)
    _stair_turn("TreadU", K, 8.0)
    _ring_wall("WallInU", SR_IN, 8.0, 16.0, ash, True)
    _rail_turn("R1", K, 8.0)
    an = 135 * DEG
    s = _mark()
    prism("Niche", [(0.0, 0.0), (0.0, -0.5), (-0.45, -0.3), (-0.55, 0.0)], 0.0, 0.7, sd, plane="YZ", bevel=0.02)
    lathe("NicheCandle", [(0, 0), (0.07, 0), (0.075, 0.35), (0.06, 0.42), (0, 0.42)], K["wax"], seg=12, loc=(0, -0.3, 0.0))
    set_group("Glow")
    flame("NicheFlame", (0, -0.3, 0.45), h=0.11)
    set_group("Upper")
    _xform(s, T(SR_IN * math.cos(an), SR_IN * math.sin(an), 12.2) @ RZ(an + PI / 2))
    set_group("UpperWall")
    _ring_wall("ShellU", SR_OUT, 8.0, 16.0, K["stone"], False)
    # Head: the landing sector, the way out, the ceiling
    set_group("Head")
    land = (A0 + 4.0, A0 + 60.0)
    out = (A0 + 12.0, A0 + 54.0)
    _annulus("Landing", SR_NEW, SR_IN, land[0], land[1], 16.0, st)
    _annulus("LandingUnder", SR_NEW, SR_IN, land[0], land[1], 15.55, sd, up=False)
    for k, a in enumerate(land):
        x, y = math.cos(a * DEG), math.sin(a * DEG)
        rows = [[(SR_NEW * x, SR_NEW * y, 15.55), (SR_IN * x, SR_IN * y, 15.55)], [(SR_NEW * x, SR_NEW * y, 16.0), (SR_IN * x, SR_IN * y, 16.0)]]
        grid_surface(f"LandingEdge{k}", rows, sd, [[(0, 0), (1, 0)], [(0, 1), (1, 1)]],
                     target=lambda p, a=a, k=k: (p.x + math.cos((a + (-90 if k == 0 else 90)) * DEG), p.y + math.sin((a + (-90 if k == 0 else 90)) * DEG), p.z))
    cyl("NewelH", SR_NEW, 7.6, (0, 0, 19.8), st, verts=24, bevel=0.0)
    hoop("NewelRopeH", (0, 0, 16.0), SR_NEW + 0.04, "Z", st, thick=0.06)
    _ring_wall("WallInH", SR_IN, 16.0, 23.6, ash, True, gaps=[(out[0], out[1], 23.0)])
    _annulus("Ceiling", SR_NEW, SR_IN, -180, 180, 23.6, sd, up=False, n=72)
    for j in range(6):
        a = (j * 60) * DEG
        rtube(f"CeilRib{j}", [(SR_NEW * math.cos(a), SR_NEW * math.sin(a), 23.51), (SR_IN * math.cos(a), SR_IN * math.sin(a), 23.51)], 0.09, st)
    # an iron balustrade on the landing's open edge (the stairwell side)
    a = land[1] * DEG
    for i in range(7):
        r = SR_NEW + 0.3 + i * (SR_IN - SR_NEW - 0.6) / 6
        sq_bar(f"Baluster{i}", [(r * math.cos(a) - 0.12 * math.sin(a), r * math.sin(a) + 0.12 * math.cos(a), 16.0),
                                (r * math.cos(a) - 0.12 * math.sin(a), r * math.sin(a) + 0.12 * math.cos(a), 19.3)], 0.03, K["iron"])
    rtube("Handrail", [((SR_NEW + 0.2) * math.cos(a) - 0.12 * math.sin(a), (SR_NEW + 0.2) * math.sin(a) + 0.12 * math.cos(a), 19.35),
                       ((SR_IN - 0.05) * math.cos(a) - 0.12 * math.sin(a), (SR_IN - 0.05) * math.sin(a) + 0.12 * math.cos(a), 19.35)], 0.05, K["iron"])
    for k, a2 in enumerate(out):
        x, y = math.cos(a2 * DEG), math.sin(a2 * DEG)
        box(f"OutJamb{k}", (0.3, SR_OUT - SR_IN + 0.06, 7.0), ((SR_IN + SR_OUT) / 2 * x, (SR_IN + SR_OUT) / 2 * y, 19.5), st, bevel=0.02,
            rot=(0, 0, a2 * DEG + PI / 2))
    am = (out[0] + out[1]) / 2 * DEG
    box("OutLintel", (4.3, SR_OUT - SR_IN + 0.06, 0.5), ((SR_IN + SR_OUT) / 2 * math.cos(am), (SR_IN + SR_OUT) / 2 * math.sin(am), 23.25), st, bevel=0.03,
        rot=(0, 0, am + PI / 2))
    set_group("HeadWall")
    _ring_wall("ShellH", SR_OUT, 16.0, 24.0, K["stone"], False, gaps=[(out[0], out[1], 23.0)])
    _annulus("ShellTop", 0.01, SR_OUT, -180, 180, 24.0, K["stone"], n=72)
    set_group("Main")
    return _dims()


# ------------------------------------------------------------------ the stage crawlspace and the boarded passage

def stage_crawlspace(M):
    """An 8 x 8 stage module (deck 3.2 up) over a dug crawlspace 6.0 clear under its iron joists (floor 3.4 below the room's),
    open at both sides so modules chain along X; a deck trap (Door0, 5.6 x 5.6) hinged on its -X edge with an iron ladder
    under it, a lacquered apron with gilt mouldings and a louvred peep grille, a crimson velvet valance, brick piers, an old
    trunk with a tragedy mask and a rolled backdrop in the dark."""
    K = kit(M)
    rnd = random.Random(5341)
    ZD, ZJ, ZP = 3.2, 2.6, -3.4      # deck top, joist bottoms, pit floor
    pk, iron, br = K["plankdk"], K["iron"], K["brickdk"]
    t0, t1 = -1.9, 3.7               # the trap along Y
    tx = DA
    # deck boards (along X) with the trap opening
    n = 20
    for i in range(n):
        y = -4 + 8 * (i + 0.5) / n
        w = 8 / n - 0.012
        if t0 < y < t1:
            for k, (a, b) in enumerate(((-4.0, -tx), (tx, 4.0))):
                box(f"Board{i}_{k}", (b - a - 0.01, w, 0.2), ((a + b) / 2, y, ZD - 0.1), pk, bevel=0.01)
        else:
            box(f"Board{i}", (7.99, w, 0.2), (0, y, ZD - 0.1), pk, bevel=0.01)
    # joists: iron beams along X on piers, trimmers along Y round the trap
    for j, y in enumerate((-3.6, -2.1, 3.85)):
        box(f"Joist{j}", (8.0, 0.25, ZD - 0.2 - ZJ), (0, y, (ZD - 0.2 + ZJ) / 2), iron, bevel=0.01)
    for sx in (-1, 1):
        box(f"Trimmer{sx}", (0.25, t1 - t0, ZD - 0.2 - ZJ), (sx * (tx + 0.125), (t0 + t1) / 2, (ZD - 0.2 + ZJ) / 2), iron, bevel=0.01)
    for sx in (-1, 1):
        for sy, y in ((-1, -3.6), (1, 3.85)):
            box(f"Pier{sx}{sy}", (0.7, 0.7, ZJ - ZP), (sx * 3.55, y if sy < 0 else 3.55, (ZJ + ZP) / 2), br, bevel=0.03)
    # the pit: brick retaining walls front and back (below the room's floor), an earth and flag floor
    for sy in (-1, 1):
        box(f"PitWall{sy}", (8.0, 0.3, -ZP), (0, sy * 3.85 if sy < 0 else 4.0 - 0.15, ZP / 2), br, bevel=0.0)
    box("PitFloor", (8.0, 7.4, 0.2), (0, 0.15, ZP - 0.1), K["limedk"], bevel=0.0)
    # the apron (front, y = -4 .. -3.85 above the room's floor): lacquered panels, gilt mouldings, a peep grille
    box("Apron", (8.0, 0.15, ZD - 0.2), (0, -3.925, (ZD - 0.2) / 2), K["lacquer"], bevel=0.01)
    for k, z in enumerate((0.15, ZD - 0.35)):
        box(f"ApronMould{k}", (8.0, 0.05, 0.08), (0, -4.025, z), K["gilt"], bevel=0.01)
    for i in range(4):
        x = -3.0 + i * 2.0
        if i == 2:
            continue
        for k, (a, b) in enumerate((((x - 0.7, 0.45), (x + 0.7, 0.45)), ((x - 0.7, ZD - 0.65), (x + 0.7, ZD - 0.65)), ((x - 0.7, 0.45), (x - 0.7, ZD - 0.65)),
                                    ((x + 0.7, 0.45), (x + 0.7, ZD - 0.65)))):
            rtube(f"Panel{i}{k}", [(a[0], -4.02, a[1]), (b[0], -4.02, b[1])], 0.025, K["gilt"])
    for j in range(8):
        box(f"Louvre{j}", (1.4, 0.04, 0.2), (1.0, -4.03, 0.6 + j * 0.24), K["iron"], bevel=0.005, rot=(-0.6, 0, 0))
    # the velvet valance on the deck's front edge
    rows, uvs = [], []
    for j in range(5):
        z = ZD - 0.02 - 0.12 * j
        row = [(-4 + 8 * i / 48, -4.06 - 0.03 * math.sin(i / 48 * PI * 24) * (j / 4), z) for i in range(49)]
        rows.append(row)
        uvs.append([(p[0], z) for p in row])
    vel = grid_surface("Valance", rows, K["velvet"], uvs, target=lambda p: (p.x, p.y - 1, p.z))
    md = vel.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = 0.03
    rtube("ValanceFringe", [(-4.0, -4.07, ZD - 0.5), (4.0, -4.07, ZD - 0.5)], 0.03, K["gilt"])
    # the ladder under the trap (iron) and the clutter
    for sx in (-1, 1):
        sq_bar(f"LadStile{sx}", [(sx * 0.8, t1 - 0.25, ZP), (sx * 0.8, t1 - 0.25, ZD - 0.2)], 0.045, iron)
    for i in range(8):
        rtube(f"LadRung{i}", [(-0.8, t1 - 0.25, ZP + 0.6 + i * 0.75), (0.8, t1 - 0.25, ZP + 0.6 + i * 0.75)], 0.03, iron)
    s = _mark()
    box("Trunk", (1.8, 1.0, 1.0), (0, 0, 0.5), K["plank"], bevel=0.04)
    for k, x in enumerate((-0.6, 0.6)):
        box(f"TrunkBand{k}", (0.12, 1.04, 1.04), (x, 0, 0.5), iron, bevel=0.01)
    box("TrunkLock", (0.2, 0.06, 0.24), (0, -0.52, 0.8), K["brass"], bevel=0.02)
    lathe("Mask", [(0, 0), (0.28, 0.0), (0.3, 0.06), (0.22, 0.1), (0, 0.11)], K["china"], seg=24, loc=(0.2, 0.0, 1.0), scale=(0.8, 1.0))
    for sx in (-1, 1):
        box(f"MaskEye{sx}", (0.08, 0.03, 0.012), (0.2 + sx * 0.09, -0.07, 1.11), K["ink"], bevel=0.0, rot=(0, 0, sx * 0.3))
    _xform(s, T(-2.4, 1.2, ZP))
    cyl("Backdrop", 0.32, 6.6, (0.6, -2.4, ZP + 0.32), K["canvas"], rot=(0, PI / 2, 0.05), verts=16, bevel=0.02)
    for i in range(6):
        lathe(f"Dust{i}", [(0, 0), (0.5, 0), (0.3, 0.03), (0, 0.04)], K["ash"], seg=10, loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), ZP), scale=(1.6, 1))
    # the trap: hinged on its -X edge, lifts up (about +Y by -100)
    opening("StageCrawlspace", "Door0", "hatch", (-tx, (t0 + t1) / 2, ZD), angle=-100, axis=(0, 1, 0))
    m = 10
    for i in range(m):
        y = t0 + (t1 - t0) * (i + 0.5) / m
        box(f"TrapBoard{i}", (2 * tx - 0.02, (t1 - t0) / m - 0.012, 0.2), (0, y, ZD - 0.1), pk, bevel=0.01)
    for k, x in enumerate((-tx + 0.6, tx - 0.6)):
        box(f"TrapBatten{k}", (0.3, t1 - t0 - 0.4, 0.1), (x, (t0 + t1) / 2, ZD - 0.25), pk, bevel=0.01)
    box("TrapRing", (0.24, 0.05, 0.02), (tx - 0.4, (t0 + t1) / 2, ZD + 0.01), K["brass"], bevel=0.005)
    set_group("Main")
    return _dims()


def boarded_passage(M):
    """A pointed arch through a 1.2 stone wall (4.4 x 7.9), boarded up: nine planks (Board0..8) nailed across the dressed
    quoins, edge to edge so nothing shows through, the top one wide over the arch; the seventh pried loose at one end on a
    bent nail; a chalked warning sigil across two planks; a crowbar against the wall. The wall faces are tiled (Wall)."""
    K = kit(M)
    rnd = random.Random(5342)
    st, sd = K["lime"], K["limedk"]
    HW, ZS, RISE = 2.2, 6.0, 1.9
    WY = 0.6
    WW, WH = 10.0, 10.0
    arch = B43.arch_xz(-HW, HW, ZS, RISE, n=16)
    hole = [(-HW, 0.0)] + arch + [(HW, 0.0)]
    # quoins and voussoirs round the arch, 0.05 proud of both faces
    for sy in (-1, 1):
        y = sy * (WY + 0.025)
        for i in range(6):
            z0 = i * 1.0
            w = 0.8 if i % 2 == 0 else 0.55
            for sx in (-1, 1):
                box(f"Quoin{sy}{sx}{i}", (w, 0.05, 0.98), (sx * (HW + w / 2), y, z0 + 0.49), st, bevel=0.02)
        vou = B43.arch_xz(-HW - 0.7, HW + 0.7, ZS, RISE + 0.75, n=16)
        prism(f"Arch{sy}", [(-HW - 0.7, ZS), (-HW, ZS)] + arch[1:-1] + [(HW, ZS), (HW + 0.7, ZS)] + list(reversed(vou[1:-1])), y, 0.05, st)
    # the reveal through the wall
    for sx in (-1, 1):
        box(f"RevealJ{sx}", (0.02, 2 * WY, ZS), (sx * (HW + 0.01), 0, ZS / 2), sd, bevel=0.0)
    rows = [[(x, -WY, z) for x, z in arch], [(x, WY, z) for x, z in arch]]
    grid_surface("RevealArch", rows, sd, [[(x, z) for x, z in arch], [(x, z) for x, z in arch]], target=lambda p: (0, p.y, ZS))
    # the wall section (tiled): both faces with the arch hole, ends and top
    set_group("Wall")
    face = [(-WW / 2, 0.0), (-HW, 0.0)] + arch + [(HW, 0.0), (WW / 2, 0.0), (WW / 2, WH), (-WW / 2, WH)]
    for sy in (-1, 1):
        poly_face(f"Face{sy}", [[(x, sy * WY, z) for x, z in face]], K["stone"], (0, sy, 0))
    poly_face("Top", [[(-WW / 2, -WY, WH), (WW / 2, -WY, WH), (WW / 2, WY, WH), (-WW / 2, WY, WH)]], K["stone"], (0, 0, 1))
    for sx in (-1, 1):
        poly_face(f"End{sx}", [[(sx * WW / 2, -WY, 0), (sx * WW / 2, WY, 0), (sx * WW / 2, WY, WH), (sx * WW / 2, -WY, WH)]], K["stone"], (sx, 0, 0))
    # the boards: on the quoins' faces (front y = -WY - 0.05), each its own piece with its origin at its centre
    yb = -WY - 0.05
    th = 0.16
    hs = [0.92] * 8 + [1.0]
    z = 0.0
    for i, h in enumerate(hs):
        L = 2 * (HW + 0.75) if i < 8 else 2 * (HW + 0.95)
        zc = z + h / 2
        pried = i == 6
        name = f"Board{i}"
        opening("BoardedPassage", name, "board", (0.0, yb - th / 2, zc), slide=(0, -1.5, -0.5))
        s = _mark()
        pk = K["plank"] if i % 3 else K["plankdk"]
        box(f"{name}Plank", (L, th, h), (0, 0, 0), pk, bevel=0.025)
        for sx in (-1, 1):
            for dz in (-h * 0.25, h * 0.25):
                if pried and sx > 0:
                    continue
                cyl(f"{name}Nail{sx}{dz:.2f}", 0.035, 0.03, (sx * (L / 2 - 0.35), -th / 2 - 0.012, dz), K["iron"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
        if pried:
            rtube(f"{name}BentNail", [(L / 2 - 0.35, th / 2, 0.0), (L / 2 - 0.35, th / 2 + 0.25, 0.02), (L / 2 - 0.3, th / 2 + 0.32, 0.1)], 0.018, K["iron"])
        if i in (3, 4):
            # the chalk sigil spans boards 3 and 4 (each carries its half)
            zz = (z + h) if i == 3 else z
            pts = []
            for k in range(25):
                a = k / 24 * 2 * PI
                pts.append((0.85 * math.cos(a), -th / 2 - 0.005, 0.85 * math.sin(a) + zz - zc))
            seg = [p for p in pts if (p[2] <= 0.0 if i == 4 else p[2] >= 0.0) or True]
            half = [p for p in pts if ((p[2] + zc) >= z - 1e-6 and (p[2] + zc) <= z + h + 1e-6)]
            if len(half) > 1:
                rtube(f"{name}Sigil", half, 0.022, K["chalkm"])
            for k, (a, b) in enumerate((((-0.6, -0.6), (0.6, 0.6)), ((-0.6, 0.6), (0.6, -0.6)))):
                pa = (a[0], -th / 2 - 0.005, a[1] + zz - zc)
                pb = (b[0], -th / 2 - 0.005, b[1] + zz - zc)
                # clip each stroke to this board's height band
                lo, hi = z - zc, z + h - zc
                def clip(p, q):
                    out = []
                    for tt in [i_ / 20 for i_ in range(21)]:
                        pp = (p[0] + (q[0] - p[0]) * tt, p[1], p[2] + (q[2] - p[2]) * tt)
                        if lo <= pp[2] <= hi:
                            out.append(pp)
                    return out
                c = clip(pa, pb)
                if len(c) > 1:
                    rtube(f"{name}Cross{k}", c, 0.022, K["chalkm"])
        mtx = T(0.0, yb - th / 2, zc)
        if pried:
            mtx = mtx @ T(-L / 2, 0, 0) @ RZ(-0.09) @ T(L / 2, 0, 0)
        _xform(s, mtx)
        z += h
    set_group("Main")
    # the crowbar against the wall, rubble at the foot
    rtube("Crowbar", [(3.85, -WY - 0.9, 0.04), (3.85, -WY - 0.04, 3.1)], 0.035, K["iron"])
    rtube("CrowClaw", [(3.85, -WY - 0.9, 0.04), (3.85, -WY - 1.05, 0.06), (3.85, -WY - 1.12, 0.16)], 0.03, K["iron"])
    for i in range(6):
        box(f"Rubble{i}", (rnd.uniform(0.15, 0.4), rnd.uniform(0.15, 0.35), rnd.uniform(0.1, 0.22)), (rnd.uniform(-3.8, 3.8), rnd.uniform(-1.6, -0.9), 0.08),
            st, bevel=0.03, rot=(0, 0, rnd.uniform(0, PI)))
    return _dims()


# ------------------------------------------------------------------ triggers

def sconce_lever(M):
    """A candle sconce that is a lever: a gothic iron backplate with a slotted quadrant, its scrolled arm (Lever0, with the
    candle; the flame Lever0Glow) pulls down 35 degrees about its pivot boss. Wall piece, the back on y = 0, the bottom at z = 0
    (mount it about 4.0 up)."""
    K = kit(M)
    iron, br = K["iron"], K["brass"]
    plate = [(-0.3, 0.0), (0.3, 0.0), (0.3, 1.1)] + B43.arch_xz(0.3, -0.3, 1.1, 0.45, n=8)[1:-1] + [(-0.3, 1.1)]
    prism("Plate", plate, -0.03, 0.06, iron, bevel=0.01)
    prism("PlateTrim", [(x * 0.85, 0.07 + z * 0.9) for x, z in plate], -0.065, 0.02, br)
    for k, z in enumerate((0.15, 1.3)):
        cyl(f"Screw{k}", 0.035, 0.03, (0, -0.08, z), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    # the quadrant slot the arm travels in, and the pivot boss
    zp = 0.8
    box("SlotGuideL", (0.04, 0.05, 0.55), (-0.09, -0.085, zp - 0.2), iron, bevel=0.005)
    box("SlotGuideR", (0.04, 0.05, 0.55), (0.09, -0.085, zp - 0.2), iron, bevel=0.005)
    cyl("PivotBoss", 0.1, 0.08, (0, -0.1, zp), br, rot=(PI / 2, 0, 0), verts=16, bevel=0.01)
    hinge = (0.0, -0.1, zp)
    opening("SconceLever", "Lever0", "lever", hinge, angle=35, axis=(1, 0, 0))
    rtube("Arm", [(0, -0.14, zp), (0, -0.4, zp + 0.02), (0, -0.62, zp + 0.18), (0, -0.66, zp + 0.42)], 0.035, iron, poly=False)
    hoop("Curl", (0, -0.34, zp - 0.12), 0.09, "X", iron, thick=0.018)
    lathe("Pan", [(0, 0), (0.17, 0), (0.18, 0.04), (0.06, 0.05), (0, 0.05)], br, seg=18, loc=(0, -0.66, zp + 0.42))
    lathe("Candle", [(0, 0), (0.055, 0), (0.058, 0.32), (0.045, 0.37), (0, 0.37)], K["wax"], seg=12, loc=(0, -0.66, zp + 0.47))
    lathe("Drip", [(0, 0), (0.08, 0), (0.06, 0.05), (0, 0.06)], K["wax"], seg=12, loc=(0, -0.66, zp + 0.47))
    opening("SconceLever", "Lever0Glow", "with", hinge, angle=35, axis=(1, 0, 0))
    flame("Flame", (0, -0.66, zp + 0.86), h=0.13)
    set_group("Main")
    return _dims()


def loose_brick(M):
    """A brick dado panel (4.0 x 3.0 on a limestone plinth under a moulded coping) with one loose brick (Brick0): its mortar
    cracked out, scratched round the edges, a crumb of mortar on the coping below; it pushes 0.45 into a hollow behind.
    Wall piece, the back on y = 0."""
    K = kit(M)
    rnd = random.Random(5352)
    bricks = [B40.mossy(flat(f"LooseBrick{k}", c, 0.88, wear=0.25, dirt=0.9), 0.15, scale=2.5, low=0.4) for k, c in
              enumerate(((0.15, 0.05, 0.035), (0.19, 0.065, 0.045), (0.11, 0.035, 0.032), (0.13, 0.055, 0.045)))]
    for b in bricks:
        B24._bump(b, B40._noise(b, 30.0), 0.02, 0.5)
    W, H = 4.0, 3.0
    z0 = 0.4
    bw, bh, mj = 0.5, 0.25, 0.03
    box("Mortar", (W, 0.06, H), (0, -0.03, z0 + H / 2), K["limedk"], bevel=0.0)
    box("Plinth", (W + 0.3, 0.34, z0), (0, -0.17, z0 / 2), K["lime"], bevel=0.03)
    box("Coping", (W + 0.4, 0.42, 0.22), (0, -0.21, z0 + H + 0.11), K["lime"], bevel=0.04)
    rows = int(H / bh)
    loose = (5, 4)
    for r in range(rows):
        off = 0.0 if r % 2 == 0 else bw / 2
        x = -W / 2 - off
        c = 0
        while x < W / 2 - 1e-6:
            xa, xb = max(x, -W / 2), min(x + bw, W / 2)
            if xb - xa > 0.05:
                cx = (xa + xb) / 2
                cz = z0 + r * bh + bh / 2
                if (r, c) == loose:
                    lb = (cx, cz, xb - xa - mj)
                else:
                    box(f"Brick{r}_{c}", (xb - xa - mj, 0.24, bh - mj), (cx, -0.06 - 0.12 - rnd.uniform(0, 0.012), cz), bricks[rnd.randrange(4)],
                        bevel=0.02, rot=(rnd.uniform(-0.01, 0.01), 0, rnd.uniform(-0.008, 0.008)))
                c += 1
            x += bw
    cx, cz, w = lb
    # the hollow behind the loose brick and scratches round it
    box("Hollow", (w + 0.02, 0.02, bh - mj + 0.02), (cx, -0.065, cz), K["gloom"], bevel=0.0)
    for k in range(5):
        a = rnd.uniform(-0.4, 0.4)
        rtube(f"Scratch{k}", [(cx - w / 2 - 0.06 + k * 0.03, -0.302, cz + bh / 2 + 0.01), (cx - w / 2 - 0.02 + k * 0.035, -0.302, cz + bh / 2 + 0.07)], 0.006,
              K["chalkm"])
    opening("LooseBrick", "Brick0", "press", (cx, -0.06 - 0.12 - 0.05, cz), slide=(0, 0.45, 0))
    box("Loose", (w, 0.24, bh - mj - 0.01), (cx, -0.06 - 0.12 - 0.05, cz), bricks[1], bevel=0.02, rot=(0, 0, 0.02))
    set_group("Main")
    # mortar crumbs on the plinth's top below
    for k in range(5):
        sphere(f"Crumb{k}", rnd.uniform(0.02, 0.035), (cx + rnd.uniform(-0.4, 0.4), -0.3 + rnd.uniform(-0.02, 0.02), z0 + 0.012), K["limedk"], seg=6, rings=3,
               scale=(1, 1, 0.6))
    return _dims()


def tilting_bust(M):
    """A bronze bust of an invented founding architect (AEDIFICATOR) on a fluted black marble pedestal: slick hair, a high
    collar and a frock coat, a gilt compass medallion on his chest, a mantle on one shoulder. The bust (Bust0) tilts back 22
    degrees on a hidden hinge at the back edge of its socle: the trigger."""
    K = kit(M)
    K41 = B41.kit(M)
    br, dk = K41["bronze"], K41["bronzedk"]
    mb = K41["obsidian"]
    gl = K["gilt"]
    # the pedestal (Main): base, fluted shaft, capital, a gilt plaque
    lathe("PedBase", [(0, 0), (0.95, 0), (0.95, 0.18), (0.82, 0.26), (0.78, 0.4), (0.62, 0.48), (0.6, 0.55), (0, 0.55)], mb, seg=32)
    lathe("PedShaft", [(0, 0.55), (0.5, 0.55), (0.46, 3.2), (0, 3.2)], mb, seg=48, flute=(16, 0.05))
    lathe("PedCap", [(0, 3.2), (0.56, 3.2), (0.6, 3.3), (0.78, 3.42), (0.82, 3.55), (0.82, 3.62), (0, 3.62)], mb, seg=32)
    box("Plaque", (0.9, 0.04, 0.3), (0, -0.48, 2.5), gl, bevel=0.01, rot=(0.02, 0, 0))
    label("PlaqueTxt", "AEDIFICATOR", K["ink"], 0, -0.5, 2.5, 0.8, 0.15, depth=0.008)
    zt = 3.62
    # the bust: socle and figure, all on the hinge at the socle's back bottom edge
    opening("TiltingBust", "Bust0", "tilt", (0.0, 0.55, zt), angle=-22, axis=(1, 0, 0))
    s = _mark()
    h = B41._socle("S", K41, mb, gl, w=1.0, h=0.55)
    sc = 0.62
    f = B41.R.Fig(base=(0, 0, h - 2.0 * sc), scale=sc, pose={"neck": (-6, 0, -12)}, mats=br, parts=("head", "torso"), face="stern", dark=dk)
    B41.hair_sculpt(f, br, "slick", seed=21)
    B41.fitted_torso(f, br, trim=gl, buttons=4, lapels=True, collar=True, name="Coat")

    def medal():
        hoop("MedalRing", (0.32, -0.62, 3.4), 0.16, "Y", gl, thick=0.022)
        for sx in (-1, 1):
            rtube(f"Compass{sx}", [(0.32, -0.64, 3.52), (0.32 + sx * 0.1, -0.64, 3.28)], 0.014, gl)
    f.build("torso", medal)
    B41.mantle(f, dk, open_deg=60, z0=3.98, z1=2.3, folds=6, amp=0.06, name="Mantle", seed=23)
    B41._bust_cut(f, br)
    _xform(s, T(0, 0, zt))
    set_group("Main")
    return _dims()


BUILDERS = {
    "VentWallLow": vent_wall_low,
    "VentWallHigh": vent_wall_high,
    "VentCeiling": vent_ceiling,
    "VentFloor": vent_floor,
    "DuctStraight": duct_straight,
    "DuctCorner": duct_corner,
    "DuctTee": duct_tee,
    "DuctRiser": duct_riser,
    "DuctEndCap": duct_end_cap,
    "DuctDamaged": duct_damaged,
    "BookcaseSecretDoor": bookcase_secret_door,
    "FireplacePassage": fireplace_passage,
    "TapestryPassage": tapestry_passage,
    "SlidingWallPanel": sliding_wall_panel,
    "TrapdoorLadder": trapdoor_ladder,
    "SecretSpiralStair": secret_spiral_stair,
    "TunnelStraight": tunnel_straight,
    "TunnelCurve": tunnel_curve,
    "TunnelJunction": tunnel_junction,
    "TunnelSteps": tunnel_steps,
    "TunnelDeadEnd": tunnel_dead_end,
    "StageCrawlspace": stage_crawlspace,
    "BoardedPassage": boarded_passage,
    "SconceLever": sconce_lever,
    "LooseBrick": loose_brick,
    "TiltingBust": tilting_bust,
}


def _wrap(fn):
    def w(M):
        d = fn(M)
        _write_rig()
        return d
    return w


TILES = {}
for _n in ("TunnelStraight", "TunnelCurve", "TunnelJunction", "TunnelSteps", "TunnelDeadEnd"):
    TILES[f"{_n}_Wall"] = ("NH_CastleStone", 8.0)
for _n in ("TunnelStraight", "TunnelCurve", "TunnelJunction", "TunnelDeadEnd"):
    TILES[f"{_n}_Floor"] = ("NH_MossyPaving", 8.0)
for _p in ("Wall", "UpperWall", "HeadWall"):
    TILES[f"SecretSpiralStair_{_p}"] = ("NH_CastleStone", 8.0)
for _n in ("VentFloor", "TrapdoorLadder", "BoardedPassage"):
    TILES[f"{_n}_Wall"] = ("NH_CastleStone", 8.0)
P.TILED.update(TILES)
P.BUILD.update({k: _wrap(v) for k, v in BUILDERS.items()})
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"SconceLever": 1.3, "LooseBrick": 1.15, "DuctEndCap": 1.2})
