"""Kit C, batch C2: three sculpted masks at the shipping standard of nh_kitc_hq.py (the kintsugi porcelain and the beaked
night-watch masks). All three are Head pieces, unisex, held on by sitting on the face (no ties round the head).

  FoxMask    - Fox half-mask (kitsune crossed with the gothic school): one solid shell of glossy black lacquer covering
               the brow, eyes and nose, a short carved muzzle with a glossy nose, pointed ears formed by the mask's upper
               corners (crimson inner ears), crimson brush-stroke markings (an upswept liner round each eye, a flame
               between the brows over a gold bead, strokes down the muzzle, whisker dots), a gilt line round the edge
               and both eyes, and a crimson silk tassel hanging from the tip of each cheek tuft on a gold bead and collar.
  WolfMask   - Wolf half-mask: antique silver-grey, the muzzle down to the nose (the mouth stays free). A sharp brow
               ridge slanting down to a frown over angry eyes ringed in blackened iron (carved in: a deep socket under
               the ridge), pointed ears at the mask's upper corners with dark inner ears and fur, carved fur locks in
               relief swept out along the brows and across the cheeks to a jagged ruff, and a black glossy nose.

Hair (2026-11-12): every head piece is checked against the 35 catalog hairs, and anything over the brow line, past the
temples or over the head crosses the fringe or side locks of nearly all of them. Fox and Wolf therefore keep inside
|x| 0.45 with the ears lying on the brow (tips z 1.85), and their relief stays low where hair lies over the mask (the
brows and cheeks, r 0.66 .. 0.70); the muzzle, where no hair hangs, keeps its full depth.
  GrilleMask - Iron grille mask: the lower face only (nose bridge to chin), a dark oxblood leather backing under
               thirteen bevelled vertical iron bars, a riveted iron frame band round the edge, a riveted strap across
               the mouth, brass rivets, and a brass shield crest with a crimson enamel field and a brass rose.

Built flat (x across, z up) and bent round the R6 head's face cylinder like the references, but as solid shells: the
back sits on the head's surface at an even 0.012 offset (following the head's rounded top and bottom edges), only the
front carries the sculpt, so a muzzle is solid rather than a hollow shell and there's no gap under it. Each shell is
triangulated with a constrained Delaunay mesh (fine on the front, coarse on the hidden back) to stay inside the
12,000-triangle mesh limit; detail (paint strokes, fur locks, rivets) is laid on the front surface as low-poly strips
and domes that hug it.

E:/Blender/blender.exe -b --factory-startup -P nh_kitc_masks_a.py -- FoxMask --nobake --out E:/NH-Work/kitc_masks_a --res 700
(--quick: the close-ups only, on the standard mannequin)
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import nh_acc as A
sys.modules.setdefault("nh_acc", A)
from nh_acc import item, piece, smooth, lerp
from nh_acc_batch1 import ccw, offset_poly
from nh_kitc_hq import g, smooth_shade, HEAD_R, almond

HP = math.pi / 2
GAP = 0.012          # the mask's back sits this far off the head's surface (the references' offset)
KEYS = ["FoxMask", "WolfMask", "GrilleMask"]


# ================================================================ the head and the face surface
def head_r(z):
    """the R6 mannequin head: a cylinder r 0.6 (z 0.9 to 2.1) with its top and bottom edges rounded (bevel 0.25)"""
    if z > 1.85:
        return 0.35 + math.sqrt(max(0.0, 0.0625 - (z - 1.85) ** 2))
    if z < 1.15:
        return 0.35 + math.sqrt(max(0.0, 0.0625 - (1.15 - z) ** 2))
    return 0.6


def back_r(z, lean_from=None, lean=0.2):
    """where the mask's back sits: on the head (following its rounded edges); above lean_from (ears) it rises
    straight on, leaning back gently, always in front of the head"""
    if lean_from is not None and z > lean_from:
        return max(head_r(lean_from) + GAP - lean * (z - lean_from), head_r(z) + GAP)
    return head_r(z) + GAP


def P(x, z, off, F):
    """a point on the surface F(x, z) (a radius round the face cylinder), lifted off it by `off`"""
    ang = x / HEAD_R
    r = F(x, z) + off
    return Vector((r * math.sin(ang), -r * math.cos(ang), z))


def N(x, z, F, e=0.004):
    a = P(x + e, z, 0, F) - P(x - e, z, 0, F)
    b = P(x, z + e, 0, F) - P(x, z - e, 0, F)
    n = b.cross(a).normalized()
    ang = x / HEAD_R
    return n if n.dot(Vector((math.sin(ang), -math.cos(ang), 0))) > 0 else -n


# ================================================================ curves and outlines
def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def cr_open(ctrl, step):
    """a Catmull-Rom curve through ctrl, sampled about every `step`"""
    Pp = [Vector(c) for c in ctrl]
    if len(Pp) == 2:
        Pp = [Pp[0], Pp[0].lerp(Pp[1], 0.5), Pp[1]]
    Pp = [2 * Pp[0] - Pp[1]] + Pp + [2 * Pp[-1] - Pp[-2]]
    out = []
    for i in range(1, len(Pp) - 2):
        k = max(1, int(math.ceil((Pp[i + 1] - Pp[i]).length / step)))
        for j in range(k):
            out.append(tuple(_cr(Pp[i - 1], Pp[i], Pp[i + 1], Pp[i + 2], j / k)))
    out.append(tuple(Pp[-2]))
    return out


def outline_loop(half, corners=(), step=0.024):
    """a closed outline mirrored from its +x half (top centre -> round the +x side -> bottom centre), a smooth
    Catmull-Rom loop with sharp corners (ear tips, fur tufts) at the given half indices"""
    nh = len(half)
    full = list(half) + [(-x, z) for x, z in reversed(half[1:-1])]
    cs = set(corners) | {nh + (nh - 2 - i) for i in corners if 0 < i < nh - 1}
    if not cs:
        n = len(full)
        Pp = [Vector(c) for c in full]
        out = []
        for i in range(n):
            k = max(1, int(math.ceil((Pp[(i + 1) % n] - Pp[i]).length / step)))
            for j in range(k):
                out.append(tuple(_cr(Pp[i - 1], Pp[i], Pp[(i + 1) % n], Pp[(i + 2) % n], j / k)))
        return ccw(out)
    cl = sorted(cs)
    full = full[cl[0]:] + full[:cl[0]]
    cl = sorted((c - cl[0]) % len(full) for c in cs) + [len(full)]
    full = full + [full[0]]
    out = []
    for a, b in zip(cl, cl[1:]):
        out += cr_open(full[a:b + 1], step)[:-1]
    return ccw(out)


def resample(loop, step, closed=True):
    pts = [Vector(p) for p in loop] + ([Vector(loop[0])] if closed else [])
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        L = (b - a).length
        d = step - acc
        while d <= L:
            out.append(a.lerp(b, d / L))
            d += step
        acc = L - (d - step)
    return [tuple(p) for p in (out[:-1] if closed and (out[-1] - pts[0]).length < step * 0.5 else out)]


def _seg_d(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * t)).length


def edge_dist(p, loops):
    p = Vector(p)
    best = 1e9
    for lp in loops:
        for i in range(len(lp)):
            d = _seg_d(p, Vector(lp[i - 1]), Vector(lp[i]))
            if d < best:
                best = d
    return best


def inside(p, loop):
    return A._inside(p, loop)


# ================================================================ solid shells (constrained Delaunay, wrapped)
def _cdt(loops, s, fine=None, margin=0.6, fs=0.6, extra=()):
    """triangulate the region inside loops[0] minus the holes loops[1:] with interior points every s (s * 0.6 where
    fine(x, z)); returns verts2d, tris, the output index of each input boundary point"""
    bnd = [p for lp in loops for p in lp]
    xs = [p[0] for p in loops[0]]; zs = [p[1] for p in loops[0]]
    pts = []
    grid = {}
    cell = 0.01
    for (x, z) in extra:   # rows laid along a crisp sculpted edge (a brow), so it's not stepped by the grid
        if inside((x, z), loops[0]) and not any(inside((x, z), h) for h in loops[1:]) and edge_dist((x, z), loops) > 0.008:
            pts.append((x, z))
            grid.setdefault((int(x // cell), int(z // cell)), []).append((x, z))

    def near(x, z, d):
        i, j = int(x // cell), int(z // cell)
        r = int(d // cell) + 1
        for a in range(i - r, i + r + 1):
            for b in range(j - r, j + r + 1):
                for q in grid.get((a, b), ()):
                    if (q[0] - x) ** 2 + (q[1] - z) ** 2 < d * d:
                        return True
        return False
    for ss, want in ((s, False), (s * fs, True)):
        if want and fine is None:
            continue
        dz = ss * 0.866
        j = 0
        z = min(zs) + dz * 0.5
        while z < max(zs):
            x = min(xs) + (ss * 0.5 if j % 2 else 0.0)
            while x < max(xs):
                f = bool(fine and fine(x, z))
                if f == want and inside((x, z), loops[0]) and not any(inside((x, z), h) for h in loops[1:]) \
                        and edge_dist((x, z), loops) > margin * ss and not (grid and near(x, z, 0.75 * ss)):
                    pts.append((x, z))
                x += ss
            z += dz; j += 1
    coords = [Vector(p) for p in bnd + pts]
    edges = []
    k = 0
    for lp in loops:
        n = len(lp)
        edges += [(k + i, k + (i + 1) % n) for i in range(n)]
        k += n
    vs, es, fs, ov, oe, of = delaunay_2d_cdt(coords, edges, [], 1, 1e-7)
    idx = {}
    for o, ins in enumerate(ov):
        for i in ins:
            idx[i] = o
    keep = []
    for f in fs:
        c = sum((Vector(vs[i]) for i in f), Vector((0, 0))) / len(f)
        if inside(c, loops[0]) and not any(inside(c, h) for h in loops[1:]):
            keep.append(f)
    return [tuple(v) for v in vs], keep, [idx[i] for i in range(len(bnd))]


def shell(name, outline, depth, mat, holes=(), sf=0.024, sb=0.07, bevel=0.006, seg=2, fine=None, fs=0.6, extra=()):
    """a flat solid plate (front toward -Y at y = -depth, back at y = 0), fine on the front, coarse on the back,
    its rim bevelled; wrap it with wrap_r"""
    loops = [ccw(list(outline))] + [list(reversed(ccw(list(h)))) for h in holes]
    fv, ft, fb = _cdt(loops, sf, fine, fs=fs, extra=extra)
    bv, bt, bb = _cdt(loops, sb)
    verts = [(x, -depth, z) for x, z in fv] + [(x, 0.0, z) for x, z in bv]
    o = len(fv)
    faces = [tuple(f) for f in ft] + [tuple(o + i for i in reversed(f)) for f in bt]
    k = 0
    for lp in loops:
        n = len(lp)
        for i in range(n):
            a, b = k + i, k + (i + 1) % n
            faces.append((fb[b], fb[a], o + bb[a], o + bb[b]))
        k += n
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = A._new_obj(name, me)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    if bevel > 0:   # only the front rim (the back rim lies on the head, unseen)
        rim = [e for e in bm.edges if all(v.co.y < -depth * 0.5 for v in e.verts)
               and any(abs(f.normal.y) < 0.5 for f in e.link_faces)]
        vs = list({v for e in rim for v in e.verts})
        bmesh.ops.bevel(bm, geom=rim + vs, offset=bevel, offset_type="OFFSET", segments=seg, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    bm.to_mesh(me); bm.free()
    ob["nh_depth"] = depth
    return A._finish(ob, mat)


def wrap_r(ob, rfun):
    """bend a flat shell round the face cylinder: a vertex at depth fraction t (0 back, 1 front) goes to radius
    rfun(x, z, t)"""
    depth = ob["nh_depth"]
    for v in ob.data.vertices:
        x, y, z = v.co
        t = min(1.0, max(0.0, -y / depth))
        r = rfun(x, z, t)
        ang = x / HEAD_R
        v.co = (r * math.sin(ang), -r * math.cos(ang), z)
    ob.data.update()
    smooth_shade(ob)
    return ob


def layer(name, outline, F, lo, hi, mat, holes=(), sf=0.02, bevel=0.002, seg=1):
    """a plate laid on the surface F from F + lo (sunk a touch) to F + hi: inlays, bands, plates"""
    ob = shell(name, outline, hi - lo, mat, holes=holes, sf=sf, sb=0.05, bevel=bevel, seg=seg)
    return wrap_r(ob, lambda x, z, t: F(x, z) + lo + (hi - lo) * t)


# ================================================================ surface detail: strips, domes, lines
def strip(name, ctrl, width, height, F, mat, step=0.014, taper=None, prof=None, sink=0.0025, cap=0.6, closed=False):
    """a strip lying on F along a curve through ctrl: paint strokes (flat dome profile) and carved fur locks
    (a sharp, leaning crest). width/height scaled by taper(t); prof = [(u across -1..1, height fraction)], the edges
    sunk below the surface; the ends closed with a point (closed=True: a loop, ctrl already sampled)"""
    path = resample(ctrl, step, True) if closed else cr_open(ctrl, step)
    taper = (lambda t: 1.0) if closed else (taper or (lambda t: math.sin(math.pi * t) ** 0.6))
    prof = prof or [(-1, None), (-0.55, 0.75), (0, 1.0), (0.55, 0.75), (1, None)]
    n = len(path)
    verts, faces = [], []
    m = len(prof)
    for i, (x, z) in enumerate(path):
        t = i / (n - 1)
        if closed:
            a = Vector(path[i - 1]); b = Vector(path[(i + 1) % n])
        else:
            a = Vector(path[max(i - 1, 0)]); b = Vector(path[min(i + 1, n - 1)])
        d = (b - a).normalized()
        side = Vector((-d.y, d.x))
        k = max(taper(t), 0.0)
        w = width * 0.5 * k
        for u, hf in prof:
            q = Vector((x, z)) + side * (u * w)
            verts.append(P(q.x, q.y, -sink if hf is None else height * hf * k ** 0.5, F))
    for i in range(n if closed else n - 1):
        i2 = (i + 1) % n
        for j in range(m - 1):
            faces.append((i * m + j, i * m + j + 1, i2 * m + j + 1, i2 * m + j))
    for end, row, sgn in (() if closed else ((0, 0, -1), (1, n - 1, 1))):   # close each end with a point
        q0 = Vector(path[row]); q1 = Vector(path[row - sgn]) if 0 <= row - sgn < n else q0
        dd = (q0 - q1).normalized() if (q0 - q1).length > 1e-9 else Vector((1, 0))
        w = width * 0.5 * max(taper(end), 0.0)
        tip = q0 + dd * (w * cap + 0.001)
        verts.append(P(tip.x, tip.y, -sink, F))
        ti = len(verts) - 1
        for j in range(m - 1):
            a0, a1 = row * m + j, row * m + j + 1
            faces.append((a1, a0, ti) if sgn < 0 else (a0, a1, ti))
    ob = A.mesh_from(name, verts, faces, mat)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:   # outward (away from the head)
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    bm.to_mesh(ob.data); bm.free()
    return ob


FUR = [(-1, None), (0.35, 1.0), (1, None)]   # a carved lock: the crest leans to one side


def dome(name, x, z, r, h, F, mat, seg=12, prof=((0.0, 1.0), (0.45, 0.9), (0.75, 0.62), (0.95, 0.2)), sink=0.003,
         sx=1.0):
    """a small dome hugging F (rivets, paint dots, beads): rings of (radius fraction, height fraction)"""
    verts = [P(x, z, h, F)]
    rings = [p for p in prof if p[0] > 0] + [(1.0, None)]
    for rf, hf in rings:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append(P(x + r * rf * sx * math.cos(a), z + r * rf * math.sin(a), -sink if hf is None else h * hf, F))
    faces = [(0, 1 + k, 1 + (k + 1) % seg) for k in range(seg)]
    for i in range(len(rings) - 1):
        b0, b1 = 1 + i * seg, 1 + (i + 1) * seg
        for k in range(seg):
            faces.append((b0 + k, b1 + k, b1 + (k + 1) % seg, b0 + (k + 1) % seg))
    ob = A.mesh_from(name, verts, faces, mat)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    bm.to_mesh(ob.data); bm.free()
    return ob


BEAD = [(-1, None), (-0.62, 0.72), (0, 1.0), (0.62, 0.72), (1, None)]


def line(name, loop, off, r, F, mat, step=0.022, closed=True):
    """a fine half-round bead (gilt edge, iron rim) lying along a loop on F: r its half-width, standing r * 0.8 + off"""
    return strip(name, loop, 2 * r, 0.8 * r + off, F, mat, step=step, prof=BEAD, sink=0.002, closed=closed)


def band(name, mid, width, prof, mat, step=0.03):
    """a moulded band along a closed loop `mid`: a cross-section of (u across -1 outer .. 1 inner, radius function
    r(x, z)) swept round it as clean quads (frames, rims)"""
    path = resample(ccw(list(mid)), step, True)
    n, m = len(path), len(prof)
    verts, faces = [], []
    for i, (x, z) in enumerate(path):
        d = (Vector(path[(i + 1) % n]) - Vector(path[i - 1])).normalized()
        inward = Vector((-d.y, d.x))    # left of a counter-clockwise loop
        for u, rf in prof:
            q = Vector((x, z)) + inward * (u * width * 0.5)
            ang = q.x / HEAD_R
            r = rf(q.x, q.y)
            verts.append((r * math.sin(ang), -r * math.cos(ang), q.y))
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(m - 1):
            faces.append((i * m + j, i2 * m + j, i2 * m + j + 1, i * m + j + 1))
    ob = A.mesh_from(name, verts, faces, mat)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    up = [f for f in bm.faces if abs(f.normal.z) < 0.9]
    if up:   # face away from the head
        f = max(bm.faces, key=lambda f: Vector((f.calc_center_median().x, f.calc_center_median().y, 0)).length)
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            for f in bm.faces:
                f.normal_flip()
    bm.to_mesh(ob.data); bm.free()
    return ob


def clip_to(path, ok):
    """keep a fur lock's control points while they stay in the allowed region"""
    out = []
    for p in path:
        if not ok(p):
            break
        out.append(p)
    return out


def nose(name, c, n, size, mat, seg=18, rings=11):
    """a sculpted animal nose: a rounded wedge facing along n, a groove down the middle and two nostrils"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    sx_, sy_, sz_ = size
    for v in bm.verts:
        x, y, z = v.co   # local: x across, -y forward (along n), z up
        fwd = max(0.0, -y)
        z2 = z * (1 - 0.25 * max(0.0, z))                      # flatter top
        x2 = x * (1 + 0.15 * max(0.0, -z))                     # wider at the nostrils
        dent = 0.0
        dent += 0.20 * g(x, 0, 0.16) * smooth(0.1, -0.6, z) * fwd                 # the groove
        for s in (-1, 1):
            dent += 0.28 * g(x, s * 0.42, 0.17) * g(z, -0.28, 0.2) * fwd          # nostrils
        r = Vector((x2, y, z2)) * (1 - dent)
        v.co = (r.x * sx_, r.y * sy_, r.z * sz_)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = A._new_obj(name, me)
    q = Vector((0, -1, 0)).rotation_difference(n)
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = q
    ob.location = c
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    smooth_shade(ob)
    return A._finish(ob, mat)


# ================================================================ renders: three close-ups on the mannequin
def closeups(key, tz=1.6, detail=None):
    """three-quarter, front, side and low close-ups on the standard mannequin (+ an optional detail shot)"""
    def r(objs, cam, man):
        out = os.path.join(A.OUT, "renders")
        A.shoot(cam, os.path.join(out, f"{key}_c34.png"), (2.2, -3.3, tz + 0.4), target=(0.05, -0.45, tz + 0.02), lens=58, aspect=1.0)
        A.shoot(cam, os.path.join(out, f"{key}_cfront.png"), (0, -4.0, tz + 0.08), target=(0, -0.5, tz), lens=58, aspect=1.0)
        A.shoot(cam, os.path.join(out, f"{key}_cside.png"), (3.9, -0.55, tz + 0.08), target=(0, -0.5, tz), lens=58, aspect=1.0)
        A.shoot(cam, os.path.join(out, f"{key}_clow.png"), (1.4, -3.4, tz - 0.7), target=(0, -0.5, tz - 0.1), lens=58, aspect=1.0)
        if detail:
            A.shoot(cam, os.path.join(out, f"{key}_cdetail.png"), detail[0], target=detail[1], lens=detail[2], aspect=1.0)
    return r


def eye_hole(cx, cz, w, h, tilt, n=28):
    return ccw(almond(cx, cz, w, h, tilt, n))


# ================================================================ 1. the fox half-mask
FOX_D = 0.026


def fox_sculpt(x, z):
    ax = abs(x)
    t = min(1.0, max(0.0, (1.665 - z) / 0.32))                # 0 at the stop between the eyes, 1 at the nose
    mw = 0.112 - 0.050 * t
    muzzle = (0.010 + 0.150 * t ** 1.2) * math.exp(-(x / mw) ** 2) * (1 - 0.30 * smooth(1.385, 1.335, z))
    nosebulb = 0.020 * g(x, 0, 0.045) * g(z, 1.375, 0.03)
    brow = 0.016 * g(ax, 0.21, 0.10) * g(z, 1.68 + 0.18 * (ax - 0.2), 0.032)
    socket = -0.012 * g(ax, 0.205, 0.085) * g(z, 1.615 + 0.32 * (ax - 0.205), 0.035)
    fore = 0.008 * g(x, 0, 0.12) * g(z, 1.70, 0.05)
    cheek = 0.018 * g(ax, 0.33, 0.10) * g(z, 1.50, 0.07)
    edge = -0.006 * smooth(0.36, 0.44, ax)
    ear = -0.009 * smooth(1.72, 1.80, z)
    return muzzle + nosebulb + brow + socket + fore + cheek + edge + ear


def fox_back(x, z):
    return back_r(z)


def fox_F(x, z):
    return fox_back(x, z) + FOX_D + fox_sculpt(x, z)


# Hair-friendly (2026-11-12): every catalog hair with a fringe or side hair crosses anything over the brow line or past
# the temples, so the mask keeps inside |x| 0.44 and the ears are the mask's own upper corners, lying on the brow
# (tips z 1.85) rather than standing over the head.
FOX_HALF = [(0.0, 1.713), (0.05, 1.705), (0.105, 1.708),
            (0.155, 1.750), (0.212, 1.798), (0.272, 1.846),     # 5: the ear tip
            (0.31, 1.795), (0.345, 1.745), (0.385, 1.70), (0.418, 1.655), (0.432, 1.59), (0.436, 1.53),
            (0.442, 1.442),                  # 12: the outer cheek tuft (a tassel hangs here)
            (0.405, 1.468), (0.37, 1.46),
            (0.338, 1.398),                  # 15: the inner cheek tuft
            (0.29, 1.428), (0.22, 1.405), (0.15, 1.365), (0.075, 1.345), (0.0, 1.338)]
FOX_CORNERS = [5, 12, 15]
FOX_EYE = (0.205, 1.615, 0.094, 0.040, 0.32)


@item("FoxMask", "Fox half-mask", views=["front34", "front", "side"],
      close=((1.6, -3.5, 1.85), (0, -0.6, 1.65), 58), render=closeups("FoxMask"))
def build_fox(M):
    piece("FoxMask", "Head")
    lacquer = A.mat_flat("FoxLacquer", (0.010, 0.009, 0.011), rough=0.07, coat=1.0, noise=30, bump=0.004, vary=0.02,
                         wear=0.06, dirt=0.3)
    nosemat = A.mat_flat("FoxNose", (0.004, 0.004, 0.005), rough=0.04, coat=1.0, noise=30, bump=0.0, vary=0.0, wear=0.0)
    paint = A.mat_flat("FoxCrimson", (0.46, 0.022, 0.05), rough=0.16, coat=0.7, noise=60, bump=0.004, vary=0.05,
                       wear=0.05, dirt=0.2)
    gold = A.mat_metal("FoxGold", (1.0, 0.74, 0.32), rough=0.18, scratch=0.2, wear=0.2)
    silk = A.mat_cloth("FoxSilk", (0.34, 0.022, 0.045), weave=650, rough=0.45, sheen=0.6, bump=0.06, twill=False)
    outline = outline_loop(FOX_HALF, FOX_CORNERS, step=0.026)
    cx, cz, w, h, tl = FOX_EYE
    eyes = [eye_hole(sx * cx, cz, w, h, tl * sx) for sx in (-1, 1)]
    sh = shell("FoxShell", outline, FOX_D, lacquer, holes=eyes, sf=0.025, sb=0.08, bevel=0.007, seg=2,
               fine=lambda x, z: abs(x) < 0.16 and 1.33 < z < 1.67)
    wrap_r(sh, lambda x, z, t: fox_back(x, z) + t * (FOX_D + fox_sculpt(x, z)))
    # the gilt: a fine line just inside the edge and round both eyes
    line("FoxEdgeGilt", offset_poly(outline, 0.016), 0.0, 0.0048, fox_F, gold, step=0.03)
    for k, e in enumerate(eyes):
        line(f"FoxEyeGilt{k}", offset_poly(e, -0.009), 0.0, 0.0052, fox_F, gold, step=0.017)
    # the glossy nose on the muzzle tip
    nc = P(0, 1.372, -0.012, fox_F)
    nose("FoxNoseTip", nc, N(0, 1.40, fox_F).lerp(Vector((0, -1, 0)), 0.5).normalized(), (0.040, 0.030, 0.026), nosemat)
    for sx in (-1, 1):
        # the inner ear: a crimson lacquer inlay edged in gold
        ear = cr_open([(0.180, 1.728), (0.222, 1.762), (0.267, 1.800)], 0.012)[:-1]
        ear += cr_open([(0.267, 1.800), (0.295, 1.764), (0.323, 1.728)], 0.012)[:-1]
        ear += cr_open([(0.323, 1.728), (0.29, 1.719), (0.232, 1.719), (0.180, 1.728)], 0.02)[:-1]
        ear = ccw([(sx * x, z) for x, z in ear])
        layer(f"FoxInnerEar{sx}", ear, fox_F, -0.002, 0.003, paint, sf=0.032, bevel=0.0015)
        # the eye liner: from the inner corner over the lid, flicked up past the outer corner toward the temple
        lid = []
        for i in range(9):
            u = i / 8
            lx = sx * w * (-math.cos(math.pi * (0.06 + 0.9 * u)))
            q = lx / w
            lid.append((sx * cx + lx, cz + h * math.sqrt(max(0.0, 1 - q * q)) * (1 - 0.35 * q * q) + tl * sx * lx + 0.030 + 0.008 * u))
        lid += [(sx * (cx + w + 0.023), cz + tl * w + 0.040), (sx * (cx + w + 0.046), cz + tl * w + 0.067)]
        strip(f"FoxLiner{sx}", lid, 0.026, 0.0035, fox_F, paint, step=0.012,
              taper=lambda t: (0.35 + 0.65 * smooth(0.0, 0.35, t)) * (1 - smooth(0.62, 1.0, t)) + 0.02)
        under = [(sx * (cx + 0.01), cz - h - 0.034), (sx * (cx + 0.065), cz - h - 0.022), (sx * (cx + w + 0.03), cz + tl * w - 0.006),
                 (sx * (cx + w + 0.063), cz + tl * w + 0.035)]
        strip(f"FoxUnder{sx}", under, 0.017, 0.003, fox_F, paint, step=0.012,
              taper=lambda t: math.sin(math.pi * min(1.0, 0.15 + 0.85 * t)) ** 0.7 * (1 - 0.5 * t) + 0.02)
        # strokes down the muzzle from the inner corner of the eye
        strip(f"FoxMuzzleStroke{sx}", [(sx * 0.098, 1.585), (sx * 0.092, 1.535), (sx * 0.082, 1.475), (sx * 0.064, 1.42),
                                        (sx * 0.044, 1.39)], 0.020, 0.003, fox_F, paint, step=0.012,
              taper=lambda t: (0.5 + 0.5 * math.sin(math.pi * min(1, t * 1.4))) * (1 - smooth(0.7, 1.0, t)) + 0.02)
        # the side tongues of the brow flame
        strip(f"FoxFlame{sx}", [(sx * 0.020, 1.672), (sx * 0.048, 1.684), (sx * 0.080, 1.689), (sx * 0.112, 1.692)],
              0.020, 0.003, fox_F, paint, step=0.012, taper=lambda t: (1 - t) ** 0.8 * (0.6 + 0.4 * math.sin(math.pi * t)) + 0.02)
        # whisker dots on the muzzle
        for k, (dx, dz) in enumerate(((0.118, 1.462), (0.142, 1.488), (0.150, 1.440))):
            dome(f"FoxDot{sx}{k}", sx * dx, dz, 0.0105, 0.0035, fox_F, paint, seg=9, prof=((0, 1.0), (0.6, 0.8)))
        # the tassel: a gold eyelet on the tip of the outer cheek tuft, a silk cord, gold bead, knot, gold collar, skirt
        tx, tz = 0.418, 1.458
        dome(f"FoxEyelet{sx}", sx * tx, tz, 0.018, 0.008, fox_F, gold, seg=12, prof=((0, 1.0), (0.5, 0.85), (0.85, 0.4)))
        top = P(sx * tx, tz - 0.012, 0.016, fox_F)
        tassel(f"FoxTassel{sx}", top, gold, silk)
    # the centre tongue of the flame, over a gold bead
    strip("FoxFlame0", [(0.0, 1.668), (0.005, 1.679), (-0.003, 1.689), (0.002, 1.697)], 0.026, 0.0035, fox_F, paint,
          step=0.012, taper=lambda t: (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.8))) * (1 - t) ** 0.7 + 0.02)
    dome("FoxJewel", 0.0, 1.655, 0.015, 0.011, fox_F, gold, seg=14)
    return {"notes": "Kit C2"}


def tassel(name, top, gold, silk):
    """hangs straight down from top: a silk cord, gold bead, silk knot, gold collar and a fluted silk skirt"""
    top = Vector(top)
    A.tube(f"{name}Cord", [tuple(top), tuple(top + Vector((0, 0, -0.05)))], 0.0065, silk, res=8, poly=True)
    A.sphere(f"{name}Bead", 0.016, tuple(top + Vector((0, 0, -0.056))), gold, seg=12, rings=7)
    A.sphere(f"{name}Knot", 0.019, tuple(top + Vector((0, 0, -0.087))), silk, scale=(1, 1, 0.85), seg=12, rings=7)
    A.lathe(f"{name}Collar", [(0.0, 0.0), (0.017, 0.0), (0.0195, 0.004), (0.0195, 0.014), (0.017, 0.018), (0.0, 0.018)],
            tuple(top + Vector((0, 0, -0.124))), gold, seg=16)
    # the skirt: fluted (each flute a bundle of threads), flaring, the strand ends uneven
    K, J, L = 20, 7, 0.150
    verts, faces = [], []
    for j in range(J + 1):
        v = j / J
        R = 0.0165 + 0.012 * v ** 0.8
        for k in range(K):
            a = 2 * math.pi * k / K
            r = R * (1.0 if k % 2 == 0 else 0.86)
            zz = -L * v - (0.010 * ((k * 7) % 5) / 4 if j == J else 0.0)
            verts.append(top + Vector((r * math.cos(a), r * math.sin(a), -0.122 + zz)))
    for j in range(J):
        for k in range(K):
            a, b = j * K + k, j * K + (k + 1) % K
            faces.append((a, b, b + K, a + K))
    verts.append(top + Vector((0, 0, -0.122)))
    c0 = len(verts) - 1
    faces += [(c0, (k + 1) % K, k) for k in range(K)]
    verts.append(top + Vector((0, 0, -0.122 - L + 0.02)))
    c1 = len(verts) - 1
    faces += [(J * K + k, J * K + (k + 1) % K, c1) for k in range(K)]
    sk = A.mesh_from(f"{name}Skirt", [tuple(v) for v in verts], faces, silk)
    bm = bmesh.new(); bm.from_mesh(sk.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(sk.data); bm.free()


# ================================================================ 2. the wolf half-mask
WOLF_D = 0.022
WOLF_EYE = (0.212, 1.606, 0.096, 0.040, 0.36)


def wolf_brow_z(ax):
    """the brow line: just over the eye, slanting down hard to the inner corner (the frown)"""
    cx, cz, w, h, tl = WOLF_EYE
    return cz + 0.55 * h + tl * (ax - cx) + 0.036


def wolf_mw(z):
    t = min(1.0, max(0.0, (1.645 - z) / 0.30))
    return 0.143 - 0.032 * t, t


def wolf_sculpt(x, z):
    ax = abs(x)
    mw, t = wolf_mw(z)
    muzzle = (0.022 + 0.175 * t ** 1.05) * math.exp(-(x / mw) ** 4) * (1 - 0.28 * smooth(1.39, 1.335, z))
    bridge = 0.010 * g(x, 0, 0.035) * (1 - smooth(1.62, 1.66, z)) * smooth(1.36, 1.45, z)
    stop = -0.016 * g(x, 0, 0.05) * g(z, 1.652, 0.03)
    db = z - wolf_brow_z(ax)
    # the brow ridge and cheeks stay low (hair lies over them at r 0.66 .. 0.70): the frown is carved in, a deep
    # socket under a sharp-edged ridge, rather than built out
    brow = 0.026 * smooth(0.03, 0.12, ax) * (1 - smooth(0.34, 0.44, ax)) * \
        (math.exp(-(db / 0.050) ** 2) if db > 0 else math.exp(-(db / 0.016) ** 2))
    furrow = -0.008 * g(ax, 0.045, 0.018) * g(z, 1.69, 0.04)        # two frown furrows between the brows
    socket = -0.013 * g(ax, 0.215, 0.09) * g(z, 1.60 + 0.3 * (ax - 0.215), 0.04)
    fore = 0.006 * g(x, 0, 0.14) * g(z, 1.70, 0.04)
    cheek = 0.020 * g(ax, 0.30, 0.11) * g(z, 1.48, 0.075)
    edge = -0.006 * smooth(0.37, 0.45, ax)
    ear = -0.008 * smooth(1.72, 1.80, z)
    return muzzle + bridge + stop + brow + furrow + socket + fore + cheek + edge + ear


def wolf_back(x, z):
    return back_r(z)


def wolf_F(x, z):
    return wolf_back(x, z) + WOLF_D + wolf_sculpt(x, z)


# Hair-friendly (2026-11-12): inside |x| 0.45 and under the brow line, the ears the mask's own upper corners lying on
# the brow (tips z 1.85), the ruff a row of short jagged tufts down the cheek edge.
WOLF_HALF = [(0.0, 1.712), (0.05, 1.704), (0.10, 1.708), (0.15, 1.752), (0.205, 1.80), (0.262, 1.852),
             (0.30, 1.80), (0.338, 1.752), (0.375, 1.712),
             (0.400, 1.69), (0.430, 1.668),           # 10: upper ruff tuft
             (0.400, 1.625), (0.432, 1.565),          # 12: middle tuft
             (0.398, 1.535), (0.428, 1.462),          # 14: lower tuft
             (0.385, 1.448), (0.392, 1.372),          # 16: jaw tuft
             (0.36, 1.40), (0.30, 1.405), (0.24, 1.39), (0.17, 1.36), (0.085, 1.338), (0.0, 1.330)]
WOLF_CORNERS = [5, 10, 11, 12, 13, 14, 15, 16]


def wolf_flow(x, z):
    """the way the carved fur lies (x >= 0): fanned up and out over the brow to the ears, out across the temples
    and cheeks to the ruff"""
    db = z - wolf_brow_z(x)
    if abs(db) < 0.026 and 0.05 < x < 0.42 and z > 1.60:   # along the brow ridge, swept out and up to the ear
        v = Vector((1.0, 0.42 + 0.6 * smooth(0.0, 0.026, db)))
    elif db > -0.01 and z > 1.60:
        v = Vector((x * 1.5 + 0.015, z - 1.585))
        v = v.normalized().lerp(Vector((1.0, 0.2)).normalized(), smooth(0.36, 0.44, x))
    elif x < 0.17:
        v = Vector((0.3, -1.0))
    else:
        v = Vector((1.0, -0.30 - 1.2 * max(0.0, 1.53 - z)))
    return v.normalized()


def _h01(a, b):
    v = math.sin(a * 127.1 + b * 311.7) * 43758.5453
    return v - math.floor(v)


LOCK = [(-1, None), (0.3, 1.0), (1, None)]   # a carved lock: the crest leans to the trailing side


def fur(prefix, F, mat, ok, flow, region, box, sp=0.07, L=0.12, W=0.046, H=0.012, step=0.02):
    """carved fur locks seeded on a jittered hex grid over the +x half (mirrored), each traced along the flow and
    clipped where it would leave the allowed region; leaf shaped, blunt at the root, pointed at the tip"""
    x0, x1, z0, z1 = box
    j, z, n = 0, z0, 0
    while z < z1:
        x = x0 + (sp * 0.5 if j % 2 else 0.0)
        while x < x1:
            h1, h2 = _h01(x, z), _h01(z, x)
            px = max(0.0, x + (h1 - 0.5) * sp * 0.35)
            pz = z + (h2 - 0.5) * sp * 0.35
            if px < sp * 0.3:
                px = 0.0
            if region(px, pz) and ok((px, pz)):
                Lk = L * (0.85 + 0.3 * h1)
                for sx in ((1, -1) if px > 0 else (1,)):
                    p = Vector((px, pz))
                    pts = [(sx * p.x, p.y)]
                    for k in range(3):
                        p = p + flow(abs(p.x), p.y) * (Lk / 3)
                        p.x = max(p.x, 0.0) if px > 0 else p.x
                        pts.append((sx * p.x, p.y))
                    pts = clip_to(pts, ok)
                    if len(pts) >= 3:
                        strip(f"{prefix}{n}", pts, W * (0.9 + 0.2 * h2), H, F, mat, step=step,
                              prof=LOCK if sx > 0 else [(-1, None), (-0.3, 1.0), (1, None)],
                              taper=lambda t: math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5, cap=0.8)
                        n += 1
            x += sp
        z += sp * 0.866
        j += 1
    return n


@item("WolfMask", "Wolf half-mask", views=["front34", "front", "side"],
      close=((1.6, -3.5, 1.85), (0, -0.6, 1.65), 58), render=closeups("WolfMask"))
def build_wolf(M):
    piece("WolfMask", "Head")
    pewter = A.mat_metal("WolfSilver", (0.62, 0.63, 0.65), rough=0.40, scratch=0.7, wear=0.55, dirt=1.0,
                         tarnish=(0.15, 0.15, 0.16))
    dark = A.mat_metal("WolfIron", (0.075, 0.074, 0.08), rough=0.42, scratch=0.4, wear=0.4, dirt=0.6,
                       tarnish=(0.04, 0.04, 0.04))
    nosemat = A.mat_flat("WolfNose", (0.008, 0.008, 0.009), rough=0.10, coat=0.9, noise=90, bump=0.02, vary=0.02, wear=0.05)
    outline = outline_loop(WOLF_HALF, WOLF_CORNERS, step=0.026)
    cx, cz, w, h, tl = WOLF_EYE
    eyes = []
    for sx in (-1, 1):   # angry eyes: the top edge cut flat under the brow, slanting down to the inner corner
        e = []
        for i in range(28):
            a = 2 * math.pi * i / 28
            lx = w * math.cos(a)
            q = lx / w
            up = math.sin(a) > 0
            lz = (0.55 if up else 1.0) * h * math.sin(a) * (1 - 0.3 * q * q) + tl * lx - (0.012 * (1 - q) ** 2 if up else 0.0)
            e.append((sx * cx + sx * lx, cz + lz))
        eyes.append(ccw(e))
    sh = shell("WolfShell", outline, WOLF_D, pewter, holes=eyes, sf=0.029, sb=0.08, bevel=0.007, seg=2, fs=0.68,
               fine=lambda x, z: abs(x) < 0.20 and 1.33 < z < 1.67,
               extra=[(sx * x, wolf_brow_z(x) + db) for sx in (-1, 1) for x in [0.025 + 0.0125 * i for i in range(36)]
                      for db in (-0.048, -0.032, -0.02, -0.01, 0.0, 0.011, 0.024, 0.042, 0.064)])
    wrap_r(sh, lambda x, z, t: wolf_back(x, z) + t * (WOLF_D + wolf_sculpt(x, z)))
    for k, e in enumerate(eyes):   # blackened iron round each eye
        line(f"WolfEyeRim{k}", offset_poly(e, -0.011), 0.002, 0.0082, wolf_F, dark, step=0.014)
    nc = P(0, 1.37, -0.018, wolf_F)
    nose("WolfNoseTip", nc, N(0, 1.40, wolf_F).lerp(Vector((0, -1, 0)), 0.45).normalized(), (0.066, 0.046, 0.042), nosemat,
         seg=20, rings=12)
    inset = offset_poly(outline, 0.020)
    eyes_out = [offset_poly(e, -0.026) for e in eyes]

    def inner_ear(sx):
        ear = cr_open([(0.153, 1.722), (0.204, 1.766), (0.260, 1.816)], 0.011)[:-1]
        ear += cr_open([(0.260, 1.816), (0.297, 1.769), (0.336, 1.722)], 0.011)[:-1]
        ear += cr_open([(0.336, 1.722), (0.30, 1.711), (0.21, 1.711), (0.153, 1.722)], 0.02)[:-1]
        return ccw([(sx * x, z) for x, z in ear])
    ears_out = [offset_poly(inner_ear(sx), -0.014) for sx in (-1, 1)]

    def ok(p):   # fur stays on the mask, clear of the edge, the eyes and the inner ears
        return inside(p, inset) and not any(inside(p, e) for e in eyes_out + ears_out)

    def region(x, z):   # the muzzle and the brow ridge stay smooth
        mw, t = wolf_mw(z)
        if x < mw * 0.95 and z < 1.665:
            return False
        return True

    fur("WolfFur", wolf_F, pewter, ok, wolf_flow, region, (0.0, 0.46, 1.36, 1.80), sp=0.036, L=0.078, W=0.032, H=0.0068)
    for sx in (-1, 1):
        # the inner ear: blackened iron, fur locks rising from its base
        ear = inner_ear(sx)
        layer(f"WolfInnerEar{sx}", ear, wolf_F, -0.002, 0.003, dark, sf=0.024, bevel=0.0012)
        efF = lambda x, z: wolf_F(x, z) + 0.002
        for k, c in enumerate(([(0.200, 1.720), (0.213, 1.746), (0.229, 1.774)], [(0.246, 1.716), (0.250, 1.748), (0.254, 1.788)],
                               [(0.297, 1.718), (0.288, 1.744), (0.274, 1.772)])):
            strip(f"WolfEarFur{sx}{k}", [(sx * x, z) for x, z in c], 0.026, 0.006, efF, pewter, step=0.012,
                  prof=LOCK if sx > 0 else [(-1, None), (-0.3, 1.0), (1, None)],
                  taper=lambda t: math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5, cap=0.8)
        # the ear's edges: a lock up each side of the ear from the brow
        for k, c in enumerate(([(0.372, 1.676), (0.362, 1.704), (0.345, 1.732)], [(0.112, 1.690), (0.128, 1.712), (0.15, 1.734)])):
            cc = clip_to([(sx * x, z) for x, z in c], lambda p: inside(p, inset))
            if len(cc) >= 3:
                strip(f"WolfEarEdge{sx}{k}", cc, 0.030, 0.0075, wolf_F, pewter, step=0.014,
                      prof=LOCK if sx > 0 else [(-1, None), (-0.3, 1.0), (1, None)],
                      taper=lambda t: math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5, cap=0.8)
    return {"notes": "Kit C2"}


# ================================================================ 3. the iron grille mask
GR_D = 0.022
GR_HALF = [(0.0, 1.548), (0.07, 1.535), (0.15, 1.495), (0.25, 1.468), (0.37, 1.462), (0.48, 1.47), (0.565, 1.475),
           (0.61, 1.44), (0.625, 1.33), (0.615, 1.20), (0.565, 1.105), (0.46, 1.055), (0.32, 1.032), (0.16, 1.022), (0.0, 1.02)]


def grille_sculpt(x, z):
    ax = abs(x)
    bulge = 0.065 * g(x, 0, 0.30) * g(z, 1.27, 0.22)
    bridge = 0.035 * g(x, 0, 0.07) * g(z, 1.50, 0.07)
    chin = 0.02 * g(x, 0, 0.2) * g(z, 1.08, 0.07)
    edge = -0.006 * smooth(0.5, 0.63, ax)
    return bulge + bridge + chin + edge


def gr_back(x, z):
    return back_r(z)


def gr_F(x, z):   # the backing's front
    return gr_back(x, z) + GR_D + grille_sculpt(x, z)


def span_z(loop, x):
    """the z range of a closed loop along the vertical line at x"""
    zs = []
    for i in range(len(loop)):
        (x0, z0), (x1, z1) = loop[i - 1], loop[i]
        if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
            zs.append(lerp(z0, z1, (x - x0) / (x1 - x0)))
    return min(zs), max(zs)


def span_x(loop, z, sx):
    """where a closed loop crosses the horizontal line at z, on the sx side"""
    xs = []
    for i in range(len(loop)):
        (x0, z0), (x1, z1) = loop[i - 1], loop[i]
        if (z0 - z) * (z1 - z) <= 0 and z0 != z1:
            xs.append(lerp(x0, x1, (z - z0) / (z1 - z0)))
    return max(xs) if sx > 0 else min(xs)


@item("GrilleMask", "Iron grille mask", views=["front34", "front", "side"],
      close=((1.6, -3.5, 1.5), (0, -0.6, 1.3), 58),
      render=closeups("GrilleMask", tz=1.36, detail=((0.75, -2.3, 1.6), (0.0, -0.62, 1.42), 70)))
def build_grille(M):
    piece("GrilleMask", "Head")
    iron = A.mat_set("GrilleIron", "NH_Iron", tint=(0.085, 0.08, 0.085), scale=5.0, wear=0.25, wear_metal=True, dirt=0.8)
    backing = A.mat_leather("GrilleBacking", (0.11, 0.022, 0.03), scale=3.0, wear=0.35)
    brass = M["brass"]; brass_old = M["brassold"]
    enamel = A.mat_flat("GrilleEnamel", (0.36, 0.022, 0.045), rough=0.12, coat=0.8, noise=60, bump=0.005, vary=0.04, wear=0.05)
    outline = outline_loop(GR_HALF, (), step=0.028)
    sh = shell("GrilleBacking", offset_poly(outline, 0.005), GR_D, backing, sf=0.042, sb=0.08, bevel=0.004, seg=1)
    wrap_r(sh, lambda x, z, t: gr_back(x, z) + t * (GR_D + grille_sculpt(x, z)))
    BAND = 0.058
    window = offset_poly(outline, BAND)
    bandF = lambda x, z: gr_F(x, z) + 0.024
    band("GrilleFrame", offset_poly(outline, BAND / 2), BAND, [
        (-1.0, lambda x, z: gr_back(x, z) + 0.001), (-1.0, lambda x, z: gr_F(x, z) + 0.017),
        (-0.82, lambda x, z: gr_F(x, z) + 0.024), (0.82, lambda x, z: gr_F(x, z) + 0.024),
        (1.0, lambda x, z: gr_F(x, z) + 0.017), (1.0, lambda x, z: gr_F(x, z) - 0.003)], iron, step=0.026)
    # the bars: eleven bevelled iron slats from the frame's top edge to its bottom, tucked under it; the middle one
    # broader, with a raised spine down the prow
    xs = [0.084 * (k - 5) for k in range(11)]
    for k, xc in enumerate(xs):
        z0, z1 = span_z(window, xc)
        o0, o1 = span_z(outline, xc)
        hw = 0.026 if k == 5 else 0.018
        bar = [(xc - hw, max(z0 - 0.025, o0 + 0.012)), (xc + hw, max(z0 - 0.025, o0 + 0.012)),
               (xc + hw, min(z1 + 0.025, o1 - 0.012)), (xc - hw, min(z1 + 0.025, o1 - 0.012))]
        bar = resample(bar, 0.032)
        layer(f"GrilleBar{k}", bar, gr_F, -0.003, 0.020, iron, sf=0.032, bevel=0.006, seg=1)
    strip("GrilleSpine", [(0.0, z0 + 0.004), (0.0, (z0 + z1) / 2), (0.0, z1 - 0.004)], 0.014, 0.008,
          lambda x, z: gr_F(x, z) + 0.020, iron, step=0.03, prof=[(-1, None), (-0.45, 0.9), (0, 1.0), (0.45, 0.9), (1, None)],
          taper=lambda t: 1.0, cap=0.8)
    # the strap across the mouth, riveted to each bar and to the frame
    strapF = lambda x, z: gr_F(x, z) + 0.032
    zs = 1.262
    xa = 0.575
    strap = [(x, zs + 0.024 - 0.02 * (x / xa) ** 2) for x in [lerp(-xa, xa, i / 40) for i in range(41)]]
    strap += [(x, zs - 0.024 - 0.02 * (x / xa) ** 2) for x in [lerp(xa, -xa, i / 40) for i in range(41)]]
    layer("GrilleStrap", ccw(strap), gr_F, 0.012, 0.032, iron, sf=0.03, bevel=0.005, seg=1)
    RIV = ((0, 1.0), (0.55, 0.8), (0.85, 0.4))
    for k, xc in enumerate(xs + [-0.545, 0.545]):
        dome(f"StrapRivet{k}", xc, zs - 0.02 * (xc / xa) ** 2, 0.0125, 0.0095, strapF, brass_old, seg=9, prof=RIV)
    # rivets round the frame band
    mid = offset_poly(outline, BAND / 2)
    for k, (x, z) in enumerate(resample(mid, 0.078)):
        if abs(x) < 0.07 and z > 1.4:
            continue   # under the crest
        if abs(z - (zs - 0.02 * (x / xa) ** 2)) < 0.04 and abs(x) > 0.5:
            continue   # where the strap meets the frame
        dome(f"FrameRivet{k}", x, z, 0.0128, 0.0095, bandF, brass, seg=9, prof=RIV)
    # a hinged iron clasp at each side, riveted over the frame (the mask sits on the face; nothing goes round the head)
    for sx in (-1, 1):
        zc = 1.33
        xm = span_x(mid, zc, sx)
        plate = ccw([(xm + sx * 0.030 * math.cos(a), zc + 0.062 * math.sin(a) * (1 - 0.25 * math.cos(a) ** 2))
                     for a in [2 * math.pi * i / 22 for i in range(22)]])
        layer(f"Clasp{sx}", plate, gr_F, 0.018, 0.034, iron, sf=0.03, bevel=0.004, seg=1)
        for k, dz in enumerate((-0.036, 0.036)):
            dome(f"ClaspRivet{sx}{k}", xm, zc + dz, 0.011, 0.008, lambda x, z: gr_F(x, z) + 0.034, brass_old, seg=9, prof=RIV)
        q0, q1 = P(xm + sx * 0.028, zc - 0.058, 0.026, gr_F), P(xm + sx * 0.028, zc + 0.058, 0.026, gr_F)
        A.tube(f"ClaspPin{sx}", [tuple(q0), tuple(q1)], 0.0085, iron, res=8, poly=True)
        for k, dz in enumerate((-0.064, 0.064)):
            A.sphere(f"ClaspPinHead{sx}{k}", 0.010, tuple(P(xm + sx * 0.028, zc + dz, 0.026, gr_F)), brass, seg=10, rings=6)
    # the crest: a brass shield on the nose bridge, a crimson enamel field, a brass rose
    sz0 = 1.468
    shield_half = [(0.0, sz0 + 0.072), (0.03, sz0 + 0.062), (0.052, sz0 + 0.072), (0.056, sz0 + 0.02), (0.046, sz0 - 0.025),
                   (0.024, sz0 - 0.058), (0.0, sz0 - 0.075)]
    shield = outline_loop(shield_half, [2, 3, 6], step=0.012)
    field = offset_poly(shield, 0.0095)
    layer("Crest", shield, gr_F, 0.012, 0.040, brass, holes=[field], sf=0.012, bevel=0.0025, seg=2)
    layer("CrestField", field, gr_F, 0.012, 0.0335, enamel, sf=0.01, bevel=0.0012)
    rose = lambda x, z: gr_F(x, z) + 0.0335
    for k in range(5):
        a = 2 * math.pi * k / 5 + HP
        dome(f"RosePetal{k}", 0.0 + 0.0125 * math.cos(a), sz0 + 0.004 + 0.0125 * math.sin(a), 0.0115, 0.0055, rose, brass, seg=10)
    dome("RoseHeart", 0.0, sz0 + 0.004, 0.0085, 0.010, rose, brass_old, seg=10)
    return {"notes": "Kit C2"}


if "--quick" in A.argv:   # iterate on the close-ups only
    for _k in KEYS:
        A.ITEMS[_k]["views"] = ["close"]
    A.FEMALE_TOO = False

if "--parts" in A.argv:   # print the triangles each part costs (with --norender for a fast budget check)
    _join = A.join_pieces

    def _report():
        import re
        tot = {}
        for ob in A.PARTS:
            dg = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            t = sum(len(p.vertices) - 2 for p in dg.data.polygons)
            k = re.sub(r"[-\d]+$", "", ob.name)
            tot[k] = tot.get(k, 0) + t
        for k, t in sorted(tot.items(), key=lambda kv: -kv[1]):
            print(f"[parts] {k:24s} {t}")
        return _join()
    A.join_pieces = _report


if __name__ == "__main__":
    targets = [a for a in A.argv if not a.startswith("--") and (A.argv.index(a) == 0 or not A.argv[A.argv.index(a) - 1].startswith("--"))]
    keys = targets[0].split(",") if targets else KEYS
    for k in keys:
        try:
            A.run(k)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[kitc] {k} FAILED: {e}")
