"""Nightmare Highschool tier-up (evolution) VFX meshes, PBR (Blender 5.x, run headless).

usage:
  "E:/Blender/blender.exe" --background --factory-startup --python art/vfx/evolve/nh_evolve_meshes.py -- <Mesh|all> [--size 1024] [--samples 32]
  Meshes: BloodCrystal, IceSpike, BoneSpike, StoneChunk, HunterSigil, GoldHalo

Reuses the school-props pipeline (art/props/nh_props.py): the same seamless PBR source set, bake-time weathering,
one smart-UV atlas, baked colour (x AO) / normal / roughness / metalness, FBX export and a preview render.
Outputs go to art/vfx/evolve/{textures,fbx,previews}. In Roblox each mesh is one MeshPart with a SurfaceAppearance
and lives in ReplicatedStorage.NHEvolveFX; Gui.Evolution clones them on the client during the cutscene.

What each one is for (see docs/VFX-Design-Bible.md, P1-17):
  BloodCrystal  Vampire   a cluster of glossy blood-red crystal shards that erupts round the feet
  IceSpike      Wraith    frosted spectral ice spikes that grow out of the ground
  BoneSpike     Ghoul     curved, cracked bone spurs that claw up from the earth
  StoneChunk    Werewolf  a rough rock chunk; the howl throws a ring of them up out of a cracked floor
  HunterSigil   Human     a forged-iron hunter's compass ring with runes, floating and turning behind the student
  GoldHalo      Priest    a gilded halo with rays, set above the head
All modelled in studs, centred on the origin, base at z=0 (flat pieces lie in the XY plane, facing up).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector, Matrix, noise

HERE = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.join(HERE, "..", "..", "props")
sys.path.insert(0, os.path.abspath(PROPS))
import nh_props as P  # noqa: E402  (its __main__ guard keeps it from running)

P.OUT_TEX = os.path.join(HERE, "textures")
P.OUT_FBX = os.path.join(HERE, "fbx")
P.OUT_PRE = os.path.join(HERE, "previews")
for d in (P.OUT_TEX, P.OUT_FBX, P.OUT_PRE):
    os.makedirs(d, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0] if argv else "all"
P.SIZE = int(argv[argv.index("--size") + 1]) if "--size" in argv else 1024
P.SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 32


# ------------------------------------------------------------------ materials

def mats():
    m = P.material
    M = {
        # deep, glossy blood glass: dark core, lighter worn facet edges read as light catching the edges
        "blood": m("BloodCrystal", base=(0.11, 0.003, 0.01), rough=0.05, metal=0.0, wear=0.18, dirt=0.35),
        "bloodcore": m("BloodCore", base=(0.24, 0.006, 0.02), rough=0.08, wear=0.15, dirt=0.3),
        # frosted ice: pale blue, glossy faces, frosted (lighter, rougher) edges
        "ice": m("Ice", base=(0.62, 0.78, 0.92), rough=0.1, metal=0.0, wear=0.8, dirt=0.15),
        "icedeep": m("IceDeep", base=(0.32, 0.48, 0.68), rough=0.06, wear=0.5, dirt=0.2),
        # old bone: limestone pores and chisel marks read as bone texture, dark grime in the cracks
        "bone": m("Bone", "NH_Limestone", tint=(0.92, 0.84, 0.66), scale=0.9, normal=1.0, wear=0.35, dirt=1.0),
        "bonedark": m("BoneDark", "NH_Limestone", tint=(0.55, 0.47, 0.36), scale=0.9, normal=1.0, wear=0.3, dirt=1.0),
        # rock and earth for the werewolf's cracked floor
        "rock": m("Rock", "NH_Slate", tint=(0.17, 0.16, 0.155), scale=0.35, rough_mul=0.6, rough_add=0.35, normal=0.9, wear=0.4, dirt=0.9),
        # forged iron and gilt
        "iron": m("Iron", "NH_Iron", tint=(0.13, 0.12, 0.13), scale=0.6, rough_add=0.05, wear=0.6, wear_metal=True),
        "silver": m("Silver", base=(0.80, 0.82, 0.86), rough=0.25, metal=1.0, wear=0.3),
        "gold": m("Gilt", "NH_Brass", tint=(1.25, 1.0, 0.55), scale=0.9, wear=0.25, dirt=0.7),
        "goldbright": m("GiltBright", base=(1.0, 0.78, 0.36), rough=0.18, metal=1.0, wear=0.2),
        "wetblood": m("WetBlood", base=(0.07, 0.002, 0.006), rough=0.03, metal=0.0, wear=0.05, dirt=0.2),
        "soil": m("Soil", "NH_Slate", tint=(0.13, 0.095, 0.07), scale=0.6, rough_mul=0.3, rough_add=0.7, normal=1.0, wear=0.15, dirt=1.0),
        "moon": m("Moon", "NH_Limestone", tint=(0.62, 0.66, 0.74), scale=0.5, normal=1.0, wear=0.35, dirt=1.6),
        "wood": m("StakeWood", "NH_DeskWood", tint=(0.42, 0.27, 0.15), scale=0.6, rough_add=0.15, wear=0.5, dirt=0.9),
    }
    # internal veins / cracks through the crystals and ice (baked into the colour map)
    veins(M["blood"], (0.05, 0.0, 0.004), (0.34, 0.012, 0.03), 5.0)
    veins(M["bloodcore"], (0.1, 0.002, 0.008), (0.5, 0.03, 0.05), 4.0)
    veins(M["ice"], (0.5, 0.66, 0.84), (0.92, 0.97, 1.0), 6.0)
    veins(M["icedeep"], (0.2, 0.34, 0.55), (0.7, 0.85, 1.0), 5.0)
    veins(M["wetblood"], (0.03, 0.0, 0.002), (0.16, 0.004, 0.012), 3.0)
    return M


def veins(mat, dark, light, scale):
    """Replace a flat base colour with dark glass shot through with bright Voronoi crack veins."""
    nt = mat.node_tree
    rgb = next((n for n in nt.nodes if n.type == "RGB"), None)
    if rgb is None:
        return
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = scale
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale * 2.5
    mix_v = nt.nodes.new("ShaderNodeVectorMath"); mix_v.operation = "ADD"
    nt.links.new(tc.outputs["Object"], mix_v.inputs[0])
    sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 0.08
    nt.links.new(nz.outputs["Color"], sc.inputs[0])
    nt.links.new(sc.outputs[0], mix_v.inputs[1])
    nt.links.new(mix_v.outputs[0], vo.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*[d + (l - d) * 0.55 for d, l in zip(dark, light)], 1)
    ramp.color_ramp.elements[1].position = 0.018
    ramp.color_ramp.elements[1].color = (*dark, 1)
    nt.links.new(vo.outputs["Distance"], ramp.inputs["Fac"])
    # depth: a second, larger cloudiness
    nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = scale * 0.6
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 0.35
    nt.links.new(ramp.outputs["Color"], mul.inputs[6])
    nt.links.new(nz2.outputs["Color"], mul.inputs[7])
    for l in list(rgb.outputs[0].links):
        nt.links.new(mul.outputs[2], l.to_socket)


# ------------------------------------------------------------------ mesh helpers

def mesh_object(name, bm, mat, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    return P._finish(ob, mat, bevel)


def crystal(name, base, height, radius, tilt, yaw, mat, sides=6, rng=None, tip=1.5):
    """A faceted crystal: jittered n-gon prism with a pointed tip, tilted out from its base point."""
    rng = rng or random
    bm = bmesh.new()
    rings = []
    twist = rng.uniform(-0.25, 0.25)
    for k, (z, rs) in enumerate(((0.0, 1.0), (height * 0.22, 0.98), (height * 0.45, 0.95), (height * 0.7, 0.9), (height, 0.8))):
        ring = []
        for i in range(sides):
            a = i / sides * math.tau + rng.uniform(-0.08, 0.08) + twist * k / 4
            r = radius * rs * rng.uniform(0.9, 1.08) * (rng.uniform(0.8, 0.95) if rng.random() < 0.15 else 1.0)  # chips
            ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z + rng.uniform(-0.04, 0.04) * height)))
        rings.append(ring)
    tipv = bm.verts.new((rng.uniform(-0.15, 0.15) * radius, rng.uniform(-0.15, 0.15) * radius, height + radius * tip))
    for a, b in zip(rings, rings[1:]):
        for i in range(sides):
            bm.faces.new((a[i], a[(i + 1) % sides], b[(i + 1) % sides], b[i]))
    top = rings[-1]
    for i in range(sides):
        bm.faces.new((top[i], top[(i + 1) % sides], tipv))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    M = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(tilt, 4, "X")
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return mesh_object(name, bm, mat, bevel=min(0.03, radius * 0.12))


def horn(name, base, length, radius, bend, yaw, mat, rings=18, sides=10, rng=None):
    """A curved, tapering spur (bone): lofted rings along an arc, with growth ridges."""
    rng = rng or random
    bm = bmesh.new()
    prev = None
    first = None
    for k in range(rings + 1):
        t = k / rings
        ang = bend * t
        # arc in the XZ plane, then yawed
        centre = Vector((math.sin(ang) * length * 0.55 * t, 0, length * t * (1 - 0.25 * t)))
        tangent = Vector((math.cos(ang) * 0.9, 0, 1)).normalized()
        side = Vector((0, 1, 0))
        normal = tangent.cross(side).normalized()
        ridge = 1.0 + (0.08 if (k % 4 == 2 and k < rings - 2) else 0.0)
        r = radius * (1 - t) ** 0.85 * ridge + radius * 0.02
        ring = []
        for i in range(sides):
            a = i / sides * math.tau
            off = normal * math.cos(a) * r + side * math.sin(a) * r * 0.85
            ring.append(bm.verts.new(centre + off))
        if prev:
            for i in range(sides):
                bm.faces.new((prev[i], prev[(i + 1) % sides], ring[(i + 1) % sides], ring[i]))
        else:
            first = ring
        prev = ring
    tipv = bm.verts.new(prev[0].co * 0 + sum((v.co for v in prev), Vector()) / sides + Vector((0, 0, radius * 0.1)))
    for i in range(sides):
        bm.faces.new((prev[i], prev[(i + 1) % sides], tipv))
    bm.faces.new(list(reversed(first)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # organic wobble
    for v in bm.verts:
        n = noise.noise(v.co * 3.1 + Vector((rng.random() * 0, 0, 0)))
        v.co += v.normal * n * radius * 0.06
    M = Matrix.Translation(base) @ Matrix.Rotation(yaw, 4, "Z")
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return mesh_object(name, bm, mat, bevel=0.0)


def rock(name, centre, size, mat, seed, flat=0.7, rough=0.35):
    """A fractured rock: displaced icosphere, flattened, with a few planar 'break' cuts."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((seed * 1.7, seed * 2.3, seed * 0.9))
    for v in bm.verts:
        d = noise.noise(v.co * 1.4 + off) * rough + noise.noise(v.co * 4.0 + off) * rough * 0.35
        v.co *= 1.0 + d
        v.co.z *= flat
    rng = random.Random(seed)
    for _ in range(3):
        n = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 0.6))).normalized()
        cut = rng.uniform(0.55, 0.8)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=n * cut, plane_no=n, clear_outer=True)
        edges = [e for e in bm.edges if e.is_boundary]
        if edges:
            bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.scale(bm, vec=Vector((size, size, size)), verts=bm.verts)
    lo = min(v.co.z for v in bm.verts)
    bmesh.ops.translate(bm, vec=Vector(centre) - Vector((0, 0, lo)), verts=bm.verts)
    return mesh_object(name, bm, mat, bevel=0.02)


def torus(name, major, minor, mat, loc=(0, 0, 0), maj_seg=64, min_seg=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=maj_seg, minor_segments=min_seg, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return P._finish(ob, mat, 0.0)


def cone(name, r1, depth, loc, rot, mat, verts=8, r2=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return P._finish(ob, mat, 0.004)


# ------------------------------------------------------------------ builders (return dims W, D, H)

def blood_crystal(M):
    rng = random.Random(7)
    spec = [(0, 0, 2.6, 0.34, 0.0, 0.0), (0.45, 0.1, 1.7, 0.24, 0.42, 0.3), (-0.4, 0.25, 1.9, 0.26, 0.38, 2.4),
            (0.05, -0.45, 1.4, 0.2, 0.5, 4.3), (-0.2, -0.3, 1.1, 0.17, 0.62, 3.6), (0.35, 0.4, 1.0, 0.15, 0.7, 1.2),
            (0.6, -0.25, 0.7, 0.11, 0.85, 5.6), (-0.6, -0.05, 0.8, 0.12, 0.8, 2.9), (0.15, 0.6, 0.6, 0.1, 0.9, 1.6),
            (-0.35, 0.55, 0.5, 0.08, 1.0, 2.1), (0.5, 0.45, 0.45, 0.07, 1.05, 0.9)]
    for i, (x, y, h, r, tilt, yaw) in enumerate(spec):
        crystal(f"Shard{i}", Vector((x, y, -0.05)), h, r, tilt, yaw, M["blood"] if i % 3 else M["bloodcore"], rng=rng)
    rock("Base", (0, 0, -0.25), 0.55, M["bonedark"], seed=3, flat=0.35)
    return (1.8, 1.8, 3.1)


def ice_spike(M):
    rng = random.Random(11)
    spec = [(0, 0, 3.0, 0.26, 0.0, 0.0), (0.38, 0.05, 2.0, 0.18, 0.35, 0.5), (-0.34, 0.2, 2.3, 0.2, 0.3, 2.2),
            (0.1, -0.38, 1.6, 0.15, 0.45, 4.1), (-0.25, -0.25, 1.2, 0.12, 0.6, 3.3), (0.3, 0.35, 1.3, 0.13, 0.55, 1.4),
            (0.55, -0.2, 0.8, 0.1, 0.75, 5.2), (-0.55, 0.0, 0.9, 0.11, 0.7, 2.7), (0.2, 0.55, 0.7, 0.09, 0.85, 1.7),
            (-0.4, -0.5, 0.6, 0.08, 0.9, 3.9), (0.45, -0.5, 0.5, 0.07, 1.0, 5.0)]
    for i, (x, y, h, r, tilt, yaw) in enumerate(spec):
        crystal(f"Spike{i}", Vector((x, y, -0.05)), h, r, tilt, yaw, M["ice"] if i % 2 == 0 else M["icedeep"], sides=5, rng=rng, tip=2.4)
    return (1.6, 1.6, 3.5)


def bone_spike(M):
    rng = random.Random(5)
    horn("SpurA", Vector((0, 0, -0.1)), 3.0, 0.32, 0.9, 0.0, M["bone"], rng=rng)
    horn("SpurB", Vector((0.35, 0.2, -0.1)), 2.1, 0.24, 1.2, 2.3, M["bone"], rng=rng)
    horn("SpurC", Vector((-0.3, 0.25, -0.1)), 1.7, 0.2, 1.4, 4.0, M["bonedark"], rng=rng)
    horn("SpurD", Vector((0.05, -0.35, -0.1)), 1.3, 0.16, 1.6, 5.4, M["bone"], rng=rng)
    rock("Clod", (0, 0, -0.3), 0.6, M["rock"], seed=9, flat=0.3)
    return (2.0, 2.0, 2.9)


def stone_chunk(M):
    rock("Chunk", (0, 0, 0), 0.9, M["rock"], seed=21, flat=0.75, rough=0.45)
    return (1.8, 1.8, 1.4)


def hunter_sigil(M):
    torus("Outer", 1.6, 0.075, M["iron"])
    torus("Inner", 1.12, 0.05, M["iron"])
    torus("Hub", 0.28, 0.06, M["silver"])
    for i in range(8):
        a = i / 8 * math.tau
        long = i % 2 == 0
        L = 1.75 if long else 1.25
        P.box(f"Spoke{i}", (L - 0.3, 0.06, 0.05), (math.cos(a) * (0.3 + (L - 0.3) / 2), math.sin(a) * (0.3 + (L - 0.3) / 2), 0),
              M["iron"], bevel=0.012, rot=(0, 0, a))
        if long:
            cone(f"Head{i}", 0.14, 0.32, (math.cos(a) * (L + 0.08), math.sin(a) * (L + 0.08), 0), (0, math.pi / 2, a), M["silver"], verts=4)
    # engraved rune plates between the rings
    for i in range(16):
        a = (i + 0.5) / 16 * math.tau
        P.box(f"Rune{i}", (0.16, 0.05 + 0.04 * (i % 3), 0.03), (math.cos(a) * 1.36, math.sin(a) * 1.36, 0.04), M["silver"], bevel=0.006, rot=(0, 0, a + math.pi / 2))
    return (3.8, 3.8, 0.3)


def gold_halo(M):
    torus("Ring", 1.0, 0.07, M["gold"], maj_seg=72)
    torus("InnerRing", 0.86, 0.025, M["goldbright"], maj_seg=72, min_seg=8)
    for i in range(24):
        a = i / 24 * math.tau
        L = 0.42 if i % 2 == 0 else 0.24
        cone(f"Ray{i}", 0.05 if i % 2 == 0 else 0.035, L, (math.cos(a) * (1.07 + L / 2), math.sin(a) * (1.07 + L / 2), 0), (0, math.pi / 2, a), M["goldbright"], verts=6)
    for i in range(12):
        a = (i + 0.5) / 12 * math.tau
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.045, location=(math.cos(a) * 0.93, math.sin(a) * 0.93, 0))
        ob = bpy.context.active_object
        ob.name = f"Bead{i}"
        P._finish(ob, M["goldbright"], 0.0)
    return (3.0, 3.0, 0.2)


def blood_pool(M):
    """a wet pool of blood: irregular edge, rippled surface (concentric waves), slightly domed."""
    bm = bmesh.new()
    rings, seg = 26, 96
    centre = bm.verts.new((0, 0, 0.06))
    prev = None
    for k in range(1, rings + 1):
        t = k / rings
        ring = []
        for i in range(seg):
            a = i / seg * math.tau
            edge = 1.0 + 0.18 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, 0.5)))
            r = 2.2 * t * edge
            z = 0.06 * (1 - t * t) + 0.012 * math.sin(t * 34) * (1 - t)
            ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        if prev is None:
            for i in range(seg):
                bm.faces.new((centre, ring[i], ring[(i + 1) % seg]))
        else:
            for i in range(seg):
                bm.faces.new((prev[i], ring[i], ring[(i + 1) % seg], prev[(i + 1) % seg]))
        prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_object("Pool", bm, M["wetblood"])
    # a few drops round the edge
    rng = random.Random(4)
    for i in range(9):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(2.3, 2.9)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=rng.uniform(0.06, 0.14), location=(math.cos(a) * r, math.sin(a) * r, 0.02))
        ob = bpy.context.active_object
        ob.scale = (1, 1, 0.25)
        P._finish(ob, M["wetblood"], 0.0)
    return (5.6, 5.6, 0.12)


def moon_disc(M):
    """a cratered moon (the werewolf's howl rises behind them)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    rng = random.Random(12)
    craters = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(), rng.uniform(0.08, 0.32)) for _ in range(38)]
    for v in bm.verts:
        n = v.co.normalized()
        d = 0.0
        for c, r in craters:
            x = (n - c).length / r
            if x < 1.25:
                d += (-0.16 * (1 - x * x) if x < 1 else 0.05 * (1.25 - x) * 4) * r
        d += noise.noise(n * 6) * 0.01
        v.co = n * (1 + d)
    mesh_object("Moon", bm, M["moon"])
    return (2.0, 2.0, 2.0)


def cracked_floor(M):
    """the floor breaking under a howl: radial slabs pushed up at odd angles, with rubble."""
    rng = random.Random(8)
    n = 11
    for i in range(n):
        a0 = i / n * math.tau + rng.uniform(-0.05, 0.05)
        a1 = (i + 1) / n * math.tau - 0.04
        r0, r1 = rng.uniform(0.15, 0.4), rng.uniform(2.4, 3.2)
        bm = bmesh.new()
        pts = [(math.cos(a0) * r0, math.sin(a0) * r0), (math.cos(a1) * r0, math.sin(a1) * r0)]
        for k in range(6):
            a = a1 + (a0 - a1) * k / 5
            rr = r1 * rng.uniform(0.85, 1.05)
            pts.append((math.cos(a) * rr, math.sin(a) * rr))
        top = [bm.verts.new((x, y, 0.25)) for x, y in pts]
        bot = [bm.verts.new((x, y, -0.15)) for x, y in pts]
        bm.faces.new(top)
        bm.faces.new(list(reversed(bot)))
        for k in range(len(pts)):
            bm.faces.new((top[k], bot[k], bot[(k + 1) % len(pts)], top[(k + 1) % len(pts)]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mid = Vector((math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0))
        tilt = Matrix.Rotation(rng.uniform(0.08, 0.3), 4, mid.cross(Vector((0, 0, 1))).normalized())
        bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, rng.uniform(0.0, 0.25))) @ tilt, verts=bm.verts)
        mesh_object(f"Slab{i}", bm, M["rock"], bevel=0.04)
    for i in range(14):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(2.6, 3.6)
        rock(f"Rubble{i}", (math.cos(a) * r, math.sin(a) * r, -0.05), rng.uniform(0.12, 0.3), M["rock"], seed=100 + i, flat=0.6)
    return (7.0, 7.0, 0.9)


def grave_mound(M):
    """a heap of grave soil breaking open, a skull and long bones poking out."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for v in bm.verts:
        v.co.z *= 0.75
        v.co *= 1 + noise.noise(v.co * 2.2) * 0.18 + noise.noise(v.co * 7) * 0.05
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, -0.05), plane_no=(0, 0, 1), clear_inner=True)
    bmesh.ops.scale(bm, vec=(1.6, 1.4, 1.0), verts=bm.verts)
    mesh_object("Soil", bm, M["soil"])
    # skull: cranium, cheekbones, jaw, sockets
    # an R6-style skull: the classic Roblox head (a short, upright cylinder with well-rounded top and bottom edges)
    sk = Vector((0.35, -0.75, 0.62))
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.4, depth=0.62, location=sk)
    c = bpy.context.active_object
    c.name = "Cranium"
    rb = c.modifiers.new("Round", "BEVEL"); rb.width = 0.16; rb.segments = 8; rb.limit_method = "ANGLE"
    P._finish(c, M["bone"], 0.0)
    P.box("Jaw", (0.42, 0.26, 0.14), tuple(sk + Vector((0, -0.2, -0.34))), M["bone"], bevel=0.05)
    for x in (-0.15, 0.15):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.12, location=tuple(sk + Vector((x, -0.36, 0.06))))
        e = bpy.context.active_object; e.scale = (1, 0.55, 1.05); P._finish(e, P.material("Socket", base=(0.02, 0.015, 0.012), rough=0.95, wear=0.0, dirt=0.0), 0.0)
    cone("Nose", 0.06, 0.14, tuple(sk + Vector((0, -0.4, -0.09))), (math.pi / 2, 0, 0), M["bonedark"], verts=3)
    for k in range(6):
        P.box(f"Tooth{k}", (0.045, 0.06, 0.08), tuple(sk + Vector((-0.125 + k * 0.05, -0.37, -0.2))), M["bone"], bevel=0.01)
    # long bones
    rng = random.Random(6)
    for i, (x, y, yaw, pitch) in enumerate(((-0.6, 0.2, 0.6, 0.5), (0.7, 0.4, -1.1, 0.35), (-0.1, 0.65, 2.0, 0.6))):
        L = rng.uniform(1.0, 1.4)
        d = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
        a = Vector((x, y, 0.15))
        b = a + d * L
        P.tube(f"Bone{i}", [tuple(a), tuple(b)], 0.07, M["bone"])
        for end in (a, b):
            for k in (-1, 1):
                bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.09, location=tuple(end + d.cross(Vector((0, 0, 1))).normalized() * 0.06 * k))
                P._finish(bpy.context.active_object, M["bone"], 0.0)
    return (3.4, 3.0, 1.0)


def ice_floor(M):
    """a frozen disc spreading over the floor: thin ice with deep cracks and frost ridges."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=3.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        r = v.co.length
        v.co.x *= 1 + noise.noise(Vector((v.co.x * 0.6, v.co.y * 0.6, 3))) * 0.12
        v.co.z = 0.04 + noise.noise(v.co * 3) * 0.02 * (1 - r / 3.2)
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    for e in ext["geom"]:
        if isinstance(e, bmesh.types.BMVert):
            e.co.z -= 0.12
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ice = mesh_object("Ice", bm, M["ice"], bevel=0.0)
    # cracks: thin boxes cut out of the sheet
    rng = random.Random(14)
    for i in range(9):
        a = rng.uniform(0, math.tau)
        L = rng.uniform(1.2, 2.6)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a) * L / 2, math.sin(a) * L / 2, 0.05), rotation=(0, 0, a))
        cut = bpy.context.active_object
        cut.scale = (L, 0.035, 0.12)
        cut.data.materials.append(M["ice"])  # no empty material slot after the boolean
        cut.hide_render = True
        b = ice.modifiers.new(f"Crack{i}", "BOOLEAN"); b.object = cut; b.operation = "DIFFERENCE"
    for i in range(10):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.8, 2.6)
        crystal(f"Frost{i}", Vector((math.cos(a) * r, math.sin(a) * r, 0.02)), rng.uniform(0.15, 0.35), rng.uniform(0.04, 0.07),
                rng.uniform(0.6, 1.3), a, M["icedeep"], sides=5, rng=rng, tip=2.0)
    return (6.4, 6.4, 0.5)


def silver_stake(M):
    """a sharpened hunter's stake: ash wood, silver bands and a silver tip, nail heads."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.11, depth=2.6, location=(0, 0, 1.6))
    sh = bpy.context.active_object
    P._finish(sh, M["wood"], 0.01)
    cone("Tip", 0.12, 0.5, (0, 0, 0.05), (math.pi, 0, 0), M["silver"], verts=12)
    for z in (0.55, 1.2, 2.5):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.025, major_segments=24, minor_segments=8, location=(0, 0, z))
        P._finish(bpy.context.active_object, M["silver"], 0.0)
    for k in range(4):
        a = k / 4 * math.tau
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.025, location=(math.cos(a) * 0.115, math.sin(a) * 0.115, 1.85))
        P._finish(bpy.context.active_object, M["iron"], 0.0)
    return (0.3, 0.3, 2.95)


def gilded_cross(M):
    """an ornate gilded cross with trefoil ends, a centre ring and filigree beads."""
    P.box("Upright", (0.32, 0.18, 4.2), (0, 0, 2.1), M["gold"], bevel=0.04)
    P.box("Arm", (2.6, 0.22, 0.32), (0, -0.02, 3.05), M["gold"], bevel=0.04)
    for (x, z) in ((0, 4.2), (1.3, 3.05), (-1.3, 3.05), (0, 0.0)):
        for (dx, dz) in ((0, 0.18), (0.18, 0), (-0.18, 0), (0, -0.18)):
            if (x, z) == (0, 0.0) and dz < 0:
                continue
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.16, location=(x + dx, 0, z + dz))
            P._finish(bpy.context.active_object, M["goldbright"], 0.0)
    torus("CentreRing", 0.55, 0.06, M["goldbright"], loc=(0, 0, 3.05))
    bpy.data.objects["CentreRing"].rotation_euler = (math.pi / 2, 0, 0)
    for i in range(16):
        a = i / 16 * math.tau
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.04, location=(math.cos(a) * 0.55, -0.08, 3.05 + math.sin(a) * 0.55))
        P._finish(bpy.context.active_object, M["goldbright"], 0.0)
    return (2.9, 0.3, 4.4)


BUILD = {
    "BloodCrystal": blood_crystal,
    "IceSpike": ice_spike,
    "BoneSpike": bone_spike,
    "StoneChunk": stone_chunk,
    "HunterSigil": hunter_sigil,
    "GoldHalo": gold_halo,
    "BloodPool": blood_pool,
    "MoonDisc": moon_disc,
    "CrackedFloor": cracked_floor,
    "GraveMound": grave_mound,
    "IceFloor": ice_floor,
    "SilverStake": silver_stake,
    "GildedCross": gilded_cross,
}


def run(name):
    P.PARTS, P.GROUP, P.HINGES = [], "Main", {}
    P._img_cache.clear()  # the scene reset frees the images it cached for the previous mesh
    P.reset()
    M = mats()
    dims = BUILD[name](M)
    objs = P.join_parts(name)
    P.bake_uv(objs)
    imgs = P.bake_all(objs, name)
    P.final_material(objs, name, imgs)
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    P.export(objs, name)
    P.preview(objs, name, dims)
    print(f"[evolve] {name}: {tris} tris, dims {dims}")


if __name__ == "__main__":
    for n in (list(BUILD) if WHICH == "all" else [WHICH]):
        run(n)
