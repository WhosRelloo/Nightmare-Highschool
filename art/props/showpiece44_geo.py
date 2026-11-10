"""Props batch 44 (the showpiece kit): geometry for the clothed R6 figures and their effects.

- sweep / ribbon / grid_mesh: tapered tubes (hair locks, tendrils, flames, wisps, lightning), flat bands (staves, trails,
  sashes) and free sheets.
- shell: a rounded-rectangle sleeve of cloth or armour wrapped round an R6 block (sleeves, trouser legs, coat bodies,
  boots, gauntlets), with wrinkle rings at the bends and a flared hem. Built in the R6 rest frame and skinned onto the
  posed figure with Fig.build, so it keeps the blocky R6 silhouette.
- drape: a small verlet cloth simulation in world space (numpy): a sheet pinned along a line (shoulders, waist), pulled
  by gravity and a wind field, colliding with the posed body's boxes and the floor, gathered so it buckles into real
  folds; the frozen result is the cape, cloak or coat skirt.
- effects: spectral flames, rune circles, halos, lightning, wisps, staves, shards, embers, mist.
- gear: sabre, scythe, lantern, book, staff, crown, spray can, key, quill, a blocky spectral wolf, ravens.
"""
import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform, _solid
import nh_props_batch20 as B20
import window_shapes as WS


def _obj(name, bm, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    if smooth:
        for f in bm.faces:
            f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0)


def in_group(g, fn):
    """Build fn() into group g, then go back to the group before."""
    old = P.GROUP
    set_group(g)
    try:
        return fn()
    finally:
        set_group(old)


# ------------------------------------------------------------------ frames along a path

def _frames(pts, up=None):
    """Parallel-transport frames (tangent, normal, binormal) along a polyline."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    T = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        t = (b - a)
        T.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    ref = Vector(up) if up is not None else (Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0)))
    N = [(ref - T[0] * ref.dot(T[0])).normalized()]
    for i in range(1, n):
        nv = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(nv.normalized() if nv.length > 1e-9 else N[-1])
    B = [T[i].cross(N[i]) for i in range(n)]
    return pts, T, N, B


def smooth_path(pts, it=2):
    for _ in range(it):
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            a, b = Vector(a), Vector(b)
            new += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        new.append(Vector(pts[-1]))
        pts = new
    return [Vector(p) for p in pts]


def sweep(name, pts, radius, mat, sides=8, cap=True, flat=1.0, twist=0.0, smooth=2, up=None):
    """A tube along pts whose radius is radius(t) (t 0..1) or a number; flat < 1 squashes the section (a ribbon-ish lock),
    twist turns the section along the path (radians end to end). Tapers to a point when the radius reaches 0."""
    pts = smooth_path(pts, smooth) if smooth else [Vector(p) for p in pts]
    pts, T, N, B = _frames(pts, up)
    rf = radius if callable(radius) else (lambda t, r=radius: r)
    bm = bmesh.new()
    rings = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = i / (n - 1)
        r = max(rf(t), 0.0)
        if r < 1e-4:
            rings.append([bm.verts.new(p)])
            continue
        tw = twist * t
        rg = []
        for k in range(sides):
            a = 2 * math.pi * k / sides + tw
            rg.append(bm.verts.new(p + N[i] * (math.cos(a) * r) + B[i] * (math.sin(a) * r * flat)))
        rings.append(rg)
    for A, Bq in zip(rings, rings[1:]):
        if len(A) == 1 and len(Bq) == 1:
            continue
        for k in range(sides):
            j = (k + 1) % sides
            if len(A) == 1:
                bm.faces.new((A[0], Bq[k], Bq[j]))
            elif len(Bq) == 1:
                bm.faces.new((A[k], A[j], Bq[0]))
            else:
                bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
    if cap:
        for rg, rev in ((rings[0], True), (rings[-1], False)):
            if len(rg) > 2:
                bm.faces.new(list(reversed(rg)) if rev else rg)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mat)


def ribbon(name, pts, width, mat, up=(0, 0, 1), thick=0.03, twist=0.0, smooth=2, normal=None):
    """A flat band along pts, width(t) or a number wide across `up` (or across each point's own normal if given),
    twisting `twist` radians end to end."""
    pts = smooth_path(pts, smooth) if smooth else [Vector(p) for p in pts]
    pts, T, N, Bn = _frames(pts, up)
    wf = width if callable(width) else (lambda t, w=width: w)
    rows = []
    n = len(pts)
    for i, p in enumerate(pts):
        t = i / (n - 1)
        a = twist * t
        side = N[i] * math.cos(a) + Bn[i] * math.sin(a)
        w = max(wf(t), 0.002) / 2
        rows.append([p - side * w, p, p + side * w])
    return grid_mesh(name, rows, mat, thick)


def grid_mesh(name, rows, mat, thick=0.0, keep=None, closed=False):
    """Quads between rows of points (every row the same length). keep(r, c) -> bool drops faces (ragged hems);
    closed joins each row's last point to its first."""
    bm = bmesh.new()
    vs = [[bm.verts.new(tuple(p)) for p in row] for row in rows]
    m = len(rows[0])
    for r, (a, b) in enumerate(zip(vs, vs[1:])):
        for c in range(m if closed else m - 1):
            c2 = (c + 1) % m
            if keep is None or keep(r, c):
                try:
                    bm.faces.new((a[c], a[c2], b[c2], b[c]))
                except ValueError:
                    pass
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    ob = _obj(name, bm, mat)
    if thick:
        _solid(ob, thick)
    return ob


# ------------------------------------------------------------------ cloth shells round the R6 blocks

def rr_pts(hw, hd, r, n=24):
    """A rounded rectangle (half width, half depth, corner radius) as n points, counter-clockwise from +X."""
    r = min(r, hw * 0.95, hd * 0.95)
    per = n // 4
    pts = []
    for q, (cx, cy) in enumerate(((hw - r, hd - r), (-hw + r, hd - r), (-hw + r, -hd + r), (hw - r, -hd + r))):
        for i in range(per):
            a = math.radians(q * 90 + 90 * i / per)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def shell(name, z0, z1, hw, hd, mat, cx=0.0, cy=0.0, r=0.16, n=28, nz=8, flare0=1.0, flare1=1.0, wrinkles=(), seed=1,
          thick=0.04, cap0=False, cap1=False, sag=0.0, front_open=None, taper_y=None, tatter=0):
    """A rounded-rectangle tube of cloth or plate from z0 to z1 round the block centred on (cx, cy):
    flare0 / flare1 scale the section at the bottom / top; wrinkles = [(z, half width, amplitude, rings)] add
    buckled folds round a bend; sag droops the bottom hem at the back (+Y) by that much; front_open = half width of a
    gap left open at the front (-Y) (an open coat); cap0 / cap1 close the ends."""
    rnd = random.Random(seed)
    base = rr_pts(hw, hd, r, n)
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    rows = []
    for j in range(nz + 1):
        t = j / nz
        z = z0 + (z1 - z0) * t
        k = flare0 + (flare1 - flare0) * t
        row = []
        for i, (x, y) in enumerate(base):
            a = math.atan2(y, x)
            amp = 0.0
            for (wz, wh, wa, wn) in wrinkles:
                d = abs(z - wz) / wh
                if d < 1:
                    amp += wa * (1 - d) ** 1.5 * (0.6 + 0.4 * math.sin(a * wn + ph[0] + z * 9.0)) * math.sin((z - wz) / wh * math.pi * 2.0 + a * 1.3 + ph[1])
            kk = k * (1 + amp)
            px, py = x * kk, y * kk
            if taper_y is not None:
                py *= 1 + (taper_y - 1) * t
            zz = z
            if sag and j == 0:
                zz -= sag * max(0.0, y / hd) ** 2
            row.append(Vector((cx + px, cy + py, zz)))
        rows.append(row)
    keep = None
    cut = [int(rnd.random() ** 1.5 * tatter) for _ in range(len(base))]
    if front_open or tatter:
        def keep(rw, c, base=base):
            if tatter and rw < max(cut[c], cut[(c + 1) % len(base)]):
                return False
            if not front_open:
                return True
            x0, y0 = base[c]
            x1, y1 = base[(c + 1) % len(base)]
            return not (y0 < 0 and y1 < 0 and abs((x0 + x1) / 2) < front_open)
    ob = grid_mesh(name, rows, mat, thick, keep=keep, closed=True)
    if cap0 or cap1:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        m = len(base)
        if cap0:
            bm.faces.new([bm.verts[i] for i in range(m)][::-1])
        if cap1:
            bm.faces.new([bm.verts[nz * m + i] for i in range(m)])
        bm.to_mesh(ob.data)
        bm.free()
    return ob


# ------------------------------------------------------------------ the cloth simulation

def _resample(pts, n):
    pts = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1)
        i = max(0, min(len(pts) - 2, next((j for j in range(len(L) - 1) if L[j + 1] >= s), len(pts) - 2)))
        seg = L[i + 1] - L[i]
        u = 0 if seg < 1e-9 else (s - L[i]) / seg
        out.append(pts[i].lerp(pts[i + 1], u))
    return out


def drape(name, top, length, mat, rows=22, cols=26, gather=1.18, wind=(0, 0, 0), gravity=1.0, colliders=(), floor=None,
          thick=0.05, iters=220, turb=0.35, seed=0, outward=None, fold_amp=0.12, fold_period=4.5, ragged=0.0, hem=None,
          wind_curl=0.0, pins_extra=None, smooth=1, stretch=1.0):
    """Hang a sheet from the polyline `top` (world points, pinned) and let it settle.
    length: hanging length (studs); gather: how much wider the cloth is than its pin line (folds buckle out of it);
    wind: a world vector (studs per step^2, relative to gravity 1) growing toward the hem; turb: wind gusts;
    colliders: [(matrix, half extents)] oriented boxes (Fig.colliders); floor: a z the cloth lies on;
    outward: a world direction the folds first buckle toward (default away from the top line's middle, horizontally);
    ragged: 0..1 tears the hem into tatters; hem: (mat, radius) adds a rolled hem tube.
    Returns the object (its grid is kept on ob["nh_rows"] / ["nh_cols"])."""
    rnd = random.Random(seed)
    top = _resample(top, cols)
    dl = length / (rows - 1)
    tw = [(top[min(c + 1, cols - 1)] - top[max(c - 1, 0)]) for c in range(cols)]
    mid = sum(top, Vector()) / cols
    X = np.zeros((rows, cols, 3))
    for c in range(cols):
        t = tw[c].normalized()
        nrm = t.cross(Vector((0, 0, 1)))
        if nrm.length < 1e-6:
            nrm = Vector((0, 1, 0))
        nrm.normalize()
        o = Vector(outward) if outward is not None else (top[c] - mid)
        o.z = 0
        if o.length > 1e-6 and nrm.dot(o) < 0:
            nrm = -nrm
        if outward is not None and nrm.dot(Vector(outward)) < 0:
            nrm = -nrm
        ph = 2 * math.pi * c / fold_period + rnd.uniform(-0.3, 0.3)
        for r in range(rows):
            u = r / (rows - 1)
            off = nrm * (fold_amp * math.sin(ph) * min(1.0, u * 3) + 0.15 * u * length * 0.15)
            X[r, c] = (top[c] + Vector((0, 0, -dl * r)) + off)
    X = X.reshape(-1, 3)
    idx = lambda r, c: r * cols + c  # noqa: E731
    pin = np.zeros(len(X), bool)
    pin[[idx(0, c) for c in range(cols)]] = True
    pinpos = X[pin].copy()
    if pins_extra:
        for (r, c, p) in pins_extra:
            pin[idx(r, c)] = True
        pinpos = None
    hrest = [((top[c + 1] - top[c]).length) * gather for c in range(cols - 1)]
    I, J, R, S = [], [], [], []

    def con(a, b, rest, st):
        I.append(a); J.append(b); R.append(rest); S.append(st)
    for r in range(rows):
        for c in range(cols):
            if c < cols - 1:
                con(idx(r, c), idx(r, c + 1), hrest[c] * (1.0 if r else 1 / gather), 1.0)
            if r < rows - 1:
                con(idx(r, c), idx(r + 1, c), dl * stretch, 1.0)
            if r < rows - 1 and c < cols - 1:
                d = math.hypot(hrest[c], dl)
                con(idx(r, c), idx(r + 1, c + 1), d, 0.5)
                con(idx(r, c + 1), idx(r + 1, c), d, 0.5)
            if r < rows - 2:
                con(idx(r, c), idx(r + 2, c), 2 * dl, 0.12)
            if c < cols - 2:
                con(idx(r, c), idx(r, c + 2), hrest[c] + hrest[c + 1], 0.08)
    I, J, R, S = map(np.array, (I, J, R, S))
    rowfrac = np.repeat(np.arange(rows) / (rows - 1), cols)
    g = np.array([0, 0, -gravity * 0.004 * length])
    wv = np.array(wind, dtype=float) * 0.004 * length
    ph = np.array([rnd.uniform(0, 6.28) for _ in range(3)])
    colm = [(np.array(M.inverted()), np.array(M), np.array(h)) for M, h in colliders]
    prev = X.copy()
    if pins_extra:
        for (r, c, p) in pins_extra:
            X[idx(r, c)] = p
        pinpos = X[pin].copy()
    for it in range(iters):
        acc = np.tile(g, (len(X), 1))
        if np.any(wv):
            gust = 1 + turb * np.sin(X[:, 0] * 1.7 + ph[0] + it * 0.0) * np.cos(X[:, 2] * 1.3 + ph[1])
            acc += np.outer(rowfrac ** 1.3 * gust, wv)
            if wind_curl:
                acc[:, 2] += wind_curl * 0.004 * length * rowfrac ** 2 * np.sin(rowfrac * 3.0 + X[:, 0] * 0.8)
        v = (X - prev) * 0.92
        vn = np.linalg.norm(v, axis=1, keepdims=True)
        v = v * np.minimum(1.0, dl * 0.35 / (vn + 1e-9))
        prev = X.copy()
        X = X + v + acc
        for _ in range(4):
            d = X[J] - X[I]
            L = np.linalg.norm(d, axis=1) + 1e-9
            corr = (d * ((L - R) / L * 0.5 * S)[:, None])
            dX = np.zeros_like(X)
            cnt = np.zeros(len(X))
            np.add.at(dX, I, corr)
            np.add.at(dX, J, -corr)
            np.add.at(cnt, I, 1)
            np.add.at(cnt, J, 1)
            X = X + dX / np.maximum(cnt, 1)[:, None] * 1.6
            X[pin] = pinpos
        for Minv, M, h in colm:
            hp = np.c_[X, np.ones(len(X))]
            loc = (Minv @ hp.T).T[:, :3]
            m = h + 0.02
            inside = np.all(np.abs(loc) < m, axis=1)
            if not inside.any():
                continue
            li = loc[inside]
            pen = m - np.abs(li)
            ax = np.argmin(pen, axis=1)
            li[np.arange(len(li)), ax] = np.sign(li[np.arange(len(li)), ax] + 1e-9) * m[ax]
            X[inside] = (M @ np.c_[li, np.ones(len(li))].T).T[:, :3]
        if floor is not None:
            low = X[:, 2] < floor + thick
            X[low, 2] = floor + thick
            prev[low] = X[low] * 0.5 + prev[low] * 0.5
        X[pin] = pinpos
    G = X.reshape(rows, cols, 3)
    for _ in range(smooth):
        Gs = G.copy()
        Gs[1:-1, 1:-1] = (G[1:-1, 1:-1] * 4 + G[:-2, 1:-1] + G[2:, 1:-1] + G[1:-1, :-2] + G[1:-1, 2:]) / 8
        G = Gs
    keep = None
    if ragged:
        cut = [rows - 1 - int(rnd.random() ** 2 * ragged * rows * 0.45) for _ in range(cols)]
        for c in range(1, cols - 1):
            if rnd.random() < ragged * 0.5:
                cut[c] = min(cut[c], int(rows * (1 - ragged * rnd.uniform(0.2, 0.5))))
        keep = lambda r, c: r < min(cut[c], cut[c + 1] if c + 1 < cols else cut[c])  # noqa: E731
    ob = grid_mesh(name, [[Vector(p) for p in row] for row in G], mat, thick, keep=keep)
    if hem:
        hm, hr = hem
        last = [Vector(G[(cut[c] if ragged else rows - 1) - (1 if ragged else 0), c]) for c in range(cols)] if ragged else \
            [Vector(p) for p in G[-1]]
        if not ragged:
            sweep(name + "Hem", last, hr, hm, sides=6, smooth=1)
    ob["nh_rows"], ob["nh_cols"] = rows, cols
    return ob


# ------------------------------------------------------------------ effects

def flames(prefix, base, h, r, mat, n=5, seed=0, lean=(0, 0, 0), spread=None, sides=7):
    """Spectral flames: n licking tongues rising from base, each a curling tapered tube, the middle one tallest."""
    rnd = random.Random(seed)
    base = Vector(base)
    spread = r * 0.9 if spread is None else spread
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.uniform(-0.3, 0.3)
        d = 0 if k == 0 else spread * rnd.uniform(0.4, 1.0)
        p0 = base + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        hh = h * (1.0 if k == 0 else rnd.uniform(0.45, 0.8))
        ph = rnd.uniform(0, 6.28)
        pts = []
        for i in range(7):
            t = i / 6
            w = math.sin(t * 3.4 + ph) * r * 0.45 * t
            pts.append(p0 + Vector(lean) * t * t * hh + Vector((w * math.cos(a + 1.5), w * math.sin(a + 1.5), hh * t)))
        rr = r * (1.0 if k == 0 else rnd.uniform(0.45, 0.7))
        sweep(f"{prefix}{k}", pts, lambda t, rr=rr: rr * (math.sin(min(1, t * 1.25 + 0.15) * math.pi) ** 0.8) * (1 - t) ** 0.4,
              mat, sides=sides, smooth=1, twist=rnd.uniform(-1.5, 1.5), flat=0.75)


def wisp(name, center, radius, z0, z1, mat, turns=1.2, r0=0.08, r1=0.0, phase=0.0, flat=0.35, wobble=0.15, sides=6, n=24):
    """A ghostly wisp frozen mid-swirl: a tapered, flattened tube spiralling up round center (its x, y; z0..z1 absolute)."""
    c = Vector((center[0], center[1], 0.0))
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = phase + turns * 2 * math.pi * t
        rr = radius * (1 + wobble * math.sin(t * 7 + phase))
        pts.append(c + Vector((math.cos(a) * rr, math.sin(a) * rr, z0 + (z1 - z0) * t)))
    return sweep(name, pts, lambda t: r0 + (r1 - r0) * t if t < 0.92 else (r0 + (r1 - r0) * t) * (1 - t) / 0.08, mat, sides=sides,
                 flat=flat, smooth=1)


def trail(name, pts, w0, w1, mat, up=(0, 0, 1), thick=0.02, twist=0.0):
    """A speed or ribbon trail: a band narrowing from w0 to w1."""
    return ribbon(name, pts, lambda t: w0 + (w1 - w0) * t, mat, up=up, thick=thick, twist=twist)


def rune_circle(prefix, c, R, mat, n=12, seed=0, star=5, depth=0.03, z=None, inner=0.78):
    """An arcane sigil laid flat at c: two rings, a star polygon in the middle and glyphs between the rings."""
    rnd = random.Random(seed)
    c = Vector(c)
    zz = c.z if z is None else z
    hoop(f"{prefix}Outer", (c.x, c.y, zz), R, "Z", mat, thick=depth)
    hoop(f"{prefix}Inner", (c.x, c.y, zz), R * inner, "Z", mat, thick=depth * 0.8)
    hoop(f"{prefix}Core", (c.x, c.y, zz), R * 0.2, "Z", mat, thick=depth * 0.7)
    if star:
        k = 2 if star >= 5 else 1
        pts = [(c.x + math.cos(math.pi / 2 + 2 * math.pi * i * k / star) * R * inner * 0.97,
                c.y + math.sin(math.pi / 2 + 2 * math.pi * i * k / star) * R * inner * 0.97, zz) for i in range(star + 1)]
        tube(f"{prefix}Star", pts, depth * 0.8, mat, poly=True)
    mid = R * (1 + inner) / 2
    gh = R * (1 - inner) * 0.36
    for i in range(n):
        a = 2 * math.pi * i / n
        cx, cy = c.x + math.cos(a) * mid, c.y + math.sin(a) * mid
        tdir = Vector((-math.sin(a), math.cos(a), 0))
        rdir = Vector((math.cos(a), math.sin(a), 0))
        kind = rnd.randrange(5)
        p = Vector((cx, cy, zz))
        if kind == 0:   # a crossed staff
            segs = [(-rdir * gh, rdir * gh), (-tdir * gh * 0.6 + rdir * gh * 0.3, tdir * gh * 0.6 + rdir * gh * 0.3)]
        elif kind == 1:  # an eye
            segs = [(-tdir * gh, rdir * gh * 0.4), (rdir * gh * 0.4, tdir * gh), (tdir * gh, -rdir * gh * 0.4), (-rdir * gh * 0.4, -tdir * gh)]
        elif kind == 2:  # a fork
            segs = [(-rdir * gh, rdir * gh * 0.2), (rdir * gh * 0.2, rdir * gh + tdir * gh * 0.5), (rdir * gh * 0.2, rdir * gh - tdir * gh * 0.5)]
        elif kind == 3:  # a crescent made of three strokes
            segs = [(-tdir * gh + rdir * gh * 0.2, -rdir * gh * 0.5), (-rdir * gh * 0.5, tdir * gh + rdir * gh * 0.2), (rdir * gh, rdir * gh * 0.3)]
        else:            # a hooked rune
            segs = [(-rdir * gh - tdir * gh * 0.3, rdir * gh - tdir * gh * 0.3), (rdir * gh - tdir * gh * 0.3, tdir * gh * 0.5)]
        for j, (a0, a1) in enumerate(segs):
            tube(f"{prefix}G{i}_{j}", [tuple(p + a0), tuple(p + a1)], depth * 0.75, mat, poly=True, square=True)


def halo(prefix, c, R, normal, mat, rays=0, ray_len=0.4, thick=0.05, spikes=False):
    """A halo ring at c facing `normal`, with optional rays (or spikes) round it."""
    c = Vector(c)
    s = _mark()
    hoop(f"{prefix}Ring", (0, 0, 0), R, "Z", mat, thick=thick)
    for i in range(rays):
        a = 2 * math.pi * i / rays
        d = Vector((math.cos(a), math.sin(a), 0))
        L = ray_len * (1.0 if i % 2 == 0 else 0.6)
        if spikes:
            cone(f"{prefix}Spike{i}", thick * 1.5, 0.0, L, tuple(d * (R + L / 2)), mat, verts=4,
                 rot=Vector((0, 0, 1)).rotation_difference(d).to_euler())
        else:
            tube(f"{prefix}Ray{i}", [tuple(d * (R + thick * 2)), tuple(d * (R + L))], thick * 0.5, mat, poly=True)
    _xform(s, Matrix.Translation(c) @ Vector((0, 0, 1)).rotation_difference(Vector(normal).normalized()).to_matrix().to_4x4())


def lightning(prefix, a, b, mat, seed=0, r=0.05, jag=0.35, segs=9, branches=2):
    """A frozen lightning bolt from a to b: a jagged, tapering strike with forked branches."""
    rnd = random.Random(seed)
    a, b = Vector(a), Vector(b)
    d = b - a
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    up2 = d.cross(side).normalized()
    pts = [a]
    for i in range(1, segs):
        t = i / segs
        pts.append(a + d * t + side * rnd.uniform(-jag, jag) + up2 * rnd.uniform(-jag, jag) * 0.6)
    pts.append(b)
    sweep(f"{prefix}Bolt", pts, lambda t: r * (1 - 0.6 * t), mat, sides=5, smooth=0)
    for k in range(branches):
        i = rnd.randrange(2, segs - 1)
        p0 = pts[i]
        L = d.length * rnd.uniform(0.15, 0.3)
        dirv = (d.normalized() + side * rnd.uniform(-1, 1) + up2 * rnd.uniform(-0.6, 0.6)).normalized()
        bp = [p0]
        for j in range(1, 4):
            bp.append(p0 + dirv * L * j / 3 + side * rnd.uniform(-jag, jag) * 0.4)
        sweep(f"{prefix}Fork{k}", bp, lambda t: r * 0.55 * (1 - t), mat, sides=4, smooth=0)
    return pts


def crystal(name, c, size, mat, axis=(0, 0, 1), sides=5, tip=1.6, seed=0):
    """A floating shard: an elongated bipyramid crystal."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    top = bm.verts.new((0, 0, size * tip))
    bot = bm.verts.new((0, 0, -size * tip * 0.6))
    ring_ = [bm.verts.new((math.cos(2 * math.pi * i / sides) * size * rnd.uniform(0.35, 0.5),
                           math.sin(2 * math.pi * i / sides) * size * rnd.uniform(0.35, 0.5), size * rnd.uniform(-0.1, 0.2))) for i in range(sides)]
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((ring_[i], ring_[j], top))
        bm.faces.new((ring_[j], ring_[i], bot))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, mat, smooth=False)
    ob.matrix_world = Matrix.Translation(c) @ Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
    return ob


def shards(prefix, center, n, spread, size, mat, seed=0, up=0.5, zmin=None):
    rnd = random.Random(seed)
    c = Vector(center)
    for i in range(n):
        p = c + Vector((rnd.uniform(-1, 1) * spread, rnd.uniform(-1, 1) * spread * 0.7, rnd.uniform(-0.3, 1) * spread * up))
        if zmin is not None:
            p.z = max(p.z, zmin)
        ax = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 1)))
        crystal(f"{prefix}{i}", p, size * rnd.uniform(0.5, 1.2), mat, ax, sides=rnd.choice((4, 5)), seed=seed * 31 + i)


def embers(prefix, center, n, spread, mat, seed=0, size=0.045, rise=1.0):
    rnd = random.Random(seed)
    c = Vector(center)
    for i in range(n):
        p = c + Vector((rnd.gauss(0, spread * 0.5), rnd.gauss(0, spread * 0.5), rnd.random() * spread * rise))
        crystal(f"{prefix}{i}", p, size * rnd.uniform(0.6, 1.3), mat, (rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1), sides=3, tip=1.0, seed=i)


def mist(prefix, center, n, spread, size, mat, seed=0, flat=0.55, rise=0.4):
    """Billowing mist or ectoplasm: overlapping squashed blobs (a _Glass piece in Roblox)."""
    rnd = random.Random(seed)
    c = Vector(center)
    for i in range(n):
        a = rnd.uniform(0, 6.28)
        d = spread * math.sqrt(rnd.random())
        p = c + Vector((math.cos(a) * d, math.sin(a) * d, rnd.random() * size * rise * 3))
        s = size * rnd.uniform(0.55, 1.15) * (1.15 - 0.5 * d / max(spread, 1e-6))
        sphere(f"{prefix}{i}", s, tuple(p), mat, seg=10, rings=6, scale=(rnd.uniform(1.0, 1.5), rnd.uniform(1.0, 1.4), flat))


def staves(prefix, center, radius, z0, z1, mat, turns=1.1, phase=0.0, lines=5, gap=0.07, notes=9, seed=0, note_mat=None):
    """Spectral music: a five-line stave spiralling up round center (x, y; z0..z1 absolute) with note heads and stems."""
    rnd = random.Random(seed)
    c = Vector((center[0], center[1], 0.0))
    n = 30
    base = []
    for i in range(n):
        t = i / (n - 1)
        a = phase + turns * 2 * math.pi * t
        rr = radius * (1 + 0.12 * math.sin(t * 5 + phase))
        base.append((a, rr, z0 + (z1 - z0) * t + 0.25 * math.sin(t * 9 + phase)))
    for k in range(lines):
        off = (k - (lines - 1) / 2) * gap
        pts = [c + Vector((math.cos(a) * rr, math.sin(a) * rr, z + off)) for a, rr, z in base]
        sweep(f"{prefix}L{k}", pts, lambda t: 0.012 * min(1, t * 8, (1 - t) * 8), mat, sides=4, smooth=1)
    nm = note_mat or mat
    for j in range(notes):
        t = (j + 0.5) / notes
        i = int(t * (n - 1))
        a, rr, z = base[i]
        zz = z + gap * rnd.choice((-2, -1, 0, 1, 2)) * 0.9
        p = c + Vector((math.cos(a) * rr, math.sin(a) * rr, zz))
        out = Vector((math.cos(a), math.sin(a), 0))
        ob = sphere(f"{prefix}N{j}", 0.07, tuple(p + out * 0.02), nm, seg=8, rings=4, scale=(1.3, 1.3, 0.85))
        ob.rotation_euler = (0, 0.4, a)
        tube(f"{prefix}S{j}", [tuple(p + out * 0.02 + Vector((math.sin(a) * 0.07, -math.cos(a) * 0.07, 0))),
                               tuple(p + out * 0.02 + Vector((math.sin(a) * 0.07, -math.cos(a) * 0.07, 0.32)))], 0.012, nm, poly=True)
        if rnd.random() < 0.5:
            tube(f"{prefix}F{j}", [tuple(p + out * 0.02 + Vector((math.sin(a) * 0.07, -math.cos(a) * 0.07, 0.32))),
                                   tuple(p + out * 0.1 + Vector((math.sin(a) * 0.2, -math.cos(a) * 0.2, 0.2)))], 0.012, nm, poly=True)


# ------------------------------------------------------------------ gear and props in hand (built at the origin, placed by matrix)

def place(s, at, aim=(0, 0, 1), roll=0.0):
    """Move parts built since mark s from the origin (their axis +Z) to `at`, pointing +Z along `aim`, rolled about it."""
    R = Vector((0, 0, 1)).rotation_difference(Vector(aim).normalized()).to_matrix().to_4x4()
    _xform(s, Matrix.Translation(at) @ R @ Matrix.Rotation(roll, 4, "Z"))


def sabre(prefix, K, blade="blade", L=3.2, curve=0.25, guard="gold", grip="leather_black", glow=None):
    """A cavalry sabre along +Z from the grip at the origin: a curved single-edged blade with a fuller, a stirrup guard
    and a bound grip; glow puts a second, glowing edge along the blade (a group name)."""
    pts = [Vector((curve * (t * t) * L * 0.3, 0, 0.35 + t * L)) for t in [i / 10 for i in range(11)]]
    rows = []
    for i, p in enumerate(pts):
        t = i / 10
        w = 0.16 * (1 - t ** 3) + 0.01
        rows.append([p + Vector((-w * 0.2, 0, 0)), p + Vector((w, 0, 0))])
    grid_mesh(f"{prefix}Blade", rows, K[blade], 0.035)
    if glow:
        in_group(glow, lambda: sweep(f"{prefix}Edge", [p + Vector((0.17 * (1 - (i / 10) ** 3) + 0.02, 0, 0)) for i, p in enumerate(pts)],
                                     lambda t: 0.035 * (1 - t * 0.7), K["glowmat"], sides=5, smooth=1))
    tube(f"{prefix}Guard", [(-0.05, 0, 0.32), (0.25, 0, 0.36), (0.33, 0, 0.1), (0.2, 0, -0.42), (0.05, 0, -0.48)], 0.028, K[guard])
    box(f"{prefix}Quillon", (0.4, 0.07, 0.07), (-0.1, 0, 0.33), K[guard], bevel=0.02)
    cyl(f"{prefix}Grip", 0.07, 0.75, (0, 0, -0.05), K[grip], verts=10)
    for k in range(3):
        hoop(f"{prefix}Wire{k}", (0, 0, -0.3 + k * 0.22), 0.072, "Z", K[guard], thick=0.01)
    sphere(f"{prefix}Pommel", 0.1, (0, 0, -0.48), K[guard], seg=10, rings=6)


def scythe(prefix, K, L=6.0, blade=2.6, glow=None):
    """A reaper's scythe along +Z: a snaithe of dark wood with two grips and iron bands, a long hooked blade at the top
    curving to -X, a skull boss at the tang."""
    tube(f"{prefix}Shaft", [(0, 0, 0), (0.08, 0, L * 0.35), (-0.05, 0, L * 0.7), (0, 0, L)], 0.07, K["ebony"])
    for z in (L * 0.45, L * 0.75):
        tube(f"{prefix}Nib{z:.1f}", [(0.0, 0, z), (0.4, 0, z + 0.05)], 0.05, K["ebony"], poly=True)
        hoop(f"{prefix}Band{z:.1f}", (0, 0, z), 0.08, "Z", K["iron"], thick=0.02)
    pts = []
    for i in range(14):
        t = i / 13
        a = math.radians(-8 - 150 * t ** 1.1)
        pts.append(Vector((-math.sin(-a) * blade * 0.55 * t - blade * 0.45 * t, 0, L - 0.05 + math.sin(t * math.pi) * 0.55 - t * 0.6)))
    rows = []
    for i, p in enumerate(pts):
        t = i / 13
        w = 0.42 * (1 - t) ** 0.7 + 0.01
        rows.append([p, p + Vector((0, 0, -w))])
    grid_mesh(f"{prefix}Blade", rows, K["blade"], 0.04)
    if glow:
        in_group(glow, lambda: sweep(f"{prefix}Edge", [p + Vector((0, 0, -0.43 * (1 - i / 13) ** 0.7 - 0.02)) for i, p in enumerate(pts)],
                                     lambda t: 0.035 * (1 - 0.8 * t), K["glowmat"], sides=5, smooth=1))
    box(f"{prefix}Tang", (0.3, 0.16, 0.36), (0, 0, L - 0.15), K["iron"], bevel=0.04)
    sphere(f"{prefix}Skull", 0.16, (0.05, -0.14, L - 0.2), K["bone"], seg=10, rings=6, scale=(1, 0.9, 1.1))


def lantern(prefix, K, s=1.0, glow="Glow", glass="Glass", flame_n=4, seed=0):
    """A watchman's lantern hanging below the origin (its ring at 0): an iron cage on a pointed roof, glass panes
    (Glass) round a tall spectral flame (Glow)."""
    hoop(f"{prefix}Ring", (0, 0, -0.12 * s), 0.12 * s, "Y", K["iron"], thick=0.025 * s)
    lathe(f"{prefix}Roof", [(0, -0.22 * s), (0.08 * s, -0.3 * s), (0.36 * s, -0.55 * s), (0.4 * s, -0.6 * s), (0, -0.6 * s)], K["iron"], seg=6)
    lathe(f"{prefix}Base", [(0, -1.45 * s), (0.38 * s, -1.45 * s), (0.36 * s, -1.33 * s), (0.3 * s, -1.3 * s), (0, -1.3 * s)], K["iron"], seg=6)
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, y = math.cos(a) * 0.33 * s, math.sin(a) * 0.33 * s
        tube(f"{prefix}Bar{k}", [(x, y, -0.6 * s), (x, y, -1.32 * s)], 0.022 * s, K["iron"], poly=True)
    if glass:
        in_group(glass, lambda: lathe(f"{prefix}Pane", [(0.31 * s, -1.3 * s), (0.31 * s, -0.6 * s)], K["glassmat"], seg=6))
    in_group(glow, lambda: flames(f"{prefix}Flame", (0, 0, -1.28 * s), 0.62 * s, 0.13 * s, K["glowmat"], n=flame_n, seed=seed))


def book(prefix, K, w=0.9, d=1.2, t=0.28, cover="leather_oxblood", open_=False, clasp="gold"):
    """A grimoire at the origin (lying in XY, spine along Y at -X when closed). open_: spread pages."""
    if open_:
        for sx in (-1, 1):
            box(f"{prefix}Cover{sx}", (w, d, 0.04), (sx * w / 2, 0, 0.02), K[cover], bevel=0.015, rot=(0, -sx * 0.12, 0))
            rows = []
            for i in range(7):
                u = i / 6
                x = sx * (0.04 + u * (w - 0.1))
                z = 0.05 + 0.12 * math.sin(u * math.pi * 0.9) + 0.03 * (1 - u)
                rows.append([Vector((x, -d / 2 + 0.05, z)), Vector((x, d / 2 - 0.05, z))])
            grid_mesh(f"{prefix}Pages{sx}", rows, K["parchment"], 0.05)
        box(f"{prefix}Spine", (0.1, d, 0.06), (0, 0, 0.0), K[cover], bevel=0.02)
    else:
        box(f"{prefix}Cover", (w, d, t), (0, 0, t / 2), K[cover], bevel=0.03)
        box(f"{prefix}Block", (w - 0.04, d - 0.06, t - 0.06), (0.03, 0, t / 2), K["parchment"], bevel=0.01)
        for k in range(4):
            box(f"{prefix}Band{k}", (0.06, 0.06, t + 0.02), (-w / 2, -d * 0.35 + k * d * 0.23, t / 2), K[cover], bevel=0.02)
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(f"{prefix}Corner{sx}{sy}", (0.16, 0.16, t + 0.02), (sx * (w / 2 - 0.06), sy * (d / 2 - 0.06), t / 2), K[clasp], bevel=0.02)
        sphere(f"{prefix}Boss", 0.12, (0, 0, t), K[clasp], seg=10, rings=5, scale=(1, 1, 0.4))


def crown(prefix, K, c, r=0.62, h=0.42, points=7, metal="gold", gems=("ruby",), tilt=(0, 0, 0)):
    """A circlet crown: a band with a rope edge, pointed tines tipped with pearls, gems set round it."""
    s = _mark()
    lathe(f"{prefix}Band", [(r, 0), (r + 0.03, 0.02), (r + 0.03, h * 0.38), (r, h * 0.42), (r - 0.04, h * 0.42), (r - 0.04, 0)], K[metal], seg=28)
    for k in range(points):
        a = 2 * math.pi * k / points
        x, y = math.cos(a) * (r + 0.01), math.sin(a) * (r + 0.01)
        tall = h * (1.0 if k % 2 == 0 else 0.7)
        cone(f"{prefix}Tine{k}", 0.1, 0.0, tall, (x, y, h * 0.4 + tall / 2), K[metal], verts=4, rot=(0, 0, a + math.pi / 4))
        sphere(f"{prefix}Pearl{k}", 0.045, (x, y, h * 0.4 + tall + 0.02), K["moonstone"], seg=8, rings=4)
        g = gems[k % len(gems)]
        ob = sphere(f"{prefix}Gem{k}", 0.065, (math.cos(a + math.pi / points) * (r + 0.04), math.sin(a + math.pi / points) * (r + 0.04), h * 0.2), K[g],
                    seg=6, rings=3, scale=(1, 1, 1.3))
    _xform(s, Matrix.Translation(c) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))


def raven(prefix, K, at, heading=0.0, wings=0.8, s=1.0, mat="feather", eye=None, beak="iron"):
    """A raven in flight (wings up by `wings` 0..1) or gliding, built of feather blades, heading (radians about Z, 0 = +X)."""
    st = _mark()
    m = K[mat]
    sphere(f"{prefix}Body", 1.0, (0, 0, 0), m, seg=10, rings=6, scale=(0.32 * s, 0.13 * s, 0.13 * s))
    sphere(f"{prefix}Head", 0.1 * s, (0.3 * s, 0, 0.05 * s), m, seg=10, rings=6)
    cone(f"{prefix}Beak", 0.04 * s, 0.0, 0.16 * s, (0.44 * s, 0, 0.04 * s), K[beak], verts=5, rot=(0, math.pi / 2 + 0.15, 0))
    if eye:
        in_group(eye, lambda: [sphere(f"{prefix}Eye{sy}", 0.022 * s, (0.36 * s, sy * 0.07 * s, 0.08 * s), K["glowmat"], seg=6, rings=3)
                                for sy in (-1, 1)])
    for sy in (-1, 1):
        for k in range(6):
            t = k / 5
            L = (0.55 + 0.35 * math.sin(t * 2.2)) * s
            ang = math.radians(-10 + 50 * t) * sy
            lift = wings * (0.6 + 0.4 * t)
            p0 = Vector((0.08 * s - t * 0.22 * s, sy * 0.08 * s, 0.02 * s))
            dirv = Vector((-math.sin(abs(ang)) * 0.6, sy * math.cos(ang), lift)).normalized()
            B20.tprism(f"{prefix}F{sy}{k}", WS.ccw([(0, 0), (L * 0.5, 0.09 * s), (L, 0.03 * s), (L * 0.95, -0.03 * s), (L * 0.4, -0.06 * s)]),
                       0, 0.025 * s, m)
            ob = P.PARTS[-1]
            ob.matrix_world = Matrix.Translation(p0) @ Vector((1, 0, 0)).rotation_difference(dirv).to_matrix().to_4x4()
    for k in range(5):
        a = math.radians(-24 + 12 * k)
        B20.tprism(f"{prefix}T{k}", WS.ccw([(0, -0.05 * s), (0.42 * s, -0.07 * s), (0.45 * s, 0.07 * s), (0, 0.05 * s)]), 0, 0.02 * s, m)
        P.PARTS[-1].matrix_world = Matrix.Translation((-0.25 * s, 0, 0)) @ Matrix.Rotation(math.pi + a, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
    _xform(st, Matrix.Translation(at) @ Matrix.Rotation(heading, 4, "Z"))


def ghost_wolf(prefix, mat, M, howl=True, s=1.0):
    """A blocky spectral wolf in the R6 manner (boxes and wedges), rearing with its head thrown back when howl;
    built facing -Y with its paws at the origin, placed by M."""
    st = _mark()
    box(f"{prefix}Chest", (1.7 * s, 1.8 * s, 1.7 * s), (0, 0, 2.2 * s), mat, bevel=0.25 * s)
    box(f"{prefix}Belly", (1.4 * s, 2.0 * s, 1.3 * s), (0, 1.5 * s, 1.75 * s), mat, bevel=0.25 * s, rot=(-0.35, 0, 0))
    box(f"{prefix}Haunch", (1.5 * s, 1.4 * s, 1.4 * s), (0, 2.6 * s, 1.0 * s), mat, bevel=0.25 * s)
    for sx in (-1, 1):
        box(f"{prefix}Fore{sx}", (0.5 * s, 0.5 * s, 2.0 * s), (sx * 0.55 * s, -0.55 * s, 1.2 * s), mat, bevel=0.12 * s, rot=(0.25, 0, 0))
        box(f"{prefix}Paw{sx}", (0.6 * s, 0.75 * s, 0.3 * s), (sx * 0.55 * s, -0.95 * s, 0.15 * s), mat, bevel=0.1 * s)
        box(f"{prefix}Hind{sx}", (0.55 * s, 0.9 * s, 1.0 * s), (sx * 0.6 * s, 2.7 * s, 0.4 * s), mat, bevel=0.12 * s)
    ns = _mark()
    box(f"{prefix}Head", (1.2 * s, 1.2 * s, 1.1 * s), (0, 0, 0), mat, bevel=0.2 * s)
    box(f"{prefix}Snout", (0.6 * s, 1.0 * s, 0.5 * s), (0, -0.95 * s, -0.2 * s), mat, bevel=0.12 * s)
    box(f"{prefix}Jaw", (0.5 * s, 0.85 * s, 0.22 * s), (0, -0.85 * s, -0.62 * s), mat, bevel=0.08 * s, rot=(0.45 if howl else 0.1, 0, 0))
    for sx in (-1, 1):
        cone(f"{prefix}Ear{sx}", 0.3 * s, 0.0, 0.7 * s, (sx * 0.38 * s, 0.2 * s, 0.85 * s), mat, verts=4, rot=(0.2, sx * 0.2, math.pi / 4))
    _xform(ns, Matrix.Translation((0, -0.8 * s, 3.45 * s)) @ Matrix.Rotation(math.radians(-55 if howl else -5), 4, "X"))
    tail = [Vector((0, 3.2 * s, 1.4 * s)), Vector((0, 4.0 * s, 1.9 * s)), Vector((0, 4.6 * s, 1.4 * s)), Vector((0.3 * s, 5.0 * s, 0.6 * s))]
    sweep(f"{prefix}Tail", tail, lambda t: 0.35 * s * (1 - t) + 0.05, mat, sides=6)
    for k in range(7):
        a = -0.9 + k * 0.3
        cone(f"{prefix}Ruff{k}", 0.3 * s, 0.0, 0.8 * s, (math.sin(a) * 0.85 * s, -0.5 * s, 2.9 * s - abs(a) * 0.3 * s), mat, verts=4,
             rot=(-0.9, a * 0.8, 0))
    _xform(st, M)


def spray_can(prefix, K):
    cyl(f"{prefix}Can", 0.13, 0.5, (0, 0, 0.25), K["spraycan"], verts=14)
    lathe(f"{prefix}Dome", [(0.13, 0.5), (0.1, 0.58), (0.04, 0.62), (0, 0.62)], K["silver"], seg=14)
    box(f"{prefix}Nozzle", (0.06, 0.06, 0.08), (0, -0.02, 0.66), K["enamel_black"], bevel=0.01)


def staff(prefix, K, L=5.5, head="moonstone", glow=None):
    """A tall staff along +Z: a twisted dark shaft with gilt bands, an iron claw at the top holding an orb."""
    pts = [Vector((0.04 * math.sin(i * 1.3), 0.04 * math.cos(i * 1.3), L * i / 12)) for i in range(13)]
    sweep(f"{prefix}Shaft", pts, lambda t: 0.08 - 0.02 * t, K["ebony"], sides=7)
    for z in (L * 0.3, L * 0.62, L * 0.9):
        hoop(f"{prefix}Band{z:.1f}", (0, 0, z), 0.085, "Z", K["gilt"], thick=0.025)
    for k in range(4):
        a = k * math.pi / 2
        tube(f"{prefix}Claw{k}", [(0, 0, L), (math.cos(a) * 0.2, math.sin(a) * 0.2, L + 0.2), (math.cos(a) * 0.15, math.sin(a) * 0.15, L + 0.5)], 0.03, K["iron"])
    if glow:
        in_group(glow, lambda: sphere(f"{prefix}Orb", 0.2, (0, 0, L + 0.32), K["glowmat"], seg=14, rings=8))
    else:
        sphere(f"{prefix}Orb", 0.2, (0, 0, L + 0.32), K[head], seg=14, rings=8)


def quill(prefix, K, L=1.6, mat="feather"):
    """A long quill along +Z: a shaft and a curved vane."""
    tube(f"{prefix}Shaft", [(0, 0, 0), (0.05, 0, L * 0.5), (0.18, 0, L)], 0.02, K["bone"])
    rows = []
    for i in range(9):
        t = i / 8
        p = Vector((0.18 * t * t, 0, L * (0.2 + 0.8 * t)))
        w = 0.18 * math.sin(t * math.pi) ** 0.6 + 0.01
        rows.append([p + Vector((-w, 0, -w * 0.4)), p, p + Vector((w * 0.6, 0, -w * 0.3))])
    grid_mesh(f"{prefix}Vane", rows, K[mat], 0.012)
    cone(f"{prefix}Nib", 0.025, 0.0, 0.12, (0, 0, -0.06), K["gold"], verts=6, rot=(math.pi, 0, 0))


def chain_links(prefix, a, b, mat, link=0.16, thick=0.03, sag=0.0):
    """A chain of alternating links from a to b, sagging by `sag`."""
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, int(d.length / (link * 1.4)))
    for k in range(n):
        t = (k + 0.5) / n
        p = a + d * t + Vector((0, 0, -sag * 4 * t * (1 - t)))
        s = _mark()
        hoop(f"{prefix}{k}", (0, 0, 0), link * 0.5, "X" if k % 2 else "Y", mat, thick=thick)
        _xform(s, Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4() @ Matrix.Diagonal((1, 1, 1.5, 1)))


def slab(name, c, w, d, t, mat, seed=0, tilt=(0, 0), yaw=0.0, chip=0.18):
    """A hand-cut stone slab or flag: an irregular chipped outline (8-10 corners), bevelled, tilted."""
    rnd = random.Random(seed)
    n = rnd.choice((7, 8, 9))
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.2, 0.2)
        rx, ry = w / 2 * (1 - rnd.uniform(0, chip)), d / 2 * (1 - rnd.uniform(0, chip))
        ca, sa = math.cos(a), math.sin(a)
        k = 1 / max(abs(ca), abs(sa)) ** 0.7
        pts.append((ca * rx * min(k, 1.35), sa * ry * min(k, 1.35)))
    ob = B20.tprism(name, WS.ccw(pts), -t / 2, t, mat, plane="XY", bevel=min(0.05, t * 0.3))
    ob.matrix_world = Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y")
    return ob


def rubble(prefix, c, n, spread, size, mat, seed=0):
    """Broken masonry: angular chunks of stone strewn round c (lying on z = c.z)."""
    rnd = random.Random(seed)
    c = Vector(c)
    for i in range(n):
        a = rnd.uniform(0, 6.28)
        d = spread * math.sqrt(rnd.random())
        sz = size * rnd.uniform(0.4, 1.0)
        p = c + Vector((math.cos(a) * d, math.sin(a) * d, sz * 0.3))
        ob = crystal(f"{prefix}{i}", p, sz, mat, (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)), sides=rnd.choice((4, 5, 6)), tip=0.7,
                     seed=seed * 13 + i)
