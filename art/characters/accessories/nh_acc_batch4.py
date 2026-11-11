"""Accessories batch 4: hunter and armory (Kit A 17-20).

  Bandolier   a diagonal oxblood bandolier over the left shoulder to the right hip (clear of the sheathed katana at the
              left hip): stoppered silver-capped holy-water vials (faint blue glass) and whittled ash stakes in leather
              loops, a silver crescent medallion, a silver buckle; three spare stakes on the back
  Pauldrons   blackened-steel pauldrons, one on each arm (each rides its arm, so the R6 arm swing never meets it): a
              domed cop over three lames, rolled edges, brass rivets and filigree, a buckled arming strap
  Gorget      a blackened-steel gorget of three crescent lames on the chest front, brass rivets and filigree, a silver
              sunburst boss, oxblood leather tabs over the collar line (nothing at the nape, where long hair falls)
  Bracers     oxblood leather bracers on both forearms, a riveted blackened-steel plate with brass filigree, two buckled
              straps and a laced back seam
  Gauntlets   flared steel cuffs with a back-of-hand plate and knuckle lames on the outer face only: the right one stops
              above the drawn katana's grip (arm space y -1.05..-0.63, poking out of the hand front and back)
  Crossbow    a compact hunter's crossbow slung diagonally across the back (stirrup down to the right), its sling over
              the left shoulder across the chest; walnut, blackened steel, brass furniture, cocked, no bolt on the string
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch4 --gpu
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, crescent, band_loop, project_out, sash_plane, buckle

TORSO_FRONT = -0.5


# ================================================================== shared helpers
def hunt_mats(M):
    """the hunter palette: blackened steel, silver, brass, oxblood leather, ash, walnut, holy-water glass"""
    return dict(
        steel=A.mat_metal("BlackSteel", (0.050, 0.050, 0.056), rough=0.34, scratch=0.8, wear=0.8, dirt=0.85,
                          tarnish=(0.032, 0.028, 0.026)),
        silver=M["silver"], brass=M["brass"], brassold=M["brassold"],
        oxblood=M["leather_oxblood"],
        strap=A.mat_leather("HuntStrap", (0.15, 0.035, 0.03), wear=0.6),
        thread=A.mat_cloth("WaxThread", (0.55, 0.46, 0.32), weave=900, rough=0.6, sheen=0.1, bump=0.05, twill=False),
        ash=A.mat_set("AshWood", "NH_DeskWood", tint=(1.0, 0.93, 0.80), scale=7.0, normal=0.5, wear=0.2, dirt=0.7),
        walnut=A.mat_set("Walnut", "NH_DeskWood", tint=(0.36, 0.22, 0.15), scale=3.0, normal=0.5, wear=0.35, dirt=0.6,
                         rough_add=-0.08),
        glass=A.mat_flat("HolyGlass", (0.16, 0.30, 0.44), rough=0.06, coat=0.9, noise=12, bump=0.004, vary=0.10, wear=0.0,
                         dirt=0.3),
        cord=A.mat_cloth("Bowstring", (0.42, 0.36, 0.26), weave=700, rough=0.7, sheen=0.1, bump=0.08, twill=True),
    )


def wire(name, pts, r, mat, sides=5, closed=False, smooth_all=True):
    """a light polygonal tube along a poly line (stitching, filigree, rolled edges, cords): `sides`-gon rings with a
    rotation-minimising frame, capped at both ends unless closed"""
    P = [Vector(p) for p in pts]
    if closed and (P[0] - P[-1]).length < 1e-6:
        P = P[:-1]
    n = len(P)
    T = []
    for k in range(n):
        a = P[(k - 1) % n] if closed or k > 0 else P[k]
        b = P[(k + 1) % n] if closed or k < n - 1 else P[k]
        t = (b - a)
        T.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    u = T[0].orthogonal().normalized()
    rings = []
    for k in range(n):
        if k:
            u = u - T[k] * u.dot(T[k])
            u = u.normalized() if u.length > 1e-9 else T[k].orthogonal().normalized()
        v = T[k].cross(u)
        rings.append([P[k] + (u * math.cos(2 * math.pi * i / sides) + v * math.sin(2 * math.pi * i / sides)) * r
                      for i in range(sides)])
    verts, faces = [], []
    for rg in rings:
        verts += rg
    segs = n if closed else n - 1
    for k in range(segs):
        k2 = (k + 1) % n
        for i in range(sides):
            i2 = (i + 1) % sides
            faces.append([k * sides + i, k * sides + i2, k2 * sides + i2, k2 * sides + i])
    if not closed:
        faces.append(list(range(sides))[::-1])
        faces.append([(n - 1) * sides + i for i in range(sides)])
    ob = A.mesh_from(name, verts, faces, mat, smooth_all=smooth_all)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def axis_frame(o, z, x_hint=(1, 0, 0)):
    """a frame at o whose local Z is z (local X as close to x_hint as it can be)"""
    z = Vector(z).normalized()
    x = Vector(x_hint)
    x = (x - z * x.dot(z))
    if x.length < 1e-6:
        x = z.orthogonal()
    x.normalize()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(o)
    return M


def basis_frame(o, X, Y, Z):
    M = Matrix((Vector(X), Vector(Y), Vector(Z))).transposed().to_4x4()
    M.translation = Vector(o)
    return M


def place(ob, M):
    """move a part built at the origin (identity world) into place"""
    ob.data.transform(M @ ob.matrix_world)
    ob.matrix_world = Matrix()
    ob.data.update()
    return ob


def loft(name, rings, mat, caps=True, smooth_all=True):
    """a closed solid through a list of equal-length closed rings (caps fanned to each end ring's centre)"""
    n = len(rings[0])
    verts, faces = [], []
    for r in rings:
        verts += [Vector(p) for p in r]
    for k in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            faces.append([k * n + i, k * n + i2, (k + 1) * n + i2, (k + 1) * n + i])
    if caps:
        for k in (0, len(rings) - 1):
            c = sum((Vector(p) for p in rings[k]), Vector()) / n
            ci = len(verts)
            verts.append(c)
            for i in range(n):
                faces.append([k * n + i, k * n + (i + 1) % n, ci])
    ob = A.mesh_from(name, verts, faces, mat, smooth_all=smooth_all)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def rrect(w, h, r, n=3):
    """a rounded rectangle (half sizes w, h; corner radius r), counter-clockwise, 4 * (n + 1) points"""
    pts = []
    for cx, cy, a0 in ((w - r, h - r, 0), (-w + r, h - r, 90), (-w + r, -h + r, 180), (w - r, -h + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sweep(name, path, sec, mat, up=(0, 0, 1), caps=True):
    """a solid swept along a poly line: sec(t) -> (half width, half height) of a rounded section, the height along
    `up` (projected off the tangent)"""
    P = [Vector(p) for p in path]
    rings = []
    for k, p in enumerate(P):
        t = (P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]).normalized()
        u = Vector(up) - t * Vector(up).dot(t)
        u.normalize()
        s = t.cross(u)
        w, h = sec(k / (len(P) - 1))
        rings.append([p + s * a + u * b for a, b in rrect(w, h, min(w, h) * 0.45, 2)])
    return loft(name, rings, mat, caps)


def rivet(name, at, nrm, mat, r=0.016, h=0.55, seg=8):
    """a domed rivet head on a surface (half of it sunk into the plate)"""
    ob = A.sphere(name, r, (0, 0, 0), mat, scale=(1, 1, h), seg=seg, rings=4 if seg >= 8 else 3)
    ob.matrix_world = axis_frame(at, nrm)
    return ob


def mirror_piece(src, dst):
    """copy every part of piece `src` across the centre plane (x -> -x) into piece `dst`"""
    for ob in [o for o in A.PARTS if o["nh_piece"] == src]:
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix()
        me = ob.data.copy()
        o2 = A._new_obj(ob.name + "_R", me)
        for md in ob.modifiers:
            n = o2.modifiers.new(md.name, md.type)
            for attr in ("width", "segments", "limit_method", "harden_normals"):
                if hasattr(md, attr):
                    setattr(n, attr, getattr(md, attr))
        me.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
        me.flip_normals()
        o2["nh_piece"] = dst
        A.PARTS.append(o2)


def spiral(cx, cy, r0, a0, a1, shrink=0.25, n=14):
    return [(cx + lerp(r0, r0 * shrink, k / n) * math.cos(lerp(a0, a1, k / n)),
             cy + lerp(r0, r0 * shrink, k / n) * math.sin(lerp(a0, a1, k / n))) for k in range(n + 1)]


def filigree(kind="panel"):
    """engraved scrollwork as poly lines in a unit panel (u, v in -1..1), mirror-symmetric about u = 0"""
    lines = []
    if kind == "panel":
        lines.append([(0, -0.95), (0, -0.55), (0, -0.1), (0, 0.4), (0, 0.85)])   # the stem
        for s in (-1, 1):
            # a large C-scroll off the stem, curling in at the top
            arc = [(s * 0.05, -0.45), (s * 0.35, -0.48), (s * 0.66, -0.30), (s * 0.80, 0.02), (s * 0.74, 0.34)]
            a0 = 0.0 if s > 0 else math.pi
            arc += spiral(s * 0.50, 0.30, 0.26, a0, a0 + s * 4.2, 0.3, 10)[1:]
            lines.append(arc)
            # a small counter-scroll at the foot
            lines.append([(s * 0.04, -0.80)] + spiral(s * 0.38, -0.76, 0.16, math.pi if s > 0 else 0,
                                                      (math.pi if s > 0 else 0) - s * 4.2, 0.25, 9))
            # leaves off the stem near the top
            lines.append([(s * 0.02, 0.45), (s * 0.20, 0.58), (s * 0.34, 0.76), (s * 0.22, 0.86), (s * 0.08, 0.70)])
    elif kind == "band":   # a running scroll for long narrow fields (u along, v across)
        for k in range(-3, 4):
            c = k * 0.30
            sg = 1 if k % 2 == 0 else -1
            lines.append(spiral(c, 0.0, 0.55, math.pi * 0.5 * sg, math.pi * 0.5 * sg + 4.0 * sg, 0.25, 7))
        lines.append([(lerp(-1, 1, i / 12), 0.62 * math.sin(i * math.pi / 2)) for i in range(13)])
    return lines


def tubes_on(name, lines, mapfn, r, mat):
    """raised filigree: each poly line mapped through mapfn(u, v) -> point, as a thin tube"""
    for k, ln in enumerate(lines):
        pts = [tuple(mapfn(u, v)) for u, v in ln]
        if len(pts) >= 2:
            wire(f"{name}{k}", pts, r, mat, sides=4)


def arm_wrap(d, x_in=-0.48, a=0.07, n_arc=5, n_face=4, n_out=6, x_out=None):
    """the U-profile (arm-local X, Y; X = x - 1.5 on the left arm) round an arm's front, outer and back faces at
    clearance d; the inner face is flush on the torso side and is left open"""
    R = a + d
    cx, cy = 0.5 - a, 0.5 - a
    pts = []
    for k in range(n_face):
        pts.append((lerp(x_in, cx, k / n_face), -(0.5 + d)))
    for k in range(n_arc + 1):
        ang = math.radians(-90 + 90 * k / n_arc)
        pts.append((cx + R * math.cos(ang), -cy + R * math.sin(ang)))
    for k in range(1, n_out):
        pts.append((0.5 + d, lerp(-cy, cy, k / n_out)))
    for k in range(n_arc + 1):
        ang = math.radians(90 * k / n_arc)
        pts.append((cx + R * math.cos(ang), cy + R * math.sin(ang)))
    for k in range(1, n_face + 1):
        pts.append((lerp(cx, x_in, k / n_face), 0.5 + d))
    return pts


def wrap_surface(name, z0, z1, dfun, mat, thick=0.014, nz=4, x_in=-0.48, cx=1.5, **kw):
    """a band round the arm (left arm, centre x = cx) from z0 (top) to z1 (bottom), clearance dfun(t) (t 0 top .. 1)"""
    cols = []
    for j in range(nz + 1):
        t = j / nz
        cols.append([Vector((cx + X, Y, lerp(z0, z1, t))) for X, Y in arm_wrap(dfun(t), x_in=x_in, **kw)])
    G = [[cols[j][i] for j in range(nz + 1)] for i in range(len(cols[0]))]
    return A.surface(name, G, thick, mat), G


def edge_roll(name, G, j, r, mat):
    """a rolled edge (a tube) along row j of a wrap grid"""
    return wire(name, [tuple(G[i][j]) for i in range(len(G))], r, mat)


def quatrefoil(R, n=32):
    return ccw([(R * (0.74 + 0.26 * abs(math.cos(2 * a))) * math.cos(a), R * (0.74 + 0.26 * abs(math.cos(2 * a))) * math.sin(a))
                for a in (2 * math.pi * k / n for k in range(n))])


def star_pts(n, r1, r2, a0=math.pi / 2):
    return ccw([((r1 if k % 2 == 0 else r2) * math.cos(a0 + math.pi * k / n), (r1 if k % 2 == 0 else r2) * math.sin(a0 + math.pi * k / n))
                for k in range(2 * n)])


# ================================================================== 17. the bandolier
def vial(name, F, X, r=0.040):
    """a stoppered holy-water vial along the frame's Z (cap up): faint blue glass in a silver cage"""
    place(A.lathe(name + "_glass", [(0.0, -0.096), (0.030, -0.096), (r, -0.080), (r, 0.040), (r * 0.86, 0.064),
                                    (0.019, 0.080), (0.017, 0.096), (0.0, 0.096)], (0, 0, 0), X["glass"], seg=10), F)
    place(A.lathe(name + "_foot", [(0.0, -0.112), (r + 0.003, -0.112), (r + 0.006, -0.104), (r + 0.005, -0.084),
                                   (r + 0.001, -0.078), (0.0, -0.078)], (0, 0, 0), X["silver"], seg=10), F)
    place(A.lathe(name + "_cap", [(0.0, 0.088), (0.026, 0.088), (0.027, 0.112), (0.019, 0.120),
                                  (0.010, 0.134), (0.0, 0.137)], (0, 0, 0), X["silver"], seg=10), F)
    for k in range(3):   # the cage's three wires
        a = math.pi / 2 + k * 2 * math.pi / 3
        wire(f"{name}_wire{k}", [tuple(F @ Vector(((r + 0.002) * math.cos(a), (r + 0.002) * math.sin(a), z)))
                                   for z in (-0.080, -0.040, 0.020, 0.052)], 0.0032, X["silver"], sides=4)


def stake(name, F, X, r=0.030):
    """a whittled ash stake along the frame's Z, point down, a silver collar near the head"""
    place(A.lathe(name, [(0.0, -0.165), (0.006, -0.140), (0.016, -0.095), (0.025, -0.045), (r, 0.0), (r, 0.10),
                         (r * 0.86, 0.128), (0.0, 0.138)], (0, 0, 0), X["ash"], seg=7, smooth_all=False), F)
    place(A.lathe(name + "_collar", [(r - 0.004, 0.060), (r + 0.004, 0.062), (r + 0.006, 0.070), (r + 0.006, 0.086),
                                     (r + 0.004, 0.094), (r - 0.004, 0.096)], (0, 0, 0), X["silver"], seg=8), F)


def item_loop(name, F, r, X, w=0.044, foot=0.014, band_y=None):
    """a leather loop over an item lying across a strap: in the frame, the item's axis is Z, the strap surface is at
    local Y = band_y (into the body), the loop arches over the item's front (-Y)"""
    R = r + 0.009
    by = band_y if band_y is not None else r + 0.004
    path = [Vector((R + foot, by, 0))]
    path.append(Vector((R + 0.004, by - 0.004, 0)))
    for k in range(9):
        a = lerp(0.0, -math.pi, k / 8)
        path.append(Vector((R * math.cos(a), R * math.sin(a), 0)))
    path.append(Vector((-R - 0.004, by - 0.004, 0)))
    path.append(Vector((-R - foot, by, 0)))
    G = [[F @ (p + Vector((0, 0, dz))) for p in path] for dz in (-w / 2, w / 2)]
    A.surface(name, G, 0.010, X["strap"])
    for s in (-1, 1):
        rivet(f"{name}_riv{s}", F @ Vector((s * (R + foot * 0.5), by - 0.006, 0)), F.to_3x3() @ Vector((0, -1, 0)),
              X["silver"], r=0.008, seg=6)


@item("Bandolier", "Hunter's bandolier", views=["front34", "front", "side", "back", "close"],
      close=((2.4, -6.2, 0.9), (0.0, 0, 0.18), 82))
def build_bandolier(M):
    X = hunt_mats(M)
    piece("Bandolier", "Torso")
    c, n, d = sash_plane(True)          # over the left shoulder (x 0.92, clear of the hair) to the right hip
    W, OFF, T = 0.26, 0.029, 0.014
    G = band_loop(c, n, W, OFF)
    A.surface("BandStrap", G, T, X["oxblood"])
    for k, kk in ((0, 1), (3, 2)):     # saddle stitching just inside both edges
        pts = [tuple(project_out(G[k][j].lerp(G[kk][j], 0.22), OFF + T / 2 + 0.0005)) for j in range(0, len(G[0]) - 1, 2)]
        wire(f"BandStitch{k}", pts, 0.0032, X["thread"], sides=4, closed=True)
    u = -n                               # across the strap, pointing up toward the right shoulder side
    y_out = TORSO_FRONT - OFF - T / 2    # the strap's outer face on the chest
    base = Vector((c.x, y_out, c.z))
    # the front: a silver medallion near the top, then vials and stakes in loops, a buckle low by the right hip
    kinds = ["V", "S", "V", "V", "S", "V", "V", "S", "V"]
    ts = [0.22 - 0.125 * k for k in range(len(kinds))]
    for k, (kd, t) in enumerate(zip(kinds, ts)):
        r = 0.040 if kd == "V" else 0.030
        at = base + d * t
        F = basis_frame(at + Vector((0, -(r + 0.004), 0)), d, u.cross(d), u)
        if kd == "V":
            vial(f"Vial{k}", F, X, r)
        else:
            stake(f"Stake{k}", F, X, r)
        item_loop(f"Loop{k}", F, r, X)
    # the medallion: a brass quatrefoil, a silver face, a raised crescent and star
    mt = 0.43
    Fm = frame(base + d * mt + Vector((0, -0.001, 0)))
    qf = quatrefoil(0.105)
    A.extrude_poly("MedBack", qf, 0.012, X["brass"], Fm, bevel=0.003, segments=1)
    A.extrude_poly("MedFace", ccw(offset_poly(qf, 0.012)), 0.020, X["silver"], Fm, bevel=0.003, segments=1)
    A.extrude_poly("MedMoon", crescent(-0.012, 0.0, 0.058, 0.026, 0.010, 0.048), 0.032, X["silver"], Fm, bevel=0.0)
    A.extrude_poly("MedStar", [(x + 0.040, z + 0.004) for x, z in star_pts(4, 0.026, 0.009)], 0.030, X["brass"], Fm,
                   bevel=0.0015, segments=1)
    for k in range(4):
        a = k * math.pi / 2
        rivet(f"MedRiv{k}", Fm @ Vector((0.099 * math.cos(a), -0.012, 0.099 * math.sin(a))), (0, -1, 0), X["brass"], r=0.0075)
    # the buckle, low on the front by the right hip, and the strap's tip through its keeper
    bt = -0.93
    ang = math.atan2(d.z, d.x)
    bat = base + d * bt
    tip = ccw([(-0.13, -0.10), (0.05, -0.10), (0.05, 0.10), (-0.13, 0.10), (-0.165, 0.06), (-0.18, 0.0), (-0.165, -0.06)])
    Ft = frame(bat + Vector((0, -0.001, 0)), (0, -ang, 0))
    A.extrude_poly("BandTip", tip, 0.010, X["oxblood"], Ft, bevel=0.003, segments=1)
    for k, x in enumerate((-0.07, -0.12)):
        A.extrude_poly(f"BandHole{k}", A.circle_pts(x, 0.0, 0.011, 10), 0.002, X["steel"],
                       Ft @ Matrix.Translation((0, -0.0095, 0)), bevel=0.0)
    buckle("BandBuckle", bat + Vector((0, -0.011, 0)), 0.10, 0.31, X["silver"], rot=(0, -ang, 0))
    # the back: three spare stakes in loops, low across the back (below where long hair hangs)
    y_back = -TORSO_FRONT + OFF + T / 2
    bb = Vector((c.x, y_back, c.z))
    for k, t in enumerate((-0.30, -0.19, -0.08)):
        at = bb + d * t
        F = basis_frame(at + Vector((0, 0.034, 0)), -d, u.cross(-d), u)
        stake(f"BackStake{k}", F, X, 0.030)
        item_loop(f"BackLoop{k}", F, 0.030, X)
    return dict(notes="oxblood leather bandolier over the left shoulder to the right hip: six silver-capped holy-water vials "
                      "and three ash stakes in loops on the front, three stakes on the back, a silver crescent medallion "
                      "and buckle")


# ================================================================== 18. pauldrons and gorget
COP_A, COP_B, COP_ZC = 0.62, 0.56, 0.54


def cop_point(s, v):
    """the pauldron's domed cop on the LEFT arm: s 0 (the inner edge on the arm top) .. 1 (down the outer face),
    v -1 (front) .. 1 (back); a superellipse over the arm's top-outer corner that dips over the front and back"""
    th = math.radians(lerp(119.0, 0.0, s))
    c, sn = math.cos(th), math.sin(th)
    e = 0.45
    Xp = COP_A * math.copysign(abs(c) ** e, c)
    Zp = COP_B * abs(sn) ** e
    f = smooth(0.80, 1.0, abs(v))
    return Vector((1.5 + Xp * (1 - 0.05 * f), v * 0.63, COP_ZC + Zp * (1 - 0.22 * f)))


def cop_normal(s, v, e=1e-3):
    a = cop_point(min(1, s + e), v) - cop_point(max(0, s - e), v)
    b = cop_point(s, min(1, v + e)) - cop_point(s, max(-1, v - e))
    nm = b.cross(a).normalized()
    p = cop_point(s, v)
    if nm.dot(p - Vector((1.5, 0, 0.45))) < 0:
        nm = -nm
    return nm


@item("Pauldrons", "Blackened steel pauldrons", views=["front34", "front", "side", "back", "close"],
      close=((4.8, -4.4, 2.3), (1.55, 0, 0.62), 92))
def build_pauldrons(M):
    X = hunt_mats(M)
    piece("PauldronL", "LeftArm")
    nu, nv = 22, 26
    G = [[cop_point(i / nu, lerp(-1, 1, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    A.surface("Cop", G, 0.016, X["steel"])
    # rolled edges: round the cop's rim (inner edge, front, back, bottom)
    rim = ([cop_point(0, lerp(-1, 1, j / nv)) for j in range(nv + 1)] +
           [cop_point(i / nu, 1) for i in range(1, nu + 1)] +
           [cop_point(1, lerp(1, -1, j / nv)) for j in range(1, nv + 1)] +
           [cop_point(i / nu, -1) for i in range(nu - 1, 0, -1)])
    wire("CopRoll", [tuple(p) for p in rim], 0.011, X["steel"], closed=True)
    # a low roped ridge along the crown of the cop
    wire("CopRidge", [tuple(cop_point(0.42, v) + cop_normal(0.42, v) * 0.008) for v in [lerp(-0.86, 0.86, k / 14) for k in range(15)]],
           0.010, X["steel"])
    # the haute-piece: a flange standing up from the cop's inner edge, arched, its top rolled outward
    hp = []
    for i in range(17):
        yy = lerp(-0.42, 0.42, i / 16)
        b = cop_point(0.02, yy / 0.63)
        top = 0.045 + 0.125 * max(0.0, math.cos(yy / 0.42 * math.pi / 2)) ** 0.7
        hp.append([b + Vector((0.004 + 0.022 * (j / 4) ** 2, 0, -0.012 + top * j / 4)) for j in range(5)])
    A.surface("HautePiece", hp, 0.014, X["steel"])
    wire("HauteRoll", [tuple(hp[i][-1] + Vector((0.004, 0, 0.004))) for i in range(17)], 0.0105, X["steel"])
    def haute_map(u, v):
        yy = u * 0.30
        h = lerp(0.18, 0.78, (v + 1) / 2)
        b = cop_point(0.02, yy / 0.63)
        top = 0.045 + 0.125 * max(0.0, math.cos(yy / 0.42 * math.pi / 2)) ** 0.7
        return b + Vector((0.004 + 0.022 * h * h - 0.0085, yy, -0.012 + top * h))
    tubes_on("HauteFil", filigree("band"), haute_map, 0.0032, X["brass"])
    # brass filigree on the outer flank of the cop
    def cop_map(uu, vv):
        s = lerp(0.93, 0.58, (vv + 1) / 2)
        v = uu * 0.62
        return cop_point(s, v) + cop_normal(s, v) * 0.0095
    tubes_on("CopFil", filigree("panel"), cop_map, 0.0042, X["brass"])
    # rivets round the cop's rim
    for k in range(9):
        v = lerp(-0.84, 0.84, k / 8)
        rivet(f"CopRivI{k}", cop_point(0.05, v) + cop_normal(0.05, v) * 0.008, cop_normal(0.05, v), X["brass"], r=0.014)
    for k, s in enumerate((0.25, 0.50, 0.75, 0.95)):
        for sg in (-1, 1):
            rivet(f"CopRivE{k}{sg}", cop_point(s, sg * 0.93) + cop_normal(s, sg * 0.93) * 0.008, cop_normal(s, sg * 0.93),
                  X["brass"], r=0.014)
    # three lames below the cop, each tucked under the one above, flaring a little at the hem
    lames = ((0.600, 0.420, 0.094), (0.470, 0.290, 0.074), (0.340, 0.160, 0.054))
    for k, (zt, zb, dd) in enumerate(lames):
        _, L = wrap_surface(f"Lame{k}", zt, zb, lambda t, dd=dd: dd + 0.015 * t, X["steel"], thick=0.013, nz=3,
                            x_in=-0.30, a=min(0.16, (dd - 0.016) / 0.4142), n_arc=6, n_face=3, n_out=6)
        edge_roll(f"LameRoll{k}", L, len(L[0]) - 1, 0.009, X["steel"])
        for i in (0, len(L) // 2, len(L) - 1):     # the articulation rivets at the ends and the centre
            p = L[i][1]
            nrm = (p - Vector((1.5, 0, p.z)))
            nrm.z = 0
            rivet(f"LameRiv{k}_{i}", p + nrm.normalized() * 0.008, nrm, X["brass"], r=0.013)
    # the arming strap round the upper arm and its leather to the lowest lame
    _, S = wrap_surface("ArmStrap", 0.105, 0.035, lambda t: 0.020, X["strap"], thick=0.012, nz=1, x_in=-0.47)
    A.box("ArmLeather", (0.012, 0.062, 0.15), (2.0 + 0.040, 0.0, 0.135), X["strap"], bevel=0.003)
    buckle("ArmBuckle", Vector((2.0 + 0.027, 0.0, 0.07)), 0.085, 0.075, X["brass"], rot=(0, 0, math.radians(90)))
    mirror_piece("PauldronL", "PauldronR")
    piece("PauldronR", "RightArm")
    return dict(notes="blackened steel pauldrons on both arms (each rides its arm): a domed cop over three lames, rolled "
                      "edges, a roped ridge, brass filigree and rivets, an arming strap with a brass buckle")


# the gorget: three crescent lames on the chest front
def g_top(u):
    return 0.365 * u, 0.905 + 0.072 * u * u


def g_bot(u):
    a = u * math.pi / 2
    return 0.38 * math.sin(a), 0.60 + 0.29 * (1 - math.cos(a))


def g_point(u, v, off):
    tx, tz = g_top(u)
    bx, bz = g_bot(u)
    x, z = lerp(tx, bx, v), lerp(tz, bz, v)
    y = TORSO_FRONT - off - 0.030 * (1 - u * u) * (0.6 + 0.4 * v)
    return Vector((x, y, z))


@item("Gorget", "Riveted steel gorget", views=["front34", "front", "side", "close"],
      close=((2.2, -5.4, 1.4), (0, 0, 0.78), 110))
def build_gorget(M):
    X = hunt_mats(M)
    piece("Gorget", "Torso")
    lames = ((0.00, 0.38, 0.046), (0.32, 0.70, 0.032), (0.64, 1.00, 0.019))
    nu = 32
    grids = []
    for k, (v0, v1, off) in enumerate(lames):
        G = [[g_point(lerp(-1, 1, i / nu), lerp(v0, v1, j / 5), off) for j in range(6)] for i in range(nu + 1)]
        A.surface(f"GLame{k}", G, 0.012, X["steel"])
        grids.append(G)
        wire(f"GRoll{k}", [tuple(G[i][-1] + Vector((0, -0.004, 0))) for i in range(nu + 1)], 0.0085, X["steel"])
        for i in (1, nu // 4, nu // 2, 3 * nu // 4, nu - 1):
            p = G[i][2]
            rivet(f"GRiv{k}_{i}", p + Vector((0, -0.007, 0)), (0, -1, 0), X["brass"], r=0.012)
    wire("GRollTop", [tuple(grids[0][i][0] + Vector((0, -0.002, 0.004))) for i in range(nu + 1)], 0.011, X["steel"])
    # oxblood leather lining showing above the top lame, and the tabs over the collar line
    L = [[g_point(lerp(-0.97, 0.97, i / nu), lerp(-0.10, 0.06, j), 0.032) + Vector((0, 0.004, 0.0)) for j in (0, 1)]
         for i in range(nu + 1)]
    A.surface("GLining", L, 0.008, X["oxblood"])
    for s in (-1, 1):
        x = s * 0.445
        path = [Vector((s * 0.40, -0.548, 0.92)), Vector((x, -0.535, 0.975)), Vector((x, -0.522, 1.005)),
                Vector((x, -0.495, 1.019)), Vector((x, -0.44, 1.020))]
        G = [[p + Vector((dx, 0, 0)) for p in path] for dx in (-0.035, 0.0, 0.035)]
        A.surface(f"GTab{s}", G, 0.010, X["strap"])
        rivet(f"GTabRiv{s}", Vector((s * 0.41, -0.565, 0.925)), (0, -1, 0), X["brass"], r=0.013)
    # brass filigree on the wings of the lowest lame and the middle lame
    for s in (-1, 1):
        def m2(uu, vv, s=s):
            u = s * lerp(0.30, 0.78, (uu + 1) / 2)
            v = lerp(0.70, 0.94, (vv + 1) / 2)
            return g_point(u, v, 0.019) + Vector((0, -0.0075, 0))
        tubes_on(f"GFil{s}_", filigree("band"), m2, 0.0038, X["brass"])
        def m1(uu, vv, s=s):
            u = s * lerp(0.28, 0.80, (uu + 1) / 2)
            v = lerp(0.40, 0.62, (vv + 1) / 2)
            return g_point(u, v, 0.032) + Vector((0, -0.0075, 0))
        tubes_on(f"GFilM{s}_", filigree("band"), m1, 0.0034, X["brass"])
    # the silver sunburst boss on the centre of the lower lames
    at = g_point(0, 0.66, 0.019) + Vector((0, -0.010, 0))
    Fb = frame(at)
    A.extrude_poly("GBossRays", star_pts(16, 0.105, 0.062), 0.014, X["silver"], Fb, bevel=0.002, segments=1)
    A.extrude_poly("GBossRim", A.circle_pts(0, 0, 0.066, 32), 0.022, X["brass"], Fb, bevel=0.003, segments=1)
    A.extrude_poly("GBossFace", A.circle_pts(0, 0, 0.052, 32), 0.028, X["silver"], Fb, bevel=0.004, segments=2)
    A.extrude_poly("GBossMoon", crescent(0, 0, 0.034, 0.014, 0.008, 0.028), 0.036, X["brass"], Fb, bevel=0.0015, segments=1)
    return dict(notes="a blackened steel gorget of three crescent lames on the chest front, rolled edges, brass rivets and "
                      "filigree, a silver sunburst boss with a brass crescent, oxblood leather lining and tabs")


# ================================================================== 19. bracers and gauntlets
@item("Bracers", "Hunter's bracers", views=["front34", "front", "side", "back", "close"],
      close=((4.4, -4.8, 0.2), (1.6, 0, -0.38), 92))
def build_bracers(M):
    X = hunt_mats(M)
    piece("BracerL", "LeftArm")
    z0, z1 = -0.13, -0.555
    _, G = wrap_surface("BracerLeather", z0, z1, lambda t: 0.022, X["oxblood"], thick=0.016, nz=5, x_in=-0.36)
    edge_roll("BracerPipeT", G, 0, 0.0095, X["strap"])
    edge_roll("BracerPipeB", G, len(G[0]) - 1, 0.0095, X["strap"])
    # stitching along both edges on the outer face
    for k, z in enumerate((z0 - 0.022, z1 + 0.022)):
        pts = [(1.5 + Xp, Yp, z) for Xp, Yp in arm_wrap(0.0315, x_in=-0.35)]
        wire(f"BracerStitch{k}", pts, 0.0028, X["thread"], sides=4)
    # the riveted steel plate on the outer face, pointed at both ends, with brass filigree
    xo = 2.0 + 0.040
    plate = ccw([(-0.15, -0.12), (-0.11, -0.17), (0.0, -0.205), (0.11, -0.17), (0.15, -0.12), (0.15, 0.12), (0.11, 0.17),
                 (0.0, 0.205), (-0.11, 0.17), (-0.15, 0.12)])
    Fp = Matrix.Translation((xo, 0.0, (z0 + z1) / 2)) @ Matrix.Rotation(math.radians(90), 4, "Z")
    A.extrude_poly("BracerPlate", plate, 0.016, X["steel"], Fp, bevel=0.004, segments=2)
    A.extrude_poly("BracerPlateRim", plate, 0.020, X["steel"], Fp, bevel=0.003, segments=1, holes=[ccw(offset_poly(plate, 0.018))[::-1]])
    tubes_on("BracerFil", filigree("panel"), lambda u, v: Vector((xo + 0.0175, u * 0.105, (z0 + z1) / 2 + v * 0.15)), 0.0036, X["brass"])
    for k, (yy, zz) in enumerate(((-0.12, 0.10), (0.12, 0.10), (-0.12, -0.10), (0.12, -0.10), (0.0, 0.175), (0.0, -0.175))):
        rivet(f"BracerRiv{k}", Vector((xo + 0.019, yy, (z0 + z1) / 2 + zz)), (1, 0, 0), X["brass"], r=0.013)
    # two buckled straps
    for k, zc in enumerate((-0.205, -0.475)):
        _, S = wrap_surface(f"BracerStrap{k}", zc + 0.024, zc - 0.024, lambda t: 0.034, X["strap"], thick=0.010, nz=1, x_in=-0.35)
        buckle(f"BracerBuckle{k}", Vector((1.5 - 0.17, -0.5 - 0.043, zc)), 0.07, 0.062, X["silver"])
        A.box(f"BracerStrapEnd{k}", (0.08, 0.008, 0.040), (1.5 - 0.25, -0.5 - 0.046, zc), X["strap"], bevel=0.003)
    # the laced seam on the back
    yb = 0.5 + 0.031
    for k in range(5):
        z = lerp(z0 - 0.05, z1 + 0.05, k / 4)
        for s in (-1, 1):
            A.torus(f"BracerEye{k}{s}", 0.010, 0.0035, (1.5 + 0.05 + s * 0.055, yb, z), X["brass"], rot=(math.radians(90), 0, 0),
                    major=10, minor=4)
    zz = [lerp(z0 - 0.05, z1 + 0.05, k / 4) for k in range(5)]
    wire("BracerLaceA", [(1.5 + 0.05 + (0.055 if k % 2 else -0.055), yb + 0.005, z) for k, z in enumerate(zz)], 0.0045, X["cord"])
    wire("BracerLaceB", [(1.5 + 0.05 + (-0.055 if k % 2 else 0.055), yb + 0.007, z) for k, z in enumerate(zz)], 0.0045, X["cord"])
    mirror_piece("BracerL", "BracerR")
    piece("BracerR", "RightArm")
    return dict(notes="oxblood leather bracers on both forearms with a riveted blackened steel plate (brass filigree), two "
                      "silver-buckled straps and a laced back seam; the right one ends above the drawn katana's grip")


@item("Gauntlets", "Hunter's gauntlets", views=["front34", "front", "side", "back", "close"],
      close=((4.6, -4.6, -0.1), (1.7, 0, -0.55), 88))
def build_gauntlets(M):
    X = hunt_mats(M)
    piece("GauntletL", "LeftArm")
    z0, z1 = -0.14, -0.555
    # the flared cuff (steel over an oxblood lining that shows at the top)
    _, G = wrap_surface("CuffSteel", z0, z1, lambda t: 0.026 + 0.026 * t * t, X["steel"], thick=0.013, nz=5, x_in=-0.36)
    _, L = wrap_surface("CuffLining", z0 + 0.022, z0 - 0.01, lambda t: 0.019, X["oxblood"], thick=0.008, nz=1, x_in=-0.35)
    edge_roll("CuffRollT", G, 0, 0.0095, X["steel"])
    edge_roll("CuffRollB", G, len(G[0]) - 1, 0.011, X["brassold"])
    # brass filigree on the cuff's outer face and rivets round it
    def cuff_map(u, v):
        t = (1 - v) / 2 * 0.80 + 0.10
        d = 0.026 + 0.026 * t * t
        return Vector((2.0 + d + 0.0075, u * 0.34, lerp(z0, z1, t)))
    tubes_on("CuffFil", filigree("panel"), cuff_map, 0.0038, X["brass"])
    for sg in (-1, 1):   # a running scroll along the cuff's front and back faces
        def side_map(u, v, sg=sg):
            t = (1 - v) / 2 * 0.56 + 0.22
            d = 0.026 + 0.026 * t * t
            return Vector((1.5 + lerp(-0.26, 0.36, (u + 1) / 2), sg * (0.5 + d + 0.0072), lerp(z0, z1, t)))
        tubes_on(f"CuffSide{sg}_", filigree("band"), side_map, 0.0034, X["brass"])
    for k in range(7):
        yy = lerp(-0.40, 0.40, k / 6)
        t = 0.08
        rivet(f"CuffRiv{k}", Vector((2.0 + 0.026 + 0.0072, yy, lerp(z0, z1, t))), (1, 0, 0), X["brass"], r=0.012)
    # the back-of-hand plate (outer face only: the grip of a drawn blade fills the hand's front, bottom and back)
    hp = []
    for i in range(13):
        yy = lerp(-0.40, 0.40, i / 12)
        col = []
        for j in range(5):
            z = lerp(-0.535, -0.80, j / 4)
            bulge = 0.020 * math.cos(yy / 0.40 * math.pi / 2)
            col.append(Vector((2.0 + 0.034 + bulge, yy, z)))
        hp.append(col)
    A.surface("HandPlate", hp, 0.012, X["steel"])
    wire("HandPlateRoll", [tuple(hp[i][-1] + Vector((0.004, 0, 0))) for i in range(13)], 0.0085, X["steel"])
    tubes_on("HandFil", [[(0, -0.8), (0, 0.6)]] + [spiral(s * 0.45, 0.1, 0.35, math.pi * (0 if s > 0 else 1),
                                                        math.pi * (0 if s > 0 else 1) + s * 4.4, 0.25, 10) for s in (-1, 1)],
             lambda u, v: Vector((2.0 + 0.034 + 0.020 * math.cos(u * 0.30 / 0.40 * math.pi / 2) + 0.0075, u * 0.30,
                                  lerp(-0.56, -0.78, (1 - v) / 2))), 0.0034, X["brass"])
    for k, (yy, zz) in enumerate(((-0.34, -0.58), (0.34, -0.58), (-0.34, -0.76), (0.34, -0.76))):
        rivet(f"HandRiv{k}", Vector((2.0 + 0.034 + 0.020 * math.cos(yy / 0.40 * math.pi / 2) + 0.007, yy, zz)), (1, 0, 0),
              X["brass"], r=0.012)
    # knuckle lames, each over the one below, down to the hand's lower edge (outer face only)
    for k, (zt, zb) in enumerate(((-0.785, -0.865), (-0.845, -0.925), (-0.905, -0.975))):
        g = []
        for i in range(11):
            yy = lerp(-0.38, 0.38, i / 10)
            col = []
            for j in range(3):
                z = lerp(zt, zb, j / 2)
                knuck = 0.010 * abs(math.sin(yy / 0.38 * math.pi * 2))
                col.append(Vector((2.0 + 0.040 - 0.006 * k + 0.012 * math.cos(yy / 0.38 * math.pi / 2) + knuck, yy, z)))
            g.append(col)
        A.surface(f"Knuckle{k}", g, 0.011, X["steel"])
        wire(f"KnuckleRoll{k}", [tuple(g[i][-1] + Vector((0.004, 0, 0))) for i in range(11)], 0.0065, X["steel"])
        for s in (-1, 1):
            rivet(f"KnuckleRiv{k}{s}", g[5 + s * 5][1] + Vector((0.007, 0, 0)), (1, 0, 0), X["brass"], r=0.010)
    # the leather strap across the back of the hand, riveted at the plate's sides
    hs = [[Vector((2.0 + 0.034 + 0.020 * math.cos(yy / 0.40 * math.pi / 2) + 0.012, yy, z))
           for yy in [lerp(-0.42, 0.42, i / 12) for i in range(13)]] for z in (-0.668, -0.69, -0.712)]
    A.surface("HandStrap", hs, 0.008, X["strap"])
    for s in (-1, 1):
        rivet(f"HandStrapRiv{s}", Vector((2.0 + 0.034 + 0.020 * math.cos(0.36 / 0.40 * math.pi / 2) + 0.017, s * 0.36, -0.69)),
              (1, 0, 0), X["silver"], r=0.011)
    mirror_piece("GauntletL", "GauntletR")
    piece("GauntletR", "RightArm")
    return dict(notes="flared blackened steel cuffs (brass filigree, oxblood lining, a brass roped hem), a back-of-hand plate "
                      "and three knuckle lames on the outer face; the right one leaves the hand's front, bottom and back "
                      "free for a drawn katana's grip")


# ================================================================== 20. the crossbow
XB_C, XB_D = None, None


def _xb_frame():
    """the crossbow's frame on the back: local X from the butt (upper left) toward the stirrup (lower right) along
    the sling's back path, local Z out from the back, local Y across (the prod's limbs)"""
    c, n, d = sash_plane(True, 0.86)
    Xl = -d
    Zl = Vector((0, 1, 0))
    Yl = Zl.cross(Xl)
    tb = 0.66
    o = Vector((c.x, 0.515, c.z)) + d * tb
    return basis_frame(o, Xl, Yl, Zl), c, d, tb


@item("Crossbow", "Hunter's crossbow", views=["front34", "back", "back34", "side", "close"],
      close=((-2.2, 7.4, 1.4), (-0.05, 0.6, 0.1), 74))
def build_crossbow(M):
    X = hunt_mats(M)
    F, c, d, tb = _xb_frame()
    # ---- the sling: over the left shoulder, across the chest to the right hip, round to the stirrup end; cut where
    # the crossbow lies on the back (its ends meet the swivels at the butt and the stirrup)
    piece("CrossbowStrap", "Torso")
    c2, n2, d2 = sash_plane(True, 0.86)
    G = band_loop(c2, n2, 0.10, 0.052)
    L = 1.62
    t_of = lambda p: (p - Vector((c2.x, p.y, c2.z))).dot(d2)
    inside = lambda p: p.y > 0.3 and (tb - L - 0.06) < t_of(p) < tb + 0.06
    runs, cur = [], []
    for j in range(len(G[0])):
        if any(inside(G[i][j]) for i in range(4)):
            if cur:
                runs.append(cur); cur = []
        else:
            cur.append(j)
    if cur:
        runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(G[0]) - 1:
        runs = [runs[-1] + runs[0][1:]] + runs[1:-1]
    for k, run in enumerate(r for r in runs if len(r) > 1):
        Gs = [[G[i][j] for j in run] for i in range(4)]
        A.surface(f"Sling{k}", Gs, 0.012, X["oxblood"])
        for e, ee in ((0, 1), (3, 2)):
            wire(f"SlingStitch{k}{e}", [tuple(project_out(Gs[e][j].lerp(Gs[ee][j], 0.25), 0.0585)) for j in range(len(run))],
                   0.0026, X["thread"], sides=4)
    # a padded leather shoulder guard under the sling on the shoulder top (the sling rests on it on every body: the
    # depth fit never moves the shoulder top)
    A.box("SlingPad0", (0.17, 0.52, 0.030), (0.865, 0.0, 1.029), X["strap"], bevel=0.012, segments=2)
    wire("SlingPadStitch", [(0.865 + 0.072 * math.cos(2 * math.pi * k / 16) / max(abs(math.cos(2 * math.pi * k / 16)), abs(math.sin(2 * math.pi * k / 16))),
                             0.245 * math.sin(2 * math.pi * k / 16) / max(abs(math.cos(2 * math.pi * k / 16)), abs(math.sin(2 * math.pi * k / 16))),
                             1.0445) for k in range(16)], 0.0025, X["thread"], sides=4, closed=True)
    # a brass buckle and keeper on the chest run
    u2 = -n2
    ang = math.atan2(d2.z, d2.x)
    bat = Vector((c2.x, TORSO_FRONT - 0.052 - 0.006, c2.z)) + d2 * -0.52
    buckle("SlingBuckle", bat + Vector((0, -0.006, 0)), 0.07, 0.135, X["brass"], rot=(0, -ang, 0))
    A.extrude_poly("SlingPad", ccw([(-0.13, -0.065), (0.13, -0.065), (0.15, 0.0), (0.13, 0.065), (-0.13, 0.065), (-0.15, 0.0)]),
                   0.008, X["strap"], frame(bat + d2 * 0.32 + Vector((0, -0.002, 0)), (0, -ang, 0)), bevel=0.003, segments=1)
    for s in (-1, 1):
        rivet(f"SlingPadRiv{s}", bat + d2 * (0.32 + s * 0.10) + Vector((0, -0.010, 0)), (0, -1, 0), X["brass"], r=0.010)

    # ---- the crossbow (local frame F: X along the stock, Y across, Z out from the back)
    piece("Crossbow", "Torso")
    W = lambda p: F @ Vector(p)
    secs = [(0.000, 0.056, 0.074), (0.030, 0.060, 0.082), (0.20, 0.060, 0.078), (0.36, 0.052, 0.064), (0.46, 0.044, 0.050),
            (0.58, 0.042, 0.046), (0.95, 0.042, 0.047), (1.12, 0.048, 0.050), (1.22, 0.054, 0.052)]
    rings = []
    for x, hw, hh in secs:
        rings.append([W((x, a, hh + b)) for a, b in rrect(hw, hh, min(hw, hh) * 0.55, 3)])
    loft("Stock", rings, X["walnut"])
    # the butt plate and the brass bands
    bp = [[W((x, a * 1.06, 0.072 + b * 1.04)) for a, b in rrect(0.056, 0.074, 0.03, 3)] for x in (-0.018, 0.004)]
    loft("ButtPlate", bp, X["steel"])
    for k, (x, hw, hh) in enumerate(((0.43, 0.047, 0.054), (1.05, 0.044, 0.048))):
        loft(f"StockBand{k}", [[W((xx, a * 1.12, hh + b * 1.10)) for a, b in rrect(hw, hh, min(hw, hh) * 0.5, 3)]
                               for xx in (x - 0.018, x + 0.018)], X["brass"])
    # the brass cheek plate with filigree on the butt's outward face
    zt = 0.152
    Fc = F @ Matrix.Translation((0.16, 0.0, zt)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    cheek = ccw([(-0.13, -0.040), (0.10, -0.040), (0.14, 0.0), (0.10, 0.040), (-0.13, 0.040)])
    A.extrude_poly("CheekPlate", cheek, 0.006, X["brass"], Fc, bevel=0.0015, segments=1)
    tubes_on("CheekFil", filigree("band"), lambda u, v: W((0.16 + u * 0.10, v * 0.028, zt + 0.0075)), 0.0030, X["brassold"])
    # the flight groove rails, the nut (latch) and its cocked string
    for s in (-1, 1):
        A.box(f"Rail{s}", (0.50, 0.012, 0.012), tuple(W((0.95, s * 0.016, 0.092))), X["steel"], bevel=0.002,
              rot=F.to_euler())
    nut_at = W((0.70, 0.0, 0.094))
    A.cyl("Nut", 0.032, 0.070, tuple(nut_at), X["brass"], rot=(F.to_3x3() @ Matrix.Rotation(math.radians(90), 3, "X")).to_euler(), verts=14)
    # the tickler: a steel lever folded along the stock's side, pivoted below the nut
    lever = [W((0.62, -0.048, 0.040)), W((0.48, -0.054, 0.036)), W((0.34, -0.060, 0.030)), W((0.28, -0.064, 0.034)), W((0.27, -0.064, 0.046))]
    wire("Lever", [tuple(p) for p in lever], 0.0085, X["steel"])
    A.cyl("LeverPin", 0.012, 0.13, tuple(W((0.66, 0.0, 0.040))), X["brass"],
          rot=(F.to_3x3() @ Matrix.Rotation(math.radians(90), 3, "X")).to_euler(), verts=10)
    # the prod mount and the recurve steel prod
    A.box("ProdMount", (0.18, 0.17, 0.12), tuple(W((1.27, 0.0, 0.064))), X["steel"], bevel=0.016, rot=F.to_euler())
    for s in (-1, 1):
        A.cyl(f"MountBolt{s}", 0.016, 0.012, tuple(W((1.27, s * 0.050, 0.125))), X["brass"], rot=F.to_euler(), verts=10)
    limb = [(1.27, 0.0), (1.265, 0.10), (1.245, 0.22), (1.215, 0.33), (1.190, 0.42), (1.195, 0.47), (1.215, 0.505), (1.245, 0.522)]
    path = [(x, -y) for x, y in reversed(limb)] + limb[1:]
    pts = [W((x, y, 0.062)) for x, y in path]
    def prod_sec(t):
        k = abs(t - 0.5) * 2
        return lerp(0.040, 0.015, k ** 0.8), lerp(0.032, 0.017, k)
    sweep("Prod", [tuple(p) for p in pts], prod_sec, X["steel"], up=tuple(F.to_3x3() @ Vector((0, 0, 1))))
    for s in (-1, 1):
        A.sphere(f"ProdNock{s}", 0.018, tuple(W((1.245, s * 0.522, 0.062))), X["brass"], scale=(1, 1, 1), seg=10, rings=6)
        for k, y in enumerate((0.125, 0.155, 0.185)):   # a cord binding near the mount
            A.torus(f"ProdWrap{s}{k}", 0.039, 0.0065, tuple(W((1.262, s * y, 0.062))), X["cord"],
                    rot=(F.to_3x3() @ Matrix.Rotation(math.radians(90), 3, "X")).to_euler(), major=10, minor=4)
    # the string, drawn back to the nut
    for s in (-1, 1):
        wire(f"String{s}", [tuple(W((1.245, s * 0.522, 0.062))), tuple(W((0.98, s * 0.21, 0.094))), tuple(W((0.72, s * 0.02, 0.118)))],
               0.0062, X["cord"])
    wire("StringNock", [tuple(W((0.72, -0.02, 0.118))), tuple(W((0.705, 0.0, 0.122))), tuple(W((0.72, 0.02, 0.118)))],
           0.0062, X["cord"])
    # the stirrup
    st = [(1.355, -0.070)] + [(1.47 + 0.11 * math.cos(a), 0.125 * math.sin(a)) for a in
                              [lerp(-2.2, 2.2, k / 12) for k in range(13)]] + [(1.355, 0.070)]
    wire("Stirrup", [tuple(W((x, y, 0.052))) for x, y in st], 0.017, X["steel"], sides=6)
    # sling swivels at the butt and the stirrup
    for nm, x, sg in (("SwivelButt", -0.036, -1), ("SwivelFront", 1.598, 1)):
        wire(nm, [tuple(W((x, a, 0.046 + b))) for a, b in rrect(0.060, 0.022, 0.016, 2)], 0.0065, X["steel"], closed=True)
        # the sling's end, doubled back through the swivel and riveted
        fold = [[W((x + sg * dx, a, 0.048)) for dx in (0.0, 0.05, 0.10, 0.13)] for a in (-0.050, 0.0, 0.050)]
        A.surface(nm + "Fold", fold, 0.008, X["oxblood"])
        rivet(nm + "FoldRiv", W((x + sg * 0.085, 0.0, 0.053)), tuple(F.to_3x3() @ Vector((0, 0, 1))), X["brass"], r=0.010)
    # two spare bolts clipped along the stock's upper side
    for k, (yy, zz) in enumerate(((0.050, 0.030), (0.064, 0.058))):
        A.cyl(f"Bolt{k}", 0.0085, 0.50, tuple(W((0.62, yy, zz))), X["ash"],
              rot=(F.to_3x3() @ Matrix.Rotation(math.radians(90), 3, "Y")).to_euler(), verts=8)
        A.cyl(f"BoltHead{k}", 0.016, 0.07, tuple(W((0.905, yy, zz))), X["steel"],
              rot=(F.to_3x3() @ Matrix.Rotation(math.radians(90), 3, "Y")).to_euler(), verts=8, r2=0.0)
        for v in range(3):   # leather fletching
            a = v * 2 * math.pi / 3 + 0.4
            dy, dz = math.cos(a), math.sin(a)
            A.extrude_poly(f"Fletch{k}{v}", ccw([(0.0, 0.0), (0.10, 0.0), (0.075, 0.022), (0.01, 0.022)]), 0.003, X["oxblood"],
                           F @ Matrix.Translation((0.385, yy + dy * 0.008, zz + dz * 0.008)) @
                           Matrix.Rotation(a - math.pi / 2, 4, "X") @ Matrix.Rotation(math.radians(0), 4, "Z"),
                           bevel=0.0)
    for k, x in enumerate((0.40, 0.78)):
        A.box(f"BoltClip{k}", (0.026, 0.040, 0.050), tuple(W((x, 0.054, 0.046))), X["brass"], bevel=0.006, rot=F.to_euler())
    return dict(notes="a compact walnut-and-blackened-steel crossbow slung across the back along its sling (butt at the "
                      "left shoulder blade, stirrup down to the right), cocked with no bolt on the string, two spare "
                      "bolts clipped to the stock; the sling crosses the chest over the left shoulder with a brass buckle")
