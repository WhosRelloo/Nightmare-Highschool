"""The owner's teleport bat (Blender 5.x, headless). Shares nh_crow.py's helpers (scene, bake, save, stage).

  "E:/Blender/blender.exe" --background --factory-startup --python art/vfx/crow/nh_bat.py -- [--size 2048] [--gpu]
        [--nobake] [--preview] [--studio] [--out E:/NH-Work/crow]

An original gothic night bat, one skinned mesh, one material, studs, facing -Y, wings spread (the rest pose):
  body + head + snout   one loft; a ruff of fur painted on
  ears                  two tall cupped ears
  wings                 membrane panels between four long fingers, the trailing edge scalloped between the tips
                        (the classic bat outline), and the big arm membrane down to the ankle
  tail membrane         between the ankles and the tail
  eyes                  crimson, emissive; two small ivory fangs
Membranes are single surfaces: the Roblox MeshPart is DoubleSided.

The rig (9 bones): Root > Body > Head, Body > Wing{L,R}1 (arm) > Wing{L,R}2 (forearm) > Wing{L,R}3 (hand).
Each vertex's weights are written as it is made (the membrane between the arm and the hand blends across).
"""
import math
import os
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_crow as C  # noqa: E402

NAME = "NHBat"
C.NAME = NAME
PART_FUR, PART_MEM, PART_EAR, PART_EYE, PART_FANG = 0, 1, 2, 3, 4
VW = {}            # BMVert -> {bone: weight}


def V(p, w):
    v = C.BM.verts.new(p)
    VW[v] = w
    return v


def lerp(a, b, t):
    return a + (b - a) * t


def blendw(a, b, t):
    out = {}
    for k, x in a.items():
        out[k] = out.get(k, 0) + x * (1 - t)
    for k, x in b.items():
        out[k] = out.get(k, 0) + x * t
    return out


# (y, z, half width, half height): tail stub to nose
PROFILE = [
    (0.30, 0.000, 0.018, 0.018),
    (0.21, 0.000, 0.065, 0.055),
    (0.07, 0.010, 0.110, 0.090),
    (-0.06, 0.020, 0.120, 0.100),
    (-0.15, 0.040, 0.090, 0.085),
    (-0.215, 0.052, 0.098, 0.092),
    (-0.275, 0.046, 0.068, 0.062),
    (-0.315, 0.036, 0.036, 0.036),
    (-0.335, 0.030, 0.010, 0.012),
]


def body(rings=20, around=12):
    secs = []
    for i in range(rings + 1):
        t = i / rings
        y, z, w, h = C.catmull(PROFILE, t)
        hw = C.smooth(0.62, 0.78, t)
        wt = {"Head": hw, "Body": 1 - hw}
        ring = []
        for j in range(around):
            a = j / around * 2 * math.pi
            s, c = math.sin(a), math.cos(a)
            ring.append(V((w * s, y, z + h * c), wt))
        secs.append((t, ring))
    cd = C.code(PART_FUR)
    for i in range(rings):
        t0, r0 = secs[i]
        t1, r1 = secs[i + 1]
        for j in range(around):
            j2 = (j + 1) % around
            a0, a1 = j / around, (j + 1) / around
            C.face([r0[j], r0[j2], r1[j2], r1[j]], [(a0, t0, cd), (a1, t0, cd), (a1, t1, cd), (a0, t1, cd)])
    for (t, ring), flip in ((secs[0], True), (secs[-1], False)):
        cc = V(sum((v.co for v in ring), Vector()) / len(ring), VW[ring[0]])
        for j in range(around):
            j2 = (j + 1) % around
            vs = [ring[j], ring[j2], cc] if not flip else [ring[j2], ring[j], cc]
            C.face(vs, [(0.5, t, cd)] * 3)


def ear(sx):
    """A tall cupped ear: a strip curling round its long axis, the tip leaning out and back."""
    base = Vector((sx * 0.052, -0.205, 0.118))
    tip = Vector((sx * 0.105, -0.165, 0.335))
    up = (tip - base).normalized()
    side = Vector((sx * 1, -0.35, 0)).normalized()
    side = (side - up * side.dot(up)).normalized()
    fwd = up.cross(side).normalized()
    if fwd.y > 0:
        fwd = -fwd
    rows = []
    n, m = 5, 4
    for i in range(n + 1):
        t = i / n
        width = 0.060 * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7 * (1 - 0.85 * t ** 3)
        p = base + (tip - base) * t
        row = []
        for k in range(m + 1):
            b = k / m * 2 - 1
            cup = 0.028 * (1 - b * b) * (1 - t)        # the hollow faces forward
            q = p + side * (b * width) - fwd * cup * -1 + fwd * (0.012 * b * b)
            row.append((V(q, {"Head": 1.0}), (b + 1) / 2, t))
        rows.append(row)
    cd = C.code(PART_EAR)
    for i in range(n):
        for k in range(m):
            q = [rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]]
            if sx < 0:
                q = q[::-1]
            C.face([a for a, _, _ in q], [(u, v, cd) for _, u, v in q])


def eye(sx):
    c = Vector((sx * 0.056, -0.272, 0.080))
    r = 0.017
    axis = Vector((sx * 0.8, -1.0, 0.2)).normalized()
    rot = Vector((0, 0, 1)).rotation_difference(axis).to_matrix()
    seg, rings = 8, 5
    grid = []
    for i in range(rings + 1):
        th = i / rings * math.pi
        row = []
        for j in range(seg):
            ph = j / seg * 2 * math.pi
            p = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))) * r
            row.append((V(c + rot @ p, {"Head": 1.0}), th / math.pi))
        grid.append(row)
    cd = C.code(PART_EYE)
    for i in range(rings):
        for j in range(seg):
            j2 = (j + 1) % seg
            q = [grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]]
            vs = [v for v, _ in q]
            if len(set(vs)) < 4:
                continue
            C.face(vs, [(k, 0.0, cd) for _, k in q])


def cone(base, tip, r, wt, cd, n=5):
    base, tip = Vector(base), Vector(tip)
    d = (tip - base).normalized()
    a = d.orthogonal().normalized()
    b = d.cross(a)
    ring = [V(base + (a * math.cos(k / n * 2 * math.pi) + b * math.sin(k / n * 2 * math.pi)) * r, wt) for k in range(n)]
    tv = V(tip, wt)
    for k in range(n):
        C.face([ring[k], ring[(k + 1) % n], tv], [(0, 0, cd), (1, 0, cd), (0.5, 1, cd)])


# the arm and finger joints of the right wing (x mirrored for the left)
SHOULDER = Vector((0.085, -0.07, 0.055))
ELBOW = Vector((0.40, 0.03, 0.075))
WRIST = Vector((0.70, -0.11, 0.080))
TIPS = [Vector((1.06, -0.13, 0.060)),      # finger 2: along the leading edge
        Vector((1.12, 0.12, 0.050)),
        Vector((0.95, 0.50, 0.045)),
        Vector((0.58, 0.60, 0.045))]       # finger 5
ANKLE = Vector((0.13, 0.32, 0.020))
SAG = [0.0, 0.11, 0.13, 0.12]              # how deep the trailing edge scallops between tip k-1 and k


def mir(p, sx):
    return Vector((p.x * sx, p.y, p.z))


def wing(sx):
    side = "R" if sx > 0 else "L"
    W1, W2, W3 = {f"Wing{side}1": 1.0}, {f"Wing{side}2": 1.0}, {f"Wing{side}3": 1.0}
    cd_m = lambda k: C.code(PART_MEM, k)   # noqa: E731

    def emit(grid, k):
        nA, nB = len(grid) - 1, len(grid[0]) - 1
        for i in range(nA):
            for j in range(nB):
                q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                if sx < 0:
                    q = q[::-1]
                vs = [a for a, _, _ in q]
                if len(set(vs)) < 3:
                    continue
                if len(set(vs)) == 3:
                    seen, vv, cc = set(), [], []
                    for a, u, v in q:
                        if a not in seen:
                            seen.add(a)
                            vv.append(a)
                            cc.append((u, v, cd_m(k)))
                    C.face(vv, cc)
                    continue
                C.face(vs, [(u, v, cd_m(k)) for _, u, v in q])

    # finger panels: radial grids from the wrist to the scalloped trailing edge between two tips
    wv = V(mir(WRIST, sx), blendw(W2, W3, 0.5))
    na, nb = 4, 3
    for k in range(1, 4):
        A, B = TIPS[k - 1], TIPS[k]
        grid = []
        for i in range(na + 1):
            a = i / na
            row = []
            for j in range(nb + 1):
                b = j / nb
                edge = lerp(A, B, b)
                mid = (A + B) / 2
                pull = (WRIST - mid).normalized() * (SAG[k] * math.sin(math.pi * b))
                e = edge + pull
                p = lerp(WRIST, e, a)
                p.z -= 0.025 * math.sin(math.pi * b) * math.sin(math.pi * a)   # the membrane billows
                if i == 0:
                    row.append((wv, b, 0.0))
                else:
                    row.append((V(mir(p, sx), blendw(W2, W3, min(1, 0.5 + a))), b, a))
            grid.append(row)
        emit(grid, k)
    # the arm membrane (plagiopatagium): from the body side out to finger 5, the arm along its leading edge
    ns, nt = 6, 4
    grid = []
    for i in range(ns + 1):
        s = i / ns
        # leading edge: shoulder -> elbow -> wrist
        if s < 0.5:
            L = lerp(SHOULDER, ELBOW, s / 0.5)
            lw = blendw(blendw({"Body": 1.0}, W1, min(1, s / 0.12)), W2, C.smooth(0.35, 0.5, s))
        else:
            L = lerp(ELBOW, WRIST, (s - 0.5) / 0.5)
            lw = blendw(W1, W2, C.smooth(0.45, 0.62, s))
            if s > 0.95:
                lw = blendw(W2, W3, 0.5)
        T = lerp(ANKLE, TIPS[3], s)
        T = T + (Vector((0, -1, 0)) * (SAG[1] * 1.1 * math.sin(math.pi * s)))
        tw = blendw({"Body": 1.0}, blendw(W2, W3, s), C.smooth(0.0, 0.7, s))
        row = []
        for j in range(nt + 1):
            t = j / nt
            p = lerp(L, T, t)
            p.z -= 0.03 * math.sin(math.pi * t) * math.sin(math.pi * s)
            w = blendw(lw, tw, t)
            if s == 1 and j == 0:
                row.append((wv, s, t))
            else:
                row.append((V(mir(p, sx), w), s, t))
        grid.append(row)
    emit(grid, 0)
    # the leading-edge membrane in front of the arm (propatagium): a thin strip shoulder -> wrist
    grid = []
    for i in range(5):
        s = i / 4
        L = lerp(SHOULDER, ELBOW, s / 0.5) if s < 0.5 else lerp(ELBOW, WRIST, (s - 0.5) / 0.5)
        lw = blendw({"Body": 1.0}, W1, min(1, s / 0.15)) if s < 0.5 else blendw(W1, W2, C.smooth(0.5, 0.7, s))
        F = Vector((L.x, -0.15 - 0.02 * math.sin(math.pi * s), L.z + 0.005))
        F = lerp(L, F, 0.55 if 0 < s < 1 else 0.0)
        row = [(V(mir(F, sx), lw), s, 0.0), (V(mir(L + Vector((0, 0, 0.004)), sx), lw), s, 1.0)]
        grid.append(row)
    emit(grid, 4)
    # a small claw on the thumb, at the wrist
    cone(mir(WRIST + Vector((0, -0.01, 0.01)), sx), mir(WRIST + Vector((0.01, -0.08, 0.025)), sx), 0.012,
         blendw(W2, W3, 0.5), C.code(PART_FANG, 1))
    # the feet, at the ankle
    cone(mir(ANKLE, sx), mir(ANKLE + Vector((0.01, 0.07, -0.02)), sx), 0.014, {"Body": 1.0}, C.code(PART_FANG, 1))


def tail_membrane():
    """Between the ankles and the tail tip, its trailing edge curving in."""
    tip = Vector((0, 0.40, 0.0))
    grid = []
    for i in range(4):
        a = i / 3
        row = []
        for j in range(5):
            b = j / 4 * 2 - 1
            inner = Vector((b * 0.10, 0.19, 0.012))
            outer = lerp(tip, mir(ANKLE, 1 if b >= 0 else -1), abs(b)) + Vector((0, -0.05 * (1 - b * b) * abs(b) * 2, 0))
            row.append((V(lerp(inner, outer, a), {"Body": 1.0}), (b + 1) / 2, a))
        grid.append(row)
    cd = C.code(PART_MEM, 5)
    for i in range(3):
        for j in range(4):
            q = [grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]
            C.face([a for a, _, _ in q], [(u, v, cd) for _, u, v in q])


def build():
    C.BM = bmesh.new()
    C.FUV.clear()
    VW.clear()
    body()
    for sx in (1, -1):
        ear(sx)
        eye(sx)
        wing(sx)
        cone((sx * 0.018, -0.305, 0.012), (sx * 0.016, -0.312, -0.025), 0.007, {"Head": 1.0}, C.code(PART_FANG))
    tail_membrane()
    C.BM.verts.index_update()
    weights = {v.index: w for v, w in VW.items()}
    me = bpy.data.meshes.new(NAME)
    C.BM.to_mesh(me)
    attr = me.color_attributes.new("fuv", "FLOAT_COLOR", "CORNER")
    C.BM.faces.index_update()
    idx = {f.index: c for f, c in C.FUV}
    data = np.zeros((len(me.loops), 4), dtype=np.float32)
    for p in me.polygons:
        cs = idx[p.index]
        us = [c[0] for c in cs]
        if cs[0][2] < 0.1 and max(us) - min(us) > 0.5:
            us = [u + 1 if u < 0.5 else u for u in us]
        for k, li in enumerate(p.loop_indices):
            data[li] = (us[k], cs[k][1], cs[k][2], 1.0)
    attr.data.foreach_set("color", data.ravel())
    C.BM.free()
    ob = bpy.data.objects.new(NAME, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob, weights


BONES = {
    "Root": ((0, 0.05, 0), (0, -0.10, 0), None),
    "Body": ((0, 0.20, 0.0), (0, -0.12, 0.03), "Root"),
    "Head": ((0, -0.15, 0.045), (0, -0.34, 0.03), "Body"),
}
for _s, _n in ((1, "R"), (-1, "L")):
    BONES[f"Wing{_n}1"] = (tuple(mir(SHOULDER, _s)), tuple(mir(ELBOW, _s)), "Body")
    BONES[f"Wing{_n}2"] = (tuple(mir(ELBOW, _s)), tuple(mir(WRIST, _s)), f"Wing{_n}1")
    BONES[f"Wing{_n}3"] = (tuple(mir(WRIST, _s)), tuple(mir(TIPS[1], _s)), f"Wing{_n}2")


def rig(ob, weights):
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
    bpy.ops.object.mode_set(mode="OBJECT")
    groups = {n: ob.vertex_groups.new(name=n) for n in BONES}
    for vi, w in weights.items():
        tot = sum(w.values()) or 1
        for n, val in w.items():
            if val / tot > 0.002:
                groups[n].add([vi], val / tot, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = ao
    ob.parent = ao
    return ao


def pose(ao, phase, amp=1.0, glide=0.0):
    """A bat's beat: a deep stroke, and the hand folds back and in on the upstroke (the membrane goes slack)."""
    from mathutils import Matrix
    pb = ao.pose.bones
    for b in pb:
        b.rotation_mode = "QUATERNION"
        b.rotation_quaternion = (1, 0, 0, 0)
    up = max(0.0, math.sin(phase))          # 1 at the top of the stroke
    for s, side in ((1, "R"), (-1, "L")):
        a1 = math.radians(55) * math.sin(phase) * amp
        a2 = math.radians(18) * math.sin(phase - 0.5) * amp
        a3 = math.radians(28) * math.sin(phase - 1.0) * amp
        fold = math.radians(38) * up * amp      # the hand sweeps back about the vertical
        for bn, a in ((f"Wing{side}1", a1), (f"Wing{side}2", a2), (f"Wing{side}3", a3)):
            b = pb[bn]
            rest = b.bone.matrix_local.to_3x3()
            q = Matrix.Rotation(-s * a, 3, rest.inverted() @ Vector((0, 1, 0)))
            if bn.endswith("2"):
                q = Matrix.Rotation(-s * fold * 0.5, 3, rest.inverted() @ Vector((0, 0, 1))) @ q
            if bn.endswith("3"):
                q = Matrix.Rotation(-s * fold, 3, rest.inverted() @ Vector((0, 0, 1))) @ q
            b.rotation_quaternion = q.to_quaternion()
    pb["Body"].rotation_mode = "XYZ"
    pb["Body"].rotation_euler = (0.06 * math.sin(phase + 1.5) * amp, 0, 0)
    pb["Head"].rotation_mode = "XYZ"
    pb["Head"].rotation_euler = (-0.06 * math.sin(phase + 1.5) * amp, 0, 0)


def paint(F, A):
    u, v, c = F[:, :, 0], F[:, :, 1], F[:, :, 2]
    cover = c > 0.02
    part = np.clip(np.floor((c - 0.05) / 0.1 + 0.5), 0, 4).astype(np.int32)
    idx = np.round((c - 0.05 - part * 0.1) / 0.004)
    H = np.zeros_like(u)
    rough = np.full_like(u, 0.6)
    emis = np.zeros_like(u)
    base = np.zeros(u.shape + (3,), dtype=np.float32)
    rng = np.random.default_rng(7)
    noise = rng.random((64, 64)).astype(np.float32)

    def vnoise(x, y):
        xi, yi = np.floor(x).astype(np.int64) % 64, np.floor(y).astype(np.int64) % 64
        fx, fy = x - np.floor(x), y - np.floor(y)
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a, b = noise[yi, xi], noise[yi, (xi + 1) % 64]
        cc, d = noise[(yi + 1) % 64, xi], noise[(yi + 1) % 64, (xi + 1) % 64]
        return lerp(lerp(a, b, fx), lerp(cc, d, fx), fy)

    FUR = np.array([0.010, 0.0075, 0.0080])
    FUR_TIP = np.array([0.030, 0.016, 0.016])
    MEM = np.array([0.0090, 0.0055, 0.0075])
    MEM_EDGE = np.array([0.045, 0.006, 0.014])
    # fur: long strands running back along the body, clumped
    m = cover & (part == PART_FUR)
    strand = vnoise(u * 160, v * 18) * 0.6 + vnoise(u * 420, v * 40) * 0.4
    clump = vnoise(u * 30, v * 10)
    fur_h = np.clip(strand * 0.8 + clump * 0.4, 0, 1)
    H = np.where(m, fur_h, H)
    rough = np.where(m, 0.75 - 0.2 * fur_h, rough)
    tipmix = np.clip((fur_h - 0.55) * 2.2, 0, 1)
    face = m & (v > 0.86)                     # the bare snout
    for ch in range(3):
        b = FUR[ch] + (FUR_TIP[ch] - FUR[ch]) * tipmix
        b = np.where(face, 0.018 if ch == 0 else 0.012, b)
        base[:, :, ch] = np.where(m, b, base[:, :, ch])
    rough = np.where(face, 0.4, rough)
    # membranes: leathery, wrinkled across the fingers, a raised bone along each finger, a crimson cast at the edge
    m = cover & (part == PART_MEM)
    wr = np.sin((v * 46 + vnoise(u * 12, v * 12) * 3.0) * math.pi) * 0.5 + 0.5
    fine = vnoise(u * 300, v * 300)
    bone = np.exp(-(u / 0.05) ** 2) + np.exp(-((1 - u) / 0.05) ** 2)
    bone = np.where((idx >= 1) & (idx <= 3), bone, np.exp(-((1 - v) / 0.06) ** 2) * (idx == 4))
    edge = np.clip((v - 0.80) / 0.2, 0, 1) * np.where((idx >= 1) & (idx <= 3), 1.0, 0.6)
    mh = 0.25 * wr + 0.15 * fine + 0.6 * np.clip(bone, 0, 1)
    H = np.where(m, mh, H)
    rough = np.where(m, 0.55 - 0.15 * np.clip(bone, 0, 1), rough)
    for ch in range(3):
        b = MEM[ch] * (0.8 + 0.4 * wr) + (MEM_EDGE[ch] - MEM[ch]) * edge ** 2 + 0.012 * np.clip(bone, 0, 1)
        base[:, :, ch] = np.where(m, b, base[:, :, ch])
    # ears: thin and ridged inside, crimson toward the rim
    m = cover & (part == PART_EAR)
    ridge = np.sin(v * 9 * math.pi) * 0.5 + 0.5
    rim = np.clip((np.abs(u - 0.5) * 2 - 0.7) / 0.3, 0, 1)
    H = np.where(m, 0.3 * ridge + 0.4 * rim, H)
    for ch in range(3):
        b = MEM[ch] * (0.9 + 0.3 * ridge) + (MEM_EDGE[ch] - MEM[ch]) * rim * 0.8
        base[:, :, ch] = np.where(m, b, base[:, :, ch])
    # eyes: crimson all over, a dark slit pupil; the whole ball glows faintly (the emissive mask)
    m = cover & (part == PART_EYE)
    k = u
    pupil = k < 0.08
    for ch, val in enumerate((0.42, 0.03, 0.05)):
        base[:, :, ch] = np.where(m, np.where(pupil, 0.002, val * (1.1 - k)), base[:, :, ch])
    emis = np.where(m & ~pupil, np.clip(1.15 - k * 1.2, 0, 1), emis)
    rough = np.where(m, 0.05, rough)
    H = np.where(m, 0.5, H)
    # fangs ivory, claws dark horn
    m = cover & (part == PART_FANG)
    for ch, (fv, cv) in enumerate(((0.55, 0.02), (0.50, 0.016), (0.42, 0.014))):
        base[:, :, ch] = np.where(m, np.where(idx >= 1, cv, fv), base[:, :, ch])
    rough = np.where(m, 0.3, rough)
    H = np.where(m, 0.5, H)

    ao = 0.45 + 0.55 * np.clip(A, 0, 1)
    base *= ao[:, :, None]
    gx = np.zeros_like(H)
    gy = np.zeros_like(H)
    gx[:, 1:-1] = (H[:, 2:] - H[:, :-2]) * 0.5
    gy[1:-1, :] = (H[2:, :] - H[:-2, :]) * 0.5
    gx, gy = np.clip(gx, -0.25, 0.25), np.clip(gy, -0.25, 0.25)
    st = 3.0 * C.SIZE / 2048
    nx, ny, nz = -gx * st, -gy * st, np.ones_like(gx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    N = np.stack([nx / ln, ny / ln, nz / ln], axis=2) * 0.5 + 0.5
    N[~cover] = (0.5, 0.5, 1.0)
    return base, N, np.clip(rough, 0.04, 0.9), emis


def main():
    sc = C.reset()
    ob, weights = build()
    ao = rig(ob, weights)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(f"[bat] built: {tris} tris, {len(ob.data.vertices)} verts, dims {tuple(round(d, 3) for d in ob.dimensions)}")
    os.makedirs(os.path.join(C.OUT, "prev"), exist_ok=True)
    C.pose = pose
    if "--nobake" in C.argv:
        C.flat_material(ob)
    else:
        C.bake_uv(ob)
        F, A = C.bake_maps(ob)
        base, N, R, E = paint(F, A)
        paths = {"color": C.save("color", base, srgb=True), "normal": C.save("normal", N), "rough": C.save("rough", R),
                 "emissive": C.save("emissive", E)}
        C.final_material(ob, paths)
        print("[bat] maps:", paths)
        C.export(ob, ao)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, f"{NAME}.blend"))
    C.stage(sc)
    if "--preview" in C.argv:
        import shutil
        st = C.render_stills(ob, ao)
        fl = C.render_flap(ob, ao)
        for p in st + fl:
            d = os.path.join(os.path.dirname(p), "bat_" + os.path.basename(p))
            shutil.move(p, d)
    print("[bat] done")


if __name__ == "__main__":
    main()
