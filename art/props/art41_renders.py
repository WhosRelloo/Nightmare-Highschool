"""The figures for props batch 41's paintings, icons and tapestry (the art kit), posed on the owner's R6 rig
(art41_rig.py, from PaintRigV3.blend) and lit like the art kit's paintings, rendered from the front for art41_canvases.py
to paint over:

  <Scene>_beauty.png  RGBA, transparent background, the figures lit: a cool moon rim, a warm candlelit key, glowing
                      candles, lanterns, torches and eyes
  <Scene>_gilt.png    a mask of the gilt parts (gold in the paint, gilt thread in the tapestry)
  <Scene>_ghost.png   a mask of the ghostly parts (painted translucent)
  <Scene>_points.json the glow sources in px, for the painted halos

into art/props/source_art41/.  "E:/Blender/blender.exe" -b --factory-startup --python E:/NH-Work/props41/renders41.py -- [Scene ...] --gpu
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube  # noqa: E402
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import hoop, strip, lathe, _mark, _xform  # noqa: E402
from nh_props_batch9 import raven  # noqa: E402
from nh_props_batch12 import frustum  # noqa: E402
import nh_props_batch27 as S  # noqa: E402
import tapestry_renders as TR  # noqa: E402
import art41_rig as R  # noqa: E402

OUT = os.path.join(HERE, "source_art41")
os.makedirs(OUT, exist_ok=True)
TR.C["ghost"] = (196, 218, 255)
TR.GLOW["ghost"] = 1.4
TR.GLOW["torch"] = 18.0
TR.C["torch"] = (255, 150, 60)
dye = TR.dye
POINTS = TR.POINTS
GHOST = ("ghost",)


def skin(k="cream"):
    return dye(k)


def fig(base, scale, pose, body, skin_k="cream", face="stern", yaw=0.0, parts=("head", "torso", "rarm", "larm", "rleg", "lleg"), legs=None):
    m = {"head": skin(skin_k), "torso": body, "rarm": body, "larm": body, "rleg": legs or body, "lleg": legs or body}
    return R.Fig(base=base, yaw=yaw, scale=scale, pose=pose, mats=m, parts=parts, face=face, dark=dye("soot"))


# ------------------------------------------------------------------ costume

def hair(f, m, style="short"):
    def h():
        if style in ("short", "bun", "long", "slick", "messy", "curls"):
            sphere("HairCap", 0.7, (0, 0.1, 4.78), m, seg=16, rings=8, scale=(1.0, 0.98, 0.72 if style == "slick" else 0.85))
        if style == "bun":
            sphere("Bun", 0.36, (0, 0.5, 5.15), m, seg=12, rings=6)
        if style == "long":
            box("HairBack", (1.35, 0.5, 1.9), (0, 0.45, 4.1), m, bevel=0.15)
            for sx in (-1, 1):
                box(f"HairSide{sx}", (0.22, 0.9, 1.5), (sx * 0.66, 0.0, 4.15), m, bevel=0.08)
        if style == "messy":
            for k in range(9):
                a = k / 9 * 2 * math.pi
                cone(f"Spike{k}", 0.16, 0.0, 0.5, (math.cos(a) * 0.45, math.sin(a) * 0.4 + 0.1, 5.15), m, verts=5,
                     rot=(math.sin(a) * 0.7, -math.cos(a) * 0.7, 0))
        if style == "curls":
            for k in range(10):
                a = k / 10 * 2 * math.pi
                sphere(f"Curl{k}", 0.22, (math.cos(a) * 0.62, math.sin(a) * 0.55 + 0.1, 4.75 + 0.15 * math.sin(a * 2)), m, seg=8, rings=5)
    f.build("head", h)


def blazer(f, coat, shirt, tie, crest=True):
    def t():
        box("Blazer", (2.1, 1.1, 2.05), (0, 0, 3.0), coat, bevel=0.1)
        for sx in (-1, 1):
            strip(f"Lapel{sx}", [(sx * 0.25, -0.58, 3.98), (sx * 0.45, -0.6, 3.4), (sx * 0.3, -0.6, 2.7)], 0.28, (1, 0, 0), coat, thick=0.04)
        box("Shirt", (0.42, 0.04, 0.8), (0, -0.56, 3.6), shirt, bevel=0.01)
        strip("Tie", [(0, -0.6, 3.95), (0, -0.62, 3.4), (0, -0.6, 2.9)], 0.18, (1, 0, 0), tie, thick=0.03)
        if crest:
            box("Crest", (0.36, 0.04, 0.42), (-0.55, -0.58, 3.45), dye("crimson"), bevel=0.02)
            hoop("CrestRim", (-0.55, -0.6, 3.45), 0.17, "Y", dye("gold"), thick=0.02)
    f.build("torso", t)
    for side in (-1, 1):
        S.sleeve(f, side, coat, bell=1.0)


def skirt(f, m, w=2.6):
    f.build("torso", lambda: frustum("Skirt", (0, 0), w, 1.5, 0.9, 2.08, 1.1, 2.2, m, bevel=0.04))


def held(f, part, rest=(1.5, -0.2, 1.95)):
    return f.at(part, rest)


def candle_at(p, h=1.0, s=1.0, kind="candle"):
    lathe("CandleDish", [(0, 0), (0.32 * s, 0), (0.34 * s, 0.06 * s), (0.12 * s, 0.1 * s), (0, 0.1 * s)], dye("gold"), seg=16, loc=tuple(p))
    cyl("Candle", 0.13 * s, h * s, (p.x, p.y, p.z + 0.1 * s + h * s / 2), dye("bone"), verts=12, bevel=0.0)
    top = Vector((p.x, p.y, p.z + 0.1 * s + h * s))
    sphere("Flame", 0.1 * s, (top.x, top.y, top.z + 0.18 * s), dye("amber"), seg=10, rings=6, scale=(1, 1, 1.9))
    TR.glow_light((top.x, top.y - 0.5, top.z + 0.25 * s), 500 * s, (1.0, 0.62, 0.3), radius=0.2, kind=kind)
    return top


def torch_at(p, d, s=1.0):
    a, b = p - d * 0.8 * s, p + d * 2.4 * s
    tube("Torch", [tuple(a), tuple(b)], 0.11 * s, dye("soot"), poly=True)
    sphere("TorchHead", 0.22 * s, tuple(b), dye("rust"), seg=10, rings=6, scale=(1, 1, 1.4))
    for k in range(3):
        cone(f"TorchFlame{k}", 0.3 * s - k * 0.07 * s, 0.0, 0.9 * s - k * 0.1 * s, (b.x + (k - 1) * 0.12 * s, b.y, b.z + 0.55 * s), dye("torch"), verts=8)
    TR.glow_light((b.x, b.y - 0.8, b.z + 0.6 * s), 1400 * s, (1.0, 0.5, 0.2), radius=0.5, kind="torch")


def halo(f, m, r=1.0):
    f.build("head", lambda: hoop("Halo", (0, 0.65, 4.55), r, "Y", m, thick=0.09))


def hood(f, m):
    def h():
        sphere("Hood", 0.86, (0, 0.18, 4.6), m, seg=16, rings=8, scale=(1.0, 1.0, 1.08))
        cone("HoodTip", 0.4, 0.0, 0.7, (0, 0.55, 5.35), m, verts=10, rot=(-0.9, 0, 0))
        box("HoodDrape", (1.9, 1.2, 0.5), (0, 0.1, 4.0), m, bevel=0.2)
    f.build("head", h)


def whiskers(f, m):
    """Grey side-whiskers and a short pointed goatee (the tapestry beard hides an R6's whole face)."""
    def h():
        for sx in (-1, 1):
            box(f"Whisker{sx}", (0.16, 0.5, 0.62), (sx * 0.58, -0.12, 4.45), m, bevel=0.06)
        box("Moustache", (0.5, 0.08, 0.09), (0, -0.64, 4.36), m, bevel=0.03)
        cone("Goatee", 0.16, 0.0, 0.45, (0, -0.62, 4.05), m, verts=6, rot=(math.pi, 0, 0))
    f.build("head", h)


def coat_tails(f, m, z0=0.9):
    f.build("torso", lambda: frustum("CoatSkirt", (0, 0.05), 2.45, 1.35, z0, 2.12, 1.12, 2.3, m, bevel=0.03))


# ------------------------------------------------------------------ scenes (field origin: bottom centre)

def scene_headmaster_gallery():
    """Headmaster Corvin Ashgrave, full length: a black frock coat, a candlestick held at his heart, a silver-headed cane,
    a raven on a stone pedestal beside him."""
    soot, crim = dye("soot"), dye("crimsondk")
    f = fig((0.9, 0, 0.8), 1.95, {"rshoulder": (-55, 22, 0), "relbow": (-62, 0, 0), "lshoulder": (0, 10, 0), "lelbow": (-22, 0, 0),
                                  "neck": (-5, 0, 6), "waist": (0, 0, -5), "lhip": (-6, 0, 0), "rhip": (4, 0, 0)}, soot)
    f.build("torso", lambda: [box("Coat", (2.12, 1.12, 2.06), (0, 0, 3.0), soot, bevel=0.1),
                              box("Waistcoat", (0.9, 0.05, 1.6), (0, -0.58, 3.05), crim, bevel=0.02),
                              box("Cravat", (0.5, 0.08, 0.5), (0, -0.62, 3.75), dye("bone"), bevel=0.06),
                              tube("WatchChain", [(-0.4, -0.62, 3.0), (-0.1, -0.64, 2.8), (0.35, -0.62, 2.95)], 0.03, dye("gold"))] +
            [strip(f"Lapel{sx}", [(sx * 0.3, -0.6, 3.98), (sx * 0.52, -0.62, 3.3), (sx * 0.48, -0.62, 2.4)], 0.3, (1, 0, 0), soot, thick=0.04)
             for sx in (-1, 1)])
    coat_tails(f, soot, 0.55)
    for side in (-1, 1):
        S.sleeve(f, side, soot, bell=1.02)
    hair(f, dye("bonedk"), "slick")
    whiskers(f, dye("bonedk"))
    hp = held(f, "rshoulder", (1.5, -0.25, 1.85))
    candle_at(hp, h=0.9, s=1.1)
    lh = held(f, "lshoulder", (-1.5, -0.2, 1.95))
    tube("Cane", [tuple(lh), (lh.x - 0.2, lh.y - 0.1, 0.9)], 0.09, soot, poly=True)
    sphere("CaneKnob", 0.22, tuple(lh + Vector((0, 0, 0.18))), dye("bonedk"), seg=12, rings=6)
    box("Pedestal", (1.5, 1.5, 5.2), (-3.0, 1.5, 0.8 + 2.6), dye("sootlt"), bevel=0.08)
    box("PedestalCap", (1.9, 1.9, 0.3), (-3.0, 1.5, 6.15), dye("sootlt"), bevel=0.06)
    raven("RavenPed", (-3.0, 1.2, 6.3), -math.pi / 2 + 0.6, 7.5, soot, dye("ink"))


def scene_headmistress():
    """Headmistress Isolde Morrow, half length: a high-necked crimson gown, a lace collar, a cameo, spectacles, a black book
    held at her waist, keys on a chatelaine."""
    g = dye("crimsondk")
    f = fig((0, 0, -5.1), 3.4, {"rshoulder": (-38, 0, -14), "relbow": (-62, 0, -28), "lshoulder": (-38, 0, 14), "lelbow": (-62, 0, 28),
                                "neck": (-4, 0, -9), "waist": (0, 0, 4)}, g, face="stern")
    f.build("torso", lambda: [box("Bodice", (2.1, 1.1, 2.05), (0, 0, 3.0), g, bevel=0.1),
                              box("HighCollar", (1.0, 1.0, 0.45), (0, 0, 4.12), dye("bone"), bevel=0.12),
                              cyl("Cameo", 0.2, 0.08, (0, -0.6, 3.7), dye("bone"), rot=(math.pi / 2, 0, 0), verts=20, bevel=0.02),
                              hoop("CameoRim", (0, -0.65, 3.7), 0.21, "Y", dye("gold"), thick=0.03),
                              tube("Chatelaine", [(0.5, -0.6, 2.4), (0.55, -0.66, 2.0), (0.52, -0.62, 1.6)], 0.03, dye("gold"))] +
            [hoop(f"Ruff{k}", (0, 0, 3.98 + k * 0.08), 0.62 - k * 0.04, "Z", dye("bone"), thick=0.06) for k in range(3)])
    for side in (-1, 1):
        S.sleeve(f, side, g, bell=1.12)
    hair(f, dye("soot"), "bun")

    def specs():
        for sx in (-1, 1):
            hoop(f"Lens{sx}", (sx * 0.22, -0.63, 4.6), 0.14, "Y", dye("gold"), thick=0.022)
        tube("Bridge", [(-0.08, -0.64, 4.62), (0, -0.66, 4.64), (0.08, -0.64, 4.62)], 0.015, dye("gold"))
    f.build("head", specs)
    a, b = held(f, "rshoulder"), held(f, "lshoulder")
    c = (a + b) / 2
    box("Book", (1.6, 0.5, 1.15), tuple(c + Vector((0, -0.3, 0.2))), dye("ink"), bevel=0.06)
    box("BookClasp", (0.2, 0.1, 0.4), tuple(c + Vector((0.75, -0.55, 0.2))), dye("gold"), bevel=0.02)
    hoop("BookBoss", tuple(c + Vector((0, -0.56, 0.2))), 0.22, "Y", dye("gold"), thick=0.03)


def scene_cursed_student():
    """A student in the school blazer, head bowed, eyes lit a ghostly pale; two ghost hands reach over his shoulders."""
    f = fig((0, 0, -5.1), 3.4, {"rshoulder": (4, -6, 0), "lshoulder": (4, 6, 0), "neck": (16, 0, -8), "waist": (4, 0, 0)}, dye("ink"),
            face="sorrow")
    blazer(f, dye("ink"), dye("bone"), dye("crimson"))
    hair(f, dye("soot"), "messy")
    TR.glow_eyes(f, dye("spirit"), y=-0.63)
    # the ghost's arms from behind, reaching over his shoulders, long fingers spread on them
    for side in (-1, 1):
        sh = f.at("torso", (side * 0.75, -0.5, 4.1))
        d = Vector((side * -0.75, -0.3, -0.55)).normalized()
        L = 5.2
        s = _mark()
        box(f"GhostArm{side}", (0.95, 0.95, L), (0, 0, L / 2), dye("ghost"), bevel=0.25)
        for k in range(4):
            box(f"GhostFinger{side}{k}", (0.15, 0.15, 1.7), ((k - 1.5) * 0.24, -0.1, -0.75), dye("ghost"), bevel=0.06)
        rot = Vector((0, 0, -1)).rotation_difference(d).to_matrix().to_4x4()
        _xform(s, Matrix.Translation(sh) @ rot)


def scene_countess():
    """Countess Vesperine of the Crimson Court, half length: black hair, a high collar lined in crimson, a cape, red eyes, a
    garnet pendant, a gilt goblet raised."""
    f = fig((0, 0, -4.7), 3.2, {"rshoulder": (-35, 0, 0), "relbow": (-75, 0, -35), "lshoulder": (-10, 6, 0), "neck": (-6, 0, 12), "waist": (0, 0, -6)},
            dye("soot"), skin_k="bone", face="stern")
    f.build("torso", lambda: [box("Gown", (2.1, 1.1, 2.05), (0, 0, 3.0), dye("soot"), bevel=0.1),
                              S.sphere("Bodice", 0.7, (0, -0.42, 3.0), dye("crimson"), seg=14, rings=7, scale=(1.1, 0.25, 1.3)),
                              tube("Necklace", [(-0.5, -0.56, 3.98), (-0.2, -0.62, 3.6), (0, -0.64, 3.5), (0.2, -0.62, 3.6), (0.5, -0.56, 3.98)], 0.03, dye("gold")),
                              S.sphere("Garnet", 0.14, (0, -0.68, 3.42), dye("crimsonlt"), seg=10, rings=6)])
    for side in (-1, 1):
        S.sleeve(f, side, dye("soot"), bell=1.2)
    TR.high_collar(f, dye("soot"), dye("crimson"))
    TR.cape(f, dye("soot"), dye("crimson"), flare=2.5, hem=0.2)
    hair(f, dye("soot"), "long")
    TR.glow_eyes(f, dye("ember"), y=-0.63)
    hp = held(f, "rshoulder", (1.5, -0.25, 1.9))
    lathe("Goblet", [(0, 0), (0.3, 0), (0.08, 0.1), (0.07, 0.5), (0.36, 0.7), (0.42, 1.15), (0, 1.15)], dye("gold"), seg=20, loc=tuple(hp))
    lathe("Wine", [(0, 1.05), (0.38, 1.05), (0, 1.08)], dye("crimsonlt"), seg=20, loc=tuple(hp))


def _dancer(x, y, yaw, man, gown, s=1.25, lead=1):
    if man:
        f = fig((x, y, 0.5), s, {"lshoulder": (0, 75, 0), "lelbow": (0, 40, 0), "rshoulder": (-75, 0, -20), "relbow": (-30, 0, 0),
                                 "neck": (0, 0, 10 * lead), "lhip": (-12, 0, 0), "rhip": (14, 0, 0)}, dye("soot"), skin_k="bone", yaw=yaw)
        f.build("torso", lambda: [box("Tailcoat", (2.12, 1.12, 2.06), (0, 0, 3.0), dye("soot"), bevel=0.1),
                                  box("Shirtfront", (0.5, 0.05, 0.9), (0, -0.58, 3.5), dye("bone"), bevel=0.02)])
        coat_tails(f, dye("soot"), 1.3)
        for side in (-1, 1):
            S.sleeve(f, side, dye("soot"), bell=1.0)
        TR.cape(f, dye("soot"), gown, flare=1.8, hem=1.0, name="DanceCape")
        hair(f, dye("soot"), "slick")
    else:
        f = fig((x, y, 0.5), s * 0.96, {"rshoulder": (0, -75, 0), "relbow": (0, -40, 0), "lshoulder": (-70, 0, 20), "lelbow": (-40, 0, 0),
                                        "neck": (6, 0, -12 * lead), "waist": (0, 0, 8)}, gown, skin_k="bone", yaw=yaw,
                parts=("head", "torso", "rarm", "larm"))
        f.build("torso", lambda: [frustum("BallGown", (0, 0), 3.6, 2.6, 0.02, 2.05, 1.08, 2.2, gown, bevel=0.04),
                                  frustum("GownTier", (0, 0), 3.2, 2.3, 0.7, 2.2, 1.2, 1.6, dye("bone") if gown != dye("bone") else dye("crimson"), bevel=0.03),
                                  box("Bodice", (2.08, 1.08, 2.0), (0, 0, 3.0), gown, bevel=0.1)])
        hair(f, dye("soot") if lead > 0 else dye("rust"), "bun")
    return f


def scene_vampire_ball():
    """The Crimson Court's midnight ball: three couples whirl under a blazing chandelier, the vampire host spreads his cape
    on the dais, his eyes alight."""
    host = fig((0, 5.0, 2.4), 1.55, {"rshoulder": (0, -105, 0), "relbow": (0, -20, 0), "lshoulder": (0, 105, 0), "lelbow": (0, 20, 0), "neck": (-8, 0, 0)},
               dye("soot"), skin_k="bone", face="fierce")
    TR.cape(host, dye("soot"), dye("crimson"), flare=3.6, hem=0.1, name="HostCape")
    TR.high_collar(host, dye("soot"), dye("crimson"))
    TR.glow_eyes(host, dye("ember"), y=-0.63)
    hair(host, dye("soot"), "slick")
    box("Dais", (12, 4, 1.9), (0, 6.0, 1.45), dye("crimsondk"), bevel=0.1)
    box("DaisStep", (13, 4.5, 0.5), (0, 5.4, 0.75), dye("soot"), bevel=0.06)
    for x, y, gown, lead in ((-8.4, 0.0, dye("crimson"), 1), (-1.4, -1.2, dye("bone"), -1), (6.4, 0.4, dye("plum"), 1)):
        _dancer(x - 1.1, y, math.radians(90 - 28), True, gown, lead=lead)
        _dancer(x + 1.1, y, math.radians(-90 - 28), False, gown, lead=lead)
    # the chandelier
    cz = 12.6
    tube("ChanChain", [(0, 3, 13.6), (0, 3, cz + 0.6)], 0.06, dye("golddk"), poly=True)
    hoop("ChanRing", (0, 3, cz), 2.4, "Z", dye("gold"), thick=0.12)
    hoop("ChanRing2", (0, 3, cz - 0.6), 1.3, "Z", dye("gold"), thick=0.1)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        p = Vector((math.cos(a) * 2.4, 3 + math.sin(a) * 2.4, cz + 0.05))
        candle_at(p, h=0.5, s=0.8, kind="chandelier")
        tube(f"ChanDrop{k}", [(p.x, p.y, cz - 0.1), (p.x * 0.6, 3 + (p.y - 3) * 0.6, cz - 1.0)], 0.03, dye("gold"))


def scene_class_1887():
    """The Class of 1887 sat for their portrait: five standing behind, four on the bench, the Headmaster to one side, and
    one of the five who should not be there, pale and see-through."""
    s = 1.15
    box("Bench", (12.5, 1.6, 0.4), (-0.3, -1.0, 2.4), dye("rust"), bevel=0.05)
    for sx in (-1, 1):
        box(f"BenchLeg{sx}", (0.4, 1.4, 2.0), (-0.3 + sx * 5.6, -1.0, 1.2), dye("rust"), bevel=0.04)
    box("Riser", (17, 2.0, 1.8), (-0.3, 1.6, 0.9), dye("soot"), bevel=0.05)
    styles = ["short", "bun", "curls", "long", "messy"]
    for k, x in enumerate((-6.0, -3.0, 0.0, 3.0, 6.0)):
        ghost = k == 3
        coat = dye("ghost") if ghost else (dye("ink") if k % 2 == 0 else dye("crimsondk"))
        pose = {"neck": (0, 0, (k - 2) * 4), "rshoulder": (0, -4, 0), "lshoulder": (0, 4, 0)}
        if k == 1:
            pose.update({"rshoulder": (-50, 0, -20), "relbow": (-80, 0, -40), "lshoulder": (-50, 0, 20), "lelbow": (-80, 0, 40)})
        if k == 4:
            pose.update({"lshoulder": (0, -30, 0)})          # a hand on his neighbour's shoulder
        f = fig((x, 1.6, 1.8), s, pose, coat, skin_k="ghost" if ghost else "cream", face="sorrow" if ghost else ("smile" if k == 2 else "stern"),
                legs=dye("ghost") if ghost else dye("soot"))
        if not ghost:
            blazer(f, coat, dye("bone"), dye("crimson") if k % 2 == 0 else dye("gold"))
            if styles[k] in ("bun", "long", "curls"):
                skirt(f, dye("soot"))
        hair(f, dye("ghost") if ghost else (dye("soot") if k % 2 else dye("rust")), styles[k])
    for k, x in enumerate((-4.6, -1.6, 1.4, 4.4)):
        f = fig((x, -1.0, 2.6 - 2 * s), s, {"lhip": (-90, 0, 0), "rhip": (-90, 0, 0), "lknee": (90, 0, 0), "rknee": (90, 0, 0),
                                            "rshoulder": (-40, 0, -10), "relbow": (-40, 0, 0), "lshoulder": (-40, 0, 10), "lelbow": (-40, 0, 0),
                                            "neck": (0, 0, (k - 1.5) * -5)}, dye("ink") if k % 2 else dye("crimsondk"), face="smile" if k == 1 else "stern",
                legs=dye("soot"))
        blazer(f, dye("ink") if k % 2 else dye("crimsondk"), dye("bone"), dye("gold"))
        hair(f, dye("rust") if k == 2 else dye("soot"), ["short", "bun", "short", "long"][k])
    hm = fig((8.6, 0.0, 0.0), 1.3, {"lshoulder": (-30, 0, 30), "lelbow": (-40, 0, 0), "neck": (-4, 0, -10)}, dye("soot"), parts=("head", "torso", "rarm", "larm"))
    S.robe(hm, dye("soot"))
    for side in (-1, 1):
        S.sleeve(hm, side, dye("soot"), bell=1.15)
    TR.mortarboard(hm, dye("ink"), dye("gold"))
    TR.beard(hm, dye("bonedk"), long=1.0)


def scene_wolf_hunt_snow():
    """Hunters with torches file into a snowbound pine wood, their backs to us; on the ridge above, the werewolf crouches,
    watching them, its eyes alight."""
    for k, (x, y, s, coat) in enumerate(((2.0, -1.0, 1.55, dye("moss")), (5.2, 1.0, 1.32, dye("crimsondk")), (7.6, 2.6, 1.12, dye("rust")),
                                         (9.4, 3.8, 0.95, dye("slate")))):
        side = 1 if k % 2 else -1
        f = fig((x, y, 0.6 + k * 0.7), s, {"rhip": (-22, 0, 0), "lhip": (18, 0, 0), "lknee": (30, 0, 0), "lshoulder": (-150, 10, 0),
                                           "lelbow": (-10, 0, 0), "rshoulder": (20, 0, 0), "neck": (0, 0, 15 * side)}, coat, yaw=math.pi + 0.25,
                legs=dye("soot"))
        f.build("torso", lambda coat=coat: [box("HuntCoat", (2.15, 1.15, 2.1), (0, 0, 3.0), coat, bevel=0.1),
                                             frustum("HuntSkirt", (0, 0), 2.5, 1.5, 1.1, 2.15, 1.15, 2.2, coat),
                                             box("Belt", (2.2, 1.2, 0.2), (0, 0, 2.2), dye("soot"), bevel=0.04)])
        TR.cape(f, dye("soot"), coat, flare=1.7, hem=1.4, name="HuntCapelet")
        for side2 in (-1, 1):
            S.sleeve(f, side2, coat, bell=1.05)
        f.build("head", lambda: [box("HatBrim", (1.9, 1.9, 0.1), (0, 0, 5.1), dye("soot"), bevel=0.02),
                                 frustum("HatCrown", (0, 0), 1.2, 1.2, 5.1, 1.0, 1.0, 6.0, dye("soot"))])
        a = f.at("lshoulder", (-1.5, 0, 2.0))
        d = (f.at("lshoulder", (-1.5, 0, 1.0)) - f.at("lshoulder", (-1.5, 0, 2.6))).normalized()
        torch_at(a, d, s=s * 0.8)
    w = fig((-7.0, 6.0, 4.6), 1.65, {"waist": (24, 0, 0), "root": (8, 0, 0), "rhip": (-60, 0, 0), "rknee": (100, 0, 0), "lhip": (-20, 0, 0),
                                    "lknee": (60, 0, 0), "rshoulder": (-80, 0, -10), "relbow": (-20, 0, 0), "lshoulder": (-40, 0, 10), "neck": (-26, 0, 0)},
            dye("slate"), skin_k="slate", face=None, yaw=math.radians(25))
    TR.bulk(w, dye("slate"))
    TR.wolf_head(w, dye("slate"), dye("soot"), dye("bone"))
    w.build("torso", lambda: tube("WolfTail", [(0, 0.5, 2.1), (0.4, 1.3, 1.6), (1.1, 1.6, 1.0)], 0.28, dye("slate")))
    TR.claws(w, dye("bone"))


def scene_procession():
    """A candlelit procession of the Chapel Choir and the Vigil over the bridge at midnight: hooded figures with lanterns
    on poles, the cantor with the crescent staff leading."""
    for k in range(6):
        x = 9.0 - k * 3.4
        robe = dye("bone") if k % 2 == 0 else dye("ink")
        step = 18 if k % 2 else -18
        f = fig((x, 0.4 * (k % 2), 0.4), 1.3, {"rhip": (-step, 0, 0), "lhip": (step, 0, 0), "rshoulder": (-70, 0, 0), "relbow": (-30, 0, 0),
                                               "lshoulder": (-45, 0, 0), "lelbow": (-60, 0, 0), "neck": (10, 0, 0)}, robe, yaw=math.radians(90),
                parts=("head", "torso", "rarm", "larm"), face="sing" if k % 2 == 0 else "sorrow")
        S.robe(f, robe, w0=2.7, d0=1.9)
        for side in (-1, 1):
            S.sleeve(f, side, robe, bell=1.25)
        hood(f, robe)
        if k == 0:
            hp = f.at("rshoulder", (1.5, -0.2, 2.0))
            TR.crescent_staff(hp.x, hp.y, 0.4, hp.z + 3.2, dye("gold"))
        else:
            TR.lantern_pole(f, "rshoulder", 1, dye("gold"), dye("amber"), s=0.9)
        cp = f.at("lshoulder", (-1.5, -0.3, 1.9))
        candle_at(cp, h=0.5, s=0.7)


def _icon(robe, stole, item, face="stern", skin_k="cream"):
    f = fig((0, 0, 0.4), 1.75, {"rshoulder": (-28, 0, -12), "relbow": (-58, 0, -30), "lshoulder": (-28, 0, 12), "lelbow": (-58, 0, 30)} if item != "key" else
            {"rshoulder": (0, -150, 0), "relbow": (0, -10, 0), "lshoulder": (-50, 0, 18), "lelbow": (-60, 0, 20)}, robe, skin_k=skin_k, face=face,
            parts=("head", "torso", "rarm", "larm"))
    S.robe(f, robe, w0=2.9, d0=1.9)
    for side in (-1, 1):
        S.sleeve(f, side, robe, bell=1.25)
    f.build("torso", lambda: [strip(f"Stole{sx}", [(sx * 0.36, -0.6, 4.0), (sx * 0.42, -0.7, 2.6), (sx * 0.46, -0.98, 0.3)], 0.34, (1, 0, 0), stole, thick=0.04)
                              for sx in (-1, 1)])
    halo(f, dye("gold"), r=1.05)
    a, b = f.at("rshoulder", (1.5, -0.25, 1.95)), f.at("lshoulder", (-1.5, -0.25, 1.95))
    c = (a + b) / 2
    if item == "candle":
        candle_at(c + Vector((0, -0.2, 0)), h=0.9, s=1.0)
    elif item == "book":
        box("HymnL", (1.0, 0.08, 1.3), tuple(c + Vector((-0.5, -0.3, 0.3))), dye("bone"), bevel=0.02, rot=(0, 0, 0.3))
        box("HymnR", (1.0, 0.08, 1.3), tuple(c + Vector((0.5, -0.3, 0.3))), dye("bone"), bevel=0.02, rot=(0, 0, -0.3))
        box("HymnCover", (2.2, 0.06, 1.4), tuple(c + Vector((0, -0.2, 0.3))), dye("crimsondk"), bevel=0.02)
    else:
        TR.great_key(f, "rshoulder", 1, dye("gold"), dye("holy"))
        box("FounderBook", (1.0, 0.6, 1.3), tuple(b + Vector((0, -0.3, 0.2))), dye("crimsondk"), bevel=0.05)
    return f


def scene_icon_vigil():
    f = _icon(dye("ink"), dye("gold"), "candle", face="sorrow")
    hair(f, dye("rust"), "long")


def scene_icon_founder():
    f = _icon(dye("crimsondk"), dye("bone"), "key")
    TR.beard(f, dye("bone"), long=1.3)
    hair(f, dye("bone"), "short")


def scene_icon_cantor():
    f = _icon(dye("bone"), dye("crimson"), "book", face="sing")
    hair(f, dye("soot"), "short")


def _mini(body, skin_k, face, style, hairc, extra=None, pose=None):
    f = fig((0, 0, -8.6), 3.0, pose or {"neck": (-4, 0, 14), "waist": (0, 0, -8)}, body, skin_k=skin_k, face=face, parts=("head", "torso", "rarm", "larm"))
    hair(f, hairc, style)
    if extra:
        extra(f)


def scene_mini_vampire():
    def x(f):
        TR.high_collar(f, dye("soot"), dye("crimson"))
        TR.glow_eyes(f, dye("ember"), y=-0.63)
        f.build("torso", lambda: box("Jabot", (0.45, 0.1, 0.6), (0, -0.6, 3.7), dye("bone"), bevel=0.08))
    _mini(dye("soot"), "bone", "stern", "slick", dye("soot"), x)


def scene_mini_wolf_girl():
    def x(f):
        f.build("head", lambda: [cone(f"WolfEar{sx}", 0.22, 0.0, 0.55, (sx * 0.42, 0.05, 5.25), dye("rust"), verts=4, rot=(0.15, sx * -0.3, 0)) for sx in (-1, 1)])
        TR.glow_eyes(f, dye("amber"), y=-0.63)
        f.build("torso", lambda: [box("Collar", (1.3, 1.1, 0.25), (0, 0, 3.95), dye("soot"), bevel=0.06)])
    _mini(dye("moss"), "cream", "fierce", "curls", dye("rust"), x)


def scene_mini_choir_boy():
    def x(f):
        f.build("torso", lambda: [hoop(f"ChoirRuff{k}", (0, 0, 3.95 + k * 0.07), 0.8 - k * 0.06, "Z", dye("bone"), thick=0.07) for k in range(3)])
    _mini(dye("crimson"), "cream", "sing", "short", dye("gold"), x)


def scene_mini_court_girl():
    def x(f):
        f.build("head", lambda: [S.sphere(f"Bow{sx}", 0.28, (sx * 0.3, 0.3, 5.3), dye("crimson"), seg=10, rings=6, scale=(1.3, 0.5, 0.9)) for sx in (-1, 1)])
        f.build("torso", lambda: [tube("Pearls", [(-0.5, -0.56, 3.98), (-0.25, -0.62, 3.65), (0, -0.64, 3.55), (0.25, -0.62, 3.65), (0.5, -0.56, 3.98)], 0.05,
                                       dye("bone"))])
    _mini(dye("plum"), "bone", "smile", "long", dye("soot"), x)


def scene_mini_professor():
    def x(f):
        whiskers(f, dye("bonedk"))
        f.build("head", lambda: [hoop(f"PLens{sx}", (sx * 0.22, -0.64, 4.6), 0.14, "Y", dye("gold"), thick=0.022) for sx in (-1, 1)])
        f.build("torso", lambda: box("ProfCollar", (0.5, 0.08, 0.4), (0, -0.6, 3.8), dye("bone"), bevel=0.05))
    _mini(dye("sootlt"), "cream", "stern", "short", dye("bonedk"), x)


# name -> (builder, field w, h (scene units), px w, h, lights)
SCENES = {
    "HeadmasterGallery": (scene_headmaster_gallery, 9, 16, 1152, 2048, dict(moon=((0.6, -0.4, -0.5), 2.0), fill=0.09)),
    "Headmistress": (scene_headmistress, 12, 16, 1536, 2048, dict(moon=((-0.6, -0.4, -0.5), 1.8), fill=0.1)),
    "CursedStudent": (scene_cursed_student, 12, 16, 1536, 2048, dict(moon=((0.3, -0.5, -0.6), 2.4), fill=0.08)),
    "Countess": (scene_countess, 12, 16, 1536, 2048, dict(moon=((0.6, -0.3, -0.5), 2.0), fill=0.08)),
    "VampireBall": (scene_vampire_ball, 24, 13.5, 2048, 1152, dict(moon=((-0.4, -0.5, -0.6), 1.2), fill=0.1)),
    "Class1887": (scene_class_1887, 20, 14, 2048, 1434, dict(moon=((0.2, -0.6, -0.5), 1.8), fill=0.14)),
    "WolfHuntSnow": (scene_wolf_hunt_snow, 24, 13.5, 2048, 1152, dict(moon=((-0.5, 0.4, -0.5), 2.2), fill=0.1)),
    "Procession": (scene_procession, 24, 11.3, 2048, 964, dict(moon=((0.5, 0.3, -0.6), 1.8), fill=0.08)),
    "IconVigil": (scene_icon_vigil, 6, 10, 820, 1366, dict(moon=((0.2, -0.6, -0.6), 1.6), fill=0.16)),
    "IconFounder": (scene_icon_founder, 6, 10, 820, 1366, dict(moon=((0.2, -0.6, -0.6), 1.6), fill=0.16)),
    "IconCantor": (scene_icon_cantor, 6, 10, 820, 1366, dict(moon=((0.2, -0.6, -0.6), 1.6), fill=0.16)),
    "MiniVampire": (scene_mini_vampire, 6, 8, 768, 1024, dict(moon=((0.6, -0.4, -0.5), 2.0), fill=0.1)),
    "MiniWolfGirl": (scene_mini_wolf_girl, 6, 8, 768, 1024, dict(moon=((-0.6, -0.4, -0.5), 2.0), fill=0.1)),
    "MiniChoirBoy": (scene_mini_choir_boy, 6, 8, 768, 1024, dict(moon=((0.6, -0.4, -0.5), 2.0), fill=0.1)),
    "MiniCourtGirl": (scene_mini_court_girl, 6, 8, 768, 1024, dict(moon=((-0.6, -0.4, -0.5), 2.0), fill=0.1)),
    "MiniProfessor": (scene_mini_professor, 6, 8, 768, 1024, dict(moon=((0.6, -0.4, -0.5), 2.0), fill=0.1)),
}


def _mask(white):
    m = bpy.data.materials.new("MaskWhite" if white else "MaskBlack")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1) if white else (0, 0, 0, 1)
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def render(name):
    builder, fw, fh, rx, ry, cfg = SCENES[name]
    sc = P.reset()
    P.PARTS[:] = []
    TR._mats.clear()
    POINTS.clear()
    builder()
    for ob in P.PARTS:                      # apply the bevels etc. now, so the mask passes see the same shapes
        pass
    cam = bpy.data.cameras.new("Cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(fw, fh)
    co = bpy.data.objects.new("Cam", cam)
    bpy.context.collection.objects.link(co)
    co.location = (0, -60, fh / 2)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.35, 0.4, 0.75, 1)
    bg.inputs["Strength"].default_value = cfg["fill"]
    d, e = cfg["moon"]
    L = bpy.data.lights.new("Moon", "SUN")
    L.energy = e
    L.color = (0.72, 0.8, 1.0)
    L.angle = math.radians(6)
    lo = bpy.data.objects.new("Moon", L)
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = (Vector(d) * -1).to_track_quat("Z", "Y").to_euler()
    K = bpy.data.lights.new("Key", "AREA")
    K.energy = 2600 * (max(fw, fh) / 20) ** 2
    K.size = max(fw, fh) * 0.7
    K.color = (1.0, 0.82, 0.62)
    ko = bpy.data.objects.new("Key", K)
    bpy.context.collection.objects.link(ko)
    ko.location = (-fw * 0.4, -max(fw, fh) * 1.3, fh * 0.8)
    ko.rotation_euler = (Vector((0, 0, fh * 0.45)) - ko.location).to_track_quat("-Z", "Y").to_euler()
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    sc.render.filepath = os.path.join(OUT, f"{name}_beauty.png")
    bpy.ops.render.render(write_still=True)
    white, black = _mask(True), _mask(False)
    keep = {}
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            keep[ob.name] = [s.material for s in ob.material_slots]
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.hide_render = True
    bg.inputs["Strength"].default_value = 0.0
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.cycles.samples = 8
    sc.cycles.use_denoising = False
    for kind, keys in (("gilt", TR.GILT), ("ghost", GHOST)):
        for ob in bpy.data.objects:
            if ob.type == "MESH":
                for slot, orig in zip(ob.material_slots, keep[ob.name]):
                    slot.material = white if (orig is not None and orig.get("dye") in keys) else black
        sc.render.filepath = os.path.join(OUT, f"{name}_{kind}.png")
        bpy.ops.render.render(write_still=True)
    k_ = max(rx, ry) / max(fw, fh)
    pts = {k: [(rx / 2 + x * k_, ry - z * k_) for x, y, z in v] for k, v in POINTS.items()}
    with open(os.path.join(OUT, f"{name}_points.json"), "w") as f:
        json.dump(pts, f)
    print(f"[art41] {name} rendered")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in argv if a in SCENES] or list(SCENES)
    for n in names:
        try:
            render(n)
        except Exception:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print(f"[art41] {name if False else n} FAILED")
