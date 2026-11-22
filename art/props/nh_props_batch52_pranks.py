"""Props batch 52 (2026-11-19): the tutorial's prank sites (docs/expansion/15-Tutorial-The-Last-Normal-Night.md §6).

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch52_pranks.py -- <Prop|all> [--size 2048] [--samples 64] [--gpu]

WFChetTruck  Chet's pickup (the Combat prank): an original 1970s-style full-size pickup, 17 long, two-tone faded red over
             cream, rust blooms and a dent in the bed side, wheel arches cut into the body (boolean), a chrome grille and
             bumpers, round headlights (Glow), a bench-seat cab, a toolbox and a spare tyre in the bed, a bumper sticker
             (HONK IF YOU LOVE WICKFIELD). Rigged: Body (the suspension), DoorL, Tailgate, the four Tyres (they bulge flat).
             Clips: TyresDeflate (the body sags onto its rims, a tired bounce), DoorOpen, TailgateDrop.

Front faces -Y, Z up, origin at the bottom centre.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube, set_group, material, _finish  # noqa: E402
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import lathe, prism, _dims  # noqa: E402
from nh_props_batch28 import solid  # noqa: E402
import nh_props_batch49_hometown as B49  # noqa: E402
from nh_props_batch49_hometown import kit, wmat, wall, ease, back_out  # noqa: E402

BUILDERS = {}


def _cutter(name, r, depth, loc, rot):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=depth, location=loc, rotation=rot)
    c = bpy.context.active_object
    c.name = name
    c.hide_render = True
    c.display_type = "WIRE"
    return c


def _cut(ob, cutters):
    for c in cutters:
        if not c.data.materials:
            c.data.materials.append(ob.data.materials[0])
        md = ob.modifiers.new(f"Cut{c.name}", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.object = c
        md.solver = "EXACT"
        md.material_mode = "INDEX"
    # booleans first, then the bevel
    for md in list(ob.modifiers):
        if md.type == "BEVEL":
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_move_to_index(modifier=md.name, index=len(ob.modifiers) - 1)


def chet_truck(M):
    K = kit(M)
    red = wmat("TruckRed", "NH_Enamel", (0.5, 0.09, 0.07), 0.5, wear=0.55, dirt=1.0)
    cream = wmat("TruckCream", "NH_Enamel", (0.86, 0.8, 0.66), 0.5, wear=0.5, dirt=1.0)
    chrome = material("TruckChrome", base=(0.85, 0.85, 0.87), rough=0.12, metal=1.0, wear=0.35, dirt=0.6)
    rubber = material("Tyre", base=(0.04, 0.04, 0.045), rough=0.85, wear=0.0, dirt=0.8)
    rust = material("Rust", base=(0.34, 0.16, 0.07), rough=0.9, metal=0.3, wear=0.0, dirt=1.0)
    vinyl = material("SeatVinyl", base=(0.45, 0.32, 0.22), rough=0.5, wear=0.3)
    W, WR = 6.6, 1.35
    FX, BY = -5.2, 4.6                              # front and rear axle y
    xs = W / 2
    cutters = [_cutter(f"Arch{y}", WR + 0.25, W + 1.0, (0, y, WR + 0.1), (0, math.pi / 2, 0)) for y in (FX, BY)]
    # ---- the body: the hood and front fenders, the cab, the bed sides (red above a cream lower band)
    set_group("Body")
    hood = [(-8.3, 1.4), (-8.4, 3.3), (-8.1, 3.75), (-3.7, 4.05), (-3.6, 3.0), (-3.6, 1.4)]
    ob = prism("Hood", [(y, z) for y, z in hood], 0.0, W, red, plane="YZ", bevel=0.18)
    _cut(ob, cutters)
    cab = [(-3.6, 1.4), (-3.6, 4.05), (-2.35, 6.05), (0.55, 6.1), (0.75, 4.0), (0.8, 1.4)]
    prism("Cab", cab, 0.0, W - 0.1, red, plane="YZ", bevel=0.2)
    lower = [(-8.35, 1.15), (-8.35, 2.25), (8.35, 2.25), (8.35, 1.15)]
    ob = prism("Rocker", lower, 0.0, W + 0.04, cream, plane="YZ", bevel=0.08)
    _cut(ob, cutters)
    for sx in (-1, 1):                                    # the bed sides, with a dent and a rust bloom on the right
        side = [(1.0, 1.4), (1.0, 4.0), (8.3, 4.0), (8.3, 1.4)]
        ob = prism(f"BedSide{sx}", side, sx * (xs - 0.15), 0.3, red, plane="YZ", bevel=0.08)
        _cut(ob, cutters)
        box(f"BedRail{sx}", (0.45, 7.4, 0.2), (sx * (xs - 0.15), 4.65, 4.05), red, bevel=0.06)
    sphere("Dent", 0.7, (xs + 0.05, 6.0, 3.0), rust, seg=12, rings=8, scale=(0.08, 1.0, 0.7))
    sphere("RustA", 0.5, (xs + 0.04, 2.6, 2.05), rust, seg=10, rings=6, scale=(0.06, 1.2, 0.5))
    sphere("RustB", 0.4, (-xs - 0.04, -6.5, 2.1), rust, seg=10, rings=6, scale=(0.06, 1.0, 0.45))
    box("BedFloor", (W - 0.6, 7.3, 0.2), (0, 4.65, 1.6), material("BedLiner", base=(0.12, 0.12, 0.12), rough=0.9, wear=0.2), bevel=0)
    box("BedFront", (W - 0.3, 0.3, 2.6), (0, 1.1, 2.7), red, bevel=0.06)
    # the cab's glass, the pillars' trim, the bench seat (seen through the glass), the mirrors, the handles
    set_group("Glass")
    prism("Windshield", [(-3.45, 4.2), (-2.4, 5.9), (-2.38, 5.95), (-3.5, 4.2)], 0.0, W - 0.8, K["glass"], plane="YZ")
    for sx in (-1, 1):
        prism(f"SideGlass{sx}", [(-3.1, 4.25), (-2.25, 5.85), (0.4, 5.85), (0.55, 4.25)], sx * (xs - 0.05), 0.04, K["glass"], plane="YZ")
    box("BackGlass", (W - 1.6, 0.05, 1.5), (0, 0.78, 5.05), K["glass"], bevel=0)
    set_group("Body")
    box("Seat", (W - 1.0, 1.4, 0.7), (0, -0.4, 3.0), vinyl, bevel=0.15, segments=3)
    box("SeatBack", (W - 1.0, 0.5, 1.8), (0, 0.3, 3.9), vinyl, bevel=0.15, segments=3)
    cyl("Wheel", 0.75, 0.12, (0.9, -2.7, 4.2), K["iron"], rot=(0.5, 0, 0), verts=24, bevel=0.03)
    for sx in (-1, 1):
        box(f"Mirror{sx}", (0.6, 0.15, 0.45), (sx * (xs + 0.55), -3.3, 4.8), chrome, bevel=0.06)
        tube(f"MirrorArm{sx}", [Vector((sx * xs, -3.5, 4.4)), Vector((sx * (xs + 0.5), -3.35, 4.7))], 0.05, chrome)
        box(f"Handle{sx}", (0.1, 0.55, 0.1), (sx * (xs + 0.02), -0.4, 3.75), chrome, bevel=0.03)
    # the front: a chrome grille, round headlights, the bumper; the rear: the bumper, taillights, the sticker
    box("GrilleSurround", (W - 1.0, 0.25, 1.6), (0, -8.45, 2.75), chrome, bevel=0.08)
    for k in range(9):
        box(f"GrilleBar{k}", (W - 1.6, 0.1, 0.07), (0, -8.58, 2.15 + k * 0.15), chrome, bevel=0)
    for sx in (-1, 1):
        cyl(f"LampRing{sx}", 0.5, 0.2, (sx * 2.25, -8.5, 2.85), chrome, rot=(math.pi / 2, 0, 0), verts=24, bevel=0.05)
    box("BumperF", (W + 0.4, 0.6, 0.6), (0, -8.75, 1.35), chrome, bevel=0.15, segments=3)
    box("BumperR", (W + 0.2, 0.6, 0.55), (0, 8.65, 1.35), chrome, bevel=0.15, segments=3)
    box("Sticker", (2.2, 0.03, 0.42), (-1.2, 8.97, 1.35), material("Sticker", base=(0.95, 0.85, 0.2), rough=0.5, wear=0.2), bevel=0)
    for sx in (-1, 1):
        box(f"Taillight{sx}", (0.4, 0.15, 0.9), (sx * (xs - 0.25), 8.4, 3.3), material("TailRed", base=(0.6, 0.02, 0.02), rough=0.2, wear=0.1), bevel=0.05)
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Headlamp{sx}", 0.42, (sx * 2.25, -8.55, 2.85), K["bulb"], seg=16, rings=10, scale=(1, 0.35, 1))
    # the bed: a toolbox across it, a spare tyre lying down
    set_group("Body")
    box("Toolbox", (W - 0.4, 1.2, 0.9), (0, 1.9, 4.45), chrome, bevel=0.08)
    lathe("Spare", [(0.0, 1.71), (1.1, 1.71), (1.25, 1.85), (1.25, 2.3), (1.1, 2.45), (0.0, 2.45)], rubber, seg=28, loc=(-0.8, 5.6, 0))
    # ---- the door (its own piece), the tailgate (its own piece)
    set_group("DoorL")
    prism("DoorPanel", [(-3.4, 2.3), (-3.4, 4.2), (0.6, 4.2), (0.6, 2.3)], xs + 0.08, 0.06, red, plane="YZ", bevel=0.02)
    set_group("Tailgate")
    box("Gate", (W - 0.2, 0.3, 2.6), (0, 8.3, 2.7), red, bevel=0.06)
    box("GateBand", (W - 0.2, 0.32, 0.45), (0, 8.3, 1.7), cream, bevel=0.04)
    box("GateHandle", (0.7, 0.1, 0.2), (0, 8.48, 3.5), chrome, bevel=0.03)
    # ---- the wheels: tyres with a tread, steel rims with a hubcap (each its own piece, so they can flatten)
    for nm, (x, y) in (("FL", (xs - 0.3, FX)), ("FR", (-xs + 0.3, FX)), ("RL", (xs - 0.3, BY)), ("RR", (-xs + 0.3, BY))):
        set_group(f"Tyre{nm}")
        tyre = lathe(f"Tyre{nm}", [(0.85, -0.5), (1.2, -0.52), (WR, -0.42), (WR, 0.42), (1.2, 0.52), (0.85, 0.5)], rubber, seg=36, loc=(0, 0, 0),
                     flute=(36, 0.03))
        tyre.rotation_euler = (0, math.pi / 2, 0)
        tyre.location = (x, y, WR)
        rim = lathe(f"Rim{nm}", [(0.0, -0.3), (0.85, -0.32), (0.88, 0.0), (0.6, 0.12), (0.25, 0.3), (0.0, 0.33)], chrome, seg=24, loc=(0, 0, 0))
        rim.rotation_euler = (0, math.pi / 2 * (1 if x > 0 else -1), 0)
        rim.location = (x, y, WR)
    set_group("Body")
    for c in cutters:
        pass
    # the rig: the body on its suspension, the door, the tailgate, each tyre
    bones = {"Body": ((0, 0, WR), (0, 0, WR + 1.0), None), "DoorL": ((xs + 0.08, -3.4, 2.3), (xs + 0.08, -3.4, 3.3), "Body"),
             "Tailgate": ((0, 8.3, 1.45), (1.0, 8.3, 1.45), "Body")}
    own = {"Body": "Body", "Glass": "Body", "Glow": "Body", "Main": "Body", "DoorL": "DoorL", "Tailgate": "Tailgate"}
    for nm, (x, y) in (("FL", (xs - 0.3, FX)), ("FR", (-xs + 0.3, FX)), ("RL", (xs - 0.3, BY)), ("RR", (-xs + 0.3, BY))):
        bones[f"Tyre{nm}"] = ((x, y, WR), (x, y, WR + 0.5), None)
        own[f"Tyre{nm}"] = f"Tyre{nm}"
    B49.RIG["WFChetTruck"] = dict(bones=bones, own=own)
    return (W + 2, 18.5, 6.4)


CHET_CLIPS = {
    # the tyres go: the body sinks onto its rims in two tired lurches (front then back), a slow bounce, settles low
    "TyresDeflate": dict(length=2.4, keys={
        "Body": lambda t: ([("x", 3.0 * ease((t - 0.3) / 0.5) - 3.0 * ease((t - 0.9) / 0.6) + 0.6 * math.sin(t * 9) * max(0, 1 - (t - 1.5) / 0.9) * (t > 1.5))],
                           (0, 0, -0.32 * back_out((t - 0.3) / 1.2, 0.8) - 0.04 * math.sin(t * 9) * max(0, 1 - (t - 1.5) / 0.9) * (t > 1.5))),
        **{f"Tyre{n}": (lambda t, n=n: ("x", 0, (0, 0, -0.18 * ease((t - (0.3 if n[0] == "F" else 0.9)) / 0.5)))) for n in ("FL", "FR", "RL", "RR")}}),
    "DoorOpen": dict(length=1.0, keys={"DoorL": lambda t: ("z", 62 * back_out(t / 0.7, 1.1), (0, 0, 0))}),
    "TailgateDrop": dict(length=1.0, keys={"Tailgate": lambda t: ("x", 92 * back_out(t / 0.45, 2.2), (0, 0, 0))}),
}


# ================================================================== Wickfield Junior High: the Hall of Fame board

def hall_of_fame(M):
    """a walnut board 10 wide, the gilt title on top, eight brass name rows that each flip (a rig bone per row) to a blank
    brass back where the game writes your name (a SurfaceGui), a brass picture light over it (Glow). Clip FlipToYou: the
    rows cascade over one after another, top to bottom, each with an overshoot; LightsFlicker: the light stutters on"""
    K = kit(M)
    walnut = material("Walnut", "NH_DeskWood", tint=(0.32, 0.19, 0.1), scale=0.3, rough_add=0.05, wear=0.4)
    brass = K["brass"]
    W_, RH, N = 10.0, 0.9, 8
    top = 2.0 + N * RH
    box("Board", (W_ + 0.8, 0.35, top + 2.2), (0, 0.2, (top + 2.2) / 2 + 0.4), walnut, bevel=0.08)
    box("Crown", (W_ + 1.2, 0.6, 0.35), (0, 0.15, top + 2.75), walnut, bevel=0.1)
    box("Ledge", (W_ + 1.0, 0.7, 0.25), (0, 0.1, 0.45), walnut, bevel=0.08)
    set_group("Title")
    box("Title", (W_, 0.02, W_ / 4), (0, -0.0, top + 1.25), K["place"], bevel=0)
    set_group("Main")
    for i in range(N):
        z = top - (i + 0.5) * RH
        set_group("Main")
        box(f"Hinge{i}L", (0.12, 0.2, 0.12), (-W_ / 2 - 0.1, -0.05, z), brass, bevel=0.03)
        box(f"Hinge{i}R", (0.12, 0.2, 0.12), (W_ / 2 + 0.1, -0.05, z), brass, bevel=0.03)
        set_group(f"Row{i}")
        box(f"Row{i}", (W_, 0.02, RH * 0.92), (0, -0.07, z), K["place"], bevel=0)
        set_group(f"RowBack{i}")
        box(f"RowBack{i}", (W_, 0.02, RH * 0.92), (0, -0.04, z), K["place"], bevel=0)
    set_group("Main")
    # the picture light: a brass arm and hood over the top
    for sx in (-1, 1):
        tube(f"LightArm{sx}", [Vector((sx * 2.0, 0.0, top + 2.6)), Vector((sx * 2.0, -0.6, top + 3.2)), Vector((sx * 2.0, -1.1, top + 3.1))], 0.05, brass)
    prism("LightHood", [(-2.6, 0.0), (2.6, 0.0), (2.4, 0.35), (-2.4, 0.35)], -1.15, 0.5, brass, plane="XZ")
    P.PARTS[-1].location = (0, 0, top + 2.95)
    set_group("Glow")
    box("LightTube", (4.6, 0.12, 0.12), (0, -1.15, top + 2.88), K["bulb"], bevel=0.04)
    set_group("Main")
    bones = {"Light": ((0, -1.15, top + 2.88), (1, -1.15, top + 2.88), None)}
    own = {"Glow": "Light"}
    for i in range(N):
        z = top - (i + 0.5) * RH
        bones[f"Row{i}"] = ((-W_ / 2, -0.055, z), (W_ / 2, -0.055, z), None)
        own[f"Row{i}"] = f"Row{i}"
        own[f"RowBack{i}"] = f"Row{i}"
    B49.RIG["WFHallOfFame"] = dict(bones=bones, own=own)
    return (W_ + 2, 3.0, top + 3.4)


def _row_flip(i):
    t0 = 0.15 + i * 0.22
    return lambda t: ("x", 180 * back_out((t - t0) / 0.35, 1.3), (0, 0, 0))


HOF_CLIPS = {
    "FlipToYou": dict(length=2.8, keys={f"Row{i}": _row_flip(i) for i in range(8)}),
    # the light: a stutter, then on (a tiny wobble reads as the tube flickering at the cut)
    "LightsFlicker": dict(length=1.2, keys={"Light": lambda t: ("x", 0, (0, 0, 0.0))}),
}


# ================================================================== Wickfield Junior High: the front

def junior_high(M):
    """the school's front: 40 wide, two storeys of red brick (tiled) with limestone bands, a white portico of four columns and
    a pediment with the Wicks crest, the gilt name panel, steps; rows of windows; the office window on the ground floor right
    (its lower sash rides up: OfficeWindowOpen); a flagpole with a flag that waves (FlagWave, loops)"""
    K = kit(M)
    lime = material("SchoolLime", "NH_Limestone", tint=(0.86, 0.83, 0.77), scale=0.3, wear=0.3, dirt=0.9)
    W_, D_, H_ = 40.0, 14.0, 24.0
    X0, X1 = -W_ / 2, W_ / 2
    office = (12.0, 16.0, 3.0, 8.0)
    wins = [(x - 1.8, x + 1.8, z0, z0 + 5.0) for x in (-16, -11, 11, 16) for z0 in (3.0, 14.0)] + [(x - 1.8, x + 1.8, 14.0, 19.0) for x in (-5, 5)]
    wins = [w for w in wins if not (w[0] == 14.2 and w[2] == 3.0)]
    set_group("Brick")
    wall("Front", "y", 0.0, X0, X1, 0.0, H_, 0.8, [(-3.0, 3.0, 0.0, 9.0)] + [w for w in wins if w != (14.2, 17.8, 3.0, 8.0)], K["place"])
    wall("SideL", "x", X0, 0.0, D_, 0.0, H_, 0.8, [], K["place"])
    wall("SideR", "x", X1, 0.0, D_, 0.0, H_, 0.8, [], K["place"])
    set_group("Main")
    box("Roof", (W_, D_, 0.4), (0, D_ / 2, H_ - 0.2), material("SchoolRoof", base=(0.12, 0.12, 0.13), rough=0.9, wear=0.0), bevel=0)
    for z, h in ((0.6, 1.2), (11.5, 0.6), (H_ - 0.9, 1.2)):
        box(f"Band{z}", (W_ + 0.6, 1.0, h), (0, -0.1, z), lime, bevel=0.06)
    box("Parapet", (W_ + 0.8, 1.2, 1.4), (0, 0.0, H_ + 0.7), lime, bevel=0.08)
    for x in (X0, X1):
        box(f"Quoin{x}", (1.2, 1.2, H_), (x, 0.0, H_ / 2), lime, bevel=0.06)
    for k, (a, b, z0, z1) in enumerate(wins):
        c = (a + b) / 2
        box(f"Lintel{k}", (b - a + 1.0, 0.6, 0.6), (c, -0.3, z1 + 0.3), lime, bevel=0.05)
        box(f"Sill{k}", (b - a + 0.8, 0.8, 0.25), (c, -0.35, z0 - 0.12), lime, bevel=0.04)
        for x in (a + 0.1, b - 0.1, c):
            box(f"Frame{k}{x}", (0.2 if x != c else 0.12, 0.3, z1 - z0), (x, 0.0, (z0 + z1) / 2), K["trim"], bevel=0.01)
        for z in (z0 + 0.1, (z0 + z1) / 2, z1 - 0.1):
            box(f"Rail{k}{z}", (b - a, 0.3, 0.14), (c, 0.0, z), K["trim"], bevel=0.01)
        set_group("Glass")
        box(f"Glass{k}", (b - a - 0.2, 0.05, z1 - z0 - 0.2), (c, 0.08, (z0 + z1) / 2), K["glass"], bevel=0)
        set_group("Main")
    # the office window: frame, a fixed top sash, the lower sash (its own piece), a little sign
    a, b, z0, z1 = office
    c = (a + b) / 2
    box("OffLintel", (b - a + 1.0, 0.6, 0.6), (c, -0.3, z1 + 0.3), lime, bevel=0.05)
    box("OffSill", (b - a + 0.8, 0.8, 0.25), (c, -0.35, z0 - 0.12), lime, bevel=0.04)
    for x in (a + 0.1, b - 0.1):
        box(f"OffFrame{x}", (0.2, 0.4, z1 - z0), (x, 0.0, (z0 + z1) / 2), K["trim"], bevel=0.01)
    box("OffTopRail", (b - a, 0.3, 0.14), (c, -0.05, (z0 + z1) / 2 + 0.07), K["trim"], bevel=0.01)
    set_group("Glass")
    box("OffTopGlass", (b - a - 0.3, 0.05, (z1 - z0) / 2 - 0.25), (c, 0.05, z1 - (z1 - z0) / 4), K["glass"], bevel=0)
    set_group("OfficeSash")
    for z in (z0 + 0.1, (z0 + z1) / 2 - 0.07):
        box(f"SashRail{z}", (b - a - 0.25, 0.22, 0.14), (c, -0.18, z), K["trim"], bevel=0.01)
    for x in (a + 0.22, b - 0.22):
        box(f"SashStile{x}", (0.14, 0.22, (z1 - z0) / 2 - 0.1), (x, -0.18, z0 + (z1 - z0) / 4), K["trim"], bevel=0.01)
    box("SashGlass", (b - a - 0.5, 0.04, (z1 - z0) / 2 - 0.35), (c, -0.18, z0 + (z1 - z0) / 4), K["glass"], bevel=0)
    set_group("Main")
    # the portico: steps, four columns, an entablature, the pediment with the crest, the name panel, the doors
    for s_ in range(4):
        box(f"Step{s_}", (16.0 - s_ * 0.8, 1.4, (s_ + 1) * 0.4), (0, -2.8 - (3 - s_) * 1.4 + 1.4 * 0, (s_ + 1) * 0.2), lime, bevel=0.05)
    pz = 1.6
    for x in (-6.0, -2.2, 2.2, 6.0):
        lathe(f"Column{x}", [(0.0, pz), (0.8, pz), (0.8, pz + 0.5), (0.62, pz + 0.7), (0.58, pz + 9.0), (0.75, pz + 9.4), (0.85, pz + 9.6), (0.0, pz + 9.6)],
              K["trim"], seg=20, loc=(x, -4.2, 0), flute=(16, 0.05))
    box("Entablature", (14.5, 4.6, 1.4), (0, -2.2, pz + 10.3), K["trim"], bevel=0.06)
    box("PortRoof", (14.5, 4.6, 0.3), (0, -2.2, pz + 11.15), K["trim"], bevel=0.04)
    prism("Pediment", [(-7.6, pz + 11.3), (7.6, pz + 11.3), (0.0, pz + 15.0)], -4.4, 0.6, K["trim"], plane="XZ")
    set_group("Crest")
    box("Crest", (2.8, 0.03, 2.8), (0, -4.75, pz + 12.85), K["place"], bevel=0)
    set_group("NamePanel")
    box("NamePanel", (13.0, 0.04, 2.03), (0, -4.55, pz + 10.3), K["place"], bevel=0)
    set_group("Main")
    red = wmat("SchoolDoorRed", "NH_PaintedWood", (0.18, 0.36, 0.24), 0.3, wear=0.4)
    for sx in (-1, 1):
        box(f"Door{sx}", (2.9, 0.25, 8.2), (sx * 1.5, 0.15, 4.1), red, bevel=0.05)
        box(f"DoorBar{sx}", (1.8, 0.12, 0.12), (sx * 1.5, -0.05, 4.0), K["brass"], bevel=0.03)
        set_group("Glass")
        box(f"DoorGlass{sx}", (1.6, 0.05, 2.6), (sx * 1.5, 0.0, 6.0), K["glass"], bevel=0)
        set_group("Main")
    box("DoorHead", (6.6, 0.6, 0.8), (0, -0.2, 9.3), lime, bevel=0.05)
    # the flagpole to the left of the steps, a flag (its own piece, several bones so it ripples)
    fx = -12.0
    lathe("PoleBase", [(0, 0), (1.0, 0), (1.0, 0.6), (0.4, 0.8), (0, 0.8)], lime, seg=16, loc=(fx, -6.0, 0))
    cyl("Pole", 0.14, 26.0, (fx, -6.0, 13.8), material("PoleAlu", base=(0.82, 0.82, 0.84), rough=0.25, metal=1.0, wear=0.2), verts=12)
    sphere("PoleBall", 0.3, (fx, -6.0, 26.95), K["brass"], seg=12, rings=8)
    set_group("Flag")
    flag = B49.panel("Flag", 0.0, 6.0, 0.0, 3.6, 0.0, wmat("FlagCloth", "NH_Cotton", (0.18, 0.4, 0.26), 0.2, wear=0.0), nu=12, nv=6, thick=0.03)
    from mathutils import Matrix as _M
    flag.matrix_world = _M.Translation((fx + 0.18, -6.0, 22.8))
    set_group("Main")
    bones = {"Sash": ((c, -0.18, z0), (c, -0.18, z0 + 1.0), None)}
    own = {"OfficeSash": "Sash", "Flag": ["Flag1", "Flag2", "Flag3"]}
    for k in range(3):
        bones[f"Flag{k + 1}"] = ((fx + 0.18 + 2.0 * k, -6.0, 24.6), (fx + 0.18 + 2.0 * (k + 1), -6.0, 24.6), f"Flag{k}" if k else None)
    B49.RIG["WFJuniorHigh"] = dict(bones=bones, own=own)
    return (W_ + 6, D_ + 10, 28.0)


JHS_CLIPS = {
    "OfficeWindowOpen": dict(length=1.4, keys={"Sash": lambda t: ("x", 0, (0, 0, 2.3 * ease((t - 0.2) / 0.6) + 0.06 * math.sin(t * 20) * (t > 0.8) * max(0, 1.4 - t)))}),
    "FlagWave": dict(length=2.0, loop=True, keys={
        **{f"Flag{k}": (lambda t, k=k: ("z", (6 + 4 * k) * math.sin(2 * math.pi * t / 2.0 - 0.9 * k), (0, 0, 0))) for k in (1, 2, 3)}}),
}



# ================================================================== the field: the Pumas' bus, the mascot head, the scoreboard, bleachers

def team_bus(M):
    """the Pembrook Prep team bus: an original long-nose coach, 30 long, deep purple with a silver stripe, the Pumas crest on
    the side (canvas), a row of windows, chrome bumpers, round headlights; parked, doors closed"""
    K = kit(M)
    purple = wmat("BusPurple", "NH_Enamel", (0.32, 0.14, 0.48), 0.5, wear=0.35, dirt=0.8)
    silver = material("BusSilver", base=(0.8, 0.8, 0.84), rough=0.2, metal=1.0, wear=0.25)
    rubber = material("BusTyre", base=(0.04, 0.04, 0.045), rough=0.85, wear=0.0)
    W_, L_ = 8.0, 30.0
    y0, y1 = -L_ / 2, L_ / 2
    prism("Body", [(y0 + 4.0, 1.2), (y0 + 4.0, 9.6), (y0 + 4.6, 10.3), (y1 - 0.4, 10.3), (y1, 9.6), (y1, 1.2)], 0.0, W_, purple, plane="YZ", bevel=0.35)
    prism("Nose", [(y0, 1.2), (y0, 4.6), (y0 + 0.4, 5.2), (y0 + 4.2, 5.4), (y0 + 4.2, 1.2)], 0.0, W_ - 1.0, purple, plane="YZ", bevel=0.3)
    for sx in (-1, 1):
        box(f"Stripe{sx}", (0.06, L_ - 4.4, 0.45), (sx * (W_ / 2 + 0.01), (y0 + 4.2 + y1) / 2, 5.55), silver, bevel=0)
        set_group("Glass")
        for k in range(8):
            y = y0 + 6.2 + k * 2.9
            box(f"Win{sx}{k}", (0.05, 2.4, 2.4), (sx * (W_ / 2 + 0.02), y, 7.9), K["glass"], bevel=0)
        set_group("Main")
        for k in range(9):
            box(f"Pillar{sx}{k}", (0.08, 0.5, 2.6), (sx * (W_ / 2 + 0.03), y0 + 4.75 + k * 2.9, 7.9), silver, bevel=0.02)
    set_group("Glass")
    box("Windshield", (W_ - 0.8, 0.05, 2.6), (0, y0 + 4.05, 8.0), K["glass"], bevel=0)
    set_group("Crest")
    box("CrestL", (0.03, 3.4, 3.4), (W_ / 2 + 0.03, 1.5, 3.4), K["place"], bevel=0)
    set_group("Main")
    box("Grille", (W_ - 2.0, 0.2, 2.6), (0, y0 - 0.05, 3.0), silver, bevel=0.1)
    for k in range(8):
        box(f"GrilleBar{k}", (W_ - 2.4, 0.12, 0.08), (0, y0 - 0.16, 1.95 + k * 0.3), silver, bevel=0)
    for sx in (-1, 1):
        cyl(f"LampRing{sx}", 0.55, 0.2, (sx * 2.8, y0 - 0.05, 4.0), silver, rot=(math.pi / 2, 0, 0), verts=20, bevel=0.05)
    box("BumperF", (W_ + 0.4, 0.7, 0.7), (0, y0 - 0.4, 1.2), silver, bevel=0.15, segments=3)
    box("BumperR", (W_ + 0.4, 0.7, 0.7), (0, y1 + 0.3, 1.2), silver, bevel=0.15, segments=3)
    box("Door", (0.08, 2.4, 6.6), (W_ / 2 + 0.04, y0 + 5.6, 4.6), purple, bevel=0.04)
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Headlamp{sx}", 0.45, (sx * 2.8, y0 - 0.12, 4.0), K["bulb"], seg=14, rings=8, scale=(1, 0.35, 1))
    set_group("Main")
    for y in (y0 + 2.4, y1 - 5.0):
        for sx in (-1, 1):
            t_ = lathe(f"Tyre{y}{sx}", [(0.8, -0.55), (1.3, -0.55), (1.45, -0.45), (1.45, 0.45), (1.3, 0.55), (0.8, 0.55)], rubber, seg=32, loc=(0, 0, 0), flute=(32, 0.03))
            t_.rotation_euler = (0, math.pi / 2, 0)
            t_.location = (sx * (W_ / 2 - 0.4), y, 1.45)
    return (W_ + 2, L_ + 2, 10.6)


def mascot_head(M):
    """the Pumas' mascot head: a giant foam costume head (4 tall) on a stand, sculpted (skinned skeleton): a broad tawny
    puma face, a cream muzzle, a pink nose, big friendly-fierce eyes, felt ears, whiskers; the open mouth is the
    eye-hole you look out of. It's carried in the Athletic prank (no rig: it's picked up whole)"""
    from nh_props_batch33 import Skel
    from nh_props_batch34 import chain
    tawny = material("FoamTawny", base=(0.72, 0.46, 0.18), rough=0.92, wear=0.0, dirt=0.4)
    cream = material("FoamCream", base=(0.92, 0.86, 0.72), rough=0.92, wear=0.0, dirt=0.3)
    def meta(name, balls, mat, res=0.12):
        """a smooth blended shape from metaballs (centre, radius, (sx, sy, sz)), converted to a mesh"""
        mb = bpy.data.metaballs.new(name)
        mb.resolution = res
        mb.render_resolution = res
        ob = bpy.data.objects.new(name, mb)
        bpy.context.collection.objects.link(ob)
        for (cx_, cy_, cz_), r, sc in balls:
            e = mb.elements.new()
            e.co = (cx_, cy_, cz_)
            e.radius = r * 1.75            # a metaball surface sits well inside its radius
            e.type = "ELLIPSOID"
            e.size_x, e.size_y, e.size_z = sc
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.convert(target="MESH")
        me_ob = bpy.context.active_object
        me_ob.name = name
        bpy.ops.object.shade_smooth()
        return _finish(me_ob, mat, 0)
    meta("Head", [((0, 0, 3.4), 1.0, (1.7, 1.6, 1.6)), ((0, -0.3, 4.3), 1.0, (1.3, 1.1, 0.9)), ((0, 0.5, 3.5), 1.0, (1.5, 1.4, 1.5)),
                  ((1.15, -0.65, 3.0), 1.0, (0.95, 0.85, 0.9)), ((-1.15, -0.65, 3.0), 1.0, (0.95, 0.85, 0.9)),
                  ((1.2, 0.05, 4.75), 1.0, (0.5, 0.28, 0.7)), ((-1.2, 0.05, 4.75), 1.0, (0.5, 0.28, 0.7))], tawny)
    meta("Muzzle", [((0, -1.45, 2.75), 1.0, (0.75, 0.55, 0.6)), ((0.5, -1.55, 2.85), 1.0, (0.55, 0.45, 0.5)), ((-0.5, -1.55, 2.85), 1.0, (0.55, 0.45, 0.5)),
                    ((0, -1.35, 2.2), 1.0, (0.55, 0.45, 0.4))], cream)
    sphere("Nose", 0.32, (0, -2.35, 3.1), material("FoamPink", base=(0.85, 0.42, 0.45), rough=0.8, wear=0.0), seg=16, rings=10, scale=(1.3, 0.8, 0.9))
    sphere("Mouth", 0.55, (0, -2.1, 2.3), material("MeshBlack", base=(0.02, 0.02, 0.02), rough=0.9, wear=0.0), seg=16, rings=10, scale=(1.4, 0.4, 0.7))
    for sx in (-1, 1):
        sphere(f"EyeW{sx}", 0.5, (sx * 0.7, -1.8, 3.8), cream, seg=16, rings=10, scale=(1.0, 0.5, 1.15))
        sphere(f"Iris{sx}", 0.3, (sx * 0.66, -2.02, 3.75), material("FoamGreen", base=(0.55, 0.7, 0.15), rough=0.6, wear=0.0), seg=14, rings=8, scale=(1.0, 0.4, 1.1))
        sphere(f"Pupil{sx}", 0.15, (sx * 0.64, -2.12, 3.72), material("FoamBlack", base=(0.02, 0.02, 0.02), rough=0.4, wear=0.0), seg=12, rings=8, scale=(0.7, 0.4, 1.3))
        sphere(f"Brow{sx}", 0.35, (sx * 0.75, -1.7, 4.4), material("FoamBrown", base=(0.4, 0.22, 0.08), rough=0.9, wear=0.0), seg=12, rings=8, scale=(1.4, 0.5, 0.45))
        sphere(f"EarIn{sx}", 0.3, (sx * 1.2, -0.42, 5.05), material("FoamPinkIn", base=(0.75, 0.45, 0.4), rough=0.9, wear=0.0), seg=12, rings=8, scale=(0.9, 0.3, 1.2))
        for k in range(3):
            tube(f"Whisker{sx}{k}", [Vector((sx * 0.7, -1.9, 2.95 + k * 0.12)), Vector((sx * 2.0, -1.8, 2.8 + k * 0.25))], 0.025, cream)
    # the stand it sits on
    wood = material("StandWood", "NH_DeskWood", tint=(0.5, 0.36, 0.24), scale=0.3, wear=0.4)
    cyl("StandPost", 0.15, 1.5, (0, 0, 0.75), wood, verts=12)
    cyl("StandBase", 0.9, 0.15, (0, 0, 0.08), wood, verts=24, bevel=0.03)
    return (4.4, 4.4, 6.0)


def scoreboard(M):
    """an old field scoreboard on two posts: a green panel, HOME / GUESTS / QUARTER, bulb-grid digits; the bulbs are their own
    Glow piece (the game switches them on in the prank: the board lights up by itself)"""
    K = kit(M)
    green = wmat("ScoreGreen", "NH_PaintedWood", (0.12, 0.32, 0.18), 0.3, wear=0.4, dirt=0.8)
    for x in (-6.0, 6.0):
        box(f"Post{x}", (0.6, 0.6, 14.0), (x, 0.4, 7.0), K["iron"], bevel=0.05)
    box("Panel", (14.0, 0.6, 7.0), (0, 0, 14.5), green, bevel=0.1)
    box("Trim", (14.4, 0.7, 0.4), (0, 0, 18.2), K["trim"], bevel=0.06)
    set_group("Labels")
    box("Labels", (13.0, 0.02, 6.2), (0, -0.32, 14.5), K["place"], bevel=0)
    set_group("Bulbs")
    bulb = K["bulb"]
    for gx in (-3.8, 3.8):
        for d in (-0.9, 0.9):
            for i in range(5):
                for j in range(7):
                    sphere(f"B{gx}{d}{i}{j}", 0.1, (gx + d + (i - 2) * 0.28, -0.34, 13.0 + j * 0.32), bulb, seg=6, rings=4)
    set_group("Main")
    return (15.0, 2.0, 18.6)


def bleachers(M):
    """a run of aluminium bleachers: five rising benches on a steel frame, a back rail"""
    K = kit(M)
    alu = material("Alu", base=(0.75, 0.76, 0.78), rough=0.35, metal=1.0, wear=0.3, dirt=0.8)
    steel = material("SteelFrame", base=(0.35, 0.36, 0.38), rough=0.5, metal=1.0, wear=0.4)
    L_ = 20.0
    for k in range(5):
        box(f"Seat{k}", (L_, 0.9, 0.15), (0, k * 1.6, 1.2 + k * 1.1), alu, bevel=0.04)
        box(f"Foot{k}", (L_, 0.8, 0.1), (0, k * 1.6 - 0.9, 0.6 + k * 1.1), alu, bevel=0.03)
    for x in range(-9, 10, 3):
        tube(f"Frame{x}", [Vector((x, -1.4, 0.0)), Vector((x, 6.8, 5.8))], 0.1, steel)
        box(f"Leg{x}", (0.18, 0.18, 6.0), (x, 6.6, 3.0), steel, bevel=0)
    box("BackRail", (L_, 0.1, 0.1), (0, 7.0, 7.4), steel, bevel=0)
    for x in range(-9, 10, 3):
        box(f"RailPost{x}", (0.1, 0.1, 1.6), (x, 7.0, 6.6), steel, bevel=0)
    return (L_ + 1, 9.0, 7.6)



# ================================================================== the Ashby House and Mrs Ashby's portrait

def portrait_ashby(M):
    """Mrs Ashby's portrait: an ornate gilt frame (a moulded profile swept round, corner cartouches), the oil canvas, and the
    irises: two dark discs riding just in front of the painted eye whites (their own pieces, a bone each) so they follow you.
    Clips: EyesFollow (they track left to right across the room, a beat late, loops), Stare (they snap to centre and hold)"""
    K = kit(M)
    gilt = material("FrameGilt", base=(0.95, 0.74, 0.36), rough=0.3, metal=1.0, wear=0.5, dirt=1.0)
    CW, CH = 3.0, 4.0                       # canvas size (768 x 1024 at 256 px a stud)
    Z0 = 4.0
    set_group("Canvas")
    box("Canvas", (CW, 0.02, CH), (0, 0.0, Z0 + CH / 2), K["place"], bevel=0)
    set_group("Main")
    box("Backing", (CW + 0.2, 0.1, CH + 0.2), (0, 0.08, Z0 + CH / 2), material("FrameBack", base=(0.15, 0.1, 0.06), rough=0.9, wear=0.0), bevel=0)
    # the frame: a profile (cove, bead, ogee) swept round the rectangle
    prof = [(0.0, 0.0), (0.12, -0.05), (0.2, -0.22), (0.32, -0.28), (0.42, -0.2), (0.5, -0.32), (0.6, -0.12), (0.62, 0.0)]
    pts = [(-CW / 2, Z0), (CW / 2, Z0), (CW / 2, Z0 + CH), (-CW / 2, Z0 + CH)]
    for k in range(4):
        a, b = Vector((pts[k][0], 0, pts[k][1])), Vector((pts[(k + 1) % 4][0], 0, pts[(k + 1) % 4][1]))
        d = (b - a).normalized()
        out = Vector((d.z, 0, -d.x))                       # outward from the canvas
        L_ = (b - a).length
        for (o0, y0), (o1, y1) in zip(prof, prof[1:]):
            q = [a + out * o0 - d * o0, b + out * o0 + d * o0, b + out * o1 + d * o1, a + out * o1 - d * o1]
            bot = [Vector((p.x, y0 - 0.02, p.z)) if i < 2 else Vector((p.x, y1 - 0.02, p.z)) for i, p in enumerate(q)]
            top = [p + Vector((0, 0.12, 0)) for p in bot]
            solid(f"Frame{k}_{o0}", [tuple(p) for p in bot], [tuple(p) for p in top], gilt)
    for sx in (-1, 1):                                      # corner cartouches and a crest on top
        for sz in (0, 1):
            sphere(f"Corner{sx}{sz}", 0.32, (sx * (CW / 2 + 0.3), -0.3, Z0 + sz * CH + (0.3 if sz else -0.3)), gilt, seg=14, rings=8, scale=(1.2, 0.6, 1.2))
    prism("Crest", [(-0.9, Z0 + CH + 0.4), (0.9, Z0 + CH + 0.4), (0.5, Z0 + CH + 0.9), (0.0, Z0 + CH + 1.2), (-0.5, Z0 + CH + 0.9)], -0.25, 0.15, gilt, plane="XZ", bevel=0.03)
    box("NamePlate", (1.1, 0.05, 0.25), (0, -0.35, Z0 - 0.42), gilt, bevel=0.02)
    # the irises (eye centres from art/hometown/ashby_canvases.py EYES, on the 768 x 1024 canvas)
    bones = {}
    own = {}
    for side, (dx, ey) in (("L", (-62, 395)), ("R", (62, 395))):
        x = dx / 256.0
        z = Z0 + CH - ey / 256.0
        set_group(f"Iris{side}")
        cyl(f"Iris{side}", 0.075, 0.015, (x, -0.02, z), material("IrisDark", base=(0.12, 0.08, 0.05), rough=0.25, wear=0.0), rot=(math.pi / 2, 0, 0), verts=20)
        cyl(f"Pupil{side}", 0.04, 0.015, (x, -0.032, z), material("PupilBlack", base=(0.01, 0.01, 0.01), rough=0.15, wear=0.0), rot=(math.pi / 2, 0, 0), verts=16)
        sphere(f"Glint{side}", 0.012, (x - 0.02, -0.042, z + 0.02), K["bulb"], seg=6, rings=4)
        bones[f"Iris{side}"] = ((x, -0.03, z), (x, -0.3, z), None)
        own[f"Iris{side}"] = f"Iris{side}"
    set_group("Main")
    B49.RIG["WFPortraitAshby"] = dict(bones=bones, own=own)
    return (CW + 2, 1.0, Z0 + CH + 1.4)


def _look(t):
    """where the eyes look (x offset in studs, within the white): a slow sweep that holds at each end, a beat late"""
    u = math.sin(2 * math.pi * (t - 0.15) / 6.0)
    return 0.07 * math.tanh(2.2 * u)


PORTRAIT_CLIPS = {
    "EyesFollow": dict(length=6.0, loop=True, keys={
        "IrisL": lambda t: ("x", 0, (_look(t), 0, 0)), "IrisR": lambda t: ("x", 0, (_look(t - 0.08), 0, 0))}),
    "Stare": dict(length=0.6, keys={
        "IrisL": lambda t: ("x", 0, (0.07 * (1 - back_out(t / 0.15, 2.0)), 0, 0)), "IrisR": lambda t: ("x", 0, (0.07 * (1 - back_out(t / 0.17, 2.0)), 0, 0))}),
}


def ashby_house(M):
    """the condemned Ashby House: two storeys of grey weathered clapboard (tiled), a corner turret with a conical slate roof,
    a steep main gable, every window boarded with crossed planks, a porch whose roof sags and whose left post has given
    way, the front door with the CONDEMNED notice (it creaks open: DoorCreak), an upstairs shutter hanging by one hinge
    (ShutterBang, loops), a lightning-split chimney, dead vines"""
    K = kit(M)
    W_, D_, H_ = 26.0, 22.0, 20.0
    X0, X1 = -W_ / 2, W_ / 2
    trim = wmat("AshTrim", "NH_PaintedWood", (0.62, 0.6, 0.55), 0.3, wear=0.8, dirt=1.0)
    plank = material("Plank", "NH_DeskWood", tint=(0.42, 0.36, 0.28), scale=0.3, rough_add=0.2, wear=0.6, dirt=1.0)
    slate = material("AshSlate", "NH_Slate", tint=(0.09, 0.09, 0.11), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.2)
    rotten = material("RotWood", "NH_DeskWood", tint=(0.25, 0.2, 0.15), scale=0.3, rough_add=0.3, wear=0.7, dirt=1.0)
    door = (-2.0, 2.0)
    wins = [(x - 1.8, x + 1.8, z0, z0 + 5.0) for x in (-8.0, 8.0) for z0 in (3.0, 12.5)] + [(-1.8, 1.8, 12.5, 17.5)]
    set_group("Siding")
    wall("Front", "y", 0.0, X0, X1, 0.0, H_, 0.6, [(door[0], door[1], 1.6, 9.4)] + wins, K["place"])
    wall("SideL", "x", X0, 0.0, D_, 0.0, H_, 0.6, [], K["place"])
    wall("SideR", "x", X1, 0.0, D_, 0.0, H_, 0.6, [], K["place"])
    wall("Back", "y", D_, X0, X1, 0.0, H_, 0.6, [], K["place"])
    solid("Gable", [(X0, -0.3, H_), (X1, -0.3, H_), (0, -0.3, H_ + 10)], [(X0, 0.3, H_), (X1, 0.3, H_), (0, 0.3, H_ + 10)], K["place"])
    set_group("Main")
    for nm, s_ in (("L", -1), ("R", 1)):                       # the steep main roof, slate
        solid(f"Roof{nm}", [(s_ * (W_ / 2 + 1.0), -1.0, H_ - 1.0), (0, -1.0, H_ + 10.3), (0, D_ + 1.0, H_ + 10.3), (s_ * (W_ / 2 + 1.0), D_ + 1.0, H_ - 1.0)],
              [(s_ * (W_ / 2 + 1.0), -1.0, H_ - 0.6), (0, -1.0, H_ + 10.7), (0, D_ + 1.0, H_ + 10.7), (s_ * (W_ / 2 + 1.0), D_ + 1.0, H_ - 0.6)], slate)
    # the turret on the right front corner: an octagonal tower, a conical roof, a finial
    tx, ty = X1, 0.0
    lathe("Turret", [(0, 0.0), (4.0, 0.0), (4.0, H_ + 3.0), (0, H_ + 3.0)], wmat("TurretGrey", "NH_PaintedWood", (0.2, 0.19, 0.18), 0.3, wear=0.7, dirt=1.0), seg=8, loc=(tx, ty, 0))
    lathe("TurretRoof", [(0, H_ + 3.0), (4.6, H_ + 3.0), (4.4, H_ + 3.4), (0.15, H_ + 12.0), (0, H_ + 12.0)], slate, seg=8, loc=(tx, ty, 0))
    lathe("Finial", [(0, H_ + 12.0), (0.15, H_ + 12.1), (0.25, H_ + 12.6), (0.05, H_ + 13.6), (0, H_ + 13.8)], K["iron"], seg=8, loc=(tx, ty, 0))
    for k in range(3):                                         # a ring of turret windows, boarded
        a = math.pi * (1.1 + 0.4 * k)
        px, py = tx + 4.05 * math.cos(a), ty + 4.05 * math.sin(a)
        box(f"TWin{k}", (1.8, 0.2, 3.0), (px, py, 14.5), material("TWinDark", base=(0.02, 0.02, 0.03), rough=0.4, wear=0.0), bevel=0, rot=(0, 0, a + math.pi / 2))
        box(f"TBoardA{k}", (2.3, 0.15, 0.4), (px, py, 14.5), plank, bevel=0.03, rot=(0.0, 0.6, a + math.pi / 2))
        box(f"TBoardB{k}", (2.3, 0.15, 0.4), (px, py, 14.5), plank, bevel=0.03, rot=(0.0, -0.6, a + math.pi / 2))
    # the windows: dark inside, frames, two or three planks nailed across each
    for k, (a, b, z0, z1) in enumerate(wins):
        c = (a + b) / 2
        box(f"Dark{k}", (b - a, 0.1, z1 - z0), (c, 0.3, (z0 + z1) / 2), material("WinDark", base=(0.02, 0.02, 0.025), rough=0.5, wear=0.0), bevel=0)
        for x in (a, b):
            box(f"Frame{k}{x}", (0.35, 0.35, z1 - z0 + 0.4), (x, -0.2, (z0 + z1) / 2), trim, bevel=0.03)
        box(f"Head{k}", (b - a + 1.0, 0.45, 0.45), (c, -0.25, z1 + 0.25), trim, bevel=0.04)
        for j, (zz, ang) in enumerate(((z0 + 1.0, 0.25), ((z0 + z1) / 2, -0.15), (z1 - 1.0, 0.1))):
            box(f"Board{k}{j}", (b - a + 0.8, 0.18, 0.55), (c, -0.45, zz), plank, bevel=0.04, rot=(0, ang, 0))
            for nx in (a - 0.2, b + 0.2):
                box(f"Nail{k}{j}{nx}", (0.06, 0.06, 0.06), (nx, -0.55, zz + ang * (nx - c)), K["iron"], bevel=0)
    # the door (its own piece) and its frame, the notice
    for x in door:
        box(f"DoorFrame{x}", (0.4, 0.4, 8.2), (x, -0.2, 5.5), trim, bevel=0.03)
    box("DoorHead", (5.0, 0.5, 0.5), (0, -0.25, 9.65), trim, bevel=0.04)
    set_group("Door")
    box("Door", (3.9, 0.25, 7.7), (0, 0.05, 5.5), rotten, bevel=0.04)
    for z in (3.0, 5.5, 8.0):
        box(f"DoorRail{z}", (3.6, 0.1, 0.25), (0, -0.12, z), rotten, bevel=0.02)
    cyl("Knocker", 0.22, 0.06, (0, -0.18, 6.4), K["iron"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.02)
    set_group("DoorNotice")
    box("Notice", (1.5, 0.02, 2.0), (0.0, -0.18, 4.3), K["place"], bevel=0)
    set_group("Main")
    # the porch: a deck, steps, three posts (the left one broken), the porch roof sagging toward it
    box("Deck", (W_ - 4, 6.0, 0.4), (0, -3.0, 1.4), rotten, bevel=0.03, rot=(0.0, 0.03, 0))
    for k in range(3):
        box(f"Step{k}", (5.0, 1.0, 0.45 * (k + 1)), (0, -6.5 - (2 - k) * 1.0, 0.225 * (k + 1)), rotten, bevel=0.03, rot=(0, 0, 0.04 * (k - 1)))
    for x, h, lean in ((-10.0, 4.5, 0.35), (0.0 + 3.5, 8.6, 0.0), (10.0, 8.6, 0.0)):
        box(f"PorchPost{x}", (0.5, 0.5, h), (x, -5.7, 1.6 + h / 2), trim, bevel=0.03, rot=(0, lean, 0))
    box("PostStump", (0.5, 0.5, 1.0), (-10.0, -5.7, 2.1), trim, bevel=0.03)
    solid("PorchRoof", [(-11.5, -6.5, 8.6), (11.5, -6.5, 10.5), (11.5, 0.0, 11.5), (-11.5, 0.0, 11.0)],
          [(-11.5, -6.5, 8.9), (11.5, -6.5, 10.8), (11.5, 0.0, 11.8), (-11.5, 0.0, 11.3)], slate)
    for x in range(-9, 10, 2):                                   # a railing with gaps where balusters fell out
        if x in (-5, 1, 7):
            continue
        box(f"Baluster{x}", (0.15, 0.15, 2.4), (x, -5.7, 2.8), trim, bevel=0, rot=(0, 0.08 * ((x * 7) % 3 - 1), 0))
    box("PorchRail", (20.0, 0.25, 0.2), (0, -5.7, 4.0), trim, bevel=0.03, rot=(0, 0.02, 0))
    # the hanging shutter (its own piece) on the upper left window
    set_group("Shutter")
    a, b, z0, z1 = wins[1]
    box("ShutterPanel", (1.6, 0.15, 5.0), (a - 1.0, -0.45, (z0 + z1) / 2), trim, bevel=0.03)
    for k in range(10):
        box(f"Louvre{k}", (1.3, 0.1, 0.3), (a - 1.0, -0.55, z0 + 0.4 + k * 0.45), trim, bevel=0, rot=(0.5, 0, 0))
    set_group("Main")
    # the chimney, split
    for sx, tilt in ((-0.6, -0.12), (0.6, 0.1)):
        box(f"Chimney{sx}", (1.2, 2.4, 8.0), (-8.0 + sx, 10.0, H_ + 5.5), material("AshBrick", "NH_Limestone", tint=(0.4, 0.22, 0.18), scale=0.3, wear=0.5, dirt=1.0), bevel=0.05, rot=(0, tilt, 0))
    # dead vines up the front
    import random as _r
    rr = _r.Random(91)
    vine = material("DeadVine", base=(0.12, 0.09, 0.06), rough=0.9, wear=0.0)
    for k in range(5):
        x = rr.uniform(X0 + 1, X1 - 1)
        pts_ = [Vector((x + rr.uniform(-0.5, 0.5) * i * 0.3, -0.42, i * 1.8)) for i in range(8)]
        tube(f"Vine{k}", pts_, 0.06, vine)
    B49.RIG["WFAshbyHouse"] = dict(
        bones={"Door": ((door[0] + 0.05, 0.05, 1.6), (door[0] + 0.05, 0.05, 2.6), None),
               "Shutter": ((a - 1.8, -0.45, z1 - 0.3), (a - 0.2, -0.45, z1 - 0.3), None)},
        own={"Door": "Door", "DoorNotice": "Door", "Shutter": "Shutter"})
    return (W_ + 10, D_ + 10, H_ + 14)


ASHBY_CLIPS = {
    # the door creaks open by itself: a hesitation, a few inches, a stop, then it swings the rest of the way
    "DoorCreak": dict(length=3.0, keys={"Door": lambda t: ("z", -(18 * ease(t / 0.9) + 72 * ease((t - 1.6) / 1.2)), (0, 0, 0))}),
    # the shutter, hanging by its top hinge, swings in the wind and bangs against the siding; loops
    "ShutterBang": dict(length=3.0, loop=True, keys={
        "Shutter": lambda t: ("y", -14 - 12 * math.sin(2 * math.pi * t / 3.0) + 9 * math.exp(-((t % 3.0 - 2.25) / 0.06) ** 2), (0, 0, 0))}),
}


BUILDERS["WFChetTruck"] = chet_truck
B49.CLIPS["WFChetTruck"] = CHET_CLIPS
P.RIGS["WFChetTruck"] = lambda objs: B49.rig_pieces("WFChetTruck", objs)
B49.CLIP_CAM["WFChetTruck"] = {c: ((14.0, -12.0, 7.0), (0, 0, 2.5)) for c in CHET_CLIPS}
BUILDERS.update({"WFHallOfFame": hall_of_fame, "WFJuniorHigh": junior_high, "WFTeamBus": team_bus, "WFMascotHead": mascot_head,
                 "WFScoreboard": scoreboard, "WFBleachers": bleachers})
P.CANVAS.update({"WFTeamBus_Crest": "WF_CrestPumas", "WFScoreboard_Labels": "WF_ScoreLabels"})
BUILDERS.update({"WFPortraitAshby": portrait_ashby, "WFAshbyHouse": ashby_house})
P.CANVAS.update({"WFPortraitAshby_Canvas": "WF_PortraitAshby", "WFAshbyHouse_DoorNotice": "WF_Condemned"})
P.TILED["WFAshbyHouse_Siding"] = ("WF_ClapGrey", 8.0)
for _n, _c in (("WFPortraitAshby", PORTRAIT_CLIPS), ("WFAshbyHouse", ASHBY_CLIPS)):
    B49.CLIPS[_n] = _c
    P.RIGS[_n] = (lambda n: (lambda objs: B49.rig_pieces(n, objs)))(_n)
B49.CLIP_CAM["WFPortraitAshby"] = {c: ((0.0, -4.5, 6.6), (0, 0, 6.6)) for c in PORTRAIT_CLIPS}
B49.CLIP_CAM["WFAshbyHouse"] = {"DoorCreak": ((6.0, -16.0, 7.0), (0, 0, 5.0)), "ShutterBang": ((-2.0, -16.0, 16.0), (-10.0, 0, 15.0))}
B49.CLIPS["WFHallOfFame"] = HOF_CLIPS
B49.CLIPS["WFJuniorHigh"] = JHS_CLIPS
P.RIGS["WFHallOfFame"] = lambda objs: B49.rig_pieces("WFHallOfFame", objs)
P.RIGS["WFJuniorHigh"] = lambda objs: B49.rig_pieces("WFJuniorHigh", objs)
B49.CLIP_CAM["WFHallOfFame"] = {c: ((2.5, -12.0, 5.5), (0, 0, 5.5)) for c in HOF_CLIPS}
B49.CLIP_CAM["WFJuniorHigh"] = {"OfficeWindowOpen": ((14.0, -9.0, 6.0), (14.0, 0.0, 5.5)), "FlagWave": ((-4.0, -22.0, 22.0), (-9.0, -6.0, 24.0))}
P.TILED["WFJuniorHigh_Brick"] = ("WF_Brick", 6.0)
P.CANVAS.update({"WFHallOfFame_Title": "WF_HallFameTitle", "WFJuniorHigh_Crest": "WF_CrestWicks", "WFJuniorHigh_NamePanel": "WF_SchoolName"})
for _i in range(8):
    P.CANVAS[f"WFHallOfFame_Row{_i}"] = f"WF_HallFameRow{_i}"
    P.CANVAS[f"WFHallOfFame_RowBack{_i}"] = "WF_HallFameBlank"
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.15 for n in BUILDERS})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        if n in B49.CLIPS:
            B49.clip_strips(n)
