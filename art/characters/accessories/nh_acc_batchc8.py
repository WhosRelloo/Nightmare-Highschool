"""Accessories batch C8 (Kit C, "The Night School Wardrobe"): bags and things on the back.

  CoffinBackpack  a black-lacquer coffin with a crimson velvet lid panel, brass beading, corner plates and the school's
                  crescent; straps that wrap the torso (owner) and a waist strap joining them
  BatWingBackpack a black leather bat as a pack (pug face, tall ears, crimson glass eyes) whose wings sway back as you run
  ViolinCase      a shaped violin case in pebbled black leather, crimson piping, brass caps, latches and an N.H plate
  GladstoneBag    an oxblood doctor's bag on a hinged brass frame with an alchemist's sigil, held (right hand)
  ScrollTube      a tan leather scroll tube with brass caps, slung over the left shoulder to the right hip
  BirdcagePurse   a domed brass birdcage purse on a velvet drum, a paper moth inside that opens its wings (held, Female)

Backpacks (owner, 2026-11-11): "Make the backpack straps, wrap around the character" and "Add another horizontal
strap that connects the straps going down, which would wrap around the torso. Remember this for when I ask you to make
more backpacks". Every backpack here uses `wrap_straps`.
Run: bash E:/NH-Work/acc/bake_batch.sh CoffinBackpack,BatWingBackpack,ViolinCase,GladstoneBag,ScrollTube,BirdcagePurse
"""
import math
from mathutils import Matrix, Vector
import nh_acc as A
from nh_acc import item, piece, lerp
from nh_acc_batch1 import ccw, frame, band_loop, buckle, crescent, offset_poly

HP = math.pi / 2


# ---------------------------------------------------------------- shared: the straps that wrap the torso
def wrap_straps(M, tag, pack_half_x, pack_back_y, tab_z=0.60, waist_z=0.20, strap_m=None, lock_z=0.58, low_z=0.05,
                tab_x=None):
    """two shoulder straps, each a loop hugging the torso box: over the shoulder top (x 0.72, clear of the head), down
    the chest slanting out to the armpit, round under the arm and up the back; a waist strap wraps round the torso over
    them (a larger offset, so it lies on top) with a front buckle, its back run tucked into the pack's sides
    (|x| < pack_half_x behind y pack_back_y); a tab from the pack's shoulder to each strap on the back.
    Measured limits: the loop comes back under the arm at z 0.05, like a real strap at the armpit. Lower, its plane
    leaves the torso's side through the bottom corner (into the legs' tops and the striding leg's corner) and its
    front-left run crosses the sheathed katana's guard (up to z -0.31 at the front-left hip). The horizontal strap
    crosses both shoulder straps on the chest at z 0.20"""
    strap_m = strap_m or M["leather_black"]
    tab_x = pack_half_x - 0.02 if tab_x is None else tab_x   # where the tab leaves the pack's side (at tab_z)

    def runs_of(G, cut):
        runs, cur = [], []
        for j in range(len(G[0])):
            if any(cut(G[i][j]) for i in range(4)):
                if cur:
                    runs.append(cur); cur = []
            else:
                cur.append(j)
        if cur:
            runs.append(cur)
        if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(G[0]) - 1:   # join across the loop's seam
            runs = [runs[-1] + runs[0][1:]] + runs[1:-1]
        return [r for r in runs if len(r) > 1]

    for s in (1, -1):
        sh, low = Vector((s * 0.72, 0, 1.0)), Vector((s * 1.0, 0, low_z))
        d = (sh - low).normalized()
        n = Vector((0, 1, 0)).cross(d).normalized()
        G = band_loop((sh + low) / 2, n, 0.15, 0.052)
        A.surface(f"{tag}Strap{s}", G, 0.012, strap_m)
        x_at = lambda z: s * (0.72 + 0.28 * (1.0 - z) / (1.0 - low_z))
        buckle(f"{tag}StrapLock{s}", (x_at(lock_z), -0.559, lock_z), 0.19, 0.085, M["brass"])
        A.tube(f"{tag}StrapTab{s}", [(s * tab_x, pack_back_y + 0.16, tab_z), (s * 0.50, 0.62, tab_z),
                                     (x_at(tab_z), 0.566, tab_z)], 0.022, strap_m, square=True)
        A.cyl(f"{tag}TabRivet{s}", 0.022, 0.012, (s * (tab_x + 0.50) / 2, 0.66, tab_z), M["brass"],
              rot=(HP, 0, 0), verts=10)
    G = band_loop((0, 0, waist_z), (0, 0, 1), 0.12, 0.068)
    for k, run in enumerate(runs_of(G, lambda p: p.y > 0.3 and abs(p.x) < pack_half_x)):
        A.surface(f"{tag}WaistStrap{k}", [[G[i][j] for j in run] for i in range(4)], 0.012, strap_m)
    buckle(f"{tag}WaistBuckle", (0, -0.575, waist_z), 0.19, 0.16, M["brass"])


# ---------------------------------------------------------------- 1. the coffin backpack
@item("CoffinBackpack", "Coffin backpack", views=["back", "back34", "side", "front34"],
      close=((-3.4, 6.0, 1.0), (0, 0.6, 0.2), 80))
def build_coffin(M):
    piece("CoffinBackpack", "Torso")
    lacquer = A.mat_flat("CoffinLacquer", (0.018, 0.015, 0.02), rough=0.18, coat=0.7, noise=60, bump=0.02, vary=0.05,
                         wear=0.35, dirt=0.6)
    brass, brass_old = M["brass"], M["brassold"]
    # the classic six-sided coffin, its shoulders a little above the middle: 1.0 x 1.6 studs on the back (K scales the
    # drawing, Z0 is its centre height), its top at z 0.85 so the handle stays under the head
    K, Z0 = 1.18, 0.02
    outline = ccw([(K * x, K * z) for x, z in
                   ((0.0, 0.70), (0.30, 0.56), (0.42, 0.26), (0.24, -0.64), (-0.24, -0.64), (-0.42, 0.26), (-0.30, 0.56))])
    # extrude_poly draws the outline upright (x, z) and pushes it toward the front (-Y): from y 0.84 back to 0.54
    A.extrude_poly("CoffinBox", outline, 0.30, lacquer, frame((0, 0.84, Z0)), bevel=0.035, segments=4)
    # the lid: a raised, bevelled panel with a crimson velvet inset framed in brass beading
    lid = ccw(offset_poly(outline, 0.05))
    A.extrude_poly("CoffinLid", lid, 0.035, lacquer, frame((0, 0.875, Z0)), bevel=0.018, segments=3)
    inset = ccw(offset_poly(outline, 0.13))
    A.extrude_poly("CoffinVelvet", inset, 0.012, M["crimson_velvet"], frame((0, 0.884, Z0)), bevel=0.004)
    A.tube("CoffinBeading", [(x, 0.886, z + Z0) for x, z in inset], 0.010, brass, closed=True, res=6, poly=True)
    A.tube("CoffinTrim", [(x, 0.842, z + Z0) for x, z in offset_poly(outline, 0.006)], 0.014, brass_old, closed=True,
           res=6, poly=True)
    # brass corner plates and a row of studs round the lid's edge
    for k, (x, z) in enumerate(outline):
        A.cyl(f"CornerPlate{k}", 0.062, 0.012, (x * 0.96, 0.86, z * 0.97 + Z0), brass, rot=(HP, 0, 0), verts=6,
              bevel=0.003)
        A.sphere(f"CornerBoss{k}", 0.022, (x * 0.96, 0.87, z * 0.97 + Z0), brass_old, seg=10, rings=6)
    ring = offset_poly(outline, 0.085)
    for k in range(len(ring)):
        (x0, z0), (x1, z1) = ring[k], ring[(k + 1) % len(ring)]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 0.09))
        for i in range(1, n):
            A.sphere(f"Stud{k}_{i}", 0.011, (lerp(x0, x1, i / n), 0.893, lerp(z0, z1, i / n) + Z0), brass, seg=8, rings=5)
    # the emblem on the velvet: the school's crescent and three stars
    A.extrude_poly("Crescent", crescent(0.0, 0.0, 0.15 * K, 0.075 * K, 0.045 * K, 0.125 * K), 0.02, brass,
                   frame((0, 0.905, Z0 + 0.15 * K)), bevel=0.004)
    for k, (x, z) in enumerate(((-0.13, 0.35), (0.14, 0.33), (0.0, -0.15))):
        r0, r1 = 0.035 * K, 0.014 * K
        star = [((r0 if i % 2 == 0 else r1) * math.sin(math.pi * i / 5), (r0 if i % 2 == 0 else r1) * math.cos(math.pi * i / 5))
                for i in range(10)]
        A.extrude_poly(f"Star{k}", ccw([(K * x + a, K * z + b) for a, b in star]), 0.015, brass_old, frame((0, 0.9, Z0)),
                       bevel=0.002)
    # two hinges on the left side edge (the lid opens like a door) and a carry handle on top
    for k, (z, xe) in enumerate(((0.31, 0.40), (-0.25, 0.33))):
        A.cyl(f"Hinge{k}", 0.02, 0.14, (K * xe + 0.012, 0.86, K * z + Z0), brass, verts=10)
    top = 0.70 * K + Z0
    A.tube("Handle", [(-0.10, 0.70, top - 0.02), (-0.08, 0.70, top + 0.06), (0.08, 0.70, top + 0.06), (0.10, 0.70, top - 0.02)],
           0.016, M["leather_black"], res=6)
    for s in (-1, 1):
        A.box(f"HandleMount{s}", (0.05, 0.05, 0.03), (s * 0.10, 0.70, top - 0.025), brass, bevel=0.006)
    wrap_straps(M, "Coffin", pack_half_x=0.40, pack_back_y=0.54)
    return {"notes": "Kit C8: black-lacquer coffin, crimson velvet lid panel, brass beading, studs, corner plates and the "
                     "school crescent; straps wrap the torso with a waist strap joining them"}


# ---------------------------------------------------------------- 2. the bat-wing backpack
BAT_Y = 0.83          # the wings lie flat behind the pack, parallel to the back
BAT_WING = {          # the character's left wing (x, z); the right one mirrors it: shoulder, wrist, finger tips, body
    "root": (0.40, 0.34), "wrist": (0.64, 0.62), "tips": [(0.93, 0.86), (0.96, 0.44), (0.84, 0.04)], "body": (0.42, -0.22),
}


def _bat_pt(s, xz, dy=0.0):
    return Vector((s * xz[0], BAT_Y + dy, xz[1]))


def _batpack_rig(ob):
    """Root on the pack; each wing a sway chain: H<n> at the wing's root, C<n>_1 root -> wrist, C<n>_2 wrist -> the
    middle finger's tip. The pack, the head and the straps stay on Root (|x| < 0.42)"""
    W = BAT_WING
    bones = [("Root", Vector((0, 0.70, 0.10)), Vector((0, 0.70, 0.18)), None)]
    for n, s in enumerate((1, -1)):
        r, w, t = _bat_pt(s, W["root"]), _bat_pt(s, W["wrist"]), _bat_pt(s, W["tips"][1])
        bones += [(f"H{n}", r, r + (w - r) * 0.25, "Root"), (f"C{n}_1", r, w, f"H{n}"), (f"C{n}_2", w, t, f"C{n}_1")]

    def wfn(co):
        ax = abs(co.x)
        if ax < 0.42 or co.y < BAT_Y - 0.03:
            return {"Root": 1.0}
        n = 0 if co.x > 0 else 1
        if ax < 0.48:
            f = (ax - 0.42) / 0.06
            return {"Root": 1 - f, f"C{n}_1": f}
        if ax < 0.60:
            return {f"C{n}_1": 1.0}
        if ax < 0.70:
            f = (ax - 0.60) / 0.10
            return {f"C{n}_1": 1 - f, f"C{n}_2": f}
        return {f"C{n}_2": 1.0}
    return A.make_rig(ob, bones, wfn), bones


def _scallop(a, b, sag, n=8, toward=(0.0, 0.0)):
    """points from a (excluded) to b (x, z), bowed by `sag` toward the point `toward` (a bat wing's trailing edge)"""
    ax, az = a
    bx, bz = b
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    dx, dz = toward[0] - mx, toward[1] - mz
    L = math.hypot(dx, dz) or 1.0
    cx, cz = mx + dx / L * sag * 2, mz + dz / L * sag * 2
    out = []
    for i in range(1, n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx,
                    (1 - t) ** 2 * az + 2 * (1 - t) * t * cz + t * t * bz))
    return out


@item("BatWingBackpack", "Bat-wing backpack", views=["back", "back34", "side", "front34"],
      close=((-3.6, 6.2, 1.0), (0, 0.6, 0.2), 80))
def build_batpack(M):
    piece("BatWingBackpack", "Torso", rig=_batpack_rig, sway="BackHang", keepout=(0, -1, 0))
    hide = A.mat_leather("BatHide", (0.05, 0.035, 0.045), scale=2.6, wear=0.4)
    membrane = A.mat_leather("BatMembrane", (0.16, 0.035, 0.05), scale=3.4, wear=0.25)
    finger = A.mat_leather("BatFinger", (0.03, 0.022, 0.028), scale=4.0, wear=0.3)
    # the pack: a rounded leather body (the bat's), a scalloped flap with a brass crescent clasp
    A.box("BatBody", (0.80, 0.26, 0.92), (0, 0.68, -0.10), hide, bevel=0.14, segments=4)
    flap = ccw([(-0.36, 0.30), (0.36, 0.30), (0.36, -0.02)]
               + _scallop((0.36, -0.02), (0.12, -0.12), 0.025, toward=(0.0, 0.3))
               + _scallop((0.12, -0.12), (-0.12, -0.12), 0.025, toward=(0.0, 0.3))
               + _scallop((-0.12, -0.12), (-0.36, -0.02), 0.025, toward=(0.0, 0.3))[:-1])
    A.extrude_poly("BatFlap", flap, 0.022, hide, frame((0, 0.834, 0.0)), bevel=0.008, segments=2)
    A.extrude_poly("BatClasp", crescent(0.0, 0.0, 0.08, 0.04, 0.024, 0.066), 0.014, M["brass"], frame((0, 0.852, -0.07)),
                   bevel=0.003)
    # the head on top: a rounded skull, two tall pointed ears, crimson glass eyes, a pug nose and two little fangs
    A.sphere("BatHead", 0.20, (0, 0.72, 0.46), hide, scale=(1.15, 0.85, 0.85), seg=24, rings=14)
    for s in (1, -1):
        A.cyl(f"BatEar{s}", 0.09, 0.28, (s * 0.13, 0.72, 0.68), hide, rot=(0, s * -0.32, 0), verts=12, r2=0.004)
        A.cyl(f"BatEarIn{s}", 0.055, 0.21, (s * 0.13, 0.772, 0.67), membrane, rot=(0, s * -0.32, 0), verts=10, r2=0.003)
        A.sphere(f"BatEye{s}", 0.036, (s * 0.08, 0.875, 0.50), M["crimson_enamel"], seg=14, rings=8)
        A.cyl(f"BatFang{s}", 0.012, 0.05, (s * 0.035, 0.877, 0.35), M["bone"], verts=8, r2=0.001)
    A.sphere("BatNose", 0.038, (0, 0.89, 0.42), hide, scale=(1.3, 0.8, 0.8), seg=12, rings=8)
    # the wings: membranes between three fingers with a scalloped trailing edge, the arm and finger bones on top and a
    # thumb claw at the wrist. Flat behind the pack (BAT_Y), so they sway back as you run (BackHang)
    W = BAT_WING
    for s in (1, -1):
        r, w = W["root"], W["wrist"]
        t1, t2, t3 = W["tips"]
        edge = [r, w, t1] + _scallop(t1, t2, 0.07, toward=w) + _scallop(t2, t3, 0.07, toward=w) \
            + _scallop(t3, W["body"], 0.08, toward=w)
        A.extrude_poly(f"BatWing{s}", ccw([(s * x, z) for x, z in edge]), 0.012, membrane, frame((0, BAT_Y + 0.006, 0)),
                       bevel=0.003, segments=1)
        A.tube(f"BatArm{s}", [_bat_pt(s, r, 0.010), _bat_pt(s, ((r[0] + w[0]) / 2, (r[1] + w[1]) / 2 + 0.03), 0.012),
                              _bat_pt(s, w, 0.012)], 0.016, finger, res=8)
        for k, t in enumerate((t1, t2, t3)):
            A.tube(f"BatFinger{s}_{k}", [_bat_pt(s, w, 0.012), _bat_pt(s, t, 0.010)], 0.009, finger, res=6,
                   taper=lambda u: 1.0 - 0.6 * u)
        A.cyl(f"BatThumb{s}", 0.014, 0.06, tuple(_bat_pt(s, (w[0] - 0.02, w[1] + 0.05), 0.012)), M["bone"],
              rot=(0, s * 0.5, 0), verts=8, r2=0.002)
    wrap_straps(M, "Bat", pack_half_x=0.36, pack_back_y=0.55, tab_z=0.18)
    return {"notes": "Kit C8: a black leather bat as a backpack (pug face, tall ears, crimson glass eyes, little fangs), "
                     "a scalloped flap with a brass crescent clasp, wings that sway back as you run (BackHang); straps "
                     "wrap the torso with a chest strap joining them"}


# ---------------------------------------------------------------- 3. the violin case
def _violin_half(z):
    """the case's half-width at height z: the lower bout, the waist, the upper bout, then the neck end"""
    pts = [(-0.72, 0.13), (-0.66, 0.30), (-0.52, 0.39), (-0.34, 0.39), (-0.14, 0.32), (0.02, 0.28), (0.18, 0.31),
           (0.36, 0.30), (0.52, 0.21), (0.68, 0.165), (0.80, 0.15), (0.88, 0.09)]
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, w0), (z1, w1) in zip(pts, pts[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0)
            return lerp(w0, w1, t * t * (3 - 2 * t))
    return pts[-1][1]


def violin_outline(n=40):
    z0, z1 = -0.72, 0.88
    right = [(-_violin_half(lerp(z0, z1, i / n)), lerp(z0, z1, i / n)) for i in range(n + 1)]
    left = [(_violin_half(lerp(z1, z0, i / n)), lerp(z1, z0, i / n)) for i in range(n + 1)]
    top = [(-0.09 * math.cos(math.pi * i / 8), z1 + 0.03 * math.sin(math.pi * i / 8)) for i in range(1, 8)]
    bot = [(0.13 * math.cos(math.pi * i / 8), z0 - 0.035 * math.sin(math.pi * i / 8)) for i in range(1, 8)]
    return ccw(right + top + left + bot)


@item("ViolinCase", "Violin case", views=["back", "back34", "side", "front34"],
      close=((-3.6, 6.2, 0.8), (0, 0.6, 0.0), 80))
def build_violin(M):
    piece("ViolinCase", "Torso")
    shell = A.mat_leather("ViolinShell", (0.035, 0.03, 0.035), scale=3.0, wear=0.45)
    piping = A.mat_leather("ViolinPiping", (0.32, 0.03, 0.05), scale=4.0, wear=0.2)
    out = violin_outline()
    # the shell from y 0.56 back to 0.82; a crimson piping where lid meets base and round the lid's crown
    A.extrude_poly("ViolinBody", out, 0.26, shell, frame((0, 0.82, 0)), bevel=0.05, segments=4)
    A.tube("ViolinSeam", [(x, 0.70, z) for x, z in offset_poly(out, -0.004)], 0.012, piping, closed=True, res=6, poly=True)
    A.tube("ViolinLidRim", [(x, 0.818, z) for x, z in offset_poly(out, 0.055)], 0.008, piping, closed=True, res=6,
           poly=True)
    # brass caps hugging both rounded ends (any lower, the bottom one meets a striding leg's top corner)
    for k, (zc, r) in enumerate(((-0.69, 0.095), (0.86, 0.085))):
        A.cyl(f"ViolinCap{k}", r, 0.24, (0, 0.69, zc), M["brassold"], rot=(HP, 0, 0), verts=24, bevel=0.01)
    # two brass latches on the right edge, a leather carry handle on the left edge, a name plate on the lid
    for k, z in enumerate((-0.40, 0.30)):
        x = -_violin_half(z) - 0.012
        A.box(f"ViolinLatch{k}", (0.03, 0.10, 0.07), (x, 0.70, z), M["brass"], bevel=0.008)
        A.cyl(f"ViolinLatchPin{k}", 0.012, 0.10, (x - 0.016, 0.70, z), M["brassold"], rot=(HP, 0, 0), verts=10)
    xh = _violin_half(-0.05) + 0.010
    A.tube("ViolinHandle", [(xh, 0.64, -0.18), (xh + 0.07, 0.66, -0.12), (xh + 0.08, 0.70, -0.05), (xh + 0.07, 0.74, 0.02),
                            (xh, 0.76, 0.08)], 0.018, M["leather_black"], res=8)
    for k, (y, z) in enumerate(((0.64, -0.18), (0.76, 0.08))):
        A.box(f"ViolinHandleMount{k}", (0.03, 0.05, 0.05), (xh - 0.008, y, z), M["brass"], bevel=0.006)
    plate = [(0.11 * math.cos(2 * math.pi * i / 24), 0.06 * math.sin(2 * math.pi * i / 24)) for i in range(24)]
    A.extrude_poly("ViolinPlate", ccw([(x, z - 0.44) for x, z in plate]), 0.008, M["brass"], frame((0, 0.828, 0)),
                   bevel=0.002)
    A.text_mesh("ViolinPlateText", "N . H", 0.055, M["black_enamel"], frame((0, 0.833, -0.458), (HP, 0, math.pi)),
                depth=0.004)
    # brass studs round the bouts
    for s in (1, -1):
        for k, z in enumerate((-0.52, 0.22)):
            A.sphere(f"ViolinStud{s}_{k}", 0.024, (s * (_violin_half(z) - 0.025), 0.823, z), M["brassold"], seg=10, rings=6)
    wrap_straps(M, "Violin", pack_half_x=0.30, pack_back_y=0.56, tab_x=0.15)
    return {"notes": "Kit C8: a shaped violin case in pebbled black leather with crimson piping, brass end caps, latches, "
                     "corner studs and an N.H name plate; straps wrap the torso with a chest strap joining them"}


# ---------------------------------------------------------------- 4. the alchemist's Gladstone bag (held)
GRIP = Vector((-1.5, 0.0, -1.03))   # the right hand: the bottom of the right arm, where the book strap is held


def _gladstone_rig(ob):
    return A.pendulum_rig(ob, GRIP, [Vector((-1.5, 0, -1.26)), Vector((-1.5, 0, -1.62))])


def gladstone_profile(zb, zt, wb, wt, r=0.07, n=6):
    """the bag's end profile (x, z about the bag's centre line): a wide, rounded bottom narrowing to the frame"""
    pts = []
    for cx, cz, a0, a1 in ((-wb / 2 + r, zb + r, math.pi, 1.5 * math.pi), (wb / 2 - r, zb + r, 1.5 * math.pi, 2 * math.pi)):
        for i in range(n + 1):
            a = lerp(a0, a1, i / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    pts += [(wt / 2 + 0.01, zt - 0.03), (wt / 2, zt), (-wt / 2, zt), (-wt / 2 - 0.01, zt - 0.03)]
    return ccw(pts)


@item("GladstoneBag", "Alchemist's Gladstone bag", views=["front34", "front", "side_r", "close"],
      close=((-4.8, -4.4, -0.6), (-1.5, 0, -1.45), 80))
def build_gladstone(M):
    piece("GladstoneBag", "RightArm", rig=_gladstone_rig, sway="Pendulum", keepout=(1, 0, 0))
    hide = A.mat_leather("GladstoneHide", (0.13, 0.02, 0.025), scale=2.4, wear=0.55)
    base = A.mat_leather("GladstoneBase", (0.07, 0.03, 0.03), scale=2.8, wear=0.4)
    zt, zb = -1.30, -1.85
    L = 0.96                                  # along Y (fore and aft, clear of the leg)
    prof = [(x - 1.5, z) for x, z in gladstone_profile(zb, zt, 0.36, 0.13)]
    A.extrude_poly("GladstoneBody", ccw(prof), L, hide, frame((0, L / 2, 0)), bevel=0.05, segments=4)
    # a darker stitched base panel, brass feet at the corners
    A.box("GladstoneBasePanel", (0.36, L - 0.02, 0.05), (-1.5, 0, zb + 0.03), base, bevel=0.02, segments=2)
    for sx in (1, -1):
        for sy in (1, -1):
            A.sphere(f"GladstoneFoot{sx}{sy}", 0.028, (-1.5 + sx * 0.12, sy * (L / 2 - 0.08), zb - 0.002), M["brassold"],
                     scale=(1, 1, 0.6), seg=10, rings=6)
    # the hinged brass frame along the mouth, its end hinges and a clasp at the middle
    for sx in (1, -1):
        A.tube(f"GladstoneRail{sx}", [(-1.5 + sx * 0.065, -L / 2 + 0.07, zt + 0.006), (-1.5 + sx * 0.065, L / 2 - 0.07, zt + 0.006)],
               0.014, M["brass"], res=8)
    for sy in (1, -1):
        A.cyl(f"GladstoneHinge{sy}", 0.022, 0.13, (-1.5, sy * (L / 2 - 0.07), zt + 0.006), M["brassold"], rot=(0, HP, 0),
              verts=12)
    A.box("GladstoneClasp", (0.13, 0.09, 0.05), (-1.5, 0.0, zt + 0.02), M["brass"], bevel=0.01)
    A.cyl("GladstoneLock", 0.016, 0.02, (-1.5 - 0.066, 0.0, zt + 0.02), M["iron"], rot=(0, HP, 0), verts=10)
    # the handle: one leather grip on brass loops at both rails' middles, up into the hand
    A.tube("GladstoneHandle", [(-1.5, -0.13, zt + 0.02), (-1.5, -0.12, zt + 0.12), (-1.5, -0.06, GRIP.z - 0.01),
                               (-1.5, 0.06, GRIP.z - 0.01), (-1.5, 0.12, zt + 0.12), (-1.5, 0.13, zt + 0.02)], 0.024,
           M["leather_black"], res=10)
    for sy in (1, -1):
        A.torus(f"GladstoneLoop{sy}", 0.03, 0.007, (-1.5, sy * 0.13, zt + 0.03), M["brass"], rot=(0, HP, 0), major=12,
                minor=5)
    # two leather straps round the girth with buckles on the outer side (-X)
    for k, y in enumerate((-0.27, 0.27)):
        ring = [(x, z) for x, z in offset_poly(prof, -0.008)]
        A.tube(f"GladstoneStrap{k}", [(x, y, z) for x, z in ring], 0.012, M["leather_black"], closed=True, res=4,
               square=True, poly=True)
        buckle(f"GladstoneBuckle{k}", (-1.5 - 0.183, y, zb + 0.17), 0.07, 0.09, M["brass"], rot=(0, 0, -HP))
    # a brass plate on the outer side with the alchemists' sigil: a circle round a triangle and a crescent
    Fp = Matrix.Translation((-1.5 - 0.172, 0.0, zb + 0.22)) @ Matrix.Rotation(HP, 4, "Z")
    A.extrude_poly("GladstonePlate", A.circle_pts(0, 0, 0.07, 32), 0.008, M["brass"], Fp, bevel=0.002)
    A.extrude_poly("GladstoneSigilRing", A.circle_pts(0, 0, 0.055, 32), 0.012, M["black_enamel"], Fp, bevel=0.0,
                   holes=[A.circle_pts(0, 0, 0.047, 32)[::-1]])
    tri = ccw([(0.0, 0.045), (0.039, -0.0225), (-0.039, -0.0225)])
    A.extrude_poly("GladstoneSigilTri", tri, 0.012, M["black_enamel"], Fp, bevel=0.0, holes=[ccw(offset_poly(tri, 0.008))[::-1]])
    return {"notes": "Kit C8: an oxblood leather doctor's bag on a hinged brass frame, two girth straps with buckles, "
                     "brass feet and an alchemist's sigil plate; held in the right hand, swings from the grip"}


# ---------------------------------------------------------------- 5. the scroll tube (slung over the left shoulder)
@item("ScrollTube", "Scroll tube", views=["back", "back34", "front34", "side"],
      close=((-3.6, 6.2, 0.8), (0, 0.6, 0.2), 80))
def build_scrolltube(M):
    from nh_acc_batch1 import sash_plane
    piece("ScrollTube", "Torso")
    hide = A.mat_leather("TubeHide", (0.20, 0.10, 0.05), scale=2.6, wear=0.55)
    strap_m = M["leather_black"]
    # the sling: over the left shoulder (clear of the hair) to the right hip, like the sashes (the sword is at the left)
    c, n, d = sash_plane(True, 0.86)
    G = band_loop(c, n, 0.11, 0.052)
    A.surface("TubeSling", G, 0.012, strap_m)
    # the tube lies on the sling's back run: along d, centred a little above the sling's middle
    axis = Vector((d.x, 0, d.z)).normalized()
    centre = Vector((c.x + axis.x * 0.06, 0.5 + 0.064 + 0.155, c.z + axis.z * 0.06))
    ang = math.atan2(axis.x, axis.z)
    rot = (0, ang, 0)
    half = 0.76
    body = [(0.0, -half + 0.06), (0.15, -half + 0.06), (0.15, half - 0.06), (0.0, half - 0.06)]
    A.lathe("TubeBody", body, tuple(centre), hide, seg=32, rot=rot)
    # brass end caps (the top one a screw cap with a ring), three tooled brass bands
    capb = [(0.0, -half), (0.145, -half), (0.165, -half + 0.012), (0.165, -half + 0.10), (0.153, -half + 0.11),
            (0.0, -half + 0.11)]
    capt = [(0.0, half), (0.13, half), (0.165, half - 0.016), (0.165, half - 0.12), (0.153, half - 0.13),
            (0.0, half - 0.13)]
    A.lathe("TubeCapLow", capb, tuple(centre), M["brassold"], seg=32, rot=rot)
    A.lathe("TubeCapTop", capt, tuple(centre), M["brass"], seg=32, rot=rot)
    tip = centre + axis * (half + 0.035)
    A.torus("TubeCapRing", 0.04, 0.009, tuple(tip), M["brass"], rot=(0, ang, 0), major=14, minor=6)
    for k, t in enumerate((-0.32, 0.0, 0.32)):
        A.lathe(f"TubeBand{k}", [(0.0, t - 0.025), (0.158, t - 0.025), (0.162, t), (0.158, t + 0.025), (0.0, t + 0.025)],
                tuple(centre), M["brassold"], seg=32, rot=rot)
    # two leather loops tie the tube onto the sling
    for k, t in enumerate((-0.45, 0.45)):
        p = centre + axis * t
        A.torus(f"TubeLoop{k}", 0.16, 0.012, tuple(p), strap_m, rot=(0, ang, 0), major=32, minor=6)
    # a crescent badge on the top band and a brass buckle on the chest
    A.extrude_poly("TubeBadge", crescent(0.0, 0.0, 0.06, 0.03, 0.018, 0.05), 0.012, M["gold"],
                   frame(tuple(centre + axis * 0.16 + Vector((0, 0.16, 0))), (0, ang, 0)), bevel=0.003)
    chest = c + Vector((0, -0.552, 0)) + d * 0.18
    buckle("TubeBuckle", (chest.x, -0.566, chest.z), 0.13, 0.10, M["brass"], rot=(0, ang, 0))
    return {"notes": "Kit C8: a tan leather scroll tube with brass end caps (a screw cap with a ring), tooled bands and a "
                     "gold crescent badge, slung on a black strap over the left shoulder to the right hip"}


# ---------------------------------------------------------------- 6. the birdcage purse with a paper moth (held)
CAGE_C = Vector((-1.5, 0.0, -1.50))   # the cage's axis and the moth's perch height
CAGE_R = 0.17


def _cage_rig(ob):
    """a pendulum from the grip (Root, H0, C0_1, C0_2) and the moth's two wings (WingL, WingR on C0_2, along the moth's
    body: turning about their length opens and closes the wings, AccessoryFx's Familiar idle)"""
    piv, l1, l2 = GRIP, Vector((-1.5, 0, -1.20)), Vector((-1.5, 0, -1.40))
    mz0, mz1 = CAGE_C.z - 0.045, CAGE_C.z + 0.045
    bones = [("Root", piv, piv + Vector((0, 0, 0.08)), None), ("H0", piv, piv + (l1 - piv) * 0.25, "Root"),
             ("C0_1", piv, l1, "H0"), ("C0_2", l1, l2, "C0_1"),
             ("WingL", Vector((-1.5, 0.006, mz0)), Vector((-1.5, 0.006, mz1)), "C0_2"),
             ("WingR", Vector((-1.5, -0.006, mz1)), Vector((-1.5, -0.006, mz0)), "C0_2")]

    def wfn(co):
        # the moth's wings: flat in the y-z plane through the cage's axis, beside the body
        if abs(co.x - CAGE_C.x) < 0.012 and 0.010 < abs(co.y) < 0.11 and abs(co.z - CAGE_C.z) < 0.07:
            return {"WingL" if co.y > 0 else "WingR": 1.0}
        if co.z > piv.z + 0.01:
            return {"Root": 1.0}
        if co.z > l1.z:
            f = (piv.z - co.z) / (piv.z - l1.z)
            return {"H0": max(0.0, 0.3 - f), "C0_1": min(1.0, 0.7 + f)}
        if co.z > l1.z - 0.06:
            f = (l1.z - co.z) / 0.06
            return {"C0_1": 1 - f, "C0_2": f}
        return {"C0_2": 1.0}
    return A.make_rig(ob, bones, wfn), bones


@item("BirdcagePurse", "Birdcage purse", views=["front34", "front", "side_r", "close"],
      close=((-4.2, -3.8, -0.9), (-1.5, 0, -1.45), 75))
def build_birdcage(M):
    from nh_acc_batchc1 import write_extra
    piece("BirdcagePurse", "RightArm", rig=_cage_rig, sway="Pendulum", keepout=(1, 0, 0))
    cx, cy = CAGE_C.x, CAGE_C.y
    z_base, z_ring, z_dome = -1.66, -1.36, -1.17
    velvet, brass, wire = M["crimson_velvet"], M["brass"], M["brassold"]
    # the purse: a velvet drum under the cage with a brass rim and a little clasp
    A.cyl("CageDrum", CAGE_R + 0.025, 0.10, (cx, cy, z_base - 0.05), velvet, verts=40, bevel=0.02)
    for k, z in enumerate((z_base, z_base - 0.10)):
        A.torus(f"CageRim{k}", CAGE_R + 0.027, 0.010, (cx, cy, z), brass, major=40, minor=6)
    A.box("CageClasp", (0.012, 0.05, 0.05), (cx - CAGE_R - 0.035, cy, z_base - 0.05), brass, bevel=0.006)
    # the cage: 18 bars from the base ring up the wall and over the dome to the finial, two rings round it
    nbar = 18
    for i in range(nbar):
        a = 2 * math.pi * i / nbar
        pts = [(cx + CAGE_R * math.cos(a), cy + CAGE_R * math.sin(a), z) for z in (z_base, z_ring)]
        for j in range(1, 7):
            t = j / 6
            r = CAGE_R * math.cos(t * HP)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z_ring + (z_dome - z_ring) * math.sin(t * HP)))
        A.tube(f"CageBar{i}", pts[:-1], 0.0055, wire, res=5)
    for k, z in enumerate((z_ring, (z_base + z_ring) / 2)):
        A.torus(f"CageHoop{k}", CAGE_R + 0.002, 0.008, (cx, cy, z), brass, major=40, minor=6)
    # the finial, a hanging ring the hand closes on, and a small door on the outer side with a latch
    A.lathe("CageFinial", [(0.0, 0.0), (0.035, 0.005), (0.028, 0.03), (0.012, 0.05), (0.016, 0.07), (0.0, 0.08)],
            (cx, cy, z_dome - 0.01), brass, seg=20)
    A.torus("CageHanger", 0.045, 0.009, (cx, cy, GRIP.z - 0.05), brass, rot=(HP, 0, 0), major=20, minor=6)
    door = [(cx - CAGE_R * math.cos(a), cy + CAGE_R * math.sin(a)) for a in (-0.30, 0.30)]
    for k, (x, y) in enumerate(door):
        A.tube(f"CageDoorPost{k}", [(x - 0.004, y, z_base + 0.02), (x - 0.004, y, z_ring - 0.03)], 0.007, brass, res=5)
    A.tube("CageDoorTop", [(door[0][0] - 0.004, door[0][1], z_ring - 0.03), (cx - CAGE_R - 0.006, cy, z_ring - 0.01),
                           (door[1][0] - 0.004, door[1][1], z_ring - 0.03)], 0.007, brass, res=5)
    A.sphere("CageLatch", 0.012, (cx - CAGE_R - 0.012, cy - 0.04, (z_base + z_ring) / 2), brass, seg=8, rings=6)
    # the perch across the cage, and the paper moth clinging to it, wings half open
    A.tube("CagePerch", [(cx - CAGE_R + 0.01, cy, CAGE_C.z - 0.07), (cx + CAGE_R - 0.01, cy, CAGE_C.z - 0.07)], 0.009,
           M["leather_brown"], res=6)
    paper = A.mat_set("MothPaper", "NH_Paper", tint=(0.86, 0.80, 0.66), scale=3.0, wear=0.2, dirt=0.5)
    ink = A.mat_flat("MothInk", (0.30, 0.03, 0.05), rough=0.6, noise=80, bump=0.02, wear=0.0, dirt=0.2)
    A.sphere("MothBody", 0.016, (cx, cy, CAGE_C.z), M["black_wool"], scale=(1, 1, 3.0), seg=12, rings=8)
    A.sphere("MothHead", 0.014, (cx, cy, CAGE_C.z + 0.052), M["black_wool"], seg=10, rings=6)
    for s in (1, -1):
        fore = [(0.010, 0.030), (0.040, 0.050), (0.085, 0.045), (0.098, 0.020), (0.070, -0.004), (0.012, -0.004)]
        hind = [(0.010, -0.004), (0.060, -0.010), (0.072, -0.040), (0.040, -0.060), (0.012, -0.030)]
        for nm, poly in (("Fore", fore), ("Hind", hind)):
            pts = ccw([(s * u, v) for u, v in poly])
            # the wing lies in the y-z plane: extrude_poly draws (x, z), so turn it a quarter about Z
            F = Matrix.Translation((cx + 0.003, cy, CAGE_C.z)) @ Matrix.Rotation(HP, 4, "Z")
            A.extrude_poly(f"Moth{nm}{s}", pts, 0.004, paper, F, bevel=0.0, segments=1)
        Fs = Matrix.Translation((cx - 0.002, cy, CAGE_C.z)) @ Matrix.Rotation(HP, 4, "Z")
        A.extrude_poly(f"MothSpot{s}", A.circle_pts(s * 0.058, 0.024, 0.011, 16), 0.002, ink, Fs, bevel=0.0)
        A.tube(f"MothFeeler{s}", [(cx, cy + s * 0.004, CAGE_C.z + 0.062), (cx - 0.004, cy + s * 0.022, CAGE_C.z + 0.095)],
               0.0018, M["black_wool"], res=4)
    write_extra("BirdcagePurse", {"BirdcagePurse": {
        "idle": "Familiar",
        "bones": {"WingL": {"axis": [0, 1, 0], "min": 0, "max": 32}, "WingR": {"axis": [0, 1, 0], "min": 0, "max": 32}}}})
    return {"notes": "Kit C8: a domed brass birdcage purse on a crimson velvet drum, held in the right hand by its ring, "
                     "with a paper moth on the perch inside that opens and closes its wings now and then (AccessoryFx "
                     "Familiar idle); swings from the grip"}
