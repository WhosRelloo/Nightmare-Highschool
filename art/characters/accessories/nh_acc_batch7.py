"""Accessories batch 7: the coats (Kit A 7 and Kit B 2), one coat builder for both.

  LongCoat    the Delinquent's long coat (Kit A 7, anyone may buy it): worn black wool, worn open, notch lapels and a
              rolled collar, a violet satin lining, silver buttons, buckled leather cuff straps, a leather half-belt on
              the back and the Delinquents' spade-and-bolt worked in silver thread between the shoulders; long split
              coattails at both sides
  Greatcoat   the Headmaster's greatcoat (Kit B 2, staff only): fine black wool, peak lapels and a wide fall collar in
              black velvet with gilt piping, a crimson silk lining (#600E1A), brass-and-bone buttons (double-breasted
              rows, the lapels buttoned back), crimson velvet turnback cuffs, a wool half-belt with a cast brass crow
              clasp, a gilt crow worked on the back; full-length split coattails with crimson turnbacks

How a coat works on R6 (no layered clothing): five pieces worn together.
  <Coat>Shell    Torso: the body of the coat. Open at the front (the shirt, tie and waistcoat show), lapels and a
                 collar. Its front panels are cut away at the side front (x >= 0.76 the panel ends above z -0.21: the
                 sheathed katana's guard sits there on the deep bodies) and its back hem ends at z -0.72 (below that a
                 striding leg's top corner pokes out of the torso). Under each arm it is a thin band (x 1.004..1.016,
                 the arm's inner 0.1 studs, so the arm covers it in every pose) down to the waist seam.
  <Coat>TailL/R  Torso, rigged (Tails): the long coattails hang beside the legs, OUTSIDE the leg-sweep volume: R6 legs
                 swing in their own planes and never pass |x| = 1, so a panel at x >= 1.02 clears them at any stride and
                 at every sway limit (fore and aft it bends in its own plane; sideways only outward, keep-out toward
                 the body). The inner face is the lining, which shows at the turnbacks and as the tails swing. The left
                 tail stays at x <= 1.035 above z -1.32: the sheathed scabbard runs back along the left side just
                 outside it (x >= 1.04 there).
  <Coat>SleeveL/R  LeftArm / RightArm: each wraps its arm (front, outer and back faces and the shoulder top; the inner
                 face is flush on the torso and left open), so it follows the arm swing exactly. The inner edge starts
                 at x 1.07 and steps out to x 1.14 below the elbow (the sheathed scabbard's top edge passes the
                 left forearm's front inner corner at z -0.53). The cuffs end at z -0.535, above the drawn katana's
                 grip in the right hand (its guard top at z -0.60, the blade's back end at -0.57).
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch7 --gpu
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import ccw, frame, buckle
from nh_acc_batch4 import wire, axis_frame, place, arm_wrap, mirror_piece

D_F = 0.024        # the shell's mid-surface off the torso's front / back / top
T_SHELL = 0.016    # its thickness
D_S = 0.010        # the side band's mid-surface off the torso side (under the arm)
T_BAND = 0.012
HEM_BACK = -0.72   # the back hem (a striding leg's top corner pokes out of the torso below about z -0.75)
WAIST = -0.60      # the waist seam at the sides, where the tails hang from
X_TAIL = 1.029     # the tails' mid-surface at the top (inner face 1.0225, outer 1.0355)
T_TAIL = 0.013
HINGE = -1.0       # the tails bend below the torso's bottom (rigid above)


# ================================================================== generic cloth
def oriented(G, hint):
    """reverse the grid's first index if its surface normal points against hint(p) (A.surface puts its 'outer'
    shell on the +normal side)"""
    nu, nv = len(G), len(G[0])
    score = 0.0
    for i in range(1, nu - 1, max(1, nu // 6)):
        for j in range(1, nv - 1, max(1, nv // 6)):
            n = (G[i + 1][j] - G[i - 1][j]).cross(G[i][j + 1] - G[i][j - 1])
            score += n.normalized().dot(hint(G[i][j])) if n.length > 1e-9 else 0.0
    return G if score >= 0 else G[::-1]


def cloth(name, G, thick, mat, hint, mat_in=None):
    """a cloth panel of real thickness from a mid-surface grid G[i][j]; the face toward hint(p) gets `mat`, the
    other face `mat_in` (a lining) when given"""
    G = oriented([[Vector(p) for p in col] for col in G], hint)
    ob = A.surface(name, G, thick, mat)
    if mat_in is not None:
        nq = (len(G) - 1) * (len(G[0]) - 1)
        ob.data.materials.append(mat_in)
        for k, p in enumerate(ob.data.polygons):
            if k < 2 * nq and k % 2 == 1:
                p.material_index = 1
    return ob


def out_hint_torso(p):
    """away from the torso box (the coat's outside)"""
    q = Vector((max(abs(p.x) - 0.9, 0) * (1 if p.x >= 0 else -1), max(abs(p.y) - 0.4, 0) * (1 if p.y >= 0 else -1),
                max(p.z - 0.9, 0)))
    return q if q.length > 1e-6 else Vector((0, 0, 1))


def button(name, at, nrm, X, kind, r=0.034):
    """a coat button on a surface, its face along nrm: 'bonebrass' (a bone dome in a brass cup) or 'silver' (domed)"""
    F = axis_frame(at, nrm)
    if kind == "bonebrass":   # one lathe: the bone dome set in a raised brass bezel (two materials)
        ob = A.lathe(name, [(0.0, 0.0205), (r * 0.36, 0.0195), (r * 0.62, 0.0165), (r * 0.78, 0.0110), (r * 0.86, 0.0150),
                            (r * 1.02, 0.0125), (r * 1.06, 0.0050), (r, 0.0), (0.0, 0.0)], (0, 0, 0), X["brass"], seg=10)
        ob.data.materials.append(X["bone"])
        for p in ob.data.polygons:
            c = p.center
            if math.hypot(c.x, c.y) < r * 0.79 and c.z > 0.009:
                p.material_index = 1
        place(ob, F)
    else:   # domed silver with a raised ring
        place(A.lathe(name, [(0.0, 0.021), (r * 0.35, 0.0205), (r * 0.58, 0.0180), (r * 0.66, 0.0200), (r * 0.74, 0.0170),
                             (r * 0.95, 0.011), (r * 1.03, 0.005), (r, 0.0), (0.0, 0.0)], (0, 0, 0), X["silver"], seg=10), F)


# ================================================================== the shell (torso)
def lapel_line(z, P):
    """x of the front edge (the lapel's fold line above the break, straight below, rounded into the hem)"""
    zb = P["break"]
    if z >= zb:
        return lerp(P["xo_break"], P["xo_top"], (z - zb) / (1.0 - zb))
    if z > -0.62:
        return P["xo_break"]
    R = 0.10
    return P["xo_break"] + R - math.sqrt(max(0.0, R * R - (z + 0.62) ** 2))


def cut_line(z):
    """x where the front panel ends at the side front: the cutaway (x <= 0.76 below z -0.21, clear of the sheathed
    katana's guard on every body) sweeping up into the side seam at z -0.08"""
    if z >= -0.08:
        return 1.0
    if z >= -0.26:
        th = math.asin(min(1.0, (z + 0.26) / 0.18))
        return 0.74 + 0.26 * (1 - math.cos(th))
    if z >= -0.62:
        return 0.74
    R = 0.10
    return 0.64 + math.sqrt(max(0.0, R * R - (z + 0.62) ** 2))


FRONT_Z = [-0.72, -0.70, -0.66, -0.62, -0.48, -0.34, -0.26, -0.20, -0.14, -0.105, -0.08, 0.05, 0.18, 0.40, 0.62, 0.82, 0.94, 1.0]
BACK_Z = [1.0, 0.98, 0.95, 0.91, 0.80, 0.55, 0.30, 0.05, -0.20, -0.40, -0.56, -0.66, -0.72]
TOP_Y = [-0.5, -0.25, 0.0, 0.25, 0.5]
ARC = [30, 60]


def shell_rows(P):
    """the shell's rows on one side (x >= 0): front face (hem up), round the front top edge, across the shoulder top,
    round the back top edge, down the back. Each row: (y, z, region, x_start, x_end); the point at the mid-surface"""
    d = D_F
    rn = math.hypot(P["xo_top"], 0.5 + d)   # the neckline on the shoulder top: a circle through the lapel tops
    rows = []
    for z in FRONT_Z:
        rows.append((-(0.5 + d), z, "front", lapel_line(z, P), cut_line(z)))
    for a in ARC:
        y = -0.5 - d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for y in TOP_Y:
        rows.append((y, 1.0 + d, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for a in ARC[::-1]:
        y = 0.5 + d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", math.sqrt(max(0.0, rn * rn - y * y)), 1.0))
    for z in BACK_Z:
        rows.append((0.5 + d, z, "back", P["xo_top"] * smooth(0.91, 1.0, z), 1.0))
    return rows


def back_fold(x, z, P):
    """soft vertical folds below the half-belt (outward only)"""
    k = P.get("back_folds", 0.006)
    return k * smooth(-0.30, HEM_BACK, z) * (0.5 - 0.5 * math.cos(2 * math.pi * x / 0.5))


def shell_grid(side, P, ncol=9):
    rows = shell_rows(P)
    G = []
    for i in range(ncol + 1):
        col = []
        for (y, z, reg, xs, xe) in rows:
            x = lerp(xs, xe, i / ncol)
            yy = y
            if reg == "back":
                yy = y + back_fold(x, z, P)
            col.append(Vector((side * x, yy, z)))
        G.append(col)
    return G, rows


def band_path(z):
    """the side band's plan path (x > 0) at height z: round the front vertical corner, along the side, round the
    back corner; returns a sampler u (0..1) -> (x, y). Below the cutaway it starts at y -0.45 (no front corner):
    on the deep bodies the depth fit pushes the band's front out toward the sheathed guard"""
    pts = []
    for a in (0, 20, 40, 60, 80):
        t = math.radians(a)
        pts.append(Vector((1.0 + D_S * math.sin(t), -0.5 - D_F * math.cos(t))))
    for y in (-0.47, -0.30, -0.10, 0.10, 0.30, 0.47):
        pts.append(Vector((1.0 + D_S, y)))
    for a in (80, 60, 40, 20, 0):
        t = math.radians(a)
        pts.append(Vector((1.0 + D_S * math.sin(t), 0.5 + D_F * math.cos(t))))
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    u0 = 0.0
    if z < -0.08:
        s_side = L[4] + abs(-0.45 - pts[4].y)   # pts[4] is the corner's end (x 1.0098, y -0.5)
        u0 = lerp(0.0, s_side / L[-1], smooth(-0.08, -0.20, z))

    def at(u):
        s = lerp(u0, 1.0, u) * L[-1]
        for k in range(len(pts) - 1):
            if s <= L[k + 1] or k == len(pts) - 2:
                f = (s - L[k]) / max(1e-9, L[k + 1] - L[k])
                return pts[k].lerp(pts[k + 1], min(1.0, max(0.0, f)))
    return at


BAND_Z = [WAIST - 0.12, WAIST, -0.36, -0.20, -0.14, -0.08, 0.20, 0.60, 0.90, 1.0]


def band_grid(side, ncol=10):
    G = [[None] * len(BAND_Z) for _ in range(ncol + 1)]
    for j, z in enumerate(BAND_Z):
        at = band_path(z)
        for i in range(ncol + 1):
            p = at(0.5 - 0.5 * math.cos(math.pi * i / ncol))   # dense round the corners
            G[i][j] = Vector((side * p.x, p.y, z))
    return G


def build_shell(name, P, X):
    """both halves of the shell (built per side so each half's details can differ), the side bands, the collar,
    the lapels, seams and piping"""
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G, rows = shell_grid(side, P)
        cloth(f"{name}Body{sd}", G, T_SHELL, X["wool"], out_hint_torso, mat_in=X["lining"])
        cloth(f"{name}Band{sd}", band_grid(side), T_BAND, X["wool"], out_hint_torso, mat_in=X["lining"])
        out = T_SHELL / 2 + 0.004
        # piping: the front edge below the break, the cutaway hem round to the side seam, the back hem
        nf = len(FRONT_Z)
        jb = FRONT_Z.index(P["break"])
        edge = [G[0][j] for j in range(jb, -1, -1)] + [G[i][0] for i in range(1, len(G))] + \
               [G[-1][j] for j in range(1, nf) if FRONT_Z[j] <= -0.075]
        edge = [p + Vector((0, -out, 0)) for p in edge]
        wire(f"{name}PipeFront{sd}", [tuple(p) for p in edge], P["pipe_r"], X["pipe"], sides=5)
        jh = len(rows) - 1
        hem = [G[i][jh] + Vector((0, out + 0.002, 0)) for i in range(len(G))]
        wire(f"{name}PipeBack{sd}", [tuple(p) for p in hem], P["pipe_r"], X["pipe"], sides=5)
        # the shoulder seam (top-stitched) and the side-front seam down the corner
        top = [r for r in rows if r[2] == "top"]
        yk = min(range(len(top)), key=lambda k: abs(top[k][0]))
        ys = top[yk]
        wire(f"{name}SeamShoulder{sd}", [(side * lerp(ys[3], 1.0, t), ys[0], ys[1] + out + 0.001) for t in (0.04, 0.5, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSide{sd}", [(side * (1.0 + 0.002), -(0.5 + D_F + out - 0.004), z) for z in (-0.06, 0.4, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSideB{sd}", [(side * (1.0 + 0.002), 0.5 + D_F + out - 0.004, z) for z in (HEM_BACK + 0.02, 0.2, 0.97)],
             0.0035, X["thread"], sides=4)
        build_collar(f"{name}Collar{sd}", G, rows, side, P, X)
        build_lapel(f"{name}Lapel{sd}", side, P, X)
    # the centre back seam
    wire(f"{name}SeamBack", [(0, 0.5 + D_F + T_SHELL / 2 + 0.001, z) for z in (HEM_BACK + 0.02, -0.2, 0.4, 0.90)], 0.004,
         X["thread"], sides=4)


def build_collar(name, G, rows, side, P, X):
    """the rolled collar along the neckline (the shell's first column from the front top round to the centre back):
    a stand, a crest and a fall lying out over the shoulder top (on the back it falls down the back)"""
    j0 = next(j for j, r in enumerate(rows) if r[2] == "top")
    jz = [j for j, r in enumerate(rows) if r[2] == "back" and r[1] >= 0.905]
    js = [j0 - 1] + list(range(j0, jz[-1] + 1))
    base = []
    for j in js:
        p = G[0][j]
        y, z, reg = rows[j][0], rows[j][1], rows[j][2]
        nrm = Vector((0, 0, 1)) if reg == "top" else (Vector((0, 1, 0)) if reg == "back" else Vector((0, -1, 0)))
        if reg == "top" and abs(y) > 0.5:
            nrm = Vector((0, math.copysign(math.cos(math.radians(60)), y), math.sin(math.radians(60))))
        base.append((p + nrm * (T_SHELL / 2 + 0.002), reg, y, z))
    rise, reach = P["collar_rise"], P["collar_reach"]
    cols = []
    n = len(base)
    for k, (b, reg, y, z) in enumerate(base):
        t = k / (n - 1)
        out = Vector((b.x, b.y, 0)).normalized()
        w = 1.0 if reg == "back" else (smooth(0.49, 0.524, y) if reg == "top" else 0.0)
        fr = smooth(0.0, 0.22, t)   # the front end flattens into the lapel's top (the notch)
        up = Vector((0, 0, 1))
        S = b + up * (0.045 * fr + 0.008) + out * 0.006
        C = b + up * (rise * fr + 0.012) + out * lerp(0.04, 0.06, w)
        Fp = b + up * lerp(rise * 0.75 * fr + 0.01, 0.035, w) + out * lerp(reach * 0.62, 0.075, w)
        O = b + up * lerp(0.010, -P["collar_back"], w) + out * lerp(reach * fr + 0.05 * (1 - fr), 0.028, w)
        cols.append([b, S, C, Fp, O])

    def hint(p):
        return Vector((p.x, p.y, 0)).normalized() * 0.5 + Vector((0, 0, 0.9))
    cloth(name, cols, 0.014, X["collar"], hint)
    # piping along the collar's outer edge
    wire(name + "Edge", [tuple(c[4] + Vector((0, 0, 0.002))) for c in cols], P["pipe_r"] * 0.9, X["collar_pipe"], sides=5)


def build_lapel(name, side, P, X):
    """the lapel folded back on the front panel, from the break up to the collar: notch (top edge falling outward)
    or peak (rising to a point)"""
    zb = P["break"]
    y = -(0.5 + D_F + T_SHELL / 2 + 0.0075)
    rows_z = [zb + (0.99 - zb) * (k / 10) ** 0.9 for k in range(11)]
    cols = []
    nu = 5
    for i in range(nu + 1):
        u = i / nu
        col = []
        for v, z in enumerate(rows_z):
            zt = 0.99 - P["notch"] * u if P["lapel"] == "notch" else 0.95 + 0.05 * u
            zz = lerp(zb, zt, (z - zb) / (0.99 - zb))
            W = P["lapel_w"] * smooth(zb - 0.05, zb + 0.55, zz) + 0.02
            if P["lapel"] == "peak":
                W += 0.05 * smooth(0.80, 0.97, zz) * u
            x = lapel_line(zz, P) + W * u
            col.append(Vector((side * x, y - 0.004 * u, zz)))
        cols.append(col)
    cloth(name, cols, 0.012, X["lapel"], lambda p: Vector((0, -1, 0)), mat_in=X["wool"])
    # the roll along the fold and the piping on the lapel's outer edge
    wire(name + "Roll", [(side * lapel_line(z, P), y + 0.002, z) for z in rows_z], 0.011, X["lapel"], sides=6)
    wire(name + "Edge", [tuple(cols[-1][v] + Vector((0, -0.0065, 0))) for v in range(len(rows_z))] +
         [tuple(cols[i][-1] + Vector((0, -0.0065, 0))) for i in range(nu - 1, 0, -1)], P["pipe_r"] * 0.8, X["lapel_pipe"], sides=5)


# ================================================================== the coattails (Torso, rigged)
def tail_fns(P):
    zb = P["tail_bot"]

    def X_(u, z):
        fl = P["tail_flare"] * smooth(-1.35, zb, z) ** 1.3
        fo = P["tail_fold"] * smooth(-1.05, zb, z) * (0.5 - 0.5 * math.cos(2 * math.pi * P["tail_nfold"] * u))
        return X_TAIL + fl + fo

    def Y_(u, z):
        yf = -0.50 - P["tail_fwd"] * smooth(-1.0, zb, z)
        yb = 0.50 + P["tail_back"] * smooth(-0.9, zb, z)
        return lerp(yf, yb, u)
    return X_, Y_


def tail_rows(P):
    zb = P["tail_bot"]
    zs = [WAIST, -0.66, -0.74, -0.84, -0.93, -1.0, -1.06]
    z = -1.06
    while z - 0.13 > zb + 0.03:
        z -= 0.13
        zs.append(z)
    zs += [zb + 0.012, zb]
    return zs


def tail_joints(P):
    zb = P["tail_bot"]
    n = P["tail_bones"]
    return [lerp(HINGE, zb + 0.04, k / n) for k in range(n + 1)]


def tail_rig(side, P):
    X_, Y_ = tail_fns(P)

    def rig(ob):
        cols = [[Vector((side * X_(u, z), Y_(u, z), z)) for z in tail_joints(P)] for u in (0.1, 0.5, 0.9)]
        return A.chain_rig(ob, (side * X_TAIL, 0.0, HINGE + 0.05), cols, rigid_above=HINGE)
    return rig


def build_tail(name, P, X):
    """the left coattail (x > 0): the wool outside, the lining inside, a facing of lining down the front edge,
    a binding at the hem, a welt where it hangs from the waist seam"""
    X_, Y_ = tail_fns(P)
    zs = tail_rows(P)
    zb = P["tail_bot"]
    nu = 18
    G = [[Vector((X_(i / nu, z), Y_(i / nu, z), z)) for z in zs] for i in range(nu + 1)]
    cloth(name + "Panel", G, T_TAIL, X["wool"], lambda p: Vector((1, 0, 0)), mat_in=X["lining"])
    o = T_TAIL / 2 + 0.0035
    # the facing: the lining turned out over the front edge (a narrow strip on the outside)
    fw = P["facing_w"]
    z_lo = zb + (P["turnback"][1] - 0.02 if P.get("turnback") else 0.0)
    zs_f = [z for z in zs if HINGE + 0.02 >= z >= z_lo] + ([z_lo] if P.get("turnback") else [])
    Gf = [[Vector((X_(u, z) + T_TAIL / 2 + 0.0025, Y_(u, z), z)) for z in zs_f] for u in (0.0, fw * 0.5, fw)]
    cloth(name + "Facing", Gf, 0.004, X["lining"], lambda p: Vector((1, 0, 0)))
    wire(name + "Hem", [(X_(i / 24, zb) + 0.002, Y_(i / 24, zb), zb + 0.004) for i in range(25)], P["pipe_r"], X["pipe"], sides=5)
    wire(name + "Stitch", [(X_(i / 24, zb + 0.045) + o - 0.001, Y_(i / 24, zb + 0.045), zb + 0.045) for i in range(1, 24)],
         0.0028, X["thread"], sides=4)
    if P.get("turnback"):   # the front-bottom corner turned back and buttoned: the lining shows
        uw, H = P["turnback"]
        rows = [zb + H * (k / 8) for k in range(9)]
        Gt = []
        for i in range(7):
            col = []
            for z in rows:
                u = (uw * (1 - (z - zb) / H) + 0.03) * i / 6
                col.append(Vector((X_(u, z) + o + 0.004, Y_(u, z), z)))
            Gt.append(col)
        cloth(name + "Turnback", Gt, 0.006, X["lining"], lambda p: Vector((1, 0, 0)))
        wire(name + "TurnRoll", [tuple(Gt[6][k] + Vector((0.003, 0, 0))) for k in range(9)], 0.008, X["lining"], sides=5)
        zt = zb + H * 0.30
        ut = (uw * 0.70 + 0.03) * 0.8
        button(name + "TurnBtn", Vector((X_(ut, zt) + o + 0.008, Y_(ut, zt), zt)), (1, 0, 0), X, X["btn"], r=0.030)


# ================================================================== the sleeves (arms)
SLEEVE_Z = [-0.535, -0.50, -0.42, -0.30, -0.18, -0.05, 0.10, 0.28, 0.46, 0.62, 0.76, 0.88, 0.96, 1.0]
X_IN_TOP, X_IN_LOW = -0.43, -0.36   # arm-local inner edge (x 1.07 up top, 1.14 below the elbow)


def x_in(z):
    return lerp(X_IN_LOW, X_IN_TOP, smooth(-0.24, 0.04, z))


def wrap_kw():
    return dict(a=0.025, n_arc=3, n_face=4, n_out=6)


def sleeve_grid(d=0.020):
    """the left sleeve's mid-surface: the U round the arm's front, outer and back faces (cuff to shoulder), round the
    top edge, and a cap over the shoulder top to the inner edge"""
    rowsP = []
    for z in SLEEVE_Z:
        ease = 0.003 * math.sin(math.pi * smooth(-0.5, 0.9, z))
        rowsP.append([Vector((1.5 + X, Y, z)) for X, Y in arm_wrap(d + ease, x_in=x_in(z), **wrap_kw())])
    E0 = arm_wrap(0.0, x_in=X_IN_TOP, **wrap_kw())
    Ed = arm_wrap(d, x_in=X_IN_TOP, **wrap_kw())
    for a in (35, 70):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rowsP.append([Vector((1.5 + e[0] + (f[0] - e[0]) * c, e[1] + (f[1] - e[1]) * c, 1.0 + d * s_)) for e, f in zip(E0, Ed)])
    n = len(E0)
    T = [(X_IN_TOP, lerp(-0.40, 0.40, k / (n - 1))) for k in range(n)]
    for f in (0.0, 0.3, 0.6, 1.0):
        rowsP.append([Vector((1.5 + lerp(E0[k][0], T[k][0], f), lerp(E0[k][1], T[k][1], f), 1.0 + d)) for k in range(n)])
    return [[rowsP[j][k] for j in range(len(rowsP))] for k in range(n)]


def sleeve_hint(p):
    return Vector((p.x - 1.5, p.y, 3.0 if p.z > 0.995 else 0.0))


def build_sleeve(name, P, X):
    G = sleeve_grid()
    cloth(name + "Body", G, 0.014, X["wool"], sleeve_hint, mat_in=X["lining"])
    wire(name + "Hem", [tuple(c[0] + (c[0] - Vector((1.5, 0, c[0].z))).normalized() * 0.006) for c in G], 0.0075,
         X["wool"], sides=5)
    seam = [Vector((1.5 + 0.10, 0.5 + 0.020 + 0.0085, z)) for z in (-0.52, -0.2, 0.3, 0.8, 0.97)]
    wire(name + "Seam", [tuple(p) for p in seam], 0.0032, X["thread"], sides=4)
    if P["cuff"] == "turnback":   # a turned-back velvet cuff, gilt piping, two buttons
        zs = [-0.535, -0.50, -0.44, -0.37, -0.30]
        prof = [arm_wrap(0.040 + 0.004 * (j / 4), x_in=X_IN_LOW + 0.005, **wrap_kw()) for j in range(len(zs))]
        Gc = [[Vector((1.5 + prof[j][k][0], prof[j][k][1], z)) for j, z in enumerate(zs)] for k in range(len(prof[0]))]
        cloth(name + "Cuff", Gc, 0.014, X["cuff"], sleeve_hint)
        wire(name + "CuffPipe", [tuple(c[-1] + (c[-1] - Vector((1.5, 0, c[-1].z))).normalized() * 0.006 + Vector((0, 0, 0.004)))
                                 for c in Gc], P["pipe_r"] * 0.9, X["cuff_pipe"], sides=5)
        for k, z in enumerate((-0.37, -0.47)):
            button(f"{name}CuffBtn{k}", Vector((2.0 + 0.049, 0.30, z)), (1, 0, 0), X, X["btn"], r=0.028)
    else:   # a buckled leather strap round the cuff
        zc = -0.43
        Gs = [[Vector((1.5 + Xp, Yp, z)) for z in (zc + 0.028, zc - 0.028)]
              for Xp, Yp in arm_wrap(0.034, x_in=X_IN_LOW + 0.004, **wrap_kw())]
        cloth(name + "Strap", Gs, 0.010, X["strap"], sleeve_hint)
        buckle(name + "Buckle", Vector((2.0 + 0.044, -0.08, zc)), 0.075, 0.068, X["silver"], rot=(0, 0, math.radians(90)))
        A.box(name + "StrapEnd", (0.008, 0.09, 0.044), (2.0 + 0.046, 0.06, zc), X["strap"], bevel=0.003)
        for k, y in enumerate((-0.30, 0.30)):
            A.sphere(f"{name}Stud{k}", 0.010, (2.0 + 0.040, y, zc), X["silver"], scale=(0.5, 1, 1), seg=8, rings=5)


# ================================================================== details
def front_point(x, z, lift=0.0):
    """a point on the shell's front outside (x signed)"""
    return Vector((x, -(0.5 + D_F + T_SHELL / 2 + lift), z))


def back_point(x, z, lift=0.0):
    return Vector((x, 0.5 + D_F + T_SHELL / 2 + lift, z))


def pocket_flap(name, side, z, X, mat, pipe=None, btn=None):
    x0, x1 = 0.45, 0.69
    pts = [(x0, z), (x1, z), (x1 - 0.004, z - 0.085), (lerp(x0, x1, 0.5), z - 0.10), (x0 + 0.004, z - 0.085)]
    pts = ccw([(side * x, zz) for x, zz in pts])
    A.extrude_poly(name, pts, 0.010, mat, Matrix.Translation((0, -(0.5 + D_F + T_SHELL / 2), 0)), bevel=0.003, segments=1)
    if pipe is not None:
        wire(name + "Pipe", [(side * x, -(0.5 + D_F + T_SHELL / 2) - 0.010, zz) for x, zz in
                             ((x0, z - 0.002), (x0 + 0.004, z - 0.083), (lerp(x0, x1, 0.5), z - 0.098), (x1 - 0.004, z - 0.083),
                              (x1, z - 0.002))], 0.0045, pipe, sides=4)
    if btn is not None:
        button(name + "Btn", front_point(side * lerp(x0, x1, 0.5), z - 0.06, 0.010), (0, -1, 0), X, btn, r=0.024)


def half_belt(name, z, X, mat, folds, w=0.085, x1=0.64):
    """a half-belt across the back at z, stitched down at both ends"""
    G = [[back_point(x, zz, 0.006 + back_fold(abs(x), zz, folds)) for zz in (z - w / 2, z + w / 2)]
         for x in [lerp(-x1, x1, k / 16) for k in range(17)]]
    cloth(name, G, 0.012, mat, lambda p: Vector((0, 1, 0)))
    for s in (-1, 1):
        wire(f"{name}Stitch{s}", [tuple(back_point(s * (x1 - 0.015), z + dz, 0.0125)) for dz in (-w / 2 + 0.012, w / 2 - 0.012)],
             0.0025, X["thread"], sides=4)


def crow_outline():
    """a heraldic crow displayed (wings spread, head turned), unit size, x across, z up"""
    R = [(0.10, 0.22), (0.30, 0.31), (0.55, 0.43), (0.82, 0.47), (1.0, 0.41), (0.88, 0.32), (0.95, 0.23), (0.79, 0.19),
         (0.84, 0.08), (0.65, 0.07), (0.66, -0.04), (0.45, -0.02), (0.22, -0.06), (0.14, -0.23), (0.22, -0.53),
         (0.08, -0.46), (0.0, -0.60)]
    L = [(-x, z) for x, z in reversed(R[:-1])]
    head = [(-0.08, 0.32), (-0.02, 0.40), (0.05, 0.42), (0.10, 0.38), (0.24, 0.37), (0.11, 0.31)]
    return R + L + head


def spade_bolt():
    """the Delinquents' crest: a spade with a lightning bolt across it (unit size, x across, z up)"""
    spade = [(0.0, 0.62), (0.22, 0.34), (0.48, 0.08), (0.52, -0.14), (0.40, -0.30), (0.20, -0.30), (0.07, -0.18),
             (0.16, -0.55), (-0.16, -0.55), (-0.07, -0.18), (-0.20, -0.30), (-0.40, -0.30), (-0.52, -0.14), (-0.48, 0.08),
             (-0.22, 0.34)]
    bolt = [(-0.42, 0.52), (0.06, 0.12), (-0.10, 0.06), (0.42, -0.42), (-0.02, 0.0), (0.14, 0.05)]
    return spade, bolt


def coat_mats(M, kind):
    if kind == "delinquent":
        X = dict(
            wool=A.mat_cloth("DelinqWool", (0.022, 0.021, 0.025), weave=240, rough=0.86, sheen=0.45, bump=0.14, vary=0.10,
                             wear=0.35, dirt=0.6),
            lining=A.mat_cloth("VioletSatin", (0.070, 0.020, 0.105), weave=520, rough=0.36, sheen=0.35, bump=0.04, twill=False),
            thread=A.mat_cloth("SilverThread", (0.55, 0.55, 0.60), weave=900, rough=0.40, sheen=0.2, bump=0.05, twill=False),
            silver=M["silver"], strap=M["leather_black"], brass=M["brass"], bone=M["bone"], btn="silver")
        X.update(collar=X["wool"], lapel=X["wool"], pipe=X["wool"], collar_pipe=X["wool"], lapel_pipe=X["thread"])
        return X
    X = dict(
        wool=A.mat_cloth("HeadmasterWool", (0.015, 0.014, 0.017), weave=330, rough=0.84, sheen=0.5, bump=0.10, vary=0.06,
                         wear=0.12, dirt=0.4),
        lining=M["crimson_silk"], velvet=M["black_velvet"], cuff=M["crimson_velvet"], gilt=M["gold"],
        brass=A.mat_metal("BlackenedBrass", (0.46, 0.33, 0.15), rough=0.34, tarnish=(0.07, 0.05, 0.03), wear=0.55),
        bone=M["bone"], silver=M["silver"],
        thread=A.mat_cloth("BlackThread", (0.03, 0.028, 0.03), weave=900, rough=0.6, sheen=0.2, bump=0.05, twill=False),
        btn="bonebrass")
    X.update(collar=X["velvet"], lapel=X["velvet"], pipe=X["velvet"], collar_pipe=X["gilt"], lapel_pipe=X["gilt"],
             cuff_pipe=X["gilt"])
    return X


# ================================================================== the coats
def coat_params(kind):
    if kind == "delinquent":
        return dict(xo_top=0.50, xo_break=0.36, lapel="notch", lapel_w=0.24, notch=0.07, collar_rise=0.085,
                    collar_reach=0.15, collar_back=0.09, pipe_r=0.0055, tail_bot=-2.45, tail_flare=0.16, tail_fold=0.035,
                    tail_nfold=2.5, tail_fwd=0.12, tail_back=0.26, tail_bones=4, facing_w=0.05, cuff="strap",
                    back_folds=0.007, brk=0.18)
    return dict(xo_top=0.50, xo_break=0.36, lapel="peak", lapel_w=0.29, notch=0.0, collar_rise=0.10, collar_reach=0.21,
                collar_back=0.13, pipe_r=0.0065, tail_bot=-2.85, tail_flare=0.24, tail_fold=0.045, tail_nfold=3.0,
                tail_fwd=0.18, tail_back=0.40, tail_bones=4, facing_w=0.06, cuff="turnback", turnback=(0.42, 0.62),
                back_folds=0.009, brk=0.18)


def coat_pieces(key):
    return [f"{key}Shell", f"{key}TailL", f"{key}TailR", f"{key}SleeveL", f"{key}SleeveR"]


def build_coat(key, P, X, details):
    P["break"] = P["brk"]
    piece(f"{key}Shell", "Torso")
    build_shell(key, P, X)
    details(key, P, X)
    piece(f"{key}TailL", "Torso", rig=tail_rig(1, P), sway="Tails", keepout=(-1, 0, 0), lock="X")
    build_tail(f"{key}TailL", P, X)
    mirror_piece(f"{key}TailL", f"{key}TailR")
    piece(f"{key}TailR", "Torso", rig=tail_rig(-1, P), sway="Tails", keepout=(1, 0, 0), lock="X")
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve(f"{key}SleeveL", P, X)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")


def delinquent_details(key, P, X):
    # silver buttons down the wearer's right front, thread buttonholes on the left
    for k, z in enumerate((0.10, -0.08, -0.26, -0.44)):
        button(f"{key}Btn{k}", front_point(-0.43, z), (0, -1, 0), X, "silver", r=0.032)
        wire(f"{key}Hole{k}", [tuple(front_point(x, z, 0.002)) for x in (0.385, 0.425, 0.465)], 0.0045, X["thread"], sides=4)
    for s in (1, -1):
        pocket_flap(f"{key}Pocket{'L' if s > 0 else 'R'}", s, -0.30, X, X["wool"])
        A.sphere(f"{key}PocketSnap{s}", 0.014, tuple(front_point(s * 0.57, -0.36, 0.010)), X["silver"], scale=(1, 0.5, 1),
                 seg=10, rings=6)
    half_belt(f"{key}HalfBelt", -0.26, X, X["strap"], P)
    for s in (-1, 1):
        button(f"{key}BeltBtn{s}", back_point(s * 0.58, -0.26, 0.0125), (0, 1, 0), X, "silver", r=0.030)
    # the spade-and-bolt in silver thread between the shoulders (couched cord)
    spade, bolt = spade_bolt()
    for nm, pts, r in (("Spade", spade, 0.0055), ("Bolt", bolt, 0.0045)):
        wire(f"{key}Crest{nm}", [tuple(back_point(-0.34 * x, 0.40 + 0.34 * z, 0.003)) for x, z in pts], r, X["thread"],
             sides=4, closed=True)
    # a small silver spade stud on the left lapel
    A.extrude_poly(f"{key}LapelStud", ccw([(0.0, 0.05), (0.03, 0.012), (0.034, -0.012), (0.012, -0.018), (0.006, -0.01),
                                           (0.012, -0.04), (-0.012, -0.04), (-0.006, -0.01), (-0.012, -0.018),
                                           (-0.034, -0.012), (-0.03, 0.012)]), 0.008, X["silver"],
                   Matrix.Translation((lapel_line(0.62, P) + 0.13, -(0.5 + D_F + T_SHELL / 2 + 0.0135) - 0.002, 0.62)),
                   bevel=0.002, segments=1)


def headmaster_details(key, P, X):
    # brass-and-bone buttons, double-breasted, both front panels; two more on each lapel, buttoned back
    for s in (1, -1):
        for k, z in enumerate((0.06, -0.22, -0.48)):
            for c, x in enumerate((0.47, 0.66)):
                button(f"{key}Btn{s}{k}{c}", front_point(s * x, z), (0, -1, 0), X, "bonebrass", r=0.034)
        for k, z in enumerate((0.60,)):
            W = P["lapel_w"] * smooth(P["break"] - 0.05, P["break"] + 0.55, z) + 0.02
            button(f"{key}LapelBtn{s}{k}", front_point(s * (lapel_line(z, P) + W * 0.62), z, 0.0135), (0, -1, 0), X,
                   "bonebrass", r=0.026)
    # a wool half-belt across the back with the brass crow clasp
    half_belt(f"{key}HalfBelt", -0.24, X, X["wool"], P, w=0.09, x1=0.66)
    for s in (-1, 1):
        button(f"{key}BeltBtn{s}", back_point(s * 0.60, -0.24, 0.0125), (0, 1, 0), X, "bonebrass", r=0.030)
    crow = ccw(crow_outline())
    Fc = Matrix.Translation(back_point(0.0, -0.24, 0.0125)) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Scale(0.13, 4)
    A.extrude_poly(f"{key}CrowClasp", crow, 0.016 / 0.13, X["brass"], Fc, bevel=0.0)
    # the gilt crow worked on the back (couched gold cord)
    wire(f"{key}BackCrow", [tuple(back_point(-0.40 * x, 0.30 + 0.40 * z, 0.003)) for x, z in crow_outline()], 0.0050,
         X["gilt"], sides=4, closed=True)


@item("LongCoat", "Delinquent's long coat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.35, 0, 0.30), 85))
def build_longcoat(M):
    build_coat("LongCoat", coat_params("delinquent"), coat_mats(M, "delinquent"), delinquent_details)
    return dict(notes="the Delinquent's long coat: worn black wool, open, notch lapels and a rolled collar, a violet satin "
                      "lining, silver buttons, buckled cuff straps, a leather half-belt and the spade-and-bolt in silver "
                      "thread on the back; long split coattails at the sides (outside the leg sweep), Tails sway")


@item("Greatcoat", "Headmaster's greatcoat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.35, 0, 0.30), 85))
def build_greatcoat(M):
    build_coat("Greatcoat", coat_params("headmaster"), coat_mats(M, "headmaster"), headmaster_details)
    return dict(notes="the Headmaster's greatcoat: fine black wool, black velvet peak lapels and fall collar with gilt "
                      "piping, crimson silk lining, brass-and-bone buttons, crimson velvet turnback cuffs, a half-belt "
                      "with a brass crow clasp and a gilt crow on the back; full-length split coattails with crimson "
                      "turnbacks, Tails sway")
