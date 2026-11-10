"""Props batch 44 (the showpiece kit): the painting scenes. Each painting is a lit Cycles scene of fully clothed, posed
R6 characters (the owner's rig, the batch's modelled clothing and PBR materials, their effects glowing) in a setting
of its own, rendered at the canvas's aspect (long side 2048) and then painted over by showpiece44_canvas.py.

  blender --background --factory-startup --python E:/NH-Work/props44/scenes44.py -- <Painting> [--samples 96] [--preview]

No two scenes share a kind of room: a bell tower in a storm, a flooded crypt, a burning library, a moonlit rooftop,
the chapel choir loft, the dorm corridor at 3 am, a frozen lake, the Headmaster's study, the gym at midnight, the
ink-flooded archive, and the blood-moon courtyard for the mural.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform
import nh_props_batch20 as B20
import window_shapes as WS
import showpiece44_mats as MT
import showpiece44_geo as GE
import showpiece44_chars as C
import showpiece44_rig as R
import showpiece44_organic as O

S = 1.6
# canvas sizes (studs): the image has the same aspect, long side 2048
CANVAS = {
    "PaintingBellTowerStorm": (4.0, 6.0), "PaintingFloodedCrypt": (6.4, 4.0), "PaintingBurningLibrary": (7.2, 4.05),
    "PaintingMoonlitRooftop": (4.2, 5.6), "PaintingChoirLoft": (4.4, 6.2), "PaintingDormCorridor": (3.6, 5.0),
    "PaintingFrozenLake": (7.2, 4.05), "PaintingHeadmasterStudy": (5.0, 6.4), "PaintingGymMidnight": (6.4, 4.0),
    "PaintingInkArchive": (5.0, 5.0), "MuralBloodMoonCourtyard": (14.0, 7.875),
}
# each painting figure's own pose: (yaw degrees, pose); none repeats a statue's
POSES = {
    "Wraith": (15, {"rshoulder": (-6, -172, 0), "relbow": (0, -6, 0), "lshoulder": (-34, 138, 0), "lelbow": (-30, 0, 0), "rhip": (-34, 0, 0),
                    "rknee": (64, 0, 0), "lhip": (-8, 0, 0), "lknee": (28, 0, 0), "neck": (14, 0, 24), "waist": (-6, 8, 0), "lift": 0.0}),
    "Ghoul": (-20, {"waist": (22, 0, 12), "neck": (-22, 0, -12), "rshoulder": (-72, -12, 0), "relbow": (-22, 0, 0), "lshoulder": (-48, 18, 0),
                    "lelbow": (-44, 0, 0), "rhip": (-30, 0, 0), "rknee": (34, 0, 0), "lhip": (14, 0, 0), "lknee": (20, 0, 0)}),
    "Scholar": (-38, {"waist": (14, 0, 12), "neck": (0, 0, 44), "rshoulder": (44, -14, 0), "relbow": (-30, 0, 0), "lshoulder": (-18, 12, 0),
                      "lelbow": (-70, 0, 0), "rhip": (-52, 0, 0), "rknee": (72, 0, 0), "lhip": (32, 0, 0), "lknee": (58, 0, 0)}),
    "VampLeap": (24, {"waist": (-14, 0, 0), "neck": (-12, 0, 20), "rshoulder": (-8, -122, 0), "relbow": (0, -16, 0), "lshoulder": (-6, 112, 0),
                       "lelbow": (0, 18, 0), "rhip": (-64, 0, 0), "rknee": (92, 0, 0), "lhip": (30, 10, 0), "lknee": (44, 0, 0)}),
    "ChoirChild": (8, {"neck": (-30, 0, -6), "rshoulder": (-50, 0, -26), "relbow": (-72, 0, 0), "lshoulder": (-50, 0, 26), "lelbow": (-72, 0, 0),
                       "waist": (-4, 0, 0)}),
    "Pip": (14, {"waist": (-16, 0, 6), "neck": (6, 0, -10), "rshoulder": (-76, -10, 0), "relbow": (-18, 0, 0), "lshoulder": (-112, 30, 0),
                 "lelbow": (-92, 0, 0), "rhip": (14, 0, 0), "lhip": (-26, 0, 0), "lknee": (22, 0, 0)}),
    "GhostGirl": (0, {"neck": (16, 0, 0), "rshoulder": (0, -12, 0), "lshoulder": (0, 12, 0), "lift": 0.5}),
    "Werewolf": (24, {"root": (10, 0, 0), "waist": (12, 0, 0), "neck": (-56, 0, 0), "rshoulder": (24, -34, 0), "relbow": (-30, 0, 0),
                      "lshoulder": (20, 38, 0), "lelbow": (-34, 0, 0), "rhip": (-40, -10, 0), "rknee": (70, 0, 0), "lhip": (20, 10, 0), "lknee": (60, 0, 0)}),
    "Headmaster": (0, {"neck": (10, 0, 0), "rhip": (-90, 0, 0), "rknee": (90, 0, 0), "lhip": (-90, 0, 0), "lknee": (90, 0, 0),
                       "rshoulder": (-62, 0, -32), "relbow": (-76, 0, 0), "lshoulder": (-62, 0, 32), "lelbow": (-76, 0, 0)}),
    "Captain": (18, {"neck": (0, 0, -32), "rshoulder": (10, -30, 0), "relbow": (-100, 0, 0), "lshoulder": (-8, 30, 0), "lelbow": (-24, 0, 0),
                     "rhip": (-8, -6, 0), "lhip": (8, 6, 0), "waist": (0, 0, -10)}),
    "GhostA": (-24, {"rshoulder": (0, -20, 0), "lshoulder": (0, 20, 0), "neck": (10, 0, 0)}),
    "GhostB": (12, {"rshoulder": (-30, 0, 0), "relbow": (-60, 0, 0), "lshoulder": (0, 18, 0), "neck": (0, 0, 20)}),
    "GhostC": (-6, {"rshoulder": (0, -150, 0), "lshoulder": (0, 30, 0), "neck": (-10, 0, 0)}),
    "InkGirl": (-12, {"neck": (-16, 0, 16), "rshoulder": (-30, -132, 0), "relbow": (0, -30, 0), "lshoulder": (-62, 42, 0), "lelbow": (-32, 0, 0),
                      "rhip": (-18, -18, 0), "rknee": (16, 0, 0), "lhip": (14, 18, 0), "lknee": (18, 0, 0), "waist": (-8, 0, -10)}),
    # the mural's cast
    "MuralVigil": (20, {"rshoulder": (-20, -140, 0), "relbow": (0, -10, 0), "lshoulder": (10, 30, 0), "rhip": (-30, 0, 0), "rknee": (30, 0, 0),
                        "neck": (-20, 0, 0)}),
    "MuralCourt": (-25, {"rshoulder": (-80, -10, 0), "relbow": (0, 0, 0), "lshoulder": (20, 40, 0), "lelbow": (-40, 0, 0), "rhip": (-40, 0, 0),
                         "rknee": (50, 0, 0), "lhip": (30, 0, 0), "waist": (14, 0, 0)}),
    "MuralPack": (30, {"waist": (24, 0, 0), "neck": (-36, 0, 0), "rshoulder": (20, -50, 0), "lshoulder": (20, 50, 0), "rhip": (-30, -14, 0),
                       "rknee": (50, 0, 0), "lhip": (24, 14, 0), "lknee": (40, 0, 0)}),
    "MuralChoir": (-10, {"rshoulder": (-40, 0, -30), "relbow": (-80, 0, 0), "lshoulder": (-40, 0, 30), "lelbow": (-80, 0, 0), "neck": (-26, 0, 0)}),
    "MuralAthlete": (40, {"rshoulder": (-160, -10, 0), "lshoulder": (30, 30, 0), "lelbow": (-50, 0, 0), "rhip": (-60, 0, 0), "rknee": (80, 0, 0),
                          "lhip": (30, 0, 0), "waist": (-10, 0, 0)}),
    "MuralInk": (-35, {"rshoulder": (-60, -50, 0), "relbow": (-20, 0, 0), "lshoulder": (0, 80, 0), "neck": (0, 0, -20), "rhip": (-20, 0, 0),
                       "lhip": (10, 0, 0)}),
    "MuralKing": (0, {"lift": 2.2, "rshoulder": (-10, -110, 0), "relbow": (0, -20, 0), "lshoulder": (-10, 110, 0), "lelbow": (0, 20, 0),
                      "neck": (20, 0, 0)}),
}

FIT = {"MuralBloodMoonCourtyard": 1.15, "PaintingFrozenLake": 1.6, "PaintingBurningLibrary": 1.5, "PaintingGymMidnight": 1.25,
       "PaintingHeadmasterStudy": 1.6, "PaintingInkArchive": 1.25}     # framing margin per scene
KEY = {"PaintingDormCorridor": 1.2, "PaintingMoonlitRooftop": 1.4, "PaintingFrozenLake": 1.0, "PaintingBurningLibrary": 0.6}
GLOWC = {}       # per scene: {"Glow": rgb, "Glow2": rgb, "Glass": rgb}


def kit():
    MT.clear()
    K = MT.kit()
    K["glowmat"] = MT.glow_mat((1, 0.5, 0.2))
    K["glow2mat"] = MT.glow_mat((0.5, 0.7, 1))
    K["glassmat"] = MT.glass_mat((0.8, 0.9, 1))
    return K


def fig(key, base, K, skin, face="stern", parts=("head", "rarm", "larm"), glow_eyes=None, scale=S):
    yaw, pose = POSES[key]
    return R.Fig(base=base, scale=scale, yaw=math.radians(yaw), pose=pose, mats=K[skin], parts=parts, face=face, dark=K["dark"], glow_eyes=glow_eyes)


def tp(name, pts, y, depth, mat):
    return B20.tprism(name, WS.ccw(pts), y, depth, mat)


# ------------------------------------------------------------------ the environment kit

def slab_wall(name, x0, x1, y, z0, z1, mat, thick=0.6):
    return box(name, (x1 - x0, thick, z1 - z0), ((x0 + x1) / 2, y, (z0 + z1) / 2), mat, bevel=0.02)


def lancet_window(prefix, K, x, y, z, w, h, sky, frame="limestonedk", bars=True, axis="Y"):
    """A pointed window in a wall facing -Y (axis Y) or -X: a stone frame, iron bars and a glowing sky behind it."""
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, h * 0.62)] + [(math.cos(a) * w / 2 * 1.0, h * 0.62 + math.sin(a) * h * 0.38) for a in
                                                         [math.radians(t) for t in (20, 45, 70, 90, 110, 135, 160)]] + [(-w / 2, h * 0.62)]
    s = _mark()
    GE.sweep(f"{prefix}Frame", [(px, 0, pz) for px, pz in pts + pts[:1]], 0.14, K[frame], sides=6, smooth=0, cap=False)
    if bars:
        for k in range(3):
            tube(f"{prefix}Bar{k}", [((k - 1) * w / 4, 0, 0), ((k - 1) * w / 4, 0, h * 0.9)], 0.03, K["iron"], poly=True)
    set_group("Sky")
    tp(f"{prefix}Sky", pts, 0.4, 0.05, K["glowmat"])
    P.PARTS[-1]["sky"] = sky
    set_group("Main")
    M = Matrix.Translation((x, y, z)) @ (Matrix.Identity(4) if axis == "Y" else Matrix.Rotation(-math.pi / 2, 4, "Z"))
    _xform(s, M)


def bookshelf(prefix, K, x, y, w, h, rot=0.0, seed=0, burnt=0.0):
    """A tall oak bookcase full of leather and cloth books, built as one mesh (fast: no per-book objects)."""
    import bmesh
    rnd = random.Random(seed)
    covers = ["oak", "leather_oxblood", "leather_brown", "leather_black", "velvet_blue", "wool_green", "parchment"]
    bm = bmesh.new()

    def cube(sx, sy, sz, cx, cy, cz, mi, lean=0.0):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        M = Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(lean, 4, "Y") @ Matrix.Diagonal((sx, sy, sz, 1))
        bmesh.ops.transform(bm, matrix=M, verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi
    cube(w, 0.15, h, 0, 0.95, h / 2, 0)
    for sx in (-1, 1):
        cube(0.15, 1.0, h, sx * (w / 2 - 0.075), 0.5, h / 2, 0)
    rows = int(h / 1.1)
    for r in range(rows):
        z = 0.15 + r * 1.1
        cube(w - 0.1, 0.95, 0.08, 0, 0.45, z, 0)
        xx = -w / 2 + 0.18
        while xx < w / 2 - 0.3:
            bw = rnd.uniform(0.12, 0.26)
            bh = rnd.uniform(0.6, 0.95)
            lean = rnd.uniform(-0.12, 0.12) if rnd.random() < 0.2 else 0
            cube(bw, 0.7, bh, xx + bw / 2, 0.45, z + 0.04 + bh / 2, rnd.randrange(1, len(covers)), lean)
            xx += bw + 0.012
    cube(w + 0.3, 1.15, 0.3, 0, 0.5, h + 0.15, 0)
    me = bpy.data.meshes.new(prefix)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(prefix, me)
    bpy.context.collection.objects.link(ob)
    for c in covers:
        me.materials.append(K[c])
    ob["nh_group"] = P.GROUP
    P.PARTS.append(ob)
    ob.matrix_world = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, "Z")


def candle(prefix, K, x, y, z, h=0.5, lights=None, color=(1.0, 0.6, 0.25), energy=30):
    cyl(f"{prefix}Wax", 0.09, h, (x, y, z + h / 2), K["wax"], verts=10)
    GE.in_group("Glow", lambda: GE.flames(f"{prefix}F", (x, y, z + h), 0.25, 0.06, K["glowmat"], n=1, seed=int(x * 10) % 7))
    if lights is not None:
        lights.append(("POINT", (x, y, z + h + 0.3), energy, color, 0.1))


def column(prefix, K, x, y, h, r=0.6, mat="limestonedk"):
    lathe(f"{prefix}", [(0, 0), (r * 1.4, 0), (r * 1.4, 0.4), (r, 0.6), (r, h - 0.6), (r * 1.4, h - 0.4), (r * 1.4, h), (0, h)], K[mat], seg=16,
          loc=(x, y, 0))


def floor_plane(name, K, mat, size=60, z=0.0):
    box(name, (size, size, 0.2), (0, 0, z - 0.1), K[mat], bevel=0.0)


# ------------------------------------------------------------------ the scenes: each returns (camera loc, target, lens, lights, world rgb, fog)

def bell_tower(K):
    """The Revenant of the bell tower, hanging one-handed from the great bell's rope in a thunderstorm."""
    GLOWC["cur"] = {"Glow": (150, 200, 255), "Glow2": (210, 230, 255), "Glass": (180, 210, 255)}
    L = []
    floor_plane("Floor", K, "slate")
    for k, (x0, x1, y) in enumerate(((-8, 8, 5), )):
        slab_wall(f"Wall{k}", x0, x1, y, 0, 22, K["limestonedk"])
    slab_wall("WallL", -6.5, -5.9, -6, 0, 22, K["limestonedk"], thick=12)
    slab_wall("WallR", 5.9, 6.5, -6, 0, 22, K["limestonedk"], thick=12)
    for k, x in enumerate((-3.2, 3.2)):
        lancet_window(f"Win{k}", K, x, 4.6, 4.0, 3.0, 8.0, (0.35, 0.45, 0.7))
    for k in range(5):
        box(f"Beam{k}", (13, 0.6, 0.6), (0, -4 + k * 2.2, 16.0 + (k % 2) * 0.4), K["oak"], bevel=0.05)
    # the bell
    prof = [(0.0, 0.0), (0.7, 0.0), (0.9, 0.2), (1.1, 1.0), (1.4, 2.0), (1.9, 2.8), (2.3, 3.1), (2.32, 3.3), (2.1, 3.3), (1.75, 2.95), (1.2, 2.05),
            (0.9, 1.05), (0.7, 0.3), (0.0, 0.3)]
    s = _mark()
    lathe("Bell", prof, K["bronzegreen"], seg=40)
    _xform(s, Matrix.Translation((0.8, 1.0, 15.6)) @ Matrix.Rotation(math.pi, 4, "X") @ Matrix.Rotation(0.18, 4, "Y"))
    tube("Rope", [(0.8, 1.0, 12.3), (0.4, 0.6, 9.5), (0.3, 0.2, 6.0), (0.5, 0.0, 2.0)], 0.08, K["linen_grey"])
    f = fig("Wraith", (0.2, 0.0, 6.2), K, "skin_ghoul", face="none", glow_eyes="Glow")
    C.hood(f, K, "wool_black", up=True, deep=0.1)
    f.build("head", lambda: sphere("Void", 0.55, (0, -0.05, 4.6), K["dark"], seg=12, rings=8))
    f.build("head", lambda: GE.in_group("Glow", lambda: [sphere(f"Eye{sx}", 0.08, (sx * 0.2, -0.62, 4.62), K["glowmat"], seg=8, rings=4) for sx in (-1, 1)]))
    C.sleeve_pair(f, K, "wool_black", bell=1.25, z0=2.3, seed=4)
    f.build("torso", lambda: GE.shell("Robe", 1.6, 4.05, 1.08, 0.58, K["wool_black"], r=0.15, nz=8, thick=0.04))
    C.claws(f, K, "bone", L=0.5)
    C.coat_skirt(f, K, "wool_black", length=4.2, z=2.0, gather=1.3, wind=(0.45, 0.3, 0.1), gap=0.0, seed=8, ragged=0.85, turb=0.6, curl=0.4)
    C.cape(f, K, "wool_black", length=4.4, wind=(0.5, 0.4, 0.2), gather=1.3, ragged=0.85, seed=3, clasp="iron", turb=0.6)
    set_group("Glow")
    GE.lightning("Bolt", (-3.6, 8.0, 13.0), (-2.6, 9.0, 4.0), K["glowmat"], seed=2, r=0.12, branches=3)
    GE.lightning("Bolt2", (3.8, 9.0, 12.0), (3.0, 9.5, 5.0), K["glowmat"], seed=5, r=0.08, branches=2)
    set_group("Main")
    rnd = random.Random(1)
    for k in range(40):
        x = rnd.uniform(-5, 5)
        y = rnd.uniform(4.8, 8)
        z = rnd.uniform(2, 14)
        tube(f"Rain{k}", [(x, y, z), (x + 0.15, y, z - 0.8)], 0.012, K["glassmat"], poly=True)
    L += [("AREA", (-3.2, 9, 8), 3000, (0.6, 0.7, 1.0), 6.0), ("AREA", (3.2, 9, 8), 2200, (0.6, 0.7, 1.0), 6.0),
          ("SPOT", (0.5, -9, 4), 2600, (1.0, 0.72, 0.45), 1.0), ("POINT", (0.4, -0.8, 11.0), 120, (0.6, 0.8, 1.0), 0.2)]
    return (Vector((2.8, -13.5, 3.2)), Vector((0.3, 0.5, 9.0)), 38, L, (0.01, 0.012, 0.025), 0.035)


def flooded_crypt(K):
    """The Crypt Lord wading out of the black water of the flooded crypt between drowned tombs and candles."""
    GLOWC["cur"] = {"Glow": (255, 170, 80), "Glow2": (140, 255, 120), "Glass": (20, 40, 35)}
    L = []
    floor_plane("Floor", K, "slate", z=-1.5)
    slab_wall("Back", -14, 14, 9, -2, 14, K["limestonedk"])
    for k, x in enumerate((-8, -3, 3, 8)):
        for yy in (-2, 5):
            column(f"Col{k}{yy}", K, x, yy, 12, r=0.7)
    for k in range(4):
        s = _mark()
        GE.sweep(f"Vault{k}", [(-8 + k * 5.33, -2, 12), (-8 + k * 5.33 + 2.66, -2, 14.5), (-8 + k * 5.33 + 5.33, -2, 12)], 0.4, K["limestonedk"], sides=8)
        _xform(s, Matrix.Identity(4))
    for k, (x, y, r) in enumerate(((-5.5, 2.5, 0.3), (5.0, 3.5, -0.4), (-2.0, 6.5, 0.1))):
        box(f"Tomb{k}", (2.2, 4.0, 1.2), (x, y, 0.2), K["limestone"], bevel=0.08, rot=(0, 0, r))
        box(f"TombLid{k}", (2.4, 4.2, 0.3), (x, y, 0.95), K["limestonedk"], bevel=0.06, rot=(0.05, 0.04, r))
        for sx in (-1, 1):
            candle(f"TC{k}{sx}", K, x + sx * 0.7, y - 1.6, 1.1, h=0.45, lights=L, energy=25)
    set_group("Glass")
    box("Water", (40, 40, 0.1), (0, 0, 0.55), K["glassmat"], bevel=0.0)
    set_group("Main")
    f = fig("Ghoul", (0.4, -1.2, -1.0), K, "skin_ghoul", face="snarl", glow_eyes="Glow2")
    C.hair(f, K, "hair_white", "long", seed=3, length=0.8)
    f.build("head", lambda: [GE.sweep(f"BoneSpike{k}", [(math.cos(a) * 0.6, math.sin(a) * 0.6, 5.1), (math.cos(a) * 0.72, math.sin(a) * 0.72, 5.6 + 0.2 * (k % 2))],
                                      lambda t: 0.08 * (1 - t) + 0.01, K["bone"], sides=5, smooth=0) for k, a in enumerate([i * 2 * math.pi / 9 for i in range(9)])])
    C.jacket(f, K, "wool_green", hem=1.3, lapel="velvet_black", shirt="linen_grey", tie="silk_black", buttons="silver", seed=5, trim="silver")
    C.trousers(f, K, "wool_black", seed=6)
    C.claws(f, K, "bone", L=0.55)
    C.coat_skirt(f, K, "wool_green", length=2.4, z=2.1, gather=1.2, wind=(0, 0.6, 0.15), gap=0.35, ragged=0.6, seed=2)
    set_group("Glow2")
    GE.embers("Mote", (0.4, -1.2, 3.0), 30, 6.0, K["glow2mat"], seed=3, size=0.06, rise=1.2)
    set_group("Main")
    L += [("AREA", (0, 8.5, 10), 900, (0.3, 1.0, 0.5), 8.0), ("SPOT", (5, -10, 9), 2400, (1.0, 0.75, 0.5), 1.5), ("POINT", (0.4, -3.0, 3.0), 80, (0.4, 1.0, 0.5), 0.3)]
    return (Vector((-2.5, -12.5, 2.6)), Vector((0.4, 1.0, 3.6)), 32, L, (0.006, 0.012, 0.01), 0.05)


def burning_library(K):
    """Ezra Vale of the Vigil running from the burning library, books clutched to his chest, looking back at the flames."""
    GLOWC["cur"] = {"Glow": (255, 130, 40), "Glow2": (255, 210, 120), "Glass": (60, 50, 45)}
    L = []
    floor_plane("Floor", K, "oak")
    for k, x in enumerate((-9, -4.5, 4.5, 9)):
        bookshelf(f"ShelfL{k}", K, x, 6, 4.2, 10.5, seed=k)
    for k, y in enumerate((-2, 2.5)):
        bookshelf(f"ShelfS{k}", K, -11.5, y, 4.0, 10.5, rot=math.pi / 2, seed=10 + k)
        bookshelf(f"ShelfE{k}", K, 11.5, y, 4.0, 10.5, rot=-math.pi / 2, seed=20 + k)
    set_group("Glow")
    for k, (x, y, z, h) in enumerate(((-9, 5.6, 0.0, 6.0), (-4.5, 5.6, 2.0, 7.0), (4.5, 5.6, 0.5, 8.0), (-11, 2.5, 1.0, 6.0), (8.0, 5.6, 4.0, 6.0), (0, 4.0, 0, 3.0))):
        GE.flames(f"Fire{k}", (x, y, z), h, 1.0, K["glowmat"], n=7, seed=k, spread=1.6)
    GE.embers("Embers", (0, 2, 4), 60, 9.0, K["glow2mat"], seed=4, size=0.07, rise=1.2)
    set_group("Main")
    rnd = random.Random(5)
    for k in range(10):
        s = _mark()
        GE.book(f"Fallen{k}", K, w=0.7, d=0.9, t=0.2, cover=rnd.choice(("leather_oxblood", "leather_brown", "leather_black")), open_=k % 3 == 0)
        _xform(s, Matrix.Translation((rnd.uniform(-5, 5), rnd.uniform(-3, 3), 0.02)) @ Matrix.Rotation(rnd.uniform(0, 6), 4, "Z"))
    f = fig("Scholar", (1.2, -2.0, 0), K, "skin_warm", face="fierce")
    f.settle(0.0)
    C.hair(f, K, "hair_brown", "swept", seed=5, flow=(0.4, 1, 0.2))
    C.jacket(f, K, "wool_navy", hem=1.75, lapel="wool_black", shirt="linen", tie="silk_crimson", buttons="silver", seed=7, trim="silver",
             crest=("silk_crimson", "silver"), cuff="wool_black")
    C.trousers(f, K, "wool_grey", seed=8)
    C.boots(f, K, "leather_brown", h=0.8, sole="rubber")
    C.coat_skirt(f, K, "wool_navy", length=1.4, z=2.1, gather=1.2, wind=(0.6, 0.7, 0.1), gap=0.3, seed=3)
    root = f.at("torso", (0.6, 0.55, 4.0))
    tail = [root + Vector((0.8 * t, 1.2 * t, -0.3 * t + 0.4 * math.sin(t * 5))) for t in [i / 6 for i in range(7)]]
    GE.ribbon("Scarf", tail, 0.42, K["wool_crimson"], up=(0, 0, 1), thick=0.06, twist=0.9)
    for k in range(4):
        s = _mark()
        GE.book(f"Arms{k}", K, w=0.8, d=1.1, t=0.22, cover=("leather_oxblood", "leather_black", "velvet_blue", "leather_brown")[k])
        _xform(s, Matrix.Translation(f.at("torso", (-1.2, -0.75, 2.55 + k * 0.26))) @ f.world("waist").to_3x3().normalized().to_4x4() @
               Matrix.Rotation(math.radians(-8 + k * 7), 4, "Z") @ Matrix.Scale(S * 0.75, 4))
    L += [("AREA", (0, 8, 6), 9000, (1.0, 0.45, 0.15), 10.0), ("POINT", (-6, 3, 4), 1800, (1.0, 0.5, 0.2), 1.0), ("POINT", (6, 3, 5), 1800, (1.0, 0.5, 0.2), 1.0),
          ("AREA", (-6, -10, 6), 400, (0.4, 0.5, 0.9), 6.0)]
    return (Vector((-3.5, -13.0, 2.4)), Vector((0.8, 0.0, 4.0)), 30, L, (0.03, 0.012, 0.005), 0.06)


def moonlit_rooftop(K):
    """A Court vampire leaping the gap between two rooftops under the full moon, cape spread like wings."""
    GLOWC["cur"] = {"Glow": (220, 230, 255), "Glow2": (255, 40, 50), "Glass": (200, 210, 230)}
    L = []
    for k, (x0, x1, h) in enumerate(((-14, -3.5, 0), (3.5, 14, -1.5))):
        box(f"Roof{k}", (x1 - x0, 14, 0.6), ((x0 + x1) / 2, 2, h), K["slate"], bevel=0.05)
        box(f"Parapet{k}", (0.8, 14, 1.4), (x1 if k == 0 else x0, 2, h + 0.8), K["limestonedk"], bevel=0.06)
        box(f"Mass{k}", (x1 - x0, 14, 20), ((x0 + x1) / 2, 2, h - 10.3), K["limestonedk"], bevel=0.05)
    for k, (x, y, h) in enumerate(((-9, 5, 3.5), (-6, 7, 4.5), (9, 6, 3.0))):
        box(f"Chimney{k}", (1.2, 1.2, h), (x, y, h / 2 + (0 if x < 0 else -1.5)), K["brick"], bevel=0.04)
    # a gargoyle crouched on the near parapet (a sculpted beast)
    O.blob("Gargoyle", [((-3.5, -1.5, 1.6), 0.6, (1.0, 1.2, 0.9), None, 2.0), ((-3.5, -2.2, 2.2), 0.42, None, None, 2.0),
                        ((-3.2, -1.2, 1.1), 0.3, None, None, 2.0), ((-3.8, -1.2, 1.1), 0.3, None, None, 2.0)], K["limestonedk"], res=0.06, decimate=0.6,
           displace=(0.05, 0.1))
    for sx in (-1, 1):
        GE.sweep(f"GargWing{sx}", [(-3.5 + sx * 0.4, -1.4, 2.0), (-3.5 + sx * 1.4, -1.0, 2.8), (-3.5 + sx * 1.9, -0.8, 2.2)], lambda t: 0.25 * (1 - t) + 0.03,
                 K["limestonedk"], sides=6, flat=0.3)
    # the school far off on its hill
    for k, (x, w, h) in enumerate(((-30, 6, 16), (-22, 4, 24), (-16, 8, 14), (18, 6, 18), (26, 3, 28))):
        box(f"Far{k}", (w, 2, h), (x, 60, h / 2 - 12), K["dark"], bevel=0.0)
        cone(f"Spire{k}", w * 0.45, 0, 6, (x, 60, h - 12 + 3), K["dark"], verts=4)
    set_group("Glow")
    sphere("Moon", 9.0, (16, 80, 30), K["glowmat"], seg=40, rings=20)
    set_group("Main")
    f = fig("VampLeap", (0, 0.5, 4.0), K, "skin_vamp", face="smirk", glow_eyes="Glow2")
    C.hair(f, K, "hair_black", "long", seed=8, length=1.2, flow=(0.6, 1, 0.6))
    f.build("torso", lambda: [GE.shell("Bodice", 2.2, 4.05, 1.08, 0.58, K["velvet_crimson"], r=0.15, nz=6, thick=0.04)] +
            [GE.sweep(f"Lace{k}", [(-0.12, -0.6, 2.3 + k * 0.28), (0.12, -0.6, 2.44 + k * 0.28)], 0.02, K["gold"], sides=4, smooth=0) for k in range(6)])
    C.sleeve_pair(f, K, "silk_black", bell=1.15, cuff="velvet_crimson")
    C.trousers(f, K, "silk_black", seed=4)
    C.boots(f, K, "leather_black", h=1.2, sole="leather_black", heel=0.2, buckles="silver")
    C.coat_skirt(f, K, "silk_black", length=1.2, z=2.25, gather=1.4, wind=(0.4, 0.5, 0.5), gap=0.0, seed=4)
    C.cape(f, K, "velvet_black", lining="silk_crimson", length=5.0, wind=(0.5, 0.55, 0.45), gather=1.3, seed=12, collar="silk_crimson", gem="ruby", curl=0.4)
    L += [("SUN", (0, 0, 0), 2.2, (0.7, 0.78, 1.0), (math.radians(-60), 0, math.radians(160))), ("AREA", (-6, -8, 6), 300, (1.0, 0.4, 0.4), 5.0)]
    return (Vector((-1.5, -13.0, 1.0)), Vector((0.5, 3.0, 6.0)), 30, L, (0.02, 0.025, 0.05), 0.012)


def choir_loft(K):
    """A boy of the Chapel Choir singing the solo in the loft, shafts of moonlight from the rose window, staves of
    spectral music rising from the hymnal."""
    GLOWC["cur"] = {"Glow": (255, 236, 190), "Glow2": (255, 170, 80), "Glass": (230, 230, 255)}
    L = []
    floor_plane("Floor", K, "oak")
    slab_wall("Back", -12, 12, 6.5, 0, 20, K["limestonedk"])
    for k in range(9):      # organ pipes
        h = 7 + 4 * math.sin(k / 8 * math.pi)
        cyl(f"Pipe{k}", 0.35, h, (-7.5 + k * 0.8, 5.6, h / 2 + 1), K["silver"], verts=16)
        cone(f"PipeMouth{k}", 0.36, 0.2, 0.4, (-7.5 + k * 0.8, 5.25, 2.6), K["dark"], verts=12, rot=(math.pi / 2, 0, 0))
    box("Balustrade", (16, 0.6, 1.3), (0, -2.6, 0.65), K["oak"], bevel=0.05)
    for k in range(14):
        tube(f"Spindle{k}", [(-7.5 + k * 1.15, -2.9, 0.1), (-7.5 + k * 1.15, -2.9, 1.25)], 0.08, K["oak"], poly=True)
    # the rose window
    s = _mark()
    hoop("Rose", (0, 0, 0), 2.6, "Y", K["limestonedk"], thick=0.2)
    for k in range(12):
        a = k * 2 * math.pi / 12
        tube(f"Spoke{k}", [(0, 0, 0), (math.cos(a) * 2.6, 0, math.sin(a) * 2.6)], 0.07, K["limestonedk"], poly=True)
    set_group("Sky")
    cyl("RoseGlass", 2.6, 0.05, (0, 0.3, 0), K["glowmat"], rot=(math.pi / 2, 0, 0), verts=32)
    P.PARTS[-1]["sky"] = (0.6, 0.65, 1.0)
    set_group("Main")
    _xform(s, Matrix.Translation((4.0, 6.1, 12.0)))
    f = fig("ChoirChild", (0.5, -0.8, 0), K, "skin_pale", face="sing", scale=1.35)
    f.settle(0)
    C.hair(f, K, "hair_blond", "bob", seed=2)
    f.build("torso", lambda: [GE.shell("Cassock", 1.2, 4.04, 1.07, 0.575, K["wool_crimson"], r=0.13, nz=6, thick=0.035),
                              GE.shell("Surplice", 2.0, 3.98, 1.1, 0.6, K["linen"], r=0.15, nz=6, flare0=1.3, thick=0.035, wrinkles=[(2.4, 0.35, 0.06, 6)])] +
            [hoop(f"Ruff{k}", (0, 0, 4.0 + k * 0.08), 0.78 - k * 0.06, "Z", K["linen"], thick=0.08) for k in range(3)])
    C.sleeve_pair(f, K, "linen", bell=1.25, z0=2.2)
    C.coat_skirt(f, K, "wool_crimson", length=1.9, z=1.95, gather=1.15, gap=0.0, seed=2)
    hp = (C.hand_at(f, 1)[0] + C.hand_at(f, -1)[0]) / 2
    s = _mark()
    GE.book("Hymnal", K, w=0.8, d=1.0, open_=True, cover="leather_oxblood")
    _xform(s, Matrix.Translation(hp + Vector((0, -0.3, 0.2))) @ Matrix.Rotation(-0.9, 4, "X"))
    set_group("Glow")
    GE.staves("Stave", (hp.x, hp.y - 0.3, 0), 1.2, hp.z + 0.4, hp.z + 7.5, K["glowmat"], turns=1.4, phase=0.5, notes=12, seed=4)
    set_group("Main")
    for k in range(5):
        candle(f"C{k}", K, -6 + k * 3, -2.6, 1.3, h=0.4, lights=L, energy=20)
    L += [("SPOT", (4.0, 9.0, 13.0), 9000, (0.65, 0.7, 1.0), 0.6), ("AREA", (3, -8, 5), 500, (1.0, 0.75, 0.5), 4.0)]
    return (Vector((-2.4, -10.5, 2.2)), Vector((0.6, 0.0, 4.4)), 32, L, (0.01, 0.01, 0.02), 0.045)


def dorm_corridor(K):
    """Pip Larkin of the Ordinary in the dorm corridor at three in the morning, candle held out, shielding his eyes
    from the drowned girl drifting toward him at the far end."""
    GLOWC["cur"] = {"Glow": (255, 170, 80), "Glow2": (170, 230, 255), "Glass": (170, 230, 255)}
    L = []
    floor_plane("Floor", K, "oak")
    GE.ribbon("Runner", [(0, -24, 0.02), (0, 30, 0.02)], 2.2, K["velvet_crimson"], up=(1, 0, 0), thick=0.02, smooth=0)
    for side in (-1, 1):
        box(f"Wall{side}", (0.5, 60, 11), (side * 3.2, 5, 5.5), K["limestone"], bevel=0.0)
        for k in range(5):
            y = 1 + k * 5.5
            box(f"Door{side}{k}", (0.2, 2.4, 6.0), (side * 2.95, y, 3.0), K["oak"], bevel=0.04)
            sphere(f"Knob{side}{k}", 0.1, (side * 2.82, y - 0.8, 3.0), K["brass"], seg=8, rings=4)
            box(f"Panel{side}{k}", (0.22, 1.8, 2.0), (side * 2.94, y, 4.2), K["oak"], bevel=0.04)
            box(f"Wains{side}{k}", (0.15, 3.0, 2.0), (side * 3.0, y + 2.7, 1.0), K["oak"], bevel=0.02)
    box("Ceiling", (7, 60, 0.3), (0, 5, 11), K["limestonedk"], bevel=0.0)
    lancet_window("End", K, 0, 31, 2.0, 3.0, 7.0, (0.5, 0.6, 0.9))
    f = fig("Pip", (0.2, -1.0, 0), K, "skin_warm", face="shout")
    f.settle(0)
    C.hair(f, K, "hair_brown", "messy" if False else "crop", seed=7)
    f.build("torso", lambda: [GE.shell("PJTop", 1.85, 4.04, 1.08, 0.58, K["knit_grey"], r=0.15, nz=7, flare0=1.06, thick=0.035, wrinkles=[(2.6, 0.4, 0.06, 4)])] +
            [sphere(f"PJBtn{k}", 0.05, (0, -0.62, 2.3 + k * 0.4), K["porcelain"], seg=6, rings=3) for k in range(4)])
    C.sleeve_pair(f, K, "knit_grey", bell=1.05)
    C.trousers(f, K, "knit_grey", seed=9, cuff=0.15, flare=1.05)
    C.hold(f, 1, lambda: [lathe("Holder", [(0, 0), (0.3, 0), (0.32, 0.06), (0.1, 0.1), (0.07, 0.25), (0, 0.25)], K["brass"], seg=12),
                          cyl("PipCandle", 0.07, 0.4, (0, 0, 0.45), K["wax"], verts=10)], along=(0, 0, 1), push=-0.1)
    hp, _ = C.hand_at(f, 1)
    GE.in_group("Glow", lambda: GE.flames("PipFlame", hp + Vector((0, 0, 1.15)), 0.35, 0.08, K["glowmat"], n=1))
    L.append(("POINT", tuple(hp + Vector((0, 0, 1.4))), 160, (1.0, 0.6, 0.3), 0.1))
    set_group("Glass")
    g = fig("GhostGirl", (0, 14, 0.3), K, "glassmat", face="closed", parts=("head", "torso", "rarm", "larm", "rleg", "lleg"))
    C.hair(g, K, "glassmat", "long", seed=5, length=1.6)
    g.build("torso", lambda: GE.shell("Shroud", 0.2, 4.0, 1.12, 0.62, K["glassmat"], r=0.2, nz=8, flare0=1.4, thick=0.03, tatter=3))
    set_group("Main")
    L += [("AREA", (0, 30, 6), 3500, (0.55, 0.7, 1.0), 4.0), ("POINT", (0, 14.5, 3.5), 300, (0.6, 0.9, 1.0), 1.0)]
    return (Vector((0.0, -9.5, 3.4)), Vector((0.0, 6.0, 3.6)), 30, L, (0.004, 0.005, 0.01), 0.04)


def frozen_lake(K):
    """A Bloodmoon werewolf, fully turned, howling on the cracked ice of the frozen lake under the blood moon, the
    black pines on the far shore."""
    GLOWC["cur"] = {"Glow": (255, 60, 40), "Glow2": (255, 190, 70), "Glass": (190, 220, 255)}
    L = []
    box("Ice", (120, 120, 0.3), (0, 0, -0.15), K["moonstone"], bevel=0.0)
    rnd = random.Random(3)
    for k in range(18):
        a = rnd.uniform(0, 6.28)
        pts = [Vector((0.5, -0.5, 0.01))]
        for i in range(5):
            pts.append(pts[-1] + Vector((math.cos(a + rnd.uniform(-0.5, 0.5)) * 1.4, math.sin(a + rnd.uniform(-0.5, 0.5)) * 1.4, 0)))
        GE.sweep(f"Crack{k}", pts, 0.04, K["dark"], sides=4, smooth=0)
    for k in range(9):
        GE.slab(f"Floe{k}", (rnd.uniform(-6, 6), rnd.uniform(-3, 4), 0.1), rnd.uniform(0.8, 1.8), rnd.uniform(0.6, 1.4), 0.25, K["moonstone"], seed=k,
                tilt=(rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2)))
    for k in range(40):
        x = -45 + k * 2.3 + rnd.uniform(-0.8, 0.8)
        h = rnd.uniform(8, 16)
        for t in range(4):
            cone(f"Pine{k}_{t}", h * (0.22 - t * 0.04), 0, h * 0.45, (x, 45 + rnd.uniform(-2, 2), h * 0.18 + t * h * 0.2), K["dark"], verts=6)
    set_group("Glow")
    sphere("BloodMoon", 7.0, (-8, 75, 22), K["glowmat"], seg=40, rings=20)
    set_group("Main")
    f = fig("Werewolf", (0.4, 0, 0), K, "fur_grey", face="howl", glow_eyes="Glow2", parts=("head", "torso", "rarm", "larm", "rleg", "lleg"))
    f.settle(0)
    fur = K["fur_grey"]
    f.build("head", lambda: [O.blob("Muzzle", [(p, r, (1.25, 1.0, 0.75), None, 2.0) for p, r, *_ in
                                               O.chain([(0, -0.45, 4.62), (0, -0.95, 4.52), (0, -1.45, 4.42), (0, -1.7, 4.38)], 0.36, 0.17)] +
                                    O.chain([(0, -0.5, 4.22), (0, -0.95, 4.02), (0, -1.35, 3.88)], 0.2, 0.1), fur, res=0.045, decimate=0.5),
                             sphere("Nose", 0.12, (0, -1.8, 4.44), K["dark"], seg=10, rings=6, scale=(1.3, 1, 0.75))] +
            [GE.sweep(f"Ear{sx}", [(sx * 0.42, 0.1, 5.0), (sx * 0.6, 0.25, 5.5), (sx * 0.72, 0.45, 6.0)], lambda t: 0.26 * (1 - t) ** 0.8 + 0.01, fur, sides=8, flat=0.45)
             for sx in (-1, 1)])
    for part, pts, r0, r1 in (("torso", [(0, 0.6, 2.2), (0, 0.75, 3.2), (0, 0.65, 4.3)], 0.45, 0.5), ("torso", [(-0.8, -0.55, 3.9), (0, -0.7, 3.6), (0.8, -0.55, 3.9)], 0.4, 0.4),
                              ("head", [(-0.6, 0.3, 4.9), (0, 0.6, 5.0), (0.6, 0.3, 4.9)], 0.35, 0.35)):
        f.build(part, lambda pts=pts, r0=r0, r1=r1: O.blob("Fur", O.chain(pts, r0, r1), fur, res=0.07, decimate=0.4, displace=(0.08, 0.1)))
    f.build("torso", lambda: GE.shell("TornShirt", 2.0, 3.6, 1.06, 0.57, K["linen"], r=0.14, nz=6, thick=0.03, tatter=5, seed=4))
    C.trousers(f, K, "denim", seed=10, cuff=0.9)
    C.claws(f, K, "bone", L=0.55)
    set_group("Glass")
    O.plume("Breath", K["glassmat"], f.at("head", (0, -1.9, 4.5)), 0.35, 1.2, seed=2, tendrils=3, billows=4, res=0.08)
    set_group("Main")
    L += [("AREA", (-8, 40, 18), 30000, (1.0, 0.3, 0.2), 20.0), ("SUN", (0, 0, 0), 0.6, (0.6, 0.7, 1.0), (math.radians(-50), 0, math.radians(30))),
          ("AREA", (6, -6, 4), 300, (0.5, 0.6, 1.0), 4.0)]
    return (Vector((3.5, -12.0, 1.4)), Vector((0.0, 2.0, 4.6)), 32, L, (0.02, 0.025, 0.05), 0.012)


def headmaster_study(K):
    """The Headmaster at his desk by the fire, fingers steepled, a raven on the bust behind him; his shadow on the wall
    has horns."""
    GLOWC["cur"] = {"Glow": (255, 140, 50), "Glow2": (255, 60, 60), "Glass": (60, 50, 45)}
    L = []
    floor_plane("Floor", K, "oak")
    GE.ribbon("Rug", [(-5, -2, 0.02), (5, -2, 0.02)], 6, K["velvet_crimson"], up=(0, 1, 0), thick=0.02, smooth=0)
    slab_wall("Back", -12, 12, 6, 0, 16, K["wool_green"])
    for k, x in enumerate((-8.5, 8.5)):
        bookshelf(f"Shelf{k}", K, x, 4.6, 4.5, 11, seed=30 + k)
    box("Mantel", (5, 1.4, 0.4), (-3.5, 5.0, 4.6), K["blackmarble"], bevel=0.05)
    box("Hearth", (4.4, 1.2, 4.4), (-3.5, 5.3, 2.2), K["blackmarble"], bevel=0.05)
    box("Firebox", (3.0, 0.8, 3.0), (-3.5, 4.75, 1.5), K["dark"], bevel=0.02)
    GE.in_group("Glow", lambda: GE.flames("Fire", (-3.5, 4.7, 0.2), 2.2, 0.8, K["glowmat"], n=7, seed=3, spread=1.0))
    L.append(("POINT", (-3.5, 3.8, 1.5), 900, (1.0, 0.5, 0.2), 0.6))
    # the desk
    box("Desk", (7.0, 3.2, 0.3), (0.8, -1.2, 3.0), K["ebony"], bevel=0.06)
    box("DeskTop", (6.6, 2.8, 0.05), (0.8, -1.2, 3.17), K["leather_oxblood"], bevel=0.01)
    for sx in (-1, 1):
        box(f"Pedestal{sx}", (2.0, 2.8, 2.85), (0.8 + sx * 2.3, -1.2, 1.43), K["ebony"], bevel=0.05)
    candle("DeskCandle", K, 3.2, -1.6, 3.2, h=0.6, lights=L, energy=60)
    s = _mark()
    GE.book("DeskBook", K, w=0.9, d=1.2, open_=True, cover="leather_black")
    _xform(s, Matrix.Translation((-1.2, -1.8, 3.2)))
    lathe("Bust", [(0, 0), (0.4, 0), (0.3, 0.3), (0.5, 0.6), (0.45, 1.2), (0.25, 1.5), (0.35, 1.9), (0, 2.1)], K["marble"], seg=16, loc=(4.5, 4.4, 4.8))
    O.raven("Raven", K, (4.5, 4.4, 7.2), heading=math.radians(-120), wings=0.0, perch=True, s=1.4, eye="Glow2")
    f = fig("Headmaster", (0.8, 0.9, 0), K, "skin_pale", face="stern", parts=("head", "rarm", "larm"))
    f.settle(0)
    C.hair(f, K, "hair_white", "slick", seed=4)
    f.build("head", lambda: [O.blob("Sideburns", [((sx * 0.62, -0.1, 4.45), 0.14, (0.6, 1.0, 1.6), None, 2.0) for sx in (-1, 1)], K["hair_white"], res=0.04, decimate=0.5)] +
            [hoop(f"Pince{sx}", (sx * 0.2, -0.66, 4.6), 0.11, "Y", K["gold"], thick=0.015) for sx in (-1, 1)])
    C.jacket(f, K, "wool_black", hem=1.5, lapel="silk_black", shirt="linen", vest="silk_gold", tie="silk_crimson", buttons="gold", seed=9, trim="gold",
             crest=("velvet_crimson", "gold"), cuff="silk_black")
    C.trousers(f, K, "wool_grey", seed=10)
    box("Chair", (3.0, 1.4, 7.4), (0.8, 2.3, 3.7), K["leather_oxblood"], bevel=0.3)
    # the horned shadow: a flat dark silhouette on the back wall
    tp("Shadow", [(-2.2, 6.0), (2.2, 6.0), (2.6, 11.5), (3.4, 13.8), (2.0, 12.4), (0.8, 13.0), (-0.8, 13.0), (-2.0, 12.4), (-3.4, 13.8), (-2.6, 11.5)], 5.65, 0.02,
       K["dark"])
    P.PARTS[-1].matrix_world = Matrix.Translation((1.2, 0, 0))
    L += [("SPOT", (-3, -10, 5), 2600, (1.0, 0.8, 0.6), 0.8), ("AREA", (6, -4, 9), 300, (0.5, 0.6, 1.0), 3.0)]
    return (Vector((-1.0, -12.5, 5.6)), Vector((0.8, 0.5, 5.4)), 32, L, (0.008, 0.006, 0.005), 0.025)


def gym_midnight(K):
    """Captain Rhys Thorne alone on the gym floor at midnight, ball under his arm, facing the translucent ghosts of
    the 1903 team lined up on the centre line under the swinging lamps."""
    GLOWC["cur"] = {"Glow": (255, 220, 160), "Glow2": (255, 200, 80), "Glass": (180, 230, 255)}
    L = []
    floor_plane("Floor", K, "oak")
    for k in range(4):
        GE.sweep(f"CourtLine{k}", [(-12, -2 + k * 6, 0.02), (12, -2 + k * 6, 0.02)], 0.06, K["linen"], sides=4, smooth=0, cap=False)
    GE.sweep("Circle", [(math.cos(a) * 3.0, 6 + math.sin(a) * 3.0, 0.02) for a in [i * 2 * math.pi / 40 for i in range(41)]], 0.06, K["linen"], sides=4, smooth=0)
    slab_wall("Back", -16, 16, 16, 0, 18, K["brick"])
    for k in range(6):
        box(f"Bleacher{k}", (20, 1.2, 0.6), (0, 13 + k * 0.6, 0.3 + k * 0.6), K["oak"], bevel=0.04)
    box("Scoreboard", (6, 0.4, 2.4), (0, 15.6, 12), K["enamel_black"], bevel=0.05)
    GE.in_group("Glow", lambda: [box(f"Digit{k}", (0.6, 0.1, 1.0), (-1.8 + k * 1.2, 15.35, 12), K["glowmat"], bevel=0.02) for k in range(4)])
    for k, x in enumerate((-6, 0, 6)):
        tube(f"LampCord{k}", [(x, 4 + k, 20), (x + 0.4 * k, 4 + k, 11)], 0.03, K["iron"], poly=True)
        lathe(f"Shade{k}", [(0.1, 0), (1.2, -0.9), (1.25, -1.0), (0, -0.2)], K["enamel_black"], seg=16, loc=(x + 0.4 * k, 4 + k, 11))
        GE.in_group("Glow", lambda x=x, k=k: sphere(f"Bulb{k}", 0.3, (x + 0.4 * k, 4 + k, 10.2), K["glowmat"], seg=10, rings=6))
        L.append(("SPOT", (x + 0.4 * k, 4 + k, 10.0), 2200, (1.0, 0.85, 0.6), 0.5))
    f = fig("Captain", (0.5, -2.0, 0), K, "skin_dark", face="stern")
    f.settle(0)
    C.hair(f, K, "hair_black", "crop", seed=6)
    f.build("torso", lambda: [GE.shell("Jersey", 2.0, 4.05, 1.08, 0.58, K["knit_crimson"], r=0.14, nz=7, flare0=1.06, thick=0.03)])
    C.sleeve_pair(f, K, "knit_crimson", z0=3.1, cuff="knit_gold", cuff_h=0.12)
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"
        f.build(part, lambda side=side: [GE.shell(f"Shorts{side}", 1.4, 2.1, 0.58, 0.58, K["knit_white"], cx=side * 0.5, r=0.13, n=20, nz=3, flare0=1.08, thick=0.03),
                                         GE.shell(f"Sock{side}", 0.3, 1.0, 0.54, 0.54, K["knit_crimson"], cx=side * 0.5, r=0.13, n=20, nz=3, thick=0.025)])
    C.boots(f, K, "leather_black", h=0.32, sole="rubber", toe=0.25, heel=0.05)
    sphere("Ball", 0.55, tuple(f.at("torso", (-1.25, -0.2, 2.7)) + Vector((-0.6, 0, 0))), K["leather_brown"], seg=20, rings=12, scale=(1.25, 1, 1))
    set_group("Glass")
    for k, key in enumerate(("GhostA", "GhostB", "GhostC")):
        g = fig(key, (-4 + k * 4, 7.0, 0), K, "glassmat", face="closed", parts=("head", "torso", "rarm", "larm", "rleg", "lleg"))
        g.settle(0)
        g.build("torso", lambda: GE.shell("OldJersey", 2.0, 4.05, 1.1, 0.6, K["glassmat"], r=0.14, nz=4, thick=0.03))
    set_group("Main")
    L += [("AREA", (0, -10, 7), 500, (0.4, 0.5, 0.9), 6.0), ("POINT", (0, 7.5, 3), 400, (0.6, 0.9, 1.0), 2.0)]
    return (Vector((-3.0, -12.5, 2.8)), Vector((0.5, 3.0, 4.0)), 30, L, (0.006, 0.007, 0.012), 0.03)


def ink_archive(K):
    """Wren Ashby in the flooded archive, standing in the black ink that has risen off every page, calling the ink up
    into tendrils and shapes of beasts round her."""
    GLOWC["cur"] = {"Glow": (185, 90, 255), "Glow2": (120, 230, 255), "Glass": (40, 20, 60)}
    L = []
    floor_plane("Floor", K, "slate")
    for k, x in enumerate((-9, -4.5, 0, 4.5, 9)):
        bookshelf(f"Stack{k}", K, x, 8, 4.2, 12, seed=50 + k)
    for k, y in enumerate((-1, 4)):
        bookshelf(f"Side{k}", K, -11, y, 4.6, 12, rot=math.pi / 2, seed=60 + k)
    box("InkFlood", (40, 40, 0.5), (0, 0, 0.25), K["ink"], bevel=0.0)
    f = fig("InkGirl", (0.4, -1.2, 0.5), K, "skin_pale", face="smirk")
    f.settle(0.35)
    C.hair(f, K, "hair_red", "bob", seed=6)
    f.build("torso", lambda: [GE.shell("Smock", 1.4, 4.04, 1.08, 0.58, K["linen_grey"], r=0.15, nz=9, flare0=1.18, thick=0.035, wrinkles=[(2.6, 0.5, 0.06, 5)]),
                              tp("Apron", [(-0.75, 1.5), (0.75, 1.5), (0.68, 3.1), (0.42, 3.55), (-0.42, 3.55), (-0.68, 3.1)], -0.64, 0.03, K["leather_brown"])])
    C.sleeve_pair(f, K, "linen_grey", z0=2.75, cuff="linen_grey", cuff_h=0.25)
    C.trousers(f, K, "denim_black", seed=9)
    C.boots(f, K, "leather_brown", h=0.95, sole="rubber", buckles="brass")
    rnd = random.Random(8)
    for k in range(8):
        a = k * 2 * math.pi / 8 + rnd.uniform(-0.2, 0.2)
        base = Vector((0.4 + math.cos(a) * 2.6, -1.2 + math.sin(a) * 2.0, 0.5))
        h = rnd.uniform(4, 9)
        pts = [base + Vector((math.cos(a + t * 3) * 0.8 * t, math.sin(a + t * 3) * 0.8 * t, h * t)) for t in [i / 8 for i in range(9)]]
        GE.sweep(f"Tendril{k}", pts, lambda t: 0.35 * (1 - t) ** 0.9 + 0.03, K["ink"], sides=8, smooth=2)
        GE.in_group("Glow", lambda pts=pts, k=k: GE.crystal(f"Tip{k}", pts[-1], 0.25, K["glowmat"], (0, 0, 1)))
    # an ink wolf and an ink raven rising out of the flood
    O.wolf("InkWolf", K["ink"], Matrix.Translation((-4.5, 1.5, 0.3)) @ Matrix.Rotation(math.radians(30), 4, "Z") @ Matrix.Scale(1.1, 4), howl=False, rear=0.3,
           eye="Glow", eye_mat=K["glowmat"], fur=0.04)
    O.raven("InkRaven", K, (4.5, 1.0, 7.0), heading=math.radians(200), wings=0.8, s=2.2, mat="ink", eye="Glow")
    L += [("AREA", (0, -6, 12), 1500, (0.7, 0.4, 1.0), 8.0), ("POINT", (0.4, -2.0, 6), 500, (0.7, 0.4, 1.0), 1.0), ("SPOT", (-4, -10, 6), 1800, (1.0, 0.8, 0.6), 0.8)]
    return (Vector((-2.0, -12.0, 2.8)), Vector((0.2, 0.5, 4.2)), 30, L, (0.01, 0.006, 0.015), 0.04)


def mural_courtyard(K):
    """The Night of the Blood Moon: in the school's courtyard the six cliques stand together against the Hollow King
    rising over the fountain, the blood moon behind the bell tower."""
    GLOWC["cur"] = {"Glow": (255, 40, 40), "Glow2": (150, 210, 255), "Glass": (190, 210, 255)}
    L = []
    floor_plane("Floor", K, "slate")
    lathe("Fountain", [(0, 0), (3.2, 0), (3.2, 1.0), (2.9, 1.1), (2.9, 0.4), (0.6, 0.4), (0.5, 2.6), (1.4, 2.8), (1.4, 3.0), (0, 3.0)], K["limestone"], seg=32,
          loc=(0, 9, 0))
    for k, x in enumerate((-22, -14, 14, 22)):
        box(f"Wing{k}", (8, 6, 14), (x, 18, 7), K["limestonedk"], bevel=0.05)
        for j in range(3):
            lancet_window(f"W{k}{j}", K, x - 2.5 + j * 2.5, 14.9, 3.0, 1.4, 4.0, (1.0, 0.6, 0.3), bars=False)
    box("Tower", (6, 6, 30), (0, 24, 15), K["limestonedk"], bevel=0.05)
    cone("TowerSpire", 4.5, 0, 10, (0, 24, 35), K["slate"], verts=4)
    set_group("Glow")
    sphere("BloodMoon", 9.0, (8, 60, 30), K["glowmat"], seg=40, rings=20)
    set_group("Main")
    cast = [("MuralVigil", (-9, -1, 0), "skin_warm", "wool_navy"), ("MuralCourt", (-5.5, 0.5, 0), "skin_vamp", "velvet_crimson"),
            ("MuralPack", (-2.0, -1.5, 0), "skin_warm", "wool_crimson"), ("MuralChoir", (2.5, 0.5, 0), "skin_pale", "linen"),
            ("MuralAthlete", (6.0, -1.0, 0), "skin_dark", "knit_gold"), ("MuralInk", (9.5, 0.0, 0), "skin_pale", "linen_grey")]
    for k, (key, base, skin, cloth) in enumerate(cast):
        f = fig(key, base, K, skin, face="fierce")
        f.settle(0)
        C.hair(f, K, ("hair_brown", "hair_black", "hair_black", "hair_blond", "hair_black", "hair_red")[k], ("swept", "long", "mane", "bob", "crop", "bob")[k], seed=k)
        C.jacket(f, K, cloth, hem=1.7, lapel="wool_black", shirt="linen", buttons="gold", seed=70 + k)
        C.trousers(f, K, "wool_black", seed=80 + k)
        C.boots(f, K, "leather_black", h=0.8)
        if k in (0, 1):
            C.coat_skirt(f, K, cloth, length=1.6, z=2.1, wind=(0.3, 0.6, 0.2), gap=0.3, seed=k)
    # the Hollow King: a crowned wraith rising over the fountain
    set_group("Glass")
    king = fig("MuralKing", (0, 9.5, 3.0), K, "glassmat", face="none", glow_eyes="Glow2", parts=("head", "torso", "rarm", "larm"), scale=2.6)
    king.build("torso", lambda: GE.shell("KingRobe", -1.0, 4.05, 1.15, 0.65, K["glassmat"], r=0.2, nz=8, flare0=1.6, thick=0.04, tatter=4))
    C.sleeve_pair(king, K, "glassmat", bell=1.4, z0=2.2)
    set_group("Glow2")
    king.build("head", lambda: GE.crown("KingCrown", K, (0, 0, 5.1), r=0.66, h=0.55, points=9, metal="glow2mat", gems=("glow2mat",)))
    set_group("Main")
    L += [("AREA", (8, 40, 25), 40000, (1.0, 0.25, 0.2), 25.0), ("AREA", (0, -12, 8), 900, (0.5, 0.6, 1.0), 10.0), ("POINT", (0, 8, 10), 1500, (0.6, 0.8, 1.0), 2.0)]
    return (Vector((0.0, -22.0, 4.0)), Vector((0.0, 6.0, 7.5)), 30, L, (0.02, 0.01, 0.015), 0.012)


SCENES = {
    "PaintingBellTowerStorm": bell_tower, "PaintingFloodedCrypt": flooded_crypt, "PaintingBurningLibrary": burning_library,
    "PaintingMoonlitRooftop": moonlit_rooftop, "PaintingChoirLoft": choir_loft, "PaintingDormCorridor": dorm_corridor,
    "PaintingFrozenLake": frozen_lake, "PaintingHeadmasterStudy": headmaster_study, "PaintingGymMidnight": gym_midnight,
    "PaintingInkArchive": ink_archive, "MuralBloodMoonCourtyard": mural_courtyard,
}


def render(name, out, samples=96, preview=False, wb=False):
    P.PARTS[:] = []
    P.reset()
    P._img_cache.clear()
    sc = bpy.context.scene
    K = kit()
    R.FIGS.clear()
    cam_loc, target, lens, lights, world, fog = SCENES[name](K)
    # frame the cast: keep the scene's camera direction and lens, move in or out so every figure fits with a margin
    figs = list(R.FIGS)
    if figs:
        bpy.context.view_layer.update()
        pts = []
        for f in figs:      # the bodies themselves (capes and effects are allowed to break the frame)
            for o in list(f.body.values()) + ([f.hair] if f.hair else []):
                pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
            pts += [f.at(leg, (sx * 0.5, 0, 0)) for leg, sx in (("rleg", 1), ("lleg", -1))]
        lo = Vector([min(p[k] for p in pts) for k in range(3)])
        hi = Vector([max(p[k] for p in pts) for k in range(3)])
        cw_, ch_ = CANVAS[name]
        tan_h = 18 / lens if cw_ >= ch_ else 18 / lens * cw_ / ch_
        tan_v = 18 / lens * ch_ / cw_ if cw_ >= ch_ else 18 / lens
        size_v = (hi.z - lo.z) * FIT.get(name, 1.35)
        size_h = max(hi.x - lo.x, hi.y - lo.y) * FIT.get(name, 1.35)
        d = max(size_v / 2 / tan_v, size_h / 2 / tan_h)
        new_t = (lo + hi) / 2 + Vector((0, 0, (hi.z - lo.z) * 0.06))
        dirv = (cam_loc - target).normalized()
        target = new_t
        cam_loc = new_t + dirv * d
    cols = GLOWC["cur"]
    # glowing and glass pieces get their colours
    for ob in list(P.PARTS):
        if ob.type != "MESH":
            continue
        g = ob.get("nh_group", "Main")
        if g in ("Glow", "Glow2", "Sky"):
            rgb = tuple(c / 255 for c in cols.get(g, (255, 200, 150))) if g != "Sky" else tuple(ob.get("sky", (0.5, 0.6, 0.9)))
            m = bpy.data.materials.new("E_" + g)
            m.use_nodes = True
            bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 4.5 if g != "Sky" else 2.5
            ob.data.materials.clear()
            ob.data.materials.append(m)
        elif g == "Glass" or (ob.data.materials and ob.data.materials[0] is K["glassmat"]):
            rgb = tuple(c / 255 for c in cols.get("Glass", (200, 220, 255)))
            m = bpy.data.materials.new("G_glass")
            m.use_nodes = True
            bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Roughness"].default_value = 0.1
            bs.inputs["Transmission Weight"].default_value = 0.9
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 0.8
            ob.data.materials.clear()
            ob.data.materials.append(m)
    # a soft key from beside the camera so the faces read (the painter keeps the drama of the scene's own lights)
    kd = (cam_loc - target).length
    side = (cam_loc - target).cross(Vector((0, 0, 1))).normalized()
    lights = list(lights) + [("AREA", tuple(cam_loc + side * kd * 0.12 + Vector((0, 0, kd * 0.15))), KEY.get(name, 1.0) * 3.5 * kd * kd,
                              (1.0, 0.86, 0.72), kd * 0.4)]
    for kind, loc, energy, color, size in lights:
        Ld = bpy.data.lights.new(kind, kind)
        Ld.energy = energy
        Ld.color = color
        o = bpy.data.objects.new(kind, Ld)
        sc.collection.objects.link(o)
        if kind == "SUN":
            o.rotation_euler = size
            Ld.angle = 0.02
        else:
            o.location = loc
            if kind == "AREA":
                Ld.size = size
            else:
                Ld.shadow_soft_size = size
            if kind in ("AREA", "SPOT"):
                o.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            if kind == "SPOT":
                Ld.spot_size = math.radians(40)
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*world, 1)
    if fog:
        vol = w.node_tree.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = fog * 0.3
        vol.inputs["Color"].default_value = (0.8, 0.82, 0.9, 1)
        out_n = next(n for n in w.node_tree.nodes if n.type == "OUTPUT_WORLD")
        w.node_tree.links.new(vol.outputs[0], out_n.inputs["Volume"])
    cam = bpy.data.cameras.new("C")
    cam.lens = lens
    co = bpy.data.objects.new("C", cam)
    sc.collection.objects.link(co)
    co.location = cam_loc
    co.rotation_euler = (target - cam_loc).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    cw, ch = CANVAS[name]
    long = 900 if preview else 2048
    sc.render.resolution_x, sc.render.resolution_y = (long, int(round(long * ch / cw))) if cw >= ch else (int(round(long * cw / ch)), long)
    cam.sensor_fit = "AUTO"
    cam.sensor_width = 36
    sc.cycles.samples = 24 if preview else samples
    sc.cycles.use_denoising = True
    sc.cycles.volume_step_rate = 4.0
    sc.cycles.max_bounces = 6
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    if wb:
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.display.shading.light = "STUDIO"
        sc.display.shading.show_cavity = True
        sc.render.resolution_x //= 2
        sc.render.resolution_y //= 2
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("[scene] saved", out)
