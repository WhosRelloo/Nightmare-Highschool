"""Props batch 22 (2026-11-04): the Main Hall's live notice board for nh_props.py, on theme with the Institution: cast
iron, brass and gilt, crimson enamel and wax, candlelight on aged parchment. No wood (the board's face is cork).

  MidnightBellBoard 6 x 4.5 frame (4.87 high with the crest, 6.82 wide with the candle sconces): a cork board in a cast-iron frame
                    with brass corner gussets and rosettes, a brass slip round the cork, a crimson enamel header plate
                    reading THE MIDNIGHT BELL in modelled gilt capitals between two gilt bells, a low pointed iron crest
                    with a gilt quatrefoil and finial, a cast-iron candle sconce on each side (the flames are Glow), and
                    four blank parchment cards in a 2 x 2 grid, each held by a crimson wax seal on its top edge.
                    The game draws live text on the cards with SurfaceGuis, so every card is its own flat piece
                    (Card1 top-left, Card2 top-right, Card3 bottom-left, Card4 bottom-right, as seen from the front)
                    whose bounding box is exactly the card: plain light parchment, darkened only at the very edge.
                    The card rectangles are written to art/props/midnight_bell_board_faces.json on every build.

Front faces -Y, Z is up, the origin is at the bottom centre of the board; it hangs on a wall with its back flat at +Y
(the hidden back faces of the cork, frame and cards are left open, so the atlas is spent on what shows).
Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish
from nh_props_batch3 import sphere, flame, cone, circle_pts
from nh_props_batch4 import lathe, hoop, _xform, _mark, _dims, flat
from nh_props_batch8 import _pointed
from nh_props_batch9 import foil, candle, wax_mat
from nh_props_batch10 import velvet
from nh_props_batch21 import frame_gilt
import nh_props_batch20 as B20


# ------------------------------------------------------------------ layout (studs)

W, H = 6.0, 4.5            # the frame
FW = 0.22                  # frame member width
YB = 0.10                  # the back plane (on the wall)
YF = -0.10                 # the frame's front face
HB = 3.86                  # header band bottom (cork opening top)
CW, CH, CT = 2.45, 1.55, 0.02   # card width, height, thickness
CARD_BACK = -0.002         # cards stand just proud of the cork face (y = 0)
SEAL_R = 0.1
FONT = "C:/Windows/Fonts/georgiab.ttf"   # Georgia Bold; Blender's built-in font if it is missing


def _cards():
    """(piece, cx, cz) of the four cards, as seen from the front (x < 0 is the viewer's left)."""
    ox0, ox1, oz0, oz1 = -(W / 2 - FW), W / 2 - FW, FW, HB
    gx = ((ox1 - ox0) - 2 * CW) / 3
    gz = ((oz1 - oz0) - 2 * CH) / 3
    xs = (ox0 + gx + CW / 2, ox1 - gx - CW / 2)
    zs = (oz1 - gz - CH / 2, oz0 + gz + CH / 2)
    return [("Card1", xs[0], zs[0]), ("Card2", xs[1], zs[0]), ("Card3", xs[0], zs[1]), ("Card4", xs[1], zs[1])]


# ------------------------------------------------------------------ materials

def _rgb_dst(m):
    """The flat material's colour node and the sockets it feeds (to splice a procedural colour in)."""
    nt = m.node_tree
    rgb = next(n for n in nt.nodes if n.type == "RGB")
    return nt, rgb, [lk.to_socket for lk in rgb.outputs[0].links]


def cork():
    """Pressed cork: fine dark and light granules over a mid brown, a few broad age blotches, granular bump."""
    m = P.material("Cork", base=(0.3, 0.18, 0.085), rough=0.9, wear=0.0, dirt=0.9)
    nt, rgb, dst = _rgb_dst(m)
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 48; fine.inputs["Detail"].default_value = 4
    fine.inputs["Roughness"].default_value = 0.7
    L(tc.outputs["Object"], fine.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.36, (0.075, 0.04, 0.02, 1)
    el[1].position, el[1].color = 0.66, (0.44, 0.28, 0.14, 1)
    mid = el.new(0.5); mid.color = (0.27, 0.16, 0.075, 1)
    L(fine.outputs["Fac"], ramp.inputs["Fac"])
    blot = nt.nodes.new("ShaderNodeTexNoise"); blot.inputs["Scale"].default_value = 0.9; blot.inputs["Detail"].default_value = 3
    L(tc.outputs["Object"], blot.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeMapRange")
    bm.inputs["From Min"].default_value, bm.inputs["From Max"].default_value = 0.45, 0.7
    bm.inputs["To Min"].default_value, bm.inputs["To Max"].default_value = 0.0, 0.45
    L(blot.outputs["Fac"], bm.inputs["Value"])
    age = nt.nodes.new("ShaderNodeMix"); age.data_type = "RGBA"; age.blend_type = "MULTIPLY"
    L(bm.outputs["Result"], age.inputs["Factor"]); L(ramp.outputs["Color"], age.inputs[6])
    age.inputs[7].default_value = (0.45, 0.38, 0.33, 1)
    for s in dst:
        L(age.outputs[2], s)
    bump = next(n for n in nt.nodes if n.type == "BUMP")
    bump.inputs["Strength"].default_value = 0.35
    L(fine.outputs["Fac"], bump.inputs["Height"])
    return m


def parchment(hw, hh, name="Parchment", base=(0.80, 0.69, 0.48), edge=(0.45, 0.32, 0.17)):
    """Aged parchment for a card hw x hh (half sizes, the card's own object space): one plain light colour with the
    faintest mottle, browned only in a thin worn band at the very edge (the outer 4 % each side), so the game's ink
    text reads on an even ground."""
    m = P.material(name, base=base, rough=0.82, wear=0.0, dirt=0.25)
    nt, rgb, dst = _rgb_dst(m)
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs["Vector"])
    def op(kind, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = kind; n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    ex = op("DIVIDE", op("ABSOLUTE", sep.outputs["X"]), hw)
    ez = op("DIVIDE", op("ABSOLUTE", sep.outputs["Z"]), hh)
    rim = op("MULTIPLY", op("SUBTRACT", op("MAXIMUM", ex, ez), 0.955), 1 / 0.045, clamp=True)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 5
    L(tc.outputs["Object"], nz.inputs["Vector"])
    ragged = op("MULTIPLY", op("POWER", rim, 1.6), op("ADD", op("MULTIPLY", nz.outputs["Fac"], 0.9), 0.25), clamp=True)
    mott = nt.nodes.new("ShaderNodeTexNoise"); mott.inputs["Scale"].default_value = 2.2; mott.inputs["Detail"].default_value = 3
    L(tc.outputs["Object"], mott.inputs["Vector"])
    faint = nt.nodes.new("ShaderNodeMix"); faint.data_type = "RGBA"; faint.blend_type = "MULTIPLY"
    L(op("MULTIPLY", op("SUBTRACT", mott.outputs["Fac"], 0.35, clamp=True), 0.12), faint.inputs["Factor"])
    L(rgb.outputs[0], faint.inputs[6]); faint.inputs[7].default_value = (0.9, 0.86, 0.8, 1)
    worn = nt.nodes.new("ShaderNodeMix"); worn.data_type = "RGBA"; worn.blend_type = "MIX"
    L(ragged, worn.inputs["Factor"]); L(faint.outputs[2], worn.inputs[6]); worn.inputs[7].default_value = (*edge, 1)
    for s in dst:
        L(worn.outputs[2], s)
    return m


def wax_seal_mat():
    """Crimson sealing wax (#600E1A), a little glossy."""
    return flat("SealWax", (0.15, 0.009, 0.017), 0.32, dirt=0.5)


def enamel():
    """The header plate's crimson enamel (#600E1A): a clean, glossy ground so the gilt capitals read (no chips or spatter)."""
    return flat("CrimsonEnamel", (0.105, 0.0055, 0.011), 0.26, wear=0.12, dirt=0.7)


def cast_iron():
    """The frame's cast iron: the school's iron set, darker and finer-grained for a frame this close to the eye."""
    return P.material("CastIron", "NH_Iron", tint=(0.085, 0.08, 0.09), scale=1.0, rough_add=0.08, wear=0.5, wear_metal=True, dirt=0.8)


# ------------------------------------------------------------------ helpers

def _open_back(ob, y=YB, eps=0.004):
    """Drop the faces that lie flat on the wall at +Y (never seen), before the bevel is applied."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    gone = [f for f in bm.faces if (mw.to_3x3() @ f.normal).y > 0.99 and (mw @ f.calc_center_median()).y > y - eps]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def _lettering(name, text, cx, y_back, cz, width, cap, mat, depth=0.022):
    """Modelled capitals standing on a face at y_back (facing -Y), centred at (cx, cz), fitted to `width` (cap height at
    most `cap`). Converted to mesh and triangulated so the concave letter faces import into Roblox correctly."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    if os.path.exists(FONT):
        cu.font = bpy.data.fonts.load(FONT)
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size = 1.0
    cu.space_character = 1.1
    cu.extrude = 0.5 * depth
    cu.bevel_depth = 0.0
    cu.resolution_u = 3
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    s = min(width / (max(xs) - min(xs)), cap / (max(ys) - min(ys)))
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    zmax = max(v.co.z for v in me.vertices)
    for v in me.vertices:
        x, yy, z = v.co
        # font plane XY (face +Z) -> the wall's XZ plane facing -Y; depth keeps its true size, back at y_back
        v.co = Vector((cx + (x - mx) * s, y_back - (z - (zmax - depth)), cz + (yy - my) * s))
    me.update()
    _open_back(ob, y=y_back)
    _finish(ob, mat, 0)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    md.quad_method = "BEAUTY"
    md.ngon_method = "BEAUTY"
    return ob


def _bell(prefix, x, y, z, mat, s=1.0):
    """A small hand bell (mouth down) with a clapper and a crown loop, at (x, y, z) = its mouth centre."""
    prof = [(0, 0.2), (0.035, 0.2), (0.06, 0.18), (0.068, 0.12), (0.078, 0.06), (0.1, 0.02), (0.118, 0.0), (0.11, -0.012),
            (0.09, 0.0), (0.06, 0.05), (0, 0.06)]
    lathe(f"{prefix}Bell", [(r * s, zz * s) for r, zz in prof], mat, seg=16, loc=(x, y, z))
    sphere(f"{prefix}Clapper", 0.028 * s, (x, y, z - 0.02 * s), mat, seg=8, rings=4)
    hoop(f"{prefix}Loop", (x, y, z + 0.235 * s), 0.035 * s, "Y", mat, thick=0.011 * s)


def _sconce(prefix, sx, M, wax):
    """A cast-iron candle sconce beside the frame: a pointed wall plate (back on the wall), a scrolled arm, a brass drip
    pan, a wax candle; the flame is Glow."""
    iron, brass = M["iron"], M["brass"]
    x0 = sx * 3.2
    hw, z0 = 0.13, 2.7
    plate = [(x0 + u, z) for u, z in [(-hw, z0), (hw, z0)] + list(reversed(_pointed(hw, 3.22, 3.48, 6)))]
    B20.tprism(f"{prefix}Plate", plate, YB - 0.025, 0.05, iron, bevel=0.008)
    tip = [(x0 + u, z) for u, z in ((-0.06, z0), (0.06, z0), (0.0, z0 - 0.14))]
    B20.tprism(f"{prefix}PlateTip", tip, YB - 0.025, 0.05, iron, bevel=0.006)
    sphere(f"{prefix}Boss", 0.04, (x0, YB - 0.06, 3.28), brass, seg=10, rings=5)
    sphere(f"{prefix}Boss2", 0.03, (x0, YB - 0.06, 2.76), brass, seg=10, rings=5)
    cx, cy = x0 + sx * 0.06, -0.38
    tube(f"{prefix}Arm", [(x0, YB - 0.04, 2.98), (x0 + sx * 0.02, -0.12, 2.86), (x0 + sx * 0.05, -0.3, 2.93), (cx, cy, 3.1)], 0.03, iron)
    tube(f"{prefix}Curl", [(x0 + sx * 0.02, -0.16, 2.86), (x0 + sx * 0.02, -0.24, 2.74), (x0 + sx * 0.02, -0.17, 2.66),
                           (x0 + sx * 0.02, -0.11, 2.72), (x0 + sx * 0.02, -0.15, 2.77)], 0.016, iron)
    lathe(f"{prefix}Pan", [(0, 3.1), (0.14, 3.1), (0.152, 3.14), (0.135, 3.152), (0.05, 3.14), (0.045, 3.215), (0.058, 3.235),
                           (0.05, 3.24), (0, 3.24)], brass, seg=16, loc=(cx, cy, 0))
    sphere(f"{prefix}PanDrip", 0.03, (cx - sx * 0.07, cy - 0.04, 3.15), wax, seg=8, rings=4, scale=(1.3, 1.0, 0.45))
    top = candle(f"{prefix}Candle", cx, cy, 3.235, 0.42, wax, r=0.05)
    set_group("Glow")
    flame(f"{prefix}Flame", (cx, cy, top - 0.005), h=0.12)
    set_group("Main")


def _corner(prefix, sx, sz, M):
    """A brass corner gusset: a triangle over the frame's corner with a boss and two rivets."""
    brass = M["brass"]
    zc = 0.0 if sz < 0 else H
    cxp = sx * W / 2
    tri = [(cxp, zc), (cxp - sx * 0.42, zc), (cxp, zc - sz * 0.42)]
    B20.tprism(f"{prefix}Gusset", [(x - sx * 0.02, z - sz * 0.02) for x, z in tri], YF - 0.016, 0.03, brass, bevel=0.008)
    gx, gz = cxp - sx * 0.13, zc - sz * 0.13
    sphere(f"{prefix}Boss", 0.055, (gx, YF - 0.035, gz), brass, seg=12, rings=6, scale=(1, 0.7, 1))
    for k, (dx, dz) in enumerate(((0.27, 0.06), (0.06, 0.27))):
        sphere(f"{prefix}Rivet{k}", 0.022, (cxp - sx * dx, YF - 0.035, zc - sz * dz), brass, seg=8, rings=4, scale=(1, 0.6, 1))


# ------------------------------------------------------------------ the board

def midnight_bell_board(M):
    rnd = random.Random(2204)
    M = dict(M, iron=cast_iron())
    iron, brass, gl = M["iron"], M["brass"], frame_gilt()
    wax, seal = wax_mat(), wax_seal_mat()

    # cork and the cast-iron frame (backs open on the wall)
    _open_back(box("Cork", (W - 0.36, YB, HB - 0.2 + 0.02), (0, YB / 2, (HB + 0.2) / 2), cork(), bevel=0.004))
    for sx in (-1, 1):
        _open_back(box(f"Stile{sx}", (FW, YB - YF, H), (sx * (W / 2 - FW / 2), (YB + YF) / 2, H / 2), iron, bevel=0.03))
    _open_back(box("Rail", (W - 2 * FW, YB - YF, FW), (0, (YB + YF) / 2, FW / 2), iron, bevel=0.03))
    _open_back(box("HeaderBand", (W - 2 * FW, YB - YF, H - HB), (0, (YB + YF) / 2, (H + HB) / 2), iron, bevel=0.03))
    ox, oz0, oz1 = W / 2 - FW, FW, HB
    tube("Slip", [(-ox, YF + 0.005, oz0), (ox, YF + 0.005, oz0), (ox, YF + 0.005, oz1), (-ox, YF + 0.005, oz1)], 0.028, brass, closed=True,
         poly=True)
    tube("OuterBead", [(-W / 2 + 0.035, YF, 0.035), (W / 2 - 0.035, YF, 0.035), (W / 2 - 0.035, YF, H - 0.035), (-W / 2 + 0.035, YF, H - 0.035)],
         0.032, iron, closed=True, poly=True)
    # cast-iron rivets down the stiles and along the rail, brass rosettes at mid height and on the rail
    for sx in (-1, 1):
        for k in range(7):
            z = 0.75 + k * 0.5
            if abs(z - 2.0) < 0.2:
                continue
            sphere(f"Rivet{sx}{k}", 0.024, (sx * (W / 2 - FW / 2), YF - 0.005, z), iron, seg=6, rings=3, scale=(1, 0.6, 1))
        foil(f"Rose{sx}", sx * (W / 2 - FW / 2), YF - 0.012, 2.04, 0.075, brass, thick=0.016)
        sphere(f"RoseBoss{sx}", 0.03, (sx * (W / 2 - FW / 2), YF - 0.03, 2.04), brass, seg=8, rings=4)
    for k in range(8):
        x = -2.1 + k * 0.6
        if abs(x) < 0.2:
            continue
        sphere(f"RailRivet{k}", 0.024, (x, YF - 0.005, FW / 2), iron, seg=6, rings=3, scale=(1, 0.6, 1))
    foil("RailRose", 0, YF - 0.012, FW / 2, 0.075, brass, thick=0.016)
    sphere("RailBoss", 0.03, (0, YF - 0.03, FW / 2), brass, seg=8, rings=4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            _corner(f"Corner{sx}{sz}", sx, sz, M)

    # the crimson enamel header plate with gilt lettering and two gilt bells
    pw, ph, pz = 2 * 2.66, 0.46, (HB + H) / 2
    yp = YF - 0.02                    # plate front
    _open_back(box("Plate", (pw, 0.03, ph), (0, yp + 0.015, pz), enamel(), bevel=0.008), y=yp + 0.03)
    tube("PlateRim", [(-pw / 2, yp, pz - ph / 2), (pw / 2, yp, pz - ph / 2), (pw / 2, yp, pz + ph / 2), (-pw / 2, yp, pz + ph / 2)], 0.018, gl,
         closed=True, square=True, poly=True)
    _lettering("Title", "THE MIDNIGHT BELL", 0, yp + 0.004, pz - 0.005, 3.95, 0.27, gl)
    for sx in (-1, 1):
        _bell(f"Bell{sx}", sx * 2.33, yp - 0.07, pz - 0.12, gl, s=1.0)
        for dz in (-1, 1):
            sphere(f"PlateStud{sx}{dz}", 0.018, (sx * (pw / 2 - 0.07), yp - 0.01, pz + dz * (ph / 2 - 0.07)), gl, seg=8, rings=4)
    # a low pointed iron crest over the header with a gilt quatrefoil and finial
    edge = [(t, H - 0.02 + 0.3 * (1 - abs(t)) ** 1.7) for t in [k / 6 - 1 for k in range(13)]]
    B20.tprism("Crest", [(-1.0, H - 0.04)] + edge[1:-1] + [(1.0, H - 0.04)], (YB + YF) / 2 + 0.03, YB - YF - 0.06, iron, bevel=0.012)
    tube("CrestEdge", [(x, -0.05, z + 0.01) for x, z in edge], 0.02, iron, poly=True)
    # cast-iron spear finials over the top corners
    for sx in (-1, 1):
        x = sx * (W / 2 - FW / 2)
        cyl(f"FinialCollar{sx}", 0.045, 0.06, (x, 0.0, H + 0.03), iron, verts=10, bevel=0)
        cone(f"Finial{sx}", 0.04, 0.0, 0.2, (x, 0.0, H + 0.16), iron, verts=8)
        sphere(f"FinialKnop{sx}", 0.035, (x, 0.0, H + 0.08), brass, seg=10, rings=5)
    foil("CrestFoil", 0, -0.052, H + 0.11, 0.07, gl, thick=0.014)
    sphere("CrestFinial", 0.05, (0, (YB + YF) / 2 + 0.02, H + 0.32), gl, seg=12, rings=6)

    # cork dressing (none of it touches a card): a crimson ribbon rosette pinned at the centre cross, spare pins in the
    # gaps, two torn scraps tucked under the frame at opposite corners
    cards = _cards()
    cxg, czg = 0.0, (cards[0][2] - CH / 2 + cards[2][2] + CH / 2) / 2
    vel = velvet()
    for k in range(6):
        a = k / 6 * 2 * math.pi
        sphere(f"RosettePetal{k}", 0.035, (cxg + math.cos(a) * 0.042, -0.012, czg + math.sin(a) * 0.042), vel, seg=8, rings=4, scale=(1, 0.4, 1))
    sphere("RosettePin", 0.022, (cxg, -0.03, czg), brass, seg=8, rings=4)
    for k, (x, z) in enumerate(((-2.67, 2.0), (2.67, 2.1), (-0.0, 0.31), (0.0, 3.77), (-0.62, czg), (0.7, czg))):
        sphere(f"SparePin{k}", 0.02, (x, -0.022, z), M["brasssteel"] if k % 2 else brass, seg=8, rings=4)
        cyl(f"SparePinShank{k}", 0.006, 0.02, (x, -0.008, z), M["brasssteel"], rot=(math.pi / 2, 0, 0), verts=6, bevel=0)
    scrap = flat("Scrap", (0.62, 0.5, 0.33), 0.85, dirt=0.6)
    box("ScrapTop", (0.42, 0.008, 0.26), (2.38, -0.004, 3.86), scrap, bevel=0.0, segments=1, rot=(0, math.radians(5), 0))
    box("ScrapLow", (0.4, 0.008, 0.24), (-2.42, -0.004, 0.24), scrap, bevel=0.0, segments=1, rot=(0, math.radians(-4), 0))

    # the candle sconces
    for sx in (-1, 1):
        _sconce(f"Sconce{sx}", sx, M, wax)

    # the four blank cards, each its own piece; a crimson wax seal straddles each card's top edge (in Main)
    card_mat = parchment(CW / 2, CH / 2)
    cy = CARD_BACK - CT / 2
    seal_x = {}
    for k, (name, x, z) in enumerate(cards):
        set_group(name)
        _open_back(box(name, (CW, CT, CH), (x, cy, z), card_mat, bevel=0.0, segments=1), y=CARD_BACK)
        set_group("Main")
        s = _mark()
        lathe(f"{name}Seal", [(0, 0), (SEAL_R, 0), (SEAL_R * 1.04, 0.012), (SEAL_R * 0.88, 0.027), (SEAL_R * 0.55, 0.032), (0, 0.032)], seal,
              seg=20, jitter=(0.07, 50 + k))
        tube(f"{name}SealRing", circle_pts(0, 0, 0.034, SEAL_R * 0.5, "Z", 8), 0.007, seal, closed=True, poly=True)
        sphere(f"{name}SealBell", 0.016, (0, 0, 0.034), seal, seg=8, rings=4, scale=(1, 1, 0.5))
        seal_x[name] = x + rnd.uniform(-0.12, 0.12)
        _xform(s, Matrix.Translation((seal_x[name], CARD_BACK - CT, z + CH / 2 - 0.01)) @ Matrix.Rotation(math.pi / 2, 4, "X"))

    _write_faces(cards, seal_x)
    return _dims()


def _write_faces(cards, seal_x):
    """The card rectangles in the prop's own studs, for the game's SurfaceGuis (art/props/midnight_bell_board_faces.json)."""
    bpy.context.view_layer.update()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in P.PARTS:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for k in range(3):
                lo[k], hi[k] = min(lo[k], w[k]), max(hi[k], w[k])
    r = lambda v: round(v, 4)
    front = CARD_BACK - CT
    out = {
        "_note": ("MidnightBellBoard cards, in the prop's own studs as modelled in Blender: origin at the board's bottom centre, X to the "
                  "viewer's right when facing the board, Y into the wall (the front faces -Y, the back is flat on the wall at y = back_y), "
                  "Z up. Each card is its own piece (MidnightBellBoard_CardN) whose bounding box is exactly the card (wax seals are in Main), "
                  "so a SurfaceGui on that MeshPart's Front face covers the card. Roblox axes after import (front = -Z, LookVector): "
                  "X_rbx = -x, Y_rbx = z, Z_rbx = y, relative to the same origin; a MeshPart's position is its bounding-box centre. "
                  "text_safe keeps clear of the crimson wax seal on the top edge and the browned rim."),
        "dims": [r(hi[0] - lo[0]), r(hi[1] - lo[1]), r(hi[2] - lo[2])],
        "bbox_min": [r(v) for v in lo],
        "bbox_max": [r(v) for v in hi],
        "back_y": YB,
        "frame": {"width": W, "height": H, "cork_opening": {"x": [-(W / 2 - FW), W / 2 - FW], "z": [FW, HB]}},
        "cards": [],
    }
    for name, x, z in cards:
        out["cards"].append({
            "piece": f"MidnightBellBoard_{name}",
            "position": {"Card1": "top-left", "Card2": "top-right", "Card3": "bottom-left", "Card4": "bottom-right"}[name],
            "center": [r(x), r(CARD_BACK - CT / 2), r(z)],
            "face_center": [r(x), r(front), r(z)],
            "width": CW,
            "height": CH,
            "thickness": CT,
            "front_y": r(front),
            "seal": {"center_x": r(seal_x[name]), "center_z": r(z + CH / 2 - 0.01), "radius": round(SEAL_R * 1.07, 3)},
            "text_safe": {"center": [r(x), r(front), r(z - 0.035)], "width": r(CW - 0.2), "height": r(CH - 0.23)},
        })
    with open(os.path.join(P.HERE, "midnight_bell_board_faces.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


P.PREVIEW_PAD.update({"MidnightBellBoard": 1.0})
P.BUILD.update({
    "MidnightBellBoard": midnight_bell_board,
})
