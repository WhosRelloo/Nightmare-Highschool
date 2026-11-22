"""Blender preview of every sky-2360 variant: a gothic school blockout + Wickfield houses, lit by tools/sky-2360/presets.py.

usage:
  python tools/sky-2360/equirect.py E:/tmp/pano                       (panoramas from art/group-upload-skies)
  blender -b --factory-startup -P tools/sky-2360/preview_scene.py -- E:/tmp/pano E:/tmp/raw [names...]
  python tools/sky-2360/post.py E:/tmp/raw docs/img/sky-2360          (Roblox-like grade + bloom, labels, sheet)

An approximation of Roblox, for judging the look, not a match: the painted sky is what the camera sees and (times the
ambient strength) what lights the scene; a sun/moon key; distance fog stands in for the Atmosphere; lamps and lit
windows are the night's light pools. Two students (a dark outfit and the crimson uniform) are the readability test.
"""
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
PANO, OUT = argv[0], argv[1]
ONLY = argv[2:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presets as PR  # noqa: E402


def rb(d):  # Roblox (x, y up, z) -> Blender (x, -z, y)
    v = Vector((d[0], -d[2], d[1]))
    return v.normalized()


def c(r, g, b):
    return (r / 255) ** 2.2, (g / 255) ** 2.2, (b / 255) ** 2.2, 1


def lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


# where the key light sits per time of day (Roblox directions); nights are lit by the moon
KEY_DIR = {"Dawn": (0.9, 0.08, -0.42), "Morning": (0.6, 0.45, -0.6), "Day": (0.3, 0.75, -0.6),
           "Golden": (-0.75, 0.22, -0.5), "Dusk": (-0.9, 0.07, -0.42), "Night": (0.45, 0.38, -0.81),
           "Witching": (0.2, 0.6, -0.78)}
NIGHTS = ("Night", "Witching")


def params(key, L, sky, moon=None, title=""):
    """Roblox look -> scene parameters (a rough, consistent mapping, so variants compare fairly)."""
    night = key in NIGHTS
    top = L["ColorShiftTop"] if any(L["ColorShiftTop"]) else (255, 250, 240)
    return dict(
        sky=sky, title=title, sun=KEY_DIR[key], col=top,
        pw=L["Brightness"] * (1.25 if night else 1.35),
        amb=(lum(L["OutdoorAmbient"]) / 100) ** 1.5 + lum(L["Ambient"]) / 120,
        fog=0.006 * L["Density"], fogc=L["AtmosphereColor"],
        lamps=key in ("Dawn", "Golden", "Dusk") + NIGHTS, moon=night and moon != "New",
        ex=L["ExposureCompensation"], gb=L["GradeBrightness"], con=L["Contrast"], sat=L["Saturation"],
        tint=L["Tint"], bloom=max(0.05, (L["Bloom"] - 0.4) * 0.55))


def variants():
    V = {}
    seasons_sky = {s: d["Skies"] for s, d in PR.SEASONS.items()}
    names = {"Dawn": "dawn 06:00", "Morning": "morning 07:30", "Day": "day 12:00", "Golden": "golden hour 17:00",
             "Dusk": "dusk 18:30", "Night": "night 23:00", "Witching": "witching hour 02:00"}
    sky_for = {"Dawn": "Dawn", "Morning": "Day", "Day": "Day", "Golden": "Day", "Dusk": "Dusk", "Night": "Night",
               "Witching": "Night"}
    for i, k in enumerate(PR.LOOKS):
        V[f"A{i}_Autumn_{k}"] = params(k, PR.resolve(k), sky_for[k], title=f"Autumn  ·  {names[k]}")
    V["A7_Autumn_Night_2.16"] = params("Night", PR.OLD_NIGHT, "Old_Night", title="Before: the 2.16 night (for comparison)")
    for i, m in enumerate(("Full", "New", "Crimson", "Blue")):
        sky = PR.MOON[m].get("Sky", "Night")
        V[f"B{i}_Moon_{m}"] = params("Night", PR.resolve("Night", moon=m), sky, moon=m, title=f"{m} moon  ·  night 23:00")
    storm = dict(PR.LOOKS["Day"], Brightness=1.5, OutdoorAmbient=(84, 86, 98), Density=0.4, AtmosphereColor=(120, 124, 136),
                 Contrast=0.02, Saturation=-0.12, Tint=(236, 240, 250))
    V["B4_Storm_Day"] = params("Day", storm, "Storm", title="Storm  ·  day (sky set NHSky = Storm)")
    j = 0
    for s in ("Winter", "Spring", "Summer", "Nightmare"):
        for k in ("Day", "Dusk", "Night"):
            if k not in seasons_sky[s]:
                continue
            V[f"C{j:02d}_{s}_{k}"] = params(k, PR.resolve(k, season=s), seasons_sky[s][k], title=f"{s} event  ·  {names[k]}")
            j += 1
    return V


P = variants()

random.seed(7)
S = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
S.render.engine = "BLENDER_EEVEE"
S.render.resolution_x, S.render.resolution_y = 1280, 720
S.view_settings.view_transform = "AgX"
S.view_settings.look = "AgX - Base Contrast"
E = S.eevee
for k, v in dict(taa_render_samples=32, use_shadows=True, volumetric_end=1600.0, volumetric_tile_size="4",
                 use_raytracing=True, shadow_ray_count=2, clamp_world=0.0).items():
    try:
        setattr(E, k, v)
    except Exception:
        pass


def mat(name, rgb, rough=0.85, emit=None, es=0.0, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = c(*rgb)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = c(*emit)
        b.inputs["Emission Strength"].default_value = es
    return m


STONE = mat("stone", (52, 48, 54))
ROOF = mat("roof", (30, 32, 40), 0.6)
GRASS = mat("grass", (34, 46, 32), 0.95)
PATH = mat("path", (96, 92, 86), 0.9)
WIN = mat("win", (40, 30, 20), 0.3, (255, 176, 80), 3.5)
DARKWIN = mat("darkwin", (14, 16, 24), 0.15)
IRON = mat("iron", (18, 18, 20), 0.5, metal=0.8)
LAMP = mat("lamp", (255, 220, 160), 0.4, (255, 196, 110), 30.0)
TREE = mat("tree", (16, 26, 20), 0.95)
DARKFIT = mat("darkfit", (14, 14, 18), 0.8)
UNIFORM = mat("uniform", (110, 18, 30), 0.75)
SKIN = mat("skin", (200, 160, 130), 0.6)
HOUSE = mat("house", (78, 70, 66), 0.9)
MOON = mat("moon", (0, 0, 0), 1, (220, 226, 255), 6.0)


def box(x, y, z, sx, sy, sz, m):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + sz / 2))
    o = bpy.context.object
    o.scale = (sx / 2, sy / 2, sz / 2)
    o.data.materials.append(m)
    return o


def gable(x, y, z, sx, sy, h, m, along="x"):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1, depth=1, location=(0, 0, 0))
    o = bpy.context.object
    # a triangular prism: a 3-sided cone is not a prism; build one from a mesh instead
    bpy.data.objects.remove(o)
    hx, hy = sx / 2, sy / 2
    if along == "x":
        vs = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (-hx, 0, h), (hx, 0, h)]
        fs = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    else:
        vs = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (0, -hy, h), (0, hy, h)]
        fs = [(1, 2, 5, 4), (3, 0, 4, 5), (0, 1, 4), (2, 3, 5), (0, 3, 2, 1)]
    me = bpy.data.meshes.new("g")
    me.from_pydata(vs, [], fs)
    ob = bpy.data.objects.new("gable", me)
    ob.location = (x, y, z)
    me.materials.append(m)
    S.collection.objects.link(ob)
    return ob


def spire(x, y, z, r, h, m, verts=4):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, depth=h, location=(x, y, z + h / 2))
    o = bpy.context.object
    if verts == 4:
        o.rotation_euler[2] = math.pi / 4
    o.data.materials.append(m)
    return o


def cyl(x, y, z, r, h, m, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=(x, y, z + h / 2))
    o = bpy.context.object
    o.data.materials.append(m)
    return o


def windows(x0, x1, y, z, n, w, h, lit=0.7):
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        box(x, y - 0.06, z, w, 0.12, h, WIN if random.random() < lit else DARKWIN)


# ground and path
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, 0))
bpy.context.object.data.materials.append(GRASS)
box(0, 45, -0.04, 6, 100, 0.06, PATH)
box(0, 82, -0.04, 70, 12, 0.06, PATH)

# the school: main hall, bell tower, wings, turrets
box(0, 95, 0, 50, 16, 15, STONE)
gable(0, 95, 15, 51, 17, 9, ROOF)
windows(-23, -6, 86.95, 2.5, 6, 1.6, 4.2)
windows(6, 23, 86.95, 2.5, 6, 1.6, 4.2)
windows(-23, -6, 86.95, 9, 6, 1.6, 4.2, 0.5)
windows(6, 23, 86.95, 9, 6, 1.6, 4.2, 0.5)
box(0, 85, 0, 10, 10, 32, STONE)
spire(0, 85, 32, 7.6, 16, ROOF)
box(0, 79.9, 0, 3.4, 0.3, 5.5, DARKWIN)
box(0, 79.88, 20, 3.2, 0.2, 3.2, WIN)  # the clock / rose window
windows(-2.5, 2.5, 79.9, 10, 2, 1.2, 4.0, 1.0)
for sx in (-1, 1):
    box(sx * 40, 93, 0, 24, 14, 11, STONE)
    gable(sx * 40, 93, 11, 25, 15, 7, ROOF)
    windows(sx * 40 - 10, sx * 40 + 10, 85.95, 3, 5, 1.5, 4.0, 0.6)
    cyl(sx * 26, 86, 0, 3.2, 22, STONE)
    spire(sx * 26, 86, 22, 4.0, 11, ROOF, 12)
    cyl(sx * 52, 86, 0, 2.4, 16, STONE)
    spire(sx * 52, 86, 16, 3.0, 8, ROOF, 12)

# Wickfield houses, mid distance on the left, a church spire beyond
for i, (x, y) in enumerate([(-34, 30), (-46, 44), (-30, 56), (-58, 62), (40, 40), (52, 58)]):
    box(x, y, 0, 9, 9, 6, HOUSE)
    gable(x, y, 6, 10, 10, 4.5, ROOF, along="y")
    box(x + 4.55, y - 1.5, 2, 0.1, 1.2, 1.6, WIN if i % 2 == 0 else DARKWIN)
    box(x - 1.5, y - 4.55, 2, 1.2, 0.1, 1.6, WIN if i % 3 else DARKWIN)
box(-90, 160, 0, 10, 16, 14, HOUSE)
box(-90, 152, 0, 6, 6, 24, HOUSE)
spire(-90, 152, 24, 4.5, 14, ROOF)

# trees
for i in range(70):
    a = random.uniform(0, math.tau)
    r = random.uniform(70, 260)
    x, y = math.cos(a) * r, 60 + math.sin(a) * r
    if abs(x) < 70 and 70 < y < 110:
        continue
    if y < 5:
        continue
    h = random.uniform(9, 20)
    cyl(x, y, 0, 0.4, h * 0.3, TREE, 6)
    spire(x, y, h * 0.25, h * 0.22, h * 0.8, TREE, 8)

# lamp posts along the path
LAMPS = []
for y in (12, 28, 44, 60, 76):
    for sx in (-1, 1):
        x = sx * 4.5
        cyl(x, y, 0, 0.09, 4.4, IRON, 8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(x, y, 4.6))
        bulb = bpy.context.object
        bulb.data.materials.append(LAMP)
        L = bpy.data.lights.new("lamp", "POINT")
        L.energy, L.color, L.shadow_soft_size = 2600, (1.0, 0.72, 0.42), 0.3
        lo = bpy.data.objects.new("lampL", L)
        lo.location = (x, y, 4.4)
        S.collection.objects.link(lo)
        LAMPS.append((bulb, lo))

# two students: a dark outfit (left) and the crimson uniform (right), the readability test
for x, m in ((-1.3, DARKFIT), (1.3, UNIFORM)):
    cyl(x, 9, 0, 0.42, 1.55, m, 16)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.33, location=(x, 9, 1.95))
    bpy.context.object.data.materials.append(SKIN if m is UNIFORM else DARKFIT)

# camera
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.lens = 22
cam.location = (0, -6, 2.4)
cam.rotation_euler = (math.radians(95), 0, 0)
S.collection.objects.link(cam)
S.camera = cam

# key light (sun or moon) and the moon disc
key = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
S.collection.objects.link(key)
key.data.angle = math.radians(1.5)
bpy.ops.mesh.primitive_uv_sphere_add(radius=34, location=(0, 0, 0))
moon = bpy.context.object
moon.data.materials.append(MOON)
moon.visible_shadow = False

# world: the painted sky is what the camera sees; lighting is the same sky times the ambient strength

# world: the painted sky is what the camera sees; lighting is the same sky times the ambient strength
W = bpy.data.worlds.new("w")
S.world = W
W.use_nodes = True
nt = W.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tex = nt.nodes.new("ShaderNodeTexEnvironment")
bg_cam = nt.nodes.new("ShaderNodeBackground")
bg_lit = nt.nodes.new("ShaderNodeBackground")
lp = nt.nodes.new("ShaderNodeLightPath")
mx = nt.nodes.new("ShaderNodeMixShader")
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tex.outputs["Color"], bg_cam.inputs["Color"])
nt.links.new(tex.outputs["Color"], bg_lit.inputs["Color"])
nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
nt.links.new(bg_lit.outputs[0], mx.inputs[1])
nt.links.new(bg_cam.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs["Surface"])

S.view_layers[0].use_pass_z = True
ct = bpy.data.node_groups.new("comp", "CompositorNodeTree")
S.compositing_node_group = ct
ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ct.nodes.new("CompositorNodeRLayers")
def M_(op):
    n = ct.nodes.new("ShaderNodeMath"); n.operation = op; return n
m1 = M_("MULTIPLY"); m2 = M_("EXPONENT"); m3 = M_("SUBTRACT"); m3.inputs[0].default_value = 1.0
lt = M_("LESS_THAN"); lt.inputs[1].default_value = 5000.0
m4 = M_("MULTIPLY")
fogmix = ct.nodes.new("ShaderNodeMix"); fogmix.data_type = "RGBA"
comp = ct.nodes.new("NodeGroupOutput")
ct.links.new(rl.outputs["Depth"], m1.inputs[0])
ct.links.new(m1.outputs[0], m2.inputs[0])
ct.links.new(m2.outputs[0], m3.inputs[1])
ct.links.new(rl.outputs["Depth"], lt.inputs[0])
ct.links.new(m3.outputs[0], m4.inputs[0])
ct.links.new(lt.outputs[0], m4.inputs[1])
ct.links.new(m4.outputs[0], fogmix.inputs[0])
ct.links.new(rl.outputs["Image"], fogmix.inputs[6])
ct.links.new(fogmix.outputs[2], comp.inputs[0])

os.makedirs(OUT, exist_ok=True)
for name, p in P.items():
    if ONLY and name not in ONLY:
        continue
    tex.image = bpy.data.images.load(f"{PANO}/{p['sky']}.png", check_existing=True)
    bg_cam.inputs["Strength"].default_value = 1.0
    bg_lit.inputs["Strength"].default_value = p["amb"]
    m1.inputs[1].default_value = -p["fog"]
    fogmix.inputs[7].default_value = c(*p["fogc"])
    d = rb(p["sun"])
    key.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    key.data.color = tuple(v / 255 for v in p["col"])
    key.data.energy = p["pw"]
    moon.location = d * 1400
    moon.hide_render = not p["moon"]
    MOON.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = c(*p["col"])
    for bulb, lo in LAMPS:
        bulb.hide_render = not p["lamps"]
        lo.hide_render = not p["lamps"]
    WIN.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3.5 if p["lamps"] else 0.3
    S.render.filepath = f"{OUT}/{name}_raw.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)

json.dump(P, open(f"{OUT}/variants.json", "w"), indent=1)
