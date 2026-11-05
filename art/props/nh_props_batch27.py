"""Props batch 27 (2026-11-05): the statue kit for nh_props.py. Ten original statues of R6-built figures (the classic
blocky Roblox body: a 2 x 2 x 1 torso, 1 x 2 x 1 arms and legs, a rounded 1.2 head, measured from the owner's R6 rig in
Blender), posed on their real joints and carved, cast or gilt in the Institution's look: weathered marble and soot-dark
stone, bronze, black marble, crimson enamel and gilt, on gothic plinths.

  FounderStatue    the school's founder in a bronze gown and mortarboard, the crest's key raised high, a book at the heart,
                   on a tall gothic plinth with a brass plaque
  MourningAngel    a veiled marble angel weeping into her hands, wings folded, on a tomb chest with a carved wreath
  Gargoyle         a horned, bat-winged gargoyle sitting on the edge of an octagonal column, grinning, a tail curled down
  VampireLord      a black marble vampire spreading a crimson-lined cape, a high collar, a crimson gem, on black marble
  WerewolfHowl     a wolf-headed figure howling on a mossy rock under a gilt crescent moon
  LanternPriest    a robed priest with a crescent staff and a lit lantern (Glow), a gilt halo, on a stepped plinth
  HollowWraith     a hooded wraith with no face and no feet, tattered sleeves reaching, floating over a slim spire
  KnightGuardian   an armoured knight leaning on a greatsword, a crimson tabard with the crest; made to stand in pairs
  FencingDuel      two bronze students mid-lunge with sabres and fencing masks on one long plinth
  RavenScholar     a student reading on a stone bench with ravens on her shoulder, the bench and the book

Pieces: Main (the plinth), Figure (the statue; FencingDuel has Figure and Figure2), Glow (the priest's flame). Front faces
-Y, Z is up, the origin is at the bottom centre. Registered into nh_props.BUILD on import.
"""
import math
import random

import bpy
from mathutils import Euler, Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere, cone, flame
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _mesh
from nh_props_batch5 import marble
from nh_props_batch7 import lump
from nh_props_batch8 import castle, mossy, hollow, _moss, _crack, _panel
from nh_props_batch9 import foil, raven
from nh_props_batch10 import gilt, black_marble
from nh_props_batch12 import soot_stone, frustum, sheet
import nh_props_batch20 as B20
import window_shapes as WS

S = 1.6          # statue scale: studs per R6 unit (an R6 figure is 5.1 tall, a statue about 8.2)


# ------------------------------------------------------------------ materials

def mats():
    worn, _ = castle()
    return {
        "marble": marble("StatueMarble", base=(0.74, 0.72, 0.68), vein=(0.36, 0.35, 0.36), scale=1.1, width=0.03, distortion=9.0),
        "soot": soot_stone("StatueSoot", (0.2, 0.205, 0.195)),
        "sootdk": soot_stone("StatueSootDark", (0.1, 0.104, 0.098)),
        "worn": worn,
        "bronze": material("Bronze", "NH_Brass", tint=(0.26, 0.19, 0.12), scale=0.6, rough_add=0.22, wear=0.6, dirt=1.0),
        "bronzedk": material("BronzeDark", "NH_Brass", tint=(0.13, 0.1, 0.07), scale=0.6, rough_add=0.25, wear=0.5, dirt=1.0),
        "black": black_marble(),
        "gilt": gilt(),
        "crimson": material("StatueCrimson", "NH_PaintedMetal", tint=(0.26, 0.02, 0.04), scale=1.2, rough_mul=0.5, wear=0.4, wear_metal=True),
        "hollow": hollow(),
        "moss": mossy(),
    }


# ------------------------------------------------------------------ the R6 rig

class R6:
    """A posed R6 figure. Parts are built in R6 units at rest (feet on z = 0, facing -Y), then turned about their joints
    and placed: world = T(base) @ Rz(yaw) @ Scale(S) @ T(lift) @ root @ joint. pose: degrees (rx, ry, rz) per joint:
      root (about the hips' centre), neck, lshoulder, rshoulder, lhip, rhip; and lift (R6 units up).
    rx < 0 swings a limb forward (-Y); rx > 0 on the neck bows the head."""
    JOINT = {"neck": (0, 0, 4.0), "rshoulder": (1.25, 0, 3.5), "lshoulder": (-1.25, 0, 3.5), "rhip": (0.5, 0, 2.0), "lhip": (-0.5, 0, 2.0),
             "root": (0, 0, 2.0)}

    def __init__(self, base=(0, 0, 0), yaw=0.0, pose=None, scale=S):
        self.pose = pose or {}
        lift = self.pose.get("lift", 0.0)
        self.G = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Scale(scale, 4) @ Matrix.Translation((0, 0, lift))
        self.root = self._turn("root")

    def _turn(self, joint):
        d = self.pose.get(joint, (0, 0, 0))
        p = Vector(self.JOINT[joint])
        R = Euler([math.radians(a) for a in d], "XYZ").to_matrix().to_4x4()
        return Matrix.Translation(p) @ R @ Matrix.Translation(-p)

    def M(self, part):
        if part == "torso":
            return self.G @ self.root
        return self.G @ self.root @ self._turn(part if part != "head" else "neck")

    def at(self, part, p):
        """A point given in a part's rest frame, in the world."""
        return self.M(part) @ Vector(p)

    def build(self, part, fn):
        s = _mark()
        fn()
        _xform(s, self.M(part))


def body(fig, m, head=True, face="stern", arms=True, legs=True, torso=True, dark=None):
    """The R6 body itself: rounded blocks like the R6 mesh, and an optional carved face."""
    dark = dark or m
    if torso:
        fig.build("torso", lambda: box("Torso", (2.0, 1.0, 2.0), (0, 0, 3.0), m, bevel=0.1, segments=3))
    if arms:
        for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
            fig.build(j, lambda side=side: box(f"Arm{side}", (1.0, 1.0, 2.0), (side * 1.5, 0, 3.0), m, bevel=0.1, segments=3))
    if legs:
        for side, j in ((1, "rhip"), (-1, "lhip")):
            fig.build(j, lambda side=side: box(f"Leg{side}", (1.0, 1.0, 2.0), (side * 0.5, 0, 1.0), m, bevel=0.1, segments=3))
    if head:
        def h():
            box("Head", (1.2, 1.2, 1.2), (0, 0, 4.5), m, bevel=0.3, segments=4)
            if face == "stern":
                for sx in (-1, 1):
                    sphere(f"Eye{sx}", 0.09, (sx * 0.22, -0.585, 4.6), dark, seg=8, rings=4, scale=(1.0, 0.35, 1.3))
                    box(f"Brow{sx}", (0.3, 0.06, 0.07), (sx * 0.22, -0.6, 4.78), m, bevel=0.02, rot=(0, sx * 0.2, 0))
                box("Mouth", (0.36, 0.04, 0.05), (0, -0.6, 4.28), dark, bevel=0.015)
            elif face == "smile":
                for sx in (-1, 1):
                    sphere(f"Eye{sx}", 0.08, (sx * 0.22, -0.585, 4.62), dark, seg=8, rings=4, scale=(1.0, 0.35, 1.4))
                tube("Smile", [(-0.28, -0.6, 4.36), (-0.14, -0.605, 4.26), (0.0, -0.606, 4.23), (0.14, -0.605, 4.26), (0.28, -0.6, 4.36)], 0.025, dark)
            elif face == "sorrow":
                for sx in (-1, 1):
                    tube(f"Lid{sx}", [(sx * 0.1, -0.6, 4.56), (sx * 0.22, -0.605, 4.52), (sx * 0.34, -0.6, 4.56)], 0.022, dark)
        fig.build("head", h)


def robe(fig, m, w0=2.6, d0=1.7, w1=2.05, d1=1.08, z1=2.15, name="Robe"):
    """A long gown from the waist to the ground (on the torso, so it leans with the body)."""
    fig.build("torso", lambda: frustum(name, (0, 0), w0, d0, 0.02, w1, d1, z1, m, bevel=0.04))


def sleeve(fig, side, m, bell=1.12):
    j = "rshoulder" if side > 0 else "lshoulder"

    def f():
        box(f"Sleeve{side}", (1.12, 1.12, 1.6), (side * 1.5, 0, 3.15), m, bevel=0.08, segments=2)
        frustum(f"Cuff{side}", (side * 1.5, 0), 1.12 * bell, 1.12 * bell, 2.12, 1.12, 1.12, 2.45, m, bevel=0.03)
    fig.build(j, f)


def _rotz_mat(a):
    return Matrix.Rotation(a, 4, "Z")


def plinth_square(prefix, w, h, st, dk, plaque=None):
    """A gothic plinth: a moulded base, a die with blind tracery on three sides and a brass plaque in front, a cornice."""
    box(f"{prefix}Foot", (w + 0.5, w + 0.5, 0.35), (0, 0, 0.175), dk, bevel=0.05)
    box(f"{prefix}Torus", (w + 0.3, w + 0.3, 0.2), (0, 0, 0.45), st, bevel=0.08)
    box(f"{prefix}Die", (w, w, h - 1.0), (0, 0, 0.55 + (h - 1.0) / 2), st, bevel=0.04)
    box(f"{prefix}Cornice", (w + 0.36, w + 0.36, 0.26), (0, 0, h - 0.32), dk, bevel=0.05)
    box(f"{prefix}Top", (w + 0.2, w + 0.2, 0.2), (0, 0, h - 0.1), st, bevel=0.04)
    zc = 0.55 + (h - 1.0) / 2
    for k, rot in enumerate((math.pi / 2, math.pi, -math.pi / 2)):
        s = _mark()
        _panel(f"{prefix}Blind{k}", 0, 0, zc - (h - 1.6) / 2, w * 0.62, h - 1.6, dk, thick=0.03)
        _xform(s, _rotz_mat(rot) @ Matrix.Translation((0, -w / 2 - 0.005, 0)))
    if plaque:
        box(f"{prefix}Plaque", (w * 0.62, 0.05, 0.7), (0, -w / 2 - 0.02, zc + 0.2), plaque, bevel=0.012)
        foil(f"{prefix}PlaqueFoil", 0, -w / 2 - 0.05, zc - 0.55, 0.14, plaque, lobes=4, thick=0.015)
    return h


def wing(prefix, mtx, m, span=3.4, n=7, bat=False, dark=None):
    """A wing built from the shoulder blade along +X, in the XZ plane: overlapping lance-shaped feathers fanning up, or a
    bat wing (finger bones and a scalloped membrane) when bat. mtx turns it into place."""
    s = _mark()
    if bat:
        tips = [(span * 0.95, 0.4), (span * 0.85, -0.6), (span * 0.6, -1.6), (span * 0.32, -2.1)]
        tube(f"{prefix}Arm", [(0, 0, 0), (span * 0.45, 0.05, 0.6), (span, 0.0, 0.9)], 0.07, dark or m)
        for k, (x, z) in enumerate(tips):
            tube(f"{prefix}Finger{k}", [(span * 0.45, 0.05, 0.6), (x, 0.08, z)], 0.04, dark or m, poly=True)
        outline = [(0.0, 0.0), (span * 0.45, 0.6), (span, 0.9)] + tips + [(0.0, -1.4)]
        mem = []
        cx = sum(p[0] for p in outline) / len(outline)
        cz = sum(p[1] for p in outline) / len(outline)
        for i, (ax, az) in enumerate(outline):
            mem.append((ax, az))
            bx, bz = outline[(i + 1) % len(outline)]
            if i >= 2:
                mx, mz = (ax + bx) / 2, (az + bz) / 2
                mem.append((mx + (cx - mx) * 0.18, mz + (cz - mz) * 0.18))
        B20.tprism(f"{prefix}Membrane", WS.ccw(mem), 0.06, 0.04, m)
    else:
        for row in range(3):
            cnt = n - row
            for k in range(cnt):
                t = k / max(1, cnt - 1)
                L = span * (1.0 - 0.28 * row) * (0.55 + 0.45 * math.sin(t * math.pi * 0.5 + 0.3))
                ang = math.radians(8 + 70 * t)
                ox, oz = 0.35 * row, 0.15 * row
                dx, dz = math.cos(ang), math.sin(ang)
                w = 0.55 - 0.1 * row
                pts = [(ox, oz), (ox + dx * L * 0.35 - dz * w, oz + dz * L * 0.35 + dx * w), (ox + dx * L * 0.8 - dz * w * 0.6, oz + dz * L * 0.8 + dx * w * 0.6),
                       (ox + dx * L, oz + dz * L), (ox + dx * L * 0.45 + dz * w * 0.5, oz + dz * L * 0.45 - dx * w * 0.5)]
                B20.tprism(f"{prefix}F{row}{k}", WS.ccw(pts), 0.04 + 0.05 * row, 0.06, m)
    _xform(s, mtx)


def folded_wing(prefix, side, m, y=0.56):
    """A folded angel's wing down the back (torso rest frame): a long teardrop from the shoulder blade to a point near the
    ground, rounded covert feathers along its top and long primaries down to the tip, layered outward from the back."""
    def X(pts):
        return WS.ccw([(side * x, z) for x, z in pts])
    shape = [(0.35, 4.2), (0.7, 4.85), (1.35, 5.05), (1.95, 4.6), (2.1, 3.6), (1.9, 2.2), (1.45, 0.9), (1.0, 0.25), (0.75, 1.2), (0.5, 2.6),
             (0.35, 3.6)]
    B20.tprism(f"{prefix}Web", X(shape), y + 0.06, 0.12, m)
    k = 0
    # coverts: a few rows of rounded little feathers over the top of the wing
    for row, (z0, n) in enumerate(((4.55, 5), (4.1, 5), (3.6, 4))):
        for i in range(n):
            x = 0.55 + i * 0.32 + row * 0.08
            if x > 2.0:
                continue
            f = [(x - 0.17, z0 + 0.12), (x + 0.17, z0 + 0.12), (x + 0.15, z0 - 0.25), (x, z0 - 0.42), (x - 0.15, z0 - 0.25)]
            B20.tprism(f"{prefix}Covert{k}", X(f), y + 0.14 + row * 0.025, 0.05, m)
            k += 1
    # primaries: long lance feathers fanning slightly, from the coverts down to the tip
    for i in range(7):
        t = i / 6
        top = (0.55 + t * 1.35, 3.35 - t * 0.2)
        tip = (0.95 + t * 0.75, 0.3 + t * 1.6)
        dx, dz = tip[0] - top[0], tip[1] - top[1]
        L = math.hypot(dx, dz)
        nx, nz = -dz / L * 0.17, dx / L * 0.17
        f = [(top[0] - nx, top[1] - nz), (top[0] + nx, top[1] + nz), (tip[0] + nx * 0.5, tip[1] + nz * 0.5 + 0.2), tip,
             (tip[0] - nx * 0.6, tip[1] - nz * 0.6 + 0.25)]
        B20.tprism(f"{prefix}Primary{i}", X(f), y + 0.12 + (6 - i) * 0.018, 0.05, m)


def claws(fig, side, mat):
    j = "rshoulder" if side > 0 else "lshoulder"
    fig.build(j, lambda: [cone(f"Claw{side}{k}", 0.055, 0.0, 0.3, (side * 1.5 - 0.3 + k * 0.3, -0.32, 1.88), mat, verts=4, rot=(math.pi, 0, 0))
                          for k in range(3)])


# ================================================================== the statues

def founder_statue(M):
    K = mats()
    st, dk, br, gl = K["soot"], K["sootdk"], K["bronze"], K["gilt"]
    rnd = random.Random(2701)
    H = plinth_square("P", 3.4, 3.6, st, dk, plaque=M["brass"])
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"rshoulder": (-160, 0, -8), "lshoulder": (-55, 0, 22), "neck": (-8, 0, 0)})
    body(fig, br, face="stern", dark=K["bronzedk"])
    robe(fig, br)
    for side in (-1, 1):
        sleeve(fig, side, br)

    def gown():
        tube("GownEdgeL", [(-0.2, -0.56, 4.0), (-0.35, -0.6, 3.0), (-0.5, -0.9, 0.05)], 0.05, K["bronzedk"])
        tube("GownEdgeR", [(0.2, -0.56, 4.0), (0.35, -0.6, 3.0), (0.5, -0.9, 0.05)], 0.05, K["bronzedk"])
        tube("Chain", [(-0.75, -0.52, 3.95), (-0.45, -0.56, 3.35), (0.0, -0.58, 3.1), (0.45, -0.56, 3.35), (0.75, -0.52, 3.95)], 0.04, gl)
        cyl("Medal", 0.2, 0.05, (0, -0.6, 2.95), gl, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
        foil("MedalFoil", 0, -0.63, 2.95, 0.1, gl, lobes=4, thick=0.012)
        box("Collar", (1.6, 1.12, 0.22), (0, 0, 4.0), br, bevel=0.06)
    fig.build("torso", gown)

    def cap():
        box("Cap", (1.25, 1.25, 0.32), (0, 0, 5.12), K["bronzedk"], bevel=0.06)
        box("Board", (1.7, 1.7, 0.07), (0, 0, 5.32), K["bronzedk"], bevel=0.015)
        sphere("Button", 0.06, (0, 0, 5.37), gl, seg=8, rings=4)
        tube("Tassel", [(0, 0, 5.37), (0.6, -0.1, 5.36), (0.82, -0.62, 5.3), (0.83, -0.7, 4.95)], 0.025, gl)
        sphere("TasselEnd", 0.06, (0.83, -0.7, 4.9), gl, seg=8, rings=4, scale=(1, 1, 1.6))
    fig.build("head", cap)

    def key():
        x = 1.5
        hoop("KeyBow", (x, 0, 1.45), 0.28, "Y", gl, thick=0.05)
        foil("KeyFoil", x, -0.02, 1.45, 0.16, gl, lobes=4, thick=0.02)
        tube("KeyShaft", [(x, 0, 1.17), (x, 0, -0.4)], 0.06, gl, poly=True)
        box("KeyBit", (0.26, 0.08, 0.36), (x + 0.15, 0, -0.18), gl, bevel=0.02)
        box("KeyGrip", (0.5, 1.15, 0.42), (x, 0, 2.05), br, bevel=0.1)
    fig.build("rshoulder", key)

    def book():
        box("Book", (0.95, 0.32, 1.25), (-1.45, -0.62, 2.25), K["bronzedk"], bevel=0.04)
        box("Pages", (0.88, 0.28, 1.18), (-1.39, -0.62, 2.25), br, bevel=0.02)
    fig.build("lshoulder", book)
    set_group("Main")
    _moss("Moss", [(-1.8, -1.9, 0.36), (1.9, -1.6, 0.36), (1.2, 1.9, 0.36)], K["moss"], rnd, size=0.12)
    return _dims()


def mourning_angel(M):
    K = mats()
    mb, st, dk = K["marble"], K["soot"], K["sootdk"]
    rnd = random.Random(2702)
    # the tomb chest with carved panels and a wreath
    box("ChestFoot", (5.4, 3.4, 0.35), (0, 0, 0.175), dk, bevel=0.05)
    box("Chest", (5.0, 3.0, 2.0), (0, 0, 1.35), st, bevel=0.04)
    box("Lid", (5.4, 3.4, 0.3), (0, 0, 2.5), dk, bevel=0.06)
    for sx in (-1, 1):
        s = _mark()
        _panel(f"ChestPanel{sx}", 0, 0, 0.6, 1.6, 1.5, dk, thick=0.03)
        _xform(s, Matrix.Translation((sx * 1.3, -1.505, 0)))
    s = _mark()
    hoop("Wreath", (0, 0, 1.35), 0.55, "Y", dk, thick=0.1)
    for k in range(14):
        a = k / 14 * 2 * math.pi
        sphere(f"WreathLeaf{k}", 0.12, (math.cos(a) * 0.55, 0, 1.35 + math.sin(a) * 0.55), dk, seg=6, rings=4, scale=(1.6, 0.5, 0.8))
    _xform(s, Matrix.Translation((0, -1.56, 0)))
    H = 2.65
    set_group("Figure")
    fig = R6(base=(0, 0.2, H), pose={"neck": (28, 0, 0), "rshoulder": (-128, 0, 28), "lshoulder": (-128, 0, -28), "root": (8, 0, 0)})
    body(fig, mb, face="sorrow")
    robe(fig, mb, w0=2.9, d0=1.9)
    for side in (-1, 1):
        sleeve(fig, side, mb, bell=1.08)

    def veil():
        sphere("Veil", 0.82, (0, 0.08, 4.62), mb, seg=16, rings=8, scale=(1.0, 0.95, 0.98))
        strip("VeilFall", [(0, 0.55, 4.9), (0, 0.85, 3.8), (0, 0.95, 2.4), (0, 1.0, 0.8)], 1.6, (1, 0, 0), mb, thick=0.06)
    fig.build("head", veil)
    # folded wings down the back
    for side in (-1, 1):
        fig.build("torso", lambda side=side: folded_wing(f"Wing{side}", side, mb))
    set_group("Main")
    _moss("Moss", [(-2.4, -1.6, 0.36), (2.2, -1.65, 0.36), (2.5, 1.2, 2.65)], K["moss"], rnd, size=0.12)
    _crack("Crack", (-1.9, -1.505, 2.0), (0.2, 0, -1), (1, 0, 0), 0.9, rnd, K["hollow"])
    return _dims()


def gargoyle(M):
    K = mats()
    st, dk = K["sootdk"], K["soot"]
    rnd = random.Random(2703)
    lathe("ColFoot", [(0, 0), (1.9, 0), (1.9, 0.35), (1.6, 0.5), (1.5, 0.7), (0, 0.7)], dk, seg=8)
    lathe("Col", [(0, 0.7), (1.3, 0.7), (1.25, 3.6), (0, 3.6)], dk, seg=8)
    lathe("ColCap", [(0, 3.6), (1.45, 3.6), (1.75, 3.85), (1.75, 4.1), (0, 4.1)], st, seg=8)
    H = 4.1
    set_group("Figure")
    # sitting on the column's front edge: legs straight out over it (the R6 sit)
    fig = R6(base=(0, 0.3, H - 2.0 * S), pose={"lhip": (-90, 0, 0), "rhip": (-90, 0, 0), "rshoulder": (-62, 0, -6), "lshoulder": (-62, 0, 6),
                                              "neck": (-6, 0, 0), "root": (6, 0, 0)})
    body(fig, st, face="none")

    def head():
        for sx in (-1, 1):
            tube(f"Horn{sx}", [(sx * 0.4, 0.1, 5.0), (sx * 0.7, 0.2, 5.4), (sx * 0.78, 0.45, 5.75), (sx * 0.62, 0.7, 5.95)], 0.09, dk)
            cone(f"Ear{sx}", 0.16, 0.0, 0.5, (sx * 0.72, 0.0, 4.75), st, verts=5, rot=(0, sx * 1.2, 0))
            sphere(f"EyeSocket{sx}", 0.1, (sx * 0.24, -0.58, 4.62), K["hollow"], seg=8, rings=4, scale=(1.2, 0.4, 0.8))
            box(f"Brow{sx}", (0.42, 0.14, 0.12), (sx * 0.24, -0.6, 4.8), st, bevel=0.04, rot=(0, sx * -0.35, 0))
        box("Mouth", (0.7, 0.1, 0.2), (0, -0.6, 4.26), K["hollow"], bevel=0.04)
        for k in range(5):
            cone(f"Fang{k}", 0.05, 0.0, 0.13, (-0.28 + k * 0.14, -0.64, 4.34), st, verts=4, rot=(math.pi, 0, 0))
        box("Snout", (0.5, 0.25, 0.3), (0, -0.66, 4.5), st, bevel=0.08)
    fig.build("head", head)

    def back():
        tube("Tail", [(0, 0.5, 2.1), (0, 1.2, 1.6), (0.4, 1.6, 0.6), (0.2, 1.3, -0.6), (-0.3, 0.9, -1.2)], 0.1, st)
        cone("TailTip", 0.16, 0.0, 0.4, (-0.38, 0.82, -1.45), st, verts=4, rot=(0, 0.5, 0))
        for k in range(4):
            cone(f"Spine{k}", 0.1, 0.0, 0.25, (0, 0.55, 2.4 + k * 0.45), st, verts=4, rot=(-math.pi / 2, 0, 0))
    fig.build("torso", back)
    # bat wings spread up and out from the shoulder blades
    for side in (-1, 1):
        mt = Matrix.Translation((side * 0.6, 0.55, 3.7)) @ Matrix.Rotation(side * -0.5, 4, "Z") @ Matrix.Rotation(math.radians(30), 4, "X")
        if side < 0:
            mt = mt @ Matrix.Rotation(math.pi, 4, "Z")
        fig.build("torso", lambda side=side, mt=mt: wing(f"Wing{side}", mt, st, span=3.0, bat=True, dark=dk))
    for side in (-1, 1):
        claws(fig, side, dk)
    set_group("Main")
    _moss("Moss", [(1.2, -1.2, 0.7), (-1.4, 0.6, 0.7), (0.6, 1.3, 4.1)], K["moss"], rnd, size=0.12)
    return _dims()


def vampire_lord(M):
    K = mats()
    bk, gl, cr = K["black"], K["gilt"], K["crimson"]
    lathe("Base", [(0, 0), (2.2, 0), (2.2, 0.3), (1.95, 0.45), (1.8, 0.6), (1.8, 2.3), (2.05, 2.45), (2.05, 2.7), (0, 2.7)], bk, seg=8)
    hoop("BaseGilt", (0, 0, 2.47), 2.06, "Z", gl, thick=0.035)
    hoop("BaseGilt2", (0, 0, 0.47), 1.97, "Z", gl, thick=0.03)
    H = 2.7
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"rshoulder": (-20, -62, 0), "lshoulder": (-20, 62, 0), "neck": (4, 0, 0)})
    body(fig, bk, face="stern", dark=cr)
    # the cape: from the shoulders out to each hand and down to the ground behind, crimson inside, black outside
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        sh = fig.at("torso", (side * 0.9, 0.45, 4.0))
        hand = fig.at(j, (side * 1.5, 0.3, 2.1))
        low = fig.at("torso", (side * 2.2, 0.9, 0.05))
        mid = fig.at("torso", (side * 0.4, 0.95, 0.05))
        for k, (mat, off) in enumerate(((cr, -0.03), (bk, 0.05))):
            sheet(f"Cape{side}{k}", [[p + Vector((0, off, 0)) for p in (sh, hand, low, mid)]], mat, 0.05)

    def collar():
        for sx in (-1, 1):
            B20.tprism(f"Collar{sx}", WS.ccw([(sx * 0.2, 3.95), (sx * 1.05, 4.0), (sx * 1.25, 5.3), (sx * 0.5, 5.0)]), 0.62, 0.06, bk)
            B20.tprism(f"CollarIn{sx}", WS.ccw([(sx * 0.25, 3.98), (sx * 0.98, 4.03), (sx * 1.15, 5.15), (sx * 0.52, 4.94)]), 0.57, 0.04, cr)
        sphere("Gem", 0.17, (0, -0.56, 3.75), cr, seg=12, rings=6, scale=(1, 0.5, 1.2))
        hoop("GemSetting", (0, -0.55, 3.75), 0.2, "Y", gl, thick=0.03)
        tube("GemChain", [(-0.6, -0.52, 4.0), (0, -0.56, 3.9), (0.6, -0.52, 4.0)], 0.025, gl)
    fig.build("torso", collar)
    fig.build("head", lambda: [cone(f"Fang{sx}", 0.04, 0.0, 0.12, (sx * 0.09, -0.61, 4.24), K["marble"], verts=4, rot=(math.pi, 0, 0)) for sx in (-1, 1)])
    set_group("Main")
    return _dims()


def werewolf_howl(M):
    K = mats()
    st, dk, worn = K["soot"], K["sootdk"], K["worn"]
    rnd = random.Random(2705)
    for k, (x, y, z, r) in enumerate(((0, 0, 0.6, 1.6), (-1.1, 0.4, 0.5, 1.2), (1.2, 0.2, 0.55, 1.25), (0.5, -0.9, 0.4, 1.0), (-0.7, -0.6, 1.3, 0.9),
                                     (0.9, 0.5, 1.4, 0.8))):
        lump(f"Rock{k}", (x, y, z), r, worn if k % 2 else dk, rnd, squash=0.75)
    box("RockTop", (3.0, 2.2, 0.4), (0, 0, 1.7), worn, bevel=0.12)
    H = 1.9
    tube("MoonRod", [(0.6, 1.3, 1.0), (0.6, 1.3, 9.4)], 0.07, dk, poly=True)
    B20.tprism("Moon", WS.crescent(0.6, 10.3, 1.3, shift=0.42, tilt=2.6), 1.3, 0.14, K["gilt"])
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"root": (12, 0, 0), "neck": (-42, 0, 0), "rshoulder": (-35, 0, -14), "lshoulder": (-20, 0, 18),
                                   "lhip": (-28, 0, 0), "rhip": (8, 0, 0), "lift": 0.12})
    body(fig, st, face="none")

    def wolf():
        box("Snout", (0.62, 0.85, 0.5), (0, -0.85, 4.32), st, bevel=0.14, segments=3)
        sphere("Nose", 0.12, (0, -1.27, 4.48), dk, seg=10, rings=5)
        box("Jaw", (0.5, 0.7, 0.18), (0, -0.78, 4.06), st, bevel=0.06, rot=(0.25, 0, 0))
        for sx in (-1, 1):
            cone(f"Ear{sx}", 0.22, 0.0, 0.62, (sx * 0.38, 0.05, 5.2), st, verts=4, rot=(0.2, sx * -0.2, 0))
            sphere(f"Eye{sx}", 0.08, (sx * 0.27, -0.6, 4.66), dk, seg=8, rings=4, scale=(1.3, 0.4, 0.7))
            cone(f"Fang{sx}", 0.04, 0.0, 0.14, (sx * 0.16, -1.15, 4.12), K["marble"], verts=4, rot=(math.pi, 0, 0))
        for k in range(12):
            a = k / 12 * 2 * math.pi
            sphere(f"Ruff{k}", 0.34, (math.cos(a) * 0.62, math.sin(a) * 0.55 + 0.05, 4.02), st, seg=6, rings=4, scale=(1, 1, 0.7))
    fig.build("head", wolf)

    def fur():
        for k in range(10):
            x, z = rnd.uniform(-0.85, 0.85), rnd.uniform(2.2, 3.9)
            cone(f"Tuft{k}", 0.12, 0.0, 0.35, (x, 0.5, z), st, verts=4, rot=(math.radians(110), 0, 0))
        tube("Tail", [(0, 0.5, 2.1), (0, 1.1, 1.7), (0.2, 1.4, 0.9), (0.1, 1.3, 0.3)], 0.17, st)
    fig.build("torso", fur)
    for side in (-1, 1):
        claws(fig, side, dk)
    set_group("Main")
    _moss("Moss", [(-1.3, -0.8, 1.0), (1.0, -1.0, 0.9), (-0.2, 0.9, 1.9), (1.6, 0.4, 1.4)], K["moss"], rnd, size=0.16)
    return _dims()


def lantern_priest(M):
    K = mats()
    mb, st, dk, gl, cr = K["marble"], K["soot"], K["sootdk"], K["gilt"], K["crimson"]
    rnd = random.Random(2706)
    for k, (w, z) in enumerate(((4.6, 0.0), (3.9, 0.4), (3.2, 0.8))):
        box(f"Step{k}", (w, w, 0.4), (0, 0, z + 0.2), st if k % 2 else dk, bevel=0.05)
    H = 1.2
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"rshoulder": (-72, 0, -6), "lshoulder": (-28, 0, 10), "neck": (6, 0, 0)})
    body(fig, mb, face="stern")
    robe(fig, mb, w0=2.8, d0=1.8)
    for side in (-1, 1):
        sleeve(fig, side, mb)

    def vest():
        for sx in (-1, 1):
            strip(f"Stole{sx}", [(sx * 0.35, -0.56, 4.0), (sx * 0.4, -0.62, 2.6), (sx * 0.42, -0.9, 0.9)], 0.3, (1, 0, 0), cr, thick=0.04)
            foil(f"StoleFoil{sx}", sx * 0.42, -0.86, 1.2, 0.1, gl, lobes=4, thick=0.012)
        sphere("Hood", 0.75, (0, 0.62, 3.95), mb, seg=14, rings=7, scale=(1.25, 0.55, 0.55))
        hoop("Halo", (0, 0.72, 4.6), 0.95, "Y", gl, thick=0.05)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            cone(f"Ray{k}", 0.04, 0.0, 0.3, (math.cos(a) * 1.15, 0.72, 4.6 + math.sin(a) * 1.15), gl, verts=4, rot=(0, -a + math.pi / 2, 0))
    fig.build("torso", vest)
    # the staff, upright in the left hand with a crescent on top; the lantern hanging from the right hand
    lh = fig.at("lshoulder", (-1.5, 0, 2.15))
    tube("Staff", [(lh.x, lh.y, H + 0.02), (lh.x, lh.y, lh.z + 3.4)], 0.07, gl, poly=True)
    B20.tprism("StaffMoon", WS.crescent(lh.x, lh.z + 3.75, 0.42, shift=0.4, tilt=math.pi / 2), lh.y, 0.06, gl)
    rh = fig.at("rshoulder", (1.5, 0, 2.05))
    zt = rh.z - 0.1
    tube("LanternBail", [(rh.x, rh.y, rh.z), (rh.x, rh.y, zt - 0.1)], 0.02, gl, poly=True)
    lz = zt - 1.0
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tube(f"LanternPost{k}", [(rh.x + math.cos(a) * 0.22, rh.y + math.sin(a) * 0.22, lz), (rh.x + math.cos(a) * 0.22, rh.y + math.sin(a) * 0.22, lz + 0.75)],
             0.022, gl, square=True, poly=True)
    cone("LanternRoof", 0.36, 0.05, 0.25, (rh.x, rh.y, lz + 0.86), gl, verts=4, rot=(0, 0, math.pi / 4))
    box("LanternBase", (0.44, 0.44, 0.07), (rh.x, rh.y, lz - 0.03), gl, bevel=0.01)
    set_group("Glow")
    flame("LanternFlame", (rh.x, rh.y, lz + 0.12), h=0.36)
    set_group("Main")
    _moss("Moss", [(-2.0, -2.1, 0.4), (1.7, -1.8, 0.8)], K["moss"], rnd, size=0.1)
    return _dims()


def hollow_wraith(M):
    K = mats()
    st, dk = K["sootdk"], K["soot"]
    rnd = random.Random(2707)
    lathe("Spire", [(0, 0), (1.6, 0), (1.6, 0.4), (1.2, 0.55), (0.75, 1.0), (0.55, 2.6), (0.85, 2.9), (0.9, 3.1), (0, 3.1)], dk, seg=8)
    for k in range(4):
        s = _mark()
        _panel(f"SpirePanel{k}", 0, 0, 1.0, 0.6, 1.5, st, thick=0.02)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z") @ Matrix.Translation((0, -0.6, 0)))
    H = 3.1
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"rshoulder": (-75, 0, -10), "lshoulder": (-75, 0, 10), "neck": (12, 0, 0), "lift": 0.55})
    body(fig, st, head=False, legs=False, face="none")

    def shroud():
        rows = []
        for i in range(9):
            t = i / 8
            z = 2.2 - t * 2.45
            r = 1.25 + 0.35 * t
            row = []
            for j in range(25):
                a = j / 24 * 2 * math.pi
                jag = 0.0 if i < 6 else (0.25 * (t - 0.6) * math.sin(a * 7) + rnd.uniform(-0.12, 0.12))
                row.append(Vector((math.cos(a) * r * 0.95, math.sin(a) * r * 0.72, z + jag)))
            rows.append(row)
        _mesh("Shroud", rows, st, 0.06)
        for k in range(6):
            a = k / 6 * 2 * math.pi + 0.3
            tube(f"Wisp{k}", [(math.cos(a) * 0.9, math.sin(a) * 0.7, -0.2), (math.cos(a) * 0.5, math.sin(a) * 0.4, -0.45)], 0.06, st)
        tube("Stem", [(0, 0, 0.3), (0, 0, -0.55)], 0.25, dk, poly=True)
        sphere("Cowl", 0.92, (0, 0.12, 4.55), st, seg=16, rings=9, scale=(1.0, 1.1, 1.12))
        sphere("Void", 0.68, (0, -0.15, 4.45), K["hollow"], seg=14, rings=7, scale=(0.9, 0.7, 1.05))
        cone("HoodPeak", 0.5, 0.0, 0.7, (0, 0.35, 5.45), st, verts=8, rot=(0.5, 0, 0))
        strip("HoodFall", [(0, 0.8, 4.9), (0, 1.0, 3.6), (0, 0.95, 2.4)], 1.5, (1, 0, 0), st, thick=0.05)
    fig.build("torso", shroud)
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        def arm(side=side):
            frustum(f"Sleeve{side}", (side * 1.5, 0), 1.6, 1.5, 1.7, 1.1, 1.1, 3.9, st, bevel=0.03)
            for k in range(4):
                strip(f"Tatter{side}{k}", [(side * 1.5 - 0.6 + k * 0.4, 0.55, 1.8), (side * 1.5 - 0.6 + k * 0.4, 0.75, 1.2 - 0.2 * (k % 2))], 0.28, (1, 0, 0), st,
                      thick=0.03)
            for k in range(4):
                box(f"Finger{side}{k}", (0.12, 0.12, 0.7), (side * 1.5 - 0.27 + k * 0.18, -0.2, 1.45), dk, bevel=0.04)
            hoop(f"Shackle{side}", (side * 1.5, 0, 2.0), 0.62, "Z", dk, thick=0.06)
            for k in range(4):
                hoop(f"Link{side}{k}", (side * 1.5 + 0.1 * k, 0.55, 1.75 - 0.22 * k), 0.12, "X" if k % 2 else "Y", dk, thick=0.03)
        fig.build(j, arm)
    set_group("Main")
    _moss("Moss", [(1.2, -1.0, 0.4), (-1.1, 0.9, 0.4)], K["moss"], rnd, size=0.1)
    return _dims()


def knight_guardian(M):
    K = mats()
    st, dk, cr, gl = K["soot"], K["sootdk"], K["crimson"], K["gilt"]
    rnd = random.Random(2708)
    H = plinth_square("P", 3.4, 2.4, dk, st)
    B20._crest("PlinthCrest", 0, -1.73, 1.3, M, gl, s=1.4)
    set_group("Figure")
    fig = R6(base=(0, 0, H), pose={"rshoulder": (-38, 0, 22), "lshoulder": (-38, 0, -22)})
    body(fig, st, head=False)

    def armour():
        box("Breast", (2.15, 1.2, 1.7), (0, 0, 3.2), st, bevel=0.2, segments=3)
        box("Tabard", (1.2, 0.08, 2.9), (0, -0.62, 2.5), cr, bevel=0.03)
        B20._crest("TabardCrest", 0, -0.68, 3.25, M, gl, s=0.9)
        box("Belt", (2.1, 1.12, 0.2), (0, 0, 2.15), dk, bevel=0.04)
        sphere("Buckle", 0.12, (0, -0.58, 2.15), gl, seg=8, rings=4, scale=(1, 0.5, 1))
        box("Shield", (1.6, 0.18, 2.0), (0, 0.65, 3.1), dk, bevel=0.06)
        foil("ShieldFoil", 0, 0.76, 3.2, 0.45, gl, lobes=4, thick=0.03)
    fig.build("torso", armour)

    def helm():
        box("Helm", (1.3, 1.3, 1.35), (0, 0, 4.55), st, bevel=0.28, segments=4)
        box("Visor", (0.9, 0.06, 0.08), (0, -0.66, 4.62), K["hollow"], bevel=0.01)
        for k in range(5):
            box(f"Breath{k}", (0.05, 0.05, 0.22), (-0.24 + k * 0.12, -0.66, 4.28), K["hollow"], bevel=0.0, segments=1)
        box("Crest", (0.14, 1.2, 0.35), (0, 0.05, 5.32), cr, bevel=0.05)
        box("Gorget", (1.4, 1.3, 0.25), (0, 0, 4.0), dk, bevel=0.08)
    fig.build("head", helm)
    for side, j in ((1, "rshoulder"), (-1, "lshoulder")):
        fig.build(j, lambda side=side: [sphere(f"Pauldron{side}", 0.78, (side * 1.5, 0, 3.9), st, seg=14, rings=7, scale=(1.0, 0.85, 0.6)),
                                        box(f"Gauntlet{side}", (1.12, 1.12, 0.55), (side * 1.5, 0, 2.3), dk, bevel=0.1)])
    for side, j in ((1, "rhip"), (-1, "lhip")):
        fig.build(j, lambda side=side: [box(f"Greave{side}", (1.1, 1.1, 1.2), (side * 0.5, 0, 0.6), dk, bevel=0.1),
                                        sphere(f"Knee{side}", 0.4, (side * 0.5, -0.5, 1.3), st, seg=10, rings=5, scale=(1, 0.6, 1))])
    # the greatsword, point down on the plinth, its pommel between the hands
    hr, hl = fig.at("rshoulder", (1.5, 0, 2.1)), fig.at("lshoulder", (-1.5, 0, 2.1))
    hc = (hr + hl) / 2
    x, y = hc.x, hc.y
    box("Blade", (0.32, 0.06, hc.z - H - 0.9), (x, y, H + (hc.z - H - 0.9) / 2), M["brasssteel"], bevel=0.02)
    box("Guard", (1.5, 0.16, 0.16), (x, y, hc.z - 0.75), gl, bevel=0.03)
    tube("Grip", [(x, y, hc.z - 0.68), (x, y, hc.z + 0.3)], 0.09, dk, poly=True)
    sphere("Pommel", 0.17, (x, y, hc.z + 0.4), gl, seg=12, rings=6)
    set_group("Main")
    _moss("Moss", [(-1.8, -1.8, 0.36), (1.9, 1.7, 0.36)], K["moss"], rnd, size=0.1)
    return _dims()


def fencing_duel(M):
    K = mats()
    st, dk, br, gl = K["soot"], K["sootdk"], K["bronze"], K["gilt"]
    rnd = random.Random(2709)
    box("Foot", (11.4, 3.2, 0.35), (0, 0, 0.175), dk, bevel=0.05)
    box("Plinth", (11.0, 2.8, 1.2), (0, 0, 0.95), st, bevel=0.04)
    box("Top", (11.3, 3.1, 0.22), (0, 0, 1.66), dk, bevel=0.05)
    for k in range(5):
        foil(f"PlinthFoil{k}", -4.4 + k * 2.2, -1.41, 0.95, 0.28, dk, lobes=4, thick=0.03)
    H = 1.77
    # the lunge: front leg forward, back leg back, the hips lowered to keep both feet down; each faces the other
    drop = 2.0 * (1 - math.cos(math.radians(34)))
    for k, (gx, yaw) in enumerate(((-3.35, math.pi / 2), (3.35, -math.pi / 2))):
        set_group("Figure" if k == 0 else "Figure2")
        fig = R6(base=(gx, 0, H), yaw=yaw, pose={"rhip": (-34, 0, 0), "lhip": (34, 0, 0), "rshoulder": (-88, 0, -4), "lshoulder": (130, 0, -25),
                                                 "lift": -drop * 0.98, "root": (-6, 0, 0)})
        body(fig, br, face="none")

        def mask():
            box("Mask", (1.24, 0.12, 1.1), (0, -0.62, 4.5), K["bronzedk"], bevel=0.04)
            for i in range(5):
                tube(f"MaskBar{i}", [(-0.5 + i * 0.25, -0.69, 4.0), (-0.5 + i * 0.25, -0.69, 5.0)], 0.02, gl, poly=True)
            for i in range(4):
                tube(f"MaskRail{i}", [(-0.55, -0.69, 4.12 + i * 0.25), (0.55, -0.69, 4.12 + i * 0.25)], 0.02, gl, poly=True)
            box("Bib", (1.0, 0.1, 0.4), (0, -0.62, 3.85), br, bevel=0.04)
        fig.build("head", mask)

        def jacket():
            box("Plastron", (1.5, 0.08, 1.6), (0, -0.53, 3.1), K["bronzedk"], bevel=0.03)
            box("JacketHem", (2.15, 1.15, 0.3), (0, 0, 2.15), br, bevel=0.05)
        fig.build("torso", jacket)

        def sabre():
            x = 1.5
            hoop("SabreGuard", (x, -0.1, 1.95), 0.32, "X", gl, thick=0.04)
            tube("SabreGrip", [(x, 0, 2.2), (x, 0, 1.7)], 0.07, K["bronzedk"], poly=True)
            box("SabreBlade", (0.07, 0.14, 3.6), (x, 0, 1.7 - 1.8), M["brasssteel"], bevel=0.01)
        fig.build("rshoulder", sabre)
        set_group("Main")
    _moss("Moss", [(-5.3, -1.4, 0.36), (5.0, 1.4, 0.36)], K["moss"], rnd, size=0.1)
    return _dims()


def raven_scholar(M):
    K = mats()
    mb, st, dk, br = K["marble"], K["soot"], K["sootdk"], K["bronze"]
    rnd = random.Random(2710)
    box("BenchFoot", (5.6, 2.6, 0.3), (0, 0, 0.15), dk, bevel=0.04)
    for sx in (-1, 1):
        box(f"BenchLeg{sx}", (0.8, 2.0, 1.9), (sx * 2.1, 0, 1.25), st, bevel=0.06)
        foil(f"BenchFoil{sx}", sx * 2.1, -1.01, 1.25, 0.24, dk, lobes=4, thick=0.025)
    box("Seat", (5.4, 2.4, 0.35), (0, 0, 2.37), dk, bevel=0.06)
    H = 2.55
    set_group("Figure")
    # sitting (the R6 sit): legs straight out, the torso's foot on the seat
    fig = R6(base=(0, 0.35, H - 2.0 * S), pose={"lhip": (-90, 0, 0), "rhip": (-90, 0, 0), "rshoulder": (-58, 0, 24), "lshoulder": (-58, 0, -24),
                                              "neck": (24, 0, 0)})
    body(fig, mb, face="smile")

    def hair():
        sphere("Hair", 0.7, (0, 0.12, 4.75), mb, seg=16, rings=8, scale=(1.0, 0.95, 0.85))
        sphere("Bun", 0.32, (0, 0.62, 4.85), mb, seg=12, rings=6)
        box("Scarf", (2.15, 1.15, 0.3), (0, 0, 3.95), mb, bevel=0.1)
        strip("ScarfEnd", [(0.5, -0.6, 3.9), (0.6, -0.7, 3.2), (0.55, -0.72, 2.7)], 0.32, (1, 0, 0), mb, thick=0.04)
    fig.build("head", hair)
    fig.build("torso", lambda: frustum("Skirt", (0, 0), 2.3, 1.3, 1.4, 2.05, 1.08, 2.2, mb, bevel=0.04))
    hr, hl = fig.at("rshoulder", (1.5, -0.2, 2.1)), fig.at("lshoulder", (-1.5, -0.2, 2.1))
    c = (hr + hl) / 2
    s = _mark()
    box("BookL", (1.0, 0.06, 1.3), (-0.52, 0, 0), br, bevel=0.02, rot=(0, 0, 0.25))
    box("BookR", (1.0, 0.06, 1.3), (0.52, 0, 0), br, bevel=0.02, rot=(0, 0, -0.25))
    box("Spine", (0.12, 0.1, 1.3), (0, 0.04, 0), K["bronzedk"], bevel=0.02)
    _xform(s, Matrix.Translation(c + Vector((0, -0.1, 0.05))) @ Matrix.Rotation(math.radians(-50), 4, "X"))
    sh = fig.at("torso", (0.95, 0.0, 4.02))
    raven("RavenShoulder", (sh.x, sh.y, sh.z), -math.pi / 2 + 0.6, 2.6, br, K["bronzedk"])
    raven("RavenBench", (-1.9, -0.4, 2.55), -math.pi / 2 - 0.4, 2.8, br, K["bronzedk"])
    raven("RavenBook", (c.x + 0.4, c.y - 0.3, c.z + 0.65), -math.pi / 2 + 1.4, 2.2, br, K["bronzedk"])
    set_group("Main")
    _moss("Moss", [(-2.4, -1.2, 0.3), (2.6, 1.1, 0.3)], K["moss"], rnd, size=0.1)
    return _dims()


BUILDERS = {
    "FounderStatue": founder_statue,
    "MourningAngel": mourning_angel,
    "Gargoyle": gargoyle,
    "VampireLord": vampire_lord,
    "WerewolfHowl": werewolf_howl,
    "LanternPriest": lantern_priest,
    "HollowWraith": hollow_wraith,
    "KnightGuardian": knight_guardian,
    "FencingDuel": fencing_duel,
    "RavenScholar": raven_scholar,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.1 for n in BUILDERS})
P.PREVIEW_PAD.update({"FencingDuel": 1.0, "WerewolfHowl": 1.05})
