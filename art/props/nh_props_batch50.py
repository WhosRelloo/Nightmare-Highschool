"""Props batch 50, the misc signs kit (2026-11-11), for nh_props.py: blank sign bases for door and wall plaques, restrooms,
wayfinding and rules signs. Each base has a blank `_Field` piece: a pale enamel the template tints (SurfaceAppearance.Color)
and the face the builder's icon and text sit on (a SurfaceGui on the Field's face; the icon set is E:/NH-Work/props50,
uploaded separately). So one base takes any icon, text and enamel colour without a new mesh. Brass, black iron, crimson
enamel, limestone and gilt; no wood. Every design is invented.

Bases (NHBuildKit "Signs"; the face layouts are in signs_batch50.json)
  BrassPlaque     door plaque, 2.4 x 0.9: cartouche brass plate, beaded rim, four rosette screws (wall)
  EnamelPlate     restroom and office door plate, 1.3 x 1.9: a lancet of black iron, gilt hairline, apex finial (wall)
  LintelTablet    over a classroom door, 6.0 x 1.6: carved limestone tablet, a small crocketed gable, slate field (wall)
  Roundel         floor and room numbers, 1.7 across: brass disc, bead rim, four cusps (wall)
  CorridorSign    hangs from the ceiling, 5.0 wide: a double-sided board on a scrolled iron bar and chains (ceiling)
  BracketSign     sticks out from the wall, double-sided: a lancet panel under a traceried iron bracket (wall)
  ArrowBoard / ArrowBoardLeft   a pointing board with a fishtail tail, right and left (wall)
  FloorStand      a free-standing double-sided lancet panel on a cast-iron stanchion, 4.9 tall (floor)
  ExitLantern     a lit iron lantern box: Glass front (the text sits on it), Glow behind (wall)
  WingDirectory   a wing's directory board hung from the ceiling, double-sided: a header and up to five rows (ceiling)

Pieces: Main, Field (tinted in Roblox), and for ExitLantern Glass and Glow. Front faces -Y, Z is up, the origin is at the
bottom centre; wall pieces have their back on y = 0. Registered into nh_props.BUILD on import.
"""
import json
import math
import os

import bpy
from mathutils import Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _quatrefoil
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, prism, _dims, flat
import nh_props_batch30 as B30
import nh_props_batch43 as B43
import nh_props_batch46 as B46

DEG = math.pi / 180
PI = math.pi
SPEC = json.load(open(os.path.join(P.HERE, "signs_batch50.json"), encoding="utf-8"))
GLOW = {"ExitLantern": {"Glow": (255, 196, 120)}}
FIELD_RGB = {k: tuple(c / 255 for c in v) for k, v in SPEC["field"].items()}


def kit(M):
    K = B46.kit(M)
    K["field"] = flat("SignFieldEnamel", (0.74, 0.73, 0.71), 0.26, wear=0.12, dirt=0.55)
    K["plaque"] = P.material("SignBrass", "NH_Brass", tint=(1.0, 0.95, 0.86), scale=0.3, wear=0.06, dirt=0.5)
    K["limestone"] = M["stone"]
    K["ironb"] = K["iron"]
    return K


# ------------------------------------------------------------------ helpers

def inset(poly, d):
    """Offset a polygon (x, z), counter-clockwise, inward by d (mitred corners, limited on sharp ones)."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((-e0.y, e0.x))
        n1 = Vector((-e1.y, e1.x))
        bis = n0 + n1
        if bis.length < 1e-6:
            bis = n0
        bis.normalize()
        k = d / max(0.35, bis.dot(n1))
        q = p1 + bis * k
        out.append((q.x, q.y))
    return out


def ccw(poly):
    a = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))
    return poly if a > 0 else list(reversed(poly))


def outline(name, poly, y, r, mat, axis="XZ", x=0.0):
    """A round bar along a closed outline (a rim or frame): in the XZ plane at y, or the YZ plane at x."""
    if axis == "XZ":
        pts = [(u, y, w) for u, w in poly]
    else:
        pts = [(x, u, w) for u, w in poly]
    return tube(name, pts + [pts[0]], r, mat, poly=True)


def lancet(w, hs, rise, n=12, z0=0.0):
    """A lancet outline: straight sides from z0 to z0 + hs, a pointed arch `rise` tall on top (x, z), counter-clockwise."""
    pts = [(-w / 2, z0), (w / 2, z0)]
    pts += B43.arch_xz(w / 2, -w / 2, z0 + hs, rise, n)
    return ccw(pts)


def rosette(prefix, x, y, z, mat, r=0.06, face=-1):
    """A domed screw head on a little four-petalled rose."""
    for k in range(4):
        a = k * PI / 2 + PI / 4
        sphere(f"{prefix}P{k}", r * 0.55, (x + math.cos(a) * r * 0.7, y, z + math.sin(a) * r * 0.7), mat, seg=8, rings=4,
               scale=(1, 0.35, 1))
    sphere(f"{prefix}H", r * 0.6, (x, y + face * r * 0.12, z), mat, seg=10, rings=5, scale=(1, 0.6, 1))


def beads(prefix, cx, y, cz, R, r, n, mat, axis="XZ"):
    for k in range(n):
        a = k / n * 2 * PI
        if axis == "XZ":
            loc = (cx + math.cos(a) * R, y, cz + math.sin(a) * R)
        else:
            loc = (y, cx + math.cos(a) * R, cz + math.sin(a) * R)
        sphere(f"{prefix}{k}", r, loc, mat, seg=6, rings=4)


def field_xz(poly, y_front, depth, mat, name="Field"):
    """The blank Field: a thin slab whose front is at y_front (it looks to -Y)."""
    set_group("Field")
    o = prism(name, poly, y_front + depth / 2, depth, mat, plane="XZ")
    set_group("Main")
    return o


def field_both(poly, plane, thick, mat, name="Field"):
    """A double-sided Field: a slab `thick` through, centred on the board (plane XZ: faces look to -Y and +Y; YZ: -X, +X)."""
    set_group("Field")
    o = prism(name, poly, 0.0, thick, mat, plane=plane)
    set_group("Main")
    return o


def scroll_curl(name, x, y, z, r, turns, mat, plane="XZ", sx=1, thick=0.025, start=0.0):
    pts = []
    n = int(turns * 16)
    for i in range(n + 1):
        t = start + i / 16 * 2 * PI
        rr = r * (1 - i / (n + 4))
        u, w = math.cos(t) * rr * sx, math.sin(t) * rr
        pts.append((x + u, y, z + w) if plane == "XZ" else (x, y + u, z + w))
    return tube(name, pts, thick, mat, poly=True)


# ------------------------------------------------------------------ the bases

def brass_plaque(M):
    """Door plaque: a brass cartouche with notched corners, a beaded rim, four rosette screws and a black enamel field."""
    K = kit(M)
    br, gl = K["plaque"], K["gilt"]
    W, H, D = 2.5, 0.9, 0.06
    cz = H / 2
    c = 0.13
    poly = []
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):    # rectangle with concave quarter-round notches at the corners
        cx0, cz0 = sx * W / 2, cz + sz * H / 2
        for i in range(7):
            t = i / 6 * PI / 2
            # quarter circle centred on the corner, going from the vertical edge to the horizontal edge
            if (sx, sz) == (-1, -1):
                poly.append((cx0 + c * math.sin(t), cz0 + c * math.cos(t)))
            elif (sx, sz) == (1, -1):
                poly.append((cx0 - c * math.cos(t), cz0 + c * math.sin(t)))
            elif (sx, sz) == (1, 1):
                poly.append((cx0 - c * math.sin(t), cz0 - c * math.cos(t)))
            else:
                poly.append((cx0 + c * math.cos(t), cz0 - c * math.sin(t)))
    poly = ccw(poly)
    prism("Plate", poly, -D / 2, D, br, plane="XZ", bevel=0.012)
    outline("Rim", inset(poly, 0.045), -D - 0.004, 0.016, br)
    fw, fh = SPEC["bases"]["BrassPlaque"]["field"]
    fpoly = ccw([(-fw / 2, cz - fh / 2), (fw / 2, cz - fh / 2), (fw / 2, cz + fh / 2), (-fw / 2, cz + fh / 2)])
    field_xz(fpoly, -D - 0.012, 0.012, K["field"])
    outline("FieldLip", inset(fpoly, -0.022), -D - 0.008, 0.011, gl)
    for sx in (-1, 1):
        rosette(f"Screw{sx}", sx * (W / 2 - 0.125), -D - 0.006, cz, gl, r=0.05)
    return _dims()


def enamel_plate(M):
    """Door plate: a lancet of black iron round an enamel field, a gilt hairline, an iron apex finial and a gilt drop."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    W, HS, RISE = 1.3, 1.25, 0.65
    D = 0.05
    poly = lancet(W, HS, RISE)
    prism("Back", poly, -D / 2, D, ir, plane="XZ", bevel=0.01)
    outline("Frame", inset(poly, 0.035), -D - 0.012, 0.03, ir)
    fpoly = lancet(1.12, HS - 0.09, RISE - 0.05, z0=0.09)
    field_xz(fpoly, -D - 0.012, 0.012, K["field"])
    outline("Hair", inset(fpoly, 0.05), -D - 0.016, 0.009, gl)
    B43.finial("Finial", 0, -0.025, HS + RISE - 0.04, ir, s=0.55)
    sphere("FinialBall", 0.04, (0, -0.025, HS + RISE + 0.2), gl, seg=10, rings=6)
    cone("Drop", 0.06, 0.0, 0.16, (0, -0.03, -0.07), gl, verts=12, rot=(PI, 0, 0))
    sphere("DropBall", 0.05, (0, -0.03, 0.01), gl, seg=10, rings=6)
    for sz in (0.2, HS + 0.15):
        rosette(f"Screw{sz:.2f}", 0, -D - 0.008, sz if sz < 1 else HS + RISE - 0.25, gl, r=0.045)
    return _dims()


def lintel_tablet(M):
    """Over a classroom door: a carved limestone tablet, moulded borders, rosettes at the ends, a low crocketed gable with a
    trefoil in the middle of its top, and a recessed slate field for the room's name."""
    K = kit(M)
    st, gl = K["limestone"], K["gilt"]
    W, H, D = 6.0, 1.34, 0.3
    box("Body", (W, D, H), (0, -D / 2, H / 2), st, bevel=0.03)
    # moulded border: a raised outer band and a sunk step inside it
    for z in (0.08, H - 0.08):
        box(f"BandH{z:.2f}", (W - 0.04, 0.08, 0.14), (0, -D - 0.03, z), st, bevel=0.025)
    for sx in (-1, 1):
        box(f"BandV{sx}", (0.14, 0.08, H - 0.04), (sx * (W / 2 - 0.08), -D - 0.03, H / 2), st, bevel=0.025)
        box(f"Pier{sx}", (0.26, 0.06, H - 0.3), (sx * (W / 2 - 0.3), -D - 0.02, H / 2), st, bevel=0.02)
        _quatrefoil(f"Rose{sx}", sx * (W / 2 - 0.3), -D - 0.055, H / 2, 0.11, st)
        box(f"Corbel{sx}", (0.34, D + 0.06, 0.14), (sx * (W / 2 - 0.3), -D / 2 - 0.03, 0.0 + 0.07), st, bevel=0.03)
    fw, fh = SPEC["bases"]["LintelTablet"]["field"]
    fpoly = ccw([(-fw / 2, H / 2 - fh / 2), (fw / 2, H / 2 - fh / 2), (fw / 2, H / 2 + fh / 2), (-fw / 2, H / 2 + fh / 2)])
    field_xz(fpoly, -D - 0.012, 0.012, K["field"])
    outline("FieldLip", inset(fpoly, -0.02), -D - 0.008, 0.012, gl)
    # the gable on top: a low pointed pediment with crockets and a trefoil
    gpoly = ccw([(-0.9, H), (0.9, H)] + B43.arch_xz(0.9, -0.9, H, 0.48, 10)[1:-1])
    prism("Gable", gpoly, -D / 2 + 0.02, D - 0.04, st, plane="XZ", bevel=0.02)
    tube("GableEdge", [(x, -D + 0.01, z) for x, z in B43.arch_xz(-0.86, 0.86, H + 0.02, 0.44, 10)], 0.03, st, poly=True)
    for k, t in enumerate((0.25, 0.5, 0.75)):
        for sx in (-1, 1):
            x = sx * 0.86 * (1 - t)
            z = H + 0.02 + 0.44 * math.sin(t * PI / 2) ** 0.75
            sphere(f"Crocket{k}{sx}", 0.05, (x, -D / 2, z + 0.04), st, seg=8, rings=4)
    B43.finial("Apex", 0, -D / 2, H + 0.46, st, s=0.55)
    for k, (dx, dz) in enumerate(((0, 0.16), (-0.13, -0.05), (0.13, -0.05))):
        hoop(f"Tref{k}", (dx, -D + 0.03, H + 0.2 + dz * 0.6), 0.09, "Y", st, thick=0.02)
    return _dims()


def roundel(M):
    """Floor and room numbers: a brass disc with a bead rim and four pointed cusps, an enamel field inside a gilt ring."""
    K = kit(M)
    br, gl = K["plaque"], K["gilt"]
    R, D = 0.7, 0.06
    cz = 0.85
    disc = ccw([(math.cos(i / 48 * 2 * PI) * R, cz + math.sin(i / 48 * 2 * PI) * R) for i in range(48)])
    prism("Disc", disc, -D / 2, D, br, plane="XZ", bevel=0.01)
    beads("Bead", 0, -D - 0.004, cz, R - 0.045, 0.026, 40, br)
    for k in range(4):
        a = k * PI / 2
        tip = (math.cos(a) * (R + 0.15), cz + math.sin(a) * (R + 0.15))
        l = (math.cos(a - 0.22) * (R - 0.04), cz + math.sin(a - 0.22) * (R - 0.04))
        r = (math.cos(a + 0.22) * (R - 0.04), cz + math.sin(a + 0.22) * (R - 0.04))
        prism(f"Cusp{k}", ccw([l, tip, r]), -D / 2, D * 0.8, br, plane="XZ", bevel=0.008)
        sphere(f"CuspBall{k}", 0.03, (tip[0] * 0.94, -D * 0.9, cz + (tip[1] - cz) * 0.94), gl, seg=8, rings=4)
    fr = SPEC["bases"]["Roundel"]["field"][0] / 2
    fpoly = ccw([(math.cos(i / 48 * 2 * PI) * fr, cz + math.sin(i / 48 * 2 * PI) * fr) for i in range(48)])
    field_xz(fpoly, -D - 0.012, 0.012, K["field"])
    outline("Ring", inset(fpoly, -0.02), -D - 0.008, 0.013, gl)
    return _dims()


def corridor_sign(M):
    """Hangs from a corridor ceiling: a double-sided board in a black iron frame with brass corner caps, slung on two rings
    under a scrolled iron bar, the bar on two chains to ceiling roses. The top (the roses) is 3.0 above the pivot."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    W, H, T = 4.4, 1.1, 0.1
    rect = ccw([(-W / 2, 0), (W / 2, 0), (W / 2, H), (-W / 2, H)])
    prism("Board", rect, 0, T, ir, plane="XZ", bevel=0.015)
    for sy in (-1, 1):
        outline(f"Frame{sy}", inset(rect, 0.03), sy * (T / 2 + 0.005), 0.028, ir)
    for sx in (-1, 1):
        for sz in (0, 1):
            box(f"Cap{sx}{sz}", (0.16, T + 0.05, 0.16), (sx * (W / 2 - 0.05), 0, sz * H + (0.05 if sz == 0 else -0.05)), gl,
                bevel=0.02)
    fw, fh = SPEC["bases"]["CorridorSign"]["field"]
    fpoly = ccw([(-fw / 2, H / 2 - fh / 2), (fw / 2, H / 2 - fh / 2), (fw / 2, H / 2 + fh / 2), (-fw / 2, H / 2 + fh / 2)])
    field_both(fpoly, "XZ", T + 0.02, K["field"])
    zb = H + 0.32
    tube("Bar", [(-2.35, 0, zb), (2.35, 0, zb)], 0.045, ir, poly=True)
    for sx in (-1, 1):
        scroll_curl(f"Curl{sx}", sx * 2.35, 0, zb - 0.16, 0.16, 1.4, ir, sx=sx, thick=0.03, start=PI / 2)
        x = sx * 1.6
        hoop(f"Ring{sx}", (x, 0, H + 0.16), 0.11, "X", ir, thick=0.022)
        B43.chain(f"Chain{sx}", [(sx * 2.05, 0, zb + 0.05), (sx * 2.05, 0, 2.92)], ir, r=0.07, thick=0.014)
        cyl(f"Rose{sx}", 0.16, 0.05, (sx * 2.05, 0, 2.975), ir, verts=16, bevel=0.01)
        sphere(f"RoseKnob{sx}", 0.05, (sx * 2.05, 0, 2.93), gl, seg=8, rings=4)
    for sx in (-1, 1):
        sphere(f"BarEnd{sx}", 0.06, (sx * 2.38, 0, zb), gl, seg=10, rings=6)
    B43.finial("Crest", 0, 0, zb + 0.03, ir, s=0.6)
    return _dims()


def bracket_sign(M):
    """Sticks out from the wall so it reads down a corridor: a tall wall plate, an iron arm with a traceried bracket (a
    quatrefoil in the triangle under it) and a lantern knop at its tip, and a fixed lancet panel slung under the arm on two
    straps; the panel is double-sided (its faces look along X)."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    box("WallPlate", (0.42, 0.07, 3.0), (0, -0.035, 1.9), ir, bevel=0.02)
    for z in (0.6, 3.2):
        rosette(f"WP{z}", 0, -0.075, z, gl, r=0.05)
    za = 3.15
    tube("Arm", [(0, -0.07, za), (0, -2.35, za)], 0.055, ir, poly=True)
    tube("Brace", [(0, -0.07, 1.25), (0, -0.7, 2.05), (0, -1.35, za - 0.05)], 0.045, ir, poly=True)
    hoop("Tracery", (0, -0.55, 2.55), 0.3, "X", ir, thick=0.03)
    for k, (dy, dz) in enumerate(((0.16, 0), (-0.16, 0), (0, 0.16), (0, -0.16))):
        hoop(f"Foil{k}", (0, -0.55 + dy, 2.55 + dz), 0.13, "X", ir, thick=0.018)
    tube("Spoke1", [(0, -0.07, 2.55), (0, -0.25, 2.55)], 0.03, ir, poly=True)
    tube("Spoke2", [(0, -0.55, za - 0.04), (0, -0.55, 2.85)], 0.03, ir, poly=True)
    # the lantern knop at the tip
    lathe("Knop", [(0, 0), (0.05, 0), (0.12, 0.08), (0.12, 0.22), (0.08, 0.28), (0.1, 0.32), (0.03, 0.42), (0, 0.46)], ir,
          seg=8, loc=(0, -2.42, za - 0.22))
    sphere("KnopGilt", 0.05, (0, -2.42, za + 0.26), gl, seg=10, rings=6)
    # the panel (in the YZ plane): 1.6 wide out from the wall, a lancet top
    pw, hs, rise = 1.6, 1.5, 0.65
    yc = -1.4
    poly = [(yc + x, z) for x, z in lancet(pw, hs, rise)]
    poly = ccw(poly)
    prism("Panel", poly, 0, 0.09, ir, plane="YZ", bevel=0.012)
    for sx in (-1, 1):
        outline(f"PFrame{sx}", inset(poly, 0.03), 0, 0.026, ir, axis="YZ", x=sx * 0.05)
    fw, fh = SPEC["bases"]["BracketSign"]["field"]
    fpoly = ccw([(yc + x, z) for x, z in lancet(fw, hs - 0.09, rise - 0.03, z0=0.09)])
    field_both(fpoly, "YZ", 0.11, K["field"])
    for y in (yc - 0.55, yc + 0.55):
        z_top = hs + rise * math.sin((1 - abs((y - yc) / (pw / 2))) * PI / 2) ** 0.75
        tube(f"Strap{y:.2f}", [(0, y, za - 0.04), (0, y, z_top - 0.05)], 0.025, ir, poly=True)
        hoop(f"Eye{y:.2f}", (0, y, za - 0.06), 0.06, "X", ir, thick=0.016)
    sphere("PanelFinial", 0.06, (0, yc, hs + rise + 0.04), gl, seg=10, rings=6)
    cone("PanelDrop", 0.07, 0.0, 0.18, (0, yc, -0.08), gl, verts=12, rot=(PI, 0, 0))
    return _dims()


def arrow_board(M, sx=1):
    """A pointing board: brass-edged black iron, an arrow head one end and a fishtail the other, on two stand-off studs."""
    K = kit(M)
    br, gl, ir = K["plaque"], K["gilt"], K["iron"]
    L0, L1, Lh = -1.65, 1.05, 1.65
    h, hh = 0.8, 1.0
    cz = 0.5
    shape = [(L0, cz - h / 2), (L1, cz - h / 2), (L1, cz - hh / 2), (Lh, cz), (L1, cz + hh / 2), (L1, cz + h / 2),
             (L0, cz + h / 2), (L0 + 0.28, cz)]
    shape = ccw([(sx * x, z) for x, z in shape])
    D = 0.06
    prism("Board", shape, -D / 2, D, br, plane="XZ", bevel=0.012)
    inner = inset(shape, 0.07)
    prism("Inlay", inner, -D - 0.004, 0.008, ir, plane="XZ")
    outline("Rim", inset(shape, 0.03), -D - 0.005, 0.014, br)
    # the Field is the board's body (tail notch to the head's shoulders), a hair in front of the inlay; the head stays iron
    fpoly = ccw([(sx * x, z) for x, z in ((L0 + 0.1, cz - 0.3), (L1, cz - 0.3), (L1, cz + 0.3), (L0 + 0.1, cz + 0.3),
                                          (L0 + 0.38, cz))])
    field_xz(fpoly, -D - 0.016, 0.01, K["field"])
    rosette("Stud", sx * 1.32, -D - 0.018, cz, gl, r=0.045)
    return _dims()


def arrow_board_left(M):
    return arrow_board(M, sx=-1)


def floor_stand(M):
    """A free-standing sign: a weighted cast-iron foot with ogee mouldings, a fluted post, a gilt collar, two scroll brackets
    and a double-sided lancet panel with a gilt finial; 4.9 tall."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    lathe("Foot", [(0, 0), (0.8, 0), (0.8, 0.06), (0.72, 0.1), (0.6, 0.12), (0.5, 0.2), (0.36, 0.24), (0.3, 0.3), (0.16, 0.36),
                   (0.12, 0.42), (0, 0.42)], ir, seg=32)
    lathe("Post", [(0, 0.4), (0.09, 0.4), (0.08, 2.25), (0, 2.25)], ir, seg=16, flute=(8, 0.012))
    lathe("Collar", [(0, 2.21), (0.13, 2.21), (0.15, 2.27), (0.12, 2.35), (0.15, 2.41), (0.1, 2.47), (0, 2.47)], gl, seg=16)
    lathe("Knot", [(0, 1.0), (0.12, 1.0), (0.15, 1.06), (0.12, 1.12), (0, 1.12)], gl, seg=16)
    pw, hs, rise = 1.8, 1.45, 0.7
    z0 = 2.5
    poly = lancet(pw, hs, rise, z0=z0)
    prism("Panel", poly, 0, 0.09, ir, plane="XZ", bevel=0.012)
    for sy in (-1, 1):
        outline(f"PFrame{sy}", inset(poly, 0.03), sy * 0.05, 0.026, ir)
    fw, fh = SPEC["bases"]["FloorStand"]["field"]
    fpoly = lancet(fw, hs - 0.08, rise - 0.04, z0=z0 + 0.08)
    field_both(fpoly, "XZ", 0.11, K["field"])
    for sx in (-1, 1):
        scroll_curl(f"Bracket{sx}", sx * 0.4, 0, z0 - 0.12, 0.18, 1.2, ir, sx=sx, thick=0.028, start=-PI / 2)
        tube(f"BrArm{sx}", [(sx * 0.07, 0, 2.41), (sx * 0.4, 0, z0 - 0.3), (sx * 0.7, 0, z0 + 0.01)], 0.028, ir)
    B43.finial("Finial", 0, 0, z0 + hs + rise - 0.04, ir, s=0.6)
    sphere("FinialBall", 0.045, (0, 0, z0 + hs + rise + 0.22), gl, seg=10, rings=6)
    return _dims()


def exit_lantern(M):
    """A lit way-out lantern for over a door: an iron box with corner colonnettes, a pitched hood with cresting and a
    finial, a drip tray with a knop; the front is Glass (the text sits on it) and a warm Glow panel lights it from behind."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    W, H, D = 2.3, 0.85, 0.5
    z0 = 0.2
    box("Back", (W, 0.06, H), (0, -0.03, z0 + H / 2), ir, bevel=0.01)
    box("Top", (W + 0.08, D, 0.07), (0, -D / 2, z0 + H + 0.035), ir, bevel=0.015)
    box("Bottom", (W + 0.08, D, 0.07), (0, -D / 2, z0 - 0.035), ir, bevel=0.015)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.06, D - 0.06, H), (sx * (W / 2 - 0.03), -D / 2, z0 + H / 2), ir, bevel=0.01)
        cyl(f"Col{sx}", 0.04, H, (sx * (W / 2 + 0.0), -D + 0.02, z0 + H / 2), ir, verts=12)
        sphere(f"ColCap{sx}", 0.06, (sx * W / 2, -D + 0.02, z0 + H + 0.1), gl, seg=10, rings=6)
    # mullion bars in front of the glass (a light iron grille), leaving the middle clear for the text
    for z in (z0 + 0.06, z0 + H - 0.06):
        box(f"Rail{z:.2f}", (W - 0.06, 0.04, 0.05), (0, -D + 0.005, z), ir, bevel=0.01)
    # hood: a shallow pitched roof with cresting
    hood = ccw([(-W / 2 - 0.1, 0), (W / 2 + 0.1, 0), (W / 2 + 0.1, 0.05), (0, 0.3), (-W / 2 - 0.1, 0.05)])
    prism("Hood", [(x, z + z0 + H + 0.07) for x, z in hood], -D / 2, D + 0.08, ir, plane="XZ", bevel=0.01)
    for k in range(9):
        x = -1.0 + k * 0.25
        zt = z0 + H + 0.07 + 0.05 + (0.25 * (1 - abs(x) / (W / 2 + 0.1)))
        cone(f"Crest{k}", 0.035, 0.0, 0.12, (x, -D / 2, zt + 0.06), ir, verts=4)
    B43.finial("HoodFinial", 0, -D / 2, z0 + H + 0.32, ir, s=0.6)
    lathe("Knop", [(0, 0), (0.03, 0), (0.08, 0.06), (0.05, 0.12), (0.06, 0.16), (0, 0.2)], gl, seg=12, loc=(0, -D / 2, -0.0))
    set_group("Glass")
    fw, fh = SPEC["bases"]["ExitLantern"]["field"]
    box("Pane", (fw, 0.02, fh), (0, -D + 0.04, z0 + H / 2), K["field"], bevel=0.0)
    set_group("Glow")
    box("Light", (W - 0.2, 0.03, H - 0.16), (0, -0.09, z0 + H / 2), K["field"], bevel=0.0)
    set_group("Main")
    return _dims()


def wing_directory(M):
    """The wing directory: a big double-sided board hung from a corridor ceiling, a header for the wing's name over up to
    five rows of destinations (each an icon, a name and an arrow; SignKit draws them from Row1..Row5). Black iron frame and
    cresting, a pointed gable with a quatrefoil, gilt corner caps and a gilt rail under the header, two chains to ceiling
    roses. The top (the roses) is 5.4 above the pivot."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    W, H, T = 4.6, 3.4, 0.12
    z0 = 0.2
    rect = ccw([(-W / 2, z0), (W / 2, z0), (W / 2, z0 + H), (-W / 2, z0 + H)])
    prism("Board", rect, 0, T, ir, plane="XZ", bevel=0.015)
    for sy in (-1, 1):
        outline(f"Frame{sy}", inset(rect, 0.03), sy * (T / 2 + 0.005), 0.03, ir)
    fw, fh = SPEC["bases"]["WingDirectory"]["field"]
    zc = z0 + H / 2
    fpoly = ccw([(-fw / 2, zc - fh / 2), (fw / 2, zc - fh / 2), (fw / 2, zc + fh / 2), (-fw / 2, zc + fh / 2)])
    field_both(fpoly, "XZ", T + 0.02, K["field"])
    # the gilt rail under the header, at the layout's header line
    hy = SPEC["bases"]["WingDirectory"]["layout"]["Title"][3]
    zr = zc + fh / 2 - fh * hy
    for sy in (-1, 1):
        tube(f"Rail{sy}", [(-fw / 2 + 0.06, sy * (T / 2 + 0.02), zr), (fw / 2 - 0.06, sy * (T / 2 + 0.02), zr)], 0.016, gl, poly=True)
    for sx in (-1, 1):
        for sz in (0, 1):
            box(f"Cap{sx}{sz}", (0.18, T + 0.06, 0.18), (sx * (W / 2 - 0.05), 0, z0 + sz * H + (0.05 if sz == 0 else -0.05)), gl,
                bevel=0.02)
        cone(f"Drop{sx}", 0.06, 0.0, 0.18, (sx * (W / 2 - 0.05), 0, z0 - 0.09), gl, verts=12, rot=(PI, 0, 0))
    # cresting along the top, a pointed gable in the middle with a quatrefoil, finials at the corners
    top = z0 + H
    gpoly = ccw([(-0.95, top), (0.95, top)] + B43.arch_xz(0.95, -0.95, top, 0.62, 10)[1:-1])
    prism("Gable", gpoly, 0, T * 0.8, ir, plane="XZ", bevel=0.012)
    for sy in (-1, 1):
        _quatrefoil(f"Foil{sy}", 0, sy * (T * 0.4 + 0.01), top + 0.26, 0.15, gl)
    for k in range(14):
        x = -2.15 + k * (4.3 / 13)
        if abs(x) < 1.0:
            continue
        cone(f"Crest{k}", 0.035, 0.0, 0.16, (x, 0, top + 0.08), ir, verts=4)
    B43.finial("Apex", 0, 0, top + 0.58, ir, s=0.6)
    for sx in (-1, 1):
        B43.finial(f"Corner{sx}", sx * (W / 2 - 0.05), 0, top + 0.0, ir, s=0.5)
        hoop(f"Eye{sx}", (sx * 1.7, 0, top + 0.12), 0.08, "X", ir, thick=0.02)
        B43.chain(f"Chain{sx}", [(sx * 1.7, 0, top + 0.2), (sx * 1.7, 0, 5.33)], ir, r=0.07, thick=0.014)
        cyl(f"Rose{sx}", 0.17, 0.05, (sx * 1.7, 0, 5.375), ir, verts=16, bevel=0.01)
        sphere(f"RoseKnob{sx}", 0.05, (sx * 1.7, 0, 5.33), gl, seg=8, rings=4)
    return _dims()


BUILDERS = {
    "BrassPlaque": brass_plaque,
    "EnamelPlate": enamel_plate,
    "LintelTablet": lintel_tablet,
    "Roundel": roundel,
    "CorridorSign": corridor_sign,
    "BracketSign": bracket_sign,
    "ArrowBoard": arrow_board,
    "ArrowBoardLeft": arrow_board_left,
    "FloorStand": floor_stand,
    "ExitLantern": exit_lantern,
    "WingDirectory": wing_directory,
}
P.BUILD.update(BUILDERS)


# ------------------------------------------------------------------ preview (the template look, with a face applied)

FACE_DIR = "E:/NH-Work/props50/faces"


def _face_planes(objs, name):
    """For the preview only: lay the face image(s) E:/NH-Work/props50/faces/<name>_<Face>.png over the Field's faces."""
    field = next((o for o in objs if o.name.endswith("_Field") or o.name.endswith("_Glass")), None)
    if field is None:
        return
    lo = Vector([min((field.matrix_world @ Vector(c))[k] for c in field.bound_box) for k in range(3)])
    hi = Vector([max((field.matrix_world @ Vector(c))[k] for c in field.bound_box) for k in range(3)])
    for face in SPEC["bases"][name]["faces"]:
        img = os.path.join(FACE_DIR, f"{name}_{face}.png")
        if not os.path.exists(img):
            continue
        if face in ("Front", "Back"):
            w, h = hi.x - lo.x, hi.z - lo.z
            y = lo.y - 0.004 if face == "Front" else hi.y + 0.004
            loc = ((lo.x + hi.x) / 2, y, (lo.z + hi.z) / 2)
            rot = (PI / 2, 0, 0) if face == "Front" else (PI / 2, 0, PI)
        else:
            w, h = hi.y - lo.y, hi.z - lo.z
            x = lo.x - 0.004 if face == "Left" else hi.x + 0.004
            loc = (x, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2)
            rot = (PI / 2, 0, -PI / 2) if face == "Left" else (PI / 2, 0, PI / 2)
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
        pl = bpy.context.active_object
        pl.scale = (w, h, 1)
        m = bpy.data.materials.new(f"Face{face}")
        m.use_nodes = True
        nt = m.node_tree
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(img)
        tx.interpolation = "Cubic"
        nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
        nt.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
        bs.inputs["Metallic"].default_value = 0.55 if SPEC["bases"][name]["ink"] == "Gilt" else 0.0
        bs.inputs["Roughness"].default_value = 0.32
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
        pl.data.materials.append(m)


def preview(objs, name, dims, suffix=""):
    """The template look: the Field in its default enamel, the face image over it, ExitLantern's Glow lit."""
    tint = SPEC["bases"][name]["tint"]
    for ob in objs:
        if ob.name.endswith("_Field") and tint:
            m = bpy.data.materials.new("PreviewField")
            m.use_nodes = True
            bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            rgb = tuple(0.72 * c ** 2.2 for c in FIELD_RGB[tint])   # x the baked enamel's albedo
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Roughness"].default_value = 0.28
            ob.data.materials.clear()
            ob.data.materials.append(m)
    B46.GLOW.setdefault(name, GLOW.get(name, {}))
    _face_planes(objs, name)
    B46.CAM[name] = {"CorridorSign": 0.1, "Roundel": 0.12, "BrassPlaque": 0.1}.get(name, 0.18)
    B46.preview(objs, name, dims, suffix)
UV_WEIGHT = {"Field": 0.6, "Glow": 0.3, "Glass": 0.3, "Main": 1.0}
