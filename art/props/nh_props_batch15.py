"""Props batch 15 (2026-11-04): the cafeteria's serving and kitchen side, for the school's cafe area. On theme with the
Institution: black marble, oxblood enamel, cast iron, brass and copper, pewter and porcelain, warm gaslight. Wood is
kept off. Original designs.

  ServingCounter  a 10-stud steam-table counter: a black marble top round a sunken steel well of five food pans (mash,
                  peas, a dark stew, sausages and a bubbling "mystery" green), ladles and tongs, an oxblood enamel
                  front of gothic panels with brass beading and the school crest, a brass tray rail, a glass sneeze
                  guard (Glass) on brass posts with three brass heat lamps under its shelf (Glow), and a stack of
                  pewter trays at the right end; steam rises from three of the pans (NHAmbient:Steam spots)
  TrayRack        a tall cast-iron tray trolley on castors: twelve slots of runners, pewter trays in most, a few
                  carrying dirty plates, a push bar and a brass number plate
  DrinksDispenser a counter-top drinks station on a brass drip tray: two glass jugs (Glass) of crimson and amber
                  juice on a black enamel stand with brass taps, a brass tea urn with a tap, handles and a raven
                  finial, and porcelain cups
  BakeryCase      a pastry case: a black lacquer cabinet base with gilt mouldings, a brass-framed glass case (Glass)
                  with a sloped front, three tiers of tarts, iced buns, twists, a pie and a dark cherry cake on a
                  stand, a warm amber backlight baked into its back, and a small brass lamp on top (Glow)
  CoffeeMachine   a brass and black enamel steam coffee machine: a banded upright boiler under a dome with a raven,
                  two pressure gauges, two group heads with levers and spouts over a drip grate with cups, a steam
                  wand, and cups warming on top; steam from the vent at the top (an NHAmbient:Steam spot)
  KitchenShelf    a wall piece: two cast-iron shelves on scrolled brackets with copper pots, jars of preserves and
                  flour sacks, and a hook rail below with hanging copper pans and ladles (the back sits at +Y)
  DishStack       a counter piece: stacks of crimson-rimmed porcelain plates and bowls, an iron cutlery bin of forks,
                  knives and spoons, and a brass cup tree hung with cups

Front faces -Y, Z is up, the origin is at the bottom centre.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _arch_loop
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch7 import lump
from nh_props_batch9 import raven, foil
from nh_props_batch12 import kit, room_mat
from nh_props_batch13 import black_marble, lacquer, pewter, gilt


# ------------------------------------------------------------------ materials

def porcelain():
    return flat("Porcelain", (0.84, 0.82, 0.77), 0.22, dirt=0.35)


def copper():
    return flat("Copper", (0.62, 0.3, 0.17), 0.3, metal=1.0, wear=0.3, dirt=0.85)


def steel():
    return flat("PanSteel", (0.6, 0.6, 0.62), 0.28, metal=1.0, wear=0.2, dirt=0.9)


def food(name, rgb, rough=0.6):
    return flat(name, rgb, rough, dirt=0.4)


def _bounds():
    """lo, hi of everything built so far (Blender space)."""
    bpy.context.view_layer.update()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in P.PARTS:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for k in range(3):
                lo[k], hi[k] = min(lo[k], w[k]), max(hi[k], w[k])
    return lo, hi


def _report_spots(name, spots):
    """Print smoke/steam spots in Roblox model space (from the bottom-centre pivot): X = -(x - cx), Y = z, Z = y - cy."""
    lo, hi = _bounds()
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    pts = ", ".join(f"({-(x - cx):.2f}, {z:.2f}, {y - cy:.2f})" for x, y, z in spots)
    print(f"[props] {name} steam spots (Roblox model-local): {pts}")


def cup(prefix, x, y, z, por, band, s=1.0, handle=True):
    """A porcelain cup on a saucer, with a crimson band."""
    lathe(f"{prefix}Saucer", [(0, z), (0.16 * s, z), (0.19 * s, z + 0.025 * s), (0.17 * s, z + 0.035 * s), (0, z + 0.02 * s)], por, seg=16, loc=(x, y, 0))
    lathe(f"{prefix}Cup", [(0, z + 0.02 * s), (0.07 * s, z + 0.02 * s), (0.1 * s, z + 0.06 * s), (0.115 * s, z + 0.17 * s), (0.105 * s, z + 0.17 * s),
                           (0.09 * s, z + 0.06 * s), (0, z + 0.05 * s)], por, seg=16, loc=(x, y, 0))
    hoop(f"{prefix}Band", (x, y, z + 0.14 * s), 0.113 * s, "Z", band, thick=0.007 * s)
    if handle:
        tube(f"{prefix}Handle", [(x + 0.1 * s, y, z + 0.15 * s), (x + 0.17 * s, y, z + 0.13 * s), (x + 0.16 * s, y, z + 0.07 * s), (x + 0.1 * s, y, z + 0.07 * s)],
             0.012 * s, por)


def plate_stack(prefix, x, y, z, n, r, por, band):
    """n plates as one ridged lathe (cheap), with a crimson rim band on the top plate."""
    prof = [(0, z)]
    t = 0.035
    for i in range(n):
        zb = z + i * t
        prof += [(r * 0.62, zb), (r * 0.98, zb + t * 0.55), (r, zb + t * 0.8), (r * 0.94, zb + t)]
    prof += [(r * 0.6, z + n * t - 0.01), (0, z + n * t - 0.01)]
    lathe(f"{prefix}Plates", prof, por, seg=24, loc=(x, y, 0))
    hoop(f"{prefix}Rim", (x, y, z + n * t - 0.004), r * 0.9, "Z", band, thick=0.008)
    return z + n * t


def tray(prefix, x, y, z, w, d, pw, rot=0.0):
    """A pewter cafeteria tray: a flat base with a raised rim."""
    m = _mark()
    box(f"{prefix}Base", (w, d, 0.03), (0, 0, 0.015), pw, bevel=0.01)
    for sx in (-1, 1):
        box(f"{prefix}RimX{sx}", (0.03, d, 0.07), (sx * (w / 2 - 0.015), 0, 0.035), pw, bevel=0.008)
    for sy in (-1, 1):
        box(f"{prefix}RimY{sy}", (w, 0.03, 0.07), (0, sy * (d / 2 - 0.015), 0.035), pw, bevel=0.008)
    _xform(m, Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z"))


def gauge(prefix, x, y, z, r, br, face, needle, axis="Y"):
    """A pressure gauge: brass bezel, paper face with ticks, a needle; facing -Y."""
    cyl(f"{prefix}Body", r, 0.08, (x, y + 0.02, z), br, rot=(math.pi / 2, 0, 0), verts=20, bevel=0.01)
    cyl(f"{prefix}Face", r * 0.82, 0.01, (x, y - 0.025, z), face, rot=(math.pi / 2, 0, 0), verts=20, bevel=0)
    hoop(f"{prefix}Bezel", (x, y - 0.03, z), r * 0.88, "Y", br, thick=0.014)
    for k in range(7):
        a = math.radians(-120 + k * 40)
        box(f"{prefix}Tick{k}", (0.008, 0.004, r * 0.18), (x + math.sin(a) * r * 0.62, y - 0.032, z + math.cos(a) * r * 0.62), needle,
            bevel=0, segments=1, rot=(0, a, 0))
    box(f"{prefix}Needle", (0.012, 0.004, r * 0.6), (x + math.sin(0.5) * r * 0.25, y - 0.036, z + math.cos(0.5) * r * 0.25), M_CRIM[0],
        bevel=0, segments=1, rot=(0, 0.5, 0))


M_CRIM = [None]   # the crimson for needles, set per build


# ================================================================== serving counter
def serving_counter(M):
    K = kit(M)
    mb, lq, pw, por, st = black_marble(), lacquer(), pewter(), porcelain(), steel()
    en, br, gl = K["enamel"], M["brass"], gilt()
    mash = food("Mash", (0.86, 0.79, 0.58), 0.85)
    peas = food("Peas", (0.24, 0.46, 0.08), 0.45)
    stew = food("Stew", (0.2, 0.075, 0.03), 0.35)
    meat = food("StewMeat", (0.32, 0.13, 0.06), 0.6)
    carrot = food("Carrot", (0.7, 0.28, 0.04), 0.5)
    saus = food("Sausage", (0.42, 0.17, 0.07), 0.45)
    green = food("Mystery", (0.28, 0.42, 0.1), 0.25)
    rnd = random.Random(15)
    W, D, H = 10.0, 2.4, 3.0
    yf = -D / 2
    set_group("Main")
    # body: a lacquer plinth, an oxblood enamel carcass, gothic panels with brass beading, pilasters
    box("Plinth", (W, D - 0.1, 0.3), (0, 0.05, 0.15), lq, bevel=0.03)
    box("Carcass", (W - 0.1, D - 0.2, H - 0.45), (0, 0.05, 0.3 + (H - 0.45) / 2), en, bevel=0.02)
    npan = 5
    pw_ = (W - 0.6) / npan
    for k in range(npan):
        cx = -W / 2 + 0.3 + pw_ * (k + 0.5)
        tube(f"PanelArch{k}", _arch_loop(cx, yf + 0.08, pw_ / 2 - 0.22, 0.55, 1.9, 2.4), 0.022, br, square=True, closed=True, poly=True)
        box(f"PanelField{k}", (pw_ - 0.5, 0.02, 1.3), (cx, yf + 0.1, 0.55 + 0.65), en, bevel=0.01)
        foil(f"PanelFoil{k}", cx, yf + 0.07, 2.12, 0.14, br, lobes=4, thick=0.014)
    for k in range(npan + 1):
        x = -W / 2 + 0.3 + pw_ * k
        box(f"Pilaster{k}", (0.16, 0.08, H - 0.55), (x, yf + 0.06, 0.3 + (H - 0.55) / 2), lq, bevel=0.015)
    # the crest on the middle panel: a brass shield with a crescent
    _m = _mark()
    prism("CrestShield", [(-0.22, 0.3), (0.22, 0.3), (0.22, 0.05), (0, -0.22), (-0.22, 0.05)], yf + 0.04, 0.04, gl, plane="XZ")
    for i in range(10):
        a = math.radians(40 + i * 28)
        box(f"CrestMoon{i}", (0.04, 0.02, 0.03), (math.cos(a) * 0.1, yf + 0.015, 0.06 + math.sin(a) * 0.1), en, bevel=0, segments=1)
    _xform(_m, Matrix.Translation((0, 0, 1.15)))
    # tray rail: three brass rods on brackets along the front, at counter height
    for sx in range(-2, 3):
        x = sx * (W / 2 - 0.4) / 2
        box(f"RailBracket{sx}", (0.06, 0.42, 0.06), (x, yf - 0.18, H - 0.32), br, bevel=0.01)
        box(f"RailDrop{sx}", (0.06, 0.06, 0.2), (x, yf - 0.36, H - 0.4), br, bevel=0.01)
    for k, dy in enumerate((-0.42, -0.3, -0.18)):
        tube(f"TrayRail{k}", [(-W / 2 + 0.2, yf + dy, H - 0.3), (W / 2 - 0.2, yf + dy, H - 0.3)], 0.022, br, poly=True)
    # the black marble top round a sunken well (front lip, back lip, two ends)
    WL, WD = W - 2.0, 1.15                       # well (pans) length and depth; tray stack at the right end
    wx0 = -W / 2 + 0.35
    wcx = wx0 + WL / 2
    wcy = 0.05
    tz = H - 0.1
    box("TopFront", (W, (WD / 2 + wcy) - yf + 0.06 - WD, 0.1), (0, (yf - 0.06 + (wcy - WD / 2)) / 2, tz + 0.05), mb, bevel=0.02)
    box("TopBack", (W, D / 2 - (wcy + WD / 2) + 0.06, 0.1), (0, (wcy + WD / 2 + D / 2 + 0.06) / 2, tz + 0.05), mb, bevel=0.02)
    box("TopLeft", (wx0 + W / 2, WD, 0.1), ((-W / 2 + wx0) / 2, wcy, tz + 0.05), mb, bevel=0.01)
    box("TopRight", (W / 2 - (wx0 + WL), WD, 0.1), ((wx0 + WL + W / 2) / 2, wcy, tz + 0.05), mb, bevel=0.01)
    tube("TopEdge", [(-W / 2, yf - 0.05, tz + 0.1), (W / 2, yf - 0.05, tz + 0.1)], 0.014, br, poly=True)
    box("Well", (WL, WD, 0.5), (wcx, wcy, tz - 0.25), st, bevel=0.01)
    set_group("Food")   # the pans and food are their own piece (Main would pass 16k)
    # five pans with food, 0.1 below the top
    fz = tz + 0.1                         # the food mounds just above the pan rims
    pl = WL / 5
    spots = []
    for k in range(5):
        px = wx0 + pl * (k + 0.5)
        box(f"PanLip{k}", (pl - 0.04, WD - 0.04, 0.03), (px, wcy, tz + 0.085), st, bevel=0.008)
        box(f"PanInner{k}", (pl - 0.16, WD - 0.16, 0.02), (px, wcy, fz - 0.06), st, bevel=0)
        for sx in (-1, 1):
            box(f"PanHandle{k}{sx}", (0.12, 0.04, 0.02), (px + sx * (pl / 2 - 0.1), wcy - WD / 2 + 0.06, tz + 0.105), st, bevel=0.005)
        if k == 0:     # mash: soft heaps
            box("MashBed", (pl - 0.18, WD - 0.18, 0.06), (px, wcy, fz), mash, bevel=0.03)
            for i in range(7):
                sphere(f"Mash{i}", 0.24, (px + rnd.uniform(-0.45, 0.45), wcy + rnd.uniform(-0.3, 0.3), fz + 0.03), mash, seg=10, rings=5,
                       scale=(1.0, 0.9, 0.55))
            spots.append((px, wcy, tz + 0.35))
        elif k == 1:   # peas
            box("PeaBed", (pl - 0.18, WD - 0.18, 0.05), (px, wcy, fz - 0.01), peas, bevel=0.01)
            for i in range(70):
                sphere(f"Pea{i}", 0.035, (px + rnd.uniform(-0.62, 0.62), wcy + rnd.uniform(-0.42, 0.42), fz + 0.03), peas, seg=6, rings=3)
        elif k == 2:   # stew with meat and carrots
            box("StewBed", (pl - 0.18, WD - 0.18, 0.05), (px, wcy, fz - 0.01), stew, bevel=0.01)
            for i in range(9):
                lump(f"Meat{i}", (px + rnd.uniform(-0.55, 0.55), wcy + rnd.uniform(-0.35, 0.35), fz + 0.03), 0.07, meat, rnd, squash=0.6)
            for i in range(6):
                cyl(f"Carrot{i}", 0.04, 0.03, (px + rnd.uniform(-0.55, 0.55), wcy + rnd.uniform(-0.35, 0.35), fz + 0.035), carrot, verts=8, bevel=0)
            spots.append((px, wcy, tz + 0.35))
        elif k == 3:   # sausages
            box("GravyBed", (pl - 0.18, WD - 0.18, 0.04), (px, wcy, fz - 0.02), stew, bevel=0.01)
            for i in range(6):
                y = wcy - 0.38 + i * 0.15
                a = rnd.uniform(-0.15, 0.15)
                cyl(f"Sausage{i}", 0.055, 1.1, (px, y, fz + 0.04), saus, rot=(0, math.pi / 2, a), verts=10, bevel=0.03)
        else:          # the mystery green, bubbling
            box("GreenBed", (pl - 0.18, WD - 0.18, 0.06), (px, wcy, fz), green, bevel=0.02)
            for i in range(10):
                sphere(f"Bubble{i}", rnd.uniform(0.03, 0.07), (px + rnd.uniform(-0.55, 0.55), wcy + rnd.uniform(-0.38, 0.38), fz + 0.03), green, seg=8,
                       rings=4, scale=(1, 1, 0.6))
            spots.append((px, wcy, tz + 0.35))
    # ladles and tongs resting in the pans
    for k, px in enumerate((wx0 + pl * 0.5, wx0 + pl * 2.5, wx0 + pl * 4.5)):
        sphere(f"LadleBowl{k}", 0.1, (px + 0.25, wcy - 0.1, fz + 0.06), st, seg=10, rings=5, scale=(1, 1, 0.55))
        tube(f"LadleHandle{k}", [(px + 0.25, wcy - 0.1, fz + 0.08), (px + 0.3, wcy + 0.15, fz + 0.3), (px + 0.32, wcy + 0.48, fz + 0.42)], 0.016, st)
    px = wx0 + pl * 3.5
    for sx in (-1, 1):
        tube(f"Tongs{sx}", [(px - 0.25 + sx * 0.03, wcy + 0.35, tz + 0.14), (px + 0.1 + sx * 0.05, wcy - 0.05, fz + 0.1)], 0.012, st, poly=True)
    set_group("Main")
    # the sneeze guard: brass posts, a glass pane sloping out over the front, a brass top shelf with heat lamps
    gz0, gz1 = tz + 0.1, tz + 1.35
    posts = [wx0 + 0.05, wx0 + WL / 2, wx0 + WL - 0.05]
    for k, x in enumerate(posts):
        tube(f"GuardPost{k}", [(x, wcy + WD / 2 - 0.1, gz0), (x, wcy + WD / 2 - 0.1, gz1)], 0.03, br, poly=True)
        sphere(f"GuardKnob{k}", 0.05, (x, wcy + WD / 2 - 0.1, gz1 + 0.03), br, seg=8, rings=4)
        tube(f"GuardArm{k}", [(x, wcy + WD / 2 - 0.1, gz1 - 0.08), (x, yf + 0.1, gz1 - 0.35)], 0.02, br, poly=True)
    box("GuardShelf", (WL + 0.1, 0.55, 0.05), (wcx, wcy + WD / 2 - 0.35, gz1), br, bevel=0.01)
    tube("GuardShelfEdge", [(wx0 - 0.05, wcy + WD / 2 - 0.62, gz1 + 0.02), (wx0 + WL + 0.05, wcy + WD / 2 - 0.62, gz1 + 0.02)], 0.015, gl, poly=True)
    hx = [wx0 + pl * 0.5, wx0 + pl * 2.5, wx0 + pl * 4.5]
    for k, x in enumerate(hx):
        lathe(f"HeatLampShade{k}", [(0, gz1 - 0.02), (0.05, gz1 - 0.02), (0.14, gz1 - 0.16), (0.16, gz1 - 0.2), (0.15, gz1 - 0.2), (0.12, gz1 - 0.15),
                                    (0, gz1 - 0.06)], br, seg=16, loc=(x, wcy + WD / 2 - 0.35, 0))
    # tray stack at the right end of the top
    sx0 = wx0 + WL + (W / 2 - (wx0 + WL)) / 2
    for i in range(9):
        tray(f"Tray{i}", sx0 + rnd.uniform(-0.02, 0.02), wcy - 0.05, tz + 0.1 + i * 0.075, 1.3, 0.95, pw, rot=rnd.uniform(-0.04, 0.04))
    set_group("Glass")
    gt, gb = (yf + 0.1, gz1 - 0.35), (yf + 0.28, tz + 0.5)          # the pane: from the arm tips down toward the server
    gdy, gdz = gt[0] - gb[0], gt[1] - gb[1]
    box("GuardGlass", (WL + 0.05, 0.03, math.hypot(gdy, gdz)), (wcx, (gt[0] + gb[0]) / 2, (gt[1] + gb[1]) / 2), M["glassclear"], bevel=0,
        rot=(math.atan2(-gdy, gdz), 0, 0))
    set_group("Glow")
    for k, x in enumerate(hx):
        sphere(f"HeatBulb{k}", 0.08, (x, wcy + WD / 2 - 0.35, gz1 - 0.15), K["glow"], seg=10, rings=5)
    set_group("Main")
    _report_spots("ServingCounter", spots)
    return _dims()


# ================================================================== tray rack
def tray_rack(M):
    pw, por = pewter(), porcelain()
    ir, br = M["iron"], M["brass"]
    smear = food("Smear", (0.4, 0.2, 0.08), 0.5)
    pea = food("PeaDry", (0.26, 0.42, 0.1), 0.5)
    rnd = random.Random(7)
    W, D, H = 2.2, 1.7, 5.6
    set_group("Main")
    # frame: four corner posts on castors, top and bottom rings, a push bar
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * W / 2, sy * D / 2
            box(f"Post{sx}{sy}", (0.08, 0.08, H - 0.55), (x, y, 0.45 + (H - 0.55) / 2), ir, bevel=0.012)
            cyl(f"Castor{sx}{sy}", 0.17, 0.08, (x, y, 0.17), M["felt"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.02)
            box(f"Fork{sx}{sy}", (0.14, 0.06, 0.26), (x, y, 0.32), ir, bevel=0.01)
            sphere(f"Finial{sx}{sy}", 0.06, (x, y, H - 0.06), br, seg=8, rings=4)
    for z in (0.45, H - 0.15):
        for sy in (-1, 1):
            box(f"RailX{z:.1f}{sy}", (W, 0.06, 0.08), (0, sy * D / 2, z), ir, bevel=0.01)
        for sx in (-1, 1):
            box(f"RailY{z:.1f}{sx}", (0.06, D, 0.08), (sx * W / 2, 0, z), ir, bevel=0.01)
    box("BackPanel", (W, 0.03, H - 0.7), (0, D / 2 - 0.02, 0.5 + (H - 0.7) / 2), ir, bevel=0.0)
    for sx in (-1, 1):
        box(f"SidePanel{sx}", (0.03, D, 0.08), (sx * W / 2, 0, H / 2), ir, bevel=0.0)
        tube(f"PushBar{sx}", [(sx * W / 2, D / 2, H - 0.5), (sx * W / 2, D / 2 + 0.3, H - 0.4)], 0.03, ir, poly=True)
    tube("PushBar", [(-W / 2, D / 2 + 0.3, H - 0.4), (W / 2, D / 2 + 0.3, H - 0.4)], 0.035, br, poly=True)
    box("NumberPlate", (0.5, 0.03, 0.25), (0, -D / 2 - 0.03, H - 0.4), br, bevel=0.01)
    box("NumberPlateInk", (0.32, 0.01, 0.12), (0, -D / 2 - 0.05, H - 0.4), M["glass"], bevel=0)
    # twelve slots of runners; trays in most of them
    slots = 12
    z0, z1 = 0.65, H - 0.45
    dz = (z1 - z0) / slots
    for k in range(slots):
        z = z0 + k * dz
        for sx in (-1, 1):
            box(f"Runner{k}{sx}", (0.1, D - 0.1, 0.03), (sx * (W / 2 - 0.05), 0, z), ir, bevel=0.0, segments=1)
        if k in (3, 8):
            continue
        out = rnd.uniform(-0.25, 0.05) if k % 4 == 1 else 0.0
        tray(f"Tray{k}", 0, out, z + 0.016, W - 0.18, D - 0.12, pw)
        if k in (1, 5, 10):    # a dirty plate left on it
            pz = z + 0.05
            x, y = rnd.uniform(-0.4, 0.4), out + rnd.uniform(-0.2, 0.2)
            lathe(f"DirtyPlate{k}", [(0, pz), (0.25, pz), (0.34, pz + 0.035), (0.33, pz + 0.04), (0.24, pz + 0.012), (0, pz + 0.012)], por, seg=20,
                  loc=(x, y, 0))
            sphere(f"Smear{k}", 0.13, (x + 0.05, y, pz + 0.02), smear, seg=10, rings=4, scale=(1.2, 0.8, 0.12))
            for i in range(4):
                sphere(f"Pea{k}{i}", 0.03, (x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15), pz + 0.035), pea, seg=6, rings=3)
    return _dims()


# ================================================================== drinks dispenser
def drinks_dispenser(M):
    K = kit(M)
    br, por, en = M["brass"], porcelain(), K["enamel"]
    juices = (food("CrimsonJuice", (0.6, 0.03, 0.07), 0.1), food("AmberJuice", (0.9, 0.5, 0.08), 0.1))
    set_group("Main")
    # the drip tray: a brass tray with a pierced grate
    box("DripTray", (2.7, 1.1, 0.08), (0, 0, 0.04), br, bevel=0.02)
    for i in range(13):
        box(f"Grate{i}", (0.03, 0.9, 0.02), (-1.2 + i * 0.2, -0.02, 0.09), M["iron"], bevel=0, segments=1)
    # the jug stand: black enamel plinth on brass feet, two jugs, taps
    box("Stand", (1.5, 0.8, 0.7), (-0.55, 0.12, 0.1 + 0.35), en, bevel=0.03)
    tube("StandBand", [(-1.3, -0.29, 0.75), (0.2, -0.29, 0.75)], 0.018, br, poly=True)
    for k, x in enumerate((-0.92, -0.18)):
        lathe(f"Juice{k}", [(0, 0.82), (0.25, 0.82), (0.26, 1.55), (0, 1.55)], juices[k], seg=20, loc=(x, 0.12, 0))
        lathe(f"JugBase{k}", [(0, 0.8), (0.32, 0.8), (0.33, 0.86), (0.29, 0.9), (0, 0.9)], br, seg=20, loc=(x, 0.12, 0))
        lathe(f"JugCap{k}", [(0, 1.75), (0.29, 1.75), (0.31, 1.8), (0.22, 1.86), (0.08, 1.9), (0.06, 1.98), (0, 2.0)], br, seg=20, loc=(x, 0.12, 0))
        cyl(f"TapBody{k}", 0.045, 0.22, (x, -0.22, 0.6), br, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
        cyl(f"TapSpout{k}", 0.03, 0.12, (x, -0.31, 0.53), br, verts=8, bevel=0.005)
        box(f"TapLever{k}", (0.04, 0.04, 0.2), (x, -0.27, 0.72), M["glass"], bevel=0.01)
        cup(f"JuiceCup{k}", x, -0.33, 0.1, por, M["crimson"], s=0.9, handle=False)
    # the tea urn: brass, a lacquer band, handles, a tap, a raven finial
    ux = 0.85
    lathe("Urn", [(0, 0.1), (0.25, 0.1), (0.3, 0.18), (0.22, 0.28), (0.24, 0.36), (0.42, 0.55), (0.46, 0.9), (0.44, 1.2), (0.34, 1.38), (0.36, 1.42),
                  (0.2, 1.46), (0, 1.46)], br, seg=28, loc=(ux, 0.1, 0))
    lathe("UrnBand", [(0, 0.82), (0.47, 0.82), (0.47, 0.98), (0, 0.98)], M["glass"], seg=28, loc=(ux, 0.1, 0))
    lathe("UrnLid", [(0, 1.44), (0.22, 1.44), (0.18, 1.56), (0.08, 1.62), (0, 1.63)], br, seg=20, loc=(ux, 0.1, 0))
    raven("UrnRaven", (ux, 0.1, 1.62), -math.pi / 2, 0.9, M["glass"], M["iron"])
    for sx in (-1, 1):
        tube(f"UrnHandle{sx}", [(ux + sx * 0.42, 0.1, 1.15), (ux + sx * 0.6, 0.1, 1.1), (ux + sx * 0.6, 0.1, 0.75), (ux + sx * 0.44, 0.1, 0.7)], 0.025, br)
    cyl("UrnTap", 0.05, 0.3, (ux, -0.3, 0.55), br, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
    cyl("UrnSpout", 0.035, 0.14, (ux, -0.44, 0.46), br, verts=8, bevel=0.005)
    sphere("UrnTapKnob", 0.06, (ux, -0.36, 0.64), M["glass"], seg=8, rings=4)
    cup("TeaCup", ux, -0.42, 0.1, por, M["crimson"])
    cup("SpareCup", 0.4, -0.42, 0.1, por, M["crimson"])
    set_group("Glass")
    for k, x in enumerate((-0.92, -0.18)):
        lathe(f"Jug{k}", [(0, 0.86), (0.28, 0.86), (0.29, 1.7), (0.27, 1.78), (0.25, 1.78), (0.27, 1.7), (0.27, 0.88), (0, 0.88)], M["glassclear"], seg=20,
              loc=(x, 0.12, 0))
    set_group("Main")
    return _dims()


# ================================================================== bakery case
def bakery_case(M):
    lq, gl, br, por = lacquer(), gilt(), M["brass"], porcelain()
    K = kit(M)
    pastry = food("Pastry", (0.86, 0.52, 0.18), 0.5)
    crust = food("Crust", (0.74, 0.42, 0.14), 0.55)
    jam = food("Jam", (0.62, 0.03, 0.07), 0.2)
    icing = food("Icing", (0.95, 0.92, 0.86), 0.35)
    pink = food("PinkIcing", (0.88, 0.4, 0.46), 0.35)
    cake = food("DarkCake", (0.08, 0.035, 0.03), 0.45)
    cherry = food("Cherry", (0.5, 0.01, 0.03), 0.15)
    W, D = 4.2, 1.9
    bz = 2.6                                  # cabinet top (the case floor)
    yf = -D / 2
    set_group("Main")
    # the black lacquer cabinet base: a gilt-banded plinth, two doors with crimson inset panels in gilt pointed-arch mouldings,
    # gilt corner beads and a gilt cornice bead (deep gloss black lacquer, so it never reads as steel)
    blk = P.material("CaseLacquer", base=(0.012, 0.011, 0.014), rough=0.32, wear=0.08, dirt=0.5)
    crim = flat("CaseCrimson", (0.2, 0.02, 0.032), 0.75, dirt=0.4)
    box("Plinth", (W + 0.1, D + 0.08, 0.2), (0, 0, 0.1), blk, bevel=0.03)
    tube("PlinthBand", [(-W / 2 - 0.05, yf - 0.05, 0.18), (W / 2 + 0.05, yf - 0.05, 0.18)], 0.018, gl, poly=True)
    box("Cabinet", (W, D, bz - 0.2), (0, 0, 0.2 + (bz - 0.2) / 2), blk, bevel=0.025)
    for sx in (-1, 1):
        tube(f"CornerBead{sx}", [(sx * (W / 2 + 0.005), yf - 0.005, 0.22), (sx * (W / 2 + 0.005), yf - 0.005, bz - 0.04)], 0.02, gl, poly=True)
    tube("DoorSplit", [(0, yf - 0.012, 0.3), (0, yf - 0.012, bz - 0.12)], 0.014, gl, poly=True)
    for k, x in enumerate((-W / 4, W / 4)):
        hw = W / 4 - 0.25
        box(f"Door{k}", (W / 2 - 0.12, 0.04, bz - 0.5), (x, yf - 0.02, 0.25 + (bz - 0.5) / 2), blk, bevel=0.02)
        # the crimson inset: a rectangle up to the springing and a convex pointed top (one concave n-gon shades badly)
        box(f"DoorPanel{k}", (2 * (hw - 0.06), 0.012, 1.65 - 0.5), (x, yf - 0.045, 0.5 + (1.65 - 0.5) / 2), crim, bevel=0)
        top = [(p[0], p[2]) for p in _arch_loop(x, yf - 0.05, hw - 0.06, 0.5, 1.65, 2.12) if p[2] >= 1.65 - 1e-6]
        top = sorted(set(top), key=lambda q: q[0])
        prism(f"DoorPanelTop{k}", top, yf - 0.045, 0.012, crim, plane="XZ")
        tube(f"PanelArch{k}", _arch_loop(x, yf - 0.055, hw, 0.45, 1.7, 2.2), 0.024, gl, square=True, closed=True, poly=True)
        tube(f"PanelArchIn{k}", _arch_loop(x, yf - 0.055, hw - 0.1, 0.55, 1.62, 2.04), 0.012, gl, square=True, closed=True, poly=True)
        foil(f"PanelFoil{k}", x, yf - 0.065, 1.25, 0.17, gl, lobes=4, thick=0.016)
        kx = -0.12 if k == 0 else 0.12                 # gilt knobs either side of the centre split
        cyl(f"DoorKnobRose{k}", 0.06, 0.015, (kx, yf - 0.045, 1.2), gl, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.004)
        sphere(f"DoorKnob{k}", 0.045, (kx, yf - 0.085, 1.2), gl, seg=10, rings=5)
    box("Cornice", (W + 0.08, D + 0.06, 0.1), (0, 0, bz - 0.05), blk, bevel=0.02)
    tube("CabinetBead", [(-W / 2 - 0.04, yf - 0.04, bz - 0.06), (W / 2 + 0.04, yf - 0.04, bz - 0.06)], 0.02, gl, poly=True)
    box("CaseFloor", (W - 0.1, D - 0.1, 0.06), (0, 0, bz + 0.03), por, bevel=0.01)
    # the case: brass frame (a sloped front, upright back), shelves, a backlit back panel
    ch = 1.7                                   # case height
    zt = bz + ch
    yb = D / 2 - 0.08                          # back
    yt = -D / 2 + 0.55                         # front edge at the top (the front slopes back)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.04)
        tube(f"FrameFront{sx}", [(x, yf + 0.04, bz + 0.06), (x, yt, zt)], 0.035, br, poly=True, square=True)
        tube(f"FrameBack{sx}", [(x, yb, bz + 0.06), (x, yb, zt)], 0.035, br, poly=True, square=True)
        tube(f"FrameTop{sx}", [(x, yt, zt), (x, yb, zt)], 0.035, br, poly=True, square=True)
    for k, (y, z) in enumerate(((yf + 0.04, bz + 0.08), (yt, zt), (yb, zt))):
        tube(f"FrameX{k}", [(-W / 2 + 0.04, y, z), (W / 2 - 0.04, y, z)], 0.035, br, poly=True, square=True)
    box("CaseTop", (W - 0.06, yb - yt + 0.1, 0.06), (0, (yb + yt) / 2, zt + 0.03), lq, bevel=0.015)
    # gilt cresting along the case top: a beaded rail, fleur finials on trefoil roundels, pinnacles at the corners
    cy_ = (yb + yt) / 2
    tube("CaseCresting", [(-W / 2 + 0.1, cy_, zt + 0.08), (W / 2 - 0.1, cy_, zt + 0.08)], 0.022, gl, poly=True)
    tube("CaseCrestingTop", [(-W / 2 + 0.1, cy_, zt + 0.2), (W / 2 - 0.1, cy_, zt + 0.2)], 0.012, gl, poly=True)
    n = 9
    for i in range(n):
        x = -W / 2 + 0.3 + i * (W - 0.6) / (n - 1)
        foil(f"CrestFoil{i}", x, cy_, zt + 0.15, 0.06, gl, lobes=3, thick=0.012)
        cone(f"Crest{i}", 0.04, 0.0, 0.16, (x, cy_, zt + 0.3), gl, verts=6)
        sphere(f"CrestBud{i}", 0.025, (x, cy_, zt + 0.24), gl, seg=6, rings=3)
    for sx in (-1, 1):
        cone(f"CornerPinnacle{sx}", 0.06, 0.0, 0.32, (sx * (W / 2 - 0.08), cy_, zt + 0.26), gl, verts=8)
    back = room_mat("BakeryBacklight", (0, yb, bz + 1.0), 3.4, (1.0, 0.66, 0.3), (0.2, 0.09, 0.04))
    box("Backlight", (W - 0.12, 0.02, ch - 0.06), (0, yb - 0.02, bz + ch / 2), back, bevel=0)
    # shelves: three tiers stepping up toward the back
    tiers = ((bz + 0.06, -0.45, 0.0), (bz + 0.62, 0.05, 0.6), (bz + 1.12, 0.45, 0.55))
    for k, (z, y, _) in enumerate(tiers[1:]):
        box(f"Shelf{k}", (W - 0.14, 0.5, 0.04), (0, y, z), M["glassclear"], bevel=0.005)
        tube(f"ShelfEdge{k}", [(-W / 2 + 0.07, y - 0.25, z + 0.02), (W / 2 - 0.07, y - 0.25, z + 0.02)], 0.012, br, poly=True)
        for sx in (-1, 1):
            box(f"ShelfBracket{k}{sx}", (0.04, 0.5, 0.04), (sx * (W / 2 - 0.1), y, z - 0.04), br, bevel=0.005)
    # tier 0 (floor, front): jam tarts on doilies
    z = tiers[0][0]
    for i in range(5):
        x = -1.6 + i * 0.6
        cyl(f"Doily{i}", 0.26, 0.006, (x, -0.42, z + 0.005), icing, verts=12, bevel=0)
        lathe(f"Tart{i}", [(0, z), (0.2, z), (0.22, z + 0.04), (0.21, z + 0.08), (0.17, z + 0.07), (0, z + 0.06)], crust, seg=16, loc=(x, -0.42, 0))
        cyl(f"TartJam{i}", 0.16, 0.02, (x, -0.42, z + 0.065), jam if i % 2 == 0 else food("Custard", (0.85, 0.65, 0.2), 0.3), verts=14, bevel=0)
    # the cake on a porcelain stand at the right of the floor
    cx, cy = 1.45, -0.3
    lathe("CakeStand", [(0, z), (0.12, z), (0.06, z + 0.06), (0.05, z + 0.2), (0.34, z + 0.22), (0.36, z + 0.25), (0, z + 0.25)], por, seg=20,
          loc=(cx, cy, 0))
    lathe("Cake", [(0, z + 0.25), (0.3, z + 0.25), (0.3, z + 0.45), (0, z + 0.45)], cake, seg=24, loc=(cx, cy, 0))
    for i in range(10):
        a = i / 10 * 2 * math.pi
        sphere(f"CakeDrip{i}", 0.05, (cx + math.cos(a) * 0.29, cy + math.sin(a) * 0.29, z + 0.41), icing, seg=6, rings=3, scale=(0.7, 0.7, 1.6))
    cyl("CakeTop", 0.3, 0.02, (cx, cy, z + 0.46), icing, verts=24, bevel=0.005)
    for i in range(5):
        a = i / 5 * 2 * math.pi
        sphere(f"Cherry{i}", 0.045, (cx + math.cos(a) * 0.18, cy + math.sin(a) * 0.18, z + 0.5), cherry, seg=8, rings=4)
    # tier 1: iced buns
    z = tiers[1][0]
    for i in range(7):
        x = -1.75 + i * 0.58
        sphere(f"Bun{i}", 0.2, (x, 0.05, z + 0.14), pastry, seg=12, rings=6, scale=(1, 1, 0.6))
        sphere(f"BunIcing{i}", 0.17, (x, 0.05, z + 0.19), pink if i % 2 else icing, seg=12, rings=6, scale=(1, 1, 0.35))
        sphere(f"BunCherry{i}", 0.04, (x, 0.05, z + 0.27), cherry, seg=6, rings=3)
    # tier 2: pastry twists and a pie
    z = tiers[2][0]
    for i in range(4):
        x = -1.7 + i * 0.5
        pts = [(x - 0.2 + t * 0.4 / 12, 0.45 + math.sin(t * 1.2) * 0.04, z + 0.09 + math.cos(t * 1.2) * 0.03) for t in range(13)]
        tube(f"Twist{i}", pts, 0.05, pastry)
    lathe("Pie", [(0, z + 0.02), (0.42, z + 0.02), (0.44, z + 0.1), (0.4, z + 0.16), (0, z + 0.17)], crust, seg=24, loc=(1.0, 0.45, 0))
    for i in range(4):
        a = i / 4 * math.pi
        box(f"PieLattice{i}", (0.76, 0.05, 0.02), (1.0, 0.45, z + 0.17), pastry, bevel=0.01, rot=(0, 0, a))
    # the small brass lamp on the case top
    lx = -W / 2 + 0.4
    lathe("LampBase", [(0, zt + 0.06), (0.12, zt + 0.06), (0.1, zt + 0.1), (0.03, zt + 0.12), (0.03, zt + 0.45), (0, zt + 0.45)], br, seg=12,
          loc=(lx, (yb + yt) / 2, 0))
    lathe("LampShade", [(0, zt + 0.62), (0.06, zt + 0.62), (0.16, zt + 0.45), (0.15, zt + 0.44), (0.05, zt + 0.58), (0, zt + 0.58)], br, seg=16,
          loc=(lx, (yb + yt) / 2, 0))
    set_group("Glass")
    sl = math.hypot(yt - (yf + 0.04), zt - bz - 0.06)
    ang = math.atan2(yt - (yf + 0.04), zt - bz - 0.06)
    box("FrontGlass", (W - 0.1, 0.025, sl), (0, (yf + 0.04 + yt) / 2, bz + 0.06 + (zt - bz - 0.06) / 2), M["glassclear"], bevel=0, rot=(-ang, 0, 0))
    for sx in (-1, 1):
        prism(f"SideGlass{sx}", [(yf + 0.04, bz + 0.06), (yb, bz + 0.06), (yb, zt), (yt, zt)], sx * (W / 2 - 0.04), 0.025, M["glassclear"], plane="YZ")
    set_group("Glow")
    sphere("LampBulb", 0.07, (lx, (yb + yt) / 2, zt + 0.5), K["glow"], seg=10, rings=5)
    set_group("Main")
    return _dims()


# ================================================================== coffee machine
def coffee_machine(M):
    K = kit(M)
    br, en, por, gl = M["brass"], K["enamel"], porcelain(), gilt()
    blk = M["glass"]
    face = M["paper"]
    M_CRIM[0] = M["crimson"]
    W, D = 2.2, 1.3
    set_group("Main")
    # base: a black enamel plinth with brass edges and a drip grate
    box("Base", (W, D, 0.9), (0, 0, 0.45), en, bevel=0.04)
    tube("BaseEdge", [(-W / 2, -D / 2 - 0.01, 0.88), (W / 2, -D / 2 - 0.01, 0.88)], 0.02, br, poly=True)
    tube("BaseFoot", [(-W / 2, -D / 2 - 0.01, 0.06), (W / 2, -D / 2 - 0.01, 0.06)], 0.025, br, poly=True)
    foil("BaseFoil", 0, -D / 2 - 0.01, 0.45, 0.2, gl, lobes=4, thick=0.016)
    box("DripTray", (W - 0.2, 0.55, 0.06), (0, -D / 2 + 0.2, 0.93), br, bevel=0.01)
    for i in range(10):
        box(f"Grate{i}", (0.025, 0.45, 0.02), (-0.85 + i * 0.19, -D / 2 + 0.2, 0.97), M["iron"], bevel=0, segments=1)
    # the upright boiler: brass with black bands, dome and a raven
    bx, by = 0.0, 0.18
    lathe("Boiler", [(0, 0.9), (0.55, 0.9), (0.58, 0.98), (0.55, 1.05), (0.55, 2.45), (0.58, 2.5), (0.55, 2.56), (0.48, 2.75), (0.3, 2.9), (0.12, 2.96),
                     (0, 2.97)], br, seg=32, loc=(bx, by, 0))
    for k, z in enumerate((1.3, 2.1)):
        lathe(f"BoilerBand{k}", [(0, z), (0.565, z), (0.565, z + 0.12), (0, z + 0.12)], blk, seg=32, loc=(bx, by, 0))
    for i in range(14):
        a = i / 14 * 2 * math.pi
        sphere(f"Rivet{i}", 0.02, (bx + math.cos(a) * 0.565, by + math.sin(a) * 0.565, 1.36), br, seg=6, rings=3)
    lathe("Finial", [(0, 2.96), (0.1, 2.96), (0.06, 3.02), (0.08, 3.06), (0, 3.08)], gl, seg=12, loc=(bx, by, 0))
    raven("TopRaven", (bx, by, 3.08), -math.pi / 2, 1.3, blk, M["iron"])
    # steam vent and whistle on the dome
    tube("VentPipe", [(bx + 0.3, by + 0.1, 2.85), (bx + 0.42, by + 0.1, 3.15)], 0.035, br, poly=True)
    cone("VentCap", 0.06, 0.03, 0.08, (bx + 0.43, by + 0.1, 3.18), br, verts=10)
    # gauges either side of the front
    for k, sx in enumerate((-1, 1)):
        gauge(f"Gauge{k}", bx + sx * 0.3, by - math.sqrt(0.55 ** 2 - 0.3 ** 2) - 0.03, 1.75, 0.15, br, face, blk)
    # two group heads with levers and spouts, cups under them
    for k, sx in enumerate((-1, 1)):
        x = sx * 0.55
        tube(f"GroupArm{k}", [(x * 0.5, by - 0.45, 1.6), (x, -D / 2 + 0.2, 1.55)], 0.06, br, poly=True)
        lathe(f"GroupHead{k}", [(0, 1.62), (0.16, 1.62), (0.18, 1.55), (0.14, 1.42), (0.08, 1.38), (0, 1.38)], br, seg=16, loc=(x, -D / 2 + 0.2, 0))
        tube(f"Lever{k}", [(x, -D / 2 + 0.2, 1.62), (x, -D / 2 + 0.05, 1.95), (x, -D / 2 + 0.0, 2.2)], 0.025, br, poly=True)
        sphere(f"LeverKnob{k}", 0.065, (x, -D / 2 + 0.0, 2.24), blk, seg=10, rings=5)
        cyl(f"Spout{k}", 0.025, 0.14, (x, -D / 2 + 0.2, 1.31), br, verts=8, bevel=0.005)
        cup(f"Cup{k}", x, -D / 2 + 0.2, 0.96, por, M["crimson"], s=0.9)
    # the steam wand at the right
    tube("Wand", [(0.55, by - 0.4, 2.0), (0.85, by - 0.45, 1.9), (0.92, by - 0.5, 1.3)], 0.025, br)
    sphere("WandValve", 0.07, (0.55, by - 0.42, 2.0), blk, seg=10, rings=5)
    # cups warming on top of the base behind the boiler
    for k, x in enumerate((-0.8, 0.8)):
        cup(f"WarmCup{k}", x, 0.45, 0.9, por, M["crimson"], s=0.85, handle=False)
        cup(f"WarmCupStack{k}", x, 0.45, 1.05, por, M["crimson"], s=0.85, handle=False)
    _report_spots("CoffeeMachine", [(bx + 0.43, by + 0.1, 3.25)])
    return _dims()


# ================================================================== kitchen shelf
def kitchen_shelf(M):
    ir, br = M["iron"], M["brass"]
    cu = copper()
    burlap = P.material("Sack", "NH_Leather", tint=(0.5, 0.4, 0.27), scale=3.0, normal=0.9, wear=0.15, dirt=0.8)
    flour = food("Flour", (0.88, 0.86, 0.8), 0.95)
    jars = (food("JarPlum", (0.25, 0.03, 0.08), 0.15), food("JarApricot", (0.6, 0.3, 0.05), 0.15), food("JarPickle", (0.22, 0.3, 0.06), 0.15))
    lid = flat("JarCloth", (0.42, 0.05, 0.06), 0.85)
    rnd = random.Random(11)
    W, D = 5.0, 1.0
    set_group("Main")
    # wall straps, two shelves on scrolled brackets
    for sx in (-1, 1):
        box(f"Strap{sx}", (0.1, 0.05, 4.6), (sx * (W / 2 - 0.4), -0.025, 2.4), ir, bevel=0.01)
    for k, z in enumerate((2.6, 4.1)):
        box(f"Shelf{k}", (W, D, 0.07), (0, -D / 2, z), ir, bevel=0.015)
        tube(f"ShelfLip{k}", [(-W / 2, -D + 0.02, z + 0.08), (W / 2, -D + 0.02, z + 0.08)], 0.02, br, poly=True)
        for sx in (-1, 1):
            x = sx * (W / 2 - 0.4)
            tube(f"Bracket{k}{sx}", [(x, -0.05, z - 0.65), (x, -0.25, z - 0.5), (x, -0.55, z - 0.25), (x, -0.85, z - 0.04)], 0.03, ir, square=True)
            tube(f"BracketCurl{k}{sx}", circle_pts(x, -0.35, z - 0.2, 0.12, "X", 12), 0.018, ir, closed=True, poly=True)
    # top shelf: jars of preserves with cloth caps, a copper pot
    z = 4.14
    for i in range(7):
        x = -2.1 + i * 0.42
        j = jars[i % 3]
        lathe(f"Jar{i}", [(0, z), (0.14, z), (0.15, z + 0.04), (0.15, z + 0.38), (0.11, z + 0.44), (0.12, z + 0.47), (0, z + 0.47)], j, seg=16,
              loc=(x, -0.45, 0))
        lathe(f"JarCap{i}", [(0, z + 0.46), (0.15, z + 0.43), (0.16, z + 0.48), (0.1, z + 0.51), (0, z + 0.52)], lid, seg=16, loc=(x, -0.45, 0))
    lathe("Pot", [(0, z), (0.32, z), (0.36, z + 0.06), (0.36, z + 0.42), (0.38, z + 0.45), (0.34, z + 0.45), (0.32, z + 0.06), (0, z + 0.04)], cu, seg=24,
          loc=(1.65, -0.45, 0))
    lathe("PotLid", [(0, z + 0.44), (0.36, z + 0.44), (0.3, z + 0.52), (0.06, z + 0.56), (0.05, z + 0.62), (0, z + 0.63)], cu, seg=24, loc=(1.65, -0.45, 0))
    for sx in (-1, 1):
        tube(f"PotHandle{sx}", [(1.65 + sx * 0.36, -0.45, z + 0.34), (1.65 + sx * 0.48, -0.45, z + 0.36), (1.65 + sx * 0.48, -0.45, z + 0.28),
                                (1.65 + sx * 0.36, -0.45, z + 0.26)], 0.018, br)
    # lower shelf: flour sacks, a stockpot, a stack of copper pans
    z = 2.64
    for k, x in enumerate((-1.7, -1.1)):
        sphere(f"Sack{k}", 0.34, (x, -0.48, z + 0.36), burlap, seg=12, rings=8, scale=(1.0, 0.85, 1.15))
        sphere(f"SackNeck{k}", 0.12, (x, -0.48, z + 0.78), burlap, seg=8, rings=4, scale=(1, 1, 1.4))
        hoop(f"SackTie{k}", (x, -0.48, z + 0.72), 0.12, "Z", M["iron"], thick=0.015)
        sphere(f"Spill{k}", 0.15, (x + 0.2, -0.72, z + 0.02), flour, seg=10, rings=4, scale=(1.3, 1, 0.15))
    lathe("Stockpot", [(0, z), (0.4, z), (0.44, z + 0.06), (0.44, z + 0.7), (0.46, z + 0.74), (0.42, z + 0.74), (0.4, z + 0.06), (0, z + 0.04)], cu, seg=24,
          loc=(0.05, -0.47, 0))
    for sx in (-1, 1):
        tube(f"StockHandle{sx}", [(0.05 + sx * 0.44, -0.47, z + 0.6), (0.05 + sx * 0.56, -0.47, z + 0.6), (0.05 + sx * 0.56, -0.47, z + 0.5),
                                  (0.05 + sx * 0.44, -0.47, z + 0.5)], 0.02, br)
    for i in range(3):
        r = 0.42 - i * 0.06
        zz = z + i * 0.09
        lathe(f"PanStack{i}", [(0, zz), (r * 0.85, zz), (r, zz + 0.08), (r - 0.02, zz + 0.08), (r * 0.83, zz + 0.02), (0, zz + 0.02)], cu, seg=24,
              loc=(1.4, -0.48, 0))
    # the hook rail below with hanging copper pans and ladles
    rz = 1.9
    tube("HookRail", [(-W / 2 + 0.3, -0.35, rz), (W / 2 - 0.3, -0.35, rz)], 0.03, br, poly=True)
    for sx in (-1, 1):
        box(f"RailMount{sx}", (0.06, 0.35, 0.06), (sx * (W / 2 - 0.3), -0.18, rz), br, bevel=0.01)
    hangs = (("Pan", -1.7, 0.42), ("Pan", -0.85, 0.34), ("Ladle", -0.2, 0.0), ("Skimmer", 0.3, 0.0), ("Pan", 1.05, 0.38), ("Ladle", 1.8, 0.0))
    for k, (kind, x, r) in enumerate(hangs):
        tube(f"Hook{k}", [(x, -0.35, rz + 0.04), (x, -0.42, rz - 0.02), (x, -0.4, rz - 0.12)], 0.012, ir)
        if kind == "Pan":
            hz = rz - 0.15 - 0.5 - r
            box(f"PanHandle{k}", (0.07, 0.03, 0.5), (x, -0.42, rz - 0.15 - 0.25), cu, bevel=0.01)
            cyl(f"PanBody{k}", r, 0.1, (x, -0.4, hz), cu, rot=(math.pi / 2, 0, 0), verts=24, bevel=0.03)
            cyl(f"PanBottom{k}", r * 0.9, 0.02, (x, -0.34, hz), M["iron"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0)
        else:
            tube(f"{kind}Handle{k}", [(x, -0.42, rz - 0.12), (x, -0.43, rz - 0.9)], 0.018, cu, poly=True)
            if kind == "Ladle":
                sphere(f"LadleBowl{k}", 0.13, (x, -0.45, rz - 1.0), cu, seg=12, rings=6, scale=(1, 0.8, 0.8))
            else:
                cyl(f"Skimmer{k}", 0.15, 0.02, (x, -0.43, rz - 1.02), M["iron"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.005)
    return _dims()


# ================================================================== dish stack
def dish_stack(M):
    por, ir, br = porcelain(), M["iron"], M["brass"]
    band = M["crimson"]
    st = steel()
    set_group("Main")
    # two plate stacks and a bowl stack on a pewter mat
    box("Mat", (2.5, 1.25, 0.03), (0, 0, 0.015), pewter(), bevel=0.01)
    plate_stack("Big", -0.75, -0.1, 0.03, 14, 0.36, por, band)
    plate_stack("Small", -0.05, -0.25, 0.03, 10, 0.27, por, band)
    prof = [(0, 0.03)]
    for i in range(6):
        zb = 0.03 + i * 0.07
        prof += [(0.12, zb), (0.24, zb + 0.08), (0.27, zb + 0.15), (0.25, zb + 0.15)]
    prof += [(0.12, 0.03 + 6 * 0.07 + 0.02), (0, 0.03 + 6 * 0.07 + 0.02)]
    lathe("Bowls", prof, por, seg=24, loc=(-0.15, 0.32, 0))
    hoop("BowlRim", (-0.15, 0.32, 0.03 + 5 * 0.07 + 0.14), 0.26, "Z", band, thick=0.008)
    # the cutlery bin: an iron box of three compartments, forks, knives and spoons
    bx = 0.75
    box("BinBase", (0.75, 0.5, 0.04), (bx, 0.0, 0.05), ir, bevel=0.01)
    for sx in (-1, 1):
        box(f"BinEnd{sx}", (0.03, 0.5, 0.42), (bx + sx * 0.36, 0.0, 0.25), ir, bevel=0.005)
    for sy in (-1, 1):
        box(f"BinSide{sy}", (0.75, 0.03, 0.42), (bx, sy * 0.235, 0.25), ir, bevel=0.005)
    for k in (-1, 1):
        box(f"BinDivider{k}", (0.02, 0.47, 0.38), (bx + k * 0.12, 0.0, 0.24), ir, bevel=0)
    tube("BinHandle", [(bx - 0.3, 0.0, 0.46), (bx - 0.3, 0.0, 0.62), (bx + 0.3, 0.0, 0.62), (bx + 0.3, 0.0, 0.46)], 0.02, br, poly=True)
    rnd = random.Random(3)
    for k, cx in enumerate((bx - 0.24, bx, bx + 0.24)):
        for i in range(7):
            x, y = cx + rnd.uniform(-0.06, 0.06), rnd.uniform(-0.17, 0.17)
            lean = rnd.uniform(-0.12, 0.12)
            tube(f"Utensil{k}{i}", [(x, y, 0.1), (x + lean * 0.3, y, 0.62)], 0.014, st, poly=True)
            if k == 0:
                box(f"Fork{k}{i}", (0.06, 0.01, 0.12), (x + lean * 0.35, y, 0.68), st, bevel=0)
            elif k == 1:
                box(f"Knife{k}{i}", (0.035, 0.008, 0.16), (x + lean * 0.35, y, 0.7), st, bevel=0)
            else:
                sphere(f"Spoon{k}{i}", 0.04, (x + lean * 0.35, y, 0.68), st, seg=8, rings=4, scale=(0.8, 0.4, 1.2))
    # the brass cup tree with six cups
    tx, ty = 0.15, 0.5
    lathe("TreeBase", [(0, 0.03), (0.2, 0.03), (0.18, 0.07), (0.05, 0.1), (0, 0.1)], br, seg=16, loc=(tx, ty, 0))
    tube("TreeStem", [(tx, ty, 0.1), (tx, ty, 1.35)], 0.03, br, poly=True)
    sphere("TreeKnob", 0.05, (tx, ty, 1.38), br, seg=8, rings=4)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        hz = 0.75 + (i % 2) * 0.3
        hx, hy = tx + math.cos(a) * 0.22, ty + math.sin(a) * 0.22
        tube(f"TreeArm{i}", [(tx, ty, hz - 0.05), (hx, hy, hz + 0.04)], 0.012, br, poly=True)
        m = _mark()
        cup(f"TreeCup{i}", 0, 0, 0, por, band, s=0.8, handle=False)
        _xform(m, Matrix.Translation((hx + math.cos(a) * 0.08, hy + math.sin(a) * 0.08, hz - 0.12)) @ Matrix.Rotation(a, 4, "Z"))
    return _dims()


P.PREVIEW_PAD.update({"ServingCounter": 0.95, "TrayRack": 1.05, "KitchenShelf": 1.0})

P.BUILD.update({
    "ServingCounter": serving_counter,
    "TrayRack": tray_rack,
    "DrinksDispenser": drinks_dispenser,
    "BakeryCase": bakery_case,
    "CoffeeMachine": coffee_machine,
    "KitchenShelf": kitchen_shelf,
    "DishStack": dish_stack,
})
