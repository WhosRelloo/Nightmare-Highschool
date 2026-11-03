"""Props batch 3 (2026-11-03): eight more school props for nh_props.py, in the same gothic style.

  GrandfatherClock  oak longcase clock: pointed hood with pinnacles, brass dial with hour ticks and hands,
                    an arched glass door, brass weights, and a pendulum that can swing (own piece, hinge at the top)
  WallSconce        a caged iron lantern with a candle on a scrolled wall arm (Glow: the flame; Glass: the panes)
  HallBench         an oak slatted bench on wrought-iron scroll ends with a quatrefoil in each end
  NoticeBoard       a cork board in a carved oak frame with a pointed crest, pinned papers and wax seals
  CelestialGlobe    a night-blue star globe in brass meridian and horizon rings on an oak tripod
  AlchemyTable      an oak and iron workbench: flasks of glowing liquid, a retort, a test-tube rack,
                    a mortar and pestle, an open book and a candle (Glow: liquids and flame; Glass: the vessels)
  SchoolBell        a brass hand-cast bell in an iron yoke on a wall bracket (Bell: own piece, hinge at the axle)
  TrophyCabinet     an oak cabinet with arched glass doors, glass shelves, cups, a shield plaque and medals

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy

import nh_props as P
from nh_props import box, cyl, tube, ring, set_group, _finish, _gable, _quatrefoil, _pinnacle, _column, \
    _arch_loop, _candlestick, material


def sphere(name, r, loc, mat, seg=16, rings=8, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(o, mat, 0)


def cone(name, r1, r2, depth, loc, mat, verts=16, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return _finish(o, mat, 0.01)


def circle_pts(cx, cy, cz, r, axis="Z", n=24, tilt=0.0):
    """Points round a circle; axis is the circle's normal. tilt rotates the circle about X (radians)."""
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        if axis == "Z":
            x, y, z = math.cos(a) * r, math.sin(a) * r, 0.0
        elif axis == "X":
            x, y, z = 0.0, math.cos(a) * r, math.sin(a) * r
        else:
            x, y, z = math.cos(a) * r, 0.0, math.sin(a) * r
        if tilt:
            y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
        pts.append((cx + x, cy + y, cz + z))
    return pts


def flame(name, loc, h=0.16):
    sphere(name, h * 0.32, (loc[0], loc[1], loc[2] + h * 0.5), material("FlameTmp", base=(1.0, 0.7, 0.3), rough=0.5),
           seg=8, rings=6, scale=(1, 1, 2.3))


# ================================================================== grandfather clock
def grandfather_clock(M):
    W, D = 2.0, 1.3
    set_group("Case")
    box("Plinth", (W, D, 0.45), (0, 0, 0.225), M["oakdark"], bevel=0.04, segments=2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Foot{sx}{sy}", 0.12, 0.12, (sx * (W / 2 - 0.18), sy * (D / 2 - 0.18), 0.02), M["oakdark"], verts=12)
    box("Base", (1.7, 1.1, 1.6), (0, 0, 0.45 + 0.8), M["oak"], bevel=0.04)
    box("BasePanel", (1.25, 0.05, 1.15), (0, -0.56, 1.25), M["oakdark"], bevel=0.02)
    _quatrefoil("BaseSeal", 0, -0.6, 1.25, 0.24, M["brass"])
    box("BaseCap", (1.85, 1.2, 0.14), (0, 0, 2.08), M["oakdark"], bevel=0.03)
    # waist with an arched glass door
    box("Waist", (1.3, 0.95, 3.0), (0, 0, 2.1 + 1.5), M["oak"], bevel=0.03)
    tube("DoorFrame", _arch_loop(0, -0.49, 0.42, 2.35, 4.55, 4.95), 0.045, M["oakdark"], square=True, closed=True, poly=True)
    for sx in (-1, 1):
        _column(f"Pil{sx}", sx * 0.58, -0.45, 2.15, 5.05, 0.06, M["oakdark"], M["brass"])
    cyl("Keyhole", 0.03, 0.03, (0.36, -0.5, 3.4), M["brass"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0)
    # brass weights on chains behind the glass
    for sx in (-1, 1):
        cyl(f"Weight{sx}", 0.08, 0.55, (sx * 0.24, -0.28, 3.95), M["brass"], verts=14)
        tube(f"Chain{sx}", [(sx * 0.24, -0.28, 4.23), (sx * 0.24, -0.28, 4.95)], 0.012, M["brasssteel"], poly=True)
    box("WaistBack", (1.1, 0.04, 2.8), (0, 0.2, 3.6), M["oakdark"], bevel=0.01)
    box("WaistCap", (1.65, 1.15, 0.16), (0, 0, 5.12), M["oakdark"], bevel=0.03)
    # hood: the dial under a pointed gable with pinnacles
    box("Hood", (1.8, 1.2, 1.95), (0, 0, 5.2 + 0.975), M["oak"], bevel=0.04)
    cyl("DialBack", 0.74, 0.05, (0, -0.61, 6.15), M["brass"], rot=(math.pi / 2, 0, 0), verts=40)
    cyl("Dial", 0.66, 0.05, (0, -0.635, 6.15), M["paper"], rot=(math.pi / 2, 0, 0), verts=40)
    ring("Bezel", (0, -0.66, 6.15), 0.7, "Y", M["brass"], thick=0.035)
    ring("Chapter", (0, -0.665, 6.15), 0.5, "Y", M["oakdark"], thick=0.008)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        big = k % 3 == 0
        x, z = math.sin(a) * 0.58, 6.15 + math.cos(a) * 0.58
        box(f"Tick{k}", (0.03 if not big else 0.05, 0.02, 0.12 if big else 0.08), (x, -0.665, z), M["glass"], bevel=0.003, segments=1,
            rot=(0, -a, 0))
    box("HourHand", (0.04, 0.02, 0.32), (-0.13, -0.68, 6.24), M["iron"], bevel=0.005, rot=(0, math.radians(60), 0))
    box("MinuteHand", (0.03, 0.02, 0.5), (0.2, -0.685, 6.28), M["iron"], bevel=0.005, rot=(0, math.radians(-60), 0))
    cyl("HandCap", 0.05, 0.04, (0, -0.7, 6.15), M["brass"], rot=(math.pi / 2, 0, 0), verts=12)
    for sx in (-1, 1):
        _column(f"HoodPil{sx}", sx * 0.82, -0.56, 5.25, 7.1, 0.07, M["oakdark"], M["brass"])
    box("HoodCap", (2.0, 1.32, 0.16), (0, 0, 7.2), M["oakdark"], bevel=0.04)
    _gable("Crown", 0, -0.5, 0.92, 7.28, 8.0, 0.16, M["oak"], M["oakdark"], edge=0.05)
    _quatrefoil("CrownSeal", 0, -0.6, 7.6, 0.17, M["brass"])
    for sx in (-1, 1):
        _pinnacle(f"Pin{sx}", sx * 0.9, -0.5, 7.28, 0.7, M["oak"])
    # the pendulum swings from the top of the waist (Roblox can rock it about this hinge)
    set_group("Pendulum", hinge=(0, -0.36, 5.0), swing=1)
    tube("Rod", [(0, -0.36, 4.98), (0, -0.36, 3.05)], 0.022, M["brass"], poly=True)
    cyl("Bob", 0.24, 0.05, (0, -0.36, 2.95), M["brass"], rot=(math.pi / 2, 0, 0), verts=28)
    ring("BobRim", (0, -0.39, 2.95), 0.24, "Y", M["brass"], thick=0.02)
    _quatrefoil("BobSeal", 0, -0.4, 2.95, 0.1, M["crimson"])
    set_group("Glass")
    box("DoorGlass", (0.8, 0.02, 2.55), (0, -0.5, 3.6), M["glassclear"], bevel=0.0, segments=1)
    set_group("Case")
    return (W, D, 8.0)


# ================================================================== wall sconce
def wall_sconce(M):
    set_group("Sconce")
    # back plate: a pointed iron shield with brass rivets
    tube("Plate", _arch_loop(0, 0.42, 0.24, 0.55, 1.2, 1.5), 0.03, M["iron"], square=True, closed=True, poly=True)
    box("PlateFill", (0.42, 0.05, 0.62), (0, 0.44, 0.88), M["iron"], bevel=0.02)
    for z in (0.62, 1.14):
        for sx in (-1, 1):
            sphere(f"Rivet{z}{sx}", 0.03, (sx * 0.15, 0.4, z), M["brass"], seg=8, rings=4)
    _quatrefoil("PlateSeal", 0, 0.4, 0.88, 0.1, M["brass"])
    # scrolled arm out to the lantern hook
    tube("Arm", [(0, 0.42, 0.98), (0, 0.2, 1.12), (0, -0.08, 1.32), (0, -0.25, 1.42)], 0.03, M["iron"], square=True)
    tube("ArmCurl", [(0, 0.4, 0.78), (0, 0.18, 0.86), (0, 0.06, 1.0), (0, 0.12, 1.12), (0, 0.2, 1.08)], 0.02, M["iron"])
    tube("Hook", [(0, -0.25, 1.42), (0, -0.25, 1.32)], 0.02, M["iron"], poly=True)
    ring("HookRing", (0, -0.25, 1.28), 0.05, "X", M["iron"], thick=0.015)
    # the caged lantern
    cx, cy = 0.0, -0.25
    s = 0.17
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Post{sx}{sy}", [(cx + sx * s, cy + sy * s, 0.62), (cx + sx * s, cy + sy * s, 1.12)], 0.02, M["iron"], square=True, poly=True)
    box("LBase", (0.42, 0.42, 0.06), (cx, cy, 0.6), M["iron"], bevel=0.015)
    box("LTopBand", (0.4, 0.4, 0.04), (cx, cy, 1.12), M["iron"], bevel=0.01)
    cone("Roof", 0.3, 0.04, 0.2, (cx, cy, 1.24), M["iron"], verts=4, rot=(0, 0, math.pi / 4))
    sphere("Finial", 0.035, (cx, cy, 1.36), M["brass"], seg=8, rings=4)
    cone("Drop", 0.05, 0.0, 0.12, (cx, cy, 0.52), M["iron"], verts=8, rot=(math.pi, 0, 0))
    for sx in (-1, 1):
        tube(f"Bar{sx}", [(cx + sx * 0.08, cy - s, 0.64), (cx + sx * 0.08, cy - s, 1.1)], 0.008, M["iron"], poly=True)
    cyl("Pan", 0.09, 0.03, (cx, cy, 0.65), M["brass"], verts=14)
    cyl("Candle", 0.05, 0.22, (cx, cy, 0.78), M["chalk"], verts=12)
    sphere("Drip", 0.02, (cx + 0.05, cy, 0.84), M["chalk"], seg=6, rings=3, scale=(1, 1, 2))
    set_group("Glow")
    flame("Flame", (cx, cy, 0.89), h=0.15)
    set_group("Glass")
    for sx, sy, w, d in ((0, -1, 0.34, 0.01), (0, 1, 0.34, 0.01), (-1, 0, 0.01, 0.34), (1, 0, 0.01, 0.34)):
        box(f"Pane{sx}{sy}", (w, d, 0.48), (cx + sx * (s - 0.005), cy + sy * (s - 0.005), 0.87), M["glassamber"], bevel=0.0, segments=1)
    set_group("Sconce")
    return (0.5, 0.95, 1.5)


# ================================================================== hall bench
def hall_bench(M):
    W = 5.0
    for i, y in enumerate((-0.58, -0.3, -0.02, 0.26)):
        box(f"Slat{i}", (W - 0.3, 0.25, 0.09), (0, y, 1.42), M["oak"], bevel=0.025)
    for i, z in enumerate((1.95, 2.3, 2.65)):
        box(f"Back{i}", (W - 0.3, 0.07, 0.22), (0, 0.62 + (z - 1.95) * 0.12, z), M["oak"], bevel=0.02, rot=(math.radians(-12), 0, 0))
    box("BackCap", (W - 0.1, 0.12, 0.08), (0, 0.72, 2.92), M["oakdark"], bevel=0.02, rot=(math.radians(-12), 0, 0))
    for x in (-(W / 2 - 0.12), W / 2 - 0.12, 0):
        mid = x == 0
        # front leg with a scrolled foot, rear leg rising into the back
        tube(f"FrontLeg{x}", [(x, -0.62, 0.04), (x, -0.6, 0.7), (x, -0.62, 1.38)], 0.04, M["iron"], square=True)
        tube(f"FootCurl{x}", [(x, -0.62, 0.04), (x, -0.8, 0.06), (x, -0.86, 0.18), (x, -0.76, 0.24)], 0.03, M["iron"])
        tube(f"RearLeg{x}", [(x, 0.5, 0.04), (x, 0.52, 1.0), (x, 0.6, 1.4), (x, 0.78, 2.95)], 0.04, M["iron"], square=True)
        tube(f"Rail{x}", [(x, -0.62, 1.36), (x, 0.0, 1.32), (x, 0.55, 1.36)], 0.035, M["iron"], square=True)
        tube(f"Stretch{x}", [(x, -0.6, 0.45), (x, 0.52, 0.45)], 0.025, M["iron"], poly=True)
        if not mid:
            # arm rest with a scroll, a quatrefoil in the end frame
            tube(f"Arm{x}", [(x, 0.62, 2.0), (x, 0.0, 2.02), (x, -0.62, 1.95), (x, -0.78, 1.82), (x, -0.7, 1.7), (x, -0.6, 1.76)], 0.035, M["iron"])
            tube(f"ArmPost{x}", [(x, -0.62, 1.38), (x, -0.62, 1.95)], 0.03, M["iron"], square=True, poly=True)
            ring(f"Rose{x}", (x, -0.05, 0.85), 0.22, "X", M["iron"], thick=0.025)
            for k, (dy, dz) in enumerate(((0, 0.22), (0, -0.22), (0.22, 0), (-0.22, 0))):
                ring(f"Foil{x}{k}", (x, -0.05 + dy * 0.6, 0.85 + dz * 0.6), 0.09, "X", M["iron"], thick=0.018)
            box(f"ArmPad{x}", (0.22, 1.3, 0.06), (x, -0.02, 2.06), M["oakdark"], bevel=0.02)
    for x in (-(W / 2 - 0.12), W / 2 - 0.12):
        for y in (-0.62, 0.5):
            box(f"Pad{x}{y}", (0.16, 0.16, 0.04), (x, y, 0.02), M["iron"], bevel=0.01)
    return (W, 1.75, 3.0)


# ================================================================== notice board
def notice_board(M):
    W, H = 4.2, 2.9
    cork = material("Cork", "NH_Boards", tint=(0.62, 0.42, 0.24), scale=1.4, rough_add=0.35, wear=0.1)
    box("Cork", (W - 0.36, 0.05, H - 0.36), (0, 0.04, H / 2), cork, bevel=0.005)
    for name, size, loc in (("FrameTop", (W, 0.16, 0.2), (0, 0, H - 0.1)), ("FrameBottom", (W, 0.2, 0.22), (0, -0.02, 0.11)),
                            ("FrameL", (0.2, 0.16, H), (-W / 2 + 0.1, 0, H / 2)), ("FrameR", (0.2, 0.16, H), (W / 2 - 0.1, 0, H / 2))):
        box(name, size, loc, M["oak"], bevel=0.03)
    box("Ledge", (W - 0.2, 0.3, 0.06), (0, -0.12, 0.24), M["oakdark"], bevel=0.015)
    _gable("Crest", 0, 0.0, 1.0, H, H + 0.55, 0.14, M["oak"], M["oakdark"], edge=0.04)
    box("Plaque", (1.3, 0.04, 0.22), (0, -0.09, H - 0.1), M["brass"], bevel=0.01)
    _quatrefoil("Seal", 0, -0.09, H + 0.22, 0.12, M["brass"])
    for sx in (-1, 1):
        sphere(f"Boss{sx}", 0.07, (sx * (W / 2 - 0.1), -0.09, H - 0.1), M["brass"], seg=10, rings=5)
    rnd = random.Random(31)
    pins = [M["brass"], M["crimson"], M["brasssteel"]]
    placed = 0
    for row in range(3):
        for col in range(5):
            if rnd.random() < 0.18:
                continue
            w, h = rnd.uniform(0.45, 0.7), rnd.uniform(0.55, 0.8)
            x = -W / 2 + 0.55 + col * 0.78 + rnd.uniform(-0.08, 0.08)
            z = 0.55 + row * 0.75 + rnd.uniform(-0.06, 0.06) + h / 2
            if z + h / 2 > H - 0.25:
                continue
            ang = math.radians(rnd.uniform(-7, 7))
            placed += 1
            box(f"Paper{placed}", (w, 0.012, h), (x, -0.005, z), M["paper"], bevel=0.0, segments=1, rot=(0, ang, 0))
            if rnd.random() < 0.35:
                cyl(f"Seal{placed}", 0.06, 0.02, (x + w * 0.25, -0.02, z - h * 0.3), M["crimson"], rot=(math.pi / 2, 0, 0), verts=10)
            sphere(f"Pin{placed}", 0.03, (x, -0.03, z + h / 2 - 0.05), rnd.choice(pins), seg=8, rings=4)
    return (W, 0.4, H + 0.55)


# ================================================================== celestial globe
def celestial_globe(M):
    night = material("NightSky", base=(0.02, 0.035, 0.11), rough=0.35, wear=0.0, dirt=0.4)
    zc, R = 2.75, 0.85
    # oak tripod
    for k in range(3):
        a = k / 3 * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.08, s * 0.08, 1.7), (c * 0.45, s * 0.45, 1.0), (c * 0.82, s * 0.82, 0.08)], 0.06, M["oak"], square=True)
        sphere(f"Toe{k}", 0.08, (c * 0.84, s * 0.84, 0.06), M["brass"], seg=10, rings=5)
    ring("Stretcher", (0, 0, 0.75), 0.6, "Z", M["brass"], thick=0.03)
    cyl("Column", 0.11, 0.8, (0, 0, 1.75), M["oak"], verts=14)
    sphere("Knop", 0.16, (0, 0, 2.0), M["oakdark"], seg=12, rings=6, scale=(1, 1, 0.7))
    # horizon ring on three brass posts
    tube("Horizon", circle_pts(0, 0, zc, R + 0.16, "Z", 40), 0.05, M["brass"], closed=True, square=True, poly=True)
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 3
        tube(f"Post{k}", [(0, 0, 2.05), (math.cos(a) * 0.5, math.sin(a) * 0.5, 2.3), (math.cos(a) * (R + 0.16), math.sin(a) * (R + 0.16), zc)], 0.025, M["brass"])
    # the globe: night blue, brass stars and constellation lines, tilted on its axis
    tilt = math.radians(23.5)
    sphere("Globe", R, (0, 0, zc), night, seg=32, rings=16)
    tube("Meridian", circle_pts(0, 0, zc, R + 0.07, "X", 48, tilt=0), 0.03, M["brass"], closed=True, square=True, poly=True)
    ax = (0, math.sin(tilt), math.cos(tilt))
    tube("Axis", [(0, -ax[1] * (R + 0.18), zc - ax[2] * (R + 0.18)), (0, ax[1] * (R + 0.18), zc + ax[2] * (R + 0.18))], 0.02, M["brass"], poly=True)
    rnd = random.Random(5)
    stars = []
    for i in range(40):
        u, v = rnd.uniform(-1, 1), rnd.uniform(0, 2 * math.pi)
        x, y, z = math.sqrt(1 - u * u) * math.cos(v), math.sqrt(1 - u * u) * math.sin(v), u
        p = (x * (R + 0.005), y * (R + 0.005), zc + z * (R + 0.005))
        stars.append(p)
        sphere(f"Star{i}", rnd.choice((0.018, 0.022, 0.03)), p, M["brass"], seg=6, rings=3)
    for i in range(0, 24, 3):
        a, b = stars[i], stars[i + 1]
        mid = [(a[k] + b[k]) / 2 for k in range(3)]
        d = math.sqrt(mid[0] ** 2 + mid[1] ** 2 + (mid[2] - zc) ** 2) or 1
        m2 = (mid[0] / d * (R + 0.01), mid[1] / d * (R + 0.01), zc + (mid[2] - zc) / d * (R + 0.01))
        tube(f"Line{i}", [a, m2, b], 0.006, M["brass"])
    # a small crescent moon set in the meridian
    sphere("Moon", 0.07, (0, -(R + 0.07), zc + 0.35), M["chalk"], seg=10, rings=5)
    return (1.8, 1.8, zc + R + 0.25)


# ================================================================== alchemy table
def alchemy_table(M):
    W, D, H = 4.0, 2.0, 2.4
    box("Top", (W, D, 0.16), (0, 0, H), M["oak"], bevel=0.03)
    box("Apron", (W - 0.3, D - 0.3, 0.3), (0, 0, H - 0.22), M["oakdark"], bevel=0.02)
    for sx in (-1, 1):
        box(f"Drawer{sx}", (1.1, 0.04, 0.22), (sx * 0.9, -D / 2 + 0.13, H - 0.22), M["oak"], bevel=0.015)
        sphere(f"Pull{sx}", 0.04, (sx * 0.9, -D / 2 + 0.09, H - 0.22), M["brass"], seg=8, rings=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(sx * (W / 2 - 0.2), sy * (D / 2 - 0.2), 0.05), (sx * (W / 2 - 0.22), sy * (D / 2 - 0.22), H - 0.3)], 0.06, M["iron"], square=True, poly=True)
        tube(f"Brace{sx}", [(sx * (W / 2 - 0.2), -(D / 2 - 0.2), 0.5), (sx * (W / 2 - 0.2), 0, 0.75), (sx * (W / 2 - 0.2), D / 2 - 0.2, 0.5)], 0.035, M["iron"], square=True)
    box("Shelf", (W - 0.4, D - 0.4, 0.08), (0, 0, 0.55), M["oakdark"], bevel=0.015)
    # jars and a crate on the lower shelf
    for i, x in enumerate((-1.2, -0.85, -0.5)):
        cyl(f"Jar{i}", 0.13, 0.32, (x, 0.1, 0.75), M["glassamber"], verts=14)
        cyl(f"JarLid{i}", 0.14, 0.05, (x, 0.1, 0.93), M["oakdark"], verts=14)
    box("Crate", (0.8, 0.6, 0.4), (0.9, 0.1, 0.79), M["oak"], bevel=0.02)
    t = H + 0.08
    # open book and loose papers
    for sx in (-1, 1):
        box(f"Page{sx}", (0.42, 0.6, 0.03), (-0.9 + sx * 0.21, -0.2, t + 0.04), M["paper"], bevel=0.005, rot=(0, sx * math.radians(-6), 0))
    box("Cover", (0.9, 0.64, 0.02), (-0.9, -0.2, t + 0.01), M["leather"], bevel=0.005)
    box("Loose", (0.5, 0.35, 0.01), (0.2, -0.55, t + 0.01), M["paper"], bevel=0.0, segments=1, rot=(0, 0, math.radians(14)))
    # mortar and pestle
    cyl("Mortar", 0.2, 0.22, (1.4, -0.4, t + 0.11), M["stone"], verts=16)
    tube("Pestle", [(1.35, -0.4, t + 0.15), (1.55, -0.25, t + 0.42)], 0.035, M["stonedark"])
    # candle
    end = _candlestick("Candle", 1.55, 0.55, t, 0.18, M["brass"])
    cyl("Wax", 0.05, 0.24, (1.55, 0.55, end + 0.12), M["chalk"], verts=12)
    # test-tube rack
    box("Rack", (0.7, 0.18, 0.06), (0.4, 0.45, t + 0.25), M["oak"], bevel=0.01)
    box("RackBase", (0.7, 0.3, 0.05), (0.4, 0.45, t + 0.03), M["oak"], bevel=0.01)
    for sx in (-1, 1):
        box(f"RackEnd{sx}", (0.05, 0.3, 0.3), (0.4 + sx * 0.33, 0.45, t + 0.15), M["oak"], bevel=0.01)
    liquids = []
    set_group("Glass")
    for i in range(4):
        x = 0.4 - 0.24 + i * 0.16
        cyl(f"Tube{i}", 0.04, 0.42, (x, 0.45, t + 0.25), M["glassclear"], verts=10, bevel=0)
        liquids.append(((x, 0.45, t + 0.14), 0.034, 0.18))
    # round flasks and a retort
    for i, (x, y, r) in enumerate(((-0.25, 0.25, 0.24), (-0.65, 0.55, 0.18))):
        sphere(f"Flask{i}", r, (x, y, t + r), M["glassclear"], seg=16, rings=8)
        cyl(f"Neck{i}", r * 0.28, r * 1.4, (x, y, t + r * 2 + r * 0.55), M["glassclear"], verts=10, bevel=0)
        liquids.append(("sphere", (x, y, t + r * 0.8), r * 0.82))
    sphere("Retort", 0.2, (0.95, 0.25, t + 0.2), M["glassclear"], seg=16, rings=8)
    tube("RetortNeck", [(0.95, 0.25, t + 0.35), (1.05, 0.2, t + 0.6), (1.3, 0.1, t + 0.55), (1.45, 0.05, t + 0.42)], 0.04, M["glassclear"])
    set_group("Glow")
    for L in liquids:
        if L[0] == "sphere":
            sphere("Liquid", L[2], L[1], M["chalk"], seg=12, rings=6, scale=(1, 1, 0.75))
        else:
            cyl("TubeLiquid", L[1], L[2], L[0], M["chalk"], verts=10, bevel=0)
    sphere("RetortLiquid", 0.16, (0.95, 0.25, t + 0.16), M["chalk"], seg=12, rings=6, scale=(1, 1, 0.7))
    flame("Flame", (1.55, 0.55, end + 0.24), h=0.14)
    set_group("Main")
    return (W, D, t + 0.75)


# ================================================================== school bell
def school_bell(M):
    set_group("Bracket")
    box("WallPlate", (0.7, 0.08, 1.1), (0, 0.5, 1.75), M["iron"], bevel=0.02)
    for z in (1.32, 2.18):
        for sx in (-1, 1):
            sphere(f"Bolt{z}{sx}", 0.035, (sx * 0.24, 0.45, z), M["brass"], seg=8, rings=4)
    tube("Arm", [(0, 0.46, 2.05), (0, 0.1, 2.15), (0, -0.25, 2.12)], 0.045, M["iron"], square=True)
    tube("Brace", [(0, 0.46, 1.4), (0, 0.15, 1.7), (0, -0.05, 2.08)], 0.03, M["iron"])
    tube("Curl", [(0, 0.3, 1.55), (0, 0.18, 1.6), (0, 0.16, 1.75), (0, 0.26, 1.78)], 0.02, M["iron"])
    for sx in (-1, 1):
        tube(f"Yoke{sx}", [(sx * 0.42, -0.25, 2.12), (sx * 0.42, -0.25, 1.82)], 0.035, M["iron"], square=True, poly=True)
    tube("YokeTop", [(-0.42, -0.25, 2.12), (0.42, -0.25, 2.12)], 0.035, M["iron"], square=True, poly=True)
    # the bell swings on the axle between the yoke arms
    set_group("Bell", hinge=(0, -0.25, 1.82), swing=1)
    tube("Axle", [(-0.44, -0.25, 1.82), (0.44, -0.25, 1.82)], 0.025, M["brasssteel"], poly=True)
    cyl("Crown", 0.1, 0.12, (0, -0.25, 1.75), M["brass"], verts=14)
    sphere("Shoulder", 0.3, (0, -0.25, 1.55), M["brass"], seg=20, rings=10, scale=(1, 1, 0.55))
    cone("Waist", 0.48, 0.29, 0.5, (0, -0.25, 1.28), M["brass"], verts=28)
    cone("Flare", 0.56, 0.48, 0.12, (0, -0.25, 0.98), M["brass"], verts=28)
    ring("Lip", (0, -0.25, 0.92), 0.56, "Z", M["brass"], thick=0.035)
    ring("Band1", (0, -0.25, 1.4), 0.4, "Z", M["brass"], thick=0.02)
    ring("Band2", (0, -0.25, 1.12), 0.5, "Z", M["brass"], thick=0.018)
    _quatrefoil("Seal", 0, -0.25 - 0.44, 1.22, 0.1, M["crimson"])
    tube("ClapperRod", [(0, -0.25, 1.5), (0, -0.25, 1.0)], 0.02, M["iron"], poly=True)
    sphere("Clapper", 0.07, (0, -0.25, 0.96), M["iron"], seg=10, rings=5)
    tube("Lever", [(0.42, -0.25, 1.82), (0.6, -0.25, 1.86), (0.72, -0.25, 1.8)], 0.025, M["iron"])
    tube("Rope", [(0.72, -0.25, 1.78), (0.74, -0.28, 1.2), (0.72, -0.25, 0.4)], 0.025, M["oakdark"])
    set_group("Bracket")
    return (1.5, 1.1, 2.3)


# ================================================================== trophy cabinet
def trophy_cabinet(M):
    W, D, H = 4.0, 1.4, 6.4
    box("Plinth", (W + 0.15, D + 0.1, 0.5), (0, 0, 0.25), M["oakdark"], bevel=0.04)
    box("Drawers", (W, D, 1.0), (0, 0, 0.5 + 0.5), M["oak"], bevel=0.03)
    for sx in (-1, 1):
        box(f"DrawerFront{sx}", (1.7, 0.04, 0.7), (sx * 0.95, -D / 2 - 0.01, 1.0), M["oakdark"], bevel=0.02)
        tube(f"Pull{sx}", [(sx * 0.95 - 0.18, -D / 2 - 0.06, 1.05), (sx * 0.95, -D / 2 - 0.1, 0.98), (sx * 0.95 + 0.18, -D / 2 - 0.06, 1.05)], 0.02, M["brass"])
    for sx in (-1, 1):
        box(f"Side{sx}", (0.18, D, H - 1.5), (sx * (W / 2 - 0.09), 0, 1.5 + (H - 1.5) / 2), M["oak"], bevel=0.03)
    box("Back", (W - 0.2, 0.06, H - 1.5), (0, D / 2 - 0.05, 1.5 + (H - 1.5) / 2), M["leatherdark"], bevel=0.01)
    box("Cornice", (W + 0.25, D + 0.2, 0.22), (0, 0, H + 0.11), M["oakdark"], bevel=0.04)
    _gable("Crown", 0, -D / 2 + 0.08, W / 2 - 0.3, H + 0.22, H + 1.0, 0.14, M["oak"], M["oakdark"], edge=0.05)
    _quatrefoil("CrownSeal", 0, -D / 2 - 0.02, H + 0.55, 0.18, M["brass"])
    for sx in (-1, 1):
        _pinnacle(f"Pin{sx}", sx * (W / 2 - 0.1), -D / 2 + 0.1, H + 0.22, 0.8, M["oak"])
    box("Mullion", (0.12, 0.12, H - 1.6), (0, -D / 2 + 0.06, 1.5 + (H - 1.6) / 2), M["oakdark"], bevel=0.02)
    for sx in (-1, 1):
        tube(f"DoorFrame{sx}", _arch_loop(sx * 0.98, -D / 2 + 0.02, 0.88, 1.6, H - 1.2, H - 0.2), 0.05, M["oakdark"], square=True, closed=True, poly=True)
        sphere(f"Knob{sx}", 0.05, (sx * 0.16, -D / 2 - 0.06, 3.6), M["brass"], seg=8, rings=4)
    shelves_z = (1.55, 3.05, 4.5)
    # trophies: cups, a shield plaque, medals on ribbons
    def cup(prefix, x, z, s=1.0):
        cyl(f"{prefix}Foot", 0.16 * s, 0.06, (x, 0, z + 0.03), M["brass"], verts=16)
        cyl(f"{prefix}Stem", 0.04 * s, 0.25 * s, (x, 0, z + 0.06 + 0.125 * s), M["brass"], verts=10)
        sphere(f"{prefix}Knop", 0.06 * s, (x, 0, z + 0.12 * s), M["brass"], seg=10, rings=5)
        cone(f"{prefix}Bowl", 0.11 * s, 0.26 * s, 0.4 * s, (x, 0, z + 0.06 + 0.25 * s + 0.2 * s), M["brass"], verts=20)
        for sx in (-1, 1):
            ring(f"{prefix}Handle{sx}", (x + sx * 0.27 * s, 0, z + 0.06 + 0.4 * s), 0.11 * s, "Y", M["brass"], thick=0.02)
        return z
    cup("CupA", -1.2, shelves_z[1], 1.3)
    cup("CupB", 0.6, shelves_z[1], 1.0)
    cup("CupC", 1.25, shelves_z[2], 0.8)
    cup("CupD", -0.5, shelves_z[0], 1.5)
    # shield plaque
    box("ShieldBoard", (0.7, 0.06, 0.85), (-0.9, D / 2 - 0.12, shelves_z[2] + 0.55), M["oakdark"], bevel=0.02)
    tube("Shield", _arch_loop(-0.9, D / 2 - 0.16, 0.22, shelves_z[2] + 0.3, shelves_z[2] + 0.75, shelves_z[2] + 0.75), 0.03, M["brass"], square=True, closed=True, poly=True)
    _quatrefoil("ShieldSeal", -0.9, D / 2 - 0.18, shelves_z[2] + 0.58, 0.1, M["crimson"])
    # medals on a crimson ribbon
    for i, x in enumerate((0.3, 0.6, 0.9)):
        box(f"Ribbon{i}", (0.07, 0.01, 0.4), (x, D / 2 - 0.12, shelves_z[2] + 0.75), M["crimson"], bevel=0.0, segments=1)
        cyl(f"Medal{i}", 0.09, 0.02, (x, D / 2 - 0.13, shelves_z[2] + 0.5), M["brass"], rot=(math.pi / 2, 0, 0), verts=16)
    # a crossed pair of fencing foils on the bottom shelf
    for sx in (-1, 1):
        tube(f"Foil{sx}", [(1.2 + sx * 0.4, D / 2 - 0.2, shelves_z[0] + 0.1), (1.2 - sx * 0.4, D / 2 - 0.2, shelves_z[0] + 1.0)], 0.012, M["brasssteel"], poly=True)
        cyl(f"Guard{sx}", 0.06, 0.02, (1.2 + sx * 0.36, D / 2 - 0.2, shelves_z[0] + 0.15), M["brass"], verts=12)
    set_group("Glass")
    for z in shelves_z[1:]:
        box(f"ShelfGlass{z}", (W - 0.4, D - 0.25, 0.04), (0, 0.05, z), M["glassclear"], bevel=0.0, segments=1)
    for sx in (-1, 1):
        box(f"DoorGlass{sx}", (1.7, 0.02, H - 2.0), (sx * 0.98, -D / 2 + 0.03, 1.6 + (H - 2.0) / 2 + 0.1), M["glassclear"], bevel=0.0, segments=1)
    set_group("Main")
    box("Floor", (W - 0.3, D - 0.2, 0.05), (0, 0, shelves_z[0] - 0.03), M["oakdark"], bevel=0.01)
    return (W + 0.25, D + 0.2, H + 1.0)


P.BUILD.update({
    "GrandfatherClock": grandfather_clock,
    "WallSconce": wall_sconce,
    "HallBench": hall_bench,
    "NoticeBoard": notice_board,
    "CelestialGlobe": celestial_globe,
    "AlchemyTable": alchemy_table,
    "SchoolBell": school_bell,
    "TrophyCabinet": trophy_cabinet,
})
