"""Nightmare Highschool: R6 training dummy, a beaten gym/boxing-club bag body on the standard non-bending R6 rig.

Headless:  E:/Blender/blender.exe -b --factory-startup -P build_training_dummy.py -- [--no-render] [--samples 128]
(run make_stencils.py first; it writes src/stencil_back.png)

What it makes (everything next to this script):
  NH_TrainingDummy.blend, fbx/NH_TrainingDummy.fbx, textures/dummy_<set>_{color,normal,roughness,metalness}.png,
  previews/*.png, build_report.json
Geometry is in studs, in each R6 part's own space. Blender axes: +x = the character's right, +y = front, +z = up
(Roblox +x right, +y up, -z front; Blender = (x, -z, y), the same as art/characters/female/nh_female_body.py).
- Six objects named like the R6 parts, origin at the part centre, placed at the standard R6 rig offsets.
- Every part's bounding box is centred on the part (symmetric in x, y and z): Roblox's 3D importer re-centres each
  mesh on its bounding box, so an off-centre detail would shift the part off its Motor6D.
- Each surface is an analytic rounded box / rounded cylinder (+ pillow bulge). The low poly samples it coarsely and
  the high poly samples it densely and adds the stitching, quilting, dents, wrinkles, tape and webbing as real
  displacement; the tangent normal map is a Cycles high-to-low bake. Colour / roughness / metalness come from the
  same feature functions evaluated at each texel's baked object-space position, so they line up with the normals.
- Texture sets (1024 each): Head, Torso, Limbs (the four limbs share one atlas).
No blood or gore: wear is scuffs, dents, dust, tape and paint only (browns and greys, no red).
"""
import bpy, bmesh, math, os, sys, json, zlib, struct, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = HERE
TEX, FBXD, PREV, SRC = (os.path.join(OUT, d) for d in ("textures", "fbx", "previews", "src"))
for d in (TEX, FBXD, PREV):
    os.makedirs(d, exist_ok=True)
RES = 1024
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 128
ONLY_SETS = argv[argv.index("--sets") + 1].split(",") if "--sets" in argv else None   # debug: bake only these
VIEWS = argv[argv.index("--views") + 1].split(",") if "--views" in argv else None    # render only these views
DEBUG = argv[argv.index("--debug") + 1] if "--debug" in argv else None
T0 = time.time()


def log(*a):
    print(f"[dummy {time.time() - T0:6.1f}s]", *a, flush=True)


# =====================================================================================================
# noise (numpy value noise, deterministic)
# =====================================================================================================
_rng = np.random.RandomState(1313)
_PERM = np.tile(_rng.permutation(256), 4)
_GRAD = _rng.uniform(-1, 1, 256)


def vnoise(P):
    P = np.asarray(P, dtype=np.float64)
    Pi = np.floor(P)
    f = P - Pi
    Pi = Pi.astype(np.int64) & 255
    u = f * f * (3 - 2 * f)
    x, y, z = Pi[:, 0], Pi[:, 1], Pi[:, 2]

    def g(dx, dy, dz):
        return _GRAD[_PERM[_PERM[_PERM[x + dx] + y + dy] + z + dz]]
    ux, uy, uz = u[:, 0], u[:, 1], u[:, 2]
    x00 = g(0, 0, 0) * (1 - ux) + g(1, 0, 0) * ux
    x10 = g(0, 1, 0) * (1 - ux) + g(1, 1, 0) * ux
    x01 = g(0, 0, 1) * (1 - ux) + g(1, 0, 1) * ux
    x11 = g(0, 1, 1) * (1 - ux) + g(1, 1, 1) * ux
    y0 = x00 * (1 - uy) + x10 * uy
    y1 = x01 * (1 - uy) + x11 * uy
    return y0 * (1 - uz) + y1 * uz


def fbm(P, octaves=4, seed=0.0):
    P = np.asarray(P, dtype=np.float64) + seed * 17.31
    s, a, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s = s + a * vnoise(P * (2.0 ** o) + o * 5.17)
        tot += a
        a *= 0.5
    return s / tot


def ridged(P, seed=0.0):
    return 1 - np.abs(vnoise(np.asarray(P) + seed * 11.7))


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# =====================================================================================================
# part specs
# =====================================================================================================
# box parts: half extents of the un-bulged cube, edge radius r, pillow bulge per axis.
# steps: (z_lo_edge, z_hi_edge, amount): extra outward offset of the side walls below a height (hand wraps, boots)
# bands: separate strap shells (z0, z1, t, c, sid): t = how far it stands proud, c = lip chamfer height
PARTS = {
    "Torso": dict(kind="box", loc=(0, 0, 3), half=(0.97, 0.45, 1.0), r=0.12, bulge=(0.03, 0.05, 0.0), set="Torso",
                  xs=[-0.97, -0.85, -0.42, 0, 0.42, 0.85, 0.97], ys=[-0.45, -0.33, 0, 0.33, 0.45],
                  zs=[-1, -0.88, -0.6125, -0.4075, -0.15, 0.12, 0.3875, 0.5925, 0.88, 1],
                  steps=[], bands=[(0.38, 0.60, 0.035, 0.015, 1), (-0.62, -0.40, 0.035, 0.015, 2)]),
    "Right Arm": dict(kind="box", loc=(1.5, 0, 3), half=(0.47, 0.47, 1.0), r=0.12, bulge=(0.03, 0.03, 0.0), set="Limbs",
                      xs=[-0.47, -0.35, 0, 0.35, 0.47], ys=[-0.47, -0.35, 0, 0.35, 0.47],
                      zs=[-1, -0.88, -0.47, -0.41, -0.1, 0.3, 0.88, 1], steps=[(-0.47, -0.41, 0.022)], bands=[]),
    "Left Arm": dict(kind="box", loc=(-1.5, 0, 3), half=(0.47, 0.47, 1.0), r=0.12, bulge=(0.03, 0.03, 0.0), set="Limbs",
                     xs=[-0.47, -0.35, 0, 0.35, 0.47], ys=[-0.47, -0.35, 0, 0.35, 0.47],
                     zs=[-1, -0.88, -0.47, -0.41, -0.1, 0.3075, 0.4925, 0.88, 1], steps=[(-0.47, -0.41, 0.022)],
                     bands=[(0.30, 0.50, 0.035, 0.015, 1)]),
    "Right Leg": dict(kind="box", loc=(0.5, 0, 1), half=(0.47, 0.47, 1.0), r=0.12, bulge=(0.03, 0.03, 0.0), set="Limbs",
                      xs=[-0.47, -0.35, 0, 0.35, 0.47], ys=[-0.47, -0.35, 0, 0.35, 0.47],
                      zs=[-1, -0.88, -0.63, -0.57, -0.1125, 0.0725, 0.45, 0.88, 1], steps=[(-0.63, -0.57, 0.028)],
                      bands=[(-0.12, 0.08, 0.035, 0.015, 1)]),
    "Left Leg": dict(kind="box", loc=(-0.5, 0, 1), half=(0.47, 0.47, 1.0), r=0.12, bulge=(0.03, 0.03, 0.0), set="Limbs",
                     xs=[-0.47, -0.35, 0, 0.35, 0.47], ys=[-0.47, -0.35, 0, 0.35, 0.47],
                     zs=[-1, -0.88, -0.63, -0.57, -0.1, 0.45, 0.88, 1], steps=[(-0.63, -0.57, 0.028)], bands=[]),
    # head: rounded cylinder like the R6 head (about 1.2 across), shifted down by half the crown strap so the bbox
    # stays centred; the bottom sinks into the Torso like the stock head does
    "Head": dict(kind="cyl", loc=(0, 0, 4.5), R=0.6, hz=0.625, zc=-0.015, r=0.27, set="Head", N=32,
                 zs_rel=[-0.625, -0.355, -0.1, 0.06, 0.32, 0.355, 0.445, 0.535, 0.625],
                 cap_top=[0.6, 0.51, 0.42, 0.33, 0.16], cap_bot=[0.6, 0.33],
                 bands=[(0.02, 0.30, 0.05, 0.02, 1)], strap=dict(w=0.22, t=0.03, c=0.02, zb=0.17, sid=2, n=20)),
}
ORDER = ["Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg"]
SETS = {"Head": ["Head"], "Torso": ["Torso"], "Limbs": ["Left Arm", "Right Arm", "Left Leg", "Right Leg"]}


# =====================================================================================================
# analytic surface: closest point on an inner shape + radius (+ bulge + steps + extra offset)
# =====================================================================================================
def param(spec, P):
    """P (n,3) part-local -> (cl, dn). Offset-invariant: moving P along dn keeps cl and dn."""
    P = np.asarray(P, dtype=np.float64)
    if spec["kind"] == "box":
        A = np.array(spec["half"]) - spec["r"]
        cl = np.clip(P, -A, A)
    else:
        a = spec["R"] - spec["r"]
        az = spec["hz"] - spec["r"]
        rho = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        sc = np.minimum(1.0, a / np.maximum(rho, 1e-9))
        cl = np.stack([P[:, 0] * sc, P[:, 1] * sc,
                       np.clip(P[:, 2], spec["zc"] - az, spec["zc"] + az)], 1)
    d = P - cl
    n = np.linalg.norm(d, axis=1, keepdims=True)
    dn = d / np.maximum(n, 1e-12)
    return cl, dn


def offset(spec, cl, dn):
    """radial offset beyond r: pillow bulge and side-wall steps"""
    off = np.zeros(len(cl))
    if spec["kind"] == "box":
        A = np.array(spec["half"]) - spec["r"]
        u = cl / A
        b = spec["bulge"]
        for a in range(3):
            o = [c for c in range(3) if c != a]
            off += b[a] * dn[:, a] ** 2 * (1 - u[:, o[0]] ** 2) * (1 - u[:, o[1]] ** 2)
        for (zlo, zhi, amt) in spec["steps"]:
            off += amt * ss(zhi, zlo, cl[:, 2]) * (1 - dn[:, 2] ** 2)
    return off


def surf(spec, P, extra=0.0):
    cl, dn = param(spec, P)
    return cl + (spec["r"] + offset(spec, cl, dn) + extra)[:, None] * dn


# =====================================================================================================
# mesh generation
# =====================================================================================================
def merge(verts, faces):
    """merge coincident verts (np.unique on rounded coords) and remap faces (list of int arrays)"""
    V = np.asarray(verts)
    key = np.round(V * 1e5).astype(np.int64)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    newV = np.zeros((len(uniq), 3))
    newV[inv] = V
    out = []
    for f in faces:
        g = inv[f]
        out.append(g)
    return newV, out


def box_cube(spec, xs, ys, zs):
    """cube-surface grid points (before mapping) + quads (with outward winding) + face ids"""
    h = spec["half"]
    axes_vals = [np.asarray(xs), np.asarray(ys), np.asarray(zs)]
    V, F = [], []
    base = 0
    for axis, (ua, va) in ((0, (1, 2)), (1, (2, 0)), (2, (0, 1))):
        for sign in (1, -1):
            us, vs = axes_vals[ua], axes_vals[va]
            U, W = np.meshgrid(us, vs, indexing="ij")
            P = np.zeros(U.shape + (3,))
            P[..., axis] = sign * h[axis]
            P[..., ua] = U
            P[..., va] = W
            idx = np.arange(U.size).reshape(U.shape) + base
            a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
            q = np.stack([a, b, c, d], -1).reshape(-1, 4)
            if sign < 0:
                q = q[:, ::-1]
            V.append(P.reshape(-1, 3))
            F.extend(list(q))
            base += U.size
    return np.concatenate(V), F


def cyl_cube(spec, N, zs_rel, cap_top, cap_bot):
    R, zc, hz = spec["R"], spec["zc"], spec["hz"]
    th = np.arange(N) * 2 * math.pi / N
    V, F = [], []

    def add(P):
        V.append(np.asarray(P))
        return len(V) - 1
    side = [[add((R * math.cos(t), R * math.sin(t), zc + z)) for z in zs_rel] for t in th]
    for k in range(N):
        k1 = (k + 1) % N
        for j in range(len(zs_rel) - 1):
            F.append(np.array([side[k][j], side[k1][j], side[k1][j + 1], side[k][j + 1]]))

    def cap(rings, zt, top):
        ring_ids = [[add((rho * math.cos(t), rho * math.sin(t), zt)) for t in th] for rho in rings]
        ctr = add((0, 0, zt))
        for j in range(len(rings) - 1):
            for k in range(N):
                k1 = (k + 1) % N
                q = [ring_ids[j][k], ring_ids[j][k1], ring_ids[j + 1][k1], ring_ids[j + 1][k]]
                F.append(np.array(q if top else q[::-1]))
        for k in range(N):
            k1 = (k + 1) % N
            t3 = [ring_ids[-1][k], ring_ids[-1][k1], ctr]
            F.append(np.array(t3 if top else t3[::-1]))
    cap(cap_top, zc + hz, True)
    cap(cap_bot, zc - hz, False)
    return np.array(V, dtype=np.float64), F


def lin(a, b, step):
    n = max(2, int(math.ceil(abs(b - a) / step)) + 1)
    return list(np.linspace(a, b, n))


def body_mesh(spec, hi=False):
    """returns verts (mapped onto the surface), faces, per-face sid (0)"""
    if spec["kind"] == "box":
        if hi:
            h = spec["half"]
            st = 0.0065
            V, F = box_cube(spec, lin(-h[0], h[0], st), lin(-h[1], h[1], st), lin(-h[2], h[2], st))
        else:
            V, F = box_cube(spec, spec["xs"], spec["ys"], spec["zs"])
    else:
        if hi:
            N = 360
            zr = lin(-spec["hz"], spec["hz"], 0.0065)
            ct = lin(spec["R"], 0.0, 0.0065)[:-1]
            cb = list(ct)
            V, F = cyl_cube(spec, N, zr, ct, cb)
        else:
            V, F = cyl_cube(spec, spec["N"], spec["zs_rel"], spec["cap_top"], spec["cap_bot"])
    V, F = merge(V, F)
    V = surf(spec, V)
    if not hi:   # holes under the strap bands (hidden by the band lips)
        keep = []
        for f in F:
            c = V[f].mean(0)
            hidden = False
            for (z0, z1, t, cc, sid) in spec.get("bands", []):
                if z0 + 0.5 * cc - 1e-4 < c[2] < z1 - 0.5 * cc + 1e-4:
                    _, dn = param(spec, c[None])
                    if abs(dn[0, 2]) < 0.5:
                        hidden = True
            if not hidden:
                keep.append(f)
        F = keep
    return V, F, [0] * len(F)


def ring_points(spec, hi):
    """horizontal loop of rough points around the part (CCW seen from above)"""
    if spec["kind"] == "box":
        h = spec["half"]
        if hi:
            xs, ys = lin(-h[0], h[0], 0.0065), lin(-h[1], h[1], 0.0065)
        else:
            xs, ys = spec["xs"], spec["ys"]
        pts = []
        for y in ys[:-1]:
            pts.append((h[0], y))
        for x in list(reversed(xs))[:-1]:
            pts.append((x, h[1]))
        for y in list(reversed(ys))[:-1]:
            pts.append((-h[0], y))
        for x in xs[:-1]:
            pts.append((x, -h[1]))
        return pts
    N = 360 if hi else spec["N"]
    return [(spec["R"] * math.cos(2 * math.pi * k / N), spec["R"] * math.sin(2 * math.pi * k / N)) for k in range(N)]


def band_mesh(spec, band, hi=False):
    z0, z1, t, c, sid = band
    pts = ring_points(spec, hi)
    rows = [(z0, -0.012), (z0 + c, t), (z1 - c, t), (z1, -0.012)]
    if hi:   # dense rows across the band
        zz = lin(z0 + c, z1 - c, 0.0065)
        rows = [(z0, -0.012)] + [(z0 + c * f, -0.012 + (t + 0.012) * math.sin(f * math.pi / 2)) for f in (0.33, 0.66)] + \
               [(z, t) for z in zz] + [(z1 - c * f, -0.012 + (t + 0.012) * math.sin(f * math.pi / 2)) for f in (0.66, 0.33)] + [(z1, -0.012)]
    M = len(pts)
    V = []
    for (z, o) in rows:
        P = np.array([(x, y, z) for (x, y) in pts], dtype=np.float64)
        V.append(surf(spec, P, o))
    V = np.concatenate(V)
    F = []
    for i in range(len(rows) - 1):
        for k in range(M):
            k1 = (k + 1) % M
            F.append(np.array([i * M + k, i * M + k1, (i + 1) * M + k1, (i + 1) * M + k]))
    return V, F, [sid] * len(F)


def strap_mesh(spec, st, hi=False):
    """head crown strap: left side, over the crown, right side (plane y = 0, width w)"""
    w, t, c, zb, sid, n = st["w"], st["t"], st["c"], st["zb"], st["sid"], st["n"]
    if hi:
        n = 260
    top = spec["zc"] + spec["hz"]
    cols = [(-w / 2, -0.012), (-w / 2 + c, t), (w / 2 - c, t), (w / 2, -0.012)]
    if hi:
        cols = [(-w / 2, -0.012)] + [(y, t) for y in lin(-w / 2 + c, w / 2 - c, 0.0065)] + [(w / 2, -0.012)]
    phis = np.linspace(-math.pi / 2, math.pi / 2, n + 1)
    V = []
    for phi in phis:
        P = np.array([(spec["R"] * math.sin(phi), y, zb + (top - zb) * math.cos(phi)) for (y, _) in cols])
        offs = np.array([o for (_, o) in cols])
        cl, dn = param(spec, P)
        V.append(cl + (spec["r"] + offset(spec, cl, dn) + offs)[:, None] * dn)
    V = np.concatenate(V)
    C = len(cols)
    F = []
    for k in range(n):
        for i in range(C - 1):
            F.append(np.array([k * C + i, (k + 1) * C + i, (k + 1) * C + i + 1, k * C + i + 1]))
    return V, F, [sid] * len(F)


def face_normal(p):
    n = np.cross(p[1] - p[0], p[2] - p[0])
    if len(p) == 4:
        n = n + np.cross(p[2] - p[0], p[3] - p[0])
    return n


def frame_mesh(center, w, h, wi, hi_, back, front, sid, dirn=1):
    """rectangular buckle frame in the x-z plane facing +y*dirn: outer w x h, hole wi x hi_ (no back face)"""
    cx, cz = center[0], center[2]
    yb, yf = center[1] + dirn * back, center[1] + dirn * front

    def rect(ww, hh, y):
        return [(cx - ww / 2, y, cz - hh / 2), (cx + ww / 2, y, cz - hh / 2), (cx + ww / 2, y, cz + hh / 2), (cx - ww / 2, y, cz + hh / 2)]
    V = np.array(rect(w, h, yf) + rect(wi, hi_, yf) + rect(w, h, yb) + rect(wi, hi_, yb))
    ctr = np.array([cx, 0, cz])
    F = []
    for k in range(4):
        k1 = (k + 1) % 4
        for f, want in ((np.array([k, k1, 4 + k1, 4 + k]), "front"),
                        (np.array([8 + k, 8 + k1, k1, k]), "out"),
                        (np.array([4 + k, 4 + k1, 12 + k1, 12 + k]), "in")):
            p = V[f]
            mid = (p.mean(0) - ctr) * np.array([1, 0, 1])
            d = np.array([0, dirn, 0.0]) if want == "front" else (mid if want == "out" else -mid)
            F.append(f if np.dot(face_normal(p), d) > 0 else f[::-1])
    return V, F, [sid] * len(F)


def rbox(half, r, center, sid, hi):
    """small rounded box (steel plates), mapped through the same analytic surface"""
    sp = dict(kind="box", half=half, r=r, bulge=(0, 0, 0), steps=[])
    if hi:
        xs, ys, zs = (lin(-h, h, 0.004) for h in half)
    else:
        xs, ys, zs = ([-h, h] for h in half)
    V, F = box_cube(sp, xs, ys, zs)
    V, F = merge(V, F)
    if hi:
        V = surf(sp, V)     # the low stays a plain box so its extents are exact (bbox balance)
    return V + np.asarray(center), F, [sid] * len(F)


# torso hardware (part-local): buckles on the front of each belt, steel plates on the back (balance the bbox)
BUCKLE_X = 0.42
HW_PROUD = 0.032      # how far buckles and plates stand off the belt


def torso_hardware(spec, hi):
    """-> list of (V, F, S, kind, centre on the belt surface)"""
    parts = []
    for (z0, z1, t, c, sid) in spec["bands"]:
        zm = 0.5 * (z0 + z1)
        for side, kind in ((1, "buckle"), (-1, "plate")):
            x = BUCKLE_X if side > 0 else -BUCKLE_X
            p = surf(spec, np.array([[x, side * 0.5, zm]]), t)[0]
            if kind == "buckle":
                V, F, S = frame_mesh(p, 0.24, 0.27, 0.13, 0.16, -0.008, HW_PROUD, sid + 2, side)
            else:
                hy = (HW_PROUD + 0.008) / 2
                V, F, S = rbox((0.1, hy, 0.1), 0.01, p + np.array([0, side * (HW_PROUD - hy), 0]), sid + 4, hi)
            parts.append((V, F, S, kind, p))
    return parts


def join(chunks):
    Vs, Fs, Ss = [], [], []
    base = 0
    for (V, F, S) in chunks:
        Vs.append(V)
        Fs.extend([np.asarray(f) + base for f in F])
        Ss.extend(S)
        base += len(V)
    return np.concatenate(Vs), Fs, np.array(Ss, dtype=np.int32)


def build_geometry(name, hi=False):
    """-> (V, F, S, hardware list, buckle chunk or None). Low: everything in one mesh. High: buckles split out
    (they get a bevel modifier instead of displacement)."""
    spec = PARTS[name]
    chunks = [body_mesh(spec, hi)]
    for b in spec.get("bands", []):
        chunks.append(band_mesh(spec, b, hi))
    if spec.get("strap"):
        chunks.append(strap_mesh(spec, spec["strap"], hi))
    hw, buckles = [], []
    if name == "Torso":
        for (V, F, S, kind, p) in torso_hardware(spec, hi):
            if hi and kind == "buckle":
                buckles.append((V, F, S))
            else:
                chunks.append((V, F, S))
            hw.append((kind, p, S[0]))
    V, F, S = join(chunks)
    return V, F, S, hw, (join(buckles) if buckles else None)


def make_object(name, V, F, S, coll, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], [list(map(int, f)) for f in F])
    me.polygons.foreach_set("material_index", np.asarray(S, dtype=np.int32))
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), dtype=bool))
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# =====================================================================================================
# features: one function per part -> height H (studs, along dn) + masks for the texture pass
# =====================================================================================================
def seam(s, t, depth=0.010, gw=0.011, off=0.032, tw=0.0075, spacing=0.068, dash=0.62, th=0.0065, slant=0.35):
    groove = np.exp(-(s / gw) ** 2)
    f = np.mod((t + slant * (s - off)) / spacing, 1.0)
    x = (f - 0.5) / (dash / 2)
    prof = np.clip(1 - x * x, 0, 1) ** 0.6
    rows = np.exp(-((s - off) / tw) ** 2)
    thread = rows * prof
    pinch = np.exp(-((s - off) / (tw * 2.5)) ** 2) * (1 - prof)
    H = -depth * groove + th * thread - 0.0018 * pinch
    return H, thread, groove


def perim_t(cl, dn, r):
    ax, ay = np.abs(dn[:, 0]), np.abs(dn[:, 1])
    a = np.arctan2(ay, ax)
    b = np.arctan2(ax, ay)
    return np.where(ax >= ay, np.abs(cl[:, 1]) + r * a, np.abs(cl[:, 0]) + r * b)


def rect(u, v, cu, cv, ang, L, W, P, soft=0.004, jag=0.018, seed=0.0):
    ca, sa = math.cos(ang), math.sin(ang)
    du, dv = u - cu, v - cv
    a = du * ca + dv * sa
    b = -du * sa + dv * ca
    endL = L / 2 + jag * vnoise(np.stack([b * 38 + seed, a * 0 + seed * 3, np.full_like(a, seed)], 1))
    sideW = W / 2 + 0.0025 * vnoise(np.stack([a * 60, b * 0 + seed, np.full_like(a, seed + 2)], 1))
    m = ss(soft, -soft, np.abs(a) - endL) * ss(soft, -soft, np.abs(b) - sideW)
    edge = np.exp(-((np.abs(b) - sideW) / 0.004) ** 2) + np.exp(-((np.abs(a) - endL) / 0.004) ** 2)
    return m, a, b, edge * (m > 0.05)


def wrap(z, z0, z1, along, P, seed=0.0):
    """tape wrapped around a limb between z0..z1 (torn, slightly spiralled edges)"""
    j0 = z0 + 0.012 * vnoise(np.stack([along * 30, np.full_like(z, seed), np.full_like(z, 1.0)], 1))
    j1 = z1 + 0.012 * vnoise(np.stack([along * 30, np.full_like(z, seed), np.full_like(z, 4.0)], 1))
    m = ss(j0 - 0.003, j0 + 0.003, z) * ss(j1 + 0.003, j1 - 0.003, z)
    layer = np.mod((z - z0 + along * 0.03) / 0.07, 1.0)
    return m, layer


def face_w(dn, axis, sign, lo=0.55, hi=0.85):
    return ss(lo, hi, sign * dn[:, axis])


def features(name, P, sid):
    """P (n,3) part-local points on or near the surface; sid (n,) strap/hardware id. Returns dict of fields."""
    spec = PARTS[name]
    n = len(P)
    cl, dn = param(spec, P)
    r = spec["r"]
    Z = np.zeros(n)
    F = dict(H=Z.copy(), thread=Z.copy(), groove=Z.copy(), tape=Z.copy(), tape_edge=Z.copy(), gaffer=Z.copy(),
             paint=Z.copy(), target=Z.copy(), metal=Z.copy(), rivet=Z.copy(), wear=Z.copy(), dent=Z.copy(),
             wrapcloth=Z.copy(), wraplayer=Z.copy(), rubber=Z.copy(), scratch=Z.copy(), fray=Z.copy())
    body = sid == 0
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    if spec["kind"] == "box":
        edge = np.clip((1 - np.max(np.abs(dn), 1)) / 0.29, 0, 1)
    else:
        hwn = np.sqrt(dn[:, 0] ** 2 + dn[:, 1] ** 2)
        edge = np.clip((1 - np.maximum(np.abs(dn[:, 2]), hwn)) / 0.29, 0, 1)
    F["edge"] = edge
    H = F["H"]

    def add_seam(s, t, mask, **kw):
        h, th, gr = seam(s, t, **kw)
        H[:] += h * mask
        F["thread"][:] = np.maximum(F["thread"], th * mask)
        F["groove"][:] = np.maximum(F["groove"], gr * mask)

    if spec["kind"] == "box":
        hw = np.sqrt(dn[:, 0] ** 2 + dn[:, 1] ** 2)
        ang = np.arctan2(np.abs(dn[:, 1]), np.abs(dn[:, 0]))
        s_v = r * np.abs(ang - math.pi / 4)
        elev = np.arctan2(np.abs(dn[:, 2]), hw)
        s_h = r * np.abs(elev - math.pi / 4)
        tp = perim_t(cl, dn, r)
        topm = (dn[:, 2] > 0).astype(float)
        botm = 1 - topm
        steps_zone = np.ones(n)
        for (zlo, zhi, amt) in spec["steps"]:
            steps_zone *= ss(zlo - 0.02, zhi + 0.02, z)          # no seams under wraps / boots
        sidew = ss(0.3, 0.6, hw)
        add_seam(s_v, z, body * sidew * steps_zone)
        add_seam(s_h, tp, body * topm)
        if not spec["steps"]:
            add_seam(s_h, tp, body * botm)
        # soft fabric/leather wrinkles: vertical creases + broad lumps
        crease = ridged(P * np.array([7.0, 7.0, 1.6]), seed=len(name)) ** 3
        lumps = fbm(P * 2.2, 3, seed=len(name) * 0.7)
        H[:] += body * (0.006 * crease + 0.006 * lumps)
        fine = fbm(P * 26, 2, seed=3.3)
        H[:] += body * 0.0012 * fine

    if name == "Torso":
        front, back = face_w(dn, 1, 1), face_w(dn, 1, -1)
        rside, lside = face_w(dn, 0, 1), face_w(dn, 0, -1)
        # front/back panel seams and a wrap seam round the middle
        for px_ in (-0.6, 0.6):
            add_seam(np.abs(x - px_), z, body * (front + back) * ss(0.86, 0.8, np.abs(z)))
        add_seam(np.abs(cl[:, 2] + 0.12), tp, body * sidew * ss(0.25, 0.1, np.abs(z + 0.12)) * (1 - front))
        # punch dents round the target
        dents = [(0.0, 0.05, 0.2, 0.022), (-0.18, -0.12, 0.13, 0.014), (0.22, 0.2, 0.14, 0.016), (0.1, -0.22, 0.11, 0.012),
                 (-0.3, 0.22, 0.12, 0.012), (0.35, -0.05, 0.1, 0.01), (-0.05, 0.3, 0.09, 0.01), (0.55, 0.15, 0.12, 0.009)]
        dsum = np.zeros(n)
        for (dx, dz, rad, dep) in dents:
            dsum += dep * np.exp(-((x - dx) ** 2 + (z - dz) ** 2) / rad ** 2)
        H[:] -= body * front * dsum
        F["dent"][:] = body * front * np.clip(dsum / 0.02, 0, 1)
        # wear (lighter, scratched leather) in the strike zone and on edges
        strike = np.exp(-((x / 0.62) ** 2 + ((z - 0.03) / 0.5) ** 2))
        F["wear"][:] = body * np.clip(front * strike * 0.9 + edge * 0.7, 0, 1)
        sc = ridged(np.stack([x * 3 + z * 9, z * 3 - x * 9, y * 2], 1) * 6, seed=5) ** 14
        sc2 = ridged(np.stack([x * 9 - z * 4, z * 9 + x * 4, y * 2], 1) * 5, seed=9) ** 14
        F["scratch"][:] = body * front * strike * np.clip(sc + sc2, 0, 1)
        H[:] -= 0.0015 * F["scratch"]
        # painted target (faded, rubbed off where it gets hit most)
        rr = np.sqrt(x ** 2 + (z - 0.05) ** 2)
        ring = np.maximum(ss(0.027, 0.02, np.abs(rr - 0.3)), ss(0.022, 0.015, np.abs(rr - 0.14)))
        ring = np.maximum(ring, ss(0.05, 0.04, rr))
        rub = ss(0.15, 0.45, fbm(P * np.array([9, 9, 9.0]), 4, seed=2) * 0.5 + 0.5 + 0.12 - 0.25 * F["dent"])
        F["target"][:] = body * front * ring * rub
        # duct tape: X on the upper right chest, a long patch on the front left, a strip on the right side
        for (cu, cv, angd, L, W, sd) in ((0.56, 0.74, 35, 0.4, 0.09, 1), (0.56, 0.74, -35, 0.4, 0.09, 2), (-0.72, -0.08, 82, 0.55, 0.1, 3)):
            m, a, b, e = rect(x, z, cu, cv, math.radians(angd), L, W, P, seed=sd)
            m *= body * front
            F["tape"][:] = np.maximum(F["tape"], m)
            F["tape_edge"][:] = np.maximum(F["tape_edge"], e * m)
            H[:] += m * (0.004 + 0.0018 * ridged(np.stack([a * 6, b * 40, np.full(n, sd)], 1)) ** 2) + 0.0015 * e * m
        for (cu, cv, angd, L, W, sd) in ((0.02, -0.2, 3, 0.62, 0.1, 4), (0.0, -0.3, -4, 0.55, 0.1, 5)):
            m, a, b, e = rect(y, z, cu, cv, math.radians(angd), L, W, P, seed=sd)
            m *= body * rside
            F["tape"][:] = np.maximum(F["tape"], m)
            F["tape_edge"][:] = np.maximum(F["tape_edge"], e * m)
            H[:] += m * 0.004 + 0.0015 * e * m
        m, a, b, e = rect(x, z, 0.64, 0.74, math.radians(8), 0.36, 0.1, P, seed=6)
        m *= body * back
        F["gaffer"][:] = m
        H[:] += m * 0.004 + 0.0015 * e * m
        # stencil on the back
        F["paint"][:] = body * back * stencil_sample(x, z) * ss(0.25, 0.5, fbm(P * 11, 4, seed=8) * 0.5 + 0.55)
        # belts: webbing ribs + edge stitching
        for (z0, z1, t, c, bsid) in spec["bands"]:
            bm = (sid == bsid).astype(float)
            add_seam(np.abs(z - (z0 + 0.03)), tp, bm, depth=0.002, off=0.0, gw=0.01, th=0.004, spacing=0.05)
            add_seam(np.abs(z - (z1 - 0.03)), tp, bm, depth=0.002, off=0.0, gw=0.01, th=0.004, spacing=0.05)
            H[:] += bm * 0.0014 * np.sin(2 * math.pi * z / 0.016)
            F["fray"][:] = np.maximum(F["fray"], bm * (ss(0.03, 0.0, z - z0) + ss(0.03, 0.0, z1 - z)))
            # compression wrinkles in the bag just above and below each belt
            near = np.exp(-((z - z1) / 0.08) ** 2) * (z > z1) + np.exp(-((z - z0) / 0.08) ** 2) * (z < z0)
            H[:] += body * near * 0.006 * np.sin(tp * 38 + 3 * vnoise(P * 4))
        # hardware
        hwm = (sid >= 3)
        F["metal"][:] = hwm.astype(float)
        for (kind, p, hsid) in HARDWARE:
            if kind == "plate":
                for (ox, oz) in ((-0.07, -0.07), (0.07, -0.07), (0.07, 0.07), (-0.07, 0.07)):
                    d = np.sqrt((x - p[0] - ox) ** 2 + (z - p[2] - oz) ** 2)
                    dome = np.sqrt(np.clip(1 - (d / 0.022) ** 2, 0, 1)) * (sid == hsid)
                    H[:] += 0.008 * dome
                    F["rivet"][:] = np.maximum(F["rivet"], (d < 0.022) * (sid == hsid))

    if name in ("Left Arm", "Right Arm", "Left Leg", "Right Leg"):
        arm = "Arm" in name
        tp = perim_t(cl, dn, r)
        if arm:
            # boxing hand wraps over the bottom ~0.55 studs, layered in a spiral; the fist end too
            m = ss(-0.41, -0.47, z) * body
            q = z + tp * 0.035
            layer = np.mod(q / 0.085, 1.0)
            F["wrapcloth"][:] = m
            F["wraplayer"][:] = layer * m
            H[:] += m * (0.004 * layer - 0.004 * ss(0.9, 1.0, layer) + 0.0015 * fbm(P * 30, 2))
            bot = (dn[:, 2] < -0.5) * body
            H[:] += bot * 0.003 * np.sin((x + y) * 40) * np.sin((x - y) * 40)
        else:
            # boots: rubber cuff below -0.6 with ribs near the sole
            m = ss(-0.57, -0.63, z) * body
            F["rubber"][:] = m
            ribs = (np.sin(2 * math.pi * z / 0.05) > 0.55) * ss(-0.78, -0.82, z)
            H[:] += m * (-0.004 * ribs + 0.0015 * fbm(P * 18, 2, seed=7))
        # tape wraps / patches
        if name == "Right Arm":
            m, layer = wrap(z, -0.22, 0.0, tp, P, seed=1)
            m *= body
            F["tape"][:] = np.maximum(F["tape"], m)
            H[:] += m * (0.004 + 0.0025 * ss(0.85, 1.0, layer))
            F["tape_edge"][:] = np.maximum(F["tape_edge"], m * ss(0.8, 1.0, layer))
        if name == "Left Leg":
            m, layer = wrap(z, 0.28, 0.5, tp, P, seed=2)
            m *= body
            F["gaffer"][:] = np.maximum(F["gaffer"], m)
            H[:] += m * (0.004 + 0.0025 * ss(0.85, 1.0, layer))
        if name == "Left Arm":
            ow = face_w(dn, 0, -1)
            m, a, b, e = rect(y, z, 0.08, -0.05, math.radians(20), 0.36, 0.1, P, seed=7)
            m *= body * ow
            F["tape"][:] = np.maximum(F["tape"], m)
            H[:] += m * 0.004 + 0.0015 * e * m
        if name == "Right Leg":
            fw = face_w(dn, 1, 1)
            for (cu, cv, angd, sd) in ((0.0, 0.45, 40, 8), (0.0, 0.45, -40, 9)):
                m, a, b, e = rect(x, z, cu, cv, math.radians(angd), 0.36, 0.09, P, seed=sd)
                m *= body * fw
                F["tape"][:] = np.maximum(F["tape"], m)
                H[:] += m * 0.004 + 0.0015 * e * m
        for (z0, z1, t, c, bsid) in spec["bands"]:
            bm = (sid == bsid).astype(float)
            add_seam(np.abs(z - (z0 + 0.03)), tp, bm, depth=0.002, off=0.0, gw=0.01, th=0.004, spacing=0.05)
            add_seam(np.abs(z - (z1 - 0.03)), tp, bm, depth=0.002, off=0.0, gw=0.01, th=0.004, spacing=0.05)
            H[:] += bm * 0.0014 * np.sin(2 * math.pi * z / 0.016)
            F["fray"][:] = np.maximum(F["fray"], bm * (ss(0.03, 0.0, z - z0) + ss(0.03, 0.0, z1 - z)))
            near = np.exp(-((z - z1) / 0.07) ** 2) * (z > z1) + np.exp(-((z - z0) / 0.07) ** 2) * (z < z0)
            H[:] += body * near * 0.005 * np.sin(tp * 40 + 3 * vnoise(P * 4))
            # rivet on the outer side of the strap
            sgn = 1 if name.startswith("Right") else -1
            d = np.sqrt((y) ** 2 + (z - 0.5 * (z0 + z1)) ** 2) * (sgn * dn[:, 0] > 0.6)
            dome = np.sqrt(np.clip(1 - (d / 0.026) ** 2, 0, 1)) * bm * (sgn * dn[:, 0] > 0.6)
            H[:] += 0.008 * dome
            F["rivet"][:] = np.maximum(F["rivet"], dome > 0)
        F["wear"][:] = body * np.clip(edge * 0.8, 0, 1)

    if name == "Head":
        zc = spec["zc"]
        ang = np.arctan2(y, x)
        rho = np.sqrt(cl[:, 0] ** 2 + cl[:, 1] ** 2)
        hw = np.sqrt(dn[:, 0] ** 2 + dn[:, 1] ** 2)
        elev = np.arctan2(dn[:, 2], hw)
        s_top = r * np.abs(elev - math.pi / 4)
        add_seam(s_top, ang * spec["R"], body * (dn[:, 2] > 0))
        # centre seam front-to-back over the crown (plane x = 0) - a stitched sack face
        add_seam(np.abs(x), np.arctan2(z - zc, y) * spec["R"], body * ss(-0.5, -0.4, z - zc))
        crease = ridged(P * np.array([6.0, 6.0, 2.0]), seed=4) ** 3
        H[:] += body * (0.006 * crease + 0.004 * fbm(P * 2.5, 3, seed=1) + 0.001 * fbm(P * 26, 2, seed=2))
        # X of duct tape on the face (hit here)
        fw = face_w(dn, 1, 1, 0.3, 0.7)
        u = np.arctan2(x, y) * spec["R"]
        for (angd, sd) in ((38, 11), (-38, 12)):
            m, a, b, e = rect(u, z, 0.0, -0.2, math.radians(angd), 0.52, 0.1, P, seed=sd)
            m *= body * fw
            F["tape"][:] = np.maximum(F["tape"], m)
            F["tape_edge"][:] = np.maximum(F["tape_edge"], e * m)
            H[:] += m * (0.004 + 0.0018 * ridged(np.stack([a * 6, b * 40, np.full(n, sd)], 1)) ** 2) + 0.0015 * e * m
        F["wear"][:] = body * np.clip(edge * 0.6 + fw * ss(0.3, 0.0, np.abs(z + 0.2)) * 0.3, 0, 1)
        # padded head band (sid 1): vertical padding channels + edge stitches + rivets where the crown strap lands
        z0, z1, t, c, bsid = spec["bands"][0]
        bm = (sid == bsid).astype(float)
        add_seam(np.abs(z - (z0 + 0.035)), ang * 0.65, bm, depth=0.003, off=0.0, gw=0.01, th=0.0045, spacing=0.055)
        add_seam(np.abs(z - (z1 - 0.035)), ang * 0.65, bm, depth=0.003, off=0.0, gw=0.01, th=0.0045, spacing=0.055)
        chan = np.cos(ang * 4) ** 12
        H[:] += bm * (-0.008 * chan * ss(z0 + 0.03, z0 + 0.06, z) * ss(z1 - 0.03, z1 - 0.06, z) + 0.002 * fbm(P * 12, 2))
        F["groove"][:] = np.maximum(F["groove"], bm * chan * 0.6)
        for sx in (-1, 1):
            d = np.sqrt(y ** 2 + (z - 0.16) ** 2) * (sx * dn[:, 0] > 0.7)
            dome = np.sqrt(np.clip(1 - (d / 0.03) ** 2, 0, 1)) * bm * (sx * dn[:, 0] > 0.7)
            H[:] += 0.01 * dome
            F["rivet"][:] = np.maximum(F["rivet"], dome > 0)
        # crown strap (sid 2): webbing along its length + edge stitches
        st = spec["strap"]
        sm = (sid == st["sid"]).astype(float)
        along = np.arctan2(z - 0.17, x) * 0.6
        add_seam(np.abs(np.abs(y) - (st["w"] / 2 - 0.03)), along, sm, depth=0.002, off=0.0, gw=0.01, th=0.004, spacing=0.05)
        H[:] += sm * 0.0014 * np.sin(2 * math.pi * y / 0.016)
        F["fray"][:] = np.maximum(F["fray"], sm * ss(0.03, 0.0, st["w"] / 2 - np.abs(y)))
    return F


_STENCIL = None


def stencil_sample(u, v):
    global _STENCIL
    if _STENCIL is None:
        img = bpy.data.images.load(os.path.join(SRC, "stencil_back.png"), check_existing=True)
        w, h = img.size
        px = np.zeros(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        _STENCIL = px.reshape(h, w, 4)[:, :, 0]      # rows bottom-up (row 0 = v -1)
        bpy.data.images.remove(img)
    h, w = _STENCIL.shape
    i = np.clip(((u + 1) * 0.5 * w).astype(int), 0, w - 1)
    j = np.clip(((v + 1) * 0.5 * h).astype(int), 0, h - 1)
    return _STENCIL[j, i]


HARDWARE = []


# =====================================================================================================
# textures: colour / roughness / metalness from features
# =====================================================================================================
def C(r, g, b):
    return np.array([r, g, b], dtype=np.float64) / 255.0


def mix(a, b, t):
    t = np.asarray(t)[:, None] if np.ndim(t) else t
    return a * (1 - t) + b * t


def shade(name, P, sid, F):
    n = len(P)
    spec = PARTS[name]
    _, dn = param(spec, P)
    body = (sid == 0).astype(float)
    big = fbm(P * 1.6, 4, seed=21) * 0.5 + 0.5
    mid = fbm(P * 7, 3, seed=22) * 0.5 + 0.5
    grain = fbm(P * 45, 2, seed=23) * 0.5 + 0.5
    H = F["H"]
    cav = np.clip(-H / 0.012, 0, 1)
    # base materials
    if name == "Torso":
        base, worn, rough0 = C(68, 47, 34), C(118, 93, 72), 0.6
    elif name == "Head":
        base, worn, rough0 = C(48, 38, 32), C(90, 77, 64), 0.62
    elif "Arm" in name:
        base, worn, rough0 = C(74, 72, 53), C(112, 108, 86), 0.86
    else:
        base, worn, rough0 = C(56, 55, 45), C(92, 90, 75), 0.86
    col = np.tile(base, (n, 1))
    col *= (0.82 + 0.3 * big)[:, None] * (0.92 + 0.14 * mid)[:, None] * (0.94 + 0.1 * grain)[:, None]
    rough = np.full(n, rough0) + 0.08 * (mid - 0.5) + 0.05 * (grain - 0.5)
    metal = np.zeros(n)
    leather = name in ("Torso", "Head")
    w = F["wear"]
    col = mix(col, worn * (0.9 + 0.2 * mid)[:, None], np.clip(w * (0.35 + 0.6 * mid), 0, 1))
    if leather:
        rough -= 0.1 * w              # polished where it gets hit / rubbed
    col = mix(col, C(170, 150, 120), F["scratch"] * 0.7)
    rough += 0.15 * F["scratch"]
    # dust on upward faces, grime at the bottom
    up = np.clip(dn[:, 2], 0, 1) ** 2
    col = mix(col, C(120, 112, 100), up * 0.25 * (0.5 + big) * body)
    rough += up * 0.1 * body
    zabs = P[:, 2] + spec["loc"][2]
    low = ss(0.9, 0.0, zabs)
    col = mix(col, C(58, 50, 42), low * 0.45 * (0.5 + big))
    # grime where straps and belts press into the bag
    press = np.zeros(n)
    for (z0, z1, t, c, bsid) in spec.get("bands", []):
        d = np.minimum(np.abs(P[:, 2] - z0), np.abs(P[:, 2] - z1)) * ((P[:, 2] < z0) | (P[:, 2] > z1))
        press = np.maximum(press, np.exp(-d / 0.035) * ((P[:, 2] < z0) | (P[:, 2] > z1)))
    col *= (1 - 0.35 * press * body)[:, None]
    # cavities darker (seams, dents, creases)
    col *= (1 - 0.45 * cav)[:, None]
    col *= (1 - 0.25 * F["groove"])[:, None]
    # hand wraps
    wc = F["wrapcloth"]
    wcol = C(150, 143, 124) * (0.8 + 0.25 * mid)[:, None] * (0.93 + 0.1 * grain)[:, None]
    knuck = ss(-0.75, -1.0, P[:, 2])
    wcol = mix(wcol, C(100, 90, 74), np.clip(knuck * 0.85 + 0.45 * (1 - big) ** 2 + 0.3 * ss(0.55, 0.8, fbm(P * 9, 3, seed=41) * 0.5 + 0.5), 0, 1))
    wcol *= (0.85 + 0.15 * F["wraplayer"])[:, None]
    col = mix(col, wcol, wc)
    rough = rough * (1 - wc) + 0.92 * wc
    # rubber boots
    rb = F["rubber"]
    rcol = C(44, 43, 44) * (0.9 + 0.2 * mid)[:, None]
    rcol = mix(rcol, C(92, 90, 86), np.clip(F["edge"] * 0.9 + 0.2 * (big - 0.5), 0, 1))
    rcol = mix(rcol, C(70, 62, 52), ss(-0.85, -1.0, P[:, 2]) * 0.6)
    col = mix(col, rcol, rb)
    rough = rough * (1 - rb) + (0.68 + 0.1 * mid) * rb
    # thread
    th = np.clip(F["thread"] * 1.6, 0, 1) * 0.85
    tcol = C(146, 128, 88) * (0.75 + 0.3 * mid)[:, None]
    tcol = np.where((sid > 0)[:, None], C(92, 90, 86) * (0.9 + 0.2 * mid)[:, None], tcol)
    col = mix(col, tcol, th)
    rough = rough * (1 - th) + 0.66 * th
    # straps (webbing) and padded head band
    strap = ((sid > 0) & (F["metal"] < 0.5)).astype(float)
    if name == "Head":
        band = (sid == 1).astype(float)
        bcol = C(34, 31, 29) * (0.85 + 0.3 * big)[:, None]
        bcol = mix(bcol, C(84, 74, 64), np.clip(F["edge"] * 0.8 + (1 - big) * 0.15, 0, 1))
        bcol *= (1 - 0.35 * np.clip(F["groove"], 0, 1))[:, None]
        col = mix(col, bcol, band * (1 - th))
        rough = rough * (1 - band) + (0.55 + 0.1 * mid) * band
        strap = strap * (sid == 2)
    scol = C(30, 30, 31) * (0.85 + 0.3 * big)[:, None] * (0.9 + 0.2 * grain)[:, None]
    scol = mix(scol, C(68, 66, 62), np.clip(F["fray"] * 0.8 + 0.15 * (1 - mid), 0, 1))
    col = mix(col, scol, strap * (1 - th))
    rough = rough * (1 - strap) + (0.74 + 0.08 * grain) * strap
    # duct tape (silver) and gaffer tape (black)
    tp = np.clip(F["tape"], 0, 1)
    tcol = C(118, 120, 122) * (0.8 + 0.25 * mid)[:, None]
    tcol = mix(tcol, C(72, 68, 62), np.clip(F["tape_edge"] * 0.8 + 0.45 * (1 - big) ** 2 + 0.25 * (1 - mid), 0, 1))
    col = mix(col, tcol, tp)
    rough = rough * (1 - tp) + (0.42 + 0.15 * mid + 0.2 * F["tape_edge"]) * tp
    gf = np.clip(F["gaffer"], 0, 1)
    gcol = C(38, 38, 40) * (0.85 + 0.3 * mid)[:, None]
    col = mix(col, gcol, gf)
    rough = rough * (1 - gf) + (0.6 + 0.1 * mid) * gf
    # paint: stencil + target
    pt = np.clip(F["paint"], 0, 1)
    col = mix(col, C(196, 190, 172) * (0.85 + 0.2 * grain)[:, None], pt * 0.92)
    rough = rough * (1 - pt) + 0.66 * pt
    tg = np.clip(F["target"], 0, 1)
    col = mix(col, C(188, 158, 72) * (0.85 + 0.2 * grain)[:, None], tg * 0.9)
    rough = rough * (1 - tg) + 0.62 * tg
    # metal: steel buckles / plates / rivets with grime and a little brown rust in the corners
    mt = np.clip(np.maximum(F["metal"], F["rivet"]), 0, 1)
    mcol = C(150, 150, 148) * (0.8 + 0.3 * mid)[:, None]
    grime = np.clip((1 - big) * 0.6 + cav * 0.6, 0, 1)
    mcol = mix(mcol, C(68, 66, 62), grime * 0.8)
    rust = ss(0.62, 0.8, fbm(P * 14, 3, seed=31) * 0.5 + 0.5)
    col = mix(col, mcol, mt)
    metal = mt * (1 - rust * 0.9)
    rough = rough * (1 - mt) + (0.32 + 0.3 * grime) * mt
    col = mix(col, C(104, 70, 46) * (0.8 + 0.3 * mid)[:, None], mt * rust)
    rough = rough * (1 - mt * rust) + 0.88 * mt * rust
    return np.clip(col, 0, 1), np.clip(rough, 0.05, 1), np.clip(metal, 0, 1)


# =====================================================================================================
# Blender scene helpers
# =====================================================================================================
def setup_cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == t]
                if devs:
                    for d in prefs.devices:
                        d.use = d.type == t
                    sc.cycles.device = "GPU"
                    log("cycles device", t, [d.name for d in devs])
                    break
            except Exception:
                pass
    except Exception as e:
        log("gpu setup failed", e)
    sc.cycles.samples = samples


def new_image(name, float_=True):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, RES, RES, alpha=True, float_buffer=float_)
    img.colorspace_settings.name = "Non-Color"
    img.generated_color = (0, 0, 0, 0)
    return img


def read_image(img):
    a = np.zeros(RES * RES * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(RES, RES, 4)


def bake_materials(ob, nslots):
    """one emission material per slot: emits either object position or an ID colour into the active image node"""
    mats = []
    for s in range(nslots):
        m = bpy.data.materials.new(f"BK_{ob.name}_{s}")
        try:
            m.use_nodes = True
        except Exception:
            pass
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.name = "ID"
        im = nt.nodes.new("ShaderNodeTexImage")
        im.name = "BAKE"
        enc = nt.nodes.new("ShaderNodeVectorMath")      # emission can't carry negatives: store P/4 + 0.5
        enc.name = "ENC"
        enc.operation = "MULTIPLY_ADD"
        enc.inputs[1].default_value = (0.25, 0.25, 0.25)
        enc.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(tc.outputs["Object"], enc.inputs[0])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        nt.links.new(enc.outputs[0], em.inputs["Color"])
        nt.nodes.active = im
        mats.append(m)
        ob.data.materials.append(m)
    return mats


def set_bake_mode(ob, mode, image, obj_index):
    for s, slot in enumerate(ob.material_slots):
        nt = slot.material.node_tree
        em = [n for n in nt.nodes if n.type == "EMISSION"][0]
        rgb = nt.nodes["ID"]
        for l in list(em.inputs["Color"].links):
            nt.links.remove(l)
        if mode == "pos":
            nt.links.new(nt.nodes["ENC"].outputs[0], em.inputs["Color"])
        else:
            rgb.outputs[0].default_value = ((obj_index + 1) / 8.0, (s + 1) / 16.0, 1.0, 1.0)
            nt.links.new(rgb.outputs[0], em.inputs["Color"])
        im = nt.nodes["BAKE"]
        im.image = image
        nt.nodes.active = im


def select_only(obs, active):
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active


def dilate(arr, cov, iters=10):
    """fill uncovered pixels from covered neighbours (bake margin)"""
    arr = arr.copy()
    cov = cov.copy()
    for _ in range(iters):
        acc = np.zeros_like(arr)
        cnt = np.zeros(cov.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sc = np.roll(np.roll(cov, dy, 0), dx, 1)
            sa = np.roll(np.roll(arr, dy, 0), dx, 1)
            acc += sa * sc[..., None]
            cnt += sc
        fill = (~cov) & (cnt > 0)
        arr[fill] = acc[fill] / cnt[fill][:, None]
        cov = cov | fill
    return arr, cov


def write_png(path, arr):
    """arr (H, W[, C]) uint8, row 0 = top"""
    arr = np.ascontiguousarray(arr)
    h, w = arr.shape[:2]
    c = 1 if arr.ndim == 2 else arr.shape[2]
    ct = {1: 0, 3: 2, 4: 6}[c]
    raw = np.concatenate([np.zeros((h, 1), np.uint8), arr.reshape(h, w * c)], 1).tobytes()

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0)) +
                 chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


# =====================================================================================================
# main
# =====================================================================================================
def main():
    global HARDWARE
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    root = sc.collection
    low_c = bpy.data.collections.new("TrainingDummy")
    hi_c = bpy.data.collections.new("_bake_high")
    root.children.link(low_c)
    root.children.link(hi_c)
    bpy.context.view_layer.update()

    # ---------- low poly ----------
    lows, report = {}, {}
    for name in ORDER:
        V, F, S, hw, _ = build_geometry(name, hi=False)
        if name == "Torso":
            HARDWARE = hw
        ob = make_object(name, V, F, S, low_c)
        ob.location = PARTS[name]["loc"]
        lows[name] = ob
        me = ob.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        co = np.array([v.co[:] for v in me.vertices])
        mn, mx = co.min(0), co.max(0)
        report[name] = dict(tris=int(tris), verts=len(me.vertices), bbox_min=[round(float(a), 4) for a in mn],
                            bbox_max=[round(float(a), 4) for a in mx],
                            bbox_centre_offset=[round(float(a), 4) for a in (mn + mx) / 2],
                            size_roblox_studs=[round(float(mx[0] - mn[0]), 3), round(float(mx[2] - mn[2]), 3), round(float(mx[1] - mn[1]), 3)])
    log("low poly", {k: v["tris"] for k, v in report.items()}, "total", sum(v["tris"] for v in report.values()))

    # ---------- UVs: one atlas per texture set ----------
    for setname, names in SETS.items():
        obs = [lows[n] for n in names]
        select_only(obs, obs[0])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(52), island_margin=0.006, area_weight=0.0,
                                 correct_aspect=True, scale_to_bounds=False)
        try:
            bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, margin=0.006)
        except TypeError:
            bpy.ops.uv.pack_islands(rotate=True, margin=0.006)
        bpy.ops.object.mode_set(mode="OBJECT")

    # ---------- high poly ----------
    highs = {}
    for name in ORDER:
        spec = PARTS[name]
        V, F, S, _, buckles = build_geometry(name, hi=True)
        cl, dn = param(spec, V)
        Fe = features(name, V, vert_sid(V, F, S))
        V2 = V + Fe["H"][:, None] * dn
        ob = make_object(name + "_high", V2, F, S, hi_c)
        ob.location = spec["loc"]
        highs[name] = [ob]
        if buckles is not None:      # steel buckle frames: bevelled, not displaced
            bo = make_object(name + "_high_buckles", buckles[0], buckles[1], buckles[2], hi_c, smooth=False)
            bo.location = spec["loc"]
            mod = bo.modifiers.new("bevel", "BEVEL")
            mod.width = 0.007
            mod.segments = 3
            mod.limit_method = "ANGLE"
            mod.angle_limit = math.radians(40)
            mod.use_clamp_overlap = True
            highs[name].append(bo)
        log("high", name, len(V2), "verts")

    # ---------- bakes ----------
    setup_cycles(1)
    rb = sc.render.bake
    rb.target = "IMAGE_TEXTURES"
    rb.margin = 0
    rb.use_clear = True
    for o in list(low_c.objects) + list(hi_c.objects):
        o.hide_render = True
    stex = {}
    for setname, names in SETS.items():
        if ONLY_SETS and setname not in ONLY_SETS:
            continue
        acc = dict(pos=np.zeros((RES, RES, 3)), nrm=np.zeros((RES, RES, 3)), obj=np.full((RES, RES), -1, int),
                   sid=np.zeros((RES, RES), int))
        cov_all = np.zeros((RES, RES), bool)
        for oi, name in enumerate(names):
            lo, his = lows[name], highs[name]
            nslots = int(max(p.material_index for p in lo.data.polygons)) + 1
            bake_materials(lo, nslots)
            lo.hide_render = False
            img_id, img_pos, img_n = new_image("bk_id"), new_image("bk_pos"), new_image("bk_nrm")
            select_only([lo], lo)
            rb.use_selected_to_active = False
            sc.cycles.samples = 1
            set_bake_mode(lo, "id", img_id, oi)
            bpy.ops.object.bake(type="EMIT")
            set_bake_mode(lo, "pos", img_pos, oi)
            bpy.ops.object.bake(type="EMIT")
            # normal: high -> low
            for hi in his:
                hi.hide_render = False
            set_bake_mode(lo, "pos", img_n, oi)
            select_only(his + [lo], lo)
            rb.use_selected_to_active = True
            rb.use_cage = False
            rb.cage_extrusion = 0.06
            rb.max_ray_distance = 0.14
            rb.normal_space = "TANGENT"
            rb.normal_r, rb.normal_g, rb.normal_b = "POS_X", "POS_Y", "POS_Z"
            sc.cycles.samples = 8
            bpy.ops.object.bake(type="NORMAL")
            for hi in his:
                hi.hide_render = True
            lo.hide_render = True
            idp, pp, nn = read_image(img_id), read_image(img_pos), read_image(img_n)
            cov = idp[..., 2] > 0.5
            acc["pos"][cov] = (pp[..., :3][cov] - 0.5) * 4.0
            acc["nrm"][cov] = nn[..., :3][cov]
            acc["obj"][cov] = oi
            acc["sid"][cov] = np.round(idp[..., 1][cov] * 16).astype(int) - 1
            cov_all |= cov
            for m in list(lo.data.materials):
                bpy.data.materials.remove(m)
            lo.data.materials.clear()
            log("baked", setname, name, int(cov.sum()), "texels")
        # colour / roughness / metal from the features at each texel
        col = np.zeros((RES, RES, 3))
        rou = np.zeros((RES, RES))
        met = np.zeros((RES, RES))
        for oi, name in enumerate(names):
            m = acc["obj"] == oi
            P = acc["pos"][m]
            sid = acc["sid"][m]
            Fe = features(name, P, sid)
            c, r, mt = shade(name, P, sid, Fe)
            col[m], rou[m], met[m] = c, r, mt
        if DEBUG:
            dbg = np.zeros((RES, RES, 3))
            dbg[..., 0] = (acc["obj"] + 1) / 8.0
            dbg[..., 1] = (acc["sid"] + 1) / 8.0
            dbg[..., 2] = cov_all
            write_png(os.path.join(DEBUG, f"ids_{setname}.png"), to8(dbg[::-1]))
        pack = np.concatenate([col, rou[..., None], met[..., None], acc["nrm"]], -1)
        pack, cov2 = dilate(pack, cov_all, 12)
        pack[~cov2] = np.array([0.2, 0.2, 0.2, 0.8, 0.0, 0.5, 0.5, 1.0])
        flip = lambda a: a[::-1]
        base = os.path.join(TEX, f"dummy_{setname.lower()}")
        write_png(base + "_color.png", to8(flip(pack[..., 0:3])))
        write_png(base + "_roughness.png", to8(flip(pack[..., 3])))
        write_png(base + "_metalness.png", to8(flip(pack[..., 4])))
        write_png(base + "_normal.png", to8(flip(pack[..., 5:8])))
        stex[setname] = base
        report.setdefault("_sets", {})[setname] = dict(coverage=round(float(cov_all.mean()), 3), parts=names)
        log("textures", setname)

    if ONLY_SETS:
        log("partial bake (--sets): stopping before materials / export")
        return
    # high polys are not kept in the .blend (re-created by this script)
    for o in list(hi_c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(hi_c)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)

    # ---------- final materials (one per texture set) ----------
    for setname, names in SETS.items():
        m = bpy.data.materials.new(f"NH_Dummy_{setname}")
        try:
            m.use_nodes = True
        except Exception:
            pass
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
        base = stex[setname]

        def tex(suffix, color):
            im = nt.nodes.new("ShaderNodeTexImage")
            img = bpy.data.images.load(base + f"_{suffix}.png", check_existing=False)
            img.colorspace_settings.name = "sRGB" if color else "Non-Color"
            img.filepath = bpy.path.relpath(img.filepath) if bpy.data.filepath else img.filepath
            im.image = img
            return im
        nt.links.new(tex("color", True).outputs[0], bsdf.inputs["Base Color"])
        nt.links.new(tex("roughness", False).outputs[0], bsdf.inputs["Roughness"])
        nt.links.new(tex("metalness", False).outputs[0], bsdf.inputs["Metallic"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex("normal", False).outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
        for n_ in names:
            ob = lows[n_]
            ob.data.materials.clear()
            ob.data.materials.append(m)
            ob.data.polygons.foreach_set("material_index", np.zeros(len(ob.data.polygons), dtype=np.int32))
            ob.data.update()

    with open(os.path.join(OUT, "build_report.json"), "w") as fh:
        json.dump(report, fh, indent=1)

    # ---------- export ----------
    export_fbx(list(lows.values()))
    # ---------- rig ----------
    arm = build_rig(lows)
    export_rigged_fbx(arm, lows)
    # ---------- previews ----------
    if "--no-render" not in argv:
        render_previews(lows, arm)
    path = os.path.join(OUT, "NH_TrainingDummy.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    log("done")


def vert_sid(V, F, S):
    vs = np.zeros(len(V), dtype=np.int32)
    for f, s in zip(F, S):
        if s:
            vs[f] = np.maximum(vs[f], s)
    return vs


def export_fbx(obs):
    """FBX for Studio's 3D importer: 0.01 scale (it reads cm), turned so Blender -Y is front (repo convention)"""
    saved = []
    for ob in obs:
        co = np.zeros(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        saved.append((ob, co.copy(), tuple(ob.location)))
        co = co.reshape(-1, 3)
        co[:, 0] *= -1
        co[:, 1] *= -1
        ob.data.vertices.foreach_set("co", co.reshape(-1))
        ob.data.update()
        ob.location = (-ob.location[0], -ob.location[1], ob.location[2])
    select_only(obs, obs[0])
    bpy.ops.export_scene.fbx(filepath=os.path.join(FBXD, "NH_TrainingDummy.fbx"), use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, global_scale=0.01, axis_forward="-Z", axis_up="Y",
                             mesh_smooth_type="FACE", path_mode="STRIP", embed_textures=False, add_leaf_bones=False,
                             bake_anim=False, use_mesh_modifiers=True)
    for ob, co, loc in saved:
        ob.data.vertices.foreach_set("co", co)
        ob.data.update()
        ob.location = loc
    log("fbx exported")


# R6 joints: bone head = the stock Motor6D pivot (Blender coords, studs; Blender y = Roblox -z).
#   RootJoint HRP->Torso at the Torso centre; Neck C0 (0,1,0); Shoulders C0 (+-1,0.5,0); Hips C0 (+-1,-1,0)
R6_BONES = {
    "HumanoidRootPart": ((0, 0, 3), (0, 0, 3.7), None),
    "Torso": ((0, 0, 3), (0, 0, 4), "HumanoidRootPart"),
    "Head": ((0, 0, 4), (0, 0, 5.1), "Torso"),
    "Right Arm": ((1, 0, 3.5), (1, 0, 2.1), "Torso"),
    "Left Arm": ((-1, 0, 3.5), (-1, 0, 2.1), "Torso"),
    "Right Leg": ((1, 0, 2), (1, 0, 0.6), "Torso"),
    "Left Leg": ((-1, 0, 2), (-1, 0, 0.6), "Torso"),
}


def build_rig(lows):
    """R6 armature: every part 100% weighted to its own bone (rigid, non-bending)"""
    ad = bpy.data.armatures.new("R6")
    ad.display_type = "STICK"
    arm = bpy.data.objects.new("R6_Rig", ad)
    lows["Torso"].users_collection[0].objects.link(arm)
    bpy.context.view_layer.update()
    select_only([arm], arm)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (h, t, parent) in R6_BONES.items():
        b = ad.edit_bones.new(name)
        b.head, b.tail, b.roll = h, t, 0.0
    for name, (h, t, parent) in R6_BONES.items():
        if parent:
            ad.edit_bones[name].parent = ad.edit_bones[parent]
            ad.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, ob in lows.items():
        vg = ob.vertex_groups.new(name=name)
        vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
        mod = ob.modifiers.new("R6", "ARMATURE")
        mod.object = arm
        mw = ob.matrix_world.copy()
        ob.parent = arm
        ob.matrix_world = mw
    log("rig built", list(R6_BONES))
    return arm


def export_rigged_fbx(arm, lows):
    """armature + rigidly skinned parts, same units / turn as the mesh FBX (for Blender / animation tools)"""
    obs = list(lows.values())
    arm.rotation_euler = (0, 0, math.pi)     # Blender -Y front, as in export_fbx
    bpy.context.view_layer.update()
    select_only(obs + [arm], arm)
    bpy.ops.export_scene.fbx(filepath=os.path.join(FBXD, "NH_TrainingDummy_Rigged.fbx"), use_selection=True,
                             object_types={"MESH", "ARMATURE"}, apply_unit_scale=True, global_scale=0.01,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP",
                             embed_textures=False, add_leaf_bones=False, bake_anim=False,
                             use_armature_deform_only=False, primary_bone_axis="Y", secondary_bone_axis="X")
    arm.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    log("rigged fbx exported")


def pose_guard(arm, on=True):
    """a boxing guard to prove the rig: rotations about world axes at each R6 pivot"""
    from mathutils import Matrix
    poses = {"Right Arm": [("X", 78), ("Z", 20)], "Left Arm": [("X", 100), ("Z", -24)],
             "Right Leg": [("X", -14)], "Left Leg": [("X", 16)], "Head": [("X", -8)], "Torso": [("Z", 14)]}
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    if on:
        for name, rots in poses.items():
            pb = arm.pose.bones[name]
            Rw = Matrix.Identity(3)
            for ax, deg in rots:
                Rw = Matrix.Rotation(math.radians(deg), 3, ax) @ Rw
            rest = pb.bone.matrix_local.to_3x3()
            pb.rotation_quaternion = (rest.inverted() @ Rw @ rest).to_quaternion()
    bpy.context.view_layer.update()


def render_previews(lows, arm=None):
    sc = bpy.context.scene
    setup_cycles(SAMPLES)
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1000, 1300
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    for o in lows.values():
        o.hide_render = False
    pc = bpy.data.collections.new("_preview")
    sc.collection.children.link(pc)
    # floor: dark worn gym rubber
    me = bpy.data.meshes.new("floor")
    me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new("PreviewFloor", me)
    pc.objects.link(fl)
    fm = bpy.data.materials.new("PreviewFloor")
    try:
        fm.use_nodes = True
    except Exception:
        pass
    b = fm.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.008, 0.008, 0.009, 1)
    b.inputs["Roughness"].default_value = 0.75
    me.materials.append(fm)
    # world
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.012, 0.013, 0.016, 1)
    bg.inputs[1].default_value = 1.0

    def area(name, loc, rot, energy, size, color):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size, ld.color = energy, size, color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = rot
        pc.objects.link(lo)
        return lo

    def aim(ob, target):
        from mathutils import Vector
        d = Vector(target) - ob.location
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    key = area("Key", (5, 7, 8), (0, 0, 0), 2000, 3, (1.0, 0.93, 0.84)); aim(key, (0, 0, 2.6))
    fill = area("Fill", (-7, 4, 4), (0, 0, 0), 700, 6, (0.75, 0.82, 1.0)); aim(fill, (0, 0, 2.6))
    rim = area("Rim", (-2, -7, 7), (0, 0, 0), 2800, 3, (0.85, 0.9, 1.0)); aim(rim, (0, 0, 3))
    rim2 = area("Rim2", (5, -6, 4), (0, 0, 0), 900, 3, (1.0, 0.9, 0.8)); aim(rim2, (0, 0, 3))
    cd = bpy.data.cameras.new("PreviewCam")
    cd.lens = 70
    cam = bpy.data.objects.new("PreviewCam", cd)
    pc.objects.link(cam)
    sc.camera = cam
    views = {"front": ((0, 14.5, 2.75), (0, 0, 2.55)), "three_quarter": ((9.5, 10.5, 5.2), (0, 0, 2.6)),
             "back": ((0, -14.5, 2.75), (0, 0, 2.55)), "closeup": ((2.6, 5.2, 4.6), (0.1, 0, 3.75)),
             "posed": ((7.5, 11.5, 4.2), (0, 0, 2.6))}
    for vn, (loc, target) in views.items():
        if VIEWS and vn not in VIEWS:
            continue
        if arm is not None:
            pose_guard(arm, vn == "posed")
        cam.location = loc
        aim(cam, target)
        # keep the key light on the camera side
        key.location = (loc[0] * 0.4 + 5 * np.sign(loc[1] or 1), loc[1] * 0.6, 8)
        aim(key, (0, 0, 2.6))
        rim.location = (-2, -7 * np.sign(loc[1] or 1), 7)
        aim(rim, (0, 0, 3))
        fill.location = (-7, 4 * np.sign(loc[1] or 1), 4)
        aim(fill, (0, 0, 2.6))
        sc.render.filepath = os.path.join(PREV, f"preview_{vn}.png")
        bpy.ops.render.render(write_still=True)
        log("rendered", vn)
    if arm is not None:
        pose_guard(arm, False)


if __name__ == "__main__":
    main()
