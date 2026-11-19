"""Accessories batch P1: the Standing Path wardrobe (2.34, docs/expansion/14-Progression-and-Identity.md §6.1). Earned,
never sold: each is granted when a path reaches its tier (Services.Player.Paths).

  AcademicPin        Academic 3 (Honor Student). A gilt lapel brooch on the left breast: an oval with a beaded rim, a
                     crimson enamel field, an open book and a quill crossed over it in gilt relief, two short crimson silk
                     ribbon tails. Slot Pin, Torso mount
  KnuckleWraps       Combat 4 (Notorious). Fighter's hand wraps on both hands: worn linen tape wound round the knuckles and
                     wrist in overlapping turns, ink-dark scuffs where the punches land, a frayed loose end hanging from
                     each wrist, a black leather wrist band with a brass stud. Pieces WrapL (LeftArm), WrapR (RightArm).
                     Slot Hands
  SilverSigil        Supernatural 4 (Keeper of Secrets). A silver pendant on a fine chain round the neck: a disc with a
                     beaded rim, a black enamel field, a crescent moon and a seven-point star in silver relief, a
                     moonstone (faint cold glow) at the star's heart. Slot Collar, Torso mount

Space as nh_acc (studs, -Y front, +X the character's left). Torso 2 x 2 x 1 at the origin; arms at x = +-1.5 (each 1 x 2 x 1,
the hand at the bottom, z -1 to about -0.6); the neck at the torso's top (z 1.0).
Run (geometry): E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- AcademicPin,KnuckleWraps,SilverSigil --nobake --norender
Bake: bash E:/NH-Work/acc/bake_batch.sh AcademicPin,KnuckleWraps,SilverSigil
"""
import math, os, sys
import bpy
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_acc as A
from nh_acc import item, piece, lerp
from nh_acc_batch1 import ccw
import nh_acc_batch3 as B3

MOON = (0.62, 0.78, 1.0)


def oval(rx, rz, n=40):
    return [(rx * math.cos(a), rz * math.sin(a)) for a in (2 * math.pi * k / n for k in range(n))]


# ================================================================== the academic pin
@item("AcademicPin", "Academic pin", views=["front34", "front", "close"], close=((1.6, -3.2, 0.9), (0.55, -0.5, 0.55), 110))
def build_academic_pin(M):
    gilt, en, silk = M["gold"], M["crimson_enamel"], M["crimson_silk"]
    piece("AcademicPin", "Torso")
    cx, cz, y0 = 0.55, 0.55, -0.5
    F = Matrix.Translation((cx, y0 - 0.012, cz)) @ Matrix.Scale(1.35, 4)   # the brooch's back sits on the shirt; its face looks to -Y
    o = oval(0.115, 0.09)
    A.extrude_poly("APBack", ccw(o), 0.018, gilt, F, bevel=0.004, segments=1)
    A.extrude_poly("APRim", ccw(o), 0.026, gilt, F @ Matrix.Translation((0, -0.004, 0)), bevel=0.003, segments=1,
                   holes=[ccw([(x * 0.84, z * 0.82) for x, z in o])[::-1]])
    A.extrude_poly("APField", ccw([(x * 0.84, z * 0.82) for x, z in o]), 0.02, en, F @ Matrix.Translation((0, -0.004, 0)), bevel=0.0)
    for k in range(22):
        a = 2 * math.pi * k / 22
        A.sphere(f"APBead{k}", 0.0072, F @ Vector((0.104 * math.cos(a), -0.02, 0.081 * math.sin(a))), gilt, seg=6, rings=4)
    # the open book: two ivory enamel pages in gilt frames, a gilt spine, ruled lines in gilt
    ivory = M["porcelain"]
    for sd in (-1, 1):
        page = [(sd * 0.005, -0.026), (sd * 0.032, -0.031), (sd * 0.058, -0.027), (sd * 0.058, 0.022), (sd * 0.032, 0.027), (sd * 0.005, 0.03)]
        if sd < 0:
            page = page[::-1]
        A.extrude_poly(f"APPageRim{sd}", ccw(page), 0.007, gilt, F @ Matrix.Translation((0, -0.02, -0.008)), bevel=0.0012, segments=1)
        inner = [(x * 0.86 + sd * 0.004, z * 0.82) for x, z in page]
        A.extrude_poly(f"APPage{sd}", ccw(inner), 0.004, ivory, F @ Matrix.Translation((0, -0.026, -0.008)), bevel=0.0006, segments=1)
        for k in range(4):
            z = -0.016 + k * 0.011
            A.extrude_poly(f"APRule{sd}{k}", ccw([(sd * 0.014, z - 0.0011), (sd * 0.05, z - 0.0011), (sd * 0.05, z + 0.0011), (sd * 0.014, z + 0.0011)][::(1 if sd > 0 else -1)]),
                           0.0016, gilt, F @ Matrix.Translation((0, -0.0302, -0.008)), bevel=0.0)
    B3.sweep("APSpine", [F @ Vector((0, -0.028, -0.036)), F @ Vector((0, -0.028, 0.024))], 0.0032, gilt, nr=6)
    # the quill across it: a shaft and a feathered vane
    P = [F @ Vector((-0.072 + 0.15 * t, -0.036, -0.056 + 0.104 * t + 0.01 * math.sin(math.pi * t))) for t in (i / 12 for i in range(13))]
    B3.sweep("APQuill", P, 0.0024, gilt, nr=6)
    G = []
    for u in (-1, 0, 1):
        row = []
        for t in (i / 10 for i in range(11)):
            tt = 0.38 + 0.62 * t
            c = F @ Vector((-0.072 + 0.15 * tt, -0.037, -0.056 + 0.104 * tt + 0.01 * math.sin(math.pi * tt)))
            w = 0.013 * math.sin(math.pi * min(1.0, t * 1.15)) * (1 - 0.3 * t)
            row.append(c + F.to_3x3() @ Vector((-0.6 * w * u, 0, 0.8 * w * u)))
        G.append(row)
    A.surface("APVane", G, 0.003, gilt)
    # two ribbon tails hanging below
    for s in (-1, 1):
        G = [[F @ Vector((s * (0.012 + 0.03 * u) + s * 0.012 * t, -0.006, -0.09 - 0.11 * t)) for u in (0, 0.5, 1)] for t in (i / 6 for i in range(7))]
        A.surface(f"APTail{s}", G, 0.004, silk)
    return dict(notes="the Honor Student's lapel pin on the left breast: a gilt oval with a beaded rim, a crimson enamel "
                      "field, an open book with a quill in gilt relief, two crimson silk tails")


# ================================================================== the knuckle wraps
def _hand_loop(cx, z, o, n=40, r=0.07):
    """a rounded rectangle round the arm part (x cx-0.5..cx+0.5, y -0.5..0.5) at height z, pushed out by o; returns
    (points, outward normals)"""
    pts, nrm = [], []
    corners = [(cx + 0.5 - r, 0.5 - r, 0), (cx - 0.5 + r, 0.5 - r, 90), (cx - 0.5 + r, -0.5 + r, 180), (cx + 0.5 - r, -0.5 + r, 270)]
    per = n // 4
    for (ax, ay, a0) in corners:
        for k in range(per):
            a = math.radians(a0 + 90 * k / per)
            d = Vector((math.cos(a), math.sin(a), 0))
            pts.append(Vector((ax, ay, z)) + d * (r + o))
            nrm.append(d)
    pts.append(pts[0].copy())
    nrm.append(nrm[0].copy())
    return pts, nrm


def _band(name, cx, z0, z1, o, mat, thick=0.012, tilt=0.0, bulge=0.006, seed=0):
    """one turn of tape: a band from z0 to z1 round the hand, its middle bulged out (soft cloth, not a plate), tilted so
    it climbs across the back of the hand, the edges a touch wavy"""
    pts, nrm = _hand_loop(cx, 0.0, o)
    rows = []
    for u in (0.0, 0.25, 0.5, 0.75, 1.0):
        row = []
        for j, (p, nv) in enumerate(zip(pts, nrm)):
            ph = j / (len(pts) - 1) * 2 * math.pi
            z = z0 + (z1 - z0) * u + tilt * math.sin(ph) + 0.004 * math.sin(ph * 7 + seed) * (1 if u in (0.0, 1.0) else 0)
            push = bulge * math.sin(math.pi * u)
            row.append(Vector((p.x, p.y, z)) + nv * push)
        rows.append(row)
    A.surface(name, rows, thick, mat)


def _wrap(name, mount, cx, side, linen, stain, leather, brass):
    piece(name, mount)
    # turns from the knuckles up past the wrist: each overlaps the one below and sits a hair further out, so the tape
    # reads as wound on, layer over layer
    turns = 8
    for k in range(turns):
        z0 = -0.985 + k * 0.05
        _band(f"{name}Turn{k}", cx, z0, z0 + 0.078, 0.006 + 0.0028 * k, stain if k < 2 else linen,
              tilt=0.012 * (1 if k % 2 else -1), seed=k * 1.7)
    # the figure-eight: two strips crossing over the back of the hand (the -Y face) and over the palm
    for face_y, fs in ((-0.5, -1), (0.5, 1)):
        for d in (-1, 1):
            G = []
            for u in (0.0, 0.5, 1.0):
                row = []
                for t in (i / 10 for i in range(11)):
                    x = cx + d * (-0.42 + 0.84 * t)
                    z = -0.95 + 0.30 * t + 0.035 * (u - 0.5) * 2
                    row.append(Vector((x, face_y + fs * (0.034 + 0.006 * math.sin(math.pi * t)), z)))
                G.append(row)
            A.surface(f"{name}X{face_y > 0 and 'P' or 'B'}{d}", G, 0.011, stain if face_y < 0 else linen)
    # the leather wrist band and its stud
    _band(f"{name}Band", cx, -0.6, -0.52, 0.052, leather, thick=0.016, bulge=0.004)
    A.sphere(f"{name}Stud", 0.017, (cx + side * 0.56, 0.0, -0.56), brass, scale=(0.6, 1, 1), seg=12, rings=8)
    # the frayed loose end hanging from the inner wrist
    P = [Vector((cx - side * (0.5 + 0.045), -0.18 + 0.05 * t, -0.62 - 0.2 * t + 0.02 * math.sin(t * 6))) for t in (i / 8 for i in range(9))]
    G = [[Vector((p.x, p.y + dy, p.z)) for p in P] for dy in (-0.03, 0.0, 0.03)]
    A.surface(f"{name}Tail", G, 0.008, linen)
    for k in range(5):   # frayed threads at its end
        e = P[-1] + Vector((0, -0.024 + 0.012 * k, 0))
        B3.sweep(f"{name}Fray{k}", [e, e + Vector((side * 0.004 * (k % 2), 0.002 * k, -0.03 - 0.012 * (k % 3)))], 0.0026, linen, nr=4)


@item("KnuckleWraps", "Scarred knuckle wraps", views=["front34", "front", "side", "close"], close=((3.2, -3.6, -0.6), (1.5, 0, -0.75), 100))
def build_knuckle_wraps(M):
    linen = A.mat_cloth("WrapLinen", (0.60, 0.56, 0.48), weave=520, rough=0.93, sheen=0.12, bump=0.16, twill=False, vary=0.14, wear=0.35, dirt=0.9)
    stain = A.mat_cloth("WrapStained", (0.30, 0.27, 0.23), weave=520, rough=0.95, sheen=0.1, bump=0.18, twill=False, vary=0.18, wear=0.5, dirt=1.0)
    _wrap("WrapL", "LeftArm", 1.5, 1, linen, stain, M["leather_black"], M["brass"])
    _wrap("WrapR", "RightArm", -1.5, -1, linen, stain, M["leather_black"], M["brass"])
    return dict(notes="the Notorious fighter's hand wraps: worn linen tape wound over the knuckles and wrist, ink-dark scuffs "
                      "on the knuckle turns, a black leather wrist band with a brass stud, a frayed loose end at each wrist")


# ================================================================== the silver sigil
@item("SilverSigil", "Silver sigil", views=["front34", "front", "close"], close=((1.2, -3.4, 0.7), (0, -0.5, 0.35), 100))
def build_silver_sigil(M):
    silver, black = M["silver"], M["black_enamel"]
    piece("SilverSigil", "Torso")
    # the chain: behind the neck on the torso's top, forward over the collar edge, down the chest in a V to the bail
    R = 1.33                                   # the pendant 1.33x the first cut
    PZ = 0.40                                  # the pendant's centre height on the chest
    bail_z = PZ + 0.12 * R + 0.02
    half = []
    for k in range(13):                        # back half round the neck (the character's left side), top face
        a = math.pi / 2 * (k / 12)
        half.append(Vector((0.34 * math.sin(a), 0.06 + 0.22 * math.cos(a), 1.006)))
    for t in (i / 6 for i in range(1, 7)):     # forward across the top face to the front edge
        half.append(Vector((0.34 - 0.04 * t, 0.06 - 0.565 * t, 1.006)))
    half.append(Vector((0.29, -0.512, 0.985)))  # over the edge
    for t in (i / 10 for i in range(1, 11)):   # down the chest to the bail, curving in
        half.append(Vector((0.29 * (1 - t) ** 1.25 + 0.006, -0.508, 0.97 - (0.97 - bail_z - 0.01) * t)))
    full = [Vector((-p.x, p.y, p.z)) for p in reversed(half)] + half[1:]
    full = B3.resample(full, 0.018)
    B3.sweep("SSChain", full, 0.0075, silver, nr=6)
    for i, p in enumerate(full[::2]):          # links: small flattened beads along it
        A.sphere(f"SSLink{i}", 0.0115, p, silver, scale=(1, 0.7, 0.7), seg=6, rings=4)
    # the pendant
    F = Matrix.Translation((0, -0.525, PZ)) @ Matrix.Scale(R, 4)
    A.sphere("SSBail", 0.022 * R, (0, -0.52, bail_z - 0.01), silver, scale=(0.7, 0.5, 1.2), seg=10, rings=6)
    d = oval(0.12, 0.12)
    A.extrude_poly("SSDisc", ccw(d), 0.022, silver, F, bevel=0.005, segments=1)
    A.extrude_poly("SSField", ccw([(x * 0.84, z * 0.84) for x, z in d]), 0.026, black, F @ Matrix.Translation((0, -0.002, 0)), bevel=0.0)
    for k in range(24):
        a = 2 * math.pi * k / 24
        A.sphere(f"SSBead{k}", 0.0078, F @ Vector((0.11 * math.cos(a), -0.016, 0.11 * math.sin(a))), silver, seg=6, rings=4)
    # a crescent moon and a seven-point star in relief
    moon = [(0.07 * math.cos(a), 0.07 * math.sin(a)) for a in (math.radians(60 + 240 * k / 24) for k in range(25))]
    moon += [(0.03 + 0.055 * math.cos(a), 0.01 + 0.055 * math.sin(a)) for a in (math.radians(300 - 240 * k / 24) for k in range(25))]
    A.extrude_poly("SSMoon", ccw(moon), 0.01, silver, F @ Matrix.Translation((-0.012, -0.018, 0)), bevel=0.002, segments=1)
    star = []
    for k in range(14):
        r = 0.036 if k % 2 == 0 else 0.015
        a = math.pi / 2 + 2 * math.pi * k / 14
        star.append((0.045 + r * math.cos(a), -0.035 + r * math.sin(a)))
    A.extrude_poly("SSStar", ccw(star), 0.01, silver, F @ Matrix.Translation((0, -0.018, 0)), bevel=0.0015, segments=1)
    piece("SilverSigilStone", "Torso", kind="Glow", glow=MOON)
    A.sphere("SSStone", 0.016, F @ Vector((0.045, -0.026, -0.035)), M["porcelain"], scale=(1, 0.6, 1), seg=10, rings=6)
    return dict(notes="the Keeper of Secrets' silver pendant on a fine chain: a beaded silver disc, a black enamel field, a "
                      "crescent moon and a seven-point star in relief, a moonstone with a faint cold glow")
