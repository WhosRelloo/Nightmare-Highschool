"""The admin teleport crow (Blender 5.x, headless).

  "E:/Blender/blender.exe" --background --factory-startup --python art/vfx/crow/nh_crow.py -- [--size 2048] [--gpu]
        [--nobake] [--preview] [--mock] [--out E:/NH-Work/crow]

One skinned mesh, one material, in studs (1 Blender unit = 1 stud), facing -Y, wings spread flat (the rest pose).
  body + head + beak   one loft (so the neck has no seam), contour feathers painted on
  wings                a covert surface (arm and hand) and seven separate primaries, the outer five fingered
  tail                 nine fanned tail feathers, a slight wedge
  eyes                 two small spheres; the iris carries an emissive mask (a faint crimson glint in Roblox)
Wings and tail are single surfaces: the Roblox MeshPart is DoubleSided.

The rig (11 bones): Root > Body > Neck > Head, Body > Tail, Body > Wing{L,R}1 > Wing{L,R}2 > Wing{L,R}3.
Roblox flaps it on the client (Bone.Transform), so nothing has to be published.

Maps (2048): each vertex carries a feather coordinate (a corner colour attribute: u, v, part). That is baked
into the bake UV, then the feathers are painted per pixel in numpy: contour scallops on the body, rows of
coverts on the wing, barbed vanes with a rachis on every flight feather. Colour, a tangent normal map from the
painted height, roughness and the eye's emissive mask; colour is multiplied by a soft baked AO.
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SIZE = int(argv[argv.index("--size") + 1]) if "--size" in argv else 2048
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/crow"
GPU = "--gpu" in argv
os.makedirs(OUT, exist_ok=True)
NAME = "NHCrow"


# ------------------------------------------------------------------ scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    if GPU:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            if [d for d in prefs.devices if d.type == kind]:
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                break
    return sc


# ------------------------------------------------------------------ geometry
# every builder appends to one bmesh; each face's corners get a feather coordinate (u, v, part)

BM = None
FUV = []          # per face: list of (u, v, code) per corner, in face-loop order
PART_BODY, PART_WING, PART_PRIM, PART_TAIL, PART_EYE = 0, 1, 2, 3, 4


def code(part, idx=0):
    return 0.05 + part * 0.1 + idx * 0.004


def face(verts, coords):
    f = BM.faces.new(verts)
    FUV.append((f, coords))
    return f


def catmull(pts, t):
    """A Catmull-Rom spline through pts (list of tuples) at t in [0, 1]."""
    n = len(pts) - 1
    x = min(n - 1e-6, max(0.0, t * n))
    i = int(x)
    f = x - i
    p0 = np.array(pts[max(0, i - 1)])
    p1 = np.array(pts[i])
    p2 = np.array(pts[min(n, i + 1)])
    p3 = np.array(pts[min(n, i + 2)])
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


# (y, z, half width, half height, bottom squash): tail base to beak tip
PROFILE = [
    (0.46, 0.030, 0.050, 0.040, 1.0),
    (0.34, 0.010, 0.120, 0.095, 1.0),
    (0.16, -0.005, 0.175, 0.150, 1.08),
    (-0.04, 0.000, 0.190, 0.165, 1.12),
    (-0.22, 0.030, 0.160, 0.145, 1.05),
    (-0.36, 0.070, 0.112, 0.118, 1.0),
    (-0.45, 0.095, 0.108, 0.118, 1.0),
    (-0.54, 0.102, 0.104, 0.108, 1.0),
    (-0.615, 0.098, 0.080, 0.088, 1.0),
    (-0.665, 0.080, 0.050, 0.060, 1.0),
    (-0.745, 0.064, 0.027, 0.036, 1.0),
    (-0.815, 0.040, 0.006, 0.010, 1.0),
]
BEAK_T = 0.80      # t along the loft where the beak starts


def body(rings=28, around=14):
    secs = []
    for i in range(rings + 1):
        t = i / rings
        t2 = t ** 0.92
        y, z, w, h, sq = catmull(PROFILE, t2)
        ring = []
        for j in range(around):
            a = j / around * 2 * math.pi
            s, c = math.sin(a), math.cos(a)   # a = 0 on top
            hh = h * (sq if c < 0 else 1.0)
            # a slightly flatter back and a keeled belly
            x = w * s * (1 - 0.06 * c * c)
            zz = z + hh * c * (1 + 0.05 * (c < 0) * s * s)
            if t > BEAK_T:   # the beak: taller than wide, a culmen ridge on top
                x *= 0.85
                if c > 0.8:
                    zz += 0.006 * (1 - t)
            ring.append(BM.verts.new((x, y, zz)))
        secs.append((t, ring))
    for i in range(rings):
        t0, r0 = secs[i]
        t1, r1 = secs[i + 1]
        for j in range(around):
            j2 = (j + 1) % around
            a0, a1 = j / around, (j + 1) / around
            cd = code(PART_BODY)
            face([r0[j], r0[j2], r1[j2], r1[j]], [(a0, t0, cd), (a1, t0, cd), (a1, t1, cd), (a0, t1, cd)])
    # caps
    for (t, ring), flip in ((secs[0], True), (secs[-1], False)):
        c = BM.verts.new(sum((v.co for v in ring), Vector()) / len(ring))
        for j in range(around):
            j2 = (j + 1) % around
            vs = [ring[j], ring[j2], c] if not flip else [ring[j2], ring[j], c]
            cd = code(PART_BODY)
            face(vs, [(0.5, t, cd)] * 3)


def eye(sx):
    """A small sphere on the side of the head, looking out and a little forward."""
    c = Vector((sx * 0.088, -0.565, 0.118))
    r = 0.024
    axis = Vector((sx * 1.0, -0.45, 0.15)).normalized()
    seg, rings = 8, 5
    rot = Vector((0, 0, 1)).rotation_difference(axis).to_matrix()
    grid = []
    for i in range(rings + 1):
        th = i / rings * math.pi
        row = []
        for j in range(seg):
            ph = j / seg * 2 * math.pi
            p = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))) * r
            row.append((BM.verts.new(c + rot @ p), th / math.pi))
        grid.append(row)
    cd = code(PART_EYE)
    for i in range(rings):
        for j in range(seg):
            j2 = (j + 1) % seg
            q = [grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]]
            vs = [v for v, _ in q]
            if len(set(vs)) < 4:
                continue
            face(vs, [(k, 0.0, cd) for _, k in q])


def wing_planform(x):
    """Leading and trailing edge y and the camber at span x (right wing), for the covert surface."""
    le = catmull([(-0.215,), (-0.270,), (-0.285,), (-0.262,), (-0.185,)], (x - 0.12) / 0.90)[0]
    te = catmull([(0.300,), (0.385,), (0.370,), (0.255,), (0.020,)], (x - 0.12) / 0.90)[0]
    return le, te


def wing(sx, nu=10, nv=5):
    """The covert surface from the shoulder to just past the wrist, cambered."""
    rows = []
    for i in range(nu + 1):
        u = i / nu
        x = 0.12 + 0.90 * u
        le, te = wing_planform(x)
        row = []
        for k in range(nv + 1):
            v = k / nv
            y = le + (te - le) * (v ** 0.9)
            z = 0.075 + 0.035 * math.sin(math.pi * min(1, v * 1.3)) * (1 - 0.5 * u) - 0.02 * u * u
            row.append((BM.verts.new((sx * x, y, z)), u, v))
        rows.append(row)
    cd = code(PART_WING)
    for i in range(nu):
        for k in range(nv):
            q = [rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]]
            if sx < 0:
                q = q[::-1]
            face([a for a, _, _ in q], [(u, v, cd) for _, u, v in q])
    # the secondaries: a fringe of rounded feather tips along the arm's trailing edge (a scalloped silhouette)
    n_sec = 12
    for s in range(n_sec):
        x0 = 0.16 + (0.74 - 0.16) * s / n_sec
        x1 = 0.16 + (0.74 - 0.16) * (s + 1.3) / n_sec
        xm = (x0 + x1) / 2
        _, te0 = wing_planform(x0)
        _, te1 = wing_planform(x1)
        _, tem = wing_planform(xm)
        L = 0.06 + 0.015 * math.sin(s * 1.7)
        z0 = 0.075 - 0.02 * ((x0 - 0.12) / 0.90) ** 2
        z1 = 0.075 - 0.02 * ((x1 - 0.12) / 0.90) ** 2
        base0 = BM.verts.new((sx * x0, te0 - 0.04, z0 + 0.004))
        base1 = BM.verts.new((sx * x1, te1 - 0.04, z1 + 0.004))
        tip0 = BM.verts.new((sx * (x0 + 0.01), te0 + L * 0.8, z0 - 0.006))
        tip1 = BM.verts.new((sx * (x1 - 0.01), te1 + L * 0.8, z1 - 0.006))
        tipm = BM.verts.new((sx * xm, tem + L, (z0 + z1) / 2 - 0.008))
        cd = code(PART_PRIM, 7 + s % 5)
        q1 = [base0, base1, tip1, tipm, tip0]
        c1 = [(-1, 0.0, cd), (1, 0.0, cd), (1, 0.8, cd), (0, 1.0, cd), (-1, 0.8, cd)]
        if sx < 0:
            q1, c1 = q1[::-1], c1[::-1]
        face(q1, c1)


def vane(prefix_code, root, direction, side, L, W, droop=0.0, curl=0.0, emarg=0.0, segs=4, sx=1):
    """One flight feather: a strip with a raised rachis, from root along direction, `side` the vane's width axis.
    emarg narrows the outer half (the fingered primaries)."""
    root, d, s = Vector(root), Vector(direction).normalized(), Vector(side).normalized()
    up = d.cross(s).normalized()
    if up.z < 0:
        up = -up
    cols = []
    for i in range(segs + 1):
        t = i / segs
        # width: full in the middle, a rounded tip; emarginated feathers taper hard past half way
        w = W * (math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.35)
        if emarg and t > 0.45:
            w *= 1 - emarg * min(1, (t - 0.45) / 0.25)
        if t == 1:
            w *= 0.55
        p = root + d * (L * t) + up * (-droop * t * t) + s * (curl * t * t)
        lead = p - s * (w * 0.35)
        rach = p + up * (0.006 * (1 - t))
        trail = p + s * (w * 0.65)
        cols.append([(BM.verts.new(lead), -1, t), (BM.verts.new(rach), 0, t), (BM.verts.new(trail), 1, t)])
    for i in range(segs):
        for k in range(2):
            q = [cols[i][k], cols[i][k + 1], cols[i + 1][k + 1], cols[i + 1][k]]
            if sx < 0:
                q = q[::-1]
            face([a for a, _, _ in q], [(w, t, prefix_code) for _, w, t in q])


def primaries(sx):
    n = 7
    for k in range(n):
        f = k / (n - 1)
        rx = 0.74 + 0.16 * f
        ry = 0.22 - 0.38 * f
        ang = math.radians(50 - 52 * f)                 # inner ones sweep back, the outer point out and forward
        L = 0.40 + 0.18 * math.sin(math.pi * min(1, f * 1.15)) + 0.04 * f
        W = 0.135 - 0.04 * f
        d = Vector((math.cos(ang), math.sin(ang), -0.06 * f))
        side = Vector((-math.sin(ang), math.cos(ang), 0))   # trailing side (toward +Y)
        z = 0.062 - 0.006 * k
        root = Vector((rx, ry, z))
        if sx < 0:
            root.x, d.x, side.x = -root.x, -d.x, -side.x
        vane(code(PART_PRIM, k), root, d, side, L, W, droop=0.04 + 0.02 * f, curl=-0.03 * f,
             emarg=0.45 if k >= 2 else 0.0, sx=sx)


def tail():
    n = 9
    for k in range(n):
        f = k / (n - 1) * 2 - 1                         # -1 .. 1 across the fan
        ang = math.radians(90 + 26 * f)
        L = 0.50 - 0.07 * f * f                         # a slight wedge: the centre feathers longest
        d = Vector((math.cos(ang), math.sin(ang), -0.02))
        side = Vector((math.sin(ang), -math.cos(ang), 0))
        root = Vector((0.03 * f, 0.36, 0.035 - 0.004 * abs(f) + 0.002 * k))
        vane(code(PART_TAIL, k), root, d, side, L, 0.10, droop=-0.01, curl=0.0, segs=4, sx=1 if f >= 0 else 1)


def build():
    global BM
    BM = bmesh.new()
    body()
    for sx in (1, -1):
        eye(sx)
        wing(sx)
        primaries(sx)
    tail()
    me = bpy.data.meshes.new(NAME)
    BM.to_mesh(me)
    # corner feather coordinates
    attr = me.color_attributes.new("fuv", "FLOAT_COLOR", "CORNER")
    BM.faces.index_update()
    idx = {f.index: c for f, c in FUV}
    data = np.zeros((len(me.loops), 4), dtype=np.float32)
    for p in me.polygons:
        cs = idx[p.index]
        us = [c[0] for c in cs]
        # the body wraps round: a face spanning the seam gets its small u lifted by 1
        if cs[0][2] < 0.1 and max(us) - min(us) > 0.5:
            us = [u + 1 if u < 0.5 else u for u in us]
        for k, li in enumerate(p.loop_indices):
            data[li] = (us[k], cs[k][1], cs[k][2], 1.0)
    attr.data.foreach_set("color", data.ravel())
    BM.free()
    ob = bpy.data.objects.new(NAME, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


# ------------------------------------------------------------------ rig

BONES = {
    # name: (head, tail, parent)
    "Root": ((0, 0.05, 0), (0, -0.10, 0), None),
    "Body": ((0, 0.22, 0.0), (0, -0.26, 0.03), "Root"),
    "Neck": ((0, -0.30, 0.05), (0, -0.45, 0.095), "Body"),
    "Head": ((0, -0.45, 0.095), (0, -0.80, 0.05), "Neck"),
    "Tail": ((0, 0.36, 0.03), (0, 0.86, 0.0), "Body"),
}
for _s, _n in ((1, "R"), (-1, "L")):
    BONES[f"Wing{_n}1"] = ((_s * 0.12, -0.17, 0.075), (_s * 0.42, -0.15, 0.075), "Body")
    BONES[f"Wing{_n}2"] = ((_s * 0.42, -0.15, 0.075), (_s * 0.73, -0.13, 0.07), f"Wing{_n}1")
    BONES[f"Wing{_n}3"] = ((_s * 0.73, -0.13, 0.07), (_s * 1.35, -0.03, 0.05), f"Wing{_n}2")


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def rig(ob):
    arm = bpy.data.armatures.new(NAME + "Rig")
    ao = bpy.data.objects.new(NAME + "Rig", arm)
    bpy.context.scene.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode="EDIT")
    for n, (h, t, p) in BONES.items():
        b = arm.edit_bones.new(n)
        b.head, b.tail = h, t
        b.roll = 0
        if p:
            b.parent = arm.edit_bones[p]
            b.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    groups = {n: ob.vertex_groups.new(name=n) for n in BONES}
    fuv = ob.data.color_attributes["fuv"].data
    vpart = {}
    for p in ob.data.polygons:
        for li, vi in zip(p.loop_indices, p.vertices):
            vpart[vi] = fuv[li].color[2]
    for v in ob.data.vertices:
        x, y, z = v.co
        ax = abs(x)
        side = "R" if x > 0 else "L"
        part = int((vpart.get(v.index, 0.05) - 0.05) / 0.1 + 0.5)
        w = {}
        if part in (PART_WING, PART_PRIM) and ax > 0.1:
            w1 = 1 - smooth(0.32, 0.48, ax)
            w3 = smooth(0.66, 0.80, ax)
            w2 = 1 - w1 - w3
            root = 1 - smooth(0.12, 0.22, ax)            # the shoulder blends into the body
            w = {f"Wing{side}1": w1 * (1 - root), f"Wing{side}2": w2, f"Wing{side}3": w3, "Body": w1 * root}
        elif part == PART_TAIL or (part == PART_BODY and y > 0.40):
            tw = smooth(0.30, 0.46, y)
            w = {"Tail": tw, "Body": 1 - tw}
        else:
            hw = smooth(-0.34, -0.46, y)
            nw = smooth(-0.22, -0.34, y) * (1 - hw)
            w = {"Head": hw, "Neck": nw, "Body": max(0.0, 1 - hw - nw)}
        for n, val in w.items():
            if val > 0.002:
                groups[n].add([v.index], val, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = ao
    ob.parent = ao
    return ao


def pose(ao, phase, amp=1.0, glide=0.0):
    """The flap: the arm leads, the forearm and the hand follow a little later (the wingtip whips)."""
    pb = ao.pose.bones
    for n in pb:
        n.rotation_mode = "XYZ"
        n.rotation_euler = (0, 0, 0)
    for s, side in ((1, "R"), (-1, "L")):
        a1 = math.radians(48) * math.sin(phase) * amp + math.radians(8) * glide
        a2 = math.radians(14) * math.sin(phase - 0.6) * amp
        a3 = math.radians(24) * math.sin(phase - 1.1) * amp
        sweep = math.radians(10) * max(0, -math.sin(phase)) * amp   # the hand sweeps forward on the downstroke
        for bn, a in ((f"Wing{side}1", a1), (f"Wing{side}2", a2), (f"Wing{side}3", a3)):
            b = pb[bn]
            # rotate about the world forward axis (Y), expressed in the bone's rest frame
            rest = b.bone.matrix_local.to_3x3()
            axis = rest.inverted() @ Vector((0, 1, 0))
            q = Matrix.Rotation(-s * a, 3, axis)
            if bn.endswith("3"):
                q = Matrix.Rotation(s * sweep, 3, rest.inverted() @ Vector((0, 0, 1))) @ q
            b.rotation_mode = "QUATERNION"
            b.rotation_quaternion = q.to_quaternion()
    pb["Body"].rotation_mode = "XYZ"
    pb["Body"].rotation_euler = (0.04 * math.sin(phase + 1.5) * amp, 0, 0)
    pb["Tail"].rotation_mode = "XYZ"
    pb["Tail"].rotation_euler = (0.08 * math.sin(phase + 2.2) * amp, 0, 0)
    pb["Head"].rotation_mode = "XYZ"
    pb["Head"].rotation_euler = (-0.05 * math.sin(phase + 1.5) * amp, 0, 0)


# ------------------------------------------------------------------ maps

def bake_uv(ob):
    me = ob.data
    uv = me.uv_layers.new(name="Bake")
    me.uv_layers.active = uv
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.6)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=8 / SIZE, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_maps(ob):
    sc = bpy.context.scene
    sc.cycles.samples = 64
    bk = sc.render.bake
    bk.margin = 16
    bk.use_selected_to_active = False
    m = bpy.data.materials.new("Bake")
    m.use_nodes = True
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "fuv"
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(at.outputs["Color"], em.inputs["Color"])
    tgt = nt.nodes.new("ShaderNodeTexImage")
    nt.nodes.active = tgt
    ob.data.materials.clear()
    ob.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

    fimg = bpy.data.images.new("fuv", SIZE, SIZE, alpha=False, float_buffer=True)
    fimg.colorspace_settings.name = "Non-Color"
    tgt.image = fimg
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    sc.cycles.samples = 1
    bk.margin = 6   # a feather coordinate must not bleed far (the painting is per island)
    bpy.ops.object.bake(type="EMIT")
    F = np.array(fimg.pixels[:], dtype=np.float32).reshape(SIZE, SIZE, 4)

    aimg = bpy.data.images.new("ao", SIZE, SIZE, alpha=False, float_buffer=False)
    aimg.colorspace_settings.name = "Non-Color"
    tgt.image = aimg
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    sc.cycles.samples = 96
    bk.margin = 16
    sc.world = sc.world or bpy.data.worlds.new("W")
    bpy.ops.object.bake(type="AO")
    A = np.array(aimg.pixels[:], dtype=np.float32).reshape(SIZE, SIZE, 4)[:, :, 0]
    return F, A


def hash2(a, b):
    return np.modf(np.sin(a * 127.1 + b * 311.7) * 43758.5453)[0] % 1.0


def shingle(p, q, cols_jit=0.5):
    """Overlapping rounded feathers in rows: p across, q along (increasing toward the feather tips).
    Returns height 0..1, an edge mask (the visible tip arc) and a per-feather random."""
    row = np.floor(q)
    pp = p + cols_jit * (row % 2)
    col = np.floor(pp)
    cx = pp - col - 0.5
    cy = q - row
    rnd = hash2(row, col)
    edge = 0.78 + 0.08 * (rnd - 0.5) - 1.5 * cx * cx
    on = cy < edge
    h = np.where(on, (cy / np.maximum(edge, 0.05)) ** 1.4, 0.15 * (cy - edge) / np.maximum(1 - edge, 0.05))
    em = np.exp(-((cy - edge) / 0.06) ** 2) * on
    return h, em, rnd


def paint(F, A):
    u, v, c = F[:, :, 0], F[:, :, 1], F[:, :, 2]
    cover = c > 0.02
    part = np.clip(np.floor((c - 0.05) / 0.1 + 0.5), 0, 4).astype(np.int32)
    idx = np.round((c - 0.05 - part * 0.1) / 0.004)
    H = np.zeros_like(u)
    col_var = np.zeros_like(u)        # per feather tone
    sheen = np.zeros_like(u)          # edge sheen (blue-violet)
    rough = np.full_like(u, 0.55)
    emis = np.zeros_like(u)
    base = np.zeros(u.shape + (3,), dtype=np.float32)
    BLACK = np.array([0.0065, 0.0068, 0.0085])
    SHEEN = np.array([0.020, 0.024, 0.046])
    BEAK = np.array([0.013, 0.013, 0.015])

    # body: contour feathers, finer on the head; tips point toward the tail
    m = cover & (part == PART_BODY)
    t = v
    # rows get finer toward the head (q falls faster there) but never fold back on themselves
    q = 40 * np.power(np.clip(1 - t, 0, 1), 0.8)
    p = u * 22
    h, e, r = shingle(p, q)
    barb = 0.5 + 0.5 * np.sin((q * 9 + np.abs((p % 1) - 0.5) * 14) * math.pi)
    H = np.where(m, h * 0.8 + 0.05 * barb, H)
    sheen = np.where(m, e * 0.7 + 0.25 * h, sheen)
    col_var = np.where(m, 0.5 + 0.5 * (r - 0.5), col_var)
    beak = m & (t > 0.80)
    bristle = m & (t > 0.75) & (t <= 0.80) & (np.cos(u * 2 * math.pi) > 0.35)   # over the top of the beak base only
    H = np.where(beak, 0.3 + 0.08 * np.sin(u * 2 * math.pi * 3) * (t - 0.8) * 4, H)
    sheen = np.where(beak, 0.1, sheen)
    rough = np.where(beak, 0.30, rough)
    # nasal bristles: fine forward strokes over the beak base
    st = 0.5 + 0.5 * np.sin(u * 2 * math.pi * 42 + t * 30)
    H = np.where(bristle, 0.45 + 0.2 * st, H)
    sheen = np.where(bristle, 0.18 * st, sheen)

    # wing coverts: rows getting larger toward the trailing edge
    m = cover & (part == PART_WING)
    zones = [(0.0, 0.26, 34, 3.2), (0.26, 0.48, 24, 2.2), (0.48, 1.01, 15, 1.6)]
    for a, b, ncol, nrow in zones:
        z = m & (v >= a) & (v < b)
        q = (v - a) / (b - a) * nrow
        p = u * ncol
        h, e, r = shingle(p, q)
        bb = 0.5 + 0.5 * np.sin((q * 7 + np.abs((p % 1) - 0.5) * 10) * math.pi)
        H = np.where(z, h * 0.85 + 0.06 * bb, H)
        sheen = np.where(z, e * 0.8 + 0.3 * h, sheen)
        col_var = np.where(z, 0.5 + 0.45 * (r - 0.5), col_var)

    # flight feathers (primaries, secondaries, tail): a vane with a rachis and barbs
    m = cover & ((part == PART_PRIM) | (part == PART_TAIL))
    w, s = u, v                       # w across -1..1 (0 at the rachis), s along 0..1
    rach = np.exp(-(w / 0.07) ** 2)
    vane_h = np.sqrt(np.clip(1 - np.abs(w) ** 2.2, 0, 1))
    barbs = 0.5 + 0.5 * np.sin((s * 70 + np.abs(w) * 22 + idx * 3.1) * math.pi)
    # a few splits in the vane, like real feathers
    split = (np.sin(s * 23 + idx * 5.0) > 0.93) & (np.abs(w) > 0.3)
    hh = 0.55 * vane_h + 0.35 * rach + 0.08 * barbs - 0.25 * split
    H = np.where(m, hh, H)
    sheen = np.where(m, 0.35 * vane_h * (0.6 + 0.4 * barbs) + 0.4 * rach, sheen)
    col_var = np.where(m, hash2(idx, part * 1.0) * 0.6 + 0.2 * s, col_var)
    rough = np.where(m, 0.5 - 0.12 * rach, rough)

    # eyes: a black glossy ball with a crimson iris ring (the emissive mask)
    m = cover & (part == PART_EYE)
    k = u                              # 0 at the outward pole, 1 at the back
    iris = (k > 0.10) & (k < 0.27)
    pupil = k <= 0.10
    rough = np.where(m, 0.06, rough)
    H = np.where(m, 0.5, H)
    emis = np.where(m & iris, 1.0 - np.abs(k - 0.185) / 0.085 * 0.6, emis)

    # compose colour
    tone = 0.75 + 0.5 * col_var
    for ch in range(3):
        b = BLACK[ch] * tone + SHEEN[ch] * np.clip(sheen, 0, 1)
        b = np.where(beak, BEAK[ch] * (1 + 0.3 * H), b)
        b = np.where(cover & (part == PART_EYE), 0.003, b)
        b = np.where(cover & (part == PART_EYE) & iris, [0.30, 0.025, 0.045][ch], b)
        b = np.where(cover & (part == PART_EYE) & pupil, 0.001, b)
        base[:, :, ch] = b
    ao = 0.45 + 0.55 * np.clip(A, 0, 1)
    base *= ao[:, :, None]
    rough = np.clip(rough + 0.08 * (1 - np.clip(sheen, 0, 1)), 0.04, 0.9)

    # tangent normals from the painted height (gradient in UV pixel space = tangent space; OpenGL +Y)
    Hs = H.copy()
    gx = np.zeros_like(Hs)
    gy = np.zeros_like(Hs)
    gx[:, 1:-1] = (Hs[:, 2:] - Hs[:, :-2]) * 0.5
    gy[1:-1, :] = (Hs[2:, :] - Hs[:-2, :]) * 0.5
    # a jump between islands or parts is not a slope
    lim = 0.25
    gx = np.clip(gx, -lim, lim)
    gy = np.clip(gy, -lim, lim)
    strength = 3.0 * SIZE / 2048
    nx, ny = -gx * strength, -gy * strength
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    N = np.stack([nx / ln, ny / ln, nz / ln], axis=2) * 0.5 + 0.5
    N[~cover] = (0.5, 0.5, 1.0)
    return base, N, rough, emis


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def save(name, arr, srgb=False):
    a = to_srgb(arr) if srgb else np.clip(arr, 0, 1)
    if a.ndim == 2:
        a = np.stack([a, a, a], axis=2)
    h, w = a.shape[:2]
    rgba = np.concatenate([a, np.ones((h, w, 1), dtype=np.float32)], axis=2).astype(np.float32)
    im = bpy.data.images.new(f"out_{name}", w, h, alpha=False, float_buffer=False)
    im.colorspace_settings.name = "Non-Color"     # values are already encoded; write them as they are
    im.pixels.foreach_set(rgba.ravel())
    p = os.path.join(OUT, f"{NAME}_{name}.png")
    im.filepath_raw = p
    im.file_format = "PNG"
    im.save()
    return p


def final_material(ob, paths):
    m = bpy.data.materials.new(NAME)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def tex(p, nonc=True):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(p)
        if nonc:
            t.image.colorspace_settings.name = "Non-Color"
        return t
    nt.links.new(tex(paths["color"], False).outputs["Color"], bs.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(paths["normal"]).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex(paths["rough"]).outputs["Color"], bs.inputs["Roughness"])
    et = tex(paths["emissive"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(et.outputs["Color"], mul.inputs["A"])
    mul.inputs["B"].default_value = (0.62, 0.05, 0.09, 1)
    nt.links.new(mul.outputs["Result"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 1.2
    ob.data.materials.clear()
    ob.data.materials.append(m)
    for uv in list(ob.data.uv_layers):
        if uv.name != "Bake":
            ob.data.uv_layers.remove(uv)
    return m


def flat_material(ob):
    m = bpy.data.materials.new("Flat")
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.01, 0.01, 0.013, 1)
    bs.inputs["Roughness"].default_value = 0.45
    ob.data.materials.clear()
    ob.data.materials.append(m)


def export(ob, ao):
    pose(ao, 0, amp=0)
    # the feather coordinates are bake data only: Roblox would draw them as vertex colours (a rainbow tint)
    for ca in list(ob.data.color_attributes):
        ob.data.color_attributes.remove(ca)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    ao.select_set(True)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, f"{NAME}.fbx"), use_selection=True,
                             object_types={"MESH", "ARMATURE"}, apply_unit_scale=True, global_scale=1.0,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP",
                             embed_textures=False, add_leaf_bones=False, bake_anim=False, use_armature_deform_only=True,
                             colors_type="NONE")


# ------------------------------------------------------------------ previews

def stage(sc, night=True):
    w = bpy.data.worlds.new("Night")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    studio = "--studio" in argv
    bg.inputs["Color"].default_value = (0.35, 0.36, 0.40, 1) if studio else (0.006, 0.006, 0.012, 1)
    bg.inputs["Strength"].default_value = 1.0
    sc.world = w
    def light(name, kind, loc, rot, energy, color, size=1.0):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = color
        if kind == "AREA":
            ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = rot
        sc.collection.objects.link(lo)
        return lo
    light("Moon", "AREA", (3, 4, 6), (math.radians(-35), math.radians(30), math.radians(150)), 2600, (0.70, 0.78, 1.0), 4)
    light("Rim", "AREA", (-3, 3, 2), (math.radians(-70), 0, math.radians(-130)), 1600, (0.75, 0.82, 1.0), 3)
    light("Fill", "AREA", (0, -5, 1), (math.radians(80), 0, 0), 160, (1.0, 0.55, 0.45), 4)
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"


def camera(sc, loc, target, lens=50):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def render_flap(ob, ao, frames=12, res=640, samples=48):
    sc = bpy.context.scene
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 0.72)
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    camera(sc, (2.6, -3.4, 1.7), (0, -0.05, 0.05), lens=55)
    paths = []
    for i in range(frames):
        pose(ao, i / frames * 2 * math.pi)
        bpy.context.view_layer.update()
        p = os.path.join(OUT, "prev", f"flap_{i:02d}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


def render_stills(ob, ao, res=1100, samples=96):
    sc = bpy.context.scene
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 0.62)
    sc.cycles.samples = samples
    shots = [
        ("hero", (2.2, -2.6, 1.3), (0, -0.1, 0.05), 50, 0.7, 1.0),
        ("top", (0.01, -0.2, 4.2), (0, -0.2, 0), 45, 0.0, 0.0),
        ("head", (0.9, -1.5, 0.35), (0, -0.62, 0.08), 80, 2.2, 0.0),
    ]
    out = []
    for nm, loc, tgt, lens, ph, amp in shots:
        for o in [o for o in sc.objects if o.type == "CAMERA"]:
            bpy.data.objects.remove(o)
        camera(sc, loc, tgt, lens)
        pose(ao, ph, amp=amp)
        bpy.context.view_layer.update()
        p = os.path.join(OUT, "prev", f"still_{nm}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    return out


def main():
    sc = reset()
    ob = build()
    ao = rig(ob)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    dims = tuple(round(d, 3) for d in ob.dimensions)
    print(f"[crow] built: {tris} tris, {len(ob.data.vertices)} verts, dims {dims}")
    os.makedirs(os.path.join(OUT, "prev"), exist_ok=True)
    if "--nobake" in argv:
        flat_material(ob)
    else:
        bake_uv(ob)
        F, A = bake_maps(ob)
        base, N, R, E = paint(F, A)
        paths = {"color": save("color", base, srgb=True), "normal": save("normal", N), "rough": save("rough", R),
                 "emissive": save("emissive", E)}
        final_material(ob, paths)
        print("[crow] maps:", paths)
        export(ob, ao)
        print("[crow] fbx:", os.path.join(OUT, f"{NAME}.fbx"))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}.blend"))
    stage(sc)
    if "--preview" in argv:
        print("[crow] stills:", render_stills(ob, ao))
        print("[crow] flap:", render_flap(ob, ao))
    print("[crow] done")


if __name__ == "__main__":
    main()
