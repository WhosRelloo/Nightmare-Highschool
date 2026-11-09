"""Props batch 43, the gym kit (2026-11-09), for nh_props.py: the old gothic gymnasium and sports hall of the Institution,
Victorian and Edwardian apparatus with a dark academy twist. The house look of batches 34-39: cast iron, dark oak and ebony,
crimson leather and enamel, brass and gilt, black marble, bone, hemp and canvas, with the five house colours (Crimson, Ravens,
Rovers, Vigil, Wardens) and the Athletes' blue. Every name, motto and design is invented.

Apparatus   ClimbingRopes (ceiling), GymRings (ceiling), WallBars (wall), PommelHorse, ParallelBars, BalanceBeam, VaultingBox,
            Springboard, HighJumpStands, MatTrolley
Fitness     MedicineBallRack, IndianClubRack (wall), RowingMachine, WallPulley (wall), PunchingBag (wall), BoxingRingCorner,
            BoxingGloves (plinth)
Fencing     FencingPiste, FencingMaskRack (wall), ArcheryTarget, BowRack
House       KitHamper, WhistleBoard (wall), HousePointsBoard (wall), CursedTrophy (Glow), LockerBench (wall), Megaphone (plinth)
Facilities  SaunaDoor (wall; Door0 swings), EquipmentCage, FirstAidStation (wall), StopwatchStand (Glass), RefereeChair,
            BasketballHoop (wall)

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back on y = 0 (pivot on the wall plane at
their lowest point). The ceiling pieces stand on the floor too: their ropes and rings end just above it and the beam's top is
given in the docs. Printed faces come from art/props/gym_atlas.py (GymPrint). Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish, _quatrefoil
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, prism, _mark, _xform, _dims, flat, _football
from nh_props_batch24 import _text, _fine
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import nh_props_batch36 as B36
import nh_props_batch37 as B37

DEG = math.pi / 180
PI = math.pi
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = B37.FONT
FONT_I = B37.FONT_I

GA = json.load(open(os.path.join(P.HERE, "gym_atlas.json")))
for _k, _v in GA["regions"]["GymPrint"].items():
    B30.REG["GY_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_GY_" + _k[7:]] = _v
SHIELD = GA["shield"]
HOUSES = ("Crimson", "Ravens", "Rovers", "Vigil", "Wardens")


# ------------------------------------------------------------------ materials

def hemp():
    m = flat("GymHemp", (0.36, 0.27, 0.16), 0.92, dirt=0.65)
    nt = m.node_tree
    w = nt.nodes.new("ShaderNodeTexWave")
    w.bands_direction = "DIAGONAL"
    w.inputs["Scale"].default_value = 7.0
    w.inputs["Distortion"].default_value = 1.2
    nt.links.new(B24._coords(nt), w.inputs["Vector"])
    B24._bump(m, w.outputs["Fac"], 0.012)
    return m


def kit(M):
    K = B36.kit(M)
    K.update({
        "gp": B30.atlas_mat("GymPrintMat", "GymPrint", rough=0.55, leather=0.04, wear=0.05, dirt=0.45),
        "hemp": hemp(),
        "suede": B24.leather("GymSuede", (0.24, 0.17, 0.11), scale=6.0, wear=0.1),
        "canvas": B24.cloth("GymCanvas", (0.5, 0.45, 0.35), rough=0.9, weave=0.01),
        "wicker": B24.cloth("GymWicker", (0.3, 0.2, 0.1), rough=0.8, weave=0.045),
        "straw": B24.cloth("GymStraw", (0.48, 0.38, 0.18), rough=0.9, weave=0.025),
        "inkleather": B24.leather("GymInkLeather", (0.03, 0.035, 0.07), scale=3.0, wear=0.3),
        "j_Crimson": B24.cloth("JerseyCrimson", (0.2, 0.012, 0.025), rough=0.9, weave=0.008),
        "j_Ravens": B24.cloth("JerseyRavens", (0.05, 0.02, 0.11), rough=0.9, weave=0.008),
        "j_Rovers": B24.cloth("JerseyRovers", (0.02, 0.07, 0.03), rough=0.9, weave=0.008),
        "j_Vigil": B24.cloth("JerseyVigil", (0.012, 0.014, 0.035), rough=0.9, weave=0.008),
        "j_Wardens": B24.cloth("JerseyWardens", (0.09, 0.09, 0.1), rough=0.9, weave=0.008),
        "towel": B24.cloth("GymTowel", (0.6, 0.56, 0.48), rough=0.95, weave=0.012),
        "athblue": flat("AthleteBlue", (0.03, 0.08, 0.24), 0.35, wear=0.2, dirt=0.5),
        "feltc": B24.cloth("CrimsonFelt", (0.13, 0.008, 0.016), rough=0.97, weave=0.006),
        "silver": material("TarnishedSilver", base=(0.5, 0.49, 0.47), rough=0.3, metal=1.0, wear=0.2, dirt=1.0),
        "mesh": B24.cloth("MaskMesh", (0.07, 0.07, 0.075), rough=0.35, weave=0.02),
        "frost": flat("SteamedGlass", (0.36, 0.42, 0.42), 0.35, dirt=0.3),
        "stone": M["stonedark"],
        "violet": flat("CurseViolet", (0.35, 0.1, 0.8), 0.4),
    })
    return K


# ------------------------------------------------------------------ helpers

def circ(r, n=32, cx=0.0, cz=0.0):
    return [(cx + r * math.cos(i / n * 2 * PI), cz + r * math.sin(i / n * 2 * PI)) for i in range(n)]


def shield_poly(h):
    """The house shield h tall, its point at z = 0, centred on x = 0."""
    return [(u * h, (1 - v) * h) for u, v in SHIELD]


def pprism(name, key, poly, depth, mtx, mat, edge="GY_black", k=2.0, both=False):
    """A flat polygon (x, z) extruded `depth` along Y and centred on y = 0, its front (-Y) face showing the atlas region `key`
    stretched over the polygon's bounds; the sides take the `edge` swatch."""
    bm = bmesh.new()
    a = [bm.verts.new((u, -depth / 2, w)) for u, w in poly]
    b = [bm.verts.new((u, depth / 2, w)) for u, w in poly]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    us, ws = [p[0] for p in poly], [p[1] for p in poly]
    x0, x1, z0, z1 = min(us), max(us), min(ws), max(ws)
    u0, v0, u1, v1 = B30.REG[key]
    pt = B30._swatch(edge)
    for f in bm.faces:
        if f.normal.y < -0.9 or (both and f.normal.y > 0.9):
            flip = f.normal.y > 0
            for lp in f.loops:
                x, _, z = lp.vert.co
                fx = (x - x0) / (x1 - x0)
                if flip:
                    fx = 1 - fx
                lp[uvl].uv = (u0 + fx * (u1 - u0), v0 + (z - z0) / (z1 - z0) * (v1 - v0))
            f[kl] = k
        else:
            for lp in f.loops:
                lp[uvl].uv = pt
            f[kl] = 0.4
    return B30._bm_object(name, bm, mat, mtx)


def rect(w, h, cz=0.0):
    return [(-w / 2, cz - h / 2), (w / 2, cz - h / 2), (w / 2, cz + h / 2), (-w / 2, cz + h / 2)]


def plate(name, key, w, h, t, mtx, K, edge="GY_black"):
    return pprism(name, key, rect(w, h), t, mtx, K["gp"], edge)


def crest(name, house, h, t, mtx, K):
    return pprism(name, f"GY_Crest_{house}", shield_poly(h), t, mtx, K["gp"], "GY_gilt")


def label(name, text, mat, cx, y, cz, w, h, depth=0.01, font=FONT):
    """Raised lettering on a face that looks to -Y at plane y, centred at (cx, cz), fitted into w x h."""
    return _text(name, text, font, mat, lambda x, yy, hh: (cx + x, y - hh, cz + yy), fit=(w, h), depth=depth)


def _ground(s):
    bpy.context.view_layer.update()
    lo = min((ob.matrix_world @ Vector(c)).z for ob in P.PARTS[s:] for c in ob.bound_box)
    _xform(s, T(0, 0, -lo))


def rope(name, pts, r, K, res=5):
    return tube(name, pts, r, K["hemp"], res=res)


def rivet(name, x, y, z, mat, r=0.035, face=-1):
    """A domed rivet head on a face looking to `face` * Y."""
    sphere(name, r, (x, y, z), mat, seg=6, rings=3, scale=(1, 0.5, 1))


def castor(prefix, x, y, ztop, K):
    box(f"{prefix}Plate", (0.26, 0.26, 0.04), (x, y, ztop - 0.02), K["iron"], bevel=0.01)
    for sx in (-1, 1):
        box(f"{prefix}Fork{sx}", (0.03, 0.14, ztop - 0.12), (x + sx * 0.07, y, 0.12 + (ztop - 0.12) / 2 - 0.02), K["iron"], bevel=0.005)
    cyl(f"{prefix}Wheel", 0.12, 0.08, (x, y, 0.12), K["rubber"], rot=(0, PI / 2, 0), verts=16, bevel=0.015)
    cyl(f"{prefix}Hub", 0.05, 0.1, (x, y, 0.12), K["brassf"], rot=(0, PI / 2, 0), verts=10, bevel=0.005)


def ibeam(prefix, L, zb, K, hang=2.0):
    """A heavy riveted iron I-beam along X (bottom at zb, 1.3 deep, flanges 1.0 wide) with stiffener ends and brass quatrefoils on
    its web, hung from the ceiling (`hang` above its top; 0 for none) on two cast-iron hangers pierced with brass-lined lancets."""
    ir, br = K["iron"], K["brassf"]
    D, Wf = 1.3, 1.0
    box(prefix + "FlLo", (L, Wf, 0.14), (0, 0, zb + 0.07), ir, bevel=0.025)
    box(prefix + "Web", (L, 0.14, D - 0.2), (0, 0, zb + D / 2), ir, bevel=0.015)
    box(prefix + "FlHi", (L, Wf, 0.14), (0, 0, zb + D - 0.07), ir, bevel=0.025)
    n = max(2, int(L / 0.5))
    for i in range(n + 1):
        x = -L / 2 + 0.25 + i * (L - 0.5) / n
        for sy in (-1, 1):
            for z in (zb + 0.24, zb + D - 0.24):
                rivet(f"{prefix}Rv{i}{sy}{z:.1f}", x, sy * 0.075, z, ir, r=0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"{prefix}Stiff{sx}{sy}", (0.1, 0.43, D - 0.2), (sx * (L / 2 - 0.08), sy * 0.28, zb + D / 2), ir, bevel=0.015)
    k = max(1, int(L / 2.6))
    for i in range(k):
        x = -L / 2 + L * (i + 0.5) / k
        for sy in (-1, 1):
            _quatrefoil(f"{prefix}Q{i}{sy}", x, sy * 0.085, zb + D / 2, 0.36, br)
    if hang:
        zt = zb + D
        for sx in (-1, 1):
            x = sx * (L / 2 - 0.6)
            hw = 0.5
            outer = [(x - hw, zt), (x + hw, zt), (x + hw * 0.55, zt + hang), (x - hw * 0.55, zt + hang)]
            inner = arch_xz(x - hw + 0.2, x + hw - 0.2, zt + 0.12, hang - 0.5, n=8)
            for sy in (-1, 1):
                prism(f"{prefix}Hanger{sx}{sy}", outer, sy * 0.2, 0.08, ir, plane="XZ", bevel=0.01)
                tube(f"{prefix}HangArch{sx}{sy}", [(px, sy * 0.25, pz) for px, pz in inner], 0.03, br, square=True, poly=True)
            box(f"{prefix}Ceil{sx}", (1.0, 0.9, 0.1), (x, 0, zt + hang + 0.05), ir, bevel=0.025)
            for bx in (-1, 1):
                for by in (-1, 1):
                    cyl(f"{prefix}Bolt{sx}{bx}{by}", 0.06, 0.06, (x + bx * 0.36, by * 0.32, zt + hang - 0.02), br, verts=6, bevel=0.006)


def finial(prefix, x, y, z, mat, s=1.0):
    lathe(prefix, [(0, 0), (0.07 * s, 0), (0.08 * s, 0.04 * s), (0.05 * s, 0.08 * s), (0.09 * s, 0.16 * s), (0.05 * s, 0.26 * s), (0.02 * s, 0.38 * s),
                   (0, 0.42 * s)], mat, seg=12, loc=(x, y, z))


def arch_xz(x0, x1, zs, rise, n=10):
    """A pointed arch from (x0, zs) over (mid, zs + rise) to (x1, zs), as (x, z)."""
    out = []
    for i in range(n + 1):
        t = i / n
        k = 1 - abs(t - 0.5) * 2
        out.append((x0 + (x1 - x0) * t, zs + rise * math.sin(k * PI / 2) ** 0.75))
    return out


def chain(prefix, pts, mat, r=0.06, thick=0.014):
    B30.chain(prefix, pts, mat, r=r, thick=thick)


# ================================================================== apparatus

def climbing_ropes(M):
    """Three thick hemp climbing ropes from a heavy riveted iron I-beam (bottom 19.0, top 20.3; ceiling plates at 22.4) on pierced
    lancet hangers: brass swivel shackles, long crimson leather whippings bound in brass, knotted and frayed ends 0.3 above the
    floor; the middle rope knotted for climbing, and a brass bell under the beam to ring at the top."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    ZB = 19.0
    ibeam("Beam", 9.0, ZB, K)
    for k, x in enumerate((-2.8, 0.0, 2.8)):
        box(f"Clamp{k}", (0.4, 1.05, 0.12), (x, 0, ZB - 0.06), ir, bevel=0.02)
        for sy in (-1, 1):
            cyl(f"ClampBolt{k}{sy}", 0.05, 0.2, (x, sy * 0.45, ZB - 0.02), br, verts=6, bevel=0.006)
        tube(f"Shackle{k}", [(x, -0.16, ZB - 0.1), (x, -0.18, ZB - 0.42), (x, 0, ZB - 0.58), (x, 0.18, ZB - 0.42), (x, 0.16, ZB - 0.1)], 0.05, ir)
        cyl(f"Swivel{k}", 0.12, 0.3, (x, 0, ZB - 0.75), br, verts=14, bevel=0.02)
        hoop(f"Eye{k}", (x, 0, ZB - 1.05), 0.16, "Y", br, thick=0.045)
        sway = 0.0 if k == 1 else (-0.15 if k == 0 else 0.12)
        top = ZB - 1.15
        pts = [(x, 0, top)]
        for i in range(1, 6):
            z = top - i * (top - 2.4) / 5
            pts.append((x, sway * math.sin(i / 5 * PI), z))
        rope(f"Rope{k}", pts, 0.17, K, res=3)
        cyl(f"WhipTop{k}", 0.195, 0.35, (x, 0, top - 0.1), K["leather"], verts=16, bevel=0.02)
        cyl(f"Whip{k}", 0.2, 1.1, (x, 0, 1.9), K["leather"], verts=16, bevel=0.03)
        for z in (1.4, 1.9, 2.4):
            cyl(f"WhipBand{k}{z}", 0.21, 0.07, (x, 0, z), br, verts=16, bevel=0.012)
        sphere(f"Knot{k}", 0.3, (x, 0, 1.05), K["hemp"], seg=16, rings=8, scale=(1, 1, 0.85))
        cone(f"Fray{k}", 0.22, 0.1, 0.6, (x, 0, 0.62), K["hemp"], verts=12, rot=(PI, 0, 0))
        if k == 1:
            for j, z in enumerate((4.4, 7.0, 9.6, 12.2, 14.8)):
                sphere(f"ClimbKnot{j}", 0.3, (x, 0, z), K["hemp"], seg=14, rings=8, scale=(1, 1, 0.8))
    tube("BellArm", [(0.7, 0, ZB - 0.05), (0.7, 0, ZB - 0.45), (1.1, 0, ZB - 0.55)], 0.045, ir, square=True, poly=True)
    lathe("Bell", [(0, 0.66), (0.09, 0.66), (0.17, 0.6), (0.22, 0.4), (0.29, 0.16), (0.4, 0.03), (0.41, 0.0), (0.36, 0.02), (0.24, 0.16),
                   (0.17, 0.4), (0, 0.55)], br, seg=24, loc=(1.1, 0, ZB - 1.3))
    sphere("Clapper", 0.08, (1.1, 0, ZB - 1.25), ir, seg=8, rings=4)
    tube("BellPull", [(1.1, 0, ZB - 1.3), (0.8, 0.0, ZB - 2.4), (0.25, 0.0, ZB - 3.2)], 0.02, K["cord"])
    sphere("PullTassel", 0.08, (0.25, 0, ZB - 3.25), K["leather"], seg=8, rings=4, scale=(1, 1, 1.6))
    return _dims()


def gym_rings(M):
    """Gymnastic rings: two thick turned ash rings wrapped in crimson leather, hung on broad buckled leather straps studded in brass
    from swivels under a heavy iron beam (bottom 18.0, top 19.3; ceiling plates at 21.3); the rings' bottoms at 7.4."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    ZB = 18.0
    ibeam("Beam", 4.2, ZB, K)
    for k, x in enumerate((-1.0, 1.0)):
        box(f"Clamp{k}", (0.4, 1.05, 0.12), (x, 0, ZB - 0.06), ir, bevel=0.02)
        cyl(f"Swivel{k}", 0.12, 0.32, (x, 0, ZB - 0.28), br, verts=14, bevel=0.02)
        hoop(f"Dee{k}", (x, 0, ZB - 0.58), 0.18, "X", ir, thick=0.04)
        z1, z0 = ZB - 0.7, 8.85
        box(f"Strap{k}", (0.06, 0.32, z1 - z0), (x, 0, (z0 + z1) / 2), K["satchel"], bevel=0.015)
        for sy in (-1, 1):
            box(f"Stitch{k}{sy}", (0.065, 0.015, z1 - z0 - 0.3), (x, sy * 0.13, (z0 + z1) / 2), K["bone"], bevel=0.0)
        box(f"StrapB{k}", (0.06, 0.32, 2.8), (x + 0.06, 0, 10.6), K["satchel"], bevel=0.015)
        box(f"Buckle{k}", (0.16, 0.44, 0.36), (x, 0, 12.0), br, bevel=0.03)
        box(f"BuckleIn{k}", (0.18, 0.3, 0.2), (x, 0, 12.0), K["ink"], bevel=0.015)
        for j in range(7):
            cyl(f"Stud{k}{j}", 0.055, 0.04, (x - 0.035, 0, 12.7 + j * 0.6), br, rot=(0, PI / 2, 0), verts=10, bevel=0.008)
        for z in (9.4, 10.2, 13.2, 15.6):
            box(f"Keeper{k}{z}", (0.12, 0.36, 0.14), (x, 0, z), K["satchel"], bevel=0.02)
        zc, R = 8.0, 0.6
        hoop(f"Ring{k}", (x, 0, zc), R, "X", K["oak"], thick=0.1)
        pts = [(x, R * math.sin(a), zc - R * math.cos(a)) for a in [(-75 + i * 15) * DEG for i in range(11)]]
        tube(f"Grip{k}", pts, 0.125, K["leather"], poly=True)
        for i in (0, 5, 10):
            hoop(f"GripBand{k}{i}", pts[i], 0.13, "X", br, thick=0.02)
        tube(f"Loop{k}", [(x, -0.2, zc + R + 0.35), (x, -0.16, zc + R + 0.05), (x, 0, zc + R - 0.1), (x, 0.16, zc + R + 0.05), (x, 0.2, zc + R + 0.35)],
             0.055, K["satchel"])
        box(f"LoopRivet{k}", (0.14, 0.36, 0.18), (x, 0, zc + R + 0.42), br, bevel=0.03)
    return _dims()


def wall_bars(M):
    """Wall bars, two bays: three dark oak posts with 18 ash rungs in each bay, the top rung swept forward, gothic arches of oak
    tracery over the bays with the school crest in the spandrel, iron wall brackets; 6.6 wide, 10.6 tall."""
    K = kit(M)
    ir, oak, oakdk = K["iron"], K["oak"], K["oakdk"]
    yc = -0.42
    xs = (-3.1, 0.0, 3.1)
    H = 9.2
    for i, x in enumerate(xs):
        box(f"Post{i}", (0.34, 0.3, H), (x, yc, H / 2), oakdk, bevel=0.03)
        cone(f"Cap{i}", 0.28, 0.0, 0.5, (x, yc, H + 0.25), oakdk, verts=4, rot=(0, 0, PI / 4))
        finial(f"Fin{i}", x, yc, H + 0.45, K["brassf"], s=0.9)
        for z in (0.6, 4.6, 8.6):
            box(f"Bracket{i}{z}", (0.42, 0.28, 0.08), (x, -0.14, z), ir, bevel=0.01)
            for sx in (-1, 1):
                cyl(f"BrBolt{i}{z}{sx}", 0.035, 0.03, (x + sx * 0.15, yc - 0.16, z), K["brassf"], rot=(PI / 2, 0, 0), verts=8, bevel=0.004)
        box(f"Shoe{i}", (0.42, 0.38, 0.12), (x, yc, 0.06), ir, bevel=0.015)
    for b in range(2):
        x0, x1 = xs[b] + 0.17, xs[b + 1] - 0.17
        L = x1 - x0
        for j in range(17):
            z = 0.55 + j * 0.5
            cyl(f"Rung{b}{j}", 0.065, L, ((x0 + x1) / 2, yc, z), oak, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
        # the top rung swept forward on iron arms
        cyl(f"TopRung{b}", 0.07, L, ((x0 + x1) / 2, yc - 0.6, 9.0), oak, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
        for sx, xx in ((-1, x0 + 0.04), (1, x1 - 0.04)):
            tube(f"Arm{b}{sx}", [(xx, yc, 8.75), (xx, yc - 0.35, 8.85), (xx, yc - 0.6, 9.0)], 0.035, ir, square=True)
        # the arch tracery over the bay
        pts = [(x, yc, z) for x, z in arch_xz(x0, x1, H - 0.1, 1.25)]
        tube(f"Arch{b}", pts, 0.07, oakdk, square=True, poly=True)
        pin = [(x, yc, z) for x, z in arch_xz(x0 + 0.35, x1 - 0.35, H - 0.1, 0.85)]
        tube(f"ArchIn{b}", pin, 0.04, oakdk, square=True, poly=True)
        for sx in (-1, 1):
            cx = (x0 + x1) / 2 + sx * 0.75
            _quatrefoil(f"Foil{b}{sx}", cx, yc - 0.05, H + 0.25, 0.17, K["brassf"])
        box(f"Lintel{b}", (L, 0.26, 0.14), ((x0 + x1) / 2, yc, H - 0.12), oakdk, bevel=0.02)
    pprism("Crest", "GY_School_Crest", rect(0.72, 0.8), 0.06, T(0, yc - 0.18, H + 1.25), K["gp"], "GY_black")
    box("CrestBack", (0.86, 0.06, 0.94), (0, yc - 0.12, H + 1.25), oakdk, bevel=0.02)
    return _dims()


def pommel_horse(M):
    """A pommel horse: a stitched leather body (top 3.8) with two bentwood oak pommels, brass end caps with the Crimson and Ravens
    shields, on two turned cast-iron columns with brass height wheels, over iron soles on wolf-paw feet."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    L = 5.0
    B29.cushion("Body", (L, 1.15, 0.85), (0, 0, 3.35), K["gymleather"], e=(0.3, 0.2), cuts=8, piping=K["gymleather"], pipe_r=0.025)
    top = 3.775
    for i in range(9):
        x = -L / 2 + 0.6 + i * (L - 1.2) / 8
        if abs(abs(x) - 0.75) < 0.2:
            continue
        sphere(f"Button{i}", 0.03, (x, 0, top - 0.004), K["gymleather"], seg=8, rings=4, scale=(1, 1, 0.5))
    for k, x in enumerate((-0.75, 0.75)):
        for sy in (-1, 1):
            box(f"PomFoot{k}{sy}", (0.16, 0.14, 0.1), (x, sy * 0.3, top + 0.02), br, bevel=0.02)
        tube(f"Pommel{k}", [(x, -0.3, top + 0.02), (x, -0.31, top + 0.3), (x, -0.18, top + 0.44), (x, 0.18, top + 0.44), (x, 0.31, top + 0.3),
                            (x, 0.3, top + 0.02)], 0.065, K["oak"], res=6)
    for sx, house in ((-1, "Crimson"), (1, "Ravens")):
        cyl(f"EndCap{sx}", 0.36, 0.06, (sx * (L / 2 + 0.0), 0, 3.35), br, rot=(0, PI / 2, 0), verts=24, bevel=0.015)
        crest(f"EndCrest{sx}", house, 0.5, 0.03, T(sx * (L / 2 + 0.045), 0, 3.1) @ RZ(sx * PI / 2), K)
    box("Saddle", (3.6, 0.7, 0.12), (0, 0, 2.9), ir, bevel=0.02)
    for k, x in enumerate((-1.5, 1.5)):
        lathe(f"Column{k}", [(0, 0.45), (0.24, 0.45), (0.26, 0.52), (0.18, 0.6), (0.15, 1.2), (0.2, 1.3), (0.15, 1.4), (0.13, 2.4), (0.18, 2.55),
                             (0.25, 2.75), (0.24, 2.84), (0, 2.84)], ir, seg=20)
        cyl(f"Inner{k}", 0.1, 0.5, (0, 0, 2.15), K["steel"], verts=14, bevel=0.01)
        _xform(len(P.PARTS) - 2, T(x, 0, 0))
        hoop(f"Wheel{k}", (x, 0, 1.85), 0.3, "Z", br, thick=0.025)
        for s in range(4):
            a = s * PI / 2 + PI / 4
            tube(f"Spoke{k}{s}", [(x, 0, 1.85), (x + math.cos(a) * 0.3, math.sin(a) * 0.3, 1.85)], 0.015, br, poly=True)
        box(f"Sole{k}", (0.3, 2.2, 0.18), (x, 0, 0.36), ir, bevel=0.03)
        for sy in (-1, 1):
            sphere(f"Paw{k}{sy}", 0.17, (x, sy * 1.12, 0.17), ir, seg=12, rings=6, scale=(1.1, 1.3, 1))
            for t in (-1, 0, 1):
                sphere(f"Toe{k}{sy}{t}", 0.07, (x + t * 0.1, sy * 1.3, 0.07), ir, seg=8, rings=4)
            tube(f"Gusset{k}{sy}", [(x, sy * 0.9, 0.45), (x, sy * 0.25, 1.05)], 0.035, ir, square=True, poly=True)
    box("Stretcher", (3.0, 0.16, 0.14), (0, 0, 0.5), ir, bevel=0.02)
    return _dims()


def parallel_bars(M):
    """Parallel bars: two oval oak rails (tops 4.3), 8.4 long, on iron uprights with brass collars and T-screws, cast-iron soles
    braced with pierced gothic gussets, a long stretcher and castors."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    for sy in (-1, 1):
        y = sy * 0.85
        box(f"Rail{sy}", (8.4, 0.17, 0.24), (0, y, 4.18), K["oak"], bevel=0.07, segments=3)
        for sx in (-1, 1):
            cyl(f"RailCap{sx}{sy}", 0.09, 0.08, (sx * 4.22, y, 4.18), br, rot=(0, PI / 2, 0), verts=12, bevel=0.02)
            x = sx * 2.7
            cyl(f"Upright{sx}{sy}", 0.09, 3.1, (x, y, 2.05), ir, verts=14, bevel=0.01)
            cyl(f"Slide{sx}{sy}", 0.06, 0.5, (x, y, 3.8), K["steel"], verts=12, bevel=0.005)
            cyl(f"Collar{sx}{sy}", 0.12, 0.16, (x, y, 3.58), br, verts=14, bevel=0.015)
            cyl(f"Screw{sx}{sy}", 0.025, 0.25, (x, y - sy * 0.2, 3.58), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.003)
            cyl(f"ScrewT{sx}{sy}", 0.025, 0.2, (x, y - sy * 0.33, 3.58), br, rot=(0, PI / 2, 0), verts=8, bevel=0.003)
            box(f"Cup{sx}{sy}", (0.22, 0.22, 0.14), (x, y, 4.02), ir, bevel=0.02)
    for sx in (-1, 1):
        x = sx * 2.7
        box(f"Sole{sx}", (0.36, 2.7, 0.22), (x, 0, 0.36), ir, bevel=0.03)
        for sy in (-1, 1):
            castor(f"Castor{sx}{sy}", x, sy * 1.15, 0.25, K)
        for sy in (-1, 1):
            prism(f"Gusset{sx}{sy}", [(sy * 1.3, 0.47), (sy * 0.95, 0.47), (sy * 0.95, 1.6)], x, 0.05, ir, plane="YZ", bevel=0.005)
        # pierced gothic panel between the two uprights
        box(f"Tie{sx}", (0.08, 1.7, 0.12), (x, 0, 1.8), ir, bevel=0.01)
        s = _mark()
        _quatrefoil(f"Foil{sx}", 0, 0, 0, 0.3, ir)
        _xform(s, T(x, 0, 1.2) @ RZ(PI / 2))
    box("Stretcher", (5.4, 0.18, 0.18), (0, 0, 0.42), ir, bevel=0.02)
    for sx in (-1, 1):
        tube(f"Brace{sx}", [(sx * 2.6, 0, 0.55), (sx * 1.6, 0, 0.5), (sx * 0.9, 0, 0.47)], 0.04, ir)
    box("MakerPlate", (0.8, 0.03, 0.12), (0, -0.105, 0.42), br, bevel=0.01)
    return _dims()


def balance_beam(M):
    """The house beam: an 11-long suede-topped oak balance beam (top 4.0) whose ends are carved as raven heads, the five house
    shields set along its front under a brass distance rule, on two pierced cast-iron A-trestles with raven-wing brackets, a tie
    rod between them."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    L = 11.0
    box("Core", (L, 0.36, 0.4), (0, 0, 3.7), K["oakdk"], bevel=0.035)
    box("Suede", (L + 0.02, 0.4, 0.12), (0, 0, 3.94), K["suede"], bevel=0.045, segments=3)
    for sy in (-1, 1):
        box(f"Rule{sy}", (L - 0.4, 0.02, 0.05), (0, sy * 0.185, 3.82), br, bevel=0.0)
    for i in range(23):
        x = -L / 2 + 0.5 + i * (L - 1.0) / 22
        h = 0.14 if i % 2 == 0 else 0.07
        box(f"Mark{i}", (0.025, 0.02, h), (x, -0.19, 3.78 - h / 2), br, bevel=0.0)
    for i, h in enumerate(HOUSES):
        crest(f"Crest{h}", h, 0.3, 0.03, T(-4.0 + i * 2.0, -0.195, 3.5), K)
    for sx in (-1, 1):
        x = sx * (L / 2 + 0.25)
        box(f"Neck{sx}", (0.4, 0.34, 0.38), (sx * (L / 2 + 0.05), 0, 3.72), K["ebony"], bevel=0.08, segments=3)
        sphere(f"Head{sx}", 0.3, (x, 0, 3.85), K["ebony"], seg=16, rings=10, scale=(1.3, 0.75, 0.9))
        cone(f"Beak{sx}", 0.13, 0.0, 0.6, (x + sx * 0.6, 0, 3.8), K["ebony"], verts=10, rot=(0, sx * PI / 2, 0))
        for sy in (-1, 1):
            sphere(f"Eye{sx}{sy}", 0.045, (x + sx * 0.12, sy * 0.21, 3.93), K["gilt"], seg=8, rings=4)
            prism(f"Ruff{sx}{sy}", [(x - sx * 0.45, 3.5), (x - sx * 0.05, 3.55), (x + sx * 0.05, 3.62), (x - sx * 0.2, 3.9), (x - sx * 0.5, 3.88)],
                  sy * 0.17, 0.04, K["ebony"], plane="XZ", bevel=0.005)
    for sx in (-1, 1):
        x = sx * 3.9
        box(f"Cradle{sx}", (0.7, 0.62, 0.16), (x, 0, 3.42), ir, bevel=0.03)
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(x, sy * 0.3, 3.36), (x, sy * 1.25, 0.08)], 0.09, ir, square=True, poly=True)
            box(f"Foot{sx}{sy}", (0.5, 0.4, 0.14), (x, sy * 1.25, 0.07), K["rubber"], bevel=0.04)
        tube(f"Lancet{sx}", [(x, y, z) for y, z in arch_xz(-0.95, 0.95, 0.5, 2.3, n=12)], 0.05, ir, square=True, poly=True)
        tube(f"LancetIn{sx}", [(x, y, z) for y, z in arch_xz(-0.6, 0.6, 0.9, 1.6, n=10)], 0.03, br, square=True, poly=True)
        box(f"Sill{sx}", (0.1, 2.0, 0.1), (x, 0, 0.5), ir, bevel=0.01)
        s = _mark()
        _quatrefoil(f"TFoil{sx}", 0, 0, 0, 0.26, br)
        _xform(s, T(x, 0, 1.75) @ RZ(PI / 2))
        for d in (-1, 1):
            fe = []
            n = 6
            for i in range(n + 1):
                t = i / n
                fe.append((d * (0.3 + 1.5 * t), 3.38 - 0.6 * (1 - t) ** 1.6 - 0.12 * (i % 2)))
            poly = [(d * 0.25, 3.42), (d * 1.8, 3.42)] + list(reversed(fe))
            poly = [(x + u, w) for u, w in poly]
            if d < 0:
                poly = list(reversed(poly))
            for sy in (-1, 1):
                prism(f"Wing{sx}{d}{sy}", poly, sy * 0.15, 0.05, ir, plane="XZ", bevel=0.005)
    tube("TieRod", [(-3.9, 0, 0.9), (3.9, 0, 0.9)], 0.05, ir, poly=True)
    for sx in (-1, 1):
        cyl(f"TieNut{sx}", 0.09, 0.1, (sx * 3.75, 0, 0.9), br, rot=(0, PI / 2, 0), verts=6, bevel=0.006)
    return _dims()


def _frustum(name, Lb, Wb, Lt, Wt, z0, z1, mat, bev=0.03):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        top = v.co.z > 0
        L, W = (Lt, Wt) if top else (Lb, Wb)
        v.co = Vector((v.co.x * L, v.co.y * W, z1 if top else z0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, bev)


def vaulting_box(M):
    """A five-tier vaulting box, 5.0 x 2.6 at the foot, a buttoned leather top at 4.05: each oak tier banded in a house colour
    and numbered I to V in gilt, oval hand slots, iron corner plates, castor levers at the ends."""
    K = kit(M)
    ir = K["iron"]
    th = 0.72
    for i in range(5):
        z0 = i * th
        Lb, Wb = 5.0 - i * 0.16, 2.6 - i * 0.22
        Lt, Wt = 5.0 - (i + 1) * 0.16, 2.6 - (i + 1) * 0.22
        _frustum(f"Tier{i}", Lb, Wb, Lt, Wt, z0, z0 + th - 0.02, K["oak"] if i % 2 else K["oakdk"], bev=0.03)
        ang = math.atan(0.11 / th)
        yf = -(Wb + Wt) / 4
        house = HOUSES[i]
        box(f"Band{i}", ((Lb + Lt) / 2 - 0.1, 0.03, 0.09), (0, yf - 0.02, z0 + th - 0.12), K[f"j_{house}"], bevel=0.01, rot=(-ang, 0, 0))
        if 1 <= i <= 3:
            for sx in (-1, 1):
                box(f"Slot{i}{sx}", (0.85, 0.05, 0.2), (sx * 1.2, yf, z0 + th * 0.45), K["ink"], bevel=0.09, rot=(-ang, 0, 0))
        num = ("I", "II", "III", "IV", "V")[i]
        _text(f"Num{i}", num, FONT, K["gilt"], lambda x, y, h, z0=z0, yf=yf: (x, yf - 0.012 - h, z0 + th * 0.45 + y), fit=(0.5, 0.3), depth=0.012)
        for sx in (-1, 1):
            for sy in (-1, 1):
                xx, yy = sx * ((Lb + Lt) / 4 - 0.05), sy * ((Wb + Wt) / 4 - 0.05)
                box(f"Corner{i}{sx}{sy}", (0.22, 0.22, th * 0.5), (xx, yy, z0 + th * 0.5), ir, bevel=0.01)
    top0 = 5 * th
    B29.cushion("Top", (5.0 - 5 * 0.16 + 0.08, 2.6 - 5 * 0.22 + 0.08, 0.5), (0, 0, top0 + 0.22), K["gymleather"], e=(0.35, 0.2), cuts=6,
                piping=K["gymleather"], pipe_r=0.022)
    for i in range(5):
        sphere(f"Btn{i}", 0.03, (-1.6 + i * 0.8, 0, top0 + 0.465), K["gymleather"], seg=8, rings=4, scale=(1, 1, 0.5))
    for sx in (-1, 1):
        x = sx * 2.55
        box(f"LeverPlate{sx}", (0.1, 0.5, 0.3), (x, 0, 0.3), ir, bevel=0.02)
        tube(f"Lever{sx}", [(x + sx * 0.05, 0, 0.35), (x + sx * 0.35, 0, 0.55), (x + sx * 0.5, 0, 1.0)], 0.035, ir)
        sphere(f"LeverKnob{sx}", 0.07, (x + sx * 0.5, 0, 1.02), K["brassf"], seg=10, rings=6)
        for sy in (-1, 1):
            cyl(f"Wheel{sx}{sy}", 0.12, 0.08, (x + sx * 0.08, sy * 0.38, 0.12), K["rubber"], rot=(PI / 2, 0, 0), verts=14, bevel=0.015)
    return _dims()


def springboard(M):
    """A springboard: a curved oak board covered in ribbed crimson felt, rising from 0.25 at the front to 1.05, on four iron coil
    springs and an oak sledge; a brass maker's plate on its nose."""
    K = kit(M)
    ir = K["iron"]
    L = 3.7
    n = 10
    for i in range(n):
        y0 = -L / 2 + i * L / n
        y1 = y0 + L / n
        z = lambda y: 0.25 + 0.8 * ((y + L / 2) / L) ** 1.3
        ang = math.atan2(z(y1) - z(y0), y1 - y0)
        ym = (y0 + y1) / 2
        box(f"Board{i}", (2.0, L / n + 0.02, 0.12), (0, ym, z(ym)), K["oak"], bevel=0.0, rot=(ang, 0, 0))
        box(f"Felt{i}", (1.9, L / n + 0.02, 0.03), (0, ym - math.sin(ang) * 0.075, z(ym) + math.cos(ang) * 0.075), K["feltc"], bevel=0.0, rot=(ang, 0, 0))
        if i % 2 == 0 and i < n - 1:
            box(f"Rib{i}", (1.8, 0.05, 0.03), (0, y1 - math.sin(ang) * 0.1, z(y1) + 0.1), K["rubber"], bevel=0.01, rot=(ang, 0, 0))
    for sx in (-1, 1):
        box(f"Runner{sx}", (0.16, L - 0.1, 0.16), (sx * 0.85, 0.05, 0.08), K["oakdk"], bevel=0.03)
    box("BackBlock", (1.86, 0.2, 0.2), (0, L / 2 - 0.2, 0.18), K["oakdk"], bevel=0.03)
    box("FrontBlock", (1.86, 0.18, 0.12), (0, -L / 2 + 0.25, 0.14), K["oakdk"], bevel=0.03)
    for sx in (-1, 1):
        for y in (0.2, 1.2):
            ztop = 0.25 + 0.8 * ((y + L / 2) / L) ** 1.3 - 0.07
            pts = []
            turns = 5
            for i in range(turns * 12 + 1):
                a = i / 12 * 2 * PI
                pts.append((sx * 0.6 + math.cos(a) * 0.16, y + math.sin(a) * 0.16, 0.17 + (ztop - 0.17) * i / (turns * 12)))
            tube(f"Coil{sx}{y}", pts, 0.022, ir, poly=True)
            cyl(f"Seat{sx}{y}", 0.2, 0.03, (sx * 0.6, y, 0.165), ir, verts=14, bevel=0.005)
    box("Nose", (1.9, 0.04, 0.16), (0, -L / 2 - 0.0, 0.22), K["brassf"], bevel=0.015)
    label("Maker", "THORNE PATENT", K["ink"], 0, -L / 2 - 0.02, 0.22, 1.2, 0.09, depth=0.006)
    return _dims()


def high_jump_stands(M):
    """A pair of high-jump stands 8 apart: stout square iron posts on heavy cast-iron bases weighted with stacked iron discs, brass
    height scales, sliding brass peg carriers with thumb screws, finials, and a thick ash crossbar banded crimson and oak resting on
    the pegs at 4.3."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    zb = 4.3
    for sx in (-1, 1):
        x = sx * 4.0
        cyl(f"Base{sx}", 0.85, 0.22, (x, 0, 0.11), ir, verts=8, bevel=0.03)
        for k, r in enumerate((0.7, 0.62, 0.54)):
            cyl(f"Disc{sx}{k}", r, 0.13, (x, 0, 0.29 + k * 0.14), ir, verts=24, bevel=0.02)
            box(f"DiscTag{sx}{k}", (0.16, 0.02, 0.07), (x, -r - 0.005, 0.29 + k * 0.14), br, bevel=0.0)
        cyl(f"Collar{sx}", 0.24, 0.2, (x, 0, 0.78), br, verts=16, bevel=0.02)
        box(f"Post{sx}", (0.22, 0.22, 6.5), (x, 0, 3.95), ir, bevel=0.02)
        for k in range(4):
            a = k * PI / 2 + PI / 4
            tube(f"Gusset{sx}{k}", [(x + math.cos(a) * 0.62, math.sin(a) * 0.62, 0.72), (x + math.cos(a) * 0.12, math.sin(a) * 0.12, 1.6)], 0.035, ir,
                 square=True, poly=True)
        lathe(f"Fin{sx}", [(0, 0), (0.15, 0), (0.12, 0.08), (0.22, 0.25), (0.12, 0.42), (0, 0.45)], br, seg=16, loc=(x, 0, 7.2))
        box(f"Scale{sx}", (0.16, 0.02, 5.6), (x, -0.12, 4.0), br, bevel=0.004)
        for i in range(29):
            z = 1.2 + i * 0.2
            w = 0.14 if i % 5 == 0 else 0.07
            box(f"Tick{sx}{i}", (w, 0.012, 0.018), (x, -0.135, z), K["ink"], bevel=0.0)
        box(f"Carrier{sx}", (0.36, 0.36, 0.4), (x, 0, zb - 0.08), br, bevel=0.04)
        cyl(f"Thumb{sx}", 0.04, 0.26, (x, -0.28, zb - 0.08), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.005)
        sphere(f"ThumbKnob{sx}", 0.08, (x, -0.43, zb - 0.08), br, seg=10, rings=6)
        cyl(f"Peg{sx}", 0.05, 0.45, (x - sx * 0.4, 0, zb - 0.12), ir, rot=(0, PI / 2, 0), verts=10, bevel=0.005)
    cyl("Bar", 0.09, 7.5, (0, 0, zb), K["oak"], rot=(0, PI / 2, 0), verts=14, bevel=0.0)
    for i in range(-7, 8):
        if i % 2 == 0:
            cyl(f"Band{i}", 0.095, 0.5, (i * 0.5, 0, zb), K["enamel"], rot=(0, PI / 2, 0), verts=14, bevel=0.0)
    for sx in (-1, 1):
        cyl(f"BarCap{sx}", 0.1, 0.08, (sx * 3.75, 0, zb), br, rot=(0, PI / 2, 0), verts=14, bevel=0.015)
    return _dims()


def mat_trolley(M):
    """A mat trolley: an iron cradle on castors with pointed-arch ends and a push bar, carrying three rolled leather mats (two
    crimson, one ink) bound with buckled straps, their spiral ends showing."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    W, D = 4.4, 2.2
    zf = 0.5
    for sy in (-1, 1):
        box(f"Side{sy}", (W, 0.1, 0.1), (0, sy * D / 2, zf), ir, bevel=0.015)
    for sx in (-1, 1):
        box(f"End{sx}", (0.1, D, 0.1), (sx * W / 2, 0, zf), ir, bevel=0.015)
        for sy in (-1, 1):
            castor(f"C{sx}{sy}", sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), zf - 0.05, K)
        pts = [(sx * W / 2, y, z) for y, z in arch_xz(-D / 2, D / 2, zf, 2.6)]
        tube(f"Arch{sx}", pts, 0.05, ir, square=True, poly=True)
        tube(f"ArchIn{sx}", [(sx * W / 2, y, z) for y, z in arch_xz(-D / 2 + 0.35, D / 2 - 0.35, zf, 1.9)], 0.03, ir, square=True, poly=True)
        finial(f"Fin{sx}", sx * W / 2, 0, zf + 2.6, br, s=0.8)
    for k in range(5):
        x = -W / 2 + 0.6 + k * (W - 1.2) / 4
        tube(f"Slat{k}", [(x, -D / 2, zf), (x, -0.4, zf - 0.08), (x, 0.4, zf - 0.08), (x, D / 2, zf)], 0.035, ir, poly=True)
    # the push bar at +X
    for sy in (-1, 1):
        tube(f"Handle{sy}", [(W / 2, sy * 0.8, zf), (W / 2 + 0.5, sy * 0.8, 2.6), (W / 2 + 0.55, sy * 0.8, 3.1)], 0.04, ir)
    cyl("Grip", 0.07, 1.8, (W / 2 + 0.55, 0, 3.1), K["oak"], rot=(PI / 2, 0, 0), verts=12, bevel=0.02)
    R = 0.5
    Lm = 3.6
    rolls = ((-0.52, zf + 0.06 + R, K["leather"]), (0.52, zf + 0.06 + R, K["inkleather"]), (0.0, zf + 0.06 + R + 0.88, K["leather"]))
    for k, (y, z, mat) in enumerate(rolls):
        cyl(f"Roll{k}", R, Lm, (0, y, z), mat, rot=(0, PI / 2, 0), verts=28, bevel=0.03)
        for sx in (-1, 1):
            pts = []
            for i in range(3 * 20 + 1):
                a = i / 20 * 2 * PI
                r = 0.05 + (R - 0.07) * i / 60
                pts.append((sx * (Lm / 2 + 0.005), y + math.cos(a) * r, z + math.sin(a) * r))
            tube(f"Spiral{k}{sx}", pts, 0.012, K["ink"], poly=True)
            hoop(f"Strap{k}{sx}", (sx * 1.0, y, z), R + 0.015, "X", K["satchel"], thick=0.025)
            box(f"Buckle{k}{sx}", (0.08, 0.14, 0.12), (sx * 1.0, y - 0.1, z - R - 0.01), br, bevel=0.015)
    return _dims()


# ================================================================== fitness

def medicine_ball_rack(M):
    """A three-tier oak rack of seven stitched leather medicine balls on paired rails, stepped side cheeks with a pointed back
    board carrying the Wardens' shield and a brass WEIGHTS plate."""
    K = kit(M)
    oak, oakdk, br = K["oak"], K["oakdk"], K["brassf"]
    W = 4.4
    tiers = ((-0.75, 0.55), (0.0, 1.45), (0.75, 2.35))
    prof = [(-1.15, 0), (1.15, 0), (1.15, 2.6), (0.4, 2.6), (0.4, 1.7), (-0.35, 1.7), (-0.35, 0.8), (-1.15, 0.8)]
    for sx in (-1, 1):
        prism(f"Cheek{sx}", [(y, z) for y, z in prof], sx * W / 2, 0.14, oakdk, plane="YZ", bevel=0.02)
    for k, (y, z) in enumerate(tiers):
        for d in (-1, 1):
            cyl(f"Rail{k}{d}", 0.06, W, (0, y + d * 0.24, z), oak, rot=(0, PI / 2, 0), verts=12, bevel=0.0)
    back = [(-W / 2, 2.4), (W / 2, 2.4), (W / 2, 3.6)] + [(x, z) for x, z in arch_xz(W / 2, -W / 2, 3.6, 0.9)][1:-1] + [(-W / 2, 3.6)]
    prism("Back", back, 1.1, 0.1, oakdk, plane="XZ", bevel=0.015)
    crest("Crest", "Wardens", 0.75, 0.05, T(0, 1.03, 3.35), K)
    box("WeightPlate", (1.2, 0.03, 0.22), (0, -1.17, 0.4), br, bevel=0.01)
    label("WeightText", "WEIGHTS", K["ink"], 0, -1.185, 0.4, 0.9, 0.13, depth=0.006)
    mats = [K["gymleather"], K["satchel"], K["leather"], K["inkleather"], K["gymleather"], K["satchel"], K["leather"]]
    spots = [(-1.3, 0), (0.0, 0), (1.3, 0), (-0.75, 1), (0.75, 1), (-1.2, 2), (0.6, 2)]
    g = random.Random(4304)
    for i, ((x, t), mat) in enumerate(zip(spots, mats)):
        y, z = tiers[t]
        r = 0.42 - t * 0.04
        cz = z + math.sqrt(max(0.0, (r + 0.06) ** 2 - 0.24 ** 2))
        s = _mark()
        sphere(f"Ball{i}", r, (0, 0, 0), mat, seg=22, rings=12)
        hoop(f"SeamA{i}", (0, 0, 0), r + 0.004, "X", K["cord"], thick=0.012)
        hoop(f"SeamB{i}", (0, 0, 0), r + 0.004, "Y", K["cord"], thick=0.012)
        cyl(f"Tag{i}", 0.08, 0.02, (0, -r - 0.005, 0.12), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.005)
        _xform(s, T(x, y, cz) @ RZ(g.uniform(-0.5, 0.5)) @ RX(g.uniform(-0.3, 0.3)))
    return _dims()


def _club(prefix, mtx, K, band):
    s = _mark()
    lathe(prefix, [(0, 0), (0.07, 0), (0.08, 0.04), (0.05, 0.09), (0.042, 0.18), (0.045, 0.45), (0.065, 0.75), (0.13, 1.1), (0.175, 1.38),
                   (0.18, 1.5), (0.165, 1.66), (0.12, 1.84), (0.06, 1.93), (0, 1.95)], K["ebony"], seg=18)
    cyl(f"{prefix}Band", 0.163, 0.12, (0, 0, 1.25), band, verts=18, bevel=0.0)
    cyl(f"{prefix}Gilt1", 0.172, 0.025, (0, 0, 1.17), K["gilt"], verts=18, bevel=0.0)
    cyl(f"{prefix}Gilt2", 0.181, 0.025, (0, 0, 1.33), K["gilt"], verts=18, bevel=0.0)
    _xform(s, mtx)


def indian_club_rack(M):
    """A wall rack of Indian clubs: a pointed oak board with the Athletes' VARSITY pennant, three crossed pairs of ebonised clubs
    in house-coloured bands on brass pegs, and a shelf of chalk; 3.6 wide, 5.3 tall."""
    K = kit(M)
    oakdk, br = K["oakdk"], K["brassf"]
    W, H = 3.6, 4.5
    board = [(-W / 2, 0), (W / 2, 0), (W / 2, H)] + [(x, z) for x, z in arch_xz(W / 2, -W / 2, H, 0.8)][1:-1] + [(-W / 2, H)]
    prism("Board", board, -0.06, 0.12, oakdk, plane="XZ", bevel=0.02)
    frame = [(x, -0.14, z) for x, z in [(-W / 2 + 0.08, 0.08), (W / 2 - 0.08, 0.08), (W / 2 - 0.08, H)]]
    frame += [(x, -0.14, z) for x, z in arch_xz(W / 2 - 0.08, -W / 2 + 0.08, H, 0.72)][1:]
    frame += [(-W / 2 + 0.08, -0.14, 0.08)]
    tube("Frame", frame, 0.04, K["oak"], square=True, poly=True)
    plate("Pennant", "GY_Pennant", 2.2, 0.82, 0.04, T(0, -0.14, H - 0.05), K)
    bands = (K["enamel"], K["j_Ravens"], K["j_Rovers"])
    for p, x in enumerate((-1.05, 0.0, 1.05)):
        zc = 2.2
        for d in (-1, 1):
            _club(f"Club{p}{d}", T(x, -0.32 - 0.12 * (d + 1), zc) @ RY(d * 24 * DEG) @ T(0, 0, -1.0), K, bands[p])
        cyl(f"Peg{p}", 0.04, 0.3, (x, -0.27, zc - 0.85), br, rot=(PI / 2, 0, 0), verts=10, bevel=0.006)
        cyl(f"PegTop{p}", 0.04, 0.3, (x, -0.27, zc + 0.75), br, rot=(PI / 2, 0, 0), verts=10, bevel=0.006)
    box("Shelf", (W - 0.3, 0.45, 0.08), (0, -0.3, 0.32), K["oak"], bevel=0.015)
    for sx in (-1, 1):
        prism(f"ShelfBr{sx}", [(-0.02, 0.28), (-0.5, 0.28), (-0.02, 0.0)], sx * 1.4, 0.06, K["iron"], plane="YZ", bevel=0.004)
    for i in range(4):
        cyl(f"Chalk{i}", 0.04, 0.32, (-1.0 + i * 0.18, -0.33, 0.4), K["chalk"], rot=(0, PI / 2, i * 0.3), verts=8, bevel=0.01)
    box("ChalkBlock", (0.4, 0.28, 0.2), (0.9, -0.32, 0.46), K["chalk"], bevel=0.04)
    return _dims()


def rowing_machine(M):
    """A Victorian rowing machine: an oak monorail on iron feet, a crimson leather sliding seat on brass rails, a raked foot
    stretcher with straps, two iron oar levers on outriggers working brass dashpots, oak handles, and a stroke counter dial."""
    K = kit(M)
    ir, br, oak = K["iron"], K["brassf"], K["oak"]
    L = 7.4
    box("Rail", (L, 0.5, 0.22), (0, 0, 0.62), oak, bevel=0.04)
    for sy in (-1, 1):
        cyl(f"Track{sy}", 0.03, L - 0.6, (0.4, sy * 0.17, 0.76), br, rot=(0, PI / 2, 0), verts=8, bevel=0.0)
    for sx in (-1, 1):
        x = sx * (L / 2 - 0.3)
        box(f"Foot{sx}", (0.3, 1.6, 0.14), (x, 0, 0.07), ir, bevel=0.02)
        prism(f"Leg{sx}", [(-0.5, 0.14), (0.5, 0.14), (0.15, 0.52), (-0.15, 0.52)], x, 0.1, ir, plane="YZ", bevel=0.01)
    # the seat
    box("SeatBase", (0.9, 0.7, 0.1), (0.8, 0, 0.86), oak, bevel=0.02)
    B29.cushion("Seat", (0.9, 0.75, 0.2), (0.8, 0, 1.0), K["leather"], e=(0.3, 0.25), cuts=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Roller{sx}{sy}", 0.05, 0.06, (0.8 + sx * 0.3, sy * 0.17, 0.82), br, rot=(PI / 2, 0, 0), verts=10, bevel=0.005)
    # foot stretcher
    xs = -2.6
    box("Stretcher", (0.08, 1.2, 0.9), (xs, 0, 1.15), oak, bevel=0.02, rot=(0, -30 * DEG, 0))
    for sy in (-1, 1):
        box(f"Shoe{sy}", (0.5, 0.36, 0.14), (xs + 0.18, sy * 0.3, 1.05), K["satchel"], bevel=0.05, rot=(0, -30 * DEG, 0))
        box(f"Heel{sy}", (0.1, 0.36, 0.2), (xs - 0.12, sy * 0.3, 0.84), K["satchel"], bevel=0.03)
    for sy in (-1, 1):
        tube(f"Strut{sy}", [(xs - 0.3, sy * 0.25, 0.73), (xs - 0.05, sy * 0.4, 1.45)], 0.03, ir, poly=True)
    # outriggers, levers and dashpots
    xp = -1.6
    tube("Outrigger", [(xp, -1.5, 0.72), (xp, 1.5, 0.72)], 0.05, ir, square=True, poly=True)
    for sy in (-1, 1):
        y = sy * 1.5
        cyl(f"Pivot{sy}", 0.1, 0.18, (xp, y, 0.8), br, verts=12, bevel=0.01)
        tube(f"Lever{sy}", [(xp, y, 0.85), (xp + 0.35, y * 0.93, 1.7), (xp + 0.75, y * 0.82, 2.45)], 0.045, ir)
        cyl(f"Handle{sy}", 0.065, 0.55, (xp + 0.75, y * 0.82 - sy * 0.25, 2.45), oak, rot=(PI / 2, 0, 0), verts=12, bevel=0.02)
        cyl(f"HandleCap{sy}", 0.075, 0.05, (xp + 0.75, y * 0.82 - sy * 0.53, 2.45), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.01)
        # the dashpot from the outrigger's foot to the lever
        p0, p1 = Vector((xp - 0.9, y, 0.2)), Vector((xp + 0.18, y * 0.96, 1.3))
        d = p1 - p0
        mid = p0 + d * 0.35
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
        cyl(f"Pot{sy}", 0.11, d.length * 0.6, tuple(mid), br, rot=tuple(rot), verts=14, bevel=0.015)
        cyl(f"Piston{sy}", 0.03, d.length * 0.5, tuple(p0 + d * 0.78), K["steel"], rot=tuple(rot), verts=8, bevel=0.0)
        box(f"PotBase{sy}", (0.3, 0.3, 0.1), (xp - 0.9, y, 0.15), ir, bevel=0.02)
        tube(f"PotArm{sy}", [(xp - 0.9, y, 0.15), (xp - 0.2, y * 0.6, 0.6), (xp, y * 0.3, 0.72)], 0.035, ir, poly=True)
    # the stroke counter on the rail's front
    cyl("CounterCase", 0.24, 0.1, (-0.6, -0.3, 0.62), br, rot=(PI / 2, 0, 0), verts=20, bevel=0.015)
    pprism("CounterDial", "GY_Dial", circ(0.2, 24), 0.02, T(-0.6, -0.36, 0.0), K["gp"], "GY_enamel")
    box("CounterHand", (0.012, 0.01, 0.16), (-0.6, -0.375, 0.68), K["ink"], bevel=0.0, rot=(0, 0.6, 0))
    return _dims()


def wall_pulley(M):
    """A wall pulley machine: a cast-iron cabinet like a lancet window, 2.4 wide and 8.6 tall, the iron weight stack on guide rods
    behind a grille of bars, a brass pulley wheel at the top, the hemp cord down to two oak handles; the Wardens' shield on the
    hood."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    W, D = 2.4, 0.9
    yf = -D
    box("Back", (W, 0.08, 7.4), (0, -0.04, 3.7), ir, bevel=0.01)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.12, D, 7.4), (sx * (W / 2 - 0.06), -D / 2, 3.7), ir, bevel=0.015)
        box(f"Stile{sx}", (0.28, 0.1, 7.4), (sx * (W / 2 - 0.14), yf, 3.7), ir, bevel=0.02)
        cone(f"Pin{sx}", 0.14, 0.0, 0.9, (sx * (W / 2 - 0.14), yf + 0.1, 8.0), ir, verts=4, rot=(0, 0, PI / 4))
        box(f"Plinth{sx}", (0.36, D + 0.15, 0.4), (sx * (W / 2 - 0.12), -D / 2 - 0.05, 0.2), ir, bevel=0.03)
    hood = [(-W / 2, 7.3), (W / 2, 7.3)] + [(x, z) for x, z in arch_xz(W / 2, -W / 2, 7.3, 1.3)][1:-1]
    prism("Hood", hood, yf, 0.12, ir, plane="XZ", bevel=0.015)
    prism("HoodBack", hood, -0.45, 0.8, ir, plane="XZ", bevel=0.01)
    crest("Crest", "Wardens", 0.85, 0.05, T(0, yf - 0.08, 7.35), K)
    box("Base", (W, D, 0.3), (0, -D / 2, 0.15), ir, bevel=0.02)
    box("Head", (W, D, 0.25), (0, -D / 2, 7.2), ir, bevel=0.02)
    # weight stack and guide rods
    for sx in (-1, 1):
        cyl(f"Rod{sx}", 0.035, 6.8, (sx * 0.45, -0.45, 3.7), K["steel"], verts=10, bevel=0.0)
    for i in range(12):
        box(f"Weight{i}", (1.1, 0.55, 0.17), (0, -0.45, 0.4 + i * 0.19), ir, bevel=0.02)
        box(f"WLabel{i}", (0.25, 0.02, 0.08), (0, -0.735, 0.4 + i * 0.19), br, bevel=0.005)
    box("TopPlate", (1.0, 0.5, 0.1), (0, -0.45, 2.75), K["steel"], bevel=0.02)
    cyl("Stem", 0.03, 4.0, (0, -0.45, 4.8), K["steel"], verts=8, bevel=0.0)
    # the grille: a lancet of bars
    for i in range(9):
        x = -0.72 + i * 0.18
        tube(f"Bar{i}", [(x, yf - 0.02, 0.35), (x, yf - 0.02, 6.4 + 0.5 * math.cos(x / 0.8 * PI / 2))], 0.022, ir, poly=True)
    for z in (1.9, 4.2):
        tube(f"Rail{z}", [(-0.85, yf - 0.03, z), (0.85, yf - 0.03, z)], 0.03, ir, square=True, poly=True)
    tube("GrilleArch", [(x, yf - 0.03, z) for x, z in arch_xz(-0.85, 0.85, 6.1, 0.9)], 0.035, ir, square=True, poly=True)
    # the pulley, cord and handles
    cyl("Pulley", 0.32, 0.12, (0, yf - 0.25, 6.8), br, rot=(PI / 2, 0, 0), verts=24, bevel=0.02)
    cyl("Axle", 0.06, 0.4, (0, yf - 0.1, 6.8), K["steel"], rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
    box("PulleyFork", (0.08, 0.35, 0.5), (0.36, yf - 0.15, 6.8), ir, bevel=0.015)
    box("PulleyFork2", (0.08, 0.35, 0.5), (-0.36, yf - 0.15, 6.8), ir, bevel=0.015)
    rope("Cord", [(0.3, yf - 0.25, 6.8), (0.33, yf - 0.3, 5.0), (0.36, yf - 0.32, 3.5)], 0.03, K)
    rope("Cord2", [(0.36, yf - 0.32, 3.5), (0.0, yf - 0.32, 3.25), (-0.6, yf - 0.3, 3.0)], 0.025, K)
    rope("Cord3", [(0.36, yf - 0.32, 3.5), (0.62, yf - 0.32, 3.2), (0.8, yf - 0.3, 2.9)], 0.025, K)
    for k, x in enumerate((-0.6, 0.8)):
        hoop(f"HRing{k}", (x, yf - 0.3, 2.9), 0.06, "Y", br, thick=0.015)
        cyl(f"HGrip{k}", 0.06, 0.45, (x, yf - 0.3, 2.62), K["oak"], rot=(0, PI / 2, 0), verts=12, bevel=0.02)
        for sx in (-1, 1):
            tube(f"HYoke{k}{sx}", [(x, yf - 0.3, 2.84), (x + sx * 0.25, yf - 0.3, 2.62)], 0.015, br, poly=True)
    return _dims()


def punching_bag(M):
    """A heavy leather punching bag on a chain from a scrolled iron wall bracket (arm at 10.2, 3 out from the wall): laced seam,
    crimson bands, an iron top ring on four short chains, bottom at 3.4."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    box("WallPlate", (0.9, 0.1, 2.8), (0, -0.05, 9.2), ir, bevel=0.02)
    for z in (8.0, 10.4):
        for sx in (-1, 1):
            cyl(f"Bolt{z}{sx}", 0.06, 0.06, (sx * 0.3, -0.11, z), br, rot=(PI / 2, 0, 0), verts=6, bevel=0.008)
    yb = -2.6
    tube("Arm", [(0, -0.1, 10.2), (0, -3.0, 10.2)], 0.07, ir, square=True, poly=True)
    sphere("ArmEnd", 0.1, (0, -3.02, 10.2), br, seg=12, rings=6)
    tube("Brace", [(0, -0.1, 8.1), (0, -0.7, 8.5), (0, -1.6, 9.4), (0, -2.3, 10.13)], 0.05, ir)
    tube("Scroll", [(0, -0.1, 8.1), (0, -0.3, 7.75), (0, -0.62, 7.82), (0, -0.6, 8.08), (0, -0.42, 8.05)], 0.035, ir)
    tube("Scroll2", [(0, -1.1, 10.15), (0, -1.0, 9.6), (0, -1.35, 9.45), (0, -1.45, 9.7), (0, -1.3, 9.78)], 0.03, ir)
    tube("Scroll3", [(0, -0.4, 10.15), (0, -0.35, 9.4), (0, -0.7, 9.15), (0, -0.8, 9.45), (0, -0.65, 9.55)], 0.03, ir)
    cyl("Swivel", 0.08, 0.25, (0, yb, 10.0), br, verts=12, bevel=0.015)
    hoop("Hook", (0, yb, 9.75), 0.09, "X", ir, thick=0.025)
    chain("Chain", [(0, yb, 9.66), (0, yb, 7.95)], ir, r=0.065, thick=0.016)
    hoop("TopRing", (0, yb, 7.85), 0.12, "Y", ir, thick=0.03)
    top = 7.1
    for k in range(4):
        a = k * PI / 2 + PI / 4
        chain(f"Leg{k}", [(0, yb, 7.75), (math.cos(a) * 0.42, yb + math.sin(a) * 0.42, top + 0.05)], ir, r=0.05, thick=0.012)
        hoop(f"Dee{k}", (math.cos(a) * 0.45, yb + math.sin(a) * 0.45, top - 0.02), 0.06, "Z", br, thick=0.015)
    prof = [(0, 3.4), (0.35, 3.42), (0.6, 3.55), (0.7, 3.8), (0.72, 4.2), (0.72, 6.6), (0.68, 6.9), (0.5, 7.08), (0.2, 7.14), (0, 7.15)]
    lathe("Bag", prof, K["gymleather"], seg=28, loc=(0, yb, 0))
    for z in (3.9, 6.6):
        cyl(f"Band{z}", 0.735, 0.22, (0, yb, z), K["leather"], verts=28, bevel=0.02)
    for i in range(12):
        z = 4.2 + i * 0.19
        box(f"Lace{i}", (0.14, 0.03, 0.025), (0, yb + 0.725, z), K["bone"], bevel=0.008, rot=(0, 0.5 if i % 2 else -0.5, 0))
    box("Seam", (0.04, 0.03, 2.4), (0, yb + 0.715, 5.25), K["cord"], bevel=0.01)
    crest("Crest", "Crimson", 0.7, 0.08, T(0, yb - 0.71, 4.85), K)
    return _dims()


def boxing_ring_corner(M):
    """A boxing ring's corner on a 5 x 5 block of raised canvas floor (top 1.4) with a crimson skirt: an iron corner post with
    a buttoned crimson pad bearing the Crimson shield, three crimson-wrapped ropes on turnbuckles running off to +X and +Y (where
    the ring goes on), spacer straps, a towel on the top rope; a corner stool and a bucket on the floor in front."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    S, zt = 5.0, 1.4
    box("Deck", (S, S, zt - 0.15), (0, 0, (zt - 0.15) / 2), K["oakdk"], bevel=0.02)
    box("Canvas", (S + 0.1, S + 0.1, 0.15), (0, 0, zt - 0.075), K["canvas"], bevel=0.04)
    for sy, sx in ((-1, 0), (0, -1)):
        if sy:
            box("Skirt", (S, 0.04, zt - 0.2), (0, -S / 2 - 0.04, (zt - 0.2) / 2 + 0.05), K["enamel"], bevel=0.01)
            box("SkirtTrim", (S, 0.06, 0.08), (0, -S / 2 - 0.05, zt - 0.2), K["gilt"], bevel=0.01)
        else:
            box("SkirtL", (0.04, S, zt - 0.2), (-S / 2 - 0.04, 0, (zt - 0.2) / 2 + 0.05), K["enamel"], bevel=0.01)
            box("SkirtTrimL", (0.06, S, 0.08), (-S / 2 - 0.05, 0, zt - 0.2), K["gilt"], bevel=0.01)
    px = py = -S / 2 + 0.5
    cyl("Post", 0.13, 4.8, (px, py, zt + 2.3), ir, verts=14, bevel=0.01)
    sphere("PostBall", 0.2, (px, py, zt + 4.75), br, seg=16, rings=8)
    box("Pad", (0.55, 0.55, 3.7), (px, py, zt + 2.3), K["leather"], bevel=0.14, segments=3)
    for z in (zt + 0.9, zt + 1.6, zt + 2.3, zt + 3.0, zt + 3.7):
        sphere(f"PadBtn{z}", 0.04, (px - 0.28, py - 0.28, z), K["leather"], seg=8, rings=4)
    crest("PadCrest", "Crimson", 0.9, 0.04, T(px - 0.205, py - 0.205, zt + 1.85) @ RZ(-PI / 4), K)
    for k, h in enumerate((1.2, 2.3, 3.4)):
        z = zt + h
        for d in ("x", "y"):
            a = (px + 0.25, py, z) if d == "x" else (px, py + 0.25, z)
            e = (px + 0.95, py, z) if d == "x" else (px, py + 0.95, z)
            end = (S / 2 + 0.02, py, z) if d == "x" else (px, S / 2 + 0.02, z)
            tube(f"Eye{k}{d}", [a, e], 0.03, ir, poly=True)
            rot = (0, PI / 2, 0) if d == "x" else (PI / 2, 0, 0)
            mid = ((a[0] + e[0]) / 2, (a[1] + e[1]) / 2, z)
            cyl(f"Buckle{k}{d}", 0.08, 0.35, mid, br, rot=rot, verts=10, bevel=0.015)
            tube(f"Rope{k}{d}", [e, end], 0.1, K["leather"], poly=True)
    for d in ("x", "y"):
        for t in (1.7, 3.2):
            p = (px + t, py, 0) if d == "x" else (px, py + t, 0)
            box(f"Spacer{d}{t}", (0.12, 0.12, 2.35), (p[0], p[1], zt + 2.3), K["satchel"], bevel=0.03)
    strip("Towel", [(px + 1.0, py - 0.35, zt + 2.8), (px + 1.05, py - 0.12, zt + 3.4), (px + 1.1, py + 0.05, zt + 3.5),
                    (px + 1.12, py + 0.2, zt + 3.2), (px + 1.1, py + 0.3, zt + 2.95)], 0.7, (1, 0, 0), K["towel"], thick=0.03)
    # the corner stool and bucket on the floor in front
    sx0, sy0 = 0.4, -S / 2 - 0.8
    cyl("StoolSeat", 0.42, 0.1, (sx0, sy0, 1.55), K["oak"], verts=20, bevel=0.03)
    for k in range(3):
        a = k * 2 * PI / 3
        tube(f"StoolLeg{k}", [(sx0 + math.cos(a) * 0.25, sy0 + math.sin(a) * 0.25, 1.5), (sx0 + math.cos(a) * 0.45, sy0 + math.sin(a) * 0.45, 0.0)],
             0.045, K["oak"], poly=True)
    hoop("StoolRing", (sx0, sy0, 0.6), 0.36, "Z", ir, thick=0.02)
    bx, by = -1.6, -S / 2 - 0.85
    lathe("Bucket", [(0, 0), (0.33, 0), (0.42, 0.85), (0.4, 0.86), (0.31, 0.06), (0, 0.06)], K["zinc"], seg=24, loc=(bx, by, 0))
    hoop("BucketRim", (bx, by, 0.85), 0.42, "Z", K["zinc"], thick=0.02)
    tube("Bail", [(bx - 0.42, by, 0.8), (bx - 0.3, by - 0.1, 1.2), (bx, by - 0.15, 1.35), (bx + 0.3, by - 0.1, 1.2), (bx + 0.42, by, 0.8)], 0.015, ir)
    sphere("Sponge", 0.2, (bx + 0.1, by + 0.05, 0.82), flat("Sponge", (0.5, 0.38, 0.16), 0.95), seg=10, rings=6, scale=(1.2, 0.9, 0.6))
    return _dims()


def boxing_gloves(M):
    """A pair of crimson leather boxing gloves laced together, lying on their sides; for a plinth, 1.4 across."""
    K = kit(M)
    for k, (x, yaw, roll) in enumerate(((-0.33, 0.25, 0.0), (0.36, -0.35, 0.5))):
        s = _mark()
        sphere(f"Fist{k}", 1.0, (0, 0, 0), K["leather"], seg=20, rings=12, scale=(0.32, 0.46, 0.3))
        sphere(f"Thumb{k}", 1.0, (0.26, -0.05, 0.05), K["leather"], seg=12, rings=8, scale=(0.12, 0.26, 0.12))
        cyl(f"Cuff{k}", 0.22, 0.42, (0, 0.5, 0), K["leather"], rot=(PI / 2, 0, 0), verts=20, bevel=0.03)
        cyl(f"CuffBand{k}", 0.225, 0.08, (0, 0.68, 0), K["bone"], rot=(PI / 2, 0, 0), verts=20, bevel=0.01)
        tube(f"Seam{k}", [(0, -0.45, 0.0), (0, -0.3, 0.27), (0, 0.0, 0.3), (0, 0.3, 0.22)], 0.012, K["cord"])
        for i in range(5):
            y = 0.35 + i * 0.07
            for sx in (-1, 1):
                cyl(f"Eyelet{k}{i}{sx}", 0.018, 0.02, (sx * 0.05, y, 0.215), K["brassf"], verts=8, bevel=0.0)
            box(f"LaceX{k}{i}", (0.12, 0.012, 0.012), (0, y, 0.225), K["bone"], bevel=0.004, rot=(0, 0, 0.5 if i % 2 else -0.5))
        _xform(s, T(x, 0, 0.3) @ RZ(yaw) @ RY(roll))
    tube("Lace", [(-0.2, 0.55, 0.52), (0.0, 0.8, 0.55), (0.2, 0.75, 0.52)], 0.015, K["bone"])
    tube("LaceEnd", [(0.0, 0.8, 0.55), (0.05, 0.95, 0.3), (0.1, 1.0, 0.02)], 0.012, K["bone"])
    _ground(0)
    return _dims()


def megaphone(M):
    """A coach's megaphone in the Athletes' blue enamel with a brass bell rim, mouthpiece and handle, a gilt ATHLETES plate; lying
    on its side, 2.0 long; for a plinth."""
    K = kit(M)
    s = _mark()
    lathe("Horn", [(0.11, 0.0), (0.12, 0.15), (0.2, 0.7), (0.32, 1.35), (0.46, 1.8), (0.48, 1.85), (0.45, 1.85), (0.3, 1.36), (0.18, 0.7),
                   (0.1, 0.15), (0.09, 0.0)], K["athblue"], seg=28)
    hoop("Rim", (0, 0, 1.84), 0.47, "Z", K["brassf"], thick=0.025)
    lathe("Mouth", [(0, -0.2), (0.11, -0.2), (0.13, -0.12), (0.11, 0.0), (0.0, 0.0)], K["brassf"], seg=16)
    cyl("Grip", 0.125, 0.3, (0, 0, 0.3), K["satchel"], verts=16, bevel=0.01)
    hoop("Band", (0, 0, 1.0), 0.245, "Z", K["gilt"], thick=0.012)
    tube("Handle", [(0.15, 0, 0.6), (0.36, 0, 0.75), (0.38, 0, 1.05), (0.24, 0, 1.15)], 0.03, K["brassf"])
    hoop("Band2", (0, 0, 1.5), 0.405, "Z", K["gilt"], thick=0.012)
    _xform(s, T(-0.8, 0, 0) @ RY(PI / 2 - math.atan((0.48 - 0.12) / 1.85)) @ RZ(PI))
    _ground(s)
    return _dims()


# ================================================================== fencing and archery

def fencing_piste(M):
    """A raised fencing piste 18 long and 2.6 wide (top 0.3): dark oak boards on a crimson plinth with inlaid brass lines and crimson
    warning zones, brass edging, a squat cast-iron end-marker post at each end with a house shield and a brass cord reel, raised
    brass-capped on-guard blocks, and an iron scoring box on legs behind the middle with two touch dials and lamps."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    L, W = 18.0, 2.6
    zt = 0.3
    box("Plinth", (L + 0.1, W + 0.1, zt - 0.1), (0, 0, (zt - 0.1) / 2), K["enamel"], bevel=0.02)
    box("Board", (L, W, 0.12), (0, 0, zt - 0.06), K["oakdk"], bevel=0.02)
    for i in range(1, 9):
        box(f"Seam{i}", (0.02, W - 0.1, 0.012), (-L / 2 + i * 2.0, 0, zt + 0.003), K["ink"], bevel=0.0)
    for sy in (-1, 1):
        box(f"Edge{sy}", (L, 0.08, 0.16), (0, sy * W / 2, zt - 0.06), br, bevel=0.01)
    for k, (x, w) in enumerate([(0, 0.08), (-2.2, 0.06), (2.2, 0.06), (-8.8, 0.08), (8.8, 0.08)]):
        box(f"Line{k}", (w, W - 0.2, 0.014), (x, 0, zt + 0.007), br, bevel=0.0)
    for sx in (-1, 1):
        box(f"Warn{sx}", (1.4, W - 0.2, 0.012), (sx * 7.4, 0, zt + 0.006), K["enamel"], bevel=0.0)
        for sy in (-1, 1):
            box(f"Block{sx}{sy}", (0.3, 0.3, 0.35), (sx * 2.2, sy * (W / 2 + 0.25), 0.175), ir, bevel=0.03)
            sphere(f"BlockCap{sx}{sy}", 0.13, (sx * 2.2, sy * (W / 2 + 0.25), 0.4), br, seg=12, rings=6)
        x = sx * (L / 2 + 0.6)
        lathe(f"EndPost{sx}", [(0, 0), (0.5, 0), (0.48, 0.15), (0.32, 0.25), (0.28, 1.1), (0.36, 1.2), (0.36, 1.3), (0, 1.3)], ir, seg=8, loc=(x, 0, 0))
        sphere(f"EndBall{sx}", 0.22, (x, 0, 1.5), br, seg=14, rings=8)
        crest(f"EndCrest{sx}", "Crimson" if sx < 0 else "Ravens", 0.5, 0.04, T(x, -0.3, 0.45), K)
        cyl(f"Drum{sx}", 0.28, 0.14, (x - sx * 0.2, -0.35, 0.95), br, rot=(PI / 2, 0, 0), verts=18, bevel=0.015)
        tube(f"Cord{sx}", [(x - sx * 0.3, -0.3, 0.95), (x - sx * 1.0, -0.1, 0.45), (x - sx * 1.6, 0.2, zt + 0.02)], 0.02, K["cord"])
    ys = W / 2 + 1.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"BoxLeg{sx}{sy}", [(sx * 1.0, ys + sy * 0.3, 0.0), (sx * 0.85, ys + sy * 0.25, 2.2)], 0.05, ir, square=True, poly=True)
    box("BoxShelf", (1.8, 0.6, 0.08), (0, ys, 0.8), K["oakdk"], bevel=0.02)
    box("Box", (2.4, 0.7, 1.3), (0, ys, 2.85), ir, bevel=0.06)
    box("BoxLid", (2.55, 0.85, 0.12), (0, ys, 3.56), ir, bevel=0.04)
    for sx in (-1, 1):
        cyl(f"DialRim{sx}", 0.44, 0.08, (sx * 0.6, ys - 0.36, 2.8), br, rot=(PI / 2, 0, 0), verts=24, bevel=0.015)
        pprism(f"Dial{sx}", "GY_FenceDial", circ(0.38, 28), 0.02, T(sx * 0.6, ys - 0.405, 2.8), K["gp"], "GY_black")
        box(f"Hand{sx}", (0.025, 0.01, 0.26), (sx * 0.6, ys - 0.42, 2.9), K["gilt"], bevel=0.0, rot=(0, sx * 0.9, 0))
        cyl(f"LampHood{sx}", 0.2, 0.25, (sx * 0.9, ys, 3.75), br, verts=14, bevel=0.02)
        sphere(f"Lamp{sx}", 0.17, (sx * 0.9, ys, 3.95), K["enamel"] if sx < 0 else K["j_Rovers"], seg=14, rings=8)
    finial("BoxFin", 0, ys, 3.62, br, s=1.2)
    box("BoxPlate", (1.0, 0.03, 0.2), (0, ys - 0.36, 2.3), br, bevel=0.01)
    label("BoxText", "TOUCHES", K["ink"], 0, ys - 0.375, 2.3, 0.8, 0.13, depth=0.006)
    return _dims()


def _mask(prefix, mtx, K, bib):
    """A fencing mask looking to -Y: a black wire-mesh face with steel wires, a white padded rim, a white canvas bib under the chin
    with a house-coloured trim, a leather back strap."""
    s = _mark()
    sphere(f"{prefix}Face", 1.0, (0, -0.05, 0.05), K["mesh"], seg=18, rings=12, scale=(0.34, 0.32, 0.46))
    hoop(f"{prefix}Wire", (0, -0.05, 0.05), 0.35, "X", K["steel"], thick=0.012)
    hoop(f"{prefix}Rim", (0, 0.12, 0.02), 0.4, "Y", K["canvas"], thick=0.07)
    pts = [(math.cos(a) * 0.42, 0.1 - 0.18 * math.sin(a) ** 2, -0.32 - 0.18 * math.sin(a)) for a in [(195 + i * 15) * DEG for i in range(11)]]
    strip(f"{prefix}Bib", pts, 0.42, (0, 0.25, -1), K["canvas"], thick=0.04, it=1)
    tpts = [(x * 1.02, y - 0.02, z - 0.2) for x, y, z in pts]
    strip(f"{prefix}Trim", tpts, 0.08, (0, 0.25, -1), bib, thick=0.045, it=1)
    tube(f"{prefix}Strap", [(-0.32, 0.12, 0.25), (0, 0.42, 0.5), (0.32, 0.12, 0.25)], 0.035, K["satchel"])
    _xform(s, mtx)


def _foil(prefix, mtx, K):
    s = _mark()
    cyl(f"{prefix}Blade", 0.014, 2.6, (0, 0, 1.55), K["steel"], verts=6, bevel=0.0)
    lathe(f"{prefix}Bell", [(0, 0.2), (0.17, 0.2), (0.16, 0.24), (0.08, 0.28), (0, 0.29)], K["steel"], seg=18)
    cyl(f"{prefix}Grip", 0.035, 0.32, (0, 0, 0.04), K["satchel"], verts=10, bevel=0.01)
    sphere(f"{prefix}Pommel", 0.05, (0, 0, -0.14), K["brassf"], seg=10, rings=6)
    sphere(f"{prefix}Tip", 0.025, (0, 0, 2.86), K["leather"], seg=8, rings=4)
    _xform(s, mtx)


def fencing_mask_rack(M):
    """A wall rack of four fencing masks (black mesh, bibs in house colours) on iron hooks, two crossed foils above, on a dark
    oak board with a battlemented top; 4.6 wide, 4.0 tall."""
    K = kit(M)
    W, H = 4.6, 3.4
    top = [(-W / 2, 0), (W / 2, 0)]
    n = 7
    for i in range(n):
        x0 = W / 2 - i * W / n
        h = H + 0.35 if i % 2 == 0 else H
        top += [(x0, h), (x0 - W / n, h)]
    prism("Board", top, -0.06, 0.12, K["oakdk"], plane="XZ", bevel=0.015)
    box("Rail", (W - 0.2, 0.12, 0.18), (0, -0.18, 1.85), K["oak"], bevel=0.03)
    houses = ("Crimson", "Ravens", "Rovers", "Wardens")
    for i, h in enumerate(houses):
        x = -1.65 + i * 1.1
        tube(f"Hook{i}", [(x, -0.24, 1.85), (x, -0.5, 1.9), (x, -0.55, 2.05), (x, -0.45, 2.1)], 0.025, K["iron"])
        _mask(f"M{i}", T(x, -0.58, 1.4) @ RZ(0.08 * (i - 1.5)), K, K[f"j_{h}"])
    _foil("FoilA", T(0, -0.2, 2.25) @ RY(62 * DEG) @ T(0, 0, -1.3), K)
    _foil("FoilB", T(0, -0.28, 2.25) @ RY(-62 * DEG) @ T(0, 0, -1.3), K)
    for sx in (-1, 1):
        cyl(f"FoilPeg{sx}", 0.04, 0.3, (sx * 1.0, -0.2, 2.75), K["brassf"], rot=(PI / 2, 0, 0), verts=10, bevel=0.005)
    box("NamePlate", (1.4, 0.03, 0.26), (0, -0.135, 0.5), K["brassf"], bevel=0.01)
    label("NameText", "SALLE D'ARMES", K["ink"], 0, -0.15, 0.5, 1.15, 0.15, depth=0.006)
    return _dims()


def archery_target(M):
    """An archery target: a coiled straw boss with a painted face in the house colours (a raven in the gold) on a leaning oak
    tripod easel, three arrows in the face and one in a leg."""
    K = kit(M)
    oak, br = K["oak"], K["brassf"]
    for sx in (-1, 1):
        tube(f"Leg{sx}", [(sx * 1.35, -0.75, 0), (sx * 0.25, 0.25, 5.2)], 0.07, oak, square=True, poly=True)
        box(f"LegFoot{sx}", (0.22, 0.22, 0.08), (sx * 1.35, -0.75, 0.04), K["iron"], bevel=0.02)
    tube("BackLeg", [(0, 2.2, 0), (0, 0.45, 5.0)], 0.07, oak, square=True, poly=True)
    box("Crown", (0.7, 0.3, 0.3), (0, 0.3, 5.2), oak, bevel=0.03)
    tube("Ledge", [(-1.05, -0.5, 1.15), (1.05, -0.5, 1.15)], 0.07, oak, square=True, poly=True)
    for sx in (-1, 1):
        cyl(f"Peg{sx}", 0.05, 0.4, (sx * 0.85, -0.55, 1.35), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.005)
    s = _mark()
    R = 1.6
    cyl("Boss", R, 0.45, (0, 0, 0), K["straw"], rot=(PI / 2, 0, 0), verts=40, bevel=0.06)
    for k, y in enumerate((-0.16, 0.0, 0.16)):
        hoop(f"Coil{k}", (0, y, 0), R + 0.01, "Y", K["straw"], thick=0.06)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        tube(f"Bind{k}", [(math.cos(a) * (R - 0.05), -0.24, math.sin(a) * (R - 0.05)), (math.cos(a) * (R + 0.07), 0, math.sin(a) * (R + 0.07)),
                          (math.cos(a) * (R - 0.05), 0.24, math.sin(a) * (R - 0.05))], 0.025, K["cord"])
    pprism("Face", "GY_Target", circ(1.5, 48), 0.02, T(0, -0.235, 0), K["gp"], "GY_bone")
    g = random.Random(4380)
    for k, (u, w) in enumerate(((0.12, 0.2), (-0.45, -0.3), (0.6, 0.5))):
        _arrow(f"Arrow{k}", T(u, -0.25, w) @ RX(-PI / 2 + g.uniform(-0.15, 0.15)) @ RY(g.uniform(-0.15, 0.15)) @ T(0, 0, 0.3), K)
    _xform(s, T(0, -0.3, 3.0) @ RX(-15 * DEG))
    _arrow("ArrowLeg", T(-0.85, -0.45, 2.0) @ RX(-PI / 2 + 0.3) @ RY(-0.3) @ T(0, 0, 0.1), K)
    return _dims()


def _arrow(prefix, mtx, K, L=1.9):
    """An arrow along -Z from its point at the origin (so mtx sinks the point into the target), fletching at the far end."""
    s = _mark()
    cyl(f"{prefix}Shaft", 0.022, L, (0, 0, -L / 2), K["oak"], verts=8, bevel=0.0)
    cyl(f"{prefix}Nock", 0.026, 0.06, (0, 0, -L + 0.02), K["bone"], verts=8, bevel=0.0)
    for k in range(3):
        a = k * 2 * PI / 3
        f = prism(f"{prefix}Fl{k}", [(0.02, -L + 0.1), (0.13, -L + 0.18), (0.11, -L + 0.48), (0.02, -L + 0.45)], 0, 0.006,
                  K["leather"] if k == 0 else K["bone"], plane="XZ")
        f.matrix_world = RZ(a) @ f.matrix_world
    _xform(s, mtx)


def bow_rack(M):
    """An oak rack of four strung longbows (leather grips, horn nocks), a top rail ending in carved raven heads, a leather quiver
    of arrows hung on the right post and a brass ARCHERY SOCIETY plate; 4.2 wide, 5.8 tall."""
    K = kit(M)
    oak, oakdk, br = K["oak"], K["oakdk"], K["brassf"]
    W = 3.6
    box("Base", (W + 0.4, 1.2, 0.3), (0, 0, 0.15), oakdk, bevel=0.04)
    box("Trough", (W - 0.2, 0.4, 0.12), (0, 0.15, 0.36), K["felt"], bevel=0.02)
    for sx in (-1, 1):
        box(f"Post{sx}", (0.22, 0.22, 5.2), (sx * W / 2, 0.3, 2.9), oakdk, bevel=0.03)
        finial(f"PostFin{sx}", sx * W / 2, 0.3, 5.5, br)
    box("TopRail", (W + 0.6, 0.24, 0.24), (0, 0.3, 4.9), oak, bevel=0.04)
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.38)
        sphere(f"RavenHead{sx}", 0.17, (x, 0.3, 4.98), K["ebony"], seg=14, rings=8, scale=(1.2, 0.9, 1.0))
        cone(f"Beak{sx}", 0.07, 0.0, 0.32, (x + sx * 0.3, 0.3, 4.95), K["ebony"], verts=8, rot=(0, sx * PI / 2, 0))
        sphere(f"Eye{sx}", 0.025, (x + sx * 0.1, 0.18, 5.03), K["leather"], seg=8, rings=4)
    for k in range(4):
        x = -1.2 + k * 0.8
        box(f"Notch{k}", (0.14, 0.06, 0.12), (x, 0.16, 4.9), K["felt"], bevel=0.01)
        pts = [(x, 0.15, 0.4), (x, -0.25, 1.4), (x, -0.42, 2.6), (x, -0.25, 3.8), (x, 0.15, 4.85)]
        tube(f"Bow{k}", pts, 0.045, oak if k % 2 else K["oakdk"], res=6)
        tube(f"String{k}", [(x, 0.17, 0.42), (x, 0.17, 4.83)], 0.008, K["bone"], poly=True)
        cyl(f"BowGrip{k}", 0.06, 0.4, (x, -0.42, 2.6), K["satchel"], verts=10, bevel=0.01)
        for z in (0.4, 4.85):
            sphere(f"Horn{k}{z}", 0.05, (x, 0.15, z), K["bone"], seg=8, rings=4, scale=(1, 1, 1.6))
    # quiver on the right post
    qx = W / 2 + 0.38
    s = _mark()
    lathe("Quiver", [(0, 0), (0.18, 0), (0.22, 0.15), (0.24, 1.6), (0.25, 1.65), (0.22, 1.65), (0.21, 0.2), (0, 0.15)], K["satchel"], seg=18)
    hoop("QBand1", (0, 0, 0.4), 0.235, "Z", K["brassf"], thick=0.015)
    hoop("QBand2", (0, 0, 1.45), 0.245, "Z", K["brassf"], thick=0.015)
    for i in range(6):
        a = i * 2 * PI / 6
        x, y = math.cos(a) * 0.11, math.sin(a) * 0.11
        cyl(f"QShaft{i}", 0.018, 0.7, (x, y, 1.8), oak, verts=6, bevel=0.0, rot=(0.05 * math.sin(a), 0.05 * math.cos(a), 0))
        f = prism(f"QFl{i}", [(0.0, 1.95), (0.1, 2.0), (0.09, 2.15), (0.0, 2.12)], 0, 0.006, K["leather"] if i % 2 else K["bone"], plane="XZ")
        f.matrix_world = T(x, y, 0) @ RZ(a)
    _xform(s, T(qx, -0.05, 2.2) @ RY(-0.12))
    tube("QStrap", [(qx - 0.05, -0.05, 3.9), (qx - 0.1, 0.2, 4.6), (qx - 0.2, 0.3, 4.8)], 0.025, K["satchel"])
    box("Plaque", (1.8, 0.03, 0.2), (0, -0.615, 0.16), br, bevel=0.01)
    label("PlaqueText", "ARCHERY SOCIETY", K["ink"], 0, -0.63, 0.16, 1.5, 0.12, depth=0.006)
    return _dims()


# ================================================================== team and house

def kit_hamper(M):
    """A wicker team kit hamper, 3.6 x 2.2 x 2.0, its lid thrown back on a leather check strap: leather straps and brass
    buckles, the HOUSE KIT label, house jerseys heaped in it with a sleeve over the rim, a striped scarf and a football."""
    K = kit(M)
    W, D, H = 3.6, 2.2, 2.0
    wk, br = K["wicker"], K["brassf"]
    box("Bottom", (W, D, 0.12), (0, 0, 0.12), wk, bevel=0.04)
    for sy in (-1, 1):
        box(f"WallY{sy}", (W, 0.1, H - 0.12), (0, sy * (D / 2 - 0.05), 0.12 + (H - 0.12) / 2), wk, bevel=0.03)
    for sx in (-1, 1):
        box(f"WallX{sx}", (0.1, D - 0.2, H - 0.12), (sx * (W / 2 - 0.05), 0, 0.12 + (H - 0.12) / 2), wk, bevel=0.03)
        for sy in (-1, 1):
            box(f"Skid{sx}{sy}", (0.3, 0.3, 0.08), (sx * (W / 2 - 0.2), sy * (D / 2 - 0.2), 0.04), K["oakdk"], bevel=0.02)
    for z in (0.15, H - 0.05):
        for sy in (-1, 1):
            box(f"Rim{z}{sy}", (W + 0.04, 0.14, 0.1), (0, sy * (D / 2 - 0.05), z), K["oakdk"], bevel=0.03)
    for sx in (-1, 1):
        x = sx * 1.1
        box(f"StrapF{sx}", (0.2, 0.03, H - 0.2), (x, -D / 2 - 0.015, H / 2 + 0.05), K["satchel"], bevel=0.01)
        box(f"Buckle{sx}", (0.26, 0.05, 0.2), (x, -D / 2 - 0.03, H - 0.45), br, bevel=0.02)
        box(f"BuckleIn{sx}", (0.17, 0.06, 0.11), (x, -D / 2 - 0.03, H - 0.45), K["ink"], bevel=0.01)
        cyl(f"HandleRose{sx}", 0.08, 0.04, (sx * (W / 2 + 0.02), 0, H - 0.4), br, rot=(0, PI / 2, 0), verts=12, bevel=0.01)
        tube(f"Handle{sx}", [(sx * (W / 2 + 0.02), -0.3, H - 0.4), (sx * (W / 2 + 0.2), -0.25, H - 0.5), (sx * (W / 2 + 0.2), 0.25, H - 0.5),
                             (sx * (W / 2 + 0.02), 0.3, H - 0.4)], 0.035, K["satchel"])
    plate("Label", "GY_KitLabel", 1.5, 0.5, 0.03, T(0, -D / 2 - 0.02, 1.15), K, edge="GY_label")
    # the lid, hinged at the back top edge and thrown back
    s = _mark()
    box("Lid", (W + 0.08, D + 0.06, 0.16), (0, 0, H + 0.08), wk, bevel=0.04)
    box("LidRim", (W + 0.1, D + 0.08, 0.06), (0, 0, H + 0.03), K["oakdk"], bevel=0.02)
    for sx in (-1, 1):
        box(f"LidStrap{sx}", (0.2, D + 0.08, 0.03), (sx * 1.1, 0, H + 0.17), K["satchel"], bevel=0.01)
    _xform(s, T(0, D / 2, H) @ RX(-108 * DEG) @ T(0, -D / 2, -H))
    tube("Check", [(-W / 2 + 0.15, D / 2 - 0.4, H - 0.1), (-W / 2 + 0.12, D / 2 + 0.25, H + 0.9), (-W / 2 + 0.15, D / 2 + 0.15, H + 1.6)],
         0.02, K["satchel"])
    # the heap of jerseys
    g = random.Random(4390)
    for i, h in enumerate(("Crimson", "Ravens", "Rovers", "Vigil", "Wardens", "Crimson", "Ravens")):
        x, y = g.uniform(-1.2, 1.2), g.uniform(-0.55, 0.55)
        z = H - 0.15 + g.uniform(-0.05, 0.18) + (0.12 if i > 4 else 0)
        box(f"Jersey{i}", (g.uniform(1.0, 1.4), g.uniform(0.7, 0.9), 0.16), (x, y, z), K[f"j_{h}"], bevel=0.07, segments=3,
            rot=(g.uniform(-0.12, 0.12), g.uniform(-0.12, 0.12), g.uniform(-0.6, 0.6)))
    strip("Sleeve", [(0.4, -0.7, H + 0.05), (0.45, -D / 2 - 0.05, H + 0.02), (0.5, -D / 2 - 0.12, H - 0.4), (0.48, -D / 2 - 0.1, H - 0.85)],
          0.32, (1, 0, 0), K["j_Ravens"], thick=0.05)
    strip("Scarf", [(-1.5, 0.2, H + 0.15), (-W / 2 - 0.02, 0.15, H + 0.05), (-W / 2 - 0.1, 0.1, H - 0.5), (-W / 2 - 0.08, 0.05, H - 1.2)],
          0.3, (0, 1, 0), K["j_Crimson"], thick=0.04)
    for i in range(4):
        box(f"ScarfStripe{i}", (0.04, 0.31, 0.12), (-W / 2 - 0.1, 0.1, H - 0.4 - i * 0.22), K["gilt"], bevel=0.01)
    _football("Ball", T(0.9, 0.1, H + 0.45) @ RY(PI / 2 - 0.2) @ RX(0.2), K["gymleather"], K["bone"], L=0.75, R=0.22)
    return _dims()


def whistle_board(M):
    """The coach's board: a pointed dark oak board with a brass COACH plate, the First Eleven team sheet pinned up, a framed slate
    of laps in chalk, a brass whistle on a crimson lanyard and a stopwatch on hooks, a chalk ledge; 3.2 wide, 4.9 tall."""
    K = kit(M)
    W, H = 3.2, 4.2
    board = [(-W / 2, 0), (W / 2, 0), (W / 2, H)] + [(x, z) for x, z in arch_xz(W / 2, -W / 2, H, 0.7)][1:-1] + [(-W / 2, H)]
    prism("Board", board, -0.06, 0.12, K["oakdk"], plane="XZ", bevel=0.02)
    box("Header", (1.6, 0.04, 0.34), (0, -0.14, 4.15), K["brassf"], bevel=0.015)
    label("HeaderText", "COACH", K["ink"], 0, -0.16, 4.15, 1.2, 0.22, depth=0.008)
    plate("Sheet", "GY_TeamSheet", 1.3, 1.75, 0.01, T(-0.65, -0.125, 2.65), K, edge="GY_paper")
    for x, z in ((-1.25, 3.47), (-0.05, 3.47)):
        sphere(f"Pin{x}", 0.04, (x, -0.14, z), K["enamel"], seg=8, rings=4)
    box("SlateFrame", (1.3, 0.05, 0.98), (0.75, -0.145, 1.25), K["oak"], bevel=0.02)
    plate("Slate", "GY_LapSlate", 1.18, 0.82, 0.02, T(0.75, -0.175, 1.25), K, edge="GY_slate")
    # whistle on its lanyard
    tube("WHook", [(0.55, -0.12, 3.5), (0.55, -0.3, 3.5), (0.55, -0.32, 3.62)], 0.02, K["iron"])
    tube("Lanyard", [(0.5, -0.3, 3.5), (0.42, -0.24, 2.9), (0.55, -0.22, 2.5), (0.68, -0.24, 2.9), (0.6, -0.3, 3.5)], 0.015, K["enamel"])
    s = _mark()
    cyl("Whistle", 0.09, 0.18, (0, 0, 0), K["brassf"], rot=(PI / 2, 0, 0), verts=16, bevel=0.01)
    box("WMouth", (0.07, 0.04, 0.2), (0.0, 0, 0.13), K["brassf"], bevel=0.01)
    hoop("WRing", (0, 0, -0.12), 0.035, "X", K["brassf"], thick=0.008)
    _xform(s, T(0.55, -0.24, 2.36) @ RX(PI))
    # stopwatch on a hook
    tube("SHook", [(1.05, -0.12, 3.5), (1.05, -0.3, 3.5), (1.05, -0.32, 3.62)], 0.02, K["iron"])
    hoop("SBow", (1.05, -0.3, 3.38), 0.07, "Y", K["brassf"], thick=0.015)
    cyl("SCrown", 0.04, 0.08, (1.05, -0.3, 3.29), K["brassf"], verts=10, bevel=0.005)
    cyl("SCase", 0.24, 0.08, (1.05, -0.3, 3.02), K["brassf"], rot=(PI / 2, 0, 0), verts=24, bevel=0.02)
    pprism("SDial", "GY_Dial", circ(0.2, 24), 0.012, T(1.05, -0.345, 3.02), K["gp"], "GY_enamel")
    box("SHand", (0.01, 0.006, 0.16), (1.05, -0.355, 3.08), K["ink"], bevel=0.0, rot=(0, -0.7, 0))
    # chalk ledge
    box("Ledge", (W - 0.2, 0.32, 0.08), (0, -0.22, 0.28), K["oak"], bevel=0.015)
    for i in range(3):
        cyl(f"Chalk{i}", 0.035, 0.3, (-1.0 + i * 0.4, -0.25, 0.35), K["chalk"], rot=(0, PI / 2, 0.3 * i), verts=8, bevel=0.01)
    box("Rag", (0.5, 0.3, 0.06), (0.9, -0.24, 0.35), K["towel"], bevel=0.03, rot=(0, 0, 0.3))
    return _dims()


POINTS = {"Crimson": 412, "Ravens": 389, "Rovers": 251, "Vigil": 407, "Wardens": 298}


def house_points_board(M):
    """The house points board: an ebonised gothic board 7.6 wide, 7.0 tall, between crocketed pinnacles: the gilt HOUSE POINTS
    header, the five house shields and under each three enamel digit tiles on brass hooks with the term's points."""
    K = kit(M)
    W, H = 7.0, 6.0
    eb, br = K["ebony"], K["brassf"]
    box("Board", (W, 0.2, H), (0, -0.1, H / 2), eb, bevel=0.03)
    gable = [(-1.8, H), (1.8, H)] + [(x, z) for x, z in arch_xz(1.8, -1.8, H, 1.0)][1:-1]
    prism("Gable", gable, -0.1, 0.2, eb, plane="XZ", bevel=0.02)
    _quatrefoil("GableFoil", 0, -0.22, H + 0.45, 0.28, K["gilt"])
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.15)
        box(f"Pier{sx}", (0.4, 0.4, H + 0.2), (x, -0.2, (H + 0.2) / 2), eb, bevel=0.03)
        cone(f"Pinnacle{sx}", 0.28, 0.0, 1.1, (x, -0.2, H + 0.75), eb, verts=4, rot=(0, 0, PI / 4))
        for k in range(3):
            sphere(f"Crocket{sx}{k}", 0.06, (x, -0.42 + 0.06 * k, H + 0.4 + k * 0.28), K["gilt"], seg=8, rings=4)
        finial(f"PFin{sx}", x, -0.2, H + 1.25, K["gilt"], s=0.8)
    box("Moulding", (W, 0.1, 0.12), (0, -0.24, H - 0.95), K["gilt"], bevel=0.02)
    box("Base", (W + 0.4, 0.45, 0.3), (0, -0.22, 0.15), eb, bevel=0.03)
    plate("Header", "GY_HP_Header", 5.4, 0.72, 0.04, T(0, -0.22, H - 0.5), K)
    for i, h in enumerate(HOUSES):
        x = -2.8 + i * 1.4
        crest(f"Crest{h}", h, 1.15, 0.05, T(x, -0.23, 3.6), K)
        box(f"Slot{h}", (1.25, 0.04, 0.7), (x, -0.22, 2.7), br, bevel=0.015)
        box(f"SlotIn{h}", (1.15, 0.05, 0.6), (x, -0.23, 2.7), K["ink"], bevel=0.01)
        for j, d in enumerate(f"{POINTS[h]:03d}"):
            xx = x - 0.36 + j * 0.36
            cyl(f"Hook{h}{j}", 0.02, 0.1, (xx, -0.28, 2.97), br, rot=(PI / 2, 0, 0), verts=6, bevel=0.0)
            plate(f"Tile{h}{j}", f"GY_Digit_{d}", 0.32, 0.44, 0.03, T(xx, -0.27, 2.7), K)
        box(f"NameRail{h}", (1.25, 0.06, 0.06), (x, -0.24, 2.3), br, bevel=0.01)
    box("SpareBox", (1.4, 0.4, 0.3), (2.6, -0.5, 0.45), eb, bevel=0.03)
    for j in range(4):
        plate(f"Spare{j}", f"GY_Digit_{(j * 3) % 10}", 0.28, 0.38, 0.03, T(2.15 + j * 0.3, -0.4, 0.62) @ RX(-0.4), K)
    return _dims()


def cursed_trophy(M):
    """The cursed trophy on its plinth: a black marble plinth (top 3.4) with a gilt plaque (THE THORNE CUP, never won twice), a
    tarnished silver cup with bat-wing handles and a skull on its lid, bound in an iron chain and padlock; a violet light leaks
    from under the lid and through cracks in the bowl (Glow)."""
    K = kit(M)
    mb, sv, ir = K["marble"], K["silver"], K["iron"]
    box("Skirt", (1.8, 1.8, 0.3), (0, 0, 0.15), mb, bevel=0.04)
    box("Shaft", (1.4, 1.4, 2.8), (0, 0, 1.7), mb, bevel=0.03)
    box("Cap", (1.75, 1.75, 0.3), (0, 0, 3.25), mb, bevel=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f"Col{sx}{sy}", 0.09, 2.8, (sx * 0.7, sy * 0.7, 1.7), K["gilt"], verts=12, bevel=0.01)
    box("Plaque", (1.0, 0.04, 0.55), (0, -0.72, 2.3), K["gilt"], bevel=0.02)
    box("PlaqueIn", (0.9, 0.05, 0.45), (0, -0.73, 2.3), K["ebony"], bevel=0.01)
    label("PlaqueT1", "THE THORNE CUP", K["gilt"], 0, -0.755, 2.4, 0.78, 0.11, depth=0.006)
    label("PlaqueT2", "never won twice", K["gilt"], 0, -0.755, 2.2, 0.6, 0.1, depth=0.006, font=FONT_I)
    z0 = 3.4
    lathe("Cup", [(0, 0), (0.42, 0), (0.42, 0.06), (0.3, 0.12), (0.12, 0.25), (0.08, 0.45), (0.16, 0.55), (0.08, 0.65), (0.12, 0.8), (0.32, 0.95),
                  (0.5, 1.2), (0.56, 1.5), (0.55, 1.75), (0.6, 1.82), (0.56, 1.84), (0, 1.84)], sv, seg=32, loc=(0, 0, z0))
    lathe("Lid", [(0, 1.86), (0.56, 1.86), (0.5, 1.95), (0.36, 2.1), (0.16, 2.2), (0.1, 2.25), (0, 2.26)], sv, seg=32, loc=(0, 0, z0))
    sphere("Skull", 0.14, (0, 0, z0 + 2.38), K["bone"], seg=14, rings=8, scale=(0.9, 1, 1))
    box("Jaw", (0.14, 0.1, 0.08), (0, -0.07, z0 + 2.27), K["bone"], bevel=0.02)
    for sx in (-1, 1):
        sphere(f"Socket{sx}", 0.035, (sx * 0.05, -0.115, z0 + 2.39), K["ink"], seg=8, rings=4)
        wing = [(0.0, 1.55), (0.25, 1.75), (0.55, 1.85), (0.62, 1.6), (0.48, 1.55), (0.5, 1.35), (0.36, 1.32), (0.34, 1.1), (0.18, 1.12), (0.0, 1.0)]
        prism(f"Wing{sx}", [(sx * (0.5 + u), z0 + w) for u, w in wing], 0, 0.05, sv, plane="XZ", bevel=0.006)
        tube(f"WingBone{sx}", [(sx * 0.52, 0, z0 + 1.55), (sx * 0.8, 0, z0 + 1.78), (sx * 1.05, 0, z0 + 1.86)], 0.025, sv)
    pts = []
    for i in range(41):
        t = i / 40
        a = t * 2.2 * PI - PI / 2
        r = 0.58
        pts.append((math.cos(a) * r, math.sin(a) * r, z0 + 1.15 + t * 0.55))
    chain("Chain", pts, ir, r=0.055, thick=0.014)
    box("Lock", (0.2, 0.08, 0.24), (0.0, -0.6, z0 + 1.2), ir, bevel=0.03)
    hoop("Shackle", (0.0, -0.6, z0 + 1.36), 0.07, "Y", ir, thick=0.018)
    cyl("Keyhole", 0.025, 0.02, (0, -0.645, z0 + 1.18), K["ink"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    set_group("Glow")
    hoop("CurseSeam", (0, 0, z0 + 1.865), 0.53, "Z", K["violet"], thick=0.02)
    g = random.Random(4395)
    for k, a0 in enumerate((-100, -60, -125)):
        a = a0 * DEG
        pp = []
        z = z0 + 1.75
        for i in range(5):
            r = 0.555 + 0.004 if z > z0 + 1.3 else 0.5
            pp.append((math.cos(a) * r, math.sin(a) * r, z))
            a += g.uniform(-0.12, 0.12)
            z -= g.uniform(0.08, 0.14)
        tube(f"Crack{k}", pp, 0.012, K["violet"], poly=True)
    set_group("Main")
    return _dims()


def locker_bench(M):
    """The changing-room bench: a slatted oak bench 8 long (seat 1.6) on three cast-iron end frames with pointed arches, against
    a panelled back board with a rail of iron double hooks and the house name tags; a towel and a Ravens jersey hung up, a canvas
    kit bag under the seat."""
    K = kit(M)
    ir, oak, oakdk, br = K["iron"], K["oak"], K["oakdk"], K["brassf"]
    L = 8.0
    for k in range(4):
        box(f"Slat{k}", (L, 0.3, 0.1), (0, -1.45 + k * 0.34, 1.55), oak, bevel=0.03)
    for x in (-3.6, 0.0, 3.6):
        box(f"FrameTop{x}", (0.12, 1.4, 0.12), (x, -1.0, 1.44), ir, bevel=0.015)
        for sy in (-1, 1):
            y = -1.0 + sy * 0.6
            box(f"FrameLeg{x}{sy}", (0.12, 0.12, 1.4), (x, y, 0.7), ir, bevel=0.015)
            box(f"FrameFoot{x}{sy}", (0.18, 0.28, 0.06), (x, y, 0.03), ir, bevel=0.01)
        tube(f"FrameArch{x}", [(x, yy, z) for yy, z in arch_xz(-1.55, -0.45, 0.6, 0.7)], 0.04, ir, square=True, poly=True)
        tube(f"FrameShelf{x}", [(x, -1.6, 0.3), (x, -0.4, 0.3)], 0.04, ir, square=True, poly=True)
    for k in range(3):
        box(f"ShoeSlat{k}", (L - 0.2, 0.22, 0.05), (0, -1.4 + k * 0.4, 0.36), oak, bevel=0.015)
    # back boards
    box("BackPanel", (L, 0.1, 3.2), (0, -0.05, 2.0 + 1.6), oakdk, bevel=0.02)
    for k in range(9):
        x = -L / 2 + k * L / 8
        box(f"Muntin{k}", (0.12, 0.06, 3.2), (x, -0.13, 3.6), oak, bevel=0.015)
    box("Backrest", (L, 0.14, 0.5), (0, -0.17, 2.4), oak, bevel=0.04)
    box("HookRail", (L, 0.12, 0.42), (0, -0.16, 5.0), oak, bevel=0.03)
    box("Cornice", (L + 0.2, 0.3, 0.14), (0, -0.15, 5.28), oakdk, bevel=0.03)
    plate("Tags", "GY_HookTags", 3.6, 0.48, 0.02, T(0, -0.23, 4.6), K, edge="GY_bone")
    for k in range(7):
        x = -3.3 + k * 1.1
        cyl(f"HookRose{k}", 0.07, 0.03, (x, -0.235, 5.0), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.006)
        tube(f"Hook{k}", [(x, -0.24, 5.0), (x, -0.5, 4.95), (x, -0.56, 5.1), (x, -0.48, 5.18)], 0.025, ir)
        tube(f"HookUp{k}", [(x, -0.3, 4.98), (x, -0.42, 5.3), (x, -0.36, 5.42)], 0.02, ir)
    strip("Towel", [(-2.2, -0.3, 4.2), (-2.2, -0.48, 4.85), (-2.2, -0.56, 5.02), (-2.2, -0.62, 4.85), (-2.2, -0.75, 3.7)], 0.8, (1, 0, 0), K["towel"],
          thick=0.04)
    box("TowelStripe", (0.82, 0.05, 0.1), (-2.2, -0.73, 3.95), K["enamel"], bevel=0.02, rot=(0.1, 0, 0))
    jersey = [(-0.75, 0), (0.75, 0), (0.72, 1.3), (1.1, 1.0), (1.3, 1.2), (0.85, 1.7), (0.25, 1.85), (0.0, 1.7), (-0.25, 1.85), (-0.85, 1.7),
              (-1.3, 1.2), (-1.1, 1.0), (-0.72, 1.3)]
    prism("Jersey", [(1.1 + u, 3.15 + w) for u, w in jersey], -0.62, 0.1, K["j_Ravens"], plane="XZ", bevel=0.03)
    pprism("JerseyCrest", "GY_Crest_Ravens", shield_poly(0.5), 0.02, T(1.4, -0.68, 4.1), K["gp"], "GY_gilt")
    label("JerseyNum", "7", K["bone"], 0.8, -0.675, 3.95, 0.3, 0.4, depth=0.01)
    s = _mark()
    cyl("KitBag", 0.42, 1.8, (0, 0, 0), K["canvas"], rot=(0, PI / 2, 0), verts=20, bevel=0.15)
    for sx in (-1, 1):
        hoop(f"BagBand{sx}", (sx * 0.5, 0, 0), 0.425, "X", K["satchel"], thick=0.025)
    tube("BagHandle", [(-0.5, 0, 0.42), (0, -0.05, 0.75), (0.5, 0, 0.42)], 0.03, K["satchel"])
    _xform(s, T(1.6, -1.0, 0.82) @ RZ(0.1))
    return _dims()


# ================================================================== facilities

def sauna_door(M):
    """The sweatbox: a limestone gothic doorway (5.2 wide, 9.8 tall) with a heavy oak plank door (Door0; hinge on the left, opens
    out) with iron strap hinges, a steamed porthole in a brass ring and a ring pull; an enamel SWEATBOX sign over it, a
    thermometer on the left jamb, a steam pipe and valve on the right, an oak bucket and ladle at the foot."""
    K = kit(M)
    st, ir, br = K["stone"], K["iron"], K["brassf"]
    zs, apex = 5.4, 7.2
    for sx in (-1, 1):
        box(f"Jamb{sx}", (0.9, 0.6, zs), (sx * 2.15, -0.3, zs / 2), st, bevel=0.04)
        box(f"Plinth{sx}", (1.0, 0.7, 0.4), (sx * 2.15, -0.35, 0.2), st, bevel=0.04)
    head = [(-2.6, zs), (-1.7, zs)] + [(x, z) for x, z in arch_xz(-1.7, 1.7, zs, apex - zs, n=12)][1:-1] + [(1.7, zs), (2.6, zs), (2.6, 9.6), (-2.6, 9.6)]
    prism("Head", head, -0.3, 0.6, st, plane="XZ", bevel=0.03)
    box("Hood", (5.4, 0.8, 0.22), (0, -0.4, 9.7), st, bevel=0.04)
    pts = [(x, -0.62, z) for x, z in arch_xz(-1.75, 1.75, zs, apex - zs + 0.05, n=12)]
    tube("Archivolt", pts, 0.06, st, square=True, poly=True)
    plate("Sign", "GY_Sign_Sauna", 2.4, 0.82, 0.04, T(0, -0.63, 8.45), K, edge="GY_teal")
    box("Threshold", (3.6, 0.8, 0.12), (0, -0.4, 0.06), st, bevel=0.03)
    # thermometer on the left jamb
    box("ThermoBoard", (0.42, 0.06, 1.7), (-2.15, -0.63, 4.0), K["oak"], bevel=0.015)
    plate("Thermo", "GY_Thermo", 0.26, 1.34, 0.01, T(-2.08, -0.665, 4.0), K, edge="GY_enamel")
    cyl("ThermoTube", 0.025, 1.3, (-2.28, -0.7, 4.0), K["glass"], verts=8, bevel=0.0)
    cyl("ThermoRed", 0.012, 0.95, (-2.28, -0.7, 3.8), K["enamel"], verts=6, bevel=0.0)
    sphere("ThermoBulb", 0.05, (-2.28, -0.7, 3.32), K["enamel"], seg=10, rings=6)
    # steam pipe and valve
    tube("Pipe", [(2.15, -0.6, 6.9), (2.15, -0.85, 6.9), (2.15, -0.85, 3.6), (2.15, -0.6, 3.6)], 0.07, K["copper"], poly=True)
    hoop("Valve", (2.15, -1.0, 5.6), 0.18, "Y", br, thick=0.025)
    cyl("ValveStem", 0.03, 0.16, (2.15, -0.92, 5.6), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    for k in range(3):
        a = k * 2 * PI / 3
        tube(f"VSpoke{k}", [(2.15, -1.0, 5.6), (2.15 + math.cos(a) * 0.18, -1.0, 5.6 + math.sin(a) * 0.18)], 0.015, br, poly=True)
    cyl("Gauge", 0.14, 0.08, (2.15, -0.92, 6.3), br, rot=(PI / 2, 0, 0), verts=16, bevel=0.01)
    pprism("GaugeDial", "GY_Dial", circ(0.11, 20), 0.01, T(2.15, -0.965, 6.3), K["gp"], "GY_enamel")
    # bucket and ladle
    bx, by = 2.6, -1.4
    lathe("Bucket", [(0, 0), (0.42, 0), (0.48, 0.75), (0.45, 0.76), (0.4, 0.06), (0, 0.06)], K["oak"], seg=20, loc=(bx, by, 0))
    for z in (0.15, 0.6):
        hoop(f"BHoop{z}", (bx, by, z), 0.43 + z * 0.075, "Z", K["copper"], thick=0.02)
    tube("Ladle", [(bx + 0.1, by, 0.5), (bx + 0.25, by - 0.05, 0.85), (bx + 0.45, by - 0.1, 1.3)], 0.025, K["oak"])
    lathe("LadleCup", [(0, 0), (0.1, 0.02), (0.12, 0.12), (0.0, 0.1)], K["copper"], seg=12, loc=(bx + 0.1, by, 0.42))
    # the door
    hx, yd = -1.68, -0.36
    set_group("Door0", hinge=(hx, yd, 0.0), swing=-1)
    dpoly = [(-1.68, 0.12), (1.68, 0.12)] + [(x, z) for x, z in arch_xz(1.68, -1.68, zs, apex - zs - 0.08, n=12)][:-1] + [(-1.68, zs)]
    prism("Door", dpoly, yd, 0.24, K["oakdk"], plane="XZ", bevel=0.02)
    for k in range(1, 6):
        x = -1.68 + k * 3.36 / 6
        ztop = zs + (apex - zs - 0.1) * math.sin((1 - abs(x) / 1.68) * PI / 2) ** 0.75
        box(f"Groove{k}", (0.03, 0.02, ztop - 0.2), (x, yd - 0.12, 0.12 + (ztop - 0.2) / 2), K["ink"], bevel=0.0)
    for z in (1.2, 3.4, 5.2):
        box(f"Strap{z}", (2.6, 0.04, 0.16), (hx + 1.3, yd - 0.14, z), ir, bevel=0.01)
        sphere(f"StrapEnd{z}", 0.1, (hx + 2.6, yd - 0.14, z), ir, seg=10, rings=6, scale=(1, 0.4, 1))
        for k in range(5):
            rivet(f"SRiv{z}{k}", hx + 0.2 + k * 0.55, yd - 0.165, z, br, r=0.03)
        cyl(f"Knuckle{z}", 0.06, 0.3, (hx - 0.02, yd - 0.08, z), ir, verts=10, bevel=0.01)
    hoop("PortRing", (0, yd - 0.13, 4.6), 0.4, "Y", br, thick=0.05)
    cyl("Port", 0.38, 0.05, (0, yd - 0.1, 4.6), K["frost"], rot=(PI / 2, 0, 0), verts=24, bevel=0.0)
    for k in range(6):
        a = k * PI / 3
        rivet(f"PRiv{k}", math.cos(a) * 0.4, yd - 0.18, 4.6 + math.sin(a) * 0.4, br, r=0.03)
    cyl("PullRose", 0.1, 0.04, (1.25, yd - 0.14, 2.9), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.01)
    hoop("Pull", (1.25, yd - 0.2, 2.72), 0.17, "Y", br, thick=0.025)
    set_group("Main")
    return _dims()


def equipment_cage(M):
    """The equipment cage: an iron mesh cage 5 wide, 2.4 deep and 7 tall with a crested front and spear finials, its right-hand
    door padlocked; oak shelves inside with balls, a net of footballs, cricket bats and hockey sticks; an EQUIPMENT plate."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    W, D, H = 5.0, 2.4, 7.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Post{sx}{sy}", (0.12, 0.12, H), (sx * W / 2, sy * D / 2, H / 2), ir, bevel=0.01)
            cone(f"Spear{sx}{sy}", 0.09, 0.0, 0.4, (sx * W / 2, sy * D / 2, H + 0.2), ir, verts=4)
    for z in (0.1, H):
        for sy in (-1, 1):
            box(f"RailX{z}{sy}", (W, 0.08, 0.1), (0, sy * D / 2, z), ir, bevel=0.01)
        for sx in (-1, 1):
            box(f"RailY{z}{sx}", (0.08, D, 0.1), (sx * W / 2, 0, z), ir, bevel=0.01)
    sp = 0.32
    # back and sides: mesh
    for i in range(int(W / sp)):
        x = -W / 2 + sp * (i + 0.5)
        tube(f"BackV{i}", [(x, D / 2, 0.1), (x, D / 2, H)], 0.012, ir, square=True, poly=True)
    for j in range(int(H / sp)):
        z = 0.1 + sp * (j + 0.5)
        tube(f"BackH{j}", [(-W / 2, D / 2, z), (W / 2, D / 2, z)], 0.012, ir, square=True, poly=True)
        for sx in (-1, 1):
            tube(f"SideH{j}{sx}", [(sx * W / 2, -D / 2, z), (sx * W / 2, D / 2, z)], 0.012, ir, square=True, poly=True)
        tube(f"FrontH{j}", [(-W / 2, -D / 2, z), (0.0, -D / 2, z)], 0.012, ir, square=True, poly=True)
    for i in range(int(D / sp)):
        y = -D / 2 + sp * (i + 0.5)
        for sx in (-1, 1):
            tube(f"SideV{i}{sx}", [(sx * W / 2, y, 0.1), (sx * W / 2, y, H)], 0.012, ir, square=True, poly=True)
    for i in range(int(W / 2 / sp)):
        x = -W / 2 + sp * (i + 0.5)
        tube(f"FrontV{i}", [(x, -D / 2, 0.1), (x, -D / 2, H)], 0.012, ir, square=True, poly=True)
    box("Mullion", (0.1, 0.1, H), (0, -D / 2, H / 2), ir, bevel=0.01)
    # cresting
    for k in range(9):
        x = -W / 2 + 0.25 + k * (W - 0.5) / 8
        tube(f"Crest{k}", [(x - 0.25, -D / 2, H), (x, -D / 2, H + 0.45), (x + 0.25, -D / 2, H)], 0.02, ir)
        cone(f"CrestSpear{k}", 0.05, 0.0, 0.2, (x, -D / 2, H + 0.52), ir, verts=4)
    # the door (right half)
    dx0, dx1 = 0.08, W / 2 - 0.08
    yd = -D / 2 - 0.06
    for x in (dx0, dx1):
        box(f"DoorStile{x}", (0.08, 0.06, H - 0.4), (x, yd, H / 2), ir, bevel=0.01)
    for z in (0.3, H / 2, H - 0.3):
        box(f"DoorRail{z}", (dx1 - dx0, 0.06, 0.08), ((dx0 + dx1) / 2, yd, z), ir, bevel=0.01)
    for i in range(7):
        x = dx0 + (i + 1) * (dx1 - dx0) / 8
        tube(f"DoorV{i}", [(x, yd, 0.3), (x, yd, H - 0.3)], 0.012, ir, square=True, poly=True)
    for j in range(int((H - 0.6) / sp)):
        z = 0.3 + sp * (j + 0.5)
        tube(f"DoorH{j}", [(dx0, yd, z), (dx1, yd, z)], 0.012, ir, square=True, poly=True)
    box("Hasp", (0.3, 0.06, 0.1), (0.12, yd - 0.05, 3.6), ir, bevel=0.01)
    box("Padlock", (0.22, 0.1, 0.26), (0.12, yd - 0.12, 3.4), br, bevel=0.04)
    hoop("PadShackle", (0.12, yd - 0.12, 3.58), 0.08, "Y", K["steel"], thick=0.02)
    box("SignPlate", (1.6, 0.03, 0.3), (-1.25, -D / 2 - 0.05, 5.6), br, bevel=0.01)
    label("SignText", "EQUIPMENT", K["ink"], -1.25, -D / 2 - 0.07, 5.6, 1.3, 0.18, depth=0.006)
    # shelves and gear
    for z in (2.6, 4.8):
        box(f"Shelf{z}", (W - 0.2, D - 0.2, 0.1), (0, 0, z), K["oak"], bevel=0.02)
    g = random.Random(4396)
    for i in range(5):
        x = -2.0 + i * 0.95
        r = 0.36 if i % 2 else 0.4
        mat = K["gymleather"] if i % 2 else K["satchel"]
        y = g.uniform(-0.3, 0.3)
        sphere(f"Ball{i}", r, (x, y, 2.65 + r), mat, seg=18, rings=10)
        hoop(f"BallSeam{i}", (x, y, 2.65 + r), r + 0.004, "X", K["cord"], thick=0.01)
    for i in range(3):
        _football(f"FB{i}", T(-1.6 + i * 0.6, 0.2, 5.1) @ RY(PI / 2) @ RX(g.uniform(-0.3, 0.3)), K["gymleather"], K["bone"], L=0.7, R=0.2)
    for i in range(3):
        s = _mark()
        box(f"Bat{i}", (0.36, 0.12, 1.9), (0, 0, 0.95), K["oak"], bevel=0.05)
        cyl(f"BatHandle{i}", 0.06, 1.0, (0, 0, 2.4), K["satchel"], verts=10, bevel=0.01)
        _xform(s, T(0.6 + i * 0.5, 0.6, 0.15) @ RY(0.12 - i * 0.05))
    for i in range(3):
        tube(f"Stick{i}", [(1.8 + i * 0.18, -0.4, 4.4), (1.85 + i * 0.18, -0.4, 0.6), (1.9 + i * 0.18, -0.6, 0.2), (2.15 + i * 0.18, -0.65, 0.2)],
             0.045, K["oakdk"], res=4)
    return _dims()


def first_aid_station(M):
    """The first-aid station: a canvas stretcher on oak poles stood on end on iron wall brackets, a crimson enamel cabinet with
    the FIRST AID sign, a rolled grey blanket on top and a brass bell-pull to call the Matron; 5.4 wide, 8.3 tall."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    # stretcher
    for k, x in enumerate((-2.55, -1.35)):
        cyl(f"Pole{k}", 0.08, 7.9, (x, -0.45, 4.15), K["oak"], verts=12, bevel=0.02)
        for z in (2.0, 6.6):
            tube(f"Bracket{k}{z}", [(x, 0, z), (x, -0.35, z), (x, -0.55, z + 0.15)], 0.035, ir, square=True, poly=True)
        cyl(f"PoleCap{k}", 0.085, 0.12, (x, -0.45, 0.25), K["rubber"], verts=12, bevel=0.01)
    box("Canvas", (1.12, 0.03, 5.6), (-1.95, -0.45, 4.2), K["canvas"], bevel=0.01)
    for z in (1.6, 6.8):
        box(f"Spreader{z}", (1.3, 0.06, 0.08), (-1.95, -0.39, z), K["iron"], bevel=0.01)
    for z in (2.8, 5.2):
        box(f"StrapS{z}", (1.4, 0.06, 0.16), (-1.95, -0.48, z), K["satchel"], bevel=0.015)
        box(f"BuckleS{z}", (0.14, 0.04, 0.2), (-1.35, -0.52, z), br, bevel=0.015)
    # the cabinet
    cx, W, H, D = 1.0, 2.4, 2.8, 0.8
    z0 = 2.8
    box("Cab", (W, D, H), (cx, -D / 2, z0 + H / 2), K["oakdk"], bevel=0.03)
    box("CabDoor", (W - 0.25, 0.05, H - 0.3), (cx, -D - 0.02, z0 + H / 2), K["enamel"], bevel=0.02)
    plate("Sign", "GY_Sign_Aid", 1.9, 0.6, 0.03, T(cx, -D - 0.06, z0 + H - 0.55), K, edge="GY_enamel")
    for z in (z0 + 0.5, z0 + H - 1.15):
        box(f"Hinge{z}", (0.08, 0.04, 0.3), (cx - W / 2 + 0.1, -D - 0.05, z), br, bevel=0.01)
    cyl("Knob", 0.06, 0.08, (cx + W / 2 - 0.3, -D - 0.08, z0 + H / 2 - 0.3), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.01)
    box("Cornice", (W + 0.2, D + 0.15, 0.15), (cx, -D / 2 - 0.05, z0 + H + 0.07), K["oakdk"], bevel=0.03)
    box("Corbel", (W - 0.6, D - 0.2, 0.2), (cx, -D / 2 + 0.1, z0 - 0.1), K["oakdk"], bevel=0.03)
    cyl("Blanket", 0.32, 2.0, (cx, -D / 2, z0 + H + 0.47), material("Blanket", "NH_Leather", tint=(0.12, 0.12, 0.13), scale=4.0, normal=0.3, wear=0.0),
        rot=(0, PI / 2, 0), verts=18, bevel=0.1)
    for sx in (-1, 1):
        hoop(f"BlanketTie{sx}", (cx + sx * 0.6, -D / 2, z0 + H + 0.47), 0.325, "X", K["enamel"], thick=0.02)
    # bell pull
    tube("BellCord", [(cx + W / 2 + 0.35, -0.15, 7.6), (cx + W / 2 + 0.35, -0.2, 3.0)], 0.02, K["enamel"], poly=True)
    box("BellCrank", (0.2, 0.2, 0.2), (cx + W / 2 + 0.35, -0.1, 7.7), br, bevel=0.03)
    lathe("BellHandle", [(0, 0), (0.06, 0), (0.08, 0.1), (0.05, 0.3), (0.02, 0.35), (0, 0.35)], br, seg=12, loc=(cx + W / 2 + 0.35, -0.2, 2.65))
    return _dims()


def stopwatch_stand(M):
    """The race clock: a giant brass stopwatch (the dial 1.6 across, Glass: its crystal) with a bow and crown on a fluted cast-iron
    column on an octagonal base, a little last-lap bell on a bracket; 7.9 tall."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    cyl("Base", 1.0, 0.25, (0, 0, 0.125), ir, verts=8, bevel=0.03)
    cyl("Step", 0.75, 0.2, (0, 0, 0.35), ir, verts=8, bevel=0.03)
    lathe("Column", [(0, 0.45), (0.3, 0.45), (0.26, 0.6), (0.2, 0.7), (0.17, 1.0), (0.15, 4.6), (0.22, 4.75), (0.3, 4.95), (0.3, 5.05), (0, 5.05)],
          ir, seg=24, flute=(12, 0.08))
    zc = 5.95
    tube("Yoke", [(-0.5, 0, 5.0), (-0.75, 0, 5.4), (-0.95, 0, zc)], 0.06, ir)
    tube("Yoke2", [(0.5, 0, 5.0), (0.75, 0, 5.4), (0.95, 0, zc)], 0.06, ir)
    box("YokeBar", (1.0, 0.16, 0.12), (0, 0, 5.02), ir, bevel=0.02)
    cyl("Case", 0.92, 0.42, (0, 0, zc), br, rot=(PI / 2, 0, 0), verts=40, bevel=0.06)
    hoop("Bezel", (0, -0.23, zc), 0.86, "Y", br, thick=0.05)
    pprism("Dial", "GY_Dial", circ(0.82, 48), 0.02, T(0, -0.225, zc), K["gp"], "GY_enamel")
    box("HandSec", (0.025, 0.015, 0.72), (0.0, -0.245, zc + 0.24), K["enamel"], bevel=0.0, rot=(0, 0.4, 0))
    box("HandMin", (0.02, 0.015, 0.12), (0.0, -0.245, zc - 0.33), K["ink"], bevel=0.0, rot=(0, -0.9, 0))
    cyl("Pin", 0.04, 0.03, (0, -0.25, zc), br, rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
    cyl("Stem", 0.1, 0.25, (0, 0, zc + 1.02), br, verts=14, bevel=0.01)
    cyl("Crown", 0.17, 0.2, (0, 0, zc + 1.22), br, verts=20, bevel=0.03)
    hoop("Bow", (0, 0, zc + 1.42), 0.22, "Y", br, thick=0.04)
    for sx in (-1, 1):
        cyl(f"Pusher{sx}", 0.07, 0.18, (sx * 0.62, 0, zc + 0.72), br, rot=(0, sx * 0.75, 0), verts=10, bevel=0.01)
    _quatrefoil("BackFoil", 0, 0.22, zc, 0.4, K["gilt"])
    tube("BellArm", [(0.2, 0, 4.4), (0.6, 0, 4.45), (0.75, 0, 4.35)], 0.03, ir, square=True, poly=True)
    lathe("Bell", [(0, 0.3), (0.05, 0.3), (0.1, 0.25), (0.12, 0.1), (0.17, 0.0), (0.14, 0.01), (0.1, 0.1), (0, 0.25)], br, seg=18, loc=(0.75, 0, 4.03))
    set_group("Glass")
    cyl("Crystal", 0.84, 0.03, (0, -0.28, zc), K["glass"], rot=(PI / 2, 0, 0), verts=40, bevel=0.0)
    set_group("Main")
    return _dims()


def referee_chair(M):
    """An umpire's chair: a tall oak frame (seat 5.6) with a ladder up its front legs, iron cross braces, a footrest, a crimson
    leather seat, arms and a pointed back with the school crest, a brass flag socket with a crimson flag; 9.3 tall."""
    K = kit(M)
    oak, oakdk, ir, br = K["oak"], K["oakdk"], K["iron"], K["brassf"]
    zt = 5.4
    corners = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = (sx * 1.3, sy * 1.3, 0.0)
            b = (sx * 0.8, sy * 0.8, zt)
            corners.append((a, b))
            tube(f"Leg{sx}{sy}", [a, b], 0.1, oakdk, square=True, poly=True)
            box(f"Foot{sx}{sy}", (0.3, 0.3, 0.1), (a[0], a[1], 0.05), ir, bevel=0.02)
    def at(sx, sy, z):
        k = z / zt
        return (sx * (1.3 - 0.5 * k), sy * (1.3 - 0.5 * k), z)
    for i in range(7):
        z = 0.7 + i * 0.68
        tube(f"Rung{i}", [at(-1, -1, z), at(1, -1, z)], 0.055, oak, poly=True)
    for sy in (1,):
        for k in range(2):
            z0, z1 = (0.4, 2.8) if k == 0 else (2.8, 5.1)
            tube(f"XB{k}a", [at(-1, sy, z0), at(1, sy, z1)], 0.04, ir, square=True, poly=True)
            tube(f"XB{k}b", [at(1, sy, z0), at(-1, sy, z1)], 0.04, ir, square=True, poly=True)
    for sx in (-1, 1):
        for k in range(2):
            z0, z1 = (0.4, 2.8) if k == 0 else (2.8, 5.1)
            tube(f"XS{sx}{k}a", [at(sx, -1, z0), at(sx, 1, z1)], 0.04, ir, square=True, poly=True)
            tube(f"XS{sx}{k}b", [at(sx, 1, z0), at(sx, -1, z1)], 0.04, ir, square=True, poly=True)
    box("Platform", (2.0, 2.0, 0.14), (0, 0, zt + 0.07), oak, bevel=0.03)
    tube("Footrest", [(-0.9, -1.05, 4.3), (0.9, -1.05, 4.3)], 0.06, br, poly=True)
    for sx in (-1, 1):
        tube(f"FootrestArm{sx}", [(sx * 0.9, -1.05, 4.3), at(sx, -1, 4.6)], 0.035, ir, poly=True)
    B29.cushion("Seat", (1.5, 1.3, 0.25), (0, 0.1, zt + 0.32), K["leather"], e=(0.3, 0.25), cuts=4)
    for sx in (-1, 1):
        box(f"ArmPost{sx}", (0.1, 0.1, 1.0), (sx * 0.85, -0.5, zt + 0.6), oakdk, bevel=0.02)
        box(f"Arm{sx}", (0.18, 1.5, 0.1), (sx * 0.85, 0.15, zt + 1.15), oak, bevel=0.03)
    back = [(-0.9, zt + 0.15), (0.9, zt + 0.15), (0.9, zt + 2.3)] + [(x, z) for x, z in arch_xz(0.9, -0.9, zt + 2.3, 1.2)][1:-1] + [(-0.9, zt + 2.3)]
    prism("Back", back, 0.85, 0.14, oakdk, plane="XZ", bevel=0.02)
    B29.cushion("BackPad", (1.4, 0.15, 1.4), (0, 0.72, zt + 1.3), K["leather"], e=(0.3, 0.3), cuts=4)
    pprism("Crest", "GY_School_Crest", rect(0.6, 0.66), 0.04, T(0, 0.76, zt + 2.75), K["gp"], "GY_black")
    finial("BackFin", 0, 0.85, zt + 3.5, br, s=1.0)
    cyl("FlagSocket", 0.05, 0.4, (0.95, -0.6, zt + 1.0), br, verts=10, bevel=0.01)
    cyl("FlagStaff", 0.025, 1.7, (0.95, -0.6, zt + 1.85), oak, verts=8, bevel=0.0)
    prism("Flag", [(0.97, zt + 2.0), (1.75, zt + 2.2), (1.7, zt + 2.55), (0.97, zt + 2.65)], -0.6, 0.02, K["j_Crimson"], plane="XZ")
    return _dims()


def basketball_hoop(M):
    """A basketball hoop in an iron frame: two flat iron uprights pinned to the wall from the floor, a pair of riveted truss arms
    holding an oak backboard (bottom 9.6) painted with a crimson square and the school crest, an iron rim at 10.0 and a corded
    net; 3.0 out from the wall."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    for sx in (-1, 1):
        x = sx * 1.4
        box(f"Upright{sx}", (0.24, 0.1, 13.2), (x, -0.08, 6.6), ir, bevel=0.015)
        for z in (0.5, 4.0, 7.5, 11.0, 13.0):
            box(f"Pin{sx}{z}", (0.4, 0.06, 0.16), (x, -0.06, z), ir, bevel=0.01)
            for b in (-1, 1):
                cyl(f"PinBolt{sx}{z}{b}", 0.04, 0.04, (x + b * 0.14, -0.13, z), br, rot=(PI / 2, 0, 0), verts=6, bevel=0.004)
        # the truss arm
        tube(f"TopChord{sx}", [(x, -0.1, 13.0), (x * 0.9, -2.85, 13.0)], 0.06, ir, square=True, poly=True)
        tube(f"BotChord{sx}", [(x, -0.1, 9.4), (x * 0.9, -2.85, 11.0)], 0.06, ir, square=True, poly=True)
        for k in range(4):
            t0, t1 = k / 4, (k + 1) / 4
            ya, yb = -0.1 - 2.75 * t0, -0.1 - 2.75 * t1
            zb0, zb1 = 9.4 + 1.6 * t0, 9.4 + 1.6 * t1
            tube(f"Web{sx}{k}", [(x * (1 - 0.1 * t0), ya, zb0), (x * (1 - 0.1 * t1), yb, 13.0)], 0.035, ir, square=True, poly=True)
            tube(f"Vert{sx}{k}", [(x * (1 - 0.1 * t1), yb, zb1), (x * (1 - 0.1 * t1), yb, 13.0)], 0.035, ir, square=True, poly=True)
        s = _mark()
        _quatrefoil(f"Foil{sx}", 0, 0, 0, 0.3, br)
        _xform(s, T(x * 0.96, -1.3, 11.75) @ RZ(PI / 2))
    for z in (4.0, 11.0):
        box(f"Tie{z}", (2.8, 0.06, 0.12), (0, -0.12, z), ir, bevel=0.01)
    yb = -3.0
    box("Board", (6.0, 0.16, 3.6), (0, yb - 0.08, 11.4), K["oak"], bevel=0.04)
    box("BoardFrame", (6.15, 0.12, 3.75), (0, yb + 0.02, 11.4), ir, bevel=0.02)
    for k, (w, h, cz) in enumerate(((2.0, 0.1, 10.1), (2.0, 0.1, 11.4), (0.1, 1.4, 10.75), (0.1, 1.4, 10.75))):
        x = 0 if k < 2 else (-0.95 if k == 2 else 0.95)
        box(f"Square{k}", (w, 0.02, h), (x, yb - 0.17, cz), K["enamel"], bevel=0.0)
    box("Edge", (5.8, 0.02, 0.1), (0, yb - 0.17, 9.75), K["enamel"], bevel=0.0)
    pprism("Crest", "GY_School_Crest", rect(0.8, 0.88), 0.03, T(0, yb - 0.175, 12.55), K["gp"], "GY_black")
    # the rim and net
    rz, R = 10.0, 0.75
    cy = yb - 0.16 - 0.15 - R
    box("RimPlate", (0.6, 0.1, 0.5), (0, yb - 0.21, rz - 0.1), ir, bevel=0.02)
    tube("RimArm", [(0, yb - 0.25, rz - 0.3), (0, cy + R, rz)], 0.03, ir, poly=True)
    hoop("Rim", (0, cy, rz), R, "Z", K["enamel"], thick=0.035)
    n = 12
    rings = [(R, rz), (0.6, rz - 0.6), (0.48, rz - 1.25)]
    for t in range(2):
        r0, z0 = rings[t]
        r1, z1 = rings[t + 1]
        for i in range(n):
            a0 = (i + 0.5 * t) / n * 2 * PI
            for d in (-0.5, 0.5):
                a1 = a0 + d / n * 2 * PI
                tube(f"Net{t}{i}{d}", [(math.cos(a0) * r0, cy + math.sin(a0) * r0, z0), (math.cos(a1) * r1, cy + math.sin(a1) * r1, z1)], 0.012,
                     K["bone"], poly=True)
    hoop("NetHem", (0, cy, rings[2][1]), rings[2][0], "Z", K["bone"], thick=0.018)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "ClimbingRopes": climbing_ropes,
    "GymRings": gym_rings,
    "WallBars": wall_bars,
    "PommelHorse": pommel_horse,
    "ParallelBars": parallel_bars,
    "BalanceBeam": balance_beam,
    "VaultingBox": vaulting_box,
    "Springboard": springboard,
    "HighJumpStands": high_jump_stands,
    "MatTrolley": mat_trolley,
    "MedicineBallRack": medicine_ball_rack,
    "IndianClubRack": indian_club_rack,
    "RowingMachine": rowing_machine,
    "WallPulley": wall_pulley,
    "PunchingBag": punching_bag,
    "BoxingRingCorner": boxing_ring_corner,
    "BoxingGloves": boxing_gloves,
    "FencingPiste": fencing_piste,
    "FencingMaskRack": fencing_mask_rack,
    "ArcheryTarget": archery_target,
    "BowRack": bow_rack,
    "KitHamper": kit_hamper,
    "WhistleBoard": whistle_board,
    "HousePointsBoard": house_points_board,
    "CursedTrophy": cursed_trophy,
    "LockerBench": locker_bench,
    "Megaphone": megaphone,
    "SaunaDoor": sauna_door,
    "EquipmentCage": equipment_cage,
    "FirstAidStation": first_aid_station,
    "StopwatchStand": stopwatch_stand,
    "RefereeChair": referee_chair,
    "BasketballHoop": basketball_hoop,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"ClimbingRopes": 1.0, "GymRings": 1.0, "FencingPiste": 0.9, "BalanceBeam": 0.95})
B24.SMALL.update({"BoxingGloves": 1.3, "Megaphone": 1.3})
