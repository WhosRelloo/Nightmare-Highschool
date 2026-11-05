"""Props batch 29 (2026-11-05): the soft furnishings and tapestry kit for nh_props.py. Velvet, damask and gilt in the
Institution's look; every rug, mat, carpet and tapestry is an original woven design (weave_textiles.py, weave_motifs.py,
tapestry_weave.py), its maps mapped straight onto the cloth so they stay sharp.

Seats (baked; upholstery from the woven fabric sets in source_fabric/: velvet, damask, bat damask, regency stripe, a
small tapestry weave):
  VelvetChesterfield  a three-seat chesterfield in crimson velvet: deep diamond tufting on the back and the rolled arms,
                      three piped cushions, brass nailheads, ebonised bun feet
  CamelbackSofa       black velvet on a humped back with a carved ebony rail and a gilt bead, crimson piping, bolsters,
                      cabriole legs on gilt claw-and-ball feet
  ChaiseLongue        a fainting couch in crimson damask: a high scrolled head, a back rail sloping away, a bolster,
                      turned ebony legs on brass castors
  GothicSettle        a high-backed settle: three pointed arches with tufted crimson pads, pinnacles with gilt finials,
                      a quatrefoil apron, a tapestry-woven seat cushion
  ShellLoveseat       a two-seater in bone velvet: a scalloped shell back channel-tufted in fluted ribs, a gilt rim,
                      tapered gilt legs
  CornerSectional     the common room's L-shaped corner sofa in ink-blue velvet: piped seat and back cushions, bat-damask
                      throw pillows, a black plinth
  CoffinCouch         a couch with a coffin for a back: black lacquer, a tufted crimson coffin-shaped pad, brass coffin
                      handles, a crimson seat
  BatwingSofa         a back of spread bat wings, padded in black bat damask, the wing bones in gilt, a bat's head and ears
                      on top, a crimson seat
  ThroneSettee        the Headmaster's settee: a tall pointed back in tufted crimson velvet, a crocketed gilt frame with
                      pinnacles and the crest, ravens perched on the arms
  TuftedBench         a long window bench, its top deep-tufted in plum velvet, turned ebony legs with gilt collars, tassels
  RoundOttoman        a drum ottoman in ink-blue velvet: a radially tufted top with a tasselled button, a gilt bullion fringe

Rugs, mats, carpets (no bake: the woven maps alone):
  MothMedallionRug 12 x 8, WatchingRunner 4 x 18, ThornRoseRug (round, 9), StarChartRug (octagon, 8), RavenHearthRug
  (half-round, 7 x 3.5), BatDamaskRugWorn 9 x 6, Doormat and DoormatCrest (coir, 4 x 2.4), BathMat 3.2 x 2,
  CarpetDamask / CarpetWeb / CarpetHarlequin / CarpetMoth (8 x 8 tiles that butt edge to edge, seamless)

Tapestries (Main: the gilt rod, finials, brackets and rings, baked; Weave: the cloth and its gold fringe):
  TapestryHeadmaster, TapestryPriestDemon, TapestryAngelDemon, TapestryJudgement, TapestryCrest (7.5 x 10),
  TapestryWolfHunt (13 x 7.3)

Front faces -Y, Z is up, the origin is at the bottom centre; tapestries hang with their backs at y = 0 (the wall).
Registered into nh_props.BUILD on import.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, material
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch9 import foil, raven
from nh_props_batch10 import gilt
import nh_props_batch20 as B20
import window_shapes as WS

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "source_fabric")
SW = 32            # the swatch band at the foot of every woven map (weave_textiles.SW)


# ------------------------------------------------------------------ materials

def fabric(name, set_name, tint=(1, 1, 1), scale=0.4, normal=0.7, wear=0.08):
    return material(name, os.path.join(FAB, set_name), tint=tint, scale=scale, metal=0.0, normal=normal, wear=wear, dirt=0.7)


def kit(M):
    return {
        "crimson": fabric("VelvetCrimson", "NH_Velvet", (0.13, 0.007, 0.014), 0.3),
        "crimsondk": fabric("VelvetCrimsonDark", "NH_Velvet", (0.055, 0.003, 0.007), 0.3),
        "black": fabric("VelvetBlack", "NH_Velvet", (0.011, 0.01, 0.013), 0.3),
        "ink": fabric("VelvetInk", "NH_Velvet", (0.011, 0.014, 0.042), 0.3),
        "bone": fabric("VelvetBone", "NH_Velvet", (0.52, 0.43, 0.3), 0.3),
        "plum": fabric("VelvetPlum", "NH_Velvet", (0.045, 0.008, 0.026), 0.3),
        "damask": fabric("DamaskCrimson", "NH_Damask", (0.15, 0.01, 0.018), 1.7),
        "batdamask": fabric("DamaskBat", "NH_DamaskBat", (0.022, 0.02, 0.026), 0.6),
        "batdamaskcr": fabric("DamaskBatCrimson", "NH_DamaskBat", (0.13, 0.008, 0.016), 0.9),
        "stripe": fabric("RegencyStripe", "NH_Stripe", (1, 1, 1), 0.7),
        "weave": fabric("TapestryWeave", "NH_TapestryWeave", (1, 1, 1), 0.6),
        "ebony": material("Ebony", "NH_DeskWood", tint=(0.075, 0.055, 0.05), scale=0.22, rough_add=0.02, wear=0.45),
        "lacquer": material("BlackLacquer", base=(0.018, 0.016, 0.02), rough=0.22, metal=0.0, wear=0.12, dirt=0.5),
        "gilt": gilt(), "brass": M["brass"], "iron": M["iron"],
        "button": flat("ButtonDark", (0.05, 0.01, 0.015), 0.6),
        "cord": material("GiltCord", "NH_Brass", tint=(0.9, 0.7, 0.36), scale=1.6, rough_add=0.25, wear=0.2, dirt=0.9),
    }


# ------------------------------------------------------------------ upholstery shapes

def cushion(name, size, loc, mat, e=(0.45, 0.22), cuts=6, rot=(0, 0, 0), piping=None, pipe_r=0.028, puff=0.0):
    """A pillowy cushion: a superellipsoid (e[0] how round its sides, e[1] how round its corners in plan), with a piped
    seam round its middle. size is the full size; puff domes the top and bottom a little more."""
    a, b, c = size[0] / 2, size[1] / 2, size[2] / 2
    e1, e2 = e
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)

    def surf(d):
        f = (abs(d.x) ** (2 / e2) + abs(d.y) ** (2 / e2)) ** (e2 / e1) + abs(d.z) ** (2 / e1)
        return d * f ** (-e1 / 2)
    for v in bm.verts:
        d = v.co.normalized()
        p = surf(d)
        dome = 1 + puff * (1 - min(1.0, (p.x ** 2 + p.y ** 2) ** 0.5))
        v.co = Vector((p.x * a, p.y * b, p.z * c * dome))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    R = Matrix.Translation(loc) @ __import__("mathutils").Euler(rot, "XYZ").to_matrix().to_4x4()
    ob.data.transform(R)
    _finish(ob, mat, 0)
    if piping is not None:
        ring = []
        for i in range(40):
            t = i / 40 * 2 * math.pi
            d = Vector((math.cos(t), math.sin(t), 0.0))
            p = surf(d)
            ring.append(tuple(R @ Vector((p.x * a * 1.005, p.y * b * 1.005, 0.0))))
        tube(f"{name}Piping", ring, pipe_r, piping, closed=True, poly=True)
    return ob


def tufted(name, w, h, mat, button, nx=6, nz=3, depth=0.3, puff=0.2, res=0.09, roll=0.22, crease=0.5, outline=None, xf=None):
    """A diamond-tufted panel facing -Y: its back flat at y = 0, its front puffed out between buttons sunk into it, the
    pleats between the buttons pulled in, the edges rolling back. w across (x), h up (z, from 0). outline: an optional
    closed (x, z) polygon the panel is cut to (buttons only inside it). xf: a Matrix placing it."""
    s0 = _mark()
    nxv, nzv = max(4, int(w / res)), max(4, int(h / res))
    btn = []
    for j in range(nz + 1):
        for i in range(nx + 1):
            if (i + j) % 2:
                continue
            mx, mz = w * 0.5 / nx, h * 0.5 / nz
            bx = -w / 2 + mx + (w - 2 * mx) * i / nx
            bz = mz + (h - 2 * mz) * j / nz
            if outline and not WS.inside((bx, bz), outline):
                continue
            btn.append((bx, bz))
    sig = 0.35 * min(w / nx, h / nz)
    pairs = []
    for p in btn:
        for q in btn:
            if q <= p:
                continue
            dx, dz = abs(q[0] - p[0]), abs(q[1] - p[1])
            if 0 < dx < w / nx * 1.6 and 0 < dz < h / nz * 1.6:
                pairs.append((p, q))

    def front(x, z):
        ex = min(x + w / 2, w / 2 - x) / roll
        ez = min(z, h - z) / roll
        edge = min(1.0, max(0.0, min(ex, ez))) ** 0.5
        dip = 0.0
        for bx, bz in btn:
            r2 = (x - bx) ** 2 + (z - bz) ** 2
            if r2 < (sig * 3) ** 2:
                dip = max(dip, math.exp(-r2 / (sig * sig)))
        for (ax, az), (bx, bz) in pairs:
            vx, vz = bx - ax, bz - az
            L2 = vx * vx + vz * vz
            t = max(0.0, min(1.0, ((x - ax) * vx + (z - az) * vz) / L2))
            px, pz = ax + vx * t, az + vz * t
            d2 = (x - px) ** 2 + (z - pz) ** 2
            if d2 < (sig * 1.2) ** 2:
                dip = max(dip, crease * math.exp(-d2 / (sig * sig * 0.12)))
        return -(depth * 0.3 + puff * edge) * (1 - 0.75 * dip) - depth * 0.7 * edge ** 0.3
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    grid = []
    for j in range(nzv + 1):
        row = []
        for i in range(nxv + 1):
            x = -w / 2 + w * i / nxv
            z = h * j / nzv
            row.append(bm.verts.new((x, front(x, z), z)))
        grid.append(row)
    for j in range(nzv):
        for i in range(nxv):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.smooth = True
    # close it: the rim back to the flat back plane, the back as one face
    rim = [grid[0][i] for i in range(nxv + 1)] + [grid[j][nxv] for j in range(1, nzv + 1)] + \
          [grid[nzv][i] for i in range(nxv - 1, -1, -1)] + [grid[j][0] for j in range(nzv - 1, 0, -1)]
    back = [bm.verts.new((v.co.x, 0.0, v.co.z)) for v in rim]
    n = len(rim)
    for k in range(n):
        bm.faces.new((rim[k], back[k], back[(k + 1) % n], rim[(k + 1) % n]))
    bm.faces.new(list(reversed(back)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    ob.modifiers.new("Tri", "TRIANGULATE")
    cut = None
    if outline:
        B20.tprism(f"{name}Cut", WS.ccw(outline), -depth * 0.5, depth * 3, mat)
        cut = P.PARTS.pop()
        cut.hide_render = True
        md = ob.modifiers.new("Clip", "BOOLEAN")
        md.operation = "INTERSECT"
        md.solver = "EXACT"
        md.object = cut
    for k, (bx, bz) in enumerate(btn):
        sphere(f"{name}Button{k}", 0.05, (bx, front(bx, bz) - 0.015, bz), button, seg=8, rings=4, scale=(1, 0.6, 1))
    if xf is not None:
        _xform(s0, xf)
        if cut is not None:
            cut.matrix_world = xf @ cut.matrix_world
    return ob


def channels(name, w, h, mat, n=9, depth=0.28, shell=True, xf=None):
    """Channel tufting: padded flutes fanning from a point below the seat (a shell back when shell), each a long rounded
    rib, their tops scalloped."""
    s = _mark()
    for k in range(n):
        t = (k + 0.5) / n
        a = math.radians(-62 + 124 * t) if shell else 0.0
        top_h = h * (0.82 + 0.18 * math.cos((t - 0.5) * math.pi)) if shell else h
        x0 = (t - 0.5) * w * 0.25 if shell else (t - 0.5) * w
        x1 = x0 + math.sin(a) * top_h * 0.95 if shell else x0
        z1 = 0.15 + math.cos(a) * top_h if shell else h
        width = w / n * (1.6 if shell else 1.0)
        pts = [(x0 + (x1 - x0) * u, -depth * 0.5, 0.15 + (z1 - 0.15) * u) for u in (0.0, 0.5, 1.0)]
        L = math.dist(pts[0], pts[-1])
        cushion(f"{name}Flute{k}", (width * 0.62 if shell else width * 0.95, depth, L), ((pts[0][0] + pts[-1][0]) / 2, -depth * 0.5, (pts[0][2] + pts[-1][2]) / 2),
                mat, e=(0.6, 0.6), cuts=6, rot=(0, -a if shell else 0, 0))
    if xf is not None:
        _xform(s, xf)


def bun(name, x, y, mat, r=0.16, h=0.32):
    lathe(name, [(0, 0), (r * 0.7, 0), (r, h * 0.3), (r * 0.95, h * 0.7), (r * 0.6, h), (0, h)], mat, seg=16, loc=(x, y, 0))


def turned_leg(name, x, y, h, mat, collar=None, r=0.12):
    lathe(name, [(0, 0), (r * 0.55, 0), (r * 0.6, h * 0.08), (r * 0.45, h * 0.2), (r * 0.9, h * 0.42), (r * 0.5, h * 0.62), (r * 0.65, h * 0.8),
                 (r, h * 0.88), (r, h), (0, h)], mat, seg=16, loc=(x, y, 0))
    if collar:
        hoop(f"{name}Collar", (x, y, h * 0.8), r * 0.67, "Z", collar, thick=0.022)


def cabriole(name, x, y, h, wood, foot, sx=1, sy=-1):
    """A cabriole leg: a knee swelling out, an ankle curving in, a gilt claw gripping a ball."""
    pts = [(x, y, h), (x + sx * 0.12, y + sy * 0.12, h * 0.78), (x + sx * 0.08, y + sy * 0.08, h * 0.5), (x - sx * 0.02, y - sy * 0.02, h * 0.22),
           (x + sx * 0.03, y + sy * 0.03, 0.16)]
    tube(name, pts, 0.085, wood)
    sphere(f"{name}Ball", 0.11, (x + sx * 0.03, y + sy * 0.03, 0.11), foot, seg=12, rings=6)
    for k in range(3):
        a = math.atan2(sy, sx) + (k - 1) * 0.8
        tube(f"{name}Claw{k}", [(x + sx * 0.03, y + sy * 0.03, 0.2), (x + sx * 0.03 + math.cos(a) * 0.1, y + sy * 0.03 + math.sin(a) * 0.1, 0.13),
                                (x + sx * 0.03 + math.cos(a) * 0.12, y + sy * 0.03 + math.sin(a) * 0.12, 0.03)], 0.025, foot)


def nails(prefix, pts, mat):
    for k, p in enumerate(pts):
        sphere(f"{prefix}{k}", 0.028, p, mat, seg=6, rings=3)


def tassel(name, x, y, z, mat, cord, s=1.0):
    tube(f"{name}Cord", [(x, y, z), (x, y, z - 0.18 * s)], 0.015 * s, cord, poly=True)
    sphere(f"{name}Head", 0.06 * s, (x, y, z - 0.22 * s), mat, seg=10, rings=5)
    lathe(f"{name}Skirt", [(0, z - 0.26 * s), (0.05 * s, z - 0.26 * s), (0.08 * s, z - 0.4 * s), (0.09 * s, z - 0.5 * s), (0, z - 0.5 * s)], mat, seg=12, loc=(x, y, 0))


# ================================================================== the seats

def velvet_chesterfield(M):
    K = kit(M)
    W, D, SH, H = 6.3, 2.8, 1.45, 2.85
    rnd = random.Random(2901)
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            if sx == 0 and sy > 0:
                continue
            bun(f"Bun{sx}{sy}", sx * (W / 2 - 0.35), sy * (D / 2 - 0.3), K["ebony"])
    box("Base", (W - 0.1, D - 0.1, 0.95), (0, 0, 0.32 + 0.475), K["crimson"], bevel=0.12, segments=3)
    tube("BasePiping", [(-W / 2 + 0.06, -D / 2 + 0.06, 1.25), (W / 2 - 0.06, -D / 2 + 0.06, 1.25)], 0.03, K["crimsondk"], poly=True)
    # the back: tufted inside, rolled over at the top
    tufted("Back", W - 1.1, H - SH + 0.2, K["crimson"], K["button"], nx=9, nz=3, depth=0.5, puff=0.22,
           xf=Matrix.Translation((0, D / 2 - 0.05, SH - 0.2)))
    cyl("BackRoll", 0.26, W - 0.7, (0, D / 2 - 0.3, H - 0.02), K["crimson"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.0)
    box("BackOuter", (W - 0.3, 0.25, H - 0.35), (0, D / 2 - 0.15, 0.35 + (H - 0.35) / 2), K["crimson"], bevel=0.1, segments=3)
    for sx in (-1, 1):
        # the arms: tufted on the inside face, rolled outward over the top, a scroll face with nailheads in front
        x = sx * (W / 2 - 0.3)
        box(f"Arm{sx}", (0.55, D - 0.15, H - 0.6), (x, 0, 0.35 + (H - 0.6) / 2), K["crimson"], bevel=0.12, segments=3)
        tufted(f"ArmTuft{sx}", D - 0.55, H - SH - 0.15, K["crimson"], K["button"], nx=4, nz=2, depth=0.22, puff=0.12,
               xf=Matrix.Translation((x - sx * 0.27, -0.1, SH)) @ Matrix.Rotation(-sx * math.pi / 2, 4, "Z"))
        cyl(f"ArmRoll{sx}", 0.3, D - 0.1, (x + sx * 0.04, 0, H - 0.3), K["crimson"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.0)
        cyl(f"Scroll{sx}", 0.24, 0.06, (x + sx * 0.04, -D / 2 + 0.02, H - 0.3), K["crimsondk"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
        nails(f"Nail{sx}_", [(x + sx * 0.04 + math.cos(t) * 0.27, -D / 2 - 0.02, H - 0.3 + math.sin(t) * 0.27) for t in [i / 14 * 2 * math.pi for i in range(14)]], K["brass"])
        nails(f"NailF{sx}_", [(x + sx * 0.04, -D / 2 + 0.0, 0.5 + k * 0.17) for k in range(7)], K["brass"])
    nails("NailBase", [(-W / 2 + 0.6 + k * (W - 1.2) / 24, -D / 2 + 0.04, 0.42) for k in range(25)], K["brass"])
    for k in range(3):
        cw = (W - 1.2) / 3
        cushion(f"Seat{k}", (cw - 0.04, D - 0.75, 0.42), (-W / 2 + 0.6 + cw * (k + 0.5), -0.22, SH - 0.02), K["crimson"], piping=K["crimsondk"], puff=0.12)
    return _dims()


def camelback_sofa(M):
    K = kit(M)
    W, D, SH = 6.0, 2.6, 1.45
    prof = [(-W / 2 + 0.3, 1.9), (-W / 2 + 1.0, 2.5), (-1.2, 3.1), (0.0, 3.3), (1.2, 3.1), (W / 2 - 1.0, 2.5), (W / 2 - 0.3, 1.9)]
    outline = [(-W / 2 + 0.3, SH - 0.2)] + prof + [(W / 2 - 0.3, SH - 0.2)]
    sm = WS.resample(PC_smooth(outline), 0.08)
    B20.tprism("BackPad", WS.ccw(sm), D / 2 - 0.35, 0.5, K["black"], bevel=0.08)
    rail = [(x, D / 2 - 0.1, z + 0.08) for x, z in PC_smooth(prof, closed=False)]
    tube("Rail", rail, 0.09, K["ebony"])
    tube("RailBead", [(x, y - 0.09, z) for x, y, z in rail], 0.03, K["gilt"])
    cushion("RailCrest", (0.5, 0.18, 0.4), (0, D / 2 - 0.2, 3.44), K["ebony"], e=(0.5, 0.5), cuts=5)
    foil("RailFoil", 0, D / 2 - 0.3, 3.44, 0.12, K["gilt"], lobes=4, thick=0.02)
    tube("BackPiping", [(x, D / 2 - 0.61, z) for x, z in sm] + [(sm[0][0], D / 2 - 0.61, sm[0][1])], 0.03, K["crimson"], poly=True)
    box("SeatDeck", (W - 0.5, D - 0.3, 0.55), (0, 0, 0.75 + 0.27), K["black"], bevel=0.1, segments=3)
    box("Apron", (W - 0.3, 0.12, 0.3), (0, -D / 2 + 0.12, 0.72), K["ebony"], bevel=0.03)
    tube("ApronBead", [(-W / 2 + 0.2, -D / 2 + 0.05, 0.6), (W / 2 - 0.2, -D / 2 + 0.05, 0.6)], 0.025, K["gilt"], poly=True)
    cushion("Seat", (W - 1.2, D - 0.8, 0.42), (0, -0.2, SH - 0.02), K["black"], piping=K["crimson"], puff=0.1)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.3)
        box(f"Arm{sx}", (0.45, D - 0.3, 1.0), (x, -0.05, SH + 0.15), K["black"], bevel=0.14, segments=3)
        tube(f"ArmRail{sx}", [(x, -D / 2 + 0.15, SH + 0.68), (x, D / 2 - 0.3, SH + 0.68)], 0.09, K["ebony"], poly=True)
        cushion(f"Bolster{sx}", (0.5, 0.5, 1.5), (x - sx * 0.6, -0.15, SH + 0.45), K["crimson"], e=(0.9, 0.9), cuts=6, rot=(math.pi / 2, 0, 0))
        sphere(f"BolsterButton{sx}", 0.07, (x - sx * 0.6, -0.92, SH + 0.45), K["gilt"], seg=8, rings=4)
        for sy in (-1, 1):
            cabriole(f"Leg{sx}{sy}", sx * (W / 2 - 0.4), sy * (D / 2 - 0.3), 0.85, K["ebony"], K["gilt"], sx=sx, sy=sy)
    return _dims()


def PC_smooth(pts, closed=True, it=3):
    """Chaikin-smooth a 2D polyline (keeps the ends when open)."""
    out = list(pts)
    for _ in range(it):
        nxt = []
        n = len(out)
        rng = range(n) if closed else range(n - 1)
        if not closed:
            nxt.append(out[0])
        for i in rng:
            a, b = out[i], out[(i + 1) % n]
            nxt.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            nxt.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        if not closed:
            nxt.append(out[-1])
        out = nxt
    return out


def chaise_longue(M):
    K = kit(M)
    L, D, SH = 6.2, 2.4, 1.35
    box("Frame", (L - 0.2, D - 0.1, 0.5), (0, 0, 0.55 + 0.25), K["damask"], bevel=0.1, segments=3)
    tube("FrameBead", [(-L / 2 + 0.1, -D / 2 + 0.03, 0.58), (L / 2 - 0.1, -D / 2 + 0.03, 0.58)], 0.03, K["gilt"], poly=True)
    box("FrameRail", (L - 0.1, D, 0.16), (0, 0, 0.6), K["ebony"], bevel=0.04)
    cushion("Seat", (L - 1.0, D - 0.3, 0.45), (0.35, 0, SH - 0.1), K["damask"], piping=K["crimsondk"], puff=0.08)
    # the scrolled head end, high on the left
    head = PC_smooth([(-L / 2 + 0.05, 0.6), (-L / 2 + 0.05, 2.7), (-L / 2 + 0.2, 3.2), (-L / 2 + 0.6, 3.35), (-L / 2 + 0.95, 3.1), (-L / 2 + 0.9, 2.8),
                      (-L / 2 + 0.6, 2.75), (-L / 2 + 0.55, 1.2), (-L / 2 + 0.7, 0.6)])
    B20.tprism("HeadEnd", WS.ccw(head), 0, D - 0.15, K["damask"], plane="XZ", bevel=0.06)
    for sy in (-1, 1):
        y = sy * (D / 2 - 0.06)
        spiral = [(-L / 2 + 0.62 + math.cos(t) * 0.32 * (1 - t / 13), y + sy * 0.05, 3.0 + math.sin(t) * 0.32 * (1 - t / 13)) for t in [i / 3 for i in range(0, 34)]]
        tube(f"Scroll{sy}", spiral, 0.05, K["gilt"])
    # the back rail sloping away along the far side
    back = PC_smooth([(-L / 2 + 0.6, SH), (-L / 2 + 0.6, 2.9), (-0.4, 2.3), (1.2, 1.75), (1.6, SH)])
    B20.tprism("BackRest", WS.ccw(back), D / 2 - 0.25, 0.4, K["damask"], bevel=0.06)
    tube("BackRail", [(x, D / 2 - 0.05, z + 0.06) for x, z in back[1:-6]], 0.07, K["ebony"])
    tube("BackBead", [(x, D / 2 - 0.13, z + 0.02) for x, z in back[1:-6]], 0.025, K["gilt"])
    cushion("Bolster", (0.5, 0.5, D - 0.5), (-L / 2 + 0.95, 0, SH + 0.45), K["crimson"], e=(0.9, 0.9), cuts=6, rot=(math.pi / 2, 0, 0))
    for sy in (-1, 1):
        sphere(f"BolsterEnd{sy}", 0.08, (-L / 2 + 0.95, sy * (D / 2 - 0.22), SH + 0.45), K["gilt"], seg=10, rings=5)
        tassel(f"BolsterTassel{sy}", -L / 2 + 0.95, sy * (D / 2 - 0.15), SH + 0.38, K["cord"], K["cord"], 0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (L / 2 - 0.35), sy * (D / 2 - 0.3)
            turned_leg(f"Leg{sx}{sy}", x, y, 0.5, K["ebony"], collar=K["gilt"], r=0.11)
            sphere(f"Castor{sx}{sy}", 0.07, (x, y, 0.06), K["brass"], seg=10, rings=5)
    return _dims()


def gothic_settle(M):
    K = kit(M)
    W, D, SH, H = 6.0, 2.2, 1.45, 6.2
    lac, gl = K["lacquer"], K["gilt"]
    box("Seatbox", (W - 0.6, D - 0.2, SH - 0.35), (0, 0, 0.15 + (SH - 0.35) / 2), lac, bevel=0.04)
    for k in range(4):
        foil(f"ApronFoil{k}", -W / 2 + 1.05 + k * (W - 2.1) / 3, -D / 2 + 0.08, 0.7, 0.28, gl, lobes=4, thick=0.025)
    box("Plinth", (W - 0.4, D, 0.15), (0, 0, 0.075), lac, bevel=0.03)
    box("BackBoard", (W - 0.6, 0.22, H - SH), (0, D / 2 - 0.15, SH + (H - SH) / 2), lac, bevel=0.03)
    bw = (W - 0.6) / 3
    for k in range(3):
        cx = -W / 2 + 0.3 + bw * (k + 0.5)
        hw = bw / 2 - 0.16
        arch = WS.arch(hw, SH + 0.35, H - 1.6, H - 0.55, 14, cx=cx)
        pad = WS.offset(arch, -0.06)
        tufted(f"Pad{k}", hw * 2, H - 0.55 - SH - 0.35, K["crimson"], K["button"], nx=3, nz=5, depth=0.32, puff=0.12,
               outline=[(x - cx, z - SH - 0.35) for x, z in pad], xf=Matrix.Translation((cx, D / 2 - 0.26, SH + 0.35)))
        tube(f"ArchMould{k}", [(x, D / 2 - 0.3, z) for x, z in WS.offset(arch, 0.04)], 0.05, gl, square=True, poly=True)
        _spike(f"Crocket{k}", (cx, D / 2 - 0.2, H - 0.45), 0.1, 0.3, gl)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.15)
        # a tall back post with a pinnacle, a front post to the arm with a gilt knop, an open arm between them
        box(f"BackPost{sx}", (0.36, 0.36, H - 0.3), (x, D / 2 - 0.2, (H - 0.3) / 2), lac, bevel=0.03)
        P_spirelet(f"Pin{sx}", x, D / 2 - 0.2, H - 0.3, 1.3, 0.36, lac, gl)
        box(f"FrontPost{sx}", (0.3, 0.3, SH + 1.0), (x, -D / 2 + 0.2, (SH + 1.0) / 2), lac, bevel=0.03)
        sphere(f"FrontKnop{sx}", 0.17, (x, -D / 2 + 0.2, SH + 1.15), gl, seg=12, rings=6)
        box(f"Arm{sx}", (0.26, D - 0.3, 0.16), (x, 0, SH + 0.95), lac, bevel=0.04)
        for k in range(3):
            tube(f"ArmBaluster{sx}{k}", [(x, -D / 2 + 0.6 + k * 0.45, SH + 0.05), (x, -D / 2 + 0.6 + k * 0.45, SH + 0.88)], 0.05, lac, poly=True)
        foil(f"ArmFoil{sx}", x, -D / 2 + 0.04, SH - 0.4, 0.12, gl, lobes=4, thick=0.02)
    P_spirelet("PinMid", 0, D / 2 - 0.15, H, 1.0, 0.3, lac, gl)
    cushion("Seat", (W - 0.9, D - 0.5, 0.36), (0, -0.15, SH + 0.1), K["weave"], piping=K["crimsondk"], puff=0.1)
    return _dims()


def _spike(name, loc, r, h, mat):
    from nh_props_batch8 import _spike as sp
    sp(name, loc, r, h, mat)


def P_spirelet(name, x, y, z, h, w, mat, gl):
    from nh_props_batch8 import _spirelet
    _spirelet(name, x, y, z, h, w, mat, crockets=2)
    sphere(f"{name}Gilt", w * 0.18, (x, y, z + h + 0.05), gl, seg=10, rings=5)


def shell_loveseat(M):
    K = kit(M)
    W, D, SH = 4.4, 2.4, 1.4
    # the shell: a scalloped fan, padded, with channel cords radiating from its foot, a gilt rim along its edge
    R0, zb = W / 2 - 0.2, SH - 0.2
    fan = []
    for i in range(13):
        a0, a1 = math.radians(-80 + 160 * i / 13), math.radians(-80 + 160 * (i + 1) / 13)
        for j in range(5):
            t = j / 4
            a = a0 + (a1 - a0) * t
            r = R0 * (1.0 - 0.05 * math.sin(math.pi * t))
            fan.append((math.sin(a) * r, zb + math.cos(a) * r * 0.95))
    fan = [(fan[0][0], zb)] + fan + [(fan[-1][0], zb)]
    B20.tprism("Shell", WS.ccw(fan), D / 2 - 0.45, 0.45, K["bone"], bevel=0.12)
    for i in range(1, 13):
        a = math.radians(-80 + 160 * i / 13)
        tube(f"Channel{i}", [(math.sin(a) * 0.35, D / 2 - 0.72, zb + math.cos(a) * 0.33), (math.sin(a) * R0 * 0.93, D / 2 - 0.72, zb + math.cos(a) * R0 * 0.88)], 0.028, K["cord"], poly=True)
    tube("ShellRim", [(x, D / 2 - 0.45, z) for x, z in WS.offset(WS.ccw(fan), 0.02)[1:-1]], 0.06, K["gilt"], poly=True)
    sphere("ShellBoss", 0.22, (0, D / 2 - 0.68, zb + 0.15), K["gilt"], seg=12, rings=6, scale=(1, 0.5, 1))
    box("Base", (W - 0.2, D - 0.2, 0.7), (0, 0, 0.5 + 0.35), K["bone"], bevel=0.14, segments=3)
    tube("BasePiping", [(-W / 2 + 0.1, -D / 2 + 0.1, 1.18), (W / 2 - 0.1, -D / 2 + 0.1, 1.18)], 0.03, K["gilt"], poly=True)
    for k in range(2):
        cushion(f"Seat{k}", ((W - 1.0) / 2 - 0.03, D - 0.8, 0.4), (-(W - 1.0) / 4 + k * (W - 1.0) / 2, -0.2, SH), K["bone"], piping=K["crimson"], puff=0.12)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.25)
        cushion(f"Arm{sx}", (0.5, D - 0.3, 1.3), (x, -0.05, SH + 0.05), K["bone"], e=(0.55, 0.4), cuts=7)
        sphere(f"ArmRosette{sx}", 0.12, (x, -D / 2 + 0.1, SH + 0.35), K["gilt"], seg=12, rings=6, scale=(1, 0.5, 1))
        cushion(f"Pillow{sx}", (0.9, 0.3, 0.9), (x - sx * 0.75, 0.55, SH + 0.65), K["crimson"], e=(0.6, 0.3), cuts=6, rot=(0.25, 0, sx * 0.1), piping=K["cord"])
        for sy in (-1, 1):
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.05, 0), (0.08, 0.35), (0.11, 0.5), (0, 0.5)], K["gilt"], seg=12, loc=(sx * (W / 2 - 0.35), sy * (D / 2 - 0.3), 0))
    return _dims()


def corner_sectional(M):
    K = kit(M)
    L, D, SH = 9.0, 2.8, 1.25
    ink, blk = K["ink"], K["lacquer"]
    # two runs meeting at the back-left corner: one along X (the back), one along Y (the left side)
    box("PlinthA", (L, D, 0.25), (0, 0, 0.125), blk, bevel=0.03)
    box("PlinthB", (D, L - D, 0.25), (-L / 2 + D / 2, -(L - D) / 2 - D / 2 + 0.0, 0.125), blk, bevel=0.03)
    box("DeckA", (L - 0.1, D - 0.1, 0.7), (0, 0, 0.25 + 0.35), ink, bevel=0.12, segments=3)
    box("DeckB", (D - 0.1, L - D - 0.1, 0.7), (-L / 2 + D / 2, -(L - D) / 2 - D / 2, 0.25 + 0.35), ink, bevel=0.12, segments=3)
    box("BackA", (L - 0.2, 0.55, 1.5), (0, D / 2 - 0.3, 1.0 + 0.75), ink, bevel=0.15, segments=3)
    box("BackB", (0.55, L - D, 1.5), (-L / 2 + 0.3, -(L - D) / 2 - D / 2 + 0.25, 1.0 + 0.75), ink, bevel=0.15, segments=3)
    box("ArmA", (0.6, D - 0.1, 1.2), (L / 2 - 0.3, 0, 1.2), ink, bevel=0.15, segments=3)
    box("ArmB", (D - 0.1, 0.6, 1.2), (-L / 2 + D / 2, -L + D / 2 + 0.3 + 0.0, 1.2), ink, bevel=0.15, segments=3)
    # seat and back cushions round the L
    n = 3
    sw = (L - D - 0.6) / n
    for k in range(n):
        x = -L / 2 + D + sw * (k + 0.5)
        cushion(f"SeatA{k}", (sw - 0.04, D - 0.8, 0.38), (x, -0.2, SH), ink, piping=K["crimsondk"], puff=0.1)
        cushion(f"BackCushA{k}", (sw - 0.06, 0.55, 1.3), (x, D / 2 - 0.85, SH + 0.8), ink, piping=K["crimsondk"], rot=(-0.18, 0, 0), puff=0.15)
        y = -D / 2 - sw * (k + 0.5) + 0.12
        cushion(f"SeatB{k}", (D - 0.8, sw - 0.04, 0.38), (-L / 2 + D / 2 + 0.2, y, SH), ink, piping=K["crimsondk"], puff=0.1)
        cushion(f"BackCushB{k}", (0.55, sw - 0.06, 1.3), (-L / 2 + 0.85, y, SH + 0.8), ink, piping=K["crimsondk"], rot=(0, -0.18, 0), puff=0.15)
    cushion("SeatCorner", (D - 0.8, D - 0.8, 0.38), (-L / 2 + D / 2 + 0.2, -0.2, SH), ink, piping=K["crimsondk"], puff=0.1)
    for k, (x, y, r) in enumerate(((L / 2 - 1.2, 0.5, 0.2), (-L / 2 + 1.0, 0.4, -0.3), (-L / 2 + 0.95, -L + D + 1.2, 1.4))):
        cushion(f"Pillow{k}", (1.0, 0.32, 1.0), (x, y, SH + 0.85), K["batdamaskcr"], e=(0.6, 0.25), cuts=6, rot=(0.25, 0, r), piping=K["cord"])
    return _dims()


def coffin_couch(M):
    K = kit(M)
    W, D, SH = 5.2, 2.4, 1.4
    lac, br = K["lacquer"], K["brass"]
    coffin = [(-1.25, SH - 0.2), (1.25, SH - 0.2), (2.35, 3.2), (1.6, 5.0), (-1.6, 5.0), (-2.35, 3.2)]
    B20.tprism("CoffinLid", WS.ccw(coffin), D / 2 - 0.15, 0.35, lac, bevel=0.06)
    inner = WS.offset(WS.ccw(coffin), -0.22)
    tufted("CoffinPad", 4.3, 5.0 - SH - 0.2, K["crimson"], K["button"], nx=7, nz=5, depth=0.3, puff=0.13,
           outline=[(x, z - (SH - 0.2)) for x, z in inner], xf=Matrix.Translation((0, D / 2 - 0.33, SH - 0.2)))
    tube("CoffinMould", [(x, D / 2 - 0.34, z) for x, z in WS.offset(WS.ccw(coffin), -0.1)] + [(WS.offset(WS.ccw(coffin), -0.1)[0][0], D / 2 - 0.34, WS.offset(WS.ccw(coffin), -0.1)[0][1])],
         0.05, br, square=True, poly=True)
    B20.tprism("CoffinCross", WS.ccw([(-0.06, 4.35), (0.06, 4.35), (0.06, 4.6), (0.22, 4.6), (0.22, 4.72), (0.06, 4.72), (0.06, 4.85), (-0.06, 4.85),
                                     (-0.06, 4.72), (-0.22, 4.72), (-0.22, 4.6), (-0.06, 4.6)]), D / 2 - 0.36, 0.04, br)
    box("Base", (W - 0.2, D - 0.2, 0.85), (0, 0, 0.3 + 0.42), lac, bevel=0.08)
    box("BaseBand", (W, D, 0.16), (0, 0, 0.3), lac, bevel=0.04)
    for k in range(5):
        cyl(f"Stud{k}", 0.05, 0.04, (-W / 2 + 0.6 + k * (W - 1.2) / 4, -D / 2 + 0.08, 0.75), br, rot=(math.pi / 2, 0, 0), verts=10)
    cushion("Seat", (W - 1.1, D - 0.6, 0.42), (0, -0.15, SH), K["crimson"], piping=K["crimsondk"], puff=0.12)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.25)
        box(f"Arm{sx}", (0.5, D - 0.2, 1.1), (x, 0, SH + 0.1), lac, bevel=0.06)
        cushion(f"ArmPad{sx}", (0.46, D - 0.4, 0.2), (x, 0, SH + 0.7), K["crimson"], e=(0.5, 0.3), cuts=6)
        # brass coffin handles along the arm sides
        for sy in (-1, 1):
            y = sy * 0.55
            tube(f"Handle{sx}{sy}", [(x + sx * 0.27, y - 0.3, SH + 0.15), (x + sx * 0.42, y - 0.22, SH + 0.15), (x + sx * 0.42, y + 0.22, SH + 0.15), (x + sx * 0.27, y + 0.3, SH + 0.15)],
                 0.035, br, poly=True)
            cyl(f"HandlePlate{sx}{sy}", 0.09, 0.03, (x + sx * 0.26, y - 0.3, SH + 0.15), br, rot=(0, math.pi / 2, 0), verts=10)
            cyl(f"HandlePlateB{sx}{sy}", 0.09, 0.03, (x + sx * 0.26, y + 0.3, SH + 0.15), br, rot=(0, math.pi / 2, 0), verts=10)
        for sy in (-1, 1):
            box(f"Foot{sx}{sy}", (0.4, 0.4, 0.3), (sx * (W / 2 - 0.35), sy * (D / 2 - 0.35), 0.15), lac, bevel=0.05)
    return _dims()


def batwing_sofa(M):
    K = kit(M)
    W, D, SH = 6.4, 2.5, 1.4
    # the wings: a scalloped outline, padded in black bat damask, finger bones in gilt
    tips = [(3.15, 2.0), (2.85, 3.9), (2.0, 3.25), (1.25, 3.55), (0.55, 3.0)]
    right = [(0.4, SH - 0.15), (3.1, SH - 0.15)]
    for (ax, az), (bx, bz) in zip([(3.1, SH - 0.15)] + tips[:-1], tips):
        for j in range(1, 7):
            t = j / 6
            right.append((ax + (bx - ax) * t, az + (bz - az) * t - (0.0 if (ax, az) == (3.1, SH - 0.15) else 0.32 * math.sin(math.pi * t))))
    right = right[:2] + right[2:]
    outline = right + [(-x, z) for x, z in reversed(right)]
    B20.tprism("Wings", WS.ccw(outline), D / 2 - 0.3, 0.45, K["batdamask"], bevel=0.08)
    for sx in (-1, 1):
        root = (sx * 0.5, D / 2 - 0.56, 2.3)
        tube(f"Arm{sx}", [root, (sx * 1.6, D / 2 - 0.56, 3.3), (sx * 2.85, D / 2 - 0.56, 3.85)], 0.06, K["gilt"])
        for k, (tx, tz) in enumerate(tips[:-1]):
            tube(f"Finger{sx}{k}", [(sx * 1.6, D / 2 - 0.56, 3.3), (sx * tx, D / 2 - 0.56, tz)], 0.04, K["gilt"], poly=True)
    cushion("BatHead", (0.9, 0.5, 0.75), (0, D / 2 - 0.4, 3.35), K["black"], e=(0.6, 0.6), cuts=6)
    for sx in (-1, 1):
        cone(f"Ear{sx}", 0.18, 0.0, 0.6, (sx * 0.25, D / 2 - 0.4, 3.85), K["black"], verts=6, rot=(0, sx * -0.25, 0))
        sphere(f"Eye{sx}", 0.06, (sx * 0.17, D / 2 - 0.67, 3.42), flat("BatEye", (0.55, 0.05, 0.03), 0.3), seg=8, rings=4)
    box("Base", (W - 1.6, D - 0.2, 0.8), (0, 0, 0.4 + 0.4), K["black"], bevel=0.12, segments=3)
    tube("BasePiping", [(-W / 2 + 0.85, -D / 2 + 0.1, 1.17), (W / 2 - 0.85, -D / 2 + 0.1, 1.17)], 0.03, K["gilt"], poly=True)
    cushion("Seat", (W - 2.0, D - 0.8, 0.42), (0, -0.2, SH), K["crimson"], piping=K["crimsondk"], puff=0.1)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.65)
        cushion(f"ArmBlock{sx}", (0.65, D - 0.3, 1.2), (x, -0.05, SH - 0.05), K["black"], e=(0.5, 0.35), cuts=7)
        for sy in (-1, 1):
            turned_leg(f"Leg{sx}{sy}", sx * (W / 2 - 1.0), sy * (D / 2 - 0.35), 0.42, K["ebony"], collar=K["gilt"], r=0.1)
    return _dims()


def throne_settee(M):
    K = kit(M)
    W, D, SH, H = 4.6, 2.5, 1.45, 6.4
    gl = K["gilt"]
    back = [(-W / 2 + 0.35, SH - 0.1)] + [(x, z) for x, z in WS.pointed(W / 2 - 0.35, H - 2.2, H - 0.3, 18)] + [(W / 2 - 0.35, SH - 0.1)]
    B20.tprism("BackShell", WS.ccw(back), D / 2 - 0.2, 0.35, K["ebony"], bevel=0.05)
    pad = WS.offset(WS.ccw(back), -0.22)
    tufted("BackPad", W - 1.1, H - 0.5 - SH, K["crimson"], K["button"], nx=6, nz=7, depth=0.32, puff=0.13,
           outline=[(x, z - (SH - 0.1)) for x, z in pad], xf=Matrix.Translation((0, D / 2 - 0.37, SH - 0.1)))
    edge = WS.offset(WS.ccw(back), 0.02)
    tube("Frame", [(x, D / 2 - 0.39, z) for x, z in edge[1:-1]], 0.08, gl)
    for k, (x, z) in enumerate(edge[3:-3:2]):
        sphere(f"Crocket{k}", 0.1, (x, D / 2 - 0.3, z + 0.08), gl, seg=8, rings=4, scale=(1, 1, 1.4))
    P_spirelet("Finial", 0, D / 2 - 0.3, H - 0.25, 1.0, 0.34, gl, gl)
    B20._crest("Crest", 0, D / 2 - 0.62, H - 1.55, P_pal(M, K), gl, s=1.5)
    box("Base", (W - 0.2, D - 0.2, 0.75), (0, 0, 0.45 + 0.37), K["crimson"], bevel=0.12, segments=3)
    box("BaseRail", (W, D, 0.2), (0, 0, 0.42), K["ebony"], bevel=0.04)
    tube("BaseBead", [(-W / 2 + 0.05, -D / 2 - 0.01, 0.5), (W / 2 - 0.05, -D / 2 - 0.01, 0.5)], 0.03, gl, poly=True)
    for k in range(2):
        cushion(f"Seat{k}", ((W - 1.1) / 2 - 0.03, D - 0.7, 0.42), (-(W - 1.1) / 4 + k * (W - 1.1) / 2, -0.15, SH), K["crimson"], piping=K["cord"], puff=0.12)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.25)
        box(f"Arm{sx}", (0.42, D - 0.3, 1.0), (x, -0.05, SH + 0.15), K["crimson"], bevel=0.12, segments=3)
        box(f"ArmRail{sx}", (0.5, D - 0.15, 0.16), (x, -0.05, SH + 0.72), K["ebony"], bevel=0.05)
        lathe(f"ArmPost{sx}", [(0, 0.4), (0.1, 0.4), (0.13, 0.6), (0.08, 1.2), (0.13, 1.8), (0.1, SH + 0.64), (0, SH + 0.64)], K["ebony"], seg=12, loc=(x, -D / 2 + 0.22, 0))
        raven(f"Raven{sx}", (x, -D / 2 + 0.25, SH + 0.8), -math.pi / 2 + sx * 0.5, 2.4, flat("RavenBlack", (0.02, 0.02, 0.03), 0.4), gl)
        for sy in (-1, 1):
            box(f"Foot{sx}{sy}", (0.42, 0.42, 0.42), (sx * (W / 2 - 0.25), sy * (D / 2 - 0.25), 0.21), K["ebony"], bevel=0.06)
            sphere(f"FootBall{sx}{sy}", 0.09, (sx * (W / 2 - 0.25), sy * (D / 2 - 0.25) - (0.22 if sy < 0 else -0.22), 0.25), gl, seg=8, rings=4)
    return _dims()


def P_pal(M, K):
    return {"crimson": M["crimson"]}


def tufted_bench(M):
    K = kit(M)
    W, D, H = 6.0, 1.8, 1.55
    tufted("Top", W - 0.1, D - 0.1, K["plum"], K["button"], nx=8, nz=2, depth=0.42, puff=0.16,
           xf=Matrix.Translation((0, 0, H - 0.42)) @ Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Translation((0, 0, -(D - 0.1) / 2)))
    box("Rail", (W, D, 0.3), (0, 0, H - 0.56), K["ebony"], bevel=0.04)
    tube("RailBead", [(-W / 2 + 0.02, -D / 2 - 0.01, H - 0.62), (W / 2 - 0.02, -D / 2 - 0.01, H - 0.62)], 0.025, K["gilt"], poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(f"Leg{sx}{sy}", sx * (W / 2 - 0.3), sy * (D / 2 - 0.25), H - 0.7, K["ebony"], collar=K["gilt"], r=0.13)
            tassel(f"Tassel{sx}{sy}", sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H - 0.42, K["cord"], K["cord"])
    box("Stretcher", (W - 0.6, 0.12, 0.12), (0, 0, 0.35), K["ebony"], bevel=0.03)
    return _dims()


def round_ottoman(M):
    K = kit(M)
    R, H = 1.6, 1.5
    ink = K["ink"]
    lathe("Drum", [(0, 0.12), (R - 0.05, 0.12), (R, 0.3), (R, H - 0.45), (R - 0.05, H - 0.4), (0, H - 0.4)], ink, seg=48)
    # the top: a dome tufted on rings of buttons
    rings = 12
    me = bpy.data.meshes.new("Top")
    bm = bmesh.new()
    btn = [(0.0, 0.0)] + [(math.cos(a) * 0.62, math.sin(a) * 0.62) for a in [k / 8 * 2 * math.pi for k in range(8)]] + \
          [(math.cos(a) * 1.2, math.sin(a) * 1.2) for a in [(k + 0.5) / 12 * 2 * math.pi for k in range(12)]]

    def top(x, y):
        r = math.hypot(x, y) / R
        base = H - 0.42 + 0.38 * max(0.0, 1 - r ** 2.4) ** 0.6
        dip = max(math.exp(-((x - bx) ** 2 + (y - by) ** 2) / 0.03) for bx, by in btn)
        return base - 0.16 * dip * max(0.0, 1 - r ** 4)
    n, m = 48, 28
    verts = [[bm.verts.new((math.cos(a) * R * t, math.sin(a) * R * t, top(math.cos(a) * R * t, math.sin(a) * R * t))) for a in [i / n * 2 * math.pi for i in range(n)]]
             for t in [j / m for j in range(1, m + 1)]]
    c0 = bm.verts.new((0, 0, top(0, 0)))
    for i in range(n):
        bm.faces.new((c0, verts[0][i], verts[0][(i + 1) % n]))
    for j in range(m - 1):
        for i in range(n):
            bm.faces.new((verts[j][i], verts[j + 1][i], verts[j + 1][(i + 1) % n], verts[j][(i + 1) % n]))
    for f in bm.faces:
        f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.faces[:] and bm.faces[0].normal.z < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Top", me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, ink, 0)
    for k, (bx, by) in enumerate(btn[1:]):
        sphere(f"Button{k}", 0.05, (bx, by, top(bx, by) + 0.01), K["button"], seg=8, rings=4, scale=(1, 1, 0.6))
    sphere("TopButton", 0.1, (0, 0, top(0, 0) + 0.04), K["gilt"], seg=12, rings=6)
    tassel("TopTassel", 0.05, -0.05, top(0, 0) + 0.02, K["cord"], K["cord"], 1.2)
    hoop("Welt", (0, 0, H - 0.42), R + 0.005, "Z", K["cord"], thick=0.035)
    # the bullion fringe: twisted gilt cords hanging all round the drum's foot
    for k in range(110):
        a = k / 110 * 2 * math.pi
        x, y = math.cos(a) * (R + 0.035), math.sin(a) * (R + 0.035)
        tx, ty = -math.sin(a) * 0.035, math.cos(a) * 0.035
        tube(f"Bullion{k}", [(x, y, 0.62), (x + tx, y + ty, 0.48), (x * 1.012, y * 1.012, 0.34), (x - tx, y - ty, 0.22), (x * 1.005, y * 1.005, 0.14)], 0.024, K["cord"], poly=True)
    hoop("FringeBand", (0, 0, 0.64), R + 0.025, "Z", K["cord"], thick=0.04)
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        bun(f"Foot{k}", math.cos(a) * (R - 0.4), math.sin(a) * (R - 0.4), K["ebony"], r=0.15, h=0.14)
    return _dims()


# ================================================================== the woven pieces (rugs, mats, carpets, tapestries)

TEXTILE = {}       # piece -> {maps, mode ("top" / "front"), rect (x0, x1, a0, a1)}


def _register(piece, maps, mode, rect):
    TEXTILE[piece] = {"maps": maps, "mode": mode, "rect": rect}
    P.CANVAS[piece] = maps


def slab(name, poly, h, mat, bevel=0.012):
    """A flat cloth on the floor: the outline (x, y) extruded up h."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, 0.0)) for x, y in poly]
    hi = [bm.verts.new((x, y, h)) for x, y in poly]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, bevel, segments=2)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    return ob


def _fringe(prefix, x0, x1, y, side, mat, every=0.11, length=0.34):
    """Knotted fringe off a rug's end at y (side -1 hangs toward -Y): tassel bundles lying on the floor."""
    n = int((x1 - x0) / every)
    rnd = random.Random(int(abs(y) * 100) + n)
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        L = length * rnd.uniform(0.85, 1.1)
        a = rnd.uniform(-0.12, 0.12)
        box(f"{prefix}{k}", (0.05, L, 0.02), (x + math.sin(a) * L / 2, y + side * L / 2, 0.012), mat, bevel=0.0, segments=1, rot=(0, 0, a))


def rug(maps, w, d, h=0.06, fringe=True, shape="rect", bind=True, bevel=0.012):
    mat = flat("RugTmp", (0.3, 0.1, 0.1), 0.9)
    if shape == "rect":
        slab("Rug", [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)], h, mat, bevel=bevel)
        if bind:
            for sx in (-1, 1):
                tube(f"Binding{sx}", [(sx * w / 2, -d / 2 + 0.01, h * 0.5), (sx * w / 2, d / 2 - 0.01, h * 0.5)], h * 0.55, mat, poly=True)
        if fringe:
            for sy in (-1, 1):
                _fringe(f"Fringe{sy}", -w / 2 + 0.06, w / 2 - 0.06, sy * d / 2, sy, mat)
        rect = (-w / 2, w / 2, -d / 2, d / 2)
    elif shape == "round":
        r = w / 2
        slab("Rug", [(math.cos(a) * r, math.sin(a) * r) for a in [i / 96 * 2 * math.pi for i in range(96)]], h, mat)
        if bind:
            hoop("Binding", (0, 0, h * 0.5), r, "Z", mat, thick=h * 0.55)
        rect = (-r, r, -r, r)
    elif shape == "octagon":
        R = w / 2 / math.cos(math.pi / 8)
        poly = [(math.cos(math.pi / 8 + k * math.pi / 4) * R, math.sin(math.pi / 8 + k * math.pi / 4) * R) for k in range(8)]
        slab("Rug", poly, h, mat)
        if bind:
            tube("Binding", [(x, y, h * 0.5) for x, y in poly], h * 0.55, mat, closed=True, poly=True)
        rect = (-w / 2, w / 2, -w / 2, w / 2)
    elif shape == "half":
        r = w / 2
        poly = [(math.cos(a) * r, d - math.sin(a) * r * (d / r)) for a in [i / 64 * math.pi for i in range(65)]]
        poly = [(x, y - d / 2) for x, y in poly]
        slab("Rug", poly, h, mat)
        if bind:
            tube("Binding", [(x, y, h * 0.5) for x, y in poly], h * 0.55, mat, poly=True)
        rect = (-r, r, -d / 2, d / 2)
    _register(maps, maps, "top", rect)
    W_, D_, H_ = _dims()
    return (W_, D_, max(W_, D_) * 0.28)      # the preview's camera looks down on a flat piece (only the preview uses the height)


TAP_W, TAP_H = 7.5, 10.0


def tapestry(maps, w=TAP_W, hgt=TAP_H, M=None):
    """A tapestry hanging from a gilt rod on iron brackets: rippled wool cloth (Weave), a gold tassel fringe below it; the
    rod, finials, brackets and rings (Main). Its back hangs at y = 0 (the wall)."""
    K = kit(M)
    z0 = 0.62
    z1 = z0 + hgt
    yc = -0.55                       # the cloth's plane
    set_group("Weave")
    cloth = flat("ClothTmp", (0.4, 0.1, 0.1), 0.9)
    nx, nz = int(w * 5.5), int(hgt * 5)       # enough for the ripples, under half the 20k a mesh may have
    me = bpy.data.meshes.new("Cloth")
    bm = bmesh.new()

    def ripple(x, z):
        t = (z1 - z) / hgt
        return yc - 0.05 * math.sin(x / w * math.pi * 7.0 + 0.6) * (0.25 + 0.75 * t) - 0.03 * math.sin(x / w * math.pi * 17 + z * 0.4) * t
    rows = [[bm.verts.new((-w / 2 + w * i / nx, ripple(-w / 2 + w * i / nx, z0 + hgt * j / nz), z0 + hgt * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.normal_update()
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Cloth", me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, cloth, 0)
    md = ob.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = 0.04
    md.offset = 1.0
    # the gold tassel fringe below the bottom edge
    n = int(w / 0.3)
    for k in range(n + 1):
        x = -w / 2 + 0.06 + (w - 0.12) * k / n
        y = ripple(x, z0)
        tube(f"FringeCord{k}", [(x, y, z0 + 0.02), (x, y, z0 - 0.16)], 0.02, cloth, poly=True)
        lathe(f"FringeTassel{k}", [(0, z0 - 0.16), (0.04, z0 - 0.16), (0.07, z0 - 0.4), (0.075, z0 - 0.58), (0, z0 - 0.58)], cloth, seg=10, loc=(x, y, 0))
    set_group("Main")
    # the rod, its finials, the rings through the cloth's loops, the brackets into the wall
    zr = z1 + 0.32
    tube("Rod", [(-w / 2 - 0.55, yc, zr), (w / 2 + 0.55, yc, zr)], 0.09, K["gilt"], poly=True)
    for sx in (-1, 1):
        x = sx * (w / 2 + 0.55)
        lathe(f"FinialBase{sx}", [(0, 0), (0.14, 0), (0.12, 0.06), (0.15, 0.12), (0, 0.12)], K["gilt"], seg=16)
        P.PARTS[-1].data.transform(Matrix.Translation((x, yc, zr)) @ Matrix.Rotation(sx * math.pi / 2, 4, "Y"))
        P.PARTS[-1].matrix_world = Matrix.Identity(4)
        sphere(f"FinialBall{sx}", 0.13, (x + sx * 0.18, yc, zr), K["gilt"], seg=14, rings=7)
        cone(f"FinialSpike{sx}", 0.07, 0.0, 0.42, (x + sx * 0.48, yc, zr), K["gilt"], verts=8, rot=(0, sx * math.pi / 2, 0))
        for k in range(3):
            a = (k - 1) * 0.7
            tube(f"FinialLeaf{sx}{k}", [(x + sx * 0.2, yc, zr), (x + sx * 0.32, yc + math.sin(a) * 0.14, zr + math.cos(a) * 0.14), (x + sx * 0.46, yc + math.sin(a) * 0.06, zr + math.cos(a) * 0.06)],
                 0.025, K["gilt"])
        bx = sx * (w / 2 + 0.25)
        tube(f"Bracket{sx}", [(bx, 0.0, zr + 0.35), (bx, -0.2, zr + 0.35), (bx, yc + 0.08, zr + 0.16), (bx, yc, zr - 0.11)], 0.04, K["iron"], poly=True)
        tube(f"BracketHook{sx}", [(bx, yc, zr - 0.11), (bx, yc - 0.14, zr - 0.05), (bx, yc - 0.14, zr + 0.06)], 0.03, K["iron"], poly=True)
        box(f"BracketPlate{sx}", (0.24, 0.04, 0.5), (bx, -0.02, zr + 0.3), K["iron"], bevel=0.015)
        for dz in (-0.15, 0.15):
            sphere(f"BracketRivet{sx}{dz:+.0f}", 0.03, (bx, -0.045, zr + 0.3 + dz), K["iron"], seg=8, rings=4)
    nr = int(w / 0.6)
    for k in range(nr + 1):
        x = -w / 2 + 0.1 + (w - 0.2) * k / nr
        hoop(f"Ring{k}", (x, yc, zr - 0.02), 0.14, "X", K["gilt"], thick=0.025)
        box(f"Tab{k}", (0.22, 0.06, 0.2), (x, yc - 0.02, z1 + 0.05), K["crimsondk"], bevel=0.02)
    _register(f"{maps}_Weave", f"{maps}Weave", "front", (-w / 2, w / 2, z0, z1))
    return _dims()


# ------------------------------------------------------------------ the woven pieces' UVs and materials

_orig_canvas_uv = P.canvas_uv
_orig_canvas_material = P.canvas_material
_orig_bake_uv, _orig_bake_all, _orig_final = P.bake_uv, P.bake_all, P.final_material


def _map_size(maps):
    im = bpy.data.images.load(os.path.join(P.OUT_TEX, f"{maps}_color.png"), check_existing=True)
    return im.size[0], im.size[1]


def textile_uv(ob, spec):
    """The design straight onto the cloth (top-down for floor pieces, from the front for hangings) over its rect; the
    fringe (outside the rect) onto the fringe wool swatch, the edges and back onto the backing swatch (the 32 px band)."""
    me = ob.data
    for uv in list(me.uv_layers):
        me.uv_layers.remove(uv)
    uv = me.uv_layers.new(name="Bake")
    me.uv_layers.active = uv
    W, H = _map_size(spec["maps"])
    sw = SW / H
    x0, x1, a0, a1 = spec["rect"]
    mw = ob.matrix_world
    rot = mw.to_3x3()
    eps = 0.06
    for poly in me.polygons:
        n = (rot @ poly.normal).normalized()
        cen = mw @ poly.center
        if spec["mode"] == "top":
            a = cen.y
            design = n.z > 0.5
            outside = cen.x < x0 - eps or cen.x > x1 + eps or a < a0 - eps or a > a1 + eps
        else:
            a = cen.z
            design = n.y < -0.3
            outside = a < a0 - eps or cen.x < x0 - eps or cen.x > x1 + eps
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if design and not outside:
                av = co.y if spec["mode"] == "top" else co.z
                u = (co.x - x0) / (x1 - x0)
                v = sw + (1 - sw) * (av - a0) / (a1 - a0)
                uv.data[li].uv = (min(max(u, 0.0005), 0.9995), min(max(v, sw + 0.0005), 0.9995))
            else:
                k = (co.x * 0.37 + co.y * 0.53 + co.z * 0.41) % 1.0
                u = (0.03 + 0.44 * k) if outside else (0.53 + 0.44 * k)
                v = sw * (0.2 + 0.6 * ((co.z * 5 + co.x * 0.3) % 1.0))
                uv.data[li].uv = (u, v)


def textile_material(ob, maps):
    m = bpy.data.materials.new(f"NH_{maps}")
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def tex(kind, color=False):
        p = os.path.join(P.OUT_TEX, f"{maps}_{kind}.png")
        if not os.path.exists(p):
            return None
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(p, check_existing=True)
        if not color:
            t.image.colorspace_settings.name = "Non-Color"
        return t
    nt.links.new(tex("color", True).outputs["Color"], bs.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(tex("rough").outputs["Color"], bs.inputs["Roughness"])
    mt = tex("metal")
    if mt:
        nt.links.new(mt.outputs["Color"], bs.inputs["Metallic"])
    else:
        bs.inputs["Metallic"].default_value = 0.0
    bs.inputs["Sheen Weight"].default_value = 0.05     # Roblox has no sheen; keep the preview honest
    ob.data.materials.clear()
    ob.data.materials.append(m)


def _canvas_uv(ob):
    if ob.name in TEXTILE:
        return textile_uv(ob, TEXTILE[ob.name])
    return _orig_canvas_uv(ob)


def _canvas_material(ob, image):
    if ob.name in TEXTILE:
        return textile_material(ob, TEXTILE[ob.name]["maps"])
    return _orig_canvas_material(ob, image)


def _bake_uv(objs):
    if objs:
        _orig_bake_uv(objs)


def _bake_all(objs, name):
    return _orig_bake_all(objs, name) if objs else None


def _final(objs, name, imgs):
    if objs:
        _orig_final(objs, name, imgs)


P.canvas_uv, P.canvas_material = _canvas_uv, _canvas_material
P.bake_uv, P.bake_all, P.final_material = _bake_uv, _bake_all, _final


BUILDERS = {
    "VelvetChesterfield": velvet_chesterfield,
    "CamelbackSofa": camelback_sofa,
    "ChaiseLongue": chaise_longue,
    "GothicSettle": gothic_settle,
    "ShellLoveseat": shell_loveseat,
    "CornerSectional": corner_sectional,
    "CoffinCouch": coffin_couch,
    "BatwingSofa": batwing_sofa,
    "ThroneSettee": throne_settee,
    "TuftedBench": tufted_bench,
    "RoundOttoman": round_ottoman,
    "MothMedallionRug": lambda M: rug("MothMedallionRug", 12, 8),
    "WatchingRunner": lambda M: rug("WatchingRunner", 18, 4),
    "ThornRoseRug": lambda M: rug("ThornRoseRug", 9, 9, shape="round"),
    "StarChartRug": lambda M: rug("StarChartRug", 8, 8, shape="octagon"),
    "RavenHearthRug": lambda M: rug("RavenHearthRug", 7, 3.5, shape="half"),
    "BatDamaskRugWorn": lambda M: rug("BatDamaskRugWorn", 9, 6),
    "Doormat": lambda M: rug("Doormat", 4, 2.4, h=0.1, fringe=False, bind=False),
    "DoormatCrest": lambda M: rug("DoormatCrest", 4, 2.4, h=0.1, fringe=False, bind=False),
    "BathMat": lambda M: rug("BathMat", 3.2, 2.0, h=0.08, fringe=False),
    "CarpetDamask": lambda M: rug("CarpetDamask", 8, 8, fringe=False, bind=False, bevel=0.0),
    "CarpetWeb": lambda M: rug("CarpetWeb", 8, 8, fringe=False, bind=False, bevel=0.0),
    "CarpetHarlequin": lambda M: rug("CarpetHarlequin", 8, 8, fringe=False, bind=False, bevel=0.0),
    "CarpetMoth": lambda M: rug("CarpetMoth", 8, 8, fringe=False, bind=False, bevel=0.0),
    "TapestryHeadmaster": lambda M: tapestry("TapestryHeadmaster", M=M),
    "TapestryPriestDemon": lambda M: tapestry("TapestryPriestDemon", M=M),
    "TapestryAngelDemon": lambda M: tapestry("TapestryAngelDemon", M=M),
    "TapestryJudgement": lambda M: tapestry("TapestryJudgement", M=M),
    "TapestryCrest": lambda M: tapestry("TapestryCrest", M=M),
    "TapestryWolfHunt": lambda M: tapestry("TapestryWolfHunt", w=13.0, hgt=13.0 * 1152 / 2048, M=M),
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"WatchingRunner": 1.0, "CornerSectional": 1.0, "TapestryWolfHunt": 1.0})
