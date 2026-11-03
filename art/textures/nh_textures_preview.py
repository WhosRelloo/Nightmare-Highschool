"""Lit previews of the texture sets, shot the same way as the props (art/props/nh_props.py preview): Cycles, a dark
world, a warm candle key, a blue-violet fill and a crimson rim. Each set is shown on a bevelled block standing on a
floor of the same material (3 x 3 repeats, so the tiling shows), then one contact sheet: art/textures/_lit_sheet.png.

    "E:/Blender/blender.exe" -b --factory-startup --python art/textures/nh_textures_preview.py
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
NAMES = [d for d in sorted(os.listdir(OUT), key=lambda d: os.path.getctime(os.path.join(OUT, d)))
         if os.path.isdir(os.path.join(OUT, d)) and not d.startswith("_") and os.path.exists(os.path.join(OUT, d, f"{d}_color.png"))]
W, H = 480, 380

sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'CYCLES'
sc.cycles.samples = 40
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
w = bpy.data.worlds.new("W"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.028, 0.045, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

size = 2.0
target = Vector((0, 0, 0.6))


def light(kind, loc, energy, color, s=2.0):
    L = bpy.data.lights.new(kind, kind)
    L.energy = energy
    L.color = color
    L.size = s
    o = bpy.data.objects.new(kind, L)
    o.location = loc
    bpy.context.collection.objects.link(o)
    o.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


light("AREA", (size * 1.2, -size * 1.4, size * 1.3), 400 * size, (1.0, 0.82, 0.6), s=size)     # warm candle key
light("AREA", (-size * 1.4, -size * 0.6, size * 0.9), 160 * size, (0.55, 0.55, 0.9), s=size)   # blue-violet fill
light("AREA", (0, size * 1.5, size * 1.4), 260 * size, (0.9, 0.3, 0.35), s=size)               # crimson rim

bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
floor = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.6))
block = bpy.context.active_object
bev = block.modifiers.new("Bevel", "BEVEL")
bev.width = 0.05
bev.segments = 3
block.rotation_euler = (0, 0, math.radians(28))

cam = bpy.data.cameras.new("C")
cam.lens = 50
co = bpy.data.objects.new("C", cam)
bpy.context.collection.objects.link(co)
co.location = (size * 1.15, -size * 1.65, size * 0.95)
co.rotation_euler = (Vector((0, 0, 0.45)) - co.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = co


def material(name, repeat):
    m = bpy.data.materials.new(f"{name}{repeat}")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (repeat, repeat, repeat)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])

    def img(kind, data):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(OUT, name, f"{name}_{kind}.png"), check_existing=True)
        if data:
            t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    nt.links.new(img("color", False).outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(img("rough", True).outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(img("metal", True).outputs["Color"], bsdf.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(img("normal", True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


tiles = []
for name in NAMES:
    floor.data.materials.clear(); floor.data.materials.append(material(name, 3))
    block.data.materials.clear(); block.data.materials.append(material(name, 1))
    path = os.path.join(OUT, "_lit", f"{name}.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    tiles.append(np.array(im.pixels[:], np.float32).reshape(H, W, 4))
    print("rendered", name)

cols = 4
rows = math.ceil(len(tiles) / cols)
sheet = np.zeros((rows * H, cols * W, 4), np.float32)
sheet[..., 3] = 1
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    r = rows - 1 - r                      # Blender images are bottom-up
    sheet[r * H:(r + 1) * H, c * W:(c + 1) * W] = t
img = bpy.data.images.new("_lit_sheet", cols * W, rows * H, alpha=False)
img.pixels.foreach_set(sheet.ravel())
img.filepath_raw = os.path.join(OUT, "_lit_sheet.png")
img.file_format = 'PNG'
img.save()
print("wrote _lit_sheet.png")
