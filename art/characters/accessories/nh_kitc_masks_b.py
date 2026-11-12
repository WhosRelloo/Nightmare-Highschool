"""Kit C, batch C2: three Head masks at the shipping standard of nh_kitc_hq.py (owner: "HIGH QUALITY WORK ONLY" and
"Make the boots look wayyy cooler and better. Wayy higher quality. Same with any masks"). Unisex, no ties or straps
(they would pass through every hairstyle): each mask holds on by sitting on the face.

  WaxMask    - Wax saint mask: a serene saint's face cast in warm ivory candle wax, brow to chin (the brow edge just
               over the brows, the sides short of the temples). Closed, downcast eyes carved as lids with see-through
               slits, a long straight nose, closed lips. The wax has run: a rolled, lumpy rim along the brow edge with
               drips running down onto the brows, the jaw edge sagging into drip tongues with pooled beads hanging just
               off it. A faint gilt halo-line arcs over the eyes and a small gilt cross pattee sits between the brows;
               wax runs over the gilt.
  MothMask   - Moth mask: a domino band over the eyes whose two halves are velvet moth wings (dusty black-violet),
               falcate forewing tips at the brows' outer ends and rounded hindwing lobes over the cheekbones. Each eye
               hole is the wing's discal cell: a raised vein loop rims it and veins radiate to the margin. Crimson and
               bone eye-spots on the fore- and hindwings, a crimson submarginal band and a bone dash line. A small
               furry moth body down the nose bridge (banded
               crimson/black abdomen, a fur-tufted thorax with a bone collar, glossy compound eyes) and two feathered
               (bipectinate) antennae that rise from its head and curl forward and out, standing clear in front of
               the brow (over the head they crossed nearly every hairstyle; now the mask keeps inside |x| 0.45 and
               under z 1.73, the antennae in front of any fringe).
  DominoMask - Black silk domino: the classic eye mask flush to the face, black silk with a sheen, upswept outer tips,
               almond eye holes, crimson satin piping rolled over every edge and a fine gold thread line inset from
               the outer edge. Compact and close: the most hair-friendly mask.

All three are modelled flat (x across, z up) and bent round the R6 head. Unlike nh_kitc_hq's wrap_sculpt, the back of
each shell keeps an even OFF gap from the head's real surface (the face cylinder and its rounded top and bottom edges,
Rz(z)), and only the front takes the sculpt, so the back never lifts off the face or sinks into it. The shells are
Delaunay-triangulated (an even, adaptive triangle size on the front, coarse on the hidden back) with a rolled front
edge, which keeps each mask well under the 12k-triangle mesh limit.

cd E:/Nightmare-Highschool/art/characters/accessories
E:/Blender/blender.exe -b --factory-startup -P nh_kitc_masks_b.py -- WaxMask --nobake --out E:/NH-Work/kitc_masks_b --res 700
"""
import math, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
import nh_acc as A
sys.modules.setdefault("nh_acc", A)
from nh_acc import item, piece, smooth, lerp
from nh_acc_batch1 import ccw, offset_poly
from nh_kitc_hq import g, HEAD_R, almond

HP = math.pi / 2
OFF = 0.009      # the even gap between a mask's back and the head
HEAD_RAD = 0.6   # the mannequin head: a cylinder r 0.6, z 0.9 .. 2.1, its top and bottom edges rounded r 0.25


# ================================================================== the head and the face surface
def Rz(z):
    """the head's radius at height z (the face cylinder, rounding in at the top and bottom edges)"""
    if 1.15 <= z <= 1.85:
        return HEAD_RAD
    d = min(0.25, (z - 1.85) if z > 1.85 else (1.15 - z))
    return 0.35 + math.sqrt(max(0.0, 0.0625 - d * d))


def head_sdf(p):
    """signed distance from the head (the rounded cylinder): < 0 inside"""
    qx = math.hypot(p.x, p.y) - 0.35
    qz = abs(p.z - 1.5) - 0.35
    return math.hypot(max(qx, 0.0), max(qz, 0.0)) + min(max(qx, qz), 0.0) - 0.25


def head_normal(p):
    h = 0.002
    return Vector(((head_sdf(p + Vector((h, 0, 0))) - head_sdf(p - Vector((h, 0, 0)))),
                   (head_sdf(p + Vector((0, h, 0))) - head_sdf(p - Vector((0, h, 0)))),
                   (head_sdf(p + Vector((0, 0, h))) - head_sdf(p - Vector((0, 0, h)))))).normalized()


def head_point(ang, z, clear):
    """the point `clear` off the head surface at azimuth ang (0 = straight ahead, + toward the character's left), height z"""
    if z <= 1.85:
        r = HEAD_RAD + clear
    else:
        R = 0.25 + clear
        dz = min(z - 1.85, R * 0.999)
        r = 0.35 + math.sqrt(R * R - dz * dz)
    return Vector((r * math.sin(ang), -r * math.cos(ang), z))


class Face:
    """a mask's front surface: the head's surface + OFF + the shell's depth + sculpt(x, z), x as arc length round it"""
    def __init__(self, sculpt, depth):
        self.s, self.d = sculpt, depth

    def r(self, x, z, lift=0.0):
        return Rz(z) + OFF + self.d + self.s(x, z) + lift

    def p(self, x, z, lift=0.0):
        a = x / HEAD_R
        r = self.r(x, z, lift)
        return Vector((r * math.sin(a), -r * math.cos(a), z))

    def frac(self, x, z, f):
        """a point at fraction f through the shell's thickness (0 the back, 1 the front)"""
        a = x / HEAD_R
        r = Rz(z) + OFF + (self.d + self.s(x, z)) * f
        return Vector((r * math.sin(a), -r * math.cos(a), z))

    def n(self, x, z):
        h = 0.002
        dx = self.p(x + h, z) - self.p(x - h, z)
        dz = self.p(x, z + h) - self.p(x, z - h)
        return dx.cross(dz).normalized()


# ================================================================== 2D outlines
def catmull(ctrl, n=10, closed=True):
    P = [Vector(c) for c in ctrl]
    m = len(P)
    out = []
    for i in range(m if closed else m - 1):
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]
        p1, p2 = P[i], P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            q = 0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)
            out.append((q.x, q.y))
    if not closed:
        out.append(tuple(P[-1]))
    return out


def resample(pts, step, closed=True):
    P = [Vector(p) for p in pts]
    if closed:
        P = P + [P[0]]
    L = [0.0]
    for a, b in zip(P, P[1:]):
        L.append(L[-1] + (b - a).length)
    total = L[-1]
    n = max(3, int(round(total / step)))
    out, j = [], 0
    for i in range(n if closed else n + 1):
        s = total * i / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = L[j + 1] - L[j]
        q = P[j].lerp(P[j + 1], min(1.0, (s - L[j]) / seg) if seg > 0 else 0.0)
        out.append((q.x, q.y))
    return out


def mirrored(half):
    """a symmetric closed outline from its +x half (from the top centre round to the bottom centre, both on x 0)"""
    return half + [(-x, z) for x, z in reversed(half[1:-1])]


def edge_z(loop, x):
    """(lowest, highest) z where the closed outline crosses the vertical line at x"""
    zs = []
    n = len(loop)
    for i in range(n):
        (x0, z0), (x1, z1) = loop[i], loop[(i + 1) % n]
        if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
            zs.append(z0 + (z1 - z0) * (x - x0) / (x1 - x0))
    return min(zs), max(zs)


def run_where(loop, pred):
    """the longest contiguous run of a closed loop's points satisfying pred (wrapping round the start)"""
    n = len(loop)
    ok = [pred(*p) for p in loop]
    if all(ok):
        return list(loop)
    start = ok.index(False)
    best, cur = [], []
    for k in range(1, n + 1):
        i = (start + k) % n
        if ok[i]:
            cur.append(loop[i])
        else:
            if len(cur) > len(best):
                best = cur
            cur = []
    if len(cur) > len(best):
        best = cur
    return best


# ================================================================== geometry
def _interior(outline, holes, sp, bpts):
    """interior vertices on a hex lattice, thinned so each keeps ~sp(x, z) from its neighbours and the boundary"""
    xs = [p[0] for p in outline]; zs = [p[1] for p in outline]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    smin = min(sp(lerp(x0, x1, i / 10), lerp(z0, z1, j / 10)) for i in range(11) for j in range(11))
    cell = smin
    grid = {}

    def add(p):
        grid.setdefault((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell))), []).append(p)
    for p in bpts:
        add(p)
    out = []
    c = smin * 0.5
    row, z = 0, z0 + c * 0.5
    while z < z1:
        x = x0 + (c * 0.5 if row % 2 else 0.0)
        while x < x1:
            s = sp(x, z)
            rr = 0.86 * s
            k = int(math.ceil(rr / cell))
            gx, gz = int(math.floor(x / cell)), int(math.floor(z / cell))
            ok = True
            for i in range(gx - k, gx + k + 1):
                for j in range(gz - k, gz + k + 1):
                    for q in grid.get((i, j), ()):
                        if (q[0] - x) ** 2 + (q[1] - z) ** 2 < rr * rr:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok and A._inside((x, z), outline) and not any(A._inside((x, z), h) for h in holes):
                out.append((x, z)); add((x, z))
            x += c
        z += c * 0.866
        row += 1
    return out


def shell(name, outline, holes, depth, mat, spacing, back=0.08, bevel=0.0, segments=3):
    """a flat plate in (x, z) of real thickness: the back at y 0, the front at y -depth. Each cap is a constrained
    Delaunay triangulation of the boundary plus interior points (front: local size spacing(x, z); back, hidden against
    the head: coarse), joined by the side wall. bevel rolls the front edge only (the back edge sits on the face)."""
    sp = spacing if callable(spacing) else (lambda x, z, s=spacing: s)
    loops = [list(outline)] + [list(h) for h in holes]
    bpts = [p for L in loops for p in L]
    nb = len(bpts)
    cons, b = [], 0
    for L in loops:
        cons += [(b + i, b + (i + 1) % len(L)) for i in range(len(L))]
        b += len(L)
    bm = bmesh.new()
    FB = [bm.verts.new((x, -depth, z)) for x, z in bpts]
    BB = [bm.verts.new((x, 0.0, z)) for x, z in bpts]
    for side, s, y, ring in (("f", sp, -depth, FB), ("b", (lambda x, z: back), 0.0, BB)):
        pts = bpts + _interior(outline, holes, s, bpts)
        vo, eo, fo, ov, oe, of = delaunay_2d_cdt([Vector(p) for p in pts], cons, [], 0, 1e-9)
        vm = {}
        for f in fo:
            cx = sum(vo[i].x for i in f) / len(f); cz = sum(vo[i].y for i in f) / len(f)
            if not A._inside((cx, cz), outline) or any(A._inside((cx, cz), h) for h in holes):
                continue
            vs = []
            for i in f:
                if i not in vm:
                    bi = next((o for o in ov[i] if o < nb), None)
                    vm[i] = ring[bi] if bi is not None else bm.verts.new((vo[i].x, y, vo[i].y))
                vs.append(vm[i])
            area = sum(vo[f[k]].x * vo[f[(k + 1) % len(f)]].y - vo[f[(k + 1) % len(f)]].x * vo[f[k]].y for k in range(len(f)))
            if (area > 0) != (side == "f"):
                vs = vs[::-1]
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
    b = 0
    lay = bm.edges.layers.float.new("bevel_weight_edge")
    for L in loops:
        n = len(L)
        for i in range(n):
            j = (i + 1) % n
            try:
                bm.faces.new((FB[b + i], FB[b + j], BB[b + j], BB[b + i]))
            except ValueError:
                pass
            e = bm.edges.get((FB[b + i], FB[b + j]))
            if e is not None:
                e[lay] = 1.0
        b += n
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = A._new_obj(name, me)
    for p in ob.data.polygons:
        p.use_smooth = True
    A._finish(ob, mat)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel; md.segments = segments; md.limit_method = "WEIGHT"; md.harden_normals = False
    return ob


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)


def wrap_fit(ob, sculpt, depth, base=0.0, full=False):
    """bend a flat shell (y 0 back .. -depth front) round the head: the back OFF + base off the head's real surface,
    the front taking sculpt(x, z) (full=True: the whole shell rides on the sculpt, for decals lying on a front)"""
    apply_mods(ob)
    me = ob.data
    mw = ob.matrix_world
    inv = mw.inverted()
    for v in me.vertices:
        co = mw @ v.co
        t = 1.0 if full else min(1.0, max(0.0, -co.y / depth))
        r = Rz(co.z) + OFF + base - co.y + sculpt(co.x, co.z) * t
        a = co.x / HEAD_R
        v.co = inv @ Vector((r * math.sin(a), -r * math.cos(a), co.z))
    me.update()
    return ob


def decal(name, pts, F, thick, mat, lift=0.0, spacing=0.012, bevel=0.0012, holes=(), segments=2):
    """a thin raised inlay (paint, gilt, a marking) lying on the front surface F"""
    ob = shell(name, resample(pts, min(spacing, 0.008)) if segments > 1 else list(pts), [resample(h, 0.008) for h in holes],
               thick, mat, spacing, back=spacing * 2.5, bevel=bevel, segments=segments)
    return wrap_fit(ob, F.s, thick, base=F.d - 0.0015 + lift, full=True)


def ridge(name, pts, F, mat, w, h, nprof=5, sink=0.0015, closed=False, lift=0.0):
    """a raised bead lying on the front surface F along the (x, z) path pts: half-width w(t), height h(t) (t 0..1 along
    the path; numbers or functions), a half-elliptic section; the ends close (fully where w is 0)"""
    n = len(pts)
    P = [F.p(x, z, lift - sink) for x, z in pts]
    N = [F.n(x, z) for x, z in pts]
    verts, faces = [], []
    for i in range(n):
        d = (P[(i + 1) % n] - P[i - 1]) if closed else (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])
        d.normalize()
        side = d.cross(N[i]).normalized()
        t = i / (n if closed else n - 1)
        wi = w(t) if callable(w) else w
        hi = h(t) if callable(h) else h
        for k in range(nprof):
            a = math.pi * k / (nprof - 1)
            verts.append(P[i] + side * (wi * math.cos(a)) + N[i] * (hi * math.sin(a)))
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(nprof - 1):
            faces.append((i * nprof + k, j * nprof + k, j * nprof + k + 1, i * nprof + k + 1))
    if not closed:
        faces.append(tuple(range(nprof)))
        faces.append(tuple((n - 1) * nprof + k for k in reversed(range(nprof))))
    bm = bmesh.new()
    bv = [bm.verts.new(v) for v in verts]
    for f in faces:
        try:
            bm.faces.new([bv[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = A._new_obj(name, me)
    for p in ob.data.polygons:
        p.use_smooth = True
    return A._finish(ob, mat)


def cones(name, specs, mat, sides=4, cap=False):
    """many thin cones in one mesh (fur tufts, barbs): specs = [(base, tip, base radius)]"""
    verts, faces = [], []
    for b, tp, r in specs:
        b, tp = Vector(b), Vector(tp)
        d = (tp - b).normalized()
        u = d.orthogonal().normalized()
        w = d.cross(u)
        i0 = len(verts)
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(b + (u * math.cos(a) + w * math.sin(a)) * r)
        verts.append(tp)
        for k in range(sides):
            faces.append((i0 + k, i0 + (k + 1) % sides, i0 + sides))
        if cap:
            faces.append(tuple(i0 + k for k in reversed(range(sides))))
    return A.mesh_from(name, verts, faces, mat)


def report(key):
    """triangles per part and the head clearance (min distance off the head's surface; < 0 is inside it)"""
    dg = bpy.context.evaluated_depsgraph_get()
    tot, rows = 0, {}
    worst = (9.0, "")
    for ob in A.PARTS:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        tot += tris
        d = min((head_sdf(ev.matrix_world @ v.co) for v in me.vertices), default=9.0)
        grp = ob.name.rstrip("0123456789-_")
        r = rows.setdefault(grp, [0, 9.0])
        r[0] += tris; r[1] = min(r[1], d)
        if d < worst[0]:
            worst = (d, ob.name)
        ev.to_mesh_clear()
    print(f"[c2] {key}: {tot} tris; closest to the head {worst[0]:.4f} ({worst[1]})")
    for grp, (t, d) in sorted(rows.items(), key=lambda kv: -kv[1][0]):
        print(f"[c2]   {grp:24s} {t:6d} tris  clear {d:+.4f}")


# ================================================================== 1. the wax saint mask
WAX_DEPTH = 0.028


def wax_sculpt(x, z):
    ax = abs(x)
    brow = 0.026 * g(ax, 0.19, 0.12) * g(z, 1.695, 0.040)
    lid = 0.022 * g(ax, 0.205, 0.068) * g(z, 1.608, 0.036)          # the closed, downcast lids
    crease = -0.010 * g(ax, 0.20, 0.085) * g(z, 1.652, 0.020)        # between the brow and the lid
    under = -0.006 * g(ax, 0.20, 0.08) * g(z, 1.555, 0.022)
    nose = (0.068 * g(x, 0, 0.048) * smooth(1.33, 1.42, z) * (1 - smooth(1.63, 1.72, z))
            + 0.030 * g(x, 0, 0.072) * g(z, 1.355, 0.042) + 0.012 * g(ax, 0.058, 0.026) * g(z, 1.345, 0.026))
    cheek = 0.026 * g(ax, 0.29, 0.10) * g(z, 1.43, 0.09)
    lips = (0.019 * g(x, 0, 0.092) * g(z, 1.226, 0.024) * (1 - 0.35 * g(x, 0, 0.018))
            + 0.017 * g(x, 0, 0.074) * g(z, 1.170, 0.022) - 0.007 * g(x, 0, 0.085) * g(z, 1.199, 0.009))
    philtrum = 0.006 * g(ax, 0.016, 0.010) * g(z, 1.272, 0.030)
    chin = 0.030 * g(x, 0, 0.13) * g(z, 1.100, 0.050)
    temples = -0.012 * smooth(0.32, 0.43, ax)
    lumps = 0.0022 * (math.sin(23 * x + 1.3) * math.sin(19 * z + 0.4) + 0.6 * math.sin(41 * x - 31 * z + 2.0))
    return brow + lid + crease + under + nose + cheek + lips + philtrum + chin + temples + lumps


WAX_JAW_DRIPS = [(-0.275, 0.060, 0.046, 0.13), (-0.125, 0.034, 0.042, 0.0), (0.020, 0.052, 0.046, 0.16),
                 (0.165, 0.040, 0.042, 0.0), (0.292, 0.066, 0.046, 0.11)]   # (x, how far the tongue sags, width, bead run)
WAX_BROW_DRIPS = [(-0.330, 0.075), (-0.215, 0.118), (-0.085, 0.060), (0.105, 0.088), (0.235, 0.105),
                  (0.335, 0.062)]                                           # (x, length)


def wax_outline():
    # hair-friendly (2026-11-12): the brow edge runs just over the brows and the sides stop short of the temples
    # (a fringe or side lock crosses anything higher or wider)
    half = [(0, 1.762), (0.12, 1.757), (0.24, 1.742), (0.33, 1.715), (0.395, 1.672), (0.428, 1.605), (0.436, 1.53),
            (0.428, 1.44), (0.404, 1.34), (0.36, 1.245), (0.292, 1.155), (0.205, 1.09), (0.105, 1.053), (0, 1.042)]
    loop = resample(catmull(mirrored(half), 12), 0.005)
    out = []
    for x, z in loop:
        if z > 1.62:   # the brow edge has softened into lumps
            z += 0.005 * math.sin(41 * x + 0.7) * smooth(1.62, 1.70, z)
        if z < 1.40:   # the jaw edge sags into drip tongues
            for x0, sag, w, _ in WAX_JAW_DRIPS:
                u = (x - x0) / w
                if abs(u) < 1:
                    z -= sag * (1 - u * u) ** 0.6 * (1 - smooth(1.25, 1.40, z))
        out.append((x, z))
    return ccw(resample(out, 0.012))


def drip_profile(L, w0, ws, rb, emerge=False):
    """half-width along a drip of length L: a stream (from the rim, or emerging from the surface) ending in a pooled bead"""
    sc = L - rb

    def w(t):
        s = t * L
        stream = lerp(ws, ws * 0.78, s / L) * (smooth(0.0, 0.035, s) if emerge else 1.0)
        if not emerge:
            stream += (w0 - ws) * math.exp(-s / 0.018)
        bead = rb * math.sqrt(max(0.0, 1 - ((s - sc) / rb) ** 2)) if s > sc - rb else 0.0
        return bead if s >= sc else max(stream, bead)
    return w


def drip_path(x0, z0, L, rb, seed):
    ss = [i * 0.009 for i in range(int((L - 2 * rb) / 0.009) + 1)]
    ss += [L - rb - rb * math.cos(math.pi * k / 8) for k in range(9)]
    pts = []
    for s in ss:
        pts.append((x0 + 0.004 * math.sin(11 * s + seed) * min(1, s / 0.05), z0 - s))
    return pts, [s / L for s in ss]


def ridge_s(name, pts, ts, F, mat, w, h, nprof=6, sink=0.0015):
    """a ridge whose profile functions take each sample's own t (uneven sampling along the path)"""
    tl = list(ts)
    return ridge(name, pts, F, mat, lambda t, tl=tl, n=len(pts): w(tl[min(n - 1, int(round(t * (n - 1))))]),
                 lambda t, tl=tl, n=len(pts): h(tl[min(n - 1, int(round(t * (n - 1))))]), nprof=nprof, sink=sink)


@item("WaxMask", "Wax saint mask", views=["front34", "front", "side"], close=((1.5, -3.6, 1.65), (0, -0.6, 1.45), 60))
def build_wax(M):
    piece("WaxMask", "Head")
    wax = A.mat_flat("SaintWax", (0.82, 0.72, 0.52), rough=0.46, noise=22, bump=0.05, vary=0.08, wear=0.0, dirt=0.35,
                     sheen=0.35)
    drip = A.mat_flat("RunWax", (0.93, 0.87, 0.71), rough=0.20, coat=0.6, noise=30, bump=0.02, vary=0.04, wear=0.0,
                      dirt=0.1)
    gilt = A.mat_metal("SaintGilt", (1.0, 0.77, 0.36), rough=0.22, scratch=0.25, wear=0.35)
    F = Face(wax_sculpt, WAX_DEPTH)
    outline = wax_outline()
    # the eyes: closed lids carved with a see-through slit along the lash line, curving down (downcast), outer corners low
    slits = []
    for sx in (-1, 1):
        cx, cz, w = sx * 0.205, 1.600, 0.074
        up, lo = [], []
        for i in range(19):
            u = -1 + 2 * i / 18
            mid = cz - 0.011 * (1 - u * u) - 0.008 * u * sx
            hs = 0.0062 * (1 - u * u) ** 0.85
            up.append((cx + u * w, mid + hs)); lo.append((cx + u * w, mid - hs))
        slits.append(ccw(up[:-1] + lo[::-1][:-1]))

    def spacing(x, z):
        feat = max(g(x, 0, 0.12) * g(z, 1.40, 0.30), g(abs(x), 0.205, 0.10) * g(z, 1.62, 0.09))
        return lerp(0.029, 0.016, smooth(0.15, 0.8, feat))
    ob = shell("WaxShell", outline, [s[::-1] for s in slits], WAX_DEPTH, wax, spacing, bevel=0.012, segments=3)
    wrap_fit(ob, wax_sculpt, WAX_DEPTH)
    # the lash line: a fine carved lip along each slit's upper edge
    for k, s in enumerate(slits):
        sx = (-1, 1)[k]
        cx, cz, w = sx * 0.205, 1.600, 0.074
        lash = []
        for i in range(17):
            u = -0.94 + 1.88 * i / 16
            lash.append((cx + u * w, cz - 0.011 * (1 - u * u) - 0.008 * u * sx + 0.0062 * (1 - u * u) ** 0.85 + 0.004))
        ridge(f"WaxLash{k}", lash, F, wax, lambda t: 0.0042 * math.sin(math.pi * t) ** 0.5, lambda t: 0.0032 * math.sin(math.pi * t) ** 0.5,
              nprof=5)
    # the gilt nimbus: a fine line arched over the brow, worn faint at its ends, and a small cross pattee
    def arc(a, b, n=40):
        return [(a * math.cos(math.radians(lerp(14, 166, i / n))), 1.565 + b * math.sin(math.radians(lerp(14, 166, i / n))))
                for i in range(n + 1)]
    ends = lambda t: smooth(0.0, 0.05, t) * smooth(1.0, 0.95, t)
    ends = lambda t: smooth(0.0, 0.16, t) * smooth(1.0, 0.84, t)
    ridge("Halo", arc(0.335, 0.158, 48), F, gilt, lambda t: 0.0016 + 0.0030 * ends(t), lambda t: 0.0010 + 0.0024 * ends(t),
          nprof=5)
    # order the arm outline: each arm right-flank then the flare tip then left-flank, arms ccw
    cr = []
    for k in range(4):
        rot = k * HP
        for x, z in ((0.0055, 0.0055), (0.0068, 0.020), (0.0165, 0.031), (-0.0165, 0.031), (-0.0068, 0.020), (-0.0055, 0.0055)):
            cr.append((x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot)))
    cr = ccw([(x, 1.690 + z * 1.0) for x, z in cr])
    decal("GiltCross", cr, F, 0.0040, gilt, spacing=0.008, bevel=0.0014)
    # the wax has run: a rolled, lumpy rim along the brow edge with drips running down the forehead ...
    rim = run_where(offset_poly(outline, 0.009), lambda x, z: z > 1.62)
    rim = resample(rim, 0.010, closed=False)
    ridge("BrowRim", rim, F, drip,
          lambda t: (0.0150 + 0.0040 * math.sin(37 * t) + 0.0030 * math.sin(83 * t + 1)) * smooth(0.0, 0.06, t) * smooth(1.0, 0.94, t),
          lambda t: (0.0115 + 0.0025 * math.sin(53 * t + 2)) * smooth(0.0, 0.06, t) * smooth(1.0, 0.94, t), nprof=6)
    for k, (x0, L) in enumerate(WAX_BROW_DRIPS):
        z0 = edge_z(outline, x0)[1] - 0.010
        rb = 0.027 + 0.007 * ((k * 37) % 5) / 4
        pts, ts = drip_path(x0, z0, L, rb, k * 1.7)
        wf = drip_profile(L, 0.032, 0.0185 + 0.0025 * (k % 3), rb)
        ridge_s(f"BrowDrip{k}", pts, ts, F, drip, wf, lambda t, wf=wf: wf(t) * (0.80 + 0.12 * smooth(0.6, 0.95, t)))
    # ... and the jaw edge has sagged into tongues, each with a bead of wax running down it to hang just off the edge
    for k, (x0, sag, w, run) in enumerate(WAX_JAW_DRIPS):
        if not run:
            continue
        zb = edge_z(outline, x0)[0]
        rb = min(w * 0.68, 0.030)
        L = run + sag
        pts, ts = drip_path(x0, zb - 0.010 + L, L, rb, k * 2.3)
        wf = drip_profile(L, 0.0, 0.0175, rb, emerge=True)
        ridge_s(f"JawDrip{k}", pts, ts, F, drip, wf, lambda t, wf=wf: wf(t) * (0.78 + 0.14 * smooth(0.6, 0.95, t)))
    report("WaxMask")
    return {"notes": "Kit C2"}


# ================================================================== 2. the moth mask
MOTH_DEPTH = 0.020


def moth_sculpt(x, z):
    ax = abs(x)
    swell = 0.010 * g(ax, 0.32, 0.16) * g(z, 1.70, 0.12)
    bridge = 0.010 * g(x, 0, 0.07) * g(z, 1.62, 0.12)
    socket = -0.005 * g(ax, 0.205, 0.09) * g(z, 1.605, 0.05)
    cup = -0.004 * smooth(0.46, 0.58, ax)
    return swell + bridge + socket + cup


MOTH_EYE = dict(cz=1.606, w=0.094, h=0.047)


def moth_outline():
    # hair-friendly (2026-11-12): the wings keep inside |x| 0.45 and under the brow line (every fringe and side lock
    # crosses anything above or outside), the falcate forewing tips at the brow's outer ends
    half = [(0, 1.722), (0.028, 1.716), (0.048, 1.696), (0.085, 1.678), (0.160, 1.684), (0.250, 1.694), (0.330, 1.704),
            (0.385, 1.720), (0.418, 1.723), (0.434, 1.708), (0.436, 1.675), (0.428, 1.640), (0.414, 1.613),
            (0.420, 1.578), (0.408, 1.528), (0.389, 1.474), (0.356, 1.424), (0.312, 1.392), (0.252, 1.388),
            (0.192, 1.405), (0.140, 1.432), (0.100, 1.458), (0.065, 1.480), (0.038, 1.460), (0, 1.440)]
    loop = resample(catmull(mirrored(half), 12), 0.004)
    # the wing margins are softly scalloped between the vein ends
    out = []
    S = 0.0
    for i, (x, z) in enumerate(loop):
        if i:
            S += math.hypot(x - loop[i - 1][0], z - loop[i - 1][1])
        m = max(smooth(0.38, 0.42, abs(x)) * smooth(1.47, 1.52, z), smooth(0.20, 0.30, abs(x)) * (1 - smooth(1.44, 1.47, z)))
        sc = 0.0055 * m * (1 - abs(math.sin(math.pi * S / 0.052))) ** 1.6
        out.append((x, z, sc))
    pts = []
    n = len(out)
    for i, (x, z, sc) in enumerate(out):   # push the scallop cusps inward along the outline's inward normal
        x0, z0, _ = out[i - 1]; x1, z1, _ = out[(i + 1) % n]
        tx, tz = x1 - x0, z1 - z0
        L = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / L, tx / L   # the left normal; outline orientation decides which side is in
        pts.append((x, z, nx, nz, sc))
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sg = 1 if area > 0 else -1
    return ccw(resample([(x + sg * nx * sc, z + sg * nz * sc) for x, z, nx, nz, sc in pts], 0.0135))


def moth_eye(sx, grow=0.0, n=32):
    return ccw(almond(sx * 0.205, MOTH_EYE["cz"], MOTH_EYE["w"] + grow, MOTH_EYE["h"] + grow, 0.06 * sx, n=n))


@item("MothMask", "Moth mask", views=["front34", "front", "side"], close=((1.6, -3.7, 1.85), (0, -0.6, 1.66), 60))
def build_moth(M):
    piece("MothMask", "Head")
    velvet = A.mat_velvet("MothVelvet", (0.014, 0.008, 0.022), rough=0.85, sheen=0.18)
    vein = A.mat_velvet("MothVein", (0.060, 0.042, 0.072), rough=0.7, sheen=0.6)
    crimson = A.mat_velvet("MothCrimson", (0.19, 0.014, 0.032), rough=0.72, sheen=0.8)
    bone = A.mat_flat("MothBone", (0.74, 0.66, 0.53), rough=0.78, noise=60, bump=0.05, vary=0.08, wear=0.0, dirt=0.3,
                      sheen=0.6)
    black = A.mat_velvet("MothBlack", (0.010, 0.008, 0.012), rough=0.8, sheen=0.6)
    gloss = M["black_enamel"]
    barb_m = A.mat_flat("AntennaUmber", (0.30, 0.215, 0.135), rough=0.72, noise=80, bump=0.05, vary=0.08, wear=0.0, dirt=0.3,
                        sheen=0.7)
    F = Face(moth_sculpt, MOTH_DEPTH)
    outline = moth_outline()
    eyes = [moth_eye(sx) for sx in (-1, 1)]
    ob = shell("MothWings", outline, [resample(e, 0.011)[::-1] for e in eyes], MOTH_DEPTH, velvet, 0.031,
               bevel=0.009, segments=3)
    wrap_fit(ob, moth_sculpt, MOTH_DEPTH)
    inset = offset_poly(outline, 0.016)
    for k, sx in enumerate((-1, 1)):
        c = Vector((sx * 0.205, MOTH_EYE["cz"]))
        # the discal cell: a raised vein loop round the eye hole
        loop = resample(moth_eye(sx, 0.017), 0.011)
        ridge(f"CellVein{k}", loop, F, vein, 0.0048, 0.0036, nprof=4, closed=True)
        # veins radiating from the cell to the margin (and two back to the body), curving like a wing's
        root = Vector((sx * 0.02, 1.62))
        for j, th in enumerate((104, 70, 16, -10, -30, -62, -98, -136, 166, -170)):
            a = math.radians(th if sx > 0 else 180 - th)
            dir0 = Vector((math.cos(a), math.sin(a)))
            p = c + Vector((dir0.x * (MOTH_EYE["w"] + 0.017), dir0.y * (MOTH_EYE["h"] + 0.017)))
            path = [tuple(p)]
            for _ in range(80):
                rad = (p - root).normalized()
                d = (dir0 * 0.72 + rad * 0.28).normalized() if abs(th) < 150 else dir0
                q = p + d * 0.013
                if not A._inside(tuple(q), inset) or abs(q.x) < 0.062:
                    break
                p = q
                path.append(tuple(p))
            if len(path) < 3:
                continue
            ridge(f"Vein{k}_{j}", path, F, vein, lambda t: 0.0042 * (1 - 0.55 * t) * smooth(1.0, 0.9, t) + 0.0006,
                  lambda t: 0.0032 * (1 - 0.5 * t), nprof=4)
        # a crimson submarginal band and a bone dash line along the outer margins
        band = run_where(offset_poly(outline, 0.046),
                         lambda x, z, sx=sx: x * sx > 0 and (abs(x) > 0.36 or (z < 1.50 and abs(x) > 0.20)))
        band = resample(band, 0.012, closed=False)
        band = [(x, z) for x, z in band]
        ridge(f"MarginBand{k}", band, F, crimson, lambda t: 0.0065 * smooth(0, 0.06, t) * smooth(1, 0.94, t),
              lambda t: 0.0016, nprof=4, lift=0.0004)
        dash = run_where(offset_poly(outline, 0.024),
                         lambda x, z, sx=sx: x * sx > 0 and (abs(x) > 0.33 or (z < 1.52 and abs(x) > 0.14)))
        dash = resample(dash, 0.0045, closed=False)
        for i in range(2, len(dash) - 4, 9):
            ridge(f"MarginDash{k}_{i}", dash[i:i + 4], F, bone, lambda t: 0.0036 * math.sin(math.pi * (0.15 + 0.7 * t)),
                  0.0020, nprof=3)
        # the eye-spots: a big one on the forewing, a small one on the hindwing (inlays over the veins)
        for name, (x, z), rings in (("Fore", (sx * 0.362, 1.666), ((0.036, bone, 0.0060), (0.028, crimson, 0.0070),
                                                                   (0.016, black, 0.0080), (0.0062, bone, 0.0090))),
                                    ("Hind", (sx * 0.292, 1.458), ((0.030, crimson, 0.0060), (0.019, bone, 0.0070),
                                                                   (0.0088, black, 0.0080)))):
            for r_i, (rad, mat, t) in enumerate(rings):
                cx = x + (sx * -0.005 if r_i == 3 else 0.0)
                cz = z + (0.006 if r_i == 3 else 0.0)
                nq = max(12, int(2 * math.pi * rad / 0.0095))
                d = [(cx + rad * math.cos(2 * math.pi * q / nq), cz + rad * 0.92 * math.sin(2 * math.pi * q / nq)) for q in range(nq)]
                decal(f"Spot{name}{k}_{r_i}", d, F, t, mat, spacing=min(0.018, rad * 0.7), bevel=0.0015, segments=1)
    # the moth's body down the nose bridge: head, a furry thorax with a bone collar, a banded abdomen
    def seg(name, z, rx, ry, rz, mat, seg_=14, rings=8, lift_f=0.25):
        p = F.p(0.0, z, ry * lift_f)
        return A.sphere(name, 1.0, tuple(p), mat, scale=(rx, ry, rz), seg=seg_, rings=rings)
    HZ, TZ = 1.700, 1.643   # the head sits on the wings' top edge, the thorax between the brows
    seg("MothHead", HZ, 0.028, 0.024, 0.024, velvet, 12, 8)
    for sx in (-1, 1):
        p = F.p(sx * 0.020, HZ + 0.003, 0.017)
        A.sphere(f"MothEye{sx}", 0.0115, tuple(p), gloss, seg=8, rings=5)
    seg("MothThorax", TZ, 0.046, 0.033, 0.046, velvet, 16, 10)
    abd = [(1.589, 0.038, 0.027, 0.024), (1.555, 0.035, 0.025, 0.022), (1.525, 0.031, 0.023, 0.020),
           (1.499, 0.026, 0.020, 0.018), (1.477, 0.021, 0.016, 0.016), (1.460, 0.015, 0.012, 0.013)]
    for i, (z, rx, ry, rz) in enumerate(abd):
        seg(f"Abdomen{i}", z, rx, ry, rz, crimson if i % 2 == 0 else velvet, 10, 6)
    rnd = random.Random(7)
    fur, collar = [], []
    T = F.p(0.0, TZ, 0.033 * 0.25)
    for i in range(70):   # fur tufts all over the thorax's visible side
        u = rnd.uniform(-1, 1); v = rnd.uniform(-0.95, 0.95)
        a = math.pi * 0.5 * u * 1.15
        nrm = Vector((math.sin(a) * math.cos(v * HP), -math.cos(a) * math.cos(v * HP), math.sin(v * HP)))
        if nrm.y > 0.15:
            continue
        base = T + Vector((nrm.x * 0.046, nrm.y * 0.033, nrm.z * 0.046)) * 0.85
        tip = base + (nrm + Vector((rnd.uniform(-0.3, 0.3), 0, -0.35))).normalized() * rnd.uniform(0.014, 0.024)
        fur.append((base, tip, 0.0055))
    for i in range(26):   # the bone collar between the head and the thorax
        a = -HP * 1.05 + math.pi * 1.05 * i / 25
        nrm = Vector((math.sin(a), -math.cos(a), 0.25)).normalized()
        base = T + Vector((math.sin(a) * 0.039, -math.cos(a) * 0.027, 0.036))
        tip = base + (nrm + Vector((0, 0, 0.35)) * rnd.uniform(0.5, 1.2)).normalized() * rnd.uniform(0.015, 0.022)
        collar.append((base, tip, 0.0060))
    for i, (z, rx, ry, rz) in enumerate(abd[:-1]):   # side tufts along the abdomen
        C = F.p(0.0, z, ry * 0.25)
        for sx in (-1, 1):
            base = C + Vector((sx * rx * 0.9, -ry * 0.2, 0))
            tip = base + Vector((sx * 0.9, -0.3, -0.35)).normalized() * (0.014 - 0.0015 * i)
            fur.append((base, tip, 0.0045))
    cones("ThoraxFur", fur, velvet)
    cones("CollarFur", collar, bone)
    # two feathered antennae: they rise from the head and curl forward and out, standing well in front of the brow
    # (a fringe lies 0.03 .. 0.10 off the forehead: over the head they would cross nearly every hairstyle)
    def cyl(x, z, r):
        a_ = x / HEAD_R
        return Vector((r * math.sin(a_), -r * math.cos(a_), z))

    def cr3(ctrl, n):
        P = [ctrl[0] * 2 - ctrl[1]] + list(ctrl) + [ctrl[-1] * 2 - ctrl[-2]]
        out = []
        for i in range(n):
            f = i / (n - 1) * (len(ctrl) - 1)
            j = min(len(ctrl) - 2, int(f)); t = f - j
            p0, p1, p2, p3 = P[j], P[j + 1], P[j + 2], P[j + 3]
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
        return out
    for sx in (-1, 1):
        ctrl = [cyl(sx * x, z, r) for x, z, r in ((0.010, HZ + 0.014, 0.656), (0.028, 1.752, 0.692), (0.062, 1.786, 0.735),
                                                  (0.110, 1.800, 0.772), (0.160, 1.806, 0.795), (0.204, 1.798, 0.808),
                                                  (0.228, 1.780, 0.810), (0.226, 1.760, 0.804))]
        sh = cr3(ctrl, 25)
        A.tube(f"AntennaShaft{sx}", [tuple(p) for p in sh], 0.0075, barb_m, res=4, poly=True,
               taper=lambda t: 1.0 - 0.6 * t)
        A.sphere(f"AntennaScape{sx}", 0.0100, tuple(sh[0]), velvet, seg=8, rings=5)
        barbs = []
        nb = 36
        for i in range(1, nb):   # a comb of barbs both sides, longest a third of the way up: a feather's outline
            t = 0.06 + 0.92 * i / nb
            f = t * 24
            j = min(23, int(f))
            p = sh[j].lerp(sh[j + 1], f - j)
            tg = (sh[j + 1] - sh[j]).normalized()
            hn = Vector((p.x, p.y, 0)).normalized()   # outward, away from the face
            side = tg.cross(hn).normalized()
            L = 0.042 * math.sin(math.pi * min(1.0, 0.10 + 0.95 * t)) ** 0.55 + 0.006
            for s in (-1, 1):
                d = (side * s * 0.80 + tg * 0.50 + hn * 0.20).normalized()
                barbs.append((p, p + d * L, 0.0034))
        cones(f"AntennaBarbs{sx}", barbs, barb_m, sides=3)
    report("MothMask")
    return {"notes": "Kit C2"}


# ================================================================== 3. the black silk domino
DOM_DEPTH = 0.022


def domino_sculpt(x, z):
    ax = abs(x)
    brow = 0.010 * g(ax, 0.20, 0.16) * g(z, 1.705, 0.045)
    bridge = 0.012 * g(x, 0, 0.06) * g(z, 1.56, 0.08)
    socket = -0.004 * g(ax, 0.205, 0.09) * g(z, 1.60, 0.05)
    return brow + bridge + socket


def domino_outline():
    half = [(0, 1.744), (0.10, 1.751), (0.20, 1.758), (0.30, 1.768), (0.39, 1.785), (0.462, 1.808), (0.512, 1.828),
            (0.530, 1.812), (0.516, 1.735), (0.476, 1.625), (0.415, 1.533), (0.335, 1.482), (0.245, 1.466),
            (0.158, 1.476), (0.092, 1.503), (0.050, 1.540), (0, 1.560)]
    return ccw(resample(catmull(mirrored(half), 12), 0.013))


@item("DominoMask", "Black silk domino", views=["front34", "front", "side"], close=((1.4, -3.2, 1.75), (0, -0.6, 1.6), 60))
def build_domino(M):
    piece("DominoMask", "Head")
    silk = A.mat_cloth("DominoSilk", (0.011, 0.010, 0.014), weave=700, rough=0.27, sheen=0.5, bump=0.03, twill=False,
                       vary=0.04, wear=0.05, dirt=0.2)
    piping = A.mat_cloth("DominoPiping", (0.30, 0.025, 0.05), weave=900, rough=0.35, sheen=0.5, bump=0.04, twill=True,
                         vary=0.05, wear=0.05, dirt=0.2)
    gold = M["gold"]
    F = Face(domino_sculpt, DOM_DEPTH)
    outline = domino_outline()
    eyes = [ccw(resample(almond(sx * 0.205, 1.607, 0.094, 0.046, 0.10 * sx, n=48), 0.011)) for sx in (-1, 1)]
    ob = shell("DominoSilk", outline, [e[::-1] for e in eyes], DOM_DEPTH, silk, 0.020, bevel=0.010, segments=3)
    wrap_fit(ob, domino_sculpt, DOM_DEPTH)
    # crimson satin piping rolled over the outer edge and round both eyes
    for k, loop in enumerate([resample(outline, 0.015)] + [resample(e, 0.012) for e in eyes]):
        A.tube(f"Piping{k}", [tuple(F.frac(x, z, 0.58)) for x, z in loop], 0.0094, piping, res=4, closed=True, poly=True)
    # a fine gold thread line inset from the outer edge
    line = resample(offset_poly(outline, 0.026), 0.012)
    ridge("GoldThread", line, F, gold, 0.0026, 0.0020, nprof=4, closed=True)
    report("DominoMask")
    return {"notes": "Kit C2"}


if __name__ == "__main__":
    targets = [a for a in A.argv if not a.startswith("--") and (A.argv.index(a) == 0 or not A.argv[A.argv.index(a) - 1].startswith("--"))]
    keys = targets[0].split(",") if targets else ["WaxMask", "MothMask", "DominoMask"]
    for k in keys:
        try:
            A.run(k)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[kitc] {k} FAILED: {e}")
