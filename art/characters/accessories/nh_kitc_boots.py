"""Kit C concept: cavalier knee boots at the shipping standard (owner: "Make the boots look wayyy cooler and better").
R6 legs touch at x = 0, so the boot covers the front, outer and back faces and stays flush on the inner face.
Imported by nh_kitc_concepts.py."""
import math
import bpy, bmesh
from mathutils import Vector
import nh_acc as A
from nh_acc import item, piece, smooth, lerp
from nh_acc_batch1 import ccw, offset_poly, buckle as _buckle
from nh_acc_batch4 import mirror_piece
from nh_kitc_hq import dashes

HP = math.pi / 2
LEG_X0, LEG_X1 = 0.0, 1.0   # the left leg's inner and outer faces


def boot_section(off, bulge=0.022, r=0.20, n_face=10, n_corner=8):
    """the boot's section at one height: a U from the inner front edge round the front, outer and back faces to the
    inner back edge, `off` outside the leg, with rounded outer corners and faces bowed a little outward (not a box).
    Returns [(x, y, w)], w the 'frontness' (1 at the front, 0 at the back) for shaping the top line."""
    pts = []
    for i in range(n_face + 1):            # the front face, inner edge to the corner
        t = i / n_face
        x = lerp(LEG_X0 + 0.004, LEG_X1 - r, t)
        pts.append((x, -0.5 - off - bulge * math.sin(math.pi * (0.5 + 0.5 * t)), 1.0 - 0.15 * t))
    for i in range(1, n_corner):           # the front-outer corner
        a = -HP + HP * i / n_corner
        pts.append((LEG_X1 - r + (r + off) * math.cos(a), -0.5 + r + (r + off) * math.sin(a), 0.85 - 0.35 * i / n_corner))
    for i in range(n_face + 1):            # the outer face
        t = i / n_face
        pts.append((LEG_X1 + off + bulge * math.sin(math.pi * t), lerp(-0.5 + r, 0.5 - r, t), 0.5 - 0.4 * t))
    for i in range(1, n_corner):           # the outer-back corner
        a = HP * i / n_corner
        pts.append((LEG_X1 - r + (r + off) * math.cos(a), 0.5 - r + (r + off) * math.sin(a), 0.1 * (1 - i / n_corner)))
    for i in range(n_face + 1):            # the back face, to the inner edge
        t = i / n_face
        pts.append((lerp(LEG_X1 - r, LEG_X0 + 0.004, t), 0.5 + off + bulge * math.sin(math.pi * (1 - 0.5 * t)), 0.0))
    return pts


def top_line(w):
    """the cavalier top: up over the knee in front, down behind"""
    return -1.98 + 0.27 * w ** 1.6


def slab(name, outline, z_top, h, mat, bevel=0.012):
    """a flat piece (a sole, a heel lift) from a counter-clockwise outline in plan (x, y)"""
    bm = bmesh.new()
    top = [bm.verts.new((x, y, z_top)) for x, y in outline]
    f = bm.faces.new(top)
    if f.normal.z < 0:
        f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, -h), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = A._new_obj(name, me)
    return A._finish(ob, mat, bevel=bevel, segments=2)


def outward(p, z=None):
    c = Vector((0.5, 0.0, p.z))
    d = p - c
    d.z = 0
    return d.normalized()


@item("CBoots", "Cavalier knee boots", views=["front34", "side", "back", "front"], close=((2.6, -4.2, -2.1), (0.5, -0.15, -2.45), 62))
def build_boots(M):
    piece("CBootL", "LeftLeg")
    leather = A.mat_leather("BootCalf", (0.045, 0.040, 0.044), scale=2.4, wear=0.8)
    lining = A.mat_cloth("BootLining", (0.20, 0.02, 0.035), weave=420, rough=0.5, sheen=0.4, bump=0.04, twill=False)
    strap_m = M["leather_oxblood"]
    sole_m = A.mat_leather("BootSole", (0.09, 0.055, 0.03), scale=2.0, wear=0.4)
    welt = A.mat_leather("BootWelt", (0.22, 0.12, 0.06), scale=3.0, wear=0.6)
    thread = A.mat_flat("BootThread", (0.72, 0.62, 0.44), rough=0.7, noise=200, bump=0.2, vary=0.1, wear=0.0)
    cord = A.mat_cloth("LaceCord", (0.04, 0.035, 0.04), weave=900, rough=0.7, bump=0.1)
    brass, brass_old = M["brass"], M["brassold"]
    z_bot = -2.945
    nz = 18
    sec = boot_section(0.036)

    def calf(z):   # a little fuller over the calf
        return 0.025 * smooth(-2.6, -2.1, z)

    # the shaft: one continuous bowed U, cut to the cavalier top line
    G = []
    for k, (_, _, w) in enumerate(sec):
        zt = top_line(w)
        col = []
        for j in range(nz + 1):
            z = lerp(z_bot, zt, j / nz)
            x, y, _ = boot_section(0.036 + calf(z))[k]
            col.append(Vector((x, y, z)))
        G.append(col)
    A.surface("BootShaft", G, 0.026, leather)
    # the bucket cuff: it flares out from the top line, its crimson lining showing inside
    Gc, Gl = [], []
    for k, (_, _, w) in enumerate(sec):
        zt = top_line(w)
        col, coll = [], []
        for j in range(5):
            t = j / 4
            x, y, _ = boot_section(0.064 + 0.045 * t ** 1.4)[k]
            col.append(Vector((x, y, zt - 0.16 + 0.22 * t)))
            x2, y2, _ = boot_section(0.050 + 0.045 * t ** 1.4)[k]
            coll.append(Vector((x2, y2, zt - 0.14 + 0.22 * t)))
        Gc.append(col); Gl.append(coll)
    A.surface("BootCuff", Gc, 0.020, leather)
    A.surface("BootCuffLining", Gl, 0.008, lining)
    A.tube("BootCuffEdge", [tuple(Gc[k][-1]) for k in range(len(sec))], 0.012, leather, res=6)
    for k in range(2, len(sec) - 2, 4):   # brass studs round the cuff
        p = Gc[k][1]
        A.sphere(f"CuffStud{k}", 0.018, tuple(p + outward(p) * 0.014), brass_old, seg=10, rings=6)
    dashes("CuffStitch", [tuple(Gc[k][2] + outward(Gc[k][2]) * 0.012) for k in range(len(sec))], 0.0045, thread)
    # front lacing: brass hooks in two rows, the lace crossing between them and tied at the top
    hooks = []
    for n_, z in enumerate([lerp(-2.80, -1.98, i / 9) for i in range(10)]):
        row = []
        for xs in (0.40, 0.60):
            p = Vector((xs, -0.5 - 0.036 - calf(z) - 0.022 * math.sin(math.pi * (0.5 + 0.5 * xs / 0.8)) - 0.03, z))
            A.torus(f"Hook{n_}{xs}", 0.019, 0.006, tuple(p), brass, rot=(HP, 0, 0), major=12, minor=5)
            row.append(p + Vector((0, -0.006, 0)))
        hooks.append(row)
    lace = []
    for n_, row in enumerate(hooks):
        lace.append(tuple(row[n_ % 2])); lace.append(tuple(row[(n_ + 1) % 2]))
    A.tube("Lace", lace, 0.0085, cord, res=6, poly=True)
    top = hooks[-1]
    A.tube("LaceBow", [tuple(top[0]), tuple(top[0] + Vector((-0.04, -0.02, 0.05))), tuple((top[0] + top[1]) / 2 + Vector((0, -0.03, 0.02))),
                       tuple(top[1] + Vector((0.04, -0.02, 0.05))), tuple(top[1])], 0.008, cord, res=6)
    # the toe box: a closed loft from the instep to a rounded nose, in proportion with the 1-stud R6 leg (0.32 studs
    # long, narrowing from 0.86 to a 0.5 nose), its top sloping down from the instep, a little toe spring at the tip
    floor, sole_top = -3.0, -2.945   # nothing below the leg's bottom (the floor): the boot never sinks into the ground
    L, nv, na = 0.36, 18, 24

    def toe_dims(v):
        nose = math.sqrt(max(0.0, 1 - ((v - 0.62) / 0.38) ** 2)) if v > 0.62 else 1.0
        W = lerp(0.42, 0.20, v ** 1.15) * nose
        H = lerp(0.30, 0.13, v ** 0.85) * (0.40 + 0.60 * nose)
        y = -0.53 - L * v
        zb = sole_top + 0.022 * v ** 3   # toe spring
        return W, H, y, zb

    def toe_ring(v, grow=0.0, top_only=False):
        W, H, y, zb = toe_dims(v)
        W += grow; H += grow
        ring = []
        for i in range(na + 1):   # the top: a soft superellipse arch
            a = math.pi * i / na
            c, s_ = math.cos(a), math.sin(a)
            ring.append(Vector((0.5 + W * math.copysign(abs(c) ** 0.75, c), y - grow * 0.6 * v, zb + H * abs(s_) ** 0.7)))
        if not top_only:
            for i in range(1, 6):   # the flat underside, back across
                ring.append(Vector((0.5 - W + 2 * W * i / 6, y, zb)))
        return ring
    verts, faces = [], []
    rings = [toe_ring(j / nv) for j in range(nv + 1)]
    M_ = len(rings[0])
    for r in rings:
        verts += [tuple(p) for p in r]
    for j in range(nv):
        for i in range(M_):
            a, b = j * M_ + i, j * M_ + (i + 1) % M_
            faces.append((a, b, b + M_, a + M_))
    tip = len(verts)
    W, H, y, zb = toe_dims(1.0)
    verts.append((0.5, y - 0.01, zb + 0.10))
    last = nv * M_
    faces += [(last + i, last + (i + 1) % M_, tip) for i in range(M_)]
    toe = A.mesh_from("BootToe", verts, faces, leather, bevel=0.0)
    toe.data.polygons.foreach_set("use_smooth", [True] * len(toe.data.polygons))
    # a polished leather toe cap with a stitched edge, a line of brogue punching along it and a punched medallion
    # on the nose (the dress-boot finish), and a stitched seam where the toe box meets the vamp
    polish = A.mat_leather("BootCapPolish", (0.03, 0.027, 0.03), scale=2.0, rough_add=-0.25, wear=0.35)
    A.surface("BootToeCap", [[toe_ring(0.52 + 0.48 * j / 10, 0.007, True)[i] for j in range(11)] for i in range(na + 1)], 0.006, polish)
    edge = toe_ring(0.52, 0.0135, True)
    dashes("CapStitch", [tuple(p) for p in edge], 0.004, thread)
    punch = A.mat_flat("Punch", (0.005, 0.004, 0.005), rough=0.6, noise=10, bump=0.0, vary=0.0, wear=0.0)
    for i in range(2, na - 1, 2):
        p = toe_ring(0.555, 0.0135, True)[i]
        A.sphere(f"Brogue{i}", 0.0075, tuple(p), punch, scale=(1, 1, 1), seg=8, rings=4)
    for k, (du, dv) in enumerate(((0, 0), (-1, 0), (1, 0), (0, 1), (-2, 1), (2, 1), (-1, 2), (1, 2), (0, 3))):
        v = 0.70 + 0.045 * dv
        p = toe_ring(v, 0.0135, True)[na // 2 + du]
        A.sphere(f"Medallion{k}", 0.0065, tuple(p), punch, seg=8, rings=4)
    dashes("ToeSeam", [tuple(p + Vector((0, -0.012, 0))) for p in toe_ring(0.22, 0.012, True)], 0.0045, thread)
    # the sole: the boot's own footprint, an even margin round it, smoothed: the shaft's rounded heel and outer
    # corners, a smooth run into the almond toe and round its nose, flush on the inner side (the legs touch there)
    m = 0.024   # how far the sole stands out from the boot all round
    sec0 = boot_section(0.036 + m, bulge=0.0)
    back = [(x, y) for x, y, w in sec0 if y > -0.5 + 0.2 - 1e-6]            # inner back, back face, the rounded corner, outer face
    back = sorted(back, key=lambda p: (0 if p[1] >= 0.5 else 1, p[0] if p[1] >= 0.5 else -p[1]))
    outer_back = [(x, y) for x, y, w in sec0 if y > 0.25]                     # inner-back edge round to the outer side
    pts = [(0.004, y) for y in (0.5 + 0.036 + m,)]
    # walk: inner back -> back face -> outer-back corner -> outer face -> outer-front corner -> the toe's outer side ->
    # the nose -> the toe's inner side -> the inner front edge -> back along the inner edge
    walk = list(reversed([(x, y) for x, y, w in sec0]))                        # from the inner back edge round to the front
    walk = [p for p in walk if not (p[1] < -0.5 and p[0] < 0.5 + toe_dims(0)[0])]   # the front face gives way to the toe
    for j in range(nv + 1):
        W, H, y, zb = toe_dims(j / nv)
        walk.append((0.5 + W + m, y - 0.004))
    nose = toe_dims(1.0)
    walk.append((0.5, nose[2] - m - 0.004))
    for j in range(nv, -1, -1):
        W, H, y, zb = toe_dims(j / nv)
        walk.append((max(0.004, 0.5 - W - m), y - 0.004))
    walk.append((0.004, -0.5))

    def chaikin(poly, n=3, keep=lambda p: False):
        for _ in range(n):
            out = []
            for i in range(len(poly)):
                a, b = poly[i], poly[(i + 1) % len(poly)]
                if keep(a) and keep(b):
                    out.append(a)
                    continue
                out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
                out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
            poly = out
        return poly
    plan = ccw(chaikin(walk, 3, keep=lambda p: p[0] < 0.006))   # smooth, but keep the inner edge straight and flush
    slab("BootSole", plan, sole_top, sole_top - floor, sole_m, bevel=0.022)
    slab("BootWelt", ccw(offset_poly(plan, 0.006)), sole_top + 0.016, 0.018, welt, bevel=0.007)
    welt_line = [(x, y, sole_top + 0.017) for x, y in offset_poly(plan, 0.028) if x > 0.02]
    dashes("WeltStitch", welt_line, 0.004, thread, step=1, fill=0.55)
    # the heel: a stacked block up the back of the foot (it can't go under the foot: that's the floor), following the
    # sole's rounded back, a brass cap on its back edge
    arc = sorted([p for p in plan if p[1] > 0.22], key=lambda p: math.atan2(p[1] - 0.22, p[0] - 0.5))   # outer, round the back, inner
    heel = ccw(arc + [(0.004, 0.22), (arc[0][0], 0.22)])
    for k, (h, mt) in enumerate(((0.055, sole_m), (0.05, welt), (0.055, sole_m))):
        slab(f"Heel{k}", ccw(offset_poly(heel, 0.004 * k)), floor + 0.055 * (k + 1), h, mt, bevel=0.01)
    cap = [(x, y + 0.004, floor + 0.035) for x, y in offset_poly(heel, -0.004) if y > 0.5 + 0.036 and x > 0.03]
    A.tube("HeelCap", cap, 0.012, brass_old, res=6, poly=True)
    # two straps across the front and outer side, each buckled behind the ankle
    for n_, z in enumerate((-2.70, -2.30)):
        band = [p for p in boot_section(0.064 + calf(z)) if p[2] > 0.25]
        Gs = [[Vector((x, y, z - 0.032 - 0.04 * (1 - w))), Vector((x, y, z + 0.032 - 0.04 * (1 - w)))] for x, y, w in band]
        A.surface(f"Strap{n_}", Gs, 0.014, strap_m)
        end = Gs[-1][0].lerp(Gs[-1][1], 0.5)
        _buckle(f"Buckle{n_}", tuple(end + Vector((0.02, 0.02, 0))), 0.11, 0.12, brass, rot=(0, 0, -HP))
        A.box(f"StrapTail{n_}", (0.012, 0.16, 0.06), tuple(end + Vector((0.016, 0.12, 0))), strap_m, bevel=0.008)
        for i in range(2):
            A.cyl(f"Punch{n_}{i}", 0.009, 0.016, tuple(end + Vector((0.022, 0.10 + 0.045 * i, 0))), M["black_enamel"], rot=(0, HP, 0),
                  verts=10, bevel=0.0)
    # a pull loop at the back of the cuff
    A.tube("PullLoop", [(0.50, 0.62, -2.04), (0.50, 0.68, -1.94), (0.50, 0.64, -1.86), (0.50, 0.59, -1.92)], 0.016, strap_m, res=6)
    mirror_piece("CBootL", "CBootR")
    piece("CBootR", "RightLeg")
    return {"notes": "concept"}
