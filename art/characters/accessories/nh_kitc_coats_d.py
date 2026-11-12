"""Kit C coats D: three closed-front coats on the Kit C coat architecture (see nh_acc_batchc1.py).

  CadetCoat        the Academy cadet coat (unisex): black wool, double-breasted (two rows of brass buttons), crimson
                   frogging across the chest between the rows, crimson piping on every edge, a low stand collar,
                   pointed crimson cuffs, a half-belt; mid-thigh skirts with the slit to the hem
  ChesterfieldCoat the Chesterfield overcoat (Male): black wool, a black velvet upper collar on long-roll notch lapels,
                   a fly front (the buttons hidden under a plain placket), flapped hip pockets, a breast welt;
                   knee-length skirts
  CardiganCoat     the cable-knit cardigan coat (unisex): ink-blue knit with cables (a procedural bump, no geometry), a
                   big rolled shawl collar, horn toggles on leather tabs, ribbed cuffs, hem band and front band;
                   knee-length skirts with patch pockets

Every coat is the Kit C set: <Key>Shell (Torso, rigid), <Key>Skirt (Torso, skinned to F_LL / F_RL: each half rides
its leg), <Key>SleeveL/R (the arms).

The closed front: Kit A's shell is open (lapels). Here both front panels run to the centre (x +-0.003) below the break
or neckline, and an overlap panel (the "flap", in the Shell piece) lies on top of them: full thickness from its visible
edge, then tapering to 0.002 so the far side blends flush into the panel beneath (it reads as one front overlapping
the other). Its inner face is 0.001 off the shell's outer face. The shell's side-front cutaway (x <= 0.74 below
z -0.26, the sheathed katana's guard) is kept: every front detail stays inside it.

Necklines follow the Kit C shell (nh_acc_batchc1.build_shell_k): wide at the shoulders (xo_top ~0.72) and scooped
down the back to nape_z 0.78, so the collars sit low, clear of the hair.

Build: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- CadetCoat --nobake --out E:/NH-Work/kitc_coats_d
(--selfcheck prints the triangle overlaps between this item's own parts, before they are joined)
"""
import math
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import ccw
from nh_acc_batch4 import wire, axis_frame, place, mirror_piece, arm_wrap
import nh_acc_batch7 as K7
from nh_acc_batch7 import (cloth, out_hint_torso, button, cut_line, band_grid, back_fold, build_lapel, front_point,
                           back_point, half_belt, pocket_flap, sleeve_hint, wrap_kw, x_in, X_IN_LOW, X_IN_TOP,
                           D_F, T_SHELL, T_BAND, HEM_BACK, ARC, TOP_Y)
import nh_acc_batchc1 as C1

SH_OUT = 0.5 + D_F + T_SHELL / 2      # |y| of the shell's outer face (front and back): 0.532
SH_TOP = 1.0 + D_F + T_SHELL / 2      # z of its outer face on the shoulder tops
Z = Vector((0, 0, 1))


# ================================================================== the closed shell
def shell_rows_d(P):
    """the shell's rows on one side (x >= 0), as Kit A's / Kit C's: front face (hem up; its front edge from
    P["edge"](z)), round the front top edge, across the shoulder top (the neckline a circle through (xo_top, front)),
    round the back top edge, down the back (the scooped Kit C back neckline)"""
    d = D_F
    rn = math.hypot(P["xo_top"], 0.5 + d)
    rows = []
    for z in P["front_z"]:
        rows.append((-(0.5 + d), z, "front", P["edge"](z), cut_line(z)))
    for a in ARC:
        y = -0.5 - d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for y in TOP_Y:
        rows.append((y, 1.0 + d, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for a in ARC[::-1]:
        y = 0.5 + d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for z in C1.BACK_Z_K:
        rows.append((0.5 + d, z, "back", C1.back_neck(z, P), 1.0))
    return rows


def shell_grid_d(side, P, ncol=None):
    ncol = ncol or P.get("ncol", 9)
    rows = shell_rows_d(P)
    G = []
    for i in range(ncol + 1):
        col = []
        for (y, z, reg, xs, xe) in rows:
            x = lerp(xs, xe, i / ncol)
            col.append(Vector((side * x, y + (back_fold(x, z, P) if reg == "back" else 0.0), z)))
        G.append(col)
    return G, rows


# ---------------------------------------------------------------- the overlap panel ("flap")
def flap_range(F):
    return min(F["e"], F["g"]), max(F["e"], F["g"])


def flap_t(x, F):
    """the flap's thickness at x: full from the visible edge e to f, tapering to 0.002 at the far end g"""
    u = (x - F["e"]) / (F["g"] - F["e"])
    uf = (F["f"] - F["e"]) / (F["g"] - F["e"])
    if u <= uf:
        return F["t"]
    return lerp(F["t"], 0.002, smooth(uf, 1.0, u))


def outer_y(x, F, z=None):
    """|y| of the outermost front face at x (the flap where it lies, else the shell)"""
    if F is None:
        return SH_OUT
    lo, hi = flap_range(F)
    if lo - 1e-9 <= x <= hi + 1e-9 and (z is None or (-0.72 <= z <= F["top"](x))):
        return SH_OUT + F["gap"] + flap_t(x, F)
    return SH_OUT


def on_front(x, z, F, r, lift=0.0003):
    """a point for a cord of radius r lying on the front's outermost face"""
    return Vector((x, -(outer_y(x, F, z) + r + lift), z))


def build_flap(name, F, mat, mat_in=None):
    lo, hi = flap_range(F)
    nx, nz = 14, 14
    us = [k / nx for k in range(nx + 1)]
    # denser toward the visible edge
    xs = [F["e"] + (F["g"] - F["e"]) * (u ** 1.3) for u in us]
    xs = sorted(xs)
    G = []
    for x in xs:
        zt = F["top"](x)
        G.append([Vector((x, -(SH_OUT + F["gap"] + flap_t(x, F) / 2), lerp(-0.72, zt, j / nz))) for j in range(nz + 1)])
    ob = A.surface(name, G, lambda u, v: flap_t(xs[min(nx, int(round(u * nx)))], F), mat)   # columns +x, rows +z: normal -y
    if mat_in is not None:
        ob.data.materials.append(mat_in)
        nq = nx * nz
        for k, p in enumerate(ob.data.polygons):
            if k < 2 * nq and k % 2 == 1:
                p.material_index = 1
    return G


def flap_edge_pipe(name, F, r, mat, hem=True):
    """piping down the flap's visible edge (lying on its face) and along its hem"""
    e = F["e"]
    sgn = 1 if F["g"] > F["e"] else -1     # from the edge into the flap
    xe = e + sgn * 0.003
    ze = F["top"](xe)
    pts = [Vector((xe, -(outer_y(xe, F) + 0.0035), z)) for z in [lerp(ze - 0.03, -0.72, k / 12) for k in range(13)]]
    if hem:
        g_end = F["g"] - sgn * 0.03
        for k in range(1, 13):
            x = lerp(xe, g_end, k / 12)
            pts.append(Vector((x, -(outer_y(x, F) + 0.0035), -0.72)))
    wire(name, [tuple(p) for p in pts], r, mat, sides=4)


# ---------------------------------------------------------------- the shell
def build_shell_d(name, P, X, collar):
    """both halves of the closed shell, the side bands, the overlap flap, piping and seams; collar(name, G, rows, side)
    builds the collar on each half"""
    F = P.get("flap")
    out = T_SHELL / 2 + 0.004
    pr = P["pipe_r"]
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G, rows = shell_grid_d(side, P)
        cloth(f"{name}Body{sd}", G, T_SHELL, X["wool"], out_hint_torso, mat_in=X["lining"])
        cloth(f"{name}Band{sd}", band_grid(side), T_BAND, X["wool"], out_hint_torso, mat_in=X["lining"])
        if P.get("hem_pipe", True):
            # the front hem from clear of the flap to the cutaway corner, then up the cutaway into the side seam
            x0 = 0.003
            if F is not None:
                lo, hi = flap_range(F)
                if side > 0 and hi > 0:
                    x0 = hi + (0.010 if F["e"] == hi else 0.012)
                if side < 0 and lo < 0:
                    x0 = -lo + (0.010 if F["e"] == lo else 0.012)
            xc = cut_line(-0.72)
            nf = len(P["front_z"])
            edge = [Vector((side * lerp(x0, xc, k / 10), -(0.5 + D_F), -0.72)) for k in range(11)] + \
                   [G[-1][j] for j in range(1, nf) if P["front_z"][j] <= -0.075]
            wire(f"{name}PipeFront{sd}", [tuple(p + Vector((0, -out, 0))) for p in edge], pr, X["pipe"], sides=5)
            jh = len(rows) - 1
            wire(f"{name}PipeBack{sd}", [tuple(G[i][jh] + Vector((0, out + 0.002, 0))) for i in range(len(G))], pr,
                 X["pipe"], sides=5)
        if P.get("seam_shoulder", True):
            top = [r for r in rows if r[2] == "top"]
            ys = top[min(range(len(top)), key=lambda k: abs(top[k][0]))]
            wire(f"{name}SeamShoulder{sd}", [(side * lerp(ys[3], 1.0, t), ys[0], ys[1] + out + 0.001) for t in (0.30, 0.6, 0.97)],
                 0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSide{sd}", [(side * (1.0 + 0.002), -(0.5 + D_F + out - 0.004), z) for z in (-0.06, 0.4, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSideB{sd}", [(side * (1.0 + 0.002), 0.5 + D_F + out - 0.004, z) for z in (HEM_BACK + 0.02, 0.2, 0.97)],
             0.0035, X["thread"], sides=4)
        collar(f"{name}Collar{sd}", G, rows, side)
    zn = P.get("nape_z", 0.78)
    if P.get("back_seam", True):
        wire(f"{name}SeamBack", [(0, SH_OUT + 0.001, z) for z in (HEM_BACK + 0.02, -0.2, 0.4, zn - 0.08)], 0.004,
             X["thread"], sides=4)
    if F is not None:
        build_flap(f"{name}Flap", F, X["flap"], X.get("flap_in"))
    if P.get("inner"):
        build_inner(name, P, X)


# ---------------------------------------------------------------- the inner layer (no bare torso shows)
# Owner: "Make the jackets cover the torso". Under the shell (whose inner face is 0.016 off the torso) a thin layer
# covers every part of the torso the shell leaves open: the front opening or scoop, the shoulder tops inside the wide
# neckline, the scooped back (a "dickey", from the head round to 0.05 under the shell's edges) and the katana cutaways at
# the lower front corners (the hip panels). Mid-surface D_IN off the torso, T_IN thick (faces 0.004 and 0.010; lower
# grazes the muscular body's chest and gains no hair: the hairs that cross it rest on the torso's own surface), and a
# tie can lie on it and still tuck under the shell.
D_IN = 0.007
T_IN = 0.006


def head_r(z):
    """the head's radius at height z (the checker's head: a cylinder r 0.6 from z 0.9, its bottom edge bevelled 0.25)"""
    if z < 0.9:
        return 0.0
    if z > 1.15:
        return 0.6
    return 0.35 + math.sqrt(max(0.0, 0.0625 - (1.15 - z) ** 2))


def x_head(y, z, m=0.016):
    """the least x at (y, z) that keeps m off the head"""
    R = head_r(z + T_IN / 2 + 0.002)
    return math.sqrt(max(0.0, (R + m) ** 2 - y * y)) if R > 0 else 0.0


def inner_rows(P):
    """the dickey's rows (one side): (y, z, region, x_in, x_out): x_in clears the head, x_out reaches 0.05 under the
    shell past its opening (the opening's widest point within a few hundredths up or down, so no sliver shows)"""
    d = D_IN
    rn = math.hypot(P["xo_top"], 0.5 + D_F)
    rows = []

    def front_open(z):
        return max(P["edge"](z + dz) if z + dz <= 1.0 else P["xo_top"] for dz in (-0.02, 0.0, 0.015, 0.03, 0.045))

    def back_open(z):
        return max(C1.back_neck(min(1.0, z + dz), P) for dz in (-0.02, 0.0, 0.015, 0.03, 0.045))
    for z in P["inner"]["front_z"]:
        rows.append((-(0.5 + d), z, "front", front_open(z) + 0.05))
    for a in ARC:
        y = -0.5 - d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)) + 0.05))
    for y in TOP_Y:
        rows.append((y, 1.0 + d, "top", math.sqrt(max(0.0, rn * rn - y * y)) + 0.05))
    for a in ARC[::-1]:
        y = 0.5 + d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)) + 0.05))
    for z in (1.0, 0.98, 0.95, 0.91, 0.87, 0.83, 0.79, 0.75, 0.71):
        rows.append((0.5 + d, z, "back", back_open(z) + 0.05))
    out = []
    for (y, z, reg, xo) in rows:
        xi = x_head(y, z)
        xo = min(0.985, max(xo, xi + 0.06))
        out.append((y, z, reg, xi, xo))
    return out


def build_inner(name, P, X):
    I = P["inner"]
    rows = inner_rows(P)
    nf = len(I["front_z"])
    ncol = 4
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G = [[Vector((side * lerp(xi, xo, (i / ncol) ** 1.15), y, z)) for (y, z, reg, xi, xo) in rows] for i in range(ncol + 1)]
        if I.get("front_mat") is not None and I["front_mat"] is not I["mat"]:   # the front in its own cloth (a shirt)
            cloth(f"{name}InnerFront{sd}", [c[:nf] for c in G], T_IN, I["front_mat"], out_hint_torso)
            cloth(f"{name}Inner{sd}", [c[nf - 1:] for c in G], T_IN, I["mat"], out_hint_torso)
        else:
            cloth(f"{name}Inner{sd}", G, T_IN, I["mat"], out_hint_torso)
        if I.get("edge_r"):   # the neck edge, bound
            wire(f"{name}InnerEdge{sd}", [tuple(c) for c in G[0]], I["edge_r"], I["edge_mat"], sides=5)
        # (the hip corners are their own pieces: C1.add_hips in each coat's builder)


def build_hip(name, side, mat):
    """the lower front corner under the katana cutaway (x > cut_line, z < -0.08): a panel from 0.04 under the shell's
    cut edge to the corner; below z -0.22 it wraps the torso's vertical corner onto the side (the side band starts at
    y -0.45 there), above that the side band's own corner covers it.
    The left side (the sheathed katana's guard) is covered above the guard only (z > -0.20): on the deepest body
    (heavy) the torso itself is within 0.005 of the guard there, so no cloth fits between them on every body type; the
    guard hides that corner"""
    y0 = -(0.5 + D_IN)
    lo = [-0.72, -0.66, -0.56, -0.44, -0.32, -0.22]
    hi = [-0.218, -0.18, -0.14, -0.11, -0.08, -0.05]
    if side > 0:
        hi = [-0.195, -0.17, -0.14, -0.11, -0.08, -0.05]
        Gu = [[Vector((side * lerp(max(0.70, cut_line(z) - 0.04), 0.98, k / 3), y0, z)) for z in hi] for k in range(4)]
        cloth(name + "Up", Gu, T_IN, mat, out_hint_torso)
        return
    nx = 3
    Gl = []
    cols = []
    for k in range(nx + 1):
        cols.append(("f", k / nx))
    for a in (45, 90):
        cols.append(("c", a))
    cols.append(("s", -0.485))
    for kind, v in cols:
        col = []
        for z in lo:
            xi = max(0.70, cut_line(z) - 0.04)
            if kind == "f":
                col.append(Vector((side * lerp(xi, 1.0, v), y0, z)))
            elif kind == "c":
                t = math.radians(v)
                col.append(Vector((side * (1.0 + D_IN * math.sin(t)), -0.5 - D_IN * math.cos(t), z)))
            else:
                col.append(Vector((side * (1.0 + D_IN), v, z)))
        Gl.append(col)
    cloth(name, Gl, T_IN, mat, out_hint_torso)
    Gu = [[Vector((side * lerp(max(0.70, cut_line(z) - 0.04), 0.98, k / 3), y0, z)) for z in hi] for k in range(4)]
    cloth(name + "Up", Gu, T_IN, mat, out_hint_torso)


def shirt_and_tie(key, P, X):
    """the Chesterfield's shirt front shows in the V: a turn-down collar's points either side of the knot, the tie
    down the shirt, tucked under the closed front below the break"""
    yS = 0.5 + D_IN + T_IN / 2        # the shirt's outer face
    for s in (1, -1):   # collar points, lying on the shirt
        t = 0.004
        G = []
        for k in range(5):
            u = k / 4
            # from the neck edge (top) down to the point
            zt = lerp(0.948, 0.992, u)
            xt = max(x_head(-(yS + 0.004), zt, 0.022), 0.028 + 0.20 * u)
            pt = Vector((lerp(0.035, 0.235, u), 0, lerp(0.905, 0.94, u)))
            tip = Vector((0.105, 0, 0.835))
            bot = pt.lerp(tip, 0.6 * (1 - abs(u - 0.4) / 0.6))
            G.append([Vector((s * lerp(xt, bot.x, v), -(yS + 0.001 + t / 2), lerp(zt, bot.z, v))) for v in (0.0, 0.5, 1.0)])
        if s < 0:
            G = G[::-1]
        cloth(f"{key}ShirtCollar{s}", G, t, X["shirt"], lambda p: Vector((0, -1, 0)))
    # the knot
    A.extrude_poly(f"{key}TieKnot", ccw([(-0.036, 0.947), (0.036, 0.947), (0.024, 0.898), (-0.024, 0.898)]), 0.016,
                   X["tie"], Matrix.Translation((0, -(yS + 0.0006), 0)), bevel=0.004, segments=2)
    # the blade: widening down to z 0.0, its point at -0.10 under the fly front
    zs = [0.90, 0.80, 0.65, 0.50, 0.35, 0.20, 0.07, -0.02, -0.07, -0.10]
    G = []
    for k in range(5):
        u = k / 4 - 0.5
        col = []
        for z in zs:
            w = lerp(0.062, 0.110, smooth(0.90, 0.0, z))
            if z < -0.02:
                w *= max(0.04, (z + 0.10) / 0.08)
            zz = z - (0.03 * (1 - abs(u) * 2) if z == -0.10 else 0.0)
            col.append(Vector((u * w, -(yS + 0.0005 + 0.002), zz)))
        G.append(col)
    cloth(f"{key}Tie", G, 0.004, X["tie"], lambda p: Vector((0, -1, 0)))


# ================================================================== helpers
def button(name, at, nrm, X, kind="silver", r=0.030):
    """a light domed coat button with a raised rim (X["silver"]: brass, horn...), its face along nrm"""
    F = axis_frame(at, nrm)
    place(A.lathe(name, [(0.0, 0.019), (r * 0.42, 0.0182), (r * 0.66, 0.0150), (r * 0.76, 0.0172), (r * 0.92, 0.0105),
                         (r * 1.0, 0.004), (r * 0.97, 0.0), (0.0, 0.0)], (0, 0, 0), X["silver"], seg=8), F)


def wire_r(name, pts, radii, mat, sides=8):
    """a tube along a poly line with a radius per point (rotation-minimising frame, capped)"""
    import bmesh
    P = [Vector(p) for p in pts]
    n = len(P)
    T = []
    for k in range(n):
        t = P[min(k + 1, n - 1)] - P[max(k - 1, 0)]
        T.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    u = T[0].orthogonal().normalized()
    verts, faces = [], []
    for k in range(n):
        if k:
            u = u - T[k] * u.dot(T[k])
            u = u.normalized() if u.length > 1e-9 else T[k].orthogonal().normalized()
        v = T[k].cross(u)
        for i in range(sides):
            a = 2 * math.pi * i / sides
            verts.append(P[k] + (u * math.cos(a) + v * math.sin(a)) * radii[k])
    for k in range(n - 1):
        for i in range(sides):
            i2 = (i + 1) % sides
            faces.append([k * sides + i, k * sides + i2, (k + 1) * sides + i2, (k + 1) * sides + i])
    faces.append(list(range(sides))[::-1])
    faces.append([(n - 1) * sides + i for i in range(sides)])
    ob = A.mesh_from(name, verts, faces, mat)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    return ob


def edge_frames(G, rows, js):
    """per neckline point j: the edge point E (mid-surface), the face normal n, the horizontal outward normal nh, the
    top weight w (1 on the shoulder top) and the in-surface direction a away from the opening (perpendicular to the
    neckline)"""
    out = []
    E = [G[0][j] for j in js]
    for k, j in enumerate(js):
        y, z, reg = rows[j][0], rows[j][1], rows[j][2]
        p = E[k]
        if reg == "front":
            n = Vector((0, -1, 0)); nh = n.copy(); w = 0.0
        elif reg == "back":
            n = Vector((0, 1, 0)); nh = n.copy(); w = 0.0
        else:
            if abs(y) > 0.5 + 1e-6:
                c = Vector((p.x, math.copysign(0.5, y), 1.0))
                n = p - c; n.x = 0.0; n.normalize()
            else:
                n = Z.copy()
            w = n.z
            face = Vector((0, math.copysign(1, y), 0))
            rad = Vector((p.x, p.y, 0)).normalized()
            nh = (face * (1 - w) + rad * w).normalized()
        a_prev = E[max(k - 1, 0)]
        a_next = E[min(k + 1, len(E) - 1)]
        if k == len(E) - 1 and reg == "back" and abs(p.x) < 0.01:   # the centre back: the neckline is level there
            tng = Vector((1, 0, 0))
        else:
            tng = (a_next - a_prev)
        a = n.cross(tng)
        a = a - n * a.dot(n)
        if a.length < 1e-9:
            a = (G[1][j] - G[0][j])
        a.normalize()
        if a.dot(G[1][j] - G[0][j]) < 0:
            a = -a
        out.append((p, n, nh, w, a, reg, y, z))
    return out


def neck_js(rows, z_front, nape):
    js = [j for j, r in enumerate(rows) if r[2] == "front" and r[1] >= z_front - 1e-6]
    js += [j for j, r in enumerate(rows) if r[2] == "top"]
    js += [j for j, r in enumerate(rows) if r[2] == "back" and r[1] >= nape - 0.005]
    return js


def self_overlaps(key):
    """--selfcheck: the triangle overlaps between this item's own parts (the checker skips pieces of one item)"""
    if "--selfcheck" not in A.argv:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    data = []
    for ob in A.PARTS:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        vs = [ob.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles()
        tris = [tuple(t.vertices) for t in me.loop_triangles]
        ev.to_mesh_clear()
        if not tris:
            continue
        lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        data.append((ob.name, ob.get("nh_piece"), BVHTree.FromPolygons(vs, tris, epsilon=0.0), lo, hi, vs, tris))
    n = 0
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            a, b = data[i], data[j]
            if any(a[3][k] > b[4][k] or b[3][k] > a[4][k] for k in range(3)):
                continue
            ov = a[2].overlap(b[2])
            if ov:
                n += 1
                cs = [sum((a[5][q] for q in a[6][i0]), Vector()) / 3 for i0, _ in ov]
                lo_ = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
                hi_ = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
                print(f"[self] {key}: {a[0]} ({a[1]}) x {b[0]} ({b[1]}): {len(ov)}  "
                      f"x {lo_.x:.3f}..{hi_.x:.3f} y {lo_.y:.3f}..{hi_.y:.3f} z {lo_.z:.3f}..{hi_.z:.3f}")
    print(f"[self] {key}: {n} overlapping part pairs")


# ================================================================== sleeves
SLV_CUFF, SLV_XIN = C1.SLV_CUFF, C1.SLV_XIN
slv_xin = getattr(C1, "slv_xin", lambda z: SLV_XIN)   # the inner edge, stepping out below the elbow (the scabbard)


def sleeve_grid_z(zs, d=0.020):
    """the Kit C sleeve grid (nh_acc_batchc1.sleeve_grid_k: the whole arm, the front and back faces to the inner
    edge) from the given cuff-to-shoulder rows"""
    rowsP = []
    for z in zs:
        ease = 0.003 * math.sin(math.pi * smooth(-0.8, 0.9, z))
        rowsP.append([Vector((1.5 + X, Y, z)) for X, Y in arm_wrap(d + ease, x_in=slv_xin(z), **wrap_kw())])
    E0 = arm_wrap(0.0, x_in=SLV_XIN, **wrap_kw())
    Ed = arm_wrap(d, x_in=SLV_XIN, **wrap_kw())
    for a in (35, 70):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rowsP.append([Vector((1.5 + e[0] + (f[0] - e[0]) * c, e[1] + (f[1] - e[1]) * c, 1.0 + d * s_)) for e, f in zip(E0, Ed)])
    n = len(E0)
    T = [(SLV_XIN + 0.01, lerp(-0.40, 0.40, k / (n - 1))) for k in range(n)]
    for f in (0.0, 0.3, 0.6, 1.0):
        rowsP.append([Vector((1.5 + lerp(E0[k][0], T[k][0], f), lerp(E0[k][1], T[k][1], f), 1.0 + d)) for k in range(n)])
    return [[rowsP[j][k] for j in range(len(rowsP))] for k in range(n)]


def build_sleeve_d(name, P, X):
    """the left sleeve, the whole arm to the wrist (SLV_CUFF), with this module's cuffs: "pointed" (a crimson pointed
    cuff over the sleeve, piped, two buttons), "plain" (a bound hem, a stitched line, three small buttons), "rib" (the
    knit sleeve stops 0.167 above the wrist and a thick rib-knit cuff continues it)"""
    cuff = P["cuff"]
    SZ = C1.SLEEVE_Z_K
    c0 = SLV_CUFF
    if cuff == "rib":
        zs = [c0 + 0.169] + [z for z in SZ if z > c0 + 0.21]
    else:
        zs = list(SZ)
    G = sleeve_grid_z(zs)
    cloth(name + "Body", G, 0.014, X["wool"], sleeve_hint, mat_in=X["lining"])
    seam_lo = c0 + 0.02 if cuff != "rib" else c0 + 0.19
    wire(name + "Seam", [tuple(Vector((1.5 + 0.10, 0.5 + 0.020 + 0.0085, z))) for z in (seam_lo, -0.2, 0.3, 0.8, 0.97)],
         0.0032, X["thread"], sides=4)
    if cuff == "plain":
        wire(name + "Hem", [tuple(c[0] + (c[0] - Vector((1.5, 0, c[0].z))).normalized() * 0.006) for c in G], 0.0070,
             X["wool"], sides=5)
        zt = c0 + 0.095   # the cuff's stitched line round the sleeve
        ring = arm_wrap(0.020 + 0.007 + 0.0012, x_in=slv_xin(zt) + 0.004, **wrap_kw())
        wire(name + "CuffStitch", [(1.5 + Xp, Yp, zt) for Xp, Yp in ring], 0.0024, X["thread"], sides=4)
        for k, z in enumerate((c0 + 0.065, c0 + 0.11, c0 + 0.155)):   # three small buttons up the back-outer edge
            button(f"{name}CuffBtn{k}", Vector((2.0 + 0.020 + 0.007, 0.33, z)), (1, 0, 0), X, "silver", r=0.019)
    elif cuff == "pointed":
        # the crimson cuff over the sleeve, its top rising to a point on the outer face
        prof = arm_wrap(0.040, x_in=slv_xin(c0) + 0.005, **wrap_kw())
        nv = 5
        Gc = []
        for k, (Xp, Yp) in enumerate(prof):
            pk = max(0.0, 1.0 - abs(Yp) / 0.34) if Xp > 0.44 else 0.0
            ztop = c0 + 0.165 + 0.10 * pk ** 1.2
            col = []
            for j in range(nv + 1):
                v = j / nv
                z = lerp(c0, ztop, v)
                dd = 0.040 + 0.004 * v
                p = arm_wrap(dd, x_in=slv_xin(z) + 0.005, **wrap_kw())[k]
                col.append(Vector((1.5 + p[0], p[1], z)))
            Gc.append(col)
        cloth(name + "Cuff", Gc, 0.014, X["cuff"], sleeve_hint)
        top = [c[-1] + (c[-1] - Vector((1.5, 0, c[-1].z))).normalized() * 0.0065 + Vector((0, 0, 0.003)) for c in Gc]
        wire(name + "CuffPipe", [tuple(p) for p in top], P["pipe_r"] * 0.9, X["cuff_pipe"], sides=4)
        bot = [c[0] + (c[0] - Vector((1.5, 0, c[0].z))).normalized() * 0.0065 for c in Gc]
        wire(name + "CuffHem", [tuple(p) for p in bot], P["pipe_r"] * 0.9, X["cuff_pipe"], sides=4)
        for k, z in enumerate((c0 + 0.135, c0 + 0.06)):
            button(f"{name}CuffBtn{k}", Vector((2.0 + 0.044 + 0.007, 0.25, z)), (1, 0, 0), X, "silver", r=0.024)
    elif cuff == "rib":
        zc = [c0 + 0.166, c0 + 0.13, c0 + 0.09, c0 + 0.05, c0 + 0.02, c0]
        Gc = []
        nprof = len(arm_wrap(0.02, x_in=SLV_XIN, **wrap_kw()))
        for k in range(nprof):
            col = []
            for z in zc:
                g = smooth(c0 + 0.13, c0, z)     # gathered a little toward the wrist
                ease = 0.003 * math.sin(math.pi * smooth(-0.8, 0.9, z))
                p = arm_wrap(0.020 + ease + 0.002 - 0.004 * g, x_in=slv_xin(z), **wrap_kw())[k]
                col.append(Vector((1.5 + p[0], p[1], z)))
            Gc.append(col)
        cloth(name + "Cuff", Gc, 0.022, X["rib"], sleeve_hint)
        wire(name + "CuffRoll", [tuple(c[-1] + (c[-1] - Vector((1.5, 0, c[-1].z))).normalized() * 0.002) for c in Gc],
             0.008, X["rib"], sides=6)


def sleeves(key, P, X):
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve_d(f"{key}SleeveL", P, X)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")


# ================================================================== 1. the Academy cadet coat
def cadet_mats(M):
    X = dict(
        wool=A.mat_cloth("CadetWool", (0.020, 0.019, 0.024), weave=320, rough=0.84, sheen=0.45, bump=0.11, vary=0.06,
                         wear=0.15, dirt=0.4),
        lining=M["crimson_silk"],
        crimson=A.mat_cloth("CadetCrimson", (0.24, 0.022, 0.042), weave=320, rough=0.80, sheen=0.5, bump=0.10, vary=0.06,
                            wear=0.12, dirt=0.35),
        braid=A.mat_cloth("CrimsonBraid", (0.30, 0.028, 0.052), weave=700, rough=0.55, sheen=0.55, bump=0.25,
                          twill=True, vary=0.05, wear=0.1),
        thread=A.mat_cloth("CadetThread", (0.03, 0.028, 0.03), weave=900, rough=0.6, sheen=0.2, bump=0.05, twill=False),
        brass=M["brass"], silver=M["brass"], bone=M["bone"], btn="silver")
    X.update(collar=X["wool"], pipe=X["braid"], collar_pipe=X["braid"], cuff=X["crimson"], cuff_pipe=M["brass"],
             flap=X["wool"], flap_in=X["lining"])
    return X


def cadet_params():
    zn = 0.70                  # the front neckline's lowest point: a wide, squared scoop (flat across the chest, rising
    pw = 5.0                   # steeply to the shoulders), so long hair falling over the chest clears it
    P = dict(xo_top=0.70, neck_z=zn, nape_z=0.78, pipe_r=0.0055, back_folds=0.006, cuff="pointed",
             skirt_bot=-1.45, skirt_flare=0.06, skirt_vent=0.03, seam_shoulder=True, hem_pipe=True)
    XS = [0.30, 0.45, 0.55, 0.62, 0.665, 0.69]
    P["ncol"] = 8
    P["front_z"] = [-0.72, -0.70, -0.66, -0.62, -0.48, -0.34, -0.26, -0.20, -0.14, -0.105, -0.08, 0.05, 0.25, 0.45,
                    0.60, zn] + [zn + (1 - zn) * (x / 0.70) ** pw for x in XS] + [1.0]

    def edge(z):
        if z <= zn + 1e-6:
            return 0.003
        t = (z - zn) / (1 - zn)
        return max(0.003, P["xo_top"] * t ** (1 / pw))
    P["edge"] = edge

    def neck_at(x):   # the neckline's height at |x| (inverse of edge)
        q = min(1.0, abs(x) / P["xo_top"])
        return zn + (1 - zn) * q ** pw
    P["neck_at"] = neck_at
    P["flap"] = dict(e=-0.46, f=-0.10, g=0.18, t=0.012, gap=0.001, top=lambda x: neck_at(x) - 0.004)
    P["skirt_open"] = lambda z: 0.03 + 0.05 * smooth(-0.8, P["skirt_bot"], z)
    return P


def stand_collar(name, G, rows, side, P, X):
    """a low stand collar: a band standing up off the neckline (+z) from the centre front to the centre back. On the
    chest it stands in the plane of the panel (0.048 at the centre, over the overlap flap); along the shoulder tops it
    rises 0.028; down the scooped back it narrows to a 0.010 binding (the hair lies there)"""
    F = P["flap"]
    tc = 0.014
    fr = edge_frames(G, rows, neck_js(rows, P["neck_z"], P["nape_z"]))
    e, g = F["e"], F["g"]
    full = F["gap"] + F["t"]
    cols = []
    for (p, n, nh, w, a, reg, y, z) in fr:
        if reg == "front":
            x = p.x
            lo, hi = flap_range(F)
            if lo <= x <= hi:
                lf = F["gap"] + flap_t(x, F)
            elif x < lo:
                lf = full * smooth(lo - 0.12, lo, x)
            else:
                lf = (F["gap"] + 0.002) * smooth(hi + 0.06, hi, x)
            h = lerp(0.040, 0.028, smooth(P["neck_z"], 1.0, z))
        elif reg == "back":   # down the scooped back it is only a narrow binding
            lf = 0.0
            h = lerp(0.028, 0.010, smooth(0.99, 0.94, z))
        else:
            lf = 0.0
            h = 0.028
        B = p + n * (T_SHELL / 2 + 0.001 + (0.0015 + lf) * (1 - w) + 0.007 * w) + nh * (tc / 2)
        ext = 0.02 * (1 - w) + 0.006 * w
        lean = 0.008 * w + 0.004
        cols.append([B + a * ext, B + Z * (h * 0.2), B + Z * (h * 0.6) + nh * lean * 0.35, B + Z * h + nh * lean])

    def hint(q):
        return Vector((q.x, q.y, 0))
    cloth(name, cols, tc, X["collar"], hint, mat_in=X["wool"])
    wire(name + "Edge", [tuple(c[-1] + Z * 0.0035 + (c[-1] - c[-2]).normalized() * 0.0) for c in cols], P["pipe_r"],
         X["collar_pipe"], sides=4)
    # the front end bound in crimson too
    c0 = cols[0]
    wire(name + "End", [tuple(c0[k] + Vector((side * 0.0, 0, 0)) + Vector((side * 0.0045, 0, 0))) for k in range(4)],
         P["pipe_r"] * 0.9, X["collar_pipe"], sides=4)


def frog(name, z0, F, X, bx=0.30, cr=0.0062):
    """a Brandenburg frog across the chest: a braid bar between the button rows, a ring round each button, a teardrop
    loop beyond it and a small crown loop over the bar's middle; couched on the front (over the flap's taper)"""
    def P_(path):
        return [tuple(on_front(x, z, F, cr, lift=0.0015)) for x, z in path]
    R = 0.052
    for s in (-1, 1):
        ring = [(s * bx + R * math.cos(2 * math.pi * k / 10), z0 + R * math.sin(2 * math.pi * k / 10)) for k in range(10)]
        wire(f"{name}Ring{s}", P_(ring), cr, X["braid"], sides=4, closed=True)
        lc = s * (bx + R + 0.034)
        loop = [(lc + 0.034 * math.cos(2 * math.pi * k / 9), z0 + 0.022 * math.sin(2 * math.pi * k / 9)) for k in range(9)]
        wire(f"{name}Loop{s}", P_(loop), cr, X["braid"], sides=4, closed=True)
    bar = [(lerp(-bx + R, bx - R, k / 6), z0) for k in range(7)]
    wire(f"{name}Bar", P_(bar), cr, X["braid"], sides=4)
    crown = [(0.020 * math.cos(2 * math.pi * k / 7 - math.pi / 2), z0 + 0.028 + 0.023 * math.sin(2 * math.pi * k / 7 - math.pi / 2))
             for k in range(7)]
    wire(f"{name}Crown", P_(crown), cr * 0.9, X["braid"], sides=4, closed=True)


@item("CadetCoat", "Academy cadet coat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.2, 0, 0.30), 85))
def build_cadet(M):
    key = "CadetCoat"
    X, P = cadet_mats(M), cadet_params()
    F = P["flap"]
    piece(f"{key}Shell", "Torso")
    P["inner"] = dict(front_z=[0.64, 0.68, 0.70, 0.72, 0.76, 0.82, 0.88, 0.92, 0.95, 0.98, 1.0], mat=X["wool"],
                      edge_r=0.0042, edge_mat=X["braid"])
    build_shell_d(key, P, X, lambda nm, G, rows, side: stand_collar(nm, G, rows, side, P, X))
    flap_edge_pipe(f"{key}FlapPipe", F, P["pipe_r"], X["pipe"])
    # double-breasted: two rows of brass buttons, frogged across
    levels = (0.56, 0.37, 0.18, -0.01, -0.20, -0.39)
    for k, z in enumerate(levels):
        frog(f"{key}Frog{k}", z, F, X)
        for s in (-1, 1):
            x = s * 0.30
            button(f"{key}Btn{k}{'L' if s > 0 else 'R'}", Vector((x, -outer_y(x, F, z), z)), (0, -1, 0), X, "silver", r=0.034)
    for s in (-1, 1):
        x = s * 0.30
        button(f"{key}BtnLow{'L' if s > 0 else 'R'}", Vector((x, -outer_y(x, F, -0.57), -0.57)), (0, -1, 0), X, "silver", r=0.034)
    # the half-belt on the back, piped, two brass buttons
    half_belt(f"{key}HalfBelt", -0.42, X, X["wool"], P, w=0.07, x1=0.58)
    for s in (-1, 1):
        button(f"{key}BeltBtn{s}", back_point(s * 0.52, -0.42, 0.0125), (0, 1, 0), X, "silver", r=0.026)
    piece(f"{key}Skirt", "Torso", rig=C1.skirt_rig)
    C1.build_skirt(f"{key}Skirt", P, X)
    sleeves(key, P, X)
    self_overlaps(key)
    hips_extra = C1.add_hips(key, P, X, P["inner"].get("hip_mat", P["inner"]["mat"]))
    C1.write_extra(key, dict(hips_extra, **{f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}))
    return dict(notes="the Academy cadet coat: black wool, double-breasted with brass buttons and crimson frogging, "
                      "crimson piping, a low stand collar, pointed crimson cuffs; mid-thigh skirts that move with the legs")


# ================================================================== 2. the Chesterfield overcoat
def chester_mats(M):
    X = dict(
        wool=A.mat_cloth("ChesterWool", (0.014, 0.0135, 0.016), weave=360, rough=0.84, sheen=0.5, bump=0.09, vary=0.05,
                         wear=0.10, dirt=0.35),
        lining=A.mat_cloth("ChesterLining", (0.022, 0.018, 0.022), weave=520, rough=0.36, sheen=0.35, bump=0.04, twill=False),
        thread=A.mat_cloth("ChesterThread", (0.032, 0.030, 0.034), weave=900, rough=0.6, sheen=0.2, bump=0.05, twill=False),
        silver=A.mat_flat("BlackHorn", (0.020, 0.017, 0.015), rough=0.28, noise=30, bump=0.02, vary=0.25, wear=0.1, coat=0.3),
        velvet=M["black_velvet"], brass=M["brass"], bone=M["bone"], btn="silver", shirt=M["white_linen"],
        tie=A.mat_cloth("ChesterTie", (0.16, 0.014, 0.030), weave=700, rough=0.38, sheen=0.3, bump=0.05, twill=True,
                        stripe=((0.05, 0.006, 0.012), 0.05, 0.012, 45)))
    X.update(collar=X["velvet"], collar_pipe=X["velvet"], lapel=X["wool"], lapel_pipe=X["wool"], pipe=X["wool"],
             flap=X["wool"], flap_in=X["lining"], cuff=X["wool"])
    return X


def chester_params():
    zb = 0.05                  # a long roll: the lapels roll to the waist, so hair falling over the chest clears it
    P = dict(xo_top=0.72, xo_break=0.10, lapel="notch", lapel_w=0.20, notch=0.07, collar_rise=0.035, collar_reach=0.11,
             collar_back=0.03, nape_z=0.78, pipe_r=0.0042, back_folds=0.004, brk=zb, cuff="plain",
             skirt_bot=-2.10, skirt_flare=0.09, skirt_vent=0.03, seam_shoulder=True, hem_pipe=True)
    P["break"] = zb
    P["front_z"] = list(K7.FRONT_Z)          # has the break (0.05)
    P["edge"] = lambda z: 0.003 if z < zb - 1e-6 else K7.lapel_line(z, P)
    P["flap"] = dict(e=-0.10, f=0.0, g=0.10, t=0.010, gap=0.001, top=lambda x: zb - 0.015)
    P["skirt_open"] = lambda z: 0.04 + 0.10 * smooth(-0.8, P["skirt_bot"], z)
    return P


def welt(name, x0, x1, zc, slope, X, mat, h=0.042, t=0.008):
    """a welt pocket: a narrow strip on the front, slanted (its outer end higher), bar-tacked at both ends"""
    G = []
    for k in range(5):
        x = lerp(x0, x1, k / 4)
        z = zc + slope * (x - (x0 + x1) / 2)
        G.append([Vector((x, -(SH_OUT + 0.001 + t / 2), z + dz)) for dz in (-h / 2, 0.0, h / 2)])
    A.surface(name, G, t, mat)
    for nm, x in (("A", x0 + 0.004), ("B", x1 - 0.004)):
        z = zc + slope * (x - (x0 + x1) / 2)
        wire(name + "Tack" + nm, [(x, -(SH_OUT + 0.001 + t + 0.0015), z + dz) for dz in (-h / 2 + 0.004, h / 2 - 0.004)],
             0.0024, X["thread"], sides=4)


@item("ChesterfieldCoat", "Chesterfield overcoat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.2, 0, 0.30), 85))
def build_chesterfield(M):
    key = "ChesterfieldCoat"
    X, P = chester_mats(M), chester_params()
    F = P["flap"]

    def collar(nm, G, rows, side):
        C1.build_collar_k(nm, G, rows, side, P, X)
        build_lapel(nm.replace("Collar", "Lapel"), side, P, X)
    P["inner"] = dict(front_z=[-0.04, 0.05, 0.15, 0.30, 0.45, 0.60, 0.75, 0.86, 0.90, 0.93, 0.96, 0.98, 1.0], mat=X["wool"], front_mat=X["shirt"])
    piece(f"{key}Shell", "Torso")
    build_shell_d(key, P, X, collar)
    shirt_and_tie(key, P, X)
    flap_edge_pipe(f"{key}FlapPipe", F, P["pipe_r"], X["pipe"])
    # the fly's top-stitching: down the placket, curving out to the edge below the last hidden button
    xs_ = -0.03
    path = [(xs_, z) for z in (0.01, -0.15, -0.30, -0.46)]
    for k in range(1, 7):
        a = math.radians(90 * k / 6)
        path.append((xs_ - 0.05 * (1 - math.cos(a)), -0.46 - 0.07 * math.sin(a)))
    wire(f"{key}FlyStitch", [tuple(on_front(x, z, F, 0.0022, lift=-0.0012)) for x, z in path], 0.0022, X["thread"], sides=4)
    # flapped hip pockets, a breast welt on the left, a buttonhole worked in the left lapel
    for s in (1, -1):
        pocket_flap(f"{key}Pocket{'L' if s > 0 else 'R'}", s, -0.40, X, X["wool"])
        wire(f"{key}PocketJet{s}", [(s * x, -(SH_OUT + 0.0016), -0.398) for x in (0.452, 0.57, 0.688)], 0.0026, X["thread"], sides=4)
    welt(f"{key}Welt", 0.47, 0.69, 0.30, 0.12, X, X["wool"])
    zl = 0.72
    W = P["lapel_w"] * smooth(P["break"] - 0.05, P["break"] + 0.55, zl) + 0.02
    xl = K7.lapel_line(zl, P) + W * 0.45
    yl = -(0.5 + D_F + T_SHELL / 2 + 0.0075 + 0.006 + 0.0012)
    wire(f"{key}LapelHole", [(xl - 0.022, yl, zl + 0.014), (xl, yl, zl + 0.004), (xl + 0.022, yl, zl - 0.006)], 0.0030,
         X["thread"], sides=4)
    piece(f"{key}Skirt", "Torso", rig=C1.skirt_rig)
    C1.build_skirt(f"{key}Skirt", P, X)
    sleeves(key, P, X)
    self_overlaps(key)
    hips_extra = C1.add_hips(key, P, X, P["inner"].get("hip_mat", P["inner"]["mat"]))
    C1.write_extra(key, dict(hips_extra, **{f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}))
    return dict(notes="the Chesterfield overcoat: black wool, a black velvet upper collar, notch lapels, a fly front "
                      "(hidden buttons), flapped hip pockets and a breast welt; knee-length skirts that move with the legs")


# ================================================================== 3. the cable-knit cardigan coat
def _knit_stitch(T, h, v):
    """stockinette: chevron V's, 0.034 wide, 0.026 tall (0..1)"""
    cu = T.math("FRACT", T.math("DIVIDE", h, 0.034))
    vv = T.math("ADD", T.math("DIVIDE", v, 0.026), T.math("ABSOLUTE", T.math("SUBTRACT", cu, 0.5)))
    st = T.math("FRACT", vv)
    return T.math("SUBTRACT", 1.0, T.math("MULTIPLY", T.math("ABSOLUTE", T.math("SUBTRACT", st, 0.5)), 2.0))


def mat_knit(name, rgb, kind="cable", bump=1.3):
    """hand-knit wool as a procedural height (cables, ribs or moss stitch) driving a bump and a crevice shade.
    The horizontal coordinate is x + y in object space: on every face of the R6 boxes one of the two is constant, so
    the cables run straight down the front, sides and back alike"""
    m, T, bs = A._base(name)
    tc = T.node("ShaderNodeTexCoord")
    sep = T.node("ShaderNodeSeparateXYZ"); T.L(tc.outputs["Object"], sep.inputs["Vector"])
    h = T.math("ADD", sep.outputs["X"], sep.outputs["Y"])
    v = sep.outputs["Z"]
    knit = _knit_stitch(T, h, v)
    if kind == "cable":
        period = 0.32
        U = T.math("FRACT", T.math("DIVIDE", h, period))
        # a rope cable in U 0.16..0.60: a dome across, diagonal twisted strands along
        s = T.math("DIVIDE", T.math("SUBTRACT", U, 0.16), 0.44)
        s = T.math("MINIMUM", T.math("MAXIMUM", s, 0.0), 1.0)
        dome = T.math("POWER", T.math("SINE", T.math("MULTIPLY", s, math.pi)), 0.55)
        rope = T.math("FRACT", T.math("ADD", T.math("DIVIDE", v, 0.12), T.math("MULTIPLY", s, 0.60)))
        tri = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", T.math("ABSOLUTE", T.math("SUBTRACT", rope, 0.5)), 2.0))
        tri = T.math("POWER", tri, 0.6)
        cable = T.math("MULTIPLY", dome, T.math("ADD", 0.35, T.math("MULTIPLY", tri, 0.65)))
        # twin ribs in U 0.68..0.92
        r = T.math("DIVIDE", T.math("SUBTRACT", U, 0.68), 0.12)
        inr = T.math("MULTIPLY", T.math("GREATER_THAN", U, 0.68), T.math("LESS_THAN", U, 0.92))
        ribs = T.math("MULTIPLY", inr, T.math("ADD", 0.5, T.math("MULTIPLY", T.math("COSINE", T.math("MULTIPLY", r, 2 * math.pi)), -0.5)))
        ribs = T.math("MULTIPLY", ribs, 0.55)
        height = T.math("ADD", T.math("MAXIMUM", cable, ribs), T.math("MULTIPLY", knit, 0.16))
    elif kind == "rib":
        r = T.math("FRACT", T.math("DIVIDE", h, 0.042))
        rib = T.math("POWER", T.math("ADD", 0.5, T.math("MULTIPLY", T.math("COSINE", T.math("MULTIPLY", r, 2 * math.pi)), 0.5)), 0.7)
        height = T.math("ADD", T.math("MULTIPLY", rib, 0.85), T.math("MULTIPLY", knit, 0.15))
    else:   # moss (the shawl): small round bumps
        vo = T.node("ShaderNodeTexVoronoi", feature="F1")
        vo.inputs["Scale"].default_value = 1.0
        T.L(T.coord(55.0), vo.inputs["Vector"])
        height = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", vo.outputs["Distance"], 1.6), clamp=True)
        height = T.math("ADD", T.math("MULTIPLY", height, 0.8), T.math("MULTIPLY", knit, 0.2))
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    T.L(T.coord(40.0), nz.inputs["Vector"])
    base = A._rgb(T, rgb)
    shade = T.math("ADD", 0.30, T.math("MULTIPLY", height, 0.85))
    col = T.mix(1.0, base, shade, "MULTIPLY")
    col = T.mix(0.10, col, nz.outputs["Color"], "OVERLAY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.010
    T.L(height, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 0.7
    bs.inputs["Sheen Roughness"].default_value = 0.5
    rgh = T.math("ADD", 0.90, T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.08))
    A._weather(T, bs, col, rgh, A._val(T, 0.0), bp.outputs["Normal"], 0.08, False, 0.35, 0.008)
    return m


def cardigan_mats(M):
    ink = (0.020, 0.032, 0.085)
    X = dict(
        wool=mat_knit("InkCableKnit", ink, "cable"),
        lining=mat_knit("InkKnitInside", (0.016, 0.026, 0.070), "rib", bump=0.4),
        rib=mat_knit("InkRibKnit", ink, "rib"),
        moss=mat_knit("InkMossKnit", ink, "moss"),
        jumper=mat_knit("OatmealRibKnit", (0.50, 0.44, 0.35), "rib", bump=0.7),
        thread=mat_knit("InkKnitSeam", (0.016, 0.026, 0.070), "rib", bump=0.3),
        horn=A.mat_flat("HornToggle", (0.17, 0.105, 0.055), rough=0.30, noise=14, bump=0.02, vary=0.5, wear=0.2, coat=0.35),
        leather=M["leather_brown"],
        thong=A.mat_flat("LeatherThong", (0.20, 0.11, 0.055), rough=0.55, noise=60, bump=0.05, vary=0.15, wear=0.3),
        brass=M["brass"], bone=M["bone"], silver=M["brass"], btn="silver")
    X.update(pipe=X["rib"], flap=X["rib"], flap_in=X["lining"], collar=X["moss"])
    return X


def cardigan_params():
    zb = 0.05
    P = dict(xo_top=0.72, xo_break=0.10, brk=zb, nape_z=0.78, pipe_r=0.0075, back_folds=0.0, cuff="rib",
             skirt_bot=-2.05, skirt_flare=0.10, skirt_vent=0.03, seam_shoulder=False, hem_pipe=True, back_seam=False)
    P["break"] = zb
    P["front_z"] = list(K7.FRONT_Z)          # has the break (0.05)
    P["edge"] = lambda z: 0.003 if z < zb - 1e-6 else K7.lapel_line(z, P)
    # right over left: the overlapping band's visible edge is on the wearer's left (x +0.10), the toggles beyond it
    P["flap"] = dict(e=0.10, f=0.0, g=-0.08, t=0.014, gap=0.001, top=lambda x: zb - 0.015)
    P["skirt_open"] = lambda z: 0.03 + 0.10 * smooth(-0.8, P["skirt_bot"], z)
    P["hem_band"] = 0.12
    return P


def shawl_collar(name, G, rows, side, P, X):
    """the rolled shawl collar: from the break up the front edge, along the wide neckline over the shoulders and down
    the scooped back to the centre back. One continuous roll (no notch): a thick rounded fold on the panel's edge and
    a fall lying back over the panel, wide on the chest, narrow over the shoulders (the hair lies there), flat down the
    back"""
    fr = edge_frames(G, rows, neck_js(rows, P["break"], P["nape_z"]))
    tc = 0.014
    ws, rs = [], []
    for (p, n, nh, w, a, reg, y, z) in fr:
        if reg == "front":
            W = lerp(0.04, 0.23, smooth(P["break"], P["break"] + 0.40, z)) * lerp(1.0, 0.62, smooth(0.80, 1.0, z))
            rr = lerp(0.010, 0.028, smooth(P["break"], P["break"] + 0.30, z)) * lerp(1.0, 0.60, smooth(0.85, 1.0, z))
        elif reg == "top":
            W, rr = 0.085, 0.012
        else:   # flat down the scooped back (short hair lies on the nape)
            W = lerp(0.085, 0.11, smooth(0.99, 0.88, z))
            rr = lerp(0.012, 0.0065, smooth(0.99, 0.90, z))
        ws.append(W); rs.append(rr)
    # soften the steps between regions
    for _ in range(2):
        ws = [ws[0]] + [(ws[k - 1] + 2 * ws[k] + ws[k + 1]) / 4 for k in range(1, len(ws) - 1)] + [ws[-1]]
        rs = [rs[0]] + [(rs[k - 1] + 2 * rs[k] + rs[k + 1]) / 4 for k in range(1, len(rs) - 1)] + [rs[-1]]
    us = [0.0, 0.10, 0.24, 0.42, 0.62, 0.82, 1.0]
    G2, roll = [], []
    for k, (p, n, nh, w, a, reg, y, z) in enumerate(fr):
        W, rr = ws[k], rs[k]
        col = []
        for u in us:
            f = (1 - u) ** 1.7
            hgt = (2 * rr + tc / 2 + 0.002) * f + (tc / 2 + 0.0015) * (1 - f)
            col.append(p + n * (T_SHELL / 2 + hgt) + a * (W * u))
        G2.append(col)
        roll.append(p + n * (T_SHELL / 2 + 0.0012 + rr))
    cloth(name, G2, tc, X["collar"], out_hint_torso, mat_in=X["collar"])
    wire_r(name + "Roll", [tuple(q) for q in roll], rs, X["collar"], sides=8)
    # the fall's outer edge, rolled a little
    wire(name + "Edge", [tuple(c[-1] + (c[-1] - c[-2]).normalized() * 0.002) for c in G2], 0.0075, X["collar"], sides=5)


def toggle(name, at, X, L=0.16, R=0.022):
    """a horn toggle lying across the front (its axis along x), waisted for the loop"""
    prof = [(0.0, -L / 2), (R * 0.45, -L / 2 + 0.002), (R * 0.80, -L / 2 + 0.012), (R, -L * 0.22), (R * 0.82, -0.008),
            (R * 0.80, 0.0), (R * 0.82, 0.008), (R, L * 0.22), (R * 0.80, L / 2 - 0.012), (R * 0.45, L / 2 - 0.002),
            (0.0, L / 2)]
    A.lathe(name, prof, tuple(at), X["horn"], seg=10, rot=(0, math.pi / 2, 0))


def tab(name, x0, x1, z0, h, base, X, t=0.005):
    """a leather tab sewn flat on the front at |y| base (its outer face), rounded ends, stitched round"""
    pts = []
    for k in range(7):
        a = math.pi / 2 + math.pi * k / 6
        pts.append((x0 + h / 2 + (h / 2) * math.cos(a), z0 + (h / 2) * math.sin(a)))
    for k in range(7):
        a = -math.pi / 2 + math.pi * k / 6
        pts.append((x1 - h / 2 + (h / 2) * math.cos(a), z0 + (h / 2) * math.sin(a)))
    A.extrude_poly(name, ccw(pts), t, X["leather"], Matrix.Translation((0, -(base + 0.0005), 0)), bevel=0.0015, segments=1)


def toggles(key, P, X):
    """three horn toggles: each sewn by a thong to a leather tab on the left front, caught by a thong loop that comes
    from a tab on the overlapping band"""
    F = P["flap"]
    cr = 0.0042
    for k, z0 in enumerate((-0.07, -0.31, -0.55)):
        tb = outer_y(0.05, F, z0)
        tab(f"{key}TabA{k}", 0.012, 0.082, z0, 0.050, tb, X)
        tab(f"{key}TabB{k}", 0.318, 0.390, z0, 0.050, SH_OUT, X)
        xt = 0.215
        Ry = 0.022
        yt = -(SH_OUT + 0.001 + 2 * cr + 0.002 + Ry)
        toggle(f"{key}Toggle{k}", Vector((xt, yt, z0)), X, R=Ry)
        # the loop: from tab A over the band's edge, under the toggle's waist and back
        lp = []
        for x, dz in ((0.055, 0.010), (0.085, 0.011), (0.097, 0.011), (0.112, 0.011), (0.16, 0.011), (0.20, 0.010),
                      (0.222, 0.0), (0.20, -0.010), (0.16, -0.011), (0.112, -0.011), (0.097, -0.011), (0.085, -0.011),
                      (0.055, -0.010)):
            base = outer_y(x, F, z0)
            if 0.0965 <= x <= 0.115:
                base = outer_y(0.099, F, z0) + 0.0012
            yb = base + cr + 0.0005
            if x >= 0.2:
                yb = SH_OUT + 0.0005 + cr
            if 0.25 > x > 0.18 and abs(dz) < 0.005:
                yb = SH_OUT + 0.0005 + cr
            lp.append((x, -(yb + (0.0055 if x <= 0.086 else 0.0)), z0 + dz))
        wire(f"{key}Loop{k}", lp, cr, X["thong"], sides=5, closed=True)
        # the thong from tab B to the toggle's waist (two strands)
        for dz in (-0.006, 0.006):
            st = [(0.35, -(SH_OUT + 0.0055 + cr), z0 + dz), (0.31, -(SH_OUT + 0.0008 + cr), z0 + dz * 0.8),
                  (0.27, -(SH_OUT + 0.003 + cr), z0 + dz * 0.6), (xt + 0.006, yt + Ry * 0.80 - cr * 0.2 - 0.0005, z0 + dz * 0.5)]
            wire(f"{key}Tie{k}{dz:+.3f}", st, cr * 0.85, X["thong"], sides=5)


def build_skirt_knit(name, P, X):
    """the knit skirt: as nh_acc_batchc1.build_skirt, but the bottom hb studs are a thick rib band (the same mid-surface,
    no layering, so the side stays under x 1.034), a rib front band along each front edge, rib bindings on the slit
    and the waist, and a patch pocket on each front"""
    zb = P["skirt_bot"]
    hb = P["hem_band"]
    zcut = zb + hb
    zs = [z for z in C1.skirt_rows(P) if z > zcut + 0.03] + [zcut]
    jj = zs.index(C1.SL_JOIN) if C1.SL_JOIN in zs else len(zs) - 1
    T_SK = C1.T_SKIRT
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        rows = []
        for z in zs:
            r, ia, ib = C1.skirt_plan(side, z, P)
            rows.append(r)
        nc = len(rows[0])

        def grid(cols, js, R=rows):
            return [[R[j][i] for j in js] for i in cols]

        def hint(p, side=side):
            return Vector((p.x - side * 0.5, p.y, 0)).normalized() if abs(p.x) > 0.1 or abs(p.y) > 0.1 else Vector((0, -1, 0))
        up, lo = list(range(0, jj + 1)), list(range(jj, len(zs)))
        cloth(f"{name}Front{sd}", grid(range(0, ia + 1), up), T_SK, X["wool"], hint, mat_in=X["lining"])
        cloth(f"{name}Back{sd}", grid(range(ib, nc), up), T_SK, X["wool"], hint, mat_in=X["lining"])
        if len(lo) > 1:
            cloth(f"{name}Hem{sd}", grid(range(0, nc), lo), T_SK, X["wool"], hint, mat_in=X["lining"])
        # the rib hem band: the same mid-surface, thicker, from just under the knit to the hem
        brow = [C1.skirt_plan(side, z, P)[0] for z in (zcut - 0.002, zcut - hb * 0.5, zb)]
        cloth(f"{name}HemBand{sd}", [[brow[j][i] for j in range(3)] for i in range(nc)], 0.020, X["rib"], hint)
        wire(f"{name}HemRoll{sd}", [tuple(brow[2][i] + Vector((0, 0, 0.002))) for i in range(nc)], 0.0115, X["rib"], sides=6)

        def nrm(R, i):
            a, b = R[max(i - 1, 0)], R[min(i + 1, len(R) - 1)]
            d = Vector((b.x - a.x, b.y - a.y, 0))
            n = Vector((d.y, -d.x, 0)).normalized()
            c = Vector((side * 0.5, 0, 0))
            if n.dot(Vector((R[i].x, R[i].y, 0)) - c) < 0:
                n = -n
            return n
        o = T_SK / 2 + 0.004
        for nm, cols in (("F", range(0, ia + 1)), ("B", range(ib, nc))):   # the waist seam, a rib binding
            wire(f"{name}Waist{nm}{sd}", [tuple(rows[0][i] + nrm(rows[0], i) * o + Vector((0, 0, -0.004))) for i in cols],
                 0.0055, X["rib"], sides=5)
        for nm, i in (("F", ia), ("B", ib)):   # the slit's edges
            wire(f"{name}Slit{nm}{sd}", [tuple(rows[j][i] + nrm(rows[j], i) * (o - 0.003)) for j in up], 0.0055, X["rib"], sides=5)
        # the front band: rib knit along the front edge, over the skirt (stops at the hem band)
        tf = 0.010
        Gf = [[rows[j][i] + nrm(rows[j], i) * (T_SK / 2 + 0.001 + tf / 2) for j in range(1, len(zs))] for i in (0, 1)]
        Gf = [[p - Vector((side * 0.002, 0, 0)) * (1 - k) for p in col] for k, col in enumerate(Gf)]
        cloth(f"{name}FrontBand{sd}", Gf, tf, X["rib"], lambda p: Vector((0, -1, 0)))
        # a patch pocket on the front: cable knit, a rib band across the top
        px0, px1 = 0.26, 0.60
        tp = 0.012
        yfront = lambda z: C1.skirt_plan(side, z, P)[0][0].y
        for nm, z0, z1, mat in (("Pocket", -1.17, -0.925, X["wool"]), ("PocketRib", -0.921, -0.87, X["rib"])):
            Gp = [[Vector((side * lerp(px0, px1, k / 6), yfront(lerp(z0, z1, j / 4)) - (T_SK / 2 + 0.001 + tp / 2),
                           lerp(z0, z1, j / 4))) for j in range(5)] for k in range(7)]
            cloth(f"{name}{nm}{sd}", Gp, tp, mat, lambda p: Vector((0, -1, 0)))


def build_cardigan_details(key, P, X):
    toggles(key, P, X)


@item("CardiganCoat", "Cable-knit cardigan coat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.2, 0, 0.30), 85))
def build_cardigan(M):
    key = "CardiganCoat"
    X, P = cardigan_mats(M), cardigan_params()
    P["inner"] = dict(front_z=[-0.04, 0.05, 0.15, 0.30, 0.45, 0.60, 0.75, 0.86, 0.90, 0.93, 0.96, 0.98, 1.0], mat=X["jumper"], edge_r=0.0065, edge_mat=X["jumper"])
    piece(f"{key}Shell", "Torso")
    build_shell_d(key, P, X, lambda nm, G, rows, side: shawl_collar(nm, G, rows, side, P, X))
    build_cardigan_details(key, P, X)
    piece(f"{key}Skirt", "Torso", rig=C1.skirt_rig)
    build_skirt_knit(f"{key}Skirt", P, X)
    sleeves(key, P, X)
    self_overlaps(key)
    hips_extra = C1.add_hips(key, P, X, P["inner"].get("hip_mat", P["inner"]["mat"]))
    C1.write_extra(key, dict(hips_extra, **{f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}))
    return dict(notes="the cable-knit cardigan coat: ink-blue knit with cables, a rolled shawl collar, horn toggles on "
                      "leather tabs, ribbed cuffs, front and hem bands, patch pockets; knee-length skirts that move with "
                      "the legs")
