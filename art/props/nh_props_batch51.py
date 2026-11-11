"""Props batch 51, the gate kit (2026-11-11), for nh_props.py: new gates, piers, fences and walls for the school's gate, in the
family of IronGate (batch 25) but each its own design: black wrought iron, weathered limestone and soot-dark stone, slate, brass
and gilt, crimson enamel, moss and ivy. Wood only for the removable boards. No blood or gore. Every name and design is invented.

Gates (every leaf is its own piece with its FBX origin on its hinge; all swing OUT to the front, -Y)
  GateGrand        the grand double gate: 13.2 opening between crocketed pinnacle piers, swan-neck leaves with arcading, a rosette
                   medallion and fleur finials, under a scrolled crest overthrow with the school shield and a hanging lantern
  GatePedestrian   a single moon gate for walkers: an arched leaf with a spoked moon wheel and crescent finials, a fixed side screen
  GateWicket       an 8-long stone wall with a small iron door (Door0) under a sunburst grille, gabled portal and hood mould
  GatehouseArch    a crenellated gatehouse arch with machicolations and a RAISED portcullis (Portcullis, slides down 9.0)
  GateLych         a stone-and-iron lychgate: dwarf side walls with benches, iron columns and trusses, a slate roof with cresting
  GateService      the delivery gate: brick piers, wide leaves with riveted iron dado panels, braces and an anti-climb comb
  GateChained      a derelict gate chained and padlocked (Chain is its own piece, so it can be taken off), rusted and bent
  GateBroken       an overgrown gate: one leaf works, the other has dropped off its top hinge and leans in the weeds
  GateMoon         a 16-long wall with a round moon door: two half-disc leaves (a crescent and a full moon) on the front face
  GatePierLantern  a lantern-topped pier for any gate or run
Runs on the 8-stud grid (infills are 8 long and end flush at x = +-4; posts and piers sit on the grid points over the joints)
  Railing8, RailingPost, RailingCorner, RailingEnd, RailingGatePier, StoneWall8, StoneWallPier, BrickWallIron, BrickWallPier,
  HedgeRailing
Sneak gaps (sized for the tallest character crouched: CLEAR_W x CLEAR_H, see SNEAK); boards and loose bars are their own pieces
  SneakBentBars (Board0..), SneakMissingBars (Board0..), SneakWallHole (Board0..), SneakCulvert (Board0..), SneakHedgeGap,
  SneakLooseBars (Bar0..)

Pieces: Main, plus Leaf0 / Leaf1 / Door0 (hinged), Portcullis (slides), Chain, Board<k>, Bar<k> (lift off; origin at the piece's
centre), Glow (candle flames), Glass (lantern panes), Leaves (alpha cards on NH_GardenLeaves). Front faces -Y, Z is up, the origin is
at the bottom centre. The rig is written to art/props/gates_batch51.json. Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import nh_props as P
from nh_props import box, cyl, set_group, material, _finish
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform, _dims, flat
from nh_props_batch8 import _spike, _moss, _crack
from nh_props_batch10 import gilt
import nh_props_batch20 as B20
from nh_props_batch23 import kit, sweep as osweep, ribbon, loopbar, pierce
import nh_props_batch40 as B40
from nh_props_batch40 import Cards, frame, RNG, mk, poly_slab, blob, stone
import window_shapes as WS

DEG = math.pi / 180
PI = math.pi
GRID = 8.0
CAP = 20.48                    # Roblox's 2048-stud mesh cap at the FBX's 100x
ART = os.path.normpath(os.path.join(P.HERE, "..", "textures"))
# the tallest character (7'0", Height v2) crouched, measured 2026-11-11 (E:/NH-Work/props51/logs/00_crouch_measure.md):
# CrouchWalk top of head 5.32, Head + Torso collision 5.16 tall and 2.85 wide; every sneak gap is at least this, clear
CLEAR_H, CLEAR_W = 5.8, 3.4
HINGE_OFF = 0.27               # a leaf's hinge axis stands this far off its pier's shaft (clear of the foot and cornice when open)
# railing standard (Railing8 and every railing-based piece): granite base to 0.5, coping to 0.8, rails, bars every 0.5
PB, PT, PW = 0.5, 0.8, 1.1
R_BOT, R_DOG, R_BAND, R_TOP = 1.1, 2.0, 6.05, 6.7
BAR_TOP = 7.25
BARS = [-3.75 + 0.5 * i for i in range(16)]

RIG = {}           # prop -> {piece: {kind, hinge, axis, angle / slide}}
SNEAK = {}         # prop -> {"clear": [(x0, x1, y0, y1, z0, z1)], "cover": (x0, x1, z0, z1), "kind": "Board" | "Bar"}
GLOW = {}          # prop -> {piece suffix: (r, g, b)}
FLAME = (255, 170, 90)


# ================================================================== materials

def gk51(M):
    """The kit's materials: batch 40's haunted-garden stones and forged iron, batch 23's soot stone, gilt and enamel, plus
    rusted iron, grey weathered boards, red brick and chalk."""
    K = B40.gk2(M)
    K23 = kit(M)
    for k in ("st", "dk", "gilt", "enamel", "hollow", "rust", "glass"):
        K[k] = K23[k]
    K["rusty"] = B40.forged(material("RustIron", "NH_Iron", tint=(0.16, 0.09, 0.06), scale=0.6, rough_add=0.12, wear=0.6, wear_metal=True,
                                     dirt=1.0), 0.8)
    # silver-grey weathered planks (wood grain, no paint); two tones so a boarded gap reads as odd planks nailed up
    K["board"] = material("GateBoard", "NH_DeskWood", tint=(0.4, 0.37, 0.34), scale=0.3, metal=0.0, rough_add=0.25, normal=1.0, wear=0.55,
                          dirt=1.2)
    K["boardd"] = material("GateBoardDark", "NH_DeskWood", tint=(0.24, 0.2, 0.17), scale=0.3, metal=0.0, rough_add=0.22, normal=1.0, wear=0.5,
                           dirt=1.2)
    K["brick"] = B40.streaks(material("GateBrick", os.path.join(ART, "RedBrick", "RedBrick"), tint=(0.62, 0.5, 0.48), scale=0.14, metal=0.0,
                                      wear=0.35, dirt=1.0), 0.35)
    K["castle"] = B40.streaks(B40.mossy(material("GateAshlar", os.path.join(ART, "CastleStone", "CastleStone"), tint=(0.62, 0.62, 0.6),
                                                 scale=0.13, metal=0.0, wear=0.35, dirt=1.0), 0.45, low=1.0), 0.45)
    K["plate"] = material("GatePlateBlack", "NH_PaintedMetal", tint=(0.03, 0.028, 0.032), scale=0.8, rough_mul=0.9, rough_add=0.1, wear=0.35,
                          wear_metal=True, dirt=0.9)        # big sheet-iron faces: black paint worn at the edges (no rust leopard spots)
    K["chalk"] = flat("GateChalk", (0.82, 0.8, 0.74), 0.95, dirt=0.2)
    K["nail"] = flat("NailHead", (0.09, 0.07, 0.06), 0.55, metal=0.8, wear=0.3)
    K["wire"] = flat("TieWire", (0.2, 0.15, 0.11), 0.5, metal=0.9, wear=0.2)
    K["mud"] = B40._soil("TrampledMud", (0.05, 0.036, 0.026), 14.0)
    K["flame"] = flat("GateFlame", (1.0, 0.62, 0.28), 0.5)
    return K


# ================================================================== geometry helpers

def sqbar(name, pts, r, mat, closed=False):
    """A square wrought-iron bar along a polyline. Built here rather than with nh_props.tube(square=True): the profile is
    wound [(-r,-r), (-r,r), (r,r), (r,-r)] (the square-bar audit's fix), so the side faces point outward."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, co in zip(sp.points, pts):
        p.co = (co[0], co[1], co[2], 1)
    sp.use_cyclic_u = closed
    prof = bpy.data.curves.new(name + "_prof", "CURVE")
    ps = prof.splines.new("POLY")
    ps.points.add(3)
    for i, (x, y) in enumerate([(-r, -r), (-r, r), (r, r), (r, -r)]):
        ps.points[i].co = (x, y, 0, 1)
    ps.use_cyclic_u = True
    po = bpy.data.objects.new(name + "_prof", prof)
    bpy.context.collection.objects.link(po)
    cu.bevel_mode = "OBJECT"
    cu.bevel_object = po
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    bpy.data.objects.remove(po)
    return _finish(ob, mat, 0)


def rbar(name, pts, r, mat, seg=6, caps=True):
    """A round bar (scrolls, rings, chains of curves). batch 24's sweep can come out inside out when its frames flip handedness
    (some scrolls did): a closed tube with negative volume has its faces reversed, so it always faces outward."""
    ob = B40.bar(name, pts, r, mat, seg=seg, caps=caps)
    outward(ob)
    return ob


def outward(ob):
    """Reverse every face of a closed mesh whose signed volume is negative (wound inside out)."""
    me = ob.data
    vol = 0.0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for j in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[j].cross(vs[j + 1])) / 6.0
    if vol < 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
    return ob


def vbar(name, x, y, z0, z1, r, mat):
    return sqbar(name, [(x, y, z0), (x, y, z1)], r, mat)


def hrail(name, x0, x1, y, z, r, mat):
    return sqbar(name, [(x0, y, z), (x1, y, z)], r, mat)


def spiral(c, r, turns, a0, sense, n=22, shrink=0.72, plane="XZ"):
    out = []
    for i in range(n + 1):
        t = i / n
        a = a0 + sense * t * turns * 2 * PI
        rr = r * (1 - shrink * t)
        if plane == "XZ":
            out.append((c[0] + rr * math.cos(a), c[1], c[2] + rr * math.sin(a)))
        else:
            out.append((c[0], c[1] + rr * math.cos(a), c[2] + rr * math.sin(a)))
    return out


def cscroll(name, cx, y, z, h, mat, r=0.022, flip=1):
    """A C-scroll standing in the XZ plane between z and z + h: two spirals curling in opposite ways, joined."""
    rr = h / 4
    lo = list(reversed(spiral((cx, y, z + rr), rr, 0.8, PI / 2 * flip, flip, 14)))
    hi = spiral((cx, y, z + h - rr), rr, 0.8, -PI / 2 * flip, -flip, 14)
    return rbar(name, lo + hi[1:], r, mat)


def sscroll(name, p0, p1, mat, r=0.022, curl=0.3):
    """An S-scroll from p0 to p1 in the XZ plane (each end curled into a small volute)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    u = d.normalized()
    n = Vector((-u.z, 0, u.x))
    pts = []
    for i in range(25):
        t = i / 24
        p = p0 + d * t + n * (math.sin(t * 2 * PI) * L * 0.16)
        pts.append(tuple(p))
    a = spiral(tuple(p0 + n * L * curl * 0.5), L * curl * 0.5, 0.75, math.atan2(-n.z, -n.x), 1, 10)
    b = spiral(tuple(p1 - n * L * curl * 0.5), L * curl * 0.5, 0.75, math.atan2(n.z, n.x), 1, 10)
    rbar(name + "a", list(reversed(a)), r * 0.9, mat)
    rbar(name + "b", list(reversed(b)), r * 0.9, mat)
    return rbar(name, pts, r, mat)


def wedge(name, pts2, y0, y1, mat):
    """A flat outline [(x, z)] extruded from y0 to y1 (triangulated, any outline)."""
    return B20.tprism(name, WS.ccw(pts2), (y0 + y1) / 2, abs(y1 - y0), mat)


def crescent(name, cx, y, cz, r, mat, t=0.03, tilt=0.5):
    return wedge(name, WS.crescent(cx, cz, r, tilt=tilt), y - t, y + t, mat)


def rosette(pfx, cx, y, cz, r, mat, petals=8):
    """An eight-petal gilt rosette on a boss, facing both ways."""
    for i in range(petals):
        a = i / petals * 2 * PI
        sphere(f"{pfx}P{i}", r * 0.42, (cx + math.cos(a) * r * 0.55, y, cz + math.sin(a) * r * 0.55), mat, seg=8, rings=4,
               scale=(1.0 if abs(math.cos(a)) > 0.7 else 0.55, 0.35, 1.0 if abs(math.sin(a)) > 0.7 else 0.55))
    sphere(f"{pfx}Boss", r * 0.3, (cx, y, cz), mat, seg=10, rings=5, scale=(1, 0.6, 1))


def fleur(pfx, x, y, z, mat, gm, s=1.0):
    """A fleur finial on a bar top at (x, y, z): a tall spear, two curled side leaves and a gilt collar."""
    _spike(f"{pfx}S", (x, y, z + 0.2 * s), 0.065 * s, 0.4 * s, mat, verts=4, rot=(0, 0, PI / 4))
    for sx in (-1, 1):
        pts = [(x + sx * 0.03 * s, y, z + 0.02 * s), (x + sx * 0.12 * s, y, z + 0.08 * s), (x + sx * 0.17 * s, y, z + 0.18 * s),
               (x + sx * 0.14 * s, y, z + 0.25 * s), (x + sx * 0.09 * s, y, z + 0.22 * s)]
        rbar(f"{pfx}L{sx}", pts, 0.018 * s, mat, seg=5)
    sphere(f"{pfx}C", 0.05 * s, (x, y, z - 0.02 * s), gm, seg=8, rings=4)


def club(pfx, x, y, z, mat, s=1.0):
    """A trefoil club finial: three knobs round a short point."""
    for k, (dx, dz) in enumerate(((-0.06, 0.05), (0.06, 0.05), (0.0, 0.13))):
        sphere(f"{pfx}K{k}", 0.05 * s, (x + dx * s, y, z + dz * s), mat, seg=6, rings=4, scale=(1, 0.8, 1))
    _spike(f"{pfx}S", (x, y, z + 0.27 * s), 0.035 * s, 0.18 * s, mat, verts=4, rot=(0, 0, PI / 4))


def spear(pfx, x, y, z, mat, s=1.0, bent=0.0):
    """A plain spear head (four-sided) with a collar; bent tilts it (a derelict gate)."""
    _spike(f"{pfx}S", (x + bent * 0.15, y, z + 0.16 * s), 0.06 * s, 0.32 * s, mat, verts=4, rot=(0, bent, PI / 4))
    box(f"{pfx}C", (0.1 * s, 0.1 * s, 0.05 * s), (x, y, z - 0.01), mat, bevel=0.01)


def nails(pfx, pts, y, mat, r=0.03):
    for k, (x, z) in enumerate(pts):
        cyl(f"{pfx}{k}", r, 0.02, (x, y - 0.01, z), mat, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)


# ------------------------------------------------------------------ stonework

def course_block(name, cx, cy, w, d, z0, z1, mat, rough=0.0, rng=None, bevel=0.04):
    """One ashlar course of a pier or wall (its joints read from the bevel)."""
    return box(name, (w, d, z1 - z0), (cx, cy, (z0 + z1) / 2), mat, bevel=bevel, segments=1)


def pier(pfx, cx, w, h, K, mat=None, cap=None, base=None, rust=False, cy=0.0, d=None):
    """A stone gate pier w square (d deep) to h: a granite foot, rusticated courses (alternate courses set back), a moulded
    cornice. Returns the cap's top z."""
    d = d or w
    st = mat or K["lime"]
    cm = cap or K["limel"]
    bm = base or K["gran"]
    box(f"{pfx}Foot", (w + 0.36, d + 0.36, 0.55), (cx, cy, 0.275), bm, bevel=0.05, segments=1)
    wedge(f"{pfx}Wash", [(-w / 2 - 0.18, 0.55), (w / 2 + 0.18, 0.55), (w / 2 + 0.02, 0.72), (-w / 2 - 0.02, 0.72)], cy - d / 2 - 0.02,
          cy + d / 2 + 0.02, bm)
    _xform(len(P.PARTS) - 1, Matrix.Translation((cx, 0, 0)))
    z0, zt = 0.72, h - 0.55
    n = max(2, round((zt - z0) / 0.85))
    dz = (zt - z0) / n
    for i in range(n):
        k = 0.0 if i % 2 == 0 else 0.07
        course_block(f"{pfx}C{i}", cx, cy, w - k, d - k, z0 + dz * i, z0 + dz * (i + 1), st)
    box(f"{pfx}Neck", (w + 0.06, d + 0.06, 0.12), (cx, cy, zt + 0.06), cm, bevel=0.03, segments=1)
    box(f"{pfx}Corn", (w + 0.42, d + 0.42, 0.24), (cx, cy, zt + 0.24), cm, bevel=0.06, segments=2)
    box(f"{pfx}Cap", (w + 0.2, d + 0.2, 0.2), (cx, cy, zt + 0.46), cm, bevel=0.05, segments=1)
    return zt + 0.56


def lancet_panel(pfx, cx, cy_face, side, w, z0, z1, mat, gm=None):
    """A sunk lancet panel on a pier face: a raised moulding round a lancet and a small gilt foil in its head."""
    hw = w / 2
    ol = WS.arch(hw, z0, z1 - hw * 1.3, z1, 10, cx=cx)
    loopbar(f"{pfx}Mould", ol, 0.07, cy_face - side * 0.04, cy_face + side * 0.05, mat)
    if gm is not None:
        loopbar(f"{pfx}Foil", WS.foil_outline(cx, z1 - hw * 0.9, hw * 0.45, 3, n=36, a0=PI / 2), 0.03, cy_face - side * 0.04, cy_face + side * 0.03, gm)


def pinnacle(pfx, cx, z, s, K, mat=None, gm=None):
    """A crocketed gothic pinnacle on a pier cap: a gableted base block, a four-sided spire with crockets up its edges, a gilt
    knob. Returns its top z."""
    st = mat or K["limel"]
    box(f"{pfx}Base", (s, s, 0.5 * s), (cx, 0, z + 0.25 * s), st, bevel=0.03, segments=1)
    for k in range(4):
        a = k * PI / 2
        gab = wedge(f"{pfx}Gab{k}", [(-s * 0.42, 0), (s * 0.42, 0), (0, 0.42 * s)], -0.04, 0.04, st)
        _xform(len(P.PARTS) - 1, Matrix.Translation((cx, 0, z + 0.5 * s)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, -s / 2 + 0.04, 0)))
    H = 2.3 * s
    sp = _spike(f"{pfx}Spire", (cx, 0, z + 0.5 * s + H / 2), s * 0.52, H, st, verts=4, rot=(0, 0, PI / 4))
    bpy.context.view_layer.update()
    corners = [sp.matrix_world @ v.co for v in sp.data.vertices if (sp.matrix_world @ v.co).z < z + 0.5 * s + 0.01]
    for e, c in enumerate(corners):
        a = math.atan2(c.y, c.x - cx)
        for j in range(1, 5):
            t = j / 5.5
            rr = s * 0.52 * (1 - t) + 0.035
            sphere(f"{pfx}Cr{e}{j}", 0.07 * s, (cx + math.cos(a) * rr, math.sin(a) * rr, z + 0.5 * s + H * t), st, seg=6, rings=4,
                   scale=(1, 1, 1.5))
    sphere(f"{pfx}Knob", 0.13 * s, (cx, 0, z + 0.5 * s + H + 0.05), gm or K["gilt"], seg=10, rings=6)
    return z + 0.5 * s + H + 0.18 * s


def obelisk(pfx, cx, z, s, K, mat=None, gm=None):
    st = mat or K["limel"]
    box(f"{pfx}Plinth", (s, s, 0.3 * s), (cx, 0, z + 0.15 * s), st, bevel=0.03, segments=1)
    cone(f"{pfx}Shaft", 0.34 * s, 0.2 * s, 1.6 * s, (cx, 0, z + 0.3 * s + 0.8 * s), st, verts=4, rot=(0, 0, PI / 4))
    _spike(f"{pfx}Top", (cx, 0, z + 1.9 * s + 0.12 * s), 0.2 * s, 0.24 * s, st, verts=4, rot=(0, 0, PI / 4))
    sphere(f"{pfx}Orb", 0.1 * s, (cx, 0, z + 2.13 * s), gm or K["gilt"], seg=10, rings=6)
    return z + 2.23 * s


def lantern(pfx, cx, cy, z, s, K, hang=False):
    """A hexagonal iron lantern standing on (or hanging from, hang=True) z: base, six posts, Glass panes, a candle with a Glow
    flame, a six-sided roof and a finial (or a ring)."""
    iron = K["iron"]
    g = P.GROUP
    R = 0.34 * s
    if hang:              # z is the top of the hanging ring
        z = z - 0.2 * s - 1.55 * s
    lathe(f"{pfx}Base", [(0, 0), (R * 0.55, 0), (R * 1.08, 0.12 * s), (R * 1.08, 0.2 * s), (0, 0.2 * s)], iron, seg=6, loc=(cx, cy, z))
    for i in range(6):
        a = i / 6 * 2 * PI
        vbar(f"{pfx}Post{i}", cx + math.cos(a) * R, cy + math.sin(a) * R, z + 0.2 * s, z + 1.0 * s, 0.022 * s, iron)
    cyl(f"{pfx}Candle", 0.07 * s, 0.32 * s, (cx, cy, z + 0.36 * s), K["bone"], verts=10, bevel=0.0)
    set_group("Glass")
    cyl(f"{pfx}Pane", R * 0.97, 0.8 * s, (cx, cy, z + 0.6 * s), K["glass"], verts=6, bevel=0.0, rot=(0, 0, 0))
    set_group("Glow")
    sphere(f"{pfx}Flame", 0.05 * s, (cx, cy, z + 0.6 * s), K["flame"], seg=8, rings=5, scale=(1, 1, 2.0))
    set_group(g)
    lathe(f"{pfx}Roof", [(0, 1.0 * s), (R * 1.2, 1.0 * s), (R * 1.2, 1.06 * s), (R * 0.2, 1.5 * s), (0, 1.55 * s)], iron, seg=6, loc=(cx, cy, z))
    if hang:
        hoop(f"{pfx}Ring", (cx, cy, z + 1.65 * s), 0.1 * s, "Y", iron, thick=0.02 * s)
    else:
        _spike(f"{pfx}Fin", (cx, cy, z + 1.72 * s), 0.05 * s, 0.34 * s, iron, verts=4)
    return z


def ivy_climb(cards, rng, x0, x1, z0, z1, y, side, n, size=0.9):
    """Ivy cards climbing a vertical face at y (facing side = -1 front, +1 back)."""
    nn = Vector((0, side, 0))
    for k in range(n):
        x = rng.uniform(x0, x1)
        s = size * rng.uniform(0.75, 1.25)
        z = max(rng.uniform(z0, z1), s * 0.95)
        t = (nn + Vector((rng.normal() * 0.25, 0, rng.normal() * 0.25))).normalized()
        ax, ay = frame(t, roll=rng.uniform(-0.6, 0.6))
        cards.add((x, y + side * 0.04, z), ax, ay, s, s * 1.2, "ivy", "fill", nrm=nn)


def grass(cards, rng, x0, x1, y0, y1, n, sprite="grass", w=0.9, h=0.9):
    for k in range(n):
        cards.crossed((rng.uniform(x0, x1), rng.uniform(y0, y1), 0.0), w, h, sprite, k=2)


def leaves_done(name, cards):
    for v in cards.V:              # nothing under the ground
        if v.z < 0.01:
            v.z = 0.01
    if cards.build("Leaves"):
        P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"


def rig(prop, piece, kind, hinge, angle=90, axis=(0, 0, 1), slide=(0, 0, 0)):
    RIG.setdefault(prop, {})[f"{prop}_{piece}"] = {"kind": kind, "hinge": [round(v, 4) for v in hinge], "axis": list(axis),
                                                   "slide": list(slide), "angle": angle}


def hinge_pins(pfx, xh, face_x, zs, mat, r=0.055):
    """Gudgeons for a leaf hinged at x = xh: an iron strap from the pier face to the pin at each height, and the pin."""
    for j, z in enumerate(zs):
        box(f"{pfx}Strap{j}", (abs(xh - face_x) + 0.06, 0.1, 0.1), ((xh + face_x) / 2 - 0.03 * (1 if xh > face_x else -1), 0, z), mat, bevel=0.01)
        cyl(f"{pfx}Pin{j}", r, 0.27, (xh, 0, z + 0.135), mat, verts=10, bevel=0.0)


def collars(pfx, xh, zs, mat, r=0.085, sx=-1):
    """A leaf's hinge eyes on the hinge axis at xh (they run into the hinge stile 0.14 in)."""
    for j, z in enumerate(zs):
        cyl(f"{pfx}Eye{j}", r, 0.22, (xh, 0, z + 0.06 + 0.11), mat, verts=12, bevel=0.0)


# ------------------------------------------------------------------ boards (removable)

def boards(prop, rect, yface, K, rng, orient="h", n=None, over=0.45, pried=None, chalk=None, ties=None, w=0.72, t=0.11, base_fn=None,
           layer_fn=None, bar_back=None, ground=0.0):
    """Board<k> pieces covering rect = (x0, x1, z0, z1) on the front: each plank's back sits on the face at y = yface (or
    base_fn(zc) where the face steps), odd planks on the layer in front (layer_fn(k) overrides), overlapping their neighbours
    by 0.08, so with every board on nothing shows through. Each is its own piece with its origin at its centre and carries
    its own nails, or wire ties when ties(k, ctr, size) gives the (x, z, axis) of the bars it is wired to (bar_back: the y of
    the bars' back faces, so the ties loop round bar and plank). pried: an odd (front) plank prised off at one end;
    chalk: the plank with a chalk mark."""
    x0, x1, z0, z1 = rect
    span = (z1 - z0) if orient == "h" else (x1 - x0)
    n = n or max(2, math.ceil((span - 0.08) / (w - 0.08)))
    step = (span - w) / (n - 1)
    out = []
    for k in range(n):
        layer = layer_fn(k) if layer_fn else k % 2
        if orient == "h":
            zc = z0 + w / 2 + step * k
            L = (x1 - x0) + 2 * over + rng.uniform(-0.15, 0.15)
            xc = (x0 + x1) / 2 + rng.uniform(-0.1, 0.1)
            size = (L, t, w)
        else:
            xc = x0 + w / 2 + step * k
            L = (z1 - z0) + 2 * over - (rng.uniform(0.0, 0.12) if over > 0 else 0.0)
            zc = max((z0 + z1) / 2, ground + L / 2)
            size = (w, t, L)
        yb = (base_fn(zc) if base_fn else yface) - layer * t
        yc = yb - t / 2
        ctr = (xc, yc, zc)
        if orient == "h":
            ends = [(xc - L / 2 + 0.2, zc - w * 0.22), (xc - L / 2 + 0.2, zc + w * 0.22), (xc + L / 2 - 0.2, zc - w * 0.22),
                    (xc + L / 2 - 0.2, zc + w * 0.22)]
        else:
            ends = [(xc - w * 0.22, zc - L / 2 + 0.2), (xc + w * 0.22, zc - L / 2 + 0.2), (xc - w * 0.22, zc + L / 2 - 0.2),
                    (xc + w * 0.22, zc + L / 2 - 0.2)]
        set_group(f"Board{k}", hinge=ctr, swing=1)
        s0 = _mark()
        box(f"Plank{k}", size, ctr, K["board"] if k % 3 else K["boardd"], bevel=0.025, segments=1)
        if ties:
            for j, (tx, tz, ax) in enumerate(ties(k, ctr, size)):
                front = yb - t
                bb = bar_back if bar_back is not None else yface + 0.09
                cy, rr = (front + bb) / 2, (bb - front) / 2 + 0.014
                hoop(f"Tie{k}_{j}", (tx, cy, tz), rr, ax, K["wire"], thick=0.011)
        else:
            nails(f"Nail{k}_", ends, yb - t, K["nail"])
        if chalk == k:
            cz, cx = ctr[2] + (0 if orient == "h" else rng.uniform(-0.6, 0.6)), ctr[0] + (rng.uniform(-0.5, 0.5) if orient == "h" else 0)
            for a in (1, -1):
                ribbon(f"Chalk{k}{a}", [(cx - 0.24, cz - 0.22 * a), (cx + 0.24, cz + 0.22 * a)], 0.05, yb - t - 0.004, yb - t + 0.002, K["chalk"])
        if pried == k:
            # the free end prised off the face, toward the front (it can't cut into the planks behind it: it is a front plank)
            if orient == "h":
                piv, ax, ang = Vector((ctr[0] + size[0] / 2 - 0.25, yb, ctr[2])), "Z", 4 * DEG
            else:
                piv, ax, ang = Vector((ctr[0], yb, ctr[2] + size[2] / 2 - 0.25)), "X", -4 * DEG
            _xform(s0, Matrix.Translation(piv) @ Matrix.Rotation(ang, 4, ax) @ Matrix.Translation(-piv))
        out.append(f"Board{k}")
    set_group("Main")
    return out


def ground(s0):
    """Drop (or lift) the parts built since s0 so their lowest point sits on the ground."""
    bpy.context.view_layer.update()
    lo = min((o.matrix_world @ Vector(c)).z for o in P.PARTS[s0:] for c in o.bound_box)
    _xform(s0, Matrix.Translation((0, 0, -lo)))


def piece_names(prop, prefix):
    return [n for n in P.HINGES if n.startswith(prefix)]


# ================================================================== GATES

def leaf_bars(pfx, xa, xb, n, z0, ztop, r, mat, ends=True):
    """n bars evenly between the stiles at xa and xb (not on them), from z0 to ztop(x); returns their x."""
    xs = [xa + (xb - xa) * (i + 1) / (n + 1) for i in range(n)]
    for i, x in enumerate(xs):
        vbar(f"{pfx}{i}", x, 0, z0, ztop(x), r, mat)
    return xs


def gate_grand(M):
    K = gk51(M)
    rng = RNG(5101)
    iron, gl = K["iron"], K["gilt"]
    PX, PW = 8.0, 2.8
    face = PX - PW / 2                   # 6.6: the piers' inner faces
    ztops = []
    for sx in (-1, 1):
        x = sx * PX
        zt = pier(f"Pier{sx}", x, PW, 13.3, K, mat=K["castle"])
        for sy in (-1, 1):
            lancet_panel(f"Pan{sx}{sy}", x, sy * PW / 2, sy, 1.5, 3.2, 10.6, K["limel"], gl)
        ztops.append(pinnacle(f"Pin{sx}", x, zt, 1.3, K))
    box("Sill", (2 * face, 1.6, 0.08), (0, 0, 0.04), K["gran"], bevel=0.02)
    # the crest overthrow: two arcs from the piers' tops, scrolls between them, the shield on top, a lantern under
    zs, za_o, za_i = 12.05, 16.4, 15.3
    arc = lambda zs_, za_, i, n: (-face + 2 * face * i / n, zs_ + (za_ - zs_) * math.sin(PI * i / n) ** 0.8)
    for nm, za, rr in (("ArcOut", za_o, 0.07), ("ArcIn", za_i, 0.06)):
        pts = [arc(zs + (0.7 if nm == "ArcOut" else 0.0), za, i, 30) for i in range(31)]
        sqbar(nm, [(x, 0, z) for x, z in pts], rr, iron)
    for i in range(1, 12):
        t = i / 12
        x = -face + 2 * face * t
        zi = zs + (za_i - zs) * math.sin(PI * t) ** 0.8
        zo = zs + 0.7 + (za_o - zs - 0.7) * math.sin(PI * t) ** 0.8
        if 0.36 < t < 0.64:
            continue
        cscroll(f"OScroll{i}", x, 0, zi + 0.02, zo - zi - 0.04, iron, flip=1 if t < 0.5 else -1)
    # the shield: crimson enamel, gilt rim, a gilt crescent and key
    sh = [(0, 14.85)]
    for k in range(1, 13):
        a = PI / 2 * k / 12
        sh.append((1.1 * math.sin(a), 14.85 + 1.15 * (1 - math.cos(a))))
    sh += [(1.1, 17.25), (-1.1, 17.25)]
    for k in range(12, 0, -1):
        a = PI / 2 * k / 12
        sh.append((-1.1 * math.sin(a), 14.85 + 1.15 * (1 - math.cos(a))))
    wedge("Shield", sh, -0.07, 0.07, K["enamel"])
    loopbar("ShieldRim", sh, 0.1, -0.11, 0.11, gl)
    for sy in (-1, 1):
        crescent(f"ShMoon{sy}", -0.35, sy * 0.09, 16.35, 0.42, gl, t=0.02)
        sqbar(f"ShKey{sy}", [(0.4, sy * 0.09, 15.4), (0.4, sy * 0.09, 16.6)], 0.035, gl)
        hoop(f"ShKeyBow{sy}", (0.4, sy * 0.09, 16.78), 0.17, "Y", gl, thick=0.035)
        box(f"ShKeyBit{sy}", (0.22, 0.05, 0.16), (0.53, sy * 0.09, 15.55), gl, bevel=0.01)
    box("ShieldChief", (2.38, 0.24, 0.22), (0, 0, 17.36), gl, bevel=0.03)
    for k, x in enumerate((-0.8, 0.0, 0.8)):
        _spike(f"Crown{k}", (x, 0, 17.47 + (0.45 if x == 0 else 0.3) / 2), 0.09, 0.45 if x == 0 else 0.3, gl, verts=4, rot=(0, 0, PI / 4))
    fleur("CrestF", 0, 0, 17.95, iron, gl, s=1.8)
    vbar("CrestStem", 0, 0, 17.47, 17.95, 0.045, iron)
    sqbar("LampArm", [(0, 0, 14.87), (0, 0, 14.4)], 0.03, iron)
    lantern("Lamp", 0, 0, 14.4, 0.95, K, hang=True)
    # the two leaves: swan-neck tops rising to the middle, arcading band, a rosette medallion, dog bars, fleur finials
    for k, sx in enumerate((-1, 1)):
        xh, xm = sx * (face - HINGE_OFF), sx * 0.075
        set_group(f"Leaf{k}", hinge=(xh, 0.0, 0.25), swing=sx)
        rig("GateGrand", f"Leaf{k}", "swing", (xh, 0.0, 0.25), 90)
        Wd = abs(xh - xm)
        top = lambda x, xh=xh, Wd=Wd: 10.0 + 1.3 * (0.5 - 0.5 * math.cos(PI * min(1, abs(x - xh) / Wd)))
        xs_ = xh - sx * 0.14           # the hinge stile, 0.14 in from the hinge axis (the eyes are on the axis)
        x0, x1 = sorted((xs_, xm))
        vbar(f"StileH{k}", xs_, 0, 0.3, top(xh) + 0.3, 0.075, iron)
        vbar(f"StileM{k}", xm, 0, 0.3, top(xm) + 0.3, 0.06, iron)
        for nm, z in (("Bot", 0.34), ("Dog", 1.7), ("Mid", 7.35), ("Band", 8.25)):
            hrail(f"Rail{nm}{k}", x0, x1, 0, z, 0.05, iron)
        sqbar(f"TopRail{k}", [(x, 0, top(x)) for x in [x0 + (x1 - x0) * i / 16 for i in range(17)]], 0.055, iron)
        xs = leaf_bars(f"Bar{k}_", xs_, xm, 13, 0.34, lambda x: top(x) + 0.45, 0.04, iron)
        for i, x in enumerate(xs):
            fleur(f"Fl{k}_{i}", x, 0, top(x) + 0.45, iron, gl)
        allx = sorted([xs_] + xs + [xm])
        for i in range(len(allx) - 1):
            xa, xb = allx[i], allx[i + 1]
            xc = (xa + xb) / 2
            vbar(f"Dog{k}_{i}", xc, 0, 0.34, 1.7, 0.03, iron)
            _spike(f"DogT{k}_{i}", (xc, 0, 1.86), 0.04, 0.22, iron, verts=4, rot=(0, 0, PI / 4))
            pts = [(xa, 0, 7.35)] + [(xa + (xb - xa) * j / 8, 0, 7.35 + 0.82 * math.sin(PI * j / 8) ** 0.6) for j in range(1, 8)] + [(xb, 0, 7.35)]
            rbar(f"Arc{k}_{i}", pts, 0.02, iron, seg=5)
            sphere(f"ArcDot{k}_{i}", 0.045, (xc, 0, 8.05), gl, seg=6, rings=4)
        cx = (xh + xm) / 2
        hoop(f"MedRing{k}", (cx, 0, 5.0), 1.05, "Y", iron, thick=0.05)
        hoop(f"MedRing2{k}", (cx, 0, 5.0), 0.82, "Y", gl, thick=0.025)
        rosette(f"Ros{k}", cx, 0, 5.0, 0.62, gl)
        for j in range(4):
            a = PI / 4 + j * PI / 2
            sscroll(f"MedS{k}{j}", (cx + math.cos(a) * 1.08, 0, 5.0 + math.sin(a) * 1.08), (cx + math.cos(a) * 1.85, 0, 5.0 + math.sin(a) * 1.85),
                    iron, r=0.02)
        for i in range(len(allx) - 1):
            xa, xb = allx[i], allx[i + 1]
            cscroll(f"LowS{k}_{i}", (xa + xb) / 2, 0, 2.1, 0.95, iron, flip=1 if i % 2 else -1, r=0.018)
        collars(f"Col{k}", xh, (1.2, 8.6), iron, sx=sx)
        if k == 1:
            box("DropBolt", (0.08, 0.12, 1.2), (xm + 0.2, 0.12, 0.9), iron, bevel=0.01)
        set_group("Main")
        hinge_pins(f"Gud{k}", xh, sx * face, (1.2, 8.6), iron)
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * PX - 1.3, sx * PX + 1.3, 0.6, 5.5 + rng.uniform(0, 3), -PW / 2 - 0.02, -1, 26)
        ivy_climb(cards, rng, sx * PX - 1.2, sx * PX + 1.2, 0.6, 4.0, PW / 2 + 0.02, 1, 14)
        grass(cards, rng, sx * PX - 1.6, sx * PX + 1.6, -2.0, -1.6, 7)
    leaves_done("GateGrand", cards)
    _moss("Moss", [(sx * PX + rng.uniform(-1.4, 1.4), -1.62, 0.6) for sx in (-1, 1) for _ in range(5)], K["moss"], random.Random(5), size=0.1)
    return _dims()


def gate_pedestrian(M):
    K = gk51(M)
    rng = RNG(5102)
    iron, gl = K["iron"], K["gilt"]
    PX, PW = 4.0, 1.9
    face = PX - PW / 2           # 3.05
    for sx in (-1, 1):
        zt = pier(f"Pier{sx}", sx * PX, PW, 7.6, K, mat=K["lime"])
        obelisk(f"Ob{sx}", sx * PX, zt, 1.05, K)
        for sy in (-1, 1):
            loopbar(f"Ring{sx}{sy}", WS.circle(sx * PX, 4.9, 0.42, 28), 0.08, sy * PW / 2, sy * (PW / 2 + 0.05), K["limel"])
            crescent(f"PMoon{sx}{sy}", sx * PX, sy * (PW / 2 + 0.02), 4.9, 0.3, K["limel"], t=0.025)
    box("Sill", (2 * face, 1.2, 0.08), (0, 0, 0.04), K["gran"], bevel=0.02)
    xl = 1.0                     # the latch post between the leaf and the fixed screen
    vbar("LatchPost", xl, 0, 0.08, 6.62, 0.06, iron)
    crescent("LatchMoon", xl, 0, 6.82, 0.26, gl, t=0.03)
    box("LatchFoot", (0.2, 0.3, 0.08), (xl, 0, 0.12), iron, bevel=0.01)
    # the fixed screen between the latch post and the right pier
    x0, x1 = xl + 0.06, face - 0.02
    hrail("ScrBot", x0, x1, 0, 0.35, 0.045, iron)
    hrail("ScrMid", x0, x1, 0, 1.55, 0.04, iron)
    hrail("ScrTop", x0, x1, 0, 5.3, 0.045, iron)
    for i, x in enumerate([x0 + (x1 - x0) * (j + 0.5) / 4 for j in range(4)]):
        vbar(f"ScrBar{i}", x, 0, 0.35, 5.6, 0.032, iron)
        crescent(f"ScrMoon{i}", x, 0, 5.82, 0.2, iron, t=0.025)
        cscroll(f"ScrS{i}", x + (x1 - x0) / 8, 0, 0.42, 1.06, iron, r=0.017)
    for j in range(2):
        cscroll(f"ScrHi{j}", x0 + (x1 - x0) * (0.25 + 0.5 * j), 0, 4.45, 0.8, iron, flip=-1, r=0.018)
    box("ScrPin", (0.16, 0.1, 0.1), (face + 0.03, 0, 2.5), iron, bevel=0.01)
    # the leaf: hinged on the left pier, a round-arched top, a spoked moon wheel with a gilt crescent, crescent finials
    xh, xm = -(face - HINGE_OFF), xl - 0.14
    xs_ = xh + 0.14
    set_group("Leaf0", hinge=(xh, 0.0, 0.25), swing=-1)
    rig("GatePedestrian", "Leaf0", "swing", (xh, 0.0, 0.25), 90)
    Wd = xm - xh
    top = lambda x: 6.0 + 0.75 * math.sin(PI * min(1.0, max(0.0, (x - xh) / Wd)))
    vbar("StileH", xs_, 0, 0.3, 6.35, 0.065, iron)
    vbar("StileM", xm, 0, 0.3, 6.35, 0.055, iron)
    hrail("Bot", xs_, xm, 0, 0.34, 0.05, iron)
    hrail("Low", xs_, xm, 0, 1.75, 0.045, iron)
    sqbar("Top", [(x, 0, top(x)) for x in [xs_ + (xm - xs_) * i / 14 for i in range(15)]], 0.05, iron)
    xs = leaf_bars("Bar", xs_, xm, 7, 0.34, lambda x: top(x) + 0.35, 0.034, iron)
    for i, x in enumerate(xs):
        crescent(f"Moon{i}", x, 0, top(x) + 0.55, 0.2, iron, t=0.025)
    allx = [xs_] + xs + [xm]
    for i in range(len(allx) - 1):
        xa, xb = allx[i], allx[i + 1]
        sqbar(f"X{i}a", [(xa, 0, 0.36), (xb, 0, 1.73)], 0.02, iron)
        sqbar(f"X{i}b", [(xb, 0, 0.36), (xa, 0, 1.73)], 0.02, iron)
    cx = (xh + xm) / 2
    hoop("Wheel", (cx, 0, 4.1), 1.3, "Y", iron, thick=0.055)
    hoop("WheelIn", (cx, 0, 4.1), 0.42, "Y", iron, thick=0.04)
    for j in range(12):
        a = j / 12 * 2 * PI
        sqbar(f"Spoke{j}", [(cx + math.cos(a) * 0.44, 0, 4.1 + math.sin(a) * 0.44), (cx + math.cos(a) * 1.27, 0, 4.1 + math.sin(a) * 1.27)], 0.018, iron)
        sphere(f"Stud{j}", 0.04, (cx + math.cos(a) * 1.3, 0, 4.1 + math.sin(a) * 1.3), gl, seg=6, rings=4)
    crescent("WheelMoon", cx, 0, 4.1, 0.36, gl, t=0.04)
    hoop("Pull", (xm - 0.62, -0.08, 3.3), 0.12, "Y", K["brass"], thick=0.02)
    box("Lock", (0.3, 0.12, 0.42), (xm - 0.62, 0, 3.75), K["brass"], bevel=0.02)
    collars("Col", xh, (1.0, 5.4), iron, sx=-1)
    set_group("Main")
    hinge_pins("Gud", xh, -face, (1.0, 5.4), iron)
    # a lamp on the right pier's front face: a scrolled bracket and a hanging lantern
    yb = -PW / 2
    box("LampPlate", (0.4, 0.06, 0.6), (PX, yb - 0.03, 6.3), iron, bevel=0.01)
    sqbar("LampArm", [(PX, yb - 0.05, 6.45), (PX, yb - 0.95, 6.45)], 0.035, iron)
    cscroll("LampS", PX, yb - 0.5, 5.75, 0.65, iron)
    _xform(len(P.PARTS) - 1, Matrix.Translation((PX, yb - 0.5, 5.75)) @ Matrix.Rotation(PI / 2, 4, "Z") @ Matrix.Translation((-PX, -(yb - 0.5), -5.75)))
    lantern("Lamp", PX, yb - 0.9, 6.45 + 0.047, 0.75, K, hang=True)
    GLOW["GatePedestrian"] = {"Glow": FLAME}
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * PX - 0.9, sx * PX + 0.9, 0.6, 3.5, -PW / 2 - 0.02, -1, 10)
        grass(cards, rng, sx * PX - 1.0, sx * PX + 1.0, -1.5, -1.25, 5)
    leaves_done("GatePedestrian", cards)
    return _dims()


# ------------------------------------------------------------------ stone wall (shared by StoneWall8, the wicket and the hole)

WALL_T, WALL_H, WALL_TOP = 1.6, 7.4, 8.05


def stone_wall(pfx, x0, x1, K, holes=None, cope=True, rng=None, band=True):
    """A stretch of ashlar wall from x0 to x1, 1.6 thick: a battered granite plinth, ashlar to 7.4, a string course, a
    saddleback coping with drips to 8.05. holes: outlines [(x, z)] pierced through (doors, a crumbled hole)."""
    L = x1 - x0
    cx = (x0 + x1) / 2
    pl = B20.tprism(f"{pfx}Plinth", [(-WALL_T / 2 - 0.16, 0), (WALL_T / 2 + 0.16, 0), (WALL_T / 2 + 0.16, 0.45), (WALL_T / 2, 0.62),
                                     (-WALL_T / 2, 0.62), (-WALL_T / 2 - 0.16, 0.45)], cx, L, K["gran"], plane="YZ")
    body = box(f"{pfx}Body", (L, WALL_T, WALL_H - 0.62), (cx, 0, 0.62 + (WALL_H - 0.62) / 2), K["castle"], bevel=0.0)
    band = box(f"{pfx}String", (L, WALL_T + 0.16, 0.22), (cx, 0, 4.2), K["limel"], bevel=0.03, segments=1) if band else None
    if holes:
        for o in [o for o in (pl, body, band) if o is not None]:
            pierce(o, holes, y0=-3.0, y1=3.0)
    if cope:
        c = B20.tprism(f"{pfx}Cope", [(-WALL_T / 2 - 0.18, WALL_H), (WALL_T / 2 + 0.18, WALL_H), (WALL_T / 2 + 0.18, WALL_H + 0.2),
                                      (0, WALL_TOP), (-WALL_T / 2 - 0.18, WALL_H + 0.2)], cx, L, K["limel"], plane="YZ")
        for sy in (-1, 1):
            box(f"{pfx}Drip{sy}", (L, 0.05, 0.05), (cx, sy * (WALL_T / 2 + 0.12), WALL_H - 0.02), K["limel"], bevel=0.0)


def stone_wall8(M):
    K = gk51(M)
    rng = RNG(5111)
    stone_wall("W", -4.0, 4.0, K)
    cards = Cards(rng)
    for k in range(16):
        x = rng.uniform(1.4, 3.9)
        side = -1 if k % 2 else 1
        n = Vector((0, side, 0.12)).normalized()
        ax, ay = frame(n)
        cards.add((x, side * (WALL_T / 2 + 0.22), WALL_TOP - 0.1), ax, ay, 1.2, rng.uniform(1.6, 3.2), "ivy", "top", segs=2, bend=n * 0.15, nrm=n)
    grass(cards, rng, -3.9, 3.9, -1.25, -1.05, 8)
    grass(cards, rng, -3.9, 3.9, 1.05, 1.25, 6)
    leaves_done("StoneWall8", cards)
    _moss("Moss", [(rng.uniform(-3.8, 3.8), rng.uniform(-0.3, 0.3), WALL_TOP - 0.25) for _ in range(7)], K["moss"], random.Random(8), size=0.12)
    _crack("Crack", (-2.2, -WALL_T / 2 - 0.004, 5.6), (0.3, 0, -1), (1, 0, 0), 1.2, random.Random(3), K["hollow"])
    return _dims()


def gate_wicket(M):
    K = gk51(M)
    rng = RNG(5103)
    iron, gl = K["iron"], K["gilt"]
    DW, DH, ZA = 1.9, 6.6, 8.0              # door half width, door head (clear 6.5 for a 7'0" standing), arch apex
    PH, PD, PX = 8.2, 1.0, 2.9              # the gabled portal: its eaves, half depth, half width (apex 10.0)
    op = WS.arch(DW, -0.5, DH, ZA, 14)
    stone_wall("WL", -4.0, -PX, K)
    stone_wall("WR", PX, 4.0, K)
    # the gabled portal (a block proud of both wall faces): ashlar, the door arch through it, a moulded surround, a gable
    # coping with a finial, a carved quatrefoil
    pb = wedge("Portal", [(-PX, 0.62), (PX, 0.62), (PX, PH), (0, 10.0), (-PX, PH)], -PD, PD, K["castle"])
    pp = B20.tprism("PortalPlinth", [(-PD - 0.16, 0), (PD + 0.16, 0), (PD + 0.16, 0.45), (PD, 0.62), (-PD, 0.62), (-PD - 0.16, 0.45)], 0, 2 * PX,
                    K["gran"], plane="YZ")
    pierce(pb, [op], y0=-3.0, y1=3.0)
    pierce(pp, [op], y0=-3.0, y1=3.0)
    gb = [(-PX - 0.18, PH - 0.12), (0, 10.12), (PX + 0.18, PH - 0.12)]
    ribbon("GableCope", gb, 0.34, -PD - 0.14, PD + 0.14, K["limel"])
    _spike("GFin", (0, 0, 10.55), 0.2, 0.75, K["limel"], verts=4, rot=(0, 0, PI / 4))
    for sy in (-1, 1):
        yf = sy * PD
        osweep(f"Surround{sy}", WS.ccw(WS.arch(DW, 0.62, DH, ZA, 14)), [(0.0, yf - sy * 0.04), (0.5, yf - sy * 0.04), (0.5, yf + sy * 0.1),
                                                                          (0.0, yf + sy * 0.1)], K["limel"], rng=(1, 0), drop_back=False)
        loopbar(f"GFoil{sy}", WS.foil_outline(0, 9.05, 0.36, 4, n=40, a0=PI / 4), 0.07, yf - sy * 0.04, yf + sy * 0.06, K["limel"])
        pierce(box(f"PortBand{sy}", (2 * PX + 0.1, 0.12, 0.22), (0, yf + sy * 0.04, 4.2), K["limel"], bevel=0.03, segments=1),
               [WS.offset(WS.ccw(op), 0.5)], y0=-3.0, y1=3.0)
    # the tympanum grille under the arch head: a sunburst of bars round a gilt half-sun
    yg = 0.0
    hrail("TymBar", -DW, DW, yg, DH + 0.03, 0.05, iron)
    sun = (0, yg, DH + 0.05)
    for j in range(9):
        a = PI * (j + 0.5) / 9
        L = 3.0
        ex = Vector((math.cos(a), 0, math.sin(a)))
        pts = [(sun[0] + ex.x * 0.45, yg, sun[2] + ex.z * 0.45), (sun[0] + ex.x * L, yg, sun[2] + ex.z * L)]
        # clip the ray at the arch's intrados
        for t in [i / 40 for i in range(41)]:
            p = Vector(pts[0]).lerp(Vector(pts[1]), t)
            if not WS.inside((p.x, p.z), WS.offset(WS.ccw(op), -0.02)):
                pts[1] = tuple(Vector(pts[0]).lerp(Vector(pts[1]), max(0, t - 0.03)))
                break
        sqbar(f"Ray{j}", pts, 0.025, iron)
    lathe("Sun", [(0, -0.04), (0.42, -0.04), (0.42, 0.04), (0, 0.04)], gl, seg=20, loc=(0, 0, 0))
    _xform(len(P.PARTS) - 1, Matrix.Translation(sun) @ Matrix.Rotation(PI / 2, 4, "X"))
    # a stop round the door opening behind the door (no light round its edges)
    ribbon("Stop", [(-DW + 0.05, 0.0), (-DW + 0.05, DH - 0.05), (DW - 0.05, DH - 0.05), (DW - 0.05, 0.0)], 0.3, -0.52, -0.4, K["dk"])
    box("Threshold", (2 * DW + 0.1, 2 * PD + 0.1, 0.1), (0, 0, 0.05), K["gran"], bevel=0.02)
    # the door: an iron plate on a frame, studs, strap hinges, a speaking grille, a ring pull and a keyhole
    xh, yd, t = -DW + 0.15, -0.64, 0.14
    pl0, pl1 = xh + 0.08, DW - 0.15          # the plate starts 0.08 off the hinge axis (the strap hinges carry it)
    Wd = pl1 - pl0
    set_group("Door0", hinge=(xh, yd, 0.12), swing=-1)
    rig("GateWicket", "Door0", "swing", (xh, yd, 0.12), 90)
    door = box("Plate", (Wd, t, DH - 0.14), ((pl0 + pl1) / 2, yd, 0.12 + (DH - 0.14) / 2), K["enamel"], bevel=0.015)
    gx, gz = (pl0 + pl1) / 2, 4.55
    pierce(door, [WS.rect(0.34, gz - 0.24, gz + 0.24, cx=gx)], y0=yd - 1, y1=yd + 1)
    for j in range(3):
        vbar(f"GrBar{j}", gx - 0.2 + 0.2 * j, yd, gz - 0.26, gz + 0.26, 0.025, iron)
    loopbar("GrFrame", WS.rect(0.34, gz - 0.24, gz + 0.24, cx=gx), 0.08, yd - t / 2 - 0.03, yd - t / 2, K["brass"])
    for sy in (-1, 1):
        y = yd + sy * t / 2
        loopbar(f"Edge{sy}", WS.rect(Wd / 2 - 0.08, 0.2, DH - 0.1, cx=gx), 0.07, y, y + sy * 0.03, iron)
        for j, z in enumerate((1.0, 3.2, 5.3)):
            box(f"Strap{sy}{j}", (2.4, 0.03, 0.16), (xh + 1.2, y + sy * 0.015, z), iron, bevel=0.008)
            box(f"StrapEnd{sy}{j}", (0.12, 0.03, 0.12), (xh + 2.45, y + sy * 0.015, z), iron, bevel=0.01, rot=(0, PI / 4, 0))
        for row in range(6):
            for col in range(4):
                z = 0.55 + row * 0.98
                if abs(z - gz) < 0.4 or any(abs(z - zz) < 0.15 for zz in (1.0, 3.2, 5.3)):
                    continue
                sphere(f"Stud{sy}{row}{col}", 0.04, (pl0 + 0.4 + col * (Wd - 0.8) / 3, y + sy * 0.01, z), iron, seg=6, rings=3, scale=(1, 0.6, 1))
        cyl(f"Rose{sy}", 0.11, 0.03, (pl1 - 0.4, y + sy * 0.015, 3.3), K["brass"], rot=(PI / 2, 0, 0), verts=14, bevel=0.005)
        hoop(f"Ring{sy}", (pl1 - 0.4, y + sy * 0.06, 3.12), 0.16, "Y", K["brass"], thick=0.022)
    box("Keyhole", (0.14, 0.02, 0.24), (pl1 - 0.4, yd - t / 2 - 0.012, 2.8), K["brass"], bevel=0.01)
    for j, z in enumerate((1.0, 5.3)):
        cyl(f"Knuckle{j}", 0.06, 0.5, (xh, yd, z), iron, verts=10, bevel=0.0)
    set_group("Main")
    for j, z in enumerate((1.0, 5.3)):
        cyl(f"Pintle{j}", 0.03, 0.62, (xh, yd, z), iron, verts=8, bevel=0.0)
        box(f"PintleB{j}", (0.18, 0.08, 0.08), (-DW + 0.09, yd, z - 0.29), iron, bevel=0.005)
    cards = Cards(rng)
    ivy_climb(cards, rng, 3.0, 3.9, 0.8, 6.8, -WALL_T / 2 - 0.02, -1, 14)
    ivy_climb(cards, rng, 2.0, 2.8, 0.8, 4.0, -PD - 0.02, -1, 6)
    ivy_climb(cards, rng, -3.9, -3.0, 0.8, 3.0, -WALL_T / 2 - 0.02, -1, 5)
    grass(cards, rng, -3.9, 3.9, -1.25, -1.05, 7)
    leaves_done("GateWicket", cards)
    return _dims()


# ================================================================== RUNS: the railing

def railing(pfx, K, x0=-4.0, x1=4.0, gap=None, keep_bars=None, plinth=True, bars=None, mat=None, finial="club", rings=True,
            rails=None, cope_gap=None, bar_bottom=None):
    """The Railing8 standard from x0 to x1: a granite base to 0.5, a limestone coping to 0.8, bars every 0.5 (r 0.035) from the
    coping into the top rail at 6.6, dog bars between the bottom (1.1) and dog (2.0) rails, a band of rings between 5.95 and
    6.6, club finials to 7.5. gap = (xa, xb): no lower rails, rings or dog bars between xa and xb (sneak gaps); bars: which bar
    x positions to build (default BARS within x0..x1); cope_gap: (xa, xb) where the coping is missing."""
    iron = mat or K["iron"]
    xs = [x for x in (bars if bars is not None else BARS) if x0 - 1e-6 <= x <= x1 + 1e-6]
    if plinth:
        box(f"{pfx}Base", (x1 - x0, PW + 0.12, PB), ((x0 + x1) / 2, 0, PB / 2), K["gran"], bevel=0.03, segments=1)
        segs = [(x0, x1)] if not cope_gap else [(x0, cope_gap[0]), (cope_gap[1], x1)]
        for k, (a, b) in enumerate(segs):
            if b - a > 0.05:
                B20.tprism(f"{pfx}Cope{k}", [(-PW / 2, PB), (PW / 2, PB), (PW / 2, PT - 0.08), (0.2, PT), (-0.2, PT), (-PW / 2, PT - 0.08)],
                           (a + b) / 2, b - a, K["limel"], plane="YZ")
    def ingap(x):
        return gap is not None and gap[0] < x < gap[1]
    rails = rails or (("Bot", R_BOT, 0.04), ("Dog", R_DOG, 0.035), ("Band", R_BAND, 0.035))
    for nm, z, r in rails:
        if gap is None:
            hrail(f"{pfx}{nm}", x0, x1, 0, z, r, iron)
        else:
            if gap[0] > x0:
                hrail(f"{pfx}{nm}A", x0, gap[0], 0, z, r, iron)
            if gap[1] < x1:
                hrail(f"{pfx}{nm}B", gap[1], x1, 0, z, r, iron)
    hrail(f"{pfx}Top", x0, x1, 0, R_TOP, 0.05, iron)
    built = []
    for i, x in enumerate(xs):
        if keep_bars is not None and not keep_bars(x):
            continue
        zb = bar_bottom(x) if bar_bottom else None
        vbar(f"{pfx}Bar{i}", x, 0, PT - 0.02 if zb is None else zb, BAR_TOP, 0.035, iron if zb is None else K["rusty"])
        if zb is None:
            box(f"{pfx}Sock{i}", (0.13, 0.13, 0.06), (x, 0, PT + 0.02), K["lead"] if "lead" in K else iron, bevel=0.01)
        if finial == "club":
            club(f"{pfx}F{i}", x, 0, BAR_TOP, iron)
        elif finial == "spear":
            spear(f"{pfx}F{i}", x, 0, BAR_TOP, iron)
        built.append(x)
    for i, x in enumerate(xs):
        xc = x + 0.25
        if xc > x1 or ingap(xc) or ingap(x) or ingap(x + 0.5):
            continue
        vbar(f"{pfx}Dog{i}", xc, 0, R_BOT, R_DOG, 0.025, iron)
        if rings:
            hoop(f"{pfx}Ring{i}", (xc, 0, (R_BAND + R_TOP) / 2), 0.197, "Y", iron, thick=0.018)
    return built


def railing8(M):
    K = gk51(M)
    rng = RNG(5121)
    railing("R", K)
    cards = Cards(rng)
    grass(cards, rng, -3.9, 3.9, -0.85, -0.65, 7)
    grass(cards, rng, -3.9, 3.9, 0.65, 0.85, 5)
    leaves_done("Railing8", cards)
    _moss("Moss", [(rng.uniform(-3.8, 3.8), rng.uniform(-0.35, 0.35), PT - 0.03) for _ in range(5)], K["moss"], random.Random(4), size=0.07)
    return _dims()


def rail_post(pfx, K, w=1.5, h=8.4, top="pinnacle", octa=False):
    """A stone railing post on its grid point (the railings' ends tuck into it), w square."""
    box(f"{pfx}Foot", (w + 0.3, w + 0.3, PB), (0, 0, PB / 2), K["gran"], bevel=0.04, segments=1)
    box(f"{pfx}Wash", (w + 0.14, w + 0.14, PT - PB), (0, 0, (PB + PT) / 2), K["limel"], bevel=0.05, segments=1)
    zt = h - 0.5
    if octa:
        cyl(f"{pfx}Shaft", w * 0.56, zt - PT, (0, 0, (PT + zt) / 2), K["lime"], verts=8, bevel=0.03, rot=(0, 0, PI / 8))
        for k in range(4):
            cyl(f"{pfx}Band{k}", w * 0.6, 0.16, (0, 0, PT + 1.4 + k * 1.6), K["limel"], verts=8, bevel=0.02, rot=(0, 0, PI / 8))
    else:
        n = round((zt - PT) / 0.8)
        dz = (zt - PT) / n
        for i in range(n):
            k = 0.0 if i % 2 == 0 else 0.06
            course_block(f"{pfx}C{i}", 0, 0, w - k, w - k, PT + dz * i, PT + dz * (i + 1), K["lime"])
    box(f"{pfx}Corn", (w + 0.3, w + 0.3, 0.22), (0, 0, zt + 0.11), K["limel"], bevel=0.05, segments=2)
    box(f"{pfx}Cap", (w + 0.12, w + 0.12, 0.2), (0, 0, zt + 0.32), K["limel"], bevel=0.04, segments=1)
    z = zt + 0.42
    if top == "pinnacle":
        return pinnacle(f"{pfx}Pin", 0, z, w * 0.62, K)
    if top == "obelisk":
        return obelisk(f"{pfx}Ob", 0, z, w * 0.75, K)
    return z


def railing_post(M):
    K = gk51(M)
    rail_post("P", K, 1.5, 8.4, "pinnacle")
    for sy in (-1, 1):
        lancet_panel(f"Pan{sy}", 0, sy * 0.75, sy, 0.7, 2.0, 6.6, K["limel"])
    return _dims()


def railing_corner(M):
    K = gk51(M)
    rail_post("P", K, 1.8, 8.9, "obelisk", octa=True)
    return _dims()


def railing_end(M):
    """The end post of a run (the railing goes off to +X): a post and a great iron scroll stay on its free side."""
    K = gk51(M)
    iron = K["iron"]
    rail_post("P", K, 1.5, 8.4, "pinnacle")
    box("StubBase", (1.3, PW + 0.12, PB), (-1.4, 0, PB / 2), K["gran"], bevel=0.03, segments=1)
    B20.tprism("StubCope", [(-PW / 2, PB), (PW / 2, PB), (PW / 2, PT - 0.08), (0.2, PT), (-0.2, PT), (-PW / 2, PT - 0.08)], -1.4, 1.3, K["limel"],
               plane="YZ")
    # the stay: a big S-curve from high on the post down to the stub, scrolled at both ends
    pts = [(-0.74, 0, 6.3), (-1.0, 0, 6.05), (-1.3, 0, 5.5), (-1.55, 0, 4.6), (-1.7, 0, 3.4), (-1.75, 0, 2.0), (-1.75, 0, PT - 0.02)]
    sqbar("Stay", pts, 0.045, iron)

    def sx_at(z):
        for a, b in zip(pts, pts[1:]):
            if b[2] <= z <= a[2]:
                t = (z - b[2]) / (a[2] - b[2])
                return b[0] + (a[0] - b[0]) * t
        return pts[-1][0]
    zs = (1.2, 2.5, 3.8, 5.0)
    for k, z in enumerate(zs):
        hrail(f"StayRail{k}", sx_at(z), -0.72, 0, z, 0.03, iron)
    for k in range(len(zs) - 1):
        za, zb = zs[k] + 0.04, zs[k + 1] - 0.04
        xa = max(sx_at(za), sx_at(zb)) + 0.06
        cscroll(f"StayS{k}", (xa - 0.75) / 2 + 0.0, 0, za, zb - za, iron, flip=1 if k % 2 else -1, r=0.02)
    club("StayKnob", -1.75, 0, 2.0, iron) if False else None
    return _dims()


def railing_gate_pier(M):
    """A taller gate pier for a run: rusticated, a lancet panel with a gilt foil, an obelisk; gudgeon pins on its -X face to hang a
    leaf (the railing tucks into its +X face)."""
    K = gk51(M)
    iron = K["iron"]
    zt = pier("P", 0, 2.2, 9.6, K, mat=K["castle"])
    for sy in (-1, 1):
        lancet_panel(f"Pan{sy}", 0, sy * 1.1, sy, 1.1, 2.4, 8.0, K["limel"], K["gilt"])
    obelisk("Ob", 0, zt, 1.25, K)
    for j, z in enumerate((1.2, 5.6)):
        box(f"GudStrap{j}", (0.35, 0.1, 0.1), (-1.1 - 0.12, 0, z), iron, bevel=0.01)
        cyl(f"GudPin{j}", 0.055, 0.36, (-1.1 - 0.25, 0, z + 0.18), iron, verts=10, bevel=0.0)
    return _dims()


# ------------------------------------------------------------------ a plain leaf (the chained and broken gates)

def plain_leaf(pfx, xh, xm, sx, K, mat, top=6.4, spear_top=7.1, n=6, bent=None, missing=(), broken=(), rails=(0.35, 1.55, 3.35)):
    """A plain wrought-iron leaf from its hinge axis xh to its meeting stile xm: hinge eyes, stiles, rails, n bars with spear
    heads (bent: {i: tilt} bends a head over, missing: heads gone, broken: bars snapped off short), dog bars, a band of
    C-scrolls under the top rail."""
    xs_ = xh - sx * 0.14
    x0, x1 = sorted((xs_, xm))
    vbar(f"{pfx}StileH", xs_, 0, 0.3, top + 0.25, 0.06, mat)
    vbar(f"{pfx}StileM", xm, 0, 0.3, top + 0.25, 0.05, mat)
    for j, z in enumerate(rails + (top - 0.75, top)):
        hrail(f"{pfx}Rail{j}", x0, x1, 0, z, 0.045 if z in (rails[0], top) else 0.038, mat)
    xs = [xs_ + (xm - xs_) * (i + 1) / (n + 1) for i in range(n)]
    bent = bent or {}
    for i, x in enumerate(xs):
        if i in broken:
            pts = [(x, 0, rails[0]), (x, 0, top - 0.75), (x + 0.04, 0, top - 0.55), (x + 0.14, -0.05, top - 0.42)]
            sqbar(f"{pfx}Bar{i}", pts, 0.03, mat)
            continue
        vbar(f"{pfx}Bar{i}", x, 0, rails[0], spear_top, 0.03, mat)
        if i not in missing:
            spear(f"{pfx}Sp{i}", x, 0, spear_top, mat, bent=bent.get(i, 0.0))
    allx = sorted([xs_] + xs + [xm])
    for i in range(len(allx) - 1):
        xa, xb = allx[i], allx[i + 1]
        vbar(f"{pfx}Dog{i}", (xa + xb) / 2, 0, rails[0], rails[1], 0.024, mat)
        cscroll(f"{pfx}S{i}", (xa + xb) / 2, 0, top - 0.72, 0.68, mat, flip=1 if i % 2 else -1, r=0.017)
    collars(f"{pfx}Col", xh, (1.0, 5.2), mat, sx=sx)
    return xs


# ------------------------------------------------------------------ chain links

def chain(pfx, path, mat, a=0.07, b=0.036, r=0.013, closed=False):
    """Interlocking oval links along a polyline (alternate links turned a quarter turn about the path)."""
    pts = [Vector(p) for p in path]
    segs = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    L = sum((q - p).length for p, q in segs)
    step = a * 1.45
    n = max(2, int(L / step))
    out = []
    for k in range(n):
        d = (k + 0.5) * L / n
        for p, q in segs:
            l = (q - p).length
            if d <= l:
                c = p + (q - p) * (d / l)
                tng = (q - p).normalized()
                break
            d -= l
        up = Vector((0, 0, 1)) if abs(tng.z) < 0.9 else Vector((1, 0, 0))
        side = tng.cross(up).normalized()
        nrm = side.cross(tng).normalized()
        w = nrm if k % 2 else side
        loop = [tuple(c + tng * (math.cos(t) * a) + w * (math.sin(t) * b)) for t in [2 * PI * i / 14 for i in range(15)]]
        out.append(rbar(f"{pfx}{k}", loop, r, mat, seg=5, caps=False))
    return out


# ================================================================== more gates

def gatehouse_arch(M):
    K = gk51(M)
    rng = RNG(5104)
    iron, st, stl = K["iron"], K["castle"], K["limel"]
    HW, ZS, ZA = 4.0, 7.6, 11.6
    X, Y, TOP = 8.0, 4.0, 17.4
    op = WS.arch(HW, -0.5, ZS, ZA, 16)
    YS0, YS1 = -2.7, -2.3                    # the portcullis slot
    front = box("Front", (2 * X, YS0 + Y, TOP), (0, (-Y + YS0) / 2, TOP / 2), st, bevel=0.0)
    slot = box("SlotWall", (2 * X, YS1 - YS0, TOP), (0, (YS0 + YS1) / 2, TOP / 2), st, bevel=0.0)
    back = box("Back", (2 * X, Y - YS1, TOP), (0, (YS1 + Y) / 2, TOP / 2), st, bevel=0.0)
    plinth = box("Plinth", (2 * X + 0.3, 2 * Y + 0.3, 0.9), (0, 0, 0.45), K["gran"], bevel=0.04, segments=1)
    for o in (front, back, plinth):
        pierce(o, [op], y0=-6, y1=6)
    pierce(slot, [WS.rect(HW + 0.35, -0.5, TOP - 0.15)], y0=-6, y1=6)
    box("Floor", (2 * HW, 2 * Y + 0.3, 0.06), (0, 0, 0.03), K["flagdark"], bevel=0.01)
    ol = WS.ccw(op)
    nv = len(ol)
    for sy in (-1, 1):
        yf = sy * Y
        # voussoirs and quoins round the arch, a hood mould with label stops
        for i in range(2, nv - 1):
            osweep(f"Vous{sy}_{i}", ol, [(0.0, yf - sy * 0.05), (1.0 if i % 2 else 0.85, yf - sy * 0.05), (1.0 if i % 2 else 0.85, yf + sy * 0.06),
                                         (0.0, yf + sy * 0.06)], stl if i % 2 else K["lime"], rng=(i, i + 1), drop_back=False, shrink=0.015)
        osweep(f"Hood{sy}", ol, [(1.02, yf - sy * 0.05), (1.3, yf - sy * 0.05), (1.3, yf + sy * 0.18), (1.12, yf + sy * 0.24), (1.02, yf + sy * 0.2)],
               stl, rng=(2, nv - 1), drop_back=False)
        for sx in (-1, 1):
            box(f"Stop{sy}{sx}", (0.42, 0.3, 0.42), (sx * (HW + 1.16), yf + sy * 0.1, ZS - 0.15), stl, bevel=0.04)
            for j in range(7):
                z0 = 0.9 + j * (ZS - 1.05) / 7
                z1 = z0 + (ZS - 1.05) / 7
                wq = 1.1 if j % 2 else 0.75
                box(f"Quoin{sy}{sx}{j}", (wq, 0.11, z1 - z0 - 0.02), (sx * (HW + wq / 2), yf + sy * 0.015, (z0 + z1) / 2), stl, bevel=0.025, segments=1)
        # a string course over the arch, machicolations and a crenellated breastwork
        if sy < 0:
            for i in range(15):
                x = -7.0 + i * 1.0
                if abs(x) < 1.2:
                    continue
                for j, (d, h) in enumerate(((0.2, 0.3), (0.38, 0.3), (0.56, 0.32))):
                    box(f"Corbel{i}{j}", (0.5, d + 0.05, h), (x, yf - d / 2 + 0.02, 14.4 + j * 0.3 + h / 2), stl, bevel=0.03, segments=1)
            box("Breast", (2 * X, 0.65, 1.55), (0, yf - 0.58 + 0.33 - 0.33 + 0.0, 15.3 + 0.775), st, bevel=0.03, segments=1)
            box("BreastCope", (2 * X + 0.1, 0.75, 0.16), (0, yf - 0.25, 16.93), stl, bevel=0.03, segments=1)
        box(f"String{sy}", (2 * X, 0.16, 0.24), (0, yf + sy * 0.07, 13.05), stl, bevel=0.03, segments=1)
    # the breastwork's back face sits on the wall face: move it so its back is embedded 0.05
    br = [o for o in P.PARTS if o.name.startswith(("Breast",))]
    for o in br:
        o.location.y = -Y - 0.33 + 0.08 if o.name == "Breast" else -Y - 0.3
    for sx in (-1, 1):
        for i in range(4):
            x = sx * (1.0 + i * 2.05)
            box(f"Merlon{sx}{i}", (1.25, 1.0, 1.7), (x, -Y + 0.12, TOP + 0.85), st, bevel=0.03, segments=1)
            box(f"MerlonB{sx}{i}", (1.25, 0.8, 1.2), (x, Y - 0.4, TOP + 0.6), st, bevel=0.03, segments=1)
            box(f"MerlonCap{sx}{i}", (1.35, 1.1, 0.14), (x, -Y + 0.12, TOP + 1.77), stl, bevel=0.02, segments=1)
        for j in range(2):
            y = -2.2 + j * 2.5
            box(f"MerlonS{sx}{j}", (0.8, 1.25, 1.2), (sx * (X - 0.4), y, TOP + 0.6), st, bevel=0.03, segments=1)
    # arrow slits (blind, cut into the front face), the crest shield, two lanterns
    for sx in (-1, 1):
        cx = sx * 5.9
        cross = [(cx - 0.09, 8.6), (cx + 0.09, 8.6), (cx + 0.09, 9.85), (cx + 0.42, 9.85), (cx + 0.42, 10.05), (cx + 0.09, 10.05), (cx + 0.09, 11.4),
                 (cx - 0.09, 11.4), (cx - 0.09, 10.05), (cx - 0.42, 10.05), (cx - 0.42, 9.85), (cx - 0.09, 9.85)]
        pierce(front, [cross], y0=-Y - 0.5, y1=-Y + 0.35)
        box(f"LampPlate{sx}", (0.36, 0.06, 0.5), (sx * 5.9, -Y - 0.03, 7.0), iron, bevel=0.01)
        sqbar(f"LampArm{sx}", [(sx * 5.9, -Y - 0.05, 7.15), (sx * 5.9, -Y - 0.95, 7.15)], 0.035, iron)
        lantern(f"Lamp{sx}", sx * 5.9, -Y - 0.88, 7.15 + 0.047, 0.85, K, hang=True)
    sh = [(0, 13.35)]
    for k in range(1, 13):
        a = PI / 2 * k / 12
        sh.append((0.9 * math.sin(a), 13.35 + 0.9 * (1 - math.cos(a))))
    sh += [(0.9, 14.85), (-0.9, 14.85)]
    for k in range(12, 0, -1):
        a = PI / 2 * k / 12
        sh.append((-0.9 * math.sin(a), 13.35 + 0.9 * (1 - math.cos(a))))
    wedge("Shield", sh, -Y - 0.1, -Y + 0.05, K["enamel"])
    loopbar("ShieldRim", sh, 0.09, -Y - 0.14, -Y + 0.04, K["gilt"])
    crescent("ShieldMoon", 0, -Y - 0.12, 14.1, 0.42, K["gilt"], t=0.02)
    # the portcullis, raised: its spikes hang in the arch head; it slides down 9.0 to close the arch
    set_group("Portcullis", hinge=(0, (YS0 + YS1) / 2, 9.0), swing=1)
    rig("GatehouseArch", "Portcullis", "slide", (0, (YS0 + YS1) / 2, 9.0), 0, slide=(0, 0, -9.0))
    yp = (YS0 + YS1) / 2
    for i in range(15):
        x = -4.2 + i * 0.6
        vbar(f"PV{i}", x, yp - 0.05, 9.4, 17.0, 0.07, K["rusty"] if i % 4 == 0 else iron)
        _spike(f"PSpike{i}", (x, yp - 0.05, 9.18), 0.07, 0.44, iron, verts=4, rot=(PI, 0, PI / 4))
    for j in range(10):
        z = 9.75 + j * 0.8
        hrail(f"PH{j}", -4.3, 4.3, yp + 0.08, z, 0.06, iron)
        for i in range(15):
            box(f"PRiv{j}_{i}", (0.09, 0.05, 0.09), (-4.2 + i * 0.6, yp - 0.13, z), iron, bevel=0.01)
    set_group("Main")
    GLOW["GatehouseArch"] = {"Glow": FLAME}
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * 6.2 - 1.4, sx * 6.2 + 1.4, 1.0, 6.0, -Y - 0.02, -1, 22)
        grass(cards, rng, sx * 6.0 - 1.8, sx * 6.0 + 1.8, -Y - 0.45, -Y - 0.2, 8)
    leaves_done("GatehouseArch", cards)
    return _dims()


def gate_lych(M):
    K = gk51(M)
    rng = RNG(5105)
    iron, st, stl = K["iron"], K["castle"], K["limel"]
    WX, D = 3.9, 3.0
    for sx in (-1, 1):
        x = sx * WX
        box(f"Wall{sx}", (1.0, 2 * D - 0.4, 2.9), (x, 0, 1.45), st, bevel=0.03, segments=1)
        B20.tprism(f"WallCope{sx}", [(x - 0.62, 2.9), (x + 0.62, 2.9), (x + 0.62, 3.05), (x, 3.3), (x - 0.62, 3.05)], 0, 2 * D - 0.5, stl)
        box(f"Seat{sx}", (0.75, 2 * D - 1.8, 0.16), (x - sx * 0.85, 0, 1.6), stl, bevel=0.03, segments=1)
        for sy in (-1, 1):
            box(f"SeatLeg{sx}{sy}", (0.5, 0.32, 1.52), (x - sx * 0.85, sy * 1.6, 0.76), K["lime"], bevel=0.03, segments=1)
            y = sy * (D - 0.3)
            box(f"Pier{sx}{sy}", (1.15, 0.95, 4.3), (x, y, 2.15), K["lime"], bevel=0.04, segments=1)
            box(f"PierCap{sx}{sy}", (1.35, 1.15, 0.22), (x, y, 4.41), stl, bevel=0.04, segments=1)
            # a cast-iron column on each pier: base, shaft with a ring, a leafy capital block
            lathe(f"ColBase{sx}{sy}", [(0, 4.52), (0.3, 4.52), (0.3, 4.64), (0.2, 4.75), (0.17, 4.75), (0, 4.75)], iron, seg=12, loc=(x, y, 0))
            cyl(f"Col{sx}{sy}", 0.15, 2.65, (x, y, 4.75 + 1.325), iron, verts=12, bevel=0.0)
            cyl(f"ColRing{sx}{sy}", 0.2, 0.1, (x, y, 5.9), iron, verts=12, bevel=0.0)
            lathe(f"ColCap{sx}{sy}", [(0, 7.4), (0.17, 7.4), (0.3, 7.6), (0.32, 7.7), (0, 7.7)], iron, seg=12, loc=(x, y, 0))
        box(f"Eave{sx}", (0.32, 2 * D - 0.2, 0.3), (x, 0, 7.85), iron, bevel=0.01)
    # roof: slate on rafters, the underside z(x) = 10.95 - 0.79 |x| (through the eaves beams' tops at |x| = 4.05)
    zr = lambda x: 11.2 - 0.79 * abs(x)
    XE, RY = 5.25, D + 0.65
    for sy in (-1, 0, 1):
        y = sy * (D - 0.3)
        for sx in (-1, 1):
            sqbar(f"Rafter{sy}{sx}", [(sx * 4.05, y, zr(4.05) - 0.08), (0, y, zr(0) - 0.08)], 0.08, iron)
        pts = [(x, y, 7.75 + 1.65 * max(0.0, math.sin(PI * (x + WX - 0.15) / (2 * WX - 0.3))) ** 0.7) for x in [-(WX - 0.15) + (2 * WX - 0.3) * i / 28 for i in range(29)]]
        sqbar(f"Arch{sy}", pts, 0.06, iron)
        hrail(f"Tie{sy}", -WX, WX, y, 7.82, 0.06, iron)
        vbar(f"King{sy}", 0, y, 9.4, zr(0) - 0.16, 0.05, iron)
        for sx in (-1, 1):
            cscroll(f"Spandrel{sy}{sx}", sx * 3.2, y, 7.88, 0.42, iron, flip=sx, r=0.018)
    box("RidgeBeam", (0.24, 2 * D, 0.24), (0, 0, zr(0) - 0.12), iron, bevel=0.01)
    for sx in (-1, 1):
        wedge(f"Roof{sx}", [(0, zr(0)), (sx * XE, zr(XE)), (sx * XE, zr(XE) + 0.26), (0, zr(0) + 0.26)], -RY, RY, K["slatec"])
        # slate courses: lapped strips proud of the roof
        for k in range(9):
            t0 = k / 9
            xa, xb = sx * XE * (1 - t0), sx * XE * (1 - t0 - 1 / 9 - 0.015)
            za, zb = zr(xa) + 0.26, zr(xb) + 0.26
            wedge(f"Slates{sx}{k}", [(xa, za - 0.005), (xb, zb - 0.005), (xb, zb + 0.06), (xa, za + 0.09)], -RY + 0.03, RY - 0.03, K["slatec"])
        ribbon(f"Barge{sx}", [(0, zr(0) - 0.05), (sx * XE, zr(XE) - 0.05)], 0.28, -RY - 0.06, -RY, iron)
        ribbon(f"BargeB{sx}", [(0, zr(0) - 0.05), (sx * XE, zr(XE) - 0.05)], 0.28, RY, RY + 0.06, iron)
    box("Ridge", (0.34, 2 * RY + 0.1, 0.2), (0, 0, zr(0) + 0.33), stl, bevel=0.05)
    for i in range(13):
        y = -RY + 0.2 + i * (2 * RY - 0.4) / 12
        vbar(f"CrestBar{i}", 0, y, zr(0) + 0.42, zr(0) + 0.8, 0.02, iron)
        club(f"Crest{i}", 0, y, zr(0) + 0.8, iron, s=0.8)
    hrail("CrestRail", 0, 0, 0, 0, 0.01, iron) if False else sqbar("CrestRail", [(0, -RY + 0.2, zr(0) + 0.62), (0, RY - 0.2, zr(0) + 0.62)], 0.02, iron)
    for sy in (-1, 1):
        vbar(f"EndFin{sy}", 0, sy * (RY - 0.05), zr(0) + 0.42, zr(0) + 1.2, 0.035, iron)
        fleur(f"EndFl{sy}", 0, sy * (RY - 0.05), zr(0) + 1.2, iron, K["gilt"], s=1.3)
        # a pendant under each gable apex
        _spike(f"Pend{sy}", (0, sy * (RY + 0.03), zr(0) - 0.45), 0.08, 0.5, iron, verts=4, rot=(PI, 0, PI / 4))
    lantern("Lamp", 0, 0, 9.4 - 0.06, 0.9, K, hang=True)
    sqbar("LampHook", [(0, 0, 9.36), (0, 0, 9.46)], 0.02, iron)
    # the leaves: low double iron gates between the front piers, swinging out
    face = WX - 0.575
    yg = -(D - 0.3)
    for k, sx in enumerate((-1, 1)):
        xh, xm = sx * (face - HINGE_OFF), sx * 0.06
        set_group(f"Leaf{k}", hinge=(xh, yg, 0.2), swing=sx)
        rig("GateLych", f"Leaf{k}", "swing", (xh, yg, 0.2), 90)
        s0 = _mark()
        xs_ = xh - sx * 0.14
        x0, x1 = sorted((xs_, xm))
        vbar(f"StileH{k}", xs_, 0, 0.28, 4.3, 0.055, iron)
        vbar(f"StileM{k}", xm, 0, 0.28, 4.3, 0.045, iron)
        top = lambda x, xs_=xs_, xm=xm: 3.6 + 0.35 * math.sin(PI * (x - xs_) / (xm - xs_))
        for nm, z in (("Bot", 0.32), ("Mid", 1.5)):
            hrail(f"R{nm}{k}", x0, x1, 0, z, 0.04, iron)
        sqbar(f"RTop{k}", [(x, 0, top(x)) for x in [xs_ + (xm - xs_) * i / 12 for i in range(13)]], 0.045, iron)
        xs = leaf_bars(f"B{k}_", xs_, xm, 6, 0.32, lambda x: top(x) + 0.3, 0.03, iron)
        for i, x in enumerate(xs):
            spear(f"Sp{k}_{i}", x, 0, top(x) + 0.3, iron, s=0.85)
        allx = sorted([xs_] + xs + [xm])
        for i in range(len(allx) - 1):
            xa, xb = allx[i], allx[i + 1]
            pts = [(xa + (xb - xa) * j / 8, 0, 1.5 + 0.62 * math.sin(PI * j / 8)) for j in range(9)]
            rbar(f"Lanc{k}_{i}", pts, 0.018, iron, seg=5)
        hoop(f"Ring{k}", ((xs_ + xm) / 2, 0, 2.55), 0.42, "Y", iron, thick=0.03)
        crescent(f"Moon{k}", (xs_ + xm) / 2, 0, 2.55, 0.28, K["gilt"], t=0.03)
        collars(f"Col{k}", xh, (0.8, 3.0), iron, sx=sx)
        _xform(s0, Matrix.Translation((0, yg, 0)))
        set_group("Main")
        hinge_pins(f"Gud{k}", xh, sx * face, (0.8, 3.0), iron)
        _xform(len(P.PARTS) - 4, Matrix.Translation((0, yg, 0)))
    box("Sill", (2 * face, 0.95, 0.07), (0, yg, 0.035), K["gran"], bevel=0.02)
    box("Path", (2 * (WX - 0.5) - 0.05, 2 * D - 1.2, 0.05), (0, 0.15, 0.025), K["flag"], bevel=0.01)
    GLOW["GateLych"] = {"Glow": FLAME}
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * WX - 0.6, sx * WX + 0.6, 0.6, 3.6, -D - 0.2, -1, 6)
        grass(cards, rng, sx * WX - 0.6, sx * WX + 0.6, -D - 0.5, -D - 0.3, 4)
        for k in range(6):
            n = Vector((sx, 0, 0.15)).normalized()
            ax, ay = frame(n)
            cards.add((sx * (WX + 0.68), rng.uniform(-2.0, 2.0), 3.2), ax, ay, 1.0, rng.uniform(1.2, 2.0), "ivy", "top", segs=2, bend=n * 0.12, nrm=n)
    leaves_done("GateLych", cards)
    return _dims()


def gate_service(M):
    K = gk51(M)
    rng = RNG(5106)
    iron = K["iron"]
    PX, PW = 8.0, 2.4
    face = PX - PW / 2
    for sx in (-1, 1):
        x = sx * PX
        zt = pier(f"Pier{sx}", x, PW, 8.6, K, mat=K["brick"], cap=K["limel"])
        for j, z in enumerate((2.6, 5.4)):
            box(f"Band{sx}{j}", (PW + 0.1, PW + 0.1, 0.3), (x, 0, z), K["limel"], bevel=0.03, segments=1)
        cone(f"Pyr{sx}", PW * 0.72, 0.12, 0.9, (x, 0, zt + 0.45), K["limel"], verts=4, rot=(0, 0, PI / 4))
        vbar(f"Rod{sx}", x, 0, zt + 0.85, zt + 1.6, 0.03, iron)
        crescent(f"RodMoon{sx}", x, 0, zt + 1.78, 0.22, K["gilt"], t=0.025)
        for sy in (-1, 1):
            lathe(f"Guard{sx}{sy}", [(0, 0), (0.36, 0), (0.33, 0.35), (0.22, 0.75), (0.12, 0.85), (0, 0.86)], K["gran"], seg=12,
                  loc=(sx * (face + 0.25), sy * (PW / 2 + 0.5), 0))
    box("Sill", (2 * face, 1.6, 0.08), (0, 0, 0.04), K["gran"], bevel=0.02)
    lathe("CentreStop", [(0, 0), (0.16, 0), (0.12, 0.12), (0, 0.14)], iron, seg=12, loc=(0, 0, 0))
    # a bell on the right pier: a scrolled bracket, a brass bell and its pull chain
    yb = -PW / 2
    box("BellPlate", (0.4, 0.06, 0.5), (PX - 0.6, yb - 0.03, 6.6), iron, bevel=0.01)
    sqbar("BellArm", [(PX - 0.6, yb - 0.05, 6.75), (PX - 0.6, yb - 0.6, 6.75)], 0.03, iron)
    lathe("Bell", [(0, 6.28), (0.2, 6.28), (0.21, 6.3), (0.16, 6.38), (0.12, 6.6), (0.05, 6.72), (0, 6.72)], K["brass"], seg=16,
          loc=(PX - 0.6, yb - 0.6, 0))
    chain("BellChain", [(PX - 0.6, yb - 0.6, 6.27), (PX - 0.6, yb - 0.6, 4.6)], iron, a=0.05, b=0.025, r=0.009)
    lathe("BellPull", [(0, 4.28), (0.03, 4.3), (0.06, 4.4), (0.05, 4.55), (0, 4.56)], K["brass"], seg=10, loc=(PX - 0.6, yb - 0.6, 0))
    for k, sx in enumerate((-1, 1)):
        xh, xm = sx * (face - HINGE_OFF), sx * 0.07
        set_group(f"Leaf{k}", hinge=(xh, 0.0, 0.25), swing=sx)
        rig("GateService", f"Leaf{k}", "swing", (xh, 0.0, 0.25), 90)
        xs_ = xh - sx * 0.16
        x0, x1 = sorted((xs_, xm))
        Wd = x1 - x0
        vbar(f"StileH{k}", xs_, 0, 0.3, 7.35, 0.08, iron)
        vbar(f"StileM{k}", xm, 0, 0.3, 7.35, 0.06, iron)
        for nm, z, r in (("Bot", 0.35, 0.06), ("Dado", 3.25, 0.06), ("Mid", 5.1, 0.045), ("Top", 7.0, 0.06)):
            hrail(f"R{nm}{k}", x0, x1, 0, z, r, iron)
        box(f"Panel{k}", (Wd, 0.05, 2.84), ((x0 + x1) / 2, 0, 1.8), K["plate"], bevel=0.005)
        for sy in (-1, 1):
            box(f"Band{k}{sy}", (Wd - 0.3, 0.02, 0.46), ((x0 + x1) / 2, sy * 0.035, 2.25), K["enamel"], bevel=0.004)
            for j in range(2):
                box(f"PanelEdge{k}{sy}{j}", (Wd - 0.2, 0.025, 0.06), ((x0 + x1) / 2, sy * 0.037, (0.6, 2.95)[j]), iron, bevel=0.004)
            for i in range(int(Wd / 0.4)):
                xr = x0 + 0.2 + i * 0.4
                for z in (0.48, 3.12):
                    sphere(f"Riv{k}{sy}{i}{z}", 0.028, (xr, sy * 0.03, z), iron, seg=6, rings=3, scale=(1, 0.6, 1))
        xs = leaf_bars(f"B{k}_", xs_, xm, 13, 3.25, lambda x: 7.45, 0.035, iron)
        for i, x in enumerate(xs):
            spear(f"Sp{k}_{i}", x, 0, 7.45, iron)
        sqbar(f"Brace{k}", [(xs_, 0, 3.3), (xm, 0, 6.95)], 0.04, iron)
        # the anti-climb comb: a bar on brackets above the top rail, bristling with spikes
        for xb in (x0 + 0.3, x1 - 0.3):
            vbar(f"CombPost{k}{xb:.1f}", xb, 0, 7.0, 7.88, 0.025, iron)
        hrail(f"CombBar{k}", x0 + 0.2, x1 - 0.2, 0, 7.88, 0.035, iron)
        for i in range(int((Wd - 0.5) / 0.3)):
            xc = x0 + 0.32 + i * 0.3
            for a in (0, PI / 2, 3 * PI / 2):
                rot = (a, 0, 0)
                _spike(f"Comb{k}_{i}_{a:.1f}", (xc, -math.sin(a) * 0.14, 7.88 + math.cos(a) * 0.14), 0.03, 0.22, iron, verts=4, rot=rot)
        if k == 1:
            box("DropBolt", (0.08, 0.1, 1.4), (xm + 0.25, 0.11, 1.0), iron, bevel=0.01)
            box("Hasp", (0.5, 0.05, 0.14), (xm + 0.2, -0.065, 4.2), iron, bevel=0.01)
        collars(f"Col{k}", xh, (1.0, 6.2), iron, r=0.1, sx=sx)
        set_group("Main")
        hinge_pins(f"Gud{k}", xh, sx * face, (1.0, 6.2), iron, r=0.065)
    cards = Cards(rng)
    for sx in (-1, 1):
        grass(cards, rng, sx * PX - 1.4, sx * PX + 1.4, -1.85, -1.6, 7)
        ivy_climb(cards, rng, sx * PX - 1.2, sx * PX + 1.2, 0.6, 3.0, -PW / 2 - 0.02, -1, 9)
    leaves_done("GateService", cards)
    return _dims()


def gate_chained(M):
    K = gk51(M)
    rng = RNG(5107)
    rust = K["rusty"]
    PX, PW = 4.0, 1.7
    face = PX - PW / 2
    for sx in (-1, 1):
        zt = pier(f"Pier{sx}", sx * PX, PW, 7.8, K, mat=K["dk"], cap=K["st"], base=K["dk"])
        if sx < 0:
            cone("Pyr", PW * 0.6, 0.08, 1.1, (sx * PX, 0, zt + 0.55), K["st"], verts=4, rot=(0, 0, PI / 4))
        else:
            # the right pier's cap stone has fallen and lies cracked at its foot
            o = cone("PyrFallen", PW * 0.6, 0.08, 1.1, (0, 0, 0), K["st"], verts=4, rot=(0, 0, PI / 4))
            o.matrix_world = Matrix.Translation((PX + 1.0, -1.85, PW * 0.6 * 0.7071)) @ Matrix.Rotation(PI / 2 - 0.1, 4, "Y") @ \
                Matrix.Rotation(0.3, 4, "Z")
            ground(len(P.PARTS) - 1)
        _crack(f"Crack{sx}", (sx * PX - 0.3, -PW / 2 - 0.005, 6.0), (0.2, 0, -1), (1, 0, 0), 1.4, random.Random(sx + 9), K["hollow"])
    box("Sill", (2 * face, 1.2, 0.07), (0, 0, 0.035), K["dk"], bevel=0.02)
    for k, sx in enumerate((-1, 1)):
        xh, xm = sx * (face - HINGE_OFF), sx * 0.075
        set_group(f"Leaf{k}", hinge=(xh, 0.0, 0.25), swing=sx)
        rig("GateChained", f"Leaf{k}", "swing", (xh, 0.0, 0.25), 90)
        plain_leaf(f"L{k}", xh, xm, sx, K, rust, top=6.3, spear_top=7.05, n=6,
                   bent={1: 0.35, 4: -0.5} if k == 0 else {2: 0.6}, missing=(3,) if k == 0 else (0, 5), broken=() if k == 0 else (3,))
        if k == 1:
            # a rusted warning plate wired to the bars, a white bar painted across it
            box("Plate", (1.1, 0.03, 0.62), (xm + sx * 1.35, -0.07, 4.4), K["enamel"], bevel=0.008)
            ribbon("PlateBar", [(xm + sx * 1.35 - 0.45, 4.15), (xm + sx * 1.35 + 0.45, 4.65)], 0.1, -0.087, -0.083, K["chalk"])
            for dx in (-0.4, 0.4):
                hoop(f"PlateWire{dx}", (xm + sx * 1.35 + dx, -0.035, 4.62), 0.05, "Z", K["wire"], thick=0.008)
        set_group("Main")
        hinge_pins(f"Gud{k}", xh, sx * face, (1.0, 5.2), rust)
    # the chain: wrapped twice round both meeting stiles, its tail hanging to a padlock (its own piece, to take off)
    set_group("Chain", hinge=(0, -0.2, 2.9), swing=1)
    for j, z in enumerate((3.55, 3.75)):
        loop = [(-0.21, -0.13, z), (0.21, -0.13, z + 0.02), (0.24, 0.0, z + 0.03), (0.21, 0.13, z + 0.02), (-0.21, 0.13, z), (-0.24, 0.0, z)]
        chain(f"Loop{j}", loop, K["iron"], closed=True)
    chain("Tail", [(0.0, -0.2, 3.5), (0.03, -0.21, 3.2), (0.05, -0.21, 3.05)], K["iron"])
    box("Lock", (0.3, 0.13, 0.26), (0.05, -0.21, 2.78), K["brass"], bevel=0.04)
    hoop("Shackle", (0.05, -0.21, 2.96), 0.1, "Y", K["iron"], thick=0.022)
    box("Keyway", (0.05, 0.02, 0.1), (0.05, -0.28, 2.74), K["ink"], bevel=0.0)
    set_group("Main")
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * PX - 0.85, sx * PX + 0.85, 0.6, 6.5, -PW / 2 - 0.02, -1, 22)
        grass(cards, rng, sx * PX - 1.0, sx * PX + 1.0, -1.4, -1.1, 6, sprite="bramble", w=1.2, h=1.0)
    grass(cards, rng, -3.0, 3.0, -1.6, -0.5, 14)
    grass(cards, rng, -3.0, 3.0, 0.5, 1.6, 8, sprite="twigs")
    leaves_done("GateChained", cards)
    return _dims()


def gate_broken(M):
    K = gk51(M)
    rng = RNG(5108)
    iron = K["rusty"]
    PX, PW = 4.0, 1.8
    face = PX - PW / 2
    for sx in (-1, 1):
        zt = pier(f"Pier{sx}", sx * PX, PW, 7.6, K, mat=K["lime"])
        if sx < 0:
            obelisk("Ob", sx * PX, zt, 0.95, K)
    s0 = _mark()
    obelisk("ObFallen", 0, 0, 0.95, K)
    _xform(s0, Matrix.Translation((PX + 0.6, -2.0, 0.95 * 0.34 * 0.72)) @ Matrix.Rotation(0.5, 4, "Z") @ Matrix.Rotation(PI / 2, 4, "Y") @
           Matrix.Translation((0, 0, -0.95 * 1.1)))
    ground(s0)
    box("Sill", (2 * face, 1.2, 0.07), (0, 0, 0.035), K["gran"], bevel=0.02)
    # the working leaf
    xh0 = -(face - HINGE_OFF)
    set_group("Leaf0", hinge=(xh0, 0.0, 0.25), swing=-1)
    rig("GateBroken", "Leaf0", "swing", (xh0, 0.0, 0.25), 90)
    plain_leaf("L0", xh0, -0.075, -1, K, iron, top=6.2, spear_top=6.95, n=6, bent={2: 0.25})
    set_group("Main")
    hinge_pins("Gud0", xh0, -face, (1.0, 5.2), iron)
    # the broken leaf: off its top hinge, swung part open and tilted, its meeting corner down in the weeds
    xh1 = face - HINGE_OFF
    hinge_pins("Gud1", xh1, face, (1.0,), iron)
    box("GudStub", (0.27, 0.1, 0.1), ((xh1 + face) / 2 + 0.03, 0, 5.2), iron, bevel=0.01)
    box("GudStubBent", (0.1, 0.18, 0.06), (xh1 + 0.06, -0.08, 5.17), iron, bevel=0.01, rot=(0, 0, 0.6))
    s1 = _mark()
    plain_leaf("L1", xh1, 0.075, 1, K, iron, top=6.2, spear_top=6.95, n=6, bent={0: 0.3, 3: -0.45}, missing=(5,))
    piv = Vector((xh1, 0, 1.17))
    _xform(s1, Matrix.Translation(piv) @ Matrix.Rotation(30 * DEG, 4, "Z") @ Matrix.Rotation(-9 * DEG, 4, "Y") @ Matrix.Translation(-piv))
    bpy.context.view_layer.update()
    lo = min((o.matrix_world @ Vector(c)).z for o in P.PARTS[s1:] for c in o.bound_box)
    _xform(s1, Matrix.Translation((0, 0, -lo)))
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * PX - 0.9, sx * PX + 0.9, 0.6, 7.0, -PW / 2 - 0.02, -1, 30)
        ivy_climb(cards, rng, sx * PX - 0.9, sx * PX + 0.9, 0.6, 5.0, PW / 2 + 0.02, 1, 14)
        grass(cards, rng, sx * PX - 1.2, sx * PX + 1.2, -1.6, -1.15, 6, sprite="bramble", w=1.4, h=1.2)
    grass(cards, rng, 0.2, 3.0, -1.8, -0.3, 16, sprite="grass", w=1.1, h=1.2)
    grass(cards, rng, 0.4, 2.6, -1.6, -0.6, 6, sprite="fern", w=1.0, h=0.9)
    grass(cards, rng, -3.0, 3.0, 0.4, 1.4, 8)
    # ivy scrambling over the fallen leaf (static, so it can carry leaves)
    for k in range(18):
        t = rng.uniform(0.1, 0.9)
        z = rng.uniform(0.4, 4.0)
        p0 = Vector((xh1 - t * 2.7, 0, z))
        p = Matrix.Translation(piv) @ Matrix.Rotation(30 * DEG, 4, "Z") @ Matrix.Rotation(-9 * DEG, 4, "Y") @ Matrix.Translation(-piv) @ p0
        p.z += -lo
        nrm = Matrix.Rotation(30 * DEG, 3, "Z") @ Vector((0, -1, 0))
        ax, ay = frame(nrm, roll=rng.uniform(-0.8, 0.8))
        s = rng.uniform(0.6, 0.95)
        cards.add(tuple(p + nrm * 0.06), ax, ay, s, s * 1.2, "ivy", "fill", nrm=nrm)
    leaves_done("GateBroken", cards)
    return _dims()


def gate_moon(M):
    K = gk51(M)
    rng = RNG(5109)
    iron, gl = K["iron"], K["gilt"]
    R, ZC = 3.5, 3.3
    circ = WS.circle(0, ZC, R, 64)
    stone_wall("W", -8.0, 8.0, K, holes=[circ])
    box("Sill", (2.6, WALL_T + 0.2, 0.06), (0, 0, 0.03), K["gran"], bevel=0.02)
    cl = WS.ccw(circ)
    for sy in (-1, 1):
        yf = sy * WALL_T / 2
        for i in range(0, 64, 2):
            mz = (cl[i][1] + cl[(i + 2) % 64][1]) / 2
            if mz < 0.8:
                continue
            osweep(f"Ring{sy}_{i}", cl, [(0.0, yf - sy * 0.04), (0.55, yf - sy * 0.04), (0.55, yf + sy * 0.02), (0.0, yf + sy * 0.02)],
                   K["limel"] if (i // 2) % 2 else K["lime"], rng=(i, (i + 2) % 64), drop_back=False, shrink=0.012)
        if sy > 0:
            osweep("Hood", cl, [(0.58, yf), (0.82, yf), (0.82, yf + 0.16), (0.66, yf + 0.22), (0.58, yf + 0.18)], K["limel"], rng=(6, 26),
                   drop_back=False)
    # two half-disc leaves on the front face, hinged outside the ring: a gilt crescent on the left, a full moon on the right
    yl, RL = -WALL_T / 2 - 0.22, R + 0.1
    for k, sx in enumerate((-1, 1)):
        xh = sx * (R + 0.62)
        set_group(f"Leaf{k}", hinge=(xh, yl, 0.15), swing=sx)
        rig("GateMoon", f"Leaf{k}", "swing", (xh, yl, 0.15), 90)
        s0 = _mark()
        xm = sx * 0.06
        zb = 0.3
        a0 = math.asin((zb - ZC) / RL)
        arc = []
        for i in range(25):
            a = a0 + (PI / 2 - a0) * i / 24
            arc.append((sx * RL * math.cos(a), 0, ZC + RL * math.sin(a)))
        arc[-1] = (xm, 0, ZC + math.sqrt(RL * RL - xm * xm))
        sqbar(f"Rim{k}", arc, 0.05, iron)
        vbar(f"StileM{k}", xm, 0, zb, arc[-1][2], 0.05, iron)
        hrail(f"Bot{k}", arc[0][0], xm, 0, zb, 0.05, iron)
        # verticals clipped to the disc
        for i in range(1, 8):
            x = xm + sx * i * 0.44
            if abs(x) >= RL - 0.08:
                continue
            zt = ZC + math.sqrt(RL * RL - x * x) - 0.04
            vbar(f"V{k}{i}", x, 0, zb, zt, 0.028, iron)
        half = [(xm, 0, ZC - 1.7)] + [(sx * 1.7 * math.sin(PI * j / 20), 0, ZC - 1.7 * math.cos(PI * j / 20)) for j in range(1, 20)] + [(xm, 0, ZC + 1.7)]
        sqbar(f"Inner{k}", half, 0.035, iron)
        for j in range(5):
            a = -PI / 2 + PI * (j + 0.5) / 5
            re = RL - 0.05 if math.sin(a) > -0.1 else min(RL - 0.05, (ZC - zb) / -math.sin(a))     # stop at the bottom rail
            sqbar(f"Ray{k}{j}", [(sx * 1.72 * math.cos(a), 0, ZC + 1.72 * math.sin(a)), (sx * re * math.cos(a), 0, ZC + re * math.sin(a))],
                  0.024, iron)
        if k == 0:
            crescent("Crescent", -1.05, 0, ZC, 0.85, gl, t=0.04, tilt=0.0)
        else:
            for sy in (-1, 1):
                lathe(f"FullMoon{sy}", [(0, 0), (0.78, 0), (0.78, 0.035), (0.6, 0.05), (0, 0.06)], gl, seg=28, loc=(0, 0, 0))
                _xform(len(P.PARTS) - 1, Matrix.Translation((1.0, 0, ZC)) @ Matrix.Rotation(sy * PI / 2, 4, "X"))
            hoop("MoonRing", (1.0, 0, ZC), 0.84, "Y", iron, thick=0.03)
        # strap hinges from the hinge eyes across the rim
        for j, z in enumerate((1.3, 5.3)):
            xr = sx * math.sqrt(max(RL * RL - (z - ZC) ** 2, 0.0))
            box(f"Strap{k}{j}", (abs(xh - xr) + 0.7, 0.04, 0.16), ((xh + xr) / 2 - sx * 0.35, -0.07, z + 0.17), iron, bevel=0.008)
            cyl(f"Eye{k}{j}", 0.07, 0.22, (xh, 0, z + 0.17), iron, verts=12, bevel=0.0)
        if k == 1:
            hoop("Pull", (xm + 0.35, -0.12, 3.0), 0.14, "Y", K["brass"], thick=0.02)
            cyl("PullRose", 0.06, 0.06, (xm + 0.35, -0.09, 3.16), K["brass"], rot=(PI / 2, 0, 0), verts=12, bevel=0.0)
        _xform(s0, Matrix.Translation((0, yl, 0)))
        set_group("Main")
        for j, z in enumerate((1.3, 5.3)):
            box(f"Gud{k}{j}", (0.14, -WALL_T / 2 - 0.02 - yl, 0.1), (xh, (yl - WALL_T / 2 - 0.02) / 2, z), iron, bevel=0.01)
            cyl(f"GudPin{k}{j}", 0.045, 0.27, (xh, yl, z + 0.135), iron, verts=10, bevel=0.0)
            box(f"GudPlate{k}{j}", (0.3, 0.04, 0.4), (xh, -WALL_T / 2 - 0.02, z), iron, bevel=0.01)
    cards = Cards(rng)
    for sx in (-1, 1):
        ivy_climb(cards, rng, sx * 6.0 - 1.6, sx * 6.0 + 1.6, 0.6, 6.0, -WALL_T / 2 - 0.02, -1, 16)
        grass(cards, rng, sx * 6.0 - 1.8, sx * 6.0 + 1.8, -1.25, -1.05, 7)
        for k in range(8):
            x = sx * rng.uniform(4.6, 7.8)
            n = Vector((0, -1, 0.12)).normalized()
            ax, ay = frame(n)
            cards.add((x, -WALL_T / 2 - 0.22, WALL_TOP - 0.1), ax, ay, 1.2, rng.uniform(1.6, 3.0), "ivy", "top", segs=2, bend=n * 0.15, nrm=n)
    leaves_done("GateMoon", cards)
    return _dims()


def gate_pier_lantern(M):
    K = gk51(M)
    zt = pier("P", 0, 2.2, 8.6, K, mat=K["castle"])
    box("LampBlock", (1.3, 1.3, 0.35), (0, 0, zt + 0.175), K["limel"], bevel=0.04, segments=1)
    lantern("Lamp", 0, 0, zt + 0.35, 1.55, K)
    for sy in (-1, 1):
        y = sy * 1.1
        box(f"Plaque{sy}", (1.0, 0.08, 1.25), (0, y + sy * 0.0, 5.6), K["enamel"], bevel=0.02)
        loopbar(f"PlaqueRim{sy}", WS.rect(0.5, 4.975, 6.225), 0.07, y - sy * 0.02, y + sy * 0.07, K["gilt"])
        crescent(f"PlaqueMoon{sy}", 0, y + sy * 0.06, 5.65, 0.34, K["gilt"], t=0.02)
        hoop(f"Tether{sy}", (0, y + sy * 0.1, 3.0), 0.2, "Y", K["iron"], thick=0.03)
        cyl(f"TetherBoss{sy}", 0.08, 0.1, (0, y + sy * 0.05, 3.2), K["iron"], rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
    GLOW["GatePierLantern"] = {"Glow": FLAME}
    return _dims()


# ================================================================== more runs

def stone_wall_pier(M):
    K = gk51(M)
    zt = pier("P", 0, 2.6, 9.4, K, mat=K["castle"])
    for sy in (-1, 1):
        lancet_panel(f"Pan{sy}", 0, sy * 1.3, sy, 1.2, 2.2, 7.6, K["limel"])
    # a stone urn of flames on the cap
    lathe("Urn", [(0, 0), (0.55, 0), (0.55, 0.12), (0.3, 0.22), (0.26, 0.4), (0.5, 0.62), (0.62, 0.9), (0.6, 1.1), (0.66, 1.16), (0, 1.16)],
          K["limel"], seg=20, loc=(0, 0, zt))
    for k in range(7):
        a = k / 7 * 2 * PI
        h = 0.7 + 0.25 * ((k * 3) % 4) / 3
        cone(f"Flame{k}", 0.16, 0.0, h, (math.cos(a) * 0.32, math.sin(a) * 0.32, zt + 1.16 + h / 2 - 0.05), K["limel"], verts=6,
             rot=(math.sin(a) * 0.25, -math.cos(a) * 0.25, 0))
    cone("FlameMid", 0.24, 0.0, 1.15, (0, 0, zt + 1.16 + 0.52), K["limel"], verts=6)
    return _dims()


def brick_wall_iron(M):
    K = gk51(M)
    rng = RNG(5131)
    iron = K["iron"]
    box("Base", (8.0, 1.6, 0.5), (0, 0, 0.25), K["gran"], bevel=0.03, segments=1)
    box("Brick", (8.0, 1.3, 3.5), (0, 0, 2.25), K["brick"], bevel=0.0)
    box("Band", (8.0, 1.38, 0.2), (0, 0, 2.3), K["limel"], bevel=0.03, segments=1)
    B20.tprism("Cope", [(-0.75, 4.0), (0.75, 4.0), (0.75, 4.18), (0.25, 4.3), (-0.25, 4.3), (-0.75, 4.18)], 0, 8.0, K["limel"], plane="YZ")
    for sy in (-1, 1):
        box(f"Drip{sy}", (8.0, 0.05, 0.05), (0, sy * 0.71, 3.98), K["limel"], bevel=0.0)
    xs = [-3.75 + 0.5 * i for i in range(16)]
    hrail("RBot", -4.0, 4.0, 0, 4.65, 0.04, iron)
    hrail("RTop", -4.0, 4.0, 0, 6.9, 0.05, iron)
    hrail("RUnder", -4.0, 4.0, 0, 6.25, 0.035, iron)
    for i, x in enumerate(xs):
        vbar(f"Bar{i}", x, 0, 4.28, 7.4, 0.033, iron)
        box(f"Sock{i}", (0.12, 0.12, 0.06), (x, 0, 4.32), iron, bevel=0.01)
        spear(f"Sp{i}", x, 0, 7.4, iron, s=0.9)
        cscroll(f"S{i}", x + 0.25, 0, 6.29, 0.57, iron, flip=1 if i % 2 else -1, r=0.017)
        if i % 2 == 0:
            hoop(f"Ring{i}", (x + 0.25, 0, 5.4), 0.195, "Y", iron, thick=0.018)
    cards = Cards(rng)
    ivy_climb(cards, rng, -3.9, -1.8, 0.7, 3.6, -0.67, -1, 16)
    ivy_climb(cards, rng, 1.0, 3.9, 0.7, 2.6, 0.67, 1, 10)
    grass(cards, rng, -3.9, 3.9, -1.05, -0.85, 7)
    leaves_done("BrickWallIron", cards)
    return _dims()


def brick_wall_pier(M):
    K = gk51(M)
    zt = pier("P", 0, 2.2, 8.8, K, mat=K["brick"], cap=K["limel"])
    for j, z in enumerate((2.3, 4.45, 6.6)):
        box(f"Band{j}", (2.3, 2.3, 0.26), (0, 0, z), K["limel"], bevel=0.03, segments=1)
    cone("Pyr", 1.62, 0.1, 1.05, (0, 0, zt + 0.52), K["limel"], verts=4, rot=(0, 0, PI / 4))
    vbar("Rod", 0, 0, zt + 0.95, zt + 1.9, 0.035, K["iron"])
    for sx in (-1, 1):
        sqbar(f"Scroll{sx}", [(0, 0, zt + 1.3), (sx * 0.2, 0, zt + 1.45), (sx * 0.24, 0, zt + 1.65)], 0.02, K["iron"])
    sphere("RodBall", 0.09, (0, 0, zt + 1.98), K["gilt"], seg=10, rings=6)
    return _dims()


def hedge_railing(M, gap=False):
    K = gk51(M)
    rng = RNG(5141 + gap)
    iron = K["iron"]
    yr = -0.9
    HTOP = 7.2
    hole = [(-1.95, -0.5), (1.95, -0.5), (2.05, 1.6), (2.2, 3.2), (2.0, 4.6), (1.75, 5.9), (1.1, 6.25), (0.3, 6.15), (-0.6, 6.3), (-1.4, 6.05),
            (-1.95, 5.95), (-2.15, 4.0), (-2.0, 2.3), (-2.1, 1.0)]
    # the stone kerb (broken where the gap is) and a low railing on it
    segs = [(-4.0, 4.0)] if not gap else [(-4.0, -1.85), (1.85, 4.0)]
    for k, (a, b) in enumerate(segs):
        box(f"Kerb{k}", (b - a, 0.85, 0.5), ((a + b) / 2, yr, 0.25), K["gran"], bevel=0.03, segments=1)
        box(f"KerbCope{k}", (b - a, 0.7, 0.14), ((a + b) / 2, yr, 0.57), K["limel"], bevel=0.03, segments=1)
    if gap:
        for k, (x, y, sz) in enumerate(((-2.45, -1.75, 0.35), (2.6, -1.8, 0.3), (2.25, -1.55, 0.2))):
            box(f"KerbChunk{k}", (sz * 2.2, sz * 1.6, sz), (x, y, sz / 2), K["gran"], bevel=0.04, rot=(0, 0, rng.uniform(-0.6, 0.6)))
        box("Mud", (3.6, 4.6, 0.03), (0, 0.4, 0.015), K["mud"], bevel=0.0)
    xs = [-3.8 + 0.4 * i for i in range(20)]
    for nm, z, r in (("Bot", 0.95, 0.035), ("Top", 4.05, 0.045)):
        if not gap:
            hrail(f"R{nm}", -4.0, 4.0, yr, z, r, iron)
        else:
            hrail(f"R{nm}A", -4.0, -1.95, yr, z, r, iron)
            hrail(f"R{nm}B", 1.95, 4.0, yr, z, r, iron)
            for sx in (-1, 1):     # the cut rail ends, bent forward
                sqbar(f"R{nm}End{sx}", [(sx * 1.95, yr, z), (sx * 1.82, yr - 0.12, z - 0.04)], r * 0.9, iron)
    for i, x in enumerate(xs):
        if gap and abs(x) < 1.9:
            continue
        vbar(f"Bar{i}", x, yr, 0.62, 4.4, 0.028, iron)
        spear(f"Sp{i}", x, yr, 4.4, iron, s=0.75)
    if gap:
        sqbar("FallenBar", [(2.3, -1.6, 0.03), (3.6, -1.35, 0.03)], 0.028, iron)
    # the clipped yew behind
    core = B40.hedge_core("Hedge", K, (8.5, 2.5, HTOP), (0, 1.0, HTOP / 2))
    if gap:
        pierce(core, [hole], y0=-1.0, y1=3.0)
    cards = Cards(rng)
    keep = (lambda p, n: abs(p.x) < 4.25 and not (abs(p.x) < 1.75 and p.z < 6.0)) if gap else (lambda p, n: abs(p.x) < 4.25)
    cards.cover(core, 1.6, "hedge", 1.5, offset=0.1, tilt=0.4, zmin=1.05, keep=keep)
    grass(cards, rng, -3.9, 3.9, -1.55, -1.38, 7)
    if gap:
        grass(cards, rng, -2.5, -1.9, -1.4, 2.4, 4)
        grass(cards, rng, 1.9, 2.5, -1.4, 2.4, 4)
    leaves_done("SneakHedgeGap" if gap else "HedgeRailing", cards)
    if gap:
        SNEAK["SneakHedgeGap"] = {"clear": [(-1.7, 1.7, -1.6, 2.4, 0.05, 0.05 + CLEAR_H)], "cover": None, "kind": "Board"}
    return _dims()


# ================================================================== sneak gaps

def _broken_plinth(K, rng, xa, xb):
    """The railing plinth with a gap broken out between xa and xb: base and coping each side, rubble pushed aside."""
    for k, (a, b) in enumerate(((-4.0, xa), (xb, 4.0))):
        box(f"Base{k}", (b - a, PW + 0.12, PB), ((a + b) / 2, 0, PB / 2), K["gran"], bevel=0.03, segments=1)
        B20.tprism(f"Cope{k}", [(-PW / 2, PB), (PW / 2, PB), (PW / 2, PT - 0.08), (0.2, PT), (-0.2, PT), (-PW / 2, PT - 0.08)], (a + b) / 2,
                   b - a, K["limel"], plane="YZ")
    for k, (x, y, sz) in enumerate(((xa - 0.5, -1.05, 0.32), (xb + 0.55, -1.1, 0.26), (xb + 0.35, 0.95, 0.3), (xa - 0.3, 1.05, 0.22))):
        box(f"Rubble{k}", (sz * 2.0, sz * 1.5, sz), (x, y, sz / 2), K["gran"] if k % 2 else K["limel"], bevel=0.05, rot=(0, 0, rng.uniform(-0.7, 0.7)))


def sneak_bent_bars(M):
    K = gk51(M)
    rng = RNG(5151)
    iron = K["iron"]
    G = 1.75
    _broken_plinth(K, rng, -2.5, 2.5)
    railing("R", K, gap=(-G, G), keep_bars=lambda x: abs(x) >= G - 1e-6, plinth=False,
            bar_bottom=lambda x: 0.95 + 0.1 * (abs(x) > 2.0) if abs(x) < 2.5 else None)
    # the six middle bars, rusted off at their feet and bent aside under the top rail, stacked behind the standing bars
    for x0 in (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25):
        s = 1 if x0 > 0 else -1
        j = {1.25: 0, 0.75: 1, 0.25: 2}[abs(x0)]
        xe, ye = s * (1.86 + 0.12 * j), 0.09 + 0.1 * j
        vbar(f"BTop{x0}", x0, 0, R_TOP - 0.05, BAR_TOP, 0.035, iron)
        club(f"BF{x0}", x0, 0, BAR_TOP, iron)
        pts = [(x0, 0, R_TOP - 0.03), (xe, ye, 6.02), (xe, ye, 4.2), (xe + s * 0.05, ye, 2.6), (xe + s * 0.12, ye + 0.03, 1.5 + 0.2 * j)]
        sqbar(f"Bent{x0}", pts, 0.035, iron)
    for sx in (-1, 1):     # rusted rail ends
        for z in (R_BOT, R_DOG):
            sqbar(f"RailTip{sx}{z}", [(sx * G, 0, z), (sx * (G + 0.03), -0.09, z - 0.04)], 0.028, K["rusty"])
    yface = -0.055
    tie = lambda k, ctr, size: [(-G, ctr[2], "Z"), (G, ctr[2], "Z")] + ([(-2.25, ctr[2], "Z"), (2.25, ctr[2], "Z")] if ctr[2] > 0.9 else [])
    boards("SneakBentBars", (-G, G, 0.0, R_TOP - 0.06), yface, K, rng, orient="h", over=0.5, pried=5, chalk=2, ties=tie, bar_back=0.035)
    SNEAK["SneakBentBars"] = {"clear": [(-1.68, 1.68, -0.9, 0.9, 0.05, 0.05 + CLEAR_H)], "cover": (-G + 0.03, G - 0.03, 0.0, R_TOP - 0.06),
                              "kind": "Board"}
    cards = Cards(rng)
    grass(cards, rng, -3.9, 3.9, -0.85, -0.65, 7)
    grass(cards, rng, -1.6, 1.6, -0.6, 0.6, 6, sprite="grass", w=0.6, h=0.5)
    leaves_done("SneakBentBars", cards)
    return _dims()


def sneak_missing_bars(M):
    K = gk51(M)
    rng = RNG(5152)
    iron = K["iron"]
    G = 1.75
    railing("R", K, gap=(-G, G), keep_bars=lambda x: abs(x) >= G - 1e-6)
    # sawn stubs where six bars were cut out (their tops still hang under the rail), a sawn-off bar lying in the grass
    for x in (-1.25, -0.75, -0.25, 0.25, 0.75, 1.25):
        box(f"StubLo{x}", (0.13, 0.13, 0.05), (x, 0, PT + 0.015), K["dk"], bevel=0.01)
        vbar(f"StubHi{x}", x, 0, R_TOP - 0.09, BAR_TOP, 0.035, iron)
        club(f"F{x}", x, 0, BAR_TOP, iron)
    sqbar("SawnBar", [(2.2, -1.5, 0.035), (3.6, -1.15, 0.035)], 0.035, K["rusty"])
    sqbar("SawnBar2", [(-3.5, -1.3, 0.035), (-2.5, -1.75, 0.035)], 0.035, K["rusty"])
    yface = -0.055
    tie = lambda k, ctr, size: [(ctr[0], R_TOP, "X")]
    boards("SneakMissingBars", (-1.98, 1.98, PT, R_TOP - 0.06), yface, K, rng, orient="v", over=0.0, pried=3, chalk=4, ties=tie, bar_back=0.05,
           ground=PT)
    SNEAK["SneakMissingBars"] = {"clear": [(-1.68, 1.68, -0.9, 0.9, PT + 0.06, R_TOP - 0.1)], "cover": (-1.75, 1.75, PT + 0.02, R_TOP - 0.08),
                                 "kind": "Board"}
    cards = Cards(rng)
    grass(cards, rng, -3.9, 3.9, -0.85, -0.65, 7)
    leaves_done("SneakMissingBars", cards)
    return _dims()


def sneak_wall_hole(M):
    K = gk51(M)
    rng = RNG(5153)
    g = random.Random(53)
    pts = [(-1.95, -0.5), (1.95, -0.5)]
    for k in range(6):            # the right side up, ragged outward only
        z = 0.6 + k * 1.0
        pts.append((1.95 + g.uniform(0.0, 0.35), z))
    top = []
    for k in range(9):
        x = 1.9 - k * 3.8 / 8
        top.append((x, 6.0 + g.uniform(0.0, 0.55) + 0.25 * math.sin(PI * k / 8)))
    pts += top
    for k in range(5, -1, -1):
        z = 0.6 + k * 1.0
        pts.append((-1.95 - g.uniform(0.0, 0.35), z))
    stone_wall("W", -4.0, 4.0, K, holes=[pts], band=False)
    zmax = max(z for _, z in pts)
    # fallen blocks, pushed to the sides
    for k, (x, y, sz) in enumerate(((-2.9, -1.5, 0.45), (-3.4, -1.25, 0.32), (2.95, -1.55, 0.4), (2.8, 1.35, 0.36), (-2.6, 1.45, 0.3),
                                   (3.4, -1.9, 0.28))):
        box(f"Block{k}", (sz * 1.8, sz * 1.2, sz), (x, y, sz / 2), K["castle"] if k % 2 else K["lime"], bevel=0.05, rot=(0, 0, g.uniform(-0.8, 0.8)))
    # boards on the front: the bottom plank on the plinth's face, the rest on the wall face
    base = lambda zc: -WALL_T / 2 - 0.16 - 0.005 if zc < 0.5 else -WALL_T / 2 - 0.005
    lay = lambda k: 0 if k <= 1 else (k - 1) % 2
    boards("SneakWallHole", (-2.35, 2.35, 0.0, zmax + 0.05), None, K, rng, orient="h", over=0.35, pried=4, chalk=6, base_fn=base, layer_fn=lay)
    SNEAK["SneakWallHole"] = {"clear": [(-1.68, 1.68, -1.2, 1.2, 0.05, 0.05 + CLEAR_H)], "cover": (-2.3, 2.3, 0.0, zmax), "kind": "Board"}
    cards = Cards(rng)
    for k in range(12):
        x = rng.uniform(2.6, 3.9) * (1 if k % 2 else -1)
        n = Vector((0, -1, 0.12)).normalized()
        ax, ay = frame(n)
        cards.add((x, -WALL_T / 2 - 0.22, WALL_TOP - 0.1), ax, ay, 1.2, rng.uniform(1.4, 2.8), "ivy", "top", segs=2, bend=n * 0.15, nrm=n)
    grass(cards, rng, -3.9, -2.4, -1.25, -1.05, 4)
    grass(cards, rng, 2.4, 3.9, -1.25, -1.05, 4)
    leaves_done("SneakWallHole", cards)
    return _dims()


def sneak_culvert(M):
    K = gk51(M)
    rng = RNG(5154)
    iron = K["iron"]
    PXW, PD = 2.6, 0.75
    railing("RL", K, x0=-4.0, x1=-PXW)
    railing("RR", K, x0=PXW, x1=4.0)
    # the culvert portal: the railing's plinth rises into a stone bridge over an old drain, its grate long rusted out and the
    # silt under it dug away to a muddy scrape
    hw, js, rise = 1.95, 5.95, 0.45
    Rr = (hw * hw + rise * rise) / (2 * rise)
    zc = js + rise - Rr
    a = math.asin(hw / Rr)
    head = [(Rr * math.sin(a - 2 * a * i / 16), zc + Rr * math.cos(a - 2 * a * i / 16)) for i in range(17)]
    op = [(-hw, -0.5), (hw, -0.5)] + [(hw, js)] + head[1:-1] + [(-hw, js)]
    blk = wedge("Portal", [(-PXW, 0), (PXW, 0), (PXW, 7.0), (-PXW, 7.0)], -PD, PD, K["castle"])
    pierce(blk, [op], y0=-3, y1=3)
    B20.tprism("PortalCope", [(-PD - 0.15, 7.0), (PD + 0.15, 7.0), (PD + 0.15, 7.18), (0, 7.55), (-PD - 0.15, 7.18)], 0, 2 * PXW + 0.3, K["limel"],
               plane="YZ")
    opc = WS.ccw(op)
    for sy in (-1, 1):
        yf = sy * PD
        hi = [i for i, (x, z) in enumerate(opc) if z > js - 0.01 or abs(abs(x) - hw) < 1e-6 and z > 0.3]
        osweep(f"Ring{sy}", opc, [(0.0, yf - sy * 0.04), (0.42, yf - sy * 0.04), (0.42, yf + sy * 0.07), (0.0, yf + sy * 0.07)], K["limel"],
               rng=(2, len(opc) - 1), drop_back=False)
        box(f"Key{sy}", (0.5, 0.18, 0.5), (0, yf + sy * 0.04, js + rise + 0.32), K["limel"], bevel=0.04)
        for sx in (-1, 1):       # the grate's rusted hinge stubs on the jambs
            for z in (1.0, 4.6):
                box(f"Stub{sy}{sx}{z}", (0.12, 0.14, 0.14), (sx * (hw - 0.04), yf - sy * 0.12, z), K["rusty"], bevel=0.01)
    box("Scrape", (2 * hw, 2 * PD + 2.0, 0.03), (0, 0, 0.015), K["mud"], bevel=0.0)
    s0 = _mark()
    B40.mound("Spoil", 0.9, 0.7, 0.45, K["mud"], rng)
    _xform(s0, Matrix.Translation((3.2, -1.6, 0)))
    # a spade left leaning on the portal
    sqbar("SpadeShaft", [(3.1, -1.5, 0.42), (2.52, -0.79, 2.6)], 0.035, K["oakd"])
    box("SpadeBlade", (0.34, 0.04, 0.45), (3.16, -1.57, 0.23), K["rusty"], bevel=0.01, rot=(0.0, 0, -0.88))
    box("SpadeGrip", (0.3, 0.06, 0.06), (2.52, -0.81, 2.62), K["oakd"], bevel=0.01, rot=(0, 0, -0.88))
    boards("SneakCulvert", (-hw, hw, 0.0, js + rise + 0.05), -PD - 0.005, K, rng, orient="h", over=0.25, pried=3, chalk=4)
    SNEAK["SneakCulvert"] = {"clear": [(-1.7, 1.7, -1.0, 1.0, 0.05, 0.05 + CLEAR_H)], "cover": (-hw, hw, 0.0, js + rise), "kind": "Board"}
    cards = Cards(rng)
    grass(cards, rng, -3.9, -2.8, -0.85, -0.65, 3)
    grass(cards, rng, 2.8, 3.9, -0.85, -0.65, 3)
    grass(cards, rng, -1.6, 1.6, 1.0, 1.8, 5, sprite="fern")
    ivy_climb(cards, rng, -2.5, -2.0, 0.8, 5.0, -PD - 0.02, -1, 6)
    leaves_done("SneakCulvert", cards)
    return _dims()


def sneak_loose_bars(M):
    K = gk51(M)
    rng = RNG(5155)
    iron = K["iron"]
    G = 1.75
    railing("R", K, gap=(-G, G), keep_bars=lambda x: abs(x) >= G - 1e-6)
    for sx in (-1, 1):
        for z in (R_BOT, R_DOG, R_BAND):
            sqbar(f"RailTip{sx}{z}", [(sx * G, 0, z), (sx * (G + 0.03), 0.09, z - 0.04)], 0.028, K["rusty"])
    g = random.Random(55)
    for k, x in enumerate((-1.25, -0.75, -0.25, 0.25, 0.75, 1.25)):
        box(f"Sock{k}", (0.15, 0.15, 0.06), (x, 0, PT + 0.02), K["dk"], bevel=0.01)
        zc = (PT + BAR_TOP + 0.35) / 2
        set_group(f"Bar{k}", hinge=(x, 0, zc), swing=1)
        s0 = _mark()
        vbar(f"LB{k}", x, 0, PT + 0.0, BAR_TOP, 0.035, K["rusty"] if k % 2 else iron)
        club(f"LF{k}", x, 0, BAR_TOP, iron)
        piv = Vector((x, 0, PT))
        _xform(s0, Matrix.Translation(piv) @ Matrix.Rotation(g.uniform(-0.6, 0.6) * DEG, 4, "X") @ Matrix.Rotation(g.uniform(5, 20) * DEG, 4, "Z")
               @ Matrix.Translation(-piv))
        set_group("Main")
    SNEAK["SneakLooseBars"] = {"clear": [(-1.68, 1.68, -0.9, 0.9, PT + 0.08, R_TOP - 0.1)], "cover": None, "kind": "Bar"}
    cards = Cards(rng)
    grass(cards, rng, -3.9, 3.9, -0.85, -0.65, 7)
    leaves_done("SneakLooseBars", cards)
    return _dims()


# ================================================================== registration, checks, previews

BUILDERS = {
    "GateGrand": gate_grand,
    "GatePedestrian": gate_pedestrian,
    "GateWicket": gate_wicket,
    "GatehouseArch": gatehouse_arch,
    "GateLych": gate_lych,
    "GateService": gate_service,
    "GateChained": gate_chained,
    "GateBroken": gate_broken,
    "GateMoon": gate_moon,
    "GatePierLantern": gate_pier_lantern,
    "Railing8": railing8,
    "RailingPost": railing_post,
    "RailingCorner": railing_corner,
    "RailingEnd": railing_end,
    "RailingGatePier": railing_gate_pier,
    "StoneWall8": stone_wall8,
    "StoneWallPier": stone_wall_pier,
    "BrickWallIron": brick_wall_iron,
    "BrickWallPier": brick_wall_pier,
    "HedgeRailing": lambda M: hedge_railing(M, False),
    "SneakBentBars": sneak_bent_bars,
    "SneakMissingBars": sneak_missing_bars,
    "SneakWallHole": sneak_wall_hole,
    "SneakCulvert": sneak_culvert,
    "SneakHedgeGap": lambda M: hedge_railing(M, True),
    "SneakLooseBars": sneak_loose_bars,
}


def _write_rig():
    path = os.path.join(P.HERE, "gates_batch51.json")
    old = {}
    if os.path.exists(path):
        try:
            old = json.load(open(path))
        except Exception:      # noqa: BLE001
            old = {}
    old.update(RIG)
    for k, v in SNEAK.items():
        old.setdefault("_sneak", {})[k] = v
    json.dump(old, open(path, "w"), indent=1)


def _wrap(fn):
    def build(M):
        d = fn(M)
        _write_rig()
        return d
    return build


P.BUILD.update({k: _wrap(v) for k, v in BUILDERS.items()})
P.PREVIEW_PAD.update({n: 1.05 for n in BUILDERS})


def _open_degs():
    for prop, pieces in RIG.items():
        for piece, r in pieces.items():
            P.OPEN_DEG[piece] = r["angle"] if r["kind"] == "swing" else 0


_preview = P.preview


def preview(objs, name, dims, suffix=""):
    """nh_props.preview, then (for a prop with removable boards or bars) a second view with them taken off: <name>_clear.png."""
    _open_degs()
    for o in objs:
        if o.name.split("_")[-1].startswith(("Board", "Bar", "Chain", "Portcullis")):
            P.OPEN_DEG[o.name] = 0          # the _open view turns only the leaves and doors
    _preview(objs, name, dims, suffix)
    lift = [o for o in objs if o.name.split("_")[-1].startswith(("Board", "Bar"))]
    if lift and not suffix:
        for o in lift:
            o.hide_render = True
        _preview(objs, name, dims, "_clear")
        for o in lift:
            o.hide_render = False


P.preview = preview


# ------------------------------------------------------------------ checks (run51.py --check calls check())

def _islands(me):
    """Loose parts of a mesh: lists of polygon indices."""
    parent = list(range(len(me.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    out = {}
    for p in me.polygons:
        out.setdefault(find(p.vertices[0]), []).append(p.index)
    return list(out.values())


def inside_out(ob):
    """Closed loose parts whose signed volume is negative (their normals point inward). Returns (bad, closed, total)."""
    me = ob.data
    edge_faces = {}
    for p in me.polygons:
        for k in p.edge_keys:
            edge_faces[k] = edge_faces.get(k, 0) + 1
    bad, closed = 0, 0
    isl = _islands(me)
    for polys in isl:
        if any(edge_faces[k] != 2 for pi in polys for k in me.polygons[pi].edge_keys):
            continue
        closed += 1
        vol = 0.0
        for pi in polys:
            vs = [me.vertices[i].co for i in me.polygons[pi].vertices]
            for j in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[j].cross(vs[j + 1])) / 6.0
        if vol < -1e-7:
            bad += 1
    return bad, closed, len(isl)


def _bvh(ob, skip_axis=None):
    """A world-space BVH of a joined piece; skip_axis = r leaves out the faces within r of the piece's own Z axis (a leaf's
    hinge eyes, which ride on the pier's pins by design)."""
    mw = ob.matrix_world
    vs = [mw @ v.co for v in ob.data.vertices]
    polys = [p.vertices[:] for p in ob.data.polygons if skip_axis is None or Vector(p.center[:2]).length > skip_axis]
    return BVHTree.FromPolygons(vs, polys)


def _box_bvh(b):
    x0, x1, y0, y1, z0, z1 = b
    vs = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return BVHTree.FromPolygons(vs, fs)


def _verts_in(ob, b):
    x0, x1, y0, y1, z0, z1 = b
    mw = ob.matrix_world
    return sum(1 for v in ob.data.vertices if x0 < (mw @ v.co).x < x1 and y0 < (mw @ v.co).y < y1 and z0 < (mw @ v.co).z < z1)


def check_parts():
    """Before the join: the named parts with closed loose parts that are inside out (negative volume)."""
    dg = bpy.context.evaluated_depsgraph_get()
    bad = []
    for ob in P.PARTS:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        tmp = bpy.data.meshes.new("_t")
        tmp.from_pydata([v.co.copy() for v in me.vertices], [], [p.vertices[:] for p in me.polygons])
        ev.to_mesh_clear()
        class _O:
            pass
        o = _O()
        o.data = tmp
        b, c, t = inside_out(o)
        if b:
            bad.append(f"{ob.name}({b}/{c})")
        bpy.data.meshes.remove(tmp)
    print("[parts] inside-out:", ", ".join(bad) or "none", flush=True)


def check(name, objs):
    """Size cap, inside-out parts, leaf / door clearance (closed and open), and for sneak props: the clear box with the
    boards / bars off, and full board cover."""
    bpy.context.view_layer.update()
    rep = []
    for o in objs:
        lo = [min((o.matrix_world @ Vector(c))[k] for c in o.bound_box) for k in range(3)]
        hi = [max((o.matrix_world @ Vector(c))[k] for c in o.bound_box) for k in range(3)]
        dim = [hi[k] - lo[k] for k in range(3)]
        bad, closed, tot = inside_out(o)
        flag = " OVER-CAP" if max(dim) >= CAP else ""
        rep.append(f"  {o.name}: {dim[0]:.2f} x {dim[1]:.2f} x {dim[2]:.2f}{flag}; inside-out {bad}/{closed} closed parts ({tot} parts)")
    main = [o for o in objs if o.name == name or o.name.endswith("_Main")]
    moving = [o for o in objs if "nh_swing" in o.keys() and o.name.split("_")[-1].startswith(("Leaf", "Door"))]
    for m in moving:
        hits = []
        for ang in (0, 1):
            if ang:
                m.rotation_euler[2] = math.radians(RIG.get(name, {}).get(m.name, {}).get("angle", 90)) * m["nh_swing"]
                bpy.context.view_layer.update()
            bm = _bvh(m, skip_axis=0.14)
            for o in objs:
                if o is m or o.name.endswith(("_Leaves", "_Glow", "_Glass")):
                    continue
                if (o in moving or o.name.endswith("_Chain")) and ang:
                    continue
                pairs = bm.overlap(_bvh(o))
                if pairs:
                    mw = o.matrix_world
                    cs = [mw @ o.data.polygons[j].center for _, j in pairs]
                    lo = [round(min(c[k] for c in cs), 2) for k in range(3)]
                    hi = [round(max(c[k] for c in cs), 2) for k in range(3)]
                    hits.append(f"{'open' if ang else 'shut'}:{o.name.split('_')[-1]}={len(pairs)} at {lo}..{hi}")
            m.rotation_euler[2] = 0
            bpy.context.view_layer.update()
        rep.append(f"  swing {m.name}: {'CLEAR' if not hits else 'TOUCHES ' + ' '.join(hits)}")
    for o in objs:
        if o.name.split("_")[-1].startswith(("Portcullis", "Chain", "Board", "Bar")):
            n = sum(len(_bvh(o).overlap(_bvh(m))) for m in main)
            rep.append(f"  {o.name} against Main: {n} touching faces")
    sn = SNEAK.get(name)
    if sn:
        solid = [o for o in objs if not o.name.split("_")[-1].startswith(("Board", "Bar", "Leaves"))]
        for b in sn["clear"]:
            bb = _box_bvh(b)
            hits = [(o.name.split("_")[-1], len(bb.overlap(_bvh(o))), _verts_in(o, b)) for o in solid]
            hits = [h for h in hits if h[1] or h[2]]
            rep.append(f"  clear box {tuple(round(v, 2) for v in b)} (boards off): {'CLEAR' if not hits else 'BLOCKED ' + str(hits)}")
        lift = [o for o in objs if o.name.split("_")[-1].startswith(sn["kind"])]
        if sn.get("cover") and lift:
            x0, x1, z0, z1 = sn["cover"]
            trees = [_bvh(o) for o in lift]
            miss, tot = 0, 0
            for i in range(int((x1 - x0) / 0.05) + 1):
                for j in range(int((z1 - z0) / 0.05) + 1):
                    x, z = x0 + i * 0.05, z0 + j * 0.05
                    tot += 1
                    if not any(t.ray_cast(Vector((x, -30, z)), Vector((0, 1, 0)))[0] is not None for t in trees):
                        miss += 1
            rep.append(f"  board cover of {sn['cover']}: {tot - miss}/{tot} rays hit a {sn['kind']} ({'FULL' if miss == 0 else 'GAPS'})")
        # each lifting piece's origin at its centre
        for o in lift:
            lo = [min(Vector(c)[k] for c in o.bound_box) for k in range(3)]
            hi = [max(Vector(c)[k] for c in o.bound_box) for k in range(3)]
            off = max(abs((lo[k] + hi[k]) / 2) for k in range(3))
            if off > 0.35:
                rep.append(f"  {o.name}: origin {off:.2f} off its centre")
    lows = {o.name.split("_")[-1]: min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in objs}
    rep.append(f"  lowest point z = {min(lows.values()):.3f}" + ("  below ground: " + str({k: round(v, 2) for k, v in lows.items() if v < -0.01})
                                                             if min(lows.values()) < -0.01 else ""))
    print(f"[check] {name}\n" + "\n".join(rep), flush=True)
