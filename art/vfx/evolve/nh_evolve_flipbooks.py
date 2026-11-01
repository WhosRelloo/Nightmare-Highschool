"""Tier-up flipbooks rendered with Cycles (Blender 5.x, headless).

usage: "E:/Blender/blender.exe" --background --factory-startup --python art/vfx/evolve/nh_evolve_flipbooks.py

  sprites/evo_bat_4x4.png      1024  a bat flapping, 16 frames (one wingbeat), white, soft-shaded (tinted dark in Roblox)
  sprites/evo_feather_4x4.png  1024  a feather tumbling, 16 frames, white with soft shading (Priest)
Each frame is 256 px, transparent, the subject kept well inside its cell so edges fade to nothing.
"""
import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sprites")
TMP = os.path.join(OUT, "_frames")
os.makedirs(TMP, exist_ok=True)
CELL = 256
FRAMES = 16


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = CELL
    sc.render.resolution_y = CELL
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    sc.world = w
    return sc


def white_mat(name, rough=0.6, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1)
    bs.inputs["Roughness"].default_value = rough
    m.diffuse_color = (0.9, 0.9, 0.9, 1)
    return m


def camera(sc, loc, target, scale):
    cd = bpy.data.cameras.new("C")
    cd.type = "ORTHO"
    cd.ortho_scale = scale
    co = bpy.data.objects.new("C", cd)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def key_light(sc, loc, energy):
    L = bpy.data.lights.new("K", "SUN")
    L.energy = energy
    L.angle = math.radians(30)
    o = bpy.data.objects.new("K", L)
    sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def montage(prefix, out_name):
    sheet = np.zeros((CELL * 4, CELL * 4, 4), np.float32)
    for f in range(FRAMES):
        im = bpy.data.images.load(os.path.join(TMP, f"{prefix}_{f:02d}.png"))
        px = np.array(im.pixels[:], np.float32).reshape(CELL, CELL, 4)[::-1]
        # soft cell edge: fade alpha to zero in the outer 10 px of each cell
        yy, xx = np.mgrid[0:CELL, 0:CELL]
        edge = np.minimum(np.minimum(xx, CELL - 1 - xx), np.minimum(yy, CELL - 1 - yy))
        px[..., 3] *= np.clip(edge / 10.0, 0, 1)
        # white sprites: keep shading in RGB, alpha as rendered
        r, c = divmod(f, 4)
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = px
    img = bpy.data.images.new(out_name, CELL * 4, CELL * 4, alpha=True)
    img.pixels[:] = sheet[::-1].ravel()
    img.filepath_raw = os.path.join(OUT, out_name)
    img.file_format = "PNG"
    img.save()
    print("[flipbook]", out_name)


# ------------------------------------------------------------------ bat

def bat_wing(side, beat):
    """A membrane wing: finger bones fan out from the shoulder; the trailing edge scallops between them."""
    bm = bmesh.new()
    s = 1 if side > 0 else -1
    lift = math.sin(beat) * 1.6          # wing up/down (a full, readable wingbeat)
    fold = 0.25 + 0.25 * (1 - math.cos(beat)) * 0.5
    shoulder = Vector((0.12 * s, 0, 0.05))
    elbow = shoulder + Vector((0.45 * s, 0.05, 0.25 * lift))
    fingers = []
    for k, (ang, L) in enumerate(((0.35, 0.75), (0.0, 0.85), (-0.45, 0.7), (-0.95, 0.55))):
        a = ang - fold * 0.4
        d = Vector((math.cos(a) * s, 0.0, math.sin(a))) * L
        d.z += lift * 0.55 * L
        fingers.append(elbow + d)
    body_back = Vector((0.08 * s, 0, -0.35))
    vs = [bm.verts.new(shoulder), bm.verts.new(elbow)]
    tips = [bm.verts.new(p) for p in fingers]
    back = bm.verts.new(body_back)
    # membrane panels between consecutive fingers, scalloped inward
    chain = tips + [back]
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        mid = (a.co + b.co) / 2
        toward = (elbow - mid).normalized() * (0.12 if i < len(chain) - 2 else 0.08)
        m = bm.verts.new(mid + toward)
        bm.faces.new((vs[1], a, m))
        bm.faces.new((vs[1], m, b))
    bm.faces.new((vs[0], vs[1], back))
    return bm


def render_bats():
    for f in range(FRAMES):
        sc = reset()
        beat = f / FRAMES * math.tau
        mat = white_mat("Bat", rough=0.7)
        for side in (-1, 1):
            bm = bat_wing(side, beat)
            me = bpy.data.meshes.new("W")
            bm.to_mesh(me)
            ob = bpy.data.objects.new("W", me)
            sc.collection.objects.link(ob)
            ob.data.materials.append(mat)
            sol = ob.modifiers.new("S", "SOLIDIFY")
            sol.thickness = 0.015
        # body, head, ears
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, -0.1))
        b = bpy.context.active_object
        b.scale = (0.85, 0.8, 1.6)
        b.data.materials.append(mat)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0, -0.02, 0.17))
        bpy.context.active_object.data.materials.append(mat)
        for s in (-1, 1):
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, depth=0.12, location=(0.045 * s, -0.01, 0.28), rotation=(0, 0.25 * s, 0))
            bpy.context.active_object.data.materials.append(mat)
        camera(sc, (0.6, -4, 1.4), (0, 0, 0.05), 3.6)
        key_light(sc, (1.5, -2, 3), 3.0)
        sc.render.filepath = os.path.join(TMP, f"bat_{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    montage("bat", "evo_bat_4x4.png")


# ------------------------------------------------------------------ feather

def feather_mesh():
    bm = bmesh.new()
    n = 40
    L = 1.6
    left, right, spine = [], [], []
    for i in range(n + 1):
        t = i / n
        z = -L / 2 + t * L
        curve = 0.08 * math.sin(t * math.pi)            # gentle arc
        width = 0.26 * math.sin(min(1, t * 1.15) * math.pi) ** 0.7 * (1 - 0.3 * t)
        notch = 0.03 * math.sin(t * 37) * (t > 0.15)    # ragged barbs
        spine.append(bm.verts.new((curve, 0, z)))
        left.append(bm.verts.new((curve - width - notch, 0.04 * width, z + 0.06 * width)))
        right.append(bm.verts.new((curve + width * 0.8 + notch * 0.6, 0.03 * width, z + 0.05 * width)))
    for i in range(n):
        bm.faces.new((left[i], spine[i], spine[i + 1], left[i + 1]))
        bm.faces.new((spine[i], right[i], right[i + 1], spine[i + 1]))
    return bm


def render_feathers():
    for f in range(FRAMES):
        sc = reset()
        t = f / FRAMES
        mat = white_mat("Feather", rough=0.85)
        bm = feather_mesh()
        me = bpy.data.meshes.new("F")
        bm.to_mesh(me)
        ob = bpy.data.objects.new("F", me)
        sc.collection.objects.link(ob)
        ob.data.materials.append(mat)
        sol = ob.modifiers.new("S", "SOLIDIFY")
        sol.thickness = 0.01
        sub = ob.modifiers.new("Sub", "SUBSURF")
        sub.levels = 1
        sub.render_levels = 1
        # tumble: spin round its length, rock side to side
        ob.rotation_euler = (math.sin(t * math.tau) * 0.5, t * math.tau, 0.6 + math.sin(t * math.tau * 2) * 0.25)
        camera(sc, (0, -4, 0), (0, 0, 0), 2.2)
        key_light(sc, (1.2, -2, 2.5), 3.5)
        sc.render.filepath = os.path.join(TMP, f"feather_{f:02d}.png")
        bpy.ops.render.render(write_still=True)
    montage("feather", "evo_feather_4x4.png")


import sys as _s
_only = _s.argv[_s.argv.index('--') + 1] if '--' in _s.argv else 'all'
if _only in ('all', 'bat'):
    render_bats()
if _only in ('all', 'feather'):
    render_feathers()
