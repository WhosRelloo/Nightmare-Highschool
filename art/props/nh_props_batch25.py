"""Props batch 25 (2026-11-05): the door kit for nh_props.py, on theme with the Institution: soot-dark stone, cast iron,
brass and gilt, crimson enamel and black lacquer (oak only in the secret bookcase). Every door is finished on BOTH faces,
so it looks right from whichever side a player comes through, and every leaf is its own rigged piece.

  ClassroomDoor     a crimson enamel iron door with raised panels, a wired-glass light and brass levers both sides, under a
                    glazed transom in a soot-stone frame
  GothicDoubleDoor  pointed-arch double doors, iron-sheathed and studded, strap hinges and ring pulls on both faces, in a
                    moulded stone portal with a hood mould on both faces
  IronGate          a wrought-iron double gate (spear-topped bars, scrolls, gilt quatrefoil medallions) between stone piers
  HeadmasterDoor    a grand black lacquer door, six gilt-moulded panels and the crest on both faces, brass knobs, under an
                    iron sunburst fanlight in a moulded round-headed frame with a keystone
  BookcaseDoor      a secret door: a full oak bookcase of leather-bound books on one face, a panelled, iron-strapped back on
                    the other, swinging on a hidden pivot
  SlidingIronDoor   a riveted iron boiler-room door with crimson X-braces and a wired viewing port, sliding into the wall
  CellarHatch       a floor hatch, iron-banded both faces with a ring pull, hinged along its back edge over stone steps going
                    down into the dark

Rig: each moving piece is its own group with its origin on the hinge (the FBX origin, Roblox PivotOffset):
  Leaf0, Leaf1          swinging leaves; they turn about the world's up axis through the hinge, which sits on the wall's
                        centre line, so a door can swing either way (away from whoever opens it)
  Leaf0Glass            a leaf's glass (Roblox Glass), turning with it about the same hinge
  CellarHatch_Leaf0     turns about its back edge (Blender X) and opens one way, up
  SlidingIronDoor_Leaf0 slides along Blender X (into the wall)
The rig is written to art/props/doors_batch25.json on every build for the Studio setup.

Front faces -Y, Z is up, the origin is at the bottom centre on the wall's centre line (y = 0); a frame spans the wall from
y = -D to +D. CellarHatch's origin is at floor level with its pit below z = 0. Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch8 import _spike, _crockets, _moss, _crack
from nh_props_batch9 import foil
from nh_props_batch10 import gilt, lacquer
import nh_props_batch20 as B20
import nh_props_batch23 as B23
from nh_props_batch23 import kit, sweep, ribbon, loopbar, pierce, _rotz
import window_shapes as WS

RIG = {}          # prop -> {piece: {kind, hinge (Blender), axis, slide, angle}}


def _rig(prop, piece, kind, hinge, angle=100, axis=(0, 0, 1), slide=(0, 0, 0)):
    RIG.setdefault(prop, {})[f"{prop}_{piece}"] = {"kind": kind, "hinge": list(hinge), "axis": list(axis), "slide": list(slide), "angle": angle}


def _write_rig():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doors_batch25.json")
    old = {}
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf-8"))
        except ValueError:
            old = {}
    old.update(RIG)
    json.dump(old, open(path, "w", encoding="utf-8"), indent=1)


# ------------------------------------------------------------------ helpers

def frame(prefix, path, w, D, mat, step=0.5, every=2, mould=True):
    """Jamb and head stones round a door opening, the same on both faces (an architrave each side), no sill.
    path: the opening's edge from the right foot, up, over the head and down to the left foot (x, z), counter-clockwise."""
    if mould:
        prof = [(0.0, -D + 0.12), (0.08, -D + 0.02), (0.15, -D - 0.05), (0.27, -D - 0.05), (0.31, -D + 0.01), (w, -D + 0.01),
                (w, D - 0.01), (0.31, D - 0.01), (0.27, D + 0.05), (0.15, D + 0.05), (0.08, D - 0.02), (0.0, D - 0.12)]
    else:
        prof = [(0.0, -D + 0.1), (0.1, -D), (w, -D), (w, D), (0.1, D), (0.0, D - 0.1)]
    o = WS.resample(path, step, closed=False)
    loops = [WS.offset(o, d, closed=False) for d, _ in prof]
    n = len(o)
    m = len(prof)
    cuts = list(range(0, n - 1, every)) + [n - 1]
    for j, (c0, c1) in enumerate(zip(cuts, cuts[1:])):
        idx = list(range(c0, c1 + 1))
        verts = [(loops[k][i][0], y, loops[k][i][1]) for i in idx for k, (_, y) in enumerate(prof)]
        cx = sum(v[0] for v in verts) / len(verts)
        cz = sum(v[2] for v in verts) / len(verts)
        verts = [(cx + (x - cx) * 0.988, y, cz + (z - cz) * 0.988) if z > 0.02 else (cx + (x - cx) * 0.988, y, z) for x, y, z in verts]
        faces = []
        L = len(idx)
        for a in range(L - 1):
            for k in range(m):
                k2 = (k + 1) % m
                faces.append((a * m + k, a * m + k2, (a + 1) * m + k2, (a + 1) * m + k))
        faces.append(tuple(range(m)))
        faces.append(tuple((L - 1) * m + k for k in range(m)))
        B23._mk(f"{prefix}{j}", verts, faces, mat)


def door_path(outline):
    """An opening outline from WS (foot, right jamb up, head, left jamb down) as the open edge path for frame()."""
    return outline[1:] + [outline[0]]


def both(s0, fn):
    """Build fn() for the front face, then again turned 180 degrees about Z for the back (for decoration symmetric in x)."""
    fn()
    s1 = _mark()
    fn()
    _xform(s1, _rotz(math.pi))


def threshold(prefix, hw, D, mat):
    box(prefix, (2 * hw + 0.4, 2 * D + 0.2, 0.08), (0, 0, 0.04), mat, bevel=0.02)


def knuckles(prefix, x, z0, z1, mat, n=3, r=0.055):
    for k in range(n):
        z = z0 + (z1 - z0) * (0.12 + 0.76 * k / (n - 1))
        cyl(f"{prefix}{k}", r, 0.34, (x, 0, z), mat, verts=12, bevel=0.0)
        sphere(f"{prefix}Cap{k}", r * 1.05, (x, 0, z + 0.19), mat, seg=10, rings=4, scale=(1, 1, 0.5))


def lever(prefix, x, z, t, mat, hand=1):
    """Brass lever handles on both faces of a leaf of thickness t: a rose, a lever turned toward the hinge side."""
    for sy in (-1, 1):
        y = sy * (t / 2 + 0.02)
        cyl(f"{prefix}Rose{sy}", 0.09, 0.04, (x, y, z), mat, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
        tube(f"{prefix}Lever{sy}", [(x, y + sy * 0.03, z), (x, y + sy * 0.12, z), (x - hand * 0.12, y + sy * 0.14, z), (x - hand * 0.34, y + sy * 0.12, z - 0.02)],
             0.022, mat)
        box(f"{prefix}Plate{sy}", (0.12, 0.02, 0.42), (x, y, z - 0.24), mat, bevel=0.008)
        box(f"{prefix}Key{sy}", (0.025, 0.006, 0.07), (x, y + sy * 0.012, z - 0.34), material("Keyhole", base=(0.01, 0.01, 0.012), rough=0.9),
            bevel=0.0, segments=1)


def panel(prefix, x0, x1, z0, z1, y, sgn, field, mould, depth=0.035):
    """A raised panel on a leaf face at y (sgn -1 = the front face, +1 the back): a proud field inside a square moulding."""
    w, h = x1 - x0, z1 - z0
    box(f"{prefix}Field", (w - 0.16, depth, h - 0.16), ((x0 + x1) / 2, y + sgn * depth / 2, (z0 + z1) / 2), field, bevel=0.025)
    tube(f"{prefix}Mould", [(x0, y + sgn * 0.01, z0), (x1, y + sgn * 0.01, z0), (x1, y + sgn * 0.01, z1), (x0, y + sgn * 0.01, z1)], 0.03, mould,
         closed=True, square=True, poly=True)


def rivets(prefix, pts, y, mat, r=0.03):
    for k, (x, z) in enumerate(pts):
        sphere(f"{prefix}{k}", r, (x, y, z), mat, seg=6, rings=3, scale=(1, 0.6, 1))


def strap(prefix, x0, x1, y, z, mat, sgn):
    """A wrought-iron strap hinge on a face (from the hinge edge x0 toward x1), ending in a pointed fleur."""
    d = 1 if x1 > x0 else -1
    tube(prefix, [(x0, y, z), (x1, y, z)], 0.045, mat, square=True, poly=True)
    _spike(f"{prefix}Tip", (x1 + d * 0.09, y, z), 0.09, 0.2, mat, verts=4, rot=(0, -d * math.pi / 2, 0))
    for k in range(5):
        x = x0 + (x1 - x0) * (0.08 + 0.2 * k)
        sphere(f"{prefix}Nail{k}", 0.03, (x, y + sgn * 0.045, z), mat, seg=6, rings=3, scale=(1, 0.6, 1))


# ================================================================== the doors

def classroom_door(M):
    K = kit(M)
    st, dk, iron, brass, en = K["st"], K["dk"], K["iron"], K["brass"], K["enamel"]
    rnd = random.Random(2501)
    HW, ZD, ZT, D = 1.8, 7.6, 9.0, 0.55
    frame("Frame", door_path(WS.rect(HW, 0.0, ZT)), 0.55, D, st)
    threshold("Threshold", HW, D, dk)
    # the stone transom between the door and the glazed light above, the light's iron glazing bars and glass
    box("Transom", (2 * HW + 0.02, 2 * D - 0.06, 0.24), (0, 0, ZD + 0.12), dk, bevel=0.025)
    for x in (-HW / 3, HW / 3):
        ribbon(f"TransomBar{x:.1f}", [(x, ZD + 0.24), (x, ZT)], 0.05, -0.04, 0.04, iron)
    ribbon("TransomRail", [(-HW, ZD + 0.85), (HW, ZD + 0.85)], 0.04, -0.035, 0.035, iron)
    set_group("Glass")
    B20.tprism("TransomPane", WS.rect(HW, ZD + 0.24, ZT), 0.0, 0.02, K["glass"])
    # the leaf: crimson enamel iron, stiles and rails, two raised panels below, a wired-glass light above, both faces
    t = 0.22
    xh = -HW + 0.03
    W, H = 2 * HW - 0.06, ZD - 0.05
    x0, x1 = xh, xh + W
    set_group("Leaf0", hinge=(xh, 0.0, 0.02), swing=-1)
    _rig("ClassroomDoor", "Leaf0", "swing", (xh, 0.0, 0.02), 100)
    body = box("Leaf", (W, t, H), ((x0 + x1) / 2, 0, 0.02 + H / 2), en, bevel=0.015)
    lx0, lx1, lz0, lz1 = x0 + 0.55, x1 - 0.55, 4.35, 6.75
    pierce(body, [WS.rect((lx1 - lx0) / 2, lz0, lz1, cx=(lx0 + lx1) / 2)])
    for sy in (-1, 1):
        y = sy * t / 2
        for k, (za, zb) in enumerate(((0.55, 2.0), (2.25, 3.95))):
            panel(f"Panel{sy}{k}", x0 + 0.5, x1 - 0.5, za, zb, y, sy, en, iron)
        tube(f"LightMould{sy}", [(lx0, y + sy * 0.015, lz0), (lx1, y + sy * 0.015, lz0), (lx1, y + sy * 0.015, lz1), (lx0, y + sy * 0.015, lz1)], 0.035, brass,
             closed=True, square=True, poly=True)
        box(f"Kick{sy}", (W - 0.2, 0.012, 0.42), ((x0 + x1) / 2, y + sy * 0.006, 0.3), brass, bevel=0.004)
        box(f"Plaque{sy}", (0.62, 0.02, 0.24), ((x0 + x1) / 2, y + sy * 0.01, 7.05), brass, bevel=0.006)
        rivets(f"PlaqueRivet{sy}", [((x0 + x1) / 2 - 0.25, 7.05), ((x0 + x1) / 2 + 0.25, 7.05)], y + sy * 0.022, iron, r=0.018)
    for x in ((lx0 + lx1) / 2,):
        ribbon("LightBarV", [(x, lz0), (x, lz1)], 0.04, -0.03, 0.03, iron)
    ribbon("LightBarH", [(lx0, (lz0 + lz1) / 2), (lx1, (lz0 + lz1) / 2)], 0.04, -0.03, 0.03, iron)
    lever("Lever", x1 - 0.32, 3.4, t, brass, hand=1)
    knuckles("Knuckle", xh, 0.1, H, brass)
    set_group("Leaf0Glass", hinge=(xh, 0.0, 0.02), swing=-1)
    _rig("ClassroomDoor", "Leaf0Glass", "with", (xh, 0.0, 0.02))
    B20.tprism("Wired", WS.rect((lx1 - lx0) / 2 + 0.02, lz0 - 0.02, lz1 + 0.02, cx=(lx0 + lx1) / 2), 0.0, 0.02, K["glass"])
    set_group("Main")
    _moss("Moss", [(-HW - 0.4, -D - 0.06, 0.08), (HW + 0.45, D + 0.06, 0.08)], K["moss"], rnd, size=0.08)
    return _dims()


def gothic_double_door(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2502)
    HW, ZS, ZA, D = 3.0, 6.0, 10.3, 0.7
    op = WS.arch(HW, 0.0, ZS, ZA, 16)
    frame("Portal", door_path(op), 0.8, D, st, step=0.55)
    threshold("Threshold", HW, D, dk)
    s0 = _mark()
    both(s0, lambda: B23.hood("Hood", HW + 0.92, ZS, ZA + 1.05, -D - 0.12, dk, dk, st, r=0.1, ret=0.32, n=18))
    t = 0.26
    inner = WS.offset(WS.ccw(op), -0.03)
    for k, sx in enumerate((-1, 1)):
        xh = sx * (HW - 0.03)
        half = WS.clip_convex(inner, WS.rect((HW - 0.03) / 2 - 0.005, -1.0, ZA + 1, cx=sx * (HW + 0.03) / 2))
        half = [(x, max(z, 0.02)) for x, z in half]
        set_group(f"Leaf{k}", hinge=(xh, 0.0, 0.02), swing=sx)
        _rig("GothicDoubleDoor", f"Leaf{k}", "swing", (xh, 0.0, 0.02), 95)
        B20.tprism(f"Leaf{k}", WS.ccw(half), 0.0, t, iron)
        xs = [p[0] for p in half]
        xa, xb = min(xs), max(xs)
        meet = xa if sx > 0 else xb             # the leaf's meeting edge (at the middle)
        for sy in (-1, 1):
            y = sy * (t / 2 + 0.01)
            # an edging bar round the leaf, three strap hinges from the hinge edge, studs in rows, a ring pull
            tube(f"Edge{k}{sy}", [(x, y, z) for x, z in WS.offset(WS.ccw(half), -0.06)], 0.04, iron, closed=True, square=True, poly=True)
            for j, z in enumerate((1.0, 3.4, 5.6)):
                strap(f"Strap{k}{sy}{j}", xh - sx * 0.02, xh - sx * 2.2, y + sy * 0.03, z, iron, sy)
            for row in range(9):
                z = 0.5 + row * 0.62
                xsr = [xa + 0.25 + i * (xb - xa - 0.5) / 4 for i in range(5)]
                rivets(f"Stud{k}{sy}{row}", [(x, z) for x in xsr if z < ZS - 0.2 or abs(x) < HW * 0.6], y + sy * 0.02, iron, r=0.035)
            xr = meet - sx * 0.45
            cyl(f"PullRose{k}{sy}", 0.12, 0.04, (xr, y + sy * 0.03, 3.5), brass, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
            hoop(f"PullRing{k}{sy}", (xr, y + sy * 0.09, 3.3), 0.18, "Y", brass, thick=0.024)
        knuckles(f"Knuckle{k}", xh, 0.2, ZS - 0.2, iron, r=0.07)
        set_group("Main")
    _moss("Moss", [(-HW - 0.6, -D - 0.1, 0.08), (HW + 0.7, D + 0.1, 0.08), (-HW - 1.0, D + 0.12, ZS - 0.03)], K["moss"], rnd, size=0.1)
    _crack("Crack", (HW + 0.35, -D - 0.065, 3.5), (0.2, 0, -1), (1, 0, 0), 0.8, rnd, K["hollow"])
    return _dims()


def iron_gate(M):
    K = kit(M)
    st, dk, iron, gl = K["st"], K["dk"], K["iron"], K["gilt"]
    HW, H, RISE = 3.0, 6.6, 0.7
    # the piers: stone with a cap and a ball finial
    for sx in (-1, 1):
        x = sx * (HW + 0.55)
        box(f"PierFoot{sx}", (1.3, 1.3, 0.5), (x, 0, 0.25), dk, bevel=0.04)
        box(f"Pier{sx}", (1.0, 1.0, 7.4), (x, 0, 0.5 + 3.7), st, bevel=0.04)
        box(f"PierBand{sx}", (1.12, 1.12, 0.2), (x, 0, 5.2), dk, bevel=0.03)
        box(f"PierCap{sx}", (1.3, 1.3, 0.3), (x, 0, 8.05), dk, bevel=0.04)
        lathe(f"PierFinial{sx}", [(0, 8.2), (0.32, 8.2), (0.22, 8.35), (0.14, 8.45), (0, 8.45)], st, seg=20, loc=(x, 0, 0))
        sphere(f"PierBall{sx}", 0.34, (x, 0, 8.75), st, seg=18, rings=10)
        for sy in (-1, 1):
            s1 = _mark()
            foil(f"PierFoil{sx}{sy}", 0, 0, 0, 0.26, dk, lobes=4, thick=0.02)
            _xform(s1, Matrix.Translation((x, sy * 0.505, 3.0)) @ _rotz(0 if sy < 0 else math.pi))
    box("Threshold", (2 * HW + 0.2, 1.0, 0.08), (0, 0, 0.04), dk, bevel=0.02)
    # two leaves of wrought iron in the wall plane (the same both ways)
    for k, sx in enumerate((-1, 1)):
        xh = sx * (HW - 0.04)
        xm = sx * 0.03
        set_group(f"Leaf{k}", hinge=(xh, 0.0, 0.1), swing=sx)
        _rig("IronGate", f"Leaf{k}", "swing", (xh, 0.0, 0.1), 100)
        x0, x1 = sorted((xh, xm))
        R = (HW * HW + RISE * RISE) / (2 * RISE)
        zc = H + RISE - R
        topz = lambda x: zc + math.sqrt(max(R * R - x * x, 0))
        tube(f"StileH{k}", [(xh, 0, 0.15), (xh, 0, topz(xh))], 0.07, iron, square=True, poly=True)
        tube(f"StileM{k}", [(xm, 0, 0.15), (xm, 0, topz(xm))], 0.05, iron, square=True, poly=True)
        for z in (0.25, 1.35, 4.9):
            tube(f"Rail{k}{z}", [(x0, 0, z), (x1, 0, z)], 0.045, iron, square=True, poly=True)
        tube(f"TopRail{k}", [(x, 0, topz(x)) for x in [x0 + (x1 - x0) * i / 10 for i in range(11)]], 0.05, iron, square=True, poly=True)
        n = 9
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            zt = topz(x) + 0.35
            tube(f"Bar{k}{i}", [(x, 0, 0.25), (x, 0, zt)], 0.03, iron, square=True, poly=True)
            _spike(f"Spear{k}{i}", (x, 0, zt + 0.14), 0.06, 0.28, iron, verts=4)
            sphere(f"Collar{k}{i}", 0.045, (x, 0, topz(x) - 0.12), gl if i % 2 else iron, seg=8, rings=4)
        # C-scrolls in the dog-bar band, a gilt quatrefoil medallion in the middle band
        for i in range(n - 1):
            xa = x0 + (x1 - x0) * (i + 0.5) / n
            hoop(f"Scroll{k}{i}", (xa + (x1 - x0) / n / 2, 0, 0.8), 0.24, "Y", iron, thick=0.02)
        cx = (x0 + x1) / 2
        hoop(f"MedalRing{k}", (cx, 0, 3.1), 0.62, "Y", iron, thick=0.04)
        loopbar(f"MedalFoil{k}", WS.foil_outline(cx, 3.1, 0.52, 4, n=56, a0=math.pi / 4), 0.04, -0.03, 0.03, gl)
        sphere(f"MedalBoss{k}", 0.1, (cx, 0, 3.1), gl, seg=10, rings=5, scale=(1, 0.7, 1))
        for j, z in enumerate((1.1, 5.4)):
            cyl(f"Gudgeon{k}{j}", 0.08, 0.3, (xh, 0, z), iron, verts=10, bevel=0.0)
        if k == 1:
            tube("Latch", [(xm - 0.35, 0, 3.6), (xm + 0.25, 0, 3.6)], 0.03, iron, square=True, poly=True)
            hoop("LatchRing", (xm - 0.3, 0, 3.45), 0.1, "Y", iron, thick=0.015)
        set_group("Main")
    return _dims()


def headmaster_door(M):
    K = kit(M)
    st, dk, iron, brass, gl = K["st"], K["dk"], K["iron"], K["brass"], K["gilt"]
    lq = lacquer()
    rnd = random.Random(2504)
    HW, ZD, D = 2.1, 8.2, 0.6
    op = WS.roundhead(HW, 0.0, ZD + 0.25, 18)
    frame("Frame", door_path(op), 0.65, D, st, step=0.45)
    threshold("Threshold", HW, D, dk)
    kz = ZD + 0.25 + HW
    for k in range(1):
        prism("Keystone", [(-0.34, kz + 0.9), (0.34, kz + 0.9), (0.22, kz - 0.05), (-0.22, kz - 0.05)], 0.0, 2 * D + 0.16, dk, bevel=0.03)
    for sy in (-1, 1):
        B20._crest(f"KeyCrest{sy}", 0, sy * (D + 0.1), kz + 0.45, M, gl, s=0.6, face=sy)
    box("Transom", (2 * HW + 0.02, 2 * D - 0.08, 0.25), (0, 0, ZD + 0.125), dk, bevel=0.025)
    # the iron sunburst fanlight
    zc = ZD + 0.25
    ribbon("FanHub", [(math.cos(a) * 0.5, zc + math.sin(a) * 0.5) for a in [i / 14 * math.pi for i in range(15)]], 0.06, -0.04, 0.04, iron)
    for i in range(1, 8):
        a = i / 8 * math.pi
        ribbon(f"FanRay{i}", [(math.cos(a) * 0.5, zc + math.sin(a) * 0.5), (math.cos(a) * (HW - 0.04), zc + math.sin(a) * (HW - 0.04))], 0.05, -0.035, 0.035,
               iron)
    sphere("FanBoss", 0.16, (0, 0, zc + 0.05), gl, seg=12, rings=6, scale=(1, 0.6, 1))
    set_group("Glass")
    B20.tprism("Fanlight", WS.ccw([(-HW, zc), (HW, zc)] + [(math.cos(a) * HW, zc + math.sin(a) * HW) for a in [i / 18 * math.pi for i in range(1, 18)]]), 0.0, 0.02,
               K["glass"])
    # the leaf: black lacquer, six raised panels with gilt mouldings, the crest above the middle rail, both faces
    t = 0.26
    xh = -HW + 0.03
    W, H = 2 * HW - 0.06, ZD - 0.05
    x0, x1 = xh, xh + W
    set_group("Leaf0", hinge=(xh, 0.0, 0.02), swing=-1)
    _rig("HeadmasterDoor", "Leaf0", "swing", (xh, 0.0, 0.02), 100)
    box("Leaf", (W, t, H), ((x0 + x1) / 2, 0, 0.02 + H / 2), lq, bevel=0.015)
    cxm = (x0 + x1) / 2
    for sy in (-1, 1):
        y = sy * t / 2
        for row, (za, zb) in enumerate(((0.5, 2.6), (2.9, 4.9), (5.4, 7.7))):
            for col, (xa, xb) in enumerate(((x0 + 0.35, cxm - 0.12), (cxm + 0.12, x1 - 0.35))):
                panel(f"P{sy}{row}{col}", xa, xb, za, zb, y, sy, lq, gl)
        box(f"MidRail{sy}", (W - 0.3, 0.03, 0.3), (cxm, y + sy * 0.015, 5.15), lq, bevel=0.01)
        tube(f"Bead{sy}", [(x0 + 0.12, y + sy * 0.02, 0.2), (x1 - 0.12, y + sy * 0.02, 0.2), (x1 - 0.12, y + sy * 0.02, H - 0.1), (x0 + 0.12, y + sy * 0.02, H - 0.1)],
             0.018, gl, closed=True, square=True, poly=True)
        B20._crest(f"Crest{sy}", cxm, y + sy * 0.05, 5.15, M, gl, s=0.55, face=sy)
        xk = x1 - 0.35
        cyl(f"KnobRose{sy}", 0.11, 0.04, (xk, y + sy * 0.02, 3.6), brass, rot=(math.pi / 2, 0, 0), verts=18, bevel=0.008)
        tube(f"KnobNeck{sy}", [(xk, y + sy * 0.03, 3.6), (xk, y + sy * 0.12, 3.6)], 0.03, brass, poly=True)
        sphere(f"Knob{sy}", 0.09, (xk, y + sy * 0.17, 3.6), brass, seg=14, rings=8, scale=(1, 0.8, 1))
        box(f"Escutcheon{sy}", (0.1, 0.02, 0.2), (xk, y + sy * 0.01, 3.25), brass, bevel=0.006)
    knuckles("Knuckle", xh, 0.1, H, brass)
    set_group("Main")
    _moss("Moss", [(-HW - 0.45, -D - 0.06, 0.08), (HW + 0.45, D + 0.06, 0.08)], K["moss"], rnd, size=0.08)
    return _dims()


def bookcase_door(M):
    K = kit(M)
    st, dk, iron, brass, gl = K["st"], K["dk"], K["iron"], K["brass"], K["gilt"]
    oak = M["oakdark"]
    rnd = random.Random(2505)
    HW, ZD, D = 2.15, 8.1, 0.6
    frame("Lining", door_path(WS.rect(HW, 0.0, ZD)), 0.42, D, st, mould=False)
    threshold("Threshold", HW, D, dk)
    # the bookcase leaf: a deep oak case on a hidden pivot at its left edge, on the wall's centre line
    T = 0.86
    xh = -HW + 0.06
    W, H = 2 * HW - 0.12, ZD - 0.08
    x0, x1 = xh, xh + W
    cx = (x0 + x1) / 2
    set_group("Leaf0", hinge=(xh, 0.0, 0.02), swing=-1)
    _rig("BookcaseDoor", "Leaf0", "swing", (xh, 0.0, 0.02), 80)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.12, T, H), (cx + sx * (W / 2 - 0.06), 0, 0.02 + H / 2), oak, bevel=0.015)
    box("Top", (W, T, 0.16), (cx, 0, 0.02 + H - 0.08), oak, bevel=0.015)
    box("Plinth", (W, T, 0.3), (cx, 0, 0.17), oak, bevel=0.015)
    box("Back", (W - 0.2, 0.08, H - 0.4), (cx, T / 2 - 0.08, 0.02 + H / 2), oak, bevel=0.01)
    box("Cornice", (W + 0.1, T + 0.08, 0.14), (cx, 0, 0.02 + H - 0.02), oak, bevel=0.03)
    tube("CorniceGilt", [(x0 + 0.02, -T / 2 - 0.05, H - 0.12), (x1 - 0.02, -T / 2 - 0.05, H - 0.12)], 0.02, gl, poly=True)
    leathers = [material(f"Leather{i}", "NH_Leather", tint=c, scale=1.8, normal=0.5, wear=0.5) for i, c in
                enumerate(((0.26, 0.035, 0.05), (0.06, 0.08, 0.2), (0.05, 0.1, 0.06), (0.32, 0.2, 0.08), (0.1, 0.05, 0.03), (0.14, 0.02, 0.06)))]
    shelves = [0.32, 1.85, 3.35, 4.85, 6.35]
    for j, z in enumerate(shelves):
        box(f"Shelf{j}", (W - 0.24, T - 0.12, 0.08), (cx, -0.04, z + 0.04), oak, bevel=0.01)
        top = (shelves[j + 1] if j + 1 < len(shelves) else H - 0.18) - 0.04
        x = x0 + 0.16
        k = 0
        while x < x1 - 0.3:
            w = rnd.uniform(0.09, 0.17)
            h = min(top - z - 0.14, rnd.uniform(0.85, 1.3))
            lean = 0.0 if rnd.random() > 0.12 else rnd.uniform(0.1, 0.25)
            d = rnd.uniform(0.5, 0.62)
            bk = box(f"Book{j}_{k}", (w, d, h), (x + w / 2, -T / 2 + 0.06 + d / 2, z + 0.08 + h / 2), leathers[rnd.randrange(len(leathers))], bevel=0.008,
                     segments=1, rot=(0, lean, 0))
            if rnd.random() < 0.45:
                box(f"Band{j}_{k}", (w + 0.004, 0.01, 0.025), (x + w / 2, -T / 2 + 0.055, z + 0.08 + h * 0.8), gl, bevel=0.0, segments=1)
            x += w + (0.05 if lean else 0.006)
            k += 1
    # the secret side: a panelled back with iron straps
    yb = T / 2
    for row, (za, zb) in enumerate(((0.5, 2.9), (3.2, 5.6), (5.9, 7.7))):
        for col, (xa, xb) in enumerate(((x0 + 0.25, cx - 0.08), (cx + 0.08, x1 - 0.25))):
            panel(f"BackPanel{row}{col}", xa, xb, za, zb, yb, 1, oak, oak)
    for j, z in enumerate((1.2, 6.6)):
        strap(f"BackStrap{j}", x0 + 0.05, x0 + 1.9, yb + 0.03, z, iron, 1)
    hoop("BackRing", (x1 - 0.35, yb + 0.08, 3.6), 0.14, "Y", iron, thick=0.02)
    cyl("BackRingRose", 0.08, 0.03, (x1 - 0.35, yb + 0.02, 3.75), iron, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.0)
    cyl("PivotTop", 0.06, 0.12, (xh + 0.08, 0, H + 0.02), iron, verts=10, bevel=0.0)
    set_group("Main")
    return _dims()


def sliding_iron_door(M):
    K = kit(M)
    st, dk, iron, brass, en = K["st"], K["dk"], K["iron"], K["brass"], K["enamel"]
    rnd = random.Random(2506)
    HW, ZD, D = 2.4, 7.6, 0.55
    frame("Frame", door_path(WS.rect(HW, 0.0, ZD + 0.4)), 0.5, D, st, mould=False)
    threshold("Threshold", HW, D, dk)
    # an iron head box hiding the track, rivetted on both faces, and iron jamb channels
    box("HeadBox", (2 * HW + 0.02, 0.5, 0.42), (0, 0, ZD + 0.2), iron, bevel=0.015)
    for sy in (-1, 1):
        rivets(f"HeadRivet{sy}", [(-HW + 0.2 + i * (2 * HW - 0.4) / 12, ZD + 0.2) for i in range(13)], sy * 0.255, iron, r=0.028)
        for sx in (-1, 1):
            box(f"Channel{sx}{sy}", (0.12, 0.06, ZD), (sx * (HW - 0.06), sy * 0.16, ZD / 2), iron, bevel=0.01)
    # the leaf: rivetted iron plate, crimson enamel rails and an X-brace on both faces, a wired port, pull handles
    t = 0.2
    W, H = 2 * HW - 0.08, ZD - 0.04
    x0, x1 = -HW + 0.04, HW - 0.04
    set_group("Leaf0", hinge=(x0, 0.0, 0.02), swing=-1)
    _rig("SlidingIronDoor", "Leaf0", "slide", (x0, 0.0, 0.02), slide=(W - 0.35, 0, 0))
    body = box("Plate", (W, t, H), (0, 0, 0.02 + H / 2), iron, bevel=0.012)
    pz = 5.6
    pierce(body, [WS.circle(0, pz, 0.38, 24)])
    for sy in (-1, 1):
        y = sy * (t / 2 + 0.02)
        for z in (0.3, 3.7, H - 0.2):
            box(f"Rail{sy}{z:.1f}", (W - 0.1, 0.04, 0.3), (0, y, z), en, bevel=0.01)
        for sx in (-1, 1):
            box(f"Stile{sy}{sx}", (0.3, 0.04, H - 0.2), (sx * (W / 2 - 0.15), y, 0.02 + H / 2), en, bevel=0.01)
        for a, b in (((-1, 0.45), (1, 3.55)), ((-1, 3.55), (1, 0.45))):
            ribbon(f"Brace{sy}{a[1]:.1f}", [(a[0] * (W / 2 - 0.3), a[1]), (b[0] * (W / 2 - 0.3), b[1])], 0.24, y - 0.02, y + 0.02, en)
        hoop(f"PortRing{sy}", (0, y, pz), 0.44, "Y", brass, thick=0.04)
        rivets(f"PortRivet{sy}", [(math.cos(a) * 0.52, pz + math.sin(a) * 0.52) for a in [i / 10 * 2 * math.pi for i in range(10)]], y + sy * 0.02, iron, r=0.025)
        rivets(f"PlateRivet{sy}", [(sx * (W / 2 - 0.15), 0.6 + i * 0.6) for sx in (-1, 1) for i in range(11)], y + sy * 0.025, iron, r=0.022)
        tube(f"Pull{sy}", [(x1 - 0.4, y, 3.0), (x1 - 0.4, y + sy * 0.14, 3.1), (x1 - 0.4, y + sy * 0.14, 4.2), (x1 - 0.4, y, 4.3)], 0.035, iron, poly=True)
    ribbon("PortBarV", [(0, pz - 0.38), (0, pz + 0.38)], 0.03, -0.02, 0.02, iron)
    ribbon("PortBarH", [(-0.38, pz), (0.38, pz)], 0.03, -0.02, 0.02, iron)
    set_group("Leaf0Glass", hinge=(x0, 0.0, 0.02), swing=-1)
    _rig("SlidingIronDoor", "Leaf0Glass", "with", (x0, 0.0, 0.02))
    B20.tprism("Port", WS.circle(0, pz, 0.4, 24), 0.0, 0.02, K["glass"])
    set_group("Main")
    _moss("Moss", [(-HW - 0.35, -D - 0.06, 0.08)], K["moss"], rnd, size=0.08)
    return _dims()


def cellar_hatch(M):
    K = kit(M)
    st, dk, iron, brass, en = K["st"], K["dk"], K["iron"], K["brass"], K["enamel"]
    rnd = random.Random(2507)
    S, PIT = 1.8, 2.6                       # the opening's half size, the pit's depth below the floor
    # the stone curb round the opening (flush with the floor, a chamfered lip)
    for k, (cx, cy, w, d) in enumerate(((0, -S - 0.3, 2 * S + 1.2, 0.6), (0, S + 0.3, 2 * S + 1.2, 0.6), (-S - 0.3, 0, 0.6, 2 * S), (S + 0.3, 0, 0.6, 2 * S))):
        box(f"Curb{k}", (w, d, 0.24), (cx, cy, -0.1), st, bevel=0.04)
    # the pit: dark stone walls and steps going down along the far side
    hol = K["hollow"]
    for k, (cx, cy, w, d) in enumerate(((0, -S - 0.05, 2 * S, 0.1), (0, S + 0.05, 2 * S, 0.1), (-S - 0.05, 0, 0.1, 2 * S), (S + 0.05, 0, 0.1, 2 * S))):
        box(f"PitWall{k}", (w, d, PIT), (cx, cy, -0.22 - PIT / 2), dk, bevel=0.0, segments=1)
    box("PitFloor", (2 * S, 2 * S, 0.1), (0, 0, -0.22 - PIT), hol, bevel=0.0, segments=1)
    n = 6
    for k in range(n):
        z = -0.22 - (k + 1) * PIT / (n + 1)
        y = S - 0.35 - k * 0.5
        box(f"Step{k}", (2 * S - 0.4, 0.5, 0.18), (0, y, z), st, bevel=0.03)
    box("Gloom", (2 * S - 0.02, 2 * S - 0.02, 0.02), (0, 0, -0.22 - PIT * 0.75), hol, bevel=0.0, segments=1)
    # the hatch: iron plate, crimson enamel bands and rivets on both faces, a sunk ring pull, hinged on its back edge
    t = 0.16
    set_group("Leaf0", hinge=(0.0, S - 0.02, 0.02), swing=1)
    _rig("CellarHatch", "Leaf0", "hatch", (0.0, S - 0.02, 0.02), 105, axis=(1, 0, 0))
    box("Hatch", (2 * S - 0.06, 2 * S - 0.06, t), (0, 0, 0.02 - t / 2 + 0.01), iron, bevel=0.012)
    for sz in (-1, 1):
        z = 0.02 + 0.012 if sz > 0 else 0.02 - t - 0.002
        for j, y in enumerate((-S + 0.45, 0.0, S - 0.45)):
            box(f"Band{sz}{j}", (2 * S - 0.16, 0.26, 0.03), (0, y, z), en, bevel=0.008)
            for i in range(8):
                x = -S + 0.25 + i * (2 * S - 0.5) / 7
                sphere(f"BandRivet{sz}{j}{i}", 0.03, (x, y, z + sz * 0.02), iron, seg=6, rings=3, scale=(1, 1, 0.6))
        if sz < 0:
            for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
                tube(f"Brace{a[0]}{a[1]}", [(a[0] * (S - 0.3), a[1] * (S - 0.3), z - 0.04), (b[0] * (S - 0.3), b[1] * (S - 0.3), z - 0.04)], 0.05, iron,
                     square=True, poly=True)
    cyl("PullCup", 0.22, 0.03, (0, -S + 0.6, 0.035), iron, verts=18, bevel=0.005)
    hoop("PullRing", (0, -S + 0.6, 0.06), 0.18, "Z", brass, thick=0.025)
    for x in (-S + 0.6, S - 0.6):
        cyl(f"Knuckle{x:.1f}", 0.07, 0.5, (x, S - 0.02, 0.02), iron, rot=(0, math.pi / 2, 0), verts=12, bevel=0.0)
    set_group("Main")
    _moss("Moss", [(-S - 0.55, -S - 0.5, 0.03), (S + 0.5, S + 0.45, 0.03)], K["moss"], rnd, size=0.08)
    return _dims()


BUILDERS = {
    "ClassroomDoor": classroom_door,
    "GothicDoubleDoor": gothic_double_door,
    "IronGate": iron_gate,
    "HeadmasterDoor": headmaster_door,
    "BookcaseDoor": bookcase_door,
    "SlidingIronDoor": sliding_iron_door,
    "CellarHatch": cellar_hatch,
}


def _wrap(fn):
    def build(M):
        d = fn(M)
        _write_rig()
        return d
    return build


P.BUILD.update({k: _wrap(v) for k, v in BUILDERS.items()})
P.PREVIEW_PAD.update({"ClassroomDoor": 1.15, "GothicDoubleDoor": 1.05, "IronGate": 1.05, "HeadmasterDoor": 1.1, "BookcaseDoor": 1.15,
                      "SlidingIronDoor": 1.15, "CellarHatch": 1.3})
# the _open preview turns pieces about Z only: the hatch and the slider are shown closed there
P.OPEN_DEG.update({"CellarHatch_Leaf0": 0, "SlidingIronDoor_Leaf0": 0, "SlidingIronDoor_Leaf0Glass": 0})
