"""Props batch 42 (2026-11-09): the indoor lighting kit for nh_props.py. Thirty-two light fittings to brighten the
school's halls, classrooms and corridors, each with its own silhouette and one signature idea, none repeating the
lights the school already has (batch 19's lamp kit, the dorm, library and lounge lights). Black wrought iron, gilt and
aged brass, crimson enamel, bone, dark oak, alabaster and wax; warm candle and gas light by default, with four cool
pieces (moonlight blue and violet).

Every prop has a `_Glow` piece (the flames, bulbs, mantles or lit glass) that the template script turns to Neon and
lights with the Roblox light given in LIGHTS below (the docs section is generated from it). Lanterns have `_Glass`,
the mirror sconce has `_Mirror` and the stained lightbox has `_Stained` (a painted canvas with an emissive mask, like
the window kit's stained glass, painted by E:/NH-Work/props42/lightbox_glass.py).

Ceiling pieces are modelled hanging with their top at the ceiling (pivot at the bottom centre, as batch 19): the
drop is their height. Wall pieces have their back face on y = 0 (the pivot is the bottom centre of the back face)
and stand out toward -Y. Floor and table pieces stand on z = 0, front toward -Y.

Registered into nh_props.BUILD on import (E:/NH-Work/props42/run42.py imports it).
"""
import math
import random
import sys
import os

from mathutils import Matrix, Vector, Quaternion
import bmesh
import bpy

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere, cone, circle_pts, flame
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _aim, _dims, flat, _mesh, leaf
from nh_props_batch5 import marble
from nh_props_batch9 import foil, candle, wax_mat, twist, stiff_leaf, raven, tracery
from nh_props_batch10 import gilt, lacquer, black_marble, tongue
from nh_props_batch13 import ring_band, claw_foot
from nh_props_batch19 import _gothic, _shrink, bulb, mantle, fire, soot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import window_shapes as WS  # noqa: E402

TAU = 2 * math.pi


# ------------------------------------------------------------------ materials

def bone():
    return flat("Bone", (0.7, 0.64, 0.52), 0.55, dirt=0.85, wear=0.0)


def bronze():
    return material("Bronze", "NH_Brass", tint=(0.42, 0.29, 0.17), scale=0.5, wear=0.45, dirt=0.9)


def shade_lit(rgb=(0.86, 0.62, 0.36)):
    return flat("ShadeLit", rgb, 0.6, dirt=0.15)


def opal():
    return flat("Opal", (0.95, 0.9, 0.8), 0.35, dirt=0.05)


def glow_amber():
    return flat("LitAmber", (1.0, 0.62, 0.22), 0.4, dirt=0.05)


def glow_moon():
    return flat("Moonlit", (0.78, 0.86, 1.0), 0.5, dirt=0.1)


def glow_violet():
    return flat("Witchlight", (0.66, 0.42, 1.0), 0.4, dirt=0.05)


def glow_rose():
    return flat("RoseGlass", (1.0, 0.42, 0.36), 0.35, dirt=0.05)


def coal():
    return flat("Coals", (0.05, 0.035, 0.03), 0.95, dirt=0.4)


# ------------------------------------------------------------------ geometry helpers

def smooth_path(pts, per=4):
    """Catmull-Rom through the control points, `per` samples per span."""
    Pv = [Vector(p) for p in pts]
    if len(Pv) < 3:
        return Pv
    out = []
    for i in range(len(Pv) - 1):
        p0, p1, p2, p3 = Pv[max(i - 1, 0)], Pv[i], Pv[i + 1], Pv[min(i + 2, len(Pv) - 1)]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(Pv[-1])
    return out


def sweep(name, pts, r0, mat, r1=None, seg=8, per=4, flat_k=(1.0, 1.0), caps=True, up=None, prof=None):
    """A tapering tube along a smooth path (radius r0 at the start to r1 at the end, or a radius profile function
    prof(t)); flat_k squashes the section (normal, binormal); up fixes the first normal."""
    path = smooth_path(pts, per) if per > 1 else [Vector(p) for p in pts]
    n = len(path)
    r1 = r0 if r1 is None else r1
    T = []
    for i in range(n):
        a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    ref = Vector(up) if up else (Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0)))
    N = T[0].cross(ref).cross(T[0]).normalized() * -1
    if N.length < 1e-6:
        N = T[0].orthogonal().normalized()
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + (path[i] - path[i - 1]).length)
    tot = L[-1] or 1.0
    for i in range(n):
        if i:
            N = (N - T[i] * N.dot(T[i]))
            N = N.normalized() if N.length > 1e-6 else T[i].orthogonal().normalized()
        B = T[i].cross(N)
        t = L[i] / tot
        r = prof(t) if prof else r0 + (r1 - r0) * t
        r = max(r, 0.002)
        rings.append([bm.verts.new(path[i] + (N * math.cos(a) * flat_k[0] + B * math.sin(a) * flat_k[1]) * r)
                      for a in [k / seg * TAU for k in range(seg)]])
    for A, Bq in zip(rings, rings[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0)


def chain(prefix, x, y, z0, z1, mat, pitch=0.15, r=0.045, h=0.08, thick=0.011):
    """Square-section iron chain links hanging straight from z1 down to z0 at (x, y)."""
    z, k = z0, 0
    while z < z1 - pitch * 0.5:
        rot = Matrix.Rotation((k % 2) * math.pi / 2, 4, "Z")
        pts = [(math.cos(t) * r, 0, math.sin(t) * h) for t in [i / 8 * TAU for i in range(8)]]
        s = _mark()
        tube(f"{prefix}{k}", pts, thick, mat, closed=True, square=True, poly=True)
        _xform(s, Matrix.Translation((x, y, z + h)) @ rot)
        z += pitch
        k += 1


def ceil_rose(prefix, z, r, iron, gl, seg=32):
    """A ceiling rose whose top is at z."""
    lathe(prefix, [(0.04, z - 0.2), (r * 0.35, z - 0.18), (r * 0.62, z - 0.12), (r * 0.9, z - 0.06), (r, z - 0.03), (r, z), (0, z)], iron, seg=seg)
    hoop(f"{prefix}Gilt", (0, 0, z - 0.09), r * 0.78, "Z", gl, thick=0.012)
    lathe(f"{prefix}Hook", [(0, z - 0.3), (0.035, z - 0.28), (0.04, z - 0.2), (0, z - 0.19)], iron, seg=10)


def light_candle(prefix, x, y, z, h, wax, r=0.045, seed=0):
    """A lighter pillar candle than batch 9's (a turned lathe with a wax lip and a drip run, a square wick); returns the wick top."""
    rnd = random.Random(seed + int(h * 1000))
    lathe(f"{prefix}Wax", [(0, z), (r, z), (r * 1.0, z + h * 0.6), (r * 0.98, z + h - 0.01), (r * 0.8, z + h), (r * 0.3, z + h - 0.012), (0, z + h - 0.012)],
          wax, seg=8, loc=(x, y, 0))
    a = rnd.uniform(0, TAU)
    sphere(f"{prefix}Drip", r * 0.4, (x + math.cos(a) * r * 0.95, y + math.sin(a) * r * 0.95, z + h - 0.07), wax, seg=5, rings=3, scale=(1, 1, 2.4))
    tube(f"{prefix}Wick", [(x, y, z + h - 0.012), (x, y, z + h + 0.035)], 0.007, flat("Wick", (0.02, 0.02, 0.02), 0.8), square=True, poly=True)
    return z + h


def cup_candle(prefix, x, y, z, h, wax, pan_mat, r=0.045, pan=0.09, sleeve=None):
    """A drip pan (and optional enamel sleeve) with a candle standing at z; returns the wick tip."""
    lathe(f"{prefix}Pan", [(0, z - 0.04), (pan * 0.4, z - 0.035), (pan, z), (pan + 0.012, z + 0.022), (pan - 0.012, z + 0.026), (0, z + 0.018)],
          pan_mat, seg=8, loc=(x, y, 0))
    z0 = z + 0.02
    if sleeve is not None:
        lathe(f"{prefix}Sleeve", [(r + 0.016, z0), (r + 0.02, z0 + 0.03), (r + 0.012, z0 + 0.05), (r + 0.012, z0 + 0.2), (r + 0.02, z0 + 0.22),
                                  (0, z0 + 0.22)], sleeve, seg=10, loc=(x, y, 0))
        z0 += 0.22
        h = max(0.08, h - 0.2)
    tip = light_candle(f"{prefix}C", x, y, z0, h, wax, r=r)
    return (x, y, tip)


def flames(prefix, tips, h=0.12):
    """Candle flames, drawn a third bigger than batch 19's so they read (and glow) from across a room."""
    set_group("Glow")
    for k, p in enumerate(tips):
        flame(f"{prefix}{k}", p, h=h * 1.35)
    set_group("Main")


def ring_xy(cx, cy, r, n, a0=0.0):
    return [(cx + math.cos(a0 + k / n * TAU) * r, cy + math.sin(a0 + k / n * TAU) * r) for k in range(n)]


def sq_lantern(prefix, M, gl, mtx, glass_mat=None, w=0.36, h=0.62):
    """A small square gothic lantern (pierced quatrefoil crown, pyramid roof and ring, a pointed drop) with one candle,
    built with its cage floor at the origin; returns the flame tip (world)."""
    s = _mark()
    iron = M["iron"]
    hw = w / 2
    box(f"{prefix}Floor", (w + 0.04, w + 0.04, 0.05), (0, 0, 0.025), iron, bevel=0.01)
    lathe(f"{prefix}Drop", [(0, -0.3), (0.025, -0.26), (0.04, -0.16), (0.11, -0.06), (0.15, 0.0), (0, 0.0)], iron, seg=4)
    _xform(len(P.PARTS) - 1, Matrix.Rotation(math.pi / 4, 4, "Z"))
    sphere(f"{prefix}DropBall", 0.035, (0, 0, -0.32), gl, seg=8, rings=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"{prefix}Post{sx}{sy}", [(sx * hw, sy * hw, 0.04), (sx * hw, sy * hw, h)], 0.016, iron, square=True, poly=True)
    for k in range(4):
        rot = Matrix.Rotation(k * math.pi / 2, 4, "Z")
        g = _mark()
        tube(f"{prefix}Arch{k}", [(u, -hw, z) for u, z in _gothic(hw - 0.01, h - 0.2, h - 0.12, h - 0.03, n=6)][2:], 0.01, iron, square=True, poly=True)
        box(f"{prefix}Crown{k}", (w + 0.03, 0.025, 0.12), (0, -hw - 0.01, h + 0.06), iron, bevel=0.006)
        foil(f"{prefix}Foil{k}", 0, -hw - 0.026, h + 0.06, 0.04, gl, thick=0.007, n=6)
        _xform(g, rot)
    lathe(f"{prefix}Roof", [(hw * 1.5, h + 0.12), (hw * 1.2, h + 0.16), (0.05, h + 0.36), (0, h + 0.38)], iron, seg=4)
    _xform(len(P.PARTS) - 1, Matrix.Rotation(math.pi / 4, 4, "Z"))
    lathe(f"{prefix}Finial", [(0, h + 0.36), (0.03, h + 0.37), (0.025, h + 0.43), (0, h + 0.46)], gl, seg=8)
    tube(f"{prefix}Ring", circle_pts(0, 0, h + 0.52, 0.05, "X", 10), 0.012, iron, closed=True, poly=True)
    wax = wax_mat()
    cyl(f"{prefix}Pan", 0.09, 0.02, (0, 0, 0.06), M["brass"], verts=12, bevel=0.005)
    tip = light_candle(f"{prefix}C", 0, 0, 0.07, 0.2, wax, r=0.04)
    set_group("Glass")
    for k in range(4):
        g = _mark()
        _mesh(f"{prefix}Pane{k}", [[(-hw + 0.01, -hw + 0.004, 0.05), (hw - 0.01, -hw + 0.004, 0.05)],
                                   [(-hw + 0.01, -hw + 0.004, h - 0.02), (hw - 0.01, -hw + 0.004, h - 0.02)]], glass_mat or M["glassclear"], 0.006)
        _xform(g, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    set_group("Main")
    _xform(s, mtx)
    return mtx @ Vector((0, 0, tip))


def wing_feather(name, root, yaw, length, width, z, mat, thick=0.035, droop=0.0):
    """A long pointed feather lying in a horizontal plane from root toward angle yaw."""
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((length * t, width * math.sin(min(1, t * 1.3) * math.pi) ** 0.6 * (1 - t * 0.35) * 0.5))
    outline = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    s = _mark()
    prism(name, outline, 0, thick, mat, plane="XY")
    _xform(s, Matrix.Translation((root[0], root[1], z)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(droop, 4, "Y"))


# ================================================================== CHANDELIERS

def chandelier_great_wheel(M):
    """The great hall wheel: a 7-across iron cartwheel, 36 candles, a crimson hub with a gilt crest."""
    gl, iron, wax, cr = gilt(), M["iron"], wax_mat(), M["crimson"]
    R, z = 3.5, 1.4
    ring_band("Tyre", R - 0.06, R + 0.05, z - 0.13, z + 0.13, iron, seg=96)
    ring_band("Felloe", R - 0.2, R - 0.06, z - 0.09, z + 0.09, M["crimsonin"], seg=96)
    hoop("FelloeIn", (0, 0, z), R - 0.22, "Z", iron, thick=0.05)
    hoop("TyreBead", (0, 0, z + 0.13), R + 0.05, "Z", gl, thick=0.014)
    # twelve spokes, a mid ring with gilt bosses and scrolls in the bays
    Rm = R * 0.55
    hoop("MidRing", (0, 0, z), Rm, "Z", iron, thick=0.045)
    for k in range(12):
        a = k / 12 * TAU
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Spoke{k}", [(c * 0.45, s_ * 0.45, z), (c * (R - 0.24), s_ * (R - 0.24), z)], 0.05, iron, square=True, poly=True)
        lathe(f"SpokeKnop{k}", [(0, -0.09), (0.07, -0.06), (0.08, 0.0), (0.07, 0.06), (0, 0.09)], gl, seg=10)
        _xform(len(P.PARTS) - 1, Matrix.Translation((c * (R * 0.78), s_ * (R * 0.78), z)) @ _aim((c, s_, 0)))
        sphere(f"MidBoss{k}", 0.08, (c * Rm, s_ * Rm, z), gl, seg=10, rings=5)
        b = a + TAU / 24
        cb, sb = math.cos(b), math.sin(b)
        curl = [(Rm + 0.15, -0.0), (Rm + 0.45, 0.25), (Rm + 0.85, 0.2), (Rm + 1.0, -0.05), (Rm + 0.85, -0.2), (Rm + 0.7, -0.08)]
        tube(f"Scroll{k}", [(cb * r - sb * t, sb * r + cb * t, z) for r, t in curl], 0.022, iron, res=2)
    # the hub: a crimson drum with gilt bands, a turned pendant below with a crest
    lathe("Hub", [(0, z - 0.3), (0.45, z - 0.28), (0.5, z - 0.2), (0.5, z + 0.2), (0.45, z + 0.28), (0, z + 0.3)], cr, seg=32)
    for zz in (z - 0.2, z + 0.2):
        hoop(f"HubBand{zz:.2f}", (0, 0, zz), 0.505, "Z", gl, thick=0.02)
    lathe("Pendant", [(0, 0.0), (0.05, 0.06), (0.09, 0.2), (0.07, 0.34), (0.16, 0.5), (0.3, 0.72), (0.38, 0.92), (0.4, z - 0.28), (0, z - 0.28)],
          iron, seg=24)
    sphere("PendantBall", 0.08, (0, 0, 0.02), gl, seg=12, rings=6)
    for k in range(2):
        a = k / 2 * TAU
        g = _mark()
        foil(f"HubFoil{k}", 0, -0.51, z, 0.11, gl, thick=0.012, n=6)
        _xform(g, Matrix.Rotation(a, 4, "Z"))
    # 24 candles on the tyre, 12 on the mid ring
    tips = []
    for k in range(24):
        a = k / 24 * TAU
        x, y = math.cos(a) * (R - 0.08), math.sin(a) * (R - 0.08)
        tips.append(cup_candle(f"T{k}", x, y, z + 0.16, 0.36 + 0.05 * (k % 3), wax, M["brass"], r=0.05, pan=0.1))
        cone(f"TSpike{k}", 0.012, 0.0, 0.08, (x * 1.025, y * 1.025, z + 0.22), iron, verts=4)
    for k in range(8):
        a = (k + 0.5) / 8 * TAU
        x, y = math.cos(a) * Rm, math.sin(a) * Rm
        tips.append(cup_candle(f"M{k}", x, y, z + 0.06, 0.3, wax, M["brass"], r=0.045, pan=0.09, sleeve=cr))
    # suspension: four flat iron bars to a crown, a short chain to the rose
    zc = 6.7
    for k in range(4):
        a = (k + 0.5) / 4 * TAU
        c, s_ = math.cos(a), math.sin(a)
        p0, p1 = Vector((c * (R - 0.15), s_ * (R - 0.15), z + 0.14)), Vector((c * 0.18, s_ * 0.18, zc - 0.05))
        tube(f"Bar{k}", [tuple(p0), tuple(p1)], 0.03, iron, square=True, poly=True)
        for t in (0.33, 0.66):
            sphere(f"BarKnop{k}{t}", 0.06, tuple(p0.lerp(p1, t)), gl, seg=10, rings=5)
    tube("Mast", [(0, 0, z + 0.3), (0, 0, zc)], 0.05, iron, poly=True)
    lathe("MastKnop", [(0, 3.2), (0.1, 3.25), (0.14, 3.4), (0.1, 3.55), (0, 3.6)], gl, seg=16)
    lathe("Crown", [(0, zc - 0.15), (0.24, zc - 0.12), (0.3, zc), (0.24, zc + 0.12), (0, zc + 0.15)], iron, seg=20)
    hoop("CrownGilt", (0, 0, zc), 0.3, "Z", gl, thick=0.016)
    chain("Link", 0, 0, zc + 0.12, 7.9, iron)
    ceil_rose("Rose", 8.2, 0.42, iron, gl)
    flames("Flame", tips, h=0.13)
    return _dims()


def chandelier_antler(M):
    """Eight bone antler racks bound to an iron hub with candles on their tines (the Pack's)."""
    gl, iron, wax, bn = gilt(), M["iron"], wax_mat(), bone()
    rnd = random.Random(4207)
    zh = 1.5
    lathe("Hub", [(0, zh - 0.5), (0.18, zh - 0.48), (0.42, zh - 0.3), (0.55, zh - 0.12), (0.58, zh + 0.18), (0.48, zh + 0.32), (0.2, zh + 0.38), (0, zh + 0.4)],
          iron, seg=32)
    for zz in (zh - 0.1, zh + 0.12):
        hoop(f"Strap{zz:.2f}", (0, 0, zz), 0.59, "Z", gl, thick=0.02)
    lathe("Drop", [(0, 0.2), (0.04, 0.26), (0.08, 0.45), (0.06, 0.62), (0.12, 0.8), (0.18, zh - 0.48), (0, zh - 0.48)], iron, seg=16)
    # a gilt crescent hanging under the drop
    s = _mark()
    pts = [(math.cos(a) * 0.18, 0, math.sin(a) * 0.18) for a in [math.radians(200 + 140 * i / 12) for i in range(13)]]
    sweep("Crescent", pts, 0.035, gl, prof=lambda t: 0.012 + 0.035 * math.sin(t * math.pi), seg=8, per=1)
    _xform(s, Matrix.Translation((0, 0, 0.32)) @ Matrix.Rotation(math.pi, 4, "Y"))
    tips = []
    for k in range(8):
        a = k / 8 * TAU + 0.2
        c, s_ = math.cos(a), math.sin(a)
        side = 1 if k % 2 else -1

        def W(r, z, t=0.0):
            return (c * r - s_ * t, s_ * r + c * t, z)
        beam = [W(0.55, zh), W(0.95, zh - 0.06, 0.05 * side), W(1.4, zh + 0.02, 0.12 * side), W(1.85, zh + 0.3, 0.1 * side),
                W(2.15, zh + 0.75, 0.02 * side), W(2.25, zh + 1.15, -0.06 * side)]
        roughen(sweep(f"Beam{k}", beam, 0.1, bn, r1=0.03, seg=12, per=5), 0.012, 0.035)
        lathe(f"Burr{k}", [(0.0, -0.05), (0.12, -0.04), (0.14, 0.0), (0.12, 0.04), (0, 0.05)], bn, seg=10, jitter=(0.15, k))
        _xform(len(P.PARTS) - 1, Matrix.Translation(W(0.6, zh)) @ _aim((c, s_, 0)))
        tips.append(cup_candle(f"B{k}", *W(2.25, zh + 1.15, -0.06 * side)[:2], zh + 1.17, 0.26, wax, M["brass"], r=0.04, pan=0.08))
        # tines: a brow tine low and forward, two candle tines up from the beam
        bpts = smooth_path(beam, 3)
        for j, (f, up, lean) in enumerate(((0.22, 0.42, 0.18), (0.5, 0.62, 0.0), (0.72, 0.5, -0.12))):
            p = bpts[int(f * (len(bpts) - 1))]
            q = Vector(p) + Vector((c * lean, s_ * lean, up)) + Vector((-s_ * 0.08 * side, c * 0.08 * side, 0))
            mid = Vector(p).lerp(q, 0.5) + Vector((c * 0.06, s_ * 0.06, 0))
            roughen(sweep(f"Tine{k}{j}", [tuple(p), tuple(mid), tuple(q)], 0.055, bn, r1=0.018, seg=10, per=4), 0.008, 0.03)
            if j:
                tips.append(cup_candle(f"N{k}{j}", q.x, q.y, q.z + 0.02, 0.22 + 0.04 * rnd.random(), wax, M["brass"], r=0.038, pan=0.07))
            else:
                cone(f"TineTip{k}", 0.02, 0.0, 0.06, (q.x, q.y, q.z + 0.03), bn, verts=6)
        # an iron strap binding each root to the hub
        hoop(f"Bind{k}", W(0.68, zh), 0.115, "X", iron, thick=0.016)
        _xform(len(P.PARTS) - 1, Matrix.Translation(W(0.68, zh)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation(Vector(W(0.68, zh)) * -1))
    # suspension: three iron rods to a ring, a chain to the rose
    zr = 4.0
    for k in range(3):
        a = k / 3 * TAU + 0.6
        tube(f"Rod{k}", [(math.cos(a) * 0.45, math.sin(a) * 0.45, zh + 0.3), (math.cos(a) * 0.08, math.sin(a) * 0.08, zr)], 0.025, iron, poly=True)
    tube("TopRing", circle_pts(0, 0, zr + 0.08, 0.1, "X", 12), 0.02, iron, closed=True, poly=True)
    chain("Link", 0, 0, zr + 0.16, 5.3, iron)
    ceil_rose("Rose", 5.6, 0.34, iron, gl)
    flames("Flame", tips, h=0.12)
    return _dims()


def chandelier_cage(M):
    """A domed gothic birdcage holding a candle tree, a raven on its ring."""
    gl, iron, wax, cr = gilt(), M["iron"], wax_mat(), M["crimson"]
    R, zb = 1.0, 0.75
    lathe("Tray", [(0, zb - 0.18), (0.5, zb - 0.17), (0.9, zb - 0.1), (R + 0.06, zb - 0.04), (R + 0.08, zb + 0.04), (R + 0.02, zb + 0.08), (0, zb + 0.06)],
          iron, seg=40)
    ring_band("TrayBand", R - 0.01, R + 0.03, zb - 0.06, zb + 0.06, M["crimsonin"], seg=40)
    hoop("TrayBead", (0, 0, zb + 0.07), R + 0.04, "Z", gl, thick=0.016)
    lathe("Drop", [(0, 0.0), (0.04, 0.04), (0.07, 0.15), (0.05, 0.25), (0.1, 0.38), (0.2, 0.5), (0.3, zb - 0.17), (0, zb - 0.17)], iron, seg=16)
    sphere("DropBall", 0.06, (0, 0, 0.01), gl, seg=10, rings=6)
    prof = [(R, zb + 0.05), (R, 2.0), (0.93, 2.4), (0.7, 2.74), (0.36, 2.96), (0.08, 3.04)]
    n = 20
    for k in range(n):
        a = k / n * TAU
        c, s_ = math.cos(a), math.sin(a)
        if abs(a - 1.5 * math.pi) < 0.2:      # the door sits over these
            pass
        tube(f"Bar{k}", [(c * r, s_ * r, z) for r, z in prof], 0.016, iron, res=3)
    for zz, rr, m in ((1.15, R, gl), (2.0, R, iron), (2.5, 0.88, gl)):
        hoop(f"Hoop{zz}", (0, 0, zz), rr + 0.01, "Z", m, thick=0.018)
    # gothic arcade between the low hoops: little pointed arches every bay
    for k in range(n):
        a0, a1 = k / n * TAU, (k + 1) / n * TAU
        pts = []
        for i in range(7):
            t = i / 6
            kk = 1 - abs(2 * t - 1)
            a = a0 + (a1 - a0) * t
            pts.append((math.cos(a) * (R + 0.012), math.sin(a) * (R + 0.012), 1.7 + 0.22 * math.sin(kk * math.pi / 2) ** 0.75))
        tube(f"Arcade{k}", pts, 0.009, gl, square=True, poly=True)
    # the door on the front, with a latch
    door = [(-0.28, 0.85), (0.28, 0.85), (0.28, 1.6), (0.0, 1.85), (-0.28, 1.6)]
    tube("Door", [(u, -R - 0.03, z) for u, z in door], 0.016, iron, closed=True, square=True, poly=True)
    for u in (-0.14, 0.0, 0.14):
        tube(f"DoorBar{u}", [(u, -R - 0.03, 0.86), (u, -R - 0.03, 1.6 + (0.25 * (1 - abs(u) / 0.28)) - 0.02)], 0.01, iron, square=True, poly=True)
    box("Latch", (0.05, 0.05, 0.12), (0.3, -R - 0.05, 1.25), M["brass"], bevel=0.01)
    lathe("Crown", [(0, 2.98), (0.14, 3.0), (0.18, 3.08), (0.12, 3.16), (0.06, 3.2), (0, 3.22)], iron, seg=16)
    tube("CageRing", circle_pts(0, 0, 3.36, 0.13, "X", 14), 0.026, iron, closed=True, poly=True)
    raven("Raven", (0, -0.02, 3.47), -math.pi / 2, 2.1, iron, M["felt"])
    # the candle tree inside: a stem with three tiers of arms
    lathe("Stem", [(0, zb), (0.08, zb), (0.05, 0.95), (0.04, 2.1), (0, 2.1)], gl, seg=16)
    tips = []
    tiers = ((1.05, 0.62, 4, 0.0), (1.45, 0.45, 3, 0.5), (1.8, 0.0, 1, 0.0))
    for t, (z, r, cnt, ph) in enumerate(tiers):
        for k in range(cnt):
            a = (k + ph) / cnt * TAU + 0.4
            c, s_ = math.cos(a), math.sin(a)
            if r:
                tube(f"TreeArm{t}{k}", [(c * 0.04, s_ * 0.04, z - 0.12), (c * r * 0.5, s_ * r * 0.5, z - 0.16), (c * r, s_ * r, z - 0.05)], 0.018, gl)
            tips.append(cup_candle(f"K{t}{k}", c * r, s_ * r, z, 0.24, wax, gl, r=0.04, pan=0.075, sleeve=cr if t < 2 else None))
    chain("Link", 0, 0, 3.47, 5.1, iron)
    ceil_rose("Rose", 5.4, 0.32, iron, gl)
    flames("Flame", tips, h=0.12)
    return _dims()


def chandelier_cascade(M):
    """A crystal cascade: three gilt hoops of hanging bead strands making a cone round a stem of moonlight bulbs."""
    gl, iron = gilt(), M["iron"]
    glass = M["glassclear"]
    zt = 5.0
    ceil_rose("Rose", zt, 0.6, gl, iron, seg=40)
    tube("Rod", [(0, 0, zt - 0.2), (0, 0, 3.95)], 0.035, gl, poly=True)
    lathe("Crown", [(0, 3.7), (0.12, 3.72), (0.3, 3.82), (0.36, 3.92), (0.3, 3.96), (0, 3.98)], gl, seg=32)
    for k in range(10):
        a = k / 10 * TAU
        cone(f"CrownLeaf{k}", 0.035, 0.0, 0.18, (math.cos(a) * 0.33, math.sin(a) * 0.33, 4.02), gl, verts=6)
    hoops = ((1.5, 3.55, 30), (1.05, 3.12, 22), (0.62, 2.68, 14))
    ends = (2.75, 1.7, 0.62)
    for i, (r, z, n) in enumerate(hoops):
        hoop(f"Hoop{i}", (0, 0, z), r, "Z", gl, thick=0.026)
        hoop(f"HoopB{i}", (0, 0, z - 0.06), r, "Z", gl, thick=0.012)
        for k in range(6):
            a = (k + 0.5 * i) / 6 * TAU
            tube(f"Hanger{i}{k}", [(math.cos(a) * 0.3, math.sin(a) * 0.3, 3.75), (math.cos(a) * r, math.sin(a) * r, z)], 0.012, gl, poly=True)
    # the central stem with three tiers of bulb candles
    lathe("Stem", [(0, 0.85), (0.06, 0.88), (0.05, 1.2), (0.09, 1.3), (0.05, 1.4), (0.04, 3.7), (0, 3.7)], gl, seg=16)
    bulbs, op = [], opal()
    for t, (z, r, n) in enumerate(((1.3, 0.38, 6), (2.0, 0.3, 6), (2.7, 0.22, 4))):
        lathe(f"Tier{t}", [(0, z - 0.06), (r + 0.06, z - 0.02), (r + 0.08, z + 0.02), (0, z + 0.01)], gl, seg=24)
        for k in range(n):
            a = (k + 0.5 * t) / n * TAU
            x, y = math.cos(a) * r, math.sin(a) * r
            lathe(f"Sock{t}{k}", [(0, z), (0.035, z), (0.035, z + 0.12), (0.045, z + 0.13), (0, z + 0.13)], op, seg=10, loc=(x, y, 0))
            bulbs.append((x, y, z + 0.13))
    set_group("Glass")
    for i, (r, z, n) in enumerate(hoops):
        zb = ends[i]
        for k in range(n):
            a = (k + 0.5) / n * TAU
            x, y = math.cos(a) * r, math.sin(a) * r
            nb = int((z - 0.08 - zb) / 0.13)
            for b in range(nb):
                sphere(f"Bead{i}_{k}_{b}", 0.03, (x, y, z - 0.1 - b * 0.13), glass, seg=4, rings=2, scale=(1, 1, 1.3))
            lathe(f"Prism{i}_{k}", [(0, zb + 0.02), (0.035, zb - 0.04), (0.03, zb - 0.12), (0, zb - 0.22)], glass, seg=6, loc=(x, y, 0))
    lathe("Finial", [(0, 0.86), (0.08, 0.78), (0.11, 0.62), (0.08, 0.45), (0, 0.2)], glass, seg=8)
    set_group("Glow")
    gm = glow_moon()
    for k, (x, y, z) in enumerate(bulbs):
        lathe(f"Bulb{k}", [(0, z), (0.035, z + 0.02), (0.045, z + 0.07), (0.03, z + 0.14), (0, z + 0.19)], gm, seg=10, loc=(x, y, 0))
    sphere("Heart", 0.13, (0, 0, 3.3), gm, seg=14, rings=8)
    set_group("Main")
    return _dims()


def chandelier_raven_wing(M):
    """An iron raven with its wings spread 6.6 across, candles riding the leading edges of both wings."""
    gl, iron, wax = gilt(), M["iron"], wax_mat()
    dark, eye = M["felt"], M["crimson"]
    zb = 2.0
    # the body, head and beak (looking out to -Y and a little down), talons gripping an orb
    body = [("ell", (0, 0.1, zb), 0.36, (1.0, 2.1, 1.0)),                 # body
            ("ell", (0, -0.42, zb - 0.04), 0.33, (1.0, 1.0, 1.05)),           # breast
            ("cap", (0, -0.55, zb + 0.06), (0, -0.82, zb + 0.14), 0.17),     # neck
            ("ell", (0, -0.9, zb + 0.15), 0.21, (0.9, 1.15, 0.92)),           # head
            ("ell", (0, -1.04, zb + 0.24), 0.08, (1.8, 0.7, 0.5)),            # brow ridge
            ("cap", (0, 0.6, zb + 0.02), (0, 0.95, zb - 0.02), 0.12)]         # rump to the tail
    for sx in (-1, 1):
        body += [("ell", (sx * 0.24, -0.25, zb + 0.1), 0.16, (0.8, 1.4, 0.8)),     # shoulder
                 ("ball", (sx * 0.1, -0.92, zb + 0.03), 0.09),                       # cheek / rictal feathers
                 ("-ball", (sx * 0.12, -1.0, zb + 0.19), 0.035)]                     # eye socket
    blob("Body", body, iron, res=0.03, target=4200, pit=0.012, pit_scale=0.04)
    # the beak: heavy, curved, slightly open
    sweep("Beak", [(0, -1.02, zb + 0.13), (0, -1.2, zb + 0.13), (0, -1.38, zb + 0.08), (0, -1.48, zb - 0.01)], 0.11, dark, r1=0.006, seg=10, per=4,
          flat_k=(1.0, 0.7), up=(0, 0, 1))
    sweep("BeakLow", [(0, -1.02, zb + 0.04), (0, -1.2, zb + 0.02), (0, -1.36, zb - 0.02)], 0.07, dark, r1=0.006, seg=8, per=3, flat_k=(1.0, 0.6),
          up=(0, 0, 1))
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.04, (sx * 0.12, -1.02, zb + 0.19), eye, seg=10, rings=6)
        for j in range(3):
            sweep(f"Talon{sx}{j}", [(sx * 0.12 + (j - 1) * 0.05, -0.1, zb - 0.3), (sx * 0.14 + (j - 1) * 0.07, -0.2, zb - 0.56),
                                    (sx * 0.1 + (j - 1) * 0.05, -0.14, zb - 0.72), (sx * 0.08 + (j - 1) * 0.04, -0.06, zb - 0.76)], 0.026, dark, r1=0.006,
                  seg=7, per=3)
    # breast and nape feathers: overlapping hackles
    for k in range(16):
        a = math.radians(-150 + 120 * (k % 8) / 7)
        row = k // 8
        y = -0.62 + row * 0.18
        r = 0.26 - row * 0.03
        base = Vector((math.cos(a) * r, y, zb + math.sin(a) * r * 0.9))
        d = Vector((math.cos(a) * 0.3, 0.8, math.sin(a) * 0.4)).normalized()
        sweep(f"Hackle{k}", [tuple(base), tuple(base + d * 0.14), tuple(base + d * 0.26 + Vector((0, 0, -0.04)))], 0.05, iron, r1=0.004, seg=6, per=2,
              flat_k=(1.0, 0.3))
    sphere("Orb", 0.2, (0, -0.1, zb - 0.78), gl, seg=16, rings=8)
    lathe("OrbDrop", [(0, 0.85), (0.04, 0.9), (0.06, 1.0), (0.04, 1.06), (0, zb - 0.95)], gl, seg=10, loc=(0, -0.1, 0))
    # tail fan
    for k in range(7):
        yaw = math.pi / 2 + math.radians(-27 + 9 * k)
        wing_feather(f"Tail{k}", (0, 0.7, 0), yaw, 1.05 - 0.04 * abs(k - 3), 0.3, zb - 0.05 + 0.012 * k, iron, droop=0.12)
    tips = []
    for sx in (-1, 1):
        # the wing's leading-edge bone, rising a little to the wrist and sweeping back to the tip
        edge = [(sx * 0.3, -0.15, zb + 0.15), (sx * 1.0, -0.4, zb + 0.45), (sx * 1.9, -0.45, zb + 0.75), (sx * 2.7, -0.2, zb + 0.95), (sx * 3.3, 0.2, zb + 1.0)]
        sweep(f"Edge{sx}", edge, 0.12, iron, r1=0.035, seg=8, per=4, flat_k=(1.0, 0.65))
        ep = smooth_path(edge, 6)
        # primaries fanned off the outer wing, a broad run of secondaries straight back, coverts over them
        for j in range(9):
            p = ep[int((0.6 + 0.4 * j / 8) * (len(ep) - 1))]
            yaw = math.pi / 2 - sx * math.radians(25 + 50 * j / 8)
            wing_feather(f"Prim{sx}{j}", (p.x, p.y + 0.05, 0), yaw, 1.5 + 0.3 * math.sin(j / 8 * math.pi), 0.5, p.z - 0.05 - 0.008 * j, iron, droop=0.08)
        for j in range(11):
            t = 0.04 + 0.6 * j / 10
            p = ep[int(t * (len(ep) - 1))]
            wing_feather(f"Sec{sx}{j}", (p.x, p.y + 0.05, 0), math.pi / 2 - sx * math.radians(4 + 22 * j / 10), 1.35 - 0.1 * t, 0.55, p.z - 0.07, iron,
                         droop=0.06)
        for j in range(10):
            p = ep[int((0.04 + 0.86 * j / 9) * (len(ep) - 1))]
            wing_feather(f"Cov{sx}{j}", (p.x, p.y, 0), math.pi / 2 - sx * math.radians(10 + 45 * j / 9), 0.75, 0.42, p.z + 0.01, iron, droop=0.05)
        # five candles riding the leading edge, gilt cups on short spikes
        for j in range(5):
            p = ep[int((0.18 + 0.78 * j / 4) * (len(ep) - 1))]
            tube(f"Spike{sx}{j}", [(p.x, p.y, p.z), (p.x, p.y - 0.04, p.z + 0.14)], 0.02, iron, poly=True)
            tips.append(cup_candle(f"W{sx}{j}", p.x, p.y - 0.04, p.z + 0.14, 0.26, wax, gl, r=0.042, pan=0.08))
    # suspension: two rods from the shoulders and one from the back to a ring, a chain to the rose
    zr = 4.0
    for k, (x, y) in enumerate(((-1.1, -0.3), (1.1, -0.3), (0, 0.6))):
        tube(f"Rod{k}", [(x, y, zb + 0.55 if x else zb + 0.4), (x * 0.06, y * 0.06, zr)], 0.022, iron, poly=True)
    tube("TopRing", circle_pts(0, 0, zr + 0.08, 0.1, "X", 12), 0.02, iron, closed=True, poly=True)
    chain("Link", 0, 0, zr + 0.16, 5.0, iron)
    ceil_rose("Rose", 5.3, 0.34, iron, gl)
    flames("Flame", tips, h=0.12)
    return _dims()


def chandelier_ship_hull(M):
    """An upturned ship's hull of dark oak, keel to the ceiling, ringed with candles, three lanterns under it."""
    gl, iron, wax, oak = gilt(), M["iron"], wax_mat(), M["oakdark"]
    L, nx, ns = 7.0, 28, 14
    zg0 = 1.5

    def section(x, th):
        t = x / (L / 2)
        w = 1.15 * max(0.02, 1 - t ** 4) ** 0.5
        h = 0.95 * (1 - 0.25 * t * t)
        zg = zg0 + 0.22 * t * t
        return Vector((x, w * math.sin(th), zg + h * math.cos(th)))
    xs = [(-L / 2 + 0.06) + (L - 0.12) * i / nx for i in range(nx + 1)]
    ths = [math.radians(-90 + 180 * j / ns) for j in range(ns + 1)]
    rows = [[tuple(section(x, th)) for th in ths] for x in xs]
    _mesh("Hull", rows, oak, 0.06)
    # planking seams, ribs inside, the keel, gunwales
    for j in range(1, ns, 2):
        th = ths[j]
        tube(f"Seam{j}", [tuple(section(x, th) + Vector((0, math.sin(th), math.cos(th))) * 0.032) for x in xs[1:-1:2]], 0.01, M["felt"], square=True, poly=True)
    for i in range(2, nx - 1, 4):
        x = xs[i]
        pts = [tuple(section(x, th) - Vector((0, math.sin(th), math.cos(th))) * 0.07) for th in ths[1:-1]]
        tube(f"Rib{i}", pts, 0.045, oak, square=True, res=2)
    tube("Keel", [tuple(section(x, 0) + Vector((0, 0, 0.08))) for x in xs[1:-1]], 0.07, oak, square=True, res=2)
    # stem and stern posts curling into scrolls, gilt-tipped
    for sx in (-1, 1):
        a = section(sx * (L / 2 - 0.08), 0)
        post = [tuple(a), (a.x + sx * 0.35, 0, a.z - 0.05), (a.x + sx * 0.5, 0, a.z - 0.4), (a.x + sx * 0.42, 0, a.z - 0.65),
                (a.x + sx * 0.28, 0, a.z - 0.55), (a.x + sx * 0.3, 0, a.z - 0.42)]
        sweep(f"Post{sx}", post, 0.09, oak, r1=0.05, seg=8, per=4)
        sphere(f"PostKnob{sx}", 0.07, post[-1], gl, seg=10, rings=5)
    for sy in (-1, 1):
        rail = [tuple(section(x, sy * math.pi / 2) + Vector((0, sy * 0.03, -0.02))) for x in xs]
        tube(f"Gunwale{sy}", rail, 0.06, oak, square=True, res=2)
        tube(f"GunwaleIron{sy}", [tuple(Vector(p) + Vector((0, sy * 0.06, -0.05))) for p in rail], 0.018, iron, square=True, poly=True)
    tips = []
    # seven candle brackets out of each gunwale
    for sy in (-1, 1):
        for k in range(7):
            x = -2.7 + 5.4 * k / 6
            g = section(x, sy * math.pi / 2)
            o = Vector((x, g.y + sy * 0.32, g.z + 0.04))
            tube(f"Bracket{sy}{k}", [(x, g.y, g.z - 0.06), (x, g.y + sy * 0.18, g.z - 0.08), (o.x, o.y, o.z - 0.02)], 0.022, iron)
            tips.append(cup_candle(f"G{sy}{k}", o.x, o.y, o.z, 0.28, wax, M["brass"], r=0.042, pan=0.08))
    # three ship's lanterns hanging under the keel
    for k, x in enumerate((-1.9, 0.0, 1.9)):
        top = section(x, 0).z - 0.05
        zl = 0.25 if k == 1 else 0.5
        chain(f"LChain{k}", x, 0, zl + 0.98, top, iron)
        tips.append(sq_lantern(f"Lan{k}", M, gl, Matrix.Translation((x, 0, zl)) @ Matrix.Scale(1.1, 4)))
    # suspension: four iron rods from the gunwale ends to a ring, a chain to the rose
    zr = 4.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            g = section(sx * 2.4, sy * math.pi / 2)
            tube(f"Rod{sx}{sy}", [(g.x, g.y, g.z + 0.02), (sx * 0.1, sy * 0.05, zr)], 0.022, iron, poly=True)
    tube("TopRing", circle_pts(0, 0, zr + 0.08, 0.12, "X", 12), 0.022, iron, closed=True, poly=True)
    chain("Link", 0, 0, zr + 0.18, 5.2, iron)
    ceil_rose("Rose", 5.5, 0.36, iron, gl)
    flames("Flame", tips, h=0.12)
    return _dims()


def chandelier_thorn_crown(M):
    """A crown of twisted iron bramble with thorns, glowing rose-glass buds, and one great rose hanging in its heart."""
    gl, iron = gilt(), M["iron"]
    rnd = random.Random(4277)
    R, z = 1.8, 1.5
    for v in range(3):
        pts = []
        for i in range(97):
            a = i / 96 * TAU
            ph = a * 7 + v * TAU / 3
            rr = R + math.cos(ph) * 0.1
            pts.append((math.cos(a) * rr, math.sin(a) * rr, z + math.sin(ph) * 0.1))
        sweep(f"Vine{v}", pts, 0.032, iron, seg=6, per=1, caps=False)
    for k in range(70):
        a = rnd.uniform(0, TAU)
        ph = rnd.uniform(0, TAU)
        d = Vector((math.cos(a) * math.cos(ph), math.sin(a) * math.cos(ph), math.sin(ph)))
        base = Vector((math.cos(a) * R, math.sin(a) * R, z)) + d * 0.12
        s = _mark()
        cone(f"Thorn{k}", 0.018, 0.0, 0.1, (0, 0, 0.05), iron, verts=4)
        _xform(s, Matrix.Translation(base) @ _aim(d))
    hoop("Inner", (0, 0, z - 0.02), R - 0.22, "Z", gl, thick=0.018)
    for k in range(12):
        a = k / 12 * TAU
        tube(f"Tie{k}", [(math.cos(a) * (R - 0.22), math.sin(a) * (R - 0.22), z - 0.02), (math.cos(a) * (R - 0.05), math.sin(a) * (R - 0.05), z)],
             0.012, gl, poly=True)
    buds = []
    for k in range(12):
        a = (k + 0.5) / 12 * TAU
        x, y = math.cos(a) * R, math.sin(a) * R
        lathe(f"Calyx{k}", [(0, z + 0.08), (0.06, z + 0.1), (0.1, z + 0.17), (0.08, z + 0.2), (0, z + 0.18)], iron, seg=10, flute=(5, 0.35), loc=(x, y, 0))
        for j, yaw in enumerate((a + 0.9, a - 0.9)):
            leaf(f"Leaf{k}{j}", (x, y, z + 0.12), yaw, 0.35, 0.24, 0.1, 0.05, iron)
        buds.append((x, y, z + 0.16))
    # three thorned rods up to an apex, and a chain down from it to the great rose in the heart
    za = 3.6
    for k in range(3):
        a = k / 3 * TAU + 0.3
        p0, p1 = Vector((math.cos(a) * R, math.sin(a) * R, z + 0.1)), Vector((0, 0, za))
        tube(f"Rod{k}", [tuple(p0), tuple(p1)], 0.024, iron, poly=True)
        d = (p1 - p0).normalized()
        for t in (0.2, 0.4, 0.6, 0.8):
            q = p0.lerp(p1, t)
            side = d.cross(Vector((0, 0, 1))).normalized() * (1 if int(t * 10) % 4 else -1)
            s = _mark()
            cone(f"RodThorn{k}{t}", 0.015, 0.0, 0.08, (0, 0, 0.04), iron, verts=4)
            _xform(s, Matrix.Translation(q) @ _aim(side + Vector((0, 0, 0.4))))
    lathe("Apex", [(0, za - 0.1), (0.1, za - 0.05), (0.12, za + 0.05), (0.06, za + 0.15), (0, za + 0.18)], gl, seg=16)
    chain("Hang", 0, 0, 1.3, za - 0.08, iron)
    lathe("RoseCup", [(0, 1.08), (0.09, 1.1), (0.16, 1.22), (0.14, 1.3), (0, 1.28)], iron, seg=14, flute=(6, 0.3))
    chain("Link", 0, 0, za + 0.16, 4.6, iron)
    ceil_rose("Rose", 4.9, 0.32, iron, gl)
    set_group("Glow")
    gr = glow_rose()
    for k, (x, y, zz) in enumerate(buds):
        lathe(f"Bud{k}", [(0, zz), (0.07, zz + 0.03), (0.1, zz + 0.1), (0.08, zz + 0.18), (0.03, zz + 0.23), (0, zz + 0.24)], gr, seg=12,
              flute=(5, 0.22), loc=(x, y, 0))
    # the great rose: three rings of cupped petals
    for i, (r, h, n, tw) in enumerate(((0.3, 0.26, 7, 0.0), (0.22, 0.3, 6, 0.4), (0.12, 0.3, 5, 0.9))):
        lathe(f"Bloom{i}", [(0, 1.02), (r * 0.6, 1.06), (r, 1.12 + h * 0.4), (r * 0.92, 1.12 + h), (r * 0.6, 1.12 + h * 0.85)], gr, seg=28,
              flute=(n, 0.3))
        _xform(len(P.PARTS) - 1, Matrix.Translation((0, 0, 1.02)) @ Matrix.Rotation(tw, 4, "Z") @ Matrix.Translation((0, 0, -1.02)))
    set_group("Main")
    return _dims()


# ================================================================== PENDANTS AND LANTERN CLUSTERS

def lantern_cluster(M):
    """Five square gothic lanterns at staggered drops from one pierced iron ceiling plate."""
    gl, iron = gilt(), M["iron"]
    zt = 4.2
    plate = [(-0.8, -0.55), (-0.55, -0.8), (0.55, -0.8), (0.8, -0.55), (0.8, 0.55), (0.55, 0.8), (-0.55, 0.8), (-0.8, 0.55)]
    prism("Plate", plate, zt - 0.12, 0.12, iron, plane="XY", bevel=0.015)
    prism("PlateInset", [(x * 0.8, y * 0.8) for x, y in plate], zt - 0.135, 0.02, M["crimsonin"], plane="XY")
    tube("PlateRim", [(x * 0.86, y * 0.86, zt - 0.14) for x, y in plate], 0.014, gl, closed=True, square=True, poly=True)
    for k, (x, y) in enumerate(((0.62, 0.62), (-0.62, 0.62), (-0.62, -0.62), (0.62, -0.62))):
        cone(f"Crocket{k}", 0.05, 0.0, 0.18, (x, y, zt - 0.2), gl, verts=6, rot=(math.pi, 0, 0))
    spots = [(0, 0, 0.3), (0.5, 0.5, 1.5), (-0.5, 0.5, 0.9), (-0.5, -0.5, 1.75), (0.5, -0.5, 1.15)]
    tips = []
    for k, (x, y, zl) in enumerate(spots):
        s = 1.0 if k == 0 else 0.8
        top = zl + (0.62 + 0.52) * s
        chain(f"Chain{k}", x, y, top + 0.04, zt - 0.14, iron, pitch=0.14, r=0.035, h=0.07, thick=0.009)
        lathe(f"Boss{k}", [(0, zt - 0.2), (0.06, zt - 0.18), (0.07, zt - 0.14), (0, zt - 0.13)], gl, seg=12, loc=(x, y, 0))
        tips.append(sq_lantern(f"L{k}", M, gl, Matrix.Translation((x, y, zl)) @ Matrix.Rotation(k * 0.35, 4, "Z") @ Matrix.Scale(s, 4)))
    flames("Flame", tips, h=0.1)
    return _dims()


def pendant_spire(M):
    """An inverted openwork spire: violet glass between crocketed iron ribs, a witchlight burning inside."""
    gl, iron = gilt(), M["iron"]
    z0, z1, r1 = 0.15, 2.5, 0.62

    def rib_pt(k, t):
        a = k / 6 * TAU
        r = r1 * (1 - (1 - t) ** 1.6)
        return Vector((math.cos(a) * r, math.sin(a) * r, z0 + (z1 - z0) * t))
    for k in range(6):
        pts = [tuple(rib_pt(k, i / 10)) for i in range(11)]
        tube(f"Rib{k}", pts, 0.028, iron, square=True, poly=True)
        for t in (0.3, 0.5, 0.7, 0.88):
            p = rib_pt(k, t)
            s = _mark()
            tube(f"Crocket{k}{t}", [(0, 0, 0), (0.07, 0, -0.02), (0.11, 0, 0.04), (0.08, 0, 0.07)], 0.018, gl)
            _xform(s, Matrix.Translation(p) @ Matrix.Rotation(k / 6 * TAU, 4, "Z"))
    for t in (0.35, 0.65):
        pts = [tuple(rib_pt(k, t)) for k in range(6)]
        tube(f"Band{t}", pts, 0.016, gl, closed=True, square=True, poly=True)
    lathe("Tip", [(0, -0.35), (0.02, -0.28), (0.04, -0.1), (0.06, 0.05), (0.07, z0 + 0.05), (0, z0 + 0.06)], gl, seg=6)
    sphere("TipBall", 0.04, (0, 0, -0.37), gl, seg=8, rings=4)
    # the crown: a hexagonal band, six pointed gablets up and a gilt trefoil in each
    lathe("Crown", [(0, z1 - 0.04), (r1 + 0.04, z1 - 0.04), (r1 + 0.07, z1 + 0.02), (r1 + 0.07, z1 + 0.14), (r1 + 0.03, z1 + 0.18), (0, z1 + 0.18)], iron, seg=6)
    ap = (r1 + 0.07) * math.cos(math.pi / 6)
    for k in range(6):
        g = _mark()
        prism(f"Gablet{k}", [(-0.3, z1 + 0.16), (0.3, z1 + 0.16), (0, z1 + 0.52)], -ap + 0.01, 0.03, iron)
        foil(f"GabletFoil{k}", 0, -ap - 0.01, z1 + 0.29, 0.06, gl, lobes=3, thick=0.008, centre=False)
        sphere(f"GabletTip{k}", 0.03, (0, -ap + 0.01, z1 + 0.54), gl, seg=8, rings=4)
        _xform(g, Matrix.Rotation(math.radians(30 + 60 * k - 270), 4, "Z"))
    for k in range(3):
        a = k / 3 * TAU + math.pi / 6
        tube(f"Rod{k}", [(math.cos(a) * r1 * 0.9, math.sin(a) * r1 * 0.9, z1 + 0.16), (math.cos(a) * 0.06, math.sin(a) * 0.06, 3.45)], 0.02, iron, poly=True)
    tube("TopRing", circle_pts(0, 0, 3.52, 0.08, "X", 12), 0.018, iron, closed=True, poly=True)
    chain("Link", 0, 0, 3.6, 4.0, iron)
    ceil_rose("Rose", 4.3, 0.3, iron, gl)
    tube("Stem", [(0, 0, z1), (0, 0, 1.5)], 0.02, gl, poly=True)
    lathe("Cup", [(0, 1.38), (0.08, 1.4), (0.1, 1.46), (0.06, 1.5), (0, 1.49)], gl, seg=12)
    set_group("Glass")
    for k in range(6):
        rows = []
        for i in range(9):
            t = 0.04 + 0.94 * i / 8
            a, b = rib_pt(k, t), rib_pt(k + 1, t)
            a = Vector((a.x * 0.985, a.y * 0.985, a.z))
            b = Vector((b.x * 0.985, b.y * 0.985, b.z))
            rows.append([tuple(a), tuple(b)])
        _mesh(f"Pane{k}", rows, M["glassclear"], 0.008)
    set_group("Glow")
    gv = glow_violet()
    sphere("Witchlight", 0.17, (0, 0, 1.2), gv, seg=14, rings=8, scale=(1, 1, 1.2))
    tongue("Flame", (0, 0, 1.0), 0.32, 0.08, 0.02, 0.0, gv, seg=8, rows=8)
    set_group("Main")
    return _dims()


def pendant_bell_cage(M):
    """The Midnight Bell as a lamp: an openwork iron bell with a glowing ember clapper and a lit heart."""
    gl, iron, cr = gilt(), M["iron"], M["crimson"]
    prof = [(0.92, 0.9), (0.9, 0.98), (0.78, 1.15), (0.62, 1.45), (0.55, 1.8), (0.52, 2.15), (0.45, 2.4), (0.28, 2.52), (0.0, 2.55)]
    n = 16
    for k in range(n):
        a = k / n * TAU
        tube(f"Rib{k}", [(math.cos(a) * r, math.sin(a) * r, z) for r, z in prof[1:-1]], 0.022, iron, res=3)
    lathe("Lip", [(0.84, 0.86), (0.95, 0.86), (0.98, 0.92), (0.95, 1.02), (0.85, 1.02), (0.84, 0.94), (0.84, 0.86)], iron, seg=48)
    ring_band("LipBand", 0.955, 0.985, 0.89, 0.99, cr, seg=48)
    for k in range(12):
        g = _mark()
        foil(f"LipFoil{k}", 0, -0.99, 0.94, 0.035, gl, thick=0.007)
        _xform(g, Matrix.Rotation(k / 12 * TAU, 4, "Z"))
    for z, r in ((1.45, 0.62), (2.15, 0.52)):
        hoop(f"Band{z}", (0, 0, z), r + 0.01, "Z", gl, thick=0.022)
    lathe("Shoulder", [(0.5, 2.3), (0.46, 2.4), (0.3, 2.52), (0.0, 2.56), (0, 2.62), (0.34, 2.58), (0.52, 2.44), (0.54, 2.3)], iron, seg=32)
    lathe("Boss", [(0, 2.58), (0.14, 2.6), (0.15, 2.7), (0, 2.72)], iron, seg=16)
    for k in range(6):
        a = k / 6 * TAU
        tube(f"Canon{k}", [(math.cos(a) * 0.08, math.sin(a) * 0.08, 2.68), (math.cos(a) * 0.14, math.sin(a) * 0.14, 2.82),
                           (math.cos(a) * 0.06, math.sin(a) * 0.06, 2.92)], 0.025, iron)
    tube("Ring", circle_pts(0, 0, 3.02, 0.08, "X", 12), 0.02, iron, closed=True, poly=True)
    chain("Link", 0, 0, 3.1, 3.6, iron)
    ceil_rose("Rose", 3.9, 0.3, iron, gl)
    tube("ClapperRod", [(0, 0, 2.5), (0, 0, 0.56)], 0.02, iron, poly=True)
    lathe("ClapperCup", [(0, 0.5), (0.1, 0.52), (0.13, 0.58), (0.1, 0.62), (0, 0.63)], gl, seg=16)
    set_group("Glow")
    sphere("Ember", 0.15, (0, 0, 0.38), fire(), seg=14, rings=8, scale=(1, 1, 1.15))
    sphere("Heart", 0.24, (0, 0, 1.85), bulb(), seg=16, rings=10, scale=(1, 1, 1.25))
    set_group("Main")
    return _dims()


def classroom_pendant(M):
    """A classroom light: an opal schoolhouse globe under a crimson crested gallery on a downrod."""
    gl, iron, cr = gilt(), M["iron"], M["crimson"]
    lathe("Canopy", [(0.03, 3.82), (0.12, 3.84), (0.26, 3.92), (0.3, 3.98), (0.3, 4.0), (0, 4.0)], iron, seg=32)
    hoop("CanopyGilt", (0, 0, 3.93), 0.27, "Z", gl, thick=0.01)
    tube("Rod", [(0, 0, 3.85), (0, 0, 1.55)], 0.03, iron, poly=True)
    for z in (3.0, 2.2):
        lathe(f"Knop{z}", [(0, z - 0.07), (0.05, z - 0.05), (0.07, z), (0.05, z + 0.05), (0, z + 0.07)], gl, seg=14)
    lathe("Fitter", [(0, 1.6), (0.06, 1.6), (0.1, 1.54), (0.22, 1.5), (0.3, 1.44), (0.31, 1.32), (0.25, 1.3), (0, 1.3)], cr, seg=32)
    hoop("FitterBead", (0, 0, 1.31), 0.31, "Z", gl, thick=0.014)
    for k in range(4):
        g = _mark()
        foil(f"Crest{k}", 0, -0.31, 1.4, 0.05, gl, thick=0.008)
        _xform(g, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    gp = [(0.2, 1.3), (0.34, 1.18), (0.44, 0.95), (0.45, 0.7), (0.38, 0.45), (0.22, 0.27), (0.0, 0.22)]
    for k in range(4):
        a = k / 4 * TAU + math.pi / 4
        tube(f"Strap{k}", [(math.cos(a) * (r + 0.02), math.sin(a) * (r + 0.02), z) for r, z in gp], 0.014, iron, res=3)
    lathe("Finial", [(0, 0.04), (0.03, 0.08), (0.05, 0.16), (0.03, 0.22), (0, 0.23)], gl, seg=12)
    set_group("Glow")
    lathe("Globe", [(0, 0.24), (0.2, 0.28), (0.36, 0.42), (0.43, 0.65), (0.43, 0.9), (0.36, 1.1), (0.22, 1.22), (0.19, 1.3), (0, 1.3)], opal(), seg=40)
    set_group("Main")
    return _dims()


def classroom_tri_pendant(M):
    """A long gothic iron bar over a row of desks, three crimson enamel shades hanging from it."""
    gl, iron, cr = gilt(), M["iron"], M["crimson"]
    zb, L = 1.9, 6.4
    for z in (zb - 0.18, zb + 0.18):
        box(f"Chord{z}", (L, 0.08, 0.06), (0, 0, z), iron, bevel=0.012)
    n = 16
    for k in range(n):
        x0 = -L / 2 + 0.1 + (L - 0.2) * k / n
        hw = (L - 0.2) / n / 2
        tube(f"Arch{k}", [(x0 + hw + u, 0, z) for u, z in _gothic(hw, zb - 0.15, zb + 0.02, zb + 0.15, n=6)][2:], 0.012, iron, square=True, poly=True)
        tube(f"Post{k}", [(x0, 0, zb - 0.15), (x0, 0, zb + 0.15)], 0.012, iron, square=True, poly=True)
        sphere(f"Boss{k}", 0.03, (x0, -0.045, zb + 0.18), gl, seg=8, rings=4)
    for sx in (-1, 1):
        lathe(f"EndCap{sx}", [(0, zb - 0.26), (0.08, zb - 0.22), (0.1, zb), (0.08, zb + 0.22), (0, zb + 0.26)], iron, seg=8, loc=(sx * L / 2, 0, 0))
        lathe(f"EndSpire{sx}", [(0.07, zb + 0.24), (0.04, zb + 0.4), (0, zb + 0.55)], gl, seg=8, loc=(sx * L / 2, 0, 0))
        lathe(f"EndDrop{sx}", [(0.07, zb - 0.24), (0.04, zb - 0.36), (0, zb - 0.48)], gl, seg=8, loc=(sx * L / 2, 0, 0))
        x = sx * 2.4
        tube(f"Hanger{sx}", [(x, 0, zb + 0.21), (x, 0, 3.86)], 0.024, iron, poly=True)
        lathe(f"Canopy{sx}", [(0.03, 3.82), (0.1, 3.84), (0.2, 3.92), (0.22, 4.0), (0, 4.0)], iron, seg=24, loc=(x, 0, 0))
        hoop(f"CanopyGilt{sx}", (x, 0, 3.92), 0.2, "Z", gl, thick=0.01)
    lit = shade_lit((0.92, 0.78, 0.55))
    xs = (-2.0, 0.0, 2.0)
    for k, x in enumerate(xs):
        tube(f"Stem{k}", [(x, 0, zb - 0.2), (x, 0, 1.36)], 0.02, gl, poly=True)
        lathe(f"Shade{k}", [(0.08, 1.3), (0.16, 1.26), (0.32, 1.1), (0.5, 0.92), (0.56, 0.86)], cr, seg=40, loc=(x, 0, 0))
        lathe(f"ShadeIn{k}", [(0.55, 0.865), (0.49, 0.925), (0.31, 1.105), (0.15, 1.265), (0.07, 1.29)], lit, seg=40, loc=(x, 0, 0))
        hoop(f"ShadeRim{k}", (x, 0, 0.865), 0.56, "Z", gl, thick=0.014)
        lathe(f"ShadeCap{k}", [(0, 1.38), (0.06, 1.37), (0.1, 1.3), (0.08, 1.27), (0, 1.27)], gl, seg=16, loc=(x, 0, 0))
        lathe(f"Socket{k}", [(0, 1.27), (0.06, 1.27), (0.06, 1.12), (0, 1.12)], M["brass"], seg=12, loc=(x, 0, 0))
    set_group("Glow")
    gb = bulb()
    for k, x in enumerate(xs):
        sphere(f"Bulb{k}", 0.12, (x, 0, 1.0), gb, seg=14, rings=8, scale=(1, 1, 1.15))
        lathe(f"Diffuser{k}", [(0, 0.84), (0.3, 0.85), (0.52, 0.875), (0, 0.885)], opal(), seg=40, loc=(x, 0, 0))
    set_group("Main")
    return _dims()


# ================================================================== GOTHIC CEILING LIGHTS AND CORRIDOR LIGHTS

def tracery_ceiling_rose(M):
    """A flush ceiling light like a rose window laid on the ceiling: iron tracery over frosted glow."""
    gl, iron = gilt(), M["iron"]
    zt, R = 0.5, 1.75
    lathe("Pan", [(0, zt - 0.16), (R - 0.05, zt - 0.16), (R + 0.06, zt - 0.1), (R + 0.08, zt), (0, zt)], iron, seg=64)
    lathe("Rim", [(R - 0.14, 0.12), (R, 0.1), (R + 0.06, 0.16), (R + 0.06, 0.26), (R - 0.04, 0.36), (R - 0.14, 0.34), (R - 0.14, 0.12)], iron, seg=64)
    hoop("RimGilt", (0, 0, 0.33), R + 0.065, "Z", gl, thick=0.015)
    for k in range(24):
        a = (k + 0.5) / 24 * TAU
        sphere(f"Ballflower{k}", 0.04, (math.cos(a) * (R + 0.07), math.sin(a) * (R + 0.07), 0.36), gl, seg=8, rings=4)
        a2 = k / 24 * TAU
        g = _mark()
        tube(f"RimLancet{k}", [(u, -(R + 0.075), z) for u, z in _gothic(0.13, 0.14, 0.24, 0.31, n=6)], 0.012, gl, closed=True, square=True, poly=True)
        _xform(g, Matrix.Rotation(a2 + math.pi / 2, 4, "Z"))
    zt2 = 0.12
    hoop("Hub", (0, 0, zt2), 0.36, "Z", iron, thick=0.04)
    hoop("Mid", (0, 0, zt2), 1.05, "Z", iron, thick=0.03)
    hoop("Outer", (0, 0, zt2), R - 0.12, "Z", iron, thick=0.045)
    for k in range(12):
        a = k / 12 * TAU
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Spoke{k}", [(c * 0.36, s_ * 0.36, zt2), (c * (R - 0.12), s_ * (R - 0.12), zt2)], 0.03, iron, square=True, poly=True)
        b = a + TAU / 24
        cb, sb = math.cos(b), math.sin(b)
        hw = (R - 0.12) * math.sin(TAU / 24) * 0.82
        petal = [(r, u) for u, r in _gothic(hw, 1.12, R - 0.5, R - 0.2, n=8)]
        tube(f"Petal{k}", [(cb * r - sb * u, sb * r + cb * u, zt2 - 0.01) for r, u in petal], 0.02, iron, square=True, closed=True, poly=True)
        hw2 = 0.45 * math.sin(TAU / 24) * 1.6
        inner = [(r, u) for u, r in _gothic(hw2, 0.42, 0.75, 0.98, n=8)]
        tube(f"Lancet{k}", [(cb * r - sb * u, sb * r + cb * u, zt2 - 0.01) for r, u in inner], 0.016, gl, square=True, closed=True, poly=True)
        fr = R - 0.62
        s = _mark()
        foil(f"Foil{k}", 0, 0, 0, 0.11, gl, lobes=3, thick=0.012, centre=False)
        _xform(s, Matrix.Translation((cb * fr, sb * fr, zt2 - 0.02)) @ Matrix.Rotation(b - math.pi / 2, 4, "Z") @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    s = _mark()
    foil("HubFoil", 0, 0, 0, 0.2, gl, lobes=4, thick=0.016)
    _xform(s, Matrix.Translation((0, 0, zt2 - 0.03)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    lathe("Boss", [(0, -0.12), (0.06, -0.08), (0.12, 0.0), (0.16, 0.08), (0.12, 0.1), (0, 0.1)], gl, seg=20)
    lathe("Pendant", [(0, -0.32), (0.04, -0.28), (0.05, -0.2), (0.03, -0.12), (0, -0.12)], gl, seg=10)
    set_group("Glow")
    lit = opal()
    lathe("Frost", [(0, 0.2), (R - 0.12, 0.17), (R - 0.1, 0.26), (0, 0.3)], lit, seg=64)
    for k in range(24):
        g = _mark()
        prism(f"RimLight{k}", _gothic(0.12, 0.15, 0.24, 0.3, n=6), -(R + 0.062), 0.02, lit)
        _xform(g, Matrix.Rotation(k / 24 * TAU + math.pi / 2, 4, "Z"))
    set_group("Main")
    return _dims()


def vault_boss_light(M):
    """A rib vault in miniature on the ceiling: eight stone ribs meet at a hanging boss lantern of lit lancets."""
    gl, iron, st = gilt(), M["iron"], M["stone"]
    zt, H = 2.2, 1.3
    box("Plate", (3.0, 3.0, 0.12), (0, 0, zt - 0.06), st, bevel=0.03)
    box("PlateMould", (2.82, 2.82, 0.06), (0, 0, zt - 0.14), st, bevel=0.02)
    zboss = zt - H
    ends = [(1.35, 1.35), (-1.35, 1.35), (-1.35, -1.35), (1.35, -1.35), (1.35, 0), (0, 1.35), (-1.35, 0), (0, -1.35)]
    for k, (x, y) in enumerate(ends):
        d = math.hypot(x, y)
        pts = []
        for i in range(9):
            t = i / 8
            r = max(d * (1 - t), 0.36)
            z = zt - 0.17 - (zt - 0.17 - (zboss + 0.22)) * (1 - math.cos(t * math.pi / 2)) ** 1.4
            pts.append((x / d * r, y / d * r, z))
        sweep(f"Rib{k}", pts, 0.085 if k < 4 else 0.06, st, seg=6, per=3, flat_k=(1.0, 0.6), up=(0, 0, 1))
        if k < 4:
            for i in (3, 5):
                p = Vector(pts[i])
                sphere(f"RibBoss{k}{i}", 0.07, tuple(p + Vector((0, 0, -0.07))), gl, seg=8, rings=4)
    zl0, zl1 = zboss - 0.62, zboss + 0.12
    lathe("Head", [(0, zl1 + 0.2), (0.42, zl1 + 0.18), (0.48, zl1 + 0.08), (0.44, zl1 - 0.02), (0, zl1 - 0.02)], st, seg=8)
    lathe("Foot", [(0, zl0 + 0.04), (0.44, zl0 + 0.04), (0.48, zl0 - 0.04), (0.34, zl0 - 0.14), (0, zl0 - 0.16)], st, seg=8)
    _xform(len(P.PARTS) - 2, Matrix.Rotation(math.pi / 8, 4, "Z"))
    ap = 0.4 * math.cos(math.pi / 8)
    hs = 0.4 * math.sin(math.pi / 8)
    for k in range(8):
        g = _mark()
        tube(f"Mullion{k}", [(hs, -ap - 0.01, zl0 + 0.04), (hs, -ap - 0.01, zl1)], 0.025, iron, square=True, poly=True)
        tube(f"LancetArch{k}", [(u, -ap - 0.02, z) for u, z in _gothic(0.12, zl0 + 0.08, zl1 - 0.18, zl1 - 0.04, n=8)], 0.014, gl, closed=True,
             square=True, poly=True)
        _xform(g, Matrix.Rotation(k * math.pi / 4, 4, "Z"))
    lathe("Cone", [(0.3, zl0 - 0.14), (0.25, zl0 - 0.3), (0.16, zl0 - 0.45), (0.06, zl0 - 0.56), (0, zl0 - 0.6)], gl, seg=12, flute=(6, 0.18))
    set_group("Glow")
    ga = glow_amber()
    for k in range(8):
        g = _mark()
        prism(f"Light{k}", _gothic(0.115, zl0 + 0.09, zl1 - 0.18, zl1 - 0.05, n=8), -ap + 0.005, 0.02, ga)
        _xform(g, Matrix.Rotation(k * math.pi / 4, 4, "Z"))
    lathe("Core", [(0, zl0 + 0.05), (0.33, zl0 + 0.05), (0.33, zl1 - 0.03), (0, zl1 - 0.03)], ga, seg=8)
    _xform(len(P.PARTS) - 1, Matrix.Rotation(math.pi / 8, 4, "Z"))
    set_group("Main")
    return _dims()


def corridor_strip_light(M):
    """An 8-stud iron ceiling housing: a gothic arcade grille over a frosted strip of light; tiles end to end."""
    gl, iron = gilt(), M["iron"]
    L, W, H = 8.0, 0.9, 0.5
    box("Top", (L, W + 0.1, 0.08), (0, 0, H - 0.04), iron, bevel=0.012)
    for sy in (-1, 1):
        box(f"Side{sy}", (L, 0.06, H - 0.08), (0, sy * W / 2, (H - 0.08) / 2), iron, bevel=0.01)
        box(f"Bead{sy}", (L, 0.03, 0.03), (0, sy * (W / 2 + 0.04), 0.08), gl, bevel=0.006)
        box(f"BeadTop{sy}", (L, 0.03, 0.03), (0, sy * (W / 2 + 0.04), H - 0.1), gl, bevel=0.006)
        for k in range(16):
            g = _mark()
            x = -L / 2 + 0.25 + k * 0.5
            tube(f"SideLancet{sy}{k}", [(x + u, -(W / 2 + 0.04), z) for u, z in _gothic(0.17, 0.12, 0.28, 0.36, n=6)], 0.014, iron, closed=True, square=True,
                 poly=True)
            if sy > 0:
                _xform(g, Matrix.Rotation(math.pi, 4, "Z"))
    for sy in (-1, 1):
        tube(f"GrilleRail{sy}", [(-L / 2, sy * (W / 2 - 0.03), 0.04), (L / 2, sy * (W / 2 - 0.03), 0.04)], 0.025, iron, square=True, poly=True)
    tube("GrilleSpine", [(-L / 2, 0, 0.04), (L / 2, 0, 0.04)], 0.02, iron, square=True, poly=True)
    n = 16
    for k in range(n):
        x0 = -L / 2 + L * k / n
        x1 = x0 + L / n
        tube(f"Cross{k}", [(x0, -W / 2 + 0.03, 0.04), (x0, W / 2 - 0.03, 0.04)], 0.02, iron, square=True, poly=True)
        for sy in (-1, 1):
            arch = _gothic((x1 - x0) / 2 - 0.05, 0.0, 0.2, 0.34, n=8)
            tube(f"Arch{k}{sy}", [(x0 + (x1 - x0) / 2 + u, sy * (0.03 + v), 0.03) for u, v in arch], 0.014, gl, closed=True, square=True, poly=True)
        sphere(f"Rivet{k}", 0.025, (x0, 0, 0.02), gl, seg=8, rings=4)
    for sx in (-1, 1):
        box(f"End{sx}", (0.06, W + 0.1, H), (sx * (L / 2 - 0.03), 0, H / 2), iron, bevel=0.012)
    set_group("Glow")
    lit = opal()
    box("Strip", (L - 0.12, W - 0.1, 0.04), (0, 0, 0.12), lit, bevel=0.01)
    for sy in (-1, 1):
        for k in range(16):
            g = _mark()
            x = -L / 2 + 0.25 + k * 0.5
            prism(f"SideLight{sy}{k}", _gothic(0.16, 0.13, 0.28, 0.35, n=6), -(W / 2 + 0.025), 0.02, lit)
            _xform(g, Matrix.Translation((x, 0, 0)))
            if sy > 0:
                _xform(g, Matrix.Rotation(math.pi, 4, "Z"))
    set_group("Main")
    return _dims()


def corridor_uplighter(M):
    """A wall piece: a 6-stud iron trough on bat-wing brackets, lit along its open top and a slot beneath."""
    gl, iron = gilt(), M["iron"]
    L, D = 6.0, 0.6
    zb, zt = 0.45, 1.05
    box("Back", (L, 0.06, zt - zb + 0.1), (0, -0.03, (zb + zt) / 2), iron, bevel=0.01)
    box("Floor", (L, D, 0.06), (0, -D / 2, zb + 0.03), iron, bevel=0.01)
    box("Front", (L, 0.06, zt - zb), (0, -D, (zb + zt) / 2), iron, bevel=0.012)
    box("Frieze", (L - 0.2, 0.02, 0.36), (0, -D - 0.035, (zb + zt) / 2), M["crimsonin"], bevel=0.004)
    box("MouldLow", (L + 0.04, 0.08, 0.05), (0, -D - 0.02, zb + 0.03), iron, bevel=0.012)
    box("MouldHigh", (L + 0.04, 0.08, 0.05), (0, -D - 0.02, zt - 0.02), gl, bevel=0.012)
    n = 12
    for k in range(n):
        x = -L / 2 + 0.25 + (L - 0.5) * (k + 0.5) / n
        tube(f"Arcade{k}", [(x + u, -D - 0.05, z) for u, z in _gothic(0.2, zb + 0.1, zt - 0.3, zt - 0.1, n=8)], 0.013, gl, closed=True, square=True, poly=True)
        foil(f"Trefoil{k}", x, -D - 0.055, zt - 0.27, 0.05, gl, lobes=3, thick=0.007, centre=False)
    for sx in (-1, 1):
        box(f"EndCap{sx}", (0.06, D, zt - zb + 0.06), (sx * (L / 2 - 0.03), -D / 2 - 0.01, (zb + zt) / 2), iron, bevel=0.012)
        lathe(f"EndFinial{sx}", [(0.06, zt), (0.04, zt + 0.12), (0, zt + 0.22)], gl, seg=8, loc=(sx * (L / 2 - 0.03), -D - 0.02, 0))
    for k, x in enumerate((-2.2, 0.0, 2.2)):
        wing = [(0.0, zb), (-0.45, zb), (-0.34, zb - 0.1), (-0.38, zb - 0.2), (-0.24, zb - 0.22), (-0.2, zb - 0.32), (-0.04, zb - 0.42), (0.0, zb - 0.45)]
        prism(f"Bracket{k}", wing, x, 0.05, iron, plane="YZ", bevel=0.006)
        sphere(f"BracketBoss{k}", 0.04, (x, -0.18, zb - 0.16), gl, seg=8, rings=4)
    set_group("Glow")
    lit = opal()
    box("Uplight", (L - 0.14, D - 0.12, 0.05), (0, -D / 2, zt - 0.12), lit, bevel=0.01)
    box("Slot", (L - 0.4, 0.06, 0.02), (0, -D / 2, zb - 0.005), lit, bevel=0.004)
    set_group("Main")
    return _dims()


# ================================================================== WALL SCONCES (back face on y = 0, out toward -Y)

def _plate(name, outline, M, gl, depth=0.06, inset=True):
    """A pointed iron wall plate whose back is on y = 0, with a gilt rim and a crimson inset."""
    prism(name, outline, -depth / 2, depth, M["iron"], bevel=0.012)
    tube(f"{name}Rim", [(u, -depth - 0.008, z) for u, z in _shrink(outline, 0.04)], 0.012, gl, closed=True, square=True, poly=True)
    if inset:
        prism(f"{name}Inset", _shrink(outline, 0.08), -depth - 0.005, 0.012, M["crimsonin"])


def sconce_iron_hand(M):
    """An iron hand reaching out of a lace cuff in the wall, gripping a burning torch."""
    gl, iron = gilt(), M["iron"]
    _plate("Plate", _gothic(0.36, 0.0, 1.75, 2.3, n=10), M, gl)
    for z in (0.2, 2.05):
        sphere(f"Rivet{z}", 0.035, (0, -0.07, z), M["brass"], seg=8, rings=4)
    # the cuff: a flared iron sleeve out of the plate, a gilt band and a fluted ruffle of lace
    s = _mark()
    lathe("Sleeve", [(0.15, 0.0), (0.17, 0.05), (0.17, 0.16), (0.18, 0.2), (0, 0.2)], iron, seg=24)
    lathe("Cuff", [(0.17, 0.16), (0.2, 0.18), (0.2, 0.25), (0.16, 0.27), (0, 0.27)], gl, seg=24)
    lathe("Ruffle", [(0.12, 0.25), (0.18, 0.28), (0.23, 0.33), (0.22, 0.35), (0.16, 0.31), (0.1, 0.3)], flat("Lace", (0.3, 0.27, 0.24), 0.7, dirt=0.7),
          seg=36, flute=(14, 0.22))
    _xform(s, Matrix.Translation((0, -0.06, 0.95)) @ _aim((0, -1, 0.35)))
    # the hand: a slim palm, four long fingers curled round the haft, a thumb over them (a vampire's hand)
    wrist = Vector((0, -0.7, 1.16))
    haft0, haft1 = Vector((-0.16, -0.8, 0.7)), Vector((-0.16, -1.02, 2.0))
    hd = (haft1 - haft0).normalized()
    grip = haft0.lerp(haft1, 0.36)
    side = hd.cross(Vector((1, 0, 0))).normalized()
    palm = grip + Vector((0.17, 0.07, 0.0))
    hand = [("cap", (0, -0.28, 1.04), tuple(wrist), 0.095), ("cap", tuple(wrist), tuple(palm + Vector((0.02, 0.06, -0.05))), 0.085),
            ("ell", tuple(palm), 0.1, (0.75, 1.0, 1.15)), ("ball", tuple(palm + Vector((0.04, 0.02, -0.08))), 0.07)]
    nails = []
    for k in range(4):
        c = grip + hd * (-0.13 + 0.085 * k)
        r = 0.1
        ring = [c + Vector((math.cos(a_), 0, 0)) * r + side * math.sin(a_) * r for a_ in [math.radians(v) for v in (-10, 40, 95, 150, 195)]]
        pts = [c + Vector((0.2, 0.05, 0))] + ring
        rr = 0.044 - 0.004 * k
        for j in range(len(pts) - 1):
            hand.append(("cap", tuple(pts[j]), tuple(pts[j + 1]), rr * (1 - 0.13 * j)))
            if j in (1, 2):
                hand.append(("ball", tuple(pts[j + 1]), rr * (1.05 - 0.13 * j)))      # knuckles
        nails.append((pts[-1], (pts[-1] - pts[-2]).normalized()))
    th = [palm + Vector((0.0, -0.08, 0.12)), grip + Vector((0.1, -0.12, 0.2)), grip + Vector((0.0, -0.13, 0.24)), grip + Vector((-0.08, -0.1, 0.23))]
    for j in range(3):
        hand.append(("cap", tuple(th[j]), tuple(th[j + 1]), 0.048 - 0.008 * j))
    nails.append((th[-1], (th[-1] - th[-2]).normalized()))
    blob("Hand", hand, iron, res=0.012, target=3600, pit=0.004, pit_scale=0.03)
    for k, (p_, d_) in enumerate(nails):
        spike(f"Claw{k}", tuple(p_ + d_ * 0.03), tuple(d_), 0.022, 0.07, M["felt"], seg=6)
    for k in range(3):        # tendons on the back of the hand
        sweep(f"Tendon{k}", [tuple(wrist + Vector((0.02 * (k - 1), 0, 0.06))), tuple(palm + Vector((0.08, -0.02 + 0.04 * (k - 1), 0.06)))], 0.012, iron,
              r1=0.008, seg=5, per=1)
    hoop("Ring", tuple(palm + Vector((0.06, -0.03, 0.0))), 0.06, "X", gl, thick=0.016)
    # the torch
    s = _mark()
    tube("Haft", [(0, 0, 0), (0, 0, 1.12)], 0.05, M["oakdark"], poly=True)
    for z in (0.1, 0.92, 1.02):
        hoop(f"HaftBand{z}", (0, 0, z), 0.056, "Z", iron, thick=0.012)
    lathe("Cresset", [(0.05, 1.08), (0.13, 1.12), (0.19, 1.22), (0.2, 1.3), (0.18, 1.3), (0.17, 1.24), (0.11, 1.15), (0.0, 1.14)], iron, seg=16)
    lathe("Pitch", [(0, 1.14), (0.16, 1.17), (0.17, 1.26), (0.13, 1.33), (0, 1.35)], soot(), seg=14, jitter=(0.06, 3))
    for k in range(6):
        a = k / 6 * TAU
        tube(f"Strap{k}", [(math.cos(a) * 0.1, math.sin(a) * 0.1, 1.14), (math.cos(a) * 0.2, math.sin(a) * 0.2, 1.28), (math.cos(a) * 0.23, math.sin(a) * 0.23, 1.4)],
             0.011, iron)
    _xform(s, Matrix.Translation(haft0) @ _aim(hd))
    top = haft0 + hd * 1.32
    set_group("Glow")
    fm = fire()
    for k, (h, w, lean, yaw) in enumerate(((0.62, 0.13, 0.05, 0.0), (0.46, 0.09, 0.07, 1.9), (0.42, 0.09, -0.06, 4.0), (0.34, 0.08, 0.05, 3.0))):
        b = top + Vector((math.cos(yaw) * 0.05 * (k > 0), math.sin(yaw) * 0.05 * (k > 0), -0.02))
        tongue(f"Fire{k}", tuple(b), h, w, lean, yaw, fm, seg=8, rows=10)
    set_group("Main")
    return _dims()


def sconce_bat_wing(M):
    """Three candles on scrolled arms before an iron bat whose wings spread flat on the wall."""
    gl, iron, wax, cr = gilt(), M["iron"], wax_mat(), M["crimson"]
    zc = 1.3
    # the wings: scalloped membranes with finger bones, flat on the wall
    for sx in (-1, 1):
        fingers = [(0.2, zc + 0.15), (1.25, zc + 0.75), (1.3, zc + 0.15), (1.0, zc - 0.35), (0.55, zc - 0.55)]
        outline = [(0.12, zc + 0.3), (0.7, zc + 0.62), (1.25, zc + 0.75)]
        for a, b in zip(fingers[1:], fingers[2:]):
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            ins = 0.85
            outline.append((m[0] * ins + 0.2 * (1 - ins), m[1] * ins + zc * (1 - ins)))
            outline.append(b)
        outline += [(0.3, zc - 0.32), (0.12, zc - 0.2)]
        prism(f"Wing{sx}", [(sx * x, z) for x, z in outline], -0.02, 0.04, iron, bevel=0.006)
        prism(f"WingIn{sx}", [(sx * x, z) for x, z in _shrink(outline, 0.07)], -0.055, 0.012, M["crimsonin"])
        for j, f in enumerate(fingers[1:]):
            tube(f"Finger{sx}{j}", [(sx * 0.2, -0.065, zc + 0.15), (sx * (0.2 + (f[0] - 0.2) * 0.5), -0.07, zc + 0.15 + (f[1] - zc - 0.15) * 0.55 + 0.05),
                                    (sx * f[0], -0.065, f[1])], 0.02, iron)
        cone(f"Claw{sx}", 0.025, 0.0, 0.09, (sx * 1.25, -0.065, zc + 0.8), gl, verts=6)
    # the body and head, sculpted
    bat_sculpt("Bat", Vector((0, -0.14, zc - 0.36)), 0.82, iron, cr, wax, target=3000)
    # three scrolled candle arms from under the body
    tips = []
    for k, sx in enumerate((-1, 0, 1)):
        ex, ez = sx * 0.62, zc - 0.05 + (0.25 if sx == 0 else 0.0)
        ey = -0.55
        arm = [(0, -0.12, zc - 0.32), (sx * 0.15, -0.3, zc - 0.5), (sx * 0.4, -0.45, zc - 0.45), (ex, ey, ez - 0.25), (ex, ey, ez - 0.06)]
        tube(f"Arm{k}", arm, 0.026, iron)
        tube(f"Curl{k}", [(sx * 0.15, -0.3, zc - 0.5), (sx * 0.08, -0.33, zc - 0.62), (sx * 0.16, -0.36, zc - 0.68), (sx * 0.22, -0.35, zc - 0.6)], 0.016, iron)
        lathe(f"Bobeche{k}", [(0, ez - 0.08), (0.12, ez - 0.03), (0.14, ez), (0.1, ez + 0.01), (0, ez)], gl, seg=16, loc=(ex, ey, 0))
        tips.append(cup_candle(f"K{k}", ex, ey, ez, 0.42, wax, gl, r=0.045, pan=0.06, sleeve=cr))
    lathe("Drop", [(0, zc - 0.85), (0.03, zc - 0.78), (0.05, zc - 0.6), (0.07, zc - 0.42), (0, zc - 0.3)], iron, seg=10, loc=(0, -0.1, 0))
    flames("Flame", tips, h=0.13)
    return _dims()


def sconce_gas_bracket(M):
    """A jointed brass gas bracket: a wall rose with a tap, a swing arm with a knuckle, a frosted tulip shade."""
    gl, br, iron = gilt(), M["brass"], M["iron"]
    zr = 0.75
    s = _mark()
    lathe("Rose", [(0, 0.0), (0.26, 0.0), (0.26, 0.04), (0.2, 0.1), (0.1, 0.16), (0.07, 0.24), (0, 0.24)], br, seg=32)
    hoop("RoseBead", (0, 0, 0.06), 0.235, "Z", gl, thick=0.012)
    _xform(s, Matrix.Translation((0, 0, zr)) @ _aim((0, -1, 0)))
    box("Backplate", (0.42, 0.04, 1.1), (0, -0.02, zr + 0.05), iron, bevel=0.012)
    foil("PlateFoil", 0, -0.045, zr + 0.45, 0.07, gl, thick=0.01)
    # the tap: a T key on the first pipe, and the pipe out to the knuckle
    p0 = Vector((0, -0.24, zr))
    k1 = Vector((0, -0.62, zr + 0.05))
    tube("Pipe0", [tuple(p0), tuple(k1)], 0.032, br, poly=True)
    lathe("TapBody", [(0, -0.07), (0.05, -0.06), (0.055, 0.06), (0, 0.07)], br, seg=12)
    _xform(len(P.PARTS) - 1, Matrix.Translation((0, -0.4, zr + 0.02)))
    tube("TapKey", [(-0.1, -0.4, zr + 0.1), (0.1, -0.4, zr + 0.1)], 0.018, br, poly=True)
    tube("TapStem", [(0, -0.4, zr + 0.06), (0, -0.4, zr + 0.1)], 0.015, br, poly=True)
    sphere("Knuckle", 0.07, tuple(k1), br, seg=14, rings=8)
    # the swung arm, out and a little to the side, rising to the burner
    k2 = Vector((0.32, -1.08, zr + 0.12))
    tube("Pipe1", [tuple(k1), tuple(k2)], 0.03, br, poly=True)
    sphere("Knuckle2", 0.06, tuple(k2), br, seg=12, rings=6)
    tube("Riser", [tuple(k2), tuple(k2 + Vector((0, 0, 0.3)))], 0.03, br, poly=True)
    tube("Brace", [(0, -0.05, zr - 0.35), (0.04, -0.4, zr - 0.25), (0.2, -0.8, zr - 0.05), tuple(k2 + Vector((0, 0.05, -0.04)))], 0.02, iron)
    tube("BraceCurl", [(0.04, -0.4, zr - 0.25), (0.0, -0.45, zr - 0.38), (0.08, -0.5, zr - 0.42), (0.12, -0.46, zr - 0.33)], 0.014, iron)
    zg = k2.z + 0.3
    lathe("Gallery", [(0, zg), (0.05, zg), (0.1, zg + 0.04), (0.14, zg + 0.08), (0.14, zg + 0.12), (0.11, zg + 0.12), (0, zg + 0.08)], br, seg=24,
          loc=(k2.x, k2.y, 0))
    for j in range(8):
        a = j / 8 * TAU
        tube(f"Prong{j}", [(k2.x + math.cos(a) * 0.12, k2.y + math.sin(a) * 0.12, zg + 0.1), (k2.x + math.cos(a) * 0.19, k2.y + math.sin(a) * 0.19, zg + 0.24)],
             0.01, gl, poly=True)
    # the pull chain with a gilt acorn
    chain("Pull", 0.0, -0.62, zr - 0.5, zr, br, pitch=0.08, r=0.02, h=0.035, thick=0.006)
    lathe("Acorn", [(0, zr - 0.68), (0.03, zr - 0.64), (0.035, zr - 0.56), (0.028, zr - 0.52), (0, zr - 0.5)], gl, seg=10, loc=(0, -0.62, 0))
    set_group("Glow")
    lathe("Tulip", [(0.07, zg + 0.1), (0.12, zg + 0.16), (0.2, zg + 0.3), (0.24, zg + 0.46), (0.24, zg + 0.56), (0.21, zg + 0.62)], opal(), seg=40,
          flute=(6, 0.08), loc=(k2.x, k2.y, 0))
    lathe("TulipIn", [(0.2, zg + 0.61), (0.225, zg + 0.555), (0.225, zg + 0.46), (0.19, zg + 0.3), (0.11, zg + 0.165), (0.065, zg + 0.105)], opal(), seg=40,
          flute=(6, 0.08), loc=(k2.x, k2.y, 0))
    lathe("Mantle", [(0, zg + 0.1), (0.04, zg + 0.12), (0.05, zg + 0.22), (0.03, zg + 0.28), (0, zg + 0.29)], mantle(), seg=12, loc=(k2.x, k2.y, 0))
    set_group("Main")
    return _dims()


def sconce_mirror(M):
    """A gilt lancet mirror with two candle arms before it, crystal drops on their pans: the mirror doubles the light."""
    gl, wax = gilt(), wax_mat()
    hw, z0, zs, za = 0.42, 0.2, 1.55, 2.15
    out = _gothic(hw + 0.14, z0 - 0.12, zs, za + 0.16, n=12)
    prism("Back", out, -0.03, 0.06, lacquer(), bevel=0.01)
    tube("Frame", [(u, -0.075, z) for u, z in _gothic(hw + 0.06, z0 - 0.04, zs, za + 0.06, n=12)], 0.05, gl, closed=True, square=True, poly=True)
    tube("FrameIn", [(u, -0.09, z) for u, z in _gothic(hw, z0, zs, za, n=12)], 0.018, gl, closed=True, square=True, poly=True)
    # crockets up the frame's head and a crest finial
    for i, t in enumerate((0.25, 0.45, 0.65, 0.82)):
        for sx in (-1, 1):
            ang = t * math.pi / 2
            u = sx * (hw + 0.1) * math.cos(ang) ** 0.9
            z = zs + (za + 0.1 - zs) * math.sin(ang) ** 0.75
            sphere(f"Crocket{i}{sx}", 0.04, (u, -0.09, z), gl, seg=8, rings=4)
    foil("CrestFoil", 0, -0.1, za + 0.32, 0.1, gl, thick=0.016)
    lathe("Finial", [(0, za + 0.42), (0.04, za + 0.44), (0.03, za + 0.55), (0, za + 0.62)], gl, seg=10, loc=(0, -0.1, 0))
    lathe("Apron", [(0, z0 - 0.4), (0.04, z0 - 0.36), (0.07, z0 - 0.24), (0.06, z0 - 0.12), (0, z0 - 0.1)], gl, seg=12, loc=(0, -0.08, 0))
    # two scrolled arms from the frame's foot, out and up to the candles
    tips, drops = [], []
    for sx in (-1, 1):
        ex, ey, ez = sx * 0.55, -0.5, 0.7
        arm = [(sx * 0.2, -0.09, z0 + 0.15), (sx * 0.3, -0.22, z0 + 0.05), (sx * 0.48, -0.38, z0 + 0.15), (ex, ey, ez - 0.25), (ex, ey, ez - 0.05)]
        tube(f"Arm{sx}", arm, 0.024, gl)
        tube(f"Curl{sx}", [(sx * 0.3, -0.22, z0 + 0.05), (sx * 0.24, -0.26, z0 - 0.05), (sx * 0.32, -0.3, z0 - 0.1), (sx * 0.38, -0.28, z0 - 0.02)], 0.015, gl)
        lathe(f"Bobeche{sx}", [(0, ez - 0.08), (0.15, ez - 0.03), (0.17, ez), (0.12, ez + 0.01), (0, ez)], gl, seg=16, loc=(ex, ey, 0))
        tips.append(cup_candle(f"K{sx}", ex, ey, ez, 0.4, wax, gl, r=0.045, pan=0.06, sleeve=M["crimson"]))
        for j in range(6):
            a = j / 6 * TAU
            drops.append((ex + math.cos(a) * 0.15, ey + math.sin(a) * 0.15, ez - 0.04))
    set_group("Glass")
    for k, (x, y, z) in enumerate(drops):
        lathe(f"Drop{k}", [(0, z), (0.025, z - 0.04), (0.022, z - 0.1), (0, z - 0.17)], M["glassclear"], seg=6, loc=(x, y, 0))
    set_group("Mirror")
    prism("Glass", _gothic(hw, z0, zs, za, n=12), -0.075, 0.02, flat("Silvered", (0.72, 0.74, 0.77), 0.04, metal=1.0, dirt=0.3))
    set_group("Main")
    flames("Flame", tips, h=0.13)
    return _dims()


# ================================================================== ORGANIC MODELLING (sculpt-quality creatures)

MB_K = 1.5      # a metaball's visible radius is about 2/3 of its field radius (stiffness 2, threshold 0.6): radii below are visible sizes


def blob(name, elems, mat, res=0.02, target=10000, pit=0.008, pit_scale=0.06, seed=0):
    """An organic form as one implicit surface: metaball elements blended together, converted to a mesh, pitted with a fine
    noise (weathering, skin) and decimated to `target` triangles. elems:
      ("ball", centre, r)  ("ell", centre, r, (sx, sy, sz))  ("cap", p0, p1, r)   (a leading "-" on the kind subtracts it)."""
    nm = name.replace(".", "_")
    mb = bpy.data.metaballs.new(nm)
    mb.resolution = mb.render_resolution = res
    mb.threshold = 0.6
    for el in elems:
        kind, neg = el[0].lstrip("-"), el[0].startswith("-")
        if kind == "ball":
            e = mb.elements.new(type="BALL")
            e.co, e.radius = el[1], el[2] * MB_K
        elif kind == "ell":
            e = mb.elements.new(type="ELLIPSOID")
            e.co, e.radius = el[1], el[2] * MB_K
            e.size_x, e.size_y, e.size_z = el[3]
        else:
            p0, p1 = Vector(el[1]), Vector(el[2])
            d = p1 - p0
            e = mb.elements.new(type="CAPSULE")
            e.co = (p0 + p1) / 2
            e.radius = el[3] * MB_K
            e.size_x = max(d.length / 2, 1e-4)
            e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()) if d.length > 1e-6 else Quaternion()
        e.use_negative = neg
    ob = bpy.data.objects.new(nm, mb)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    if pit > 0:
        tex = bpy.data.textures.new(f"{nm}Pit", "CLOUDS")
        tex.noise_scale = pit_scale
        tex.noise_depth = 2
        md = ob.modifiers.new("Pit", "DISPLACE")
        md.texture = tex
        md.strength = pit
        md.mid_level = 0.5
        md.texture_coords = "GLOBAL"
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if tris > target:
        dm = ob.modifiers.new("Decimate", "DECIMATE")
        dm.ratio = target / tris
    return P._finish(ob, mat, 0)


def spike(name, centre, direction, r, h, mat, seg=6):
    """A light smooth spike (tooth, claw tip, spine ridge) centred at `centre` like a cone() primitive, pointing along direction."""
    d = Vector(direction).normalized()
    s = _mark()
    lathe(name, [(0, 0), (r, 0), (r * 0.62, h * 0.45), (0, h)], mat, seg=seg)
    _xform(s, Matrix.Translation(Vector(centre) - d * h / 2) @ _aim(d))


def membrane(name, bone_a, bone_b, mat, n=10, rows=6, sag=0.12, thick=0.012, scallop=0.0):
    """A wing membrane stretched between two bones (point lists from the shared root), sagging toward `sag` between them;
    scallop cuts the free edge into an arc."""
    A, B = smooth_path(bone_a, 3), smooth_path(bone_b, 3)
    ra = [A[int(i / n * (len(A) - 1))] for i in range(n + 1)]
    rb = [B[int(i / n * (len(B) - 1))] for i in range(n + 1)]
    grid = []
    for i in range(n + 1):
        a, b = Vector(ra[i]), Vector(rb[i])
        row = []
        mid_drop = scallop * (i / n) ** 2
        for j in range(rows + 1):
            t = j / rows
            p = a.lerp(b, t)
            p.z -= sag * math.sin(t * math.pi) * (i / n) + mid_drop * math.sin(t * math.pi)
            row.append(tuple(p))
        grid.append(row)
    return _mesh(name, grid, mat, thick)


def weathered_stone(name, tint=(0.62, 0.6, 0.55), soot=None):
    """Limestone with lichen blooms, darker weather staining in the hollows and (soot = (x, y, z, radius)) soot streaking up
    from a flame. The bake's edge wear chips the edges."""
    m = material(name, "NH_Limestone", tint=tint, scale=0.28, wear=0.6, dirt=1.0)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = bs.inputs["Base Color"].links[0].from_socket
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # lichen: patchy yellow-green and grey-white blooms
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.5
    nz.inputs["Detail"].default_value = 8
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.56
    ramp.color_ramp.elements[1].position = 0.66
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs[7].default_value = (0.33, 0.36, 0.16, 1)
    nt.links.new(src, mix.inputs[6])
    mf = nt.nodes.new("ShaderNodeMath"); mf.operation = "MULTIPLY"; mf.inputs[1].default_value = 0.7
    nt.links.new(ramp.outputs["Color"], mf.inputs[0])
    nt.links.new(mf.outputs[0], mix.inputs["Factor"])
    out = mix.outputs[2]
    if soot:
        sx, sy, sz, sr = soot
        # distance from the flame's column in plan, and height above the flame's base
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        dx = nt.nodes.new("ShaderNodeMath"); dx.operation = "SUBTRACT"; dx.inputs[1].default_value = sx
        dy = nt.nodes.new("ShaderNodeMath"); dy.operation = "SUBTRACT"; dy.inputs[1].default_value = sy
        nt.links.new(sep.outputs[0], dx.inputs[0]); nt.links.new(sep.outputs[1], dy.inputs[0])
        cmb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(dx.outputs[0], cmb.inputs[0]); nt.links.new(dy.outputs[0], cmb.inputs[1])
        ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
        nt.links.new(cmb.outputs[0], ln.inputs[0])
        near = nt.nodes.new("ShaderNodeMapRange")
        near.inputs["From Min"].default_value = sr
        near.inputs["From Max"].default_value = 0.0
        nt.links.new(ln.outputs["Value"], near.inputs["Value"])
        up = nt.nodes.new("ShaderNodeMapRange")
        up.inputs["From Min"].default_value = sz - 0.1
        up.inputs["From Max"].default_value = sz + 0.35
        nt.links.new(sep.outputs[2], up.inputs["Value"])
        streak = nt.nodes.new("ShaderNodeTexNoise")
        streak.inputs["Scale"].default_value = 6
        stv = nt.nodes.new("ShaderNodeVectorMath"); stv.operation = "MULTIPLY"; stv.inputs[1].default_value = (9.0, 9.0, 0.6)
        nt.links.new(geo.outputs["Position"], stv.inputs[0])
        nt.links.new(stv.outputs[0], streak.inputs["Vector"])
        m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
        nt.links.new(near.outputs["Result"], m1.inputs[0]); nt.links.new(up.outputs["Result"], m1.inputs[1])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
        nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(streak.outputs["Fac"], m2.inputs[1])
        m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = 1.6
        m3.use_clamp = True
        nt.links.new(m2.outputs[0], m3.inputs[0])
        sm = nt.nodes.new("ShaderNodeMix"); sm.data_type = "RGBA"
        sm.inputs[7].default_value = (0.025, 0.022, 0.02, 1)
        nt.links.new(out, sm.inputs[6])
        nt.links.new(m3.outputs[0], sm.inputs["Factor"])
        out = sm.outputs[2]
    # the base colour feeds _weather's chain; re-route its input
    for l in list(nt.links):
        if l.from_socket == src and l.to_node not in (mix,):
            nt.links.new(out, l.to_socket)
    return m


def roughen(ob, amt=0.008, scale=0.05):
    """Add a fine noise displacement (bark, bone, weathering) to a mesh piece; the join applies it."""
    tex = bpy.data.textures.new(f"{ob.name}Rough", "CLOUDS")
    tex.noise_scale = scale
    tex.noise_depth = 2
    md = ob.modifiers.new("Rough", "DISPLACE")
    md.texture = tex
    md.strength = amt
    md.texture_coords = "GLOBAL"
    ob.modifiers.move(len(ob.modifiers) - 1, 0)
    return ob


def bat_sculpt(prefix, pos, s, mat, eye, fang, face=0.0, target=2600):
    """A sculpted bat's body and head (facing -Y, rotated by `face`), feet at pos: a furred barrel body, a short neck, a
    pug-nosed head with big ribbed ears, deep eyes and fangs, haunches and clawed feet. Returns the world shoulder points."""
    m = _mark()
    S = lambda *v: tuple(c * s for c in v)       # noqa: E731
    elems = [("ell", S(0, 0.0, 0.42), 0.17 * s, (0.95, 0.8, 1.35)),          # body
             ("ell", S(0, -0.05, 0.56), 0.13 * s, (1.1, 0.8, 0.9)),           # chest
             ("cap", S(0, -0.02, 0.66), S(0, -0.04, 0.74), 0.08 * s),         # neck
             ("ell", S(0, -0.06, 0.82), 0.13 * s, (1.1, 1.0, 0.95)),          # head
             ("ell", S(0, -0.17, 0.79), 0.06 * s, (1.1, 0.8, 0.8)),           # muzzle
             ("ball", S(0, -0.22, 0.81), 0.035 * s),                          # nose leaf
             ("-ell", S(0, -0.2, 0.745), 0.03 * s, (1.6, 1.0, 0.6))]          # mouth
    for sx in (-1, 1):
        elems += [("ball", S(sx * 0.09, -0.12, 0.85), 0.04 * s),              # brow
                  ("-ball", S(sx * 0.06, -0.165, 0.84), 0.024 * s),           # eye socket
                  ("ell", S(sx * 0.08, 0.0, 0.25), 0.08 * s, (0.9, 1.0, 1.2)),  # haunch
                  ("cap", S(sx * 0.08, -0.01, 0.2), S(sx * 0.07, -0.05, 0.05), 0.04 * s),   # leg
                  ("ell", S(sx * 0.07, -0.08, 0.02), 0.04 * s, (0.9, 1.4, 0.5))]           # foot
    blob(f"{prefix}Body", elems, mat, res=0.012 * max(s, 0.6), target=target, pit=0.004 * s, pit_scale=0.03 * s)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.018 * s, S(sx * 0.06, -0.17, 0.84), eye, seg=8, rings=6)
        spike(f"{prefix}Fang{sx}", S(sx * 0.025, -0.215, 0.74), (0, 0, -1), 0.012 * s, 0.05 * s, fang, seg=6)
        # big ears: a cupped blade with a rib up its middle
        root = Vector(S(sx * 0.07, -0.04, 0.9))
        tip = Vector(S(sx * 0.17, 0.0, 1.12))
        sweep(f"{prefix}Ear{sx}", [tuple(root), tuple(root.lerp(tip, 0.5) + Vector(S(sx * 0.02, -0.01, 0))), tuple(tip)], 0.055 * s, mat, r1=0.004 * s,
              seg=10, per=3, flat_k=(1.0, 0.3))
        sweep(f"{prefix}EarRib{sx}", [tuple(root + Vector(S(0, -0.012, 0.02))), tuple(root.lerp(tip, 0.7) + Vector(S(0, -0.012, 0)))], 0.008 * s, mat,
              r1=0.003 * s, seg=5, per=1)
        for j in range(3):
            spike(f"{prefix}Toe{sx}{j}", S(sx * (0.05 + 0.02 * j), -0.13, 0.015), (0, -1, -0.6), 0.01 * s, 0.05 * s, mat, seg=5)
    _xform(m, Matrix.Translation(pos) @ Matrix.Rotation(face, 4, "Z"))
    M_ = Matrix.Translation(pos) @ Matrix.Rotation(face, 4, "Z")
    return [M_ @ Vector(S(sx * 0.12, -0.02, 0.58)) for sx in (-1, 1)]


def bat_wing(prefix, sx, shoulder, wrist, tips, body_pt, mat, s=1.0):
    """A bat's wing: an arm bone to the wrist, finger bones to the tips, membranes stretched between them and back to the body,
    sagging between the bones (scalloped trailing edge)."""
    sweep(f"{prefix}Arm{sx}", [shoulder, tuple(Vector(shoulder).lerp(Vector(wrist), 0.5) + Vector((0, 0.02, 0.04 * s))), wrist], 0.03 * s, mat, r1=0.018 * s,
          seg=8, per=3)
    sphere(f"{prefix}Wrist{sx}", 0.026 * s, wrist, mat, seg=8, rings=6)
    bones = []
    for j, t in enumerate(tips):
        mid = Vector(wrist).lerp(Vector(t), 0.5) + Vector((0, 0.03 * s, 0.02 * s))
        b = [wrist, tuple(mid), t]
        sweep(f"{prefix}Finger{sx}{j}", b, 0.016 * s, mat, r1=0.005 * s, seg=7, per=3)
        bones.append(b)
    for j in range(len(bones) - 1):
        membrane(f"{prefix}Mem{sx}{j}", bones[j], bones[j + 1], mat, n=8, rows=6, sag=0.0, thick=0.01 * s, scallop=0.0)
    last = bones[-1]
    trail = [wrist, tuple(Vector(wrist).lerp(Vector(body_pt), 0.5) + Vector((0, 0, -0.08 * s))), body_pt]
    membrane(f"{prefix}MemBody{sx}", last, trail, mat, n=8, rows=6, sag=0.0, thick=0.01 * s)


def wolf_sculpt(prefix, pos, yaw, s, mat, dark, eye, target=2600):
    """A sculpted howling wolf's head and neck, muzzle raised, facing out toward yaw: skull, brow, long muzzle with an open
    jaw and fangs, ears laid back, a ruff of fur tufts."""
    m = _mark()
    S = lambda *v: tuple(c * s for c in v)       # noqa: E731
    elems = [("cap", S(0, 0.07, -0.18), S(0, 0.0, 0.0), 0.075 * s),            # neck
             ("ell", S(0, 0.0, 0.04), 0.115 * s, (1.0, 1.15, 0.95)),          # skull
             ("ell", S(0, -0.07, 0.1), 0.06 * s, (1.6, 0.8, 0.6)),            # brow
             ("cap", S(0, -0.08, 0.07), S(0, -0.18, 0.14), 0.055 * s), ("cap", S(0, -0.18, 0.14), S(0, -0.29, 0.21), 0.036 * s),         # muzzle
             ("ball", S(0, -0.305, 0.222), 0.028 * s),                         # nose
             ("cap", S(0, -0.06, -0.02), S(0, -0.25, 0.08), 0.036 * s),       # lower jaw
             ("-ell", S(0, -0.23, 0.135), 0.028 * s, (0.9, 1.8, 0.7)),          # the open mouth
             ("ball", S(0, 0.02, -0.08), 0.075 * s)]                            # throat
    for sx in (-1, 1):
        elems += [("ball", S(sx * 0.07, -0.06, 0.02), 0.05 * s), ("-ball", S(sx * 0.05, -0.1, 0.11), 0.018 * s)]
    blob(f"{prefix}Head", elems, mat, res=0.012 * max(s, 0.6), target=target, pit=0.004 * s, pit_scale=0.03 * s)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.014 * s, S(sx * 0.048, -0.105, 0.112), eye, seg=8, rings=5)
        sweep(f"{prefix}Ear{sx}", [S(sx * 0.06, 0.01, 0.11), S(sx * 0.085, 0.02, 0.24), S(sx * 0.1, 0.04, 0.36)], 0.06 * s, mat, r1=0.004 * s, seg=8, per=3,
              flat_k=(1.0, 0.4))
        spike(f"{prefix}Fang{sx}", S(sx * 0.022, -0.25, 0.155), (0, 0.2, -1), 0.008 * s, 0.035 * s, dark, seg=5)
        spike(f"{prefix}LowFang{sx}", S(sx * 0.02, -0.22, 0.1), (0, 0, 1), 0.007 * s, 0.03 * s, dark, seg=5)
    rnd = random.Random(int(s * 100) + len(prefix))
    for k in range(14):
        a = math.radians(-100 + 200 * k / 13)
        base = Vector(S(math.sin(a) * 0.1, 0.03 + math.cos(a) * 0.06, -0.08 + rnd.uniform(-0.03, 0.03)))
        d = Vector((math.sin(a), 0.6 + math.cos(a) * 0.5, -0.5)).normalized()
        sweep(f"{prefix}Tuft{k}", [tuple(base), tuple(base + d * 0.08 * s), tuple(base + d * 0.15 * s + Vector(S(0, 0.02, -0.03)))], 0.03 * s, mat,
              r1=0.003 * s, seg=6, per=2, flat_k=(1.0, 0.45))
    _xform(m, Matrix.Translation(pos) @ Matrix.Rotation(yaw + math.pi / 2, 4, "Z"))


def sconce_gargoyle(M):
    """A gothic cathedral gargoyle crouched on a moulded corbel: haunches and clawed feet gripping the ledge, a hunched spine
    with vertebral ridges, folded bat wings, a long neck and a snarling head (heavy brow, deep eyes, horns, pointed ears,
    jaws wide open on fangs and a tongue). It clutches an iron cresset in its forepaws, set on an iron bracket from the wall;
    the fire rises into its jaws, soot streaking the stone above."""
    gl, iron = gilt(), M["iron"]
    z0 = 0.78                 # the corbel's top
    fx, fy = 0.0, -1.06       # the cresset's centre
    st = weathered_stone("GargoyleStone", tint=(0.36, 0.35, 0.32), soot=(fx, fy, z0 + 0.45, 0.42))
    cs = weathered_stone("CorbelStone", tint=(0.34, 0.33, 0.31), soot=(fx, fy, z0 + 0.1, 0.5))
    # ---- the corbel: an ogee bracket under a moulded cap, its back on the wall
    prof = [(0.0, 0.0), (-0.12, 0.0)]
    for i in range(1, 15):
        t = i / 14
        prof.append((-0.12 - 0.66 * t, 0.06 + 0.58 * (0.5 - 0.5 * math.cos(t * math.pi)) - 0.06 * math.sin(t * math.pi * 2)))
    prof += [(-0.86, z0 - 0.08), (-0.9, z0 - 0.02), (-0.9, z0), (0.0, z0)]
    prism("Corbel", prof, 0, 0.82, cs, plane="YZ", bevel=0.02)
    lathe("CapRoll", [(0.0, -0.45), (0.045, -0.4), (0.05, 0.0), (0.045, 0.4), (0.0, 0.45)], cs, seg=12)
    _xform(len(P.PARTS) - 1, Matrix.Translation((0, -0.9, z0 - 0.05)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    for k, x in enumerate((-0.26, 0.0, 0.26)):
        sphere(f"Ballflower{k}", 0.05, (x, -0.62, 0.42), cs, seg=10, rings=6, scale=(1, 0.8, 1))
        for j in range(3):
            a = j / 3 * TAU + math.pi / 2
            sphere(f"BallPetal{k}{j}", 0.03, (x + math.cos(a) * 0.045, -0.64, 0.42 + math.sin(a) * 0.045), cs, seg=8, rings=4, scale=(1, 0.6, 1))
    # ---- the body: one sculpted form
    Z = z0
    body = []
    for sx in (-1, 1):
        body += [("ell", (sx * 0.17, -0.27, Z + 0.22), 0.19, (0.85, 1.0, 0.9)),                    # haunch
                 ("cap", (sx * 0.2, -0.3, Z + 0.22), (sx * 0.28, -0.6, Z + 0.34), 0.095),          # thigh
                 ("cap", (sx * 0.28, -0.6, Z + 0.34), (sx * 0.25, -0.66, Z + 0.08), 0.065),        # shin
                 ("ell", (sx * 0.24, -0.72, Z + 0.045), 0.065, (0.9, 1.4, 0.55)),                 # foot
                 ("ball", (sx * 0.17, -0.44, Z + 0.78), 0.1),                                      # shoulder
                 ("cap", (sx * 0.18, -0.45, Z + 0.76), (sx * 0.29, -0.55, Z + 0.52), 0.07),        # upper arm
                 ("cap", (sx * 0.29, -0.55, Z + 0.52), (sx * 0.16, -0.84, Z + 0.46), 0.055),       # forearm
                 ("ell", (sx * 0.13, -0.88, Z + 0.47), 0.055, (0.9, 1.2, 0.7)),                   # forepaw
                 ("ball", (sx * 0.12, -0.9, Z + 1.05), 0.06),                                      # cheekbone
                 ("ball", (sx * 0.11, -0.5, Z + 0.62), 0.09)]                                      # flank
    body += [("ball", (0, -0.2, Z + 0.32), 0.17), ("ball", (0, -0.27, Z + 0.5), 0.19), ("ball", (0, -0.36, Z + 0.68), 0.19),
             ("ell", (0, -0.46, Z + 0.64), 0.17, (1.1, 0.9, 1.05)),                              # chest
             ("ball", (0, -0.45, Z + 0.44), 0.12),                                                # belly
             ("cap", (0, -0.5, Z + 0.8), (0, -0.7, Z + 0.98), 0.095),                            # neck
             ("ell", (0, -0.77, Z + 1.07), 0.17, (1.0, 1.1, 0.9)),                                # skull
             ("ell", (0, -0.9, Z + 1.14), 0.09, (1.7, 0.7, 0.55)),                              # brow
             ("cap", (0, -0.86, Z + 1.04), (0, -1.07, Z + 1.0), 0.078),                            # muzzle
             ("ball", (0, -1.1, Z + 1.03), 0.052),                                               # nose
             ("cap", (0, -0.82, Z + 0.93), (0, -1.04, Z + 0.82), 0.06),                           # lower jaw
             ("-ell", (0, -1.01, Z + 0.925), 0.07, (1.1, 1.5, 0.75)),                              # the open mouth
             ("-ball", (0.088, -0.92, Z + 1.085), 0.034), ("-ball", (-0.088, -0.92, Z + 1.085), 0.034)]   # eye sockets
    blob("Body", body, st, res=0.016, target=8700, pit=0.01, pit_scale=0.05)
    # eyes deep in their sockets, nostrils
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.024, (sx * 0.085, -0.925, Z + 1.083), M["felt"], seg=8, rings=6)
        sphere(f"Nostril{sx}", 0.015, (sx * 0.028, -1.14, Z + 1.04), M["felt"], seg=6, rings=4)
    # horns, ears
    for sx in (-1, 1):
        sweep(f"Horn{sx}", [(sx * 0.08, -0.8, Z + 1.18), (sx * 0.17, -0.74, Z + 1.33), (sx * 0.24, -0.62, Z + 1.42), (sx * 0.28, -0.5, Z + 1.4),
                             (sx * 0.29, -0.43, Z + 1.32)], 0.06, st, r1=0.008, seg=10, per=5)
        for j in range(2):
            t = 0.2 + j * 0.25
            p = smooth_path([(sx * 0.08, -0.8, Z + 1.18), (sx * 0.17, -0.74, Z + 1.33), (sx * 0.24, -0.62, Z + 1.42)], 6)
            q = p[int(t * (len(p) - 1))]
            hoop(f"HornRing{sx}{j}", tuple(q), 0.056 - 0.008 * j, "Z", st, thick=0.006)
        sweep(f"Ear{sx}", [(sx * 0.14, -0.74, Z + 1.1), (sx * 0.23, -0.7, Z + 1.17), (sx * 0.31, -0.66, Z + 1.23)], 0.05, st, r1=0.004, seg=8, per=3,
              flat_k=(1.0, 0.35))
    # teeth: fangs and a row each side, a tongue lolling over the lower jaw
    teeth = flat("Tooth", (0.62, 0.58, 0.48), 0.5, dirt=0.8)
    for sx in (-1, 1):
        spike(f"Fang{sx}", (sx * 0.05, -1.04, Z + 0.95), (0, -0.15, -1), 0.02, 0.095, teeth, seg=8)
        spike(f"LowFang{sx}", (sx * 0.045, -1.0, Z + 0.87), (0, -0.2, 1), 0.017, 0.075, teeth, seg=8)
        for j in range(4):
            y = -0.99 + 0.04 * j
            spike(f"Tooth{sx}{j}", (sx * (0.055 - 0.004 * j), y, Z + 0.955 + 0.005 * j), (0, 0, -1), 0.009, 0.035, teeth, seg=5)
            spike(f"LowTooth{sx}{j}", (sx * (0.05 - 0.004 * j), y + 0.01, Z + 0.885 + 0.008 * j), (0, 0, 1), 0.008, 0.03, teeth, seg=5)
    sweep("Tongue", [(0, -0.88, Z + 0.91), (0, -0.98, Z + 0.89), (0, -1.07, Z + 0.85), (0, -1.1, Z + 0.78)], 0.035, flat("Tongue", (0.3, 0.12, 0.1), 0.6),
          r1=0.015, seg=10, per=4, flat_k=(0.4, 1.0), up=(0, 0, 1))
    # the spine's vertebral ridge, and the tail curling off the corbel's side
    spine = smooth_path([(0, -0.2, Z + 0.4), (0, -0.24, Z + 0.62), (0, -0.33, Z + 0.84), (0, -0.48, Z + 0.96), (0, -0.66, Z + 1.1)], 4)
    for j, p in enumerate(spine[1:-1]):
        s = _mark()
        lathe(f"Ridge{j}", [(0, 0), (0.035, 0), (0.02, 0.045), (0, 0.09 - 0.003 * j)], st, seg=7)
        q = Vector(p)
        d = (Vector(spine[min(j + 2, len(spine) - 1)]) - Vector(spine[j])).normalized()
        outw = d.cross(Vector((1, 0, 0))).normalized()
        if outw.y < 0 and outw.z < 0:
            outw = -outw
        _xform(s, Matrix.Translation(q + outw * 0.1) @ _aim(outw + d * -0.3))
    sweep("Tail", [(0, -0.14, Z + 0.22), (0.18, -0.14, Z + 0.06), (0.36, -0.2, Z + 0.02), (0.44, -0.34, Z - 0.12), (0.43, -0.42, Z - 0.34),
                   (0.45, -0.34, Z - 0.48)], 0.075, st, r1=0.02, seg=10, per=4)
    spike("TailBarb", (0.45, -0.33, Z - 0.55), (0, 0, -1), 0.06, 0.13, st, seg=8)
    # claws over the ledge edge and round the cresset
    for sx in (-1, 1):
        for j in range(3):
            x = sx * (0.18 + 0.055 * j)
            sweep(f"Claw{sx}{j}", [(x, -0.76, Z + 0.05), (x, -0.86, Z + 0.04), (x, -0.91, Z - 0.02), (x, -0.9, Z - 0.08)], 0.022, st, r1=0.004, seg=7, per=3)
        for j in range(3):
            a = (j - 1) * 0.5
            x0 = sx * 0.13
            sweep(f"HandClaw{sx}{j}", [(x0, -0.9 + j * 0.03, Z + 0.47), (x0 - sx * 0.07, -0.93 + j * 0.03, Z + 0.46 + 0.02 * a),
                                       (x0 - sx * 0.11, -0.95 + j * 0.03, Z + 0.4)], 0.018, st, r1=0.004, seg=7, per=3)
    # folded wings rising off the shoulders: an arm bone to the wrist, three fingers, membranes between them
    for sx in (-1, 1):
        root = (sx * 0.16, -0.3, Z + 0.78)
        wrist = (sx * 0.36, -0.2, Z + 1.36)
        f1 = [wrist, (sx * 0.44, -0.14, Z + 1.02), (sx * 0.47, -0.1, Z + 0.62), (sx * 0.42, -0.12, Z + 0.3)]
        f2 = [wrist, (sx * 0.52, -0.14, Z + 1.16), (sx * 0.6, -0.12, Z + 0.9), (sx * 0.62, -0.12, Z + 0.64)]
        f3 = [wrist, (sx * 0.5, -0.16, Z + 1.36), (sx * 0.66, -0.14, Z + 1.24), (sx * 0.72, -0.12, Z + 1.06)]
        arm = [root, (sx * 0.28, -0.26, Z + 1.1), wrist]
        sweep(f"WingArm{sx}", arm, 0.05, st, r1=0.03, seg=9, per=4)
        for j, f in enumerate((f1, f2, f3)):
            sweep(f"WingFinger{sx}{j}", f, 0.028, st, r1=0.008, seg=7, per=3)
        spike(f"WingThumb{sx}", (sx * 0.38, -0.2, Z + 1.44), (sx * 0.4, 0, 1), 0.03, 0.12, st, seg=8)
        membrane(f"MembraneA{sx}", f3, f2, st, n=10, rows=5, sag=0.07, thick=0.014)
        membrane(f"MembraneB{sx}", f2, f1, st, n=10, rows=5, sag=0.07, thick=0.014)
        trail = [wrist, (sx * 0.3, -0.18, Z + 1.0), (sx * 0.27, -0.2, Z + 0.62), (sx * 0.25, -0.22, Z + 0.36)]
        membrane(f"MembraneC{sx}", f1, trail, st, n=10, rows=4, sag=0.05, thick=0.014)
    # ---- the iron: a cresset in its forepaws, on a bracket from the corbel's face; a collar chained to the wall
    zc = Z + 0.36
    lathe("Cresset", [(0.04, zc - 0.06), (0.09, zc - 0.03), (0.15, zc + 0.05), (0.19, zc + 0.16), (0.2, zc + 0.2), (0.18, zc + 0.2), (0.17, zc + 0.16),
                      (0.13, zc + 0.07), (0.07, zc + 0.0), (0, zc - 0.01)], iron, seg=20, loc=(fx, fy, 0))
    for j in range(8):
        a = j / 8 * TAU
        tube(f"CressetBar{j}", [(fx + math.cos(a) * 0.17, fy + math.sin(a) * 0.17, zc + 0.15), (fx + math.cos(a) * 0.23, fy + math.sin(a) * 0.23, zc + 0.3),
                                (fx + math.cos(a) * 0.25, fy + math.sin(a) * 0.25, zc + 0.36)], 0.011, iron)
    hoop("CressetRim", (fx, fy, zc + 0.2), 0.195, "Z", iron, thick=0.014)
    lathe("Coals", [(0, zc + 0.08), (0.16, zc + 0.12), (0.16, zc + 0.18), (0.08, zc + 0.22), (0, zc + 0.23)], coal(), seg=14, jitter=(0.1, 7), loc=(fx, fy, 0))
    tube("Stem", [(fx, fy, zc - 0.05), (fx, fy, Z - 0.3)], 0.03, iron, poly=True)
    lathe("StemKnop", [(0, Z - 0.1), (0.05, Z - 0.08), (0.06, Z - 0.03), (0.05, Z + 0.02), (0, Z + 0.04)], iron, seg=12, loc=(fx, fy, 0))
    bracket = [(fx, fy, Z - 0.3), (fx, fy + 0.04, Z - 0.42), (fx, -0.8, Z - 0.46), (fx, -0.66, Z - 0.42)]
    tube("Bracket", bracket, 0.03, iron, square=True)
    tube("BracketCurl", [(fx, fy + 0.04, Z - 0.42), (fx, fy + 0.12, Z - 0.56), (fx, fy + 0.22, Z - 0.54), (fx, fy + 0.2, Z - 0.46)], 0.018, iron)
    box("Staple", (0.18, 0.03, 0.14), (fx, -0.655, Z - 0.42), iron, bevel=0.008)
    for sx in (-1, 1):
        sphere(f"StapleRivet{sx}", 0.018, (fx + sx * 0.06, -0.672, Z - 0.42), iron, seg=6, rings=4)
    hoop("Collar", (0, -0.62, Z + 0.93), 0.105, "Y", iron, thick=0.018)
    _xform(len(P.PARTS) - 1, Matrix.Translation((0, -0.6, Z + 0.92)) @ Matrix.Rotation(-0.75, 4, "X") @ Matrix.Translation((0, 0.6, -(Z + 0.92))))
    tube("CollarChain", [(0, -0.52, Z + 0.98), (0, -0.3, Z + 1.0), (0, -0.04, Z + 0.98)], 0.012, iron, square=True)
    box("WallPlate", (0.14, 0.03, 0.18), (0, -0.015, Z + 0.98), iron, bevel=0.008)
    set_group("Glow")
    fm = fire()
    rnd = random.Random(4231)
    for k in range(6):
        a = k / 6 * TAU
        r = 0.0 if k == 0 else 0.09
        tongue(f"Fire{k}", (fx + math.cos(a) * r, fy + math.sin(a) * r, zc + 0.18), 0.5 if k == 0 else rnd.uniform(0.3, 0.42), 0.12 if k == 0 else 0.08,
               rnd.uniform(-0.05, 0.05), rnd.uniform(0, TAU), fm, seg=8, rows=10)
    # flames licking from its jaws
    for k, (yaw, h) in enumerate(((0.0, 0.2), (2.0, 0.15), (4.0, 0.14))):
        tongue(f"Breath{k}", (0, -1.03, Z + 0.9), h, 0.04, 0.02, yaw, fm, seg=8, rows=8)
    set_group("Main")
    return _dims()


def sconce_witchlight(M):
    """A violet witchlight: a crescent moon of iron on the wall, a violet glass orb lantern hung from its lower horn."""
    gl, iron = gilt(), M["iron"]
    zc, R = 1.3, 0.8
    cres = WS.crescent(0.0, zc, R, shift=0.42, n=40, tilt=0.35)
    prism("Moon", cres, -0.04, 0.08, iron, bevel=0.012)
    tube("MoonRim", [(u, -0.088, z) for u, z in WS.offset(WS.ccw(cres), -0.035)], 0.012, gl, closed=True, square=True, poly=True)
    # pierced stars on the moon's face
    rnd = random.Random(4222)
    for k in range(6):
        a = math.radians(120 + 120 * k / 5)
        x, z = math.cos(a + 0.35) * R * 0.75 - 0.0, zc + math.sin(a + 0.35) * R * 0.75
        pts = []
        for j in range(10):
            rr = 0.05 if j % 2 == 0 else 0.02
            aa = math.pi / 2 + j * math.pi / 5
            pts.append((x + math.cos(aa) * rr, z + math.sin(aa) * rr))
        prism(f"Star{k}", pts, -0.09, 0.01, gl)
    # the arm from the lower horn and the lantern
    lo = min(cres, key=lambda p: p[1])
    hx = lo[0] + 0.05
    arm = [(hx, -0.08, lo[1] + 0.1), (hx - 0.1, -0.35, lo[1] + 0.3), (hx - 0.25, -0.55, lo[1] + 0.32), (hx - 0.3, -0.62, lo[1] + 0.2)]
    tube("Arm", arm, 0.026, iron)
    tube("ArmCurl", [(hx - 0.1, -0.35, lo[1] + 0.3), (hx - 0.05, -0.42, lo[1] + 0.42), (hx - 0.12, -0.46, lo[1] + 0.46), (hx - 0.16, -0.42, lo[1] + 0.4)],
         0.016, iron)
    lx, ly = hx - 0.3, -0.62
    zl = lo[1] - 0.35
    chain("Hang", lx, ly, zl + 0.3, lo[1] + 0.2, iron, pitch=0.1, r=0.026, h=0.05, thick=0.008)
    lathe("Cap", [(0, zl + 0.36), (0.05, zl + 0.34), (0.12, zl + 0.24), (0.13, zl + 0.2), (0, zl + 0.2)], iron, seg=16, loc=(lx, ly, 0))
    lathe("Base", [(0, zl - 0.26), (0.13, zl - 0.2), (0.12, zl - 0.16), (0, zl - 0.17)], iron, seg=16, loc=(lx, ly, 0))
    for j in range(4):
        a = j / 4 * TAU + math.pi / 4
        pts = [(lx + math.cos(a) * 0.21 * math.sin(t * math.pi) + math.cos(a) * 0.12 * (1 - math.sin(t * math.pi)), ly + math.sin(a) * 0.21 * math.sin(t * math.pi) +
                math.sin(a) * 0.12 * (1 - math.sin(t * math.pi)), zl - 0.19 + 0.4 * t) for t in [i / 8 for i in range(9)]]
        tube(f"Band{j}", pts, 0.012, iron, poly=True)
    lathe("Drop", [(0, zl - 0.5), (0.025, zl - 0.45), (0.04, zl - 0.32), (0.05, zl - 0.25), (0, zl - 0.24)], gl, seg=8, loc=(lx, ly, 0))
    star = []
    for j in range(10):
        rr = 0.07 if j % 2 == 0 else 0.03
        aa = math.pi / 2 + j * math.pi / 5
        star.append((math.cos(aa) * rr, math.sin(aa) * rr))
    g = _mark()
    prism("HangStar", star, 0, 0.02, gl)
    _xform(g, Matrix.Translation((lx, ly, zl - 0.6)))
    set_group("Glass")
    sphere("Orb", 0.2, (lx, ly, zl), M["glassclear"], seg=20, rings=12)
    set_group("Glow")
    gv = glow_violet()
    sphere("Wisp", 0.09, (lx, ly, zl - 0.03), gv, seg=12, rings=8, scale=(1, 1, 1.2))
    tongue("Flame", (lx, ly, zl - 0.02), 0.16, 0.05, 0.015, 0.0, gv, seg=8, rows=8)
    set_group("Main")
    return _dims()


def stained_lightbox(M):
    """A wall lightbox: a lit lancet of stained glass (a crescent cradling a crimson rose over a gilt key) in a gothic
    iron case with a crocketed hood; the glass is the `_Stained` canvas, the light leaks round it as `_Glow`."""
    gl, iron = gilt(), M["iron"]
    hw, z0, zs, za = 0.95, 0.35, 2.85, 3.85
    D = 0.32
    case = _gothic(hw + 0.2, z0 - 0.2, zs, za + 0.2, n=14)
    prism("Case", case, -D / 2, D, iron, bevel=0.02)
    tube("Rim", [(u, -D - 0.025, z) for u, z in _gothic(hw + 0.08, z0 - 0.08, zs, za + 0.08, n=14)], 0.045, gl, closed=True, square=True, poly=True)
    tube("RimIn", [(u, -D - 0.035, z) for u, z in _gothic(hw - 0.02, z0 + 0.02, zs, za - 0.02, n=14)], 0.018, iron, closed=True, square=True, poly=True)
    # hood mould with crockets, a finial, carved label stops
    hood = _gothic(hw + 0.3, zs - 0.3, zs, za + 0.34, n=14)[2:]
    tube("Hood", [(u, -D - 0.06, z) for u, z in hood], 0.05, iron, square=True, poly=True)
    for i, (u, z) in enumerate(hood[1:-1:2]):
        sphere(f"Crocket{i}", 0.05, (u * 1.03, -D - 0.08, z + 0.06), gl, seg=8, rings=4)
    lathe("Finial", [(0, za + 0.35), (0.06, za + 0.38), (0.05, za + 0.55), (0.08, za + 0.6), (0, za + 0.78)], gl, seg=12, loc=(0, -D - 0.06, 0))
    for sx in (-1, 1):
        sphere(f"LabelStop{sx}", 0.09, (sx * (hw + 0.3), -D - 0.07, zs - 0.34), iron, seg=10, rings=6)
        foil(f"StopFoil{sx}", sx * (hw + 0.3), -D - 0.16, zs - 0.34, 0.05, gl, thick=0.008)
    # the sill and its brackets
    box("Sill", (2 * hw + 0.6, 0.5, 0.12), (0, -0.25, z0 - 0.26), M["stone"], bevel=0.02)
    for sx in (-1, 1):
        prism(f"SillBracket{sx}", [(0.0, z0 - 0.32), (-0.42, z0 - 0.32), (-0.3, z0 - 0.5), (0.0, z0 - 0.7)], sx * (hw - 0.1), 0.1, M["stone"], plane="YZ",
              bevel=0.01)
    # saddle bars across the glass
    for z in (1.15, 2.0):
        tube(f"Saddle{z}", [(-hw, -D - 0.04, z), (hw, -D - 0.04, z)], 0.016, iron, square=True, poly=True)
    set_group("Stained")
    prism("Glass", [(x, z) for x, z in WS.ccw(_gothic(hw, z0, zs, za, n=24))], -D - 0.01, 0.02, flat("StainedTmp", (0.5, 0.2, 0.2), 0.3))
    set_group("Glow")
    ring = _gothic(hw + 0.035, z0 - 0.035, zs, za + 0.035, n=24)
    tube("Leak", [(u, -D - 0.005, z) for u, z in ring], 0.018, glow_amber(), closed=True, square=True, poly=True)
    set_group("Main")
    return _dims()


# ================================================================== GLOWING PIECES

def moon_orb(M):
    """A cratered moon of frosted glass, cradled in an iron crescent with gilt stars on fine chains (moonlight blue)."""
    gl, iron = gilt(), M["iron"]
    zc, R = 1.75, 1.4
    # the crescent cradle round the moon's lower left, on a rod from the rose
    arc = [(math.cos(a) * (R + 0.16), 0, zc + math.sin(a) * (R + 0.16)) for a in [math.radians(100 + 200 * i / 20) for i in range(21)]]
    sweep("Cradle", arc, 0.1, iron, prof=lambda t: 0.03 + 0.15 * math.sin(t * math.pi) ** 0.8, seg=10, per=1, flat_k=(1.0, 0.45))
    tube("CradleGilt", [(x * 1.0, -0.055, z) for x, _, z in arc[3:-3]], 0.012, gl, poly=True)
    top = arc[0]
    tube("Rod", [top, (top[0], 0, 4.6)], 0.032, iron, poly=True)
    for z in (3.75, 4.2):
        lathe(f"Knop{z}", [(0, z - 0.06), (0.05, z - 0.04), (0.065, z), (0.05, z + 0.04), (0, z + 0.06)], gl, seg=12, loc=(top[0], 0, 0))
    ceil_rose("Rose", 4.9, 0.34, iron, gl)
    _xform(len(P.PARTS) - 3, Matrix.Translation((top[0], 0, 0)))
    # gilt stars hanging on fine chains from the cradle
    for k, (t, L) in enumerate(((0.35, 0.5), (0.6, 0.7), (0.85, 0.4))):
        p = arc[int(t * 20)]
        chain(f"StarChain{k}", p[0], 0, p[2] - L, p[2] - 0.05, gl, pitch=0.07, r=0.016, h=0.03, thick=0.005)
        pts = []
        for j in range(10):
            rr = 0.09 if j % 2 == 0 else 0.038
            aa = math.pi / 2 + j * math.pi / 5
            pts.append((p[0] + math.cos(aa) * rr, p[2] - L - 0.09 + math.sin(aa) * rr))
        prism(f"Star{k}", pts, 0, 0.025, gl)
    # the moon: a sphere pocked with craters (the Glow)
    set_group("Glow")
    ob = sphere("Moon", R, (0, 0, zc), glow_moon(), seg=64, rings=32)
    rnd = random.Random(42071)
    craters = [(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized(), rnd.uniform(0.1, 0.32)) for _ in range(22)]
    for v in ob.data.vertices:          # (the sphere's mesh is centred on its own origin)
        n = v.co.normalized()
        d = 0.0
        for c, r in craters:
            ang = math.acos(max(-1, min(1, n.dot(c))))
            if ang < r * 1.35:
                x = ang / r
                d += (-0.06 * (1 - x * x) if x < 1 else 0.025 * math.sin((x - 1) / 0.35 * math.pi)) * r / 0.3
        v.co = n * R * (1 + d)
    set_group("Main")
    return _dims()


# ================================================================== FLOOR CANDELABRA AND TORCHERES

def _wolf_head(prefix, pos, yaw, s, mat, dark, eye):
    """A howling wolf's head (muzzle raised), facing out toward yaw."""
    m = _mark()
    sphere(f"{prefix}Skull", 1.0, (0, 0, 0), mat, seg=14, rings=10, scale=(0.15 * s, 0.17 * s, 0.15 * s))
    sweep(f"{prefix}Muzzle", [(0, -0.08 * s, 0.02 * s), (0, -0.2 * s, 0.12 * s), (0, -0.28 * s, 0.24 * s)], 0.09 * s, mat, r1=0.045 * s, seg=10, per=3)
    sphere(f"{prefix}Nose", 0.035 * s, (0, -0.29 * s, 0.27 * s), dark, seg=8, rings=5)
    sweep(f"{prefix}Jaw", [(0, -0.06 * s, -0.06 * s), (0, -0.18 * s, 0.02 * s), (0, -0.24 * s, 0.12 * s)], 0.05 * s, mat, r1=0.03 * s, seg=8, per=3)
    for sx in (-1, 1):
        cone(f"{prefix}Ear{sx}", 0.05 * s, 0.0, 0.16 * s, (sx * 0.08 * s, 0.06 * s, 0.14 * s), mat, verts=5, rot=(-0.5, sx * 0.35, 0))
        sphere(f"{prefix}Eye{sx}", 0.02 * s, (sx * 0.07 * s, -0.12 * s, 0.08 * s), eye, seg=6, rings=4)
    for k in range(9):
        a = math.radians(-80 + 160 * k / 8)
        cone(f"{prefix}Ruff{k}", 0.05 * s, 0.0, 0.18 * s, (math.sin(a) * 0.13 * s, 0.05 * s + math.cos(a) * 0.06 * s, -0.12 * s), mat, verts=4,
             rot=(2.4, 0, a))
    _xform(m, Matrix.Translation(pos) @ Matrix.Rotation(yaw + math.pi / 2, 4, "Z"))


def torchere_wolves(M):
    """A fire bowl held high on a fluted iron column, three iron wolves howling up from its collar (the Pack's)."""
    gl, iron = gilt(), M["iron"]
    lathe("Plinth", [(0, 0), (0.8, 0), (0.82, 0.05), (0.78, 0.14), (0.62, 0.2), (0.6, 0.48), (0.66, 0.52), (0.66, 0.58), (0.45, 0.66), (0.32, 0.78),
                     (0.28, 0.86), (0, 0.86)], iron, seg=6)
    hoop("PlinthBead", (0, 0, 0.55), 0.665, "Z", gl, thick=0.014)
    ap = 0.6 * math.cos(math.pi / 6)
    for k in range(6):
        g = _mark()
        tube(f"Lancet{k}", [(u, -ap - 0.01, z) for u, z in _gothic(0.15, 0.24, 0.38, 0.47, n=6)], 0.012, gl, closed=True, square=True, poly=True)
        _xform(g, Matrix.Rotation(math.radians(30 + 60 * k - 90 - 30), 4, "Z"))
    for k in range(3):
        a = k / 3 * TAU + math.pi / 2
        claw_foot(f"Foot{k}", math.cos(a) * 0.78, math.sin(a) * 0.78, a, M, r=0.1)
    lathe("Column", [(0, 0.84), (0.14, 0.84), (0.12, 4.1), (0, 4.1)], iron, seg=40, flute=(12, 0.12))
    for z in (1.0, 2.5):
        lathe(f"Knop{z}", [(0, z - 0.1), (0.14, z - 0.08), (0.2, z), (0.14, z + 0.08), (0, z + 0.1)], gl if z > 2 else iron, seg=24)
    lathe("Collar", [(0, 4.05), (0.15, 4.05), (0.28, 4.15), (0.3, 4.28), (0.24, 4.36), (0, 4.36)], iron, seg=32)
    lathe("WolfCollar", [(0, 3.3), (0.14, 3.3), (0.3, 3.42), (0.34, 3.56), (0.26, 3.66), (0.13, 3.7), (0, 3.7)], iron, seg=32)
    hoop("WolfCollarGilt", (0, 0, 3.56), 0.34, "Z", gl, thick=0.016)
    for k in range(3):
        a = k / 3 * TAU - math.pi / 2
        wolf_sculpt(f"Wolf{k}", (math.cos(a) * 0.4, math.sin(a) * 0.4, 3.82), a, 2.1, iron, wax_mat(), M["crimson"], target=2400)
    # the bowl: wide and shallow, gilt rim, scalloped lip, glowing coals and flames
    zb = 4.5
    lathe("Bowl", [(0, zb - 0.14), (0.25, zb - 0.12), (0.55, zb), (0.75, zb + 0.18), (0.82, zb + 0.32), (0.78, zb + 0.34), (0.7, zb + 0.22), (0.5, zb + 0.08),
                   (0, zb + 0.04)], iron, seg=48)
    hoop("BowlRim", (0, 0, zb + 0.33), 0.81, "Z", gl, thick=0.022)
    for k in range(16):
        a = k / 16 * TAU
        cone(f"Point{k}", 0.05, 0.0, 0.16, (math.cos(a) * 0.82, math.sin(a) * 0.82, zb + 0.42), iron, verts=4)
    lathe("Coals", [(0, zb + 0.18), (0.68, zb + 0.22), (0.6, zb + 0.3), (0.3, zb + 0.36), (0, zb + 0.38)], coal(), seg=24, jitter=(0.12, 9))
    set_group("Glow")
    fm = fire()
    rnd = random.Random(4223)
    for k in range(7):
        a = k / 7 * TAU
        r = 0.0 if k == 0 else 0.35
        tongue(f"Fire{k}", (math.cos(a) * r, math.sin(a) * r, zb + 0.3), 0.95 if k == 0 else rnd.uniform(0.5, 0.7), 0.2 if k == 0 else 0.13,
               rnd.uniform(-0.08, 0.08), rnd.uniform(0, TAU), fm, seg=8, rows=10)
    set_group("Main")
    return _dims()


def candelabra_dead_tree(M):
    """A floor candelabra cast as a bare dead tree: roots for feet, a twisted trunk, candles on its branch tips."""
    gl, iron, wax = gilt(), M["iron"], wax_mat()
    rnd = random.Random(4224)
    # roots splaying over a rough disc of iron 'earth'
    lathe("Earth", [(0, 0), (0.75, 0), (0.78, 0.04), (0.7, 0.1), (0.4, 0.16), (0, 0.18)], iron, seg=24, jitter=(0.08, 3))
    for k in range(6):
        a = k / 6 * TAU + rnd.uniform(-0.2, 0.2)
        c, s_ = math.cos(a), math.sin(a)
        roughen(sweep(f"Root{k}", [(c * 0.1, s_ * 0.1, 0.9), (c * 0.3, s_ * 0.3, 0.4), (c * 0.6, s_ * 0.6, 0.15), (c * 0.92, s_ * 0.92, 0.05)], 0.12, iron,
                      r1=0.025, seg=9, per=4), 0.012, 0.04)
    trunk = [(0, 0, 0.1), (0.04, 0.02, 1.0), (-0.05, 0.03, 2.0), (0.03, -0.02, 2.8), (0.0, 0.0, 3.3)]
    roughen(sweep("Trunk", trunk, 0.2, iron, r1=0.11, seg=16, per=6), 0.025, 0.06)
    for k in range(3):        # twisting ridges up the trunk
        pts = []
        for i in range(13):
            t = i / 12
            z = 0.2 + 3.0 * t
            a = k / 3 * TAU + t * 3.5
            r = 0.2 - 0.08 * t
            pts.append((math.cos(a) * r, math.sin(a) * r, z))
        sweep(f"Ridge{k}", pts, 0.045, iron, r1=0.03, seg=6, per=2)
    sphere("Knot", 0.1, (0.15, -0.08, 1.6), iron, seg=10, rings=6, scale=(0.8, 0.9, 1.2))
    lathe("Hollow", [(0.0, 1.55), (0.06, 1.58), (0.06, 1.68), (0.0, 1.7)], M["felt"], seg=10, loc=(0.17, -0.12, 0))
    # branches and twigs, candles on the tips
    tips = []
    branches = [(0.0, 3.0, 4.4, 1.0), (2.1, 2.6, 3.9, 1.1), (4.2, 2.9, 4.1, 0.95), (1.05, 3.3, 5.0, 0.6), (3.15, 3.3, 4.8, 0.7)]
    for k, (a, z0, ztip, reach) in enumerate(branches):
        c, s_ = math.cos(a), math.sin(a)
        mid = (c * reach * 0.6, s_ * reach * 0.6, (z0 + ztip) / 2 + 0.1)
        tip = (c * reach, s_ * reach, ztip)
        roughen(sweep(f"Branch{k}", [(c * 0.05, s_ * 0.05, z0), mid, tip], 0.08, iron, r1=0.03, seg=9, per=4), 0.012, 0.04)
        tw = (c * reach * 0.7 + s_ * 0.3, s_ * reach * 0.7 - c * 0.3, ztip - 0.3)
        sweep(f"Twig{k}", [mid, tw], 0.04, iron, r1=0.018, seg=6, per=1)
        tips.append(cup_candle(f"K{k}", tip[0], tip[1], tip[2], 0.32 + 0.06 * (k % 2), wax, gl, r=0.045, pan=0.1))
        tips.append(cup_candle(f"T{k}", tw[0], tw[1], tw[2], 0.24, wax, gl, r=0.04, pan=0.08))
        for j in range(2):
            p = Vector(mid).lerp(Vector(tip), 0.3 + 0.4 * j)
            q = p + Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(0.15, 0.3)))
            sweep(f"Spur{k}{j}", [tuple(p), tuple(q)], 0.022, iron, r1=0.006, seg=5, per=1)
    tips.append(cup_candle("Top", 0, 0, 3.3, 0.45, wax, gl, r=0.055, pan=0.12))
    flames("Flame", tips, h=0.14)
    return _dims()


def torchere_alabaster(M):
    """An uplighter: a lit alabaster bowl on a clustered gothic shaft with a stiff-leaf capital, black marble foot."""
    gl, iron = gilt(), M["iron"]
    bm_ = black_marble()
    box("Foot", (1.1, 1.1, 0.16), (0, 0, 0.08), bm_, bevel=0.025)
    box("FootStep", (0.85, 0.85, 0.14), (0, 0, 0.23), bm_, bevel=0.02)
    lathe("Base", [(0, 0.3), (0.32, 0.3), (0.34, 0.36), (0.3, 0.42), (0.26, 0.48), (0.28, 0.54), (0, 0.54)], iron, seg=32)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Ball{sx}{sy}", 0.06, (sx * 0.42, sy * 0.42, 0.36), gl, seg=10, rings=6)
    lathe("Core", [(0, 0.5), (0.13, 0.5), (0.11, 5.0), (0, 5.0)], iron, seg=24)
    for k in range(4):
        a = k / 4 * TAU + math.pi / 4
        lathe(f"Shaft{k}", [(0, 0.5), (0.06, 0.5), (0.05, 5.0), (0, 5.0)], iron, seg=12, loc=(math.cos(a) * 0.14, math.sin(a) * 0.14, 0))
    for z in (1.8, 3.4):
        lathe(f"Annulet{z}", [(0, z - 0.05), (0.22, z - 0.04), (0.24, z), (0.22, z + 0.04), (0, z + 0.05)], gl, seg=24)
    lathe("Capital", [(0, 4.95), (0.22, 4.95), (0.26, 5.02), (0.24, 5.08), (0.34, 5.2), (0.4, 5.3), (0.36, 5.34), (0, 5.34)], iron, seg=32)
    stiff_leaf("Leaf", 0.2, 5.0, 8, 0.28, iron, pitch=70, droop=0.35, width=0.14, knob=0.05, kseg=(6, 4))
    # gilt cradle of four straps round the bowl
    for k in range(4):
        a = k / 4 * TAU
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Cradle{k}", [(c * 0.3, s_ * 0.3, 5.3), (c * 0.6, s_ * 0.6, 5.4), (c * 0.86, s_ * 0.86, 5.62), (c * 0.92, s_ * 0.92, 5.78)], 0.02, gl)
        sphere(f"CradleKnob{k}", 0.035, (c * 0.92, s_ * 0.92, 5.8), gl, seg=8, rings=4)
    set_group("Glow")
    lathe("Bowl", [(0.1, 5.32), (0.4, 5.36), (0.68, 5.46), (0.86, 5.62), (0.9, 5.74), (0.86, 5.74), (0.82, 5.64), (0.64, 5.5), (0.38, 5.42), (0, 5.4)],
          flat("Alabaster", (0.98, 0.86, 0.66), 0.5), seg=48)
    set_group("Main")
    return _dims()


def candle_hearse(M):
    """A triangular iron hearse of fifteen candles on a tall twisted pedestal with clawed feet."""
    gl, iron, wax = gilt(), M["iron"], wax_mat()
    for k in range(3):
        a = k / 3 * TAU + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.1, s_ * 0.1, 1.0), (c * 0.3, s_ * 0.3, 0.6), (c * 0.55, s_ * 0.55, 0.3), (c * 0.68, s_ * 0.68, 0.22)], 0.045, iron, square=True)
        claw_foot(f"Foot{k}", c * 0.72, s_ * 0.72, a, M, r=0.11)
        tube(f"LegCurl{k}", [(c * 0.3, s_ * 0.3, 0.6), (c * 0.42, s_ * 0.42, 0.74), (c * 0.5, s_ * 0.5, 0.66), (c * 0.45, s_ * 0.45, 0.58)], 0.022, iron)
    lathe("Hub", [(0, 0.85), (0.16, 0.88), (0.2, 1.0), (0.16, 1.14), (0, 1.18)], iron, seg=24)
    twist("Shaft", 1.15, 4.1, 0.09, iron, lobes=4, depth=0.25, turns=4.0, seg=20, rings=90)
    lathe("Knop", [(0, 2.5), (0.12, 2.52), (0.16, 2.6), (0.12, 2.68), (0, 2.7)], gl, seg=24)
    lathe("Head", [(0, 4.05), (0.14, 4.05), (0.18, 4.16), (0.14, 4.24), (0, 4.26)], iron, seg=24)
    # the triangle: a base bar, two raking sides, a gilt-traceried front plate
    zb, W, zt = 4.3, 1.35, 6.05
    tube("BaseBar", [(-W, 0, zb), (W, 0, zb)], 0.045, iron, square=True, poly=True)
    for sx in (-1, 1):
        tube(f"Side{sx}", [(sx * W, 0, zb), (0, 0, zt)], 0.045, iron, square=True, poly=True)
        tube(f"SideCurl{sx}", [(sx * W, 0, zb), (sx * (W + 0.15), 0, zb - 0.08), (sx * (W + 0.18), 0, zb - 0.22), (sx * (W + 0.05), 0, zb - 0.25)], 0.025, iron)
    tri = [(-W + 0.12, zb + 0.06), (W - 0.12, zb + 0.06), (0, zt - 0.2)]
    prism("Plate", tri, 0.0, 0.03, M["crimsonin"])
    tube("PlateRim", [(u, -0.03, z) for u, z in tri], 0.014, gl, closed=True, square=True, poly=True)
    for k, (x, z) in enumerate(((0, zb + 0.6), (-0.42, zb + 0.32), (0.42, zb + 0.32), (0, zb + 1.08))):
        foil(f"Foil{k}", x, -0.04, z, 0.11 if k == 0 else 0.08, gl, lobes=3 if k else 4, thick=0.012)
    tips = []
    for k in range(7):
        t = (k + 0.5) / 7
        for sx in (-1, 1):
            x, z = sx * W * (1 - t), zb + (zt - zb) * t
            cone(f"Pricket{sx}{k}", 0.012, 0.0, 0.08, (x, 0, z + 0.06), iron, verts=4)
            tips.append(cup_candle(f"K{sx}{k}", x, 0, z + 0.04, 0.42, wax, M["brass"], r=0.045, pan=0.08))
    tips.append(cup_candle("Apex", 0, 0, zt + 0.04, 0.5, wax, gl, r=0.05, pan=0.1))
    flames("Flame", tips, h=0.13)
    return _dims()


# ================================================================== DESK, PIANO AND READING LAMPS

def piano_lamp(M):
    """A piano lamp: a weighted brass foot, a swan-neck arm, a long curved trough shade lit along its underside."""
    gl, br = gilt(), M["brass"]
    lathe("Foot", [(0, 0.0), (0.4, 0.0), (0.42, 0.03), (0.38, 0.07), (0.3, 0.1), (0.2, 0.12), (0, 0.13)], br, seg=48, scale=(1.4, 1))
    hoop("FootBead", (0, 0, 0.05), 0.4, "Z", gl, thick=0.012)
    _xform(len(P.PARTS) - 1, Matrix.Scale(1.4, 4, (1, 0, 0)))
    lathe("Weight", [(0, 0.12), (0.12, 0.12), (0.14, 0.2), (0.1, 0.28), (0.05, 0.3), (0, 0.3)], black_marble(), seg=24)
    # the swan neck rising behind and arching forward over the music desk
    neck = [(0, 0.05, 0.28), (0, 0.08, 0.7), (0, 0.04, 1.1), (0, -0.12, 1.32), (0, -0.36, 1.36), (0, -0.52, 1.28)]
    sweep("Neck", neck, 0.03, br, seg=10, per=5)
    sphere("NeckKnob", 0.05, (0, 0.08, 0.7), gl, seg=10, rings=6)
    # the trough shade along X, open toward the front and down
    L, R = 0.85, 0.2
    ys, zs = -0.62, 1.2
    rows, rows_in = [], []
    for i in range(13):
        a = math.radians(-20 + 160 * i / 12)        # from the open lower front edge over the top to the back
        rows.append([(x, ys + math.cos(a + math.pi / 2) * R * -1, zs + math.sin(a + math.pi / 2) * R) for x in (-L, L)])
    _mesh("Shade", [[(r[0][0], r[0][1], r[0][2]), (r[1][0], r[1][1], r[1][2])] for r in rows], br, 0.02)
    _mesh("ShadeIn", [[(r[0][0] * 0.99, r[0][1] + 0.0, r[0][2] - 0.015), (r[1][0] * 0.99, r[1][1], r[1][2] - 0.015)] for r in rows], shade_lit((0.95, 0.85, 0.65)),
          0.004)
    for sx in (-1, 1):
        pts = [(sx * L, ys + math.cos(math.radians(-20 + 160 * i / 12) + math.pi / 2) * R * -1, zs + math.sin(math.radians(-20 + 160 * i / 12) + math.pi / 2) * R)
               for i in range(13)]
        prism(f"EndCap{sx}", [(y, z) for _, y, z in pts] + [(ys, zs)], sx * L, 0.03, br, plane="YZ")
        sphere(f"EndKnob{sx}", 0.035, (sx * (L + 0.03), ys, zs + 0.04), gl, seg=8, rings=5)
    tube("ShadeRim", [(-L, rows[0][0][1], rows[0][0][2]), (L, rows[0][0][1], rows[0][0][2])], 0.014, gl, poly=True)
    lathe("Hinge", [(0, -0.06), (0.05, -0.05), (0.05, 0.05), (0, 0.06)], br, seg=12)
    _xform(len(P.PARTS) - 1, Matrix.Translation((0, -0.52, 1.3)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    tube("BulbBar", [(-L + 0.1, ys, zs + 0.08), (L - 0.1, ys, zs + 0.08)], 0.015, br, poly=True)
    set_group("Glow")
    gb = bulb()
    for k, x in enumerate((-0.45, 0.0, 0.45)):
        sphere(f"Bulb{k}", 0.07, (x, ys + 0.02, zs + 0.03), gb, seg=12, rings=6, scale=(1.6, 1, 1))
    set_group("Main")
    return _dims()


def reading_lamp_swing(M):
    """A reading lamp on a jointed iron swing arm with a gilt counterweight and a pierced gothic cone shade."""
    gl, iron = gilt(), M["iron"]
    box("Base", (0.62, 0.5, 0.1), (0, 0.1, 0.05), iron, bevel=0.02)
    box("BaseTop", (0.52, 0.4, 0.05), (0, 0.1, 0.12), black_marble(), bevel=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"BaseBall{sx}{sy}", 0.03, (sx * 0.29, 0.1 + sy * 0.23, 0.1), gl, seg=8, rings=4)
    lathe("Post", [(0, 0.14), (0.06, 0.14), (0.045, 0.2), (0.035, 0.75), (0, 0.75)], iron, seg=16, loc=(0, 0.2, 0))
    j1 = Vector((0, 0.2, 0.8))
    sphere("Joint1", 0.06, tuple(j1), gl, seg=12, rings=6)
    j2 = Vector((0, -0.25, 1.75))
    tw = (j2 - j1).normalized()
    for sx in (-1, 1):
        tube(f"Lower{sx}", [tuple(j1 + Vector((sx * 0.035, 0, 0))), tuple(j2 + Vector((sx * 0.035, 0, 0)))], 0.016, iron, square=True, poly=True)
    tube("Spring", [tuple(j1.lerp(j2, 0.1 + 0.8 * i / 24) + Vector((math.cos(i * 1.6) * 0.012, 0.03 + math.sin(i * 1.6) * 0.012, 0))) for i in range(25)],
         0.006, M["brass"], poly=True)
    sphere("Joint2", 0.055, tuple(j2), gl, seg=12, rings=6)
    back = j2 + Vector((0, 0.42, 0.18))
    j3 = j2 + Vector((0, -0.72, -0.12))
    tube("Upper", [tuple(back), tuple(j3)], 0.018, iron, square=True, poly=True)
    sphere("Weight", 0.09, tuple(back + Vector((0, 0.04, 0.01))), gl, seg=14, rings=8)
    sphere("Joint3", 0.045, tuple(j3), gl, seg=10, rings=6)
    # the shade: a cone hanging nose-down from the last joint, gilt bands, pierced lancets round it
    s = _mark()
    lathe("Shade", [(0.05, 0.0), (0.09, -0.05), (0.18, -0.2), (0.27, -0.34), (0.29, -0.36)], iron, seg=32)
    lathe("ShadeIn", [(0.28, -0.355), (0.26, -0.335), (0.17, -0.2), (0.08, -0.05), (0.04, -0.005)], shade_lit(), seg=32)
    hoop("ShadeRim", (0, 0, -0.355), 0.29, "Z", gl, thick=0.013)
    for k in range(8):
        a = k / 8 * TAU
        g = _mark()
        pts = [(u, -0.012, z) for u, z in _gothic(0.035, -0.29, -0.17, -0.11, n=6)]
        tube(f"Lancet{k}", pts, 0.008, gl, closed=True, square=True, poly=True)
        _xform(g, Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, -0.192, -0.2)) @ Matrix.Rotation(-0.55, 4, "X") @ Matrix.Translation((0, 0, 0.2)))
    lathe("Cap", [(0, 0.08), (0.04, 0.07), (0.06, 0.0), (0, 0.0)], gl, seg=12)
    set_group("Glow")
    sphere("Bulb", 0.09, (0, 0, -0.22), bulb(), seg=12, rings=8, scale=(1, 1, 1.2))
    set_group("Main")
    _xform(s, Matrix.Translation(tuple(j3 + Vector((0, 0, -0.04)))) @ Matrix.Rotation(0.35, 4, "X"))
    return _dims()


def desk_lamp_chapel(M):
    """A desk lamp whose shade is a little chapel tower: four lit amber lancets in iron tracery, pinnacles and a spire."""
    gl, iron = gilt(), M["iron"]
    box("Plinth", (0.7, 0.7, 0.12), (0, 0, 0.06), iron, bevel=0.02)
    box("PlinthTop", (0.6, 0.6, 0.06), (0, 0, 0.15), M["crimsonin"], bevel=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Foot{sx}{sy}", 0.05, (sx * 0.3, sy * 0.3, 0.02), gl, seg=8, rings=4)
    lathe("Stem", [(0, 0.18), (0.12, 0.18), (0.08, 0.28), (0.05, 0.5), (0.09, 0.56), (0.05, 0.62), (0.05, 0.7), (0, 0.7)], gl, seg=20)
    # the tower: four faces with a lancet each
    hw, z0, z1 = 0.32, 0.72, 1.62
    box("Floor", (2 * hw + 0.06, 2 * hw + 0.06, 0.06), (0, 0, z0), iron, bevel=0.012)
    box("Cornice", (2 * hw + 0.1, 2 * hw + 0.1, 0.07), (0, 0, z1 + 0.035), iron, bevel=0.012)
    for k in range(4):
        g = _mark()
        lancet = _gothic(0.2, z0 + 0.06, z1 - 0.3, z1 - 0.06, n=10)
        tube(f"Arch{k}", [(u, -hw - 0.01, z) for u, z in lancet], 0.022, iron, closed=True, square=True, poly=True)
        tube(f"Mullion{k}", [(0, -hw - 0.01, z0 + 0.06), (0, -hw - 0.01, z1 - 0.32)], 0.012, iron, square=True, poly=True)
        for sx in (-1, 1):
            tube(f"Sub{k}{sx}", [(sx * 0.1 + u, -hw - 0.012, z) for u, z in _gothic(0.088, z1 - 0.5, z1 - 0.38, z1 - 0.3, n=6)][2:], 0.009, iron, square=True,
                 poly=True)
        foil(f"Foil{k}", 0, -hw - 0.015, z1 - 0.2, 0.06, iron, lobes=3, thick=0.009, centre=False)
        for sx in (-1, 1):
            prism(f"Spandrel{k}{sx}", [(sx * 0.2, z1 - 0.3), (sx * hw, z1 - 0.3), (sx * hw, z1), (sx * 0.0, z1)][::sx], -hw, 0.02, iron)
        _xform(g, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * hw, sy * hw
            box(f"Buttress{sx}{sy}", (0.08, 0.08, z1 - z0), (x, y, (z0 + z1) / 2), iron, bevel=0.01)
            lathe(f"Pinnacle{sx}{sy}", [(0.05, z1 + 0.07), (0.04, z1 + 0.15), (0, z1 + 0.38)], iron, seg=4, loc=(x, y, 0))
            sphere(f"PinTip{sx}{sy}", 0.022, (x, y, z1 + 0.39), gl, seg=8, rings=4)
    lathe("Spire", [(hw * 1.05, z1 + 0.07), (hw * 0.75, z1 + 0.22), (0.04, z1 + 0.74), (0, z1 + 0.76)], iron, seg=4)
    _xform(len(P.PARTS) - 1, Matrix.Rotation(math.pi / 4, 4, "Z"))
    for k in range(4):
        a = k / 4 * TAU + math.pi / 4
        for t in (0.3, 0.55, 0.8):
            r = hw * 1.05 * (1 - t) * 1.414 * 0.75
            sphere(f"Crocket{k}{t}", 0.022, (math.cos(a) * r, math.sin(a) * r, z1 + 0.1 + 0.62 * t), gl, seg=6, rings=4)
    lathe("Finial", [(0, z1 + 0.74), (0.025, z1 + 0.76), (0.02, z1 + 0.84), (0, z1 + 0.9)], gl, seg=8)
    set_group("Glow")
    ga = glow_amber()
    for k in range(4):
        g = _mark()
        prism(f"Pane{k}", _gothic(0.19, z0 + 0.06, z1 - 0.3, z1 - 0.07, n=10), -hw + 0.01, 0.02, ga)
        _xform(g, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    set_group("Main")
    return _dims()


def mantel_lamp_bat(M):
    """A mantel lamp: a bronze bat on a black marble plinth, wings raised to hold up a crimson-amber glass tulip."""
    gl, bz = gilt(), bronze()
    box("Plinth", (1.1, 0.55, 0.22), (0, 0, 0.11), black_marble(), bevel=0.03)
    box("PlinthCap", (0.95, 0.45, 0.08), (0, 0, 0.26), black_marble(), bevel=0.02)
    box("PlinthBand", (1.12, 0.57, 0.04), (0, 0, 0.17), gl, bevel=0.01)
    for sx in (-1, 1):
        sphere(f"Foot{sx}", 0.06, (sx * 0.48, -0.22, 0.02), gl, seg=8, rings=5, scale=(1, 1, 0.6))
        sphere(f"FootB{sx}", 0.06, (sx * 0.48, 0.22, 0.02), gl, seg=8, rings=5, scale=(1, 1, 0.6))
    foil("Crest", 0, -0.286, 0.11, 0.06, gl, thick=0.01)
    # the bat: a sculpted body and head, feet gripping a little rock
    rock = blob("Rock", [("ell", (0, 0, 0.34), 0.15, (1.4, 1.0, 0.55)), ("ball", (0.12, 0.05, 0.32), 0.08), ("ball", (-0.1, -0.04, 0.31), 0.07)], bz,
                res=0.02, target=900, pit=0.012, pit_scale=0.04)
    sh = bat_sculpt("Bat", Vector((0, 0.0, 0.4)), 0.92, bz, M["crimson"], gl, target=3600)
    # the wings raised in a V, the thumbs reaching in to hold the tulip's ring above the head
    zr = 1.56
    for sx, shp in zip((-1, 1), sh):
        wrist = (sx * 0.44, 0.03, 1.3)
        tips = [(sx * 0.76, 0.05, 1.64), (sx * 0.88, 0.06, 1.16), (sx * 0.68, 0.06, 0.74)]
        bat_wing("Bat", sx, tuple(shp), wrist, tips, (sx * 0.12, 0.02, 0.62), bz, s=1.0)
        sweep(f"Thumb{sx}", [wrist, (sx * 0.32, 0.0, zr - 0.02), (sx * 0.14, -0.02, zr - 0.03)], 0.018, bz, r1=0.008, seg=7, per=3)
    hoop("TulipRing", (0, -0.02, zr), 0.11, "Z", gl, thick=0.016)
    lathe("Gallery", [(0, zr - 0.04), (0.08, zr - 0.04), (0.11, zr + 0.02), (0, zr + 0.02)], bz, seg=16, loc=(0, -0.02, 0))
    set_group("Glow")
    lathe("Tulip", [(0.06, zr + 0.02), (0.11, zr + 0.08), (0.18, zr + 0.22), (0.22, zr + 0.38), (0.22, zr + 0.46), (0.19, zr + 0.5), (0, zr + 0.48)],
          flat("TulipGlass", (1.0, 0.45, 0.25), 0.3), seg=36, flute=(6, 0.1), loc=(0, -0.02, 0))
    set_group("Main")
    return _dims()


# ================================================================== registration

CEILING = {
    "ChandelierGreatWheel": chandelier_great_wheel,
    "ChandelierAntler": chandelier_antler,
    "ChandelierCage": chandelier_cage,
    "ChandelierCascade": chandelier_cascade,
    "ChandelierRavenWing": chandelier_raven_wing,
    "ChandelierShipHull": chandelier_ship_hull,
    "ChandelierThornCrown": chandelier_thorn_crown,
    "LanternCluster": lantern_cluster,
    "PendantSpire": pendant_spire,
    "PendantBellCage": pendant_bell_cage,
    "ClassroomPendant": classroom_pendant,
    "ClassroomTriPendant": classroom_tri_pendant,
    "MoonOrb": moon_orb,
    "TraceryCeilingRose": tracery_ceiling_rose,
    "VaultBossLight": vault_boss_light,
    "CorridorStripLight": corridor_strip_light,
}

WALL = {
    "SconceIronHand": sconce_iron_hand,
    "SconceBatWing": sconce_bat_wing,
    "SconceGasBracket": sconce_gas_bracket,
    "SconceMirror": sconce_mirror,
    "SconceGargoyle": sconce_gargoyle,
    "SconceWitchlight": sconce_witchlight,
    "CorridorUplighter": corridor_uplighter,
    "StainedLightbox": stained_lightbox,
}

STANDING = {
    "TorchereWolves": torchere_wolves,
    "CandelabraDeadTree": candelabra_dead_tree,
    "TorchereAlabaster": torchere_alabaster,
    "CandleHearse": candle_hearse,
    "PianoLamp": piano_lamp,
    "ReadingLampSwing": reading_lamp_swing,
    "DeskLampChapel": desk_lamp_chapel,
    "MantelLampBat": mantel_lamp_bat,
}

BUILDERS = {**CEILING, **WALL, **STANDING}

# glow colours (sRGB 0-255) for the template's Neon pieces
CANDLE, GAS, BULB, FIRE = (255, 170, 90), (255, 214, 160), (255, 222, 175), (255, 130, 55)
MOON, VIOLET = (185, 210, 255), (170, 110, 255)
GLOW_RGB = {
    "ChandelierGreatWheel": CANDLE, "ChandelierAntler": CANDLE, "ChandelierCage": CANDLE, "ChandelierCascade": MOON,
    "ChandelierRavenWing": CANDLE, "ChandelierShipHull": CANDLE, "ChandelierThornCrown": (255, 120, 105), "LanternCluster": CANDLE,
    "PendantSpire": VIOLET, "PendantBellCage": GAS, "ClassroomPendant": (255, 236, 205), "ClassroomTriPendant": BULB, "MoonOrb": MOON,
    "TraceryCeilingRose": (255, 228, 190), "VaultBossLight": (255, 165, 70), "CorridorStripLight": (255, 230, 195),
    "SconceIronHand": FIRE, "SconceBatWing": CANDLE, "SconceGasBracket": (255, 232, 200), "SconceMirror": CANDLE, "SconceGargoyle": FIRE,
    "SconceWitchlight": VIOLET, "CorridorUplighter": (255, 225, 185), "StainedLightbox": (255, 180, 110),
    "TorchereWolves": FIRE, "CandelabraDeadTree": CANDLE, "TorchereAlabaster": (255, 218, 170), "CandleHearse": CANDLE,
    "PianoLamp": BULB, "ReadingLampSwing": BULB, "DeskLampChapel": (255, 165, 70), "MantelLampBat": (255, 120, 75),
}
GLOW_LINEAR = {k: tuple((c / 255) ** 2.2 for c in v) for k, v in GLOW_RGB.items()}

# the Roblox light the template adds: (type, piece, colour, brightness, range, shadows, face / angle or None)
LIGHTS = {
    "ChandelierGreatWheel": ("PointLight", "Glow", (255, 190, 120), 3.0, 30, True, None),
    "ChandelierAntler": ("PointLight", "Glow", (255, 185, 115), 2.5, 26, True, None),
    "ChandelierCage": ("PointLight", "Glow", (255, 185, 115), 2.2, 22, True, None),
    "ChandelierCascade": ("PointLight", "Glow", (200, 220, 255), 2.5, 26, True, None),
    "ChandelierRavenWing": ("PointLight", "Glow", (255, 185, 115), 2.5, 26, True, None),
    "ChandelierShipHull": ("PointLight", "Glow", (255, 185, 115), 2.8, 28, True, None),
    "ChandelierThornCrown": ("PointLight", "Glow", (255, 150, 120), 2.2, 22, True, None),
    "LanternCluster": ("PointLight", "Glow", (255, 185, 115), 2.0, 20, False, None),
    "PendantSpire": ("PointLight", "Glow", (175, 120, 255), 1.8, 18, False, None),
    "PendantBellCage": ("PointLight", "Glow", (255, 205, 150), 2.0, 20, False, None),
    "ClassroomPendant": ("PointLight", "Glow", (255, 232, 200), 2.0, 20, False, None),
    "ClassroomTriPendant": ("SpotLight", "Glow", (255, 225, 185), 2.5, 24, False, ("Bottom", 120)),
    "MoonOrb": ("PointLight", "Glow", (185, 210, 255), 2.0, 22, False, None),
    "TraceryCeilingRose": ("SurfaceLight", "Glow", (255, 225, 185), 2.0, 22, False, ("Bottom", 160)),
    "VaultBossLight": ("PointLight", "Glow", (255, 180, 100), 2.2, 22, False, None),
    "CorridorStripLight": ("SurfaceLight", "Glow", (255, 228, 195), 1.8, 18, False, ("Bottom", 150)),
    "SconceIronHand": ("PointLight", "Glow", (255, 150, 75), 1.8, 18, False, None),
    "SconceBatWing": ("PointLight", "Glow", (255, 185, 115), 1.5, 16, False, None),
    "SconceGasBracket": ("PointLight", "Glow", (255, 225, 185), 1.6, 16, False, None),
    "SconceMirror": ("PointLight", "Glow", (255, 190, 125), 1.6, 16, False, None),
    "SconceGargoyle": ("PointLight", "Glow", (255, 150, 75), 2.0, 20, False, None),
    "SconceWitchlight": ("PointLight", "Glow", (175, 120, 255), 1.4, 14, False, None),
    "CorridorUplighter": ("SurfaceLight", "Glow", (255, 222, 180), 2.0, 18, False, ("Top", 150)),
    "StainedLightbox": ("SurfaceLight", "Stained", (255, 185, 140), 1.5, 14, False, ("Front", 120)),
    "TorchereWolves": ("PointLight", "Glow", (255, 150, 75), 2.5, 24, True, None),
    "CandelabraDeadTree": ("PointLight", "Glow", (255, 185, 115), 1.8, 18, False, None),
    "TorchereAlabaster": ("SpotLight", "Glow", (255, 215, 165), 2.5, 24, False, ("Top", 120)),
    "CandleHearse": ("PointLight", "Glow", (255, 185, 115), 2.0, 20, False, None),
    "PianoLamp": ("SpotLight", "Glow", (255, 222, 175), 1.5, 12, False, ("Bottom", 90)),
    "ReadingLampSwing": ("SpotLight", "Glow", (255, 222, 175), 1.5, 12, False, ("Bottom", 80)),
    "DeskLampChapel": ("PointLight", "Glow", (255, 175, 95), 1.2, 12, False, None),
    "MantelLampBat": ("PointLight", "Glow", (255, 140, 90), 1.2, 12, False, None),
}
# a second, fill light for the pieces that light a room from one side (a lamp's spot leaves the room dark round it)
FILL = {
    "ClassroomTriPendant": ("PointLight", "Glow", (255, 225, 185), 1.0, 16, False, None),
    "TorchereAlabaster": ("PointLight", "Glow", (255, 215, 165), 1.0, 14, False, None),
    "PianoLamp": ("PointLight", "Glow", (255, 222, 175), 0.6, 8, False, None),
    "ReadingLampSwing": ("PointLight", "Glow", (255, 222, 175), 0.6, 8, False, None),
    "StainedLightbox": ("PointLight", "Glow", (255, 180, 110), 0.8, 10, False, None),
}

FLIP_PREVIEW = {"TraceryCeilingRose", "VaultBossLight", "CorridorStripLight"}   # previewed upside down, so the lit underside shows
P.CANVAS["StainedLightbox_Stained"] = "StainedLightboxStained"
P.PREVIEW_PAD.update({"ChandelierGreatWheel": 1.05, "ChandelierShipHull": 1.0, "SconceIronHand": 1.2, "SconceGasBracket": 1.3, "SconceWitchlight": 1.25,
                      "SconceGargoyle": 1.25, "PianoLamp": 1.3, "ReadingLampSwing": 1.2, "DeskLampChapel": 1.25, "MantelLampBat": 1.3, "TraceryCeilingRose": 1.0,
                      "CorridorStripLight": 0.85, "CorridorUplighter": 0.9, "MoonOrb": 1.1})
def _grounded(fn, wall):
    """Run a builder, then lift everything so nothing is below the pivot (z = 0); a wall piece is checked for its back on y = 0."""
    def run(M):
        fn(M)
        bpy.context.view_layer.update()
        lo, hi_y = 1e9, -1e9
        for ob in P.PARTS:
            for c in ob.bound_box:
                w = ob.matrix_world @ Vector(c)
                lo, hi_y = min(lo, w.z), max(hi_y, w.y)
        if lo < -1e-4:
            for ob in P.PARTS:
                ob.matrix_world = Matrix.Translation((0, 0, -lo)) @ ob.matrix_world
            print(f"[b42] {fn.__name__}: lifted {-lo:.3f}", flush=True)
        if wall and hi_y > 0.002:
            print(f"[b42] {fn.__name__}: WARNING back at y = {hi_y:.3f}", flush=True)
        return _dims()
    return run


P.BUILD.update({k: _grounded(v, k in WALL) for k, v in BUILDERS.items()})
