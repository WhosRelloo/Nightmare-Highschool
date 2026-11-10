"""Props batch 44 (2026-11-09): the showpiece kit, statues, set-pieces and grand paintings of the school's legends, for
nh_props.py. Every figure is the owner's R6 rig (PaintRigV3.blend, appended read-only, posed on its armature;
showpiece44_rig.py) dressed in modelled clothing and gear (showpiece44_chars.py: tailored jackets with lapels, simulated
capes and coat skirts, boots, armour, hair, crowns, weapons), finished in procedural PBR materials, one per real
material (showpiece44_mats.py), with effects built in as _Glow (Neon) and _Glass pieces (showpiece44_geo.py).

Pieces: Main (the base and its scene), Figure (Figure2, Figure3 for groups), Glow / Glow2 (Neon, one colour each, see
GLOW), Glass (translucent mist, ghosts, panes), and Canvas for the paintings (P.CANVAS, painted by
showpiece44_canvas.py over Cycles renders from showpiece44_scenes.py).

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back flat on y = 0.
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform, _dims
from nh_props_batch12 import frustum
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch21 as B21
import window_shapes as WS
import showpiece44_mats as MT
import showpiece44_geo as GE
import showpiece44_chars as C
import showpiece44_rig as R
import showpiece44_organic as O
import showpiece44_poses as PO

S = 1.6
FONT = "C:/Windows/Fonts/palab.ttf"

# Neon / glass colours per prop and piece (0-255): read by the preview, the scene renders and the template notes
GLOW = {}
# atlas share by piece suffix (run44.bake_uv): the figures get the most texels
UV_WEIGHT = {"Main": 0.55, "Glow": 0.35, "Glow2": 0.35, "Glass": 0.4}


def kit(glow=(255, 60, 60), glow2=None, glass=(200, 220, 255)):
    MT.clear()
    K = MT.kit()
    K["glowmat"] = MT.glow_mat(tuple(c / 255 for c in glow))
    K["glow2mat"] = MT.glow_mat(tuple(c / 255 for c in (glow2 or glow)))
    K["glassmat"] = MT.glass_mat(tuple(c / 255 for c in glass))
    return K


def figure(key, base, **kw):
    """A posed R6 for one of the batch's figures: yaw and pose from showpiece44_poses (so every pose is its own)."""
    yaw, pose = PO.POSES[key]
    return R.Fig(base=base, scale=S, yaw=math.radians(yaw), pose=pose, **kw)


def tp(name, pts, y, depth, mat):
    return B20.tprism(name, WS.ccw(pts), y, depth, mat)


def tpz(name, pts, z, depth, mat):
    """A flat outline in XY extruded up from z by depth (triangulated)."""
    return B20.tprism(name, WS.ccw(pts), z, depth, mat, plane="XY")


def text(name, s, mat, x, y, z, fit, depth=0.02):
    B24._text(name, s, FONT, mat, lambda u, v, d: (x + u, y - d, z + v), fit=fit, depth=depth, res=1)


def glow(fn):
    return GE.in_group("Glow", fn)


def glow2(fn):
    return GE.in_group("Glow2", fn)


def glass(fn):
    return GE.in_group("Glass", fn)


# ------------------------------------------------------------------ bases

def oct_plinth(prefix, K, r=3.0, h=2.4, st="limestonedk", trim="gilt", band="blackmarble", plaque=None, title=None):
    """An octagonal plinth: a stepped foot, a die with a marble band and a gilt rope, a moulded cornice, a brass
    plaque in front with the legend's name."""
    lathe(f"{prefix}Plinth", [(0, 0), (r + 0.35, 0), (r + 0.35, 0.3), (r + 0.15, 0.42), (r, 0.5), (r, h - 0.45), (r + 0.18, h - 0.3),
                              (r + 0.3, h - 0.15), (r + 0.3, h), (0, h)], K[st], seg=8)
    lathe(f"{prefix}Band", [(r + 0.02, h * 0.42), (r + 0.06, h * 0.45), (r + 0.06, h * 0.62), (r + 0.02, h * 0.65)], K[band], seg=8)
    hoop(f"{prefix}Rope", (0, 0, h * 0.42), (r + 0.06) * 0.95, "Z", K[trim], thick=0.04)
    if plaque:
        ap = r * math.cos(math.pi / 8)
        box(f"{prefix}Plaque", (r * 0.62, 0.06, 0.55), (0, -ap - 0.08, h * 0.535), K[plaque], bevel=0.02)
        if title:
            text(f"{prefix}Title", title, K["enamel_black"], 0, -ap - 0.11, h * 0.535, (r * 0.52, 0.3), depth=0.015)
    return h


def rect_plinth(prefix, K, w, d, h, st="limestonedk", top="limestone", trim="gilt", plaque=None, title=None):
    box(f"{prefix}Foot", (w + 0.6, d + 0.6, 0.35), (0, 0, 0.175), K[st], bevel=0.06)
    box(f"{prefix}Die", (w, d, h - 0.7), (0, 0, 0.35 + (h - 0.7) / 2), K[st], bevel=0.05)
    box(f"{prefix}Cap", (w + 0.4, d + 0.4, 0.35), (0, 0, h - 0.175), K[top], bevel=0.07)
    box(f"{prefix}Rope", (w + 0.08, d + 0.08, 0.06), (0, 0, h - 0.42), K[trim], bevel=0.02)
    if plaque:
        box(f"{prefix}Plaque", (w * 0.5, 0.06, 0.5), (0, -d / 2 - 0.03, h * 0.5), K[plaque], bevel=0.02)
        if title:
            text(f"{prefix}Title", title, K["enamel_black"], 0, -d / 2 - 0.06, h * 0.5, (w * 0.42, 0.28), depth=0.015)
    return h


def bat(prefix, K, at, heading=0.0, s=1.0, flap=0.6, mat="leather_black"):
    """A small bat in flight: a furred body, ears and scalloped membrane wings."""
    st = _mark()
    m = K[mat]
    sphere(f"{prefix}Body", 0.14 * s, (0, 0, 0), K["fur_black"], seg=8, rings=5, scale=(1.4, 0.9, 0.9))
    sphere(f"{prefix}Head", 0.09 * s, (0.17 * s, 0, 0.03 * s), K["fur_black"], seg=8, rings=5)
    for sy in (-1, 1):
        cone(f"{prefix}Ear{sy}", 0.03 * s, 0, 0.09 * s, (0.18 * s, sy * 0.05 * s, 0.12 * s), m, verts=4)
        outline = [(0, 0), (0.15, 0.55), (0.05, 0.62), (-0.05, 0.5), (-0.15, 0.58), (-0.22, 0.42), (-0.3, 0.45), (-0.25, 0.1)]
        pts = [(x * s, y * s) for x, y in outline]
        B20.tprism(f"{prefix}Wing{sy}", WS.ccw(pts), 0, 0.02 * s, m, plane="XY")
        ob = P.PARTS[-1]
        ob.matrix_world = Matrix.Rotation(sy * flap, 4, "X") @ Matrix.Diagonal((1, sy, 1, 1))
    _xform(st, Matrix.Translation(at) @ Matrix.Rotation(heading, 4, "Z"))


# ================================================================== the statues

def vampire_lord_rising(M):
    """The Royal Vamp, Lord Malachar Crane, founder of the Crimson Court, rising out of his opened coffin on a column of
    blood-red mist: a black-marble face and hands, a black wool tailcoat, crimson silk waistcoat and linen jabot, a black
    velvet cape lined in crimson silk flaring up in the updraft, a ruby at his throat, glowing eyes, bats, droplets."""
    K = kit(glow=(255, 30, 40), glass=(200, 20, 35))
    GLOW["VampireLordRising"] = {"Glow": (255, 30, 40), "Glass": (200, 20, 35)}
    H = oct_plinth("P", K, r=3.2, h=2.2, plaque="brass", title="MALACHAR CRANE")
    # the coffin, lying across the plinth (head to +X), its lid slid off and leaning on the plinth
    out = [(-2.9, 0.0), (-2.35, -0.95), (1.2, -1.35), (2.85, -0.85), (2.85, 0.85), (1.2, 1.35), (-2.35, 0.95)]
    tpz("CoffinFloor", out, H, 0.18, K["coffin"])
    for nm, k, z0, z1, mat in (("CoffinWall", 1.0, H + 0.1, H + 1.05, "coffin"), ("CoffinLining", 0.9, H + 0.17, H + 0.98, "velvet_crimson")):
        rows = [[Vector((x * k, y * k, z)) for x, y in out] for z in (z0, z1)]
        GE.grid_mesh(nm, rows, K[mat], 0.12 if k == 1.0 else 0.05, closed=True)
    rows = [[Vector((x * 1.03, y * 1.03, z)) for x, y in out] for z in (H + 1.0, H + 1.1)]
    GE.grid_mesh("CoffinRim", rows, K["gilt"], 0.06, closed=True)
    for i, (x, y) in enumerate(out):
        tube(f"CoffinPost{i}", [(x * 1.02, y * 1.02, H + 0.15), (x * 1.02, y * 1.02, H + 1.0)], 0.06, K["gilt"], poly=True)
    for sx in (-0.9, 0.9):
        for sy in (-1, 1):
            tube(f"Handle{sx}{sy}", [(sx - 0.35, sy * 1.28, H + 0.6), (sx - 0.3, sy * 1.48, H + 0.45), (sx + 0.3, sy * 1.48, H + 0.45), (sx + 0.35, sy * 1.28, H + 0.6)],
                 0.04, K["iron"])
    sphere("Pillow", 0.5, (2.2, 0.0, H + 0.4), K["silk_crimson"], seg=14, rings=8, scale=(0.9, 1.4, 0.45))
    # the lid, cracked and slid down against the plinth's right front
    s = _mark()
    tpz("Lid", out, 0, 0.2, K["coffin"])
    tpz("LidPanel", [(x * 0.8, y * 0.8) for x, y in out], 0.2, 0.06, K["coffin"])
    tube("LidCrossV", [(-1.9, 0, 0.3), (2.3, 0, 0.3)], 0.07, K["gilt"], poly=True, square=True)
    tube("LidCrossH", [(1.2, -0.85, 0.3), (1.2, 0.85, 0.3)], 0.07, K["gilt"], poly=True, square=True)
    sphere("LidRuby", 0.16, (1.2, 0, 0.36), K["ruby"], seg=8, rings=4, scale=(1, 1, 0.6))
    _xform(s, Matrix.Translation((2.6, -3.6, 0.0)) @ Matrix.Rotation(math.radians(-25), 4, "Z") @ Matrix.Rotation(math.radians(62), 4, "X")
           @ Matrix.Translation((0, 0, 0)))
    GE.chain_links("Chain", (-2.4, -1.0, H + 1.05), (-3.3, -1.9, 0.4), K["iron"], link=0.2, thick=0.035, sag=0.25)
    GE.chain_links("Chain2", (0.4, -1.3, H + 1.05), (0.9, -3.4, 0.3), K["iron"], link=0.2, thick=0.035, sag=0.2)
    # the lord, rising
    set_group("Figure")
    f = figure("VampireLordRising", (-0.35, 0.1, H + 0.15), parts=("head", "rarm", "larm"),
              mats=K["marble"], face="snarl", dark=K["dark"], glow_eyes="Glow")
    C.hair(f, K, "blackmarble", "slick", seed=3)
    C.claws(f, K, "blackmarble")
    C.jacket(f, K, "wool_black", hem=1.55, lapel="silk_black", shirt="linen", vest="silk_crimson", buttons="gold", cuff="velvet_black", seed=4)
    f.build("torso", lambda: [GE.ribbon(f"Jabot{k}", [(0, -0.64 - k * 0.02, 3.98 - k * 0.12), (0.03, -0.68 - k * 0.03, 3.8 - k * 0.12)],
                                         0.34 - k * 0.04, K["linen"], up=(1, 0, 0), thick=0.02, twist=0.4) for k in range(4)] +
            [sphere("Ruby", 0.13, (0, -0.72, 3.95), K["ruby"], seg=8, rings=4, scale=(1, 0.6, 1.2)),
             hoop("RubySet", (0, -0.7, 3.95), 0.15, "Y", K["gold"], thick=0.03)])
    C.trousers(f, K, "wool_black", seed=5)
    C.boots(f, K, "leather_black", h=0.85, sole="leather_black", buckles="silver")
    C.cape(f, K, "velvet_black", lining="silk_crimson", length=5.4, wind=(0.25, 0.55, 0.75), gather=1.35, collar="silk_crimson", gem="ruby",
           seed=2, curl=0.5, turb=0.5)
    # the mist he rises on, and the droplets and bats round him
    set_group("Glass")
    O.plume("Mist", K["glassmat"], (-0.3, 0.0, H + 0.7), 1.9, 4.2, seed=4, tendrils=7, billows=12)
    O.mist("Spill", K["glassmat"], (2.3, -1.4, H + 0.7), 7, 0.9, 0.42, seed=9, rise=0.3)
    O.mist("Pour", K["glassmat"], (-2.7, -1.3, H - 1.2), 7, 0.6, 0.4, seed=12, rise=1.2)
    set_group("Glow")
    GE.embers("Drop", (-0.3, 0.0, H + 3.5), 26, 3.0, K["glowmat"], seed=5, size=0.06, rise=1.6)
    GE.wisp("Wisp1", (-0.3, 0.8, 0), 2.6, H + 1.2, H + 7.6, K["glowmat"], turns=0.42, r0=0.07, phase=0.3)
    GE.wisp("Wisp2", (-0.3, 0.8, 0), 2.9, H + 1.0, H + 6.4, K["glowmat"], turns=-0.4, r0=0.05, phase=2.9)
    set_group("Main")
    for k, (p, hd) in enumerate((((-3.2, -0.6, H + 7.6), 0.6), ((2.4, 0.4, H + 8.6), 2.4), ((3.4, -1.0, H + 6.0), -2.6))):
        O.bat(f"Bat{k}", K, p, hd, s=2.0, flap=0.3 + 0.3 * k)
    return _dims()



def werewolf_turning(M):
    """The Pack's first Bloodmoon, caught mid-turn under the blood moon: a bronze student in a torn navy school blazer
    doubled over and twisting, one hand clawing at his own lengthening face, the other flung back with claws out; the
    muzzle and ears are breaking through, fur bursts from the split back seam and the torn cuffs and trouser legs, the
    tie and shreds of cloth fly; he stands on smashed flagstones with snapped shackle chains before an iron-ringed moon."""
    K = kit(glow=(255, 70, 40), glow2=(255, 190, 70))
    GLOW["WerewolfTurning"] = {"Glow": (255, 70, 40), "Glow2": (255, 190, 70)}
    H = rect_plinth("P", K, 5.6, 4.4, 1.6, st="limestonedk", top="slate", trim="iron", plaque="bronze", title="THE FIRST TURNING")
    rnd = random.Random(7)
    for i, (x, y, w, d, tx, ty) in enumerate(((-1.8, -1.2, 1.9, 1.5, 0.12, -0.2), (0.3, -1.4, 1.7, 1.3, -0.25, 0.1), (2.0, -1.0, 1.4, 1.6, 0.05, 0.3),
                                               (-2.0, 0.8, 1.6, 1.7, -0.1, -0.12), (0.2, 1.1, 2.0, 1.4, 0.3, 0.05), (2.1, 1.1, 1.3, 1.5, -0.15, 0.25))):
        GE.slab(f"Flag{i}", (x, y, H + 0.12 + abs(tx) * 0.5), w, d, 0.24, K["slate"], seed=i, tilt=(tx, ty), yaw=rnd.uniform(-0.3, 0.3))
    GE.rubble("Rub", (0, -1.6, H + 0.05), 9, 2.4, 0.32, K["rock"], seed=3)
    for k, (a, b) in enumerate((((-2.6, 1.7, H + 0.2), (-1.6, 0.3, H + 1.4)), ((2.6, 1.7, H + 0.2), (1.9, 0.2, H + 1.0)))):
        cyl(f"Ring{k}", 0.16, 0.2, a, K["iron"], verts=10)
        GE.chain_links(f"Chain{k}", a, b, K["iron"], link=0.22, thick=0.04, sag=0.15)
    mz = H + 9.2
    set_group("Glow")
    cyl("Moon", 2.3, 0.18, (0, 2.3, mz), K["glowmat"], rot=(math.pi / 2, 0, 0), verts=40, bevel=0.04)
    set_group("Main")
    hoop("MoonRing", (0, 2.2, mz), 2.45, "Y", K["iron"], thick=0.09)
    for k in range(12):
        a = 2 * math.pi * k / 12
        cone(f"MoonRay{k}", 0.1, 0.0, 0.6 + 0.3 * (k % 2), (math.cos(a) * 2.85, 2.2, mz + math.sin(a) * 2.85), K["iron"], verts=4,
             rot=(0, -a + math.pi / 2, 0))
    tube("MoonPost", [(0, 2.0, H), (0, 2.2, mz - 2.45)], 0.12, K["iron"], poly=True)
    for sx in (-1, 1):
        tube(f"MoonStay{sx}", [(sx * 1.6, 1.9, H), (sx * 0.4, 2.15, H + 2.6), (sx * 1.0, 2.2, mz - 2.3)], 0.06, K["iron"])
    set_group("Figure")
    f = figure("WerewolfTurning", (0, -0.2, H + 0.3), mats=K["bronze"], parts=("head", "rarm", "larm", "rleg", "lleg"), face="snarl", dark=K["dark"], glow_eyes="Glow2")
    f.settle(H + 0.3)
    C.jacket(f, K, "wool_navy", hem=1.85, lapel="wool_navy", shirt="linen", tie=None, buttons="brass", pocket=True, seed=11, sleeves=False)
    f.build("torso", lambda: GE.ribbon("TieFly", [(0.0, -0.64, 3.95), (0.15, -0.8, 3.7), (0.5, -1.0, 3.75), (0.9, -1.1, 3.95)],
                                        lambda t: 0.15 + 0.08 * t, K["silk_crimson"], up=(0, 0, 1), thick=0.025, twist=1.2))
    for side in (-1, 1):
        part = "rarm" if side > 0 else "larm"
        f.build(part, lambda side=side: GE.shell(f"Sleeve{side}", 2.45 if side > 0 else 2.2, 4.06, 0.56, 0.56, K["wool_navy"], cx=side * 1.5, r=0.14,
                                                 n=20, nz=9, seed=20 + side, thick=0.035, tatter=4, wrinkles=[(3.05, 0.3, 0.06, 3)]))
    C.trousers(f, K, "wool_grey", seed=13)
    fur = K["fur_brown"]
    f.build("torso", lambda: O.blob("BackFur", O.chain([(0, 0.55, 2.4), (0, 0.72, 3.1), (0, 0.75, 3.7), (0, 0.6, 4.15)], 0.25, 0.36), fur,
                                     res=0.07, decimate=0.3, displace=(0.07, 0.12)))
    for side in (-1, 1):
        part = "rarm" if side > 0 else "larm"
        z = 2.45 if side > 0 else 2.2
        f.build(part, lambda side=side, z=z: O.blob(f"ArmFur{side}", O.chain([(side * 1.5, 0, z + 0.25), (side * 1.5, 0, z - 0.2)], 0.48, 0.42), fur,
                                                    res=0.07, decimate=0.3, displace=(0.08, 0.1)))
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"
        f.build(part, lambda side=side: O.blob(f"LegFur{side}", O.chain([(side * 0.5, 0, 0.45), (side * 0.5, 0, 0.0)], 0.45, 0.5), fur, res=0.07,
                                               decimate=0.3, displace=(0.08, 0.1)))
    C.claws(f, K, "bone", L=0.5)
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"
        f.build(part, lambda side=side: [GE.sweep(f"Toe{side}{k}", [(side * 0.5 - 0.3 + k * 0.3, -0.45, 0.05), (side * 0.5 - 0.33 + k * 0.33, -0.75, 0.03),
                                                                    (side * 0.5 - 0.34 + k * 0.34, -0.85, -0.08)], lambda t: 0.06 * (1 - t) + 0.004,
                                                   K["bone"], sides=6) for k in range(3)])

    def wolfhead():
        E = [(p, r, (1.25, 1.0, 0.75), None, 2.0) for p, r, *_ in O.chain([(0, -0.45, 4.62), (0, -0.95, 4.52), (0, -1.45, 4.42), (0, -1.7, 4.38)], 0.36, 0.17)]
        E += O.chain([(0, -0.5, 4.22), (0, -0.95, 4.02), (0, -1.35, 3.88)], 0.2, 0.1)
        for sx in (-1, 1):
            E += O.chain([(sx * 0.62, -0.3, 4.45), (sx * 0.85, 0.1, 4.35), (sx * 1.0, 0.4, 4.2)], 0.2, 0.05)
        O.blob("Muzzle", E, K["bronze"], res=0.045, decimate=0.45, displace=(0.02, 0.06))
        sphere("Nose", 0.12, (0, -1.8, 4.44), K["dark"], seg=10, rings=6, scale=(1.3, 1, 0.75))
        for k in range(5):
            for jaw, z in ((0, 4.25), (1, 4.02)):
                GE.sweep(f"Tooth{jaw}{k}", [(-0.18 + k * 0.09, -0.75 - k * 0.12, z), (-0.18 + k * 0.09, -0.75 - k * 0.12, z + (-0.12 if jaw == 0 else 0.1))],
                         lambda t: 0.03 * (1 - t) + 0.003, K["bone"], sides=4, smooth=0)
        for sx in (-1, 1):
            GE.sweep(f"Ear{sx}", [(sx * 0.42, 0.1, 5.0), (sx * 0.6, 0.25, 5.5), (sx * 0.72, 0.45, 6.0)], lambda t: 0.26 * (1 - t) ** 0.8 + 0.01, K["fur_brown"],
                     sides=8, flat=0.45)
            for k in range(2):
                GE.sweep(f"Fang{sx}{k}", [(sx * 0.12, -1.0 - k * 0.12, 4.3), (sx * 0.12, -1.0 - k * 0.12, 4.12)], lambda t: 0.035 * (1 - t) + 0.003,
                         K["bone"], sides=5, smooth=0)
        O.blob("Mane", O.chain([(-0.6, 0.2, 5.0), (0, 0.55, 5.05), (0.6, 0.2, 5.0)], 0.28, 0.28) +
               O.chain([(0, 0.6, 4.9), (0, 0.75, 4.3)], 0.3, 0.32), K["fur_brown"], res=0.05, decimate=0.5, displace=(0.06, 0.08))
    f.build("head", wolfhead)
    set_group("Main")
    rnd = random.Random(5)
    for k in range(7):
        p = Vector((rnd.uniform(-2.6, 2.6), rnd.uniform(-1.6, 1.2), H + rnd.uniform(4.5, 8.5)))
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1))).normalized()
        GE.ribbon(f"Shred{k}", [p, p + d * 0.35 + Vector((0, 0, 0.1)), p + d * 0.7], lambda t: 0.25 * (1 - 0.6 * t), K["wool_navy" if k % 3 else "linen"],
                  up=(rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.3), thick=0.02, twist=rnd.uniform(-2, 2))
    set_group("Glow")
    GE.embers("Spark", (0, 0, H + 3.0), 18, 3.2, K["glowmat"], seed=8, size=0.05, rise=1.6)
    set_group("Main")
    return _dims()


def vigil_captain(M):
    """Ezra Vale, captain of the Vigil, climbing the broken graveyard steps with a burning lantern held high: a long
    charcoal greatcoat with silver buttons and epaulettes whipping back, a crimson wool scarf streaming, a sabre at his
    hip, boots; ghost-blue flame in the lantern, embers and a wisp rising; a toppled gravestone and votive candles."""
    K = kit(glow=(150, 210, 255), glow2=(255, 170, 70), glass=(190, 225, 255))
    GLOW["VigilCaptainLantern"] = {"Glow": (150, 210, 255), "Glow2": (255, 170, 70), "Glass": (190, 225, 255)}
    box("Foot", (6.6, 5.6, 0.45), (0, 0, 0.225), K["limestonedk"], bevel=0.06)
    box("Landing", (6.0, 5.0, 0.5), (0, 0, 0.7), K["limestone"], bevel=0.08)
    GE.rubble("Rub", (-2.3, -2.0, 0.95), 6, 0.8, 0.3, K["rock"], seed=9)
    s = _mark()
    tp("Grave", [(-0.8, 0), (0.8, 0), (0.8, 1.8), (0.55, 2.3), (0, 2.5), (-0.55, 2.3), (-0.8, 1.8)], 0, 0.3, K["limestonedk"])
    text("GraveText", "REQUIESCAT", K["enamel_black"], 0, -0.16, 1.4, (1.2, 0.22), depth=0.02)
    _xform(s, Matrix.Translation((-2.0, 1.6, 0.95)) @ Matrix.Rotation(math.radians(28), 4, "Z") @ Matrix.Rotation(math.radians(-18), 4, "Y"))
    set_group("Figure")
    f = figure("VigilCaptainLantern", (0, 0.2, 2.05), mats=K["marble"], parts=("head", "rarm", "larm"), face="stern", dark=K["dark"])
    f.settle(0.95)
    set_group("Main")
    # the broken step his right boot is planted on, cut to the boot's height
    ft = f.at("rleg", (0.5, -0.1, 0.0))
    top = ft.z
    box("Step", (2.6, 1.8, top - 0.95), (ft.x + 0.4, ft.y - 0.4, 0.95 + (top - 0.95) / 2), K["limestonedk"], bevel=0.08)
    GE.slab("StepCap", (ft.x + 0.4, ft.y - 0.4, top - 0.06), 2.8, 2.0, 0.14, K["limestone"], seed=12, chip=0.12)
    GE.slab("Broken", (ft.x + 1.6, ft.y - 1.4, 1.05), 1.2, 0.9, 0.2, K["limestone"], seed=4, tilt=(0.2, -0.5), yaw=0.4)
    for k, (dx, dy, h) in enumerate(((1.1, 0.6, 0.6), (1.4, 0.2, 0.4), (-2.4, -1.4, 0.5), (-2.0, -1.9, 0.3))):
        x, y = ft.x + dx if k < 2 else dx, ft.y + dy if k < 2 else dy
        z = top if k < 2 else 0.95
        cyl(f"Candle{k}", 0.1, h, (x, y, z + h / 2), K["wax"], verts=10)
        GE.in_group("Glow2", lambda x=x, y=y, z=z, h=h, k=k: GE.flames(f"CFlame{k}", (x, y, z + h), 0.28, 0.06, K["glow2mat"], n=1, seed=k))
    set_group("Figure")
    C.hair(f, K, "hair_brown", "swept", seed=5, flow=(0.3, 1, 0.2))
    C.jacket(f, K, "wool_grey", hem=1.9, lapel="wool_black", shirt="linen", vest="wool_black", buttons="silver", collar=True, seed=21, cuff="wool_black",
             epaulettes="silver")
    C.trousers(f, K, "wool_black", seed=22)
    C.boots(f, K, "leather_black", h=1.1, sole="leather_brown", cuff="leather_black")
    C.belt(f, K, "leather_brown", "silver")
    C.coat_skirt(f, K, "wool_grey", length=3.0, z=2.15, gather=1.25, wind=(0.15, 0.9, 0.25), gap=0.35, lining="wool_black", seed=4, turb=0.5,
                 curl=0.4)
    GE.sweep("ScarfWrap", [f.at("torso", (x * 0.62, y * 0.62, 4.1)) for x, y in [(1, -1), (0, -1.1), (-1, -1), (-1.1, 0.4), (0, 1.05), (1.1, 0.4), (1, -1)]],
             0.17, K["wool_crimson"], sides=8, flat=0.7, smooth=1)
    root = f.at("torso", (0.6, 0.55, 4.0))
    tail = [root + Vector((0.3 * t, 1.6 * t + 0.6 * t * t, -0.6 * t + 0.5 * math.sin(t * 5))) for t in [i / 6 for i in range(7)]]
    GE.ribbon("ScarfTail", tail, 0.42, K["wool_crimson"], up=(1, 0, 0.3), thick=0.06, twist=0.9)
    for k in range(5):
        GE.sweep(f"Fringe{k}", [tail[-1] + Vector((-0.18 + k * 0.09, 0, 0)), tail[-1] + Vector((-0.18 + k * 0.1, 0.3, -0.12))], 0.02, K["wool_crimson"], sides=4,
                 smooth=0)
    # the sabre sheathed at his left hip, his hand on the hilt
    hp, _ = C.hand_at(f, -1)
    down = (f.at("torso", (-1.1, 0.9, 0.6)) - hp).normalized()
    s = _mark()
    GE.sabre("Sabre", K, curve=0.25, L=0.3)
    GE.sweep("Scabbard", [(0.02 * (i / 8) ** 2, 0, 0.4 + 2.8 * i / 8) for i in range(9)], lambda t: 0.13 - 0.04 * t, K["leather_black"], sides=8, flat=0.4)
    cone("Chape", 0.1, 0.02, 0.3, (0.02, 0, 3.25), K["silver"], verts=8)
    hoop("Locket", (0, 0, 0.6), 0.14, "Z", K["silver"], thick=0.03)
    _xform(s, Matrix.Translation(hp) @ Vector((0, 0, 1)).rotation_difference(down).to_matrix().to_4x4() @ Matrix.Scale(S * 0.85, 4))
    C.hold(f, 1, lambda: GE.lantern("Lantern", K, s=1.0, glow="Glow", glass="Glass", flame_n=5, seed=3), along=(0, 0, 1), push=-0.05)
    set_group("Glow")
    lp, _ = C.hand_at(f, 1)
    GE.embers("Ember", lp + Vector((0, 0, 0.5)), 16, 2.2, K["glowmat"], seed=4, size=0.05, rise=1.4)
    GE.wisp("Wisp", lp - Vector((0, 0, 1.0)), 0.9, lp.z - 1.2, lp.z + 2.6, K["glowmat"], turns=1.3, r0=0.06, phase=0.4)
    set_group("Main")
    return _dims()



def round_plinth(prefix, K, r=3.0, h=1.8, st="limestonedk", band="marble", trim="gilt", seg=24, plaque=None, title=None):
    lathe(f"{prefix}Plinth", [(0, 0), (r + 0.4, 0), (r + 0.4, 0.25), (r + 0.2, 0.38), (r, 0.45), (r - 0.1, 0.6), (r - 0.1, h - 0.45), (r + 0.05, h - 0.32),
                              (r + 0.25, h - 0.15), (r + 0.25, h), (0, h)], K[st], seg=seg)
    lathe(f"{prefix}Band", [(r - 0.08, h * 0.45), (r - 0.02, h * 0.48), (r - 0.02, h * 0.64), (r - 0.08, h * 0.67)], K[band], seg=seg)
    hoop(f"{prefix}Rope", (0, 0, h - 0.4), r + 0.02, "Z", K[trim], thick=0.035)
    if plaque:
        box(f"{prefix}Plaque", (r * 0.7, 0.06, 0.45), (0, -(r - 0.07), h * 0.56), K[plaque], bevel=0.02)
        if title:
            text(f"{prefix}Title", title, K["enamel_black"], 0, -(r - 0.04), h * 0.56, (r * 0.6, 0.26), depth=0.015)
    return h


def choir_conductor(M):
    """Lucien Grey, cantor of the Chapel Choir, conducting the dead: standing with one foot on the lip of the great
    cracked chapel bell that fell in the storm, baton flung high, the other hand spread to hold the note, head thrown
    back in song; a black wool cassock to the ankles, a white linen surplice with wide bell sleeves and a lace hem, a
    crimson silk stole with gilt crosses. Spectral staves and notes spiral round him; a moonlight halo behind his head."""
    K = kit(glow=(255, 236, 190), glow2=(170, 200, 255))
    GLOW["ChoirConductor"] = {"Glow": (255, 236, 190), "Glow2": (170, 200, 255)}
    H = round_plinth("P", K, r=3.1, h=1.7, plaque="brass", title="LUCIEN GREY, CANTOR")
    # the fallen bell lying on its side across the back of the plinth, crack and all
    s = _mark()
    prof = [(0.0, 0.0), (0.55, 0.0), (0.7, 0.15), (0.85, 0.75), (1.05, 1.5), (1.45, 2.1), (1.75, 2.35), (1.78, 2.5), (1.62, 2.5), (1.35, 2.2),
            (0.95, 1.55), (0.72, 0.8), (0.55, 0.2), (0.0, 0.2)]
    lathe("Bell", prof, K["bronzegreen"], seg=40)
    hoop("BellLip", (0, 0, 2.38), 1.72, "Z", K["bronze"], thick=0.06)
    hoop("BellBand", (0, 0, 1.2), 0.98, "Z", K["bronze"], thick=0.04)
    box("Crown", (0.5, 0.3, 0.4), (0, 0, -0.15), K["bronze"], bevel=0.08)
    tube("Crack", [(1.0, -1.05, 1.5), (1.25, -1.2, 1.9), (1.3, -1.35, 2.2), (1.45, -1.25, 2.45)], 0.04, K["dark"], poly=True)
    _xform(s, Matrix.Translation((-1.0, 1.2, H + 1.55)) @ Matrix.Rotation(math.radians(38), 4, "Z") @ Matrix.Rotation(math.radians(-96), 4, "Y"))
    GE.rubble("Chips", (-0.5, -0.4, H + 0.05), 7, 2.2, 0.25, K["limestone"], seed=6)
    set_group("Figure")
    f = figure("ChoirConductor", (0.9, -0.55, H), mats=K["marble"], parts=("head", "rarm", "larm"), face="sing", dark=K["dark"])
    f.settle(H)
    C.hair(f, K, "hair_black", "crop", seed=2)
    f.build("torso", lambda: [GE.shell("Cassock", 1.5, 4.04, 1.07, 0.575, K["wool_black"], r=0.13, nz=8, thick=0.035),
                              GE.shell("Surplice", 2.15, 3.98, 1.1, 0.6, K["linen"], r=0.15, nz=6, flare0=1.32, thick=0.035,
                                       wrinkles=[(2.5, 0.35, 0.06, 6)]),
                              GE.shell("ClericalCollar", 3.86, 4.0, 0.62, 0.5, K["linen"], cy=0.0, r=0.25, nz=1, thick=0.03),
                              frustum("Yoke", (0, 0), 2.26, 1.24, 3.96, 1.4, 0.9, 4.1, K["linen"], bevel=0.04)])
    f.build("torso", lambda: [sphere(f"Lace{k}", 0.09, (math.cos(a) * 1.42, math.sin(a) * 0.82, 2.13), K["linen"], seg=6, rings=3, scale=(1, 1, 0.6))
                              for k, a in enumerate([i * 2 * math.pi / 28 for i in range(28)])])
    f.build("torso", lambda: [GE.ribbon(f"Stole{sx}", [(sx * 0.35, -0.64, 4.05), (sx * 0.3, -0.7, 3.3), (sx * 0.28, -0.74, 2.3), (sx * 0.3, -0.74, 1.75)],
                                        0.26, K["silk_crimson"], up=(1, 0, 0), thick=0.03) for sx in (-1, 1)] +
            [GE.sweep(f"StoleX{sx}{k}", [(sx * 0.29 + d[0], -0.77, 2.0 + d[1]) for d in seg], 0.022, K["gold"], sides=4, smooth=0)
             for sx in (-1, 1) for k, seg in enumerate((((-0.1, 0), (0.1, 0)), ((0, -0.12), (0, 0.12))))])
    C.sleeve_pair(f, K, "linen", bell=1.2, z0=2.15, cuff="linen")
    C.coat_skirt(f, K, "wool_black", length=2.4, z=2.0, gather=1.15, wind=(0.1, 0.35, 0.05), gap=0.0, seed=7, turb=0.3)
    C.boots(f, K, "leather_black", h=0.5, sole="leather_black")
    C.hold(f, 1, lambda: [tube("Baton", [(0, 0, 0), (0, 0, 1.5)], 0.025, K["ebony"], poly=True),
                          sphere("BatonGrip", 0.07, (0, 0, 0.0), K["bone"], seg=8, rings=4, scale=(1, 1, 1.6))], along=(0, 0, -1), push=0.1)
    set_group("Glow")
    hc = f.at("head", (0, 0.9, 4.75))
    GE.staves("Stave", (0.6, -0.4, 0), 2.6, H + 2.0, H + 9.0, K["glowmat"], turns=1.25, phase=0.6, notes=10, seed=3)
    GE.staves("StaveB", (0.6, -0.4, 0), 3.2, H + 1.2, H + 6.0, K["glowmat"], turns=-0.7, phase=2.4, notes=6, seed=8, lines=3)
    set_group("Glow2")
    GE.halo("Halo", hc, 1.25, (0, -1, 0.15), K["glow2mat"], rays=16, ray_len=0.45, thick=0.05)
    set_group("Main")
    return _dims()


def ink_scribe(M):
    """Wren Ashby, ringleader of the Ink Club, painting a sigil on the air: lunging low across a toppled pile of
    leather-bound books with a great brush thrust out, the ink from an overturned well rising off the pages as living
    tendrils that coil round her and end in violet light; a paint-flecked linen smock, a leather apron, rolled sleeves,
    a violet velvet beret and silk scarf, black denim, buckled boots."""
    K = kit(glow=(185, 90, 255), glow2=(120, 230, 255))
    GLOW["InkScribeTendrils"] = {"Glow": (185, 90, 255), "Glow2": (120, 230, 255)}
    H = rect_plinth("P", K, 6.0, 4.2, 1.2, st="limestonedk", top="ebony", trim="brass", plaque="brass", title="WREN ASHBY")
    # the book pile: tumbled great tomes under her, ink spilt across them
    rnd = random.Random(4)
    books = [(-1.4, 0.4, 0.0, 2.1, 1.5, 0.45, 0.2, "leather_oxblood"), (-1.2, 0.2, 0.45, 1.9, 1.4, 0.4, -0.3, "leather_brown"),
             (-1.5, 0.5, 0.85, 1.8, 1.3, 0.38, 0.5, "leather_black"), (1.4, 0.6, 0.0, 2.0, 1.5, 0.42, -0.2, "leather_black"),
             (1.6, 0.3, 0.42, 1.6, 1.2, 0.35, 0.15, "leather_oxblood"), (0.3, -1.0, 0.0, 1.6, 1.1, 0.3, 0.9, "leather_brown")]
    for i, (x, y, z, w, d, t, yaw, cov) in enumerate(books):
        s = _mark()
        GE.book(f"Book{i}", K, w=w, d=d, t=t, cover=cov)
        _xform(s, Matrix.Translation((x, y, H + z)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.06, 0.06), 4, "X"))
    s = _mark()
    GE.book("OpenBook", K, w=1.1, d=1.4, open_=True, cover="leather_oxblood")
    _xform(s, Matrix.Translation((1.7, -1.2, H + 0.05)) @ Matrix.Rotation(-0.4, 4, "Z"))
    lathe("Inkwell", [(0, 0), (0.32, 0), (0.36, 0.18), (0.3, 0.38), (0.14, 0.45), (0.16, 0.55), (0, 0.55)], K["silver"], seg=16, loc=(0, 0, 0))
    P.PARTS[-1].matrix_world = Matrix.Translation((-0.2, -1.25, H + 0.35)) @ Matrix.Rotation(math.radians(80), 4, "Y")
    pool = [(math.cos(a) * (0.9 + 0.3 * math.sin(a * 3)), math.sin(a) * (0.6 + 0.2 * math.cos(a * 2))) for a in [k * 2 * math.pi / 18 for k in range(18)]]
    tpz("InkPool", [(x + 0.5, y - 1.2) for x, y in pool], H + 0.01, 0.03, K["ink"])
    set_group("Figure")
    f = figure("InkScribeTendrils", (0.1, 0.2, H + 0.85), mats=K["marblewarm"], parts=("head", "rarm", "larm"), face="smirk", dark=K["dark"])
    f.settle(H + 0.85)
    C.hair(f, K, "hair_red", "bob", seed=6)
    C.headwear(f, lambda: [O.blob("Beret", [((0.12, 0.08, 5.28), 0.62, (1.15, 1.1, 0.42), (0.0, 0.25, 0.0), 2.0)], K["velvet_violet"], res=0.05, decimate=0.5),
                             GE.sweep("BeretStalk", [(0.1, 0.0, 5.48), (0.12, -0.02, 5.62)], 0.05, K["velvet_violet"], sides=6)])
    f.build("torso", lambda: [GE.shell("Smock", 1.45, 4.04, 1.08, 0.58, K["linen_grey"], r=0.15, nz=9, flare0=1.18, thick=0.035,
                                       wrinkles=[(2.6, 0.5, 0.06, 5), (3.4, 0.3, 0.04, 4)]),
                              tp("Apron", [(-0.75, 1.5), (0.75, 1.5), (0.68, 3.1), (0.42, 3.55), (-0.42, 3.55), (-0.68, 3.1)], -0.64, 0.03, K["leather_brown"]),
                              box("ApronPocket", (0.7, 0.04, 0.42), (0.1, -0.67, 2.45), K["leather_brown"], bevel=0.02),
                              GE.sweep("ApronTie", [(-0.7, -0.62, 2.9), (-1.12, 0.0, 2.9), (0, 0.63, 2.9), (1.12, 0.0, 2.9), (0.7, -0.62, 2.9)], 0.03,
                                       K["leather_brown"], sides=5),
                              GE.sweep("Scarf", [(-0.45, -0.6, 4.08), (0.0, -0.66, 4.02), (0.45, -0.6, 4.08), (0.62, 0.0, 4.1), (0.0, 0.62, 4.1), (-0.62, 0.0, 4.1),
                                                 (-0.45, -0.6, 4.08)], 0.12, K["silk_violet"], sides=8, flat=0.6),
                              GE.ribbon("ScarfEnd", [(0.3, -0.68, 4.0), (0.45, -0.85, 3.6), (0.8, -1.0, 3.4)], 0.22, K["silk_violet"], up=(1, 0, 0), thick=0.025,
                                        twist=0.8)])
    C.sleeve_pair(f, K, "linen_grey", z0=2.75, cuff="linen_grey", cuff_h=0.25)
    C.trousers(f, K, "denim_black", seed=9)
    C.boots(f, K, "leather_brown", h=0.95, sole="rubber", buckles="brass")
    # the great brush
    C.hold(f, 1, lambda: [tube("BrushHandle", [(0, 0, -0.4), (0, 0, 2.4)], 0.07, K["ebony"], poly=True),
                          lathe("Ferrule", [(0.08, 2.35), (0.14, 2.5), (0.14, 2.75), (0.1, 2.8)], K["brass"], seg=12),
                          O.blob("Bristles", O.chain([(0, 0, 2.8), (0.02, 0, 3.2), (0.1, 0, 3.55)], 0.2, 0.03), K["fur_black"], res=0.03, decimate=0.5)],
           along=(0, 0, -1), push=0.15)
    bp, bd = C.hand_at(f, 1)
    tip = bp + bd * 3.5 * S * 0.62
    set_group("Main")
    # living ink: tendrils climbing from the well and the pool, coiling round her and out to the brush
    rnd = random.Random(11)
    starts = [Vector((-0.2, -1.4, H + 0.3)), Vector((0.6, -1.4, H + 0.05)), Vector((1.2, -0.9, H + 0.05)), Vector((-0.8, -1.0, H + 0.05)),
              Vector((0.2, -1.6, H + 0.05))]
    ends = []
    for k, a in enumerate(starts):
        hgt = rnd.uniform(4.5, 8.0)
        ph = rnd.uniform(0, 6.28)
        pts = []
        for i in range(10):
            t = i / 9
            ang = ph + t * rnd.uniform(3.0, 5.0)
            rr = 1.4 + 1.2 * t
            pts.append(a.lerp(Vector((0.3, 0.2, a.z)), t * 0.6) + Vector((math.cos(ang) * rr * t, math.sin(ang) * rr * t * 0.8, hgt * t)))
        if k == 0:
            pts[-1] = tip
            pts[-2] = tip.lerp(pts[-3], 0.5)
        GE.sweep(f"Tendril{k}", pts, lambda t: 0.22 * (1 - t) ** 0.9 + 0.02, K["ink"], sides=8, smooth=2)
        ends.append(pts[-1])
    set_group("Glow")
    for k, e in enumerate(ends[1:]):
        GE.crystal(f"TendrilTip{k}", e, 0.22, K["glowmat"], (0, 0, 1), sides=5)
        GE.embers(f"InkMote{k}", e, 5, 0.9, K["glowmat"], seed=k, size=0.05)
    # the sigil she is painting on the air, standing upright in front of the brush
    s = _mark()
    GE.rune_circle("Sigil", (0, 0, 0), 1.25, K["glowmat"], n=10, seed=4, star=7, depth=0.04)
    _xform(s, Matrix.Translation(tip + bd * 0.6) @ Vector((0, 0, 1)).rotation_difference(bd).to_matrix().to_4x4())
    set_group("Main")
    return _dims()


def delinquent_glare(M):
    """Bruno Vance, boss of the Delinquents, walking away from the sigil he has just sprayed on the Back Lot wall and
    glaring back over his shoulder: a long black leather duster flaring in the wind, a studded leather jacket, a white
    tee, torn jeans, buckled engineer boots, a pompadour; the spray can still hissing in his hand. The sigil burns
    toxic green on a broken brick wall, its paint running; cinder blocks, a tyre and spent cans on cracked asphalt."""
    K = kit(glow=(120, 255, 90), glow2=(255, 60, 200), glass=(150, 255, 120))
    GLOW["DelinquentGlare"] = {"Glow": (120, 255, 90), "Glow2": (255, 60, 200), "Glass": (150, 255, 120)}
    box("Asphalt", (7.0, 5.4, 0.6), (0, 0, 0.3), K["granite"], bevel=0.05)
    for i in range(5):
        GE.slab(f"Crack{i}", (-2.6 + i * 1.3, -1.0 + (i % 2) * 1.4, 0.62), 1.4, 1.2, 0.1, K["granite"], seed=20 + i, tilt=(0.04 * (i - 2), 0.03), chip=0.25)
    H = 0.65
    # the broken brick wall behind, angled to the viewer, with the sigil on it
    s = _mark()
    rnd = random.Random(3)
    for row in range(9):
        n = 7 - max(0, row - 4)
        for c in range(n):
            if row > 5 and rnd.random() < 0.35:
                continue
            x = -2.0 + c * 0.62 + (0.31 if row % 2 else 0)
            box(f"Brick{row}_{c}", (0.58, 0.5, 0.27), (x, 0, 0.15 + row * 0.3), K["brick"], bevel=0.03, rot=(0, rnd.uniform(-0.02, 0.02), 0))
    box("WallCore", (4.0, 0.42, 1.6), (-0.2, 0.02, 0.85), K["granite"], bevel=0.02)
    WM = Matrix.Translation((-1.0, 1.7, H)) @ Matrix.Rotation(math.radians(-24), 4, "Z")
    _xform(s, WM)
    s2 = _mark()
    GE.in_group("Glow", lambda: GE.rune_circle("Sigil", (0, 0, 0), 0.95, K["glowmat"], n=7, seed=9, star=5, depth=0.05))
    GE.in_group("Glow2", lambda: [GE.sweep(f"Tag{k}", pts, 0.05, K["glow2mat"], sides=5, smooth=1) for k, pts in
                                  enumerate(([(-1.6, 0.3, 0), (-1.2, -0.4, 0), (-0.9, 0.4, 0), (-0.5, -0.5, 0)],
                                             [(0.9, -0.6, 0), (1.3, 0.5, 0), (1.5, -0.2, 0), (1.8, 0.6, 0)]))])
    _xform(s2, WM @ Matrix.Translation((-0.2, -0.27, 1.55)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    set_group("Glow")
    for k in range(6):
        x = -1.9 + k * 0.32
        p0 = WM @ Vector((x + 1.0, -0.27, 0.95 + 0.2 * math.sin(k * 2)))
        GE.sweep(f"Drip{k}", [p0, p0 - Vector((0, 0, 0.3 + 0.25 * (k % 3)))], lambda t: 0.035 * (1 - 0.5 * t), K["glowmat"], sides=5, smooth=0)
    set_group("Main")
    tire = lathe("Tire", [(0.35, -0.22), (0.62, -0.25), (0.72, -0.1), (0.72, 0.1), (0.62, 0.25), (0.35, 0.22), (0.3, 0.0), (0.35, -0.22)], K["rubber"], seg=28)
    tire.matrix_world = Matrix.Translation((2.4, 1.2, H + 0.25)) @ Matrix.Rotation(0.3, 4, "X")
    for k, (x, y, z, r) in enumerate(((2.6, -1.5, H, 0.2), (1.6, 1.9, H, 0.0), (2.0, 1.9, H + 0.62, 0.3))):
        box(f"Cinder{k}", (0.9, 0.45, 0.6), (x, y, z + 0.3), K["limestonedk"], bevel=0.03, rot=(0, 0, r))
    for k in range(4):
        cyl(f"Can{k}", 0.12, 0.45, (-2.6 + k * 0.4, -2.0 + (k % 2) * 0.3, H + 0.12), K["spraycan"], verts=12, rot=(math.pi / 2, 0, k * 0.9))
    set_group("Figure")
    f = figure("DelinquentGlare", (0.5, -0.3, H), mats=K["marblewarm"], parts=("head", "rarm", "larm"), face="smirk", dark=K["dark"])
    f.settle(H)
    C.hair(f, K, "hair_black", "pompadour", seed=4)
    f.build("torso", lambda: [GE.shell("Tee", 2.0, 4.0, 1.04, 0.545, K["knit_white"], r=0.12, nz=4, thick=0.02),
                              GE.shell("Jacket", 2.35, 4.05, 1.09, 0.6, K["leather_black"], r=0.14, nz=7, thick=0.045, front_open=0.35,
                                       wrinkles=[(3.0, 0.4, 0.04, 4)]),
                              GE.shell("CollarUp", 3.98, 4.45, 0.78, 0.7, K["leather_black"], cy=0.08, r=0.3, nz=2, flare1=1.15, front_open=0.5, thick=0.05)] +
            [GE.sweep(f"Zip{sx}", [(sx * 0.36, -0.62, 2.4), (sx * 0.38, -0.62, 3.95)], 0.025, K["silver"], sides=4, smooth=0) for sx in (-1, 1)] +
            [sphere(f"Stud{k}", 0.05, (sx * (0.75 + 0.12 * (k % 3)), y, 4.08), K["silver"], seg=6, rings=3)
             for k, (sx, y) in enumerate([(sx, y) for sx in (-1, 1) for y in (-0.35, -0.15, 0.05, 0.25, 0.45)])])
    C.sleeve_pair(f, K, "leather_black", z0=2.05, cuff="leather_black", cuff_h=0.18)
    C.trousers(f, K, "denim", seed=6)
    C.boots(f, K, "leather_black", h=1.0, sole="rubber", buckles="silver", heel=0.16)
    C.belt(f, K, "leather_black", "silver", z=2.05)
    C.coat_skirt(f, K, "leather_black", length=3.0, z=2.25, gather=1.2, wind=(-0.45, -0.25, 0.1), gap=0.4, seed=12, turb=0.5, curl=0.3)
    C.hold(f, 1, lambda: GE.spray_can("Spray", K), along=(0, 0, -1), push=0.05)
    sp, sd = C.hand_at(f, 1)
    set_group("Glass")
    O.plume("SprayMist", K["glassmat"], sp + sd * 1.4 + Vector((0, 0, -0.2)), 0.45, 0.9, seed=3, tendrils=3, billows=6, res=0.08)
    set_group("Main")
    return _dims()


def athlete_spin_kick(M):
    """Captain Rhys Thorne of the Athletes, held mid-air in a spinning hook kick on a cyclone of gold speed-ribbons and
    torn-up turf: the kicking leg flung out high, the other tucked, arms whipping round, the match ball blasting off
    his boot with a trail. Crimson and gold knit kit with the number 1, a captain's armband, striped socks, studded
    boots; the base is a cracked disc of pitch with its white lines, a crater where he launched."""
    K = kit(glow=(255, 200, 70), glow2=(255, 90, 50))
    GLOW["AthleteSpinKick"] = {"Glow": (255, 200, 70), "Glow2": (255, 90, 50)}
    H = round_plinth("P", K, r=3.0, h=1.4, st="limestonedk", band="blackmarble", trim="gold", plaque="gold", title="CAPTAIN RHYS THORNE")
    lathe("Turf", [(0, H), (3.0, H), (3.05, H + 0.12), (0, H + 0.22)], K["turf"], seg=32)
    for k in range(3):
        GE.sweep(f"Line{k}", [(math.cos(a) * 1.5, math.sin(a) * 1.5, H + 0.2) for a in [k * 0.0 + i * 0.25 for i in range(26)]] if k == 0 else
                 [(-2.9 + 0 * k, -1.2 + k * 1.2, H + 0.18), (2.9, -1.2 + k * 1.2, H + 0.18)], 0.05, K["linen"], sides=4, smooth=0, cap=False)
    for i in range(7):
        a = i * 0.9
        GE.slab(f"Clod{i}", (math.cos(a) * 1.1, math.sin(a) * 0.9, H + 0.3), 0.9, 0.6, 0.25, K["rockmoss"], seed=30 + i,
                tilt=(math.sin(a) * 0.6, math.cos(a) * 0.6), yaw=a)
    # the cyclone holding him up: ribbons spiralling from the crater to his hips, turf and stones caught in it
    set_group("Glow")
    for k in range(5):
        ph = k * 2 * math.pi / 5
        pts = [Vector((math.cos(ph + t * 5.5) * (0.5 + 1.3 * t), math.sin(ph + t * 5.5) * (0.5 + 1.1 * t), H + 0.3 + t * 5.0)) for t in [i / 14 for i in range(15)]]
        GE.trail(f"Cyclone{k}", pts, 0.08, 0.32, K["glowmat"], up=(0, 0, 1), thick=0.02, twist=1.0)
    set_group("Main")
    rnd = random.Random(2)
    for i in range(10):
        t = rnd.random()
        a = rnd.uniform(0, 6.28)
        p = (math.cos(a) * (0.6 + 1.4 * t), math.sin(a) * (0.6 + 1.2 * t), H + 0.6 + t * 4.2)
        GE.crystal(f"Debris{i}", p, rnd.uniform(0.12, 0.25), K["rockmoss" if i % 2 else "rock"], (rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1), sides=5, tip=0.8,
                   seed=i)
    set_group("Figure")
    f = figure("AthleteSpinKick", (0, 0, H + 3.6), mats=K["bronze"], parts=("head", "rarm", "larm"), face="shout", dark=K["dark"])
    C.hair(f, K, "bronzedk", "spiky", seed=8)
    f.build("torso", lambda: [GE.shell("Jersey", 2.0, 4.05, 1.08, 0.58, K["knit_crimson"], r=0.14, nz=7, flare0=1.06, thick=0.03,
                                       wrinkles=[(2.7, 0.4, 0.05, 4)]),
                              GE.shell("Neck", 3.95, 4.14, 0.55, 0.45, K["knit_gold"], r=0.2, nz=1, thick=0.03)] +
            [GE.sweep(f"Num{k}", seg, 0.06, K["knit_gold"], sides=4, smooth=0) for k, seg in
             enumerate((((0.0, 0.6, 2.6), (0.0, 0.6, 3.7)), ((0.0, 0.6, 3.7), (-0.25, 0.6, 3.45)), ((-0.25, 0.6, 2.6), (0.25, 0.6, 2.6))))] +
            [GE.sweep(f"Stripe{sx}", [(sx * 1.09, 0, 2.05), (sx * 1.09, 0, 3.95)], 0.05, K["knit_gold"], sides=4, smooth=0) for sx in (-1, 1)])
    C.sleeve_pair(f, K, "knit_crimson", z0=3.1, cuff="knit_gold", cuff_h=0.12)
    f.build("larm", lambda: GE.shell("Armband", 3.3, 3.55, 0.6, 0.6, K["gold"], cx=-1.5, r=0.15, n=20, nz=1, thick=0.04))
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"
        f.build(part, lambda side=side: [GE.shell(f"Shorts{side}", 1.4, 2.1, 0.58, 0.58, K["knit_white"], cx=side * 0.5, r=0.13, n=20, nz=3, flare0=1.08,
                                                  thick=0.03),
                                         GE.shell(f"Sock{side}", 0.3, 1.0, 0.54, 0.54, K["knit_crimson"], cx=side * 0.5, r=0.13, n=20, nz=3, thick=0.025),
                                         GE.shell(f"SockBand{side}", 0.85, 1.0, 0.56, 0.56, K["knit_gold"], cx=side * 0.5, r=0.13, n=20, nz=1, thick=0.02)])
    f.build("torso", lambda: GE.shell("ShortsTop", 1.85, 2.2, 1.06, 0.565, K["knit_white"], r=0.12, nz=1, thick=0.03))
    C.boots(f, K, "leather_black", h=0.32, sole="rubber", toe=0.25, heel=0.05)
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"
        f.build(part, lambda side=side: [cone(f"Stud{side}{k}", 0.06, 0.03, 0.12, (side * 0.5 + (k % 2 - 0.5) * 0.6, -0.4 + (k // 2) * 0.4, -0.06), K["silver"], verts=6)
                                         for k in range(6)])
    # the ball blasting off his kicking boot
    ft = f.at("rleg", (0.5, -0.5, 0.2))
    kd = (f.at("rleg", (0.5, 0, 0.0)) - f.at("rleg", (0.5, 0, 1.0))).normalized()
    ball = ft + kd * 1.4 + Vector((0, -0.4, 0))
    set_group("Main")
    sphere("Ball", 0.55, tuple(ball), K["leather_brown"], seg=20, rings=12, scale=(1.25, 1, 1))
    for k in range(3):
        hoop(f"BallSeam{k}", tuple(ball), 0.56 + 0.005 * k, ("X", "Y", "Z")[k], K["linen"], thick=0.015)
    set_group("Glow2")
    GE.trail("BallTrail", [ball - kd * 0.3, ball - kd * 1.5 + Vector((0, 0.3, -0.4)), ball - kd * 3.0 + Vector((0, 0.8, -0.6))], 0.7, 0.05, K["glow2mat"],
             up=(0, 0, 1), thick=0.02)
    set_group("Glow")
    GE.trail("KickArc", [f.at("rleg", (0.5, 0, 0.3)) + Vector((0, 0.4 * k, 0)) for k in range(1)] + [ft + Vector((1.2, 1.5, 0.6)), ft + Vector((2.6, 2.2, 1.6)),
                                                                                                 ft + Vector((3.2, 1.6, 3.0))], 0.5, 0.05, K["glowmat"],
             up=kd, thick=0.02)
    set_group("Main")
    return _dims()



def obb(c, h):
    """An axis-aligned collider box for the cloth simulation (centre, half extents)."""
    return (Matrix.Translation(c), Vector(h))


def court_duchess_throne(M):
    """Vesper Crane, the Crimson Court's duchess, lounging on her throne at the top of a black-marble dais: legs crossed,
    chin on one gloved hand, a gold goblet dangling from the other over the carved arm; a crimson velvet gown whose
    simulated skirt spills over the seat and down the steps, a gilt-laced corset, black silk sleeves and gloves, a
    ruby choker and a gold tiara; a great blood-moon halo burns behind the throne's pointed back."""
    K = kit(glow=(255, 40, 50), glow2=(255, 120, 90))
    GLOW["CourtDuchessThrone"] = {"Glow": (255, 40, 50), "Glow2": (255, 120, 90)}
    z = 0.0
    for k, (w, d, h) in enumerate(((7.2, 6.0, 0.45), (6.2, 5.0, 0.45), (5.2, 4.0, 0.45))):
        box(f"Dais{k}", (w, d, h), (0, 0.5 * k * 0.6, z + h / 2), K["blackmarble"], bevel=0.06)
        box(f"Nosing{k}", (w + 0.04, 0.08, 0.08), (0, 0.5 * k * 0.6 - d / 2, z + h - 0.04), K["gilt"], bevel=0.02)
        z += h
    H = z
    GE.ribbon("Runner", [(0, -3.05, 0.05), (0, -2.85, 0.47), (0, -2.5, 0.92), (0, -2.0, H + 0.02), (0, -0.6, H + 0.02)], 1.6, K["velvet_crimson"],
              up=(1, 0, 0), thick=0.03, smooth=1)
    rnd = random.Random(8)
    for i in range(16):
        p = (rnd.uniform(-2.8, 2.8), rnd.uniform(-2.9, 0.6), 0.0)
        zz = 0.46 * min(3, max(0, int((p[1] + 3.1) / 0.6))) + 0.02
        O.feather(f"Petal{i}", (p[0], p[1], zz + 0.01), (rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.05), 0.22, 0.2, K["velvet_crimson"], curl=0.25,
                  side=(0, 0, 1), n=4, thick=0.01)
    # the figure first, then the throne built round her
    set_group("Figure")
    f = figure("CourtDuchessThrone", (0, 0.4, H), mats=K["marble"], parts=("head", "rarm", "larm"), face="smirk", dark=K["dark"], glow_eyes="Glow")
    f.settle(H)
    seat = f.at("torso", (0, 0, 2.0)).z - 0.12
    set_group("Main")
    sy = f.at("torso", (0, 0, 2.0)).y
    box("Seat", (4.0, 3.0, 0.5), (0, sy + 0.3, seat - 0.25), K["ebony"], bevel=0.08)
    box("Cushion", (3.6, 2.7, 0.3), (0, sy + 0.25, seat - 0.05), K["velvet_crimson"], bevel=0.12)
    for sx in (-1, 1):
        for yy in (-1.2, 1.2):
            lathe(f"Leg{sx}{yy}", [(0, H), (0.3, H), (0.22, H + 0.3), (0.28, (H + seat) / 2), (0.2, seat - 0.5), (0, seat - 0.5)], K["ebony"], seg=12,
                  loc=(sx * 1.75, sy + 0.3 + yy, 0))
        box(f"Arm{sx}", (0.45, 2.8, 0.35), (sx * 2.0, sy + 0.2, seat + 1.1), K["ebony"], bevel=0.1)
        box(f"ArmPad{sx}", (0.42, 2.2, 0.15), (sx * 2.0, sy + 0.3, seat + 1.32), K["velvet_crimson"], bevel=0.05)
        tube(f"ArmPost{sx}", [(sx * 2.0, sy - 1.0, seat), (sx * 2.0, sy - 1.05, seat + 1.0)], 0.13, K["ebony"])
        sphere(f"ArmKnob{sx}", 0.28, (sx * 2.0, sy - 1.25, seat + 1.15), K["gilt"], seg=12, rings=8)
    by = sy + 1.65
    back = [(-1.95, 0), (1.95, 0), (1.95, 4.2), (1.6, 5.2), (0.9, 6.0), (0.0, 6.7), (-0.9, 6.0), (-1.6, 5.2), (-1.95, 4.2)]
    tp("Back", [(x, seat + z) for x, z in back], by, 0.35, K["ebony"])
    tp("BackPad", [(x * 0.82, seat + 0.3 + z * 0.86) for x, z in back], by - 0.22, 0.12, K["velvet_crimson"])
    for r in range(4):
        for c in range(3):
            sphere(f"Tuft{r}{c}", 0.08, ((c - 1) * 0.9 + (0.45 if r % 2 else 0) * 0, by - 0.3, seat + 1.0 + r * 1.1), K["gilt"], seg=8, rings=4)
    GE.sweep("BackTrim", [(x * 1.02, by - 0.2, seat + z) for x, z in back[1:] + back[:1]], 0.06, K["gilt"], sides=6, smooth=0)
    for sx in (-1, 1):
        lathe(f"Finial{sx}", [(0, 0), (0.22, 0), (0.25, 0.2), (0.12, 0.35), (0.18, 0.6), (0.05, 0.9), (0, 1.1)], K["gilt"], seg=12,
              loc=(sx * 1.95, by, seat + 4.2))
    cone("Crest", 0.3, 0.0, 0.9, (0, by, seat + 7.1), K["gilt"], verts=8)
    # the blood moon behind the throne
    set_group("Glow")
    cyl("BloodMoon", 2.9, 0.15, (0, by + 0.45, seat + 5.2), K["glowmat"], rot=(math.pi / 2, 0, 0), verts=48, bevel=0.03)
    set_group("Glow2")
    GE.halo("MoonRays", (0, by + 0.3, seat + 5.2), 3.15, (0, -1, 0), K["glow2mat"], rays=24, ray_len=0.9, thick=0.05, spikes=True)
    set_group("Figure")
    C.hair(f, K, "hair_black", "long", seed=3, length=1.1)
    C.headwear(f, mode="crown", fn=lambda: GE.crown("Tiara", K, (0, -0.05, 5.0), r=0.62, h=0.3, points=7, metal="gold", gems=("ruby", "amethyst"), tilt=(0.18, 0)))
    f.build("torso", lambda: [GE.shell("Corset", 2.0, 4.0, 1.07, 0.58, K["velvet_crimson"], r=0.15, nz=6, thick=0.04, flare1=1.02),
                              GE.shell("Bust", 3.85, 4.06, 1.1, 0.6, K["silk_black"], r=0.15, nz=1, thick=0.03)] +
            [GE.sweep(f"Lace{k}", [(-0.12, -0.6, 2.2 + k * 0.28), (0.12, -0.6, 2.34 + k * 0.28)], 0.02, K["gold"], sides=4, smooth=0) for k in range(6)] +
            [GE.sweep(f"LaceB{k}", [(0.12, -0.6, 2.2 + k * 0.28), (-0.12, -0.6, 2.34 + k * 0.28)], 0.02, K["gold"], sides=4, smooth=0) for k in range(6)] +
            [hoop("Choker", (0, 0, 4.12), 0.48, "Z", K["silk_black"], thick=0.04),
             sphere("ChokerRuby", 0.1, (0, -0.52, 4.08), K["ruby"], seg=8, rings=4, scale=(1, 0.6, 1.3))])
    C.sleeve_pair(f, K, "silk_black", bell=1.18, z0=2.4, cuff="velvet_crimson")
    C.gauntlets(f, K, "silk_black", cuff="silk_black", plates=False)
    C.boots(f, K, "leather_black", h=0.6, sole="leather_black", heel=0.25)
    cols = f.colliders(pad=0.05, skip=("head",)) + [obb((0, sy + 0.3, seat - 0.25), (2.05, 1.55, 0.3))]
    C.coat_skirt(f, K, "velvet_crimson", length=3.6, z=2.15, gather=1.35, wind=(0, -0.2, 0.0), gap=0.0, colliders=cols, floor=H, seed=5, lining="silk_black",
                 rows=20, cols=32)
    C.hold(f, 1, lambda: [lathe("Goblet", [(0, 0), (0.25, 0), (0.08, 0.06), (0.05, 0.4), (0.06, 0.45), (0.26, 0.6), (0.3, 0.95), (0.27, 0.95), (0.03, 0.62),
                                           (0, 0.62)], K["gold"], seg=16),
                          sphere("GobletRuby", 0.06, (0.0, -0.05, 0.4), K["ruby"], seg=6, rings=3)], along=(0, 0.3, -1), push=0.0)
    set_group("Main")
    return _dims()


def reaper_guard(M):
    """The Reaper Prefect, the school's oldest legend, braced low in a guard stance with the great scythe held across
    his body while violet lightning crackles off the blade: a tattered hooded black cloak over the prefect's blazer
    with its silver badge and sash, a bone skull mask with burning eyes, leather gloves and boots; lost souls coil round
    the blade. A graveyard base: a mound of grave soil, a toppled stone cross, a split headstone and iron railings."""
    K = kit(glow=(200, 160, 255), glow2=(120, 255, 230), glass=(190, 230, 255))
    GLOW["ReaperGuard"] = {"Glow": (200, 160, 255), "Glow2": (120, 255, 230), "Glass": (190, 230, 255)}
    H = rect_plinth("P", K, 6.2, 4.6, 1.3, st="limestonedk", top="slate", trim="iron", plaque="silver", title="THE REAPER PREFECT")
    O.blob("Mound", [((x, y, H), r, (1.4, 1.0, 0.4), None, 2.0) for x, y, r in ((-0.4, 0.4, 1.4), (1.2, 0.8, 1.1), (-1.8, 0.9, 0.9), (0.6, -0.8, 1.0))],
           K["rockmoss"], res=0.14, decimate=0.5, displace=(0.12, 0.3))
    s = _mark()
    tp("Cross", [(-0.2, 0), (0.2, 0), (0.2, 1.6), (0.65, 1.6), (0.65, 2.0), (0.2, 2.0), (0.2, 2.6), (-0.2, 2.6), (-0.2, 2.0), (-0.65, 2.0), (-0.65, 1.6),
                 (-0.2, 1.6)], 0, 0.3, K["limestone"])
    _xform(s, Matrix.Translation((2.0, 1.4, H + 0.2)) @ Matrix.Rotation(math.radians(-30), 4, "Z") @ Matrix.Rotation(math.radians(-62), 4, "X"))
    s = _mark()
    tp("StoneL", [(-0.7, 0), (0.0, 0), (0.05, 1.2), (-0.2, 1.7), (-0.5, 1.9), (-0.7, 1.7)], 0, 0.28, K["limestonedk"])
    tp("StoneR", [(0.1, 0), (0.7, 0), (0.7, 1.7), (0.5, 1.9), (0.25, 1.75), (0.15, 1.1)], 0, 0.28, K["limestonedk"])
    _xform(s, Matrix.Translation((-2.0, 1.7, H)) @ Matrix.Rotation(math.radians(18), 4, "Z") @ Matrix.Rotation(math.radians(-8), 4, "Y"))
    for k in range(5):
        x = -3.0 + k * 0.4
        tube(f"Rail{k}", [(x, 2.1, H), (x, 2.1, H + 1.6 + 0.1 * (k % 2))], 0.04, K["iron"], poly=True)
        cone(f"RailSpike{k}", 0.08, 0.0, 0.25, (x, 2.1, H + 1.75 + 0.1 * (k % 2)), K["iron"], verts=4)
    tube("RailBar", [(-3.05, 2.1, H + 1.3), (-1.35, 2.1, H + 1.3)], 0.035, K["iron"], poly=True)
    set_group("Figure")
    f = figure("ReaperGuard", (0, -0.4, H + 0.2), mats=K["marble"], parts=("head", "rarm", "larm"), face="none", dark=K["dark"])
    f.settle(H + 0.2)
    C.jacket(f, K, "wool_black", hem=1.75, lapel="silk_black", shirt="linen", tie="silk_violet", buttons="silver", seed=31, trim="silver",
             crest=("silk_violet", "silver"))
    C.trousers(f, K, "wool_black", seed=32)
    C.boots(f, K, "leather_black", h=1.0, sole="rubber", buckles="silver")
    C.gauntlets(f, K, "leather_black", cuff="leather_black", plates=False)
    f.build("torso", lambda: GE.ribbon("Sash", [(-1.0, -0.66, 3.95), (-0.3, -0.68, 3.2), (0.4, -0.68, 2.55), (1.05, -0.64, 2.05)], 0.3, K["silk_violet"],
                                        up=(0.6, 0, 0.8), thick=0.03))
    f.build("torso", lambda: [lathe("Badge", [(0, 0), (0.16, 0), (0.18, 0.04), (0, 0.06)], K["silver"], seg=12)])
    P.PARTS[-1].matrix_world = Matrix.Translation(f.at("torso", (0.55, -0.66, 3.55))) @ Vector((0, 0, 1)).rotation_difference(
        (f.world("waist").to_3x3() @ Vector((0, -1, 0))).normalized()).to_matrix().to_4x4()
    C.hood(f, K, "wool_black", up=True, deep=0.25)
    f.build("head", lambda: [O.blob("Mask", [((0, -0.62, 4.6), 0.5, (1.05, 0.35, 1.15), None, 2.0), ((0, -0.66, 4.3), 0.3, (1.0, 0.5, 0.8), None, 2.0)],
                                    K["bone"], res=0.04, decimate=0.5)] +
            [sphere(f"Socket{sx}", 0.13, (sx * 0.2, -0.78, 4.68), K["dark"], seg=10, rings=6, scale=(1, 0.5, 1.1)) for sx in (-1, 1)] +
            [box(f"Tooth{k}", (0.07, 0.05, 0.1), (-0.15 + k * 0.075, -0.82, 4.25), K["bone"], bevel=0.02) for k in range(5)])
    GE.in_group("Glow2", lambda: f.build("head", lambda: [sphere(f"EyeFire{sx}", 0.06, (sx * 0.2, -0.8, 4.68), K["glow2mat"], seg=8, rings=4)
                                                         for sx in (-1, 1)]))
    C.cape(f, K, "wool_black", lining="velvet_violet", length=4.4, wind=(0.3, 0.35, 0.05), gather=1.3, ragged=0.7, seed=6, clasp="silver", gem="amethyst",
           turb=0.6, curl=0.3, floor=H)
    # the scythe held across his body through both fists
    a, _ = C.hand_at(f, 1)
    b, _ = C.hand_at(f, -1)
    ax = (b - a).normalized()
    s = _mark()
    GE.scythe("Scythe", K, L=6.2, blade=2.8, glow="Glow")
    _xform(s, Matrix.Translation(a - ax * 1.6) @ Vector((0, 0, 1)).rotation_difference(ax).to_matrix().to_4x4() @ Matrix.Rotation(math.radians(200), 4, "Z") @
           Matrix.Scale(1.0, 4))
    top = a - ax * 1.6 + ax * 6.2
    set_group("Glow")
    for k in range(4):
        GE.lightning(f"Bolt{k}", top + Vector((0, 0, 0.2)), top + Vector((random.Random(k).uniform(-2.2, 2.2), random.Random(k + 9).uniform(-1.5, 1.0),
                                                                        random.Random(k + 3).uniform(-2.5, 1.5))), K["glowmat"], seed=k, r=0.05, branches=2)
    GE.lightning("Ground", a + Vector((0, 0, -0.5)), Vector((a.x + 1.2, a.y - 0.6, H + 0.1)), K["glowmat"], seed=11, r=0.045, branches=3)
    set_group("Glass")
    for k in range(3):
        GE.wisp(f"Soul{k}", top - ax * 1.5, 1.1 + 0.3 * k, top.z - 2.5, top.z + 1.0, K["glassmat"], turns=0.8 * (1 if k % 2 else -1), r0=0.22, phase=k * 2.1,
                flat=0.5, sides=8)
    set_group("Main")
    return _dims()


def pack_alpha_landing(M):
    """Dex Moreno, alpha of the Pack, crashing down in a three-point landing that has smashed the plinth's top into a
    crater, one fist driven into the stone, glaring up through his mane; a crimson varsity jacket with leather sleeves
    and a grey fur collar, a white tee, ripped jeans, high-top trainers; the cracks glow ember-orange, debris hangs in
    the air, and a great spectral wolf rears up behind him, howling."""
    K = kit(glow=(255, 120, 40), glow2=(255, 200, 80), glass=(160, 210, 255))
    GLOW["PackAlphaLanding"] = {"Glow": (255, 120, 40), "Glow2": (255, 200, 80), "Glass": (160, 210, 255)}
    H = oct_plinth("P", K, r=3.3, h=1.6, st="limestonedk", band="granite", trim="iron", plaque="bronze", title="DEX MORENO")
    rnd = random.Random(14)
    for i in range(10):     # the crater: slabs of the top heaved up and tilted outward round the impact
        a = i * 2 * math.pi / 10 + rnd.uniform(-0.15, 0.15)
        d = rnd.uniform(1.4, 2.6)
        GE.slab(f"Heave{i}", (math.cos(a) * d, math.sin(a) * d * 0.9, H + 0.18), rnd.uniform(1.0, 1.5), rnd.uniform(0.8, 1.2), 0.3, K["limestonedk"], seed=40 + i,
                tilt=(math.sin(a) * 0.45, -math.cos(a) * 0.45), yaw=a)
    set_group("Glow")
    for i in range(10):
        a = i * 2 * math.pi / 10 + 0.3
        pts = [Vector((math.cos(a) * r_, math.sin(a) * r_ * 0.9, H + 0.03)) + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0)) for r_ in
               (0.3, 0.9, 1.6, 2.3, 3.0)]
        GE.sweep(f"Crack{i}", pts, lambda t: 0.07 * (1 - 0.6 * t), K["glowmat"], sides=4, smooth=0)
    set_group("Main")
    GE.rubble("Debris", (0.0, -0.4, H + 1.2), 12, 2.6, 0.32, K["limestonedk"], seed=4)
    set_group("Figure")
    f = figure("PackAlphaLanding", (0, -0.2, H), mats=K["marblewarm"], parts=("head", "rarm", "larm"), face="fierce", dark=K["dark"], glow_eyes="Glow2")
    f.settle(H)
    C.hair(f, K, "hair_black", "mane", seed=9, length=0.8, flow=(0, 1, 0.6))
    f.build("torso", lambda: [GE.shell("Tee", 2.0, 4.0, 1.04, 0.545, K["knit_white"], r=0.12, nz=4, thick=0.02),
                              GE.shell("Varsity", 2.2, 4.05, 1.09, 0.6, K["wool_crimson"], r=0.14, n=32, nz=10, thick=0.045, front_open=0.32,
                                       wrinkles=[(3.0, 0.4, 0.05, 4)]),
                              GE.shell("RibHem", 2.12, 2.36, 1.1, 0.61, K["knit_gold"], r=0.14, nz=1, thick=0.04, front_open=0.32),
                              O.blob("FurCollar", O.chain([(-0.95, -0.5, 4.08), (-1.05, 0.25, 4.12), (0, 0.95, 4.15), (1.05, 0.25, 4.12), (0.95, -0.5, 4.08)],
                                                          0.24, 0.24), K["fur_grey"], res=0.06, decimate=0.4, displace=(0.06, 0.08))] +
            [GE.sweep(f"Letter{k}", seg, 0.05, K["knit_gold"], sides=4, smooth=0) for k, seg in
             enumerate((((-0.75, -0.61, 3.0), (-0.75, -0.61, 3.6)), ((-0.75, -0.61, 3.6), (-0.45, -0.61, 3.3)), ((-0.45, -0.61, 3.3), (-0.45, -0.61, 3.0))))])
    C.sleeve_pair(f, K, "leather_black", z0=2.05, cuff="knit_gold", cuff_h=0.22)
    C.trousers(f, K, "denim", seed=15)
    C.boots(f, K, "knit_white", h=0.75, sole="rubber", toe=0.2, cuff="knit_white", heel=0.06)
    C.claws(f, K, "bone", L=0.32)
    # the spectral wolf rearing behind him
    set_group("Glass")
    O.wolf("SpiritWolf", K["glassmat"], Matrix.Translation((1.5, 3.2, H + 0.4)) @ Matrix.Rotation(math.radians(-15), 4, "Z") @ Matrix.Scale(1.6, 4), howl=True, rear=0.75, res=0.11, decimate=0.4,
           eye="Glow2", eye_mat=K["glow2mat"], fur=0.07)
    set_group("Glow2")
    GE.embers("Spark", (0, 0, H + 1.5), 16, 3.0, K["glow2mat"], seed=2, size=0.05, rise=1.6)
    set_group("Main")
    return _dims()


def founder_ravens(M):
    """The Founder, Alaric Vauclair, crowned by ravens: on the cracked cornerstone of the school, his arms flung wide,
    the great key held high in one hand, a raven landing on the other; a black velvet academic robe with an ermine
    cape and a gold chain of office, a long white beard; six ravens wheel round his head in a living crown, their eyes
    burning, a ring of moonlight running through their flight."""
    K = kit(glow=(255, 60, 60), glow2=(190, 210, 255))
    GLOW["FounderRavens"] = {"Glow": (255, 60, 60), "Glow2": (190, 210, 255)}
    H = oct_plinth("P", K, r=2.9, h=2.4, st="limestonedk", band="blackmarble", trim="gilt", plaque="brass", title="ALARIC VAUCLAIR, FOUNDER")
    box("Cornerstone", (3.6, 2.8, 0.9), (0, 0, H + 0.45), K["limestone"], bevel=0.08)
    text("Anno", "ANNO MDCCCXXI", K["gilt"], 0, -1.42, H + 0.45, (2.8, 0.36), depth=0.03)
    tube("Crack", [(1.3, -1.41, H + 0.9), (1.0, -1.43, H + 0.55), (1.2, -1.43, H + 0.3), (0.9, -1.42, H)], 0.035, K["dark"], poly=True)
    for k, (x, y, yaw) in enumerate(((-1.7, -1.6, 0.4), (1.6, -1.4, -0.7))):
        s = _mark()
        GE.sweep(f"Scroll{k}", [(-0.5, 0, 0.15), (0.5, 0, 0.15)], 0.15, K["parchment"], sides=10)
        for sx in (-1, 1):
            cyl(f"ScrollEnd{k}{sx}", 0.06, 0.25, (sx * 0.58, 0, 0.15), K["ebony"], rot=(0, math.pi / 2, 0), verts=8)
        _xform(s, Matrix.Translation((x, y, H)) @ Matrix.Rotation(yaw, 4, "Z"))
    GE.chain_links("Chain", (-1.8, 1.4, H + 0.9), (-2.6, -0.4, 0.4), K["iron"], link=0.22, thick=0.04, sag=0.3)
    set_group("Figure")
    top = H + 0.9
    f = figure("FounderRavens", (0, 0.0, top), mats=K["marble"], parts=("head", "rarm", "larm"), face="stern", dark=K["dark"])
    f.settle(top)
    C.hair(f, K, "hair_white", "long", seed=12, length=0.8)
    f.build("head", lambda: O.blob("Beard", [(p, r, (1.3, 0.55, 1.0), None, 2.0) for p, r, *_ in
                                             O.chain([(-0.5, -0.5, 4.35), (-0.3, -0.62, 4.15), (0, -0.66, 4.08), (0.3, -0.62, 4.15), (0.5, -0.5, 4.35)], 0.17, 0.17) +
                                             O.chain([(0, -0.64, 4.1), (0.0, -0.64, 3.75), (0.03, -0.6, 3.4)], 0.3, 0.16)] +
                                   [((sx * 0.18, -0.64, 4.32), 0.12, (1.6, 0.6, 0.6), None, 2.0) for sx in (-1, 1)],
                                   K["hair_white"], res=0.04, decimate=0.4, displace=(0.015, 0.04)))
    C.jacket(f, K, "velvet_black", hem=1.6, lapel="silk_gold", shirt="linen", vest="silk_crimson", buttons="gold", seed=41, trim="gold", cuff="velvet_black")
    C.coat_skirt(f, K, "velvet_black", length=3.4, z=2.1, gather=1.22, wind=(0.1, 0.4, 0.05), gap=0.25, lining="silk_crimson", seed=13)
    C.boots(f, K, "leather_black", h=0.6, sole="leather_black")
    f.build("torso", lambda: [O.blob("Ermine", O.chain([(-1.25, -0.5, 4.1), (-1.3, 0.35, 4.14), (0, 1.0, 4.18), (1.3, 0.35, 4.14), (1.25, -0.5, 4.1)], 0.3, 0.3),
                                     K["fur_white"], res=0.07, decimate=0.4, displace=(0.04, 0.08))] +
            [sphere(f"Spot{k}", 0.06, (math.cos(a) * 1.15, math.sin(a) * 0.7 + 0.05, 4.18), K["fur_black"], seg=6, rings=3, scale=(0.7, 0.7, 1.5))
             for k, a in enumerate([0.2 + i * 0.45 for i in range(7)])] +
            [GE.sweep("OfficeChain", [(-0.85, -0.6, 4.0), (-0.45, -0.68, 3.45), (0, -0.7, 3.3), (0.45, -0.68, 3.45), (0.85, -0.6, 4.0)], 0.045, K["gold"], sides=6),
             lathe("Medal", [(0, 0), (0.22, 0), (0.24, 0.05), (0, 0.07)], K["gold"], seg=16)])
    P.PARTS[-1].matrix_world = Matrix.Translation(f.at("torso", (0, -0.74, 3.2))) @ Matrix.Rotation(math.pi / 2, 4, "X")
    # the great key in his raised hand
    C.hold(f, 1, lambda: [tube("KeyShaft", [(0, 0, -0.3), (0, 0, 2.2)], 0.09, K["gold"], poly=True),
                          GE.sweep("KeyBow", [(math.cos(a) * 0.35, 0, -0.65 + math.sin(a) * 0.35) for a in [i * 2 * math.pi / 16 for i in range(17)]], 0.07,
                                   K["gold"], sides=6, smooth=0),
                          box("KeyBit1", (0.5, 0.1, 0.18), (0.25, 0, 2.0), K["gold"], bevel=0.03),
                          box("KeyBit2", (0.35, 0.1, 0.16), (0.18, 0, 1.7), K["gold"], bevel=0.03)], along=(0, 0, -1), push=0.3)
    set_group("Main")
    hp, _ = C.hand_at(f, -1)
    O.raven("Perch", K, hp + Vector((0, 0, 0.6)), heading=math.radians(150), wings=0.95, s=1.7, eye="Glow")
    hc = f.at("head", (0, 0, 5.6))
    for k in range(6):
        a = k * 2 * math.pi / 6
        p = hc + Vector((math.cos(a) * 2.2, math.sin(a) * 1.8, 0.4 + 0.35 * math.sin(a * 2)))
        O.raven(f"Crown{k}", K, p, heading=a + math.pi / 2, wings=0.45 + 0.4 * (k % 2), s=1.45, eye="Glow", bank=0.45)
    set_group("Glow2")
    GE.wisp("CrownRing", hc, 2.0, hc.z + 0.2, hc.z + 0.7, K["glow2mat"], turns=1.0, r0=0.05, r1=0.02, flat=0.6, wobble=0.05)
    set_group("Main")
    return _dims()


def exorcist_sigil(M):
    """A Grand Priest of the Chapel, a Saint of the Exorcists, standing in a blazing sigil cut into the crypt floor:
    one hand raised before his face in the sign of binding, the other holding out an open grimoire that floats above his
    palm, its pages tearing loose; a black cassock with a long skirt, an ivory silk chasuble embroidered with gold, a
    crimson stole, a rosary; chains burst from the floor and shards of light orbit him."""
    K = kit(glow=(255, 210, 120), glow2=(170, 210, 255))
    GLOW["ExorcistSigil"] = {"Glow": (255, 210, 120), "Glow2": (170, 210, 255)}
    H = round_plinth("P", K, r=3.3, h=1.2, st="slate", band="blackmarble", trim="gilt", plaque="gilt", title="THE SAINT OF BINDING")
    for i in range(6):
        GE.slab(f"Flag{i}", (math.cos(i * 1.05) * 1.9, math.sin(i * 1.05) * 1.9, H + 0.06), 1.5, 1.2, 0.12, K["limestonedk"], seed=60 + i, yaw=i * 1.05, chip=0.2)
    set_group("Glow")
    GE.rune_circle("Sigil", (0, 0, H + 0.14), 2.9, K["glowmat"], n=14, seed=21, star=7, depth=0.045)
    set_group("Main")
    for k, (a, b) in enumerate((((-2.3, -1.2, H), (-1.1, -0.6, H + 2.2)), ((2.2, -1.4, H), (1.4, -0.5, H + 1.8)), ((0.2, 2.4, H), (0.4, 1.2, H + 2.6)))):
        GE.chain_links(f"BurstChain{k}", a, b, K["iron"], link=0.2, thick=0.035, sag=-0.2)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        x, y = math.cos(a) * 2.75, math.sin(a) * 2.75
        cyl(f"Candle{k}", 0.1, 0.5 + 0.15 * (k % 2), (x, y, H + 0.3), K["wax"], verts=10)
        GE.in_group("Glow", lambda x=x, y=y, k=k: GE.flames(f"CF{k}", (x, y, H + 0.6 + 0.15 * (k % 2)), 0.26, 0.06, K["glowmat"], n=1, seed=k))
    set_group("Figure")
    f = figure("ExorcistSigil", (0, 0, H + 0.15), mats=K["marble"], parts=("head", "rarm", "larm"), face="closed", dark=K["dark"])
    f.settle(H + 0.15)
    C.hair(f, K, "hair_white", "crop", seed=4)
    f.build("torso", lambda: [GE.shell("Cassock", 1.6, 4.04, 1.07, 0.575, K["wool_black"], r=0.13, nz=8, thick=0.035),
                              GE.shell("ClericalCollar", 3.86, 4.0, 0.62, 0.5, K["linen"], r=0.25, nz=1, thick=0.03)])
    C.sleeve_pair(f, K, "wool_black", bell=1.12, cuff="silk_ivory")
    C.coat_skirt(f, K, "wool_black", length=2.3, z=2.0, gather=1.2, wind=(0.0, 0.0, 0.45), gap=0.0, seed=17, turb=0.5)
    C.boots(f, K, "leather_black", h=0.5, sole="leather_black")
    # the chasuble: front and back panels of embroidered silk falling over the cassock
    def chasuble():
        out = []
        for sy, nm in ((-1, "Front"), (1, "Back")):
            pts = [(-0.95, 4.02), (0.95, 4.02), (0.98, 2.4), (0.6, 1.75), (0, 1.55), (-0.6, 1.75), (-0.98, 2.4)]
            out.append(tp(f"Chasuble{nm}", pts, sy * 0.66, 0.04, K["silk_ivory"]))
            out.append(GE.sweep(f"Orphrey{nm}", [(x * 0.96, sy * 0.69, z) for x, z in pts + pts[:1]], 0.03, K["gold"], sides=4, smooth=0, cap=False))
            out.append(GE.sweep(f"CrossV{nm}", [(0, sy * 0.7, 3.85), (0, sy * 0.7, 1.75)], 0.07, K["gold"], sides=4, smooth=0))
            out.append(GE.sweep(f"CrossH{nm}", [(-0.6, sy * 0.7, 3.3), (0.6, sy * 0.7, 3.3)], 0.07, K["gold"], sides=4, smooth=0))
            out.append(sphere(f"Boss{nm}", 0.12, (0, sy * 0.73, 3.3), K["ruby"], seg=8, rings=4, scale=(1, 0.5, 1)))
        out.append(GE.ribbon("StoleL", [(-0.35, -0.72, 4.05), (-0.32, -0.75, 2.6), (-0.32, -0.76, 1.4)], 0.22, K["silk_crimson"], up=(1, 0, 0), thick=0.03))
        out.append(GE.ribbon("StoleR", [(0.35, -0.72, 4.05), (0.32, -0.75, 2.6), (0.32, -0.76, 1.4)], 0.22, K["silk_crimson"], up=(1, 0, 0), thick=0.03))
        return out
    f.build("torso", chasuble)
    hp, hd = C.hand_at(f, 1)
    lp, _ = C.hand_at(f, -1)
    set_group("Main")
    beads = [lp + Vector((0.25 * math.cos(a), 0.15 * math.sin(a), -0.3 - 0.6 * (1 - math.cos(a)) / 2)) for a in [i * 2 * math.pi / 14 for i in range(14)]]
    for k, p in enumerate(beads):
        sphere(f"Bead{k}", 0.05, tuple(p), K["ebony"], seg=6, rings=3)
    s = _mark()
    GE.book("Grimoire", K, w=1.0, d=1.3, open_=True, cover="leather_oxblood")
    _xform(s, Matrix.Translation(lp + Vector((0, -0.3, 0.9))) @ Matrix.Rotation(-0.35, 4, "X") @ Matrix.Rotation(0.3, 4, "Z"))
    rnd = random.Random(6)
    for k in range(6):
        p = lp + Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-1.2, 0.8), rnd.uniform(1.2, 3.2)))
        GE.ribbon(f"Page{k}", [p, p + Vector((0.3, 0.05, 0.12)), p + Vector((0.55, 0.0, 0.05))], 0.36, K["parchment"], up=(rnd.uniform(-1, 1), 0.4, 1), thick=0.01,
                  twist=rnd.uniform(-1, 1))
    set_group("Glow")
    s = _mark()
    GE.rune_circle("Binding", (0, 0, 0), 0.7, K["glowmat"], n=6, seed=33, star=5, depth=0.035, inner=0.7)
    _xform(s, Matrix.Translation(hp + Vector((0, -0.6, 0.6))) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    set_group("Glow2")
    GE.shards("Shard", (0, 0, H + 5.2), 14, 2.6, 0.28, K["glow2mat"], seed=8, up=0.9)
    GE.halo("Aura", f.at("head", (0, 1.4, 4.7)), 1.15, (0, -1, 0), K["glow2mat"], rays=12, ray_len=0.5, thick=0.04)
    set_group("Main")
    return _dims()


def ghoul_uppercut(M):
    """The Crypt Lord bursting out of his own grave in a rising uppercut: the slab split and flung up, grave soil and
    bones erupting, his fist driving up through a burst of green soul-fire; grey-green ghoul skin, a crown of bone, a
    rotted Victorian frock coat in tatters with tarnished silver buttons, a torn shirt and cravat, long claws."""
    K = kit(glow=(150, 255, 110), glow2=(220, 255, 160), glass=(170, 255, 170))
    GLOW["GhoulUppercut"] = {"Glow": (150, 255, 110), "Glow2": (220, 255, 160), "Glass": (170, 255, 170)}
    H = rect_plinth("P", K, 5.6, 4.4, 1.5, st="limestonedk", top="granite", trim="iron", plaque="iron", title="HERE LIES THE CRYPT LORD")
    O.blob("Soil", [((x, y, H), r, (1.3, 1.1, 0.45), None, 2.0) for x, y, r in ((0, 0, 1.6), (-1.6, 0.6, 1.0), (1.5, 0.7, 1.0), (0.2, -1.3, 0.9))],
           K["rockmoss"], res=0.14, decimate=0.5, displace=(0.12, 0.3))
    for k, (x, rot) in enumerate(((-1.8, 0.8), (1.9, -0.9))):
        GE.slab(f"GraveSlab{k}", (x, 0.2, H + 1.0), 1.8, 3.2, 0.3, K["limestone"], seed=70 + k, tilt=(0.1, rot), yaw=0.1 * (k - 0.5), chip=0.1)
    text("Epitaph", "R.I.P.", K["enamel_black"], -1.95, -0.1, H + 1.2, (0.9, 0.3), depth=0.02)
    rnd = random.Random(3)
    for k in range(7):     # bones and a skull thrown up out of the soil
        p = Vector((rnd.uniform(-2.2, 2.2), rnd.uniform(-1.6, 1.0), H + rnd.uniform(0.3, 3.5)))
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        GE.sweep(f"Bone{k}", [p, p + d * 0.7], lambda t: 0.07 + 0.05 * abs(math.cos(t * math.pi)), K["bone"], sides=6, smooth=0)
        for e in (p, p + d * 0.7):
            sphere(f"BoneKnob{k}{e.z:.2f}", 0.09, tuple(e), K["bone"], seg=8, rings=4)
    O.blob("Skull", [((1.4, -1.5, H + 0.35), 0.32, (1.0, 1.1, 1.0), None, 2.0), ((1.4, -1.75, H + 0.22), 0.18, (1.0, 1.0, 0.8), None, 2.0)], K["bone"],
           res=0.04, decimate=0.5)
    set_group("Figure")
    f = figure("GhoulUppercut", (0, 0.1, H - 1.4), mats=K["skin_ghoul"], parts=("head", "rarm", "larm"), face="snarl", dark=K["dark"], glow_eyes="Glow")
    C.hair(f, K, "hair_white", "long", seed=21, length=0.7)
    C.headwear(f, mode="crown", fn=lambda: [GE.sweep(f"BoneSpike{k}", [(math.cos(a) * 0.62, math.sin(a) * 0.62, 5.1), (math.cos(a) * 0.74, math.sin(a) * 0.74, 5.6 + 0.2 * (k % 2))],
                                    lambda t: 0.08 * (1 - t) + 0.01, K["bone"], sides=5, smooth=0) for k, a in enumerate([i * 2 * math.pi / 9 for i in range(9)])] +
               [hoop("BoneBand", (0, 0, 5.1), 0.64, "Z", K["bone"], thick=0.05)])
    C.jacket(f, K, "wool_green", hem=1.4, lapel="velvet_black", shirt="linen_grey", tie="silk_black", buttons="silver", seed=51, sleeves=False, trim="silver")
    C.sleeve_pair(f, K, "wool_green", z0=2.35, seed=52, cuff=None)
    for side in (-1, 1):
        part = "rarm" if side > 0 else "larm"
        f.build(part, lambda side=side: GE.shell(f"Rag{side}", 2.3, 2.6, 0.6, 0.6, K["wool_green"], cx=side * 1.5, r=0.14, n=20, nz=3, thick=0.03, tatter=3,
                                                 seed=60 + side))
    C.claws(f, K, "bone", L=0.55)
    hp, hd = C.hand_at(f, 1)
    set_group("Glow")
    GE.flames("SoulFire", hp - hd * 0.3, 1.6, 0.35, K["glowmat"], n=6, seed=4, lean=(0, 0, 0))
    GE.embers("Mote", hp + Vector((0, 0, 0.5)), 18, 2.0, K["glowmat"], seed=5, size=0.05, rise=1.5)
    set_group("Glass")
    for k in range(4):
        GE.wisp(f"Soul{k}", (0, 0.1, 0), 1.6 + 0.35 * k, H + 0.3, hp.z + 0.5, K["glassmat"], turns=0.7 * (1 if k % 2 else -1), r0=0.2, phase=k * 1.6, flat=0.5,
                sides=8)
    set_group("Main")
    return _dims()


def court_iai_draw(M):
    """Seraphine Crane, the Crimson Court's blade, in a low iai-draw lunge across a broken terrace balustrade: the
    sabre ripped from its scabbard in one flashing crimson arc, her ponytail and coat-tails whipping back; a crimson
    velvet duelling coat with gold frogging, a black silk sash, a white lace cravat, tall boots; rose petals torn off
    the climbing rose by the cut swirl round her."""
    K = kit(glow=(255, 40, 70), glow2=(255, 170, 190))
    GLOW["CourtIaiDraw"] = {"Glow": (255, 40, 70), "Glow2": (255, 170, 190)}
    H = rect_plinth("P", K, 7.0, 4.4, 1.2, st="limestonedk", top="limestone", trim="gilt", plaque="gilt", title="SERAPHINE CRANE")
    # the balustrade along the back, one baluster sheared through and toppled
    box("RailBase", (6.6, 0.7, 0.3), (0, 1.6, H + 0.15), K["limestone"], bevel=0.04)
    for k in range(9):
        x = -3.0 + k * 0.75
        if k == 5:
            continue
        lathe(f"Baluster{k}", [(0, 0), (0.22, 0), (0.24, 0.1), (0.14, 0.3), (0.28, 0.75), (0.12, 1.25), (0.2, 1.4), (0.2, 1.5), (0, 1.5)], K["limestone"], seg=12,
              loc=(x, 1.6, H + 0.3))
    box("RailTopL", (3.6, 0.8, 0.25), (-1.4, 1.6, H + 1.92), K["limestone"], bevel=0.05)
    box("RailTopR", (1.8, 0.8, 0.25), (2.3, 1.6, H + 1.6), K["limestone"], bevel=0.05, rot=(0, 0.35, 0))
    ob = lathe("Fallen", [(0, 0), (0.22, 0), (0.24, 0.1), (0.14, 0.3), (0.28, 0.75), (0.12, 1.25), (0.2, 1.4), (0.2, 1.5), (0, 1.5)], K["limestone"], seg=12)
    ob.matrix_world = Matrix.Translation((1.2, 0.2, H + 0.25)) @ Matrix.Rotation(math.radians(80), 4, "Y") @ Matrix.Rotation(0.4, 4, "X")
    O.blob("RoseVine", O.chain([(-3.0, 1.9, H + 0.3), (-2.4, 1.9, H + 1.2), (-1.5, 1.95, H + 2.2), (-0.4, 1.95, H + 2.3)], 0.18, 0.08), K["rockmoss"], res=0.06,
           decimate=0.4, displace=(0.06, 0.1))
    rnd = random.Random(12)
    for k in range(5):
        p = (-2.8 + k * 0.6, 1.75, H + 1.0 + k * 0.25)
        sphere(f"Rose{k}", 0.16, p, K["velvet_crimson"], seg=10, rings=6, scale=(1, 1, 0.8))
    set_group("Figure")
    f = figure("CourtIaiDraw", (0.2, -0.3, H), mats=K["marble"], parts=("head", "rarm", "larm"), face="fierce", dark=K["dark"])
    f.settle(H)
    C.hair(f, K, "hair_black", "long", seed=31, length=1.4, flow=(0.4, 1, 0.5))
    C.jacket(f, K, "velvet_crimson", hem=1.75, lapel="silk_black", shirt="linen", vest="silk_black", buttons="gold", seed=61, trim="gold", cuff="silk_black")
    f.build("torso", lambda: [GE.sweep(f"Frog{k}", [(-0.5, -0.63, 2.4 + k * 0.32), (-0.15, -0.65, 2.45 + k * 0.32)], 0.025, K["gold"], sides=4, smooth=0)
                              for k in range(4)] +
            [GE.sweep(f"FrogR{k}", [(0.5, -0.63, 2.4 + k * 0.32), (0.15, -0.65, 2.45 + k * 0.32)], 0.025, K["gold"], sides=4, smooth=0) for k in range(4)] +
            [GE.ribbon(f"Cravat{k}", [(0, -0.64 - k * 0.02, 4.0 - k * 0.1), (0.02, -0.68 - k * 0.03, 3.78 - k * 0.1)], 0.3 - k * 0.04, K["linen"], up=(1, 0, 0),
                       thick=0.02, twist=0.4) for k in range(3)])
    C.belt(f, K, "silk_black", "gold", sash=None, h=0.3)
    C.trousers(f, K, "wool_black", seed=62)
    C.boots(f, K, "leather_black", h=1.3, sole="leather_black", cuff="leather_black", heel=0.12)
    C.coat_skirt(f, K, "velvet_crimson", length=2.6, z=2.1, gather=1.2, wind=(0.6, 0.8, 0.3), gap=0.35, lining="silk_black", seed=19, turb=0.5, curl=0.5)
    # the scabbard in her left hand at the hip, the drawn sabre in her right, the crimson arc of the draw
    lp, ld = C.hand_at(f, -1)
    s = _mark()
    GE.sweep("Scabbard", [(0.04 * (i / 8) ** 2, 0, 2.8 * i / 8) for i in range(9)], lambda t: 0.12 - 0.03 * t, K["leather_black"], sides=8, flat=0.4)
    cone("Chape", 0.09, 0.02, 0.28, (0.04, 0, 2.9), K["gold"], verts=8)
    hoop("Throat", (0, 0, 0.05), 0.13, "Z", K["gold"], thick=0.03)
    back = (f.at("torso", (0.4, 1.0, 1.2)) - lp).normalized()
    _xform(s, Matrix.Translation(lp) @ Vector((0, 0, 1)).rotation_difference(back).to_matrix().to_4x4() @ Matrix.Scale(S * 0.9, 4))
    C.hold(f, 1, lambda: GE.sabre("Blade", K, L=3.3, curve=0.3, glow="Glow2"), along=(0, 0, -1), push=0.15)
    hp, hd = C.hand_at(f, 1)
    set_group("Glow")
    sweep_pts = []
    c = f.at("torso", (0, 0, 2.6))
    for i in range(12):
        t = i / 11
        a = math.radians(-150 + 170 * t)
        sweep_pts.append(c + Vector((math.cos(a) * 4.2, math.sin(a) * 3.2 - 0.8, -1.0 + 0.9 * t)))
    GE.trail("DrawArc", sweep_pts, 0.05, 0.75, K["glowmat"], up=(0, 0, 1), thick=0.02)
    set_group("Main")
    for k in range(14):
        p = (rnd.uniform(-3.2, 3.4), rnd.uniform(-2.0, 1.2), H + rnd.uniform(0.6, 5.0))
        O.feather(f"Petal{k}", p, (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3)), 0.24, 0.22, K["velvet_crimson"], curl=0.3,
                  side=(rnd.uniform(-1, 1), 0.3, 1), n=4, thick=0.01)
    return _dims()



# ================================================================== the paintings: one modular grand frame

def _outline(shape, w, h, z0, n=48):
    """A canvas outline (x, z), counter-clockwise: rect, arch (lancet top), oval, round."""
    if shape == "rect":
        return [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + h), (-w / 2, z0 + h)]
    if shape in ("oval", "round"):
        return [(math.cos(a) * w / 2, z0 + h / 2 + math.sin(a) * h / 2) for a in [-math.pi / 2 + k * 2 * math.pi / n for k in range(n)]]
    hs = h - w * 0.62
    pts = [(-w / 2, z0), (w / 2, z0), (w / 2, z0 + hs)]
    for k in range(1, 12):
        t = k / 12
        a = math.pi * t
        pts.append((math.cos(a) * w / 2 * (1 - 0.1 * math.sin(a)), z0 + hs + math.sin(a) ** 0.8 * w * 0.62))
    pts.append((-w / 2, z0 + hs))
    return pts


def _resample2(pts, step):
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def moulding(name, outline, profile, mat, step=0.25):
    """A frame moulding: the 2D profile [(outward offset, depth toward -Y)] swept round the closed outline."""
    pts = _resample2(outline, step)
    n = len(pts)
    rows = []
    for off, dep in profile:
        row = []
        for i in range(n):
            a, b, c = Vector((*pts[i - 1], 0)), Vector((*pts[i], 0)), Vector((*pts[(i + 1) % n], 0))
            t = (c - a).normalized()
            nrm = Vector((t.y, -t.x, 0))
            row.append(Vector((b.x + nrm.x * off, -dep, b.y + nrm.y * off)))
        rows.append(row)
    return GE.grid_mesh(name, rows, mat, 0.0, closed=True)


PROFILES = {   # (outward offset, depth) from the sight edge outward: each a different carved section
    "ogee": [(0.0, 0.05), (0.06, 0.14), (0.16, 0.2), (0.3, 0.16), (0.42, 0.26), (0.55, 0.32), (0.68, 0.22), (0.74, 0.06), (0.74, 0.0)],
    "cushion": [(0.0, 0.04), (0.05, 0.1), (0.2, 0.3), (0.45, 0.36), (0.62, 0.24), (0.66, 0.06), (0.66, 0.0)],
    "stepped": [(0.0, 0.05), (0.08, 0.05), (0.08, 0.16), (0.28, 0.16), (0.28, 0.26), (0.5, 0.26), (0.5, 0.12), (0.62, 0.12), (0.62, 0.0)],
    "scoop": [(0.0, 0.08), (0.1, 0.24), (0.25, 0.14), (0.4, 0.12), (0.55, 0.3), (0.62, 0.2), (0.64, 0.0)],
    "thin": [(0.0, 0.05), (0.06, 0.12), (0.22, 0.16), (0.32, 0.1), (0.34, 0.0)],
}


def grand_frame(name, K, w, h, shape="rect", profile="ogee", body="gilt", inner="ebony", slip="velvet_crimson", corner=None, crest=None, gems=None,
                glow_gems=False, iron=False, light=False, z0=0.0, sconces=False, extra=None):
    """The batch's one frame builder: canvas (Canvas piece, painted image), a velvet slip, the carved moulding in the
    chosen profile and metal, an inner bead, and optional corner ornaments (rosette, skull, bat, star, leaf), a crest
    (crown, raven, wolf, moon, shield, bell, book, flame), set gems (optionally haloed in Glow), iron strapwork with
    rivets, candle sconces and a brass picture light. Wall piece: built facing -Y, back flattened to y = 0 at the end."""
    o = _outline(shape, w, h, z0)
    o = WS.ccw(o)
    B21._canvas(f"{name}Canvas", o, 0.0)
    P.CANVAS[f"{name}_Canvas"] = name
    sl = PROFILES["thin"]
    moulding(f"{name}Slip", o, [(x * 0.6, d * 0.6) for x, d in sl], K[slip])
    k_ = max(1.0, min(2.3, max(w, h) / 5.0))         # bigger canvases get proportionally heavier mouldings
    pr = [(x * k_, d * k_) for x, d in PROFILES[profile]]
    oo = [(x, z) for x, z in o]
    oo = WS.ccw(oo)
    moulding(f"{name}Moulding", oo, [(x + 0.2, d) for x, d in pr], K[body])
    moulding(f"{name}Inner", oo, [(0.0, 0.02), (0.05, 0.09), (0.12, 0.11), (0.2, 0.08), (0.2, 0.0)], K[inner])
    ow = max(x for x, _ in pr) + 0.2
    moulding(f"{name}Bead", oo, [(ow - 0.03, 0.0), (ow - 0.02, 0.07), (ow + 0.02, 0.1), (ow + 0.06, 0.06), (ow + 0.06, 0.0)], K["gold"])
    # carved bead-and-reel running round the crest of the moulding
    ridge = max(pr, key=lambda t: t[1])
    rp = _resample2(oo, 0.32 * k_)
    for i, (x, z) in enumerate(rp):
        a, c = rp[i - 1], rp[(i + 1) % len(rp)]
        tx, tz = c[0] - a[0], c[1] - a[1]
        L = math.hypot(tx, tz) or 1
        nx, nz = tz / L, -tx / L
        off = ridge[0] + 0.2
        ob = sphere(f"{name}Reel{i}", 0.07 * k_, (x + nx * off, -ridge[1] - 0.02, z + nz * off), K[body], seg=8, rings=4,
                    scale=(1.0, 0.6, 1.0) if i % 2 else (1.6, 0.5, 0.6))
        if i % 2 == 0:
            ob.rotation_euler = (0, -math.atan2(tz, tx), 0)
    # scrolled cartouches at the head and foot of rect and arched frames
    if shape in ("rect", "arch"):
        for zc_, sgn in ((z0 - ow * 0.5, -1), (z0 + h + ow * 0.5, 1)):
            if shape == "arch" and sgn > 0:
                continue
            for sx in (-1, 1):
                pts = [(sx * 0.05, -0.3, zc_), (sx * 0.45 * k_, -0.32, zc_ + sgn * 0.12 * k_), (sx * 0.75 * k_, -0.3, zc_ - sgn * 0.02), (sx * 0.62 * k_, -0.32, zc_ - sgn * 0.16 * k_),
                       (sx * 0.5 * k_, -0.32, zc_ - sgn * 0.05 * k_)]
                GE.sweep(f"{name}Scroll{sgn}{sx}", pts, lambda t: (0.07 - 0.04 * t) * k_, K[body], sides=6, smooth=2)
            sphere(f"{name}Cartouche{sgn}", 0.16 * k_, (0, -0.34, zc_), K[gems[0] if gems else body], seg=10, rings=5, scale=(1.3, 0.5, 1.0))
    box(f"{name}Back", (w + ow, 0.06, h + ow), (0, 0.04, z0 + h / 2), K["oak"], bevel=0.0) if shape == "rect" else None
    cx, cz = 0.0, z0 + h / 2
    cpos = [(-w / 2 - ow * 0.45, z0 - ow * 0.45), (w / 2 + ow * 0.45, z0 - ow * 0.45), (w / 2 + ow * 0.45, z0 + h + ow * 0.45),
            (-w / 2 - ow * 0.45, z0 + h + ow * 0.45)] if shape in ("rect", "arch") else \
        [(math.cos(a) * (w / 2 + ow * 0.6), cz + math.sin(a) * (h / 2 + ow * 0.6)) for a in (math.radians(-135), math.radians(-45), math.radians(45), math.radians(135))]
    if shape == "arch":
        cpos = cpos[:2] + [(w / 2 + ow * 0.45, z0 + h - w * 0.62), (-w / 2 - ow * 0.45, z0 + h - w * 0.62)]
    for k, (x, z) in enumerate(cpos):
        y = -0.36
        x, z = x * 1.0, z
        sc_ = k_
        if corner == "rosette":
            for j in range(8):
                a = j * math.pi / 4
                sphere(f"{name}Petal{k}{j}", 0.12, (x + math.cos(a) * 0.14, y, z + math.sin(a) * 0.14), K[body], seg=8, rings=4, scale=(1, 0.5, 0.6))
            sphere(f"{name}Rose{k}", 0.1, (x, y - 0.05, z), K[gems[0] if gems else body], seg=8, rings=4, scale=(1, 0.6, 1))
        elif corner == "skull":
            O.blob(f"{name}Skull{k}", [((x, y, z + 0.04 * sc_), 0.2 * sc_, (1.0, 0.8, 1.05), None, 2.0), ((x, y - 0.06 * sc_, z - 0.12 * sc_), 0.12 * sc_, (1.0, 0.8, 0.8), None, 2.0)],
                   K["bone"], res=0.03 * sc_, decimate=0.5)
            for sx in (-1, 1):
                sphere(f"{name}SkullEye{k}{sx}", 0.05 * sc_, (x + sx * 0.07 * sc_, y - 0.18 * sc_, z + 0.04 * sc_), K["dark"], seg=6, rings=3)
        elif corner == "bat":
            O.bat(f"{name}Bat{k}", K, (x, y, z), heading=-math.pi / 2, flap=0.1, s=1.6)
        elif corner == "star":
            for j in range(8):
                a = j * math.pi / 4
                cone(f"{name}Star{k}{j}", 0.06, 0.0, 0.32 if j % 2 == 0 else 0.18, (x + math.cos(a) * 0.12, y, z + math.sin(a) * 0.12), K[body], verts=4,
                     rot=(0, -a + math.pi / 2, 0))
        elif corner == "leaf":
            for j in range(5):
                a = math.radians(-60 + 30 * j) + (math.pi / 2 if x < 0 else -math.pi / 2) * 0 + math.atan2(z - cz, x - cx)
                O.feather(f"{name}Leaf{k}{j}", (x, y, z), (math.cos(a), -0.2, math.sin(a)), 0.45, 0.18, K[body], curl=0.3, side=(0, 1, 0), n=5, thick=0.02)
        if gems and corner != "rosette":
            sphere(f"{name}Gem{k}", 0.1, (x, y - 0.12, z), K[gems[k % len(gems)]], seg=8, rings=4, scale=(1, 0.6, 1))
            if glow_gems:
                GE.in_group("Glow", lambda x=x, z=z, k=k: hoop(f"{name}GemHalo{k}", (x, y - 0.14, z), 0.16, "Y", K["glowmat"], thick=0.02))
    if iron:
        for k, (x, z) in enumerate(cpos):
            sx, sz = (1 if x > 0 else -1), (1 if z > cz else -1)
            pts = [(x - sx * 0.9, z), (x, z), (x, z - sz * 0.9)]
            GE.sweep(f"{name}Strap{k}", [(px, -0.42, pz) for px, pz in pts], 0.05, K["iron"], sides=4, smooth=0)
            for j, (px, pz) in enumerate(pts):
                sphere(f"{name}Rivet{k}{j}", 0.05, (px, -0.47, pz), K["iron"], seg=6, rings=3)
    top = z0 + h + ow
    if crest:
        s = _mark()
        if crest == "crown":
            GE.crown(f"{name}Crown", K, (0, -0.35 * k_, top - 0.05), r=0.45 * k_, h=0.45 * k_, points=7, metal="gold", gems=gems or ("ruby",))
        elif crest == "raven":
            O.raven(f"{name}Raven", K, (0, -0.2, top + 0.35), heading=-math.pi / 2, wings=0.85, s=1.5)
        elif crest == "moon":
            tp(f"{name}Moon", [(math.cos(a) * 0.6, top + 0.55 + math.sin(a) * 0.6) for a in [k * 2 * math.pi / 24 for k in range(24)]], -0.25, 0.12, K[body])
            GE.in_group("Glow", lambda: tp(f"{name}MoonFace", [(math.cos(a) * 0.45 + 0.12, top + 0.55 + math.sin(a) * 0.45) for a in [k * 2 * math.pi / 20 for k in range(20)]],
                                            -0.33, 0.04, K["glowmat"]))
        elif crest == "shield":
            sh = [(-0.5, top + 1.0), (0.5, top + 1.0), (0.5, top + 0.45), (0.3, top + 0.15), (0, top + 0.02), (-0.3, top + 0.15), (-0.5, top + 0.45)]
            tp(f"{name}Shield", sh, -0.25, 0.1, K["velvet_crimson"])
            GE.sweep(f"{name}ShieldRim", [(x, -0.32, z) for x, z in sh + sh[:1]], 0.04, K["gold"], sides=5, smooth=0, cap=False)
            GE.sweep(f"{name}ShieldKey", [(0, -0.34, top + 0.2), (0, -0.34, top + 0.85)], 0.04, K["gold"], sides=5, smooth=0)
        elif crest == "flame":
            GE.in_group("Glow", lambda: GE.flames(f"{name}CrestFlame", (0, -0.25, top + 0.3), 0.9, 0.22, K["glowmat"], n=4, seed=2))
            lathe(f"{name}Brazier", [(0, 0), (0.3, 0), (0.42, 0.22), (0.38, 0.32), (0, 0.32)], K["iron"], seg=12, loc=(0, -0.25, top))
        elif crest == "bell":
            lathe(f"{name}Bell", [(0, 0.8), (0.12, 0.8), (0.2, 0.55), (0.42, 0.1), (0.45, 0.0), (0, 0.0)], K["bronze"], seg=16, loc=(0, -0.25, top))
        elif crest == "book":
            s2 = _mark()
            GE.book(f"{name}Book", K, w=0.9, d=0.6, open_=True, cover="leather_oxblood")
            _xform(s2, Matrix.Translation((0, -0.3, top + 0.1)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
        elif crest == "wolf":
            O.wolf(f"{name}Wolf", K[body], Matrix.Translation((0, -0.3, top - 0.1)) @ Matrix.Scale(0.32, 4), howl=True, rear=0.2, fur=0.0, res=0.12, decimate=0.5)
        elif crest == "trophy":
            lathe(f"{name}Cup", [(0, 0), (0.3, 0), (0.12, 0.12), (0.08, 0.4), (0.4, 0.6), (0.45, 1.05), (0.4, 1.05), (0.06, 0.62), (0, 0.62)], K["gold"], seg=16,
                  loc=(0, -0.25, top))
    if sconces:
        for sx in (-1, 1):
            x = sx * (w / 2 + ow + 0.35)
            tube(f"{name}SconceArm{sx}", [(x - sx * 0.3, -0.05, z0 + h * 0.4), (x, -0.4, z0 + h * 0.42), (x, -0.45, z0 + h * 0.5)], 0.04, K["iron"])
            lathe(f"{name}SconcePan{sx}", [(0, 0), (0.18, 0), (0.2, 0.05), (0, 0.06)], K["brass"], seg=12, loc=(x, -0.45, z0 + h * 0.5))
            cyl(f"{name}SconceCandle{sx}", 0.06, 0.4, (x, -0.45, z0 + h * 0.5 + 0.25), K["wax"], verts=10)
            GE.in_group("Glow2", lambda x=x, sx=sx: GE.flames(f"{name}SconceFlame{sx}", (x, -0.45, z0 + h * 0.5 + 0.45), 0.22, 0.05, K["glow2mat"], n=1))
    if light:
        tube(f"{name}LampArm", [(0, -0.1, top - 0.1), (0, -0.6, top + 0.25), (0, -0.95, top + 0.2)], 0.035, K["brass"])
        s = _mark()
        lathe(f"{name}LampHood", [(0, 0), (0.1, 0), (0.16, -0.25), (0.14, -0.25), (0, -0.05)], K["brass"], seg=12)
        _xform(s, Matrix.Translation((0, -0.95, top + 0.2)) @ Matrix.Rotation(math.radians(70), 4, "X"))
        GE.in_group("Glow2", lambda: cyl(f"{name}LampTube", 0.04, w * 0.5, (0, -0.95, top + 0.12), K["glow2mat"], rot=(0, math.pi / 2, 0), verts=8))
    if extra:
        extra()


def _wall():
    """Flatten the piece's back onto y = 0 (the wall), keeping x and z."""
    bpy.context.view_layer.update()
    ymax = max((ob.matrix_world @ Vector(c)).y for ob in P.PARTS for c in ob.bound_box)
    for ob in P.PARTS:
        ob.matrix_world = Matrix.Translation((0, -ymax, 0)) @ ob.matrix_world


def _painting(name, frame_kw, glow=(255, 200, 120), glow2=(255, 170, 80), desc=None):
    import showpiece44_scenes as SCN
    def build(M):
        K = kit(glow=glow, glow2=glow2)
        GLOW[name] = {"Glow": glow, "Glow2": glow2}
        w, h = SCN.CANVAS[name]
        grand_frame(name, K, w, h, **frame_kw)
        _wall()
        return _dims()
    build.__doc__ = desc
    return build


PAINTINGS = {
    "PaintingBellTowerStorm": dict(frame_kw=dict(shape="arch", profile="stepped", body="iron", inner="ebony", slip="velvet_blue", corner="star", gems=("sapphire",),
                                                 glow_gems=True, iron=True, crest="bell"), glow=(150, 200, 255),
                                   desc="The Revenant of the bell tower in a thunderstorm: a lancet-arched frame of blackened iron with stepped mouldings, iron straps "
                                        "and rivets, star bosses set with sapphires haloed in lightning-blue Glow, a bronze bell on the crest."),
    "PaintingFloodedCrypt": dict(frame_kw=dict(shape="rect", profile="scoop", body="bone", inner="ebony", slip="velvet_black", corner="skull", gems=("emerald",),
                                               glow_gems=True, crest="shield"), glow=(140, 255, 120),
                                 desc="The Crypt Lord wading out of the flooded crypt: a carved bone frame with a scooped section, skulls at the corners with emerald "
                                      "eyes haloed in grave-green Glow, a crimson shield and gold key on the crest."),
    "PaintingBurningLibrary": dict(frame_kw=dict(shape="rect", profile="ogee", body="gilt", inner="ebony", slip="velvet_crimson", corner="leaf", gems=("ruby",),
                                                 crest="flame", light=True), glow=(255, 130, 40), glow2=(255, 220, 160),
                                   desc="Ezra Vale escaping the burning library: a broad carved gilt ogee frame with acanthus corners and rubies, a flaming iron "
                                        "brazier on the crest (Glow) and a brass picture light (Glow2)."),
    "PaintingMoonlitRooftop": dict(frame_kw=dict(shape="oval", profile="cushion", body="enamel_black", inner="silver", slip="silk_crimson", corner="bat",
                                                 gems=("moonstone",), glow_gems=True, crest="moon"), glow=(215, 225, 255),
                                   desc="A Court vampire leaping the rooftops: an oval black-lacquer cushion frame with a silver slip, sculpted bats at four points, "
                                        "moonstones haloed in moonlight Glow and a crescent moon crest."),
    "PaintingChoirLoft": dict(frame_kw=dict(shape="arch", profile="ogee", body="gilt", inner="ebony", slip="velvet_blue", corner="rosette", gems=("amethyst",),
                                            crest="crown", sconces=True), glow=(255, 236, 190), glow2=(255, 170, 80),
                              desc="The choir soloist in the loft: a gothic-arched gilt frame with rosettes and amethysts, a gold crown crest and two iron candle "
                                   "sconces (Glow2 flames)."),
    "PaintingDormCorridor": dict(frame_kw=dict(shape="rect", profile="stepped", body="oak", inner="brass", slip="wool_green", corner=None, gems=None, crest=None,
                                               light=True), glow2=(255, 200, 130),
                                 desc="Pip Larkin in the dorm corridor at 3 am: a plain stepped dark-oak frame with a brass slip and a brass picture light (Glow2), "
                                      "as it hangs in the Ordinary's common room."),
    "PaintingFrozenLake": dict(frame_kw=dict(shape="rect", profile="cushion", body="silver", inner="enamel_black", slip="velvet_blue", corner="star",
                                             gems=("moonstone",), glow_gems=True, crest="wolf"), glow=(190, 220, 255),
                               desc="The Bloodmoon werewolf on the frozen lake: a frosted silver cushion frame with star bosses and moonstones haloed in ice-blue "
                                    "Glow, a silver wolf howling on the crest."),
    "PaintingHeadmasterStudy": dict(frame_kw=dict(shape="rect", profile="ogee", body="gilt", inner="velvet_crimson", slip="velvet_crimson", corner="rosette",
                                                  gems=("ruby",), crest="shield", light=True, iron=False), glow2=(255, 210, 140),
                                    desc="The Headmaster in his study: the heaviest gilt ogee frame with a crimson velvet mount, rosettes with rubies, the school shield "
                                         "on the crest and a brass picture light (Glow2)."),
    "PaintingGymMidnight": dict(frame_kw=dict(shape="rect", profile="stepped", body="oak", inner="gold", slip="knit_crimson", corner="star", gems=("ruby",),
                                              crest="trophy"), glow=(255, 220, 150),
                                desc="Captain Thorne and the ghost team at midnight: a varsity oak frame with a gold slip, crimson knit mount, gold stars with "
                                     "rubies and a gold trophy cup crest."),
    "PaintingInkArchive": dict(frame_kw=dict(shape="round", profile="scoop", body="ebony", inner="silver", slip="velvet_violet", corner="leaf", gems=("amethyst",),
                                             glow_gems=True, crest="book"), glow=(185, 90, 255),
                               desc="Wren Ashby in the ink-flooded archive: a round ebony tondo frame with a scooped section, carved leaves, amethysts haloed in "
                                    "violet Glow and an open book on the crest."),
    "MuralBloodMoonCourtyard": dict(frame_kw=dict(shape="rect", profile="ogee", body="gilt", inner="ebony", slip="velvet_crimson", corner="skull", gems=("ruby",),
                                                  glow_gems=True, iron=True, crest="crown", sconces=True), glow=(255, 40, 40), glow2=(255, 170, 80),
                                    desc="The mural of the Night of the Blood Moon (set-piece, 14 x 7.9): a grand gilt ogee frame strapped in iron, skull corners "
                                         "with rubies haloed in blood-red Glow, a jewelled crown crest and two candle sconces."),
}
for _n, _kw in PAINTINGS.items():
    globals()["paint_" + _n] = _painting(_n, **_kw)



def twin_rivals_duel(M):
    """Set-piece: the twin rivals, Cassius Vale of the Vigil and Corvin Crane of the Crimson Court, duelling on the
    broken landing of the bell-tower stair: the Vigil twin lunging up the steps with a sabre burning ghost-blue, the
    Court twin leaning back on the step above in a high parry with a sabre burning crimson; where the blades cross a
    knot of lightning bursts. Navy greatcoat against crimson velvet, both coats flaring."""
    K = kit(glow=(120, 190, 255), glow2=(255, 50, 70))
    GLOW["TwinRivalsDuel"] = {"Glow": (120, 190, 255), "Glow2": (255, 50, 70)}
    box("Foot", (11.5, 5.4, 0.45), (0, 0, 0.225), K["limestonedk"], bevel=0.06)
    box("Landing", (6.0, 5.0, 0.6), (-2.6, 0, 0.75), K["limestone"], bevel=0.08)
    for k in range(3):
        box(f"Step{k}", (1.4, 5.0, 0.6), (0.9 + k * 1.4, 0, 0.75 + (k + 1) * 0.5), K["limestone" if k % 2 else "limestonedk"], bevel=0.08)
    box("UpperLanding", (2.2, 5.0, 0.6), (5.2, 0, 2.75), K["limestone"], bevel=0.08)
    box("UpperMass", (6.4, 5.0, 2.3), (3.5, 0, 1.2), K["limestonedk"], bevel=0.04)
    GE.rubble("Rub", (-3.6, -1.8, 1.05), 7, 1.1, 0.3, K["rock"], seed=5)
    for k, x in enumerate((-5.2, -3.4)):
        lathe(f"Baluster{k}", [(0, 0), (0.22, 0), (0.24, 0.1), (0.14, 0.3), (0.28, 0.75), (0.12, 1.25), (0.2, 1.4), (0.2, 1.5), (0, 1.5)], K["limestone"], seg=12,
              loc=(x, 2.2, 1.05))
    box("RailStub", (2.4, 0.6, 0.25), (-4.3, 2.2, 2.65), K["limestone"], bevel=0.04)
    set_group("Figure")
    a = figure("DuelVigil", (-2.4, 0.0, 1.05), mats=K["marblewarm"], parts=("head", "rarm", "larm"), face="fierce", dark=K["dark"])
    a.settle(1.05)
    C.hair(a, K, "hair_brown", "swept", seed=21, flow=(-0.8, 0.2, 0.3))
    C.jacket(a, K, "wool_navy", hem=1.8, lapel="wool_black", shirt="linen", tie="silk_black", buttons="silver", seed=91, trim="silver",
             crest=("wool_navy", "silver"), cuff="wool_black")
    C.trousers(a, K, "wool_grey", seed=92)
    C.boots(a, K, "leather_black", h=1.1, sole="rubber", cuff="leather_black")
    C.coat_skirt(a, K, "wool_navy", length=2.6, z=2.15, gather=1.2, wind=(-0.5, 0.2, 0.15), gap=0.35, lining="wool_black", seed=31, turb=0.5, curl=0.3, floor=1.05)
    C.hold(a, 1, lambda: GE.sabre("SabreA", K, L=3.0, curve=0.2, glow="Glow"), along=(0, 0, -1), push=0.15)
    pa, da = C.hand_at(a, 1)
    set_group("Figure2")
    b = figure("DuelCourt", (3.6, 0.0, 2.25), mats=K["marble"], parts=("head", "rarm", "larm"), face="snarl", dark=K["dark"])
    b.settle(2.25)
    C.hair(b, K, "hair_black", "long", seed=22, length=1.0, flow=(0.8, 0.3, 0.3))
    C.jacket(b, K, "velvet_crimson", hem=1.75, lapel="silk_black", shirt="linen", vest="silk_black", buttons="gold", seed=93, trim="gold", cuff="silk_black")
    C.trousers(b, K, "wool_black", seed=94)
    C.boots(b, K, "leather_black", h=1.3, sole="leather_black", heel=0.12)
    C.coat_skirt(b, K, "velvet_crimson", length=2.6, z=2.1, gather=1.2, wind=(0.8, 0.3, 0.3), gap=0.35, lining="silk_black", seed=32, turb=0.5, curl=0.4)
    C.hold(b, 1, lambda: GE.sabre("SabreB", K, L=3.0, curve=0.25, glow="Glow2"), along=(0, 0, -1), push=0.15)
    pb, db = C.hand_at(b, 1)
    set_group("Glow")
    from mathutils.geometry import intersect_line_line
    ia = intersect_line_line(pa, pa + da * 6, pb, pb + db * 6)
    cross = (ia[0] + ia[1]) / 2 if ia else (pa + pb) / 2
    for k in range(6):
        rnd = random.Random(k)
        GE.lightning(f"Arc{k}", cross, cross + Vector((rnd.uniform(-2.2, 2.2), rnd.uniform(-1.4, 1.0), rnd.uniform(-1.5, 2.2))), K["glowmat"], seed=k, r=0.04,
                     branches=1)
    GE.embers("Spark", cross, 22, 1.8, K["glowmat"], seed=3, size=0.05, rise=0.6)
    set_group("Glow2")
    GE.embers("SparkB", cross, 14, 1.6, K["glow2mat"], seed=9, size=0.05, rise=0.6)
    set_group("Main")
    return _dims()


def back_to_back(M):
    """Set-piece: back to back in the crypt circle, the human Slayer Mara Thorne and Father Anselm of the Exorcists hold
    off the ghouls clawing up through the floor: she aims a heavy crossbow one way with her long leather coat flaring,
    he holds out a burning reliquary the other way, his cassock and stole whipping; grey ghoul hands burst from the
    cracked flagstones round them inside a ring of holy fire."""
    K = kit(glow=(255, 200, 110), glow2=(150, 255, 120))
    GLOW["BackToBackStandoff"] = {"Glow": (255, 200, 110), "Glow2": (150, 255, 120)}
    H = round_plinth("P", K, r=4.0, h=1.0, st="slate", band="blackmarble", trim="iron", seg=32, plaque="iron", title="THE LAST WATCH")
    for i in range(8):
        GE.slab(f"Flag{i}", (math.cos(i * 0.785) * 2.6, math.sin(i * 0.785) * 2.6, H + 0.06), 1.8, 1.4, 0.12, K["limestonedk"], seed=80 + i, yaw=i * 0.785,
                tilt=(0.05 * math.sin(i), 0.05 * math.cos(i)), chip=0.2)
    set_group("Glow")
    GE.rune_circle("Ring", (0, 0, H + 0.14), 3.6, K["glowmat"], n=16, seed=44, star=0, depth=0.04, inner=0.9)
    for k in range(10):
        a = k * 2 * math.pi / 10
        GE.flames(f"Holy{k}", (math.cos(a) * 3.6, math.sin(a) * 3.6, H + 0.14), 0.55, 0.12, K["glowmat"], n=2, seed=k)
    set_group("Main")
    # ghoul hands clawing up through the floor
    for k, a in enumerate((0.5, 1.6, 2.6, 3.7, 4.6, 5.6)):
        base = Vector((math.cos(a) * 3.0, math.sin(a) * 3.0, H + 0.05))
        up = Vector((-math.cos(a) * 0.4, -math.sin(a) * 0.4, 1)).normalized()
        arm = [base, base + up * 0.7, base + up * 1.3 + Vector((0, 0, 0.1))]
        O.blob(f"GhoulArm{k}", O.chain(arm, 0.2, 0.17) + [(tuple(arm[-1] + up * 0.15), 0.22, (1.0, 0.7, 1.1), None, 2.0)], K["skin_ghoul"], res=0.05, decimate=0.5)
        for j in range(4):
            side = Vector((-math.sin(a), math.cos(a), 0)) * ((j - 1.5) * 0.09)
            tip = arm[-1] + up * 0.28 + side
            GE.sweep(f"GhoulFinger{k}{j}", [tuple(arm[-1] + up * 0.1 + side), tuple(tip), tuple(tip + up * 0.18 - Vector((math.cos(a), math.sin(a), 0)) * 0.12)],
                     lambda t: 0.05 * (1 - t) + 0.008, K["skin_ghoul"], sides=5, smooth=1)
        GE.rubble(f"Burst{k}", base, 4, 0.5, 0.18, K["limestonedk"], seed=k)
    set_group("Figure")
    a = figure("StandHunter", (0.0, -1.15, H + 0.15), mats=K["marblewarm"], parts=("head", "rarm", "larm"), face="fierce", dark=K["dark"])
    a.settle(H + 0.15)
    C.hair(a, K, "hair_red", "long", seed=31, length=1.1, flow=(-0.6, 0.4, 0.4))
    C.jacket(a, K, "leather_brown", hem=1.9, lapel="leather_brown", shirt="linen", buttons="brass", seed=95, trim="brass", cuff="leather_brown")
    C.trousers(a, K, "wool_black", seed=96)
    C.boots(a, K, "leather_black", h=1.2, sole="rubber", buckles="brass")
    C.belt(a, K, "leather_black", "brass", sash=None)
    C.coat_skirt(a, K, "leather_brown", length=3.0, z=2.15, gather=1.2, wind=(-0.7, -0.2, 0.25), gap=0.35, seed=33, turb=0.5, curl=0.3)
    def crossbow():
        box("Stock", (0.18, 0.18, 1.6), (0, 0, 0.5), K["oak"], bevel=0.04)
        GE.sweep("Prod", [(-0.9, 0, 1.25), (-0.4, -0.05, 1.18), (0, -0.08, 1.15), (0.4, -0.05, 1.18), (0.9, 0, 1.25)], 0.05, K["iron"], sides=6)
        tube("String", [(-0.9, 0, 1.25), (0, 0, 0.8), (0.9, 0, 1.25)], 0.012, K["linen"], poly=True)
        tube("Bolt", [(0, 0, 0.8), (0, 0, 1.7)], 0.025, K["silver"], poly=True)
        cone("BoltHead", 0.06, 0.0, 0.18, (0, 0, 1.78), K["silver"], verts=4)
    C.hold(a, 1, crossbow, along=(0, 0, -1), push=0.15)
    set_group("Figure2")
    b = figure("StandPriest", (0.0, 1.15, H + 0.15), mats=K["marble"], parts=("head", "rarm", "larm"), face="stern", dark=K["dark"])
    b.settle(H + 0.15)
    C.hair(b, K, "hair_white", "crop", seed=32)
    b.build("torso", lambda: [GE.shell("Cassock", 1.6, 4.04, 1.07, 0.575, K["wool_black"], r=0.13, nz=8, thick=0.035),
                              GE.shell("ClericalCollar", 3.86, 4.0, 0.62, 0.5, K["linen"], r=0.25, nz=1, thick=0.03),
                              GE.ribbon("StoleL", [(-0.35, -0.66, 4.05), (-0.32, -0.7, 2.6), (-0.32, -0.72, 1.5)], 0.22, K["silk_crimson"], up=(1, 0, 0), thick=0.03),
                              GE.ribbon("StoleR", [(0.35, -0.66, 4.05), (0.32, -0.7, 2.6), (0.32, -0.72, 1.5)], 0.22, K["silk_crimson"], up=(1, 0, 0), thick=0.03)])
    C.sleeve_pair(b, K, "wool_black", bell=1.15, cuff="silk_ivory")
    C.coat_skirt(b, K, "wool_black", length=2.3, z=2.0, gather=1.2, wind=(0.7, 0.3, 0.25), gap=0.0, seed=34, turb=0.5)
    C.boots(b, K, "leather_black", h=0.5, sole="leather_black")
    def reliquary():
        tube("RelPole", [(0, 0, -0.2), (0, 0, 1.2)], 0.04, K["gold"], poly=True)
        lathe("RelCase", [(0, 1.2), (0.25, 1.25), (0.3, 1.5), (0.25, 1.75), (0.1, 1.85), (0, 1.9)], K["gold"], seg=8)
        GE.in_group("Glow", lambda: GE.flames("RelFire", (0, 0, 1.9), 0.6, 0.14, K["glowmat"], n=3, seed=5))
        GE.sweep("RelCrossV", [(0, 0, 2.6), (0, 0, 3.2)], 0.05, K["gold"], sides=5, smooth=0)
        GE.sweep("RelCrossH", [(-0.2, 0, 3.0), (0.2, 0, 3.0)], 0.05, K["gold"], sides=5, smooth=0)
    rp, _ = C.hand_at(b, -1)
    s = _mark()
    reliquary()
    _xform(s, Matrix.Translation(rp + Vector((0, 0, -0.35))) @ Matrix.Scale(S * 0.85, 4))
    set_group("Main")
    return _dims()


BUILDERS = {
    "TwinRivalsDuel": twin_rivals_duel,
    "BackToBackStandoff": back_to_back,
    "PaintingBellTowerStorm": paint_PaintingBellTowerStorm,
    "PaintingFloodedCrypt": paint_PaintingFloodedCrypt,
    "PaintingBurningLibrary": paint_PaintingBurningLibrary,
    "PaintingMoonlitRooftop": paint_PaintingMoonlitRooftop,
    "PaintingChoirLoft": paint_PaintingChoirLoft,
    "PaintingDormCorridor": paint_PaintingDormCorridor,
    "PaintingFrozenLake": paint_PaintingFrozenLake,
    "PaintingHeadmasterStudy": paint_PaintingHeadmasterStudy,
    "PaintingGymMidnight": paint_PaintingGymMidnight,
    "PaintingInkArchive": paint_PaintingInkArchive,
    "MuralBloodMoonCourtyard": paint_MuralBloodMoonCourtyard,
    "CourtDuchessThrone": court_duchess_throne,
    "ReaperGuard": reaper_guard,
    "PackAlphaLanding": pack_alpha_landing,
    "FounderRavens": founder_ravens,
    "ExorcistSigil": exorcist_sigil,
    "GhoulUppercut": ghoul_uppercut,
    "CourtIaiDraw": court_iai_draw,
    "ChoirConductor": choir_conductor,
    "InkScribeTendrils": ink_scribe,
    "DelinquentGlare": delinquent_glare,
    "AthleteSpinKick": athlete_spin_kick,
    "WerewolfTurning": werewolf_turning,
    "VigilCaptainLantern": vigil_captain,
    "VampireLordRising": vampire_lord_rising,
}

def _finished(fn):
    """Run a builder, then the layering pass (showpiece44_chars.finish) on every figure it made."""
    def w(M):
        R.FIGS.clear()
        d = fn(M)
        figs = list(R.FIGS)
        for i, f in enumerate(figs):
            C.finish(f, figs[i + 1].start if i + 1 < len(figs) else None)
        return d
    w.__doc__ = fn.__doc__
    return w


BUILDERS = {k: _finished(v) for k, v in BUILDERS.items()}
P.BUILD.update(BUILDERS)


# ------------------------------------------------------------------ preview with the real glow colours

def preview(objs, name, dims, suffix=""):
    """nh_props.preview, but the Glow / Glow2 / Glass pieces show in their template colours, with a moody three-light
    rig and a dark floor, and a second, closer camera on the figure (<name>_close.png)."""
    sc = bpy.context.scene
    cols = GLOW.get(name, {})
    for ob in objs:
        suf = ob.name.rsplit("_", 1)[-1] if "_" in ob.name else ""
        if suf not in ("Glow", "Glow2", "Glass"):
            continue
        rgb = tuple(c / 255 for c in cols.get(suf, (255, 160, 80) if suf != "Glass" else (220, 230, 255)))
        m = bpy.data.materials.new(f"Preview{suf}")
        m.use_nodes = True
        bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        if suf == "Glass":
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Roughness"].default_value = 0.15
            bs.inputs["Transmission Weight"].default_value = 0.85
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 0.6
            bs.inputs["Alpha"].default_value = 0.55
        else:
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 7.0
        ob.data.materials.clear()
        ob.data.materials.append(m)
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 900, 1100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.032, 1)
    bpy.context.view_layer.update()
    lo = [min((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    hi = [max((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    ctr = Vector([(a + b) / 2 for a, b in zip(lo, hi)])
    size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    zc = ctr.z

    def light(kind, loc, energy, color, s=2.0):
        L = bpy.data.lights.new(kind, kind)
        L.energy = energy
        L.color = color
        if kind == "AREA":
            L.size = s
        o = bpy.data.objects.new(kind, L)
        o.location = loc
        bpy.context.collection.objects.link(o)
        o.rotation_euler = (Vector((0, 0, zc)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    light("AREA", (size * 0.9, -size * 1.2, size * 1.2), 520 * size, (1.0, 0.85, 0.7), s=size * 0.8)
    light("AREA", (-size * 1.3, -size * 0.5, size * 0.6), 140 * size, (0.5, 0.55, 0.95), s=size)
    light("AREA", (-size * 0.3, size * 1.4, size * 1.1), 420 * size, (0.95, 0.35, 0.4), s=size)
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(0, 0, 0))
    fl = bpy.context.active_object
    fm = P.material("Floor44", "NH_Slate", tint=(0.2, 0.2, 0.22), scale=0.15)
    fl.data.materials.append(fm)
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    bpy.context.collection.objects.link(co)
    sc.collection.objects.link(co) if co.name not in sc.collection.objects else None
    d = size * 1.45
    co.location = ctr + Vector((d * 0.42, -d, size * 0.12))
    co.rotation_euler = (ctr - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}{suffix}.png")
    bpy.ops.render.render(write_still=True)


def _pose_lab(M, names=None):
    """Every pose in showpiece44_poses on a bare rig, in a row, for checking silhouettes (not a prop)."""
    import showpiece44_poses as PO
    K = kit()
    names = names or list(PO.POSES)
    for k, n in enumerate(names):
        yaw, pose = PO.POSES[n]
        x = (k % 5) * 9.0
        y = (k // 5) * 12.0
        f = R.Fig(base=(x, y, 0), scale=S, yaw=math.radians(yaw), pose=pose, mats=K["marble"], face="fierce", dark=K["dark"])
        f.settle(0)
    return _dims()


P.BUILD["_PoseLab"] = _pose_lab
