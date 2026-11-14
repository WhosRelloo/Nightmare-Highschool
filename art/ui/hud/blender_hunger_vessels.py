"""Hunger vessels (Hunger 1.0), stage 1 of 2: the six race reliquaries, modelled and rendered in headless Blender (Cycles).

Each race's vessel is real geometry: a quatrefoil iron plinth, a glass jar in a strapped cage, a Gothic spire canopy
with pinnacles, and the race's own finial and contents. Materials are full Principled PBR with procedural surface
detail (hammered iron, brushed brass, gilt, silver, verdigris), ambient-occlusion grime in the crevices and edge wear
from pointiness. The lights are the HUD bake's (a warm key from the top left, a cool fill, a candle rim, a soft box,
and the warm-ceiling / dark-floor world).

Three renders per race, all with a transparent film (glass included):
  <Race>_empty.png  the vessel with its contents spent (the HUD's back layer)
  <Race>_full.png   the vessel brimming (cut down to the contents by the mask in stage 2)
  <Race>_mask.png   the contents alone, everything in front of them held out (straps, rings)
Plus Plate.png, the enamel band plate (9-slice).

  E:/Blender/blender.exe -b --factory-startup -P blender_hunger_vessels.py -- [Race ...] [--samples=N]
  -> art/ui/hud/out/hunger/render/*.png      then: python finish_hunger_vessels.py
"""
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "hunger" / "render"
OUT.mkdir(parents=True, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WANT = [a for a in argv if not a.startswith("--")]
SAMPLES = 192
for a in argv:
    if a.startswith("--samples="):
        SAMPLES = int(a.split("=")[1])

W, H = 768, 1152            # rendered 2x; stage 2 halves it to 384 x 576
ORTHO = 2.55                # world height in view
CAM_TILT = 9.0              # degrees down, so the rims read as ellipses

RACES = ["Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith"]


def srgb(c):
    return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 if x / 255.0 > 0.04045 else x / 255.0 / 12.92 for x in c)


# ---------------------------------------------------------------- scene helpers
def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves,
                 bpy.data.images, bpy.data.textures):
        for d in list(coll):
            coll.remove(d)


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def active():
    return bpy.context.view_layer.objects.active


def smooth(o, bevel=0.0, segs=3, sub=0, auto=True):
    if bevel > 0:
        m = o.modifiers.new("bevel", "BEVEL")
        m.width = bevel
        m.segments = segs
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(35)
        m.harden_normals = False
    if sub:
        m = o.modifiers.new("sub", "SUBSURF")
        m.levels = sub
        m.render_levels = sub
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def flat(o):
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def cyl(r, h, z, verts=48, mat=None, x=0.0, y=0.0, bevel=0.01, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(x, y, z + h / 2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=(x, y, z + h / 2))
    o = active()
    smooth(o, bevel)
    if mat:
        o.data.materials.append(mat)
    return o


def torus(R, r, z, mat, x=0.0, y=0.0, rot=(0, 0, 0), maj=64, mn=16):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=maj, minor_segments=mn,
                                     location=(x, y, z), rotation=rot)
    o = active()
    smooth(o)
    o.data.materials.append(mat)
    return o


def sphere(r, loc, mat, scale=(1, 1, 1), seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = active()
    o.scale = scale
    smooth(o)
    o.data.materials.append(mat)
    return o


def box(size, loc, mat, rot=(0, 0, 0), bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = active()
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    smooth(o, bevel, 2)
    o.data.materials.append(mat)
    return o


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = active()
    o.name = name
    return o


def poly_prism(points, depth, loc, mat, rot=(0, 0, 0), bevel=0.006):
    """an extruded flat outline (x, z) of the given depth, facing the camera"""
    me = bpy.data.meshes.new("prism")
    bm = bmesh.new()
    vs = [bm.verts.new((x, -depth / 2, z)) for x, z in points]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in r["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.y += depth
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new("prism", me))
    o.location = loc
    o.rotation_euler = rot
    smooth(o, bevel, 2)
    flat(o)
    o.data.materials.append(mat)
    return o


# ---------------------------------------------------------------- materials
def node(nt, kind, loc=(0, 0)):
    n = nt.nodes.new(kind)
    n.location = loc
    return n


def material(name, col, metal=0.0, rough=0.4, detail="none", grime=0.35, wear=0.0, emit=None, emit_str=0.0,
             trans=0.0, ior=1.45, coat=0.0, sss=0.0, tint2=None):
    """a Principled material with procedural detail; col and emit are 0-255 sRGB"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (900, 0))
    bs = node(nt, "ShaderNodeBsdfPrincipled", (600, 0))
    nt.links.new(bs.outputs[0], out.inputs[0])
    tc = node(nt, "ShaderNodeTexCoord", (-900, 0))
    base = (*srgb(col), 1.0)
    colour = None
    # variation: a second tone mottled in by noise (verdigris on old brass, tarnish on silver)
    if tint2 is not None:
        nz = node(nt, "ShaderNodeTexNoise", (-500, 300))
        nz.inputs["Scale"].default_value = 9.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = node(nt, "ShaderNodeValToRGB", (-300, 300))
        ramp.color_ramp.elements[0].position = 0.48
        ramp.color_ramp.elements[0].color = base
        ramp.color_ramp.elements[1].position = 0.66
        ramp.color_ramp.elements[1].color = (*srgb(tint2), 1.0)
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        colour = ramp.outputs["Color"]
    # grime: ambient occlusion darkens the crevices
    if grime > 0:
        ao = node(nt, "ShaderNodeAmbientOcclusion", (-300, 100))
        ao.inputs["Distance"].default_value = 0.08
        mix = node(nt, "ShaderNodeMix", (100, 150))
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        if colour is not None:
            nt.links.new(colour, mix.inputs["A"])
        else:
            mix.inputs["A"].default_value = base
        lift = node(nt, "ShaderNodeMapRange", (-100, 50))
        lift.inputs["From Min"].default_value = 0.0
        lift.inputs["From Max"].default_value = 1.0
        lift.inputs["To Min"].default_value = 1.0 - grime
        lift.inputs["To Max"].default_value = 1.0
        nt.links.new(ao.outputs["AO"], lift.inputs["Value"])
        comb = node(nt, "ShaderNodeCombineColor", (0, -50))
        for i in range(3):
            nt.links.new(lift.outputs["Result"], comb.inputs[i])
        nt.links.new(comb.outputs[0], mix.inputs["B"])
        colour = mix.outputs["Result"]
    # edge wear: bright metal on the convex edges
    if wear > 0:
        geo = node(nt, "ShaderNodeNewGeometry", (-300, -250))
        pr = node(nt, "ShaderNodeMapRange", (-100, -250))
        pr.inputs["From Min"].default_value = 0.52
        pr.inputs["From Max"].default_value = 0.62
        pr.inputs["To Max"].default_value = wear
        nt.links.new(geo.outputs["Pointiness"], pr.inputs["Value"])
        mix2 = node(nt, "ShaderNodeMix", (300, 150))
        mix2.data_type = "RGBA"
        nt.links.new(pr.outputs["Result"], mix2.inputs["Factor"])
        if colour is not None:
            nt.links.new(colour, mix2.inputs["A"])
        else:
            mix2.inputs["A"].default_value = base
        hi = tuple(min(1.0, c * 1.9 + 0.08) for c in srgb(col))
        mix2.inputs["B"].default_value = (*hi, 1.0)
        colour = mix2.outputs["Result"]
    if colour is not None:
        nt.links.new(colour, bs.inputs["Base Color"])
    else:
        bs.inputs["Base Color"].default_value = base
    bs.inputs["Metallic"].default_value = metal
    bs.inputs["IOR"].default_value = ior
    if trans > 0:
        bs.inputs["Transmission Weight"].default_value = trans
    if coat > 0:
        bs.inputs["Coat Weight"].default_value = coat
        bs.inputs["Coat Roughness"].default_value = 0.05
    if sss > 0:
        bs.inputs["Subsurface Weight"].default_value = sss
        bs.inputs["Subsurface Radius"].default_value = (0.1, 0.05, 0.03)
    if emit is not None:
        bs.inputs["Emission Color"].default_value = (*srgb(emit), 1.0)
        bs.inputs["Emission Strength"].default_value = emit_str
    # roughness breakup and the surface's own bump
    rn = node(nt, "ShaderNodeTexNoise", (-500, -450))
    rn.inputs["Scale"].default_value = 30.0
    rn.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], rn.inputs["Vector"])
    rr = node(nt, "ShaderNodeMapRange", (-300, -450))
    rr.inputs["To Min"].default_value = max(0.02, rough * 0.7)
    rr.inputs["To Max"].default_value = min(1.0, rough * 1.35)
    nt.links.new(rn.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bs.inputs["Roughness"])
    if detail != "none":
        bump = node(nt, "ShaderNodeBump", (300, -400))
        if detail == "hammered":
            vo = node(nt, "ShaderNodeTexVoronoi", (0, -500))
            vo.inputs["Scale"].default_value = 70.0
            nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
            nt.links.new(vo.outputs["Distance"], bump.inputs["Height"])
            bump.inputs["Strength"].default_value = 0.22
        elif detail == "brushed":
            mp = node(nt, "ShaderNodeMapping", (-200, -600))
            mp.inputs["Scale"].default_value = (60.0, 60.0, 1.5)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            nz = node(nt, "ShaderNodeTexNoise", (0, -600))
            nz.inputs["Scale"].default_value = 40.0
            nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
            nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
            bump.inputs["Strength"].default_value = 0.06
        elif detail == "scratched":
            mp = node(nt, "ShaderNodeMapping", (-200, -600))
            mp.inputs["Scale"].default_value = (2.0, 2.0, 90.0)
            mp.inputs["Rotation"].default_value = (0.0, 0.5, 0.3)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            wv = node(nt, "ShaderNodeTexWave", (0, -600))
            wv.inputs["Scale"].default_value = 3.0
            wv.inputs["Distortion"].default_value = 14.0
            nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
            nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
            bump.inputs["Strength"].default_value = 0.18
        elif detail == "velvet":
            nz = node(nt, "ShaderNodeTexNoise", (0, -600))
            nz.inputs["Scale"].default_value = 260.0
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
            bump.inputs["Strength"].default_value = 0.3
            bs.inputs["Sheen Weight"].default_value = 0.8
            bs.inputs["Sheen Tint"].default_value = (*srgb(tuple(min(255, c * 3 + 40) for c in col)), 1.0)
        elif detail == "craters":
            vo = node(nt, "ShaderNodeTexVoronoi", (0, -600))
            vo.inputs["Scale"].default_value = 11.0
            nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
            nz = node(nt, "ShaderNodeTexNoise", (0, -800))
            nz.inputs["Scale"].default_value = 25.0
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            add = node(nt, "ShaderNodeMath", (150, -700))
            add.operation = "ADD"
            nt.links.new(vo.outputs["Distance"], add.inputs[0])
            nt.links.new(nz.outputs["Fac"], add.inputs[1])
            nt.links.new(add.outputs[0], bump.inputs["Height"])
            bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.004
        nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    return m


def volume_glow(name, col, density=0.6, strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (600, 0))
    pv = node(nt, "ShaderNodeVolumePrincipled", (300, 0))
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (*srgb(col), 1.0)
    pv.inputs["Emission Color"].default_value = (*srgb(col), 1.0)
    pv.inputs["Emission Strength"].default_value = strength
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    return m


# ---------------------------------------------------------------- the race looks
TRIM = {
    #            cage metal                          trim metal                       backdrop velvet
    "Human":    ((44, 42, 46), "hammered", 0.85,    (210, 164, 92), "brushed",      (40, 22, 14)),
    "Priest":   ((196, 198, 206), "brushed", 1.0,   (240, 206, 122), "brushed",     (16, 22, 46)),
    "Vampire":  ((24, 20, 24), "hammered", 0.85,    (236, 198, 112), "brushed",     (20, 10, 22)),
    "Werewolf": ((40, 40, 44), "scratched", 0.85,   (178, 182, 190), "brushed",     (22, 22, 26)),
    "Ghoul":    ((50, 46, 40), "hammered", 0.8,     (160, 120, 66), "brushed",      (14, 24, 14)),
    "Wraith":   ((150, 160, 176), "brushed", 1.0,   (206, 216, 232), "brushed",     (12, 12, 34)),
}


def mats_for(race):
    cage_c, cage_d, cage_m, trim_c, trim_d, velvet = TRIM[race]
    M = {}
    M["cage"] = material(f"{race}_cage", cage_c, metal=cage_m, rough=0.42 if cage_m < 1 else 0.28, detail=cage_d,
                         grime=0.5, wear=0.35 if cage_m < 1 else 0.12,
                         tint2=(70, 92, 78) if race == "Ghoul" else None)
    M["trim"] = material(f"{race}_trim", trim_c, metal=1.0, rough=0.22, detail=trim_d, grime=0.45, wear=0.15,
                         tint2=(84, 128, 104) if race == "Ghoul" else ((150, 150, 156) if race == "Wraith" else None))
    M["gilt"] = material(f"{race}_gilt", (246, 210, 124), metal=1.0, rough=0.14, detail="brushed", grime=0.3)
    M["velvet"] = material(f"{race}_velvet", velvet, rough=0.85, detail="velvet", grime=0.4)
    M["glass"] = material(f"{race}_glass", (236, 240, 244), rough=0.03, trans=1.0, ior=1.47, grime=0.0)
    if race == "Wraith":   # a frosted bell jar
        M["glass"] = material("Wraith_glass", (226, 236, 250), rough=0.16, trans=1.0, ior=1.47, grime=0.0)
    return M


def build_vessel(race, M):
    """the shared reliquary; returns (objects in front of the contents, every object)"""
    front, every = [], []
    # quatrefoil plinth
    every.append(cyl(0.56, 0.07, 0.0, mat=M["cage"], bevel=0.02))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        every.append(cyl(0.2, 0.07, 0.0, mat=M["cage"], x=0.42 * math.cos(a), y=0.42 * math.sin(a), bevel=0.02))
    every.append(cyl(0.5, 0.09, 0.07, mat=M["cage"], bevel=0.02, r2=0.44))
    every.append(cyl(0.44, 0.04, 0.16, mat=M["trim"], bevel=0.01))
    every.append(torus(0.43, 0.025, 0.18, M["gilt"]))
    every.append(cyl(0.39, 0.07, 0.2, mat=M["cage"], bevel=0.015))
    # the jar's floor and the backdrop inside it (half cylinder behind the contents)
    every.append(cyl(0.34, 0.02, 0.27, mat=M["velvet"], bevel=0.0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.325, depth=1.0, location=(0, 0, 0.79))
    back = active()
    bm = bmesh.new()
    bm.from_mesh(back.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.02], context="VERTS")
    bm.to_mesh(back.data)
    bm.free()
    smooth(back)
    back.data.materials.append(M["velvet"])
    every.append(back)
    # glass jar
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.345, depth=1.06, location=(0, 0, 0.27 + 0.53))
    glass = active()
    sm = glass.modifiers.new("shell", "SOLIDIFY")
    sm.thickness = 0.012
    smooth(glass)
    glass.data.materials.append(M["glass"])
    glass.name = "Glass"
    every.append(glass)
    # rings
    for z in (0.28, 1.31):
        r = torus(0.36, 0.035, z, M["trim"])
        every.append(r)
        front.append(r)
    r = torus(0.37, 0.012, 0.8, M["gilt"])
    every.append(r)
    front.append(r)
    # four straps with rivets
    for i in range(4):
        a = math.radians(45 + 90 * i)
        x, y = 0.365 * math.cos(a), 0.365 * math.sin(a)
        s = box((0.05, 0.022, 1.06), (x, y, 0.8), M["cage"], rot=(0, 0, a + math.pi / 2), bevel=0.006)
        every.append(s)
        if y < 0:
            front.append(s)
        for z in (0.36, 0.8, 1.24):
            rv = sphere(0.02, (x * 1.04, y * 1.04, z), M["gilt"])
            every.append(rv)
            if y < 0:
                front.append(rv)
    # canopy: an octagonal spire, a brass band, four pinnacles and crockets
    every.append(cyl(0.42, 0.06, 1.33, verts=8, mat=M["cage"], bevel=0.012))
    every.append(cyl(0.4, 0.035, 1.39, verts=8, mat=M["trim"], bevel=0.008))
    spire = cyl(0.36, 0.52, 1.425, verts=8, mat=M["cage"], bevel=0.01, r2=0.035)
    spire.rotation_euler.z = math.radians(22.5)
    every.append(spire)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        x, y = 0.42 * math.cos(a), 0.42 * math.sin(a)
        every.append(cyl(0.05, 0.1, 1.39, verts=8, mat=M["cage"], x=x, y=y, bevel=0.006))
        every.append(cyl(0.05, 0.2, 1.49, verts=8, mat=M["cage"], x=x, y=y, bevel=0.004, r2=0.004))
        every.append(sphere(0.022, (x, y, 1.705), M["gilt"]))
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        for t in (0.3, 0.6):
            r_ = 0.36 + (0.035 - 0.36) * t
            every.append(sphere(0.018, (r_ * math.cos(a) * 1.02, r_ * math.sin(a) * 1.02, 1.425 + 0.52 * t), M["gilt"],
                                scale=(1, 1, 1.4)))
    every.append(sphere(0.04, (0, 0, 1.955), M["gilt"]))
    return front, every


def finial(race, M):
    """the race's crown, sitting on the spire tip at z ~1.98"""
    z = 1.99
    objs = []
    if race == "Human":       # a brass lunch bell
        objs.append(cyl(0.11, 0.17, z + 0.02, mat=M["trim"], bevel=0.01, r2=0.045))
        objs.append(torus(0.11, 0.015, z + 0.02, M["trim"]))
        objs.append(sphere(0.03, (0, 0, z + 0.015), M["gilt"]))
        objs.append(torus(0.035, 0.012, z + 0.215, M["gilt"], rot=(math.pi / 2, 0, 0)))
    elif race == "Priest":    # a silver sun-cross: a ring, rays and a cross
        zc = z + 0.17
        objs.append(torus(0.1, 0.014, zc, M["gilt"], rot=(math.pi / 2, 0, 0)))
        for i in range(12):
            a = math.radians(30 * i + 15)
            objs.append(box((0.012, 0.012, 0.07), (0.15 * math.cos(a), 0, zc + 0.15 * math.sin(a)), M["gilt"],
                            rot=(0, -a + math.pi / 2, 0), bevel=0.003))
        objs.append(box((0.032, 0.03, 0.36), (0, 0, zc), M["trim"], bevel=0.006))
        objs.append(box((0.22, 0.03, 0.032), (0, 0, zc + 0.05), M["trim"], bevel=0.006))
        objs.append(cyl(0.02, 0.06, z - 0.03, mat=M["trim"]))
    elif race == "Vampire":   # bat wings round a garnet
        zc = z + 0.11
        wing = [(0.0, 0.0), (0.08, 0.05), (0.19, 0.1), (0.3, 0.06), (0.27, 0.02), (0.24, -0.03), (0.19, 0.0),
                (0.15, -0.05), (0.1, -0.01), (0.05, -0.06)]
        objs.append(poly_prism(wing, 0.02, (0.03, 0, zc), M["cage"]))
        objs.append(poly_prism([(-x, z_) for x, z_ in reversed(wing)], 0.02, (-0.03, 0, zc), M["cage"]))
        garnet = material("Vampire_garnet", (120, 8, 26), rough=0.08, trans=0.5, ior=1.75, emit=(160, 10, 30),
                          emit_str=0.6, grime=0.0)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.05, location=(0, 0, zc + 0.01))
        g = active()
        g.scale = (1, 1, 1.25)
        flat(g)
        g.data.materials.append(garnet)
        objs.append(g)
        objs.append(cyl(0.02, 0.07, z - 0.03, mat=M["gilt"]))
    elif race == "Werewolf":  # a silver crescent moon
        zc = z + 0.15
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.13, depth=0.035, location=(0, 0, zc),
                                            rotation=(math.pi / 2, 0, 0))
        moon = active()
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.115, depth=0.2, location=(0.06, 0, zc + 0.03),
                                            rotation=(math.pi / 2, 0, 0))
        cut = active()
        bo = moon.modifiers.new("cut", "BOOLEAN")
        bo.object = cut
        bo.operation = "DIFFERENCE"
        bpy.context.view_layer.objects.active = moon
        bpy.ops.object.modifier_apply(modifier="cut")
        bpy.data.objects.remove(cut, do_unlink=True)
        smooth(moon, 0.006, 2)
        moon.data.materials.append(M["trim"])
        objs.append(moon)
        objs.append(cyl(0.02, 0.06, z - 0.03, mat=M["trim"]))
    elif race == "Ghoul":     # a grave-lantern cap with a chain
        objs.append(cyl(0.09, 0.05, z, verts=6, mat=M["cage"], bevel=0.006))
        objs.append(cyl(0.08, 0.1, z + 0.05, verts=6, mat=M["cage"], bevel=0.005, r2=0.012))
        zc = z + 0.17
        for i in range(3):
            objs.append(torus(0.028, 0.008, zc + i * 0.045, M["trim"],
                              rot=(math.pi / 2 if i % 2 == 0 else 0, 0, math.pi / 2 if i % 2 else 0), maj=24, mn=8))
    elif race == "Wraith":    # a four-point frost star
        zc = z + 0.16
        for a in (0, 90, 45, 135):
            ln = 0.16 if a in (0, 90) else 0.09
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.022, radius2=0.0, depth=ln, location=(0, 0, zc))
            p1 = active()
            p1.rotation_euler = (0, math.radians(a), 0)
            p1.location = (math.sin(math.radians(a)) * ln / 2, 0, zc + math.cos(math.radians(a)) * ln / 2)
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.022, radius2=0.0, depth=ln, location=(0, 0, zc))
            p2 = active()
            p2.rotation_euler = (0, math.radians(a + 180), 0)
            p2.location = (-math.sin(math.radians(a)) * ln / 2, 0, zc - math.cos(math.radians(a)) * ln / 2)
            for p in (p1, p2):
                flat(p)
                p.data.materials.append(M["trim"])
                objs.append(p)
        objs.append(sphere(0.025, (0, 0, zc), M["gilt"]))
        objs.append(cyl(0.015, 0.06, z - 0.03, mat=M["trim"]))
    return objs


# ---------------------------------------------------------------- contents (empty and full)
Z0, ZTOP = 0.285, 1.21   # the jar's floor and the brim level


def liquid(name, r, z0, z1, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=z1 - z0, location=(0, 0, (z0 + z1) / 2))
    o = active()
    smooth(o, 0.02, 3)
    o.data.materials.append(mat)
    o.name = name
    return o


def contents(race, full):
    """the race's contents; returns the objects"""
    rnd = random.Random(7)
    objs = []
    if race in ("Human", "Priest"):
        if race == "Human":
            m = material("broth", (160, 84, 22), rough=0.05, trans=0.45, ior=1.34, emit=(255, 140, 50),
                         emit_str=0.28 if full else 0.04, grime=0.0)
        else:
            m = material("holywater", (196, 222, 236), rough=0.04, trans=0.85, ior=1.33, emit=(250, 226, 160),
                         emit_str=0.45 if full else 0.05, grime=0.0)
        top = ZTOP if full else Z0 + 0.06
        objs.append(liquid("Contents", 0.33, Z0, top, m))
        if full:
            # floating bits (Human: rice and spring onion; Priest: gold motes)
            for i in range(26 if race == "Priest" else 14):
                a = rnd.uniform(0, math.tau)
                r = rnd.uniform(0.04, 0.27)
                zz = rnd.uniform(Z0 + 0.06, top - 0.04)
                if race == "Priest":
                    gm = material(f"mote{i}", (255, 220, 140), emit=(255, 214, 120), emit_str=8.0, grime=0.0)
                    objs.append(sphere(rnd.uniform(0.006, 0.014), (r * math.cos(a), r * math.sin(a), zz), gm, seg=12))
                else:
                    col = (238, 232, 214) if i % 3 else (92, 150, 60)
                    bm_ = material(f"bit{i}", col, rough=0.5, sss=0.2, grime=0.0)
                    objs.append(sphere(0.012, (r * math.cos(a), r * math.sin(a), top - 0.02), bm_,
                                       scale=(1.6, 1.0, 0.5), seg=12))
    elif race == "Vampire":
        # a faceted garnet heart on a crimson velvet cushion: unlit when spent, alight when fed (no liquid, ever)
        # (no blood rule) a black velvet cushion and a ruby-magenta gem, so nothing in the jar reads as red liquid
        cush = material("cushion", (26, 18, 24), rough=0.8, detail="velvet", grime=0.4)
        objs.append(sphere(0.2, (0, 0, Z0 + 0.06), cush, scale=(1.3, 1.3, 0.42)))
        parts = []
        parts.append(sphere(0.15, (-0.1, 0, 0.86), cush, seg=24))
        parts.append(sphere(0.15, (0.1, 0, 0.86), cush, seg=24))
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.235, radius2=0.0, depth=0.42, location=(0, 0, 0.66),
                                        rotation=(math.pi, 0, 0))
        parts.append(active())
        heart = join(parts, "Contents")
        rm = heart.modifiers.new("remesh", "REMESH")
        rm.mode = "VOXEL"
        rm.voxel_size = 0.02
        dm = heart.modifiers.new("facets", "DECIMATE")
        dm.ratio = 0.035
        heart.data.materials.clear()
        if full:
            gm = material("garnet_lit", (190, 20, 92), rough=0.06, trans=0.55, ior=1.77, emit=(255, 46, 128),
                          emit_str=2.4, grime=0.0)
        else:
            gm = material("garnet_dark", (40, 8, 26), rough=0.12, trans=0.3, ior=1.77, grime=0.0)
        heart.data.materials.append(gm)
        flat(heart)
        heart.rotation_euler.z = math.radians(8)
        objs.append(heart)
        if full:
            core = sphere(0.07, (0, 0, 0.8), volume_glow("heartglow", (255, 90, 160), 2.0, 4.0))
            objs.append(core)
    elif race == "Werewolf":
        # a moon disc standing in the jar: a dark slate moon when spent, a glowing silver one when fed
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.27, depth=0.05, location=(0, 0.04, 0.76),
                                            rotation=(math.pi / 2, 0, 0))
        moon = active()
        smooth(moon, 0.02, 3)
        moon.name = "Contents"
        if full:
            mm = material("moon_lit", (214, 210, 196), rough=0.6, detail="craters", grime=0.55, emit=(255, 240, 210),
                          emit_str=0.45)
        else:
            mm = material("moon_dark", (52, 54, 62), rough=0.7, detail="craters", grime=0.4)
        # maria: darker patches in the moon's colour, so it reads as a moon even lit
        nt = mm.node_tree
        bs = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 3.2
        nz.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        lit = full
        base = (0.62, 0.6, 0.55, 1) if lit else (0.04, 0.045, 0.055, 1)
        dark = (0.3, 0.3, 0.3, 1) if lit else (0.02, 0.022, 0.028, 1)
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.45, dark
        ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.6, base
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        old_link = [l for l in nt.links if l.to_socket == bs.inputs["Base Color"]]
        for l in old_link:
            nt.links.remove(l)
        nt.links.new(ramp.outputs["Color"], bs.inputs["Base Color"])
        if lit:
            nt.links.new(ramp.outputs["Color"], bs.inputs["Emission Color"])
        moon.data.materials.append(mm)
        objs.append(moon)
        stand = material("moonstand", (40, 40, 44), metal=0.85, rough=0.4, detail="hammered", grime=0.5)
        objs.append(cyl(0.06, 0.2, Z0, mat=stand))
        objs.append(cyl(0.16, 0.035, Z0, mat=stand, bevel=0.01))
    elif race == "Ghoul":
        # an ember bed and a wick; the acid-green grave flame stands up from it when fed
        for i in range(30):
            a = rnd.uniform(0, math.tau)
            r = rnd.uniform(0.0, 0.27)
            em = material(f"ember{i}", (40, 30, 26), rough=0.8, grime=0.2,
                          emit=(150, 255, 90) if full else (90, 160, 50), emit_str=rnd.uniform(0.6, 2.4) if full else 0.25)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.03, 0.055),
                                                  location=(r * math.cos(a), r * math.sin(a), Z0 + 0.03))
            e = active()
            e.scale = (1, 1, 0.6)
            flat(e)
            e.data.materials.append(em)
            objs.append(e)
        wick = material("wick", (20, 18, 16), rough=0.9, grime=0.0)
        objs.append(cyl(0.012, 0.12, Z0 + 0.04, mat=wick))
        if full:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.15, location=(0, 0, 0.6))
            fl = active()
            fl.scale = (1.0, 1.0, 2.9)
            bm = bmesh.new()
            bm.from_mesh(fl.data)
            for v in bm.verts:      # taper the top into a tongue that leans a little
                t = max(0.0, v.co.z)
                k = max(0.12, 1.0 - t / 0.17)
                v.co.x = v.co.x * k + 0.03 * t * t
                v.co.y *= k
            bm.to_mesh(fl.data)
            bm.free()
            smooth(fl)
            fl.name = "Contents"
            fm = volume_glow("graveflame", (150, 255, 110), 3.0, 9.0)
            fl.data.materials.append(fm)
            objs.append(fl)
            objs.append(sphere(0.07, (0, 0, 0.42), volume_glow("flamecore", (230, 255, 200), 4.0, 16.0),
                               scale=(1, 1, 1.8)))
    elif race == "Wraith":
        if full:
            # a cold soul-wisp: a spiral ribbon of light with a glowing heart
            cu = bpy.data.curves.new("wisp", "CURVE")
            cu.dimensions = "3D"
            cu.bevel_depth = 0.022
            cu.bevel_resolution = 4
            sp = cu.splines.new("NURBS")
            n = 40
            sp.points.add(n - 1)
            for i in range(n):
                t = i / (n - 1)
                a = t * math.tau * 2.2
                r = 0.22 * (1 - t) + 0.03
                sp.points[i].co = (r * math.cos(a), r * math.sin(a), Z0 + 0.12 + t * 0.8, 1)
                sp.points[i].radius = 1.4 * math.sin(math.pi * t) + 0.2
            sp.order_u = 4
            w = link(bpy.data.objects.new("Contents", cu))
            wm = material("wisp", (170, 210, 255), emit=(150, 200, 255), emit_str=7.0, grime=0.0)
            w.data.materials.append(wm)
            objs.append(w)
            objs.append(sphere(0.2, (0, 0, 0.78), volume_glow("wispglow", (120, 170, 255), 1.6, 4.0),
                               scale=(1, 1, 1.5)))
            objs.append(sphere(0.06, (0, 0, 0.82), volume_glow("wispcore", (220, 240, 255), 5.0, 18.0)))
        # the spent state is the dark bell jar with a little frost of cold breath at the bottom
        mist = sphere(0.3, (0, 0, Z0 + 0.06), volume_glow("coldmist", (90, 110, 160), 0.6, 0.25 if not full else 0.8),
                      scale=(1, 1, 0.3))
        objs.append(mist)
    return objs


# ---------------------------------------------------------------- lights, world, render
def sun(name, direction, color, strength, angle=8.0):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, ld))
    d = Vector(direction).normalized()
    o.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    return o


def setup_world():
    w = bpy.data.worlds.new("NHHunger")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputWorld", (800, 0))
    bg = node(nt, "ShaderNodeBackground", (600, 0))
    tc = node(nt, "ShaderNodeTexCoord", (-400, 0))
    sep = node(nt, "ShaderNodeSeparateXYZ", (-200, 0))
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mr = node(nt, "ShaderNodeMapRange", (0, 0))
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = node(nt, "ShaderNodeValToRGB", (200, 0))
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.008, 0.007, 0.010, 1)
    els[1].position, els[1].color = 1.0, (0.70, 0.55, 0.38, 1)
    for pos, c in ((0.42, (0.05, 0.04, 0.045)), (0.52, (0.42, 0.33, 0.24)), (0.70, (0.95, 0.78, 0.55)),
                   (0.84, (2.4, 1.95, 1.4))):
        e = els.new(pos)
        e.color = (*c, 1)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.9
    nt.links.new(bg.outputs[0], out.inputs[0])


def setup_render(w, h):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    dev = "CPU"
    for kind in ("OPTIX", "CUDA", "HIP"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == kind
                dev = "GPU"
                break
        except Exception:
            pass
    sc.cycles.device = dev
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 10
    sc.cycles.transmission_bounces = 10
    sc.cycles.volume_bounces = 2
    sc.render.film_transparent = True
    sc.cycles.film_transparent_glass = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.filter_size = 1.2
    return dev


def camera_and_lights(ortho, cz):
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = ortho
    cam = link(bpy.data.objects.new("cam", cam_d))
    t = math.radians(CAM_TILT)
    cam.location = (0, -8 * math.cos(t), cz + 8 * math.sin(t))
    cam.rotation_euler = (math.pi / 2 - t, 0, 0)
    bpy.context.scene.camera = cam
    # the HUD bake's rig, turned for a camera looking along +Y
    sun("key", (-0.55, -0.55, 0.65), (1.0, 0.88, 0.74), 2.8, 6)
    sun("fill", (0.6, -0.6, 0.35), (0.55, 0.62, 0.9), 0.8, 12)
    sun("rim", (0.1, 0.9, 0.35), (1.0, 0.55, 0.28), 1.6, 10)
    ad = bpy.data.lights.new("softbox", "AREA")
    ad.energy, ad.size, ad.color = 60.0, 2.0, (1.0, 0.9, 0.78)
    sb = link(bpy.data.objects.new("softbox", ad))
    sb.location = (-2.2, -2.6, 3.2)
    sb.rotation_euler = (Vector((0, 0, 1.0)) - sb.location).to_track_quat("-Z", "Y").to_euler()
    setup_world()


def render(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_race(race):
    for state in ("empty", "full", "mask"):
        clear_scene()
        M = mats_for(race)
        front, every = build_vessel(race, M)
        every += finial(race, M)
        cont = contents(race, state != "empty")
        camera_and_lights(ORTHO, 1.08)
        dev = setup_render(W, H)
        if state == "mask":
            # only the contents count: what's in front of them is held out, the glass and the rest are hidden
            for o in every:
                if o in front:
                    o.is_holdout = True
                else:
                    o.hide_render = True
            bpy.context.scene.cycles.samples = 48
        render(OUT / f"{race}_{state}.png")
        print(f"rendered {race} {state} on {dev}")


def render_plate():
    """the band plate: black enamel in a brass bezel with gilt end studs, rendered flat-on for a 9-slice"""
    clear_scene()
    brass = material("plate_brass", (210, 164, 92), metal=1.0, rough=0.24, detail="brushed", grime=0.5, wear=0.2)
    iron = material("plate_iron", (40, 38, 42), metal=0.85, rough=0.45, detail="hammered", grime=0.5, wear=0.3)
    enamel = material("plate_enamel", (14, 11, 16), rough=0.1, coat=1.0, grime=0.2)
    gilt = material("plate_gilt", (246, 210, 124), metal=1.0, rough=0.14, grime=0.3)
    box((3.0, 0.08, 0.72), (0, 0, 0), iron, bevel=0.05)
    box((2.84, 0.1, 0.58), (0, -0.01, 0), brass, bevel=0.035)
    box((2.68, 0.1, 0.44), (0, -0.03, 0), enamel, bevel=0.03)
    for x in (-1.38, 1.38):
        sphere(0.06, (x, -0.06, 0), gilt, scale=(1, 0.6, 1))
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 3.2
    cam = link(bpy.data.objects.new("cam", cam_d))
    cam.location = (0, -6, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    bpy.context.scene.camera = cam
    sun("key", (-0.55, -0.55, 0.65), (1.0, 0.88, 0.74), 2.8, 6)
    sun("fill", (0.6, -0.6, 0.35), (0.55, 0.62, 0.9), 0.8, 12)
    sun("rim", (0.1, 0.9, -0.35), (1.0, 0.55, 0.28), 1.2, 10)
    setup_world()
    setup_render(1024, 256)
    render(OUT / "Plate.png")
    print("rendered Plate")


for race in RACES:
    if WANT and race not in WANT:
        continue
    render_race(race)
if not WANT or "Plate" in WANT:
    render_plate()
