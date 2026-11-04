"""Props batch 16 (2026-11-04): the cafeteria's dining side for nh_props.py, for the school's cafe area. On theme with
the Institution: black lacquer, black marble with thin bone veins, cast and wrought iron, brass and gilt, crimson
leather, candlelight, and very little wood. Seats and table tops are flat and level.

  CafeteriaTable   a 10-long school dining table with two attached benches: a black lacquer top with a brass edge
                   (scuffs and carved initials), a lacquer apron with gilt quatrefoils, three gothic cast-iron trestles
                   (pointed arch, quatrefoil roundel, brass bosses) carrying the benches' crimson tufted leather pads,
                   and a riveted stretcher
  CafeChair        an ornate cast-iron bistro chair: four scrolled legs and a ring stretcher, a crimson leather
                   cushion, and a hoop back filled with scrolls under a gilt quatrefoil crest
  CafeBooth        a gothic high-backed booth: two facing crimson tufted leather benches whose tall black lacquer
                   backs carry gilt pointed arches, crocketed pinnacles and a crest, and a black marble table between
                   on two iron pedestals
  ChalkMenuStand   a standing A-frame chalkboard in an iron frame with a gilt crest: chalk scribble "writing", a
                   cup, a cake slice and a skull doodled on it, a chalk ledge with sticks
  CondimentCaddy   a table piece: a brass caddy with salt and pepper, a sauce bottle, a mustard pot with its spoon, a
                   napkin holder and a small candle (Glow: the flame)
  CakeStand        a table piece: a three-tier silver cake stand of black-iced cakes and raspberry tarts, the top cake
                   under a glass cloche (Glass)
  PendantLamp      a hanging iron cafe lamp: a ceiling rose, a chain, an iron-caged crimson glass shade (Glass) with a
                   gilt rim, and a bulb (Glow)

Front faces -Y, Z is up, the origin is at the bottom centre. Heights (studs): CafeteriaTable top 3.0, bench seats
1.82; CafeChair seat 1.88; CafeBooth seats 1.75, table top 2.9; PendantLamp chain top 3.8, ceiling rose top 4.0.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

from mathutils import Matrix

import nh_props as P
from nh_props import box, cyl, tube, set_group, _tufts
from nh_props_batch3 import sphere, cone, circle_pts, flame
from nh_props_batch4 import lathe, hoop, prism, rrect, _mark, _xform, _dims, flat
from nh_props_batch9 import foil, candle, wax_mat
from nh_props_batch10 import gilt, silver
from nh_props_batch5 import marble
from nh_props_batch13 import volute


# ------------------------------------------------------------------ materials

def lacquer():
    """Smooth black lacquer (as batch 13's tables): the painted-metal set blotches across a broad booth back."""
    return flat("BlackLacquerSmooth", (0.022, 0.02, 0.025), 0.22, wear=0.1, dirt=0.55)


def chalkboard():
    return P.material("ChalkSlate", "NH_Slate", tint=(0.1, 0.11, 0.105), scale=0.3, rough_mul=0.5, rough_add=0.45, normal=0.25, wear=0.1, dirt=0.4)


def chalk():
    return flat("ChalkLine", (0.86, 0.85, 0.8), 0.95, dirt=0.1)


def scratch():
    return flat("Scratch", (0.17, 0.14, 0.12), 0.75, dirt=0.3)


def porcelain(dark=False):
    return flat("PorcelainBlack" if dark else "Porcelain", (0.03, 0.03, 0.035) if dark else (0.86, 0.84, 0.79), 0.22, dirt=0.4)


# ------------------------------------------------------------------ helpers

def arch_curve(cx, y, hw, zs, za, n=6):
    """A pointed arch from the left springing (cx - hw, zs) over the apex za to the right springing, in XZ at y."""
    pts = []
    for tt in [i / n for i in range(0, n + 1)]:
        pts.append((cx - hw + hw * math.sin(tt * math.pi / 2) ** 0.9, y, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    for tt in [i / n for i in range(n - 1, -1, -1)]:
        pts.append((cx + hw - hw * math.sin(tt * math.pi / 2) ** 0.9, y, zs + (za - zs) * (1 - math.cos(tt * math.pi / 2))))
    return pts


def scrawl(prefix, pts, mat, r=0.013):
    tube(prefix, pts, r, mat, square=True, poly=True)


def raspberry(name, loc, r, mat):
    sphere(name, r, loc, mat, seg=8, rings=6, scale=(1, 1, 1.15))


# ================================================================== cafeteria table
def _trestle(M, iron, boss):
    """One trestle built in the XZ plane spanning x -2.95..2.95 (it is turned to span Y by the caller)."""
    box("Foot", (5.9, 0.22, 0.14), (0, 0, 0.07), iron, bevel=0.03)
    for sx in (-1, 1):
        box(f"Toe{sx}", (0.3, 0.3, 0.08), (sx * 2.85, 0, 0.04), iron, bevel=0.025)
        box(f"Post{sx}", (0.13, 0.15, 2.66), (sx * 0.55, 0, 1.47), iron, bevel=0.02)
        box(f"Arm{sx}", (2.3, 0.13, 0.11), (sx * 1.75, 0, 1.565), iron, bevel=0.02)
        box(f"Leg{sx}", (0.11, 0.13, 1.42), (sx * 2.78, 0, 0.85), iron, bevel=0.02)
        tube(f"Brace{sx}", [(sx * 0.62, 0, 0.75), (sx * 1.4, 0, 1.08), (sx * 2.2, 0, 1.5)], 0.032, iron, square=True)
        volute(f"Curl{sx}", sx * 2.45, 0, 0.55, 0.22, 0 if sx > 0 else math.pi, iron, thick=0.026)
        sphere(f"BossA{sx}", 0.06, (sx * 0.55, -0.08, 1.565), boss, seg=10, rings=5, scale=(1, 0.5, 1))
        sphere(f"BossB{sx}", 0.06, (sx * 0.55, 0.08, 1.565), boss, seg=10, rings=5, scale=(1, 0.5, 1))
    box("Beam", (2.8, 0.16, 0.12), (0, 0, 2.82), iron, bevel=0.02)
    tube("Arch", arch_curve(0, 0, 0.49, 1.75, 2.62), 0.04, iron, square=True, poly=True)
    tube("Sill", [(-0.49, 0, 1.75), (0.49, 0, 1.75)], 0.035, iron, square=True, poly=True)
    hoop("Roundel", (0, 0, 1.1), 0.34, "Y", iron, thick=0.035)
    foil("Foil", 0, 0, 1.1, 0.28, iron, lobes=4, thick=0.022, n=10, centre=False)
    sphere("FoilBoss", 0.07, (0, 0, 1.1), boss, seg=10, rings=6)


def cafeteria_table(M):
    lq, iron, brass = lacquer(), M["iron"], M["brass"]
    gl, leather, sc = gilt(), M["leather"], scratch()
    T = 3.0
    # the top and its brass edge
    box("Top", (10.0, 3.0, 0.12), (0, 0, T - 0.06), lq, bevel=0.02)
    for sy in (-1, 1):
        box(f"EdgeX{sy}", (10.06, 0.03, 0.1), (0, sy * 1.515, T - 0.05), brass, bevel=0.008)
    for sx in (-1, 1):
        box(f"EdgeY{sx}", (0.03, 3.06, 0.1), (sx * 5.015, 0, T - 0.05), brass, bevel=0.008)
    # the apron under it with gilt quatrefoils
    for sy in (-1, 1):
        box(f"Apron{sy}", (9.6, 0.06, 0.26), (0, sy * 1.3, T - 0.25), lq, bevel=0.012)
        box(f"Bead{sy}", (9.6, 0.02, 0.02), (0, sy * 1.333, T - 0.37), gl, bevel=0.0)
    for x in (-4.0, -2.0, 0.0, 2.0, 4.0):
        foil(f"ApronFoil{int(x)}", x, -1.34, T - 0.25, 0.1, gl, lobes=4, thick=0.012, n=8)
    for sx in (-1, 1):
        box(f"ApronEnd{sx}", (0.06, 2.6, 0.26), (sx * 4.8, 0, T - 0.25), lq, bevel=0.012)
    # three trestles
    for i, x in enumerate((-3.9, 0.0, 3.9)):
        s = _mark()
        _trestle(M, iron, brass)
        _xform(s, Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
    # the riveted stretcher
    box("Stretcher", (7.9, 0.1, 0.13), (0, 0, 0.75), iron, bevel=0.015)
    for k in range(-4, 5):
        if k in (-2, 0, 2):
            continue
        sphere(f"Rivet{k}", 0.025, (k * 0.88, -0.055, 0.75), iron, seg=6, rings=3, scale=(1, 0.5, 1))
    for x in (-3.9, 3.9):
        box(f"Collar{int(x)}", (0.16, 0.14, 0.18), (x * 0.96, 0, 0.75), brass, bevel=0.015)
    # the benches: a lacquer board, a crimson tufted leather pad
    for sy in (-1, 1):
        y = sy * 2.35
        box(f"Bench{sy}", (9.6, 1.0, 0.1), (0, y, 1.67), lq, bevel=0.02)
        box(f"BenchEdge{sy}", (9.62, 0.025, 0.06), (0, y + sy * 0.5, 1.67), brass, bevel=0.006)
        box(f"Pad{sy}", (9.4, 0.86, 0.08), (0, y, 1.76), leather, bevel=0.03)
        for i in range(16):
            for j in range(2):
                sphere(f"Tuft{sy}{i}{j}", 0.026, (-4.4 + i * 0.587, y - 0.2 + j * 0.4, 1.8), M["leatherdark"], seg=8, rings=4,
                       scale=(1, 1, 0.45))
    # scuffs and carved initials on the top (proud by a hair so the top stays flat)
    z = T + 0.004
    ox, oy = 2.6, -0.75
    scrawl("InitN", [(ox, oy, z), (ox, oy + 0.3, z), (ox + 0.2, oy, z), (ox + 0.2, oy + 0.3, z)], sc, 0.006)
    scrawl("InitH1", [(ox + 0.32, oy, z), (ox + 0.32, oy + 0.3, z)], sc, 0.006)
    scrawl("InitH2", [(ox + 0.52, oy, z), (ox + 0.52, oy + 0.3, z)], sc, 0.006)
    scrawl("InitH3", [(ox + 0.32, oy + 0.15, z), (ox + 0.52, oy + 0.15, z)], sc, 0.006)
    hx, hy = 3.5, -0.62
    heart = [(hx + 0.13 * math.sin(t) ** 3 * 1.6, hy + 0.1 * (0.8125 * math.cos(t) - 0.3125 * math.cos(2 * t) - 0.125 * math.cos(3 * t)
             - 0.0625 * math.cos(4 * t)) * 1.6, z) for t in [i / 16 * 2 * math.pi for i in range(17)]]
    scrawl("Heart", heart, sc, 0.006)
    scrawl("Arrow", [(hx - 0.25, hy - 0.2, z), (hx + 0.28, hy + 0.15, z)], sc, 0.005)
    scrawl("InitR", [(-3.1, 0.55, z), (-3.1, 0.82, z), (-2.95, 0.78, z), (-3.0, 0.69, z), (-3.1, 0.68, z), (-2.93, 0.55, z)], sc, 0.006)
    rnd = random.Random(16)
    for k in range(9):
        x, y = rnd.uniform(-4.5, 4.5), rnd.uniform(-1.3, 1.3)
        a, ln = rnd.uniform(0, math.pi), rnd.uniform(0.15, 0.5)
        scrawl(f"Scuff{k}", [(x, y, z), (x + math.cos(a) * ln * 0.5, y + math.sin(a) * ln * 0.5 + 0.02, z),
                             (x + math.cos(a) * ln, y + math.sin(a) * ln, z)], sc, 0.004)
    return _dims()


# ================================================================== cafe chair
def cafe_chair(M):
    iron, brass, gl, leather = M["iron"], M["brass"], gilt(), M["leather"]
    S = 1.7
    # seat ring and plate
    hoop("SeatRing", (0, 0, S), 0.7, "Z", iron, thick=0.035)
    lathe("SeatPlate", [(0, S - 0.02), (0.69, S - 0.02), (0.69, S + 0.02), (0, S + 0.02)], iron, seg=32)
    # the cushion
    lathe("Cushion", [(0, S + 0.02), (0.62, S + 0.02), (0.67, S + 0.06), (0.66, S + 0.13), (0.56, S + 0.175), (0.3, S + 0.18), (0, S + 0.18)],
          leather, seg=40)
    sphere("Button", 0.03, (0, 0, S + 0.17), M["leatherdark"], seg=8, rings=4, scale=(1, 1, 0.5))
    hoop("Piping", (0, 0, S + 0.085), 0.67, "Z", M["leatherdark"], thick=0.012)
    # four scrolled legs, a ring stretcher, C-scroll brackets under the seat
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        pts = [(c * 0.55, s * 0.55, S - 0.02), (c * 0.62, s * 0.62, 1.1), (c * 0.7, s * 0.7, 0.5), (c * 0.8, s * 0.8, 0.1), (c * 0.86, s * 0.86, 0.03)]
        tube(f"Leg{k}", pts, 0.035, iron, square=True)
        sphere(f"Foot{k}", 0.05, (c * 0.87, s * 0.87, 0.05), brass, seg=10, rings=5, scale=(1, 1, 0.8))
        volute(f"Bracket{k}", c * 0.42, s * 0.42, S - 0.22, 0.17, a, iron, thick=0.022)
    hoop("Stretcher", (0, 0, 0.55), 0.68, "Z", iron, thick=0.025)
    # the back: two posts, a hoop top rail, scrolls and a gilt crest
    yb = 0.62
    for sx in (-1, 1):
        tube(f"BackPost{sx}", [(sx * 0.46, 0.5, S), (sx * 0.46, 0.58, S + 0.8), (sx * 0.44, yb, S + 1.55)], 0.035, iron, square=True)
    rail = [(math.cos(t) * 0.44, yb + 0.02 * math.sin(t), S + 1.55 + math.sin(t) * 0.38) for t in [i / 14 * math.pi for i in range(15)]]
    tube("TopRail", rail, 0.035, iron, square=True)
    tube("MidRail", [(-0.46, 0.57, S + 0.55), (0, 0.6, S + 0.5), (0.46, 0.57, S + 0.55)], 0.028, iron, square=True)
    for sx in (-1, 1):
        volute(f"BackScrollA{sx}", sx * 0.2, 0.6, S + 0.92, 0.18, 0 if sx > 0 else math.pi, iron, thick=0.022)
        volute(f"BackScrollB{sx}", sx * 0.2, 0.61, S + 1.35, 0.15, math.pi if sx > 0 else 0, iron, thick=0.02)
    tube("Spine", [(0, 0.6, S + 0.5), (0, 0.62, S + 1.6)], 0.025, iron, square=True, poly=True)
    hoop("CrestRing", (0, yb - 0.02, S + 1.72), 0.13, "Y", gl, thick=0.018)
    foil("Crest", 0, yb - 0.03, S + 1.72, 0.11, gl, lobes=4, thick=0.014, n=8, centre=False)
    sphere("Finial", 0.045, (0, yb + 0.02, S + 1.97), brass, seg=10, rings=6)
    return _dims()


# ================================================================== cafe booth
def _booth_bench(M, s, lq, gl, leather, tuft):
    """One bench of the booth on side s (-1 front, +1 back); its seat faces the table (toward y = 0)."""
    W = 4.8
    yc = s * 2.15
    box(f"Base{s}", (W, 1.3, 1.45), (0, yc, 0.725), lq, bevel=0.03)
    yf = s * 1.5   # the base's face toward the table
    for k, x in enumerate((-1.6, 0.0, 1.6)):
        box(f"PanelTop{s}{k}", (1.3, 0.02, 0.02), (x, yf - s * 0.01, 1.2), gl, bevel=0.0)
        box(f"PanelBot{s}{k}", (1.3, 0.02, 0.02), (x, yf - s * 0.01, 0.25), gl, bevel=0.0)
        box(f"PanelL{s}{k}", (0.02, 0.02, 0.97), (x - 0.65, yf - s * 0.01, 0.725), gl, bevel=0.0)
        box(f"PanelR{s}{k}", (0.02, 0.02, 0.97), (x + 0.65, yf - s * 0.01, 0.725), gl, bevel=0.0)
    box(f"Kick{s}", (W + 0.02, 0.04, 0.12), (0, yf - s * 0.01, 0.06), gl, bevel=0.005)
    # the seat
    box(f"Seat{s}", (4.6, 1.2, 0.3), (0, s * 2.1, 1.6), leather, bevel=0.08)
    for i in range(7):
        for j in range(2):
            sphere(f"SeatTuft{s}{i}{j}", 0.03, (-1.95 + i * 0.65, s * (1.85 + j * 0.5), 1.75), tuft, seg=8, rings=4, scale=(1, 1, 0.5))
    # the tall back
    box(f"Back{s}", (W, 0.2, 3.6), (0, s * 2.9, 3.25), lq, bevel=0.03)
    box(f"BackCushion{s}", (4.5, 0.26, 1.55), (0, s * 2.67, 2.55), leather, bevel=0.09)
    for i in range(7):
        for j in range(3):
            sphere(f"BackTuft{s}{i}{j}", 0.03, (-1.95 + i * 0.65, s * 2.535, 2.0 + j * 0.55), tuft, seg=8, rings=4, scale=(1, 0.5, 1))
    yi = s * 2.79    # the back's inner face above the cushion
    for k, x in enumerate((-1.55, 0.0, 1.55)):
        tube(f"Arch{s}{k}", arch_curve(x, yi, 0.66, 3.55, 4.75), 0.03, gl, square=True, poly=True)
        tube(f"ArchSill{s}{k}", [(x - 0.66, yi, 3.45), (x + 0.66, yi, 3.45)], 0.025, gl, square=True, poly=True)
        tube(f"Mull{s}{k}", [(x, yi, 3.45), (x, yi, 4.1)], 0.02, gl, square=True, poly=True)
        tube(f"Sub{s}{k}", arch_curve(x - 0.33, yi, 0.3, 3.75, 4.12, n=4), 0.016, gl, square=True, poly=True)
        tube(f"Sub2{s}{k}", arch_curve(x + 0.33, yi, 0.3, 3.75, 4.12, n=4), 0.016, gl, square=True, poly=True)
        hoop(f"Oculus{s}{k}", (x, yi, 4.4), 0.17, "Y", gl, thick=0.016)
        foil(f"Foil{s}{k}", x, yi, 4.4, 0.14, gl, lobes=4, thick=0.012, n=8, centre=False)
    yo = s * 3.005   # the back's outer face
    for k, x in enumerate((-1.2, 1.2)):
        tube(f"OutArch{s}{k}", arch_curve(x, yo, 0.95, 4.0, 4.8), 0.022, gl, square=True, poly=True)
        tube(f"OutPanel{s}{k}", [(x - 0.95, yo, 4.0), (x - 0.95, yo, 1.7), (x + 0.95, yo, 1.7), (x + 0.95, yo, 4.0)], 0.022, gl, square=True, poly=True)
        hoop(f"OutBoss{s}{k}", (x, yo, 3.0), 0.16, "Y", gl, thick=0.016)
    box(f"OutPlinth{s}", (W + 0.02, 0.03, 0.04), (0, yo, 1.5), gl, bevel=0.0)
    # the cornice, pinnacles and crest
    box(f"Cornice{s}", (W + 0.1, 0.32, 0.14), (0, s * 2.9, 5.1), lq, bevel=0.03)
    box(f"CorniceGilt{s}", (W + 0.12, 0.02, 0.03), (0, s * 2.73, 5.05), gl, bevel=0.0)
    for sx in (-1, 1):
        box(f"PinBase{s}{sx}", (0.24, 0.24, 0.2), (sx * 2.3, s * 2.9, 5.27), lq, bevel=0.02)
        cone(f"Pin{s}{sx}", 0.11, 0.0, 0.55, (sx * 2.3, s * 2.9, 5.65), lq, verts=8)
        for kk, zz in enumerate((5.5, 5.68)):
            for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
                sphere(f"Crocket{s}{sx}{kk}{a:.1f}", 0.03, (sx * 2.3 + math.cos(a) * (0.1 - kk * 0.03), s * 2.9 + math.sin(a) * (0.1 - kk * 0.03), zz),
                       gl, seg=6, rings=3)
        sphere(f"PinTip{s}{sx}", 0.035, (sx * 2.3, s * 2.9, 5.95), gl, seg=8, rings=4)
    box(f"CrestPlinth{s}", (0.5, 0.26, 0.08), (0, s * 2.9, 5.21), lq, bevel=0.015)
    hoop(f"CrestRing{s}", (0, s * 2.9 - s * 0.17, 5.47), 0.22, "Y", gl, thick=0.025)
    foil(f"Crest{s}", 0, s * 2.9 - s * 0.17, 5.47, 0.18, gl, lobes=4, thick=0.016, n=8, centre=False)
    lathe(f"CrestDisc{s}", [(0, -0.03), (0.2, -0.03), (0.2, 0.03), (0, 0.03)], lq, seg=24)
    # turn the crest disc to stand up behind the ring
    ob = P.PARTS[-1]
    ob.matrix_world = Matrix.Translation((0, s * 2.9 - s * 0.12, 5.47)) @ Matrix.Rotation(math.pi / 2, 4, "X")
    # the open end panels (arms)
    for sx in (-1, 1):
        box(f"Arm{s}{sx}", (0.1, 1.3, 0.35), (sx * 2.45, s * 2.15, 2.0), lq, bevel=0.03)
        sphere(f"ArmKnob{s}{sx}", 0.06, (sx * 2.45, s * 1.5, 2.2), gl, seg=8, rings=5)


def cafe_booth(M):
    lq, gl, leather, iron, brass = lacquer(), gilt(), M["leather"], M["iron"], M["brass"]
    tuft = M["leatherdark"]
    s0 = _mark()
    for s in (-1, 1):
        _booth_bench(M, s, lq, gl, leather, tuft)
    # the table: black marble top, brass edge, two iron pedestals
    set_group("Table")
    blk = marble("MarbleBlackFine", base=(0.03, 0.028, 0.034), vein=(0.42, 0.4, 0.36), scale=0.45, width=0.011, distortion=3.5, detail=3.0)
    T = 2.9
    box("TableTop", (4.2, 1.8, 0.12), (0, 0, T - 0.06), blk, bevel=0.02)
    for sy in (-1, 1):
        box(f"TEdgeX{sy}", (4.24, 0.025, 0.09), (0, sy * 0.912, T - 0.06), brass, bevel=0.006)
    for sx in (-1, 1):
        box(f"TEdgeY{sx}", (0.025, 1.85, 0.09), (sx * 2.112, 0, T - 0.06), brass, bevel=0.006)
        x = sx * 1.4
        lathe(f"Pedestal{sx}", [(0.12, 0.12), (0.1, 0.4), (0.07, 0.8), (0.075, 1.5), (0.09, 2.2), (0.13, 2.65), (0.3, 2.78), (0.3, 2.84), (0, 2.84)],
              iron, seg=16, loc=(x, 0, 0), flute=(8, 0.12))
        hoop(f"Collar{sx}", (x, 0, 1.6), 0.085, "Z", brass, thick=0.02)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            c, s_ = math.cos(a), math.sin(a)
            tube(f"Foot{sx}{k}", [(x, 0, 0.2), (x + c * 0.3, s_ * 0.3, 0.12), (x + c * 0.55, s_ * 0.55, 0.04)], 0.04, iron, square=True)
            sphere(f"Toe{sx}{k}", 0.05, (x + c * 0.57, s_ * 0.57, 0.05), brass, seg=8, rings=4)
    set_group("Main")
    # turn it so the open end (the seats and the table) faces the front, as a booth is seen from the aisle
    _xform(s0, Matrix.Rotation(math.pi / 2, 4, "Z"))
    return _dims()


# ================================================================== chalk menu stand
def _menu_panel(M, board, ch, iron, gl, front=True):
    """One A-frame panel built upright at the origin (its board faces -Y, legs from z 0 to 4.3)."""
    H = 4.3
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.12, 0.1, H), (sx * 1.2, 0, H / 2), iron, bevel=0.02)
        sphere(f"StileCap{sx}", 0.07, (sx * 1.2, 0, H + 0.03), M["brass"], seg=8, rings=5)
        box(f"Shoe{sx}", (0.16, 0.14, 0.08), (sx * 1.2, 0, 0.04), iron, bevel=0.015)
    box("Board", (2.28, 0.05, 2.75), (0, 0.0, 2.35), board, bevel=0.01)
    for z in (0.95, 3.75):
        box(f"Rail{z:.0f}", (2.4, 0.09, 0.1), (0, 0, z), iron, bevel=0.015)
    box("Ledge", (2.3, 0.2, 0.05), (0, -0.09, 0.93), iron, bevel=0.01)
    box("LedgeLip", (2.3, 0.02, 0.05), (0, -0.19, 0.96), iron, bevel=0.0)
    # corner scrolls under the top rail and a pointed arch top with the crest
    for sx in (-1, 1):
        volute(f"Corner{sx}", sx * 0.95, -0.04, 3.5, 0.17, 0 if sx < 0 else math.pi, iron, thick=0.02)
    tube("TopArch", arch_curve(0, 0, 1.2, 3.8, 4.25), 0.035, iron, square=True, poly=True)
    yb = -0.045
    if not front:
        # the back board: a few lines only
        for k in range(4):
            z = 3.2 - k * 0.5
            scrawl(f"BackLine{k}", [(-0.8 + 0.05 * k, yb, z), (-0.2, yb, z + 0.03), (0.3, yb, z - 0.02), (0.75 - 0.1 * k, yb, z + 0.02)], ch, 0.012)
        return
    # the crest: a gilt shield with a crescent, in the arch
    shield = [(-0.2, 0.25), (0.2, 0.25), (0.2, 0.05), (0.14, -0.12), (0, -0.22), (-0.14, -0.12), (-0.2, 0.05)]
    prism("Shield", [(u, 3.95 + w) for u, w in shield], -0.06, 0.04, gl)
    cres = [(math.cos(t) * 0.1, -0.085, 3.95 + math.sin(t) * 0.1) for t in [math.pi * 0.35 + i / 10 * math.pi * 1.3 for i in range(11)]]
    tube("Crescent", cres, 0.018, M["iron"], poly=True)
    # chalk on the front board: a heading flourish, scribbled lines of "writing", and the doodles
    rnd = random.Random(23)
    head = [(-0.75 + i * 0.075, yb, 3.42 + 0.06 * math.sin(i * 1.3) + (0.05 if i % 3 == 0 else 0)) for i in range(21)]
    scrawl("Heading", head, ch, 0.016)
    scrawl("Underline", [(-0.85, yb, 3.25), (0, yb, 3.22), (0.85, yb, 3.26)], ch, 0.01)
    for k in range(7):
        z = 3.02 - k * 0.24
        x0, x1 = -0.95, rnd.uniform(-0.05, 0.35)
        n = 14
        line = [(x0 + (x1 - x0) * i / n, yb, z + 0.035 * math.sin(i * 2.1 + k) + rnd.uniform(-0.01, 0.01)) for i in range(n + 1)]
        scrawl(f"Line{k}", line, ch, 0.01)
        scrawl(f"Price{k}", [(0.62, yb, z - 0.03), (0.66, yb, z + 0.04), (0.72, yb, z - 0.02), (0.78, yb, z + 0.03)], ch, 0.01)
    # a cup with a saucer and steam
    cx, cz = 0.62, 2.55 + 0.3
    cup = [(cx - 0.14, yb, cz + 0.16), (cx - 0.13, yb, cz + 0.02), (cx - 0.07, yb, cz - 0.06), (cx + 0.07, yb, cz - 0.06), (cx + 0.13, yb, cz + 0.02),
           (cx + 0.14, yb, cz + 0.16), (cx - 0.14, yb, cz + 0.16)]
    scrawl("Cup", cup, ch, 0.011)
    scrawl("CupHandle", [(cx + 0.13, yb, cz + 0.12), (cx + 0.21, yb, cz + 0.11), (cx + 0.21, yb, cz + 0.04), (cx + 0.12, yb, cz + 0.03)], ch, 0.01)
    scrawl("Saucer", [(cx - 0.22, yb, cz - 0.08), (cx, yb, cz - 0.11), (cx + 0.22, yb, cz - 0.08)], ch, 0.01)
    for k, dx in enumerate((-0.05, 0.05)):
        scrawl(f"Steam{k}", [(cx + dx, yb, cz + 0.2 + i * 0.05) if i % 2 == 0 else (cx + dx + 0.04, yb, cz + 0.2 + i * 0.05) for i in range(5)], ch, 0.008)
    # a cake slice with a cherry
    kx, kz = 0.6, 1.55
    scrawl("Cake", [(kx - 0.2, yb, kz), (kx + 0.2, yb, kz), (kx + 0.2, yb, kz + 0.17), (kx - 0.2, yb, kz), (kx - 0.2, yb, kz)], ch, 0.011)
    scrawl("CakeLayer", [(kx - 0.08, yb, kz + 0.06), (kx + 0.2, yb, kz + 0.09)], ch, 0.008)
    hoop("Cherry", (kx + 0.2, yb, kz + 0.23), 0.04, "Y", ch, thick=0.01)
    # a skull
    sx_, sz_ = -0.55, 1.35
    hoop("Skull", (sx_, yb, sz_ + 0.12), 0.15, "Y", ch, thick=0.011)
    scrawl("Jaw", [(sx_ - 0.09, yb, sz_ + 0.0), (sx_ - 0.08, yb, sz_ - 0.1), (sx_ + 0.08, yb, sz_ - 0.1), (sx_ + 0.09, yb, sz_ + 0.0)], ch, 0.01)
    for k, dx in enumerate((-0.04, 0.0, 0.04)):
        scrawl(f"Tooth{k}", [(sx_ + dx, yb, sz_ - 0.02), (sx_ + dx, yb, sz_ - 0.09)], ch, 0.007)
    for k, dx in enumerate((-0.055, 0.055)):
        hoop(f"Eye{k}", (sx_ + dx, yb, sz_ + 0.13), 0.035, "Y", ch, thick=0.01)
    scrawl("Nose", [(sx_ - 0.015, yb, sz_ + 0.04), (sx_, yb, sz_ + 0.08), (sx_ + 0.015, yb, sz_ + 0.04)], ch, 0.008)
    # chalk sticks and a smudge on the ledge
    for k, (x, rot) in enumerate(((-0.6, 0.15), (-0.45, -0.3), (0.4, 0.05))):
        cyl(f"Stick{k}", 0.022, 0.22, (x, -0.1, 0.98), ch, rot=(0, math.pi / 2, rot), verts=8, bevel=0.004)
    scrawl("Smudge", [(-0.2, yb, 1.05), (0.1, yb, 1.1), (0.3, yb, 1.04)], ch, 0.02)


def chalk_menu_stand(M):
    board, ch, iron, gl = chalkboard(), chalk(), M["iron"], gilt()
    tilt = 0.2
    L = 4.3
    off = L * math.sin(tilt)   # each panel's foot sits this far out; the tops meet over y = 0
    s = _mark()
    _menu_panel(M, board, ch, iron, gl, front=True)
    _xform(s, Matrix.Translation((0, -off, 0)) @ Matrix.Rotation(-tilt, 4, "X") @ Matrix.Translation((0, 0, 0)))
    s = _mark()
    _menu_panel(M, board, ch, iron, gl, front=False)
    _xform(s, Matrix.Translation((0, off, 0)) @ Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(math.pi, 4, "Z"))
    # the hinge rod at the top and the spreader chains
    top = L * math.cos(tilt)
    tube("Hinge", [(-1.25, 0, top - 0.05), (1.25, 0, top - 0.05)], 0.03, iron, poly=True)
    for sx in (-1, 1):
        zc = 1.4
        dy = off - zc * math.tan(tilt)   # how far out each frame is at that height
        tube(f"Spreader{sx}", [(sx * 1.2, -dy + 0.06, zc), (sx * 1.2, 0, zc - 0.12), (sx * 1.2, dy - 0.06, zc)], 0.014, iron, res=3)
    return _dims()


# ================================================================== condiment caddy
def condiment_caddy(M):
    brass, slv, iron = M["brass"], silver(), M["iron"]
    white, black = porcelain(), porcelain(dark=True)
    sauce = flat("SauceRed", (0.22, 0.015, 0.02), 0.25, dirt=0.4)
    mustard = flat("MustardGlaze", (0.5, 0.33, 0.07), 0.3, dirt=0.4)
    napkin = flat("Napkin", (0.62, 0.05, 0.07), 0.9, dirt=0.3)
    # the caddy: a brass tray with a gallery and a centre handle
    prism("Base", [(x, y) for x, y, _ in rrect(0.45, 0.22, 0.06, 0)], 0.0, 0.035, brass, plane="XY")
    gal = [(x, y, 0.11) for x, y, _ in rrect(0.44, 0.21, 0.06, 0)]
    tube("Gallery", gal, 0.008, brass, closed=True, poly=True)
    for k, (x, y, _) in enumerate(rrect(0.44, 0.21, 0.06, 0, n=1)):
        tube(f"GalPost{k}", [(x, y, 0.035), (x, y, 0.11)], 0.008, brass, poly=True)
    for x in (-0.3, -0.15, 0.15, 0.3):
        for y in (-0.21, 0.21):
            tube(f"GalBar{x:.2f}{y:.1f}", [(x, y, 0.035), (x, y, 0.11)], 0.006, brass, poly=True)
    handle = [(0, -0.12, 0.035), (0, -0.12, 0.42), (0, -0.08, 0.56), (0, 0, 0.6), (0, 0.08, 0.56), (0, 0.12, 0.42), (0, 0.12, 0.035)]
    tube("Handle", handle, 0.014, brass)
    hoop("HandleRing", (0, 0, 0.66), 0.045, "X", brass, thick=0.01)
    # salt (white) and pepper (black) with silver caps
    for k, (x, y, mat) in enumerate(((-0.33, -0.09, white), (-0.2, -0.09, black))):
        lathe(f"Shaker{k}", [(0.045, 0.035), (0.05, 0.08), (0.04, 0.16), (0.038, 0.2), (0, 0.2)], mat, seg=16, loc=(x, y, 0))
        lathe(f"ShakerCap{k}", [(0.04, 0.2), (0.042, 0.23), (0.025, 0.26), (0, 0.27)], slv, seg=16, loc=(x, y, 0))
        for d in range(3):
            sphere(f"Hole{k}{d}", 0.005, (x - 0.008 + d * 0.008, y - 0.01, 0.265), black if mat is white else white, seg=4, rings=2)
    # the sauce bottle
    lathe("Sauce", [(0.055, 0.035), (0.06, 0.08), (0.06, 0.3), (0.045, 0.36), (0.02, 0.42), (0.018, 0.46), (0, 0.46)], sauce, seg=18,
          loc=(-0.28, 0.1, 0))
    lathe("SauceCap", [(0.022, 0.45), (0.024, 0.5), (0.008, 0.53), (0, 0.535)], iron, seg=12, loc=(-0.28, 0.1, 0))
    lathe("SauceLabel", [(0.062, 0.15), (0.062, 0.24)], flat("Label", (0.78, 0.72, 0.56), 0.8), seg=18, loc=(-0.28, 0.1, 0))
    # the mustard pot with its lid and spoon
    lathe("Mustard", [(0.05, 0.035), (0.06, 0.07), (0.06, 0.15), (0.052, 0.17), (0, 0.17)], mustard, seg=18, loc=(0.15, -0.09, 0))
    lathe("MustardLid", [(0.058, 0.17), (0.06, 0.185), (0.03, 0.21), (0.012, 0.215), (0.012, 0.24), (0, 0.245)], slv, seg=18, loc=(0.15, -0.09, 0))
    tube("MustardSpoon", [(0.19, -0.09, 0.18), (0.24, -0.09, 0.26)], 0.006, slv, poly=True)
    # the napkin holder with folded napkins
    for sy in (-1, 1):
        prism(f"NapkinSide{sy}", [(-0.13, 0.035), (0.13, 0.035), (0.13, 0.2), (0.07, 0.27), (-0.07, 0.27), (-0.13, 0.2)],
              0.1 + sy * 0.05, 0.012, iron)
    box("NapkinBase", (0.28, 0.12, 0.015), (0.26, 0.1, 0.045), iron, bevel=0.003)
    for k in range(6):
        box(f"Napkin{k}", (0.24, 0.012, 0.2), (0.26, 0.06 + k * 0.016, 0.15), napkin, bevel=0.003)
    # the candle in a small brass holder
    cx, cy = 0.35, -0.09
    lathe("CandleCup", [(0.045, 0.035), (0.05, 0.05), (0.04, 0.06), (0.04, 0.075), (0, 0.075)], brass, seg=16, loc=(cx, cy, 0))
    tip = candle("Candle", cx, cy, 0.075, 0.12, wax_mat(), r=0.03)
    set_group("Glow")
    flame("Flame", (cx, cy, tip - 0.005), h=0.08)
    set_group("Main")
    return _dims()


# ================================================================== cake stand
def cake_stand(M):
    slv = silver()
    icing = flat("IcingBlack", (0.025, 0.02, 0.03), 0.3, dirt=0.3)
    sponge = flat("SpongeDark", (0.17, 0.07, 0.04), 0.85, dirt=0.4)
    cream = flat("Cream", (0.86, 0.8, 0.68), 0.6, dirt=0.3)
    rasp = flat("Raspberry", (0.32, 0.015, 0.05), 0.45, dirt=0.2)
    pastry = flat("Pastry", (0.6, 0.4, 0.17), 0.8, dirt=0.4)
    gold = gilt()
    # the stand: foot, stem, three dished tiers with beaded rims, a ring finial
    lathe("Foot", [(0, 0), (0.32, 0), (0.33, 0.03), (0.22, 0.07), (0.08, 0.12), (0.05, 0.18), (0, 0.18)], slv, seg=36)
    tiers = ((0.35, 0.58), (0.8, 0.44), (1.2, 0.3))
    for i, (z, r) in enumerate(tiers):
        lathe(f"Tier{i}", [(0, z - 0.02), (r * 0.9, z - 0.01), (r, z + 0.035), (r * 1.02, z + 0.045), (r * 0.97, z + 0.035), (r * 0.88, z + 0.005),
                           (0, z + 0.005)], slv, seg=48)
        hoop(f"Bead{i}", (0, 0, z + 0.04), r * 1.0, "Z", slv, thick=0.008)
    lathe("Stem", [(0.03, 0.18), (0.025, 0.6), (0.035, 0.7), (0.022, 0.78), (0.022, 1.18), (0.03, 1.22), (0.02, 1.26), (0, 1.26)], slv, seg=16)
    for z in (0.33, 0.78):
        lathe(f"Knop{z:.2f}", [(0.02, z - 0.04), (0.05, z), (0.02, z + 0.04)], slv, seg=16)
    # bottom tier: six black-iced cakes with a raspberry each
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.3
        x, y, z = math.cos(a) * 0.4, math.sin(a) * 0.4, 0.355
        lathe(f"Cake{k}", [(0.1, z), (0.105, z + 0.08), (0, z + 0.08)], sponge, seg=16, loc=(x, y, 0))
        lathe(f"Icing{k}", [(0.11, z + 0.05), (0.112, z + 0.09), (0.09, z + 0.115), (0, z + 0.12)], icing, seg=16, loc=(x, y, 0))
        raspberry(f"CakeBerry{k}", (x, y, z + 0.145), 0.03, rasp)
        lathe(f"Dot{k}", [(0.025, z + 0.116), (0.02, z + 0.125), (0, z + 0.127)], cream, seg=10, loc=(x + 0.04, y, 0))
    # middle tier: four raspberry tarts
    for k in range(4):
        a = k / 4 * 2 * math.pi + 0.4
        x, y, z = math.cos(a) * 0.27, math.sin(a) * 0.27, 0.805
        lathe(f"Tart{k}", [(0.08, z), (0.11, z + 0.05), (0.105, z + 0.06), (0.08, z + 0.045), (0, z + 0.045)], pastry, seg=16, loc=(x, y, 0))
        lathe(f"TartCream{k}", [(0.08, z + 0.045), (0.075, z + 0.06), (0, z + 0.065)], cream, seg=14, loc=(x, y, 0))
        for b in range(5):
            bb = b / 5 * 2 * math.pi
            raspberry(f"TartBerry{k}{b}", (x + math.cos(bb) * 0.045, y + math.sin(bb) * 0.045, z + 0.085), 0.025, rasp)
        raspberry(f"TartBerryC{k}", (x, y, z + 0.1), 0.025, rasp)
    # top tier: a tall black cake crowned with raspberries, under a glass cloche
    z = 1.205
    lathe("TopCake", [(0.17, z), (0.172, z + 0.2), (0, z + 0.2)], sponge, seg=28)
    lathe("TopIcing", [(0.178, z + 0.06), (0.18, z + 0.2), (0.16, z + 0.225), (0, z + 0.23)], icing, seg=28)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        sphere(f"Drip{k}", 0.018, (math.cos(a) * 0.178, math.sin(a) * 0.178, z + 0.17 - (k % 3) * 0.02), icing, seg=6, rings=4, scale=(1, 0.6, 2.2))
    for k in range(7):
        a = k / 7 * 2 * math.pi
        raspberry(f"TopBerry{k}", (math.cos(a) * 0.1, math.sin(a) * 0.1, z + 0.255), 0.028, rasp)
    hoop("TopGold", (0, 0, z + 0.03), 0.173, "Z", gold, thick=0.008)
    lathe("DomeKnob", [(0.02, 1.62), (0.035, 1.65), (0.02, 1.69), (0.03, 1.71), (0, 1.73)], slv, seg=14)
    set_group("Glass")
    lathe("Dome", [(0.27, 1.24), (0.27, 1.38), (0.24, 1.5), (0.17, 1.58), (0.08, 1.62), (0, 1.625)], M["glassclear"], seg=32)
    set_group("Main")
    return _dims()


# ================================================================== pendant lamp
def pendant_lamp(M):
    iron, brass, gl = M["iron"], M["brass"], gilt()
    red = flat("CrimsonGlass", (0.5, 0.03, 0.05), 0.15, dirt=0.1)
    # the iron cap, cage ribs and gilt rim round the shade
    lathe("Cap", [(0.15, 0.6), (0.2, 0.62), (0.16, 0.68), (0.09, 0.74), (0.07, 0.8), (0.05, 0.84), (0, 0.85)], iron, seg=24)
    hoop("Rim", (0, 0, 0.02), 0.565, "Z", gl, thick=0.022)
    hoop("RimLow", (0, 0, 0.0), 0.56, "Z", iron, thick=0.015)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        c, s = math.cos(a), math.sin(a)
        pts = [(c * r, s * r, z) for r, z in ((0.57, 0.02), (0.53, 0.2), (0.43, 0.4), (0.28, 0.55), (0.17, 0.62))]
        tube(f"Rib{k}", pts, 0.012, iron, res=3)
        sphere(f"Drop{k}", 0.025, (c * 0.57, s * 0.57, -0.03), gl, seg=8, rings=5, scale=(1, 1, 1.4))
    hoop("Band", (0, 0, 0.32), 0.49, "Z", iron, thick=0.012)
    # the bulb's socket
    cyl("Socket", 0.06, 0.12, (0, 0, 0.55), brass, verts=14, bevel=0.01)
    # chain from the cap to the ceiling rose
    z = 0.86
    k = 0
    while z < 3.72:
        rot = Matrix.Rotation((k % 2) * math.pi / 2, 4, "Z")
        pts = [(math.cos(t) * 0.04, 0, math.sin(t) * 0.07) for t in [i / 10 * 2 * math.pi for i in range(10)]]
        s = _mark()
        tube(f"Link{k}", pts, 0.011, iron, closed=True, poly=True)
        _xform(s, Matrix.Translation((0, 0, z + 0.07)) @ rot)
        z += 0.115
        k += 1
    lathe("Hook", [(0.03, 3.72), (0.035, 3.8), (0, 3.8)], iron, seg=12)
    lathe("Rose", [(0.05, 3.8), (0.12, 3.82), (0.22, 3.9), (0.24, 3.97), (0.22, 4.0), (0, 4.0)], iron, seg=28)
    hoop("RoseGilt", (0, 0, 3.9), 0.215, "Z", gl, thick=0.01)
    # the bulb
    set_group("Glow")
    sphere("Bulb", 0.11, (0, 0, 0.4), P.material("BulbTmp", base=(1.0, 0.75, 0.45), rough=0.4), seg=14, rings=8, scale=(1, 1, 1.2))
    # the crimson glass shade
    set_group("Glass")
    lathe("Shade", [(0.55, 0.0), (0.53, 0.12), (0.45, 0.32), (0.32, 0.5), (0.18, 0.61), (0.15, 0.62),
                    (0.14, 0.6), (0.17, 0.585), (0.3, 0.48), (0.43, 0.31), (0.51, 0.12), (0.53, 0.0)], red, seg=40)
    set_group("Main")
    return _dims()


P.PREVIEW_PAD.update({"CondimentCaddy": 1.3, "CakeStand": 1.25, "PendantLamp": 1.1, "ChalkMenuStand": 1.1})

P.BUILD.update({
    "CafeteriaTable": cafeteria_table,
    "CafeChair": cafe_chair,
    "CafeBooth": cafe_booth,
    "ChalkMenuStand": chalk_menu_stand,
    "CondimentCaddy": condiment_caddy,
    "CakeStand": cake_stand,
    "PendantLamp": pendant_lamp,
})
