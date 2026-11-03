"""Props batch 9 (2026-11-03): building support pillars for nh_props.py: dark weathered castle stone, moss in the
joints, brass and wrought iron, candlelight and carved detail, each a different shape. All stand 12 studs, floor to
ceiling. Original designs with an old magical-school feel.

  PillarCluster   a clustered gothic pier: eight shafts round a core on a stepped, moss-edged base, a carved band of
                  quatrefoils at mid height, and a stiff-leaf capital with four grotesque heads under the abacus
  PillarOctagon   an octagonal pier with blind tracery on every face, brass bands, four stone ravens perched under
                  the capital and a wrought-iron candle bracket (Glow: flame)
  PillarTwisted   a twisted column in wine-dark marble on a base guarded by four crouching grotesques, with a
                  crocketed capital
  PillarFanVault  a round column on an octagonal base whose stiff-leaf capital springs into sixteen ribs fanning to
                  the ceiling, with liernes and carved rosette bosses where they cross
  PillarNiche     a square pier with a deep canopied niche (crocketed hood, finial) holding a brass candlestick
                  (Glow: flame), a carved shield, ringed corner shafts, and an iron cramp across an old crack
  PillarMarble    a polished black marble column with bone veins, gilt bands, a ring of gilt quatrefoils and a
                  gilt stiff-leaf capital
  PillarIron      a fluted cast-iron column with riveted collars, a foundry plate, and four scrolled brackets with
                  cast tracery in their spandrels
  Pilaster        a wall pilaster: a traceried blind arch, a crest with a shield, and an iron lantern on a scrolled
                  bracket (Glow: flame; a wall piece: the back sits at +Y)

Front faces -Y, Z is up, the origin is at the bottom centre.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _pinnacle, _arch_loop, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, leaf, prism, _mark, _xform, _dims, flat
from nh_props_batch5 import marble


# ------------------------------------------------------------------ materials

def stones():
    """Dark weathered castle stone, and a darker course for plinths and mouldings."""
    return (material("CastleStone", "NH_Limestone", tint=(0.36, 0.35, 0.335), scale=0.3, wear=0.26, dirt=1.0),
            material("CastleStoneDark", "NH_Limestone", tint=(0.21, 0.205, 0.2), scale=0.3, wear=0.2, dirt=1.0))


def moss_mat():
    return flat("Moss", (0.022, 0.045, 0.016), 0.92, dirt=0.6)


def crack_mat():
    return flat("Crack", (0.012, 0.011, 0.011), 0.95, dirt=0.2)


def wax_mat():
    return flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)


# ------------------------------------------------------------------ carving helpers

def twist(name, z0, z1, r, mat, lobes=4, depth=0.24, turns=2.0, seg=40, rings=110, taper=0.0):
    """A twisted column: a lobed section turning `turns` times between z0 and z1, capped at both ends."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for j in range(rings + 1):
        t = j / rings
        z = z0 + (z1 - z0) * t
        ph = turns * 2 * math.pi * t
        r0 = r * (1 - taper * t)
        row = []
        for i in range(seg):
            a = i / seg * 2 * math.pi
            rr = r0 * (1 - depth * (0.5 + 0.5 * math.cos(lobes * (a - ph))))
            row.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z)))
        rows.append(row)
    for A, B in zip(rows, rows[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def oct_band(name, r, z, h, mat, rot=math.pi / 8):
    """A flat band round an octagonal shaft."""
    s = _mark()
    lathe(name, [(r, z - h / 2), (r + 0.04, z - h / 2 + 0.02), (r + 0.04, z + h / 2 - 0.02), (r, z + h / 2)], mat, seg=8)
    _xform(s, Matrix.Rotation(rot, 4, "Z"))


def _base_mould(prefix, r, z, mat, seg=32):
    """Attic-style base moulding: a torus, a hollow and a smaller torus, from z up. Returns its top."""
    lathe(prefix, [(0, z), (r, z), (r + 0.05, z + 0.08), (r, z + 0.16), (r * 0.86, z + 0.22), (r * 0.84, z + 0.3), (r * 0.9, z + 0.36),
                   (r * 0.82, z + 0.44), (0, z + 0.44)], mat, seg=seg)
    return z + 0.44


def foil(prefix, cx, y, cz, r, mat, lobes=4, thick=0.02, n=8, centre=True):
    """A light cusped foil (quatrefoil, trefoil) carved on a face at y, facing -Y."""
    if centre:
        tube(prefix, circle_pts(cx, y, cz, r, "Y", n), thick, mat, closed=True, square=True, poly=True)
    for k in range(lobes):
        a = math.pi / 2 + k * 2 * math.pi / lobes
        tube(f"{prefix}L{k}", circle_pts(cx + math.cos(a) * r * 0.55, y, cz + math.sin(a) * r * 0.55, r * 0.44, "Y", n), thick * 0.8, mat,
             closed=True, square=True, poly=True)


def tracery(prefix, cx, y, hw, z0, zs, za, mat, recess=None, thick=0.022):
    """Blind tracery on a face at y (facing -Y): a pointed arch with a mullion, two lancets and a trefoil in the head,
    over a dark recess so it reads as carved depth."""
    if recess is not None:
        # the recess as two simple convex pieces (a panel and the pointed head), stood a little proud of the face
        yr = y - 0.012
        box(f"{prefix}Recess", (2 * hw, 0.012, zs - z0), (cx, yr, (z0 + zs) / 2), recess, bevel=0.0, segments=1)
        headpts = [(x, z) for x, _, z in _arch_loop(cx, 0, hw, z0, zs, za) if z >= zs - 1e-6]
        prism(f"{prefix}RecessHead", headpts, yr, 0.012, recess)
        y -= 0.018
    outer = _arch_loop(cx, y - thick, hw, z0, zs, za)
    tube(f"{prefix}Arch", outer, thick, mat, square=True, closed=True, poly=True)
    tube(f"{prefix}Mullion", [(cx, y - thick, z0), (cx, y - thick, zs + (za - zs) * 0.2)], thick * 0.8, mat, square=True, poly=True)
    for sx in (-1, 1):
        lh = hw / 2 - thick * 0.6
        tube(f"{prefix}Lancet{sx}", _arch_loop(cx + sx * hw / 2, y - thick, lh, z0, zs, zs + (za - zs) * 0.45), thick * 0.75, mat, square=True,
             closed=True, poly=True)
    foil(f"{prefix}Foil", cx, y - thick, zs + (za - zs) * 0.66, hw * 0.34, mat, lobes=3, thick=thick * 0.7, centre=False)


def stiff_leaf(prefix, r, z, n, h, mat, phase=0.0, pitch=78, droop=0.5, width=0.22, knob=0.08, kseg=(8, 5)):
    """A ring of stiff-leaf foliage: leaves rising round a bell and curling over into a knob at each tip."""
    p = math.radians(pitch)
    for k in range(n):
        a = k / n * 2 * math.pi + phase
        c, s_ = math.cos(a), math.sin(a)
        leaf(f"{prefix}{k}", (c * r, s_ * r, z), a, p, h, width, droop, mat, n=8, fold=0.45, thick=0.04)
        ro = r + h * math.cos(p) + knob * 0.6
        sphere(f"{prefix}Knob{k}", knob, (c * ro, s_ * ro, z + h * (math.sin(p) - droop) + knob * 0.4), mat, seg=kseg[0], rings=kseg[1], scale=(1, 1, 0.8))


def grotesque(prefix, pos, face, s, mat, dark):
    """A small carved grotesque head with a hunched body, horns and paws, looking out toward angle `face`."""
    m = _mark()
    sphere(f"{prefix}Hunch", 0.24 * s, (0, 0.12 * s, -0.18 * s), mat, seg=12, rings=6, scale=(1, 0.9, 0.8))
    sphere(f"{prefix}Head", 0.2 * s, (0, -0.02 * s, 0), mat, seg=12, rings=7, scale=(1, 0.92, 0.95))
    box(f"{prefix}Brow", (0.34 * s, 0.1 * s, 0.07 * s), (0, -0.16 * s, 0.07 * s), mat, bevel=0.01 * s, rot=(0.25, 0, 0))
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.04 * s, (sx * 0.075 * s, -0.19 * s, 0.02 * s), dark, seg=6, rings=4)
        cone(f"{prefix}Horn{sx}", 0.05 * s, 0.0, 0.24 * s, (sx * 0.13 * s, 0.02 * s, 0.2 * s), mat, verts=6, rot=(0.3, sx * 0.55, 0))
        sphere(f"{prefix}Ear{sx}", 0.06 * s, (sx * 0.2 * s, 0.0, 0.05 * s), mat, seg=6, rings=4, scale=(0.4, 1, 1.4))
        sphere(f"{prefix}Paw{sx}", 0.075 * s, (sx * 0.12 * s, -0.17 * s, -0.24 * s), mat, seg=8, rings=4, scale=(1, 1.3, 0.7))
        cone(f"{prefix}Fang{sx}", 0.018 * s, 0.0, 0.06 * s, (sx * 0.04 * s, -0.27 * s, -0.135 * s), mat, verts=4, rot=(math.pi, 0, 0))
    sphere(f"{prefix}Snout", 0.1 * s, (0, -0.21 * s, -0.06 * s), mat, seg=10, rings=5, scale=(1.2, 1.0, 0.8))
    box(f"{prefix}Mouth", (0.14 * s, 0.04 * s, 0.03 * s), (0, -0.28 * s, -0.11 * s), dark, bevel=0.0, segments=1)
    _xform(m, Matrix.Translation(pos) @ Matrix.Rotation(face + math.pi / 2, 4, "Z"))


def raven(prefix, pos, face, s, mat, dark):
    """A small perched raven, looking out toward angle `face`; feet at pos."""
    m = _mark()
    sphere(f"{prefix}Body", 1.0, (0, 0.03 * s, 0.14 * s), mat, seg=12, rings=6, scale=(0.1 * s, 0.17 * s, 0.11 * s))
    sphere(f"{prefix}Head", 0.07 * s, (0, -0.13 * s, 0.25 * s), mat, seg=10, rings=5)
    cone(f"{prefix}Beak", 0.03 * s, 0.0, 0.12 * s, (0, -0.24 * s, 0.24 * s), dark, verts=6, rot=(math.pi / 2 + 0.25, 0, 0))
    for sx in (-1, 1):
        sphere(f"{prefix}Wing{sx}", 1.0, (sx * 0.08 * s, 0.06 * s, 0.15 * s), mat, seg=8, rings=4, scale=(0.03 * s, 0.17 * s, 0.08 * s))
        sphere(f"{prefix}Eye{sx}", 0.012 * s, (sx * 0.045 * s, -0.17 * s, 0.27 * s), dark, seg=6, rings=3)
        box(f"{prefix}Foot{sx}", (0.03 * s, 0.08 * s, 0.05 * s), (sx * 0.04 * s, -0.02 * s, 0.025 * s), dark, bevel=0.004 * s)
    box(f"{prefix}Tail", (0.09 * s, 0.18 * s, 0.02 * s), (0, 0.22 * s, 0.07 * s), mat, bevel=0.005 * s, rot=(-0.45, 0, 0))
    _xform(m, Matrix.Translation(pos) @ Matrix.Rotation(face + math.pi / 2, 4, "Z"))


def rosette(prefix, pos, normal, r, mat):
    """A carved rosette boss: a domed centre ringed by petals, facing along `normal`."""
    m = _mark()
    sphere(f"{prefix}Centre", r * 0.45, (0, 0, r * 0.1), mat, seg=8, rings=4, scale=(1, 1, 0.7))
    for k in range(6):
        a = k / 6 * 2 * math.pi
        sphere(f"{prefix}Petal{k}", r * 0.32, (math.cos(a) * r * 0.62, math.sin(a) * r * 0.62, 0), mat, seg=6, rings=3, scale=(1, 0.7, 0.45))
    from mathutils import Vector
    rot = Vector((0, 0, 1)).rotation_difference(Vector(normal).normalized()).to_matrix().to_4x4()
    _xform(m, Matrix.Translation(pos) @ rot)


def moss(prefix, pts, mat, rnd, size=0.12):
    """Flat clumps of moss tucked into joints."""
    for k, (x, y, z) in enumerate(pts):
        for j in range(2):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size * rnd.uniform(0.6, 1.1),
                                                  location=(x + rnd.uniform(-0.07, 0.07), y + rnd.uniform(-0.07, 0.07), z + rnd.uniform(-0.01, 0.02)))
            o = bpy.context.active_object
            o.name = f"{prefix}{k}_{j}"
            for v in o.data.vertices:
                v.co *= 1 + rnd.uniform(-0.2, 0.15)
            o.scale = (1.4, 1.4, 0.45)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            for f in o.data.polygons:
                f.use_smooth = True
            _finish(o, mat, 0)


def square_edge(half, z, n, rnd, inset=0.02):
    """Points along the top edges of a square block (for moss)."""
    pts = []
    for _ in range(n):
        side = rnd.randrange(4)
        t = rnd.uniform(-half * 0.9, half * 0.9)
        x, y = [(t, -half + inset), (t, half - inset), (-half + inset, t), (half - inset, t)][side]
        pts.append((x, y, z))
    return pts


def crack(prefix, pts, mat, r=0.012):
    tube(prefix, pts, r, mat, poly=True)


def face_crack(prefix, x0, z0, x1, z1, y, mat, rnd, steps=6):
    """A jagged crack on a face at y."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        j = 0 if i in (0, steps) else rnd.uniform(-0.06, 0.06)
        pts.append((x0 + (x1 - x0) * t + j, y, z0 + (z1 - z0) * t + rnd.uniform(-0.03, 0.03)))
    crack(prefix, pts, mat)


def candle(prefix, x, y, z, h, wax, r=0.055):
    """A pillar candle with a drip, standing at z; returns the wick top."""
    cyl(f"{prefix}Wax", r, h, (x, y, z + h / 2), wax, verts=12, bevel=0.01)
    sphere(f"{prefix}Drip", r * 0.42, (x + r, y, z + h - 0.08), wax, seg=6, rings=4, scale=(1, 1, 2.6))
    tube(f"{prefix}Wick", [(x, y, z + h), (x, y, z + h + 0.04)], 0.008, flat("Wick", (0.02, 0.02, 0.02), 0.8), poly=True)
    return z + h


# ================================================================== clustered pier
def pillar_cluster(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(91)
    box("Plinth", (2.7, 2.7, 0.3), (0, 0, 0.15), dk, bevel=0.04)
    box("Plinth2", (2.5, 2.5, 0.25), (0, 0, 0.425), st, bevel=0.07)
    top = _base_mould("Base", 1.15, 0.55, st, seg=40)
    cyl("Core", 0.58, 10.95 - top, (0, 0, (top + 10.95) / 2), st, verts=24, bevel=0.0)
    for k in range(8):
        a = k / 8 * 2 * math.pi + math.pi / 8
        big = k % 2 == 0
        r, d = (0.21, 0.66) if big else (0.13, 0.7)
        x, y = math.cos(a) * d, math.sin(a) * d
        cyl(f"Shaft{k}", r, 10.9 - top - 0.3, (x, y, (top + 10.9) / 2), st, verts=14, bevel=0.0)
        lathe(f"ShaftBase{k}", [(0, top), (r + 0.07, top), (r + 0.08, top + 0.1), (r + 0.02, top + 0.2), (0, top + 0.2)], dk, seg=14, loc=(x, y, 0))
    # a carved band at mid height: rolls above and below, a frieze of quatrefoils between the big shafts
    lathe("Band", [(0, 5.5), (0.93, 5.5), (0.99, 5.56), (0.97, 5.62), (0.97, 5.98), (0.99, 6.04), (0.93, 6.1), (0, 6.1)], dk, seg=40)
    for k in range(8):
        m = _mark()
        foil(f"BandFoil{k}", 0, -0.985, 5.8, 0.12, st)
        _xform(m, Matrix.Rotation(k / 8 * 2 * math.pi, 4, "Z"))
    # a stiff-leaf capital with grotesque heads under the corners of the abacus
    lathe("Bell", [(0, 10.85), (0.86, 10.85), (0.88, 11.0), (1.0, 11.25), (1.16, 11.4), (1.2, 11.48), (0, 11.48)], st, seg=40)
    hoop("Necking", (0, 0, 10.9), 0.88, "Z", dk, thick=0.06)
    stiff_leaf("LeafA", 0.86, 10.88, 10, 0.62, st, pitch=80, droop=0.42)
    stiff_leaf("LeafB", 0.92, 11.06, 10, 0.4, st, phase=math.pi / 10, pitch=70, droop=0.35, width=0.18, knob=0.065)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        grotesque(f"Head{k}", (math.cos(a) * 1.22, math.sin(a) * 1.22, 11.26), a, 0.8, st, ck)
    box("Abacus", (2.5, 2.5, 0.22), (0, 0, 11.59), dk, bevel=0.04)
    box("Impost", (2.3, 2.3, 0.3), (0, 0, 11.85), st, bevel=0.03)
    # moss in the base joints, an old crack in the plinth
    moss("Moss", square_edge(1.25, 0.55, 9, rnd) + square_edge(1.35, 0.3, 5, rnd), mo, rnd)
    face_crack("Crack", -0.7, 0.04, -0.35, 0.52, -1.352, ck, rnd)
    return _dims()


# ================================================================== octagonal pier
def pillar_octagon(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(92)
    rot = math.pi / 8                       # a flat face to the front
    box("Plinth", (2.5, 2.5, 0.35), (0, 0, 0.175), dk, bevel=0.04)
    s = _mark()
    lathe("Base", [(0, 0.35), (1.18, 0.35), (1.18, 0.6), (1.05, 0.7), (1.05, 0.82), (0.9, 0.92), (0, 0.92)], st, seg=8)
    lathe("Shaft", [(0, 0.9), (0.84, 0.9), (0.84, 10.9), (0, 10.9)], st, seg=8)
    lathe("Capital", [(0, 10.88), (0.84, 10.88), (0.9, 11.0), (1.05, 11.25), (1.15, 11.45), (1.15, 11.55), (0, 11.55)], st, seg=8)
    _xform(s, Matrix.Rotation(rot, 4, "Z"))
    box("Impost", (2.4, 2.4, 0.45), (0, 0, 11.775), dk, bevel=0.04)
    for z in (2.6, 6.2, 9.6):
        oct_band(f"Band{z}", 0.84, z, 0.18, M["brass"], rot=rot)
    # blind tracery on all eight faces, in two registers (the front's upper register carries the candle bracket)
    ap = 0.84 * math.cos(math.pi / 8)
    for k in range(8):
        for zb, zt in ((2.85, 5.95), (6.45, 9.35)):
            if k == 0 and zb > 6:
                continue
            m = _mark()
            tracery(f"Tr{k}{zb}", 0, -ap, 0.24, zb + 0.15, zt - 1.0, zt - 0.15, st, recess=dk, thick=0.03)
            _xform(m, Matrix.Rotation(k * math.pi / 4, 4, "Z"))
    # four stone ravens perched on corbels under the capital, on the diagonal faces
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        m = _mark()
        box(f"Perch{k}", (0.32, 0.36, 0.1), (0, -0.95, 10.95), dk, bevel=0.02)
        _xform(m, Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        raven(f"Raven{k}", (c * 1.0, s_ * 1.0, 11.0), a, 1.0, dk, ck)
    # a wrought-iron candle bracket on the front face: an arched back plate, a scrolled arm, a brass drip pan
    y0 = -ap
    prism("BracketPlate", [(x, z) for x, _, z in _arch_loop(0, 0, 0.16, 7.25, 7.75, 8.0)], y0 - 0.02, 0.04, M["iron"], bevel=0.008)
    for zz in (7.35, 7.85):
        sphere(f"BracketRivet{zz}", 0.025, (0, y0 - 0.045, zz), M["brass"], seg=6, rings=3)
    tube("BracketArm", [(0, y0 - 0.04, 7.45), (0, y0 - 0.3, 7.5), (0, y0 - 0.5, 7.7)], 0.03, M["iron"], square=True)
    tube("BracketCurl", [(0, y0 - 0.04, 7.8), (0, y0 - 0.2, 7.85), (0, y0 - 0.3, 7.72), (0, y0 - 0.22, 7.62)], 0.018, M["iron"])
    tube("BracketDrop", [(0, y0 - 0.3, 7.5), (0, y0 - 0.33, 7.3), (0, y0 - 0.26, 7.22)], 0.016, M["iron"])
    wax = wax_mat()
    cyl("Pan", 0.15, 0.03, (0, y0 - 0.5, 7.72), M["brass"], verts=16, bevel=0.008)
    hoop("PanRim", (0, y0 - 0.5, 7.74), 0.15, "Z", M["brass"], thick=0.012)
    cyl("Socket", 0.07, 0.1, (0, y0 - 0.5, 7.78), M["brass"], verts=12, bevel=0.01)
    tip = candle("Candle", 0, y0 - 0.5, 7.82, 0.3, wax)
    moss("Moss", square_edge(1.2, 0.35, 10, rnd), mo, rnd)
    face_crack("Crack", 0.5, 0.36, 0.25, 1.6, -ap - 0.005, ck, rnd)
    set_group("Glow")
    flame("Flame", (0, y0 - 0.5, tip - 0.02), h=0.15)
    set_group("Main")
    return _dims()


# ================================================================== twisted column
def pillar_twisted(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(93)
    wine = marble("MarbleWine", base=(0.05, 0.012, 0.016), vein=(0.32, 0.12, 0.11), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    box("Plinth", (2.4, 2.4, 0.5), (0, 0, 0.25), dk, bevel=0.04)
    top = _base_mould("Base", 1.0, 0.5, st, seg=40)
    lathe("Foot", [(0, top), (0.68, top), (0.62, top + 0.12), (0, top + 0.12)], st, seg=32)
    hoop("FootBrass", (0, 0, top + 0.12), 0.62, "Z", M["brass"], thick=0.03)
    twist("Shaft", top + 0.1, 10.6, 0.62, wine, lobes=4, depth=0.26, turns=2.5, taper=0.06, seg=32, rings=90)
    # four crouching grotesques guard the corners of the plinth
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        grotesque(f"Guard{k}", (math.cos(a) * 1.3, math.sin(a) * 1.3, 0.5 + 0.48), a, 1.3, st, ck)
    # a crocketed capital
    lathe("Neck", [(0, 10.55), (0.6, 10.55), (0.62, 10.7), (0, 10.7)], st, seg=32)
    hoop("NeckBead", (0, 0, 10.72), 0.6, "Z", M["brass"], thick=0.04)
    lathe("Capital", [(0, 10.7), (0.6, 10.7), (0.75, 10.95), (0.95, 11.2), (1.1, 11.35), (0, 11.35)], st, seg=40)
    stiff_leaf("Crocket", 0.66, 10.78, 10, 0.34, st, pitch=40, droop=0.25, width=0.15, knob=0.07, kseg=(6, 4))
    stiff_leaf("CrocketB", 0.9, 11.06, 10, 0.24, st, phase=math.pi / 10, pitch=30, droop=0.2, width=0.13, knob=0.06, kseg=(6, 4))
    box("Abacus", (2.3, 2.3, 0.25), (0, 0, 11.48), dk, bevel=0.04)
    box("Impost", (2.1, 2.1, 0.4), (0, 0, 11.8), st, bevel=0.03)
    moss("Moss", square_edge(1.15, 0.5, 8, rnd), mo, rnd)
    return _dims()


# ================================================================== fan-vault column
def pillar_fan_vault(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(94)
    box("Plinth", (2.4, 2.4, 0.4), (0, 0, 0.2), dk, bevel=0.04)
    s = _mark()
    lathe("BaseOct", [(0, 0.4), (1.05, 0.4), (1.05, 0.6), (0, 0.6)], st, seg=8)
    _xform(s, Matrix.Rotation(math.pi / 8, 4, "Z"))
    top = _base_mould("Base", 0.78, 0.6, st, seg=36)
    lathe("Shaft", [(0, top), (0.55, top), (0.53, 4.5), (0.5, 8.2), (0, 8.2)], st, seg=36)
    # an annulet at mid height with a ring of small foils
    lathe("Annulet", [(0, 4.42), (0.56, 4.42), (0.6, 4.48), (0.6, 4.72), (0.56, 4.78), (0, 4.78)], dk, seg=36)
    for k in range(8):
        m = _mark()
        foil(f"AnnFoil{k}", 0, -0.605, 4.6, 0.08, st, thick=0.014)
        _xform(m, Matrix.Rotation(k / 8 * 2 * math.pi, 4, "Z"))
    # a stiff-leaf capital where the ribs spring
    lathe("Capital", [(0, 8.15), (0.5, 8.15), (0.62, 8.3), (0.62, 8.42), (0.55, 8.5), (0, 8.5)], dk, seg=36)
    stiff_leaf("CapLeaf", 0.5, 8.0, 12, 0.36, st, pitch=72, droop=0.3, width=0.14, knob=0.055, kseg=(6, 4))
    # the conoid: a solid fan of stone flaring from the capital to the ceiling, ribbed, with liernes and bosses
    prof = [(0.55, 8.45), (0.66, 9.3), (0.95, 10.15), (1.45, 10.9), (2.1, 11.45), (2.75, 11.85), (3.0, 12.0)]
    lathe("Fan", [(0, 8.45)] + prof + [(0, 12.0)], st, seg=64)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        c, s_ = math.cos(a), math.sin(a)
        pts = [(c * (r + 0.035), s_ * (r + 0.035), z - 0.035) for r, z in prof]    # just proud of the fan's underside
        tube(f"Rib{k}", pts, 0.06 if k % 2 == 0 else 0.042, dk, square=True)
    for r, z in ((0.95, 10.15), (1.45, 10.9), (2.1, 11.45)):
        tube(f"Lierne{z}", circle_pts(0, 0, z - 0.04, r + 0.045, "Z", 48), 0.045, dk, closed=True, square=True, poly=True)
    # carved rosette bosses where the main ribs cross the middle and outer liernes
    for k in range(8):
        a = k / 8 * 2 * math.pi
        c, s_ = math.cos(a), math.sin(a)
        rosette(f"Boss{k}", (c * 1.5, s_ * 1.5, 10.84), (c * 0.75, s_ * 0.75, -0.66), 0.13, dk)
        rosette(f"BossOut{k}", (c * 2.15, s_ * 2.15, 11.4), (c * 0.6, s_ * 0.6, -0.8), 0.11, dk)
    tube("Rim", circle_pts(0, 0, 11.97, 3.0, "Z", 64), 0.05, dk, closed=True, square=True, poly=True)
    moss("Moss", square_edge(1.15, 0.4, 9, rnd), mo, rnd)
    face_crack("Crack", 0.3, 0.02, 0.7, 0.38, -1.202, ck, rnd)
    return _dims()


# ================================================================== niche pier
def pillar_niche(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(95)
    W, D = 2.0, 2.0
    box("Plinth", (2.6, 2.6, 0.5), (0, 0, 0.25), dk, bevel=0.04)
    box("Lower", (2.3, 2.3, 2.5), (0, 0, 0.5 + 1.25), st, bevel=0.03)
    s = _mark()
    cone("Weathering", 2.3 * 0.7071, W * 0.7071, 0.4, (0, 0, 3.2), st, verts=4)
    _xform(s, Matrix.Rotation(math.pi / 4, 4, "Z"))
    # a carved shield on the lower block, and an old crack held by an iron cramp
    yl = -1.15
    half = [(0.0, 2.55), (0.42, 2.55)]
    for i in range(9):
        t = i / 8
        half.append((0.42 * math.cos(t * math.pi / 2) ** 0.9, 2.2 - 0.7 * math.sin(t * math.pi / 2) ** 1.3))
    half[-1] = (0.0, half[-1][1])
    shield = half + [(-x, z) for x, z in reversed(half[1:-1])]
    prism("Shield", shield, yl - 0.03, 0.06, dk, bevel=0.01)
    foil("ShieldFoil", 0, yl - 0.065, 2.05, 0.13, st, thick=0.018)
    tube("ShieldBand", [(-0.4, yl - 0.065, 2.4), (0.4, yl - 0.065, 2.4)], 0.02, st, square=True, poly=True)
    face_crack("Crack", -0.95, 0.55, -0.5, 1.75, yl - 0.005, ck, rnd, steps=7)
    box("Cramp", (0.5, 0.04, 0.09), (-0.72, yl - 0.02, 1.15), M["iron"], bevel=0.01)
    for sx in (-1, 1):
        sphere(f"CrampPin{sx}", 0.03, (-0.72 + sx * 0.2, yl - 0.045, 1.15), M["iron"], seg=6, rings=3)
    # the upper pier with a deep pointed niche
    z0, z1 = 3.4, 11.3
    zb, zs, za = 4.7, 6.6, 7.55            # niche sill, arch spring, apex
    nw = 0.46                              # half the niche width
    dep = 0.62                             # niche depth
    yf = -D / 2
    box("PierBack", (W, D - dep, z1 - z0), (0, yf + dep + (D - dep) / 2, (z0 + z1) / 2), st, bevel=0.02)
    for sx in (-1, 1):
        box(f"PierSide{sx}", ((W / 2 - nw), dep, z1 - z0), (sx * (nw + (W / 2 - nw) / 2), yf + dep / 2, (z0 + z1) / 2), st, bevel=0.02)
    box("PierBelow", (2 * nw, dep, zb - z0), (0, yf + dep / 2, (z0 + zb) / 2), st, bevel=0.015)
    arch = [(x, z) for x, _, z in _arch_loop(0, 0, nw, zb, zs, za)]
    head = [(-nw, z1)] + arch[1:-1] + [(nw, z1)]
    prism("PierAbove", head, yf + dep / 2, dep, st, bevel=0.0)
    box("NicheBack", (2 * nw, 0.05, za - zb + 0.1), (0, yf + dep - 0.02, (zb + za) / 2), dk, bevel=0.0, segments=1)
    box("Sill", (2 * nw + 0.3, dep + 0.2, 0.12), (0, yf + dep / 2 - 0.1, zb + 0.06), dk, bevel=0.02)
    tube("NicheMould", [(x, yf - 0.02, z) for x, z in arch], 0.045, dk, square=True, poly=True)
    # the canopy: a crocketed hood mould with stops and a finial
    hood = [(x * 1.25, yf - 0.06, z + (z - zb) * 0.08 + 0.12) for x, z in arch[1:-1]]
    tube("HoodMould", hood, 0.055, dk, square=True, poly=True)
    for k, (x, y, z) in enumerate(hood[1:-1:2]):
        sphere(f"HoodCrocket{k}", 0.07, (x * 1.06, y - 0.03, z + 0.08), dk, seg=8, rings=4, scale=(1, 1, 0.8))
    for sx in (-1, 1):
        sphere(f"Stop{sx}", 0.08, (sx * nw * 1.25, yf - 0.06, zs + 0.12), dk, seg=8, rings=4)
    apex = max(z for _, _, z in hood)
    _pinnacle("Finial", 0, yf - 0.06, apex - 0.05, 0.75, dk)
    # ringed corner shafts
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Corner{sx}{sy}", 0.09, z1 - z0 - 0.2, (sx * W / 2, sy * D / 2, (z0 + z1) / 2), dk, verts=12, bevel=0.0)
            for zz in (5.2, 8.6):
                hoop(f"CornerRing{sx}{sy}{zz}", (sx * W / 2, sy * D / 2, zz), 0.1, "Z", dk, thick=0.025)
    # a brass candlestick in the niche
    wax = wax_mat()
    stick = P._candlestick("Stick", 0, yf + dep / 2, zb + 0.12, 0.3, M["brass"])
    tip = candle("Candle", 0, yf + dep / 2, stick, 0.42, wax, r=0.06)
    lathe("Puddle", [(0, stick), (0.12, stick), (0.11, stick + 0.02), (0, stick + 0.03)], wax, seg=16, loc=(0, yf + dep / 2, 0), jitter=(0.12, 3))
    # capital: a moulding with a frieze of foils, the impost
    box("CapMould", (2.35, 2.35, 0.25), (0, 0, z1 + 0.12), dk, bevel=0.04)
    for k, x in enumerate((-0.6, 0.0, 0.6)):
        foil(f"CapFoil{k}", x, -1.18, z1 + 0.12, 0.09, st, thick=0.015)
    box("Impost", (2.55, 2.55, 0.45), (0, 0, z1 + 0.25 + 0.2), st, bevel=0.04)
    moss("Moss", square_edge(1.25, 0.5, 9, rnd), mo, rnd)
    set_group("Glow")
    flame("Flame", (0, yf + dep / 2, tip - 0.02), h=0.17)
    set_group("Main")
    return _dims()


# ================================================================== black marble column
def pillar_marble(M):
    slab = marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    box("Plinth", (2.3, 2.3, 0.6), (0, 0, 0.3), slab, bevel=0.04)
    for z in (0.04, 0.58):
        box(f"PlinthBead{z}", (2.34, 2.34, 0.05), (0, 0, z), M["brass"], bevel=0.015)
    top = _base_mould("Base", 0.9, 0.6, M["brass"], seg=40)
    lathe("Shaft", [(0, top), (0.56, top), (0.56, top + 0.12), (0.54, 3.5), (0.5, 8.0), (0.47, 10.45), (0, 10.45)], slab, seg=40)
    # gilt bands: a raised band with beads above and below
    for z in (top + 0.12, 4.2, 7.6):
        r = 0.555 - (z - top) * 0.009
        lathe(f"Band{z:.1f}", [(0, z - 0.08), (r + 0.01, z - 0.08), (r + 0.04, z - 0.04), (r + 0.04, z + 0.04), (r + 0.01, z + 0.08), (0, z + 0.08)],
              M["brass"], seg=40)
        for dz in (-0.11, 0.11):
            hoop(f"Bead{z:.1f}{dz}", (0, 0, z + dz), r + 0.012, "Z", M["brass"], thick=0.016)
    # a ring of gilt quatrefoils between the bands
    for k in range(6):
        m = _mark()
        foil(f"GiltFoil{k}", 0, -0.53, 5.9, 0.13, M["brass"], thick=0.018)
        _xform(m, Matrix.Rotation(k / 6 * 2 * math.pi, 4, "Z"))
    # a gilt stiff-leaf capital
    lathe("Astragal", [(0, 10.4), (0.5, 10.4), (0.53, 10.47), (0.5, 10.54), (0, 10.54)], M["brass"], seg=40)
    lathe("Bell", [(0, 10.5), (0.5, 10.5), (0.56, 10.8), (0.7, 11.15), (0.84, 11.35), (0, 11.35)], M["brass"], seg=40)
    stiff_leaf("LeafA", 0.52, 10.55, 10, 0.55, M["brass"], pitch=76, droop=0.42, width=0.18, knob=0.07)
    stiff_leaf("LeafB", 0.6, 10.82, 10, 0.4, M["brass"], phase=math.pi / 10, pitch=66, droop=0.32, width=0.15, knob=0.06)
    box("Abacus", (2.0, 2.0, 0.2), (0, 0, 11.45), M["brass"], bevel=0.03)
    box("Impost", (2.2, 2.2, 0.45), (0, 0, 11.775), slab, bevel=0.04)
    return _dims()


# ================================================================== cast-iron column
def pillar_iron(M):
    box("Plinth", (1.6, 1.6, 0.3), (0, 0, 0.15), M["iron"], bevel=0.03)
    for k in range(4):
        m = _mark()
        foil(f"PlinthFoil{k}", 0, -0.805, 0.15, 0.09, M["iron"], thick=0.015)
        _xform(m, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    lathe("Base", [(0, 0.3), (0.66, 0.3), (0.66, 0.42), (0.52, 0.52), (0.55, 0.62), (0.42, 0.75), (0.4, 0.95), (0.44, 1.05), (0, 1.05)],
          M["iron"], seg=40)
    lathe("Shaft", [(0, 1.0), (0.42, 1.0), (0.41, 6.0), (0.38, 10.0), (0, 10.0)], M["iron"], seg=64, flute=(16, 0.07))
    # riveted collars with a brass bead
    for z in (1.05, 4.0, 7.2):
        lathe(f"Collar{z}", [(0, z), (0.48, z), (0.5, z + 0.06), (0.48, z + 0.12), (0, z + 0.12)], M["iron"], seg=32)
        hoop(f"Brass{z}", (0, 0, z + 0.06), 0.5, "Z", M["brass"], thick=0.02)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            sphere(f"Rivet{z}{k}", 0.02, (math.cos(a) * 0.49, math.sin(a) * 0.49, z + 0.02), M["iron"], seg=6, rings=3)
    # a foundry plate on the front
    s = _mark()
    lathe("FoundryPlate", [(0, 0), (0.16, 0), (0.17, 0.015), (0.15, 0.03), (0, 0.03)], M["brass"], seg=20, scale=(1.0, 0.6))
    _xform(s, Matrix.Translation((0, -0.43, 2.2)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    lathe("Capital", [(0, 9.95), (0.4, 9.95), (0.44, 10.15), (0.54, 10.45), (0.66, 10.7), (0.7, 10.8), (0, 10.8)], M["iron"], seg=40)
    hoop("CapBrass", (0, 0, 10.5), 0.56, "Z", M["brass"], thick=0.022)
    box("Bearer", (0.8, 0.8, 0.7), (0, 0, 11.43), M["iron"], bevel=0.03)
    box("Plate", (2.8, 2.8, 0.22), (0, 0, 11.89), M["iron"], bevel=0.03)
    # four scrolled brackets under the plate, with cast tracery (a cusped ring and a trefoil) in each spandrel
    for k in range(4):
        s = _mark()
        tube(f"Bracket{k}", [(0.0, -0.42, 10.0), (0.0, -0.6, 10.4), (0.0, -0.95, 11.0), (0.0, -1.3, 11.6), (0.0, -1.35, 11.78)], 0.04, M["iron"], square=True)
        tube(f"BracketTop{k}", [(0.0, -0.4, 11.76), (0.0, -1.38, 11.76)], 0.035, M["iron"], square=True, poly=True)
        tube(f"BracketScroll{k}", [(0.0, -0.6, 10.4), (0.0, -0.45, 10.75), (0.0, -0.6, 11.0), (0.0, -0.75, 10.8), (0.0, -0.68, 10.65)], 0.022, M["iron"])
        tube(f"Tracery{k}", circle_pts(0.0, -0.82, 11.38, 0.24, "X", 16), 0.022, M["iron"], closed=True, square=True, poly=True)
        for j in range(3):
            a = math.pi / 2 + j * 2 * math.pi / 3
            tube(f"Cusp{k}{j}", circle_pts(0.0, -0.82 + math.cos(a) * 0.11, 11.38 + math.sin(a) * 0.11, 0.09, "X", 10), 0.016, M["iron"],
                 closed=True, square=True, poly=True)
        tube(f"Strut{k}", [(0.0, -0.58, 11.13), (0.0, -0.62, 11.74)], 0.02, M["iron"], square=True, poly=True)
        sphere(f"BracketRivet{k}", 0.04, (0.0, -1.35, 11.62), M["brass"], seg=8, rings=4)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    return _dims()


# ================================================================== wall pilaster
def pilaster(M):
    st, dk = stones()
    mo, ck = moss_mat(), crack_mat()
    rnd = random.Random(96)
    W, D = 1.8, 0.55
    yb = 0.3                                  # the back, flat to the wall
    yc = yb - D / 2
    box("Plinth", (2.3, D + 0.35, 0.45), (0, yb - (D + 0.35) / 2, 0.225), dk, bevel=0.04)
    box("Plinth2", (2.05, D + 0.2, 0.3), (0, yb - (D + 0.2) / 2, 0.6), st, bevel=0.03)
    box("Shaft", (W, D, 10.4), (0, yc, 0.75 + 5.2), st, bevel=0.03)
    yf = yb - D
    # a traceried blind arch: a dark recess, the mould, and two lancets with a trefoil in the head
    tube("PanelMould", _arch_loop(0, yf - 0.03, W / 2 - 0.18, 1.3, 6.9, 8.25), 0.045, dk, square=True, closed=True, poly=True)
    tracery("Panel", 0, yf, W / 2 - 0.3, 1.45, 6.85, 8.0, st, recess=dk, thick=0.035)
    # a carved crest with a shield
    _gable("Crest", 0, yf - 0.06, 0.62, 8.5, 9.55, 0.12, st, dk, edge=0.035)
    box("Corbel", (1.1, 0.18, 0.16), (0, yf - 0.06, 8.42), dk, bevel=0.02)
    half = [(0.0, 9.22), (0.26, 9.22)]
    for i in range(9):
        t = i / 8
        half.append((0.26 * math.cos(t * math.pi / 2) ** 0.9, 9.0 - 0.42 * math.sin(t * math.pi / 2) ** 1.3))
    half[-1] = (0.0, half[-1][1])
    shield = half + [(-x, z) for x, z in reversed(half[1:-1])]
    prism("Shield", shield, yf - 0.15, 0.05, dk, bevel=0.008)
    tube("ShieldRim", [(x, yf - 0.18, z) for x, z in shield], 0.012, M["brass"], closed=True, square=True, poly=True)
    tube("ShieldChevron", [(-0.2, yf - 0.18, 8.78), (0.0, yf - 0.18, 9.0), (0.2, yf - 0.18, 8.78)], 0.02, M["brass"], square=True, poly=True)
    # capital to the ceiling
    box("CapMould", (W + 0.2, D + 0.15, 0.22), (0, yb - (D + 0.15) / 2, 11.26), dk, bevel=0.03)
    box("Capital", (W + 0.45, D + 0.3, 0.6), (0, yb - (D + 0.3) / 2, 11.7), st, bevel=0.04)
    # a small iron lantern on a scrolled bracket, between the crest and the capital
    ly, lz = yf - 0.55, 10.15
    box("LanternPlate", (0.22, 0.04, 0.4), (0, yf - 0.02, 10.85), M["iron"], bevel=0.01)
    tube("LanternArm", [(0, yf - 0.04, 10.95), (0, yf - 0.3, 11.0), (0, ly, 10.92)], 0.025, M["iron"], square=True)
    tube("LanternCurl", [(0, yf - 0.04, 10.72), (0, yf - 0.18, 10.75), (0, yf - 0.26, 10.86), (0, yf - 0.2, 10.92)], 0.016, M["iron"])
    tube("LanternHook", [(0, ly, 10.92), (0, ly, 10.8)], 0.014, M["iron"], poly=True)
    sl = 0.13
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"LanternPost{sx}{sy}", [(sx * sl, ly + sy * sl, lz - 0.2), (sx * sl, ly + sy * sl, lz + 0.22)], 0.014, M["iron"], square=True, poly=True)
    box("LanternBase", (0.32, 0.32, 0.05), (0, ly, lz - 0.22), M["iron"], bevel=0.01)
    box("LanternBand", (0.3, 0.3, 0.03), (0, ly, lz + 0.22), M["iron"], bevel=0.008)
    s = _mark()
    cone("LanternRoof", 0.24, 0.03, 0.18, (0, ly, lz + 0.33), M["iron"], verts=4)
    _xform(s, Matrix.Translation((0, ly, 0)) @ Matrix.Rotation(math.pi / 4, 4, "Z") @ Matrix.Translation((0, -ly, 0)))
    sphere("LanternFinial", 0.03, (0, ly, lz + 0.44), M["brass"], seg=6, rings=3)
    tip = candle("LanternCandle", 0, ly, lz - 0.2, 0.2, wax_mat(), r=0.045)
    moss("Moss", [(rnd.uniform(-1.0, 1.0), yb - (D + 0.35) + 0.04, 0.45) for _ in range(6)], mo, rnd)
    face_crack("Crack", 0.6, 0.76, 0.75, 1.3, yf - 0.002, ck, rnd)
    set_group("Glow")
    flame("Flame", (0, ly, tip - 0.02), h=0.13)
    set_group("Main")
    return _dims()


# tall props need the preview camera further back
P.PREVIEW_PAD.update({"PillarCluster": 1.05, "PillarOctagon": 1.05, "PillarTwisted": 1.05, "PillarFanVault": 1.0, "PillarNiche": 1.05,
                      "PillarMarble": 1.05, "PillarIron": 1.05, "Pilaster": 1.05})

P.BUILD.update({
    "PillarCluster": pillar_cluster,
    "PillarOctagon": pillar_octagon,
    "PillarTwisted": pillar_twisted,
    "PillarFanVault": pillar_fan_vault,
    "PillarNiche": pillar_niche,
    "PillarMarble": pillar_marble,
    "PillarIron": pillar_iron,
    "Pilaster": pilaster,
})
