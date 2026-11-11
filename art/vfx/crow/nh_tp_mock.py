"""Mock-up stills of the two teleport effects, for the design review (Blender 5.x, headless, after the bakes).

  "E:/Blender/blender.exe" --background --factory-startup --python art/vfx/crow/nh_tp_mock.py -- [--gpu] [--out E:/NH-Work/crow]

Six panels: the admin's crows (leave: bursting / scattering; arrive: swirling in / re-forming) and the owner's
bats (leave: the vortex over the sigil; arrive: diving in). A blocky stand-in student, the baked NHCrow and NHBat.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_crow as C  # noqa: E402
import nh_bat as B  # noqa: E402

OUT = C.OUT
PREV = os.path.join(OUT, "prev")


def load(blend, names):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    objs = {}
    for o in dst.objects:
        objs[o.name] = o
    return objs


def mat(name, color, rough=0.6, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = (*emit, 1)
        bs.inputs["Emission Strength"].default_value = strength
    return m


def dissolve_mat(name, color, cut, scale=6.0):
    """Principled mixed to transparent where a noise is under `cut` (0 = whole, 1 = gone), a sooty edge."""
    m = mat(name, color)
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4
    ramp = nt.nodes.new("ShaderNodeMath")
    ramp.operation = "GREATER_THAN"
    ramp.inputs[1].default_value = cut * 0.9 + 0.2 if cut > 0 else -1
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bs.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("b", "BEVEL")
    bev.width = 0.08
    bev.segments = 2
    o.data.materials.append(m)
    return o


def student(at, cut=0.0, head_cut=None):
    """An R6 stand-in in the school's black blazer, grey trousers, crimson tie."""
    x, y, z = at
    parts = []
    blazer = dissolve_mat("Blazer", (0.012, 0.012, 0.016), cut)
    trous = dissolve_mat("Trousers", (0.04, 0.04, 0.045), cut)
    skin = dissolve_mat("Skin", (0.55, 0.40, 0.33), cut if head_cut is None else head_cut)
    tie = dissolve_mat("Tie", (0.22, 0.02, 0.04), cut)
    parts.append(box("Torso", (2, 1, 2), (x, y, z + 3), blazer))
    parts.append(box("Tie", (0.3, 0.05, 1.3), (x, y - 0.52, z + 3.2), tie))
    parts.append(box("Head", (1.15, 1.15, 1.15), (x, y, z + 4.6), skin))
    hair = dissolve_mat("Hair", (0.01, 0.008, 0.01), cut if head_cut is None else head_cut)
    parts.append(box("Hair", (1.25, 1.25, 0.45), (x, y + 0.05, z + 5.15), hair))
    for s in (-1, 1):
        parts.append(box(f"Arm{s}", (1, 1, 2), (x + s * 1.5, y, z + 3), blazer))
        parts.append(box(f"Leg{s}", (1, 1, 2), (x + s * 0.5, y, z + 1), trous))
    return parts


def ground(sigil=False):
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    g = bpy.context.active_object
    m = mat("Stone", (0.03, 0.028, 0.032), rough=0.85)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 0.35
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (0.012, 0.011, 0.013, 1)
    rp.color_ramp.elements[1].color = (0.05, 0.047, 0.052, 1)
    nt.links.new(v.outputs["Distance"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bs.inputs["Base Color"])
    g.data.materials.append(m)
    if sigil:
        glow = mat("Sigil", (0.05, 0.0, 0.01), emit=(0.85, 0.06, 0.12), strength=6)
        for r, w in ((4.2, 0.08), (3.6, 0.05), (2.2, 0.06)):
            bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=w, location=(0, 0, 0.02))
            t = bpy.context.active_object
            t.scale.z = 0.05
            t.data.materials.append(glow)
        # a crescent and a ring of runic ticks between the circles
        for k in range(24):
            a = k / 24 * 2 * math.pi
            L = 0.35 if k % 3 else 0.6
            bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 3.9, math.sin(a) * 3.9, 0.02))
            t = bpy.context.active_object
            t.scale = (L, 0.05, 0.01)
            t.rotation_euler.z = a
            t.data.materials.append(glow)
        for k in range(6):
            a = k / 6 * 2 * math.pi + 0.3
            bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * 2.9, math.sin(a) * 2.9, 0.02))
            t = bpy.context.active_object
            t.scale = (0.5, 0.18, 0.01)
            t.rotation_euler.z = a + math.pi / 2
            t.data.materials.append(glow)


def mist(at, r, density=0.12, color=(0.02, 0.02, 0.03), emit=None, h=1.5):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(at[0], at[1], at[2] + h / 2))
    o = bpy.context.active_object
    o.scale = (r, r, h / 2)
    m = bpy.data.materials.new("Mist")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*color, 1)
    if emit:
        vol.inputs["Emission Color"].default_value = (*emit, 1)
        vol.inputs["Emission Strength"].default_value = 0.05
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.2
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    co = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(nz.outputs["Fac"], mul.inputs[0])
    nt.links.new(gr.outputs["Fac"], mul.inputs[1])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = density * 2.5
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(mul2.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    return o


def feather_mat():
    return mat("Feather", (0.008, 0.008, 0.011), rough=0.5)


def feathers(center, n, spread, rnd, m):
    for k in range(n):
        p = Vector(center) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread
        bpy.ops.mesh.primitive_plane_add(size=1, location=p)
        o = bpy.context.active_object
        o.scale = (0.07, 0.26, 1)
        o.rotation_euler = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
        o.data.materials.append(m)


def flock(src, rigname, posefn, items, rnd):
    """items: (position, velocity direction, scale, phase); each bird its own rig copy (its own pose)."""
    mesh0, rig0 = src
    for k, (p, d, s, ph) in enumerate(items):
        ao = rig0.copy()
        bpy.context.scene.collection.objects.link(ao)
        ob = mesh0.copy()
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = ao
        ob.matrix_parent_inverse.identity()
        ob.location = (0, 0, 0)
        ob.modifiers["Armature"].object = ao
        d = Vector(d).normalized()
        # the birds face -Y: turn -Y onto the flight direction, banked a little
        q = Vector((0, -1, 0)).rotation_difference(d)
        ao.rotation_mode = "QUATERNION"
        ao.rotation_quaternion = q
        ao.location = p
        ao.scale = (s, s, s)
        posefn(ao, ph)


def light_night(sc):
    w = bpy.data.worlds.new("Night")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.011, 0.020, 1)
    sc.world = w
    def add(kind, rot, energy, color, loc=(0, 0, 0), size=None):
        ld = bpy.data.lights.new(kind, kind)
        ld.energy = energy
        ld.color = color
        if size and kind == "SUN":
            ld.angle = size
        lo = bpy.data.objects.new(kind, ld)
        lo.rotation_euler = rot
        lo.location = loc
        sc.collection.objects.link(lo)
    add("SUN", (math.radians(50), 0, math.radians(140)), 2.2, (0.62, 0.70, 1.0), size=0.05)       # moonlight
    add("SUN", (math.radians(75), 0, math.radians(-30)), 1.2, (0.55, 0.62, 0.9), size=0.1)        # rim from behind
    add("POINT", (0, 0, 0), 600, (1.0, 0.62, 0.36), loc=(-9, -4, 4))                            # a distant lamp
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"


def scene_reset():
    for o in list(bpy.context.scene.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def render(name, cam_loc, target, lens=35, res=(960, 640)):
    sc = bpy.context.scene
    light_night(sc)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.film_transparent = False
    C.camera(sc, cam_loc, target, lens)
    p = os.path.join(PREV, f"mock_{name}.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    return p


def around_body(rnd):
    """A random point inside the stand-in's silhouette."""
    pick = rnd.random()
    if pick < 0.45:
        return Vector((rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5), rnd.uniform(2, 4)))
    if pick < 0.6:
        return Vector((rnd.uniform(-0.55, 0.55), rnd.uniform(-0.55, 0.55), rnd.uniform(4.1, 5.2)))
    if pick < 0.8:
        s = rnd.choice((-1, 1))
        return Vector((s * 1.5 + rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(2, 4)))
    s = rnd.choice((-1, 1))
    return Vector((s * 0.5 + rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 2)))


def main():
    sc = C.reset()
    crow_objs = load(os.path.join(OUT, "NHCrow.blend"), {"NHCrow", "NHCrowRig"})
    bat_objs = load(os.path.join(OUT, "NHBat.blend"), {"NHBat", "NHBatRig"})
    crow = (crow_objs["NHCrow"], crow_objs["NHCrowRig"])
    bat = (bat_objs["NHBat"], bat_objs["NHBatRig"])
    for o in (crow[1], bat[1]):
        o.location = (0, 0, -500)       # the originals, out of shot (their meshes follow as children)
    cam = ((7.5, -11.5, 4.2), (0, 0, 3.2))
    out = []

    # 1. crows, leaving: the student breaking apart as the flock bursts out of them
    rnd = random.Random(3)
    scene_reset()
    ground()
    student((0, 0, 0), cut=0.38)
    items = []
    for k in range(30):
        p = around_body(rnd)
        d = (p - Vector((0, 0, 3))) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0.6))
        p = p + d.normalized() * rnd.uniform(0.2, 1.6)
        items.append((p, d, rnd.uniform(0.5, 0.72), rnd.uniform(0, 6.28)))
    flock(crow, "c", C.pose, items, rnd)
    feathers((0, 0, 3.2), 18, 2.2, rnd, feather_mat())
    mist((0, 0, 0), 2.6, density=0.06, h=2.0)
    out.append(render("crow_leave_burst", *cam))

    # 2. crows, leaving: the flock scattering up and away; only drifting feathers where they stood
    rnd = random.Random(4)
    scene_reset()
    ground()
    items = []
    for k in range(32):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(2.5, 9)
        p = Vector((math.cos(a) * r, math.sin(a) * r * 0.7, 3 + r * 0.6 + rnd.uniform(-1, 1.5)))
        d = Vector((math.cos(a), math.sin(a) * 0.7, 0.55))
        items.append((p, d, rnd.uniform(0.5, 0.72), rnd.uniform(0, 6.28)))
    flock(crow, "c", C.pose, items, rnd)
    feathers((0, 0, 2.6), 16, 2.0, rnd, feather_mat())
    mist((0, 0, 0), 2.2, density=0.035, h=1.2)
    out.append(render("crow_leave_scatter", (8.5, -15, 5.5), (0, 0, 5.0), 30))

    # 3. crows, arriving: a ring swirling in, tightening on the spot
    rnd = random.Random(5)
    scene_reset()
    ground()
    items = []
    for k in range(32):
        a = k / 32 * 2 * math.pi * 1.6 + rnd.uniform(-0.2, 0.2)
        r = 1.4 + 3.2 * (k / 32) + rnd.uniform(-0.3, 0.3)
        h = 1.0 + 4.5 * (k / 32) + rnd.uniform(-0.4, 0.4)
        p = Vector((math.cos(a) * r, math.sin(a) * r, h))
        d = Vector((-math.sin(a), math.cos(a), -0.25)) - Vector((math.cos(a), math.sin(a), 0)) * 0.35
        items.append((p, d, rnd.uniform(0.5, 0.72), rnd.uniform(0, 6.28)))
    flock(crow, "c", C.pose, items, rnd)
    mist((0, 0, 0), 1.8, density=0.09, h=3.5)
    out.append(render("crow_arrive_swirl", *cam))

    # 4. crows, arriving: the last of them folding into the re-formed student
    rnd = random.Random(6)
    scene_reset()
    ground()
    student((0, 0, 0), cut=0.3)
    items = []
    for k in range(12):
        p = around_body(rnd)
        d = (Vector((0, 0, 3)) - p) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0))
        p = p - d.normalized() * rnd.uniform(0.6, 2.2)
        items.append((p, d, rnd.uniform(0.45, 0.62), rnd.uniform(0, 6.28)))
    flock(crow, "c", C.pose, items, rnd)
    feathers((0, 0, 2.2), 10, 2.0, rnd, feather_mat())
    out.append(render("crow_arrive_reform", *cam))

    # 5. the owner's bats, leaving: a vortex of bats tearing them away over a crimson sigil
    rnd = random.Random(7)
    scene_reset()
    ground(sigil=True)
    student((0, 0, 0), cut=0.65, head_cut=0.4)
    items = []
    for k in range(48):
        f = k / 48
        a = f * 2 * math.pi * 3.2 + rnd.uniform(-0.25, 0.25)
        r = 1.6 + 2.0 * f + rnd.uniform(-0.3, 0.3)
        h = 0.6 + 8.5 * f + rnd.uniform(-0.3, 0.3)
        p = Vector((math.cos(a) * r, math.sin(a) * r, h))
        d = Vector((-math.sin(a), math.cos(a), 0.55))
        items.append((p, d, rnd.uniform(0.55, 0.85), rnd.uniform(0, 6.28)))
    flock(bat, "b", B.pose, items, rnd)
    mist((0, 0, 0), 4.6, density=0.07, color=(0.05, 0.01, 0.02), emit=(0.25, 0.01, 0.03), h=1.3)
    out.append(render("bat_leave_vortex", (8.5, -15, 5.5), (0, 0, 4.5), 30))

    # 6. the owner's bats, arriving: a stoop of bats diving into the sigil, the owner forming at its heart
    rnd = random.Random(8)
    scene_reset()
    ground(sigil=True)
    student((0, 0, 0), cut=0.8, head_cut=0.75)
    items = []
    for k in range(44):
        f = k / 44
        a = f * 2 * math.pi * 2.5 + rnd.uniform(-0.3, 0.3)
        r = 0.8 + 3.8 * f + rnd.uniform(-0.3, 0.3)
        h = 1.2 + 9 * f * f + rnd.uniform(-0.3, 0.3)
        p = Vector((math.cos(a) * r, math.sin(a) * r, h))
        d = Vector((-math.sin(a) * 0.8, math.cos(a) * 0.8, -1.0)) - Vector((math.cos(a), math.sin(a), 0)) * 0.4
        items.append((p, d, rnd.uniform(0.55, 0.85), rnd.uniform(0, 6.28)))
    flock(bat, "b", B.pose, items, rnd)
    mist((0, 0, 0), 2.4, density=0.12, color=(0.05, 0.01, 0.02), emit=(0.3, 0.01, 0.04), h=5.5)
    out.append(render("bat_arrive_dive", (8.5, -15, 5.5), (0, 0, 4.5), 30))
    print("[mock]", out)


main()
