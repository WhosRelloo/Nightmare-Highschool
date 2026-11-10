"""Props batch 44 (the showpiece kit): modelled clothing for the owner's R6 rig, and the cast.

Every garment is real geometry wrapped round the R6 blocks (it keeps the blocky silhouette, just as an R6 avatar's 3D
layered clothing does): tailored jackets with lapels and a tie, long coats whose skirts are simulated cloth, capes and
cloaks (verlet cloth flaring in a wind, lined), trouser legs, boots with soles and toes, gloves and gauntlets, armour,
hoods, hair, hats and crowns. Rest frame (R6 units): feet on z = 0, facing -Y, torso x -1..1 / y -0.5..0.5 / z 2..4,
arms at x = +-1.5, legs at x = +-0.5, head centred near (0, 0, 4.6). Each piece is built at rest and skinned onto the
posed rig with Fig.build (showpiece44_rig).

The cast (each a function taking the kit K, a base, a yaw, a pose and options, returning the posed Fig) is shared by
the statues (nh_props_batch44.py, part stone or bronze) and the painting renders (showpiece44_scenes.py, full colour).
"""
import math
import random

from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform
from nh_props_batch12 import frustum
import nh_props_batch20 as B20
import window_shapes as WS
import showpiece44_rig as R
import showpiece44_geo as GE

S = 1.6


def tp(name, pts, y, depth, mat):
    return B20.tprism(name, WS.ccw(pts), y, depth, mat)


def mirror(pts):
    return [(-x, z) for x, z in pts]


# ================================================================== garments

def jacket(f, K, m, hem=1.7, lapel=None, shirt="linen", tie=None, buttons="gold", vest=None, collar=False, double=False, pocket=True,
           seed=1, sleeves=True, cuff=None, shoulder=True, epaulettes=None, flare=1.05, trim=None, crest=None):
    """A tailored blazer or tailcoat body: a wool shell from the hem to the shoulders, padded shoulders, peaked lapels
    (lapel material), a shirt front and tie in the V, buttons, a breast pocket, sleeves with cuffs."""
    lapel = lapel or m

    def body():
        GE.shell("JacketBody", hem, 4.04, 1.07, 0.575, K[m], r=0.13, n=32, nz=14, flare0=flare, flare1=1.0, seed=seed,
                 wrinkles=[(2.9, 0.4, 0.045, 4), (2.25, 0.3, 0.04, 5), (3.6, 0.25, 0.02, 3)], thick=0.04)
        if shoulder:
            frustum("JacketYoke", (0, 0), 2.18, 1.18, 3.98, 1.5, 0.95, 4.12, K[m], bevel=0.04)
        # the V: shirt, tie, lapels
        y = -0.6
        tp("ShirtV", [(-0.3, 4.06), (0.3, 4.06), (0.0, 2.95)], y + 0.015, 0.02, K[vest or shirt])
        if vest:
            tp("ShirtV2", [(-0.16, 4.06), (0.16, 4.06), (0.0, 3.55)], y + 0.0, 0.02, K[shirt])
        if tie:
            GE.ribbon("Tie", [(0, y - 0.02, 3.92), (0.0, y - 0.03, 3.5), (0.02, y - 0.035, 3.05)], lambda t: 0.13 + 0.07 * t, K[tie], up=(1, 0, 0),
                      thick=0.025, smooth=1)
            box("TieKnot", (0.15, 0.06, 0.13), (0, y - 0.03, 3.97), K[tie], bevel=0.03)
        L = [(-0.3, 4.06), (-0.62, 4.0), (-0.58, 3.78), (-0.82, 3.64), (-0.52, 3.2), (-0.06 if not double else 0.12, 2.78), (-0.02 if not double else 0.2, 2.9),
             (-0.26, 3.9)]
        for sx, pts in ((-1, L), (1, mirror(L))):
            tp(f"Lapel{sx}", pts, y - 0.02, 0.035, K[lapel])
        if collar:
            GE.shell("Collar", 3.98, 4.4, 0.74, 0.66, K[lapel], cy=0.08, r=0.3, nz=2, flare1=1.2, front_open=0.5, thick=0.04)
        bz = [2.65, 2.35, 2.05] if hem < 2.0 else [2.65, 2.4]
        for k, z in enumerate(bz):
            for sx in ((-0.22, 0.22) if double else (0.0,)):
                sphere(f"Btn{k}{sx}", 0.055, (sx, y - 0.03, z), K[buttons], seg=8, rings=4, scale=(1, 0.5, 1))
        if pocket:
            box("Pocket", (0.42, 0.03, 0.08), (0.55, y - 0.005, 3.62), K[m], bevel=0.015)
            tp("Kerchief", [(0.4, 3.66), (0.48, 3.78), (0.55, 3.7), (0.62, 3.8), (0.7, 3.66)], y - 0.01, 0.02, K.get("kerchief", K[shirt]))
        if trim:     # piping round the hem, up the front edges and round the lapels; seams down the sides and over the shoulders
            hr = [Vector((x * flare, y * flare, hem + 0.02)) for x, y in GE.rr_pts(1.085, 0.59, 0.13, 28)]
            GE.sweep("HemTrim", hr + [hr[0]], 0.028, K[trim], sides=5, smooth=0, cap=False)
            for sx, pts in ((-1, L), (1, mirror(L))):
                GE.sweep(f"LapelTrim{sx}", [(x, y - 0.045, z) for x, z in pts[:6]], 0.018, K[trim], sides=4, smooth=0)
        for sx in (-1, 1):
            GE.sweep(f"SideSeam{sx}", [(sx * 1.085, 0.0, hem + 0.05), (sx * 1.085, 0.0, 3.95)], 0.012, K[m], sides=4, smooth=0)
            GE.sweep(f"ShoulderSeam{sx}", [(sx * 0.55, -0.45, 4.1), (sx * 1.0, -0.4, 4.08), (sx * 1.0, 0.4, 4.08), (sx * 0.55, 0.45, 4.1)], 0.012, K[m],
                     sides=4, smooth=0)
        if crest:    # an embroidered house crest on the breast pocket: a shield, a gilt rim and a charge
            sh = [(-0.2, 3.62), (0.2, 3.62), (0.2, 3.38), (0.12, 3.24), (0.0, 3.18), (-0.12, 3.24), (-0.2, 3.38)]
            tp("Crest", [(x - 0.55, z) for x, z in sh], y - 0.03, 0.025, K[crest[0]])
            GE.sweep("CrestRim", [(x - 0.55, y - 0.05, z) for x, z in sh + [sh[0]]], 0.014, K[crest[1]], sides=4, smooth=0, cap=False)
            GE.sweep("CrestCharge", [(-0.55, y - 0.055, 3.27), (-0.55, y - 0.055, 3.55)], 0.022, K[crest[1]], sides=4, smooth=0)
            GE.sweep("CrestBar", [(-0.66, y - 0.055, 3.47), (-0.44, y - 0.055, 3.47)], 0.018, K[crest[1]], sides=4, smooth=0)
        if epaulettes:
            for sx in (-1, 1):
                box(f"Epaulette{sx}", (0.55, 0.62, 0.08), (sx * 1.25, 0, 4.08), K[epaulettes], bevel=0.03)
                for k in range(6):
                    tube(f"Fringe{sx}{k}", [(sx * (1.0 + k * 0.1), -0.25, 4.05), (sx * (1.05 + k * 0.1), -0.27, 3.82)], 0.02, K[epaulettes], poly=True)
    f.build("torso", body)
    if sleeves:
        sleeve_pair(f, K, m, cuff=cuff, seed=seed)


def sleeve_pair(f, K, m, cuff=None, bell=1.0, z0=2.05, seed=2, torn=None, cuff_h=0.2, sides=(-1, 1)):
    for side in sides:
        part = "rarm" if side > 0 else "larm"

        def fn(side=side):
            GE.shell(f"Sleeve{side}", z0, 4.06, 0.555, 0.555, K[m], cx=side * 1.5, r=0.14, n=20, nz=12, flare0=bell, seed=seed + side,
                     wrinkles=[(3.05, 0.35, 0.08, 3), (z0 + 0.3, 0.25, 0.05, 4), (3.65, 0.2, 0.025, 2)], thick=0.04)
            if cuff:
                GE.shell(f"Cuff{side}", z0 - 0.01, z0 + cuff_h, 0.585 * bell, 0.585 * bell, K[cuff], cx=side * 1.5, r=0.14, n=20, nz=1, thick=0.04)
                for k in range(2):
                    sphere(f"CuffBtn{side}{k}", 0.04, (side * 1.5 + side * 0.15 * (k - 0.5), 0.62 * bell, z0 + cuff_h * 0.5), K.get("cuffbtn", K["gold"]),
                           seg=6, rings=3, scale=(1, 0.5, 1))
        f.build(part, fn)


def trousers(f, K, m, seed=3, cuff=0.25, flare=1.02, waist=True, torn=0.0):
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"

        def fn(side=side):
            GE.shell(f"Trouser{side}", cuff, 2.08, 0.55, 0.55, K[m], cx=side * 0.5, r=0.12, n=20, nz=12, flare0=flare, seed=seed + side,
                     wrinkles=[(1.05, 0.32, 0.08, 3), (cuff + 0.25, 0.25, 0.06, 4), (1.75, 0.2, 0.03, 3)], thick=0.04)
        f.build(part, fn)
    if waist:
        f.build("torso", lambda: GE.shell("Waistband", 1.92, 2.3, 1.06, 0.565, K[m], r=0.12, nz=2, thick=0.035))


def boots(f, K, m, h=0.9, sole="rubber", toe=0.18, cuff=None, buckles=None, heel=0.1):
    for side in (-1, 1):
        part = "rleg" if side > 0 else "lleg"

        def fn(side=side):
            x = side * 0.5
            GE.shell(f"Boot{side}", 0.08, h, 0.575, 0.575, K[m], cx=x, r=0.14, n=20, nz=4, flare1=1.04, seed=7 + side,
                     wrinkles=[(0.55, 0.2, 0.03, 4)], thick=0.04, cap0=True)
            box(f"Toe{side}", (1.12, 0.5, 0.42), (x, -0.42 - toe * 0.5, 0.25), K[m], bevel=0.17)
            box(f"Sole{side}", (1.2, 1.25 + toe, 0.1), (x, -toe * 0.5, 0.05), K[sole], bevel=0.03)
            box(f"Heel{side}", (1.1, 0.4, heel + 0.06), (x, 0.38, 0.03 + heel / 2), K[sole], bevel=0.02)
            if cuff:
                GE.shell(f"BootCuff{side}", h - 0.05, h + 0.25, 0.62, 0.62, K[cuff], cx=x, r=0.16, nz=1, flare1=1.08, thick=0.04)
            if buckles:
                for k, z in enumerate((0.45, 0.72)):
                    box(f"Strap{side}{k}", (1.2, 1.2, 0.08), (x, 0, z), K["leather_black"], bevel=0.02)
                    box(f"Buckle{side}{k}", (0.16, 0.05, 0.14), (x + side * 0.3, -0.61, z), K[buckles], bevel=0.015)
        f.build(part, fn)


def belt(f, K, m="leather_black", buckle="gold", z=2.12, h=0.2, sash=None):
    def fn():
        GE.shell("Belt", z - h / 2, z + h / 2, 1.1, 0.6, K[m], r=0.14, nz=1, thick=0.04)
        box("Buckle", (0.32, 0.06, 0.26), (0, -0.635, z), K[buckle], bevel=0.03)
        box("BuckleIn", (0.2, 0.07, 0.14), (0, -0.64, z), K[m], bevel=0.02)
        if sash:
            GE.ribbon("Sash", [(-1.0, -0.62, 3.95), (-0.3, -0.64, 3.2), (0.4, -0.64, 2.55), (1.05, -0.6, 2.05)], 0.36, K[sash], up=(0.6, 0, 0.8),
                      thick=0.03)
    f.build("torso", fn)


def gauntlets(f, K, m, cuff=None, sides=(-1, 1), plates=True):
    for side in sides:
        part = "rarm" if side > 0 else "larm"

        def fn(side=side):
            x = side * 1.5
            GE.shell(f"Glove{side}", 1.94, 2.55, 0.575, 0.575, K[m], cx=x, r=0.15, nz=2, thick=0.03, cap0=True)
            GE.shell(f"Gauntlet{side}", 2.35, 2.9, 0.6, 0.6, K[cuff or m], cx=x, r=0.15, nz=2, flare1=1.15, thick=0.04)
            if plates:
                for k in range(3):
                    box(f"Knuckle{side}{k}", (0.3, 0.2, 0.1), (x - 0.3 + k * 0.3, -0.56, 2.05), K[cuff or m], bevel=0.03)
        f.build(part, fn)


def pauldrons(f, K, m, trim=None, layers=3, size=1.0, spikes=False):
    for side in (-1, 1):
        part = "rarm" if side > 0 else "larm"

        def fn(side=side):
            x = side * 1.5
            for k in range(layers):
                z = 4.1 - k * 0.3
                r = (0.78 - k * 0.04) * size
                sphere(f"Pauldron{side}{k}", r, (x + side * 0.05, 0, z - 0.2), K[m], seg=14, rings=7, scale=(1.0, 0.95, 0.55))
                if trim:
                    hoop(f"PauldronTrim{side}{k}", (x + side * 0.05, 0, z - 0.42 * 0.55 * r / 0.78 - 0.08), r * 0.93, "Z", K[trim], thick=0.03)
            if spikes:
                for k in range(3):
                    cone(f"Spike{side}{k}", 0.09, 0.0, 0.45, (x + side * 0.15, -0.25 + k * 0.25, 4.25), K[m], verts=6, rot=(0, side * 0.5, 0))
        f.build(part, fn)


def breastplate(f, K, m, trim=None, gem=None):
    def fn():
        GE.shell("Cuirass", 2.6, 4.02, 1.1, 0.62, K[m], r=0.3, nz=4, flare0=0.97, thick=0.05)
        tube("Ridge", [(0, -0.66, 3.95), (0, -0.7, 3.2), (0, -0.66, 2.62)], 0.04, K[m], poly=True)
        if trim:
            for z in (2.6, 4.0):
                GE.shell(f"CuirassTrim{z}", z - 0.04, z + 0.04, 1.13, 0.645, K[trim], r=0.3, nz=1, thick=0.03)
        if gem:
            sphere("Gorget", 0.16, (0, -0.72, 3.75), K[gem], seg=8, rings=4, scale=(1, 0.5, 1.2))
        for k in range(3):
            GE.shell(f"Fauld{k}", 2.25 - k * 0.22, 2.55 - k * 0.22, 1.12 + k * 0.03, 0.63 + k * 0.02, K[m], r=0.3, nz=1, thick=0.04, front_open=0.0)
    f.build("torso", fn)


def cape(f, K, m, lining=None, length=6.5, wind=(0, 1.2, 0.3), gather=1.25, colliders=None, floor=None, ragged=0.0, seed=0, collar=None,
         clasp="gold", gem=None, width=1.0, rows=24, cols=28, turb=0.4, curl=0.0, iters=240, front=0.35, thick=0.05):
    """A cape or cloak pinned along the shoulders and across the back, simulated as cloth (flaring in `wind`, world
    studs), lined with `lining` (the solidified inner face), a stand-up collar and a jewelled clasp."""
    w = 1.95 * width
    top_rest = [(-w, -front, 4.08), (-w, 0.2, 4.1), (-w * 0.8, 0.6, 4.12), (-0.4, 0.66, 4.15), (0.4, 0.66, 4.15), (w * 0.8, 0.6, 4.12), (w, 0.2, 4.1),
                (w, -front, 4.08)]
    top = [f.at("torso", p) for p in top_rest]
    cols_ = colliders if colliders is not None else f.colliders(pad=0.04)
    ob = GE.drape("Cape", top, length, K[m], rows=rows, cols=cols, gather=gather, wind=wind, colliders=cols_, floor=floor, seed=seed,
                  ragged=ragged, outward=None, turb=turb, wind_curl=curl, iters=iters, thick=thick,
                  fold_amp=0.18, fold_period=4.0)
    if lining:
        ob.data.materials.append(K[lining])
        ob.modifiers["Solid"].material_offset = 1
    if collar:
        def col():
            pts = []
            for i in range(9):
                a = math.radians(-70 + i * 140 / 8)
                pts.append((math.sin(a) * 0.95, math.cos(a) * 0.55 + 0.08))
            rows_ = []
            for j in range(4):
                t = j / 3
                k = 1.1 + 0.45 * t
                rows_.append([Vector((x * k, y * k + 0.25 + 0.3 * t, 4.08 + t * 1.1)) for x, y in pts])
            GE.grid_mesh("CapeCollar", rows_, K[collar], 0.05)
        f.build("torso", col)
    if clasp:
        def cl():
            for sx in (-1, 1):
                sphere(f"Clasp{sx}", 0.17, (sx * 0.75, -0.62, 3.95), K[clasp], seg=10, rings=6, scale=(1, 0.5, 1))
                if gem:
                    sphere(f"ClaspGem{sx}", 0.1, (sx * 0.75, -0.7, 3.95), K[gem], seg=6, rings=3, scale=(1, 0.6, 1))
            GE.sweep("ClaspChain", [(-0.75, -0.66, 3.92), (0, -0.7, 3.7), (0.75, -0.66, 3.92)], 0.025, K[clasp], sides=5)
        f.build("torso", cl)
    return ob


def coat_skirt(f, K, m, length=2.0, z=2.2, gather=1.2, wind=(0, 0.3, 0.0), colliders=None, floor=None, gap=0.3, seed=1, lining=None,
               ragged=0.0, rows=16, cols=30, turb=0.3, curl=0.0):
    """A long coat's skirt from the waist: simulated cloth hanging round the legs, open at the front by `gap` (rest
    half width), so a stride splits it."""
    ring = GE.rr_pts(1.1, 0.6, 0.18, 48)
    pts = []
    start = None
    for i, (x, y) in enumerate(ring):
        pass
    # order from the front-left edge round the back to the front-right edge
    left = [(x, y) for x, y in ring]
    ang = [(math.atan2(y, x) + 2 * math.pi) % (2 * math.pi) for x, y in left]
    order = sorted(range(len(left)), key=lambda i: (ang[i] - (1.5 * math.pi + 0.001)) % (2 * math.pi))
    seq = [left[i] for i in order]
    seq = [p for p in seq if not (p[1] < 0 and abs(p[0]) < gap)]
    # seq now runs from just right of the front gap anticlockwise round to just left of it
    top = [f.at("torso", (x, y, z)) for x, y in seq]
    cols_ = colliders if colliders is not None else f.colliders(pad=0.05, skip=("head",))
    ob = GE.drape("Skirt", top, length, K[m], rows=rows, cols=cols, gather=gather, wind=wind, colliders=cols_, floor=floor, seed=seed,
                  ragged=ragged, fold_amp=0.1, fold_period=3.5, turb=turb, wind_curl=curl, iters=200, thick=0.045)
    if lining:
        ob.data.materials.append(K[lining])
        ob.modifiers["Solid"].material_offset = 1
    return ob


def hood(f, K, m, up=True, deep=0.25, drape=True):
    """A deep sculpted hood: one smooth mass round the head rising to a soft peak at the back, its face opening cut
    out, the cowl folding onto the shoulders in heavy rolls."""
    import showpiece44_organic as O

    def fn():
        import bmesh
        E = [((0, 0.08, 4.65), 0.78, (1.0, 1.05, 1.08), None, 2.0), ((0, 0.45, 5.15), 0.42, (0.9, 1.0, 1.1), None, 2.0),
             ((0, 0.75, 5.45), 0.2, None, None, 2.0)]
        ob = O.blob("Hood", E, K[m], res=0.07, decimate=0.3, displace=(0.025, 0.12))
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        kill = [v for v in bm.verts if v.co.y < -0.3 + deep * 0.5 and abs(v.co.x) < 0.58 and 4.05 < v.co.z < 5.15]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(ob.data)
        bm.free()
        GE._solid(ob, 0.04)
    if up:
        headwear(f, fn, ease=True)
    else:
        f.build("torso", fn)


def hair(f, K, m, style="slick", seed=0, length=1.0, flow=(0, 1, 0.15)):
    """Sculpted hair, one smooth clumped mass (metaballs): a cap over the crown and back plus big tapering locks with
    pointed tips, in the stylised way of anime and R6 hair accessories. flow is the direction the hair streams in.
    Styles: slick (combed back, a widow's peak), swept (wind-swept back with lifted points), spiky (anime spikes),
    pompadour, long (to the shoulder blades), bob, bun, mane (shaggy, wolfish), crop."""
    import showpiece44_organic as O
    rnd = random.Random(seed)
    fl = Vector(flow).normalized()
    cap = ((0, 0.15, 4.9), 0.64, (1.0, 1.0, 0.7))
    locks = []

    def lock(root, direction, L, r0, lift=0.0, curl=0.0, r1=0.015):
        root = Vector(root)
        d = Vector(direction).normalized()
        side = d.cross(Vector((0, 0, 1)))
        pts = [root]
        for i in range(1, 4):
            t = i / 3
            p = root + d * L * t + Vector((0, 0, lift * t * t)) + side * curl * math.sin(t * math.pi)
            # below the jaw the hair must fall over the clothes, never through them: behind the back, outside the shoulders
            rr = r0 + (r1 - r0) * t
            if p.z < 4.25:
                if abs(p.x) < 1.2:
                    p.y = max(p.y, 0.68 + rr + 0.06)
            pts.append(p)
        locks.append(([tuple(p) for p in pts], r0, r1))

    if style in ("slick", "swept", "spiky", "pompadour"):
        n = 9
        for k in range(n):
            x = -0.5 + k / (n - 1)
            root = (x * 1.0, -0.42, 5.12 - abs(x) * 0.18)
            if style == "slick":
                lock(root, (x * 0.25, 1.0, -0.15), 1.05, 0.2, lift=-0.25)
            elif style == "swept":
                lock(root, (x * 0.4 + fl.x, fl.y + 0.2, fl.z + 0.25), 1.2 + 0.25 * rnd.random(), 0.22, lift=0.25 + 0.2 * rnd.random(),
                     curl=rnd.uniform(-0.15, 0.15))
            elif style == "spiky":
                lock(root, (x * 0.9, 0.6, 0.7 + rnd.uniform(-0.1, 0.3)), 0.75 + 0.3 * rnd.random(), 0.24, lift=0.2)
            else:
                lock(root, (x * 0.2, 1.0, -0.1), 1.0, 0.18, lift=-0.2)
        if style == "spiky":
            for k in range(6):
                a = -1.2 + k * 0.48
                lock((math.sin(a) * 0.4, 0.2 + math.cos(a) * 0.3, 5.3), (math.sin(a) * 0.8, 0.7, 0.6), 0.75, 0.24, lift=0.15)
        if style == "slick":
            lock((0, -0.5, 5.05), (0, 0.4, 0.6), 0.25, 0.14)
    if style == "pompadour":
        locks.append(([(-0.42, -0.42, 5.18), (-0.12, -0.66, 5.36), (0.18, -0.68, 5.36), (0.42, -0.44, 5.2)], 0.17, 0.15))
        lock((0.12, -0.7, 5.3), (0.25, -0.5, -0.9), 0.3, 0.08, curl=0.1)
    if style in ("swept", "spiky", "bob", "crop"):        # fringe falling over the brow
        for k in range(4 if style != "crop" else 3):
            x = -0.36 + k * 0.24
            lock((x, -0.4, 5.15), (x * 0.4 + rnd.uniform(-0.2, 0.2), -0.5, -0.9), 0.42 + rnd.uniform(-0.05, 0.1), 0.15, curl=rnd.uniform(-0.1, 0.1))
    if style in ("swept", "spiky", "bob", "long", "mane"):  # side locks over the ears
        for sx in (-1, 1):
            lock((sx * 0.6, -0.15, 5.0), (sx * 0.3, 0.1, -1.0), 0.65 if style != "bob" else 0.75, 0.16)
            lock((sx * 0.62, 0.2, 5.0), (sx * 0.35, 0.4, -1.0), 0.7, 0.17)
    if style in ("long", "bob", "mane"):
        L = {"long": 2.0, "bob": 0.8, "mane": 1.3}[style] * length
        for k in range(9):
            a = -1.5 + k * 0.375
            root = (math.sin(a) * 0.6, 0.15 + math.cos(a) * 0.45, 5.05)
            d = (math.sin(a) * 0.3 + fl.x * 0.4, 0.35 + fl.y * 0.6, -1.0 + fl.z * 0.5)
            lock(root, d, L * rnd.uniform(0.85, 1.1), 0.27 if style != "mane" else 0.26, curl=rnd.uniform(-0.12, 0.12), lift=0.1, r1=0.06)
        for k in range(5):
            lock((-0.5 + k * 0.25, -0.3, 5.2), (0, 1.0, -0.2), 0.9, 0.18, lift=-0.1)
        for zz in (4.5, 4.9 - L * 0.5, 4.9 - L * 0.8):      # fuse the back locks into one falling sheet
            if zz < 4.95 - L:
                continue
            locks.append(([(-0.55, 0.62 + 0.25 * fl.y * (4.9 - zz), zz), (0.0, 0.72 + 0.25 * fl.y * (4.9 - zz), zz), (0.55, 0.62 + 0.25 * fl.y * (4.9 - zz), zz)],
                          0.2, 0.2))
    if style == "mane":
        for k in range(7):
            a = rnd.uniform(-2.4, 2.4)
            lock((math.sin(a) * 0.5, math.cos(a) * 0.5, 5.15), (math.sin(a), math.cos(a) * 0.6 + 0.4, 0.4), 0.55, 0.2, lift=0.1)
    if style == "bun":
        lock((0, -0.45, 5.1), (0, 1.0, -0.1), 1.0, 0.22, lift=-0.2)
        for sx in (-1, 1):
            lock((sx * 0.35, -0.42, 5.08), (sx * 0.2, 1.0, -0.15), 0.95, 0.2, lift=-0.2)
        locks.append(([(0, 0.62, 5.05), (0, 0.8, 5.1)], 0.32, 0.28))
    if style == "crop":
        for k in range(8):
            a = -2.6 + k * 0.75
            lock((math.sin(a) * 0.45, math.cos(a) * 0.45 + 0.1, 5.2), (math.sin(a), math.cos(a), 0.3), 0.3, 0.16)
    f.build("head", lambda: O.hair_mass("Hair", K[m], locks, cap=cap, res=0.05, decimate=0.26))
    f.hair = P.PARTS[-1]
    import showpiece44_fit as FT
    # long hair falls over the clothes: anything that would sink into the torso or the arms is cut away there
    FT.trim_inside(f.hair, FT.inside_obbs(f.colliders(pad=0.12, skip=("head", "rleg", "lleg"))))
    return f.hair


def headwear(f, fn, ease=False, mode=None):
    """Build a hat, crown or hood on the head, then seat it so it sits on the hair and head with nothing poking
    through: hats and crowns are lifted along the head's up axis, hoods are eased out about the head's centre."""
    import showpiece44_fit as FT
    s = len(P.PARTS)
    f.build("head", fn)
    obs = [o for o in P.PARTS[s:] if o.type == "MESH"]
    against = [o for o in (f.hair, f.body.get("head")) if o is not None]
    if not against:
        return obs
    if ease:
        FT.ease(obs, against, f.at("head", (0, 0, 4.6)))
    else:
        up = (f.world("neck").to_3x3().normalized() @ Vector((0, 0, 1))).normalized()
        mv = FT.seat(obs, against, up * f.G.to_scale()[0])
        print('[seat]', [o.name for o in obs][:3], 'moved', mv, 'left', FT.any_overlap(obs, against), flush=True)
    return obs


def claws(f, K, m, sides=(-1, 1), n=4, L=0.45):
    """Curved talons from the end of each arm (a vampire's or a turning wolf's hands)."""
    for side in sides:
        part = "rarm" if side > 0 else "larm"

        def fn(side=side):
            x = side * 1.5
            for k in range(n):
                u = -0.33 + 0.66 * k / (n - 1)
                p0 = (x + u, -0.35, 2.02)
                GE.sweep(f"Claw{side}{k}", [p0, (x + u * 1.1, -0.5, 2.02 - L * 0.45), (x + u * 1.12, -0.42, 2.02 - L * 0.8), (x + u * 1.1, -0.2, 2.02 - L * 0.9)],
                         lambda t: 0.06 * (1 - t) + 0.004, K[m], sides=6, smooth=1)
        f.build(part, fn)


def hand_at(f, side, k=0.05):
    """The posed world point at the end of an arm (where the hand would be) and the forearm's downward axis."""
    part = "rarm" if side > 0 else "larm"
    x = side * 1.5
    a = f.at(part, (x, 0, 2.0 - k))
    b = f.at(part, (x, 0, 2.9))
    return a, (a - b).normalized()


def grip(f, side, s, along=(0, 0, -1), roll=0.0, push=0.12):
    """Put the parts built since mark s (an item built along +Z with its grip at the origin) in a hand: the item's +Z is
    turned to `along` in the forearm's frame (default: straight out of the fist, along the forearm)."""
    p, d = hand_at(f, side)
    part = "rarm" if side > 0 else "larm"
    j = "relbow" if side > 0 else "lelbow"
    Mj = f.world(j).to_3x3().normalized()
    axis = Mj @ Vector((0, 0, -1))
    v = Mj @ Vector(along)
    R_ = Vector((0, 0, 1)).rotation_difference(v.normalized()).to_matrix().to_4x4()
    _xform(s, Matrix.Translation(p - axis * push * f.G.to_scale()[0]) @ R_ @ Matrix.Rotation(roll, 4, "Z") @ Matrix.Scale(f.G.to_scale()[0], 4))


def hold(f, side, build, along=(0, 0, -1), roll=0.0, push=0.12):
    s = _mark()
    build()
    grip(f, side, s, along, roll, push)


COLLARS = ("Collar", "ClericalCollar", "CollarUp", "CapeCollar", "Ruff", "Choker", "FurCollar", "Scarf", "Cowl", "Ermine", "Neck", "Lace")
CLOSED = ("FurCollar", "Ermine", "ScarfWrap", "Scarf", "Hair", "Beard", "Mane")
CLOTHES = ("JacketBody", "JacketYoke", "Robe", "Cassock", "Surplice", "Smock", "Tee", "Varsity", "Corset", "Jersey", "Jacket", "Bodice")
HOODS = ("Hood",)


def _base(o):
    return o.name.split(".")[0].rstrip("0123456789-")


def finish(f, end=None):
    """The last pass on a dressed figure so its layers sit cleanly: collars are cut back where the head or hair would
    pass through them (a fur collar or ermine instead hides the hair under it), and a hood is cut off where it would
    sink into the shoulders."""
    import showpiece44_fit as FT
    end = len(P.PARTS) if end is None else end
    own = [o for o in P.PARTS[f.start:end] if o.type == "MESH"]
    head = f.body.get("head")
    cloth = [o for o in own if _base(o) in CLOTHES]
    for o in own:
        b = next((c for c in COLLARS + ("ScarfWrap",) if o.name.startswith(c)), _base(o))
        if b in CLOSED and b not in ("Hair", "Beard", "Mane"):
            for c in cloth:       # the coat under a fur collar or a wound scarf is hidden inside it, never through it
                FT.trim_inside(c, FT.inside_mesh([o]))
        if b in COLLARS or b == "ScarfWrap":
            if b in CLOSED and f.hair is not None:
                FT.trim_inside(f.hair, FT.inside_mesh([o]))
            tests = [m for m in (head, f.hair) if m is not None]
            if tests and b not in CLOSED:
                FT.trim_inside(o, FT.inside_mesh(tests))
            elif head is not None:
                FT.trim_inside(o, FT.inside_mesh([head]))
        if b in HOODS:
            FT.trim_inside(o, FT.inside_obbs(f.colliders(pad=0.06, skip=("head", "rleg", "lleg", "rarm", "larm"))))
