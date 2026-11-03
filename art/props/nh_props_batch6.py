"""Props batch 6 (2026-11-03): clubs and faculty props for nh_props.py, in the same gothic style.

  BannerRavens    the Night Ravens' banner (basketball): purple cloth, a raven displayed on a bone roundel
  BannerRovers    the Grave Rovers' banner (soccer): green cloth, a grave cross and a ball on an ink roundel
  BannerWardens   the Iron Wardens' banner (football): iron-grey cloth with rust-red braid, an iron shield with a brass chevron
  BannerVigil     The Vigil's banner: ink cloth with gold braid, a candle and its flame in gold
  BannerCrimson   The Crimson Court's banner: crimson cloth, a thorned bone rose on an ink roundel
                  (each banner: folded cloth with braid and a brass fringe on an iron rod with finials, on
                  scrolled wall brackets; wall pieces)
  ChessTable      a black marble table on a fluted iron pedestal, an inlaid board and a full set of bone and
                  ink pieces, a few moves into a game
  ArtEasel        an iron easel with a moonlit canvas, a palette of paint on a peg, brushes in a glass jar
                  (Glass: the jar)
  Gramophone      a crimson enamel cabinet with brass corners, a record on the platter, a tonearm and a fluted
                  brass horn (table piece)
  Telescope       a brass refracting telescope tilted to the sky on a yoke and an iron tripod (Glass: the lens)
  FilingCabinet   a cast-iron four-drawer cabinet with brass label frames and pulls, arched side panels and a
                  small crest
  Typewriter      black enamel and brass, a sheet of typed paper in the carriage, ribbon spools (table piece)
  TeaTrolley      an iron and brass two-tier trolley on castors: a teapot, cups and saucers, milk and sugar,
                  a three-tier cake stand
  Pigeonholes     staff mail cubbies: an iron case of 24 slots with brass name plates, letters, envelopes with
                  wax seals, parcels and scrolls (wall piece)

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _quatrefoil, _arch_loop_x, material
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mesh, prism, rrect, _mark, _xform, _aim, _dims, flat, painting_mat
from nh_props_batch5 import marble


# ------------------------------------------------------------------ helpers

def lin(r, g, b, k=1.0):
    """sRGB 0-255 to a linear tint."""
    return tuple(((c / 255.0) ** 2.2) * k for c in (r, g, b))


def relief(name, poly, pos, depth, mat, plane="XZ", bevel=0.0):
    """A flat (possibly concave) polygon extruded `depth`, caps triangulated so concave shapes import cleanly.
    plane XZ: poly in (x, z), thickness along Y centred on pos; YZ: (y, z) along X; XY: (x, y) along Z from pos."""
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
    caps = [bm.faces.new(a), bm.faces.new(list(reversed(b)))]
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=caps, quad_method="BEAUTY", ngon_method="EAR_CLIP")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, bevel)


def ellipse(cx, cz, rx, rz, n=20, a0=0.0):
    return [(cx + math.cos(a0 + i / n * 2 * math.pi) * rx, cz + math.sin(a0 + i / n * 2 * math.pi) * rz) for i in range(n)]


def mirror_half(half):
    """A symmetric outline from its right half (x >= 0), listed top to bottom with both ends on the axis."""
    return half + [(-x, z) for x, z in reversed(half) if x > 1e-6]


def bone_ink():
    return (flat("Bone", (0.8, 0.76, 0.66), 0.45, dirt=0.6), flat("InkLacquer", (0.022, 0.02, 0.026), 0.22, dirt=0.5))


# ================================================================== banners
HW, TOP, Y0, ZC = 1.4, 5.8, -0.32, 3.45


def _fold(x, t):
    """Vertical pleats toward the edges; the middle stays flat for the emblem."""
    k = min(1.0, max(0.0, (abs(x) - 0.62) / (HW - 0.62))) ** 1.2
    return 0.075 * k * (0.45 + 0.55 * t) * math.sin(x / HW * math.pi * 3.0)


def _cloth(xa, xb, ta, tb, nx, nt, zb, dy=0.0):
    rows = []
    for i in range(nt + 1):
        t = ta + (tb - ta) * i / nt
        row = []
        for j in range(nx + 1):
            x = xa + (xb - xa) * j / nx
            z = TOP - t * (TOP - zb(x))
            row.append(Vector((x, Y0 - _fold(x, t) - dy, z)))
        rows.append(row)
    return rows


def _banner(M, cloth_rgb, emblem, field=None, trim=None, tail="point"):
    cloth = material("BannerCloth", "NH_Leather", tint=cloth_rgb, scale=4.0, normal=0.3, rough_add=0.45, wear=0.05, dirt=0.6)
    trim = trim or M["brass"]
    lo, hi = 0.35, 1.0
    if tail == "point":
        def zb(x):
            return lo + (hi - lo) * abs(x) / HW          # lowest in the middle
    else:
        def zb(x):
            return lo + (hi - lo) * (1 - abs(x) / HW)    # swallowtail: lowest at the sides
    # the cloth sways (its own piece, origin on the rod); the rod, finials and brackets stay put
    set_group("Cloth", hinge=(0, Y0, TOP + 0.06), swing=1)
    _mesh("Cloth", _cloth(-HW, HW, 0.0, 1.0, 28, 34, zb), cloth, 0.03)
    # braid down both sides and along the hem, following the folds
    for sx in (-1, 1):
        xa, xb = sorted((sx * (HW - 0.17), sx * (HW - 0.07)))
        _mesh(f"Braid{sx}", _cloth(xa, xb, 0.02, 0.985, 2, 34, zb, dy=0.019), trim, 0.012)
    _mesh("Hem", _cloth(-HW + 0.07, HW - 0.07, 0.905, 0.945, 28, 2, zb, dy=0.019), trim, 0.012)
    # sleeve over the rod, the rod, finials, scrolled wall brackets
    zr = TOP + 0.06
    cyl("Sleeve", 0.1, 2.86, (0, Y0, zr), cloth, rot=(0, math.pi / 2, 0), verts=20, bevel=0.01)
    set_group("Main")
    tube("Rod", [(-1.78, Y0, zr), (1.78, Y0, zr)], 0.035, M["iron"], poly=True)
    for sx in (-1, 1):
        sphere(f"FinialBall{sx}", 0.07, (sx * 1.82, Y0, zr), M["brass"], seg=12, rings=6)
        cone(f"FinialSpike{sx}", 0.05, 0.0, 0.2, (sx * 1.95, Y0, zr), M["brass"], verts=8, rot=(0, sx * math.pi / 2, 0))
        x = sx * 1.58
        box(f"WallPlate{sx}", (0.2, 0.05, 0.38), (x, 0.0, zr - 0.05), M["iron"], bevel=0.012)
        tube(f"Bracket{sx}", [(x, 0.0, zr), (x, Y0, zr)], 0.03, M["iron"], square=True, poly=True)
        tube(f"Scroll{sx}", [(x, 0.0, zr - 0.2), (x, -0.12, zr - 0.18), (x, -0.24, zr - 0.08), (x, Y0 + 0.04, zr - 0.02)], 0.022, M["iron"])
        hoop(f"Curl{sx}", (x, -0.1, zr - 0.28), 0.06, "X", M["iron"], thick=0.015)
    set_group("Cloth")
    # brass fringe along the hem and tassels at the points
    rnd = random.Random(4)
    x = -HW + 0.06
    while x < HW - 0.05:
        z = zb(x)
        y = Y0 - _fold(x, 1.0)
        ln = 0.13 + rnd.uniform(-0.015, 0.015)
        tube(f"Fringe{x:.2f}", [(x, y, z + 0.02), (x, y - 0.004, z - ln)], 0.011, trim, poly=True)
        x += 0.085
    tips = [0.0] if tail == "point" else [-HW + 0.02, HW - 0.02]
    for k, tx in enumerate(tips):
        tz = zb(tx)
        sphere(f"TasselKnot{k}", 0.055, (tx, Y0, tz - 0.04), trim, seg=10, rings=6)
        cone(f"Tassel{k}", 0.06, 0.02, 0.26, (tx, Y0, tz - 0.22), trim, verts=12, rot=(math.pi, 0, 0))
    # the roundel and the emblem, in low relief on the flat middle
    if field is not None:
        cyl("Field", 0.82, 0.03, (0, Y0 - 0.055, ZC), field, rot=(math.pi / 2, 0, 0), verts=40, bevel=0.006)
    hoop("Roundel", (0, Y0 - 0.075, ZC), 0.86, "Y", M["brass"], thick=0.028)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        sphere(f"Stud{k}", 0.03, (math.sin(a) * 0.86, Y0 - 0.1, ZC + math.cos(a) * 0.86), M["brass"], seg=8, rings=4)
    emblem(Y0 - 0.085)
    set_group("Main")
    return _dims()


def banner_ravens(M):
    bone, ink = bone_ink()

    def raven(ye):
        half = [(0.0, 0.62), (0.07, 0.6), (0.1, 0.5), (0.15, 0.4), (0.3, 0.47), (0.48, 0.6), (0.68, 0.66), (0.6, 0.52), (0.66, 0.44),
                (0.55, 0.36), (0.6, 0.27), (0.47, 0.22), (0.5, 0.12), (0.35, 0.09), (0.2, 0.03), (0.15, -0.2), (0.22, -0.48),
                (0.1, -0.42), (0.05, -0.52), (0.0, -0.45)]
        relief("Raven", [(x, ZC + z) for x, z in mirror_half(half)], ye, 0.03, ink, bevel=0.004)
        relief("Beak", [(-0.03, ZC + 0.52), (0.03, ZC + 0.52), (0.0, ZC + 0.4)], ye - 0.02, 0.02, M["brass"])
        for sx in (-1, 1):
            sphere(f"Eye{sx}", 0.022, (sx * 0.035, ye - 0.025, ZC + 0.56), M["crimson"], seg=6, rings=4)
            for k in range(3):
                relief(f"Feather{sx}{k}", [(sx * (0.3 + k * 0.1), ZC + 0.4 - k * 0.07), (sx * (0.36 + k * 0.1), ZC + 0.43 - k * 0.07),
                                           (sx * (0.34 + k * 0.1), ZC + 0.18 - k * 0.04)], ye - 0.02, 0.012, M["brass"])
    return _banner(M, lin(120, 70, 160, 0.55), raven, field=bone, tail="swallow")


def banner_rovers(M):
    bone, ink = bone_ink()

    def emblem(ye):
        # a grave cross with flared ends on a low mound, the ball resting against it
        arm, w = 0.055, 0.1
        cross = [(-w * 0.7, ZC - 0.55), (w * 0.7, ZC - 0.55), (arm, ZC - 0.3), (arm, ZC + 0.12), (0.32, ZC + 0.08), (0.36, ZC + 0.2),
                 (0.32, ZC + 0.32), (arm, ZC + 0.28), (arm, ZC + 0.5), (w, ZC + 0.62), (-w, ZC + 0.62), (-arm, ZC + 0.5),
                 (-arm, ZC + 0.28), (-0.32, ZC + 0.32), (-0.36, ZC + 0.2), (-0.32, ZC + 0.08), (-arm, ZC + 0.12), (-arm, ZC - 0.3)]
        relief("Cross", cross, ye, 0.03, bone, bevel=0.004)
        top = [(-0.62 + 1.24 * i / 10, ZC - 0.6 + 0.09 * math.sin(math.pi * i / 10)) for i in range(11)]
        relief("Mound", top + [(0.62, ZC - 0.66), (-0.62, ZC - 0.66)], ye, 0.025, M["brass"])
        bx, bz, br = 0.36, ZC - 0.33, 0.2
        cyl("Ball", br, 0.035, (bx, ye - 0.01, bz), bone, rot=(math.pi / 2, 0, 0), verts=28, bevel=0.008)
        for k in range(6):
            a = k / 5 * 2 * math.pi + 0.3
            cx, cz = (bx, bz) if k == 5 else (bx + math.cos(a) * br * 0.72, bz + math.sin(a) * br * 0.72)
            r = 0.06 if k == 5 else 0.045
            relief(f"Patch{k}", ellipse(cx, cz, r, r, n=5, a0=math.pi / 2), ye - 0.032, 0.012, ink)
    return _banner(M, lin(70, 140, 90, 0.5), emblem, field=ink, tail="point")


def banner_wardens(M):
    bone, ink = bone_ink()

    def emblem(ye):
        # a heater shield in iron, a brass rim, a chevron and rivets
        half = [(0.0, ZC + 0.5), (0.46, ZC + 0.5)]
        for i in range(11):
            t = i / 10
            half.append((0.46 * math.cos(t * math.pi / 2) ** 0.9, ZC + 0.15 - 0.75 * math.sin(t * math.pi / 2) ** 1.3))
        half[-1] = (0.0, half[-1][1])
        shield = mirror_half(half)
        relief("Shield", shield, ye, 0.04, M["iron"], bevel=0.008)
        tube("ShieldRim", [(x, ye - 0.025, z) for x, z in shield], 0.022, M["brass"], closed=True, square=True, poly=True)
        relief("Chevron", [(-0.36, ZC - 0.12), (0.0, ZC + 0.22), (0.36, ZC - 0.12), (0.36, ZC - 0.27), (0.0, ZC + 0.07), (-0.36, ZC - 0.27)],
               ye - 0.028, 0.016, M["brass"])
        for k, (x, z) in enumerate(((-0.3, ZC + 0.38), (0.3, ZC + 0.38), (0.0, ZC - 0.42))):
            sphere(f"Rivet{k}", 0.04, (x, ye - 0.025, z), M["brass"], seg=8, rings=4)
    # iron-grey cloth with rust-red braid, so it never reads as the Crimson Court
    return _banner(M, lin(84, 86, 94, 0.55), emblem, field=bone, trim=flat("WardensRust", lin(150, 60, 34, 0.85), 0.6), tail="swallow")


def banner_vigil(M):
    def emblem(ye):
        # a tall candle with a drip, its flame, rays of candlelight
        relief("Candle", [(-0.12, ZC - 0.55), (0.12, ZC - 0.55), (0.12, ZC + 0.15), (0.06, ZC + 0.2), (0.0, ZC + 0.12), (-0.12, ZC + 0.15)],
               ye, 0.03, M["brass"], bevel=0.004)
        relief("Drip", [(0.12, ZC + 0.12), (0.17, ZC + 0.1), (0.16, ZC - 0.1), (0.13, ZC - 0.14), (0.12, ZC - 0.05)], ye - 0.006, 0.02, M["brass"])
        relief("Dish", [(-0.32, ZC - 0.55), (0.32, ZC - 0.55), (0.24, ZC - 0.64), (-0.24, ZC - 0.64)], ye, 0.03, M["brass"])
        half = [(0.0, ZC + 0.66)]
        for i in range(1, 10):
            t = i / 10
            half.append((0.15 * math.sin(math.pi * t) ** 0.8 * (0.4 + 0.6 * t), ZC + 0.66 - 0.42 * t))
        half.append((0.0, ZC + 0.24))
        relief("Flame", mirror_half(half), ye - 0.01, 0.03, M["brass"], bevel=0.004)
        for k in range(9):
            a = math.radians(-80 + k * 20)
            r0, r1 = 0.32, (0.62 if k % 2 == 0 else 0.5)
            cz = ZC + 0.4
            relief(f"Ray{k}", [(math.sin(a - 0.05) * r0, cz + math.cos(a - 0.05) * r0), (math.sin(a) * r1, cz + math.cos(a) * r1),
                               (math.sin(a + 0.05) * r0, cz + math.cos(a + 0.05) * r0)], ye, 0.014, M["brass"])
    return _banner(M, (0.03, 0.028, 0.036), emblem, field=None, tail="point")


def banner_crimson(M):
    bone, ink = bone_ink()

    def emblem(ye):
        # a thorned rose: a bone bloom, a brass stem with thorns, two leaves
        stem = [(0.05 * math.sin(i / 8 * 3.0), ZC + 0.1 - 0.7 * i / 8) for i in range(9)]
        relief("Stem", [(x - 0.03, z) for x, z in stem] + [(x + 0.03, z) for x, z in reversed(stem)], ye, 0.025, M["brass"])
        for k, (i, sx) in enumerate(((2, 1), (4, -1), (5, 1), (7, -1))):
            x, z = stem[i]
            relief(f"Thorn{k}", [(x + sx * 0.025, z + 0.03), (x + sx * 0.11, z + 0.05), (x + sx * 0.025, z - 0.02)], ye - 0.005, 0.02, M["brass"])
        for k, (sx, z) in enumerate(((-1, ZC - 0.3), (1, ZC - 0.45))):
            upper = [(sx * (0.04 + 0.34 * t), z + 0.16 * math.sin(math.pi * t)) for t in [i / 8 for i in range(9)]]
            lower = [(sx * (0.04 + 0.34 * t), z - 0.06 * math.sin(math.pi * t)) for t in [i / 8 for i in range(7, 0, -1)]]
            relief(f"Leaf{k}", upper + lower, ye - 0.003, 0.02, M["brass"])
        bz = ZC + 0.28
        for rk, (cnt, rr, pr) in enumerate(((7, 0.25, 0.17), (6, 0.15, 0.13), (5, 0.06, 0.09))):
            for i in range(cnt):
                a = i / cnt * 2 * math.pi + rk * 0.4
                relief(f"Petal{rk}{i}", ellipse(math.cos(a) * rr, bz + math.sin(a) * rr * 0.85, pr, pr * 0.8, n=12, a0=a),
                       ye - 0.01 - rk * 0.012, 0.02, bone, bevel=0.003)
        relief("Heart", ellipse(0.0, bz, 0.05, 0.045, n=10), ye - 0.05, 0.02, M["crimson"])
    return _banner(M, lin(118, 12, 22, 0.75), emblem, field=bone_ink()[1], tail="swallow")


# ================================================================== chess table
def _chess_piece(prefix, kind, mat, accent):
    s = _mark()
    base = [(0, 0), (0.078, 0), (0.078, 0.022), (0.062, 0.034)]
    if kind == "P":
        lathe(f"{prefix}Body", base + [(0.04, 0.05), (0.027, 0.1), (0.045, 0.11), (0.03, 0.12), (0, 0.12)], mat, seg=12)
        sphere(f"{prefix}Head", 0.042, (0, 0, 0.152), mat, seg=12, rings=6)
    elif kind == "R":
        lathe(f"{prefix}Body", base + [(0.052, 0.05), (0.05, 0.18), (0.068, 0.2), (0.068, 0.24), (0.045, 0.24), (0.045, 0.225), (0, 0.225)], mat, seg=12)
        for k in range(4):
            a = k / 4 * 2 * math.pi + math.pi / 4
            box(f"{prefix}Merlon{k}", (0.032, 0.032, 0.035), (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.255), mat, bevel=0.004, rot=(0, 0, a))
    elif kind == "B":
        lathe(f"{prefix}Body", base + [(0.036, 0.12), (0.052, 0.14), (0.03, 0.155), (0.046, 0.2), (0.04, 0.25), (0.02, 0.28), (0, 0.29)], mat, seg=12)
        sphere(f"{prefix}Tip", 0.016, (0, 0, 0.3), accent, seg=8, rings=4)
        box(f"{prefix}Slit", (0.008, 0.06, 0.04), (0.02, 0, 0.24), accent, bevel=0.0, segments=1, rot=(0, math.radians(30), 0))
    elif kind in "QK":
        top = 0.3 if kind == "Q" else 0.32
        lathe(f"{prefix}Body", base + [(0.04, 0.17), (0.062, 0.2), (0.04, 0.212), (0.052, top - 0.02), (0.042, top), (0, top)], mat, seg=12)
        if kind == "Q":
            for k in range(8):
                a = k / 8 * 2 * math.pi
                sphere(f"{prefix}Crown{k}", 0.012, (math.cos(a) * 0.046, math.sin(a) * 0.046, top + 0.006), accent, seg=6, rings=3)
            sphere(f"{prefix}Orb", 0.022, (0, 0, top + 0.03), mat, seg=10, rings=5)
        else:
            box(f"{prefix}CrossV", (0.022, 0.022, 0.1), (0, 0, top + 0.05), accent, bevel=0.004)
            box(f"{prefix}CrossH", (0.07, 0.022, 0.022), (0, 0, top + 0.065), accent, bevel=0.004)
    else:   # knight: a turned base and a horse's head in profile, facing +Y
        lathe(f"{prefix}Body", base + [(0.052, 0.06), (0, 0.06)], mat, seg=12)
        head = [(-0.048, 0.055), (0.048, 0.055), (0.042, 0.12), (0.078, 0.15), (0.088, 0.18), (0.062, 0.2), (0.03, 0.212), (0.022, 0.245),
                (0.003, 0.226), (-0.024, 0.232), (-0.036, 0.2), (-0.052, 0.15), (-0.052, 0.1)]
        relief(f"{prefix}Head", head, 0.0, 0.055, mat, plane="YZ", bevel=0.006)
        relief(f"{prefix}Mane", [(-0.052, 0.1), (-0.06, 0.15), (-0.044, 0.2), (-0.03, 0.225), (-0.04, 0.2), (-0.052, 0.15)], 0.0, 0.064, accent, plane="YZ")
        for sx in (-1, 1):
            sphere(f"{prefix}Eye{sx}", 0.01, (sx * 0.028, 0.035, 0.19), accent, seg=6, rings=3)
    return s


def chess_table(M):
    bone, ink = bone_ink()
    black = marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    pale = marble("Marble")
    T = 2.4
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        pts = [(0.12, 0.5), (0.4, 0.32), (0.75, 0.09), (0.95, 0.11), (0.97, 0.26), (0.86, 0.29)]
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in pts], 0.04, M["iron"], square=True)
        sphere(f"Toe{k}", 0.075, (c * 0.75, s_ * 0.75, 0.075), M["iron"], seg=10, rings=5)
    lathe("PedFoot", [(0, 0.3), (0.34, 0.3), (0.33, 0.42), (0.22, 0.56), (0, 0.56)], M["iron"], seg=32)
    lathe("Pedestal", [(0, 0.5), (0.21, 0.5), (0.16, 0.8), (0.15, 1.8), (0, 1.8)], M["iron"], seg=48, flute=(12, 0.1))
    lathe("PedCap", [(0, 1.75), (0.17, 1.75), (0.3, 1.95), (0.5, 2.15), (0.55, T - 0.15), (0, T - 0.15)], M["iron"], seg=32)
    hoop("PedBand", (0, 0, 0.6), 0.215, "Z", M["brass"], thick=0.018)
    hoop("PedBand2", (0, 0, 1.78), 0.18, "Z", M["brass"], thick=0.018)
    box("Top", (2.4, 2.4, 0.15), (0, 0, T - 0.075), black, bevel=0.03)
    for sx in (-1, 1):
        box(f"EdgeX{sx}", (2.44, 0.04, 0.05), (0, sx * 1.21, T - 0.11), M["brass"], bevel=0.01)
        box(f"EdgeY{sx}", (0.04, 2.44, 0.05), (sx * 1.21, 0, T - 0.11), M["brass"], bevel=0.01)
    sq = 0.22
    for f in range(8):
        for r in range(8):
            box(f"Sq{f}{r}", (sq, sq, 0.012), ((f - 3.5) * sq, (r - 3.5) * sq, T + 0.006), pale if (f + r) % 2 else black, bevel=0.0, segments=1)
    tube("BoardFrame", [(-0.9, -0.9, T + 0.012), (0.9, -0.9, T + 0.012), (0.9, 0.9, T + 0.012), (-0.9, 0.9, T + 0.012)], 0.022, M["brass"],
         closed=True, square=True, poly=True)
    # the pieces: bone at the front (-Y), ink at the back, a few moves into a game
    back = "RNBQKBNR"
    pos = {}
    for f in range(8):
        pos[("bone", back[f], f)] = (f, 0)
        pos[("bone", "P", f)] = (f, 1)
        pos[("ink", back[f], f)] = (f, 7)
        pos[("ink", "P", f)] = (f, 6)
    pos[("bone", "P", 4)] = (4, 3)
    pos[("ink", "P", 3)] = (3, 4)
    pos[("bone", "N", 6)] = (5, 2)
    pos[("ink", "N", 1)] = (2, 5)
    for (side, kind, f0), (f, r) in pos.items():
        mat = bone if side == "bone" else ink
        s = _chess_piece(f"{side}{kind}{f0}", kind, mat, M["brass"])
        turn = 0.0 if side == "bone" else math.pi
        _xform(s, Matrix.Translation(((f - 3.5) * sq, (r - 3.5) * sq, T + 0.012)) @ Matrix.Rotation(turn, 4, "Z"))
    return _dims()


# ================================================================== art easel
def art_easel(M):
    paints = [flat("PaintCrimson", (0.3, 0.015, 0.025), 0.35), flat("PaintGold", (0.75, 0.52, 0.12), 0.35), flat("PaintBlue", (0.05, 0.08, 0.3), 0.35),
              flat("PaintBone", (0.85, 0.82, 0.72), 0.35), flat("PaintGreen", (0.04, 0.15, 0.07), 0.35), flat("PaintInk", (0.02, 0.02, 0.03), 0.3)]
    set_group("Main")
    H = 5.2

    def leg_y(z):
        return -0.38 + 0.36 * z / H
    for sx in (-1, 1):
        tube(f"Leg{sx}", [(sx * 0.95, leg_y(0), 0.04), (sx * 0.28, leg_y(H), H)], 0.04, M["iron"], square=True, poly=True)
        box(f"Shoe{sx}", (0.14, 0.14, 0.05), (sx * 0.95, leg_y(0), 0.025), M["iron"], bevel=0.01)
    tube("BackLeg", [(0, 1.35, 0.04), (0, 0.02, H - 0.25)], 0.035, M["iron"], square=True, poly=True)
    tube("Hinge", [(-0.32, leg_y(H - 0.25), H - 0.25), (0.32, leg_y(H - 0.25), H - 0.25)], 0.03, M["iron"], poly=True)
    sphere("HingeKnob", 0.06, (0, leg_y(H - 0.25) + 0.04, H - 0.25), M["brass"], seg=10, rings=5)
    for z, w in ((0.7, 0.86), (1.6, 0.74)):
        tube(f"Rung{z}", [(-w, leg_y(z), z), (w, leg_y(z), z)], 0.025, M["iron"], square=True, poly=True)
    tube("Stay", [(0, leg_y(0.7), 0.7), (0, 0.85, 1.6)], 0.02, M["iron"], poly=True)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.05, (sx * 0.28, leg_y(H), H + 0.03), M["brass"], seg=10, rings=5)
    # the ledge tray and the canvas leaning on it, the top clamp
    zt = 1.82
    box("Tray", (2.3, 0.34, 0.05), (0, leg_y(zt) - 0.14, zt), M["iron"], bevel=0.012)
    box("TrayLip", (2.3, 0.03, 0.09), (0, leg_y(zt) - 0.3, zt + 0.04), M["brass"], bevel=0.008)
    CW, CH = 2.0, 2.6
    tilt = math.atan2(0.36, H)
    cz = zt + 0.03 + CH / 2 * math.cos(tilt)
    cy = leg_y(cz) - 0.1
    box("Canvas", (CW, 0.06, CH), (0, cy, cz), painting_mat(CH, (0.55, 0.72, 0.18)), bevel=0.0, segments=1, rot=(-tilt, 0, 0))
    for sx in (-1, 1):
        box(f"Stretcher{sx}", (0.05, 0.08, CH), (sx * (CW / 2 + 0.02), cy + 0.02, cz), M["oakdark"], bevel=0.008, rot=(-tilt, 0, 0))
    # the painting in progress: a far hill, a chapel on a rise and a dead tree, in low relief on the canvas
    sil = flat("PaintSilhouette", (0.014, 0.012, 0.02), 0.6)
    far = flat("PaintHill", (0.05, 0.045, 0.08), 0.6)
    s = _mark()
    xs = [-CW / 2 + 0.02 + i * (CW - 0.04) / 16 for i in range(17)]
    relief("PaintFar", [(x, -0.62 + 0.12 * math.sin(2.1 * x + 0.4)) for x in xs] + [(xs[-1], -1.28), (xs[0], -1.28)], 0.0, 0.006, far)
    relief("PaintNear", [(x, -0.92 + 0.1 * math.sin(2.7 * x + 1.9)) for x in xs] + [(xs[-1], -1.28), (xs[0], -1.28)], -0.004, 0.006, sil)
    relief("PaintChapel", [(-0.5, -0.9), (-0.1, -0.9), (-0.1, -0.62), (-0.3, -0.48), (-0.5, -0.62)], -0.008, 0.006, sil)
    relief("PaintSpire", [(-0.08, -0.9), (0.04, -0.9), (0.04, -0.5), (-0.02, -0.22), (-0.08, -0.5)], -0.008, 0.006, sil)
    for k, x in enumerate((-0.42, -0.3, -0.18)):
        relief(f"PaintWin{k}", [(x - 0.02, -0.82), (x + 0.02, -0.82), (x + 0.02, -0.74), (x - 0.02, -0.74)], -0.012, 0.004, M["paper"])
    tube("PaintTree", [(0.62, -0.012, -0.95), (0.66, -0.012, -0.6), (0.58, -0.012, -0.3)], 0.018, sil)
    tube("PaintBranch", [(0.65, -0.012, -0.62), (0.82, -0.012, -0.45)], 0.01, sil)
    _xform(s, Matrix.Translation((0, cy - 0.034, cz)) @ Matrix.Rotation(-tilt, 4, "X"))
    ztop = zt + 0.03 + CH * math.cos(tilt)
    box("Clamp", (0.5, 0.18, 0.1), (0, leg_y(ztop) - 0.06, ztop + 0.03), M["iron"], bevel=0.015)
    cyl("ClampKnob", 0.05, 0.08, (0.3, leg_y(ztop) - 0.08, ztop + 0.03), M["brass"], rot=(0, math.pi / 2, 0), verts=12)
    # a palette of paint hung on a peg on the left leg
    s = _mark()
    pal = []
    for i in range(26):
        a = i / 26 * 2 * math.pi
        r = 1.0 - 0.32 * math.exp(-((a - math.pi * 1.15) ** 2) / 0.08)        # the thumb notch
        pal.append((math.cos(a) * 0.46 * r, math.sin(a) * 0.33 * r))
    relief("Palette", pal, 0.0, 0.025, M["oak"], plane="XZ", bevel=0.006)
    cyl("ThumbHole", 0.05, 0.03, (-0.22, -0.002, -0.12), M["iron"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0)
    rnd = random.Random(9)
    for k, (x, z) in enumerate(((0.28, 0.12), (0.14, 0.22), (-0.04, 0.24), (-0.22, 0.16), (0.32, -0.06), (0.18, -0.18))):
        sphere(f"Dab{k}", 0.065, (x, -0.02, z), paints[k], seg=10, rings=5, scale=(1.1 + rnd.uniform(-0.2, 0.2), 0.3, 0.9))
    _xform(s, Matrix.Translation((-1.06, leg_y(1.3) - 0.08, 1.3)) @ Matrix.Rotation(math.radians(-14), 4, "Y"))
    tube("Peg", [(-0.86, leg_y(1.5), 1.5), (-0.9, leg_y(1.5) - 0.12, 1.52)], 0.018, M["brass"], poly=True)
    # brushes standing in a glass jar on the tray
    jx, jy = 0.8, leg_y(zt) - 0.14
    for k in range(5):
        a = k / 5 * 2 * math.pi
        top = Vector((jx + math.cos(a) * 0.1, jy + math.sin(a) * 0.06, zt + 0.5 + k * 0.03))
        bot = Vector((jx + math.cos(a) * 0.02, jy + math.sin(a) * 0.02, zt + 0.06))
        tube(f"Brush{k}", [tuple(bot), tuple(top)], 0.012, M["oakdark"], poly=True)
        d = (top - bot).normalized()
        cone(f"Bristle{k}", 0.018, 0.004, 0.08, tuple(top + d * 0.04), paints[k], verts=8, rot=tuple(_aim(d).to_euler()))
        hoop(f"Ferrule{k}", tuple(top), 0.016, "Z", M["brass"], thick=0.006)
    set_group("Glass")
    lathe("Jar", [(0, zt + 0.025), (0.11, zt + 0.025), (0.12, zt + 0.06), (0.12, zt + 0.27), (0.13, zt + 0.29), (0.115, zt + 0.29),
                  (0.105, zt + 0.27), (0.105, zt + 0.06), (0, zt + 0.045)], M["glassclear"], seg=20, loc=(jx, jy, 0))
    set_group("Main")
    return _dims()


# ================================================================== gramophone
def gramophone(M):
    bone, ink = bone_ink()
    felt = flat("Felt", (0.12, 0.012, 0.018), 0.95)
    groove = flat("Groove", (0.06, 0.06, 0.07), 0.15)
    cz0, ch = 0.12, 0.75
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Foot{sx}{sy}", 0.07, (sx * 0.55, sy * 0.55, 0.07), M["brass"], seg=10, rings=5)
            box(f"Corner{sx}{sy}", (0.07, 0.07, ch + 0.02), (sx * 0.64, sy * 0.64, cz0 + ch / 2), M["brass"], bevel=0.012)
    box("Cabinet", (1.3, 1.3, ch), (0, 0, cz0 + ch / 2), M["crimson"], bevel=0.02)
    box("Lid", (1.38, 1.38, 0.06), (0, 0, cz0 + ch + 0.03), ink, bevel=0.015)
    box("Base", (1.36, 1.36, 0.05), (0, 0, cz0 + 0.025), ink, bevel=0.012)
    _quatrefoil("Seal", 0, -0.67, cz0 + ch / 2, 0.16, M["brass"])
    tube("Panel", [(-0.5, -0.66, cz0 + 0.1), (0.5, -0.66, cz0 + 0.1), (0.5, -0.66, cz0 + ch - 0.1), (-0.5, -0.66, cz0 + ch - 0.1)], 0.018, M["brass"],
         closed=True, square=True, poly=True)
    # the crank on the right side
    tube("CrankShaft", [(0.65, 0.1, cz0 + 0.45), (0.8, 0.1, cz0 + 0.45)], 0.025, M["brass"], poly=True)
    tube("CrankArm", [(0.8, 0.1, cz0 + 0.45), (0.82, 0.1, cz0 + 0.22)], 0.02, M["brass"], poly=True)
    cyl("CrankKnob", 0.035, 0.12, (0.88, 0.1, cz0 + 0.22), ink, rot=(0, math.pi / 2, 0), verts=12)
    # the platter and the record
    zt = cz0 + ch + 0.06
    # the platter and record turn together on the spindle (their own piece, origin on the spindle)
    set_group("Record", hinge=(0, 0, zt + 0.02), swing=1)
    cyl("Platter", 0.52, 0.04, (0, 0, zt + 0.02), M["brass"], verts=40, bevel=0.008)
    cyl("Mat", 0.5, 0.01, (0, 0, zt + 0.045), felt, verts=40, bevel=0)
    cyl("Record", 0.47, 0.012, (0, 0, zt + 0.056), ink, verts=48, bevel=0.002)
    for r in (0.24, 0.31, 0.38, 0.44):
        hoop(f"Groove{r}", (0, 0, zt + 0.063), r, "Z", groove, thick=0.003)
    cyl("Label", 0.14, 0.004, (0, 0, zt + 0.064), M["crimson"], verts=24, bevel=0)
    box("LabelMark", (0.05, 0.09, 0.004), (0.085, 0, zt + 0.067), M["brass"], bevel=0.0, segments=1)   # shows the spin
    cyl("Spindle", 0.012, 0.05, (0, 0, zt + 0.08), M["brass"], verts=8, bevel=0)
    set_group("Main")
    # the tonearm and sound box
    px, py = 0.5, 0.5
    cyl("ArmBase", 0.09, 0.1, (px, py, zt + 0.05), M["brass"], verts=16, bevel=0.012)
    tube("Tonearm", [(px, py, zt + 0.12), (0.36, 0.25, zt + 0.15), (0.2, 0.02, zt + 0.14)], 0.026, M["brass"])
    cyl("SoundBox", 0.095, 0.045, (0.17, -0.02, zt + 0.14), M["brass"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.01)
    cyl("Diaphragm", 0.07, 0.05, (0.17, -0.02, zt + 0.14), bone, rot=(0, math.pi / 2, 0), verts=20, bevel=0)
    cone("Needle", 0.008, 0.0, 0.06, (0.17, -0.04, zt + 0.085), M["iron"], verts=6, rot=(math.pi, 0, 0))
    # the horn: an elbow rising from the arm base, a fluted brass flower
    tube("Elbow", [(px, py, zt + 0.1), (0.5, 0.58, zt + 0.35), (0.38, 0.55, zt + 0.62)], 0.065, M["brass"])
    s = _mark()
    outer = [(0.07, 0.0), (0.09, 0.35), (0.13, 0.7), (0.22, 0.98), (0.38, 1.18), (0.58, 1.3), (0.72, 1.34)]
    inner = [(r - 0.022, z) for r, z in reversed(outer)]
    lathe("Horn", outer + [(0.73, 1.36)] + inner, M["brass"], seg=48, flute=(8, 0.07))
    lathe("HornInside", [(r - 0.028, z) for r, z in outer[2:]], M["crimson"], seg=48, flute=(8, 0.07))
    _xform(s, Matrix.Translation((0.38, 0.55, zt + 0.6)) @ _aim((-0.32, -0.72, 0.62)))
    return _dims()


# ================================================================== telescope
def telescope(M):
    set_group("Main")
    hub = 2.55
    for k in range(3):
        a = math.radians(270 + k * 120)
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.12, s_ * 0.12, hub), (c * 1.05, s_ * 1.05, 0.06)], 0.045, M["iron"], square=True, poly=True)
        sphere(f"Toe{k}", 0.07, (c * 1.06, s_ * 1.06, 0.06), M["brass"], seg=10, rings=5)
    pts = []
    for k in range(3):
        a = math.radians(270 + k * 120)
        r = 0.12 + (hub - 1.05) / (hub - 0.06) * (1.05 - 0.12)
        pts.append((math.cos(a) * r, math.sin(a) * r, 1.05))
    tube("Spreader", pts, 0.025, M["brass"], closed=True, poly=True)
    cyl("Hub", 0.2, 0.18, (0, 0, hub), M["brass"], verts=24, bevel=0.02)
    cyl("Turntable", 0.16, 0.1, (0, 0, hub + 0.14), M["iron"], verts=20, bevel=0.015)
    za = hub + 0.55
    for sx in (-1, 1):
        tube(f"Yoke{sx}", [(0, 0, hub + 0.18), (sx * 0.28, 0, hub + 0.24), (sx * 0.28, 0, za)], 0.035, M["iron"], square=True)
        cyl(f"Trunnion{sx}", 0.07, 0.08, (sx * 0.3, 0, za), M["brass"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
    # the brass tube, eyepiece toward the back, tilted 35 degrees to the sky
    s = _mark()
    prof = [(0, -1.78), (0.035, -1.78), (0.035, -1.62), (0.065, -1.6), (0.065, -1.46), (0.11, -1.43), (0.11, -1.3), (0.15, -1.27),
            (0.15, 1.12), (0.172, 1.14), (0.172, 1.22), (0.19, 1.24), (0.19, 1.66), (0.172, 1.68), (0.172, 1.52), (0, 1.52)]
    lathe("Tube", prof, M["brass"], seg=36)
    for z in (-0.62, 0.32):
        hoop(f"Band{z}", (0, 0, z), 0.152, "Z", M["iron"], thick=0.02)
    hoop("Cradle", (0, 0, 0.0), 0.16, "Z", M["iron"], thick=0.035)
    for sx in (-1, 1):
        cyl(f"FocusKnob{sx}", 0.05, 0.06, (sx * 0.13, 0, -1.37), M["iron"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.008)
    for z in (-0.3, 0.3):
        tube(f"FinderPost{z}", [(0, 0.15, z), (0, 0.25, z)], 0.015, M["brass"], poly=True)
    lathe("Finder", [(0, -0.45), (0.035, -0.45), (0.035, 0.42), (0.045, 0.44), (0.045, 0.52), (0.035, 0.52), (0, 0.48)], M["brass"], seg=16,
          loc=(0, 0.27, 0))
    set_group("Glass")
    cyl("Lens", 0.17, 0.02, (0, 0, 1.53), M["glassclear"], verts=32, bevel=0)
    set_group("Main")
    el = math.radians(35)
    _xform(s, Matrix.Translation((0, 0, za)) @ _aim((0, -math.cos(el), math.sin(el))))
    return _dims()


# ================================================================== filing cabinet
def filing_cabinet(M):
    W, D, H = 1.7, 2.0, 4.4
    inkline = flat("InkLine", (0.03, 0.03, 0.05), 0.5)
    ink_folder = flat("Folder", (0.32, 0.22, 0.12), 0.7)
    set_group("Main")
    box("Plinth", (W + 0.12, D + 0.12, 0.25), (0, 0, 0.125), M["iron"], bevel=0.03)
    box("Carcass", (W, D, H - 0.25), (0, 0, 0.25 + (H - 0.25) / 2), M["iron"], bevel=0.025)
    box("Cap", (W + 0.14, D + 0.14, 0.12), (0, 0, H + 0.06), M["iron"], bevel=0.03)
    box("CapBead", (W + 0.16, 0.03, 0.04), (0, -D / 2 - 0.07, H + 0.0), M["brass"], bevel=0.008)
    _gable("Crest", 0, -D / 2 + 0.05, 0.5, H + 0.12, H + 0.48, 0.08, M["iron"], M["brass"], edge=0.025)
    _quatrefoil("CrestSeal", 0, -D / 2 - 0.0, H + 0.26, 0.08, M["brass"])
    z0, z1 = 0.35, H - 0.1
    dh = (z1 - z0) / 4
    y = -D / 2
    for i in range(4):
        zc = z0 + dh * (i + 0.5)
        if i == 3:
            # the top drawer slides out (its own piece): a front and a tray of folders behind it
            set_group("Drawer0")
            tray_d = D - 0.4
            box("DrawerTray", (W - 0.3, tray_d, dh - 0.22), (0, y + tray_d / 2 + 0.02, zc - 0.03), M["iron"], bevel=0.012)
            for k in range(9):
                box(f"Folder{k}", (W - 0.42, 0.03, dh - 0.3 + (0.05 if k % 3 == 0 else 0)), (0, y + 0.2 + k * 0.13, zc + 0.02), M["paper"] if k % 2 else ink_folder,
                    bevel=0.004)
        box(f"Drawer{i}", (W - 0.16, 0.06, dh - 0.08), (0, y - 0.02, zc), M["iron"], bevel=0.02)
        tube(f"DrawerPanel{i}", [(-W / 2 + 0.2, y - 0.055, zc - dh / 2 + 0.14), (W / 2 - 0.2, y - 0.055, zc - dh / 2 + 0.14),
                                 (W / 2 - 0.2, y - 0.055, zc + dh / 2 - 0.14), (-W / 2 + 0.2, y - 0.055, zc + dh / 2 - 0.14)],
             0.018, M["iron"], closed=True, square=True, poly=True)
        lz = zc + 0.18
        for name, size, loc in (("LabelT", (0.46, 0.025, 0.03), (0, y - 0.07, lz + 0.12)), ("LabelB", (0.46, 0.025, 0.03), (0, y - 0.07, lz - 0.12)),
                                ("LabelL", (0.03, 0.025, 0.27), (-0.215, y - 0.07, lz)), ("LabelR", (0.03, 0.025, 0.27), (0.215, y - 0.07, lz))):
            box(f"{name}{i}", size, loc, M["brass"], bevel=0.006)
        box(f"Card{i}", (0.4, 0.01, 0.21), (0, y - 0.062, lz), M["paper"], bevel=0.0, segments=1)
        for k in range(3):
            box(f"Ink{i}{k}", (0.26 - k * 0.06, 0.004, 0.012), (-0.02 * k, y - 0.069, lz + 0.05 - k * 0.045), inkline, bevel=0.0, segments=1)
        pz = zc - 0.12
        box(f"PullPlate{i}", (0.42, 0.02, 0.14), (0, y - 0.06, pz), M["brass"], bevel=0.01)
        tube(f"Pull{i}", [(-0.16, y - 0.07, pz + 0.04), (-0.12, y - 0.14, pz - 0.03), (0.12, y - 0.14, pz - 0.03), (0.16, y - 0.07, pz + 0.04)],
             0.022, M["brass"], square=True)
        set_group("Main")
    for sx in (-1, 1):
        tube(f"SideArch{sx}", _arch_loop_x(sx * (W / 2 + 0.01), 0, 0.68, 0.7, 2.9, 3.9), 0.03, M["iron"], square=True, closed=True, poly=True)
        q = _mark()
        _quatrefoil(f"SideSeal{sx}", 0, 0, 0, 0.14, M["brass"])
        _xform(q, Matrix.Translation((sx * (W / 2 + 0.025), 0, 3.25)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        for k in range(9):
            z = 0.4 + k * (H - 0.6) / 8
            sphere(f"Rivet{sx}{k}", 0.025, (sx * (W / 2 - 0.05), -D / 2 - 0.005, z), M["brass"], seg=6, rings=3)
    return _dims()


# ================================================================== typewriter
def typewriter(M):
    bone, ink = bone_ink()
    enamel = flat("BlackEnamel", (0.018, 0.017, 0.02), 0.16, wear=0.08, dirt=0.5)
    rubber = flat("Platen", (0.03, 0.03, 0.03), 0.7)
    typed = flat("Typed", (0.04, 0.04, 0.06), 0.6)
    W = 1.22
    box("BasePlate", (1.28, 1.1, 0.05), (0, 0, 0.025), M["iron"], bevel=0.012)
    side = [(-0.55, 0.05), (0.45, 0.05), (0.45, 0.42), (0.3, 0.5), (0.05, 0.47), (-0.45, 0.17), (-0.55, 0.11)]
    relief("Body", side, 0.0, W, enamel, plane="YZ", bevel=0.02)
    for sx in (-1, 1):
        tube(f"Pinstripe{sx}", [(sx * (W / 2 + 0.004), y * 0.92, 0.05 + (z - 0.05) * 0.9) for y, z in side], 0.007, M["brass"],
             closed=True, square=True, poly=True)
    box("Decal", (0.42, 0.012, 0.06), (0, -0.552, 0.085), M["brass"], bevel=0.004)

    def slope_z(y):
        return 0.17 + (y + 0.45) * 0.6
    # four staggered rows of round keys on the slope
    for row, (y, n, off) in enumerate(((-0.4, 10, 0.0), (-0.3, 11, 0.03), (-0.2, 11, -0.02), (-0.1, 10, 0.02))):
        for k in range(n):
            x = (k - (n - 1) / 2) * 0.1 + off
            z = slope_z(y)
            tube(f"Stem{row}{k}", [(x, y + 0.02, z - 0.02), (x, y, z + 0.06)], 0.01, M["iron"], poly=True)
            cyl(f"KeyRim{row}{k}", 0.04, 0.012, (x, y, z + 0.06), M["brass"], verts=12, bevel=0)
            cyl(f"Key{row}{k}", 0.034, 0.014, (x, y, z + 0.07), bone, verts=12, bevel=0.003)
    box("SpaceBar", (0.6, 0.045, 0.026), (0, -0.5, slope_z(-0.5) + 0.04), bone, bevel=0.006)
    for sx in (-1, 1):
        tube(f"SpaceArm{sx}", [(sx * 0.28, -0.48, slope_z(-0.5) + 0.03), (sx * 0.28, -0.38, slope_z(-0.4))], 0.008, M["iron"], poly=True)
    # ribbon spools, the carriage, the platen and the paper
    for sx in (-1, 1):
        cyl(f"Spool{sx}", 0.085, 0.035, (sx * 0.36, 0.18, 0.49), M["brass"], verts=20, bevel=0.006)
        cyl(f"Ribbon{sx}", 0.06, 0.04, (sx * 0.36, 0.18, 0.49), M["crimson"], verts=16, bevel=0)
    box("Carriage", (1.52, 0.16, 0.06), (0, 0.42, 0.5), M["iron"], bevel=0.012)
    cyl("PlatenRoll", 0.085, 1.32, (0, 0.34, 0.6), rubber, rot=(0, math.pi / 2, 0), verts=24, bevel=0.01)
    for sx in (-1, 1):
        cyl(f"Knob{sx}", 0.075, 0.06, (sx * 0.7, 0.34, 0.6), M["brass"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.012)
    tube("Bail", [(-0.62, 0.26, 0.63), (0.62, 0.26, 0.63)], 0.008, M["brass"], poly=True)
    tube("ReturnLever", [(-0.68, 0.3, 0.62), (-0.76, 0.12, 0.7), (-0.82, -0.02, 0.74)], 0.018, M["brass"])
    sphere("LeverKnob", 0.035, (-0.82, -0.03, 0.74), ink, seg=10, rings=5)
    pt = math.radians(10)
    box("Paper", (0.85, 0.006, 0.9), (0, 0.42 + 0.45 * math.sin(pt), 0.6 + 0.45 * math.cos(pt)), M["paper"], bevel=0.0, segments=1, rot=(-pt, 0, 0))
    box("PaperFront", (0.85, 0.006, 0.12), (0, 0.255, 0.6), M["paper"], bevel=0.0, segments=1)
    rnd = random.Random(14)
    for k in range(9):
        z = 0.95 - k * 0.07
        ln = rnd.uniform(0.35, 0.68) if k % 4 else 0.25
        box(f"Line{k}", (ln, 0.003, 0.012), (-0.36 + ln / 2, 0.42 + (z - 0.6) * math.tan(pt) - 0.006, z), typed, bevel=0.0, segments=1, rot=(-pt, 0, 0))
    return _dims()


# ================================================================== tea trolley
def tea_trolley(M):
    porcelain = flat("Porcelain", (0.82, 0.8, 0.74), 0.08, wear=0.02, dirt=0.6)
    tea = flat("Tea", (0.12, 0.05, 0.02), 0.05)
    sponge = flat("Sponge", (0.55, 0.36, 0.16), 0.7)
    stone = marble("Marble")
    rubber = flat("Rubber", (0.03, 0.03, 0.03), 0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 1.0, sy * 0.5
            tube(f"Leg{sx}{sy}", [(x, y, 0.3), (x, y, 2.32)], 0.035, M["iron"], square=True, poly=True)
            tube(f"Fork{sx}{sy}", [(x, y, 0.32), (x, y, 0.2)], 0.025, M["iron"], poly=True)
            cyl(f"Castor{sx}{sy}", 0.15, 0.07, (x, y, 0.15), rubber, rot=(0, math.pi / 2, 0), verts=20, bevel=0.012)
            cyl(f"Hub{sx}{sy}", 0.06, 0.09, (x, y, 0.15), M["brass"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.008)
            sphere(f"LegTop{sx}{sy}", 0.05, (x, y, 2.34), M["brass"], seg=10, rings=5)
    z1, z2 = 0.9, 2.2
    for name, z in (("Lower", z1), ("Upper", z2)):
        prism(f"{name}Tray", [(x, y) for x, y, _ in rrect(1.06, 0.56, 0.1, 0)], z, 0.06, stone, plane="XY", bevel=0.01)
        tube(f"{name}Frame", rrect(1.07, 0.57, 0.1, z), 0.025, M["iron"], closed=True, square=True, poly=True)
    tube("Gallery", rrect(1.05, 0.55, 0.1, z2 + 0.17), 0.016, M["brass"], closed=True, poly=True)
    pts = rrect(1.05, 0.55, 0.1, 0)
    for k in range(14):
        p = pts[int(k / 14 * len(pts))]
        tube(f"Baluster{k}", [(p[0], p[1], z2 + 0.06), (p[0], p[1], z2 + 0.17)], 0.008, M["brass"], poly=True)
    tube("Handle", [(1.0, -0.5, 2.3), (1.18, -0.46, 2.55), (1.26, -0.3, 2.72), (1.26, 0.3, 2.72), (1.18, 0.46, 2.55), (1.0, 0.5, 2.3)], 0.035, M["brass"])
    # the tea service on the top tier
    T = z2 + 0.06
    tx = -0.5
    lathe("Teapot", [(0, T), (0.17, T), (0.2, T + 0.03), (0.27, T + 0.12), (0.29, T + 0.22), (0.26, T + 0.32), (0.18, T + 0.38), (0.12, T + 0.4),
                     (0, T + 0.4)], porcelain, seg=32, loc=(tx, 0, 0))
    lathe("TeapotLid", [(0, T + 0.38), (0.13, T + 0.38), (0.1, T + 0.43), (0.03, T + 0.45), (0.045, T + 0.49), (0.03, T + 0.52), (0, T + 0.52)],
          porcelain, seg=24, loc=(tx, 0, 0))
    hoop("TeapotBand", (tx, 0, T + 0.22), 0.292, "Z", M["crimson"], thick=0.012)
    hoop("TeapotRim", (tx, 0, T + 0.385), 0.132, "Z", M["brass"], thick=0.01)
    tube("Spout", [(tx + 0.24, 0, T + 0.14), (tx + 0.36, 0, T + 0.2), (tx + 0.44, 0, T + 0.34), (tx + 0.5, 0, T + 0.38)], 0.032, porcelain)
    tube("TeapotHandle", [(tx - 0.24, 0, T + 0.32), (tx - 0.36, 0, T + 0.3), (tx - 0.38, 0, T + 0.18), (tx - 0.26, 0, T + 0.1)], 0.025, porcelain)
    for k, (x, y) in enumerate(((0.12, -0.28), (0.45, -0.22), (0.32, 0.24))):
        lathe(f"Saucer{k}", [(0, T), (0.12, T), (0.15, T + 0.02), (0.16, T + 0.03), (0.14, T + 0.03), (0, T + 0.015)], porcelain, seg=24, loc=(x, y, 0))
        lathe(f"Cup{k}", [(0, T + 0.02), (0.055, T + 0.02), (0.08, T + 0.05), (0.1, T + 0.14), (0.095, T + 0.145), (0.085, T + 0.14), (0.072, T + 0.06),
                          (0, T + 0.05)], porcelain, seg=24, loc=(x, y, 0))
        hoop(f"CupBand{k}", (x, y, T + 0.12), 0.098, "Z", M["crimson"], thick=0.006)
        hoop(f"CupHandle{k}", (x + 0.12, y, T + 0.1), 0.035, "Y", porcelain, thick=0.009)
        if k != 2:
            cyl(f"Tea{k}", 0.08, 0.006, (x, y, T + 0.12), tea, verts=16, bevel=0)
    lathe("MilkJug", [(0, T), (0.07, T), (0.085, T + 0.06), (0.07, T + 0.14), (0.08, T + 0.18), (0.07, T + 0.18), (0.06, T + 0.14), (0, T + 0.13)],
          porcelain, seg=20, loc=(0.72, 0.12, 0))
    hoop("JugHandle", (0.81, 0.12, T + 0.1), 0.04, "Y", porcelain, thick=0.009)
    lathe("SugarBowl", [(0, T), (0.08, T), (0.11, T + 0.05), (0.11, T + 0.11), (0.09, T + 0.13), (0.05, T + 0.15), (0.03, T + 0.18), (0, T + 0.18)],
          porcelain, seg=20, loc=(-0.05, 0.3, 0))
    # a three-tier cake stand and a stack of plates below
    B = z1 + 0.06
    cx = -0.4
    tube("StandRod", [(cx, 0, B + 0.02), (cx, 0, B + 0.85)], 0.018, M["brass"], poly=True)
    sphere("StandFinial", 0.04, (cx, 0, B + 0.88), M["brass"], seg=10, rings=5)
    for k, (z, r) in enumerate(((B + 0.02, 0.34), (B + 0.34, 0.26), (B + 0.62, 0.18))):
        lathe(f"Plate{k}", [(0, z), (r - 0.05, z), (r, z + 0.035), (r - 0.015, z + 0.04), (0, z + 0.015)], porcelain, seg=32, loc=(cx, 0, 0))
        hoop(f"PlateRim{k}", (cx, 0, z + 0.036), r - 0.01, "Z", M["brass"], thick=0.006)
        n = 6 - 2 * k
        for i in range(n):
            a = i / n * 2 * math.pi + k
            px, py = cx + math.cos(a) * (r - 0.11), math.sin(a) * (r - 0.11)
            cyl(f"Cake{k}{i}", 0.05, 0.05, (px, py, z + 0.045), sponge, verts=12, bevel=0.008)
            cyl(f"Icing{k}{i}", 0.052, 0.016, (px, py, z + 0.075), M["crimson"] if (i + k) % 2 else porcelain, verts=12, bevel=0.006)
    for k in range(5):
        lathe(f"StackPlate{k}", [(0, B + k * 0.035), (0.2, B + k * 0.035), (0.24, B + k * 0.035 + 0.03), (0.22, B + k * 0.035 + 0.033),
                                 (0, B + k * 0.035 + 0.012)], porcelain, seg=28, loc=(0.45, 0.05, 0))
    box("Napkins", (0.3, 0.3, 0.06), (0.5, -0.32, B + 0.03), M["crimson"], bevel=0.015)
    return _dims()


# ================================================================== pigeonholes
def pigeonholes(M):
    W, H, D = 3.6, 3.1, 0.9
    yf = -D
    NC, NR = 6, 4
    box("Back", (W, 0.06, H), (0, -0.03, H / 2), M["iron"], bevel=0.01)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.08, D, H), (sx * (W / 2 - 0.04), -D / 2, H / 2), M["iron"], bevel=0.015)
    box("Bottom", (W, D, 0.1), (0, -D / 2, 0.05), M["iron"], bevel=0.015)
    box("Cornice", (W + 0.2, D + 0.12, 0.14), (0, -D / 2 - 0.03, H + 0.07), M["iron"], bevel=0.03)
    box("CorniceBead", (W + 0.22, 0.03, 0.04), (0, yf - 0.1, H + 0.0), M["brass"], bevel=0.008)
    _gable("Crest", 0, yf + 0.06, 0.6, H + 0.14, H + 0.62, 0.08, M["iron"], M["brass"], edge=0.025)
    _quatrefoil("CrestSeal", 0, yf - 0.0, H + 0.34, 0.1, M["brass"])
    iw = W - 0.16
    cw = iw / NC
    z0, rh = 0.1, (H - 0.1) / NR
    for c in range(1, NC):
        x = -iw / 2 + c * cw
        box(f"Divider{c}", (0.03, D - 0.04, H - 0.1), (x, -D / 2 - 0.02, z0 + (H - 0.1) / 2), M["iron"], bevel=0.005)
    for r in range(1, NR):
        box(f"Shelf{r}", (iw, D - 0.04, 0.03), (0, -D / 2 - 0.02, z0 + r * rh), M["iron"], bevel=0.005)
    tube("FrontBead", [(-W / 2, yf - 0.01, 0.02), (W / 2, yf - 0.01, 0.02), (W / 2, yf - 0.01, H), (-W / 2, yf - 0.01, H)], 0.022, M["brass"],
         closed=True, square=True, poly=True)
    rnd = random.Random(21)
    paper, card = M["paper"], flat("Manila", (0.62, 0.48, 0.28), 0.7)
    wax = M["crimson"]
    for r in range(NR):
        zb = z0 + r * rh + 0.015
        for c in range(NC):
            cx = -iw / 2 + (c + 0.5) * cw
            key = f"{r}{c}"
            # the brass name plate and its card on the shelf edge
            box(f"Plate{key}", (0.3, 0.012, 0.075), (cx, yf - 0.012, zb), M["brass"], bevel=0.004)
            box(f"PlateCard{key}", (0.24, 0.006, 0.045), (cx, yf - 0.02, zb), paper, bevel=0.0, segments=1)
            kind = rnd.choice(("empty", "stack", "stack", "upright", "upright", "parcel", "scroll"))
            if kind == "stack":
                z = zb + 0.016
                for k in range(rnd.randint(2, 5)):
                    box(f"Env{key}{k}", (0.4, 0.3, 0.012), (cx + rnd.uniform(-0.03, 0.03), -0.5 + rnd.uniform(-0.04, 0.04), z), paper if k % 2 else card,
                        bevel=0.002, segments=1, rot=(0, 0, rnd.uniform(-0.12, 0.12)))
                    z += 0.014
                if rnd.random() < 0.6:
                    cyl(f"Seal{key}", 0.035, 0.012, (cx + 0.05, -0.55, z), wax, verts=10, bevel=0.003)
            elif kind == "upright":
                for k in range(rnd.randint(2, 4)):
                    lean = math.radians(rnd.uniform(6, 22))
                    h = rnd.uniform(0.24, 0.34)
                    y = -0.32 - k * 0.06
                    ly, lz = y + h / 2 * math.sin(lean), zb + h / 2 * math.cos(lean)
                    box(f"Letter{key}{k}", (0.38, 0.008, h), (cx + rnd.uniform(-0.03, 0.03), ly, lz), paper if k % 2 else card, bevel=0.0, segments=1,
                        rot=(-lean, 0, 0))
                    if k == 0 and rnd.random() < 0.7:
                        cyl(f"LSeal{key}", 0.03, 0.01, (cx, ly - 0.008 * math.cos(lean), lz + 0.008 * math.sin(lean)), wax,
                            rot=(math.pi / 2 - lean, 0, 0), verts=10, bevel=0.003)
            elif kind == "parcel":
                w, d, h = rnd.uniform(0.3, 0.42), rnd.uniform(0.3, 0.45), rnd.uniform(0.16, 0.3)
                y = -0.5
                box(f"Parcel{key}", (w, d, h), (cx, y, zb + h / 2), card, bevel=0.012)
                tube(f"StringA{key}", [(cx - w / 2 - 0.003, y, zb + 0.005), (cx - w / 2 - 0.003, y, zb + h + 0.003), (cx + w / 2 + 0.003, y, zb + h + 0.003),
                                       (cx + w / 2 + 0.003, y, zb + 0.005)], 0.006, M["brass"], poly=True)
                tube(f"StringB{key}", [(cx, y - d / 2 - 0.003, zb + 0.005), (cx, y - d / 2 - 0.003, zb + h + 0.004), (cx, y + d / 2 + 0.003, zb + h + 0.004)],
                     0.006, M["brass"], poly=True)
            elif kind == "scroll":
                for k in range(rnd.randint(1, 3)):
                    rr = 0.05
                    sxp = cx + (k - 1) * 0.12
                    sz = zb + rr + (0.09 if k == 1 else 0)
                    cyl(f"Scroll{key}{k}", rr, 0.55, (sxp, -0.45, sz), paper, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.005)
                    hoop(f"Tie{key}{k}", (sxp, -0.45, sz), rr + 0.004, "Y", wax, thick=0.007)
    return _dims()


P.PREVIEW_PAD.update({"BannerRavens": 1.05, "BannerRovers": 1.05, "BannerWardens": 1.05, "BannerVigil": 1.05, "BannerCrimson": 1.05,
                      "Telescope": 1.05, "Gramophone": 1.1, "Typewriter": 1.25})

P.BUILD.update({
    "BannerRavens": banner_ravens,
    "BannerRovers": banner_rovers,
    "BannerWardens": banner_wardens,
    "BannerVigil": banner_vigil,
    "BannerCrimson": banner_crimson,
    "ChessTable": chess_table,
    "ArtEasel": art_easel,
    "Gramophone": gramophone,
    "Telescope": telescope,
    "FilingCabinet": filing_cabinet,
    "Typewriter": typewriter,
    "TeaTrolley": tea_trolley,
    "Pigeonholes": pigeonholes,
})
