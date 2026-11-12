"""Kit C coats, batch C: the Inverness cape-coat, the oilskin rain cloak and the lamplighter's coat (all unisex).

Each is built like the Scholar's frock coat (nh_acc_batchc1): a rigid <Key>Shell on the torso (Kit C's shell: the wide
neckline, the scooped nape and the low collar of build_shell_k, here with a plain front edge instead of lapels), sleeves
rigid on the arms, and a <Key>Skirt skinned to the legs' follow bones (BodyFollow).

  InvernessCoat    black houndstooth wool (a woven 2/2-twill houndstooth in the material), knee-length skirts, and a
                   <Key>Cape: a shoulder cape to the elbow, open at the front, with a black velvet collar. The cape is
                   one skinned Torso piece: over the torso it stays on Root, over each arm (|x| >= 1) it rides that
                   arm's follow bone F_LA / F_RA entirely (BodyFollow turns them with the arms): the R6 arm's top rises
                   above the shoulder as it swings (its front-top corner to z ~1.2 at 55 degrees) and cloth lying over
                   it has to go with it. Its collar's inner edge tucks down onto the torso's top beside the neck (where
                   the shell's wide neckline leaves it bare): the cape rests there.
  RainCloak        olive-black oilskin to mid-calf, bell sleeves flaring at the cuff, horn toggles on cord loops down
                   the front, and the hood worn down: a flat, thin pouch on the upper back tucked under the collar's
                   fall at the scooped neckline (it never rises up the head; hair falls over it).
  LamplighterCoat  brown-black oilcloth to z -2.5, a storm flap across the chest buttoned in brass (flame buttons), a
                   brass lamp hook on a leather tab at the right hip (lying flat on the coat, clear of the striding
                   right leg), turned-up cuffs.

Layers kept apart (the checker doesn't test one item's pieces against each other): the cape's mid-surface stands
0.074 / 0.078 / 0.052 off the torso's front / back / the arm's outer face and 0.050 over the shoulders (the shell's
outer face is at 0.032, the sleeves' at 0.027); its depth fit is the shell's (so on every body it keeps the same
proportion off the shell). `--selfcheck` prints triangle overlaps between the item's own parts (SELF lines).
Run: cd art/characters/accessories && E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- InvernessCoat --nobake
"""
import math, sys
import bpy
from mathutils import Vector, Matrix
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import ccw
from nh_acc_batch4 import wire, axis_frame, place, mirror_piece, arm_wrap
import nh_acc_batch7 as K7
from nh_acc_batch7 import (cloth, out_hint_torso, band_grid, button, front_point, back_point, pocket_flap, half_belt,
                           D_F, T_SHELL, HEM_BACK, FRONT_Z, ARC, TOP_Y, cut_line, x_in, wrap_kw, sleeve_hint, X_IN_TOP)
import nh_acc_batchc1 as C1
from nh_acc_batchc1 import (build_skirt, skirt_rig, write_extra, back_neck, build_collar_k, BACK_Z_K, build_sleeve_k,
                            SLV_CUFF, SLV_XIN, slv_xin)

Y_OUT = 0.5 + D_F + T_SHELL / 2   # the shell's outer face (front / back)


# ================================================================== materials
def mat_houndstooth(name, dark, light, cell=0.0105, rough=0.85, sheen=0.42, bump=0.11, wear=0.22, dirt=0.5, vary=0.07):
    """woven houndstooth: a 2/2 twill with four dark and four light threads in both warp and weft (the colour of each
    cell is the warp's where the twill lifts it, else the weft's). Cells are `cell` studs; the pattern runs across
    (x + y) and down z, so it reads on the front, the back and the sides alike"""
    m, T, bs = A._base(name)
    tc = T.node("ShaderNodeTexCoord")
    sep = T.node("ShaderNodeSeparateXYZ")
    T.L(tc.outputs["Object"], sep.inputs["Vector"])
    u = T.math("FLOOR", T.math("DIVIDE", T.math("ADD", sep.outputs["X"], sep.outputs["Y"]), cell))
    v = T.math("FLOOR", T.math("DIVIDE", T.math("ADD", sep.outputs["Z"], 40.0), cell))

    def mod(a, n):
        return T.math("SUBTRACT", a, T.math("MULTIPLY", T.math("FLOOR", T.math("DIVIDE", a, n)), n))
    lift = T.math("LESS_THAN", mod(T.math("ADD", u, v), 4.0), 2.0)
    warp = T.math("LESS_THAN", mod(u, 8.0), 4.0)
    weft = T.math("LESS_THAN", mod(v, 8.0), 4.0)
    dk = T.math("ADD", T.math("MULTIPLY", lift, warp), T.math("MULTIPLY", T.math("SUBTRACT", 1.0, lift), weft))
    base = T.mix(dk, light, dark, "MIX")
    # the twill's ridges as bump, and the fibre noise
    mp = T.node("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / cell, 1 / cell, 1 / cell)
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(45))
    T.L(tc.outputs["Object"], mp.inputs["Vector"])
    wa = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wa.inputs["Scale"].default_value = 0.5; wa.inputs["Distortion"].default_value = 0.5
    T.L(mp.outputs["Vector"], wa.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 10
    T.L(T.coord(25.0), nz.inputs["Vector"])
    col = T.mix(vary, base, nz.outputs["Color"], "OVERLAY")
    col = T.mix(T.math("MULTIPLY", wa.outputs["Fac"], 0.15), col, (0, 0, 0), "MULTIPLY")
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.004
    T.L(wa.outputs["Fac"], bp.inputs["Height"])
    bs.inputs["Sheen Weight"].default_value = sheen
    bs.inputs["Sheen Roughness"].default_value = 0.4
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.1))
    A._weather(T, bs, col, r, A._val(T, 0.0), bp.outputs["Normal"], wear, False, dirt, 0.006)
    return m


def mat_oilskin(name, rgb, rough=0.40, coat=0.35, crease=0.22, weave=520.0, wax=0.12, wear=0.3, dirt=0.55):
    """waxed cotton / oilcloth: a fine plain weave under a waxy film (a clear coat), soft creases and paler rubbed wax
    where the creases stand"""
    m, T, bs = A._base(name)
    tc = T.node("ShaderNodeTexCoord")
    mp = T.node("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (weave, weave, weave)
    T.L(tc.outputs["Object"], mp.inputs["Vector"])
    wa = T.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wa.inputs["Scale"].default_value = 1.0; wa.inputs["Distortion"].default_value = 0.4
    T.L(mp.outputs["Vector"], wa.inputs["Vector"])
    cr = T.node("ShaderNodeTexNoise"); cr.inputs["Scale"].default_value = 1.0; cr.inputs["Detail"].default_value = 6
    cr.inputs["Distortion"].default_value = 1.6
    T.L(T.coord((11.0, 11.0, 4.0)), cr.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    T.L(T.coord(18.0), nz.inputs["Vector"])
    ridge = T.math("MULTIPLY", T.math("SUBTRACT", cr.outputs["Fac"], 0.52), 6.0, clamp=True)
    col = T.mix(0.10, A._rgb(T, rgb), nz.outputs["Color"], "OVERLAY")
    col = T.mix(T.math("MULTIPLY", ridge, wax), col, tuple(min(1.0, c * 1.8 + 0.01) for c in rgb), "MIX")
    h = T.math("ADD", cr.outputs["Fac"], T.math("MULTIPLY", wa.outputs["Fac"], 0.04))
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = crease; bp.inputs["Distance"].default_value = 0.02
    T.L(h, bp.inputs["Height"])
    bs.inputs["Coat Weight"].default_value = coat
    bs.inputs["Coat Roughness"].default_value = 0.28
    r = T.math("ADD", rough, T.math("MULTIPLY", T.math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.16))
    r = T.math("ADD", r, T.math("MULTIPLY", ridge, 0.12))
    A._weather(T, bs, col, r, A._val(T, 0.0), bp.outputs["Normal"], wear, False, dirt, 0.006)
    return m


def mat_horn(name="Horn"):
    return A.mat_flat(name, (0.075, 0.055, 0.040), rough=0.30, coat=0.45, noise=140, bump=0.03, vary=0.35, wear=0.15)


# ================================================================== the Kit C shell with a plain front edge
def front_fn(P):
    """x of the front edge: a V from the neckline's front corner (xo_top at z 1) down to xo_break at `break` (curved by
    v_pow), straight below, rounded into the hem"""
    zb, xb, xt, pw = P["break"], P["xo_break"], P["xo_top"], P.get("v_pow", 1.0)

    def fx(z):
        if z >= zb:
            return xb + (xt - xb) * ((z - zb) / (1.0 - zb)) ** pw
        if z > -0.62:
            return xb
        R = 0.10
        return xb + R - math.sqrt(max(0.0, R * R - (z + 0.62) ** 2))
    return fx


def shell_rows_c(P, fx):
    rows = []
    for (y, z, reg, xs, xe) in C1.shell_rows_k(P):
        if reg == "front":
            xs = fx(z)
        rows.append((y, z, reg, xs, xe))
    return rows


def shell_grid_c(side, P, fx, ncol=9):
    rows = shell_rows_c(P, fx)
    G = []
    for i in range(ncol + 1):
        col = []
        for (y, z, reg, xs, xe) in rows:
            x = lerp(xs, xe, i / ncol)
            col.append(Vector((side * x, y + (K7.back_fold(x, z, P) if reg == "back" else 0.0), z)))
        G.append(col)
    return G, rows


def build_shell_c(name, P, X, collar=True, seam_back_top=None, seam_shoulder=True):
    """build_shell_k with a plain (lapel-less) front edge, piped from the neckline down; optionally no collar (the
    Inverness's collar is on its cape) and a shorter centre back seam (under a hood)"""
    from nh_acc_batch7 import T_BAND
    fx = front_fn(P)
    nf = len(FRONT_Z)
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G, rows = shell_grid_c(side, P, fx)
        cloth(f"{name}Body{sd}", G, T_SHELL, X["wool"], out_hint_torso, mat_in=X["lining"])
        cloth(f"{name}Band{sd}", band_grid(side), T_BAND, X["wool"], out_hint_torso, mat_in=X["lining"])
        out = T_SHELL / 2 + 0.004
        edge = [G[0][j] for j in range(nf - 1, -1, -1)] + [G[i][0] for i in range(1, len(G))] + \
               [G[-1][j] for j in range(1, nf) if FRONT_Z[j] <= -0.075]
        edge = [p + Vector((0, -out, 0)) for p in edge]
        wire(f"{name}PipeFront{sd}", [tuple(p) for p in edge], P["pipe_r"], X["pipe"], sides=5)
        jh = len(rows) - 1
        wire(f"{name}PipeBack{sd}", [tuple(G[i][jh] + Vector((0, out + 0.002, 0))) for i in range(len(G))], P["pipe_r"],
             X["pipe"], sides=5)
        if seam_shoulder:
            top = [r for r in rows if r[2] == "top"]
            ys = top[min(range(len(top)), key=lambda k: abs(top[k][0]))]
            wire(f"{name}SeamShoulder{sd}", [(side * lerp(ys[3], 0.994, t), ys[0], ys[1] + out + 0.001) for t in (0.04, 0.5, 0.97)],
                 0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSide{sd}", [(side * (1.0 + 0.002), -(0.5 + D_F + out - 0.004), z) for z in (-0.06, 0.4, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSideB{sd}", [(side * (1.0 + 0.002), 0.5 + D_F + out - 0.004, z) for z in (HEM_BACK + 0.02, 0.2, 0.97)],
             0.0035, X["thread"], sides=4)
        if collar:
            build_collar_k(f"{name}Collar{sd}", G, rows, side, P, X)
    zt = seam_back_top if seam_back_top is not None else P.get("nape_z", 0.78) - 0.06
    wire(f"{name}SeamBack", [(0, Y_OUT + 0.001, z) for z in (HEM_BACK + 0.02, -0.2, lerp(-0.2, zt, 0.5), zt)], 0.004,
         X["thread"], sides=4)
    return fx


def collar_edge_back(P):
    """the collar_k's lower edge down the scooped back: [(x, z)] from the centre back out to the shoulder top"""
    zn = P.get("nape_z", 0.78)
    pts = [(back_neck(z, P), z - P["collar_back"]) for z in BACK_Z_K if z >= zn - 0.005]
    return sorted(pts)


# ================================================================== the inner layer (no bare torso shows)
D_IN, T_IN = 0.0035, 0.003    # its mid-surface off the torso and its thickness (thin and close: hair rests on it)
HIP_X = 0.035                   # the inner layer's front stops this far inside the shell's cutaway edge
IN_FZ = [-0.72, -0.67, -0.62, -0.48, -0.26, -0.20, -0.14, -0.08, 0.10, 0.50, 0.80, 0.90, 0.94, 0.97, 0.99, 1.0]
IN_TY = [-0.5, -0.25, 0.0, 0.25, 0.5]


def head_clear_x(z, y=0.5 + D_IN, margin=0.014):
    """the smallest |x| at which a point on the torso's front / back face (|y|) at height z is clear of the head
    (the checker's head: a cylinder r 0.6 from z 0.9, its bottom edge rounded by 0.25)"""
    dz = z - 0.9
    if dz <= 0:
        return 0.0
    rh = 0.35 + math.sqrt(max(0.0, 0.0625 - (0.25 - min(dz, 0.25)) ** 2)) + margin
    return math.sqrt(max(0.0, rh * rh - y * y))


def inner_grid(side, ncol=4, neck_r=0.60):
    """one half of the inner layer's mid-surface: the front face (hem up), round the top front edge, over the top
    (a neck hole r neck_r), round the back top edge, down the back. The neckline follows the head's own edge, so
    the torso is covered wherever it isn't inside the head"""
    d = D_IN
    rows = []
    for z in IN_FZ:   # in front it stops short of the shell's katana cutaway (the Hips piece covers the corners)
        rows.append((-(0.5 + d), z, head_clear_x(z), min(0.99, cut_line(z) - HIP_X)))
    for a in (40,):
        y = -0.5 - d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, math.sqrt(max(0.0, neck_r ** 2 - y * y)), 0.99))
    for y in IN_TY:
        rows.append((y, 1.0 + d, math.sqrt(max(0.0, neck_r ** 2 - y * y)), 0.99))
    for a in (40,):
        y = 0.5 + d * math.cos(math.radians(a)); z = 1.0 + d * math.sin(math.radians(a))
        rows.append((y, z, math.sqrt(max(0.0, neck_r ** 2 - y * y)), 0.99))
    for z in IN_FZ[::-1]:
        rows.append((0.5 + d, z, head_clear_x(z), 0.99))
    G = [[Vector((side * lerp(xs, xe, i / ncol), y, z)) for (y, z, xs, xe) in rows] for i in range(ncol + 1)]
    return G


def build_inner(name, X, mat, lining=None):
    """the inner layer (a waistcoat / jumper / shirt) under the shell: it covers the open front, the katana cutaway at
    the lower front corners, the scooped neckline and the shoulder tops round the neck. Rigid in the Shell piece"""
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        cloth(f"{name}{sd}", inner_grid(side), T_IN, mat, out_hint_torso, mat_in=lining)


def build_hips(name, X, mat):
    """the inner layer's lower front corners, under the shell's katana cutaway (x from HIP_X inside the cutaway edge to
    the side, z -0.72..-0.08): their own piece, so its depth fit hugs each body there (the shell's, set by the chest,
    would push them into the sheathed katana's guard in front of the left hip on the deep bodies)"""
    y = -(0.5 + 0.0045)   # thin and close: on the heavy body the guard's padded back face is 0.01 off the torso here
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        zs = [-0.62, -0.55, -0.48, -0.36, -0.26, -0.20, -0.14, -0.08]   # the hem rises at the sides (a striding
        # leg's top corner pokes out of the torso below about -0.65 there)
        # on the left, below z -0.17 it stops at x 0.755: the corner behind is the sheathed katana's guard's place
        # (x 0.77-1.29, z -0.93..-0.24); a deep body's own depth fit there would push the cloth into it
        xe = (lambda z: 0.755 if z < -0.17 else 0.99) if side > 0 else (lambda z: 0.99)
        G = [[Vector((side * lerp(cut_line(z) - HIP_X + 0.003, xe(z), i / 4), y, z)) for z in zs] for i in range(5)]
        cloth(f"{name}{sd}", G, 0.004, mat, lambda p: Vector((0, -1, 0)))


def inner_front(x, z, lift=0.0):
    return Vector((x, -(0.5 + D_IN + T_IN / 2 + lift), z))


# ================================================================== details
MY_KEYS = ("InvernessCoat", "RainCloak", "LamplighterCoat")


def close_fit(obj, base):
    """A.fit_table samples 400 of a piece's contact points; the inner layer lies 0.004 off the torso, so every one of
    its points counts: raise each body's depth scale until all of them clear that body (by 0.003)"""
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    near = [p for p in pts if abs(p.x) < 0.98 and abs(p.z) < 0.98 and abs(p.y) > 0.3 and abs(p.y) - 0.5 < 0.014]
    out = dict(base)
    for bid in A.BODY_IDS:
        if bid == "standard":
            continue
        need = 0.0
        for p in near:
            d = A.body_depth(bid, "Torso", p.x, p.z, -1 if p.y < 0 else 1)
            if d is not None:
                need = max(need, (d + 0.003) / abs(p.y))
        out[bid] = round(min(1.45, max(out.get(bid, 1.0), need)), 3)
    return out


def shell_fit_hook():
    """a piece named <Key>Cape takes its shell's depth fit (it lies outside the shell: scaled together they keep their
    spacing on every body); this batch's shells and hips clear the body at every inner-layer point (close_fit)"""
    prev = A.fit_table
    cache = {}

    def fit(obj, mount):
        if obj.name.endswith("Cape"):
            sh = bpy.data.objects.get(obj.name[:-4] + "Shell")
            if sh is not None:
                return dict(fit(sh, "Torso"))
        if obj.name in cache:
            return dict(cache[obj.name])
        f = prev(obj, mount)
        if any(obj.name in (k + "Shell", k + "Hips") for k in MY_KEYS):
            f = close_fit(obj, f)
        cache[obj.name] = f
        return dict(f)
    A.fit_table = fit


shell_fit_hook()


def self_check(pairs):
    """--selfcheck: triangle overlaps between groups of this item's parts (name prefixes), at rest"""
    if "--selfcheck" not in sys.argv:
        return
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()

    def group(prefixes):
        V, T = [], []
        for ob in A.PARTS:
            if any(ob.name.startswith(p) for p in prefixes):
                ev = ob.evaluated_get(dg)
                me = ev.to_mesh()
                me.calc_loop_triangles()
                off = len(V)
                V += [ob.matrix_world @ v.co for v in me.vertices]
                T += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
                ev.to_mesh_clear()
        return V, T
    for a, b in pairs:
        Va, Ta = group(a)
        Vb, Tb = group(b)
        if not Ta or not Tb:
            print(f"SELF {a} x {b}: (empty)")
            continue
        ov = BVHTree.FromPolygons(Va, Ta, epsilon=0.0).overlap(BVHTree.FromPolygons(Vb, Tb, epsilon=0.0))
        ex = ""
        for k in range(0, len(ov), max(1, len(ov) // 5)):
            c = sum((Va[i] for i in Ta[ov[k][0]]), Vector()) / 3
            ex += f" ({c.x:.3f}, {c.y:.3f}, {c.z:.3f})"
        print(f"SELF {a} x {b}: {len(ov)}{ex}")


def domed_button(name, at, nrm, mat, r=0.030):
    place(A.lathe(name, [(0.0, 0.019), (r * 0.40, 0.0185), (r * 0.70, 0.0155), (r * 0.80, 0.0170), (r * 0.88, 0.0140),
                         (r * 1.0, 0.007), (r * 0.98, 0.0), (0.0, 0.0)], (0, 0, 0), mat, seg=12), axis_frame(at, nrm))


def flame_button(name, at, nrm, X, r=0.032):
    """a domed brass button with a raised lamp flame"""
    F = axis_frame(at, nrm, x_hint=(1, 0, 0))
    place(A.lathe(name, [(0.0, 0.0145), (r * 0.6, 0.0128), (r * 0.9, 0.0118), (r * 1.0, 0.0070),
                         (r * 0.98, 0.0), (0.0, 0.0)], (0, 0, 0), X["brass"], seg=10), F)
    fl = [(0.0, 0.62), (0.10, 0.34), (0.24, 0.10), (0.27, -0.14), (0.16, -0.36), (0.0, -0.42), (-0.16, -0.36),
          (-0.27, -0.14), (-0.24, 0.10), (-0.08, 0.26), (-0.04, 0.05), (-0.13, 0.18)]
    s = r * 0.95
    # the flame outline lies in the button's local x/y (extrude_poly works in x/z, toward -y): turn it onto the face
    M = F @ Matrix.Translation((0, 0, 0.0128)) @ Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Scale(s, 4)
    A.extrude_poly(name + "Flame", ccw(fl), 0.0055 / s, X["brass"], M, bevel=0.0, segments=1)


# ================================================================== the Inverness cape
CT, CF, CB, CS, CR, T_CAPE = 1.054, 0.574, 0.578, 2.052, 0.062, 0.014   # top z, front |y|, back y, side x, corner r


def zn_back(x, P):
    """the height of the scooped back neckline at x (inverse of build_shell_k's back_neck)"""
    zn, xt = P.get("nape_z", 0.78), P["xo_top"]
    s = min(1.0, (abs(x) / xt) ** 2)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        if t * t * (3 - 2 * t) < s:
            lo = t
        else:
            hi = t
    return zn + (1.0 - zn) * lo


def cape_outline():
    """the left half of the cape's plan outline (the mid-surface of the hanging part), front edge -> centre back:
    [(point2, normal2, kind)]. The corners round the arm's outer edges are superellipses (n 3): as round as the
    sleeve's square corner (2.007, -0.507) lets them be"""
    cx, cy, ne = 1.86, 0.37, 4.0
    rx = CS - cx
    out = []
    for x in (0.74, 0.80, 0.87, 0.96, 1.006, 1.12, 1.30, 1.48, 1.66, 1.86):
        out.append((Vector((x, -CF)), Vector((0, -1)), "front"))

    def corner(a, sy, ry):
        c, s_ = math.cos(a), math.sin(a)
        p = Vector((cx + rx * math.copysign(abs(c) ** (2 / ne), c), sy * cy + ry * math.copysign(abs(s_) ** (2 / ne), s_)))
        g = Vector((math.copysign(abs(c) ** (2 * (ne - 1) / ne), c) / rx, math.copysign(abs(s_) ** (2 * (ne - 1) / ne), s_) / ry))
        return p, g.normalized()
    for k in range(1, 6):
        p, g = corner(math.radians(-90 + 90 * k / 6), -1, CF - cy)
        out.append((p, g, "corner"))
    for y in (-0.37, -0.18, 0.0, 0.18, 0.37):
        out.append((Vector((CS, y)), Vector((1, 0)), "side"))
    for k in range(1, 6):
        p, g = corner(math.radians(90 * k / 6), 1, CB - cy)
        out.append((p, g, "corner"))
    for x in (1.86, 1.66, 1.48, 1.30, 1.12, 1.006, 0.94, 0.86, 0.79, 0.72, 0.685, 0.65, 0.57, 0.47, 0.36, 0.24, 0.12, 0.0):
        out.append((Vector((x, CB)), Vector((0, 1)), "back"))
    return out


def cape_front_x(x, z):
    """the front edge leans in toward the hem (x 0.74 at the top, 0.64 at the hem); the front panel's columns follow"""
    if x >= 0.96:
        return x
    xf = lerp(0.64, 0.74, smooth(0.14, 0.95, z))
    return xf + (x - 0.74) * (0.96 - xf) / (0.96 - 0.74)


def cape_hem(y):
    return lerp(0.14, 0.10, smooth(-0.3, 0.3, y))


def cape_column(Q, n, kind, s_perim, P, R=16):
    """one column of the cape's mid-surface, from the top edge (the neck) to the hem, R+1 points"""
    rn = math.hypot(P["xo_top"], 0.5 + D_F) + 0.006
    th = math.atan2(Q.y, Q.x)
    yc = rn * math.sin(th)
    K = Q - n * CR
    zk = CT - CR
    zh = cape_hem(Q.y)
    path, dens = [], []
    start_z = None
    if abs(yc) <= 0.52 or yc < 0 or Q.x >= 0.76:   # over the shoulder top (clamped at the front / back edge)
        N = Vector((rn * math.cos(th), yc)) if abs(yc) <= 0.52 else Vector((math.sqrt(rn * rn - 0.52 ** 2), math.copysign(0.52, yc)))
        for k in range(9):
            p = N.lerp(K, k / 8)
            path.append(Vector((p.x, p.y, CT))); dens.append(1.0)
    else:
        # down the back: scooped below the shell's own nape (z 0.66 at the centre: short cuts reach the nape at
        # z ~0.73), easing up onto the shoulder top toward x 0.8
        start_z = lerp(P.get("cape_nape", 0.66), CT + 0.01, smooth(0.42, 0.76, Q.x))
    for k in range(0 if not path else 1, 10):
        f = math.radians(90 * k / 9)
        p = K + n * (CR * math.sin(f))
        path.append(Vector((p.x, p.y, zk + CR * math.cos(f)))); dens.append(3.0)
    z = zk
    while z - 0.04 > zh + 0.005:
        z -= 0.04
        path.append(Vector((Q.x, Q.y, z))); dens.append(1.0)
    path.append(Vector((Q.x, Q.y, zh))); dens.append(1.0)
    if start_z is not None:   # a column on the scooped back: it starts on the back face below the neckline
        if start_z < path[0].z:
            k = next(i for i, p in enumerate(path) if p.z <= start_z)
            a, b = path[k - 1], path[k]
            f = (a.z - start_z) / max(1e-9, a.z - b.z)
            path = [a.lerp(b, f)] + path[k:]
            dens = [dens[k]] + dens[k:]
    # resample by density-weighted arc length
    W = [0.0]
    for i in range(1, len(path)):
        W.append(W[-1] + (path[i] - path[i - 1]).length * 0.5 * (dens[i] + dens[i - 1]))
    out = []
    for j in range(R + 1):
        w = W[-1] * j / R
        i = min(len(path) - 2, max(0, next((k for k in range(1, len(W)) if W[k] >= w), len(W) - 1) - 1))
        f = (w - W[i]) / max(1e-9, W[i + 1] - W[i])
        out.append(path[i].lerp(path[i + 1], min(1.0, max(0.0, f))))
    # the hanging part: the front edge leans in; a little flare and soft folds toward the hem (outward only)
    res = []
    n3 = Vector((n.x, n.y, 0))
    for p in out:
        q = p.copy()
        if kind == "front":
            q.x = cape_front_x(Q.x, p.z) if p.z < zk - 0.001 else q.x
        h = smooth(zk - 0.05, zh, p.z) if p.z < zk else 0.0
        fold = 0.0 if (kind == "front" and Q.x < 0.80) else 0.018 * (0.5 - 0.5 * math.cos(2 * math.pi * s_perim / 0.40))
        q += n3 * ((0.085 * h ** 1.3) + fold * h)
        res.append(q)
    return res


def cape_hint(p):
    q = Vector((math.copysign(max(abs(p.x) - 1.9, 0), p.x), math.copysign(max(abs(p.y) - 0.4, 0), p.y), max(p.z - 0.95, 0)))
    return q if q.length > 1e-6 else Vector((0, 0, 1))


def cape_rig(ob):
    bones = [("Root", Vector((0, 0, 0)), Vector((0, 0, 0.08)), None),
             ("F_LA", Vector((1.5, 0, 0.5)), Vector((1.5, 0, 0.2)), "Root"),
             ("F_RA", Vector((-1.5, 0, 0.5)), Vector((-1.5, 0, 0.2)), "Root")]

    def wfn(co):   # over an arm (|x| >= 1) the cape rides it entirely; over the torso it stays
        if co.x >= 1.0:
            return {"F_LA": 1.0}
        if co.x <= -1.0:
            return {"F_RA": 1.0}
        return {"Root": 1.0}
    return A.make_rig(ob, bones, wfn), bones


def build_cape(name, P, X):
    outl = cape_outline()
    s, prev = 0.0, None
    cols = []
    for Q, n, kind in outl:
        if prev is not None:
            s += (Q - prev).length
        prev = Q
        cols.append(cape_column(Q, n, kind, s, P))
    mir = [[Vector((-p.x, p.y, p.z)) for p in c] for c in cols]
    G = mir + list(reversed(cols))[1:]
    pn = [Vector((-n.x, n.y)) for _, n, _ in outl] + [n for _, n, _ in reversed(outl)][1:]   # each column's plan normal
    cloth(name + "Body", G, T_CAPE, X["wool"], cape_hint, mat_in=X["lining"])
    nI, nJ = len(G), len(G[0])
    o = T_CAPE / 2

    def outw(i, j, k):
        c = G[i][j]
        nn = (G[min(i + 1, nI - 1)][j] - G[max(i - 1, 0)][j]).cross(G[i][min(j + 1, nJ - 1)] - G[i][max(j - 1, 0)])
        nn.normalize()
        if nn.dot(cape_hint(c)) < 0:
            nn = -nn
        return c + nn * k
    # the binding: round the hem and up both front edges
    wire(name + "Hem", [tuple(G[i][-1] + Vector((0, 0, 0.001))) for i in range(nI)], 0.0095, X["pipe"], sides=5)
    for i, nm in ((0, "R"), (nI - 1, "L")):
        wire(name + "Edge" + nm, [tuple(G[i][j]) for j in range(nJ)], 0.0095, X["pipe"], sides=5)
    # top-stitching above the hem
    wire(name + "Stitch", [tuple(outw(i, nJ - 2, o + 0.0012)) for i in range(1, nI - 1)], 0.0024, X["thread"], sides=4)
    # the collar, along the top edge
    rows = []
    half = (nI - 1) / 2
    for i in range(nI):
        E = G[i][0]
        tin = (G[i][1] - G[i][0]).normalized()
        side = G[min(i + 1, nI - 1)][0] - G[max(i - 1, 0)][0]
        # the cape's outward normal at its edge: up on the shoulder top, round the corner's arc, level on the drop
        zk = CT - CR
        f = math.acos(max(-1.0, min(1.0, (E.z - zk) / CR))) if E.z > zk else math.pi / 2
        nn = Vector((pn[i].x * math.sin(f), pn[i].y * math.sin(f), math.cos(f))).normalized()
        if E.z > CT - 0.002:
            nn = Vector((0, 0, 1))
        ep = side.normalized().cross(nn).normalized()   # in the cape's surface, square to its edge, outward
        if ep.dot(-tin) < 0:
            ep = -ep
        tw = max(0.0, min(1.0, nn.z))
        e = (-tin).lerp(ep, 1 - tw).normalized()   # down the slanting back edge: square to it
        tk = tw * smooth(0.47, 0.36, abs(E.y))
        fr = smooth(0.0, 0.18, min(i, nI - 1 - i) / half)
        b0 = E + e * lerp(lerp(-0.006, 0.030, tw), 0.045, tk) + nn * lerp(lerp(-0.033, 0.006, tw), -0.027, tk)
        bm = E + e * lerp(0.034, 0.020, tw) + nn * lerp(0.010, 0.022, tw)
        b1 = E + e * (-0.012) + nn * 0.024
        up = Vector((0, 0, 1))
        rad = Vector((E.x, E.y, 0)).normalized()
        rise, reach = P["collar_rise"], P["collar_reach"]
        S1 = b1 + up * (0.030 * fr + 0.006) + rad * 0.006
        C1 = b1 + up * (rise * fr + 0.010) + rad * lerp(0.020, 0.040, fr)
        F1 = b1 + up * (rise * 0.75 * fr + 0.009) + rad * lerp(0.030, reach * 0.62, fr)
        O1 = b1 + up * 0.010 + rad * lerp(0.040, reach, fr)
        S2 = b1 + nn * 0.004 + e * 0.004
        C2 = b1 + nn * 0.016 + e * 0.014
        F2 = b1 + nn * 0.026 + e * 0.004
        O2 = b1 + nn * 0.020 - e * P["collar_back"]
        rows.append([b0, bm, b1, S2.lerp(S1, tw), C2.lerp(C1, tw), F2.lerp(F1, tw), O2.lerp(O1, tw)])

    def chint(p):
        return Vector((p.x, p.y, 0)).normalized() * 0.5 + Vector((0, 0, 0.9))
    cloth(name + "Collar", rows, 0.012, X["collar"], chint)
    wire(name + "CollarEdge", [tuple(r[-1]) for r in rows], P["pipe_r"] * 0.9, X["collar"], sides=5)
    return G


def cravat(name, mat, X):
    """a silk cravat at the throat: a soft knot and two falls lying on the waistcoat"""
    A.sphere(name + "Knot", 0.052, tuple(inner_front(0.0, 0.848, 0.021)), mat, scale=(1.0, 0.42, 0.78), seg=12, rings=8)
    for s_ in (-1, 1):
        G = []
        for i in range(4):
            u = i / 3
            col = []
            for z in (0.83, 0.76, 0.68, 0.60, 0.54):
                t = (0.83 - z) / 0.29
                w = lerp(0.035, 0.060, t)
                xc = s_ * lerp(0.012, 0.030, t)
                col.append(inner_front(xc + (u - 0.5) * w * 2 * 0.5, z, 0.0045 + 0.004 * (1 - t) + 0.002 * (s_ > 0)))
            G.append(col)
        cloth(f"{name}Fall{'L' if s_ > 0 else 'R'}", G, 0.005, mat, lambda p: Vector((0, -1, 0)))


# ================================================================== the Inverness cape-coat
def inverness_mats(M):
    X = dict(
        wool=mat_houndstooth("InvernessTooth", (0.012, 0.012, 0.014), (0.16, 0.155, 0.15)),
        lining=M["crimson_silk"], velvet=M["black_velvet"],
        thread=A.mat_cloth("BlackThread", (0.03, 0.028, 0.03), weave=900, rough=0.6, sheen=0.2, bump=0.05, twill=False),
        horn=mat_horn(), brass=M["brass"], bone=M["bone"], strap=M["leather_black"], btn="silver",
        vest=A.mat_cloth("InvernessVest", (0.016, 0.015, 0.019), weave=520, rough=0.45, sheen=0.4, bump=0.04, twill=False,
                         stripe=((0.16, 0.016, 0.03), 0.055, 0.005, 0)))
    X.update(silver=X["horn"], collar=X["velvet"], lapel=X["wool"], pipe=X["velvet"], collar_pipe=X["velvet"],
             cuff=X["velvet"], cuff_pipe=X["velvet"])
    return X


def inverness_params():
    P = dict(xo_top=0.72, xo_break=0.36, brk=0.18, v_pow=1.0, collar_rise=0.035, collar_reach=0.11, collar_back=0.03,
             nape_z=0.78, pipe_r=0.0055, back_folds=0.006, cuff="turnback", skirt_bot=-2.10, skirt_flare=0.09,
             skirt_vent=0.03)
    P["break"] = P["brk"]
    P["skirt_open"] = lambda z: P["xo_break"] + 0.02 + 0.10 * smooth(-0.9, P["skirt_bot"], z)
    return P


@item("InvernessCoat", "Inverness cape-coat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.35, 0, 0.30), 85))
def build_inverness(M):
    key = "InvernessCoat"
    X, P = inverness_mats(M), inverness_params()
    piece(f"{key}Shell", "Torso")
    build_shell_c(key, P, X, collar=False, seam_shoulder=False)
    # the waistcoat under it (black silk, a crimson pinstripe), horn buttons, a crimson silk cravat
    build_inner(f"{key}Vest", X, X["vest"], X["lining"])
    for k, z in enumerate((0.42, 0.20, -0.02, -0.24, -0.46)):
        domed_button(f"{key}VestBtn{k}", inner_front(0.0, z), (0, -1, 0), X["horn"], r=0.020)
    cravat(f"{key}Cravat", X["lining"], X)
    for s in (1, -1):   # horn buttons below the cape, both fronts; worked holes on the left
        for k, z in enumerate((-0.02, -0.22, -0.42)):
            domed_button(f"{key}Btn{s}{k}", front_point(s * 0.42, z), (0, -1, 0), X["horn"], r=0.028)
    for k, z in enumerate((-0.02, -0.22, -0.42)):
        wire(f"{key}Hole{k}", [tuple(front_point(x, z + 0.034, 0.002)) for x in (0.39, 0.42, 0.45)], 0.0040, X["thread"], sides=4)
    for s in (1, -1):
        pocket_flap(f"{key}Pocket{'L' if s > 0 else 'R'}", s, -0.26, X, X["wool"], pipe=X["velvet"])
    half_belt(f"{key}HalfBelt", -0.40, X, X["wool"], P, w=0.07, x1=0.60)
    for s in (-1, 1):
        domed_button(f"{key}BeltBtn{s}", back_point(s * 0.55, -0.40, 0.0125), (0, 1, 0), X["horn"], r=0.028)
    hips_extra = C1.add_hips(key, P, X, X["vest"])   # the hip corners, both sides (C1.build_hips: split, own fits)
    piece(f"{key}Cape", "Torso", rig=cape_rig)
    build_cape(f"{key}Cape", P, X)
    piece(f"{key}Skirt", "Torso", rig=skirt_rig)
    build_skirt(f"{key}Skirt", P, X)
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve_k(f"{key}SleeveL", P, X)
    self_check([((f"{key}CapeBody",), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Seam")),
                ((f"{key}CapeCollar",), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Seam")),
                ((f"{key}CapeCollar",), (f"{key}CapeBody", f"{key}CapeEdge")),
                ((f"{key}Cape",), (f"{key}SleeveL",)),
                ((f"{key}HipsUp", f"{key}HipsLo"), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Vest", f"{key}Pocket", f"{key}Btn")),
                ((f"{key}Vest", f"{key}Cravat"), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Seam", f"{key}Cape",
                                                 f"{key}Btn", f"{key}Pocket", f"{key}Hole"))])
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    write_extra(key, hips_extra)
    write_extra(key, {f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}Cape": {"follow": "LA=1;RA=1"},
                      f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}})
    return dict(notes="the Inverness cape-coat: black houndstooth wool, crimson silk lining, black velvet collar and "
                      "cuffs, horn buttons; an elbow-length shoulder cape open at the front (over the arms it rides "
                      "them: BodyFollow F_LA / F_RA) and knee-length skirts that move with the legs")


# ================================================================== the oilskin rain cloak
def toggle(name, at, X, L=0.125, r=0.018):
    """a horn toggle (upright), waisted where the cords hold it"""
    prof = [(0.0, -L / 2), (r * 0.45, -L / 2 + 0.002), (r * 0.82, -L / 2 + 0.012), (r, -L / 4), (r * 0.86, 0.0),
            (r, L / 4), (r * 0.82, L / 2 - 0.012), (r * 0.45, L / 2 - 0.002), (0.0, L / 2)]
    ob = A.lathe(name, prof, (0, 0, 0), X["horn"], seg=8)
    place(ob, Matrix.Translation(at))


def leather_patch(name, x, z, w, h, X, lift=0.0):
    pts = [(x - w / 2, z), (x - w / 2 + 0.012, z + h / 2), (x + w / 2 - 0.012, z + h / 2), (x + w / 2, z),
           (x + w / 2 - 0.012, z - h / 2), (x - w / 2 + 0.012, z - h / 2)]
    A.extrude_poly(name, ccw(pts), 0.006, X["strap"], Matrix.Translation((0, -(Y_OUT + 0.0008 + lift), 0)), bevel=0.0015,
                   segments=1)
    wire(name + "St", [(x - w / 2 + 0.010, -(Y_OUT + lift + 0.007), z), (x + w / 2 - 0.010, -(Y_OUT + lift + 0.007), z)],
         0.0016, X["thread"], sides=4)


def toggle_set(name, z, X, xt=-0.17, xa=0.215):
    """a horn toggle on the wearer's right front, fixed by a cord stay to a leather patch; a doubled cord loop from a
    patch on the left front crosses the opening behind the toggle and wraps round its far side"""
    yc = -(Y_OUT + 0.016)           # the loop's cords, clear of the front edge's piping
    yt = -(Y_OUT + 0.040)           # the toggle's axis
    toggle(name + "Tog", Vector((xt, yt, z)), X)
    cr = 0.0045
    ya = -(Y_OUT + 0.0008 + 0.006 + cr)   # sewn down on the left patch
    loop = [(xa + 0.022, ya, z + 0.004), (xa + 0.012, ya, z + 0.010), (xa - 0.03, ya, z + 0.010), (0.125, yc, z + 0.010),
            (xt + 0.04, yc, z + 0.010), (xt - 0.022, yc, z + 0.010), (xt - 0.034, yc - 0.004, z + 0.006),
            (xt - 0.038, yc - 0.008, z), (xt - 0.034, yc - 0.004, z - 0.006), (xt - 0.022, yc, z - 0.010),
            (xt + 0.04, yc, z - 0.010), (0.125, yc, z - 0.010), (xa - 0.03, ya, z - 0.010), (xa + 0.012, ya, z - 0.010),
            (xa + 0.022, ya, z - 0.004)]
    wire(name + "Loop", loop, cr, X["cord"], sides=5)
    leather_patch(name + "PatchL", xa + 0.004, z, 0.085, 0.050, X)
    wire(name + "Tack", [(xa - 0.012, ya - 0.0035, z + 0.016), (xa - 0.012, ya - 0.0035, z - 0.016)], 0.0022, X["thread"], sides=4)
    leather_patch(name + "PatchR", xt - 0.105, z, 0.070, 0.044, X)
    wire(name + "Stay", [(xt - 0.090, -(Y_OUT + 0.0068), z), (xt - 0.065, -(Y_OUT + 0.024), z + 0.002),
                         (xt - 0.042, yt + 0.0005, z + 0.001), (xt - 0.004, yt, z)], 0.0042, X["cord"], sides=6)


def bell_sleeve(name, P, X, flare=0.12):
    """Kit C's full sleeve (build_sleeve_k: the whole arm to the wrist, the front and back faces to the inner edge)
    widening to a bell below the elbow: the U-profile is pushed out along its normal, a little less toward the inner
    edge"""
    zs = [SLV_CUFF, SLV_CUFF + 0.02] + [z for z in (-0.50, -0.45, -0.40, -0.34, -0.28, -0.21, -0.14, -0.06, 0.02, 0.10,
                                                    0.20, 0.32, 0.46, 0.62, 0.76, 0.88, 0.96, 1.0) if z > SLV_CUFF + 0.04]
    d = 0.020
    kw = wrap_kw()
    rowsP = []
    for z in zs:
        ease = 0.003 * math.sin(math.pi * smooth(-0.8, 0.9, z))
        prof = arm_wrap(d + ease, x_in=slv_xin(z), **kw)
        ex = flare * smooth(0.20, SLV_CUFF, z) ** 1.5
        row = []
        for k, (X_, Y_) in enumerate(prof):
            a, b = prof[max(k - 1, 0)], prof[min(k + 1, len(prof) - 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            L = math.hypot(tx, ty)
            nx, ny = ty / L, -tx / L
            if nx * X_ + ny * Y_ < 0:
                nx, ny = -nx, -ny
            g = lerp(0.35, 1.0, smooth(-0.36, 0.35, X_))   # least toward the inner front (the katana's guard)
            row.append(Vector((1.5 + X_ + nx * ex * g, Y_ + ny * ex * g, z)))
        rowsP.append(row)
    E0 = arm_wrap(0.0, x_in=SLV_XIN, **kw)
    Ed = arm_wrap(d, x_in=SLV_XIN, **kw)
    for a in (35, 70):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rowsP.append([Vector((1.5 + e[0] + (f[0] - e[0]) * c, e[1] + (f[1] - e[1]) * c, 1.0 + d * s_)) for e, f in zip(E0, Ed)])
    n = len(E0)
    T = [(SLV_XIN + 0.01, lerp(-0.40, 0.40, k / (n - 1))) for k in range(n)]
    for f in (0.0, 0.3, 0.6, 1.0):
        rowsP.append([Vector((1.5 + lerp(E0[k][0], T[k][0], f), lerp(E0[k][1], T[k][1], f), 1.0 + d)) for k in range(n)])
    G = [[rowsP[j][k] for j in range(len(rowsP))] for k in range(n)]
    cloth(name + "Body", G, 0.014, X["wool"], sleeve_hint, mat_in=X["lining"])

    def outv(c, k):
        return c + (Vector((c.x - 1.5, c.y, 0))).normalized() * k
    wire(name + "Hem", [tuple(outv(c[0], 0.002)) for c in G], 0.0085, X["pipe"], sides=5)
    wire(name + "Stitch", [tuple(outv(c[2], 0.0085)) for c in G[1:-1]], 0.0024, X["thread"], sides=4)
    seam = [Vector((1.5 + 0.10, 0.5 + 0.020 + 0.0085, z)) for z in (0.0, 0.3, 0.8, 0.97)]
    wire(name + "Seam", [tuple(p) for p in seam], 0.0032, X["thread"], sides=4)
    return G


def build_hood(name, P, X):
    """the hood worn down: a flat pouch on the upper back, its top edge just below the collar's fall along the
    scooped neckline, thin at the rims and softly full in the middle, falling to a soft point (the crown); its face
    opening lies turned back along the top (a band of lining), the crown seam runs down its centre"""
    edge = collar_edge_back(P)   # [(x, z)] of the collar's lower edge

    def ztop(x):
        x = abs(x)
        if x <= edge[0][0]:
            return edge[0][1] - 0.008
        for (x0, z0), (x1, z1) in zip(edge, edge[1:]):
            if x0 <= x <= x1:
                return lerp(z0, z1, (x - x0) / max(1e-9, x1 - x0)) - 0.008
        return edge[-1][1] - 0.008
    nu, nv = 14, 12
    y0 = Y_OUT + 0.0035     # the inner face

    def W(v):
        return lerp(0.37, 0.05, smooth(0.40, 1.0, v) ** 1.2) + 0.03 * math.sin(math.pi * min(1.0, v / 0.75))

    def thick(u, v):
        uu = 2 * u - 1
        t = 0.0045 + 0.028 * math.sqrt(max(0.0, 1 - uu * uu)) * smooth(0.0, 0.22, v) * (1 - 0.45 * smooth(0.65, 1.0, v))
        return t * (1 - 0.28 * math.exp(-(uu / 0.08) ** 2))
    G = []
    for i in range(nu + 1):
        uu = 2 * i / nu - 1
        col = []
        for j in range(nv + 1):
            v = j / nv
            x = uu * W(v)
            z = lerp(ztop(x), 0.20 + 0.10 * uu * uu, v)
            col.append(Vector((x, y0 + thick(i / nu, v) / 2, z)))
        G.append(col)
    cloth(name, G, thick, X["wool"], lambda p: Vector((0, 1, 0)), mat_in=X["lining"])

    def outer(i, j, k=0.0):
        return G[i][j] + Vector((0, thick(i / nu, j / nv) / 2 + k, 0))
    # the face opening turned back along the top: a band of lining lying on the hood
    Gb = [[outer(i, j, 0.0012 + 0.0012 * (j == 1)) for j in (0, 1, 2)] for i in range(1, nu)]
    cloth(name + "Opening", Gb, 0.003, X["lining"], lambda p: Vector((0, 1, 0)))
    wire(name + "OpeningEdge", [tuple(outer(i, 2, 0.003)) for i in range(1, nu)], 0.0040, X["pipe"], sides=5)
    # the binding round the sides and the point, the crown seam
    rim = [G[0][j] for j in range(1, nv + 1)] + [G[i][nv] for i in range(1, nu)] + [G[nu][j] for j in range(nv, 0, -1)]
    wire(name + "Rim", [tuple(p + Vector((0, 0.0005, 0))) for p in rim], 0.0055, X["pipe"], sides=5)
    ic = nu // 2
    wire(name + "Seam", [tuple(outer(ic, j, 0.0008)) for j in range(3, nv)], 0.0030, X["thread"], sides=4)
    return G


def raincloak_mats(M):
    X = dict(
        wool=mat_oilskin("Oilskin", (0.017, 0.020, 0.012), rough=0.42, coat=0.32, crease=0.20),
        lining=A.mat_cloth("OliveCotton", (0.045, 0.048, 0.030), weave=420, rough=0.88, sheen=0.25, bump=0.06, twill=True),
        thread=A.mat_cloth("WaxThread", (0.05, 0.05, 0.035), weave=900, rough=0.55, sheen=0.2, bump=0.05, twill=False),
        cord=A.mat_cloth("WaxCord", (0.11, 0.085, 0.055), weave=700, rough=0.6, sheen=0.25, bump=0.10, twill=True),
        horn=mat_horn(), strap=M["leather_brown"], brass=M["brassold"], bone=M["bone"], btn="silver",
        knit=A.mat_cloth("OliveKnit", (0.040, 0.044, 0.028), weave=150, rough=0.92, sheen=0.3, bump=0.22, twill=False))
    X.update(silver=X["horn"], collar=X["wool"], lapel=X["wool"], pipe=X["wool"], collar_pipe=X["wool"], cuff=X["wool"],
             cuff_pipe=X["wool"])
    return X


def raincloak_params():
    P = dict(xo_top=0.72, xo_break=0.10, brk=0.62, v_pow=1.15, collar_rise=0.035, collar_reach=0.11, collar_back=0.03,
             nape_z=0.78, pipe_r=0.006, back_folds=0.008, cuff="none", skirt_bot=-2.40, skirt_flare=0.11, skirt_vent=0.03)
    P["break"] = P["brk"]
    P["skirt_open"] = lambda z: P["xo_break"] + 0.02 + 0.12 * smooth(-0.9, P["skirt_bot"], z)
    return P


@item("RainCloak", "Oilskin rain cloak", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.0, 0, 0.30), 85))
def build_raincloak(M):
    key = "RainCloak"
    X, P = raincloak_mats(M), raincloak_params()
    piece(f"{key}Shell", "Torso")
    build_shell_c(key, P, X, collar=True, seam_back_top=0.14)
    build_inner(f"{key}Jumper", X, X["knit"])   # an olive knit jumper under it
    for k, z in enumerate((0.44, 0.18, -0.08, -0.34)):
        toggle_set(f"{key}T{k}", z, X)
    for s in (1, -1):
        pocket_flap(f"{key}Pocket{'L' if s > 0 else 'R'}", s, -0.40, X, X["wool"], pipe=X["thread"])
        domed_button(f"{key}PocketBtn{s}", front_point(s * 0.57, -0.46, 0.010), (0, -1, 0), X["horn"], r=0.022)
    build_hood(f"{key}Hood", P, X)
    hips_extra = C1.add_hips(key, P, X, X["knit"])   # the hip corners, both sides (C1.build_hips: split, own fits)
    piece(f"{key}Skirt", "Torso", rig=skirt_rig)
    build_skirt(f"{key}Skirt", P, X)
    piece(f"{key}SleeveL", "LeftArm")
    bell_sleeve(f"{key}SleeveL", P, X, flare=0.12)
    self_check([((f"{key}Hood",), (f"{key}Collar", f"{key}Body", f"{key}Seam")),
                ((f"{key}T",), (f"{key}Body", f"{key}Pipe", f"{key}Collar", f"{key}Jumper")),
                ((f"{key}HipsUp", f"{key}HipsLo"), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Jumper", f"{key}Pocket", f"{key}T")),
                ((f"{key}Jumper",), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Seam", f"{key}Collar", f"{key}Pocket"))])
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    write_extra(key, dict(hips_extra, **{f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}))
    return dict(notes="the oilskin rain cloak: olive-black waxed cotton, an olive lining, horn toggles on waxed cord "
                      "loops, bell sleeves, the hood worn down flat on the back; mid-calf skirts that move with the legs")


# ================================================================== the lamplighter's coat
def storm_flap(name, X):
    """a storm flap buttoned across the chest over the coat's V opening"""
    x0, x1, z0, z1 = -0.56, 0.60, 0.44, 0.955
    yf = -(Y_OUT + 0.017)   # clear of the front edges' piping (outer face 0.5415)
    nu, nv = 14, 6
    G = [[Vector((lerp(x0, x1, i / nu), yf, lerp(z0, z1, j / nv))) for j in range(nv + 1)] for i in range(nu + 1)]
    cloth(name, G, 0.011, X["wool"], lambda p: Vector((0, -1, 0)), mat_in=X["lining"])
    o = 0.0055 + 0.0012
    rim = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    wire(name + "Edge", [(x, yf, z) for x, z in rim], 0.0060, X["pipe"], sides=5, closed=True)
    ins = 0.028
    wire(name + "Stitch", [(x0 + ins, yf - o, z0 + ins), (x1 - ins, yf - o, z0 + ins), (x1 - ins, yf - o, z1 - ins),
                           (x0 + ins, yf - o, z1 - ins)], 0.0022, X["thread"], sides=4, closed=True)
    for k, (x, z) in enumerate(((0.54, 0.89), (0.54, 0.70), (0.54, 0.51), (-0.50, 0.89), (-0.50, 0.51))):
        flame_button(f"{name}Btn{k}", Vector((x, yf - 0.0055, z)), (0, -1, 0), X, r=0.030)


def lamp_hook(name, X, x0=-0.60):
    """a brass lamp hook on a leather tab at the right hip, flat against the coat's front"""
    yt = -(Y_OUT + 0.0045)
    G = [[Vector((x0 + dx, yt, z)) for z in (-0.452, -0.40, -0.33, -0.272)] for dx in (-0.032, 0.0, 0.032)]
    cloth(name + "Tab", G, 0.008, X["strap"], lambda p: Vector((0, -1, 0)))
    for k, z in enumerate((-0.30, -0.40)):
        A.sphere(f"{name}Rivet{k}", 0.0085, (x0, yt - 0.004, z), X["brass"], scale=(1, 0.55, 1), seg=8, rings=5)
    wire(name + "TabSt", [(x0 + dx, yt - 0.0042, z) for dx, z in ((-0.024, -0.285), (-0.024, -0.44), (0.024, -0.44),
                                                                   (0.024, -0.285))], 0.0018, X["thread"], sides=4, closed=True)
    yr = -(Y_OUT + 0.030)
    A.cyl(name + "Keeper", 0.0125, 0.052, (x0, yr, -0.450), X["strap"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.0)
    Gf = [[Vector((x0 + dx, y, z)) for y, z in ((yt, -0.446), (-0.548, -0.4545), (-0.559, -0.4625))] for dx in (-0.024, 0.0, 0.024)]
    cloth(name + "Fold", Gf, 0.006, X["strap"], lambda p: Vector((0, -1, 0.3)))
    A.torus(name + "Ring", 0.026, 0.0055, (x0, yr, -0.476), X["brass"], rot=(math.pi / 2, 0, 0), major=18, minor=6)
    zb = -0.476 - 0.026
    A.torus(name + "Eye", 0.013, 0.0045, (x0, yr, zb), X["brass"], rot=(0, math.pi / 2, 0), major=12, minor=5)
    hook = [(x0, yr, zb - 0.013), (x0, yr, zb - 0.05), (x0 + 0.002, yr, zb - 0.09), (x0 + 0.014, yr, zb - 0.112),
            (x0 + 0.032, yr, zb - 0.105), (x0 + 0.040, yr, zb - 0.082), (x0 + 0.037, yr, zb - 0.064)]
    wire(name + "Hook", hook, 0.0058, X["brass"], sides=6)
    A.sphere(name + "Tip", 0.0072, hook[-1], X["brass"], seg=8, rings=5)


def lamplighter_mats(M):
    X = dict(
        wool=mat_oilskin("Oilcloth", (0.026, 0.017, 0.011), rough=0.38, coat=0.38, crease=0.18, wax=0.14),
        lining=A.mat_cloth("UmberTwill", (0.10, 0.055, 0.030), weave=380, rough=0.86, sheen=0.3, bump=0.07, twill=True),
        thread=A.mat_cloth("UmberThread", (0.16, 0.10, 0.05), weave=900, rough=0.55, sheen=0.2, bump=0.05, twill=False),
        brass=M["brass"], strap=M["leather_brown"], bone=M["bone"], btn="silver",
        vest=A.mat_cloth("UmberVest", (0.085, 0.045, 0.022), weave=300, rough=0.82, sheen=0.35, bump=0.08, twill=True))
    X.update(silver=X["brass"], collar=X["wool"], lapel=X["wool"], pipe=X["wool"], collar_pipe=X["brass"],
             cuff=X["wool"], cuff_pipe=X["thread"])
    return X


def lamplighter_params():
    P = dict(xo_top=0.72, xo_break=0.08, brk=0.82, v_pow=1.0, collar_rise=0.035, collar_reach=0.11, collar_back=0.03,
             nape_z=0.78, pipe_r=0.0055, back_folds=0.008, cuff="turnback", skirt_bot=-2.50, skirt_flare=0.11,
             skirt_vent=0.03)
    P["break"] = P["brk"]
    P["skirt_open"] = lambda z: P["xo_break"] + 0.02 + 0.12 * smooth(-0.9, P["skirt_bot"], z)
    return P


@item("LamplighterCoat", "Lamplighter's coat", views=["front34", "front", "side", "back", "close"],
      close=((2.4, -6.2, 0.4), (-0.3, 0, 0.10), 85))
def build_lamplighter(M):
    key = "LamplighterCoat"
    X, P = lamplighter_mats(M), lamplighter_params()
    piece(f"{key}Shell", "Torso")
    build_shell_c(key, P, X, collar=True)
    build_inner(f"{key}Vest", X, X["vest"], X["lining"])   # an umber waistcoat under it, small brass buttons
    for k, z in enumerate((0.30, 0.08, -0.14, -0.36)):
        domed_button(f"{key}VestBtn{k}", inner_front(0.0, z), (0, -1, 0), X["brass"], r=0.018)
    storm_flap(f"{key}Flap", X)
    for s in (1, -1):   # brass flame buttons down both fronts below the flap
        for k, z in enumerate((0.24, -0.06, -0.36)):
            flame_button(f"{key}Btn{s}{k}", front_point(s * 0.17, z), (0, -1, 0), X, r=0.030)
    pocket_flap(f"{key}PocketL", 1, -0.30, X, X["wool"], pipe=X["thread"])
    lamp_hook(f"{key}Hook", X)
    half_belt(f"{key}HalfBelt", -0.32, X, X["wool"], P, w=0.075, x1=0.60)
    for s in (-1, 1):
        flame_button(f"{key}BeltBtn{s}", back_point(s * 0.55, -0.32, 0.0125), (0, 1, 0), X, r=0.028)
    hips_extra = C1.add_hips(key, P, X, X["vest"])   # the hip corners, both sides (C1.build_hips: split, own fits)
    piece(f"{key}Skirt", "Torso", rig=skirt_rig)
    build_skirt(f"{key}Skirt", P, X)
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve_k(f"{key}SleeveL", P, X)
    self_check([((f"{key}Flap",), (f"{key}Body", f"{key}Pipe", f"{key}Collar", f"{key}Btn")),
                ((f"{key}Hook",), (f"{key}Body", f"{key}Pipe")),
                ((f"{key}HipsUp", f"{key}HipsLo"), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Vest", f"{key}Pocket", f"{key}Hook")),
                ((f"{key}Vest",), (f"{key}Body", f"{key}Band", f"{key}Pipe", f"{key}Seam", f"{key}Collar", f"{key}Btn",
                                   f"{key}Flap", f"{key}Pocket"))])
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    write_extra(key, dict(hips_extra, **{f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True}}))
    return dict(notes="the lamplighter's coat: brown-black oilcloth, an umber twill lining, a storm flap buttoned "
                      "across the chest in brass flame buttons, a brass lamp hook on a leather tab at the right hip, "
                      "turned-up cuffs; long skirts that move with the legs")
