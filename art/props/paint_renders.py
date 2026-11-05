"""The 3D source for the art kit's still life (props batch 21), rendered in Blender from the props library and then
painted over by paint_canvases.py (which also paints the raven onto the skull):

  _paint_raven_still.png    a skull, an open book, a closed book and a guttering candle on crimson velvet and black
                            marble, lit by the candle alone (a cool fill from the left)

  "E:/Blender/blender.exe" -b --factory-startup --python art/props/paint_renders.py -- PaintRenders --gpu
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402
from nh_props import box, set_group  # noqa: E402
from nh_props_batch3 import sphere  # noqa: E402
from nh_props_batch4 import _book, flat, _mark, _xform  # noqa: E402
from nh_props_batch9 import raven, candle, wax_mat  # noqa: E402
from nh_props_batch10 import _skull, black_marble, founder_bust, velvet  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")


def _camera(loc, target, lens=50, ortho=None):
    cam = bpy.data.cameras.new("Cam")
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    co = bpy.data.objects.new("Cam", cam)
    bpy.context.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co


def _light(kind, loc, energy, color, size=0.1, target=None):
    L = bpy.data.lights.new(kind, kind)
    L.energy, L.color = energy, color
    if kind == "POINT":
        L.shadow_soft_size = size
    elif kind == "AREA":
        L.size = size
    o = bpy.data.objects.new(kind, L)
    o.location = loc
    bpy.context.collection.objects.link(o)
    if target:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def _emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Emission Color"].default_value = (*rgb, 1)
    bs.inputs["Emission Strength"].default_value = strength
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    return m


def _smooth_all(subdivide=()):
    """Smooth shading on every mesh (the props get it when joined; these scenes aren't), and subdivision on the named
    parts so close-up forms are round, not faceted."""
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for poly in o.data.polygons:
            poly.use_smooth = True
        if any(o.name.startswith(n) for n in subdivide):
            md = o.modifiers.new("Sub", "SUBSURF")
            md.levels = md.render_levels = 2


def _render(path, px, transparent=False, samples=96):
    sc = bpy.context.scene
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = px
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.render.film_transparent = transparent
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def _fine_skull(prefix, mtx, bone, dark):
    """A closer-to-life skull for the painting (facing -Y, resting on the origin): an elongated cranium, brow ridges,
    recessed sockets, cheekbones, the nasal cavity, upper and lower teeth and the mandible."""
    from nh_props_batch3 import sphere, cone
    from nh_props import tube
    s = _mark()
    sphere(f"{prefix}Cranium", 0.2, (0, 0.06, 0.3), bone, seg=24, rings=14, scale=(0.84, 1.18, 0.95))
    sphere(f"{prefix}Forehead", 0.16, (0, -0.08, 0.32), bone, seg=20, rings=10, scale=(0.95, 0.7, 0.9))
    tube(f"{prefix}Brow", [(-0.12, -0.155, 0.265), (-0.05, -0.18, 0.272), (0.05, -0.18, 0.272), (0.12, -0.155, 0.265)], 0.03, bone)
    for sx in (-1, 1):
        sphere(f"{prefix}Socket{sx}", 0.046, (sx * 0.062, -0.168, 0.225), dark, seg=14, rings=8, scale=(1.05, 0.55, 0.9))
        sphere(f"{prefix}Cheek{sx}", 0.05, (sx * 0.105, -0.12, 0.175), bone, seg=12, rings=6, scale=(0.8, 1.4, 0.6))
        tube(f"{prefix}Zyg{sx}", [(sx * 0.11, -0.12, 0.18), (sx * 0.14, -0.05, 0.19), (sx * 0.15, 0.02, 0.2)], 0.02, bone)
        sphere(f"{prefix}Temple{sx}", 0.1, (sx * 0.1, 0.0, 0.27), bone, seg=14, rings=8, scale=(0.5, 1.0, 0.9))
    sphere(f"{prefix}Maxilla", 0.08, (0, -0.15, 0.135), bone, seg=16, rings=8, scale=(1.05, 0.7, 0.75))
    cone(f"{prefix}Nasal", 0.03, 0.0, 0.06, (0, -0.205, 0.175), dark, verts=3, rot=(math.radians(-90), 0, math.pi))
    for k in range(8):
        a = (k - 3.5) / 8 * 1.6
        x, y = math.sin(a) * 0.075, -0.2 + (1 - math.cos(a)) * 0.07
        sphere(f"{prefix}Upper{k}", 0.014, (x, y, 0.098), bone, seg=8, rings=5, scale=(0.9, 0.7, 1.6))
        sphere(f"{prefix}Lower{k}", 0.013, (x * 0.95, y + 0.008, 0.066), bone, seg=8, rings=5, scale=(0.9, 0.7, 1.5))
    tube(f"{prefix}Jaw", [(-0.11, 0.02, 0.12), (-0.1, -0.08, 0.05), (-0.05, -0.17, 0.03), (0.05, -0.17, 0.03), (0.1, -0.08, 0.05), (0.11, 0.02, 0.12)],
         0.032, bone)
    sphere(f"{prefix}Chin", 0.04, (0, -0.185, 0.035), bone, seg=10, rings=6, scale=(1.3, 0.8, 0.8))
    _xform(s, mtx)


def raven_still():
    P.PARTS.clear()
    P._img_cache.clear()
    P.reset()
    M = P.palette()
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.006, 1)
    bpy.context.scene.world = w
    bone = flat("Bone", (0.62, 0.55, 0.42), 0.6, dirt=0.6)
    dark = flat("Socket", (0.01, 0.008, 0.008), 0.9)
    box("Table", (3.2, 1.8, 0.12), (0, 0.2, -0.06), black_marble(), bevel=0.02)
    box("Velvet", (2.2, 1.3, 0.012), (0.05, 0.15, 0.006), velvet(), bevel=0.004, rot=(0, 0, 0.05))
    box("Wall", (6, 0.1, 4), (0, 1.3, 1.5), flat("Plaster", (0.035, 0.028, 0.022), 0.95), bevel=0)
    _fine_skull("Skull", Matrix.Translation((-0.05, 0.05, 0.03)) @ Matrix.Rotation(0.6, 4, "Z"), bone, dark)
    # a quill in a brass inkwell behind the skull
    from nh_props_batch4 import lathe
    from nh_props import tube
    lathe("Inkwell", [(0, 0), (0.09, 0), (0.1, 0.06), (0.06, 0.1), (0.04, 0.12), (0, 0.12)], M["brass"], seg=20, loc=(-0.38, 0.35, 0.012))
    tube("Quill", [(-0.37, 0.35, 0.1), (-0.33, 0.37, 0.4), (-0.25, 0.4, 0.7)], 0.006, flat("QuillShaft", (0.8, 0.76, 0.66), 0.5))
    tube("Vane", [(-0.36, 0.36, 0.3), (-0.31, 0.38, 0.5), (-0.26, 0.4, 0.68)], 0.03, flat("Vane", (0.06, 0.06, 0.07), 0.6))
    # the open book, left: two page blocks tilted up to a spine, a crimson cover beneath
    s = _mark()
    box("Cover", (0.82, 0.56, 0.02), (0, 0, 0.01), M["leather"], bevel=0.008)
    for sx in (-1, 1):
        box(f"Pages{sx}", (0.38, 0.52, 0.05), (sx * 0.2, 0, 0.05), M["paper"], bevel=0.01, rot=(0, -sx * 0.12, 0))
    _xform(s, Matrix.Translation((-0.62, -0.18, 0.012)) @ Matrix.Rotation(-0.25, 4, "Z"))
    s = _mark()
    _book("Closed", 0.5, 0.36, 0.12, M["inkblue"], M, corners=True)
    _xform(s, Matrix.Translation((0.75, 0.32, 0.012)) @ Matrix.Rotation(0.5, 4, "Z"))
    # the candle and a brass stick, the flame emissive with its light
    cx, cy = 0.42, -0.08
    box("CandleFoot", (0.18, 0.18, 0.03), (cx, cy, 0.027), M["brass"], bevel=0.012)
    tip = candle("Candle", cx, cy, 0.04, 0.5, wax_mat(), r=0.045)
    sphere("Flame", 0.025, (cx, cy, tip + 0.06), _emissive("FlameE", (1.0, 0.62, 0.25), 60), seg=10, rings=6, scale=(1, 1, 2.4))
    _light("POINT", (cx, cy, tip + 0.07), 9.0, (1.0, 0.62, 0.3), size=0.03)
    _light("AREA", (-2.2, -1.4, 1.3), 18, (0.45, 0.45, 0.75), size=1.6, target=(0, 0, 0.3))
    _smooth_all(("Skull", "Flame"))
    _camera((0.05, -2.2, 0.58), (0.02, 0.1, 0.4), lens=55)
    _render(os.path.join(OUT, "_paint_raven_still.png"), (1536, 2048), samples=64)


want = [a for a in sys.argv[sys.argv.index("--") + 2:] if not a.startswith("--")] if "--" in sys.argv else []
for fn in (raven_still,):
    if not want or fn.__name__ in want:
        fn()
