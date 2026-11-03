"""Props batch 8 (2026-11-03, reworked): the courtyard, for nh_props.py, in the school's gothic style.

Dark weathered castle stone (greener grey, darker in the joints), moss and ivy, wrought iron, brass and crimson,
lantern and candle light, and the school's motifs: pointed arches, trefoils and quatrefoils, crockets and
pinnacles, buttresses, grotesque heads and ravens. Chips are suggested with cracks and darker stains.

  Fountain      an octagonal gothic basin with lancet-and-quatrefoil panels and crocketed corner pinnacles, a
                clustered central pier with a foliage capital, a lobed upper bowl with four grotesque-head spouts,
                and a crocketed spire with a brass raven (Pool: the water surfaces and every stream; it always shows)
  CloisterArch  one bay of a cloister arcade: clustered piers with foliage capitals, buttresses, a double-moulded
                pointed arch with a trefoil in its head, a crocketed hood mould ending in grotesque label stops, a
                cornice, crest and pinnacles, an iron lantern on a chain (Glass: the panes, Glow: the flame) and ivy
  StonePlanter  a buttressed raised bed with lancet tracery panels and a moulded coping: dark rose bushes with
                crimson roses, ferns, moss and a trail of ivy
  Topiary       a clipped yew in three tiers (rounded clumps) in a carved tub with lancet panels and crocketed
                corner pinnacles
  Sundial       an octagonal stepped base, a pedestal of clustered colonnettes with a foliage capital, a brass dial
                with hour marks and a compass rose, a pierced gothic gnomon, and a crow on the rim
  Well          a stone wellhead with a carved trefoil band, a wrought-iron canopy with pointed gables and scrolls,
                a steep slate roof with iron cresting, a windlass with a chain and an iron-banded bucket, and an
                iron lantern (Glass, Glow)
  Balustrade    a pierced gothic parapet: a trefoil-headed lancet arcade between buttressed posts with crocketed
                pinnacles, a moulded coping, an iron lantern on one post (Glass, Glow); 8 studs, tiles end to end
  Memorial      the founders' memorial spire: stepped plinths, a buttressed die with a canopied niche holding a
                brass plaque, a traceried octagonal shaft, a crocketed spire and an iron cross, three votive
                candles (Glow), a laurel wreath, and a low iron railing with spear tips

Front faces -Y, Z is up, the origin is at the bottom centre.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _pinnacle, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, leaf, strip, prism, _mark, _xform, _dims, flat, _smooth, _solid


# ------------------------------------------------------------------ materials

def castle():
    """The courtyard's castle stone: a dark, greenish weathered grey, and a darker shade for plinths and joints."""
    return (material("CastleStone", "NH_Limestone", tint=(0.27, 0.285, 0.265), scale=0.28, wear=0.22, dirt=1.0),
            material("CastleStoneDark", "NH_Limestone", tint=(0.16, 0.17, 0.155), scale=0.28, wear=0.18, dirt=1.0))


def mossy():
    return flat("Moss", (0.018, 0.04, 0.014), 0.95, dirt=0.8)


def ivies():
    return [flat("Ivy", (0.01, 0.035, 0.012), 0.45, dirt=0.7), flat("IvyOld", (0.018, 0.042, 0.01), 0.5, dirt=0.8)]


def hollow():
    """Near-black: cracks, eye sockets, open mouths, recesses."""
    return flat("Hollow", (0.008, 0.008, 0.01), 0.95, dirt=0.3)


def staining():
    return flat("Stain", (0.06, 0.065, 0.05), 0.95, dirt=0.6)


# ------------------------------------------------------------------ helpers

def _moss(prefix, pts, mat, rnd, size=0.12):
    """Low cushions of moss at the given points (squashed, lumpy ico spheres)."""
    for k, p in enumerate(pts):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size * rnd.uniform(0.6, 1.3), location=p)
        o = bpy.context.active_object
        o.name = f"{prefix}{k}"
        o.scale = (rnd.uniform(1.0, 1.9), rnd.uniform(1.0, 1.9), rnd.uniform(0.3, 0.5))
        o.rotation_euler[2] = rnd.uniform(0, math.pi)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for v in o.data.vertices:
            v.co *= 1 + rnd.uniform(-0.2, 0.15)
        _finish(o, mat, 0)


def _ring_pts(r, z, n, rnd, cx=0.0, cy=0.0):
    pts = []
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r, z))
    return pts


def _foil(name, cx, y, cz, r, mat, lobes=4, thick=0.022):
    """A carved quatrefoil (or trefoil) facing -Y: a ring with lobes, in square-section stone."""
    tube(name, circle_pts(cx, y, cz, r, "Y", 10), thick, mat, closed=True, square=True, poly=True)
    for k in range(lobes):
        a = k / lobes * 2 * math.pi + (math.pi / 2 if lobes == 3 else 0.0)
        tube(f"{name}F{k}", circle_pts(cx + math.cos(a) * r * 0.52, y, cz + math.sin(a) * r * 0.52, r * 0.44, "Y", 6), thick * 0.8, mat,
             closed=True, square=True, poly=True)


def _pointed(hw, zs, za, n=12):
    """A gothic pointed arch from the left springing over the apex to the right springing, as (x, z)."""
    h = za - zs
    c = (h * h - hw * hw) / (2 * hw)
    rho = c + hw
    a0, a1 = math.pi, math.acos(max(-1.0, min(1.0, -c / rho)))
    left = [(c + rho * math.cos(a0 + (a1 - a0) * i / n), zs + rho * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    left[-1] = (0.0, za)
    return left + [(-x, z) for x, z in reversed(left[:-1])]


def _lancet(name, cx, y, z0, hw, zs, za, mat, thick=0.03, cusp=True, n=8):
    """A lancet outline facing -Y: straight jambs from z0, a pointed head, a trefoil in the head."""
    pts = [(cx - hw, y, z0)] + [(cx + x, y, z) for x, z in _pointed(hw, zs, za, n)] + [(cx + hw, y, z0)]
    tube(name, pts, thick, mat, closed=True, square=True, poly=True)
    if cusp:
        _foil(f"{name}Tre", cx, y, zs + (za - zs) * 0.42, hw * 0.52, mat, lobes=3, thick=thick * 0.75)


def _panel(name, cx, y, z0, w, h, mat, thick=0.035):
    """A carved tracery panel facing -Y: a moulded frame round a trefoil-headed lancet."""
    tube(f"{name}Frame", [(cx - w / 2, y, z0), (cx + w / 2, y, z0), (cx + w / 2, y, z0 + h), (cx - w / 2, y, z0 + h)], thick, mat,
         closed=True, square=True, poly=True)
    hw = w / 2 - 0.12
    _lancet(f"{name}Lancet", cx, y - 0.005, z0 + 0.1, hw, z0 + h * 0.5, z0 + h - 0.1, mat, thick=thick * 0.8)


def _spirelet(name, x, y, z, h, w, mat, crockets=1):
    """A small crocketed pinnacle: a square shaft, a moulded band, a spire with crockets up its edges, a finial."""
    box(f"{name}Shaft", (w, w, h * 0.38), (x, y, z + h * 0.19), mat, bevel=min(0.03, w * 0.1), segments=1)
    box(f"{name}Band", (w * 1.15, w * 1.15, h * 0.05), (x, y, z + h * 0.4), mat, bevel=0.01, segments=1)
    hs = h * 0.56
    zb = z + h * 0.42
    _spike(f"{name}Spire", (x, y, zb + hs / 2), w * 0.72, hs, mat, verts=4, rot=(0, 0, math.pi / 4))
    for k in range(crockets):
        t = (k + 1) / (crockets + 1)
        rr = w * 0.72 * (1 - t) + 0.015
        for j in range(4):
            a = math.pi / 4 + j * math.pi / 2
            sphere(f"{name}Crocket{k}{j}", w * 0.13, (x + math.cos(a) * rr, y + math.sin(a) * rr, zb + hs * t), mat, seg=6, rings=3,
                   scale=(1, 1, 1.5))
    sphere(f"{name}Finial", w * 0.16, (x, y, zb + hs + w * 0.1), mat, seg=8, rings=4)


def _spike(name, loc, r, h, mat, verts=4, rot=(0, 0, 0)):
    """A plain cone with no bevel (cone() bevels, which multiplies a tiny spike's triangles)."""
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=0.0, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return _finish(o, mat, 0)


def _crockets(prefix, pts, mat, size=0.06):
    for k, p in enumerate(pts):
        sphere(f"{prefix}{k}", size, p, mat, seg=6, rings=3, scale=(1, 1, 1.4))


def _grotesque(prefix, mtx, mat, dark):
    """A carved grotesque head facing -Y (built at the origin, moved by mtx). Returns the mouth point."""
    s = _mark()
    sphere(f"{prefix}Skull", 0.2, (0, 0, 0), mat, seg=10, rings=6, scale=(1.0, 1.15, 0.9))
    cone(f"{prefix}Snout", 0.12, 0.07, 0.26, (0, -0.25, -0.04), mat, verts=8, rot=(math.pi / 2, 0, 0))
    sphere(f"{prefix}Jaw", 0.1, (0, -0.2, -0.12), mat, seg=8, rings=4, scale=(1.1, 1.25, 0.6))
    box(f"{prefix}Brow", (0.34, 0.08, 0.06), (0, -0.16, 0.09), mat, bevel=0.02)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.032, (sx * 0.08, -0.205, 0.04), dark, seg=6, rings=4)
        cone(f"{prefix}Horn{sx}", 0.05, 0.0, 0.2, (sx * 0.14, 0.04, 0.17), mat, verts=6, rot=(math.radians(-30), sx * math.radians(28), 0))
        cone(f"{prefix}Fang{sx}", 0.02, 0.0, 0.07, (sx * 0.05, -0.33, -0.11), mat, verts=4, rot=(math.pi, 0, 0))
        sphere(f"{prefix}Ear{sx}", 0.06, (sx * 0.19, 0.0, 0.03), mat, seg=6, rings=3, scale=(0.5, 1.0, 1.4))
    sphere(f"{prefix}Mouth", 0.05, (0, -0.37, -0.07), dark, seg=6, rings=4)
    _xform(s, mtx)
    return mtx @ Vector((0, -0.39, -0.07))


def _raven(prefix, mtx, mat, eye):
    """A perched raven facing -Y, feet at the origin."""
    s = _mark()
    sphere(f"{prefix}Body", 0.16, (0, 0.03, 0.2), mat, seg=10, rings=6, scale=(0.75, 1.35, 0.85))
    sphere(f"{prefix}Chest", 0.1, (0, -0.12, 0.25), mat, seg=8, rings=5, scale=(0.9, 0.9, 1.1))
    sphere(f"{prefix}Head", 0.085, (0, -0.2, 0.36), mat, seg=10, rings=6)
    cone(f"{prefix}Beak", 0.033, 0.0, 0.16, (0, -0.34, 0.345), mat, verts=6, rot=(math.radians(97), 0, 0))
    box(f"{prefix}Tail", (0.13, 0.28, 0.025), (0, 0.33, 0.15), mat, bevel=0.008, rot=(math.radians(-18), 0, 0))
    for sx in (-1, 1):
        sphere(f"{prefix}Wing{sx}", 1.0, (sx * 0.1, 0.07, 0.22), mat, seg=8, rings=5, scale=(0.05, 0.24, 0.12))
        tube(f"{prefix}Leg{sx}", [(sx * 0.04, 0.0, 0.11), (sx * 0.04, -0.02, 0.0)], 0.011, mat, poly=True)
        tube(f"{prefix}Toes{sx}", [(sx * 0.04, 0.03, 0.0), (sx * 0.04, -0.1, 0.0)], 0.008, mat, poly=True)
        sphere(f"{prefix}Eye{sx}", 0.014, (sx * 0.055, -0.255, 0.375), eye, seg=6, rings=3)
    _xform(s, mtx)


def _lantern(prefix, mtx, M, lanterns, wax):
    """An iron lantern (cage, roof, ring, candle), its origin at the base; the panes and the flame are added later
    by _lights() in the Glass and Glow pieces."""
    s = _mark()
    w = 0.13
    box(f"{prefix}Base", (0.3, 0.3, 0.04), (0, 0, 0.02), M["iron"], bevel=0.01)
    cone(f"{prefix}Drop", 0.06, 0.0, 0.12, (0, 0, -0.06), M["iron"], verts=8, rot=(math.pi, 0, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"{prefix}Post{sx}{sy}", [(sx * w, sy * w, 0.04), (sx * w, sy * w, 0.42)], 0.014, M["iron"], square=True, poly=True)
    box(f"{prefix}Band", (0.3, 0.3, 0.03), (0, 0, 0.43), M["iron"], bevel=0.008)
    cone(f"{prefix}Roof", 0.24, 0.03, 0.18, (0, 0, 0.54), M["iron"], verts=4, rot=(0, 0, math.pi / 4))
    sphere(f"{prefix}Finial", 0.03, (0, 0, 0.65), M["brass"], seg=8, rings=4)
    tube(f"{prefix}Ring", circle_pts(0, 0, 0.71, 0.04, "X", 8), 0.01, M["iron"], closed=True, square=True, poly=True)
    cyl(f"{prefix}Candle", 0.035, 0.12, (0, 0, 0.1), wax, verts=10, bevel=0)
    _xform(s, mtx)
    lanterns.append(mtx)


def _lights(lanterns, M, flames=()):
    """The lanterns' glass panes (Glass) and every flame (Glow), then back to Main."""
    if lanterns:
        set_group("Glass")
        for i, mtx in enumerate(lanterns):
            s = _mark()
            w = 0.126
            for k, (sx, sy, a) in enumerate(((0, -1, 0), (0, 1, 0), (-1, 0, 1), (1, 0, 1))):
                box(f"Pane{i}{k}", (0.24 if a == 0 else 0.008, 0.008 if a == 0 else 0.24, 0.36), (sx * w, sy * w, 0.23), M["glassclear"],
                    bevel=0.0, segments=1)
            _xform(s, mtx)
    set_group("Glow")
    for i, mtx in enumerate(lanterns):
        flame(f"LanternFlame{i}", tuple(mtx @ Vector((0, 0, 0.16))), h=0.12)
    for i, (p, h) in enumerate(flames):
        flame(f"Flame{i}", p, h=h)
    set_group("Main")


def _ivy(prefix, path, mats, vine, rnd, count=30, size=0.16):
    """A climbing ivy stem along a path with leaves along it."""
    tube(f"{prefix}Vine", path, 0.016, vine)
    pts = _smooth(path, 3)
    for k in range(count):
        p = pts[int(k / max(1, count - 1) * (len(pts) - 1))]
        q = (p[0] + rnd.uniform(-0.07, 0.07), p[1] + rnd.uniform(-0.05, 0.05), p[2] + rnd.uniform(-0.05, 0.05))
        leaf(f"{prefix}Leaf{k}", q, rnd.uniform(0, 2 * math.pi), math.radians(rnd.uniform(-25, 50)), size * rnd.uniform(0.7, 1.2), size * 0.8, 0.25,
             mats[k % 2], n=3, fold=0.2, thick=0.008)


def _crack(name, p0, u, v, length, rnd, mat, n=6):
    """A hairline crack on a face: a zigzag from p0 along u, wandering along v."""
    u, v = Vector(u).normalized(), Vector(v).normalized()
    pts = []
    for i in range(n + 1):
        t = i / n
        j = rnd.uniform(-0.07, 0.07) if 0 < i < n else 0.0
        pts.append(tuple(Vector(p0) + u * (length * t) + v * j))
    tube(name, pts, 0.009, mat, square=True, poly=True)


def _stain(name, c, u, v, w, h, mat, rnd, n=10):
    """A darker weather stain on a face: an irregular thin patch spanned by u (across) and v (down)."""
    u, v = Vector(u).normalized(), Vector(v).normalized()
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = []
    for k in range(n):
        a = k / n * 2 * math.pi
        k1 = rnd.uniform(0.7, 1.1)
        vs.append(bm.verts.new(tuple(Vector(c) + u * (math.cos(a) * w * k1) + v * (math.sin(a) * h * k1))))
    bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    _solid(ob, 0.004)


def _link(name, c, axis, r, mat):
    """One chain link (a light square-section ring)."""
    tube(name, circle_pts(c[0], c[1], c[2], r, axis, 8), 0.009, mat, closed=True, square=True, poly=True)


def _bloom(prefix, pos, r, petal, sepal):
    """A light crimson rose: a bud, two rings of cupped petals, sepals (lighter than nh_props_batch4.rose)."""
    x, y, z = pos
    sphere(f"{prefix}Bud", r * 0.35, (x, y, z + r * 0.2), petal, seg=8, rings=5, scale=(1, 1, 1.3))
    for k, cnt in enumerate((4, 5)):
        d = r * (0.22 + 0.22 * k)
        for i in range(cnt):
            a = i / cnt * 2 * math.pi + k * 0.7
            sphere(f"{prefix}Petal{k}{i}", r * (0.42 + 0.12 * k), (x + math.cos(a) * d, y + math.sin(a) * d, z + r * (0.15 - 0.06 * k)), petal,
                   seg=6, rings=4, scale=(0.75, 0.75, 0.55))
    for i in range(3):
        a = i / 3 * 2 * math.pi
        leaf(f"{prefix}Sepal{i}", (x, y, z - r * 0.1), a, math.radians(-30), r * 0.7, r * 0.18, 0.0, sepal, n=3, thick=0.008)


def _rotz(mtx_t, a):
    return Matrix.Translation(mtx_t) @ Matrix.Rotation(a, 4, "Z")


# ================================================================== fountain
def fountain(M):
    stone, dark = castle()
    moss, hol, stain = mossy(), hollow(), staining()
    water = flat("FountainWater", (0.025, 0.045, 0.055), 0.02)
    rnd = random.Random(81)
    R, B = 4.2, 0.14             # basin radius (octagon corners), step height
    set_group("Main")
    lathe("Step", [(0, 0), (R + 0.6, 0), (R + 0.6, B), (0, B)], dark, seg=8)
    lathe("Basin", [(0, B), (R + 0.1, B), (R + 0.1, B + 0.24), (R - 0.05, B + 0.34), (R - 0.05, B + 1.12), (R + 0.12, B + 1.2), (R + 0.2, B + 1.36),
                    (R + 0.1, B + 1.5), (R - 0.4, B + 1.5), (R - 0.5, B + 1.4), (R - 0.5, B + 0.43), (0, B + 0.43)], stone, seg=8)
    rf = (R - 0.05) * math.cos(math.pi / 8)       # wall face distance from the centre
    # eight traceried faces, a buttress and a crocketed pinnacle at every corner
    for k in range(8):
        phi = math.pi / 8 + k * math.pi / 4
        s = _mark()
        _panel(f"Panel{k}", 0, 0, B + 0.4, 2.25, 0.72, dark)
        _xform(s, Matrix.Rotation(phi + math.pi / 2, 4, "Z") @ Matrix.Translation((0, -(rf + 0.012), 0)))
        th = k * math.pi / 4
        s = _mark()
        box(f"Buttress{k}", (0.42, 0.5, 1.25), (0, 0, B + 0.62), dark, bevel=0.04)
        _spirelet(f"Pin{k}", 0, 0, B + 1.48, 1.0, 0.3, stone)
        _xform(s, _rotz((math.cos(th) * (R + 0.08), math.sin(th) * (R + 0.08), 0), th))
    zf = B + 0.43
    # the clustered central pier with a foliage capital
    lathe("PierBase", [(0, zf), (0.92, zf), (0.94, zf + 0.12), (0.78, zf + 0.22), (0.7, zf + 0.42), (0, zf + 0.42)], dark, seg=8)
    zt = 2.9
    cyl("PierCore", 0.36, zt - zf - 0.42, (0, 0, (zf + 0.42 + zt) / 2), stone, verts=12, bevel=0)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        cyl(f"PierShaft{k}", 0.13, zt - zf - 0.42, (math.cos(a) * 0.4, math.sin(a) * 0.4, (zf + 0.42 + zt) / 2), stone, verts=10, bevel=0)
    cyl("PierAnnulet", 0.56, 0.07, (0, 0, 1.95), dark, verts=16, bevel=0)
    lathe("Capital", [(0, zt - 0.05), (0.55, zt - 0.05), (0.7, zt + 0.1), (0.84, zt + 0.22), (0, zt + 0.22)], dark, seg=12)
    _crockets("CapLeaf", [(math.cos(a) * 0.7, math.sin(a) * 0.7, zt + 0.06) for a in [k / 10 * 2 * math.pi for k in range(10)]], stone, 0.08)
    # the lobed upper bowl, grotesque spouts at four lobes, a spire with a brass raven on the top
    lathe("Bowl", [(0, 3.08), (0.6, 3.08), (1.1, 3.24), (1.55, 3.5), (1.85, 3.74), (1.95, 3.87), (1.85, 3.93), (1.62, 3.8), (1.0, 3.62),
                   (0, 3.57)], stone, seg=40, flute=(8, 0.14))
    tube("BowlBand", circle_pts(0, 0, 3.32, 1.25, "Z", 24), 0.03, dark, closed=True, square=True, poly=True)
    mouths = []
    for k in range(4):
        a = math.pi / 8 + k * math.pi / 2
        r = 1.95 * (1 - 0.14 * (0.5 + 0.5 * math.cos(8 * a))) + 0.04
        mouths.append((a, _grotesque(f"Spout{k}", _rotz((math.cos(a) * r, math.sin(a) * r, 3.74), a + math.pi / 2) @ Matrix.Scale(0.85, 4), stone, hol)))
    lathe("FinialFoot", [(0, 3.57), (0.4, 3.57), (0.36, 3.72), (0.22, 3.86), (0, 3.86)], dark, seg=8)
    _spirelet("Spire", 0, 0, 3.84, 1.5, 0.4, stone, crockets=3)
    _raven("Raven", Matrix.Translation((0, 0, 3.84 + 1.5 + 0.1)) @ Matrix.Rotation(-0.6, 4, "Z") @ Matrix.Scale(1.1, 4), M["brass"], hol)
    # weathering: cracks and stains on the wall faces, moss round the foot, the coping and the pier
    for k in (0, 3, 5):
        phi = math.pi / 8 + k * math.pi / 4
        n = Vector((math.cos(phi), math.sin(phi), 0))
        u = Vector((-math.sin(phi), math.cos(phi), 0))
        _crack(f"Crack{k}", tuple(n * (rf + 0.03) + u * rnd.uniform(-1.2, -0.6) + Vector((0, 0, B + 1.1))), u + Vector((0, 0, -1.4)), Vector((0, 0, 1)),
               0.8, rnd, hol)
    for k in (1, 2, 6):
        phi = math.pi / 8 + k * math.pi / 4
        n = Vector((math.cos(phi), math.sin(phi), 0))
        u = Vector((-math.sin(phi), math.cos(phi), 0))
        _stain(f"Stain{k}", tuple(n * (rf + 0.03) + u * rnd.uniform(-0.5, 0.5) + Vector((0, 0, B + 0.8))), u, (0, 0, 1), 0.5, 0.35, stain, rnd)
    _moss("MossFoot", _ring_pts(R + 0.3, B + 0.03, 10, rnd), moss, rnd, 0.17)
    _moss("MossLip", _ring_pts(R + 0.05, B + 1.5, 6, rnd), moss, rnd, 0.08)
    _moss("MossPier", _ring_pts(0.8, zf + 0.42, 5, rnd), moss, rnd, 0.08)
    # the water: both surfaces, a stream from every grotesque, an overflow from the other lobes
    set_group("Pool")
    lathe("PoolLow", [(0, B + 1.2), (R - 0.49, B + 1.2), (R - 0.49, B + 1.24), (0, B + 1.24)], water, seg=8)
    lathe("PoolHigh", [(0, 3.7), (1.6, 3.7), (1.6, 3.74), (0, 3.74)], water, seg=48, flute=(8, 0.14))
    for k, (a, m) in enumerate(mouths):
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Jet{k}", [tuple(m), (c * 2.55, s_ * 2.55, 3.55), (c * 2.9, s_ * 2.9, 2.6), (c * 3.05, s_ * 3.05, B + 1.22)], 0.04, water)
    for k in range(4):
        a = math.pi / 8 + math.pi / 4 + k * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Overflow{k}", [(c * 1.92, s_ * 1.92, 3.88), (c * 2.08, s_ * 2.08, 3.5), (c * 2.15, s_ * 2.15, 2.4), (c * 2.18, s_ * 2.18, B + 1.22)], 0.028, water)
    set_group("Main")
    return _dims()


# ================================================================== cloister arch
def cloister_arch(M, lantern=True):
    stone, dark = castle()
    moss, hol, stain, ivy = mossy(), hollow(), staining(), ivies()
    vine = flat("Vine", (0.05, 0.04, 0.025), 0.9)
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)
    rnd = random.Random(82)
    lanterns = []
    set_group("Main")
    zs, xp = 5.6, 3.4            # springing height, pier centres
    for sx in (-1, 1):
        x = sx * xp
        box(f"Plinth{sx}", (1.45, 1.45, 0.5), (x, 0, 0.25), dark, bevel=0.05)
        box(f"Base{sx}", (1.15, 1.15, 0.3), (x, 0, 0.65), stone, bevel=0.06)
        box(f"Core{sx}", (0.8, 0.8, zs - 1.3), (x, 0, 0.8 + (zs - 1.3) / 2), stone, bevel=0.04)
        for k, (dx, dy) in enumerate(((0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4))):
            cyl(f"Shaft{sx}{k}", 0.17, zs - 1.3, (x + dx, dy, 0.8 + (zs - 1.3) / 2), stone, verts=10, bevel=0)
            cyl(f"Annulet{sx}{k}", 0.2, 0.06, (x + dx, dy, 3.2), dark, verts=10, bevel=0)
            cyl(f"ShaftBase{sx}{k}", 0.22, 0.14, (x + dx, dy, 0.87), dark, verts=10, bevel=0)
        box(f"Bell{sx}", (1.1, 1.1, 0.25), (x, 0, zs - 0.62), dark, bevel=0.05)
        _crockets(f"Leaf{sx}", [(x + math.cos(a) * 0.64, math.sin(a) * 0.64, zs - 0.58) for a in [k / 8 * 2 * math.pi + math.pi / 8 for k in range(8)]],
                  stone, 0.1)
        box(f"Capital{sx}", (1.35, 1.35, 0.25), (x, 0, zs - 0.38), stone, bevel=0.05)
        box(f"Abacus{sx}", (1.55, 1.55, 0.16), (x, 0, zs - 0.08), dark, bevel=0.03)
        # a stepped buttress on the outer side
        xb = sx * (xp + 1.0)
        box(f"Buttress{sx}", (0.6, 0.95, 4.0), (xb, 0, 2.0), stone, bevel=0.04)
        box(f"ButtressCap{sx}", (0.72, 1.05, 0.14), (xb, 0, 4.06), dark, bevel=0.03, rot=(0, sx * math.radians(28), 0))
        box(f"ButtressUpper{sx}", (0.42, 0.8, 2.6), (sx * (xp + 0.9), 0, 5.35), stone, bevel=0.04)
        box(f"ButtressTop{sx}", (0.54, 0.9, 0.14), (sx * (xp + 0.9), 0, 6.68), dark, bevel=0.03, rot=(0, sx * math.radians(32), 0))
        box(f"ButtressFoot{sx}", (0.75, 1.1, 0.35), (xb, 0, 0.18), dark, bevel=0.04)
        _moss(f"MossPier{sx}", [(x + rnd.uniform(-0.7, 0.7), sy * 0.74, 0.04) for sy in (-1, 1) for _ in range(3)], moss, rnd, 0.12)
    # the arch: two moulded orders, carved spandrels, a trefoil in the head
    outer, inner = _pointed(4.05, zs, 10.25), _pointed(2.75, zs, 9.6)
    prism("ArchBand", outer + list(reversed(inner)), 0, 1.0, dark, bevel=0.03)
    # the wall face round the arch is its own piece with the seamless NH_CastleStone set (not baked), so a builder can run
    # the same stone (a MaterialVariant at 8 studs a tile) across his wall and blend it into the arch
    set_group("Wall")
    prism("Spandrel", [(-4.05, 10.6), (4.05, 10.6)] + list(reversed(outer)), 0, 0.82, stone, bevel=0.02)
    set_group("Main")
    tube("Roll", [(x, 0, z) for x, z in inner], 0.13, stone, poly=True)
    for face in (-1, 1):
        tube(f"Order{face}", [(x, face * 0.48, z) for x, z in _pointed(3.45, zs, 9.95, 10)], 0.07, stone, square=True, poly=True)
    _foil("HeadTrefoil", 0, 0, 8.72, 0.62, stone, lobes=3, thick=0.07)
    for sx in (-1, 1):
        tube(f"HeadTie{sx}", [(sx * 0.35, 0, 9.12), (sx * 0.5, 0, 9.42)], 0.05, stone, square=True, poly=True)
    # the hood mould with crockets and grotesque label stops, trefoils in the spandrels
    hood = _pointed(4.12, zs - 0.1, 10.35, 12)
    for face in (-1, 1):
        y = face * 0.53
        tube(f"Hood{face}", [(x, y, z) for x, z in hood], 0.07, dark, square=True, poly=True)
        pts = []
        for i in range(3, len(hood) - 3, 3):
            x, z = hood[i]
            d = Vector((x, z - 7.4)).normalized()
            pts.append((x + d.x * 0.1, y + face * 0.02, z + d.y * 0.1))
        _crockets(f"HoodCrocket{face}", pts, dark, 0.075)
        for sx in (-1, 1):
            _grotesque(f"Stop{face}{sx}", Matrix.Translation((sx * 4.12, y + face * 0.08, zs - 0.25)) @ Matrix.Rotation(0 if face < 0 else math.pi, 4, "Z") @
                       Matrix.Scale(0.62, 4), stone, hol)
            _foil(f"Trefoil{face}{sx}", sx * 3.3, face * 0.43, 9.55, 0.26, dark, lobes=3)
    box("Cornice", (8.5, 1.12, 0.3), (0, 0, 10.75), dark, bevel=0.04)
    box("CorniceBed", (8.2, 0.95, 0.1), (0, 0, 10.57), stone, bevel=0.02)
    _gable("Crest", 0, 0, 0.9, 10.9, 11.7, 0.3, stone, dark, edge=0.045)
    _foil("CrestSeal", 0, -0.17, 11.22, 0.16, dark)
    for sx in (-1, 1):
        _pinnacle(f"Pin{sx}", sx * xp, 0, 10.9, 1.0, stone)
    # the lantern hangs on a chain from the trefoil (CloisterArchNoLamp leaves it out)
    if lantern:
        for k in range(5):
            _link(f"Chain{k}", (0, 0, 8.04 - k * 0.12), "X" if k % 2 else "Y", 0.05, M["iron"])
        _lantern("Lantern", Matrix.Translation((0, 0, 7.4 - 0.72)), M, lanterns, wax)
    # weathering and ivy
    _crack("CrackL", (-3.0, -0.42, 9.1), (0.3, 0, -1), (1, 0, 0), 1.1, rnd, hol)
    _crack("CrackR", (2.3, -0.42, 10.3), (0.6, 0, -1), (1, 0, 0), 0.9, rnd, hol)
    _stain("StainL", (-3.6, -0.42, 8.2), (1, 0, 0), (0, 0, 1), 0.35, 0.8, stain, rnd)
    _stain("StainR", (xp, -0.73, 1.4), (1, 0, 0), (0, 0, 1), 0.45, 0.6, stain, rnd)
    _ivy("Ivy", [(-xp - 0.3, -0.78, 0.05), (-xp + 0.1, -0.62, 1.2), (-xp - 0.25, -0.6, 2.4), (-xp + 0.15, -0.6, 3.6), (-xp - 0.1, -0.62, 4.6),
                 (-xp + 0.25, -0.74, 5.3)], ivy, vine, rnd, count=20)
    _moss("MossCornice", [(rnd.uniform(-4, 4), rnd.uniform(-0.45, 0.45), 10.9) for _ in range(5)], moss, rnd, 0.1)
    _lights(lanterns, M)
    return _dims()


# ================================================================== stone planter
def stone_planter(M):
    stone, dark = castle()
    moss, hol, stain, ivy = mossy(), hollow(), staining(), ivies()
    vine = flat("Vine", (0.05, 0.04, 0.025), 0.9)
    soil = material("Soil", "NH_Limestone", tint=(0.1, 0.07, 0.05), scale=1.2, rough_add=0.35, wear=0.0, dirt=0.9)
    rose_leaf = [flat("RoseLeaf", (0.012, 0.032, 0.014), 0.88, dirt=0.7), flat("RoseLeafOld", (0.02, 0.035, 0.012), 0.9, dirt=0.8)]
    petal = flat("RosePetal", (0.16, 0.006, 0.016), 0.55, dirt=0.9)
    fern = [flat("Fern", (0.014, 0.045, 0.014), 0.5), flat("FernDark", (0.01, 0.03, 0.01), 0.55)]
    rnd = random.Random(83)
    set_group("Main")
    W, D, H = 6.2, 2.5, 1.5
    box("Plinth", (W + 0.3, D + 0.3, 0.28), (0, 0, 0.14), dark, bevel=0.04)
    for sy in (-1, 1):
        box(f"Wall{sy}", (W, 0.3, H - 0.28), (0, sy * (D / 2 - 0.15), 0.28 + (H - 0.28) / 2), stone, bevel=0.03)
        box(f"Cap{sy}", (W + 0.2, 0.5, 0.14), (0, sy * (D / 2 - 0.15), H + 0.07), dark, bevel=0.04)
        box(f"Drip{sy}", (W + 0.1, 0.06, 0.06), (0, sy * (D / 2 + 0.07), H - 0.03), dark, bevel=0.015)
    for sx in (-1, 1):
        box(f"End{sx}", (0.3, D - 0.6, H - 0.28), (sx * (W / 2 - 0.15), 0, 0.28 + (H - 0.28) / 2), stone, bevel=0.03)
        box(f"EndCap{sx}", (0.5, D - 0.5, 0.14), (sx * (W / 2 - 0.15), 0, H + 0.07), dark, bevel=0.04)
    # buttresses with sloped caps between the panels and at the corners
    for sy in (-1, 1):
        y = sy * (D / 2 + 0.12)
        for x in (-3.0, -1.0, 1.0, 3.0):
            box(f"Buttress{sy}{x}", (0.32, 0.26, 1.05), (x, y, 0.28 + 0.52), dark, bevel=0.03, segments=1)
            box(f"ButtressCap{sy}{x}", (0.36, 0.34, 0.1), (x, y + sy * 0.02, 1.33), dark, bevel=0.02, segments=1, rot=(sy * math.radians(-30), 0, 0))
    # tracery panels: three a side, one at each end
    for sy in (-1, 1):
        for k, cx in enumerate((-2.0, 0.0, 2.0)):
            s = _mark()
            _panel(f"Panel{sy}{k}", 0, 0, 0.42, 1.4, 0.88, dark)
            _xform(s, Matrix.Translation((cx, sy * (D / 2 + 0.012), 0)) @ Matrix.Rotation(0 if sy < 0 else math.pi, 4, "Z"))
    for sx in (-1, 1):
        s = _mark()
        _panel(f"EndPanel{sx}", 0, 0, 0.42, 1.3, 0.88, dark)
        _xform(s, Matrix.Translation((sx * (W / 2 + 0.012), 0, 0)) @ Matrix.Rotation(-sx * math.pi / 2, 4, "Z"))
    box("Soil", (W - 0.6, D - 0.6, 0.12), (0, 0, H - 0.08), soil, bevel=0.01)
    # three dark rose bushes with crimson roses, ferns at the ends
    for b, bx in enumerate((-1.9, 0.0, 1.9)):
        for i in range(9):
            a = rnd.uniform(0, 2 * math.pi)
            d = rnd.uniform(0, 0.5)
            z = H + rnd.uniform(0.0, 0.42) * (1 - d)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=rnd.uniform(0.17, 0.24), location=(bx + math.cos(a) * d, math.sin(a) * d * 0.7, z))
            c = bpy.context.active_object
            c.name = f"Bush{b}_{i}"
            for v in c.data.vertices:
                v.co *= 1 + rnd.uniform(-0.15, 0.15)
            for f in c.data.polygons:
                f.use_smooth = True
            _finish(c, rose_leaf[i % 2], 0)
        for r in range(3):
            a = r / 3 * 2 * math.pi + b + 0.5
            _bloom(f"Rose{b}{r}", (bx + math.cos(a) * 0.32, math.sin(a) * 0.24 - 0.05, H + 0.66 + rnd.uniform(-0.04, 0.06)), 0.15, petal, rose_leaf[0])
    for sx in (-1, 1):
        for k in range(6):
            leaf(f"Frond{sx}{k}", (sx * 2.75, rnd.uniform(-0.2, 0.2), H - 0.02), k / 6 * 2 * math.pi + rnd.uniform(-0.3, 0.3), math.radians(rnd.uniform(40, 60)),
                 rnd.uniform(0.6, 0.8), 0.13, 0.6, fern[k % 2], n=6, fold=0.3, thick=0.01)
    # ivy trailing over the front coping, moss, a crack and a stain
    _ivy("Ivy", [(1.4, -1.0, H + 0.15), (1.8, -1.42, H + 0.05), (1.9, -1.48, 1.0), (2.2, -1.47, 0.55), (2.4, -1.5, 0.3)], ivy, vine, rnd, count=22, size=0.14)
    _moss("MossFoot", [(x, sy * (D / 2 + 0.2), 0.3) for sy in (-1, 1) for x in [rnd.uniform(-2.9, 2.9) for _ in range(5)]], moss, rnd, 0.07)
    _moss("MossCap", [(rnd.uniform(-2.9, 2.9), sy * (D / 2 - 0.15), H + 0.15) for sy in (-1, 1) for _ in range(2)], moss, rnd, 0.06)
    _crack("Crack", (-0.8, -(D / 2 + 0.02), 1.25), (0.3, 0, -1), (1, 0, 0), 0.7, rnd, hol)
    _stain("Stain", (0.9, -(D / 2 + 0.02), 0.7), (1, 0, 0), (0, 0, 1), 0.3, 0.4, stain, rnd)
    return _dims()


# ================================================================== topiary
def topiary(M):
    stone, dark = castle()
    moss = mossy()
    soil = material("Soil", "NH_Limestone", tint=(0.1, 0.07, 0.05), scale=1.2, rough_add=0.35, wear=0.0, dirt=0.9)
    yews = [flat("Yew", (0.012, 0.035, 0.016), 0.92, dirt=0.75), flat("YewYoung", (0.02, 0.046, 0.017), 0.92, dirt=0.75)]
    core = flat("YewShade", (0.006, 0.016, 0.008), 0.9, dirt=0.5)
    bark = flat("Bark", (0.1, 0.065, 0.04), 0.9, dirt=0.8)
    rnd = random.Random(84)
    set_group("Main")
    # the tub: a plinth, a carved box with a lancet panel on each face, a moulded cap, crocketed corner pinnacles
    box("TubPlinth", (2.3, 2.3, 0.22), (0, 0, 0.11), dark, bevel=0.03)
    box("TubFoot", (2.05, 2.05, 0.1), (0, 0, 0.27), stone, bevel=0.02)
    box("Tub", (1.9, 1.9, 1.15), (0, 0, 0.88), stone, bevel=0.04)
    box("TubCap", (2.14, 2.14, 0.12), (0, 0, 1.5), dark, bevel=0.03)
    for k in range(4):
        s = _mark()
        _panel(f"TubPanel{k}", 0, 0, 0.42, 1.25, 0.92, dark, thick=0.03)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z") @ Matrix.Translation((0, -0.962, 0)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            _spirelet(f"Pin{sx}{sy}", sx * 0.98, sy * 0.98, 1.56, 0.62, 0.2, stone)
    box("Soil", (1.65, 1.65, 0.06), (0, 0, 1.54), soil, bevel=0.005)
    tube("Trunk", [(0, 0, 1.54), (0.02, 0.01, 3.0), (-0.01, 0, 4.5), (0, 0, 5.6)], 0.08, bark)
    # three clipped tiers and a tip: a dark core under a skin of small rounded clumps
    golden = math.pi * (3 - math.sqrt(5))
    for t, (r, z) in enumerate(((0.95, 2.6), (0.72, 4.0), (0.5, 5.1), (0.26, 5.77))):
        sphere(f"Core{t}", r * 0.9, (0, 0, z), core, seg=12, rings=6)
        n = int(48 * r * r) + 5
        for i in range(n):
            dz = 1 - 2 * (i + 0.5) / n
            rr = math.sqrt(max(0.0, 1 - dz * dz))
            phi = i * golden + rnd.uniform(-0.1, 0.1)
            d = Vector((math.cos(phi) * rr, math.sin(phi) * rr, dz))
            root = Vector((0, 0, z)) + d * r * rnd.uniform(0.84, 0.9)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=r * rnd.uniform(0.34, 0.4), location=tuple(root + d * r * 0.02))
            c = bpy.context.active_object
            c.name = f"Clump{t}_{i}"
            for v in c.data.vertices:
                v.co *= 1 + rnd.uniform(-0.12, 0.12)
            c.scale = (1, 1, 0.8)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            for f in c.data.polygons:
                f.use_smooth = True
            _finish(c, yews[i % 2], 0)
    _moss("MossTub", [(sx * 1.14, rnd.uniform(-1, 1), 0.24) for sx in (-1, 1) for _ in range(3)], moss, rnd, 0.09)
    return _dims()


# ================================================================== sundial
def sundial(M):
    stone, dark = castle()
    moss, hol = mossy(), hollow()
    crow = flat("Crow", (0.012, 0.012, 0.016), 0.35, dirt=0.4)
    rnd = random.Random(85)
    set_group("Main")
    lathe("Step0", [(0, 0), (1.15, 0), (1.15, 0.25), (0, 0.25)], dark, seg=8)
    lathe("Step1", [(0, 0.25), (0.86, 0.25), (0.86, 0.45), (0, 0.45)], stone, seg=8)
    lathe("BaseMould", [(0, 0.45), (0.62, 0.45), (0.62, 0.55), (0.52, 0.64), (0.46, 0.76), (0, 0.76)], dark, seg=8)
    # clustered colonnettes round a core, an annulet, a foliage capital
    z0, z1 = 0.76, 2.52
    cyl("Core", 0.2, z1 - z0, (0, 0, (z0 + z1) / 2), stone, verts=8, bevel=0)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cyl(f"Colonnette{k}", 0.085, z1 - z0, (math.cos(a) * 0.25, math.sin(a) * 0.25, (z0 + z1) / 2), stone, verts=8, bevel=0)
        cyl(f"ColBase{k}", 0.12, 0.1, (math.cos(a) * 0.25, math.sin(a) * 0.25, z0 + 0.05), dark, verts=8, bevel=0)
    cyl("Annulet", 0.36, 0.07, (0, 0, 1.64), dark, verts=8, bevel=0)
    lathe("Capital", [(0, z1 - 0.02), (0.36, z1 - 0.02), (0.5, z1 + 0.12), (0.62, z1 + 0.26), (0, z1 + 0.26)], dark, seg=8)
    _crockets("CapLeaf", [(math.cos(a) * 0.48, math.sin(a) * 0.48, z1 + 0.12) for a in [k / 8 * 2 * math.pi + math.pi / 8 for k in range(8)]], stone, 0.07)
    lathe("Top", [(0, z1 + 0.26), (0.74, z1 + 0.26), (0.76, z1 + 0.33), (0.72, z1 + 0.42), (0, z1 + 0.42)], stone, seg=8)
    zd = z1 + 0.42
    # the brass dial: rim, rings, hour marks, a compass rose
    cyl("Dial", 0.6, 0.04, (0, 0, zd + 0.02), M["brass"], verts=48, bevel=0.008)
    hoop("DialRim", (0, 0, zd + 0.04), 0.6, "Z", M["brass"], thick=0.02)
    hoop("DialRing", (0, 0, zd + 0.042), 0.4, "Z", M["glass"], thick=0.005)
    hoop("DialRing2", (0, 0, zd + 0.042), 0.53, "Z", M["glass"], thick=0.004)
    for k in range(24):
        a = k / 24 * 2 * math.pi
        big = k % 2 == 0
        box(f"Hour{k}", (0.11 if big else 0.06, 0.02 if big else 0.012, 0.006), (math.cos(a) * 0.465, math.sin(a) * 0.465, zd + 0.044), M["glass"],
            bevel=0.0, segments=1, rot=(0, 0, a))
    for k in range(8):
        a = k / 8 * 2 * math.pi
        ln = 0.26 if k % 2 == 0 else 0.15
        prism(f"Rose{k}", [(0.0, 0.0), (ln, -0.025), (ln + 0.02, 0.0), (ln, 0.025)], zd + 0.04, 0.004, M["glass"], plane="XY")
        _xform(len(P.PARTS) - 1, Matrix.Rotation(a, 4, "Z"))
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        sphere(f"Stud{k}", 0.03, (math.cos(a) * 0.57, math.sin(a) * 0.57, zd + 0.05), M["brass"], seg=8, rings=4)
    # a pierced gothic gnomon
    s = _mark()
    prism("Gnomon", [(-0.36, 0.0), (0.42, 0.0), (0.42, 0.05), (0.12, 0.3), (-0.08, 0.5), (-0.18, 0.52), (-0.24, 0.46), (-0.36, 0.08)], 0.0, 0.04,
          M["brass"], plane="YZ", bevel=0.004)
    for side in (-1, 1):
        q = _mark()
        _foil(f"GnomonFoil{side}", 0, 0, 0, 0.08, hol, thick=0.01)
        _xform(q, Matrix.Translation((side * 0.022, -0.06, 0.24)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    sphere("GnomonKnob", 0.035, (0, -0.2, 0.53), M["brass"], seg=8, rings=4)
    _xform(s, Matrix.Translation((0, 0, zd + 0.04)))
    # a crow perched on the rim, moss on the steps, a crack in the top step
    _raven("Crow", Matrix.Translation((0.42, -0.4, zd + 0.06)) @ Matrix.Rotation(math.radians(-150), 4, "Z") @ Matrix.Scale(0.9, 4), crow, M["brass"])
    _moss("MossStep", [(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.26) for a in [rnd.uniform(0, 2 * math.pi) for _ in range(6)]], moss, rnd, 0.09)
    _crack("Crack", (-0.5, -0.8, 0.44), (1, -0.1, 0), (0, 1, 0), 0.6, rnd, hol)
    return _dims()


# ================================================================== well
def well(M):
    stone, dark = castle()
    moss, hol, ivy = mossy(), hollow(), ivies()
    vine = flat("Vine", (0.05, 0.04, 0.025), 0.9)
    staves = flat("BucketWood", (0.1, 0.06, 0.035), 0.75, dirt=0.8)
    deep = flat("WellWater", (0.006, 0.01, 0.014), 0.03)
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)
    rnd = random.Random(86)
    lanterns = []
    set_group("Main")
    # the wellhead: a moulded base, a carved band of trefoils, a coping with a roll
    lathe("Wall", [(0, 0), (1.66, 0), (1.66, 0.12), (1.56, 0.2), (1.55, 0.66), (1.62, 0.7), (1.62, 1.02), (1.55, 1.06), (1.55, 1.2), (1.7, 1.28),
                   (1.74, 1.42), (1.62, 1.5), (1.25, 1.5), (1.2, 1.42), (1.2, 0.3), (0, 0.3)], stone, seg=40)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        s = _mark()
        _foil(f"Band{k}", 0, 0, 0, 0.12, dark, lobes=3, thick=0.02)
        _xform(s, _rotz((math.cos(a) * 1.625, math.sin(a) * 1.625, 0.86), a + math.pi / 2))
    lathe("Water", [(0, 0.42), (1.21, 0.42), (1.21, 0.44), (0, 0.44)], deep, seg=32)
    # the wrought-iron canopy: two posts, pointed gables with scrolls and a ring, a steep slate roof with cresting
    for sx in (-1, 1):
        x = sx * 1.42
        tube(f"Post{sx}", [(x, 0, 1.45), (x, 0, 4.15)], 0.07, M["iron"], square=True, poly=True)
        box(f"Foot{sx}", (0.3, 0.3, 0.1), (x, 0, 1.5), M["iron"], bevel=0.02)
        for sy in (-1, 1):
            tube(f"Brace{sx}{sy}", [(x, 0, 3.3), (x, sy * 0.7, 3.9), (x, sy * 1.25, 4.15)], 0.035, M["iron"])
            tube(f"Scroll{sx}{sy}", [(x, sy * 0.15, 3.55), (x, sy * 0.45, 3.62), (x, sy * 0.5, 3.45), (x, sy * 0.36, 3.42)], 0.02, M["iron"])
            tube(f"LowBrace{sx}{sy}", [(x, sy * 0.05, 2.0), (x, sy * 0.6, 1.52)], 0.035, M["iron"], square=True, poly=True)
        tube(f"Tie{sx}", [(x, -1.3, 4.15), (x, 1.3, 4.15)], 0.04, M["iron"], square=True, poly=True)
        tube(f"Gable{sx}", [(x, -1.3, 4.15), (x, -0.75, 4.75), (x, 0, 5.55), (x, 0.75, 4.75), (x, 1.3, 4.15)], 0.045, M["iron"])
        tube(f"GableRing{sx}", circle_pts(x, 0, 4.6, 0.26, "X", 12), 0.02, M["iron"], closed=True, square=True, poly=True)
        for k, (dy, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
            tube(f"GableFoil{sx}{k}", circle_pts(x, dy * 0.13, 4.6 + dz * 0.13, 0.11, "X", 8), 0.014, M["iron"], closed=True, square=True, poly=True)
        for sy in (-1, 1):
            tube(f"GableCurl{sx}{sy}", [(x, sy * 0.95, 4.2), (x, sy * 0.9, 4.45), (x, sy * 0.7, 4.5), (x, sy * 0.66, 4.36)], 0.016, M["iron"])
    tube("Beam", [(-1.5, 0, 4.15), (1.5, 0, 4.15)], 0.06, M["iron"], square=True, poly=True)
    ang = math.atan2(1.4, 1.32)
    for sy in (-1, 1):
        box(f"Roof{sy}", (3.5, 1.98, 0.08), (0, sy * 0.68, 4.86), M["slate"], bevel=0.015, rot=(-sy * ang, 0, 0))
    tube("Ridge", [(-1.78, 0, 5.6), (1.78, 0, 5.6)], 0.055, M["iron"], poly=True)
    for k in range(9):
        x = -1.6 + k * 0.4
        _spike(f"Cresting{k}", (x, 0, 5.72), 0.04, 0.18, M["iron"])
        sphere(f"CrestBall{k}", 0.025, (x, 0, 5.66), M["iron"], seg=6, rings=3)
    for sx in (-1, 1):
        cone(f"Finial{sx}", 0.07, 0.0, 0.4, (sx * 1.78, 0, 5.82), M["iron"], verts=8)
        sphere(f"FinialBall{sx}", 0.06, (sx * 1.78, 0, 5.62), M["brass"], seg=8, rings=4)
    # the windlass with its chain, a crank, an iron-banded bucket
    tube("Axle", [(-1.5, 0, 3.1), (1.62, 0, 3.1)], 0.04, M["iron"], poly=True)
    cyl("Drum", 0.17, 1.5, (0, 0, 3.1), M["iron"], rot=(0, math.pi / 2, 0), verts=20, bevel=0)
    for k in range(7):
        cyl(f"Wound{k}", 0.2, 0.05, (-0.5 + k * 0.15, 0, 3.1), M["iron"], rot=(0, math.pi / 2, 0), verts=12, bevel=0)
    tube("Crank", [(1.62, 0, 3.1), (1.62, 0, 2.75), (1.86, 0, 2.75)], 0.03, M["iron"], poly=True)
    sphere("CrankKnob", 0.05, (1.88, 0, 2.75), M["brass"], seg=8, rings=4)
    for k in range(9):
        _link(f"Chain{k}", (0.1, -0.2, 3.0 - k * 0.1), "X" if k % 2 else "Y", 0.045, M["iron"])
    bz = 1.7
    lathe("Bucket", [(0, bz), (0.22, bz), (0.3, bz + 0.38), (0.27, bz + 0.38), (0.2, bz + 0.05), (0, bz + 0.05)], staves, seg=24, loc=(0.1, -0.2, 0),
          flute=(12, 0.04))
    for z in (bz + 0.06, bz + 0.3):
        cyl(f"BucketBand{z:.2f}", 0.23 + (z - bz) * 0.21, 0.035, (0.1, -0.2, z), M["iron"], verts=24, bevel=0)
    tube("Bail", [(-0.19, -0.2, bz + 0.36), (0.1, -0.2, bz + 0.52), (0.39, -0.2, bz + 0.36)], 0.015, M["iron"])
    # a lantern on a scrolled bracket at the front corner
    tube("LanternArm", [(1.42, 0, 3.75), (1.6, -0.3, 3.85), (1.75, -0.6, 3.8)], 0.03, M["iron"])
    tube("LanternCurl", [(1.42, 0, 3.55), (1.55, -0.25, 3.62), (1.6, -0.35, 3.75)], 0.018, M["iron"])
    _lantern("Lantern", Matrix.Translation((1.75, -0.6, 3.0)), M, lanterns, wax)
    # ivy up the wellhead and a post, moss
    _ivy("Ivy", [(-1.4, -0.95, 0.05), (-1.25, -0.98, 0.7), (-1.35, -0.82, 1.3), (-1.42, -0.12, 1.55), (-1.43, -0.08, 2.4), (-1.43, 0.05, 3.1)], ivy, vine,
         rnd, count=30)
    _moss("MossFoot", _ring_pts(1.72, 0.03, 12, rnd), moss, rnd, 0.12)
    _moss("MossCope", _ring_pts(1.5, 1.5, 5, rnd), moss, rnd, 0.07)
    _lights(lanterns, M)
    return _dims()


# ================================================================== balustrade
def balustrade(M):
    stone, dark = castle()
    moss, hol, stain = mossy(), hollow(), staining()
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)
    rnd = random.Random(87)
    lanterns = []
    set_group("Main")
    W = 8.0
    box("Plinth", (W, 0.72, 0.35), (0, 0, 0.175), dark, bevel=0.04)
    box("BaseRail", (W - 1.5, 0.56, 0.2), (0, 0, 0.45), stone, bevel=0.03)
    # buttressed posts with crocketed pinnacles
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.4)
        box(f"Post{sx}", (0.8, 0.8, 2.5), (x, 0, 0.35 + 1.25), stone, bevel=0.04)
        box(f"PostFoot{sx}", (0.9, 0.9, 0.25), (x, 0, 0.47), dark, bevel=0.03)
        box(f"PostCap{sx}", (0.95, 0.95, 0.18), (x, 0, 2.94), dark, bevel=0.04)
        _spirelet(f"PostPin{sx}", x, 0, 3.03, 1.15, 0.5, stone, crockets=3)
        for face in (-1, 1):
            s = _mark()
            _lancet(f"PostLancet{sx}{face}", 0, 0, 0.85, 0.2, 2.0, 2.55, dark, thick=0.03)
            _xform(s, Matrix.Translation((x, face * 0.405, 0)) @ Matrix.Rotation(0 if face < 0 else math.pi, 4, "Z"))
    # the pierced arcade: six trefoil-headed lancets between mullions, roundels in the spandrels
    x0, x1 = -(W / 2 - 0.8), W / 2 - 0.8
    n = 6
    bay = (x1 - x0) / n
    for k in range(n + 1):
        x = x0 + k * bay
        if 0 < k < n:
            box(f"Mullion{k}", (0.16, 0.34, 1.62), (x, 0, 0.55 + 0.81), stone, bevel=0.025)
    for k in range(n):
        cx = x0 + (k + 0.5) * bay
        for face in (-1, 1):
            _lancet(f"Arch{k}{face}", cx, face * 0.11, 0.55, bay / 2 - 0.08, 1.55, 2.4, stone, thick=0.075, cusp=(face < 0))
        if k < n - 1:
            _foil(f"Roundel{k}", cx + bay / 2, -0.12, 2.42, 0.13, dark)
    box("RailBed", (x1 - x0, 0.5, 0.1), (0, 0, 2.53), dark, bevel=0.015)
    box("Rail", (x1 - x0 + 0.1, 0.66, 0.24), (0, 0, 2.7), stone, bevel=0.04)
    box("RailDrip", (x1 - x0, 0.72, 0.05), (0, 0, 2.6), dark, bevel=0.012)
    # an iron lantern on the right post
    tube("LanternArm", [(x1 + 0.4, -0.4, 2.6), (x1 + 0.4, -0.75, 2.75), (x1 + 0.4, -0.95, 2.72)], 0.03, M["iron"])
    tube("LanternCurl", [(x1 + 0.4, -0.4, 2.35), (x1 + 0.4, -0.62, 2.42), (x1 + 0.4, -0.72, 2.6)], 0.018, M["iron"])
    box("LanternPlate", (0.22, 0.04, 0.42), (x1 + 0.4, -0.41, 2.48), M["iron"], bevel=0.01)
    _lantern("Lantern", Matrix.Translation((x1 + 0.4, -0.95, 2.0)), M, lanterns, wax)
    # weathering
    _moss("MossFoot", [(rnd.uniform(-3.9, 3.9), sy * 0.42, 0.36) for sy in (-1, 1) for _ in range(4)], moss, rnd, 0.09)
    _moss("MossRail", [(rnd.uniform(-3.0, 3.0), rnd.uniform(-0.2, 0.2), 2.83) for _ in range(3)], moss, rnd, 0.07)
    _crack("Crack", (-1.2, -0.34, 2.75), (0.4, 0, -1), (1, 0, 0), 0.3, rnd, hol, n=3)
    _stain("Stain", (-(W / 2 - 0.4), -0.42, 1.2), (1, 0, 0), (0, 0, 1), 0.28, 0.6, stain, rnd)
    _lights(lanterns, M)
    return _dims()


# ================================================================== memorial
def memorial(M):
    stone, dark = castle()
    moss, hol, stain, ivy = mossy(), hollow(), staining(), ivies()
    vine = flat("Vine", (0.05, 0.04, 0.025), 0.9)
    greens = [flat("Laurel", (0.02, 0.05, 0.02), 0.5, dirt=0.7), flat("LaurelOld", (0.03, 0.055, 0.018), 0.55, dirt=0.8)]
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)
    rnd = random.Random(88)
    set_group("Main")
    for k, (w, mat) in enumerate(((3.4, dark), (2.7, stone), (2.1, stone))):
        box(f"Step{k}", (w, w, 0.3), (0, 0, 0.15 + k * 0.3), mat, bevel=0.04)
    # the die with corner buttresses and pinnacles
    zd0, zd1 = 0.9, 2.3
    box("Die", (1.6, 1.6, zd1 - zd0), (0, 0, (zd0 + zd1) / 2), stone, bevel=0.03)
    box("DieBase", (1.8, 1.8, 0.14), (0, 0, zd0 + 0.07), dark, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Buttress{sx}{sy}", (0.34, 0.34, 1.45), (sx * 0.86, sy * 0.86, zd0 + 0.72), stone, bevel=0.03)
            _spirelet(f"Pin{sx}{sy}", sx * 0.86, sy * 0.86, zd0 + 1.45, 0.85, 0.3, stone)
    box("DieCornice", (1.86, 1.86, 0.18), (0, 0, zd1 + 0.09), dark, bevel=0.04)
    # the canopied niche on the front: a dark recess in a pointed frame, the plaque, a crocketed gable
    yf = -0.8
    hw, ns, na = 0.42, 1.65, 2.12
    prism("NicheBack", [(-hw, 1.02)] + _pointed(hw, ns, na, 8) + [(hw, 1.02)], yf - 0.003, 0.012, hol)
    tube("NicheFrame", [(-hw - 0.04, yf - 0.03, 1.0)] + [(x, yf - 0.03, z) for x, z in _pointed(hw + 0.04, ns, na + 0.04, 8)] + [(hw + 0.04, yf - 0.03, 1.0)],
         0.045, dark, closed=True, square=True, poly=True)
    box("Sill", (2 * hw + 0.2, 0.18, 0.08), (0, yf - 0.06, 0.99), dark, bevel=0.02)
    box("Plaque", (0.6, 0.03, 0.44), (0, yf - 0.03, 1.4), M["brass"], bevel=0.01)
    tube("PlaqueRim", [(-0.28, yf - 0.05, 1.2), (0.28, yf - 0.05, 1.2), (0.28, yf - 0.05, 1.6), (-0.28, yf - 0.05, 1.6)], 0.01, M["brass"], closed=True, poly=True)
    for k in range(4):
        box(f"PlaqueLine{k}", (0.42 - k * 0.06, 0.008, 0.02), (0, yf - 0.048, 1.52 - k * 0.09), M["glass"], bevel=0.0, segments=1)
    _gable("Canopy", 0, yf - 0.06, 0.62, 2.12, 2.85, 0.14, stone, dark, edge=0.03)
    _crockets("CanopyCrocket", [(x, yf - 0.1, 2.12 + (2.85 - 2.12) * (0.45 * t + 0.55 * math.sin(t * math.pi / 2)) + 0.06)
                                for sxx in (-1, 1) for t in (0.3, 0.55, 0.8) for x in [sxx * 0.62 * (1 - t)]], stone, 0.05)
    sphere("CanopyFinial", 0.07, (0, yf - 0.06, 2.92), stone, seg=8, rings=4, scale=(1, 1, 1.4))
    _foil("CanopyFoil", 0, yf - 0.14, 2.42, 0.12, dark, lobes=3)
    # the traceried octagonal shaft, a crocketed spire and an iron cross
    zs0, zs1 = zd1 + 0.18, 5.6
    lathe("Shaft", [(0, zs0), (0.58, zs0), (0.46, zs1), (0, zs1)], stone, seg=8)
    rf = 0.52 * math.cos(math.pi / 8)
    for k in range(4):
        a = k * math.pi / 2 - math.pi / 2 + math.pi / 8 * 0
        s = _mark()
        _lancet(f"ShaftLancet{k}", 0, 0, zs0 + 0.5, 0.13, zs0 + 2.2, zs0 + 2.6, dark, thick=0.025)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z") @ Matrix.Translation((0, -(rf + 0.01), 0)))
    lathe("ShaftCornice", [(0, zs1 - 0.02), (0.5, zs1 - 0.02), (0.62, zs1 + 0.1), (0.58, zs1 + 0.18), (0, zs1 + 0.18)], dark, seg=8)
    zp0, zp1 = zs1 + 0.18, 8.4
    cone("Spire", 0.52, 0.0, zp1 - zp0, (0, 0, (zp0 + zp1) / 2), stone, verts=8, rot=(0, 0, math.pi / 8))
    pts = []
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        for t in (0.3, 0.62):
            rr = 0.52 * (1 - t) * math.cos(math.pi / 8) + 0.02
            pts.append((math.cos(a) * rr, math.sin(a) * rr, zp0 + (zp1 - zp0) * t))
    _crockets("SpireCrocket", pts, stone, 0.055)
    box("CrossStem", (0.07, 0.07, 0.62), (0, 0, zp1 + 0.27), M["iron"], bevel=0.01)
    box("CrossArm", (0.36, 0.07, 0.07), (0, 0, zp1 + 0.38), M["iron"], bevel=0.01)
    for p in ((0, 0, zp1 + 0.6), (0.19, 0, zp1 + 0.38), (-0.19, 0, zp1 + 0.38)):
        sphere(f"CrossEnd{p[0]:.2f}{p[2]:.2f}", 0.04, p, M["brass"], seg=8, rings=4)
    tube("CrossRing", circle_pts(0, 0, zp1 + 0.38, 0.11, "Y", 12), 0.014, M["iron"], closed=True, square=True, poly=True)
    # a laurel wreath with a crimson ribbon, leaning on the right of the die
    s = _mark()
    r = 0.38
    hoop("WreathBand", (0, 0, 0), r, "Z", greens[0], thick=0.045)
    for k in range(24):
        a = k / 24 * 2 * math.pi
        rr = r + rnd.uniform(-0.05, 0.05)
        leaf(f"Laurel{k}", (math.cos(a) * rr, math.sin(a) * rr, 0.02), a + math.pi / 2 + rnd.uniform(-0.3, 0.3), math.radians(rnd.uniform(5, 25)), 0.18, 0.065,
             0.1, greens[k % 2], n=3, fold=0.3, thick=0.008)
    for k in range(8):
        a = rnd.uniform(0, 2 * math.pi)
        sphere(f"Berry{k}", 0.024, (math.cos(a) * r, math.sin(a) * r, 0.05), M["crimson"], seg=6, rings=4)
    for sx in (-1, 1):
        strip(f"Ribbon{sx}", [(0, -r, 0.05), (sx * 0.08, -r - 0.2, 0.05), (sx * 0.14, -r - 0.42, 0.04)], 0.075, (1, 0, 0), M["crimson"], thick=0.01)
    sphere("Bow", 0.06, (0, -r, 0.06), M["crimson"], seg=8, rings=4, scale=(1.6, 1, 0.6))
    _xform(s, Matrix.Translation((1.12, -0.1, zd0 + r * 0.95)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Rotation(math.radians(72), 4, "X"))
    # three votive candles in crimson cups on the top step
    flames = []
    for k, (vx, vy) in enumerate(((-0.55, -0.92), (0.0, -0.98), (0.55, -0.92))):
        vz = 0.9
        lathe(f"Votive{k}", [(0, vz), (0.09, vz), (0.11, vz + 0.02), (0.11, vz + 0.18), (0.09, vz + 0.18), (0.08, vz + 0.04), (0, vz + 0.04)], M["crimson"],
              seg=14, loc=(vx, vy, 0))
        cyl(f"VotiveWax{k}", 0.07, 0.11, (vx, vy, vz + 0.095), wax, verts=12, bevel=0)
        tube(f"VotiveWick{k}", [(vx, vy, vz + 0.15), (vx, vy, vz + 0.19)], 0.006, M["felt"], poly=True)
        flames.append(((vx, vy, vz + 0.18), 0.12))
    # a low iron railing with spear tips round the plinth (open at the front)
    rr = 1.95
    posts = []
    for side in range(4):
        for i in range(11):
            t = -1 + i * 0.2
            p = [(t * rr, -rr), (rr, t * rr), (-t * rr, rr), (-rr, -t * rr)][side]
            if side == 0 and abs(p[0]) < 0.45:
                continue
            posts.append(p)
    for k, (x, y) in enumerate(posts):
        corner = abs(abs(x) - rr) < 1e-6 and abs(abs(y) - rr) < 1e-6
        tube(f"Rail{k}", [(x, y, 0.02), (x, y, 0.95 if corner else 0.82)], 0.03 if corner else 0.018, M["iron"], square=True, poly=True)
        if corner:
            sphere(f"RailBall{k}", 0.06, (x, y, 1.0), M["brass"], seg=8, rings=4)
        else:
            _spike(f"RailSpear{k}", (x, y, 0.88), 0.035, 0.12, M["iron"])
    for z in (0.25, 0.75):
        tube(f"RailBar{z}", [(-0.45, -rr, z), (-rr, -rr, z), (-rr, rr, z), (rr, rr, z), (rr, -rr, z), (0.45, -rr, z)], 0.02, M["iron"], square=True, poly=True)
    # weathering and ivy
    _ivy("Ivy", [(-1.6, -1.65, 0.05), (-1.3, -1.32, 0.4), (-1.0, -1.02, 0.7), (-0.95, -0.82, 1.2), (-0.98, -0.82, 1.8), (-0.88, -0.84, 2.3)], ivy, vine,
         rnd, count=18, size=0.15)
    _moss("MossStep", [(rnd.uniform(-1.6, 1.6), sy * 1.62, 0.31) for sy in (-1, 1) for _ in range(3)] +
          [(sx * 1.62, rnd.uniform(-1.5, 1.5), 0.31) for sx in (-1, 1) for _ in range(2)], moss, rnd, 0.1)
    _crack("Crack", (0.55, -0.81, 2.2), (0.15, 0, -1), (1, 0, 0), 0.8, rnd, hol)
    _stain("Stain", (-0.6, -0.81, 1.5), (1, 0, 0), (0, 0, 1), 0.12, 0.5, stain, rnd)
    _lights([], M, flames)
    return _dims()


P.PREVIEW_PAD.update({"CloisterArch": 1.1, "CloisterArchNoLamp": 1.1, "Topiary": 1.2, "Sundial": 1.15, "Well": 1.1, "Memorial": 1.25, "Balustrade": 1.0})

P.TILED.update({"CloisterArch_Wall": ("NH_CastleStone", 8.0), "CloisterArchNoLamp_Wall": ("NH_CastleStone", 8.0)})

P.BUILD.update({
    "Fountain": fountain,
    "CloisterArch": cloister_arch,
    "CloisterArchNoLamp": lambda M: cloister_arch(M, lantern=False),
    "StonePlanter": stone_planter,
    "Topiary": topiary,
    "Sundial": sundial,
    "Well": well,
    "Balustrade": balustrade,
    "Memorial": memorial,
})
