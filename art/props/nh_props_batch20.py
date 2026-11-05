"""Props batch 20 (2026-11-04): the stair and bridge kit for nh_props.py. Building pieces for the map builder, made to
the courtyard set's standard (batches 8 and 9): dark weathered castle stone with worn edges, dirt in the joints, moss and
hairline cracks; carved blind lancets and crocketed pinnacles; gothic cast iron with gilt roundels and a brass handrail;
crimson enamel crests; a crimson runner; gaslight. Very little wood (none).

The stairs are baked whole (weathering, AO, edge wear) into the 2048 atlas. The bridges, which are too big for one atlas
to stay sharp, keep their broad flat faces as a Wall piece in the seamless castle stone (world-scaled, 8 studs a tile, as
the cloister arch does) with the carved details baked.

  StairStone        a straight flight: 8 worn stone treads (rise 0.75, run 1.25) between cheek walls carved with
                    blind lancets under a raking coping, crocketed pinnacle newels with crimson and gilt crests;
                    6 wide inside, 6 up, 10 long
  StairStoneRailed  the same flight with a raking gothic cast-iron balustrade (trefoil-headed arcade, gilt roundels,
                    brass handrail) on both cheeks, iron newels at the head
  StairLanding      a 7.6 x 7.6 landing 6 high to join flights into turns and switchbacks: buttressed corners
                    rising into crocketed pinnacles, three carved lancet panels a face (the middle one framing a large
                    crimson and gilt crest under a hood moulding), an arched corbel table under the cornice, worn
                    random-run flagstones round a crimson and gilt quatrefoil medallion, two gas lanterns on brackets
  StairGrand        the entrance hall's grand stair, 12 wide: 10 treads (rise 0.6), a crimson runner with gilt borders
                    and quatrefoils held by brass rods, carved cheeks, a gilt-and-iron balustrade, tall newel pedestals
                    with crests and gas lanterns
  StairSpiral       a tower stair: a clustered gothic newel shaft, 20 wedge treads making one turn 12 high, a landing
                    at the top, an iron rail with gilt roundels and a brass handrail round the outside
  StairIron         an open cast-iron stair (mezzanine, fire stair): 10 chequer-plate treads (rise 0.8), 4 wide,
                    stringers pierced with quatrefoils, the gothic balustrade on both sides
  BridgeStoneArch   a humped stone footbridge 24 long: a segmental arch of dark voussoirs with a crimson-crested
                    keystone and a hood moulding, pierced gothic parapets (the courtyard Balustrade's arcade), crested end
                    piers with gas lanterns, moss and cracks
  BridgeIron        a Victorian cast-iron footbridge 24 long: crimson lattice girders with gilt quatrefoil bosses and
                    spear finials, arched ribs with ring spandrels, a plated deck on carved stone abutments, lanterns
  BridgeDeck        a modular 16-stud straight span with the pierced parapets; tiles end to end
  BridgePier        a 16-high stone pier with pointed cutwaters, string courses, iron cramps and crests; carries BridgeDeck

Front faces -Y, Z is up, the origin is at the bottom centre. Stairs climb toward +Y (the bottom step at the front).
Bridges span along X (their elevation faces the front). Registered into nh_props.BUILD on import.
"""
import math
import random

from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch8 import castle, mossy, hollow, staining, _moss, _crack, _stain, _lancet, _foil, _spirelet, _pointed
from nh_props_batch9 import foil
from nh_props_batch10 import gilt
from nh_props_batch19 import hex_lantern, _gothic


def _stone(M):
    """Placeholder stone for the bridges' Wall pieces (they get the tiled castle stone, see TILED below)."""
    return M["stonedark"]


def tprism(name, poly, pos, depth, mat, plane="XZ", bevel=0.0):
    """prism() triangulated (beauty), so concave outlines (arches, stepped profiles) import into Roblox correctly."""
    ob = prism(name, poly, pos, depth, mat, plane=plane, bevel=bevel)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    md.quad_method = "BEAUTY"
    md.ngon_method = "BEAUTY"
    return ob


def _side(s, x, face):
    """Move the parts built since mark s (built facing -Y at the origin, their local x running along the stair) onto a
    side face at x: face +1 looks to +X, -1 to -X."""
    _xform(s, Matrix.Translation((x, 0, 0)) @ Matrix.Rotation(math.pi / 2 * face, 4, "Z"))


def _crest(prefix, x, y, z, M, gl, s=1.0, face=-1):
    """A crimson enamel shield with a gilt rim and a gilt quatrefoil, on a face looking along Y (face -1 = to the front)."""
    m = _mark()
    shield = [(-0.28 * s, 0.32 * s), (0.28 * s, 0.32 * s), (0.28 * s, -0.02 * s), (0.18 * s, -0.24 * s), (0, -0.34 * s), (-0.18 * s, -0.24 * s),
              (-0.28 * s, -0.02 * s)]
    prism(f"{prefix}Shield", shield, 0, 0.05, M["crimson"], bevel=0.008)
    tube(f"{prefix}Rim", [(u, -0.03, v) for u, v in shield], 0.012, gl, closed=True, square=True, poly=True)
    foil(f"{prefix}Foil", 0, -0.035, 0.02 * s, 0.11 * s, gl, thick=0.012)
    _xform(m, Matrix.Translation((x, y, z)) @ Matrix.Rotation(0 if face < 0 else math.pi, 4, "Z"))


def _pin_newel(prefix, x, y, M, stone, dark, gl, h=3.0, w=1.15, crest_face=-1, pinnacle=True):
    """A stone newel: a plinth, a shaft with a trefoil-headed lancet on its front and sides, a cap, a crocketed
    pinnacle with a gilt finial, a crimson and gilt crest on the front."""
    box(f"{prefix}Plinth", (w + 0.16, w + 0.16, 0.35), (x, y, 0.175), dark, bevel=0.04)
    box(f"{prefix}Shaft", (w, w, h - 0.55), (x, y, 0.35 + (h - 0.55) / 2), stone, bevel=0.04)
    box(f"{prefix}Cap", (w + 0.2, w + 0.2, 0.22), (x, y, h - 0.09), dark, bevel=0.05)
    for k, (dx, dy, rot) in enumerate(((0, -1, 0), (1, 0, math.pi / 2), (-1, 0, -math.pi / 2))):
        s = _mark()
        _lancet(f"{prefix}Lancet{k}", 0, 0, 0.7, w * 0.3, h * 0.55, h * 0.78, dark, thick=0.03)
        _xform(s, Matrix.Translation((x + dx * (w / 2 + 0.005), y + dy * (w / 2 + 0.005), 0)) @ Matrix.Rotation(rot, 4, "Z"))
    if pinnacle:
        _spirelet(f"{prefix}Pin", x, y, h + 0.02, 1.5, w * 0.62, stone, crockets=3)
        sphere(f"{prefix}Gilt", w * 0.09, (x, y, h + 1.55), gl, seg=10, rings=6)
    _crest(f"{prefix}Crest", x, y - (w / 2 + 0.03) * (1 if crest_face < 0 else -1), h * 0.32, M, gl, s=1.0, face=crest_face)


def _iron_rake(prefix, M, gl, x, pts, height, bay=0.62, rail=0.045, face=1):
    """A gothic cast-iron balustrade on a raking or level foot line (pts: (y, z) in order), in the plane x:
    a bottom rail, bars every bay, trefoil-headed pointed arches between them under a top rail, a gilt roundel in every
    other spandrel, a gilt collar on every fourth bar and a brass handrail on top."""
    iron = M["iron"]
    feet = []
    for (ya, za), (yb, zb) in zip(pts, pts[1:]):
        n = max(1, int(round((yb - ya) / bay)))
        for k in range(n):
            t = k / n
            feet.append((ya + (yb - ya) * t, za + (zb - za) * t))
    feet.append(pts[-1])
    P3 = lambda y, z: (x, y, z)
    tube(f"{prefix}Base", [P3(y, z + 0.1) for y, z in pts], 0.032, iron, square=True, poly=True)
    tube(f"{prefix}Top", [P3(y, z + height - 0.08) for y, z in pts], 0.035, iron, square=True, poly=True)
    tube(f"{prefix}Rail", [P3(y, z + height + 0.02) for y, z in pts], rail, M["brass"], poly=True)
    for k, (y, z) in enumerate(feet):
        tube(f"{prefix}Bar{k}", [P3(y, z + 0.1), P3(y, z + height - 0.08)], 0.026, iron, square=True, poly=True)
        if k % 4 == 0:
            sphere(f"{prefix}Collar{k}", 0.05, P3(y, z + height * 0.42), gl, seg=8, rings=5, scale=(1, 1, 1.6))
    # the arcade: a pointed arch in each bay, its springing following the rake
    for k, ((ya, za), (yb, zb)) in enumerate(zip(feet, feet[1:])):
        hw = (yb - ya) / 2
        if hw < 0.12:
            continue
        slope = (zb - za) / (yb - ya)
        yc, zc = (ya + yb) / 2, (za + zb) / 2
        zs, za_ = height - 0.48, height - 0.16
        arch = [(yc + u, zc + w + slope * u) for u, w in _pointed(hw - 0.005, zs, za_, 6)]
        tube(f"{prefix}Arch{k}", [P3(y, z) for y, z in arch], 0.016, iron, square=True, poly=True)
        # a trefoil in the head
        s = _mark()
        foil(f"{prefix}Tre{k}", 0, 0, zc + zs + (za_ - zs) * 0.2, hw * 0.42, iron, lobes=3, thick=0.01, centre=False)
        _xform(s, Matrix.Translation((x, yc, 0)) @ Matrix.Rotation(math.pi / 2 * face, 4, "Z"))
        if k % 2 == 1:
            s = _mark()
            foil(f"{prefix}Roundel{k}", 0, 0, zc + height * 0.3, 0.09, gl, thick=0.012)
            _xform(s, Matrix.Translation((x, yc, 0)) @ Matrix.Rotation(math.pi / 2 * face, 4, "Z"))


def _treads(prefix, steps, rise, run, inner, stone, dark, rnd, y0=None):
    """The stepped stone body (one solid, a stepped side profile) and a separate worn tread slab with a rounded nosing on
    every step, each a touch out of true. Returns (length, height)."""
    L, H = steps * run, steps * rise
    y0 = -L / 2 if y0 is None else y0
    prof = [(y0, 0.0)]
    for i in range(steps):
        prof += [(y0 + i * run, (i + 1) * rise - 0.14), (y0 + (i + 1) * run, (i + 1) * rise - 0.14)]
    prof += [(y0 + L, 0.0)]
    tprism(f"{prefix}Body", prof, 0, inner - 0.02, dark, plane="YZ", bevel=0.01)
    for i in range(steps):
        yf = y0 + i * run
        z = (i + 1) * rise
        dz = rnd.uniform(-0.012, 0.008)
        box(f"{prefix}Tread{i}", (inner - 0.06, run + 0.08, 0.15), (rnd.uniform(-0.01, 0.01), yf + run / 2 - 0.05, z - 0.075 + dz), stone,
            bevel=0.045, rot=(rnd.uniform(-0.004, 0.004), 0, rnd.uniform(-0.003, 0.003)))
    return L, H


def _cheek(prefix, sx, xc, cw, y0, L, rise, run, H, up, stone, dark, rnd, lancets=True):
    """A cheek wall along the flight: a raking top `up` above the nosings, a dark plinth course, a moulded raking coping
    with a bead below it, blind trefoil lancets on its outer face."""
    top = lambda y: rise + up + (H - rise) * min(1, max(0, (y - (y0 + run * 0.5)) / (L - run * 1.5)))
    prof = [(y0 - 0.4, 0), (y0 + L, 0), (y0 + L, H + up), (y0 + L - run, H + up), (y0 + run * 0.5, rise + up), (y0 - 0.4, rise + up)]
    tprism(f"{prefix}Wall", prof, sx * xc, cw, stone, plane="YZ", bevel=0.03)
    tprism(f"{prefix}Plinth", [(y0 - 0.45, 0), (y0 + L, 0), (y0 + L, 0.35), (y0 - 0.45, 0.35)], sx * xc, cw + 0.12, dark, plane="YZ", bevel=0.03)
    rake = [(y0 - 0.4, rise + up), (y0 + run * 0.5, rise + up), (y0 + L - run, H + up), (y0 + L, H + up)]
    band = [(y, z) for y, z in rake] + [(y, z + 0.22) for y, z in rake[::-1]]
    tprism(f"{prefix}Coping", band, sx * xc, cw + 0.2, stone, plane="YZ", bevel=0.05)
    for face in (-1, 1):
        tube(f"{prefix}Bead{face}", [(sx * xc + face * (cw / 2 + 0.02), y, z - 0.05) for y, z in rake], 0.045, dark, poly=True)
    if lancets:
        n = max(2, int(L / 1.7))
        for k in range(n):
            yc = y0 + 0.6 + (L - 1.0) * (k + 0.5) / n
            zt = top(yc) - 0.35
            z0 = max(0.55, zt - 2.6)
            if zt - z0 < 0.9:
                continue
            s = _mark()
            _lancet(f"{prefix}Lancet{k}", 0, 0, z0, 0.36, z0 + (zt - z0) * 0.62, zt, dark, thick=0.035)
            _side(s, sx * (xc + cw / 2 + 0.005), sx)
            # translate along the stair (the lancet was built at local x 0 = y 0)
            for ob in P.PARTS[s:]:
                ob.matrix_world = Matrix.Translation((0, yc, 0)) @ ob.matrix_world
    return rake


def _weather(prefix, steps, rise, run, inner, y0, moss, hol, stain, rnd):
    """Moss in the back corners of some treads and along the foot, a few hairline cracks on the risers, a stain."""
    pts = []
    for i in range(steps):
        if rnd.random() < 0.55:
            sx = rnd.choice((-1, 1))
            pts.append((sx * (inner / 2 - 0.12), y0 + (i + 1) * run - 0.15, (i + 1) * rise + 0.005))
    pts += [(rnd.uniform(-inner / 2, inner / 2), y0 - 0.05, 0.02) for _ in range(3)]
    _moss(f"{prefix}Moss", pts, moss, rnd, 0.1)
    for k in range(3):
        i = rnd.randrange(1, steps)
        _crack(f"{prefix}Crack{k}", (rnd.uniform(-inner / 3, inner / 3), y0 + i * run - 0.006, i * rise + 0.05 + rise * 0.3), (1, 0, 0.25), (0, 0, 1),
               rnd.uniform(0.5, 1.1), rnd, hol, n=5)


def _flight(M, steps, rise, run, inner, gl, rnd, cw=0.9, up=0.65, newels=True):
    """A stone flight: the treads, both cheeks, pinnacle newels at the foot, weathering. Returns (L, H, xc, y0, rakes)."""
    stone, dark = castle()
    L, H = steps * run, steps * rise
    y0 = -L / 2
    _treads("S", steps, rise, run, inner, stone, dark, rnd)
    xc = inner / 2 + cw / 2
    rakes = {}
    for sx in (-1, 1):
        rakes[sx] = _cheek(f"C{sx}", sx, xc, cw, y0, L, rise, run, H, up, stone, dark, rnd)
        if newels:
            _pin_newel(f"N{sx}", sx * xc, y0 - 0.55, M, stone, dark, gl, h=rise + up + 1.5, w=cw + 0.3)
    _weather("W", steps, rise, run, inner, y0, mossy(), hollow(), staining(), rnd)
    return L, H, xc, y0, rakes


def stair_stone(M):
    rnd = random.Random(201)
    gl = gilt()
    set_group("Main")
    _flight(M, 8, 0.75, 1.25, 6.0, gl, rnd)
    return _dims()


def stair_stone_railed(M):
    rnd = random.Random(202)
    gl = gilt()
    set_group("Main")
    L, H, xc, y0, rakes = _flight(M, 8, 0.75, 1.25, 6.0, gl, rnd)
    set_group("Rail")
    for sx in (-1, 1):
        foot = [(y, z + 0.22) for y, z in rakes[sx][1:]]
        _iron_rake(f"R{sx}", M, gl, sx * xc, foot, 2.3, face=sx)
        # a cast-iron newel at the head of the flight
        y, z = foot[-1]
        lathe(f"HeadPost{sx}", [(0, z), (0.13, z), (0.1, z + 0.25), (0.07, z + 2.2), (0.12, z + 2.32), (0.1, z + 2.45), (0, z + 2.47)], M["iron"],
              seg=12, loc=(sx * xc, y - 0.05, 0))
        sphere(f"HeadBall{sx}", 0.1, (sx * xc, y - 0.05, z + 2.56), gl, seg=12, rings=6)
    set_group("Main")
    return _dims()


def _recess_lancet(prefix, cx, y, z0, hw, zs, za, stone, dark, hol, cusp=True):
    """A carved lancet panel facing -Y at the face y: a dark recess, a raised stone frame round it with a trefoil head,
    a sloped sill."""
    pts = [(cx - hw, z0)] + [(cx + x, z) for x, z in _pointed(hw, zs, za, 10)] + [(cx + hw, z0)]
    tprism(f"{prefix}Recess", pts, y - 0.004, 0.012, hol)
    tube(f"{prefix}Frame", [(x, y - 0.03, z) for x, z in pts], 0.055, stone, closed=True, square=True, poly=True)
    if cusp:
        _foil(f"{prefix}Tre", cx, y - 0.03, zs + (za - zs) * 0.4, hw * 0.55, stone, lobes=3, thick=0.045)
    box(f"{prefix}Sill", (hw * 2 + 0.3, 0.16, 0.12), (cx, y - 0.07, z0 - 0.02), dark, bevel=0.03)


def stair_landing(M):
    rnd = random.Random(203)
    stone, dark = castle()
    hol = hollow()
    gl = gilt()
    S, H = 7.6, 6.0
    set_group("Main")
    # the core, a two-step plinth with a weathered top, the corner buttresses
    box("Core", (S, S, H - 0.6), (0, 0, (H - 0.6) / 2), stone, bevel=0.03)
    box("Plinth", (S + 0.36, S + 0.36, 0.45), (0, 0, 0.225), dark, bevel=0.06)
    box("PlinthStep", (S + 0.18, S + 0.18, 0.2), (0, 0, 0.55), dark, bevel=0.05)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (S / 2 - 0.35), sy * (S / 2 - 0.35)
            box(f"Butt{sx}{sy}", (1.2, 1.2, H - 0.6), (x, y, (H - 0.6) / 2), stone, bevel=0.04)
            box(f"ButtStep{sx}{sy}", (1.34, 1.34, 0.22), (x, y, 2.4), dark, bevel=0.06)
            box(f"ButtCap{sx}{sy}", (1.4, 1.4, 0.26), (x, y, H - 0.47), dark, bevel=0.06)
            _spirelet(f"Pin{sx}{sy}", x, y, H - 0.34, 1.9, 0.7, stone, crockets=3)
            sphere(f"PinGilt{sx}{sy}", 0.07, (x, y, H - 0.34 + 1.98), gl, seg=10, rings=6)
    set_group("Faces")
    # each face: three carved lancet panels between the buttresses, the middle one framing a crest under a hood moulding
    for k in range(4):
        s = _mark()
        f = -S / 2
        for cx in (-1.75, 1.75):
            _recess_lancet(f"Side{k}{cx}", cx, f, 1.0, 0.62, 3.0, 4.35, stone, dark, hol)
        _recess_lancet(f"Mid{k}", 0, f, 1.0, 0.85, 3.25, 4.75, stone, dark, hol, cusp=False)
        hood = [(x, f - 0.07, z) for x, z in _pointed(1.0, 3.2, 4.95, 12)]
        tube(f"Hood{k}", hood, 0.06, dark, square=True, poly=True)
        for sx in (-1, 1):
            sphere(f"HoodStop{k}{sx}", 0.09, (sx * 1.0, f - 0.09, 3.12), stone, seg=8, rings=5, scale=(1, 0.7, 1.2))
        _crest(f"Crest{k}", 0, f - 0.035, 2.75, M, gl, s=1.9)
        # the corbel table: little corbels with pointed arches between, under the cornice
        n = 11
        for j in range(n + 1):
            x = -2.75 + 5.5 * j / n
            box(f"Corbel{k}{j}", (0.14, 0.2, 0.24), (x, f - 0.1, H - 1.05), dark, bevel=0.03)
            if j < n:
                xm = x + 5.5 / n / 2
                arch = [(xm + u, f - 0.12, z) for u, z in _pointed(5.5 / n / 2 - 0.07, H - 1.12, H - 0.92, 4)]
                tube(f"CorbArch{k}{j}", arch, 0.03, stone, square=True, poly=True)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    set_group("Main")
    box("CornBed", (S + 0.3, S + 0.3, 0.12), (0, 0, H - 0.8), dark, bevel=0.03)
    box("Cornice", (S + 0.46, S + 0.46, 0.3), (0, 0, H - 0.6), stone, bevel=0.07)
    for k in range(4):
        s = _mark()
        tube(f"CornBead{k}", [(-S / 2 - 0.25, -S / 2 - 0.25, H - 0.74), (S / 2 + 0.25, -S / 2 - 0.25, H - 0.74)], 0.05, dark, poly=True)
        _xform(s, Matrix.Rotation(k * math.pi / 2, 4, "Z"))
    # the floor: random-run worn flagstones over a dark joint bed, a crimson and gilt quatrefoil medallion in the middle
    set_group("Floor")
    box("JointBed", (S + 0.3, S + 0.3, 0.12), (0, 0, H - 0.4), hol, bevel=0.01)
    half = S / 2 + 0.15
    y = -half
    while y < half - 0.05:
        d = min(rnd.choice((1.1, 1.3, 1.5, 1.7)), half - y)
        x = -half
        while x < half - 0.05:
            w = min(rnd.choice((1.2, 1.5, 1.8, 2.2, 2.6)), half - x)
            cx, cy = x + w / 2, y + d / 2
            if not (abs(cx) < 1.3 and abs(cy) < 1.3):
                box(f"Flag{x:.1f}{y:.1f}", (w - 0.05, d - 0.05, 0.28), (cx, cy, H - 0.2 + rnd.uniform(-0.012, 0.006)), stone, bevel=0.045,
                    rot=(rnd.uniform(-0.003, 0.003), rnd.uniform(-0.003, 0.003), rnd.uniform(-0.004, 0.004)))
            x += w
        y += d
    box("CentreSlab", (2.55, 2.55, 0.28), (0, 0, H - 0.2), stone, bevel=0.05)
    lathe("Medallion", [(0, H - 0.06), (1.05, H - 0.06), (1.05, H + 0.0), (0, H + 0.0)], dark, seg=48)
    hoop("MedalRing", (0, 0, H + 0.004), 1.0, "Z", gl, thick=0.035)
    hoop("MedalRing2", (0, 0, H + 0.004), 0.82, "Z", gl, thick=0.022)
    prism("MedalField", [(math.cos(a) * 0.8, math.sin(a) * 0.8) for a in [k / 32 * 2 * math.pi for k in range(32)]], H - 0.01, 0.015, M["crimson"],
          plane="XY")
    s = _mark()
    foil("MedalFoil", 0, 0, 0, 0.5, gl, thick=0.03)
    _xform(s, Matrix.Translation((0, 0, H + 0.012)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        sphere(f"MedalStud{k}", 0.06, (math.cos(a) * 0.91, math.sin(a) * 0.91, H + 0.01), gl, seg=8, rings=4, scale=(1, 1, 0.5))
    # moss in the joints and at the foot, a crack or two
    _moss("MossTop", [(rnd.uniform(-3.3, 3.3), rnd.uniform(-3.3, 3.3), H + 0.0) for _ in range(6)], mossy(), rnd, 0.08)
    set_group("Main")
    _moss("MossFoot", [(rnd.uniform(-3.4, 3.4), sy * (S / 2 + 0.2), 0.46) for sy in (-1, 1) for _ in range(3)], mossy(), rnd, 0.11)
    _crack("Crack", (-2.4, -S / 2 - 0.006, 1.4), (0.25, 0, 1), (1, 0, 0), 1.3, rnd, hol)
    _crack("Crack2", (S / 2 + 0.006, 1.2, 4.6), (0, 0.3, -1), (0, 1, 0), 0.9, rnd, hol)
    # two gas lanterns on scrolled iron brackets from the front buttresses
    set_group("Lamps")
    for sx in (-1, 1):
        x, yb = sx * (S / 2 - 0.35), -S / 2 - 0.25
        box(f"LampPlate{sx}", (0.32, 0.05, 0.6), (x, yb - 0.02, 3.9), M["iron"], bevel=0.01)
        tube(f"LampArm{sx}", [(x, yb - 0.05, 4.05), (x, yb - 0.4, 4.1), (x, yb - 0.75, 4.05)], 0.035, M["iron"], square=True)
        tube(f"LampCurl{sx}", [(x, yb - 0.05, 3.7), (x, yb - 0.3, 3.75), (x, yb - 0.45, 3.9), (x, yb - 0.38, 4.02)], 0.022, M["iron"])
        lathe(f"LampCup{sx}", [(0, 4.03), (0.09, 4.03), (0.11, 4.07), (0.09, 4.1), (0, 4.1)], M["iron"], seg=12, loc=(x, yb - 0.75, 0))
        hex_lantern(f"L{sx}", M, gl, Matrix.Translation((x, yb - 0.75, 4.1 + 0.3 * 0.62)) @ Matrix.Scale(0.62, 4))
    set_group("Main")
    return _dims()


def stair_grand(M):
    rnd = random.Random(204)
    stone, dark = castle()
    gl = gilt()
    runner = flat("Runner", (0.2, 0.012, 0.022), 0.9, dirt=0.5)
    border = flat("RunnerBorder", (0.45, 0.32, 0.09), 0.55, metal=0.2, dirt=0.4)
    steps, rise, run, inner = 10, 0.6, 1.3, 12.0
    set_group("Main")
    L, H, xc, y0, rakes = _flight(M, steps, rise, run, inner, gl, rnd, cw=1.1, up=0.55, newels=False)
    # tall newel pedestals at the foot with crests, carrying lamp standards
    for sx in (-1, 1):
        _pin_newel(f"N{sx}", sx * xc, y0 - 0.75, M, stone, dark, gl, h=3.2, w=1.6, pinnacle=False)
    # the runner over every tread and riser: crimson, gilt borders, a gilt quatrefoil on every tread, brass rods
    set_group("Runner")
    rw = 6.0
    for i in range(steps):
        yf = y0 + i * run
        z = (i + 1) * rise
        box(f"RunTread{i}", (rw, run - 0.06, 0.03), (0, yf + run / 2 - 0.02, z + 0.014), runner, bevel=0.008)
        box(f"RunRiser{i}", (rw, 0.03, rise - 0.1), (0, yf - 0.075, z - rise / 2 - 0.03), runner, bevel=0.008)
        for sx in (-1, 1):
            box(f"RunEdge{i}{sx}", (0.2, run - 0.06, 0.034), (sx * (rw / 2 - 0.16), yf + run / 2 - 0.02, z + 0.017), border, bevel=0.006)
        s = _mark()
        foil(f"RunFoil{i}", 0, 0, 0, 0.24, gl, thick=0.02)
        _xform(s, Matrix.Translation((0, yf + run / 2, z + 0.035)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
        tube(f"Rod{i}", [(-rw / 2 - 0.15, yf - 0.06, z - rise + 0.07), (rw / 2 + 0.15, yf - 0.06, z - rise + 0.07)], 0.025, M["brass"], poly=True)
        for sx in (-1, 1):
            sphere(f"RodEye{i}{sx}", 0.045, (sx * (rw / 2 + 0.2), yf - 0.06, z - rise + 0.07), gl, seg=8, rings=4)
    box("RunFoot", (rw, 1.0, 0.03), (0, y0 - 0.5, 0.015), runner, bevel=0.008)
    set_group("Rail")
    for sx in (-1, 1):
        foot = [(y, z + 0.22) for y, z in rakes[sx][1:]]
        _iron_rake(f"R{sx}", M, gl, sx * xc, foot, 2.5, bay=0.82, rail=0.06, face=sx)
    for sx in (-1, 1):
        x, y = sx * xc, y0 - 0.75
        lathe(f"Standard{sx}", [(0, 3.2), (0.24, 3.2), (0.2, 3.4), (0.12, 3.55), (0.1, 4.6), (0.15, 4.7), (0.12, 4.8), (0, 4.8)], M["iron"], seg=16,
              loc=(x, y, 0))
        hex_lantern(f"L{sx}", M, gl, Matrix.Translation((x, y, 4.8 + 0.3 * 0.95)) @ Matrix.Scale(0.95, 4))
    set_group("Main")
    return _dims()


def stair_spiral(M):
    rnd = random.Random(205)
    stone, dark = castle()
    gl = gilt()
    n, H, R, r0 = 20, 12.0, 4.0, 0.6
    rise = H / n
    set_group("Main")
    # the newel: a clustered shaft on an octagonal base, a moulded capital, a pinnacle
    lathe("Base", [(0, 0), (1.0, 0), (1.0, 0.35), (0.85, 0.5), (0.75, 0.55), (0, 0.55)], dark, seg=8)
    lathe("Shaft", [(0, 0.5), (r0, 0.5), (r0, H + 0.6), (0, H + 0.6)], stone, seg=48, flute=(8, 0.22))
    for z in (H * 0.33, H * 0.66):
        hoop(f"ShaftBand{z:.0f}", (0, 0, z), r0 * 0.98, "Z", dark, thick=0.05)
    lathe("Capital", [(0, H + 0.55), (r0 + 0.05, H + 0.55), (r0 + 0.3, H + 0.8), (r0 + 0.35, H + 0.95), (0, H + 0.95)], dark, seg=24)
    _spirelet("Pin", 0, 0, H + 0.95, 1.6, 0.6, stone, crockets=3)
    # the treads: wedge slabs with a rounded nosing, a soffit block under each
    for i in range(n):
        a0 = i / n * 2 * math.pi - math.pi / 2
        a1 = (i + 1.04) / n * 2 * math.pi - math.pi / 2
        poly = [(math.cos(a0) * (r0 - 0.05), math.sin(a0) * (r0 - 0.05))]
        poly += [(math.cos(a0 + (a1 - a0) * t) * R, math.sin(a0 + (a1 - a0) * t) * R) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        poly += [(math.cos(a1) * (r0 - 0.05), math.sin(a1) * (r0 - 0.05))]
        z = rise * (i + 1) + rnd.uniform(-0.01, 0.005)
        tprism(f"Tread{i}", poly, z - 0.16, 0.16, stone, plane="XY", bevel=0.04)
        tprism(f"Soffit{i}", poly, z - rise - 0.02, rise - 0.14, dark, plane="XY", bevel=0.01)
    # the head landing: a quarter-turn slab at the top
    poly = [(0, 0)] + [(math.cos(-math.pi / 2 + k / 8 * math.pi / 2) * R, math.sin(-math.pi / 2 + k / 8 * math.pi / 2) * R) for k in range(9)]
    tprism("HeadSlab", poly, H - 0.16 + rise, 0.16, stone, plane="XY", bevel=0.04)
    pts = []
    for i in range(n):
        if rnd.random() < 0.4:
            a = (i + 0.5) / n * 2 * math.pi - math.pi / 2
            pts.append((math.cos(a) * (r0 + 0.2), math.sin(a) * (r0 + 0.2), rise * (i + 1) + 0.005))
    _moss("Moss", pts, mossy(), rnd, 0.09)
    set_group("Rail")
    rail = []
    for i in range(n):
        a = (i + 0.5) / n * 2 * math.pi - math.pi / 2
        z = rise * (i + 1)
        x, y = math.cos(a) * (R - 0.15), math.sin(a) * (R - 0.15)
        tube(f"Bal{i}", [(x, y, z), (x, y, z + 2.45)], 0.03, M["iron"], square=True, poly=True)
        sphere(f"Collar{i}", 0.05, (x, y, z + 1.0), gl, seg=8, rings=5, scale=(1, 1, 1.5)) if i % 3 == 0 else None
        if i % 2 == 1 and i < n - 1:
            s = _mark()
            foil(f"Roundel{i}", 0, 0, 0, 0.16, gl, thick=0.014)
            ap = (i + 1.0) / n * 2 * math.pi - math.pi / 2
            _xform(s, Matrix.Translation((math.cos(ap) * (R - 0.15), math.sin(ap) * (R - 0.15), z + rise * 0.5 + 1.95)) @
                   Matrix.Rotation(ap + math.pi / 2, 4, "Z"))
        rail.append((x, y, z + 2.45))
    tube("Handrail", rail, 0.045, M["brass"])
    tube("MidRail", [(x, y, z - 0.9) for x, y, z in rail], 0.022, M["iron"])
    tube("LowRail", [(x, y, z - 2.3) for x, y, z in rail], 0.022, M["iron"])
    sphere("RailEnd", 0.08, rail[-1], gl, seg=10, rings=5)
    set_group("Main")
    return _dims()


def stair_iron(M):
    gl = gilt()
    iron, brass = M["iron"], M["brass"]
    steps, rise, run, W = 10, 0.8, 0.9, 4.0
    L, H = steps * run, steps * rise
    y0 = -L / 2
    plate = flat("Chequer", (0.11, 0.105, 0.115), 0.45, metal=0.85, wear=0.5, dirt=0.6)
    set_group("Main")
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.06)
        prism(f"Stringer{sx}", [(y0, 0), (y0 + 0.5, 0), (y0 + L, H - 0.6), (y0 + L, H + 0.12), (y0 + L - 0.4, H + 0.12), (y0, 0.55)], x, 0.1, iron,
              plane="YZ", bevel=0.01)
        # quatrefoils pierced along the stringer, rivets
        for k in range(1, steps):
            yy = y0 + k * run
            zz = (yy - y0) / L * (H - 0.05) + 0.1
            s = _mark()
            foil(f"SFoil{sx}{k}", 0, 0, zz, 0.16, gl if k % 3 == 0 else iron, thick=0.014)
            _xform(s, Matrix.Translation((x + sx * 0.055, yy, 0)) @ Matrix.Rotation(math.pi / 2 * sx, 4, "Z"))
    for i in range(steps):
        yf = y0 + i * run
        z = rise * (i + 1)
        box(f"Tread{i}", (W, run + 0.05, 0.07), (0, yf + run / 2, z - 0.035), plate, bevel=0.01)
        for j in range(9):
            for k in range(3):
                box(f"Diamond{i}{j}{k}", (0.12, 0.05, 0.02), (-W / 2 + 0.25 + j * 0.44, yf + 0.2 + k * 0.25, z + 0.008), plate, bevel=0.0,
                    rot=(0, 0, math.pi / 4 * (1 if (j + k) % 2 else -1)))
        box(f"Nosing{i}", (W, 0.06, 0.12), (0, yf + 0.0, z - 0.06), brass, bevel=0.01)
    set_group("Rail")
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.06)
        foot = [(y0 + 0.3, rise), (y0 + L - 0.3, H)]
        _iron_rake(f"R{sx}", M, gl, x, foot, 2.5, face=sx)
        for (y, z) in foot:
            sphere(f"Ball{sx}{y:.1f}", 0.07, (x, y, z + 2.62), gl, seg=10, rings=5)
    set_group("Main")
    return _dims()


# ------------------------------------------------------------------ bridges

def _lamp_pier(prefix, M, gl, x, y, z, lights):
    lathe(f"{prefix}Post", [(0, z), (0.16, z), (0.14, z + 0.2), (0.08, z + 0.35), (0.07, z + 1.4), (0.12, z + 1.5), (0.1, z + 1.6), (0, z + 1.6)],
          M["iron"], seg=16, loc=(x, y, 0))
    lights += hex_lantern(f"{prefix}L", M, gl, Matrix.Translation((x, y, z + 1.6 + 0.3 * 0.85)) @ Matrix.Scale(0.85, 4))


def _parapet(prefix, x0, x1, zf, y, stone, dark, rnd, bay=1.45, face=-1):
    """A pierced gothic parapet in the courtyard Balustrade's manner, following a deck line zf(x) at y: a plinth rail,
    mullions, trefoil-headed lancet arches (traceried on the outer face), a moulded top rail with a drip, moss."""
    n = max(2, int(round((x1 - x0) / bay)))
    xs = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    lo = [(x, zf(x)) for x in xs]
    tprism(f"{prefix}Plinth", lo + [(x, z + 0.45) for x, z in lo[::-1]], y, 0.62, dark, bevel=0.03)
    for k, x in enumerate(xs):
        if 0 < k < n:
            box(f"{prefix}Mullion{k}", (0.16, 0.34, 1.2), (x, y, zf(x) + 0.45 + 0.6), stone, bevel=0.025)
    for k in range(n):
        cx = (xs[k] + xs[k + 1]) / 2
        z0 = zf(cx) + 0.45
        hw = (xs[k + 1] - xs[k]) / 2 - 0.08
        for f in (-1, 1):
            _lancet(f"{prefix}Arch{k}{f}", cx, y + f * 0.11, z0, hw, z0 + 0.7, z0 + 1.17, stone, thick=0.07, cusp=(f == face))
    top = [(x, z + 1.65) for x, z in lo]
    tprism(f"{prefix}Rail", top + [(x, z + 0.3) for x, z in top[::-1]], y, 0.72, stone, bevel=0.04)
    tprism(f"{prefix}Drip", top + [(x, z - 0.05) for x, z in top[::-1]], y, 0.78, dark, bevel=0.012)
    mp = []
    for _ in range(5):
        x = rnd.uniform(x0 + 0.3, x1 - 0.3)
        mp.append((x, y + rnd.choice((-1, 1)) * 0.33, zf(x) + 0.46))
    for _ in range(3):
        x = rnd.uniform(x0 + 0.3, x1 - 0.3)
        mp.append((x, y + rnd.uniform(-0.2, 0.2), zf(x) + 1.96))
    _moss(f"{prefix}Moss", mp, mossy(), rnd, 0.08)


def _end_pier(prefix, x, y, z_deck, M, stone, dark, gl, lights, crest=True):
    """A square stone pier at a parapet's end: plinth, a lancet panel on its outer face, a crest, a cap and a lantern."""
    h = z_deck + 2.4
    box(f"{prefix}Shaft", (1.3, 1.3, h - z_deck), (x, y, z_deck + (h - z_deck) / 2), stone, bevel=0.04)
    box(f"{prefix}Foot", (1.45, 1.45, 0.3), (x, y, z_deck + 0.15), dark, bevel=0.04)
    box(f"{prefix}Cap", (1.55, 1.55, 0.25), (x, y, h + 0.12), dark, bevel=0.05)
    side = -1 if y < 0 else 1
    s = _mark()
    _lancet(f"{prefix}Lancet", 0, 0, z_deck + 0.45, 0.4, z_deck + 1.5, z_deck + 2.05, dark, thick=0.035)
    _xform(s, Matrix.Translation((x, y + side * 0.655, 0)) @ Matrix.Rotation(0 if side < 0 else math.pi, 4, "Z"))
    if crest:
        _crest(f"{prefix}Crest", x, y + side * 0.69, z_deck + 1.15, M, gl, s=0.9, face=side)
    _lamp_pier(f"{prefix}P", M, gl, x, y, h + 0.25, lights)


def bridge_stone_arch(M):
    rnd = random.Random(206)
    stone, dark = castle()
    gl = gilt()
    st = _stone(M)
    Lh, W, deck0, hump = 12.0, 7.6, 3.6, 0.9
    span, srise = 8.0, 3.0
    def deck_z(x):
        return deck0 + hump * (1 - (x / Lh) ** 2)
    set_group("Wall")
    outline = [(-Lh, 0.0), (-span, 0.0)]
    for i in range(1, 24):
        a = math.pi * (1 - i / 24)
        outline.append((math.cos(a) * span, math.sin(a) * srise))
    outline += [(span, 0.0), (Lh, 0.0)]
    outline += [(x, deck_z(x)) for x in [Lh - k * 1.5 for k in range(17)]]
    tprism("Body", outline, 0.0, W, st, bevel=0.03)
    set_group("Main")
    lights = []
    for sy in (-1, 1):
        yf = sy * (W / 2 + 0.04)
        # the arch ring: dark voussoirs, a keystone with a crimson crest, a hood moulding over it
        for i in range(17):
            a0, a1 = math.pi * (1 - i / 17) - 0.004, math.pi * (1 - (i + 1) / 17) + 0.004
            ring = [(math.cos(a0) * span, math.sin(a0) * srise), (math.cos(a1) * span, math.sin(a1) * srise),
                    (math.cos(a1) * (span + 0.75), math.sin(a1) * (srise + 0.75)), (math.cos(a0) * (span + 0.75), math.sin(a0) * (srise + 0.75))]
            tprism(f"Vous{sy}{i}", ring, yf, 0.12, dark if i != 8 else stone, bevel=0.015)
        hood = [(math.cos(math.pi * (1 - t / 24)) * (span + 0.85), sy * (W / 2 + 0.08), math.sin(math.pi * (1 - t / 24)) * (srise + 0.85))
                for t in range(25)]
        tube(f"Hood{sy}", hood, 0.07, stone, square=True, poly=True)
        _crest(f"Key{sy}", 0, sy * (W / 2 + 0.13), srise + 0.38, M, gl, s=0.95, face=sy)
        # the string course under the parapet, then the pierced parapet itself
        tube(f"String{sy}", [(x, sy * (W / 2 + 0.06), deck_z(x) - 0.15) for x in [-Lh + 0.9 + k * 1.35 for k in range(17)]], 0.11, dark,
             square=True, poly=True)
        set_group(f"Parapet{'L' if sy < 0 else 'R'}")
        _parapet(f"Para{sy}", -Lh + 1.3, Lh - 1.3, deck_z, sy * (W / 2 - 0.36), stone, dark, rnd, face=sy)
        set_group("Main")
        set_group("Piers")
        for sx in (-1, 1):
            _end_pier(f"E{sx}{sy}", sx * (Lh - 0.65), sy * (W / 2 - 0.36), deck_z(sx * Lh), M, stone, dark, gl, lights)
        set_group("Main")
    # weathering on the spandrels and the ring
    for sy in (-1, 1):
        for k in range(2):
            _crack(f"Crack{sy}{k}", (rnd.uniform(-6, 6), sy * (W / 2 + 0.105), rnd.uniform(1.5, 2.6)), (0.3, 0, 1), (1, 0, 0), 0.7, rnd, hollow())
        _moss(f"MossFoot{sy}", [(rnd.choice((-1, 1)) * rnd.uniform(8.2, 11.5), sy * (W / 2 + 0.05), 0.03) for _ in range(4)], mossy(), rnd, 0.14)
    return _dims()


def bridge_iron(M):
    gl = gilt()
    st = _stone(M)
    iron, cr = M["iron"], M["crimson"]
    Lh, W, deck = 12.0, 5.0, 3.0
    stone, dark = castle()
    rnd = random.Random(207)
    set_group("Main")
    for sx in (-1, 1):
        box(f"Abutment{sx}", (2.4, W + 1.6, deck), (sx * (Lh - 1.2), 0, deck / 2), stone, bevel=0.05)
        box(f"AbutCap{sx}", (2.7, W + 1.9, 0.3), (sx * (Lh - 1.2), 0, deck + 0.0), dark, bevel=0.05)
        for sy in (-1, 1):
            s = _mark()
            _lancet(f"AbutLancet{sx}{sy}", 0, 0, 0.4, 0.55, 1.6, 2.4, dark, thick=0.04)
            _xform(s, Matrix.Translation((sx * (Lh - 1.2), sy * (W / 2 + 0.805), 0)) @ Matrix.Rotation(0 if sy < 0 else math.pi, 4, "Z"))
        _moss(f"AbutMoss{sx}", [(sx * (Lh - 1.2) + rnd.uniform(-1, 1), sy * (W / 2 + 0.82), 0.04) for sy in (-1, 1) for _ in range(2)], mossy(), rnd, 0.12)
    for k in range(13):
        x = -9.6 + k * 1.6
        box(f"Cross{k}", (0.16, W + 0.4, 0.3), (x, 0, deck - 0.12), iron, bevel=0.015)
    plate = flat("DeckPlate", (0.12, 0.115, 0.12), 0.5, metal=0.8, wear=0.5, dirt=0.7)
    box("Deck", (Lh * 2 - 4.6, W, 0.1), (0, 0, deck + 0.08), plate, bevel=0.01)
    for k in range(40):
        box(f"Plank{k}", (0.03, W - 0.1, 0.02), (-9.75 + k * 0.5, 0, deck + 0.14), iron, bevel=0.005)
    gh = 2.4
    set_group("Girders")
    for sy in (-1, 1):
        y = sy * (W / 2 + 0.05)
        x0, x1 = -Lh + 2.3, Lh - 2.3
        for z in (deck + 0.15, deck + gh):
            tube(f"Chord{sy}{z:.1f}", [(x0, y, z), (x1, y, z)], 0.09, cr, square=True, poly=True)
        n = 24
        for k in range(n):
            xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
            tube(f"LatA{sy}{k}", [(xa, y, deck + 0.2), (xb, y, deck + gh - 0.05)], 0.035, cr, square=True, poly=True)
            tube(f"LatB{sy}{k}", [(xa, y, deck + gh - 0.05), (xb, y, deck + 0.2)], 0.035, cr, square=True, poly=True)
            if k % 4 == 0:
                tube(f"Post{sy}{k}", [(xa, y, deck + 0.15), (xa, y, deck + gh)], 0.07, cr, square=True, poly=True)
                s = _mark()
                foil(f"Boss{sy}{k}", 0, 0, deck + gh / 2, 0.16, gl, thick=0.018)
                _xform(s, Matrix.Translation((xa, y + sy * 0.1, 0)) @ Matrix.Rotation(0 if sy < 0 else math.pi, 4, "Z"))
                tube(f"Spear{sy}{k}", [(xa, y, deck + gh), (xa, y, deck + gh + 0.28)], 0.025, iron, square=True, poly=True)
                cone(f"SpearTip{sy}{k}", 0.06, 0.0, 0.16, (xa, y, deck + gh + 0.36), gl, verts=4)
        tube(f"Handrail{sy}", [(x0, y, deck + gh + 0.12), (x1, y, deck + gh + 0.12)], 0.06, M["brass"], poly=True)
        rib = [(x, y, deck - 0.3 - 1.6 * (1 - (x / 9.6) ** 2)) for x in [-9.6 + k * 0.8 for k in range(25)]]
        tube(f"Rib{sy}", rib, 0.09, cr, square=True)
        for k in range(-5, 6):
            x = k * 1.6
            zr = deck - 0.3 - 1.6 * (1 - (x / 9.6) ** 2)
            h = (deck - 0.3) - zr
            if h > 0.3:
                hoop(f"Ring{sy}{k}", (x, y, zr + h / 2), h / 2 * 0.9, "Y", iron, thick=0.035)
    set_group("Main")
    lights = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (Lh - 2.15), sy * (W / 2 + 0.05)
            box(f"EndPost{sx}{sy}", (0.3, 0.3, gh + 0.4), (x, y, deck + (gh + 0.4) / 2), cr, bevel=0.02)
            _lamp_pier(f"P{sx}{sy}", M, gl, x, y, deck + gh + 0.4, lights)
    return _dims()


def bridge_deck(M):
    rnd = random.Random(208)
    stone, dark = castle()
    st = _stone(M)
    Lh, W, D = 8.0, 7.6, 1.6
    set_group("Wall")
    box("Slab", (Lh * 2, W, D), (0, 0, D / 2), st, bevel=0.03)
    set_group("Main")
    for sy in (-1, 1):
        box(f"String{sy}", (Lh * 2, 0.25, 0.25), (0, sy * (W / 2 + 0.08), D - 0.15), dark, bevel=0.04)
        for x in (-4.0, 4.0):
            cyl(f"Spout{sy}{x}", 0.08, 0.6, (x, sy * (W / 2 + 0.25), D - 0.45), M["iron"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
        _parapet(f"Para{sy}", -Lh, Lh, lambda x: D, sy * (W / 2 - 0.36), stone, dark, rnd, face=sy)
        _crack(f"Crack{sy}", (rnd.uniform(-6, 6), sy * (W / 2 + 0.005), 0.5), (0.3, 0, 1), (1, 0, 0), 0.6, rnd, hollow())
    return _dims()


def bridge_pier(M):
    rnd = random.Random(209)
    stone, dark = castle()
    gl = gilt()
    st = _stone(M)
    H, wx, wy = 16.0, 3.0, 7.6
    set_group("Wall")
    box("Shaft", (wx, wy, H), (0, 0, H / 2), st, bevel=0.04)
    for sy in (-1, 1):
        tprism(f"Cutwater{sy}", [(-wx / 2, 0), (wx / 2, 0), (0, sy * 1.8)], 0, H - 2.0, st, plane="XY", bevel=0.03)
        _xform(len(P.PARTS) - 1, Matrix.Translation((0, sy * wy / 2, 0)))
    set_group("Main")
    for z in (0.0, H * 0.45):
        box(f"Course{z:.0f}", (wx + 0.3, wy + 0.3, 0.4), (0, 0, z + 0.2), dark, bevel=0.05)
    box("Cap", (wx + 0.6, wy + 0.4, 0.5), (0, 0, H - 0.25), dark, bevel=0.05)
    box("CapBed", (wx + 0.3, wy + 0.2, 0.3), (0, 0, H - 0.65), stone, bevel=0.04)
    for sy in (-1, 1):
        # the cutwater's sloped cap (a pyramid over the triangle) and a carved crest on its point
        tprism(f"CutCap{sy}", [(-wx / 2, 0), (wx / 2, 0), (0, sy * 1.8)], H - 2.0, 0.25, dark, plane="XY", bevel=0.03)
        _xform(len(P.PARTS) - 1, Matrix.Translation((0, sy * wy / 2, 0)))
        _crest(f"Crest{sy}", 0, sy * (wy / 2 + 0.03), H - 1.2, M, gl, s=1.0, face=sy)
        for z in (4.0, 9.0):
            for sx in (-1, 1):
                box(f"Cramp{sy}{z}{sx}", (0.5, 0.06, 0.12), (sx * (wx / 2 - 0.35), sy * (wy / 2 + 0.03), z), M["iron"], bevel=0.01)
                sphere(f"CrampHead{sy}{z}{sx}", 0.06, (sx * (wx / 2 - 0.15), sy * (wy / 2 + 0.07), z), M["brass"], seg=8, rings=4)
        _moss(f"Moss{sy}", [(rnd.uniform(-1.2, 1.2), sy * (wy / 2 + rnd.uniform(0.2, 1.4)), 0.42) for _ in range(4)], mossy(), rnd, 0.14)
        _crack(f"Crack{sy}", (rnd.uniform(-1, 1), sy * (wy / 2 + 0.005), rnd.uniform(5, 12)), (0.2, 0, 1), (1, 0, 0), 1.4, rnd, hollow())
    return _dims()


P.TILED.update({f"{n}_Wall": ("NH_CastleStone", 8.0) for n in ("BridgeStoneArch", "BridgeIron", "BridgeDeck", "BridgePier")})

P.PREVIEW_PAD.update({"StairStone": 1.05, "StairStoneRailed": 1.05, "StairLanding": 1.15, "StairGrand": 1.05, "StairSpiral": 1.05, "StairIron": 1.1,
                      "BridgeStoneArch": 1.05, "BridgeIron": 1.05, "BridgeDeck": 1.1, "BridgePier": 1.05})

P.BUILD.update({
    "StairStone": stair_stone,
    "StairStoneRailed": stair_stone_railed,
    "StairLanding": stair_landing,
    "StairGrand": stair_grand,
    "StairSpiral": stair_spiral,
    "StairIron": stair_iron,
    "BridgeStoneArch": bridge_stone_arch,
    "BridgeIron": bridge_iron,
    "BridgeDeck": bridge_deck,
    "BridgePier": bridge_pier,
})
