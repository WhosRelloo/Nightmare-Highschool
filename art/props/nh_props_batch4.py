"""Props batch 4 (2026-11-03): twelve "building fill" props for nh_props.py, in the same gothic style.

  CeramicVase     a tall oxblood-glazed floor urn with black-glaze foot and neck, brass bands, scroll handles
                  and four brass medallions
  FlowerVase      a smoky glass vase in a brass foot with three crimson roses, two white lilies, baby's breath
                  and leaves (Glass: the vase)
  PottedPlant     a gadrooned limestone urn on a plinth, planted with a dark-leaved aspidistra
  LunchTray       a pewter compartment tray: mash with gravy, mystery meat, peas, a bread roll, a red jelly,
                  an apple, a milk carton and a fork on a crimson napkin
  LunchTrayEmpty  the same tray after lunch: crumbs, a gravy smear, an apple core, a crumpled napkin, a tipped
                  carton and the cutlery
  BookStack       six leather-bound books (raised bands, gilt, brass corners and clasp, ribbons) with an
                  inkwell and a quill on top
  OilLamp         a brass oil lamp with a crimson enamel font, a glass chimney and a flame (Glass, Glow)
  WallClock       a round oak wall clock with a brass bezel, a pointed crest and a glass front (Glass)
  PictureFrame    an ebonised and gilt frame round a painting of the school on its hill under a full moon
  CandleCluster   seven pillar candles of different heights on an iron tray, melted and dripping (Glow)
  UmbrellaStand   a fluted cast-iron stand with brass bands and quatrefoils, two furled umbrellas and a cane
  CoatRack        a turned oak hall stand on scrolled iron feet with eight hooks, a crimson scarf and a satchel

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, ring, set_group, _finish, _gable, _quatrefoil, material
from nh_props_batch3 import sphere, cone, flame


# ------------------------------------------------------------------ helpers

def lathe(name, prof, mat, seg=32, loc=(0, 0, 0), flute=None, jitter=None, scale=(1, 1)):
    """Solid of revolution from a (radius, z) profile, going up the outside and (for a vessel) back down
    the inside. A radius of 0 closes the end with a fan. flute=(count, depth) fluting, jitter=(amount, seed)
    random radial wobble, scale=(sx, sy) squashes it in plan."""
    rnd = random.Random(jitter[1]) if jitter else None
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r <= 1e-6:
            rings.append([bm.verts.new((loc[0], loc[1], loc[2] + z))])
            continue
        rg = []
        for i in range(seg):
            a = i / seg * 2 * math.pi
            rr = r
            if flute:
                rr *= 1 - flute[1] * (0.5 + 0.5 * math.cos(flute[0] * a))
            if rnd:
                rr *= 1 + rnd.uniform(-jitter[0], jitter[0])
            rg.append(bm.verts.new((loc[0] + math.cos(a) * rr * scale[0], loc[1] + math.sin(a) * rr * scale[1], loc[2] + z)))
        rings.append(rg)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(A) == 1:
                bm.faces.new((A[0], B[j], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[j], B[0]))
            else:
                bm.faces.new((A[i], A[j], B[j], B[i]))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def _solid(ob, thick):
    md = ob.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = thick
    md.offset = 0
    md.use_even_offset = True
    return ob


def _mesh(name, rows, mat, thick):
    """A sheet from rows of vertex positions (each row the same length), given a little thickness."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [[bm.verts.new(tuple(p)) for p in row] for row in rows]
    for a, b in zip(vs, vs[1:]):
        for k in range(len(a) - 1):
            bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    return _solid(ob, thick)


def leaf(name, root, yaw, pitch, length, width, droop, mat, n=10, fold=0.35, thick=0.014):
    """A lance-shaped leaf (or petal) rising from root at `pitch` toward `yaw`, arching down by `droop`,
    folded along its midrib."""
    d = Vector((math.cos(yaw), math.sin(yaw), 0))
    s = Vector((-math.sin(yaw), math.cos(yaw), 0))
    up = Vector((0, 0, 1))
    rows = []
    for i in range(n + 1):
        t = i / n
        c = Vector(root) + d * (length * t * math.cos(pitch)) + up * (length * t * math.sin(pitch) - droop * length * t * t)
        w = max(width * 1.9 * (t ** 0.55) * ((1 - t) ** 0.85), 0.004)
        e = up * fold * w
        rows.append((c - s * w + e, c, c + s * w + e))
    return _mesh(name, rows, mat, thick)


def _smooth(pts, it=3):
    for _ in range(it):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            new.append(tuple(a[k] * 0.75 + b[k] * 0.25 for k in range(3)))
            new.append(tuple(a[k] * 0.25 + b[k] * 0.75 for k in range(3)))
        new.append(pts[-1])
        pts = new
    return pts


def strip(name, pts, width, side, mat, thick=0.03, it=3):
    """A cloth band along a smoothed path, `width` wide along the `side` direction."""
    s = Vector(side).normalized() * width / 2
    rows = [(Vector(p) - s, Vector(p), Vector(p) + s) for p in _smooth(pts, it)]
    return _mesh(name, rows, mat, thick)


def prism(name, poly, pos, depth, mat, plane="XZ", bevel=0.0):
    """A flat polygon extruded `depth`: plane XZ (poly in x, z; thickness along Y at pos), YZ (y, z; along X)
    or XY (x, y; along Z, pos is the bottom)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    def v(u, w, side):
        if plane == "XZ":
            return (u, pos + side * depth / 2, w)
        if plane == "YZ":
            return (pos + side * depth / 2, u, w)
        return (u, w, pos + (side + 1) / 2 * depth)
    a = [bm.verts.new(v(u, w, -1)) for u, w in poly]
    b = [bm.verts.new(v(u, w, 1)) for u, w in poly]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, bevel)


def rrect(hw, hd, r, z, n=4):
    """Rounded-rectangle outline (half width, half depth, corner radius) at height z."""
    pts = []
    for cx, cy, a0 in ((hw - r, hd - r, 0), (-hw + r, hd - r, 90), (-hw + r, -hd + r, 180), (hw - r, -hd + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    return pts


def _mark():
    return len(P.PARTS)


def _xform(start, mtx):
    """Move every part built since _mark() by a matrix (to place a sub-assembly built at the origin)."""
    for ob in P.PARTS[start:]:
        ob.matrix_world = mtx @ ob.matrix_world


def _aim(direction):
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()


def _dims():
    """W, D, H of everything built, from the parts' bounds."""
    bpy.context.view_layer.update()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in P.PARTS:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for k in range(3):
                lo[k], hi[k] = min(lo[k], w[k]), max(hi[k], w[k])
    return (round(hi[0] - lo[0], 2), round(hi[1] - lo[1], 2), round(hi[2], 2))


def flat(name, rgb, rough, metal=0.0, wear=0.0, dirt=0.5):
    """A plain colour material; no edge wear by default (thin organic parts are all edge)."""
    return material(name, base=rgb, rough=rough, metal=metal, wear=wear, dirt=dirt)


# ================================================================== ceramic vase
def ceramic_vase(M):
    ox = flat("GlazeOxblood", (0.1, 0.006, 0.012), 0.13, wear=0.04, dirt=0.55)
    blk = flat("GlazeBlack", (0.018, 0.016, 0.02), 0.14, wear=0.04, dirt=0.4)
    lathe("Foot", [(0, 0), (0.44, 0), (0.46, 0.04), (0.44, 0.1), (0.36, 0.18), (0.31, 0.27), (0.33, 0.32), (0, 0.32)], blk, seg=40)
    lathe("Body", [(0, 0.29), (0.34, 0.3), (0.5, 0.5), (0.68, 0.85), (0.78, 1.25), (0.78, 1.45), (0.72, 1.75), (0.6, 2.02),
                   (0.44, 2.28), (0.31, 2.48), (0, 2.5)], ox, seg=40)
    lathe("Neck", [(0, 2.44), (0.3, 2.44), (0.27, 2.62), (0.27, 2.78), (0.33, 2.94), (0.42, 3.07), (0.47, 3.14), (0.46, 3.19),
                   (0.41, 3.19), (0.36, 3.1), (0.25, 2.92), (0.22, 2.7), (0, 2.6)], blk, seg=40)
    ring("FootBand", (0, 0, 0.3), 0.335, "Z", M["brass"], thick=0.025)
    ring("NeckBand", (0, 0, 2.47), 0.315, "Z", M["brass"], thick=0.025)
    ring("Shoulder", (0, 0, 1.92), 0.655, "Z", M["brass"], thick=0.02)
    ring("Belly", (0, 0, 1.0), 0.72, "Z", M["brass"], thick=0.018)
    ring("LipBand", (0, 0, 3.12), 0.455, "Z", M["brass"], thick=0.02)
    for sx in (-1, 1):
        tube(f"Handle{sx}", [(sx * 0.62, 0, 1.98), (sx * 0.86, 0, 2.12), (sx * 0.9, 0, 2.42), (sx * 0.62, 0, 2.7), (sx * 0.32, 0, 2.72)],
             0.045, M["brass"])
        tube(f"HandleCurl{sx}", [(sx * 0.86, 0, 2.12), (sx * 0.98, 0, 2.06), (sx * 1.0, 0, 2.18), (sx * 0.93, 0, 2.22)], 0.025, M["brass"])
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        x, y = math.cos(a) * 0.79, math.sin(a) * 0.79
        bpy.ops.mesh.primitive_torus_add(major_segments=20, minor_segments=6, major_radius=0.16, minor_radius=0.025,
                                         location=(x, y, 1.35), rotation=(math.pi / 2, 0, a + math.pi / 2))
        t = bpy.context.active_object
        t.name = f"Medallion{k}"
        _finish(t, M["brass"], 0)
        sphere(f"Boss{k}", 0.06, (math.cos(a) * 0.79, math.sin(a) * 0.79, 1.35), M["brass"], seg=10, rings=5)
    return _dims()


# ================================================================== flower vase
def rose(prefix, pos, direction, r, petal, sepal):
    s = _mark()
    sphere(f"{prefix}Bud", r * 0.32, (0, 0, r * 0.25), petal, seg=10, rings=6, scale=(1, 1, 1.35))
    for k, cnt in enumerate((4, 5, 6)):
        pr = r * (0.4 + 0.2 * k)
        for i in range(cnt):
            a = i / cnt * 2 * math.pi + k * 0.6
            d = r * (0.12 + 0.18 * k)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=1,
                                                 location=(math.cos(a) * d, math.sin(a) * d, r * (0.22 - 0.06 * k)),
                                                 rotation=(-math.radians(12 + 22 * k), 0, a - math.pi / 2))
            o = bpy.context.active_object
            o.name = f"{prefix}Petal{k}{i}"
            o.scale = (pr * 0.62, pr * 0.16, pr * 0.72)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            _finish(o, petal, 0)
    for i in range(5):
        a = i / 5 * 2 * math.pi
        leaf(f"{prefix}Sepal{i}", (0, 0, -r * 0.1), a, math.radians(-35), r * 0.7, r * 0.12, 0.0, sepal, n=5, thick=0.008)
    _xform(s, Matrix.Translation(pos) @ _aim(direction))


def lily(prefix, pos, direction, r, petal, pollen, stalk):
    s = _mark()
    for i in range(6):
        a = i / 6 * 2 * math.pi + (0.5 if i % 2 else 0)
        leaf(f"{prefix}Petal{i}", (0, 0, 0), a, math.radians(62), r, r * 0.2, 1.1, petal, n=10, fold=0.25, thick=0.01)
    for i in range(6):
        a = i / 6 * 2 * math.pi + 0.25
        tip = (math.cos(a) * r * 0.35, math.sin(a) * r * 0.35, r * 0.62)
        tube(f"{prefix}Stamen{i}", [(0, 0, 0.0), (tip[0] * 0.5, tip[1] * 0.5, tip[2] * 0.6), tip], 0.007, stalk)
        sphere(f"{prefix}Anther{i}", 0.022, tip, pollen, seg=6, rings=3, scale=(1, 1, 1.8))
    cone(f"{prefix}Base", 0.025, 0.06, 0.12, (0, 0, -0.05), stalk, verts=10)
    _xform(s, Matrix.Translation(pos) @ _aim(direction))


def flower_vase(M):
    rose_m = flat("RosePetal", (0.11, 0.004, 0.012), 0.55, dirt=0.9)
    lily_m = flat("LilyPetal", (0.8, 0.78, 0.7), 0.5, dirt=0.7)
    stem_m = flat("Stem", (0.03, 0.07, 0.025), 0.55)
    leaf_m = flat("LeafDark", (0.014, 0.04, 0.016), 0.45)
    pollen = flat("Pollen", (0.45, 0.16, 0.03), 0.8, wear=0.0)
    breath = flat("Breath", (0.92, 0.9, 0.86), 0.8, wear=0.0)
    set_group("Main")
    lathe("Foot", [(0, 0), (0.36, 0), (0.38, 0.03), (0.35, 0.08), (0.3, 0.11), (0.29, 0.14), (0, 0.14)], M["brass"], seg=36)
    ring("FootBead", (0, 0, 0.11), 0.31, "Z", M["brass"], thick=0.02)
    ring("Collar", (0, 0, 1.08), 0.205, "Z", M["brass"], thick=0.022)
    # stems run from the bottom of the vase, out through the neck, to each head
    heads = [("rose", (0.0, -0.04, 2.15), (0, -0.25, 1)), ("rose", (0.32, -0.16, 1.88), (0.6, -0.5, 1)),
             ("rose", (-0.3, 0.12, 1.95), (-0.6, 0.2, 1)), ("lily", (-0.36, -0.24, 1.72), (-0.7, -0.6, 1)),
             ("lily", (0.26, 0.3, 2.05), (0.45, 0.6, 1))]
    for k, (kind, pos, d) in enumerate(heads):
        base = (pos[0] * 0.15, pos[1] * 0.15, 0.25)
        neck = (pos[0] * 0.25, pos[1] * 0.25, 1.2)
        tube(f"Stem{k}", [base, neck, (pos[0] * 0.8, pos[1] * 0.8, pos[2] - 0.35), (pos[0], pos[1], pos[2] - 0.05)], 0.018, stem_m)
        if kind == "rose":
            rose(f"Rose{k}", pos, d, 0.17, rose_m, leaf_m)
        else:
            lily(f"Lily{k}", pos, d, 0.34, lily_m, pollen, stem_m)
    rnd = random.Random(11)
    for k in range(7):
        a = k / 7 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        leaf(f"Leaf{k}", (math.cos(a) * 0.06, math.sin(a) * 0.06, rnd.uniform(1.2, 1.45)), a, math.radians(rnd.uniform(25, 45)),
             rnd.uniform(0.42, 0.58), 0.12, 0.6, leaf_m)
    # baby's breath sprays
    for k in range(3):
        a = k / 3 * 2 * math.pi + 1.0
        tip = (math.cos(a) * 0.42, math.sin(a) * 0.42, 1.75 + k * 0.12)
        tube(f"Spray{k}", [(0, 0, 0.4), (math.cos(a) * 0.08, math.sin(a) * 0.08, 1.2), tip], 0.008, stem_m)
        for j in range(9):
            p = (tip[0] + rnd.uniform(-0.12, 0.12), tip[1] + rnd.uniform(-0.12, 0.12), tip[2] + rnd.uniform(-0.08, 0.1))
            tube(f"Twig{k}{j}", [tip, p], 0.004, stem_m, poly=True)
            sphere(f"Floret{k}{j}", 0.025, p, breath, seg=6, rings=4)
    set_group("Glass")
    lathe("Vase", [(0, 0.14), (0.27, 0.14), (0.3, 0.2), (0.33, 0.42), (0.31, 0.65), (0.23, 0.88), (0.2, 1.0), (0.24, 1.12),
                   (0.28, 1.17), (0.27, 1.19), (0.25, 1.17), (0.21, 1.11), (0.17, 1.0), (0.2, 0.88), (0.28, 0.65), (0.3, 0.42),
                   (0.27, 0.22), (0, 0.18)], M["glassclear"], seg=36)
    set_group("Main")
    return _dims()


# ================================================================== potted plant
def potted_plant(M):
    soil = material("Soil", "NH_Limestone", tint=(0.12, 0.08, 0.055), scale=1.2, rough_add=0.35, wear=0.0, dirt=0.9)
    greens = [flat("Aspidistra", (0.016, 0.05, 0.02), 0.4, dirt=0.7),
              flat("AspidistraOld", (0.028, 0.06, 0.018), 0.48, dirt=0.8)]
    box("Plinth", (1.55, 1.55, 0.3), (0, 0, 0.15), M["stonedark"], bevel=0.04)
    box("PlinthCap", (1.35, 1.35, 0.08), (0, 0, 0.34), M["stone"], bevel=0.025)
    lathe("UrnFoot", [(0, 0.38), (0.5, 0.38), (0.52, 0.44), (0.44, 0.52), (0.32, 0.58), (0.3, 0.7), (0.36, 0.74), (0, 0.74)], M["stone"], seg=40)
    lathe("Bowl", [(0, 0.7), (0.36, 0.7), (0.52, 0.82), (0.68, 0.98), (0.79, 1.2), (0.84, 1.42), (0, 1.42)], M["stone"], seg=64, flute=(16, 0.07))
    lathe("Rim", [(0, 1.36), (0.85, 1.36), (0.9, 1.44), (0.95, 1.52), (0.96, 1.62), (0.9, 1.66), (0.84, 1.64), (0.8, 1.56),
                  (0.76, 1.45), (0, 1.45)], M["stone"], seg=48)
    ring("RimBead", (0, 0, 1.44), 0.91, "Z", M["stonedark"], thick=0.025)
    cyl("Soil", 0.79, 0.06, (0, 0, 1.55), soil, verts=40, bevel=0.01)
    rnd = random.Random(23)
    for k in range(7):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.25, 0.65)
        sphere(f"Pebble{k}", rnd.uniform(0.04, 0.07), (math.cos(a) * d, math.sin(a) * d, 1.58), M["stonedark"], seg=8, rings=4, scale=(1, 0.8, 0.6))
    golden = math.pi * (3 - math.sqrt(5))
    n = 24
    for k in range(n):
        t = k / (n - 1)
        a = k * golden
        pitch = math.radians(78 - 42 * t + rnd.uniform(-5, 5))
        leaf(f"Leaf{k}", (math.cos(a) * 0.08 * t, math.sin(a) * 0.08 * t, 1.56), a, pitch, rnd.uniform(1.7, 2.5) * (1 - 0.15 * t),
             rnd.uniform(0.24, 0.32), rnd.uniform(0.25, 0.45) + 0.3 * t, greens[k % 2], n=14, fold=0.32, thick=0.012)
    return _dims()


# ================================================================== lunch trays
def _tray(M):
    pewter = flat("Pewter", (0.62, 0.62, 0.64), 0.36, metal=1.0, wear=0.3, dirt=0.85)
    prism("Tray", [(x, y) for x, y, _ in rrect(0.95, 0.675, 0.14, 0)], 0.0, 0.035, pewter, plane="XY", bevel=0.01)
    tube("Rim", rrect(0.92, 0.645, 0.12, 0.06), 0.035, pewter, closed=True, square=True, poly=True)
    for name, pts in (("DivA", [(-0.89, 0.1, 0.05), (0.89, 0.1, 0.05)]), ("DivB", [(-0.3, 0.1, 0.05), (-0.3, 0.62, 0.05)]),
                      ("DivC", [(0.3, 0.1, 0.05), (0.3, 0.62, 0.05)]), ("DivD", [(0.25, 0.1, 0.05), (0.25, -0.62, 0.05)])):
        tube(name, pts, 0.022, pewter, square=True, poly=True)
    return pewter


def _fork(prefix, mtx, steel):
    s = _mark()
    box(f"{prefix}Handle", (0.42, 0.05, 0.016), (0.21, 0, 0.008), steel, bevel=0.006)
    box(f"{prefix}Neck", (0.08, 0.035, 0.014), (0.46, 0, 0.012), steel, bevel=0.005)
    box(f"{prefix}Head", (0.06, 0.08, 0.012), (0.52, 0, 0.012), steel, bevel=0.004)
    for k in range(4):
        box(f"{prefix}Tine{k}", (0.12, 0.012, 0.01), (0.6, -0.03 + k * 0.02, 0.014), steel, bevel=0.003, segments=1)
    _xform(s, mtx)


def _spoon(prefix, mtx, steel):
    s = _mark()
    box(f"{prefix}Handle", (0.42, 0.045, 0.016), (0.21, 0, 0.008), steel, bevel=0.006)
    sphere(f"{prefix}Bowl", 1, (0.52, 0, 0.022), steel, seg=14, rings=7, scale=(0.11, 0.07, 0.022))
    _xform(s, mtx)


def _carton(prefix, mtx, M, print_m):
    s = _mark()
    box(f"{prefix}Body", (0.26, 0.26, 0.36), (0, 0, 0.18), M["paper"], bevel=0.008)
    box(f"{prefix}Band", (0.266, 0.266, 0.12), (0, 0, 0.2), print_m, bevel=0.004)
    prism(f"{prefix}Gable", [(-0.13, 0.36), (0.13, 0.36), (0, 0.46)], 0.0, 0.26, M["paper"], plane="YZ")
    box(f"{prefix}Fin", (0.26, 0.022, 0.05), (0, 0, 0.48), M["paper"], bevel=0.004)
    _xform(s, mtx)


def lunch_tray(M):
    steel = M["brasssteel"]
    _tray(M)
    T = 0.035
    potato = flat("Mash", (0.86, 0.79, 0.6), 0.75, wear=0.05, dirt=0.6)
    gravy = flat("Gravy", (0.16, 0.07, 0.03), 0.18, wear=0.0, dirt=0.4)
    meat = flat("MysteryMeat", (0.32, 0.14, 0.09), 0.5, wear=0.1, dirt=0.8)
    peas = flat("Peas", (0.16, 0.34, 0.06), 0.35, wear=0.0, dirt=0.5)
    crust = flat("Crust", (0.5, 0.26, 0.09), 0.6, wear=0.25, dirt=0.6)
    jelly = flat("Jelly", (0.3, 0.012, 0.02), 0.06, dirt=0.25)
    apple = flat("Apple", (0.38, 0.025, 0.03), 0.28, wear=0.15, dirt=0.5)
    butter = flat("Butter", (0.9, 0.72, 0.28), 0.4, wear=0.0)
    napkin = material("Napkin", "NH_Leather", tint=(0.3, 0.03, 0.045), scale=3.0, normal=0.3, rough_add=0.3, wear=0.1)
    # mash with a well of gravy and a pat of butter
    lathe("Mash", [(0, T), (0.25, T), (0.25, T + 0.04), (0.21, T + 0.1), (0.15, T + 0.16), (0.08, T + 0.2), (0, T + 0.205)],
          potato, seg=24, loc=(-0.6, -0.22, 0), jitter=(0.1, 4))
    lathe("GravyPool", [(0, T + 0.17), (0.13, T + 0.17), (0.12, T + 0.19), (0, T + 0.2)], gravy, seg=20, loc=(-0.6, -0.22, 0.02), jitter=(0.15, 9))
    box("Butter", (0.08, 0.08, 0.035), (-0.57, -0.2, T + 0.235), butter, bevel=0.01, rot=(0.15, 0.1, 0.5))
    # mystery meat in gravy
    box("Meat", (0.42, 0.3, 0.08), (-0.08, -0.24, T + 0.04), meat, bevel=0.03, rot=(0, 0, math.radians(14)))
    lathe("GravyMeat", [(0, T + 0.002), (0.27, T + 0.002), (0.25, T + 0.012), (0, T + 0.016)], gravy, seg=24, loc=(-0.1, -0.23, 0),
          jitter=(0.12, 2), scale=(1.1, 0.75))
    for k, (x, y) in enumerate(((-0.14, -0.25), (0.0, -0.2), (-0.2, -0.18))):
        sphere(f"Drizzle{k}", 0.06, (x, y, T + 0.078), gravy, seg=12, rings=6, scale=(2.2, 0.8, 0.18))
    # peas
    rnd = random.Random(8)
    for k in range(30):
        layer = 0 if k < 20 else 1
        sphere(f"Pea{k}", 0.038, (rnd.uniform(-0.84, -0.36), rnd.uniform(0.16, 0.56), T + 0.038 + layer * 0.06), peas, seg=8, rings=5)
    # bread roll with a scored top
    sphere("Roll", 1, (0, 0.36, T + 0.13), crust, seg=20, rings=10, scale=(0.23, 0.19, 0.14))
    tube("Score", [(-0.12, 0.33, T + 0.255), (0.0, 0.36, T + 0.272), (0.12, 0.39, T + 0.255)], 0.014, potato)
    # a red jelly with cream and a cherry
    box("Jelly", (0.3, 0.3, 0.22), (0.59, 0.36, T + 0.11), jelly, bevel=0.05, segments=3)
    lathe("Cream", [(0, T + 0.21), (0.09, T + 0.21), (0.07, T + 0.26), (0.04, T + 0.3), (0, T + 0.33)], M["chalk"], seg=12,
          loc=(0.59, 0.36, 0), flute=(6, 0.3))
    sphere("Cherry", 0.04, (0.6, 0.36, T + 0.36), apple, seg=10, rings=5)
    # apple and milk carton
    lathe("Apple", [(0, T + 0.01), (0.06, T), (0.13, T + 0.04), (0.16, T + 0.1), (0.16, T + 0.17), (0.12, T + 0.24), (0.06, T + 0.26),
                    (0.02, T + 0.23), (0, T + 0.22)], apple, seg=24, loc=(0.43, -0.4, 0))
    tube("AppleStem", [(0.43, -0.4, T + 0.22), (0.44, -0.4, T + 0.3)], 0.01, M["oakdark"], poly=True)
    leaf("AppleLeaf", (0.44, -0.4, T + 0.28), 0.4, math.radians(20), 0.12, 0.05, 0.2, peas, n=5, thick=0.006)
    _carton("Carton", Matrix.Translation((0.73, -0.12, T)) @ Matrix.Rotation(0.2, 4, "Z"), M, M["crimson"])
    # fork on a folded napkin
    box("Napkin", (0.62, 0.16, 0.012), (-0.45, -0.52, T + 0.006), napkin, bevel=0.004, rot=(0, 0, math.radians(-3)))
    _fork("Fork", Matrix.Translation((-0.78, -0.52, T + 0.012)) @ Matrix.Rotation(math.radians(-3), 4, "Z"), steel)
    return _dims()


def lunch_tray_empty(M):
    steel = M["brasssteel"]
    _tray(M)
    T = 0.035
    gravy = flat("Gravy", (0.16, 0.07, 0.03), 0.18, wear=0.0, dirt=0.4)
    crust = flat("Crust", (0.5, 0.26, 0.09), 0.6, wear=0.25, dirt=0.6)
    peas = flat("Peas", (0.16, 0.34, 0.06), 0.35, wear=0.0, dirt=0.5)
    flesh = flat("AppleFlesh", (0.82, 0.74, 0.5), 0.55, wear=0.0, dirt=0.6)
    apple = flat("Apple", (0.38, 0.025, 0.03), 0.28, wear=0.15, dirt=0.5)
    jelly = flat("Jelly", (0.3, 0.012, 0.02), 0.06, dirt=0.25)
    # smears
    lathe("Smear", [(0, T + 0.001), (0.3, T + 0.001), (0.27, T + 0.008), (0, T + 0.011)], gravy, seg=24, loc=(-0.42, -0.26, 0),
          jitter=(0.22, 5), scale=(1.3, 0.7))
    lathe("JellySmear", [(0, T + 0.001), (0.12, T + 0.001), (0.1, T + 0.012), (0, T + 0.016)], jelly, seg=16, loc=(0.6, 0.38, 0),
          jitter=(0.25, 6))
    rnd = random.Random(12)
    for k in range(16):
        x, y = (rnd.uniform(-0.25, 0.25), rnd.uniform(0.17, 0.55)) if k < 10 else (rnd.uniform(-0.8, 0.2), rnd.uniform(-0.55, 0.05))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.014, 0.03), location=(x, y, T + 0.012))
        c = bpy.context.active_object
        c.name = f"Crumb{k}"
        for f in c.data.polygons:
            f.use_smooth = False
        _finish(c, crust, 0)
    for k, (x, y) in enumerate(((-0.36, 0.5), (-0.84, 0.16), (-0.2, -0.5))):
        sphere(f"Pea{k}", 0.038, (x, y, T + 0.038), peas, seg=8, rings=5)
    # apple core lying on its side
    s = _mark()
    lathe("Core", [(0, 0), (0.1, 0.01), (0.11, 0.04), (0.05, 0.09), (0.04, 0.15), (0.09, 0.21), (0.1, 0.24), (0, 0.26)], flesh, seg=16,
          jitter=(0.08, 3))
    lathe("CoreSkinB", [(0, -0.005), (0.085, 0.005), (0.09, 0.025), (0, 0.025)], apple, seg=16)
    lathe("CoreSkinT", [(0, 0.232), (0.085, 0.232), (0.08, 0.252), (0, 0.265)], apple, seg=16)
    tube("CoreStem", [(0, 0, 0.26), (0.01, 0, 0.32)], 0.01, M["oakdark"], poly=True)
    _xform(s, Matrix.Translation((0.5, -0.49, T + 0.1)) @ Matrix.Rotation(0.2, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y") @ Matrix.Translation((0, 0, -0.13)))
    # crumpled napkin
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.17, location=(-0.6, 0.36, T + 0.12))
    nap = bpy.context.active_object
    nap.name = "Napkin"
    for v in nap.data.vertices:
        v.co *= 1 + rnd.uniform(-0.28, 0.12)
        v.co.z *= 0.7
    for f in nap.data.polygons:
        f.use_smooth = False
    _finish(nap, M["paper"], 0)
    # the carton tipped over, the cutlery left askew
    _carton("Carton", Matrix.Translation((0.62, -0.2, T + 0.13)) @ Matrix.Rotation(0.12, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y") @
            Matrix.Translation((0, 0, -0.25)), M, M["crimson"])
    _fork("Fork", Matrix.Translation((-0.78, -0.48, T)) @ Matrix.Rotation(math.radians(18), 4, "Z"), steel)
    _spoon("Spoon", Matrix.Translation((-0.55, 0.05, T)) @ Matrix.Rotation(math.radians(-25), 4, "Z") @ Matrix.Rotation(math.radians(-4), 4, "X"), steel)
    return _dims()


# ================================================================== book stack
def _book(prefix, w, d, t, cover, M, corners=False, clasp=False, ribbon=None):
    bt = 0.03
    box(f"{prefix}CoverB", (w, d, bt), (0, 0, bt / 2), cover, bevel=0.01)
    box(f"{prefix}CoverT", (w, d, bt), (0, 0, t - bt / 2), cover, bevel=0.01)
    box(f"{prefix}Pages", (w - 0.07, d - 0.05, t - 2 * bt + 0.006), (0, -0.005, t / 2), M["paper"], bevel=0.006)
    box(f"{prefix}Spine", (w, 0.07, t), (0, -d / 2 + 0.025, t / 2), cover, bevel=min(0.03, t * 0.3))
    for k in range(4):
        x = -w * 0.3 + k * w * 0.2
        box(f"{prefix}Band{k}", (0.035, 0.08, t + 0.008), (x, -d / 2 + 0.022, t / 2), cover, bevel=0.012)
    for sx in (-1, 1):
        box(f"{prefix}Gilt{sx}", (0.018, 0.074, t * 0.86), (sx * w * 0.42, -d / 2 + 0.022, t / 2), M["brass"], bevel=0.004)
    box(f"{prefix}Label", (w * 0.16, 0.074, t * 0.5), (w * 0.0 - w * 0.1, -d / 2 + 0.024, t / 2), M["brass"], bevel=0.004)
    if corners:
        for sx in (-1, 1):
            for z in (bt / 2, t - bt / 2):
                box(f"{prefix}Corner{sx}{z:.2f}", (0.11, 0.11, bt + 0.012), (sx * (w / 2 - 0.045), d / 2 - 0.045, z), M["brass"], bevel=0.008)
    if clasp:
        box(f"{prefix}ClaspT", (0.09, 0.16, 0.012), (0, d / 2 - 0.06, t + 0.005), M["brass"], bevel=0.004)
        box(f"{prefix}ClaspE", (0.09, 0.012, t + 0.01), (0, d / 2 + 0.006, t / 2), M["brass"], bevel=0.004)
        sphere(f"{prefix}ClaspStud", 0.025, (0, d / 2 - 0.12, t + 0.012), M["brass"], seg=8, rings=4)
    if ribbon is not None:
        box(f"{prefix}Ribbon", (0.045, 0.006, t * 0.85), (w * 0.22, d / 2 - 0.02, t * 0.48), ribbon, bevel=0.0, segments=1,
            rot=(math.radians(8), 0, 0))


def book_stack(M):
    # thin boards are "all edge" to the wear pass, so the bindings get their own low-wear leathers
    def hide(name, tint, normal=0.5):
        return material(name, "NH_Leather", tint=tint, scale=1.8, normal=normal, wear=0.1, dirt=0.75)
    oxblood, ink, red = hide("BindOxblood", (0.12, 0.018, 0.026)), hide("BindInk", (0.07, 0.09, 0.22)), hide("BindCrimson", (0.2, 0.026, 0.04))
    green, vellum, black = hide("BindGreen", (0.035, 0.08, 0.045)), hide("BindVellum", (0.55, 0.5, 0.42), 0.35), hide("BindBlack", (0.03, 0.028, 0.034))
    books = [(1.3, 0.98, 0.22, oxblood, 0, True, False), (1.18, 0.88, 0.17, ink, 7, False, False),
             (1.22, 0.92, 0.24, green, -5, True, True), (1.04, 0.78, 0.15, red, 12, False, False),
             (0.98, 0.74, 0.19, vellum, -9, True, False), (0.86, 0.64, 0.13, black, 22, False, True)]
    z = 0.0
    top = None
    for k, (w, d, t, cov, yaw, corners, clasp) in enumerate(books):
        s = _mark()
        _book(f"Book{k}", w, d, t, cov, M, corners=corners, clasp=clasp, ribbon=M["crimson"] if k in (1, 4) else None)
        _xform(s, Matrix.Translation((0.03 * math.sin(k * 2.1), 0.03 * math.cos(k * 1.7), z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z"))
        z += t + 0.004
        top = z
    # inkwell and quill on top
    lathe("Inkwell", [(0, top), (0.12, top), (0.13, top + 0.02), (0.13, top + 0.12), (0.09, top + 0.16), (0.05, top + 0.17), (0.05, top + 0.2),
                      (0.04, top + 0.2), (0.035, top + 0.17), (0, top + 0.17)], M["glass"], seg=20, loc=(-0.12, 0.05, 0))
    ring("InkCollar", (-0.12, 0.05, top + 0.18), 0.052, "Z", M["brass"], thick=0.012)
    quill = flat("Quill", (0.88, 0.86, 0.8), 0.7, wear=0.1)
    tube("QuillShaft", [(-0.12, 0.05, top + 0.08), (-0.02, 0.1, top + 0.4), (0.12, 0.18, top + 0.78)], 0.009, quill)
    s = _mark()
    leaf("QuillVane", (0, 0, 0), 0, math.radians(90), 0.55, 0.06, 0.0, quill, n=12, fold=0.15, thick=0.006)
    _xform(s, Matrix.Translation((-0.06, 0.08, top + 0.26)) @ _aim((0.24, 0.13, 0.75)))
    return _dims()


# ================================================================== oil lamp
def oil_lamp(M):
    set_group("Main")
    lathe("Base", [(0, 0), (0.34, 0), (0.35, 0.03), (0.32, 0.07), (0.2, 0.12), (0.12, 0.18), (0.09, 0.28), (0.09, 0.34), (0.13, 0.38),
                   (0.14, 0.42), (0, 0.42)], M["brass"], seg=32)
    ring("BaseBead", (0, 0, 0.065), 0.325, "Z", M["brass"], thick=0.016)
    sphere("Knop", 0.13, (0, 0, 0.27), M["brass"], seg=16, rings=8, scale=(1, 1, 0.6))
    lathe("Font", [(0, 0.4), (0.13, 0.4), (0.24, 0.47), (0.31, 0.58), (0.32, 0.65), (0.28, 0.75), (0.19, 0.82), (0.12, 0.85), (0, 0.85)],
          M["crimson"], seg=32)
    ring("FontBand", (0, 0, 0.63), 0.322, "Z", M["brass"], thick=0.022)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        sphere(f"Stud{k}", 0.025, (math.cos(a) * 0.31, math.sin(a) * 0.31, 0.63), M["brass"], seg=8, rings=4)
    lathe("Burner", [(0, 0.83), (0.13, 0.83), (0.15, 0.88), (0.14, 0.95), (0.12, 0.97), (0.12, 1.0), (0, 1.0)], M["brass"], seg=24)
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        tube(f"Prong{k}", [(math.cos(a) * 0.12, math.sin(a) * 0.12, 0.96), (math.cos(a) * 0.15, math.sin(a) * 0.15, 1.08)], 0.012, M["brass"], poly=True)
    cyl("WickKnobStem", 0.015, 0.12, (0.18, 0, 0.9), M["brass"], rot=(0, math.pi / 2, 0), verts=8, bevel=0)
    cyl("WickKnob", 0.05, 0.03, (0.25, 0, 0.9), M["brass"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.005)
    box("Wick", (0.06, 0.012, 0.04), (0, 0, 1.02), M["iron"], bevel=0.004)
    # a finger loop on the base
    ring("Loop", (-0.42, 0, 0.22), 0.1, "Y", M["brass"], thick=0.022)
    tube("LoopArm", [(-0.3, 0, 0.08), (-0.38, 0, 0.12)], 0.02, M["brass"], poly=True)
    tube("LoopArm2", [(-0.12, 0, 0.3), (-0.33, 0, 0.27)], 0.018, M["brass"], poly=True)
    set_group("Glow")
    flame("Flame", (0, 0, 1.03), h=0.2)
    set_group("Glass")
    lathe("Chimney", [(0.125, 0.98), (0.14, 1.04), (0.2, 1.14), (0.215, 1.24), (0.16, 1.35), (0.11, 1.45), (0.1, 1.7), (0.115, 1.74),
                      (0.1, 1.74), (0.085, 1.7), (0.09, 1.45), (0.14, 1.35), (0.195, 1.24), (0.18, 1.14), (0.12, 1.04), (0.11, 0.98)],
          M["glassclear"], seg=28)
    set_group("Main")
    return _dims()


# ================================================================== wall clock
def wall_clock(M):
    zc = 1.45
    set_group("Main")
    cyl("Case", 1.0, 0.3, (0, 0.05, zc), M["oak"], rot=(math.pi / 2, 0, 0), verts=48, bevel=0.04)
    ring("CaseRim", (0, -0.1, zc), 0.96, "Y", M["oakdark"], thick=0.045)
    ring("Bezel", (0, -0.14, zc), 0.86, "Y", M["brass"], thick=0.05)
    cyl("Dial", 0.83, 0.02, (0, -0.105, zc), M["paper"], rot=(math.pi / 2, 0, 0), verts=48, bevel=0.002)
    ring("Chapter", (0, -0.118, zc), 0.6, "Y", M["oakdark"], thick=0.007)
    ring("ChapterOut", (0, -0.118, zc), 0.76, "Y", M["oakdark"], thick=0.006)
    for k in range(60):
        a = k / 60 * 2 * math.pi
        hour = k % 5 == 0
        r = 0.68 if hour else 0.73
        x, z = math.sin(a) * r, zc + math.cos(a) * r
        box(f"Tick{k}", (0.045 if hour else 0.012, 0.012, 0.13 if hour else 0.04), (x, -0.12, z), M["glass"], bevel=0.003, segments=1, rot=(0, a, 0))
    # spade hands
    ha, ma = math.radians(-50), math.radians(70)
    for nm, ang, ln, w, y in (("Hour", ha, 0.42, 0.045, -0.128), ("Minute", ma, 0.62, 0.032, -0.136)):
        c, s_ = math.sin(ang), math.cos(ang)
        box(f"{nm}Hand", (w, 0.012, ln), (c * ln / 2, y, zc + s_ * ln / 2), M["iron"], bevel=0.004, rot=(0, ang, 0))
        box(f"{nm}Spade", (0.1, 0.012, 0.1), (c * ln * 0.78, y, zc + s_ * ln * 0.78), M["iron"], bevel=0.004, rot=(0, ang + math.pi / 4, 0))
        box(f"{nm}Tail", (w * 1.4, 0.012, 0.14), (-c * 0.07, y, zc - s_ * 0.07), M["iron"], bevel=0.004, rot=(0, ang, 0))
    cyl("HandCap", 0.045, 0.03, (0, -0.15, zc), M["brass"], rot=(math.pi / 2, 0, 0), verts=14)
    # pointed crest with a quatrefoil, side finials and a drop below
    _gable("Crest", 0, 0.08, 0.62, zc + 0.6, zc + 1.42, 0.18, M["oak"], M["oakdark"], edge=0.045)
    _quatrefoil("CrestSeal", 0, -0.03, zc + 1.16, 0.12, M["brass"])
    for sx in (-1, 1):
        a = math.radians(55)
        sphere(f"Finial{sx}", 0.09, (sx * math.sin(a) * 1.04, 0.05, zc + math.cos(a) * 1.04), M["brass"], seg=12, rings=6)
    cone("Drop", 0.16, 0.0, 0.42, (0, 0.05, zc - 1.0 - 0.17), M["oakdark"], verts=8, rot=(math.pi, 0, 0))
    sphere("DropBead", 0.07, (0, 0.05, zc - 0.98), M["brass"], seg=10, rings=5)
    box("Hanger", (0.3, 0.04, 0.2), (0, 0.22, zc + 0.75), M["iron"], bevel=0.01)
    set_group("Glass")
    cyl("Glass", 0.84, 0.012, (0, -0.165, zc), M["glassclear"], rot=(math.pi / 2, 0, 0), verts=48, bevel=0)
    set_group("Main")
    return _dims()


# ================================================================== picture frame
def painting_mat(h, moon):
    """Oil-painted night sky (canvas object space: x across, z up, centred): a ink-blue gradient with a soft
    full moon, horizontal brush strokes and canvas texture in the normal."""
    m = bpy.data.materials.new("Painting")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])

    def mth(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, b, blend="MIX"):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v, 1)
            else:
                L(v, sock)
        return n.outputs[2]

    def maprange(v, a, b):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.clamp = True
        L(v, n.inputs[0])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = 0.0, 1.0
        return n.outputs[0]

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    wob = nt.nodes.new("ShaderNodeTexNoise")
    wob.inputs["Scale"].default_value = 3.0
    wob.inputs["Detail"].default_value = 6.0
    L(tc.outputs["Object"], wob.inputs["Vector"])
    zn = mth("ADD", mth("MULTIPLY_ADD", sep.outputs["Z"], 1 / h, 0.5), mth("MULTIPLY", mth("SUBTRACT", wob.outputs["Fac"], 0.5), 0.16))
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.02, 0.015, 0.03, 1)
    els[1].position, els[1].color = 1.0, (0.03, 0.03, 0.08, 1)
    for pos, col in ((0.3, (0.05, 0.045, 0.11)), (0.55, (0.09, 0.09, 0.2)), (0.8, (0.05, 0.06, 0.15))):
        e = els.new(pos)
        e.color = (*col, 1)
    L(zn, ramp.inputs["Fac"])
    dx = mth("SUBTRACT", sep.outputs["X"], moon[0])
    dz = mth("SUBTRACT", sep.outputs["Z"], moon[1])
    dist = mth("SQRT", mth("ADD", mth("MULTIPLY", dx, dx), mth("MULTIPLY", dz, dz)))
    halo = mth("POWER", maprange(dist, moon[2] * 4.5, moon[2]), 2.0)
    disc = maprange(dist, moon[2], moon[2] * 0.9)
    col = mix(mth("MULTIPLY", halo, 0.6), ramp.outputs["Color"], (0.55, 0.5, 0.42))
    col = mix(disc, col, (0.93, 0.88, 0.7))
    # moon craters: soft darker blotches inside the disc
    cr = nt.nodes.new("ShaderNodeTexNoise")
    cr.inputs["Scale"].default_value = 14.0
    L(tc.outputs["Object"], cr.inputs["Vector"])
    col = mix(mth("MULTIPLY", disc, mth("MULTIPLY", maprange(cr.outputs["Fac"], 0.5, 0.7), 0.35)), col, (0.55, 0.5, 0.42))
    # horizontal brush strokes
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 38.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 4.0
    st.inputs["Detail"].default_value = 4.0
    L(mp.outputs["Vector"], st.inputs["Vector"])
    shade = mth("MULTIPLY_ADD", st.outputs["Fac"], 0.5, 0.75)
    cm = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        L(shade, cm.inputs[i])
    col = mix(1.0, col, cm.outputs["Color"], blend="MULTIPLY")
    # canvas weave + strokes in the normal
    cv = nt.nodes.new("ShaderNodeTexNoise")
    cv.inputs["Scale"].default_value = 90.0
    L(tc.outputs["Object"], cv.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    L(mth("ADD", st.outputs["Fac"], mth("MULTIPLY", cv.outputs["Fac"], 0.5)), bump.inputs["Height"])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, col, 0.55, mv.outputs[0], bump.outputs["Normal"], 0.0, False, 0.3)
    return m


def picture_frame(M):
    W, H = 3.6, 2.6               # canvas
    FW = 0.34                     # frame rail width
    zc = FW + H / 2
    ebony = material("Ebony", "NH_DeskWood", tint=(0.12, 0.08, 0.06), scale=0.22, rough_add=0.0, wear=0.5)
    sil = flat("Silhouette", (0.012, 0.01, 0.016), 0.85, wear=0.0, dirt=0.3)
    hill = flat("FarHill", (0.04, 0.03, 0.065), 0.85, wear=0.0, dirt=0.3)
    lit = flat("LitWindow", (1.0, 0.62, 0.22), 0.5, wear=0.0, dirt=0.0)
    box("Canvas", (W, 0.04, H), (0, 0.04, zc), painting_mat(H, (0.95, 0.62, 0.21)), bevel=0.0, segments=1)
    # frame: ebonised rails, a gilt slip round the canvas, a gilt bead round the outside, rosettes and a crest
    for name, size, loc in (("RailT", (W + 2 * FW, 0.16, FW), (0, -0.0, zc + H / 2 + FW / 2)), ("RailB", (W + 2 * FW, 0.16, FW), (0, 0, FW / 2)),
                            ("RailL", (FW, 0.16, H), (-W / 2 - FW / 2, 0, zc)), ("RailR", (FW, 0.16, H), (W / 2 + FW / 2, 0, zc))):
        box(name, size, loc, ebony, bevel=0.04)
    hw, hh = W / 2, H / 2
    tube("Slip", [(-hw, -0.03, zc - hh), (hw, -0.03, zc - hh), (hw, -0.03, zc + hh), (-hw, -0.03, zc + hh)], 0.045, M["brass"],
         closed=True, square=True, poly=True)
    ow, oh = hw + FW - 0.03, hh + FW - 0.03
    tube("Bead", [(-ow, -0.08, zc - oh), (ow, -0.08, zc - oh), (ow, -0.08, zc + oh), (-ow, -0.08, zc + oh)], 0.04, M["brass"],
         closed=True, poly=True)
    tube("Fillet", [(-hw - FW / 2, -0.085, zc - hh - FW / 2), (hw + FW / 2, -0.085, zc - hh - FW / 2), (hw + FW / 2, -0.085, zc + hh + FW / 2),
                    (-hw - FW / 2, -0.085, zc + hh + FW / 2)], 0.014, M["brass"], closed=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            _quatrefoil(f"Rose{sx}{sz}", sx * (hw + FW / 2), -0.1, zc + sz * (hh + FW / 2), 0.11, M["brass"])
            sphere(f"RoseBoss{sx}{sz}", 0.045, (sx * (hw + FW / 2), -0.1, zc + sz * (hh + FW / 2)), M["brass"], seg=8, rings=4)
    _gable("Crest", 0, 0.0, 0.75, H + 2 * FW - 0.05, H + 2 * FW + 0.5, 0.12, ebony, M["brass"], edge=0.035)
    _quatrefoil("CrestSeal", 0, -0.07, H + 2 * FW + 0.17, 0.11, M["brass"])
    box("Plaque", (0.9, 0.03, 0.16), (0, -0.095, FW / 2), M["brass"], bevel=0.012)
    # the painting's relief: far hills, the near hill with the school and a dead tree, lit windows
    y0 = 0.013
    xs = [-W / 2 + 0.01 + i * (W - 0.02) / 30 for i in range(31)]
    far = [(x, zc - hh + 0.62 + 0.16 * math.sin(1.7 * x + 0.5) + 0.06 * math.sin(4.3 * x)) for x in xs]
    prism("FarHills", [(xs[-1], zc - hh + 0.01), (xs[0], zc - hh + 0.01)] + far, y0, 0.008, hill)
    near = [(x, zc - hh + 0.36 + 0.12 * math.sin(2.3 * x + 1.2) + 0.03 * math.sin(7 * x)) for x in xs]
    prism("NearHill", [(xs[-1], zc - hh + 0.01), (xs[0], zc - hh + 0.01)] + near, y0 - 0.004, 0.008, sil)
    gz = zc - hh + 0.34
    yb = y0 - 0.008
    box("Hall", (1.05, 0.008, 0.42), (0.05, yb, gz + 0.21), sil, bevel=0.0, segments=1)
    prism("HallRoof", [(-0.47, gz + 0.42), (0.57, gz + 0.42), (0.05, gz + 0.66)], yb, 0.008, sil)
    for tx, th in ((-0.5, 0.82), (0.6, 0.72)):
        box(f"Tower{tx}", (0.17, 0.008, th), (tx, yb, gz + th / 2), sil, bevel=0.0, segments=1)
        prism(f"Spire{tx}", [(tx - 0.1, gz + th), (tx + 0.1, gz + th), (tx, gz + th + 0.38)], yb, 0.008, sil)
    box("Belfry", (0.2, 0.008, 0.5), (0.05, yb, gz + 0.66 + 0.15), sil, bevel=0.0, segments=1)
    prism("BelfrySpire", [(-0.07, gz + 1.06), (0.17, gz + 1.06), (0.05, gz + 1.6)], yb, 0.008, sil)
    for k in range(7):
        x = -0.36 + k * 0.135
        box(f"Window{k}", (0.04, 0.006, 0.08), (x, yb - 0.005, gz + 0.22 + (0.04 if k % 2 else 0)), lit, bevel=0.0, segments=1)
    for tx, th in ((-0.5, 0.82), (0.6, 0.72)):
        box(f"TowerWin{tx}", (0.04, 0.006, 0.09), (tx, yb - 0.005, gz + th * 0.7), lit, bevel=0.0, segments=1)
    box("BelfryWin", (0.05, 0.006, 0.11), (0.05, yb - 0.005, gz + 0.85), lit, bevel=0.0, segments=1)
    tx, tz = -1.32, zc - hh + 0.3
    tube("Trunk", [(tx, yb, tz), (tx + 0.04, yb, tz + 0.4), (tx - 0.02, yb, tz + 0.8)], 0.025, sil)
    for k, pts in enumerate(([(tx + 0.03, tz + 0.4), (tx + 0.28, tz + 0.62), (tx + 0.42, tz + 0.6)],
                             [(tx, tz + 0.62), (tx - 0.25, tz + 0.82), (tx - 0.32, tz + 0.98)],
                             [(tx - 0.02, tz + 0.8), (tx + 0.1, tz + 1.05), (tx + 0.22, tz + 1.12)],
                             [(tx + 0.28, tz + 0.62), (tx + 0.33, tz + 0.8)], [(tx - 0.25, tz + 0.82), (tx - 0.4, tz + 0.84)])):
        tube(f"Branch{k}", [(x, yb, z) for x, z in pts], 0.012 if k < 3 else 0.008, sil)
    return _dims()


# ================================================================== candle cluster
def candle_cluster(M):
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, wear=0.05, dirt=0.55)
    red = flat("WaxCrimson", (0.3, 0.02, 0.03), 0.45, wear=0.05, dirt=0.55)
    set_group("Main")
    cyl("Tray", 0.64, 0.06, (0, 0, 0.12), M["iron"], verts=40, bevel=0.02)
    ring("TrayRim", (0, 0, 0.16), 0.63, "Z", M["iron"], thick=0.03)
    ring("TrayInlay", (0, 0, 0.152), 0.5, "Z", M["brass"], thick=0.012)
    for k in range(3):
        a = k / 3 * 2 * math.pi + 0.3
        sphere(f"Foot{k}", 0.07, (math.cos(a) * 0.45, math.sin(a) * 0.45, 0.07), M["iron"], seg=10, rings=5)
    T = 0.15
    rnd = random.Random(19)
    candles = [(0.0, 0.02, 0.11, 1.0), (0.28, 0.14, 0.1, 0.66), (-0.26, 0.2, 0.09, 0.78), (0.14, -0.3, 0.1, 0.48),
               (-0.3, -0.18, 0.12, 0.38), (0.42, -0.12, 0.075, 0.3), (-0.02, 0.4, 0.08, 0.55)]
    flames = []
    for k, (x, y, r, h) in enumerate(candles):
        m = red if k == 2 else wax
        lathe(f"Puddle{k}", [(0, T), (r * 1.7, T), (r * 1.55, T + 0.018), (r * 1.1, T + 0.03), (0, T + 0.035)], m, seg=20, loc=(x, y, 0), jitter=(0.14, k))
        lathe(f"Candle{k}", [(0, T), (r, T), (r, T + h - 0.04), (r * 0.97, T + h - 0.005), (r * 0.86, T + h), (r * 0.55, T + h - 0.03),
                             (0, T + h - 0.04)], m, seg=22, loc=(x, y, 0), jitter=(0.025, 30 + k))
        for d in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            ln = rnd.uniform(0.08, 0.28)
            sphere(f"Drip{k}{d}", 0.024, (x + math.cos(a) * r * 1.01, y + math.sin(a) * r * 1.01, T + h - 0.03 - ln / 2), m, seg=8, rings=5,
                   scale=(1, 1, ln / 0.05))
        tube(f"Wick{k}", [(x, y, T + h - 0.04), (x, y, T + h + 0.03)], 0.01, M["felt"], poly=True)
        flames.append((x, y, T + h + 0.01, 0.12 + r * 0.5))
    # a run of wax over the tray's edge
    sphere("Overflow", 0.04, (0.6, -0.2, 0.12), wax, seg=10, rings=5, scale=(0.8, 1, 2.2))
    set_group("Glow")
    for k, (x, y, z, fh) in enumerate(flames):
        flame(f"Flame{k}", (x, y, z), h=fh)
    set_group("Main")
    return _dims()


# ================================================================== umbrella stand
def _umbrella(prefix, canopy, handle, M, cane=False):
    if cane:
        tube(f"{prefix}Shaft", [(0, 0, 0.28), (0, 0, 2.7)], 0.03, handle, poly=True)
        cyl(f"{prefix}Ferrule", 0.034, 0.12, (0, 0, 0.32), M["brass"], verts=10)
        sphere(f"{prefix}Knob", 0.09, (0, 0, 2.76), M["brass"], seg=14, rings=7, scale=(1, 1, 1.15))
        ring(f"{prefix}Collar", (0, 0, 2.66), 0.04, "Z", M["brass"], thick=0.015)
        return
    tube(f"{prefix}Tip", [(0, 0, 0.27), (0, 0, 0.5)], 0.016, M["brasssteel"], poly=True)
    lathe(f"{prefix}Canopy", [(0, 0.44), (0.03, 0.5), (0.08, 0.75), (0.12, 1.1), (0.13, 1.4), (0.12, 1.75), (0.08, 2.05), (0.04, 2.25),
                              (0.02, 2.3), (0, 2.31)], canopy, seg=32, flute=(8, 0.38))
    ring(f"{prefix}Tie", (0, 0, 1.72), 0.105, "Z", canopy, thick=0.016)
    sphere(f"{prefix}Button", 0.02, (0.11, 0, 1.72), M["brass"], seg=6, rings=3)
    tube(f"{prefix}Shaft", [(0, 0, 2.28), (0, 0, 2.62)], 0.022, M["iron"], poly=True)
    tube(f"{prefix}Crook", [(0, 0, 2.58), (0, 0, 2.82), (0.04, 0, 2.96), (0.16, 0, 2.99), (0.23, 0, 2.87), (0.21, 0, 2.74)], 0.035, handle)
    ring(f"{prefix}Ferrule", (0, 0, 2.6), 0.03, "Z", M["brass"], thick=0.012)


def umbrella_stand(M):
    black = flat("Gamp", (0.022, 0.022, 0.028), 0.55, wear=0.25, dirt=0.6)
    gamp_red = material("GampCrimson", "NH_Leather", tint=(0.2, 0.02, 0.03), scale=3.0, normal=0.25, rough_add=0.25, wear=0.25)
    lathe("Foot", [(0, 0), (0.56, 0), (0.58, 0.05), (0.54, 0.12), (0.5, 0.16), (0.5, 0.24), (0, 0.24)], M["iron"], seg=40)
    lathe("Body", [(0, 0.2), (0.48, 0.2), (0.47, 0.6), (0.46, 1.2), (0.47, 1.85)], M["iron"], seg=72, flute=(18, 0.05))
    lathe("Mouth", [(0, 1.8), (0.48, 1.8), (0.5, 1.9), (0.55, 2.0), (0.57, 2.06), (0.53, 2.1), (0.47, 2.06), (0.44, 1.98), (0.43, 1.9),
                    (0.42, 0.26), (0, 0.26)], M["iron"], seg=48)
    for z, r in ((0.3, 0.495), (1.0, 0.48), (1.78, 0.48)):
        ring(f"Band{z}", (0, 0, z), r, "Z", M["brass"], thick=0.025)
    for k in range(4):
        s = _mark()
        _quatrefoil(f"Foil{k}", 0, -0.475, 1.39, 0.15, M["brass"])
        sphere(f"FoilBoss{k}", 0.05, (0, -0.48, 1.39), M["brass"], seg=8, rings=4)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    # two furled umbrellas and a cane, leaning a little apart
    for k, (yaw, canopy, handle, cane) in enumerate(((0.5, black, M["oakdark"], False), (2.6, gamp_red, M["leatherdark"], False),
                                                     (4.4, None, M["oakdark"], True))):
        s = _mark()
        _umbrella(f"Umbrella{k}", canopy, handle, M, cane=cane)
        d = Vector((math.cos(yaw), math.sin(yaw), 0)) * 0.19
        _xform(s, Matrix.Translation(d) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Translation((0, 0, 0.27)) @
               Matrix.Rotation(math.radians(2.5), 4, "Y") @ Matrix.Translation((0, 0, -0.27)))
    return _dims()


# ================================================================== coat rack
def coat_rack(M):
    scarf = material("Scarf", "NH_Leather", tint=(0.28, 0.025, 0.04), scale=3.5, normal=0.3, rough_add=0.35, wear=0.15)
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        pts = [(0.1, 0.5), (0.34, 0.32), (0.6, 0.1), (0.78, 0.12), (0.8, 0.26), (0.7, 0.28)]
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in pts], 0.035, M["iron"], square=True)
        sphere(f"Toe{k}", 0.07, (c * 0.6, s_ * 0.6, 0.07), M["iron"], seg=10, rings=5)
    lathe("Post", [(0, 0.3), (0.2, 0.3), (0.22, 0.36), (0.2, 0.42), (0.14, 0.5), (0.14, 0.62), (0.18, 0.7), (0.18, 0.78), (0.12, 0.86),
                   (0.1, 1.2), (0.09, 2.8), (0.13, 2.9), (0.13, 3.0), (0.09, 3.1), (0.085, 4.6), (0.12, 4.68), (0.12, 4.76), (0.09, 4.82),
                   (0.09, 5.2), (0.13, 5.28), (0.13, 5.36), (0.1, 5.44), (0.11, 5.6), (0.15, 5.7), (0.1, 5.8), (0, 5.82)], M["oak"], seg=24)
    sphere("FinialBall", 0.13, (0, 0, 5.9), M["oakdark"], seg=16, rings=8)
    cone("FinialSpire", 0.08, 0.0, 0.32, (0, 0, 6.15), M["oakdark"], verts=8)
    sphere("FinialTip", 0.035, (0, 0, 6.32), M["brass"], seg=8, rings=4)
    ring("CollarHi", (0, 0, 5.32), 0.135, "Z", M["brass"], thick=0.02)
    ring("CollarLo", (0, 0, 4.72), 0.125, "Z", M["brass"], thick=0.02)
    ring("CollarMid", (0, 0, 2.95), 0.135, "Z", M["brass"], thick=0.02)
    for tier, (z, off, sc) in enumerate(((5.32, 0.0, 1.0), (4.72, math.pi / 4, 0.8))):
        for k in range(4):
            a = k / 4 * 2 * math.pi + off
            c, s_ = math.cos(a), math.sin(a)
            pts = [(0.1, z), (0.28 * sc + 0.02, z + 0.02), (0.4 * sc, z + 0.16 * sc), (0.42 * sc, z + 0.32 * sc), (0.36 * sc, z + 0.4 * sc)]
            tube(f"Hook{tier}{k}", [(c * r, s_ * r, zz) for r, zz in pts], 0.03, M["iron"])
            sphere(f"HookTip{tier}{k}", 0.045, (c * 0.36 * sc, s_ * 0.36 * sc, z + 0.4 * sc), M["brass"], seg=8, rings=4)
    # a crimson scarf over the +X hook
    x = 0.33
    strip("Scarf", [(x, 0.12, 4.3), (x, 0.13, 4.9), (x, 0.08, 5.33), (x, 0.0, 5.43), (x, -0.08, 5.33), (x, -0.13, 4.8), (x + 0.01, -0.12, 4.1),
                    (x + 0.02, -0.1, 3.72)], 0.2, (1, 0, 0), scarf, thick=0.035)
    for end, (y, z) in enumerate(((0.12, 4.3), (-0.1, 3.72))):
        for j in range(5):
            xx = x - 0.08 + j * 0.04 + end * 0.02
            tube(f"Tassel{end}{j}", [(xx, y, z + 0.01), (xx, y, z - 0.12)], 0.008, scarf, poly=True)
    # a leather satchel on the -X hook
    lea = M["leather"]
    box("Satchel", (0.2, 0.62, 0.5), (-0.44, 0, 4.53), lea, bevel=0.05, segments=3)
    box("Flap", (0.03, 0.64, 0.32), (-0.555, 0, 4.64), lea, bevel=0.012)
    box("FlapTop", (0.22, 0.64, 0.03), (-0.45, 0, 4.79), lea, bevel=0.012)
    box("Buckle", (0.02, 0.09, 0.08), (-0.575, 0, 4.5), M["brass"], bevel=0.008)
    box("BuckleStrap", (0.012, 0.06, 0.2), (-0.574, 0, 4.58), M["leatherdark"], bevel=0.004)
    tube("SatchelStrap", [(-0.44, -0.28, 4.76), (-0.38, -0.15, 5.15), (-0.31, -0.03, 5.4), (-0.31, 0.03, 5.4), (-0.38, 0.15, 5.15),
                          (-0.44, 0.28, 4.76)], 0.025, M["leatherdark"], square=True)
    return _dims()


# tall, narrow props need the preview camera further back
P.PREVIEW_PAD.update({"CeramicVase": 1.25, "CoatRack": 1.15, "UmbrellaStand": 1.2, "FlowerVase": 1.1, "OilLamp": 1.15, "CandleCluster": 1.1})

P.BUILD.update({
    "CeramicVase": ceramic_vase,
    "FlowerVase": flower_vase,
    "PottedPlant": potted_plant,
    "LunchTray": lunch_tray,
    "LunchTrayEmpty": lunch_tray_empty,
    "BookStack": book_stack,
    "OilLamp": oil_lamp,
    "WallClock": wall_clock,
    "PictureFrame": picture_frame,
    "CandleCluster": candle_cluster,
    "UmbrellaStand": umbrella_stand,
    "CoatRack": coat_rack,
})
