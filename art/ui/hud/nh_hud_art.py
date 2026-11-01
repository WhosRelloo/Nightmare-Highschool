"""Nightmare Highschool HUD art, rendered with Cycles from PBR materials (Blender 5.x, headless).

usage: "E:/Blender/blender.exe" --background --factory-startup --python art/ui/hud/nh_hud_art.py -- [piece|all] [--samples 64]
Pieces (transparent PNGs in art/ui/hud/out):
  hud_frame.png     2400x360  the health bar's frame: aged brass capsule rail with rivets, iron clamps at the ends wrapped in
                              barbed wire, a short chain hanging from each clamp. The window where the fill shows is empty.
  hud_back.png      2400x360  the dark iron channel behind the fill
  hud_mini.png      1200x160  the small top bar (posture): brass rail with three brackets
  hud_socket.png    256x256   a cooldown socket: brass ring, smoked-glass well, four rivets
  hud_tag.png       1024x1024 combat tag emblem: a rusted iron padlock with a skull keyhole, crossed chains, barbed wire ring
Uses the school's seamless PBR set (art/props/source) through the props pipeline's material(), lit like a candlelit corridor.
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "props")))
import nh_props as P  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0] if argv and not argv[0].startswith("--") else "all"
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64


def reset(res_x, res_y):
    P._img_cache.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = res_x, res_y
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.07, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    return sc


def cam(sc, width, height, dist=20):
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = width
    co = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(co)
    co.location = (0, -dist, 0)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    sc.render.resolution_y = int(sc.render.resolution_x * height / width)


def lights(sc, scale=10):
    def area(loc, energy, color, size):
        L = bpy.data.lights.new("A", "AREA")
        L.energy = energy
        L.color = color
        L.size = size
        o = bpy.data.objects.new("A", L)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area((-scale * 0.4, -scale * 0.8, scale * 0.7), 80 * scale, (1.0, 0.78, 0.52), scale * 0.8)   # warm candle key, top-left
    area((scale * 0.6, -scale * 0.6, -scale * 0.3), 25 * scale, (0.55, 0.5, 0.85), scale * 0.8)    # blue-violet fill
    area((0, scale * 0.5, scale * 0.4), 40 * scale, (0.95, 0.25, 0.3), scale)                    # crimson rim


def mats():
    m = P.material
    return {
        "brass": m("Brass", "NH_Brass", tint=(1.05, 0.82, 0.55), scale=1.6, wear=0.45, dirt=0.9),
        "brassdark": m("BrassDark", "NH_Brass", tint=(0.55, 0.38, 0.22), scale=1.6, wear=0.35, dirt=1.0),
        "iron": m("Iron", "NH_Iron", tint=(0.11, 0.1, 0.11), scale=1.4, rough_add=0.05, wear=0.6, wear_metal=True),
        "rust": m("Rust", "NH_Iron", tint=(0.32, 0.16, 0.08), scale=1.2, rough_add=0.25, wear=0.5, dirt=1.0),
        "steel": m("Steel", base=(0.62, 0.62, 0.66), rough=0.3, metal=1.0, wear=0.4),
        "back": m("Back", "NH_Leather", tint=(0.05, 0.03, 0.035), scale=3.0, normal=0.6, wear=0.2),
        "glass": m("Glass", base=(0.04, 0.03, 0.045), rough=0.12, wear=0.0, dirt=0.2),
    }


def emissive(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Emission Color"].default_value = (*color, 1)
    bs.inputs["Emission Strength"].default_value = strength
    return m


def link(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def curve_obj(name, pts, radius, mat, closed=False, res=6, bevel_res=4):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def capsule_path(cx, length, h, z=0.0, n=24):
    """a stadium (capsule) outline in the XZ plane, facing the camera (-Y)."""
    r = h / 2
    half = length / 2 - r
    pts = []
    for i in range(n + 1):  # right cap
        a = -math.pi / 2 + math.pi * i / n
        pts.append((cx + half + math.cos(a) * r, 0, z + math.sin(a) * r))
    for i in range(n + 1):  # left cap
        a = math.pi / 2 + math.pi * i / n
        pts.append((cx - half + math.cos(a) * r, 0, z + math.sin(a) * r))
    return pts


def capsule_slab(name, length, h, depth, y, mat, n=24):
    """a solid stadium-shaped slab facing the camera."""
    bm = bmesh.new()
    pts = capsule_path(0, length, h, n=n)
    vs = [bm.verts.new((p[0], y, p[2])) for p in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.y += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bev = ob.modifiers.new("B", "BEVEL"); bev.width = 0.04; bev.segments = 3; bev.limit_method = "ANGLE"
    return link(ob, mat)


def rivet(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.scale = (1, 0.55, 1)
    return link(ob, mat)


def barbed_wire(cx, cz, radius, length, turns, mat, wire_mat):
    """a coil of barbed wire wrapped round a clamp (axis X), with barbs every so often."""
    pts = []
    n = int(turns * 24)
    for i in range(n + 1):
        t = i / n
        a = t * turns * math.tau
        pts.append((cx - length / 2 + length * t, math.sin(a) * radius, cz + math.cos(a) * radius))
    curve_obj("Wire", pts, 0.022, wire_mat)
    for i in range(0, n, 9):
        p = Vector(pts[i])
        for s in (-1, 1):
            d = Vector((0.06 * s, -0.12, 0.09 * s))
            curve_obj("Barb", [tuple(p - d), tuple(p + d)], 0.012, wire_mat)


def chain(x0, z0, links, mat, size=0.16, sway=0.0):
    for i in range(links):
        bpy.ops.mesh.primitive_torus_add(major_radius=size, minor_radius=size * 0.28, major_segments=20, minor_segments=8,
                                         location=(x0 + math.sin(i * 0.5) * sway, -0.05, z0 - i * size * 1.45),
                                         rotation=(0, math.pi / 2 if i % 2 else 0, math.pi / 2))
        ob = bpy.context.active_object
        ob.scale = (1, 1, 1.45)
        link(ob, mat)


def render(name):
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    print("[hud]", name)


# ------------------------------------------------------------------ pieces

L, H = 20.0, 2.0      # main bar: 20 x 2 units (window inside the rail)


def frame(back_only=False):
    sc = reset(2400, 360)
    M = mats()
    cam(sc, 24.0, 3.6)
    lights(sc, 14)
    if back_only:
        capsule_slab("Back", L - 0.05, H - 0.05, 0.3, 0.25, M["back"])
        render("hud_back.png")
        return
    # the outer rail and an inner lip
    # an iron band behind the rail (ring-shaped: outer slab minus the window)
    band = capsule_slab("Band", L + 0.95, H + 0.95, 0.25, 0.35, M["iron"])
    hole = capsule_slab("BandHole", L - 0.05, H - 0.05, 0.6, 0.15, M["iron"])
    hole.hide_render = True
    bo = band.modifiers.new("Hole", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"
    curve_obj("Rail", capsule_path(0, L + 0.32, H + 0.32), 0.26, M["brass"], closed=True)
    curve_obj("Rail2", capsule_path(0, L + 0.82, H + 0.82), 0.09, M["brassdark"], closed=True)
    curve_obj("Lip", capsule_path(0, L - 0.04, H - 0.04), 0.06, M["brassdark"], closed=True)
    # top rail with brackets (like a coat of arms bar)
    curve_obj("Top", [(-L / 2 + 0.6, 0, H / 2 + 0.72), (L / 2 - 0.6, 0, H / 2 + 0.72)], 0.08, M["brass"])
    for x in (-L / 2 + 0.6, -L * 0.25, 0, L * 0.25, L / 2 - 0.6):
        curve_obj("Bracket", [(x, 0, H / 2 + 0.4), (x, 0, H / 2 + 0.8)], 0.05, M["brassdark"])
        rivet((x, -0.08, H / 2 + 0.77), 0.08, M["brass"])
    # rivets round the rail
    for i in range(18):
        x = -L / 2 + 1.4 + i * (L - 2.8) / 17
        for z in (H / 2 + 0.3, -H / 2 - 0.3):
            rivet((x, -0.05, z), 0.07, M["brass"])
    # lower studs (the cooldown sockets sit below in the UI)
    for x in (-L * 0.32, L * 0.32):
        curve_obj("Drop", [(x, 0, -H / 2 - 0.12), (x, 0, -H / 2 - 0.42)], 0.05, M["brassdark"])
        rivet((x, -0.08, -H / 2 - 0.42), 0.08, M["brass"])
    # iron clamps at the ends, wrapped in barbed wire, with a chain hanging off
    for s in (-1, 1):
        cx = s * (L / 2 - 1.15)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=H / 2 + 0.3, depth=0.55, location=(cx, 0, 0), rotation=(0, math.pi / 2, 0))
        cl = bpy.context.active_object
        bev = cl.modifiers.new("B", "BEVEL"); bev.width = 0.06; bev.segments = 3
        link(cl, M["iron"])
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=H / 2 + 0.05, depth=0.6, location=(cx, -0.05, 0), rotation=(0, math.pi / 2, 0))
        hole = bpy.context.active_object
        boo = cl.modifiers.new("Hole", "BOOLEAN"); boo.object = hole; boo.operation = "DIFFERENCE"
        hole.hide_render = True
        for k in range(6):
            a = k / 6 * math.tau
            rivet((cx + 0.0, -(H / 2 + 0.3) * 0 - 0.3, math.cos(a) * (H / 2 + 0.17)), 0.05, M["steel"])
        barbed_wire(cx + s * 0.9, 0, H / 2 + 0.22, 1.1, 3.5, M["rust"], M["rust"])
        chain(cx + s * 0.5, -H / 2 - 0.35, 5, M["iron"], size=0.13, sway=0.04)
    render("hud_frame.png")


def mini():
    sc = reset(1200, 160)
    M = mats()
    cam(sc, 12.0, 1.6)
    lights(sc, 8)
    curve_obj("Rail", capsule_path(0, 10.4, 0.62), 0.09, M["brass"], closed=True)
    curve_obj("Lip", capsule_path(0, 10.1, 0.42), 0.03, M["brassdark"], closed=True)
    for x in (-4.6, 0, 4.6):
        curve_obj("Bracket", [(x, 0, 0.3), (x, 0, 0.62)], 0.04, M["brassdark"])
        rivet((x, -0.06, 0.6), 0.06, M["brass"])
    for x in (-5.3, 5.3):
        rivet((x, -0.08, 0), 0.08, M["steel"])
    render("hud_mini.png")


def socket():
    sc = reset(256, 256)
    M = mats()
    cam(sc, 2.4, 2.4)
    lights(sc, 3)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.12, major_segments=48, minor_segments=12, rotation=(math.pi / 2, 0, 0))
    link(bpy.context.active_object, M["brass"])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.76, minor_radius=0.04, major_segments=48, minor_segments=8, rotation=(math.pi / 2, 0, 0))
    link(bpy.context.active_object, M["brassdark"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.78, depth=0.1, location=(0, 0.12, 0), rotation=(math.pi / 2, 0, 0))
    link(bpy.context.active_object, M["glass"])
    for k in range(4):
        a = k / 4 * math.tau + math.pi / 4
        rivet((math.cos(a) * 0.9, -0.12, math.sin(a) * 0.9), 0.07, M["steel"])
    render("hud_socket.png")


def tag():
    sc = reset(1024, 1024)
    M = mats()
    cam(sc, 6.0, 6.0)
    lights(sc, 6)
    # crossed chains behind
    for s in (-1, 1):
        for i in range(17):
            t = (i - 8) * 0.3
            ang = math.pi / 4 * s
            bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.065, major_segments=24, minor_segments=10,
                                             location=(t * 0.7071 * s, 0.6, t * 0.7071),
                                             rotation=(math.pi / 2 if i % 2 else 0, -ang * s, 0))
            ob = bpy.context.active_object
            ob.scale = (1.5, 1, 1) if i % 2 == 0 else (1.5, 1, 1)
            ob.rotation_euler = (math.pi / 2 if i % 2 else 0, 0, 0)
            ob.rotation_euler.rotate_axis("Y", -ang * s)
            link(ob, M["iron"])
    # barbed-wire ring
    pts = []
    for i in range(241):
        a = i / 240 * math.tau * 1.0
        r = 2.45 + math.sin(a * 9) * 0.06
        pts.append((math.cos(a) * r, 0.3 + math.sin(a * 40) * 0.04, math.sin(a) * r))
    curve_obj("Ring", pts, 0.055, M["rust"], closed=True)
    for i in range(0, 240, 12):
        p = Vector(pts[i])
        o = p.normalized() * 0.16
        curve_obj("Barb", [tuple(p - o + Vector((0, -0.08, 0))), tuple(p + o + Vector((0, 0.08, 0)))], 0.02, M["rust"])
    # padlock: shackle
    pts = []
    for i in range(41):
        a = math.pi * i / 40
        pts.append((math.cos(a) * 0.82, 0, 0.55 + math.sin(a) * 0.95))
    pts = [(0.82, 0, 0.1)] + pts + [(-0.82, 0, 0.1)]
    curve_obj("Shackle", pts, 0.17, M["steel"])
    # body
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.55))
    body = bpy.context.active_object
    body.scale = (2.3, 0.75, 1.9)
    bev = body.modifiers.new("B", "BEVEL"); bev.width = 0.28; bev.segments = 6
    link(body, M["rust"])
    # iron face plate with rivets
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.4, -0.55))
    plate = bpy.context.active_object
    plate.scale = (1.85, 0.08, 1.5)
    bev = plate.modifiers.new("B", "BEVEL"); bev.width = 0.12; bev.segments = 4
    link(plate, M["iron"])
    for x in (-0.78, 0.78):
        for z in (-1.18, 0.08):
            rivet((x, -0.46, z), 0.08, M["brass"])
    # skull keyhole: cranium + eye sockets + jaw slot, glowing crimson from inside
    glow = emissive("Glow", (0.55, 0.0, 0.015), 1.4)
    # R6-style skull: the classic Roblox head silhouette (upright rounded cylinder), pressed flat as an inlay
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.42, depth=0.66, location=(0, -0.47, -0.3))
    sk = bpy.context.active_object
    rb = sk.modifiers.new("Round", "BEVEL"); rb.width = 0.17; rb.segments = 8; rb.limit_method = "ANGLE"
    sk.scale = (1, 0.12, 1)
    link(sk, glow)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.47, -0.78))
    jaw = bpy.context.active_object
    jaw.scale = (0.42, 0.05, 0.36)
    bev = jaw.modifiers.new("B", "BEVEL"); bev.width = 0.08; bev.segments = 3
    link(jaw, glow)
    dark = P.material("Hole", base=(0.01, 0.005, 0.01), rough=0.9, wear=0.0, dirt=0.0)
    for x in (-0.16, 0.16):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.12, location=(x, -0.53, -0.3))
        e = bpy.context.active_object
        e.scale = (1.1, 0.3, 0.9)
        link(e, dark)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.07, depth=0.12, location=(0, -0.53, -0.47), rotation=(math.pi / 2, 0, math.pi))
    link(bpy.context.active_object, dark)
    for k in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.15 + k * 0.1, -0.53, -0.8))
        t = bpy.context.active_object
        t.scale = (0.02, 0.05, 0.3)
        link(t, dark)
    render("hud_tag.png")


PIECES = {
    "frame": lambda: frame(),
    "back": lambda: frame(back_only=True),
    "mini": mini,
    "socket": socket,
    "tag": tag,
}

if __name__ == "__main__":
    for n in (list(PIECES) if WHICH == "all" else [WHICH]):
        PIECES[n]()
