"""Props batch 52, the ending (2026-11-20): the bus stop at the edge of town and the black bus
(docs/expansion/15-Tutorial-The-Last-Normal-Night.md §5 beat 10, §8 "The bus").

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch52_ending.py -- <Prop|all> [--size 2048] [--samples 64] [--gpu]

WFBlackBus  the bus that isn't on the timetable: a 1950s-style long-nosed coach, 35 long, in black lacquer gone dull,
            crimson pin lines, nickel and brass trim. A real hollow body: open window bays with half-drop sashes (Glass),
            a lit interior of crimson leather bench seats under amber dome lamps (Glow), a ribbed aisle, a stairwell with
            brass nosings, a fare box, a forgotten satchel. Up front: an arched brass-barred grille with a crimson shield,
            a brass moth on the hood, bucket headlamps and fog lamps (Glow), crossview mirrors, west-coast mirrors,
            wipers. Gold-leaf NIGHTMARE HIGHSCHOOL on the letterboards (WF_BusSide), the NIGHTMARE HIGH blind
            (WF_BusBlind), NH 1313 plates (WF_BusPlate). Crimson wheels, duals at the back. The driver at the wheel:
            tall, thin, a long coat with the collar up, gloves, a peaked cap; no face, two pale points where the eyes
            should be (Glow).
            Rigged: Body (suspension), DoorA, DoorB (the folding doors), WiperL, WiperR, DriverHead, the six wheels.
            Clips: BrakeStop, EngineIdle (loop), DoorsOpen (the hiss), DoorsClose, WipersSweep (loop), DriverTurn (he
            looks at you), PullAway.
WFBusStop   the shelter on Alder Lane: green steel posts on bolted plates, arched ribs under a smoked curved roof (Glass),
            the WICKFIELD TRANSIT fascia (WF_ShelterBand), three glazed bays, the timetable in its locked case
            (WF_Timetable), a slatted bench on cast-iron brackets with armrest dividers, a caged tube lamp (Glow, the game
            flickers it) and its conduit, a lit ad case (WF_PosterBand). The flag pole with the stop sign (WF_BusSign)
            and a litter bin. Slab paving, a granite kerb, a slice of wet road with the yellow bus box, a drain, puddles,
            wet leaves, weeds in the joints, a crushed can and a soggy copy of THE PLAN (WF_ThePlan).

Front faces -Y, Z up, origin at the bottom centre.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube, set_group, material  # noqa: E402
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import lathe, prism, leaf  # noqa: E402
import nh_props_batch49_hometown as B49  # noqa: E402
from nh_props_batch49_hometown import kit, wmat, wall, drape, ease, back_out  # noqa: E402
from nh_props_batch52_pranks import _cutter, _cut  # noqa: E402

BUILDERS = {}


# ------------------------------------------------------------------ canvases that face sideways, backwards or up

_orig_canvas_uv = P.canvas_uv


def _canvas_uv(ob):
    """canvas_uv projects from the front (-Y). A piece tagged nh_canvas_face ("+X", "-X", "+Y", "+Z") is projected from
    that side instead, the image the right way round for someone looking at it."""
    face = ob.get("nh_canvas_face")
    if not face:
        return _orig_canvas_uv(ob)
    me = ob.data
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    uv = me.uv_layers.new(name="Bake")
    me.uv_layers.active = uv
    mw = ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]

    def f(co, k, flip=False):
        t = (co[k] - lo[k]) / max(1e-6, hi[k] - lo[k])
        return 1 - t if flip else t
    for li, loop in enumerate(me.loops):
        co = mw @ me.vertices[loop.vertex_index].co
        if face == "+X":
            uv.data[li].uv = (f(co, 1), f(co, 2))
        elif face == "-X":
            uv.data[li].uv = (f(co, 1, True), f(co, 2))
        elif face == "+Y":
            uv.data[li].uv = (f(co, 0, True), f(co, 2))
        else:                                                   # "+Z", top of the image toward +Y
            uv.data[li].uv = (f(co, 0), f(co, 1))


P.canvas_uv = _canvas_uv


def canvas(group, name, size, loc, K, face=None, back="Main"):
    set_group(group)
    ob = box(name, size, loc, K["place"], bevel=0)
    if face:
        ob["nh_canvas_face"] = face
    set_group(back)
    return ob


def _box_cutter(name, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    c = bpy.context.active_object
    c.name = name
    c.scale = size
    c.hide_render = True
    c.display_type = "WIRE"
    return c


def _superellipse(hw, zb, h, n=20, e=0.45):
    """the top half of a squarish ellipse from (+hw, zb) over the crown (0, zb + h) to (-hw, zb)"""
    pts = []
    for i in range(n + 1):
        a = math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        pts.append((hw * math.copysign(abs(c) ** e, c), zb + h * (max(0.0, s) ** e)))
    return pts


# ================================================================== the black bus

W_ = 8.4                       # body width
XS = 4.1                       # side wall plane
WR = 1.55                      # wheel radius
FY, RY = -12.4, 10.6           # front and rear axle y
Z_FLOOR = 2.9
Z_SILL, Z_WTOP = 6.4, 9.4      # the window band
Z_ROOF = 10.2
PITCH = 2.85
PILLARS = [-6.9 + k * PITCH for k in range(9)]           # -6.9 .. 15.9
DX, DY = -2.4, -7.6            # the driver's seat
WHEELS = {"WheelFL": (-3.5, FY), "WheelFR": (3.5, FY), "WheelRL": (-3.6, RY), "WheelRR": (3.6, RY)}
BODY_GROUPS = ("Main", "Nose", "Driver", "Glass", "Glow", "Blind", "SideL", "SideR", "Plate", "PlateRear", "Interior")


def _wheel(nm, x, y, rubber, rimmat, nickel, dual):
    s = 1 if x > 0 else -1
    set_group(nm)
    tyre_prof = [(0.95, -0.5), (1.35, -0.53), (WR, -0.42), (WR, 0.42), (1.35, 0.53), (0.95, 0.5)]
    offs = [0.0, -1.1] if dual else [0.0]
    for k, o in enumerate(offs):
        cx = x + s * o
        t = lathe(f"{nm}Tyre{k}", tyre_prof, rubber, seg=40, loc=(0, 0, 0), flute=(40, 0.035))
        t.rotation_euler = (0, math.pi / 2, 0)
        t.location = (cx, y, WR)
        rim = lathe(f"{nm}Rim{k}", [(0.0, -0.3), (0.93, -0.33), (0.97, 0.0), (0.9, 0.2), (0.55, 0.26), (0.0, 0.27)], rimmat, seg=28, loc=(0, 0, 0))
        rim.rotation_euler = (0, s * math.pi / 2, 0)
        rim.location = (cx, y, WR)
    cap = lathe(f"{nm}Cap", [(0.0, 0.24), (0.42, 0.24), (0.41, 0.33), (0.27, 0.43), (0.0, 0.46)], nickel, seg=24, loc=(0, 0, 0))
    cap.rotation_euler = (0, s * math.pi / 2, 0)
    cap.location = (x, y, WR)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cyl(f"{nm}Lug{k}", 0.07, 0.12, (x + s * 0.3, y + 0.64 * math.cos(a), WR + 0.64 * math.sin(a)), nickel, rot=(0, math.pi / 2, 0), verts=6, bevel=0)


def black_bus(M):
    K = kit(M)
    lacq = material("BusLacquer", "NH_PaintedMetal", tint=(0.03, 0.028, 0.032), scale=0.8, rough_add=0.12, wear=0.45, wear_metal=True, dirt=1.0)
    lacq_in = material("BusLacquerIn", "NH_PaintedMetal", tint=(0.05, 0.035, 0.035), scale=0.8, rough_add=0.25, wear=0.3, dirt=0.9)
    crimson = material("BusCrimson", "NH_PaintedMetal", tint=(0.36, 0.03, 0.05), scale=1.0, wear=0.5, wear_metal=True)
    nickel = material("BusNickel", base=(0.78, 0.77, 0.74), rough=0.18, metal=1.0, wear=0.35, dirt=0.8)
    brass = material("BusBrass", "NH_Brass", tint=(1.0, 0.86, 0.6), scale=0.5, wear=0.4, dirt=0.9)
    rubber = material("BusRubber", base=(0.03, 0.03, 0.035), rough=0.85, wear=0.0, dirt=0.8)
    leather = material("BusSeat", "NH_Leather", tint=(0.34, 0.04, 0.05), scale=1.4, normal=0.5, wear=0.55)
    brown = material("Satchel", "NH_Leather", tint=(0.32, 0.18, 0.09), scale=1.6, normal=0.5, wear=0.6)
    glass = material("BusGlass", base=(0.09, 0.07, 0.06), rough=0.04, wear=0.0, dirt=0.4)
    amber = material("BusAmber", base=(1.0, 0.58, 0.2), rough=0.4, wear=0.0, dirt=0.0)
    tail = material("BusTail", base=(0.85, 0.05, 0.04), rough=0.3, wear=0.0, dirt=0.0)
    lamp = material("BusLamp", base=(1.0, 0.9, 0.68), rough=0.3, wear=0.0, dirt=0.0)
    gauge = material("BusGauge", base=(0.5, 0.95, 0.7), rough=0.3, wear=0.0, dirt=0.0)
    eye = material("DriverEye", base=(0.75, 0.88, 1.0), rough=0.3, wear=0.0, dirt=0.0)
    coat = material("DriverCoat", "NH_Leather", tint=(0.05, 0.05, 0.06), scale=1.2, normal=0.4, rough_add=0.3, wear=0.25)
    void = material("Void", base=(0.0, 0.0, 0.0), rough=1.0, wear=0.0, dirt=0.0)
    grime = material("BusGrime", base=(0.1, 0.08, 0.06), rough=0.95, wear=0.0, dirt=1.0)
    set_group("Main")

    # ---- the nose: hood, grille, fenders, lamps, bumper (its own piece) -------------------------------------------
    set_group("Nose")
    hood = [(2.7, 2.4)] + _superellipse(2.7, 4.6, 1.4) + [(-2.7, 2.4)]
    prism("Hood", hood, -13.3, 6.2, lacq, plane="XZ", bevel=0.25)
    box("HoodSeam", (0.16, 6.1, 0.07), (0, -13.3, 6.02), brass, bevel=0.02)
    for sx in (-1, 1):
        box(f"HoodPin{sx}", (0.03, 5.9, 0.05), (sx * 2.715, -13.3, 4.95), crimson, bevel=0)
        for k in range(7):
            box(f"Louvre{sx}{k}", (0.1, 0.16, 0.95), (sx * 2.74, -15.4 + k * 0.5, 3.85), nickel, bevel=0)
    # the grille: an arched nickel surround round a black void, brass bars, a crimson shield
    gw = 2.15
    arch = [(gw * math.cos(math.pi * i / 16), 4.6 + 1.1 * math.sin(math.pi * i / 16)) for i in range(17)]
    prism("GrilleVoid", [(gw + 0.05, 2.55)] + [(x * (gw + 0.05) / gw, z) for x, z in arch] + [(-gw - 0.05, 2.55)], -16.6, 0.2, void, plane="XZ")
    rim_pts = [Vector((gw + 0.12, -16.72, 2.5))] + [Vector((x * (gw + 0.12) / gw, -16.72, 4.6 + (z - 4.6) * 1.12)) for x, z in arch] + [Vector((-gw - 0.12, -16.72, 2.5))]
    tube("GrilleSurround", rim_pts, 0.13, nickel, closed=True, res=4)
    for k in range(15):
        x = -1.89 + k * 0.27
        top = 4.6 + 1.1 * math.sqrt(max(0.0, 1 - (x / gw) ** 2)) - 0.12
        box(f"GrilleBar{k}", (0.09 if k != 7 else 0.16, 0.08, top - 2.62), (x, -16.74, (top + 2.62) / 2), brass if k != 7 else nickel, bevel=0)
    shield = [(0.0, 4.72), (0.42, 4.95), (0.45, 5.55), (-0.45, 5.55), (-0.42, 4.95)]
    prism("Shield", shield, -16.84, 0.06, crimson, plane="XZ", bevel=0.01)
    tube("ShieldRim", [Vector((x, -16.88, z)) for x, z in shield], 0.03, brass, closed=True, res=3)
    # the brass moth on the hood
    cyl("MothPost", 0.08, 0.25, (0, -16.0, 6.12), brass, verts=10, bevel=0.01)
    sphere("MothBody", 0.15, (0, -16.05, 6.42), brass, seg=12, rings=8, scale=(0.55, 1.6, 0.55))
    for sx in (-1, 1):
        prism(f"MothWingF{sx}", [(sx * 0.05, -16.2), (sx * 0.52, -16.38), (sx * 0.62, -16.1), (sx * 0.24, -16.0)], 6.4, 0.03, brass, plane="XY")
        prism(f"MothWingB{sx}", [(sx * 0.05, -16.02), (sx * 0.4, -15.94), (sx * 0.33, -15.77), (sx * 0.08, -15.88)], 6.4, 0.03, brass, plane="XY")
        tube(f"MothFeeler{sx}", [Vector((sx * 0.04, -16.25, 6.48)), Vector((sx * 0.15, -16.45, 6.62)), Vector((sx * 0.3, -16.5, 6.66))], 0.012, brass)
    # the fenders, the arches cut out, bucket headlamps on top, the turn lamps
    arch_cut = _cutter("ArchF", WR + 0.32, W_ + 2.0, (0, FY, WR), (0, math.pi / 2, 0))
    fender = [(-16.2, 1.9), (-16.3, 3.0), (-15.9, 4.1), (-15.0, 4.75), (-13.6, 5.05), (-12.0, 5.05), (-10.8, 4.7), (-10.05, 4.0), (-10.0, 1.9)]
    for sx in (-1, 1):
        ob = prism(f"Fender{sx}", fender, sx * 3.5, 1.6, lacq, plane="YZ", bevel=0.28)
        _cut(ob, [arch_cut])
        box(f"FenderPin{sx}", (1.4, 0.03, 0.05), (sx * 3.5, -16.26, 2.95), crimson, bevel=0)
        b = lathe(f"LampBucket{sx}", [(0.0, -0.5), (0.36, -0.5), (0.56, -0.25), (0.62, 0.12), (0.62, 0.3), (0.67, 0.34), (0.6, 0.42)], nickel, seg=28, loc=(0, 0, 0))
        b.rotation_euler = (math.pi / 2, 0, 0)
        b.location = (sx * 3.5, -15.5, 5.15)
        cyl(f"LampStalk{sx}", 0.12, 0.5, (sx * 3.5, -15.3, 4.7), nickel, verts=10, bevel=0)
        lathe(f"TurnLamp{sx}", [(0.0, 0.0), (0.16, 0.0), (0.18, 0.12), (0.12, 0.3), (0.0, 0.33)], nickel, seg=16, loc=(sx * 3.95, -14.0, 4.93))
        # crossview mirror on a stalk from the fender, facing back at the driver
        tube(f"XMirrorArm{sx}", [Vector((sx * 3.95, -15.6, 4.6)), Vector((sx * 4.4, -16.0, 5.6)), Vector((sx * 4.55, -16.25, 6.15))], 0.05, nickel)
        sphere(f"XMirrorBack{sx}", 0.38, (sx * 4.55, -16.32, 6.35), lacq, seg=12, rings=8, scale=(1, 0.45, 1))
        sphere(f"XMirrorFace{sx}", 0.33, (sx * 4.55, -16.18, 6.35), nickel, seg=12, rings=8, scale=(1, 0.25, 1))
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Headlamp{sx}", 0.55, (sx * 3.5, -15.9, 5.15), lamp, seg=20, rings=12, scale=(1, 0.3, 1))
        sphere(f"Turn{sx}", 0.13, (sx * 3.95, -14.0, 5.2), amber, seg=10, rings=6, scale=(1, 1, 0.8))
        sphere(f"FogLamp{sx}", 0.27, (sx * 2.3, -17.12, 2.45), amber, seg=14, rings=8, scale=(1, 0.45, 1))
    set_group("Nose")
    for sx in (-1, 1):
        ob = lathe(f"FogRing{sx}", [(0.24, -0.05), (0.32, -0.05), (0.32, 0.12), (0.24, 0.12)], nickel, seg=16, loc=(0, 0, 0))
        ob.rotation_euler = (math.pi / 2, 0, 0)
        ob.location = (sx * 2.3, -17.0, 2.45)
        box(f"FogBracket{sx}", (0.15, 0.3, 0.3), (sx * 2.3, -16.95, 2.17), nickel, bevel=0.03)
    # the bumper: a heavy nickel bar wrapping round, two guards, the plate between them; the valance behind
    box("Valance", (5.3, 0.3, 1.0), (0, -16.25, 1.9), lacq, bevel=0.08)
    box("BumperF", (8.0, 0.7, 0.72), (0, -17.1, 1.75), nickel, bevel=0.24, segments=3)
    for sx in (-1, 1):
        box(f"BumperEnd{sx}", (1.0, 0.6, 0.66), (sx * 4.3, -16.72, 1.75), nickel, bevel=0.2, rot=(0, 0, sx * 0.55), segments=3)
        box(f"BumperGuard{sx}", (0.3, 0.32, 1.5), (sx * 1.45, -17.48, 2.0), nickel, bevel=0.12, segments=3)
    canvas("Plate", "Plate", (1.4, 0.02, 0.7), (0, -17.465, 1.75), K, back="Main")

    # ---- the body shell ---------------------------------------------------------------------------------------
    arch_r = _cutter("ArchR", WR + 0.32, W_ + 2.0, (0, RY, WR), (0, math.pi / 2, 0))
    left = [(-10.2, 1.4), (-10.2, Z_SILL), (16.72, Z_SILL), (16.72, 1.4)]
    _cut(prism("SkirtL", left, -XS, 0.2, lacq, plane="YZ", bevel=0.05), [arch_r])
    right = [(-6.9, 1.4), (-6.9, Z_SILL), (16.72, Z_SILL), (16.72, 1.4)]
    _cut(prism("SkirtR", right, XS, 0.2, lacq, plane="YZ", bevel=0.05), [arch_r])
    box("DoorPost", (0.2, 0.3, Z_WTOP - 1.4), (XS, -10.05, (Z_WTOP + 1.4) / 2), lacq, bevel=0.04)
    box("FrontWall", (W_, 0.3, 4.9), (0, -10.05, 3.85), lacq, bevel=0.05)
    holes_l = [(-9.75, -7.35, 6.7, 9.1)] + [(PILLARS[k] + 0.2, PILLARS[k + 1] - 0.2, 6.7, 9.1) for k in range(8)]
    holes_r = [(PILLARS[k] + 0.2, PILLARS[k + 1] - 0.2, 6.7, 9.1) for k in range(8)]
    wall("BandL", "x", -XS, -10.2, 16.72, Z_SILL, Z_WTOP, 0.2, holes_l, lacq)
    wall("BandR", "x", XS, -6.9, 16.72, Z_SILL, Z_WTOP, 0.2, holes_r, lacq)
    for sx in (-1, 1):
        box(f"Letterboard{sx}", (0.2, 26.92, Z_ROOF - Z_WTOP), (sx * XS, 3.26, (Z_ROOF + Z_WTOP) / 2), lacq, bevel=0.03)
    canvas("SideL", "SideL", (0.02, 8.4, 0.74), (-XS - 0.115, 4.6, 9.8), K, face="-X")
    canvas("SideR", "SideR", (0.02, 8.4, 0.74), (XS + 0.115, 4.6, 9.8), K, face="+X")
    # the window glass (half-drop sashes) and nickel frames
    wins = [(-1, a, b) for a, b, _, _ in holes_l] + [(1, a, b) for a, b, _, _ in holes_r]
    for i, (sx, a, b) in enumerate(wins):
        yc, w = (a + b) / 2, b - a
        set_group("Glass")
        box(f"PaneUp{i}", (0.04, w, 1.25), (sx * (XS + 0.06), yc, 8.47), glass, bevel=0)
        box(f"PaneLo{i}", (0.04, w, 1.25), (sx * (XS - 0.02), yc, 7.33), glass, bevel=0)
        set_group("Main")
        box(f"Sash{i}", (0.1, w, 0.1), (sx * (XS + 0.03), yc, 7.95), nickel, bevel=0)
        for z in (6.72, 9.08):
            box(f"FrameH{i}{z}", (0.06, w, 0.06), (sx * (XS + 0.1), yc, z), nickel, bevel=0)
        for yy in (a + 0.03, b - 0.03):
            box(f"FrameV{i}{yy:.2f}", (0.06, 0.06, 2.4), (sx * (XS + 0.1), yy, 7.9), nickel, bevel=0)
    # rub rails, the sill strip, the double crimson pin line, rivets down every panel seam
    for sx in (-1, 1):
        y_start = -10.2 if sx < 0 else -6.9
        box(f"Sill{sx}", (0.08, 16.72 - y_start, 0.1), (sx * (XS + 0.12), (16.72 + y_start) / 2, Z_SILL + 0.02), nickel, bevel=0.02)
        for z in (6.08, 6.24):
            box(f"Pin{sx}{z}", (0.03, 16.6 - y_start, 0.05), (sx * (XS + 0.115), (16.6 + y_start) / 2, z), crimson, bevel=0)
        box(f"RubHi{sx}", (0.14, 16.6 - y_start, 0.2), (sx * (XS + 0.13), (16.6 + y_start) / 2, 4.3), lacq, bevel=0.06)
        for a, b in ((y_start, 8.7), (12.5, 16.6)):
            box(f"RubLo{sx}{a}", (0.14, b - a, 0.2), (sx * (XS + 0.13), (a + b) / 2, 2.4), lacq, bevel=0.06)
        for p in PILLARS + ([-10.0] if sx < 0 else []):
            for k in range(9):
                z = 1.75 + k * 0.52
                if abs(p - RY) < 2.1 and z < 3.6:
                    continue
                if abs(z - 2.4) < 0.15 or abs(z - 4.3) < 0.15:
                    continue
                cyl(f"Rivet{sx}{p:.1f}{k}", 0.055, 0.06, (sx * (XS + 0.1), p, z), lacq, rot=(0, math.pi / 2, 0), verts=6, bevel=0)
        # a rust-and-grime run under the last two windows
        for yy in (PILLARS[6] + 1.0, PILLARS[7] + 0.6):
            box(f"Streak{sx}{yy:.1f}", (0.02, 0.18, 1.3), (sx * (XS + 0.105), yy, 5.6), grime, bevel=0)
    # the fuel filler, the step under the door
    cyl("FuelCap", 0.22, 0.1, (-XS - 0.12, 1.5, 3.3), brass, rot=(0, math.pi / 2, 0), verts=16, bevel=0.03)
    box("DoorKick", (0.5, 3.0, 0.12), (XS + 0.2, -8.4, 1.35), brass, bevel=0.03)
    # the front: windshield in two panes, posts, the header with the destination blind, wipers
    for x in (-XS + 0.05, 0.0, XS - 0.05):
        box(f"ScreenPost{x:.1f}", (0.28 if x else 0.22, 0.3, 2.9), (x, -10.05, 7.85), lacq, bevel=0.04)
    box("Header", (W_, 0.3, Z_ROOF + 0.15 - 9.25), (0, -10.05, (Z_ROOF + 0.15 + 9.25) / 2), lacq, bevel=0.04)
    set_group("Glass")
    for sx in (-1, 1):
        box(f"Windshield{sx}", (3.7, 0.05, 2.7), (sx * 2.0, -10.12, 7.8), glass, bevel=0)
    box("BlindGlass", (4.5, 0.03, 0.74), (0, -10.27, 9.73), glass, bevel=0)
    set_group("Main")
    for sx in (-1, 1):
        for z in (6.47, 9.13):
            box(f"ScreenFrame{sx}{z}", (3.7, 0.06, 0.06), (sx * 2.0, -10.2, z), nickel, bevel=0)
    canvas("Blind", "Blind", (4.2, 0.02, 0.6), (0, -10.22, 9.73), K)
    for z in (9.36, 10.1):
        box(f"BlindFrameH{z}", (4.66, 0.08, 0.08), (0, -10.27, z), nickel, bevel=0.015)
    for x in (-2.29, 2.29):
        box(f"BlindFrameV{x}", (0.08, 0.08, 0.82), (x, -10.27, 9.73), nickel, bevel=0.015)
    # the west-coast mirrors on their arms
    for sx in (-1, 1):
        x0, x1 = sx * (XS + 0.1), sx * (XS + 1.05)
        tube(f"MirArmT{sx}", [Vector((x0, -9.95, 9.0)), Vector((x1, -10.3, 9.0)), Vector((x1, -10.35, 8.85))], 0.05, nickel)
        tube(f"MirArmB{sx}", [Vector((x0, -9.95, 6.5)), Vector((x1, -10.3, 6.5)), Vector((x1, -10.35, 6.65))], 0.05, nickel)
        box(f"MirHead{sx}", (0.2, 0.6, 2.1), (x1, -10.35, 7.75), lacq, bevel=0.06)
        box(f"MirFace{sx}", (0.16, 0.03, 1.9), (x1, -10.04, 7.75), nickel, bevel=0)
    # the roof: a crowned shell, ribs, two hatches, clearance and ID lamps
    roof = _superellipse(XS + 0.15, Z_ROOF, 1.2) + [(-XS - 0.15, Z_ROOF - 0.2), (XS + 0.15, Z_ROOF - 0.2)]
    prism("Roof", roof, 3.25, 27.0, lacq, plane="XZ", bevel=0.12)
    for k, y in enumerate([-10.0] + PILLARS + [16.5]):
        pts = [Vector((x * (XS + 0.19) / (XS + 0.15), y, Z_ROOF + (z - Z_ROOF) * 1.03 + 0.02)) for x, z in _superellipse(XS + 0.15, Z_ROOF, 1.2, n=12)]
        tube(f"RoofRib{k}", pts, 0.05, lacq, res=1, square=True)
    for y in (1.0, 10.0):
        box(f"Hatch{y}", (2.0, 2.2, 0.22), (0, y, Z_ROOF + 1.24), lacq, bevel=0.08)
        box(f"HatchHinge{y}", (1.2, 0.12, 0.1), (0, y + 1.12, Z_ROOF + 1.28), nickel, bevel=0.02)
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"ClearF{sx}", 0.14, (sx * 3.85, -10.3, 10.5), amber, seg=10, rings=6, scale=(1, 0.6, 0.8))
        sphere(f"ClearR{sx}", 0.14, (sx * 3.85, 16.82, 10.5), tail, seg=10, rings=6, scale=(1, 0.6, 0.8))
        sphere(f"MarkF{sx}", 0.12, (sx * (XS + 0.12), -9.95, 4.8), amber, seg=10, rings=6, scale=(0.6, 1, 0.8))
        sphere(f"MarkR{sx}", 0.12, (sx * (XS + 0.12), 16.5, 4.8), tail, seg=10, rings=6, scale=(0.6, 1, 0.8))
    for x in (-0.5, 0.0, 0.5):
        sphere(f"IdF{x}", 0.11, (x, -10.32, 11.0), amber, seg=10, rings=6, scale=(1, 0.6, 0.8))
        sphere(f"IdR{x}", 0.11, (x, 16.82, 11.0), tail, seg=10, rings=6, scale=(1, 0.6, 0.8))
    set_group("Main")
    # the rear: windows, the emergency door, lamps, plate, rubber bumper, exhaust
    rear_holes = [(-3.7, -1.5, 6.7, 9.1), (1.5, 3.7, 6.7, 9.1), (-1.0, 1.0, 6.0, 9.1)]
    wall("Rear", "y", 16.6, -4.2, 4.2, 1.4, Z_ROOF, 0.25, rear_holes, lacq)
    set_group("Glass")
    for i, (a, b, z0, z1) in enumerate(rear_holes):
        box(f"RearPane{i}", (b - a, 0.04, z1 - z0), ((a + b) / 2, 16.6, (z0 + z1) / 2), glass, bevel=0)
    set_group("Main")
    tube("EmergFrame", [Vector((x, 16.75, z)) for x, z in ((-1.25, 1.9), (1.25, 1.9), (1.25, 9.3), (-1.25, 9.3))], 0.05, nickel, closed=True, res=3)
    box("EmergHandle", (0.9, 0.12, 0.12), (0.6, 16.8, 5.2), nickel, bevel=0.04)
    for sx in (-1, 1):
        for nm, r, z in (("TailRim", 0.42, 3.6), ("TurnRim", 0.3, 4.55)):
            ob = lathe(f"{nm}{sx}", [(0.0, 0.0), (r, 0.0), (r, 0.12), (r - 0.08, 0.14), (0.0, 0.14)], nickel, seg=20, loc=(0, 0, 0))
            ob.rotation_euler = (-math.pi / 2, 0, 0)
            ob.location = (sx * 3.45, 16.73, z)
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Tail{sx}", 0.34, (sx * 3.45, 16.87, 3.6), tail, seg=16, rings=8, scale=(1, 0.35, 1))
        sphere(f"TurnR{sx}", 0.25, (sx * 3.45, 16.85, 4.55), amber, seg=14, rings=8, scale=(1, 0.35, 1))
    set_group("Main")
    canvas("PlateRear", "PlateRear", (1.4, 0.02, 0.7), (0, 16.745, 2.65), K, face="+Y")
    box("BumperR", (8.4, 0.6, 0.6), (0, 17.0, 1.6), rubber, bevel=0.15, segments=3)
    cyl("Exhaust", 0.14, 1.0, (-2.9, 16.95, 1.15), nickel, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.02)
    cyl("ExhaustSoot", 0.11, 0.02, (-2.9, 17.46, 1.15), void, rot=(math.pi / 2, 0, 0), verts=14, bevel=0)
    # under the body: frame rails, the floor pan, axles, the fuel tank, mud flaps
    for sx in (-1, 1):
        box(f"FrameRail{sx}", (0.3, 32.6, 0.5), (sx * 1.6, 0.2, 1.3), K["iron"], bevel=0.04)
        box(f"MudFlap{sx}", (1.3, 0.08, 1.3), (sx * 3.4, 12.75, 1.05), rubber, bevel=0.03)
    box("Underbody", (3.8, 26.0, 1.5), (0, 3.4, 1.85), lacq_in, bevel=0.05)
    box("AxleF", (6.0, 0.3, 0.3), (0, FY, WR), K["iron"], bevel=0.04)
    cyl("AxleR", 0.32, 5.2, (0, RY, WR), K["iron"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.03)
    sphere("Diff", 0.6, (0, RY, WR), K["iron"], seg=14, rings=8, scale=(1, 0.8, 0.8))
    box("FuelTank", (1.6, 4.0, 1.0), (-3.1, 1.5, 1.4), K["iron"], bevel=0.15, segments=3)

    # ---- inside --------------------------------------------------------------------------------------------------
    set_group("Interior")
    box("Floor", (6.75, 26.6, 0.3), (-0.625, 3.4, Z_FLOOR - 0.15), rubber, bevel=0)
    box("FloorR", (1.35, 23.6, 0.3), (3.425, 4.9, Z_FLOOR - 0.15), rubber, bevel=0)
    for k in range(52):
        box(f"AisleRib{k}", (1.6, 0.06, 0.04), (0, -5.8 + k * 0.42, Z_FLOOR + 0.02), rubber, bevel=0)
    box("Headliner", (8.0, 26.6, 0.04), (0, 3.3, Z_ROOF - 0.22), material("Headliner", base=(0.13, 0.08, 0.07), rough=0.9, wear=0.0), bevel=0)
    for sx in (-1, 1):
        box(f"WheelWell{sx}", (2.2, 4.0, 0.9), (sx * 2.95, RY, 3.05), lacq_in, bevel=0.2, segments=3)
    # the stairwell: two steps with brass nosings, a grab pole, a modesty panel at the top
    box("Step1", (0.65, 2.9, 0.5), (3.775, -8.4, 1.65), rubber, bevel=0.02)
    box("Step2", (0.7, 2.9, 1.0), (3.1, -8.4, 1.9), rubber, bevel=0.02)
    for x, z in ((4.04, 1.93), (3.41, 2.43), (2.72, 2.93)):
        box(f"Nosing{x}", (0.12, 2.9, 0.06), (x, -8.4, z), brass, bevel=0.01)
    tube("GrabPole", [Vector((2.75, -7.05, 1.95)), Vector((2.75, -7.05, Z_WTOP - 0.1))], 0.06, brass)
    tube("GrabRail", [Vector((3.9, -9.75, 3.2)), Vector((3.9, -9.75, 7.8))], 0.05, brass)
    box("BarrierR", (3.0, 0.1, 2.6), (2.45, -6.55, Z_FLOOR + 1.3), lacq_in, bevel=0.03)
    box("BarrierL", (3.0, 0.1, 2.6), (-2.45, -6.25, Z_FLOOR + 1.3), lacq_in, bevel=0.03)
    for x in (2.45, -2.45):
        tube(f"BarrierTop{x}", [Vector((x - 1.5, -6.55 if x > 0 else -6.25, Z_FLOOR + 2.65)), Vector((x + 1.5, -6.55 if x > 0 else -6.25, Z_FLOOR + 2.65))], 0.05, nickel)
    # the fare box
    cyl("FarePost", 0.14, 2.5, (1.95, -9.3, Z_FLOOR + 1.25), nickel, verts=12, bevel=0.02)
    box("FareBox", (0.7, 0.55, 0.95), (1.95, -9.3, 5.85), brass, bevel=0.06)
    box("FareSlot", (0.3, 0.05, 0.04), (1.95, -9.3, 6.33), void, bevel=0)
    # the cab: dash with three pale gauges, the column and the big tilted wheel, the gear lever, pedals, the mirror
    box("Dash", (5.4, 0.6, 0.9), (-1.3, -9.65, 5.85), lacq_in, bevel=0.08)
    c = Vector((DX, -9.0, 6.3))
    nrm = Vector((0, 0.45, 0.89)).normalized()
    u = Vector((1, 0, 0))
    t = nrm.cross(u).normalized()                             # up the wheel's face, toward the windshield
    if t.y > 0:
        t = -t
    rim = [c + (u * math.cos(2 * math.pi * k / 20) + t * math.sin(2 * math.pi * k / 20)) * 0.8 for k in range(20)]
    tube("WheelRim", rim, 0.07, rubber, closed=True, res=2)
    for k in range(3):
        a = math.pi / 2 + 2 * math.pi * k / 3
        tube(f"Spoke{k}", [c, c + (u * math.cos(a) + t * math.sin(a)) * 0.78], 0.035, nickel)
    tube("Column", [c, c - nrm * 0.1 + Vector((0, -0.75, -1.2))], 0.09, lacq_in)
    cyl("Hub", 0.15, 0.1, tuple(c), nickel, rot=(-math.atan2(nrm.y, nrm.z), 0, 0), verts=16, bevel=0.02)
    tube("GearLever", [Vector((-0.9, -8.4, Z_FLOOR)), Vector((-0.86, -8.8, 5.0))], 0.04, nickel)
    sphere("GearKnob", 0.13, (-0.86, -8.8, 5.05), crimson, seg=12, rings=8)
    for sx in (-1, 1):
        box(f"Pedal{sx}", (0.3, 0.12, 0.45), (DX + sx * 0.35, -9.45, 3.25), nickel, bevel=0.02, rot=(0.5, 0, 0))
    box("CabMirror", (2.4, 0.1, 0.35), (-0.8, -9.75, 9.15), nickel, bevel=0.04)
    box("Visor", (2.0, 0.8, 0.08), (DX, -9.45, 9.55), leather, bevel=0.03, rot=(0.2, 0, 0))
    set_group("Glow")
    for k, x in enumerate((DX - 0.7, DX, DX + 0.7)):
        cyl(f"Gauge{k}", 0.16, 0.03, (x, -9.33, 6.0), gauge, rot=(math.pi / 2, 0, 0), verts=16, bevel=0)
    for y in (-4.0, 1.6, 7.2, 12.8):
        sphere(f"Dome{y}", 0.32, (0, y, Z_ROOF - 0.3), amber, seg=16, rings=8, scale=(1.6, 1.0, 0.35))
    set_group("Interior")
    for k, x in enumerate((DX - 0.7, DX, DX + 0.7)):
        ob = lathe(f"GaugeRim{k}", [(0.15, -0.03), (0.21, -0.03), (0.21, 0.04), (0.15, 0.04)], nickel, seg=16, loc=(0, 0, 0))
        ob.rotation_euler = (-math.pi / 2, 0, 0)
        ob.location = (x, -9.36, 6.0)
    for y in (-4.0, 1.6, 7.2, 12.8):
        ob = lathe(f"DomeRing{y}", [(0.45, 0.0), (0.56, 0.0), (0.53, 0.08), (0.45, 0.08)], brass, seg=20, loc=(0, y, Z_ROOF - 0.3))
        ob.scale = (1.6, 1.0, 1.0)
    # the driver's seat
    cyl("DSeatPost", 0.22, 1.1, (DX, DY, Z_FLOOR + 0.55), nickel, verts=12, bevel=0.02)
    box("DSeat", (1.7, 1.6, 0.45), (DX, DY, 4.2), leather, bevel=0.15, segments=3)
    box("DSeatBack", (1.7, 0.35, 2.7), (DX, -6.75, 5.75), leather, bevel=0.15, segments=3, rot=(-0.12, 0, 0))
    # the passengers' benches: eight rows a side, crimson leather on nickel, a grab bar along every back
    for k in range(8):
        y = -5.3 + k * PITCH
        for sx in (-1, 1):
            xc = sx * 2.45
            box(f"Cushion{k}{sx}", (3.0, 1.4, 0.45), (xc, y, 4.2), leather, bevel=0.14, segments=2)
            box(f"Back{k}{sx}", (3.0, 0.32, 2.3), (xc, y + 0.82, 5.55), leather, bevel=0.12, segments=2, rot=(-0.1, 0, 0))
            if not (RY - 2.1 < y - 0.55 < RY + 2.1):                  # no skirt where the wheel well rises
                box(f"Skirt{k}{sx}", (2.9, 0.08, 1.0), (xc, y - 0.55, 3.45), lacq_in, bevel=0)
            tube(f"GrabBar{k}{sx}", [Vector((xc - 1.45, y + 0.95, 6.75)), Vector((xc + 1.45, y + 0.95, 6.75))], 0.045, nickel, res=2)
            tube(f"Leg{k}{sx}", [Vector((sx * 1.05, y, Z_FLOOR)), Vector((sx * 1.05, y, 3.98))], 0.05, nickel, res=2)
    # someone left their satchel on row six
    ys = -5.3 + 5 * PITCH
    box("Satchel", (0.95, 0.42, 0.72), (-3.0, ys, 4.8), brown, bevel=0.1, segments=3)
    box("SatchelFlap", (0.97, 0.06, 0.45), (-3.0, ys - 0.23, 4.98), brown, bevel=0.04, rot=(0.12, 0, 0))
    box("SatchelBuckle", (0.14, 0.04, 0.14), (-3.0, ys - 0.27, 4.82), brass, bevel=0.02)
    tube("SatchelStrap", [Vector((-3.45, ys, 5.12)), Vector((-3.2, ys - 0.1, 5.6)), Vector((-2.8, ys - 0.1, 5.6)), Vector((-2.55, ys, 5.12))], 0.04, brown)

    # ---- the driver --------------------------------------------------------------------------------------------
    from nh_props_batch33 import Skel
    from nh_props_batch34 import chain
    S = Skel()
    hip = S.add(Vector((DX, DY + 0.05, 4.78)), 0.5)
    tor = chain(S, [Vector((DX, DY - 0.05, 6.1)), Vector((DX, DY - 0.2, 7.35))], [0.47, 0.5], hip)
    chain(S, [Vector((DX, DY - 0.28, 7.85))], [0.17], tor[1])
    hands = []
    for sx in (-1, 1):
        hand = c + (u * sx * 0.87 + t * 0.5) * 0.8
        hands.append(hand)
        chain(S, [Vector((DX + sx * 0.62, DY - 0.22, 7.25)), Vector((DX + sx * 0.82, DY - 0.95, 6.5)), hand - Vector((0, -0.12, 0.02))], [0.2, 0.15, 0.11], tor[1])
        chain(S, [Vector((DX + sx * 0.33, DY - 1.15, 4.85)), Vector((DX + sx * 0.36, -9.25, 3.15))], [0.23, 0.15], hip)
    set_group("Driver")
    S.build("Driver", coat, subdiv=1, knobs=0.02)
    for i, hd in enumerate(hands):
        sphere(f"Glove{i}", 0.15, tuple(hd), coat, seg=12, rings=8, scale=(1, 1.2, 0.8))
    for sx in (-1, 1):
        sphere(f"Boot{sx}", 0.2, (DX + sx * 0.36, -9.4, 3.1), rubber, seg=12, rings=8, scale=(0.9, 1.6, 0.7))
    cone("Collar", 0.36, 0.5, 0.55, (DX, DY - 0.27, 7.9), coat, verts=20)
    set_group("DriverHead")
    hc = Vector((DX, DY - 0.3, 8.3))
    sphere("Head", 0.4, tuple(hc), void, seg=16, rings=10, scale=(0.85, 0.9, 1.08))
    cyl("CapBand", 0.43, 0.24, (hc.x, hc.y, hc.z + 0.36), coat, verts=24, bevel=0.03)
    lathe("CapCrown", [(0.0, 0.0), (0.44, 0.0), (0.53, 0.18), (0.52, 0.26), (0.0, 0.28)], coat, seg=24, loc=(hc.x, hc.y + 0.04, hc.z + 0.48))
    box("CapPeak", (0.8, 0.55, 0.05), (hc.x, hc.y - 0.5, hc.z + 0.3), material("CapPeak", base=(0.01, 0.01, 0.012), rough=0.15, wear=0.1), bevel=0.04, rot=(0.25, 0, 0))
    box("CapBadge", (0.2, 0.04, 0.16), (hc.x, hc.y - 0.42, hc.z + 0.5), brass, bevel=0.01)
    set_group("DriverEyes_Glow")
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.045, (hc.x + sx * 0.13, hc.y - 0.34, hc.z + 0.02), eye, seg=8, rings=6)
    set_group("Main")

    # ---- the folding doors: two leaves, nickel-edged, glazed top and bottom, a rubber seal where they meet --------
    for nm, (ya, yb) in (("DoorA", (-9.88, -8.42)), ("DoorB", (-8.38, -6.92))):
        set_group(nm)
        yc, w = (ya + yb) / 2, yb - ya
        x = XS + 0.12
        for yy in (ya + 0.09, yb - 0.09):
            box(f"{nm}Stile{yy:.2f}", (0.1, 0.18, 7.6), (x, yy, 5.5), lacq, bevel=0.03)
        for z, h in ((9.2, 0.2), (4.95, 0.3), (2.3, 1.2)):
            box(f"{nm}Rail{z}", (0.1, w, h), (x, yc, z), lacq, bevel=0.03)
        box(f"{nm}Kick", (0.03, w - 0.2, 1.0), (x + 0.06, yc, 2.3), brass, bevel=0.01)
        box(f"{nm}Seal", (0.14, 0.07, 7.6), (x, yb if nm == "DoorA" else ya, 5.5), rubber, bevel=0.02)
        box(f"{nm}Handle", (0.06, 0.08, 0.9), (x - 0.08, yc, 6.2), nickel, bevel=0.02)
        set_group(f"{nm}_Glass")
        box(f"{nm}PaneUp", (0.04, w - 0.3, 3.9), (x, yc, 7.1), glass, bevel=0)
        box(f"{nm}PaneLo", (0.04, w - 0.3, 1.7), (x, yc, 3.95), glass, bevel=0)
    set_group("Main")

    # ---- the wipers (parked flat along the bottom of the screen) ---------------------------------------------------
    for nm, px in (("WiperL", -3.3), ("WiperR", 0.6)):
        set_group(nm)
        cyl(f"{nm}Pivot", 0.08, 0.15, (px, -10.25, 6.6), nickel, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
        tube(f"{nm}Arm", [Vector((px, -10.3, 6.6)), Vector((px + 2.2, -10.3, 6.7))], 0.035, rubber)
        box(f"{nm}Blade", (1.8, 0.06, 0.07), (px + 1.3, -10.25, 6.72), rubber, bevel=0.01)
    set_group("Main")

    # ---- the wheels ----------------------------------------------------------------------------------------------
    rimmat = material("WheelCrimson", "NH_PaintedMetal", tint=(0.32, 0.03, 0.045), scale=1.0, wear=0.5, wear_metal=True, dirt=1.0)
    for nm, (x, y) in WHEELS.items():
        _wheel(nm, x, y, rubber, rimmat, nickel, dual=(y == RY))
    set_group("Main")

    # ---- the rig ---------------------------------------------------------------------------------------------------
    bones = {"Body": ((0, 0, WR), (0, 0, WR + 1.0), None),
             "DoorA": ((XS + 0.12, -9.88, 1.7), (XS + 0.12, -9.88, 2.7), "Body"),
             "DoorB": ((XS + 0.12, -6.92, 1.7), (XS + 0.12, -6.92, 2.7), "Body"),
             "WiperL": ((-3.3, -10.25, 6.6), (-3.3, -9.75, 6.6), "Body"),
             "WiperR": ((0.6, -10.25, 6.6), (0.6, -9.75, 6.6), "Body"),
             "DriverHead": ((DX, DY - 0.28, 7.8), (DX, DY - 0.28, 8.6), "Body")}
    own = {g: "Body" for g in BODY_GROUPS}
    own.update({"DoorA": "DoorA", "DoorA_Glass": "DoorA", "DoorB": "DoorB", "DoorB_Glass": "DoorB",
                "WiperL": "WiperL", "WiperR": "WiperR", "DriverHead": "DriverHead", "DriverEyes_Glow": "DriverHead"})
    for nm, (x, y) in WHEELS.items():
        bones[nm] = ((x, y, WR), (x, y, WR + 0.5), None)
        own[nm] = nm
    B49.RIG["WFBlackBus"] = dict(bones=bones, own=own)
    return (W_ + 3.0, 35.5, 11.8)


def _brake(t, dur, w0):
    """degrees turned by a wheel slowing evenly from w0 deg/s to a stop over dur"""
    tt = max(0.0, min(t, dur))
    return w0 * tt - 0.5 * (w0 / dur) * tt * tt


def _pitch_stop(t):
    if t < 1.4:
        return 2.2 * ease(t / 1.4)
    return 2.2 * (1 - back_out((t - 1.4) / 0.7, 2.2))


BUS_CLIPS = {
    # the last few yards: the wheels slow to a stop, the nose dips on the brakes, rocks back past level, settles
    "BrakeStop": dict(length=2.4, keys={
        "Body": lambda t: ([("x", _pitch_stop(t))], (0, 0, -0.05 * math.sin(math.pi * min(1.0, t / 2.1)))),
        **{n: (lambda t: ("x", -_brake(t, 1.4, 330), (0, 0, 0))) for n in WHEELS}}),
    # the engine ticking over: a fine shudder and a slow roll (whole cycles, so it loops clean)
    "EngineIdle": dict(length=2.0, loop=True, keys={
        "Body": lambda t: ([("y", 0.18 * math.sin(2 * math.pi * 6 * t / 2.0)), ("x", 0.08 * math.sin(2 * math.pi * 2 * t / 2.0))],
                           (0, 0, 0.012 * math.sin(2 * math.pi * 12 * t / 2.0)))}),
    # the hiss: a shudder, then both leaves fold out at once, a little overshoot, settle
    "DoorsOpen": dict(length=1.4, keys={
        "DoorA": lambda t: ("z", -88 * back_out((t - 0.3) / 0.6, 1.2) + 1.2 * math.sin(t * 70) * (t < 0.3), (0, 0, 0)),
        "DoorB": lambda t: ("z", 88 * back_out((t - 0.3) / 0.6, 1.2) - 1.2 * math.sin(t * 70) * (t < 0.3), (0, 0, 0))}),
    # shut behind you: quick, then two small bounces against the seals (never through them)
    "DoorsClose": dict(length=0.9, keys={
        "DoorA": lambda t: ("z", -88 * (1 - ease(t / 0.45)) - 3.0 * math.exp(-(t - 0.45) * 8) * abs(math.sin((t - 0.45) * 30)) * (t > 0.45), (0, 0, 0)),
        "DoorB": lambda t: ("z", 88 * (1 - ease(t / 0.45)) + 3.0 * math.exp(-(t - 0.45) * 8) * abs(math.sin((t - 0.45) * 30)) * (t > 0.45), (0, 0, 0))}),
    "WipersSweep": dict(length=2.4, loop=True, keys={
        "WiperL": lambda t: ("y", -95 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 2.4)), (0, 0, 0)),
        "WiperR": lambda t: ("y", -95 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 2.4)), (0, 0, 0))}),
    # he turns his head to you: a long still beat, then a slow turn and a slight tilt, and he holds it
    "DriverTurn": dict(length=4.0, keys={
        "DriverHead": lambda t: ([("z", 62 * ease((t - 1.0) / 2.2)), ("x", -7 * ease((t - 1.4) / 2.0))], (0, 0, 0))}),
    # away into the fog: the wheels wind up, the body squats back, then levels
    "PullAway": dict(length=2.0, keys={
        "Body": lambda t: ([("x", -1.6 * ease(t / 0.6) + 1.2 * ease((t - 0.6) / 1.0))], (0, 0, 0)),
        **{n: (lambda t: ("x", -0.5 * 220 * t * t, (0, 0, 0))) for n in WHEELS}}),
}


# ================================================================== the bus stop

def _blob(cx, cy, r, seed, n=18):
    rr = random.Random(seed)
    return [(cx + r * (1 + rr.uniform(-0.25, 0.2)) * math.cos(2 * math.pi * k / n),
             cy + r * 0.7 * (1 + rr.uniform(-0.25, 0.2)) * math.sin(2 * math.pi * k / n)) for k in range(n)]


def bus_stop(M):
    K = kit(M)
    rr = random.Random(5201)
    green = material("StopGreen", "NH_PaintedMetal", tint=(0.1, 0.24, 0.15), scale=1.0, rough_add=0.08, wear=0.55, wear_metal=True, dirt=1.0)
    galv = material("Galvanised", base=(0.55, 0.56, 0.56), rough=0.45, metal=0.8, wear=0.3, dirt=1.0)
    iron = K["iron"]
    wood = material("BenchWood", "NH_DeskWood", tint=(0.42, 0.28, 0.17), scale=0.3, rough_add=0.15, wear=0.65, dirt=1.0)
    asphalt = material("WetAsphalt", "NH_Slate", tint=(0.2, 0.2, 0.22), scale=0.5, rough_mul=0.45, wear=0.1, dirt=1.0)
    granite = material("Granite", "NH_Limestone", tint=(0.5, 0.5, 0.52), scale=0.4, rough_mul=0.6, wear=0.4, dirt=1.0)
    slabs = [material(f"Slab{k}", "NH_Limestone", tint=tint, scale=0.35, rough_mul=0.55, wear=0.3, dirt=1.0)
             for k, tint in enumerate(((0.58, 0.57, 0.55), (0.52, 0.51, 0.5), (0.62, 0.6, 0.57)))]
    puddle = material("Puddle", base=(0.015, 0.018, 0.024), rough=0.02, wear=0.0, dirt=0.0)
    yellow = material("RoadYellow", base=(0.85, 0.65, 0.12), rough=0.6, wear=0.6, dirt=1.0)
    roofglass = material("RoofSmoke", base=(0.12, 0.14, 0.13), rough=0.1, wear=0.0, dirt=1.0)
    clear = material("StopGlass", base=(0.5, 0.55, 0.55), rough=0.05, wear=0.0, dirt=0.8)
    cold = material("TubeCold", base=(0.85, 0.95, 1.0), rough=0.3, wear=0.0, dirt=0.0)
    set_group("Main")

    # ---- ground: a slice of wet road, the gutter, the kerb, slab paving ---------------------------------------
    box("Road", (20.0, 4.8, 0.3), (0, -5.6, 0.15), asphalt, bevel=0)
    box("Gutter", (20.0, 0.5, 0.04), (0, -3.45, 0.31), granite, bevel=0)
    box("Kerb", (20.0, 0.6, 0.75), (0, -2.9, 0.375), granite, bevel=0.07)
    box("PaveBase", (20.0, 6.8, 0.6), (0, 0.8, 0.3), granite, bevel=0)
    for i in range(10):
        for j in range(3):
            box(f"Slab{i}{j}", (1.96, 2.23, 0.15), (-9.0 + i * 2.0, -1.47 + j * 2.27, 0.675 + rr.uniform(-0.008, 0.008)), slabs[(i * 7 + j * 3) % 3], bevel=0.03)
    # the bus box: two yellow lines and the ends
    box("BoxLineK", (18.0, 0.18, 0.012), (0, -3.95, 0.306), yellow, bevel=0)
    box("BoxLineR", (18.0, 0.18, 0.012), (0, -7.6, 0.306), yellow, bevel=0)
    for sx in (-1, 1):
        box(f"BoxEnd{sx}", (0.18, 3.83, 0.012), (sx * 9.0, -5.77, 0.306), yellow, bevel=0)
    # the drain, a puddle in the road where the bus will splash, another on the pavement
    box("DrainFrame", (1.6, 0.6, 0.05), (-2.6, -3.48, 0.335), iron, bevel=0.01)
    dvoid = material("DrainVoid", base=(0.0, 0.0, 0.0), rough=1.0, wear=0.0, dirt=0.0)
    for k in range(6):
        box(f"DrainSlot{k}", (0.12, 0.42, 0.02), (-3.2 + k * 0.24, -3.48, 0.36), dvoid, bevel=0)
    prism("PuddleRoad", _blob(3.0, -4.4, 1.5, 11), 0.3, 0.015, puddle, plane="XY")
    prism("PuddlePave", _blob(-6.1, 2.3, 0.7, 12), 0.75, 0.012, puddle, plane="XY")

    # ---- the shelter frame: posts on bolted plates, brackets, beams, arched ribs under the smoked roof ---------
    zr = lambda y: 9.1 + 0.65 * math.sin(math.pi * (y + 1.4) / 4.8) + 0.35 * (y + 1.4) / 4.8
    for x in (-4.6, 4.6):
        for y in (0.0, 2.9):
            box(f"Post{x}{y}", (0.32, 0.32, 8.6), (x, y, 5.05), green, bevel=0.04)
            box(f"Plate{x}{y}", (0.8, 0.8, 0.06), (x, y, 0.78), green, bevel=0.02)
            for bx in (-0.28, 0.28):
                for by in (-0.28, 0.28):
                    cyl(f"Bolt{x}{y}{bx}{by}", 0.05, 0.08, (x + bx, y + by, 0.84), galv, verts=6, bevel=0)
        tube(f"Bracket{x}", [Vector((x, 0.0, 8.7)), Vector((x, -1.15, 8.7))], 0.08, green, square=True)
        tube(f"Brace{x}", [Vector((x, 0.0, 7.8)), Vector((x, -1.1, 8.5))], 0.06, green, square=True)
    box("FasciaBeam", (10.0, 0.25, 0.85), (0, -1.25, 8.72), green, bevel=0.04)
    canvas("Band", "Band", (8.8, 0.02, 0.76), (0, -1.385, 8.72), K)
    box("BackBeam", (9.6, 0.25, 0.5), (0, 2.9, 9.2), green, bevel=0.04)
    for x in (-4.6, -1.55, 1.55, 4.6):
        tube(f"Rib{x}", [Vector((x, -1.35 + 4.7 * k / 12, zr(-1.35 + 4.7 * k / 12) - 0.12)) for k in range(13)], 0.09, green, square=True)
    tube("GutterF", [Vector((-5.25, -1.53, 9.02)), Vector((5.25, -1.53, 9.02))], 0.13, galv)
    tube("Downpipe", [Vector((5.2, -1.53, 9.0)), Vector((5.2, -1.53, 1.15)), Vector((5.2, -1.85, 0.86))], 0.09, galv)
    set_group("Glass")
    drape("RoofSheet", -5.2, 5.2, -1.45, 3.45, lambda x, y: zr(y), roofglass, nu=6, nv=16, thick=0.08)
    # three glazed bays along the back, a glazed end on the right
    for k, xc in enumerate((-3.07, 0.0, 3.07)):
        box(f"BackPane{k}", (2.9, 0.05, 7.3), (xc, 2.9, 5.0), clear, bevel=0)
    box("EndPaneR", (0.05, 2.58, 7.3), (4.6, 1.45, 5.0), clear, bevel=0)
    box("EndPaneL", (0.05, 2.58, 7.3), (-4.6, 1.45, 5.0), clear, bevel=0)
    set_group("Main")
    for x in (-1.55, 1.55):
        box(f"Mullion{x}", (0.18, 0.18, 7.9), (x, 2.9, 4.82), green, bevel=0.03)
    for z, h in ((1.2, 0.3), (8.75, 0.25)):
        box(f"BackRail{z}", (9.2, 0.2, h), (0, 2.9, z), green, bevel=0.03)
        for x in (-4.6, 4.6):
            box(f"EndRail{x}{z}", (0.2, 2.6, h), (x, 1.45, z), green, bevel=0.03)

    # ---- the timetable in its locked case on the left bay ---------------------------------------------------------
    box("CaseFrame", (1.9, 0.12, 2.5), (-3.07, 2.78, 5.55), green, bevel=0.04)
    canvas("Timetable", "Timetable", (1.5, 0.02, 2.0), (-3.07, 2.71, 5.55), K)
    set_group("Glass")
    box("CaseGlass", (1.7, 0.03, 2.3), (-3.07, 2.68, 5.55), clear, bevel=0)
    set_group("Main")
    box("CaseLock", (0.1, 0.06, 0.18), (-2.2, 2.68, 5.55), K["brass"], bevel=0.02)

    # ---- the ad case, outside the left end, lit from inside -------------------------------------------------------
    box("AdCase", (0.4, 2.6, 4.0), (-4.95, 1.45, 4.6), green, bevel=0.05)
    canvas("AdOut", "AdOut", (0.02, 2.2, 3.3), (-5.162, 1.45, 4.6), K, face="-X")
    set_group("Glass")
    box("AdGlass", (0.03, 2.35, 3.5), (-5.19, 1.45, 4.6), clear, bevel=0)
    set_group("Glow")
    box("AdLight", (0.04, 2.2, 0.06), (-5.17, 1.45, 6.32), cold, bevel=0)
    set_group("Main")
    for y in (0.4, 2.5):
        box(f"AdLeg{y}", (0.2, 0.2, 2.6), (-4.95, y, 1.95), green, bevel=0.03)

    # ---- the bench: slats on three cast-iron brackets, two armrest dividers ---------------------------------------
    for k, y in enumerate((1.6, 1.9, 2.2, 2.5)):
        box(f"SeatSlat{k}", (6.4, 0.26, 0.12), (0, y, 2.3), wood, bevel=0.03)
    for k, z in enumerate((3.0, 3.45)):
        box(f"BackSlat{k}", (6.4, 0.1, 0.3), (0, 2.72, z), wood, bevel=0.03)
    for x in (-3.0, 0.0, 3.0):
        box(f"LegF{x}", (0.12, 0.12, 1.5), (x, 1.55, 1.5), iron, bevel=0.02)
        box(f"LegB{x}", (0.12, 0.12, 2.95), (x, 2.62, 2.22), iron, bevel=0.02)
        box(f"SeatArm{x}", (0.12, 1.2, 0.1), (x, 2.05, 2.19), iron, bevel=0.02)
        box(f"Foot{x}", (0.3, 1.3, 0.05), (x, 2.08, 0.78), iron, bevel=0.01)
        tube(f"Scroll{x}", [Vector((x, 1.55, 1.2)), Vector((x, 1.75, 1.6)), Vector((x, 2.1, 1.75)), Vector((x, 2.55, 1.6))], 0.04, iron)
    for x in (-1.6, 1.6):
        tube(f"Divider{x}", [Vector((x, 1.55, 2.37)), Vector((x, 1.62, 2.85)), Vector((x, 2.15, 3.0)), Vector((x, 2.62, 2.9))], 0.05, iron)

    # ---- the caged tube lamp under the roof, its conduit down the back-right post --------------------------------
    for x in (-1.2, 1.2):
        tube(f"LampRod{x}", [Vector((x, 0.9, 8.83)), Vector((x, 0.9, zr(0.9) - 0.05))], 0.03, galv)
    box("LampHousing", (3.4, 0.6, 0.25), (0, 0.9, 8.7), green, bevel=0.05)
    for k in range(7):
        tube(f"Cage{k}", [Vector((-1.5 + k * 0.5, 0.65, 8.58)), Vector((-1.5 + k * 0.5, 0.65, 8.42)), Vector((-1.5 + k * 0.5, 1.15, 8.42)), Vector((-1.5 + k * 0.5, 1.15, 8.58))], 0.02, iron)
    set_group("Glow")
    box("LampTube", (3.1, 0.15, 0.15), (0, 0.9, 8.52), cold, bevel=0.03)
    set_group("Main")
    tube("Conduit", [Vector((1.7, 0.9, 8.7)), Vector((1.7, 2.7, 8.7)), Vector((4.38, 2.7, 8.7)), Vector((4.38, 2.7, 1.9))], 0.045, galv)
    box("JunctionBox", (0.3, 0.25, 0.5), (4.36, 2.66, 1.7), galv, bevel=0.03)

    # ---- the flag pole: the stop sign both ways, the bin -----------------------------------------------------------
    PX, PY = -7.2, -1.9
    cyl("Pole", 0.11, 11.2, (PX, PY, 6.35), galv, verts=12, bevel=0.01)
    sphere("PoleCap", 0.14, (PX, PY, 11.95), galv, seg=10, rings=6, scale=(1, 1, 0.6))
    box("SignFrame", (0.1, 2.2, 2.85), (PX, PY + 1.25, 10.4), green, bevel=0.04)
    canvas("SignA", "SignA", (0.02, 2.0, 2.65), (PX - 0.06, PY + 1.25, 10.4), K, face="-X")
    canvas("SignB", "SignB", (0.02, 2.0, 2.65), (PX + 0.06, PY + 1.25, 10.4), K, face="+X")
    for z in (9.3, 11.5):
        box(f"Clamp{z}", (0.26, 0.42, 0.15), (PX, PY + 0.16, z), galv, bevel=0.03)
    lathe("Bin", [(0.0, 0.0), (0.55, 0.0), (0.62, 1.6), (0.66, 1.66), (0.6, 1.7), (0.55, 0.08), (0.0, 0.08)], green, seg=24, loc=(PX + 0.85, PY, 2.6))
    for z in (2.9, 3.9):
        box(f"BinBand{z}", (0.5, 0.12, 0.12), (PX + 0.25, PY, z), galv, bevel=0.02)
    sphere("BinTrash", 0.32, (PX + 0.85, PY, 4.1), material("BinBag", base=(0.04, 0.04, 0.045), rough=0.35, wear=0.0), seg=10, rings=6, scale=(1, 1, 0.5))
    sphere("Crumple", 0.16, (PX + 0.95, PY - 0.1, 4.3), material("Crumple", base=(0.85, 0.82, 0.74), rough=0.9, wear=0.0), seg=8, rings=5, scale=(1.1, 0.9, 0.8))

    # ---- wet autumn leaves, weeds in the joints, litter, a soggy copy of THE PLAN ---------------------------------
    lmats = [material(f"WetLeaf{k}", base=b, rough=0.3, wear=0.0, dirt=0.5) for k, b in enumerate(((0.45, 0.13, 0.03), (0.6, 0.38, 0.06), (0.25, 0.12, 0.05)))]
    spots = [(rr.uniform(-9.5, 9.5), rr.uniform(-2.4, 4.0), 0.76) for _ in range(16)] + [(rr.uniform(-9.5, 9.5), rr.uniform(-3.65, -3.25), 0.33) for _ in range(10)]
    for k, (x, y, z) in enumerate(spots):
        if abs(abs(x) - 4.6) < 0.6 and (abs(y) < 0.6 or abs(y - 2.9) < 0.6):
            continue
        leaf(f"Leaf{k}", (x, y, z), rr.uniform(0, 2 * math.pi), 0.03, rr.uniform(0.32, 0.5), 0.15, 0.02, lmats[k % 3], n=6)
    weed = material("Weed", base=(0.14, 0.24, 0.07), rough=0.6, wear=0.0)
    for k in range(7):
        leaf(f"Weed{k}", (-8.0 + 0.05 * k, -2.6 + 0.02 * k, 0.74), 2 * math.pi * k / 7, 1.0 + 0.05 * k, 0.45, 0.05, 0.2, weed, n=6)
    can = cyl("Can", 0.13, 0.32, (1.3, 1.15, 0.88), material("CanRed", base=(0.55, 0.05, 0.05), rough=0.25, metal=0.8, wear=0.4), rot=(math.pi / 2, 0, 0.5), verts=12, bevel=0.02)
    can.scale = (1.0, 1.0, 0.6)
    canvas("Flyer", "Flyer", (0.85, 1.12, 0.01), (-1.7, -1.4, 0.756), K, face="+Z")
    return (20.0, 12.4, 12.4)


# ------------------------------------------------------------------ registration

BUILDERS.update({"WFBusStop": bus_stop, "WFBlackBus": black_bus})
P.CANVAS.update({"WFBusStop_Timetable": "WF_Timetable", "WFBusStop_Band": "WF_ShelterBand", "WFBusStop_SignA": "WF_BusSign",
                 "WFBusStop_SignB": "WF_BusSign", "WFBusStop_AdOut": "WF_PosterBand", "WFBusStop_Flyer": "WF_ThePlan",
                 "WFBlackBus_Blind": "WF_BusBlind", "WFBlackBus_SideL": "WF_BusSide", "WFBlackBus_SideR": "WF_BusSide",
                 "WFBlackBus_Plate": "WF_BusPlate", "WFBlackBus_PlateRear": "WF_BusPlate"})
B49.CLIPS["WFBlackBus"] = BUS_CLIPS
P.RIGS["WFBlackBus"] = lambda objs: B49.rig_pieces("WFBlackBus", objs)
B49.CLIP_CAM["WFBlackBus"] = {
    "BrakeStop": ((24.0, -6.0, 5.0), (0, 0, 4.0)), "EngineIdle": ((18.0, -22.0, 7.0), (0, -6.0, 5.0)),
    "DoorsOpen": ((14.0, -16.0, 6.0), (4.2, -8.4, 5.0)), "DoorsClose": ((14.0, -16.0, 6.0), (4.2, -8.4, 5.0)),
    "WipersSweep": ((0.0, -24.0, 8.5), (0, -10.2, 7.8)), "DriverTurn": ((3.0, -19.0, 8.6), (-2.4, -7.9, 8.2)),
    "PullAway": ((24.0, -6.0, 5.0), (0, 0, 4.0))}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.15 for n in BUILDERS})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        if n in B49.CLIPS:
            B49.clip_strips(n)
