"""Kit C concept pieces (for the owner's approval of the list): seven key designs, built with the accessory toolkit
but not baked (procedural materials), rendered on the R6 mannequin and the Female body.

E:/Blender/blender.exe -b --factory-startup -P nh_kitc_concepts.py -- [keys] --nobake --out E:/NH-Work/kitc_concept --res 640

Concept only: no clearance check, no hair fits, no bake. The approved list is then built batch by batch like Kits A and B.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Matrix
import nh_acc as A
sys.modules.setdefault("nh_acc", A)
from nh_acc import item, piece, lerp
from nh_acc_batch1 import ccw, frame
from nh_acc_batch4 import wire, mirror_piece
import nh_acc_batch7 as COAT
import nh_kitc_hq      # the masks at the shipping standard
import nh_kitc_boots   # the cavalier knee boots

HP = math.pi / 2


def head_pt(ang_deg, z, r=0.62, y_flat=1.0):
    """a point on a cylinder round the head (centre x 0, y 0), angle 0 = straight ahead (-Y), + toward the character's left"""
    a = math.radians(ang_deg)
    return Vector((r * math.sin(a), -r * math.cos(a) * y_flat, z))


# ---------------------------------------------------------------- 1. the academy varsity jacket (coat builder, cropped)
@item("CVarsity", "Academy varsity jacket", views=["front34", "back", "side"], close=((3.0, -5.6, 1.0), (0, 0, 0.2), 90))
def build_varsity(M):
    X = COAT.coat_mats(M, "delinquent")
    wool = A.mat_cloth("VarsityCrimson", (0.24, 0.022, 0.04), weave=200, rough=0.86, sheen=0.4, bump=0.16, vary=0.08)
    cream = A.mat_leather("VarsityCream", (0.80, 0.74, 0.62), scale=2.6, wear=0.25)
    rib = A.mat_cloth("VarsityRib", (0.02, 0.018, 0.022), weave=700, rough=0.9, sheen=0.2, bump=0.25)
    X.update(wool=wool, collar=rib, lapel=wool, pipe=rib, collar_pipe=rib, lapel_pipe=rib, lining=M["black_wool"])
    P = COAT.coat_params("delinquent")
    P.update(collar_rise=0.04, collar_reach=0.10, collar_back=0.06, lapel_w=0.14)
    P["break"] = P["brk"]
    piece("CVarsityShell", "Torso")
    COAT.build_shell("CVarsity", P, X)
    # snaps down the front, the rib hem band, a chenille crest on the chest and the school name across the back
    for k, z in enumerate((0.30, 0.08, -0.14, -0.36, -0.58)):
        A.cyl(f"VarsitySnap{k}", 0.026, 0.012, tuple(COAT.front_point(-0.40, z, 0.006)), M["brass"], rot=(HP, 0, 0), verts=14)
    for s in (1, -1):
        G = [[COAT.front_point(s * x, z, 0.004) for z in (-0.66, -0.80)] for x in [0.38 + 0.6 * i / 6 for i in range(7)]]
        A.surface(f"VarsityHem{s}", G, 0.02, rib)
    F = frame(tuple(COAT.front_point(0.62, 0.40, 0.012)), (HP, 0, 0))
    A.text_mesh("VarsityLetter", "N", 0.26, A.mat_cloth("Chenille", (0.80, 0.74, 0.62), weave=90, rough=0.95, bump=0.4), F,
                depth=0.018)
    Fb = frame(tuple(COAT.back_point(0.0, 0.52, 0.010)), (HP, 0, math.pi))
    A.text_mesh("VarsityBack", "NIGHTMARE", 0.15, A.mat_cloth("ChenilleB", (0.80, 0.74, 0.62), weave=90, rough=0.95, bump=0.4),
                Fb, depth=0.012)
    X["wool"] = cream   # the sleeves are cream leather
    piece("CVarsitySleeveL", "LeftArm")
    COAT.build_sleeve("CVarsitySleeveL", P, X)
    mirror_piece("CVarsitySleeveL", "CVarsitySleeveR")
    piece("CVarsitySleeveR", "RightArm")
    return {"notes": "concept"}


# ---------------------------------------------------------------- 4. the coffin backpack
@item("CCoffin", "Coffin backpack", views=["back", "side", "front34"], close=((-3.4, 6.0, 1.0), (0, 0.6, 0.2), 80))
def build_coffin(M):
    piece("CCoffin", "Torso")
    from nh_acc_batch1 import crescent, offset_poly
    lacquer = A.mat_flat("CoffinLacquer", (0.018, 0.015, 0.02), rough=0.18, coat=0.7, noise=60, bump=0.02, vary=0.05, wear=0.35, dirt=0.6)
    wood = A.mat_set("CoffinEbony", "NH_Wood", tint=(0.10, 0.07, 0.07), scale=2.2, wear=0.3) if "NH_Wood" in str(A.SRC) else lacquer
    brass, brass_old = M["brass"], M["brassold"]
    # the classic six-sided coffin, its shoulders a little above the middle
    outline = ccw([(0.0, 0.70), (0.30, 0.56), (0.42, 0.26), (0.24, -0.64), (-0.24, -0.64), (-0.42, 0.26), (-0.30, 0.56)])
    # extrude_poly draws the outline upright (x, z) and pushes it toward the front (-Y): from y 0.84 back to 0.54
    A.extrude_poly("CoffinBox", outline, 0.30, lacquer, frame((0, 0.84, 0.05)), bevel=0.035, segments=4)
    # the lid: a raised, bevelled panel with a crimson velvet inset framed in brass beading
    lid = ccw(offset_poly(outline, 0.05))
    A.extrude_poly("CoffinLid", lid, 0.035, lacquer, frame((0, 0.875, 0.05)), bevel=0.018, segments=3)
    inset = ccw(offset_poly(outline, 0.12))
    A.extrude_poly("CoffinVelvet", inset, 0.012, M["crimson_velvet"], frame((0, 0.884, 0.05)), bevel=0.004)
    A.tube("CoffinBeading", [(x, 0.886, z + 0.05) for x, z in inset], 0.010, brass, closed=True, res=6, poly=True)
    A.tube("CoffinTrim", [(x, 0.842, z + 0.05) for x, z in offset_poly(outline, 0.006)], 0.014, brass_old, closed=True, res=6, poly=True)
    # brass corner plates and a row of studs round the lid's edge
    for k, (x, z) in enumerate(outline):
        A.cyl(f"CornerPlate{k}", 0.055, 0.012, (x * 0.96, 0.86, z * 0.97 + 0.05), brass, rot=(math.pi / 2, 0, 0), verts=6, bevel=0.003)
        A.sphere(f"CornerBoss{k}", 0.02, (x * 0.96, 0.87, z * 0.97 + 0.05), brass_old, seg=10, rings=6)
    ring = offset_poly(outline, 0.08)
    for k in range(len(ring)):
        (x0, z0), (x1, z1) = ring[k], ring[(k + 1) % len(ring)]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 0.09))
        for i in range(1, n):
            A.sphere(f"Stud{k}_{i}", 0.010, (lerp(x0, x1, i / n), 0.893, lerp(z0, z1, i / n) + 0.05), brass, seg=8, rings=5)
    # the emblem on the velvet: the school's crescent and three stars
    A.extrude_poly("Crescent", crescent(0.0, 0.0, 0.15, 0.075, 0.045, 0.125), 0.02, brass, frame((0, 0.905, 0.20)), bevel=0.004)
    for k, (x, z) in enumerate(((-0.13, 0.40), (0.14, 0.38), (0.0, -0.10))):
        star = [((0.035 if i % 2 == 0 else 0.014) * math.sin(math.pi * i / 5), (0.035 if i % 2 == 0 else 0.014) * math.cos(math.pi * i / 5))
                for i in range(10)]
        A.extrude_poly(f"Star{k}", ccw([(x + a, z + b) for a, b in star]), 0.015, brass_old, frame((0, 0.9, 0.05)), bevel=0.002)
    # the hinges down the side and a carry handle on top
    for k, z in enumerate((0.40, -0.25)):
        A.cyl(f"Hinge{k}", 0.018, 0.12, (0.405 - 0.05 * (z < 0) * 1.6, 0.86, z), brass, verts=10)
    A.tube("Handle", [(-0.10, 0.70, 0.74), (-0.08, 0.70, 0.82), (0.08, 0.70, 0.82), (0.10, 0.70, 0.74)], 0.016, M["leather_black"], res=6)
    for s in (-1, 1):
        A.box(f"HandleMount{s}", (0.05, 0.05, 0.03), (s * 0.10, 0.70, 0.735), brass, bevel=0.006)
    # the straps wrap the torso (owner): each shoulder strap is a loop hugging the torso box, over the shoulder (clear
    # of the head), down the chest slanting out to the armpit, round under the arm and up the back; a horizontal strap
    # wraps round the torso over them (a larger offset, so it lies on top) and its back run tucks into the coffin's sides
    from nh_acc_batch1 import band_loop, buckle
    strap_m = M["leather_black"]

    def runs_of(G, cut):
        runs, cur = [], []
        for j in range(len(G[0])):
            if any(cut(G[i][j]) for i in range(4)):
                if cur:
                    runs.append(cur); cur = []
            else:
                cur.append(j)
        if cur:
            runs.append(cur)
        if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(G[0]) - 1:   # join across the loop's seam
            runs = [runs[-1] + runs[0][1:]] + runs[1:-1]
        return [r for r in runs if len(r) > 1]

    for s in (1, -1):
        sh, low = Vector((s * 0.72, 0, 1.0)), Vector((s * 1.0, 0, -0.95))
        d = (sh - low).normalized()
        n = Vector((0, 1, 0)).cross(d).normalized()
        G = band_loop((sh + low) / 2, n, 0.15, 0.052)
        A.surface(f"Strap{s}", G, 0.012, strap_m)
        # a brass ladder-lock on the chest, and a tab from the coffin's shoulder to the strap on the back
        x_at = lambda z: s * (0.72 + 0.28 * (1.0 - z) / 1.95)
        buckle(f"StrapLock{s}", (x_at(0.42), -0.559, 0.42), 0.19, 0.085, M["brass"])
        A.tube(f"StrapTab{s}", [(s * 0.28, 0.70, 0.60), (s * 0.50, 0.62, 0.60), (x_at(0.60), 0.566, 0.60)], 0.022, strap_m,
               square=True)
        A.cyl(f"TabRivet{s}", 0.022, 0.012, (s * 0.40, 0.672, 0.60), brass, rot=(math.pi / 2, 0, 0), verts=10)
    G = band_loop((0, 0, -0.30), (0, 0, 1), 0.12, 0.068)
    for k, run in enumerate(runs_of(G, lambda p: p.y > 0.3 and abs(p.x) < 0.33)):
        A.surface(f"WaistStrap{k}", [[G[i][j] for j in run] for i in range(4)], 0.012, strap_m)
    buckle("WaistBuckle", (0, -0.575, -0.30), 0.19, 0.16, M["brass"])
    return {"notes": "concept"}


# ---------------------------------------------------------------- 6. the floating candelabra (wax, iron, three flames)
@item("CCandles", "Floating candelabra", views=["front34", "back", "side"], close=((-3.6, -4.2, 1.9), (-1.2, 0.2, 1.4), 70))
def build_candles(M):
    piece("CCandles", "Torso")
    c = Vector((-1.25, 0.30, 1.30))   # above and behind the right shoulder
    A.lathe("CandleBase", [(0, 0), (0.10, 0), (0.12, 0.02), (0.05, 0.05), (0.03, 0.14), (0.05, 0.17), (0, 0.18)], tuple(c),
            M["iron"], seg=24)
    arms = [(-0.20, 0.0), (0.0, 0.0), (0.20, 0.0)]
    for k, (dx, dy) in enumerate(arms):
        top = c + Vector((dx, dy, 0.30 if dx == 0 else 0.24))
        if dx:
            A.tube(f"Arm{k}", [tuple(c + Vector((0, 0, 0.17))), tuple(c + Vector((dx * 0.6, 0, 0.12))), tuple(top - Vector((0, 0, 0.04)))],
                   0.014, M["iron"], res=8)
        A.lathe(f"Cup{k}", [(0, 0), (0.035, 0), (0.05, 0.03), (0.05, 0.04), (0, 0.04)], tuple(top - Vector((0, 0, 0.04))), M["iron"], seg=16)
        h = 0.24 - 0.04 * k
        A.cyl(f"Candle{k}", 0.034, h, tuple(top + Vector((0, 0, h / 2))), M["wax"], verts=16, bevel=0.004)
        for d in range(3):   # wax drips down the candle
            a = 2.1 * d + k
            A.sphere(f"Drip{k}{d}", 0.012, tuple(top + Vector((0.034 * math.cos(a), 0.034 * math.sin(a), h - 0.03 - 0.03 * d))),
                     M["wax"], scale=(0.8, 0.8, 1.8))
        A.cyl(f"Wick{k}", 0.004, 0.025, tuple(top + Vector((0, 0, h + 0.012))), M["black_enamel"], verts=6, bevel=0.0)
    piece("CCandleFlames", "Torso", kind="Glow", glow=(1.0, 0.62, 0.25))
    for k, (dx, dy) in enumerate(arms):
        h = 0.24 - 0.04 * k
        top = c + Vector((dx, dy, (0.30 if dx == 0 else 0.24) + h + 0.055))
        A.sphere(f"Flame{k}", 0.028, tuple(top), A.mat_glow(f"FlameGlow{k}", (1.0, 0.62, 0.25), 8.0), scale=(0.7, 0.7, 1.6))
    return {"notes": "concept"}


# ---------------------------------------------------------------- 7. the monocle on a chain
@item("CMonocle", "Brass monocle", views=["front34", "front", "side"], close=((-1.6, -3.6, 1.6), (-0.22, -0.6, 1.5), 60))
def build_monocle(M):
    piece("CMonocle", "Head")
    c = head_pt(-22, 1.62, 0.67)   # the character's right eye
    A.torus("MonoRim", 0.105, 0.016, tuple(c), M["gold"], rot=(HP, 0, math.radians(-22)))
    A.cyl("MonoLens", 0.095, 0.006, tuple(c), A.mat_flat("MonoGlass", (0.70, 0.75, 0.80), rough=0.03, coat=0.9, noise=5, bump=0,
                                                         vary=0, wear=0), rot=(HP, 0, math.radians(-22)), verts=24)
    ring = c + Vector((-0.09, -0.01, -0.06))
    A.torus("MonoLoop", 0.015, 0.004, tuple(ring), M["gold"], rot=(0, HP, 0))
    from nh_acc import chain
    A.chain("MonoChain", [tuple(ring), tuple(ring + Vector((-0.04, 0.02, -0.18))), tuple(ring + Vector((-0.02, 0.06, -0.36)))],
            0.011, M["gold"])
    return {"notes": "concept"}


if __name__ == "__main__":
    targets = [a for a in A.argv if not a.startswith("--") and (A.argv.index(a) == 0 or not A.argv[A.argv.index(a) - 1].startswith("--"))]
    keys = targets[0].split(",") if targets else [k for k in A.ITEMS if k.startswith("C")]
    for k in keys:
        try:
            A.run(k)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[kitc] {k} FAILED: {e}")
