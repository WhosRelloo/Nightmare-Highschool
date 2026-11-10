"""Props batch 44 (the showpiece kit): sculpt-quality organic forms. Everything that is not the R6 body itself is smooth
and organic: metaball anatomy converted to meshes (wolves, ravens, bats, hair masses, mist), curved feather blades,
bowed membranes, with sculpted relief from a displacement along the normals.
"""
import math

import bpy
from mathutils import Euler, Matrix, Vector

import nh_props as P
from nh_props_batch3 import sphere
from nh_props_batch4 import _mark, _xform
from showpiece44_geo import sweep, grid_mesh, smooth_path, _resample, in_group


def blob(name, elems, mat, res=0.09, thresh=0.6, decimate=None, displace=None, smooth_iter=0):
    """A smooth organic mass from metaball elements, converted to a mesh: elems = [(centre, radius, scale xyz or None,
    rotation euler or None, stiffness)]. res is the polygon size (studs); decimate = target ratio; displace = (strength,
    noise size) adds a sculpted clump relief along the normals."""
    mb = bpy.data.metaballs.new(name + "MB")
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = thresh
    for e in elems:
        c, r = e[0], e[1]
        sc = e[2] if len(e) > 2 else None
        rot = e[3] if len(e) > 3 else None
        st = e[4] if len(e) > 4 else 2.0
        el = mb.elements.new()
        el.co = c
        el.radius = r * 1.6      # a lone element shows at about 0.57 of its field radius (threshold 0.6, stiffness 2)
        el.stiffness = st
        if sc:
            el.type = "ELLIPSOID"
            el.size_x, el.size_y, el.size_z = sc[0], sc[1], sc[2]
        if rot:
            el.rotation = Euler(rot).to_quaternion()
    ob = bpy.data.objects.new(name + "MB", mb)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    out = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(out)
    for p in me.polygons:
        p.use_smooth = True
    P._finish(out, mat, 0)
    if smooth_iter:
        md = out.modifiers.new("Smooth", "SMOOTH")
        md.iterations = smooth_iter
        md.factor = 0.5
    if displace:
        tex = bpy.data.textures.new(name + "Tex", "CLOUDS")
        tex.noise_scale = displace[1]
        tex.noise_depth = 2
        md = out.modifiers.new("Disp", "DISPLACE")
        md.texture = tex
        md.strength = displace[0]
        md.mid_level = 0.5
    if decimate:
        md = out.modifiers.new("Decimate", "DECIMATE")
        md.ratio = decimate
    return out


def chain(pts, r0, r1, step=None, scale=None, stiff=2.0, rfn=None):
    """Metaball elements along a smoothed polyline, radius r0 -> r1 (or rfn(t))."""
    pts = smooth_path(pts, 2)
    L = sum((b - a).length for a, b in zip(pts, pts[1:]))
    step = step or max(0.03, min(r0, r1 if r1 > 0 else r0) * 0.55)
    n = max(2, int(L / step))
    res = _resample(pts, n)
    out = []
    for i, p in enumerate(res):
        t = i / (n - 1)
        r = rfn(t) if rfn else r0 + (r1 - r0) * t
        out.append((tuple(p), r, scale, None, stiff))
    return out


def wolf(name, mat, M, howl=True, rear=0.0, s=1.0, res=0.11, decimate=0.45, eye=None, eye_mat=None, fur=0.06, tail_up=0.0):
    """A sculpted wolf (metaball anatomy: a deep chest, tucked waist and haunches, long jointed legs with paws, a ruff,
    a long muzzle with open jaws, pointed ears, a brush tail), built facing -Y, paws at z = 0, then placed by M.
    rear 0..1 rears it up on its hind legs (rotating the body about the hips); howl throws the head back."""
    st = _mark()
    tilt = -rear * 0.95
    hip = Vector((0, 1.5, 1.6))

    def Rr(p, body=True):
        p = Vector(p)
        if rear and body:
            q = p - hip
            c, sn = math.cos(tilt), math.sin(tilt)
            q = Vector((q.x, q.y * c - q.z * sn, q.y * sn + q.z * c))
            p = q + hip
        return tuple(p * s)
    E = []
    E.append((Rr((0, -0.9, 2.05)), 0.95 * s, (0.78, 1.05, 1.05), None, 2.0))     # chest
    E.append((Rr((0, 0.25, 2.15)), 0.72 * s, (0.7, 1.25, 0.8), None, 2.0))      # waist
    E.append((Rr((0, 1.35, 2.05)), 0.8 * s, (0.85, 1.0, 0.95), None, 2.0))      # haunch
    E.append((Rr((0, -1.55, 2.75)), 0.72 * s, (0.95, 0.85, 1.1), None, 2.0))    # neck
    if fur:
        for k in range(9):
            a = -1.3 + k * 0.325
            E.append((Rr((math.sin(a) * 0.62, -1.7 + abs(a) * 0.12, 2.5 + math.cos(a) * 0.4)), 0.3 * s, (1.0, 0.65, 1.25), None, 2.0))
    for sx in (-1, 1):
        if rear:
            fore = [(sx * 0.48, -1.0, 1.75), (sx * 0.55, -1.55, 1.25), (sx * 0.5, -1.95, 1.0), (sx * 0.48, -2.15, 0.95)]
            hind = [(sx * 0.52, 1.45, 1.6), (sx * 0.55, 0.85, 0.95), (sx * 0.5, 1.35, 0.35), (sx * 0.5, 1.1, 0.12)]
            E += [(Rr(p), r * s, None, None, 2.0) for p, r in zip(_resample(fore, 9), [0.34, 0.3, 0.27, 0.24, 0.21, 0.19, 0.19, 0.2, 0.21])]
            E += [(Rr(p, False), r * s, None, None, 2.0) for p, r in zip(_resample(hind, 9), [0.45, 0.4, 0.33, 0.27, 0.22, 0.19, 0.18, 0.2, 0.22])]
        else:
            fore = [(sx * 0.45, -1.0, 1.7), (sx * 0.42, -1.15, 0.95), (sx * 0.4, -1.1, 0.3), (sx * 0.4, -1.35, 0.12)]
            hind = [(sx * 0.5, 1.5, 1.7), (sx * 0.5, 1.95, 0.95), (sx * 0.45, 1.75, 0.35), (sx * 0.45, 1.55, 0.12)]
            E += [(Rr(p), r * s, None, None, 2.0) for p, r in zip(_resample(fore, 9), [0.34, 0.3, 0.27, 0.24, 0.21, 0.19, 0.19, 0.2, 0.21])]
            E += [(Rr(p), r * s, None, None, 2.0) for p, r in zip(_resample(hind, 9), [0.45, 0.4, 0.33, 0.27, 0.22, 0.19, 0.18, 0.2, 0.22])]
    # head: skull, muzzle and jaw along the head's own axes
    skull = Vector((0, -2.05, 3.25))
    up = Vector((0, -0.3, 0.95)) if howl else Vector((0, -1.0, 0.2))
    up.normalize()
    side = Vector((1, 0, 0))
    top = up.cross(side).normalized()
    if top.z < 0 and not howl:
        top = -top
    if howl and top.y > 0:
        top = -top
    E.append((Rr(skull), 0.56 * s, (0.95, 1.0, 0.92), None, 2.0))
    for k in range(6):
        t = k / 5
        E.append((Rr(skull + up * (0.35 + 0.8 * t) + top * (0.08 - 0.12 * t)), (0.36 - 0.17 * t) * s, None, None, 2.0))
    jaw = 0.5 if howl else 0.22
    jdir = (up * math.cos(jaw) - top * math.sin(jaw)).normalized()
    for k in range(5):
        t = k / 4
        E.append((Rr(skull - top * 0.22 + jdir * (0.3 + 0.7 * t)), (0.22 - 0.1 * t) * s, None, None, 2.0))
    tail = [(0, 2.15, 2.15), (0, 2.85, 2.3 + tail_up), (0.15, 3.45, 2.0 + tail_up * 1.5), (0.35, 3.85, 1.4 + tail_up * 2)]
    E += [(Rr(p), r * s, (1.0, 1.0, 1.0), None, 2.0) for p, r in zip(_resample(tail, 10), [0.24, 0.3, 0.35, 0.38, 0.38, 0.36, 0.32, 0.26, 0.18, 0.1])]
    blob(name, E, mat, res=res * s, decimate=decimate, displace=(fur * s, 0.22 * s) if fur else None)
    for sx in (-1, 1):
        base = skull + top * 0.42 + side * sx * 0.3 - up * 0.08
        tip = base + top * 0.62 + side * sx * 0.14 - up * 0.2
        sweep(f"{name}Ear{sx}", [Rr(base), Rr(base.lerp(tip, 0.5)), Rr(tip)], lambda t: 0.21 * s * (1 - t) ** 0.8 + 0.01, mat, sides=7, flat=0.45,
              smooth=1)
    for k in range(3):     # fangs
        for sx in (-1, 1):
            p = skull + up * (0.95 - k * 0.15) - top * 0.08 + side * sx * 0.12
            sweep(f"{name}Fang{sx}{k}", [Rr(p), Rr(p - top * 0.16)], lambda t: 0.035 * s * (1 - t) + 0.003, eye_mat if eye_mat and k < 0 else mat,
                  sides=5, smooth=0)
    if eye:
        def ey():
            for sx in (-1, 1):
                p = skull + up * 0.3 + top * 0.25 + side * sx * 0.3
                sphere(f"{name}Eye{sx}", 0.075 * s, Rr(p), eye_mat or mat, seg=8, rings=4, scale=(1.0, 1.0, 0.55))
        in_group(eye, ey)
    _xform(st, M)


def feather(name, root, direction, length, width, mat, curl=0.15, side=(0, 0, 1), n=7, thick=0.012):
    """A curved feather blade: a vane with a raised midrib, tapering to a rounded tip, curling by `curl`."""
    root = Vector(root)
    d = Vector(direction).normalized()
    sd = Vector(side)
    sd = (sd - d * sd.dot(d))
    sd = sd.normalized() if sd.length > 1e-6 else d.orthogonal().normalized()
    nrm = d.cross(sd)
    rows = []
    for i in range(n + 1):
        t = i / n
        c = root + d * length * t + nrm * curl * length * t * t
        w = width * math.sin(min(1.0, t * 1.1 + 0.08) * math.pi) ** 0.6 * (1 - 0.25 * t)
        rows.append([c - sd * w * 0.42 - nrm * 0.004, c + nrm * 0.015, c + sd * w * 0.58 - nrm * 0.004])
    return grid_mesh(name, rows, mat, thick)


def raven(name, K, at, heading=0.0, wings=0.7, s=1.0, mat="feather", eye=None, beak="iron", perch=False, decimate=0.3, bank=0.0):
    """A sculpted raven: a smooth body and head with a shaggy throat, a heavy curved beak, broad sculpted wings (a
    flattened mass along the arm) ending in the raven's five splayed primaries, and a wedge tail. Spread in flight by
    `wings` 0..1, folded when perched. Faces +X; placed at `at`, heading about Z, banked about X."""
    st = _mark()
    m = K[mat]
    E = [((0, 0, 0), 0.3 * s, (1.4, 0.72, 0.78), None, 2.0), ((0.3 * s, 0, 0.1 * s), 0.21 * s, (1.0, 0.8, 0.9), None, 2.0),
         ((0.46 * s, 0, 0.17 * s), 0.17 * s, None, None, 2.0), ((0.38 * s, 0, 0.0), 0.14 * s, (1.0, 0.8, 1.1), None, 2.0),
         ((-0.36 * s, 0, -0.02 * s), 0.17 * s, (1.3, 0.6, 0.45), None, 2.0)]
    for sy in (-1, 1):
        if perch:
            E += [((0.05 * s - k * 0.12 * s, sy * 0.2 * s, 0.05 * s - k * 0.02 * s), 0.16 * s, (1.6, 0.4, 0.8), None, 2.0) for k in range(5)]
        else:
            sh = Vector((0.05 * s, sy * 0.15 * s, 0.08 * s))
            wr = sh + Vector((-0.1 * s, sy * 0.7 * s, wings * 0.45 * s))
            tip = wr + Vector((-0.25 * s, sy * 0.55 * s, wings * 0.25 * s - 0.1 * s))
            for k in range(9):
                t = k / 8
                p = sh.lerp(wr, t * 2) if t < 0.5 else wr.lerp(tip, (t - 0.5) * 2)
                E.append((tuple(p + Vector((-0.12 * s * (1 - t), 0, 0))), (0.2 - 0.1 * t) * s, (1.7 - 0.6 * t, 0.9, 0.3), None, 2.0))
    blob(f"{name}Body", E, m, res=0.065 * s, decimate=decimate, displace=(0.012 * s, 0.05 * s))
    sweep(f"{name}Beak", [(0.56 * s, 0, 0.17 * s), (0.72 * s, 0, 0.15 * s), (0.84 * s, 0, 0.08 * s)], lambda t: 0.07 * s * (1 - t) + 0.004, K[beak],
          sides=6, flat=0.7, smooth=1)
    if eye:
        in_group(eye, lambda: [sphere(f"{name}Eye{sy}", 0.03 * s, (0.56 * s, sy * 0.1 * s, 0.23 * s), K["glowmat"], seg=6, rings=3)
                               for sy in (-1, 1)])
    if not perch:
        for sy in (-1, 1):
            sh = Vector((0.05 * s, sy * 0.15 * s, 0.08 * s))
            wr = sh + Vector((-0.1 * s, sy * 0.7 * s, wings * 0.45 * s))
            tip = wr + Vector((-0.25 * s, sy * 0.55 * s, wings * 0.25 * s - 0.1 * s))
            for k in range(5):
                d = (tip - wr).normalized() + Vector((-0.25 * k, 0, -0.05 * k))
                feather(f"{name}P{sy}{k}", tip - (tip - wr) * 0.15 * k, d, (0.55 - 0.05 * k) * s, 0.11 * s, m, curl=-0.1, side=(1, 0, 0), n=5,
                        thick=0.01 * s)
    for k in range(5):
        a = math.radians(-20 + 10 * k)
        feather(f"{name}T{k}", (-0.42 * s, 0, 0), (-math.cos(a), math.sin(a), -0.08), 0.55 * s, 0.14 * s, m, curl=0.05, side=(0, 0, 1), n=5,
                thick=0.01 * s)
    _xform(st, Matrix.Translation(at) @ Matrix.Rotation(heading, 4, "Z") @ Matrix.Rotation(bank, 4, "X"))


def bat(name, K, at, heading=0.0, flap=0.5, s=1.0, body="fur_black", skin="leather_black"):
    """A sculpted bat: a furred body and head with tall ears, finger bones fanning from each wrist and a scalloped
    membrane bowed between them. Faces +X."""
    st = _mark()
    E = [((0, 0, 0), 0.16 * s, (1.4, 0.85, 0.9), None, 2.0), ((0.2 * s, 0, 0.03 * s), 0.11 * s, None, None, 2.0)]
    blob(f"{name}Body", E, K[body], res=0.025 * s, decimate=0.6)
    for sy in (-1, 1):
        sweep(f"{name}Ear{sy}", [(0.22 * s, sy * 0.05 * s, 0.1 * s), (0.25 * s, sy * 0.08 * s, 0.24 * s)], lambda t: 0.045 * s * (1 - t) + 0.003,
              K[skin], sides=5, flat=0.5, smooth=0)
        sh = Vector((0.05 * s, sy * 0.1 * s, 0.05 * s))
        wrist = sh + Vector((0.12 * s, sy * 0.42 * s, flap * 0.4 * s))
        tips = [wrist + Vector((x * s, sy * y * s, z * s * flap - (1 - flap) * 0.05 * s)) for x, y, z in
                ((0.28, 0.45, 0.25), (0.06, 0.62, 0.1), (-0.2, 0.52, -0.05), (-0.36, 0.3, -0.15))]
        sweep(f"{name}Arm{sy}", [sh, sh.lerp(wrist, 0.5) + Vector((0, 0, 0.05 * s)), wrist], 0.02 * s, K[skin], sides=5, smooth=1)
        for k, t in enumerate(tips):
            sweep(f"{name}Fin{sy}{k}", [wrist, wrist.lerp(t, 0.5) + Vector((0, 0, 0.03 * s)), t], lambda u: 0.014 * s * (1 - 0.6 * u), K[skin],
                  sides=4, smooth=1)
        anchors = [sh + Vector((-0.28 * s, 0, -0.05 * s))] + tips[::-1] + [wrist + Vector((0.12 * s, sy * 0.1 * s, 0.05 * s))]
        fine = []
        for a, b in zip(anchors, anchors[1:]):     # scallops between the fingers
            fine += [a, a.lerp(b, 0.5).lerp(wrist, 0.22)]
        fine.append(anchors[-1])
        rows = []
        for i in range(7):
            u = i / 6
            rows.append([sh.lerp(a, u) + Vector((0, 0, -0.05 * s * math.sin(u * math.pi))) for a in fine])
        grid_mesh(f"{name}Mem{sy}", rows, K[skin], 0.008 * s)
    _xform(st, Matrix.Translation(at) @ Matrix.Rotation(heading, 4, "Z"))


def hair_mass(name, mat, locks, res=0.045, decimate=0.5, cap=None):
    """Sculpted hair: a cap and flowing locks as one smooth metaball mass (locks = [(points, r0, r1)]), so it reads as
    carved, clumped hair rather than tubes. Points in the figure's rest frame (built inside Fig.build)."""
    E = []
    if cap:
        c, r, sc = cap
        E.append((c, r, sc, None, 2.0))
    for pts, r0, r1 in locks:
        E += chain(pts, r0, r1, scale=None, stiff=1.6)
    return blob(name, E, mat, res=res, decimate=decimate, displace=(0.012, 0.04))


def mist(name, mat, center, n, spread, size, seed=0, rise=0.6, res=0.12, decimate=0.5):
    """Billowing mist or ectoplasm as one smooth fused mass (a _Glass piece in Roblox)."""
    import random
    rnd = random.Random(seed)
    c = Vector(center)
    E = []
    for i in range(n):
        a = rnd.uniform(0, 6.28)
        d = spread * math.sqrt(rnd.random())
        p = c + Vector((math.cos(a) * d, math.sin(a) * d, rnd.random() * size * rise * 3))
        r = size * rnd.uniform(0.6, 1.2) * (1.15 - 0.5 * d / max(spread, 1e-6))
        E.append((tuple(p), r, (rnd.uniform(1.0, 1.5), rnd.uniform(1.0, 1.4), rnd.uniform(0.7, 1.0)), None, 2.0))
    return blob(name, E, mat, res=res, decimate=decimate, smooth_iter=2)


def plume(name, mat, center, radius, height, seed=0, tendrils=6, billows=14, res=0.12):
    """Rising mist or smoke for a _Glass piece: low rolling billows round the base, and curling tendrils that climb and
    thin out, all fused into one smooth mass."""
    import random
    rnd = random.Random(seed)
    c = Vector(center)
    E = []
    for i in range(billows):
        a = 2 * math.pi * i / billows + rnd.uniform(-0.2, 0.2)
        d = radius * rnd.uniform(0.55, 1.0)
        p = c + Vector((math.cos(a) * d, math.sin(a) * d, rnd.uniform(0.0, 0.25) * radius))
        r = radius * rnd.uniform(0.28, 0.42)
        E.append((tuple(p), r, (1.3, 1.3, 0.75), None, 2.0))
    for k in range(tendrils):
        a0 = 2 * math.pi * k / tendrils + rnd.uniform(-0.3, 0.3)
        turns = rnd.uniform(0.4, 0.9) * rnd.choice((-1, 1))
        h = height * rnd.uniform(0.6, 1.0)
        pts = []
        for i in range(9):
            t = i / 8
            a = a0 + turns * 2 * math.pi * t
            rr = radius * (0.85 - 0.45 * t) + 0.2 * math.sin(t * 6 + k)
            pts.append(c + Vector((math.cos(a) * rr, math.sin(a) * rr, h * t)))
        E += chain(pts, radius * 0.26, radius * 0.06, stiff=1.8)
    return blob(name, E, mat, res=res, decimate=0.45, smooth_iter=2)
