"""Props batch 37, the detention kit (Room 106) for nh_props.py. Strict and grim, never violent: no canes, no shackles.

The detention room
  DetentionDesk        a lone, heavy desk and seat on one cast-iron frame bolted to a floor plate; initials and scratches carved
                       into its ebonised oak top (desk top 2.45, seat top 1.7)
  LinesChalkboard      a wall chalkboard filled with "I will not talk in class." in chalk (kits3739_atlas.py), chalk and eraser
  LinesPaperStack      a stack of lined pages written full of lines, a worn pencil
  SupervisorPodium     a raised supervisor's desk on a low oak platform, a brass desk lamp (Glow: the bulb) and a service bell
  DetentionLog         the detention register open on a slanted iron stand, a pen on a chain
  ConfiscatedBox       a crate stencilled CONFISCATED: a slingshot, two phones, three comics, playing cards, a skateboard wheel
  SchoolRulesBoard     the rules of the school, printed under the crest, in a gilt frame with a wax seal
  DetentionSign        a door sign: DETENTION, and under it SILENCE
  FacingWallDesk       a desk boxed in by tall side panels, to face the wall
  WindowGrille         a cast-iron window grille, spear finials and a quatrefoil band (wall-mounted)
  KeyRingHook          a warden's ring of big keys on a wall hook
  WallBell             an electric school bell: a red dome, brass works, on a wall plate
Student desk variants (built on nh_props.student_desk: the same size, frame, heights and footprint as StudentDesk)
  StudentDeskCarved, StudentDeskGraffiti, StudentDeskBroken, StudentDeskWobbly, StudentDeskInkStained
  StudentDeskPrank<Id>  a clique's prank: its slogan in marker over a carving, and its emblem (ReplicatedStorage.Config.Cliques)

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: on the wall plane, y = 0). Registered into
nh_props.BUILD on import. Shared helpers here are used by batches 38 and 39.
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
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _solid
from nh_props_batch9 import foil, wax_mat
from nh_props_batch10 import gilt
from nh_props_batch24 import _text, iron_fine, _fine, rbox
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch30 as B30
import nh_props_batch34_dorm as B34
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = "C:/Windows/Fonts/palab.ttf"
FONT_I = "C:/Windows/Fonts/palabi.ttf"
FONT_HAND = "C:/Windows/Fonts/Inkfree.ttf"
FONT_PRINT = "C:/Windows/Fonts/segoeprb.ttf"

KA = json.load(open(os.path.join(P.HERE, "kits3739_atlas.json")))
for _atlas, _pre in (("DetentionPrint", "K7_"), ("ElectivesPrint", "K8_"), ("DormHousePrint", "K9_")):
    for _k, _v in KA["regions"][_atlas].items():
        B30.REG[_pre + _k] = _v
        if _k.startswith("Swatch_"):
            B30.REG["Swatch_" + _pre + _k[7:]] = _v
TOOLS = KA["tools"]


# ------------------------------------------------------------------ materials

def lin(hexstr):
    """#RRGGBB (sRGB) to a linear colour."""
    out = []
    for i in (1, 3, 5):
        c = int(hexstr[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def kit(M):
    """The dorm kit's materials (batch 34) plus the classroom woods, chalk and the three printed atlases."""
    K = B34.kit(M)
    K.update({
        "oak": M["oak"],
        "oakdark": M["oakdark"],
        "darkoak": material("DarkOak", "NH_DeskWood", tint=(0.1, 0.058, 0.034), scale=0.22, rough_add=0.06, wear=0.5),
        "slate": M["slate"],
        "chalk": M["chalk"],
        "felt": M["felt"],
        "steel": M["brasssteel"],
        "crimsonpaint": M["crimson"],
        "cut": flat("FreshCut", (0.36, 0.22, 0.11), 0.85, dirt=0.3),
        "groove": flat("Groove", (0.03, 0.02, 0.013), 0.9, dirt=0.3),
        "rubber": flat("Rubber", (0.025, 0.024, 0.026), 0.85),
        "p7": B30.atlas_mat("DetPrintMat", "DetentionPrint", rough=0.7, leather=0.05, wear=0.04, dirt=0.45),
        "p8": B30.atlas_mat("ElecPrintMat", "ElectivesPrint", rough=0.7, leather=0.05, wear=0.04, dirt=0.45),
        "p9": B30.atlas_mat("DormHousePrintMat", "DormHousePrint", rough=0.6, leather=0.03, wear=0.04, dirt=0.45),
    })
    return K


# ------------------------------------------------------------------ 2D marks on a surface (carving, ink, marker)

def mesh_obj(name, bm, mat):
    return B34.mesh_obj(name, bm, mat)


def jitter(pts, amt, seed):
    g = random.Random(seed)
    return [(x + g.uniform(-amt, amt), y + g.uniform(-amt, amt)) for x, y in pts]


def densify(pts, step=0.03, closed=False):
    pts = list(pts) + ([pts[0]] if closed else [])
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out


def ribbon(name, pts, width, mat, mtx, z=0.0012, taper=True):
    """A flat stroke along a 2D path in the surface's XY plane, `width` wide, lifted z, placed by mtx (the surface frame)."""
    pts = [Vector((p[0], p[1])) for p in pts]
    if len(pts) < 2:
        return None
    bm = bmesh.new()
    L, R = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = (b - a)
        t = t.normalized() if t.length > 1e-9 else Vector((1, 0))
        nrm = Vector((-t.y, t.x))
        w = width / 2
        if taper:
            w *= 0.55 + 0.45 * math.sin(min(1.0, (i + 0.5) / n * 1.0) * math.pi) ** 0.3
        L.append(bm.verts.new((p.x + nrm.x * w, p.y + nrm.y * w, z)))
        R.append(bm.verts.new((p.x - nrm.x * w, p.y - nrm.y * w, z)))
    for i in range(n - 1):
        bm.faces.new((R[i], R[i + 1], L[i + 1], L[i]))
    ob = mesh_obj(name, bm, mat)
    ob.matrix_world = mtx
    return ob


def fill2d(name, poly, mat, mtx, z=0.002):
    """A flat filled outline (concave is fine) in the surface plane."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in poly]
    f = bm.faces.new(vs)
    if f.normal.z < 0:
        f.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f])
    ob = mesh_obj(name, bm, mat)
    ob.matrix_world = mtx
    return ob


def carve(prefix, strokes, mtx, K, w=0.032, seed=0):
    """Knife marks: each stroke a pale cut with a dark groove down its middle."""
    for i, s in enumerate(strokes):
        pts = jitter(densify(s, 0.025), 0.004, seed + i)
        ribbon(f"{prefix}Cut{i}", pts, w, K["cut"], mtx, z=0.0008)
        ribbon(f"{prefix}Gr{i}", pts, w * 0.42, K["groove"], mtx, z=0.0016)


def surf_place(mtx, cx, cy, ang=0.0, z0=0.0):
    c, s = math.cos(ang), math.sin(ang)
    return lambda x, y, h: tuple(mtx @ Vector((cx + x * c - y * s, cy + x * s + y * c, z0 + h)))


def carve_text(name, text, mtx, K, cx, cy, fit, ang=0.0, font=FONT_PRINT, groove_bold=0.0, cut=True):
    if cut:
        _text(name + "Cut", text, font, K["cut"], surf_place(mtx, cx, cy, ang, 0.0006), fit=fit, depth=0.0012, res=2, bold=0.05 + groove_bold)
    _text(name + "Gr", text, font, K["groove"], surf_place(mtx, cx, cy, ang, 0.0014), fit=(fit[0] * 0.97, fit[1] * 0.92), depth=0.0012, res=2,
          bold=groove_bold)


def marker_text(name, text, mat, mtx, cx, cy, fit, ang=0.0, font=FONT_HAND, bold=0.035, z0=0.0035):
    _text(name, text, font, mat, surf_place(mtx, cx, cy, ang, z0), fit=fit, depth=0.0015, res=2, bold=bold)


def circle2(cx, cy, r, n=24, a0=0.0, a1=2 * math.pi, sy=1.0):
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * r * sy) for i in range(n + 1)]


def heart(cx, cy, s, n=28):
    pts = []
    for i in range(n + 1):
        t = i / n * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s / 32, cy + y * s / 32))
    return pts


def star2(cx, cy, ro, ri, n=5, rot=math.pi / 2):
    return [(cx + math.cos(rot + i * math.pi / n) * (ro if i % 2 == 0 else ri), cy + math.sin(rot + i * math.pi / n) * (ro if i % 2 == 0 else ri))
            for i in range(2 * n)]


# ------------------------------------------------------------------ the student desk and its variants

def lid_frame():
    """The StudentDesk lid's top face as a frame: x across (-1.5..1.5), y front to back (-0.78..0.78), z up off the wood."""
    return T(0, -0.21, 2.36) @ RX(9 * DEG) @ T(0, 0, 0.045)


def base_desk(M):
    dims = P.student_desk(M)
    return dims


def desk_carved(M):
    K = kit(M)
    dims = base_desk(M)
    L = lid_frame()
    # a heart with initials in it, an arrow through it
    carve("Heart", [heart(-0.85, 0.2, 0.62)], L, K, seed=1)
    carve_text("HeartIn", "J.M + E.F", L, K, -0.85, 0.2, (0.42, 0.13), ang=0.05)
    carve("Arrow", [[(-1.3, -0.05), (-0.42, 0.45)], [(-0.42, 0.45), (-0.5, 0.45)], [(-0.42, 0.45), (-0.44, 0.37)]], L, K, w=0.026, seed=3)
    # tally marks
    strokes = []
    for g_ in range(3):
        x0 = 0.55 + g_ * 0.3
        for k in range(4):
            strokes.append([(x0 + k * 0.05, 0.5), (x0 + k * 0.05 + 0.01, 0.3)])
        strokes.append([(x0 - 0.03, 0.33), (x0 + 0.2, 0.48)])
    carve("Tally", strokes, L, K, w=0.022, seed=5)
    # a crude skull
    sk = [circle2(0.25, -0.2, 0.2, 20, sy=0.95), [(0.13, -0.38), (0.13, -0.5), (0.37, -0.5), (0.37, -0.38)],
          circle2(0.17, -0.18, 0.05, 10), circle2(0.33, -0.18, 0.05, 10), [(0.25, -0.27), (0.22, -0.32), (0.28, -0.32), (0.25, -0.27)],
          [(0.19, -0.5), (0.19, -0.42)], [(0.25, -0.5), (0.25, -0.42)], [(0.31, -0.5), (0.31, -0.42)]]
    carve("Skull", sk, L, K, w=0.026, seed=7)
    carve_text("Was", "R.V. WAS HERE", L, K, 0.95, -0.15, (0.95, 0.2), ang=-0.06)
    carve_text("Ini", "T.A.", L, K, -1.2, -0.55, (0.3, 0.14), ang=0.3)
    carve_text("Yr", "'26", L, K, 1.25, -0.6, (0.22, 0.12), ang=-0.2)
    carve("Scratch", [[(-0.3, -0.62), (0.6, -0.68)], [(-0.6, 0.62), (-0.1, 0.66)], [(-1.4, 0.55), (-1.0, 0.68)]], L, K, w=0.012, seed=9)
    _fine(0.5)
    return dims


def desk_graffiti(M):
    K = kit(M)
    dims = base_desk(M)
    L = lid_frame()
    ink = flat("BallpointInk", (0.01, 0.016, 0.07), 0.35)
    black = flat("MarkerBlack", (0.012, 0.012, 0.014), 0.4)
    red = flat("MarkerRed", lin("#B4202A"), 0.4)
    # a crossed-out heart
    ribbon("Heart", jitter(densify(heart(-0.95, 0.2, 0.62), 0.02), 0.003, 1), 0.04, red, L, z=0.002)
    ribbon("HeartX1", densify([(-1.25, -0.08), (-0.65, 0.48)], 0.03), 0.05, black, L, z=0.003)
    ribbon("HeartX2", densify([(-1.25, 0.48), (-0.65, -0.08)], 0.03), 0.05, black, L, z=0.003)
    # a doodled bat
    bat = [(0.0, 0.0), (-0.1, 0.06), (-0.28, 0.04), (-0.22, -0.02), (-0.26, -0.1), (-0.14, -0.06), (0.0, -0.13), (0.14, -0.06),
           (0.26, -0.1), (0.22, -0.02), (0.28, 0.04), (0.1, 0.06)]
    bat = [(0.35 + x * 1.5, 0.35 + y * 1.5) for x, y in bat]
    fill2d("Bat", bat, black, L, z=0.002)
    fill2d("BatEarL", [(0.31, 0.43), (0.33, 0.52), (0.35, 0.44)], black, L, z=0.002)
    fill2d("BatEarR", [(0.35, 0.44), (0.37, 0.52), (0.39, 0.43)], black, L, z=0.002)
    # ballpoint scribbles: a spiral, a cube, stars, words
    sp = [(1.1 + math.cos(t) * t * 0.012, 0.35 + math.sin(t) * t * 0.012) for t in [i * 0.25 for i in range(70)]]
    ribbon("Spiral", sp, 0.014, ink, L, z=0.002, taper=False)
    cube = [[(0.8, -0.4), (1.05, -0.4), (1.05, -0.15), (0.8, -0.15), (0.8, -0.4)], [(0.9, -0.3), (1.15, -0.3), (1.15, -0.05), (0.9, -0.05), (0.9, -0.3)],
            [(0.8, -0.4), (0.9, -0.3)], [(1.05, -0.4), (1.15, -0.3)], [(1.05, -0.15), (1.15, -0.05)], [(0.8, -0.15), (0.9, -0.05)]]
    for i, c in enumerate(cube):
        ribbon(f"Cube{i}", densify(c, 0.03), 0.014, ink, L, z=0.002, taper=False)
    for i, (x, y) in enumerate(((-0.2, 0.55), (-0.05, 0.42), (1.35, -0.55))):
        ribbon(f"Star{i}", star2(x, y, 0.07, 0.03) + [star2(x, y, 0.07, 0.03)[0]], 0.012, ink, L, z=0.002, taper=False)
    marker_text("Bored", "BORED", black, L, -0.1, -0.35, (0.75, 0.24), ang=0.08, bold=0.03)
    marker_text("Sos", "SOS", red, L, -1.15, -0.5, (0.35, 0.16), ang=-0.15)
    marker_text("Hale", "Mr H. was here", ink, L, 0.5, -0.62, (0.7, 0.1), ang=0.02, font=FONT_HAND, bold=0.0)
    # gum stuck under the book shelf and the lid's front lip
    gum = [flat("GumPink", (0.6, 0.18, 0.28), 0.5), flat("GumGrey", (0.32, 0.3, 0.29), 0.6), flat("GumGreen", (0.2, 0.38, 0.22), 0.55)]
    g = random.Random(4)
    for i, (x, y, z) in enumerate(((-0.9, -0.5, 1.915), (-0.5, -0.3, 1.915), (0.3, -0.55, 1.915), (0.8, -0.2, 1.915), (1.05, -0.6, 1.915),
                                   (-0.2, -0.88, 2.24), (0.6, -0.88, 2.25))):
        r = g.uniform(0.04, 0.06)
        sphere(f"Gum{i}", r, (x, y, z - r * 0.25), gum[i % 3], seg=10, rings=6, scale=(1.2, 1.0, 0.5))
    _fine(0.5)
    return dims


def desk_broken(M):
    """The StudentDesk with its front right leg snapped off, tipped down onto that corner, its lid split, the right half hanging off
    its hinge."""
    K = kit(M)
    s0 = _mark()
    P.student_desk(M)
    parts = P.PARTS[s0:]
    W, D = 3.0, 2.0
    x, zf = W / 2 - 0.16, -D / 2 + 0.22
    # the snapped leg: keep its stub above the break, the rest lies on the floor
    for ob in list(parts):
        if ob.name in ("LegFR",) or ob.name.startswith("FootR-0.8"):
            P.PARTS.remove(ob)
            bpy.data.objects.remove(ob)
    tube("LegStub", [(x, zf + 0.02, 0.7), (x, zf + 0.02, 1.2), (x, zf, 2.25)], 0.045, K["iron"])
    tube("LegSplinter", [(x, zf + 0.02, 0.7), (x + 0.02, zf + 0.03, 0.64), (x - 0.01, zf + 0.02, 0.6)], 0.02, K["iron"], poly=True)
    lid = next(o for o in P.PARTS if o.name == "Lid")
    P.PARTS.remove(lid)
    bpy.data.objects.remove(lid)
    tilt = math.radians(9)
    lid_d = D - 0.44
    box("LidL", (1.55, lid_d, 0.09), (-0.725, -0.21, 2.36), K["oak"], bevel=0.03, rot=(tilt, 0, 0))
    Lf = lid_frame()
    carve("Split", [[(0.03, 0.75), (-0.02, 0.5), (0.03, 0.2), (-0.01, -0.1), (0.03, -0.4), (0.0, -0.75)]], Lf, K, w=0.03, seed=11)
    # the right half torn over the right side, hanging from one hinge at its outer back corner
    s1 = _mark()
    box("LidR", (1.4, lid_d, 0.09), (-0.7, 0, 0), K["oak"], bevel=0.03)
    box("Hinge", (0.16, 0.1, 0.02), (-0.06, lid_d / 2 - 0.08, 0.05), K["brass"], bevel=0.005)
    tube("Splinters", [(-1.4, -0.4, 0.0), (-1.46, -0.3, 0.02), (-1.4, -0.2, 0.0)], 0.012, K["oak"], poly=True)
    _xform(s1, T(1.5, -0.21 + lid_d / 2 * math.cos(tilt), 2.36 + lid_d / 2 * math.sin(tilt)) @ RY(-118 * DEG) @ RX(tilt) @ T(0, -lid_d / 2, 0))
    box("HingeFixed", (0.16, 0.1, 0.02), (1.4, 0.52, 2.47), K["brass"], bevel=0.005)
    # tip the whole desk over its front-left / back-right diagonal, down onto the broken corner
    a, b = Vector((-x, zf, 0.0)), Vector((x, -zf, 0.0))
    fr = Vector((x, zf, 0.7))
    best = None
    for sgn in (1, -1):
        R = T(*a) @ Matrix.Rotation(sgn * 27 * DEG, 4, (b - a).normalized()) @ T(*(-a))
        z = (R @ fr).z
        if best is None or z < best[0]:
            best = (z, R)
    _xform(s0, best[1])
    bpy.context.view_layer.update()
    lo = min((o.matrix_world @ Vector(c)).z for o in P.PARTS[s0:] for c in o.bound_box)
    _xform(s0, T(0, 0, -lo))
    # the broken-off leg on the floor
    s2 = _mark()
    tube("LegPiece", [(0, 0, 0.0), (0.02, 0, 0.5), (0.0, 0, 0.98)], 0.045, K["iron"])
    box("LegPieceFoot", (0.14, 0.34, 0.05), (0, 0, 0.0), K["iron"], bevel=0.015)
    _xform(s2, T(2.0, -1.2, 0.05) @ RZ(35 * DEG) @ RY(90 * DEG))
    _fine(0.6)
    return _dims()


def desk_wobbly(M):
    """StudentDesk at its proper height with its front left foot short, propped on a book and a folded wad of paper; scuffed."""
    K = kit(M)
    s0 = _mark()
    P.student_desk(M)
    x, zf = -1.5 + 0.16, -1.0 + 0.22
    lift = 0.15
    for ob in P.PARTS[s0:]:
        if ob.name == "LegFL":
            for v in ob.data.vertices:
                if v.co.z < 0.4:
                    v.co.z = 0.05 + lift + (v.co.z - 0.05) * (0.35 - lift) / 0.35
        if ob.name.startswith("FootL-0.8"):
            ob.location.z += lift
    # the prop under the foot: a battered book and a folded wad of paper on it
    book_cover = material("PropBook", "NH_Leather", tint=(0.05, 0.08, 0.2), scale=3.0, normal=0.4, wear=0.5)
    box("Book", (0.6, 0.85, 0.09), (x + 0.05, zf - 0.05, 0.045), book_cover, bevel=0.012, rot=(0, 0, 0.25))
    box("BookPages", (0.56, 0.8, 0.07), (x + 0.07, zf - 0.04, 0.045), B24.pages("PropPages", (0.78, 0.74, 0.64)), bevel=0.005, rot=(0, 0, 0.25))
    for k in range(3):
        box(f"Wad{k}", (0.28 - k * 0.02, 0.2, 0.018), (x, zf, 0.1 + k * 0.019), K["paper"], bevel=0.004, rot=(0.03 * k, -0.04 * k, 0.4 + 0.1 * k))
    # scuffs and chips
    L = lid_frame()
    g = random.Random(21)
    pale = flat("Scuff", (0.42, 0.3, 0.2), 0.8, dirt=0.3)
    for i in range(14):
        cx, cy = g.uniform(-1.4, 1.4), g.uniform(-0.7, 0.7)
        a = g.uniform(-0.4, 0.4)
        ln = g.uniform(0.08, 0.35)
        ribbon(f"Scuff{i}", densify([(cx, cy), (cx + math.cos(a) * ln, cy + math.sin(a) * ln)], 0.03), g.uniform(0.008, 0.02), pale, L, z=0.001)
    for i, (cx, cy) in enumerate(((-1.47, -0.75), (1.46, -0.74), (1.47, 0.6), (-0.4, -0.77))):
        fill2d(f"Chip{i}", circle2(cx, cy, 0.05, 8, sy=0.7), K["cut"], L, z=0.0012)
    _fine(0.5)
    return _dims()


def desk_inkstained(M):
    K = kit(M)
    dims = base_desk(M)
    L = lid_frame()
    ink = material("SpiltInk", base=(0.006, 0.008, 0.03), rough=0.12, wear=0.0, dirt=0.2)
    dried = material("DriedInk", base=(0.01, 0.014, 0.05), rough=0.35, wear=0.0, dirt=0.2)
    # a toppled inkwell, its pool spreading to the front edge and over it
    g = random.Random(31)
    pool = []
    for i in range(40):
        a = i / 40 * 2 * math.pi
        r = 0.32 * (1 + 0.25 * math.sin(a * 3 + 1) + 0.12 * math.sin(a * 7)) * (1.5 if -1.9 < a - math.pi < -0.6 else 1)
        pool.append((0.55 + math.cos(a) * r * 1.3, -0.25 + math.sin(a) * r))
    fill2d("Pool", pool, ink, L, z=0.0025)
    fill2d("PoolEdge", [(0.55 + (x - 0.55) * 1.08, -0.25 + (y + 0.25) * 1.08) for x, y in pool], dried, L, z=0.0015)
    # a tongue running off the front edge
    fill2d("Run", [(0.3, -0.45), (0.5, -0.45), (0.48, -0.78), (0.3, -0.78)], ink, L, z=0.0025)
    s = _mark()
    lathe("Inkwell", [(0, 0), (0.09, 0), (0.1, 0.02), (0.1, 0.09), (0.065, 0.12), (0.035, 0.13), (0.035, 0.16), (0, 0.16)], K["brassf"], seg=18)
    hoop("InkLip", (0, 0, 0.155), 0.04, "Z", K["ink"], thick=0.008)
    _xform(s, L @ T(0.95, 0.0, 0.1) @ RZ(-150 * DEG) @ RY(90 * DEG))
    # drips down the lid's lip and the front of the book box
    front = lambda x, z: Vector((x, -0.93, z))  # noqa: E731
    for i, (x, z1) in enumerate(((0.33, 1.9), (0.4, 2.1), (0.47, 1.98), (0.56, 2.18))):
        pts = [tuple(front(x + g.uniform(-0.01, 0.01), z)) for z in (2.27, (2.27 + z1) / 2, z1)]
        tube(f"Drip{i}", pts, 0.012, ink, poly=True)
        sphere(f"DripEnd{i}", 0.02, tuple(front(x, z1 - 0.01)), ink, seg=8, rings=5, scale=(1, 0.6, 1.3))
    # ink fingerprints: little oval smudges with whorl lines, on the lid and the lip
    for i, (cx, cy, a) in enumerate(((-0.6, -0.4, 0.4), (-0.35, -0.5, 0.1), (-0.95, 0.1, -0.3), (1.25, -0.5, 0.8), (1.3, 0.3, 0.2))):
        fill2d(f"Print{i}", [(cx + math.cos(t) * 0.05 * math.cos(a) - math.sin(t) * 0.07 * math.sin(a),
                              cy + math.cos(t) * 0.05 * math.sin(a) + math.sin(t) * 0.07 * math.cos(a)) for t in [k / 14 * 6.283 for k in range(14)]],
               dried, L, z=0.0018)
        for r in (0.015, 0.03, 0.045):
            ribbon(f"Whorl{i}{r}", circle2(cx, cy, r, 12, 0.3, 5.5, sy=1.35), 0.005, ink, L, z=0.0024, taper=False)
    _fine(0.5)
    return dims


# the cliques, straight from ReplicatedStorage.Config.Cliques
CLIQUES = {
    "Vigil": ("#EBCD78", "THE VIGIL REMEMBERS", "candle"),
    "Court": ("#C8283C", "FANGS OUT", "crown"),
    "Athletes": ("#5A96DC", "VARSITY", "pennant"),
    "Delinquents": ("#966E46", "BACK LOT RULES", "flames"),
    "Pack": ("#82965A", "PACK RUNS THIS", "paw"),
    "Ordinary": ("#C8BEAA", "HI MOM", "smiley"),
    "Choir": ("#E6E1D2", "REPENT", "halo"),
    "Ink": ("#9650BE", "ART IS A WEAPON", "quill"),
}


def emblem(kind, cx, cy, s, mark, K, L, seed):
    """The clique's emblem at (cx, cy) on the lid, about s across: carved first, then gone over in marker (fills and strokes)."""
    def P2(pts):
        return [(cx + x * s, cy + y * s) for x, y in pts]
    strokes, fills = [], []
    if kind == "candle":
        fills.append(P2([(-0.12, -0.45), (0.12, -0.45), (0.12, 0.1), (-0.12, 0.1)]))
        fills.append(P2([(0, 0.42), (0.07, 0.3), (0.08, 0.2), (0.0, 0.13), (-0.08, 0.2), (-0.07, 0.3)]))
        strokes += [P2([(-0.3, -0.48), (0.3, -0.48)])]
        for a in (20, 55, 125, 160):
            r0, r1 = 0.2, 0.34
            strokes.append(P2([(math.cos(a * DEG) * r0, 0.25 + math.sin(a * DEG) * r0), (math.cos(a * DEG) * r1, 0.25 + math.sin(a * DEG) * r1)]))
    elif kind == "crown":
        fills.append(P2([(-0.4, -0.05), (-0.42, 0.35), (-0.22, 0.12), (0.0, 0.42), (0.22, 0.12), (0.42, 0.35), (0.4, -0.05)]))
        fills.append(P2([(-0.22, -0.05), (-0.12, -0.05), (-0.17, -0.3)]))
        fills.append(P2([(0.12, -0.05), (0.22, -0.05), (0.17, -0.3)]))
        strokes.append(P2([(0.17, -0.3), (0.18, -0.42), (0.17, -0.5)]))
        fills.append(P2([(0.17 + math.cos(t) * 0.04, -0.52 + math.sin(t) * 0.05) for t in [k / 10 * 6.283 for k in range(10)]]))
    elif kind == "pennant":
        fills.append(P2([(-0.4, 0.4), (0.45, 0.2), (-0.4, 0.0)]))
        strokes.append(P2([(-0.42, 0.45), (-0.42, -0.5)]))
        fills.append(P2(star2(0.15, -0.28, 0.2, 0.08)))
    elif kind == "flames":
        fl = [(-0.45, -0.3)]
        for i in range(6):
            x = -0.45 + i * 0.16
            fl += [(x + 0.08, 0.1 + 0.18 * (i % 2)), (x + 0.16, -0.12)]
        fl += [(0.5, -0.3)]
        fills.append(P2(fl))
        fills.append(P2([(-0.35, -0.38), (0.35, -0.38), (0.35, -0.46), (-0.35, -0.46)]))
        for i in range(10):
            strokes.append(P2([(-0.32 + i * 0.07, -0.46), (-0.32 + i * 0.07, -0.56)]))
    elif kind == "paw":
        fills.append(P2([(math.cos(t) * 0.2, -0.15 + math.sin(t) * 0.16) for t in [k / 16 * 6.283 for k in range(16)]]))
        for tx, ty in ((-0.24, 0.12), (-0.09, 0.26), (0.09, 0.26), (0.24, 0.12)):
            fills.append(P2([(tx + math.cos(t) * 0.07, ty + math.sin(t) * 0.09) for t in [k / 12 * 6.283 for k in range(12)]]))
    elif kind == "smiley":
        strokes.append(P2(circle2(0, 0, 0.42, 28)))
        fills.append(P2(circle2(-0.14, 0.12, 0.06, 10)[:-1]))
        fills.append(P2(circle2(0.14, 0.12, 0.06, 10)[:-1]))
        strokes.append(P2(circle2(0, 0.02, 0.25, 14, a0=200 * DEG, a1=340 * DEG)))
    elif kind == "halo":
        strokes.append(P2(circle2(0, 0.38, 0.22, 24, sy=0.35)))
        fills.append(P2([(-0.05, 0.2), (0.05, 0.2), (0.05, 0.02), (0.2, 0.02), (0.2, -0.07), (0.05, -0.07), (0.05, -0.5), (-0.05, -0.5),
                         (-0.05, -0.07), (-0.2, -0.07), (-0.2, 0.02), (-0.05, 0.02)]))
    elif kind == "quill":
        fills.append(P2([(0.38, 0.45), (0.25, 0.42), (0.05, 0.25), (-0.12, 0.0), (-0.2, -0.18), (-0.1, -0.08), (0.1, 0.08), (0.3, 0.3)]))
        strokes.append(P2([(0.38, 0.45), (-0.28, -0.32)]))
        strokes.append(P2([(-0.28, -0.32), (-0.29, -0.45)]))
        g = random.Random(seed)
        for i in range(9):
            r = g.uniform(0.02, 0.06)
            x, y = g.uniform(-0.45, 0.45), g.uniform(-0.55, -0.2)
            fills.append(P2(circle2(x, y, r / max(s, 1e-3) * s, 8)[:-1]))
    carve(f"Em{kind}", [f + [f[0]] for f in fills] + strokes, L, K, w=0.03, seed=seed)
    for i, f in enumerate(fills):
        ribbon(f"EmOut{i}", densify(f + [f[0]], 0.025), 0.06, K["groove"], L, z=0.0024, taper=False)
        fill2d(f"EmFill{i}", jitter(f, 0.004, seed + i), mark, L, z=0.003)
    for i, st in enumerate(strokes):
        ribbon(f"EmLineOut{i}", densify(st, 0.025), 0.085, K["groove"], L, z=0.0024, taper=False)
        ribbon(f"EmLine{i}", jitter(densify(st, 0.025), 0.004, seed + 50 + i), 0.05, mark, L, z=0.0032)
    if kind == "paw":   # claw scratches gouged deep beside the print
        carve("Claws", [[(cx + 0.35 * s + k * 0.08, cy + 0.35 * s), (cx + 0.55 * s + k * 0.08, cy - 0.4 * s)] for k in range(4)], L, K, w=0.05, seed=seed + 9)


def desk_prank(M, key):
    K = kit(M)
    dims = base_desk(M)
    L = lid_frame()
    hexc, slogan, kind = CLIQUES[key]
    mark = flat(f"Marker{key}", lin(hexc), 0.45, dirt=0.3)
    emblem(kind, -0.9, 0.05, 1.2, mark, K, L, seed=len(key) * 7)
    words = slogan.split()
    if len(slogan) > 10 and len(words) > 1:
        cut = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    else:
        lines = [slogan]
    g = random.Random(len(slogan))
    for i, ln in enumerate(lines):
        cy = 0.05 + (0.3 - i * 0.6 if len(lines) == 2 else 0.0)
        fit = (1.8, 0.56 if len(lines) == 2 else 0.75)
        a = g.uniform(-0.05, 0.05)
        carve_text(f"Carve{i}", ln, L, K, 0.55, cy, fit, ang=a, font=FONT_HAND, groove_bold=0.07, cut=False)
        marker_text(f"Mark{i}", ln, mark, L, 0.55, cy, (fit[0] * 0.97, fit[1] * 0.93), ang=a, bold=0.035)
    # a stray marker drip or two
    ribbon("Drip", densify([(0.0, -0.6), (0.02, -0.72)], 0.02), 0.03, mark, L, z=0.003)
    _fine(0.5)
    return dims


# ------------------------------------------------------------------ detention room pieces

def detention_desk(M):
    """A heavy combination desk: an ebonised oak top on a cast-iron pedestal frame, the seat on the same frame, all bolted to one iron
    floor plate. Desk top 2.45, seat top 1.7; the seat is at the front (-Y), the student faces +Y."""
    K = kit(M)
    ir, wd = K["iron"], K["darkoak"]
    top_h = 2.45
    W, D = 3.0, 1.9
    # the floor plate and its bolts
    box("Plate", (3.2, 4.2, 0.08), (0, -0.95, 0.04), ir, bevel=0.02)
    for x in (-1.45, 1.45):
        for y in (0.95, -0.95, -2.85):
            cyl(f"Bolt{x}{y}", 0.07, 0.06, (x, y, 0.1), ir, verts=6, bevel=0.01)
            cyl(f"Washer{x}{y}", 0.1, 0.02, (x, y, 0.085), K["steel"], verts=16, bevel=0.005)
    # the desk: a thick top, a book box under it, a solid ebonised front panel with an iron pointed arch
    box("Top", (W, D, 0.14), (0, 0, top_h - 0.07), wd, bevel=0.035, segments=3)
    box("Groove", (W * 0.6, 0.07, 0.03), (0, D / 2 - 0.2, top_h + 0.005), K["groove"], bevel=0.008)
    lathe("Inkwell", [(0, 0), (0.08, 0), (0.09, 0.03), (0.06, 0.06), (0, 0.06)], K["iron"], seg=16, loc=(W / 2 - 0.3, D / 2 - 0.2, top_h - 0.02))
    box("Box", (W - 0.3, D - 0.25, 0.06), (0, 0.02, 1.95), wd, bevel=0.015)
    box("BoxFront", (W - 0.3, 0.06, 0.38), (0, D / 2 - 0.12, 2.15), wd, bevel=0.012)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.25)
        # cast-iron pedestal end: a pierced lyre with a quatrefoil, feet bolted down
        box(f"EndFoot{sx}", (0.18, D - 0.1, 0.12), (x, 0.0, 0.14), ir, bevel=0.03)
        for sy in (-1, 1):
            tube(f"EndLeg{sx}{sy}", [(x, sy * (D / 2 - 0.25), 0.2), (x, sy * (D / 2 - 0.35), 1.1), (x, sy * (D / 2 - 0.25), top_h - 0.14)], 0.05, ir)
        tube(f"EndArch{sx}", [(x, y, z) for y, z in B34.seg_arc(D / 2 - 0.3, top_h - 0.6, 0.4, 12)], 0.035, ir, poly=True)
        hoop(f"EndRing{sx}", (x, 0, 1.15), 0.3, "X", ir, thick=0.035)
        tube(f"EndBar{sx}", [(x, 0, 0.2), (x, 0, 0.85)], 0.035, ir, poly=True)
        for k, (dy, dz) in enumerate(((0, 0.15), (0, -0.15), (0.15, 0), (-0.15, 0))):
            hoop(f"EndLobe{sx}{k}", (x, dy, 1.15 + dz), 0.12, "X", ir, thick=0.02)
    # the seat in front, on the same plate: an iron standard and a slatted oak seat with a back rail
    ys = -2.0
    for sx in (-1, 1):
        x = sx * 1.05
        tube(f"SeatLeg{sx}", [(x, ys + 0.4, 0.1), (x, ys + 0.3, 0.9), (x, ys, 1.6)], 0.045, ir)
        tube(f"SeatLegB{sx}", [(x, ys - 0.45, 0.1), (x, ys - 0.35, 0.9), (x, ys, 1.6)], 0.045, ir)
        box(f"SeatFoot{sx}", (0.16, 1.1, 0.1), (x, ys, 0.13), ir, bevel=0.03)
        tube(f"Runner{sx}", [(x, ys + 0.4, 0.3), (x, -0.85, 0.3)], 0.04, ir, poly=True)
        tube(f"BackPost{sx}", [(x, ys - 0.4, 1.6), (x, ys - 0.5, 2.6)], 0.04, ir)
    for k in range(4):
        box(f"Slat{k}", (2.4, 0.2, 0.07), (0, ys - 0.33 + k * 0.22, 1.665), wd, bevel=0.02)
    box("BackRail", (2.4, 0.08, 0.32), (0, ys - 0.52, 2.45), wd, bevel=0.02, rot=(-0.12, 0, 0))
    box("BackRailLow", (2.3, 0.06, 0.14), (0, ys - 0.47, 1.95), wd, bevel=0.015, rot=(-0.12, 0, 0))
    tube("SeatTie", [(-1.05, ys, 1.0), (1.05, ys, 1.0)], 0.035, ir, poly=True)
    # carved initials and scratches on the top
    L = T(0, 0, top_h)
    carve_text("Ini1", "D.Q.", L, K, -0.9, -0.25, (0.35, 0.16), ang=0.2)
    carve_text("Ini2", "T.A. 106", L, K, 0.7, -0.45, (0.6, 0.15), ang=-0.08)
    carve_text("Ini3", "HELP", L, K, 0.2, 0.15, (0.5, 0.18), ang=0.05)
    strokes = [[(x, -0.62), (x + 0.01, -0.82)] for x in (-0.3, -0.25, -0.2, -0.15)] + [[(-0.34, -0.79), (-0.1, -0.65)]]
    strokes += [[(-1.3, 0.5), (-0.6, 0.62)], [(0.9, 0.2), (1.35, 0.05)], [(-0.4, -0.1), (-0.2, 0.4)], [(1.0, 0.55), (1.3, 0.62)]]
    carve("Scr", strokes, L, K, w=0.02, seed=37)
    _fine(0.6)
    return _dims()


def lines_chalkboard(M):
    """A wall chalkboard (its back on the wall at y = 0, its foot at z = 0): slate covered in lines, an oak frame with a pointed
    crest, a chalk tray with chalk stubs and an eraser."""
    K = kit(M)
    W, H = 7.4, 4.3
    sw, sh = 6.8, 6.8 * 1150 / 2000
    zc = 0.55 + sh / 2
    box("Back", (W, 0.12, H), (0, -0.06, H / 2 + 0.1), K["oakdark"], bevel=0.02)
    B30.plate("Slate", "K7_Lines_Board", sw, sh, 0.05, T(0, -0.14, zc), K["p7"], edge="K7_slate", k=4.0)
    fw = 0.3
    for nm, sz, loc in (("FrameT", (W + 0.2, 0.2, fw), (0, -0.2, zc + sh / 2 + fw / 2 - 0.02)), ("FrameB", (W + 0.2, 0.2, fw), (0, -0.2, zc - sh / 2 - fw / 2 + 0.02)),
                        ("FrameL", (fw, 0.2, sh + 2 * fw), (-sw / 2 - fw / 2 + 0.02, -0.2, zc)), ("FrameR", (fw, 0.2, sh + 2 * fw), (sw / 2 + fw / 2 - 0.02, -0.2, zc))):
        box(nm, sz, loc, K["oak"], bevel=0.05, segments=3)
    tube("Bead", [(-sw / 2, -0.18, zc - sh / 2), (sw / 2, -0.18, zc - sh / 2), (sw / 2, -0.18, zc + sh / 2), (-sw / 2, -0.18, zc + sh / 2)], 0.025, K["oakdark"],
         square=True, closed=True, poly=True)
    zt = zc + sh / 2 + fw
    _gable("Crest", 0, -0.18, 1.2, zt - 0.05, zt + 0.75, 0.14, K["oak"], K["oakdark"], edge=0.035)
    foil("CrestFoil", 0, -0.27, zt + 0.25, 0.17, K["brass"], lobes=3, thick=0.016)
    _text("Room", "ROOM 106", FONT, K["gilt"], lambda x, y, h: (x, -0.31 - h, zt - 0.17 + y), fit=(1.2, 0.14), depth=0.012, res=3)
    zb = zc - sh / 2 - fw
    box("Tray", (sw, 0.42, 0.06), (0, -0.4, zb + 0.03), K["oak"], bevel=0.02)
    box("TrayLip", (sw, 0.04, 0.09), (0, -0.6, zb + 0.08), K["oakdark"], bevel=0.012)
    for sx in (-1, 1):
        tube(f"Bracket{sx}", [(sx * 2.6, -0.12, zb - 0.45), (sx * 2.6, -0.2, zb - 0.2), (sx * 2.6, -0.55, zb + 0.0)], 0.03, K["iron"])
    g = random.Random(3720)
    for k, x in enumerate((-2.6, -2.4, -0.3, 1.7, 1.85)):
        ln = g.uniform(0.12, 0.35)
        cyl(f"Chalk{k}", 0.035, ln, (x, -0.42, zb + 0.095), K["chalk"], rot=(0, math.pi / 2, g.uniform(-0.4, 0.4)), verts=10, bevel=0.006)
    box("EraserWood", (0.6, 0.2, 0.09), (2.6, -0.4, zb + 0.15), K["oak"], bevel=0.02)
    box("EraserFelt", (0.58, 0.18, 0.05), (2.6, -0.4, zb + 0.08), K["felt"], bevel=0.01)
    dust = flat("ChalkDust", (0.62, 0.62, 0.6), 0.95)
    for k in range(6):
        box(f"Dust{k}", (g.uniform(0.2, 0.6), 0.3, 0.003), (g.uniform(-3, 3), -0.4, zb + 0.062), dust, bevel=0.0)
    return _dims()


def pencil(prefix, K, mtx, length=0.42, worn=0.0):
    s = _mark()
    paint = flat("PencilPaint", (0.12, 0.012, 0.02), 0.35)
    wood = flat("PencilWood", (0.62, 0.45, 0.28), 0.7)
    lead = flat("Graphite", (0.06, 0.06, 0.065), 0.3, metal=0.4)
    cyl(f"{prefix}Body", 0.016, length, (0, 0, length / 2), paint, verts=6, bevel=0.002)
    cone(f"{prefix}Tip", 0.016, 0.004, 0.06, (0, 0, length + 0.03), wood, verts=6)
    cone(f"{prefix}Lead", 0.005, 0.0005, 0.015, (0, 0, length + 0.065), lead, verts=6)
    cyl(f"{prefix}Ferrule", 0.017, 0.035, (0, 0, -0.012), K["brassf"], verts=12, bevel=0.002)
    cyl(f"{prefix}Eraser", 0.015, 0.03 * (1 - worn * 0.7), (0, 0, -0.04), flat("Eraser", (0.6, 0.25, 0.25), 0.8), verts=12, bevel=0.004)
    _xform(s, mtx)


def lines_paper_stack(M):
    K = kit(M)
    g = random.Random(3730)
    w, h = 0.64, 0.86
    box("Block", (w - 0.01, h - 0.01, 0.07), (0, 0, 0.035), B24.pages("StackEdges", (0.86, 0.84, 0.77)), bevel=0.004, rot=(0, 0, 0.02))
    z = 0.072
    for k in range(6):
        key = "K7_Lines_Page1" if k % 2 else "K7_Lines_Page2"
        B34.sheet(f"Page{k}", key, w, h, T(g.uniform(-0.04, 0.04), g.uniform(-0.04, 0.04), z) @ RZ(g.uniform(-9, 9) * DEG), K["p7"],
                  curl=g.uniform(0.005, 0.02), lift=g.uniform(0, 0.015), rnd=g)
        z += 0.005
    B34.sheet("Loose", "K7_Lines_Page1", w, h, T(0.62, -0.1, 0.004) @ RZ(-28 * DEG), K["p7"], curl=0.02, rnd=g)
    pencil("Pencil", K, T(0.15, -0.55, 0.018) @ RZ(70 * DEG) @ RY(90 * DEG), length=0.3, worn=0.8)
    _fine(0.4)
    return _dims()


def service_bell(prefix, K, loc):
    s = _mark()
    lathe(f"{prefix}Base", [(0, 0), (0.16, 0), (0.17, 0.02), (0.15, 0.05), (0, 0.05)], K["ebony"], seg=24)
    lathe(f"{prefix}Dome", [(0, 0.22), (0.05, 0.215), (0.1, 0.19), (0.13, 0.14), (0.145, 0.08), (0.15, 0.055), (0, 0.055)], K["brassf"], seg=28)
    cyl(f"{prefix}Stem", 0.012, 0.06, (0, 0, 0.25), K["brassf"], verts=10, bevel=0.002)
    sphere(f"{prefix}Knob", 0.025, (0, 0, 0.285), K["brassf"], seg=10, rings=5)
    _xform(s, T(*loc))


def supervisor_podium(M):
    """A low oak platform (0.7 high, steps up at the back) and on it the supervisor's desk (top 3.7 above the floor), a crimson
    leather inset, gothic modesty panel with enamel fields, a brass desk lamp (Glow: the bulb), a bell, the register and a pen."""
    K = kit(M)
    PW, PD, PH = 7.0, 5.0, 0.7
    wd = K["darkoak"]
    box("Platform", (PW, PD, PH - 0.08), (0, 0, (PH - 0.08) / 2), wd, bevel=0.03)
    box("PlatformTop", (PW + 0.1, PD + 0.1, 0.08), (0, 0, PH - 0.04), K["oak"], bevel=0.02)
    box("Kick", (PW + 0.02, 0.06, 0.12), (0, -PD / 2 - 0.02, 0.06), K["iron"], bevel=0.01)
    for k in range(7):
        x = -PW / 2 + 0.5 + k * (PW - 1) / 6
        box(f"Board{k}", (0.03, 0.02, PH - 0.2), (x, -PD / 2 - 0.005, PH / 2 - 0.02), K["groove"], bevel=0.0)
    box("Step", (2.4, 0.9, 0.35), (0, PD / 2 + 0.45, 0.175), wd, bevel=0.025)
    # the desk
    W, D, top = 5.0, 2.4, PH + 3.0
    box("Top", (W, D, 0.16), (0, 0.4, top - 0.08), wd, bevel=0.04, segments=3)
    box("Inset", (W - 0.7, D - 0.7, 0.012), (0, 0.45, top + 0.004), K["leather"], bevel=0.0)
    box("Front", (W - 0.1, 0.12, top - PH - 0.16), (0, 0.4 - D / 2 + 0.1, PH + (top - PH - 0.16) / 2), wd, bevel=0.02)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.12, D - 0.2, top - PH - 0.16), (sx * (W / 2 - 0.1), 0.4, PH + (top - PH - 0.16) / 2), wd, bevel=0.02)
    for k in range(4):
        cx = -W / 2 + 0.75 + k * (W - 1.5) / 3
        yf = 0.4 - D / 2 + 0.03
        pts = WS.arch(0.42, PH + 0.35, PH + 1.6, PH + 2.3, 8, cx=cx)
        B20.tprism(f"Field{k}", pts, yf - 0.01, 0.02, K["enamel"])
        tube(f"FieldEdge{k}", [(x, yf - 0.025, z) for x, z in pts] + [(pts[0][0], yf - 0.025, pts[0][1])], 0.03, K["iron"], square=True, poly=True)
        foil(f"FieldFoil{k}", cx, yf - 0.035, PH + 1.95, 0.14, K["brass"], lobes=4, thick=0.014)
    box("Apron", (W - 0.1, 0.16, 0.3), (0, 0.4 - D / 2 + 0.06, top - 0.3), wd, bevel=0.03)
    box("Brass", (W + 0.02, 0.03, 0.05), (0, 0.4 - D / 2 - 0.01, top - 0.16), K["brass"], bevel=0.01)
    # on the desk: a lamp, a bell, a closed register, an inkstand
    s = _mark()
    B34.desk_lamp(M)
    _xform(s, T(-1.7, 1.1, top) @ RZ(-25 * DEG) @ Matrix.Diagonal((0.8, 0.8, 0.8, 1)))
    service_bell("Bell", K, (1.6, 0.0, top))
    reg = material("RegCloth", "NH_Leather", tint=(0.1, 0.012, 0.02), scale=2.5, normal=0.4, wear=0.3)
    box("Register", (0.9, 1.2, 0.14), (0.3, 0.6, top + 0.07), reg, bevel=0.02, rot=(0, 0, 0.12))
    box("RegPages", (0.86, 1.14, 0.1), (0.32, 0.6, top + 0.07), B24.pages("RegPages", (0.82, 0.77, 0.64)), bevel=0.005, rot=(0, 0, 0.12))
    box("RegLabel", (0.4, 0.2, 0.004), (0.3, 0.6, top + 0.142), K["paper"], bevel=0.0, rot=(0, 0, 0.12))
    pencil("Pen", K, T(1.0, 0.5, top + 0.02) @ RZ(20 * DEG) @ RY(90 * DEG), length=0.4)
    return _dims()


def detention_log(M):
    """The detention register open on a slanted cast-iron stand (reading top ~3.6), a pen on a chain to an eye on the stand."""
    K = kit(M)
    ir = K["iron"]
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in ((0.05, 0.7), (0.35, 0.4), (0.62, 0.1), (0.8, 0.12), (0.78, 0.28))], 0.04, ir, square=True)
        sphere(f"Toe{k}", 0.06, (c * 0.62, s_ * 0.62, 0.06), ir, seg=8, rings=4)
    lathe("Column", [(0, 0.55), (0.1, 0.55), (0.08, 0.7), (0.06, 0.9), (0.055, 2.9), (0.09, 3.0), (0, 3.0)], ir, seg=20, flute=(8, 0.15))
    hoop("Collar", (0, 0, 0.95), 0.07, "Z", K["brass"], thick=0.02)
    hoop("Collar2", (0, 0, 2.85), 0.065, "Z", K["brass"], thick=0.02)
    # the desk head, tilted toward the writer at -Y
    tilt = 22 * DEG
    s = _mark()
    W, D = 2.3, 1.6
    box("Desk", (W, D, 0.1), (0, 0, 0), K["ebony"], bevel=0.025)
    box("Ledge", (W, 0.08, 0.1), (0, -D / 2 + 0.02, 0.08), K["ebony"], bevel=0.02)
    tube("Bead", [(-W / 2, -D / 2 - 0.01, 0.0), (W / 2, -D / 2 - 0.01, 0.0)], 0.015, K["brass"], poly=True)
    # the open register: boards, page blocks and two curled printed pages
    reg = material("LogCloth", "NH_Leather", tint=(0.1, 0.012, 0.02), scale=2.5, normal=0.4, wear=0.3)
    pw, ph = 1.0, 1.3
    for sx in (-1, 1):
        box(f"Board{sx}", (pw + 0.04, ph + 0.06, 0.03), (sx * (pw / 2 + 0.01), 0.04, 0.065), reg, bevel=0.01)
        box(f"Block{sx}", (pw - 0.06, ph - 0.04, 0.06), (sx * (pw / 2 + 0.01), 0.04, 0.105), B24.pages("LogPages", (0.8, 0.75, 0.62)), bevel=0.01)

        def fn(sv, tv, sx=sx):
            x = sx * (0.02 + sv * (pw - 0.06))
            z = 0.14 + 0.06 * math.sin(min(1.0, sv * 1.3) * math.pi / 2) ** 0.6 - 0.03 * sv ** 3
            return (x, 0.04 - ph / 2 + 0.03 + tv * (ph - 0.06), z)
        B30.leaf_sheet(f"Page{sx}", "K7_Ledger_L" if sx < 0 else "K7_Ledger_R", fn, 10, 1, (1, 0, 0, 1) if sx < 0 else (0, 0, 1, 1), K["p7"], thick=0.008,
                       k=3.0)
    box("Ribbon", (0.04, 0.6, 0.005), (0.15, -ph / 2 - 0.2, 0.13), K["velvet"], bevel=0.0, rot=(0.3, 0, 0))
    # the pen in the ledge's groove, a chain to an eye at the desk's right corner
    pen_body = flat("PenBody", (0.02, 0.02, 0.025), 0.25)
    cyl("Pen", 0.022, 0.5, (0.45, -D / 2 + 0.03, 0.16), pen_body, rot=(0, math.pi / 2, 0), verts=12, bevel=0.004)
    cone("Nib", 0.02, 0.003, 0.08, (0.74, -D / 2 + 0.03, 0.16), K["brassf"], verts=12, rot=(0, math.pi / 2, 0))
    cyl("PenCap", 0.024, 0.06, (0.2, -D / 2 + 0.03, 0.16), K["brassf"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.004)
    hoop("Eye", (W / 2 - 0.08, -D / 2 + 0.06, 0.1), 0.03, "Y", K["brass"], thick=0.008)
    B30.chain("Chain", [(0.17, -D / 2 + 0.03, 0.16), (0.6, -D / 2 - 0.08, 0.1), (W / 2 - 0.08, -D / 2 + 0.06, 0.1)], K["brass"], r=0.025, thick=0.006)
    _xform(s, T(0, 0, 3.05) @ RX(tilt))
    box("Head", (0.5, 0.5, 0.12), (0, 0, 3.0), ir, bevel=0.02)
    _fine(0.6)
    return _dims()


def phone(prefix, key, K, mtx):
    s = _mark()
    case = flat(f"{prefix}Case", (0.03, 0.03, 0.035), 0.35)
    rbox(f"{prefix}Body", 0.105, 0.22, 0.03, 0.0, 0.025, case)
    B34.pbox(f"{prefix}Screen", (0.19, 0.4, 0.004), (0, 0, 0.026), K["p7"], {"top": key, "else": "sw:K7_black"}, k=2.5)
    cyl(f"{prefix}Cam", 0.012, 0.004, (0.06, 0.17, -0.002), K["ink"], verts=10, bevel=0.0)
    _xform(s, mtx)


def card(prefix, key, K, mtx):
    B34.pbox(prefix, (0.19, 0.27, 0.003), (0, 0, 0), K["p7"], {"top": key, "bottom": "K7_Card_back", "else": "sw:K7_cardwhite"}, k=1.5, mtx=mtx)


def confiscated_box(M):
    """An open wooden crate, CONFISCATED painted on a board on its front, full of what was taken: a slingshot, two phones, comics,
    cards and a skateboard wheel."""
    K = kit(M)
    W, D, H = 2.2, 1.5, 1.2
    crate = material("CrateWood", "NH_DeskWood", tint=(0.34, 0.24, 0.15), scale=0.3, rough_add=0.12, wear=0.6)
    g = random.Random(3740)
    for side in ("F", "B"):
        y = -D / 2 + 0.04 if side == "F" else D / 2 - 0.04
        for k in range(3):
            box(f"Plank{side}{k}", (W, 0.08, 0.36), (0, y, 0.2 + k * 0.4), crate, bevel=0.015, rot=(0, g.uniform(-0.005, 0.005), 0))
    for sx in (-1, 1):
        for k in range(3):
            box(f"PlankS{sx}{k}", (0.08, D - 0.16, 0.36), (sx * (W / 2 - 0.04), 0, 0.2 + k * 0.4), crate, bevel=0.015)
        for sy in (-1, 1):
            box(f"Post{sx}{sy}", (0.12, 0.12, H), (sx * (W / 2 - 0.1), sy * (D / 2 - 0.1), H / 2), crate, bevel=0.015)
    box("Bottom", (W - 0.1, D - 0.1, 0.06), (0, 0, 0.03), crate, bevel=0.01)
    box("FalseFloor", (W - 0.2, D - 0.2, 0.05), (0, 0, 0.78), crate, bevel=0.01)
    for sx in (-1, 1):
        tube(f"Strap{sx}", [(sx * 0.8, -D / 2 - 0.005, 0.0), (sx * 0.8, -D / 2 - 0.005, H), (sx * 0.8, D / 2 + 0.005, H), (sx * 0.8, D / 2 + 0.005, 0.0)], 0.02,
             K["iron"], square=True, poly=True)
        box(f"Handle{sx}", (0.05, 0.3, 0.08), (sx * (W / 2 + 0.02), 0, 0.9), K["iron"], bevel=0.01)
    B30.plate("Label", "K7_Confiscated", 1.5, 0.42, 0.03, T(0, -D / 2 - 0.015, 0.62) @ RY(-2 * DEG), K["p7"], edge="K7_label", k=3.0)
    for sx in (-1, 1):
        sphere(f"Nail{sx}", 0.02, (sx * 0.7, -D / 2 - 0.035, 0.62), K["iron"], seg=8, rings=4, scale=(1, 0.5, 1))
    z0 = 0.805
    # comics fanned on top
    for k, (key, x, y, a) in enumerate((("K7_Comic_1", -0.35, 0.15, 8), ("K7_Comic_2", 0.15, 0.05, -14), ("K7_Comic_3", -0.1, -0.2, 30))):
        B34.pbox(f"Comic{k}", (0.52, 0.79, 0.01), (0, 0, 0), K["p7"], {"top": key, "else": "sw:K7_newsprint"}, k=2.2,
                 mtx=T(x, y, z0 + 0.006 + k * 0.012) @ RZ(a * DEG))
    # two phones
    phone("PhoneA", "K7_Phone_Lock", K, T(0.6, -0.25, z0 + 0.045) @ RZ(-20 * DEG))
    phone("PhoneB", "K7_Phone_Apps", K, T(0.7, 0.35, z0 + 0.12) @ RZ(65 * DEG) @ RX(-12 * DEG))
    # cards: a deck box and a spread
    deck = flat("DeckBox", (0.24, 0.03, 0.04), 0.5)
    box("Deck", (0.21, 0.29, 0.07), (-0.7, -0.4, z0 + 0.06), deck, bevel=0.006, rot=(0, 0, 0.3))
    for k, key in enumerate(("K7_Card_ace", "K7_Card_queen", "K7_Card_seven", "K7_Card_back")):
        card(f"Card{k}", key, K, T(-0.75 + k * 0.08, 0.3, z0 + 0.04 + k * 0.004) @ RZ((-25 + k * 18) * DEG))
    # a slingshot leaning out over the edge
    s = _mark()
    wood = flat("SlingWood", (0.3, 0.17, 0.08), 0.6)
    tube("SlingGrip", [(0, 0, 0), (0, 0, 0.22), (0, 0, 0.3)], 0.035, wood)
    tube("SlingL", [(0, 0, 0.3), (-0.08, 0, 0.42), (-0.13, 0, 0.56)], 0.026, wood)
    tube("SlingR", [(0, 0, 0.3), (0.08, 0, 0.42), (0.13, 0, 0.56)], 0.026, wood)
    for k in range(5):
        cyl(f"Wrap{k}", 0.04, 0.018, (0, 0, 0.04 + k * 0.035), flat("GripTape", (0.08, 0.04, 0.03), 0.8), verts=12, bevel=0.003)
    band = flat("SlingBand", (0.4, 0.08, 0.06), 0.6)
    tube("Band", [(-0.13, 0, 0.55), (-0.03, -0.18, 0.47), (0.03, -0.18, 0.47), (0.13, 0, 0.55)], 0.008, band)
    box("Pouch", (0.08, 0.02, 0.05), (0, -0.185, 0.47), flat("Pouch", (0.2, 0.1, 0.05), 0.7), bevel=0.006)
    _xform(s, T(-0.2, 0.45, z0 + 0.02) @ RZ(-10 * DEG) @ RX(-62 * DEG))
    # a skateboard wheel with its bearing
    urethane = flat("Urethane", (0.75, 0.66, 0.42), 0.5)
    lathe("Wheel", [(0.02, 0.0), (0.06, 0.0), (0.085, 0.01), (0.09, 0.035), (0.085, 0.06), (0.06, 0.07), (0.02, 0.07), (0.02, 0.0)], urethane, seg=24,
          loc=(0.35, -0.45, z0 + 0.025))
    cyl("Bearing", 0.03, 0.074, (0.35, -0.45, z0 + 0.06), K["steel"], verts=16, bevel=0.003)
    _fine(0.5)
    return _dims()


def gilt_frame(name, pw, ph, fw, zc, K):
    prof = [(0.0, 0.0), (0.0, -0.05), (0.03, -0.09), (0.07, -0.11), (0.11, -0.1), (0.14, -0.07), (0.15, -0.05), (fw, -0.04), (fw, -0.02)]
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
    fr = mesh_obj(name, bm, K["gilt"])
    fr.modifiers.new("Tri", "TRIANGULATE")
    box(name + "Back", (2 * hw - 0.02, 0.02, 2 * hh - 0.02), (0, -0.01, zc), K["ebony"], bevel=0.0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"{name}Corner{sx}{sz}", sx * (hw - 0.085), -0.122, zc + sz * (hh - 0.085), 0.06, K["gilt"], lobes=4, thick=0.012)
    return hw, hh


def wax_seal(prefix, x, y, z, K, seed=1, r=0.08):
    for sx in (-1, 1):
        box(f"{prefix}Ribbon{sx}", (0.06, 0.006, 0.24), (x + sx * 0.06, y + 0.005, z - 0.11),
            material(f"{prefix}Rib", "NH_Leather", tint=(0.16, 0.012, 0.022), scale=4.0, normal=0.2, rough_add=0.2, wear=0.0), bevel=0.0, rot=(0, sx * 0.35, 0))
    lathe(f"{prefix}Seal", [(0, 0), (r, 0), (r * 1.1, 0.01), (r * 1.05, 0.022), (r * 0.82, 0.027), (0.0, 0.025)], K["sealwax"], seg=24, jitter=(0.06, seed))
    P.PARTS[-1].matrix_world = T(x, y, z) @ RX(math.pi / 2)
    hoop(f"{prefix}Ring", (x, y - 0.028, z), r * 0.65, "Y", K["sealwax"], thick=0.008)
    B20.tprism(f"{prefix}Moon", WS.crescent(x, z, r * 0.42, shift=0.4, tilt=0.6), y - 0.028, 0.008, K["sealwax"])


def school_rules_board(M):
    """The rules of the school (kits3739_atlas.py) in a gilt frame, a wax seal at the foot; the back on the wall at y = 0."""
    K = kit(M)
    pw, ph = 2.2, 2.2 * 1500 / 1100
    fw = 0.2
    zc = ph / 2 + fw + 0.02
    gilt_frame("Frame", pw, ph, fw, zc, K)
    box("Mat", (pw + 0.04, 0.012, ph + 0.04), (0, -0.03, zc), K["velvet"], bevel=0.0)
    B30.plate("Print", "K7_Rules", pw, ph, 0.01, T(0, -0.04, zc), K["p7"], edge="K7_paper", k=4.0)
    wax_seal("Seal", 0.75, -0.05, zc - ph / 2 + 0.2, K, seed=4)
    _fine(0.5)
    return _dims()


def detention_sign(M):
    """A door sign: crimson enamel, a gilt border, DETENTION in raised gilt, a rule, SILENCE under it; back at y = 0."""
    K = kit(M)
    pw, ph, t = 2.6, 1.15, 0.08
    zc = ph / 2
    box("Plate", (pw, t, ph), (0, -t / 2, zc), K["enamel"], bevel=0.025)
    box("Backing", (pw + 0.14, 0.03, ph + 0.14), (0, -0.015, zc), K["iron"], bevel=0.015)
    tube("Border", [(-pw / 2 + 0.08, -t - 0.005, zc - ph / 2 + 0.08), (pw / 2 - 0.08, -t - 0.005, zc - ph / 2 + 0.08), (pw / 2 - 0.08, -t - 0.005, zc + ph / 2 - 0.08),
                    (-pw / 2 + 0.08, -t - 0.005, zc + ph / 2 - 0.08)], 0.016, K["gilt"], square=True, closed=True, poly=True)
    _text("Word", "DETENTION", FONT, K["gilt"], lambda x, y, h: (x, -t - h, zc + 0.17 + y), fit=(pw - 0.45, 0.42), depth=0.022, res=4)
    tube("Rule", [(-0.8, -t - 0.005, zc - 0.13), (0.8, -t - 0.005, zc - 0.13)], 0.01, K["gilt"], square=True, poly=True)
    for sx in (-1, 1):
        B20.tprism(f"Diamond{sx}", [(sx * 0.9, zc - 0.13 + 0.04), (sx * 0.94, zc - 0.13), (sx * 0.9, zc - 0.13 - 0.04), (sx * 0.86, zc - 0.13)], -t - 0.008,
                   0.012, K["gilt"])
    _text("Sub", "SILENCE", FONT, K["bone"], lambda x, y, h: (x, -t - h, zc - 0.32 + y), fit=(1.2, 0.2), depth=0.015, res=3)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sphere(f"Screw{sx}{sz}", 0.03, (sx * (pw / 2 + 0.03), -0.035, zc + sz * (ph / 2 + 0.03)), K["brassf"], seg=8, rings=4, scale=(1, 0.5, 1))
    _fine(0.6)
    return _dims()


def facing_wall_desk(M):
    """A desk boxed in by tall ebonised side panels and a low front board, set facing the wall: the student sits at -Y facing +Y.
    Desk top 2.45, panels 5.0 tall."""
    K = kit(M)
    W, D, top = 3.2, 2.0, 2.45
    wd = K["ebony"]
    box("Top", (W - 0.2, D, 0.12), (0, 0, top - 0.06), K["darkoak"], bevel=0.03)
    box("Shelf", (W - 0.3, D - 0.3, 0.05), (0, 0.1, 1.95), wd, bevel=0.01)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.05)
        box(f"Panel{sx}", (0.1, D + 0.4, 5.0), (x, 0.0, 2.5), wd, bevel=0.025)
        tube(f"PanelFrame{sx}", [(x + sx * 0.055, y, z) for y, z in ((-D / 2 + 0.05, 0.4), (D / 2 - 0.05, 0.4), (D / 2 - 0.05, 4.2), (-D / 2 + 0.05, 4.2))], 0.025,
             K["iron"], square=True, closed=True, poly=True)
        pts = WS.arch(0.7, 2.6, 3.6, 4.4, 8)
        for face in (-1, 1):
            tube(f"PanelArch{sx}{face}", [(x + face * 0.055, y, z) for y, z in pts], 0.022, K["iron"], square=True, poly=True)
        box(f"PanelCap{sx}", (0.16, D + 0.5, 0.08), (x, 0.0, 5.04), K["iron"], bevel=0.02)
        sphere(f"Finial{sx}", 0.08, (x, -D / 2 - 0.2, 5.14), K["brass"], seg=10, rings=5)
        for y in (-D / 2 + 0.1, D / 2 - 0.1):
            box(f"Shoe{sx}{y:.1f}", (0.22, 0.3, 0.1), (x, y, 0.05), K["iron"], bevel=0.02)
    box("FrontBoard", (W - 0.2, 0.08, 1.6), (0, D / 2 - 0.04, top + 0.8 - 0.06), wd, bevel=0.02)
    box("BackApron", (W - 0.2, 0.08, 0.5), (0, D / 2 - 0.04, top - 0.35), wd, bevel=0.015)
    box("Footrest", (W - 0.2, 0.25, 0.06), (0, D / 2 - 0.25, 0.35), K["iron"], bevel=0.015)
    # a card pinned to the front board
    B30.plate("Card", "K7_Lines_Page2", 0.64 * 0.8, 0.86 * 0.8, 0.006, T(0.6, D / 2 - 0.09, top + 0.9) @ RY(4 * DEG), K["p7"], edge="K7_paper", k=2.5)
    B34.pin("Pin", (0.6, D / 2 - 0.1, top + 1.2), K)
    _fine(0.7)
    return _dims()


def window_grille(M):
    """A cast-iron grille for a 4 x 6 window: bars with spear finials, a quatrefoil band, lugs bolted to the wall at y = 0."""
    K = kit(M)
    ir = K["iron"]
    W, H = 4.0, 6.0
    yb = -0.15
    for z in (0.15, 2.4, 2.9, H - 0.6):
        box(f"Rail{z}", (W, 0.08, 0.1), (0, yb, z), ir, bevel=0.015)
    n = 9
    for i in range(n):
        x = -W / 2 + 0.2 + i * (W - 0.4) / (n - 1)
        tube(f"Bar{i}", [(x, yb, 0.0), (x, yb, H - 0.25)], 0.035, ir, square=True, poly=True)
        lathe(f"Spear{i}", [(0, 0), (0.05, 0), (0.06, 0.04), (0.03, 0.08), (0.08, 0.16), (0.05, 0.24), (0, 0.38)], ir, seg=8, loc=(x, yb, H - 0.27))
        if i < n - 1:
            cx = x + (W - 0.4) / (n - 1) / 2
            foil(f"Foil{i}", cx, yb, 2.65, 0.2, ir, lobes=4, thick=0.02)
    for sx in (-1, 1):
        tube(f"Stile{sx}", [(sx * W / 2, yb, 0.0), (sx * W / 2, yb, H - 0.55)], 0.05, ir, square=True, poly=True)
        for z in (0.3, H - 0.8):
            box(f"Lug{sx}{z}", (0.12, 0.2, 0.08), (sx * (W / 2 + 0.06), yb / 2, z), ir, bevel=0.015)
            cyl(f"LugBolt{sx}{z}", 0.04, 0.05, (sx * (W / 2 + 0.06), yb / 2, z + 0.06), ir, verts=6, bevel=0.008)
    return _dims()


def key_shape(prefix, K, mtx, L=0.62, bits=2, seed=0):
    s = _mark()
    ir = K["ironf"]
    g = random.Random(seed)
    hoop(f"{prefix}Bow", (0, 0, -0.1), 0.085, "Y", ir, thick=0.02)
    foil(f"{prefix}BowFoil", 0, 0, -0.1, 0.06, ir, lobes=3, thick=0.008) if g.random() > 0.5 else None
    cyl(f"{prefix}Collar", 0.03, 0.05, (0, 0, -0.2), ir, verts=10, bevel=0.005)
    cyl(f"{prefix}Shaft", 0.022, L, (0, 0, -0.2 - L / 2), ir, verts=10, bevel=0.004)
    for b in range(bits):
        h = g.uniform(0.04, 0.09)
        box(f"{prefix}Bit{b}", (0.03, h, 0.05), (0, h / 2 + 0.01, -0.2 - L + 0.05 + b * 0.065), ir, bevel=0.004)
    _xform(s, mtx)


def key_ring_hook(M):
    """A warden's ring of eight big iron keys on a hook; the backplate on the wall at y = 0, the hook at z = 1.0."""
    K = kit(M)
    ir = K["iron"]
    B20.tprism("Plate", [(x, z + 0.95) for x, z in WS.arch(0.18, -0.35, 0.15, 0.4, 8)], -0.02, 0.04, ir)
    for z in (0.75, 1.25):
        sphere(f"Rivet{z}", 0.03, (0, -0.045, z), K["brass"], seg=8, rings=4)
    tube("Hook", [(0, -0.04, 1.02), (0, -0.2, 1.0), (0, -0.3, 0.9), (0, -0.26, 0.82), (0, -0.2, 0.85)], 0.025, ir)
    rc = (0, -0.28, 0.62)
    hoop("Ring", rc, 0.24, "X", ir, thick=0.022)
    for k in range(8):
        a = math.radians(-60 + k * 17)
        top = (0, rc[1] + math.sin(a) * 0.24, rc[2] - math.cos(a) * 0.24)
        key_shape(f"Key{k}", K, T(*top) @ RX(a * 0.7) @ RZ(k * 25 * DEG), L=0.45 + (k % 3) * 0.1, bits=1 + k % 3, seed=k)
    _fine(0.4)
    return _dims()


def wall_bell(M):
    """An old electric school bell on a round oak wall plate (back at y = 0): a crimson-painted dome, a brass striker, the coil box,
    a conduit up the wall."""
    K = kit(M)
    zc = 0.6
    s = _mark()
    lathe("Plate", [(0, 0), (0.5, 0), (0.52, 0.03), (0.5, 0.08), (0.44, 0.1), (0, 0.1)], K["darkoak"], seg=36)
    _xform(s, T(0, 0, zc) @ RX(math.pi / 2))
    s = _mark()
    lathe("Dome", [(0, 0.0), (0.06, 0.0), (0.06, 0.04), (0.18, 0.05), (0.3, 0.1), (0.37, 0.18), (0.4, 0.24), (0.38, 0.26), (0.35, 0.2), (0.27, 0.13), (0.15, 0.09),
                   (0, 0.085)], K["enamel"], seg=40)
    hoop("DomeRim", (0, 0, 0.25), 0.395, "Z", K["brassf"], thick=0.012)
    cyl("Boss", 0.06, 0.06, (0, 0, 0.0), K["brassf"], verts=14, bevel=0.01)
    _xform(s, T(0, -0.72, zc) @ RX(-math.pi / 2))
    cyl("Post", 0.04, 0.62, (0, -0.4, zc), K["brassf"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.005)
    box("CoilBox", (0.36, 0.14, 0.24), (0, -0.17, zc - 0.32), K["brassf"], bevel=0.02)
    for sx in (-1, 1):
        cyl(f"Coil{sx}", 0.05, 0.16, (sx * 0.08, -0.26, zc - 0.32), flat("CoilWire", (0.42, 0.18, 0.06), 0.4, metal=1.0), rot=(math.pi / 2, 0, 0), verts=14,
            bevel=0.004)
    tube("Arm", [(0, -0.24, zc - 0.32), (0, -0.36, zc - 0.4), (0, -0.46, zc - 0.43)], 0.012, K["brassf"])
    sphere("Striker", 0.035, (0, -0.48, zc - 0.44), K["brassf"], seg=10, rings=5)
    for sx in (-1, 1):
        cyl(f"Terminal{sx}", 0.02, 0.05, (sx * 0.14, -0.26, zc - 0.43), K["brassf"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.003)
    tube("Conduit", [(0.0, -0.06, zc + 0.5), (0.0, -0.06, zc + 1.4)], 0.035, K["iron"], poly=True)
    box("Clip", (0.12, 0.04, 0.05), (0, -0.04, zc + 1.1), K["iron"], bevel=0.008)
    _fine(0.5)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "DetentionDesk": detention_desk,
    "LinesChalkboard": lines_chalkboard,
    "LinesPaperStack": lines_paper_stack,
    "SupervisorPodium": supervisor_podium,
    "DetentionLog": detention_log,
    "ConfiscatedBox": confiscated_box,
    "SchoolRulesBoard": school_rules_board,
    "DetentionSign": detention_sign,
    "FacingWallDesk": facing_wall_desk,
    "WindowGrille": window_grille,
    "KeyRingHook": key_ring_hook,
    "WallBell": wall_bell,
    "StudentDeskCarved": desk_carved,
    "StudentDeskGraffiti": desk_graffiti,
    "StudentDeskBroken": desk_broken,
    "StudentDeskWobbly": desk_wobbly,
    "StudentDeskInkStained": desk_inkstained,
}
for _id in CLIQUES:
    BUILDERS[f"StudentDeskPrank{_id}"] = (lambda k: (lambda M: desk_prank(M, k)))(_id)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"DetentionSign": 1.4, "KeyRingHook": 1.4, "WallBell": 1.4, "SchoolRulesBoard": 1.2, "DetentionLog": 1.1})
B24.SMALL.update({"LinesPaperStack": 1.3, "ConfiscatedBox": 1.1})
