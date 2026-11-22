"""Props batch 51 (2026-11-19): Wickfield Square's Main Street (docs/expansion/15-Tutorial-The-Last-Normal-Night.md §2).

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch51_square.py -- <Prop|all> [--size 2048] [--samples 64] [--gpu]

One storefront builder for every shop: two storeys (ground 11, upper 9, a bracketed cornice and parapet to 21.5); a
painted cast-iron shop front (pilasters, panelled bulkheads, display windows either side of a recessed glass door, a
transom); a striped awning with a scalloped valance (tiled awning duck); the shop's sign on the upper facade (a PBR
canvas from art/hometown/logo_canvases.py; neon signs glow); three upper windows with lintels; a lit interior seen
through the glass (its own furniture per shop). Walls are tiled (brick or clapboard).

  WFShopDiner      Moonpie Diner, 18 wide, blue clapboard, a red awning, the neon sign; inside: a counter, stools, booths
  WFShopHardware   Wick & Sons Hardware, 16 wide, brick, a green awning; inside: shelves of tools, a key-cutting bench
  WFShopVideo      Reel Time Video, 14 wide, butter clapboard, a blue awning, the lightbox; inside: tape racks, a counter
  WFShopSuds       Suds Laundromat, 14 wide, brick, a blue awning; inside: a row of washers, a folding table
  WFShopGazette    The Wickfield Gazette office, 14 wide, brick, no awning; inside: desks, a press in the back

Front faces -Y, Z up, origin at the bottom centre of the facade line (the building runs back +Y).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube, set_group, material  # noqa: E402
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import lathe, prism, _dims  # noqa: E402
from nh_props_batch49_hometown import back_out, ease  # noqa: E402
from nh_props_batch28 import solid  # noqa: E402
import nh_props_batch49_hometown as B49  # noqa: E402
from nh_props_batch49_hometown import kit, wall, wmat, _quad_uv, panel  # noqa: E402

BUILDERS = {}
SHOP_TILES = {}       # prop -> {group: (set, studs a tile)}


def storefront(M, W, walls, awning, sign, aspect, interior, front_col=(0.18, 0.3, 0.24), no_awning=False):
    K = kit(M)
    D, H1, H2, PAR = 10.0, 11.0, 9.0, 1.5
    X0, X1 = -W / 2, W / 2
    ZT = H1 + H2
    front = wmat("ShopFront", "NH_PaintedWood", front_col, 0.3, wear=0.35, dirt=0.8)
    trim = K["trim"]
    glass = K["glass"]
    # ---- the walls (tiled): the upper facade with its window holes and the sign area, the sides, the back
    set_group("Walls")
    wins = [(X0 + W * f - 1.2, X0 + W * f + 1.2, H1 + 4.5, H1 + 7.5) for f in (0.2, 0.5, 0.8)]
    wall("Upper", "y", 0.0, X0, X1, H1, ZT, 0.6, wins, K["place"])
    wall("SideL", "x", X0, 0.0, D, 0.0, ZT, 0.6, [], K["place"])
    wall("SideR", "x", X1, 0.0, D, 0.0, ZT, 0.6, [], K["place"])
    wall("Back", "y", D, X0, X1, 0.0, ZT, 0.6, [], K["place"])
    box("Parapet", (W + 0.6, 0.6, PAR), (0, 0.0, ZT + PAR / 2), K["place"], bevel=0)
    set_group("Main")
    box("Roof", (W - 0.6, D - 0.6, 0.3), (0, D / 2, ZT - 0.2), material("ShopRoof", base=(0.12, 0.12, 0.13), rough=0.9, wear=0.0), bevel=0)
    # ---- the shop front (painted cast iron and wood)
    pil = 0.9
    for x in (X0 + pil / 2, X1 - pil / 2):
        box(f"Pilaster{x}", (pil, 0.7, H1), (x, -0.15, H1 / 2), front, bevel=0.05)
        box(f"PilCap{x}", (pil + 0.3, 0.9, 0.4), (x, -0.2, H1 - 0.2), front, bevel=0.05)
        box(f"PilBase{x}", (pil + 0.2, 0.85, 0.6), (x, -0.18, 0.3), front, bevel=0.04)
        for k in range(4):                                         # flutes
            box(f"Flute{x}{k}", (0.08, 0.06, H1 - 2.0), (x - 0.3 + k * 0.2, -0.52, H1 / 2), front, bevel=0)
    box("Beam", (W, 0.8, 1.2), (0, -0.15, H1 - 0.6), front, bevel=0.05)
    box("BeamMould", (W + 0.2, 1.0, 0.25), (0, -0.2, H1 - 0.05), front, bevel=0.04)
    dw, rec = 3.4, 1.6                                              # the door width, the entry recess
    inner_x0, inner_x1 = X0 + pil, X1 - pil
    # display windows left and right of the recessed entry: bulkhead, glass, transom
    for side, (a, b) in (("L", (inner_x0, -dw / 2 - 0.3)), ("R", (dw / 2 + 0.3, inner_x1))):
        box(f"Bulk{side}", (b - a, 0.5, 2.0), ((a + b) / 2, 0.0, 1.0), front, bevel=0.04)
        for k in range(max(1, int((b - a) / 2.4))):
            n = max(1, int((b - a) / 2.4))
            cx_ = a + (k + 0.5) * (b - a) / n
            box(f"BulkPanel{side}{k}", ((b - a) / n - 0.5, 0.1, 1.2), (cx_, -0.28, 1.0), front, bevel=0.06)
        box(f"Sill{side}", (b - a, 0.8, 0.18), ((a + b) / 2, -0.15, 2.09), front, bevel=0.03)
        box(f"Muntin{side}", (b - a, 0.25, 0.15), ((a + b) / 2, 0.0, 8.0), front, bevel=0.02)
        for x in (a + 0.08, b - 0.08):
            box(f"WinPost{side}{x}", (0.16, 0.3, 7.6), (x, 0.0, 5.9), front, bevel=0.02)
        set_group("Glass")
        box(f"Display{side}", (b - a - 0.2, 0.06, 5.75), ((a + b) / 2, 0.0, 5.1), glass, bevel=0)
        box(f"Transom{side}", (b - a - 0.2, 0.06, 1.7), ((a + b) / 2, 0.0, 9.0), glass, bevel=0)
        set_group("Main")
        # the recess walls (angled returns into the entry)
    for sx in (-1, 1):
        box(f"Return{sx}", (0.3, rec, 8.2), (sx * (dw / 2 + 0.15), rec / 2, 4.1), front, bevel=0.02)
    box("EntryCeil", (dw + 0.6, rec, 0.25), (0, rec / 2, 8.3), front, bevel=0)
    box("EntryFloor", (dw + 0.6, rec + 0.4, 0.12), (0, rec / 2 - 0.2, 0.06), material("EntryTile", base=(0.75, 0.72, 0.66), rough=0.4, wear=0.2), bevel=0)
    # the door (glass, a push bar, a brass kick plate), a transom over it, the shop's number
    box("DoorFrameL", (0.25, 0.3, 7.6), (-dw / 2 + 0.12, rec, 3.8), front, bevel=0.02)
    box("DoorFrameR", (0.25, 0.3, 7.6), (dw / 2 - 0.12, rec, 3.8), front, bevel=0.02)
    box("DoorHead", (dw, 0.3, 0.3), (0, rec, 7.55), front, bevel=0.02)
    box("DoorStile", (dw - 0.5, 0.18, 0.6), (0, rec, 0.4), front, bevel=0.02)
    box("DoorKick", (dw - 0.6, 0.05, 0.5), (0, rec - 0.1, 0.4), K["brass"], bevel=0.01)
    box("DoorBar", (dw - 0.9, 0.12, 0.12), (0, rec - 0.15, 3.6), K["brass"], bevel=0.03)
    set_group("Glass")
    box("DoorGlass", (dw - 0.5, 0.05, 6.4), (0, rec, 4.0), glass, bevel=0)
    box("DoorTransom", (dw - 0.5, 0.05, 0.9), (0, rec, 8.0), glass, bevel=0)
    set_group("Main")
    # ---- the sign on the upper facade (canvas)
    sh = 3.3
    sw = min(W - 2.5, sh * aspect)
    sh = sw / aspect
    sz = H1 + 0.4 + sh / 2 + 0.25
    box("SignBack", (sw + 0.4, 0.2, sh + 0.4), (0, -0.4, sz), front, bevel=0.05)
    set_group("Sign")
    box("Sign", (sw, 0.04, sh), (0, -0.52, sz), K["place"], bevel=0)
    set_group("Main")
    for x in (-sw / 2 + 0.3, sw / 2 - 0.3):
        box(f"SignBracket{x}", (0.12, 0.4, 0.12), (x, -0.3, sz + sh / 2 + 0.25), K["iron"], bevel=0.01)
    # ---- the upper windows: frames, sashes, lintels and sills
    for k, (a, b, z0, z1) in enumerate(wins):
        c = (a + b) / 2
        box(f"Lintel{k}", (b - a + 0.8, 0.5, 0.45), (c, -0.18, z1 + 0.22), material("Stone", "NH_Limestone", tint=(0.86, 0.83, 0.78), scale=0.3, wear=0.3, dirt=0.9), bevel=0.04)
        box(f"USill{k}", (b - a + 0.6, 0.7, 0.2), (c, -0.25, z0 - 0.1), material("Stone", "NH_Limestone", tint=(0.86, 0.83, 0.78), scale=0.3, wear=0.3, dirt=0.9), bevel=0.03)
        for x in (a + 0.08, b - 0.08):
            box(f"UFrame{k}{x}", (0.16, 0.3, z1 - z0), (x, 0.0, (z0 + z1) / 2), trim, bevel=0.01)
        box(f"UMeet{k}", (b - a, 0.25, 0.14), (c, 0.0, (z0 + z1) / 2), trim, bevel=0.01)
        box(f"UMull{k}", (0.1, 0.22, z1 - z0), (c, 0.0, (z0 + z1) / 2), trim, bevel=0)
        set_group("Glass")
        box(f"UGlass{k}", (b - a - 0.2, 0.05, z1 - z0 - 0.2), (c, 0.05, (z0 + z1) / 2), glass, bevel=0)
        set_group("Main")
        box(f"UBlind{k}", (b - a - 0.3, 0.04, (z1 - z0) * 0.4), (c, 0.3, z1 - (z1 - z0) * 0.2), material("Blind", base=(0.85, 0.8, 0.66), rough=0.9, wear=0.0), bevel=0)
    # ---- the cornice: a frieze, paired brackets, a projecting cap
    box("Frieze", (W + 0.4, 0.5, 1.0), (0, -0.2, ZT - 0.6), front, bevel=0.03)
    n_br = int(W / 2.0)
    for k in range(n_br + 1):
        x = X0 + 0.3 + k * (W - 0.6) / n_br
        prism(f"Bracket{k}", [(0.0, 0.0), (0.0, 1.3), (-0.7, 1.3), (-0.55, 0.9), (-0.2, 0.55)], 0.0, 0.35, front, plane="YZ")
        P.PARTS[-1].location = (x, -0.45, ZT - 0.9)
    box("CorniceCap", (W + 1.4, 1.5, 0.35), (0, -0.55, ZT + 0.55), front, bevel=0.05)
    box("CorniceTop", (W + 1.6, 1.6, 0.18), (0, -0.55, ZT + 0.8), front, bevel=0.03)
    # ---- the awning: a sloped striped canvas on iron arms, a scalloped valance (tiled awning duck)
    if not no_awning:
        ax0, ax1 = inner_x0 + 0.2, inner_x1 - 0.2
        zt_, zb_, out = H1 - 1.4, H1 - 3.3, 3.6
        set_group("Awning")
        ob = solid("AwningTop", [(ax0, -0.6, zt_), (ax1, -0.6, zt_), (ax1, -0.6 - out, zb_), (ax0, -0.6 - out, zb_)],
                   [(ax0, -0.6, zt_ + 0.06), (ax1, -0.6, zt_ + 0.06), (ax1, -0.6 - out, zb_ + 0.06), (ax0, -0.6 - out, zb_ + 0.06)], K["place"])
        _quad_uv(ob, (ax0, -0.6, zt_), (1, 0, 0), tuple(Vector((0, -out, zb_ - zt_)).normalized()), 4.0)
        ob["nh_keep_uv"] = 1
        n = int((ax1 - ax0) / 0.5)
        pts = []
        for i in range(n + 1):
            x = ax0 + (ax1 - ax0) * i / n
            pts.append((x, zb_ - 0.15 - 0.45 * abs(math.sin(math.pi * i / 2.0 * 2 / 2))))
        val = prism("Valance", [(ax0, zb_ + 0.05)] + [(x, zb_ - 0.25 - 0.4 * (0.5 - 0.5 * math.cos(2 * math.pi * ((x - ax0) / 1.0)))) for x, _ in pts] + [(ax1, zb_ + 0.05)],
                    -0.6 - out, 0.05, K["place"], plane="XZ")
        _quad_uv(val, (ax0, -0.6 - out, zb_), (1, 0, 0), (0, 0, -1), 4.0)
        val["nh_keep_uv"] = 1
        set_group("Main")
        for x in (ax0 + 0.3, (ax0 + ax1) / 2, ax1 - 0.3):
            tube(f"AwnArm{x}", [Vector((x, -0.4, zt_ - 1.4)), Vector((x, -0.6 - out + 0.2, zb_ + 0.05))], 0.05, K["iron"])
        box("AwnRail", (ax1 - ax0, 0.12, 0.12), ((ax0 + ax1) / 2, -0.6 - out, zb_), K["iron"], bevel=0.02)
    # ---- the interior, seen through the glass: a warm back wall, a floor, the shop's furniture
    inside = material("ShopInside", base=(0.62, 0.48, 0.34), rough=0.8, wear=0.0, dirt=0.4)
    box("InFloor", (W - 1.4, D - 1.4, 0.1), (0, D / 2, 0.05), material("InFloorMat", "NH_DeskWood", tint=(0.5, 0.36, 0.24), scale=0.3, wear=0.3), bevel=0)
    box("InBack", (W - 1.4, 0.2, H1 - 0.5), (0, D - 0.8, (H1 - 0.5) / 2), inside, bevel=0)
    box("InCeil", (W - 1.4, D - 1.4, 0.15), (0, D / 2, H1 - 0.4), material("InCeilMat", base=(0.85, 0.82, 0.74), rough=0.8, wear=0.0), bevel=0)
    set_group("Glow")
    for x in (-W / 4, W / 4):
        box(f"InLight{x}", (2.4, 0.4, 0.12), (x, D / 2, H1 - 0.5), material("InLightMat", base=(1.0, 0.86, 0.6), rough=0.4, wear=0.0), bevel=0)
    set_group("Main")
    interior(K, W, D, H1)
    return (W + 2, D + 5, ZT + 1.2)


# ------------------------------------------------------------------ the interiors

def in_diner(K, W, D, H1):
    chrome = material("DinerChrome", base=(0.82, 0.82, 0.85), rough=0.15, metal=1.0, wear=0.2)
    red = material("DinerVinyl", base=(0.62, 0.08, 0.08), rough=0.35, wear=0.2)
    box("Counter", (W - 4, 1.4, 2.6), (0, 6.6, 1.3), material("DinerCounter", base=(0.9, 0.86, 0.78), rough=0.3, wear=0.2), bevel=0.05)
    box("CounterTop", (W - 3.8, 1.6, 0.15), (0, 6.6, 2.67), chrome, bevel=0.03)
    for k in range(int((W - 5) / 1.6)):
        x = -W / 2 + 3.0 + k * 1.6
        cyl(f"Stool{x}", 0.07, 1.9, (x, 5.4, 0.95), chrome, verts=10)
        cyl(f"StoolSeat{x}", 0.42, 0.25, (x, 5.4, 1.95), red, verts=20, bevel=0.06)
    for sx in (-1, 1):                                          # booths by the windows
        x = sx * (W / 2 - 2.6)
        box(f"BoothSeat{sx}", (2.4, 1.1, 1.4), (x, 2.0, 0.7), red, bevel=0.15, segments=3)
        box(f"BoothBack{sx}", (2.4, 0.4, 2.6), (x, 2.5, 1.3), red, bevel=0.15, segments=3)
        box(f"BoothTable{sx}", (2.2, 1.3, 0.12), (x, 1.2, 2.3), material("DinerTable", base=(0.8, 0.3, 0.25), rough=0.25, wear=0.2), bevel=0.04)
        cyl(f"BoothPost{sx}", 0.08, 2.2, (x, 1.2, 1.1), chrome, verts=10)
    box("PieCase", (2.4, 1.0, 1.2), (W / 4, 6.6, 3.35), material("PieCase", base=(0.75, 0.82, 0.85), rough=0.1, wear=0.0), bevel=0.04)
    for k in range(3):
        cyl(f"Pie{k}", 0.35, 0.18, (W / 4 - 0.75 + k * 0.75, 6.6, 3.1), material("PieCrust", base=(0.78, 0.5, 0.22), rough=0.6, wear=0.0), verts=20, bevel=0.06)


def in_hardware(K, W, D, H1):
    shelf = material("HwShelf", "NH_DeskWood", tint=(0.45, 0.32, 0.2), scale=0.3, wear=0.4)
    for x in (-W / 2 + 1.6, -W / 2 + 4.2, W / 2 - 4.2, W / 2 - 1.6):
        box(f"Rack{x}", (1.0, D - 3.0, 6.5), (x, D / 2 + 0.6, 3.25), shelf, bevel=0.03)
        for k in range(5):
            for j in range(6):
                col = ((0.7, 0.2, 0.15), (0.2, 0.35, 0.6), (0.8, 0.65, 0.2), (0.3, 0.3, 0.32))[(k + j) % 4]
                box(f"Stock{x}{k}{j}", (1.06, 0.7, 0.6), (x, 2.4 + j * 1.0, 0.8 + k * 1.25), material(f"HwStock{(k + j) % 4}", base=col, rough=0.6, wear=0.2), bevel=0)
    box("KeyBench", (3.0, 1.2, 2.6), (0, D - 2.2, 1.3), shelf, bevel=0.04)
    box("KeyBoard", (3.2, 0.12, 2.0), (0, D - 1.2, 4.0), material("Pegboard", base=(0.72, 0.58, 0.4), rough=0.8, wear=0.1), bevel=0)


def in_video(K, W, D, H1):
    rack = material("VidRack", base=(0.15, 0.2, 0.45), rough=0.5, wear=0.2)
    for k, x in enumerate((-W / 2 + 1.8, -1.2, 1.2, W / 2 - 1.8)):
        box(f"Rack{k}", (1.4, D - 3.5, 5.2), (x, D / 2 + 0.6, 2.6), rack, bevel=0.03)
        for j in range(7):
            for r in range(4):
                c = ((0.85, 0.2, 0.2), (0.2, 0.6, 0.85), (0.95, 0.8, 0.2), (0.2, 0.7, 0.35), (0.85, 0.85, 0.85))[(j + r + k) % 5]
                box(f"Tape{k}{j}{r}", (1.46, 0.35, 0.95), (x, 2.4 + j * 0.85, 0.9 + r * 1.2), material(f"Tape{(j + r + k) % 5}", base=c, rough=0.4, wear=0.1), bevel=0)
    box("VidCounter", (4.0, 1.2, 2.6), (0, D - 2.0, 1.3), material("VidCounter", base=(0.85, 0.2, 0.2), rough=0.35, wear=0.2), bevel=0.05)


def in_suds(K, W, D, H1):
    white = material("Washer", base=(0.92, 0.92, 0.9), rough=0.25, wear=0.2)
    for k in range(int((W - 3) / 2.2)):
        x = -W / 2 + 2.0 + k * 2.2
        box(f"Washer{x}", (2.0, 2.0, 2.6), (x, D - 2.0, 1.3), white, bevel=0.15, segments=3)
        cyl(f"Door{x}", 0.62, 0.12, (x, D - 3.02, 1.4), material("WasherDoor", base=(0.6, 0.75, 0.85), rough=0.1, wear=0.0), rot=(math.pi / 2, 0, 0), verts=24, bevel=0.05)
        box(f"Panel{x}", (1.8, 0.1, 0.4), (x, D - 3.0, 2.4), material("WasherPanel", base=(0.3, 0.32, 0.36), rough=0.3, wear=0.1), bevel=0.02)
    box("FoldTable", (W - 4, 1.6, 0.15), (0, 3.2, 2.5), material("FoldTop", base=(0.85, 0.85, 0.82), rough=0.4, wear=0.2), bevel=0.03)
    for x in (-W / 2 + 2.3, W / 2 - 2.3):
        box(f"FoldLeg{x}", (0.15, 1.4, 2.4), (x, 3.2, 1.2), K["iron"], bevel=0.01)


def in_gazette(K, W, D, H1):
    desk = material("NewsDesk", "NH_DeskWood", tint=(0.5, 0.36, 0.24), scale=0.3, wear=0.4)
    for k, (x, y) in enumerate(((-3.5, 3.0), (3.5, 3.0), (-3.5, 5.8), (3.5, 5.8))):
        box(f"Desk{k}", (3.0, 1.6, 2.4), (x, y, 1.2), desk, bevel=0.04)
        box(f"Typewriter{k}", (1.0, 0.8, 0.45), (x, y, 2.63), material("Typewriter", base=(0.1, 0.1, 0.1), rough=0.3, wear=0.3), bevel=0.08)
        box(f"Papers{k}", (0.8, 0.6, 0.25), (x + 0.9, y, 2.53), material("Newsprint", base=(0.85, 0.82, 0.74), rough=0.9, wear=0.0), bevel=0.02)
    box("Press", (5.0, 2.0, 4.0), (0, D - 2.0, 2.0), material("Press", base=(0.22, 0.24, 0.22), rough=0.4, metal=0.6, wear=0.4), bevel=0.1)
    for k in range(3):
        cyl(f"Roller{k}", 0.4, 4.6, (0, D - 3.05, 1.0 + k * 1.1), material("Roller", base=(0.12, 0.12, 0.12), rough=0.3, metal=0.5, wear=0.3), rot=(0, math.pi / 2, 0), verts=20)



# ================================================================== the church and its clock tower

def _lancet(cx, z0, w, h, n=10):
    """a pointed (two-centred) arch outline in (u, z): straight sides from z0, two arcs meeting at the apex z0 + h"""
    r = w * 0.85
    spring = z0 + h - math.sqrt(max(0.0, r * r - (r - w / 2) ** 2))
    cl, cr = cx - w / 2 + r, cx + w / 2 - r
    top = math.acos(max(-1.0, min(1.0, (cx - cl) / r)))
    pts = [(cx - w / 2, z0), (cx + w / 2, z0), (cx + w / 2, spring)]
    for i in range(1, n + 1):
        a = top * i / n
        pts.append((cl + r * math.cos(a), spring + r * math.sin(a)))
    for i in range(n - 1, -1, -1):
        a = top * i / n
        pts.append((cr - r * math.cos(a), spring + r * math.sin(a)))
    return pts


def _outline(name, pts, plane, p0, r, mat):
    """a frame along an outline (closed), in the XZ or YZ plane at p0"""
    v = [Vector((u, p0, z)) if plane == "XZ" else Vector((p0, u, z)) for u, z in pts] + []
    v.append(v[0].copy())
    tube(name, v, r, mat, square=True)


def church(M):
    K = kit(M)
    trim = K["trim"]
    red = wmat("ChurchRed", "NH_PaintedWood", (0.6, 0.08, 0.07), 0.3, wear=0.35, dirt=0.7)
    bronze = material("BellBronze", base=(0.55, 0.38, 0.18), rough=0.32, metal=1.0, wear=0.4, dirt=0.9)
    slate = material("SpireSlate", "NH_Slate", tint=(0.22, 0.22, 0.25), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.15)
    gilt = material("Gilt", base=(0.95, 0.72, 0.3), rough=0.25, metal=1.0, wear=0.2)
    NX, NY0, NY1, NH = 8.0, 6.0, 32.0, 14.0
    TX, TY0, TY1 = 3.75, 0.0, 7.5
    T1, BEL0, BEL1 = 19.0, 19.0, 26.0
    # ---- the nave: clapboard walls with lancet windows, a gable roof
    set_group("Siding")
    holes = [(NY0 + 4 + k * 5.5 - 1.1, NY0 + 4 + k * 5.5 + 1.1, 4.0, 11.0) for k in range(4)]
    wall("NaveL", "x", -NX, NY0, NY1, 0.0, NH, 0.6, holes, K["place"])
    wall("NaveR", "x", NX, NY0, NY1, 0.0, NH, 0.6, holes, K["place"])
    wall("NaveBack", "y", NY1, -NX, NX, 0.0, NH, 0.6, [(-1.5, 1.5, 5.0, 11.0)], K["place"])
    wall("NaveFront", "y", NY0, -NX, NX, 0.0, NH, 0.6, [(-TX, TX, 0.0, NH)], K["place"])
    for nm, y in (("F", NY0), ("B", NY1)):
        solid(f"NaveGable{nm}", [(-NX, y - 0.3, NH), (NX, y - 0.3, NH), (0, y - 0.3, NH + NX)], [(-NX, y + 0.3, NH), (NX, y + 0.3, NH), (0, y + 0.3, NH + NX)], K["place"])
    # the tower shaft
    wall("TowerF", "y", TY0, -TX, TX, 0.0, T1, 0.6, [(-1.8, 1.8, 0.0, 9.0)], K["place"])
    wall("TowerL", "x", -TX, TY0, TY1, 0.0, T1, 0.6, [(3.0, 4.5, 11.0, 14.0)], K["place"])
    wall("TowerR", "x", TX, TY0, TY1, 0.0, T1, 0.6, [(3.0, 4.5, 11.0, 14.0)], K["place"])
    wall("TowerB", "y", TY1, -TX, TX, NH + NX - 4.0, T1, 0.6, [], K["place"])
    set_group("Roof")
    for nm, s in (("L", -1), ("R", 1)):
        e_x = s * (NX + 1.0)
        bot = [(e_x, NY0 - 0.5, NH - 1.0), (e_x, NY1 + 1.0, NH - 1.0), (0, NY1 + 1.0, NH + NX), (0, NY0 - 0.5, NH + NX)]
        ob = solid(f"NaveRoof{nm}", bot, [(x, y, z + 0.35) for x, y, z in bot], K["place"])
        _quad_uv(ob, (e_x, NY0 - 0.5, NH - 1.0), (0, 1, 0), tuple(Vector((-s, 0, 1)).normalized()), 6.0)
        ob["nh_keep_uv"] = 1
    set_group("Main")
    box("Ridge", (0.6, NY1 - NY0 + 1.6, 0.4), (0, (NY0 + NY1) / 2 + 0.25, NH + NX + 0.3), trim, bevel=0.06)
    for x in (-NX, NX):
        for y in (NY0, NY1):
            box(f"NaveCorner{x}{y}", (0.75, 0.75, NH), (x, y, NH / 2), trim, bevel=0.05)
    for x in (-TX, TX):
        for y in (TY0, TY1):
            box(f"TowerCorner{x}{y}", (0.75, 0.75, T1), (x, y, T1 / 2), trim, bevel=0.05)
    box("WaterTable", (2 * NX + 1.0, NY1 - NY0 + 1.0, 0.5), (0, (NY0 + NY1) / 2, 0.25), material("Foundation", "NH_Limestone", tint=(0.6, 0.58, 0.55), scale=0.3, wear=0.3, dirt=0.9), bevel=0.04)
    # lancet windows: pointed frames, diamond leading, clear glass
    for side, x in (("L", -NX), ("R", NX)):
        for k in range(4):
            yc = NY0 + 4 + k * 5.5
            out = -1 if x < 0 else 1
            pts = _lancet(yc, 4.0, 2.2, 7.0)
            _outline(f"Lancet{side}{k}", pts, "YZ", x + out * 0.34, 0.14, trim)
            set_group("Glass")
            prism(f"LancetGlass{side}{k}", pts, x, 0.05, K["glass"], plane="YZ")
            set_group("Main")
            box(f"Mullion{side}{k}", (0.12, 0.08, 6.3), (x + out * 0.06, yc, 7.2), K["iron"], bevel=0)
            for zz in (6.0, 8.2):
                box(f"Transom{side}{k}{zz}", (0.12, 2.1, 0.08), (x + out * 0.06, yc, zz), K["iron"], bevel=0)
            box(f"LancetSill{side}{k}", (0.8, 2.6, 0.2), (x + out * 0.35, yc, 3.9), trim, bevel=0.03)
    # the door: red double doors under a pointed arch, iron strap hinges, stone steps
    dpts = _lancet(0.0, 0.0, 3.6, 9.0)
    _outline("DoorArch", dpts, "XZ", TY0 - 0.36, 0.18, trim)
    tymp = [(-1.8, 7.0), (1.8, 7.0)] + [(u, z) for u, z in dpts[3:] if z > 7.0] + []
    prism("Tympanum", tymp, TY0 - 0.05, 0.12, trim, plane="XZ")
    for sx in (-1, 1):
        box(f"Door{sx}", (1.75, 0.2, 7.0), (sx * 0.9, TY0 + 0.05, 3.5), red, bevel=0.04)
        for zz in (1.5, 5.5):
            box(f"Strap{sx}{zz}", (1.4, 0.06, 0.18), (sx * 0.9, TY0 - 0.08, zz), K["iron"], bevel=0.01)
        cyl(f"Ring{sx}", 0.14, 0.05, (sx * 0.25, TY0 - 0.1, 3.6), K["iron"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.02)
    for k in range(3):
        box(f"Step{k}", (7.0 - k * 0.6, 1.2, (k + 1) * 0.45), (0, TY0 - 0.6 - (2 - k) * 1.2, (k + 1) * 0.225), material("StepStone", "NH_Limestone", tint=(0.78, 0.76, 0.72), scale=0.3, wear=0.3, dirt=0.9), bevel=0.05)
    # the clock on the tower front: a stone surround, the dial (canvas), the hands (their own pieces)
    CZ, CR = 15.5, 2.0
    lathe("ClockSurround", [(0.0, -0.05), (CR + 0.45, -0.05), (CR + 0.45, 0.25), (CR + 0.25, 0.4), (0.0, 0.4)],
          material("ClockStone", "NH_Limestone", tint=(0.86, 0.83, 0.78), scale=0.3, wear=0.3, dirt=0.9), seg=48, loc=(0, 0, 0))
    P.PARTS[-1].rotation_euler = (math.pi / 2, 0, 0)
    P.PARTS[-1].location = (0, TY0 - 0.05, CZ)
    set_group("Dial")
    disc = [(CR * math.cos(2 * math.pi * i / 48), CZ + CR * math.sin(2 * math.pi * i / 48)) for i in range(48)]
    prism("Dial", disc, TY0 - 0.48, 0.03, K["place"], plane="XZ")
    for nm, ln, w in (("Hr", 1.1, 0.16), ("Min", 1.7, 0.11)):
        set_group(f"Hand{nm}")
        tip = [(-w / 2, CZ - 0.25), (w / 2, CZ - 0.25), (w / 2, CZ + ln - 0.35), (w * 1.4, CZ + ln - 0.3), (0, CZ + ln), (-w * 1.4, CZ + ln - 0.3), (-w / 2, CZ + ln - 0.35)]
        prism(f"Hand{nm}", tip, TY0 - (0.55 if nm == "Hr" else 0.6), 0.04, K["iron"], plane="XZ")
    set_group("Main")
    cyl("ClockBoss", 0.14, 0.2, (0, TY0 - 0.6, CZ), gilt, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.03)
    # the belfry: four open arches with louvres below, corner posts, a bell on a yoke
    for x in (-TX, TX):
        for y in (TY0, TY1):
            box(f"BelPost{x}{y}", (0.9, 0.9, BEL1 - BEL0), (x, y, (BEL0 + BEL1) / 2), trim, bevel=0.05)
    box("BelFloor", (2 * TX + 0.8, TY1 - TY0 + 0.8, 0.5), (0, (TY0 + TY1) / 2, BEL0), trim, bevel=0.05)
    box("BelCap", (2 * TX + 1.4, TY1 - TY0 + 1.4, 0.6), (0, (TY0 + TY1) / 2, BEL1 + 0.3), trim, bevel=0.06)
    for nm, (axis, plane, p0, a, b) in {"F": ("y", "XZ", TY0, -TX, TX), "B": ("y", "XZ", TY1, -TX, TX), "L": ("x", "YZ", -TX, TY0, TY1), "R": ("x", "YZ", TX, TY0, TY1)}.items():
        c = (a + b) / 2
        arch = _lancet(c, BEL0 + 0.25, (b - a) - 1.0, BEL1 - BEL0 - 0.6)
        outer = [(a + 0.45, BEL0 + 0.25), (b - 0.45, BEL0 + 0.25), (b - 0.45, BEL1), (a + 0.45, BEL1)]
        prism(f"BelSpandrel{nm}", [(a + 0.45, BEL1 - 1.2), (b - 0.45, BEL1 - 1.2), (b - 0.45, BEL1), (a + 0.45, BEL1)], p0, 0.3, trim, plane=plane)
        for k in range(7):                                          # louvres in the lower half of each arch
            z = BEL0 + 0.6 + k * 0.42
            if axis == "y":
                box(f"Louvre{nm}{k}", ((b - a) - 1.2, 0.12, 0.35), (c, p0, z), trim, bevel=0.01, rot=(0.6, 0, 0))
            else:
                box(f"Louvre{nm}{k}", (0.12, (b - a) - 1.2, 0.35), (p0, c, z), trim, bevel=0.01, rot=(0, 0.6, 0))
    box("Yoke", (2.4, 0.5, 0.5), (0, (TY0 + TY1) / 2, BEL1 - 1.1), material("YokeOak", "NH_DeskWood", tint=(0.35, 0.24, 0.15), scale=0.3, wear=0.4), bevel=0.05)
    set_group("Bell")
    by = (TY0 + TY1) / 2
    lathe("Bell", [(0.0, BEL1 - 1.4), (0.5, BEL1 - 1.42), (0.62, BEL1 - 1.9), (0.7, BEL1 - 2.6), (0.95, BEL1 - 3.3), (1.15, BEL1 - 3.55), (1.1, BEL1 - 3.6),
                   (0.9, BEL1 - 3.4), (0.6, BEL1 - 2.7), (0.5, BEL1 - 1.95), (0.0, BEL1 - 1.9)], bronze, seg=32, loc=(0, by, 0))
    sphere("Clapper", 0.22, (0, by, BEL1 - 3.35), K["iron"], seg=12, rings=8)
    set_group("Main")
    # the spire: an octagonal slate pyramid, a gilt ball, the rooster weathervane (its own piece, it turns)
    oct_ = [(TX * 1.05 * math.cos(math.pi / 8 + k * math.pi / 4), (TY0 + TY1) / 2 + TX * 1.05 * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
    SP0, SP1 = BEL1 + 0.6, BEL1 + 17.0
    solid("Spire", [(x, y, SP0) for x, y in oct_], [(x * 0.02, (TY0 + TY1) / 2 + (y - (TY0 + TY1) / 2) * 0.02, SP1) for x, y in oct_], slate)
    sphere("SpireBall", 0.35, (0, (TY0 + TY1) / 2, SP1 + 0.2), gilt, seg=16, rings=10)
    cyl("VaneRod", 0.06, 2.2, (0, (TY0 + TY1) / 2, SP1 + 1.3), K["iron"], verts=8)
    for k, (dx, dy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        box(f"Compass{k}", (0.9 if dx else 0.06, 0.9 if dy else 0.06, 0.06), (dx * 0.45, (TY0 + TY1) / 2 + dy * 0.45, SP1 + 1.1), K["iron"], bevel=0)
    set_group("Vane")
    rooster = [(-1.1, 0.0), (-0.6, 0.15), (-0.2, 0.1), (0.1, 0.45), (0.35, 0.55), (0.45, 0.8), (0.3, 0.95), (0.4, 1.05), (0.55, 0.95), (0.7, 0.9), (0.55, 0.75),
               (0.6, 0.55), (0.35, 0.2), (0.4, -0.05), (0.2, -0.1), (-0.3, -0.05), (-0.75, 0.35), (-1.05, 0.55), (-1.15, 0.3)]
    prism("Rooster", [(x, SP1 + 2.05 + z) for x, z in rooster], (TY0 + TY1) / 2, 0.06, gilt, plane="XZ")
    tube("VaneArrow", [Vector((-1.3, (TY0 + TY1) / 2, SP1 + 1.95)), Vector((1.3, (TY0 + TY1) / 2, SP1 + 1.95))], 0.04, gilt)
    set_group("Main")
    by_, cz_ = (TY0 + TY1) / 2, CZ
    B49.RIG["WFChurch"] = dict(
        bones={"HandHr": ((0, TY0 - 0.55, cz_), (0, TY0 - 1.0, cz_), None), "HandMin": ((0, TY0 - 0.6, cz_), (0, TY0 - 1.0, cz_), None),
               "Bell": ((0, by_, BEL1 - 1.2), (0, by_, BEL1 - 2.2), None), "Vane": ((0, by_, SP1 + 1.9), (0, by_, SP1 + 2.9), None)},
        own={"HandHr": "HandHr", "HandMin": "HandMin", "Bell": "Bell", "Vane": "Vane"})
    return (2 * NX + 3, NY1 + 4, SP1 + 3.5)


def _tick(t, start_deg, steps, step_deg, t0, dt):
    """a ticking hand: one step every dt from t0, each step a quick snap with a little bounce"""
    a = start_deg
    for k in range(steps):
        tk = t0 + k * dt
        if t >= tk:
            a += step_deg * min(1.0, back_out((t - tk) / 0.12, 2.5))
    return a


CHURCH_CLIPS = {
    # 11:58 to midnight: the minute hand ticks up to XII (rotations about -Y, so + is clockwise seen from the front)
    "StrikeMidnight": dict(length=3.0, keys={
        "HandMin": lambda t: ("y", -12 + _tick(t, 0, 2, 6, 0.6, 1.0), (0, 0, 0)),
        "HandHr": lambda t: ("y", -1 + _tick(t, 0, 2, 0.5, 0.6, 1.0), (0, 0, 0))}),
    # the bell: three heavy swings, each a pendulum with a long settle
    "BellToll": dict(length=6.0, keys={
        "Bell": lambda t: ("x", 32 * math.sin(2 * math.pi * t / 2.0) * min(1.0, t / 0.6) * (1 - max(0.0, t - 4.0) / 2.2), (0, 0, 0))}),
    "VaneTurn": dict(length=6.0, loop=True, keys={
        "Vane": lambda t: ("z", 25 * math.sin(2 * math.pi * t / 6.0) + 6 * math.sin(2 * math.pi * t / 1.5), (0, 0, 0))}),
}



# ================================================================== the Founder's Statue

def bronze_patina():
    """weathered bronze: a dark brown-gold metal, verdigris (blue-green) collecting where rain runs (upward faces and
    down the creases, by a noise streaked downward), polished high spots"""
    m = bpy.data.materials.get("FounderBronze")
    if m:
        return m
    m = bpy.data.materials.new("FounderBronze")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links.new
    bs = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.25)            # streaks run down
    L(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 6
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    geo = N.new("ShaderNodeNewGeometry")
    up = N.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], up.inputs[0])
    mix_f = N.new("ShaderNodeMath")
    mix_f.operation = "ADD"
    L(nz.outputs["Fac"], mix_f.inputs[0])
    upm = N.new("ShaderNodeMath")
    upm.operation = "MULTIPLY"
    upm.inputs[1].default_value = 0.35
    L(up.outputs[2], upm.inputs[0])
    L(upm.outputs[0], mix_f.inputs[1])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.5
    ramp.color_ramp.elements[0].color = (0.17, 0.11, 0.05, 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.22, 0.42, 0.34, 1)
    L(mix_f.outputs[0], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], bs.inputs["Base Color"])
    met = N.new("ShaderNodeMath")
    met.operation = "SUBTRACT"
    met.inputs[0].default_value = 1.15
    L(mix_f.outputs[0], met.inputs[1])
    L(met.outputs[0], bs.inputs["Metallic"])
    rgh = N.new("ShaderNodeMapRange")
    L(mix_f.outputs[0], rgh.inputs["Value"])
    rgh.inputs["To Min"].default_value = 0.3
    rgh.inputs["To Max"].default_value = 0.75
    L(rgh.outputs["Result"], bs.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 30.0
    L(tc.outputs["Object"], nz2.inputs["Vector"])
    L(nz2.outputs["Fac"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bs.inputs["Normal"])
    return m


def ribbon(name, pts, width, mat, thick=0.015):
    """a flat paper ribbon along a path: its width across the path (kept roughly horizontal), thin, a slight twist"""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        tw = 0.6 * math.sin(i * 0.9)                          # a little twist as it hangs
        side = (side * math.cos(tw) + t.cross(side) * math.sin(tw)).normalized()
        rows.append((bm.verts.new(p - side * width / 2), bm.verts.new(p + side * width / 2)))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, a1, b1, b0))
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness = thick
    from nh_props import _finish
    return _finish(ob, mat, 0)


def founder_statue(M):
    from nh_props_batch33 import Skel
    from nh_props_batch34 import chain
    K = kit(M)
    br = bronze_patina()
    granite = material("Granite", "NH_Limestone", tint=(0.5, 0.5, 0.52), scale=0.35, wear=0.35, dirt=1.0)
    ZB = 6.2
    V = lambda x, y, z: Vector((x, y, z + ZB))
    # ---- the pedestal: two steps, the die with the plaque, a moulded cap
    box("Step1", (8.0, 11.0, 0.6), (0, 0, 0.3), granite, bevel=0.06)
    box("Step2", (7.0, 10.0, 0.6), (0, 0, 0.9), granite, bevel=0.06)
    box("Plinth", (6.0, 9.0, 0.8), (0, 0, 1.6), granite, bevel=0.08)
    box("Die", (5.2, 8.2, 3.6), (0, 0, 3.8), granite, bevel=0.06)
    box("CapMould", (5.8, 8.8, 0.4), (0, 0, 5.8), granite, bevel=0.1)
    box("Cap", (6.2, 9.2, 0.35), (0, 0, 6.03), granite, bevel=0.08)
    box("PlaqueBack", (3.6, 0.1, 2.4), (0, -4.14, 3.9), br, bevel=0.04)
    set_group("Plaque")
    box("Plaque", (3.4, 0.03, 2.13), (0, -4.2, 3.9), K["place"], bevel=0)
    set_group("Main")
    # ---- the horse (rearing a little: the near foreleg raised)
    S = Skel()
    pelvis = S.add(V(0, 2.4, 4.7), 1.32)
    sp = chain(S, [V(0, 1.2, 4.75), V(0, 0.0, 4.85), V(0, -1.2, 5.0)], [1.28, 1.32, 1.38], pelvis)
    chain(S, [V(0, -0.6, 3.85), V(0, 0.8, 3.9)], [1.05, 1.0], sp[1])
    nk = chain(S, [V(0, -2.0, 5.9), V(0, -2.6, 6.9), V(0, -3.0, 7.7)], [0.9, 0.7, 0.56], sp[2])
    hd = chain(S, [V(0, -3.3, 7.9), V(0, -3.85, 7.45), V(0, -4.35, 6.95)], [0.5, 0.38, 0.3], nk[2])
    chain(S, [V(0, -2.2, 6.35), V(0, -2.8, 7.35)], [0.42, 0.34], nk[0])          # the crest of the mane
    for sx in (-1, 1):
        chain(S, [V(sx * 0.22, -3.15, 8.45)], [0.12], hd[0])                    # ears
        chain(S, [V(sx * 0.3, -3.6, 7.6)], [0.22], hd[0])                       # cheeks
        chain(S, [V(sx * 0.6, -1.3, 5.0)], [0.75], sp[2])                       # shoulders
        chain(S, [V(sx * 0.75, 2.55, 4.85)], [0.95], pelvis)                    # quarters
    raised = [V(0.65, -1.45, 4.5), V(0.72, -1.7, 3.5), V(0.66, -2.45, 3.25), V(0.66, -2.6, 2.45), V(0.66, -2.42, 2.12)]
    chain(S, raised, [0.72, 0.44, 0.32, 0.23, 0.25], sp[2])
    planted = [V(-0.62, -1.4, 4.5), V(-0.66, -1.5, 3.3), V(-0.62, -1.55, 2.0), V(-0.6, -1.5, 0.7), V(-0.6, -1.62, 0.26)]
    chain(S, planted, [0.72, 0.42, 0.3, 0.23, 0.31], sp[2])
    for sx in (-1, 1):
        hind = [V(sx * 0.75, 2.6, 4.5), V(sx * 0.8, 2.05, 3.25), V(sx * 0.7, 3.0, 2.0), V(sx * 0.66, 2.8, 0.7), V(sx * 0.66, 2.72, 0.26)]
        chain(S, hind, [1.08, 0.64, 0.34, 0.23, 0.31], pelvis)
    chain(S, [V(0, 3.35, 5.0), V(0, 3.85, 4.3), V(0, 4.1, 3.2), V(0, 4.2, 2.1)], [0.3, 0.36, 0.3, 0.18], pelvis)   # the flowing tail
    S.build("Horse", br, subdiv=2, knobs=0.04)
    # the saddle cloth and the saddle
    box("SaddleCloth", (2.5, 2.4, 0.08), (0, 0.4, ZB + 5.95), br, bevel=0.03, rot=(0.05, 0, 0))
    box("Saddle", (1.4, 1.8, 0.4), (0, 0.35, ZB + 6.15), br, bevel=0.18, segments=3)
    # ---- the rider: Josiah Wick in a frock coat and top hat, the book of rules held high
    R = Skel()
    hips = R.add(V(0, 0.3, 6.45), 0.55)
    tor = chain(R, [V(0, 0.25, 7.4), V(0, 0.2, 8.3)], [0.6, 0.64], hips)
    nck = chain(R, [V(0, 0.15, 9.0)], [0.27], tor[1])
    chain(R, [V(0, 0.1, 9.5), V(0, 0.0, 9.75)], [0.42, 0.36], nck[0])
    chain(R, [V(0, -0.32, 9.45)], [0.1], nck[0])                                    # the nose
    chain(R, [V(0, 0.95, 6.1), V(0, 1.35, 5.65)], [0.48, 0.36], hips)               # the coat tails over the horse
    for sx in (-1, 1):
        chain(R, [V(sx * 0.78, 0.0, 6.05), V(sx * 0.98, -0.6, 5.25), V(sx * 0.92, -0.3, 4.25), V(sx * 0.92, -0.78, 4.08)], [0.34, 0.26, 0.18, 0.17], hips)
    chain(R, [V(-0.72, 0.2, 8.5), V(-1.0, -0.2, 9.4), V(-1.02, -0.4, 10.35)], [0.28, 0.2, 0.17], tor[1])   # the raised arm
    chain(R, [V(0.72, 0.2, 8.4), V(0.88, -0.3, 7.6), V(0.5, -0.9, 7.2)], [0.27, 0.2, 0.16], tor[1])        # the rein hand
    R.build("Rider", br, subdiv=2, knobs=0.02)
    cyl("HatCrown", 0.34, 0.8, (0, 0.05, ZB + 10.25), br, verts=24, bevel=0.04)
    cyl("HatBrim", 0.58, 0.06, (0, 0.05, ZB + 9.88), br, verts=28, bevel=0.03)
    box("RuleBook", (0.85, 0.3, 0.65), (-1.03, -0.45, ZB + 10.75), br, bevel=0.05)
    tube("Reins", [V(0.5, -0.9, 7.2), V(0.3, -2.2, 7.0), V(0.2, -3.9, 7.1)], 0.04, br)
    tube("Reins2", [V(0.5, -0.9, 7.2), V(-0.2, -2.2, 7.0), V(-0.2, -3.9, 7.1)], 0.04, br)
    # ---- the prank (its own piece, shown only after the Statue prank): a cone hat, toilet-paper streamers, a roll on the book
    set_group("Prank")
    orange = material("ConeOrange", base=(0.95, 0.35, 0.05), rough=0.5, wear=0.1)
    white = material("TPWhite", base=(0.95, 0.94, 0.9), rough=0.9, wear=0.0, dirt=0.3)
    cone("Cone", 0.5, 0.06, 1.5, (0, 0.05, ZB + 11.4), orange, verts=24)
    box("ConeBase", (1.1, 1.1, 0.12), (0, 0.05, ZB + 10.66), orange, bevel=0.04)
    for k, z in enumerate((ZB + 11.0, ZB + 11.5)):
        cyl(f"ConeStripe{k}", 0.4 - k * 0.14, 0.18, (0, 0.05, z), white, verts=24)
    cyl("TPRoll", 0.22, 0.4, (-1.03, -0.45, ZB + 11.3), white, verts=20, rot=(0, math.pi / 2, 0))
    import random as _r
    rnd = _r.Random(51)
    for k in range(7):                                                              # streamers draped from the book and the hat
        x0 = -1.0 + rnd.uniform(-0.3, 0.3) if k < 4 else rnd.uniform(-0.4, 0.4)
        y0 = -0.4 if k < 4 else 0.05
        z0 = ZB + (11.1 if k < 4 else 10.2)
        pts = [Vector((x0, y0, z0))]
        for i in range(1, 9):
            t = i / 8
            pts.append(Vector((x0 + rnd.uniform(-0.4, 0.4) + (1.6 * t if k in (2, 5) else -1.2 * t if k in (1, 6) else 0.3 * t),
                               y0 + (-2.5 * t if k % 2 else 1.8 * t), z0 - 4.2 * t ** 1.3)))
        ribbon(f"Streamer{k}", pts, 0.34, white)
    set_group("Main")
    return (8.0, 11.0, ZB + 12.6)



# ================================================================== the bandstand, a bench, an autumn tree, THE PLAN on its post

def bandstand(M):
    """an octagonal bandstand: a raised deck on a lattice skirt, steps, eight turned posts, a railing, an ogee shingle roof
    with a cupola and a finial, red-white-blue bunting swagged between the posts, warm string lights"""
    K = kit(M)
    trim = K["trim"]
    R_, DZ, PH = 8.0, 3.0, 9.0                      # radius (to the posts), deck height, post height
    oct_ = [(R_ * math.cos(math.pi / 8 + k * math.pi / 4), R_ * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
    deck = material("BandDeck", "NH_DeskWood", tint=(0.5, 0.36, 0.24), scale=0.3, rough_add=0.1, wear=0.4)
    solid("Deck", [(x * 1.06, y * 1.06, DZ - 0.4) for x, y in oct_], [(x * 1.06, y * 1.06, DZ) for x, y in oct_], deck)
    solid("Base", [(x * 0.98, y * 0.98, 0.0) for x, y in oct_], [(x * 0.98, y * 0.98, DZ - 0.4) for x, y in oct_], material("BandBase", "NH_Limestone", tint=(0.7, 0.68, 0.64), scale=0.3, wear=0.3, dirt=0.9))
    for k in range(8):                                                     # lattice panels on each side of the skirt
        a, b = Vector((*oct_[k], 0)), Vector((*oct_[(k + 1) % 8], 0))
        mid = (a + b) / 2
        d = (b - a)
        ang = math.atan2(d.y, d.x)
        out = Vector((math.cos(ang - math.pi / 2), math.sin(ang - math.pi / 2), 0))
        if k == 6:                                                         # the steps on the front (-Y) side
            for st in range(5):
                box(f"BandStep{st}", (d.length * 0.8, 0.9, (st + 1) * DZ / 5), (mid.x + out.x * (0.6 + (4 - st) * 0.9) * 1.0, mid.y + out.y * (0.6 + (4 - st) * 0.9), (st + 1) * DZ / 10), deck, bevel=0.03, rot=(0, 0, ang))
            continue
        for j in range(7):
            t = (j + 0.5) / 7
            p = a.lerp(b, t) * 1.02
            for s_ in (-1, 1):
                box(f"Lat{k}{j}{s_}", (0.1, 0.08, DZ * 0.95), (p.x, p.y, DZ * 0.45), trim, bevel=0, rot=(s_ * 0.55, 0, ang) if False else (0, s_ * 0.55, ang))
    for k, (x, y) in enumerate(oct_):                                      # turned posts
        box(f"PostBase{k}", (0.7, 0.7, 0.8), (x, y, DZ + 0.4), trim, bevel=0.05)
        for i, (r0, h0, h1) in enumerate(((0.26, 0.8, 2.0), (0.3, 2.0, 2.3), (0.2, 2.3, 7.4), (0.3, 7.4, 7.8), (0.24, 7.8, PH))):
            cyl(f"Post{k}_{i}", r0, h1 - h0, (x, y, DZ + (h0 + h1) / 2), trim, verts=12, bevel=0.02)
        box(f"PostCap{k}", (0.75, 0.75, 0.4), (x, y, DZ + PH + 0.2), trim, bevel=0.05)
    for k in range(8):                                                     # railing (except the steps side), the frieze
        a, b = Vector(oct_[k]), Vector(oct_[(k + 1) % 8])
        d = b - a
        ang = math.atan2(d.y, d.x)
        mid = (a + b) / 2
        box(f"Frieze{k}", (d.length, 0.25, 0.7), (mid.x, mid.y, DZ + PH - 0.6), trim, bevel=0.03, rot=(0, 0, ang))
        for j in range(9):                                                 # little fretwork brackets
            t = (j + 0.5) / 9
            p = a.lerp(b, t)
            box(f"Fret{k}{j}", (0.12, 0.2, 0.5), (p.x, p.y, DZ + PH - 1.15), trim, bevel=0, rot=(0, 0, ang))
        if k == 6:
            continue
        box(f"RailTop{k}", (d.length - 0.6, 0.3, 0.18), (mid.x, mid.y, DZ + 2.6), trim, bevel=0.04, rot=(0, 0, ang))
        box(f"RailBot{k}", (d.length - 0.6, 0.25, 0.15), (mid.x, mid.y, DZ + 0.35), trim, bevel=0.03, rot=(0, 0, ang))
        for j in range(10):
            p = a.lerp(b, 0.08 + 0.84 * (j + 0.5) / 10)
            box(f"Bal{k}{j}", (0.14, 0.14, 2.2), (p.x, p.y, DZ + 1.45), trim, bevel=0)
    # the roof: an ogee (bell-cast) octagonal roof, shingled, with a cupola and a finial
    set_group("Roof")
    prof = [(R_ * 1.15, DZ + PH + 0.4), (R_ * 0.9, DZ + PH + 1.6), (R_ * 0.55, DZ + PH + 3.4), (R_ * 0.25, DZ + PH + 5.0), (R_ * 0.12, DZ + PH + 5.6)]
    for k in range(8):
        a0, a1 = math.pi / 8 + k * math.pi / 4, math.pi / 8 + (k + 1) * math.pi / 4
        for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
            bot = [(r0 * math.cos(a0), r0 * math.sin(a0), z0), (r0 * math.cos(a1), r0 * math.sin(a1), z0),
                   (r1 * math.cos(a1), r1 * math.sin(a1), z1), (r1 * math.cos(a0), r1 * math.sin(a0), z1)]
            ob = solid(f"RoofP{k}_{z0:.1f}", bot, [(x, y, z + 0.25) for x, y, z in bot], K["place"])
            am = (a0 + a1) / 2
            u_ = (-math.sin(am), math.cos(am), 0)
            slope = Vector((r1 * math.cos(am) - r0 * math.cos(am), r1 * math.sin(am) - r0 * math.sin(am), z1 - z0)).normalized()
            _quad_uv(ob, (r0 * math.cos(a0), r0 * math.sin(a0), z0), u_, tuple(slope), 6.0)
            ob["nh_keep_uv"] = 1
    set_group("Main")
    cz0 = DZ + PH + 5.6
    lathe("Cupola", [(0, cz0), (1.0, cz0), (1.0, cz0 + 1.6), (1.2, cz0 + 1.7), (1.25, cz0 + 1.9), (0.9, cz0 + 2.4), (0.3, cz0 + 2.9), (0, cz0 + 3.0)], trim, seg=8)
    lathe("Finial", [(0, cz0 + 2.9), (0.18, cz0 + 3.0), (0.25, cz0 + 3.3), (0.08, cz0 + 3.6), (0.14, cz0 + 3.9), (0, cz0 + 4.6)], K["brass"], seg=12)
    # bunting: little triangular flags swagged between the posts; string lights along the frieze
    cols = [material("FlagRed", base=(0.7, 0.08, 0.08), rough=0.8, wear=0.0), material("FlagWhite", base=(0.92, 0.9, 0.86), rough=0.8, wear=0.0),
            material("FlagBlue", base=(0.12, 0.2, 0.5), rough=0.8, wear=0.0)]
    n_ = 0
    for k in range(8):
        a, b = Vector((*oct_[k], DZ + PH - 1.3)), Vector((*oct_[(k + 1) % 8], DZ + PH - 1.3))
        d = (b - a)
        ang = math.atan2(d.y, d.x)
        for j in range(9):
            t = (j + 0.5) / 9
            p = a.lerp(b, t)
            p.z -= 0.9 * math.sin(math.pi * t)
            out = Vector((math.cos(ang - math.pi / 2), math.sin(ang - math.pi / 2), 0)) * 0.15
            prism(f"Flag{k}{j}", [(-0.25, 0.0), (0.25, 0.0), (0.0, -0.55)], 0.0, 0.02, cols[n_ % 3], plane="XZ")
            P.PARTS[-1].matrix_world = __import__("mathutils").Matrix.Translation(p + out) @ __import__("mathutils").Matrix.Rotation(ang, 4, "Z")
            n_ += 1
        pts = [a.lerp(b, i / 12) - Vector((0, 0, 0.9 * math.sin(math.pi * i / 12))) for i in range(13)]
        tube(f"BuntCord{k}", pts, 0.025, K["iron"])
    set_group("Glow")
    for k in range(8):
        a, b = Vector((*oct_[k], DZ + PH - 0.2)), Vector((*oct_[(k + 1) % 8], DZ + PH - 0.2))
        for j in range(5):
            p = a.lerp(b, (j + 0.5) / 5)
            sphere(f"Bulb{k}{j}", 0.1, (p.x * 0.97, p.y * 0.97, p.z - 0.25), K["bulb"], seg=8, rings=6)
    set_group("Main")
    return (2 * R_ + 6, 2 * R_ + 8, cz0 + 4.6)


def park_bench(M):
    """a park bench: cast-iron scroll ends, oak slats, a small brass dedication plate"""
    K = kit(M)
    iron = material("BenchIron", "NH_Iron", tint=(0.06, 0.08, 0.07), scale=0.45, wear=0.45, wear_metal=True)
    oak = material("BenchOak", "NH_DeskWood", tint=(0.5, 0.34, 0.2), scale=0.3, rough_add=0.1, wear=0.5)
    for x in (-2.6, 2.6):
        prism(f"End{x}", [(0.9, 0.0), (0.6, 0.0), (0.55, 1.5), (-0.4, 1.6), (-0.65, 0.0), (-0.95, 0.0), (-0.75, 1.75), (-1.05, 3.6), (-0.8, 3.65), (-0.5, 1.95), (0.75, 1.8), (1.0, 2.3), (1.15, 2.2)],
              x, 0.18, iron, plane="YZ")
    for k in range(4):
        box(f"Seat{k}", (5.8, 0.42, 0.14), (0, -0.55 + k * 0.48, 1.72), oak, bevel=0.04)
    for k in range(3):
        box(f"Back{k}", (5.8, 0.14, 0.4), (0, 0.85 + k * 0.08, 2.35 + k * 0.5), oak, bevel=0.04, rot=(-0.2, 0, 0))
    box("Plate", (0.9, 0.04, 0.22), (0, 0.78, 2.95), K["brass"], bevel=0.01, rot=(-0.2, 0, 0))
    return (6.4, 2.4, 3.8)


def autumn_tree(M):
    """a street maple in full autumn: a sculpted trunk and limbs (skinned skeleton), clustered orange-red foliage clumps,
    a few bare twigs showing through"""
    from nh_props_batch33 import Skel
    from nh_props_batch34 import chain
    import random as _r
    rnd = _r.Random(77)
    bark = material("Bark", "NH_DeskWood", tint=(0.2, 0.15, 0.11), scale=0.6, rough_add=0.25, normal=1.2, wear=0.2, dirt=1.0)
    S = Skel()
    base = S.add(Vector((0, 0, 0)), 0.9)
    trunk = chain(S, [Vector((0.1, 0.0, 2.0)), Vector((0.0, 0.1, 4.5)), Vector((-0.1, 0.0, 7.0))], [0.7, 0.6, 0.5], base)
    for sx, sy in ((1.4, 0.2), (-1.2, 0.5), (0.3, -1.4)):                  # root flare
        chain(S, [Vector((sx, sy, 0.1))], [0.4], base)
    tips = []
    for k in range(7):
        a = k * 2 * math.pi / 7 + rnd.uniform(-0.3, 0.3)
        start = trunk[1] if k < 3 else trunk[2]
        r = rnd.uniform(3.0, 4.6)
        p1 = Vector((math.cos(a) * r * 0.45, math.sin(a) * r * 0.45, 7.5 + rnd.uniform(0, 1.5)))
        p2 = Vector((math.cos(a) * r, math.sin(a) * r, 9.5 + rnd.uniform(0, 2.0)))
        ids = chain(S, [p1, p2], [0.32, 0.16], start)
        tips.append(p2)
        sub = chain(S, [p2 + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1.4))], [0.08], ids[1])
    S.build("Tree", bark, subdiv=2, knobs=0.06)
    # the crown: dark leafy masses (so you can't see through) covered in alpha-cut maple-leaf cards (the garden kit's
    # Cards system, batch 40) on the autumn atlas NH_AutumnLeaves
    import nh_props_batch40 as B40
    rng2 = B40.RNG(78)
    cards = B40.Cards(rng2)
    core = B40.leafy_core("MapleCore", (0.07, 0.022, 0.01))
    set_group("Core")
    for i, tp in enumerate(tips):
        for j in range(3):
            c = tp + Vector((rnd.uniform(-1.0, 1.0), rnd.uniform(-1.0, 1.0), rnd.uniform(-0.3, 1.2)))
            r_ = rnd.uniform(1.2, 1.8)
            ob = B40.blob(f"Mass{i}_{j}", tuple(c), 1.0, core, seg=12, rings=8, scale=(r_, r_, r_ * 0.8), jitter=0.12, seed=i * 3 + j)
            cards.cover(ob, 2.6, "ivy", 1.25, offset=0.1, tilt=0.4, zmin=5.0)
    set_group("Main")
    for k in range(10):                                    # a few leaves drifting down under the crown
        p_ = Vector((rnd.uniform(-4, 4), rnd.uniform(-4, 4), rnd.uniform(1.5, 6.0)))
        cards.crossed(p_, 0.35, 0.35, "ivy", k=1, lean=0.6)
    cards.build("Leaves")
    P.ATLAS["WFTreeMaple_Leaves"] = "NH_AutumnLeaves"
    set_group("Main")
    return (11.0, 11.0, 14.0)


def plan_post(M):
    """a square lamp post (the iron streetlamp's column) with THE PLAN taped to it at eye height"""
    K = kit(M)
    iron = material("PostIron", "NH_Iron", tint=(0.07, 0.085, 0.075), scale=0.45, wear=0.45, wear_metal=True)
    lathe("Base", [(0.85, 0), (0.85, 0.25), (0.7, 0.35), (0.7, 1.0), (0.5, 1.2), (0.38, 1.4), (0, 1.4)], iron, seg=8)
    lathe("Column", [(0.32, 1.4), (0.28, 1.8), (0.26, 11.0), (0, 11.0)], iron, seg=24, flute=(12, 0.08))
    lathe("Head", [(0.4, 11.0), (0.5, 11.2), (0.3, 11.5), (0, 11.5)], iron, seg=8)
    set_group("Glow")
    sphere("Globe", 0.5, (0, 0, 12.0), K["bulb"], seg=16, rings=10)
    set_group("Flyer")
    box("Flyer", (1.6, 0.01, 2.2), (0, -0.34, 5.6), K["place"], bevel=0, rot=(0, 0.04, 0))
    set_group("Main")
    for x, z in ((-0.7, 6.65), (0.7, 6.65)):
        box(f"Tape{x}", (0.5, 0.012, 0.16), (x, -0.335, z), material("TapeClear", base=(0.95, 0.92, 0.8), rough=0.3, wear=0.0), bevel=0, rot=(0, 0.5 if x > 0 else -0.5, 0))
    box("Staple", (0.08, 0.02, 0.08), (0, -0.33, 4.55), K["iron"], bevel=0)
    return (2.0, 2.0, 12.6)


SHOPS = {
    "WFShopDiner": dict(W=18.0, walls=("WF_ClapBlue", 8.0), awning="WF_AwningRed", sign="WF_SignMoonpie", aspect=2.0, interior=in_diner, front_col=(0.85, 0.85, 0.86)),
    "WFShopHardware": dict(W=16.0, walls=("WF_Brick", 6.0), awning="WF_AwningGreen", sign="WF_SignHardware", aspect=3.0, interior=in_hardware, front_col=(0.16, 0.3, 0.22)),
    "WFShopVideo": dict(W=14.0, walls=("WF_ClapButter", 8.0), awning="WF_AwningBlue", sign="WF_SignVideo", aspect=3.0, interior=in_video, front_col=(0.14, 0.2, 0.5)),
    "WFShopSuds": dict(W=14.0, walls=("WF_Brick", 6.0), awning="WF_AwningBlue", sign="WF_SignSuds", aspect=3.0, interior=in_suds, front_col=(0.85, 0.9, 0.88)),
    "WFShopGazette": dict(W=14.0, walls=("WF_Brick", 6.0), awning=None, sign="WF_SignGazette", aspect=4.0, interior=in_gazette, front_col=(0.12, 0.12, 0.13)),
}
for _n, _c in SHOPS.items():
    BUILDERS[_n] = (lambda c: (lambda M: storefront(M, c["W"], c["walls"], c["awning"], c["sign"], c["aspect"], c["interior"],
                                                    front_col=c["front_col"], no_awning=c["awning"] is None)))(_c)
    P.TILED[f"{_n}_Walls"] = _c["walls"]
    if _c["awning"]:
        P.TILED[f"{_n}_Awning"] = (_c["awning"], 4.0)
    P.CANVAS[f"{_n}_Sign"] = _c["sign"]
BUILDERS["WFChurch"] = church
BUILDERS.update({"WFBandstand": bandstand, "WFBench": park_bench, "WFTreeMaple": autumn_tree, "WFPlanPost": plan_post})
P.TILED["WFBandstand_Roof"] = ("WF_Shingle", 6.0)
P.CANVAS["WFPlanPost_Flyer"] = "WF_ThePlan"
BUILDERS["WFFounderStatue"] = founder_statue
P.CANVAS["WFFounderStatue_Plaque"] = "WF_PlaqueFounder"
P.TILED["WFChurch_Siding"] = ("WF_ClapCream", 8.0)
P.TILED["WFChurch_Roof"] = ("WF_Shingle", 6.0)
P.CANVAS["WFChurch_Dial"] = "WF_ClockDial"
B49.CLIPS["WFChurch"] = CHURCH_CLIPS
P.RIGS["WFChurch"] = lambda objs: B49.rig_pieces("WFChurch", objs)
B49.CLIP_CAM["WFChurch"] = {"StrikeMidnight": ((0.0, -9.0, 15.5), (0.0, 0.0, 15.5)), "BellToll": ((9.0, -8.0, 24.0), (0.0, 3.75, 22.5)),
                            "VaneTurn": ((10.0, -10.0, 45.0), (0.0, 3.75, 44.0))}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.15 for n in BUILDERS})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        if n in B49.CLIPS:
            B49.clip_strips(n)
