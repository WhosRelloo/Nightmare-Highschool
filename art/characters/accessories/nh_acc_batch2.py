"""Accessories batch 2: headwear (Kit A 8-12).

  Hats           tricorn, top hat and bowler, each with a crimson band (3 pieces, one atlas)
  MourningHats   a veiled mourning toque (net veil to the chin) and a crimson fascinator with a birdcage veil
  WitchHat       a crooked witch hat (the tip flops on a 3-bone chain)
  HunterHat      the hunter's wide-brim with a silver-buckled band
  Masks          masquerade half-masks: black lace, carved bone, gilt (3 pieces)
Head space: the head part's centre is (0, 0, 1.5); the R6 head mesh is a 0.6-radius rounded cylinder from z 0.9 to
2.1; hair sits to about r 0.66 and z 2.17. Hats seat their headband at z 1.93, inner radius 0.69.
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch2 --gpu
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import nh_acc as A
from nh_acc import item, piece, lerp, smooth
from nh_acc_batch1 import frame, offset_poly, ccw, bez, crescent, rosette, buckle

A.MANNEQUIN_HAIR = {"male": "Males_Short", "female": "Females_Straight_Bob"}
SEAT = 1.93
RIN = 0.69
HEAD_CLOSE = ((3.6, -5.6, 2.6), (0, 0, 2.05), 92)


def tilt(ob, rx=0.0, ry=0.0, about=(0, 0, SEAT)):
    """tilt a finished part about the headband centre (rx: back/forward, ry: to the side)"""
    c = Vector(about)
    M = Matrix.Translation(c) @ Euler((rx, ry, 0)).to_matrix().to_4x4() @ Matrix.Translation(-c)
    ob.matrix_world = M @ ob.matrix_world


def ring_surface(name, r0, r1, zfun, rfun, mat, nu=72, nv=6, thick=0.03, sy=1.0):
    """a brim: points (r, theta) from r0 to rfun(theta) at height zfun(r_t, theta) (r_t in 0..1)"""
    G = []
    for i in range(nu + 1):
        th = 2 * math.pi * i / nu
        col = []
        R1 = rfun(th)
        for j in range(nv + 1):
            t = j / nv
            r = lerp(r0, R1, t)
            z, rr = zfun(t, th, r)
            col.append(Vector((rr * math.cos(th), rr * math.sin(th) * sy, z)))
        G.append(col)
    return A.surface(name, G, thick, mat), G


def edge_cord(name, G, r, mat, step=2):
    pts = [tuple(G[i][-1]) for i in range(0, len(G) - 1, step)]
    return A.tube(name, pts, r, mat, closed=True, res=3)


def band(name, z0, z1, r, mat, sy=1.0, seg=48):
    return A.lathe(name, [(r - 0.002, z0), (r + 0.012, z0 + 0.008), (r + 0.014, z1 - 0.008), (r - 0.002, z1)], (0, 0, 0), mat,
                   seg=seg, scale=(1, sy, 1))


def bow(name, at, mat, w=0.12, side=1):
    """a small flat ribbon bow on a hatband, facing out along +-X"""
    x, y, z = at
    for k in (-1, 1):
        A.sphere(f"{name}_l{k}", w * 0.55, (x + side * 0.02, y + k * w * 0.55, z), mat, scale=(0.35, 1.2, 0.7), seg=12, rings=8)
    A.sphere(f"{name}_k", w * 0.28, (x + side * 0.035, y, z), mat, scale=(0.6, 0.8, 1.0), seg=10, rings=6)


def felt(name, rgb, rough=0.86):
    return A.mat_cloth(name, rgb, weave=900, rough=rough, sheen=0.18, bump=0.05, twill=False, vary=0.05)


# ================================================================== 8. tricorn, top hat, bowler
@item("Hats", "Tricorn, top hat and bowler", close=HEAD_CLOSE, each=True)
def build_hats(M):
    crimson = A.mat_cloth("HatBandCrimson", (0.21, 0.018, 0.035), weave=700, rough=0.5, sheen=0.4, bump=0.12, twill=False)
    black = felt("HatFelt", (0.022, 0.020, 0.025))
    plush = A.mat_cloth("SilkPlush", (0.016, 0.015, 0.019), weave=1400, rough=0.32, sheen=0.35, bump=0.02, twill=False)
    gold = M["gold"]
    brass = M["brass"]
    lining = A.mat_cloth("HatLining", (0.20, 0.02, 0.04), weave=500, rough=0.4, sheen=0.5, bump=0.03, twill=False)

    # ---- top hat
    piece("TopHat", "Head")
    A.lathe("TopCrown", [(RIN, SEAT), (RIN + 0.012, SEAT + 0.35), (RIN + 0.03, SEAT + 0.75), (RIN + 0.055, SEAT + 1.05),
                         (RIN + 0.05, SEAT + 1.08), (RIN - 0.02, SEAT + 1.095), (0.0, SEAT + 1.10)], (0, 0, 0), plush, seg=64,
            scale=(1, 0.94, 1))
    A.lathe("TopLining", [(0.0, SEAT + 0.4), (RIN - 0.02, SEAT + 0.4), (RIN - 0.015, SEAT)], (0, 0, 0), lining, seg=48, scale=(1, 0.94, 1))
    brim, G = ring_surface("TopBrim", RIN - 0.01, 1.0,
                           lambda t, th, r: (SEAT + 0.005 + 0.20 * (abs(math.cos(th)) ** 2) * t ** 2.2 - 0.02 * t,
                                             r - 0.05 * (abs(math.cos(th)) ** 2) * t ** 3),
                           lambda th: 1.04 - 0.06 * abs(math.cos(th)), plush, thick=0.028, sy=0.95)
    edge_cord("TopBrimBind", G, 0.018, plush)
    band("TopBand", SEAT + 0.01, SEAT + 0.19, RIN + 0.004, crimson, sy=0.94)
    bow("TopBow", (RIN + 0.02, 0.0, SEAT + 0.10), crimson, 0.13, side=1)
    A.box("TopBuckle", (0.02, 0.09, 0.07), (RIN + 0.04, 0.0, SEAT + 0.10), brass, bevel=0.006)

    # ---- bowler
    piece("Bowler", "Head")
    A.lathe("BowlerCrown", [(RIN, SEAT), (RIN + 0.02, SEAT + 0.16), (RIN + 0.01, SEAT + 0.33), (0.62, SEAT + 0.48), (0.47, SEAT + 0.6),
                            (0.26, SEAT + 0.665), (0.0, SEAT + 0.68)], (0, 0, 0), black, seg=48, scale=(1, 0.94, 1))
    A.lathe("BowlerLining", [(0.0, SEAT + 0.3), (RIN - 0.02, SEAT + 0.3), (RIN - 0.015, SEAT)], (0, 0, 0), lining, seg=48, scale=(1, 0.94, 1))
    brim, G = ring_surface("BowlerBrim", RIN - 0.01, 0.95,
                           lambda t, th, r: (SEAT + 0.003 + 0.22 * (abs(math.cos(th)) ** 1.5) * t ** 2.4 + 0.02 * t ** 4,
                                             r - 0.06 * (abs(math.cos(th)) ** 1.5) * t ** 3),
                           lambda th: 0.95 - 0.04 * abs(math.cos(th)), black, thick=0.026, sy=0.95)
    edge_cord("BowlerBind", G, 0.016, A.mat_cloth("Grosgrain", (0.02, 0.018, 0.022), weave=300, rough=0.6, sheen=0.4, bump=0.25, twill=False))
    band("BowlerBand", SEAT + 0.01, SEAT + 0.13, RIN + 0.008, crimson, sy=0.94)
    bow("BowlerBow", (RIN + 0.03, 0.0, SEAT + 0.07), crimson, 0.10, side=1)

    # ---- tricorn: a low crown, the brim cocked up on three sides, points front and back corners
    piece("Tricorn", "Head")
    A.lathe("TriCrown", [(RIN, SEAT), (RIN + 0.01, SEAT + 0.18), (0.62, SEAT + 0.36), (0.40, SEAT + 0.48), (0.0, SEAT + 0.52)],
            (0, 0, 0), black, seg=48, scale=(1, 0.94, 1))
    band("TriBand", SEAT + 0.01, SEAT + 0.11, RIN + 0.006, crimson, sy=0.94)
    corners = [math.radians(-90), math.radians(30), math.radians(150)]
    mids = [c + math.radians(60) for c in corners]

    def corner_w(th):
        return max(math.exp(-((math.atan2(math.sin(th - c), math.cos(th - c))) / 0.22) ** 2) for c in corners)

    def fold_r(th):
        # distance to the triangle whose side midpoints touch the crown (r 0.74), capped at the corners
        d = min(abs(math.atan2(math.sin(th - m), math.cos(th - m))) for m in mids)
        return min(1.18, 0.74 / max(0.2, math.cos(d)))

    def zf(t, th, r):
        f = fold_r(th)
        R1 = f + 0.40
        r = lerp(RIN - 0.01, R1, t)
        if r <= f:
            return SEAT + 0.006 + 0.03 * smooth(RIN, f, r), r
        w = corner_w(th)
        up = lerp(math.radians(84), math.radians(12), w)
        d = r - f
        return SEAT + 0.036 + d * math.sin(up), f + d * math.cos(up)
    brim, G = ring_surface("TriBrim", RIN - 0.01, 1.6, zf, lambda th: 1.6, black, nu=180, nv=12, thick=0.03, sy=0.96)
    edge_cord("TriBraid", G, 0.022, gold, step=3)
    # the cockade on the front-left wall: a crimson rosette and a brass button
    a = math.radians(-30)
    p = Vector((0.80 * math.cos(a), 0.80 * math.sin(a) * 0.96, SEAT + 0.24))
    ros = A.lathe("TriCockade", [(0.0, 0.0), (0.12, -0.01), (0.15, 0.0), (0.12, 0.012), (0.0, 0.02)], (0, 0, 0), crimson, seg=40)
    ros.matrix_world = Matrix.Translation(p) @ (Vector((math.cos(a), math.sin(a), 0.25))).to_track_quat("Z", "Y").to_matrix().to_4x4()
    A.sphere("TriButton", 0.045, p + Vector((math.cos(a), math.sin(a), 0.2)).normalized() * 0.03, brass, seg=12, rings=8)
    return dict(notes="black felt and silk plush; crimson bands; the tricorn has a gold braid edge and a crimson cockade")


# ================================================================== 9. veiled mourning toque, fascinator
@item("MourningHats", "Veiled mourning hat and fascinator", close=HEAD_CLOSE,
      each={"Toque": ["MourningToque", "MourningVeil"], "Fascinator": ["Fascinator", "FascVeil"]})
def build_mourning(M):
    velvet = M["black_velvet"]
    satin = A.mat_cloth("MourningSatin", (0.018, 0.016, 0.02), weave=800, rough=0.28, sheen=0.7, bump=0.02, twill=False)
    jet = A.mat_flat("Jet", (0.01, 0.01, 0.012), rough=0.08, coat=1.0, noise=60, bump=0.01, vary=0.02, wear=0.0)
    crimson_v = M["crimson_velvet"]
    feather_b = A.mat_cloth("FeatherBlack", (0.02, 0.018, 0.022), weave=2200, rough=0.45, sheen=0.8, bump=0.35, twill=False)
    feather_c = A.mat_cloth("FeatherCrimson", (0.20, 0.015, 0.03), weave=2200, rough=0.45, sheen=0.8, bump=0.35, twill=False)
    silver = M["silver"]

    def feather(name, base, d1, length, width, mat, curl=0.4):
        """a curling plume: a tapered vane on a quill, bending along its length"""
        d1 = Vector(d1).normalized()
        side = d1.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d1).normalized()
        G = []
        for i in range(5):
            u = i / 4 - 0.5
            col = []
            for j in range(13):
                t = j / 12
                ang = curl * t * t * 2.2
                d = d1 * math.cos(ang) + up * math.sin(ang)
                p = Vector(base) + d * (length * t) + side * (u * width * math.sin(math.pi * min(1, t * 1.1)) ** 0.7)
                p += up * 0.02 * (abs(u) * 2) ** 2
                col.append(p)
            G.append(col)
        A.surface(name, G, 0.006, mat)
        A.tube(name + "_quill", [tuple(G[2][j]) for j in range(0, 13, 3)], 0.006, mat, res=3)

    # ---- the mourning toque: a small velvet drum tipped forward, satin roses, a jet pin, a plume and the net veil
    piece("MourningToque", "Head")
    toque = A.lathe("ToqueDrum", [(0.0, 0.0), (0.58, 0.0), (0.63, 0.04), (0.64, 0.30), (0.60, 0.35), (0.0, 0.36)], (0, 0, 0), velvet, seg=48)
    toque.matrix_world = Matrix.Translation((0, 0.06, 2.10)) @ Euler((math.radians(-14), math.radians(8), 0)).to_matrix().to_4x4()
    for k, (x, y) in enumerate(((0.40, -0.40), (0.56, -0.16), (0.26, -0.52))):
        r = A.lathe(f"ToqueRose{k}", [(0.0, 0.0), (0.08, -0.012), (0.12, 0.026), (0.07, 0.07), (0.0, 0.075)], (0, 0, 0), satin, seg=24)
        r.matrix_world = Matrix.Translation((x, y, 2.26 + 0.02 * k)) @ Euler((math.radians(-55), math.radians(25), 0)).to_matrix().to_4x4()
        for q in range(5):   # petals: rolled satin round each rose
            a = 2 * math.pi * q / 5
            A.sphere(f"ToquePetal{k}_{q}", 0.05, (x + 0.08 * math.cos(a), y + 0.08 * math.sin(a), 2.25 + 0.02 * k), satin,
                     scale=(1.0, 0.55, 0.5), seg=10, rings=6, rot=(math.radians(-50), 0, a))
    A.tube("ToquePin", [(0.15, -0.38, 2.36), (0.32, -0.12, 2.30), (0.50, 0.12, 2.22)], 0.007, silver, res=3)
    A.sphere("ToquePinJet", 0.045, (0.13, -0.40, 2.37), jet, seg=14, rings=10)
    feather("ToquePlume", (0.38, 0.05, 2.30), (0.15, 1.0, 0.25), 0.80, 0.22, feather_b, curl=0.55)
    piece("MourningVeil", "Head", kind="Alpha", alpha=f"{A.TEX_DIR}/NHAcc_VeilNet.png", uv=A.uv_cylinder((0, 0, 1.5), 0.32))
    G = []
    for i in range(41):
        a = lerp(math.radians(-200), math.radians(20), i / 40)
        col = []
        for j in range(15):
            t = j / 14
            r = lerp(0.70, 0.80, smooth(0, 0.35, t)) + 0.02 * math.sin(a * 5) * t
            z = lerp(2.16, 1.22, t)
            col.append(Vector((r * math.cos(a), r * math.sin(a) * 1.02, z)))
        G.append(col)
    A.surface("VeilNet", G, 0.002, None, caps=False)

    # ---- the fascinator: a crimson velvet teardrop on the right of the head, three feathers, a crescent, a birdcage veil
    piece("Fascinator", "Head")
    base = A.lathe("FascBase", [(0.0, 0.0), (0.24, 0.0), (0.27, 0.025), (0.24, 0.07), (0.0, 0.085)], (0, 0, 0), crimson_v, seg=40,
                   scale=(1.0, 1.55, 1.0))
    base.matrix_world = Matrix.Translation((-0.50, -0.10, 2.05)) @ Euler((math.radians(-10), math.radians(-34), math.radians(20))).to_matrix().to_4x4()
    feather("FascFeatherA", (-0.52, -0.05, 2.14), (-0.35, 0.6, 0.8), 0.62, 0.15, feather_b, curl=0.6)
    feather("FascFeatherB", (-0.50, -0.12, 2.13), (-0.6, 0.3, 0.6), 0.52, 0.13, feather_c, curl=0.5)
    feather("FascFeatherC", (-0.48, -0.18, 2.12), (-0.5, -0.2, 0.7), 0.42, 0.11, feather_b, curl=0.7)
    F = Matrix.Translation((-0.62, -0.30, 2.08)) @ Matrix.Rotation(math.radians(60), 4, "Z")
    A.extrude_poly("FascCrescent", crescent(0, 0, 0.085, 0.04, 0.02, 0.07), 0.02, silver, F, bevel=0.003, segments=1)
    A.sphere("FascGem", 0.03, (-0.66, -0.32, 2.08), M["crimson_enamel"], seg=12, rings=8)
    piece("FascVeil", "Head", kind="Alpha", alpha=f"{A.TEX_DIR}/NHAcc_VeilNetFine.png", uv=A.uv_cylinder((0, 0, 1.5), 0.22))
    G = []
    for i in range(21):
        a = lerp(math.radians(-175), math.radians(-95), i / 20)
        col = []
        for j in range(9):
            t = j / 8
            r = lerp(0.63, 0.70, t)
            col.append(Vector((r * math.cos(a), r * math.sin(a), lerp(2.06, 1.52, t) + 0.05 * math.sin(math.pi * i / 20) * t)))
        G.append(col)
    A.surface("FascNet", G, 0.002, None, caps=False)
    return dict(notes="black velvet toque with satin roses, a jet hatpin, a plume and a dotted net veil to the chin; a crimson "
                      "velvet fascinator with three feathers, a silver crescent and a birdcage veil over the right eye")


# ================================================================== 10. crooked witch hat
def _witch_rig(ob):
    pts = [Vector((0, 0.02, 2.55)), Vector((0.0, 0.10, 2.95)), Vector((0.05, 0.22, 3.30)), Vector((0.30, 0.30, 3.52))]
    return A.chain_rig(ob, (0, 0, SEAT), [pts])


@item("WitchHat", "Crooked witch hat", close=((4.4, -6.4, 2.9), (0, 0, 2.5), 75))
def build_witch(M):
    felt_v = felt("WitchFelt", (0.035, 0.022, 0.045), rough=0.9)
    violet = A.mat_cloth("WitchBand", (0.10, 0.03, 0.16), weave=600, rough=0.42, sheen=0.5, bump=0.06, twill=False)
    silver = M["silver"]
    piece("WitchHat", "Head", rig=_witch_rig, sway="Tails")
    # brim: wide and floppy, a gentle wave, drooping at the front
    brim, G = ring_surface("WitchBrim", RIN - 0.01, 1.36,
                           lambda t, th, r: (SEAT + 0.004 - 0.10 * t ** 2 * (0.6 + 0.4 * max(0, -math.sin(th)))
                                             + 0.045 * math.sin(3 * th + 0.6) * t ** 1.5, r),
                           lambda th: 1.36 + 0.06 * math.sin(2 * th), felt_v, nu=120, nv=10, thick=0.03, sy=0.97)
    edge_cord("WitchBrimEdge", G, 0.014, felt_v)
    # crown: a cone swept along a crooked axis: up, a kink back, then the tip flops to the left
    axis = []
    for k in range(25):
        t = k / 24
        z = SEAT + t * 1.65
        bend = smooth(0.35, 1.0, t)
        x = 0.30 * bend ** 2.2 + 0.04 * math.sin(t * 9) * t
        y = 0.08 * smooth(0.1, 0.5, t) + 0.30 * bend ** 1.6
        axis.append(Vector((x, y, z)))
    verts, faces = [], []
    ns = 40
    for k, c in enumerate(axis):
        t = k / 24
        r = lerp(RIN + 0.01, 0.015, t ** 0.85) * (1 + 0.06 * math.sin(t * 22) * t)   # a little crumpled
        nxt = axis[min(k + 1, 24)] - axis[max(k - 1, 0)]
        q = nxt.normalized().to_track_quat("Z", "Y").to_matrix()
        for s in range(ns):
            a = 2 * math.pi * s / ns
            dent = 1 - 0.07 * math.exp(-((a - 4.2) / 0.5) ** 2) * smooth(0.3, 0.6, t)
            verts.append(c + q @ Vector((r * dent * math.cos(a), r * dent * math.sin(a) * 0.96, 0)))
    for k in range(24):
        for s in range(ns):
            s2 = (s + 1) % ns
            faces.append([k * ns + s, k * ns + s2, (k + 1) * ns + s2, (k + 1) * ns + s])
    A.mesh_from("WitchCrown", verts, faces, felt_v)
    band("WitchBand", SEAT + 0.01, SEAT + 0.17, RIN + 0.012, violet, sy=0.96)
    # a square silver buckle on the band, front-right, and a stitched patch on the crown
    a = math.radians(-70)
    buckle("WitchBuckle", Vector(((RIN + 0.04) * math.cos(a), (RIN + 0.04) * math.sin(a), SEAT + 0.09)), 0.14, 0.12, silver,
           rot=(0, 0, a + math.pi / 2))
    patch = A.box("WitchPatch", (0.16, 0.012, 0.14), (0.0, 0.0, 0.0), A.mat_cloth("WitchPatchCloth", (0.06, 0.04, 0.05), weave=200, rough=0.9, bump=0.3), bevel=0.005)
    p = axis[9]
    patch.matrix_world = Matrix.Translation(p + Vector((0.28, -0.42, 0))) @ Euler((0.1, 0, math.radians(30))).to_matrix().to_4x4()
    return dict(notes="violet-black felt, crumpled crown that bends back and flops to the left; violet band with a silver "
                      "buckle; a patch; the tip swings on a 3-bone chain")


# ================================================================== 11. the hunter's wide-brim
@item("HunterHat", "Hunter's wide-brim", close=HEAD_CLOSE)
def build_hunter(M):
    hfelt = A.mat_set("HunterFelt", "NH_Leather", tint=(0.12, 0.09, 0.075), scale=1.4, normal=0.35, rough_add=0.1, wear=0.55, dirt=0.8)
    strap = M["leather_black"]
    silver = M["silver"]
    piece("HunterHat", "Head")
    cr = A.lathe("HunterCrown", [(RIN, SEAT), (RIN - 0.01, SEAT + 0.22), (0.64, SEAT + 0.44), (0.58, SEAT + 0.52), (0.40, SEAT + 0.56),
                                 (0.0, SEAT + 0.57)], (0, 0, 0), hfelt, seg=48, scale=(1, 0.92, 1))
    for v in cr.data.vertices:   # the crease: the top dips along the front-back line, pinched in at the front
        h = v.co.z - SEAT
        if h > 0.3:
            v.co.z -= 0.10 * math.exp(-(v.co.x / 0.16) ** 2) * smooth(0.3, 0.55, h)
        if h > 0.2 and v.co.y < 0:
            v.co.x *= 1 - 0.12 * smooth(0.2, 0.55, h) * smooth(0, -0.6, v.co.y)
    brim, G = ring_surface("HunterBrim", RIN - 0.01, 1.42,
                           lambda t, th, r: (SEAT + 0.004 - 0.16 * t ** 1.8 * abs(math.sin(th)) ** 1.5 + 0.05 * t ** 2 * abs(math.cos(th)) ** 2, r),
                           lambda th: 1.42 - 0.08 * abs(math.cos(th)), hfelt, nu=112, nv=10, thick=0.035, sy=0.97)
    edge_cord("HunterBrimEdge", G, 0.016, strap)
    band("HunterBand", SEAT + 0.012, SEAT + 0.13, RIN + 0.008, strap, sy=0.92)
    a = math.radians(-115)
    buckle("HunterBuckle", Vector(((RIN + 0.035) * math.cos(a), (RIN + 0.035) * math.sin(a) * 0.92, SEAT + 0.072)), 0.16, 0.13, silver,
           rot=(0, 0, a + math.pi / 2))
    for k in range(8):
        b = math.radians(-115 + 24 + k * 38)
        A.sphere(f"HunterStud{k}", 0.022, ((RIN + 0.025) * math.cos(b), (RIN + 0.025) * math.sin(b) * 0.92, SEAT + 0.072), silver, seg=10, rings=6)
    # a crow feather tucked into the band at the back-left
    fb = A.mat_cloth("CrowFeather", (0.02, 0.022, 0.03), weave=2200, rough=0.4, sheen=0.9, bump=0.35, twill=False)
    G = []
    for i in range(5):
        u = i / 4 - 0.5
        col = []
        for j in range(11):
            t = j / 10
            col.append(Vector((0.71 + 0.03 * t, 0.10 + 0.55 * t + u * 0.09 * math.sin(math.pi * min(1, t * 1.1)), SEAT + 0.07 + 0.22 * t - 0.05 * t * t)))
        G.append(col)
    A.surface("HunterFeather", G, 0.006, fb)
    return dict(notes="weathered dark felt, a wide brim that droops at the sides; black leather band with a silver buckle and "
                      "studs; a crow feather")


# ================================================================== 12. masquerade half-masks
def mask_outline(style):
    """the mask's outline and eye holes in (x across the face, z) for the front of the head"""
    pts = []
    n = 40
    for i in range(n + 1):
        t = i / n
        x = lerp(-0.46, 0.46, t)
        ax = abs(x)
        # the top: rising cat-eye wings at the temples, a dip over the nose
        top = 1.695 + 0.03 * smooth(0.22, 0.46, ax) ** 1.5 - 0.02 * math.exp(-(x / 0.08) ** 2)   # under the hairline (z ~1.75)
        if style == "bone":
            top += 0.012 * math.exp(-((ax - 0.2) / 0.1) ** 2)         # brow ridges
        pts.append((x, top))
    for i in range(n + 1):
        t = 1 - i / n
        x = lerp(-0.46, 0.46, t)
        ax = abs(x)
        bot = 1.45 + 0.08 * smooth(0.26, 0.46, ax) + 0.07 * math.exp(-((ax - 0.0) / 0.07) ** 2) - 0.035 * math.exp(-((ax - 0.2) / 0.11) ** 2)
        if style == "gilt":
            bot -= 0.05 * math.exp(-((ax - 0.34) / 0.08) ** 2)        # a cheek point
        pts.append((x, bot))
    eyes = []
    for sx in (-1, 1):
        e = []
        for i in range(20):
            a = 2 * math.pi * i / 20
            ex = sx * 0.205 + 0.105 * math.cos(a)
            ez = 1.605 + 0.055 * math.sin(a) + 0.02 * math.cos(a) * sx * (1 if math.sin(a) > 0 else -0.5)
            e.append((ex, ez))
        eyes.append(e)
    return pts, eyes


def wrap_mask(ob, R=0.612, nose=0.03):
    """bend a flat front-facing mask (made at y = 0, front -Y) round the head: x becomes an angle on a radius-R cylinder"""
    me = ob.data
    for v in me.vertices:
        co = ob.matrix_world @ v.co
        ang = co.x / R
        r = R - co.y + nose * math.exp(-(co.x / 0.06) ** 2) * smooth(1.40, 1.55, co.z) * (1 - smooth(1.62, 1.72, co.z))
        v.co = ob.matrix_world.inverted() @ Vector((r * math.sin(ang), -r * math.cos(ang), co.z))
    me.update()


def mask_runs(pts2d, style, margin=0.022):
    """split a decoration curve (x, z) on the mask into runs that stay on the mask: never across an eye hole (plus a
    margin) and never past the outline (play-test review: the filigree crossed the eye holes)"""
    outline, eyes = mask_outline(style)
    n = len(outline) // 2
    top = outline[:n]
    bot = outline[n:][::-1]
    def edge(curve, x):
        for (x0, z0), (x1, z1) in zip(curve, curve[1:]):
            if x0 <= x <= x1 or x1 <= x <= x0:
                t = 0 if x1 == x0 else (x - x0) / (x1 - x0)
                return z0 + (z1 - z0) * t
        return None
    def ok(x, z):
        for sx in (-1, 1):
            if ((x - sx * 0.205) / (0.105 + margin)) ** 2 + ((z - 1.605) / (0.075 + margin)) ** 2 < 1:
                return False
        t, b = edge(top, x), edge(bot, x)
        return t is not None and b is not None and b + margin < z < t - margin
    runs, cur = [], []
    for x, z in pts2d:
        if ok(x, z):
            cur.append((x, z))
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    return runs


@item("Masks", "Masquerade half-masks", close=((2.4, -4.6, 1.95), (0, 0, 1.62), 115),
      each={"Lace": ["LaceMask", "LaceMaskTrim"], "Bone": ["BoneMask"], "Gilt": ["GiltMask"]})
def build_masks(M):
    ribbon = A.mat_cloth("MaskRibbon", (0.02, 0.018, 0.022), weave=800, rough=0.28, sheen=0.7, bump=0.02, twill=False)
    gold, enamel = M["gold"], M["crimson_enamel"]
    bone = A.mat_flat("CarvedBone", (0.74, 0.68, 0.56), rough=0.5, noise=70, bump=0.14, vary=0.14, wear=0.3, dirt=1.0)
    stain = A.mat_flat("BoneStain", (0.16, 0.12, 0.09), rough=0.6, noise=70, bump=0.1, vary=0.1, wear=0.1)

    def shell(name, style, mat, thick):
        pts, eyes = mask_outline(style)
        ob = A.extrude_poly(name, ccw(pts), thick, mat, frame((0, 0, 0)), bevel=0.004, segments=2, holes=[ccw(e)[::-1] for e in eyes])
        bpy.context.view_layer.objects.active = ob
        for md in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
        # subdivide for a smooth wrap
        bm = bmesh.new(); bm.from_mesh(ob.data)
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > 0.05], cuts=2, use_grid_fill=True)
        bm.to_mesh(ob.data); bm.free()
        wrap_mask(ob, 0.612)
        return ob, pts, eyes

    def ties(name):
        return   # owner: nothing may clip; ties round the head would pass through the hair
        for sx in (-1, 1):
            a = sx * 0.58 / 0.635
            p = Vector((0.64 * math.sin(a), -0.64 * math.cos(a), 1.62))
            pts = [p, p + Vector((sx * 0.06, 0.18, -0.02)), p + Vector((sx * 0.04, 0.40, -0.03)), Vector((sx * 0.1, 0.64, 1.60))]
            A.tube(f"{name}_tie{sx}", [tuple(q) for q in pts], 0.012, ribbon, res=4)

    # ---- lace: a stiffened black lace mask (alpha) on a satin edge
    piece("LaceMask", "Head", kind="Alpha", alpha=f"{A.TEX_DIR}/NHAcc_Lace.png", uv=A.uv_front(-0.50, 0.50, 1.42, 1.76))
    shell("LaceShell", "lace", None, 0.006)
    piece("LaceMaskTrim", "Head")
    pts, eyes = mask_outline("lace")
    edge = [Vector((x, 0, z)) for x, z in pts]
    for k, loop in enumerate([pts] + eyes):
        P = []
        for x, z in loop:
            ang = x / 0.616
            P.append((0.621 * math.sin(ang), -0.621 * math.cos(ang), z))
        A.tube(f"LaceEdge{k}", P, 0.006, ribbon, closed=True, res=3)
    ties("LaceMaskTrim")

    # ---- bone: carved bone with stained grooves round the eyes and scrolls on the cheeks
    piece("BoneMask", "Head")
    ob, pts, eyes = shell("BoneShell", "bone", bone, 0.024)
    for v in ob.data.vertices:   # sculpt: a heavy brow over each eye, cheekbones, a ridge down the nose
        x, z = v.co.x, v.co.z
        ex = min(abs(x - 0.2), abs(x + 0.2))
        brow = 0.014 * math.exp(-((ex) / 0.13) ** 2) * math.exp(-((z - 1.675) / 0.03) ** 2)
        cheek = 0.010 * math.exp(-((abs(x) - 0.34) / 0.1) ** 2) * math.exp(-((z - 1.50) / 0.05) ** 2)
        r = math.hypot(x, v.co.y)
        if r > 0.6:
            k = (brow + cheek) / r
            v.co.x += v.co.x * k; v.co.y += v.co.y * k
    ob.data.update()
    for k, e in enumerate(eyes):
        P = []
        for x, z in e:
            dx = x - (-0.205 if k == 0 else 0.205)
            ang = (x + dx * 0.25) / 0.64
            P.append((0.642 * math.sin(ang), -0.642 * math.cos(ang), z + (z - 1.605) * 0.15))
        A.tube(f"BoneRim{k}", P, 0.008, stain, closed=True, res=3)
    for sx in (-1, 1):
        for k in range(3):
            P2 = []
            for i in range(17):
                t = i / 16
                P2.append((sx * (0.30 + 0.12 * t), 1.52 + 0.05 * k + 0.07 * math.sin(t * math.pi * 1.2 + k)))
            for r, run in enumerate(mask_runs(P2, "bone")):
                P = [(0.640 * math.sin(x / 0.64), -0.640 * math.cos(x / 0.64), z) for x, z in run]
                A.tube(f"BoneScroll{sx}_{k}_{r}", P, 0.006, stain, res=3)
    ties("BoneMask")

    # ---- gilt: gold with raised filigree, crimson jewels at the temples and a feather spray on the left
    piece("GiltMask", "Head")
    ob, pts, eyes = shell("GiltShell", "gilt", gold, 0.02)
    random.seed(3)
    for sx in (-1, 1):
        for k in range(4):
            P2 = []
            ph = random.uniform(0, 3)
            for i in range(23):
                t = i / 22
                P2.append((sx * (0.06 + 0.36 * t), 1.66 - 0.16 * t + 0.03 * math.sin(t * 6 + ph + k) + 0.02 * k))
            for r, run in enumerate(mask_runs(P2, "gilt", 0.018)):
                P = [(0.636 * math.sin(x / 0.64), -0.636 * math.cos(x / 0.64), z) for x, z in run]
                A.tube(f"GiltFil{sx}_{k}_{r}", P, 0.005, gold, res=3)
        a = sx * 0.40 / 0.64
        A.sphere(f"GiltJewel{sx}", 0.04, (0.640 * math.sin(a), -0.640 * math.cos(a), 1.66), enamel, scale=(1, 0.45, 1.3), seg=14, rings=8)
    ties("GiltMask")
    return dict(notes="three masquerade half-masks: black lace (alpha) with satin edging; carved bone with stained grooves; "
                      "gilt with filigree, crimson jewels and a feather spray. Each ties with satin ribbons")
