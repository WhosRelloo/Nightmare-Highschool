"""Props batch 19 (2026-11-04): the lamp and light kit for nh_props.py. On theme with the Institution: cast and wrought
iron, crimson enamel, gilt and brass, wax and gaslight, no wood. Every fixture has a Glow piece (the flame, mantle or
bulb) that the Studio setup lights; lanterns and lenses have a Glass piece. It fills the gaps round the lights the
school already has (WallSconce, OilLamp, CandleCluster, Chandelier, Candelabra, DeskLamp, PendantLamp).

  GasLampPost       an outdoor gas lamp standard, 11 tall: an octagonal iron plinth with crimson enamel lancet panels
                    and gilt quatrefoils, a fluted shaft with a crimson crest collar, a stiff-leaf capital, the
                    lamplighter's ladder bar, and a hexagonal gothic lantern (gablets, crockets, vent, gilt finial)
  GasLampTwin       the same standard with a scrolled cross-arm carrying two lanterns and a raven on the centre finial
  WallLantern       a wall piece: a hexagonal gas lantern on a scrolled bracket from a pointed iron shield with a
                    crimson inset and a gilt quatrefoil (the back is flat for the wall)
  HangingLantern    a large hexagonal gothic lantern of three candles on a chain from a ceiling rose (hang its top)
  FloorLamp         a standard lamp: a scrolled iron tripod, a fluted black lacquer and gilt column with a black
                    marble tray, a pleated crimson silk shade with a beaded fringe
  ChandelierCorona  a gothic iron corona 4 across: a crimson band behind a gilt arcade, eight turrets with gilt spires
                    and drops, sixteen pricket candles, suspension rods to a gilt orb and a chain
  ChandelierCrystal a gilt chandelier: a cut-glass bowl, eight lower and four upper scrolled arms with crimson
                    enamel candle sleeves, crystal swags, prism drops and a crystal finial
  PricketStand      a tall floor candlestand: a scrolled tripod, a twisted iron shaft with a gilt knop, a spiked brass
                    drip pan and a guttering church candle
  VotiveStand       a stepped iron votive rack of eighteen tea lights in crimson glass cups, crimson and gilt tier
                    lips, a pointed back panel with a gilt quatrefoil and a brass offering box
  StageSpotlight    a Victorian limelight: a crimson enamel lamp house with brass bands, cooling rings, a vent cap
                    and a glass lens, on a yoke on a telescoping iron tripod (the setup gives it a SpotLight)
  Footlights        an 8-stud run of stage footlights (tiles end to end): a crimson and gilt front over four brass
                    reflectors with wire guards, tilted up toward the stage
  TorchSconce       a wall piece: an iron torch with a pitch-wrapped cresset, burning, in a ring on a gothic plate

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their backs flat at +Y. Hanging pieces
(HangingLantern, both chandeliers) are modelled hanging: hang their top from a ceiling.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math

from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone, circle_pts, flame
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _aim, _dims, flat, _mesh
from nh_props_batch9 import foil, candle, wax_mat, twist, stiff_leaf, raven
from nh_props_batch10 import gilt, lacquer, black_marble, tongue
from nh_props_batch13 import ring_band


# ------------------------------------------------------------------ materials

def mantle():
    return flat("GasMantle", (1.0, 0.86, 0.62), 0.6, dirt=0.1)


def bulb():
    return flat("Bulb", (1.0, 0.8, 0.5), 0.4, dirt=0.1)


def fire():
    return flat("TorchFire", (1.0, 0.55, 0.18), 0.6, dirt=0.0)


def silk():
    return flat("CrimsonSilk", (0.15, 0.01, 0.02), 0.78, dirt=0.4)


def soot():
    return flat("PitchCloth", (0.05, 0.04, 0.035), 0.9, dirt=0.6)


def _gothic(hw, z0, zs, za, n=8):
    """A lancet outline (u, z): the feet at z0, springing at zs, the point at za; counter-clockwise from bottom left."""
    pts = [(-hw, z0), (hw, z0)]
    for i in range(n + 1):
        t = i / n
        u = hw - 2 * hw * t
        k = 1 - abs(2 * t - 1)
        pts.append((u, zs + (za - zs) * math.sin(k * math.pi / 2) ** 0.75))
    return pts


def _shrink(pts, d):
    """Pull an outline in toward its centre by about d."""
    cx = sum(u for u, _ in pts) / len(pts)
    cz = sum(z for _, z in pts) / len(pts)
    out = []
    for u, z in pts:
        du, dz = u - cx, z - cz
        L = math.hypot(du, dz) or 1
        out.append((u - du / L * d, z - dz / L * d))
    return out


def _chain(prefix, z0, z1, mat, r=0.04, h=0.07, pitch=0.115, thick=0.011):
    """Iron chain links from z0 up to z1 on the Z axis (the pendant lamp's chain)."""
    z, k = z0, 0
    while z < z1 - pitch * 0.5:
        rot = Matrix.Rotation((k % 2) * math.pi / 2, 4, "Z")
        pts = [(math.cos(t) * r, 0, math.sin(t) * h) for t in [i / 10 * 2 * math.pi for i in range(10)]]
        s = _mark()
        tube(f"{prefix}{k}", pts, thick, mat, closed=True, poly=True)
        _xform(s, Matrix.Translation((0, 0, z + h)) @ rot)
        z += pitch
        k += 1


# ------------------------------------------------------------------ the hexagonal gothic lantern

def hex_lantern(prefix, M, gl, mtx, inner="mantle", bottom="socket", top_ring=False):
    """A hexagonal gothic lantern built at 1.0 scale (0.43 across the band, 2.22 to the finial tip; 2.38 with the top
    ring), its origin at the floor of the cage; mtx places (and scales) it. A flat pane faces -Y.
    inner: "mantle" (a gas burner and mantle) or "candles" (three candles). bottom: "socket" (sits on a post, reaching
    0.3 below) or "drop" (a hanging pendant drop, 0.5 below). Returns the world centre of its light."""
    s = _mark()
    iron, cr = M["iron"], M["crimson"]
    R0, R1, Z0, Z1 = 0.30, 0.38, 0.12, 1.12

    def corner(k, z):
        r = R0 + (R1 - R0) * (z - Z0) / (Z1 - Z0)
        a = k * math.pi / 3
        return Vector((math.cos(a) * r, math.sin(a) * r, z))

    # the floor and its socket or drop
    lathe(f"{prefix}Floor", [(0, 0.0), (0.33, 0.0), (0.35, 0.04), (0.33, 0.1), (0.31, Z0 + 0.01), (0, Z0 + 0.01)], iron, seg=6)
    if bottom == "socket":
        lathe(f"{prefix}Socket", [(0, -0.3), (0.09, -0.3), (0.1, -0.22), (0.16, -0.12), (0.26, -0.03), (0.3, 0.0), (0, 0.0)], iron, seg=12)
        hoop(f"{prefix}SocketBand", (0, 0, -0.2), 0.105, "Z", gl, thick=0.012)
    else:
        lathe(f"{prefix}Drop", [(0, -0.42), (0.04, -0.38), (0.05, -0.3), (0.1, -0.2), (0.2, -0.08), (0.3, 0.0), (0, 0.0)], iron, seg=6)
        sphere(f"{prefix}DropBall", 0.05, (0, 0, -0.45), gl, seg=10, rings=6)
    # the cage: six posts, the top band and a gilt bead, a pointed iron arch at the head of every pane
    for k in range(6):
        tube(f"{prefix}Post{k}", [tuple(corner(k, Z0)), tuple(corner(k, Z1))], 0.02, iron, square=True, poly=True)
        a, b = corner(k, 0.88), corner(k + 1, 0.88)
        r88 = R0 + (R1 - R0) * (0.88 - Z0) / (Z1 - Z0)
        pts = []
        for i in range(9):
            t = i / 8
            kk = 1 - abs(2 * t - 1)
            z = 0.88 + 0.18 * math.sin(kk * math.pi / 2) ** 0.75
            p = a.lerp(b, t)
            f = (R0 + (R1 - R0) * (z - Z0) / (Z1 - Z0)) / r88 * 1.012
            pts.append((p.x * f, p.y * f, z))
        tube(f"{prefix}Arch{k}", pts, 0.012, iron, square=True, poly=True)
        tube(f"{prefix}Sill{k}", [tuple(corner(k, 0.2)), tuple(corner(k + 1, 0.2))], 0.012, iron, square=True, poly=True)
    lathe(f"{prefix}Band", [(0, Z1 - 0.02), (0.4, Z1 - 0.02), (0.43, Z1 + 0.02), (0.43, Z1 + 0.08), (0.4, Z1 + 0.1), (0, Z1 + 0.1)], iron, seg=6)
    lathe(f"{prefix}BandGilt", [(0.437, Z1 + 0.03), (0.442, Z1 + 0.05), (0.437, Z1 + 0.07)], gl, seg=6)
    # the crown: a crimson-filled gablet over every pane, a hexagonal roof with gilt crockets on its ridges, a vent
    ap = 0.43 * math.cos(math.pi / 6)
    zb = Z1 + 0.1
    for k in range(6):
        g = _mark()
        prism(f"{prefix}Gablet{k}", [(-0.19, zb), (0.19, zb), (0, zb + 0.27)], -ap + 0.005, 0.03, iron)
        prism(f"{prefix}GabletIn{k}", [(-0.12, zb + 0.03), (0.12, zb + 0.03), (0, zb + 0.2)], -ap - 0.012, 0.008, cr)
        sphere(f"{prefix}GabletTip{k}", 0.022, (0, -ap + 0.005, zb + 0.28), gl, seg=8, rings=4)
        _xform(g, Matrix.Rotation(math.radians(30 + 60 * k - 270), 4, "Z"))
    lathe(f"{prefix}Roof", [(0.4, zb), (0.34, zb + 0.1), (0.22, zb + 0.28), (0.12, zb + 0.4), (0.09, zb + 0.44), (0, zb + 0.44)], iron, seg=6)
    for k in range(6):
        a = k * math.pi / 3
        for t, r in ((0.3, 0.32), (0.6, 0.22)):
            z = zb + 0.1 + t * 0.3
            sphere(f"{prefix}Crocket{k}{t}", 0.024, (math.cos(a) * (r + 0.02), math.sin(a) * (r + 0.02), z + 0.02), gl, seg=6, rings=4)
    zv = zb + 0.44
    lathe(f"{prefix}Vent", [(0, zv), (0.08, zv), (0.08, zv + 0.12), (0.14, zv + 0.14), (0.15, zv + 0.18), (0.1, zv + 0.22), (0, zv + 0.24)], iron, seg=12)
    lathe(f"{prefix}Finial", [(0, zv + 0.23), (0.035, zv + 0.23), (0.05, zv + 0.28), (0.03, zv + 0.33), (0.025, zv + 0.43),
                              (0.04, zv + 0.46), (0, zv + 0.56)], gl, seg=12)
    if top_ring:
        tube(f"{prefix}TopRing", circle_pts(0, 0, zv + 0.64, 0.07, "X", 12), 0.016, iron, closed=True, poly=True)
    # inside: a brass burner and its mantle, or three candles on a brass pan
    lights = []
    if inner == "mantle":
        lathe(f"{prefix}Burner", [(0, Z0), (0.07, Z0), (0.05, Z0 + 0.07), (0.03, 0.42), (0.05, 0.46), (0, 0.46)], M["brass"], seg=12)
        set_group("Glow")
        lathe(f"{prefix}Mantle", [(0, 0.46), (0.05, 0.46), (0.07, 0.52), (0.075, 0.62), (0.06, 0.7), (0.03, 0.74), (0, 0.75)], mantle(), seg=12)
        lights.append(Vector((0, 0, 0.6)))
    else:
        cyl(f"{prefix}Pan", 0.2, 0.03, (0, 0, Z0 + 0.015), M["brass"], verts=18, bevel=0.008)
        wax = wax_mat()
        tips = []
        for k, (h, a) in enumerate(((0.36, 90), (0.28, 210), (0.22, 330))):
            x, y = math.cos(math.radians(a)) * 0.1, math.sin(math.radians(a)) * 0.1
            tips.append((x, y, candle(f"{prefix}Candle{k}", x, y, Z0 + 0.03, h, wax, r=0.045)))
        set_group("Glow")
        for k, (x, y, z) in enumerate(tips):
            flame(f"{prefix}Flame{k}", (x, y, z), h=0.12)
        lights.append(Vector((0, 0, 0.5)))
    # the glass: one pane in every face of the cage
    set_group("Glass")
    for k in range(6):
        def inner(j, z):
            c = corner(j, z)
            return (c.x * 0.985, c.y * 0.985, z)
        rows = [[inner(k, Z0 + 0.02), inner(k + 1, Z0 + 0.02)], [inner(k, Z1 - 0.02), inner(k + 1, Z1 - 0.02)]]
        _mesh(f"{prefix}Pane{k}", rows, M["glassclear"], 0.008)
    set_group("Main")
    _xform(s, mtx)
    return [mtx @ v for v in lights]


# ------------------------------------------------------------------ the lamp standard (shared by the post and the twin)

def _standard(M, gl):
    """The cast-iron standard up to the top of its capital (z 7.85)."""
    iron, cr = M["iron"], M["crimson"]
    # the octagonal plinth, turned so a face looks to the front
    s = _mark()
    lathe("Plinth", [(0, 0), (0.82, 0), (0.84, 0.04), (0.82, 0.12), (0.72, 0.18), (0.7, 0.22), (0.7, 1.08), (0.75, 1.12), (0.76, 1.2),
                     (0.62, 1.28), (0.5, 1.42), (0.42, 1.62), (0.36, 1.7), (0, 1.7)], iron, seg=8)
    _xform(s, Matrix.Rotation(math.pi / 8, 4, "Z"))
    ap = 0.7 * math.cos(math.pi / 8)
    arch = _gothic(0.165, 0.32, 0.78, 0.98)
    for k in range(8):
        g = _mark()
        prism(f"Panel{k}", arch, -ap - 0.004, 0.012, cr)
        tube(f"PanelRim{k}", [(u, -ap - 0.012, z) for u, z in arch], 0.013, gl, closed=True, square=True, poly=True)
        foil(f"PanelFoil{k}", 0, -ap - 0.014, 0.6, 0.075, gl, thick=0.011)
        _xform(g, Matrix.Rotation(math.radians(45 + 45 * k - 270), 4, "Z"))
    hoop("PlinthBead", (0, 0, 1.16), 0.76, "Z", gl, thick=0.014)
    # the shaft: a swelling foot, fluted iron, a crimson collar with a gilt crest, fluted again
    lathe("ShaftFoot", [(0, 1.7), (0.34, 1.7), (0.36, 1.78), (0.33, 1.9), (0.27, 2.05), (0.22, 2.15), (0.2, 2.22), (0, 2.22)], iron, seg=32)
    hoop("FootBead", (0, 0, 1.76), 0.355, "Z", gl, thick=0.014)
    lathe("ShaftLow", [(0, 2.2), (0.19, 2.2), (0.18, 4.32), (0, 4.32)], iron, seg=48, flute=(16, 0.1))
    lathe("Collar", [(0, 4.3), (0.2, 4.3), (0.235, 4.36), (0.235, 4.74), (0.2, 4.8), (0, 4.8)], cr, seg=32)
    for z in (4.34, 4.76):
        hoop(f"CollarBead{z}", (0, 0, z), 0.235, "Z", gl, thick=0.014)
    foil("Crest", 0, -0.24, 4.55, 0.1, gl, thick=0.014)
    lathe("ShaftHigh", [(0, 4.78), (0.17, 4.78), (0.15, 7.12), (0, 7.12)], iron, seg=48, flute=(16, 0.1))
    # the capital with stiff-leaf foliage
    lathe("Capital", [(0, 7.1), (0.16, 7.1), (0.2, 7.18), (0.17, 7.24), (0.24, 7.36), (0.3, 7.5), (0.31, 7.56), (0.26, 7.6), (0.14, 7.66),
                      (0.11, 7.75), (0.11, 7.85), (0, 7.85)], iron, seg=32)
    hoop("CapitalBead", (0, 0, 7.53), 0.31, "Z", gl, thick=0.014)
    stiff_leaf("Leaf", 0.16, 7.18, 8, 0.26, iron, pitch=70, droop=0.35, width=0.14, knob=0.045, kseg=(6, 4))
    # the lamplighter's ladder bar on scrolled braces
    tube("LadderBar", [(-0.74, 0, 6.85), (0.74, 0, 6.85)], 0.035, iron, poly=True)
    lathe("BarCollar", [(0.16, 6.76), (0.2, 6.79), (0.2, 6.91), (0.16, 6.94)], iron, seg=24)
    for sx in (-1, 1):
        sphere(f"BarKnob{sx}", 0.06, (sx * 0.78, 0, 6.85), gl, seg=12, rings=6)
        tube(f"Brace{sx}", [(sx * 0.16, 0, 6.38), (sx * 0.3, 0, 6.55), (sx * 0.5, 0, 6.76), (sx * 0.62, 0, 6.84)], 0.022, iron)
        tube(f"BraceCurl{sx}", [(sx * 0.3, 0, 6.55), (sx * 0.37, 0, 6.42), (sx * 0.45, 0, 6.45), (sx * 0.43, 0, 6.53)], 0.015, iron)
    return 7.85


def gas_lamp_post(M):
    gl = gilt()
    top = _standard(M, gl)
    s = 1.35
    hex_lantern("L", M, gl, Matrix.Translation((0, 0, top + 0.3 * s)) @ Matrix.Scale(s, 4))
    return _dims()


def gas_lamp_twin(M):
    gl = gilt()
    iron = M["iron"]
    top = _standard(M, gl)
    lathe("Neck", [(0, top), (0.11, top), (0.1, 8.3), (0.15, 8.35), (0.15, 8.45), (0, 8.45)], iron, seg=24)
    hoop("NeckBead", (0, 0, 8.4), 0.15, "Z", gl, thick=0.012)
    s, ax = 1.05, 1.45
    for sx in (-1, 1):
        tube(f"Arm{sx}", [(0, 0, 8.38), (sx * 0.5, 0, 8.5), (sx * 1.0, 0, 8.58), (sx * ax, 0, 8.6)], 0.045, iron)
        tube(f"Scroll{sx}", [(sx * 0.1, 0, 8.0), (sx * 0.35, 0, 7.98), (sx * 0.62, 0, 8.08), (sx * 0.82, 0, 8.3), (sx * 0.96, 0, 8.56)], 0.03, iron)
        tube(f"ScrollCurl{sx}", [(sx * 0.35, 0, 7.98), (sx * 0.3, 0, 7.84), (sx * 0.42, 0, 7.8), (sx * 0.47, 0, 7.9)], 0.02, iron)
        sphere(f"ScrollBoss{sx}", 0.04, (sx * 0.62, 0, 8.08), gl, seg=8, rings=5)
        lathe(f"Cup{sx}", [(0, 8.55), (0.12, 8.55), (0.16, 8.62), (0.14, 8.68), (0, 8.68)], iron, seg=16, loc=(sx * ax, 0, 0))
        hex_lantern(f"L{sx}", M, gl, Matrix.Translation((sx * ax, 0, 8.68 + 0.3 * s)) @ Matrix.Scale(s, 4))
    lathe("CentreFinial", [(0, 8.45), (0.12, 8.45), (0.1, 8.6), (0.06, 8.7), (0.09, 8.8), (0.05, 8.9), (0.04, 9.3), (0, 9.3)], iron, seg=16)
    sphere("Orb", 0.1, (0, 0, 9.38), gl, seg=16, rings=8)
    raven("Raven", (0, 0, 9.46), -math.pi / 2, 1.6, iron, M["felt"])
    return _dims()


def wall_lantern(M):
    gl = gilt()
    iron, cr = M["iron"], M["crimson"]
    shield = _gothic(0.32, 0.0, 2.0, 2.6, n=10)
    prism("Plate", shield, 0.63, 0.07, iron, bevel=0.015)
    tube("PlateRim", [(u, 0.588, z) for u, z in _shrink(shield, 0.04)], 0.014, gl, closed=True, square=True, poly=True)
    prism("PlateInset", _shrink(shield, 0.09), 0.6, 0.02, M["crimsonin"])
    foil("PlateFoil", 0, 0.582, 0.75, 0.13, gl, thick=0.013)
    for z in (0.25, 1.85):
        for sx in (-1, 1):
            sphere(f"Rivet{z}{sx}", 0.03, (sx * 0.2, 0.585, z), M["brass"], seg=8, rings=4)
    # the bracket: a square iron arm out from the plate, a scrolled brace under it
    ly = -0.5
    tube("Arm", [(0, 0.59, 1.32), (0, 0.3, 1.3), (0, 0.0, 1.26), (0, -0.3, 1.22), (0, ly, 1.2)], 0.035, iron, square=True)
    tube("Brace", [(0, 0.59, 0.42), (0, 0.42, 0.55), (0, 0.12, 0.85), (0, -0.22, 1.1), (0, ly + 0.05, 1.19)], 0.028, iron)
    tube("BraceCurl", [(0, 0.42, 0.55), (0, 0.32, 0.44), (0, 0.38, 0.34), (0, 0.47, 0.4)], 0.02, iron)
    sphere("BraceBoss", 0.04, (0, 0.12, 0.85), gl, seg=8, rings=5)
    lathe("Cup", [(0, 1.17), (0.11, 1.17), (0.13, 1.21), (0.11, 1.25), (0, 1.25)], iron, seg=16, loc=(0, ly, 0))
    s = 0.85
    hex_lantern("L", M, gl, Matrix.Translation((0, ly, 1.25 + 0.3 * s)) @ Matrix.Scale(s, 4))
    return _dims()


def hanging_lantern(M):
    gl = gilt()
    iron = M["iron"]
    s = 1.25
    zb = 0.48 * s
    hex_lantern("L", M, gl, Matrix.Translation((0, 0, zb)) @ Matrix.Scale(s, 4), inner="candles", bottom="drop", top_ring=True)
    ring_top = zb + (1.22 + 0.44 + 0.64 + 0.07) * s
    _chain("Link", ring_top - 0.04, 5.2, iron)
    lathe("Hook", [(0.03, 5.14), (0.035, 5.22), (0, 5.22)], iron, seg=12)
    lathe("Rose", [(0.05, 5.2), (0.12, 5.22), (0.2, 5.3), (0.22, 5.36), (0, 5.36)], iron, seg=28)
    hoop("RoseGilt", (0, 0, 5.3), 0.2, "Z", gl, thick=0.01)
    return _dims()


def floor_lamp(M):
    gl = gilt()
    iron, lq, sk = M["iron"], lacquer(), silk()
    # the scrolled tripod and its hub
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c, s_ = math.cos(a), math.sin(a)
        leg = [(0.12, 0.75), (0.3, 0.55), (0.5, 0.3), (0.62, 0.12), (0.68, 0.07)]
        tube(f"Leg{k}", [(c * r, s_ * r, z) for r, z in leg], 0.035, iron, square=True)
        curl = [(0.3, 0.55), (0.3, 0.72), (0.4, 0.76), (0.43, 0.66)]
        tube(f"LegCurl{k}", [(c * r, s_ * r, z) for r, z in curl], 0.02, iron)
        sphere(f"Toe{k}", 0.055, (c * 0.69, s_ * 0.69, 0.055), gl, seg=10, rings=6)
    lathe("Hub", [(0, 0.6), (0.16, 0.6), (0.2, 0.7), (0.18, 0.8), (0.12, 0.9), (0, 0.9)], lq, seg=24)
    hoop("HubBead", (0, 0, 0.7), 0.2, "Z", gl, thick=0.012)
    # the column, its knops, the marble tray
    lathe("ColumnLow", [(0, 0.9), (0.07, 0.9), (0.065, 2.5), (0, 2.5)], lq, seg=32, flute=(8, 0.12))
    lathe("KnopLow", [(0, 2.46), (0.07, 2.46), (0.11, 2.54), (0.13, 2.62), (0.1, 2.7), (0.07, 2.74), (0, 2.74)], gl, seg=24)
    lathe("TrayCollar", [(0, 2.72), (0.08, 2.72), (0.16, 2.8), (0.2, 2.86), (0, 2.86)], gl, seg=24)
    lathe("Tray", [(0, 2.85), (0.42, 2.85), (0.45, 2.89), (0.44, 2.94), (0.41, 2.95), (0, 2.95)], black_marble(), seg=48)
    hoop("TrayGallery", (0, 0, 2.97), 0.44, "Z", gl, thick=0.012)
    lathe("ColumnHigh", [(0, 2.95), (0.055, 2.95), (0.05, 4.72), (0, 4.72)], lq, seg=32, flute=(8, 0.12))
    lathe("KnopMid", [(0, 3.74), (0.06, 3.74), (0.09, 3.8), (0.06, 3.86), (0, 3.86)], gl, seg=20)
    lathe("Socket", [(0, 4.7), (0.08, 4.7), (0.09, 4.78), (0.06, 4.84), (0.06, 4.95), (0, 4.95)], M["brass"], seg=20)
    # the harp, the pleated silk shade (lit inside), its braids and beaded fringe, the finial
    for sx in (-1, 1):
        tube(f"Harp{sx}", [(0, 0, 4.82), (sx * 0.2, 0, 4.9), (sx * 0.3, 0, 5.1), (sx * 0.08, 0, 5.42)], 0.012, gl)
    lathe("Shade", [(0.72, 4.55), (0.68, 4.7), (0.56, 5.05), (0.42, 5.4), (0.38, 5.45)], sk, seg=56, flute=(28, 0.03))
    lathe("ShadeInner", [(0.37, 5.44), (0.41, 5.39), (0.55, 5.04), (0.67, 4.69), (0.71, 4.555)], flat("ShadeLit", (0.78, 0.24, 0.1), 0.6, dirt=0.2),
          seg=56, flute=(28, 0.03))
    hoop("RimBraid", (0, 0, 4.56), 0.725, "Z", gl, thick=0.016)
    hoop("TopBraid", (0, 0, 5.445), 0.385, "Z", gl, thick=0.012)
    fringe = flat("Fringe", (0.22, 0.015, 0.025), 0.8, dirt=0.3)
    for k in range(60):
        a = k / 60 * 2 * math.pi
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Strand{k}", [(c * 0.72, s_ * 0.72, 4.55), (c * 0.725, s_ * 0.725, 4.34)], 0.009, fringe, poly=True)
        sphere(f"Bead{k}", 0.02, (c * 0.725, s_ * 0.725, 4.33), gl, seg=6, rings=4)
    lathe("Finial", [(0, 5.42), (0.06, 5.42), (0.05, 5.5), (0.03, 5.56), (0.045, 5.62), (0, 5.72)], gl, seg=16)
    set_group("Glow")
    sphere("Bulb", 0.12, (0, 0, 5.07), bulb(), seg=14, rings=8, scale=(1, 1, 1.2))
    set_group("Main")
    return _dims()


def chandelier_corona(M):
    gl = gilt()
    iron, cr, wax = M["iron"], M["crimson"], wax_mat()
    R, z0, z1 = 2.0, 1.0, 1.5
    ring_band("Band", 1.955, 1.995, z0 + 0.02, z1 - 0.02, M["crimsonin"], seg=96)
    for z in (z0, z1):
        hoop(f"HoopOut{z}", (0, 0, z), R + 0.03, "Z", iron, thick=0.04)
        hoop(f"HoopIn{z}", (0, 0, z), R - 0.06, "Z", iron, thick=0.03)
    # the gilt arcade round the band: 24 bays of pointed arches on little iron shafts
    n = 24
    ra = R + 0.02
    for j in range(n):
        a0, a1 = j / n * 2 * math.pi, (j + 1) / n * 2 * math.pi
        tube(f"Shaft{j}", [(math.cos(a0) * ra, math.sin(a0) * ra, z0 + 0.02), (math.cos(a0) * ra, math.sin(a0) * ra, 1.3)], 0.014, iron, square=True, poly=True)
        pts = []
        for i in range(9):
            t = i / 8
            k = 1 - abs(2 * t - 1)
            a = a0 + (a1 - a0) * t
            z = 1.3 + 0.14 * math.sin(k * math.pi / 2) ** 0.75
            pts.append((math.cos(a) * ra, math.sin(a) * ra, z))
        tube(f"Arch{j}", pts, 0.012, gl, square=True, poly=True)
    # eight turrets with gilt spires and drops
    tops = []
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, y = math.cos(a) * (R + 0.03), math.sin(a) * (R + 0.03)
        lathe(f"Turret{k}", [(0, 0.86), (0.1, 0.86), (0.13, 0.92), (0.12, 1.0), (0.12, 1.55), (0.15, 1.58), (0.15, 1.63), (0, 1.63)], iron, seg=6, loc=(x, y, 0))
        lathe(f"Spire{k}", [(0.14, 1.63), (0.08, 1.78), (0.03, 1.94), (0, 2.0)], gl, seg=6, loc=(x, y, 0))
        sphere(f"SpireBall{k}", 0.03, (x, y, 2.02), gl, seg=8, rings=4)
        lathe(f"TurretDrop{k}", [(0, 0.6), (0.03, 0.66), (0.055, 0.76), (0.05, 0.86), (0, 0.86)], gl, seg=8, loc=(x, y, 0))
        for zz in (1.1, 1.35):
            box(f"Slit{k}{zz}", (0.03, 0.03, 0.12), (x * 1.06, y * 1.06, zz), M["felt"], bevel=0.005, rot=(0, 0, a))
        tops.append((x, y))
    # sixteen pricket candles on the top hoop between the turrets
    tips = []
    for k in range(16):
        a = (k + 0.5) / 16 * 2 * math.pi
        x, y = math.cos(a) * (R - 0.01), math.sin(a) * (R - 0.01)
        cyl(f"Pan{k}", 0.085, 0.025, (x, y, z1 + 0.045), M["brass"], verts=14, bevel=0.006)
        h = 0.3 + 0.06 * ((k * 7) % 3) / 2
        tips.append((x, y, candle(f"C{k}", x, y, z1 + 0.058, h, wax, r=0.045)))
    # suspension: four rods from the turret tops to a gilt orb, then a chain to the ceiling rose
    zo = 4.2
    for k in (0, 2, 4, 6):
        x, y = tops[k]
        tube(f"Rod{k}", [(x * 0.99, y * 0.99, 1.98), (x * 0.03, y * 0.03, zo - 0.05)], 0.02, iron, poly=True)
        sphere(f"RodKnop{k}", 0.04, (x * 0.5, y * 0.5, (1.98 + zo) / 2), gl, seg=8, rings=5)
    lathe("Orb", [(0, zo - 0.12), (0.08, zo - 0.1), (0.15, zo - 0.02), (0.15, zo + 0.08), (0.08, zo + 0.16), (0, zo + 0.18)], gl, seg=24)
    hoop("OrbBand", (0, 0, zo + 0.03), 0.152, "Z", iron, thick=0.014)
    _chain("Link", zo + 0.16, 5.4, iron)
    lathe("Rose", [(0.05, 5.38), (0.14, 5.4), (0.28, 5.48), (0.3, 5.55), (0, 5.55)], iron, seg=28)
    hoop("RoseGilt", (0, 0, 5.48), 0.28, "Z", gl, thick=0.012)
    set_group("Glow")
    for k, p in enumerate(tips):
        flame(f"Flame{k}", p, h=0.13)
    set_group("Main")
    return _dims()


def chandelier_crystal(M):
    gl = gilt()
    cr, wax, glass = M["crimson"], wax_mat(), M["glassclear"]
    # the stem and its knops
    lathe("Stem", [(0, 0.35), (0.05, 0.4), (0.09, 0.5), (0.07, 0.6), (0.05, 0.7), (0.06, 1.0), (0.1, 1.1), (0.06, 1.2), (0.045, 1.5),
                   (0.08, 1.58), (0.13, 1.66), (0.08, 1.8), (0.05, 2.0), (0.05, 2.55), (0.09, 2.64), (0.05, 2.74), (0.04, 3.3), (0.07, 3.4),
                   (0, 3.45)], gl, seg=24)
    hoop("BowlRim", (0, 0, 1.25), 0.52, "Z", gl, thick=0.016)
    flames, cups = [], []
    tiers = ((8, 1.55, 1.62, [(0.1, 1.64), (0.5, 1.47), (0.95, 1.42), (1.3, 1.52), (1.55, 1.7), (1.55, 1.84)]),
             (4, 0.85, 2.64, [(0.06, 2.66), (0.4, 2.5), (0.7, 2.55), (0.85, 2.7), (0.85, 2.82)]))
    for t, (n, r, za, arm) in enumerate(tiers):
        for k in range(n):
            a = k / n * 2 * math.pi + (math.pi / n if t else 0)
            c, s_ = math.cos(a), math.sin(a)
            tube(f"Arm{t}{k}", [(c * rr, s_ * rr, z) for rr, z in arm], 0.032, gl)
            if t == 0:
                curl = [(0.5, 1.47), (0.45, 1.32), (0.55, 1.24), (0.62, 1.32)]
                tube(f"Curl{k}", [(c * rr, s_ * rr, z) for rr, z in curl], 0.018, gl)
            x, y, z = c * r, s_ * r, arm[-1][1]
            lathe(f"Bobeche{t}{k}", [(0, z - 0.02), (0.15, z), (0.17, z + 0.03), (0.13, z + 0.035), (0.07, z + 0.03), (0, z + 0.03)], gl, seg=16, loc=(x, y, 0))
            lathe(f"Sleeve{t}{k}", [(0.06, z + 0.03), (0.062, z + 0.06), (0.055, z + 0.08), (0.055, z + 0.33), (0.06, z + 0.35), (0, z + 0.35)], cr, seg=14, loc=(x, y, 0))
            tip = candle(f"C{t}{k}", x, y, z + 0.35, 0.09, wax, r=0.042)
            flames.append((x, y, tip))
            cups.append((x, y, z - 0.02, a))
    lathe("Crown", [(0.05, 3.38), (0.16, 3.44), (0.22, 3.52), (0.23, 3.58), (0.2, 3.58)], gl, seg=24)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        cone(f"CrownSpike{k}", 0.03, 0.0, 0.16, (math.cos(a) * 0.21, math.sin(a) * 0.21, 3.66), gl, verts=6)
    _chain("Link", 3.45, 4.55, gl, thick=0.012)
    lathe("Canopy", [(0.05, 4.52), (0.14, 4.55), (0.26, 4.66), (0.28, 4.75), (0, 4.75)], gl, seg=28)
    set_group("Glass")
    # the cut-glass bowl, prism drops, swags of beads, the crystal finial
    lathe("Bowl", [(0.06, 0.9), (0.25, 0.95), (0.42, 1.05), (0.5, 1.17), (0.52, 1.25), (0.49, 1.24), (0.4, 1.1), (0.22, 1.0), (0.06, 0.97)],
          glass, seg=32, flute=(16, 0.06))
    for k in range(16):
        a = k / 16 * 2 * math.pi
        lathe(f"BowlDrop{k}", [(0, 1.23), (0.03, 1.18), (0.03, 1.12), (0, 1.02)], glass, seg=6, loc=(math.cos(a) * 0.5, math.sin(a) * 0.5, 0))
    for k, (x, y, z, a) in enumerate(cups):
        lathe(f"Prism{k}", [(0, z - 0.01), (0.04, z - 0.07), (0.035, z - 0.14), (0, z - 0.26)], glass, seg=6, loc=(x, y, 0))
    lo = cups[:8]
    for k in range(8):
        x0, y0, z0, _ = lo[k]
        x1, y1, z1, _ = lo[(k + 1) % 8]
        for i in range(1, 10):
            t = i / 10
            sag = 0.32 * math.sin(t * math.pi)
            sphere(f"Swag{k}{i}", 0.022, (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 - 0.02 - sag), glass, seg=6, rings=4)
    lathe("Finial", [(0, 0.36), (0.07, 0.3), (0.08, 0.22), (0.05, 0.1), (0, 0.0)], glass, seg=8)
    set_group("Glow")
    for k, p in enumerate(flames):
        flame(f"Flame{k}", p, h=0.12)
    set_group("Main")
    return _dims()


def pricket_stand(M):
    gl = gilt()
    iron, wax = M["iron"], wax_mat()
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c, s_ = math.cos(a), math.sin(a)
        leg = [(0.1, 1.0), (0.25, 0.75), (0.48, 0.42), (0.62, 0.16), (0.66, 0.08)]
        tube(f"Leg{k}", [(c * r, s_ * r, z) for r, z in leg], 0.04, iron, square=True)
        curl = [(0.25, 0.75), (0.36, 0.86), (0.44, 0.8), (0.4, 0.72)]
        tube(f"LegCurl{k}", [(c * r, s_ * r, z) for r, z in curl], 0.022, iron)
        sphere(f"Foot{k}", 0.07, (c * 0.68, s_ * 0.68, 0.07), iron, seg=10, rings=6, scale=(1, 1, 0.9))
    hoop("Stretcher", (0, 0, 0.52), 0.4, "Z", iron, thick=0.022)
    lathe("Hub", [(0, 0.9), (0.14, 0.9), (0.18, 1.0), (0.15, 1.12), (0.1, 1.2), (0, 1.2)], iron, seg=24)
    twist("Shaft", 1.18, 3.92, 0.075, iron, lobes=4, depth=0.25, turns=3.0, seg=20, rings=72)
    lathe("Knop", [(0, 2.42), (0.09, 2.44), (0.13, 2.52), (0.09, 2.6), (0, 2.62)], gl, seg=24)
    lathe("Head", [(0, 3.9), (0.1, 3.9), (0.14, 4.0), (0.1, 4.08), (0.09, 4.15), (0, 4.15)], iron, seg=24)
    lathe("Pan", [(0, 4.13), (0.4, 4.15), (0.46, 4.23), (0.45, 4.26), (0.38, 4.2), (0, 4.19)], M["brass"], seg=48)
    hoop("PanRim", (0, 0, 4.245), 0.455, "Z", gl, thick=0.012)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        cone(f"Spike{k}", 0.014, 0.0, 0.1, (math.cos(a) * 0.43, math.sin(a) * 0.43, 4.31), iron, verts=6)
    # the guttering church candle
    z, h, r = 4.19, 0.95, 0.2
    lathe("Candle", [(0, z), (r, z), (r * 1.01, z + h * 0.5), (r * 0.99, z + h), (r * 0.94, z + h + 0.02), (r * 0.72, z + h - 0.02), (0.05, z + h - 0.05),
                     (0, z + h - 0.05)], wax, seg=28, jitter=(0.02, 7))
    for k in range(7):
        a = k / 7 * 2 * math.pi + 0.4
        L = 0.15 + 0.12 * ((k * 5) % 4) / 3
        sphere(f"Drip{k}", 0.035, (math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, z + h - L * 0.6), wax, seg=8, rings=5, scale=(1, 0.8, L / 0.07))
    for k, (x, y) in enumerate(((0.26, -0.08), (-0.18, 0.22), (0.02, -0.28))):
        sphere(f"Pool{k}", 0.06, (x, y, 4.2), wax, seg=10, rings=4, scale=(1.4, 1, 0.35))
    tube("Wick", [(0, 0, z + h - 0.05), (0.01, 0, z + h + 0.03)], 0.01, flat("Wick", (0.02, 0.02, 0.02), 0.8), poly=True)
    set_group("Glow")
    flame("Flame", (0.01, 0, z + h + 0.02), h=0.22)
    set_group("Main")
    return _dims()


def votive_stand(M):
    gl = gilt()
    iron, cr, wax = M["iron"], M["crimson"], wax_mat()
    W = 3.0
    box("Plinth", (W, 1.3, 0.15), (0, 0, 0.075), iron, bevel=0.02)
    # the side panels: pointed iron cheeks with a gilt lancet each
    side = [(-0.62, 0.15), (0.62, 0.15), (0.62, 3.3), (0.2, 2.9), (-0.3, 2.3), (-0.62, 1.2)]
    for sx in (-1, 1):
        prism(f"Cheek{sx}", side, sx * (W / 2 - 0.04), 0.08, iron, plane="YZ", bevel=0.01)
        pts = [(sx * (W / 2 + 0.002), u, z) for u, z in _gothic(0.18, 0.5, 1.6, 2.0)]
        tube(f"CheekLancet{sx}", pts, 0.014, gl, closed=True, square=True, poly=True)
    # the three tiers (front lowest), each with a crimson lip and gilt quatrefoils
    tiers = ((1.0, -0.35, 7), (1.45, 0.0, 6), (1.9, 0.35, 5))
    flames = []
    for i, (z, y, n) in enumerate(tiers):
        box(f"Shelf{i}", (W - 0.16, 0.44, 0.06), (0, y, z), iron, bevel=0.01)
        box(f"Riser{i}", (W - 0.16, 0.04, z - 0.15), (0, y + 0.2, (z - 0.03 + 0.15) / 2), iron, bevel=0.005)
        box(f"Lip{i}", (W - 0.16, 0.03, 0.12), (0, y - 0.235, z - 0.01), cr, bevel=0.008)
        box(f"LipBead{i}", (W - 0.16, 0.035, 0.02), (0, y - 0.24, z + 0.055), gl, bevel=0.004)
        for k in range(6):
            foil(f"LipFoil{i}{k}", -1.1 + k * 0.44, y - 0.253, z - 0.01, 0.04, gl, thick=0.007)
        for k in range(n):
            x = -1.2 + 2.4 * k / (n - 1)
            zz = z + 0.03
            lathe(f"Light{i}{k}", [(0, zz + 0.02), (0.075, zz + 0.02), (0.075, zz + 0.075), (0.06, zz + 0.08), (0, zz + 0.075)], wax, seg=12, loc=(x, y, 0))
            tube(f"Wick{i}{k}", [(x, y, zz + 0.075), (x, y, zz + 0.1)], 0.006, flat("Wick", (0.02, 0.02, 0.02), 0.8), poly=True)
            flames.append((x, y, zz + 0.09))
    # the front panel under the tiers: gilt lancets and a brass offering box
    box("Front", (W - 0.16, 0.05, 0.75), (0, -0.56, 0.55), iron, bevel=0.01)
    for k in range(5):
        x = -1.1 + k * 0.55
        if k == 2:
            continue
        tube(f"FrontLancet{k}", [(x + u, -0.59, z) for u, z in _gothic(0.13, 0.3, 0.68, 0.86)], 0.012, gl, closed=True, square=True, poly=True)
    box("Box", (0.5, 0.28, 0.42), (0, -0.66, 0.5), M["brass"], bevel=0.02)
    box("BoxSlot", (0.22, 0.02, 0.025), (0, -0.8, 0.62), M["felt"], bevel=0.0)
    box("BoxLid", (0.54, 0.3, 0.04), (0, -0.66, 0.73), M["brass"], bevel=0.01)
    sphere("Lock", 0.04, (0, -0.81, 0.42), iron, seg=10, rings=6)
    # the pointed back panel with a gilt quatrefoil
    back = _gothic(1.35, 1.9, 2.8, 3.6, n=12)
    prism("Back", back, 0.6, 0.06, iron, bevel=0.01)
    prism("BackInset", _shrink(back, 0.1), 0.575, 0.02, M["crimsonin"])
    tube("BackRim", [(u, 0.558, z) for u, z in _shrink(back, 0.05)], 0.014, gl, closed=True, square=True, poly=True)
    foil("BackFoil", 0, 0.555, 2.85, 0.28, gl, thick=0.018)
    sphere("BackFinial", 0.06, (0, 0.6, 3.66), gl, seg=10, rings=6)
    set_group("Glass")
    for i, (z, y, n) in enumerate(tiers):
        for k in range(n):
            x = -1.2 + 2.4 * k / (n - 1)
            zz = z + 0.03
            lathe(f"Cup{i}{k}", [(0.08, zz), (0.1, zz + 0.04), (0.11, zz + 0.16), (0.1, zz + 0.175), (0.09, zz + 0.16), (0.085, zz + 0.04), (0, zz + 0.015)],
                  M["glassclear"], seg=14, loc=(x, y, 0))
    set_group("Glow")
    for k, p in enumerate(flames):
        flame(f"Flame{k}", p, h=0.09)
    set_group("Main")
    return _dims()


def stage_spotlight(M):
    gl = gilt()
    iron, brass, cr = M["iron"], M["brass"], M["crimson"]
    # the tripod, spreaders and telescoping column
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.12, s_ * 0.12, 3.0), (c * 1.1, s_ * 1.1, 0.06)], 0.04, iron, poly=True)
        cyl(f"Foot{k}", 0.07, 0.06, (c * 1.1, s_ * 1.1, 0.03), brass, verts=14, bevel=0.01)
        tube(f"Spreader{k}", [(c * 0.07, s_ * 0.07, 1.05), (c * 0.75, s_ * 0.75, 1.07)], 0.022, iron, poly=True)
    lathe("Hub", [(0, 2.92), (0.14, 2.92), (0.16, 3.0), (0.14, 3.08), (0, 3.08)], iron, seg=20)
    lathe("ColumnLow", [(0, 1.0), (0.07, 1.0), (0.07, 3.12), (0, 3.12)], iron, seg=20)
    lathe("SpreadCollar", [(0, 0.98), (0.1, 0.98), (0.11, 1.12), (0, 1.12)], brass, seg=20)
    lathe("Clamp", [(0, 3.1), (0.1, 3.1), (0.1, 3.24), (0, 3.24)], brass, seg=20)
    tube("ClampScrew", [(0.1, 0, 3.17), (0.25, 0, 3.17)], 0.018, brass, poly=True)
    sphere("ClampKnob", 0.04, (0.27, 0, 3.17), brass, seg=10, rings=6)
    lathe("ColumnHigh", [(0, 3.22), (0.05, 3.22), (0.05, 3.9), (0, 3.9)], iron, seg=16)
    lathe("Turntable", [(0, 3.88), (0.16, 3.88), (0.17, 3.94), (0.15, 3.98), (0, 3.98)], brass, seg=24)
    # the yoke and its trunnions
    yz = 4.45
    tube("Yoke", [(-0.5, 0, yz), (-0.5, 0, 3.98), (0.5, 0, 3.98), (0.5, 0, yz)], 0.035, iron, square=True, poly=True)
    for sx in (-1, 1):
        cyl(f"Trunnion{sx}", 0.07, 0.17, (sx * 0.43, 0, yz), brass, rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
        cyl(f"TrunnionKnob{sx}", 0.05, 0.06, (sx * 0.58, 0, yz), brass, rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    # the lamp house, built along +Z then laid along -Y (local z 0 = the back, 1.4 = the lens)
    s = _mark()
    lathe("House", [(0, 0), (0.3, 0), (0.33, 0.03), (0.34, 0.1), (0.36, 0.15), (0.36, 1.2), (0.33, 1.22), (0, 1.22)], cr, seg=40)
    lathe("LensRing", [(0.33, 1.18), (0.4, 1.2), (0.41, 1.26), (0.41, 1.34), (0.37, 1.38), (0.31, 1.38), (0.3, 1.33)], brass, seg=40)
    for z in (0.14, 0.62, 1.12):
        hoop(f"Band{z}", (0, 0, z), 0.365, "Z", brass, thick=0.016)
    for k, z in enumerate((0.24, 0.31, 0.38, 0.45)):
        hoop(f"Fin{k}", (0, 0, z), 0.375, "Z", iron, thick=0.018)
    tube("Handle", [(-0.12, 0, 0.0), (-0.12, 0, -0.14), (0.12, 0, -0.14), (0.12, 0, 0.0)], 0.018, brass)
    for sx in (-1, 1):
        tube(f"Hinge{sx}", [(sx * 0.2, 0.2, 0.01), (sx * 0.2, -0.2, 0.01)], 0.012, brass, poly=True)
    cyl("FocusKnob", 0.05, 0.08, (0.39, 0, 0.9), brass, rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    set_group("Glow")
    sphere("Burner", 1.0, (0, 0, 1.255), bulb(), seg=24, rings=6, scale=(0.29, 0.29, 0.03))
    set_group("Glass")
    lathe("Lens", [(0, 1.37), (0.15, 1.36), (0.3, 1.32), (0.3, 1.3), (0, 1.3)], M["glassclear"], seg=32)
    set_group("Main")
    _xform(s, Matrix.Translation((0, 0.6, yz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    # the chimney on the lamp house's back
    lathe("Chimney", [(0.12, 4.75), (0.12, 5.0), (0.18, 5.02), (0.2, 5.08), (0.14, 5.12), (0.14, 5.16), (0.22, 5.18), (0.22, 5.22), (0, 5.24)],
          iron, seg=20, loc=(0, 0.2, 0))
    hoop("ChimneyBand", (0, 0.2, 4.9), 0.125, "Z", brass, thick=0.012)
    return _dims()


def footlights(M):
    gl = gilt()
    iron, cr, brass = M["iron"], M["crimson"], M["brass"]
    L = 8.0
    box("Trough", (L, 0.9, 0.12), (0, 0, 0.06), iron, bevel=0.015)
    box("Front", (L, 0.06, 0.55), (0, -0.42, 0.335), M["crimsonin"], bevel=0.01)
    for z in (0.1, 0.6):
        box(f"Moulding{z}", (L, 0.08, 0.05), (0, -0.45, z), gl, bevel=0.012)
    for k in range(8):
        foil(f"Foil{k}", -3.5 + k, -0.455, 0.35, 0.09, gl, thick=0.012)
    box("BackLip", (L, 0.05, 0.22), (0, 0.42, 0.21), iron, bevel=0.01)
    for sx in (-1, 1):
        box(f"End{sx}", (0.04, 0.9, 0.5), (sx * (L / 2 - 0.02), 0, 0.3), iron, bevel=0.008)
    bulbs = []
    for k, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
        mtx = Matrix.Translation((x, -0.05, 0.2)) @ Matrix.Rotation(math.radians(-50), 4, "X")
        s = _mark()
        lathe(f"Dish{k}", [(0, 0), (0.12, 0), (0.24, 0.09), (0.31, 0.2), (0.33, 0.29), (0.31, 0.29), (0.29, 0.21), (0.22, 0.11), (0.1, 0.03), (0, 0.03)],
              brass, seg=28)
        lathe(f"DishFoot{k}", [(0, -0.12), (0.06, -0.12), (0.05, 0.0), (0, 0.0)], iron, seg=12)
        for j in (-0.15, 0.0, 0.15):
            tube(f"Guard{k}{j}", [(j, -0.3, 0.31), (j, 0.3, 0.31)], 0.008, iron, poly=True)
        hoop(f"GuardRing{k}", (0, 0, 0.3), 0.33, "Z", iron, thick=0.012)
        _xform(s, mtx)
        bulbs.append(mtx)
    set_group("Glow")
    for k, mtx in enumerate(bulbs):
        s = _mark()
        sphere(f"Bulb{k}", 0.08, (0, 0, 0.12), bulb(), seg=12, rings=6, scale=(1, 1, 1.25))
        _xform(s, mtx)
    set_group("Main")
    return _dims()


def torch_sconce(M):
    gl = gilt()
    iron = M["iron"]
    plate = _gothic(0.22, 0.25, 1.4, 1.75, n=8)
    prism("Plate", plate, 0.42, 0.06, iron, bevel=0.012)
    tube("PlateRim", [(u, 0.385, z) for u, z in _shrink(plate, 0.035)], 0.012, gl, closed=True, square=True, poly=True)
    foil("PlateFoil", 0, 0.38, 1.12, 0.08, gl, thick=0.011)
    lathe("PlateDrop", [(0, 0.0), (0.03, 0.06), (0.05, 0.16), (0.06, 0.26), (0, 0.26)], iron, seg=8, loc=(0, 0.41, 0))
    for z in (0.45, 1.5):
        sphere(f"Rivet{z}", 0.028, (0, 0.385, z), M["brass"], seg=8, rings=4)
    # the torch, leaning out from the wall
    base, tip = Vector((0, 0.05, 0.62)), Vector((0, -0.3, 1.5))
    d = (tip - base).normalized()
    hold = base.lerp(tip, 0.42)
    tube("Arm", [(0, 0.39, 0.82), (0, 0.2, 0.86), (0, hold.y + 0.02, hold.z)], 0.03, iron, square=True)
    tube("Prop", [(0, 0.39, 0.5), (0, 0.2, 0.55), (0, base.y + 0.02, base.z + 0.02)], 0.025, iron, square=True)
    s = _mark()
    tube("Haft", [(0, 0, 0), (0, 0, 0.72)], 0.04, iron, poly=True)
    for z in (0.12, 0.42, 0.62):
        hoop(f"HaftBand{z}", (0, 0, z), 0.045, "Z", gl if z == 0.42 else iron, thick=0.012)
    lathe("Cresset", [(0.04, 0.7), (0.1, 0.74), (0.15, 0.84), (0.16, 0.9), (0.15, 0.9), (0.14, 0.85), (0.09, 0.76), (0.0, 0.75)], iron, seg=16)
    lathe("Pitch", [(0, 0.75), (0.13, 0.78), (0.135, 0.86), (0.11, 0.92), (0, 0.94)], soot(), seg=14, jitter=(0.06, 3))
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        tube(f"Strap{k}", [(math.cos(a) * 0.1, math.sin(a) * 0.1, 0.74), (math.cos(a) * 0.16, math.sin(a) * 0.16, 0.86),
                           (math.cos(a) * 0.18, math.sin(a) * 0.18, 0.98)], 0.01, iron)
    _xform(s, Matrix.Translation(base) @ _aim(d))
    ring_at = hold
    hoop("Ring", tuple(ring_at), 0.07, "Z", iron, thick=0.016)
    top = base + d * 0.92
    set_group("Glow")
    for k, (h, w, lean, yaw) in enumerate(((0.55, 0.11, 0.03, 0.0), (0.42, 0.08, 0.06, 1.9), (0.38, 0.08, -0.05, 4.0), (0.3, 0.07, 0.05, 3.0))):
        b = top + Vector((math.cos(yaw) * 0.04 * (k > 0), math.sin(yaw) * 0.04 * (k > 0), -0.02))
        tongue(f"Fire{k}", tuple(b), h, w, lean, yaw, fire(), seg=8, rows=10)
    set_group("Main")
    return _dims()


P.PREVIEW_PAD.update({"GasLampPost": 1.0, "GasLampTwin": 1.0, "WallLantern": 1.15, "HangingLantern": 1.1, "FloorLamp": 1.05,
                      "ChandelierCorona": 1.1, "ChandelierCrystal": 1.15, "PricketStand": 1.05, "VotiveStand": 1.15, "StageSpotlight": 1.1,
                      "Footlights": 1.0, "TorchSconce": 1.25})

P.BUILD.update({
    "GasLampPost": gas_lamp_post,
    "GasLampTwin": gas_lamp_twin,
    "WallLantern": wall_lantern,
    "HangingLantern": hanging_lantern,
    "FloorLamp": floor_lamp,
    "ChandelierCorona": chandelier_corona,
    "ChandelierCrystal": chandelier_crystal,
    "PricketStand": pricket_stand,
    "VotiveStand": votive_stand,
    "StageSpotlight": stage_spotlight,
    "Footlights": footlights,
    "TorchSconce": torch_sconce,
})
