"""Shared PBR materials for the Anatomy renders (the school's seamless sets + procedural steel/glass)."""
import bpy


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def tex_mat(MAPS, name, set_name, scale=4.0, tint=None, rough_mul=1.0, metal=None, normal=0.6, flat=None):
    m, nt, bsdf = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(kind, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f"{MAPS}/NH_{set_name}_{kind}.png", check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        t.projection = "BOX"
        t.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    c = img("color")
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(c.outputs["Color"], mix.inputs[6])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    else:
        nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
    if flat:   # (rgb, how much of the map to keep): pulls a patchy map toward a clean finish
        src = bsdf.inputs["Base Color"].links[0].from_socket
        fm = nt.nodes.new("ShaderNodeMix")
        fm.data_type = "RGBA"
        fm.inputs["Factor"].default_value = flat[1]
        fm.inputs[6].default_value = (*flat[0], 1)
        nt.links.new(src, fm.inputs[7])
        nt.links.new(fm.outputs[2], bsdf.inputs["Base Color"])
    r = img("rough", True)
    rm = nt.nodes.new("ShaderNodeMath")
    rm.operation = "MULTIPLY"
    rm.inputs[1].default_value = rough_mul
    nt.links.new(r.outputs["Color"], rm.inputs[0])
    nt.links.new(rm.outputs[0], bsdf.inputs["Roughness"])
    if metal is None:
        nt.links.new(img("metal", True).outputs["Color"], bsdf.inputs["Metallic"])
    else:
        bsdf.inputs["Metallic"].default_value = metal
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal
    nt.links.new(img("normal", True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def flat_mat(name, color, rough=0.5, metal=0.0, emit=None, emit_k=0.0, coat=0.0, transmission=0.0, sss=0.0, ior=1.45):
    m, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["Subsurface Weight"].default_value = sss
    bsdf.inputs["IOR"].default_value = ior
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = emit_k
    return m


def steel_mat(name, color=(0.62, 0.62, 0.62), rough=(0.12, 0.3), aniso=0.6, grit=0.0, knurl=0.0):
    """Polished/brushed steel: noise-varied roughness, anisotropy, optional grit or diamond-knurl bump."""
    m, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Anisotropic"].default_value = aniso
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0
    nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = rough[0]
    ramp.inputs["To Max"].default_value = rough[1]
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    height = None
    if knurl:
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        w1 = nt.nodes.new("ShaderNodeTexWave")
        w2 = nt.nodes.new("ShaderNodeTexWave")
        for w, d in ((w1, "X"), (w2, "Y")):
            w.wave_type = "BANDS"
            w.bands_direction = "DIAGONAL"
            w.inputs["Scale"].default_value = 900.0
            w.wave_profile = "TRI"
        rot = nt.nodes.new("ShaderNodeVectorRotate")
        rot.rotation_type = "Z_AXIS"
        rot.inputs["Angle"].default_value = 1.5708
        nt.links.new(tc.outputs["Object"], w1.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], rot.inputs["Vector"])
        nt.links.new(rot.outputs["Vector"], w2.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = "MINIMUM"
        nt.links.new(w1.outputs["Color"], mx.inputs[0])
        nt.links.new(w2.outputs["Color"], mx.inputs[1])
        height, k = mx, knurl
    elif grit:
        height, k = nz, grit
    if height is not None:
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = k
        bump.inputs["Distance"].default_value = 0.0003
        nt.links.new(height.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def make(MAPS):
    return {
        "desk": tex_mat(MAPS, "Desk", "DeskWood", 2.2, tint=(0.3, 0.18, 0.11), normal=0.8),
        "brass": tex_mat(MAPS, "Brass", "Brass", 22.0, rough_mul=0.5, metal=1.0, flat=((0.86, 0.62, 0.3), 0.2)),
        "brass_dark": tex_mat(MAPS, "BrassDark", "Brass", 22.0, rough_mul=0.75, metal=1.0, flat=((0.5, 0.36, 0.18), 0.25)),
        "iron": tex_mat(MAPS, "Iron", "Iron", 8.0, tint=(0.16, 0.15, 0.17)),
        "leather": tex_mat(MAPS, "Leather", "Leather", 7.0, tint=(0.16, 0.08, 0.045), metal=0.0),
        "leather_dk": tex_mat(MAPS, "LeatherDk", "Leather", 7.0, tint=(0.07, 0.035, 0.025), metal=0.0),
        "rosewood": tex_mat(MAPS, "Rosewood", "DeskWood", 22.0, tint=(0.11, 0.03, 0.018), rough_mul=0.8, metal=0.0, normal=0.35),
        "ebony": tex_mat(MAPS, "Ebony", "DeskWood", 26.0, tint=(0.09, 0.06, 0.05), rough_mul=0.45, metal=0.0, normal=0.3),
        "steel": steel_mat("Steel", grit=0.05),
        "steel_bright": steel_mat("SteelBright", (0.78, 0.78, 0.8), (0.04, 0.1), aniso=0.3),
        "steel_dark": steel_mat("SteelKnurl", (0.4, 0.4, 0.41), (0.3, 0.45), aniso=0.0, knurl=0.6),
        "glass": flat_mat("Glass", (0.92, 0.96, 1.0), 0.0, transmission=1.0, ior=1.52),
        "porcelain": flat_mat("Porcelain", (0.93, 0.9, 0.84), 0.18, coat=0.6),
        "wax": flat_mat("Wax", (0.16, 0.025, 0.02), 0.38, sss=0.15),
        "cavity": flat_mat("Cavity", (0.03, 0.025, 0.03), 0.6, 0.6),
        "heart": flat_mat("Heart", (0.5, 0.008, 0.015), 0.08, emit=(0.9, 0.04, 0.02), emit_k=2.2, transmission=0.15, coat=0.8),
        "lacquer": flat_mat("Lacquer", (0.09, 0.012, 0.012), 0.32, coat=0.7),
        "copper": tex_mat(MAPS, "Copper", "Brass", 9.0, tint=(0.95, 0.5, 0.36), rough_mul=0.8),
        "glow": flat_mat("Glow", (1.0, 0.85, 0.5), 0.3, emit=(1.0, 0.78, 0.4), emit_k=14.0),
        "pupil": flat_mat("Pupil", (0.01, 0.01, 0.01), 0.05, coat=1.0),
        "flame": flat_mat("Flame", (1.0, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.18), emit_k=40.0),
        "candle": flat_mat("Candle", (0.85, 0.78, 0.62), 0.5, sss=0.4),
        "chalk": flat_mat("Chalk", (0.75, 0.62, 0.36), 0.9, emit=(0.92, 0.72, 0.36), emit_k=0.35),
    }
