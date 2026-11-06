"""TerrestrialGlobe's sphere with its own maps (1.50.3; Blender 5.x, run headless).

usage (the maps need Pillow, so they're made with the system Python first):
  python art/props/globe_sphere.py
  "E:/Blender/blender.exe" --background --factory-startup --python art/props/globe_sphere.py

Batch 30 baked the globe's sphere into the prop's shared atlas through a smart-UV unwrap. That cut the sphere into curved
gores and flattened them with a strong one-way squash, so in Roblox (maps served at 1024) the lettering and coastlines
smeared along one direction. This rebuilds just the sphere piece (TerrestrialGlobe_Globe, the sphere and its two brass axis
pins) exactly as batch 30 placed it, with the UV sphere's own equirectangular layout, and gives it its own maps straight
from the printed globe (textures/LibraryGlobe_color.png, 4096 x 2048):
  - the map fills v 0 to 0.97; the top strip (v 0.97 to 1) is brass for the pins;
  - colour graded 0.95 / 0.95 / 0.92 to the baked atlas's varnished tone;
  - roughness 0.35 with a faint grain (the batch 30 value), metalness 0 on the map and 1 on the brass;
  - a faint paper grain in the normal map.
Writes fbx/TerrestrialGlobeSphere.fbx (one mesh, named TerrestrialGlobe_Globe), textures/TerrestrialGlobeSphere_*.png and
previews/TerrestrialGlobeSphere.png. The stand (TerrestrialGlobe_Main) keeps the batch 30 atlas.
"""
import math
import os

import sys

import numpy as np

try:
    import bpy
    from mathutils import Matrix, Vector
except ImportError:  # the system Python: maps only
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 2048
MAP_TOP = 0.97                      # the map's share of the texture height; above it, the brass strip
ZC, R = 3.3, 1.2                    # batch 30's sphere centre and radius
TILT = 23.4 * math.pi / 180
XF = Matrix.Translation((0, 0, ZC)) @ Matrix.Rotation(TILT, 4, "Y") if bpy else None


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=R, location=(0, 0, 0))
    g = bpy.context.active_object
    me = g.data
    uv = me.uv_layers.active
    for d in uv.data:
        d.uv = (d.uv[0], d.uv[1] * MAP_TOP)
    for p in me.polygons:
        p.use_smooth = True
    g.matrix_world = XF
    parts = [g]
    ax = Vector((math.sin(TILT), 0, math.cos(TILT)))
    for sgn in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.05, location=tuple(Vector((0, 0, ZC)) + ax * sgn * (R + 0.06)))
        p = bpy.context.active_object
        for d in p.data.uv_layers.active.data:
            d.uv = (0.5, (MAP_TOP + 1) / 2)
        for f in p.data.polygons:
            f.use_smooth = True
        parts.append(p)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = g
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    g.name = g.data.name = "TerrestrialGlobe_Globe"
    return g


def maps():
    from PIL import Image, ImageFilter
    src = Image.open(os.path.join(HERE, "textures", "LibraryGlobe_color.png")).convert("RGB")
    rows = round(SIZE * MAP_TOP)
    body = np.asarray(src.resize((SIZE, rows), Image.LANCZOS)).astype(float) * np.array([0.95, 0.95, 0.92])
    brass = np.zeros((SIZE - rows, SIZE, 3)) + np.array([176, 132, 62])
    col = np.vstack([brass, body]).clip(0, 255).astype("uint8")
    rng = np.random.default_rng(31)
    grain = np.asarray(Image.fromarray((rng.random((SIZE, SIZE)) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255 - 0.5
    rough = np.full((SIZE, SIZE), 0.35) + grain * 0.06
    rough[: SIZE - rows] = 0.3
    metal = np.zeros((SIZE, SIZE))
    metal[: SIZE - rows] = 1.0
    # a faint grain as a height field -> tangent-space normals
    h = grain * 0.25
    dx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
    dy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    n = np.dstack([-dx, dy, np.full_like(h, 1.0)])
    n[: SIZE - rows] = (0, 0, 1)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    out = os.path.join(HERE, "textures", "TerrestrialGlobeSphere_%s.png")
    Image.fromarray(col).save(out % "color")
    Image.fromarray(((n + 1) * 127.5).clip(0, 255).astype("uint8")).save(out % "normal")
    Image.fromarray((rough * 255).clip(0, 255).astype("uint8")).save(out % "rough")
    Image.fromarray((metal * 255).astype("uint8")).save(out % "metal")
    return out


def material(g, out):
    m = bpy.data.materials.new("GlobeSphere")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    def tex(k, colour=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(out % k)
        if not colour:
            t.image.colorspace_settings.name = "Non-Color"
        return t
    nt.links.new(tex("color", True).outputs["Color"], bs.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex("rough").outputs["Color"], bs.inputs["Roughness"])
    nt.links.new(tex("metal").outputs["Color"], bs.inputs["Metallic"])
    g.data.materials.clear()
    g.data.materials.append(m)


def export_and_preview(g):
    bpy.ops.object.select_all(action="DESELECT")
    g.select_set(True)
    bpy.context.view_layer.objects.active = g
    bpy.ops.export_scene.fbx(filepath=os.path.join(HERE, "fbx", "TerrestrialGlobeSphere.fbx"), use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, global_scale=1.0, axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
                             path_mode="STRIP", embed_textures=False)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.07, 1)
    L = bpy.data.lights.new("Key", "AREA")
    L.energy, L.size, L.color = 900, 3, (1.0, 0.85, 0.65)
    o = bpy.data.objects.new("Key", L)
    sc.collection.objects.link(o)
    o.location = (2.5, -3.5, 5.5)
    o.rotation_euler = (Vector((0, 0, ZC)) - o.location).to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    sc.collection.objects.link(co)
    co.location = (2.2, -5.2, 4.2)
    co.rotation_euler = (Vector((0, 0, ZC)) - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(HERE, "previews", "TerrestrialGlobeSphere.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    if bpy is None:
        maps()
        print("[globe] maps written")
        sys.exit(0)
    g = build()
    out = os.path.join(HERE, "textures", "TerrestrialGlobeSphere_%s.png")
    material(g, out)
    export_and_preview(g)
    print("[globe] TerrestrialGlobe_Globe:", sum(len(p.vertices) - 2 for p in g.data.polygons), "tris, dims", tuple(round(v, 3) for v in g.dimensions))
