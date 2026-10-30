# Renders the NH main-menu VFX sprites with Cycles (physically based): run with
#   blender --background --factory-startup --python render_vfx.py -- <out_dir>
# Outputs white/greyscale sprites with alpha (tinted in Roblox):
#   nh_smoke_4x4.png    volumetric smoke flipbook, 16 frames (Grid4x4), 1024x1024
#   nh_wisp.png         tileable energy wisp strip for Beams, 1024x256
#   nh_ember.png        hot ember / spark sprite, 256x256
#   nh_shards_2x2.png   lit crystal shards, 4 variants (Grid2x2), 512x512
#   nh_fog.png          soft volumetric mist sheet, 512x512
import bpy, sys, os, math, random
import numpy as np

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(__file__)
os.makedirs(out, exist_ok=True)
frames_dir = os.path.join(out, "frames")
os.makedirs(frames_dir, exist_ok=True)


def reset(res_x, res_y, samples=64):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = world
    return sc


def ortho_camera(sc, scale, loc=(0, -10, 0), rot=(math.pi / 2, 0, 0)):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = scale
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = loc
    cam.rotation_euler = rot
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def sun(sc, energy, rot, color=(1, 1, 1)):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new("Sun", d)
    o.rotation_euler = rot
    sc.collection.objects.link(o)
    return o


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return px  # bottom-up rows


def save_rgba(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("out", width=w, height=h, alpha=True)
    img.pixels = np.clip(arr, 0, 1).astype(np.float32).ravel()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def grid(paths, cols, rows, cell, path):
    sheet = np.zeros((rows * cell, cols * cell, 4), dtype=np.float32)
    for i, p in enumerate(paths):
        px = load_rgba(p)
        c, r = i % cols, i // cols
        # numpy rows are bottom-up: row 0 of the grid is the top -> highest rows
        y0 = (rows - 1 - r) * cell
        sheet[y0:y0 + cell, c * cell:(c + 1) * cell] = px
    save_rgba(sheet, path)


# ---------------------------------------------------------------------- smoke flipbook
def smoke():
    sc = reset(256, 256, samples=96)
    sc.cycles.volume_bounces = 2
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube = bpy.context.active_object
    mat = bpy.data.materials.new("Smoke")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.85, 0.86, 0.9, 1)
    vol.inputs["Anisotropy"].default_value = 0.35
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 1.7
    noise.inputs["Detail"].default_value = 9.0
    noise.inputs["Roughness"].default_value = 0.62
    noise.inputs["Distortion"].default_value = 0.35
    # spherical falloff
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.2
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "MULTIPLY"; pw.inputs[1].default_value = 14.0
    clamp = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], grad.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    nt.links.new(grad.outputs["Fac"], mul.inputs[1])
    nt.links.new(mul.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], clamp.inputs["Value"])
    nt.links.new(clamp.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], outn.inputs["Volume"])
    cube.data.materials.append(mat)
    ortho_camera(sc, 2.2)
    sun(sc, 4.0, (math.radians(50), math.radians(-30), math.radians(20)), (1.0, 0.97, 0.92))
    sun(sc, 0.8, (math.radians(-120), 0, math.radians(160)), (0.6, 0.7, 1.0))  # cool rim from behind
    paths = []
    for f in range(16):
        noise.inputs["W"].default_value = f * 0.07
        grad.inputs  # keep
        cube.scale = (1 + f * 0.012, 1 + f * 0.012, 1 + f * 0.012)
        p = os.path.join(frames_dir, f"smoke_{f:02d}.png")
        render_to(p)
        paths.append(p)
    grid(paths, 4, 4, 256, os.path.join(out, "nh_smoke_4x4.png"))


# ---------------------------------------------------------------------- tileable wisp strip
def wisp():
    sc = reset(1024, 256, samples=32)
    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.active_object
    plane.scale = (4, 1, 1)
    plane.rotation_euler = (math.pi / 2, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mat = bpy.data.materials.new("Wisp")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    em.inputs["Strength"].default_value = 1.0
    uv = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    # cylinder mapping: (cos 2pi u, sin 2pi u, v) -> perfectly tileable along u
    m2pi = nt.nodes.new("ShaderNodeMath"); m2pi.operation = "MULTIPLY"; m2pi.inputs[1].default_value = 2 * math.pi
    cosn = nt.nodes.new("ShaderNodeMath"); cosn.operation = "COSINE"
    sinn = nt.nodes.new("ShaderNodeMath"); sinn.operation = "SINE"
    vk = nt.nodes.new("ShaderNodeMath"); vk.operation = "MULTIPLY"; vk.inputs[1].default_value = 1.6
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], m2pi.inputs[0])
    nt.links.new(m2pi.outputs[0], cosn.inputs[0])
    nt.links.new(m2pi.outputs[0], sinn.inputs[0])
    nt.links.new(sep.outputs["Y"], vk.inputs[0])
    nt.links.new(cosn.outputs[0], comb.inputs["X"])
    nt.links.new(sinn.outputs[0], comb.inputs["Y"])
    nt.links.new(vk.outputs[0], comb.inputs["Z"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 12
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 1.4
    nt.links.new(comb.outputs[0], noise.inputs["Vector"])
    # vertical falloff: brightest along the middle of the strip
    vm = nt.nodes.new("ShaderNodeMath"); vm.operation = "SUBTRACT"; vm.inputs[1].default_value = 0.5
    va = nt.nodes.new("ShaderNodeMath"); va.operation = "ABSOLUTE"
    vs = nt.nodes.new("ShaderNodeMath"); vs.operation = "MULTIPLY"; vs.inputs[1].default_value = 2.0
    vinv = nt.nodes.new("ShaderNodeMath"); vinv.operation = "SUBTRACT"; vinv.inputs[0].default_value = 1.0
    vpow = nt.nodes.new("ShaderNodeMath"); vpow.operation = "POWER"; vpow.inputs[1].default_value = 1.6
    nt.links.new(sep.outputs["Y"], vm.inputs[0])
    nt.links.new(vm.outputs[0], va.inputs[0])
    nt.links.new(va.outputs[0], vs.inputs[0])
    nt.links.new(vs.outputs[0], vinv.inputs[1])
    nt.links.new(vinv.outputs[0], vpow.inputs[0])
    # contrast the noise into tendrils
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.78
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    fac = nt.nodes.new("ShaderNodeMath"); fac.operation = "MULTIPLY"
    nt.links.new(ramp.outputs["Color"], fac.inputs[0])
    nt.links.new(vpow.outputs[0], fac.inputs[1])
    boost = nt.nodes.new("ShaderNodeMath"); boost.operation = "MULTIPLY"; boost.inputs[1].default_value = 1.35
    nt.links.new(fac.outputs[0], boost.inputs[0])
    cl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(boost.outputs[0], cl.inputs["Value"])
    nt.links.new(cl.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    plane.data.materials.append(mat)
    ortho_camera(sc, 4.0)
    render_to(os.path.join(out, "nh_wisp.png"))


# ---------------------------------------------------------------------- ember sprite
def ember():
    sc = reset(256, 256, samples=32)
    sc.render.film_transparent = True
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.active_object
    plane.rotation_euler = (math.pi / 2, 0, 0)
    mat = bpy.data.materials.new("Ember")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
    nt.links.new(coord.outputs["Object"], grad.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0, 0, 0, 1)
    e[1].position, e[1].color = 1.0, (1, 1, 1, 1)
    mid = ramp.color_ramp.elements.new(0.75); mid.color = (0.35, 0.35, 0.35, 1)
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    # a faint four-point star
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    ax = nt.nodes.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"
    az = nt.nodes.new("ShaderNodeMath"); az.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["X"], ax.inputs[0])
    nt.links.new(sep.outputs["Y"], az.inputs[0])
    mn = nt.nodes.new("ShaderNodeMath"); mn.operation = "MINIMUM"
    nt.links.new(ax.outputs[0], mn.inputs[0])
    nt.links.new(az.outputs[0], mn.inputs[1])
    st = nt.nodes.new("ShaderNodeMath"); st.operation = "LESS_THAN"; st.inputs[1].default_value = 0.025
    nt.links.new(mn.outputs[0], st.inputs[0])
    stm = nt.nodes.new("ShaderNodeMath"); stm.operation = "MULTIPLY"
    nt.links.new(st.outputs[0], stm.inputs[0])
    gpow = nt.nodes.new("ShaderNodeMath"); gpow.operation = "POWER"; gpow.inputs[1].default_value = 3.0
    nt.links.new(grad.outputs["Fac"], gpow.inputs[0])
    nt.links.new(gpow.outputs[0], stm.inputs[1])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(ramp.outputs["Color"], bw.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; add.use_clamp = True
    nt.links.new(bw.outputs[0], add.inputs[0])
    nt.links.new(stm.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    plane.data.materials.append(mat)
    ortho_camera(sc, 2.0)
    render_to(os.path.join(out, "nh_ember.png"))


# ---------------------------------------------------------------------- crystal shards
def shards():
    paths = []
    random.seed(7)
    for i in range(4):
        sc = reset(256, 256, samples=96)
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.35, radius2=0.0, depth=1.6)
        top = bpy.context.active_object
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.35, radius2=0.0, depth=0.6, location=(0, 0, -1.1), rotation=(math.pi, 0, 0))
        bot = bpy.context.active_object
        top.select_set(True)
        bpy.context.view_layer.objects.active = top
        bpy.ops.object.join()
        shard = bpy.context.active_object
        shard.location = (0, 0, 0.25)
        shard.rotation_euler = (random.uniform(-0.6, 0.6), random.uniform(0, 6.28), random.uniform(-0.9, 0.9))
        shard.scale = (1, random.uniform(0.6, 1.0), 1)
        mat = bpy.data.materials.new("Shard")
        mat.use_nodes = True
        p = mat.node_tree.nodes["Principled BSDF"]
        p.inputs["Base Color"].default_value = (0.92, 0.92, 0.95, 1)
        p.inputs["Roughness"].default_value = 0.12
        p.inputs["Metallic"].default_value = 0.0
        p.inputs["Transmission Weight"].default_value = 0.35
        p.inputs["Coat Weight"].default_value = 0.6
        p.inputs["Emission Color"].default_value = (1, 1, 1, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        shard.data.materials.append(mat)
        bpy.ops.object.shade_flat()
        ortho_camera(sc, 2.6)
        sun(sc, 7.0, (math.radians(40), math.radians(-35), math.radians(30)))
        sun(sc, 3.0, (math.radians(-130), math.radians(20), math.radians(200)), (0.9, 0.95, 1.0))
        w = sc.world.node_tree.nodes["Background"]
        w.inputs[0].default_value = (0.25, 0.25, 0.3, 1)
        w.inputs[1].default_value = 0.12
        pth = os.path.join(frames_dir, f"shard_{i}.png")
        render_to(pth)
        paths.append(pth)
    grid(paths, 2, 2, 256, os.path.join(out, "nh_shards_2x2.png"))


# ---------------------------------------------------------------------- fog sheet
def fog():
    sc = reset(512, 512, samples=64)
    bpy.ops.mesh.primitive_cube_add(size=2)
    cube = bpy.context.active_object
    cube.scale = (1, 0.4, 1)
    mat = bpy.data.materials.new("Fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.9, 0.92, 1.0, 1)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.4
    noise.inputs["Detail"].default_value = 6
    noise.inputs["Roughness"].default_value = 0.55
    grad = nt.nodes.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.1
    k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = 10.0
    cl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], grad.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    nt.links.new(grad.outputs["Fac"], mul.inputs[1])
    nt.links.new(mul.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], k.inputs[0])
    nt.links.new(k.outputs[0], cl.inputs["Value"])
    nt.links.new(cl.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], o.inputs["Volume"])
    cube.data.materials.append(mat)
    ortho_camera(sc, 2.2)
    sun(sc, 3.0, (math.radians(60), 0, math.radians(30)))
    render_to(os.path.join(out, "nh_fog.png"))


which = sys.argv[sys.argv.index("--") + 2:] if "--" in sys.argv else []
jobs = {"smoke": smoke, "wisp": wisp, "ember": ember, "shards": shards, "fog": fog}
for name in (which or list(jobs)):
    jobs[name]()
    print(f"[nh_vfx] done {name}", flush=True)
