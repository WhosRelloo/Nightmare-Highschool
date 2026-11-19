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
from nh_props_batch49_hometown import kit, wmat, ease, back_out  # noqa: E402

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

BUILDERS["WFChetTruck"] = chet_truck
B49.CLIPS["WFChetTruck"] = CHET_CLIPS
P.RIGS["WFChetTruck"] = lambda objs: B49.rig_pieces("WFChetTruck", objs)
B49.CLIP_CAM["WFChetTruck"] = {c: ((14.0, -12.0, 7.0), (0, 0, 2.5)) for c in CHET_CLIPS}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.15 for n in BUILDERS})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        if n in B49.CLIPS:
            B49.clip_strips(n)
