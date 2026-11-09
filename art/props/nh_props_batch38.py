"""Props batch 38, the electives kit, for nh_props.py: pieces to dress the new elective classrooms.

Herbology   PottingBench (a slatted bench: pots, soil, trowels, seedlings, plant markers), HerbDryingRack (bundles of herbs hung
            from a wooden rack), Terrarium (a gothic glass case of ferns and moss; Glass: the panes)
Home Ec     CastIronRange (a cast-iron kitchen range, two oven doors, hotplates, a warming shelf and flue), PotRack (an iron rack of
            copper pans on chains; hangs from the ceiling, its top 3.4 above its lowest point), MixingBowlSet (stacked bowls, a
            whisk, a rolling pin)
Sewing      TreadleSewingMachine (an iron treadle stand, a black and gilt machine), DressForm (a form on a tripod, a half-made
            garment pinned on it), FabricBolts (a rack of fabric bolts)
Photography BellowsCamera (a wooden bellows camera on a tripod), DarkroomTrays (a bench of developing trays, prints hung on a line,
            a red safelight; Glow: the safelight's lens)
Woodshop    WoodLathe (a cast-iron lathe on a bench), ToolWall (a pegboard of tools over painted outlines), Sawhorse (a pair with a
            plank)
Ceramics    PottersWheel (a kick wheel with a clay pot on it), Kiln (a brick-and-iron kiln)
Drama       CostumeRack (a rolling rail: a cape, a gown, an armour tabard), TheatreMasks (comedy and tragedy on a wall plaque)

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: on the wall plane, y = 0). Prints and fabrics come
from kits3739_atlas.py (ElectivesPrint). Registered into nh_props.BUILD on import.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish, _gable
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, leaf, _mark, _xform, _dims, flat, _solid
from nh_props_batch9 import foil
from nh_props_batch24 import _text, _fine, rbox
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import nh_props_batch34_dorm as B34
import nh_props_batch37 as B37
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = B37.FONT
kit = B37.kit


def terracotta():
    return material("Terracotta", "NH_Limestone", tint=(0.52, 0.2, 0.09), scale=1.2, rough_add=0.15, wear=0.35, dirt=0.85)


def soil_mat():
    return material("PotSoil", "NH_Limestone", tint=(0.06, 0.042, 0.03), scale=3.0, rough_add=0.15, wear=0.0, dirt=0.9)


def copper():
    return material("Copper", "NH_Brass", tint=(0.95, 0.5, 0.36), scale=0.6, wear=0.25, dirt=0.75)


def clay_mat(wet=True):
    return material("ClayWet" if wet else "ClayDry", "NH_Limestone", tint=(0.42, 0.27, 0.19) if wet else (0.62, 0.5, 0.4), scale=2.0,
                    rough_add=-0.25 if wet else 0.1, normal=0.3, wear=0.0, dirt=0.6)


def pot(prefix, x, y, z, r, K, tc, soil=True, h=None):
    h = h or r * 1.1
    lathe(f"{prefix}Pot", [(0, 0), (r * 0.7, 0), (r * 0.72, 0.02), (r * 0.92, h * 0.82), (r * 1.05, h * 0.84), (r * 1.06, h), (r * 0.96, h), (r * 0.94, h * 0.86),
                           (r * 0.68, 0.06), (0, 0.06)], tc, seg=24, loc=(x, y, z))
    if soil:
        cyl(f"{prefix}Soil", r * 0.92, 0.02, (x, y, z + h * 0.9), soil_mat(), verts=20, bevel=0.0)
    return z + h * 0.9


def seedling(prefix, x, y, z, rnd, mat, n=5, s=1.0):
    tube(f"{prefix}Stem", [(x, y, z), (x + rnd.uniform(-0.02, 0.02), y, z + 0.18 * s)], 0.008, mat, poly=True)
    for k in range(n):
        yaw = k / n * 6.28 + rnd.uniform(-0.3, 0.3)
        leaf(f"{prefix}L{k}", (x, y, z + (0.06 + 0.12 * k / n) * s), yaw, rnd.uniform(0.3, 0.8), 0.18 * s, 0.05 * s, 0.4, mat, n=6, thick=0.006)


def marker_stick(prefix, key, K, mtx):
    s = _mark()
    box(f"{prefix}Stick", (0.04, 0.012, 0.32), (0, 0, 0.16), flat("StickWood", (0.5, 0.38, 0.24), 0.8), bevel=0.003)
    B30.plate(f"{prefix}Tag", key, 0.24, 0.08, 0.008, T(0, -0.01, 0.32), K["p8"], edge="K8_label", k=1.6)
    _xform(s, mtx)


def trowel(prefix, K, mtx):
    s = _mark()
    steel = K["steel"]
    B20.tprism(f"{prefix}Blade", [(0, 0), (0.07, 0.04), (0.08, 0.2), (0, 0.3), (-0.08, 0.2), (-0.07, 0.04)], 0.0, 0.01, steel, plane="XY")
    tube(f"{prefix}Shank", [(0, -0.02, 0.01), (0, -0.07, 0.04), (0, -0.1, 0.04)], 0.012, steel)
    lathe(f"{prefix}Handle", [(0, 0), (0.025, 0), (0.03, 0.08), (0.025, 0.2), (0, 0.21)], K["darkoak"], seg=12)
    P.PARTS[-1].matrix_world = T(0, -0.1, 0.04) @ RX(math.pi / 2)
    _xform(s, mtx)


# ================================================================== herbology

def potting_bench(M):
    K = kit(M)
    rnd = random.Random(3801)
    tc = terracotta()
    W, D, top = 5.0, 2.0, 2.9
    wd = K["darkoak"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Leg{sx}{sy}", (0.16, 0.16, top - 0.08), (sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), (top - 0.08) / 2), wd, bevel=0.02)
        box(f"Rail{sx}", (0.1, D - 0.3, 0.14), (sx * (W / 2 - 0.15), 0, 0.5), wd, bevel=0.015)
        box(f"BackPost{sx}", (0.14, 0.14, 2.0), (sx * (W / 2 - 0.15), D / 2 - 0.15, top + 1.0), wd, bevel=0.02)
        tube(f"Brace{sx}", [(sx * (W / 2 - 0.15), D / 2 - 0.08, top - 0.8), (sx * (W / 2 - 0.8), D / 2 - 0.08, top - 0.1)], 0.03, K["iron"], poly=True)
    for k in range(9):
        box(f"Slat{k}", (W, 0.19, 0.08), (0, -D / 2 + 0.11 + k * 0.222, top - 0.04), wd, bevel=0.015)
    for k in range(6):
        box(f"LowSlat{k}", (W - 0.3, 0.24, 0.06), (0, -D / 2 + 0.25 + k * 0.3, 0.6), wd, bevel=0.012)
    box("Shelf", (W, 0.5, 0.07), (0, D / 2 - 0.3, top + 1.4), wd, bevel=0.015)
    box("Backboard", (W - 0.3, 0.05, 0.6), (0, D / 2 - 0.1, top + 0.3), wd, bevel=0.01)
    box("Lip", (W, 0.05, 0.18), (0, -D / 2 + 0.02, top + 0.05), wd, bevel=0.01)
    green = flat("Seedling", (0.05, 0.16, 0.04), 0.5)
    sage = flat("SageLeaf", (0.18, 0.24, 0.16), 0.6)
    # pots on the bench with seedlings and markers, a soil heap, two trowels
    for k, (x, y, r) in enumerate(((-1.9, 0.35, 0.22), (-1.35, 0.4, 0.18), (-0.8, 0.45, 0.2), (1.2, 0.4, 0.24), (1.8, 0.3, 0.2))):
        zt = pot(f"P{k}", x, y, top, r, K, tc)
        for j in range(2 + k % 2):
            seedling(f"S{k}{j}", x + rnd.uniform(-r * 0.4, r * 0.4), y + rnd.uniform(-r * 0.4, r * 0.4), zt, rnd, green if k % 2 else sage, s=1.0 + 0.3 * (k % 3))
        names = [n for n in B37.KA["regions"]["ElectivesPrint"] if n.startswith("Herb_")]
        marker_stick(f"M{k}", "K8_" + names[k % len(names)], K, T(x + r * 0.5, y - r * 0.5, zt - 0.05) @ RZ(rnd.uniform(-0.3, 0.3)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, segments=20, ring_count=10, location=(0.15, -0.05, top - 0.05))
    heap = bpy.context.active_object
    heap.name = "Heap"
    heap.scale = (1.4, 0.9, 0.35)
    bpy.ops.object.transform_apply(scale=True)
    for v in heap.data.vertices:
        if v.co.z < top:
            v.co.z = top
        v.co += Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), rnd.uniform(-0.02, 0.02)))
    _finish(heap, soil_mat(), 0)
    trowel("TrowelA", K, T(0.4, -0.55, top + 0.12) @ RZ(-30 * DEG) @ RX(0.15))
    trowel("TrowelB", K, T(-0.3, -0.6, top + 0.01) @ RZ(80 * DEG))
    # stacked empty pots on the shelf and under the bench, a sack of compost below
    for k in range(4):
        pot(f"Stk{k}", -1.6, D / 2 - 0.3, top + 1.435 + k * 0.08, 0.2, K, tc, soil=False)
    for k in range(3):
        pot(f"Sh{k}", 0.6 + k * 0.6, D / 2 - 0.3, top + 1.435, 0.16, K, tc, soil=False)
    for k in range(3):
        pot(f"Low{k}", 1.4, -0.2, 0.63 + k * 0.1, 0.26, K, tc, soil=False)
    sack = material("Burlap", "NH_Leather", tint=(0.42, 0.32, 0.2), scale=6.0, normal=0.7, rough_add=0.25, wear=0.0)
    B29.cushion("Sack", (1.3, 0.9, 1.0), (-1.2, 0.0, 1.13), sack, e=(0.6, 0.55), cuts=6, puff=0.2)
    return _dims()


HERB_COLS = [((0.12, 0.2, 0.09), "Sage"), ((0.22, 0.24, 0.1), "Thyme"), ((0.3, 0.2, 0.36), "Lavender"), ((0.25, 0.2, 0.08), "Rue"),
             ((0.1, 0.22, 0.08), "Mint"), ((0.32, 0.27, 0.12), "Moonwort")]


def herb_bundle(prefix, top, K, rnd, colour, flowers=None):
    """A bundle hanging head down: twine from the rail, a tied waist, stems fanning down, leaves along them."""
    x, y, z = top
    twine = flat("Twine", (0.42, 0.33, 0.2), 0.9)
    stem = flat(f"Stem{prefix}", tuple(c * 0.7 for c in colour), 0.8)
    lf = flat(f"Herb{prefix}", colour, 0.8)
    tube(f"{prefix}Twine", [(x, y, z), (x, y, z - 0.25)], 0.008, twine, poly=True)
    cyl(f"{prefix}Tie", 0.045, 0.05, (x, y, z - 0.28), twine, verts=10, bevel=0.005)
    for k in range(6):
        a = k / 6 * 6.28 + rnd.uniform(-0.3, 0.3)
        sp = rnd.uniform(0.08, 0.18)
        L = rnd.uniform(0.75, 1.05)
        end = (x + math.cos(a) * sp, y + math.sin(a) * sp, z - 0.28 - L)
        tube(f"{prefix}S{k}", [(x, y, z - 0.3), (x + math.cos(a) * sp * 0.5, y + math.sin(a) * sp * 0.5, z - 0.3 - L * 0.5), end], 0.007, stem, poly=True, res=2)
        for j in range(3):
            t = 0.35 + j * 0.25
            p = (x + math.cos(a) * sp * t, y + math.sin(a) * sp * t, z - 0.3 - L * t)
            leaf(f"{prefix}L{k}{j}", p, a + rnd.uniform(-0.6, 0.6), rnd.uniform(-1.3, -0.7), rnd.uniform(0.14, 0.22), 0.045, -0.1, lf, n=4, thick=0.005)
        if flowers:
            sphere(f"{prefix}F{k}", 0.035, end, flowers, seg=6, rings=4, scale=(1, 1, 1.8))


def herb_drying_rack(M):
    """A freestanding wooden rack (4.6 wide, 5.6 tall): three rails, a dozen bundles of drying herbs hung from them."""
    K = kit(M)
    rnd = random.Random(3802)
    wd = K["darkoak"]
    W, H, D = 4.6, 5.6, 1.6
    for sx in (-1, 1):
        x = sx * (W / 2)
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(x, sy * D / 2, 0.0), (x, sy * 0.08, H - 0.1)], 0.07, wd, square=True, poly=True)
        tube(f"Cross{sx}", [(x, -D / 2 * 0.62, 1.6), (x, D / 2 * 0.62, 1.6)], 0.05, wd, square=True, poly=True)
        sphere(f"Cap{sx}", 0.1, (x, 0, H), K["iron"], seg=10, rings=5)
    rails = [(0, H - 0.15), (-0.32, H - 1.5), (0.32, H - 1.5)]
    for k, (y, z) in enumerate(rails):
        tube(f"Rail{k}", [(-W / 2 - 0.1, y, z), (W / 2 + 0.1, y, z)], 0.05, wd, poly=True)
    lav = flat("LavFlower", (0.32, 0.18, 0.42), 0.8)
    yellow = flat("TansyFlower", (0.55, 0.42, 0.08), 0.8)
    n = 0
    for k, (y, z) in enumerate(rails):
        cnt = 4
        for i in range(cnt):
            x = -W / 2 + 0.5 + i * (W - 1.0) / (cnt - 1) + (0.15 if k == 2 else 0)
            col, name = HERB_COLS[n % len(HERB_COLS)]
            fl = lav if name == "Lavender" else yellow if name == "Rue" else None
            herb_bundle(f"B{n}", (x, y, z - 0.03), K, rnd, col, fl)
            n += 1
    return _dims()


def terrarium(M):
    """A tabletop gothic glass case (2.2 x 1.4, 2.6 to the finial): an iron frame with a pointed roof, ferns and moss inside;
    Glass: every pane."""
    K = kit(M)
    rnd = random.Random(3803)
    ir = K["iron"]
    W, D, Hb, Hr = 2.2, 1.4, 1.5, 0.75
    zb = 0.3
    box("Base", (W + 0.16, D + 0.16, 0.22), (0, 0, 0.11), K["ebony"], bevel=0.03)
    box("Tray", (W, D, 0.1), (0, 0, 0.27), ir, bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Foot{sx}{sy}", 0.07, (sx * (W / 2 + 0.02), sy * (D / 2 + 0.02), 0.04), K["brass"], seg=10, rings=5, scale=(1, 1, 0.6))
            tube(f"Post{sx}{sy}", [(sx * W / 2, sy * D / 2, zb), (sx * W / 2, sy * D / 2, zb + Hb)], 0.03, ir, square=True, poly=True)
    for z in (zb + 0.02, zb + Hb):
        tube(f"Ring{z:.1f}", [(-W / 2, -D / 2, z), (W / 2, -D / 2, z), (W / 2, D / 2, z), (-W / 2, D / 2, z)], 0.025, ir, square=True, closed=True, poly=True)
    for sy in (-1, 1):
        for x in (-W / 6, W / 6):
            tube(f"Mull{x:.1f}{sy}", [(x, sy * D / 2, zb), (x, sy * D / 2, zb + Hb)], 0.015, ir, square=True, poly=True)
        pts = WS.arch(W / 6 - 0.02, zb + Hb - 0.45, zb + Hb - 0.25, zb + Hb - 0.05, 6)
        for cx in (-W / 3, 0, W / 3):
            tube(f"Arch{cx:.1f}{sy}", [(cx + x, sy * (D / 2 + 0.005), z) for x, z in pts], 0.012, ir, poly=True)
    # the roof: two slopes to a ridge with cresting, gable ends
    zr = zb + Hb
    for sy in (-1, 1):
        tube(f"Eave{sy}", [(-W / 2, sy * D / 2, zr), (W / 2, sy * D / 2, zr)], 0.025, ir, square=True, poly=True)
        for k in range(5):
            x = -W / 2 + k * W / 4
            tube(f"Rafter{sy}{k}", [(x, sy * D / 2, zr), (x, 0, zr + Hr)], 0.018, ir, square=True, poly=True)
    tube("Ridge", [(-W / 2, 0, zr + Hr), (W / 2, 0, zr + Hr)], 0.03, ir, square=True, poly=True)
    for k in range(9):
        x = -W / 2 + 0.1 + k * (W - 0.2) / 8
        B20.tprism(f"Crest{k}", [(x - 0.05, zr + Hr), (x, zr + Hr + 0.14), (x + 0.05, zr + Hr)], 0.0, 0.015, ir)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.06, (sx * W / 2, 0, zr + Hr + 0.08), K["brass"], seg=10, rings=5)
    set_group("Glass")
    for sy in (-1, 1):
        box(f"PaneLong{sy}", (W - 0.04, 0.012, Hb - 0.04), (0, sy * D / 2, zb + Hb / 2), K["glass"], bevel=0.0)
    for sx in (-1, 1):
        box(f"PaneEnd{sx}", (0.012, D - 0.04, Hb - 0.04), (sx * W / 2, 0, zb + Hb / 2), K["glass"], bevel=0.0)
        B20.tprism(f"Gable{sx}", [(-D / 2, zr), (D / 2, zr), (0, zr + Hr)], sx * W / 2, 0.012, K["glass"], plane="YZ")
    ang = math.atan2(Hr, D / 2)
    sl = math.hypot(Hr, D / 2)
    for sy in (-1, 1):
        box(f"Roof{sy}", (W - 0.04, sl, 0.012), (0, sy * D / 4, zr + Hr / 2), K["glass"], bevel=0.0, rot=(-sy * ang, 0, 0))
    set_group("Main")
    # inside: soil, moss mounds, pebbles, ferns
    box("Soil", (W - 0.1, D - 0.1, 0.05), (0, 0, zb + 0.06), soil_mat(), bevel=0.0)
    moss = material("Moss", "NH_Limestone", tint=(0.08, 0.16, 0.05), scale=4.0, normal=1.2, rough_add=0.3, wear=0.0)
    for k in range(6):
        sphere(f"Moss{k}", rnd.uniform(0.15, 0.25), (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.4, 0.4), zb + 0.08), moss, seg=12, rings=6, scale=(1.3, 1.0, 0.45))
    stone = material("Pebble", "NH_Limestone", tint=(0.45, 0.43, 0.4), scale=2.0, wear=0.2)
    for k in range(10):
        sphere(f"Pebble{k}", rnd.uniform(0.03, 0.06), (rnd.uniform(-0.95, 0.95), rnd.uniform(-0.55, 0.55), zb + 0.1), stone, seg=8, rings=4, scale=(1.2, 1, 0.7))
    cols = ((0.02, 0.06, 0.016), (0.035, 0.12, 0.03), (0.06, 0.17, 0.045))
    leaves = B34.attr_mat("TerrFern", rough=0.5)
    for c, (cx, cy) in enumerate(((-0.5, 0.05), (0.55, -0.05))):
        for k in range(7):
            yaw = k / 7 * 6.28 + rnd.uniform(-0.2, 0.2)
            B34.frond(f"F{c}{k}", (cx, cy, zb + 0.1), yaw, rnd.uniform(35, 65) * DEG, rnd.uniform(0.55, 0.8), 0.45, cols, rnd, leaves, width=0.8, n=11)
    return _dims()


# ================================================================== home ec

def cast_iron_range(M):
    """A cast-iron kitchen range (5.2 wide, hotplate top 3.0) with two oven doors, a firebox door, round hotplate lids, a brass rail,
    a warming shelf on the splashback and a flue pipe (7.6 to its top), a kettle on the hob."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    W, D, top = 5.2, 2.4, 3.0
    box("Body", (W, D, top - 0.5), (0, 0, 0.5 + (top - 0.5) / 2), ir, bevel=0.03)
    box("Plinth", (W + 0.1, D + 0.06, 0.35), (0, 0, 0.3), ir, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Foot{sx}{sy}", [(0, 0), (0.14, 0), (0.12, 0.05), (0.08, 0.15), (0.1, 0.13), (0, 0.15)], ir, seg=12, loc=(sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), 0))
    box("Hob", (W + 0.08, D + 0.06, 0.12), (0, 0, top - 0.06), ir, bevel=0.025)
    for k, (x, y, r) in enumerate(((-1.6, -0.45, 0.38), (-0.6, -0.45, 0.38), (0.6, -0.45, 0.32), (1.6, -0.45, 0.32), (-1.1, 0.5, 0.3), (1.1, 0.5, 0.3))):
        cyl(f"Plate{k}", r, 0.03, (x, y, top + 0.015), ir, verts=32, bevel=0.008)
        hoop(f"PlateRing{k}", (x, y, top + 0.02), r - 0.04, "Z", K["ironf"], thick=0.01)
        cyl(f"PlateLift{k}", 0.06, 0.02, (x, y, top + 0.04), ir, verts=10, bevel=0.005)
    # doors: firebox (left top), two ovens, an ash drawer
    yf = -D / 2 - 0.01

    def door(prefix, cx, cz, w, h):
        box(f"{prefix}", (w, 0.08, h), (cx, yf - 0.02, cz), ir, bevel=0.025)
        tube(f"{prefix}Edge", [(cx - w / 2 + 0.08, yf - 0.065, cz - h / 2 + 0.08), (cx + w / 2 - 0.08, yf - 0.065, cz - h / 2 + 0.08),
                               (cx + w / 2 - 0.08, yf - 0.065, cz + h / 2 - 0.08), (cx - w / 2 + 0.08, yf - 0.065, cz + h / 2 - 0.08)], 0.02, K["ironf"], square=True,
             closed=True, poly=True)
        foil(f"{prefix}Foil", cx, yf - 0.07, cz, min(w, h) * 0.2, K["ironf"], lobes=4, thick=0.016)
        tube(f"{prefix}Bar", [(cx - w * 0.3, yf - 0.1, cz + h / 2 - 0.12), (cx + w * 0.3, yf - 0.1, cz + h / 2 - 0.12)], 0.025, br, poly=True)
        for sx in (-1, 1):
            tube(f"{prefix}BarArm{sx}", [(cx + sx * w * 0.3, yf - 0.1, cz + h / 2 - 0.12), (cx + sx * w * 0.3, yf - 0.05, cz + h / 2 - 0.12)], 0.02, br, poly=True)
        for sz in (-1, 1):
            box(f"{prefix}Hinge{sz}", (0.16, 0.06, 0.1), (cx - w / 2 - 0.02, yf - 0.03, cz + sz * h * 0.32), ir, bevel=0.01)
    door("Firebox", -1.65, 2.2, 1.3, 0.8)
    door("Oven1", -0.95, 1.2, 1.9, 1.2)
    door("Oven2", 1.2, 1.55, 2.2, 1.9)
    box("AshDrawer", (1.3, 0.06, 0.3), (-1.65, yf - 0.02, 0.62), ir, bevel=0.015)
    for k in range(5):
        box(f"Vent{k}", (0.14, 0.02, 0.04), (-1.95 + k * 0.15, yf - 0.06, 0.62), K["groove"], bevel=0.0)
    # brass rail along the front, a temperature dial, the maker's plate
    tube("Rail", [(-W / 2 - 0.05, -D / 2 - 0.25, top - 0.25), (W / 2 + 0.05, -D / 2 - 0.25, top - 0.25)], 0.035, br, poly=True)
    for sx in (-1, 1):
        tube(f"RailArm{sx}", [(sx * (W / 2 - 0.05), -D / 2 - 0.25, top - 0.25), (sx * (W / 2 - 0.05), -D / 2, top - 0.25)], 0.03, br, poly=True)
    cyl("Dial", 0.15, 0.04, (1.2, yf - 0.06, 2.75), br, rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
    cyl("DialFace", 0.12, 0.01, (1.2, yf - 0.085, 2.75), K["bone"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.0)
    tube("DialNeedle", [(1.2, yf - 0.095, 2.75), (1.26, yf - 0.095, 2.83)], 0.008, K["ink"], poly=True)
    box("MakerPlate", (1.0, 0.03, 0.22), (-0.95, yf - 0.03, 2.3), br, bevel=0.008)
    _text("Maker", "NOCTURNE", FONT, K["gilt"], lambda x, y, h: (x, yf - 0.045 - h, 2.3 + y), fit=(0.8, 0.12), depth=0.01, res=3)
    # splashback, warming shelf, flue
    box("Splash", (W, 0.12, 1.4), (0, D / 2 - 0.06, top + 0.7), ir, bevel=0.02)
    for k in range(4):
        cx = -W / 2 + 0.65 + k * (W - 1.3) / 3
        foil(f"SplashFoil{k}", cx, D / 2 - 0.13, top + 0.75, 0.2, K["ironf"], lobes=4, thick=0.016)
    box("Shelf", (W, 0.7, 0.1), (0, D / 2 - 0.35, top + 1.45), ir, bevel=0.02)
    for sx in (-1, 1):
        tube(f"ShelfBracket{sx}", [(sx * (W / 2 - 0.2), D / 2 - 0.1, top + 0.9), (sx * (W / 2 - 0.2), D / 2 - 0.6, top + 1.4)], 0.03, ir, poly=True)
    cyl("Flue", 0.25, 3.0, (1.6, D / 2 - 0.35, top + 1.5 + 1.5), ir, verts=20, bevel=0.01)
    for z in (top + 2.2, top + 3.6):
        hoop(f"FlueBand{z:.1f}", (1.6, D / 2 - 0.35, z), 0.26, "Z", K["ironf"], thick=0.02)
    cyl("Damper", 0.04, 0.6, (1.6, D / 2 - 0.35, top + 2.5), br, rot=(0, math.pi / 2, 0), verts=10, bevel=0.005)
    # a kettle on the hob
    s = _mark()
    lathe("Kettle", [(0, 0), (0.3, 0), (0.36, 0.08), (0.37, 0.2), (0.32, 0.34), (0.16, 0.42), (0.1, 0.44), (0, 0.44)], copper(), seg=28)
    cyl("KettleKnob", 0.05, 0.06, (0, 0, 0.47), K["ebony"], verts=10, bevel=0.01)
    tube("Spout", [(0.3, 0, 0.15), (0.45, 0, 0.28), (0.55, 0, 0.42)], 0.04, copper())
    tube("KHandle", [(-0.22, 0, 0.38), (-0.15, 0, 0.62), (0.15, 0, 0.62), (0.22, 0, 0.38)], 0.025, K["ebony"])
    _xform(s, T(-1.6, -0.45, top + 0.03))
    return _dims()


def pan(prefix, r, depth, K, cu, mtx, handle=0.6):
    s = _mark()
    lathe(f"{prefix}Pan", [(0, 0), (r * 0.9, 0), (r, depth * 0.3), (r * 1.02, depth), (r * 0.97, depth), (r * 0.95, depth * 0.35), (r * 0.86, 0.02), (0, 0.02)], cu,
          seg=28)
    tube(f"{prefix}Handle", [(r * 0.95, 0, depth * 0.8), (r + handle * 0.5, 0, depth * 0.95), (r + handle, 0, depth * 1.1)], 0.025, K["brassf"], poly=True)
    hoop(f"{prefix}Loop", (r + handle + 0.03, 0, depth * 1.1), 0.04, "Y", K["brassf"], thick=0.01)
    _xform(s, mtx)


def pot_rack(M):
    """An iron ceiling rack (4.8 x 1.8): a rectangular frame with a grid, hung from four chains (its top, the ceiling plates, 3.4
    above the lowest pan), copper pans on S-hooks round it, two lids on top."""
    K = kit(M)
    ir = K["iron"]
    cu = copper()
    W, D = 4.8, 1.8
    zr = 1.4
    tube("Frame", [(-W / 2, -D / 2, zr), (W / 2, -D / 2, zr), (W / 2, D / 2, zr), (-W / 2, D / 2, zr)], 0.04, ir, square=True, closed=True, poly=True)
    for k in range(1, 6):
        x = -W / 2 + k * W / 6
        tube(f"Grid{k}", [(x, -D / 2, zr), (x, D / 2, zr)], 0.018, ir, square=True, poly=True)
    tube("Spine", [(-W / 2, 0, zr), (W / 2, 0, zr)], 0.02, ir, square=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B30.chain(f"Chain{sx}{sy}", [(sx * (W / 2 - 0.2), sy * (D / 2 - 0.1), zr), (sx * (W / 2 - 0.5), sy * 0.2, 3.3)], ir, r=0.05, thick=0.012)
            sphere(f"Corner{sx}{sy}", 0.06, (sx * W / 2, sy * D / 2, zr), K["brass"], seg=10, rings=5)
    for sx in (-1, 1):
        cyl(f"Ceil{sx}", 0.18, 0.08, (sx * (W / 2 - 0.5), 0, 3.36), ir, verts=16, bevel=0.015)
        hoop(f"CeilEye{sx}", (sx * (W / 2 - 0.5), 0, 3.28), 0.05, "X", ir, thick=0.012)
    g = random.Random(3805)
    spots = [(-2.1, -1), (-1.3, -1), (-0.4, -1), (0.6, -1), (1.5, -1), (2.2, -1), (-1.8, 1), (-0.6, 1), (0.7, 1), (1.9, 1)]
    for k, (x, sy) in enumerate(spots):
        y = sy * D / 2
        tube(f"Hook{k}", [(x, y, zr + 0.02), (x, y + sy * 0.06, zr + 0.06), (x, y + sy * 0.1, zr), (x, y + sy * 0.08, zr - 0.15), (x, y + sy * 0.04, zr - 0.2)],
             0.012, K["brassf"])
        r = g.uniform(0.22, 0.4)
        hl = g.uniform(0.45, 0.7)
        # pans hang by the loop on the handle, the pan below
        pan(f"Pan{k}", r, g.uniform(0.12, 0.3), K, cu, T(x, y + sy * 0.05, zr - 0.25) @ RZ(-sy * 90 * DEG) @ RY(-90 * DEG) @ T(-(r + hl + 0.03), 0, -0.2), hl)
    for k, x in enumerate((-1.2, 1.0)):
        lathe(f"Lid{k}", [(0, 0.08), (0.2, 0.06), (0.32, 0.01), (0.34, 0.0), (0.0, 0.0)], cu, seg=24, loc=(x, 0.3, zr + 0.04))
        sphere(f"LidKnob{k}", 0.04, (x, 0.3, zr + 0.14), K["brassf"], seg=8, rings=4)
    return _dims()


def mixing_bowl_set(M):
    K = kit(M)
    glaze = [flat("BowlCrimson", (0.13, 0.016, 0.026), 0.15), flat("BowlBone", (0.62, 0.58, 0.5), 0.15), flat("BowlInk", (0.03, 0.035, 0.06), 0.12)]
    inside = flat("BowlInside", (0.7, 0.67, 0.6), 0.12)
    z = 0.0
    for k, r in enumerate((0.55, 0.44, 0.34)):
        h = r * 0.62
        lathe(f"Bowl{k}", [(0, 0), (r * 0.5, 0), (r * 0.55, 0.03), (r * 0.9, h * 0.6), (r, h), (r * 1.04, h + 0.02), (r * 0.96, h + 0.02), (r * 0.9, h * 0.65),
                           (r * 0.48, 0.06), (0, 0.06)], glaze[k], seg=36, loc=(0.0, 0.0, z))
        lathe(f"BowlIn{k}", [(0, 0.062), (r * 0.47, 0.062), (r * 0.88, h * 0.65), (r * 0.94, h + 0.015)], inside, seg=36, loc=(0.0, 0.0, z))
        z += 0.07
    flour = flat("Flour", (0.82, 0.8, 0.76), 0.95)
    lathe("FlourHeap", [(0, 0.22), (0.18, 0.18), (0.28, 0.13), (0.3, 0.12), (0, 0.12)], flour, seg=24, loc=(0, 0, 0.0))
    # the whisk
    s = _mark()
    lathe("WhiskHandle", [(0, 0), (0.035, 0), (0.04, 0.05), (0.03, 0.3), (0.035, 0.34), (0, 0.35)], K["darkoak"], seg=12)
    for k in range(6):
        a = k / 6 * math.pi
        pts = [(math.cos(a) * r, math.sin(a) * r, z_) for r, z_ in ((0.02, 0.0), (0.09, -0.1), (0.12, -0.25), (0.08, -0.38), (0.0, -0.42))]
        pts += [(-x, -y, zz) for x, y, zz in reversed(pts[:-1])]
        tube(f"Wire{k}", pts, 0.004, K["steel"], res=2)
    _xform(s, T(0.85, -0.2, 0.06) @ RZ(0.6) @ RY(-80 * DEG))
    # the rolling pin
    s = _mark()
    lathe("Pin", [(0, -0.5), (0.1, -0.5), (0.11, -0.45), (0.11, 0.45), (0.1, 0.5), (0, 0.5)], K["oak"], seg=20)
    for sz in (-1, 1):
        lathe(f"PinHandle{sz}", [(0, 0), (0.04, 0), (0.05, 0.06), (0.04, 0.2), (0.0, 0.22)], K["darkoak"], seg=12, loc=(0, 0, 0.5) if sz > 0 else (0, 0, -0.5))
        if sz < 0:
            P.PARTS[-1].matrix_world = RX(math.pi)
    _xform(s, T(-0.2, -0.85, 0.11) @ RZ(10 * DEG) @ RY(90 * DEG))
    # a wooden spoon and a dusting of flour
    s = _mark()
    tube("SpoonHandle", [(0, 0, 0), (0.45, 0, 0.0)], 0.022, K["oak"], poly=True)
    sphere("SpoonBowl", 0.08, (0.52, 0, 0.0), K["oak"], seg=12, rings=6, scale=(1.3, 1, 0.35))
    _xform(s, T(-0.95, 0.25, 0.03) @ RZ(-40 * DEG))
    g = random.Random(3806)
    for k in range(10):
        sphere(f"Dust{k}", g.uniform(0.04, 0.1), (g.uniform(-0.9, 0.9), g.uniform(-0.9, 0.6), 0.0), flour, seg=10, rings=4, scale=(1.4, 1.0, 0.06))
    _fine(0.4)
    return _dims()


# ================================================================== sewing

def treadle_side(prefix, x, K):
    ir = K["iron"]
    tube(f"{prefix}Leg1", [(x, -0.75, 0.1), (x, -0.55, 1.2), (x, -0.62, 2.5)], 0.045, ir, square=True)
    tube(f"{prefix}Leg2", [(x, 0.75, 0.1), (x, 0.55, 1.2), (x, 0.62, 2.5)], 0.045, ir, square=True)
    tube(f"{prefix}Foot", [(x, -0.85, 0.08), (x, 0.85, 0.08)], 0.06, ir, square=True, poly=True)
    tube(f"{prefix}Top", [(x, -0.65, 2.48), (x, 0.65, 2.48)], 0.04, ir, square=True, poly=True)
    hoop(f"{prefix}Ring", (x, 0, 1.5), 0.32, "X", ir, thick=0.03)
    for k, (dy, dz) in enumerate(((0, 0.2), (0, -0.2), (0.2, 0), (-0.2, 0))):
        hoop(f"{prefix}Lobe{k}", (x, dy, 1.5 + dz), 0.12, "X", ir, thick=0.018)
    for sy in (-1, 1):
        tube(f"{prefix}Scroll{sy}", [(x, sy * 0.3, 1.82), (x, sy * 0.5, 2.1), (x, sy * 0.6, 2.4)], 0.025, ir)
        tube(f"{prefix}ScrollLo{sy}", [(x, sy * 0.3, 1.2), (x, sy * 0.55, 0.85), (x, sy * 0.75, 0.15)], 0.025, ir)


def treadle_sewing_machine(M):
    """An iron treadle stand (table top 2.6), the treadle plate and big wheel, a belt up to a black-japanned machine with gilt decals."""
    K = kit(M)
    ir = K["iron"]
    W = 3.2
    for sx in (-1, 1):
        treadle_side(f"S{sx}", sx * (W / 2 - 0.3), K)
    tube("Stretcher", [(-(W / 2 - 0.3), 0.55, 0.6), (W / 2 - 0.3, 0.55, 0.6)], 0.035, ir, poly=True)
    # the treadle: a lattice plate on a pivot rod
    tube("Pivot", [(-(W / 2 - 0.3), 0, 0.35), (W / 2 - 0.3, 0, 0.35)], 0.025, ir, poly=True)
    box("Treadle", (1.8, 0.9, 0.05), (0, -0.1, 0.38), ir, bevel=0.015, rot=(-0.12, 0, 0))
    for k in range(5):
        box(f"Slot{k}", (1.5, 0.05, 0.02), (0, -0.4 + k * 0.15, 0.41 - 0.12 * (-0.4 + k * 0.15) * 0.5), K["groove"], bevel=0.0, rot=(-0.12, 0, 0))
    xw = W / 2 - 0.45
    hoop("Wheel", (xw, 0.0, 1.35), 0.55, "X", ir, thick=0.04)
    for k in range(6):
        a = k / 6 * math.pi
        tube(f"Spoke{k}", [(xw, -math.cos(a) * 0.55, 1.35 - math.sin(a) * 0.55), (xw, math.cos(a) * 0.55, 1.35 + math.sin(a) * 0.55)], 0.02, ir, poly=True)
    cyl("Hub", 0.08, 0.12, (xw, 0, 1.35), ir, rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    tube("Pitman", [(xw - 0.08, 0.3, 1.2), (xw - 0.1, -0.2, 0.42)], 0.02, ir, poly=True)
    # the table
    top = 2.6
    box("Top", (W, 1.6, 0.12), (0, 0, top - 0.06), K["darkoak"], bevel=0.03)
    box("Drawer", (0.7, 0.9, 0.3), (-(W / 2 - 0.55), 0.0, top - 0.27), K["darkoak"], bevel=0.02)
    cyl("DrawerKnob", 0.04, 0.05, (-(W / 2 - 0.55), -0.47, top - 0.27), K["brassf"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
    box("Cover", (1.8, 0.8, 0.02), (0.1, 0.0, top + 0.01), K["ebony"], bevel=0.005)
    # the machine: bed, pillar, arm, head
    black = material("Japanning", base=(0.012, 0.011, 0.013), rough=0.14, wear=0.2, dirt=0.6)
    x0 = 0.1
    box("Bed", (1.6, 0.7, 0.12), (x0, 0.0, top + 0.08), black, bevel=0.025)
    box("NeedlePlate", (0.24, 0.3, 0.012), (x0 - 0.45, -0.08, top + 0.145), K["steel"], bevel=0.003)
    box("Pillar", (0.32, 0.38, 0.75), (x0 + 0.55, 0.05, top + 0.52), black, bevel=0.06)
    B34.pbox("Arm", (1.2, 0.3, 0.26), (0, 0, 0), K["p8"], {"front": "K8_Machine_Decal", "back": "K8_Machine_Decal", "else": "sw:K8_black"}, k=2.0,
             mtx=T(x0 + 0.05, 0.05, top + 0.86))
    box("Head", (0.3, 0.32, 0.55), (x0 - 0.5, 0.05, top + 0.68), black, bevel=0.06)
    cyl("NeedleBar", 0.02, 0.22, (x0 - 0.55, -0.08, top + 0.32), K["steel"], verts=8, bevel=0.003)
    cyl("Needle", 0.006, 0.08, (x0 - 0.55, -0.08, top + 0.18), K["steel"], verts=6, bevel=0.0)
    box("PresserFoot", (0.06, 0.12, 0.02), (x0 - 0.55, -0.08, top + 0.16), K["steel"], bevel=0.004)
    cyl("FaceDisc", 0.1, 0.02, (x0 - 0.66, 0.05, top + 0.75), K["brassf"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.004)
    # the hand wheel and belt down to the stand's wheel
    cyl("HandWheel", 0.25, 0.08, (x0 + 0.75, 0.05, top + 0.85), K["brassf"], rot=(0, math.pi / 2, 0), verts=32, bevel=0.01)
    hoop("HandWheelRim", (x0 + 0.8, 0.05, top + 0.85), 0.25, "X", black, thick=0.02)
    belt = flat("Belt", (0.25, 0.15, 0.08), 0.7)
    tube("Belt", [(x0 + 0.75, 0.3, top + 0.85), (xw, 0.55, 1.35)], 0.012, belt, poly=True)
    tube("Belt2", [(x0 + 0.75, -0.2, top + 0.85), (xw, -0.55, 1.35)], 0.012, belt, poly=True)
    # spool, bobbin, a scrap of fabric under the foot
    cyl("SpoolPin", 0.01, 0.2, (x0 + 0.2, 0.05, top + 1.07), K["steel"], verts=6, bevel=0.0)
    thread = flat("Thread", (0.5, 0.05, 0.08), 0.6)
    lathe("Spool", [(0, 0), (0.06, 0), (0.06, 0.02), (0.045, 0.03), (0.045, 0.13), (0.06, 0.14), (0.06, 0.16), (0, 0.16)], K["oak"], seg=16,
          loc=(x0 + 0.2, 0.05, top + 0.99))
    cyl("SpoolThread", 0.05, 0.1, (x0 + 0.2, 0.05, top + 1.07), thread, verts=16, bevel=0.0)
    tube("ThreadRun", [(x0 + 0.2, 0.0, top + 1.07), (x0 - 0.3, -0.12, top + 1.0), (x0 - 0.55, -0.1, top + 0.4)], 0.003, thread)
    B34.sheet("Scrap", "K8_Fabric_Plaid", 0.8, 0.6, T(x0 - 0.45, -0.25, top + 0.15) @ RZ(0.2), K["p8"], curl=0.02, nu=6, nv=5)
    return _dims()


DF_PROFILE = [(0, 0.0), (0.04, 0.0), (0.06, 0.04), (0.42, 0.06), (0.48, 0.3), (0.45, 0.6), (0.38, 0.9), (0.4, 1.15), (0.46, 1.4), (0.44, 1.58), (0.32, 1.72),
              (0.16, 1.8), (0.08, 1.84), (0.08, 1.95), (0.1, 2.0), (0, 2.02)]


def dress_form(M):
    """A dressmaker's form (shoulders at 5.0) on an iron tripod, a half-made bodice and skirt pinned on its left side, a tape measure
    over its shoulders."""
    K = kit(M)
    ir = K["iron"]
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in ((0.05, 0.6), (0.4, 0.3), (0.75, 0.08), (0.85, 0.12))], 0.035, ir, square=True)
        sphere(f"Caster{k}", 0.06, (c * 0.82, s_ * 0.82, 0.06), K["brass"], seg=8, rings=4)
    lathe("Pole", [(0, 0.5), (0.06, 0.5), (0.045, 0.7), (0.035, 3.0), (0, 3.0)], ir, seg=14)
    hoop("Collar", (0, 0, 1.8), 0.05, "Z", K["brass"], thick=0.015)
    cyl("Knob", 0.04, 0.12, (0.07, 0, 1.8), K["brass"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.01)
    z0 = 2.95
    linen_form = material("FormLinen", "NH_Leather", tint=(0.55, 0.5, 0.42), scale=5.0, normal=0.4, rough_add=0.2, wear=0.0)
    lathe("Form", DF_PROFILE, linen_form, seg=40, loc=(0, 0, z0), scale=(1.0, 0.68))
    form = P.PARTS[-1]
    lathe("Neck", [(0, 0), (0.1, 0), (0.12, 0.05), (0.12, 0.1), (0, 0.12)], K["ebony"], seg=20, loc=(0, 0, z0 + 2.02))
    hoop("Waist", (0, 0, z0 + 0.92), 0.385, "Z", ir, thick=0.01)
    P.PARTS[-1].scale = (1, 0.68, 1)
    # the half garment: crimson cloth draped down the form's left half from pins at the shoulder and the waist
    garm = B34.uv_fabric("DressDamask", "NH_Damask", (0.16, 0.012, 0.02), 1.2, band=(0.55, 0.47, 0.34))
    cols = B34.collider_copies([form])
    W_, L_ = 1.3, 2.2
    bodice = B34.grid_cloth("Garment", [(-W_ / 2, 0), (W_ / 2, 0), (W_ / 2 + 0.35, -L_), (-W_ / 2 - 0.2, -L_)], 0.07, garm, Matrix.Identity(4),
                            band=lambda x, y: 1.0 if y < -L_ + 0.12 else 0.0)
    vg = bodice.vertex_groups.new(name="Pin")
    vg.add([v.index for v in bodice.data.vertices if v.co.y > -0.08], 1.0, "REPLACE")

    def form_r(z):
        for (r0, a0), (r1, a1) in zip(DF_PROFILE, DF_PROFILE[1:]):
            if a0 <= z <= a1 and a1 > a0:
                return r0 + (r1 - r0) * (z - a0) / (a1 - a0)
        return 0.3
    # wrap the flat pattern round the form's left half, from the centre front round to the back, standing off it a little
    for v in bodice.data.vertices:
        x, y = v.co.x, v.co.y
        z = 1.72 + y
        R = form_r(max(0.0, z)) + 0.05 + 0.08 * max(0.0, -y - 1.0)
        th = -math.pi / 2 - (x + W_ / 2 + 0.2) / (W_ + 0.55) * math.pi * 0.62
        v.co = Vector((math.cos(th) * R, math.sin(th) * R * 0.68 - 0.02, z0 + z))
    for c in cols:
        bpy.data.objects.remove(c)
    B34.finish_cloth([bodice], 0.02)
    # pins in a line down the front edge
    for k in range(7):
        z = z0 + 1.6 - k * 0.22
        r = 0.46 if k < 2 else 0.4
        sphere(f"PinHead{k}", 0.022, (0.05, -r * 0.68 - 0.04, z), flat("PinRed", (0.3, 0.02, 0.03), 0.3), seg=8, rings=4)
    # the tape measure over the shoulders
    tape = flat("Tape", (0.66, 0.58, 0.32), 0.6)
    strip("Tape", [(-0.42, -0.2, z0 + 0.9), (-0.42, -0.25, z0 + 1.55), (-0.25, -0.1, z0 + 1.78), (0.25, -0.1, z0 + 1.78), (0.42, -0.25, z0 + 1.55),
                   (0.44, -0.2, z0 + 1.05)], 0.06, (1, 0, 0), tape, thick=0.004)
    return _dims()


def fabric_bolts(M):
    """A sloping wooden rack of fabric bolts (5.0 wide, 4.4 tall), two rows, one bolt unrolled down the front."""
    K = kit(M)
    rnd = random.Random(3809)
    wd = K["darkoak"]
    W, D, H = 5.0, 2.0, 4.4
    for sx in (-1, 1):
        x = sx * W / 2
        B20.tprism(f"Side{sx}", [(-D / 2, 0), (D / 2, 0), (D / 2, H), (D / 2 - 0.5, H)], x, 0.12, wd, plane="YZ")
    box("Back", (W, 0.06, H - 0.2), (0, D / 2 - 0.05, H / 2), wd, bevel=0.01)
    box("Kick", (W, 0.3, 0.3), (0, -D / 2 + 0.15, 0.15), wd, bevel=0.02)
    keys = ["Plaid", "Pinstripe", "Check", "Dots", "Moths", "Ticking"]
    ang = math.atan2(H, D - 0.5)
    for row, (z0, y0) in enumerate(((0.35, -0.6), (2.15, 0.15))):
        box(f"Ledge{row}", (W, 0.5, 0.06), (0, y0, z0 - 0.03), wd, bevel=0.01, rot=(-0.12, 0, 0))
        n = 7
        for k in range(n):
            x = -W / 2 + 0.38 + k * (W - 0.76) / (n - 1)
            key = keys[(k + row * 3) % len(keys)]
            h = rnd.uniform(1.4, 1.7)
            B34.pbox(f"Bolt{row}{k}", (0.6, 0.2, h), (0, 0, 0), K["p8"], {"front": f"K8_Fabric_{key}", "back": f"K8_Fabric_{key}", "left": f"K8_Fabric_{key}",
                                                                          "right": f"K8_Fabric_{key}", "else": "sw:K8_board"}, k=1.2,
                     mtx=T(x, y0 + 0.05, z0 + h / 2 * 0.98) @ RX(-0.3) @ RZ(rnd.uniform(-0.05, 0.05)))
    # an unrolled length off the lower row down to the floor
    B34.sheet("Length", "K8_Fabric_Moths", 0.58, 1.6, T(0.6, -1.05, 0.02) @ RZ(0.1), K["p8"], curl=0.01, nu=5, nv=12)
    sc = material("Scissors", base=(0.55, 0.56, 0.58), rough=0.2, metal=1.0)
    for sx in (-1, 1):
        tube(f"Blade{sx}", [(1.6, -1.3, 0.62), (1.6 + 0.35, -1.3 + sx * 0.04, 0.62)], 0.012, sc, poly=True)
        hoop(f"Bow{sx}", (1.5, -1.3 + sx * 0.06, 0.62), 0.05, "Z", K["ink"], thick=0.012)
    return _dims()


# ================================================================== photography

def bellows_camera(M):
    """A wooden field camera on a tripod (lens centre at 4.6): front standard with a brass lens, leather bellows, the rear standard and
    ground glass; brass fittings."""
    K = kit(M)
    wd = K["oak"]
    br = K["brassf"]
    zt = 4.0
    for k in range(3):
        a = k / 3 * 2 * math.pi - math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.12, s_ * 0.12, zt - 0.1), (c * 1.25, s_ * 1.25, 0.05)], 0.05, wd, square=True, poly=True)
        tube(f"LegIn{k}", [(c * 0.18, s_ * 0.18, zt - 0.3), (c * 0.9, s_ * 0.9, 1.2)], 0.025, wd, square=True, poly=True)
        cone(f"Spike{k}", 0.04, 0.0, 0.12, (c * 1.27, s_ * 1.27, 0.03), br, verts=8, rot=(0, 0, 0))
        cyl(f"Clamp{k}", 0.06, 0.12, (c * 0.55, s_ * 0.55, 2.6), br, verts=10, bevel=0.01)
    cyl("Head", 0.3, 0.12, (0, 0, zt), wd, verts=24, bevel=0.02)
    hoop("HeadRing", (0, 0, zt), 0.3, "Z", br, thick=0.015)
    # the camera, facing -Y
    zc = zt + 0.6
    box("Rail", (0.5, 1.6, 0.08), (0, 0.1, zt + 0.1), wd, bevel=0.015)
    box("Front", (0.9, 0.12, 0.9), (0, -0.55, zc), wd, bevel=0.02)
    box("Rear", (1.0, 0.18, 1.0), (0, 0.7, zc), wd, bevel=0.02)
    box("Glass", (0.8, 0.02, 0.8), (0, 0.8, zc), material("GroundGlass", base=(0.08, 0.08, 0.075), rough=0.4, wear=0.0), bevel=0.0)
    for sx in (-1, 1):
        box(f"FrontStrut{sx}", (0.06, 0.06, 0.6), (sx * 0.4, -0.55, zt + 0.35), br, bevel=0.01)
        box(f"RearStrut{sx}", (0.06, 0.06, 0.6), (sx * 0.45, 0.7, zt + 0.35), br, bevel=0.01)
        for sz in (-1, 1):
            sphere(f"Corner{sx}{sz}", 0.03, (sx * 0.5, 0.6, zc + sz * 0.5), br, seg=8, rings=4)
    # bellows: square frames shrinking toward the lens, folds alternately in and out
    leather = material("BellowsLeather", "NH_Leather", tint=(0.04, 0.035, 0.035), scale=3.0, normal=0.5, wear=0.2)
    bm = bmesh.new()
    rings = []
    n = 12
    for i in range(n + 1):
        t = i / n
        y = -0.48 + t * 1.08
        hw = 0.33 + 0.12 * t + (0.04 if i % 2 else 0.0)
        rings.append([bm.verts.new((x, y, zc + z)) for x, z in ((-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw))])
    for A, B in zip(rings, rings[1:]):
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((A[k], A[j], B[j], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, 0, c.z - zc))) < 0:
            f.normal_flip()
    B34.mesh_obj("Bellows", bm, leather)
    # the lens
    s = _mark()
    lathe("Lens", [(0, 0), (0.22, 0), (0.24, 0.04), (0.2, 0.1), (0.18, 0.3), (0.2, 0.34), (0.15, 0.36), (0.14, 0.33), (0, 0.33)], br, seg=32)
    cyl("LensGlass", 0.13, 0.01, (0, 0, 0.345), material("LensGlass", base=(0.04, 0.05, 0.07), rough=0.05, metal=0.3), verts=24, bevel=0.0)
    hoop("LensRing", (0, 0, 0.2), 0.19, "Z", K["ink"], thick=0.012)
    _xform(s, T(0, -0.6, zc) @ RX(math.pi / 2))
    box("Plate", (0.4, 0.02, 0.1), (0, -0.62, zc + 0.36), br, bevel=0.004)
    # a dark cloth hanging over the back
    tube("Cable", [(0.45, -0.55, zc + 0.2), (0.7, -0.4, zc - 0.3), (0.75, -0.2, zc - 0.6), (0.6, 0.0, zc - 0.7)], 0.01, K["ink"])
    sphere("Bulb", 0.06, (0.6, 0.0, zc - 0.72), K["rubber"], seg=10, rings=5, scale=(1, 1, 1.4))
    return _dims()


def darkroom_trays(M):
    """A darkroom bench (top 3.0): three enamel trays labelled DEVELOPER, STOP BATH and FIXER, a line of prints pegged above, tongs, a
    brown bottle, a red safelight on the back board (Glow: its lens)."""
    K = kit(M)
    W, D, top = 6.0, 2.2, 3.0
    wd = K["ebony"]
    box("Top", (W, D, 0.14), (0, 0, top - 0.07), K["darkoak"], bevel=0.03)
    box("Lip", (W, 0.06, 0.14), (0, -D / 2 + 0.03, top + 0.05), wd, bevel=0.01)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.14, D - 0.2, top - 0.14), (sx * (W / 2 - 0.1), 0, (top - 0.14) / 2), wd, bevel=0.02)
    box("Shelf", (W - 0.3, D - 0.4, 0.06), (0, 0.1, 0.6), wd, bevel=0.01)
    box("Back", (W, 0.1, 3.2), (0, D / 2 - 0.05, top + 1.6), wd, bevel=0.02)
    enamel_w = flat("TrayEnamel", (0.75, 0.73, 0.68), 0.2)
    chem = [flat("Developer", (0.05, 0.05, 0.03), 0.04), flat("StopBath", (0.25, 0.2, 0.05), 0.04), flat("Fixer", (0.1, 0.1, 0.08), 0.04)]
    for k, (x, lab) in enumerate(((-1.8, "K8_Tray_DEVELOPER"), (0.0, "K8_Tray_STOP"), (1.8, "K8_Tray_FIXER"))):
        tw, td, th = 1.4, 1.1, 0.22
        box(f"TrayBase{k}", (tw, td, 0.03), (x, -0.15, top + 0.015), enamel_w, bevel=0.01)
        for nm, sz, loc in ((f"TrayF{k}", (tw, 0.03, th), (x, -0.15 - td / 2, top + th / 2)), (f"TrayB{k}", (tw, 0.03, th), (x, -0.15 + td / 2, top + th / 2)),
                            (f"TrayL{k}", (0.03, td, th), (x - tw / 2, -0.15, top + th / 2)), (f"TrayR{k}", (0.03, td, th), (x + tw / 2, -0.15, top + th / 2))):
            box(nm, sz, loc, enamel_w, bevel=0.01)
        box(f"Liquid{k}", (tw - 0.06, td - 0.06, 0.01), (x, -0.15, top + 0.1), chem[k], bevel=0.0)
        B30.plate(f"Label{k}", lab, 0.7, 0.21, 0.008, T(x, -0.15 - td / 2 - 0.02, top + 0.11), K["p8"], edge="K8_paper", k=2.0)
    # a print in the developer, tongs across the stop bath
    B34.pbox("PrintIn", (0.55, 0.7, 0.006), (0, 0, 0), K["p8"], {"top": "K8_Photo_Raven", "else": "sw:K8_paper"}, k=1.8, mtx=T(-1.8, -0.15, top + 0.095) @ RZ(0.2))
    bamboo = flat("Tongs", (0.6, 0.5, 0.3), 0.6)
    for sx in (-1, 1):
        tube(f"Tong{sx}", [(-0.3, -0.15 + sx * 0.03, top + 0.25), (0.4, -0.15 + sx * 0.06, top + 0.23)], 0.015, bamboo, poly=True)
    # the line of prints
    zl = top + 2.6
    tube("Line", [(-W / 2 + 0.2, -0.2, zl), (W / 2 - 0.2, -0.2, zl)], 0.008, flat("Line", (0.5, 0.45, 0.4), 0.8), poly=True)
    for sx in (-1, 1):
        tube(f"LineHook{sx}", [(sx * (W / 2 - 0.2), D / 2 - 0.1, zl), (sx * (W / 2 - 0.2), -0.2, zl)], 0.02, K["iron"], poly=True)
    for k, key in enumerate(("K8_Photo_Tower", "K8_Photo_Tree", "K8_Photo_Face", "K8_Photo_Raven", "K8_Photo_Tower")):
        x = -2.2 + k * 1.1
        B34.wall_sheet(f"Print{k}", key, 0.64, 0.8, T(x, -0.2, zl - 0.45) @ RY((k - 2) * 2 * DEG), K["p8"], curl=0.03)
        box(f"Peg{k}", (0.04, 0.05, 0.14), (x, -0.22, zl - 0.03), K["oak"], bevel=0.008)
    # a brown bottle and a measuring cylinder
    lathe("Bottle", [(0, 0), (0.14, 0), (0.15, 0.04), (0.15, 0.42), (0.08, 0.52), (0.05, 0.56), (0.05, 0.64), (0, 0.64)], M["glassamber"],
          seg=18, loc=(2.6, 0.6, top))
    cyl("BottleCap", 0.055, 0.06, (2.6, 0.6, top + 0.66), K["ink"], verts=12, bevel=0.01)
    # the safelight: an iron box with a red lens
    box("LampBox", (0.7, 0.3, 0.55), (0, D / 2 - 0.25, top + 1.6), K["iron"], bevel=0.03)
    box("LampHood", (0.8, 0.4, 0.06), (0, D / 2 - 0.27, top + 1.9), K["iron"], bevel=0.015)
    tube("LampCord", [(0.3, D / 2 - 0.12, top + 1.6), (0.6, D / 2 - 0.12, top + 1.2), (0.8, D / 2 - 0.12, top + 0.2)], 0.012, K["ink"])
    set_group("Glow")
    box("Lens", (0.55, 0.03, 0.4), (0, D / 2 - 0.41, top + 1.6), flat("SafelightRed", (0.6, 0.02, 0.01), 0.2), bevel=0.01)
    set_group("Main")
    return _dims()


# ================================================================== woodshop

def wood_lathe(M):
    """A cast-iron lathe bed on a heavy oak bench (bed top 3.3): headstock with a stepped pulley, tailstock, a tool rest and a half-turned
    spindle, a belt to a flywheel under the bench, shavings."""
    K = kit(M)
    ir = K["iron"]
    W, D = 6.0, 1.8
    top = 2.7
    wd = K["darkoak"]
    box("Bench", (W, D, 0.2), (0, 0, top - 0.1), wd, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Leg{sx}{sy}", (0.25, 0.25, top - 0.2), (sx * (W / 2 - 0.25), sy * (D / 2 - 0.2), (top - 0.2) / 2), wd, bevel=0.02)
        box(f"Stretch{sx}", (0.15, D - 0.3, 0.15), (sx * (W / 2 - 0.25), 0, 0.5), wd, bevel=0.015)
    box("ShelfLow", (W - 0.5, D - 0.3, 0.08), (0, 0, 0.6), wd, bevel=0.01)
    # the bed: two iron ways on end stands
    zb = top + 0.4
    for sy in (-1, 1):
        box(f"Way{sy}", (4.6, 0.14, 0.16), (0.2, sy * 0.13, zb), ir, bevel=0.02)
    for x in (-2.0, 2.4):
        B20.tprism(f"Stand{x}", [(-0.45, 0), (0.45, 0), (0.3, 0.32), (-0.3, 0.32)], x, 0.18, ir, plane="YZ")
        P.PARTS[-1].location.z = top
    # headstock
    box("Head", (0.8, 0.6, 0.8), (-2.0, 0, zb + 0.5), ir, bevel=0.05)
    for k, r in enumerate((0.3, 0.24, 0.18)):
        cyl(f"Pulley{k}", r, 0.1, (-2.48 - k * 0.1, 0, zb + 0.55), ir, rot=(0, math.pi / 2, 0), verts=24, bevel=0.01)
    cyl("Spindle", 0.06, 0.4, (-1.45, 0, zb + 0.55), K["steel"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.005)
    cyl("Drive", 0.12, 0.08, (-1.25, 0, zb + 0.55), K["steel"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.008)
    # tailstock
    box("Tail", (0.5, 0.5, 0.55), (1.8, 0, zb + 0.4), ir, bevel=0.04)
    cyl("Quill", 0.05, 0.5, (1.45, 0, zb + 0.55), K["steel"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.005)
    cone("Centre", 0.05, 0.0, 0.1, (1.15, 0, zb + 0.55), K["steel"], verts=12, rot=(0, -math.pi / 2, 0))
    hoop("TailWheel", (2.1, 0, zb + 0.55), 0.18, "X", ir, thick=0.02)
    tube("TailHandle", [(2.12, 0.0, zb + 0.73), (2.3, 0.0, zb + 0.73)], 0.02, K["darkoak"], poly=True)
    # the spindle being turned: a blank with beads and coves
    prof = [(0, 0)]
    for i in range(1, 25):
        t = i / 24
        r = 0.16 if t > 0.55 else 0.11 + 0.035 * math.cos(t * 30) ** 2
        prof.append((r, t * 2.2))
    prof.append((0, 2.2))
    lathe("Blank", prof, K["oak"], seg=20)
    P.PARTS[-1].matrix_world = T(-1.05, 0, zb + 0.55) @ RY(math.pi / 2)
    # tool rest
    box("RestBase", (0.3, 0.6, 0.12), (0.0, -0.3, zb + 0.14), ir, bevel=0.02)
    cyl("RestPost", 0.04, 0.3, (0.0, -0.45, zb + 0.32), ir, verts=10, bevel=0.005)
    box("Rest", (0.9, 0.05, 0.05), (0.0, -0.3, zb + 0.48), ir, bevel=0.01)
    # belt to a flywheel under the bench
    hoop("Flywheel", (-2.6, -0.1, 1.2), 0.6, "X", ir, thick=0.05)
    for k in range(4):
        a = k / 4 * math.pi
        tube(f"FlySpoke{k}", [(-2.6, -0.1 - math.cos(a) * 0.6, 1.2 - math.sin(a) * 0.6), (-2.6, -0.1 + math.cos(a) * 0.6, 1.2 + math.sin(a) * 0.6)], 0.025, ir,
             poly=True)
    belt = flat("LatheBelt", (0.22, 0.13, 0.07), 0.7)
    tube("Belt1", [(-2.58, 0.2, zb + 0.55), (-2.6, 0.45, 1.25)], 0.015, belt, poly=True)
    tube("Belt2", [(-2.58, -0.2, zb + 0.55), (-2.6, -0.7, 1.15)], 0.015, belt, poly=True)
    # gouges on the bench, shavings
    for k, (x, y) in enumerate(((0.9, -0.6), (1.1, -0.65), (2.3, -0.55))):
        s = _mark()
        cyl(f"GougeBlade{k}", 0.018, 0.4, (0, 0, 0.2), K["steel"], verts=8, bevel=0.003)
        lathe(f"GougeHandle{k}", [(0, 0), (0.03, 0), (0.04, 0.1), (0.035, 0.32), (0, 0.34)], K["oak"], seg=12, loc=(0, 0, -0.34))
        _xform(s, T(x, y, top + 0.04) @ RZ(80 * DEG + k * 0.1) @ RY(90 * DEG))
    g = random.Random(3812)
    shav = flat("Shavings", (0.62, 0.45, 0.28), 0.8)
    for k in range(20):
        x, y = g.uniform(-1.0, 1.6), g.uniform(-0.8, 0.5)
        a = g.uniform(0, 6.28)
        pts = [(x + math.cos(a + t * 2.5) * 0.05 * (1 + t), y + math.sin(a + t * 2.5) * 0.05 * (1 + t), top + 0.01 + 0.03 * t) for t in [i / 5 for i in range(6)]]
        strip(f"Shaving{k}", pts, 0.03, (0, 0, 1), shav, thick=0.003, it=1)
    return _dims()


def tool_3d(prefix, kind, L, K, mtx):
    """A woodworking tool lying in its outline's frame (x along its length, y across, z out of the board)."""
    s = _mark()
    h = L / 2
    steel, wood = K["steel"], K["oak"]
    if kind == "saw":
        B20.tprism(f"{prefix}Blade", [(-h, 0.12), (h * 0.55, 0.16), (h * 0.55, -0.22), (-h, -0.06)], 0.0, 0.01, steel, plane="XY")
        B20.tprism(f"{prefix}Grip", [(h * 0.5, 0.2), (h, 0.2), (h, -0.26), (h * 0.5, -0.26)], 0.0, 0.06, wood, plane="XY")
    elif kind in ("hammer", "mallet"):
        cyl(f"{prefix}Handle", 0.035, L * 0.8, (-h * 0.2, 0, 0.04), wood, rot=(0, math.pi / 2, 0), verts=10, bevel=0.005)
        if kind == "hammer":
            box(f"{prefix}Head", (0.12, 0.4, 0.09), (h * 0.72, 0, 0.05), K["iron"], bevel=0.015)
        else:
            box(f"{prefix}Head", (0.36, 0.3, 0.22), (h * 0.78, 0, 0.11), K["darkoak"], bevel=0.03)
    elif kind == "square":
        box(f"{prefix}Stock", (0.12, 0.8, 0.06), (-h + 0.06, 0, 0.03), K["darkoak"], bevel=0.008)
        box(f"{prefix}Blade", (L, 0.08, 0.01), (0, -0.35, 0.005), steel, bevel=0.002)
    elif kind == "brace":
        tube(f"{prefix}Crank", [(-h, 0, 0.05), (-h * 0.6, 0, 0.05), (-h * 0.5, 0.3, 0.05), (h * 0.3, 0.3, 0.05), (h * 0.4, 0, 0.05), (h, 0, 0.05)], 0.022, steel,
             poly=True)
        cyl(f"{prefix}Pad", 0.09, 0.08, (-h, 0, 0.05), wood, rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
        cyl(f"{prefix}Grip", 0.05, 0.3, (-h * 0.1, 0.3, 0.05), wood, rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    elif kind == "chisel":
        box(f"{prefix}Blade", (h * 0.9, 0.08, 0.015), (h * 0.55, 0, 0.01), steel, bevel=0.003)
        cyl(f"{prefix}Handle", 0.04, h * 1.1, (-h * 0.45, 0, 0.045), wood, rot=(0, math.pi / 2, 0), verts=10, bevel=0.008)
    elif kind == "clamp":
        tube(f"{prefix}Frame", [(-h + 0.05, -0.3, 0.03), (-h + 0.05, 0.25, 0.03), (h - 0.05, 0.25, 0.03), (h - 0.05, -0.1, 0.03)], 0.035, K["iron"], square=True,
             poly=True)
        cyl(f"{prefix}Screw", 0.02, 0.4, (-h + 0.05, -0.1, 0.03), steel, verts=8, bevel=0.002)
        box(f"{prefix}TBar", (0.3, 0.04, 0.04), (-h + 0.2, -0.3, 0.03), steel, bevel=0.005)
    elif kind == "plane":
        B20.tprism(f"{prefix}Body", [(-h, -0.12), (h, -0.12), (h * 0.8, 0.1), (-h * 0.8, 0.1)], 0.0, 0.18, K["darkoak"], plane="XY")
        B20.tprism(f"{prefix}Tote", [(-h * 0.2, 0.1), (h * 0.2, 0.1), (h * 0.1, 0.28), (-h * 0.3, 0.28)], 0.03, 0.12, K["darkoak"], plane="XY")
        box(f"{prefix}Iron", (0.1, 0.2, 0.15), (h * 0.3, 0, 0.18), steel, bevel=0.01)
    elif kind == "rasp":
        box(f"{prefix}File", (L * 0.65, 0.09, 0.03), (h * 0.35 - h * 0.0, 0, 0.02), K["ironf"], bevel=0.005)
        cyl(f"{prefix}Handle", 0.04, L * 0.35, (-h * 0.65, 0, 0.04), wood, rot=(0, math.pi / 2, 0), verts=10, bevel=0.008)
    _xform(s, mtx)


def tool_wall(M):
    """A pegboard of woodworking tools (6.0 x 3.6, in an oak frame, back on the wall at y = 0, its foot at z = 0.4): each tool hangs over
    its painted outline; three outlines stand empty."""
    K = kit(M)
    BW, BH = B37.KA["board"]
    zc = 0.4 + BH / 2
    B30.plate("Board", "K8_Pegboard", BW, BH, 0.06, T(0, -0.05, zc), K["p8"], edge="K8_board", k=2.6)
    for nm, sz, loc in (("FrameT", (BW + 0.3, 0.14, 0.15), (0, -0.07, zc + BH / 2 + 0.07)), ("FrameB", (BW + 0.3, 0.14, 0.15), (0, -0.07, zc - BH / 2 - 0.07)),
                        ("FrameL", (0.15, 0.14, BH), (-BW / 2 - 0.07, -0.07, zc)), ("FrameR", (0.15, 0.14, BH), (BW / 2 + 0.07, -0.07, zc))):
        box(nm, sz, loc, K["darkoak"], bevel=0.03)
    box("Ledge", (BW + 0.3, 0.4, 0.06), (0, -0.25, 0.4 - 0.15), K["darkoak"], bevel=0.015)
    for k, (kind, x, z, L, ang, present) in enumerate(B37.TOOLS):
        if not present:
            continue
        a = math.radians(ang)
        frame = T(x, -0.08, zc + z) @ Matrix(((math.cos(a), -math.sin(a), 0, 0), (0, 0, -1, 0), (math.sin(a), math.cos(a), 0, 0), (0, 0, 0, 1)))
        tool_3d(f"T{k}", kind, L, K, frame)
        # two pegs holding it
        for t in (-0.25, 0.25):
            px, pz = x + math.cos(a) * L * t, z + math.sin(a) * L * t
            cyl(f"Peg{k}{t}", 0.012, 0.12, (px, -0.11, zc + pz + 0.06), K["steel"], rot=(math.pi / 2, 0, 0), verts=6, bevel=0.0)
    return _dims()


def sawhorse(M):
    """A pair of sawhorses (2.4 tall) with a long plank across them, a handsaw on it and sawdust under."""
    K = kit(M)
    wd = K["oak"]
    g = random.Random(3814)
    for k, x in enumerate((-2.2, 2.2)):
        s = _mark()
        box(f"Beam{k}", (0.25, 3.0, 0.22), (0, 0, 2.29), wd, bevel=0.02)
        for sy in (-1, 1):
            for sx in (-1, 1):
                tube(f"Leg{k}{sy}{sx}", [(sx * 0.1, sy * 1.2, 2.2), (sx * 0.65, sy * 1.4, 0.0)], 0.08, wd, square=True, poly=True)
            tube(f"Brace{k}{sy}", [(-0.5, sy * 1.37, 0.5), (0.5, sy * 1.37, 0.5)], 0.05, wd, square=True, poly=True)
        box(f"Tray{k}", (0.9, 1.8, 0.05), (0, 0, 0.62), wd, bevel=0.01)
        _xform(s, T(x, 0, 0) @ RZ(g.uniform(-0.05, 0.05)))
    box("Plank", (6.5, 1.0, 0.16), (0, -0.4, 2.48), K["darkoak"], bevel=0.02, rot=(0, 0, 0.03))
    s = _mark()
    tool_3d("Saw", "saw", 2.0, K, Matrix.Identity(4))
    _xform(s, T(0.4, -0.5, 2.565) @ RZ(0.2))
    for k in range(3):
        cyl(f"Pencil{k}", 0.02, 0.4, (-1.5 + k * 0.1, -0.7, 2.58), flat("CarpPencil", (0.6, 0.45, 0.1), 0.6), rot=(0, math.pi / 2, 0.3 * k), verts=6, bevel=0.003) \
            if k == 0 else None
    dust = flat("Sawdust", (0.42, 0.28, 0.15), 0.95)
    for k in range(9):
        sphere(f"Dust{k}", g.uniform(0.15, 0.35), (g.uniform(-0.8, 1.6), g.uniform(-0.9, 0.3), 0.0), dust, seg=12, rings=5, scale=(1.3, 1.0, 0.12))
    return _dims()


# ================================================================== ceramics

def potters_wheel(M):
    """A kick wheel: an oak frame with a seat (top 1.7), a heavy flywheel at foot level, the wheel head (2.5) in a splash pan with a
    wet clay pot on it, a sponge and a water bowl."""
    K = kit(M)
    wd = K["darkoak"]
    ir = K["iron"]
    W, D = 2.6, 4.0
    for sx in (-1, 1):
        box(f"Rail{sx}", (0.18, D, 0.2), (sx * W / 2, 0, 0.12), wd, bevel=0.02)
        box(f"TopRail{sx}", (0.15, 2.2, 0.16), (sx * W / 2, -0.7, 2.2), wd, bevel=0.02)
        for y in (-1.6, 0.0):
            box(f"Post{sx}{y}", (0.16, 0.16, 2.2), (sx * W / 2, y, 1.1), wd, bevel=0.02)
        box(f"SeatPost{sx}", (0.16, 0.16, 1.6), (sx * 0.6, 1.5, 0.8), wd, bevel=0.02)
    box("Seat", (1.6, 0.9, 0.12), (0, 1.5, 1.64), wd, bevel=0.03)
    box("Cross", (W, 0.16, 0.16), (0, -1.6, 2.2), wd, bevel=0.02)
    box("CrossB", (W, 0.16, 0.16), (0, 0.0, 2.2), wd, bevel=0.02)
    box("Table", (W, 2.0, 0.08), (0, -0.8, 2.3), wd, bevel=0.015)
    # the shaft, flywheel (kicked by the potter at +Y), head
    cyl("Shaft", 0.05, 2.4, (0, -0.8, 1.25), K["steel"], verts=12, bevel=0.005)
    stone = material("FlyStone", "NH_Slate", tint=(0.28, 0.28, 0.27), scale=0.6, rough_add=0.2, wear=0.4)
    cyl("Flywheel", 0.95, 0.25, (0, -0.8, 0.45), stone, verts=40, bevel=0.03)
    hoop("FlyBand", (0, -0.8, 0.45), 0.95, "Z", ir, thick=0.04)
    cyl("Bearing", 0.12, 0.15, (0, -0.8, 0.12), ir, verts=14, bevel=0.01)
    lathe("Pan", [(0, 2.32), (0.75, 2.32), (0.8, 2.36), (0.82, 2.6), (0.78, 2.6), (0.76, 2.38), (0, 2.38)], ir, seg=40, loc=(0, -0.8, 0))
    cyl("Head", 0.55, 0.06, (0, -0.8, 2.5), material("WheelHead", base=(0.2, 0.2, 0.21), rough=0.4, metal=0.8), verts=40, bevel=0.01)
    clay = clay_mat(True)
    lathe("ClaySlurry", [(0.0, 2.535), (0.5, 2.535), (0.52, 2.545), (0, 2.545)], clay, seg=32, loc=(0, -0.8, 0))
    lathe("Vessel", [(0, 2.53), (0.3, 2.53), (0.34, 2.6), (0.36, 2.8), (0.3, 2.98), (0.22, 3.08), (0.24, 3.16), (0.21, 3.17), (0.19, 3.08), (0.26, 2.98),
                     (0.31, 2.8), (0.29, 2.62), (0, 2.6)], clay, seg=40, loc=(0, -0.8, 0), jitter=(0.006, 2))
    sp = flat("Sponge", (0.62, 0.5, 0.26), 0.9)
    box("Sponge", (0.25, 0.18, 0.1), (0.9, -1.4, 2.39), sp, bevel=0.04)
    lathe("WaterBowl", [(0, 0), (0.25, 0), (0.32, 0.2), (0.3, 0.2), (0.22, 0.03), (0, 0.03)], clay_mat(False), seg=24, loc=(-0.9, -1.5, 2.34))
    cyl("Water", 0.27, 0.01, (-0.9, -1.5, 2.5), flat("ClayWater", (0.3, 0.22, 0.17), 0.05), verts=20, bevel=0.0)
    tube("Wire", [(0.8, -0.3, 2.35), (1.0, -0.2, 2.35), (1.1, 0.0, 2.35)], 0.004, K["steel"])
    return _dims()


def kiln(M):
    """A brick-and-iron kiln (4.4 x 3.6, 5.0 to its arched top, a flue to 7.2): firebrick walls in an iron frame with tie rods, an iron
    door with a wheel latch, a spy hole, a temperature gauge."""
    K = kit(M)
    ir = K["iron"]
    W, D, H = 4.4, 3.6, 4.2
    B34.pbox("Body", (W, D, H), (0, 0, H / 2 + 0.3), K["p8"], {"else": "K8_Bricks", "bottom": "sw:K8_board"}, k=2.0)
    box("Plinth", (W + 0.3, D + 0.3, 0.3), (0, 0, 0.15), ir, bevel=0.03)
    # the arched crown
    s = _mark()
    pts = B34.seg_arc(W / 2, 0.0, 0.8, 16)
    B20.tprism("Crown", [(-W / 2, -0.01)] + pts + [(W / 2, -0.01)], 0.0, D, ir, plane="XZ")
    _xform(s, T(0, 0, H + 0.3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Angle{sx}{sy}", [(sx * (W / 2 + 0.03), sy * (D / 2 + 0.03), 0.3), (sx * (W / 2 + 0.03), sy * (D / 2 + 0.03), H + 0.4)], 0.07, ir, square=True,
                 poly=True)
    for z in (1.1, 2.6, H + 0.2):
        for sy in (-1, 1):
            tube(f"Band{z}{sy}", [(-W / 2 - 0.05, sy * (D / 2 + 0.05), z), (W / 2 + 0.05, sy * (D / 2 + 0.05), z)], 0.04, ir, square=True, poly=True)
        for sx in (-1, 1):
            tube(f"BandS{z}{sx}", [(sx * (W / 2 + 0.05), -D / 2 - 0.05, z), (sx * (W / 2 + 0.05), D / 2 + 0.05, z)], 0.04, ir, square=True, poly=True)
            for sy in (-1, 1):
                cyl(f"Nut{z}{sx}{sy}", 0.07, 0.08, (sx * (W / 2 + 0.1), sy * (D / 2 + 0.1), z), ir, verts=6, bevel=0.01)
    # the door
    yf = -D / 2 - 0.08
    box("Door", (2.2, 0.15, 2.4), (0, yf, 1.9), ir, bevel=0.04)
    tube("DoorEdge", [(-1.0, yf - 0.08, 0.8), (1.0, yf - 0.08, 0.8), (1.0, yf - 0.08, 3.0), (-1.0, yf - 0.08, 3.0)], 0.03, K["ironf"], square=True, closed=True,
         poly=True)
    for sz in (-1, 1):
        box(f"Hinge{sz}", (0.5, 0.12, 0.2), (-1.2, yf, 1.9 + sz * 0.8), ir, bevel=0.02)
    hoop("Latch", (0.6, yf - 0.15, 1.9), 0.25, "Y", ir, thick=0.03)
    for k in range(4):
        a = k / 4 * math.pi
        tube(f"LatchSpoke{k}", [(0.6 - math.cos(a) * 0.25, yf - 0.15, 1.9 - math.sin(a) * 0.25), (0.6 + math.cos(a) * 0.25, yf - 0.15, 1.9 + math.sin(a) * 0.25)],
             0.015, ir, poly=True)
    cyl("SpyHole", 0.1, 0.1, (-0.4, yf - 0.1, 2.5), K["brassf"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
    cyl("SpyPlug", 0.06, 0.12, (-0.4, yf - 0.14, 2.5), material("Ceramic", base=(0.7, 0.66, 0.6), rough=0.4), rot=(math.pi / 2, 0, 0), verts=12, bevel=0.01)
    cyl("Gauge", 0.22, 0.08, (1.6, -D / 2 - 0.08, 3.6), K["brassf"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
    cyl("GaugeFace", 0.18, 0.01, (1.6, -D / 2 - 0.125, 3.6), K["bone"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.0)
    tube("GaugeNeedle", [(1.6, -D / 2 - 0.135, 3.6), (1.68, -D / 2 - 0.135, 3.72)], 0.01, K["crimsonpaint"], poly=True)
    cyl("Flue", 0.3, 2.4, (0, 0.6, H + 0.3 + 1.6), ir, verts=20, bevel=0.01)
    lathe("FlueCap", [(0, 0.0), (0.45, 0.0), (0.0, 0.3)], ir, seg=20, loc=(0, 0.6, H + 0.3 + 2.95))
    for k in range(3):
        tube(f"CapLeg{k}", [(math.cos(k * 2.09) * 0.3, 0.6 + math.sin(k * 2.09) * 0.3, H + 2.75), (math.cos(k * 2.09) * 0.35, 0.6 + math.sin(k * 2.09) * 0.35, H + 3.27)],
             0.02, ir, poly=True)
    # kiln shelves and a stack of bisque bowls beside it
    for k in range(3):
        lathe(f"Bisque{k}", [(0, 0), (0.18, 0), (0.3, 0.18), (0.28, 0.18), (0.16, 0.03), (0, 0.03)], clay_mat(False), seg=20, loc=(2.8, -1.4, 0.0 + k * 0.05))
    return _dims()


# ================================================================== drama

# garment width profiles: (t from the shoulders 0 to the hem 1) -> half width
CAPE = (3.2, lambda t: 0.35 + 0.8 * t ** 0.8)
GOWN = (3.6, lambda t: 0.42 - 0.08 * math.sin(min(1.0, t / 0.3) * math.pi / 2) + (0.85 * ((t - 0.3) / 0.7) ** 1.2 if t > 0.3 else 0.0))
TABARD = (2.4, lambda t: 0.55 + 0.05 * t)


def pleated_cloth(name, spec, mat, mtx, key=None, band=None, nx=22, ny=30, pleat=0.07, seed=0):
    """A hanging garment: rows from the shoulders (y = 0) down to the hem (y = -L), each spanning the profile's width, pleated in
    folds that deepen toward the hem; "Spine" UV onto an atlas region (key), "Flat" UV in studs."""
    L, hw = spec
    g = random.Random(seed)
    ph = g.uniform(0, 6.28)
    bm = bmesh.new()
    uvs = bm.loops.layers.uv.new("Spine")
    uvf = bm.loops.layers.uv.new("Flat")
    vs = []
    for j in range(ny + 1):
        t = j / ny
        w = hw(t)
        row = []
        for i in range(nx + 1):
            s_ = i / nx
            x = (s_ - 0.5) * 2 * w
            z = pleat * (0.25 + t) * math.sin(s_ * 9 * math.pi + ph) + 0.02 * math.sin(t * 7 + s_ * 3)
            row.append(bm.verts.new((x, -t * L, z)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
            f.smooth = True
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                lp[uvs].uv = B34.region_uv(key, ii / nx, 1 - jj / ny) if key else (0.5, 0.5)
                lp[uvf].uv = (lp.vert.co.x, lp.vert.co.y)
    if band:
        bl = bm.verts.layers.float.new("nh_band")
        for v in bm.verts:
            v[bl] = band(v.co.x, v.co.y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = B34.mesh_obj(name, bm, mat)
    ob.matrix_world = mtx
    return ob


def costume_rack(M):
    """A rolling iron rail (6 wide, 6.4 tall, on casters) with a cape, a gown and an armour tabard on hangers, a crown and a hat on the
    shelf above."""
    K = kit(M)
    ir = K["iron"]
    W, H = 6.0, 6.2
    for sx in (-1, 1):
        x = sx * W / 2
        tube(f"Upright{sx}", [(x, 0, 0.35), (x, 0, H)], 0.05, ir, poly=True)
        tube(f"Base{sx}", [(x, -0.9, 0.35), (x, 0.9, 0.35)], 0.05, ir, poly=True)
        for sy in (-1, 1):
            cyl(f"CasterWheel{sx}{sy}", 0.14, 0.08, (x, sy * 0.85, 0.15), K["rubber"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
            box(f"CasterFork{sx}{sy}", (0.14, 0.12, 0.2), (x, sy * 0.85, 0.28), ir, bevel=0.01)
        sphere(f"Finial{sx}", 0.09, (x, 0, H + 0.08), K["brass"], seg=10, rings=5)
    tube("Rail", [(-W / 2, 0, H - 0.1), (W / 2, 0, H - 0.1)], 0.04, K["brassf"], poly=True)
    tube("Stretcher", [(-W / 2, 0, 0.6), (W / 2, 0, 0.6)], 0.035, ir, poly=True)
    rail_z = H - 0.1
    garments = [("Cape", CAPE, -1.8), ("Gown", GOWN, 0.0), ("Tabard", TABARD, 1.8)]
    mats_ = {"Cape": B34.uv_fabric("CapeVelvet", "NH_Velvet", (0.06, 0.004, 0.01), 0.8, band=(0.55, 0.47, 0.34)),
             "Gown": B34.uv_fabric("GownDamask", "NH_DamaskBat", (0.05, 0.06, 0.1), 1.0),
             "Tabard": K["p8"]}
    cloths, forms = [], []
    for name, poly, x in garments:
        tube(f"Hook{name}", [(x, 0, rail_z - 0.12), (x, 0, rail_z + 0.06), (x, 0.06, rail_z + 0.1), (x, 0.08, rail_z + 0.02)], 0.012, K["brassf"])
        tube(f"Hanger{name}", [(x - 0.75, 0, rail_z - 0.45), (x, 0, rail_z - 0.15), (x + 0.75, 0, rail_z - 0.45), (x - 0.75, 0, rail_z - 0.45)], 0.02, K["oak"],
             poly=True)
        set_group("Clothes")
        c = pleated_cloth(f"G{name}", poly, mats_[name], T(x, -0.08, rail_z - 0.42) @ RX(math.pi / 2), key="K8_Tabard" if name == "Tabard" else None,
                          band=(lambda x_, y_: 1.0 if y_ < -3.05 else 0.0) if name == "Cape" else None, pleat=0.02 if name == "Tabard" else 0.07,
                          seed=len(name))
        set_group("Main")
        vg = c.vertex_groups.new(name="Pin")
        vg.add([v.index for v in c.data.vertices if v.co.y > -0.06], 1.0, "REPLACE")
        cloths.append(c)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.1, rail_z - 1.6))
        f = bpy.context.active_object
        f.scale = (0.8 if name != "Tabard" else 0.9, 0.12, 1.8)
        bpy.ops.object.transform_apply(scale=True)
        forms.append(f)
    B34.simulate(cloths, forms + [B34.floor_collider()], frames=45, mass=0.25, stiff=10.0, bend=0.5, pin="Pin")
    B34.finish_cloth(cloths, 0.025)
    # a crown and a feathered hat on a top shelf
    return _dims()


def mask_mesh(name, mat, happy, mtx):
    """A theatre mask: a domed face shell (1.0 x 1.3) with eyes and a mouth cut through it, brows and a nose modelled on."""
    n, m = 40, 50
    bm = bmesh.new()
    grid = {}
    for i in range(n + 1):
        for j in range(m + 1):
            u, v = -1 + 2 * i / n, -1 + 2 * j / m
            if u * u + v * v > 1.0:
                continue
            x, y = u * 0.5, v * 0.65
            z = 0.32 * math.sqrt(max(0.0, 1 - u * u - v * v * 0.9))
            z += 0.12 * math.exp(-((u / 0.12) ** 2 + ((v + 0.05) / 0.3) ** 2))          # nose
            bw = 0.06 * math.exp(-(((abs(u) - 0.35) / 0.25) ** 2 + ((v - 0.32 + (0.0 if happy else 0.1 * (0.35 - abs(u)))) / 0.08) ** 2))
            z += bw
            grid[(i, j)] = bm.verts.new((x, y, z))

    def hole(u, v):
        for sx in (-1, 1):
            if ((u - sx * 0.36) / 0.16) ** 2 + ((v - 0.18 + (0.05 * sx * (u - sx * 0.36) * (-1 if happy else 1))) / 0.09) ** 2 < 1:
                return True
        if happy:
            c = (v + 0.25) - 0.9 * u * u
            return abs(u) < 0.5 and -0.12 < c + 0.05 < 0.08 and v < -0.15
        c = (v + 0.55) + 0.9 * u * u
        return abs(u) < 0.45 and -0.08 < c - 0.18 < 0.08 and v > -0.6
    for i in range(n):
        for j in range(m):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in grid for k in q):
                u, v = -1 + 2 * (i + 0.5) / n, -1 + 2 * (j + 0.5) / m
                if hole(u, v):
                    continue
                f = bm.faces.new([grid[k] for k in q])
                f.smooth = True
    # round off the stair-stepped hole edges: relax each hole's boundary loop along itself
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    for _ in range(6):
        bnd = [v for v in bm.verts if v.is_boundary and (v.co.x / 0.5) ** 2 + (v.co.y / 0.65) ** 2 < 0.8]
        new = {}
        for v in bnd:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2:
                c = (nb[0].co + nb[1].co) / 2
                new[v] = v.co * 0.4 + c * 0.6
        for v, c in new.items():
            v.co.x, v.co.y = c.x, c.y
    # the outer edge onto a clean oval
    for v in bm.verts:
        if v.is_boundary and (v.co.x / 0.5) ** 2 + (v.co.y / 0.65) ** 2 >= 0.8:
            a_ = math.atan2(v.co.y / 0.65, v.co.x / 0.5)
            v.co.x, v.co.y = math.cos(a_) * 0.5, math.sin(a_) * 0.65
            v.co.z = 0.0
    ob = B34.mesh_obj(name, bm, mat)
    _solid(ob, 0.03)
    ob.matrix_world = mtx
    return ob


def theatre_masks(M):
    """Comedy and tragedy on a black lacquered wall plaque (2.6 wide, back on the wall at y = 0): gilt masks, crimson ribbons."""
    K = kit(M)
    lac = material("PlaqueLacquer", "NH_PaintedMetal", tint=(0.02, 0.018, 0.024), scale=0.8, rough_mul=0.8, wear=0.12)
    zc = 1.0
    s = _mark()
    pts = [(math.cos(t) * 1.3, math.sin(t) * 0.95) for t in [k / 40 * 6.283 for k in range(40)]]
    B20.tprism("Plaque", [(x, z + zc) for x, z in pts], -0.05, 0.1, lac, plane="XZ")
    tube("PlaqueRim", [(math.cos(t) * 1.24, -0.105, zc + math.sin(t) * 0.9) for t in [k / 48 * 6.283 for k in range(48)]], 0.025, K["gilt"], closed=True, poly=True)
    mask_mesh("Comedy", K["gilt"], True, T(-0.45, -0.12, zc + 0.08) @ RY(-14 * DEG) @ RX(math.pi / 2))
    mask_mesh("Tragedy", material("SilverMask", base=(0.62, 0.62, 0.64), rough=0.25, metal=1.0, wear=0.25, dirt=0.8), False,
              T(0.45, -0.14, zc - 0.06) @ RY(14 * DEG) @ RX(math.pi / 2))
    rib = material("MaskRibbon", "NH_Leather", tint=(0.16, 0.012, 0.022), scale=4.0, normal=0.2, rough_add=0.2, wear=0.0)
    strip("RibbonL", [(-0.9, -0.2, zc + 0.3), (-1.05, -0.22, zc - 0.1), (-0.95, -0.2, zc - 0.5), (-1.1, -0.22, zc - 0.85)], 0.09, (1, 0, 0), rib, thick=0.006)
    strip("RibbonR", [(0.9, -0.2, zc + 0.3), (1.05, -0.22, zc - 0.1), (0.95, -0.2, zc - 0.5), (1.1, -0.22, zc - 0.85)], 0.09, (1, 0, 0), rib, thick=0.006)
    strip("RibbonTop", [(-0.9, -0.2, zc + 0.3), (-0.4, -0.3, zc + 0.75), (0.4, -0.3, zc + 0.75), (0.9, -0.2, zc + 0.3)], 0.09, (0, 1, 0), rib, thick=0.006)
    _fine(0.6)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "PottingBench": potting_bench,
    "HerbDryingRack": herb_drying_rack,
    "Terrarium": terrarium,
    "CastIronRange": cast_iron_range,
    "PotRack": pot_rack,
    "MixingBowlSet": mixing_bowl_set,
    "TreadleSewingMachine": treadle_sewing_machine,
    "DressForm": dress_form,
    "FabricBolts": fabric_bolts,
    "BellowsCamera": bellows_camera,
    "DarkroomTrays": darkroom_trays,
    "WoodLathe": wood_lathe,
    "ToolWall": tool_wall,
    "Sawhorse": sawhorse,
    "PottersWheel": potters_wheel,
    "Kiln": kiln,
    "CostumeRack": costume_rack,
    "TheatreMasks": theatre_masks,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"TheatreMasks": 1.3, "Terrarium": 1.15})
B24.SMALL.update({"MixingBowlSet": 1.3})
