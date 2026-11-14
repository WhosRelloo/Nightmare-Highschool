"""The shop icon set (make_shop_icons.py), stage 2 of 3: the PBR render in headless Blender (Cycles).

A copy of blender_seal_icons_render.py pointed at out/shop_icons. Original header follows.


A copy of blender_training_render.py (the training HUD's stage 2) pointed at out/seal_icons, with extra materials
(parchment, blue / green / gold enamel, the four moons, kraft paper, white wax for the tinted pieces, bone, twine).


Every piece from make_training_pbr.py becomes real geometry: a grid displaced by the piece's height map (the relief is
modelled, not painted), with the full-resolution height as a bump on top. Each material id gets a full Principled
shader with its own procedural surface (brushed and scratched brass with grime in the recesses, hammered black iron,
grained leather, glossy ink and crimson enamel, waxy ivory with subsurface, chalk, oak, glass, sand, an emissive candle
flame). The lights match the main HUD bake: a warm key from the top left, a cool fill from the right, a candle rim from
below, and a warm-ceiling / dark-floor world for the reflections. Rendered with a transparent film.

  E:/Blender/blender.exe -b --factory-startup -P blender_shop_icons_render.py -- [Name ...] [--samples=N]
  -> art/ui/hud/out/shop_icons/render/<Name>.png
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MAPS = HERE / "out" / "shop_icons" / "maps"
RENDER = HERE / "out" / "shop_icons" / "render"
RENDER.mkdir(parents=True, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WANT = [a for a in argv if not a.startswith("--")]
SAMPLES = 160
for a in argv:
    if a.startswith("--samples="):
        SAMPLES = int(a.split("=")[1])

PX = 1.0 / 1024.0          # one map pixel at the 1024 work size, in metres
H_SCALE = 104.0 * PX        # the HUD bake's relief scale: height 1.0 = 68 px


def srgb(c):
    return tuple(((x / 255.0 + 0.055) / 1.055) ** 2.4 if x / 255.0 > 0.04045 else x / 255.0 / 12.92 for x in c)


# ---------------------------------------------------------------- materials (id -> params)
MATS = {
    1: dict(name="brass", col=(214, 170, 96), metal=1.0, rough=0.24, scratch=0.35, grime=0.55, detail="brushed"),
    2: dict(name="gilt", col=(244, 208, 120), metal=1.0, rough=0.16, scratch=0.15, grime=0.35, detail="fine"),
    3: dict(name="iron", col=(46, 44, 48), metal=0.85, rough=0.48, scratch=0.25, grime=0.40, detail="hammered"),
    4: dict(name="ink", col=(14, 11, 16), metal=0.0, rough=0.10, coat=1.0, detail="enamel"),
    5: dict(name="crimson_enamel", col=(118, 16, 30), metal=0.0, rough=0.12, coat=1.0, detail="enamel"),
    6: dict(name="ivory", col=(214, 200, 172), metal=0.0, rough=0.42, sss=0.08, detail="fine", grime=0.35),
    7: dict(name="leather", col=(98, 18, 28), metal=0.0, rough=0.55, detail="leather", grime=0.3),
    8: dict(name="leather_black", col=(30, 24, 26), metal=0.0, rough=0.55, detail="leather", grime=0.2),
    9: dict(name="wax", col=(226, 212, 182), metal=0.0, rough=0.35, sss=0.35, detail="fine"),
    10: dict(name="wax_red", col=(150, 22, 32), metal=0.0, rough=0.32, sss=0.25, detail="fine"),
    11: dict(name="chalk", col=(226, 226, 216), metal=0.0, rough=0.95, detail="chalk"),
    12: dict(name="glass", col=(230, 236, 240), metal=0.0, rough=0.04, glass=True, detail="none"),
    13: dict(name="flame", col=(255, 180, 70), metal=0.0, rough=0.5, emit=6.0, detail="none"),
    14: dict(name="oak", col=(92, 58, 34), metal=0.0, rough=0.5, detail="grain", grime=0.3),
    15: dict(name="sand", col=(222, 196, 140), metal=0.0, rough=0.9, detail="chalk"),
    16: dict(name="brass_old", col=(176, 130, 70), metal=1.0, rough=0.34, scratch=0.3, grime=0.6, detail="brushed"),
    17: dict(name="steel", col=(52, 62, 86), metal=1.0, rough=0.26, scratch=0.2, grime=0.3, detail="brushed"),
    18: dict(name="parchment", col=(222, 204, 164), metal=0.0, rough=0.78, detail="chalk", grime=0.45),
    19: dict(name="blue_enamel", col=(40, 70, 128), metal=0.0, rough=0.12, coat=1.0, detail="enamel"),
    20: dict(name="green_enamel", col=(22, 74, 46), metal=0.0, rough=0.12, coat=1.0, detail="enamel"),
    21: dict(name="gold_enamel", col=(196, 146, 46), metal=0.0, rough=0.14, coat=1.0, detail="enamel"),
    22: dict(name="moon", col=(226, 220, 204), metal=0.0, rough=0.88, detail="chalk", grime=0.5),
    23: dict(name="moon_dark", col=(34, 34, 46), metal=0.0, rough=0.8, detail="chalk", grime=0.2),
    24: dict(name="moon_red", col=(168, 38, 40), metal=0.0, rough=0.85, detail="chalk", grime=0.5),
    25: dict(name="moon_blue", col=(168, 194, 236), metal=0.0, rough=0.85, detail="chalk", grime=0.5),
    26: dict(name="kraft", col=(168, 120, 74), metal=0.0, rough=0.82, detail="chalk", grime=0.4),
    27: dict(name="wax_white", col=(232, 228, 222), metal=0.0, rough=0.34, sss=0.3, detail="fine", grime=0.25),
    28: dict(name="bone", col=(232, 222, 200), metal=0.0, rough=0.5, sss=0.06, detail="fine", grime=0.4),
    29: dict(name="twine", col=(150, 118, 78), metal=0.0, rough=0.9, detail="grain"),
    30: dict(name="silver", col=(206, 210, 218), metal=1.0, rough=0.2, scratch=0.25, grime=0.35, detail="brushed"),
}


def node(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


def image_node(nt, path, closest=False, loc=(0, 0)):
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = "Non-Color"
    n = node(nt, "ShaderNodeTexImage", loc)
    n.image = img
    n.interpolation = "Closest" if closest else "Cubic"
    n.extension = "EXTEND"
    return n


def micro(nt, kind, uv, normal_in, loc):
    """a material's own surface detail as a bump chained after the design's bump"""
    if kind in ("none",):
        return normal_in
    x, y = loc
    bump = node(nt, "ShaderNodeBump", (x + 400, y))
    if kind == "brushed":
        mp = node(nt, "ShaderNodeMapping", (x - 200, y))
        mp.inputs["Scale"].default_value = (1.0, 40.0, 1.0)
        nt.links.new(uv, mp.inputs["Vector"])
        nz = node(nt, "ShaderNodeTexNoise", (x, y))
        nz.inputs["Scale"].default_value = 60.0
        nz.inputs["Detail"].default_value = 6.0
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.05
        bump.inputs["Distance"].default_value = 0.0015
        h = nz.outputs["Fac"]
    elif kind == "hammered":
        vo = node(nt, "ShaderNodeTexVoronoi", (x, y))
        vo.inputs["Scale"].default_value = 45.0
        nt.links.new(uv, vo.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.003
        h = vo.outputs["Distance"]
    elif kind == "leather":
        vo = node(nt, "ShaderNodeTexVoronoi", (x, y))
        vo.inputs["Scale"].default_value = 160.0
        vo.feature = "SMOOTH_F1" if hasattr(vo, "feature") else vo.feature
        nt.links.new(uv, vo.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.35
        bump.inputs["Distance"].default_value = 0.0015
        h = vo.outputs["Distance"]
    elif kind == "chalk":
        nz = node(nt, "ShaderNodeTexNoise", (x, y))
        nz.inputs["Scale"].default_value = 220.0
        nz.inputs["Detail"].default_value = 10.0
        nz.inputs["Roughness"].default_value = 0.8
        nt.links.new(uv, nz.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.003
        h = nz.outputs["Fac"]
    elif kind == "grain":
        mp = node(nt, "ShaderNodeMapping", (x - 200, y))
        mp.inputs["Scale"].default_value = (1.0, 14.0, 1.0)
        nt.links.new(uv, mp.inputs["Vector"])
        wv = node(nt, "ShaderNodeTexWave", (x, y))
        wv.inputs["Scale"].default_value = 18.0
        wv.inputs["Distortion"].default_value = 6.0
        nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.002
        h = wv.outputs["Fac"]
    elif kind == "enamel":
        nz = node(nt, "ShaderNodeTexNoise", (x, y))
        nz.inputs["Scale"].default_value = 8.0
        nt.links.new(uv, nz.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.03
        bump.inputs["Distance"].default_value = 0.002
        h = nz.outputs["Fac"]
    else:  # fine
        nz = node(nt, "ShaderNodeTexNoise", (x, y))
        nz.inputs["Scale"].default_value = 160.0
        nz.inputs["Detail"].default_value = 3.0
        nt.links.new(uv, nz.inputs["Vector"])
        bump.inputs["Strength"].default_value = 0.035
        bump.inputs["Distance"].default_value = 0.001
        h = nz.outputs["Fac"]
    nt.links.new(h, bump.inputs["Height"])
    nt.links.new(normal_in, bump.inputs["Normal"])
    return bump.outputs["Normal"]


def bsdf_for(nt, mid, P, uv, design_normal, ao_fac, loc, piece):
    x, y = loc
    b = node(nt, "ShaderNodeBsdfPrincipled", (x + 700, y))
    col = srgb(P["col"])
    rgb = node(nt, "ShaderNodeRGB", (x + 200, y + 120))
    rgb.outputs[0].default_value = (*col, 1.0)
    base = rgb.outputs[0]
    # the gauge face: crimson (#600E1A) creeping in toward the rim
    if piece == "TrainGauge" and P["name"] == "ink":
        grad = node(nt, "ShaderNodeTexGradient", (x, y + 260), gradient_type="SPHERICAL")
        mp = node(nt, "ShaderNodeMapping", (x - 200, y + 260))
        mp.inputs["Location"].default_value = (0.5, 0.5, 0)
        mp.inputs["Scale"].default_value = (1 / 0.43, 1 / 0.43, 1)
        sep_uv = node(nt, "ShaderNodeVectorMath", (x - 400, y + 260), operation="SUBTRACT")
        nt.links.new(uv, sep_uv.inputs[0])
        sep_uv.inputs[1].default_value = (0.5, 0.5, 0)
        mp2 = node(nt, "ShaderNodeVectorMath", (x - 300, y + 300), operation="SCALE")
        nt.links.new(sep_uv.outputs[0], mp2.inputs[0])
        mp2.inputs["Scale"].default_value = 1 / 0.43
        nt.links.new(mp2.outputs[0], grad.inputs["Vector"])
        ramp = node(nt, "ShaderNodeValToRGB", (x + 200, y + 260))
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (*srgb((84, 12, 24)), 1)
        ramp.color_ramp.elements[1].position = 0.20
        ramp.color_ramp.elements[1].color = (*col, 1)
        nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
        base = ramp.outputs["Color"]
    # grime: recesses (AO) go darker and rougher
    g = P.get("grime", 0.0)
    if g > 0:
        mix = node(nt, "ShaderNodeMix", (x + 450, y + 120), data_type="RGBA", blend_type="MULTIPLY")
        inv = node(nt, "ShaderNodeMath", (x + 250, y + 200), operation="SUBTRACT")
        inv.inputs[0].default_value = 1.0
        nt.links.new(ao_fac, inv.inputs[1])
        sc = node(nt, "ShaderNodeMath", (x + 350, y + 200), operation="MULTIPLY")
        nt.links.new(inv.outputs[0], sc.inputs[0])
        sc.inputs[1].default_value = g
        nt.links.new(sc.outputs[0], mix.inputs["Factor"])
        nt.links.new(base, mix.inputs["A"])
        mix.inputs["B"].default_value = (0.18, 0.14, 0.12, 1)
        base = mix.outputs["Result"]
    nt.links.new(base, b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = P["metal"]
    # roughness: base + scratches
    rough = P["rough"]
    if P.get("scratch"):
        mp = node(nt, "ShaderNodeMapping", (x - 200, y - 200))
        mp.inputs["Scale"].default_value = (3.0, 90.0, 1.0)
        mp.inputs["Rotation"].default_value = (0, 0, 0.6 + mid * 0.37)
        nt.links.new(uv, mp.inputs["Vector"])
        nz = node(nt, "ShaderNodeTexNoise", (x, y - 200))
        nz.inputs["Scale"].default_value = 40.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        mr = node(nt, "ShaderNodeMapRange", (x + 200, y - 200))
        mr.inputs["From Min"].default_value = 0.35
        mr.inputs["From Max"].default_value = 0.75
        mr.inputs["To Min"].default_value = rough + P["scratch"] * 0.2
        mr.inputs["To Max"].default_value = max(0.05, rough - P["scratch"] * 0.15)
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    if P.get("coat"):
        b.inputs["Coat Weight"].default_value = P["coat"]
        b.inputs["Coat Roughness"].default_value = 0.06
    if P.get("sss"):
        b.inputs["Subsurface Weight"].default_value = P["sss"]
        b.inputs["Subsurface Radius"].default_value = (0.02, 0.01, 0.006)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if P.get("glass"):
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.45
    if P.get("emit"):
        b.inputs["Emission Color"].default_value = (*srgb(P["col"]), 1)
        b.inputs["Emission Strength"].default_value = P["emit"]
    nrm = micro(nt, P.get("detail", "fine"), uv, design_normal, (x - 200, y - 420))
    nt.links.new(nrm, b.inputs["Normal"])
    return b


def build_material(piece, w, h):
    mat = bpy.data.materials.new(f"M_{piece}")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (4200, 0))
    tc = node(nt, "ShaderNodeTexCoord", (-1600, 0))
    uv = tc.outputs["UV"]
    himg = image_node(nt, MAPS / f"{piece}_h.png", loc=(-1300, 300))
    nt.links.new(uv, himg.inputs["Vector"])
    dbump = node(nt, "ShaderNodeBump", (-1000, 300))
    dbump.inputs["Strength"].default_value = 1.0
    dbump.inputs["Distance"].default_value = H_SCALE * 0.35
    nt.links.new(himg.outputs["Color"], dbump.inputs["Height"])
    design_normal = dbump.outputs["Normal"]
    ao = node(nt, "ShaderNodeAmbientOcclusion", (-1000, 0))
    ao.inputs["Distance"].default_value = 0.03
    ao.samples = 8
    ao_fac = ao.outputs["AO"]
    mimg = image_node(nt, MAPS / f"{piece}_m.png", closest=True, loc=(-1300, -300))
    nt.links.new(uv, mimg.inputs["Vector"])
    mid255 = node(nt, "ShaderNodeMath", (-1000, -300), operation="MULTIPLY")
    nt.links.new(mimg.outputs["Color"], mid255.inputs[0])
    mid255.inputs[1].default_value = 255.0
    aimg = image_node(nt, MAPS / f"{piece}_a.png", loc=(-1300, -600))
    nt.links.new(uv, aimg.inputs["Vector"])
    # one shader per material present, blended by id
    present = json.loads((MAPS / f"{piece}_ids.json").read_text()) if (MAPS / f"{piece}_ids.json").exists() else list(MATS)
    shader = None
    yy0 = 1200
    for i, mid in enumerate(present):
        if mid not in MATS:
            continue
        b = bsdf_for(nt, mid, MATS[mid], uv, design_normal, ao_fac, (0, yy0 - i * 900), piece)
        if shader is None:
            shader = b.outputs[0]
            continue
        cmp = node(nt, "ShaderNodeMath", (2400, yy0 - i * 900), operation="COMPARE")
        nt.links.new(mid255.outputs[0], cmp.inputs[0])
        cmp.inputs[1].default_value = float(mid)
        cmp.inputs[2].default_value = 0.5
        mx = node(nt, "ShaderNodeMixShader", (2700, yy0 - i * 900))
        nt.links.new(cmp.outputs[0], mx.inputs["Fac"])
        nt.links.new(shader, mx.inputs[1])
        nt.links.new(b.outputs[0], mx.inputs[2])
        shader = mx.outputs[0]
    tr = node(nt, "ShaderNodeBsdfTransparent", (3300, 300))
    fin = node(nt, "ShaderNodeMixShader", (3700, 0))
    nt.links.new(aimg.outputs["Color"], fin.inputs["Fac"])
    nt.links.new(tr.outputs[0], fin.inputs[1])
    nt.links.new(shader, fin.inputs[2])
    nt.links.new(fin.outputs[0], out.inputs["Surface"])
    mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else None
    return mat


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    for t in list(bpy.data.textures):
        bpy.data.textures.remove(t)
    for i in list(bpy.data.images):
        bpy.data.images.remove(i)


def sun(name, direction, color, strength, angle=8.0):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle)
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    d = Vector(direction).normalized()
    o.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()   # the sun shines along its -Z
    return o


def setup_world():
    w = bpy.data.worlds.new("NHSealIcons") if not bpy.context.scene.world else bpy.context.scene.world
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
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    ramp = node(nt, "ShaderNodeValToRGB", (200, 0))
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.008, 0.007, 0.010, 1)
    els[1].position, els[1].color = 1.0, (0.70, 0.55, 0.38, 1)
    for pos, c in ((0.42, (0.05, 0.04, 0.045)), (0.52, (0.42, 0.33, 0.24)), (0.70, (0.95, 0.78, 0.55)), (0.84, (2.4, 1.95, 1.4))):
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
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 6
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.filter_size = 1.2
    return dev


def render_piece(info):
    name, w, h = info["name"], info["w"], info["h"]
    clear_scene()
    # which materials are present (keeps the node tree small)
    import struct  # noqa
    W, Hh = w * PX, h * PX
    res = 2 if max(w, h) > 1024 else 1
    xs, ys = max(2, int(w / (2 * res))), max(2, int(h / (2 * res)))
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=xs, y_subdivisions=ys, size=1.0)
    ob = bpy.context.active_object
    ob.scale = (W, Hh, 1)
    bpy.ops.object.transform_apply(scale=True)
    tex = bpy.data.textures.new(f"T_{name}", "IMAGE")
    img = bpy.data.images.load(str(MAPS / f"{name}_h.png"))
    img.colorspace_settings.name = "Non-Color"
    tex.image = img
    tex.extension = "EXTEND"
    md = ob.modifiers.new("relief", "DISPLACE")
    md.texture = tex
    md.texture_coords = "UV"
    md.strength = H_SCALE
    md.mid_level = 0.0
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(build_material(name, w, h))
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = max(W, Hh)
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 0, 2.0)
    bpy.context.scene.camera = cam
    sun("key", (-0.55, 0.65, 0.55), (1.0, 0.88, 0.74), 2.6, 6)
    sun("fill", (0.6, -0.35, 0.7), (0.55, 0.62, 0.9), 0.8, 12)
    sun("rim", (0.0, -0.95, 0.30), (1.0, 0.55, 0.28), 1.0, 10)
    ad = bpy.data.lights.new("softbox", "AREA")
    ad.energy, ad.size, ad.color = 14.0 * max(W, Hh) ** 2, 0.8 * max(W, Hh), (1.0, 0.9, 0.78)
    sb = bpy.data.objects.new("softbox", ad)
    bpy.context.scene.collection.objects.link(sb)
    sb.location = (-0.9 * W, 1.0 * Hh, 1.1 * max(W, Hh))
    sb.rotation_euler = (-(sb.location)).to_track_quat("-Z", "Y").to_euler()
    setup_world()
    dev = setup_render(w, h)
    bpy.context.scene.render.filepath = str(RENDER / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"rendered {name} {w}x{h} on {dev}")


def main():
    pieces = json.loads((MAPS / "pieces.json").read_text())
    for info in pieces:
        if WANT and info["name"] not in WANT:
            continue
        render_piece(info)


main()
