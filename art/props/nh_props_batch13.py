"""Props batch 13 (2026-11-03): tables in different shapes for nh_props.py, for the school, the Headmaster's office
and the town. On theme with the Institution: black and bone-veined marble, wrought and cast iron, brass and gilt,
black lacquer, crimson leather and velvet, and very little wood. Every top is flat and level so other props sit on it.

  TableRound     a round black marble top (4 across) with a gilt edge and a gilt-foiled iron apron, on a fluted iron
                 pedestal with three scrolled legs ending in gilt ball-and-claw feet
  TableOval      an oval dining table (8 x 4.5) in black lacquer with gilt stringing and a crimson velvet runner with
                 gilt fringes, on twin turned pedestals, each on four splayed legs with brass paw caps
  TableBanquet   a long refectory feast table (16 x 3.5): a thick chamfered dark castle-stone slab with an ovolo and a
                 riveted iron strap, on three heavy gothic iron trestles (pointed arch, lancets, a quatrefoil roundel,
                 brass bosses), a riveted flat-bar stretcher, a crimson velvet runner with gilt fringes, and a tall
                 pewter candlestick pair with dripping candles (Glow: the flames)
  TableCafe      a small square bistro table for the town: a bone marble top with a brass edge on an ornate cast-iron
                 base of four scrolled feet and four C-scroll brackets
  TableHexagon   a hexagonal library table (4.5 across): black lacquer with a crimson leather inset and a brass edge, a
                 traceried apron, six turned iron legs joined by a hexagonal stretcher with a central boss
  TableDemilune  a half-moon wall console (a wall piece: its flat back sits at +Y): a bone marble top, a gilt carved
                 apron with rosettes and a gilt quatrefoil roundel at the front, four matching black lacquer cabriole
                 legs with gilt knee rosettes, lines and sabots, and gilt stretchers with an urn finial
  TableCoffee    a low table (4 x 2.2): a smoked glass top (Glass) in a brass rim on a black iron frame with brass
                 sabots, and a lacquer shelf below with books
  TableSide      a small round tripod side table: a bone marble top with a brass gallery rail, a turned iron column
                 with gilt bands and three scrolled legs

Front faces -Y, Z is up, the origin is at the bottom centre. Top heights (studs): Round 3.0, Oval 3.0, Banquet 3.0,
Cafe 2.7, Hexagon 3.0, Demilune 3.0, Coffee 1.5, Side 2.5 (inside the gallery).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math

import bpy
import bmesh
from mathutils import Matrix

import nh_props as P
from nh_props import box, cyl, tube, set_group, _arch_loop
from nh_props_batch3 import sphere, cone, circle_pts, flame
from nh_props_batch4 import lathe, hoop, leaf, prism, rrect, _mark, _xform, _dims, flat, _book, _mesh
from nh_props_batch5 import marble
from nh_props_batch9 import foil, candle, wax_mat


# ------------------------------------------------------------------ materials

def black_marble():
    return marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.36, 0.34, 0.3), scale=1.3, width=0.018, distortion=6.0, detail=2.5)


def bone_marble():
    return marble("MarbleBone", base=(0.8, 0.77, 0.7), vein=(0.34, 0.33, 0.34), scale=1.3, width=0.018, distortion=6.0, detail=2.5)


def lacquer():
    return flat("BlackLacquer", (0.022, 0.02, 0.025), 0.2, wear=0.12, dirt=0.6)


def velvet():
    return flat("CrimsonVelvet", (0.17, 0.018, 0.028), 0.9, dirt=0.4)


def pewter():
    return flat("Pewter", (0.55, 0.55, 0.57), 0.34, metal=1.0, wear=0.3, dirt=0.85)


def dark_stone():
    return P.material("CastleStoneDark", "NH_Limestone", tint=(0.13, 0.125, 0.12), scale=0.3, wear=0.25, dirt=1.0)


def gilt():
    """Even burnished gilding for broad carved surfaces (the brass set blotches across a wide apron)."""
    return flat("Gilt", (0.62, 0.42, 0.16), 0.32, metal=1.0, wear=0.15, dirt=0.7)


# ------------------------------------------------------------------ helpers

def poly_pts(r, z, n, a0=0.0, sx=1.0, sy=1.0):
    """Points round a (squashed) circle at height z, starting at angle a0."""
    return [(math.cos(a0 + i / n * 2 * math.pi) * r * sx, math.sin(a0 + i / n * 2 * math.pi) * r * sy, z) for i in range(n)]


def ring_band(name, r_in, r_out, z0, z1, mat, seg=48, scale=(1, 1)):
    """A closed vertical band (an apron) between two radii: a lathe of a closed rectangle."""
    return lathe(name, [(r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0), (r_out, z0)], mat, seg=seg, scale=scale)


def claw_foot(prefix, x, y, ang, M, r=0.12):
    """A gilt ball gripped by three iron talons, the talons coming down from the leg end toward angle `ang`."""
    sphere(f"{prefix}Ball", r, (x, y, r), M["brass"], seg=14, rings=7)
    c, s = math.cos(ang), math.sin(ang)
    for k, da in enumerate((-0.9, 0.0, 0.9)):
        a = ang + math.pi + da * 0.9
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x - c * 0.02, y - s * 0.02, r * 2.15), (x + ca * r * 0.75, y + sa * r * 0.75, r * 1.75),
               (x + ca * r * 1.05, y + sa * r * 1.05, r * 0.95), (x + ca * r * 0.85, y + sa * r * 0.85, r * 0.25)]
        tube(f"{prefix}Talon{k}", pts, r * 0.2, M["iron"], res=3)
        cone(f"{prefix}Nail{k}", r * 0.12, 0.0, r * 0.3, (x + ca * r * 0.8, y + sa * r * 0.8, r * 0.12), M["iron"], verts=6, rot=(math.pi, 0, 0))


def scroll_leg(prefix, pts, ang, mat, thick=0.055, square=True):
    """A leg along a path given in a radial (r, z) plane, turned to angle `ang` about Z."""
    c, s = math.cos(ang), math.sin(ang)
    return tube(prefix, [(c * r, s * r, z) for r, z in pts], thick, mat, square=square, res=5)


def volute(prefix, cx, cy, cz, r, ang, mat, thick=0.03, turns=1.4, n=16):
    """A flat spiral scroll in the vertical plane through angle `ang` (a curl at the end of a leg or bracket)."""
    c, s = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n + 1):
        t = i / n
        a = t * turns * 2 * math.pi
        rr = r * (1 - 0.72 * t)
        pts.append((cx + c * math.cos(a) * rr, cy + s * math.cos(a) * rr, cz + math.sin(a) * rr))
    return tube(prefix, pts, thick, mat, square=True, res=2)


def rosette(name, loc, r, mat, face="Y"):
    """A small carved rosette: a flattened boss with petals round it, facing -Y."""
    x, y, z = loc
    sphere(f"{name}Boss", r * 0.4, (x, y, z), mat, seg=10, rings=5, scale=(1, 0.5, 1))
    for k in range(6):
        a = k / 6 * 2 * math.pi
        sphere(f"{name}Petal{k}", r * 0.32, (x + math.cos(a) * r * 0.62, y + 0.004, z + math.sin(a) * r * 0.62), mat, seg=8, rings=4,
               scale=(1, 0.4, 0.7))


def ellipse_pts(rx, ry, z, n):
    return [(math.cos(i / n * 2 * math.pi) * rx, math.sin(i / n * 2 * math.pi) * ry, z) for i in range(n)]


# ================================================================== round table
def table_round(M):
    T = 3.0
    # fewer, finer, calmer veins than the other tables' marble
    blk = marble("MarbleBlackFine", base=(0.03, 0.028, 0.034), vein=(0.42, 0.4, 0.36), scale=0.45, width=0.011, distortion=3.5, detail=3.0)
    # the marble top, a moulded edge and a gilt rim
    lathe("Top", [(0, T - 0.15), (1.9, T - 0.15), (1.96, T - 0.12), (2.0, T - 0.07), (1.98, T - 0.02), (1.95, T), (0, T)], blk, seg=72)
    hoop("Rim", (0, 0, T - 0.075), 2.005, "Z", M["brass"], thick=0.022)
    hoop("RimLow", (0, 0, T - 0.145), 1.91, "Z", M["brass"], thick=0.016)
    # an iron apron under the top with gilt quatrefoils and a gilt bead
    ring_band("Apron", 1.52, 1.58, T - 0.5, T - 0.15, M["iron"], seg=64)
    hoop("ApronBead", (0, 0, T - 0.5), 1.585, "Z", M["brass"], thick=0.018)
    for k in range(10):
        m = _mark()
        foil(f"ApronFoil{k}", 0, -1.6, T - 0.325, 0.11, M["brass"], thick=0.014, n=8)
        _xform(m, Matrix.Rotation(k / 10 * 2 * math.pi, 4, "Z"))
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        scroll_leg(f"Brace{k}", [(0.2, T - 1.0), (0.7, T - 0.62), (1.4, T - 0.5)], a, M["iron"], thick=0.03)
    # the fluted pedestal, a bulb, gilt bands
    lathe("PedFoot", [(0, 0.5), (0.42, 0.5), (0.4, 0.62), (0.28, 0.78), (0.24, 0.9), (0, 0.9)], M["iron"], seg=40)
    lathe("Pedestal", [(0, 0.88), (0.24, 0.88), (0.17, 1.2), (0.15, 1.6), (0.24, 1.9), (0.25, 2.05), (0.16, 2.3), (0.14, T - 0.7),
                       (0, T - 0.7)], M["iron"], seg=48, flute=(14, 0.12))
    lathe("PedCap", [(0, T - 0.72), (0.2, T - 0.72), (0.32, T - 0.6), (0.55, T - 0.5), (0.6, T - 0.15), (0, T - 0.15)], M["iron"], seg=40)
    for z, r in ((0.9, 0.25), (1.98, 0.255), (T - 0.7, 0.16)):
        hoop(f"Band{z:.2f}", (0, 0, z), r, "Z", M["brass"], thick=0.02)
    # three scrolled legs with leaf knees and ball-and-claw feet
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        scroll_leg(f"Leg{k}", [(0.26, 0.78), (0.5, 0.95), (0.78, 0.88), (1.02, 0.58), (1.22, 0.36), (1.36, 0.27)], a, M["iron"], thick=0.085)
        c, s = math.cos(a), math.sin(a)
        volute(f"KneeCurl{k}", c * 0.42, s * 0.42, 0.76, 0.13, a + math.pi, M["iron"], thick=0.04)
        leaf(f"Knee{k}", (c * 0.62, s * 0.62, 0.99), a, math.radians(-38), 0.5, 0.1, 0.04, M["brass"], n=8, fold=0.4, thick=0.02)
        claw_foot(f"Foot{k}", c * 1.42, s * 1.42, a, M, r=0.13)
    return _dims()


# ================================================================== oval dining table
def table_oval(M):
    T = 3.0
    lq, vv = lacquer(), velvet()
    RX, RY = 4.0, 2.25
    sy = RY / RX
    lathe("Top", [(0, T - 0.13), (RX - 0.06, T - 0.13), (RX - 0.01, T - 0.1), (RX, T - 0.06), (RX - 0.02, T), (0, T)], lq, seg=80,
          scale=(1, sy))
    # gilt stringing: a moulded edge band and an inlaid line just proud of the top
    tube("EdgeGilt", ellipse_pts(RX + 0.004, RY + 0.004, T - 0.06, 72), 0.02, M["brass"], closed=True, poly=True)
    tube("String", ellipse_pts(RX - 0.28, RY - 0.28, T - 0.003, 72), 0.012, M["brass"], closed=True, square=True, poly=True)
    tube("String2", ellipse_pts(RX - 0.36, RY - 0.36, T - 0.003, 72), 0.006, M["brass"], closed=True, square=True, poly=True)
    # the apron, with a gilt bead along its foot
    lathe("Apron", [(RX - 0.4, T - 0.5), (RX - 0.4, T - 0.13), (RX - 0.48, T - 0.13), (RX - 0.48, T - 0.5), (RX - 0.4, T - 0.5)], lq,
          seg=72, scale=(1, (RY - 0.4) / (RX - 0.4)))
    tube("ApronBead", ellipse_pts(RX - 0.395, RY - 0.395, T - 0.5, 72), 0.016, M["brass"], closed=True, poly=True)
    # the velvet runner with gilt fringes
    box("Runner", (6.0, 1.0, 0.02), (0, 0, T + 0.01), vv, bevel=0.004)
    for sx in (-1, 1):
        box(f"RunnerBand{sx}", (0.06, 1.0, 0.024), (sx * 2.88, 0, T + 0.012), M["brass"], bevel=0.004)
        for k in range(9):
            y = -0.44 + k * 0.11
            box(f"Fringe{sx}{k}", (0.1, 0.04, 0.02), (sx * 3.05, y, T + 0.01), M["brass"], bevel=0.004)
        tube(f"RunnerLine{sx}", [(-2.8, sx * 0.42, T + 0.021), (2.8, sx * 0.42, T + 0.021)], 0.008, M["brass"], square=True, poly=True)
    # twin turned pedestals, each on four splayed legs with brass paw caps
    for px in (-2.1, 2.1):
        lathe(f"Ped{px}", [(0, 0.55), (0.3, 0.55), (0.27, 0.7), (0.18, 0.85), (0.3, 1.25), (0.32, 1.45), (0.2, 1.7), (0.15, 2.1),
                           (0.22, 2.3), (0.28, T - 0.5), (0, T - 0.5)], lq, seg=40, loc=(px, 0, 0))
        for z, r in ((0.56, 0.3), (1.35, 0.33), (2.3, 0.225)):
            hoop(f"PedBand{px}{z}", (px, 0, z), r, "Z", M["brass"], thick=0.018)
        box(f"PedBlock{px}", (0.5, 0.5, 0.25), (px, 0, 0.55), lq, bevel=0.03)
        for k in range(4):
            a = k / 4 * 2 * math.pi + math.pi / 4
            c, s = math.cos(a), math.sin(a)
            tube(f"PedLeg{px}{k}", [(px + c * 0.2, s * 0.2, 0.62), (px + c * 0.6, s * 0.6, 0.38), (px + c * 1.0, s * 1.0, 0.18)], 0.085, lq,
                 square=True, res=5)
            tube(f"PedLegGilt{px}{k}", [(px + c * 0.24, s * 0.24, 0.7), (px + c * 0.6, s * 0.6, 0.47), (px + c * 0.95, s * 0.95, 0.24)],
                 0.012, M["brass"], res=5)
            lathe(f"Paw{px}{k}", [(0, 0), (0.12, 0), (0.13, 0.06), (0.1, 0.18), (0.08, 0.24), (0, 0.24)], M["brass"], seg=16,
                  loc=(px + c * 1.03, s * 1.03, 0))
        tube(f"Bearer{px}", [(px, -1.5, T - 0.5), (px, 1.5, T - 0.5)], 0.07, lq, square=True, poly=True)
    tube("Spine", [(-2.1, 0, T - 0.56), (2.1, 0, T - 0.56)], 0.06, lq, square=True, poly=True)
    return _dims()


# ================================================================== banquet table
def table_banquet(M):
    T = 3.0
    st, pw, wax, vv = dark_stone(), pewter(), wax_mat(), velvet()
    L, D = 16.0, 3.5
    # the slab: a thick top course with a broad chamfer over a recessed lower course and a rounded ovolo between
    box("Slab", (L, D, 0.24), (0, 0, T - 0.12), st, bevel=0.07, segments=1)
    box("SlabUnder", (L - 0.24, D - 0.24, 0.14), (0, 0, T - 0.31), st, bevel=0.03)
    tube("Ovolo", rrect(L / 2 - 0.1, D / 2 - 0.1, 0.12, T - 0.245, n=3), 0.05, st, closed=True, poly=True)
    # a riveted iron strap round the lower course
    for sy in (-1, 1):
        box(f"StrapX{sy}", (L - 0.36, 0.03, 0.1), (0, sy * (D / 2 - 0.105), T - 0.31), M["iron"], bevel=0.008)
        for k in range(27):
            x = -L / 2 + 0.5 + k * (L - 1.0) / 26
            sphere(f"RivetX{sy}{k}", 0.024, (x, sy * (D / 2 - 0.088), T - 0.31), M["iron"], seg=6, rings=2)
    for sx in (-1, 1):
        box(f"StrapY{sx}", (0.03, D - 0.36, 0.1), (sx * (L / 2 - 0.105), 0, T - 0.31), M["iron"], bevel=0.008)
        for k in range(5):
            y = -D / 2 + 0.5 + k * (D - 1.0) / 4
            sphere(f"RivetY{sx}{k}", 0.024, (sx * (L / 2 - 0.088), y, T - 0.31), M["iron"], seg=6, rings=2)
    zt = T - 0.38               # underside of the slab
    # three heavy gothic iron trestles, built in the XZ plane and turned to run across the depth
    hw = D / 2 - 0.45
    for tx in (-6.0, 0.0, 6.0):
        m = _mark()
        y = 0.0
        box("TrFoot", (D - 0.3, 0.3, 0.22), (0, y, 0.11), M["iron"], bevel=0.03)
        for sx in (-1, 1):
            box(f"TrToe{sx}", (0.3, 0.36, 0.1), (sx * (D / 2 - 0.3), y, 0.05), M["iron"], bevel=0.02, segments=1)
            volute(f"TrScroll{sx}", sx * (D / 2 - 0.22), y, 0.38, 0.14, 0.0 if sx > 0 else math.pi, M["iron"], thick=0.045, n=10)
        box("TrHead", (D - 0.5, 0.26, 0.2), (0, y, zt - 0.1), M["iron"], bevel=0.025)
        for sx in (-1, 1):
            x = sx * (hw + 0.06)
            box(f"TrPost{sx}", (0.22, 0.22, zt - 0.42), (x, y, 0.22 + (zt - 0.42) / 2), M["iron"], bevel=0.02)
            for z in (0.5, zt - 0.4):
                box(f"TrPostRing{sx}{z:.1f}", (0.27, 0.27, 0.07), (x, y, z), M["iron"], bevel=0.012, segments=1)
            sphere(f"TrBoss{sx}", 0.07, (x, y - 0.12, 1.3), M["brass"], seg=10, rings=5)
        # the openwork: a heavy pointed arch, two lancets under it, a quatrefoil roundel in the head, brass bosses
        za = zt - 0.24
        tube("TrArch", _arch_loop(0, y, hw - 0.06, 0.22, 1.25, za), 0.09, M["iron"], square=True, closed=True, poly=True)
        tube("TrMullion", [(0, y, 0.22), (0, y, 1.62)], 0.07, M["iron"], square=True, poly=True)
        lh = (hw - 0.06) / 2 - 0.09
        for sx in (-1, 1):
            tube(f"TrLancet{sx}", _arch_loop(sx * (hw - 0.06) / 2, y, lh, 0.22, 1.1, 1.62), 0.06, M["iron"], square=True, closed=True, poly=True)
            foil(f"TrLancetFoil{sx}", sx * (hw - 0.06) / 2, y, 1.32, lh * 0.55, M["iron"], lobes=3, thick=0.035, n=6, centre=False)
        hoop("TrRoundel", (0, y, 2.05), 0.3, "Y", M["iron"], thick=0.055)
        foil("TrFoil", 0, y, 2.05, 0.2, M["iron"], lobes=4, thick=0.045, n=10)
        sphere("TrCentre", 0.07, (0, y - 0.07, 2.05), M["brass"], seg=10, rings=5)
        for sx in (-1, 1):
            tube(f"TrSpandrel{sx}", [(sx * 0.28, y, 2.25), (sx * (hw - 0.2), y, zt - 0.22)], 0.04, M["iron"], square=True, poly=True)
            sphere(f"TrSpBoss{sx}", 0.05, (sx * 0.62, y - 0.06, 1.62), M["brass"], seg=8, rings=4)
        _xform(m, Matrix.Translation((tx, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    # the riveted flat-bar stretcher with collars where it meets each trestle
    box("Stretcher", (12.0, 0.12, 0.26), (0, 0, 0.62), M["iron"], bevel=0.015)
    for sy in (-1, 1):
        for k in range(24):
            x = -5.75 + k * 0.5
            if abs(abs(x) - 6.0) < 0.3 or abs(x) < 0.3:
                continue
            sphere(f"StrRivet{sy}{k}", 0.026, (x, sy * 0.065, 0.62), M["iron"], seg=6, rings=2)
    for tx in (-6.0, 0.0, 6.0):
        box(f"Collar{tx}", (0.34, 0.34, 0.36), (tx, 0, 0.62), M["iron"], bevel=0.03)
    for tx in (-3.0, 3.0):
        box(f"StretchBand{tx}", (0.1, 0.16, 0.3), (tx, 0, 0.62), M["brass"], bevel=0.012)
    # a crimson velvet runner down the middle, gilt-edged, with gilt fringes
    RL = 13.0
    box("Runner", (RL, 1.2, 0.02), (0, 0, T + 0.01), vv, bevel=0.004)
    for sy in (-1, 1):
        tube(f"RunnerLine{sy}", [(-RL / 2 + 0.2, sy * 0.5, T + 0.021), (RL / 2 - 0.2, sy * 0.5, T + 0.021)], 0.01, M["brass"], square=True, poly=True)
    for sx in (-1, 1):
        box(f"RunnerBand{sx}", (0.08, 1.2, 0.026), (sx * (RL / 2 - 0.12), 0, T + 0.013), M["brass"], bevel=0.004)
        for k in range(11):
            box(f"Fringe{sx}{k}", (0.14, 0.045, 0.02), (sx * (RL / 2 + 0.06), -0.5 + k * 0.1, T + 0.01), M["brass"], bevel=0.0, segments=1)
    # a tall pewter candlestick pair with dripping candles
    tips = []
    zb = T + 0.02
    for cx in (-3.6, 3.6):
        lathe(f"Stick{cx}", [(0, zb), (0.3, zb), (0.3, zb + 0.05), (0.2, zb + 0.12), (0.1, zb + 0.24), (0.07, zb + 0.5), (0.12, zb + 0.6),
                             (0.07, zb + 0.7), (0.06, zb + 1.1), (0.1, zb + 1.18), (0.07, zb + 1.26), (0.08, zb + 1.32), (0.19, zb + 1.38),
                             (0.2, zb + 1.43), (0.08, zb + 1.44), (0, zb + 1.44)], pw, seg=24, loc=(cx, 0, 0))
        top = zb + 1.43
        tip = candle(f"Candle{cx}", cx, 0, top, 0.7, wax, r=0.06)
        for k, (a, dz, ln) in enumerate(((0.6, 0.18, 2.4), (2.4, 0.3, 3.2), (4.1, 0.12, 2.0))):
            sphere(f"Drip{cx}{k}", 0.024, (cx + math.cos(a) * 0.06, math.sin(a) * 0.06, top + 0.7 - dz - 0.04 * ln), wax, seg=6, rings=4,
                   scale=(1, 1, ln))
        lathe(f"WaxPool{cx}", [(0, top), (0.15, top), (0.13, top + 0.025), (0, top + 0.03)], wax, seg=16, loc=(cx, 0, 0))
        sphere(f"PanDrip{cx}", 0.03, (cx + 0.19, 0, top - 0.05), wax, seg=6, rings=4, scale=(1, 1, 2.2))
        tips.append((cx, tip))
    set_group("Glow")
    for cx, tip in tips:
        flame(f"Flame{cx}", (cx, 0, tip - 0.02), h=0.16)
    set_group("Main")
    return _dims()


# ================================================================== cafe table
def table_cafe(M):
    T = 2.7
    bm_ = bone_marble()
    W = 2.5
    prism("Top", [(x, y) for x, y, _ in rrect(W / 2, W / 2, 0.12, 0, n=4)], T - 0.1, 0.1, bm_, plane="XY", bevel=0.012)
    tube("Edge", rrect(W / 2 + 0.005, W / 2 + 0.005, 0.12, T - 0.05, n=4), 0.02, M["brass"], closed=True, poly=True)
    box("Frame", (1.4, 1.4, 0.08), (0, 0, T - 0.14), M["iron"], bevel=0.015)
    # a fluted column with a bowl under the top and a lotus foot
    lathe("Column", [(0, 0.42), (0.2, 0.42), (0.13, 0.6), (0.085, 0.9), (0.075, 1.9), (0.1, 2.1), (0, 2.1)], M["iron"], seg=32,
          flute=(10, 0.15))
    lathe("Bowl", [(0, 2.05), (0.1, 2.05), (0.2, 2.15), (0.34, 2.3), (0.4, T - 0.18), (0, T - 0.18)], M["iron"], seg=32)
    lathe("Knop", [(0, 1.05), (0.09, 1.05), (0.14, 1.15), (0.09, 1.25), (0, 1.25)], M["iron"], seg=24)
    for z in (0.6, 2.1):
        hoop(f"Band{z}", (0, 0, z), 0.13 if z < 1 else 0.11, "Z", M["brass"], thick=0.014)
    # four scrolled feet and four C-scroll brackets under the top
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        scroll_leg(f"Foot{k}", [(0.12, 0.5), (0.35, 0.36), (0.65, 0.2), (0.85, 0.12)], a, M["iron"], thick=0.045)
        volute(f"FootCurl{k}", c * 0.88, s * 0.88, 0.16, 0.1, a, M["iron"], thick=0.028)
        sphere(f"Toe{k}", 0.05, (c * 0.86, s * 0.86, 0.05), M["iron"], seg=8, rings=4)
        leaf(f"FootLeaf{k}", (c * 0.16, s * 0.16, 0.46), a, math.radians(-20), 0.34, 0.07, 0.04, M["iron"], n=6, fold=0.4, thick=0.016)
        scroll_leg(f"Bracket{k}", [(0.1, 1.95), (0.32, 2.2), (0.5, 2.48), (0.68, T - 0.18)], a, M["iron"], thick=0.026)
        volute(f"BracketCurl{k}", c * 0.3, s * 0.3, 2.12, 0.09, a + math.pi, M["iron"], thick=0.02)
    return _dims()


# ================================================================== hexagonal library table
def table_hexagon(M):
    T = 3.0
    lq = lacquer()
    R = 2.25
    hexp = [(math.cos(k / 6 * 2 * math.pi) * R, math.sin(k / 6 * 2 * math.pi) * R) for k in range(6)]
    prism("Top", hexp, T - 0.14, 0.14, lq, plane="XY", bevel=0.012)
    ri = R - 0.32
    prism("Leather", [(math.cos(k / 6 * 2 * math.pi) * ri, math.sin(k / 6 * 2 * math.pi) * ri) for k in range(6)], T - 0.02, 0.026,
          M["leather"], plane="XY", bevel=0.004)
    tube("LeatherTrim", [(math.cos(k / 6 * 2 * math.pi) * (ri + 0.02), math.sin(k / 6 * 2 * math.pi) * (ri + 0.02), T + 0.004) for k in range(6)],
         0.01, M["brass"], closed=True, square=True, poly=True)
    tube("Edge", [(math.cos(k / 6 * 2 * math.pi) * (R + 0.005), math.sin(k / 6 * 2 * math.pi) * (R + 0.005), T - 0.07) for k in range(6)],
         0.025, M["brass"], closed=True, square=True, poly=True)
    # the apron: six panels of blind tracery between gilt-capped corner blocks
    ra = R - 0.3
    for k in range(6):
        a0, a1 = k / 6 * 2 * math.pi, (k + 1) / 6 * 2 * math.pi
        am = (a0 + a1) / 2
        side = ra  # hexagon side length equals its circumradius
        apo = ra * math.cos(math.pi / 6)
        m = _mark()
        box(f"Apron{k}", (side - 0.2, 0.06, 0.4), (0, -apo, T - 0.34), lq, bevel=0.008)
        for sx in (-1, 1):
            tube(f"ApronArch{k}{sx}", _arch_loop(sx * side * 0.22, -apo - 0.035, side * 0.17, T - 0.52, T - 0.34, T - 0.18), 0.012,
                 M["brass"], square=True, closed=True, poly=True)
        foil(f"ApronFoil{k}", 0, -apo - 0.035, T - 0.33, 0.08, M["brass"], thick=0.01, n=8)
        _xform(m, Matrix.Rotation(am - (-math.pi / 2), 4, "Z") @ Matrix.Rotation(0, 4, "Z"))
    # six turned iron legs at the corners
    rl = R - 0.42
    for k in range(6):
        a = k / 6 * 2 * math.pi
        x, y = math.cos(a) * rl, math.sin(a) * rl
        box(f"LegBlock{k}", (0.24, 0.24, 0.42), (x, y, T - 0.35), lq, bevel=0.02)
        sphere(f"LegStud{k}", 0.045, (math.cos(a) * (rl + 0.125), math.sin(a) * (rl + 0.125), T - 0.35), M["brass"], seg=8, rings=4)
        lathe(f"Leg{k}", [(0, 0), (0.085, 0), (0.1, 0.06), (0.07, 0.16), (0.075, 0.45), (0.11, 0.55), (0.07, 0.66), (0.065, 1.3),
                          (0.1, 1.5), (0.12, 1.62), (0.09, 1.74), (0.075, 2.3), (0.1, 2.45), (0.12, T - 0.56), (0, T - 0.56)],
              M["iron"], seg=20, loc=(x, y, 0))
        hoop(f"LegBand{k}", (x, y, 1.62), 0.122, "Z", M["brass"], thick=0.012)
    # a hexagonal stretcher with spokes to a central boss
    zs = 0.55
    tube("Stretcher", [(math.cos(k / 6 * 2 * math.pi) * rl, math.sin(k / 6 * 2 * math.pi) * rl, zs) for k in range(6)], 0.04, M["iron"],
         closed=True, square=True, poly=True)
    for k in range(6):
        a = k / 6 * 2 * math.pi
        tube(f"Spoke{k}", [(math.cos(a) * rl, math.sin(a) * rl, zs), (math.cos(a) * 0.2, math.sin(a) * 0.2, zs)], 0.03, M["iron"],
             square=True, poly=True)
    lathe("Boss", [(0, zs - 0.18), (0.08, zs - 0.18), (0.22, zs - 0.06), (0.24, zs + 0.04), (0.14, zs + 0.12), (0.05, zs + 0.3),
                   (0.08, zs + 0.36), (0, zs + 0.42)], M["iron"], seg=24)
    sphere("BossFinial", 0.06, (0, 0, zs + 0.44), M["brass"], seg=10, rings=5)
    return _dims()


# ================================================================== demilune console
def table_demilune(M):
    T = 3.0
    bm_, gd, lq = bone_marble(), gilt(), lacquer()
    R, YB = 2.0, 1.0           # radius; the flat back on the wall at y = +YB, the arc reaching y = YB - R
    n = 40
    arc = [(math.cos(math.pi + i / n * math.pi) * R, YB + math.sin(math.pi + i / n * math.pi) * R) for i in range(n + 1)]
    prism("Top", arc, T - 0.12, 0.12, bm_, plane="XY", bevel=0.012)
    tube("TopEdge", [(x * 1.003, YB + (y - YB) * 1.003, T - 0.06) for x, y in arc], 0.018, M["brass"], poly=True)
    # the carved gilt apron along the arc, with rosettes and a quatrefoil roundel at the front
    ra = R - 0.15
    rows = []
    for z in (T - 0.52, T - 0.12):
        rows.append([(math.cos(math.pi + i / n * math.pi) * ra, YB + math.sin(math.pi + i / n * math.pi) * ra, z) for i in range(n + 1)])
    _mesh("Apron", rows, gd, 0.05)
    tube("ApronBead", [(math.cos(math.pi + i / n * math.pi) * (ra + 0.035), YB + math.sin(math.pi + i / n * math.pi) * (ra + 0.035), T - 0.5)
                       for i in range(n + 1)], 0.018, M["brass"], poly=True)
    tube("ApronMould", [(math.cos(math.pi + i / n * math.pi) * (ra + 0.03), YB + math.sin(math.pi + i / n * math.pi) * (ra + 0.03), T - 0.16)
                        for i in range(n + 1)], 0.016, M["brass"], poly=True)
    box("BackRail", (2 * R - 0.1, 0.08, 0.4), (0, YB - 0.05, T - 0.32), lq, bevel=0.01)
    for k in range(7):
        a = math.pi + (k + 0.5) / 7 * math.pi
        m = _mark()
        if k == 3:
            # a gilt quatrefoil in a roundel at the centre of the front
            hoop("FrontRoundel", (0, -ra - 0.05, T - 0.32), 0.15, "Y", gd, thick=0.016)
            foil("FrontFoil", 0, -ra - 0.06, T - 0.32, 0.11, gd, lobes=4, thick=0.018, n=10)
            sphere("FrontBoss", 0.035, (0, -ra - 0.07, T - 0.32), gd, seg=8, rings=4)
            for sx in (-1, 1):
                volute(f"FrontScroll{sx}", sx * 0.27, -ra - 0.06, T - 0.3, 0.08, 0.0 if sx > 0 else math.pi, gd, thick=0.016)
        else:
            rosette(f"Rose{k}", (0, -ra - 0.04, T - 0.32), 0.09, gd)
        _xform(m, Matrix.Translation((0, YB, 0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    # four matching cabriole legs in black lacquer with gilt mounts: two at the front, two at the ends by the wall
    satin = flat("SatinLacquer", (0.012, 0.011, 0.014), 0.58, wear=0.0, dirt=0.5)
    legs = []
    r0 = ra - 0.1
    for k, a in enumerate((math.pi + 0.1 * math.pi, math.pi + 0.3 * math.pi, math.pi + 0.7 * math.pi, math.pi + 0.9 * math.pi)):
        c, s_ = math.cos(a), math.sin(a)
        x0, y0 = c * r0, YB + s_ * r0
        pts = []
        for i in range(11):
            t = i / 10
            out = 0.17 * math.sin(min(t * 1.35, 1.0) * math.pi) - 0.05 * t + (0.07 * (t - 0.85) / 0.15 if t > 0.85 else 0.0)
            pts.append((x0 + c * out, y0 + s_ * out, (T - 0.52) * (1 - t) + 0.12 * t))
        tube(f"Leg{k}", pts, 0.085, satin, res=4)
        # gilt mounts: a knee rosette, a gilt line down the front, a gilt sabot toe
        m = _mark()
        rosette(f"Knee{k}", (0, 0, 0), 0.09, gd)
        _xform(m, Matrix.Translation((x0 + c * 0.2, y0 + s_ * 0.2, T - 0.72)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        tube(f"LegLine{k}", [(x + c * 0.085, y + s_ * 0.085, z) for x, y, z in pts[2:9]], 0.012, gd, res=4)
        fx, fy = pts[-1][0], pts[-1][1]
        lathe(f"Sabot{k}", [(0, 0), (0.1, 0), (0.11, 0.05), (0.085, 0.14), (0.095, 0.16), (0, 0.16)], gd, seg=16, loc=(fx, fy, 0))
        legs.append((x0, y0))
    # a gilt stretcher swooping between the front legs to an urn finial, tied back to the rail by the wall
    (xa, ya), (xb, yb) = legs[1], legs[2]
    zs = 0.7
    tube("Stretcher", [(xa, ya, zs), (xa * 0.5, ya - 0.18, zs - 0.12), (0, ya - 0.24, zs - 0.16), (xb * 0.5, yb - 0.18, zs - 0.12), (xb, yb, zs)],
         0.03, gd, res=5)
    tube("StretcherBack", [(0, ya - 0.24, zs - 0.16), (0, YB - 0.1, zs - 0.16)], 0.025, gd, poly=True)
    for (x1, y1), (x2, y2) in ((legs[0], legs[1]), (legs[2], legs[3])):
        tube(f"SideStretcher{x1:.2f}", [(x1, y1, zs + 0.05), ((x1 + x2) / 2 * 1.04, (y1 + y2) / 2 - 0.05, zs - 0.03), (x2, y2, zs + 0.05)], 0.022, gd, res=5)
    lathe("Urn", [(0, zs - 0.18), (0.06, zs - 0.18), (0.12, zs - 0.1), (0.13, zs), (0.07, zs + 0.08), (0.09, zs + 0.12), (0.03, zs + 0.18),
                  (0, zs + 0.24)], gd, seg=16, loc=(0, ya - 0.24, 0))
    return _dims()


# ================================================================== coffee table
def table_coffee(M):
    T = 1.5
    lq = lacquer()
    W, D = 4.0, 2.2
    # the brass rim holding the glass, flush with it
    for sy in (-1, 1):
        box(f"RimX{sy}", (W, 0.08, 0.08), (0, sy * (D / 2 - 0.04), T - 0.04), M["brass"], bevel=0.012)
    for sx in (-1, 1):
        box(f"RimY{sx}", (0.08, D - 0.16, 0.08), (sx * (W / 2 - 0.04), 0, T - 0.04), M["brass"], bevel=0.012)
    box("Under", (W - 0.1, D - 0.1, 0.05), (0, 0, T - 0.105), M["iron"], bevel=0.01)
    # black iron legs with brass sabots and collars, and a lattice of iron straps on the ends
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.1), sy * (D / 2 - 0.1)
            box(f"Leg{sx}{sy}", (0.1, 0.1, T - 0.25), (x, y, 0.12 + (T - 0.25) / 2), M["iron"], bevel=0.012)
            lathe(f"Sabot{sx}{sy}", [(0, 0), (0.07, 0), (0.08, 0.04), (0.065, 0.14), (0.075, 0.16), (0, 0.16)], M["brass"], seg=16, loc=(x, y, 0))
            box(f"Collar{sx}{sy}", (0.13, 0.13, 0.05), (x, y, T - 0.16), M["brass"], bevel=0.008)
            box(f"Collar2{sx}{sy}", (0.13, 0.13, 0.05), (x, y, 0.42), M["brass"], bevel=0.008)
        x = sx * (W / 2 - 0.1)
        tube(f"EndX{sx}a", [(x, -(D / 2 - 0.1), 0.48), (x, D / 2 - 0.1, T - 0.2)], 0.022, M["iron"], square=True, poly=True)
        tube(f"EndX{sx}b", [(x, D / 2 - 0.1, 0.48), (x, -(D / 2 - 0.1), T - 0.2)], 0.022, M["iron"], square=True, poly=True)
        sphere(f"EndBoss{sx}", 0.05, (x, 0, (0.48 + T - 0.2) / 2), M["brass"], seg=10, rings=5)
    for sy in (-1, 1):
        tube(f"Apron{sy}", [(-(W / 2 - 0.1), sy * (D / 2 - 0.1), T - 0.2), (W / 2 - 0.1, sy * (D / 2 - 0.1), T - 0.2)], 0.03, M["iron"],
             square=True, poly=True)
    # the lacquer shelf below, brass-edged, with books
    box("Shelf", (W - 0.2, D - 0.2, 0.06), (0, 0, 0.42), lq, bevel=0.01)
    for sy in (-1, 1):
        box(f"ShelfEdge{sy}", (W - 0.18, 0.025, 0.07), (0, sy * (D / 2 - 0.1), 0.42), M["brass"], bevel=0.006)
    z0 = 0.45
    stack = [(0.9, 0.62, 0.1, M["leather"]), (0.82, 0.58, 0.08, M["inkblue"]), (0.74, 0.54, 0.09, M["leatherdark"])]
    z = z0
    for i, (w, d, t, cov) in enumerate(stack):
        m = _mark()
        _book(f"Book{i}", w, d, t, cov, M, corners=(i == 0))
        _xform(m, Matrix.Translation((-0.9, 0.05, z)) @ Matrix.Rotation(math.radians(8 - i * 9), 4, "Z"))
        z += t
    m = _mark()
    _book("BookLone", 0.7, 0.5, 0.07, M["inkblue"], M, clasp=True)
    _xform(m, Matrix.Translation((0.95, -0.15, z0)) @ Matrix.Rotation(math.radians(-14), 4, "Z"))
    # the smoked glass top
    set_group("Glass")
    smoke = P.material("SmokedGlass", base=(0.06, 0.06, 0.07), rough=0.05, wear=0.0, dirt=0.0)
    box("GlassTop", (W - 0.16, D - 0.16, 0.04), (0, 0, T - 0.02), smoke, bevel=0.0, segments=1)
    set_group("Main")
    return _dims()


# ================================================================== tripod side table
def table_side(M):
    T = 2.5
    bm_ = bone_marble()
    R = 0.78
    lathe("Top", [(0, T - 0.08), (R - 0.02, T - 0.08), (R, T - 0.05), (R - 0.01, T), (0, T)], bm_, seg=48)
    hoop("TopEdge", (0, 0, T - 0.045), R + 0.004, "Z", M["brass"], thick=0.014)
    # the brass gallery rail on little balusters
    hoop("Gallery", (0, 0, T + 0.1), R - 0.03, "Z", M["brass"], thick=0.014)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        x, y = math.cos(a) * (R - 0.03), math.sin(a) * (R - 0.03)
        lathe(f"Baluster{k}", [(0, T), (0.022, T), (0.022, T + 0.015), (0.012, T + 0.03), (0.02, T + 0.05), (0.012, T + 0.07), (0.018, T + 0.09), (0, T + 0.1)], M["brass"], seg=8,
              loc=(x, y, 0))
    lathe("Cap", [(0, T - 0.24), (0.1, T - 0.24), (0.22, T - 0.14), (0.3, T - 0.08), (0, T - 0.08)], M["iron"], seg=24)
    lathe("Column", [(0, 0.42), (0.12, 0.42), (0.14, 0.5), (0.1, 0.62), (0.07, 0.9), (0.12, 1.15), (0.13, 1.3), (0.08, 1.5), (0.06, 2.05),
                     (0.08, T - 0.24), (0, T - 0.24)], M["iron"], seg=24)
    for z, r in ((0.55, 0.13), (1.3, 0.132), (2.05, 0.064)):
        hoop(f"Band{z}", (0, 0, z), r, "Z", M["brass"], thick=0.012)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        c, s = math.cos(a), math.sin(a)
        scroll_leg(f"Leg{k}", [(0.08, 0.6), (0.25, 0.42), (0.48, 0.18), (0.6, 0.08)], a, M["iron"], thick=0.04)
        volute(f"Curl{k}", c * 0.64, s * 0.64, 0.12, 0.08, a, M["iron"], thick=0.025)
        sphere(f"Toe{k}", 0.045, (c * 0.62, s * 0.62, 0.045), M["brass"], seg=8, rings=4)
        leaf(f"Knee{k}", (c * 0.11, s * 0.11, 0.62), a, math.radians(-30), 0.3, 0.07, 0.04, M["brass"], n=6, fold=0.4, thick=0.014)
    return _dims()


P.PREVIEW_PAD.update({"TableBanquet": 1.0, "TableCafe": 1.3, "TableSide": 1.3})

P.BUILD.update({
    "TableRound": table_round,
    "TableOval": table_oval,
    "TableBanquet": table_banquet,
    "TableCafe": table_cafe,
    "TableHexagon": table_hexagon,
    "TableDemilune": table_demilune,
    "TableCoffee": table_coffee,
    "TableSide": table_side,
})
