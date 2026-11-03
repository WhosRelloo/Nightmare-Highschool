"""Props batch 7 (2026-11-03): sports and boiler-room props for nh_props.py, in the same gothic style.

  BallRack      an iron-and-brass two-tier ball cart on casters: basketballs above, soccer balls and footballs below
  Hurdle        an iron-framed track hurdle on weighted feet with a crimson and bone enamel bar
  TackleDummy   a padded crimson leather tackling dummy on a coil-sprung post, on an iron sled with a brass shield
  GymMatStack   four stacked leather gym mats (crimson and ink) with bone piping, quilting and brass grommets
  WaterKeg      an iron-banded keg on an iron cradle with a brass tap, a drip tray and tin cups
  Scoreboard    a gothic wall scoreboard: an iron frame and crest, two numeral panels with bone bar numerals (21 / 14),
                blank brass nameplates and three club-colour lamps (Ravens, Rovers, Wardens); wall piece
  Boiler        a riveted iron boiler on a firebox with a brass dome, gauges, a sight glass and a flue; the firebox door
                swings out (Door0: origin on the hinge), the fire behind it glows (Glow)
  PipeRun       a wall run of iron pipes with flanges, brackets, a brass gate valve, a gauge and a steam vent
  ValveWheel    a wall valve on a riser pipe with a crimson iron hand wheel (Wheel: origin on its axle, turns about Y)
  CoalPile      a heap of coal with a shovel stuck in it
  CoalCart      an iron coal cart on four spoked wheels, full of coal, with a push handle
  Workbench     an iron workbench with a vice, a pegboard tool rack, spanners, a hammer, an oil can and oily rags

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _quatrefoil, _pinnacle, _arch_loop, material
from nh_props_batch3 import sphere, flame
from nh_props_batch4 import lathe, hoop, prism, rrect, _mark, _xform, _aim, _dims, flat, _football, _solid


# ------------------------------------------------------------------ helpers

def lump(name, loc, r, mat, rnd, squash=0.8):
    """A faceted lump (coal, a rag): an ico sphere pushed in and out at random."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    for v in o.data.vertices:
        v.co *= 1 + rnd.uniform(-0.3, 0.2)
        v.co.z *= squash
    for f in o.data.polygons:
        f.use_smooth = False
    o.rotation_euler = (rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))
    return _finish(o, mat, 0)


def rivet_ring(prefix, cx, cy, z, r, n, mat, rr=0.04):
    for k in range(n):
        a = k / n * 2 * math.pi
        sphere(f"{prefix}{k}", rr, (cx + math.cos(a) * r, cy + math.sin(a) * r, z), mat, seg=6, rings=3)


def tub(name, bw, bd, tw, td, z0, z1, mat, thick=0.06):
    """An open-topped tapered tub (a cart body): bottom bw x bd at z0, top tw x td at z1."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    b = [bm.verts.new((sx * bw / 2, sy * bd / 2, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    t = [bm.verts.new((sx * tw / 2, sy * td / 2, z1)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(list(reversed(b)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((b[i], b[j], t[j], t[i]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    return _solid(ob, thick)


def spoked_wheel(prefix, c, r, axis, mat, hub_mat, spokes=8, thick=0.05):
    """An iron wheel facing along `axis` ('X' or 'Y'): a rim, a flange, spokes and a hub."""
    hoop(f"{prefix}Rim", c, r, axis, mat, thick=thick)
    hoop(f"{prefix}Flange", c, r * 0.82, axis, mat, thick=thick * 0.6)
    for k in range(spokes):
        a = k / spokes * 2 * math.pi
        u, v = math.cos(a), math.sin(a)
        if axis == "X":
            p0, p1 = (c[0], c[1] + u * r * 0.18, c[2] + v * r * 0.18), (c[0], c[1] + u * r * 0.95, c[2] + v * r * 0.95)
        else:
            p0, p1 = (c[0] + u * r * 0.18, c[1], c[2] + v * r * 0.18), (c[0] + u * r * 0.95, c[1], c[2] + v * r * 0.95)
        tube(f"{prefix}Spoke{k}", [p0, p1], thick * 0.5, mat, square=True, poly=True)
    rot = (0, math.pi / 2, 0) if axis == "X" else (math.pi / 2, 0, 0)
    cyl(f"{prefix}Hub", r * 0.2, thick * 3, c, hub_mat, rot=rot, verts=14, bevel=0.01)


SEG = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abcdfg"}


def digit(prefix, d, cx, y, cz, h, mat):
    """A bar numeral (seven segments) in the XZ plane, facing -Y."""
    w, t = h * 0.55, h * 0.13
    where = {"a": (0, h / 2, True), "g": (0, 0, True), "d": (0, -h / 2, True), "f": (-w / 2, h / 4, False),
             "b": (w / 2, h / 4, False), "e": (-w / 2, -h / 4, False), "c": (w / 2, -h / 4, False)}
    for s in SEG[d]:
        dx, dz, horiz = where[s]
        size = (w - t * 0.7, 0.04, t) if horiz else (t, 0.04, h / 2 - t * 0.7)
        box(f"{prefix}{s}", size, (cx + dx, y, cz + dz), mat, bevel=0.012, segments=1)


def basketball(prefix, c, r, rnd, skin, seam):
    s = _mark()
    sphere(f"{prefix}Ball", r, (0, 0, 0), skin, seg=20, rings=10)
    hoop(f"{prefix}Eq", (0, 0, 0), r * 1.003, "Z", seam, thick=0.011)
    hoop(f"{prefix}Mer", (0, 0, 0), r * 1.003, "X", seam, thick=0.011)
    for sy in (-1, 1):
        hoop(f"{prefix}Curve{sy}", (0, sy * r * 0.55, 0), r * 0.838, "Y", seam, thick=0.011)
    _xform(s, Matrix.Translation(c) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, "X"))


def soccer_ball(prefix, c, r, rnd, bone, ink):
    s = _mark()
    sphere(f"{prefix}Ball", r, (0, 0, 0), bone, seg=20, rings=10)
    phi = (1 + math.sqrt(5)) / 2
    dirs = []
    for a in (-1, 1):
        for b in (-phi, phi):
            dirs += [Vector((0, a, b)), Vector((a, b, 0)), Vector((b, 0, a))]
    for k, d in enumerate(dirs):
        d = d.normalized()
        m = _mark()
        sphere(f"{prefix}Patch{k}", 1, (0, 0, 0), ink, seg=8, rings=4, scale=(r * 0.36, r * 0.36, r * 0.06))
        _xform(m, Matrix.Translation(d * r * 0.985) @ _aim(d))
    _xform(s, Matrix.Translation(c) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, "Y"))


def spanner(prefix, mtx, mat, L=0.6):
    """A flat spanner along X in the XY plane: a ring end and an open jaw."""
    s = _mark()
    box(f"{prefix}Shank", (L, 0.055, 0.018), (0, 0, 0.009), mat, bevel=0.006)
    hoop(f"{prefix}Ring", (L / 2 + 0.04, 0, 0.012), 0.055, "Z", mat, thick=0.018)
    for sy in (-1, 1):
        box(f"{prefix}Jaw{sy}", (0.11, 0.03, 0.02), (-L / 2 - 0.05, sy * 0.05, 0.01), mat, bevel=0.006, rot=(0, 0, sy * 0.35))
    _xform(s, mtx)


def coal_mat():
    return flat("Coal", (0.016, 0.015, 0.018), 0.55, dirt=0.5)


def enamel():
    """Crimson enamel for thin parts (the painted-metal set reads pink on a thin tube)."""
    return flat("CrimsonEnamel", (0.2, 0.018, 0.028), 0.35, wear=0.04, dirt=0.6)


# ================================================================== ball rack
def ball_rack(M):
    W, D = 3.8, 1.3
    hide = material("FootballHide", "NH_Leather", tint=(0.32, 0.13, 0.06), scale=2.4, normal=0.6, wear=0.15, dirt=0.75)
    lace = flat("Lace", (0.86, 0.84, 0.78), 0.7)
    skin = material("BasketHide", "NH_Leather", tint=(0.42, 0.14, 0.045), scale=3.0, normal=0.7, rough_add=0.15, wear=0.1, dirt=0.7)
    seam = flat("Seam", (0.02, 0.018, 0.02), 0.6)
    bone = flat("BallBone", (0.76, 0.73, 0.66), 0.45, dirt=0.7)
    rnd = random.Random(70)
    # end frames, tiers of paired rails, casters
    for sx in (-1, 1):
        x = sx * W / 2
        for sy in (-1, 1):
            tube(f"Post{sx}{sy}", [(x, sy * D / 2, 0.28), (x, sy * D / 2, 2.75)], 0.05, M["iron"], square=True, poly=True)
            sphere(f"Knob{sx}{sy}", 0.08, (x, sy * D / 2, 2.82), M["brass"], seg=10, rings=5)
            cyl(f"Caster{sx}{sy}", 0.12, 0.06, (x, sy * D / 2, 0.14), M["iron"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.01)
            box(f"Fork{sx}{sy}", (0.06, 0.12, 0.2), (x, sy * D / 2, 0.24), M["iron"], bevel=0.01)
        tube(f"EndTop{sx}", [(x, -D / 2, 2.6), (x, D / 2, 2.6)], 0.04, M["iron"], square=True, poly=True)
        tube(f"EndLow{sx}", [(x, -D / 2, 0.32), (x, D / 2, 0.32)], 0.04, M["iron"], square=True, poly=True)
        tube(f"Brace{sx}", [(x, -D / 2, 0.32), (x, 0, 0.62), (x, D / 2, 0.32)], 0.025, M["iron"])
        hoop(f"EndFoil{sx}", (x, 0, 2.02), 0.16, "X", M["brass"], thick=0.02)
    tiers = ((0.62, 0.38), (1.72, 0.4))      # rail height, ball radius
    for i, (zr, br) in enumerate(tiers):
        for sy in (-1, 1):
            tube(f"Rail{i}{sy}", [(-W / 2, sy * 0.32, zr), (W / 2, sy * 0.32, zr)], 0.04, M["iron"], poly=True)
        for k in range(5):
            x = -W / 2 + 0.3 + k * (W - 0.6) / 4
            tube(f"Cross{i}{k}", [(x, -0.32, zr - 0.02), (x, 0.32, zr - 0.02)], 0.025, M["iron"], poly=True)
    tube("TopRailF", [(-W / 2, -D / 2, 2.6), (W / 2, -D / 2, 2.6)], 0.035, M["brass"], poly=True)
    tube("TopRailB", [(-W / 2, D / 2, 2.6), (W / 2, D / 2, 2.6)], 0.035, M["brass"], poly=True)
    # the balls sit in the troughs between the rails
    zb = tiers[1][0] + math.sqrt(0.4 ** 2 - 0.3 ** 2) + 0.03
    for k, x in enumerate((-1.35, -0.45, 0.45, 1.35)):
        basketball(f"Basket{k}", (x + rnd.uniform(-0.04, 0.04), 0, zb), 0.4, rnd, skin, seam)
    zs = tiers[0][0] + math.sqrt(0.38 ** 2 - 0.3 ** 2) + 0.03
    for k, x in enumerate((-1.4, -0.55, 1.35)):
        soccer_ball(f"Soccer{k}", (x, 0, zs), 0.38, rnd, bone, seam)
    for k, (x, roll) in enumerate(((0.15, 0.0), (0.8, 0.9))):
        _football(f"Foot{k}", Matrix.Translation((x, 0, tiers[0][0] + 0.17)) @ Matrix.Rotation(math.pi / 2, 4, "Y") @
                  Matrix.Rotation(roll, 4, "Z"), hide, lace)
    return _dims()


# ================================================================== hurdle
def hurdle(M):
    W = 3.4
    bone = flat("Bone", (0.78, 0.75, 0.67), 0.4, wear=0.05)
    for sx in (-1, 1):
        x = sx * W / 2
        tube(f"Foot{sx}", [(x, -0.15, 0.06), (x, 1.15, 0.06)], 0.06, M["iron"], square=True, poly=True)
        box(f"Weight{sx}", (0.22, 0.5, 0.18), (x, 0.85, 0.12), M["iron"], bevel=0.03)
        tube(f"Upright{sx}", [(x, 0, 0.1), (x, 0, 2.55)], 0.055, M["iron"], square=True, poly=True)
        tube(f"Strut{sx}", [(x, 0.75, 0.1), (x, 0.05, 1.2)], 0.035, M["iron"], square=True, poly=True)
        cyl(f"Collar{sx}", 0.09, 0.14, (x, 0, 1.9), M["brass"], verts=12, bevel=0.015)
        cyl(f"Knob{sx}", 0.07, 0.1, (x, -0.12, 1.9), M["brass"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.01)
        sphere(f"Finial{sx}", 0.08, (x, 0, 2.6), M["brass"], seg=10, rings=5)
    tube("LowBar", [(-W / 2, 0, 0.42), (W / 2, 0, 0.42)], 0.04, M["iron"], poly=True)
    # the crimson bar with bone bands
    box("Bar", (W - 0.1, 0.07, 0.42), (0, -0.07, 2.32), M["crimson"], bevel=0.02)
    for k in range(5):
        x = -W / 2 + 0.45 + k * (W - 0.9) / 4
        box(f"Band{k}", (0.22, 0.075, 0.425), (x, -0.07, 2.32), bone, bevel=0.012)
    box("BarRail", (W - 0.1, 0.09, 0.05), (0, -0.07, 2.08), M["iron"], bevel=0.01)
    return _dims()


# ================================================================== tackle dummy
def tackle_dummy(M):
    z0 = 1.0
    thread = flat("Thread", (0.7, 0.66, 0.58), 0.7)
    # iron sled: two runners curling up at the front, cross bars, a sprung post
    for sx in (-1, 1):
        x = sx * 0.8
        tube(f"Runner{sx}", [(x, 1.5, 0.08), (x, -0.9, 0.08), (x, -1.4, 0.25), (x, -1.5, 0.55)], 0.06, M["iron"], square=True)
        tube(f"Strut{sx}", [(x, 0.9, 0.12), (0, 0.15, 0.85)], 0.035, M["iron"], square=True, poly=True)
        tube(f"StrutF{sx}", [(x, -0.7, 0.12), (0, -0.15, 0.85)], 0.035, M["iron"], square=True, poly=True)
    for y in (1.3, 0.0, -0.9):
        tube(f"Cross{y}", [(-0.8, y, 0.12), (0.8, y, 0.12)], 0.04, M["iron"], square=True, poly=True)
    tube("PushBar", [(-0.8, -1.5, 0.55), (0.8, -1.5, 0.55)], 0.05, M["iron"], poly=True)
    box("Plate", (0.6, 0.6, 0.06), (0, 0, 0.88), M["brass"], bevel=0.015)
    cyl("Post", 0.1, 0.9, (0, 0, 0.5), M["iron"], verts=14, bevel=0.01)
    pts = []
    for i in range(49):
        t = i / 48
        a = t * 7 * 2 * math.pi
        pts.append((math.cos(a) * 0.19, math.sin(a) * 0.19, 0.18 + 0.68 * t))
    tube("Spring", pts, 0.025, M["brasssteel"], res=2)
    # the pad: crimson leather, bands, side handles, a brass Wardens shield
    lathe("Pad", [(0, z0 - 0.05), (0.42, z0 - 0.05), (0.52, z0 + 0.05), (0.56, z0 + 0.4), (0.57, z0 + 1.6), (0.55, z0 + 2.6),
                  (0.5, z0 + 2.95), (0.36, z0 + 3.12), (0, z0 + 3.16)], M["leather"], seg=36)
    for z in (z0 + 0.55, z0 + 1.55, z0 + 2.55):
        hoop(f"Band{z:.2f}", (0, 0, z), 0.575, "Z", M["leatherdark"], thick=0.04)
    for z in (z0 + 1.05, z0 + 2.05):
        hoop(f"Stitch{z:.2f}", (0, 0, z), 0.572, "Z", thread, thick=0.008)
    for sx in (-1, 1):
        tube(f"Handle{sx}", [(sx * 0.56, -0.18, z0 + 1.9), (sx * 0.74, -0.12, z0 + 1.95), (sx * 0.74, 0.12, z0 + 1.95), (sx * 0.56, 0.18, z0 + 1.9)],
             0.035, M["leatherdark"])
    tube("Shield", _arch_loop(0, -0.6, 0.2, z0 + 1.2, z0 + 1.6, z0 + 1.85), 0.022, M["brass"], square=True, closed=True, poly=True)
    _quatrefoil("ShieldSeal", 0, -0.61, z0 + 1.52, 0.09, M["brass"])
    return _dims()


# ================================================================== gym mats
def gym_mat_stack(M):
    thread = flat("Thread", (0.72, 0.68, 0.6), 0.7)
    crim = material("MatCrimson", "NH_Leather", tint=(0.2, 0.025, 0.04), scale=1.8, normal=0.5, wear=0.1, dirt=0.75)
    ink = material("MatInk", "NH_Leather", tint=(0.045, 0.06, 0.16), scale=1.8, normal=0.5, wear=0.1, dirt=0.75)
    mats = [crim, ink, crim, ink]
    hw, hd, t = 2.0, 1.2, 0.32
    for k, mat in enumerate(mats):
        s = _mark()
        box(f"Mat{k}", (2 * hw, 2 * hd, t), (0, 0, t / 2), mat, bevel=0.1, segments=3)
        for zz in (0.04, t - 0.04):
            tube(f"Piping{k}{zz:.2f}", rrect(hw - 0.035, hd - 0.035, 0.11, zz), 0.022, thread, closed=True, poly=True)
        for i in range(1, 4):
            x = -hw + i * hw / 2
            tube(f"Quilt{k}{i}", [(x, -hd + 0.12, t + 0.004), (x, hd - 0.12, t + 0.004)], 0.008, thread, poly=True)
        for sx in (-1, 1):
            for sy in (-1, 1):
                hoop(f"Grommet{k}{sx}{sy}", (sx * (hw - 0.18), sy * (hd - 0.18), t + 0.004), 0.05, "Z", M["brass"], thick=0.014)
            tube(f"Strap{k}{sx}", [(sx * hw, -0.35, t * 0.5), (sx * (hw + 0.1), -0.28, t * 0.5), (sx * (hw + 0.1), 0.28, t * 0.5),
                                    (sx * hw, 0.35, t * 0.5)], 0.03, M["leatherdark"], square=True)
        _xform(s, Matrix.Translation((0.05 * math.sin(k * 2.3), 0.05 * math.cos(k * 1.9), k * (t + 0.003))) @
               Matrix.Rotation(math.radians((-3, 4, -1, 6)[k]), 4, "Z"))
    return _dims()


# ================================================================== water keg
def water_keg(M):
    kz, R, L = 1.9, 0.76, 1.1
    tin = flat("Tin", (0.6, 0.6, 0.62), 0.3, metal=1.0, wear=0.2, dirt=0.8)
    stave = material("Stave", "NH_DeskWood", tint=(0.07, 0.045, 0.032), scale=0.3, rough_add=0.1, wear=0.2)
    # the keg lies along Y (tap end at the front): built along Z, then turned
    s = _mark()
    lathe("Keg", [(0, -L), (0.6, -L), (0.66, -L + 0.04), (0.72, -0.6), (R, 0), (0.72, 0.6), (0.66, L - 0.04), (0.6, L), (0, L)], stave,
          seg=48, flute=(24, 0.025))
    for z, r in ((-0.95, 0.68), (-0.5, 0.735), (0.5, 0.735), (0.95, 0.68)):
        hoop(f"Hoop{z}", (0, 0, z), r + 0.012, "Z", M["iron"], thick=0.035)
    for z in (-L + 0.005, L - 0.005):
        hoop(f"Chime{z}", (0, 0, z), 0.6, "Z", M["iron"], thick=0.03)
    cyl("Bung", 0.08, 0.05, (0, 0, L + 0.01), M["brass"], verts=12, bevel=0.01)
    _xform(s, Matrix.Translation((0, 0, kz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    # brass tap at the front end, a lever, a drip tray
    tube("Spout", [(0, -L - 0.02, kz - 0.32), (0, -L - 0.24, kz - 0.32), (0, -L - 0.3, kz - 0.42)], 0.04, M["brass"])
    cyl("TapBody", 0.08, 0.16, (0, -L - 0.1, kz - 0.32), M["brass"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.01)
    box("Lever", (0.05, 0.05, 0.22), (0, -L - 0.12, kz - 0.18), M["brass"], bevel=0.01)
    sphere("LeverKnob", 0.04, (0, -L - 0.12, kz - 0.06), M["crimson"], seg=8, rings=4)
    lathe("DripTray", [(0, 0), (0.22, 0), (0.24, 0.05), (0.22, 0.06), (0, 0.02)], M["brass"], seg=20, loc=(0, -L - 0.3, kz - 0.82))
    tube("TrayArm", [(0, -L - 0.3, kz - 0.82), (0, -L + 0.05, kz - 0.86), (0, -L + 0.3, kz - 0.86)], 0.025, M["iron"], poly=True)
    # iron cradle and stand with a cup shelf
    for y in (-0.62, 0.62):
        arc = [(math.cos(a) * (R + 0.05), y, kz + math.sin(a) * (R + 0.05)) for a in [math.radians(v) for v in range(200, 341, 20)]]
        tube(f"Cradle{y}", arc, 0.04, M["iron"], square=True, poly=True)
        for sx in (-1, 1):
            tube(f"Leg{y}{sx}", [(sx * 0.75, y, kz - 0.3), (sx * 0.85, y * 1.15, 0.04)], 0.045, M["iron"], square=True, poly=True)
            box(f"Pad{y}{sx}", (0.16, 0.16, 0.04), (sx * 0.85, y * 1.15, 0.02), M["iron"], bevel=0.01)
    for sx in (-1, 1):
        tube(f"Rail{sx}", [(sx * 0.8, -0.7, 0.45), (sx * 0.8, 0.7, 0.45)], 0.035, M["iron"], square=True, poly=True)
    box("Shelf", (1.6, 1.4, 0.05), (0, 0, 0.48), M["iron"], bevel=0.01)
    for k, (x, y) in enumerate(((-0.45, -0.3), (0.0, -0.4), (0.42, -0.25), (0.25, 0.3))):
        lathe(f"Cup{k}", [(0, 0), (0.12, 0), (0.13, 0.02), (0.14, 0.24), (0.15, 0.26), (0.13, 0.26), (0.12, 0.04), (0, 0.04)], tin, seg=16,
              loc=(x, y, 0.505))
        tube(f"CupHandle{k}", [(x + 0.13, y, 0.7), (x + 0.22, y, 0.66), (x + 0.22, y, 0.56), (x + 0.135, y, 0.52)], 0.012, tin)
    return _dims()


# ================================================================== scoreboard
def scoreboard(M):
    W, z0, z1 = 7.0, 0.8, 4.6
    lacquer = flat("BlackLacquer", (0.022, 0.02, 0.025), 0.2, wear=0.12, dirt=0.6)
    bone = flat("Bone", (0.8, 0.77, 0.68), 0.45, dirt=0.5)
    lamps = [flat("LampRavens", (0.19, 0.06, 0.37), 0.15), flat("LampRovers", (0.06, 0.26, 0.1), 0.15), flat("LampWardens", (0.4, 0.045, 0.03), 0.15)]
    box("Back", (W, 0.12, z1 - z0), (0, 0.1, (z0 + z1) / 2), lacquer, bevel=0.02)
    tube("Frame", [(-W / 2, -0.02, z0), (W / 2, -0.02, z0), (W / 2, -0.02, z1), (-W / 2, -0.02, z1)], 0.1, M["iron"], square=True, closed=True, poly=True)
    tube("Bead", [(-W / 2 + 0.16, -0.08, z0 + 0.16), (W / 2 - 0.16, -0.08, z0 + 0.16), (W / 2 - 0.16, -0.08, z1 - 0.16),
                  (-W / 2 + 0.16, -0.08, z1 - 0.16)], 0.025, M["brass"], closed=True, poly=True)
    # two numeral panels: 21 and 14
    for side, (cx, num) in enumerate(((-1.75, (2, 1)), (1.75, (1, 4)))):
        box(f"Panel{side}", (2.6, 0.05, 2.15), (cx, 0.02, 2.75), M["glass"], bevel=0.01)
        tube(f"PanelRim{side}", [(cx - 1.3, -0.02, 1.68), (cx + 1.3, -0.02, 1.68), (cx + 1.3, -0.02, 3.82), (cx - 1.3, -0.02, 3.82)],
             0.03, M["brass"], closed=True, poly=True)
        for k, d in enumerate(num):
            digit(f"Num{side}{k}", d, cx + (k - 0.5) * 1.05, -0.02, 2.75, 1.6, bone)
        box(f"Name{side}", (1.6, 0.04, 0.28), (cx, -0.02, 1.25), M["brass"], bevel=0.012)
    # centre: a brass divider with a quatrefoil, the three club lamps above
    box("Divider", (0.12, 0.05, 2.3), (0, -0.02, 2.75), M["brass"], bevel=0.01)
    _quatrefoil("DividerSeal", 0, -0.06, 2.75, 0.14, M["brass"])
    for k, (x, lamp) in enumerate(zip((-0.7, 0.0, 0.7), lamps)):
        cyl(f"LampCup{k}", 0.17, 0.1, (x, -0.06, 4.18), M["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.012)
        sphere(f"Lamp{k}", 0.13, (x, -0.13, 4.18), lamp, seg=14, rings=7)
        hoop(f"LampCage{k}", (x, -0.16, 4.18), 0.15, "Y", M["iron"], thick=0.012)
    # header, crest and pinnacles, bottom brackets
    box("Header", (W + 0.3, 0.2, 0.36), (0, 0.02, z1 + 0.18), M["iron"], bevel=0.03)
    box("HeaderBead", (W + 0.3, 0.04, 0.05), (0, -0.09, z1 + 0.05), M["brass"], bevel=0.01)
    _gable("Crest", 0, 0.02, 1.3, z1 + 0.36, z1 + 1.35, 0.16, M["iron"], M["brass"], edge=0.035)
    _quatrefoil("CrestSeal", 0, -0.07, z1 + 0.75, 0.16, M["crimson"])
    for sx in (-1, 1):
        _pinnacle(f"Pin{sx}", sx * (W / 2 + 0.05), 0.02, z1 + 0.36, 0.8, M["iron"])
        tube(f"Bracket{sx}", [(sx * (W / 2 - 0.4), 0.12, z0), (sx * (W / 2 - 0.42), -0.05, z0 - 0.3), (sx * (W / 2 - 0.55), -0.12, z0 - 0.62),
                              (sx * (W / 2 - 0.72), -0.05, z0 - 0.72), (sx * (W / 2 - 0.78), 0.06, z0 - 0.6)], 0.035, M["iron"], square=True)
        box(f"WallPlate{sx}", (0.3, 0.05, 0.9), (sx * (W / 2 - 0.4), 0.18, z0 - 0.35), M["iron"], bevel=0.01)
    return _dims()


# ================================================================== boiler
def boiler(M):
    fire = flat("Fire", (1.0, 0.42, 0.12), 0.5)
    set_group("Main")
    # firebox: a box with a tunnel mouth at the front (x -0.6..0.6, z 0.35..1.35)
    box("FireBack", (3.2, 2.5, 1.8), (0, 0.35, 0.9), M["iron"], bevel=0.04)
    for sx in (-1, 1):
        box(f"Cheek{sx}", (1.0, 0.72, 1.8), (sx * 1.1, -1.25, 0.9), M["iron"], bevel=0.03)
    box("Lintel", (1.2, 0.72, 0.45), (0, -1.25, 1.575), M["iron"], bevel=0.03)
    box("Sill", (1.2, 0.72, 0.35), (0, -1.25, 0.175), M["iron"], bevel=0.03)
    box("Plinth", (3.5, 3.5, 0.12), (0, 0, 0.06), M["stonedark"], bevel=0.03)
    tube("MouthRim", [(-0.62, -1.62, 0.33), (0.62, -1.62, 0.33), (0.62, -1.62, 1.37), (-0.62, -1.62, 1.37)], 0.035, M["brass"],
         square=True, closed=True, poly=True)
    for k in range(5):
        x = -0.45 + k * 0.225
        tube(f"Grate{k}", [(x, -1.55, 0.45), (x, -0.95, 0.45)], 0.025, M["iron"], square=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sphere(f"CornerBolt{sx}{sz}", 0.05, (sx * 1.45, -1.62, 0.9 + sz * 0.7), M["brass"], seg=8, rings=4)
    for z in (0.55, 1.15):
        cyl(f"Knuckle{z}", 0.05, 0.22, (-0.64, -1.68, z), M["iron"], verts=10, bevel=0.005)
    # the shell: riveted iron with bands, a brass dome, a flue
    lathe("Shell", [(0, 1.75), (1.5, 1.75), (1.5, 1.85), (1.42, 1.95), (1.42, 5.9), (1.3, 6.2), (0.9, 6.45), (0, 6.55)], M["iron"], seg=48)
    for z in (2.3, 4.0, 5.6):
        hoop(f"Band{z}", (0, 0, z), 1.435, "Z", M["iron"], thick=0.05)
        rivet_ring(f"Rivet{z}", 0, 0, z + 0.09, 1.44, 28, M["iron"], rr=0.035)
    lathe("Dome", [(0, 6.35), (0.55, 6.35), (0.56, 6.85), (0.48, 7.1), (0.28, 7.24), (0, 7.27)], M["brass"], seg=32, loc=(0, -0.45, 0))
    hoop("DomeBead", (0, -0.45, 6.82), 0.565, "Z", M["brass"], thick=0.025)
    lathe("SafetyValve", [(0, 7.2), (0.09, 7.2), (0.09, 7.42), (0.14, 7.46), (0.05, 7.56), (0, 7.56)], M["brass"], seg=14, loc=(0, -0.45, 0))
    tube("Flue", [(0, 0.6, 6.3), (0, 0.6, 8.3)], 0.24, M["iron"], poly=True)
    lathe("FlueCap", [(0.2, 8.25), (0.34, 8.35), (0.36, 8.45), (0.22, 8.5)], M["iron"], seg=20, loc=(0, 0.6, 0))
    hoop("FlueBand", (0, 0.6, 7.0), 0.245, "Z", M["iron"], thick=0.03)
    # front fittings: two gauges, a sight glass, a maker's plate with the Crimson Court quatrefoil
    for k, x in enumerate((-0.55, 0.55)):
        y = -math.sqrt(1.42 ** 2 - x * x)
        tube(f"GaugePipe{k}", [(x, y + 0.05, 4.65), (x, y - 0.18, 4.65)], 0.035, M["brass"], poly=True)
        cyl(f"Gauge{k}", 0.24, 0.08, (x, y - 0.22, 4.65), M["brass"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.015)
        cyl(f"GaugeDial{k}", 0.2, 0.01, (x, y - 0.265, 4.65), M["paper"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0)
        box(f"GaugeNeedle{k}", (0.012, 0.008, 0.16), (x + 0.04, y - 0.275, 4.68), M["iron"], bevel=0.0, segments=1, rot=(0, 0.6 - k, 0))
        box(f"GaugeRed{k}", (0.07, 0.008, 0.015), (x + 0.13, y - 0.272, 4.58), M["crimson"], bevel=0.0, segments=1, rot=(0, 2.1, 0))
    x = 1.0
    y = -math.sqrt(1.42 ** 2 - x * x)
    for z in (2.8, 3.9):
        tube(f"SightCock{z}", [(x, y + 0.05, z), (x, y - 0.22, z)], 0.04, M["brass"], poly=True)
    cyl("SightGlass", 0.045, 1.0, (x, y - 0.22, 3.35), M["glassamber"], verts=12, bevel=0)
    for sx in (-1, 1):
        tube(f"SightGuard{sx}", [(x + sx * 0.07, y - 0.24, 2.85), (x + sx * 0.07, y - 0.24, 3.85)], 0.012, M["brass"], poly=True)
    box("MakersPlate", (0.9, 0.06, 0.5), (-0.1, -1.44, 3.2), M["brass"], bevel=0.02)
    _quatrefoil("CourtSeal", -0.1, -1.48, 3.2, 0.14, M["crimson"])
    # a feed pipe down the right side with a valve
    tube("FeedPipe", [(1.3, 0.55, 5.0), (1.75, 0.55, 4.9), (1.8, 0.55, 4.4), (1.8, 0.55, 1.9)], 0.08, M["iron"])
    lathe("FeedValve", [(0, 3.2), (0.15, 3.2), (0.19, 3.3), (0.15, 3.42), (0, 3.42)], M["brass"], seg=16, loc=(1.8, 0.55, 0))
    hoop("FeedWheel", (1.8, 0.55, 3.62), 0.16, "Z", enamel(), thick=0.02)
    tube("FeedSpindle", [(1.8, 0.55, 3.42), (1.8, 0.55, 3.62)], 0.02, M["iron"], poly=True)
    # the fire: glowing coals on the grate and flames, behind the door
    rnd = random.Random(7)
    set_group("Glow")
    for k in range(14):
        lump(f"Ember{k}", (rnd.uniform(-0.45, 0.45), rnd.uniform(-1.4, -1.0), 0.52 + rnd.uniform(0, 0.12)), rnd.uniform(0.07, 0.11), fire, rnd, squash=0.7)
    for k, (x, y, h) in enumerate(((-0.25, -1.15, 0.42), (0.05, -1.25, 0.5), (0.3, -1.1, 0.38), (-0.05, -1.05, 0.34))):
        flame(f"Flame{k}", (x, y, 0.5), h=h)
    # the firebox door: swings out on its left hinge
    set_group("Door0", hinge=(-0.64, -1.68, 0.0), swing=-1)
    box("Door", (1.32, 0.08, 1.14), (0.02, -1.68, 0.85), M["iron"], bevel=0.02)
    tube("DoorRim", [(-0.6, -1.73, 0.32), (0.64, -1.73, 0.32), (0.64, -1.73, 1.38), (-0.6, -1.73, 1.38)], 0.025, M["iron"], square=True,
         closed=True, poly=True)
    for k in range(4):
        box(f"Vent{k}", (0.7, 0.05, 0.06), (0.05, -1.74, 1.12 - k * 0.12), M["glass"], bevel=0.008)
    for z in (0.55, 1.15):
        box(f"Strap{z}", (0.5, 0.03, 0.09), (-0.37, -1.735, z), M["iron"], bevel=0.008)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sphere(f"DoorRivet{sx}{sz}", 0.03, (0.02 + sx * 0.56, -1.74, 0.85 + sz * 0.47), M["brass"], seg=6, rings=3)
    tube("Latch", [(0.5, -1.74, 0.72), (0.5, -1.86, 0.72), (0.5, -1.86, 0.98), (0.5, -1.74, 0.98)], 0.022, M["brass"])
    _quatrefoil("DoorSeal", 0.05, -1.74, 0.55, 0.1, M["brass"])
    set_group("Main")
    return _dims()


# ================================================================== pipe run
def pipe_run(M):
    y = -0.35
    zt, zl = 3.2, 2.4
    # the top main: down to the floor on the left, into the wall on the right
    tube("Main", [(3.75, y, zt), (-3.55, y, zt)], 0.2, M["iron"], poly=True)
    tube("ElbowL", [(-3.55, y, zt), (-3.85, y, zt), (-3.95, y, zt - 0.15), (-3.95, y, zt - 0.45)], 0.2, M["iron"])
    tube("DropL", [(-3.95, y, zt - 0.45), (-3.95, y, 0.2)], 0.2, M["iron"], poly=True)
    tube("ElbowR", [(3.75, y, zt), (4.0, y, zt), (4.1, y + 0.15, zt), (4.1, 0.35, zt)], 0.2, M["iron"])
    cyl("FootFlange", 0.32, 0.12, (-3.95, y, 0.18), M["iron"], verts=24, bevel=0.015)
    # the lower line: straight, capped both ends
    tube("Lower", [(-3.2, y + 0.05, zl), (3.6, y + 0.05, zl)], 0.14, M["iron"], poly=True)
    for x in (-3.2, 3.6):
        cyl(f"Cap{x}", 0.18, 0.1, (x, y + 0.05, zl), M["iron"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.02)
    # flanges with bolts, wall brackets
    for k, (x, z, r) in enumerate(((-2.4, zt, 0.31), (0.6, zt, 0.31), (2.4, zt, 0.31), (-1.4, zl, 0.23), (1.9, zl, 0.23))):
        yy = y + (0.05 if z == zl else 0)
        cyl(f"Flange{k}", r, 0.1, (x, yy, z), M["iron"], rot=(0, math.pi / 2, 0), verts=24, bevel=0.012)
        for b in range(6):
            a = b / 6 * 2 * math.pi
            sphere(f"Bolt{k}{b}", 0.035, (x - 0.06, yy + math.cos(a) * r * 0.78, z + math.sin(a) * r * 0.78), M["brass"], seg=6, rings=3)
    for k, x in enumerate((-3.0, -0.6, 1.5, 3.2)):
        for z, r in ((zt, 0.215), (zl, 0.155)):
            yy = y + (0.05 if z == zl else 0)
            hoop(f"Strap{k}{z}", (x, yy, z), r, "X", M["iron"], thick=0.025)
            tube(f"Stay{k}{z}", [(x, yy + r, z), (x, 0.3, z)], 0.03, M["iron"], square=True, poly=True)
        box(f"WallPlate{k}", (0.25, 0.05, 1.2), (x, 0.32, (zt + zl) / 2), M["iron"], bevel=0.01)
    # a brass gate valve on the main
    box("ValveBody", (0.4, 0.5, 0.5), (-1.3, y, zt), M["brass"], bevel=0.06, segments=3)
    tube("ValveBonnet", [(-1.3, y, zt + 0.25), (-1.3, y, zt + 0.55)], 0.08, M["brass"], poly=True)
    tube("ValveStem", [(-1.3, y, zt + 0.55), (-1.3, y, zt + 0.78)], 0.025, M["iron"], poly=True)
    hoop("ValveWheel", (-1.3, y, zt + 0.75), 0.22, "Z", enamel(), thick=0.03)
    for k in range(4):
        a = k / 4 * 2 * math.pi
        tube(f"ValveSpoke{k}", [(-1.3, y, zt + 0.75), (-1.3 + math.cos(a) * 0.21, y + math.sin(a) * 0.21, zt + 0.75)], 0.015, M["iron"], poly=True)
    # a gauge off the lower line
    tube("GaugeLeg", [(0.9, y - 0.08, zl), (0.9, y - 0.36, zl), (0.9, y - 0.4, zl + 0.2)], 0.04, M["brass"])
    cyl("Gauge", 0.2, 0.08, (0.9, y - 0.45, zl + 0.38), M["brass"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.012)
    cyl("GaugeDial", 0.165, 0.01, (0.9, y - 0.495, zl + 0.38), M["paper"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0)
    box("GaugeNeedle", (0.012, 0.008, 0.13), (0.93, y - 0.505, zl + 0.41), M["iron"], bevel=0.0, segments=1, rot=(0, 0.5, 0))
    # the steam vent: up from the main, flared at the tip
    tube("VentPipe", [(2.9, y, zt + 0.15), (2.9, y, zt + 0.85)], 0.08, M["iron"], poly=True)
    lathe("VentNozzle", [(0.07, zt + 0.8), (0.11, zt + 0.86), (0.17, zt + 1.02), (0.19, zt + 1.08), (0.16, zt + 1.08), (0.09, zt + 0.92)],
          M["brass"], seg=18, loc=(2.9, y, 0))
    lathe("VentCollar", [(0, zt + 0.1), (0.13, zt + 0.1), (0.14, zt + 0.25), (0, zt + 0.25)], M["iron"], seg=16, loc=(2.9, y, 0))
    return _dims()


# ================================================================== valve wheel
def valve_wheel(M):
    zc, yw = 1.2, -0.62
    set_group("Main")
    tube("Riser", [(0, 0.05, 0.0), (0, 0.05, 2.4)], 0.14, M["iron"], poly=True)
    for z in (0.35, 2.05):
        hoop(f"Clamp{z}", (0, 0.05, z), 0.155, "Z", M["iron"], thick=0.025)
        box(f"ClampPlate{z}", (0.4, 0.05, 0.2), (0, 0.24, z), M["iron"], bevel=0.01)
    lathe("Body", [(0, zc - 0.34), (0.17, zc - 0.34), (0.3, zc - 0.18), (0.32, zc), (0.3, zc + 0.18), (0.17, zc + 0.34), (0, zc + 0.34)],
          M["brass"], seg=28, loc=(0, 0.02, 0))
    for z in (zc - 0.36, zc + 0.36):
        cyl(f"BodyFlange{z:.2f}", 0.22, 0.06, (0, 0.05, z), M["brass"], verts=20, bevel=0.01)
    s = _mark()
    lathe("Bonnet", [(0, 0), (0.16, 0), (0.15, 0.12), (0.1, 0.2), (0.1, 0.34), (0.06, 0.38), (0, 0.38)], M["brass"], seg=20)
    _xform(s, Matrix.Translation((0, -0.2, zc)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    tube("Stem", [(0, -0.55, zc), (0, yw - 0.06, zc)], 0.03, M["brasssteel"], poly=True)
    # the hand wheel turns on its axle (Y)
    set_group("Wheel", hinge=(0, yw, zc), swing=1)
    hoop("Rim", (0, yw, zc), 0.62, "Y", enamel(), thick=0.06)
    hoop("RimBead", (0, yw - 0.02, zc), 0.53, "Y", M["iron"], thick=0.02)
    for k in range(5):
        a = k / 5 * 2 * math.pi + math.pi / 2
        tube(f"Spoke{k}", [(math.cos(a) * 0.08, yw, zc + math.sin(a) * 0.08), (math.cos(a) * 0.6, yw, zc + math.sin(a) * 0.6)], 0.035, M["iron"])
    cyl("Hub", 0.11, 0.12, (0, yw, zc), M["iron"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.015)
    cyl("Nut", 0.06, 0.06, (0, yw - 0.08, zc), M["brass"], rot=(math.pi / 2, 0, 0), verts=6, bevel=0.005)
    sphere("Knob", 0.07, (0.62 * math.cos(0.5), yw - 0.06, zc + 0.62 * math.sin(0.5)), M["brass"], seg=10, rings=5)
    set_group("Main")
    return _dims()


# ================================================================== coal pile
def coal_pile(M):
    coal = coal_mat()
    rnd = random.Random(31)
    lathe("Heap", [(0, 0), (1.4, 0), (1.2, 0.22), (0.9, 0.55), (0.58, 0.88), (0.28, 1.1), (0, 1.16)], coal, seg=20, jitter=(0.16, 3), scale=(1.0, 0.8))
    for k in range(160):
        a = rnd.uniform(0, 2 * math.pi)
        t = math.sqrt(rnd.uniform(0, 1))
        rr = 1.38 * t
        z = max(0.06, 1.16 * (1 - t ** 1.3)) + rnd.uniform(0.0, 0.06)
        lump(f"Lump{k}", (math.cos(a) * rr, math.sin(a) * rr * 0.8, z), rnd.uniform(0.1, 0.2), coal, rnd)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(1.4, 1.8)
        lump(f"Stray{k}", (math.cos(a) * rr, math.sin(a) * rr * 0.85, 0.05), rnd.uniform(0.06, 0.1), coal, rnd)
    # a shovel driven into the heap
    s = _mark()
    prism("Blade", [(-0.22, 0.0), (0.22, 0.0), (0.25, 0.38), (0.12, 0.46), (-0.12, 0.46), (-0.25, 0.38)], 0.0, 0.025, M["iron"], plane="XZ", bevel=0.005)
    tube("Socket", [(0, 0, 0.44), (0, 0, 0.62)], 0.04, M["iron"], poly=True)
    tube("Shaft", [(0, 0, 0.6), (0, 0, 1.75)], 0.03, M["iron"], poly=True)
    tube("Grip", [(0, 0, 1.5), (0, 0, 1.8)], 0.042, M["leatherdark"], poly=True)
    tube("DHandle", [(0, 0, 1.78), (-0.12, 0, 1.88), (-0.12, 0, 2.0), (0.12, 0, 2.0), (0.12, 0, 1.88), (0, 0, 1.78)], 0.022, M["iron"])
    _xform(s, Matrix.Translation((0.45, -0.3, 0.8)) @ Matrix.Rotation(0.5, 4, "Z") @ Matrix.Rotation(math.radians(-22), 4, "X") @
           Matrix.Rotation(math.radians(12), 4, "Y"))
    return _dims()


# ================================================================== coal cart
def coal_cart(M):
    coal = coal_mat()
    rnd = random.Random(12)
    zb, zt = 0.72, 1.85
    tub("Tub", 1.5, 2.3, 1.95, 2.85, zb, zt, M["iron"], thick=0.06)
    tube("RimTop", rrect(0.99, 1.44, 0.08, zt), 0.05, M["iron"], closed=True, square=True, poly=True)
    tube("RimLow", rrect(0.76, 1.16, 0.06, zb + 0.08), 0.035, M["iron"], closed=True, square=True, poly=True)
    for sy in (-1, 1):
        for k in range(5):
            t = k / 4
            x0, x1 = -0.75 + 1.5 * t, -0.975 + 1.95 * t
            box(f"Strap{sy}{k}", (0.07, 0.03, 1.15), ((x0 + x1) / 2, sy * ((1.15 + 1.425) / 2 + 0.02), (zb + zt) / 2), M["iron"], bevel=0.008,
                rot=(-sy * math.atan2(0.275, 1.13), 0, 0))
    for k in range(10):
        t = k / 9
        sphere(f"RimRivet{k}", 0.03, (-0.95 + 1.9 * t, -1.43, zt - 0.08), M["brass"], seg=6, rings=3)
    # coal heaped above the rim
    lathe("Fill", [(0, zt - 0.1), (0.9, zt - 0.1), (0.8, zt + 0.1), (0.55, zt + 0.3), (0.25, zt + 0.42), (0, zt + 0.45)], coal, seg=24,
          jitter=(0.12, 9), scale=(1.0, 1.45))
    for k in range(80):
        a = rnd.uniform(0, 2 * math.pi)
        t = math.sqrt(rnd.uniform(0, 1))
        lump(f"Lump{k}", (math.cos(a) * 0.85 * t, math.sin(a) * 1.3 * t, zt + 0.42 * (1 - t ** 1.5) + 0.04), rnd.uniform(0.1, 0.17), coal, rnd)
    # undercarriage, axles and four spoked wheels
    for sx in (-1, 1):
        box(f"Beam{sx}", (0.12, 2.5, 0.14), (sx * 0.55, 0, zb - 0.08), M["iron"], bevel=0.015)
    for y in (-0.85, 0.85):
        tube(f"Axle{y}", [(-1.08, y, 0.38), (1.08, y, 0.38)], 0.04, M["iron"], poly=True)
        for sx in (-1, 1):
            box(f"Bearing{y}{sx}", (0.14, 0.2, 0.32), (sx * 0.55, y, 0.52), M["iron"], bevel=0.02)
            spoked_wheel(f"Wheel{y}{sx}", (sx * 0.98, y, 0.38), 0.36, "X", M["iron"], M["brass"], spokes=6, thick=0.05)
    # the push handle at the back, a coupling hook at the front
    for sx in (-1, 1):
        tube(f"HandleArm{sx}", [(sx * 0.6, 1.42, zt - 0.25), (sx * 0.6, 1.75, zt + 0.05), (sx * 0.55, 1.95, zt + 0.25)], 0.035, M["iron"])
    tube("HandleBar", [(-0.55, 1.95, zt + 0.25), (0.55, 1.95, zt + 0.25)], 0.045, M["iron"], poly=True)
    tube("Grip", [(-0.35, 1.95, zt + 0.25), (0.35, 1.95, zt + 0.25)], 0.055, M["leatherdark"], poly=True)
    tube("Hook", [(0, -1.25, zb - 0.05), (0, -1.6, zb - 0.05), (0, -1.68, zb + 0.05), (0, -1.6, zb + 0.13)], 0.035, M["iron"])
    return _dims()


# ================================================================== workbench
def workbench(M):
    W, D, H = 5.0, 2.2, 2.6
    rag = flat("OilyRag", (0.16, 0.06, 0.04), 0.75, dirt=0.9)
    rnd = random.Random(5)
    box("Top", (W, D, 0.16), (0, 0, H), M["iron"], bevel=0.03)
    box("Apron", (W - 0.3, D - 0.3, 0.26), (0, 0, H - 0.2), M["iron"], bevel=0.02)
    tube("Edge", rrect(W / 2, D / 2, 0.05, H + 0.07), 0.025, M["brasssteel"], closed=True, square=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), 0.04), (sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), H - 0.1)], 0.07,
                 M["iron"], square=True, poly=True)
            box(f"Foot{sx}{sy}", (0.25, 0.25, 0.05), (sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), 0.025), M["iron"], bevel=0.01)
        tube(f"SideBrace{sx}", [(sx * (W / 2 - 0.15), -(D / 2 - 0.15), 0.6), (sx * (W / 2 - 0.15), D / 2 - 0.15, 1.6)], 0.035, M["iron"],
             square=True, poly=True)
    box("Shelf", (W - 0.4, D - 0.4, 0.06), (0, 0, 0.6), M["iron"], bevel=0.01)
    # pegboard tool rack at the back with hanging tools
    box("Rack", (W - 0.2, 0.08, 2.0), (0, D / 2 - 0.05, H + 1.1), M["iron"], bevel=0.02)
    tube("RackRail", [(-W / 2 + 0.1, D / 2 - 0.12, H + 2.05), (W / 2 - 0.1, D / 2 - 0.12, H + 2.05)], 0.03, M["brass"], poly=True)
    for sx in (-1, 1):
        tube(f"RackPost{sx}", [(sx * (W / 2 - 0.12), D / 2 - 0.05, H), (sx * (W / 2 - 0.12), D / 2 - 0.05, H + 2.15)], 0.05, M["iron"],
             square=True, poly=True)
    for k in range(5):
        x = -1.8 + k * 0.45
        sphere(f"Peg{k}", 0.025, (x, D / 2 - 0.12, H + 1.75), M["brass"], seg=6, rings=3)
        spanner(f"Hung{k}", Matrix.Translation((x, D / 2 - 0.13, H + 1.75 - (0.3 + k * 0.04))) @ Matrix.Rotation(math.pi / 2, 4, "Y") @
                Matrix.Rotation(math.pi / 2, 4, "X"), M["brasssteel"], L=0.5 + k * 0.05)
    # a hanging saw and coils of hose
    prism("SawBlade", [(0.6, 1.55), (1.7, 1.4), (1.7, 1.2), (0.6, 1.4)], D / 2 - 0.12, 0.012, M["brasssteel"])
    _xform(len(P.PARTS) - 1, Matrix.Translation((0, 0, H)))
    box("SawGrip", (0.28, 0.06, 0.22), (0.5, D / 2 - 0.12, H + 1.47), M["leatherdark"], bevel=0.03)
    for k in range(3):
        hoop(f"Hose{k}", (1.3 + k * 0.03, D / 2 - 0.16, H + 0.75), 0.32 - k * 0.04, "Y", M["leatherdark"], thick=0.03)
    # the vice on the front right corner
    vx, vy = 1.9, -D / 2 + 0.15
    box("ViceBase", (0.5, 0.45, 0.1), (vx, vy + 0.1, H + 0.13), M["iron"], bevel=0.02)
    box("ViceFixed", (0.5, 0.22, 0.34), (vx, vy + 0.2, H + 0.35), M["iron"], bevel=0.03)
    box("ViceJaw", (0.5, 0.2, 0.3), (vx, vy - 0.12, H + 0.33), M["iron"], bevel=0.03)
    for y in (vy - 0.02, vy + 0.08):
        box(f"JawPlate{y}", (0.48, 0.02, 0.12), (vx, y, H + 0.46), M["brasssteel"], bevel=0.004)
    tube("ViceScrew", [(vx, vy - 0.2, H + 0.3), (vx, vy - 0.42, H + 0.3)], 0.03, M["brass"], poly=True)
    tube("ViceBar", [(vx - 0.28, vy - 0.42, H + 0.3), (vx + 0.28, vy - 0.42, H + 0.3)], 0.022, M["brass"], poly=True)
    for sx in (-1, 1):
        sphere(f"ViceKnob{sx}", 0.04, (vx + sx * 0.3, vy - 0.42, H + 0.3), M["brass"], seg=8, rings=4)
    # tools on the top: spanners, a hammer, an oil can, oily rags
    for k, (x, y, yaw) in enumerate(((-1.6, -0.5, 0.3), (-1.2, -0.65, -0.2), (-0.7, -0.4, 1.2))):
        spanner(f"Spanner{k}", Matrix.Translation((x, y, H + 0.08)) @ Matrix.Rotation(yaw, 4, "Z"), M["brasssteel"], L=0.55 + k * 0.08)
    s = _mark()
    box("HammerHead", (0.12, 0.32, 0.12), (0, 0.18, 0.06), M["iron"], bevel=0.015)
    tube("HammerShaft", [(0, 0.12, 0.06), (0, -0.55, 0.06)], 0.03, M["iron"], poly=True)
    tube("HammerGrip", [(0, -0.3, 0.06), (0, -0.58, 0.06)], 0.038, M["leatherdark"], poly=True)
    _xform(s, Matrix.Translation((0.2, -0.3, H + 0.08)) @ Matrix.Rotation(-0.9, 4, "Z"))
    lathe("OilCan", [(0, 0), (0.16, 0), (0.17, 0.04), (0.17, 0.14), (0.1, 0.24), (0.04, 0.27), (0.04, 0.32), (0, 0.32)], M["brass"], seg=20,
          loc=(-1.9, 0.45, H + 0.08))
    tube("OilSpout", [(-1.87, 0.43, H + 0.38), (-1.75, 0.35, H + 0.55), (-1.55, 0.3, H + 0.62)], 0.015, M["brass"])
    for k in range(4):
        lump(f"Rag{k}", (0.8 + rnd.uniform(-0.25, 0.25), 0.35 + rnd.uniform(-0.2, 0.2), H + 0.14), rnd.uniform(0.13, 0.2), rag, rnd, squash=0.45)
    # a small iron bin of bolts on the shelf
    box("Bin", (0.9, 0.6, 0.35), (-1.3, 0.1, 0.81), M["iron"], bevel=0.02)
    for k in range(12):
        sphere(f"Bolt{k}", 0.04, (-1.3 + rnd.uniform(-0.35, 0.35), 0.1 + rnd.uniform(-0.22, 0.22), 1.0), M["brasssteel"], seg=6, rings=3)
    return _dims()


P.PREVIEW_PAD.update({"Boiler": 1.15, "TackleDummy": 1.15, "Hurdle": 1.05, "WaterKeg": 1.1, "ValveWheel": 1.1})
# the firebox door swings out; the valve wheel turns about Y, so its _open preview shows it at rest
P.OPEN_DEG.update({"Boiler_Door0": 100, "ValveWheel_Wheel": 0})

P.BUILD.update({
    "BallRack": ball_rack,
    "Hurdle": hurdle,
    "TackleDummy": tackle_dummy,
    "GymMatStack": gym_mat_stack,
    "WaterKeg": water_keg,
    "Scoreboard": scoreboard,
    "Boiler": boiler,
    "PipeRun": pipe_run,
    "ValveWheel": valve_wheel,
    "CoalPile": coal_pile,
    "CoalCart": coal_cart,
    "Workbench": workbench,
})
