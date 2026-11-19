"""Props batch 49 (2026-11-18): Wickfield, the tutorial's hometown (docs/expansion/15-Tutorial-The-Last-Normal-Night.md).
Warm small-town autumn: painted clapboard, white trim, red brick, asphalt shingles, brass, lamplight. Original designs.

  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch49_hometown.py -- <Prop|all> [--size 2048] [--samples 64] [--gpu]

WickHouse  14 Alder Lane, the player's house: two storeys of cream lap siding on a brick foundation (38 x 28 studs, walls
           1.6 to 21.6), a shingled gable roof (ridge along X), a brick chimney on the right. The front (-Y): a full porch
           (x -12 to 19, 7 deep) with turned posts, a railing, three steps up to the red front door, and a shed porch roof
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


WSRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_wickfield")
FSRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_fabric")


def wmat(name, set_name, tint, scale, **kw):
    """a material from the Wickfield neutral sets (source_wickfield: NH_PaintedWood, NH_Cotton, NH_Denim, NH_Enamel), tinted"""
    return material(name, os.path.join(WSRC, set_name), tint=tint, scale=scale, metal=0.0, **kw)


def fmat(name, set_name, tint, scale, **kw):
    return material(name, os.path.join(FSRC, set_name), tint=tint, scale=scale, metal=0.0, **kw)


def kit(M):
    return {
        "trim": wmat("WFTrim", "NH_PaintedWood", (0.98, 0.96, 0.92), 0.3, wear=0.25, dirt=0.7),
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

_orig_canvas_material = P.canvas_material


def _canvas_material(ob, image):
    """Wickfield canvases carry full PBR (art/hometown/posters_hq.py writes <image>_canvas_{normal,rough,metal}.png): load
    every map that exists, else the plain canvas material."""
    _orig_canvas_material(ob, image)
    base = os.path.join(P.OUT_TEX, f"{image}_canvas")
    if not os.path.exists(base + "_normal.png"):
        return
    nt = ob.data.materials[0].node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def tex(path):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        uv = next((n for n in nt.nodes if n.type == "UVMAP"), None)
        return t
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(base + "_normal.png").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex(base + "_rough.png").outputs["Color"], bs.inputs["Roughness"])
    nt.links.new(tex(base + "_metal.png").outputs["Color"], bs.inputs["Metallic"])
    if os.path.exists(base + "_emissive.png"):                 # neon: the colour glows through the emissive mask
        col = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and n.image.colorspace_settings.name != "Non-Color")
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(col.outputs["Color"], mul.inputs["A"])
        nt.links.new(tex(base + "_emissive.png").outputs["Color"], mul.inputs["B"])
        nt.links.new(mul.outputs["Result"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = 4.0


P.canvas_material = _canvas_material


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
    W, D = 38.0, 28.0
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
    CX, CY = X1 + 1.3, 5.0
    box("ChimneyLow", (2.6, 4.0, ZT - 0.0), (CX, CY, ZT / 2), K["place"], bevel=0)
    box("ChimneyHigh", (2.2, 3.2, RIDGE + 3 - ZT), (CX - 0.2, CY, (ZT + RIDGE + 3) / 2), K["place"], bevel=0)

    # ---- walls (siding) with openings
    set_group("Siding")
    front_holes = [(-8.0, -4.0, ZF, ZF + 8.0),                     # front door
                   (-17.0, -13.0, ZF + 3.0, ZF + 8.0),                # parlour window
                   (2.0, 6.0, ZF + 3.0, ZF + 8.0), (10.0, 14.0, ZF + 3.0, ZF + 8.0),   # living room pair
                   (-15.0, -11.0, ZF + 12.4, ZF + 17.4),              # upstairs left
                   (-4.0, -1.5, ZF + 13.4, ZF + 16.4),                # bathroom (small)
                   (9.5, 14.0, ZF + 11.8, ZF + 17.0)]                 # THE BEDROOM WINDOW (low sill: steps out onto the porch roof)
    wall("WallF", "y", Y0, X0, X1, ZF, ZT, T, front_holes, K["place"])
    back_holes = [(8.0, 11.5, ZF, ZF + 8.0),                          # kitchen door
                  (1.0, 5.5, ZF + 3.6, ZF + 8.0),                     # kitchen window
                  (-15.0, -11.0, ZF + 3.0, ZF + 8.0), (-15.0, -11.0, ZF + 12.4, ZF + 17.4), (6.0, 10.0, ZF + 12.4, ZF + 17.4)]
    wall("WallB", "y", Y1, X0, X1, ZF, ZT, T, back_holes, K["place"])
    side_holes = [(-5.0, -1.0, ZF + 3.0, ZF + 8.0), (-5.0, -1.0, ZF + 12.4, ZF + 17.4)]
    wall("WallL", "x", X0, Y0, Y1, ZF, ZT, T, side_holes, K["place"])
    wall("WallR", "x", X1, Y0, Y1, ZF, ZT, T, [(-9.0, -5.0, ZF + 3.0, ZF + 8.0), (-9.0, -5.0, ZF + 12.4, ZF + 17.4)], K["place"])
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
    PX0, PX1 = -12.0, X1
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
    window("WinDoorParlour", "y", Y0, -1, -15.0, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinLiving1", "y", Y0, -1, 4.0, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinLiving2", "y", Y0, -1, 12.0, ZF + 3.0, 4.0, 5.0, K, shutters=True)
    window("WinUpL", "y", Y0, -1, -13.0, ZF + 12.4, 4.0, 5.0, K, shutters=True)
    window("WinBath", "y", Y0, -1, -2.75, ZF + 13.4, 2.5, 3.0, K)
    window("WinBed", "y", Y0, -1, 11.75, ZF + 11.8, 4.5, 5.2, K, shutters=False, sash_group="BedSash")
    window("WinKitchen", "y", Y1, 1, 3.25, ZF + 3.6, 4.5, 4.4, K)
    window("WinBackL", "y", Y1, 1, -13.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinBackUL", "y", Y1, 1, -13.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinBackUR", "y", Y1, 1, 8.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinSideL", "x", X0, -1, -3.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinSideLU", "x", X0, -1, -3.0, ZF + 12.4, 4.0, 5.0, K)
    window("WinSideR", "x", X1, 1, -7.0, ZF + 3.0, 4.0, 5.0, K)
    window("WinSideRU", "x", X1, 1, -7.0, ZF + 12.4, 4.0, 5.0, K)

    # ---- the front door: a six-panel red door with a half-moon fanlight, casing, a brass knob, the house number
    set_group("Main")
    dc, dw, dh = -6.0, 4.0, 8.0
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
    posts = [PX0 + 0.45, sx0 - 0.3, sx1 + 0.3, 7.0, PX1 - 0.45]
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
    bdc, bdw = 9.75, 3.5
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
    set_group("Flag")
    box("FlagArm", (0.12, 0.06, 1.4), (0.75, 0.6, 4.75), red, bevel=0.01)
    box("FlagPlate", (0.6, 0.06, 0.45), (0.95, 0.6, 5.25), red, bevel=0.02)
    set_group("Main")
    cyl("FlagPivot", 0.08, 0.1, (0.75, 0.66, 4.2), K["iron"], rot=(math.pi / 2, 0, 0), verts=12)
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


# ================================================================== rigs and animation clips
# A prop's rig: one armature (a static Root, then a bone per moving part). Each moving part is its own piece (group) and is
# weighted only to its own bones; every other piece rides Root, so nothing else deforms. Clips are written in world terms
# (a rotation about the bone's head, a move), applied as Blender actions (exported in the FBX, rendered as preview strips) and
# saved to art/props/anim/<Prop>.json for the Studio step that turns them into KeyframeSequences.

RIG = {}      # prop -> dict(bones={name: (head, tail, parent)}, own={group: bone | [bones]})
CLIPS = {}    # prop -> {clip: dict(length=s, loop=bool, fps=30, keys={bone: fn(t) -> (axis, deg, (dx, dy, dz)) | [(axis, deg)...]})}
ANIM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anim")


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def back_out(t, s=1.4):
    """ease out with a little overshoot (the house style: overshoot, then settle)"""
    t = max(0.0, min(1.0, t)) - 1
    return 1 + t * t * ((s + 1) * t + s)


def rig_pieces(prop, objs):
    spec = RIG[prop]
    bones = {"Root": ((0, 0, 0), (0, 0, 1), None)}
    bones.update(spec["bones"])
    arm_data = bpy.data.armatures.new(f"{prop}Rig")
    arm = bpy.data.objects.new(f"{prop}Rig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    for bn, (h, t, _) in bones.items():
        b = eb.new(bn)
        b.head, b.tail = tuple(h), tuple(t)
    for bn, (_, _, par) in bones.items():
        if bn != "Root":
            eb[bn].parent = eb[par or "Root"]
    bpy.ops.object.mode_set(mode="OBJECT")

    def dist(p, a, b):
        ab = b - a
        u = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab))))
        return (p - (a + ab * u)).length
    for ob in objs:
        if ob.type != "MESH":
            continue
        grp = ob.name[len(prop) + 1:] if ob.name.startswith(prop + "_") else "Main"
        owner = spec["own"].get(grp, "Root")
        groups = {}

        def vg(bn):
            if bn not in groups:
                groups[bn] = ob.vertex_groups.new(name=bn)
            return groups[bn]
        mw = ob.matrix_world
        if isinstance(owner, str):
            vg(owner).add([v.index for v in ob.data.vertices], 1.0, "REPLACE")
        else:
            segs = [(bn, Vector(bones[bn][0]), Vector(bones[bn][1])) for bn in owner]
            for v in ob.data.vertices:
                p = mw @ v.co
                ds = sorted(((dist(p, a, b), bn) for bn, a, b in segs), key=lambda x: x[0])[:2]
                ws = [(bn, 1.0 / (d * d + 0.02)) for d, bn in ds]
                tot = sum(w for _, w in ws)
                for bn, w in ws:
                    vg(bn).add([v.index], w / tot, "REPLACE")
        md = ob.modifiers.new("Rig", "ARMATURE")
        md.object = arm
        ob.parent = arm
    make_clips(prop, arm, bones)
    print(f"[rig] {prop}: {len(bones)} bones, clips {list(CLIPS.get(prop, {}))}")
    return arm


def _delta(axis_deg_list, head, move):
    """T(head) R T(-head), then a move, as a 4x4 in armature space"""
    from mathutils import Matrix
    R = Matrix.Identity(4)
    for axis, deg in axis_deg_list:
        ax = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[axis] if isinstance(axis, str) else axis
        R = Matrix.Rotation(math.radians(deg), 4, Vector(ax)) @ R
    h = Vector(head)
    return Matrix.Translation(Vector(move)) @ Matrix.Translation(h) @ R @ Matrix.Translation(-h)


def make_clips(prop, arm, bones):
    import json
    clips = CLIPS.get(prop, {})
    if not clips:
        return
    os.makedirs(ANIM_DIR, exist_ok=True)
    out = {"prop": prop, "bones": {bn: {"head": list(h), "tail": list(t), "parent": p or ("Root" if bn != "Root" else None)}
                                   for bn, (h, t, p) in bones.items()}, "clips": {}}
    sc = bpy.context.scene
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    order = list(bones)                                    # parents are listed before children
    arm.animation_data_create()
    for cname, c in clips.items():
        fps = c.get("fps", 30)
        n = int(round(c["length"] * fps))
        act = bpy.data.actions.new(f"{prop}_{cname}")
        act.use_fake_user = True
        arm.animation_data.action = act
        frames = []
        for f in range(n + 1):
            t = f / fps
            deltas, rec = {}, {}
            for bn in order:
                par = bones[bn][2] or ("Root" if bn != "Root" else None)
                D = deltas.get(par) if par else None
                fn = c["keys"].get(bn)
                rots, move = [], (0, 0, 0)
                if fn:
                    r = fn(t)
                    if len(r) == 3 and not isinstance(r[0], (list, tuple)):
                        rots, move = [(r[0], r[1])], r[2]
                    else:
                        rots, move = r[0], r[1]
                own = _delta(rots, bones[bn][0], move)
                deltas[bn] = (D @ own) if D is not None else own
                if fn:
                    rec[bn] = {"rot": [[a if isinstance(a, str) else list(a), d] for a, d in rots], "move": list(move)}
            for bn in order:
                if bn == "Root":
                    continue
                pb = arm.pose.bones[bn]
                pb.rotation_mode = "QUATERNION"
                pb.matrix = deltas[bn] @ arm.data.bones[bn].matrix_local
                bpy.context.view_layer.update()
                pb.keyframe_insert("location", frame=f)
                pb.keyframe_insert("rotation_quaternion", frame=f)
            frames.append({"t": round(t, 4), "bones": rec})
        out["clips"][cname] = {"length": c["length"], "loop": c.get("loop", False), "fps": fps, "frames": frames}
        trk = arm.animation_data.nla_tracks.new()
        trk.name = cname
        trk.strips.new(cname, 0, act)
        trk.mute = True
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.ops.object.mode_set(mode="OBJECT")
    with open(os.path.join(ANIM_DIR, f"{prop}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    sc.frame_set(0)


_orig_export = P.export


def _export(objs, name, arm=None):
    """props with clips export their actions too (all actions, baked)"""
    if arm is None or name not in CLIPS:
        return _orig_export(objs, name, arm)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(P.OUT_FBX, f"{name}.fbx"), use_selection=True, object_types={"MESH", "ARMATURE"},
                             apply_unit_scale=True, global_scale=1.0, axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             path_mode="STRIP", embed_textures=False, add_leaf_bones=False, bake_anim=True,
                             bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True)


P.export = _export


def clip_strips(prop, cam=None, target=None, samples=24):
    """render each clip at its start, middle and end (3 frames): previews/_clip_<Prop>_<Clip>_<k>.png (art/hometown/clip_sheet.py
    lays them out)"""
    arm = bpy.data.objects.get(f"{prop}Rig")
    if arm is None or prop not in CLIPS:
        return
    sc = bpy.context.scene
    sc.cycles.samples = samples
    if cam is not None:
        camd = bpy.data.cameras.new("ClipCam")
        camd.lens = 22
        co = bpy.data.objects.new("ClipCam", camd)
        sc.collection.objects.link(co)
        co.location = cam
        co.rotation_euler = (Vector(target) - Vector(cam)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = co
    for ob in bpy.data.objects:                       # undo the open-door preview's turn
        if "nh_swing" in ob.keys():
            ob.rotation_euler = (0, 0, 0)
    for cname, c in CLIPS[prop].items():
        cc = CLIP_CAM.get(prop, {}).get(cname)
        if cc:
            co = bpy.data.objects.get("ClipCam") or bpy.data.objects.new("ClipCam", bpy.data.cameras.new("ClipCam"))
            if co.name not in sc.collection.objects:
                sc.collection.objects.link(co)
            co.data.lens = 24
            co.location = cc[0]
            co.rotation_euler = (Vector(cc[1]) - Vector(cc[0])).to_track_quat("-Z", "Y").to_euler()
            sc.camera = co
        arm.animation_data.action = bpy.data.actions.get(f"{prop}_{cname}")
        n = int(round(c["length"] * c.get("fps", 30)))
        for k, f in enumerate((0, n // 2, n)):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(P.OUT_PRE, f"_clip_{prop}_{cname}_{k}.png")
            bpy.ops.render.render(write_still=True)
    arm.animation_data.action = None
    sc.frame_set(0)
    print(f"[clips] {prop}: {list(CLIPS[prop])}")


def panel(name, x0, x1, z0, z1, y, mat, nu=6, nv=12, thick=0.02):
    """a flat sheet in the XZ plane at y, subdivided so a rig can bend it (a newspaper, a page), thickened"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [[bm.verts.new((x0 + (x1 - x0) * i / nu, y - thick / 2, z0 + (z1 - z0) * j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness = thick
    so.offset = 0.0
    return _finish(ob, mat, 0)


def drape(name, x0, x1, y0, y1, zfn, mat, nu=28, nv=40, thick=0.1):
    """a soft sheet over a height field z = zfn(x, y) (a duvet, a cloth), thickened downward, smooth shaded"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [[bm.verts.new((x0 + (x1 - x0) * i / nu, y0 + (y1 - y0) * j / nv, zfn(x0 + (x1 - x0) * i / nu, y0 + (y1 - y0) * j / nv)))
           for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    so = ob.modifiers.new("Thick", "SOLIDIFY")
    so.thickness = thick
    so.offset = -1.0
    return _finish(ob, mat, 0)


# ------------------------------------------------------------------ clip check: every item against every other one

ITEMS = []        # (item name, first part index) in build order; parts after it belong to it until the next


def item(name):
    ITEMS.append((name, len(P.PARTS)))


def clip_check(room_box, structure=("Room",), skip=("Floor",), eps=0.004):
    """Fail the build if any two items' meshes intersect (BVH triangle overlap, with modifiers), or any item leaves the
    room. Parts of the same item may touch. Structure items are tested against furniture, not against each other."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    bounds = [(n, i) for n, i in ITEMS] + [(None, len(P.PARTS))]
    owner = {}
    for (n, a), (_, b) in zip(bounds, bounds[1:]):
        for ob in P.PARTS[a:b]:
            owner[ob.name] = n
    bvh, bb = {}, {}
    bpy.context.view_layer.update()
    for ob in P.PARTS:
        if ob.name not in owner or ob.name in skip:
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ob.matrix_world
        verts = [mw @ v.co for v in me.vertices]
        polys = [list(p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
        if not verts:
            continue
        bvh[ob.name] = BVHTree.FromPolygons(verts, polys)
        lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
        hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
        bb[ob.name] = (lo, hi)
    bad = []
    names = list(bvh)
    (rx0, ry0, rz0), (rx1, ry1, rz1) = room_box
    for n in names:
        it = owner[n]
        if it in structure:
            continue
        lo, hi = bb[n]
        if lo.x < rx0 - eps or lo.y < ry0 - eps or lo.z < rz0 - eps or hi.x > rx1 + eps or hi.y > ry1 + eps or hi.z > rz1 + eps:
            bad.append(f"{it}/{n} leaves the room ({tuple(round(c, 2) for c in lo)} .. {tuple(round(c, 2) for c in hi)})")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ia, ib = owner[a], owner[b]
            if ia == ib or (ia in structure and ib in structure):
                continue
            (la, ha), (lb, hb) = bb[a], bb[b]
            if la.x > hb.x or lb.x > ha.x or la.y > hb.y or lb.y > ha.y or la.z > hb.z or lb.z > ha.z:
                continue
            if bvh[a].overlap(bvh[b]):
                bad.append(f"{ia}/{a} x {ib}/{b}")
    print(f"[clip] {len(names)} parts, {len(set(owner.values()))} items, {len(bad)} problems")
    for line in bad:
        print("[clip]  ", line)
    if bad:
        raise SystemExit("clip check failed")


# ================================================================== your bedroom (inside WickHouse, the same origin)

BED_ROOM = dict(X0=2.0, X1=18.7, Y0=-13.7, Y1=2.0, Z0=12.0, Z1=21.2)   # inner faces of the room (house space)
BED_WIN = (11.75, 4.5, 13.4, 5.2)                                       # the front window: centre x, width, sill z, height
BED_SIDE = (-7.0, 4.0, 14.0, 5.0)                                       # the right-side window: centre y, width, sill z, height


def bedroom(M):
    """The player's bedroom, upper front right of WickHouse (38 x 28), built in the house's own space (place it at the
    house's CFrame): 16.7 x 15.7 studs, floor at z 12, ceiling 21.2. The front window is the way out onto the porch roof.
    The classic gag: pillows stuffed under the duvet in the shape of a sleeping kid. Every item is clip-checked against
    every other one when it builds. The wallpaper is WF_Wallpaper; a female character gets WF_WallpaperRose on the same
    piece (docs/expansion/15 §2)."""
    ITEMS.clear()
    K = kit(M)
    oak = material("WFOak", "NH_DeskWood", tint=(0.6, 0.42, 0.26), scale=0.25, rough_add=0.05, wear=0.4)
    paint_w = wmat("WFFurnWhite", "NH_PaintedWood", (0.96, 0.94, 0.9), 0.3, wear=0.3, dirt=0.6)
    quilt = fmat("WFQuilt", "NH_Velvet", (0.16, 0.26, 0.46), 0.5, normal=0.7, wear=0.0, dirt=0.3)
    sheet = wmat("WFSheet", "NH_Cotton", (0.98, 0.96, 0.92), 0.15, wear=0.0, dirt=0.3)
    cloth_r = wmat("WFCurtain", "NH_Cotton", (0.66, 0.26, 0.16), 0.15, wear=0.0, dirt=0.4)
    R = BED_ROOM
    X0, X1, Y0, Y1, Z0, Z1 = R["X0"], R["X1"], R["Y0"], R["Y1"], R["Z0"], R["Z1"]
    G = 0.27                          # furniture stands this far from a wall (clear of the baseboard)
    wc, ww, wz, wh = BED_WIN
    sc_, sw, sz_, sh = BED_SIDE
    DOOR = (-7.8, -4.8)               # the bedroom door in the left wall (y range)
    CLO = (14.6, 17.0)                # the closet in the back wall (x range)

    # ---------------------------------------------------------------- the room (structure)
    item("Room")
    set_group("Floor")
    box("Floor", (X1 - X0, Y1 - Y0, 0.4), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z0 - 0.2), K["place"], bevel=0)
    set_group("Paper")
    wall("PapF", "y", Y0 + 0.05, X0, X1, Z0, Z1, 0.1, [(wc - ww / 2, wc + ww / 2, wz, wz + wh)], K["place"])
    wall("PapB", "y", Y1 - 0.05, X0, X1, Z0, Z1, 0.1, [(CLO[0], CLO[1], Z0, Z0 + 7.4)], K["place"])
    wall("PapL", "x", X0 + 0.05, Y0, Y1, Z0, Z1, 0.1, [(DOOR[0], DOOR[1], Z0, Z0 + 7.4)], K["place"])
    wall("PapR", "x", X1 - 0.05, Y0, Y1, Z0, Z1, 0.1, [(sc_ - sw / 2, sc_ + sw / 2, sz_, sz_ + sh)], K["place"])
    set_group("Main")
    box("Ceiling", (X1 - X0, Y1 - Y0, 0.2), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z1 + 0.1), paint_w, bevel=0)
    # baseboards (skipping the door and closet openings) and crown moulding
    def run_x(nm, y, x0, x1, gaps):
        cuts = [x0] + [g for gp in gaps for g in gp] + [x1]
        for k_, (a, b) in enumerate(zip(cuts[::2], cuts[1::2])):
            if b - a > 0.05:
                box(f"Base{nm}{k_}", (b - a, 0.15, 0.55), ((a + b) / 2, y, Z0 + 0.275), K["trim"], bevel=0.02)

    def run_y(nm, x, y0, y1, gaps):
        cuts = [y0] + [g for gp in gaps for g in gp] + [y1]
        for k_, (a, b) in enumerate(zip(cuts[::2], cuts[1::2])):
            if b - a > 0.05:
                box(f"Base{nm}{k_}", (0.15, b - a, 0.55), (x, (a + b) / 2, Z0 + 0.275), K["trim"], bevel=0.02)
    run_x("F", Y0 + 0.17, X0 + 0.1, X1 - 0.1, [])
    run_x("B", Y1 - 0.17, X0 + 0.1, X1 - 0.1, [(CLO[0] - 0.45, CLO[1] + 0.45)])
    run_y("L", X0 + 0.17, Y0 + 0.25, Y1 - 0.25, [(DOOR[0] - 0.45, DOOR[1] + 0.45)])
    run_y("R", X1 - 0.17, Y0 + 0.25, Y1 - 0.25, [])
    for nm, size, loc in (("F", (X1 - X0 - 0.2, 0.3, 0.4), ((X0 + X1) / 2, Y0 + 0.25, Z1 - 0.2)), ("B", (X1 - X0 - 0.2, 0.3, 0.4), ((X0 + X1) / 2, Y1 - 0.25, Z1 - 0.2)),
                          ("L", (0.3, Y1 - Y0 - 0.8, 0.4), (X0 + 0.25, (Y0 + Y1) / 2, Z1 - 0.2)), ("R", (0.3, Y1 - Y0 - 0.8, 0.4), (X1 - 0.25, (Y0 + Y1) / 2, Z1 - 0.2))):
        box(f"Crown{nm}", size, loc, K["trim"], bevel=0.05)
    # window casings and stools
    for s_ in (-1, 1):
        box(f"InCas{s_}", (0.4, 0.2, wh + 0.4), (wc + s_ * (ww / 2 + 0.2), Y0 + 0.2, wz + wh / 2), K["trim"], bevel=0.03)
        box(f"RCas{s_}", (0.2, 0.4, sh + 0.4), (X1 - 0.2, sc_ + s_ * (sw / 2 + 0.2), sz_ + sh / 2), K["trim"], bevel=0.03)
    box("InHead", (ww + 1.0, 0.22, 0.45), (wc, Y0 + 0.2, wz + wh + 0.42), K["trim"], bevel=0.03)
    box("InStool", (ww + 0.8, 0.6, 0.14), (wc, Y0 + 0.4, wz - 0.07), K["trim"], bevel=0.03)
    box("RHead", (0.22, sw + 1.0, 0.45), (X1 - 0.2, sc_, sz_ + sh + 0.42), K["trim"], bevel=0.03)
    box("RStool", (0.6, sw + 0.8, 0.14), (X1 - 0.4, sc_, sz_ - 0.07), K["trim"], bevel=0.03)
    # the closet door (back wall) and the bedroom door (left wall; it swings out into the hall)
    dmid, cmid = (DOOR[0] + DOOR[1]) / 2, (CLO[0] + CLO[1]) / 2
    for s_ in (-1, 1):
        box(f"DCas{s_}", (0.2, 0.45, 7.6), (X0 + 0.2, dmid + s_ * 1.72, Z0 + 3.8), K["trim"], bevel=0.03)
        box(f"CCas{s_}", (0.45, 0.2, 7.6), (cmid + s_ * 1.42, Y1 - 0.2, Z0 + 3.8), K["trim"], bevel=0.03)
    box("DHead", (0.22, 3.9, 0.45), (X0 + 0.2, dmid, Z0 + 7.75), K["trim"], bevel=0.03)
    box("CHead", (3.3, 0.22, 0.45), (cmid, Y1 - 0.2, Z0 + 7.75), K["trim"], bevel=0.03)
    box("Closet", (2.4, 0.15, 7.4), (cmid, Y1 - 0.05, Z0 + 3.7), paint_w, bevel=0.03)
    for r in range(2):
        box(f"ClosetPanel{r}", (1.8, 0.06, 2.8 if r else 3.2), (cmid, Y1 - 0.15, Z0 + (5.4 if r else 1.9)), paint_w, bevel=0.025)
    cyl("ClosetKnob", 0.13, 0.2, (CLO[0] + 0.35, Y1 - 0.28, Z0 + 3.5), K["brass"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.05)
    set_group("Door", hinge=(X0, DOOR[0], Z0), swing=-1)
    box("BedDoor", (0.15, 3.0, 7.4), (X0 + 0.05, dmid, Z0 + 3.7), paint_w, bevel=0.03)
    for r in range(2):
        box(f"BedDoorPanel{r}", (0.06, 2.3, 2.8 if r else 3.2), (X0 + 0.15, dmid, Z0 + (5.4 if r else 1.9)), paint_w, bevel=0.025)
    cyl("BedDoorKnob", 0.13, 0.2, (X0 + 0.28, DOOR[1] - 0.4, Z0 + 3.5), K["brass"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.05)
    set_group("Main")
    # the ceiling light
    lathe("CeilBase", [(0, Z1 - 0.001), (0.5, Z1 - 0.001), (0.45, Z1 - 0.12), (0, Z1 - 0.12)], K["brass"], seg=20, loc=((X0 + X1) / 2, (Y0 + Y1) / 2, 0))
    set_group("Glass")
    lathe("CeilBowl", [(0, Z1 - 0.9), (0.5, Z1 - 0.72), (0.7, Z1 - 0.36), (0.72, Z1 - 0.13), (0, Z1 - 0.13)],
          material("WFFrosted", base=(0.95, 0.93, 0.88), rough=0.5, wear=0.0), seg=24, loc=((X0 + X1) / 2, (Y0 + Y1) / 2, 0))
    set_group("Main")
    # curtains on the front window: a rod on brackets in front of the casing head, two gathered panels to the sides
    cyl("CurtainRod", 0.07, ww + 4.6, (wc, Y0 + 0.62, wz + wh + 0.85), K["brass"], rot=(0, math.pi / 2, 0), verts=12)
    for s_ in (-1, 1):
        box(f"RodBracket{s_}", (0.12, 0.42, 0.12), (wc + s_ * (ww / 2 + 1.9), Y0 + 0.4, wz + wh + 0.85), K["brass"], bevel=0.02)
        set_group("Curtains")
        for k in range(5):
            ztop_, zbot_ = wz + wh + 0.78, wz + wh + 0.78 - (wh + 1.3)
            lathe(f"Curtain{s_}{k}", [(0.0, zbot_)] + [(0.17 + 0.012 * math.sin(i * 1.7 + k), zbot_ + (ztop_ - zbot_) * i / 16) for i in range(17)] + [(0.0, ztop_)],
                  cloth_r, seg=10, loc=(wc + s_ * (ww / 2 + 0.75 + k * 0.3), Y0 + 0.62 + 0.06 * (k % 2), 0))
        set_group("Main")
        box(f"Tieback{s_}", (1.6, 0.18, 0.15), (wc + s_ * (ww / 2 + 1.35), Y0 + 0.86, wz + 1.6), K["brass"], bevel=0.04)

    # ---------------------------------------------------------------- the bed, against the back wall, and its decoy
    item("Bed")
    bx0, bx1 = 4.4, 9.4
    by1 = Y1 - G
    by0 = by1 - 7.6
    for x in (bx0 + 0.2, bx1 - 0.2):
        box(f"HeadPost{x}", (0.4, 0.4, 4.2), (x, by1 - 0.2, Z0 + 2.1), oak, bevel=0.05)
        box(f"FootPost{x}", (0.4, 0.4, 2.6), (x, by0 + 0.2, Z0 + 1.3), oak, bevel=0.05)
        lathe(f"HeadKnob{x}", [(0, Z0 + 4.2), (0.2, Z0 + 4.3), (0.19, Z0 + 4.5), (0, Z0 + 4.62)], oak, seg=16, loc=(x, by1 - 0.2, 0))
    box("Headboard", (bx1 - bx0 - 0.4, 0.2, 1.8), ((bx0 + bx1) / 2, by1 - 0.2, Z0 + 3.0), oak, bevel=0.05)
    box("Footboard", (bx1 - bx0 - 0.4, 0.2, 1.1), ((bx0 + bx1) / 2, by0 + 0.2, Z0 + 1.7), oak, bevel=0.05)
    box("Rails", (bx1 - bx0 - 0.4, by1 - by0 - 0.8, 0.5), ((bx0 + bx1) / 2, (by0 + by1) / 2, Z0 + 0.9), oak, bevel=0.04)
    mz = Z0 + 1.15 + 0.45
    box("Mattress", (bx1 - bx0 - 0.6, by1 - by0 - 0.8, 0.9), ((bx0 + bx1) / 2, (by0 + by1) / 2, mz), sheet, bevel=0.18, segments=3)
    top = mz + 0.45
    box("Pillow", (3.0, 1.2, 0.5), ((bx0 + bx1) / 2, by1 - 1.15, top + 0.25), sheet, bevel=0.22, segments=4)
    # the decoy: pillows rolled into a sleeping-kid shape (head, body, bent knees), then the duvet draped over them
    cxb = (bx0 + bx1) / 2
    lumps = (("Head", (cxb + 0.2, by1 - 2.6), (0.5, 0.45, 0.32)), ("Body", (cxb, (by0 + by1) / 2 - 0.4), (0.9, 1.7, 0.36)),
             ("Knee", (cxb + 0.6, by0 + 1.8), (0.6, 0.5, 0.42)))
    for nm, (lx_, ly_), (rx_, ry_, rz_) in lumps:
        sphere(f"Decoy{nm}", 1.0, (lx_, ly_, top + rz_ * 0.92), sheet, seg=20, rings=12, scale=(rx_, ry_, rz_))
    dy0, dy1 = by0 + 0.35, by1 - 2.0

    def duvet_z(x, y):
        z = top + 0.1
        for _, (lx_, ly_), (rx_, ry_, rz_) in lumps:
            q = 1 - ((x - lx_) / (rx_ + 0.35)) ** 2 - ((y - ly_) / (ry_ + 0.35)) ** 2
            if q > 0:
                z = max(z, top + rz_ * 0.92 + rz_ * math.sqrt(q) * 1.05 + 0.08)
        edge = min(x - (bx0 + 0.3), (bx1 - 0.3) - x)
        if edge < 0.3:
            z -= 0.275 * (1 - max(edge, -0.3) / 0.3) ** 1.5
        return z
    set_group("Duvet")
    drape("Duvet", bx0 + 0.12, bx1 - 0.12, dy0, dy1, duvet_z, quilt, nu=32, nv=48, thick=0.12)
    set_group("Main")
    drape("TurnDown", bx0 + 0.15, bx1 - 0.15, dy1 - 0.02, dy1 + 0.7, lambda x, y: top + 0.18 + 0.05 * math.sin(3.0 * (y - dy1)), sheet, nu=24, nv=6, thick=0.08)

    # ---------------------------------------------------------------- a bookshelf on the left wall, between the bed and the door
    item("Bookshelf")
    set_group("Shelf")
    sx0, sx1 = X0 + G, X0 + G + 1.1
    sy0, sy1 = DOOR[1] + 0.75, DOOR[1] + 0.75 + 3.0
    box("ShelfSideA", (sx1 - sx0, 0.15, 6.0), ((sx0 + sx1) / 2, sy0 + 0.075, Z0 + 3.0), oak, bevel=0.03)
    box("ShelfSideB", (sx1 - sx0, 0.15, 6.0), ((sx0 + sx1) / 2, sy1 - 0.075, Z0 + 3.0), oak, bevel=0.03)
    box("ShelfBack", (0.08, sy1 - sy0 - 0.3, 6.0), (sx0 + 0.04, (sy0 + sy1) / 2, Z0 + 3.0), oak, bevel=0)
    rng_ = __import__("random").Random(49)
    book_cols = [(0.5, 0.1, 0.08), (0.12, 0.24, 0.4), (0.2, 0.34, 0.2), (0.62, 0.48, 0.2), (0.3, 0.16, 0.3), (0.82, 0.78, 0.66)]
    book_mats = [material(f"WFSpine{k}", base=c_, rough=0.7, wear=0.25) for k, c_ in enumerate(book_cols)]
    for k in range(5):
        zb = Z0 + 0.1 + k * 1.45
        box(f"Shelf{k}", (sx1 - sx0 - 0.1, sy1 - sy0 - 0.3, 0.12), ((sx0 + sx1) / 2 + 0.04, (sy0 + sy1) / 2, zb + 0.06), oak, bevel=0.02)
        if k == 4:
            break
        y = sy0 + 0.2
        while y < sy1 - 0.55:
            t = rng_.uniform(0.14, 0.3)
            h = rng_.uniform(0.85, 1.2)
            if rng_.random() < 0.12:                          # a gap
                y += 0.3
                continue
            box(f"Spine{k}_{round(y, 2)}", (0.8, t, h), (sx0 + 0.55, y + t / 2, zb + 0.125 + h / 2), book_mats[rng_.randrange(6)], bevel=0.015)
            y += t + 0.012
    lathe("ShelfTrophy", [(0, Z0 + 5.91 + 0.01), (0.22, Z0 + 5.92), (0.08, Z0 + 6.0), (0.06, Z0 + 6.3), (0.22, Z0 + 6.6), (0, Z0 + 6.62)], K["brass"],
          seg=16, loc=((sx0 + sx1) / 2 + 0.05, sy0 + 0.8, 0))
    set_group("Main")

    # ---------------------------------------------------------------- nightstand (right of the bed), the clock, a lamp
    item("Nightstand")
    nx0, nx1 = bx1 + 0.35, bx1 + 1.95
    ny1 = Y1 - G
    ny0 = ny1 - 1.4
    nz = Z0 + 2.2
    box("NightStand", (nx1 - nx0, ny1 - ny0, 2.2), ((nx0 + nx1) / 2, (ny0 + ny1) / 2, Z0 + 1.1), paint_w, bevel=0.05)
    box("NSDrawer", (1.3, 0.06, 0.6), ((nx0 + nx1) / 2, ny0 - 0.02, Z0 + 1.6), paint_w, bevel=0.025)
    cyl("NSKnob", 0.08, 0.12, ((nx0 + nx1) / 2, ny0 - 0.1, Z0 + 1.6), K["brass"], rot=(math.pi / 2, 0, 0), verts=10)
    item("Clock")
    box("ClockBody", (0.9, 0.5, 0.48), (nx0 + 0.55, ny0 + 0.45, nz + 0.25), material("WFClockBody", base=(0.08, 0.08, 0.09), rough=0.4, wear=0.1), bevel=0.06)
    set_group("Clock")
    box("ClockFace", (0.74, 0.02, 0.36), (nx0 + 0.55, ny0 + 0.19, nz + 0.25), K["place"], bevel=0)
    set_group("Main")
    item("BedLamp")
    lx, ly = nx1 - 0.45, ny1 - 0.45
    lathe("LampBase", [(0, nz + 0.01), (0.3, nz + 0.01), (0.28, nz + 0.1), (0.08, nz + 0.2), (0.06, nz + 1.0), (0, nz + 1.0)], K["brass"], seg=16, loc=(lx, ly, 0))
    lathe("LampShade", [(0.42, nz + 0.85), (0.3, nz + 1.5), (0.28, nz + 1.5), (0.4, nz + 0.87)], material("WFShade", base=(0.86, 0.78, 0.6), rough=0.9, wear=0.0),
          seg=24, loc=(lx, ly, 0))

    # ---------------------------------------------------------------- the desk (left wall, front corner) and its things
    item("Desk")
    dx0, dx1 = X0 + G, X0 + G + 2.4
    dy0, dy1 = Y0 + G, Y0 + G + 5.0
    dz = Z0 + 2.6
    box("DeskTop", (dx1 - dx0, dy1 - dy0, 0.2), ((dx0 + dx1) / 2, (dy0 + dy1) / 2, dz - 0.1), oak, bevel=0.04)
    for y in (dy0 + 0.15, dy1 - 0.15):
        box(f"DeskLeg{y}", (dx1 - dx0 - 0.1, 0.18, dz - 0.2 - Z0), ((dx0 + dx1) / 2, y, (Z0 + dz - 0.2) / 2), oak, bevel=0.03)
    box("DeskDrawer", (dx1 - dx0 - 0.3, 1.6, 0.5), ((dx0 + dx1) / 2, dy1 - 1.1, dz - 0.46), oak, bevel=0.03)
    item("Laptop")
    box("Laptop", (1.3, 1.0, 0.08), ((dx0 + dx1) / 2 + 0.2, dy0 + 2.6, dz + 0.045), material("WFLaptop", base=(0.32, 0.33, 0.36), rough=0.35, metal=0.6, wear=0.2), bevel=0.03)
    box("LaptopSticker", (0.35, 0.35, 0.01), ((dx0 + dx1) / 2 + 0.3, dy0 + 2.8, dz + 0.095), material("WFSticker", base=(0.95, 0.65, 0.15), rough=0.4, wear=0.0), bevel=0.0)
    item("Books")
    hs = (0.22, 0.18, 0.26)
    for i, col_ in enumerate(((0.5, 0.1, 0.08), (0.12, 0.24, 0.4), (0.2, 0.34, 0.2))):
        box(f"Book{i}", (0.9, 1.25, hs[i]), ((dx0 + dx1) / 2 - 0.1, dy1 - 0.95, dz + 0.005 + sum(hs[:i]) + hs[i] / 2 + 0.002 * i),
            material(f"WFBook{i}", base=col_, rough=0.7, wear=0.3), bevel=0.02, rot=(0, 0, 0.08 * (i - 1)))
    item("DeskLamp")
    lx2, ly2 = dx0 + 0.55, dy0 + 0.6
    lathe("DeskLampBase", [(0, dz + 0.005), (0.3, dz + 0.005), (0.25, dz + 0.1), (0, dz + 0.12)], K["iron"], seg=16, loc=(lx2, ly2, 0))
    tube("DeskLampArm", [Vector((lx2, ly2, dz + 0.1)), Vector((lx2 + 0.2, ly2 + 0.2, dz + 1.3)), Vector((lx2 + 0.8, ly2 + 0.6, dz + 1.1))], 0.05, K["iron"])
    cone("DeskLampHead", 0.32, 0.12, 0.5, (lx2 + 0.95, ly2 + 0.7, dz + 0.95), K["iron"], rot=(0.4, 0.6, 0))
    item("Chair")
    cx_, cy_ = dx1 + 1.05, (dy0 + dy1) / 2
    box("ChairSeat", (1.4, 1.4, 0.2), (cx_, cy_, Z0 + 1.6), oak, bevel=0.05)
    for ox in (-0.55, 0.55):
        for oy in (-0.55, 0.55):
            box(f"ChairLeg{ox}{oy}", (0.15, 0.15, 1.5), (cx_ + ox, cy_ + oy, Z0 + 0.75), oak, bevel=0.02)
    box("ChairBack", (0.15, 1.4, 1.6), (cx_ + 0.62, cy_, Z0 + 2.5), oak, bevel=0.04)
    # the backpack (green canvas, a W patch), leaning against the front wall by the chair
    item("Backpack")
    bag = wmat("WFBackpack", "NH_Denim", (0.26, 0.42, 0.3), 0.2, wear=0.2, dirt=0.7)
    px_, py_ = 6.65, Y0 + G + 0.45
    box("Pack", (1.2, 0.7, 1.6), (px_, py_, Z0 + 0.82), bag, bevel=0.25, segments=3, rot=(0.12, 0, 0))
    box("PackPocket", (0.9, 0.25, 0.7), (px_, py_ + 0.42, Z0 + 0.55), bag, bevel=0.1, segments=2, rot=(0.12, 0, 0))
    box("PackPatch", (0.42, 0.05, 0.42), (px_, py_ + 0.56, Z0 + 0.6), material("WFPatch", base=(0.88, 0.7, 0.24), rough=0.8, wear=0.0), bevel=0.02, rot=(0.12, 0, 0))
    tube("PackStrap", [Vector((px_ - 0.45, py_ + 0.2, Z0 + 1.4)), Vector((px_ - 0.7, py_ + 0.5, Z0 + 0.8)), Vector((px_ - 0.55, py_ + 0.55, Z0 + 0.12))], 0.07, bag, square=True)

    # ---------------------------------------------------------------- the dresser (right wall, front corner)
    item("Dresser")
    rx1 = X1 - G
    rx0 = rx1 - 1.8
    ry0 = Y0 + G
    ry1 = ry0 + 3.0
    box("Dresser", (rx1 - rx0, ry1 - ry0, 3.2), ((rx0 + rx1) / 2, (ry0 + ry1) / 2, Z0 + 1.6), oak, bevel=0.05)
    for r in range(3):
        box(f"DrDrawer{r}", (0.06, 2.6, 0.85), (rx0 - 0.02, (ry0 + ry1) / 2, Z0 + 0.6 + r * 1.0), oak, bevel=0.025)
        for s_ in (-1, 1):
            cyl(f"DrKnob{r}{s_}", 0.08, 0.12, (rx0 - 0.1, (ry0 + ry1) / 2 + s_ * 0.8, Z0 + 0.6 + r * 1.0), K["brass"], rot=(0, math.pi / 2, 0), verts=10)
    box("DrawerSock", (0.4, 0.12, 0.6), (rx0 - 0.08, (ry0 + ry1) / 2 + 0.4, Z0 + 2.15), material("WFSock", base=(0.8, 0.3, 0.25), rough=0.95, wear=0.0), bevel=0.05)

    # ---------------------------------------------------------------- the clothes pile by the closet: folded and dropped
    item("Clothes")
    tee = wmat("WFTee", "NH_Cotton", (0.8, 0.78, 0.7), 0.15, wear=0.0)
    jean = wmat("WFJean", "NH_Denim", (0.26, 0.36, 0.6), 0.15, wear=0.1)
    hood = fmat("WFHoodie", "NH_Velvet", (0.55, 0.16, 0.13), 0.5, wear=0.0)
    kx, ky = CLO[0] - 0.6, Y1 - 2.4
    # jeans: two legs crossing, a waistband
    box("JeansL", (0.7, 2.6, 0.18), (kx - 0.2, ky - 0.2, Z0 + 0.09), jean, bevel=0.07, segments=2, rot=(0, 0, 0.35))
    box("JeansR", (0.7, 2.4, 0.18), (kx + 0.45, ky - 0.4, Z0 + 0.27), jean, bevel=0.07, segments=2, rot=(0, 0, -0.25))
    box("Waist", (1.5, 0.5, 0.2), (kx + 0.2, ky + 1.0, Z0 + 0.46), jean, bevel=0.08, segments=2, rot=(0, 0, 0.1))
    # a hoodie flung over them, a tee half folded
    box("HoodBody", (1.8, 1.6, 0.2), (kx + 0.9, ky + 0.2, Z0 + 0.66), hood, bevel=0.09, segments=3, rot=(0, 0, 0.5))
    box("HoodSleeve", (0.5, 1.8, 0.16), (kx + 1.9, ky - 0.6, Z0 + 0.86), hood, bevel=0.07, segments=2, rot=(0, 0, -0.6))
    sphere("HoodHood", 0.45, (kx + 0.3, ky + 1.0, Z0 + 0.95), hood, seg=16, rings=8, scale=(1.2, 1.0, 0.45))
    box("Tee", (1.2, 1.0, 0.14), (kx - 1.2, ky + 0.6, Z0 + 0.07), tee, bevel=0.06, segments=2, rot=(0, 0, -0.2))

    # ---------------------------------------------------------------- the braided rug (clear of the bed and the dresser)
    item("Rug")
    set_group("Rug")
    rug_cols = [(0.5, 0.18, 0.12), (0.78, 0.66, 0.42), (0.2, 0.32, 0.24), (0.5, 0.18, 0.12), (0.24, 0.3, 0.46), (0.78, 0.66, 0.42)]
    rug_mats = [material(f"WFRug{k}", base=rug_cols[k], rough=0.95, wear=0.0) for k in range(6)]
    rcx, rcy = 13.2, -6.4
    for i in range(12):
        hoop(f"Rug{i}", (rcx, rcy, Z0 + 0.076), 0.3 + i * 0.28, "Z", rug_mats[i % 6], thick=0.075)
    set_group("Main")

    # ---------------------------------------------------------------- the pennant over the bed, posters on the back wall
    item("Pennant")
    set_group("Pennant")
    pl, ph, px0, pz0 = 4.0, 1.5, (bx0 + bx1) / 2 - 2.0, Z0 + 5.4
    xh = px0 + pl * 150 / 2048
    prism("Pennant", [(px0, pz0), (xh, pz0), (px0 + pl, pz0 + ph / 2), (xh, pz0 + ph), (px0, pz0 + ph)], Y1 - 0.13, 0.04, K["place"], plane="XZ")
    item("Posters")
    set_group("PosterBand")
    box("PosterBand", (2.0, 0.04, 3.0), ((nx0 + nx1) / 2 + 1.4, Y1 - 0.13, Z0 + 4.8), K["place"], bevel=0)
    set_group("PosterMoon")
    box("PosterMoon", (1.4, 0.04, 2.1), (X0 + 1.1, Y1 - 0.13, Z0 + 4.6), K["place"], bevel=0)
    set_group("Main")
    for x, z, hw, hh in (((nx0 + nx1) / 2 + 1.4, Z0 + 4.8, 1.0, 1.5), (X0 + 1.1, Z0 + 4.6, 0.7, 1.05)):
        for cx2 in (-hw + 0.1, hw - 0.1):
            box(f"Tack{x}{cx2}", (0.1, 0.03, 0.1), (x + cx2, Y1 - 0.165, z + hh - 0.1), K["iron"], bevel=0)

    clip_check(((X0 + 0.1, Y0 + 0.1, Z0), (X1 - 0.1, Y1 - 0.1, Z1)))
    return (X1 - X0 + 2, Y1 - Y0 + 2, Z1)

# ================================================================== the kitchen (inside WickHouse, the same origin)

KIT_ROOM = dict(X0=0.0, X1=18.7, Y0=0.5, Y1=13.7, Z0=1.6, Z1=11.4)
KIT_WIN = (3.25, 4.5, 5.2, 4.4)                  # the back window: centre x, width, sill z, height
KIT_DOOR = (8.0, 11.5)                            # the back door (x), full height 8


def kitchen(M):
    """The kitchen, ground floor back right of WickHouse, in the house's own space: 18.7 x 13.2 studs. The breakfast
    scene (docs/expansion/15 beat 9): the table with three places, the black envelope propped against your cereal box,
    Dad's newspaper (held up in the scene), the brochure by Mom's place. Clip-checked like the bedroom."""
    ITEMS.clear()
    K = kit(M)
    R = KIT_ROOM
    X0, X1, Y0, Y1, Z0, Z1 = R["X0"], R["X1"], R["Y0"], R["Y1"], R["Z0"], R["Z1"]
    wc, ww, wz, wh = KIT_WIN
    paint_w = wmat("WFFurnWhite", "NH_PaintedWood", (0.96, 0.94, 0.9), 0.3, wear=0.3, dirt=0.6)
    cab = wmat("WFCabinet", "NH_PaintedWood", (0.5, 0.65, 0.55), 0.3, wear=0.35, dirt=0.7)        # sage-green cabinets
    top_m = material("WFCounter", "NH_DeskWood", tint=(0.62, 0.44, 0.26), scale=0.3, rough_add=0.1, wear=0.4)   # butcher block
    steel = material("WFSteel", base=(0.78, 0.78, 0.8), rough=0.25, metal=1.0, wear=0.2)
    enamel = wmat("WFEnamelCream", "NH_Enamel", (0.98, 0.93, 0.82), 0.5, wear=0.3, dirt=0.6)
    chrome = material("WFChrome", base=(0.8, 0.8, 0.82), rough=0.18, metal=1.0, wear=0.2)
    oak = material("WFOak", "NH_DeskWood", tint=(0.6, 0.42, 0.26), scale=0.25, rough_add=0.05, wear=0.4)
    ging = wmat("WFGingham", "NH_Cotton", (0.8, 0.26, 0.22), 0.15, wear=0.0)
    china = wmat("WFChina", "NH_Enamel", (1.0, 0.99, 0.95), 0.6, wear=0.1, dirt=0.4)
    S = 0.11                                          # cabinets stand this far off the wall paint (no baseboard behind them)
    G = 0.27                                          # loose furniture stands this far from a wall

    # ---------------------------------------------------------------- the room
    item("Room")
    set_group("Floor")
    box("Floor", (X1 - X0, Y1 - Y0, 0.4), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z0 - 0.2), K["place"], bevel=0)
    set_group("Walls")
    wall("WallB", "y", Y1 - 0.05, X0, X1, Z0, Z1, 0.1, [(wc - ww / 2, wc + ww / 2, wz, wz + wh), (KIT_DOOR[0], KIT_DOOR[1], Z0, Z0 + 8.0),
                                                        (X0, 7.45, Z0 + 3.12, Z0 + 5.0)], K["place"])
    wall("WallF", "y", Y0 + 0.05, X0, X1, Z0, Z1, 0.1, [(13.0, 16.5, Z0, Z0 + 7.6)], K["place"])
    wall("WallL", "x", X0 + 0.05, Y0, Y1, Z0, Z1, 0.1, [(2.0, 5.5, Z0, Z0 + 7.6)], K["place"])
    wall("WallR", "x", X1 - 0.05, Y0, Y1, Z0, Z1, 0.1, [(1.2, 9.8, Z0 + 3.12, Z0 + 5.0)], K["place"])
    set_group("Tile")                                  # the subway backsplashes behind the counters
    wall("SplashB", "y", Y1 - 0.05, X0, 7.45, Z0 + 3.12, Z0 + 5.0, 0.1, [(wc - ww / 2, wc + ww / 2, wz, Z0 + 5.0)], K["place"])
    wall("SplashR", "x", X1 - 0.05, 1.2, 9.8, Z0 + 3.12, Z0 + 5.0, 0.1, [], K["place"])
    set_group("Main")
    box("Ceiling", (X1 - X0, Y1 - Y0, 0.2), ((X0 + X1) / 2, (Y0 + Y1) / 2, Z1 + 0.1), paint_w, bevel=0)
    def base_x(nm, y, runs):
        for k_, (a, b) in enumerate(runs):
            box(f"Base{nm}{k_}", (b - a, 0.15, 0.55), ((a + b) / 2, y, Z0 + 0.275), K["trim"], bevel=0.02)

    def base_y(nm, x, runs):
        for k_, (a, b) in enumerate(runs):
            box(f"Base{nm}{k_}", (0.15, b - a, 0.55), (x, (a + b) / 2, Z0 + 0.275), K["trim"], bevel=0.02)
    base_x("B", Y1 - 0.17, [(KIT_DOOR[1] + 0.45, 12.05), (15.75, X1 - 0.1)])
    base_x("F", Y0 + 0.17, [(X0 + 0.1, 12.55), (16.95, X1 - 0.1)])
    base_y("L", X0 + 0.17, [(Y0 + 0.1, 1.55), (5.95, 11.2)])
    base_y("R", X1 - 0.17, [(Y0 + 0.1, 1.05), (9.95, Y1 - 0.1)])
    for nm, size, loc in (("F", (X1 - X0 - 0.2, 0.3, 0.4), ((X0 + X1) / 2, Y0 + 0.25, Z1 - 0.2)), ("B", (X1 - X0 - 0.2, 0.3, 0.4), ((X0 + X1) / 2, Y1 - 0.25, Z1 - 0.2)),
                          ("L", (0.3, Y1 - Y0 - 0.8, 0.4), (X0 + 0.25, (Y0 + Y1) / 2, Z1 - 0.2)), ("R", (0.3, Y1 - Y0 - 0.8, 0.4), (X1 - 0.25, (Y0 + Y1) / 2, Z1 - 0.2))):
        box(f"Crown{nm}", size, loc, K["trim"], bevel=0.05)
    for s_ in (-1, 1):                                # window and door casings
        box(f"WCas{s_}", (0.4, 0.2, wh + 0.4), (wc + s_ * (ww / 2 + 0.2), Y1 - 0.2, wz + wh / 2), K["trim"], bevel=0.03)
        box(f"DCas{s_}", (0.45, 0.2, 8.3), ((KIT_DOOR[0] + KIT_DOOR[1]) / 2 + s_ * ((KIT_DOOR[1] - KIT_DOOR[0]) / 2 + 0.22), Y1 - 0.2, Z0 + 4.15), K["trim"], bevel=0.03)
    box("WHead", (ww + 1.0, 0.22, 0.45), (wc, Y1 - 0.2, wz + wh + 0.42), K["trim"], bevel=0.03)
    box("DHead", (KIT_DOOR[1] - KIT_DOOR[0] + 1.3, 0.22, 0.45), ((KIT_DOOR[0] + KIT_DOOR[1]) / 2, Y1 - 0.2, Z0 + 8.45), K["trim"], bevel=0.03)
    for s_ in (-1, 1):                                # the doorways to the hall and the living room (trim only)
        box(f"HCas{s_}", (0.2, 0.45, 7.9), (X0 + 0.2, 3.75 + s_ * 1.97, Z0 + 3.95), K["trim"], bevel=0.03)
        box(f"LCas{s_}", (0.45, 0.2, 7.9), (14.75 + s_ * 1.97, Y0 + 0.2, Z0 + 3.95), K["trim"], bevel=0.03)
    box("HHead", (0.22, 4.4, 0.45), (X0 + 0.2, 3.75, Z0 + 7.85), K["trim"], bevel=0.03)
    box("LHead", (4.4, 0.22, 0.45), (14.75, Y0 + 0.2, Z0 + 7.85), K["trim"], bevel=0.03)
    # café curtains on the window, and the wall clock over the back door (7:45)
    cyl("CafeRod", 0.05, ww + 0.8, (wc, Y1 - 0.45, wz + 2.2), chrome, rot=(0, math.pi / 2, 0), verts=10)
    for k in range(8):
        cyl(f"Cafe{k}", 0.14, 2.0, (wc - ww / 2 + 0.25 + k * (ww - 0.5) / 7, Y1 - 0.48 + 0.05 * (k % 2), wz + 1.2), ging, verts=8)
    ccx, ccz = (KIT_DOOR[0] + KIT_DOOR[1]) / 2, Z0 + 9.25
    cyl("ClockRim", 0.62, 0.16, (ccx, Y1 - 0.2, ccz), material("WFClockRim", base=(0.6, 0.12, 0.1), rough=0.3, wear=0.2), rot=(math.pi / 2, 0, 0), verts=32, bevel=0.04)
    cyl("ClockDial", 0.54, 0.02, (ccx, Y1 - 0.29, ccz), china, rot=(math.pi / 2, 0, 0), verts=32, bevel=0)
    for k in range(12):
        a = k * math.pi / 6
        box(f"Tick{k}", (0.04, 0.02, 0.1), (ccx + 0.46 * math.sin(a), Y1 - 0.305, ccz + 0.46 * math.cos(a)), K["iron"], bevel=0, rot=(0, -a, 0))
    for nm, ang, ln in (("Hr", math.radians(232), 0.3), ("Min", math.radians(270), 0.44)):
        set_group(f"Hand{nm}")
        box(f"Hand{nm}", (0.05, 0.02, ln), (ccx + ln / 2 * math.sin(ang), Y1 - 0.32 - (0.01 if nm == "Min" else 0), ccz + ln / 2 * math.cos(ang)), K["iron"], bevel=0, rot=(0, -ang, 0))
    set_group("Main")
    # the pendant light over the table
    tx, ty = 8.8, 6.0
    cyl("PendCord", 0.03, 2.4, (tx, ty, Z1 - 1.2), K["iron"], verts=8)
    set_group("Glass")
    lathe("PendShade", [(0.0, Z1 - 3.1), (0.25, Z1 - 3.05), (0.9, Z1 - 2.75), (1.0, Z1 - 2.6), (0.15, Z1 - 2.35), (0.0, Z1 - 2.35)],
          material("WFMilkGlass", base=(0.97, 0.94, 0.85), rough=0.35, wear=0.0), seg=28, loc=(tx, ty, 0))
    set_group("Main")

    # ---------------------------------------------------------------- the counters: the sink run (back), the stove run (right)
    item("Counters")
    set_group("Counters")
    CZ = Z0 + 3.0                                     # countertop surface
    def base_run(nm, x0, x1, y0, y1, doors_axis):
        box(f"{nm}Carcass", (x1 - x0, y1 - y0, 2.6), ((x0 + x1) / 2, (y0 + y1) / 2, Z0 + 0.3 + 1.3), cab, bevel=0.03)
        box(f"{nm}Toe", (x1 - x0 - (0.3 if doors_axis == "x" else 0.02), y1 - y0 - (0.3 if doors_axis == "y" else 0.02), 0.3),
            ((x0 + x1) / 2 + (0.15 if doors_axis == "x" else 0), (y0 + y1) / 2 + (0.15 if doors_axis == "y" else 0), Z0 + 0.15), K["iron"], bevel=0)
        n = max(1, int(round(((x1 - x0) if doors_axis == "y" else (y1 - y0)) / 1.5)))
        span = (x1 - x0) if doors_axis == "y" else (y1 - y0)
        for i in range(n):
            c = (x0 if doors_axis == "y" else y0) + (i + 0.5) * span / n
            if doors_axis == "y":
                box(f"{nm}Door{i}", (span / n - 0.12, 0.08, 1.7), (c, y0 - 0.04, Z0 + 1.35), cab, bevel=0.04)
                box(f"{nm}Drawer{i}", (span / n - 0.12, 0.08, 0.6), (c, y0 - 0.04, Z0 + 2.55), cab, bevel=0.04)
                box(f"{nm}Pull{i}", (0.5, 0.08, 0.06), (c, y0 - 0.12, Z0 + 2.55), chrome, bevel=0.02)
                box(f"{nm}Knob{i}", (0.08, 0.08, 0.3), (c + (span / n) / 2 - 0.3, y0 - 0.12, Z0 + 1.9), chrome, bevel=0.02)
            else:
                box(f"{nm}Door{i}", (0.08, span / n - 0.12, 1.7), (x0 - 0.04, c, Z0 + 1.35), cab, bevel=0.04)
                box(f"{nm}Drawer{i}", (0.08, span / n - 0.12, 0.6), (x0 - 0.04, c, Z0 + 2.55), cab, bevel=0.04)
                box(f"{nm}Pull{i}", (0.08, 0.5, 0.06), (x0 - 0.12, c, Z0 + 2.55), chrome, bevel=0.02)
                box(f"{nm}Knob{i}", (0.08, 0.08, 0.3), (x0 - 0.12, c + (span / n) / 2 - 0.3, Z0 + 1.9), chrome, bevel=0.02)
    # the sink run along the back wall: x from the left wall to 7.6
    bx0, bx1, by0, by1 = X0 + S, 7.35, Y1 - S - 2.0, Y1 - S
    base_run("SinkRun", bx0, bx1, by0, by1, "y")
    top = box("SinkTop", (bx1 - bx0, by1 - by0 + 0.12, 0.2), ((bx0 + bx1) / 2, (by0 + by1) / 2 - 0.06, CZ - 0.1), top_m, bevel=0.03)
    # the sink: a steel basin let into the top, a gooseneck tap
    box("SinkRim", (2.6, 1.5, 0.05), (wc, by0 + 1.0, CZ + 0.025), steel, bevel=0.02)
    box("SinkBowl", (2.3, 1.2, 0.04), (wc, by0 + 1.0, CZ + 0.055), material("WFSinkDark", base=(0.3, 0.3, 0.32), rough=0.3, metal=1.0, wear=0.1), bevel=0)
    lathe("TapBase", [(0, CZ + 0.05), (0.14, CZ + 0.05), (0.1, CZ + 0.2), (0, CZ + 0.2)], chrome, seg=16, loc=(wc, by1 - 0.35, 0))
    tube("TapNeck", [Vector((wc, by1 - 0.35, CZ + 0.2)), Vector((wc, by1 - 0.35, CZ + 1.1)), Vector((wc, by1 - 0.6, CZ + 1.35)), Vector((wc, by1 - 0.95, CZ + 1.05))], 0.06, chrome)
    for s_ in (-1, 1):
        lathe(f"TapHandle{s_}", [(0, CZ + 0.05), (0.08, CZ + 0.05), (0.06, CZ + 0.25), (0.12, CZ + 0.32), (0, CZ + 0.34)], chrome, seg=12, loc=(wc + s_ * 0.5, by1 - 0.35, 0))
    # the stove run along the right wall: y 1.2 to 9.8, the range in the middle
    rx0, rx1 = X1 - S - 2.0, X1 - S
    base_run("RunA", rx0, rx1, 1.2, 4.5, "x")
    base_run("RunB", rx0, rx1, 7.1, 9.8, "x")
    for nm, (a, b) in (("A", (1.2, 4.5)), ("B", (7.1, 9.8))):
        box(f"RTop{nm}", (rx1 - rx0 + 0.12, b - a, 0.2), ((rx0 + rx1) / 2 - 0.06, (a + b) / 2, CZ - 0.1), top_m, bevel=0.03)
    # upper cabinets: beside the window on the back wall, over both right runs
    UZ0, UZ1 = Z0 + 5.0, Z0 + 8.2
    def upper(nm, x0, x1, y0, y1, face):
        box(f"{nm}Box", (x1 - x0, y1 - y0, UZ1 - UZ0), ((x0 + x1) / 2, (y0 + y1) / 2, (UZ0 + UZ1) / 2), cab, bevel=0.03)
        n = max(1, int(round(((x1 - x0) if face == "y" else (y1 - y0)) / 1.5)))
        span = (x1 - x0) if face == "y" else (y1 - y0)
        for i in range(n):
            c = (x0 if face == "y" else y0) + (i + 0.5) * span / n
            if face == "y":
                box(f"{nm}Door{i}", (span / n - 0.12, 0.08, UZ1 - UZ0 - 0.2), (c, y0 - 0.04, (UZ0 + UZ1) / 2), cab, bevel=0.04)
                box(f"{nm}Knob{i}", (0.08, 0.08, 0.3), (c + (span / n) / 2 - 0.3, y0 - 0.12, UZ0 + 0.5), chrome, bevel=0.02)
            else:
                box(f"{nm}Door{i}", (0.08, span / n - 0.12, UZ1 - UZ0 - 0.2), (x0 - 0.04, c, (UZ0 + UZ1) / 2), cab, bevel=0.04)
                box(f"{nm}Knob{i}", (0.08, 0.08, 0.3), (x0 - 0.12, c + (span / n) / 2 - 0.3, UZ0 + 0.5), chrome, bevel=0.02)
    upper("UpB", wc + ww / 2 + 0.75, 7.35, Y1 - S - 1.2, Y1 - S, "y")
    upper("UpRA", X1 - S - 1.2, X1 - S, 1.2, 4.5, "x")
    upper("UpRB", X1 - S - 1.2, X1 - S, 7.1, 9.8, "x")

    # ---------------------------------------------------------------- the range (cream enamel, chrome) and the hood
    set_group("Main")
    item("Range")
    sy0, sy1 = 4.62, 6.98
    box("RangeBody", (2.0, sy1 - sy0, 2.95), (rx0 + 1.0, (sy0 + sy1) / 2, Z0 + 1.475), enamel, bevel=0.05)
    box("RangeOven", (0.06, sy1 - sy0 - 0.5, 1.6), (rx0 - 0.03, (sy0 + sy1) / 2, Z0 + 1.2), enamel, bevel=0.04)
    set_group("Glass")
    box("OvenWindow", (0.04, 1.2, 0.7), (rx0 - 0.07, (sy0 + sy1) / 2, Z0 + 1.3), material("WFOvenGlass", base=(0.05, 0.05, 0.06), rough=0.1, wear=0.0), bevel=0)
    set_group("Main")
    box("OvenHandle", (0.1, 1.5, 0.08), (rx0 - 0.14, (sy0 + sy1) / 2, Z0 + 2.05), chrome, bevel=0.03)
    box("Backguard", (0.3, sy1 - sy0, 0.8), (rx1 - 0.15, (sy0 + sy1) / 2, Z0 + 3.35), enamel, bevel=0.04)
    for k in range(4):
        cyl(f"Dial{k}", 0.1, 0.1, (rx1 - 0.32, sy0 + 0.4 + k * 0.52, Z0 + 3.4), chrome, rot=(0, math.pi / 2, 0), verts=12, bevel=0.02)
    for ox in (-0.5, 0.5):
        for oy in (-0.55, 0.55):
            cyl(f"Burner{ox}{oy}", 0.35, 0.05, (rx0 + 1.0 + ox * 0.6 - 0.15, (sy0 + sy1) / 2 + oy, Z0 + 2.975), K["iron"], verts=20, bevel=0)
    item("Kettle")
    set_group("KettleLid")
    lathe("KettleLid", [(0, Z0 + 3.76), (0.17, Z0 + 3.76), (0.15, Z0 + 3.82), (0.04, Z0 + 3.86), (0.06, Z0 + 3.95), (0, Z0 + 3.97)], K["iron"], seg=20,
          loc=(rx0 + 0.6, (sy0 + sy1) / 2 - 0.55, 0))
    set_group("Main")
    lathe("Kettle", [(0, Z0 + 3.001), (0.45, Z0 + 3.001), (0.5, Z0 + 3.2), (0.42, Z0 + 3.6), (0.17, Z0 + 3.75), (0, Z0 + 3.75)],
          material("WFKettle", base=(0.62, 0.1, 0.08), rough=0.25, wear=0.3), seg=24, loc=(rx0 + 0.6, (sy0 + sy1) / 2 - 0.55, 0))
    tube("KettleSpout", [Vector((rx0 + 0.2, (sy0 + sy1) / 2 - 0.55, Z0 + 3.3)), Vector((rx0 - 0.05, (sy0 + sy1) / 2 - 0.55, Z0 + 3.65))], 0.06, K["iron"])
    tube("KettleHandle", [Vector((rx0 + 0.85, (sy0 + sy1) / 2 - 0.55, Z0 + 3.6)), Vector((rx0 + 0.6, (sy0 + sy1) / 2 - 0.55, Z0 + 4.05)), Vector((rx0 + 0.35, (sy0 + sy1) / 2 - 0.55, Z0 + 3.6))], 0.04, K["iron"])
    item("Hood")
    hz = Z0 + 6.2
    solid("Hood", [(rx0 - 0.1, sy0 - 0.1, hz), (X1 - S, sy0 - 0.1, hz), (X1 - S, sy1 + 0.1, hz), (rx0 - 0.1, sy1 + 0.1, hz)],
          [(X1 - S - 1.0, sy0 + 0.3, hz + 1.2), (X1 - S, sy0 + 0.3, hz + 1.2), (X1 - S, sy1 - 0.3, hz + 1.2), (X1 - S - 1.0, sy1 - 0.3, hz + 1.2)], steel)
    box("HoodFlue", (1.0, sy1 - sy0 - 0.6, Z1 - 0.45 - hz - 1.2), (X1 - S - 0.5, (sy0 + sy1) / 2, (hz + 1.2 + Z1 - 0.45) / 2), steel, bevel=0.02)

    # ---------------------------------------------------------------- the fridge (back wall, right of the door) and its door art
    item("Fridge")
    fx0, fx1 = 12.2, 15.6
    fy1 = Y1 - S
    fy0 = fy1 - 2.8
    box("FridgeBody", (fx1 - fx0, fy1 - fy0 - 0.32, 6.8), ((fx0 + fx1) / 2, (fy0 + fy1) / 2 + 0.16, Z0 + 3.4), enamel, bevel=0.3, segments=4)
    # the inside, seen when the door swings open: a white liner, wire shelves, a few things in a shallow relief
    liner = wmat("WFLiner", "NH_Enamel", (0.98, 0.98, 0.96), 0.5, wear=0.05, dirt=0.3)
    fz = fy0 + 0.315
    box("FridgeLiner", (fx1 - fx0 - 0.4, 0.004, 6.2), ((fx0 + fx1) / 2, fz + 0.002, Z0 + 3.4), liner, bevel=0)
    for k, z in enumerate((Z0 + 1.6, Z0 + 3.0, Z0 + 4.6, Z0 + 5.6)):
        box(f"FridgeShelf{k}", (fx1 - fx0 - 0.5, 0.004, 0.06), ((fx0 + fx1) / 2, fz - 0.001, z), chrome, bevel=0)
    for k, (x, z, w, h, col_) in enumerate(((12.7, Z0 + 3.05, 0.35, 0.9, (0.95, 0.95, 0.93)), (13.3, Z0 + 3.05, 0.55, 0.45, (0.85, 0.75, 0.55)),
                                             (14.2, Z0 + 3.05, 0.4, 0.7, (0.75, 0.15, 0.12)), (13.0, Z0 + 4.65, 0.9, 0.3, (0.92, 0.88, 0.7)),
                                             (14.5, Z0 + 4.65, 0.3, 0.55, (0.3, 0.55, 0.2)), (13.6, Z0 + 1.65, 1.6, 0.5, (0.9, 0.55, 0.2)))):
        box(f"FridgeItem{k}", (w, 0.008, h), (x, fz - 0.006, z + h / 2), material(f"WFFridgeItem{k}", base=col_, rough=0.4, wear=0.0), bevel=0)
    set_group("Glow")
    box("FridgeLight", (0.5, 0.004, 0.2), ((fx0 + fx1) / 2, fz - 0.001, Z0 + 6.3), material("WFFridgeBulb", base=(1.0, 0.96, 0.85), rough=0.3, wear=0.0), bevel=0)
    set_group("FridgeDoor")
    box("FridgeDoorLow", (fx1 - fx0, 0.3, 4.75), ((fx0 + fx1) / 2, fy0 + 0.15, Z0 + 2.4), enamel, bevel=0.12, segments=3)
    box("FridgeDoorHigh", (fx1 - fx0, 0.3, 2.0), ((fx0 + fx1) / 2, fy0 + 0.15, Z0 + 5.8), enamel, bevel=0.12, segments=3)
    box("FridgeSeam", (fx1 - fx0 - 0.1, 0.04, 0.05), ((fx0 + fx1) / 2, fy0 - 0.005, Z0 + 4.79), K["iron"], bevel=0)
    for z, h_ in ((Z0 + 5.9, 1.2), (Z0 + 3.2, 1.8)):
        box(f"FridgeHandle{z}", (0.12, 0.18, h_), (fx1 - 0.35, fy0 - 0.12, z), chrome, bevel=0.04)
    box("FridgeBadge", (0.9, 0.03, 0.2), ((fx0 + fx1) / 2, fy0 - 0.01, Z0 + 6.4), chrome, bevel=0.01)
    for k, (mx_, mz_, col_) in enumerate(((12.8, 5.8, (0.9, 0.2, 0.2)), (15.0, 5.2, (0.2, 0.5, 0.9)), (13.1, 3.1, (0.95, 0.75, 0.1)))):
        cyl(f"Magnet{k}", 0.13, 0.08, (mx_, fy0 - 0.04, Z0 + mz_), material(f"WFMagnet{k}", base=col_, rough=0.4, wear=0.0), rot=(math.pi / 2, 0, 0), verts=12, bevel=0.02)
    set_group("FridgeArt")
    box("FridgeArt", (1.6, 0.01, 1.2), ((fx0 + fx1) / 2 - 0.15, fy0 - 0.01, Z0 + 2.6), K["place"], bevel=0)
    set_group("Main")
    set_group("Main")
    # the calendar on the back wall, beyond the fridge
    item("Calendar")
    set_group("Calendar")
    box("Calendar", (1.3, 0.02, 1.95), (17.1, Y1 - 0.12, Z0 + 6.3), K["place"], bevel=0)
    set_group("Main")
    box("CalNail", (0.06, 0.08, 0.06), (17.1, Y1 - 0.15, Z0 + 7.32), K["iron"], bevel=0)

    # ---------------------------------------------------------------- the table and three chairs (Mom, Dad; you across)
    item("Table")
    tx0, tx1, ty0, ty1, tz = 6.3, 11.3, 4.4, 7.6, Z0 + 2.5
    box("TableTop", (tx1 - tx0, ty1 - ty0, 0.18), ((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz - 0.09), oak, bevel=0.05)
    box("TableApron", (tx1 - tx0 - 0.6, ty1 - ty0 - 0.6, 0.4), ((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz - 0.38), oak, bevel=0.03)
    for x in (tx0 + 0.45, tx1 - 0.45):
        for y in (ty0 + 0.45, ty1 - 0.45):
            lathe(f"TableLeg{x}{y}", [(0.14, Z0), (0.16, Z0 + 0.3), (0.12, Z0 + 0.6), (0.18, Z0 + 1.1), (0.12, Z0 + 1.7), (0.16, tz - 0.58), (0.0, tz - 0.58)],
                  oak, seg=12, loc=(x, y, 0))
    def chair(nm, x, y, facing):
        item(nm)
        box(f"{nm}Seat", (1.4, 1.4, 0.2), (x, y, Z0 + 1.6), oak, bevel=0.05)
        for ox in (-0.55, 0.55):
            for oy in (-0.55, 0.55):
                box(f"{nm}Leg{ox}{oy}", (0.14, 0.14, 1.5), (x + ox, y + oy, Z0 + 0.75), oak, bevel=0.02)
        by_ = y + 0.62 * facing
        box(f"{nm}BackTop", (1.4, 0.15, 0.3), (x, by_, Z0 + 3.35), oak, bevel=0.04)
        for k in range(4):
            box(f"{nm}Spindle{k}", (0.1, 0.1, 1.5), (x - 0.5 + k * 0.33, by_, Z0 + 2.45), oak, bevel=0.02)
    chair("ChairMom", 7.6, ty1 + 1.0, 1)
    chair("ChairDad", 10.0, ty1 + 1.0, 1)
    chair("ChairYou", 8.8, ty0 - 1.0, -1)

    # ---------------------------------------------------------------- breakfast on the table
    item("Places")
    for nm, (x, y) in (("You", (7.9, 5.1)), ("Mom", (7.6, 6.8)), ("Dad", (10.2, 6.85))):
        lathe(f"Bowl{nm}", [(0.0, tz + 0.005), (0.28, tz + 0.005), (0.42, tz + 0.18), (0.5, tz + 0.36), (0.45, tz + 0.36), (0.38, tz + 0.2), (0.0, tz + 0.06)], china, seg=24, loc=(x, y, 0))
        box(f"Spoon{nm}", (0.08, 0.7, 0.03), (x - 0.65, y, tz + 0.02), chrome, bevel=0.01)
    item("Cereal")
    cbx, cby = 10.2, 5.9
    box("CerealBox", (1.0, 0.36, 1.5), (cbx, cby, tz + 0.755), material("WFCerealSide", base=(0.16, 0.13, 0.42), rough=0.5, wear=0.2), bevel=0.02)
    set_group("Cereal")
    box("CerealFront", (0.98, 0.01, 1.47), (cbx, cby - 0.185, tz + 0.755), K["place"], bevel=0)
    set_group("Main")
    item("Envelope")                                     # propped up against the cereal box, facing your place
    set_group("Envelope")
    ex, ey = cbx, cby - 0.18 - 0.22
    box("EnvelopeFace", (1.5, 0.02, 1.0), (ex, ey, tz + 0.52), K["place"], bevel=0, rot=(-0.18, 0, 0))
    set_group("Main")
    envb = material("WFEnvBlack", base=(0.03, 0.025, 0.03), rough=0.6, wear=0.1)
    set_group("EnvBack")
    box("EnvelopeBack", (1.5, 0.03, 1.0), (ex, ey + 0.03, tz + 0.525), envb, bevel=0, rot=(-0.18, 0, 0))
    set_group("EnvFlap")
    ca_, sa_ = math.cos(-0.18), math.sin(-0.18)
    ty_, tz_ = ey + 0.05 + 0.5 * -sa_, tz + 0.525 + 0.5 * ca_
    prism("EnvelopeFlap", [(ex - 0.75, 0.0), (ex + 0.75, 0.0), (ex, -0.6)], 0.0, 0.02, envb, plane="XZ")
    from mathutils import Matrix as _M
    P.PARTS[-1].matrix_world = _M.Translation((0, ty_, tz_)) @ _M.Rotation(-0.18, 4, "X")
    set_group("Main")
    item("Milk")
    lathe("MilkJug", [(0, tz + 0.005), (0.32, tz + 0.005), (0.34, tz + 0.7), (0.24, tz + 0.95), (0.12, tz + 1.1), (0.12, tz + 1.2), (0, tz + 1.2)],
          material("WFMilk", base=(0.95, 0.95, 0.93), rough=0.3, wear=0.0), seg=20, loc=(10.9, 4.9, 0))
    lathe("MilkCap", [(0, tz + 1.2), (0.14, tz + 1.2), (0.14, tz + 1.32), (0, tz + 1.32)], material("WFMilkCap", base=(0.2, 0.4, 0.85), rough=0.4, wear=0.0),
          seg=16, loc=(10.9, 4.9, 0))
    item("DadMug")
    mx_, my_ = 11.0, 7.25
    lathe("Mug", [(0, tz + 0.005), (0.25, tz + 0.005), (0.27, tz + 0.62), (0.23, tz + 0.62), (0.21, tz + 0.1), (0, tz + 0.1)], china, seg=24, loc=(mx_, my_, 0))
    tube("MugHandle", [Vector((mx_ + 0.26, my_, tz + 0.5)), Vector((mx_ + 0.45, my_, tz + 0.42)), Vector((mx_ + 0.45, my_, tz + 0.22)), Vector((mx_ + 0.26, my_, tz + 0.15))], 0.045, china)
    set_group("DadMug")
    box("MugPrint", (0.36, 0.01, 0.24), (mx_, my_ - 0.272, tz + 0.33), K["place"], bevel=0)
    set_group("Main")
    item("Brochure")                                      # standing open by Mom's place, its cover toward you
    set_group("Brochure")
    box("BrochureCover", (0.62, 0.02, 0.93), (6.85, 5.6, tz + 0.47), K["place"], bevel=0, rot=(0, 0, 0))
    set_group("Main")
    for s_ in (-1, 1):
        box(f"BrochurePanel{s_}", (0.62, 0.02, 0.93), (6.85 + s_ * 0.58, 5.6 + 0.2, tz + 0.47), china, bevel=0, rot=(0, 0, -s_ * 0.6))
    item("Fruit")
    lathe("FruitBowl", [(0, tz + 0.005), (0.25, tz + 0.005), (0.6, tz + 0.3), (0.53, tz + 0.3), (0.2, tz + 0.06), (0, tz + 0.06)],
          material("WFFruitBowl", base=(0.85, 0.5, 0.2), rough=0.35, wear=0.2), seg=24, loc=(8.8, 6.0, 0))
    for k, (ox, oy, col_) in enumerate(((-0.2, 0.0, (0.75, 0.1, 0.08)), (0.21, 0.04, (0.85, 0.7, 0.1)), (0.0, -0.22, (0.5, 0.7, 0.15)))):
        sphere(f"Fruit{k}", 0.19, (8.8 + ox, 6.0 + oy, tz + 0.27), material(f"WFFruit{k}", base=col_, rough=0.35, wear=0.0), seg=16, rings=10)
    item("Toaster")
    box("Toaster", (1.1, 0.7, 0.8), (0.8, by0 + 0.9, CZ + 0.405), chrome, bevel=0.15, segments=3)
    for k in (-0.2, 0.2):
        box(f"Slot{k}", (0.7, 0.12, 0.02), (0.8, by0 + 0.9 + k, CZ + 0.81), K["iron"], bevel=0)
    item("DishRack")
    for k in range(5):
        box(f"Plate{k}", (0.06, 0.8, 0.8), (6.1 + k * 0.18, by0 + 1.0, CZ + 0.42), china, bevel=0.02)
    box("RackBase", (1.3, 1.0, 0.06), (6.45, by0 + 1.0, CZ + 0.035), chrome, bevel=0.01)

    # ---------------------------------------------------------------- Dad's newspaper: its own piece, held up in the scene
    item("Newspaper")
    set_group("Newspaper")
    panel("NewsFront", 9.0, 11.0, Z0 + 3.025, Z0 + 5.775, ty1 + 0.25, K["place"], nu=6, nv=14, thick=0.02)
    set_group("Main")
    set_group("NewsBack")
    panel("NewsBack", 9.0, 11.0, Z0 + 3.025, Z0 + 5.775, ty1 + 0.272, material("WFNewsprint", base=(0.86, 0.83, 0.75), rough=0.9, wear=0.0), nu=6, nv=14, thick=0.02)
    set_group("Main")

    clip_check(((X0 + 0.04, Y0 + 0.04, Z0), (X1 - 0.04, Y1 - 0.04, Z1)))
    return (X1 - X0 + 2, Y1 - Y0 + 2, Z1)

BUILDERS.update({
    "WFBedroom": bedroom, "WFKitchen": kitchen,
    "WFStreetLamp": street_lamp, "WFMailbox": mailbox, "WFPicketFence": picket_fence, "WFPicketGate": picket_gate,
    "WFKennel": kennel, "WFHydrant": hydrant, "WFSidewalk": sidewalk,
})
TILES.update({"Walk": ("WF_Sidewalk", 8.0), "Asphalt": ("WF_Road", 12.0), "Floor": ("WF_FloorOak", 6.0), "Paper": ("WF_Wallpaper", 4.0)})
TILES_BY = {"WFKitchen": {"Floor": ("WF_Checker", 4.0), "Walls": ("WF_KitchenPaint", 6.0), "Tile": ("WF_Subway", 2.4)}}   # per-prop overrides
P.CANVAS.update({"WFMailbox_Sign": "WF_Mailbox14", "WFKennel_Sign": "WF_Biscuit", "WFBedroom_Clock": "WF_Clock1158",
                 "WFBedroom_Pennant": "WF_Pennant", "WFBedroom_PosterBand": "WF_PosterBand", "WFBedroom_PosterMoon": "WF_PosterMoon"})
P.CANVAS.update({f"WFKitchen_{g}": f"WF_{c}" for g, c in (("FridgeArt", "FridgeArt"), ("Calendar", "Calendar"), ("Cereal", "Cereal"), ("Envelope", "Envelope"),
                                                        ("DadMug", "DadMug"), ("Brochure", "Brochure"), ("Newspaper", "Gazette"))})

for _n in BUILDERS:
    for _g, (_set, _t) in TILES.items():
        P.TILED[f"{_n}_{_g}"] = (_set, _t)
    for _g, (_set, _t) in TILES_BY.get(_n, {}).items():
        P.TILED[f"{_n}_{_g}"] = (_set, _t)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"WickHouse": 1.25})
P.PREVIEW_PAD.update({"WFBedroom": 1.1})



# ------------------------------------------------------------------ the rigs and clips (house space; studs, seconds)
def _sin(t, period, phase=0.0):
    return math.sin(2 * math.pi * t / period - phase)


_bz = 14.25                                   # the duvet's rest height (bedroom: mattress top + a little)
RIG["WFBedroom"] = dict(
    bones={"Duvet0": ((6.9, -5.52, _bz), (6.9, -2.7, _bz), None), "Duvet1": ((6.9, -2.7, _bz), (6.9, -1.45, _bz), "Duvet0"),
           "Duvet2": ((6.9, -1.45, _bz), (6.9, -0.27, _bz), "Duvet1"),
           "CurtL0": ((8.15, -13.08, 19.38), (8.15, -13.08, 17.2), None), "CurtL1": ((8.15, -13.08, 17.2), (8.15, -13.08, 15.03), "CurtL0"),
           "CurtL2": ((8.15, -13.08, 15.03), (8.15, -13.08, 12.88), "CurtL1"),
           "CurtR0": ((15.35, -13.08, 19.38), (15.35, -13.08, 17.2), None), "CurtR1": ((15.35, -13.08, 17.2), (15.35, -13.08, 15.03), "CurtR0"),
           "CurtR2": ((15.35, -13.08, 15.03), (15.35, -13.08, 12.88), "CurtR1"),
           "Door": ((2.0, -7.8, 12.0), (2.0, -7.8, 13.0), None)},
    own={"Duvet": ["Duvet0", "Duvet1", "Duvet2"], "Curtains": ["CurtL0", "CurtL1", "CurtL2", "CurtR0", "CurtR1", "CurtR2"], "Door": "Door"})
CLIPS["WFBedroom"] = {
    # Mom yanks the covers back from the head end: the top two thirds fold over toward the foot, overshoot, settle
    "DuvetReveal": dict(length=1.4, keys={
        "Duvet0": lambda t: ("x", 4 * math.sin(math.pi * min(1, t / 0.7)), (0, 0, 0)),
        "Duvet1": lambda t: ("x", 150 * back_out(t / 0.9, 1.2), (0, 0, 0.45 * math.sin(math.pi * min(1, t / 0.9)))),
        "Duvet2": lambda t: ("x", 26 * back_out((t - 0.15) / 0.9, 1.0) - 6 * math.sin(min(1, t / 1.4) * math.pi * 2) * (1 - t / 1.4), (0, 0, 0))}),
    # the night breeze through the open window: the curtains billow into the room, loopable
    "CurtainBillow": dict(length=4.0, loop=True, keys={
        **{f"Curt{s}{k}": (lambda t, k=k, ph=(0.0 if s == "L" else 0.9): ("x", [4, 8, 11][k] + [5, 7, 9][k] * _sin(t, 4.0, ph + 0.7 * k), (0, 0, 0)))
           for s in "LR" for k in range(3)}}),
    "DoorOpen": dict(length=1.2, keys={"Door": lambda t: ("z", 95 * back_out(t / 1.0, 0.8), (0, 0, 0))}),
}

RIG["WFKitchen"] = dict(
    bones={"NewsRoot": ((10.0, 7.85, 4.63), (10.0, 7.85, 6.0), None), "NewsTop": ((10.0, 7.85, 6.0), (10.0, 7.85, 7.4), "NewsRoot"),
           "Env": ((10.2, 5.30, 4.12), (10.2, 5.30, 5.1), None), "Flap": ((9.45, 5.44, 5.117), (10.95, 5.44, 5.117), "Env"),
           "FridgeDoor": ((12.2, 10.79, 1.6), (12.2, 10.79, 2.6), None),
           "HandHr": ((9.75, 13.38, 10.85), (9.75, 13.0, 10.85), None), "HandMin": ((9.75, 13.37, 10.85), (9.75, 13.0, 10.85), None),
           "Lid": ((17.19, 5.25, 5.36), (17.19, 5.25, 5.6), None)},
    own={"Newspaper": ["NewsRoot", "NewsTop"], "NewsBack": ["NewsRoot", "NewsTop"], "Envelope": "Env", "EnvBack": "Env", "EnvFlap": "Flap",
         "FridgeDoor": "FridgeDoor", "FridgeArt": "FridgeDoor", "HandHr": "HandHr", "HandMin": "HandMin", "KettleLid": "Lid"})
CLIPS["WFKitchen"] = {
    # Dad lowers the paper, slowly, to look at you over it; the top flops forward
    "NewspaperLower": dict(length=1.6, keys={
        "NewsRoot": lambda t: ("x", 12 * ease(t / 1.3), (0, 0, -1.5 * ease(t / 1.3))),
        "NewsTop": lambda t: ("x", 38 * back_out((t - 0.3) / 1.0, 1.2) - 5 * math.sin(min(1, t / 1.6) * math.pi * 3) * (1 - t / 1.6), (0, 0, 0))}),
    "NewspaperShake": dict(length=0.6, loop=True, keys={
        "NewsRoot": lambda t: ([("x", 1.5 * _sin(t, 0.3)), ("z", 1.0 * _sin(t, 0.6, 1.0))], (0, 0, 0.02 * _sin(t, 0.3))),
        "NewsTop": lambda t: ("x", 3 * _sin(t, 0.3, 0.8), (0, 0, 0))}),
    # Mom slides the envelope across the table to your place
    "EnvelopeSlide": dict(length=1.2, keys={"Env": lambda t: ("z", 8 * (1 - ease(t / 1.0)) * math.sin(t * 6), (0, 2.2 * (1 - back_out(t / 1.0, 0.6)), 0))}),
    "EnvelopeOpen": dict(length=0.8, keys={"Flap": lambda t: ("x", 165 * back_out(t / 0.7, 0.9), (0, 0, 0))}),
    "FridgeOpen": dict(length=1.0, keys={"FridgeDoor": lambda t: ("z", -100 * back_out(t / 0.8, 0.7), (0, 0, 0))}),
    "ClockMinuteTick": dict(length=0.3, keys={"HandMin": lambda t: ("y", 6 * back_out(t / 0.12, 2.0), (0, 0, 0))}),
    # the kettle on the boil: the lid rattles, loopable
    "KettleBoil": dict(length=1.0, loop=True, keys={
        "Lid": lambda t: ([("x", 5 * _sin(t, 1 / 9.0)), ("y", 4 * _sin(t, 1 / 7.0, 0.5))], (0, 0, 0.05 * abs(_sin(t, 1 / 4.5))))}),
}

RIG["WFMailbox"] = dict(bones={"Flag": ((0.75, 0.6, 4.2), (0.75, 0.6, 5.2), None)}, own={"Flag": "Flag"})
CLIPS["WFMailbox"] = {"FlagDown": dict(length=0.8, keys={"Flag": lambda t: ("y", 90 * back_out(t / 0.6, 1.6), (0, 0, 0))}),
                      "FlagUp": dict(length=0.8, keys={"Flag": lambda t: ("y", 90 * (1 - back_out(t / 0.6, 1.6)), (0, 0, 0))})}

RIG["WFPicketGate"] = dict(bones={"Gate": ((-1.95, 0.0, 0.0), (-1.95, 0.0, 1.0), None)}, own={"Gate": "Gate"})
CLIPS["WFPicketGate"] = {"GateOpen": dict(length=1.4, keys={"Gate": lambda t: ("z", -100 * back_out(t / 1.0, 1.0), (0, 0, 0))}),
                         "GateSwingShut": dict(length=1.2, keys={"Gate": lambda t: ("z", -100 * (1 - back_out(t / 0.8, 2.0)), (0, 0, 0))})}

RIG["WickHouse"] = dict(bones={"Sash": ((11.75, -14.12, 13.4), (11.75, -14.12, 14.4), None)}, own={"BedSash": "Sash"})
CLIPS["WickHouse"] = {"SashOpen": dict(length=1.0, keys={"Sash": lambda t: ("x", 0, (0, 0, 2.45 * ease(t / 0.9)))})}

CLIP_CAM = {   # per clip review cameras (cam, target)
    "WFBedroom": {"CurtainBillow": ((14.5, 0.8, 18.0), (11.75, -13.0, 15.5)), "DuvetReveal": ((12.0, -8.0, 18.0), (6.9, -2.2, 14.0)),
                  "DoorOpen": ((12.0, -1.0, 17.0), (2.0, -6.3, 14.5))},
    "WFKitchen": {"NewspaperLower": ((8.8, 2.4, 7.0), (10.0, 7.8, 5.2)), "NewspaperShake": ((8.8, 2.4, 7.0), (10.0, 7.8, 5.2)),
                  "EnvelopeSlide": ((8.0, 2.5, 6.6), (10.2, 6.0, 4.3)), "EnvelopeOpen": ((12.6, 6.6, 6.0), (10.2, 5.45, 4.9)),
                  "FridgeOpen": ((15.8, 4.6, 7.4), (13.9, 10.8, 4.6)), "ClockMinuteTick": ((9.75, 12.2, 10.85), (9.75, 13.7, 10.85)),
                  "KettleBoil": ((14.0, 5.25, 7.0), (17.2, 5.25, 5.3))},
}

for _p in RIG:
    P.RIGS[_p] = (lambda p: (lambda objs: rig_pieces(p, objs)))(_p)

INSIDE = {"WFBedroom": ((17.6, -12.8, 18.8), (6.0, 0.5, 13.0), (10.35, -5.85, 20.0)),
          "WFKitchen": ((1.2, 1.2, 8.6), (11.0, 10.0, 3.5), (8.8, 6.0, 9.0), ((3.25, 17.5, 8.0), 2500, (1.0, 0.92, 0.75)))}   # camera, target, lamp


def inside_render(name, cam, target, lamp, fill=((11.75, -16.5, 16.0), 1500, (0.55, 0.62, 1.0))):
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
    for k, (loc, e, col) in enumerate(((lamp, 900, (1.0, 0.85, 0.65)), fill)):
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
        if n in CLIPS:
            clip_strips(n, *((INSIDE[n][0], INSIDE[n][1]) if n in INSIDE else (None, None)))
