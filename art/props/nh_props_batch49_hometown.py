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
for _n in BUILDERS:
    for _g, (_set, _t) in TILES.items():
        P.TILED[f"{_n}_{_g}"] = (_set, _t)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"WickHouse": 1.25})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
