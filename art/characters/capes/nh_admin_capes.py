"""Nightmare Highschool: the admin kit's 3D capes (staff-only), rigged for Controllers.Character.CapeSway.

Headless:  E:/Blender/blender.exe -b --factory-startup -P nh_admin_capes.py -- [--only WardenMantle,...] [--nobake]

Five capes: WardenMantle, ReaperShroud, DuelistCape, CaptainGreatcape, MidnightCollar.
Writes per cape (OUT = E:/NH-Work/capes):
  fbx/NHCape_<Set>.fbx      mesh CapeBody + armature (global_scale 0.01: Roblox reads it as centimetres)
  <Set>.blend               the build, for the preview renders (cape_preview.py)
  bake/<Set>_ao.png         2048 ambient occlusion in the cape's own UV atlas
  layout/<Set>.json         UV islands (rect, material, size in studs) for paint_capes.py, plus bones and the torso fit

Space: studs on a 2 x 2 x 1 R6 torso centred at the origin. Blender -Y is the front (Roblox's importer maps it to the
front), +X is the character's LEFT, +Z up. Roblox torso space = (-x, z, y).
Rig (what CapeSway expects): Root (depth 0) > H<col> hinge (depth 1, never moved) > C<col>_<k> chain (depth 2+, swung
back about the torso's right axis, more the deeper). Collars, hoods, clasps and epaulettes ride Root or the cloth
under them. At most 4 bone weights per vertex.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "E:/NH-Work/capes"
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
BAKE = "--nobake" not in argv
for d in ("fbx", "bake", "layout"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
ATLAS = 2048
PAD = 6 / ATLAS


# ------------------------------------------------------------------ helpers
def lerp(a, b, t):
    return a + (b - a) * t


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if b != a else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


def interp(keys, x):
    """piecewise-smooth through (x, y) keys (cosine between keys)"""
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            t = (1 - math.cos(math.pi * t)) / 2
            return y0 + (y1 - y0) * t
    return keys[-1][1]


class Mesh:
    """verts with one UV and a bone-weight dict each; islands own their verts, so seams are hard"""

    def __init__(self):
        self.co, self.uv, self.w, self.faces, self.smooth = [], [], [], [], []

    def v(self, co, uv, w):
        self.co.append(Vector(co)); self.uv.append(uv); self.w.append(dict(w))
        return len(self.co) - 1

    def f(self, idx, smooth=True, expect=None):
        if expect is not None:
            a, b, c = (self.co[i] for i in idx[:3])
            n = (b - a).cross(c - a)
            if n.length < 1e-12 and len(idx) > 3:
                n = (c - a).cross(self.co[idx[3]] - a)
            if n.dot(expect) < 0:
                idx = list(reversed(idx))
        self.faces.append(list(idx)); self.smooth.append(smooth)


def rect_uv(rect, fu, fv):
    """island-relative (fu across, fv down from the top) -> atlas uv, inset by PAD"""
    u0, v0, u1, v1 = rect
    return (u0 + PAD + (u1 - u0 - 2 * PAD) * fu, v1 - PAD - (v1 - v0 - 2 * PAD) * fv)


def grid_normals(G):
    nu, nv = len(G) - 1, len(G[0]) - 1
    N = []
    for i in range(nu + 1):
        col = []
        for j in range(nv + 1):
            du = G[min(i + 1, nu)][j] - G[max(i - 1, 0)][j]
            dv = G[i][min(j + 1, nv)] - G[i][max(j - 1, 0)]
            n = du.cross(dv)
            col.append(n.normalized() if n.length > 1e-9 else Vector((0, 1, 0)))
        N.append(col)
    return N


def sheet(M, G, W, thick, outer, inner, rim, rims=("top", "bottom", "left", "right"), stats=None):
    """a cloth panel with real thickness from a mid-surface grid G[i][j] (i across, j down); W[i][j] bone weights.
    Outer shell faces cross(du, dv); inner shell gets its own UVs (mirrored across, so it reads right from inside);
    rims are flat strips in the rim island."""
    nu, nv = len(G) - 1, len(G[0]) - 1
    N = grid_normals(G)
    t = thick(i_j=None) if callable(thick) else thick
    O = [[None] * (nv + 1) for _ in range(nu + 1)]
    I = [[None] * (nv + 1) for _ in range(nu + 1)]
    for i in range(nu + 1):
        for j in range(nv + 1):
            p, n = G[i][j], N[i][j]
            O[i][j] = M.v(p + n * (t / 2), rect_uv(outer, i / nu, j / nv), W[i][j])
            I[i][j] = M.v(p - n * (t / 2), rect_uv(inner, 1 - i / nu, j / nv), W[i][j])
    for i in range(nu):
        for j in range(nv):
            M.f([O[i][j], O[i + 1][j], O[i + 1][j + 1], O[i][j + 1]])
            M.f([I[i][j], I[i][j + 1], I[i + 1][j + 1], I[i + 1][j]])
    # rims: strips joining the two shells along the open edges
    edges = []
    if "top" in rims:
        edges.append(([(i, 0) for i in range(nu + 1)], "top"))
    if "bottom" in rims:
        edges.append(([(i, nv) for i in range(nu + 1)], "bottom"))
    if "left" in rims:
        edges.append(([(0, j) for j in range(nv + 1)], "left"))
    if "right" in rims:
        edges.append(([(nu, j) for j in range(nv + 1)], "right"))
    for k, (pts, side) in enumerate(edges):
        a0 = k / max(1, len(edges)); a1 = (k + 1) / max(1, len(edges))
        ro, ri = [], []
        for q, (i, j) in enumerate(pts):
            fu = lerp(a0, a1, q / (len(pts) - 1))
            ro.append(M.v(M.co[O[i][j]], rect_uv(rim, fu, 0.0), W[i][j]))
            ri.append(M.v(M.co[I[i][j]], rect_uv(rim, fu, 1.0), W[i][j]))
        for q in range(len(pts) - 1):
            i, j = pts[q]
            i2, j2 = pts[q + 1]
            mid = (G[i][j] + G[i2][j2]) / 2
            if side == "top":
                ex = G[i][j] - G[i][min(j + 1, nv)]
            elif side == "bottom":
                ex = G[i][j] - G[i][max(j - 1, 0)]
            elif side == "left":
                ex = G[i][j] - G[min(i + 1, nu)][j]
            else:
                ex = G[i][j] - G[max(i - 1, 0)][j]
            M.f([ro[q], ro[q + 1], ri[q + 1], ri[q]], smooth=False, expect=ex)
    if stats is not None:
        # outer-shell widths per row and lengths per column, in studs (the painter scales patterns by them)
        stats["row_w"] = [sum((G[i + 1][j] - G[i][j]).length for i in range(nu)) for j in range(nv + 1)]
        stats["col_l"] = [sum((G[i][j + 1] - G[i][j]).length for j in range(nv)) for i in range(nu + 1)]
        # running length down each column at every row (rows aren't evenly spaced: the yoke and roll are packed)
        stats["col_s"] = [[0.0] + [sum((G[i][k + 1] - G[i][k]).length for k in range(j)) for j in range(1, nv + 1)]
                          for i in range(nu + 1)]
    return O, I


def tube(M, path, radius, rect, w, sides=8, cap=True, twist=0.0, along=None, flat=False):
    """a tube along path points; radius(t) or float; w(t) -> weights or dict"""
    n = len(path)
    rad = radius if callable(radius) else (lambda t: radius)
    wf = w if callable(w) else (lambda t: w)
    # parallel-transport frames
    T = [(path[min(k + 1, n - 1)] - path[max(k - 1, 0)]).normalized() for k in range(n)]
    ref = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    Nn = [T[0].cross(ref).normalized()]
    for k in range(1, n):
        b = Nn[-1] - T[k] * Nn[-1].dot(T[k])
        Nn.append(b.normalized() if b.length > 1e-9 else Nn[-1])
    L = [0.0]
    for k in range(1, n):
        L.append(L[-1] + (path[k] - path[k - 1]).length)
    tot = max(L[-1], 1e-6)
    rings = []
    for k in range(n):
        t = L[k] / tot
        B = T[k].cross(Nn[k])
        ring = []
        for s in range(sides + 1):
            a = 2 * math.pi * s / sides + twist * t
            off = (Nn[k] * math.cos(a) + B * math.sin(a)) * rad(t)
            ring.append(M.v(path[k] + off, rect_uv(rect, (along(t) if along else t), s / sides), wf(t)))
        rings.append(ring)
    for k in range(n - 1):
        for s in range(sides):
            a, b, c, d = rings[k][s], rings[k][s + 1], rings[k + 1][s + 1], rings[k + 1][s]
            centre = (path[k] + path[k + 1]) / 2
            M.f([a, b, c, d], smooth=not flat, expect=(M.co[a] + M.co[c]) / 2 - centre)
    if cap:
        for k, sgn in ((0, -1), (n - 1, 1)):
            c = M.v(path[k], rect_uv(rect, 0.5, 0.5), wf(L[k] / tot))
            for s in range(sides):
                M.f([rings[k][s], rings[k][s + 1], c], smooth=False, expect=T[k] * sgn)
    return rings


def torus(M, centre, axis_n, axis_u, R, r, rect, w, seg=10, sides=6):
    axis_n = axis_n.normalized(); axis_u = axis_u.normalized(); axis_v = axis_n.cross(axis_u)
    path = [centre + (axis_u * math.cos(2 * math.pi * k / seg) + axis_v * math.sin(2 * math.pi * k / seg)) * R
            for k in range(seg + 1)]
    tube(M, path, r, rect, w, sides=sides, cap=False)


def solid_outline(M, outline, depth_dir, depth, rect, w, smooth_side=False, bevel_front=0.0):
    """extrude a convex-ish closed 2D outline (3D points, CCW seen from -depth_dir) into a slab; fan-filled caps"""
    n = len(outline)
    c = sum(outline, Vector()) / n
    dd = depth_dir.normalized() * depth
    lo = [M.v(p, rect_uv(rect, 0.1 + 0.8 * k / n, 0.1), w) for k, p in enumerate(outline)]
    hi = [M.v(p + dd, rect_uv(rect, 0.1 + 0.8 * k / n, 0.9), w) for k, p in enumerate(outline)]
    cf = M.v(c - depth_dir.normalized() * bevel_front, rect_uv(rect, 0.5, 0.5), w)
    cb = M.v(c + dd, rect_uv(rect, 0.5, 0.5), w)
    for k in range(n):
        k2 = (k + 1) % n
        M.f([lo[k], lo[k2], cf], smooth=False, expect=-depth_dir)
        M.f([hi[k], hi[k2], cb], smooth=False, expect=depth_dir)
        mid = (outline[k] + outline[k2]) / 2
        M.f([lo[k], lo[k2], hi[k2], hi[k]], smooth=smooth_side, expect=mid - c)


def ribbon_solid(M, outer_pts, inner_pts, normal, depth, rect, w):
    """a flat crescent-like band between two matched polylines, extruded along -normal by depth"""
    n = len(outer_pts)
    dn = normal.normalized()
    F = [[M.v(p, rect_uv(rect, k / (n - 1), 0.0), w) for k, p in enumerate(outer_pts)],
         [M.v(p, rect_uv(rect, k / (n - 1), 0.5), w) for k, p in enumerate(inner_pts)]]
    Bk = [[M.v(p - dn * depth, rect_uv(rect, k / (n - 1), 0.5), w) for k, p in enumerate(outer_pts)],
          [M.v(p - dn * depth, rect_uv(rect, k / (n - 1), 1.0), w) for k, p in enumerate(inner_pts)]]
    for k in range(n - 1):
        M.f([F[0][k], F[0][k + 1], F[1][k + 1], F[1][k]], smooth=False, expect=dn)
        M.f([Bk[0][k], Bk[0][k + 1], Bk[1][k + 1], Bk[1][k]], smooth=False, expect=-dn)
        for side in (0, 1):
            a, b = outer_pts if side == 0 else inner_pts, None
            mid = (F[side][k], F[side][k + 1])
            out = (M.co[F[0][k]] - M.co[F[1][k]]) * (1 if side == 0 else -1)
            M.f([F[side][k], F[side][k + 1], Bk[side][k + 1], Bk[side][k]], smooth=False, expect=out)


def gem(M, centre, front, up, r, h_front, h_back, rect, w, sides=8):
    front = front.normalized(); up = up.normalized(); side = front.cross(up)
    ring = [centre + (up * math.cos(2 * math.pi * k / sides) + side * math.sin(2 * math.pi * k / sides)) * r
            for k in range(sides)]
    table = [centre + front * h_front + (up * math.cos(2 * math.pi * (k + 0.5) / sides) +
                                         side * math.sin(2 * math.pi * (k + 0.5) / sides)) * r * 0.55
             for k in range(sides)]
    gi = [M.v(p, rect_uv(rect, 0.5 + 0.4 * math.cos(2 * math.pi * k / sides), 0.5 + 0.4 * math.sin(2 * math.pi * k / sides)), w)
          for k, p in enumerate(ring)]
    ti = [M.v(p, rect_uv(rect, 0.5 + 0.2 * math.cos(2 * math.pi * (k + .5) / sides), 0.5 + 0.2 * math.sin(2 * math.pi * (k + .5) / sides)), w)
          for k, p in enumerate(table)]
    tc = M.v(centre + front * h_front, rect_uv(rect, 0.5, 0.5), w)
    cu = M.v(centre - front * h_back, rect_uv(rect, 0.5, 0.5), w)
    for k in range(sides):
        k2 = (k + 1) % sides
        M.f([gi[k], gi[k2], ti[k]], smooth=False, expect=front + (ring[k] - centre))
        M.f([ti[k], gi[k2], ti[k2]], smooth=False, expect=front)
        M.f([ti[k], ti[k2], tc], smooth=False, expect=front)
        M.f([gi[k], gi[k2], cu], smooth=False, expect=-front)


def ellipsoid(M, centre, radii, rect, w, seg=10, rings=6, flat=False):
    rx, ry, rz = radii
    rows = []
    for a in range(rings + 1):
        th = math.pi * a / rings - math.pi / 2
        row = []
        for b in range(seg + 1):
            ph = 2 * math.pi * b / seg
            p = centre + Vector((rx * math.cos(th) * math.cos(ph), ry * math.cos(th) * math.sin(ph), rz * math.sin(th)))
            row.append(M.v(p, rect_uv(rect, b / seg, a / rings), w))
        rows.append(row)
    for a in range(rings):
        for b in range(seg):
            q = [rows[a][b], rows[a][b + 1], rows[a + 1][b + 1], rows[a + 1][b]]
            mid = sum((M.co[i] for i in q), Vector()) / 4
            M.f(q, smooth=not flat, expect=mid - centre)


def catenary(p0, p1, sag, n):
    return [p0.lerp(p1, k / (n - 1)) + Vector((0, 0, -sag * 4 * (k / (n - 1)) * (1 - k / (n - 1)))) for k in range(n)]


def chain(M, pts, R, r, rect, w):
    """links along a polyline, alternating 90 degrees"""
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        d = (b - a); c = (a + b) / 2
        side = d.cross(Vector((0, 1, 0))).normalized() if k % 2 == 0 else Vector((0, -1, 0))
        n = d.normalized().cross(side)
        # an oval link: a torus squashed along d
        seg, sides = 10, 5
        u = d.normalized(); v = side
        path = [c + u * (math.cos(2 * math.pi * s / seg) * d.length * 0.62) + v * (math.sin(2 * math.pi * s / seg) * R)
                for s in range(seg + 1)]
        tube(M, path, r, rect, w, sides=sides, cap=False)


# ------------------------------------------------------------------ the drape model
BOX = (2.02, 0.52)   # shoulder line the yoke runs to: torso + arms tops, |x| <= 2.02, |y| <= 0.52
TOP_Z = 1.0


class Drape:
    """cloth from a neckline ellipse: across the shoulder tops (yoke), over the edge (roll), then hanging down.
    u in [0,1] runs from theta_r (character's right) to theta_l (left) around the back. s = arc length down."""

    def __init__(self, A, B, th_r, th_l, hem_z, roll, flare, folds, drift=0.0, thick=0.035, z0=None, hem=None,
                 cy=0.0, fold_seed=1, yoke_min=0.06, cols=None, chain_f=(0.0, 0.3, 0.55, 0.8), nu=48, nv=32,
                 ny=5, nr=4, lift=0.045):
        self.A, self.B, self.th_r, self.th_l = A, B, th_r, th_l
        self.hem_z, self.roll, self.flare, self.folds = hem_z, roll, flare, folds
        self.drift, self.thick, self.cy, self.hem = drift, thick, cy, hem
        self.z0 = z0 if z0 is not None else (lambda th: TOP_Z + thick / 2 + 0.004)
        self.rng = random.Random(fold_seed)
        self.ph = [self.rng.uniform(0, 2 * math.pi) for _ in range(6)]
        self.yoke_min, self.cols, self.chain_f = yoke_min, cols or [], chain_f
        self.nu, self.nv, self.ny, self.nr = nu, nv, ny, nr
        self.lift = lift

    def theta(self, u):
        return math.radians(lerp(self.th_r, self.th_l, u))

    def base(self, u):
        th = self.theta(u)
        c = Vector((self.A * math.cos(th), self.cy + self.B * math.sin(th), 0.0))
        out = Vector((math.cos(th) / self.A, math.sin(th) / self.B, 0.0)).normalized()
        c.z = self.z0(math.degrees(th))
        # yoke: from the neckline to where the ray leaves the shoulder line (a rounded box, so the corners of the
        # shoulders aren't square)
        def inside(t):  # within the torso + arm tops grown by a margin (round outside the corners, never inside)
            p = c + out * t
            dx, dy = max(abs(p.x) - 2.0, 0.0), max(abs(p.y) - 0.5, 0.0)
            return dx * dx + dy * dy < 0.035 ** 2
        lo_t, hi_t = 0.0, 4.0
        if not inside(0.0):
            hi_t = 0.0
        for _ in range(30):
            mid = (lo_t + hi_t) / 2
            lo_t, hi_t = (mid, hi_t) if inside(mid) else (lo_t, mid)
        h = max(self.yoke_min, hi_t)
        return c, out, h, math.degrees(th)

    def parts(self, u):
        c, out, h, thd = self.base(u)
        rc = self.roll(thd)
        # a softer roll over the shoulder corners (back corners of the arm tops)
        cth = math.cos(math.radians(thd)); sth = math.sin(math.radians(thd))
        rc += 0.07 * max(0.0, 1 - abs(abs(cth) - 0.93) / 0.06) * (1 if sth > 0 else 0.5)
        arc = math.pi * rc / 2
        drop = max(0.05, c.z - rc - self.hem_z(thd) + (self.hem(u) if self.hem else 0.0))
        return c, out, h, rc, arc, drop, thd

    def length(self, u):
        c, out, h, rc, arc, drop, thd = self.parts(u)
        return h + arc + drop

    def s_rows(self, u):
        c, out, h, rc, arc, drop, thd = self.parts(u)
        nd = self.nv - self.ny - self.nr
        S = [h * j / self.ny for j in range(self.ny)]
        S += [h + arc * j / self.nr for j in range(self.nr)]
        S += [h + arc + drop * (j / nd) ** 1.08 for j in range(nd + 1)]
        return S

    def point(self, u, s):
        c, out, h, rc, arc, drop, thd = self.parts(u)
        up = Vector((0, 0, 1))
        if s <= h:  # the yoke rises a little toward the neck, where the cloth gathers
            return c + out * s + up * (self.lift * (1 - s / h) ** 2)
        p0 = c + out * h
        if s <= h + arc:
            ph = (s - h) / rc
            return p0 + out * (rc * math.sin(ph)) - up * (rc * (1 - math.cos(ph)))
        q = (s - h - arc) / drop  # 0..1 down the hang
        sd = s - h - arc
        fl = self.flare(thd) * q ** 1.4
        # folds: deeper toward the hem, phase drifting so they don't look combed
        f = self.folds
        g = smooth(0.0, 0.35, q) * (0.35 + 0.65 * q)
        fold = 0.0
        if f:
            n1, amp = f
            fold = amp * g * (math.sin(2 * math.pi * n1 * u + self.ph[0] + 0.8 * q) * 0.75
                              + math.sin(2 * math.pi * (n1 * 1.7) * u + self.ph[1] - 1.3 * q) * 0.35)
        back = Vector((0, 1, 0)) * (self.drift * q * min(1.0, abs(out.x) * 1.2))
        return p0 + out * (rc + fl + fold) - up * (rc + sd) + back

    def grid(self):
        G = []
        for i in range(self.nu + 1):
            u = i / self.nu
            G.append([self.point(u, s) for s in self.s_rows(u)])
        return G

    # skinning
    def col_weights(self, u):
        cols = self.cols
        if not cols:
            return []
        us = [cu for cu, _ in cols]
        if u <= us[0]:
            return [(0, 1.0)]
        if u >= us[-1]:
            return [(len(cols) - 1, 1.0)]
        for k in range(len(us) - 1):
            if us[k] <= u <= us[k + 1]:
                t = (u - us[k]) / (us[k + 1] - us[k])
                t = t * t * (3 - 2 * t)
                return [(k, 1 - t), (k + 1, t)]

    def chain_weights(self, ci, u, s):
        """weights along column ci's chain for a point at arc length s (measured on column u's own profile)"""
        name_h = f"H{ci}"
        _, n_chain = self.cols[ci]
        c, out, h, rc, arc, drop, thd = self.parts(u)
        q = (s - h - arc) / drop
        if n_chain == 0 or q <= 0:
            return {name_h: 1.0}
        f = list(self.chain_f[:n_chain]) + [1.0]
        mids = [(f[k] + f[k + 1]) / 2 for k in range(n_chain)]
        names = [f"C{ci}_{k}" for k in range(n_chain)]
        if q <= mids[0]:
            t = q / mids[0]
            return {name_h: 1 - t, names[0]: t}
        for k in range(n_chain - 1):
            if q <= mids[k + 1]:
                t = (q - mids[k]) / (mids[k + 1] - mids[k])
                return {names[k]: 1 - t, names[k + 1]: t}
        return {names[-1]: 1.0}

    def weights(self, u, s):
        W = {}
        for ci, cw in self.col_weights(u):
            for b, w in self.chain_weights(ci, u, s).items():
                W[b] = W.get(b, 0) + w * cw
        return W

    def weight_grid(self):
        return [[self.weights(i / self.nu, s) for s in self.s_rows(i / self.nu)] for i in range(self.nu + 1)]

    def bones(self, root_head):
        """(name, head, tail, parent) list: Root, a hinge per column at the top, chain bones down the hang"""
        out = [("Root", root_head, root_head + Vector((0, 0, -0.25)), None)]
        for ci, (cu, n_chain) in enumerate(self.cols):
            c, o, h, rc, arc, drop, thd = self.parts(cu)
            top = self.point(cu, h + arc)
            out.append((f"H{ci}", c.copy(), top, "Root"))
            heads = [self.point(cu, h + arc + drop * fk) for fk in self.chain_f[:n_chain]]
            tail_end = self.point(cu, h + arc + drop)
            for k, hd in enumerate(heads):
                tl = heads[k + 1] if k + 1 < len(heads) else tail_end
                out.append((f"C{ci}_{k}", hd, tl, f"H{ci}" if k == 0 else f"C{ci}_{k-1}"))
        return out


def mirror_cols(th_r, th_l, spec):
    """column list from (theta, chain bones) pairs -> (u, n) sorted by u"""
    out = [((th - th_r) / (th_l - th_r), n) for th, n in spec]
    return sorted(out)


# ------------------------------------------------------------------ islands (UV rects, V up)
def L(**rects):
    return rects


# ------------------------------------------------------------------ the five capes
def warden(M, isl):
    """Night Warden's Mantle: shoulder cape to mid-back, standing collar with a brass edge, crimson silk lining,
    brass bosses and a chain clasp with the Warden's key."""
    th_r, th_l = 258.0, -78.0
    D = Drape(A=0.64, B=0.48, th_r=th_r, th_l=th_l,
              hem_z=lambda th: interp([(-80, 0.42), (-30, 0.28), (0, 0.18), (90, -0.32), (180, 0.18), (210, 0.28), (260, 0.42)], th),
              roll=lambda th: interp([(-80, 0.05), (-20, 0.11), (90, 0.07), (200, 0.11), (260, 0.05)], th),
              flare=lambda th: interp([(-80, 0.04), (0, 0.16), (90, 0.2), (180, 0.16), (260, 0.04)], th),
              folds=(7, 0.045), thick=0.04, fold_seed=11, nu=48, nv=22, ny=5, nr=4,
              chain_f=(0.0, 0.5),
              cols=mirror_cols(th_r, th_l, [(-60, 0), (-15, 0), (20, 2), (90, 2), (160, 2), (195, 0), (240, 0)]))
    st = {}
    sheet(M, D.grid(), D.weight_grid(), D.thick, isl["outer"], isl["lining"], isl["rim"], stats=st)
    # standing collar: a band round the neck, front ends at the gap, tilted out a little; wool outside, silk in
    nu, nv = 34, 6
    G, W = [], []
    for i in range(nu + 1):
        th = math.radians(lerp(250, -70, i / nu))
        col, wc = [], []
        for j in range(nv + 1):
            t = j / nv  # 0 top .. 1 base
            hgt = interp([(-70, 0.2), (0, 0.27), (90, 0.34), (180, 0.27), (250, 0.2)], math.degrees(th))
            a, b = 0.72 + 0.05 * (1 - t), 0.66 + 0.06 * (1 - t)
            col.append(Vector((a * math.cos(th), 0.02 + b * math.sin(th), 1.02 + hgt * (1 - t))))
            wc.append({"Root": 1.0})
        G.append(col); W.append(wc)
    sheet(M, G, W, 0.05, isl["collar_out"], isl["collar_in"], isl["rim"])
    # brass edge on the collar top
    edge = [G[i][0] + Vector((0, 0, 0.012)) for i in range(nu + 1)]
    tube(M, edge, 0.02, isl["brass"], {"Root": 1.0}, sides=6)
    # bosses at the front gap and a sagging chain between, the key hanging from it
    bl, br = Vector((0.2, -0.62, 0.92)), Vector((-0.2, -0.62, 0.92))
    for p in (bl, br):
        ellipsoid(M, p, (0.065, 0.025, 0.065), isl["brass"], {"Root": 1.0}, seg=12, rings=6)
    pts = catenary(bl + Vector((0, -0.02, -0.02)), br + Vector((0, -0.02, -0.02)), 0.1, 8)
    chain(M, pts, 0.016, 0.0055, isl["brass"], {"Root": 1.0})
    mid = pts[len(pts) // 2]
    ring_c = mid + Vector((0, -0.005, -0.045))
    torus(M, ring_c, Vector((0, 1, 0)), Vector((1, 0, 0)), 0.03, 0.007, isl["brass"], {"Root": 1.0}, seg=10, sides=5)
    shaft = [ring_c + Vector((0, 0, -0.03)), ring_c + Vector((0, 0, -0.2))]
    tube(M, shaft, 0.01, isl["brass"], {"Root": 1.0}, sides=6)
    bit = ring_c + Vector((0.025, 0, -0.17))
    solid_outline(M, [bit + Vector((-0.02, 0, -0.025)), bit + Vector((0.025, 0, -0.025)), bit + Vector((0.025, 0, 0.02)),
                      bit + Vector((-0.02, 0, 0.02))], Vector((0, 1, 0)), 0.014, isl["brass"], {"Root": 1.0})
    return D, st, Vector((0, 0.3, 1.0))


def reaper(M, isl):
    """Reaper's Tattered Shroud: hooded cloak to the calf, the hood down on the back, a cowl round the neck,
    a torn hem, a silver crescent brooch."""
    th_r, th_l = 188.0, -8.0
    rng = random.Random(404)
    teeth = []
    u = 0.0
    while u < 1.0:   # sawtooth tears: random widths and depths
        w = rng.uniform(0.018, 0.05)
        teeth.append((u, u + w, rng.uniform(0.08, 0.42)))
        u += w

    def hem(u):
        for a, b, dpt in teeth:
            if a <= u <= b:
                t = (u - a) / (b - a)
                return -dpt * (1 - abs(2 * t - 1)) ** 0.7
        return 0.0
    D = Drape(A=0.64, B=0.46, th_r=th_r, th_l=th_l,
              hem_z=lambda th: interp([(-8, -2.1), (40, -2.45), (90, -2.62), (140, -2.45), (188, -2.1)], th),
              roll=lambda th: interp([(-8, 0.12), (40, 0.1), (90, 0.06), (140, 0.1), (188, 0.12)], th),
              flare=lambda th: interp([(-8, 0.36), (90, 0.5), (188, 0.36)], th),
              folds=(8, 0.06), drift=0.28, thick=0.03, fold_seed=4, hem=hem, nu=56, nv=30, ny=5, nr=4,
              cols=mirror_cols(th_r, th_l, [(-8, 4), (35, 4), (90, 4), (145, 4), (188, 4)]))
    st = {}
    sheet(M, D.grid(), D.weight_grid(), D.thick, isl["outer"], isl["lining"], isl["rim"], stats=st)
    # the hood, down: a draped pouch on the upper back, pointed at the bottom, opening toward the neck
    u_back = 0.5
    c0, out0, h0, rc0, arc0, drop0, _ = D.parts(u_back)

    def s_at_z(z):
        return h0 + arc0 + (c0.z - rc0 - z)
    CG = D.grid()
    pts = [p for col in CG[int(D.nu * 0.25):int(D.nu * 0.75) + 1] for p in col if p.y > 0.3]

    def back_y(x, z):
        # the cape's outer surface behind (x, z): average y of the nearest mid-surface points
        near = sorted(pts, key=lambda p: (p.x - x) ** 2 + (p.z - z) ** 2)[:3]
        return sum(p.y for p in near) / len(near) + D.thick / 2
    nu, nv = 22, 14
    G, W = [], []
    for i in range(nu + 1):
        a = lerp(-1.0, 1.0, i / nu)
        col, wc = [], []
        for j in range(nv + 1):
            q = j / nv  # 0 = the opening, 1 = the point
            half = 0.8 * (1 - q) ** 0.85 + 0.03
            x = half * a
            z = 0.99 - 0.06 * (1 - a * a) - q * 0.74 - 0.05 * (1 - a * a) * q
            lift = 0.17 * (1 - a * a) ** 0.7 * (1 - q) ** 0.7          # the opening stands off the back
            lift += 0.06 * (1 - a * a) ** 1.5 * math.sin(math.pi * min(1.0, q * 1.4))  # the cowl of cloth below it
            lift += 0.025 * math.sin(5 * math.pi * a + 3 * q) * (1 - a * a) * (0.3 + q)  # folds
            y = back_y(x, z) - 0.01 + max(0.0, lift)
            col.append(Vector((x, y, z)))
            wc.append(D.weights(u_back, s_at_z(z)))
        G.append(col); W.append(wc)
    sheet(M, G, W, 0.03, isl["hood_out"], isl["hood_in"], isl["rim"], rims=("top",))
    # the rolled lip of the hood's opening
    lip = [G[i][0] for i in range(nu + 1)]
    tube(M, lip, lambda t: 0.035 * (0.4 + 0.6 * math.sin(math.pi * t)), isl["cowl"],
         lambda t: D.weights(u_back, s_at_z(0.95)), sides=7)
    # the cowl: a soft roll of cloth round the back of the neck, ends tucked at the front
    path = []
    for k in range(29):
        th = math.radians(lerp(232, -52, k / 28))
        r = 1 + 0.03 * math.sin(7 * th)
        path.append(Vector((0.8 * r * math.cos(th), 0.02 + 0.73 * r * math.sin(th), 1.1 + 0.015 * math.sin(5 * th))))
    tube(M, path, lambda t: 0.125 * (0.55 + 0.45 * math.sin(math.pi * t)) * (1 + 0.08 * math.sin(19 * t)),
         isl["cowl"], {"Root": 1.0}, sides=10, along=lambda t: t)
    # silver crescent brooch at the right front of the cowl
    cc = Vector((-0.5, -0.67, 1.05))
    outer, inner = [], []
    for k in range(13):
        a = lerp(math.radians(40), math.radians(320), k / 12)
        outer.append(cc + Vector((0.085 * math.cos(a), 0, 0.085 * math.sin(a))))
        ai = lerp(math.radians(62), math.radians(298), k / 12)
        p = Vector((0.03 + 0.07 * math.cos(ai), 0, 0.07 * math.sin(ai)))
        tip = abs(k - 6) / 6
        inner.append(cc + p.lerp(outer[-1] - cc, tip ** 3))
    ribbon_solid(M, outer, inner, Vector((0, -1, 0)), 0.025, isl["silver"], {"Root": 1.0})
    return D, st, Vector((0, 0.3, 1.0))


def duelist(M, isl):
    """Duelist's Shoulder Cape: short crimson velvet cape over the left shoulder, gold-embroidered edge, black satin
    lining, a brass ring brooch and a cord across the chest."""
    th_r, th_l = 124.0, -70.0
    D = Drape(A=0.64, B=0.47, th_r=th_r, th_l=th_l,
              z0=lambda th: TOP_Z + 0.022 - 0.0 * th,
              hem_z=lambda th: interp([(-70, 0.4), (-30, 0.12), (10, -0.32), (55, -0.82), (92, -0.86), (124, -0.42)], th),
              roll=lambda th: interp([(-70, 0.05), (-10, 0.11), (60, 0.09), (124, 0.06)], th),
              flare=lambda th: interp([(-70, 0.03), (0, 0.2), (70, 0.34), (124, 0.22)], th),
              folds=(5, 0.075), drift=0.12, thick=0.035, fold_seed=8, nu=40, nv=28, ny=5, nr=4,
              chain_f=(0.0, 0.35, 0.68),
              cols=mirror_cols(th_r, th_l, [(-70, 0), (-25, 0), (20, 3), (70, 3), (124, 3)]))
    st = {}
    sheet(M, D.grid(), D.weight_grid(), D.thick, isl["outer"], isl["lining"], isl["rim"], stats=st)
    # brass ring brooch on the front-left anchor, and the cord from it across the chest to a ring on the right
    bro = Vector((0.36, -0.6, 0.86))
    torus(M, bro, Vector((0, -1, 0)), Vector((1, 0, 0)), 0.062, 0.016, isl["brass"], {"Root": 1.0}, seg=14, sides=6)
    ellipsoid(M, bro + Vector((0, -0.005, 0)), (0.034, 0.02, 0.034), isl["brass"], {"Root": 1.0}, seg=10, rings=5)
    end = Vector((-0.66, -0.58, 0.36))
    pts = []
    for k in range(17):
        t = k / 16
        p = bro.lerp(end, t)
        p.y = -0.535 - 0.03 * math.sin(math.pi * t) - 0.02
        p.z -= 0.06 * math.sin(math.pi * t)
        pts.append(p)
    tube(M, pts, 0.022, isl["cord"], {"Root": 1.0}, sides=7, twist=60.0)
    torus(M, end + Vector((0, -0.005, 0)), Vector((0, -1, 0)), Vector((1, 0, 0)), 0.045, 0.012, isl["brass"], {"Root": 1.0}, seg=12, sides=6)
    return D, st, Vector((0.3, 0.3, 1.0))


def captain(M, isl):
    """Council Captain's Greatcape: long crimson wool, black velvet lining, brass epaulettes with bullion fringe
    holding it on the shoulders, a turn-down collar, the Council crest embroidered on the back."""
    th_r, th_l = 190.0, -10.0
    D = Drape(A=0.64, B=0.46, th_r=th_r, th_l=th_l,
              hem_z=lambda th: interp([(-10, -2.28), (45, -2.42), (90, -2.5), (135, -2.42), (190, -2.28)], th),
              roll=lambda th: interp([(-10, 0.12), (40, 0.1), (90, 0.06), (140, 0.1), (190, 0.12)], th),
              flare=lambda th: interp([(-10, 0.44), (90, 0.6), (190, 0.44)], th),
              folds=(9, 0.055), drift=0.3, thick=0.04, fold_seed=21, nu=52, nv=30, ny=5, nr=4,
              cols=mirror_cols(th_r, th_l, [(-10, 4), (35, 4), (90, 4), (145, 4), (190, 4)]))
    st = {}
    sheet(M, D.grid(), D.weight_grid(), D.thick, isl["outer"], isl["lining"], isl["rim"], stats=st)
    # turn-down collar: a short flared band
    nu, nv = 34, 5
    G, W = [], []
    for i in range(nu + 1):
        th = math.radians(lerp(228, -48, i / nu))
        col, wc = [], []
        for j in range(nv + 1):
            t = j / nv  # 0 = the top fold, 1 = the outer edge lying on the yoke
            a = lerp(0.74, 0.98, t); b = lerp(0.68, 0.9, t)
            z = 1.05 + 0.2 * math.cos(t * math.pi / 2) ** 1.5 + 0.005
            col.append(Vector((a * math.cos(th), 0.02 + b * math.sin(th), z)))
            wc.append({"Root": 1.0})
        G.append(col); W.append(wc)
    sheet(M, G, W, 0.045, isl["collar_out"], isl["collar_in"], isl["rim"])
    edge = [G[i][nv] + Vector((0, 0, 0.004)) for i in range(nu + 1)]
    tube(M, edge, 0.016, isl["brass"], {"Root": 1.0}, sides=6)
    # epaulettes
    for sgn in (1, -1):
        cx = sgn * 1.68
        # a board: round at the arm end (radius 0.2 about x +0.14), square-ish toward the neck (x -0.3)
        loc = [(0.12 + 0.22 * math.cos(math.radians(a)), 0.22 * math.sin(math.radians(a))) for a in range(-90, 91, 15)]
        loc += [(-0.26, 0.22), (-0.3, 0.18), (-0.3, -0.18), (-0.26, -0.22)]
        outline = [Vector((cx + sgn * x, 0.02 + y, 1.072)) for x, y in loc]
        solid_outline(M, outline, Vector((0, 0, 1)), 0.06, isl["brass"], {"Root": 1.0}, bevel_front=0.0)
        ellipsoid(M, Vector((cx + sgn * 0.02, 0.02, 1.132)), (0.29, 0.17, 0.032), isl["brass"], {"Root": 1.0}, seg=16, rings=6)
        rim_pts = [p + Vector((0, 0, 0.06)) for p in outline] + [outline[0] + Vector((0, 0, 0.06))]
        tube(M, rim_pts, 0.012, isl["brass"], {"Root": 1.0}, sides=5, cap=False)
        ellipsoid(M, Vector((cx - sgn * 0.2, 0.02, 1.16)), (0.045, 0.045, 0.03), isl["brass"], {"Root": 1.0}, seg=10, rings=5)
        # bullion fringe round the arm end, draped over the roll of the cape
        for k in range(11):
            a = math.radians(lerp(-60, 60, k / 10))
            d = Vector((sgn * math.cos(a), math.sin(a), 0))
            e = Vector((cx + sgn * (0.12 + 0.22 * math.cos(a)), 0.02 + 0.22 * math.sin(a), 1.09))
            p1 = e + d * 0.07 + Vector((0, 0, -0.02))
            p2 = e + d * 0.12 + Vector((0, 0, -0.08))
            p2.x = sgn * max(abs(p2.x), 2.19)
            p3 = Vector((p2.x + sgn * 0.012, p2.y * 1.05, 0.77))
            p4 = Vector((p3.x, p3.y, 0.73))
            tube(M, [e, p1, p2, p3, p4], 0.023, isl["fringe"], {"Root": 1.0}, sides=5, twist=40.0)
    return D, st, Vector((0, 0.3, 1.0))


def midnight(M, isl):
    """Midnight Lord's High-Collar Cape: knee length with a bat-wing hem, black velvet over crimson satin, a tall
    fanned collar with silver piping, a silver chain clasp with a crimson gem."""
    th_r, th_l = 190.0, -10.0
    N = 7

    def hem(u):
        fr = (u * N) % 1.0
        return -0.24 * math.sin(math.pi * fr) ** 0.85
    D = Drape(A=0.64, B=0.46, th_r=th_r, th_l=th_l,
              hem_z=lambda th: interp([(-10, -1.62), (45, -1.85), (90, -1.98), (135, -1.85), (190, -1.62)], th),
              roll=lambda th: interp([(-10, 0.12), (40, 0.1), (90, 0.07), (140, 0.1), (190, 0.12)], th),
              flare=lambda th: interp([(-10, 0.36), (90, 0.48), (190, 0.36)], th),
              folds=(N, 0.05), drift=0.25, thick=0.035, fold_seed=31, hem=hem, nu=56, nv=30, ny=5, nr=4,
              cols=mirror_cols(th_r, th_l, [(-10, 4), (35, 4), (90, 4), (145, 4), (190, 4)]))
    st = {}
    sheet(M, D.grid(), D.weight_grid(), D.thick, isl["outer"], isl["lining"], isl["rim"], stats=st)
    # the high collar: fans up and out from the neckline, highest just behind the ears
    nu, nv = 40, 10
    G, W = [], []
    for i in range(nu + 1):
        thd = lerp(245, -65, i / nu)
        th = math.radians(thd)
        hgt = interp([(-65, 0.36), (-20, 0.8), (30, 0.97), (90, 0.84), (150, 0.97), (200, 0.8), (245, 0.36)], thd)
        col, wc = [], []
        for j in range(nv + 1):
            t = 1 - j / nv  # j=0 the top edge, j=nv the base
            fan = 0.07 + 0.36 * t ** 1.9
            a, b = 0.76 + fan, 0.72 + fan * 0.9
            z = 1.03 + hgt * t
            col.append(Vector((a * math.cos(th), 0.03 + b * math.sin(th), z)))
            wc.append({"Root": 1.0})
        G.append(col); W.append(wc)
    sheet(M, G, W, 0.05, isl["collar_out"], isl["collar_in"], isl["rim"])
    tube(M, [G[i][0] for i in range(nu + 1)], 0.018, isl["silver"], {"Root": 1.0}, sides=6)
    tube(M, [G[0][j] for j in range(nv + 1)], 0.016, isl["silver"], {"Root": 1.0}, sides=6)
    tube(M, [G[nu][j] for j in range(nv + 1)], 0.016, isl["silver"], {"Root": 1.0}, sides=6)
    # chain clasp between the collar's front ends, the gem in a silver setting at its middle
    pl, pr = Vector((0.34, -0.68, 1.06)), Vector((-0.34, -0.68, 1.06))
    for p in (pl, pr):
        ellipsoid(M, p, (0.04, 0.02, 0.04), isl["silver"], {"Root": 1.0}, seg=10, rings=5)
    gc = Vector((0, -0.7, 0.9))
    chain(M, catenary(pl, gc + Vector((0.06, 0, 0.02)), 0.03, 5), 0.014, 0.005, isl["silver"], {"Root": 1.0})
    chain(M, catenary(gc + Vector((-0.06, 0, 0.02)), pr, 0.03, 5), 0.014, 0.005, isl["silver"], {"Root": 1.0})
    gem(M, gc, Vector((0, -1, 0)), Vector((0, 0, 1)), 0.055, 0.035, 0.03, isl["gem"], {"Root": 1.0})
    torus(M, gc + Vector((0, 0.005, 0)), Vector((0, -1, 0)), Vector((1, 0, 0)), 0.06, 0.012, isl["silver"], {"Root": 1.0}, seg=14, sides=6)
    return D, st, Vector((0, 0.3, 1.0))


# atlas layouts (u0, v0, u1, v1; V up). Cloth islands get AO; shared hardware islands don't (their UVs overlap).
ROW4 = dict(rim=(0.0, 0.0, 0.42, 0.045), brass=(0.43, 0.0, 0.6, 0.045), silver=(0.61, 0.0, 0.78, 0.045),
            gem=(0.79, 0.0, 0.86, 0.045), cord=(0.87, 0.0, 1.0, 0.045))
CAPES = {
    "WardenMantle": dict(fn=warden, name="Night Warden's Mantle", islands=dict(
        outer=(0.0, 0.42, 1.0, 1.0), lining=(0.0, 0.2, 1.0, 0.41), collar_out=(0.0, 0.05, 0.62, 0.19),
        collar_in=(0.63, 0.05, 1.0, 0.19), **ROW4),
        mats=dict(outer="warden_wool", lining="crimson_silk", collar_out="warden_wool_collar", collar_in="crimson_silk",
                  rim="warden_rim", brass="brass", silver="silver", gem="gem", cord="brass")),
    "ReaperShroud": dict(fn=reaper, name="Reaper's Tattered Shroud", islands=dict(
        outer=(0.0, 0.43, 1.0, 1.0), lining=(0.0, 0.25, 0.6, 0.42), hood_out=(0.61, 0.25, 1.0, 0.42),
        hood_in=(0.61, 0.05, 1.0, 0.24), cowl=(0.0, 0.05, 0.6, 0.24), **ROW4),
        mats=dict(outer="reaper_linen", lining="reaper_lining", hood_out="reaper_linen_hood", hood_in="reaper_lining",
                  cowl="reaper_cowl", rim="reaper_rim", brass="brass", silver="silver", gem="gem", cord="reaper_cowl")),
    "DuelistCape": dict(fn=duelist, name="Duelist's Shoulder Cape", islands=dict(
        outer=(0.0, 0.36, 1.0, 1.0), lining=(0.0, 0.05, 1.0, 0.35), **ROW4),
        mats=dict(outer="duelist_velvet", lining="black_satin", rim="gold_rim", brass="brass", silver="silver",
                  gem="gem", cord="gold_cord")),
    "CaptainGreatcape": dict(fn=captain, name="Council Captain's Greatcape", islands=dict(
        outer=(0.0, 0.42, 1.0, 1.0), lining=(0.0, 0.2, 1.0, 0.41), collar_out=(0.0, 0.05, 0.62, 0.19),
        collar_in=(0.63, 0.05, 0.86, 0.19), fringe=(0.87, 0.05, 1.0, 0.19), **ROW4),
        mats=dict(outer="captain_wool", lining="black_velvet", collar_out="captain_wool_collar", collar_in="black_velvet",
                  fringe="bullion", rim="brass_rim", brass="brass", silver="silver", gem="gem", cord="brass")),
    "MidnightCollar": dict(fn=midnight, name="Midnight Lord's High-Collar Cape", islands=dict(
        outer=(0.0, 0.42, 1.0, 1.0), lining=(0.0, 0.25, 1.0, 0.41), collar_out=(0.0, 0.15, 1.0, 0.24),
        collar_in=(0.0, 0.055, 1.0, 0.14), **ROW4),
        mats=dict(outer="midnight_velvet", lining="crimson_satin", collar_out="midnight_velvet_collar",
                  collar_in="crimson_satin_collar", rim="silver_rim", brass="brass", silver="silver", gem="gem",
                  cord="silver")),
}
NO_AO = {"brass", "silver", "gem", "cord", "fringe", "rim"}


# ------------------------------------------------------------------ Blender objects
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_objects(key, M, bones):
    me = bpy.data.meshes.new("CapeBody")
    me.from_pydata([tuple(c) for c in M.co], [], M.faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        poly.use_smooth = M.smooth[poly.index]
        for li in poly.loop_indices:
            uvl.data[li].uv = M.uv[me.loops[li].vertex_index]
    ob = bpy.data.objects.new("CapeBody", me)
    bpy.context.scene.collection.objects.link(ob)
    arm_d = bpy.data.armatures.new(f"{key}Rig")
    arm = bpy.data.objects.new(f"{key}Rig", arm_d)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, head, tail, parent in bones:
        b = arm_d.edit_bones.new(name)
        b.head, b.tail = head, tail if (tail - head).length > 1e-3 else head + Vector((0, 0, -0.1))
        if parent:
            b.parent = eb[parent]
        eb[name] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    groups = {name: ob.vertex_groups.new(name=name) for name, *_ in bones}
    worst = 0
    for vi, w in enumerate(M.w):
        items = sorted(((b, x) for b, x in w.items() if x > 1e-4), key=lambda t: -t[1])[:4]
        worst = max(worst, len([1 for b, x in w.items() if x > 1e-4]))
        tot = sum(x for _, x in items) or 1.0
        for b, x in items:
            groups[b].add([vi], x / tot, "REPLACE")
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    return ob, arm, worst


def bake_ao(key, ob, size=ATLAS):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 40
    sc.cycles.use_denoising = False
    sc.world = bpy.data.worlds.new("W")
    sc.world.light_settings.distance = 0.35
    img = bpy.data.images.new(f"{key}_ao", size, size, alpha=False)
    mat = bpy.data.materials.new("CapeMat")
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.nodes.active = tex
    ob.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    sc.render.bake.margin = 4
    bpy.ops.object.bake(type="AO", margin=4, use_clear=True)
    img.filepath_raw = os.path.join(OUT, "bake", f"{key}_ao.png")
    img.file_format = "PNG"
    img.save()


def export_fbx(key, ob, arm):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", f"NHCape_{key}.fbx"), use_selection=True,
                             object_types={"MESH", "ARMATURE"}, apply_unit_scale=True, global_scale=0.01,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP",
                             embed_textures=False, add_leaf_bones=False, bake_anim=False, use_armature_deform_only=True)


def build(key):
    reset()
    spec = CAPES[key]
    M = Mesh()
    D, stats, root_head = spec["fn"](M, spec["islands"])
    bones = D.bones(root_head)
    ob, arm, worst = make_objects(key, M, bones)
    xs = [c.x for c in M.co]; ys = [c.y for c in M.co]; zs = [c.z for c in M.co]
    lo = Vector((min(xs), min(ys), min(zs))); hi = Vector((max(xs), max(ys), max(zs)))
    centre = (lo + hi) / 2
    tris = sum(len(f) - 2 for f in M.faces)
    # Roblox torso space of the mesh's bounding-box centre = the CapeBody's CFrame on the torso (NH_TorsoFit)
    fit = [-centre.x, centre.z, centre.y]
    layout = dict(key=key, name=spec["name"], atlas=ATLAS, pad=PAD, islands=spec["islands"], mats=spec["mats"],
                  no_ao=sorted(NO_AO), outer_stats=stats, tris=tris, verts=len(M.co), max_influences=worst,
                  bbox_blender=[list(lo), list(hi)], size_roblox=[hi.x - lo.x, hi.z - lo.z, hi.y - lo.y],
                  torso_fit=fit, bones=[dict(name=n, head=[-h.x, h.z, h.y], parent=p) for n, h, t, p in bones])
    with open(os.path.join(OUT, "layout", f"{key}.json"), "w") as fh:
        json.dump(layout, fh, indent=1)
    if BAKE:
        bake_ao(key, ob)
    export_fbx(key, ob, arm)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{key}.blend"))
    print(f"[capes] {key}: {tris} tris, {len(M.co)} verts, {len(bones)} bones, max infl {worst}, "
          f"size (rbx) {['%.2f' % v for v in layout['size_roblox']]}, fit {['%.3f' % v for v in fit]}")


if __name__ == "__main__":
    for key in CAPES:
        if ONLY is None or key in ONLY:
            build(key)
