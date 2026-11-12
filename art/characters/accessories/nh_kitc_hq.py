"""Kit C concept pieces at the shipping standard (owner: "Make the boots look wayyy cooler and better. Wayy higher
quality. Same with any masks"): the kintsugi porcelain mask, the beaked night-watch mask and the buckled knee boots.
Imported by nh_kitc_concepts.py."""
import math
import bpy, bmesh
from mathutils import Vector
import nh_acc as A
from nh_acc import item, piece, smooth, lerp
from nh_acc_batch1 import ccw, frame, offset_poly, buckle as _buckle
from nh_acc_batch4 import mirror_piece

HP = math.pi / 2
HEAD_R = 0.612   # the R6 head's face cylinder (Kit A's masks)


def dense(ob, longer=0.04):
    """apply the modifiers and subdivide long edges twice, so a flat mask bends smoothly round the head"""
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for _ in range(2):
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > longer], cuts=1, use_grid_fill=True)
    bm.to_mesh(ob.data); bm.free()
    return ob


def head_r(z):
    """the mannequin head's radius at height z (a cylinder r 0.6, its top and bottom edges rounded r 0.25) plus the
    masks' even gap: 0.612 on the face, following the rounding in at the brow and the chin"""
    if 1.15 <= z <= 1.85:
        r = 0.6
    else:
        d = min(0.25, (z - 1.85) if z > 1.85 else (1.15 - z))
        r = 0.35 + math.sqrt(max(0.0, 0.0625 - d * d))
    return r + 0.012


def wrap_sculpt(ob, sculpt, R=HEAD_R):
    """bend a flat front mask (x across, -y out of the face, z up; y 0 the back) round the head: the back keeps an even
    gap off the real (rounded) head, the front takes sculpt(x, z). (Before 2026-11-12 the whole shell rode the sculpt,
    so the back stood off the face behind the nose and chin, and the temples' negative sculpt sank it into the head.)
    A negative sculpt thins the shell to no less than 40% of its depth."""
    me = ob.data
    inv = ob.matrix_world.inverted()
    pts = [ob.matrix_world @ v.co for v in me.vertices]
    depth = max(0.004, max(-p.y for p in pts))
    for v, co in zip(me.vertices, pts):
        ang = co.x / R
        t = min(1.0, max(0.0, -co.y / depth))
        sc = max(sculpt(co.x, co.z), -0.6 * depth)
        r = head_r(co.z) - co.y + sc * t
        v.co = inv @ Vector((r * math.sin(ang), -r * math.cos(ang), co.z))
    me.update()


def on_face(x, z, sculpt, off, R=HEAD_R):
    """a point off the mask's front: off is measured from the head's surface + gap, as the shell's depth is"""
    ang = x / R
    r = head_r(z) + off + max(sculpt(x, z), -0.6 * off)
    return (r * math.sin(ang), -r * math.cos(ang), z)


def g(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


def smooth_shade(ob):
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    ob.data.update()


def dashes(name, pts, r, mat, step=2, fill=0.7, sides=4):
    """running stitches: short thread segments along a poly line (light square cords, about 12 triangles each)"""
    from nh_acc_batch4 import wire
    for k in range(0, len(pts) - 1, step):
        a, b = Vector(pts[k]), Vector(pts[k + 1])
        wire(f"{name}{k}", [tuple(a), tuple(a.lerp(b, fill))], r, mat, sides=sides)


# ---------------------------------------------------------------- the kintsugi porcelain mask (full face, sculpted)
def porcelain_sculpt(x, z):
    ax = abs(x)
    nose = 0.075 * g(x, 0, 0.055) * smooth(1.30, 1.40, z) * (1 - smooth(1.58, 1.70, z)) + 0.03 * g(x, 0, 0.09) * g(z, 1.33, 0.05)
    brow = 0.030 * g(ax, 0.20, 0.13) * g(z, 1.69, 0.035)
    socket = -0.022 * g(ax, 0.205, 0.10) * g(z, 1.60, 0.05)
    cheek = 0.026 * g(ax, 0.30, 0.10) * g(z, 1.43, 0.08)
    lips = 0.024 * g(x, 0, 0.11) * g(z, 1.20, 0.028) + 0.012 * g(x, 0, 0.08) * g(z, 1.155, 0.02)
    chin = 0.035 * g(x, 0, 0.16) * g(z, 1.06, 0.06)
    temples = -0.02 * smooth(0.36, 0.55, ax)
    return nose + brow + socket + cheek + lips + chin + temples


def porcelain_outline():
    pts = []
    n = 72
    for i in range(n):
        a = 2 * math.pi * i / n
        c, sn = math.cos(a), math.sin(a)
        x = 0.50 * math.copysign(abs(c) ** 0.78, c)
        z = 1.42 + (0.40 if sn > 0 else 0.42) * math.copysign(abs(sn) ** 0.85, sn)
        if sn < 0:   # a narrower jaw to a soft chin
            x *= 1 - 0.30 * abs(sn) ** 2
        pts.append((x, z))
    return pts


def almond(cx, cz, w, h, tilt, n=24):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = w * math.cos(a)
        z = h * math.sin(a) * (1 - 0.35 * (x / w) ** 2) + tilt * x
        out.append((cx + x, cz + z))
    return out


@item("CPorcelain", "Kintsugi porcelain mask", views=["front34", "front", "side"], close=((1.5, -3.6, 1.65), (0, -0.6, 1.45), 60))
def build_porcelain(M, key="CPorcelain"):
    piece(key, "Head")
    porcelain = A.mat_flat("PorcelainGlaze", (0.93, 0.92, 0.89), rough=0.10, coat=0.8, noise=35, bump=0.006, vary=0.02, wear=0.04, dirt=0.4)
    gold = A.mat_metal("KintsugiGold", (1.0, 0.76, 0.33), rough=0.16, scratch=0.15, wear=0.15)
    ink = A.mat_flat("PaintInk", (0.012, 0.010, 0.014), rough=0.25, coat=0.4, noise=20, bump=0.0, vary=0.02, wear=0.0)
    rouge = A.mat_flat("PaintRouge", (0.36, 0.03, 0.06), rough=0.22, coat=0.5, noise=20, bump=0.0, vary=0.03, wear=0.0)
    outline = ccw(porcelain_outline())
    eyes = [ccw(almond(sx * 0.205, 1.605, 0.098, 0.040, -0.08 * sx)) for sx in (-1, 1)]
    ob = A.extrude_poly("PorcelainShell", outline, 0.022, porcelain, frame((0, 0, 0)), bevel=0.006, segments=3,
                        holes=[e[::-1] for e in eyes])
    dense(ob)
    wrap_sculpt(ob, porcelain_sculpt)
    smooth_shade(ob)
    # a fine gilt rim round the edge and both eyes
    for k, loop in enumerate([outline] + eyes):
        A.tube(f"PorcelainRim{k}", [on_face(x, z, porcelain_sculpt, 0.023) for x, z in loop], 0.0055, gold, closed=True, res=4)
    # painted: lashes over each eye (flicked at the outer corner), the lips, a tear-mark under the right eye
    for sx in (-1, 1):
        lash = [(sx * 0.205 + 0.112 * math.cos(a), 1.605 + 0.050 * math.sin(a) - 0.08 * sx * 0.112 * math.cos(a))
                for a in [math.pi * (0.08 + 0.84 * i / 12) for i in range(13)]]
        A.tube(f"Lash{sx}", [on_face(x, z, porcelain_sculpt, 0.025) for x, z in lash], 0.006, ink, res=4,
               taper=lambda t: 0.4 + 0.6 * math.sin(math.pi * t))
        for k in range(4):
            x0 = sx * (0.205 + 0.10 - 0.012 * k); z0 = 1.625 + 0.006 * k
            A.tube(f"LashF{sx}{k}", [on_face(x0, z0, porcelain_sculpt, 0.025),
                                    on_face(x0 + sx * 0.04, z0 + 0.035 - 0.006 * k, porcelain_sculpt, 0.025)],
                   0.003, ink, res=4, taper=lambda t: 1 - 0.8 * t)
    lips = []
    for i in range(28):
        a = 2 * math.pi * i / 28
        x = 0.075 * math.cos(a)
        up = math.sin(a) > 0
        z = 1.188 + (0.024 if up else 0.020) * math.sin(a) * (1 - 0.5 * math.cos(a) ** 2) - (0.006 * g(x, 0, 0.03) if up else 0)
        lips.append((x, z))
    lo = A.extrude_poly("PaintLips", ccw(lips), 0.003, rouge, frame((0, -0.024, 0)), bevel=0.0, segments=1)
    dense(lo, longer=0.02); wrap_sculpt(lo, porcelain_sculpt); smooth_shade(lo)
    tear = []
    for i in range(16):
        a = 2 * math.pi * i / 16
        tear.append((-0.235 + 0.012 * math.cos(a) * (1 - 0.6 * max(0, -math.sin(a))), 1.50 + 0.028 * math.sin(a)))
    to = A.extrude_poly("PaintTear", ccw(tear), 0.003, rouge, frame((0, -0.024, 0)), bevel=0.0, segments=1)
    dense(to, longer=0.01); wrap_sculpt(to, porcelain_sculpt); smooth_shade(to)
    # the gold seam: a crack mended with gold, branching across the brow and down the cheek
    main = [(0.05, 1.82), (0.03, 1.77), (0.075, 1.72), (0.06, 1.67), (0.11, 1.585), (0.15, 1.54), (0.13, 1.49), (0.20, 1.44),
            (0.24, 1.37), (0.22, 1.31), (0.30, 1.24), (0.33, 1.17)]
    branches = [[(0.11, 1.585), (0.06, 1.55), (0.02, 1.52)], [(0.20, 1.44), (0.28, 1.46), (0.36, 1.43), (0.42, 1.45)],
                [(0.06, 1.67), (-0.02, 1.70), (-0.07, 1.74), (-0.13, 1.73)], [(0.24, 1.37), (0.18, 1.30), (0.17, 1.24)]]

    def seam(name, pts, r):
        P = []
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            for t in (0, 0.33, 0.66):
                P.append(on_face(lerp(x0, x1, t), lerp(z0, z1, t), porcelain_sculpt, 0.0235))
        P.append(on_face(*pts[-1], porcelain_sculpt, 0.0235))
        A.tube(name, P, r, gold, res=6, poly=True, taper=lambda t: 0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.1)))
    seam("GoldSeam", main, 0.0075)
    for k, b in enumerate(branches):
        seam(f"GoldBranch{k}", b, 0.0050)
    return {"notes": "concept"}


# ---------------------------------------------------------------- the beaked night-watch mask (sculpted leather, lofted beak)
# Hair-friendly (2026-11-12): every catalog hair with a fringe or side locks crosses anything over the brow line or past
# the temples, so the leather keeps inside |x| 0.43 and under z 1.75 (it fitted no hair at all when it rose over the
# forehead to z 1.90 and wrapped to the temples); the beak and the lenses project forward, clear of the hair.
WATCH_EYE = (0.205, 1.605)
WATCH_LENS = 0.075   # the crimson glass's radius


def beak_sculpt(x, z):
    ax = abs(x)
    brow = 0.020 * g(z, 1.695, 0.035) * (1 - smooth(0.22, 0.34, ax))
    return brow - 0.014 * smooth(0.26, 0.40, ax)


def beak_outline():
    """forehead (just over the brows) to under the cheekbones, down over the nose for the beak's root"""
    pts = []
    n = 72
    for i in range(n):
        a = 2 * math.pi * i / n
        c, sn = math.cos(a), math.sin(a)
        x = 0.425 * math.copysign(abs(c) ** (0.62 if sn >= 0 else 0.74), c)
        if sn >= 0:   # the top edge: level over the brows, easing down to the temples
            z = 1.585 + 0.155 * abs(sn) ** 0.45 - 0.02 * (abs(x) / 0.43) ** 3
        else:         # the bottom edge: under the cheekbones, dipping over the nose to carry the beak
            ax = abs(x)
            z = 1.585 - (0.16 + 0.155 * (1 - smooth(0.08, 0.30, ax))) * abs(sn) ** 0.5
        pts.append((x, z))
    return pts


@item("CPlague", "Beaked night-watch mask", views=["front34", "side", "front"], close=((2.4, -4.6, 1.7), (0, -0.85, 1.45), 70))
def build_plague(M, key="CPlague"):
    piece(key, "Head")
    leather = A.mat_leather("WatchLeather", (0.12, 0.085, 0.065), scale=3.4, wear=0.65)
    darker = A.mat_leather("WatchLeatherDark", (0.055, 0.045, 0.04), scale=3.4, wear=0.45)
    thread = A.mat_flat("WaxThread", (0.70, 0.60, 0.42), rough=0.7, noise=200, bump=0.2, vary=0.1, wear=0.0)
    brass, brass_old = M["brass"], M["brassold"]
    glass = A.mat_flat("CrimsonGlass", (0.42, 0.02, 0.05), rough=0.04, coat=0.9, noise=8, bump=0.0, vary=0.02, wear=0.0)
    # the half-mask: brow to cheekbones and down over the nose, two holes behind the lenses
    outline = ccw(beak_outline())
    ex, ez = WATCH_EYE
    eyes = [ccw([(sx * ex + 0.083 * math.cos(a), ez + 0.083 * math.sin(a)) for a in [2 * math.pi * i / 24 for i in range(24)]])
            for sx in (-1, 1)]
    ob = A.extrude_poly("WatchMask", outline, 0.026, leather, frame((0, 0, 0)), bevel=0.008, segments=3, holes=[e[::-1] for e in eyes])
    dense(ob, longer=0.05); wrap_sculpt(ob, beak_sculpt); smooth_shade(ob)
    edge = offset_poly(outline, 0.022)
    dashes("EdgeStitch", [on_face(x, z, beak_sculpt, 0.027) for x, z in edge], 0.0040, thread, sides=3)
    # the lenses: domed crimson glass in a brass bezel with six screws, in a darker leather cup facing out of the face
    for sx in (-1, 1):
        cx = sx * ex
        ang = cx / HEAD_R
        n_ = Vector((math.sin(ang), -math.cos(ang), 0))
        u = Vector((math.cos(ang), math.sin(ang), 0))
        c = Vector(on_face(cx, ez, beak_sculpt, 0.024))
        rot = (HP, 0, ang)
        L = WATCH_LENS
        # (low: a fringe hangs 0.03 .. 0.08 in front of the eyes, so the lenses stand no more than 0.045 off the leather)
        A.lathe(f"LensCup{sx}", [(L + 0.004, 0), (L + 0.025, 0.0), (L + 0.029, 0.014), (L + 0.017, 0.026), (L + 0.004, 0.026)],
                tuple(c), darker, seg=28, rot=rot)
        A.torus(f"LensBezel{sx}", L + 0.011, 0.0135, tuple(c + n_ * 0.027), brass, rot=rot, major=28, minor=6)
        A.torus(f"LensBezelIn{sx}", L - 0.002, 0.0070, tuple(c + n_ * 0.031), brass_old, rot=rot, major=28, minor=5)
        A.sphere(f"Lens{sx}", L, tuple(c + n_ * 0.019), glass, scale=(1, 0.24, 1), rot=(0, 0, ang), seg=22, rings=10)
        for k in range(6):
            a = 2 * math.pi * k / 6 + 0.3
            p = c + n_ * 0.035 + u * ((L + 0.011) * math.cos(a)) + Vector((0, 0, (L + 0.011) * math.sin(a)))
            A.sphere(f"Screw{sx}{k}", 0.0085, tuple(p), brass_old, seg=6, rings=4)
    # the beak: lofted from the nose (its root sunk into the leather), an oval section with a ridge, curving down to a
    # slight hook
    root = Vector((0, -0.600, 1.445))
    path = [root + Vector((0, -0.36 * t - 0.38 * t * t, -0.08 * t - 0.36 * t ** 2.4)) for t in [i / 24 for i in range(25)]]
    verts, faces = [], []
    N = 24
    for i, p in enumerate(path):
        t = i / (len(path) - 1)
        w = 0.150 * (1 - t) ** 0.85 + 0.010
        h = 0.148 * (1 - t) ** 0.9 + 0.010
        d = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = Vector((1, 0, 0))
        up = side.cross(d).normalized()
        if up.z < 0:
            up = -up
        up = Vector((0, 0, 1)).lerp(up, smooth(0.0, 0.3, t)).normalized()   # the root rings stand upright in the leather
        for k in range(N):
            a = 2 * math.pi * k / N
            sa = math.sin(a)
            ridge = 0.012 * max(0.0, sa) ** 8 * (1 - t)
            q = p + side * (w * math.cos(a)) + up * ((h + ridge) * sa) * (1 if sa > 0 else 0.86)
            if i == 0:   # the root ring sunk into the leather, following the face (never into the head)
                rr = head_r(q.z) + 0.010
                an = math.atan2(q.x, -q.y)
                q = Vector((rr * math.sin(an), -rr * math.cos(an), q.z))
            verts.append(tuple(q))
    for i in range(len(path) - 1):
        for k in range(N):
            a, b = i * N + k, i * N + (k + 1) % N
            faces.append((a, a + N, b + N, b))
    tip = len(verts)
    verts.append(tuple(path[-1] + (path[-1] - path[-2]).normalized() * 0.02))
    last = (len(path) - 1) * N
    faces += [(last + k, tip, last + (k + 1) % N) for k in range(N)]
    beak = A.mesh_from("Beak", verts, faces, leather, bevel=0.0)
    smooth_shade(beak)
    for kk, ring_k in ((0, N // 4), (1, 0), (2, N // 2)):   # stitched along the ridge and both sides
        line = []
        for i in range(3, len(path) - 3):
            q = Vector(verts[i * N + ring_k])
            line.append(tuple(q + (q - path[i]).normalized() * 0.005))
        dashes(f"BeakStitch{kk}_", line, 0.0040, thread, sides=3)
    for k, t in enumerate((0.20, 0.48)):   # two brass bands round the beak
        i = int(round(t * (len(path) - 1)))
        ring = [tuple(Vector(verts[i * N + j]) + (Vector(verts[i * N + j]) - path[i]).normalized() * 0.007) for j in range(N)]
        A.tube(f"BeakBand{k}", ring, 0.011, brass, closed=True, res=6, poly=True)
    for sx in (-1, 1):   # nostril vents with brass grommets near the root
        q = Vector(verts[4 * N + N // 4]) + Vector((sx * 0.055, 0, -0.010))
        A.torus(f"Vent{sx}", 0.016, 0.0055, tuple(q + Vector((0, 0, 0.005))), brass, rot=(0.6, 0, 0), major=14, minor=5)
        A.sphere(f"VentHole{sx}", 0.0145, tuple(q), darker, scale=(1, 1, 0.35), rot=(0.6, 0, 0), seg=10, rings=6)
    return {"notes": "concept"}


