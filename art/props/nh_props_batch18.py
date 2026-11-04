"""Props batch 18 (2026-11-04): nine skateboards for the ride system (Bully-style boards players pull out and ride).
One shared generator, so every board has the same rig as the skateboard system's template:

  pieces (Roblox model-local studs; long axis X, nose at -X, wheels on the ground at y = 0):
    Main      the deck: concave, kicktails, black griptape with a cut-out sigil on top, the graphic underneath, bolts
    TruckF    front truck, origin (-1.786, 0.27, 0)        TruckB    back truck, origin (+1.786, 0.27, 0)
    WheelFL   origin (-1.81, 0.167, +0.538)                WheelFR   origin (-1.81, 0.167, -0.538)
    WheelBL   origin (+1.81, 0.167, +0.538)                WheelBR   origin (+1.81, 0.167, -0.538)
  trucks lean about the long axis at their origin; wheels spin about Roblox Z (the axle) at their origin

  SkateboardRavens      Night Ravens: purple and black, a raven before the moon; iron trucks, violet wheels
  SkateboardRovers      Grave Rovers: grave green, a ringed cross over a ball, headstones; steel trucks, bone wheels
  SkateboardWardens     Iron Wardens: iron grey and rust, a riveted shield and a chain border; rusted trucks
  SkateboardVigil       The Vigil: ink and gold, a candle in a halo of rays and stars; brass trucks, ink wheels
  SkateboardCrimson     The Crimson Court: crimson, a thorned rose and a gilt thorn vine; crimson wheels
  SkateboardMoonlit     the school on its hill under a full moon, bats; silver trucks, moon-pale wheels
  SkateboardBone        bone white with a skeleton hand and hairline cracks; bone wheels
  SkateboardGargoyle    weathered stone with a grinning gargoyle and ember eyes; stone-grey wheels
  SkateboardHeadmaster  gloss black lacquer, double gilt pinstripes and the crest; gilt trucks and hubs

The deck art is drawn by art/props/skate_art.py (Pillow) into art/props/source_skate/ and mapped in object space here.
Blender: x along the board, nose at +x (Roblox X = -x), y across (Roblox Z), z up. Origin at the bottom centre.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import os

import bpy
import bmesh
from mathutils import Matrix

import nh_props as P
from nh_props import box, cyl, set_group, material
from nh_props_batch4 import lathe, prism, _mark, _xform, _dims, flat
from nh_props_batch10 import lacquer, gilt, silver, steel

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "source_skate")

L_DECK, W_DECK, T_DECK, ZC = 5.5, 1.39, 0.15, 0.529
TRUCK_X, TRUCK_Z = 1.786, 0.27
WHEEL_X, WHEEL_Y, WHEEL_R, WHEEL_W = 1.81, 0.538, 0.167, 0.25


def _rgb(c):
    return tuple((v / 255.0) ** 2.2 for v in c)


def art_mat(name, path, rough, grit=0.0):
    """The deck art (top or bottom) in object space: u along x over the deck length, v along y over its width."""
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
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    mp.inputs["Scale"].default_value = (1.0 / L_DECK, 1.0 / W_DECK, 1.0)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(path, check_existing=True)
    im.interpolation = "Cubic"
    im.extension = "EXTEND"
    L(mp.outputs["Vector"], im.inputs["Vector"])
    rv = nt.nodes.new("ShaderNodeValue")
    rv.outputs[0].default_value = rough
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0 if grit else 30.0
    nz.inputs["Detail"].default_value = 2.0
    L(tc.outputs["Object"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = grit if grit else 0.04
    L(nz.outputs["Fac"], bump.inputs["Height"])
    P._weather(nt, bs, im.outputs["Color"], rv.outputs[0], mv.outputs[0], bump.outputs["Normal"], 0.12, False, 0.4)
    return m


def _halfwidth(u):
    r = W_DECK / 2
    straight = L_DECK / 2 - r
    a = abs(u)
    if a <= straight:
        return r
    return max(0.12, math.sqrt(max(0.0, r * r - (a - straight) ** 2)))


def _lift(u, v):
    t = max(0.0, min(1.0, (abs(u) - 1.98) / (L_DECK / 2 - 1.98)))
    kick = 0.34 * t ** 1.6
    concave = 0.035 * (v / (W_DECK / 2)) ** 2
    return kick, concave


def deck(name, top_mat, bot_mat, edge_mat, nu=60, nv=12):
    """The deck as one mesh: a top (griptape), a bottom (graphic) and the rim, kicked up at both ends with concave.
    Evenly spaced rows that stop just short of the tips: no zero-area faces (they wreck the smart UV project)."""
    end = L_DECK / 2 - 0.03
    us = [-end + 2 * end * i / (nu - 1) for i in range(nu)]
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    top, bot = [], []
    for u in us:
        hw = _halfwidth(u)
        rt, rb = [], []
        for j in range(nv):
            v = -hw + 2 * hw * j / (nv - 1)
            kick, conc = _lift(u, v)
            rt.append(bm.verts.new((u, v, ZC + T_DECK / 2 + kick + conc)))
            rb.append(bm.verts.new((u, v, ZC - T_DECK / 2 + kick + conc * 0.7)))
        top.append(rt)
        bot.append(rb)
    faces = []
    for i in range(nu - 1):
        for j in range(nv - 1):
            faces.append((bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1])), 0))
            faces.append((bm.faces.new((bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j], bot[i][j])), 1))
        faces.append((bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0])), 2))
        faces.append((bm.faces.new((top[i + 1][nv - 1], bot[i + 1][nv - 1], bot[i][nv - 1], top[i][nv - 1])), 2))
    for i, s in ((0, 1), (nu - 1, -1)):
        for j in range(nv - 1):
            q = (top[i][j], top[i][j + 1], bot[i][j + 1], bot[i][j])
            faces.append((bm.faces.new(q if s > 0 else tuple(reversed(q))), 2))
    for f, k in faces:
        f.material_index = k
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in (top_mat, bot_mat, edge_mat):
        ob.data.materials.append(m)
    ob["nh_group"] = P.GROUP
    P.PARTS.append(ob)
    return ob


def wheel(prefix, x, y, ure, hub, bearing):
    """A rounded urethane wheel with a hub and a bearing shield, built round Z and turned onto the axle (Blender Y)."""
    s = _mark()
    hw = WHEEL_W / 2
    r = WHEEL_R
    lathe(f"{prefix}Urethane", [(0, -hw), (r * 0.62, -hw), (r * 0.88, -hw * 0.95), (r * 0.98, -hw * 0.75), (r, -hw * 0.45),
                                (r, hw * 0.45), (r * 0.98, hw * 0.75), (r * 0.88, hw * 0.95), (r * 0.62, hw), (0, hw)], ure, seg=22)
    lathe(f"{prefix}Hub", [(0, -hw - 0.004), (r * 0.5, -hw - 0.004), (r * 0.56, -hw + 0.02), (r * 0.56, hw - 0.02),
                           (r * 0.5, hw + 0.004), (0, hw + 0.004)], hub, seg=16)
    cyl(f"{prefix}Bearing", r * 0.3, WHEEL_W + 0.02, (0, 0, 0), bearing, verts=16, bevel=0.004)
    side = 1 if y > 0 else -1
    cyl(f"{prefix}Nut", 0.03, 0.03, (0, 0, side * (hw + 0.02)), bearing, verts=6, bevel=0.0)
    _xform(s, Matrix.Translation((x, y, WHEEL_R)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))


def truck(prefix, x, metal, bush, iron):
    """Baseplate, kingpin with two bushings, a tapered hanger and the axle."""
    sx = 1 if x > 0 else -1
    box(f"{prefix}Base", (0.46, 0.34, 0.05), (x, 0, 0.428), metal, bevel=0.012)
    box(f"{prefix}Riser", (0.36, 0.26, 0.022), (x, 0, 0.443), iron, bevel=0.006)
    for bx in (-0.14, 0.14):
        for by in (-0.1, 0.1):
            cyl(f"{prefix}BaseBolt{bx}{by}", 0.022, 0.03, (x + bx, by, 0.4), iron, verts=6, bevel=0.0)
    cyl(f"{prefix}Kingpin", 0.026, 0.2, (x - sx * 0.07, 0, 0.33), iron, rot=(0, sx * 0.45, 0), verts=10, bevel=0.0)
    cyl(f"{prefix}BushTop", 0.062, 0.05, (x - sx * 0.065, 0, 0.375), bush, verts=16, bevel=0.012)
    cyl(f"{prefix}BushBot", 0.058, 0.045, (x - sx * 0.08, 0, 0.3), bush, verts=16, bevel=0.012)
    cyl(f"{prefix}PivotCup", 0.04, 0.09, (x + sx * 0.12, 0, 0.36), metal, rot=(0, -sx * 0.5, 0), verts=12, bevel=0.008)
    prism(f"{prefix}Hanger", [(-0.5, 0.15), (0.5, 0.15), (0.42, 0.2), (0.14, 0.27), (0, 0.29), (-0.14, 0.27), (-0.42, 0.2)],
          x, 0.15, metal, plane="YZ", bevel=0.012)
    cyl(f"{prefix}Axle", 0.028, 1.3, (x, 0, WHEEL_R), iron, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)


# per board: trucks metal, bushings, wheel urethane, hub, deck rim
LOOKS = {
    "SkateboardRavens": ("iron", (150, 110, 190), (88, 44, 120), "lacquer", (60, 30, 80)),
    "SkateboardRovers": ("steel", (110, 160, 110), (226, 214, 188), "iron", (30, 60, 40)),
    "SkateboardWardens": ("rust", (150, 70, 36), (58, 58, 62), "iron", (80, 80, 86)),
    "SkateboardVigil": ("brass", (214, 172, 92), (20, 20, 34), "gilt", (16, 20, 52)),
    "SkateboardCrimson": ("lacquer", (214, 172, 92), (150, 16, 30), "gilt", (110, 12, 24)),
    "SkateboardMoonlit": ("silver", (170, 170, 210), (230, 225, 205), "silver", (26, 34, 78)),
    "SkateboardBone": ("steel", (40, 36, 32), (226, 214, 188), "iron", (200, 188, 162)),
    "SkateboardGargoyle": ("iron", (210, 120, 40), (120, 118, 112), "iron", (90, 88, 84)),
    "SkateboardHeadmaster": ("gilt", (130, 16, 28), (14, 12, 16), "gilt", (18, 16, 20)),
}


def skateboard(name, M):
    look = LOOKS[name]
    metals = {"iron": M["iron"], "brass": M["brass"], "steel": steel(), "silver": silver(), "gilt": gilt(), "lacquer": lacquer(),
              "rust": material("RustIron", "NH_Iron", tint=(0.32, 0.15, 0.07), scale=0.6, rough_add=0.15, wear=0.6, dirt=0.9)}
    metal = metals[look[0]]
    bush = flat("Bushing", _rgb(look[1]), 0.6)
    ure = flat("Urethane", _rgb(look[2]), 0.55, dirt=0.75)
    hub = metals[look[3]]
    rim = flat("DeckRim", _rgb(look[4]), 0.35)
    grip = art_mat("Grip", os.path.join(ART, f"{name}_grip.png"), 0.95, grit=0.35)
    bottom = art_mat("Graphic", os.path.join(ART, f"{name}_bottom.png"), 0.32)
    set_group("Main")
    deck(f"{name}Deck", grip, bottom, rim)
    for tx in (TRUCK_X, -TRUCK_X):
        for bx in (-0.14, 0.14):
            for by in (-0.1, 0.1):
                cyl(f"Bolt{tx}{bx}{by}", 0.024, 0.012, (tx + bx, by, ZC + T_DECK / 2 + 0.005), M["iron"], verts=8, bevel=0.0)
    for g, tx in (("TruckF", TRUCK_X), ("TruckB", -TRUCK_X)):
        set_group(g, hinge=(tx, 0, TRUCK_Z))
        truck(g, tx, metal, bush, M["iron"])
    for g, wx, wy in (("WheelFL", WHEEL_X, WHEEL_Y), ("WheelFR", WHEEL_X, -WHEEL_Y), ("WheelBL", -WHEEL_X, WHEEL_Y), ("WheelBR", -WHEEL_X, -WHEEL_Y)):
        set_group(g, hinge=(wx, wy, WHEEL_R))
        wheel(g, wx, wy, ure, hub, steel())
    set_group("Main")
    return _dims()


for _n in LOOKS:
    P.BUILD[_n] = (lambda n: (lambda M: skateboard(n, M)))(_n)
    P.PREVIEW_PAD[_n] = 0.72
    for _g in ("TruckF", "TruckB", "WheelFL", "WheelFR", "WheelBL", "WheelBR"):
        P.OPEN_DEG[f"{_n}_{_g}"] = 0
