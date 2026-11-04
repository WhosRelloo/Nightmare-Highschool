"""Props batch 12 (2026-11-03): town building pieces for nh_props.py, a modular facade kit the builder attaches to
the town's buildings. Nightmare High's gritty gothic night-town: dark sooty castle stone (the same greenish grey as
the NHCastleStone wall material, so a wall built in it blends in), slate and lead, cast iron, oxblood and crimson
paint, brass, warm gaslit windows, moss and grime. Widths keep to the 8-stud rhythm the wall material tiles on.

  TownDoor     a stone doorway with long-and-short quoins, a pointed arch of voussoirs under a hood mould with
               carved label stops and a shield keystone, an iron sunburst fanlight (Glass), a studded oxblood
               iron-clad door with strap hinges, a knocker, a handle and a letter plate (Door0: hinged on its left
               edge, swings IN, toward +Y, into the building), a wall lantern on a scrolled bracket (Glass, Glow)
               and a stone step
  TownWindow   a tall sash window: quoined jambs, a flat arch of voussoirs with a keystone, a hood mould, a sill on
               brackets, black iron sashes (Glass), a warm lit room behind (Glow) with crimson curtains, a pelmet
               and a cat's silhouette on the inner sill, and louvred oxblood iron shutters folded back
  BayWindow    an oriel bay on a corbelled stone base with a grotesque: traceried aprons, colonnettes at the
               corners, leaded diamond-pane windows (Glass) with a lit room behind (Glow), a carved quatrefoil frieze,
               a stepped cornice and a canted lead roof with rolled hips and standing seams
  Chimney      a brick stack on a stone base: a stone string course, an iron band with tie plates, an oversailing
               corbelled cap, three clay pots (one fluted, one under an iron cowl), soot and moss; smoke rises from
               the middle pot (an NHAmbient:Steam spot)
  IronBalcony  an 8-stud wall balcony: a moulded stone slab on four scrolled iron consoles, a wrought-iron railing
               with a ring frieze, quatrefoil medallions and spear-topped newels
  ShopAwning   an 8-stud wall-mounted awning: crimson and black striped canvas sagging between iron ribs on folding
               arms, and a scalloped valance with tassels (Cloth: sways from the front bar)
  Dormer       a roof dormer for a 45-degree roof: slate-hung cheeks, a stone gable with coping, kneelers, a trefoil
               vent and a pinnacle, a pointed casement with leaded panes (Glass) and a dim lamp (Glow), a slate roof
               with an iron-crested ridge and a lead apron
  Drainpipe    a 12-stud cast-iron downpipe: a hopper head with a shield and a raven perched on the rim, socket
               collars with wall ears every two studs, and a shoe spilling onto a gully grate
  StoneStoop   front steps: a landing and three steps between sloped cheek walls with coping and newel piers,
               iron handrails with a scroll at the foot, and a boot scraper on the landing

Front faces -Y, Z is up, the origin is at the bottom centre. The wall pieces (TownDoor, TownWindow, BayWindow,
IronBalcony, ShopAwning, Drainpipe, StoneStoop) have their back flat at y = 0, the builder's wall face.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _strap_hinge, _arch_loop, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat, _mesh, _solid
from nh_props_batch6 import relief
from nh_props_batch8 import castle, mossy, hollow, staining, _moss, _foil, _pointed, _lancet, _panel, _lantern, _lights, \
    _crack, _spirelet, _grotesque, _spike
from nh_props_batch9 import raven, wax_mat


# ------------------------------------------------------------------ materials

def soot_stone(name, tint):
    """The town's stone: the castle limestone set, darker and sootier than the courtyard's, with soot running down it
    in vertical streaks (a stretched noise darkening the colour)."""
    m = material(name, "NH_Limestone", tint=tint, scale=0.28, wear=0.15, dirt=1.0, rough_add=0.08)
    nt = m.node_tree
    L = nt.links.new
    tint_mix = next(n for n in nt.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY" and n.inputs["Factor"].default_value == 1.0)
    dst = [lk.to_socket for lk in tint_mix.outputs[2].links]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.6, 2.6, 0.32)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 4.0
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.38, 0.64
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    L(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    L(ramp.outputs["Color"], mix.inputs["Factor"])
    L(tint_mix.outputs[2], mix.inputs[6])
    mix.inputs[7].default_value = (0.3, 0.29, 0.28, 1)
    for d in dst:
        L(mix.outputs[2], d)
    return m


def room_mat(name, lamp, radius, hot, cold):
    """The lit room seen through a window: a warm amber pool of light round the lamp at `lamp`, falling off to dark
    at `radius` (coordinates in a marker empty's space, so it survives the parts being joined)."""
    emp = bpy.data.objects.new(name + "Centre", None)
    emp.location = lamp
    bpy.context.collection.objects.link(emp)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.object = emp
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    L(tc.outputs["Object"], ln.inputs[0])
    dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = radius
    L(ln.outputs["Value"], dv.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.use_clamp = True; inv.inputs[0].default_value = 1.0
    L(dv.outputs[0], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.15
    L(inv.outputs[0], pw.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L(pw.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*cold, 1)
    mix.inputs[7].default_value = (*hot, 1)
    rv = nt.nodes.new("ShaderNodeValue"); rv.outputs[0].default_value = 0.9
    mv = nt.nodes.new("ShaderNodeValue"); mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mix.outputs[2], rv.outputs[0], mv.outputs[0], None, 0.0, False, 0.3)
    return m


def kit(M):
    worn, _ = castle()
    return {
        "st": soot_stone("SootStone", (0.15, 0.158, 0.148)), "dk": soot_stone("SootStoneDark", (0.09, 0.095, 0.088)), "worn": worn,
        "iron": M["iron"], "brass": M["brass"], "glass": M["glassclear"],
        "grime": flat("Grime", (0.03, 0.029, 0.027), 0.92, dirt=0.3),
        "oxblood": material("Oxblood", "NH_PaintedMetal", tint=(0.15, 0.018, 0.026), scale=0.9, wear=0.55, wear_metal=True),
        "enamel": material("OxbloodEnamel", "NH_PaintedMetal", tint=(0.12, 0.014, 0.02), scale=1.6, rough_mul=0.5, rough_add=0.05, wear=0.5,
                           wear_metal=True, dirt=0.85),
        "lead": material("Lead", "NH_PaintedMetal", tint=(0.15, 0.165, 0.175), scale=0.7, rough_add=0.3, wear=0.2),
        "slate": material("RoofSlate", "NH_Slate", tint=(0.04, 0.05, 0.07), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.15),
        "slates": [material(f"Slate{i}", "NH_Slate", tint=t, scale=0.5, rough_mul=0.55, rough_add=0.28, normal=0.7, wear=0.25)
                   for i, t in enumerate(((0.042, 0.056, 0.08), (0.032, 0.044, 0.064), (0.056, 0.068, 0.088)))],
        "velvet": material("Velvet", "NH_Leather", tint=(0.2, 0.02, 0.035), scale=3.0, normal=0.25, rough_add=0.4, wear=0.05),
        "moss": mossy(), "hollow": hollow(), "stain": staining(),
        "soot": flat("Soot", (0.012, 0.011, 0.012), 0.9),
        "glow": flat("LampGlow", (1.0, 0.55, 0.22), 0.5),
    }


def brick_mat(name, rgb1=(0.105, 0.032, 0.025), rgb2=(0.068, 0.026, 0.022), mortar=(0.085, 0.085, 0.08)):
    """Sooty old brick (a procedural course pattern on the faces, with gritty colour from the limestone set), with
    the same bake-time weathering as every other material."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
    L(sep.outputs["X"], add.inputs[0]); L(sep.outputs["Y"], add.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    L(add.outputs[0], comb.inputs["X"]); L(sep.outputs["Z"], comb.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.offset_frequency = 0.5, 2
    L(comb.outputs["Vector"], br.inputs["Vector"])
    br.inputs["Color1"].default_value = (*rgb1, 1)
    br.inputs["Color2"].default_value = (*rgb2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.022
    br.inputs["Mortar Smooth"].default_value = 0.15
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = 0.62
    br.inputs["Row Height"].default_value = 0.21
    grit = P._tex(nt, "NH_Limestone", "color", 0.6, 0, 300)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.85
    L(br.outputs["Color"], mix.inputs[6]); L(grit.outputs["Color"], mix.inputs[7])
    rgh = nt.nodes.new("ShaderNodeMath"); rgh.operation = "MULTIPLY_ADD"
    L(br.outputs["Fac"], rgh.inputs[0]); rgh.inputs[1].default_value = 0.08; rgh.inputs[2].default_value = 0.86
    mv = nt.nodes.new("ShaderNodeValue"); mv.outputs[0].default_value = 0.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.03
    L(br.outputs["Fac"], bump.inputs["Height"])
    nrm = P._tex(nt, "NH_Limestone", "normal", 0.6, 0, -300)
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.5
    L(nrm.outputs["Color"], nm.inputs["Color"]); L(nm.outputs["Normal"], bump.inputs["Normal"])
    P._weather(nt, bs, mix.outputs[2], rgh.outputs[0], mv.outputs[0], bump.outputs["Normal"], 0.25, False, 0.95)
    return m


# ------------------------------------------------------------------ helpers

def sheet(name, polys, mat, thick):
    """Flat polygons (lists of 3D points) as one thin solid sheet."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for poly in polys:
        bm.faces.new([bm.verts.new(tuple(p)) for p in poly])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    return _solid(ob, thick)


def frustum(name, c, w0, d0, z0, w1, d1, z1, mat, bevel=0.01):
    """A box tapering from w0 x d0 at z0 to w1 x d1 at z1, centred on c = (x, y)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    lo = [bm.verts.new((c[0] + sx * w0 / 2, c[1] + sy * d0 / 2, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [bm.verts.new((c[0] + sx * w1 / 2, c[1] + sy * d1 / 2, z1)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, bevel)


def lattice(prefix, x0, x1, z0, z1, y, step, mat, r=0.011):
    """Leaded lights: diagonal cames in a diamond pattern across a rectangle in the XZ plane at y."""
    k = 0
    for sgn in (1, -1):
        cmid = (x0 + x1) / 2 - sgn * (z0 + z1) / 2
        n = int((x1 - x0 + z1 - z0) / step) + 2
        for i in range(-n, n + 1):
            c = cmid + i * step
            if sgn == 1:            # x - z = c
                xa, xb = max(x0, z0 + c), min(x1, z1 + c)
                pts = [(xa, y, xa - c), (xb, y, xb - c)]
            else:                   # x + z = c
                xa, xb = max(x0, c - z1), min(x1, c - z0)
                pts = [(xa, y, c - xa), (xb, y, c - xb)]
            if xb - xa > 0.03:
                tube(f"{prefix}{k}", pts, r, mat, square=True, poly=True)
                k += 1


def quoins(prefix, x_in, z0, heights, depth, mat, long=0.85, short=0.6, gap=0.025):
    """Long-and-short jamb stones either side of an opening of half width x_in, from z0 up; returns the top."""
    z = z0
    for k, h in enumerate(heights):
        w = long if k % 2 == 0 else short
        for sx in (-1, 1):
            box(f"{prefix}{sx}{k}", (w, depth, h - gap), (sx * (x_in + w / 2), -depth / 2, z + h / 2), mat, bevel=0.04, segments=1)
        z += h
    return z


def curtain(prefix, x_out, x_in, z_top, z_tie, z_bot, y, mat, cord):
    """A velvet curtain hanging from z_top, gathered by a tie-back at z_tie, flaring a little below it."""
    x_tie = x_out + (x_in - x_out) * 0.38
    x_flare = x_out + (x_in - x_out) * 0.6
    rows = []
    nz, nx = 16, 10
    for i in range(nz + 1):
        t = i / nz
        z = z_top + (z_bot - z_top) * t
        if z >= z_tie:
            u = (z_top - z) / (z_top - z_tie)
            u = u * u * (3 - 2 * u)
            xi = x_in + (x_tie - x_in) * u
        else:
            u = (z_tie - z) / (z_tie - z_bot)
            xi = x_tie + (x_flare - x_tie) * math.sqrt(u)
        row = []
        for j in range(nx + 1):
            s = j / nx
            x = x_out + (xi - x_out) * s
            amp = 0.035 + 0.03 * (1 - abs(x_in - xi) / abs(x_in - x_out + 1e-6))
            row.append(Vector((x, y - amp * math.sin(s * math.pi * 4.0), z)))
        rows.append(row)
    _mesh(prefix, rows, mat, 0.02)
    xc = (x_out + x_tie) / 2
    tube(f"{prefix}Tie", [(x_out, y - 0.02, z_tie + 0.05), (xc, y - 0.09, z_tie), (x_tie + 0.04 * (1 if x_in > x_out else -1), y - 0.06, z_tie + 0.03)],
         0.018, cord)
    sphere(f"{prefix}Tassel", 0.04, (xc, y - 0.1, z_tie - 0.06), cord, seg=8, rings=4, scale=(1, 1, 1.6))


def iring(name, c, r, axis, mat, thick, n):
    """A light square-section iron ring (n sides): axis is its normal."""
    return tube(name, circle_pts(c[0], c[1], c[2], r, axis, n), thick, mat, closed=True, square=True, poly=True)


def bracket_scroll(prefix, x, y0, y1, z_top, z_bot, mat, r=0.035):
    """A scrolled wrought-iron console in the YZ plane at x: a top bar out from the wall (y0) to y1, a back bar down
    the wall, a C-scroll filling the corner and a curl at the bottom."""
    tube(f"{prefix}Top", [(x, y0, z_top), (x, y1, z_top)], r, mat, square=True, poly=True)
    tube(f"{prefix}Back", [(x, y0, z_top), (x, y0, z_bot)], r, mat, square=True, poly=True)
    d = y1 - y0
    h = z_top - z_bot
    tube(f"{prefix}Scroll", [(x, y0, z_bot + h * 0.08), (x, y0 + d * 0.3, z_bot + h * 0.3), (x, y0 + d * 0.62, z_bot + h * 0.62),
                             (x, y0 + d * 0.92, z_top - 0.04)], r * 0.85, mat, square=True)
    hoop(f"{prefix}Curl", (x, y0 + d * 0.2, z_bot + h * 0.12), min(0.1, h * 0.1), "X", mat, thick=r * 0.6)
    hoop(f"{prefix}Curl2", (x, y0 + d * 0.72, z_top - h * 0.22), min(0.12, h * 0.12), "X", mat, thick=r * 0.6)


# ================================================================== town door
def town_door(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(1201)
    W, ZT, D = 2.0, 0.5, 0.9
    # the step, running under the threshold
    box("Step", (6.0, 1.8, 0.5), (0, -0.9, 0.25), K["worn"], bevel=0.06)
    # quoined jambs and a pointed arch of voussoirs
    ZS = quoins("Jamb", W, ZT, [1.0, 0.95, 0.95, 1.0, 0.95, 0.95], D, st)
    ZA = ZS + 1.45
    inner = _pointed(W, ZS, ZA, n=14)
    outer = _pointed(W + 0.78, ZS, ZA + 0.82, n=14)
    for i in range(0, len(inner) - 1, 2):
        if i in (12, 14):
            continue          # the keystone goes there
        poly = [inner[i], inner[i + 2], outer[i + 2], outer[i]]
        cx = sum(p[0] for p in poly) / 4
        cz = sum(p[1] for p in poly) / 4
        poly = [(cx + (x - cx) * 0.975, cz + (z - cz) * 0.975) for x, z in poly]
        prism(f"Vous{i}", poly, -D / 2, D, st, bevel=0.03)
    key = [inner[12], inner[16], (outer[16][0] + 0.08, ZA + 0.9), (outer[12][0] - 0.08, ZA + 0.9)]
    prism("Keystone", key, -D / 2 - 0.06, D + 0.12, st, bevel=0.03)
    shield = [(-0.2, ZA + 0.62), (0.2, ZA + 0.62), (0.2, ZA + 0.32), (0.12, ZA + 0.14), (0.0, ZA + 0.06), (-0.12, ZA + 0.14), (-0.2, ZA + 0.32)]
    relief("KeyShield", shield, -D - 0.14, 0.05, dk, bevel=0.01)
    _foil("KeyFoil", 0, -D - 0.17, ZA + 0.38, 0.09, st, lobes=4, thick=0.012)
    # the hood mould hugging the arch, returning sideways at the springing onto carved label stops
    hw_h = W + 0.9
    hood = _pointed(hw_h, ZS, ZA + 0.98, n=16)
    yh = -D - 0.07
    tube("Hood", [(-(hw_h + 0.32), yh, ZS)] + [(x, yh, z) for x, z in hood] + [(hw_h + 0.32, yh, ZS)], 0.09, dk, square=True, poly=True)
    for sx in (-1, 1):
        box(f"Label{sx}", (0.36, 0.26, 0.4), (sx * (hw_h + 0.3), yh, ZS - 0.26), dk, bevel=0.035)
        _foil(f"LabelFoil{sx}", sx * (hw_h + 0.3), yh - 0.14, ZS - 0.28, 0.11, st, lobes=4, thick=0.014)
    # the transom and the sunburst fanlight
    zt = ZS + 0.22
    box("Transom", (2 * W, 0.55, 0.22), (0, -0.45, ZS + 0.11), dk, bevel=0.02)
    zc = zt
    yb = -0.5
    tube("FanHub", [(math.cos(a) * 0.5, yb, zc + math.sin(a) * 0.5) for a in [i / 12 * math.pi for i in range(13)]], 0.028, iron,
         square=True, poly=True)
    for k in range(1, 8):
        a = k / 8 * math.pi
        end = min(inner, key=lambda p: abs(math.atan2(p[1] - zc, p[0]) - a) if p[1] > zc else 9)
        tube(f"FanBar{k}", [(math.cos(a) * 0.5, yb, zc + math.sin(a) * 0.5), (end[0] * 0.98, yb, zc + (end[1] - zc) * 0.98)], 0.022, iron,
             square=True, poly=True)
    tube("FanRim", [(x * 0.985, yb, max(zc, z - 0.02)) for x, z in inner], 0.028, iron, square=True, poly=True)
    set_group("Glass")
    pane = [(x, max(zc, z)) for x, z in inner]
    prism("Fanlight", pane, -0.45, 0.03, K["glass"])
    # the door: oxblood iron-clad, studded, hinged on its left edge and opening into the building (+Y)
    set_group("Door0", hinge=(-W + 0.03, -0.1, ZT), swing=1)
    LW, LH = 2 * W - 0.07, ZS - ZT - 0.03
    z0 = ZT + 0.01
    ox = K["oxblood"]
    box("Leaf", (LW, 0.16, LH), (0, -0.2, z0 + LH / 2), ox, bevel=0.02)
    yf = -0.3
    rails = [(z0 + 0.3, 0.5, iron), (z0 + 2.55, 0.3, ox), (z0 + LH - 0.2, 0.34, ox)]
    for k, (zr, h, mt) in enumerate(rails):
        box(f"Rail{k}", (LW - 0.04, 0.05, h), (0, yf, zr), mt, bevel=0.012)
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.28, 0.05, LH - 0.04), (sx * (LW / 2 - 0.16), yf, z0 + LH / 2), ox, bevel=0.012)
    box("Muntin", (0.22, 0.05, LH - 0.9), (0, yf, z0 + 0.55 + (LH - 0.9) / 2), ox, bevel=0.012)
    pw = (LW - 0.56 - 0.22) / 2
    for sx in (-1, 1):
        cx = sx * (0.11 + pw / 2)
        # upper panels: a raised pointed-arch moulding; lower panels: an iron saltire
        tube(f"PanelArch{sx}", _arch_loop(cx, yf - 0.01, pw / 2 - 0.14, z0 + 2.9, z0 + LH - 1.0, z0 + LH - 0.52), 0.03, ox, square=True,
             closed=True, poly=True)
        _foil(f"PanelFoil{sx}", cx, yf - 0.03, z0 + LH - 0.92, 0.1, brass, lobes=4, thick=0.012)
        for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
            hx, zz0, zz1 = pw / 2 - 0.08, z0 + 0.62, z0 + 2.33
            tube(f"Saltire{sx}{a[0]}{a[1]}", [(cx + a[0] * hx, yf - 0.02, zz0 if a[1] < 0 else zz1), (cx + b[0] * hx, yf - 0.02, zz1 if b[1] > 0 else zz0)],
                 0.03, iron, square=True, poly=True)
        sphere(f"SaltireBoss{sx}", 0.06, (cx, yf - 0.05, (z0 + 0.62 + z0 + 2.33) / 2), iron, seg=8, rings=4, scale=(1, 0.6, 1))
    # studs along the rails and stiles
    k = 0
    for zr, h, _ in rails:
        for i in range(13):
            x = -LW / 2 + 0.2 + i * (LW - 0.4) / 12
            sphere(f"Stud{k}", 0.034, (x, yf - 0.035, zr), iron, seg=6, rings=3)
            k += 1
    for sx in (-1, 1):
        for i in range(14):
            z = z0 + 0.7 + i * (LH - 1.3) / 13
            sphere(f"Stud{k}", 0.034, (sx * (LW / 2 - 0.16), yf - 0.035, z), iron, seg=6, rings=3)
            k += 1
    for zz in (z0 + 0.95, z0 + LH - 0.95):
        _strap_hinge(f"Strap{zz:.1f}", -LW / 2, -0.5, yf - 0.04, zz, iron)
    # knocker, handle, keyhole and letter plate (brass)
    zk = z0 + 3.85
    cyl("KnockPlate", 0.15, 0.04, (0, yf - 0.045, zk), brass, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)
    sphere("KnockBoss", 0.075, (0, yf - 0.08, zk), brass, seg=10, rings=5, scale=(1, 0.6, 1))
    hoop("Knocker", (0, yf - 0.1, zk - 0.2), 0.17, "Y", brass, thick=0.024)
    xh = LW / 2 - 0.5
    box("Escutcheon", (0.17, 0.03, 0.46), (xh, yf - 0.035, z0 + 2.55), brass, bevel=0.01)
    box("Keyhole", (0.035, 0.01, 0.09), (xh, yf - 0.052, z0 + 2.45), K["hollow"], bevel=0.0, segments=1)
    hoop("HandleRing", (xh, yf - 0.09, z0 + 2.62), 0.11, "Y", brass, thick=0.02)
    box("LetterPlate", (0.62, 0.03, 0.16), (0, yf - 0.035, z0 + 1.75), brass, bevel=0.01)
    box("LetterSlot", (0.48, 0.01, 0.05), (0, yf - 0.052, z0 + 1.75), K["hollow"], bevel=0.0, segments=1)
    set_group("Main")
    # a wall lantern on a scrolled bracket to the right of the doorway
    lanterns = []
    xl, yl, zl, ls = 3.75, -1.0, 4.45, 1.5
    zarm = zl + 0.78 * ls
    box("LampPlate", (0.26, 0.06, 0.8), (xl, -0.03, zarm - 0.2), iron, bevel=0.012)
    tube("LampArm", [(xl, -0.03, zarm), (xl, yl, zarm)], 0.04, iron, square=True, poly=True)
    tube("LampScroll", [(xl, -0.03, zarm - 0.5), (xl, -0.32, zarm - 0.42), (xl, -0.66, zarm - 0.22), (xl, yl + 0.1, zarm - 0.03)], 0.03, iron,
         square=True)
    hoop("LampCurl", (xl, -0.2, zarm - 0.36), 0.08, "X", iron, thick=0.018)
    sphere("LampArmKnob", 0.06, (xl, yl - 0.06, zarm), brass, seg=8, rings=4)
    tube("LampHook", [(xl, yl, zarm), (xl, yl, zl + 0.68 * ls)], 0.016, iron, poly=True)
    _lantern("Lamp", Matrix.Translation((xl, yl, zl)) @ Matrix.Scale(ls, 4), M, lanterns, wax_mat())
    _lights(lanterns, M)
    # weathering: moss on the step and the label stops, cracks in a jamb stone and the step
    _moss("Moss", [(-2.85, -1.6, 0.5), (-2.4, -1.72, 0.5), (2.75, -1.65, 0.5), (-(hw_h + 0.3), yh, ZS - 0.06), (hw_h + 0.3, yh, ZS - 0.06),
                   (-2.6, -0.5, ZT + 0.02)], K["moss"], rnd, size=0.1)
    _crack("Crack", (-W - 0.2, -D - 0.005, ZT + 2.3), (0.3, 0, -1), (1, 0, 0), 0.75, rnd, K["hollow"])
    _crack("Crack3", (W + 0.3, -D - 0.005, ZT + 4.6), (-0.2, 0, -1), (1, 0, 0), 0.6, rnd, K["hollow"])
    _crack("Crack2", (-0.3, -1.81, 0.42), (1, 0, -0.2), (0, 0, 1), 0.9, rnd, K["hollow"])
    return _dims()


# ================================================================== town window
def _cat(prefix, x, y, z, mat):
    """A sitting cat's silhouette, flattened to fit between the glass and the room light."""
    sphere(f"{prefix}Body", 0.26, (x, y, z + 0.24), mat, seg=12, rings=6, scale=(1.0, 0.32, 0.95))
    sphere(f"{prefix}Chest", 0.16, (x - 0.12, y, z + 0.42), mat, seg=10, rings=5, scale=(1.0, 0.35, 1.2))
    sphere(f"{prefix}Head", 0.14, (x - 0.16, y, z + 0.66), mat, seg=12, rings=6, scale=(1.05, 0.4, 0.95))
    for sx in (-1, 1):
        cone(f"{prefix}Ear{sx}", 0.055, 0.0, 0.13, (x - 0.16 + sx * 0.08, y, z + 0.8), mat, verts=4, rot=(0, sx * 0.25, 0))
    tube(f"{prefix}Tail", [(x + 0.22, y, z + 0.06), (x + 0.38, y, z + 0.02), (x + 0.46, y, z + 0.2), (x + 0.4, y, z + 0.38)], 0.035, mat)


def town_window(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(1202)
    W, D = 1.4, 0.45
    # sill on two brackets
    for sx in (-1, 1):
        box(f"SillBracket{sx}", (0.34, 0.5, 0.36), (sx * 1.5, -0.25, 0.18), dk, bevel=0.03)
        box(f"SillBracketTip{sx}", (0.34, 0.2, 0.14), (sx * 1.5, -0.55, 0.29), dk, bevel=0.02)
    box("Sill", (3.9, 0.82, 0.3), (0, -0.41, 0.51), st, bevel=0.04)
    ZB = 0.66
    ZH = quoins("Jamb", W, ZB, [1.0, 0.8, 0.8, 1.0, 0.8, 0.6], D, st, long=0.62, short=0.42)
    # a flat arch of fanned voussoirs with a keystone
    n = 7
    for i in range(n):
        xb0, xb1 = -(W + 0.2) + 2 * (W + 0.2) * i / n, -(W + 0.2) + 2 * (W + 0.2) * (i + 1) / n
        xt0, xt1 = -(W + 0.55) + 2 * (W + 0.55) * i / n, -(W + 0.55) + 2 * (W + 0.55) * (i + 1) / n
        top = ZH + (0.95 if i == 3 else 0.72)
        if i == 3:
            xt0, xt1 = xt0 - 0.05, xt1 + 0.05
        poly = [(xb0 + 0.012, ZH), (xb1 - 0.012, ZH), (xt1 - 0.012, top), (xt0 + 0.012, top)]
        prism(f"Vous{i}", poly, -D / 2 - (0.06 if i == 3 else 0), D + (0.12 if i == 3 else 0), st, bevel=0.025)
    _foil("KeyFoil", 0, -D - 0.13, ZH + 0.5, 0.11, dk, lobes=4, thick=0.014)
    # the hood mould resting on the voussoirs (the keystone breaks through it), with short drops and label stops
    yh = -D - 0.06
    hx = W + 0.72
    box("Hood", (2 * hx + 0.2, D + 0.24, 0.2), (0, -(D + 0.24) / 2, ZH + 0.82), dk, bevel=0.035)
    box("HoodDrip", (2 * hx + 0.24, 0.1, 0.07), (0, -D - 0.2, ZH + 0.7), dk, bevel=0.02)
    for sx in (-1, 1):
        box(f"HoodDrop{sx}", (0.2, D + 0.24, 0.5), (sx * hx, -(D + 0.24) / 2, ZH + 0.47), dk, bevel=0.03)
        box(f"Label{sx}", (0.28, D + 0.3, 0.26), (sx * hx, -(D + 0.3) / 2, ZH + 0.12), dk, bevel=0.035)
        _foil(f"LabelFoil{sx}", sx * hx, -D - 0.32, ZH + 0.12, 0.08, st, lobes=4, thick=0.012)
    # black iron sashes
    yS = -0.3
    for sx in (-1, 1):
        box(f"FrameSide{sx}", (0.1, 0.12, ZH - ZB), (sx * (W - 0.05), yS, (ZB + ZH) / 2), iron, bevel=0.01)
    box("FrameTop", (2 * W, 0.12, 0.1), (0, yS, ZH - 0.05), iron, bevel=0.01)
    box("FrameBottom", (2 * W, 0.12, 0.1), (0, yS, ZB + 0.05), iron, bevel=0.01)
    zm = ZB + 2.5
    box("MeetingRail", (2 * W - 0.1, 0.14, 0.12), (0, yS - 0.02, zm), iron, bevel=0.01)
    for z0, z1 in ((ZB + 0.1, zm - 0.06), (zm + 0.06, ZH - 0.1)):
        for xx in (-W / 3, W / 3):
            tube(f"Muntin{z0:.1f}{xx:.1f}", [(xx, yS, z0), (xx, yS, z1)], 0.022, iron, square=True, poly=True)
        tube(f"Bar{z0:.1f}", [(-W + 0.1, yS, (z0 + z1) / 2), (W - 0.1, yS, (z0 + z1) / 2)], 0.022, iron, square=True, poly=True)
    box("SashLift", (0.18, 0.04, 0.05), (0, yS - 0.08, ZB + 0.3), brass, bevel=0.01)
    # the lit room behind: curtains, a pelmet and a cat on the inner sill, against the warm light
    yc = -0.15
    curtain("CurtainL", -W + 0.02, -0.3, ZH - 0.32, ZB + 1.9, ZB + 0.04, yc, K["velvet"], brass)
    curtain("CurtainR", W - 0.02, 0.3, ZH - 0.32, ZB + 1.9, ZB + 0.04, yc, K["velvet"], brass)
    box("Pelmet", (2 * W - 0.04, 0.12, 0.36), (0, yc - 0.03, ZH - 0.2), K["velvet"], bevel=0.02)
    tube("PelmetTrim", [(-W + 0.04 + i * (2 * W - 0.08) / 24, yc - 0.1, ZH - 0.37 - 0.035 * abs(math.sin(i / 24 * math.pi * 6))) for i in range(25)],
         0.016, brass, poly=True)
    _cat("Cat", 0.7, -0.2, ZB, K["soot"])
    # a little table lamp on the inner sill lights the room: an amber pool round it, dark toward the edges
    lx, ly = -0.5, -0.13
    lathe("LampBase", [(0, 0), (0.1, 0), (0.1, 0.03), (0.04, 0.06), (0.025, 0.4), (0.05, 0.43), (0, 0.43)], brass, seg=16, loc=(lx, -0.1, ZB))
    box("Room", (2 * W, 0.02, ZH - ZB), (0, -0.04, (ZB + ZH) / 2), room_mat("Room", (lx + 0.3, -0.04, ZB + 1.3), 4.2, (1.0, 0.66, 0.3), (0.2, 0.1, 0.045)),
        bevel=0.0, segments=1)
    set_group("Glass")
    box("Pane", (2 * W - 0.1, 0.02, ZH - ZB - 0.1), (0, yS + 0.03, (ZB + ZH) / 2), K["glass"], bevel=0.0, segments=1)
    set_group("Glow")
    cone("LampShade", 0.16, 0.08, 0.24, (lx, -0.1, ZB + 0.54), K["glow"], verts=14)
    flame("SconceFlame", (0.55, -0.1, ZH - 1.35), h=0.2)
    set_group("Main")
    tube("SconceArm", [(0.55, -0.05, ZH - 1.6), (0.55, -0.1, ZH - 1.45)], 0.014, brass, poly=True)
    cyl("SconceCup", 0.05, 0.08, (0.55, -0.1, ZH - 1.39), brass, verts=10, bevel=0.0)
    # louvred iron shutters in chipped oxblood enamel, folded back against the wall
    ox = K["enamel"]
    for sx in (-1, 1):
        xi, xo = sx * 2.08, sx * 3.48
        xc = (xi + xo) / 2
        ys = -0.08
        for xe, inward in ((xi, 1), (xo, -1)):
            box(f"ShStile{sx}{xe:.1f}", (0.12, 0.07, ZH - ZB), (xe + sx * inward * 0.06, ys, (ZB + ZH) / 2), ox, bevel=0.012)
        for zr in (ZB + 0.07, (ZB + ZH) / 2, ZH - 0.07):
            box(f"ShRail{sx}{zr:.1f}", (1.4, 0.07, 0.14), (xc, ys, zr), ox, bevel=0.012)
        for half in ((ZB + 0.14, (ZB + ZH) / 2 - 0.07), ((ZB + ZH) / 2 + 0.07, ZH - 0.14)):
            cnt = 12
            for i in range(cnt):
                z = half[0] + (half[1] - half[0]) * (i + 0.5) / cnt
                box(f"Louvre{sx}{z:.2f}", (1.16, 0.035, 0.29), (xc, ys - 0.01, z), ox, bevel=0.008, rot=(0.85, 0, 0), segments=1)
                for ex in (-0.55, 0.55):
                    sphere(f"LRivet{sx}{z:.2f}{ex}", 0.022, (xc + ex, ys - 0.045, z), iron, seg=6, rings=3)
            tube(f"TieBar{sx}{half[0]:.1f}", [(xc, ys - 0.06, half[0]), (xc, ys - 0.06, half[1])], 0.02, ox, square=True, poly=True)
        for zz in (ZB + 0.7, ZH - 0.7):
            _strap_hinge(f"ShStrap{sx}{zz:.1f}", xi, xi + sx * 0.75, ys - 0.05, zz, iron)
            cyl(f"Pintle{sx}{zz:.1f}", 0.035, 0.22, (sx * 2.02, -0.1, zz), iron, verts=8, bevel=0.0)
        tube(f"ShutterDog{sx}", [(xo + sx * 0.05, -0.02, ZB + 0.45), (xo + sx * 0.12, -0.12, ZB + 0.55), (xo + sx * 0.02, -0.16, ZB + 0.7),
                                  (xo - sx * 0.05, -0.13, ZB + 0.78)], 0.022, iron)
    # weathering
    _moss("Moss", [(-1.75, -0.7, 0.66), (1.8, -0.62, 0.66), (-0.4, -0.75, 0.66), (hx - 0.4, -0.5, ZH + 0.92), (-hx + 0.3, -0.45, ZH + 0.92)],
          K["moss"], rnd, size=0.09)
    _crack("Crack", (W + 0.15, -D - 0.005, ZB + 3.2), (0.25, 0, -1), (1, 0, 0), 0.7, rnd, K["hollow"])
    return _dims()


# ================================================================== bay window (oriel)
def _offset(plan, d):
    (ax, _), (bx, by), (cx, cy), (dx, _) = plan
    return [(ax - d, 0.0), (bx - d * 0.5, by - d), (cx + d * 0.5, cy - d), (dx + d, 0.0)]


def bay_window(M):
    K = kit(M)
    st, dk, iron, brass, lead = K["st"], K["dk"], K["iron"], K["brass"], K["lead"]
    rnd = random.Random(1203)
    plan = [(-2.8, 0.0), (-1.7, -1.5), (1.7, -1.5), (2.8, 0.0)]
    # the corbelled base: the bay's plan stepping in as it goes down, a moulding round every step, a grotesque
    layers = [(1.25, 1.62, 1.0), (0.9, 1.25, 0.78), (0.55, 0.9, 0.56), (0.18, 0.55, 0.34)]
    for i, (z0, z1, s) in enumerate(layers):
        poly = [(x * s, y * s) for x, y in plan]
        prism(f"Corbel{i}", poly, z0, z1 - z0, st if i % 2 == 0 else dk, plane="XY", bevel=0.03)
        op = _offset(poly, 0.03)
        tube(f"CorbelMould{i}", [(x, y, z1 - 0.04) for x, y in op], 0.04, dk, square=True, poly=True)
    lathe("Pendant", [(0, 0.0), (0.06, 0.02), (0.14, 0.1), (0.2, 0.18), (0, 0.18)], dk, seg=12, loc=(0, -0.3, 0))
    _grotesque("Grot", Matrix.Translation((0, -1.25, 1.02)), dk, K["hollow"])
    prism("Base", _offset(plan, 0.15), 1.62, 0.38, dk, plane="XY", bevel=0.04)
    # the three faces
    faces = list(zip(plan, plan[1:]))
    glass_jobs, glow_jobs = [], []
    for fi, (p, q) in enumerate(faces):
        p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
        e = (q - p)
        L = e.length
        e.normalize()
        nrm = Vector((e.y, -e.x, 0))
        th = math.atan2(nrm.x, -nrm.y)
        mid = (p + q) / 2
        mtx = Matrix.Translation(mid) @ Matrix.Rotation(th, 4, "Z")
        s = _mark()
        box(f"Apron{fi}", (L, 0.3, 0.8), (0, 0.15, 2.4), st, bevel=0.02)
        _panel(f"ApronPanel{fi}", 0, -0.012, 2.1, L * 0.72, 0.6, dk, thick=0.025)
        box(f"SillBand{fi}", (L + 0.1, 0.42, 0.15), (0, 0.1, 2.875), dk, bevel=0.02)
        lights = [(-L / 2 + 0.14, L / 2 - 0.14)] if L < 2.5 else [(-L / 2 + 0.14, -0.1), (0.1, L / 2 - 0.14)]
        if len(lights) == 2:
            box(f"Mullion{fi}", (0.2, 0.3, 3.05), (0, 0.1, 2.95 + 1.525), st, bevel=0.02)
        z0, z1 = 2.95, 6.0
        for li, (xa, xb) in enumerate(lights):
            tube(f"Frame{fi}{li}", [(xa, -0.02, z0), (xb, -0.02, z0), (xb, -0.02, z1), (xa, -0.02, z1)], 0.04, iron, closed=True, square=True, poly=True)
            tube(f"Transom{fi}{li}", [(xa, -0.02, 5.1), (xb, -0.02, 5.1)], 0.035, iron, square=True, poly=True)
            lattice(f"Came{fi}{li}_", xa, xb, z0, z1, 0.0, 0.34, lead)
        box(f"Lintel{fi}", (L + 0.1, 0.42, 0.5), (0, 0.1, 6.25), st, bevel=0.02)
        nf = max(2, int(L / 0.62))
        for k in range(nf):
            x = -L / 2 + (k + 0.5) * L / nf
            _foil(f"Frieze{fi}{k}", x, -0.12, 6.25, 0.13, dk, lobes=4, thick=0.016)
        _xform(s, mtx)
        glass_jobs.append((mtx, lights))
        glow_jobs.append((mtx, L))
    # corner colonnettes and wall pilasters
    for k, (x, y) in enumerate(plan[1:3]):
        cyl(f"Colonnette{k}", 0.15, 4.0, (x * 1.02, y - 0.06, 4.5), dk, verts=16, bevel=0.0)
        box(f"ColBase{k}", (0.38, 0.38, 0.22), (x * 1.02, y - 0.06, 2.11), dk, bevel=0.02)
        box(f"ColCap{k}", (0.38, 0.38, 0.22), (x * 1.02, y - 0.06, 6.39), dk, bevel=0.02)
    for sx in (-1, 1):
        box(f"WallPier{sx}", (0.4, 0.3, 4.5), (sx * 2.72, -0.15, 4.25), st, bevel=0.02)
    # cornice and canted lead roof
    prism("Cornice1", _offset(plan, 0.2), 6.5, 0.2, dk, plane="XY", bevel=0.03)
    prism("Cornice2", _offset(plan, 0.32), 6.7, 0.15, st, plane="XY", bevel=0.03)
    ea = [Vector((x, y, 6.85)) for x, y in _offset(plan, 0.32)]
    H1, H2 = Vector((-1.1, 0, 8.2)), Vector((1.1, 0, 8.2))
    sheet("Roof", [[ea[1], ea[2], H2, H1], [ea[0], ea[1], H1], [ea[2], ea[3], H2]], lead, 0.08)
    fn = (ea[2] - ea[1]).cross(H1 - ea[1]).normalized()
    if fn.z < 0:
        fn = -fn
    for a, b in ((ea[1], H1), (ea[2], H2)):
        tube(f"HipRoll{a.x:.1f}", [tuple(a + Vector((0, 0, 0.05))), tuple(b + Vector((0, 0, 0.05)))], 0.055, lead, poly=True)
    for k, x in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        a = Vector((x, ea[1].y, 6.85))
        b = Vector((x * 1.1 / 1.86, 0.0, 8.2))
        tube(f"Seam{k}", [tuple(a + fn * 0.05), tuple(b + fn * 0.05)], 0.022, lead, poly=True)
    tube("EaveRoll", [tuple(p + Vector((0, 0, 0.02))) for p in ea], 0.04, lead, poly=True)
    box("Flashing", (2.6, 0.12, 0.22), (0, -0.06, 8.25), lead, bevel=0.01)
    sphere("FinialBall", 0.1, (0, -0.16, 8.45), lead, seg=10, rings=5)
    _spike("FinialSpike", (0, -0.16, 8.68), 0.04, 0.3, lead, verts=6)
    # the leaded glass and the room light behind it
    set_group("Glass")
    for k, (mtx, lights) in enumerate(glass_jobs):
        s = _mark()
        for li, (xa, xb) in enumerate(lights):
            box(f"Pane{k}{li}", (xb - xa, 0.02, 3.05), ((xa + xb) / 2, 0.04, 4.475), K["glass"], bevel=0.0, segments=1)
        _xform(s, mtx)
    set_group("Main")
    lamp = (0.8, -0.7, 4.75)
    room = room_mat("Room", lamp, 4.4, (1.0, 0.66, 0.3), (0.2, 0.1, 0.045))
    # the room behind the bay: lit by the pendant and the sill candles
    box("RoomBack", (5.2, 0.02, 3.6), (0, -0.04, 4.5), room, bevel=0.0, segments=1)
    # a pendant lamp hanging in the bay
    tube("LampChain", [(lamp[0], lamp[1], 6.45), (lamp[0], lamp[1], lamp[2] + 0.28)], 0.012, iron, poly=True)
    cyl("LampCap", 0.06, 0.06, (lamp[0], lamp[1], lamp[2] + 0.26), brass, verts=10, bevel=0.0)
    set_group("Glow")
    cone("LampShade", 0.34, 0.1, 0.32, (lamp[0], lamp[1], lamp[2] + 0.1), K["glow"], verts=16)
    for sx in (-1, 1):
        flame(f"SillFlame{sx}", (sx * 1.2, -1.05, 3.25), h=0.16)
    set_group("Main")
    for sx in (-1, 1):
        cyl(f"SillCandle{sx}", 0.045, 0.28, (sx * 1.2, -1.05, 3.1), wax_mat(), verts=10, bevel=0.0)
    # dark curtains drawn at the sides of the front window
    for sx in (-1, 1):
        curtain(f"Curtain{sx}", sx * 1.5, sx * 0.85, 5.85, 4.1, 2.98, -1.2, K["velvet"], brass)
    _moss("Moss", [(-1.4, -1.5, 1.62), (1.2, -1.52, 1.62), (0.3, -1.2, 1.25), (-0.8, -0.9, 0.9), (1.0, -1.63, 6.85)], K["moss"], rnd, size=0.1)
    return _dims()


# ================================================================== chimney
def chimney(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    br = brick_mat("Brick")
    rnd = random.Random(1204)
    box("Base", (2.6, 1.8, 1.0), (0, 0, 0.5), st, bevel=0.04)
    frustum("Flashing", (0, 0), 2.9, 2.1, 0.0, 2.62, 1.82, 0.16, K["lead"], bevel=0.0)
    box("BaseCap", (2.7, 1.9, 0.18), (0, 0, 1.06), dk, bevel=0.03)
    box("Shaft", (2.3, 1.5, 6.2), (0, 0, 1.15 + 3.1), br, bevel=0.02, segments=1)
    box("String", (2.46, 1.66, 0.24), (0, 0, 4.2), st, bevel=0.03)
    # iron band with S-shaped tie plates
    z = 6.15
    for sy in (-1, 1):
        box(f"BandY{sy}", (2.36, 0.04, 0.12), (0, sy * 0.77, z), iron, bevel=0.008)
        tube(f"TieS{sy}", [(-0.2, sy * 0.8, z + 0.3), (-0.08, sy * 0.81, z + 0.32), (0.0, sy * 0.81, z), (0.08, sy * 0.81, z - 0.32), (0.2, sy * 0.8, z - 0.3)],
             0.03, iron)
        sphere(f"TieBolt{sy}", 0.05, (0, sy * 0.82, z), iron, seg=8, rings=4)
    for sx in (-1, 1):
        box(f"BandX{sx}", (0.04, 1.56, 0.12), (sx * 1.17, 0, z), iron, bevel=0.008)
    # a dentil course of projecting bricks under the cap
    for sy in (-1, 1):
        for i in range(9):
            box(f"DentY{sy}{i}", (0.16, 0.1, 0.12), (-1.0 + i * 0.25, sy * 0.79, 7.18), br, bevel=0.01, segments=1)
    for sx in (-1, 1):
        for i in range(6):
            box(f"DentX{sx}{i}", (0.1, 0.16, 0.12), (sx * 1.19, -0.62 + i * 0.25, 7.18), br, bevel=0.01, segments=1)
    # stone quoins up the corners of the shaft
    for sx in (-1, 1):
        for sy in (-1, 1):
            i = 0
            for za, zb in ((1.16, 4.06), (4.34, 7.1)):
                nq = round((zb - za) / 0.46)
                hq = (zb - za) / nq
                for j in range(nq):
                    wl, ws = (0.46, 0.3) if (i + j) % 2 == 0 else (0.3, 0.46)
                    box(f"Quoin{sx}{sy}{i}{j}", (wl, ws, hq - 0.02), (sx * (1.15 - wl / 2 + 0.03), sy * (0.75 - ws / 2 + 0.03), za + (j + 0.5) * hq), st,
                        bevel=0.02, segments=1)
                i += 1
    # the oversailing corbelled cap and the flaunching round the pots
    box("Cap1", (2.5, 1.7, 0.25), (0, 0, 7.475), br, bevel=0.02, segments=1)
    box("Cap2", (2.72, 1.92, 0.25), (0, 0, 7.725), st, bevel=0.03)
    box("Cap3", (2.88, 2.06, 0.22), (0, 0, 7.96), dk, bevel=0.04)
    frustum("Flaunch", (0, 0), 2.6, 1.6, 8.07, 2.0, 0.7, 8.32, K["stain"], bevel=0.02)
    # three clay pots: plain, fluted (the tall one, where the smoke comes out), and one under an iron cowl
    clay = material("ChimneyPot", "NH_Limestone", tint=(0.14, 0.062, 0.042), scale=0.4, wear=0.3, dirt=1.0)
    tops = []
    for k, (x, h, fl) in enumerate(((-0.78, 1.15, None), (0.0, 1.55, (12, 0.08)), (0.78, 1.0, None))):
        z0 = 8.2
        prof = [(0.3, 0.0), (0.27, 0.12), (0.22, h * 0.7), (0.24, h - 0.12), (0.29, h - 0.06), (0.29, h), (0.2, h), (0.18, h - 0.35), (0, h - 0.35)]
        lathe(f"Pot{k}", prof, clay, seg=20, loc=(x, 0, z0), flute=fl)
        cyl(f"PotSoot{k}", 0.19, 0.02, (x, 0, z0 + h - 0.34), K["soot"], verts=16, bevel=0.0)
        tops.append((x, z0 + h))
    x, zt = tops[2]
    for k in range(3):
        a = k / 3 * 2 * math.pi + 0.5
        tube(f"CowlLeg{k}", [(x + math.cos(a) * 0.24, math.sin(a) * 0.24, zt - 0.05), (x + math.cos(a) * 0.2, math.sin(a) * 0.2, zt + 0.32)], 0.014, iron,
             poly=True)
    cone("Cowl", 0.36, 0.04, 0.26, (x, 0, zt + 0.42), iron, verts=16)
    sphere("CowlKnob", 0.04, (x, 0, zt + 0.57), iron, seg=8, rings=4)
    # soot and moss
    _moss("Moss", [(-1.15, -0.83, 4.32), (0.9, -0.83, 4.32), (1.3, 0.9, 1.15), (-1.2, -0.9, 1.15), (1.3, -0.95, 8.07), (-1.3, 0.98, 8.07)],
          K["moss"], rnd, size=0.1)
    _crack("Crack", (0.6, -0.756, 3.6), (0.2, 0, -1), (1, 0, 0), 1.1, rnd, K["hollow"])
    return _dims()


# ================================================================== iron balcony
def iron_balcony(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(1205)
    HW, DP = 4.0, 1.7
    zs0, zs1 = 1.5, 1.82
    box("Slab", (2 * HW, DP, zs1 - zs0), (0, -DP / 2, (zs0 + zs1) / 2), st, bevel=0.04)
    box("SlabNose", (2 * HW + 0.08, 0.12, 0.1), (0, -DP + 0.02, zs0 + 0.06), dk, bevel=0.03)
    for sx in (-1, 1):
        box(f"SlabNoseSide{sx}", (0.12, DP, 0.1), (sx * (HW - 0.02), -DP / 2, zs0 + 0.06), dk, bevel=0.03)
    # four scrolled consoles
    for k, x in enumerate((-3.3, -1.1, 1.1, 3.3)):
        box(f"ConsolePlate{k}", (0.22, 0.05, 0.5), (x, -0.025, 0.25), iron, bevel=0.01)
        bracket_scroll(f"Console{k}", x, -0.05, -1.45, zs0 - 0.04, 0.0, iron, r=0.04)
    # the railing: posts, rails, a ring frieze, bars and quatrefoil medallions
    zb, zm, zt = zs1 + 0.18, zs1 + 0.62, zs1 + 2.95
    yF = -DP + 0.14
    corners = [(-HW + 0.12, -0.12), (-HW + 0.12, yF), (HW - 0.12, yF), (HW - 0.12, -0.12)]
    for a, b in zip(corners, corners[1:]):
        for zr, r in ((zb, 0.035), (zm, 0.03)):
            tube(f"Rail{a[0]:.0f}{a[1]:.1f}{zr:.1f}", [(a[0], a[1], zr), (b[0], b[1], zr)], r, iron, square=True, poly=True)
        tube(f"TopRail{a[0]:.0f}{a[1]:.1f}", [(a[0], a[1], zt), (b[0], b[1], zt)], 0.06, iron, square=True, poly=True)
        tube(f"Handrail{a[0]:.0f}{a[1]:.1f}", [(a[0], a[1], zt + 0.07), (b[0], b[1], zt + 0.07)], 0.045, iron, poly=True)
        va, vb = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
        L = (vb - va).length
        # ring frieze between the bottom and middle rails
        nr = int(L / 0.22)
        for i in range(nr):
            p = va + (vb - va) * ((i + 0.5) / nr)
            axis = "Y" if abs(a[1] - b[1]) < 1e-6 else "X"
            iring(f"Ring{a[0]:.0f}{a[1]:.1f}{i}", (p.x, p.y, (zb + zm) / 2), 0.095, axis, iron, 0.014, 10)
        # bars
        nb = int(L / 0.2)
        for i in range(1, nb):
            p = va + (vb - va) * (i / nb)
            tube(f"Bar{a[0]:.0f}{a[1]:.1f}{i}", [(p.x, p.y, zm), (p.x, p.y, zt)], 0.018, iron, square=True, poly=True)
        # a quatrefoil medallion in each 2-stud panel, with a brass boss
        npnl = max(1, round(L / 2.0))
        for i in range(npnl):
            p = va + (vb - va) * ((i + 0.5) / npnl)
            axis = "Y" if abs(a[1] - b[1]) < 1e-6 else "X"
            off = Vector((0, -0.03, 0)) if axis == "Y" else Vector((-0.03 if a[0] < 0 else 0.03, 0, 0))
            c = p + off
            zc = (zm + zt) / 2
            iring(f"Medal{a[0]:.0f}{a[1]:.1f}{i}", (c.x, c.y, zc), 0.48, axis, iron, 0.026, 28)
            for j in range(4):
                ang = j * math.pi / 2
                dx, dz = math.cos(ang) * 0.24, math.sin(ang) * 0.24
                cc = (c.x + (dx if axis == "Y" else 0), c.y + (0 if axis == "Y" else dx), zc + dz)
                iring(f"Lobe{a[0]:.0f}{a[1]:.1f}{i}{j}", cc, 0.2, axis, iron, 0.018, 14)
            sphere(f"Boss{a[0]:.0f}{a[1]:.1f}{i}", 0.07, (c.x + off.x, c.y + off.y, zc), brass, seg=10, rings=5)
    # newel posts with spear finials at the front corners and along the front
    for k, (x, y) in enumerate([(-HW + 0.12, yF), (-HW / 2, yF), (0.0, yF), (HW / 2, yF), (HW - 0.12, yF), (-HW + 0.12, -0.12), (HW - 0.12, -0.12)]):
        box(f"Post{k}", (0.12, 0.12, zt - zs1 + 0.1), (x, y, (zs1 + zt) / 2), iron, bevel=0.012)
        sphere(f"PostKnob{k}", 0.07, (x, y, zt + 0.17), brass, seg=10, rings=5)
        _spike(f"PostSpear{k}", (x, y, zt + 0.36), 0.05, 0.26, iron, verts=4, rot=(0, 0, math.pi / 4))
        box(f"PostFoot{k}", (0.2, 0.2, 0.08), (x, y, zs1 + 0.04), iron, bevel=0.01)
    _moss("Moss", [(-3.7, -0.15, zs1), (3.6, -0.2, zs1), (-1.0, -0.12, zs1)], K["moss"], rnd, size=0.09)
    return _dims()


# ================================================================== shop awning
def shop_awning(M):
    K = kit(M)
    iron, brass = K["iron"], K["brass"]
    red = material("CanvasRed", "NH_Leather", tint=(0.3, 0.035, 0.045), scale=4.0, normal=0.25, rough_add=0.45, wear=0.05, dirt=0.7)
    blk = material("CanvasBlack", "NH_Leather", tint=(0.05, 0.045, 0.05), scale=4.0, normal=0.25, rough_add=0.45, wear=0.05, dirt=0.6)
    HW, DP = 4.0, 2.5
    zw, zf, zv = 2.15, 0.62, 0.0          # wall rail, front bar, valance hem
    ribs = [-4.0, -2.0, 0.0, 2.0, 4.0]
    n = 16
    sw = 2 * HW / n

    def canvas_z(x, t):
        frac = ((x + HW) % 2.0) / 2.0
        return zw - (zw - zf) * t - 0.12 * math.sin(math.pi * t) - 0.06 * math.sin(math.pi * frac) * math.sin(math.pi * t)
    for i in range(n):
        xa, xb = -HW + i * sw, -HW + (i + 1) * sw
        rows = []
        for j in range(13):
            t = j / 12
            rows.append([Vector((xa + (xb - xa) * c / 3, -DP * t, canvas_z(xa + (xb - xa) * c / 3, t))) for c in range(4)])
        _mesh(f"Stripe{i}", rows, red if i % 2 == 0 else blk, 0.02)
    # iron frame: a wall rail with rosettes, ribs under the canvas, the front bar and folding arms
    box("WallRail", (2 * HW + 0.2, 0.1, 0.16), (0, -0.05, zw + 0.02), iron, bevel=0.01)
    cyl("Roller", 0.13, 2 * HW + 0.1, (0, -0.2, zw + 0.06), iron, rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    for sx in (-1, 1):
        cyl(f"RollerCap{sx}", 0.16, 0.06, (sx * (HW + 0.08), -0.2, zw + 0.06), brass, rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    for k, x in enumerate(ribs):
        tube(f"Rib{k}", [(x, -DP * t, canvas_z(x, t) - 0.04) for t in [j / 8 for j in range(9)]], 0.03, iron, poly=True)
        cyl(f"Rosette{k}", 0.08, 0.04, (x, -0.11, zw + 0.02), brass, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.008)
    tube("FrontBar", [(-HW - 0.12, -DP, zf), (HW + 0.12, -DP, zf)], 0.05, iron, poly=True)
    for sx in (-1, 1):
        sphere(f"BarKnob{sx}", 0.08, (sx * (HW + 0.18), -DP, zf), brass, seg=10, rings=5)
        x = sx * HW
        box(f"ArmPlate{sx}", (0.18, 0.05, 0.42), (x, -0.025, 0.42), iron, bevel=0.01)
        tube(f"Arm{sx}", [(x, -0.05, 0.42), (x, -DP + 0.05, zf - 0.02)], 0.032, iron, square=True, poly=True)
        tube(f"ArmScroll{sx}", [(x, -0.05, 0.72), (x, -0.4, 0.75), (x, -0.62, 0.62), (x, -0.55, 0.5)], 0.022, iron)
        hoop(f"ArmKnuckle{sx}", (x, -DP / 2, (0.42 + zf) / 2 + 0.0), 0.06, "X", iron, thick=0.02)
    # the scalloped valance (Cloth: it sways from the front bar)
    set_group("Cloth", hinge=(0, -DP, zf), swing=1)
    for i in range(n):
        xa, xb = -HW + i * sw, -HW + (i + 1) * sw
        rows = []
        for j in range(5):
            t = j / 4
            row = []
            for c in range(7):
                u = c / 6
                x = xa + (xb - xa) * u
                bottom = zv + 0.16 * (1 - math.sin(math.pi * u))
                z = zf - (zf - bottom) * t
                row.append(Vector((x, -DP - 0.03 - 0.015 * math.sin(math.pi * t), z)))
            rows.append(row)
        _mesh(f"Valance{i}", rows, red if i % 2 == 0 else blk, 0.02)
        cone(f"Tassel{i}", 0.035, 0.012, 0.12, (xa, -DP - 0.05, zv + 0.12), brass, verts=6, rot=(math.pi, 0, 0))
    cone("TasselEnd", 0.035, 0.012, 0.12, (HW, -DP - 0.05, zv + 0.12), brass, verts=6, rot=(math.pi, 0, 0))
    tube("ValanceTrim", [(-HW, -DP - 0.06, zf - 0.08), (HW, -DP - 0.06, zf - 0.08)], 0.018, brass, poly=True)
    set_group("Main")
    return _dims()


# ================================================================== dormer
def dormer(M):
    K = kit(M)
    st, dk, iron, slate, lead = K["st"], K["dk"], K["iron"], K["slate"], K["lead"]
    rnd = random.Random(1207)
    # it sits on a 45-degree roof: the roof plane is z = y + 2.6 (front-bottom edge at y -2, z 0.6)
    YF, ZF = -2.0, 0.6
    HW = 2.25
    ZE, ZR = 4.4, 6.0                      # eaves and ridge

    def roof_y(z):
        return z - 2.6
    # the lead apron draped over the roof in front
    sheet("Apron", [[(-HW - 0.15, YF - 0.05, ZF), (HW + 0.15, YF - 0.05, ZF), (HW + 0.15, YF - 0.65, 0.0), (-HW - 0.15, YF - 0.65, 0.0)]], lead, 0.04)
    tube("ApronRoll", [(-HW - 0.15, YF - 0.65, 0.02), (HW + 0.15, YF - 0.65, 0.02)], 0.03, lead, poly=True)
    # the stone front: piers, a sill, a pointed window head, the gable with coping, kneelers and a pinnacle
    WX, WZ0, WZS, WZA = 1.05, ZF + 0.75, ZF + 2.5, ZF + 3.3
    for sx in (-1, 1):
        box(f"Pier{sx}", (HW - WX, 0.4, ZE - ZF), (sx * (HW + WX) / 2, YF + 0.2, (ZF + ZE) / 2), st, bevel=0.03)
    box("SillWall", (2 * WX, 0.4, WZ0 - ZF), (0, YF + 0.2, (ZF + WZ0) / 2), st, bevel=0.02)
    box("Sill", (2 * WX + 0.4, 0.55, 0.14), (0, YF + 0.1, WZ0 - 0.04), dk, bevel=0.025)
    head = [(-WX, ZE)] + [(x, z) for x, z in _pointed(WX, WZS, WZA, n=10)] + [(WX, ZE)]
    head = [(-WX, ZE), (-WX, WZS)] + [(x, z) for x, z in _pointed(WX, WZS, WZA, n=10)][1:-1] + [(WX, WZS), (WX, ZE)]
    relief("Head", head, YF + 0.2, 0.4, st)
    tube("Reveal", [(-WX, YF - 0.01, WZ0)] + [(x, YF - 0.01, z) for x, z in _pointed(WX, WZS, WZA, n=10)] + [(WX, YF - 0.01, WZ0)], 0.05, dk,
         square=True, poly=True)
    _gable("Gable", 0, YF + 0.2, HW + 0.05, ZE, ZR + 0.15, 0.4, st, edge_mat=dk, edge=0.12)
    _foil("Vent", 0, YF - 0.02, ZE + 0.75, 0.22, dk, lobes=3, thick=0.03)
    cyl("VentHole", 0.17, 0.02, (0, YF - 0.005, ZE + 0.72), K["hollow"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.0)
    for sx in (-1, 1):
        box(f"Kneeler{sx}", (0.5, 0.55, 0.36), (sx * (HW + 0.05), YF + 0.2, ZE + 0.1), dk, bevel=0.03)
    _spirelet("Pinnacle", 0, YF + 0.2, ZR + 0.1, 1.25, 0.32, dk, crockets=2)
    # corner quoins and a string course at the eaves
    nq = 7
    hq = (ZE - ZF) / nq
    for sx in (-1, 1):
        for j in range(nq):
            wl = 0.5 if j % 2 == 0 else 0.34
            box(f"Quoin{sx}{j}", (wl, 0.46, hq - 0.02), (sx * (HW - wl / 2 + 0.03), YF + 0.2, ZF + (j + 0.5) * hq), dk, bevel=0.025, segments=1)
    box("String", (2 * HW + 0.16, 0.5, 0.14), (0, YF + 0.2, ZE - 0.05), dk, bevel=0.03)
    # the casement: iron frame, mullion and leaded panes
    arch = [(-WX + 0.06, YF + 0.12, WZ0)] + [(x * 0.95, YF + 0.12, z - 0.03) for x, z in _pointed(WX, WZS, WZA, n=10)] + [(WX - 0.06, YF + 0.12, WZ0)]
    tube("Casement", arch, 0.04, iron, closed=True, square=True, poly=True)
    tube("CaseMullion", [(0, YF + 0.12, WZ0), (0, YF + 0.12, WZA - 0.05)], 0.035, iron, square=True, poly=True)
    tube("CaseTransom", [(-WX + 0.06, YF + 0.12, WZS), (WX - 0.06, YF + 0.12, WZS)], 0.03, iron, square=True, poly=True)
    lattice("Came", -WX + 0.06, WX - 0.06, WZ0, WZS - 0.03, YF + 0.14, 0.32, lead)
    # slate-hung cheeks: courses of overlapping slates stepping up the roof slope
    for sx in (-1, 1):
        x = sx * (HW - 0.02)
        z = ZF + 0.06
        k = 0
        while z < ZE - 0.1:
            y1 = roof_y(z)
            span = y1 - (YF + 0.4)
            nt_ = max(1, int(span / 0.42))
            for j in range(nt_):
                ya = YF + 0.4 + span * j / nt_ + (0.1 if k % 2 and j == 0 and span > 0.6 else 0.0)
                yb = YF + 0.4 + span * (j + 1) / nt_ - 0.015
                if yb - ya > 0.08:
                    box(f"Cheek{sx}{k}_{j}", (0.035, yb - ya, 0.36), (x + sx * 0.02, (ya + yb) / 2, z + 0.16), rnd.choice(K["slates"]), bevel=0.0,
                        segments=1, rot=(0.0, sx * 0.07, 0.0))
            z += 0.26
            k += 1
        # the cheek's solid backing (a triangle in the YZ plane)
        prism(f"CheekCore{sx}", [(YF + 0.4, ZF), (roof_y(ZE), ZE), (YF + 0.4, ZE)], sx * (HW - 0.12), 0.16, dk, plane="YZ")
    # the slate roof: two slopes from the ridge to the eaves, running back until they meet the main roof
    yb_e, yb_r = roof_y(ZE), roof_y(ZR)
    for sx in (-1, 1):
        a, b = (sx * (HW + 0.25), YF - 0.05, ZE - 0.12), (0.0, YF - 0.05, ZR)
        c, d = (0.0, yb_r, ZR), (sx * (HW + 0.25), yb_e, ZE - 0.12)
        sheet(f"Roof{sx}", [[a, b, c, d]], slate, 0.08)
        # overlapping courses of individual slates, staggered, each tipped up a little at its tail
        va, vb = Vector(a), Vector(b)
        slope = vb - va
        ls = Vector((slope.x, 0, slope.z)).length
        ang = math.atan2(slope.z, abs(slope.x))
        nrm = Vector((sx * math.sin(ang), 0, math.cos(ang)))
        rows = 9
        for r in range(rows):
            t0, t1 = r / rows, min(1.0, (r + 1.45) / rows)
            tm = (t0 + t1) / 2
            ymax = yb_e + (yb_r - yb_e) * tm - 0.05
            y = YF - 0.05 + (0.24 if r % 2 else 0.0)
            j = 0
            while y < ymax - 0.1:
                y2 = min(y + 0.46, ymax)
                ctr = va + slope * tm + nrm * (0.06 + 0.012 * (r % 2))
                box(f"Slate{sx}{r}_{j}", ((t1 - t0) * ls, y2 - y - 0.025, 0.03), (ctr.x, (y + y2) / 2, ctr.z), rnd.choice(K["slates"]), bevel=0.0,
                    segments=1, rot=(0, sx * (ang + 0.035), 0))
                y = y2
                j += 1
        # lead flashing down the valley where the dormer roof meets the main roof, and along the cheek's foot
        tube(f"Valley{sx}", [(d[0], d[1] + 0.05, d[2] + 0.02), (0.0, c[1] + 0.05, c[2] + 0.02)], 0.07, lead, poly=True)
        tube(f"Soaker{sx}", [(sx * (HW + 0.02), YF + 0.4, ZF + 0.02), (sx * (HW + 0.02), roof_y(ZE), ZE + 0.02)], 0.06, lead, poly=True)
    tube("Ridge", [(0, YF - 0.08, ZR + 0.06), (0, yb_r, ZR + 0.06)], 0.1, lead, poly=True)
    nc = 9
    for k in range(nc):
        y = YF + 0.25 + (yb_r - YF - 0.6) * k / (nc - 1)
        tube(f"Crest{k}", [(0, y, ZR + 0.14), (0, y, ZR + 0.42)], 0.016, iron, square=True, poly=True)
        _spike(f"CrestTip{k}", (0, y, ZR + 0.48), 0.04, 0.14, iron, verts=4, rot=(0, 0, math.pi / 4))
        if k < nc - 1:
            y2 = YF + 0.25 + (yb_r - YF - 0.6) * (k + 0.5) / (nc - 1)
            hoop(f"CrestRing{k}", (0, y2, ZR + 0.3), 0.08, "X", iron, thick=0.012)
    tube("CrestRail", [(0, YF + 0.25, ZR + 0.22), (0, yb_r - 0.35, ZR + 0.22)], 0.014, iron, square=True, poly=True)
    set_group("Glass")
    pane = [(-WX + 0.06, WZ0)] + [(x * 0.95, z - 0.03) for x, z in _pointed(WX, WZS, WZA, n=10)] + [(WX - 0.06, WZ0)]
    relief("Pane", pane, YF + 0.17, 0.02, K["glass"])
    set_group("Main")
    # a dim attic: one candle on the inner sill, its glow fading into the dark
    cx_, cy_ = 0.5, YF + 0.42
    cyl("Candle", 0.045, 0.32, (cx_, cy_, WZ0 + 0.16), wax_mat(), verts=10, bevel=0.0)
    cyl("CandleDish", 0.1, 0.03, (cx_, cy_, WZ0 + 0.015), K["brass"], verts=12, bevel=0.0)
    box("Inside", (2 * WX + 0.1, 0.05, ZE - ZF), (0, YF + 0.8, (ZF + ZE) / 2), room_mat("Attic", (cx_, YF + 0.8, WZ0 + 0.5), 2.4, (0.7, 0.42, 0.17),
        (0.06, 0.032, 0.018)), bevel=0.0, segments=1)
    set_group("Glow")
    flame("CandleFlame", (cx_, cy_, WZ0 + 0.32), h=0.13)
    set_group("Main")
    _moss("Moss", [(-HW + 0.2, YF - 0.3, 0.32), (HW - 0.4, YF - 0.35, 0.3), (-WX - 0.1, YF - 0.05, WZ0 + 0.04), (HW + 0.05, YF - 0.05, ZE + 0.3)],
          K["moss"], rnd, size=0.1)
    return _dims()


# ================================================================== drainpipe
def drainpipe(M):
    K = kit(M)
    iron, dk = K["iron"], K["dk"]
    rnd = random.Random(1208)
    Y, R = -0.4, 0.17
    # the hopper head with a cast shield, and a raven on its rim
    frustum("HopperFunnel", (0, -0.42), 0.36, 0.36, 10.7, 1.1, 0.72, 11.3, iron, bevel=0.01)
    box("Hopper", (1.12, 0.74, 0.62), (0, -0.42, 11.6), iron, bevel=0.015)
    box("HopperRim", (1.24, 0.84, 0.09), (0, -0.42, 11.95), iron, bevel=0.015)
    for sx in (-1, 1):
        box(f"HopperEar{sx}", (0.16, 0.3, 0.22), (sx * 0.66, -0.15, 11.45), iron, bevel=0.01)
    shield = [(-0.24, 11.82), (0.24, 11.82), (0.24, 11.55), (0.15, 11.38), (0.0, 11.3), (-0.15, 11.38), (-0.24, 11.55)]
    relief("Shield", shield, -0.8, 0.04, iron, bevel=0.008)
    _foil("ShieldFoil", 0, -0.83, 11.57, 0.09, K["brass"], lobes=4, thick=0.012)
    box("Outlet", (0.5, 0.06, 0.3), (0, -0.03, 11.7), iron, bevel=0.01)
    raven("Raven", (-0.3, -0.62, 12.0), -math.pi / 2 + 0.4, 1.7, K["soot"], K["brass"])
    # the downpipe, its socket collars and wall ears
    cyl("Pipe", R, 10.7 - 1.0, (0, Y, 1.0 + (10.7 - 1.0) / 2), iron, verts=16, bevel=0.0)
    for k, z in enumerate((2.0, 4.0, 6.0, 8.0, 10.0)):
        cyl(f"Collar{k}", R + 0.04, 0.24, (0, Y, z), iron, verts=16, bevel=0.01)
        for sx in (-1, 1):
            box(f"Lug{k}{sx}", (0.1, 0.3, 0.18), (sx * 0.2, Y + 0.15, z), iron, bevel=0.01)
            cyl(f"Nail{k}{sx}", 0.035, 0.05, (sx * 0.2, -0.02, z), iron, rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)
    # the shoe throwing the water forward onto a gully grate
    tube("Shoe", [(0, Y, 1.05), (0, Y, 0.62), (0, Y - 0.12, 0.38), (0, Y - 0.45, 0.24)], R, iron, res=6)
    cone("ShoeMouth", R * 1.05, R * 1.4, 0.14, (0, Y - 0.52, 0.22), iron, verts=16, rot=(math.pi / 2, 0, 0))
    box("Gully", (0.8, 0.8, 0.06), (0, -0.85, 0.03), iron, bevel=0.01)
    for k in range(5):
        box(f"GullyBar{k}", (0.06, 0.72, 0.04), (-0.28 + k * 0.14, -0.85, 0.07), iron, bevel=0.005, segments=1)
    box("GullyDark", (0.68, 0.68, 0.01), (0, -0.85, 0.065), K["hollow"], bevel=0.0, segments=1)
    _moss("Moss", [(0.3, -0.5, 0.06), (-0.35, -1.1, 0.07), (0.38, -1.15, 0.07)], K["moss"], rnd, size=0.08)
    _moss("HopperMoss", [(0.4, -0.25, 12.0), (-0.45, -0.6, 12.0)], K["moss"], rnd, size=0.07)
    return _dims()


# ================================================================== stone stoop
def stone_stoop(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(1209)
    HW, CW = 2.2, 0.55
    ZL, YL = 2.0, -1.4
    # the landing and three steps with nosings
    box("Landing", (2 * HW, -YL, ZL), (0, YL / 2, ZL / 2), K["worn"], bevel=0.04)
    box("LandingNose", (2 * HW, 0.1, 0.1), (0, YL - 0.02, ZL - 0.06), dk, bevel=0.035)
    for k in range(1, 4):
        top = ZL - 0.5 * k
        y0, y1 = YL - 0.9 * k, YL - 0.9 * (k - 1)
        box(f"Step{k}", (2 * HW, y1 - y0, top), (0, (y0 + y1) / 2, top / 2), K["worn"], bevel=0.04)
        box(f"Nose{k}", (2 * HW, 0.1, 0.1), (0, y0 - 0.02, top - 0.06), dk, bevel=0.035)
    YB = YL - 2.7
    # cheek walls with sloped coping and newel piers at the foot
    for sx in (-1, 1):
        x = sx * (HW + CW / 2)
        prism(f"Cheek{sx}", [(0.0, 0.0), (0.0, ZL + 0.5), (YL, ZL + 0.5), (YB + 0.7, 0.95), (YB + 0.7, 0.0)], x, CW, st, plane="YZ", bevel=0.03)
        prism(f"Coping{sx}", [(0.05, ZL + 0.45), (0.05, ZL + 0.68), (YL - 0.04, ZL + 0.68), (YB + 0.66, 1.15), (YB + 0.66, 0.92), (YL - 0.04, ZL + 0.45)],
              x, CW + 0.12, dk, plane="YZ", bevel=0.02)
        box(f"Newel{sx}", (CW + 0.2, 0.75, 1.5), (x, YB + 0.33, 0.75), st, bevel=0.04)
        box(f"NewelCap{sx}", (CW + 0.34, 0.9, 0.18), (x, YB + 0.33, 1.59), dk, bevel=0.03)
        _foil(f"NewelFoil{sx}", x, YB - 0.06, 0.85, 0.16, dk, lobes=4, thick=0.02)
        # iron handrail: balusters up the coping, a rail following the slope and a scroll at the foot
        zc0, zc1 = 1.68, ZL + 0.68
        RH = 1.55                       # rail height above the coping

        def slope(y):
            return 1.15 + (zc1 - 1.15) * (y - (YB + 0.66)) / (YL - (YB + 0.66))

        def cz(y):
            return zc1 if y >= YL else slope(y)
        yn = YB + 0.33
        zr0 = slope(yn) + RH
        box(f"NewelPost{sx}", (0.13, 0.13, zr0 + 0.25 - zc0), (x, yn, (zc0 + zr0 + 0.25) / 2), iron, bevel=0.012)
        sphere(f"NewelBall{sx}", 0.1, (x, yn, zr0 + 0.34), brass, seg=12, rings=6)
        ys = [YB + 0.9 + i * 0.42 for i in range(int((-0.25 - (YB + 0.9)) / 0.42) + 1)]
        for i, y in enumerate(ys):
            tube(f"Baluster{sx}{i}", [(x, y, cz(y)), (x, y, cz(y) + RH)], 0.02, iron, square=True, poly=True)
            if i % 2 == 0:
                iring(f"BalRing{sx}{i}", (x, y, cz(y) + 0.34), 0.07, "X", iron, 0.012, 10)
        rail = [(x, yn, zr0)] + [(x, y, cz(y) + RH) for y in ys] + [(x, -0.12, zc1 + RH)]
        tube(f"Handrail{sx}", rail, 0.045, iron, poly=True)
        tube(f"Volute{sx}", [(x, yn, zr0 + 0.12), (x, yn - 0.2, zr0 + 0.05), (x, yn - 0.25, zr0 - 0.12), (x, yn - 0.08, zr0 - 0.2)], 0.03, iron)
        box(f"RailWallPlate{sx}", (0.16, 0.04, 0.3), (x, -0.02, zc1 + RH), iron, bevel=0.008)
    # a boot scraper on the landing by the wall
    xs = 1.45
    box("ScraperBlock", (0.75, 0.32, 0.12), (xs, -0.42, ZL + 0.06), dk, bevel=0.02)
    for sx in (-1, 1):
        tube(f"ScraperPost{sx}", [(xs + sx * 0.28, -0.42, ZL + 0.1), (xs + sx * 0.28, -0.42, ZL + 0.42), (xs + sx * 0.36, -0.42, ZL + 0.55),
                                  (xs + sx * 0.28, -0.42, ZL + 0.62)], 0.022, iron)
        hoop(f"ScraperCurl{sx}", (xs + sx * 0.3, -0.42, ZL + 0.62), 0.05, "Y", iron, thick=0.014)
    box("ScraperBlade", (0.56, 0.03, 0.1), (xs, -0.42, ZL + 0.35), iron, bevel=0.005)
    # moss in the corners, a crack, a stain
    _moss("Moss", [(-HW + 0.12, YL - 0.9 * k + 0.12, ZL - 0.5 * k) for k in range(1, 4)] + [(HW - 0.12, YL - 1.5, ZL - 1.0), (-HW + 0.15, -0.2, ZL),
                   (HW - 0.2, YB + 0.15, 0.5)], K["moss"], rnd, size=0.09)
    _crack("Crack", (-0.9, YL - 0.9 - 0.005, ZL - 0.55), (1, 0, -0.15), (0, 0, 1), 1.0, rnd, K["hollow"])
    return _dims()


# tall and wide props need the preview camera further back
P.PREVIEW_PAD.update({"TownDoor": 1.0, "TownWindow": 1.0, "BayWindow": 1.0, "Chimney": 1.0, "Drainpipe": 1.05})
P.OPEN_DEG.update({"TownDoor_Door0": 95})

P.BUILD.update({
    "TownDoor": town_door,
    "TownWindow": town_window,
    "BayWindow": bay_window,
    "Chimney": chimney,
    "IronBalcony": iron_balcony,
    "ShopAwning": shop_awning,
    "Dormer": dormer,
    "Drainpipe": drainpipe,
    "StoneStoop": stone_stoop,
})
