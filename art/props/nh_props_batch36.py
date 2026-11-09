"""Props batch 36, the School prop kit (2026-11-08) for nh_props.py: classrooms, the laboratory, the music room and the
gymnasium of the Institution. The house look: cast iron, black marble, crimson enamel (#600E1A), brass and gilt, dark oak and
ebonised wood, bone, ink, wax, paper and slate. Every name and word on the props is invented.

  Abacus            a classroom abacus: a dark oak frame on splayed feet, ten steel rods of crimson and bone beads
  AnatomySkeleton   a life-size teaching skeleton (clean bone, nothing gory) hung from an iron stand on a cross base
  LabBench          a laboratory bench: dark oak cupboards and drawers, a slate top (3.0), a brass gas line with three taps,
                    an iron-framed reagent shelf with labelled, stoppered bottles
  TestTubeRack      an oak rack of six test tubes (Glass) with coloured liquids, a brass Bunsen burner and its hose beside it
  SpecimenJars      a short ebonised wall shelf of five glass jars (Glass) with labels: a frog, a sea-horse, beetles, a
                    mandrake root and a small octopus
  Microscope        a brass microscope on a black horseshoe foot: body tube, eyepiece, two objectives, stage clips, mirror
  WallMap           a pull-down roller map on an oak wall batten: an invented country (The Nocturne Reaches), a pull ring
  WritingSlate      a student's slate in an oak frame, chalked with sums, a stick of chalk and a slate pencil
  InkwellSet        a blotter pad, an ebonised standish with two inkwells (one lid open) and two dip pens, a rocker blotter
  Satchel           an oxblood leather school satchel: front flap, two straps with brass buckles, a handle, a shoulder strap
  DunceStool        a tall oak stool (seat 2.6) with a paper dunce cap on it
  UprightPiano      an ebonised upright piano: pointed fretwork panels over crimson silk, keys, sheet music on the desk, two
                    brass candle sconces, brass pedals
  MusicStand        an iron music stand: scrolled tripod, a lyre-shaped desk holding sheet music
  Metronome         a pyramid metronome: ebonised case, a printed tempo scale, a brass pendulum and weight, a winding key
  Radiator          a cast-iron column radiator, fourteen sections with quatrefoil heads, a brass valve wheel and bleed key
  FireBucketRack    a dark oak wall rack of four crimson fire buckets lettered FIRE, on iron hooks, sand in them
  DrinkingFountain  a wall drinking fountain: a pointed black marble back, a marble basin (rim 2.8) on an iron corbel, a brass
                    bubbler and push button, the drain pipe down to the floor
  VaultingHorse     a gymnasium vaulting horse: a buttoned leather body (top 4.0) on four splayed adjustable oak legs

Printed faces from art/props/staff_atlas.py (StaffPrint), shared with batch 35 (whose helpers this module uses). Front faces -Y,
Z is up, the origin is at the bottom centre; wall pieces have their back face on y = 0. Registered into nh_props.BUILD on import.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, material, _finish, _gable
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _solid
from nh_props_batch9 import foil
from nh_props_batch10 import lacquer
from nh_props_batch24 import _fine, rbox
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import nh_props_batch34_dorm as DM
import nh_props_batch35 as B35
from nh_props_batch35 import wrap_lathe, knob, keyhole, brass_bail
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FACE_UP = RX(-math.pi / 2)       # turns a B30.plate (built facing -Y) to face up, the print's top toward +Y


def kit(M):
    K = B35.kit(M)
    K.update({
        "bone": material("SkelBone", "NH_Limestone", tint=(0.86, 0.79, 0.64), scale=1.4, rough_add=0.08, wear=0.15, dirt=0.95),
        "socket": flat("BoneShadow", (0.012, 0.009, 0.007), 0.9),
        "satchel": B24.leather("SatchelLeather", (0.11, 0.028, 0.018), scale=4.0, wear=0.3),
        "gymleather": B24.leather("GymLeather", (0.15, 0.06, 0.03), scale=3.0, wear=0.3),
        "sand": material("Sand", "NH_Limestone", tint=(0.5, 0.4, 0.26), scale=3.0, rough_add=0.3, wear=0.0, dirt=0.6),
        "lacquer": lacquer(),
        "ivory": flat("KeyIvory", (0.7, 0.66, 0.56), 0.3, dirt=0.4),
        "amber": M["glassamber"],
        "rubber": flat("Rubber", (0.12, 0.04, 0.025), 0.75),
        "liq_c": flat("LiquidCrimson", (0.3, 0.01, 0.025), 0.05),
        "liq_g": flat("LiquidGreen", (0.04, 0.2, 0.06), 0.05),
        "liq_a": flat("LiquidAmber", (0.45, 0.22, 0.03), 0.05),
        "liq_v": flat("LiquidViolet", (0.12, 0.03, 0.22), 0.05),
        "liq_b": flat("LiquidBlue", (0.05, 0.12, 0.3), 0.05),
        "frog": material("PreservedFrog", "NH_Leather", tint=(0.32, 0.36, 0.22), scale=3.0, normal=0.4, wear=0.0, dirt=0.7),
        "pale": material("PreservedPale", "NH_Leather", tint=(0.62, 0.48, 0.42), scale=3.0, normal=0.4, wear=0.0, dirt=0.7),
        "horse": flat("SeaHorse", (0.45, 0.28, 0.1), 0.5),
        "root": material("MandrakeRoot", "NH_DeskWood", tint=(0.36, 0.25, 0.15), scale=1.5, wear=0.1, dirt=0.8),
        "beetle": material("Beetle", base=(0.015, 0.03, 0.025), rough=0.12, metal=0.4, wear=0.0, dirt=0.3),
        "cork": material("Cork", "NH_Limestone", tint=(0.36, 0.22, 0.11), scale=2.5, normal=1.2, rough_add=0.2, wear=0.0, dirt=0.8),
        "silk": flat("CrimsonSilk", (0.1, 0.008, 0.015), 0.55, dirt=0.6),
        "mirror": material("Mirror", base=(0.8, 0.8, 0.82), rough=0.05, metal=1.0, wear=0.0, dirt=0.3),
    })
    return K


def curved_label(name, key, r, zc, h, width, mat, n=8):
    """A paper label wrapped on a jar of radius r round its front (-Y), `width` studs across, centred at height zc."""
    a = width / r
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    rows = []
    for j in range(2):
        z = zc - h / 2 + j * h
        rows.append([bm.verts.new((math.cos(-math.pi / 2 - a / 2 + a * i / n) * r, math.sin(-math.pi / 2 - a / 2 + a * i / n) * r, z)) for i in range(n + 1)])
    for i in range(n):
        f = bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        f.smooth = True
        f[kl] = 2.5
        for lp, (ii, jj) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            lp[uvl].uv = DM.region_uv(key, ii / n, jj)
    ob = DM.mesh_obj(name, bm, mat)
    _solid(ob, 0.004)
    return ob


# ================================================================== classroom

def abacus(M):
    K = kit(M)
    oak = K["oak"]
    W, H = 1.8, 1.7
    zb, zt = 0.2, H - 0.08
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.06)
        box(f"Post{sx}", (0.12, 0.14, zt - zb + 0.1), (x, 0, (zb + zt) / 2), oak, bevel=0.025)
        box(f"Foot{sx}", (0.16, 0.7, 0.1), (x, 0, 0.05), K["oakdk"], bevel=0.03)
        sphere(f"Finial{sx}", 0.07, (x, 0, zt + 0.1), K["brassf"], seg=12, rings=6)
        for sy in (-1, 1):
            tube(f"Brace{sx}{sy}", [(x, sy * 0.3, 0.1), (x, sy * 0.05, 0.45)], 0.025, K["iron"], square=True, poly=True)
    box("Top", (W, 0.14, 0.1), (0, 0, zt), oak, bevel=0.025)
    box("Bottom", (W, 0.14, 0.1), (0, 0, zb), oak, bevel=0.025)
    rnd = random.Random(3601)
    x0, x1 = -W / 2 + 0.12, W / 2 - 0.12
    br = 0.052
    for r in range(10):
        z = zb + 0.12 + r * (zt - zb - 0.24) / 9
        cyl(f"Rod{r}", 0.012, x1 - x0, (0, 0, z), K["steel"], rot=(0, math.pi / 2, 0), verts=6, bevel=0.0)
        left = rnd.randint(0, 10)
        for k in range(10):
            mat = K["enamel"] if k < 5 else K["bone"]
            x = x0 + br * 0.65 + k * br * 1.3 if k < left else x1 - br * 0.65 - (9 - k) * br * 1.3
            sphere(f"Bead{r}{k}", br, (x, 0, z), mat, seg=10, rings=6, scale=(0.62, 1, 1))
    _fine(0.6)
    return _dims()


def _bone_seg(name, a, b, r, mat, knob_r=None):
    """A long bone: a shaft between two knobbly ends."""
    a, b = Vector(a), Vector(b)
    m = (a + b) / 2
    tube(name, [tuple(a), tuple(a + (m - a) * 0.5), tuple(m), tuple(b + (m - b) * 0.5), tuple(b)], r, mat, poly=True)
    kr = knob_r or r * 1.9
    for k, p in enumerate((a, b)):
        sphere(f"{name}End{k}", kr, tuple(p), mat, seg=12, rings=6, scale=(1.15, 0.9, 1.0))


def anatomy_skeleton(M):
    K = kit(M)
    bn, ir = K["bone"], K["iron"]
    z0 = 0.32      # the soles of the feet
    # the stand: an iron cross base on ball feet, a post up behind the spine, an arm over to the skull
    for a in (45, 135):
        box(f"BaseArm{a}", (1.7, 0.12, 0.08), (0, 0.15, 0.1), ir, bevel=0.02, rot=(0, 0, a * DEG))
    for k in range(4):
        a = (45 + 90 * k) * DEG
        sphere(f"BaseBall{k}", 0.07, (math.cos(a) * 0.82, 0.15 + math.sin(a) * 0.82, 0.07), K["brassf"], seg=12, rings=6)
    cyl("BaseHub", 0.16, 0.14, (0, 0.15, 0.13), ir, verts=20, bevel=0.02)
    tube("Post", [(0, 0.15, 0.15), (0, 0.55, 0.6), (0, 0.55, 5.1), (0, 0.45, 5.55), (0, 0.15, 5.65), (0, 0.02, 5.55)], 0.04, ir)
    cyl("PostCollar", 0.06, 0.12, (0, 0.55, 2.6), K["brassf"], verts=14, bevel=0.01)
    tube("HipRod", [(0, 0.55, z0 + 2.45), (0, 0.17, z0 + 2.45)], 0.022, ir, poly=True)
    tube("SkullHook", [(0, 0.02, 5.55), (0, 0.0, 5.42)], 0.012, K["brassf"], poly=True)
    hoop("SkullEye", (0, 0.0, 5.39), 0.03, "X", K["brassf"], thick=0.008)
    # the skull
    zs = z0 + 4.7
    sphere("Cranium", 0.3, (0, 0.03, zs + 0.05), bn, seg=20, rings=12, scale=(0.86, 1.08, 0.98))
    sphere("Face", 0.21, (0, -0.15, zs - 0.12), bn, seg=16, rings=10, scale=(1.0, 0.75, 1.0))
    for sx in (-1, 1):
        sphere(f"Cheek{sx}", 0.07, (sx * 0.17, -0.17, zs - 0.13), bn, seg=10, rings=6, scale=(1.2, 1, 0.8))
        sphere(f"Orbit{sx}", 0.07, (sx * 0.095, -0.3, zs - 0.045), K["socket"], seg=12, rings=6, scale=(1.0, 0.45, 0.9))
        tube(f"Brow{sx}", [(sx * 0.03, -0.29, zs + 0.025), (sx * 0.1, -0.295, zs + 0.035), (sx * 0.17, -0.265, zs + 0.015)], 0.014, bn)
        sphere(f"Ear{sx}", 0.04, (sx * 0.24, 0.02, zs - 0.08), bn, seg=8, rings=5)
    sphere("Nose", 0.04, (0, -0.315, zs - 0.15), K["socket"], seg=10, rings=5, scale=(0.75, 0.6, 1.2))
    jaw = [(-0.19, -0.02, zs - 0.12), (-0.17, -0.1, zs - 0.3), (-0.09, -0.24, zs - 0.36), (0, -0.28, zs - 0.37), (0.09, -0.24, zs - 0.36),
           (0.17, -0.1, zs - 0.3), (0.19, -0.02, zs - 0.12)]
    tube("Jaw", jaw, 0.04, bn)
    for row, (zz, rr) in enumerate(((zs - 0.235, 0.155), (zs - 0.29, 0.14))):
        for k in range(10):
            a = -math.pi / 2 + (k - 4.5) * 0.17
            box(f"Tooth{row}{k}", (0.03, 0.026, 0.05), (math.cos(a) * rr * 0.95, -0.08 + math.sin(a) * rr * 1.2, zz), bn, bevel=0.0,
                rot=(0, 0, a + math.pi / 2))

    # the spine: neck and back, a gentle S-curve, a spinous process behind each vertebra
    def spine_y(z):
        return 0.1 + 0.05 * math.sin((z - z0 - 2.6) / 1.7 * math.pi)
    zn = [zs - 0.4 - k * 0.075 for k in range(6)]
    zv = [z0 + 3.98 - k * 0.1 for k in range(14)]
    for k, z in enumerate(zn + zv):
        r = 0.05 if k < 6 else 0.06 + 0.025 * (k - 6) / 13
        cyl(f"Vert{k}", r, 0.06, (0, spine_y(z), z), bn, verts=10, bevel=0.0)
        box(f"Spinous{k}", (0.03, 0.1, 0.035), (0, spine_y(z) + r + 0.03, z - 0.02), bn, bevel=0.0, rot=(-0.4, 0, 0))
        if k >= 6:
            box(f"Trans{k}", (r * 3.2, 0.03, 0.03), (0, spine_y(z) + 0.02, z), bn, bevel=0.0)
    # the ribs: ten pairs round from the spine to the sternum (the last three float)
    zr0 = z0 + 3.95
    for i in range(10):
        zb = zr0 - i * 0.11
        a = 0.2 + 0.15 * math.sin(min(1.0, (i + 1) / 5.0) * math.pi / 2) - 0.02 * max(0, i - 6)
        b = 0.26
        drop = 0.16 + 0.03 * i
        th_end = math.pi - 0.18 if i < 7 else math.pi * (0.75 - 0.05 * (i - 7))
        for sx in (-1, 1):
            pts = []
            for j in range(9):
                th = 0.15 + (th_end - 0.15) * j / 8
                pts.append((sx * a * math.sin(th) * (1.0 + 0.08 * math.sin(th * 2)), -0.15 + b * math.cos(th), zb - drop * (j / 8) ** 1.4 + 0.04 * math.sin(th)))
            pts[0] = (sx * 0.06, spine_y(zb) + 0.02, zb)
            tube(f"Rib{i}{sx}", pts, 0.019, bn, res=2)
    box("Sternum", (0.09, 0.035, 0.6), (0, -0.4, z0 + 3.6), bn, bevel=0.015, rot=(-0.12, 0, 0))
    box("Manubrium", (0.16, 0.04, 0.14), (0, -0.37, z0 + 3.95), bn, bevel=0.02)
    for sx in (-1, 1):
        tube(f"Clavicle{sx}", [(sx * 0.06, -0.37, z0 + 3.99), (sx * 0.22, -0.3, z0 + 4.03), (sx * 0.38, -0.12, z0 + 4.02), (sx * 0.44, 0.0, z0 + 4.04)],
             0.024, bn)
        B20.tprism(f"Scapula{sx}", [(sx * 0.18, z0 + 3.98), (sx * 0.42, z0 + 3.98), (sx * 0.24, z0 + 3.45)], 0.22, 0.03, bn, plane="XZ")
    # the pelvis: a bowl of two wings, the sacrum, hip sockets
    zp = z0 + 2.3
    lathe("Pelvis", [(0.16, 0.0), (0.22, 0.02), (0.3, 0.12), (0.37, 0.27), (0.38, 0.34), (0.33, 0.34), (0.27, 0.22), (0.2, 0.1), (0.14, 0.03)], bn, seg=24,
          loc=(0, 0.02, zp), scale=(1.0, 0.62))
    pel = P.PARTS[-1]
    bm = bmesh.new()
    bm.from_mesh(pel.data)
    # open the bowl at the front, so it reads as two hip wings round the sacrum rather than a dish
    cut = [f for f in bm.faces if f.calc_center_median().y < -0.1 and f.calc_center_median().z > zp + 0.1]
    bmesh.ops.delete(bm, geom=cut, context="FACES")
    bm.to_mesh(pel.data)
    bm.free()
    box("Sacrum", (0.16, 0.06, 0.3), (0, 0.18, zp + 0.12), bn, bevel=0.03, rot=(0.35, 0, 0))
    for sx in (-1, 1):
        sphere(f"HipSocket{sx}", 0.08, (sx * 0.24, -0.02, zp + 0.02), bn, seg=12, rings=6)
        hoop(f"Obturator{sx}", (sx * 0.12, -0.13, zp - 0.05), 0.07, "Y", bn, thick=0.02)
    # arms, hanging, palms in
    for sx in (-1, 1):
        sh = (sx * 0.46, 0.02, z0 + 3.98)
        el = (sx * 0.53, 0.06, z0 + 3.12)
        wr = (sx * 0.56, -0.02, z0 + 2.36)
        _bone_seg(f"Humerus{sx}", sh, el, 0.034, bn, knob_r=0.062)
        _bone_seg(f"Radius{sx}", (el[0] - sx * 0.02, el[1] - 0.03, el[2] - 0.03), (wr[0], wr[1] - 0.03, wr[2]), 0.022, bn, knob_r=0.035)
        _bone_seg(f"Ulna{sx}", (el[0] + sx * 0.02, el[1] + 0.03, el[2] - 0.02), (wr[0] + sx * 0.02, wr[1] + 0.02, wr[2]), 0.02, bn, knob_r=0.033)
        sphere(f"Carpals{sx}", 0.06, (wr[0], wr[1], wr[2] - 0.07), bn, seg=10, rings=6, scale=(0.6, 1.2, 1))
        for f in range(5):
            y = wr[1] - 0.08 + f * 0.04
            L = [0.14, 0.2, 0.22, 0.2, 0.16][f]
            if f == 0:
                tube(f"Thumb{sx}", [(wr[0], wr[1] - 0.06, wr[2] - 0.08), (wr[0] - sx * 0.02, wr[1] - 0.14, wr[2] - 0.16), (wr[0] - sx * 0.03, wr[1] - 0.17, wr[2] - 0.24)],
                     0.012, bn)
                continue
            tube(f"Finger{sx}{f}", [(wr[0], y, wr[2] - 0.1), (wr[0] + sx * 0.005, y - 0.005, wr[2] - 0.1 - L * 0.55), (wr[0] - sx * 0.01, y - 0.02, wr[2] - 0.1 - L)],
                 0.011, bn)
    # legs
    for sx in (-1, 1):
        hip = (sx * 0.24, -0.02, zp + 0.02)
        kn = (sx * 0.18, -0.04, z0 + 1.3)
        an = (sx * 0.17, 0.02, z0 + 0.14)
        tube(f"FemurNeck{sx}", [hip, (sx * 0.3, -0.02, zp - 0.06)], 0.03, bn, poly=True)
        _bone_seg(f"Femur{sx}", (sx * 0.3, -0.02, zp - 0.06), kn, 0.042, bn, knob_r=0.075)
        sphere(f"Patella{sx}", 0.045, (kn[0], kn[1] - 0.08, kn[2]), bn, seg=10, rings=6, scale=(1, 0.6, 1.2))
        _bone_seg(f"Tibia{sx}", (kn[0], kn[1], kn[2] - 0.06), an, 0.036, bn, knob_r=0.06)
        _bone_seg(f"Fibula{sx}", (kn[0] + sx * 0.06, kn[1] + 0.04, kn[2] - 0.1), (an[0] + sx * 0.06, an[1] + 0.03, an[2] + 0.02), 0.016, bn, knob_r=0.026)
        sphere(f"Heel{sx}", 0.065, (an[0], an[1] + 0.05, z0 + 0.06), bn, seg=10, rings=6, scale=(0.9, 1.3, 0.9))
        sphere(f"Tarsals{sx}", 0.07, (an[0], an[1] - 0.1, z0 + 0.07), bn, seg=10, rings=6, scale=(1.2, 1.3, 0.7))
        for t in range(5):
            x = an[0] + sx * (-0.06 + t * 0.03)
            L = [0.26, 0.24, 0.22, 0.2, 0.18][t]
            tube(f"Toe{sx}{t}", [(x, an[1] - 0.15, z0 + 0.06), (x + sx * 0.005, an[1] - 0.15 - L * 0.6, z0 + 0.03), (x, an[1] - 0.15 - L, z0 + 0.02)],
                 0.013 if t else 0.018, bn)
    return _dims()


def lab_bench(M):
    K = kit(M)
    W, D, H = 6.0, 2.6, 3.0
    zk = 0.3
    oak = K["oak"]
    box("Kick", (W - 0.16, D - 0.3, zk), (0, 0.08, zk / 2), K["ebony"], bevel=0.015)
    yf = -D / 2 + 0.1
    box("Carcass", (W - 0.06, D - 0.12, H - 0.16 - zk), (0, 0.06, zk + (H - 0.16 - zk) / 2), K["oakdk"], bevel=0.02)
    box("Top", (W + 0.14, D + 0.08, 0.16), (0, 0, H - 0.08), K["slate"], bevel=0.035, segments=3)
    box("TopEdge", (W + 0.1, 0.03, 0.05), (0, -D / 2 - 0.03, H - 0.12), K["iron"], bevel=0.008)
    bw = (W - 0.2) / 4
    for i in range(5):
        x = -W / 2 + 0.05 + i * (W - 0.1) / 4
        box(f"Stile{i}", (0.12, 0.06, H - 0.16 - zk), (x, yf - 0.03, zk + (H - 0.16 - zk) / 2), K["ebony"], bevel=0.012)
    y = yf - 0.06
    for i in range(4):
        cx = -W / 2 + 0.1 + bw * (i + 0.5)
        zd = H - 0.45
        box(f"Drawer{i}", (bw - 0.16, 0.07, 0.42), (cx, y - 0.035, zd), oak, bevel=0.02)
        box(f"DrawerPanel{i}", (bw - 0.44, 0.02, 0.2), (cx, y - 0.075, zd), K["oakdk"], bevel=0.008)
        brass_bail(f"Pull{i}", cx, y - 0.085, zd + 0.03, 0.34, K["brassf"])
        z0d, z1d = zk + 0.12, zd - 0.28
        box(f"Door{i}", (bw - 0.16, 0.07, z1d - z0d), (cx, y - 0.035, (z0d + z1d) / 2), oak, bevel=0.02)
        box(f"DoorPanel{i}", (bw - 0.46, 0.04, z1d - z0d - 0.4), (cx, y - 0.08, (z0d + z1d) / 2), K["oakdk"], bevel=0.03, segments=3)
        kx = cx + (bw / 2 - 0.22) * (1 if i % 2 == 0 else -1)
        knob(f"Knob{i}", kx, y - 0.07, (z0d + z1d) / 2 + 0.2, K["brassf"], r=0.04)
        keyhole(f"Key{i}", kx, y - 0.07, (z0d + z1d) / 2, K)
    # the gas taps: three brass pillars on the slate, each with two swan-neck nozzles and lever valves, fed by a brass gas line
    # along the back edge
    yg = D / 2 - 0.3
    cyl("GasPipe", 0.045, W - 0.6, (0, yg + 0.12, H + 0.05), K["brassf"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.005)
    for k, x in enumerate((-1.9, 0.0, 1.9)):
        yt = yg - 0.15
        cyl(f"TapFlange{k}", 0.12, 0.04, (x, yt, H + 0.02), K["brassf"], verts=20, bevel=0.01)
        cyl(f"TapFeed{k}", 0.035, 0.27, (x, yt + 0.135, H + 0.05), K["brassf"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
        lathe(f"TapPillar{k}", [(0, 0), (0.07, 0), (0.06, 0.06), (0.05, 0.42), (0.065, 0.46), (0.06, 0.52), (0.03, 0.56), (0, 0.57)], K["brassf"], seg=16,
              loc=(x, yt, H + 0.03))
        for sx in (-1, 1):
            # a lever valve on the pillar's side, then the swan neck arching out and down toward the front
            z = H + 0.33
            sphere(f"Valve{k}{sx}", 0.055, (x + sx * 0.09, yt, z), K["brassf"], seg=12, rings=6)
            cyl(f"ValveStem{k}{sx}", 0.02, 0.12, (x + sx * 0.06, yt, z), K["brassf"], rot=(0, math.pi / 2, 0), verts=8, bevel=0.0)
            box(f"Lever{k}{sx}", (0.03, 0.3, 0.035), (x + sx * 0.09, yt - 0.1, z + 0.08), K["brassf"], bevel=0.01, rot=(0.5, 0, 0))
            sphere(f"LeverKnob{k}{sx}", 0.035, (x + sx * 0.09, yt - 0.23, z + 0.15), K["ebony"], seg=10, rings=5)
            tube(f"Neck{k}{sx}", [(x + sx * 0.09, yt, z), (x + sx * 0.2, yt - 0.04, z + 0.12), (x + sx * 0.28, yt - 0.18, z + 0.12),
                                  (x + sx * 0.3, yt - 0.3, z - 0.02)], 0.026, K["brassf"])
            s = _mark()
            lathe(f"Nozzle{k}{sx}", [(0, 0), (0.032, 0), (0.03, 0.04), (0.038, 0.06), (0.022, 0.075), (0.03, 0.095), (0.018, 0.11), (0.024, 0.13), (0.012, 0.17),
                                     (0, 0.17)], K["brassf"], seg=10)
            _xform(s, T(x + sx * 0.3, yt - 0.3, z - 0.02) @ RX(math.pi + 0.35))
    # the reagent shelf on iron uprights, stoppered bottles on it
    zs = H + 1.15
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.5)
        tube(f"Upright{sx}", [(x, D / 2 - 0.15, H), (x, D / 2 - 0.15, zs + 0.3)], 0.035, K["iron"], square=True, poly=True)
        tube(f"Strut{sx}", [(x, D / 2 - 0.15, zs - 0.4), (x, D / 2 - 0.45, zs - 0.03)], 0.02, K["iron"], square=True, poly=True)
        sphere(f"UprightCap{sx}", 0.05, (x, D / 2 - 0.15, zs + 0.33), K["brassf"], seg=10, rings=5)
    box("Shelf", (W - 0.6, 0.5, 0.07), (0, D / 2 - 0.3, zs), oak, bevel=0.02)
    tube("ShelfRail", [(-(W / 2 - 0.5), D / 2 - 0.53, zs + 0.15), (W / 2 - 0.5, D / 2 - 0.53, zs + 0.15)], 0.012, K["brassf"], poly=True)
    rnd = random.Random(3603)
    for k in range(7):
        x = -2.2 + k * 0.72 + rnd.uniform(-0.1, 0.1)
        h = rnd.uniform(0.35, 0.55)
        r = rnd.uniform(0.09, 0.13)
        mat = K["amber"] if k % 3 != 1 else K["glass"]
        yb = D / 2 - 0.3
        lathe(f"Bottle{k}", [(0, 0), (r, 0), (r + 0.01, 0.02), (r + 0.01, h * 0.7), (r * 0.5, h * 0.85), (r * 0.42, h), (0, h)], mat, seg=14,
              loc=(x, yb, zs + 0.035))
        lathe(f"Stopper{k}", [(0, 0), (r * 0.38, 0), (r * 0.42, 0.03), (r * 0.6, 0.06), (r * 0.5, 0.1), (0, 0.1)], K["glass"], seg=12,
              loc=(x, yb, zs + 0.035 + h))
        s = _mark()
        curved_label(f"Label{k}", f"SP_Jar_{k % 6}", r + 0.013, 0.0, h * 0.3, r * 1.4, K["sp"])
        _xform(s, T(x, yb, zs + 0.035 + h * 0.38))
    return _dims()


def test_tube_rack(M):
    K = kit(M)
    oak = K["oak"]
    W = 1.3
    box("Base", (W, 0.42, 0.06), (0, 0, 0.03), oak, bevel=0.015)
    for sx in (-1, 1):
        box(f"End{sx}", (0.06, 0.4, 0.6), (sx * (W / 2 - 0.03), 0, 0.33), oak, bevel=0.015)
    box("Upper", (W - 0.06, 0.3, 0.05), (0, -0.02, 0.5), oak, bevel=0.012)
    box("Lower", (W - 0.06, 0.3, 0.04), (0, -0.02, 0.2), oak, bevel=0.01)
    box("PegRail", (W - 0.06, 0.08, 0.04), (0, 0.13, 0.6), oak, bevel=0.01)
    liqs = ["liq_c", "liq_a", "liq_g", None, "liq_v", "liq_b"]
    for k in range(6):
        x = -W / 2 + 0.17 + k * (W - 0.34) / 5
        hoop(f"Rim{k}", (x, -0.02, 0.525), 0.058, "Z", K["brassf"], thick=0.008)
        P.set_group("Glass")
        lathe(f"Tube{k}", [(0, 0.0), (0.03, 0.005), (0.048, 0.03), (0.05, 0.06), (0.05, 0.62), (0.056, 0.64), (0.044, 0.64), (0.044, 0.06), (0.03, 0.035),
                           (0, 0.03)], K["glass"], seg=16, loc=(x, -0.02, 0.17))
        P.set_group("Main")
        if liqs[k]:
            hgt = 0.18 + 0.06 * ((k * 7) % 5)
            lathe(f"Liquid{k}", [(0, 0.035), (0.03, 0.04), (0.042, 0.065), (0.042, hgt), (0, hgt)], K[liqs[k]], seg=12, loc=(x, -0.02, 0.17))
    for k in range(4):
        cyl(f"Peg{k}", 0.012, 0.22, (-0.45 + k * 0.3, 0.13, 0.72), oak, verts=8, bevel=0.0)
    # the Bunsen burner and its hose
    bx = 1.15
    lathe("BunsenBase", [(0, 0), (0.2, 0), (0.21, 0.02), (0.19, 0.05), (0.08, 0.08), (0.06, 0.1), (0, 0.1)], K["iron"], seg=28, loc=(bx, -0.1, 0))
    lathe("BunsenBarrel", [(0, 0), (0.045, 0), (0.045, 0.55), (0.05, 0.56), (0.05, 0.58), (0.04, 0.58), (0.04, 0.1), (0, 0.1)], K["brassf"], seg=18,
          loc=(bx, -0.1, 0.09))
    cyl("Collar", 0.055, 0.08, (bx, -0.1, 0.22), K["brassf"], verts=18, bevel=0.008)
    cyl("AirHole", 0.022, 0.02, (bx, -0.155, 0.22), K["ink"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)
    cyl("Inlet", 0.022, 0.2, (bx + 0.1, -0.1, 0.07), K["brassf"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.004)
    tube("Hose", [(bx + 0.2, -0.1, 0.07), (bx + 0.35, -0.05, 0.04), (bx + 0.45, 0.15, 0.03), (bx + 0.3, 0.4, 0.03), (bx - 0.1, 0.45, 0.03)], 0.03, K["rubber"])
    _fine(0.5)
    return _dims()


def specimen_jars(M):
    K = kit(M)
    W, D = 3.4, 0.8
    zt = 0.6
    box("Shelf", (W, D, 0.1), (0, -D / 2, zt - 0.05), K["ebony"], bevel=0.025)
    box("ShelfEdge", (W + 0.04, 0.04, 0.04), (0, -D - 0.01, zt - 0.08), K["brassf"], bevel=0.008)
    box("BackRail", (W, 0.06, 0.24), (0, -0.03, zt + 0.12), K["ebony"], bevel=0.015)
    box("Fascia", (W - 0.2, 0.06, 0.2), (0, -D + 0.05, zt - 0.2), K["ebony"], bevel=0.012)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.5)
        tube(f"Bracket{sx}", [(x, -0.04, zt - 0.6), (x, -0.04, zt - 0.1), (x, -D + 0.15, zt - 0.1), (x, -0.04, zt - 0.6)], 0.022, K["iron"], square=True, poly=True)
        tube(f"BracketScroll{sx}", [(x, -0.15, zt - 0.2), (x, -0.32, zt - 0.18), (x, -0.34, zt - 0.34), (x, -0.24, zt - 0.36)], 0.014, K["iron"])
    rnd = random.Random(3605)
    jars = [(-1.3, 0.24, 0.62, "frog"), (-0.62, 0.2, 0.78, "horse"), (0.02, 0.27, 0.55, "beetle"), (0.68, 0.22, 0.85, "root"), (1.34, 0.26, 0.68, "octo")]
    yc = -D / 2 - 0.02
    for k, (x, r, h, what) in enumerate(jars):
        z = zt
        P.set_group("Glass")
        lathe(f"Jar{k}", [(0, 0), (r - 0.03, 0), (r, 0.03), (r, h - 0.08), (r - 0.04, h - 0.04), (r - 0.04, h), (r - 0.055, h), (r - 0.055, h - 0.04),
                          (r - 0.015, h - 0.08), (r - 0.015, 0.04), (0, 0.025)], K["glass"], seg=28, loc=(x, yc, z))
        P.set_group("Main")
        lathe(f"Lid{k}", [(0, h + 0.07), (r - 0.02, h + 0.07), (r - 0.02, h - 0.02), (r - 0.035, h - 0.02), (r - 0.035, h + 0.04), (0, h + 0.04)],
              K["brassf"] if k % 2 == 0 else K["cork"], seg=24, loc=(x, yc, z))
        sphere(f"LidKnob{k}", 0.04, (x, yc, z + h + 0.09), K["brassf"], seg=10, rings=5)
        s = _mark()
        curved_label(f"Label{k}", f"SP_Jar_{k}", r + 0.006, 0.0, 0.17, 0.27, K["sp"])
        _xform(s, T(x, yc, z + h * 0.32))
        cz = z + h * 0.55
        if what == "frog":
            sphere("FrogBody", 0.12, (x, yc, cz), K["frog"], seg=14, rings=8, scale=(0.75, 0.55, 1.0))
            sphere("FrogHead", 0.08, (x, yc - 0.04, cz + 0.13), K["frog"], seg=12, rings=6, scale=(1.1, 0.7, 0.8))
            for sx in (-1, 1):
                sphere(f"FrogEye{sx}", 0.025, (x + sx * 0.05, yc - 0.08, cz + 0.17), K["ink"], seg=8, rings=4)
                tube(f"FrogLeg{sx}", [(x + sx * 0.07, yc, cz - 0.06), (x + sx * 0.17, yc - 0.03, cz - 0.02), (x + sx * 0.13, yc - 0.04, cz - 0.16),
                                      (x + sx * 0.18, yc - 0.06, cz - 0.24)], 0.022, K["frog"])
                tube(f"FrogArm{sx}", [(x + sx * 0.06, yc - 0.03, cz + 0.05), (x + sx * 0.13, yc - 0.06, cz + 0.02), (x + sx * 0.14, yc - 0.07, cz - 0.04)],
                     0.015, K["frog"])
        elif what == "horse":
            pts = [(0.0, 0.22), (0.04, 0.18), (0.05, 0.1), (0.03, 0.0), (0.0, -0.08), (-0.02, -0.16), (0.01, -0.22), (0.05, -0.24), (0.06, -0.2)]
            for i, (px, pz) in enumerate(pts):
                sphere(f"Horse{i}", 0.05 * (1.0 - 0.09 * i) + 0.01, (x + px, yc, cz + pz), K["horse"], seg=10, rings=6, scale=(1, 0.7, 1.15))
            tube("HorseSnout", [(x, yc, cz + 0.22), (x - 0.08, yc - 0.01, cz + 0.2), (x - 0.13, yc - 0.01, cz + 0.19)], 0.016, K["horse"])
            box("HorseFin", (0.004, 0.06, 0.08), (x + 0.06, yc, cz + 0.08), K["horse"], bevel=0.0)
        elif what == "beetle":
            for i in range(7):
                bxp, byp = rnd.uniform(-0.15, 0.15), rnd.uniform(-0.12, 0.12)
                bz = z + 0.06 + (0.02 if i < 4 else rnd.uniform(0.1, 0.32))
                sphere(f"Beetle{i}", 0.045, (x + bxp, yc + byp, bz), K["beetle"], seg=10, rings=6, scale=(0.75, 1.2, 0.55))
                sphere(f"BeetleHead{i}", 0.022, (x + bxp, yc + byp - 0.06, bz), K["beetle"], seg=8, rings=4)
        elif what == "root":
            tube("Root", [(x, yc, cz + 0.32), (x + 0.02, yc, cz + 0.12), (x - 0.01, yc, cz - 0.05)], 0.05, K["root"])
            for i, (dx, dz) in enumerate(((-0.12, -0.3), (0.1, -0.32), (-0.05, -0.34), (0.14, -0.15), (-0.13, -0.1))):
                tube(f"RootLeg{i}", [(x, yc, cz - 0.04), (x + dx * 0.5, yc + 0.02 * i - 0.04, cz + dz * 0.5), (x + dx, yc + 0.03 * (i - 2), cz + dz)],
                     0.022 - 0.002 * i, K["root"])
            for i in range(4):
                a = i * 1.6
                strip(f"RootLeaf{i}", [(x, yc, cz + 0.32), (x + math.cos(a) * 0.08, yc + math.sin(a) * 0.06, cz + 0.42),
                                       (x + math.cos(a) * 0.12, yc + math.sin(a) * 0.08, cz + 0.36)], 0.05, (-math.sin(a), math.cos(a), 0), K["liq_g"], thick=0.006, it=2)
        else:
            sphere("OctoHead", 0.11, (x, yc, cz + 0.12), K["pale"], seg=14, rings=8, scale=(0.9, 0.85, 1.2))
            for i in range(8):
                a = i / 8 * 2 * math.pi
                c, s_ = math.cos(a), math.sin(a)
                tube(f"Arm{i}", [(x + c * 0.05, yc + s_ * 0.05, cz + 0.02), (x + c * 0.14, yc + s_ * 0.12, cz - 0.08), (x + c * 0.12, yc + s_ * 0.1, cz - 0.2),
                                  (x + c * 0.05, yc + s_ * 0.04, cz - 0.24)], 0.018, K["pale"])
            for sx in (-1, 1):
                sphere(f"OctoEye{sx}", 0.02, (x + sx * 0.05, yc - 0.08, cz + 0.08), K["ink"], seg=8, rings=4)
    return _dims()


def microscope(M):
    K = kit(M)
    lq, br = K["lacquer"], K["brassf"]
    pts = []
    for i in range(17):
        a = math.pi * 0.15 + i / 16 * math.pi * 1.7
        pts.append((math.cos(a - math.pi / 2) * 0.32, math.sin(a - math.pi / 2) * 0.36))
    inner = [(px * 0.55, py * 0.55 + 0.04) for px, py in reversed(pts)]
    B20.tprism("Foot", pts + inner, 0.0, 0.06, lq, plane="XY", bevel=0.01)
    cyl("Pillar", 0.07, 0.4, (0, 0.05, 0.26), br, verts=16, bevel=0.01)
    box("Trunnion", (0.24, 0.12, 0.12), (0, 0.05, 0.5), br, bevel=0.02)
    s = _mark()
    # the limb, the stage, the mirror below, the tube and its optics: built about the trunnion, tilted back a little
    tube("Limb", [(0, 0.05, 0.0), (0, 0.14, 0.18), (0, 0.13, 0.5), (0, 0.06, 0.66)], 0.05, lq, square=True)
    box("Stage", (0.42, 0.42, 0.035), (0, -0.12, 0.2), lq, bevel=0.01)
    cyl("StageHole", 0.045, 0.04, (0, -0.12, 0.2), K["ink"], verts=12, bevel=0.0)
    box("StageArm", (0.1, 0.2, 0.05), (0, 0.0, 0.18), lq, bevel=0.01)
    for sx in (-1, 1):
        tube(f"Clip{sx}", [(sx * 0.12, 0.0, 0.225), (sx * 0.1, -0.12, 0.23), (sx * 0.06, -0.22, 0.222)], 0.01, br)
        sphere(f"ClipScrew{sx}", 0.018, (sx * 0.12, 0.0, 0.228), br, seg=8, rings=4)
    box("Slide", (0.3, 0.1, 0.006), (0, -0.14, 0.222), K["glass"], bevel=0.0)
    tube("MirrorArm", [(0, 0.05, 0.12), (0, -0.04, 0.02), (0, -0.12, -0.04)], 0.016, br)
    s2 = _mark()
    cyl("Mirror", 0.1, 0.02, (0, 0, 0), K["mirror"], verts=24, bevel=0.004)
    hoop("MirrorRim", (0, 0, 0.0), 0.1, "Z", br, thick=0.014)
    _xform(s2, T(0, -0.12, -0.06) @ RX(25 * DEG))
    lathe("Tube", [(0, 0.0), (0.055, 0.0), (0.06, 0.03), (0.06, 0.5), (0.065, 0.52), (0.065, 0.56), (0, 0.56)], br, seg=20, loc=(0, -0.12, 0.42))
    lathe("Eyepiece", [(0, 0), (0.04, 0), (0.04, 0.1), (0.05, 0.11), (0.052, 0.15), (0.04, 0.16), (0, 0.16)], lq, seg=18, loc=(0, -0.12, 0.98))
    cyl("Nosepiece", 0.075, 0.04, (0, -0.12, 0.41), br, verts=18, bevel=0.01)
    for k, dx in enumerate((-0.035, 0.035)):
        lathe(f"Objective{k}", [(0, 0), (0.016, 0), (0.022, 0.03), (0.026, 0.1), (0, 0.1)], br, seg=12, loc=(dx, -0.12, 0.3))
    box("Rack", (0.05, 0.12, 0.4), (0, -0.04, 0.66), br, bevel=0.01)
    for sx in (-1, 1):
        cyl(f"Focus{sx}", 0.06, 0.04, (sx * 0.1, -0.03, 0.62), br, rot=(0, math.pi / 2, 0), verts=18, bevel=0.008)
        cyl(f"FocusFine{sx}", 0.035, 0.04, (sx * 0.1, 0.12, 0.38), br, rot=(0, math.pi / 2, 0), verts=14, bevel=0.006)
    cyl("FocusAxle", 0.018, 0.2, (0, -0.03, 0.62), br, rot=(0, math.pi / 2, 0), verts=8, bevel=0.0)
    _xform(s, T(0, 0.05, 0.5) @ RX(-10 * DEG) @ T(0, -0.05, 0))
    _fine(0.5)
    return _dims()


def wall_map(M):
    K = kit(M)
    oak = K["oak"]
    W = 4.6
    zt = 3.55
    box("Batten", (W, 0.1, 0.34), (0, -0.05, zt - 0.17), oak, bevel=0.02)
    box("BattenMould", (W + 0.06, 0.14, 0.06), (0, -0.07, zt - 0.02), K["ebony"], bevel=0.015)
    zr = zt - 0.3
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.12)
        box(f"Bracket{sx}", (0.06, 0.28, 0.22), (x, -0.22, zr + 0.02), K["brassf"], bevel=0.015)
        cyl(f"EndCap{sx}", 0.1, 0.06, (x - sx * 0.07, -0.3, zr), K["brassf"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.012)
    cyl("Roller", 0.085, W - 0.4, (0, -0.3, zr), K["oakdk"], rot=(0, math.pi / 2, 0), verts=24, bevel=0.01)
    mw, mh = 4.1, 2.77
    z_bot = zr - 0.02 - mh

    def fn(s, t):
        x = (s - 0.5) * mw
        z = z_bot + t * mh
        y = -0.39 - 0.015 * math.sin(s * math.pi * 3) * (1 - t) - 0.02 * (1 - t) ** 2
        return (x, y, z)
    B30.leaf_sheet("Map", "SP_Map", fn, 16, 10, (0, 0, 1, 1), K["sp"], thick=0.008, k=3.0)
    cyl("Lath", 0.04, mw + 0.12, (0, -0.41, z_bot), K["oakdk"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.008)
    for sx in (-1, 1):
        sphere(f"LathEnd{sx}", 0.05, (sx * (mw / 2 + 0.07), -0.41, z_bot), K["brassf"], seg=10, rings=5)
    tube("Cord", [(0, -0.43, z_bot - 0.02), (0.01, -0.43, z_bot - 0.3), (0, -0.43, z_bot - 0.52)], 0.01, K["cord"])
    hoop("PullRing", (0, -0.43, z_bot - 0.6), 0.08, "Y", K["brassf"], thick=0.016)
    return _dims()


def writing_slate(M):
    K = kit(M)
    w, d = 0.95, 0.72
    fw = 0.07
    B30.plate("Slate", "SP_Slate", w - 2 * fw + 0.02, d - 2 * fw + 0.02, 0.025, T(0, 0, 0.0125) @ FACE_UP, K["sp"], edge="SP_slate", k=2.8)
    for nm, sz, loc in (("FrameT", (w, fw, 0.05), (0, d / 2 - fw / 2, 0.025)), ("FrameB", (w, fw, 0.05), (0, -d / 2 + fw / 2, 0.025)),
                        ("FrameL", (fw, d, 0.05), (-w / 2 + fw / 2, 0, 0.025)), ("FrameR", (fw, d, 0.05), (w / 2 - fw / 2, 0, 0.025))):
        box(nm, sz, loc, K["oak"], bevel=0.012)
    hoop("CordLoop", (0, d / 2 + 0.06, 0.01), 0.07, "Z", K["cord"], thick=0.008)
    cyl("Chalk", 0.022, 0.24, (0.62, -0.1, 0.022), K["chalk"], rot=(0, math.pi / 2, 0.3), verts=10, bevel=0.005)
    cyl("SlatePencil", 0.012, 0.36, (0.64, 0.15, 0.012), K["slate"], rot=(0, math.pi / 2, -0.2), verts=8, bevel=0.003)
    box("PencilWrap", (0.12, 0.03, 0.03), (0.6, 0.16, 0.012), K["paper"], bevel=0.006, rot=(0, 0, -0.2))
    _fine(0.4)
    return _dims()


def inkwell_set(M):
    K = kit(M)
    W, D = 1.7, 1.05
    box("Pad", (W, D, 0.03), (0, 0, 0.015), K["leather"], bevel=0.008)
    B30.plate("Blotter", "SP_Blotter", W - 0.36, D - 0.1, 0.006, T(0, 0, 0.033) @ FACE_UP, K["sp"], edge="SP_blotter", k=2.4)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.2, D + 0.02, 0.045), (sx * (W / 2 - 0.1), 0, 0.03), K["leather"], bevel=0.012)
        tube(f"Bead{sx}", [(sx * (W / 2 - 0.2), -D / 2, 0.055), (sx * (W / 2 - 0.2), D / 2, 0.055)], 0.008, K["gilt"], poly=True)
    # the standish at the back of the pad
    sz = 0.035
    box("Standish", (0.95, 0.42, 0.07), (0, 0.22, sz + 0.035), K["ebony"], bevel=0.02)
    box("PenGroove", (0.8, 0.08, 0.02), (0, 0.06, sz + 0.07), K["ink"], bevel=0.0)
    for k, x in enumerate((-0.25, 0.25)):
        cyl(f"WellPlate{k}", 0.14, 0.02, (x, 0.28, sz + 0.08), K["brassf"], verts=8, bevel=0.005)
        lathe(f"Well{k}", [(0, 0), (0.11, 0), (0.12, 0.02), (0.12, 0.12), (0.09, 0.15), (0.05, 0.16), (0.05, 0.19), (0, 0.19)], K["inkglass"], seg=8,
              loc=(x, 0.28, sz + 0.09))
        cyl(f"WellInk{k}", 0.1, 0.08, (x, 0.28, sz + 0.13), K["ink"], verts=8, bevel=0.0)
        lathe(f"Collar{k}", [(0.048, 0.17), (0.065, 0.17), (0.065, 0.21), (0.048, 0.21)], K["brassf"], seg=14, loc=(x, 0.28, sz + 0.09))
        s = _mark()
        lathe(f"Lid{k}", [(0, 0), (0.07, 0), (0.07, 0.02), (0.045, 0.035), (0.02, 0.05), (0, 0.05)], K["brassf"], seg=14)
        _xform(s, T(x, 0.28 + (0.1 if k == 0 else 0), sz + 0.3 + (0.04 if k == 0 else 0)) @ (RX(-75 * DEG) if k == 0 else Matrix.Identity(4)))
    for k in range(2):
        s = _mark()
        lathe(f"Holder{k}", [(0, 0), (0.014, 0), (0.022, 0.08), (0.02, 0.4), (0.012, 0.48), (0, 0.48)], K["ebony"] if k == 0 else K["red"], seg=10)
        lathe(f"Ferrule{k}", [(0.014, -0.05), (0.017, -0.05), (0.017, 0.02), (0.014, 0.02)], K["brassf"], seg=10)
        strip(f"Nib{k}", [(0, 0, -0.05), (0, 0, -0.08), (0, 0, -0.11)], 0.022, (1, 0, 0), K["steel"], thick=0.004, it=1)
        _xform(s, T(-0.25 + k * 0.08, 0.06 + k * 0.01, sz + 0.1 + k * 0.03) @ RZ(-90 * DEG) @ RY(88 * DEG))
    # the rocker blotter in front, its curved foot wrapped in blotting paper
    s = _mark()
    bm = bmesh.new()
    rows = []
    for i in range(9):
        a = -0.45 + 0.9 * i / 8
        rows.append([bm.verts.new((math.sin(a) * 0.5, y, 0.5 - math.cos(a) * 0.5)) for y in (-0.15, 0.15)])
    for i in range(8):
        bm.faces.new((rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]))
    ob = DM.mesh_obj("RockerPaper", bm, K["paper"])
    _solid(ob, 0.012)
    box("RockerTop", (0.44, 0.3, 0.05), (0, 0, 0.085), K["ebony"], bevel=0.015)
    box("RockerPlate", (0.36, 0.22, 0.012), (0, 0, 0.115), K["brassf"], bevel=0.004)
    lathe("RockerKnob", [(0, 0), (0.03, 0), (0.02, 0.04), (0.05, 0.09), (0.045, 0.13), (0, 0.14)], K["brassf"], seg=14, loc=(0, 0, 0.12))
    _xform(s, T(0.35, -0.3, sz + 0.006) @ RZ(15 * DEG))
    _fine(0.4)
    return _dims()


def satchel(M):
    K = kit(M)
    L = K["satchel"]
    W, D, H = 1.25, 0.4, 0.9
    rbox("Body", W / 2, D / 2, 0.08, 0.0, H, L, step=0.04, rows=4, bevel=0.0)
    box("Gusset", (W + 0.02, D - 0.1, 0.04), (0, 0, H - 0.02), L, bevel=0.015)
    # the flap: over the top and down the front, its bottom corners rounded
    box("FlapTop", (W + 0.04, D + 0.04, 0.03), (0, 0.0, H + 0.015), L, bevel=0.012)
    cyl("FlapRoll", 0.035, W + 0.04, (0, -D / 2 - 0.005, H - 0.015), L, rot=(0, math.pi / 2, 0), verts=12, bevel=0.0)
    pts = [(-W / 2 - 0.02, H - 0.02)] + [(-W / 2 - 0.02 + 0.12 - math.cos(a) * 0.12, 0.34 + 0.12 - math.sin(a) * 0.12) for a in [i * math.pi / 12 for i in range(7)]]
    pts += [(W / 2 + 0.02 - 0.12 + math.cos(a) * 0.12, 0.34 + 0.12 - math.sin(a) * 0.12) for a in [math.pi / 2 - i * math.pi / 12 for i in range(7)]]
    pts += [(W / 2 + 0.02, H - 0.02)]
    B20.tprism("Flap", WS.ccw(pts), -D / 2 - 0.022, 0.025, L, bevel=0.008)
    stitch = flat("Stitch", (0.5, 0.42, 0.3), 0.8)
    tube("FlapStitch", [(x, -D / 2 - 0.036, z) for x, z in WS.offset(WS.ccw(pts), -0.03)], 0.004, stitch, closed=True, poly=True)
    for sx in (-1, 1):
        x = sx * 0.3
        box(f"Strap{sx}", (0.1, 0.012, 0.42), (x, -D / 2 - 0.04, 0.48), L, bevel=0.004)
        box(f"StrapLow{sx}", (0.1, 0.012, 0.3), (x, -D / 2 - 0.006, 0.18), L, bevel=0.004)
        tube(f"Buckle{sx}", [(x - 0.07, -D / 2 - 0.035, 0.3), (x + 0.07, -D / 2 - 0.035, 0.3), (x + 0.07, -D / 2 - 0.035, 0.42), (x - 0.07, -D / 2 - 0.035, 0.42)],
             0.011, K["brassf"], closed=True, poly=True)
        box(f"Tongue{sx}", (0.012, 0.01, 0.12), (x, -D / 2 - 0.048, 0.36), K["brassf"], bevel=0.003)
        box(f"Keeper{sx}", (0.13, 0.016, 0.04), (x, -D / 2 - 0.05, 0.27), L, bevel=0.005)
    tube("Handle", [(-0.2, 0, H + 0.03), (-0.18, 0, H + 0.18), (0, 0, H + 0.24), (0.18, 0, H + 0.18), (0.2, 0, H + 0.03)], 0.025, L)
    for sx in (-1, 1):
        box(f"HandleTab{sx}", (0.08, 0.06, 0.04), (sx * 0.2, 0, H + 0.04), L, bevel=0.01)
        hoop(f"DRing{sx}", (sx * (W / 2 + 0.01), 0, H - 0.12), 0.05, "X", K["brassf"], thick=0.01)
    strip("ShoulderStrap", [(-W / 2 - 0.01, 0.0, H - 0.17), (-W / 2 - 0.05, 0.15, 0.4), (-W / 2 + 0.1, 0.45, 0.02), (0, 0.6, 0.01), (W / 2 - 0.1, 0.45, 0.02),
                            (W / 2 + 0.05, 0.15, 0.4), (W / 2 + 0.01, 0.0, H - 0.17)], 0.09, (0, 0, 1), L, thick=0.012)
    _fine(0.5)
    return _dims()


def dunce_stool(M):
    K = kit(M)
    oak = K["oak"]
    zs = 2.6
    lathe("Seat", [(0, zs - 0.12), (0.46, zs - 0.12), (0.5, zs - 0.08), (0.5, zs - 0.03), (0.47, zs), (0, zs)], oak, seg=32)
    hoop("SeatBead", (0, 0, zs - 0.1), 0.465, "Z", K["ebony"], thick=0.012)
    for k in range(4):
        a = (45 + 90 * k) * DEG
        c, s = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.3, s * 0.3, zs - 0.12), (c * 0.48, s * 0.48, 0.0)], 0.045, oak, square=True, poly=True)
        cyl(f"Shoe{k}", 0.06, 0.05, (c * 0.48, s * 0.48, 0.025), K["iron"], verts=10, bevel=0.008)
    for k, z in enumerate((0.7, 1.6)):
        f = 1 - z / zs
        r = 0.3 + 0.18 * f
        tube(f"Ring{k}", [(math.cos((45 + 90 * i) * DEG) * r, math.sin((45 + 90 * i) * DEG) * r, z) for i in range(4)], 0.025, K["iron"] if k else oak,
             closed=True, poly=True, square=k == 0)
    wrap_lathe("Cap", [(0, 0), (0.36, 0), (0.37, 0.02), (0.0, 1.25)], K["sp"], key="SP_Dunce", wrap=(0.015, 1.25), base="SP_paper", seg=36,
               mtx=T(0.02, 0.0, zs) @ RZ(-10 * DEG), step=0.06)
    hoop("CapBand", (0.02, 0.0, zs + 0.02), 0.368, "Z", K["paper"], thick=0.012)
    sphere("Pompom", 0.07, (0.02, 0.0, zs + 1.28), K["velvet"], seg=12, rings=6)
    return _dims()


def upright_piano(M):
    K = kit(M)
    eb = K["ebony"]
    W, D, H = 5.2, 2.0, 4.6
    zk = 2.45              # the key tops
    kd = 0.75              # the keyboard's depth out from the case front
    yc = -D / 2 + kd       # the case front above and below the keys
    for sx in (-1, 1):
        box(f"Cheek{sx}", (0.14, D - kd, H - 0.1), (sx * (W / 2 - 0.07), yc + (D - kd) / 2, (H - 0.1) / 2), eb, bevel=0.02)
        box(f"KeyCheek{sx}", (0.18, kd + 0.05, 0.42), (sx * (W / 2 - 0.09), -D / 2 + kd / 2, zk - 0.1), eb, bevel=0.03)
        lathe(f"Leg{sx}", [(0, 0), (0.1, 0), (0.1, 0.06), (0.07, 0.15), (0.09, 0.5), (0.11, 1.1), (0.1, 1.6), (0.14, zk - 0.32), (0, zk - 0.32)], eb, seg=14,
              loc=(sx * (W / 2 - 0.12), -D / 2 + 0.12, 0))
        cyl(f"LegCap{sx}", 0.12, 0.05, (sx * (W / 2 - 0.12), -D / 2 + 0.12, 0.025), K["brassf"], verts=14, bevel=0.008)
        box(f"Toe{sx}", (0.16, D - kd + 0.1, 0.12), (sx * (W / 2 - 0.08), yc + (D - kd) / 2 - 0.05, 0.06), eb, bevel=0.02)
    box("Back", (W - 0.2, 0.1, H - 0.1), (0, D / 2 - 0.05, (H - 0.1) / 2), K["oakdk"], bevel=0.01)
    box("Lid", (W + 0.08, D - kd + 0.12, 0.1), (0, yc + (D - kd) / 2 - 0.02, H - 0.05), eb, bevel=0.03)
    box("LidMould", (W + 0.02, 0.06, 0.08), (0, yc - 0.06, H - 0.14), eb, bevel=0.02)
    tube("LidHinge", [(-W / 2 + 0.2, yc + 0.35, H + 0.002), (W / 2 - 0.2, yc + 0.35, H + 0.002)], 0.012, K["brassf"], poly=True)
    box("KneeBoard", (W - 0.28, 0.08, zk - 0.6), (0, yc - 0.04, (zk - 0.6) / 2 + 0.12), eb, bevel=0.015)
    box("KneePanel", (W - 1.0, 0.04, zk - 1.1), (0, yc - 0.1, (zk - 0.6) / 2 + 0.12), eb, bevel=0.03, segments=3)
    foil("KneeFoil", 0, yc - 0.125, (zk - 0.6) / 2 + 0.12, 0.18, K["gilt"], lobes=4, thick=0.014)
    box("Plinth", (W - 0.28, 0.2, 0.14), (0, yc - 0.05, 0.07), eb, bevel=0.02)
    for k, x in enumerate((-0.35, 0.0, 0.35)):
        box(f"PedalBox{k}", (0.1, 0.12, 0.06), (x, yc - 0.18, 0.18), K["brassf"], bevel=0.015)
        tube(f"Pedal{k}", [(x, yc - 0.2, 0.18), (x, yc - 0.45, 0.16), (x, yc - 0.55, 0.15)], 0.03, K["brassf"], square=True)
    box("KeyBed", (W - 0.36, kd, 0.2), (0, -D / 2 + kd / 2, zk - 0.2), eb, bevel=0.015)
    box("KeySlip", (W - 0.36, 0.05, 0.12), (0, -D / 2, zk - 0.11), eb, bevel=0.012)
    kw = (W - 0.48) / 52
    x0 = -(W - 0.48) / 2
    for i in range(52):
        box(f"White{i}", (kw - 0.008, 0.5, 0.07), (x0 + kw * (i + 0.5), -D / 2 + 0.3, zk - 0.035), K["ivory"], bevel=0.006)
    pat = [1, 0, 1, 1, 0, 1, 1]     # a black key after these whites (the keyboard starts on A)
    for i in range(51):
        if pat[i % 7]:
            box(f"Black{i}", (kw * 0.55, 0.3, 0.07), (x0 + kw * (i + 1), -D / 2 + 0.4, zk + 0.035), eb, bevel=0.008)
    box("Fallboard", (W - 0.36, 0.06, 0.3), (0, -D / 2 + 0.6, zk + 0.18), eb, bevel=0.015, rot=(-0.25, 0, 0))
    tube("FallBead", [(-W / 2 + 0.4, -D / 2 + 0.565, zk + 0.2), (W / 2 - 0.4, -D / 2 + 0.565, zk + 0.2)], 0.008, K["gilt"], poly=True)
    zu0, zu1 = zk + 0.35, H - 0.25
    box("UpperBack", (W - 0.28, 0.06, zu1 - zu0), (0, yc, (zu0 + zu1) / 2), K["silk"], bevel=0.0)
    box("UpperRailB", (W - 0.28, 0.08, 0.2), (0, yc - 0.06, zu0 + 0.1), eb, bevel=0.015)
    box("UpperRailT", (W - 0.28, 0.08, 0.22), (0, yc - 0.06, zu1 - 0.11), eb, bevel=0.015)
    n = 3
    pw = (W - 0.28) / n
    for i in range(n):
        cx = -(W - 0.28) / 2 + pw * (i + 0.5)
        hw = pw / 2 - 0.16
        z0a, z1a = zu0 + 0.2, zu1 - 0.22
        za = z1a - 0.05
        zs_ = za - hw * 1.5
        hole = WS.arch(hw, z0a + 0.12, zs_, za, 14, cx=cx)
        box(f"FretL{i}", (0.16, 0.08, z1a - z0a), (cx - pw / 2 + 0.08, yc - 0.06, (z0a + z1a) / 2), eb, bevel=0.012)
        box(f"FretR{i}", (0.16, 0.08, z1a - z0a), (cx + pw / 2 - 0.08, yc - 0.06, (z0a + z1a) / 2), eb, bevel=0.012)
        box(f"FretB{i}", (pw - 0.3, 0.08, 0.12), (cx, yc - 0.06, z0a + 0.06), eb, bevel=0.012)
        for side in (-1, 1):
            pts = [(cx + x, z) for x, z in WS.pointed(hw, zs_, za, 14) if (x <= 0 if side < 0 else x >= 0)]
            if side < 0:
                poly = [(cx - hw, zs_)] + pts[1:] + [(cx, z1a), (cx - hw, z1a)]
            else:
                poly = pts[:-1] + [(cx + hw, zs_), (cx + hw, z1a), (cx, z1a)]
            B20.tprism(f"Spandrel{i}{side}", WS.ccw(poly), yc - 0.06, 0.08, eb)
        tube(f"FretArch{i}", [(x, yc - 0.105, z) for x, z in hole], 0.018, K["gilt"], poly=True)
        tube(f"Mullion{i}", [(cx, yc - 0.07, z0a + 0.12), (cx, yc - 0.07, zs_ - 0.1)], 0.025, eb, square=True, poly=True)
        foil(f"Foil{i}", cx, yc - 0.07, (zs_ + za) / 2 - 0.05, hw * 0.45, eb, lobes=4, thick=0.022)
    zm = zk + 0.55
    box("DeskLedge", (2.4, 0.18, 0.05), (0, yc - 0.18, zm), eb, bevel=0.015)
    box("DeskLip", (2.4, 0.03, 0.08), (0, yc - 0.26, zm + 0.05), eb, bevel=0.008)
    for k, x in enumerate((-0.55, 0.55)):
        B30.plate(f"Music{k}", "SP_Music_A" if k == 0 else "SP_Music_B", 1.02, 1.34, 0.006, T(x, yc - 0.14, zm + 0.7) @ RX(-12 * DEG), K["sp"],
                  edge="SP_paper", k=2.6)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.45)
        zc_ = zk + 1.05
        box(f"SconcePlate{sx}", (0.18, 0.02, 0.3), (x, yc - 0.11, zc_), K["brassf"], bevel=0.008)
        tube(f"SconceArm{sx}", [(x, yc - 0.12, zc_), (x + sx * 0.1, yc - 0.3, zc_ - 0.05), (x + sx * 0.18, yc - 0.45, zc_ + 0.02)], 0.022, K["brassf"])
        lathe(f"SconceCup{sx}", [(0, 0), (0.05, 0), (0.12, 0.04), (0.13, 0.06), (0.06, 0.07), (0.05, 0.13), (0.0, 0.13)], K["brassf"], seg=18,
              loc=(x + sx * 0.18, yc - 0.45, zc_))
        lathe(f"Candle{sx}", [(0, 0), (0.042, 0), (0.042, 0.38), (0.035, 0.4), (0, 0.4)], K["wax"], seg=14, loc=(x + sx * 0.18, yc - 0.45, zc_ + 0.12))
        tube(f"Wick{sx}", [(x + sx * 0.18, yc - 0.45, zc_ + 0.5), (x + sx * 0.18, yc - 0.45, zc_ + 0.55)], 0.006, K["ink"], poly=True)
    return _dims()


def music_stand(M):
    K = kit(M)
    ir = K["iron"]
    hub = 0.55
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.05, s * 0.05, hub), (c * 0.3, s * 0.3, 0.3), (c * 0.6, s * 0.6, 0.05), (c * 0.7, s * 0.7, 0.02)], 0.025, ir, square=True)
        tube(f"Scroll{k}", [(c * 0.7, s * 0.7, 0.02), (c * 0.78, s * 0.78, 0.06), (c * 0.74, s * 0.74, 0.12), (c * 0.68, s * 0.68, 0.09)], 0.018, ir)
        tube(f"LegScroll{k}", [(c * 0.12, s * 0.12, hub - 0.1), (c * 0.25, s * 0.25, hub - 0.05), (c * 0.28, s * 0.28, hub - 0.18), (c * 0.2, s * 0.2, hub - 0.2)],
             0.014, ir)
    cyl("Hub", 0.06, 0.16, (0, 0, hub), ir, verts=14, bevel=0.012)
    cyl("Column", 0.03, 2.0, (0, 0, hub + 1.0), ir, verts=12, bevel=0.0)
    cyl("Collar", 0.05, 0.1, (0, 0, hub + 2.0), K["brassf"], verts=14, bevel=0.01)
    sphere("CollarKnob", 0.03, (0.07, 0, hub + 2.0), K["brassf"], seg=8, rings=4)
    cyl("Inner", 0.022, 0.6, (0, 0, hub + 2.3), ir, verts=10, bevel=0.0)
    s = _mark()
    dw, dh = 1.5, 1.05
    tube("DeskFrame", [(-dw / 2, 0, 0), (dw / 2, 0, 0), (dw / 2, 0, dh), (-dw / 2, 0, dh)], 0.022, ir, closed=True, poly=True, square=True)
    for sx in (-1, 1):
        tube(f"Lyre{sx}", [(sx * 0.08, -0.005, 0.02), (sx * 0.4, -0.005, 0.25), (sx * 0.3, -0.005, 0.7), (sx * 0.12, -0.005, 0.95)], 0.014, ir)
        tube(f"Brace{sx}", [(0, 0, 0.0), (sx * dw / 2, 0, dh * 0.55)], 0.014, ir, poly=True)
    tube("Mid", [(-dw / 2, 0, dh * 0.55), (dw / 2, 0, dh * 0.55)], 0.012, ir, poly=True)
    foil("DeskFoil", 0, -0.01, 0.55, 0.1, K["brassf"], lobes=4, thick=0.01)
    box("Ledge", (dw + 0.1, 0.14, 0.03), (0, -0.07, -0.01), ir, bevel=0.008)
    box("LedgeLip", (dw + 0.1, 0.02, 0.06), (0, -0.14, 0.02), ir, bevel=0.006)
    B30.plate("SheetA", "SP_Music_A", 0.72, 0.95, 0.006, T(-0.37, -0.04, 0.48), K["sp"], edge="SP_paper", k=2.6)
    B30.plate("SheetB", "SP_Music_B", 0.72, 0.95, 0.006, T(0.37, -0.035, 0.49) @ RY(2 * DEG), K["sp"], edge="SP_paper", k=2.6)
    _xform(s, T(0, 0, hub + 2.6) @ RX(-22 * DEG))
    return _dims()


def metronome(M):
    K = kit(M)
    eb = K["ebony"]
    s = _mark()
    r = 0.3 / math.cos(math.pi / 4)
    lathe("Case", [(0, 0), (r + 0.03, 0), (r + 0.03, 0.06), (r, 0.08), (0.03, 0.88), (0.0, 0.9)], eb, seg=4)
    lathe("Plinth", [(0, 0), (r + 0.06, 0), (r + 0.06, 0.03), (0, 0.03)], K["brassf"], seg=4)
    _xform(s, RZ(math.pi / 4))
    slope = math.atan(0.3 / 0.8)

    def face(zz, off=0.0):
        y = -(0.3 - 0.3 * (zz - 0.08) / 0.8)
        n = Vector((0, -math.cos(slope), math.sin(slope)))
        return Vector((0, y, zz)) + n * off
    c = face(0.45, 0.004)
    B30.plate("Scale", "SP_Metro", 0.09, 0.45, 0.006, T(*c) @ RX(-slope), K["sp"], edge="SP_gilt", k=2.6)
    p0 = face(0.17, 0.03)
    s = _mark()
    tube("Rod", [(0, 0, 0), (0, 0, 0.62)], 0.008, K["steel"], poly=True)
    box("Weight", (0.07, 0.03, 0.06), (0, 0, 0.36), K["brassf"], bevel=0.01)
    sphere("RodTip", 0.012, (0, 0, 0.63), K["brassf"], seg=8, rings=4)
    _xform(s, T(*p0) @ RX(-slope) @ RY(8 * DEG))
    cyl("Pivot", 0.025, 0.04, tuple(p0), K["brassf"], rot=(math.pi / 2 - slope, 0, 0), verts=12, bevel=0.005)
    cyl("KeyShaft", 0.015, 0.1, (0.28, 0, 0.2), K["brassf"], rot=(0, math.pi / 2, 0), verts=8, bevel=0.0)
    box("KeyBow", (0.02, 0.12, 0.08), (0.34, 0, 0.2), K["brassf"], bevel=0.01)
    _fine(0.5)
    return _dims()


def radiator(M):
    K = kit(M)
    ir = K["iron"]
    n = 14
    sw = 0.21
    W = n * sw
    z0, z1 = 0.25, 2.55
    for i in range(n):
        x = -W / 2 + sw * (i + 0.5)
        box(f"Head{i}", (sw - 0.02, 0.62, 0.22), (x, 0, z1 - 0.11), ir, bevel=0.06, segments=3)
        box(f"Foot{i}", (sw - 0.02, 0.62, 0.22), (x, 0, z0 + 0.11), ir, bevel=0.06, segments=3)
        for k, y in enumerate((-0.2, 0.0, 0.2)):
            cyl(f"Col{i}{k}", 0.055, z1 - z0 - 0.4, (x, y, (z0 + z1) / 2), ir, verts=10, bevel=0.0)
        if i % 2 == 0:
            foil(f"HeadFoil{i}", x, -0.315, z1 - 0.11, 0.06, K["iron"], lobes=4, thick=0.01, n=8)
        if i < n - 1:
            box(f"Neck{i}", (0.06, 0.5, 0.08), (x + sw / 2, 0, z1 - 0.11), ir, bevel=0.02)
            box(f"NeckLow{i}", (0.06, 0.5, 0.08), (x + sw / 2, 0, z0 + 0.11), ir, bevel=0.02)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.3)
        tube(f"Leg{sx}", [(x, -0.2, z0 + 0.05), (x, -0.25, 0.05), (x, -0.32, 0.0)], 0.04, ir, square=True)
        tube(f"LegB{sx}", [(x, 0.2, z0 + 0.05), (x, 0.25, 0.05), (x, 0.32, 0.0)], 0.04, ir, square=True)
    xv = -W / 2 - 0.15
    cyl("InletStub", 0.05, 0.2, (-W / 2 - 0.05, 0, z0 + 0.11), K["brassf"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.008)
    sphere("Valve", 0.09, (xv, 0, z0 + 0.11), K["brassf"], seg=14, rings=7)
    cyl("Spindle", 0.02, 0.16, (xv, 0, z0 + 0.26), K["brassf"], verts=8, bevel=0.0)
    hoop("Wheel", (xv, 0, z0 + 0.34), 0.1, "Z", K["iron"], thick=0.016)
    for a in (0, 60, 120):
        tube(f"Spoke{a}", [(xv + math.cos(a * DEG) * 0.1, math.sin(a * DEG) * 0.1, z0 + 0.34), (xv - math.cos(a * DEG) * 0.1, -math.sin(a * DEG) * 0.1, z0 + 0.34)],
             0.01, K["iron"], poly=True)
    tube("Pipe", [(xv, 0, z0 + 0.05), (xv, 0, 0.0)], 0.05, K["brassf"], poly=True)
    cyl("Escutcheon", 0.1, 0.02, (xv, 0, 0.01), K["brassf"], verts=16, bevel=0.005)
    cyl("Bleed", 0.03, 0.08, (W / 2 + 0.03, 0, z1 - 0.11), K["brassf"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.005)
    box("BleedKey", (0.02, 0.08, 0.05), (W / 2 + 0.08, 0, z1 - 0.11), K["brassf"], bevel=0.008)
    return _dims()


def fire_bucket_rack(M):
    K = kit(M)
    W, H = 3.4, 2.5
    oak = K["oak"]
    box("Board", (W, 0.1, H), (0, -0.05, H / 2), oak, bevel=0.025)
    box("Field", (W - 0.5, 0.02, H - 1.1), (0, -0.105, H / 2 - 0.15), K["enamel"], bevel=0.0)
    tube("FieldFrame", [(-(W - 0.5) / 2, -0.12, 0.3), ((W - 0.5) / 2, -0.12, 0.3), ((W - 0.5) / 2, -0.12, H - 0.85), (-(W - 0.5) / 2, -0.12, H - 0.85)], 0.02,
         K["iron"], square=True, closed=True, poly=True)
    box("Rail", (W + 0.06, 0.16, 0.18), (0, -0.12, H - 0.45), K["ebony"], bevel=0.03)
    _gable("Crest", 0, -0.06, 0.8, H, H + 0.45, 0.08, oak, K["ebony"], edge=0.025)
    foil("CrestFoil", 0, -0.11, H + 0.15, 0.1, K["brassf"], lobes=4, thick=0.012)
    zh = H - 0.45
    for k in range(4):
        x = -W / 2 + 0.55 + k * (W - 1.1) / 3
        tube(f"Hook{k}", [(x, -0.2, zh), (x, -0.32, zh - 0.02), (x, -0.36, zh + 0.06)], 0.02, K["iron"])
        zb = zh - 1.12
        prof = [(0, 0), (0.12, 0.0), (0.2, 0.04), (0.24, 0.12), (0.31, 0.72), (0.33, 0.74), (0.33, 0.77), (0.3, 0.77), (0.29, 0.74), (0.22, 0.12), (0, 0.1)]
        wrap_lathe(f"Bucket{k}", prof, K["glaze"], key="SP_Bucket", wrap=(0.12, 0.72), base="SP_mugcrim", seg=32, mtx=T(x, -0.36, zb) @ RZ((k - 1.5) * 6 * DEG),
                   step=0.05)
        hoop(f"Rim{k}", (x, -0.36, zb + 0.76), 0.325, "Z", K["brassf"], thick=0.018)
        cyl(f"Sand{k}", 0.28, 0.02, (x, -0.36, zb + 0.62), K["sand"], verts=24, bevel=0.0)
        for sx in (-1, 1):
            sphere(f"Lug{k}{sx}", 0.035, (x + sx * 0.32, -0.36, zb + 0.68), K["iron"], seg=8, rings=4)
        tube(f"Bail{k}", [(x - 0.32, -0.36, zb + 0.68), (x - 0.25, -0.36, zb + 0.95), (x, -0.36, zh + 0.04), (x + 0.25, -0.36, zb + 0.95), (x + 0.32, -0.36, zb + 0.68)],
             0.016, K["iron"])
    return _dims()


def drinking_fountain(M):
    K = kit(M)
    mb = K["marble"]
    zr = 2.8
    hw = 0.8
    pts = WS.arch(hw, 1.9, 3.6, 4.5, 16)
    B20.tprism("Back", WS.ccw(pts), -0.06, 0.12, mb)
    tube("BackBead", [(x, -0.125, z) for x, z in WS.offset(WS.ccw(pts), -0.08)], 0.015, K["gilt"], closed=True, poly=True)
    foil("BackFoil", 0, -0.13, 3.85, 0.2, K["brassf"], lobes=4, thick=0.016)
    yb = -0.42
    lathe("Basin", [(0, zr - 0.38), (0.2, zr - 0.38), (0.42, zr - 0.28), (0.53, zr - 0.12), (0.56, zr - 0.02), (0.55, zr), (0.49, zr), (0.47, zr - 0.08),
                    (0.38, zr - 0.22), (0.18, zr - 0.3), (0, zr - 0.3)], mb, seg=40, loc=(0, yb, 0))
    hoop("BasinRim", (0, yb, zr - 0.005), 0.555, "Z", K["brassf"], thick=0.014)
    cyl("Drain", 0.07, 0.01, (0, yb, zr - 0.295), K["brassf"], verts=16, bevel=0.0)
    for k in range(5):
        box(f"DrainSlot{k}", (0.1, 0.012, 0.004), (0, yb - 0.04 + k * 0.02, zr - 0.288), K["ink"], bevel=0.0)
    for sx in (-1, 1):
        tube(f"Corbel{sx}", [(sx * 0.25, -0.12, zr - 0.9), (sx * 0.25, -0.12, zr - 0.35), (sx * 0.25, -0.5, zr - 0.33)], 0.035, K["iron"], square=True, poly=True)
        tube(f"CorbelScroll{sx}", [(sx * 0.25, -0.2, zr - 0.5), (sx * 0.25, -0.38, zr - 0.48), (sx * 0.25, -0.4, zr - 0.62), (sx * 0.25, -0.28, zr - 0.64)], 0.022,
             K["iron"])
    tube("DrainPipe", [(0, yb, zr - 0.38), (0, yb, zr - 0.7), (0, yb + 0.12, zr - 0.85), (0, yb + 0.1, zr - 1.0), (0, -0.2, zr - 1.1), (0, -0.2, 0.05)], 0.05, K["brassf"])
    cyl("FloorRose", 0.12, 0.04, (0, -0.2, 0.02), K["brassf"], verts=18, bevel=0.01)
    tube("Spout", [(0, -0.12, zr - 0.05), (0, -0.2, zr + 0.12), (0, -0.3, zr + 0.2), (0, -0.4, zr + 0.17)], 0.03, K["brassf"])
    lathe("Nozzle", [(0, 0), (0.035, 0), (0.04, 0.03), (0.025, 0.06), (0, 0.06)], K["brassf"], seg=14, loc=(0, -0.42, zr + 0.11))
    cyl("SpoutRose", 0.07, 0.03, (0, -0.135, zr - 0.05), K["brassf"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
    cyl("ButtonRose", 0.08, 0.03, (0.48, -0.135, zr + 0.18), K["brassf"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
    cyl("Button", 0.045, 0.05, (0.48, -0.17, zr + 0.18), K["brassf"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.012)
    return _dims()


def vaulting_horse(M):
    K = kit(M)
    oak = K["oak"]
    L, Wd = 4.4, 1.25
    top = 4.0
    zb = 3.0
    box("Frame", (L - 0.4, Wd - 0.25, 0.3), (0, 0, zb + 0.15), oak, bevel=0.03)
    B29.cushion("Body", (L, Wd, top - zb - 0.25), (0, 0, (zb + 0.25 + top) / 2), K["gymleather"], e=(0.35, 0.18), cuts=8,
                piping=K["gymleather"], pipe_r=0.025)
    for i in range(6):
        x = -L / 2 + 0.5 + i * (L - 1.0) / 5
        sphere(f"Button{i}", 0.035, (x, 0, top - 0.005), K["gymleather"], seg=8, rings=4, scale=(1, 1, 0.5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xt, yt = sx * (L / 2 - 0.45), sy * (Wd / 2 - 0.2)
            xf, yf = sx * (L / 2 - 0.15), sy * (Wd / 2 + 0.35)
            zm = 1.4

            def at(z):
                k = 1 - z / zb
                return xt + (xf - xt) * k, yt + (yf - yt) * k
            xm, ym = at(zm)
            tube(f"LegUp{sx}{sy}", [(xt, yt, zb), (*at(zm - 0.2), zm - 0.2)], 0.075, oak, square=True, poly=True)
            tube(f"LegLow{sx}{sy}", [(*at(zm + 0.1), zm + 0.1), (xf, yf, 0.08)], 0.06, oak, square=True, poly=True)
            for dz in (0.0, 0.25):
                z = zm + dz - 0.05
                box(f"Clamp{sx}{sy}{dz}", (0.2, 0.2, 0.08), (*at(z), z), K["iron"], bevel=0.015)
            sphere(f"Peg{sx}{sy}", 0.035, (xm, ym - 0.09 * sy, zm + 0.12), K["brassf"], seg=8, rings=4)
            box(f"Foot{sx}{sy}", (0.18, 0.18, 0.08), (xf, yf, 0.04), K["rubber"], bevel=0.02)
        tube(f"Brace{sx}", [(sx * (L / 2 - 0.27), -(Wd / 2 + 0.17), 0.8), (sx * (L / 2 - 0.27), (Wd / 2 + 0.17), 0.8)], 0.03, K["iron"], poly=True)
    for sy in (-1, 1):
        tube(f"LongBrace{sy}", [(-(L / 2 - 0.25), sy * (Wd / 2 + 0.2), 0.65), ((L / 2 - 0.25), sy * (Wd / 2 + 0.2), 0.65)], 0.03, K["iron"], poly=True)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "Abacus": abacus,
    "AnatomySkeleton": anatomy_skeleton,
    "LabBench": lab_bench,
    "TestTubeRack": test_tube_rack,
    "SpecimenJars": specimen_jars,
    "Microscope": microscope,
    "WallMap": wall_map,
    "WritingSlate": writing_slate,
    "InkwellSet": inkwell_set,
    "Satchel": satchel,
    "DunceStool": dunce_stool,
    "UprightPiano": upright_piano,
    "MusicStand": music_stand,
    "Metronome": metronome,
    "Radiator": radiator,
    "FireBucketRack": fire_bucket_rack,
    "DrinkingFountain": drinking_fountain,
    "VaultingHorse": vaulting_horse,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"Abacus": 1.25, "TestTubeRack": 1.25, "Microscope": 1.45, "Metronome": 1.5, "AnatomySkeleton": 1.0, "DunceStool": 1.05})
B24.SMALL.update({"WritingSlate": 1.2, "InkwellSet": 1.15, "Satchel": 1.3})
