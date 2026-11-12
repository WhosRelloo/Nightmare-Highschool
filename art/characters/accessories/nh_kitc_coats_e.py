"""Kit C coats E (Kit C, "The Night School Wardrobe"): four short jackets.

  VarsityJacket   crimson wool, cream leather sleeves, a closed snap front, a flat ribbed knit collar, striped ribbed
                  cuffs and waistband, a chenille "N" on the left chest and NIGHTMARE arched across the back. Waist length.
  HuntingJacket   black-olive waxed canvas, a brown corduroy collar, brass press-studs and grommets, a quilted tartan
                  lining; a storm-flapped closed front opening into small revers; a short skirt to the hip (BodyFollow)
                  with big bellows game pockets.
  SmokingJacket   crimson quilted velvet, a black satin shawl collar and turn-back cuffs, a frog at the break, a black
                  satin sash tied at the waist whose two tasselled tails sway (Tails); a short skirt to the hip.
  CrimsonSpencer  a cropped fitted crimson velvet spencer (hem z -0.30), puffed sleeve heads, black braid on every edge
                  and brandebourg loops across the front, a small fall collar.

Every body is the Kit C shell (nh_acc_batchc1: the wide neckline xo_top 0.72, the back scooped to nape_z 0.78, the
collar lying low; hair-friendly), varied here: a closed front (P "xo": the front edge x(z), a U neckline down to
P "neck_z"), a hem above Kit A's (P "hem"), and a body that stops above a knit waistband (P "body_bot"). The katana's
guard keeps the side-front cutaway (x <= 0.74 below z -0.26) on every jacket.
Layers (the checker doesn't test one item's pieces against each other): the shell mid-surface 0.024 off the torso,
0.016 thick; plackets, lapels, collars, patches and lettering lie on its outer face (0.032) with clearance; the sash is
outside the shell (mid 0.040 front, 0.024 under the arm); the skirt starts just below the hem (c1).
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- VarsityJacket --nobake --out E:/NH-Work/kitc_coats_e
"""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import ccw
from nh_acc_batch4 import wire, axis_frame, place, arm_wrap, mirror_piece
import nh_acc_batch7 as K7
from nh_acc_batch7 import cloth, out_hint_torso, sleeve_hint, D_F, T_SHELL, T_BAND
import nh_acc_batchc1 as C1

R_OUT = D_F + T_SHELL / 2      # the shell's outer face off the torso (0.032)


# ================================================================== materials
def mat_knit(name, rgb, period=0.034, depth=0.40, rough=0.92, sheen=0.55):
    """a rib knit: vertical ribs (a wave on x + y, so they run up the front, back and sides alike), the knit's
    stitches as a fine noise along them"""
    m, T, bs = A._base(name)
    k = 0.628 / period
    tc = T.node("ShaderNodeTexCoord")
    mp = T.node("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (k, k, 0.0)
    T.L(tc.outputs["Object"], mp.inputs["Vector"])
    wv = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL")
    wv.inputs["Scale"].default_value = 1.0; wv.inputs["Distortion"].default_value = 0.0; wv.inputs["Detail"].default_value = 0.0
    T.L(mp.outputs["Vector"], wv.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 5
    T.L(T.coord((k * 0.25, k * 0.25, k * 0.5)), nz.inputs["Vector"])
    h = T.math("ADD", wv.outputs["Fac"], T.math("MULTIPLY", nz.outputs["Fac"], 0.3))
    col = T.mix(T.math("MULTIPLY", T.math("SUBTRACT", 1.0, wv.outputs["Fac"]), depth), A._rgb(T, rgb), (0, 0, 0), "MULTIPLY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.006
    T.L(h, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = sheen; bs.inputs["Sheen Roughness"].default_value = 0.5
    A._weather(T, bs, col, A._val(T, rough), A._val(T, 0.0), bp.outputs["Normal"], 0.08, False, 0.4, 0.005)
    return m


def _quilt(T, period):
    """diamond quilting: pillows between two sets of stitch lines at 45 degrees (on x + y +- z, so the diamonds sit
    square on the front, back and sides); returns the pillow height (0 on the stitches, 1 mid-pillow)"""
    k = 1.0 / (period * math.sqrt(2.0))
    tc = T.node("ShaderNodeTexCoord")
    sp = T.node("ShaderNodeSeparateXYZ"); T.L(tc.outputs["Object"], sp.inputs["Vector"])
    xy = T.math("ADD", sp.outputs["X"], sp.outputs["Y"])

    def tri(s):
        return T.math("SINE", T.math("MULTIPLY", T.math("FRACT", T.math("MULTIPLY", s, k)), math.pi))
    return T.math("MULTIPLY", tri(T.math("ADD", xy, sp.outputs["Z"])), tri(T.math("SUBTRACT", xy, sp.outputs["Z"])))


def mat_quilt_velvet(name, rgb, period=0.13, rough=0.68):
    """velvet (crushed pile, strong sheen) quilted in diamonds: the stitch lines sunk and darker"""
    m, T, bs = A._base(name)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 4
    nz.inputs["Distortion"].default_value = 1.4
    T.L(T.coord(5.0), nz.inputs["Vector"])
    fine = T.node("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 1.0; fine.inputs["Detail"].default_value = 12
    T.L(T.coord(300.0), fine.inputs["Vector"])
    puff = _quilt(T, period)
    pillow = T.math("POWER", T.math("MAXIMUM", puff, 0.0), 0.45)
    col = T.mix(T.math("MULTIPLY", nz.outputs["Fac"], 0.55), A._rgb(T, rgb), tuple(c * 1.9 for c in rgb), "MIX")
    col = T.mix(T.math("MULTIPLY", T.math("SUBTRACT", 1.0, pillow), 0.75), col, (0, 0, 0), "MULTIPLY")
    b1 = T.node("ShaderNodeBump"); b1.inputs["Strength"].default_value = 0.08
    T.L(T.math("ADD", nz.outputs["Fac"], T.math("MULTIPLY", fine.outputs["Fac"], 0.3)), b1.inputs["Height"])
    b2 = T.node("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.55; b2.inputs["Distance"].default_value = 0.012
    T.L(pillow, b2.inputs["Height"]); T.L(b1.outputs["Normal"], b2.inputs["Normal"])
    bs.inputs["Sheen Weight"].default_value = 1.0
    bs.inputs["Sheen Tint"].default_value = (*[min(1, c * 3 + 0.2) for c in rgb], 1)
    A._weather(T, bs, col, A._val(T, rough), A._val(T, 0.0), b2.outputs["Normal"], 0.1, False, 0.4, 0.006)
    return m


def mat_tartan(name, period=0.16):
    """a quilted tartan lining: dark green ground, navy and red bands and a thin ochre line, set both ways"""
    m, T, bs = A._base(name)
    tc = T.node("ShaderNodeTexCoord")
    sp = T.node("ShaderNodeSeparateXYZ"); T.L(tc.outputs["Object"], sp.inputs["Vector"])
    col = A._rgb(T, (0.020, 0.060, 0.032))
    for axis in ("X", "Z"):
        fr = T.math("FRACT", T.math("DIVIDE", T.math("ADD", sp.outputs[axis], sp.outputs["Y"] if axis == "X" else 0.0), period))
        for lo, hi, c, a in ((0.00, 0.30, (0.012, 0.018, 0.060), 0.55), (0.55, 0.62, (0.30, 0.025, 0.035), 0.75),
                             (0.80, 0.82, (0.55, 0.40, 0.08), 0.8)):
            band = T.math("MULTIPLY", T.math("GREATER_THAN", fr, lo), T.math("LESS_THAN", fr, hi))
            col = T.mix(T.math("MULTIPLY", band, a), col, c, "MIX")
    puff = _quilt(T, 0.09)
    pillow = T.math("POWER", T.math("MAXIMUM", puff, 0.0), 0.5)
    col = T.mix(T.math("MULTIPLY", T.math("SUBTRACT", 1.0, pillow), 0.5), col, (0, 0, 0), "MULTIPLY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.inputs["Distance"].default_value = 0.008
    T.L(pillow, bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 0.3
    A._weather(T, bs, col, A._val(T, 0.6), A._val(T, 0.0), bp.outputs["Normal"], 0.05, False, 0.4, 0.005)
    return m


def mat_waxed(name, rgb):
    """waxed cotton canvas: a fine plain weave, a slight gloss, creases (the wax cracked paler and duller along them)"""
    m, T, bs = A._base(name)
    mp = T.coord(320.0)
    wa = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wa.inputs["Scale"].default_value = 1.0; wa.inputs["Distortion"].default_value = 0.4
    T.L(mp, wa.inputs["Vector"])
    wb = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
    wb.inputs["Scale"].default_value = 1.0; wb.inputs["Distortion"].default_value = 0.4
    T.L(mp, wb.inputs["Vector"])
    weave = T.math("MAXIMUM", wa.outputs["Fac"], T.math("MULTIPLY", wb.outputs["Fac"], 0.7))
    cr = T.node("ShaderNodeTexNoise"); cr.inputs["Scale"].default_value = 1.0; cr.inputs["Detail"].default_value = 3
    cr.inputs["Distortion"].default_value = 2.2
    T.L(T.coord((3.2, 3.2, 1.6)), cr.inputs["Vector"])
    crease = T.math("MULTIPLY", T.math("SUBTRACT", 0.035, T.math("ABSOLUTE", T.math("SUBTRACT", cr.outputs["Fac"], 0.5))),
                    28.0, clamp=True)
    blot = T.node("ShaderNodeTexNoise"); blot.inputs["Scale"].default_value = 1.0; blot.inputs["Detail"].default_value = 6
    T.L(T.coord(9.0), blot.inputs["Vector"])
    col = T.mix(0.06, A._rgb(T, rgb), blot.outputs["Color"], "OVERLAY")
    col = T.mix(T.math("MULTIPLY", crease, 0.16), col, tuple(min(1, c * 1.7 + 0.012) for c in rgb), "MIX")
    col = T.mix(T.math("MULTIPLY", weave, 0.12), col, (0, 0, 0), "MULTIPLY")
    r = T.math("ADD", 0.36, T.math("ADD", T.math("MULTIPLY", crease, 0.30), T.math("MULTIPLY", blot.outputs["Fac"], 0.12)))
    b1 = T.node("ShaderNodeBump"); b1.inputs["Strength"].default_value = 0.08; b1.inputs["Distance"].default_value = 0.003
    T.L(weave, b1.inputs["Height"])
    b2 = T.node("ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.16; b2.inputs["Distance"].default_value = 0.010
    T.L(T.math("SUBTRACT", 1.0, crease), b2.inputs["Height"]); T.L(b1.outputs["Normal"], b2.inputs["Normal"])
    bs.inputs["Sheen Weight"].default_value = 0.15
    A._weather(T, bs, col, r, A._val(T, 0.0), b2.outputs["Normal"], 0.25, False, 0.55, 0.006)
    return m


def mat_chenille(name, rgb):
    """chenille: a deep looped pile, fuzzy and soft-sheened"""
    m, T, bs = A._base(name)
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 6
    nz.inputs["Distortion"].default_value = 0.8
    T.L(T.coord(160.0), nz.inputs["Vector"])
    lo = T.node("ShaderNodeTexNoise"); lo.inputs["Scale"].default_value = 1.0; lo.inputs["Detail"].default_value = 3
    T.L(T.coord(18.0), lo.inputs["Vector"])
    col = T.mix(T.math("MULTIPLY", T.math("SUBTRACT", 1.0, nz.outputs["Fac"]), 0.45), A._rgb(T, rgb), (0, 0, 0), "MULTIPLY")
    col = T.mix(0.15, col, lo.outputs["Color"], "OVERLAY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.85; bp.inputs["Distance"].default_value = 0.010
    T.L(nz.outputs["Fac"], bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = 1.0; bs.inputs["Sheen Roughness"].default_value = 0.35
    A._weather(T, bs, col, A._val(T, 0.96), A._val(T, 0.0), bp.outputs["Normal"], 0.0, False, 0.3, 0.004)
    return m


def satin(name, rgb):
    return A.mat_cloth(name, rgb, weave=760, rough=0.20, sheen=0.35, bump=0.02, twill=False, vary=0.04, wear=0.05)


def braid_mat(name, rgb=(0.016, 0.015, 0.018)):
    return A.mat_cloth(name, rgb, weave=1100, rough=0.55, sheen=0.5, bump=0.25, twill=True, vary=0.05, wear=0.05)


# ================================================================== small helpers
def paint(ob, fn):
    """material per face from fn(face centre) (None keeps it); parts are built in world space"""
    names = [m.name for m in ob.data.materials]
    for p in ob.data.polygons:
        m = fn(p.center)
        if m is None:
            continue
        if m.name not in names:
            ob.data.materials.append(m)
            names.append(m.name)
        p.material_index = names.index(m.name)
    return ob


def stripes(bands, default=None):
    """bands = [(z0, z1, mat)]: the material of the band a face centre's z falls in"""
    def fn(c):
        for z0, z1, m in bands:
            if z0 <= c.z < z1:
                return m
        return default
    return fn


def resample(pts, n):
    """pts = [(point, normal)] -> n evenly spaced along the polyline (normals interpolated)"""
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b[0] - a[0]).length)
    out, k = [], 0
    for i in range(n):
        s = L[-1] * i / (n - 1)
        while k < len(L) - 2 and L[k + 1] < s:
            k += 1
        f = (s - L[k]) / max(1e-9, L[k + 1] - L[k])
        out.append((pts[k][0].lerp(pts[k + 1][0], f), pts[k][1].lerp(pts[k + 1][1], f).normalized()))
    return out


def framed(pts):
    """[(B, N)] -> [(B, T, N, O)]: T along the path, N the surface normal made square to it, O = T x N (in the
    surface, away from the neck opening for the left half's path)"""
    out = []
    for i, (B, N) in enumerate(pts):
        a = pts[max(0, i - 1)][0]; b = pts[min(len(pts) - 1, i + 1)][0]
        T = (b - a).normalized()
        N = (N - T * T.dot(N)).normalized()
        out.append((B, T, N, T.cross(N).normalized()))
    return out


def snap(name, at, nrm, X, r=0.026):
    """a domed press-stud: a rolled rim and a dome (light: there are many)"""
    place(A.lathe(name, [(0.0, 0.0175), (r * 0.55, 0.0160), (r * 0.80, 0.0120), (r * 1.0, 0.0050), (r * 0.96, 0.0), (0.0, 0.0)],
                  (0, 0, 0), X["silver"], seg=8), axis_frame(at, nrm))


def eyelet(name, at, nrm, mat, R=0.012, r=0.0042):
    ob = A.torus(name, R, r, (0, 0, 0), mat, major=12, minor=5)
    place(ob, axis_frame(at, nrm))


# ================================================================== the shell (a Kit C shell variant)
TOP_Y_E = [-0.5, -0.375, -0.25, -0.125, 0.0, 0.125, 0.25, 0.375, 0.5]
ARC_E = [30, 60]
FRONT_Z_E = sorted(set(K7.FRONT_Z + [0.30, 0.52]))


def u_neck(zn, p, xt):
    """a closed front's U neckline: x 0 (the closure) below zn, out to xt at the shoulder top (z 1.0) with a finite
    slope there"""
    def xo(z):
        if z <= zn:
            return 0.003
        return max(0.003, xt * ((z - zn) / (1.0 - zn)) ** p)
    return xo


def u_rows(zn, p, n=6):
    return [zn + (1.0 - zn) * (k / n) ** (1.0 / p) for k in range(1, n)]


def front_x(z, P):
    return P["xo"](z) if "xo" in P else K7.lapel_line(z, P)


def shell_rows_e(P):
    """the Kit C shell's rows (c1.shell_rows_k) with the front edge P "xo", a hem/body bottom P "body_bot" and a
    denser shoulder top"""
    d = D_F
    zb = P.get("body_bot", P.get("hem", -0.72))
    fz = sorted(set([zb] + [z for z in FRONT_Z_E + P.get("front_extra", []) if zb + 0.012 < z <= 1.0]))
    rn = math.hypot(P["xo_top"], 0.5 + d)

    def tx(y):
        return math.sqrt(max(0.0, rn * rn - y * y))
    rows = [(-(0.5 + d), z, "front", front_x(z, P), K7.cut_line(z)) for z in fz]
    for a in ARC_E:
        y = -0.5 - d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", tx(y), 1.0))
    for y in TOP_Y_E:
        rows.append((y, 1.0 + d, "top", tx(y), 1.0))
    for a in ARC_E[::-1]:
        y = 0.5 + d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, "top", tx(y), 1.0))
    for z in [z for z in C1.BACK_Z_K if z > zb + 0.012] + [zb]:
        rows.append((0.5 + d, z, "back", C1.back_neck(z, P), 1.0))
    return rows


def shell_grid_e(side, P, ncol=9):
    rows = shell_rows_e(P)
    G = []
    for i in range(ncol + 1):
        col = []
        for (y, z, reg, xs, xe) in rows:
            x = lerp(xs, xe, i / ncol)
            yy = y + (K7.back_fold(x, z, P) if reg == "back" and P.get("back_folds") else 0.0)
            col.append(Vector((side * x, yy, z)))
        G.append(col)
    return G, rows


def band_grid_e(side, zb, ncol=10):
    zs = [z for z in K7.BAND_Z if z > zb + 0.012] + [zb]
    zs = sorted(set(zs))
    G = [[None] * len(zs) for _ in range(ncol + 1)]
    for j, z in enumerate(zs):
        at = K7.band_path(z)
        for i in range(ncol + 1):
            p = at(0.5 - 0.5 * math.cos(math.pi * i / ncol))
            G[i][j] = Vector((side * p.x, p.y, z))
    return G


def build_shell_e(name, P, X, collar=None):
    """both halves of the shell, the bands under the arms, seams, the edge trims P asks for, and the collar
    (collar(name, G, rows, side) or None). Returns {side: (G, rows)}"""
    out_g = {}
    zb = P.get("body_bot", P.get("hem", -0.72))
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G, rows = shell_grid_e(side, P)
        out_g[side] = (G, rows)
        cloth(f"{name}Body{sd}", G, T_SHELL, X["wool"], out_hint_torso, mat_in=X["lining"])
        bd = cloth(f"{name}Band{sd}", band_grid_e(side, P.get("hem", -0.72)), T_BAND, X["wool"], out_hint_torso,
                   mat_in=X["lining"])
        if P.get("band_paint"):
            paint(bd, P["band_paint"])
        o = T_SHELL / 2 + 0.004
        nf = sum(1 for r in rows if r[2] == "front")
        fz = [r[1] for r in rows[:nf]]
        if P.get("trim_front_to") is not None:   # the front edge, hem up to a height (x nudged in: the halves' trims meet)
            e = [G[0][j] + Vector((side * 0.004, -o, 0)) for j in range(nf) if fz[j] <= P["trim_front_to"] + 1e-6]
            wire(f"{name}TrimFront{sd}", [tuple(p) for p in e], P["trim_r"], X["trim"], sides=6)
        if P.get("trim_hem", True):   # the front hem and up the cutaway into the side seam
            e = [G[i][0] for i in range(0 if P.get("trim_front_to") is None else 1, len(G))] + \
                [G[-1][j] for j in range(1, nf) if fz[j] <= -0.075]
            if P.get("trim_hem_x0") is not None:
                e = [p for p in e if abs(p.x) >= P["trim_hem_x0"]]
            wire(f"{name}TrimHem{sd}", [tuple(p + Vector((0, -o, 0))) for p in e], P["trim_r"], X["trim"], sides=6)
        if P.get("trim_back", True):
            jh = len(rows) - 1
            wire(f"{name}TrimBack{sd}", [tuple(G[i][jh] + Vector((0, o + 0.002, 0))) for i in range(len(G))], P["trim_r"],
                 X["trim"], sides=6)
        top = [r for r in rows if r[2] == "top"]
        ys = top[min(range(len(top)), key=lambda k: abs(top[k][0]))]
        wire(f"{name}SeamShoulder{sd}", [(side * lerp(ys[3], 1.0, t), ys[0], ys[1] + o + 0.001) for t in (0.10, 0.5, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSide{sd}", [(side * (1.0 + 0.002), -(0.5 + D_F + o - 0.004), z) for z in (-0.06, 0.4, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSideB{sd}", [(side * (1.0 + 0.002), 0.5 + D_F + o - 0.004, z) for z in (zb + 0.02, 0.2, 0.97)],
             0.0035, X["thread"], sides=4)
        if collar is not None:
            collar(f"{name}Collar{sd}", G, rows, side)
    zn = P.get("nape_z", 0.78)
    wire(f"{name}SeamBack", [(0, 0.5 + R_OUT + 0.001, z) for z in (zb + 0.02, (zb + zn) / 2, zn - 0.10)], 0.004,
         X["thread"], sides=4)
    return out_g


def front_pt(x, z, lift=0.0):
    return Vector((x, -(0.5 + R_OUT + lift), z))


def back_pt(x, z, lift=0.0):
    return Vector((x, 0.5 + R_OUT + lift, z))


# ================================================================== collars
def neck_path(P, n=40):
    """the left half's neckline on the shell's outer face, centre front (the U of a closed front) round the shoulder
    top to the centre back (the scooped back): [(B, T, N, O)]"""
    d, R = D_F, R_OUT
    xt = P["xo_top"]; rn = math.hypot(xt, 0.5 + d)
    zn, p = P["neck_z"], P["neck_p"]
    pts = []
    for k in range(61):
        t = k / 60
        z = zn + (1 - zn) * t ** (1 / p)
        pts.append((Vector((max(0.003, xt * t), -(0.5 + R), z)), Vector((0, -1, 0))))
    for k in range(1, 9):
        a = math.radians(90 * k / 8)
        ym = 0.5 + d * math.cos(a)
        nrm = Vector((0, -math.cos(a), math.sin(a)))
        pts.append((Vector((math.sqrt(rn * rn - ym * ym), -0.5, 1.0)) + nrm * R, nrm))
    for k in range(1, 40):
        y = -0.5 + k / 40
        pts.append((Vector((math.sqrt(rn * rn - y * y), y, 1.0 + R)), Vector((0, 0, 1))))
    for k in range(8, -1, -1):
        a = math.radians(90 * k / 8)
        ym = 0.5 + d * math.cos(a)
        nrm = Vector((0, math.cos(a), math.sin(a)))
        pts.append((Vector((math.sqrt(rn * rn - ym * ym), 0.5, 1.0)) + nrm * R, nrm))
    zb = P.get("nape_z", 0.78)
    for k in range(1, 61):
        x = lerp(xt, 0.003, k / 60)
        s = (x / xt) ** 2
        lo, hi = 0.0, 1.0
        for _ in range(30):   # invert the smoothstep of c1.back_neck
            mid = (lo + hi) / 2
            if 3 * mid * mid - 2 * mid ** 3 < s:
                lo = mid
            else:
                hi = mid
        pts.append((Vector((x, 0.5 + R, lerp(zb, 1.0, (lo + hi) / 2))), Vector((0, 1, 0))))
    return framed(resample(pts, n))


def flat_collar(name, P, side, prof, thick, mat, paint_j=None, back_w=0.40):
    """a flat collar lying on the shell round the neckline: prof = [(u, v)] across it (u outward from the neck edge,
    v off the shell's outer face; v - thick/2 > 0 keeps it off the shell). paint_j(j) -> a material for the band
    between prof[j] and prof[j+1] (stripes)"""
    fr = neck_path(P)
    G = []
    for B, T, N, O in fr:
        # narrow down the scooped back (short hair ends at the nape there): back_w of the width, a little thinner
        f = smooth(0.30, 0.95, N.y)
        ku, kv = lerp(1.0, back_w, f), lerp(1.0, 0.85, f)
        G.append([Vector((side * q.x, q.y, q.z)) for q in [B + O * (u * ku) + N * max(v * kv, thick / 2 + 0.001)
                                                           for u, v in prof]])
    ob = cloth(name, G, thick, mat, out_hint_torso)
    if paint_j is not None:
        nu, nv = len(G) - 1, len(prof) - 1
        names = [m.name for m in ob.data.materials]
        for k, p in enumerate(ob.data.polygons):
            if k >= 2 * nu * nv:
                break
            m = paint_j((k // 2) % nv)
            if m is None:
                continue
            if m.name not in names:
                ob.data.materials.append(m); names.append(m.name)
            p.material_index = names.index(m.name)
    return G


def build_collar_e(name, G, rows, side, P, X, front_w=0.05):
    """c1.build_collar_k (the low rolled collar following the scooped back) with the collar's width at its front end
    (front_w) set by the jacket: a shawl's lapel narrows into it"""
    zn = P.get("nape_z", 0.78)
    j0 = next(j for j, r in enumerate(rows) if r[2] == "top")
    jz = [j for j, r in enumerate(rows) if r[2] == "back" and r[1] >= zn - 0.005]
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
        out = Vector((0, 1, 0))
        w = 1.0 if reg == "back" else (smooth(0.49, 0.524, y) if reg == "top" else 0.0)
        fr = smooth(0.0, 0.22, t)
        up = Vector((0, 0, 1))
        rad = Vector((b.x, b.y, 0)).normalized()
        S1 = b + up * (0.045 * fr + 0.008) + rad * 0.006
        C1_ = b + up * (rise * fr + 0.012) + rad * lerp(0.04, 0.06, w)
        F1 = b + up * lerp(rise * 0.75 * fr + 0.01, 0.030, w) + rad * lerp(reach * 0.62, 0.070, w)
        O1 = b + up * lerp(0.010, -P["collar_back"] * 0.6, w) + rad * lerp(reach * fr + front_w * (1 - fr), 0.040, w)
        q = smooth(0.99, 0.90, z) if reg == "back" else 0.0
        S2 = b + out * 0.007
        C2 = b + out * 0.016 + up * 0.012
        F2 = b + out * 0.020 + up * 0.004
        O2 = b + out * 0.012 - up * P["collar_back"]
        cols.append([b, S1.lerp(S2, q), C1_.lerp(C2, q), F1.lerp(F2, q), O1.lerp(O2, q)])

    def hint(p):
        return Vector((p.x, p.y, 0)).normalized() * 0.5 + Vector((0, 0, 0.9))
    cloth(name, cols, 0.012, X["collar"], hint, mat_in=X.get("collar_in"))
    wire(name + "Edge", [tuple(c[4]) for c in cols], P["pipe_r"] * 0.9, X["collar_pipe"], sides=5)


def build_lapel_e(name, side, P, X, shawl=False):
    """Kit A's lapel (nh_acc_batch7.build_lapel) with the fold's roll set in from the front edge (a closed front's
    two lapels meet at the break), and a shawl variant: no notch, a rounded outer edge, wide on the chest and
    narrowing over the shoulder into the collar"""
    zb = P["break"]
    lf = P.get("lapel_fn") or (lambda z: K7.lapel_line(z, P))
    y = -(0.5 + R_OUT + 0.0075)
    nz = 14
    rows_z = [zb + (0.99 - zb) * (k / nz) ** 0.9 for k in range(nz + 1)]
    nu = 6
    cols = []
    for i in range(nu + 1):
        u = i / nu
        col = []
        for z in rows_z:
            if shawl:
                zz = z
                W = P["lapel_w"] * smooth(zb - 0.02, zb + 0.40, z) * (1 - 0.72 * smooth(0.40, 0.99, z)) + 0.035
            else:
                zt = 0.99 - P["notch"] * u
                zz = lerp(zb, zt, (z - zb) / (0.99 - zb))
                W = P["lapel_w"] * smooth(zb - 0.05, zb + 0.55, zz) + 0.02
            x = lf(zz) + W * u
            col.append(Vector((side * x, y - 0.004 * u, zz)))
        cols.append(col)
    cloth(name, cols, 0.012, X["lapel"], lambda p: Vector((0, -1, 0)), mat_in=X["lapel_in"])
    rr = 0.008
    wire(name + "Roll", [(side * (lf(z) + rr + 0.001), y + 0.002, z) for z in rows_z], rr, X["lapel"], sides=6)
    wire(name + "Edge", [tuple(cols[-1][v] + Vector((0, -0.0065, 0))) for v in range(len(rows_z))] +
         [tuple(cols[i][-1] + Vector((0, -0.0065, 0))) for i in range(nu - 1, 0, -1)], P["pipe_r"] * 0.8, X["lapel_pipe"],
         sides=5)


# ================================================================== sleeves
def build_sleeve_e(name, X, zs, d_fn, puff=None, gathers=0.0, mat=None, paint_fn=None, hem=True, x_in=None):
    """the left sleeve (Kit A's, nh_acc_batch7.build_sleeve) from rows zs (cuff edge up to 1.0) at clearance
    d_fn(z), plus a puff: puff(z) more clearance, eased off toward the inner edges (the sleeve stays open and flush
    there) and gathered into pleats; the cap over the shoulder top rises with it"""
    kw = K7.wrap_kw()

    def prof(z):
        d = d_fn(z)
        a = arm_wrap(d, x_in=x_in if x_in is not None else C1.slv_xin(z), **kw)
        e = puff(z) if puff else 0.0
        if e <= 1e-5:
            return [Vector((1.5 + X_, Y_, z)) for X_, Y_ in a], [d] * len(a)
        b = arm_wrap(d + e, x_in=x_in if x_in is not None else C1.slv_xin(z), **kw)
        n = len(a)
        pts, ds = [], []
        for k in range(n):
            u = k / (n - 1)
            f = math.sin(math.pi * u) ** 0.5 * (1.0 + gathers * math.cos(math.pi * k))
            pts.append(Vector((1.5 + lerp(a[k][0], b[k][0], f), lerp(a[k][1], b[k][1], f), z)))
            ds.append(d + e * f)
        return pts, ds
    rowsP = [prof(z)[0] for z in zs]
    top, dk = prof(1.0)
    E0 = arm_wrap(0.0, x_in=x_in if x_in is not None else C1.SLV_XIN, **kw)
    n = len(E0)
    for a in (35, 70):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rowsP.append([Vector((1.5 + E0[k][0] + (top[k].x - 1.5 - E0[k][0]) * c, E0[k][1] + (top[k].y - E0[k][1]) * c,
                              1.0 + dk[k] * s_)) for k in range(n)])
    T = [((x_in if x_in is not None else C1.SLV_XIN) + 0.01, lerp(-0.40, 0.40, k / (n - 1))) for k in range(n)]
    d_in = d_fn(1.0)
    for f in (0.0, 0.3, 0.6, 1.0):
        rowsP.append([Vector((1.5 + lerp(E0[k][0], T[k][0], f), lerp(E0[k][1], T[k][1], f),
                              1.0 + lerp(dk[k], d_in, f ** 1.3))) for k in range(n)])
    G = [[rowsP[j][k] for j in range(len(rowsP))] for k in range(n)]
    ob = cloth(name + "Body", G, 0.014, mat or X["wool"], sleeve_hint, mat_in=X["lining"])
    if paint_fn:
        paint(ob, paint_fn)
    if hem:
        wire(name + "Hem", [tuple(c[0] + (c[0] - Vector((1.5, 0, c[0].z))).normalized() * 0.006) for c in G], 0.0075,
             mat or X["wool"], sides=5)
    seam = [Vector((1.5 + 0.10, 0.5 + d_fn(z) + 0.0085, z)) for z in (zs[0] + 0.02, -0.2, 0.3)]
    if not puff:
        seam.append(Vector((1.5 + 0.10, 0.5 + d_fn(0.8) + 0.0085, 0.8)))
    wire(name + "Seam", [tuple(p) for p in seam], 0.0032, X["thread"], sides=4)
    return G


def ring_at(z, d, x_in=None):
    """points round the left arm at clearance d (the sleeve's U)"""
    return [Vector((1.5 + X_, Y_, z)) for X_, Y_ in arm_wrap(d, x_in=C1.slv_xin(z) if x_in is None else x_in, **K7.wrap_kw())]


def arm_band(name, z0, z1, d0, d1, mat, thick=0.012, nz=3, paint_fn=None):
    """a band round the left arm from z0 (bottom) to z1, mid-surface clearance d0 -> d1"""
    zs = [lerp(z0, z1, j / nz) for j in range(nz + 1)]
    rows = [ring_at(z, lerp(d0, d1, j / nz)) for j, z in enumerate(zs)]
    G = [[rows[j][k] for j in range(len(rows))] for k in range(len(rows[0]))]
    ob = cloth(name, G, thick, mat, sleeve_hint)
    if paint_fn:
        paint(ob, paint_fn)
    return G


# ================================================================== the sash (smoking jacket)
def girdle_path(z, of=0.040, os_=0.024):
    """the plan path (x >= 0) round the torso at height z outside the shell: the front (y -(0.5+of)) from the centre,
    a rounded corner, the side under the arm (x 1+os_), the back corner, the back to the centre"""
    rx, ry = 0.08 + os_, 0.06 + of
    pts = [Vector((lerp(0.0, 0.92, k / 8), -(0.5 + of), z)) for k in range(9)]
    for k in range(1, 6):
        a = math.radians(-90 + 18 * k)
        pts.append(Vector((0.92 + rx * math.cos(a), -0.44 + ry * math.sin(a), z)))
    for k in range(1, 7):
        pts.append(Vector((1.0 + os_, lerp(-0.44, 0.44, k / 7), z)))
    for k in range(0, 5):
        a = math.radians(18 * k)
        pts.append(Vector((0.92 + rx * math.cos(a), 0.44 + ry * math.sin(a), z)))
    pts += [Vector((lerp(0.92, 0.0, k / 8), 0.5 + of, z)) for k in range(9)]
    return pts


def tassel(name, top, X, r=0.026, L=0.085, n=14):
    """a silk tassel hanging from `top`: a gilt bell-shaped head, a gold collar, a fringe of strands flaring a little,
    ragged at the ends"""
    top = Vector(top)
    A.lathe(name + "Head", [(0.0, 0.0), (r * 0.30, -0.002), (r * 0.62, -0.010), (r * 0.80, -0.022), (r * 0.74, -0.034),
                            (r * 0.62, -0.040), (0.0, -0.040)], tuple(top), X["gold"], seg=12)
    A.torus(name + "Collar", r * 0.66, 0.0045, tuple(top + Vector((0, 0, -0.041))), X["gold"], major=12, minor=4)
    verts, faces = [], []
    levels = [(-0.040, r * 0.60), (-0.050, r * 0.66), (-0.040 - L * 0.55, r * 0.80), (-0.040 - L, r * 0.92)]
    m = 2 * n
    for li, (h, rr) in enumerate(levels):
        for k in range(m):
            a = 2 * math.pi * k / m
            q = rr * (1.0 if k % 2 == 0 else 0.84)
            dz = (0.008 * math.sin(k * 2.3) if li == len(levels) - 1 else 0.0)
            verts.append(top + Vector((q * math.cos(a), q * math.sin(a), h + dz)))
    for li in range(len(levels) - 1):
        for k in range(m):
            k2 = (k + 1) % m
            faces.append([li * m + k, li * m + k2, (li + 1) * m + k2, (li + 1) * m + k])
    c = len(verts)
    verts.append(top + Vector((0, 0, -0.040 - L * 0.9)))
    last = (len(levels) - 1) * m
    for k in range(m):
        faces.append([last + (k + 1) % m, last + k, c])
    ob = A.mesh_from(name + "Fringe", verts, faces, X["fringe"])
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()


def frog(name, at_z, X, half=0.13, mat=None, r=0.0042, x0=0.02, toggle_lift=0.010, n_tre=36, sides=5):
    """a frog / brandebourg across the closure at z: a cord bar each side ending in a trefoil of loops, a toggle at
    the centre"""
    mat = mat or X["trim"]
    lift = r + 0.0012
    for s in (1, -1):
        pts = [(s * lerp(x0, half - 0.03, k / 3), at_z) for k in range(4)]
        for k in range(1, n_tre + 1):
            a = 2 * math.pi * k / n_tre
            rr = 0.018 + 0.014 * math.cos(3 * a)
            pts.append((s * (half - rr * math.cos(a)), at_z - rr * math.sin(a)))
        wire(f"{name}{'L' if s > 0 else 'R'}", [tuple(front_pt(x, z, lift)) for x, z in pts], r, mat, sides=sides)
    A.sphere(name + "Toggle", 0.016, tuple(front_pt(0.0, at_z, toggle_lift)), mat, scale=(1.0, 0.55, 0.75), seg=10, rings=6)


# ================================================================== covering the torso: the inner layer and the hip sides
# The owner: the jackets cover the torso. Two more pieces per jacket:
#   <Key>Inner  Torso, rigid (the smoking jacket's carries its sash, rigged): what's worn under the jacket where the
#               shell leaves the torso bare: the neck opening, the shoulder tops inside the wide neckline and the scooped
#               back (a yoke), an open front (a shirt front / jumper), a cropped hem (a bodice). Mid-surface D_I off the
#               torso, T_I thick: under the shell's inner face (0.016). It shares the shell's depth fit (fit_same), so
#               the two layers keep their order on every body. The yoke on the shoulder tops keeps it resting.
#   <Key>Side   Torso, rigid: the hips' front corners (x 0.68..1.0 below the shell's katana cutaway), hugging the
#               torso at the same low offset with a depth fit of its own (fitted only where it lies): the sheathed
#               katana's guard sits just in front (its back face at y -0.605..-0.66 there), so the shell's larger fit
#               (set by the chest) would push the cloth into it on the deep bodies. It tucks under the shell's cut edge.
D_I, T_I = 0.008, 0.008
FIT_SAME = {}      # piece name -> the piece whose depth fit it shares
_fit_seen = {}
_fit_prev = A.fit_table


HUG_FIT = set()    # pieces fitted closely: their own fit without Kit A's 0.8 floor (the slim bodies' waists)
LEG_HEM = {}       # hugging piece -> its front hem's height: also clear of a leg striding forward 55 degrees (its top
                   # front corner comes out of the torso there on the bodies whose legs are deeper than the belly)


def hug_fit(obj):
    """as nh_acc.fit_table, for a layer lying right on the torso: s = max (D_body + 0.004) / |y| over its vertices,
    floor 0.6 (the lean and petite waists are 0.35 deep: at 0.8 a hugging band would hover 0.05 off them)"""
    import random
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    contact = [p for p in pts if abs(p.x) <= 0.98 and abs(p.y) > 0.3 and abs(p.y) - 0.5 < 0.03]
    random.seed(7)
    if len(contact) > 400:
        contact = random.sample(contact, 400)
    out = {}
    for bid in A.BODY_IDS:
        if bid == "standard":
            continue
        need = 0.0
        for p in contact:
            d = A.body_depth(bid, "Torso", p.x, p.z, -1 if p.y < 0 else 1)
            if d is not None:
                need = max(need, (d + 0.003) / abs(p.y))
        if obj.name in LEG_HEM:
            ld = A.body_depth(bid, "LeftLeg", 0.0, 0.9, -1) or 0.5
            a = math.radians(55)
            ly = (ld - (LEG_HEM[obj.name] + 1.0) * math.sin(a)) / math.cos(a)
            need = max(need, (ly + 0.006) / (0.5 + D_I - T_I / 2))
        out[bid] = round(min(1.45, max(0.6, need)), 3) if need > 0 else 1.0
    return out


def full_fit(obj, fit):
    """nh_acc.fit_table samples 400 of a piece's contact vertices, and can miss the deepest point of a body (a curvy
    back, a muscular chest): raise each body's fit to cover every contact vertex (fit_table's clearances)"""
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    contact = {}
    for p in pts:
        if abs(p.x) > 0.98 or abs(p.z) > 0.98 or abs(p.y) < 0.05 or abs(p.y) - 0.5 >= 0.12:
            continue
        k = (round(p.x, 2), round(p.z, 2), p.y > 0)   # one per 0.01 cell: the innermost
        if k not in contact or abs(p.y) < abs(contact[k].y):
            contact[k] = p
    out = dict(fit)
    for bid in A.BODY_IDS:
        if bid == "standard":
            continue
        need = 0.0
        for p in contact.values():
            d = A.body_depth(bid, "Torso", p.x, p.z, 1 if p.y > 0 else -1)
            if d is not None:
                need = max(need, (d + max(0.004, min(abs(p.y) - 0.5, 0.02))) / abs(p.y))
        if need > out.get(bid, 1.0):
            out[bid] = round(min(1.45, need + 0.001), 3)
    return out


def _fit_table_e(obj, mount):
    if obj.name in HUG_FIT:
        r = hug_fit(obj)
        _fit_seen[obj.name] = r
        return r
    src = FIT_SAME.get(obj.name)
    if src is not None:
        if src not in _fit_seen:
            _fit_table_e(bpy.data.objects[src], mount)
        return dict(_fit_seen[src])
    r = _fit_prev(obj, mount)
    if mount == "Torso" and not obj.name.endswith("Skirt") and obj.name.startswith(E_KEYS):
        r = full_fit(obj, r)
    _fit_seen[obj.name] = r
    return r


E_KEYS = ("VarsityJacket", "HuntingJacket", "SmokingJacket", "CrimsonSpencer")


A.fit_table = _fit_table_e


def crew(zc, xt):
    """a crew neckline on the inner layer: x 0 below zc, out to xt at the shoulder top"""
    def xo(z):
        return 0.003 if z <= zc else max(0.003, xt * ((z - zc) / (1.0 - zc)) ** 0.5)
    return xo


def inner_yoke(name, X, mat, zc_f=0.84, zc_b=0.84, ri=0.66, front_bot=0.55, back_bot=0.62, x_front=0.80, binding=None,
               front_paint=None):
    """the inner layer round the neck: the front from front_bot up to a crew neckline, over the shoulder tops (inside the
    shell's wide neckline, out under it) and down the back to back_bot. Returns {side: G}"""
    d = D_I
    xt = math.sqrt(ri * ri - (0.5 + d) ** 2)
    xf, xb = crew(zc_f, xt), crew(zc_b, xt)
    fz = sorted(set([front_bot] + [z for z in FRONT_Z_E if front_bot + 0.02 < z <= 1.0] + u_rows(zc_f, 0.5) +
                    [zc_f, (front_bot + 1.0) / 2]))
    bz = sorted(set([back_bot] + [z for z in C1.BACK_Z_K if back_bot + 0.02 < z <= 1.0] + u_rows(zc_b, 0.5) + [zc_b]),
                reverse=True)
    rows = [(-(0.5 + d), z, xf(z), x_front) for z in fz]

    def tx(y):
        return math.sqrt(max(0.0, ri * ri - y * y))
    for a in ARC_E:
        y = -0.5 - d * math.cos(math.radians(a)); rows.append((y, 1.0 + d * math.sin(math.radians(a)), tx(y), 0.95))
    for y in TOP_Y_E:
        rows.append((y, 1.0 + d, tx(y), 0.95))
    for a in ARC_E[::-1]:
        y = 0.5 + d * math.cos(math.radians(a)); rows.append((y, 1.0 + d * math.sin(math.radians(a)), tx(y), 0.95))
    rows += [(0.5 + d, z, xb(z), x_front) for z in bz]
    out = {}
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G = [[Vector((side * lerp(xs, xe, i / 7), y, z)) for (y, z, xs, xe) in rows] for i in range(8)]
        ob = cloth(f"{name}Yoke{sd}", G, T_I, mat, out_hint_torso)
        if front_paint:
            paint(ob, front_paint)
        if binding is not None:   # the neckline's binding
            e = []
            for j, (y, z, xs, xe) in enumerate(rows):
                p = G[0][j]
                if xs <= 0.0031 and abs(y) > 0.5 and z < max(zc_f, zc_b) - 0.001:
                    continue
                n = Vector((0, -1, 0)) if (y < -0.5 and z < 1.0) else (Vector((0, 1, 0)) if (y > 0.5 and z < 1.0) else Vector((0, 0, 1)))
                e.append(p + n * (T_I / 2 + 0.0035))
            wire(f"{name}Neck{sd}", [tuple(p) for p in e], 0.0045, binding, sides=5)
        out[side] = G
    return out


def inv_cut(x):
    """the height where the shell's cutaway edge (nh_acc_batch7.cut_line) reaches x (x 0.74..1.0)"""
    if x <= 0.74:
        return -0.26
    c = 1.0 - min(1.0, (x - 0.74) / 0.26)
    return -0.26 + 0.18 * math.sin(math.acos(c))


def side_band(name, mat, z0, z1, x0, mid=lambda x: 0.0045, t=0.005, paint_fn=None, top_cut=False):
    HUG_FIT.add(name)
    """one band (z0..z1) of the hips' front corners: from x0 round the torso's vertical corner onto the side (to
    y -0.46, where the shell's band under the arm begins); mid(x) its mid-surface off the torso; top_cut: the top
    follows the shell's cutaway edge (tucked 0.025 under it)"""
    plan = [(x, None) for x in sorted(set([lerp(x0, 1.0, k / 10) for k in range(11)] + [x for x in (0.770, 0.786) if x > x0 + 0.01]))]
    pts = [(x, -(0.5 + mid(x))) for x, _ in plan]
    d = mid(1.0)
    for k in range(1, 4):
        a = math.radians(-90 + 90 * k / 3)
        pts.append((1.0 + d * math.cos(a), -0.5 + d * math.sin(a)))
    pts += [(1.0 + d, -0.48), (1.0 + d, -0.46)]
    nz = 6 if top_cut else 4
    for side in (1, -1):
        G = []
        for x, y in pts:
            zt = min(inv_cut(min(x, 1.0)) + 0.025, -0.095) if top_cut else z1
            zb = z0(abs(x)) if callable(z0) else z0
            G.append([Vector((side * x, y, lerp(zb, zt, j / nz))) for j in range(nz + 1)])
        ob = cloth(f"{name}{'L' if side > 0 else 'R'}", G, t, mat, out_hint_torso)
        if paint_fn:
            paint(ob, paint_fn)


SIDE_ZB, SIDE_Z1, SIDE_Z2 = -0.68, -0.44, -0.28


def build_side(key, mat, paint_fn=None, zb=lambda x: SIDE_ZB + 0.02 * smooth(0.80, 0.92, x), mid_x0=0.742):
    """the hips' front corners in three pieces, each hugging the torso with a depth fit of its own (the sheathed
    katana's guard sits just in front, back face y -0.605..-0.68; a flat panel's fit is set by the deepest body point it
    covers, and the heavy body is 0.608 deep at x 0.70): <key>SideLow (z -0.70..-0.46, tucked under the shell's rounded
    hem corner), <key>SideMid (-0.46..-0.255, the guard's tightest zone: from the shell's cut edge x 0.745, closest
    where the guard is), <key>SideTop (-0.255 up to the cutaway's edge, above the guard)"""
    piece(f"{key}SideLow", "Torso")
    side_band(f"{key}SideLow", mat, zb, SIDE_Z1, 0.70, paint_fn=paint_fn)
    piece(f"{key}SideMid", "Torso")
    side_band(f"{key}SideMid", mat, SIDE_Z1, SIDE_Z2, mid_x0, mid=lambda x: 0.003 + 0.017 * smooth(0.786, 0.770, x), t=0.002,
              paint_fn=paint_fn)
    piece(f"{key}SideTop", "Torso")
    side_band(f"{key}SideTop", mat, SIDE_Z2, -0.10, 0.70, paint_fn=paint_fn, top_cut=True)


def hug_sleeves(key, extra=None):
    ex = {f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}
    ex.update(extra or {})
    C1.write_extra(key, ex)


# ================================================================== the Varsity jacket
def varsity_mats(M):
    crim = (0.26, 0.022, 0.040)
    X = dict(
        wool=A.mat_cloth("VarsityMelton", crim, weave=420, rough=0.88, sheen=0.5, bump=0.05, twill=False, vary=0.06,
                         wear=0.15, dirt=0.4),
        lining=satin("VarsityLiningSatin", (0.02, 0.018, 0.022)),
        thread=A.mat_cloth("VarsityThread", (0.20, 0.02, 0.035), weave=900, rough=0.5, sheen=0.2, bump=0.05, twill=False),
        leather=A.mat_flat("VarsityCreamLeather", (0.74, 0.66, 0.50), rough=0.48, noise=180, bump=0.16, vary=0.05,
                           wear=0.2, dirt=0.55, sheen=0.1, coat=0.12),
        knit=mat_knit("VarsityKnitCrimson", crim), knit_cream=mat_knit("VarsityKnitCream", (0.74, 0.67, 0.52)),
        knit_black=mat_knit("VarsityKnitBlack", (0.018, 0.017, 0.02)),
        chenille=mat_chenille("VarsityChenilleCream", (0.76, 0.69, 0.54)),
        tee=A.mat_cloth("VarsityTee", (0.022, 0.021, 0.024), weave=650, rough=0.86, sheen=0.3, bump=0.05, twill=False),
        felt=A.mat_flat("VarsityBlackFelt", (0.02, 0.019, 0.022), rough=0.95, noise=320, bump=0.18, vary=0.05, wear=0.05,
                        sheen=0.3),
        silver=M["brass"], brass=M["brass"], bone=M["bone"])
    X.update(trim=X["leather"], pipe=X["wool"])
    return X


def varsity_params():
    P = dict(xo_top=0.72, nape_z=0.78, neck_z=0.70, neck_p=0.5, hem=-0.72, body_bot=-0.60, trim_r=0.0060,
             pipe_r=0.0055, back_folds=0.0)
    P["xo"] = u_neck(P["neck_z"], P["neck_p"], P["xo_top"])
    P["front_extra"] = u_rows(P["neck_z"], P["neck_p"])
    return P


WB = [(-0.73, -0.685, "knit"), (-0.685, -0.667, "knit_cream"), (-0.667, -0.649, "knit_black"),
      (-0.649, -0.631, "knit_cream"), (-0.631, -0.59, "knit")]   # the waistband's stripes (z bands)


def varsity_waistband(key, P, X):
    """the striped rib-knit waistband from the hem (z -0.72) up to the body (-0.60): the front (centre to the
    cutaway), the back, both sides; the bands under the arms are knit below -0.60 too"""
    zs = [-0.72, -0.70, -0.685, -0.667, -0.649, -0.631, -0.615, -0.60]
    fn = stripes([(a, b, X[m]) for a, b, m in WB])
    t = 0.019
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        Gf = [[Vector((side * lerp(0.003, K7.cut_line(z), i / 9), -(0.5 + D_F), z)) for z in zs] for i in range(10)]
        paint(cloth(f"{key}WaistF{sd}", Gf, t, X["knit"], out_hint_torso), fn)
        Gb = [[Vector((side * lerp(0.003, 1.0, i / 10), 0.5 + D_F, z)) for z in zs] for i in range(11)]
        paint(cloth(f"{key}WaistB{sd}", Gb, t, X["knit"], out_hint_torso), fn)
        # the seam where the knit meets the melton
        wire(f"{key}WaistSeamF{sd}", [tuple(Vector((side * lerp(0.05, 0.74, i / 8), -(0.5 + D_F + t / 2 + 0.002), -0.60)))
                                      for i in range(9)], 0.004, X["wool"], sides=5)
        wire(f"{key}WaistSeamB{sd}", [tuple(Vector((side * lerp(0.0, 1.0, i / 8), 0.5 + D_F + t / 2 + 0.002, -0.60)))
                                      for i in range(9)], 0.004, X["wool"], sides=5)


def letter(name, ch, size, mat, R, U, F, origin, surf, depth, bevel=0.0, font="dutcheb.ttf", grow=1.0):
    """one raised letter (A.text_mesh): reading along R, up U, facing F, centred at origin's (R, U) position, its
    back laid at `surf` (a distance along F from the torso's centre plane). Returns the front's distance along F"""
    Mr = Matrix((R, -F, U)).transposed().to_4x4()
    Mr.translation = Vector(origin)
    ob = A.text_mesh(name, ch, size, mat, Mr, font=font, depth=depth, bevel=bevel)
    if grow != 1.0:   # a felt border: the glyph grown in its own plane about its middle
        vs = [v.co for v in ob.data.vertices]
        c = sum(vs, Vector()) / len(vs)
        for v in ob.data.vertices:
            d = v.co - c
            v.co = c + R * (d.dot(R) * grow) + U * (d.dot(U) * grow) + F * d.dot(F)
    vs = [v.co for v in ob.data.vertices]
    lo = min(v.dot(F) for v in vs)
    hi = max(v.dot(F) for v in vs)
    ob.data.transform(Matrix.Translation(F * (surf - lo)))
    ob.data.update()
    return surf + (hi - lo)


def felt_letter(name, ch, size, R, U, F, origin, X, surf, grow=1.13):
    top = letter(name + "Felt", ch, size, X["felt"], R, U, F, origin, surf + 0.0008, 0.006, grow=grow)
    return letter(name + "Chen", ch, size, X["chenille"], R, U, F, origin, top + 0.0008, 0.011)


@item("VarsityJacket", "Varsity jacket", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.35, 0, 0.30), 85))
def build_varsity(M):
    key = "VarsityJacket"
    X, P = varsity_mats(M), varsity_params()
    piece(f"{key}Shell", "Torso")
    P["trim_hem_x0"] = 0.735   # the leather binding only up the cutaway (the waistband is the hem)
    P["trim_back"] = False
    P["band_paint"] = stripes([(a, b, X[m]) for a, b, m in WB])
    stripe_j = {2: X["knit_cream"], 3: X["knit_black"], 4: X["knit_cream"]}

    def collar(name, G, rows, side):
        prof = [(-0.006, 0.0125), (0.012, 0.0150), (0.044, 0.0111), (0.054, 0.0108), (0.064, 0.0106), (0.084, 0.0102)]
        flat_collar(name, P, side, prof, 0.017, X["knit"], paint_j=lambda j: stripe_j.get(j))
    build_shell_e(key, P, X, collar=collar)
    varsity_waistband(key, P, X)
    # the snap placket down the centre front: from the collar to the hem, over the waistband
    zt = P["neck_z"] - 0.10
    zp = [-0.72, -0.66, -0.60, -0.45, -0.25, 0.0, 0.25, 0.45, zt]
    tp = 0.010
    Gp = [[Vector((x, -(0.5 + D_F + 0.0095 + 0.002 + tp / 2), z)) for z in zp] for x in (-0.05, -0.025, 0.0, 0.025, 0.05)]
    cloth(f"{key}Placket", Gp, tp, X["wool"], lambda p: Vector((0, -1, 0)), mat_in=X["lining"])
    yp = -(0.5 + D_F + 0.0095 + 0.002 + tp)
    for s in (-1, 1):
        wire(f"{key}PlacketStitch{s}", [(s * 0.040, yp - 0.0015, z) for z in (-0.715, -0.3, 0.2, zt - 0.005)], 0.0024,
             X["thread"], sides=4)
    for k, z in enumerate((-0.66, -0.47, -0.27, -0.07, 0.13, 0.33, zt - 0.06)):
        snap(f"{key}Snap{k}", Vector((0.0, yp, z)), (0, -1, 0), X, r=0.024)
    # the chenille "N" on the left chest, on a black felt border
    felt_letter(f"{key}ChestN", "N", 0.52, Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)),
                (0.46, 0, 0.36), X, 0.5 + R_OUT)
    # NIGHTMARE arched across the back (read from behind: the first letter on the wearer's right... the viewer's left)
    word = "NIGHTMARE"
    Ra, zc, phi = 2.6, -2.10, math.radians(19.0)
    F = Vector((0, 1, 0))
    for k, ch in enumerate(word):
        a = lerp(-phi, phi, k / (len(word) - 1))
        x = Ra * math.sin(a)          # a < 0 -> x > 0: the wearer's left, the viewer's left from behind
        z = zc + Ra * math.cos(a)
        R = Vector((-math.cos(a), 0, -math.sin(a)))
        U = Vector((-math.sin(a), 0, math.cos(a)))
        letter(f"{key}Back{k}", ch, 0.30, X["chenille"], R, U, F, (-x, 0, z), 0.5 + R_OUT + 0.0008, 0.013)
    # under it: a black crew-neck tee in the neck opening; striped rib-knit gussets at the hips' front corners
    piece(f"{key}Inner", "Torso")
    FIT_SAME[f"{key}Inner"] = f"{key}Shell"
    inner_yoke(f"{key}Inner", X, X["tee"], front_bot=0.55, back_bot=0.62, binding=X["knit_black"])
    build_side(key, X["knit"], paint_fn=stripes([(a, b, X[m]) for a, b, m in WB]))
    # sleeves: cream leather to the wrist's striped rib-knit cuffs
    piece(f"{key}SleeveL", "LeftArm")
    zt = C1.SLV_CUFF + 0.11
    zs = [zt, -0.37, -0.28, -0.18, -0.05, 0.10, 0.28, 0.46, 0.62, 0.76, 0.88, 0.96, 1.0]
    build_sleeve_e(f"{key}SleeveL", X, zs, lambda z: 0.020, mat=X["leather"], hem=False)
    zc = C1.SLV_CUFF
    cuff = stripes([(-0.90, zc + 0.04, X["knit"]), (zc + 0.04, zc + 0.052, X["knit_cream"]),
                    (zc + 0.052, zc + 0.064, X["knit_black"]), (zc + 0.064, zc + 0.076, X["knit_cream"]),
                    (zc + 0.076, 0.0, X["knit"])])
    zs_c = [zc, zc + 0.02, zc + 0.04, zc + 0.052, zc + 0.064, zc + 0.076, zc + 0.092, zt]
    rows = [ring_at(z, lerp(0.015, 0.020, (z - zc) / (zt - zc))) for z in zs_c]
    Gc = [[rows[j][k] for j in range(len(rows))] for k in range(len(rows[0]))]
    paint(cloth(f"{key}SleeveLCuff", Gc, 0.016, X["knit"], sleeve_hint), cuff)
    wire(f"{key}SleeveLCuffSeam", [tuple(c[-1] + (c[-1] - Vector((1.5, 0, c[-1].z))).normalized() * 0.010) for c in Gc],
         0.0045, X["leather"], sides=5)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    hug_sleeves(key)
    return dict(notes="the varsity jacket: crimson melton, cream leather sleeves, a closed brass-snap front, a flat striped "
                      "rib collar lying low round the wide neckline, striped rib cuffs and waistband, a chenille N on a felt "
                      "border on the left chest and NIGHTMARE arched across the back")


# ================================================================== the Waxed hunting jacket
def hunting_mats(M):
    X = dict(
        wool=mat_waxed("HuntWax", (0.020, 0.024, 0.015)),
        lining=mat_tartan("HuntTartan"),
        thread=A.mat_cloth("HuntThread", (0.05, 0.05, 0.035), weave=900, rough=0.6, sheen=0.1, bump=0.05, twill=False),
        jumper=mat_knit("HuntJumperOatmeal", (0.50, 0.43, 0.32), period=0.05, depth=0.35, rough=0.94, sheen=0.4),
        cord=mat_knit("HuntCorduroy", (0.16, 0.085, 0.040), period=0.022, depth=0.45, rough=0.8, sheen=0.7),
        brass=A.mat_metal("HuntBrass", (0.66, 0.47, 0.20), rough=0.36, tarnish=(0.10, 0.08, 0.04), wear=0.5),
        bone=M["bone"])
    X.update(silver=X["brass"], trim=X["wool"], pipe=X["wool"], collar=X["cord"], collar_in=X["cord"],
             collar_pipe=X["cord"], lapel=X["wool"], lapel_in=X["lining"], lapel_pipe=X["wool"])
    return X


def hunting_params():
    P = dict(xo_top=0.72, nape_z=0.78, hem=-0.72, xo_break=0.003, brk=0.30, lapel="notch", lapel_w=0.15, notch=0.05,
             collar_rise=0.035, collar_reach=0.10, collar_back=0.03, pipe_r=0.0055, trim_r=0.0052, back_folds=0.004,
             skirt_bot=-1.25, skirt_flare=0.050, skirt_vent=0.03)
    P["break"] = P["brk"]
    # the revers open in a rounded curve (wide at the chest, where long hair falls)
    P["xo"] = lambda z: 0.003 if z < P["brk"] else 0.003 + (P["xo_top"] - 0.003) * ((z - P["brk"]) / (1.0 - P["brk"])) ** 0.65
    P["lapel_fn"] = P["xo"]
    P["front_extra"] = [P["brk"], 0.33, 0.38, 0.45, 0.55, 0.70, 0.85]
    P["skirt_open"] = lambda z: 0.035 + 0.05 * smooth(-0.73, P["skirt_bot"], z)
    P["trim_hem_x0"] = 0.075   # the storm flap covers the hem's centre
    return P


def skirt_y(z, P):
    """the skirt's front outer face (y) at height z (c1.skirt_plan's offset + half its thickness)"""
    t = smooth(C1.SK_TOP, P["skirt_bot"], z)
    off = lerp(C1.SK_OFF_TOP, P["skirt_flare"], t ** 1.4)
    return -(0.5 + off + C1.T_SKIRT / 2)


def game_pocket(name, side, P, X, x0=0.20, x1=0.655, z0=-0.79, z1=-1.20, depth=0.032):
    """a bellows game pocket on the skirt's front: a front panel standing off on gussets (sides and bottom), a
    flap with a press-stud over the open top, two brass drain eyelets"""
    t = 0.010
    zs = [lerp(z0, z1, j / 5) for j in range(6)]
    yp = lambda z: skirt_y(z, P) - depth - t / 2
    G = [[Vector((side * lerp(x0, x1, i / 5), yp(z), z)) for z in zs] for i in range(6)]
    cloth(name + "Panel", G, t, X["wool"], lambda p: Vector((0, -1, 0)), mat_in=X["lining"])
    tg = 0.008
    for nm, x in (("A", x0 + tg / 2 + 0.001), ("B", x1 - tg / 2 - 0.001)):
        Gg = [[Vector((side * x, lerp(skirt_y(z, P) - 0.002, yp(z) + t / 2 + 0.001, f), z)) for z in zs] for f in (0, 0.5, 1)]
        cloth(name + "Gusset" + nm, Gg, tg, X["wool"], lambda p: Vector((side, 0, 0)))
    zb = z1 + tg / 2 + 0.001
    Gb = [[Vector((side * lerp(x0 + tg, x1 - tg, i / 4), lerp(skirt_y(zb, P) - 0.002, yp(zb) + t / 2 + 0.001, f), zb))
           for f in (0, 0.5, 1)] for i in range(5)]
    cloth(name + "GussetC", Gb, tg, X["wool"], lambda p: Vector((0, 0, -1)))
    # top-stitching round the panel
    yo = yp(z0) - t / 2 - 0.0015
    wire(name + "Stitch", [(side * x, yp(z) - t / 2 - 0.0015, z) for x, z in
                           ((x0 + 0.02, z0 - 0.10), (x0 + 0.02, z1 + 0.02), (x1 - 0.02, z1 + 0.02), (x1 - 0.02, z0 - 0.10))],
         0.0022, X["thread"], sides=4)
    # the flap
    tf = 0.010
    zf = [z0 + 0.035, z0 + 0.012, z0 - 0.02, z0 - 0.06, z0 - 0.095]
    yf = [skirt_y(zf[0], P) - 0.002 - tf / 2, yp(z0) - t / 2 - 0.004 - tf / 2] + [yp(z0) - t / 2 - 0.005 - tf / 2] * 3
    xf0, xf1 = x0 - 0.015, x1 + 0.015
    Gf = [[Vector((side * lerp(xf0, xf1, i / 6), yf[j] - (0.004 * math.sin(math.pi * i / 6) if j > 1 else 0.0), zf[j]))
           for j in range(len(zf))] for i in range(7)]
    cloth(name + "Flap", Gf, tf, X["wool"], lambda p: Vector((0, -1, 0)), mat_in=X["lining"])
    xm = (x0 + x1) / 2
    snap(name + "Stud", Vector((side * xm, yf[-1] - tf / 2 - 0.004 - 0.0005, z0 - 0.065)), (0, -1, 0), X, r=0.020)
    wire(name + "FlapStitch", [(side * lerp(xf0 + 0.015, xf1 - 0.015, i / 6), yf[-1] - tf / 2 - 0.0015 - 0.004 * math.sin(math.pi * i / 6),
                                z0 - 0.083) for i in range(7)], 0.0022, X["thread"], sides=4)
    for x in (x0 + 0.045, x1 - 0.045):
        eyelet(name + f"Eyelet{x:.2f}", Vector((side * x, yp(z1 + 0.04) - t / 2 - 0.0035, z1 + 0.04)), (0, -1, 0), X["brass"],
               R=0.010, r=0.0035)


def hunting_cuff_tab(name, X, zc=-0.47):
    """a storm-cuff tab across the outer face of the cuff, held by a brass press-stud"""
    t = 0.008
    G = [[Vector((2.0 + 0.020 + 0.007 + t / 2 + 0.001, y, z)) for z in (zc - 0.03, zc + 0.03)] for y in
         [lerp(-0.30, 0.22, k / 6) for k in range(7)]]
    cloth(name, G, t, X["wool"], lambda p: Vector((1, 0, 0)), mat_in=X["lining"])
    snap(name + "Stud", Vector((2.0 + 0.020 + 0.007 + t + 0.0015, 0.12, zc)), (1, 0, 0), X, r=0.020)


@item("HuntingJacket", "Waxed hunting jacket", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.6), (0.35, 0, -0.10), 85))
def build_hunting(M):
    key = "HuntingJacket"
    X, P = hunting_mats(M), hunting_params()
    piece(f"{key}Shell", "Torso")

    def collar(name, G, rows, side):
        build_collar_e(name, G, rows, side, P, X)
        build_lapel_e(name.replace("Collar", "Lapel"), side, P, X)
    build_shell_e(key, P, X, collar=collar)
    # the storm flap down the closed front, brass press-studs
    tp = 0.010
    zp = [-0.72, -0.60, -0.40, -0.20, 0.0, 0.20, P["brk"] - 0.006]
    yq = -(0.5 + R_OUT + 0.002 + tp / 2)
    Gp = [[Vector((x, yq, z)) for z in zp] for x in (-0.035, -0.01, 0.015, 0.04, 0.065)]
    cloth(f"{key}StormFlap", Gp, tp, X["wool"], lambda p: Vector((0, -1, 0)), mat_in=X["lining"])
    for s, x in ((1, 0.042), (-1, -0.025)):
        wire(f"{key}FlapStitch{s}", [(x, yq - tp / 2 - 0.0015, z) for z in (-0.71, -0.2, 0.3, P["brk"] - 0.015)], 0.0022,
             X["thread"], sides=4)
    # the tartan facing glimpsed along the flap's edge
    Gt = [[Vector((x, yq - tp / 2 - 0.0012 - 0.002, z)) for z in zp[:-1] + [P["brk"] - 0.02]] for x in (0.050, 0.058, 0.064)]
    cloth(f"{key}FlapFacing", Gt, 0.0035, X["lining"], lambda p: Vector((0, -1, 0)))
    for k, z in enumerate((-0.64, -0.42, -0.20, 0.02, 0.24)):
        snap(f"{key}Stud{k}", Vector((0.015, yq - tp / 2 - 0.0005, z)), (0, -1, 0), X, r=0.022)
    # a back yoke seam, top-stitched
    for s in (1, -1):
        wire(f"{key}Yoke{s}", [tuple(back_pt(s * x, 0.52, 0.001)) for x in (0.0, 0.5, 0.99)], 0.0028, X["thread"], sides=4)
    # under it: an oatmeal knit jumper (a crew neck in the revers' V, the hips' corners)
    piece(f"{key}Inner", "Torso")
    FIT_SAME[f"{key}Inner"] = f"{key}Shell"
    inner_yoke(f"{key}Inner", X, X["jumper"], front_bot=0.22, back_bot=0.62, binding=X["jumper"])
    build_side(key, X["jumper"])
    piece(f"{key}Skirt", "Torso", rig=C1.skirt_rig)
    C1.build_skirt(f"{key}Skirt", P, X)
    for s in (1, -1):
        game_pocket(f"{key}SkirtPocket{'L' if s > 0 else 'R'}", s, P, X)
        snap(f"{key}SkirtStud{s}", Vector((s * 0.075, skirt_y(-0.78, P) - 0.0045, -0.78)), (0, -1, 0), X, r=0.020)
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve_e(f"{key}SleeveL", X, C1.SLEEVE_Z_K, lambda z: 0.020)
    hunting_cuff_tab(f"{key}SleeveLTab", X, zc=C1.SLV_CUFF + 0.06)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    hug_sleeves(key, {f"{key}Skirt": {"follow": "LL=1;RL=1"}})
    return dict(notes="the waxed hunting jacket: black-olive waxed canvas, a brown corduroy collar, a storm-flapped front "
                      "with brass press-studs, a quilted tartan lining glimpsed at the edges, big bellows game pockets on a "
                      "hip-length skirt that moves with the legs (BodyFollow)")


# ================================================================== the Velvet smoking jacket
def smoking_mats(M):
    X = dict(
        wool=mat_quilt_velvet("SmokeQuiltVelvet", (0.20, 0.018, 0.035)),
        lining=satin("SmokeLiningSilk", (0.12, 0.012, 0.022)),
        thread=A.mat_cloth("SmokeThread", (0.02, 0.018, 0.02), weave=900, rough=0.5, sheen=0.2, bump=0.05, twill=False),
        satin=satin("SmokeBlackSatin", (0.010, 0.009, 0.012)),
        shirt=satin("SmokeShirtSilk", (0.78, 0.74, 0.64)),
        cravat=A.mat_cloth("SmokeCravatSilk", (0.10, 0.012, 0.030), weave=900, rough=0.30, sheen=0.5, bump=0.04,
                           twill=True, stripe=((0.03, 0.006, 0.012), 0.03, 0.008, 45)),
        pearl=A.mat_flat("SmokePearl", (0.86, 0.84, 0.80), rough=0.15, noise=60, bump=0.01, vary=0.05, wear=0.0, coat=0.6),
        gold=M["gold"], fringe=A.mat_cloth("SmokeTasselSilk", (0.012, 0.011, 0.014), weave=1400, rough=0.35, sheen=0.6,
                                           bump=0.3, twill=False),
        bone=M["bone"])
    X.update(silver=X["satin"], btn="silver", trim=X["satin"], pipe=X["satin"], collar=X["satin"], collar_in=X["satin"],
             collar_pipe=X["satin"], lapel=X["satin"], lapel_in=X["satin"], lapel_pipe=X["satin"], cuff=X["satin"],
             cuff_pipe=X["satin"], brass=M["gold"])
    return X


def smoking_params():
    P = dict(xo_top=0.72, nape_z=0.78, hem=-0.72, xo_break=0.003, brk=0.0, lapel="shawl", lapel_w=0.17, notch=0.0,
             collar_rise=0.030, collar_reach=0.095, collar_back=0.03, pipe_r=0.0055, trim_r=0.0060, back_folds=0.0,
             skirt_bot=-1.0, skirt_flare=0.050, skirt_vent=0.03, cuff="turnback")
    P["break"] = P["brk"]

    def xo(z):
        if z >= P["brk"]:
            return lerp(0.003, P["xo_top"], (z - P["brk"]) / (1.0 - P["brk"]))
        if z >= -0.22:
            return 0.003
        return 0.003   # wrapped closed under the sash, to the hem
    P["xo"] = xo
    P["front_extra"] = [0.0, -0.04, -0.22, -0.30, -0.40, -0.56, -0.66, 0.15, 0.55, 0.70, 0.85]
    P["trim_front_to"] = P["brk"]
    P["skirt_open"] = lambda z: 0.02 + 0.03 * smooth(-0.73, P["skirt_bot"], z)
    return P


SASH_Z0, SASH_Z1 = -0.215, -0.058   # the sash's band (above the katana guard's top, z -0.25, at x >= 0.76)
TAILS = [((-0.046, -0.19), (-0.050, -0.585)), ((0.050, -0.19), (0.054, -0.545))]   # (x, z) top and bottom


def build_sash(key, X):
    """the black satin sash round the waist outside the shell, a knot at the front, two tails hanging in front
    (kept within the skirt's front opening) ending in gilt-headed silk tassels"""
    name = f"{key}Sash"
    t = 0.012
    zs = [lerp(SASH_Z0, SASH_Z1, j / 4) for j in range(5)]
    for side in (1, -1):
        rows = [girdle_path(z) for z in zs]
        G = [[Vector((side * rows[j][i].x, rows[j][i].y, rows[j][i].z)) for j in range(len(zs))] for i in range(len(rows[0]))]
        # soft horizontal folds in the satin
        for i in range(len(G)):
            for j in range(1, len(zs) - 1):
                p = G[i][j]
                nrm = Vector((0, -1, 0)) if p.y < -0.45 and abs(p.x) < 0.92 else (Vector((0, 1, 0)) if p.y > 0.45 and abs(p.x) < 0.92 else Vector((side, 0, 0)))
                G[i][j] = p + nrm * 0.0025 * math.sin(math.pi * j / (len(zs) - 1))
        cloth(f"{name}Band{'L' if side > 0 else 'R'}", G, t, X["satin"], out_hint_torso)
    yb = -(0.5 + 0.040 + t / 2)          # the band's outer face at the front
    # the knot: a rolled lump with a wrap across it
    A.sphere(f"{name}Knot", 1.0, (0.0, yb - 0.026, -0.136), X["satin"], scale=(0.085, 0.028, 0.066), seg=16, rings=10)
    wire(f"{name}KnotWrap", [(0.0, yb - 0.026 - 0.036 * math.cos(math.radians(a)), -0.136 + 0.072 * math.sin(math.radians(a)))
                              for a in range(-80, 81, 10)], 0.011, X["satin"], sides=6)
    # the tails: satin ribbons from under the knot, hanging a little forward
    tt = 0.009
    for n, ((xa, za), (xb, zb)) in enumerate(TAILS):
        zz = [lerp(za, zb, j / 8) for j in range(9)]
        w = 0.084 if n == 0 else 0.078
        G = []
        for i in range(5):
            col = []
            for j, z in enumerate(zz):
                f = j / 8
                x = lerp(xa, xb, f) + (i / 4 - 0.5) * w * (1 - 0.15 * f)
                y = yb - tt / 2 - 0.0015 - 0.010 * f ** 1.2 - 0.0035 * math.sin(math.pi * i / 4) * f
                col.append(Vector((x, y, z)))
            G.append(col)
        cloth(f"{name}Tail{n}", G, tt, X["satin"], lambda p: Vector((0, -1, 0)))
        # the tail's end gathered into a cord and the tassel
        end = Vector((xb, yb - tt / 2 - 0.0015 - 0.010, zb))
        cy = yb - 0.0335
        wire(f"{name}Cord{n}", [tuple(end + Vector((0, 0, 0.01))), (xb, cy, zb - 0.010), (xb, cy, zb - 0.022)], 0.0045,
             X["gold"], sides=5)
        tassel(f"{name}Tassel{n}", (xb, cy, zb - 0.022), X, r=0.030, L=0.075)


def sash_rig(ob):
    cols = []
    yb = -(0.5 + 0.040 + 0.006)
    for (xa, za), (xb, zb) in TAILS:
        bot = zb - 0.022 - 0.04 - 0.075
        cols.append([Vector((lerp(xa, xb, f), yb - 0.02, lerp(za, bot, f))) for f in (0.0, 0.28, 0.55, 0.8, 1.0)])
    # the sash rides the Inner piece (the shirt's depth fit, so it stays outside the shell on every body): only the
    # tails and tassels (below the knot, in front of the sash band) sway; everything else stays on Root
    def mask(co):
        return co.z < -0.225 and co.y < -0.547 and abs(co.x) < 0.13
    orig = A.make_rig

    def mk(o, bones, wfn):
        return orig(o, bones, lambda co: wfn(co) if mask(co) else {"Root": 1.0})
    A.make_rig = mk
    try:
        return A.chain_rig(ob, (0.0, yb - 0.02, -0.15), cols)
    finally:
        A.make_rig = orig


def cravat(name, X):
    """a silk cravat at the throat over the shirt: a soft knot, two broad falls overlapping, a gold stick pin with a
    pearl. Kept below z 0.88 (the slim bodies' depth fits bring the throat close to the head's underside)"""
    yb = -(0.5 + D_I + T_I / 2)
    A.sphere(name + "Knot", 1.0, (0.0, yb - 0.026, 0.828), X["cravat"], scale=(0.080, 0.024, 0.048), seg=14, rings=8)
    for n, (s, dx) in enumerate(((1, 0.012), (-1, -0.010))):
        zs = [0.80, 0.73, 0.66, 0.59, 0.52]
        G = []
        for i in range(5):
            u = i / 4 - 0.5
            col = []
            for j, z in enumerate(zs):
                f = j / 4
                w = lerp(0.10, 0.21, f)
                y = yb - 0.0045 - 0.004 * n - 0.010 * math.sin(math.pi * (i / 4)) * (0.4 + 0.6 * f) - 0.006 * (1 - f)
                col.append(Vector((dx + s * 0.010 * f + u * w, y, z)))
            G.append(col)
        cloth(f"{name}Fall{n}", G, 0.004, X["cravat"], lambda p: Vector((0, -1, 0)))
    A.cyl(name + "Pin", 0.004, 0.03, (0.0, yb - 0.035, 0.68), X["gold"], rot=(math.pi / 2, 0, 0), verts=6, bevel=0.0)
    A.sphere(name + "Pearl", 0.012, (0.0, yb - 0.049, 0.68), X["pearl"], seg=10, rings=6)


@item("SmokingJacket", "Velvet smoking jacket", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.6), (0.20, 0, -0.10), 85))
def build_smoking(M):
    key = "SmokingJacket"
    X, P = smoking_mats(M), smoking_params()
    piece(f"{key}Shell", "Torso")

    def collar(name, G, rows, side):
        build_collar_e(name, G, rows, side, P, X, front_w=0.056)
        build_lapel_e(name.replace("Collar", "Shawl"), side, P, X, shawl=True)
    build_shell_e(key, P, X, collar=collar)
    # a satin frog at the break (above the sash)
    frog(f"{key}Frog", -0.020, X, half=0.11, mat=X["satin"], r=0.0045, x0=0.02, toggle_lift=0.016)
    # a welt breast pocket, piped in satin, a silk square peeping out
    for k, (x0, x1) in enumerate(((0.57, 0.80),)):
        G = [[front_pt(x, z, 0.004) for z in (0.40, 0.425)] for x in (x0, (x0 + x1) / 2, x1)]
        cloth(f"{key}Welt", G, 0.008, X["satin"], lambda p: Vector((0, -1, 0)))
        G2 = [[front_pt(lerp(x0 + 0.03, x1 - 0.05, i / 3), z, 0.0035) for z in (0.427, 0.465 + 0.02 * (i % 2))]
              for i in range(4)]
        cloth(f"{key}Square", G2, 0.004, X["lining"], lambda p: Vector((0, -1, 0)))
    # under it: a silk shirt in the shawl's V with a cravat; the sash (riding the same piece, so it shares the depth
    # fit) with its swaying tasselled tails; quilted velvet at the hips' corners
    piece(f"{key}Inner", "Torso", rig=sash_rig, sway="Tails", keepout=(0, 1, 0))
    FIT_SAME[f"{key}Inner"] = f"{key}Shell"
    inner_yoke(f"{key}Inner", X, X["shirt"], front_bot=-0.10, back_bot=0.62, binding=X["shirt"])
    for k, z in enumerate((0.42, 0.27, 0.12)):   # pearl shirt studs
        A.sphere(f"{key}InnerStud{k}", 0.010, (0.0, -(0.5 + D_I + T_I / 2) - 0.006, z), X["pearl"], scale=(1, 0.6, 1), seg=8, rings=5)
    cravat(f"{key}InnerCravat", X)
    build_sash(key, X)
    build_side(key, X["wool"])
    piece(f"{key}Skirt", "Torso", rig=C1.skirt_rig)
    C1.build_skirt(f"{key}Skirt", P, X)
    piece(f"{key}SleeveL", "LeftArm")
    C1.build_sleeve_k(f"{key}SleeveL", P, X)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    hug_sleeves(key, {f"{key}Skirt": {"follow": "LL=1;RL=1"}})
    return dict(notes="the velvet smoking jacket: crimson velvet quilted in diamonds, a black satin shawl collar, satin "
                      "turn-back cuffs and piping, a satin frog; a black satin sash tied at the waist with two tasselled "
                      "tails that sway (Tails); a hip-length skirt that moves with the legs (BodyFollow)")


# ================================================================== the Crimson spencer
def spencer_mats(M):
    X = dict(
        wool=A.mat_velvet("SpencerVelvet", (0.21, 0.018, 0.034), rough=0.66),
        lining=satin("SpencerLining", (0.03, 0.01, 0.015)),
        thread=A.mat_cloth("SpencerThread", (0.02, 0.018, 0.02), weave=900, rough=0.5, sheen=0.2, bump=0.05, twill=False),
        braid=braid_mat("SpencerBraid"), bone=M["bone"],
        silk=satin("SpencerGownSilk", (0.78, 0.74, 0.65)),
        lace=A.mat_cloth("SpencerLace", (0.82, 0.79, 0.71), weave=1500, rough=0.7, sheen=0.4, bump=0.4, twill=False, vary=0.05))
    X.update(trim=X["braid"], pipe=X["braid"], silver=X["braid"], brass=X["braid"])
    return X


def spencer_params():
    P = dict(xo_top=0.72, nape_z=0.80, neck_z=0.66, neck_p=0.5, hem=-0.30, trim_r=0.0065, pipe_r=0.0055,
             back_folds=0.0)
    P["xo"] = u_neck(P["neck_z"], P["neck_p"], P["xo_top"])
    P["front_extra"] = u_rows(P["neck_z"], P["neck_p"]) + [-0.30, -0.22, -0.10]
    P["trim_hem_x0"] = 0.012
    return P


def spencer_gown(name, X, zt=-0.20, zt_side=-0.31, zb=-0.72):
    """the ivory silk gown's high-waisted bodice below the cropped spencer, down to the hem line z -0.72: the front
    (x 0..0.70: the hips' corners are the Side pieces), the side under the arm (below the shell's band, -0.30) and the
    back, softly pleated, tucked up under the spencer's hem"""
    d, t = D_I, T_I
    zs = [lerp(zb, 0.0, j / 6) for j in range(7)]

    def pleat(u, k=0.0015):
        return k * math.sin(2 * math.pi * u / 0.09)
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        zbx = lambda x: zb + 0.04 * smooth(0.55, 0.70, abs(x))   # up at the hip corners: a striding leg's top corner
        G = [[Vector((side * x, -(0.5 + d + pleat(x)), lerp(zbx(x), zt, j / 6))) for j in range(7)]
             for x in [lerp(0.003, 0.70, i / 14) for i in range(15)]]
        cloth(f"{name}GownF{sd}", G, t, X["silk"], out_hint_torso)
        plan = [(1.0 + d, lerp(-0.46, 0.44, k / 8), zt_side) for k in range(9)]
        for k in range(1, 4):
            a = math.radians(90 * k / 4)
            plan.append((1.0 + d * math.cos(a), 0.5 + d * math.sin(a), zt_side))
        plan += [(lerp(1.0, 0.003, k / 14), 0.5 + d + pleat(lerp(1.0, 0.003, k / 14)), zt) for k in range(15)]
        G = [[Vector((side * x, y, lerp(zbx(x), z1, j / 6))) for j in range(7)] for x, y, z1 in plan]
        cloth(f"{name}GownB{sd}", G, t, X["silk"], out_hint_torso)


def jabot(name, X):
    """a lace jabot cascading from the blouse's throat over the spencer's closure: four ruffled tiers, each a little
    proud of the one above (the lower ones clear the spencer's collar and front braid)"""
    tiers = [(0.80, 0.69, -0.520, -0.522, 0.15), (0.725, 0.60, -0.545, -0.578, 0.19), (0.645, 0.53, -0.600, -0.602, 0.22),
             (0.575, 0.48, -0.620, -0.622, 0.24)]
    for n, (z0, z1, y0, y1, w) in enumerate(tiers):
        G = []
        nu = 16
        for i in range(nu + 1):
            u = i / nu - 0.5
            col = []
            for j in range(5):
                f = j / 4
                wav = 0.5 + 0.5 * math.cos(2 * math.pi * i * 4 / nu)
                z = lerp(z0, z1, f) - 0.012 * (1 - wav) * f ** 2   # a scalloped, fluted edge
                y = lerp(y0, y1, min(1.0, f * 1.6)) - 0.014 * wav * (0.3 + 0.7 * f)
                col.append(Vector((u * w * (0.85 + 0.3 * f), y, z)))
            G.append(col)
        cloth(f"{name}Tier{n}", G, 0.003, X["lace"], lambda p: Vector((0, -1, 0)))


@item("CrimsonSpencer", "Crimson spencer", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 1.2), (0.35, 0, 0.45), 85))
def build_spencer(M):
    key = "CrimsonSpencer"
    X, P = spencer_mats(M), spencer_params()
    piece(f"{key}Shell", "Torso")

    def collar(name, G, rows, side):
        prof = [(-0.006, 0.0110), (0.0, 0.0135), (0.010, 0.0130), (0.025, 0.0110), (0.045, 0.0100), (0.062, 0.0095)]
        Gc = flat_collar(name, P, side, prof, 0.014, X["wool"])
        wire(name + "Braid", [tuple(c[-1] + (c[-1] - c[-2]).normalized() * 0.002) for c in Gc[1:]], 0.0055, X["braid"], sides=6)
        wire(name + "Roll", [tuple(c[0] + (c[0] - c[1]).normalized() * 0.003) for c in Gc[1:]], 0.0055, X["braid"], sides=6)
    out = build_shell_e(key, P, X, collar=collar)
    # braid down both front edges (they meet edge to edge) and the brandebourgs across them
    for side in (1, -1):
        G, rows = out[side]
        nf = sum(1 for r in rows if r[2] == "front")
        e = [G[0][j] for j in range(nf) if rows[j][1] <= P["neck_z"] - 0.06]
        wire(f"{key}BraidFront{side}", [tuple(p + Vector((side * 0.0075, -(T_SHELL / 2 + 0.0065), 0))) for p in e], 0.0065,
             X["braid"], sides=5)
    for k, z in enumerate((0.44, 0.27, 0.10, -0.07)):
        frog(f"{key}Brand{k}", z, X, half=0.20 - 0.025 * k, mat=X["braid"], r=0.0045, x0=0.024, toggle_lift=0.023, n_tre=24,
             sides=4)
    # a braid trefoil at the back waist
    pts = []
    for k in range(37):
        a = 2 * math.pi * k / 36
        rr = 0.035 + 0.030 * math.cos(3 * a)
        pts.append(back_pt(rr * math.cos(a + math.pi / 2), -0.17 + rr * math.sin(a + math.pi / 2), 0.0055))
    wire(f"{key}BackKnot", [tuple(p) for p in pts], 0.0045, X["braid"], sides=5, closed=True)
    # under it: an ivory silk blouse (the neck, a lace jabot) and the gown's high-waisted bodice down to z -0.72
    piece(f"{key}Inner", "Torso")
    FIT_SAME[f"{key}Inner"] = f"{key}Shell"
    inner_yoke(f"{key}Inner", X, X["silk"], front_bot=0.45, back_bot=0.66, binding=X["lace"])
    jabot(f"{key}InnerJabot", X)
    # the gown below the hem fits the hips and belly itself (the shell's fit is set above the hem); it meets the
    # spencer's hem edge to edge, the hem's braid over the seam
    piece(f"{key}Gown", "Torso")
    HUG_FIT.add(f"{key}Gown")
    LEG_HEM[f"{key}Gown"] = -0.70
    spencer_gown(f"{key}Gown", X, zt=-0.296, zb=-0.70)
    build_side(key, X["silk"], mid_x0=0.70)
    # sleeves: puffed heads gathered into a braid band, fitted to the cuff
    piece(f"{key}SleeveL", "LeftArm")
    zs = [C1.SLV_CUFF, C1.SLV_CUFF + 0.03, -0.45, -0.37, -0.28, -0.18, -0.05, 0.10, 0.25, 0.36, 0.42, 0.50, 0.58, 0.66,
          0.74, 0.82, 0.89, 0.95, 1.0]
    puff = lambda z: 0.058 * math.sin(0.5 * math.pi * smooth(0.40, 0.90, z))
    build_sleeve_e(f"{key}SleeveL", X, zs, lambda z: 0.020, puff=puff, gathers=0.22, hem=False)
    for nm, z in (("Band", 0.40), ("CuffA", C1.SLV_CUFF + 0.025), ("CuffB", C1.SLV_CUFF + 0.06)):
        wire(f"{key}SleeveL{nm}", [tuple(p) for p in ring_at(z, 0.020 + 0.007 + 0.0058)], 0.0058, X["braid"], sides=6)
    # an Austrian knot on the cuff's outer face
    pts = []
    for k in range(41):
        a = 2 * math.pi * k / 40
        rr = 0.03 + 0.024 * math.cos(3 * a)
        pts.append(Vector((2.0 + 0.020 + 0.007 + 0.005, 0.0 + rr * math.cos(a + math.pi / 2), -0.38 + 0.9 * rr * math.sin(a + math.pi / 2))))
    wire(f"{key}SleeveLKnot", [tuple(p) for p in pts], 0.0042, X["braid"], sides=5, closed=True)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    hug_sleeves(key)
    return dict(notes="the crimson spencer: a cropped, fitted crimson velvet jacket closed edge to edge, puffed sleeve heads "
                      "gathered into braid, black braid on every edge, brandebourg loops across the front and a trefoil at "
                      "the back, a small fall collar lying low")
