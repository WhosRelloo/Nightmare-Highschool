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
  crest.png    600x600    the school crest: a shield with a crimson field, a skull, crossed rulers and a padlock
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


def crest():
    sc = reset(600, 600); M = mats(); cam(sc, 6.0); lights(sc, 6)
    # shield: a rounded-bottom shape (curve outline) with a crimson field slab behind
    pts = []
    for i in range(41):
        t = i / 40
        a = math.pi * t
        pts.append((1.9 * math.cos(a + math.pi), -0.02, -0.4 - 1.6 * math.sin(a)))
    pts = [(-1.9, -0.02, 1.9)] + pts + [(1.9, -0.02, 1.9)]
    curve("Rim", pts, 0.16, M["brass"], closed=True)
    slab("Field", 3.7, 3.9, 0.15, (0, 0.2, 0.0), M["crimson"], bevel=0.05)
    # crossed rulers (wood) behind a bone skull
    for s in (-1, 1):
        slab("Ruler", 0.4, 4.6, 0.08, (0, 0.05, -0.1), M["wood"], bevel=0.02).rotation_euler = (0, s * math.pi / 4, 0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.75, depth=1.1, location=(0, -0.25, 0.25), rotation=(0, 0, 0))
    sk = bpy.context.active_object
    rb = sk.modifiers.new("R", "BEVEL"); rb.width = 0.3; rb.segments = 8; rb.limit_method = "ANGLE"
    sk.scale = (1, 0.35, 1)
    link(sk, M["bone"])
    dark = P.material("Hole", base=(0.02, 0.01, 0.01), rough=0.9, wear=0.0, dirt=0.0)
    for x in (-0.28, 0.28):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.2, location=(x, -0.5, 0.3))
        e = bpy.context.active_object; e.scale = (1, 0.3, 1.1); link(e, dark)
    slab("Jaw", 0.9, 0.35, 0.2, (0, -0.35, -0.42), M["bone"], bevel=0.06)
    # padlock at the bottom tip
    slab("Lock", 0.7, 0.6, 0.25, (0, -0.3, -1.65), M["iron"], bevel=0.1)
    render("crest.png")


PIECES = {"panel": panel, "slot": slot, "row": row, "button": button, "node": node, "card": card, "crest": crest}

if __name__ == "__main__":
    for n in (list(PIECES) if WHICH == "all" else [WHICH]):
        PIECES[n]()
