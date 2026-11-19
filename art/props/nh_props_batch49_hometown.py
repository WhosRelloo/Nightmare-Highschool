"""Props batch 49 (2026-11-18): Wickfield, the tutorial's hometown (docs/expansion/15-Tutorial-The-Last-Normal-Night.md).
Warm small-town autumn: painted clapboard, white trim, red brick, asphalt shingles, brass, lamplight. Original designs.

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch49_hometown.py -- <Prop|all> [--size 2048] [--samples 64] [--gpu]

WickHouse  14 Alder Lane, the player's house: two storeys of cream lap siding on a brick foundation (30 x 22 studs, walls
           1.6 to 21.6), a shingled gable roof (ridge along X), a brick chimney on the right. The front (-Y): a full porch
           (x -10 to 15, 7 deep) with turned posts, a railing, three steps up to the red front door, and a shed porch roof
           whose top runs under the bedroom window (upper right): the way out. The drainpipe at the porch roof's front
           right corner goes to the ground (the way down). Back (+Y): the kitchen door and window over the garden.
           Pieces: Siding / Roof / Brick (tiled: WF_ClapCream, WF_Shingle, WF_Brick), Main (baked trim, porch, doors,
           shutters, gutters, the porch light's housing), Glass (window panes, Roblox Glass), BedSash (the bedroom
           window's lower sash, its own mesh so it can slide up), Glow (the porch light's bulb, Neon).
           The house is hollow: the bedroom (upper front right) and the kitchen (ground back right) are separate
           interior props that sit inside it.

Space: studs, -Y front, Z up, origin at the bottom centre of the footprint.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube, set_group, _finish, material  # noqa: E402
from nh_props_batch28 import mk, solid  # noqa: E402

TILES = {"Siding": ("WF_ClapCream", 8.0), "Roof": ("WF_Shingle", 6.0), "Brick": ("WF_Brick", 6.0)}
BUILDERS = {}


def kit(M):
    return {
        "trim": material("WFTrim", base=(0.86, 0.84, 0.8), rough=0.55, wear=0.25, dirt=0.7),
        "door": material("WFDoorRed", "NH_PaintedMetal", tint=(0.36, 0.05, 0.045), scale=1.0, rough_add=0.1, wear=0.35),
        "shutter": material("WFShutter", "NH_PaintedMetal", tint=(0.2, 0.28, 0.2), scale=1.0, rough_add=0.15, wear=0.4),
        "deck": material("WFDeck", "NH_DeskWood", tint=(0.48, 0.36, 0.26), scale=0.3, rough_add=0.1, wear=0.45, dirt=0.9),
        "gutter": material("WFGutter", base=(0.8, 0.8, 0.78), rough=0.4, metal=0.6, wear=0.3, dirt=0.8),
        "brass": M["brass"], "iron": M["iron"], "glass": M["glassclear"],
        "bulb": material("WFBulb", base=(1.0, 0.82, 0.5), rough=0.3, wear=0.0, dirt=0.0),
        "place": material("WFPlace", base=(0.5, 0.5, 0.5), rough=0.8, wear=0.0, dirt=0.0),
        "step": material("WFStep", "NH_Limestone", tint=(0.72, 0.7, 0.66), scale=0.3, wear=0.3, dirt=0.9),
    }


# ------------------------------------------------------------------ tiled pieces: keep the builder's UVs for the roof

def _quad_uv(ob, origin, u_dir, v_dir, tile):
    """planar UVs for a whole piece: u along u_dir, v along v_dir, from origin, `tile` studs a repeat"""
    me = ob.data
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    uv = me.uv_layers.new(name="Bake")
    mw = ob.matrix_world
    for li, loop in enumerate(me.loops):
        co = mw @ me.vertices[loop.vertex_index].co - Vector(origin)
        uv.data[li].uv = (co.dot(Vector(u_dir)) / tile, co.dot(Vector(v_dir)) / tile)


_orig_tile_uv = P.tile_uv


def _tile_uv(ob, tile):
    if ob.get("nh_keep_uv") and "Bake" in ob.data.uv_layers:
        for uv in list(ob.data.uv_layers):
            if uv.name != "Bake":
                ob.data.uv_layers.remove(uv)
        ob.data.uv_layers.active = ob.data.uv_layers["Bake"]
        return
    _orig_tile_uv(ob, tile)


P.tile_uv = _tile_uv


# ------------------------------------------------------------------ helpers

def wall(prefix, axis, plane, a0, a1, z0, z1, thick, holes, mat):
    """A wall slab in the plane x = plane (axis "x") or y = plane (axis "y"), spanning a0..a1 along the other horizontal
    axis and z0..z1, `thick` deep (centred on the plane), with rectangular holes [(h0, h1, hz0, hz1)]: built as boxes
    round the holes (vertical strips at every hole edge, then the solid runs in each strip)."""
    cuts = sorted({a0, a1, *[h[0] for h in holes], *[h[1] for h in holes]})
    k = 0
    for s0, s1 in zip(cuts, cuts[1:]):
        if s1 - s0 < 1e-4:
            continue
        mid = (s0 + s1) / 2
        blocked = sorted([(h[2], h[3]) for h in holes if h[0] < mid < h[1]])
        runs, z = [], z0
        for hz0, hz1 in blocked:
            if hz0 > z:
                runs.append((z, hz0))
            z = max(z, hz1)
        if z < z1:
            runs.append((z, z1))
        for r0, r1 in runs:
            if r1 - r0 < 1e-4:
                continue
            size = (s1 - s0, thick, r1 - r0) if axis == "y" else (thick, s1 - s0, r1 - r0)
            loc = (mid, plane, (r0 + r1) / 2) if axis == "y" else (plane, mid, (r0 + r1) / 2)
            box(f"{prefix}{k}", size, loc, mat, bevel=0)
            k += 1


def window(prefix, axis, plane, out, c, zs, w, h, K, shutters=False, sash_group=None):
    """A double-hung window in a hole centred at c (along the wall), sill at zs, w x h: casing, sill, two sashes with
    muntins (2 over 2), glass in the Glass group. `out` = +1/-1: which side of the plane is outside."""
    def at(u, d, z):
        return (u, plane + out * d, z) if axis == "y" else (plane + out * d, u, z)

    def sz(su, sd, sz_):
        return (su, sd, sz_) if axis == "y" else (sd, su, sz_)
    set_group("Win")
    cw = 0.45
    box(f"{prefix}CasL", sz(cw, 0.25, h + cw), at(c - w / 2 - cw / 2, 0.42, zs + h / 2 + cw / 2), K["trim"], bevel=0.04)
    box(f"{prefix}CasR", sz(cw, 0.25, h + cw), at(c + w / 2 + cw / 2, 0.42, zs + h / 2 + cw / 2), K["trim"], bevel=0.04)
    box(f"{prefix}Head", sz(w + 2 * cw + 0.4, 0.32, 0.55), at(c, 0.45, zs + h + cw + 0.2), K["trim"], bevel=0.05)
    box(f"{prefix}HeadCap", sz(w + 2 * cw + 0.7, 0.5, 0.12), at(c, 0.5, zs + h + cw + 0.52), K["trim"], bevel=0.03)
    box(f"{prefix}Sill", sz(w + 2 * cw + 0.3, 0.75, 0.16), at(c, 0.55, zs - 0.08), K["trim"], bevel=0.04)
    box(f"{prefix}Apron", sz(w + 0.2, 0.2, 0.45), at(c, 0.36, zs - 0.4), K["trim"], bevel=0.03)
    # jambs inside the hole
    box(f"{prefix}JambL", sz(0.12, 0.6, h), at(c - w / 2 + 0.06, 0.0, zs + h / 2), K["trim"], bevel=0)
    box(f"{prefix}JambR", sz(0.12, 0.6, h), at(c + w / 2 - 0.06, 0.0, zs + h / 2), K["trim"], bevel=0)
    box(f"{prefix}JambT", sz(w, 0.6, 0.12), at(c, 0.0, zs + h - 0.06), K["trim"], bevel=0)
    for lower in (False, True):
        g = sash_group if (lower and sash_group) else "Win"
        set_group(g)
        z0 = zs + (0.08 if lower else h / 2 - 0.04)
        sh = h / 2 - 0.04
        d = 0.12 if lower else -0.06
        fr = 0.22
        for nm, su, szz, uu, zz in (("L", fr, sh, c - w / 2 + 0.12 + fr / 2, z0 + sh / 2), ("R", fr, sh, c + w / 2 - 0.12 - fr / 2, z0 + sh / 2),
                                     ("B", w - 0.24, fr, c, z0 + fr / 2), ("T", w - 0.24, fr * 0.8, c, z0 + sh - fr * 0.4),
                                     ("M", 0.07, sh, c, z0 + sh / 2)):
            box(f"{prefix}{'Lo' if lower else 'Up'}{nm}", sz(su, 0.16, szz), at(uu, d, zz), K["trim"], bevel=0)
        set_group("Glass")
        box(f"{prefix}{'Lo' if lower else 'Up'}Pane", sz(w - 0.5, 0.03, sh - 0.4), at(c, d, z0 + sh / 2), K["glass"], bevel=0)
    set_group("Win")
    if shutters:
        for side in (-1, 1):
            u = c + side * (w / 2 + cw + 0.95)
            box(f"{prefix}Sh{side}", sz(1.7, 0.14, h + 0.2), at(u, 0.5, zs + h / 2 + 0.1), K["shutter"], bevel=0.03)
            n = int(h / 0.38)
            for i in range(n):           # louvres
                box(f"{prefix}Sh{side}L{i}", sz(1.4, 0.08, 0.2), at(u, 0.6, zs + 0.4 + i * (h - 0.6) / max(1, n - 1)), K["shutter"], bevel=0,
                    rot=((0.5, 0, 0) if axis == "y" else (0, 0.5, 0)))


def turned_post(name, x, y, z0, z1, K):
    """a square porch post with a turned middle"""
    box(f"{name}Base", (0.85, 0.85, 1.2), (x, y, z0 + 0.6), K["trim"], bevel=0.05)
    box(f"{name}Cap", (0.85, 0.85, 1.0), (x, y, z1 - 0.5), K["trim"], bevel=0.05)
    prof = [(0.32, 0), (0.36, 0.1), (0.24, 0.3), (0.3, 0.45), (0.22, 0.6), (0.28, 0.85), (0.32, 1.0)]
    L = z1 - z0 - 2.2
    for i, ((r0, t0), (r1, t1)) in enumerate(zip(prof, prof[1:])):
        cyl(f"{name}T{i}", (r0 + r1) / 2, (t1 - t0) * L, (x, y, z0 + 1.2 + (t0 + t1) / 2 * L), K["trim"], verts=12, bevel=0)


# ================================================================== WickHouse

def wick_house(M):
    K = kit(M)
    W, D = 30.0, 22.0
    X0, X1, Y0, Y1 = -W / 2, W / 2, -D / 2, D / 2
    ZF, ZT = 1.6, 21.6             # floor (top of foundation), wall top
    T = 0.6                        # wall thickness
    PITCH = math.radians(38)
    RIDGE = ZT + (D / 2) * math.tan(PITCH)

    # ---- the brick foundation
    set_group("Brick")
    for nm, size, loc in (("F", (W + 0.3, 0.9, ZF), (0, Y0, ZF / 2)), ("B", (W + 0.3, 0.9, ZF), (0, Y1, ZF / 2)),
                          ("L", (0.9, D, ZF), (X0, 0, ZF / 2)), ("R", (0.9, D, ZF), (X1, 0, ZF / 2))):
        box(f"Found{nm}", size, loc, K["place"], bevel=0)
    # the chimney (right side, outside the wall), up through the eaves
    CX, CY = X1 + 1.3, 3.0
    box("ChimneyLow", (2.6, 4.0, ZT - 0.0), (CX, CY, ZT / 2), K["place"], bevel=0)
    box("ChimneyHigh", (2.2, 3.2, RIDGE + 3 - ZT), (CX - 0.2, CY, (ZT + RIDGE + 3) / 2), K["place"], bevel=0)

    # ---- walls (siding) with openings
    set_group("Siding")
    front_holes = [(-6.0, -2.0, ZF, ZF + 8.0),                     # front door
                   (-13.4, -9.4, ZF + 3.0, ZF + 8.0),                 # parlour window
                   (2.5, 6.5, ZF + 3.0, ZF + 8.0), (9.5, 13.5, ZF + 3.0, ZF + 8.0),   # living room pair
                   (-12.0, -8.0, ZF + 12.4, ZF + 17.4),               # upstairs left
                   (-2.0, 0.5, ZF + 13.4, ZF + 16.4),                 # bathroom (small)
                   (6.5, 11.0, ZF + 11.8, ZF + 17.0)]                 # THE BEDROOM WINDOW (low sill: steps out onto the porch roof)
    wall("WallF", "y", Y0, X0, X1, ZF, ZT, T, front_holes, K["place"])
    back_holes = [(6.0, 9.5, ZF, ZF + 8.0),                           # kitchen door
                  (0.5, 5.0, ZF + 3.6, ZF + 8.0),                     # kitchen window
                  (-12.0, -8.0, ZF + 3.0, ZF + 8.0), (-12.0, -8.0, ZF + 12.4, ZF + 17.4), (4.0, 8.0, ZF + 12.4, ZF + 17.4)]
    wall("WallB", "y", Y1, X0, X1, ZF, ZT, T, back_holes, K["place"])
    side_holes = [(-4.0, 0.0, ZF + 3.0, ZF + 8.0), (-4.0, 0.0, ZF + 12.4, ZF + 17.4)]
    wall("WallL", "x", X0, Y0, Y1, ZF, ZT, T, side_holes, K["place"])
    wall("WallR", "x", X1, Y0, Y1, ZF, ZT, T, [(-7.0, -3.0, ZF + 3.0, ZF + 8.0), (-7.0, -3.0, ZF + 12.4, ZF + 17.4)], K["place"])
    # the gable ends (triangles of siding)
    for nm, x in (("L", X0), ("R", X1)):
        bot = [(x - T / 2, Y0, ZT), (x - T / 2, Y1, ZT), (x - T / 2, 0, RIDGE)]
        top = [(x + T / 2, Y0, ZT), (x + T / 2, Y1, ZT), (x + T / 2, 0, RIDGE)]
        solid(f"Gable{nm}", bot, top, K["place"])
    # an attic vent in each gable (Main, below)

    # ---- the roof: two shingle planes on a 0.35 deck, 1.2 eaves overhang and 1.0 rake overhang
    set_group("Roof")
    OV, RK, TH = 1.2, 1.0, 0.35
    zov = ZT - OV * math.tan(PITCH)
    for nm, s in (("F", -1), ("B", 1)):
        e_y = s * (D / 2 + OV)
        bot = [(X0 - RK, e_y, zov), (X1 + RK, e_y, zov), (X1 + RK, 0, RIDGE), (X0 - RK, 0, RIDGE)]
        top = [(x, y, z + TH / math.cos(PITCH)) for x, y, z in bot]
        ob = solid(f"Roof{nm}", bot, top, K["place"])
        slope = Vector((0, -s * math.cos(PITCH), math.sin(PITCH)))
        _quad_uv(ob, (X0 - RK, e_y, zov), (1 if s < 0 else -1, 0, 0), tuple(slope), TILES["Roof"][1])
        ob["nh_keep_uv"] = 1
    # the porch's shed roof: from the wall at z 12.9 (under the bedroom sill) down to the porch front
    PY0, PY1 = Y0 - 7.0, Y0                 # porch depth
    PX0, PX1 = -10.0, X1
    PZW, PZF = ZF + 11.2, ZF + 9.0          # porch roof height at the wall / at the front edge
    bot = [(PX0 - 0.6, PY0 - 0.8, PZF - 0.15), (PX1 + 0.6, PY0 - 0.8, PZF - 0.15), (PX1 + 0.6, PY1, PZW), (PX0 - 0.6, PY1, PZW)]
    top = [(x, y, z + 0.3) for x, y, z in bot]
    ob = solid("PorchRoof", bot, top, K["place"])
    ps = Vector((0, PY1 - PY0 + 0.8, PZW - PZF + 0.15)).normalized()
    _quad_uv(ob, (PX0 - 0.6, PY0 - 0.8, PZF - 0.15), (1, 0, 0), tuple(ps), TILES["Roof"][1])
    ob["nh_keep_uv"] = 1

    # ---- trim (Main)
    set_group("Main")
    for x in (X0, X1):                 # corner boards
        for y in (Y0, Y1):
            box(f"Corner{x}{y}", (0.75, 0.75, ZT - ZF + 0.2), (x, y, (ZF + ZT) / 2), K["trim"], bevel=0.05)
    box("WaterTableF", (W + 0.9, 0.85, 0.35), (0, Y0, ZF + 0.12), K["trim"], bevel=0.05)
    box("WaterTableB", (W + 0.9, 0.85, 0.35), (0, Y1, ZF + 0.12), K["trim"], bevel=0.05)
    box("WaterTableL", (0.85, D + 0.9, 0.35), (X0, 0, ZF + 0.12), K["trim"], bevel=0.05)
    box("WaterTableR", (0.85, D + 0.9, 0.35), (X1, 0, ZF + 0.12), K["trim"], bevel=0.05)
    for nm, y in (("F", Y0), ("B", Y1)):                                # frieze boards under the eaves, fascia, gutters
        box(f"Frieze{nm}", (W + 0.8, 0.8, 0.9), (0, y, ZT - 0.45), K["trim"], bevel=0.04)
        s = -1 if y < 0 else 1
        ey = s * (D / 2 + OV)
        box(f"Fascia{nm}", (W + 2 * RK + 0.2, 0.18, 0.75), (0, ey + s * 0.05, zov + 0.05), K["trim"], bevel=0.03)
        box(f"Soffit{nm}", (W + 2 * RK, OV, 0.12), (0, y + s * OV / 2, zov - 0.25), K["trim"], bevel=0)
        # gutter: a half-round trough with end caps
        g = box(f"Gutter{nm}", (W + 2 * RK + 0.2, 0.5, 0.45), (0, ey + s * 0.35, zov - 0.1), K["gutter"], bevel=0.12, segments=3)
    for nm, x in (("L", X0), ("R", X1)):                                # rake boards up the gables
        for s in (-1, 1):
            a = Vector((x, s * (D / 2 + OV), zov + 0.25))
            b = Vector((x, 0, RIDGE + 0.25))
            mid = (a + b) / 2
            L = (b - a).length
            ang = math.atan2(b.z - a.z, -(b.y - a.y) * s) * s
            box(f"Rake{nm}{s}", (0.3, L, 0.75), (x + (RK if x > 0 else -RK) + (0.1 if x > 0 else -0.1), mid.y, mid.z), K["trim"], bevel=0.03,
                rot=(-s * PITCH, 0, 0))
        # an attic vent: a louvred lancet in the gable
        vx = x + (0.35 if x > 0 else -0.35)
        box(f"Vent{nm}", (0.2, 2.0, 2.6), (vx, 0, RIDGE - 4.5), K["trim"], bevel=0.05)
        for i in range(6):
            box(f"Vent{nm}L{i}", (0.25, 1.6, 0.18), (vx + (0.05 if x > 0 else -0.05), 0, RIDGE - 5.5 + i * 0.4), K["shutter"], bevel=0.01)
    box("Ridge", (W + 2 * RK + 0.2, 0.7, 0.3), (0, 0, RIDGE + 0.4), K["trim"], bevel=0.08)
    # chimney cap and flue pots
    box("ChimCap", (2.7, 3.7, 0.35), (CX - 0.2, CY, RIDGE + 3.15), K["step"], bevel=0.05)
    for k in (-0.6, 0.6):
        cyl(f"Pot{k}", 0.32, 1.0, (CX - 0.2, CY + k, RIDGE + 3.8), K["step"], verts=16, bevel=0.03)

    # windows
    window("WinDoorParlour", "y", Y0, -1, -11.4, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinLiving1", "y", Y0, -1, 4.5, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinLiving2", "y", Y0, -1, 11.5, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinUpL", "y", Y0, -1, -10.0, ZF + 12.4, 4.0, 5.0, K, shutters=True)
    window("WinBath", "y", Y0, -1, -0.75, ZF + 13.4, 2.5, 3.0, K)
    window("WinBed", "y", Y0, -1, 8.75, ZF + 11.8, 4.5, 5.2, K, shutters=False, sash_group="BedSash")
    window("WinKitchen", "y", Y1, 1, 2.75, ZF + 3.6, 4.5, 4.4, K)
    window("WinBackL", "y", Y1, 1, -10.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinBackUL", "y", Y1, 1, -10.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinBackUR", "y", Y1, 1, 6.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinSideL", "x", X0, -1, -2.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinSideLU", "x", X0, -1, -2.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinSideR", "x", X1, 1, -5.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinSideRU", "x", X1, 1, -5.0, ZF + 12.4, 4.0, 5.0, K)

    # ---- the front door: a six-panel red door with a half-moon fanlight, casing, a brass knob, the house number
    set_group("Main")
    dc, dw, dh = -4.0, 4.0, 8.0
    box("DoorCasL", (0.55, 0.3, dh + 0.6), (dc - dw / 2 - 0.27, Y0 - 0.42, ZF + dh / 2 + 0.3), K["trim"], bevel=0.04)
    box("DoorCasR", (0.55, 0.3, dh + 0.6), (dc + dw / 2 + 0.27, Y0 - 0.42, ZF + dh / 2 + 0.3), K["trim"], bevel=0.04)
    box("DoorHead", (dw + 1.6, 0.4, 0.7), (dc, Y0 - 0.45, ZF + dh + 0.6), K["trim"], bevel=0.05)
    box("DoorPedim", (dw + 2.0, 0.55, 0.16), (dc, Y0 - 0.5, ZF + dh + 1.0), K["trim"], bevel=0.03)
    box("Door", (dw - 0.1, 0.22, dh - 0.1), (dc, Y0 - 0.05, ZF + dh / 2), K["door"], bevel=0.04)
    for r in range(3):                     # raised panels
        for cc in (-1, 1):
            hgt = (1.4, 2.4, 2.4)[r]
            zc = ZF + (1.2, 3.6, 6.3)[r]
            box(f"DoorPanel{r}{cc}", (1.35, 0.1, hgt), (dc + cc * 0.95, Y0 - 0.19, zc), K["door"], bevel=0.08)
    sphere_k = cyl("DoorKnob", 0.16, 0.25, (dc + 1.45, Y0 - 0.3, ZF + 3.6), K["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.06)
    box("DoorPlate", (0.3, 0.06, 0.9), (dc + 1.45, Y0 - 0.18, ZF + 3.7), K["brass"], bevel=0.02)
    box("DoorKick", (dw - 0.6, 0.05, 0.5), (dc, Y0 - 0.17, ZF + 0.35), K["brass"], bevel=0.01)
    box("NumPlate", (1.2, 0.08, 0.7), (dc + 3.1, Y0 - 0.33, ZF + 6.4), K["brass"], bevel=0.04)
    # mail slot
    box("MailSlot", (1.0, 0.06, 0.25), (dc, Y0 - 0.18, ZF + 4.8), K["brass"], bevel=0.02)

    # ---- the porch: deck, steps, posts, railing, beam, ceiling, the porch light
    set_group("Porch")
    deck_z = ZF
    box("PorchDeck", (PX1 - PX0, PY1 - PY0, 0.35), ((PX0 + PX1) / 2, (PY0 + PY1) / 2, deck_z - 0.175), K["deck"], bevel=0.03)
    box("PorchSkirt", (PX1 - PX0, 0.25, deck_z - 0.35), ((PX0 + PX1) / 2, PY0 + 0.12, (deck_z - 0.35) / 2), K["trim"], bevel=0.03)
    for i in range(int((PX1 - PX0) / 1.0)):                              # lattice under the skirt edge
        x = PX0 + 0.5 + i * 1.0
        box(f"Lattice{i}", (0.12, 0.1, 1.5), (x, PY0 + 0.2, 0.6), K["trim"], bevel=0, rot=(0, 0.6, 0))
        box(f"LatticeB{i}", (0.12, 0.1, 1.5), (x, PY0 + 0.22, 0.6), K["trim"], bevel=0, rot=(0, -0.6, 0))
    sx0, sx1 = dc - 3.0, dc + 3.0
    for s in range(3):                                                    # three stone steps
        box(f"Step{s}", (sx1 - sx0, 1.1, (s + 1) * deck_z / 3), ((sx0 + sx1) / 2, PY0 - 0.55 - (2 - s) * 1.1, (s + 1) * deck_z / 6), K["step"], bevel=0.05)
    posts = [PX0 + 0.45, sx0 - 0.3, sx1 + 0.3, 6.0, PX1 - 0.45]
    for i, x in enumerate(posts):
        turned_post(f"Post{i}", x, PY0 + 0.45, deck_z, PZF - 0.1, K)
    box("PorchBeam", (PX1 - PX0 + 0.4, 0.9, 1.0), ((PX0 + PX1) / 2, PY0 + 0.45, PZF - 0.55), K["trim"], bevel=0.05)
    # railing between posts, except the stair gap
    spans = [(posts[0], posts[1]), (posts[2], posts[3]), (posts[3], posts[4])]
    for i, (a, b) in enumerate(spans):
        a, b = a + 0.45, b - 0.45
        box(f"RailTop{i}", (b - a, 0.4, 0.22), ((a + b) / 2, PY0 + 0.45, deck_z + 3.0), K["trim"], bevel=0.05)
        box(f"RailBot{i}", (b - a, 0.3, 0.2), ((a + b) / 2, PY0 + 0.45, deck_z + 0.45), K["trim"], bevel=0.04)
        n = int((b - a) / 0.55)
        for j in range(n):
            x = a + (j + 0.5) * (b - a) / n
            box(f"Bal{i}_{j}", (0.18, 0.18, 2.5), (x, PY0 + 0.45, deck_z + 1.7), K["trim"], bevel=0)
    # side railings back to the house
    for x in (PX0 + 0.45,):
        box("RailSide", (0.4, PY1 - PY0 - 0.9, 0.22), (x, (PY0 + PY1) / 2 + 0.2, deck_z + 3.0), K["trim"], bevel=0.05)
        n = int((PY1 - PY0 - 1.2) / 0.55)
        for j in range(n):
            y = PY0 + 0.9 + (j + 0.5) * (PY1 - PY0 - 1.2) / n
            box(f"BalS{j}", (0.18, 0.18, 2.5), (x, y, deck_z + 1.7), K["trim"], bevel=0)
    # porch ceiling (beadboard look) and the light
    box("PorchCeil", (PX1 - PX0, PY1 - PY0, 0.12), ((PX0 + PX1) / 2, (PY0 + PY1) / 2, PZF + 0.2), K["trim"], bevel=0)
    set_group("Main")
    lx, ly, lz = dc + 3.2, Y0 - 0.5, ZF + 6.6
    box("LampBack", (0.6, 0.1, 1.0), (lx, Y0 - 0.36, lz), K["iron"], bevel=0.03)
    box("LampArm", (0.12, 0.6, 0.12), (lx, ly, lz + 0.3), K["iron"], bevel=0.02)
    for cx_ in (-0.32, 0.32):
        for cy_ in (-0.32, 0.32):
            box(f"LampBar{cx_}{cy_}", (0.06, 0.06, 0.9), (lx + cx_, ly - 0.45 + cy_, lz - 0.1), K["iron"], bevel=0)
    box("LampTop", (0.85, 0.85, 0.18), (lx, ly - 0.45, lz + 0.4), K["iron"], bevel=0.04)
    box("LampBottom", (0.75, 0.75, 0.12), (lx, ly - 0.45, lz - 0.55), K["iron"], bevel=0.03)
    set_group("Glow")
    cyl("LampBulb", 0.2, 0.45, (lx, ly - 0.45, lz - 0.15), K["bulb"], verts=12, bevel=0.08)
    set_group("Glass")
    box("LampGlass", (0.62, 0.62, 0.8), (lx, ly - 0.45, lz - 0.1), K["glass"], bevel=0)
    set_group("Main")

    # ---- the drainpipe: from the porch roof's front right gutter down to a splash block (the climb down)
    gx, gy = PX1 + 0.3, PY0 - 1.0
    box("PorchGutter", (PX1 - PX0 + 1.4, 0.45, 0.4), ((PX0 + PX1) / 2 + 0.3, PY0 - 1.0, PZF - 0.3), K["gutter"], bevel=0.12, segments=3)
    box("Downspout", (0.42, 0.42, PZF - 0.6), (gx, gy, (PZF - 0.6) / 2 + 0.3), K["gutter"], bevel=0.05)
    for zb in (2.0, 5.5, 8.5):
        box(f"SpoutStrap{zb}", (0.55, 0.5, 0.12), (gx, gy, zb), K["gutter"], bevel=0.02)
    box("SpoutShoe", (0.42, 0.9, 0.42), (gx, gy - 0.35, 0.3), K["gutter"], bevel=0.05, rot=(0.3, 0, 0))
    box("SplashBlock", (0.9, 1.6, 0.18), (gx, gy - 1.1, 0.09), K["step"], bevel=0.04)
    # the main roof's downspouts at the back corners
    for x in (X0 - 0.4, X1 - 0.4):
        box(f"BackSpout{x}", (0.42, 0.42, zov - 0.3), (x + 0.5 * (1 if x < 0 else -1) * 0, Y1 + OV + 0.3, (zov - 0.3) / 2 + 0.15), K["gutter"], bevel=0.05)

    # ---- the back door: half glass, a little stoop
    bdc, bdw = 7.75, 3.5
    set_group("Main")
    box("BDoor", (bdw - 0.1, 0.22, 7.9), (bdc, Y1 + 0.05, ZF + 3.95), K["trim"], bevel=0.04)
    box("BDoorCasL", (0.5, 0.3, 8.5), (bdc - bdw / 2 - 0.25, Y1 + 0.42, ZF + 4.2), K["trim"], bevel=0.04)
    box("BDoorCasR", (0.5, 0.3, 8.5), (bdc + bdw / 2 + 0.25, Y1 + 0.42, ZF + 4.2), K["trim"], bevel=0.04)
    box("BDoorHead", (bdw + 1.4, 0.4, 0.6), (bdc, Y1 + 0.45, ZF + 8.5), K["trim"], bevel=0.04)
    cyl("BDoorKnob", 0.15, 0.25, (bdc - 1.2, Y1 + 0.25, ZF + 3.6), K["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.06)
    set_group("Glass")
    box("BDoorPane", (bdw - 1.2, 0.05, 3.2), (bdc, Y1 + 0.1, ZF + 5.8), K["glass"], bevel=0)
    set_group("Main")
    box("Stoop", (5.5, 3.0, ZF), (bdc, Y1 + 1.5 + 0.45, ZF / 2), K["step"], bevel=0.05)
    box("StoopStep", (5.5, 1.2, ZF / 2), (bdc, Y1 + 3.6 + 0.45, ZF / 4), K["step"], bevel=0.05)
    set_group("Main")
    return (W + 4, D + 16, RIDGE + 4.5)


BUILDERS["WickHouse"] = wick_house


# ================================================================== the Alder Lane street kit
from nh_props_batch3 import sphere, cone  # noqa: E402
from nh_props_batch4 import lathe, prism, hoop  # noqa: E402


def street_lamp(M):
    """A cast-iron streetlamp, 13 studs: a fluted column on an octagonal base, a scrolled bracket, a four-sided lantern
    with a glowing bulb, the town crest's oak leaf cast on the base"""
    K = kit(M)
    iron = material("WFLampIron", "NH_Iron", tint=(0.07, 0.085, 0.075), scale=0.45, rough_add=0.05, wear=0.45, wear_metal=True)
    lathe("Base", [(0.95, 0), (0.95, 0.25), (0.8, 0.35), (0.8, 1.1), (0.62, 1.3), (0.5, 1.4), (0.42, 1.6), (0, 1.6)], iron, seg=8)
    lathe("Column", [(0.36, 1.6), (0.3, 2.0), (0.28, 9.6), (0, 9.6)], iron, seg=24, flute=(12, 0.08))
    lathe("Collar", [(0.42, 9.5), (0.48, 9.7), (0.38, 9.95), (0.46, 10.2), (0.3, 10.4), (0, 10.4)], iron, seg=24)
    # scroll bracket under the lantern
    for s in (-1, 1):
        pts = [Vector((s * (0.3 + 0.55 * math.sin(t * math.pi * 0.9)), 0, 9.0 + 1.3 * t)) for t in (i / 12 for i in range(13))]
        tube(f"Scroll{s}", pts, 0.06, iron)
        hoop(f"Curl{s}", (s * 0.42, 0, 9.05), 0.16, "y", iron, thick=0.05)
    # lantern: tapering, four glazed sides
    lathe("LanBase", [(0.5, 10.4), (0.55, 10.55), (0.42, 10.7), (0, 10.7)], iron, seg=4)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        box(f"LanPost{i}", (0.07, 0.07, 1.5), (0.5 * math.cos(a), 0.5 * math.sin(a), 11.45), iron, bevel=0, rot=(0, 0, a))
    lathe("LanRoof", [(0.85, 12.2), (0.82, 12.3), (0.35, 12.85), (0.12, 13.0), (0, 13.0)], iron, seg=4)
    lathe("Finial", [(0.1, 13.0), (0.14, 13.15), (0.05, 13.35), (0.09, 13.45), (0, 13.7)], iron, seg=8)
    set_group("Glass")
    lathe("LanGlass", [(0.38, 10.7), (0.62, 12.2), (0, 12.2)], K["glass"], seg=4)
    set_group("Glow")
    sphere("Bulb", 0.22, (0, 0, 11.35), K["bulb"], seg=12, rings=8, scale=(1, 1, 1.4))
    set_group("Main")
    return (2, 2, 13.7)


def mailbox(M):
    """14 Alder Lane's mailbox: a navy steel box on a white post, the red flag up, brass letters on its side"""
    K = kit(M)
    navy = material("WFMailNavy", "NH_PaintedMetal", tint=(0.08, 0.13, 0.22), scale=1.0, wear=0.4, wear_metal=True)
    red = material("WFFlagRed", "NH_PaintedMetal", tint=(0.42, 0.05, 0.04), scale=1.0, wear=0.3, wear_metal=True)
    box("Post", (0.55, 0.55, 3.6), (0, 0, 1.8), K["trim"], bevel=0.05)
    box("PostCap", (0.75, 0.75, 0.2), (0, 0, 3.66), K["trim"], bevel=0.04)
    box("Arm", (2.6, 0.6, 0.3), (0.3, 0, 3.9), K["trim"], bevel=0.04)
    box("Brace", (0.25, 0.45, 1.3), (-0.45, 0, 3.2), K["trim"], bevel=0.03, rot=(0, -0.7, 0))
    # the box: a flat bottom and a round top, long axis along X, door at -X (the road)
    L, R_ = 2.4, 0.55
    prof = [(-R_, 0.0)] + [(R_ * math.cos(math.pi - a), 0.5 + R_ * math.sin(math.pi - a)) for a in (math.pi * i / 16 for i in range(17))] + [(R_, 0.0)]
    pts = [(y, z) for y, z in prof]
    me_pts = [(-y, z) for y, z in pts]
    ob = prism("Box", [(z * 0 + yy, z) for yy, z in me_pts], 0.3, L, navy, plane="YZ", bevel=0.02)
    ob.location = (0.3, 0, 4.05)
    box("Door", (0.08, 1.16, 1.06), (0.3 - L / 2 - 0.04, 0, 4.05 + 0.52), navy, bevel=0.03)
    box("Latch", (0.12, 0.25, 0.12), (0.3 - L / 2 - 0.1, 0, 4.05 + 0.3), K["brass"], bevel=0.02)
    # the flag (up): an arm and a plate on the +Y side
    box("FlagArm", (0.12, 0.06, 1.4), (0.75, 0.6, 4.75), red, bevel=0.01)
    box("FlagPlate", (0.6, 0.06, 0.45), (0.95, 0.6, 5.25), red, bevel=0.02)
    cyl("FlagPivot", 0.08, 0.1, (0.75, 0.6, 4.2), K["iron"], rot=(math.pi / 2, 0, 0), verts=12)
    # the lettering plate on the -Y side (canvas)
    set_group("Sign")
    box("LetterPlate", (1.9, 0.02, 0.62), (0.3, -0.565, 4.05 + 0.42), K["place"], bevel=0)
    set_group("Main")
    return (3.2, 1.6, 5.6)


def _pickets(prefix, x0, x1, K, h=3.6, w=0.38, gap=0.3, y=0.0):
    n = int((x1 - x0) / (w + gap))
    for i in range(n):
        x = x0 + gap / 2 + w / 2 + i * (w + gap) + ((x1 - x0) - n * (w + gap)) / 2
        prism(f"{prefix}{i}", [(x - w / 2, 0.15), (x + w / 2, 0.15), (x + w / 2, h - 0.35), (x, h), (x - w / 2, h - 0.35)], y, 0.12, K["trim"], plane="XZ")


def picket_fence(M):
    """an 8-stud run of white picket fence between two capped posts"""
    K = kit(M)
    for x in (-4.0, 4.0):
        box(f"Post{x}", (0.5, 0.5, 4.3), (x, 0, 2.15), K["trim"], bevel=0.04)
        box(f"PostCap{x}", (0.7, 0.7, 0.18), (x, 0, 4.35), K["trim"], bevel=0.04)
        lathe(f"PostBall{x}", [(0.0, 4.44), (0.22, 4.55), (0.26, 4.72), (0.18, 4.9), (0, 4.98)], K["trim"], seg=16, loc=(x, 0, 0))
    for z in (0.9, 2.9):
        box(f"Rail{z}", (7.5, 0.22, 0.35), (0, 0.17, z), K["trim"], bevel=0.03)
    _pickets("Pk", -3.75, 3.75, K, y=-0.03)
    return (8.8, 0.8, 5.0)


def picket_gate(M):
    """the garden gate: two posts with a little arched header, the gate swings on its left hinges"""
    K = kit(M)
    for x in (-2.25, 2.25):
        box(f"Post{x}", (0.55, 0.55, 5.4), (x, 0, 2.7), K["trim"], bevel=0.04)
        lathe(f"PostBall{x}", [(0.0, 5.4), (0.24, 5.52), (0.28, 5.72), (0.2, 5.92), (0, 6.0)], K["trim"], seg=16, loc=(x, 0, 0))
    arch = [(x, 4.9 + 0.55 * math.sin(math.pi * (x + 2.0) / 4.0)) for x in (-2.0 + 4.0 * i / 16 for i in range(17))]
    prism("Arch", [(-2.0, 4.6)] + arch + [(2.0, 4.6)], 0.0, 0.3, K["trim"], plane="XZ", bevel=0.02)
    set_group("Gate", hinge=(-1.95, 0, 0), swing=-1)
    for z in (0.9, 2.7):
        box(f"GRail{z}", (3.8, 0.2, 0.32), (0.0, 0.15, z), K["trim"], bevel=0.03)
    box("GBrace", (0.22, 0.18, 2.2), (0.0, 0.15, 1.8), K["trim"], bevel=0.02, rot=(0, 0.9, 0))
    _pickets("GPk", -1.9, 1.9, K, h=3.4, y=-0.02)
    for z in (0.9, 2.7):
        box(f"Hinge{z}", (0.5, 0.06, 0.16), (-1.75, 0.27, z), K["iron"], bevel=0.01)
    box("GLatch", (0.35, 0.1, 0.12), (1.75, 0.27, 2.0), K["iron"], bevel=0.01)
    set_group("Main")
    return (5.2, 0.8, 6.0)


def kennel(M):
    """Biscuit's kennel: a little red-painted clapboard doghouse with a shingled gable roof, an arched doorway, a
    hand-painted BISCUIT board over it, a blanket inside and his bowl out front"""
    K = kit(M)
    red = material("WFKennelRed", "NH_DeskWood", tint=(0.42, 0.11, 0.08), scale=0.25, rough_add=0.15, wear=0.5)
    W, D, H = 4.2, 5.0, 3.0
    # walls: horizontal boards (each its own slightly proud strip), with the doorway cut out of the front
    for i in range(int(H / 0.38)):
        z = 0.3 + i * 0.38 + 0.19
        for nm, size, loc in (("B", (W, 0.18, 0.4), (0, D / 2, z)), ("L", (0.18, D, 0.4), (-W / 2, 0, z)), ("R", (0.18, D, 0.4), (W / 2, 0, z))):
            box(f"Board{nm}{i}", size, loc, red, bevel=0.03, rot=(0.06 if nm == "B" else 0, 0.06 if nm in "LR" else 0, 0))
        # front: leave the doorway (x -0.95..0.95, z < 2.4)
        if z < 2.4:
            for sx in (-1, 1):
                box(f"BoardF{i}{sx}", (W / 2 - 0.95, 0.18, 0.4), (sx * (0.95 + (W / 2 - 0.95) / 2), -D / 2, z), red, bevel=0.03, rot=(-0.06, 0, 0))
        else:
            box(f"BoardF{i}", (W, 0.18, 0.4), (0, -D / 2, z), red, bevel=0.03, rot=(-0.06, 0, 0))
    # the doorway arch and trim
    ring_pts = [(0.95 * math.cos(a), 1.9 + 0.95 * math.sin(a)) for a in (math.pi * i / 20 for i in range(21))]
    prism("DoorArchFill", [(1.15, 1.9), (1.15, 3.2), (-1.15, 3.2), (-1.15, 1.9)] + list(reversed(ring_pts)), -D / 2 - 0.02, 0.2, red, plane="XZ")
    arc = [Vector((1.08 * math.cos(a), -D / 2 - 0.16, 1.9 + 1.08 * math.sin(a))) for a in (math.pi * i / 24 for i in range(25))]
    tube("ArchTrim", arc, 0.13, K["trim"], square=True)
    for sx in (-1, 1):
        box(f"DoorTrim{sx}", (0.26, 0.26, 1.6), (sx * 1.08, -D / 2 - 0.16, 1.1), K["trim"], bevel=0.02)
    box("Floor", (W, D, 0.3), (0, 0, 0.15), K["deck"], bevel=0.03)
    for x in (-W / 2, W / 2):
        for y in (-D / 2, D / 2):
            box(f"Corner{x}{y}", (0.3, 0.3, H + 0.1), (x, y, 0.3 + H / 2), K["trim"], bevel=0.03)
    # gables
    zt = 0.3 + H
    rise = 1.7
    for y, nm in ((-D / 2, "F"), (D / 2, "B")):
        prism(f"Gable{nm}", [(-W / 2, zt), (W / 2, zt), (0, zt + rise)], y, 0.18, red, plane="XZ")
    # roof (shingle, tiled with plane UVs)
    set_group("Roof")
    pitch = math.atan2(rise, W / 2)
    for s, nm in ((-1, "L"), (1, "R")):
        ex = s * (W / 2 + 0.5)
        ez = zt - 0.5 * math.tan(pitch)
        bot = [(ex, -D / 2 - 0.5, ez), (ex, D / 2 + 0.5, ez), (0, D / 2 + 0.5, zt + rise), (0, -D / 2 - 0.5, zt + rise)]
        top = [(x, y, z + 0.18) for x, y, z in bot]
        ob = solid(f"Roof{nm}", bot, top, K["place"])
        slope = Vector((-s * math.cos(pitch), 0, math.sin(pitch)))
        _quad_uv(ob, (ex, -D / 2 - 0.5, ez), (0, 1, 0), tuple(slope), 3.0)
        ob["nh_keep_uv"] = 1
    set_group("Main")
    box("RidgeCap", (0.35, D + 1.1, 0.22), (0, 0, zt + rise + 0.2), K["trim"], bevel=0.05)
    # the name board over the door (canvas)
    set_group("Sign")
    box("NameBoard", (2.0, 0.06, 0.5), (0, -D / 2 - 0.2, zt + 0.42), K["place"], bevel=0)
    set_group("Main")
    box("NameBack", (2.14, 0.08, 0.62), (0, -D / 2 - 0.15, zt + 0.42), K["trim"], bevel=0.02)
    # a plaid blanket inside, the bowl outside (red enamel with a white rim)
    blanket = material("WFBlanket", base=(0.42, 0.2, 0.14), rough=0.95, wear=0.0, dirt=0.4)
    box("Blanket", (2.8, 3.2, 0.14), (0.1, 0.6, 0.37), blanket, bevel=0.06, segments=3, rot=(0, 0, 0.08))
    bowl = material("WFBowl", base=(0.6, 0.08, 0.06), rough=0.25, metal=0.0, wear=0.3, dirt=0.4)
    lathe("Bowl", [(0.0, 0.0), (0.5, 0.0), (0.62, 0.32), (0.66, 0.36), (0.56, 0.36), (0.48, 0.1), (0, 0.1)], bowl, seg=28, loc=(1.6, -D / 2 - 1.2, 0))
    lathe("Kibble", [(0.0, 0.1), (0.45, 0.1), (0.4, 0.26), (0.0, 0.3)], material("WFKibble", base=(0.42, 0.24, 0.12), rough=0.9, wear=0.0),
          seg=20, loc=(1.6, -D / 2 - 1.2, 0), jitter=(0.06, 3))
    return (W + 1.2, D + 3.0, zt + rise + 0.4)


def hydrant(M):
    """a squat red fire hydrant with chrome caps"""
    red = material("WFHydrant", "NH_PaintedMetal", tint=(0.48, 0.06, 0.04), scale=1.0, wear=0.15, wear_metal=True, dirt=0.8)
    chrome = material("WFChrome", base=(0.8, 0.8, 0.82), rough=0.18, metal=1.0, wear=0.2)
    lathe("Body", [(0.75, 0), (0.75, 0.2), (0.55, 0.3), (0.5, 1.9), (0.62, 2.0), (0.62, 2.2), (0.5, 2.3), (0.45, 2.7), (0.2, 2.95), (0, 3.0)], red, seg=24)
    lathe("Nut", [(0.14, 2.95), (0.14, 3.2), (0, 3.2)], chrome, seg=5)
    for s, ax in ((-1, "x"), (1, "x"), (1, "y")):
        if ax == "x":
            cyl(f"Port{s}{ax}", 0.24, 0.4, (s * 0.62, 0, 1.6), chrome, rot=(0, math.pi / 2, 0), verts=16, bevel=0.03)
        else:
            cyl(f"Port{s}{ax}", 0.32, 0.4, (0, -0.62, 1.4), chrome, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.03)
    for i in range(6):
        a = i * math.pi / 3
        cyl(f"Bolt{i}", 0.06, 0.1, (0.62 * math.cos(a), 0.62 * math.sin(a), 0.22), chrome, verts=6, bevel=0)
    return (1.6, 1.6, 3.2)


def sidewalk(M):
    """a 16-stud run of the street edge: concrete sidewalk (8 deep), a granite curb, the gutter and 8 studs of road"""
    K = kit(M)
    set_group("Walk")
    box("Walk", (16, 8, 0.6), (0, 4.0, 0.3), K["place"], bevel=0)
    set_group("Asphalt")
    box("Road", (16, 8, 0.3), (0, -4.8, 0.15 - 0.6), K["place"], bevel=0)
    set_group("Main")
    curb = material("WFCurb", "NH_Limestone", tint=(0.55, 0.55, 0.56), scale=0.4, wear=0.4, dirt=1.0)
    box("Curb", (16, 0.8, 1.0), (0, -0.4, 0.1), curb, bevel=0.08)
    box("Gutter", (16, 1.0, 0.1), (0, -1.3, -0.4), curb, bevel=0.02)
    # a storm drain grate at one end
    for i in range(7):
        box(f"Grate{i}", (0.12, 0.9, 0.08), (5.5 + i * 0.3, -1.3, -0.34), K["iron"], bevel=0)
    return (16, 16.8, 1.0)


# ================================================================== your bedroom (inside WickHouse, the same origin)

def bedroom(M):
    """The player's bedroom, upper front right of WickHouse, built in the house's own space (place it at the house's
    CFrame): x 1 to 14.7, y -10.7 to 0, floor at z 12, ceiling 21.2. The front window (x 6.5 to 11) is the way out.
    The classic gag: pillows stuffed under the duvet in the shape of a sleeping kid. The wallpaper is WF_Wallpaper;
    a female character gets WF_WallpaperRose on the same piece (docs/expansion/15 §2)."""
    K = kit(M)
    oak = material("WFOak", "NH_DeskWood", tint=(0.6, 0.42, 0.26), scale=0.25, rough_add=0.05, wear=0.4)
    paint_w = material("WFFurnWhite", base=(0.84, 0.82, 0.78), rough=0.5, wear=0.3, dirt=0.6)
    quilt = material("WFQuilt", base=(0.12, 0.2, 0.36), rough=0.92, wear=0.0, dirt=0.3)
    sheet = material("WFSheet", base=(0.86, 0.84, 0.8), rough=0.9, wear=0.0, dirt=0.3)
    cloth_r = material("WFCurtain", base=(0.5, 0.2, 0.12), rough=0.9, wear=0.0, dirt=0.4)
    X0, X1, Y0, Y1, Z0, Z1 = 1.0, 14.7, -10.7, 0.0, 12.0, 21.2
    # ---- floor, wallpaper, ceiling, mouldings
    set_group("Floor")
    box("Floor", (X1 - X0, Y1 - Y0, 0.4), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z0 - 0.2), K["place"], bevel=0)
    set_group("Paper")
    wall("PapF", "y", Y0 + 0.05, X0, X1, Z0, Z1, 0.1, [(6.5, 11.0, 13.4, 18.6)], K["place"])
    wall("PapB", "y", Y1 - 0.05, X0, X1, Z0, Z1, 0.1, [(11.8, 14.2, Z0, Z0 + 7.4)], K["place"])
    wall("PapL", "x", X0 + 0.05, Y0, Y1, Z0, Z1, 0.1, [(-3.6, -0.6, Z0, Z0 + 7.4)], K["place"])
    wall("PapR", "x", X1 - 0.05, Y0, Y1, Z0, Z1, 0.1, [(-7.0, -3.0, 14.0, 19.0)], K["place"])
    set_group("Main")
    box("Ceiling", (X1 - X0, Y1 - Y0, 0.2), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z1 + 0.1), paint_w, bevel=0)
    for nm, size, loc in (("F", (X1 - X0, 0.15, 0.55), ((X0 + X1) / 2, Y0 + 0.17, Z0 + 0.27)), ("B", (X1 - X0, 0.15, 0.55), ((X0 + X1) / 2, Y1 - 0.17, Z0 + 0.27)),
                          ("L", (0.15, Y1 - Y0, 0.55), (X0 + 0.17, (Y0 + Y1) / 2, Z0 + 0.27)), ("R", (0.15, Y1 - Y0, 0.55), (X1 - 0.17, (Y0 + Y1) / 2, Z0 + 0.27))):
        box(f"Base{nm}", size, loc, K["trim"], bevel=0.02)
        box(f"Crown{nm}", (size[0], size[1], 0.4), (loc[0], loc[1], Z1 - 0.2), K["trim"], bevel=0.05)
    c, w_, zs, h_ = 8.75, 4.5, 13.4, 5.2
    for s_ in (-1, 1):
        box(f"InCas{s_}", (0.4, 0.2, h_ + 0.4), (c + s_ * (w_ / 2 + 0.2), Y0 + 0.2, zs + h_ / 2), K["trim"], bevel=0.03)
        box(f"RCas{s_}", (0.2, 0.4, 5.4), (X1 - 0.2, -5.0 + s_ * 2.2, 16.5), K["trim"], bevel=0.03)
    box("InHead", (w_ + 1.0, 0.22, 0.45), (c, Y0 + 0.2, zs + h_ + 0.25), K["trim"], bevel=0.03)
    box("InStool", (w_ + 1.0, 0.7, 0.14), (c, Y0 + 0.4, zs - 0.05), K["trim"], bevel=0.03)
    box("RHead", (0.22, 5.0, 0.45), (X1 - 0.2, -5.0, 19.25), K["trim"], bevel=0.03)
    box("RStool", (0.7, 5.0, 0.14), (X1 - 0.4, -5.0, 13.95), K["trim"], bevel=0.03)
    # the closet (back wall) and the bedroom door (left wall, swings into the hall)
    for s_ in (-1, 1):
        box(f"DCas{s_}", (0.2, 0.45, 7.6), (X0 + 0.2, -2.1 + s_ * 1.72, Z0 + 3.8), K["trim"], bevel=0.03)
        box(f"CCas{s_}", (0.45, 0.2, 7.6), (13.0 + s_ * 1.42, Y1 - 0.2, Z0 + 3.8), K["trim"], bevel=0.03)
    box("DHead", (0.22, 3.9, 0.45), (X0 + 0.2, -2.1, Z0 + 7.6), K["trim"], bevel=0.03)
    box("CHead", (3.3, 0.22, 0.45), (13.0, Y1 - 0.2, Z0 + 7.6), K["trim"], bevel=0.03)
    box("Closet", (2.4, 0.15, 7.4), (13.0, Y1 - 0.1, Z0 + 3.7), paint_w, bevel=0.03)
    for r in range(2):
        box(f"ClosetPanel{r}", (1.8, 0.08, 2.8 if r else 3.2), (13.0, Y1 - 0.2, Z0 + (5.4 if r else 1.9)), paint_w, bevel=0.06)
    cyl("ClosetKnob", 0.13, 0.2, (12.1, Y1 - 0.3, Z0 + 3.5), K["brass"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.05)
    set_group("Door", hinge=(X0 + 0.1, -3.6, Z0), swing=1)
    box("BedDoor", (0.15, 3.0, 7.4), (X0 + 0.1, -2.1, Z0 + 3.7), paint_w, bevel=0.03)
    for r in range(2):
        box(f"BedDoorPanel{r}", (0.08, 2.3, 2.8 if r else 3.2), (X0 + 0.2, -2.1, Z0 + (5.4 if r else 1.9)), paint_w, bevel=0.06)
    cyl("BedDoorKnob", 0.13, 0.2, (X0 + 0.3, -1.0, Z0 + 3.5), K["brass"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.05)
    set_group("Main")

    # ---- the bed (headboard to the back wall) and the decoy under the duvet
    bx0, bx1, by0, by1 = 3.0, 7.6, -7.6, -0.25
    for x in (bx0 + 0.2, bx1 - 0.2):
        box(f"HeadPost{x}", (0.4, 0.4, 4.2), (x, by1 - 0.2, Z0 + 2.1), oak, bevel=0.05)
        box(f"FootPost{x}", (0.4, 0.4, 2.6), (x, by0 + 0.2, Z0 + 1.3), oak, bevel=0.05)
        lathe(f"HeadKnob{x}", [(0, Z0 + 4.2), (0.24, Z0 + 4.3), (0.22, Z0 + 4.5), (0, Z0 + 4.62)], oak, seg=16, loc=(x, by1 - 0.2, 0))
    box("Headboard", (bx1 - bx0 - 0.4, 0.2, 2.0), ((bx0 + bx1) / 2, by1 - 0.2, Z0 + 2.9), oak, bevel=0.06)
    box("Footboard", (bx1 - bx0 - 0.4, 0.2, 1.2), ((bx0 + bx1) / 2, by0 + 0.2, Z0 + 1.7), oak, bevel=0.05)
    box("Rails", (bx1 - bx0 - 0.4, by1 - by0 - 0.4, 0.5), ((bx0 + bx1) / 2, (by0 + by1) / 2, Z0 + 0.9), oak, bevel=0.04)
    box("Mattress", (bx1 - bx0 - 0.5, by1 - by0 - 0.5, 0.9), ((bx0 + bx1) / 2, (by0 + by1) / 2, Z0 + 1.6), sheet, bevel=0.18, segments=3)
    box("Pillow", (3.2, 1.3, 0.55), ((bx0 + bx1) / 2, by1 - 1.1, Z0 + 2.25), sheet, bevel=0.25, segments=4, rot=(0.25, 0, 0.05))
    box("Duvet", (bx1 - bx0 - 0.2, by1 - by0 - 2.0, 0.3), ((bx0 + bx1) / 2, (by0 + by1) / 2 - 0.8, Z0 + 2.15), quilt, bevel=0.14, segments=3)
    for nm, r, loc, sc in (("Head", 0.55, ((bx0 + bx1) / 2 + 0.2, by1 - 2.2, Z0 + 2.4), (1.0, 0.9, 0.7)),
                           ("Body", 0.75, ((bx0 + bx1) / 2, -4.3, Z0 + 2.35), (1.25, 2.3, 0.6)),
                           ("Knee", 0.55, ((bx0 + bx1) / 2 + 0.5, -6.2, Z0 + 2.5), (1.2, 1.0, 0.75))):
        sphere(f"Lump{nm}", r, loc, quilt, seg=20, rings=12, scale=sc)
    box("DuvetFold", (bx1 - bx0 - 0.1, 0.7, 0.35), ((bx0 + bx1) / 2, -1.9, Z0 + 2.3), sheet, bevel=0.15, segments=3)
    box("DuvetHang", (0.2, by1 - by0 - 2.2, 1.0), (bx1 + 0.05, (by0 + by1) / 2 - 0.8, Z0 + 1.75), quilt, bevel=0.08)

    # ---- nightstand with the alarm clock (11:58) and a lamp
    nx = 8.6
    box("NightStand", (1.6, 1.4, 2.2), (nx + 0.8, -0.95, Z0 + 1.1), paint_w, bevel=0.05)
    box("NSDrawer", (1.3, 0.06, 0.6), (nx + 0.8, -1.68, Z0 + 1.6), paint_w, bevel=0.04)
    cyl("NSKnob", 0.08, 0.12, (nx + 0.8, -1.74, Z0 + 1.6), K["brass"], rot=(math.pi / 2, 0, 0), verts=10)
    box("ClockBody", (0.9, 0.5, 0.48), (nx + 0.55, -1.1, Z0 + 2.45), material("WFClockBody", base=(0.08, 0.08, 0.09), rough=0.4, wear=0.1), bevel=0.06)
    set_group("Clock")
    box("ClockFace", (0.74, 0.02, 0.36), (nx + 0.55, -1.36, Z0 + 2.45), K["place"], bevel=0)
    set_group("Main")
    lathe("LampBase", [(0, Z0 + 2.2), (0.3, Z0 + 2.2), (0.28, Z0 + 2.3), (0.08, Z0 + 2.4), (0.06, Z0 + 3.2), (0, Z0 + 3.2)], K["brass"], seg=16, loc=(nx + 1.2, -0.7, 0))
    lathe("LampShade", [(0.6, Z0 + 3.0), (0.38, Z0 + 3.75), (0.36, Z0 + 3.75), (0.58, Z0 + 3.02)], material("WFShade", base=(0.86, 0.78, 0.6), rough=0.9, wear=0.0),
          seg=24, loc=(nx + 1.2, -0.7, 0))

    # ---- the desk (left wall, front corner), chair, laptop, books, lamp, the backpack (one prank's evidence)
    dx0, dx1, dy0, dy1 = X0 + 0.15, X0 + 2.6, -10.3, -5.4
    box("DeskTop", (dx1 - dx0, dy1 - dy0, 0.2), ((dx0 + dx1) / 2, (dy0 + dy1) / 2, Z0 + 2.5), oak, bevel=0.04)
    for y in (dy0 + 0.15, dy1 - 0.15):
        box(f"DeskLeg{y}", (dx1 - dx0 - 0.1, 0.18, 2.4), ((dx0 + dx1) / 2, y, Z0 + 1.2), oak, bevel=0.03)
    box("DeskDrawer", (dx1 - dx0 - 0.2, 1.6, 0.6), ((dx0 + dx1) / 2, dy1 - 1.0, Z0 + 2.1), oak, bevel=0.03)
    box("Laptop", (1.3, 1.0, 0.08), ((dx0 + dx1) / 2 + 0.2, -8.0, Z0 + 2.64), material("WFLaptop", base=(0.32, 0.33, 0.36), rough=0.35, metal=0.6, wear=0.2), bevel=0.03)
    box("LaptopSticker", (0.35, 0.35, 0.01), ((dx0 + dx1) / 2 + 0.3, -7.8, Z0 + 2.685), material("WFSticker", base=(0.95, 0.65, 0.15), rough=0.4, wear=0.0), bevel=0.0)
    hs = (0.22, 0.18, 0.26)
    for i, col_ in enumerate(((0.5, 0.1, 0.08), (0.12, 0.24, 0.4), (0.2, 0.34, 0.2))):
        box(f"Book{i}", (0.9, 1.25, hs[i]), ((dx0 + dx1) / 2 - 0.1, -6.4, Z0 + 2.6 + sum(hs[:i]) + hs[i] / 2),
            material(f"WFBook{i}", base=col_, rough=0.7, wear=0.3), bevel=0.02, rot=(0, 0, 0.1 * (i - 1)))
    lathe("DeskLampBase", [(0, Z0 + 2.6), (0.3, Z0 + 2.6), (0.25, Z0 + 2.7), (0, Z0 + 2.72)], K["iron"], seg=16, loc=(dx0 + 0.6, -9.7, 0))
    tube("DeskLampArm", [Vector((dx0 + 0.6, -9.7, Z0 + 2.7)), Vector((dx0 + 0.8, -9.5, Z0 + 3.9)), Vector((dx0 + 1.4, -9.1, Z0 + 3.7))], 0.05, K["iron"])
    cone("DeskLampHead", 0.32, 0.12, 0.5, (dx0 + 1.5, -9.0, Z0 + 3.55), K["iron"], rot=(0.4, 0.6, 0))
    cx_, cy_ = dx1 + 1.0, -7.8
    box("ChairSeat", (1.4, 1.4, 0.2), (cx_, cy_, Z0 + 1.6), oak, bevel=0.05)
    for ox in (-0.55, 0.55):
        for oy in (-0.55, 0.55):
            box(f"ChairLeg{ox}{oy}", (0.15, 0.15, 1.5), (cx_ + ox, cy_ + oy, Z0 + 0.75), oak, bevel=0.02)
    box("ChairBack", (0.15, 1.4, 1.6), (cx_ + 0.62, cy_, Z0 + 2.5), oak, bevel=0.04)
    bag = material("WFBackpack", base=(0.18, 0.3, 0.22), rough=0.9, wear=0.2, dirt=0.7)
    box("Pack", (1.2, 0.7, 1.6), (cx_ + 0.2, cy_ - 1.4, Z0 + 0.8), bag, bevel=0.25, segments=3, rot=(0.15, 0, 0.3))
    box("PackPocket", (0.9, 0.25, 0.7), (cx_ + 0.15, cy_ - 1.8, Z0 + 0.55), bag, bevel=0.12, segments=2, rot=(0.15, 0, 0.3))
    box("PackPatch", (0.42, 0.05, 0.42), (cx_ + 0.15, cy_ - 1.95, Z0 + 0.6), material("WFPatch", base=(0.88, 0.7, 0.24), rough=0.8, wear=0.0), bevel=0.02, rot=(0.15, 0, 0.3))
    tube("PackStrap", [Vector((cx_ - 0.3, cy_ - 1.1, Z0 + 1.5)), Vector((cx_ - 0.6, cy_ - 1.6, Z0 + 0.9)), Vector((cx_ - 0.4, cy_ - 1.9, Z0 + 0.15))], 0.08, bag, square=True)

    # ---- the dresser (right wall, front) and a clothes pile by the closet
    box("Dresser", (1.8, 3.0, 3.2), (X1 - 1.0, -9.0, Z0 + 1.6), oak, bevel=0.05)
    for r in range(3):
        box(f"DrDrawer{r}", (0.06, 2.6, 0.85), (X1 - 1.92, -9.0, Z0 + 0.6 + r * 1.0), oak, bevel=0.04)
        for s_ in (-1, 1):
            cyl(f"DrKnob{r}{s_}", 0.08, 0.12, (X1 - 1.98, -9.0 + s_ * 0.8, Z0 + 0.6 + r * 1.0), K["brass"], rot=(0, math.pi / 2, 0), verts=10)
    box("DrawerSock", (0.12, 0.6, 0.12), (X1 - 1.98, -8.4, Z0 + 2.5), material("WFSock", base=(0.8, 0.3, 0.25), rough=0.95, wear=0.0), bevel=0.05, rot=(0, 0.6, 0))
    tee = material("WFTee", base=(0.65, 0.62, 0.55), rough=0.95, wear=0.0)
    jean = material("WFJean", base=(0.16, 0.22, 0.36), rough=0.95, wear=0.0)
    for i, (m_, loc, sc) in enumerate(((jean, (11.6, -1.9, Z0 + 0.2), (1.4, 0.8, 0.3)), (tee, (12.4, -2.4, Z0 + 0.35), (1.0, 0.9, 0.35)),
                                       (jean, (12.9, -1.7, Z0 + 0.25), (0.8, 0.5, 0.25)))):
        sphere(f"Clothes{i}", 0.7, loc, m_, seg=16, rings=8, scale=sc)

    # ---- the braided rug, the ceiling light, the curtains
    rug_cols = [(0.5, 0.18, 0.12), (0.78, 0.66, 0.42), (0.2, 0.32, 0.24), (0.5, 0.18, 0.12), (0.24, 0.3, 0.46), (0.78, 0.66, 0.42)]
    rug_mats = [material(f"WFRug{k}", base=rug_cols[k], rough=0.95, wear=0.0) for k in range(6)]
    set_group("Rug")
    for i in range(12):
        hoop(f"Rug{i}", (9.6, -5.6, Z0 + 0.08), 0.3 + i * 0.28, "Z", rug_mats[i % 6], thick=0.15)
    set_group("Main")
    lathe("CeilBase", [(0, Z1 - 0.1), (0.5, Z1 - 0.1), (0.45, Z1 - 0.2), (0, Z1 - 0.2)], K["brass"], seg=20, loc=(8.0, -5.4, 0))
    set_group("Glass")
    lathe("CeilBowl", [(0, Z1 - 0.9), (0.5, Z1 - 0.7), (0.7, Z1 - 0.35), (0.72, Z1 - 0.2), (0, Z1 - 0.2)],
          material("WFFrosted", base=(0.95, 0.93, 0.88), rough=0.5, wear=0.0), seg=24, loc=(8.0, -5.4, 0))
    set_group("Main")
    cyl("CurtainRod", 0.07, 6.6, (8.75, Y0 + 0.5, 19.2), K["brass"], rot=(0, math.pi / 2, 0), verts=12)
    for s_ in (-1, 1):
        for k in range(5):
            cyl(f"Curtain{s_}{k}", 0.2, 6.4, (8.75 + s_ * (2.6 + k * 0.28), Y0 + 0.55 + 0.08 * (k % 2), 15.9), cloth_r, verts=10)
        box(f"Tieback{s_}", (1.6, 0.6, 0.15), (8.75 + s_ * 3.1, Y0 + 0.6, 15.6), K["brass"], bevel=0.04)

    # ---- the pennant (cut to its shape) over the bed, the posters (canvases) on the back wall
    set_group("Pennant")
    pl, ph, px0, pz0 = 4.0, 1.5, (bx0 + bx1) / 2 - 2.0, 17.6
    xh = px0 + pl * 150 / 2048
    prism("Pennant", [(px0, pz0), (px0 + pl, pz0 + ph / 2), (px0, pz0 + ph)][::-1] if False else
          [(px0, pz0), (xh, pz0), (px0 + pl, pz0 + ph / 2), (xh, pz0 + ph), (px0, pz0 + ph)], Y1 - 0.12, 0.04, K["place"], plane="XZ")
    set_group("PosterBand")
    box("PosterBand", (2.0, 0.04, 3.0), (9.4, Y1 - 0.12, 16.8), K["place"], bevel=0)
    set_group("PosterMoon")
    box("PosterMoon", (1.6, 0.04, 2.4), (2.0, Y1 - 0.12, 16.6), K["place"], bevel=0)
    set_group("Main")
    for x, z, hw, hh in ((9.4, 16.8, 1.0, 1.5), (2.0, 16.6, 0.8, 1.2)):
        for cx2 in (-hw + 0.1, hw - 0.1):
            box(f"Tack{x}{cx2}", (0.1, 0.06, 0.1), (x + cx2, Y1 - 0.15, z + hh - 0.1), K["iron"], bevel=0)
    for gx in (px0 + 0.1, px0 + 0.1):
        pass
    return (X1 - X0 + 2, Y1 - Y0 + 2, Z1)


BUILDERS.update({
    "WFBedroom": bedroom,
    "WFStreetLamp": street_lamp, "WFMailbox": mailbox, "WFPicketFence": picket_fence, "WFPicketGate": picket_gate,
    "WFKennel": kennel, "WFHydrant": hydrant, "WFSidewalk": sidewalk,
})
TILES.update({"Walk": ("WF_Sidewalk", 8.0), "Asphalt": ("WF_Road", 12.0), "Floor": ("WF_FloorOak", 6.0), "Paper": ("WF_Wallpaper", 4.0)})
P.CANVAS.update({"WFMailbox_Sign": "WF_Mailbox14", "WFKennel_Sign": "WF_Biscuit", "WFBedroom_Clock": "WF_Clock1158",
                 "WFBedroom_Pennant": "WF_Pennant", "WFBedroom_PosterBand": "WF_PosterBand", "WFBedroom_PosterMoon": "WF_PosterMoon"})

for _n in BUILDERS:
    for _g, (_set, _t) in TILES.items():
        P.TILED[f"{_n}_{_g}"] = (_set, _t)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"WickHouse": 1.25})
P.PREVIEW_PAD.update({"WFBedroom": 1.1})


INSIDE = {"WFBedroom": ((13.4, -10.0, 18.6), (5.0, -1.5, 13.4), (8.0, -5.4, 20.4))}   # camera, target, lamp


def inside_render(name, cam, target, lamp):
    """an interior view: a wide camera in the room's corner, the ceiling light on"""
    sc = bpy.context.scene
    camd = bpy.data.cameras.new("InCam")
    camd.lens = 16
    co = bpy.data.objects.new("InCam", camd)
    sc.collection.objects.link(co)
    co.location = cam
    d = Vector(target) - Vector(cam)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    for k, (loc, e, col) in enumerate(((lamp, 900, (1.0, 0.85, 0.65)), ((8.75, -13.5, 16.0), 1500, (0.55, 0.62, 1.0)))):
        ld = bpy.data.lights.new(f"InL{k}", "POINT")
        ld.energy = e
        ld.color = col
        ld.shadow_soft_size = 1.0
        lo = bpy.data.objects.new(f"InL{k}", ld)
        lo.location = loc
        sc.collection.objects.link(lo)
    sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}_inside.png")
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
        if n in INSIDE:
            inside_render(n, *INSIDE[n])
