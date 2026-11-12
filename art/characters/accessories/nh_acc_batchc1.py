"""Accessories batch C1 (Kit C, "The Night School Wardrobe"): the coats and jackets.

Kit C coats are rigged for the R6 body's movement (owner: "make sure all the 3d accessories and clothes are all rigged
for fluent movement with the R6 character"):
  <Coat>Shell     Torso: the body of the coat (Kit A's coat shell: front panels, lapels, collar, the bands under the
                  arms). Rigid on the torso.
  <Coat>SleeveL/R LeftArm / RightArm: each wraps its arm and follows the arm swing exactly (Kit A's sleeve).
  <Coat>Skirt     Torso, skinned (BodyFollow): the coat's skirts below the waist. Each half wraps one leg (front,
                  outer side, back; the inner face is open, the two legs touch) and is weighted to that leg's follow
                  bone F_LL / F_RL entirely: it moves exactly as its leg does, so a long skirt moves with the stride
                  instead of the legs passing through it. (A skirt blended between the torso and the leg can't work on
                  R6: the leg turns about the hip line at the torso's bottom centre, so its front face swings further
                  than any part-turned cloth in front of it and comes through it, and cloth above the hip line turns
                  the wrong way. Like the leg's own top, the skirt's top edge slides into the torso as the leg swings
                  forward, and drops below the coat's hem as it swings back.)
                  Controllers.Character.BodyFollow turns the bones in the game; acc_check.py bends the skirt the same
                  way through the whole swing.
The skirt's halves part at the front opening and at a centre-back vent (the legs swing in opposite phase). The outer
side hugs the leg (mid-surface 1.022, outer face under 1.03): the sheathed katana's scabbard runs back along the left
side at x >= 1.04.

Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batchc1 --gpu
"""
import json, math, os
import bpy
from mathutils import Vector, Matrix
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import ccw
from nh_acc_batch4 import wire, axis_frame, place, mirror_piece
import nh_acc_batch7 as K7
from nh_acc_batch7 import cloth, build_shell, build_sleeve, front_point, back_point, half_belt, pocket_flap, D_F, T_SHELL

# the skirt
SK_TOP = -0.73          # the skirt's top edge, just below the shell's hem (-0.72): the two have their own depth fits
                        # (the skirt's from the legs), so they meet edge to edge rather than overlap. Riding the leg, it
                        # turns about the hip line (z -1): 0.27 above it, its forward sweep as the leg swings back stays
                        # behind the sheathed katana's guard (its back face at y -0.68, x >= 0.77, z above -0.93)
SK_OFF_TOP = 0.046      # its mid-surface off the torso at the top (outside the shell: 0.024 + 0.008 + clearance)
SK_SIDE = 0.024         # the outer side's mid-surface off the leg (outer face 1.0305; the scabbard is outside 1.04)
T_SKIRT = 0.013


def corner(deg, sy, off, n=3.2):
    """a point on the skirt's rounded corner round the leg's vertical edge (a superellipse: it keeps its clearance
    off the leg's corner, which is rounded on the meshed bodies)"""
    a = math.radians(deg)
    rx, ry = 0.06 + SK_SIDE, (0.5 + off) - 0.44
    c, s_ = math.cos(a), math.sin(a)
    return Vector((0.94 + rx * math.copysign(abs(c) ** (2 / n), c), sy * 0.44 + ry * math.copysign(abs(s_) ** (2 / n), s_)))


SL_X = 0.70     # the front-outer slit: the front panel ends at x 0.70 ...
SL_Y = -0.30    # ... and the side panel starts at y -0.30, from the waist down to SL_JOIN, where they join to the hem.
SL_JOIN = -1.80
# Why: riding the leg, cloth over the thigh's front-outer corner swings up into the sheathed katana's guard as the leg
# swings forward (the guard sits just in front of the left hip: x 0.77-1.29, z -0.93..-0.24, its back face at y -0.68;
# acc_check found every body type hitting it at +44..+55 degrees). Below z -1.76 a point can't rise to the guard at any
# swing, so the panels join there. The right side is cut the same way, for the look.


def skirt_plan(side, z, P):
    """the skirt's plan path at height z round one leg (x > 0 for the left), front opening to the back vent, and the
    indices of the slit's two edges (ia: the front panel's outer edge at x SL_X; ib: the side panel's front edge at
    y SL_Y). Front and back stand off by `off` (flaring toward the hem), the side by SK_SIDE."""
    zb = P["skirt_bot"]
    t = smooth(SK_TOP, zb, z)
    off = lerp(SK_OFF_TOP, P["skirt_flare"], t ** 1.4)
    xo = P["skirt_open"](z)
    xv = P["skirt_vent"]
    pts = []
    for k in range(7):
        pts.append(Vector((lerp(xo, SL_X, k / 6), -(0.5 + off))))
    ia = len(pts) - 1
    for k in range(1, 3):
        pts.append(Vector((lerp(SL_X, 0.94, k / 3), -(0.5 + off))))
    for k in range(5):   # a squared (superellipse) corner from (0.94, -(0.5+off)) to (1+SK_SIDE, -0.44)
        pts.append(corner(-90 + 90 * k / 4, -1, off))
    side_y = [-0.37, SL_Y, -0.15, 0.0, 0.15, 0.30, 0.37]
    for y in side_y:
        pts.append(Vector((1.0 + SK_SIDE, y)))
        if y == SL_Y:
            ib = len(pts) - 1
    for k in range(5):
        pts.append(corner(90 * k / 4, 1, off))
    for k in range(1, 10):
        pts.append(Vector((lerp(0.94, xv, k / 9), 0.5 + off)))
    return [Vector((side * p.x, p.y, z)) for p in pts], ia, ib


def skirt_rows(P):
    """the skirt's row heights; a skirt that ends above SL_JOIN (a hip-length jacket) has no join: its slit runs to
    the hem"""
    zb = P["skirt_bot"]
    if zb > SL_JOIN - 0.08:
        zs = [z for z in (SK_TOP, -0.74, -0.79, -0.85, -0.92, -1.0, -1.06, -1.14) if z > zb + 0.04]
        z = zs[-1]
        while z - 0.12 > zb + 0.04:
            z -= 0.12
            zs.append(z)
        return zs + [zb + 0.015, zb]
    zs = [SK_TOP, -0.74, -0.79, -0.85, -0.92, -1.0, -1.06, -1.14]
    z = -1.14
    while z - 0.12 > SL_JOIN + 0.04:
        z -= 0.12
        zs.append(z)
    zs.append(SL_JOIN)
    z = SL_JOIN
    while z - 0.10 > zb + 0.04:
        z -= 0.10
        zs.append(z)
    zs += [zb + 0.015, zb]
    return zs


def skirt_rig(ob):
    bones = [("Root", Vector((0, 0, 0)), Vector((0, 0, 0.08)), None),
             ("F_LL", Vector((0.5, 0, -1.0)), Vector((0.5, 0, -1.3)), "Root"),
             ("F_RL", Vector((-0.5, 0, -1.0)), Vector((-0.5, 0, -1.3)), "Root")]

    def wfn(co):   # each half rides its leg entirely (see the module notes)
        return {"F_LL" if co.x >= 0 else "F_RL": 1.0}
    return A.make_rig(ob, bones, wfn), bones


def build_skirt(name, P, X):
    """both halves of the skirt: wool outside, the lining inside; above SL_JOIN a front panel and a side-and-back
    panel either side of the front-outer slit, below it one panel round to the hem. A binding at the hem, piping along
    the waist seam and down the slit's edges, a bar tack at the slit's top, a facing of lining down each front edge"""
    zs = skirt_rows(P)
    zb = P["skirt_bot"]
    jj = zs.index(SL_JOIN) if SL_JOIN in zs else len(zs) - 1   # no join: the slit runs to the hem
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        rows = []
        for z in zs:
            r, ia, ib = skirt_plan(side, z, P)
            rows.append(r)
        nc = len(rows[0])

        def grid(cols, js):
            return [[rows[j][i] for j in js] for i in cols]

        def hint(p, side=side):
            return Vector((p.x - side * 0.5, p.y, 0)).normalized() if abs(p.x) > 0.1 or abs(p.y) > 0.1 else Vector((0, -1, 0))
        up, lo = list(range(0, jj + 1)), list(range(jj, len(zs)))
        cloth(f"{name}Front{sd}", grid(range(0, ia + 1), up), T_SKIRT, X["wool"], hint, mat_in=X["lining"])
        cloth(f"{name}Back{sd}", grid(range(ib, nc), up), T_SKIRT, X["wool"], hint, mat_in=X["lining"])
        if len(lo) > 1:
            cloth(f"{name}Hem{sd}", grid(range(0, nc), lo), T_SKIRT, X["wool"], hint, mat_in=X["lining"])
        o = T_SKIRT / 2 + 0.004

        def outward(p, k=o):
            if abs(p.x) > 0.97:
                d = Vector((side, 0, 0))
            elif p.y < 0:
                d = Vector((0, -1, 0))
            else:
                d = Vector((0, 1, 0))
            return p + d * k
        hem_cols = [range(nc)] if len(lo) > 1 else [range(0, ia + 1), range(ib, nc)]
        for k, cols in enumerate(hem_cols):
            wire(f"{name}HemPipe{sd}{k}", [tuple(outward(rows[-1][i], o - 0.002)) for i in cols], P["pipe_r"], X["pipe"], sides=5)
        for nm, cols in (("F", range(0, ia + 1)), ("B", range(ib, nc))):
            wire(f"{name}Waist{nm}{sd}", [tuple(outward(rows[0][i], o) + Vector((0, 0, -0.004))) for i in cols],
                 P["pipe_r"] * 1.15, X["pipe"], sides=5)
        for nm, i in (("F", ia), ("B", ib)):   # the slit's edges, bound in wool
            wire(f"{name}Slit{nm}{sd}", [tuple(outward(rows[j][i], o - 0.003)) for j in up], P["pipe_r"], X["pipe"], sides=5)
        if len(lo) > 1:   # the bar tack at the slit's top (where the panels join)
            tack = [outward(rows[jj][i], o + 0.001) for i in range(ia, ib + 1)]
            wire(f"{name}Tack{sd}", [tuple(p) for p in tack], P["pipe_r"] * 1.3, X["thread"], sides=5)
        for k, cols in enumerate(hem_cols):
            cols = list(cols)
            wire(f"{name}Stitch{sd}{k}", [tuple(outward(Vector((rows[-1][i].x, rows[-1][i].y, zb + 0.045)), o - 0.001))
                                          for i in cols[1:-1]], 0.0026, X["thread"], sides=4)
        # the facing: the lining turned out down the front edge
        Gf = [[outward(rows[j][i], T_SKIRT / 2 + 0.002) for j in range(len(zs))] for i in (0, 1)]
        cloth(f"{name}Facing{sd}", Gf, 0.004, X["lining"], lambda p: Vector((0, -1, 0)))


def skirt_fit(obj):
    """the skirt's depth fit per body type (UI.AccessoryWear scales a Torso piece's depth about the torso's centre
    plane by it): from the legs where it rides them, the torso's lower part above the hip line. As A.fit_table, but
    the body's surface is probed on the part the cloth lies over"""
    import random
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    contact = [(p, -1 if p.y < 0 else 1, max(0.004, min(abs(p.y) - 0.5, 0.02))) for p in pts
               if abs(p.y) > 0.3 and abs(p.x) < 0.97 and abs(p.y) - 0.5 < 0.12]
    random.seed(7)
    if len(contact) > 500:
        contact = random.sample(contact, 500)
    out = {}
    for bid in A.BODY_IDS:
        if bid == "standard":
            continue
        need = 0.0
        for p, side, cl in contact:
            if p.z > -1.0:
                d = A.body_depth(bid, "Torso", p.x, p.z, side)
            else:
                part = "LeftLeg" if p.x > 0 else "RightLeg"
                d = A.body_depth(bid, part, p.x - (0.5 if p.x > 0 else -0.5), p.z + 2.0, side)
            if d is not None:
                need = max(need, (d + cl) / abs(p.y))
        out[bid] = round(min(1.45, max(0.8, need)), 3) if need > 0 else 1.0
    return out


_fit_table = A.fit_table


def hips_fit(obj):
    """the hip panels' depth fit: as A.fit_table, but allowed down to 0.55 (the lean body's torso is 0.33 deep at the
    lower front corner: at the toolkit's 0.8 floor the panel stood 0.04 off it)"""
    import random
    me = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [obj.matrix_world @ v.co for v in me.vertices]
    obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    contact = [(p, max(0.004, min(abs(p.y) - 0.5, 0.02))) for p in pts if p.y < -0.3 and abs(p.x) < 0.985]
    random.seed(7)
    if len(contact) > 400:
        contact = random.sample(contact, 400)
    out = {}
    for bid in A.BODY_IDS:
        if bid == "standard":
            continue
        need = 0.0
        for p, cl in contact:
            d = A.body_depth(bid, "Torso", p.x, p.z, -1)
            if d is not None:
                need = max(need, (d + cl) / abs(p.y))
        out[bid] = round(min(1.45, max(0.55, need)), 3) if need > 0 else 1.0
    return out


def _fit_table_kitc(obj, mount):
    if obj.name.endswith("Skirt"):
        return skirt_fit(obj)
    if "Hips" in obj.name:
        return hips_fit(obj)
    return _fit_table(obj, mount)


A.fit_table = _fit_table_kitc   # run() looks the name up when it fits each piece


def write_extra(key, pieces):
    p = os.path.join(A.OUT, "layout", f"{key}.extra.json")
    ex = json.load(open(p)) if os.path.exists(p) else {}
    ex.update(pieces)
    with open(p, "w") as fh:
        json.dump(ex, fh, indent=1)


# ================================================================== the Kit C shell: a scooped neckline (hair)
# The hairs rest on the shoulder tops and the nape, right where a coat goes (Kit A's coats fit 4 of 35 hairs).
# acc_hairfit on the frock coat: long hair crosses the front of the shoulders near the neck, short cuts cross the back
# of the collar at the nape (z 0.9-1.0). So Kit C's shell opens the neckline wider at the shoulders (xo_top) and
# scoops the back neckline down to NAPE_Z at the centre back, and the collar follows the neckline down and lies low.
# P: "nape_z" (the back neckline's lowest point; default 0.78).
BACK_Z_K = [1.0, 0.98, 0.95, 0.91, 0.87, 0.83, 0.79, 0.74, 0.65, 0.55, 0.30, 0.05, -0.20, -0.40, -0.56, -0.66, -0.72]


def back_neck(z, P):
    """x where the back panel starts at height z (the scooped back neckline): xo_top at the shoulder top, 0 at the
    centre back at nape_z"""
    zn = P.get("nape_z", 0.78)
    return P["xo_top"] * math.sqrt(max(0.0, smooth(zn, 1.0, z)))


def shell_rows_k(P):
    # the shoulder top stops just inside x 1: the swung arm's top rises above the shoulder line, flush on the torso's
    # side, and the cloth's rim at x 1.0 met it (0.005 into the arm at +55 degrees)
    rows = [(y, z, reg, xs, 0.994 if reg == "top" else xe) for (y, z, reg, xs, xe) in K7.shell_rows(P) if reg != "back"]
    d = D_F
    for z in BACK_Z_K:
        rows.append((0.5 + d, z, "back", back_neck(z, P), 1.0))
    return rows


def shell_grid_k(side, P, ncol=9):
    rows = shell_rows_k(P)
    G = []
    for i in range(ncol + 1):
        col = []
        for (y, z, reg, xs, xe) in rows:
            x = lerp(xs, xe, i / ncol)
            col.append(Vector((side * x, y + (K7.back_fold(x, z, P) if reg == "back" else 0.0), z)))
        G.append(col)
    return G, rows


def build_collar_k(name, G, rows, side, P, X):
    """Kit A's rolled collar along the neckline, down the scooped back to the centre back: low (it lies on the
    shoulders and the back rather than standing up the neck)"""
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
        out = Vector((0, 1, 0))   # straight back, off the back panel
        w = 1.0 if reg == "back" else (smooth(0.49, 0.524, y) if reg == "top" else 0.0)
        fr = smooth(0.0, 0.22, t)
        up = Vector((0, 0, 1))
        rad = Vector((b.x, b.y, 0)).normalized()
        S1 = b + up * (0.045 * fr + 0.008) + rad * 0.006
        C1 = b + up * (rise * fr + 0.012) + rad * lerp(0.04, 0.06, w)
        F1 = b + up * lerp(rise * 0.75 * fr + 0.01, 0.030, w) + rad * lerp(reach * 0.62, 0.070, w)
        O1 = b + up * lerp(0.010, -P["collar_back"] * 0.6, w) + rad * lerp(reach * fr + 0.05 * (1 - fr), 0.040, w)
        # down the scooped back the collar lies flat on the panel, falling a little below the neckline
        q = smooth(0.99, 0.90, z) if reg == "back" else 0.0
        S2 = b + out * 0.007
        C2 = b + out * 0.016 + up * 0.012
        F2 = b + out * 0.020 + up * 0.004
        O2 = b + out * 0.012 - up * P["collar_back"]
        col = [b, S1.lerp(S2, q), C1.lerp(C2, q), F1.lerp(F2, q), O1.lerp(O2, q)]
        # the fall stops short of the shoulder's edge (with the wide neckline it would reach x 1, where the swung
        # arm's top rises)
        cols.append([Vector((math.copysign(min(abs(c.x), 0.962), c.x), c.y, c.z)) for c in col])

    def hint(p):
        return Vector((p.x, p.y, 0)).normalized() * 0.5 + Vector((0, 0, 0.9))
    cloth(name, cols, 0.012, X["collar"], hint)
    wire(name + "Edge", [tuple(c[4]) for c in cols], P["pipe_r"] * 0.9, X["collar_pipe"], sides=5)


def build_shell_k(name, P, X):
    """Kit A's coat shell (nh_acc_batch7.build_shell) with the scooped neckline and the low collar"""
    from nh_acc_batch7 import band_grid, build_lapel, out_hint_torso, FRONT_Z, HEM_BACK, T_BAND
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        G, rows = shell_grid_k(side, P)
        cloth(f"{name}Body{sd}", G, T_SHELL, X["wool"], out_hint_torso, mat_in=X["lining"])
        cloth(f"{name}Band{sd}", band_grid(side), T_BAND, X["wool"], out_hint_torso, mat_in=X["lining"])
        out = T_SHELL / 2 + 0.004
        nf = len(FRONT_Z)
        jb = FRONT_Z.index(P["break"])
        edge = [G[0][j] for j in range(jb, -1, -1)] + [G[i][0] for i in range(1, len(G))] +                [G[-1][j] for j in range(1, nf) if FRONT_Z[j] <= -0.075]
        edge = [p + Vector((0, -out, 0)) for p in edge]
        wire(f"{name}PipeFront{sd}", [tuple(p) for p in edge], P["pipe_r"], X["pipe"], sides=5)
        jh = len(rows) - 1
        wire(f"{name}PipeBack{sd}", [tuple(G[i][jh] + Vector((0, out + 0.002, 0))) for i in range(len(G))], P["pipe_r"],
             X["pipe"], sides=5)
        top = [r for r in rows if r[2] == "top"]
        ys = top[min(range(len(top)), key=lambda k: abs(top[k][0]))]
        # the shoulder seam stops short of the shoulder's edge (the swung arm's top rises there)
        wire(f"{name}SeamShoulder{sd}", [(side * lerp(ys[3], 0.97, t), ys[0], ys[1] + out + 0.001) for t in (0.06, 0.5, 0.88)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSide{sd}", [(side * (1.0 + 0.002), -(0.5 + D_F + out - 0.004), z) for z in (-0.06, 0.4, 0.97)],
             0.0035, X["thread"], sides=4)
        wire(f"{name}SeamSideB{sd}", [(side * (1.0 + 0.002), 0.5 + D_F + out - 0.004, z) for z in (HEM_BACK + 0.02, 0.2, 0.97)],
             0.0035, X["thread"], sides=4)
        build_collar_k(f"{name}Collar{sd}", G, rows, side, P, X)
        build_lapel(f"{name}Lapel{sd}", side, P, X)
    zn = P.get("nape_z", 0.78)
    wire(f"{name}SeamBack", [(0, 0.5 + D_F + T_SHELL / 2 + 0.001, z) for z in (HEM_BACK + 0.02, -0.2, 0.4, zn - 0.06)], 0.004,
         X["thread"], sides=4)


# ================================================================== the Kit C sleeve: the whole arm (owner: "Same with the arms")
# Kit A's sleeve ends above the drawn katana's grip (z -0.535) and leaves the inner 0.07-0.14 of the front and back
# faces bare (the sheathed scabbard passes the left forearm's front inner corner). Kit C's covers the arm down to the
# cuff (SLV_CUFF, the hand below it) and the front and back faces to the inner edge. Riding the arm entirely, it meets
# the katana only where the arm itself does (acc_check: layout extra "hug"). The arm's inner face is left open: it is
# flush on the torso's side, so cloth there would be inside the torso.
SLV_CUFF = -0.56    # the katana leaves no room lower: the drawn guard spans the right forearm's front below z -0.61,
                    # and the sheathed scabbard runs through the left forearm's inner side below z -0.48 (front) to
                    # -0.70 (back), x 1.02-1.23. On most bodies the arm meets them too (allowed: "hug"), but on the
                    # thinner and deeper arms it doesn't, and a sleeve there would show the katana through the cloth.
SLV_XIN = -0.48     # arm-local inner edge (x 1.02): clear of the shell's band round the torso's front corner (x <= 1.01)
SLV_XIN_LOW = -0.36 # below the elbow the inner edge steps out to x 1.14 (the scabbard's top edge)


def slv_xin(z):
    return lerp(SLV_XIN_LOW, SLV_XIN, smooth(-0.45, -0.28, z))
SLEEVE_Z_K = [SLV_CUFF, SLV_CUFF + 0.03, -0.45, -0.37, -0.28, -0.18, -0.05, 0.10, 0.28, 0.46, 0.62, 0.76, 0.88, 0.96, 1.0]


def sleeve_grid_k(d=0.020):
    from nh_acc_batch4 import arm_wrap
    kw = K7.wrap_kw()
    rowsP = []
    for z in SLEEVE_Z_K:
        ease = 0.003 * math.sin(math.pi * smooth(-0.8, 0.9, z))
        rowsP.append([Vector((1.5 + X, Y, z)) for X, Y in arm_wrap(d + ease, x_in=slv_xin(z), **kw)])
    E0 = arm_wrap(0.0, x_in=SLV_XIN, **kw)
    Ed = arm_wrap(d, x_in=SLV_XIN, **kw)
    for a in (35, 70):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        rowsP.append([Vector((1.5 + e[0] + (f[0] - e[0]) * c, e[1] + (f[1] - e[1]) * c, 1.0 + d * s_)) for e, f in zip(E0, Ed)])
    n = len(E0)
    T = [(SLV_XIN + 0.01, lerp(-0.40, 0.40, k / (n - 1))) for k in range(n)]   # the cap over the arm top to x 1.03
    for f in (0.0, 0.3, 0.6, 1.0):
        rowsP.append([Vector((1.5 + lerp(E0[k][0], T[k][0], f), lerp(E0[k][1], T[k][1], f), 1.0 + d)) for k in range(n)])
    return [[rowsP[j][k] for j in range(len(rowsP))] for k in range(n)]


def build_sleeve_k(name, P, X):
    """the left sleeve, the whole arm: wool outside, lining inside, a rolled hem and a turned-back cuff at the wrist
    (P cuff "turnback": X["cuff"] with piping and two buttons; else a plain stitched cuff)"""
    from nh_acc_batch4 import arm_wrap
    from nh_acc_batch7 import sleeve_hint, button
    kw = K7.wrap_kw()
    G = sleeve_grid_k()
    cloth(name + "Body", G, 0.014, X["wool"], sleeve_hint, mat_in=X["lining"])
    wire(name + "Hem", [tuple(c[0] + (c[0] - Vector((1.5, 0, c[0].z))).normalized() * 0.006) for c in G], 0.0075,
         X["wool"], sides=5)
    wire(name + "Seam", [tuple(Vector((1.5 + 0.10, 0.5 + 0.020 + 0.0085, z))) for z in (SLV_CUFF + 0.02, -0.2, 0.3, 0.8, 0.97)],
         0.0032, X["thread"], sides=4)
    zs = [SLV_CUFF + 0.002, SLV_CUFF + 0.03, SLV_CUFF + 0.07, SLV_CUFF + 0.11, SLV_CUFF + 0.15]
    prof = [arm_wrap(0.040 + 0.004 * (j / 4), x_in=slv_xin(z) + 0.004, **kw) for j, z in enumerate(zs)]
    Gc = [[Vector((1.5 + prof[j][k][0], prof[j][k][1], z)) for j, z in enumerate(zs)] for k in range(len(prof[0]))]
    cloth(name + "Cuff", Gc, 0.014, X.get("cuff", X["wool"]), sleeve_hint)
    wire(name + "CuffPipe", [tuple(c[-1] + (c[-1] - Vector((1.5, 0, c[-1].z))).normalized() * 0.006 + Vector((0, 0, 0.004)))
                             for c in Gc], P["pipe_r"] * 0.9, X.get("cuff_pipe", X["thread"]), sides=5)
    if P.get("cuff") == "turnback":
        for k, z in enumerate((SLV_CUFF + 0.06, SLV_CUFF + 0.12)):
            button(f"{name}CuffBtn{k}", Vector((2.0 + 0.049, 0.30, z)), (1, 0, 0), X, X["btn"], r=0.026)


# ================================================================== under the coat: the torso covered (owner: "Make the
# jackets cover the torso (In their respective designs)"). In the Shell piece, between the torso and the shell (whose
# inner face is 0.016 off the torso): a shirt (0.002-0.007) that lies over the shoulder tops round the neck, hangs down
# the front to the waist (in the waistcoat's V) and down the scooped back to below the neckline; a waistcoat
# (0.0085-0.0145) over the whole front with a V neck and a pointed hem at z -0.72 (a striding leg's top corner pokes out
# of the torso below about -0.75); a silk cravat at the throat.
SHIRT_LIFT, SHIRT_T = 0.0045, 0.005
VEST_D, VEST_T = 0.0115, 0.006


def _ray_poly(theta, poly):
    """distance from the origin along angle theta to the polygon's boundary (the nearest crossing)"""
    d = Vector((math.cos(theta), math.sin(theta)))
    best = None
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        ex, ey = bx - ax, by - ay
        den = d.x * ey - d.y * ex
        if abs(den) < 1e-12:
            continue
        t = (ax * ey - ay * ex) / den
        u = (ax * d.y - ay * d.x) / den
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best


def shirt_plan(P):
    """the shirt in plan, draped over the torso top (A.batch1.drape_point: past an edge it hangs down that face by the
    overhang): the front hangs to the waist between x -0.5..0.5 (the waistcoat's V), the sides tuck under the shell's
    shoulder, the back hangs below the scooped neckline"""
    hf = 1.0 - P.get("shirt_front_z", 0.0)            # front overhang: down to shirt_front_z
    hb = 1.0 - (P.get("nape_z", 0.78) - 0.10)         # back overhang: 0.10 below the neckline's lowest point
    xb = P["xo_top"] + 0.06
    half = [(0.5, -(0.5 + hf)), (0.5, -0.56), (0.96, -0.47), (0.96, 0.47), (xb, 0.53), (xb, 0.5 + hb)]
    return half + [(-x, y) for x, y in reversed(half)]


HIPS_TOP = -0.08   # where the coat panel's cut edge reaches the side (cut_line 1.0)
HIPS_D, HIPS_T = 0.006, 0.004   # close and thin: on the heavy body the torso is only 0.008 short of the guard's padded box


HIPS_SPLIT = -0.45


def build_hips(name, P, X, part, hem=None):
    """the waistcoat's lower front corners (x from the coat panel's cut edge to the side), in two pieces with their
    own depth fits: part "Up" (HIPS_SPLIT to HIPS_TOP) and "Lo" (the hem to HIPS_SPLIT, a welt along its top). One
    fit can't hug the corner on every body: the curvy body is 0.53 deep at the hem and 0.37 at the waist, and the
    coat shell's fit (1.21 on the heavy body, set by the chest) would push the corners into the sheathed katana's
    guard just in front of the left hip (its back face at y -0.59 padded; the heavy torso is 0.58 deep there)"""
    hem = hem or (lambda x: -0.64 - 0.08 * smooth(0.0, 0.14, abs(x)) + 0.12 * smooth(0.20, 0.95, abs(x)))
    y = -(0.5 + HIPS_D)
    o = HIPS_T / 2 + 0.003
    z0, z1 = (HIPS_SPLIT, HIPS_TOP) if part == "Up" else (-0.72, HIPS_SPLIT + 0.004)
    for side in (1, -1):
        sd = "L" if side > 0 else "R"
        zs = [lerp(z0, z1, j / 6) for j in range(7)]
        G = []
        for i in range(7):
            u = i / 6
            col = []
            for z in zs:
                x0 = lerp(min(0.99, K7.cut_line(z) + 0.002), 0.995, u)
                col.append(Vector((side * x0, y, max(z, hem(x0)) if part == "Lo" else z)))
            G.append(col)
        cloth(f"{name}{sd}", G, HIPS_T, X["vest"], lambda p: Vector((0, -1, 0)))
        if part == "Lo":
            wire(f"{name}Hem{sd}", [tuple(G[i][0] + Vector((0, -o + 0.0015, 0.003))) for i in range(7)], 0.0025, X["vest_pipe"], sides=5)
            # a welt pocket's edge along the top: the seam where the two corner pieces meet
            wire(f"{name}Welt{sd}", [tuple(G[i][-1] + Vector((0, -o + 0.0015, -0.006))) for i in range(7)], 0.0035, X["vest_pipe"], sides=5)


def add_hips(key, P, X, mat, pipe=None):
    """the two hip-corner pieces of a coat (<key>HipsUp, <key>HipsLo) in `mat`; returns their extra entries (hug)"""
    Xh = dict(X, vest=mat, vest_pipe=pipe or mat)
    for part in ("Up", "Lo"):
        piece(f"{key}Hips{part}", "Torso")
        build_hips(f"{key}Hips{part}", P, Xh, part)
    return {f"{key}HipsUp": {"hug": True}, f"{key}HipsLo": {"hug": True}}


def build_inner(name, P, X, cravat=True):
    from nh_acc_batch1 import drape_point
    poly = shirt_plan(P)
    na, radii = 56, [0.0, 0.06, 0.16, 0.30, 0.48, 0.70, 1.0]
    r0 = 0.64   # clear of the head
    cols = []
    for i in range(len(radii)):
        col = []
        for j in range(na + 1):
            th = 2 * math.pi * (j % na) / na - math.pi / 2
            R = _ray_poly(th, poly) or r0
            r = lerp(r0, max(R, r0 + 0.02), radii[i])
            col.append(drape_point(r * math.cos(th), r * math.sin(th), 1.0, SHIRT_LIFT))
        cols.append(col)
    A.surface(name + "Shirt", cols, SHIRT_T, X["shirt"])
    # the waistcoat: the whole front, a V neck, a pointed hem
    def top(x):
        return min(0.97, P.get("vest_v", 0.30) + 1.3 * abs(x))

    def hem(x):
        ax = abs(x)
        return -0.64 - 0.08 * smooth(0.0, 0.14, ax) + 0.12 * smooth(0.20, 0.95, ax)
    xs = [lerp(-0.995, 0.995, k / 24) for k in range(25)]
    nz = 9
    y = -(0.5 + VEST_D)
    # below the shell's cutaway (x <= 0.74 under z -0.26) the waistcoat stops under the coat's panel; the hips piece
    # (build_hips) covers the corners with its own depth fit
    def w(z):
        return min(0.995, K7.cut_line(z) - 0.015)
    G = []
    for k in range(25):
        u = k / 24
        col = []
        for j in range(nz + 1):
            x0 = lerp(-0.995, 0.995, u)
            z = lerp(hem(x0), top(x0), j / nz)
            col.append(Vector((max(-w(z), min(w(z), x0)), y, z)))
        G.append(col)
    cloth(name + "Vest", G, VEST_T, X["vest"], lambda p: Vector((0, -1, 0)))
    o = VEST_T / 2 + 0.003
    wire(name + "VestEdge", [(x, y - o + 0.002, top(x) - 0.004) for x in xs if top(x) < 0.965] , 0.0045, X["vest_pipe"], sides=5)
    wire(name + "VestHem", [(x, y - o + 0.002, hem(x) + 0.004) for x in xs], 0.0045, X["vest_pipe"], sides=5)
    for k, z in enumerate([0.22, 0.08, -0.06, -0.20, -0.34, -0.48]):
        A.sphere(f"{name}VestBtn{k}", 0.016, (0.0, y - o, z), X["brass"], scale=(1, 0.5, 1), seg=10, rings=6)
    for sx in (-1, 1):   # welt pockets
        A.box(f"{name}VestWelt{sx}", (0.16, 0.006, 0.022), (sx * 0.45, y - o, -0.38), X["vest_pipe"], bevel=0.002)
    if cravat:   # a black silk cravat: a knot at the throat and two tails lying on the shirt
        yc = -(0.5 + VEST_D)
        # a full ascot: a puffed knot, a wrapped band round the collar front, two broad crossed tails with a pin
        A.sphere(name + "CravatKnot", 0.075, (0.0, yc - 0.016, 0.855), X["cravat"], scale=(1.15, 0.42, 0.80), seg=14, rings=8)
        for sx in (-1, 1):
            Gt = []
            for u in (0.0, 0.33, 0.66, 1.0):
                col = []
                for t in [k / 8 for k in range(9)]:
                    w = 0.055 + 0.075 * t ** 0.8                     # broadening toward the ends
                    cx = sx * (0.02 - 0.05 * t)                      # the tails cross at the pin
                    col.append(Vector((cx + (u - 0.5) * w, yc - 0.004 - 0.010 * math.sin(math.pi * t) - 0.004 * (1 - t) - 0.008 * (sx > 0),
                                       lerp(0.80, 0.42 + 0.05 * (sx > 0), t))))
                Gt.append(col)
            cloth(f"{name}CravatTail{sx}", Gt, 0.006, X["cravat"], lambda p: Vector((0, -1, 0)))
        A.cyl(name + "CravatPin", 0.016, 0.012, (0.0, yc - 0.03, 0.66), X["brass"], rot=(math.pi / 2, 0, 0), verts=10)
        A.sphere(name + "CravatPearl", 0.014, (0.0, yc - 0.04, 0.66), X.get("pearl", X["shirt"]), seg=10, rings=6)


# ================================================================== buttons, pins
def inkwell_button(name, at, nrm, X, r=0.034):
    """a brass button cast as a tiny inkwell: a domed brass cup, a black-enamel well in its top, a raised rim"""
    F = axis_frame(at, nrm)
    ob = A.lathe(name, [(0.0, 0.016), (r * 0.30, 0.016), (r * 0.36, 0.022), (r * 0.52, 0.023), (r * 0.62, 0.019),
                        (r * 0.86, 0.014), (r * 1.0, 0.007), (r * 0.98, 0.0), (0.0, 0.0)], (0, 0, 0), X["brass"], seg=12)
    ob.data.materials.append(X["ink"])
    for p in ob.data.polygons:
        c = p.center
        if math.hypot(c.x, c.y) < r * 0.33 and c.z > 0.012:
            p.material_index = 1
    place(ob, F)


def pen_nib(name, at, X, s=0.11):
    """a brass pen-nib pin (pointing down), with its slit and breather hole, flat on the lapel"""
    out = [(0.0, -0.5), (0.20, -0.08), (0.27, 0.22), (0.20, 0.46), (0.0, 0.52), (-0.20, 0.46), (-0.27, 0.22), (-0.20, -0.08)]
    F = Matrix.Translation(at) @ Matrix.Scale(s, 4)
    A.extrude_poly(name, ccw(out), 0.012 / s, X["brass"], F, bevel=0.0, segments=1)
    A.cyl(name + "Hole", 0.010, 0.006, tuple(Vector(at) + Vector((0, -0.007, 0.02 * s / 0.11))), X["ink"], rot=(math.pi / 2, 0, 0),
          verts=10, bevel=0.0)
    wire(name + "Slit", [tuple(Vector(at) + Vector((0, -0.0075, z * s))) for z in (-0.46, -0.06)], 0.0024, X["ink"], sides=4)


# ================================================================== the Scholar's frock coat
def scholar_mats(M):
    X = dict(
        wool=A.mat_cloth("ScholarWool", (0.040, 0.040, 0.044), weave=300, rough=0.86, sheen=0.42, bump=0.12, vary=0.08,
                         wear=0.25, dirt=0.5),
        lining=A.mat_cloth("InkSilk", (0.012, 0.022, 0.075), weave=520, rough=0.34, sheen=0.4, bump=0.04, twill=False),
        thread=A.mat_cloth("InkThread", (0.02, 0.03, 0.09), weave=900, rough=0.5, sheen=0.2, bump=0.05, twill=False),
        brass=M["brass"], ink=M["black_enamel"], silver=M["brass"], strap=M["leather_black"], bone=M["bone"], btn="silver")
    X.update(collar=X["wool"], lapel=X["wool"], pipe=X["wool"], collar_pipe=X["lining"], lapel_pipe=X["thread"],
             cuff=X["wool"], cuff_pipe=X["lining"],
             shirt=M["white_linen"], cravat=A.mat_cloth("CravatSilk", (0.012, 0.011, 0.014), weave=520, rough=0.35, sheen=0.5,
                                                          bump=0.03, twill=False),
             vest=A.mat_cloth("PlumBrocade", (0.055, 0.020, 0.050), weave=380, rough=0.6, sheen=0.55, bump=0.10),
             vest_pipe=X["lining"])
    return X


def scholar_params():
    P = dict(xo_top=0.72, xo_break=0.36, lapel="notch", lapel_w=0.22, notch=0.07, collar_rise=0.035, collar_reach=0.11,
             collar_back=0.03, nape_z=0.78, pipe_r=0.0055, back_folds=0.006, brk=0.18, cuff="turnback",
             skirt_bot=-2.05, skirt_flare=0.085, skirt_vent=0.03)
    P["break"] = P["brk"]
    P["skirt_open"] = lambda z: P["xo_break"] + 0.02 + 0.10 * smooth(-0.9, P["skirt_bot"], z)   # opening a little toward the hem
    return P


@item("ScholarCoat", "Scholar's frock coat", views=["front34", "front", "side", "back", "close"],
      close=((2.8, -6.2, 0.9), (0.35, 0, 0.30), 85))
def build_scholar(M):
    key = "ScholarCoat"
    X, P = scholar_mats(M), scholar_params()
    piece(f"{key}Shell", "Torso")
    build_shell_k(key, P, X)
    build_inner(key, P, X)
    for s in (1, -1):   # inkwell buttons: three a side, the wearer's right front buttoned, the left with worked holes
        for k, z in enumerate((0.10, -0.12, -0.34)):
            inkwell_button(f"{key}Btn{s}{k}", front_point(s * 0.44, z), (0, -1, 0), X)
    for k, z in enumerate((0.10, -0.12, -0.34)):
        wire(f"{key}Hole{k}", [tuple(front_point(x, z + 0.04, 0.002)) for x in (0.40, 0.44, 0.48)], 0.0042, X["thread"], sides=4)
    half_belt(f"{key}HalfBelt", -0.40, X, X["wool"], P, w=0.07, x1=0.60)
    for s in (-1, 1):
        inkwell_button(f"{key}BeltBtn{s}", back_point(s * 0.55, -0.40, 0.0125), (0, 1, 0), X, r=0.030)
    for part in ("Up", "Lo"):
        piece(f"{key}Hips{part}", "Torso")
        build_hips(f"{key}Hips{part}", P, X, part)
    piece(f"{key}Shell", "Torso")   # back to the shell for its details
    pen_nib(f"{key}Nib", Vector((K7.lapel_line(0.62, P) + 0.12, -(0.5 + D_F + T_SHELL / 2 + 0.0135) - 0.002, 0.60)), X)
    piece(f"{key}Skirt", "Torso", rig=skirt_rig)
    build_skirt(f"{key}Skirt", P, X)
    piece(f"{key}SleeveL", "LeftArm")
    build_sleeve_k(f"{key}SleeveL", P, X)
    mirror_piece(f"{key}SleeveL", f"{key}SleeveR")
    piece(f"{key}SleeveR", "RightArm")
    write_extra(key, {f"{key}Skirt": {"follow": "LL=1;RL=1"}, f"{key}SleeveL": {"hug": True}, f"{key}SleeveR": {"hug": True},
                      f"{key}HipsUp": {"hug": True}, f"{key}HipsLo": {"hug": True}})
    return dict(notes="the Scholar's frock coat: charcoal wool, ink-blue silk lining, brass inkwell buttons, a pen-nib pin; "
                      "knee-length skirts that move with the legs (BodyFollow)")


# the other Kit C coats live in their own modules (each registers its items with @item); a module being edited must
# not stop this batch's run
for _m in ("nh_kitc_coats_c", "nh_kitc_coats_d", "nh_kitc_coats_e"):
    try:
        __import__(_m)
    except Exception as _e:   # noqa: BLE001
        print(f"[batchc1] skipped {_m}: {type(_e).__name__}: {_e}")
