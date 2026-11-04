"""Props batch 14 (2026-11-03): Mrs. Okada's concession stand, remodelled for nh_props.py in Nightmare High's style.

  ConcessionStand  a cast-iron kiosk in oxblood enamel with brass trim: fluted iron corner columns, a pitched slate
                   canopy with iron cresting, finials and a perched crow, a carved sign board over a pierced iron frieze,
                   a crimson and black striped awning whose scalloped valance sways (Cloth), two hanging iron lanterns
                   (Glass, Glow), a black marble counter with a brass nosing and foot rail, blind lancet panels and the
                   school crest on the counter front, sweet jars (Glass) and a glass cake cloche, pastries, apples,
                   candy, corked potion-soda bottles and a brass bell on the counter, shelves of snacks either side of
                   a framed menu board on the back wall.

It keeps the greybox stand's footprint (Services.Features.Concession) so Mrs. Okada, the buy prompt and the lunch queue
still fit: 9.6 wide (X +-4.8), the back wall's rear face at Y = +3.45, the counter top's front edge at Y = -3.45 and
its surface at Z = 3.55, and a clear space behind the counter (X +-1.5, Y 0..1.2, up to Z 8) for her to stand in.
The sign board and the menu board are plain flat panels in carved frames: the game draws their text with SurfaceGuis.

Front faces -Y, Z is up, the origin is at the bottom centre.
Registered into nh_props.BUILD on import.
"""
import math
import random

from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, prism, _dims, flat
from nh_props_batch5 import marble
from nh_props_batch8 import _lancet, _foil, _spirelet, _raven, _lantern, _lights, _pointed
from nh_props_batch9 import wax_mat

W = 4.8            # half width
YB = 3.45          # back wall, rear face
YW = 3.10          # back wall, inner face
YF = -3.45         # counter top, front edge
ZC = 3.55          # counter top surface
ZE = 8.05          # wall tops / column abacus
YE, ZEV = -4.35, 8.1   # front eave line (the frieze and sign stand on it)
YR, ZR = -0.35, 10.3   # ridge
YBE = 3.62         # back eave

# where the game lays its text: model-local centre (x, y, z) of each face and its (width, height); both face -Y
SIGN_FACE = ((0.0, -4.46, 9.35), (7.2, 1.3))
MENU_FACE = ((0.0, 3.015, 5.6), (5.4, 3.4))


def _mats(M):
    return {
        "enamel": material("OxbloodEnamel", "NH_PaintedMetal", tint=(0.2, 0.025, 0.035), scale=1.1, wear=0.65, wear_metal=True),
        "enamelin": material("OxbloodShade", "NH_PaintedMetal", tint=(0.09, 0.016, 0.022), scale=0.8, rough_add=0.12, wear=0.3,
                             wear_metal=True),
        "black": material("BlackEnamel", "NH_PaintedMetal", tint=(0.025, 0.024, 0.028), scale=1.1, wear=0.55, wear_metal=True),
        "marble": marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0,
                         detail=2.5),
        "lacquer": flat("SignLacquer", (0.018, 0.016, 0.02), 0.32, dirt=0.4),
        "menu": flat("MenuSlate", (0.035, 0.038, 0.04), 0.85, dirt=0.3),
        "canvas_r": material("CanvasCrimson", "NH_Leather", tint=(0.3, 0.03, 0.045), scale=4.0, normal=0.3, rough_add=0.45, wear=0.05,
                             dirt=0.6),
        "canvas_k": material("CanvasBlack", "NH_Leather", tint=(0.03, 0.028, 0.032), scale=4.0, normal=0.3, rough_add=0.45, wear=0.05,
                             dirt=0.6),
        "floor": material("StandFloor", "NH_Slate", tint=(0.2, 0.21, 0.21), scale=0.25, rough_mul=0.7, rough_add=0.3, normal=0.4,
                          wear=0.2),
    }


# ------------------------------------------------------------------ structure

def _column(prefix, x, y, M):
    """A fluted cast-iron corner column with a moulded base, brass bands and a bell capital."""
    prof = [(0.0, 0.15), (0.27, 0.15), (0.27, 0.27), (0.22, 0.33), (0.22, 0.42), (0.17, 0.5), (0.17, 7.35), (0.2, 7.5),
            (0.27, 7.78), (0.3, 7.86), (0.0, 7.86)]
    lathe(f"{prefix}Shaft", prof, M["iron"], seg=24, loc=(x, y, 0), flute=(12, 0.12))
    for k, z in enumerate((1.05, ZC, 6.1)):
        hoop(f"{prefix}Band{k}", (x, y, z), 0.185, "Z", M["brass"], thick=0.028)
    box(f"{prefix}Abacus", (0.6, 0.6, 0.16), (x, y, 7.94), M["iron"], bevel=0.03)
    box(f"{prefix}Plinth", (0.58, 0.58, 0.12), (x, y, 0.21), M["iron"], bevel=0.02)
    # four little stiff-leaf hooks under the abacus
    for j in range(4):
        a = j * math.pi / 2 + math.pi / 4
        sphere(f"{prefix}Leaf{j}", 0.07, (x + math.cos(a) * 0.27, y + math.sin(a) * 0.27, 7.72), M["iron"], seg=6, rings=3,
               scale=(1, 1, 1.6))


def _stand_body(M, X):
    rnd = random.Random(14)
    # floor: a slate deck in an iron kerb
    box("Floor", (2 * W, YB - YF, 0.14), (0, (YB + YF) / 2, 0.07), X["floor"], bevel=0.015)
    for sx in (-1, 1):
        box(f"KerbSide{sx}", (0.1, YB - YF, 0.16), (sx * (W - 0.05), (YB + YF) / 2, 0.08), M["iron"], bevel=0.01)
    box("KerbBack", (2 * W, 0.1, 0.16), (0, YB - 0.05, 0.08), M["iron"], bevel=0.01)

    # back wall: enamel sheet, iron ribs inside and out, brass rivets
    hz = ZE - 0.14
    box("BackWall", (2 * W, 0.27, hz), (0, YW + 0.135, 0.14 + hz / 2), X["enamel"], bevel=0.02)
    for x in (-W + 0.1, -2.9, 2.9, W - 0.1):
        box(f"BackRibIn{x:.1f}", (0.14, 0.06, hz), (x, YW - 0.03, 0.14 + hz / 2), M["iron"], bevel=0.012)
    for x in (-W + 0.1, -1.6, 1.6, W - 0.1):
        box(f"BackRibOut{x:.1f}", (0.14, 0.07, hz), (x, YB - 0.035, 0.14 + hz / 2), M["iron"], bevel=0.012)
    for z in (0.3, 3.4, ZE - 0.12):
        box(f"BackRailIn{z:.1f}", (2 * W, 0.06, 0.14), (0, YW - 0.03, z), M["iron"], bevel=0.012)
        box(f"BackRailOut{z:.1f}", (2 * W, 0.07, 0.14), (0, YB - 0.035, z), M["iron"], bevel=0.012)
    # blind lancets on the outside face, between the outer ribs
    for k, cx in enumerate((-3.2, 0.0, 3.2)):
        _lancet(f"BackLancet{k}", cx, YB - 0.005, 3.7, 1.15, 5.6, 7.4, M["iron"], thick=0.035)
        for z in (1.0, 2.6):
            box(f"BackPanel{k}{z}", (2.4, 0.03, 0.04), (cx, YB - 0.012, z), M["brass"], bevel=0.0, segments=1)

    # side walls: solid to the counter all the way, solid above it behind the counter, an arched opening at the front
    for sx in (-1, 1):
        xw = sx * (W - 0.125)
        box(f"SideLow{sx}", (0.25, YB + 3.05, ZC - 0.25 - 0.14), (xw, (YB - 3.05) / 2, 0.14 + (ZC - 0.39) / 2), X["enamel"], bevel=0.02)
        y0 = 0.25
        box(f"SideHigh{sx}", (0.25, YB - y0, ZE - ZC + 0.25), (xw, (YB + y0) / 2, ZC - 0.25 + (ZE - ZC + 0.25) / 2), X["enamel"],
            bevel=0.02)
        # iron frame round the side panels
        for y in (y0 + 0.07, YB - 0.07):
            box(f"SideStile{sx}{y:.1f}", (0.31, 0.12, ZE - 0.14), (xw - sx * 0.03, y, 0.14 + (ZE - 0.14) / 2), M["iron"], bevel=0.012)
        box(f"SideRail{sx}", (0.31, YB + 3.05, 0.12), (xw - sx * 0.03, (YB - 3.05) / 2, ZC - 0.31), M["iron"], bevel=0.012)
        box(f"SideCap{sx}", (0.31, YB + 3.25, 0.14), (xw - sx * 0.03, (YB - 3.25) / 2, ZE - 0.07), M["iron"], bevel=0.012)
        # the open bay's pointed iron arch, from the column to the solid panel
        cy = (-3.25 + y0) / 2
        hw = (y0 + 3.25) / 2 - 0.12
        pts = [(xw, cy + px, pz) for px, pz in _pointed(hw, 6.35, ZE - 0.2, 10)]
        tube(f"SideArch{sx}", pts, 0.05, M["iron"], square=True, poly=True)
        _foil(f"SideFoil{sx}", 0.0, 0.0, 0.0, 0.2, M["brass"], lobes=4, thick=0.02)
        # move the five foil parts into the spandrel above the arch (built facing -Y at the origin; turn them to face X)
        for ob in P.PARTS[-5:]:
            ob.matrix_world = Matrix.Translation((xw + sx * 0.1, cy, ZE - 0.45)) @ Matrix.Rotation(sx * math.pi / 2, 4, "Z") @ ob.matrix_world
        # brass rivets on the low panel
        for k in range(6):
            for z in (0.5, ZC - 0.55):
                sphere(f"SideRivet{sx}{k}{z:.1f}", 0.03, (xw + sx * 0.13, -2.7 + k * 1.15, z), M["brass"], seg=6, rings=3)

    for sx in (-1, 1):
        _column(f"Col{sx}", sx * 4.45, -3.25, M)

    # counter: an enamel front with blind lancets and the crest, a brass kick plate, a black marble top, a foot rail
    cx0, cx1 = -4.2, 4.2
    yb0, yb1 = -3.05, -0.85
    box("CounterBody", (cx1 - cx0, yb1 - yb0, ZC - 0.25 - 0.14), (0, (yb0 + yb1) / 2, 0.14 + (ZC - 0.39) / 2), X["enamel"], bevel=0.025)
    box("CounterKick", (cx1 - cx0 + 0.02, 0.04, 0.32), (0, yb0 - 0.02, 0.32), M["brass"], bevel=0.01)
    box("CounterPlinth", (cx1 - cx0 + 0.06, 0.12, 0.1), (0, yb0 - 0.02, 0.19), M["iron"], bevel=0.015)
    box("CounterFrieze", (cx1 - cx0 + 0.04, 0.1, 0.16), (0, yb0 - 0.03, ZC - 0.33), M["iron"], bevel=0.015)
    for k, cx in enumerate((-3.35, -1.95, 1.95, 3.35)):
        _lancet(f"CounterLancet{k}", cx, yb0 - 0.02, 0.62, 0.52, 1.95, 2.9, M["iron"], thick=0.03)
        box(f"CounterInset{k}", (1.04, 0.02, 2.0), (cx, yb0 - 0.005, 1.72), X["enamelin"], bevel=0.0, segments=1)
    for k, cx in enumerate((-4.0, -2.65, -1.25, 1.25, 2.65, 4.0)):
        box(f"CounterMullion{k}", (0.1, 0.06, ZC - 0.75), (cx, yb0 - 0.03, 0.42 + (ZC - 0.75) / 2), M["iron"], bevel=0.01)
    # the crest: a crimson shield with a brass border, crescent and three stars, on a scroll
    shield = [(-0.46, 0.55), (0.46, 0.55), (0.46, 0.05), (0.3, -0.32), (0.0, -0.55), (-0.3, -0.32), (-0.46, 0.05)]
    zc = 1.9
    prism("CrestShield", [(x, zc + z) for x, z in shield], yb0 - 0.04, 0.06, M["crimson"], bevel=0.012)
    tube("CrestBorder", [(x, yb0 - 0.075, zc + z) for x, z in shield], 0.025, M["brass"], closed=True, square=True, poly=True)
    moon = [(math.cos(a) * 0.24, zc + 0.08 + math.sin(a) * 0.24) for a in [math.radians(40 + i * 14) for i in range(21)]]
    moon += [(math.cos(a) * 0.18 + 0.07, zc + 0.08 + math.sin(a) * 0.18) for a in [math.radians(320 - i * 14) for i in range(21)]]
    prism("CrestMoon", moon, yb0 - 0.085, 0.03, M["brass"])
    for k, (sx, sz) in enumerate(((-0.24, 0.36), (0.24, 0.36), (0.0, -0.3))):
        star = []
        for i in range(10):
            r = 0.08 if i % 2 == 0 else 0.035
            a = math.pi / 2 + i * math.pi / 5
            star.append((sx + math.cos(a) * r, zc + sz + math.sin(a) * r))
        prism(f"CrestStar{k}", star, yb0 - 0.085, 0.025, M["brass"])
    scroll = [(-0.75, 0.0), (-0.6, 0.06), (0.6, 0.06), (0.75, 0.0), (0.66, -0.16), (0.75, -0.3), (0.6, -0.24), (-0.6, -0.24),
              (-0.75, -0.3), (-0.66, -0.16)]
    prism("CrestScroll", [(x, zc - 0.62 + z) for x, z in scroll], yb0 - 0.05, 0.04, X["black"], bevel=0.008)
    tube("CrestScrollEdge", [(x, yb0 - 0.075, zc - 0.62 + z) for x, z in scroll], 0.012, M["brass"], closed=True, poly=True)
    # the marble top and its brass nosing
    box("CounterTop", (8.5, -0.62 - (YF + 0.05), 0.25), (0, (YF + 0.05 - 0.62) / 2, ZC - 0.125), X["marble"], bevel=0.02)
    box("CounterNosing", (8.54, 0.05, 0.22), (0, YF + 0.025, ZC - 0.12), M["brass"], bevel=0.008)
    # brass foot rail on iron brackets
    tube("FootRail", [(-3.95, -3.38, 0.62), (3.95, -3.38, 0.62)], 0.045, M["brass"], poly=True)
    for x in (-3.7, 0.0, 3.7):
        tube(f"FootBracket{x:.0f}", [(x, yb0 - 0.02, 0.85), (x, -3.3, 0.8), (x, -3.38, 0.62)], 0.025, M["iron"])
    for sx in (-1, 1):
        sphere(f"FootRailEnd{sx}", 0.06, (sx * 3.97, -3.38, 0.62), M["brass"], seg=10, rings=5)

    # inside: a low dark ceiling under the canopy, iron tie rods
    box("Ceiling", (2 * W - 0.3, YB - (-3.25), 0.06), (0, (YB - 3.25) / 2, ZE + 0.03), X["enamelin"], bevel=0.0, segments=1)
    for y in (-3.25, YB - 0.2):
        box(f"Beam{y:.1f}", (2 * W, 0.22, 0.24), (0, y, ZE + 0.1), M["iron"], bevel=0.02)
    return rnd


def _menu_and_shelves(M, X, rnd):
    set_group("Shelves")
    (mx, my, mz), (mw, mh) = MENU_FACE
    # the menu board: a slate panel in a carved iron frame with a small crocketed gablet on top
    box("MenuBoard", (mw, YW - my, mh), (mx, (YW + my) / 2, mz), X["menu"], bevel=0.005, segments=1)
    fr = [(mx - mw / 2 - 0.06, my - 0.04, mz - mh / 2 - 0.06), (mx + mw / 2 + 0.06, my - 0.04, mz - mh / 2 - 0.06),
          (mx + mw / 2 + 0.06, my - 0.04, mz + mh / 2 + 0.06), (mx - mw / 2 - 0.06, my - 0.04, mz + mh / 2 + 0.06)]
    tube("MenuFrame", fr, 0.07, M["iron"], closed=True, square=True, poly=True)
    tube("MenuFillet", [(x, y - 0.03, z) for x, y, z in fr], 0.018, M["brass"], closed=True, square=True, poly=True)
    top = mz + mh / 2 + 0.13
    gab = [(-0.9, 0.0), (0.9, 0.0), (0.0, 0.62)]
    prism("MenuGablet", [(x, top + z) for x, z in gab], YW - 0.05, 0.07, M["iron"], bevel=0.01)
    _foil("MenuGabletFoil", 0.0, YW - 0.1, top + 0.24, 0.13, M["brass"], lobes=3, thick=0.016)
    for k, t in enumerate((0.25, 0.5, 0.75)):
        sphere(f"MenuCrocketL{k}", 0.045, (-0.9 + 0.9 * t, YW - 0.07, top + 0.62 * t + 0.05), M["iron"], seg=6, rings=3, scale=(1, 1, 1.4))
        sphere(f"MenuCrocketR{k}", 0.045, (0.9 - 0.9 * t, YW - 0.07, top + 0.62 * t + 0.05), M["iron"], seg=6, rings=3, scale=(1, 1, 1.4))
    sphere("MenuFinial", 0.06, (0, YW - 0.07, top + 0.7), M["brass"], seg=8, rings=4)
    for sx in (-1, 1):
        _spirelet(f"MenuPin{sx}", sx * (mw / 2 + 0.06), YW - 0.08, mz + mh / 2 + 0.02, 0.55, 0.12, M["iron"])

    # shelves either side: iron brackets, black marble shelves, boxes, jars and bottles
    goods = [flat("BoxCrimson", (0.3, 0.03, 0.04), 0.6), flat("BoxInk", (0.05, 0.07, 0.16), 0.6), flat("BoxBone", (0.7, 0.64, 0.5), 0.7),
             flat("BoxMoss", (0.08, 0.16, 0.06), 0.6), flat("BoxPlum", (0.18, 0.04, 0.2), 0.6)]
    bottle = [flat("BottleGreen", (0.03, 0.2, 0.07), 0.08), flat("BottlePlum", (0.16, 0.02, 0.2), 0.08),
              flat("BottleAmber", (0.4, 0.17, 0.03), 0.08), flat("BottleRed", (0.35, 0.02, 0.03), 0.08)]
    cork = flat("Cork", (0.42, 0.3, 0.17), 0.85)
    for sx in (-1, 1):
        x0, x1 = sx * 2.95, sx * 4.5
        xa, xb = min(x0, x1), max(x0, x1)
        xm = (xa + xb) / 2
        for k, z in enumerate((1.35, 2.65, 3.95, 5.25, 6.55)):
            box(f"Shelf{sx}{k}", (xb - xa, 0.46, 0.06), (xm, YW - 0.23, z), X["marble"], bevel=0.01)
            box(f"ShelfLip{sx}{k}", (xb - xa, 0.025, 0.07), (xm, YW - 0.47, z + 0.02), M["brass"], bevel=0.005, segments=1)
            for xx in (xa + 0.12, xb - 0.12):
                tube(f"ShelfBracket{sx}{k}{xx:.1f}", [(xx, YW, z - 0.03), (xx, YW - 0.4, z - 0.03), (xx, YW, z - 0.38)], 0.018,
                     M["iron"], square=True, poly=True)
            # stock on this shelf
            x = xa + 0.12
            while x < xb - 0.2:
                kind = rnd.random()
                if kind < 0.45:
                    w, h = rnd.uniform(0.22, 0.34), rnd.uniform(0.3, 0.6)
                    if x + w > xb - 0.1:
                        break
                    m = rnd.choice(goods)
                    box(f"Box{sx}{k}{x:.2f}", (w, rnd.uniform(0.22, 0.32), h), (x + w / 2, YW - 0.22, z + 0.03 + h / 2), m, bevel=0.012)
                    box(f"BoxLabel{sx}{k}{x:.2f}", (w * 0.7, 0.01, h * 0.3), (x + w / 2, YW - 0.37, z + 0.03 + h * 0.55), M["brass"],
                        bevel=0.0, segments=1)
                    x += w + 0.04
                elif kind < 0.75:
                    r = 0.09
                    bm = rnd.choice(bottle)
                    prof = [(0.0, 0.0), (r, 0.0), (r, 0.26), (r * 0.45, 0.33), (r * 0.35, 0.42), (0.0, 0.42)]
                    lathe(f"Bottle{sx}{k}{x:.2f}", prof, bm, seg=12, loc=(x + r, YW - 0.22, z + 0.03))
                    cyl(f"BottleCork{sx}{k}{x:.2f}", r * 0.36, 0.06, (x + r, YW - 0.22, z + 0.48), cork, verts=8, bevel=0)
                    x += 2 * r + 0.05
                else:
                    r = 0.12
                    lathe(f"ShelfJar{sx}{k}{x:.2f}", [(0.0, 0.0), (r, 0.0), (r, 0.3), (r * 0.8, 0.34), (0.0, 0.34)],
                          rnd.choice(goods), seg=14, loc=(x + r, YW - 0.22, z + 0.03))
                    cyl(f"ShelfJarLid{sx}{k}{x:.2f}", r * 0.85, 0.05, (x + r, YW - 0.22, z + 0.39), M["brass"], verts=14, bevel=0.005)
                    x += 2 * r + 0.05
    set_group("Main")


# ------------------------------------------------------------------ canopy, sign, awning

def _slope(prefix, y0, z0, y1, z1, mat, width=2 * W, thick=0.12, inset=0.0):
    L = math.hypot(y1 - y0, z1 - z0)
    a = math.atan2(z1 - z0, y1 - y0)
    box(prefix, (width, L, thick), ((0.0), (y0 + y1) / 2, (z0 + z1) / 2 + inset), mat, bevel=0.015, rot=(a, 0, 0))
    return L, a


def _canopy(M, X):
    set_group("Roof")
    joint = flat("SlateJoint", (0.02, 0.022, 0.024), 0.9, dirt=0.3)
    # roof decks
    _slope("RoofFront", YE, ZEV, YR, ZR, M["iron"])
    _slope("RoofBack", YBE, ZEV, YR, ZR, M["iron"])
    # slate courses, each a little tilted so the lower edge stands proud (shingled)
    for prefix, (y0, z0) in (("SlateF", (YE, ZEV)), ("SlateB", (YBE, ZEV))):
        n = 7
        for k in range(n):
            t0, t1 = k / n, (k + 1.25) / n
            ya, za = y0 + (YR - y0) * t0, z0 + (ZR - z0) * t0
            yb, zb = y0 + (YR - y0) * min(t1, 1.0), z0 + (ZR - z0) * min(t1, 1.0)
            L = math.hypot(yb - ya, zb - za)
            a = math.atan2(zb - za, yb - ya)
            nz = 0.09
            c = Vector((0, (ya + yb) / 2, (za + zb) / 2 + nz))
            box(f"{prefix}{k}", (2 * W, L, 0.05), tuple(c), M["slate"], bevel=0.01, rot=(a, 0, 0))
            nrm = Vector((0, -math.sin(a), math.cos(a)))
            if nrm.z < 0:
                nrm = -nrm
            jc = c + nrm * 0.028
            x = -W + 0.3 + (0.3 if k % 2 else 0.0)
            while x < W - 0.1:
                box(f"{prefix}Joint{k}{x:.1f}", (0.022, L * 0.86, 0.01), (x, jc.y, jc.z), joint, bevel=0.0, rot=(a, 0, 0), segments=1)
                x += 0.6
    # gable ends: enamel triangles with an iron edge and a brass quatrefoil
    for sx in (-1, 1):
        x = sx * (W - 0.12)
        tri = [(YE + 0.05, ZEV), (YBE - 0.05, ZEV), (YR, ZR - 0.06)]
        prism(f"Gable{sx}", tri, x, 0.1, X["enamel"], plane="YZ", bevel=0.01)
        tube(f"GableEdge{sx}", [(x + sx * 0.06, y, z) for y, z in tri], 0.04, M["iron"], closed=True, square=True, poly=True)
        _foil(f"GableFoil{sx}", 0.0, 0.0, 0.0, 0.32, M["brass"], lobes=4, thick=0.025)
        for ob in P.PARTS[-5:]:
            ob.matrix_world = Matrix.Translation((x + sx * 0.08, YR + 0.1, ZEV + 0.8)) @ Matrix.Rotation(sx * math.pi / 2, 4, "Z") @ ob.matrix_world
    # ridge roll, cresting and finials
    cyl("RidgeRoll", 0.08, 2 * W - 0.2, (0, YR, ZR + 0.05), M["iron"], rot=(0, math.pi / 2, 0), verts=12, bevel=0)
    spear = [(-0.05, 0.0), (0.05, 0.0), (0.05, 0.2), (0.11, 0.18), (0.04, 0.3), (0.0, 0.42), (-0.04, 0.3), (-0.11, 0.18), (-0.05, 0.2)]
    x = -W + 0.45
    k = 0
    while x < W - 0.4:
        prism(f"Crest{k}", [(x + u, ZR + 0.1 + v) for u, v in spear], YR, 0.035, M["iron"])
        x += 0.42
        k += 1
    for sx in (-1, 1):
        prof = [(0.0, 0.0), (0.12, 0.0), (0.12, 0.1), (0.07, 0.16), (0.09, 0.3), (0.05, 0.42), (0.03, 0.75), (0.06, 0.8), (0.0, 0.98)]
        lathe(f"RidgeFinial{sx}", prof, M["iron"], seg=12, loc=(sx * (W - 0.15), YR, ZR + 0.05))
        sphere(f"RidgeFinialBall{sx}", 0.07, (sx * (W - 0.15), YR, ZR + 0.62), M["brass"], seg=10, rings=5)
    # a crow on the ridge, looking down at the queue
    _raven("Crow", Matrix.Translation((3.2, YR - 0.05, ZR + 0.12)) @ Matrix.Rotation(math.radians(-20), 4, "Z"),
           flat("CrowBlack", (0.015, 0.015, 0.02), 0.45), flat("CrowEye", (0.7, 0.55, 0.1), 0.3))
    # scrolled iron brackets under the front eave, on the columns
    for sx in (-1, 1):
        x = sx * 4.45
        tube(f"EaveBracket{sx}", [(x, -3.25, 6.9), (x, -3.6, 7.25), (x, -3.95, 7.85), (x, YE + 0.08, ZEV - 0.15)], 0.035, M["iron"])
        hoop(f"EaveCurl{sx}", (x, -3.55, 7.0), 0.1, "X", M["iron"], thick=0.018)
    set_group("Main")


def _sign(M, X):
    set_group("Sign")
    (sx0, sy, sz), (sw, sh) = SIGN_FACE
    # pierced iron frieze along the eave, under the sign
    box("Frieze", (2 * W, 0.08, 0.62), (0, YE - 0.02, ZEV + 0.25), X["black"], bevel=0.01)
    k = 0
    x = -W + 0.4
    while x < W - 0.3:
        _foil(f"FriezeFoil{k}", x, YE - 0.07, ZEV + 0.25, 0.18, M["iron"], lobes=3 if k % 2 else 4, thick=0.022)
        x += 0.6
        k += 1
    tube("FriezeEdgeTop", [(-W, YE - 0.07, ZEV + 0.56), (W, YE - 0.07, ZEV + 0.56)], 0.03, M["brass"], square=True, poly=True)
    tube("FriezeEdgeLow", [(-W, YE - 0.07, ZEV - 0.06), (W, YE - 0.07, ZEV - 0.06)], 0.035, M["iron"], square=True, poly=True)
    # the board: black lacquer, its face flat and clear for the game's lettering
    box("SignBoard", (sw, 0.1, sh), (sx0, sy + 0.05, sz), X["lacquer"], bevel=0.008, segments=1)
    fr = [(-sw / 2 - 0.08, sy - 0.03, sz - sh / 2 - 0.08), (sw / 2 + 0.08, sy - 0.03, sz - sh / 2 - 0.08),
          (sw / 2 + 0.08, sy - 0.03, sz + sh / 2 + 0.08), (-sw / 2 - 0.08, sy - 0.03, sz + sh / 2 + 0.08)]
    tube("SignFrame", fr, 0.075, M["iron"], closed=True, square=True, poly=True)
    tube("SignFillet", [(x, y - 0.04, z) for x, y, z in fr], 0.02, M["brass"], closed=True, square=True, poly=True)
    # crocketed gablet with the crest roundel, and pinnacles at the ends
    top = sz + sh / 2 + 0.15
    gab = [(-1.2, 0.0), (1.2, 0.0), (0.0, 0.82)]
    prism("SignGablet", [(x, top + z) for x, z in gab], sy + 0.04, 0.1, X["black"], bevel=0.01)
    tube("SignGabletEdge", [(x, sy - 0.03, top + z) for x, z in gab], 0.035, M["iron"], closed=True, square=True, poly=True)
    for k, t in enumerate((0.2, 0.4, 0.6, 0.8)):
        for s in (-1, 1):
            sphere(f"SignCrocket{s}{k}", 0.055, (s * 1.2 * (1 - t), sy - 0.02, top + 0.82 * t + 0.06), M["iron"], seg=6, rings=3,
                   scale=(1, 1, 1.4))
    hoop("SignRoundel", (0, sy - 0.04, top + 0.3), 0.2, "Y", M["brass"], thick=0.025)
    cyl("SignRoundelField", 0.18, 0.03, (0, sy - 0.02, top + 0.3), M["crimson"], rot=(math.pi / 2, 0, 0), verts=20, bevel=0.004)
    star = []
    for i in range(10):
        r = 0.11 if i % 2 == 0 else 0.045
        a = math.pi / 2 + i * math.pi / 5
        star.append((math.cos(a) * r, top + 0.3 + math.sin(a) * r))
    prism("SignStar", star, sy - 0.05, 0.02, M["brass"])
    sphere("SignFinial", 0.07, (0, sy - 0.0, top + 0.92), M["brass"], seg=8, rings=4)
    for s in (-1, 1):
        _spirelet(f"SignPin{s}", s * (sw / 2 + 0.2), sy + 0.02, ZEV + 0.56, 1.25, 0.18, M["iron"], crockets=2)
    set_group("Main")


def _awning(M, X):
    """A short striped canvas lip out from under the frieze, and its scalloped valance, which sways (Cloth)."""
    y0, z0 = YE - 0.1, ZEV - 0.12
    y1, z1 = -4.85, 7.62
    n = 16
    sw = 2 * W / n
    L = math.hypot(y1 - y0, z1 - z0)
    a = math.atan2(z1 - z0, y1 - y0)
    for k in range(n):
        x = -W + sw * (k + 0.5)
        box(f"Canvas{k}", (sw, L, 0.03), (x, (y0 + y1) / 2, (z0 + z1) / 2), X["canvas_r"] if k % 2 == 0 else X["canvas_k"], bevel=0.0,
            rot=(a, 0, 0), segments=1)
    tube("AwningRod", [(-W, y1, z1), (W, y1, z1)], 0.03, M["iron"], poly=True)
    for s in (-1, 1):
        tube(f"AwningArm{s}", [(s * (W - 0.05), y0, z0), (s * (W - 0.05), y1, z1)], 0.025, M["iron"], poly=True)
        sphere(f"AwningRodEnd{s}", 0.05, (s * (W - 0.05), y1, z1), M["brass"], seg=8, rings=4)
    # the valance: one scallop per stripe, brass tassels between
    set_group("Cloth", hinge=(0, y1, z1), swing=1)
    depth = 0.55
    for k in range(n):
        x = -W + sw * (k + 0.5)
        poly = [(x - sw / 2, z1), (x + sw / 2, z1), (x + sw / 2, z1 - depth * 0.55)]
        for i in range(1, 10):
            t = i / 10
            poly.append((x + sw / 2 - sw * t, z1 - depth * 0.55 - depth * 0.45 * math.sin(t * math.pi)))
        poly.append((x - sw / 2, z1 - depth * 0.55))
        prism(f"Valance{k}", poly, y1 - 0.02, 0.025, X["canvas_r"] if k % 2 == 0 else X["canvas_k"])
    tube("ValanceBinding", [(-W, y1 - 0.04, z1 - 0.04), (W, y1 - 0.04, z1 - 0.04)], 0.018, M["brass"], poly=True)
    for k in range(n + 1):
        x = max(-W + 0.05, min(W - 0.05, -W + sw * k))
        zt = z1 - depth * 0.55
        sphere(f"TasselKnot{k}", 0.03, (x, y1 - 0.04, zt - 0.02), M["brass"], seg=6, rings=3)
        cone(f"Tassel{k}", 0.035, 0.012, 0.16, (x, y1 - 0.04, zt - 0.12), M["brass"], verts=8, rot=(math.pi, 0, 0))
    set_group("Main")


# ------------------------------------------------------------------ counter goods

def _goods(M, X, rnd):
    set_group("Goods")
    glassy = []          # (name, prof, loc) for the Glass piece, added after
    candy = [flat("CandyRed", (0.5, 0.03, 0.04), 0.25), flat("CandyGreen", (0.08, 0.4, 0.1), 0.25), flat("CandyGold", (0.7, 0.45, 0.06), 0.25),
             flat("CandyBone", (0.85, 0.8, 0.7), 0.25), flat("CandyPlum", (0.3, 0.05, 0.36), 0.25)]
    # three sweet jars on the right, full of humbugs, brass lids
    for k, (x, y, r, h) in enumerate(((1.95, -2.35, 0.26, 0.72), (2.62, -2.35, 0.26, 0.72), (3.29, -2.35, 0.26, 0.72), (3.95, -1.5, 0.2, 0.6))):
        z = ZC
        prof = [(0.0, 0.0), (r, 0.0), (r, h * 0.82), (r * 0.72, h * 0.9), (r * 0.7, h), (0.0, h)]
        glassy.append((f"SweetJar{k}", prof, (x, y, z)))
        cyl(f"JarLid{k}", r * 0.78, 0.07, (x, y, z + h + 0.035), M["brass"], verts=16, bevel=0.006)
        sphere(f"JarKnob{k}", 0.045, (x, y, z + h + 0.1), M["brass"], seg=8, rings=4)
        m = candy[k % len(candy)]
        m2 = candy[(k + 2) % len(candy)]
        rr = 0.06
        for j in range(int(h * 0.72 / (rr * 1.6))):
            zz = z + 0.07 + j * rr * 1.55
            for i in range(7):
                a = i / 7 * 2 * math.pi + j * 0.45
                d = (r - rr - 0.03) * (0.55 if i % 2 else 0.95)
                sphere(f"Humbug{k}{j}{i}", rr, (x + math.cos(a) * d, y + math.sin(a) * d, zz), m if (i + j) % 3 else m2, seg=8, rings=4)
    # the brass bell
    lathe("Bell", [(0.0, 0.0), (0.14, 0.0), (0.14, 0.02), (0.12, 0.06), (0.08, 0.14), (0.03, 0.18), (0.0, 0.19)], M["brass"], seg=16,
          loc=(1.2, -2.95, ZC))
    cyl("BellPlate", 0.17, 0.02, (1.2, -2.95, ZC + 0.01), M["iron"], verts=16, bevel=0.004)
    sphere("BellPush", 0.03, (1.2, -2.95, ZC + 0.21), M["iron"], seg=6, rings=3)
    # apples in an iron wire basket
    bx, by = 3.55, -2.95
    lathe("Basket", [(0.0, 0.0), (0.22, 0.0), (0.3, 0.06), (0.34, 0.16), (0.3, 0.16), (0.27, 0.07), (0.0, 0.04)], M["iron"], seg=16,
          loc=(bx, by, ZC))
    hoop("BasketRim", (bx, by, ZC + 0.16), 0.34, "Z", M["brass"], thick=0.015)
    apple = flat("Apple", (0.42, 0.04, 0.035), 0.35)
    stalk = flat("Stalk", (0.15, 0.1, 0.05), 0.8)
    for i, (dx, dy, dz) in enumerate(((0.0, 0.0, 0.17), (0.15, 0.05, 0.13), (-0.14, 0.07, 0.13), (0.04, -0.15, 0.13), (-0.06, 0.12, 0.27))):
        sphere(f"Apple{i}", 0.1, (bx + dx, by + dy, ZC + dz), apple, seg=10, rings=6, scale=(1, 1, 0.88))
        tube(f"AppleStalk{i}", [(bx + dx, by + dy, ZC + dz + 0.08), (bx + dx + 0.02, by + dy, ZC + dz + 0.13)], 0.008, stalk, poly=True)
    # pastries under a glass cloche on a brass cake stand, on the left
    cx, cy = -2.3, -2.2
    lathe("CakeStand", [(0.0, 0.0), (0.18, 0.0), (0.16, 0.03), (0.05, 0.06), (0.04, 0.26), (0.06, 0.3), (0.42, 0.3), (0.44, 0.33),
                        (0.0, 0.33)], M["brass"], seg=24, loc=(cx, cy, ZC))
    crust = flat("Pastry", (0.55, 0.3, 0.1), 0.6)
    jam = flat("Jam", (0.35, 0.02, 0.04), 0.25)
    sugar = flat("Icing", (0.85, 0.82, 0.76), 0.5)
    for i in range(5):
        a = i / 5 * 2 * math.pi
        px, py = cx + math.cos(a) * 0.25, cy + math.sin(a) * 0.25
        if i % 2:
            cyl(f"Tart{i}", 0.1, 0.05, (px, py, ZC + 0.355), crust, verts=12, bevel=0.012)
            cyl(f"TartJam{i}", 0.075, 0.02, (px, py, ZC + 0.38), jam, verts=12, bevel=0.004)
        else:
            sphere(f"Bun{i}", 0.11, (px, py, ZC + 0.39), crust, seg=10, rings=6, scale=(1, 1, 0.65))
            sphere(f"BunIcing{i}", 0.085, (px, py, ZC + 0.43), sugar, seg=10, rings=5, scale=(1, 1, 0.35))
    sphere("BunTop", 0.12, (cx, cy, ZC + 0.4), crust, seg=10, rings=6, scale=(1, 1, 0.7))
    sphere("BunCherry", 0.035, (cx, cy, ZC + 0.49), jam, seg=8, rings=4)
    glassy.append(("Cloche", [(0.0, 0.0), (0.43, 0.0), (0.43, 0.16), (0.4, 0.38), (0.3, 0.55), (0.14, 0.64), (0.0, 0.66)], (cx, cy, ZC + 0.33)))
    sphere("ClocheKnob", 0.05, (cx, cy, ZC + 1.03), M["brass"], seg=8, rings=4)
    # potion-soda bottles in an iron carrier
    px, py = -3.65, -2.75
    box("CarrierBase", (0.72, 0.5, 0.04), (px, py, ZC + 0.02), M["iron"], bevel=0.008)
    for sx in (-1, 1):
        box(f"CarrierEnd{sx}", (0.03, 0.5, 0.36), (px + sx * 0.36, py, ZC + 0.2), M["iron"], bevel=0.005)
    tube("CarrierHandle", [(px - 0.36, py, ZC + 0.38), (px, py, ZC + 0.58), (px + 0.36, py, ZC + 0.38)], 0.02, M["brass"])
    tube("CarrierBand", [(px - 0.36, py - 0.25, ZC + 0.2), (px + 0.36, py - 0.25, ZC + 0.2), (px + 0.36, py + 0.25, ZC + 0.2),
                         (px - 0.36, py + 0.25, ZC + 0.2)], 0.012, M["iron"], closed=True, square=True, poly=True)
    sodas = [flat("SodaGreen", (0.03, 0.3, 0.1), 0.06), flat("SodaPlum", (0.22, 0.02, 0.28), 0.06), flat("SodaRed", (0.4, 0.02, 0.04), 0.06)]
    cork = flat("CorkB", (0.42, 0.3, 0.17), 0.85)
    for i in range(3):
        for j in range(2):
            bxx, byy = px - 0.22 + i * 0.22, py - 0.11 + j * 0.22
            prof = [(0.0, 0.0), (0.085, 0.0), (0.09, 0.24), (0.06, 0.32), (0.035, 0.4), (0.04, 0.46), (0.0, 0.46)]
            lathe(f"Soda{i}{j}", prof, sodas[(i + j) % 3], seg=12, loc=(bxx, byy, ZC + 0.04))
            cyl(f"SodaCork{i}{j}", 0.032, 0.07, (bxx, byy, ZC + 0.53), cork, verts=8, bevel=0)
            box(f"SodaLabel{i}{j}", (0.12, 0.006, 0.09), (bxx, byy - 0.09, ZC + 0.18), M["paper"], bevel=0.0, segments=1)
    # a tray of wrapped toffees and a stack of paper bags
    box("ToffeeTray", (0.7, 0.42, 0.05), (-1.75, -3.0, ZC + 0.025), M["brass"], bevel=0.01)
    wraps = [flat("WrapGold", (0.7, 0.5, 0.1), 0.3, metal=0.6), flat("WrapCrimson", (0.4, 0.03, 0.05), 0.3, metal=0.4)]
    for i in range(10):
        tx = -2.0 + (i % 5) * 0.12 + rnd.uniform(-0.02, 0.02)
        ty = -3.08 + (i // 5) * 0.16
        sphere(f"Toffee{i}", 0.04, (tx, ty, ZC + 0.08), wraps[i % 2], seg=8, rings=4, scale=(1.5, 1, 0.8))
        cone(f"ToffeeTwistL{i}", 0.03, 0.0, 0.05, (tx - 0.07, ty, ZC + 0.08), wraps[i % 2], verts=6, rot=(0, -math.pi / 2, 0))
        cone(f"ToffeeTwistR{i}", 0.03, 0.0, 0.05, (tx + 0.07, ty, ZC + 0.08), wraps[i % 2], verts=6, rot=(0, math.pi / 2, 0))
    for i in range(4):
        box(f"PaperBag{i}", (0.42, 0.3, 0.015), (-3.0 + rnd.uniform(-0.03, 0.03), -1.25, ZC + 0.01 + i * 0.016), M["paper"], bevel=0.0,
            rot=(0, 0, rnd.uniform(-0.12, 0.12)), segments=1)
    # candy sticks in a brass beaker
    lathe("Beaker", [(0.0, 0.0), (0.12, 0.0), (0.12, 0.34), (0.14, 0.36), (0.0, 0.34)], M["brass"], seg=14, loc=(-1.4, -2.2, ZC))
    for i in range(7):
        a = i / 7 * 2 * math.pi
        tx, ty = -1.4 + math.cos(a) * 0.06, -2.2 + math.sin(a) * 0.06
        tube(f"CandyStick{i}", [(tx, ty, ZC + 0.1), (tx + math.cos(a) * 0.08, ty + math.sin(a) * 0.08, ZC + 0.72)], 0.022,
             candy[i % len(candy)], poly=True)
    set_group("Glass")
    for name, prof, loc in glassy:
        lathe(name, prof, M["glassclear"], seg=24, loc=loc)
    set_group("Main")


def concession_stand(M):
    X = _mats(M)
    rnd = _stand_body(M, X)
    _menu_and_shelves(M, X, rnd)
    _canopy(M, X)
    _sign(M, X)
    _awning(M, X)
    _goods(M, X, rnd)
    # two iron lanterns on chains from the eave brackets, in front of the columns
    set_group("Sign")
    wax = wax_mat()
    lanterns = []
    for sx in (-1, 1):
        x, y, z = sx * 4.3, -4.05, 5.75
        _lantern(f"Lantern{sx}", Matrix.Translation((x, y, z)) @ Matrix.Scale(1.5, 4), M, lanterns, wax)
        tube(f"LanternChain{sx}", [(x, y, z + 1.07), (x, y, 7.25)], 0.012, M["iron"], poly=True)
        tube(f"LanternHook{sx}", [(x, y, 7.25), (x, y + 0.25, 7.3), (sx * 4.45, -3.35, 7.15)], 0.025, M["iron"])
        for k in range(5):
            hoop(f"LanternLink{sx}{k}", (x, y, z + 1.12 + k * 0.08), 0.025, "X" if k % 2 else "Y", M["iron"], thick=0.007)
    # a brass oil lamp hung inside over the counter: font, glass chimney (Glass), smoke bell, chain from the ceiling
    lx, ly = 0.0, -1.05
    lathe("LampFont", [(0.0, 6.38), (0.05, 6.38), (0.1, 6.45), (0.17, 6.55), (0.18, 6.66), (0.12, 6.74), (0.07, 6.78), (0.0, 6.8)],
          M["brass"], seg=20, loc=(lx, ly, 0))
    sphere("LampDrop", 0.04, (lx, ly, 6.34), M["brass"], seg=8, rings=4)
    hoop("LampGallery", (lx, ly, 6.82), 0.11, "Z", M["brass"], thick=0.012)
    lathe("LampBell", [(0.0, 7.52), (0.2, 7.36), (0.22, 7.33), (0.06, 7.46), (0.04, 7.6), (0.0, 7.62)], M["brass"], seg=20, loc=(lx, ly, 0))
    for k in range(3):
        a = k / 3 * 2 * math.pi
        tube(f"LampArm{k}", [(lx + math.cos(a) * 0.11, ly + math.sin(a) * 0.11, 6.82), (lx + math.cos(a) * 0.2, ly + math.sin(a) * 0.2, 7.34)],
             0.01, M["brass"], poly=True)
    tube("LampChain", [(lx, ly, 7.62), (lx, ly, ZE)], 0.012, M["iron"], poly=True)
    box("LampCanopy", (0.2, 0.2, 0.05), (lx, ly, ZE - 0.02), M["brass"], bevel=0.01)
    _lights(lanterns, M, flames=[((lx, ly, 6.8), 0.14)])
    set_group("Glass")
    lathe("LampChimney", [(0.0, 6.8), (0.07, 6.8), (0.11, 6.92), (0.1, 7.02), (0.05, 7.12), (0.05, 7.28), (0.0, 7.28)], M["glassclear"],
          seg=20, loc=(lx, ly, 0))
    set_group("Main")
    return _dims()


P.PREVIEW_PAD.update({"ConcessionStand": 1.05})
P.BUILD.update({"ConcessionStand": concession_stand})
