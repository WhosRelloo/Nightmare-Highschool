"""The figures for props batch 29's tapestries, posed in Blender on the statue kit's R6 rig (nh_props_batch27.R6) and
rendered from the front for tapestry_weave.py to paint and weave:

  <Scene>_beauty.png  the figures lit like the art kit's paintings: a cool moon rim, warm lantern light, a candlelit key,
                      velvet sheen on the cloth, real gilt, glowing lantern glass and demon eyes
  <Scene>_gilt.png    a mask of the gilt parts (the weaver's gilt thread and metal map)
  <Scene>_points.json the glow sources in px (lanterns, the fires below, the light above), for the painted halos

The images are RGBA with a transparent background, the size of the tapestry's field, into art/props/source_tapestry/.

  "E:/Blender/blender.exe" -b --factory-startup --python art/props/tapestry_renders.py -- [Scene ...] --gpu

Scenes (originals): Headmaster, PriestDemon, AngelDemon, Judgement, WolfHunt.
"""
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
from nh_props_batch4 import hoop, strip, _mark, _xform, _mesh  # noqa: E402
from nh_props_batch9 import raven  # noqa: E402
from nh_props_batch12 import frustum, sheet  # noqa: E402
import nh_props_batch20 as B20  # noqa: E402
import nh_props_batch27 as S  # noqa: E402
import window_shapes as WS  # noqa: E402
from weave_dyes import C  # noqa: E402

OUT = os.path.join(HERE, "source_tapestry")
os.makedirs(OUT, exist_ok=True)

# field sizes (scene units, px): portrait tapestries 15 x 20, the hunt frieze 24 x 13.5
FIELD = {"Headmaster": (15, 20, 1536, 2048), "PriestDemon": (15, 20, 1536, 2048), "AngelDemon": (15, 20, 1536, 2048),
         "Judgement": (15, 20, 1536, 2048), "WolfHunt": (24, 11.3, 2048, 964)}

_mats = {}
POINTS = {}          # glow sources the weaver paints halos round: kind -> [world positions]
GILT = ("gold", "golddk")
GLOW = {"amber": 14.0, "holy": 22.0, "ember": 16.0, "spirit": 12.0}
VELVET = ("soot", "crimson", "crimsondk", "crimsonlt", "ink", "inklt", "moss", "plum", "bone", "cream", "slate", "rust")


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def dye(name):
    """The lit material for one dye: cloth with a velvet sheen, gilt metal, or a glow (lantern glass, demon eyes).
    The dye key is kept on the material (the gilt mask pass reads it)."""
    if name not in _mats:
        m = bpy.data.materials.new(f"Dye_{name}")
        m["dye"] = name
        m.use_nodes = True
        nt = m.node_tree
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        rgb = tuple(_lin(v) for v in C[name]) + (1,)
        bs.inputs["Base Color"].default_value = rgb
        if name in GILT:
            bs.inputs["Metallic"].default_value = 0.7        # gilt that still catches the warm key, not only the night
            bs.inputs["Roughness"].default_value = 0.42
        elif name in GLOW:
            bs.inputs["Emission Color"].default_value = rgb
            bs.inputs["Emission Strength"].default_value = GLOW[name]
        else:
            bs.inputs["Roughness"].default_value = 0.72
            if name in VELVET:
                bs.inputs["Sheen Weight"].default_value = 0.6
                bs.inputs["Sheen Roughness"].default_value = 0.4
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 6.0
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.12
            nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
        _mats[name] = m
    return _mats[name]


def glow_light(pos, energy, color, radius=0.4, kind="lantern"):
    L = bpy.data.lights.new(kind, "POINT")
    L.energy = energy
    L.color = color
    L.shadow_soft_size = radius
    o = bpy.data.objects.new(kind, L)
    o.location = pos
    bpy.context.collection.objects.link(o)
    POINTS.setdefault(kind, []).append(tuple(pos))


# ------------------------------------------------------------------ figure pieces

def beard(fig, m, long=1.2):
    def f():
        B20.tprism("Beard", WS.ccw([(-0.5, 4.32), (0.5, 4.32), (0.42, 4.0), (0.15, 4.0 - long), (0.0, 3.9 - long), (-0.15, 4.0 - long), (-0.42, 4.0)]), -0.66, 0.12, m)
        box("Moustache", (0.6, 0.08, 0.1), (0, -0.66, 4.36), m, bevel=0.03)
        for sx in (-1, 1):
            box(f"Brow{sx}", (0.34, 0.07, 0.08), (sx * 0.22, -0.62, 4.8), m, bevel=0.02, rot=(0, sx * 0.25, 0))
    fig.build("head", f)


def horns(fig, m, big=1.0):
    def f():
        for sx in (-1, 1):
            tube(f"Horn{sx}", [(sx * 0.45, 0.0, 5.0), (sx * 0.85 * big, 0.05, 5.45), (sx * 1.0 * big, 0.1, 6.0), (sx * 0.8 * big, 0.12, 6.45)], 0.12 * big, m)
            cone(f"HornTip{sx}", 0.1 * big, 0.0, 0.35, (sx * 0.78 * big, 0.12, 6.6), m, verts=8, rot=(0, sx * -0.4, 0))
    fig.build("head", f)


def demon_face(fig, eyes, mouth, fang):
    def f():
        for sx in (-1, 1):
            B20.tprism(f"Eye{sx}", WS.ccw([(sx * 0.08, 4.62), (sx * 0.38, 4.7), (sx * 0.32, 4.56)]), -0.61, 0.03, eyes)
        B20.tprism("Grin", WS.ccw([(-0.4, 4.36), (0.4, 4.36), (0.25, 4.2), (-0.25, 4.2)]), -0.61, 0.03, mouth)
        for k in range(4):
            cone(f"Fang{k}", 0.05, 0.0, 0.14, (-0.24 + k * 0.16, -0.63, 4.3), fang, verts=4, rot=(math.pi, 0, 0))
    fig.build("head", f)


def tail(fig, m, tip):
    def f():
        tube("Tail", [(0, 0.5, 2.1), (0.3, 1.4, 1.4), (1.2, 1.7, 0.6), (2.0, 1.4, 0.5), (2.5, 1.2, 1.1)], 0.12, m)
        B20.tprism("TailTip", WS.ccw([(2.45, 1.0), (2.8, 1.35), (2.45, 1.7), (2.3, 1.35)]), 1.2, 0.06, tip)
    fig.build("torso", f)


def bat_wings(fig, m, bone, span=3.6, raise_=30):
    for side in (-1, 1):
        mt = Matrix.Translation((side * 0.6, 0.55, 3.7)) @ Matrix.Rotation(side * -0.35, 4, "Z") @ Matrix.Rotation(math.radians(raise_), 4, "X")
        if side < 0:
            mt = mt @ Matrix.Rotation(math.pi, 4, "Z")
        fig.build("torso", lambda mt=mt, side=side: S.wing(f"BatWing{side}", mt, m, span=span, bat=True, dark=bone))


def feather_wings(fig, m, span=4.2):
    for side in (-1, 1):
        mt = Matrix.Translation((side * 0.5, 0.6, 3.8)) @ Matrix.Rotation(side * -0.25, 4, "Z") @ Matrix.Rotation(math.radians(12), 4, "X")
        if side < 0:
            mt = mt @ Matrix.Rotation(math.pi, 4, "Z")
        fig.build("torso", lambda mt=mt, side=side: S.wing(f"Wing{side}", mt, m, span=span, n=8))


def claws(fig, m):
    for side in (-1, 1):
        S.claws(fig, side, m)


def lantern(x, y, z, frame, glow, s=1.0):
    """A hand lantern hanging from (x, y, z): a gilt frame, a lit pane."""
    tube("LanternBail", [(x, y, z), (x, y, z - 0.2 * s)], 0.03 * s, frame, poly=True)
    lz = z - 1.1 * s
    box("LanternGlow", (0.5 * s, 0.5 * s, 0.7 * s), (x, y, lz + 0.42 * s), glow, bevel=0.0, segments=1)
    glow_light((x, y - 0.6 * s, lz + 0.42 * s), 900 * s, (1.0, 0.62, 0.3), radius=0.3, kind="lantern")
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tube(f"LanternPost{k}", [(x + math.cos(a) * 0.3 * s, y + math.sin(a) * 0.3 * s, lz), (x + math.cos(a) * 0.3 * s, y + math.sin(a) * 0.3 * s, lz + 0.85 * s)],
             0.04 * s, frame, square=True, poly=True)
    cone("LanternRoof", 0.48 * s, 0.06 * s, 0.32 * s, (x, y, lz + 1.0 * s), frame, verts=4, rot=(0, 0, math.pi / 4))
    box("LanternBase", (0.62 * s, 0.62 * s, 0.1 * s), (x, y, lz - 0.02 * s), frame, bevel=0.01)


def lantern_pole(fig, joint, side, frame, glow, s=1.0):
    """A lantern on a short pole held up in a raised hand: the pole runs on up from the hand, the lantern hangs from a
    hook at its top, clear of the sleeve."""
    hand = fig.at(joint, (side * 1.5, 0, 2.1))
    top = hand + Vector((side * 0.55, -0.45, 1.9)) * s
    tube("LanternPole", [tuple(hand), tuple(top)], 0.07 * s, frame, poly=True)
    tube("LanternHook", [tuple(top), tuple(top + Vector((side * 0.5, 0, 0)) * s), tuple(top + Vector((side * 0.55, 0, -0.25)) * s)], 0.04 * s, frame, poly=True)
    lantern(top.x + side * 0.55 * s, top.y, top.z - 0.25 * s, frame, glow, s=s)


def crescent_staff(x, y, z0, z1, m):
    tube("Staff", [(x, y, z0), (x, y, z1)], 0.08, m, poly=True)
    B20.tprism("StaffMoon", WS.crescent(x, z1 + 0.4, 0.5, shift=0.4, tilt=math.pi / 2), y, 0.08, m)
    sphere("StaffKnop", 0.14, (x, y, z1 - 0.3), m, seg=10, rings=5)


def mortarboard(fig, m, tassel):
    def f():
        box("Cap", (1.25, 1.25, 0.32), (0, 0, 5.12), m, bevel=0.06)
        box("Board", (1.8, 1.8, 0.08), (0, 0, 5.32), m, bevel=0.015)
        sphere("Button", 0.07, (0, 0, 5.38), tassel, seg=8, rings=4)
        tube("Tassel", [(0, 0, 5.38), (0.62, -0.1, 5.37), (0.86, -0.64, 5.3), (0.87, -0.72, 4.9)], 0.03, tassel)
        sphere("TasselEnd", 0.07, (0.87, -0.72, 4.85), tassel, seg=8, rings=4, scale=(1, 1, 1.7))
    fig.build("head", f)


def crown(fig, m, gem):
    def f():
        lathe_pts = 10
        hoop("CrownBand", (0, 0, 5.15), 0.68, "Z", m, thick=0.1)
        for k in range(lathe_pts):
            a = k / lathe_pts * 2 * math.pi
            cone(f"CrownSpike{k}", 0.12, 0.0, 0.55, (math.cos(a) * 0.66, math.sin(a) * 0.66, 5.45), m, verts=4)
            sphere(f"CrownPearl{k}", 0.06, (math.cos(a) * 0.66, math.sin(a) * 0.66, 5.75), gem, seg=8, rings=4)
        sphere("CrownGem", 0.12, (0, -0.72, 5.15), gem, seg=10, rings=5)
    fig.build("head", f)


def wolf_head(fig, fur, dark, fang):
    def f():
        box("Snout", (0.62, 0.9, 0.5), (0, -0.88, 4.32), fur, bevel=0.14, segments=3)
        sphere("Nose", 0.13, (0, -1.32, 4.5), dark, seg=10, rings=5)
        box("Jaw", (0.5, 0.75, 0.18), (0, -0.8, 4.02), fur, bevel=0.06, rot=(0.35, 0, 0))
        for sx in (-1, 1):
            cone(f"Ear{sx}", 0.24, 0.0, 0.66, (sx * 0.38, 0.05, 5.22), fur, verts=4, rot=(0.2, sx * -0.2, 0))
            B20.tprism(f"Eye{sx}", WS.ccw([(sx * 0.1, 4.66), (sx * 0.38, 4.74), (sx * 0.3, 4.58)]), -0.61, 0.03, dye("amber"))
            cone(f"Fang{sx}", 0.045, 0.0, 0.16, (sx * 0.17, -1.2, 4.12), fang, verts=4, rot=(math.pi, 0, 0))
        for k in range(12):
            a = k / 12 * 2 * math.pi
            sphere(f"Ruff{k}", 0.36, (math.cos(a) * 0.64, math.sin(a) * 0.56 + 0.05, 4.02), fur, seg=6, rings=4, scale=(1, 1, 0.7))
    fig.build("head", f)


def hound(x, z, yaw, fur, dark, s=1.0, leap=0.0):
    """A lean hunting hound, running."""
    m = _mark()
    box("HoundBody", (0.8, 2.4, 0.8), (0, 0, 1.6), fur, bevel=0.3, segments=3)
    box("HoundChest", (0.9, 0.9, 1.0), (0, -0.9, 1.65), fur, bevel=0.3, segments=3)
    box("HoundNeck", (0.5, 0.7, 0.9), (0, -1.4, 2.2), fur, bevel=0.2, rot=(0.6, 0, 0))
    box("HoundHead", (0.6, 1.0, 0.55), (0, -1.9, 2.6), fur, bevel=0.2, segments=3)
    box("HoundMuzzle", (0.4, 0.6, 0.35), (0, -2.45, 2.5), fur, bevel=0.12)
    sphere("HoundNose", 0.1, (0, -2.75, 2.58), dark, seg=8, rings=4)
    for sx in (-1, 1):
        box(f"HoundEar{sx}", (0.1, 0.3, 0.45), (sx * 0.3, -1.75, 2.65), dark, bevel=0.05, rot=(0.3, sx * 0.25, 0))
    for k, (yy, ang) in enumerate(((-0.9, -0.9 - leap), (-0.9, -0.5 - leap), (0.9, 0.8 + leap), (0.9, 0.4 + leap))):
        sx = -1 if k % 2 else 1
        mt = Matrix.Translation((sx * 0.25, yy, 1.4)) @ Matrix.Rotation(ang, 4, "X")
        s2 = _mark()
        box(f"HoundLeg{k}", (0.22, 0.22, 1.4), (0, 0, -0.7), fur, bevel=0.08)
        box(f"HoundPaw{k}", (0.26, 0.4, 0.15), (0, -0.1, -1.4), dark, bevel=0.05)
        _xform(s2, mt)
    tube("HoundTail", [(0, 1.2, 1.8), (0, 1.8, 2.3), (0, 2.3, 2.5)], 0.08, fur)
    box("HoundCollar", (0.6, 0.3, 0.6), (0, -1.3, 2.05), dark, bevel=0.05, rot=(0.6, 0, 0))
    _xform(m, Matrix.Translation((x, 0, z)) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(s, 4))


# ------------------------------------------------------------------ costume (torso frame unless said)

def cape(fig, outer, lining, flare=2.3, hem=0.15, back=0.75, sway=0.0, name="Cape"):
    """A long cape from the shoulders, flaring wide behind the figure down to the hem, folded in soft pleats; the lining
    a hair in front of the outside so it shows round the edges."""
    def rows(off, shrink):
        out = []
        for i in range(9):
            t = i / 8
            z = 4.05 - (4.05 - hem) * t
            half = (1.05 + (flare - 1.05) * t ** 0.8) * shrink
            row = []
            for j in range(17):
                u = j / 16 * 2 - 1
                x = u * half + sway * t * t
                y = back + 0.25 * t + 0.18 * math.sin(u * math.pi * 3.5) * t + off
                row.append(Vector((x, y, z)))
            out.append(row)
        return out
    fig.build("torso", lambda: _mesh(name, rows(0.0, 1.0), outer, 0.05))
    fig.build("torso", lambda: _mesh(name + "Lining", rows(-0.06, 0.97), lining, 0.03))


def high_collar(fig, outer, lining):
    def f():
        for sx in (-1, 1):
            B20.tprism(f"Collar{sx}", WS.ccw([(sx * 0.2, 3.95), (sx * 1.1, 4.0), (sx * 1.35, 5.45), (sx * 0.5, 5.05)]), 0.6, 0.07, outer)
            B20.tprism(f"CollarIn{sx}", WS.ccw([(sx * 0.26, 3.98), (sx * 1.02, 4.03), (sx * 1.24, 5.28), (sx * 0.52, 4.98)]), 0.54, 0.04, lining)
    fig.build("torso", f)


def glow_eyes(fig, m, y=-0.61):
    def f():
        for sx in (-1, 1):
            B20.tprism(f"GlowEye{sx}", WS.ccw([(sx * 0.1, 4.6), (sx * 0.36, 4.68), (sx * 0.3, 4.54)]), y, 0.03, m)
    fig.build("head", f)


def bulk(fig, skin):
    """A demon's heavier frame over the R6 torso: a broad chest, shoulder knots, a spiked spine."""
    def f():
        box("Chest", (2.4, 1.25, 1.5), (0, -0.04, 3.3), skin, bevel=0.3, segments=3)
        for sx in (-1, 1):
            sphere(f"Trap{sx}", 0.55, (sx * 0.85, 0.05, 3.95), skin, seg=12, rings=6, scale=(1.1, 1.0, 0.6))
        for k in range(6):
            cone(f"Spine{k}", 0.13, 0.0, 0.42, (0, 0.62, 2.3 + k * 0.33), skin, verts=5, rot=(-1.25, 0, 0))
    fig.build("torso", f)


def ember_veins(fig, m):
    """Glowing cracks across the chest and down the arms, like embers under the skin."""
    def f():
        for k, pts in enumerate((
                [(0.0, -0.68, 3.85), (0.18, -0.68, 3.5), (0.1, -0.68, 3.1), (0.32, -0.68, 2.75), (0.25, -0.66, 2.4)],
                [(0.0, -0.68, 3.85), (-0.25, -0.68, 3.55), (-0.15, -0.68, 3.2), (-0.42, -0.68, 2.9)],
                [(0.18, -0.68, 3.5), (0.55, -0.67, 3.62), (0.85, -0.65, 3.4)],
                [(-0.15, -0.68, 3.2), (-0.6, -0.67, 3.3), (-0.95, -0.64, 3.05)],
                [(0.1, -0.68, 3.1), (-0.05, -0.68, 2.7), (0.05, -0.66, 2.3)])):
            tube(f"Vein{k}", pts, 0.035, m, poly=True)
    fig.build("torso", f)
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        fig.build(j, lambda side=side: tube(f"ArmVein{side}", [(side * 1.5, -0.52, 3.6), (side * 1.62, -0.52, 3.0), (side * 1.45, -0.52, 2.5),
                                                               (side * 1.58, -0.52, 2.1)], 0.03, m, poly=True))


def ram_horns(fig, m, big=1.0):
    def f():
        for sx in (-1, 1):
            pts = []
            for i in range(14):
                t = i / 13
                a = t * math.pi * 1.55
                r = (0.62 - 0.34 * t) * big
                pts.append((sx * (0.5 + 0.35 * big * t + math.sin(a) * r * 0.25), 0.1 + math.cos(a) * r * 0.9 - 0.2 * t, 5.0 + math.sin(a) * r * 1.2 + 0.25 * t))
            tube(f"RamHorn{sx}", pts, 0.16 * big, m)
            cone(f"RamTip{sx}", 0.1 * big, 0.0, 0.3, pts[-1], m, verts=8)
        for sx in (-1, 1):
            cone(f"Brow{sx}", 0.12, 0.0, 0.4, (sx * 0.3, -0.5, 5.05), m, verts=5, rot=(-0.4, sx * 0.4, 0))
    fig.build("head", f)


def demon(base, yaw, scale, pose, K, wings=4.0, raise_=40):
    dm = S.R6(base=base, yaw=yaw, scale=scale, pose=pose)
    S.body(dm, K["skin"], face="none")
    bulk(dm, K["skin"])
    ram_horns(dm, K["horn"])
    horns(dm, K["horn"], big=0.85)
    demon_face(dm, K["eye"], K["mouth"], K["fang"])
    ember_veins(dm, K["eye"])
    tail(dm, K["skin"], K["dark"])
    bat_wings(dm, K["dark"], K["bone"], span=wings, raise_=raise_)
    claws(dm, K["fang"])
    return dm


def DEMON():
    return {"skin": dye("crimsonlt"), "dark": dye("crimsondk"), "horn": dye("bonedk"), "eye": dye("ember"), "mouth": dye("soot"),
            "fang": dye("bone"), "bone": dye("soot")}


def great_key(fig, joint, side, gilt, gem):
    """The school's great key held up by the bow, its shaft running on out of the fist (it points where the arm points)."""
    def f():
        x = side * 1.5
        hoop("KeyBow", (x, -0.15, 2.0), 0.42, "Y", gilt, thick=0.08)
        sphere("KeyGem", 0.2, (x, -0.2, 2.0), gem, seg=12, rings=6)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            sphere(f"KeyLobe{k}", 0.16, (x + math.cos(a) * 0.42, -0.15, 2.0 + math.sin(a) * 0.42), gilt, seg=10, rings=5)
        tube("KeyShaft", [(x, -0.15, 1.58), (x, -0.15, -1.6)], 0.11, gilt, poly=True)
        box("KeyCollar", (0.34, 0.3, 0.14), (x, -0.15, 1.3), gilt, bevel=0.03)
        box("KeyBit", (0.62, 0.16, 0.34), (x + side * 0.3, -0.15, -1.3), gilt, bevel=0.03)
        box("KeyBit2", (0.42, 0.16, 0.22), (x + side * 0.2, -0.15, -0.85), gilt, bevel=0.03)
    fig.build(joint, f)


# ------------------------------------------------------------------ the scenes (field origin: bottom centre)

def scene_headmaster():
    soot, crim, gold, bone, ink = dye("soot"), dye("crimson"), dye("gold"), dye("bone"), dye("ink")
    fig = S.R6(base=(0, 0, 3.0), scale=2.0, pose={"rshoulder": (0, -150, 0), "lshoulder": (0, 22, 0), "neck": (0, 4, 0)})
    S.body(fig, dye("cream"), face="none", arms=False, legs=False)
    S.robe(fig, soot, w0=2.9, d0=1.9)
    for side in (-1, 1):
        S.sleeve(fig, side, soot, bell=1.08)
    beard(fig, dye("bone"), long=1.35)
    glow_eyes(fig, dye("holy"), y=-0.63)
    cape(fig, soot, dye("crimsondk"), flare=2.9, hem=0.1)
    high_collar(fig, soot, dye("crimsondk"))

    def vest():
        for sx in (-1, 1):
            strip(f"Stole{sx}", [(sx * 0.36, -0.6, 4.0), (sx * 0.42, -0.7, 2.6), (sx * 0.46, -0.98, 0.3)], 0.34, (1, 0, 0), crim, thick=0.04)
            tube(f"StoleTrim{sx}", [(sx * 0.53, -0.63, 4.0), (sx * 0.59, -0.73, 2.6), (sx * 0.63, -1.01, 0.3)], 0.025, gold)
            tube(f"GownEdge{sx}", [(sx * 0.2, -0.56, 3.95), (sx * 0.35, -0.6, 3.0), (sx * 0.5, -0.95, 0.05)], 0.035, gold)
        tube("Chain", [(-0.8, -0.56, 3.95), (-0.48, -0.62, 3.3), (0.0, -0.66, 3.0), (0.48, -0.62, 3.3), (0.8, -0.56, 3.95)], 0.05, gold)
        cyl("Medal", 0.26, 0.06, (0, -0.68, 2.86), gold, rot=(math.pi / 2, 0, 0), verts=20, bevel=0.01)
        sphere("MedalGem", 0.1, (0, -0.72, 2.86), dye("crimsonlt"), seg=10, rings=5)
        box("HemBand", (2.95, 1.95, 0.14), (0, 0, 0.12), gold, bevel=0.03)
    fig.build("torso", vest)
    mortarboard(fig, ink, gold)
    great_key(fig, "rshoulder", 1, gold, dye("holy"))
    kt = fig.at("rshoulder", (1.5, -0.2, 2.0))
    glow_light(tuple(kt + Vector((0, -0.6, 0))), 700, (1.0, 0.85, 0.55), radius=0.3, kind="key")
    lh = fig.at("lshoulder", (-1.5, 0, 2.1))
    crescent_staff(lh.x, lh.y - 0.6, 3.0, lh.z + 4.6, gold)
    orb = Vector((lh.x, lh.y - 0.6, lh.z + 5.0))
    sphere("StaffOrb", 0.28, tuple(orb), dye("spirit"), seg=14, rings=7)
    glow_light(tuple(orb + Vector((0, -0.5, 0))), 300, (0.6, 0.75, 1.0), radius=0.3, kind="orb")
    sh = fig.at("torso", (-1.0, -0.2, 4.05))
    raven("RavenShoulder", (sh.x, sh.y, sh.z), -math.pi / 2 - 0.9, 7.0, soot, ink)


def scene_priest_demon():
    bone, crim, gold, soot = dye("bone"), dye("crimson"), dye("gold"), dye("soot")
    pr = S.R6(base=(-3.4, 0, 2.6), yaw=math.radians(20), scale=1.5, pose={"rshoulder": (0, -150, 0), "lshoulder": (-50, 0, 15), "neck": (0, -6, 0)})
    S.body(pr, dye("cream"), face="stern", dark=soot, arms=False, legs=False)
    S.robe(pr, bone, w0=2.9, d0=1.9)
    for side in (-1, 1):
        S.sleeve(pr, side, bone, bell=1.12)
    cape(pr, dye("bonedk"), crim, flare=2.3, hem=0.1)

    def vest():
        for sx in (-1, 1):
            strip(f"Stole{sx}", [(sx * 0.35, -0.58, 4.0), (sx * 0.4, -0.66, 2.6), (sx * 0.44, -0.96, 0.3)], 0.32, (1, 0, 0), crim, thick=0.04)
            tube(f"StoleTrim{sx}", [(sx * 0.51, -0.61, 4.0), (sx * 0.56, -0.69, 2.6), (sx * 0.6, -0.99, 0.3)], 0.025, gold)
        foil = [(0, -0.72, 3.25)]
        sphere("Sunburst", 0.18, foil[0], gold, seg=12, rings=6, scale=(1, 0.4, 1))
        for k in range(8):
            a = k / 8 * 2 * math.pi
            cone(f"SunRay{k}", 0.05, 0.0, 0.3, (math.cos(a) * 0.3, -0.72, 3.25 + math.sin(a) * 0.3), gold, verts=4, rot=(0, -a + math.pi / 2, 0))
        S.sphere("Hood", 0.78, (0, 0.62, 3.95), bone, seg=14, rings=7, scale=(1.25, 0.55, 0.55))
        hoop("Halo", (0, 0.7, 4.6), 0.95, "Y", dye("holy"), thick=0.06)
    pr.build("torso", vest)
    lantern_pole(pr, "rshoulder", 1, gold, dye("amber"), s=1.1)
    # the book of rites held out in the left hand
    lh = pr.at("lshoulder", (-1.5, -0.4, 2.0))
    box("Book", (1.0, 0.75, 0.22), tuple(lh + Vector((0, -0.2, 0.1))), dye("crimsondk"), bevel=0.04)
    box("BookPages", (0.92, 0.7, 0.18), tuple(lh + Vector((0.04, -0.2, 0.1))), bone, bevel=0.02)
    hoop("BookClasp", tuple(lh + Vector((0, -0.6, 0.1))), 0.12, "Y", gold, thick=0.03)
    demon((3.1, 1.0, 2.6), math.radians(-25), 1.55,
          {"root": (0, 14, 0), "neck": (0, 18, 0), "lshoulder": (0, 155, 0), "rshoulder": (0, -70, 0), "lhip": (0, 18, 0), "rhip": (0, -14, 0),
           "lift": -0.12}, DEMON(), wings=3.6, raise_=40)


def scene_angel_demon():
    bone, gold, soot = dye("bone"), dye("gold"), dye("soot")
    an = S.R6(base=(-3.3, 0, 9.0), yaw=math.radians(15), scale=1.3, pose={"rshoulder": (0, -62, 0), "lshoulder": (0, 125, 0), "neck": (0, -6, 0),
                                                                          "lhip": (0, 8, 0), "rhip": (0, -12, 0), "root": (0, -8, 0)})
    S.body(an, dye("cream"), face="stern", dark=soot, arms=False, legs=False)
    S.robe(an, bone, w0=2.6, d0=1.7)
    for side in (-1, 1):
        S.sleeve(an, side, bone, bell=1.1)
    cape(an, dye("crimson"), dye("crimsondk"), flare=2.6, hem=0.4, sway=-0.8)

    def armour():
        box("Breastplate", (2.2, 1.25, 1.5), (0, 0, 3.3), gold, bevel=0.22, segments=3)
        box("Fauld", (2.3, 1.3, 0.35), (0, 0, 2.35), dye("golddk"), bevel=0.06)
        for k in range(5):
            box(f"Tasset{k}", (0.42, 0.1, 0.8), (-0.9 + k * 0.45, -0.68, 1.85), gold, bevel=0.04)
        sphere("Sun", 0.24, (0, -0.66, 3.4), dye("holy"), seg=12, rings=6, scale=(1, 0.4, 1))
        hoop("Halo", (0, 0.75, 4.65), 0.95, "Y", dye("holy"), thick=0.08)
    an.build("torso", armour)
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        an.build(j, lambda side=side: [sphere(f"Pauldron{side}", 0.8, (side * 1.5, 0, 3.9), gold, seg=14, rings=7, scale=(1.0, 0.85, 0.6)),
                                       box(f"Vambrace{side}", (1.15, 1.15, 0.6), (side * 1.5, 0, 2.35), gold, bevel=0.1)])
    an.build("head", lambda: S.sphere("Hair", 0.72, (0, 0.12, 4.8), dye("gold"), seg=14, rings=7, scale=(1.0, 0.95, 0.8)))
    feather_wings(an, dye("cream"), span=3.8)

    def sword():
        x = 1.5
        tube("Grip", [(x, -0.2, 2.3), (x, -0.2, 1.4)], 0.1, dye("golddk"), poly=True)
        box("Guard", (0.18, 0.2, 1.6), (x, -0.2, 1.3), gold, bevel=0.03)
        box("Blade", (0.4, 0.1, 4.4), (x, -0.2, 1.25 - 2.2), dye("holy"), bevel=0.03)
        for k in range(6):
            z = 0.9 - k * 0.7
            cone(f"Flame{k}", 0.22, 0.0, 0.7, (x + (0.25 if k % 2 else -0.25), -0.25, z), dye("ember"), verts=6, rot=(0, (0.5 if k % 2 else -0.5), 0))
    an.build("rshoulder", sword)
    st = an.at("rshoulder", (1.5, -0.2, -1.2))
    glow_light(tuple(st + Vector((0, -0.8, 0))), 1500, (1.0, 0.85, 0.6), radius=0.6, kind="sword")
    dm = demon((3.3, 1.0, 2.6), math.radians(-20), 1.45,
               {"root": (0, 10, 0), "neck": (0, 12, 0), "lshoulder": (0, 150, 0), "rshoulder": (0, -150, 0), "lhip": (0, 16, 0), "rhip": (0, -16, 0),
                "lift": -0.1}, DEMON(), wings=3.8, raise_=50)
    hl, hr2 = dm.at("lshoulder", (-1.5, 0, 2.0)), dm.at("rshoulder", (1.5, 0, 2.0))
    d = (hl - hr2).normalized()
    a, b = hr2 - d * 2.2, hl + d * 2.6
    tube("TridentShaft", [tuple(a), tuple(b)], 0.08, dye("sootlt"), poly=True)
    n0 = Vector((-d.z, 0, d.x))
    tube("TridentBar", [tuple(b - n0 * 0.45), tuple(b + n0 * 0.45)], 0.07, dye("sootlt"), poly=True)
    for k in (-1, 0, 1):
        n = n0 * 0.45 * k
        tube(f"Tine{k}", [tuple(b + n), tuple(b + n + d * (1.0 if k == 0 else 0.75))], 0.06, dye("sootlt"), poly=True)
        cone(f"TineTip{k}", 0.12, 0.0, 0.35, tuple(b + n + d * (1.15 if k == 0 else 0.9)), dye("sootlt"), verts=4,
             rot=Vector((0, 0, 1)).rotation_difference(d).to_euler())


def scene_judgement():
    gold, bone, soot = dye("gold"), dye("bone"), dye("soot")
    k = S.R6(base=(0, 0.8, 8.6), scale=1.55, pose={"lhip": (-90, 0, 0), "rhip": (-90, 0, 0), "rshoulder": (0, -82, 0), "lshoulder": (0, 82, 0)})
    S.body(k, dye("cream"), face="none", dark=soot, legs=True, arms=False)
    S.robe(k, gold, w0=2.7, d0=1.9)
    for side in (-1, 1):
        S.sleeve(k, side, gold, bell=1.3)
    beard(k, bone, long=1.6)
    glow_eyes(k, dye("holy"), y=-0.63)
    crown(k, gold, dye("crimsonlt"))

    def rays():
        hoop("Halo", (0, 0.75, 4.7), 1.15, "Y", dye("holy"), thick=0.09)
        for n in range(28):
            a = n / 28 * 2 * math.pi
            L = 1.6 if n % 2 else 2.6
            r0 = 1.3
            mid = (math.cos(a) * (r0 + L / 2), 0.8, 4.7 + math.sin(a) * (r0 + L / 2))
            cone(f"Ray{n}", 0.09 if n % 2 else 0.13, 0.0, L, mid, dye("gold"), verts=4, rot=(0, -a + math.pi / 2, 0))
        strip("Mantle", [(0, -0.62, 4.0), (0, -0.7, 2.6), (0, -0.95, 0.4)], 0.9, (1, 0, 0), dye("crimson"), thick=0.04)
        for sx in (-1, 1):
            tube(f"MantleTrim{sx}", [(sx * 0.47, -0.64, 4.0), (sx * 0.47, -0.72, 2.6), (sx * 0.47, -0.97, 0.4)], 0.03, dye("holy"))
    k.build("torso", rays)
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        h = k.at(j, (side * 1.5, 0, 2.0))
        sphere(f"Orb{side}", 0.36, (h.x, h.y - 0.3, h.z - 0.1), dye("holy") if side > 0 else dye("ember"), seg=14, rings=7)
    for n, (x, z, rr) in enumerate(((-4.2, 2.6, 40), (0.4, 1.0, -120), (4.4, 3.0, 150))):
        demon((x, 1.0, z), math.radians(30 * (1 if n % 2 else -1)), 0.85,
              {"root": (0, rr, 0), "lshoulder": (0, 150, 0), "rshoulder": (0, -125, 0), "lhip": (0, 25, 0), "rhip": (0, -30, 0)}, DEMON(), wings=3.0, raise_=60)


def scene_wolf_hunt():
    soot, gold = dye("soot"), dye("gold")
    ww = S.R6(base=(8.3, 1.0, 2.2), yaw=math.radians(-55), scale=1.45,
              pose={"root": (14, 0, 0), "neck": (-28, 0, 0), "rshoulder": (-70, 0, -30), "lshoulder": (-40, 0, 40), "lhip": (-30, 0, 0), "rhip": (12, 0, 0)})
    fur = dye("slate")
    S.body(ww, fur, face="none")
    bulk(ww, fur)
    wolf_head(ww, fur, soot, dye("bone"))
    ww.build("torso", lambda: [tube("WolfTail", [(0, 0.5, 2.1), (0, 1.1, 1.7), (0.2, 1.4, 0.9), (0.1, 1.3, 0.3)], 0.24, fur)] +
             [cone(f"Tuft{n}", 0.16, 0.0, 0.45, (math.cos(n) * 0.9, 0.55, 2.4 + (n % 5) * 0.35), fur, verts=4, rot=(1.9, 0, 0)) for n in range(10)])
    claws(ww, dye("bone"))
    hound(3.2, 0.6, math.radians(90), dye("bonedk"), soot, s=1.05, leap=0.2)
    hound(-0.2, 0.4, math.radians(90), dye("rust"), soot, s=1.0, leap=-0.1)
    for n, (x, yaw) in enumerate(((-4.6, 80), (-8.0, 75))):
        h = S.R6(base=(x, 0.5 * n, 0.6), yaw=math.radians(yaw), scale=1.2,
                 pose={"rhip": (-35, 0, 0), "lhip": (35, 0, 0), "rshoulder": (-80, 0, 0), "lshoulder": (-120, 0, 10), "root": (-8, 0, 0), "lift": -0.12})
        coat = dye("moss") if n == 0 else dye("crimsondk")
        S.body(h, dye("cream"), face="stern", dark=soot, arms=False, legs=True)
        h.build("torso", lambda coat=coat: [box("Coat", (2.15, 1.15, 2.4), (0, 0, 2.9), coat, bevel=0.1), frustum("CoatSkirt", (0, 0), 2.5, 1.5, 1.2, 2.15, 1.15, 2.2, coat),
                                            box("Belt", (2.2, 1.2, 0.2), (0, 0, 2.2), soot, bevel=0.04)])
        cape(h, soot, dye("crimson") if n == 0 else dye("moss"), flare=1.7, hem=1.6, sway=-1.2, name="Capelet")
        for side in (-1, 1):
            S.sleeve(h, side, coat, bell=1.05)
        h.build("head", lambda: [box("HatBrim", (1.9, 1.9, 0.1), (0, 0, 5.1), soot, bevel=0.02), frustum("HatCrown", (0, 0), 1.2, 1.2, 5.1, 1.0, 1.0, 6.0, soot),
                                 box("HatBand", (1.22, 1.22, 0.16), (0, 0, 5.25), gold, bevel=0.01)])
        rh = h.at("rshoulder", (1.5, 0, 2.0))
        lantern(rh.x, rh.y - 0.3, rh.z, gold, dye("amber"), s=0.9)
        lh = h.at("lshoulder", (-1.5, 0, 2.1))
        d = (h.at("lshoulder", (-1.5, 0, -1.0)) - lh).normalized()
        tube("Spear", [tuple(lh - d * 3.0), tuple(lh + d * 2.4)], 0.07, dye("sootlt"), poly=True)
        tip = lh + d * 2.4
        cone("SpearHead", 0.18, 0.0, 0.8, tuple(tip + d * 0.4), dye("bone"), verts=4, rot=Vector((0, 0, 1)).rotation_difference(d).to_euler())


SCENES = {"Headmaster": scene_headmaster, "PriestDemon": scene_priest_demon, "AngelDemon": scene_angel_demon, "Judgement": scene_judgement,
          "WolfHunt": scene_wolf_hunt}


# ------------------------------------------------------------------ render

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


# per scene: the moonlight (the direction it travels, its strength), the night fill, any coloured glow from below / above
LIGHTS = {
    "Headmaster": dict(moon=((0.6, -0.5, -0.45), 2.2), fill=0.08),
    "PriestDemon": dict(moon=((-0.5, -0.6, -0.5), 1.8), fill=0.06),
    "AngelDemon": dict(moon=((0.7, -0.4, -0.6), 2.6), fill=0.07, under=((3.4, -4, 0.6), 2400, (1.0, 0.25, 0.08))),
    "Judgement": dict(moon=((0.3, -0.5, -0.8), 3.0), fill=0.08, under=((0, -4, 0.2), 3200, (1.0, 0.3, 0.08)),
                      over=((0, -5, 15.5), 700, (1.0, 0.82, 0.5))),
    "WolfHunt": dict(moon=((-0.6, 0.3, -0.5), 2.0), fill=0.08),
}


def render(name):
    sc = P.reset()
    _mats.clear()
    POINTS.clear()
    SCENES[name]()
    fw, fh, rx, ry = FIELD[name]
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
    cfg = LIGHTS[name]
    bg.inputs["Color"].default_value = (0.35, 0.4, 0.75, 1)       # a cool night fill
    bg.inputs["Strength"].default_value = cfg["fill"]
    d, e = cfg["moon"]
    L = bpy.data.lights.new("Moon", "SUN")
    L.energy = e
    L.color = (0.72, 0.8, 1.0)
    L.angle = math.radians(6)
    lo = bpy.data.objects.new("Moon", L)
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = (Vector(d) * -1).to_track_quat("Z", "Y").to_euler()
    # a warm key from the front so faces and cloth read (the candlelit hall the tapestry hangs in)
    K = bpy.data.lights.new("Key", "AREA")
    K.energy = 2600
    K.size = 14
    K.color = (1.0, 0.82, 0.62)
    ko = bpy.data.objects.new("Key", K)
    bpy.context.collection.objects.link(ko)
    ko.location = (-9, -26, fh * 0.75)
    ko.rotation_euler = (Vector((0, 0, fh * 0.45)) - ko.location).to_track_quat("-Z", "Y").to_euler()
    for k in ("under", "over"):
        if k in cfg:
            pos, en, colr = cfg[k]
            glow_light(pos, en, colr, radius=2.0, kind=k)
    sc.cycles.samples = 128
    sc.cycles.use_denoising = True
    sc.render.filepath = os.path.join(OUT, f"{name}_beauty.png")
    bpy.ops.render.render(write_still=True)
    # the gilt mask: gilt parts white, everything else black (the gilt thread and the metal map)
    white, black = _mask(True), _mask(False)
    for ob in bpy.data.objects:
        for slot in getattr(ob, "material_slots", []):
            if slot.material is not None:
                slot.material = white if slot.material.get("dye") in GILT else black
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.hide_render = True
    bg.inputs["Strength"].default_value = 0.0
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.cycles.samples = 8
    sc.cycles.use_denoising = False
    sc.render.filepath = os.path.join(OUT, f"{name}_gilt.png")
    bpy.ops.render.render(write_still=True)
    # the glow sources in px, for the weaver's halos
    import json
    pts = {k: [((x / fw + 0.5) * rx, (1 - z / fh) * ry) for x, y, z in v] for k, v in POINTS.items()}
    with open(os.path.join(OUT, f"{name}_points.json"), "w") as f:
        json.dump(pts, f)
    print(f"[tapestry] {name} rendered")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = [a for a in argv if a in SCENES] or list(SCENES)
    for n in names:
        render(n)
