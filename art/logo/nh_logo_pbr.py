"""Nightmare High logo, PBR relief render (Blender 5.x, Cycles, headless).

usage: python art/logo/bake_relief.py 2
       "E:/Blender/blender.exe" --background --factory-startup --python art/logo/nh_logo_pbr.py -- [--samples 64] [--size 1400]
-> art/logo/out/nh_logo_pbr.png (transparent)

The owner's 2D logo (art/logo/source.png) becomes a sculpted relief: the wings and scrollwork at the back, the
quartered shield plate, the spike and the banner in front, the lettering raised on the banner. Materials match
UI kit2 (art/props/nh_props.py box-projected PBR sets): black iron, crimson enamel (glossy, slightly metallic,
worn at the edges), silver lettering.
"""
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "props")))
import nh_props as P  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 64
SIZE = int(argv[argv.index("--size") + 1]) if "--size" in argv else 1400
B = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

H = np.load(os.path.join(B, "height.npy"))
MAT = np.load(os.path.join(B, "matid.npy"))
SIL = np.load(os.path.join(B, "sil.npy")).astype(bool)
h, w = H.shape
WIDTH = 10.0
px = WIDTH / w
DEPTH = 1.6          # height map units -> scene units


def reset():
    P._img_cache.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = SIZE
    sc.render.resolution_y = int(SIZE * h / w)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    wd = bpy.data.worlds.new("W"); wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.07, 1)
    wd.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    sc.world = wd
    return sc


def build_mesh():
    """one vertex per pixel inside the silhouette (plus a 1px rim), faces where all four corners are in."""
    keep = SIL.copy()
    idx = -np.ones((h, w), np.int64)
    ys, xs = np.nonzero(keep)
    idx[ys, xs] = np.arange(len(xs))
    verts = np.zeros((len(xs), 3), np.float32)
    verts[:, 0] = (xs - w / 2) * px
    verts[:, 2] = (h / 2 - ys) * px
    verts[:, 1] = -H[ys, xs] * DEPTH
    q = (idx[:-1, :-1] >= 0) & (idx[:-1, 1:] >= 0) & (idx[1:, 1:] >= 0) & (idx[1:, :-1] >= 0)
    qy, qx = np.nonzero(q)
    faces = np.stack([idx[qy, qx], idx[qy + 1, qx], idx[qy + 1, qx + 1], idx[qy, qx + 1]], 1)
    me = bpy.data.meshes.new("Logo")
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(faces.size)
    me.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", (np.arange(len(faces)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(faces), 4, np.int32))
    # material per face from the pixel colour class (majority of the 4 corners)
    m = np.stack([MAT[qy, qx], MAT[qy + 1, qx], MAT[qy + 1, qx + 1], MAT[qy, qx + 1]], 1)
    mid = np.apply_along_axis(lambda r: np.bincount(r, minlength=3).argmax(), 1, m) if len(m) < 0 else \
        np.where((m == 2).sum(1) >= 2, 2, np.where((m == 1).sum(1) >= 2, 1, 0))
    me.polygons.foreach_set("material_index", mid.astype(np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(faces), bool))
    uvl = me.uv_layers.new(name="UV")
    vi = faces.ravel()
    uvs = np.stack([(xs[vi] + 0.5) / w, 1 - (ys[vi] + 0.5) / h], 1).astype(np.float32)
    uvl.data.foreach_set("uv", uvs.ravel())
    me.update(calc_edges=True)
    me.validate()
    ob = bpy.data.objects.new("Logo", me)
    bpy.context.collection.objects.link(ob)
    # a thin backing slab so the relief reads as a solid piece from an angle
    sol = ob.modifiers.new("Solid", "SOLIDIFY"); sol.thickness = 0.08; sol.offset = 1
    return ob


def materials():
    """one PBR material driven by maps baked from the art: albedo (painted highlights tamed), metal, roughness,
    lacquer on the crimson; a fine box-projected grunge from the kit's iron set breaks up the roughness."""
    mt = bpy.data.materials.new("LogoPBR"); mt.use_nodes = True
    nt = mt.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]
    uv = N.new("ShaderNodeTexCoord")
    alb = N.new("ShaderNodeTexImage"); alb.image = bpy.data.images.load(os.path.join(B, "albedo.png"))
    alb.interpolation = "Cubic"
    pk = N.new("ShaderNodeTexImage"); pk.image = bpy.data.images.load(os.path.join(B, "maskpack.png"))
    pk.image.colorspace_settings.name = "Non-Color"; pk.interpolation = "Cubic"
    for t in (alb, pk):
        L.new(uv.outputs["UV"], t.inputs["Vector"])
    sep = N.new("ShaderNodeSeparateColor"); L.new(pk.outputs["Color"], sep.inputs["Color"])
    L.new(alb.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(sep.outputs["Green"], bsdf.inputs["Metallic"])
    # grunge: noise multiplies roughness a little so the surfaces aren't plastic-perfect
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60; nz.inputs["Detail"].default_value = 8
    mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.8; mr.inputs["To Max"].default_value = 1.25
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(sep.outputs["Blue"], mul.inputs[0]); L.new(mr.outputs["Result"], mul.inputs[1])
    L.new(mul.outputs["Value"], bsdf.inputs["Roughness"])
    L.new(sep.outputs["Red"], bsdf.inputs["Coat Weight"])
    bsdf.inputs["Coat Roughness"].default_value = 0.06
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08; bump.inputs["Distance"].default_value = 0.02
    L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return [mt]


def lights(sc, s):
    def area(loc, e, c, size):
        L = bpy.data.lights.new("A", "AREA"); L.energy = e; L.color = c; L.size = size
        o = bpy.data.objects.new("A", L); sc.collection.objects.link(o); o.location = loc
        from mathutils import Vector
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area((-s * 0.5, -s * 0.9, s * 0.8), 95 * s, (1.0, 0.88, 0.74), s)      # warm key, top-left
    area((s * 0.7, -s * 0.6, -s * 0.4), 24 * s, (0.6, 0.55, 0.9), s)      # violet fill
    area((0, s * 0.6, s * 0.3), 30 * s, (0.95, 0.3, 0.32), s)             # crimson rim
    area((0, -s * 1.6, 0.2 * s), 55 * s, (1.0, 0.97, 0.95), s * 1.6)       # soft front fill so the reds stay vivid


def main():
    sc = reset()
    ob = build_mesh()
    for mt in materials():
        ob.data.materials.append(mt)
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = WIDTH * 1.02
    co = bpy.data.objects.new("C", cd); sc.collection.objects.link(co)
    co.location = (0, -20, 0); co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    lights(sc, 10)
    sc.render.filepath = os.path.join(OUT, "nh_logo_pbr.png")
    bpy.ops.render.render(write_still=True)
    print("[logo] rendered", sc.render.filepath)


main()
