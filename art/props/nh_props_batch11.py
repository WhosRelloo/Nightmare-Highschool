"""Props batch 11 (2026-11-03): the town's shops and street furniture for nh_props.py, in Nightmare High's gritty gothic
night-town style: dark sooty castle stone, moss in the joints, oxblood and bottle-green painted cast iron, brass,
gaslight. Original designs; the signs carry symbols, never words.

  ShopApothecary  a shop front module (12 x 12, a wall piece): stone piers and upper wall with a traceried oculus,
                  an oxblood cast-iron front with a gilt mortar-and-moon fascia, a bay window (Glass) full of coloured
                  bottles and show globes lit by a hanging lamp (Glow), a panelled door (Door0: hinge on its left edge,
                  swings out toward the street) and a hanging sign on a gallows bracket (Cloth: it sways)
  ShopCurio       a second shop front (12 x 12, a wall piece): bottle-green and brass, a pointed-arch window with
                  iron tracery (Glass) over a display of clocks, masks, candles (Glow), a skull, books, a crystal ball
                  and a raven in a cage; a door on the left (Door0: hinge on its left edge, swings out) and three gilt
                  balls hanging from a bracket (Cloth: they sway); lancet windows and a crow above
  MarketStall     an iron-framed market stall under a striped crimson and black canvas awning whose scalloped
                  valance sways (Cloth), a slate counter with crates of apples, a crate of pumpkins, jars on a stepped
                  stand, a brass hanging scale and a lantern (Glass, Glow)
  HangingSign     a wall sign: a scrolled iron gallows bracket and a gilt-bordered oxblood board with a crescent moon
                  over a mortar and pestle; the board and its chains sway about the crossbar (Cloth; a wall piece)
  Postbox         an octagonal cast-iron pillar box in crimson enamel: lancet panels, a hooded letter slot, a crest,
                  a blank times plate and a gothic crown of gables with a crocketed spire
  StreetPump      a parish water pump: a fluted iron column with a grotesque-head spout and a long lever handle over
                  a mossy stone trough holding water (Pool: the water and the trickle from the spout)
  NewsKiosk       an octagonal iron news kiosk: traceried lower panels, posters on the upper faces, a serving window
                  with stacked papers, a slate ogee dome with a crescent finial, and a lantern on a bracket (Glass, Glow)
  TelephoneBooth  a gothic cast-iron booth in ink-blue and brass: buttressed corner posts with pinnacles, lancet
                  windows (Glass), gabled roof and a crocketed spire over a little lantern (Glow), a wall telephone inside
  Bollards        three cast-iron bollards with brass bands and a sagging chain between them (about 8 long)
  IronRailing     an 8-stud wrought-iron railing on a stone coping: spear-headed bars, a ring band, a centre post;
                  it tiles end to end (the bars keep their spacing across the joint)
  Signpost        a fingerpost: an iron post with three arrow boards carrying icons (the school, a church, a
                  crossroads), a pinnacle cap and a crow
  CratePile       market goods: iron-strapped crates, an open crate of turnips and apples, an iron-hooped barrel,
                  sacks and an oxblood tarpaulin tied over the top crate

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, _mesh, prism, _mark, _xform, _dims, flat
from nh_props_batch6 import relief, lin
from nh_props_batch8 import (castle, hollow, staining, _foil, _pointed, _lancet, _spirelet, _spike, _crockets, _raven,
                             _lantern, _lights, _link, _stain, _moss, _grotesque)


# ------------------------------------------------------------------ materials

def _town_stone(name, tint):
    """The town's sooty stone, shared with the building pieces (nh_props_batch12.soot_stone: the limestone set,
    darker, with vertical soot streaks in the material). Falls back to the plain darkened set if batch 12 is missing."""
    try:
        from nh_props_batch12 import soot_stone
        return soot_stone(name, tint)
    except Exception:  # noqa: BLE001
        return material(name, "NH_Limestone", tint=tint, scale=0.28, wear=0.15, dirt=1.0, rough_add=0.08)


def town():
    """The night-town's own materials (the school palette M supplies iron, brass, slate, paper and glass)."""
    return {
        "stone": _town_stone("SootStone", (0.15, 0.158, 0.148)),
        "stonedark": _town_stone("SootStoneDark", (0.09, 0.095, 0.088)),
        "soot": material("SootStone", "NH_Limestone", tint=(0.13, 0.13, 0.125), scale=0.28, wear=0.15, dirt=1.0),
        "oxblood": material("Oxblood", "NH_PaintedMetal", tint=(0.095, 0.011, 0.016), scale=1.1, rough_add=0.08, wear=0.55, wear_metal=True),
        "signred": material("SignOxblood", "NH_PaintedMetal", tint=(0.055, 0.006, 0.009), scale=1.1, rough_add=0.15, wear=0.5, wear_metal=True),
        "oxbloodthin": flat("OxbloodEnamel", (0.075, 0.008, 0.012), 0.48, wear=0.03, dirt=0.7),
        "green": material("BottleGreen", "NH_PaintedMetal", tint=(0.018, 0.05, 0.036), scale=1.1, wear=0.6, wear_metal=True),
        "greenthin": flat("BottleGreenEnamel", (0.012, 0.04, 0.028), 0.36, wear=0.03, dirt=0.6),
        "ink": material("InkPaint", "NH_PaintedMetal", tint=(0.025, 0.03, 0.06), scale=1.1, wear=0.6, wear_metal=True),
        "inkthin": flat("InkEnamel", (0.018, 0.022, 0.045), 0.35, wear=0.03, dirt=0.6),
        "hollow": hollow(),
        "stain": staining(),
        "moss": flat("Moss", (0.022, 0.045, 0.016), 0.92, dirt=0.6),
        "crack": flat("Crack", (0.012, 0.011, 0.011), 0.95, dirt=0.2),
        "bone": flat("Bone", (0.78, 0.74, 0.64), 0.5, dirt=0.6),
        "wax": flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55),
        "darkglass": flat("DarkGlass", (0.01, 0.012, 0.018), 0.06, dirt=0.2),
        "boards": material("CrateBoards", "NH_Boards", tint=(0.15, 0.125, 0.105), scale=0.5, rough_add=0.15, wear=0.3, dirt=1.0),
        "burlap": material("Burlap", "NH_Leather", tint=(0.42, 0.33, 0.21), scale=3.0, normal=0.25, rough_add=0.5, wear=0.05, dirt=0.8),
        "canvasred": material("CanvasRed", "NH_Leather", tint=(0.2, 0.02, 0.03), scale=3.5, normal=0.25, rough_add=0.45, wear=0.05, dirt=0.7),
        "canvasblack": material("CanvasBlack", "NH_Leather", tint=(0.025, 0.022, 0.026), scale=3.5, normal=0.25, rough_add=0.45, wear=0.05, dirt=0.7),
        "water": flat("TroughWater", (0.025, 0.045, 0.055), 0.02),
    }


def glassy(name, rgb):
    """Coloured bottle glass (baked: a deep colour with a glassy sheen)."""
    return flat(name, rgb, 0.08, dirt=0.25)


# ------------------------------------------------------------------ helpers

def dims():
    """_dims() after baking every part's transform into its mesh, so rotated parts give true bounds (a rotated
    object's bound box is its local box turned, which overstates the size)."""
    for ob in P.PARTS:
        if ob.type == "MESH" and ob.matrix_basis != Matrix.Identity(4):
            ob.data.transform(ob.matrix_basis)
            ob.matrix_basis = Matrix.Identity(4)
    return _dims()


def rot_about(p, a):
    """Rotation by `a` about the vertical axis through point p."""
    return Matrix.Translation(p) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation(-Vector(p))


def bottle(prefix, x, y, z, h, r, mat, stopper, kind=0):
    """A small apothecary bottle standing at z: 0 round-shouldered, 1 square-ish (8 sides), 2 flask, 3 tall neck."""
    if kind == 2:
        prof = [(0, 0), (r * 0.9, 0.0), (r * 1.25, h * 0.25), (r * 0.9, h * 0.55), (r * 0.32, h * 0.72), (r * 0.3, h * 0.92), (r * 0.36, h), (0, h)]
    elif kind == 3:
        prof = [(0, 0), (r, 0.0), (r, h * 0.45), (r * 0.5, h * 0.56), (r * 0.22, h * 0.62), (r * 0.22, h * 0.95), (r * 0.3, h), (0, h)]
    else:
        prof = [(0, 0), (r, 0.0), (r, h * 0.64), (r * 0.8, h * 0.74), (r * 0.36, h * 0.8), (r * 0.34, h * 0.94), (r * 0.42, h), (0, h)]
    lathe(f"{prefix}Body", prof, mat, seg=8 if kind == 1 else 12, loc=(x, y, z))
    cyl(f"{prefix}Stopper", r * 0.3, h * 0.12, (x, y, z + h * 1.04), stopper, verts=8, bevel=0)


def chain(prefix, p0, p1, sag, mat, r=0.04, step=None):
    """A sagging chain of small links between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    step = step or r * 1.55
    n = max(2, int(L / step))
    d = (p1 - p0).normalized()
    for i in range(n + 1):
        t = i / n
        c = p0 + (p1 - p0) * t - Vector((0, 0, sag * 4 * t * (1 - t)))
        axis = "Z" if i % 2 else ("Y" if abs(d.x) > abs(d.y) else "X")
        if abs(d.z) > 0.8:
            axis = "X" if i % 2 else "Y"
        _link(f"{prefix}{i}", tuple(c), axis, r, mat)


def mortar_moon(prefix, cx, y, cz, s, mat, depth=0.03):
    """The apothecary's mark in flat relief facing -Y: a crescent moon over a mortar and pestle."""
    # crescent: an outer circle less an inner offset circle, as one concave outline
    n = 20
    outer = [(cx + math.cos(math.pi * 0.25 + i / n * math.pi * 1.5) * 0.3 * s, cz + 0.42 * s + math.sin(math.pi * 0.25 + i / n * math.pi * 1.5) * 0.3 * s)
             for i in range(n + 1)]
    inner = [(cx + 0.1 * s + math.cos(math.pi * 1.75 - i / n * math.pi * 1.5) * 0.25 * s, cz + 0.45 * s + math.sin(math.pi * 1.75 - i / n * math.pi * 1.5) * 0.25 * s)
             for i in range(n + 1)]
    relief(f"{prefix}Moon", outer + inner[1:-1], y, depth, mat, plane="XZ")
    bowl = [(cx - 0.34 * s, cz + 0.02 * s), (cx + 0.34 * s, cz + 0.02 * s), (cx + 0.3 * s, cz - 0.12 * s), (cx + 0.18 * s, cz - 0.27 * s),
            (cx + 0.1 * s, cz - 0.3 * s), (cx + 0.14 * s, cz - 0.4 * s), (cx - 0.14 * s, cz - 0.4 * s), (cx - 0.1 * s, cz - 0.3 * s),
            (cx - 0.18 * s, cz - 0.27 * s), (cx - 0.3 * s, cz - 0.12 * s)]
    relief(f"{prefix}Mortar", bowl, y, depth, mat, plane="XZ")
    tube(f"{prefix}Pestle", [(cx + 0.04 * s, y, cz - 0.04 * s), (cx + 0.36 * s, y, cz + 0.26 * s)], 0.045 * s, mat, square=True, poly=True)
    sphere(f"{prefix}PestleEnd", 0.07 * s, (cx + 0.38 * s, y, cz + 0.28 * s), mat, seg=10, rings=5, scale=(1, depth / (0.14 * s), 1))


def key_mark(prefix, cx, y, cz, s, mat, depth=0.03):
    """A gilt key in relief facing -Y (the curio shop's mark)."""
    tube(f"{prefix}Bow", circle_pts(cx - 0.42 * s, y, cz, 0.14 * s, "Y", 14), 0.035 * s, mat, closed=True, square=True, poly=True)
    _foil(f"{prefix}Foil", cx - 0.42 * s, y, cz, 0.06 * s, mat, lobes=4, thick=0.012 * s)
    box(f"{prefix}Shank", (0.62 * s, depth, 0.06 * s), (cx + 0.02 * s, y, cz), mat, bevel=0.004)
    for k, (dx, dz) in enumerate(((0.22, -0.09), (0.3, -0.12), (0.12, -0.07))):
        box(f"{prefix}Bit{k}", (0.06 * s, depth, abs(dz) * 2 * s), (cx + dx * s, y, cz + dz * s), mat, bevel=0.003)


def panel_door(prefix, x0, x1, y, z0, z1, paint, M, glazed=True, knob_side=1):
    """A panelled shop door between x0..x1 at y (its face toward -Y): raised lower panels, an upper glazed panel with
    a pointed-arch grille over dark glass, a brass kick plate, knob and escutcheon."""
    w, h = x1 - x0, z1 - z0
    cx = (x0 + x1) / 2
    box(f"{prefix}Leaf", (w, 0.12, h), (cx, y, (z0 + z1) / 2), paint, bevel=0.015)
    yf = y - 0.065
    for k, (pz0, pz1) in enumerate(((z0 + 0.45, z0 + h * 0.36), (z0 + h * 0.4, z0 + h * 0.52))):
        for sx in (-1, 1):
            pw = w / 2 - 0.22
            box(f"{prefix}Panel{k}{sx}", (pw, 0.04, pz1 - pz0), (cx + sx * (pw / 2 + 0.06), yf, (pz0 + pz1) / 2), paint, bevel=0.012)
    gz0, gz1 = z0 + h * 0.57, z1 - 0.22
    if glazed:
        hw = w / 2 - 0.2
        box(f"{prefix}GlassBack", (hw * 2, 0.02, gz1 - gz0), (cx, y - 0.062, (gz0 + gz1) / 2), M["darkglass"], bevel=0.0, segments=1)
        pts = [(cx - hw, yf - 0.01, gz0)] + [(cx + px, yf - 0.01, pz) for px, pz in _pointed(hw, gz1 - hw * 1.1, gz1, 8)] + [(cx + hw, yf - 0.01, gz0)]
        tube(f"{prefix}GlassFrame", pts, 0.035, paint, closed=True, square=True, poly=True)
        tube(f"{prefix}Bar", [(cx, yf - 0.02, gz0), (cx, yf - 0.02, gz1 - 0.05)], 0.018, M["brass"], square=True, poly=True)
        tube(f"{prefix}BarX", [(cx - hw, yf - 0.02, (gz0 + gz1) / 2 - 0.15), (cx + hw, yf - 0.02, (gz0 + gz1) / 2 - 0.15)], 0.018, M["brass"],
             square=True, poly=True)
    box(f"{prefix}Kick", (w - 0.12, 0.02, 0.3), (cx, y - 0.07, z0 + 0.2), M["brass"], bevel=0.006)
    kx = x1 - 0.28 if knob_side > 0 else x0 + 0.28
    box(f"{prefix}Escutcheon", (0.1, 0.02, 0.34), (kx, y - 0.07, z0 + h * 0.47), M["brass"], bevel=0.008)
    sphere(f"{prefix}Knob", 0.07, (kx, y - 0.14, z0 + h * 0.49), M["brass"], seg=12, rings=6)
    box(f"{prefix}Keyhole", (0.025, 0.01, 0.06), (kx, y - 0.083, z0 + h * 0.44), M["hollow"], bevel=0.0, segments=1)
    for k, hz in enumerate((z0 + 0.5, z1 - 0.6)):
        hx = x0 + 0.05 if knob_side > 0 else x1 - 0.05
        cyl(f"{prefix}Hinge{k}", 0.04, 0.34, (hx, y - 0.07, hz), M["brass"], verts=8, bevel=0)


def pilaster_iron(prefix, x, y, z0, z1, paint, M, w=0.32):
    """A cast-iron shop-front pilaster facing -Y: base, fluted shaft, brass necking and a foliate capital block."""
    box(f"{prefix}Base", (w + 0.12, w + 0.1, 0.4), (x, y, z0 + 0.2), paint, bevel=0.02)
    box(f"{prefix}Shaft", (w, w, z1 - z0 - 0.85), (x, y, (z0 + 0.4 + z1 - 0.45) / 2), paint, bevel=0.02)
    for k in (-1, 0, 1):
        box(f"{prefix}Flute{k}", (0.035, 0.02, z1 - z0 - 1.25), (x + k * w * 0.27, y - w / 2 - 0.002, (z0 + 0.6 + z1 - 0.65) / 2), P.PARTS[-1].active_material,
            bevel=0.0, segments=1)
    box(f"{prefix}Neck", (w + 0.04, w + 0.04, 0.07), (x, y, z1 - 0.42), M["brass"], bevel=0.01)
    box(f"{prefix}Cap", (w + 0.16, w + 0.14, 0.32), (x, y, z1 - 0.2), paint, bevel=0.03)
    for sx in (-1, 1):
        sphere(f"{prefix}Volute{sx}", 0.06, (x + sx * (w / 2 + 0.05), y - w / 2 - 0.05, z1 - 0.12), M["brass"], seg=8, rings=4)


def stone_pier(prefix, x, y0, y1, z1, M, T, w=0.8, rnd=None):
    """A stone pier from the ground to z1 between y0 (front) and y1 (back), with a plinth, quoin joints and a corbel cap."""
    d = y1 - y0
    cy = (y0 + y1) / 2
    box(f"{prefix}Plinth", (w + 0.16, d + 0.14, 0.7), (x, cy - 0.07, 0.35), T["stonedark"], bevel=0.04)
    box(f"{prefix}Shaft", (w, d, z1 - 0.7), (x, cy, 0.7 + (z1 - 0.7) / 2), T["stone"], bevel=0.03)
    z = 1.6
    k = 0
    while z < z1 - 0.3:
        box(f"{prefix}Joint{k}", (w + 0.01, 0.012, 0.025), (x, y0 - 0.004, z), T["stonedark"], bevel=0.0, segments=1)
        z += 0.9
        k += 1
    box(f"{prefix}Corbel", (w + 0.2, d + 0.24, 0.3), (x, cy - 0.12, z1 + 0.15), T["stonedark"], bevel=0.04)
    if rnd:
        _moss(f"{prefix}Moss", [(x + rnd.uniform(-0.4, 0.4), y0 - 0.08, 0.72) for _ in range(3)], T["moss"], rnd, 0.09)


def soot_streak(name, x, y, ztop, length, width, mat, rnd):
    """A soot run down a stone face (facing -Y at y): narrow, wavering, fading to a point."""
    n = 7
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = width * (1 - t) ** 0.7 * rnd.uniform(0.7, 1.15) + 0.005
        xc = x + 0.04 * math.sin(t * 5 + x * 3)
        z = ztop - length * t
        left.append((xc - w / 2, z))
        right.append((xc + w / 2, z))
    relief(name, left + list(reversed(right)), y, 0.004, mat, plane="XZ")


def grime_band(name, x0, x1, y, z0, h, mat, rnd):
    """Rising damp and street grime along the foot of a face (facing -Y at y): a wavy-topped dark band."""
    n = max(4, int((x1 - x0) / 0.25))
    top = [(x0 + (x1 - x0) * i / n, z0 + h * rnd.uniform(0.55, 1.0)) for i in range(n + 1)]
    relief(name, [(x0, z0)] + top + [(x1, z0)], y, 0.004, mat, plane="XZ")


def soot_mats():
    return flat("Soot", (0.022, 0.022, 0.02), 0.95, dirt=0.4), flat("Grime", (0.05, 0.048, 0.04), 0.95, dirt=0.6)


def cresting(prefix, pts, mat, h=0.22):
    """Iron cresting along a line of points: little fleur spikes with a ball each."""
    for k, p in enumerate(pts):
        _spike(f"{prefix}Spike{k}", (p[0], p[1], p[2] + h / 2), 0.035, h, mat, verts=4, rot=(0, 0, math.pi / 4))
        sphere(f"{prefix}Ball{k}", 0.03, (p[0], p[1], p[2] + h * 0.3), mat, seg=6, rings=3)


def upper_wall(T, rnd, W=12.0, zb=9.8, zt=12.0, streaks=()):
    """The storey above a shop front: a stringcourse, the stone face, soot stains and a cornice."""
    box("Stringcourse", (W, 0.62, 0.36), (0, -0.62, zb - 0.18), T["stonedark"], bevel=0.04)
    box("StringcourseDrip", (W, 0.12, 0.1), (0, -0.88, zb - 0.38), T["stonedark"], bevel=0.02)
    box("Cornice", (W, 0.7, 0.3), (0, -0.66, zt - 0.15), T["stonedark"], bevel=0.04)
    box("CorniceBed", (W - 0.2, 0.46, 0.16), (0, -0.55, zt - 0.38), T["stone"], bevel=0.03)
    for k in range(23):
        x = -W / 2 + 0.36 + k * (W - 0.72) / 22
        box(f"Dentil{k}", (0.18, 0.2, 0.16), (x, -0.42, zt - 0.54), T["stonedark"], bevel=0.015)
    soot, _ = soot_mats()
    for k, x in enumerate(streaks):
        soot_streak(f"Soot{k}", x + rnd.uniform(-0.08, 0.08), -0.404, zt - 0.62, rnd.uniform(0.6, 1.5), rnd.uniform(0.14, 0.24), soot, rnd)


def pier_grime(T, rnd, xs, y0, z1):
    """Soot runs from the stringcourse down the pier faces and grime along their feet."""
    soot, grime = soot_mats()
    for sx, x in enumerate(xs):
        for j in range(2):
            soot_streak(f"PierSoot{sx}{j}", x + rnd.uniform(-0.25, 0.25), y0 - 0.004, z1 - 0.05, rnd.uniform(1.2, 3.0), rnd.uniform(0.12, 0.22), soot, rnd)
        grime_band(f"PierGrime{sx}", x - 0.42, x + 0.42, y0 - 0.075 - 0.004, 0.0, 0.55, grime, rnd)


# ================================================================== apothecary
def shop_stone(T):
    """The shop fronts use the town's sooty stone (town() already carries it, matching the batch 12 building pieces)."""
    return T


def shop_apothecary(M):
    T = shop_stone(town())
    rnd = random.Random(111)
    W, H = 12.0, 12.0
    paint = T["oxblood"]
    gilt = M["brass"]
    # the building face behind it all (the back of the module sits at y = 0)
    box("Wall", (W, 0.4, H), (0, -0.2, H / 2), T["stone"], bevel=0.02)
    for sx in (-1, 1):
        stone_pier(f"Pier{sx}", sx * 5.6, -0.95, -0.4, 9.45, M, T, rnd=rnd)
    set_group("Upper")                       # the storey above the shop is its own piece
    upper_wall(T, rnd, streaks=(-5.3, -4.5, -2.75, -1.1, 1.1, 2.75, 4.5))
    pier_grime(T, rnd, (-5.6, 5.6), -0.95, 9.45)
    # oculus with tracery in the upper wall
    zc = 10.6
    cyl("OculusDark", 0.5, 0.05, (0, -0.42, zc), T["hollow"], rot=(math.pi / 2, 0, 0), verts=32, bevel=0)
    hoop("OculusRing", (0, -0.48, zc), 0.55, "Y", T["stonedark"], thick=0.09)
    _foil("OculusFoil", 0, -0.46, zc, 0.26, T["stonedark"], lobes=4, thick=0.04)
    for sx in (-1, 1):
        for j in (0, 1):
            x = sx * (2.0 + j * 1.5)
            pts = [(x - 0.4, 10.0)] + [(x + px, pz) for px, pz in _pointed(0.4, 10.8, 11.25, 8)] + [(x + 0.4, 10.0)]
            relief(f"Blind{sx}{j}", pts, -0.41, 0.03, T["hollow"], plane="XZ")
            tube(f"BlindFrame{sx}{j}", [(px, -0.45, pz) for px, pz in pts], 0.055, T["stonedark"], closed=True, square=True, poly=True)
            box(f"BlindSill{sx}{j}", (0.95, 0.24, 0.08), (x, -0.52, 9.98), T["stonedark"], bevel=0.015)
    set_group("Main")
    # the fascia: oxblood with gilt mouldings and the mortar-and-moon mark, a cornice, scrolled consoles
    box("Fascia", (10.4, 0.7, 1.2), (0, -0.75, 8.3), paint, bevel=0.02)
    for z in (7.75, 8.85):
        box(f"FasciaMould{z}", (10.4, 0.06, 0.06), (0, -1.12, z), gilt, bevel=0.01)
    box("FasciaCornice", (10.9, 0.72, 0.22), (0, -0.76, 9.0), paint, bevel=0.03)
    box("FasciaCorniceTop", (11.0, 0.6, 0.1), (0, -0.72, 9.16), T["inkthin"], bevel=0.02)
    mortar_moon("FasciaMark", 0, -1.12, 8.18, 0.8, gilt)
    for sx in (-1, 1):
        for k in range(5):
            _foil(f"FasciaFoil{sx}{k}", sx * (1.3 + k * 0.78), -1.12, 8.3, 0.17, gilt, lobes=4, thick=0.018)
        box(f"FasciaRule{sx}", (3.6, 0.03, 0.03), (sx * 2.85, -1.12, 8.62), gilt, bevel=0.0, segments=1)
        box(f"FasciaRuleLow{sx}", (3.6, 0.03, 0.03), (sx * 2.85, -1.12, 7.98), gilt, bevel=0.0, segments=1)
        box(f"Console{sx}", (0.3, 0.55, 1.3), (sx * 5.05, -1.05, 8.3), paint, bevel=0.04)
        sphere(f"ConsoleBoss{sx}", 0.1, (sx * 5.05, -1.35, 8.55), gilt, seg=10, rings=5)
        cone(f"ConsoleDrop{sx}", 0.1, 0.0, 0.26, (sx * 5.05, -1.15, 7.52), paint, verts=8, rot=(math.pi, 0, 0))
    # iron pilasters
    for k, x in enumerate((-5.0, 0.95, 4.5)):
        pilaster_iron(f"Pil{k}", x, -0.58, 0.0, 7.65, paint, M)
    box("Lintel", (10.0, 0.3, 0.12), (0, -0.62, 7.7), paint, bevel=0.015)
    # the bay window: an oxblood riser, mullions, a top with iron cresting
    back_l, back_r, front_l, front_r, yb, yfr = -4.75, 0.7, -3.75, -0.3, -0.45, -1.75
    outline = [(back_l, yb), (front_l, yfr), (front_r, yfr), (back_r, yb)]
    # a stone plinth following the bay's outline, the oxblood riser standing on it (no part cuts through another)
    prism("RiserBase", [(back_l - 0.06, yb), (front_l - 0.05, yfr - 0.07), (front_r + 0.05, yfr - 0.07), (back_r + 0.06, yb)], 0.0, 0.2, T["stonedark"], plane="XY")
    prism("Riser", [(x, y) for x, y in outline], 0.2, 1.1, paint, plane="XY", bevel=0.0)
    prism("Sill", [(back_l - 0.08, yb), (front_l - 0.06, yfr - 0.1), (front_r + 0.06, yfr - 0.1), (back_r + 0.08, yb)], 1.3, 0.1, T["stonedark"], plane="XY")
    prism("BayTop", [(back_l - 0.06, yb), (front_l - 0.05, yfr - 0.08), (front_r + 0.05, yfr - 0.08), (back_r + 0.06, yb)], 7.2, 0.26, paint, plane="XY")
    prism("BayRoof", [(back_l, yb), (front_l + 0.05, yfr + 0.05), (front_r - 0.05, yfr + 0.05), (back_r, yb)], 7.46, 0.08, M["slate"], plane="XY")
    cresting("BayCrest", [(front_l + 0.15 + k * (front_r - front_l - 0.3) / 7, yfr - 0.02, 7.5) for k in range(8)], M["iron"], h=0.18)
    # riser panels (raised mouldings on the front and sides)
    box("RiserPanel", (front_r - front_l - 0.4, 0.04, 0.7), ((front_l + front_r) / 2, yfr - 0.02, 0.7), T["oxbloodthin"], bevel=0.01)
    corners = [(back_l, yb), (front_l, yfr), (front_r, yfr), (back_r, yb)]
    for k, (x, y) in enumerate(corners):
        box(f"Mullion{k}", (0.14, 0.14, 5.9), (x, y, 4.25), paint, bevel=0.015)
    box("MullionMid", (0.08, 0.1, 5.9), ((front_l + front_r) / 2, yfr, 4.25), paint, bevel=0.01)
    for k in range(3):
        (xa, ya), (xb, yb2) = corners[k], corners[k + 1]
        ang = math.atan2(yb2 - ya, xb - xa)
        L = math.hypot(xb - xa, yb2 - ya)
        box(f"Transom{k}", (L, 0.1, 0.08), ((xa + xb) / 2, (ya + yb2) / 2, 6.35), paint, bevel=0.01, rot=(0, 0, ang))
    # the display inside the bay: slate shelves on brass brackets, bottles, show globes, a hanging lamp
    set_group("Display")
    glasses = [glassy("GlassGreen", (0.02, 0.16, 0.06)), glassy("GlassCrimson", (0.2, 0.01, 0.025)), glassy("GlassAmber", (0.28, 0.12, 0.02)),
               glassy("GlassCobalt", (0.02, 0.04, 0.2)), glassy("GlassSmoke", (0.05, 0.05, 0.05))]
    # a warm plastered back so the bottles show against the light
    box("DisplayBack", (5.4, 0.04, 5.8), (-2.02, -0.43, 4.25), flat("WarmPlaster", (0.34, 0.24, 0.13), 0.85, dirt=0.7), bevel=0.0, segments=1)
    shelves = (2.75, 4.15, 5.45)
    for k, z in enumerate(shelves):
        box(f"Shelf{k}", (5.0, 0.42, 0.06), (-2.02, -0.67, z), M["slate"], bevel=0.01)
        for sx in (-1, 0, 1):
            box(f"ShelfBracket{k}{sx}", (0.04, 0.3, 0.16), (-2.02 + sx * 2.2, -0.6, z - 0.1), gilt, bevel=0.005)
        x = -4.35
        j = 0
        while x < 0.3:
            r = rnd.uniform(0.1, 0.16)
            h = rnd.uniform(0.5, 0.85) if k < 2 else rnd.uniform(0.42, 0.7)
            bottle(f"B{k}_{j}", x + r, -0.7 + rnd.uniform(-0.06, 0.06), z + 0.03, h, r, glasses[rnd.randrange(5)], gilt if j % 3 else T["bone"],
                   kind=rnd.randrange(4))
            x += 2 * r + rnd.uniform(0.05, 0.14)
            j += 1
    # two show globes on brass stands and a big one in the middle on the riser
    for k, (x, r, g) in enumerate(((-3.35, 0.34, glasses[0]), (-0.7, 0.3, glasses[3]), (-2.05, 0.46, glasses[1]))):
        y = -1.3 if k == 2 else -1.1
        zb = 1.4
        lathe(f"GlobeStand{k}", [(0, 0), (0.22, 0), (0.22, 0.05), (0.08, 0.12), (0.06, 0.4), (0.14, 0.48), (0, 0.5)], gilt, seg=16, loc=(x, y, zb))
        lathe(f"Globe{k}", [(0, 0), (r * 0.3, 0.0), (r * 0.9, r * 0.35), (r, r * 0.9), (r * 0.85, r * 1.5), (r * 0.25, r * 1.85),
                            (r * 0.2, r * 2.15), (r * 0.28, r * 2.2), (0, r * 2.2)], g, seg=24, loc=(x, y, zb + 0.5))
        cone(f"GlobeFinial{k}", r * 0.32, 0.0, r * 0.6, (x, y, zb + 0.5 + r * 2.5), gilt, verts=8)
    # a brass mortar and a few paper packets on the riser
    lathe("Mortar", [(0, 0), (0.16, 0), (0.2, 0.12), (0.18, 0.2), (0.15, 0.2), (0.12, 0.08), (0, 0.06)], gilt, seg=16, loc=(-3.0, -1.45, 1.4))
    tube("Pestle", [(-3.0, -1.45, 1.5), (-2.88, -1.42, 1.78)], 0.025, T["bone"], poly=True)
    for k in range(3):
        box(f"Packet{k}", (0.24, 0.16, 0.3 - k * 0.05), (-1.2 + k * 0.28, -1.4, 1.4 + (0.3 - k * 0.05) / 2), M["paper"], bevel=0.01, rot=(0, 0, 0.2 * k))
    tube("LampChain", [(-2.05, -1.05, 7.18), (-2.05, -1.05, 6.6)], 0.012, gilt, poly=True)
    lathe("LampHood", [(0, 0), (0.24, 0.0), (0.14, 0.12), (0.04, 0.16), (0, 0.16)], gilt, seg=16, loc=(-2.05, -1.05, 6.42))
    set_group("Glow")
    sphere("LampGlobe", 0.17, (-2.05, -1.05, 6.28), M["glassclear"], seg=14, rings=8, scale=(1, 1, 0.9))
    # shelf lights: a warm strip under the front edge of every shelf (and under the bay top) lights the bottles below
    for k, z in enumerate(shelves):
        box(f"ShelfLight{k}", (4.7, 0.04, 0.03), (-2.02, -0.8, z - 0.045), M["glassclear"], bevel=0.0, segments=1)
    box("BayLight", (2.9, 0.04, 0.03), (-2.02, -1.55, 7.17), M["glassclear"], bevel=0.0, segments=1)
    # the bay glazing
    set_group("Glass")
    for k in range(3):
        (xa, ya), (xb, yb2) = corners[k], corners[k + 1]
        ang = math.atan2(yb2 - ya, xb - xa)
        L = math.hypot(xb - xa, yb2 - ya)
        box(f"Pane{k}", (L - 0.12, 0.02, 5.85), ((xa + xb) / 2, (ya + yb2) / 2, 4.25), M["glassclear"], bevel=0.0, rot=(0, 0, ang), segments=1)
    box("Fanlight", (2.6, 0.02, 0.62), (2.72, -0.48, 7.0), M["glassclear"], bevel=0.0, segments=1)
    set_group("Main")
    # the doorway: reveals, a dark lobby behind the door, the fanlight's bars, a worn step
    box("Lobby", (3.2, 0.02, 7.65), (2.72, -0.41, 3.825), T["hollow"], bevel=0.0, segments=1)
    box("LobbyCurtain", (2.3, 0.02, 5.6), (2.72, -0.425, 3.4), T["canvasred"], bevel=0.005)
    for sx, x in ((-1, 1.265), (1, 4.18)):
        box(f"Jamb{sx}", (0.31, 0.2, 7.65), (x, -0.5, 3.825), paint, bevel=0.01)
    box("FanHead", (3.23, 0.36, 0.34), (2.72, -0.58, 7.48), paint, bevel=0.015)
    box("RightPanel", (0.5, 0.12, 7.6), (4.92, -0.46, 3.8), T["oxbloodthin"], bevel=0.01)
    set_group("Door0", hinge=(1.42, -0.52, 0.3), swing=-1)        # hinge on the left edge, opens out toward the street
    panel_door("Door", 1.42, 4.02, -0.52, 0.3, 6.6, paint, dict(M, **T), glazed=True, knob_side=1)
    set_group("Main")
    for k in range(9):
        tube(f"Fan{k}", [(2.72, -0.5, 6.7), (2.72 + math.cos(math.pi * (k + 1) / 10) * 1.25, -0.5, 6.7 + math.sin(math.pi * (k + 1) / 10) * 0.58)],
             0.014, M["iron"], poly=True)
    box("FanSill", (2.8, 0.14, 0.08), (2.72, -0.5, 6.66), paint, bevel=0.01)
    box("Step", (3.3, 0.85, 0.3), (2.72, -0.82, 0.15), T["stonedark"], bevel=0.04)
    box("StepWorn", (1.6, 0.3, 0.02), (2.72, -1.0, 0.305), T["stone"], bevel=0.01)
    _moss("StepMoss", [(4.2, -1.2, 0.05), (1.3, -1.15, 0.05), (-4.9, -0.75, 0.25)], T["moss"], rnd, 0.1)
    # the hanging sign on a gallows bracket from the right pier
    hx, hz = 5.45, 10.85                      # above the stringcourse, so the board hangs clear of the fascia
    box("BracketPlate", (0.3, 0.06, 0.9), (hx, -0.43, hz - 0.3), M["iron"], bevel=0.01)
    tube("BracketArm", [(hx, -0.43, hz), (hx, -2.35, hz)], 0.03, M["iron"], square=True, poly=True)
    tube("BracketBrace", [(hx, -0.43, hz - 0.7), (hx, -0.9, hz - 0.45), (hx, -1.5, hz - 0.15), (hx, -1.9, hz - 0.02)], 0.022, M["iron"])
    hoop("BracketCurl", (hx, -0.85, hz - 0.22), 0.17, "X", M["iron"], thick=0.016)
    tube("Crossbar", [(hx - 0.6, -2.2, hz - 0.03), (hx + 0.6, -2.2, hz - 0.03)], 0.025, M["iron"], poly=True)
    cone("ArmFinial", 0.05, 0.0, 0.18, (hx, -2.44, hz), M["iron"], verts=6, rot=(math.pi / 2, 0, 0))
    set_group("Cloth", hinge=(hx, -2.2, hz - 0.03), swing=1)
    hanging_board("Sign", hx, -2.2, hz - 0.03, 1.1, 0.9, T["signred"], gilt, M, T, mark="moon")
    set_group("Main")
    return dims()


def hanging_board(prefix, cx, y, ztop, w, h, paint, gilt, M, T, mark="moon"):
    """A sign board hanging from two chains below ztop: a shaped board with a gilt border and a mark on both faces."""
    zb1 = ztop - 0.32
    for sx in (-1, 1):
        chain(f"{prefix}Chain{sx}", (cx + sx * w * 0.38, y, ztop - 0.02), (cx + sx * w * 0.38, y, zb1 + 0.02), 0.0, M["iron"], r=0.03)
    zc = zb1 - h / 2
    half = [(0.0, zb1 + 0.08), (w * 0.2, zb1 + 0.02), (w / 2, zb1), (w / 2, zb1 - h * 0.85), (w * 0.3, zb1 - h * 0.92), (0.0, zb1 - h)]
    outline = [(cx + x, z) for x, z in half] + [(cx - x, z) for x, z in reversed(half[1:-1])]
    relief(f"{prefix}Board", outline, y, 0.07, paint, plane="XZ")
    for face in (-1, 1):
        border = [(cx + ((x - cx) - math.copysign(0.07, x - cx) if abs(x - cx) > 0.01 else 0.0), y + face * 0.04, z + (-0.06 if z > zc else 0.06))
                  for x, z in outline]
        tube(f"{prefix}Border{face}", border, 0.014, gilt, closed=True, square=True, poly=True)
        if mark == "moon":
            mortar_moon(f"{prefix}Mark{face}", cx, y + face * 0.045, zc - 0.05, h * 0.62, gilt, depth=0.02)


# ================================================================== curio shop
def shop_curio(M):
    T = shop_stone(town())
    rnd = random.Random(112)
    W, H = 12.0, 12.0
    paint = T["green"]
    gilt = M["brass"]
    darkstone = T["stone"]
    T2 = T
    box("Wall", (W, 0.4, H), (0, -0.2, H / 2), darkstone, bevel=0.02)
    for sx in (-1, 1):
        stone_pier(f"Pier{sx}", sx * 5.6, -1.1, -0.4, 9.45, M, T2, rnd=rnd)
    set_group("Upper")                       # the storey above the shop is its own piece
    upper_wall(T2, rnd, streaks=(-4.4, -3.5, -1.3, 1.3, 3.5, 4.4, 5.3))
    pier_grime(T2, rnd, (-5.6, 5.6), -1.1, 9.45)
    # two lancet windows above (dark glass, iron leading) and a perched crow on the cornice
    for sx in (-1, 1):
        x = sx * 2.4
        pts = [(x - 0.45, -0.42, 10.0)] + [(x + px, -0.42, pz) for px, pz in _pointed(0.45, 10.75, 11.3, 8)] + [(x + 0.45, -0.42, 10.0)]
        relief(f"Lancet{sx}", [(p[0], p[2]) for p in pts], -0.41, 0.03, T["darkglass"], plane="XZ")
        tube(f"LancetFrame{sx}", [(p[0], -0.45, p[2]) for p in pts], 0.06, T["stonedark"], closed=True, square=True, poly=True)
        for k in range(3):
            tube(f"Leading{sx}{k}", [(x - 0.42, -0.44, 10.2 + k * 0.28), (x + 0.42, -0.44, 10.2 + k * 0.28)], 0.008, M["iron"], poly=True)
        tube(f"LeadingV{sx}", [(x, -0.44, 10.0), (x, -0.44, 11.25)], 0.008, M["iron"], poly=True)
        box(f"LancetSill{sx}", (1.1, 0.3, 0.1), (x, -0.55, 9.95), T["stonedark"], bevel=0.02)
    _raven("Crow", Matrix.Translation((3.9, -0.75, 12.0)) @ Matrix.Rotation(0.5, 4, "Z") @ Matrix.Scale(1.7, 4), T["inkthin"], gilt)
    # a stone-framed clock between the lancets
    cyl("WallClockFace", 0.55, 0.05, (0, -0.44, 10.7), T["bone"], rot=(math.pi / 2, 0, 0), verts=36, bevel=0.0)
    hoop("WallClockRing", (0, -0.5, 10.7), 0.62, "Y", T["stonedark"], thick=0.08)
    hoop("WallClockBezel", (0, -0.48, 10.7), 0.56, "Y", gilt, thick=0.025)
    for j in range(12):
        a = j / 12 * 2 * math.pi
        box(f"WallClockTick{j}", (0.03, 0.01, 0.1 if j % 3 else 0.16), (math.sin(a) * 0.45, -0.475, 10.7 + math.cos(a) * 0.45), T["inkthin"], bevel=0.0,
            rot=(0, -a, 0), segments=1)
    tube("WallClockHour", [(0, -0.49, 10.7), (0.18, -0.49, 10.86)], 0.022, M["iron"], square=True, poly=True)
    tube("WallClockMinute", [(0, -0.5, 10.7), (-0.05, -0.5, 11.1)], 0.014, M["iron"], square=True, poly=True)
    sphere("WallClockBoss", 0.04, (0, -0.51, 10.7), gilt, seg=8, rings=4)
    set_group("Main")
    # the projecting shop case: green-black iron, a fascia with the gilt key, a pointed-arch window
    box("Fascia", (10.4, 0.2, 1.1), (0, -1.15, 8.45), paint, bevel=0.02)
    box("FasciaCornice", (10.9, 0.66, 0.22), (0, -1.12, 9.1), paint, bevel=0.03)
    for z in (7.95, 8.95):
        box(f"FasciaMould{z}", (10.4, 0.06, 0.06), (0, -1.27, z), gilt, bevel=0.01)
    key_mark("FasciaKey", 1.2, -1.27, 8.45, 1.1, gilt)
    for k in range(5):
        _foil(f"FasciaFoil{k}", -4.3 + k * 0.72, -1.27, 8.45, 0.16, gilt, lobes=4, thick=0.016)
    for k in range(2):
        _foil(f"FasciaFoilR{k}", 3.4 + k * 0.72, -1.27, 8.45, 0.16, gilt, lobes=4, thick=0.016)
    cresting("FasciaCrest", [(-5.0 + k * 10.0 / 15, -1.3, 9.21) for k in range(16)], M["iron"], h=0.2)
    box("CaseFront", (10.4, 0.16, 0.22), (0, -1.15, 7.82), paint, bevel=0.015)
    # the window: frame x -1.4..4.9, sill 1.5, springing 6.0, apex 7.65; iron tracery of two lancets and a foil
    wx0, wx1, zs, za, z0 = -1.4, 4.9, 5.9, 7.6, 1.5
    cx, hw = (wx0 + wx1) / 2, (wx1 - wx0) / 2
    arch = [(cx + x, z) for x, z in _pointed(hw, zs, za, 14)]
    frame = [(wx0, 0.0)] + arch + [(wx1, 0.0)]
    # the case walls round the window (green iron panels below the sill and beside it)
    box("Riser", (wx1 - wx0 + 0.3, 0.9, z0), (cx, -0.85, z0 / 2), paint, bevel=0.02)
    box("RiserPanel", (wx1 - wx0 - 0.5, 0.04, z0 - 0.5), (cx, -1.31, z0 / 2 + 0.05), T["greenthin"], bevel=0.01)
    for k in range(4):
        sphere(f"RiserRosette{k}", 0.07, (wx0 + 0.6 + k * (wx1 - wx0 - 1.2) / 3, -1.33, z0 / 2 + 0.05), gilt, seg=10, rings=5)
    box("Sill", (wx1 - wx0 + 0.4, 1.0, 0.1), (cx, -0.85, z0 + 0.05), T["stonedark"], bevel=0.02)
    # spandrel panels above the arch up to the fascia (a concave outline each side)
    for side in (-1, 1):
        if side < 0:
            poly = [(wx0 - 0.15, 7.75), (wx0 - 0.15, zs)] + [p for p in arch if p[0] <= cx + 1e-6] + [(cx, 7.75)]
        else:
            poly = [(cx, 7.75)] + [p for p in arch if p[0] >= cx - 1e-6] + [(wx1 + 0.15, zs), (wx1 + 0.15, 7.75)]
        relief(f"Spandrel{side}", poly, -1.22, 0.12, paint, plane="XZ")
    _foil("SpandrelFoilL", wx0 + 0.5, -1.29, 7.15, 0.22, gilt, lobes=3, thick=0.02)
    _foil("SpandrelFoilR", wx1 - 0.5, -1.29, 7.15, 0.22, gilt, lobes=3, thick=0.02)
    for sx in (-1, 1):
        x = wx0 - 0.08 if sx < 0 else wx1 + 0.08
        box(f"Jamb{sx}", (0.2, 0.24, zs - z0), (x, -1.2, (zs + z0) / 2), paint, bevel=0.015)
        box(f"CaseSide{sx}", (0.08, 0.8, 7.75 - z0), (x, -0.8, (7.75 + z0) / 2), paint, bevel=0.01)
    tube("ArchMould", [(p[0], -1.3, p[1]) for p in arch], 0.06, gilt, square=True, poly=True)
    tube("Mullion", [(cx, -1.27, z0 + 0.1), (cx, -1.27, zs + 0.55)], 0.05, M["iron"], square=True, poly=True)
    for sx in (-1, 1):
        lx = cx + sx * hw / 2
        _lancet(f"Light{sx}", lx, -1.27, z0 + 0.1, hw / 2 - 0.1, zs - 0.1, zs + 0.9, M["iron"], thick=0.03, cusp=False)
    _foil("HeadFoil", cx, -1.27, zs + 1.12, 0.3, M["iron"], lobes=4, thick=0.03)
    tube("Transom", [(wx0 + 0.05, -1.27, 4.9), (wx1 - 0.05, -1.27, 4.9)], 0.03, M["iron"], square=True, poly=True)
    # the display: a stepped shelf of black lacquer, clocks on the back, masks, a skull, books, a crystal ball, candles, a caged raven
    set_group("Display")
    back = T["inkthin"]
    box("DisplayBack", (wx1 - wx0, 0.04, 6.0), (cx, -0.43, z0 + 3.0), material("Damask", "NH_Leather", tint=(0.34, 0.2, 0.08), scale=2.0, normal=0.4, wear=0.05),
        bevel=0.0, segments=1)
    for k, (z, d) in enumerate(((z0 + 0.1, 0.75), (z0 + 1.0, 0.45))):
        box(f"Step{k}", (wx1 - wx0 - 0.1, d, 0.08), (cx, -0.45 - d / 2, z), back, bevel=0.01)
    box("StepRiser", (wx1 - wx0 - 0.1, 0.04, 0.9), (cx, -0.45 - 0.45 + 0.02, z0 + 0.55), back, bevel=0.0, segments=1)
    bone, inkm = T["bone"], T["inkthin"]
    # clocks hung on the back
    for k, (x, z, r) in enumerate(((-0.1, 5.0, 0.55), (2.05, 5.55, 0.38), (3.85, 4.85, 0.45), (2.95, 3.8, 0.28))):
        cyl(f"ClockFace{k}", r, 0.04, (x, -0.47, z), bone, rot=(math.pi / 2, 0, 0), verts=28, bevel=0.0)
        hoop(f"ClockRim{k}", (x, -0.5, z), r + 0.02, "Y", gilt, thick=0.03)
        for j in range(12):
            a = j / 12 * 2 * math.pi
            box(f"ClockTick{k}{j}", (0.02, 0.01, 0.06 if j % 3 else 0.1), (x + math.sin(a) * r * 0.82, -0.5, z + math.cos(a) * r * 0.82), inkm, bevel=0.0,
                rot=(0, -a, 0), segments=1)
        a1, a2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
        tube(f"ClockHandH{k}", [(x, -0.51, z), (x + math.sin(a1) * r * 0.5, -0.51, z + math.cos(a1) * r * 0.5)], 0.012, inkm, poly=True)
        tube(f"ClockHandM{k}", [(x, -0.515, z), (x + math.sin(a2) * r * 0.75, -0.515, z + math.cos(a2) * r * 0.75)], 0.008, inkm, poly=True)
    # a bracket clock (gothic) on the lower step
    box("BracketClock", (0.5, 0.32, 0.6), (-0.6, -0.75, z0 + 0.48), M["iron"], bevel=0.02)
    cyl("BracketClockFace", 0.17, 0.02, (-0.6, -0.92, z0 + 0.52), bone, rot=(math.pi / 2, 0, 0), verts=20, bevel=0)
    _spike("BracketClockSpire", (-0.6, -0.75, z0 + 0.95), 0.2, 0.32, M["iron"], verts=4, rot=(0, 0, math.pi / 4))
    # masks (one bone, one black) leaning on the upper step
    for k, (x, mat) in enumerate(((0.5, bone), (1.15, inkm))):
        s = _mark()
        sphere(f"Mask{k}", 0.32, (0, 0, 0), mat, seg=14, rings=8, scale=(0.85, 0.35, 1.05))
        for sx in (-1, 1):
            sphere(f"MaskEye{k}{sx}", 0.06, (sx * 0.09, -0.08, 0.07), T["hollow"], seg=8, rings=4, scale=(1.2, 0.4, 0.7))
        mouth = [(-0.1, -0.1), (0.1, -0.1), (0.06, -0.15), (-0.06, -0.15)] if k == 0 else [(-0.1, -0.15), (0.1, -0.15), (0.06, -0.1), (-0.06, -0.1)]
        relief(f"MaskMouth{k}", mouth, -0.085, 0.02, T["hollow"], plane="XZ")
        tube(f"MaskRibbon{k}", [(-0.2, 0.02, 0.05), (-0.3, 0.05, -0.15), (-0.28, 0.0, -0.35)], 0.01, M["leather"])
        _xform(s, Matrix.Translation((x, -0.72, z0 + 1.33)) @ Matrix.Rotation(-0.25, 4, "X") @ Matrix.Rotation(0.2 - k * 0.4, 4, "Z"))
    # a skull on old books
    for k in range(3):
        box(f"Book{k}", (0.6 - k * 0.06, 0.4, 0.1), (2.2, -0.75, z0 + 0.19 + k * 0.1), [M["leather"], M["inkblue"], M["leatherdark"]][k], bevel=0.01, rot=(0, 0, 0.1 * k))
    sphere("Skull", 0.17, (2.2, -0.76, z0 + 0.62), bone, seg=14, rings=8, scale=(0.9, 1.05, 0.95))
    sphere("SkullJaw", 0.1, (2.2, -0.88, z0 + 0.5), bone, seg=10, rings=5, scale=(0.9, 0.9, 0.55))
    for sx in (-1, 1):
        sphere(f"SkullEye{sx}", 0.045, (2.2 + sx * 0.065, -0.92, z0 + 0.64), T["hollow"], seg=8, rings=4)
    # a crystal ball on a claw stand
    lathe("BallStand", [(0, 0), (0.14, 0), (0.12, 0.06), (0.06, 0.12), (0.1, 0.18), (0, 0.18)], gilt, seg=16, loc=(3.0, -0.8, z0 + 0.14))
    sphere("CrystalBall", 0.16, (3.0, -0.8, z0 + 0.47), glassy("CrystalViolet", (0.08, 0.03, 0.14)), seg=18, rings=10)
    # candles on brass sticks (the flames are Glow)
    flames = []
    for k, (x, y, z, h) in enumerate(((-0.95, -0.95, z0 + 0.14, 0.5), (3.75, -0.7, z0 + 1.08, 0.35), (4.2, -0.95, z0 + 0.14, 0.6))):
        lathe(f"Stick{k}", [(0, 0), (0.1, 0), (0.08, 0.03), (0.025, 0.06), (0.03, 0.2), (0.06, 0.22), (0, 0.23)], gilt, seg=12, loc=(x, y, z))
        cyl(f"Candle{k}", 0.035, h, (x, y, z + 0.23 + h / 2), T["wax"], verts=10, bevel=0)
        flames.append((x, y, z + 0.23 + h + 0.02))
    # the raven in a domed iron cage, hanging from the arch
    gx, gy, gz = 1.0, -0.85, 3.4
    tube("CageHook", [(gx, gy, 5.9), (gx, gy, gz + 1.25)], 0.012, M["iron"], poly=True)
    hoop("CageFloor", (gx, gy, gz), 0.38, "Z", M["iron"], thick=0.02)
    cyl("CagePan", 0.37, 0.03, (gx, gy, gz + 0.0), M["brass"], verts=24, bevel=0)
    hoop("CageBand", (gx, gy, gz + 0.62), 0.38, "Z", M["iron"], thick=0.015)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        pts = [(gx + math.cos(a) * 0.38, gy + math.sin(a) * 0.38, gz)] + \
              [(gx + math.cos(a) * 0.38 * math.cos(t), gy + math.sin(a) * 0.38 * math.cos(t), gz + 0.75 + 0.42 * math.sin(t)) for t in (0.0, 0.6, 1.1, 1.5)]
        tube(f"CageBar{k}", pts, 0.009, M["iron"])
    sphere("CageTop", 0.05, (gx, gy, gz + 1.18), M["brass"], seg=8, rings=4)
    tube("CagePerch", [(gx - 0.3, gy, gz + 0.25), (gx + 0.3, gy, gz + 0.25)], 0.015, M["brass"], poly=True)
    _raven("CageRaven", Matrix.Translation((gx, gy, gz + 0.26)) @ Matrix.Rotation(-0.4, 4, "Z") @ Matrix.Scale(1.2, 4), T["inkthin"], gilt)
    box("FootLip", (wx1 - wx0 - 0.3, 0.03, 0.16), (cx, -1.17, z0 + 0.22), gilt, bevel=0.006)
    box("PictureHood", (3.5, 0.24, 0.05), (cx, -0.62, 6.58), gilt, bevel=0.008)
    for sx in (-1, 1):
        tube(f"PictureArm{sx}", [(cx + sx * 1.5, -0.45, 6.75), (cx + sx * 1.5, -0.7, 6.6)], 0.012, gilt, poly=True)
    tube("ShopLampChain", [(3.0, -0.95, 7.2), (3.0, -0.95, 6.62)], 0.012, gilt, poly=True)
    lathe("ShopLampHood", [(0, 0), (0.24, 0.0), (0.14, 0.12), (0.04, 0.16), (0, 0.16)], gilt, seg=16, loc=(3.0, -0.95, 6.46))
    set_group("Glow")
    for k, p in enumerate(flames):
        flame(f"CandleFlame{k}", p, h=0.12)
    sphere("ShopLamp", 0.17, (3.0, -0.95, 6.32), M["glassclear"], seg=14, rings=8, scale=(1, 1, 0.9))
    # footlights along the front step (hidden by a brass lip) and a picture light under a hood for the clocks
    box("FootLight", (wx1 - wx0 - 0.4, 0.04, 0.04), (cx, -1.1, z0 + 0.2), M["glassclear"], bevel=0.0, segments=1)
    box("PictureLight", (3.4, 0.04, 0.03), (cx, -0.66, 6.52), M["glassclear"], bevel=0.0, segments=1)
    set_group("Glass")
    relief("Glazing", frame[1:-1] + [(wx1 - 0.02, z0 + 0.12), (wx0 + 0.02, z0 + 0.12)], -1.25, 0.02, M["glassclear"], plane="XZ")
    set_group("Main")
    # the door on the left in a recessed porch with an arched head
    dx0, dx1, dz1 = -4.75, -2.15, 6.6
    for sx, x in ((-1, dx0 - 0.32), (1, dx1 + 0.25)):
        pilaster_iron(f"DoorPil{sx}", x, -0.9, 0.0, 7.75, paint, M, w=0.36)
    box("DoorHead", (dx1 - dx0 + 0.9, 0.7, 7.75 - dz1), ((dx0 + dx1) / 2, -0.8, (7.75 + dz1) / 2), paint, bevel=0.02)
    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        tube(f"DoorFan{k}", [((dx0 + dx1) / 2, -1.16, dz1 + 0.06), ((dx0 + dx1) / 2 + math.cos(a) * 1.1, -1.16, dz1 + 0.06 + math.sin(a) * 0.9)], 0.014, gilt,
             poly=True)
    box("DoorFanGlass", (dx1 - dx0 - 0.1, 0.02, 0.95), ((dx0 + dx1) / 2, -1.15, dz1 + 0.5), T["darkglass"], bevel=0.0, segments=1)
    box("PorchLeft", (0.04, 0.8, dz1), (dx0 - 0.04, -0.8, dz1 / 2), paint, bevel=0.0, segments=1)
    box("PorchRight", (0.04, 0.8, dz1), (dx1 + 0.04, -0.8, dz1 / 2), paint, bevel=0.0, segments=1)
    box("PorchBack", (dx1 - dx0, 0.02, dz1), ((dx0 + dx1) / 2, -0.41, dz1 / 2), T["hollow"], bevel=0.0, segments=1)
    box("PorchFloor", (dx1 - dx0 + 0.6, 1.2, 0.25), ((dx0 + dx1) / 2, -0.95, 0.125), T["stonedark"], bevel=0.03)
    box("PorchTile", (dx1 - dx0 - 0.2, 0.7, 0.02), ((dx0 + dx1) / 2, -0.85, 0.255), M["slate"], bevel=0.005)
    box("CaseBetween", (wx0 - dx1 - 0.6, 0.9, 7.75), ((dx1 + 0.45 + wx0 - 0.15) / 2, -0.85, 7.75 / 2), paint, bevel=0.02)
    _moss("FootMoss", [(-5.2, -1.3, 0.05), (5.2, -1.3, 0.05), (-2.0, -1.45, 0.05)], T["moss"], rnd, 0.1)
    set_group("Door0", hinge=(dx0, -0.6, 0.25), swing=-1)          # hinge on the left edge, opens out toward the street
    panel_door("Door", dx0, dx1, -0.6, 0.25, dz1, paint, dict(M, **T), glazed=True, knob_side=1)
    set_group("Main")
    # three gilt balls on a bracket from the left pier (they sway)
    hx, hz = -5.45, 10.95                     # above the stringcourse, so the balls hang clear of the fascia
    box("BallsPlate", (0.3, 0.06, 0.9), (hx, -0.43, hz - 0.3), M["iron"], bevel=0.01)
    tube("BallsArm", [(hx, -0.43, hz), (hx, -2.3, hz)], 0.03, M["iron"], square=True, poly=True)
    tube("BallsBrace", [(hx, -0.43, hz - 0.7), (hx, -0.9, hz - 0.45), (hx, -1.5, hz - 0.15), (hx, -1.9, hz - 0.02)], 0.022, M["iron"])
    hoop("BallsCurl", (hx, -0.85, hz - 0.22), 0.17, "X", M["iron"], thick=0.016)
    tube("BallsBar", [(hx - 0.5, -2.2, hz - 0.03), (hx + 0.5, -2.2, hz - 0.03)], 0.025, M["iron"], poly=True)
    set_group("Cloth", hinge=(hx, -2.2, hz - 0.03), swing=1)
    tube("BallsHanger", [(hx, -2.2, hz - 0.05), (hx, -2.2, hz - 0.35)], 0.015, M["iron"], poly=True)
    tube("BallsYoke", [(hx - 0.42, -2.2, hz - 0.55), (hx, -2.2, hz - 0.35), (hx + 0.42, -2.2, hz - 0.55)], 0.022, M["iron"], poly=True)
    for k, (bx, bz) in enumerate(((hx - 0.42, hz - 1.0), (hx + 0.42, hz - 1.0), (hx, hz - 1.62))):
        tube(f"BallRod{k}", [(bx if k < 2 else hx, -2.2, hz - 0.55 if k < 2 else hz - 0.35), (bx, -2.2, bz + 0.24)], 0.012, M["iron"], poly=True)
        sphere(f"GiltBall{k}", 0.24, (bx, -2.2, bz), gilt, seg=20, rings=10)
    set_group("Main")
    return dims()


# ================================================================== market stall
def market_stall(M):
    T = town()
    rnd = random.Random(113)
    iron, gilt = M["iron"], M["brass"]
    X, YF, YB = 3.0, -1.45, 1.35
    ZF, ZB = 4.35, 5.15                          # awning front and back heights
    for sx in (-1, 1):
        for y, z in ((YF, ZF), (YB, ZB)):
            x = sx * X
            lathe(f"PostFoot{sx}{y}", [(0, 0), (0.16, 0), (0.16, 0.08), (0.1, 0.14), (0.07, 0.3), (0, 0.3)], iron, seg=12, loc=(x, y, 0))
            cyl(f"Post{sx}{y}", 0.055, z - 0.3, (x, y, 0.3 + (z - 0.3) / 2), iron, verts=10, bevel=0)
            hoop(f"PostCollar{sx}{y}", (x, y, z - 0.25), 0.07, "Z", gilt, thick=0.018)
            hoop(f"PostCollarLow{sx}{y}", (x, y, 1.0), 0.065, "Z", gilt, thick=0.016)
        tube(f"SideRail{sx}", [(sx * X, YF, ZF - 0.05), (sx * X, YB, ZB - 0.05)], 0.035, iron, poly=True)
        tube(f"SideRailLow{sx}", [(sx * X, YF, 0.6), (sx * X, YB, 0.6)], 0.03, iron, poly=True)
        for y, z in ((YF, ZF), (YB, ZB)):
            tube(f"Scroll{sx}{y}", [(sx * X, y, z - 0.9), (sx * (X - 0.18), y, z - 0.6), (sx * (X - 0.4), y, z - 0.25), (sx * (X - 0.62), y, z - 0.05)], 0.022, iron)
            hoop(f"ScrollCurl{sx}{y}", (sx * (X - 0.2), y, z - 0.38), 0.09, "Y", iron, thick=0.014)
    tube("FrontRail", [(-X, YF, ZF - 0.05), (X, YF, ZF - 0.05)], 0.035, iron, poly=True)
    tube("BackRail", [(-X, YB, ZB - 0.05), (X, YB, ZB - 0.05)], 0.035, iron, poly=True)
    # the canvas: stripes running front to back with a little sag, crimson and black
    NS = 10
    for k in range(NS):
        xa, xb = -X - 0.1 + k * (2 * X + 0.2) / NS, -X - 0.1 + (k + 1) * (2 * X + 0.2) / NS
        rows = []
        for i in range(9):
            t = i / 8
            y = YB + 0.08 + (YF - 0.06 - YB - 0.08) * t
            z = ZB + 0.02 + (ZF - ZB) * t - 0.14 * math.sin(t * math.pi)
            rows.append([Vector((xa + (xb - xa) * j / 2, y, z - 0.05 * math.sin((j / 2) * math.pi))) for j in range(3)])
        _mesh(f"Stripe{k}", rows, T["canvasred"] if k % 2 == 0 else T["canvasblack"], 0.025)
    # the counter: an iron frame, a slate top, an oxblood apron with brass studs
    for sx in (-1, 1):
        for y in (-1.25, -0.35):
            cyl(f"CounterLeg{sx}{y}", 0.04, 2.5, (sx * 2.75, y, 1.25), iron, verts=8, bevel=0)
    box("CounterTop", (5.8, 1.05, 0.1), (0, -0.8, 2.55), M["slate"], bevel=0.02)
    box("Apron", (5.7, 0.06, 0.55), (0, -1.33, 2.22), T["oxblood"], bevel=0.015)
    for k in range(11):
        sphere(f"ApronStud{k}", 0.03, (-2.6 + k * 0.52, -1.37, 2.22), gilt, seg=6, rings=3)
    box("ApronTrim", (5.75, 0.05, 0.05), (0, -1.37, 2.48), gilt, bevel=0.008)
    box("UnderShelf", (5.6, 0.95, 0.06), (0, -0.8, 0.65), iron, bevel=0.01)
    # the goods are their own piece (crates of apples, a basket of turnips, the scale, jars, pumpkins)
    set_group("Goods")
    # crates of apples on the counter
    red, green = flat("Apple", (0.24, 0.02, 0.02), 0.35, dirt=0.4), flat("AppleGreen", (0.12, 0.2, 0.03), 0.4, dirt=0.4)
    for c, (cx, cy) in enumerate(((-1.8, -0.8), (-0.4, -0.85))):
        crate(f"Crate{c}", cx, cy, 2.6, 1.1, 0.8, 0.35, T, M, open_top=True, rot=0.04 * (c - 0.5))
        for i in range(18):
            a = rnd.uniform(0, 6.28)
            rr = rnd.uniform(0, 0.36)
            sphere(f"Apple{c}_{i}", 0.09, (cx + math.cos(a) * rr * 1.2, cy + math.sin(a) * rr * 0.75, 2.9 + rnd.uniform(0, 0.12)), red if (i + c) % 4 else green,
                   seg=10, rings=6, scale=(1, 1, 0.9))
    # a basket of turnips and a brass scale
    lathe("Basket", [(0, 0), (0.3, 0), (0.42, 0.28), (0.4, 0.3), (0.28, 0.04), (0, 0.04)], T["burlap"], seg=20, loc=(1.0, -0.8, 2.6), flute=(16, 0.04))
    for i in range(6):
        sphere(f"Turnip{i}", 0.1, (1.0 + rnd.uniform(-0.2, 0.2), -0.8 + rnd.uniform(-0.15, 0.15), 2.9), T["bone"], seg=10, rings=6, scale=(1, 1, 0.85))
    tube("ScaleHook", [(2.2, YF, ZF - 0.08), (2.2, YF, ZF - 0.45)], 0.012, gilt, poly=True)
    tube("ScaleBeam", [(1.85, YF, ZF - 0.45), (2.55, YF, ZF - 0.45)], 0.02, gilt, poly=True)
    for sx in (-1, 1):
        x = 2.2 + sx * 0.33
        for j in range(3):
            a = j / 3 * 2 * math.pi
            tube(f"ScaleString{sx}{j}", [(x, YF, ZF - 0.45), (x + math.cos(a) * 0.13, YF + math.sin(a) * 0.13, ZF - 0.95)], 0.005, gilt, poly=True)
        lathe(f"ScalePan{sx}", [(0, 0), (0.15, 0.04), (0.16, 0.06), (0, 0.02)], gilt, seg=16, loc=(x, YF, ZF - 1.0))
    set_group("Stand")
    # a stepped stand of jars at the back
    for k, (y, z) in enumerate(((0.55, 1.4), (0.95, 1.95))):
        box(f"Tier{k}", (5.0, 0.42, 0.06), (0, y, z), M["slate"], bevel=0.01)
        for sx in (-1, 1):
            box(f"TierLeg{k}{sx}", (0.05, 0.05, z), (sx * 2.4, y, z / 2), iron, bevel=0.005)
        x = -2.3
        j = 0
        while x < 2.3:
            r = rnd.uniform(0.1, 0.14)
            h = rnd.uniform(0.26, 0.4)
            lathe(f"Jar{k}_{j}", [(0, 0), (r, 0), (r, h * 0.82), (r * 0.8, h * 0.9), (r * 0.8, h), (0, h)], glassy(f"JarGlass{k}{j % 3}", [(0.28, 0.12, 0.02), (0.18, 0.03, 0.02), (0.06, 0.12, 0.03)][j % 3]),
                  seg=12, loc=(x + r, y, z + 0.03))
            cyl(f"JarLid{k}_{j}", r * 0.95, 0.05, (x + r, y, z + 0.03 + h + 0.025), M["paper"] if j % 2 else T["canvasred"], verts=12, bevel=0.005)
            x += 2 * r + 0.08
            j += 1
    # pumpkins in a crate on the ground, front left
    crate("PumpkinCrate", -2.0, -2.15, 0.0, 1.3, 0.95, 0.5, T, M, open_top=True, rot=0.15)
    orange = flat("Pumpkin", (0.24, 0.05, 0.004), 0.6, dirt=0.75)
    darkp = flat("PumpkinDark", (0.12, 0.06, 0.03), 0.6, dirt=0.6)
    for i, (px, py, pz, r) in enumerate(((-2.3, -2.2, 0.2, 0.3), (-1.75, -2.05, 0.2, 0.27), (-2.05, -2.2, 0.55, 0.24), (-1.0, -2.65, 0.0, 0.36))):
        lathe(f"Pumpkin{i}", [(0, 0), (r * 0.6, r * 0.05), (r, r * 0.45), (r * 0.95, r * 0.9), (r * 0.5, r * 1.2), (0, r * 1.15)], orange if i != 2 else darkp,
              seg=24, loc=(px, py, pz), flute=(8, 0.12))
        tube(f"PumpkinStalk{i}", [(px, py, pz + r * 1.12), (px + 0.03, py, pz + r * 1.35)], 0.035, flat("Stalk", (0.06, 0.05, 0.02), 0.8), poly=True)
    set_group("Main")
    # a lantern hanging from the front rail
    lanterns = []
    tube("LanternHook", [(-2.6, YF, ZF - 0.08), (-2.6, YF, ZF - 0.32)], 0.012, iron, poly=True)
    _lantern("Lantern", Matrix.Translation((-2.6, YF, ZF - 1.05)), M, lanterns, T["wax"])
    _lights(lanterns, M)
    # the scalloped valance along the front, which sways about the front rail
    set_group("Cloth", hinge=(0, YF - 0.08, ZF - 0.02), swing=1)
    for k in range(NS):
        xa, xb = -X - 0.1 + k * (2 * X + 0.2) / NS, -X - 0.1 + (k + 1) * (2 * X + 0.2) / NS
        xm, hw = (xa + xb) / 2, (xb - xa) / 2
        poly = [(xa, ZF + 0.02), (xb, ZF + 0.02), (xb, ZF - 0.42)] + [(xm + math.cos(-i / 8 * math.pi) * hw, ZF - 0.42 + math.sin(-i / 8 * math.pi) * 0.2)
                                                                    for i in range(1, 8)] + [(xa, ZF - 0.42)]
        prism(f"Valance{k}", poly, YF - 0.09, 0.025, T["canvasred"] if k % 2 == 0 else T["canvasblack"], plane="XZ")
    tube("ValanceTrim", [(-X - 0.1, YF - 0.11, ZF - 0.12), (X + 0.1, YF - 0.11, ZF - 0.12)], 0.014, gilt, poly=True)
    set_group("Main")
    return dims()


def crate(prefix, cx, cy, z, w, d, h, T, M, open_top=False, rot=0.0):
    """An iron-cornered slatted crate standing at z (centre cx, cy)."""
    s = _mark()
    b = T["boards"]
    ns = 3
    for face in (-1, 1):
        for k in range(ns):
            zz = h * (k + 0.5) / ns
            box(f"{prefix}SlatX{face}{k}", (w, 0.04, h / ns - 0.03), (0, face * (d / 2 - 0.02), zz), b, bevel=0.008)
            box(f"{prefix}SlatY{face}{k}", (0.04, d - 0.08, h / ns - 0.03), (face * (w / 2 - 0.02), 0, zz), b, bevel=0.008)
    box(f"{prefix}Floor", (w - 0.08, d - 0.08, 0.04), (0, 0, 0.03), b, bevel=0.005)
    if not open_top:
        for k in range(4):
            box(f"{prefix}Lid{k}", ((w - 0.02) / 4 - 0.02, d, 0.04), (-w / 2 + (k + 0.5) * w / 4, 0, h + 0.02), b, bevel=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"{prefix}Corner{sx}{sy}", (0.08, 0.08, h + 0.02), (sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2), M["iron"], bevel=0.008)
    for face in (-1, 1):
        box(f"{prefix}Strap{face}", (w + 0.01, 0.015, 0.06), (0, face * (d / 2 + 0.002), h * 0.5), M["iron"], bevel=0.004)
    _xform(s, Matrix.Translation((cx, cy, z)) @ Matrix.Rotation(rot, 4, "Z"))


# ================================================================== hanging sign
def hanging_sign(M):
    T = town()
    iron, gilt = M["iron"], M["brass"]
    zr, yr = 2.25, -1.55                       # crossbar height and distance from the wall
    box("WallPlate", (0.34, 0.06, 1.3), (0, -0.03, zr - 0.5), iron, bevel=0.012)
    for k, z in enumerate((zr - 1.05, zr + 0.05)):
        sphere(f"Bolt{k}", 0.035, (0, -0.07, z), gilt, seg=8, rings=4)
    tube("Arm", [(0, -0.06, zr + 0.08), (0, yr - 0.25, zr + 0.08)], 0.035, iron, square=True, poly=True)
    cone("ArmFinial", 0.06, 0.0, 0.22, (0, yr - 0.36, zr + 0.08), iron, verts=6, rot=(math.pi / 2, 0, 0))
    tube("Brace", [(0, -0.06, zr - 0.95), (0, -0.35, zr - 0.7), (0, -0.75, zr - 0.3), (0, -1.15, zr + 0.0), (0, -1.35, zr + 0.06)], 0.026, iron)
    for k, (y, z, r) in enumerate(((-0.42, zr - 0.27, 0.3), (-0.88, zr - 0.06, 0.12))):
        hoop(f"Curl{k}", (0, y, z), r, "X", iron, thick=0.018)
        sphere(f"CurlBoss{k}", 0.035, (0, y, z), gilt, seg=8, rings=4)
    tube("Crossbar", [(-0.7, yr, zr), (0.7, yr, zr)], 0.03, iron, poly=True)
    tube("CrossbarHanger", [(0, yr, zr), (0, yr, zr + 0.08)], 0.03, iron, poly=True)
    for sx in (-1, 1):
        sphere(f"CrossKnob{sx}", 0.05, (sx * 0.72, yr, zr), gilt, seg=8, rings=4)
    set_group("Cloth", hinge=(0, yr, zr), swing=1)
    hanging_board("Sign", 0.0, yr, zr, 1.3, 1.05, T["signred"], gilt, M, T, mark="moon")
    set_group("Main")
    return dims()


# ================================================================== postbox
def postbox(M):
    T = town()
    rnd = random.Random(115)
    red, gilt, iron = T["oxblood"], M["brass"], M["iron"]
    s = _mark()
    lathe("Base", [(0, 0), (0.82, 0), (0.82, 0.18), (0.74, 0.26), (0.7, 0.42), (0, 0.42)], red, seg=8)
    lathe("Body", [(0, 0.4), (0.64, 0.4), (0.64, 3.35), (0, 3.35)], red, seg=8)
    lathe("Band", [(0, 3.3), (0.7, 3.3), (0.72, 3.4), (0.7, 3.5), (0, 3.5)], red, seg=8)
    lathe("Cornice", [(0, 3.5), (0.78, 3.5), (0.8, 3.62), (0, 3.62)], red, seg=8)
    lathe("Roof", [(0, 3.62), (0.66, 3.62), (0.5, 3.9), (0.22, 4.25), (0.1, 4.45), (0, 4.45)], red, seg=8)
    _xform(s, Matrix.Rotation(math.pi / 8, 4, "Z"))
    r_face = 0.64 * math.cos(math.pi / 8)              # distance to a flat face
    # gothic crown: a little gable over every face, a crocketed spire in the middle, a ball finial
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        m0 = _mark()
        hw = 0.3
        prism(f"Gable{k}", [(-hw, 0.0), (hw, 0.0), (0.0, 0.42)], 0.0, 0.08, red, plane="XZ")
        _foil(f"GableFoil{k}", 0.0, -0.05, 0.14, 0.08, gilt, lobes=3, thick=0.012)
        _crockets(f"GableCrocket{k}", [(-hw * 0.5, -0.0, 0.26), (hw * 0.5, 0.0, 0.26)], red, size=0.04)
        _xform(m0, Matrix.Translation((c * 0.74 * math.cos(math.pi / 8), s_ * 0.74 * math.cos(math.pi / 8), 3.62)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
        bx, by = math.cos(a + math.pi / 8) * 0.8, math.sin(a + math.pi / 8) * 0.8
        _spike(f"CornerPin{k}", (bx, by, 3.75), 0.04, 0.26, red, verts=4)
    _crockets("SpireCrocket", [(math.cos(k * math.pi / 2 + 0.4) * (0.42 - 0.1 * j), math.sin(k * math.pi / 2 + 0.4) * (0.42 - 0.1 * j), 3.82 + 0.2 * j)
                               for k in range(4) for j in range(2)], red, size=0.045)
    sphere("Finial", 0.1, (0, 0, 4.58), gilt, seg=12, rings=6)
    _spike("FinialSpike", (0, 0, 4.8), 0.03, 0.26, gilt, verts=6)
    # the front: a hooded slot, a crest, a blank times plate, a door bead with a keyhole
    yf = -r_face
    box("SlotHood", (0.66, 0.16, 0.08), (0, yf - 0.07, 2.96), red, bevel=0.02, rot=(0.25, 0, 0))
    box("Slot", (0.5, 0.03, 0.06), (0, yf - 0.006, 2.85), T["hollow"], bevel=0.0, segments=1)
    box("SlotLip", (0.56, 0.05, 0.03), (0, yf - 0.02, 2.8), gilt, bevel=0.006)
    shield = [(-0.17, 2.6), (0.17, 2.6), (0.17, 2.4), (0.1, 2.27), (0.0, 2.2), (-0.1, 2.27), (-0.17, 2.4)]
    relief("Crest", shield, yf - 0.02, 0.04, gilt, plane="XZ", bevel=0.0)
    relief("CrestField", [(x * 0.78, 2.4 + (z - 2.4) * 0.8) for x, z in shield], yf - 0.04, 0.02, T["inkthin"], plane="XZ")
    _spike("CrestStar", (0, yf - 0.06, 2.43), 0.05, 0.02, gilt, verts=5, rot=(math.pi / 2, 0, 0))
    box("Plate", (0.44, 0.02, 0.28), (0, yf - 0.012, 1.95), T["bone"], bevel=0.008)
    for k in range(3):
        box(f"PlateBar{k}", (0.32 - k * 0.06, 0.01, 0.025), (0, yf - 0.024, 2.02 - k * 0.07), T["inkthin"], bevel=0.0, segments=1)
    tube("DoorBead", [(-0.2, yf - 0.012, 0.75), (0.2, yf - 0.012, 0.75), (0.2, yf - 0.012, 1.7), (-0.2, yf - 0.012, 1.7)], 0.012, red, closed=True, square=True, poly=True)
    box("Keyhole", (0.06, 0.02, 0.1), (0.0, yf - 0.012, 1.3), gilt, bevel=0.005)
    # lancet panels on the other faces
    for k in range(1, 8):
        a = -math.pi / 2 + k * math.pi / 4
        m0 = _mark()
        _lancet(f"Panel{k}", 0.0, 0.0, 0.8, 0.17, 2.4, 2.75, red, thick=0.02, cusp=k % 2 == 0)
        _xform(m0, Matrix.Translation((math.cos(a) * (r_face + 0.005), math.sin(a) * (r_face + 0.005), 0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    return dims()


# ================================================================== street pump
def street_pump(M):
    T = town()
    rnd = random.Random(116)
    iron, gilt = M["iron"], M["brass"]
    stone, dark = T["stone"], T["stonedark"]
    py = 0.75                                   # the column stands behind the trough
    box("Plinth", (1.1, 1.1, 0.4), (0, py, 0.2), stone, bevel=0.05)
    lathe("ColumnBase", [(0, 0.4), (0.44, 0.4), (0.44, 0.55), (0.36, 0.65), (0.36, 0.78), (0.3, 0.9), (0, 0.9)], iron, seg=24, loc=(0, py, 0))
    lathe("Shaft", [(0, 0.9), (0.27, 0.9), (0.25, 3.2), (0, 3.2)], iron, seg=32, loc=(0, py, 0), flute=(12, 0.07))
    for k, z in enumerate((1.1, 2.35, 3.2)):
        hoop(f"Collar{k}", (0, py, z), 0.29, "Z", gilt if k == 1 else iron, thick=0.035)
    lathe("Capital", [(0, 3.2), (0.3, 3.2), (0.38, 3.35), (0.4, 3.5), (0.32, 3.55), (0.32, 3.7), (0, 3.7)], iron, seg=24, loc=(0, py, 0))
    lathe("Dome", [(0, 3.7), (0.34, 3.7), (0.3, 3.9), (0.18, 4.08), (0.06, 4.18), (0, 4.2)], iron, seg=24, loc=(0, py, 0), flute=(8, 0.08))
    lathe("Acorn", [(0, 4.18), (0.08, 4.22), (0.1, 4.32), (0.07, 4.44), (0, 4.5)], gilt, seg=12, loc=(0, py, 0))
    # the spout: a grotesque head on the front, water pouring from its mouth into the trough
    mouth = _grotesque("Spout", Matrix.Translation((0, py - 0.4, 2.15)) @ Matrix.Scale(1.05, 4), iron, T["hollow"])
    cyl("SpoutPipe", 0.05, 0.3, (0, mouth.y - 0.05, mouth.z - 0.01), iron, rot=(math.pi / 2, 0, 0), verts=10, bevel=0)
    # the lever handle on the right, pivoting at the capital
    box("PivotBoss", (0.16, 0.2, 0.2), (0.36, py, 3.4), iron, bevel=0.02)
    tube("Handle", [(0.38, py, 3.42), (0.75, py - 0.05, 3.35), (1.05, py - 0.1, 2.95), (1.15, py - 0.12, 2.35)], 0.04, iron)
    lathe("HandleGrip", [(0, 0), (0.06, 0.0), (0.07, 0.15), (0.05, 0.3), (0, 0.32)], gilt, seg=10, loc=(1.15, py - 0.12, 2.05))
    # the trough: stone walls round a basin, moss on the rim, an iron grate for buckets
    tw, td, th, wall = 2.2, 1.15, 0.95, 0.16
    ty = -0.3
    box("TroughFloor", (tw, td, 0.2), (0, ty, 0.1), dark, bevel=0.03)
    for sx in (-1, 1):
        box(f"TroughEnd{sx}", (wall, td, th), (sx * (tw / 2 - wall / 2), ty, th / 2), stone, bevel=0.04)
    for sy in (-1, 1):
        box(f"TroughSide{sy}", (tw - 2 * wall, wall, th), (0, ty + sy * (td / 2 - wall / 2), th / 2), stone, bevel=0.04)
    box("TroughLip", (tw + 0.08, 0.1, 0.08), (0, ty - td / 2 + 0.04, th + 0.02), dark, bevel=0.02)
    box("TroughInside", (tw - 2 * wall, td - 2 * wall, 0.02), (0, ty, 0.21), T["hollow"], bevel=0.0, segments=1)
    for k in range(5):
        tube(f"Grate{k}", [(0.35 + k * 0.1, ty - 0.3, th + 0.04), (0.35 + k * 0.1, ty + 0.3, th + 0.04)], 0.015, iron, poly=True)
    soot, grime = soot_mats()
    grime_band("TroughGrime", -tw / 2 + 0.02, tw / 2 - 0.02, ty - td / 2 - 0.004, 0.0, 0.32, grime, rnd)
    for k in range(3):
        soot_streak(f"TroughStreak{k}", -0.7 + k * 0.6 + rnd.uniform(-0.1, 0.1), ty - td / 2 - 0.006, th - 0.02, rnd.uniform(0.3, 0.6), 0.1, grime, rnd)
    _moss("RimMoss", [(rnd.uniform(-1.0, 1.0), ty + rnd.choice((-1, 1)) * 0.5, th) for _ in range(5)], T["moss"], rnd, 0.07)
    set_group("Pool")
    box("Water", (tw - 2 * wall - 0.02, td - 2 * wall - 0.02, 0.03), (0, ty, th - 0.2), T["water"], bevel=0.0, segments=1)
    tube("Trickle", [(0, mouth.y - 0.12, mouth.z - 0.03), (0, mouth.y - 0.2, mouth.z - 0.35), (0, mouth.y - 0.22, th - 0.18)], 0.025, T["water"])
    set_group("Main")
    return dims()


# ================================================================== news kiosk
def news_kiosk(M):
    T = town()
    rnd = random.Random(117)
    iron, gilt, paint = M["iron"], M["brass"], T["green"]
    R = 1.55
    s = _mark()
    lathe("Plinth", [(0, 0), (R + 0.25, 0), (R + 0.25, 0.3), (R + 0.15, 0.4), (0, 0.4)], T["stonedark"], seg=8)
    lathe("Body", [(0, 0.4), (R, 0.4), (R, 5.0), (0, 5.0)], paint, seg=8)
    lathe("Cornice", [(0, 5.0), (R + 0.1, 5.0), (R + 0.28, 5.15), (R + 0.32, 5.3), (0, 5.3)], paint, seg=8)
    lathe("Dome", [(0, 5.3), (R + 0.05, 5.3), (R - 0.1, 5.6), (R * 0.65, 5.9), (R * 0.35, 6.2), (0.12, 6.4), (0, 6.42)], M["slate"], seg=8)
    _xform(s, Matrix.Rotation(math.pi / 8, 4, "Z"))
    rf = R * math.cos(math.pi / 8)
    lathe("FinialBase", [(0, 6.38), (0.12, 6.4), (0.1, 6.55), (0, 6.6)], gilt, seg=12)
    tube("FinialRod", [(0, 0, 6.55), (0, 0, 7.05)], 0.025, gilt, poly=True)
    mm = _mark()
    n = 16
    outer = [(math.cos(math.pi * 0.2 + i / n * math.pi * 1.6) * 0.2, 7.2 + math.sin(math.pi * 0.2 + i / n * math.pi * 1.6) * 0.2) for i in range(n + 1)]
    inner = [(0.08 + math.cos(math.pi * 1.8 - i / n * math.pi * 1.6) * 0.16, 7.23 + math.sin(math.pi * 1.8 - i / n * math.pi * 1.6) * 0.16) for i in range(n + 1)]
    relief("FinialMoon", outer + inner[1:-1], 0.0, 0.04, gilt, plane="XZ")
    _xform(mm, Matrix.Rotation(0.0, 4, "Z"))
    # corner posts and the serving window on the front face
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8 - math.pi / 8
        vx, vy = math.cos(a + math.pi / 8) * (R + 0.01), math.sin(a + math.pi / 8) * (R + 0.01)
        tube(f"Post{k}", [(vx, vy, 0.4), (vx, vy, 5.0)], 0.05, iron, square=True, poly=True)
        sphere(f"PostCap{k}", 0.06, (vx, vy, 5.02), gilt, seg=8, rings=4)
    posters = [flat("PosterOchre", (0.42, 0.3, 0.12), 0.8, dirt=0.8), flat("PosterBone", (0.6, 0.56, 0.46), 0.8, dirt=0.8),
               flat("PosterRed", (0.28, 0.03, 0.03), 0.8, dirt=0.8), flat("PosterTeal", (0.04, 0.12, 0.12), 0.8, dirt=0.8)]
    ink = T["inkthin"]
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        m0 = _mark()
        w = 2 * R * math.sin(math.pi / 8) - 0.14
        # lower panel: a traceried lancet in relief, a brass rosette
        _lancet(f"LowArch{k}", 0.0, -0.01, 0.65, w / 2 - 0.12, 1.9, 2.35, iron, thick=0.025)
        sphere(f"Rosette{k}", 0.05, (0.0, -0.03, 1.4), gilt, seg=8, rings=4)
        box(f"Rail{k}", (w, 0.05, 0.08), (0, -0.02, 2.55), gilt, bevel=0.008)
        if k == 0:
            # the serving window: a dark opening, a counter, stacked and fanned papers, a little awning
            box("Opening", (w - 0.1, 0.02, 1.6), (0, -0.005, 3.5), T["hollow"], bevel=0.0, segments=1)
            box("Counter", (w + 0.1, 0.42, 0.07), (0, -0.2, 2.62), M["slate"], bevel=0.01)
            for j in range(4):
                box(f"Papers{j}", (0.34, 0.26, 0.05 * (4 - j)), (-0.32 + j * 0.22, -0.2, 2.66 + 0.025 * (4 - j)), M["paper"], bevel=0.004, rot=(0, 0, 0.1 * j - 0.15))
            box("Awning", (w + 0.1, 0.4, 0.04), (0, -0.2, 4.4), T["canvasred"], bevel=0.005, rot=(0.25, 0, 0))
            box("PaperRack", (w - 0.2, 0.05, 0.05), (0, -0.04, 4.15), iron, bevel=0.005)
            for j in range(3):
                box(f"HungPaper{j}", (0.3, 0.015, 0.42), (-0.35 + j * 0.35, -0.06, 3.92), M["paper"], bevel=0.0, segments=1)
                for b in range(3):
                    box(f"HungPaperLine{j}{b}", (0.22, 0.01, 0.025), (-0.35 + j * 0.35, -0.07, 4.04 - b * 0.08), ink, bevel=0.0, segments=1)
        else:
            # posters: a coloured sheet, an icon, rows of unreadable print
            pm = posters[k % 4]
            box(f"Poster{k}", (w - 0.12, 0.012, 1.7), (0, -0.008, 3.75), pm, bevel=0.0, segments=1)
            box(f"PosterFrame{k}", (w - 0.06, 0.008, 1.76), (0, -0.002, 3.75), ink, bevel=0.0, segments=1)
            icon = k % 4
            iy = -0.02
            if icon == 0:
                relief(f"Icon{k}", [(math.cos(i / 14 * 2 * math.pi) * 0.22, 4.15 + math.sin(i / 14 * 2 * math.pi) * 0.22) for i in range(14)], iy, 0.01, ink, plane="XZ")
                relief(f"IconCut{k}", [(0.08 + math.cos(i / 14 * 2 * math.pi) * 0.19, 4.2 + math.sin(i / 14 * 2 * math.pi) * 0.19) for i in range(14)], iy - 0.004, 0.01, pm, plane="XZ")
            elif icon == 1:
                relief(f"Icon{k}", [(-0.25, 3.95), (0.0, 4.05), (0.25, 3.95), (0.12, 4.15), (0.05, 4.35), (-0.05, 4.35), (-0.12, 4.15)], iy, 0.01, ink, plane="XZ")
            elif icon == 2:
                relief(f"Icon{k}", [(-0.2, 4.35), (0.2, 4.35), (0.18, 4.1), (0.0, 3.92), (-0.18, 4.1)], iy, 0.01, ink, plane="XZ")
                for sx in (-1, 1):
                    box(f"IconEye{k}{sx}", (0.07, 0.01, 0.04), (sx * 0.08, iy - 0.006, 4.2), pm, bevel=0.0, segments=1)
            else:
                relief(f"Icon{k}", [(math.cos(i / 10 * 2 * math.pi + math.pi / 2) * (0.24 if i % 2 == 0 else 0.1), 4.15 + math.sin(i / 10 * 2 * math.pi + math.pi / 2) * (0.24 if i % 2 == 0 else 0.1))
                                    for i in range(10)], iy, 0.01, ink, plane="XZ")
            for b in range(5):
                box(f"Print{k}{b}", (w - 0.3 - (b % 2) * 0.12, 0.008, 0.04), (0, -0.016, 3.65 - b * 0.12), ink, bevel=0.0, segments=1)
            box(f"PrintHead{k}", (w - 0.25, 0.008, 0.1), (0, -0.016, 3.83), ink, bevel=0.0, segments=1)
            if rnd.random() < 0.5:
                box(f"Torn{k}", (0.2, 0.014, 0.18), (rnd.uniform(-0.2, 0.2), -0.01, 2.98), paint, bevel=0.0, segments=1, rot=(0, 0.4, 0))
        _xform(m0, Matrix.Translation((math.cos(a) * rf, math.sin(a) * rf, 0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    # a lantern on a scrolled bracket from the front-left post
    lanterns = []
    a = -math.pi / 2 - math.pi / 8
    px, py = math.cos(a) * (R + 0.01), math.sin(a) * (R + 0.01)
    ox, oy = px + math.cos(a) * 0.55, py + math.sin(a) * 0.55
    tube("LampArm", [(px, py, 4.95), (ox, oy, 4.95)], 0.03, iron, square=True, poly=True)
    tube("LampBrace", [(px, py, 4.45), ((px + ox) / 2, (py + oy) / 2, 4.65), (ox * 0.95 + px * 0.05, oy * 0.95 + py * 0.05, 4.93)], 0.02, iron)
    tube("LampDrop", [(ox, oy, 4.95), (ox, oy, 4.78)], 0.012, iron, poly=True)
    _lantern("Lamp", Matrix.Translation((ox, oy, 4.05)) @ Matrix.Rotation(a, 4, "Z"), M, lanterns, T["wax"])
    _lights(lanterns, M)
    _moss("FootMoss", [(math.cos(t) * (R + 0.22), math.sin(t) * (R + 0.22), 0.38) for t in (0.6, 2.2, 3.7, 5.2)], T["moss"], rnd, 0.08)
    return dims()


# ================================================================== telephone booth
def telephone_booth(M):
    T = town()
    paint, gilt, iron = T["ink"], M["brass"], M["iron"]
    S, Z0, ZE = 1.25, 0.3, 6.3              # half size, floor, eaves
    hw = S - 0.17                            # half width of a side between the posts
    ZL = Z0 + 1.7                            # top of the solid lower band
    zs, za = 5.05, 5.85                      # the window head: springing, apex
    box("Plinth", (2 * S + 0.6, 2 * S + 0.6, Z0), (0, 0, Z0 / 2), T["stonedark"], bevel=0.04)
    box("Floor", (2 * S, 2 * S, 0.06), (0, 0, Z0 + 0.03), M["slate"], bevel=0.01)
    # solid cast-iron corner posts: a base block, a shaft with a colonette on the outer corner, brass bands, a capital
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * S, sy * S
            box(f"PostBase{sx}{sy}", (0.5, 0.5, 0.7), (x, y, Z0 + 0.35), paint, bevel=0.03)
            box(f"Post{sx}{sy}", (0.36, 0.36, ZE - Z0 - 0.7), (x, y, (Z0 + 0.7 + ZE) / 2), paint, bevel=0.025)
            cyl(f"Colonette{sx}{sy}", 0.075, ZE - Z0 - 1.2, (x + sx * 0.16, y + sy * 0.16, (Z0 + 0.85 + ZE - 0.35) / 2), paint, verts=12, bevel=0)
            for k, z in enumerate((Z0 + 0.9, ZL + 0.05, ZE - 0.35)):
                box(f"PostBand{sx}{sy}{k}", (0.42, 0.42, 0.07), (x, y, z), gilt, bevel=0.01)
            box(f"PostCap{sx}{sy}", (0.46, 0.46, 0.22), (x, y, ZE - 0.11), paint, bevel=0.03)
    # every side: a solid lower band, then a glazed panel with a pointed head, a mullion, transoms and tracery;
    # the front side is the door
    sides = []
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        m0 = _mark()
        box(f"Lower{k}", (2 * hw, 0.1, ZL - Z0), (0, 0, (Z0 + ZL) / 2), paint, bevel=0.015)
        tube(f"LowerFrame{k}", [(-hw + 0.12, -0.06, Z0 + 0.15), (hw - 0.12, -0.06, Z0 + 0.15), (hw - 0.12, -0.06, ZL - 0.15), (-hw + 0.12, -0.06, ZL - 0.15)],
             0.025, paint, closed=True, square=True, poly=True)
        _foil(f"LowerFoil{k}", 0, -0.07, (Z0 + ZL) / 2 + 0.1, 0.3, gilt, lobes=4, thick=0.022)
        sphere(f"LowerBoss{k}", 0.07, (0, -0.08, (Z0 + ZL) / 2 + 0.1), gilt, seg=10, rings=5)
        box(f"Rail{k}", (2 * hw, 0.18, 0.14), (0, 0, ZL + 0.07), paint, bevel=0.02)
        z1 = ZL + 0.14
        head = _pointed(hw - 0.06, zs, za, 12)
        pts = [(-hw + 0.06, 0, z1)] + [(x, 0, z) for x, z in head] + [(hw - 0.06, 0, z1)]
        tube(f"Frame{k}", pts, 0.075, paint, closed=True, square=True, poly=True)
        tube(f"Mullion{k}", [(0, -0.01, z1), (0, -0.01, zs + 0.32)], 0.04, paint, square=True, poly=True)
        for j, z in enumerate((z1 + (zs - z1) * 0.55,)):
            tube(f"Transom{k}{j}", [(-hw + 0.06, -0.01, z), (hw - 0.06, -0.01, z)], 0.035, paint, square=True, poly=True)
        for sx in (-1, 1):
            _lancet(f"HeadLight{k}{sx}", sx * (hw - 0.06) / 2, -0.01, zs - 0.05, (hw - 0.06) / 2 - 0.06, zs + 0.08, zs + 0.45, paint, thick=0.03, cusp=False)
        _foil(f"HeadFoil{k}", 0, -0.01, zs + 0.56, 0.12, paint, lobes=4, thick=0.025)
        sp = [(-hw, ZE - 0.35), (-hw, zs)] + [p for p in head if p[0] <= 1e-6] + [(0, ZE - 0.35)]
        relief(f"SpandrelL{k}", sp, 0.0, 0.08, paint, plane="XZ")
        relief(f"SpandrelR{k}", [(-x, z) for x, z in reversed(sp)], 0.0, 0.08, paint, plane="XZ")
        box(f"Frieze{k}", (2 * hw, 0.16, 0.35), (0, 0, ZE - 0.175), paint, bevel=0.015)
        for j in (-1, 0, 1):
            _foil(f"FriezeFoil{k}{j}", j * 0.6, -0.09, ZE - 0.175, 0.1, gilt, lobes=4, thick=0.014)
        if k == 0:
            # the door: heavier stiles, the hinge gap and knuckles on the left, a kick plate, a push plate and pull
            for sx in (-1, 1):
                box(f"DoorStile{sx}", (0.1, 0.14, ZE - 0.45 - Z0), (sx * (hw - 0.05), -0.02, (Z0 + ZE - 0.45) / 2), paint, bevel=0.012)
            box("DoorGap", (0.02, 0.15, ZE - 0.5 - Z0), (-hw + 0.11, -0.02, (Z0 + ZE - 0.5) / 2), T["hollow"], bevel=0.0, segments=1)
            for j, z in enumerate((Z0 + 0.5, (Z0 + ZE) / 2, ZE - 0.9)):
                cyl(f"DoorHinge{j}", 0.045, 0.3, (-hw + 0.05, -0.1, z), gilt, verts=10, bevel=0)
            box("KickPlate", (2 * hw - 0.3, 0.02, 0.3), (0, -0.065, Z0 + 0.32), gilt, bevel=0.006)
            box("PushPlate", (0.1, 0.02, 0.5), (hw - 0.25, -0.06, ZL + 0.9), gilt, bevel=0.008)
            tube("Pull", [(hw - 0.25, -0.07, ZL + 0.6), (hw - 0.25, -0.2, ZL + 0.68), (hw - 0.25, -0.2, ZL + 1.12), (hw - 0.25, -0.07, ZL + 1.2)], 0.025, gilt, poly=True)
        mtx = Matrix.Translation((math.cos(a) * S, math.sin(a) * S, 0)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z")
        _xform(m0, mtx)
        sides.append((mtx, [(-hw + 0.06, z1)] + head + [(hw - 0.06, z1)]))
    # inside, on the back wall: a brass wall telephone with bells, a mouthpiece, a handset on its hook, a coin box, a shelf
    yb = S - 0.1
    box("PhoneBoard", (0.75, 0.05, 1.25), (0, yb, ZL + 1.5), T["inkthin"], bevel=0.01)
    box("PhoneBox", (0.5, 0.24, 0.62), (0, yb - 0.15, ZL + 1.62), gilt, bevel=0.03)
    box("PhoneFace", (0.4, 0.02, 0.5), (0, yb - 0.275, ZL + 1.62), paint, bevel=0.01)
    for sx in (-1, 1):
        sphere(f"Bell{sx}", 0.08, (sx * 0.11, yb - 0.3, ZL + 1.82), gilt, seg=12, rings=6, scale=(1, 0.6, 1))
    cone("Mouthpiece", 0.07, 0.11, 0.14, (0, yb - 0.36, ZL + 1.48), iron, verts=12, rot=(math.pi / 2, 0, 0))
    box("Hook", (0.04, 0.14, 0.04), (0.3, yb - 0.2, ZL + 1.78), gilt, bevel=0.005)
    cyl("Earpiece", 0.06, 0.24, (0.33, yb - 0.26, ZL + 1.6), iron, verts=12, bevel=0.01)
    tube("Cord", [(0.33, yb - 0.27, ZL + 1.47), (0.3, yb - 0.33, ZL + 1.25), (0.2, yb - 0.27, ZL + 1.38)], 0.014, iron)
    cyl("Crank", 0.03, 0.14, (-0.32, yb - 0.18, ZL + 1.6), iron, rot=(0, math.pi / 2, 0), verts=8, bevel=0)
    sphere("CrankKnob", 0.04, (-0.4, yb - 0.24, ZL + 1.6), M["leatherdark"], seg=8, rings=4)
    box("CoinBox", (0.36, 0.2, 0.3), (0, yb - 0.12, ZL + 1.05), paint, bevel=0.02)
    box("CoinSlot", (0.12, 0.01, 0.02), (0, yb - 0.225, ZL + 1.15), T["hollow"], bevel=0.0, segments=1)
    box("Shelf", (1.0, 0.32, 0.05), (0, yb - 0.16, ZL + 0.62), gilt, bevel=0.01)
    box("Directory", (0.4, 0.28, 0.08), (-0.2, yb - 0.16, ZL + 0.69), M["leatherdark"], bevel=0.01)
    # the roof: a cornice with iron cresting and corner pinnacles, a square ogee dome with brass ribs, a lit lantern, a finial
    set_group("Roof")
    box("Cornice", (2 * S + 0.75, 2 * S + 0.75, 0.18), (0, 0, ZE + 0.09), paint, bevel=0.03)
    box("CorniceTop", (2 * S + 0.6, 2 * S + 0.6, 0.08), (0, 0, ZE + 0.22), paint, bevel=0.02)
    R = 1.7                                   # the dome's corner radius (half-side 1.2 once turned)
    prof = [(R, ZE + 0.26), (R * 0.98, ZE + 0.5), (R * 0.8, ZE + 0.8), (R * 0.45, ZE + 1.1), (R * 0.22, ZE + 1.32), (R * 0.14, ZE + 1.45)]
    s0 = _mark()
    lathe("Dome", [(0, ZE + 0.26)] + prof + [(0, ZE + 1.45)], M["slate"], seg=4)
    _xform(s0, Matrix.Rotation(math.pi / 4, 4, "Z"))
    for j in range(4):
        a = math.pi / 4 + j * math.pi / 2
        tube(f"DomeRib{j}", [(math.cos(a) * r, math.sin(a) * r, z + 0.015) for r, z in prof], 0.03, gilt)
    for j in range(4):
        a = j * math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        pts = [(c * 1.45 - s_ * t, s_ * 1.45 + c * t, ZE + 0.26) for t in [-1.15 + 0.23 * i for i in range(11)]]
        cresting(f"Crest{j}", pts, iron, h=0.2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _spirelet(f"Pinnacle{sx}{sy}", sx * 1.38, sy * 1.38, ZE + 0.26, 0.9, 0.2, paint, crockets=1)
    LZ = ZE + 1.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"LampPost{sx}{sy}", [(sx * 0.22, sy * 0.22, LZ), (sx * 0.22, sy * 0.22, LZ + 0.55)], 0.025, paint, square=True, poly=True)
    box("LampBase", (0.56, 0.56, 0.06), (0, 0, LZ), paint, bevel=0.01)
    box("LampTop", (0.6, 0.6, 0.06), (0, 0, LZ + 0.57), paint, bevel=0.01)
    _spike("LampRoof", (0, 0, LZ + 0.75), 0.36, 0.3, paint, verts=4, rot=(0, 0, math.pi / 4))
    sphere("Finial", 0.09, (0, 0, LZ + 0.97), gilt, seg=10, rings=5)
    _foil("FinialCrest", 0, 0, LZ + 1.22, 0.12, gilt, lobes=4, thick=0.022)
    _spike("FinialSpike", (0, 0, LZ + 1.5), 0.025, 0.24, gilt, verts=6)
    set_group("Glass")
    for mtx, poly in sides:
        m0 = _mark()
        relief("Pane", poly, 0.02, 0.02, M["glassclear"], plane="XZ")
        _xform(m0, mtx)
    for k, (px, py, a) in enumerate(((0, -0.21, 0), (0, 0.21, 0), (-0.21, 0, math.pi / 2), (0.21, 0, math.pi / 2))):
        box(f"LampPane{k}", (0.42, 0.012, 0.48), (px, py, LZ + 0.3), M["glassclear"], bevel=0.0, rot=(0, 0, a), segments=1)
    set_group("Glow")
    sphere("LampGlobe", 0.13, (0, 0, LZ + 0.28), M["glassclear"], seg=12, rings=6, scale=(1, 1, 1.25))
    set_group("Main")
    return dims()


# ================================================================== bollards
def bollards(M):
    T = town()
    iron, gilt = M["iron"], M["brass"]
    xs = (-3.7, 0.0, 3.7)
    prof = [(0, 0), (0.42, 0), (0.42, 0.08), (0.34, 0.16), (0.3, 0.3), (0.27, 0.4), (0.24, 1.75), (0.3, 1.82), (0.3, 1.92), (0.22, 1.98),
            (0.18, 2.05), (0.24, 2.18), (0.25, 2.3), (0.18, 2.44), (0.07, 2.53), (0, 2.55)]
    for k, x in enumerate(xs):
        lathe(f"Bollard{k}", prof, iron, seg=28, loc=(x, 0, 0), flute=(12, 0.03) if k == 1 else None)
        hoop(f"BandLow{k}", (x, 0, 0.42), 0.27, "Z", gilt, thick=0.028)
        hoop(f"BandHigh{k}", (x, 0, 1.87), 0.31, "Z", gilt, thick=0.025)
        for sx in (-1, 1):
            if (k == 0 and sx < 0) or (k == 2 and sx > 0):
                continue
            box(f"EyeBoss{k}{sx}", (0.08, 0.1, 0.1), (x + sx * 0.25, 0, 1.6), iron, bevel=0.015)
            _link(f"Eye{k}{sx}", (x + sx * 0.33, 0, 1.6), "Y", 0.06, iron)
    for k in range(2):
        chain(f"Chain{k}", (xs[k] + 0.4, 0, 1.6), (xs[k + 1] - 0.4, 0, 1.6), 0.55, iron, r=0.045)
    return dims()


# ================================================================== iron railing
def iron_railing(M):
    T = town()
    iron, gilt = M["iron"], M["brass"]
    L, ZC = 8.0, 0.7
    box("Coping", (L, 0.62, ZC - 0.1), (0, 0, (ZC - 0.1) / 2), T["stonedark"], bevel=0.0, segments=1)
    prism("CopingTop", [(-0.31, ZC - 0.1), (0.31, ZC - 0.1), (0.22, ZC), (-0.22, ZC)], 0.0, L, T["stone"], plane="YZ")
    for k in (-1, 1):
        box(f"CopingJoint{k}", (0.02, 0.64, ZC - 0.08), (k * 2.0, 0, (ZC - 0.08) / 2), T["soot"], bevel=0.0, segments=1)
    z1, z2, top = 0.92, 3.25, 3.45
    for z in (z1, z2):
        tube(f"Rail{z}", [(-L / 2, 0, z), (L / 2, 0, z)], 0.04, iron, square=True, poly=True)
    tube("RailCap", [(-L / 2, 0, z2 + 0.06), (L / 2, 0, z2 + 0.06)], 0.025, iron, square=True, poly=True)
    n = 32
    step = L / n
    for k in range(n):
        x = -L / 2 + step / 2 + k * step
        tube(f"Bar{k}", [(x, 0, ZC), (x, 0, top)], 0.024, iron, square=True, poly=True)
        _spike(f"Spear{k}", (x, 0, top + 0.12), 0.05, 0.24, iron, verts=4, rot=(0, 0, math.pi / 4))
        box(f"SpearCollar{k}", (0.07, 0.07, 0.04), (x, 0, top + 0.01), iron, bevel=0.0, segments=1)
        if k % 2 == 0:
            hoop(f"Ring{k}", (x + step / 2, 0, 2.95), step / 2 - 0.02, "Y", iron, thick=0.014)
        if k % 4 == 1:
            tube(f"ScrollL{k}", [(x, 0, z1 + 0.05), (x + step * 0.35, 0, z1 + 0.25), (x + step * 0.65, 0, z1 + 0.25), (x + step, 0, z1 + 0.05)], 0.014, iron)
    # a heavier centre post with a gilt finial
    box("Post", (0.16, 0.16, top + 0.2 - ZC), (0, 0, (ZC + top + 0.2) / 2), iron, bevel=0.015)
    lathe("PostFinial", [(0, 0), (0.12, 0), (0.1, 0.08), (0.05, 0.12), (0.09, 0.22), (0.07, 0.34), (0, 0.48)], gilt, seg=12, loc=(0, 0, top + 0.2))
    for k in (-1, 1):
        sphere(f"Rosette{k}", 0.06, (0, k * 0.09, 2.1), gilt, seg=8, rings=4)
    return dims()


# ================================================================== signpost
def signpost(M):
    T = town()
    rnd = random.Random(120)
    iron, gilt, paint, ink, bone = M["iron"], M["brass"], T["ink"], T["inkthin"], T["bone"]
    box("Base", (1.1, 1.1, 0.5), (0, 0, 0.25), T["stonedark"], bevel=0.06)
    box("BaseCap", (0.9, 0.9, 0.14), (0, 0, 0.57), T["stone"], bevel=0.035)
    # a thick cast-iron post: a moulded foot, a fluted base, a collar, a tapering shaft with brass rings, a pinnacle cap
    lathe("Foot", [(0, 0.64), (0.42, 0.64), (0.42, 0.78), (0.34, 0.9), (0.34, 1.0), (0.29, 1.08), (0, 1.08)], iron, seg=24)
    lathe("Fluted", [(0, 1.08), (0.28, 1.08), (0.26, 2.0), (0, 2.0)], iron, seg=40, flute=(10, 0.09))
    lathe("Collar", [(0, 2.0), (0.32, 2.0), (0.34, 2.08), (0.32, 2.16), (0.24, 2.22), (0, 2.22)], iron, seg=24)
    hoop("CollarBand", (0, 0, 2.08), 0.34, "Z", gilt, thick=0.03)
    lathe("Shaft", [(0, 2.22), (0.19, 2.22), (0.16, 6.6), (0, 6.6)], iron, seg=20)
    for k, z in enumerate((3.6, 6.6)):
        hoop(f"Ring{k}", (0, 0, z), 0.2, "Z", gilt, thick=0.03)
    lathe("Cap", [(0, 6.6), (0.25, 6.6), (0.28, 6.72), (0.21, 6.82), (0, 6.82)], iron, seg=16)
    _spirelet("Pinnacle", 0, 0, 6.82, 0.8, 0.24, iron, crockets=1)
    _raven("Crow", Matrix.Translation((0.0, 0.0, 7.62)) @ Matrix.Rotation(0.6, 4, "Z") @ Matrix.Scale(1.9, 4), ink, gilt)
    # three big fingerboards, each with a gilt border, a gilt rule toward the tip and an enamel symbol plaque on both faces
    icons = {
        "school": [(-0.15, -0.12), (0.15, -0.12), (0.15, 0.02), (0.1, 0.02), (0.1, 0.07), (0.05, 0.07), (0.05, 0.02), (0.02, 0.02), (0.0, 0.14),
                   (-0.02, 0.02), (-0.05, 0.02), (-0.05, 0.07), (-0.1, 0.07), (-0.1, 0.02), (-0.15, 0.02)],
        "church": [(-0.1, -0.13), (0.1, -0.13), (0.1, 0.0), (0.025, 0.05), (0.025, 0.08), (0.06, 0.08), (0.06, 0.1), (0.025, 0.1), (0.025, 0.15),
                   (-0.025, 0.15), (-0.025, 0.1), (-0.06, 0.1), (-0.06, 0.08), (-0.025, 0.08), (-0.025, 0.05), (-0.1, 0.0)],
    }
    L, h, px = 2.4, 0.58, 1.05
    for k, (z, yaw, icon) in enumerate(((6.05, math.radians(-15), "school"), (5.3, math.radians(150), "church"), (4.55, math.radians(70), "cross"))):
        m0 = _mark()
        arrow = [(0.2, -h / 2), (L - 0.42, -h / 2), (L, 0.0), (L - 0.42, h / 2), (0.2, h / 2), (0.12, 0.0)]
        relief(f"Board{k}", arrow, 0.0, 0.09, paint, plane="XZ")
        inner = [(0.32, -h / 2 + 0.07), (L - 0.46, -h / 2 + 0.07), (L - 0.12, 0.0), (L - 0.46, h / 2 - 0.07), (0.32, h / 2 - 0.07), (0.25, 0.0)]
        for face in (-1, 1):
            yf = face * 0.05
            tube(f"Border{k}{face}", [(x, yf, z_) for x, z_ in inner], 0.016, gilt, closed=True, square=True, poly=True)
            cyl(f"Plaque{k}{face}", 0.21, 0.03, (px, yf, 0.0), bone, rot=(math.pi / 2, 0, 0), verts=28, bevel=0.0)
            hoop(f"PlaqueRim{k}{face}", (px, yf + face * 0.016, 0.0), 0.215, "Y", gilt, thick=0.022)
            iy = yf + face * 0.02
            if icon == "cross":
                for sgn in (-1, 1):
                    box(f"Cross{k}{face}{sgn}", (0.28, 0.012, 0.05), (px, iy, 0.0), ink, bevel=0.0, rot=(0, sgn * math.pi / 4, 0), segments=1)
                hoop(f"CrossRing{k}{face}", (px, iy, 0.0), 0.12, "Y", ink, thick=0.014)
            else:
                relief(f"Icon{k}{face}", [(px + x, z_) for x, z_ in icons[icon]], iy, 0.012, ink, plane="XZ")
            box(f"Rule{k}{face}", (0.7, 0.012, 0.04), (1.72, yf + face * 0.008, 0.0), gilt, bevel=0.0, segments=1)
            _spike(f"RuleTip{k}{face}", (2.12, yf + face * 0.008, 0.0), 0.06, 0.12, gilt, verts=3, rot=(0, -math.pi / 2, 0))
        lathe(f"Clamp{k}", [(0, -0.14), (0.24, -0.14), (0.25, -0.08), (0.25, 0.08), (0.24, 0.14), (0, 0.14)], iron, seg=16)
        box(f"Strap{k}", (0.32, 0.13, 0.12), (0.28, 0.0, 0.0), iron, bevel=0.012)
        _xform(m0, Matrix.Translation((0, 0, z)) @ Matrix.Rotation(yaw, 4, "Z"))
    _moss("Moss", [(rnd.uniform(-0.4, 0.4), -0.52, 0.5) for _ in range(3)], T["moss"], rnd, 0.09)
    return dims()


# ================================================================== crate pile
def crate_pile(M):
    T = town()
    rnd = random.Random(121)
    crate("CrateA", -1.15, 0.35, 0.0, 1.5, 1.3, 1.2, T, M)
    crate("CrateB", -1.05, 0.35, 1.24, 1.15, 1.0, 0.9, T, M, rot=0.22)
    crate("CrateOpen", 0.5, -0.65, 0.0, 1.2, 0.9, 0.55, T, M, open_top=True, rot=-0.12)
    for i in range(14):
        a, rr = rnd.uniform(0, 6.28), rnd.uniform(0, 0.36)
        mat = T["bone"] if i % 3 else flat("Apple", (0.24, 0.02, 0.02), 0.35, dirt=0.4)
        sphere(f"Turnip{i}", 0.11, (0.5 + math.cos(a) * rr * 1.2, -0.65 + math.sin(a) * rr * 0.7, 0.5 + rnd.uniform(0, 0.12)), mat, seg=10, rings=6, scale=(1, 1, 0.85))
    # a barrel
    bx, by = 1.45, 0.55
    lathe("Barrel", [(0, 0), (0.46, 0), (0.55, 0.4), (0.58, 0.75), (0.55, 1.1), (0.46, 1.5), (0, 1.5)], T["boards"], seg=36, loc=(bx, by, 0), flute=(18, 0.015))
    for k, (z, r) in enumerate(((0.12, 0.475), (0.42, 0.56), (1.08, 0.56), (1.38, 0.475))):
        hoop(f"Hoop{k}", (bx, by, z), r + 0.01, "Z", M["iron"], thick=0.025)
    cyl("BarrelLid", 0.44, 0.03, (bx, by, 1.5), T["boards"], verts=24, bevel=0.005)
    # sacks: lumpy, tied at the neck
    for k, (sx, sy, r, tilt) in enumerate(((0.35, 0.75, 0.42, 0.15), (2.15, -0.25, 0.38, -0.3), (-0.2, -1.15, 0.34, 0.5))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(sx, sy, r * 0.85))
        o = bpy.context.active_object
        o.name = f"Sack{k}"
        o.scale = (1.0, 0.85, 1.25)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for v in o.data.vertices:                              # local coordinates: the centre is the origin
            co = v.co.copy()
            w = 1 + 0.07 * math.sin(co.x * 13 + k) * math.sin(co.y * 11) + rnd.uniform(-0.02, 0.02)
            co *= w
            if co.z < -r * 0.85:
                co.z = -r * 0.85 + (co.z + r * 0.85) * 0.1          # flattened where it sits on the ground
            if co.z > r * 0.9:
                co.x *= 0.75
                co.y *= 0.75                                      # gathered toward the neck
            v.co = co
        for f in o.data.polygons:
            f.use_smooth = True
        o.rotation_euler = (0, 0, k + tilt)
        _finish(o, T["burlap"], 0)
        top = r * 0.85 + r * 1.25 * 0.95
        cone(f"SackNeck{k}", r * 0.3, r * 0.12, r * 0.4, (sx, sy, top + r * 0.12), T["burlap"], verts=12)
        hoop(f"SackTie{k}", (sx, sy, top + 0.02), r * 0.24, "Z", flat("Twine", (0.3, 0.24, 0.14), 0.9), thick=0.022)
    # an oxblood tarpaulin tied over the top crate
    cx, cy, ztop = -1.05, 0.35, 1.24 + 0.9 + 0.05
    rows = []
    n = 22
    for i in range(n + 1):
        u = -1 + 2 * i / n
        row = []
        for j in range(n + 1):
            v = -1 + 2 * j / n
            x, y = u * 0.82, v * 0.72
            # over the top it lies flat with soft creases; past the crate's edge it falls in a curve to a rippled hem
            over = math.hypot(max(abs(x) - 0.56, 0), max(abs(y) - 0.48, 0))
            z = ztop - 0.1 * over - 2.6 * over * over
            edge = min(1.0, over / 0.22)
            z += 0.025 * math.sin(u * 7 + v * 3) + 0.07 * edge * math.sin(math.atan2(y, x) * 9)
            k = 1 + 0.12 * edge                                    # the hem flares out a little
            row.append(Vector((cx + (x * math.cos(0.22) - y * math.sin(0.22)) * k, cy + (x * math.sin(0.22) + y * math.cos(0.22)) * k, max(z, 1.5))))
        rows.append(row)
    _mesh("Tarp", rows, T["canvasred"], 0.02)
    tube("Rope", [(cx + 0.7 * math.cos(0.22), cy + 0.7 * math.sin(0.22), 1.55), (cx, cy, ztop + 0.04), (cx - 0.7 * math.cos(0.22), cy - 0.7 * math.sin(0.22), 1.55)], 0.02,
         flat("Twine", (0.3, 0.24, 0.14), 0.9))
    return dims()


P.PREVIEW_PAD.update({"ShopApothecary": 1.0, "ShopCurio": 1.0, "MarketStall": 1.05, "HangingSign": 1.25, "Postbox": 1.15, "StreetPump": 1.15,
                      "NewsKiosk": 1.05, "TelephoneBooth": 1.05, "Bollards": 1.0, "IronRailing": 1.0, "Signpost": 1.1, "CratePile": 1.1})
P.OPEN_DEG.update({"ShopApothecary_Door0": 95, "ShopCurio_Door0": 95})

P.BUILD.update({
    "ShopApothecary": shop_apothecary,
    "ShopCurio": shop_curio,
    "MarketStall": market_stall,
    "HangingSign": hanging_sign,
    "Postbox": postbox,
    "StreetPump": street_pump,
    "NewsKiosk": news_kiosk,
    "TelephoneBooth": telephone_booth,
    "Bollards": bollards,
    "IronRailing": iron_railing,
    "Signpost": signpost,
    "CratePile": crate_pile,
})
