"""Nightmare Highschool UI kit v2 (design proposal, not in the game yet), rendered with Cycles from PBR materials.

usage: "E:/Blender/blender.exe" --background --factory-startup --python art/ui/kit2/nh_ui_kit2.py -- [piece|all] [--samples 48]
Pieces (transparent PNGs in art/ui/kit2/out):
  panel.png    1600x1100  a large panel: wrought-iron frame with gothic corner finials and brass caps, a riveted band,
                          a thin crimson inner trim and a padlock clasp at the top; the inside is dark tooled leather
  slot.png     320x320    an item slot: iron frame, brass corner caps, smoked-glass well
  row.png      1800x150   a list row (party member): crimson leather bar set in an iron frame with spiked end caps
  button.png   520x150    a button plate: iron with a brass edge and rivets
  node.png     420x420    a skill-tree node: an iron diamond wrapped in chain (silver, tinted per branch later)
  card.png     760x480    a shop card frame: iron with brass filigree corners (neutral, tinted per rarity later)
  crest.png    600x680    the school crest: gothic heater shield (iron rim, brass trim, crimson leather), silver
                          crescent in a dark chief, R6 bone skull with ember eyes over crossed brass skeleton keys,
                          padlock on the point, NOCTE DISCIMUS ribbon
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "props")))
import nh_props as P  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0] if argv and not argv[0].startswith("--") else "all"
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 48


def reset(rx, ry):
    P._img_cache.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.07, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    sc.world = w
    return sc


def cam(sc, width):
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = width
    co = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(co)
    co.location = (0, -20, 0)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co


def lights(sc, s):
    def area(loc, e, c, size):
        L = bpy.data.lights.new("A", "AREA"); L.energy = e; L.color = c; L.size = size
        o = bpy.data.objects.new("A", L); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area((-s * 0.5, -s * 0.9, s * 0.8), 70 * s, (1.0, 0.8, 0.56), s)     # candle key, top-left
    area((s * 0.7, -s * 0.6, -s * 0.4), 22 * s, (0.55, 0.5, 0.85), s)    # violet fill
    area((0, s * 0.6, s * 0.3), 30 * s, (0.95, 0.25, 0.3), s)            # crimson rim


def mats():
    m = P.material
    return {
        "iron": m("Iron", "NH_Iron", tint=(0.12, 0.11, 0.12), scale=1.2, rough_add=0.05, wear=0.65, wear_metal=True),
        "brass": m("Brass", "NH_Brass", tint=(1.0, 0.8, 0.52), scale=1.5, wear=0.45, dirt=0.9),
        "silver": m("Silver", base=(0.72, 0.72, 0.76), rough=0.28, metal=1.0, wear=0.45, dirt=0.8),
        "leather": m("Leather", "NH_Leather", tint=(0.05, 0.035, 0.04), scale=2.2, normal=0.7, wear=0.25),
        "crimson": m("Crimson", "NH_Leather", tint=(0.32, 0.03, 0.045), scale=2.2, normal=0.6, wear=0.4),
        "glass": m("Glass", base=(0.03, 0.025, 0.035), rough=0.12, wear=0.0, dirt=0.3),
        "bone": m("Bone", "NH_Limestone", tint=(0.9, 0.84, 0.7), scale=1.0, wear=0.35, dirt=1.0),
        "wood": m("Wood", "NH_DeskWood", tint=(0.45, 0.3, 0.18), scale=1.0, wear=0.4),
    }


def link(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def bar(name, a, b, r, mat, square=True):
    """a straight iron bar between two points (square or round section)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(1)
    sp.points[0].co = (*a, 1); sp.points[1].co = (*b, 1)
    cu.bevel_depth = r; cu.bevel_resolution = 0 if square else 4
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def curve(name, pts, r, mat, closed=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = r; cu.bevel_resolution = 4
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def rivet(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=loc)
    ob = bpy.context.active_object; ob.scale = (1, 0.5, 1)
    return link(ob, mat)


def slab(name, w, h, d, loc, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object; ob.name = name; ob.scale = (w, d, h)
    b = ob.modifiers.new("B", "BEVEL"); b.width = bevel; b.segments = 3
    return link(ob, mat)


def scroll(cx, cz, s, sx, sz, mat):
    """a wrought-iron C-scroll (filigree) in the XZ plane, mirrored by sx/sz."""
    pts = []
    for i in range(40):
        t = i / 39
        a = t * math.pi * 1.6
        r = s * (1 - 0.7 * t)
        pts.append((cx + sx * (math.cos(a) * r), -0.05, cz + sz * (math.sin(a) * r)))
    curve("Scroll", pts, s * 0.08, mat)


def finial(x, z, s, sx, sz, M):
    """a gothic corner: brass cap, a spike outward along the diagonal, two iron scrolls."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=s * 0.32, depth=0.25, location=(x, -0.05, z), rotation=(math.pi / 2, 0, 0))
    link(bpy.context.active_object, M["brass"])
    d = Vector((sx, 0, sz)).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=s * 0.16, depth=s * 0.9, location=(x + d.x * s * 0.55, -0.05, z + d.z * s * 0.55))
    sp = bpy.context.active_object
    sp.rotation_euler = (0, math.atan2(d.x, d.z), 0)
    link(sp, M["iron"])
    scroll(x + sx * s * 0.75, z, s * 0.42, sx, -sz, M["iron"])
    scroll(x, z + sz * s * 0.75, s * 0.42, -sx, sz, M["iron"])
    rivet((x, -0.2, z), s * 0.12, M["silver"])


def frame(w, h, M, band=0.28, corner=0.9, rivets=True, trim=True):
    """an iron frame (w x h outer) with brass-capped gothic corners."""
    hw, hh = w / 2, h / 2
    for (a, b) in (((-hw, 0, hh), (hw, 0, hh)), ((-hw, 0, -hh), (hw, 0, -hh)), ((-hw, 0, -hh), (-hw, 0, hh)), ((hw, 0, -hh), (hw, 0, hh))):
        bar("Band", a, b, band * 0.5, M["iron"])
    if trim:
        i = band * 0.95
        for (a, b) in (((-hw + i, -0.02, hh - i), (hw - i, -0.02, hh - i)), ((-hw + i, -0.02, -hh + i), (hw - i, -0.02, -hh + i)),
                       ((-hw + i, -0.02, -hh + i), (-hw + i, -0.02, hh - i)), ((hw - i, -0.02, -hh + i), (hw - i, -0.02, hh - i))):
            bar("Trim", a, b, band * 0.12, M["crimson"], square=False)
    if rivets:
        nx = max(2, int(w / 1.1))
        nz = max(2, int(h / 1.1))
        for k in range(1, nx):
            x = -hw + w * k / nx
            rivet((x, -0.18, hh), band * 0.2, M["brass"]); rivet((x, -0.18, -hh), band * 0.2, M["brass"])
        for k in range(1, nz):
            z = -hh + h * k / nz
            rivet((-hw, -0.18, z), band * 0.2, M["brass"]); rivet((hw, -0.18, z), band * 0.2, M["brass"])
    for sx in (-1, 1):
        for sz in (-1, 1):
            finial(sx * hw, sz * hh, corner, sx, sz, M)


def render(name):
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("[kit2]", name)


# ------------------------------------------------------------------ pieces

def panel():
    sc = reset(1600, 1100); M = mats(); cam(sc, 16.0); lights(sc, 14)
    slab("Back", 14.4, 9.4, 0.2, (0, 0.25, 0), M["leather"], bevel=0.05)
    frame(14.6, 9.6, M, band=0.34, corner=1.0)
    # padlock clasp, top centre
    slab("LockBody", 0.9, 0.8, 0.3, (0, -0.25, 4.8 - 0.1), M["iron"], bevel=0.12)
    pts = [(0.3 * math.cos(math.pi * i / 20), -0.25, 5.15 + 0.38 * math.sin(math.pi * i / 20)) for i in range(21)]
    curve("Shackle", pts, 0.07, M["silver"])
    rivet((0, -0.45, 4.7), 0.08, M["brass"])
    render("panel.png")


def slot():
    sc = reset(320, 320); M = mats(); cam(sc, 3.2); lights(sc, 4)
    slab("Well", 2.5, 2.5, 0.2, (0, 0.2, 0), M["glass"], bevel=0.04)
    frame(2.7, 2.7, M, band=0.16, corner=0.38, rivets=False, trim=False)
    render("slot.png")


def row():
    sc = reset(1800, 150); M = mats(); cam(sc, 18.0); lights(sc, 10)
    slab("Leather", 16.6, 0.95, 0.2, (0, 0.15, 0), M["crimson"], bevel=0.05)
    for z in (0.55, -0.55):
        bar("Rail", (-8.4, 0, z), (8.4, 0, z), 0.08, M["iron"])
    for sx in (-1, 1):
        x = sx * 8.5
        slab("Cap", 0.5, 1.35, 0.35, (x, -0.05, 0), M["iron"], bevel=0.1)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.18, depth=0.55, location=(x + sx * 0.45, -0.05, 0), rotation=(0, sx * math.pi / 2, 0))
        link(bpy.context.active_object, M["iron"])
        rivet((x, -0.25, 0.4), 0.07, M["brass"]); rivet((x, -0.25, -0.4), 0.07, M["brass"])
    render("row.png")


def button():
    sc = reset(520, 150); M = mats(); cam(sc, 5.2); lights(sc, 4)
    slab("Plate", 4.6, 1.1, 0.25, (0, 0.1, 0), M["iron"], bevel=0.12)
    for (a, b) in (((-2.25, -0.06, 0.5), (2.25, -0.06, 0.5)), ((-2.25, -0.06, -0.5), (2.25, -0.06, -0.5))):
        bar("Edge", a, b, 0.045, M["brass"], square=False)
    for x in (-2.05, 2.05):
        for z in (0.32, -0.32):
            rivet((x, -0.2, z), 0.07, M["brass"])
    render("button.png")


def node():
    sc = reset(420, 420); M = mats(); cam(sc, 4.2); lights(sc, 5)
    # diamond frame
    d = 1.45
    pts = [(0, 0, d), (d, 0, 0), (0, 0, -d), (-d, 0, 0)]
    for i in range(4):
        bar("Edge", pts[i], pts[(i + 1) % 4], 0.13, M["silver"])
    slab("Well", 1.7, 1.7, 0.15, (0, 0.2, 0), M["glass"], bevel=0.02)
    bpy.data.objects["Well"].rotation_euler = (0, math.pi / 4, 0)
    # chain wrapped round the diamond
    for i in range(4):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % 4])
        n = 6
        for k in range(n):
            t = (k + 0.5) / n
            p = a.lerp(b, t) * 1.12
            ang = math.atan2((b - a).z, (b - a).x)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.04, major_segments=16, minor_segments=6,
                                             location=(p.x, -0.12, p.z), rotation=(math.pi / 2 if k % 2 else 0, -ang, 0))
            ob = bpy.context.active_object; ob.scale = (1.5, 1, 1)
            link(ob, M["silver"])
    render("node.png")


def card():
    sc = reset(760, 480); M = mats(); cam(sc, 7.6); lights(sc, 6)
    slab("Back", 6.8, 4.2, 0.15, (0, 0.2, 0), M["leather"], bevel=0.04)
    frame(7.0, 4.4, M, band=0.14, corner=0.55, rivets=False, trim=True)
    render("card.png")


def shield_outline(w, top, side, tip, n=24):
    """a gothic heater shield in the XZ plane: flat top with a small central peak, straight sides, curved to a point."""
    hw = w / 2
    head = [(-hw, top), (-hw * 0.12, top), (0, top + 0.18), (hw * 0.12, top), (hw, top), (hw, side)]
    right = []
    for i in range(1, n):
        t = i / n
        x = (1 - t) ** 2 * hw + 2 * (1 - t) * t * hw
        z = (1 - t) ** 2 * side + 2 * (1 - t) * t * (side + (tip - side) * 0.55) + t * t * tip
        right.append((x, z))
    left = [(-x, z) for (x, z) in reversed(right)]
    return head + right + [(0, tip)] + left + [(-hw, side)]


def filled(name, pts2d, depth, y, mat):
    """an extruded, filled 2D outline facing the camera (-Y)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "2D"; cu.fill_mode = "BOTH"
    cu.extrude = depth; cu.bevel_depth = 0.02
    sp = cu.splines.new("POLY"); sp.points.add(len(pts2d) - 1)
    for i, (x, z) in enumerate(pts2d):
        sp.points[i].co = (x, z, 0, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, 0); ob.location = (0, y, 0)
    ob.data.materials.append(mat)
    return ob


def text(body, size, loc, mat, extrude=0.03, font="georgiab.ttf", spacing=1.0):
    cu = bpy.data.curves.new("T", "FONT"); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.bevel_depth = 0.006; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.space_character = spacing
    try:
        cu.font = bpy.data.fonts.load("C:/Windows/Fonts/" + font, check_existing=True)
    except Exception:
        pass
    ob = bpy.data.objects.new("T", cu); bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, 0); ob.location = loc
    ob.data.materials.append(mat)
    return ob


def skeleton_key(angle, M):
    """a brass skeleton key lying diagonally behind the skull (bow up, bit down)."""
    root = bpy.data.objects.new("Key", None); bpy.context.collection.objects.link(root)
    parts = []
    bpy.ops.mesh.primitive_torus_add(major_radius=0.32, minor_radius=0.08, major_segments=28, minor_segments=8,
                                     location=(0, 0, 1.75), rotation=(math.pi / 2, 0, 0))
    parts.append(bpy.context.active_object)
    for z in (1.33, 1.2):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.045, major_segments=16, minor_segments=6, location=(0, 0, z))
        parts.append(bpy.context.active_object)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.075, depth=3.0, location=(0, 0, -0.2))
    parts.append(bpy.context.active_object)
    for (w, h, z) in ((0.42, 0.14, -1.45), (0.3, 0.12, -1.2), (0.42, 0.1, -1.0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(w / 2, 0, z)); c = bpy.context.active_object; c.scale = (w, 0.1, h)
        parts.append(c)
    for o in parts:
        link(o, M["brass"]); o.parent = root
    root.rotation_euler = (0, angle, 0); root.location = (0, 0.02, -0.15)
    return root


def r6_skull(loc, M):
    """an R6-style skull: a rounded block cranium, deep oval sockets with ember eyes, a nose notch, a squared jaw."""
    x, y, z = loc
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.18)); sk = bpy.context.active_object
    sk.scale = (1.5, 0.9, 1.25)
    bv = sk.modifiers.new("B", "BEVEL"); bv.width = 0.36; bv.segments = 10
    link(sk, M["bone"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y + 0.05, z - 0.62)); jaw = bpy.context.active_object
    jaw.scale = (1.0, 0.75, 0.42)
    bv = jaw.modifiers.new("B", "BEVEL"); bv.width = 0.12; bv.segments = 6
    link(jaw, M["bone"])
    dark = P.material("Socket", base=(0.015, 0.008, 0.01), rough=0.85, wear=0.0, dirt=0.0)
    glow = P.material("Ember", base=(0.9, 0.08, 0.06), rough=0.4, wear=0.0, dirt=0.0)
    try:
        bsdf = glow.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.12, 0.08, 1)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    except Exception:
        pass
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.27, location=(x + sx * 0.36, y - 0.42, z + 0.12))
        e = bpy.context.active_object; e.scale = (1.0, 0.45, 1.15); e.rotation_euler = (0, sx * 0.25, 0); link(e, dark)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.06, location=(x + sx * 0.36, y - 0.5, z + 0.1))
        link(bpy.context.active_object, glow)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.13, depth=0.1, location=(x, y - 0.45, z - 0.2), rotation=(math.pi / 2, 0, math.pi))
    link(bpy.context.active_object, dark)
    for k in range(-2, 3):
        slab("Gap", 0.025, 0.24, 0.05, (x + k * 0.17, y - 0.33, z - 0.6), dark, bevel=0.005)
    slab("Bite", 0.9, 0.03, 0.05, (x, y - 0.33, z - 0.6), dark, bevel=0.005)


def crest():
    sc = reset(600, 680); M = mats(); cam(sc, 6.0); lights(sc, 6)
    bpy.data.objects["C"].location = (0, -20, -0.25)
    out = shield_outline(3.8, 2.0, 0.0, -2.35)
    inner = shield_outline(3.36, 1.78, -0.05, -2.02)
    filled("Back", out, 0.12, 0.32, M["iron"])
    filled("Field", inner, 0.1, 0.18, M["crimson"])
    curve("Trim", [(x, 0.05, z) for (x, z) in inner], 0.035, M["brass"], closed=True)
    curve("Rim", [(x, 0.0, z) for (x, z) in out], 0.1, M["iron"], closed=True)
    chief = [(-1.68, 1.78), (-0.2, 1.78), (0, 1.94), (0.2, 1.78), (1.68, 1.78), (1.68, 1.02), (-1.68, 1.02)]
    filled("Chief", chief, 0.06, 0.1, M["leather"])
    curve("ChiefLine", [(-1.68, 0.02, 1.02), (1.68, 0.02, 1.02)], 0.04, M["brass"])
    moon_o = [(0.42 * math.cos(a), 0.42 * math.sin(a)) for a in [math.pi * (0.25 + 1.5 * i / 30) for i in range(31)]]
    moon_i = [(0.14 + 0.33 * math.cos(a), 0.06 + 0.33 * math.sin(a)) for a in [math.pi * (1.75 - 1.5 * i / 30) for i in range(31)]]
    mo = filled("Moon", moon_o + moon_i, 0.08, 0.02, M["silver"]); mo.location.z = 1.42; mo.location.x = -0.05
    for sx in (-1, 1):
        for k in range(3):
            rivet((sx * (0.75 + k * 0.32), -0.06, 1.4), 0.05, M["brass"])
    skeleton_key(math.pi / 4, M); skeleton_key(-math.pi / 4, M)
    r6_skull((0, -0.15, -0.1), M)
    for sx in (-1, 1):
        finial(sx * 1.9, 2.0, 0.5, sx, 1, M)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.12, depth=0.5, location=(0, -0.02, -2.55), rotation=(math.pi, 0, 0))
    link(bpy.context.active_object, M["iron"])
    slab("LockBody", 0.62, 0.52, 0.26, (0, -0.3, -1.6), M["iron"], bevel=0.1)
    curve("Shackle", [(0.2 * math.cos(math.pi * i / 16), -0.3, -1.34 + 0.24 * math.sin(math.pi * i / 16)) for i in range(17)], 0.05, M["silver"])
    rivet((0, -0.45, -1.62), 0.06, M["brass"])
    slab("Ribbon", 3.5, 0.42, 0.08, (0, -0.55, -2.15), M["crimson"], bevel=0.03)
    for sx in (-1, 1):
        t = slab("Tail", 0.55, 0.42, 0.06, (sx * 1.95, -0.45, -2.25), M["crimson"], bevel=0.03); t.rotation_euler = (0, sx * 0.35, 0)
    for z in (-1.95, -2.35):
        curve("RibbonEdge", [(-1.75, -0.6, z), (1.75, -0.6, z)], 0.018, M["brass"])
    text("NOCTE  DISCIMUS", 0.24, (0, -0.62, -2.16), M["brass"], spacing=1.15)
    render("crest.png")


PIECES = {"panel": panel, "slot": slot, "row": row, "button": button, "node": node, "card": card, "crest": crest}

if __name__ == "__main__":
    for n in (list(PIECES) if WHICH == "all" else [WHICH]):
        PIECES[n]()
