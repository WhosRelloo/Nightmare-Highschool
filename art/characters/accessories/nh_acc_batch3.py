"""Accessories batch 3: the race-flavoured pieces (Kit A 13-16). Cosmetic only: anyone may wear them, nothing sets Race.

  OperaClasp     Vampire: a jewelled double clasp in blackened silver, garnet cabochons, two chains swagged across the
                 collarbone in front of the cravat (Collar)
  BatSignet      Vampire: a bat signet ring round the hand end of the left arm, worn like a ring over a glove (Ring)
  MoonTorc       Werewolf: an open twisted-iron torc round the neck, moonstone terminals at the collarbones (Collar)
  FangNecklace   Werewolf: wolf fangs and bone beads on a leather thong (Neck)
  TornFur        Werewolf: a ragged grey-brown fur mantle on the shoulders and upper back, the hem locks sway (Shoulders)
  GhoulLantern   Ghoul: a small corroded iron lantern on a belt hook at the right hip, a faint green-white glow (Hip)
  MossShawl      Ghoul: a draped, mossy, cobwebbed shawl over the shoulders and upper back (Shoulders)
  TatteredHood   Specter: a ragged hood over the head and down to the shoulders; glowing wisps drift from it (Hat)
  ScythePendant  Specter: a small silver scythe on a fine chain (Neck)

Space (nh_acc): studs on the nominal R6 body, torso 2 x 2 x 1 at the origin, -Y the front, +X the character's left.
Neck pieces keep to rings about the neck so they can be worn together: the torc's bar at plan radius 0.615, the cords
and chains at 0.71, the mantles' inner edge at 0.77 (all draped over the torso's top edges, the R6 neck being wider
than the torso is deep). The fronts stay above the bag straps' bands. Long hair falls in r 0.6-0.8 about the neck.
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch3 --gpu
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, drape_point, rbox_sdf

TF = -0.5            # the torso's front face
NECK_R = 0.71        # plan radius of the necklace cords and chains about the neck
MANTLE_R = 0.77      # the mantles' inner edge
DEFAULT_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}


def _hair(h=None):
    """the renders' mannequin hair (nh_acc reads the global; batch 2 sets it when it's imported)"""
    A.MANNEQUIN_HAIR = dict(h or DEFAULT_HAIR)


# ================================================================== helpers
def outward(p):
    """the torso box's outward normal near p (for drapes: away from the body)"""
    e = 1e-3
    g = Vector(((rbox_sdf(p + Vector((e, 0, 0)), r=0.002) - rbox_sdf(p - Vector((e, 0, 0)), r=0.002)),
                (rbox_sdf(p + Vector((0, e, 0)), r=0.002) - rbox_sdf(p - Vector((0, e, 0)), r=0.002)),
                (rbox_sdf(p + Vector((0, 0, e)), r=0.002) - rbox_sdf(p - Vector((0, 0, e)), r=0.002))))
    return g.normalized() if g.length > 1e-9 else Vector((0, 0, 1))


def _fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def sweep(name, path, rfun, mat, nr=10, lobes=0, amp=0.0, turns=0.0, flat=1.0, up=(0, 0, 1), cap0=True, cap1=True, closed=False):
    """a tube along `path` with radius rfun(t) (t = 0..1 along the length); lobes > 0 gives a fluted profile that
    turns `turns` times along the length (a twisted bar; the lobes only ever cut in, so rfun is the outer radius);
    flat scales the profile along the frame's first axis, which starts as `up` projected off the tangent"""
    P = [Vector(p) for p in path]
    n = len(P)
    if closed:
        T = [(P[(i + 1) % n] - P[i - 1]).normalized() for i in range(n)]
        cap0 = cap1 = False
    else:
        T = [(P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized() for i in range(n)]
    u = Vector(up)
    N0 = u - T[0] * u.dot(T[0])
    if N0.length < 1e-6:
        N0 = T[0].orthogonal()
    Ns = [N0.normalized()]
    for i in range(1, n):
        v = Ns[-1] - T[i] * Ns[-1].dot(T[i])
        Ns.append(v.normalized() if v.length > 1e-9 else T[i].orthogonal().normalized())
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    tot = L[-1] or 1.0
    verts, faces = [], []
    for i in range(n):
        t = L[i] / tot
        r = rfun(t) if callable(rfun) else rfun
        B = T[i].cross(Ns[i])
        ph = 2 * math.pi * turns * t
        for k in range(nr):
            a = 2 * math.pi * k / nr
            rr = r * (1 - amp * 0.5 * (1 - math.cos(lobes * (a - ph)))) if lobes else r
            verts.append(P[i] + Ns[i] * (math.cos(a) * rr * flat) + B * (math.sin(a) * rr))
    for i in range(n if closed else n - 1):
        i2 = (i + 1) % n
        sh = 0
        if closed and i2 == 0:   # the frame drifted round the loop: join the last ring to the nearest-turned first
            sh = min(range(nr), key=lambda s_: (verts[i * nr] - verts[s_]).length)
        for k in range(nr):
            k2 = (k + 1) % nr
            faces.append([i * nr + k, i * nr + k2, i2 * nr + (k2 + sh) % nr, i2 * nr + (k + sh) % nr])
    if cap0:
        verts.append(P[0].copy()); c = len(verts) - 1
        for k in range(nr):
            faces.append([c, (k + 1) % nr, k])
    if cap1:
        verts.append(P[-1].copy()); c = len(verts) - 1; b = (n - 1) * nr
        for k in range(nr):
            faces.append([c, b + k, b + (k + 1) % nr])
    return _fix_normals(A.mesh_from(name, verts, faces, mat))


def fine_chain(name, points, link_r, mat, wire=None, major=8, minor=4):
    """nh_acc.chain with lighter links (8 x 4 segments): long necklace chains stay within the tris budget"""
    wire = wire or link_r * 0.26
    pts = [Vector(p) for p in points]
    total = sum((b - a).length for a, b in zip(pts, pts[1:]))
    n = max(2, int(total / (link_r * 1.55)))

    def at(d):
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if d <= L:
                return a + (b - a) * (d / max(L, 1e-9)), (b - a).normalized()
            d -= L
        return pts[-1], (pts[-1] - pts[-2]).normalized()
    obs = []
    for k in range(n):
        p, t = at(k * total / (n - 1))
        q = t.to_track_quat("Z", "Y")
        bpy.ops.mesh.primitive_torus_add(major_radius=link_r * 0.62, minor_radius=wire, major_segments=major, minor_segments=minor)
        ob = bpy.context.object
        ob.scale = (0.62, 1.0, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        rot = q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(90), 4, "Y") @ \
            Matrix.Rotation(math.radians(90 if k % 2 else 0), 4, "X")
        ob.matrix_world = Matrix.Translation(p) @ rot
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obs.append(ob)
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    return A._finish(ob, mat)


def resample(pts, step, closed=False):
    P = [Vector(p) for p in pts] + ([Vector(pts[0])] if closed else [])
    out = [P[0]]
    carry = 0.0
    for a, b in zip(P, P[1:]):
        L = (b - a).length
        d = step - carry
        while d <= L:
            out.append(a + (b - a) * (d / L))
            d += step
        carry = L - (d - step)
    if closed and (out[-1] - out[0]).length < step * 0.5:
        out.pop()
    elif not closed and (out[-1] - P[-1]).length > step * 0.3:
        out.append(P[-1])
    return out


def chaikin(pts, it=2, closed=False):
    P = [Vector(p) for p in pts]
    for _ in range(it):
        Q = []
        rng = range(len(P)) if closed else range(len(P) - 1)
        if not closed:
            Q.append(P[0])
        for i in rng:
            a, b = P[i], P[(i + 1) % len(P)]
            Q += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        if not closed:
            Q.append(P[-1])
        P = Q
    return P


def tag(ob, group="nh_sway"):
    """mark every vertex of a part (the rig functions read the mark after the parts are joined)"""
    vg = ob.vertex_groups.new(name=group)
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    return ob


def tagged_rig(ob, root, cols, group="nh_sway", reach=0.12):
    """a chain rig (Root > H<n> > C<n>_<k>) where only the tagged vertices swing: each is weighted to its nearest
    column (by distance to the column's polyline, blended over neighbouring segments like nh_acc.chain_rig); every
    other vertex rides Root"""
    vg = ob.vertex_groups.get(group)
    member = set()
    if vg is not None:
        gi = vg.index
        for v in ob.data.vertices:
            if any(g.group == gi and g.weight > 0.5 for g in v.groups):
                member.add(v.index)
        ob.vertex_groups.remove(vg)
    keys = {tuple(round(c, 5) for c in (ob.matrix_world @ v.co)) for v in ob.data.vertices if v.index in member}
    bones = [("Root", Vector(root), Vector(root) + Vector((0, 0, 0.08)), None)]
    C = []
    for n, col in enumerate(cols):
        col = [Vector(p) for p in col]
        C.append(col)
        bones.append((f"H{n}", col[0], col[0] + (col[1] - col[0]) * 0.25, "Root"))
        parent = f"H{n}"
        for k in range(len(col) - 1):
            bones.append((f"C{n}_{k + 1}", col[k], col[k + 1], parent))
            parent = f"C{n}_{k + 1}"

    def wfn(co):
        if tuple(round(c, 5) for c in co) not in keys:
            return {"Root": 1.0}
        best = None
        for n, col in enumerate(C):
            for k, (a, b) in enumerate(zip(col, col[1:])):
                d, t = A._seg_dist(co, a, b)
                if best is None or d < best[0]:
                    best = (d, n, k, t)
        d, n, k, t = best
        if d > reach:
            return {"Root": 1.0}
        nseg = len(C[n]) - 1
        if t < 0.35 and k > 0:
            f = 0.5 - t / 0.7
            return {f"C{n}_{k}": f, f"C{n}_{k + 1}": 1 - f}
        if t < 0.35 and k == 0:
            f = (0.35 - t) / 0.35 * 0.85
            return {f"H{n}": f, f"C{n}_1": 1 - f}
        if t > 0.65 and k + 1 < nseg:
            f = (t - 0.65) / 0.7
            return {f"C{n}_{k + 1}": 1 - f, f"C{n}_{k + 2}": f}
        return {f"C{n}_{k + 1}": 1.0}
    return A.make_rig(ob, bones, wfn), bones


def unroll(x, z):
    """a point on the torso's front face (x, z) in the drape's unrolled plan (past the top's front edge)"""
    return (x, -0.5 - (1.0 - z))


def neck_plan(R=NECK_R, v=((0.46, 0.84), (0.30, 0.73), (0.0, 0.66)), n_arc=48, back=0.05):
    """the plan of a closed necklace: an arc of radius R behind the neck (from the top's front edge round the back),
    then a V down the chest through the points v (x, z on the front face, top to bottom, the left half)"""
    th0 = math.asin(0.5 / R)
    left = [unroll(x, z) for x, z in reversed(v)]
    arc = [(R * math.cos(a), (R + back * max(0.0, math.sin(a)) ** 2) * math.sin(a))
           for a in (lerp(-th0, math.pi + th0, k / n_arc) for k in range(n_arc + 1))]
    right = [unroll(-x, z) for x, z in v]
    return left + arc + right[:-1]


def neck_cord(R, v, lift, step=0.022):
    plan = chaikin(neck_plan(R, v), 3, closed=True)
    plan = resample([Vector((x, y, 0)) for x, y, *_ in plan], step, closed=True)
    return [drape_point(p.x, p.y, 1.0, lift) for p in plan]


def cord_at(path, x, front_z=0.97):
    """the point of a draped necklace on the chest front at plan x (the branch on that side of the V)"""
    best = None
    n = len(path)
    for i in range(n):
        a, b = path[i], path[(i + 1) % n]
        if a.y > -0.5 or b.y > -0.5 or a.z > front_z or b.z > front_z:
            continue
        if (a.x - x) * (b.x - x) <= 0 and abs(a.x - b.x) > 1e-9:
            t = (x - a.x) / (b.x - a.x)
            p = a.lerp(b, t)
            if best is None or p.z < best.z:
                best = p
    return best


# ================================================================== materials
def mats_vamp():
    return dict(
        blacksil=A.mat_metal("BlackSilver", (0.20, 0.20, 0.22), rough=0.30, scratch=0.6, wear=0.7, dirt=0.95,
                             tarnish=(0.02, 0.02, 0.024)),
        garnet=A.mat_flat("Garnet", (0.20, 0.006, 0.018), rough=0.04, coat=1.0, noise=140, bump=0.0, vary=0.06,
                          wear=0.0, dirt=0.15),
        onyx=A.mat_flat("Onyx", (0.012, 0.011, 0.014), rough=0.06, coat=1.0, noise=90, bump=0.004, vary=0.03,
                        wear=0.05, dirt=0.3),
    )


def mat_fur(name, rgb):
    """shaggy fur: streaky colour and bump, rough, a little sheen"""
    m, T, bs = A._base(name)
    v = T.coord((70.0, 70.0, 14.0))
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 9
    nz.inputs["Distortion"].default_value = 2.0
    T.L(v, nz.inputs["Vector"])
    col = T.mix(0.45, A._rgb(T, rgb), nz.outputs["Color"], "OVERLAY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.55; bp.inputs["Distance"].default_value = 0.01
    T.L(nz.outputs["Fac"], bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 0.6
    bs.inputs["Sheen Roughness"].default_value = 0.5
    A._weather(T, bs, col, A._val(T, 0.86), A._val(T, 0.0), bp.outputs["Normal"], 0.05, False, 1.0, 0.004)
    return m


# ================================================================== 13. vampire: opera-cape clasp
def quatrefoil(r0, lobe, n=64, phase=0.0):
    return [((r0 + lobe * math.cos(4 * a + phase)) * math.cos(a), (r0 + lobe * math.cos(4 * a + phase)) * math.sin(a))
            for a in (2 * math.pi * k / n for k in range(n))]


def swag(p0, p1, mid, n=24):
    """a hanging curve from p0 to p1 through mid (a quadratic in x: sag and the forward bulge)"""
    p0, p1, mid = Vector(p0), Vector(p1), Vector(mid)
    out = []
    for k in range(n + 1):
        t = k / n
        s = 1 - (2 * t - 1) ** 2
        base = p0.lerp(p1, t)
        out.append(Vector((base.x, base.y + (mid.y - p0.y) * s, base.z + (mid.z - p0.z) * s)))
    return out


@item("OperaClasp", "Opera-cape clasp", close=((2.0, -5.0, 1.25), (0, 0, 0.86), 125))
def build_clasp(M):
    _hair()
    V = mats_vamp()
    bs, gar, silver = V["blacksil"], V["garnet"], M["silver"]
    piece("OperaClasp", "Torso")
    y0 = TF - 0.004
    for side in (-1, 1):
        c = Vector((side * 0.285, y0, 0.905))
        F = frame(c)
        out = ccw(quatrefoil(0.068, 0.024, n=44))
        A.extrude_poly(f"ClaspPlate{side}", out, 0.016, bs, F, bevel=0.004, segments=1)
        rim_in = ccw(quatrefoil(0.054, 0.020, n=44))
        A.extrude_poly(f"ClaspRim{side}", out, 0.026, silver, F, bevel=0.003, segments=1, holes=[rim_in[::-1]])
        # pierced tracery between the rim and the bezel: four lancet piercings on the diagonals, a beaded ring
        for k in range(4):
            a = k * math.pi / 2
            P = [(0.042 * math.cos(a) + 0.010 * math.cos(a + math.pi / 2) * s, 0.042 * math.sin(a) + 0.010 * math.sin(a + math.pi / 2) * s)
                 for s in (-1, 1)]
            tip = (0.066 * math.cos(a), 0.066 * math.sin(a))
            A.extrude_poly(f"ClaspLancet{side}_{k}", ccw([P[0], tip, P[1]]), 0.022, silver, F, bevel=0.002, segments=1)
        for k in range(12):
            a = 2 * math.pi * k / 12 + math.pi / 12
            A.sphere(f"ClaspBead{side}_{k}", 0.0068, c + Vector((0.049 * math.cos(a), -0.024, 0.049 * math.sin(a))), silver, seg=6, rings=4)
        # the bezel and its garnet cabochon, six claws
        A.extrude_poly(f"ClaspBezel{side}", A.circle_pts(0, 0, 0.040, 24), 0.032, silver, F, bevel=0.003, segments=1,
                       holes=[A.circle_pts(0, 0, 0.031, 24)[::-1]])
        A.sphere(f"ClaspStone{side}", 0.034, c + Vector((0, -0.030, 0)), gar, scale=(1, 0.62, 1), seg=20, rings=12)
        for k in range(6):
            a = 2 * math.pi * k / 6 + math.pi / 6
            A.sphere(f"ClaspClaw{side}_{k}", 0.008, c + Vector((0.036 * math.cos(a), -0.046, 0.036 * math.sin(a))), silver,
                     scale=(1, 0.8, 1), seg=6, rings=4)
        # small garnets at the four lobes
        for k in range(4):
            a = k * math.pi / 2
            p = c + Vector((0.074 * math.cos(a), -0.022, 0.074 * math.sin(a)))
            A.torus(f"ClaspSetting{side}_{k}", 0.011, 0.004, p, silver, rot=(math.radians(90), 0, 0), major=12, minor=4)
            A.sphere(f"ClaspGem{side}_{k}", 0.010, p + Vector((0, -0.003, 0)), gar, scale=(1, 0.7, 1), seg=10, rings=6)
        # the chain eyes on the inner side
        for k, (dz, r) in enumerate(((0.032, 0.015), (-0.036, 0.015))):
            A.torus(f"ClaspEye{side}_{k}", r, 0.0045, (side * 0.196, y0 - 0.020, 0.905 + dz), silver,
                    rot=(0, math.radians(90), 0), major=12, minor=5)
    # two chains swagged across, in front of a cravat's knot; a garnet drop on the lower one
    up = swag((0.196, y0 - 0.026, 0.937), (-0.196, y0 - 0.026, 0.937), (0, -0.648, 0.872), 28)
    lo = swag((0.196, y0 - 0.026, 0.869), (-0.196, y0 - 0.026, 0.869), (0, -0.652, 0.800), 28)
    fine_chain("ClaspChainUp", up, 0.026, silver)
    fine_chain("ClaspChainLo", lo, 0.024, silver)
    d = lo[len(lo) // 2]
    A.torus("ClaspDropRing", 0.010, 0.0035, d + Vector((0, 0, -0.014)), silver, rot=(0, math.radians(90), 0), major=10, minor=4)
    A.lathe("ClaspDropCap", [(0.0, 0.0), (0.012, -0.004), (0.014, -0.014), (0.0, -0.016)], d + Vector((0, 0, -0.022)), silver, seg=16)
    A.lathe("ClaspDrop", [(0.0, 0.0), (0.012, -0.006), (0.018, -0.026), (0.013, -0.046), (0.0, -0.060)],
            d + Vector((0, 0, -0.034)), gar, seg=20)
    return dict(notes="blackened-silver quatrefoil clasps with garnet cabochons, beaded rims and pierced tracery; two "
                      "silver chains swag across the collarbone in front of the throat, a garnet drop on the lower one")


# ================================================================== 13. vampire: bat signet ring
RING_Z = -0.78


def bat_outline(w=0.112, h=0.066):
    """a bat with spread scalloped wings and pricked ears (x across, z up), right half mirrored"""
    half = [(0.0, -0.92 * h), (0.10 * w, -0.70 * h), (0.16 * w, -0.48 * h),           # the body's lower point, the hip
            (0.30 * w, -0.62 * h), (0.42 * w, -0.30 * h), (0.58 * w, -0.52 * h),      # scallops along the wing's edge
            (0.70 * w, -0.16 * h), (0.86 * w, -0.30 * h), (1.0 * w, 0.30 * h),       # the wing tip
            (0.80 * w, 0.42 * h), (0.58 * w, 0.62 * h), (0.36 * w, 0.40 * h),       # the wing's leading edge
            (0.18 * w, 0.30 * h), (0.14 * w, 0.62 * h), (0.11 * w, 0.95 * h),       # the shoulder, the ear
            (0.06 * w, 0.52 * h), (0.0, 0.46 * h)]
    right = [(-x, z) for x, z in reversed(half[1:-1])]
    return ccw(half + right)


@item("BatSignet", "Bat signet ring", views=["front34", "front", "side", "back", "close"],
      close=((5.4, -3.0, -0.35), (2.0, -0.04, -0.80), 165))
def build_signet(M):
    _hair()
    V = mats_vamp()
    bs, silver, onyx, gar = V["blacksil"], M["silver"], V["onyx"], V["garnet"]
    piece("BatSignet", "LeftArm")
    tk, hh, off = 0.026, 0.074, 0.005      # band thickness, height, clearance
    o = off + tk / 2
    xo = 2.0 + o                            # the outer face's band line
    # the band: an open (bypass) band round the front, the outer face and the back of the hand, its two ends finished in
    # garnet finials a third of the way in (x 1.37): nothing passes between the arm and the torso, and the inner third of
    # the arm, which swings through the sheathed katana's guard and scabbard at the left hip, carries no metal
    rc = 0.0     # round each corner about the arm box's own corner, so the band keeps its clearance there
    XE = 1.37
    path = [Vector((XE, -0.5 - o, 0))]
    for k in range(9):   # the front-outer corner, rounded about (2.0 - rc, -0.5 + rc)
        a = lerp(-math.pi / 2, 0, k / 8)
        path.append(Vector((2.0 - rc + (rc + o) * math.cos(a), -0.5 + rc + (rc + o) * math.sin(a), 0)))
    for k in range(9):
        a = lerp(0, math.pi / 2, k / 8)
        path.append(Vector((2.0 - rc + (rc + o) * math.cos(a), 0.5 - rc + (rc + o) * math.sin(a), 0)))
    path.append(Vector((XE, 0.5 + o, 0)))
    path = resample(path, 0.03)
    for s in (-1, 1):   # the finials: a silver cap and a garnet bead on each open end
        e = Vector((XE - 0.006, s * (0.5 + o), RING_Z))
        A.sphere(f"SignetCap{s}", 0.026, e, silver, scale=(1.0, 0.60, 1.0), seg=12, rings=8)
        A.sphere(f"SignetBead{s}", 0.017, e + Vector((-0.014, s * 0.012, 0)), gar, scale=(1.0, 0.8, 1.0), seg=10, rings=6)
    G = [[Vector((p.x, p.y, RING_Z + dz)) for p in path] for dz in (-hh / 2, -hh / 6, hh / 6, hh / 2)]
    A.surface("SignetBand", G, tk, bs)
    for dz in (-1, 1):   # silver edges
        sweep(f"SignetEdge{dz}", [Vector((p.x, p.y, RING_Z + dz * hh / 2)) for p in path], 0.0055, silver, nr=5)
    # the bezel: an oval table on the outer face
    F = Matrix.Translation((xo + tk / 2, 0, RING_Z)) @ Matrix.Rotation(math.radians(90), 4, "Z")
    oval = [(0.125 * math.cos(a), 0.098 * math.sin(a)) for a in (2 * math.pi * k / 36 for k in range(36))]
    A.extrude_poly("SignetTable", ccw(oval), 0.022, bs, F, bevel=0.005, segments=1)
    A.extrude_poly("SignetRim", ccw(oval), 0.030, silver, F, bevel=0.003, segments=1,
                   holes=[ccw([(x * 0.86, z * 0.84) for x, z in oval])[::-1]])
    A.extrude_poly("SignetField", ccw([(x * 0.86, z * 0.84) for x, z in oval]), 0.026, onyx, F, bevel=0.0)
    A.extrude_poly("SignetBat", bat_outline(), 0.036, silver, F, bevel=0.0025, segments=1)
    for s in (-1, 1):   # garnet eyes
        A.sphere(f"SignetEye{s}", 0.0065, (xo + tk / 2 + 0.036, s * 0.0055, RING_Z + 0.017), gar, seg=8, rings=5)
    # the shoulders: scrolled flourishes where the band meets the table, front and back
    for s in (-1, 1):
        y = s * 0.128
        A.sphere(f"SignetKnot{s}", 0.017, (xo + tk / 2 + 0.006, y, RING_Z), silver, scale=(0.9, 0.7, 1.25), seg=12, rings=8)
        for dz in (-1, 1):
            P = [(xo + tk / 2 + 0.004, s * (0.128 + 0.03 * t), RING_Z + dz * (0.020 + 0.012 * math.sin(math.pi * t)))
                 for t in (i / 6 for i in range(7))]
            sweep(f"SignetScroll{s}_{dz}", P, lambda t: 0.005 * (1 - 0.5 * t), silver, nr=6)
    return dict(notes="a blackened-silver signet: a silver bat (garnet eyes) on an onyx oval table, scrolled shoulders, "
                      "silver edges; an open band round the left hand's front, outer face and back, its ends finished "
                      "in garnet finials")


# ================================================================== 14. werewolf: moonstone torc
TORC_R, TORC_LIFT = 0.615, 0.05


@item("MoonTorc", "Moonstone torc", close=((1.7, -5.6, 2.1), (0, -0.05, 1.0), 72))
def build_torc(M):
    _hair({"male": "Males_Short", "female": "Females_Short_Mid_Part"})   # hairs that fit it (acc_hairfit)
    iron = A.mat_set("TorcIron", "NH_Iron", tint=(0.17, 0.16, 0.17), scale=2.4, wear=0.75, wear_metal=True, dirt=0.85)
    silver = A.mat_metal("TorcSilver", (0.78, 0.78, 0.82), rough=0.30, tarnish=(0.10, 0.10, 0.11))
    moon = A.mat_flat("Moonstone", (0.72, 0.78, 0.90), rough=0.05, coat=1.0, noise=26, bump=0.008, vary=0.16, wear=0.0,
                      dirt=0.15, sheen=0.7)
    piece("MoonTorc", "Torso")
    gap = math.radians(34)
    a0, a1 = -math.pi / 2 + gap, 3 * math.pi / 2 - gap
    N = 150
    ry = lambda a: TORC_R + 0.085 * max(0.0, math.sin(a)) ** 2   # deeper over the back edge, clear of the head
    path = [drape_point(TORC_R * math.cos(a), ry(a) * math.sin(a), 1.0, TORC_LIFT) for a in (lerp(a0, a1, k / N) for k in range(N + 1))]
    L = sum((b - a).length for a, b in zip(path, path[1:]))
    rad = lambda t: 0.027 + 0.013 * math.sin(math.pi * t) ** 4   # heavy at the nape, slimmer toward the terminals
    sweep("TorcBar", path, rad, iron, nr=12, lobes=4, amp=0.30, turns=L / 0.40, cap0=False, cap1=False)
    # the terminals: a silver collar, an iron knob, a moonstone set in a bezel facing forward and up
    for end, sgn in ((0, 1), (-1, -1)):
        p = path[end]
        t = (path[end] - path[end + sgn]).normalized()   # pointing out of the bar, toward the gap
        sweep(f"TorcCollar{end}", [p - t * 0.012, p, p + t * 0.010], lambda s: 0.034, silver, nr=16)
        for k, dd in enumerate((-0.010, 0.004)):
            sweep(f"TorcWire{end}_{k}", [p - t * (0.024 - dd), p - t * (0.016 - dd)], lambda s: 0.031, silver, nr=16)
        kc = p + t * 0.034
        A.sphere(f"TorcKnob{end}", 0.040, kc, iron, seg=16, rings=10)
        o = (outward(kc) + Vector((0, -0.6, 0.25))).normalized()
        rot = o.to_track_quat("Z", "Y").to_euler()
        A.sphere(f"TorcStone{end}", 0.027, kc + o * 0.031, moon, scale=(1, 1, 0.6), seg=20, rings=10, rot=rot)
        A.torus(f"TorcBezel{end}", 0.027, 0.0055, kc + o * 0.030, silver, rot=rot, major=20, minor=5)
    return dict(notes="an open torc of twisted black iron, heavy at the nape, silver collars and wire wraps at the "
                      "terminals, a moonstone cabochon set in each knob; it rests on the shoulders and dips over the "
                      "front and back edges of the R6 torso")


# ================================================================== 14. werewolf: wolf-fang necklace
FANG_V = ((0.46, 0.85), (0.30, 0.715), (0.0, 0.635))


def fang(name, top, length, r, mat, lean=0.0, curve=0.28):
    """a wolf's canine hanging from `top`: a curved tapering cone, curling forward (away from the chest)"""
    P = []
    for k in range(9):
        t = k / 8
        P.append(Vector(top) + Vector((lean * length * t, -curve * length * t * t, -length * t)))
    return sweep(name, P, lambda t: r * max(0.06, (1 - t) ** 0.8), mat, nr=10, flat=0.80, up=(0, -1, 0), cap1=False)


@item("FangNecklace", "Wolf-fang necklace", close=((2.0, -5.2, 1.25), (0, 0, 0.74), 115))
def build_fangs(M):
    _hair({"male": "Males_Short", "female": "Females_Gojo_PonyV2"})
    thong = A.mat_leather("ThongLeather", (0.16, 0.09, 0.05), scale=4.0, wear=0.6)
    ivory = A.mat_flat("FangIvory", (0.86, 0.80, 0.66), rough=0.32, coat=0.35, noise=90, bump=0.05, vary=0.10, wear=0.25, dirt=1.0)
    bone = A.mat_flat("BeadBone", (0.76, 0.70, 0.57), rough=0.55, noise=60, bump=0.12, vary=0.14, wear=0.3, dirt=1.0)
    horn = A.mat_flat("BeadHorn", (0.10, 0.075, 0.055), rough=0.35, coat=0.3, noise=80, bump=0.04, vary=0.15, wear=0.3, dirt=0.6)
    sinew = A.mat_cloth("Sinew", (0.36, 0.27, 0.17), weave=900, rough=0.7, sheen=0.2, bump=0.3, twill=True)
    piece("FangNecklace", "Torso")
    lift = 0.020
    path = neck_cord(NECK_R, FANG_V, lift)
    sweep("Thong", path, 0.0085, thong, nr=6, closed=True)
    # fangs at the bottom of the V: a large one in the middle, pairs either side
    yb = TF - 0.004
    for k, (x, L, r) in enumerate(((0.0, 0.150, 0.028), (0.070, 0.115, 0.022), (-0.070, 0.115, 0.022),
                                   (0.136, 0.085, 0.018), (-0.136, 0.085, 0.018))):
        c = cord_at(path, x if x != 0 else 1e-4)
        top = Vector((c.x, yb - r * 0.80 - 0.002, c.z - 0.004))
        fang(f"Fang{k}", top, L, r, ivory, lean=-0.10 * x / 0.13)
        A.torus(f"FangWrap{k}", r * 0.95, 0.0055, top + Vector((0, 0, -0.010)), sinew, major=12, minor=4, scale=(1, 0.70, 1))
        A.torus(f"FangWrapB{k}", r * 0.92, 0.0050, top + Vector((0, 0, -0.022)), sinew, major=12, minor=4, scale=(1, 0.70, 1))
    # bone and horn beads strung between the fangs and up the V
    for k, (x, m, rr, ln) in enumerate(((0.034, bone, 0.016, 0.030), (-0.034, bone, 0.016, 0.030),
                                        (0.100, horn, 0.015, 0.024), (-0.100, horn, 0.015, 0.024),
                                        (0.172, bone, 0.018, 0.040), (-0.172, bone, 0.018, 0.040),
                                        (0.214, horn, 0.013, 0.022), (-0.214, horn, 0.013, 0.022),
                                        (0.256, bone, 0.017, 0.036), (-0.256, bone, 0.017, 0.036),
                                        (0.330, horn, 0.012, 0.020), (-0.330, horn, 0.012, 0.020),
                                        (0.380, bone, 0.015, 0.032), (-0.380, bone, 0.015, 0.032))):
        c = cord_at(path, x)
        i = min(range(len(path)), key=lambda j: (path[j] - c).length)
        t = (path[(i + 1) % len(path)] - path[i - 1]).normalized()
        c2 = Vector((c.x, TF - 0.004 - rr * 0.78, c.z))
        seg = [c2 - t * ln / 2 + t * ln * s / 4 for s in range(5)]
        sweep(f"Bead{k}", seg, lambda s: rr * (0.62 + 0.38 * math.sin(math.pi * s) ** 0.5), m, nr=10, flat=0.78, up=(0, -1, 0))
    return dict(notes="five wolf fangs bound with sinew to a leather thong, bone and horn beads up the V; the thong lies "
                      "outside the torc's ring and dips over the back edge")


# ================================================================== 14/15. mantles: the torn fur and the moss shawl
def mantle(Lf, Hs, Hc, xi=0.58, xo=0.95, nA=5, nB=9, nC=16, nu=6, jag=0.0, seed=1, back_in=0.07):
    """the plan (unrolled over the torso's top edges) of a mantle round the shoulders: front lappets x xi..xo hanging
    Lf down the chest, over the shoulders (x up to xo), and a back panel whose hem runs from Hs down the back at its
    outer corners to Hc at the centre; the inner edge follows the circle MANTLE_R round the neck. Returns P[i][j]
    (i inner -> outer, j from the left lappet's bottom round the back to the right one's)"""
    random.seed(seed)
    thA = math.atan2(-math.sqrt(max(0.0, MANTLE_R ** 2 - xi ** 2)), xi)
    thB = math.radians(18)

    def inner(s):   # s: 0..1 over the left half
        if s <= sA:
            return Vector((xi, lerp(-0.5 - Lf, -math.sqrt(MANTLE_R ** 2 - xi ** 2), s / sA)))
        if s <= sB:
            a = lerp(thA, thB, (s - sA) / (sB - sA))
        else:
            a = lerp(thB, math.pi / 2, (s - sB) / (1 - sB))
        return Vector((MANTLE_R * math.cos(a), (MANTLE_R + back_in * max(0.0, math.sin(a)) ** 2) * math.sin(a)))
    hem = bez((xo, 0.5 + Hs), (xo * 0.55, 0.5 + Hs + (Hc - Hs) * 0.25), (xo * 0.18, 0.5 + Hc), (0.0, 0.5 + Hc), 40) + [(0.0, 0.5 + Hc)]

    def outer(s):
        if s <= sA:
            return Vector((xo, lerp(-0.5 - Lf * 1.05, -0.5, s / sA)))
        if s <= sB:
            return Vector((xo, lerp(-0.5, 0.5, (s - sA) / (sB - sA))))
        u = (s - sB) / (1 - sB)
        drop = 0.5 + Hs
        if u < 0.25:
            return Vector((xo, lerp(0.5, drop, u / 0.25)))
        k = (u - 0.25) / 0.75 * (len(hem) - 1)
        i = min(int(k), len(hem) - 2)
        return Vector(hem[i]).lerp(Vector(hem[i + 1]), k - i)
    tot = nA + nB + nC
    sA, sB = nA / tot, (nA + nB) / tot
    ss = [k / tot for k in range(tot + 1)]
    cols = [(inner(s), outer(s)) for s in ss]
    full = cols + [(Vector((-a.x, a.y)), Vector((-b.x, b.y))) for a, b in reversed(cols[:-1])]
    fj = [jag * (0.35 * random.random() + 0.65 * abs(math.sin(k * 1.9 + random.random() * 2)) ** 4) for k in range(len(full))]
    P = [[None] * len(full) for _ in range(nu + 1)]
    for j, (a, b) in enumerate(full):
        bb = b.lerp(a, fj[j])   # torn: the hem bitten back toward the neck
        for i in range(nu + 1):
            P[i][j] = a.lerp(bb, i / nu)
    return P, fj


def drape_grid(P, lift, fold=None):
    G = []
    for i, row in enumerate(P):
        col = []
        for j, q in enumerate(row):
            p = drape_point(q.x, q.y, 1.0, lift)
            if fold:
                p = p + outward(p) * fold(i / (len(P) - 1), j / (len(row) - 1), q)
            col.append(p)
        G.append(col)
    return G


def grid_frame(G, i, j):
    """(point, outward normal, across (inner -> outer) and along directions) at a grid node"""
    nu, nv = len(G) - 1, len(G[0]) - 1
    p = G[i][j]
    du = G[min(i + 1, nu)][j] - G[max(i - 1, 0)][j]
    dv = G[i][min(j + 1, nv)] - G[i][max(j - 1, 0)]
    n = outward(p)
    return p, n, du.normalized(), dv.normalized()


def lock(name, base, d, n, length, w, mats, segs=3, curl=0.25, twist=0.0):
    """one fur lock: a 4-sided tapering clump from base along d, curling outward along n; returns (verts, faces) into
    the caller's mesh lists"""
    d = d.normalized()
    s1 = n.cross(d)
    if s1.length < 1e-6:
        s1 = d.orthogonal()
    s1.normalize()
    s2 = d.cross(s1).normalized()
    ring = []
    for k in range(segs + 1):
        t = k / segs
        c = base + d * (length * t) + n * (curl * length * t * t)
        ww = w * (1 - t) ** 0.9 if k < segs else 0.0
        a0 = twist * t
        ring.append([c + (s1 * math.cos(a0 + q * math.pi / 2) + s2 * 0.6 * math.sin(a0 + q * math.pi / 2)) * ww for q in range(4)]
                    if k < segs else [c])
    return ring


def locks_mesh(name, locks, mat):
    """build one mesh from many lock rings"""
    verts, faces = [], []
    for ring in locks:
        base = len(verts)
        idx = []
        for r in ring:
            idx.append(list(range(len(verts), len(verts) + len(r))))
            verts += r
        for k in range(len(ring) - 1):
            a, b = idx[k], idx[k + 1]
            if len(b) == 1:
                for q in range(4):
                    faces.append([a[q], a[(q + 1) % 4], b[0]])
            else:
                for q in range(4):
                    faces.append([a[q], a[(q + 1) % 4], b[(q + 1) % 4], b[q]])
        faces.append([idx[0][3], idx[0][2], idx[0][1], idx[0][0]])
    if not verts:
        return None
    return _fix_normals(A.mesh_from(name, verts, faces, mat))


def keep_out(p, clear=0.006, xmax=0.985):
    """push a point out of the torso box (and keep it off the arms: |x| <= xmax)"""
    p = Vector((max(-xmax, min(xmax, p.x)), p.y, p.z))
    d = rbox_sdf(p, r=0.002)
    if d < clear:
        p = p + outward(p) * (clear - d)
    return p


# ---------- the torn fur mantle
def _fur_rig(ob):
    return tagged_rig(ob, (0, 0, 1.0), FUR_STRANDS, reach=0.06)


FUR_STRANDS = []


@item("TornFur", "Torn shoulder fur", views=["front34", "front", "side", "back", "back34", "close"],
      close=((4.2, 5.4, 2.6), (0, 0.3, 0.85), 80))
def build_fur(M):
    _hair({"male": "Males_Short", "female": "Females_Low_Ponytail"})
    hide = A.mat_leather("FurHide", (0.20, 0.13, 0.08), scale=2.0, wear=0.6)
    furs = [mat_fur("FurGrey", (0.30, 0.285, 0.27)), mat_fur("FurBrown", (0.27, 0.19, 0.12)),
            mat_fur("FurDark", (0.11, 0.095, 0.085)), mat_fur("FurPale", (0.48, 0.44, 0.38))]
    bonem = A.mat_flat("ClawBone", (0.74, 0.68, 0.55), rough=0.45, coat=0.2, noise=70, bump=0.1, vary=0.12, wear=0.3, dirt=1.0)
    cord = A.mat_leather("FurCord", (0.12, 0.07, 0.04), scale=4.0)
    piece("TornFur", "Torso", rig=_fur_rig, sway="Tails", lock="Z")
    t_hide = 0.024
    P, fj = mantle(0.28, 0.24, 0.50, jag=0.22, seed=4)
    nu, nv = len(P) - 1, len(P[0]) - 1
    lift = 0.012 + t_hide / 2
    G = drape_grid(P, lift, fold=lambda u, v, q: 0.010 * u * (1 + math.sin(v * 37.0)))
    A.surface("FurHide", G, t_hide, hide)
    random.seed(11)
    groups = [[] for _ in furs]
    # clumped locks over the hide, pointing down the drape (or outward from the neck on the shoulder tops)
    for i in range(nu):
        for j in range(nv):
            for _ in range(1 if i < nu - 1 else 2):
                if random.random() < 0.10:
                    continue
                u, v = random.random(), random.random()
                p = (G[i][j] * (1 - u) * (1 - v) + G[i + 1][j] * u * (1 - v) + G[i][j + 1] * (1 - u) * v + G[i + 1][j + 1] * u * v)
                _, n, du, dv = grid_frame(G, i, j)
                g = Vector((0, 0, -1))
                down = g - n * g.dot(n)
                dd = (down.normalized() if down.length > 0.3 else du) * 0.85 + n * 0.42 + Vector(
                    [random.uniform(-0.18, 0.18) for _ in range(3)])
                across = (i + u) / nu
                L = random.uniform(0.07, 0.12) * (1 + 0.7 * across)
                w = random.uniform(0.034, 0.050)
                base = p + n * (t_hide / 2 - 0.006)
                ring = lock("FurLock", base, dd, n, L, w, None, segs=2, curl=0.20, twist=random.uniform(-0.6, 0.6))
                ring = [[keep_out(q) for q in r] for r in ring]
                k = random.choices(range(len(furs)), weights=(0.40, 0.30, 0.18, 0.12))[0]
                groups[k].append(ring)
    # the torn hem: longer locks hanging from the lappets' bottoms and the back hem (the swinging strands)
    FUR_STRANDS.clear()
    strands = [[] for _ in furs]
    hem_js = [j for j in range(0, nv + 1) if P[nu][j].y > 0.5 + 0.05] [::3]
    lap_js = [0, nv]
    starts = []
    for j in hem_js:
        starts.append(("back", j, nu))
    for j in lap_js:
        for i in (1, 3, 5):
            starts.append(("front", j, i))
    for kind, j, i in starts:
        p = G[i][j]
        side = 1 if kind == "back" else -1
        y = side * (0.5 + 0.028)
        L = random.uniform(0.10, 0.16) if kind == "back" else random.uniform(0.09, 0.13)
        x0 = max(-0.94, min(0.94, p.x))
        top = Vector((x0, y, p.z + 0.03))
        drift = random.uniform(-0.04, 0.04)
        pts = [Vector((x0 + drift * (k / 4) ** 2, y + side * 0.05 * (k / 4) ** 1.5, top.z - L * k / 4)) for k in range(5)]
        FUR_STRANDS.append([pts[0], pts[2], pts[4]])
        ring = []
        w = random.uniform(0.030, 0.040)
        for k, c in enumerate(pts):
            t = k / 4
            ww = w * (1 - t) ** 0.8
            if k == 4:
                ring.append([c + Vector((0, 0, -0.01))])
            else:
                ring.append([c + Vector((ww * math.cos(q * math.pi / 2 + 0.4), 0.55 * ww * math.sin(q * math.pi / 2 + 0.4), 0))
                             for q in range(4)])
        kk = random.choices(range(len(furs)), weights=(0.35, 0.35, 0.2, 0.1))[0]
        strands[kk].append(ring)
    for k, m in enumerate(furs):
        A_ob = locks_mesh(f"FurLocks{k}", groups[k], m)
        S_ob = locks_mesh(f"FurStrands{k}", strands[k], m)
        if S_ob is not None:
            tag(S_ob)
    # two bone claws on the lappets, tied with a cord
    for s in (-1, 1):
        x = s * 0.77
        top = Vector((x, TF - 0.05, 0.86))
        fang(f"FurClaw{s}", top, 0.10, 0.020, bonem, lean=0.25 * s)
        A.torus(f"FurClawTie{s}", 0.022, 0.006, top + Vector((0, 0, -0.008)), cord, major=14, minor=5, scale=(1, 0.75, 1))
    return dict(notes="a torn wolf pelt over both shoulders and the upper back: a leather hide under clumped grey, brown, "
                      "dark and pale locks; a ragged hem whose hanging locks swing side to side (Tails, flat on the "
                      "body); two bone claws on the front lappets")


# ---------- the grave-moss shawl
SHAWL_COLS = []


def _shawl_rig(ob):
    return A.chain_rig(ob, (0, 0, 1.0), SHAWL_COLS, rigid_above=0.985)


@item("MossShawl", "Grave-moss shawl", views=["front34", "front", "side", "back", "back34", "close"],
      close=((-4.6, 5.2, 2.2), (-0.1, 0.4, 0.5), 75))
def build_shawl(M):
    _hair({"male": "Males_Short", "female": "Females_Low_Ponytail"})
    wool = A.mat_cloth("ShawlWool", (0.075, 0.080, 0.062), weave=170, rough=0.92, sheen=0.25, bump=0.30, twill=False, vary=0.18,
                       wear=0.35, dirt=0.95)
    moss = A.mat_flat("Moss", (0.085, 0.13, 0.040), rough=0.92, noise=320, bump=0.55, vary=0.40, wear=0.0, dirt=1.0)
    moss2 = A.mat_flat("MossDry", (0.16, 0.16, 0.085), rough=0.92, noise=280, bump=0.45, vary=0.35, wear=0.0, dirt=1.0)
    lichen = A.mat_flat("Lichen", (0.42, 0.45, 0.36), rough=0.85, noise=220, bump=0.3, vary=0.25, wear=0.0, dirt=0.8)
    web = A.mat_flat("Cobweb", (0.80, 0.80, 0.78), rough=0.45, noise=40, bump=0.0, vary=0.05, wear=0.0, dirt=0.2, sheen=0.8)
    piece("MossShawl", "Torso", rig=_shawl_rig, sway="Flutter", lock="Z")
    t = 0.016
    P, fj = mantle(0.44, 0.30, 0.92, xi=0.58, xo=0.95, nA=7, nB=9, nC=18, nu=7, jag=0.12, seed=9, back_in=0.15)
    nu, nv = len(P) - 1, len(P[0]) - 1
    lift = 0.010 + t / 2

    def fold(u, v, q):   # soft vertical folds down the back panel, a roll along the neck edge
        back = smooth(0.5, 0.7, q.y)
        return 0.004 + 0.014 * back * u * (1 + math.sin(q.x * 21.0 + 1.3)) + 0.008 * (1 - u) ** 3
    G = drape_grid(P, lift, fold)
    A.surface("ShawlCloth", G, t, wool)
    random.seed(21)
    # fringe along the hem: short twisted threads
    for j in range(0, nv + 1, 3):
        p, n, du, dv = grid_frame(G, nu, j)
        if p.z > 0.98:
            continue
        side = 1 if p.y > 0 else -1
        L = random.uniform(0.04, 0.09)
        y = side * (0.5 + 0.012)
        P2 = [Vector((p.x + random.uniform(-0.01, 0.01) * k, y, p.z - L * k / 3)) for k in range(4)]
        sweep(f"ShawlFringe{j}", P2, lambda s: 0.0055 * (1 - 0.6 * s), wool, nr=4, flat=0.8, up=(0, 1, 0))
    # moss: lumpy cushions along the neck edge, the shoulders and the hem, lichen flecks between
    clumps = []
    for _ in range(36):
        i = random.choice([1, 1, 2, 2, nu - 1, nu - 1, random.randrange(nu)])
        j = random.randrange(nv)
        u, v = random.random(), random.random()
        p = G[i][j].lerp(G[i + 1][j], u).lerp(G[i][j + 1].lerp(G[i + 1][j + 1], u), v)
        clumps.append(p)
    for k, p in enumerate(clumps):
        n = outward(p)
        r = random.uniform(0.028, 0.055)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(0, 0, 0))
        ob = bpy.context.object; ob.name = f"Moss{k}"
        for vtx in ob.data.vertices:
            q = vtx.co
            q *= 1 + 0.30 * math.sin(q.x * 90 + k) * math.sin(q.y * 80 + 2 * k) * math.sin(q.z * 70)
            q.z *= 0.42
            q.z = max(q.z, -0.15 * r)
        R = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        ob.matrix_world = Matrix.Translation(p + n * (t / 2 + 0.002)) @ R
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for vtx in ob.data.vertices:
            vtx.co = keep_out(vtx.co, 0.006, 0.975)
        for pl in ob.data.polygons:
            pl.use_smooth = True
        A._finish(ob, random.choice([moss, moss, moss2]))
    for k in range(20):
        i, j = random.randrange(nu), random.randrange(nv)
        p = G[i][j].lerp(G[i + 1][j + 1], random.random())
        n = outward(p)
        R = n.to_track_quat("Z", "Y").to_euler()
        A.cyl(f"Lichen{k}", random.uniform(0.012, 0.024), 0.004, tuple(p + n * (t / 2 + 0.001)), lichen, rot=R, verts=8, bevel=0.0)
    # cobwebs: threads strung across the back panel and a small orb web on the right shoulder blade
    def on_cloth(q, off):
        return q + outward(q) * (t / 2 + off)
    threads = []
    for k in range(7):
        low = [(i, j) for i in range(2, nu + 1) for j in range(nv + 1) if G[i][j].y > 0.5 and G[i][j].z < 0.64]
        ia, ja = random.choice([q for q in low if G[q[0]][q[1]].x > 0.15])
        ib, jb = random.choice([q for q in low if G[q[0]][q[1]].x < -0.15])
        a, b = G[ia][ja], G[ib][jb]
        pts = []
        for s in range(13):
            tt = s / 12
            q = a.lerp(b, tt)
            q = Vector((q.x, max(q.y, 0.5) if q.y > 0.3 else q.y, q.z - 0.05 * math.sin(math.pi * tt)))
            pts.append(on_cloth(keep_out(q, 0.0), 0.008))
        threads.append(pts)
    c = drape_point(-0.42, 0.5 + 0.42, 1.0, lift)
    for k in range(7):   # spokes
        a = 2 * math.pi * k / 7 + 0.3
        threads.append([on_cloth(c + Vector((0.16 * s / 6 * math.cos(a), 0, 0.16 * s / 6 * math.sin(a))), 0.010) for s in range(7)])
    for r in (0.05, 0.09, 0.13):   # the spiral turns
        threads.append([on_cloth(c + Vector((r * math.cos(2 * math.pi * s / 21), 0, r * math.sin(2 * math.pi * s / 21))), 0.010)
                        for s in range(22)])
    for k, pts in enumerate(threads):
        pts = [Vector((p.x, max(p.y, TF + 1.0 + 0.0) if p.y > 0.3 else p.y, p.z)) for p in pts]
        sweep(f"Web{k}", [keep_out(p, t / 2 + 0.012) for p in pts], 0.0022, web, nr=4)
    # the sway columns: five down the back panel, one down each front end
    SHAWL_COLS.clear()
    for x in (-0.62, -0.31, 0.0, 0.31, 0.62):
        zh = min(G[nu][j].z for j in range(nv + 1) if abs(G[nu][j].x - x) < 0.12 and G[nu][j].y > 0.3)
        y = 0.5 + 0.03
        SHAWL_COLS.append([Vector((x, y, 0.95)), Vector((x, y, lerp(0.95, zh, 0.4))), Vector((x, y, lerp(0.95, zh, 0.75))),
                           Vector((x, y, zh - 0.02))])
    for s in (-1, 1):
        SHAWL_COLS.append([Vector((s * 0.77, -0.53, 0.95)), Vector((s * 0.77, -0.53, 0.74)), Vector((s * 0.77, -0.53, 0.52))])
    return dict(notes="a coarse grey-green wool shawl over the shoulders, its point hanging down the back; moss cushions "
                      "and lichen along the edges, cobwebs across the back and an orb web on the right shoulder blade, a "
                      "ragged fringe; the back point and the front ends flutter flat on the body")


# ================================================================== 15. ghoul: lantern on a belt hook (right hip)
LX, LY = -1.12, -0.03     # the lantern's axis (the right hip, under the arm)
HOOK = Vector((-1.064, LY, -0.990))


def _lantern_rig(ob):
    return A.pendulum_rig(ob, HOOK, [Vector((LX, LY, -1.12)), Vector((LX, LY, -1.50))])


@item("GhoulLantern", "Ghoul's lantern", views=["front34", "front", "side_r", "back34", "close"],
      close=((-5.2, -3.9, -0.55), (-1.12, -0.03, -1.27), 100))
def build_lantern(M):
    _hair()
    iron = A.mat_set("LanternIron", "NH_Iron", tint=(0.14, 0.13, 0.13), scale=3.0, wear=0.6, wear_metal=True, dirt=0.9)
    rust = A.mat_set("LanternRust", "NH_Iron", tint=(0.34, 0.17, 0.09), scale=2.6, normal=0.9, rough_add=0.15, wear=0.3, dirt=1.0)
    verd = A.mat_flat("Verdigris", (0.16, 0.30, 0.24), rough=0.8, noise=180, bump=0.25, vary=0.3, wear=0.1, dirt=1.0)
    glass = A.mat_glow("GhoulGlass", (0.36, 0.62, 0.44))
    flame = A.mat_glow("GhoulFlame", (0.80, 1.00, 0.84))
    wax = A.mat_flat("GraveWax", (0.62, 0.62, 0.52), rough=0.5, noise=40, bump=0.08, vary=0.1, wear=0.0, dirt=1.0)
    piece("GhoulLantern", "Torso", rig=_lantern_rig, sway="Pendulum", keepout=(1, 0, 0), lock="X")
    # the belt hook: a riveted plate on the right side of the torso and a J hook
    A.box("LanternHookPlate", (0.012, 0.11, 0.12), (-1.006, LY, -0.905), iron, bevel=0.004)
    for dz in (-1, 1):
        A.sphere(f"LanternRivet{dz}", 0.011, (-1.013, LY, -0.905 + dz * 0.04), rust, scale=(0.6, 1, 1), seg=10, rings=6)
    A.tube("LanternHook", [(-1.012, LY, -0.88), (-1.050, LY, -0.880), (-1.074, LY, -0.915), (-1.072, LY, -0.975),
                           (-1.055, LY, -0.996), (-1.036, LY, -0.985), (-1.030, LY, -0.965)], 0.0085, iron, res=6)
    # two links from the hook to the lantern's ring
    fine_chain("LanternChain", [(-1.064, LY, -0.992), (-1.080, LY, -1.035), (-1.098, LY, -1.075)], 0.042, rust, major=10, minor=5)
    A.torus("LanternRing", 0.022, 0.0065, (LX, LY, -1.100), iron, rot=(math.radians(90), 0, 0), major=14, minor=6)
    # the roof: a pierced square pyramid with a finial, flared eaves
    A.lathe("LanternRoof", [(0.0, -1.112), (0.017, -1.114), (0.025, -1.124), (0.034, -1.134), (0.105, -1.170),
                            (0.126, -1.182), (0.129, -1.190), (0.118, -1.194), (0.0, -1.194)],
            (LX, LY, 0), rust, seg=4, rot=(0, 0, math.radians(45)), smooth_all=False)
    A.cyl("LanternFinial", 0.012, 0.02, (LX, LY, -1.118), iron, verts=10, bevel=0.002)
    for k in range(4):   # vent holes on the roof faces (dark slots)
        a = k * math.pi / 2
        A.box(f"LanternVent{k}", (0.03, 0.006, 0.012), (LX + 0.052 * math.cos(a), LY + 0.052 * math.sin(a), -1.153),
              iron, rot=(math.radians(-38) if k % 2 == 0 else 0, 0, a + math.pi / 2), bevel=0.0015)
    h = 0.072   # half-width of the cage
    A.box("LanternTop", (2 * h + 0.012, 2 * h + 0.012, 0.018), (LX, LY, -1.203), iron, bevel=0.004)
    A.box("LanternBase", (2 * h + 0.016, 2 * h + 0.016, 0.022), (LX, LY, -1.452), iron, bevel=0.005)
    A.lathe("LanternFoot", [(0.0, -1.463), (0.070, -1.463), (0.060, -1.478), (0.040, -1.486), (0.030, -1.500), (0.0, -1.502)],
            (LX, LY, 0), rust, seg=24)
    for sx in (-1, 1):
        for sy in (-1, 1):
            A.box(f"LanternPost{sx}{sy}", (0.016, 0.016, 0.24), (LX + sx * h, LY + sy * h, -1.327), iron, bevel=0.003)
            A.sphere(f"LanternBoss{sx}{sy}", 0.012, (LX + sx * h, LY + sy * h, -1.198), rust, seg=10, rings=6)
    # glass panes (the faint green-white glow) behind iron guard bars
    for k in range(4):
        a = k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        c = Vector((LX + ca * (h - 0.004), LY + sa * (h - 0.004), -1.327))
        A.box(f"LanternPane{k}", (0.005 if abs(ca) > 0.5 else 2 * h - 0.012, 2 * h - 0.012 if abs(ca) > 0.5 else 0.005, 0.228),
              tuple(c), glass, bevel=0.0)
        for dz in (-0.07, 0.0, 0.07):
            A.box(f"LanternBar{k}_{dz}", (0.008 if abs(ca) > 0.5 else 2 * h, 2 * h if abs(ca) > 0.5 else 0.008, 0.008),
                  (LX + ca * (h + 0.006), LY + sa * (h + 0.006), -1.327 + dz), iron, bevel=0.002)
        for s in (-1, 1):   # crossed wires
            P = [(LX + ca * (h + 0.009) - sa * (h - 0.01) * s * (1 - 2 * q), LY + sa * (h + 0.009) + ca * (h - 0.01) * s * (1 - 2 * q),
                  -1.327 - 0.10 + 0.20 * q) for q in (0.0, 0.5, 1.0)]
            A.tube(f"LanternWire{k}_{s}", P, 0.0028, iron, res=3, poly=True)
    # the door's hinge and latch on the outer face
    A.box("LanternLatch", (0.012, 0.024, 0.03), (LX - h - 0.012, LY - 0.03, -1.30), rust, bevel=0.003)
    A.torus("LanternLatchRing", 0.012, 0.003, (LX - h - 0.018, LY - 0.03, -1.32), iron, rot=(0, math.radians(90), 0), major=10, minor=4)
    # inside: a stub of grave wax and its pale flame
    A.lathe("LanternCandle", [(0.0, -1.441), (0.026, -1.441), (0.024, -1.40), (0.022, -1.372), (0.012, -1.366), (0.0, -1.368)],
            (LX, LY, 0), wax, seg=16)
    A.sphere("LanternFlame", 0.018, (LX, LY, -1.335), flame, scale=(1, 1, 1.9), seg=12, rings=8)
    # verdigris crusts on the roof edges and the foot
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        A.sphere(f"LanternCrust{k}", 0.010, (LX + 0.075 * math.cos(a), LY + 0.075 * math.sin(a), -1.186), verd,
                 scale=(1.6, 1.6, 0.6), seg=8, rings=5)
    return dict(notes="a small corroded iron lantern, rusted roof and foot with verdigris crusts, guarded green glass "
                      "panes and a grave-wax candle with a pale green-white flame (emissive); hangs from a belt hook on "
                      "the right hip, swings fore and aft", glow=[0.62, 1.0, 0.72])


# ================================================================== 16. specter: tattered hood with wisps
HOOD_RINGS = [   # z, centre y, rx, ry (the hem's own drop added per angle): a baggy crown (the barber's hairs reach r 0.8 at
    # the temples), a cowl a little narrower on the shoulders, a tall peak that leans back
    (1.110, 0.040, 0.770, 0.715), (1.135, 0.040, 0.775, 0.740), (1.180, 0.038, 0.795, 0.780), (1.265, 0.032, 0.825, 0.830),
    (1.400, 0.030, 0.835, 0.850), (1.560, 0.030, 0.835, 0.858), (1.720, 0.034, 0.830, 0.856), (1.880, 0.042, 0.822, 0.848),
    (2.010, 0.050, 0.808, 0.838), (2.110, 0.062, 0.780, 0.815), (2.210, 0.080, 0.735, 0.775), (2.300, 0.112, 0.660, 0.705),
    (2.385, 0.162, 0.548, 0.590), (2.460, 0.232, 0.410, 0.445), (2.530, 0.318, 0.275, 0.295), (2.590, 0.420, 0.150, 0.160),
    (2.635, 0.520, 0.060, 0.062), (2.660, 0.580, 0.012, 0.012),
]
FACE_LO, FACE_HI = 1.16, 2.25
WISPS = []


def _ring_at(k):
    """the hood's ring k on a Catmull-Rom through HOOD_RINGS (k from 0 to len-1, fractional)"""
    n = len(HOOD_RINGS)
    i = min(int(k), n - 2)
    f = k - i
    p = [Vector(HOOD_RINGS[max(0, min(n - 1, i + d))]) for d in (-1, 0, 1, 2)]
    return 0.5 * ((2 * p[1]) + (-p[0] + p[2]) * f + (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3]) * f * f +
                  (-p[0] + 3 * p[1] - 3 * p[2] + p[3]) * f ** 3)


def face_hw(z):
    """the face opening's half-width at height z (a pointed arch at the top, a point at the throat)"""
    if z <= FACE_LO or z >= FACE_HI:
        return 0.0
    t = (z - FACE_LO) / (FACE_HI - FACE_LO)
    return 0.56 * math.sin(math.pi * t) ** 0.55 * (1 - 0.30 * smooth(0.55, 1.0, t))


def _hood_rig(ob):
    return tagged_rig(ob, (0, 0, SEAT_H), WISPS, reach=0.10)


SEAT_H = 1.93


def _noise1(n, seed, smooth_pass=2):
    random.seed(seed)
    v = [random.random() for _ in range(n)]
    for _ in range(smooth_pass):
        v = [(v[i - 1] + 2 * v[i] + v[(i + 1) % n]) / 4 for i in range(n)]
    lo, hi = min(v), max(v)
    return [(x - lo) / (hi - lo + 1e-9) for x in v]


@item("TatteredHood", "Tattered hood", close=((3.4, -5.4, 2.4), (0, 0.1, 1.75), 80))
def build_hood(M):
    _hair({"male": "Males_Short", "female": "Females_Preppy_Long_Braided"})   # both fit it at k 1.04-1.06
    cloth = A.mat_cloth("ShroudCloth", (0.030, 0.029, 0.034), weave=190, rough=0.92, sheen=0.3, bump=0.30, twill=True,
                        vary=0.12, wear=0.45, dirt=0.9)
    # (coordinator review: the five glowing wisp ribbons read as flat white shards from behind, since a SurfaceAppearance
    # can't be see-through without an alpha map; the wisps are drifting particles in the game now, from the extra.json)
    piece("TatteredHood", "Head")
    nu, nv = 52, 30
    nk = len(HOOD_RINGS) - 1
    rag = _noise1(nu + 1, 5, 1)          # the torn hem's lengths
    random.seed(6)
    tears = {random.randrange(nu + 1) for _ in range(7)}   # a few deep rips up into the cowl
    rows = [tuple(_ring_at(nk * j / nv)) for j in range(nv + 1)]
    G = [[None] * (nv + 1) for _ in range(nu + 1)]
    for j, (z, cy, rx, ry) in enumerate(rows):
        hw = face_hw(z)
        w = math.asin(min(0.98, hw / rx)) if hw > 0 else 0.0
        thL, thR = -math.pi / 2 + w, 3 * math.pi / 2 - w
        fold_amp = 0.030 * smooth(1.75, 1.14, z)          # soft folds falling to the cowl
        brow = 0.07 * smooth(1.70, 2.12, z) * (1 - smooth(2.15, 2.35, z))   # the hood droops forward over the brow
        for i in range(nu + 1):
            th = lerp(thL, thR, i / nu)
            fold = 1 + fold_amp * (0.5 + 0.5 * math.sin(7 * th + 1.1 + 0.6 * math.sin(3 * th)))
            front = max(0.0, -math.sin(th)) ** 2
            zz, rrx, rry = z, rx * fold, (ry + brow * front) * fold
            if j <= 2:   # the hem: ragged everywhere, and only drops where it hangs behind the back
                yb = cy + ry * math.sin(th)
                back = smooth(0.56, 0.72, yb)
                f = 1 - j / 3
                cut = rag[i]
                drop = 0.22 * back * (0.35 + 0.85 * cut) - 0.03 * (1 - back) * (1 - cut)
                if i in tears:
                    drop -= 0.06 * (1 - back)
                zz = z - drop * f
                rry = rry + 0.06 * back * f
            G[i][j] = Vector((rrx * math.cos(th), cy + rry * math.sin(th), zz))
    A.surface("HoodShell", G, 0.022, cloth)
    # the face opening's rolled, frayed edge
    jl = [j for j in range(nv + 1) if face_hw(rows[j][0]) > 0]
    loop = [G[0][j] for j in [jl[0] - 1] + jl + [jl[-1] + 1]] + [G[nu][j] for j in reversed(jl)]
    loop = [p + Vector((0, -0.004, 0)) for p in loop]
    sweep("HoodEdge", chaikin(loop, 1, closed=True), 0.016, cloth, nr=6, closed=True)
    WISPS.clear()
    return dict(notes="a deep, ragged shroud hood of charcoal wool: a tall peak that leans back, the brow drooping over a "
                      "rolled and frayed face opening, soft folds down to the cowl on the shoulders, a torn hem hanging "
                      "behind the back; pale wisps drift off it in the game (particles)")


# ================================================================== 16. specter: scythe pendant
SCY_V = ((0.46, 0.85), (0.28, 0.745), (0.0, 0.705))


@item("ScythePendant", "Scythe pendant", close=((1.3, -5.4, 1.05), (-0.04, -0.52, 0.66), 125))
def build_scythe(M):
    _hair({"male": "Males_Short", "female": "Females_Gojo_PonyV2"})
    silver = A.mat_metal("ScytheSilver", (0.88, 0.88, 0.90), rough=0.20, tarnish=(0.14, 0.14, 0.15), wear=0.4)
    dark = A.mat_metal("ScytheDark", (0.25, 0.25, 0.27), rough=0.30, tarnish=(0.04, 0.04, 0.045), wear=0.6)
    onyx = A.mat_flat("PendantOnyx", (0.012, 0.011, 0.014), rough=0.06, coat=1.0, noise=90, bump=0.004, vary=0.03, wear=0.05)
    piece("ScythePendant", "Torso")
    lift = 0.026
    path = neck_cord(NECK_R, SCY_V, lift, step=0.03)
    bot = min((p for p in path if p.y < -0.5), key=lambda p: p.z)
    k0 = path.index(bot)
    loop = path[k0:] + path[:k0 + 1]
    fine_chain("PendantChain", [tuple(p) for p in loop], 0.030, silver, major=6, minor=4)
    yb = TF - 0.004
    # the bail and the snath (the long handle), with its two grips; a small onyx bead at its foot
    top = Vector((0.0, yb - 0.013, bot.z - 0.018))
    A.torus("PendantBail", 0.014, 0.0045, top + Vector((0, -0.002, 0.004)), silver, rot=(0, math.radians(90), 0), major=12, minor=5)
    sn = [top + Vector((0.012 * math.sin(t * 2.4) - 0.004, 0, -0.18 * t)) for t in (k / 8 for k in range(9))]
    sweep("PendantSnath", sn, lambda t: 0.0085 - 0.002 * t, dark, nr=10, flat=0.85, up=(0, -1, 0))
    for k, (zt, s) in enumerate(((0.05, 1), (0.11, -1))):
        p = sn[0] + Vector((0, 0, -zt))
        sweep(f"PendantGrip{k}", [p, p + Vector((s * 0.030, 0, 0.006))], lambda t: 0.0055, dark, nr=8, flat=0.85, up=(0, -1, 0))
    A.sphere("PendantFoot", 0.013, sn[-1] + Vector((0, -0.001, -0.010)), onyx, scale=(1, 0.8, 1), seg=12, rings=8)
    # the blade: a long crescent sweeping to the wearer's right from a collar at the snath's head
    A.torus("PendantCollar", 0.011, 0.005, top + Vector((0, 0, -0.016)), silver, major=12, minor=5, scale=(1, 0.8, 1))
    spine = bez((0.004, -0.010), (-0.05, 0.030), (-0.12, 0.030), (-0.175, -0.035), 14) + [(-0.175, -0.035)]
    edge = bez((-0.175, -0.035), (-0.12, 0.002), (-0.06, -0.002), (0.004, -0.032), 14)
    blade = ccw(spine + edge[1:])
    F = frame(top + Vector((0, 0.009, -0.004)))
    A.extrude_poly("PendantBlade", blade, 0.010, silver, F, bevel=0.0025, segments=2)
    # an engraved groove (fuller) along the blade: a thin raised spine bead
    sweep("PendantFuller", [F @ Vector((x * 0.96, -0.011, z - 0.006)) for x, z in spine[2:-2]], 0.0025, dark, nr=5)
    return dict(notes="a small silver scythe on a fine silver chain: a crescent blade with a darkened fuller, a darkened "
                      "snath with two grips and an onyx bead at its foot")
