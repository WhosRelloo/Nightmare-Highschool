"""Props batch 32 (2026-11-05): the school entrance kit for nh_props.py, in the stair kit's stone, carving and ironwork
(batch 20: the cheek walls' own castle stone baked whole, blind lancets, crocketed pinnacles, crimson and gilt crests, the
gothic cast-iron balustrade and brass handrail, gas lanterns). Every flight is 10 treads (rise 0.6, run 1.3) up to a
6-high porch, so the pieces join each other and the batch 20 stairs and landing.

Owner: "make an entrance/stairway to the school model same style and texture as the stairs" (straight, landing, split or
curved flights, lanterns and newels: "make all of them ... we'll see which we like more"), and "something really cool,
unique, and on themed with the game".

  EntranceFlight        the straight grand flight, 10 wide inside: carved cheeks under a pierced gothic stone parapet
                        (the bridges' balustrade, raked), crested newel pedestals with gas lanterns at the foot
  EntranceFlightBowed   a flared flight: bowed treads, 15 wide at the foot narrowing to 10 at the top, between splayed
                        cheeks with the iron balustrade, lantern pedestals at the foot
  EntranceSideFlightL   a 5-wide flight that climbs along the facade toward +X (balustrade on its open front side): a
                        pair with ...R either side of a porch makes a split stair
  EntranceSideFlightR   the same climbing toward -X
  EntrancePorch         an 18 x 9 flagstone porch 6 high: buttress piers with crocketed pinnacles and crests at its front
                        corners, lancet panels on its sides; its railings are separate pieces (RailFrontL, RailFrontR,
                        RailLeft, RailRight) so the builder can take one away where a flight joins
  EntranceNewelLantern  a crested newel pedestal with a lamp standard and a gas lantern, to stand anywhere

The Moonrise entrance (the showpiece; the school runs on the moon's phases):
  EntranceMoonStair     a 12-wide grand flight that climbs from the new moon to the full: every tread has a moon-phase
                        roundel inlaid in gilt on night-blue enamel, waxing as you climb; the cheeks carry moon roundels
                        instead of lancets; the iron balustrade wears gilt crescents; at its foot two tall piers each
                        hold up a gilt crescent with a raven perched on its horn, and hang a gas lantern
  EntranceMoonPorch     an 18.4 x 10 porch 6 high, flush with the stair's cheeks: a great moon dial is set in its floor
                        (the eight phases round a crimson and gilt star), crescent-crowned corner piers, traceried lancet
                        panels with crests on its sides, side railings as separate pieces
  EntranceMoonPortico   the doorway: clustered piers with crocketed pinnacles, a deep pointed arch with moulded rings,
                        a frieze lettered PER NOCTEM AD LUCEM in gilt, crests in the spandrels, a crocketed gable with a
                        full-moon rose window that glows at night (MoonGlow), a gilt crescent and a raven on the apex,
                        and a gas lantern hung on a chain in the arch

Front faces -Y, Z is up, the origin is at the bottom centre. Flights climb toward +Y (the bottom step at the front); the
side flights climb along X. Registered into nh_props.BUILD on import.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, _mark, _xform, _dims, flat
from nh_props_batch8 import castle, mossy, hollow, staining, _moss, _crack, _lancet, _foil, _spirelet, _pointed
from nh_props_batch9 import foil, raven
from nh_props_batch10 import gilt
from nh_props_batch19 import hex_lantern
from nh_props_batch20 import tprism, _side, _crest, _pin_newel, _iron_rake, _treads, _cheek, _weather, _recess_lancet, _parapet
from nh_props_batch22 import _lettering

STEPS, RISE, RUN = 10, 0.6, 1.3
H = STEPS * RISE           # 6.0, the porch height
L = STEPS * RUN            # 13.0, a flight's length


# ------------------------------------------------------------------ shared pieces

def night():
    return material("MoonNight", base=(0.016, 0.026, 0.075), rough=0.3, wear=0.08)


def raven_black():
    return flat("RavenBlack", (0.012, 0.012, 0.016), 0.55, dirt=0.3)


def _lit(r, k, n=14, waning=False):
    """The lit part of a moon disc of radius r, as an (u, v) outline: the bright limb (a semicircle on the right) and the
    terminator (an ellipse, k = cos of the phase angle: 1 new, 0 a half moon, -1 full). Waning mirrors it."""
    vs = [r * math.cos(math.pi * t / n) for t in range(n + 1)]                 # r .. -r
    limb = [(math.sqrt(max(0.0, r * r - v * v)), v) for v in vs]
    term = [(k * math.sqrt(max(0.0, r * r - v * v)), v) for v in vs[::-1]][1:-1]
    pts = limb + term
    return [(-u, v) for u, v in pts] if waning else pts


def _moon_flat(prefix, x, y, z, r, k, gl, nm, waning=False, ring=None, seg=24):
    """A moon-phase roundel lying flat (facing up) with its top at z: night enamel, the lit part in gilt, a gilt rim and
    an optional ring of dark stone round it."""
    if ring is not None:
        lathe(f"{prefix}Ring", [(0, z - 0.02), (r + 0.14, z - 0.02), (r + 0.14, z + 0.004), (0, z + 0.004)], ring, seg=seg, loc=(x, y, 0))
    lathe(f"{prefix}Night", [(0, z - 0.01), (r, z - 0.01), (r, z + 0.008), (0, z + 0.008)], nm, seg=seg, loc=(x, y, 0))
    if k < 0.99:
        pts = _lit(r * 0.97, k, waning=waning)
        tprism(f"{prefix}Lit", [(x + u, y + v) for u, v in pts], z + 0.006, 0.01, gl, plane="XY")
    hoop(f"{prefix}Rim", (x, y, z + 0.012), r, "Z", gl, thick=0.022)


def _moon_face(prefix, cx, y, cz, r, k, gl, nm, frame=None):
    """A moon-phase roundel on a face looking -Y at y: a recessed night disc, the lit part in gilt, a gilt rim and a raised
    stone frame."""
    tprism(f"{prefix}Night", [(cx + math.cos(a) * r, cz + math.sin(a) * r) for a in [t / 24 * 2 * math.pi for t in range(24)]], y + 0.004, 0.012,
           nm)
    if k < 0.99:
        tprism(f"{prefix}Lit", [(cx + u, cz + v) for u, v in _lit(r * 0.95, k)], y - 0.006, 0.01, gl)
    hoop(f"{prefix}Rim", (cx, y - 0.012, cz), r, "Y", gl, thick=0.02)
    if frame is not None:
        tube(f"{prefix}Frame", circle_pts(cx, y - 0.03, cz, r + 0.1, "Y", 24), 0.05, frame, closed=True, square=True, poly=True)


def _crescent(prefix, cx, y, cz, r, gl, depth=0.2, k=0.42):
    """A standing gilt crescent, horns up like a cradle, its face looking -Y at y; returns the tip of its left horn."""
    pts = [(v, -u) for u, v in _lit(r, k, n=18)]                 # turned so the horns point up and out
    tprism(f"{prefix}Crescent", [(cx + u, cz + v) for u, v in pts], y, depth, gl, bevel=0.015)
    return Vector((cx - r, y, cz))


def _finial_moon(prefix, x, y, z, s, gl, stone, dark, face=-1, perch=True, horn=-1):
    """A pier's crown: a moulded stone orb pedestal, a gilt crescent cradle on it (facing the front) and a raven on its
    left horn looking out."""
    lathe(f"{prefix}Ped", [(0, z), (0.42 * s, z), (0.42 * s, z + 0.12 * s), (0.28 * s, z + 0.22 * s), (0.2 * s, z + 0.4 * s), (0.3 * s, z + 0.5 * s),
                           (0.26 * s, z + 0.58 * s), (0, z + 0.58 * s)], dark, seg=20, loc=(x, y, 0))
    sphere(f"{prefix}Orb", 0.26 * s, (x, y, z + 0.8 * s), stone, seg=16, rings=8)
    m = _mark()
    tip = _crescent(f"{prefix}", 0, 0, 0, 0.62 * s, gl, depth=0.16 * s)
    if perch:
        hx = tip.x + 0.05 * s if horn < 0 else -tip.x - 0.05 * s
        raven(f"{prefix}Raven", (hx, 0, tip.z + 0.02), 0.6 * -horn, 1.9 * s, raven_black(), hollow())
    _xform(m, Matrix.Translation((x, y, z + 1.05 * s + 0.62 * s)) @ Matrix.Rotation(0 if face < 0 else math.pi, 4, "Z"))


def _bracket_lantern(prefix, x, yb, z, M, gl, out=-1, scale=0.62):
    """A gas lantern hung from a scrolled iron bracket on a face at y = yb, reaching toward `out` (-1 = -Y)."""
    box(f"{prefix}Plate", (0.32, 0.05, 0.6), (x, yb + out * 0.02, z - 0.15), M["iron"], bevel=0.01)
    tube(f"{prefix}Arm", [(x, yb + out * 0.05, z), (x, yb + out * 0.4, z + 0.05), (x, yb + out * 0.75, z)], 0.035, M["iron"], square=True)
    tube(f"{prefix}Curl", [(x, yb + out * 0.05, z - 0.35), (x, yb + out * 0.3, z - 0.3), (x, yb + out * 0.45, z - 0.15), (x, yb + out * 0.38, z - 0.03)],
         0.022, M["iron"])
    lathe(f"{prefix}Cup", [(0, z - 0.02), (0.09, z - 0.02), (0.11, z + 0.02), (0.09, z + 0.05), (0, z + 0.05)], M["iron"], seg=12, loc=(x, yb + out * 0.75, 0))
    hex_lantern(f"{prefix}L", M, gl, Matrix.Translation((x, yb + out * 0.75, z + 0.05 + 0.3 * scale)) @ Matrix.Scale(scale, 4))


def _lamp_standard(prefix, x, y, z, M, gl, scale=0.95):
    """An iron lamp standard on a pedestal top at z with a gas lantern (StairGrand's)."""
    lathe(f"{prefix}Standard", [(0, z), (0.24, z), (0.2, z + 0.2), (0.12, z + 0.35), (0.1, z + 1.4), (0.15, z + 1.5), (0.12, z + 1.6), (0, z + 1.6)],
          M["iron"], seg=16, loc=(x, y, 0))
    hex_lantern(f"{prefix}L", M, gl, Matrix.Translation((x, y, z + 1.6 + 0.3 * scale)) @ Matrix.Scale(scale, 4))


def _feet(pts, bay):
    """The bar positions _iron_rake puts along a foot line (so ornaments can sit on its bars)."""
    feet = []
    for (ya, za), (yb, zb) in zip(pts, pts[1:]):
        n = max(1, int(round((yb - ya) / bay)))
        for k in range(n):
            t = k / n
            feet.append((ya + (yb - ya) * t, za + (zb - za) * t))
    feet.append(pts[-1])
    return feet


def _interp(pts):
    """A piecewise-linear z(y) through (y, z) points."""
    def f(y):
        if y <= pts[0][0]:
            return pts[0][1]
        for (ya, za), (yb, zb) in zip(pts, pts[1:]):
            if y <= yb:
                return za + (zb - za) * (y - ya) / max(1e-6, yb - ya)
        return pts[-1][1]
    return f


def _level_rail(prefix, M, gl, a, b, z, along, at, height=2.3, face=1):
    """A level run of the gothic iron balustrade from a to b at height z: along "Y" in the plane x = at, or along "X" in
    the plane y = at."""
    s = _mark()
    _iron_rake(prefix, M, gl, 0.0, [(a, z), (b, z)], height, bay=(b - a) / max(1, round((b - a) / 0.66)), rail=0.05, face=face)
    if along == "Y":
        _xform(s, Matrix.Translation((at, 0, 0)))
    else:
        _xform(s, Matrix.Translation((0, at, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "Z"))


def _flags(prefix, x0, x1, y0, y1, z, stone, rnd, skip=None):
    """Worn random-run flagstones over x0..x1, y0..y1 with their tops at z; skip(cx, cy) leaves a hole (a medallion)."""
    y = y0
    while y < y1 - 0.05:
        d = min(rnd.choice((1.1, 1.3, 1.5, 1.7)), y1 - y)
        x = x0
        while x < x1 - 0.05:
            w = min(rnd.choice((1.2, 1.5, 1.8, 2.2, 2.6)), x1 - x)
            cx, cy = x + w / 2, y + d / 2
            if not (skip and skip(cx, cy)):
                box(f"{prefix}{x:.1f}_{y:.1f}", (w - 0.05, d - 0.05, 0.28), (cx, cy, z - 0.14 + rnd.uniform(-0.012, 0.006)), stone, bevel=0.045,
                    rot=(rnd.uniform(-0.003, 0.003), rnd.uniform(-0.003, 0.003), rnd.uniform(-0.004, 0.004)))
            x += w
        y += d


def _porch_body(W, D, stone, dark, hol, rnd, piers, pier_w, crown, M, gl, skip=None, side_panels=2, moon_panels=False):
    """A porch W x D, H high: a core on a two-step plinth, a cornice, the flagstone deck, piers at the front corners rising
    above the deck (crown "spire" or "moon"), traceried lancet panels with crests on both sides."""
    set_group("Main")
    box("Core", (W, D, H - 0.6), (0, 0, (H - 0.6) / 2), stone, bevel=0.03)
    set_group("Deck")
    box("Plinth", (W + 0.36, D + 0.18, 0.45), (0, -0.09, 0.225), dark, bevel=0.06)
    box("PlinthStep", (W + 0.18, D + 0.09, 0.2), (0, -0.045, 0.55), dark, bevel=0.05)
    box("CornBed", (W + 0.3, D + 0.15, 0.12), (0, -0.075, H - 0.8), dark, bevel=0.03)
    box("Cornice", (W + 0.46, D + 0.23, 0.3), (0, -0.115, H - 0.6), stone, bevel=0.07)
    box("JointBed", (W + 0.3, D + 0.15, 0.12), (0, -0.075, H - 0.4), hol, bevel=0.01)
    _flags("Flag", -W / 2 - 0.15, W / 2 + 0.15, -D / 2 - 0.15, D / 2, H, stone, rnd, skip=skip)
    set_group("Main")
    # the side faces: lancet panels (a crest in the middle one, or moon roundels), built facing -Y at y = -W/2 with the
    # face's run along local x, then turned onto the side (right: +90 deg; left: -90 deg with local x = -y)
    n = side_panels
    span = D - pier_w - 0.4
    ys = [-D / 2 + pier_w + 0.2 + span * (j + 0.5) / n for j in range(n)]
    hw = min(0.75, span / n / 2 - 0.25)
    for sx in (-1, 1):
        s = _mark()
        for j, yy in enumerate(ys):
            cx = yy if sx > 0 else -yy
            _recess_lancet(f"Side{sx}{j}", cx, -W / 2, 1.0, hw, 3.0, 4.35, stone, dark, hol, cusp=not moon_panels)
            if moon_panels:
                _moon_face(f"SideMoon{sx}{j}", cx, -W / 2 - 0.02, 3.55, hw * 0.55, [0.6, -0.2, -0.9][j % 3], gl, night())
            elif j == n // 2:
                _crest(f"SideCrest{sx}{j}", cx, -W / 2 - 0.035, 2.6, M, gl, s=1.3)
        _xform(s, Matrix.Rotation(math.pi / 2 * sx, 4, "Z"))
    # the front corner piers
    for sx in (-1, 1):
        x, y = sx * (W / 2 - pier_w / 2 + 0.1), -D / 2 + pier_w / 2 - 0.1
        top = H + (2.9 if crown == "moon" else 2.6)
        box(f"Pier{sx}", (pier_w, pier_w, top - 0.6), (x, y, (top - 0.6) / 2 + 0.3), stone, bevel=0.04)
        box(f"PierFoot{sx}", (pier_w + 0.2, pier_w + 0.2, 0.5), (x, y, 0.25), dark, bevel=0.06)
        box(f"PierBand{sx}", (pier_w + 0.16, pier_w + 0.16, 0.22), (x, y, H - 0.6), dark, bevel=0.05)
        box(f"PierCap{sx}", (pier_w + 0.24, pier_w + 0.24, 0.26), (x, y, top + 0.13 - 0.3), dark, bevel=0.06)
        s = _mark()
        _lancet(f"PierLancet{sx}", 0, 0, 1.0, pier_w * 0.28, 3.4, 4.6, dark, thick=0.035)
        _xform(s, Matrix.Translation((x, y - pier_w / 2 - 0.005, 0)))
        _crest(f"PierCrest{sx}", x, y - pier_w / 2 - 0.03, H + 1.25, M, gl, s=1.0)
        s = _mark()
        _lancet(f"PierLancetS{sx}", 0, 0, H + 0.5, pier_w * 0.22, H + 1.4, H + 2.0, dark, thick=0.03)
        _xform(s, Matrix.Translation((x + sx * (pier_w / 2 + 0.005), y, 0)) @ Matrix.Rotation(math.pi / 2 * sx, 4, "Z"))
        if crown == "moon":
            _finial_moon(f"PierMoon{sx}", x, y, top - 0.17, 1.15, gl, stone, dark, horn=sx)
        else:
            _spirelet(f"PierPin{sx}", x, y, top - 0.04, 2.0, pier_w * 0.62, stone, crockets=3)
            sphere(f"PierGilt{sx}", 0.08, (x, y, top - 0.04 + 2.08), gl, seg=10, rings=6)
    # weathering
    _moss("MossFoot", [(rnd.uniform(-W / 2 + 0.5, W / 2 - 0.5), -D / 2 - 0.2, 0.46) for _ in range(4)], mossy(), rnd, 0.11)
    _crack("Crack", (W / 2 + 0.006, rnd.uniform(-1, 2), 1.6), (0, 0.3, 1), (0, 1, 0), 1.2, rnd, hol)


# ------------------------------------------------------------------ the straight grand flight (stone parapet)

def entrance_flight(M):
    rnd = random.Random(321)
    stone, dark = castle()
    gl = gilt()
    inner, cw, up = 10.0, 1.1, 0.55
    set_group("Main")
    y0 = -L / 2
    _treads("S", STEPS, RISE, RUN, inner, stone, dark, rnd)
    xc = inner / 2 + cw / 2
    for sx in (-1, 1):
        rake = _cheek(f"C{sx}", sx, xc, cw, y0, L, RISE, RUN, H, up, stone, dark, rnd)
        zf = _interp([(y, z + 0.22) for y, z in rake])
        set_group("Parapet")
        s = _mark()
        _parapet(f"Par{sx}", y0 + 0.35, y0 + L, lambda x, zf=zf: zf(x), 0.0, stone, dark, rnd, bay=1.3, face=-1 if sx > 0 else 1)
        _xform(s, Matrix.Translation((sx * xc, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        set_group("Main")
    _weather("W", STEPS, RISE, RUN, inner, y0, mossy(), hollow(), staining(), rnd)
    for sx in (-1, 1):
        x, y = sx * xc, y0 - 0.75
        set_group("Newels")
        _pin_newel(f"N{sx}", x, y, M, stone, dark, gl, h=3.2, w=1.6, pinnacle=False)
        _lamp_standard(f"Lamp{sx}", x, y, 3.2, M, gl)
    set_group("Main")
    return _dims()


# ------------------------------------------------------------------ the bowed flight

def entrance_flight_bowed(M):
    rnd = random.Random(322)
    stone, dark = castle()
    gl = gilt()
    wb, wt, cw, up = 15.0, 10.0, 1.1, 0.6
    y0, yt = -L / 2, L / 2
    set_group("Main")

    def hw(y):
        return (wt + (wb - wt) * (yt - y) / L) / 2

    def arc(i, extra=0.0):
        """The bowed front edge of tread i (bulging toward the front, more at the foot)."""
        yi = y0 + i * RUN
        h = hw(yi) + 0.4
        sag = (0.95 * (1 - i / STEPS) + 0.12) if i < STEPS else 0.0
        return [(x, yi - sag * (1 - (x / h) ** 2) - extra) for x in [h * (2 * t / 12 - 1) for t in range(13)]]

    for i in range(STEPS):
        front = arc(i)
        back = arc(i + 1, extra=-0.02) if i < STEPS - 1 else [(x, yt) for x, _ in arc(i)]
        tprism(f"Step{i}", front + back[::-1], 0.0, (i + 1) * RISE, stone if i % 2 == 0 else stone, plane="XY", bevel=0.035)
        tprism(f"Nose{i}", arc(i, extra=0.05) + [(x, y + 0.25) for x, y in arc(i)][::-1], (i + 1) * RISE - 0.1, 0.1, dark, plane="XY", bevel=0.02)
    tprism("Back", [(-wt / 2 - 0.3, yt - 0.05), (wt / 2 + 0.3, yt - 0.05), (wt / 2 + 0.3, yt + 0.0), (-wt / 2 - 0.3, yt + 0.0)], 0.0, H, dark, plane="XY")
    # the splayed cheeks with the balustrade: built straight along a local y, then turned and set along the splay
    ang = math.atan(((wb - wt) / 2) / L)
    Lc = L / math.cos(ang)
    for sx in (-1, 1):
        s = _mark()
        rake = _cheek(f"C{sx}", sx, 0.0, cw, -Lc / 2, Lc, RISE, RUN * Lc / L, H, up, stone, dark, rnd)
        foot = [(y, z + 0.22) for y, z in rake[1:]]
        set_group("Rail")
        _iron_rake(f"R{sx}", M, gl, 0.0, foot, 2.4, bay=0.82, rail=0.06, face=sx)
        set_group("Main")
        xm = sx * ((wb + wt) / 4 + cw / 2)
        _xform(s, Matrix.Translation((xm, 0, 0)) @ Matrix.Rotation(sx * ang, 4, "Z"))
    _moss("Moss", [(rnd.uniform(-wb / 2, wb / 2), y0 - 1.0, 0.02) for _ in range(4)], mossy(), rnd, 0.1)
    for k in range(3):
        _crack(f"Crack{k}", (rnd.uniform(-3, 3), y0 + (k + 2) * RUN - 0.3, (k + 2) * RISE - 0.2), (1, 0, 0.2), (0, 0, 1), 0.8, rnd, hollow(), n=5)
    for sx in (-1, 1):
        x, y = sx * (wb / 2 + cw / 2 + 0.05), y0 - 0.85
        set_group("Newels")
        _pin_newel(f"N{sx}", x, y, M, stone, dark, gl, h=3.2, w=1.6, pinnacle=False)
        _lamp_standard(f"Lamp{sx}", x, y, 3.2, M, gl)
    set_group("Main")
    return _dims()


# ------------------------------------------------------------------ the side flights of a split stair

def _side_flight(M, sign):
    """A 5-wide flight built climbing +Y with the balustrade on its +sign side, then turned to climb along X."""
    rnd = random.Random(323 if sign > 0 else 324)
    stone, dark = castle()
    gl = gilt()
    inner, cw, up = 5.0, 0.9, 0.65
    y0 = -L / 2
    set_group("Main")
    _treads("S", STEPS, RISE, RUN, inner, stone, dark, rnd)
    xc = inner / 2 + cw / 2
    rakes = {}
    for sx in (-1, 1):
        rakes[sx] = _cheek(f"C{sx}", sx, xc, cw, y0, L, RISE, RUN, H, up, stone, dark, rnd, lancets=(sx == sign))
    _weather("W", STEPS, RISE, RUN, inner, y0, mossy(), hollow(), staining(), rnd)
    _pin_newel(f"N", sign * xc, y0 - 0.55, M, stone, dark, gl, h=RISE + up + 1.5, w=cw + 0.3)
    set_group("Rail")
    foot = [(y, z + 0.22) for y, z in rakes[sign][1:]]
    _iron_rake("R", M, gl, sign * xc, foot, 2.3, face=sign)
    y, z = foot[-1]
    lathe("HeadPost", [(0, z), (0.13, z), (0.1, z + 0.25), (0.07, z + 2.2), (0.12, z + 2.32), (0.1, z + 2.45), (0, z + 2.47)], M["iron"], seg=12,
          loc=(sign * xc, y - 0.05, 0))
    sphere("HeadBall", 0.1, (sign * xc, y - 0.05, z + 2.56), gl, seg=12, rings=6)
    set_group("Main")
    # turn it: sign +1 climbs +X (rotate -90), sign -1 climbs -X (rotate +90); the balustrade ends on the front (-Y)
    _xform(0, Matrix.Rotation(-math.pi / 2 * sign, 4, "Z"))
    return _dims()


# ------------------------------------------------------------------ the porch

def entrance_porch(M):
    rnd = random.Random(325)
    stone, dark = castle()
    hol = hollow()
    gl = gilt()
    W, D, pw = 18.0, 9.0, 1.4
    opening = 12.4
    _porch_body(W, D, stone, dark, hol, rnd, True, pw, "spire", M, gl, side_panels=2)
    # a narrow lancet panel on the front face either side of where the flight meets it
    for sx in (-1, 1):
        cx = sx * ((opening / 2 + W / 2 - pw) / 2 + 0.05)
        _recess_lancet(f"Front{sx}", cx, -D / 2, 1.0, 0.42, 3.0, 4.2, stone, dark, hol)
    # the railings, each its own piece
    yf = -D / 2 + 0.3
    for sx in (-1, 1):
        set_group("RailFrontR" if sx > 0 else "RailFrontL")
        a, b = (opening / 2, W / 2 - pw + 0.1) if sx > 0 else (-(W / 2 - pw + 0.1), -opening / 2)
        _level_rail(f"F{sx}", M, gl, a, b, H, "X", yf, face=1)
        set_group("RailRight" if sx > 0 else "RailLeft")
        _level_rail(f"S{sx}", M, gl, -D / 2 + pw - 0.1, D / 2 - 0.1, H, "Y", sx * (W / 2 - 0.3), face=sx)
    set_group("Main")
    return _dims()


def entrance_newel_lantern(M):
    stone, dark = castle()
    gl = gilt()
    set_group("Main")
    _pin_newel("N", 0, 0, M, stone, dark, gl, h=3.2, w=1.6, pinnacle=False)
    _lamp_standard("Lamp", 0, 0, 3.2, M, gl)
    set_group("Main")
    return _dims()


# ------------------------------------------------------------------ the Moonrise entrance

def _moon_cheek_roundels(prefix, sx, xc, cw, y0, up, gl, nm, frame):
    """Moon roundels along a cheek's outer face in place of lancets, waxing toward the top."""
    def top(y):
        return RISE + up + (H - RISE) * min(1, max(0, (y - (y0 + RUN * 0.5)) / (L - RUN * 1.5)))
    n = 5
    for k in range(n):
        yc = y0 + 0.9 + (L - 1.4) * (k + 0.5) / n
        zc = max(1.05, top(yc) - 0.95)
        s = _mark()
        _moon_face(f"{prefix}{k}", 0, 0, zc, 0.42, math.cos(math.pi * (k + 1) / (n + 1)), gl, nm, frame=frame)
        _side(s, sx * (xc + cw / 2 + 0.005), sx)
        for ob in P.PARTS[s:]:
            ob.matrix_world = Matrix.Translation((0, yc, 0)) @ ob.matrix_world


def entrance_moon_stair(M):
    rnd = random.Random(326)
    stone, dark = castle()
    gl = gilt()
    nm = night()
    inner, cw, up = 12.0, 1.3, 0.6
    y0 = -L / 2
    set_group("Main")
    _treads("S", STEPS, RISE, RUN, inner, stone, dark, rnd)
    xc = inner / 2 + cw / 2
    rakes = {}
    set_group("Cheeks")
    for sx in (-1, 1):
        rakes[sx] = _cheek(f"C{sx}", sx, xc, cw, y0, L, RISE, RUN, H, up, stone, dark, rnd, lancets=False)
        _moon_cheek_roundels(f"CM{sx}", sx, xc, cw, y0, up, gl, nm, dark)
    set_group("Main")
    # the climb from the new moon to the full: a roundel inlaid in every tread
    for i in range(STEPS):
        yf = y0 + i * RUN
        _moon_flat(f"Phase{i}", 0, yf + RUN / 2 - 0.05, (i + 1) * RISE, 0.46, math.cos(math.pi * i / (STEPS - 1)), gl, nm, ring=dark)
        for sx in (-1, 1):
            box(f"Inlay{i}{sx}", (1.6, 0.06, 0.012), (sx * 1.6, yf + RUN / 2 - 0.05, (i + 1) * RISE + 0.004), gl, bevel=0.003)
    _weather("W", STEPS, RISE, RUN, inner, y0, mossy(), hollow(), staining(), rnd)
    # the balustrade, a gilt crescent on every fourth bar
    set_group("Rail")
    for sx in (-1, 1):
        foot = [(y, z + 0.22) for y, z in rakes[sx][1:]]
        _iron_rake(f"R{sx}", M, gl, sx * xc, foot, 2.5, bay=0.82, rail=0.06, face=sx)
        for k, (y, z) in enumerate(_feet(foot, 0.82)):
            if k % 4 == 2:
                pts = [(v, -u) for u, v in _lit(0.11, 0.4, n=10)]
                tprism(f"RC{sx}{k}", [(y + u, z + 2.5 + 0.2 + v) for u, v in pts], sx * xc, 0.02, gl, plane="YZ")
    # the foot piers: lancet panels, a crest, a bracket lantern, the crescent and the raven
    for sx in (-1, 1):
        set_group("Piers")
        x, y, w, h = sx * xc, y0 - 0.9, 1.8, 3.6
        box(f"NPlinth{sx}", (w + 0.2, w + 0.2, 0.4), (x, y, 0.2), dark, bevel=0.05)
        box(f"NShaft{sx}", (w, w, h - 0.6), (x, y, 0.4 + (h - 0.6) / 2), stone, bevel=0.04)
        box(f"NCap{sx}", (w + 0.26, w + 0.26, 0.26), (x, y, h - 0.07), dark, bevel=0.06)
        for k, (dx, dy, rot) in enumerate(((0, -1, 0), (1, 0, math.pi / 2), (-1, 0, -math.pi / 2))):
            s = _mark()
            _lancet(f"NLancet{sx}{k}", 0, 0, 0.75, w * 0.3, h * 0.55, h * 0.78, dark, thick=0.035)
            _xform(s, Matrix.Translation((x + dx * (w / 2 + 0.005), y + dy * (w / 2 + 0.005), 0)) @ Matrix.Rotation(rot, 4, "Z"))
        _crest(f"NCrest{sx}", x, y - w / 2 - 0.03, h * 0.3, M, gl, s=1.05)
        _finial_moon(f"NMoon{sx}", x, y, h + 0.06, 1.25, gl, stone, dark, horn=sx)
        _bracket_lantern(f"NLamp{sx}", x, y - w / 2, h - 0.75, M, gl)
    set_group("Main")
    return _dims()


def entrance_moon_porch(M):
    rnd = random.Random(327)
    stone, dark = castle()
    hol = hollow()
    gl = gilt()
    nm = night()
    W, D, pw = 18.4, 10.0, 1.7
    yc = 0.4                                  # the dial's centre on the deck
    R0 = 3.6
    _porch_body(W, D, stone, dark, hol, rnd, True, pw, "moon", M, gl, skip=lambda cx, cy: math.hypot(cx, cy - yc) < R0 + 0.35, side_panels=3,
                moon_panels=True)
    # the moon dial: a dark stone disc, gilt rings, the eight phases round a crimson and gilt star
    set_group("Deck")
    z = H + 0.03
    lathe("Dial", [(0, z - 0.33), (R0 + 0.3, z - 0.33), (R0 + 0.3, z - 0.04), (R0 + 0.22, z + 0.0), (0, z + 0.0)], dark, seg=64, loc=(0, yc, 0))
    for r, t in ((R0 + 0.1, 0.04), (R0 - 0.35, 0.025), (1.95, 0.03)):
        hoop(f"DialRing{r:.1f}", (0, yc, z + 0.006), r, "Z", gl, thick=t)
    for j in range(8):
        a = math.pi / 2 - j * 2 * math.pi / 8
        p = j / 8
        k = math.cos(2 * math.pi * p)
        _moon_flat(f"Dial{j}", math.cos(a) * 2.75, yc + math.sin(a) * 2.75, z + 0.01, 0.46, k if j != 4 else -1.0, gl, nm, waning=p > 0.5)
    tprism("DialField", [(math.cos(t / 40 * 2 * math.pi) * 1.75, yc + math.sin(t / 40 * 2 * math.pi) * 1.75) for t in range(40)], z - 0.005, 0.02,
           M["crimson"], plane="XY")
    star = []
    for t in range(16):
        r = 1.45 if t % 2 == 0 else 0.55
        a = math.pi / 2 + t * math.pi / 8
        star.append((math.cos(a) * r, yc + math.sin(a) * r))
    tprism("DialStar", star, z + 0.012, 0.02, gl, plane="XY", bevel=0.004)
    _moon_flat("DialHeart", 0, yc, z + 0.035, 0.36, -1.0, gl, nm)
    # the railings along the sides, each its own piece
    for sx in (-1, 1):
        set_group("RailRight" if sx > 0 else "RailLeft")
        _level_rail(f"S{sx}", M, gl, -D / 2 + pw - 0.1, D / 2 - 0.1, H, "Y", sx * (W / 2 - 0.3), height=2.5, face=sx)
    set_group("Main")
    return _dims()


def entrance_moon_portico(M):
    rnd = random.Random(328)
    stone, dark = castle()
    hol = hollow()
    gl = gilt()
    nm = night()
    X0, Dp = 5.9, 3.0                         # the piers' centres, the portico's depth
    zs, za = 9.2, 13.4                        # the arch's springing and apex
    zf0, zf1 = 13.9, 15.0                     # the frieze
    zg, zapex = 15.1, 19.6                    # the gable
    hw = X0 - 0.85
    yfr = -Dp / 2                             # the front face
    set_group("Main")
    box("Base", (2 * X0 + 2.6, Dp + 0.3, 0.4), (0, 0, 0.2), dark, bevel=0.05)
    # the clustered piers: a deep core, an engaged shaft on the front with a base and a capital, a crocketed pinnacle
    for sx in (-1, 1):
        x = sx * X0
        box(f"Pier{sx}", (1.7, Dp, zf1 - 0.4), (x, 0, 0.4 + (zf1 - 0.4) / 2), stone, bevel=0.04)
        box(f"PierFoot{sx}", (1.95, Dp + 0.2, 0.6), (x, 0, 0.7), dark, bevel=0.06)
        for dx in (-0.45, 0.45):
            lathe(f"Shaft{sx}{dx}", [(0, 1.0), (0.3, 1.0), (0.3, 1.25), (0.22, 1.4), (0.2, zs - 0.6), (0.3, zs - 0.4), (0.36, zs - 0.1), (0, zs - 0.1)], stone,
                  seg=16, loc=(x + dx, yfr - 0.12, 0))
        box(f"Capital{sx}", (2.2, Dp + 0.45, 0.45), (x, -0.1, zs + 0.12), dark, bevel=0.06)
        for f in range(3):
            sphere(f"Leaf{sx}{f}", 0.16, (x + (f - 1) * 0.55, yfr - 0.3, zs - 0.12), stone, seg=8, rings=4, scale=(1.2, 0.6, 0.9))
        _spirelet(f"Pin{sx}", x, 0, zf1, 3.6, 1.3, stone, crockets=3)
        sphere(f"PinGilt{sx}", 0.1, (x, 0, zf1 + 3.7), gl, seg=10, rings=6)
        s = _mark()
        _lancet(f"PierLancet{sx}", 0, 0, zs + 0.8, 0.38, zs + 2.4, zs + 3.6, dark, thick=0.035)
        _xform(s, Matrix.Translation((x, yfr - 0.005, 0)))
    # the arch: a spandrel wall pierced by the pointed opening, moulded rings round it, cusps inside
    ext = [(x, z) for x, z in _pointed(hw + 0.15, zs, za + 0.2, 16)]
    wall = [(-X0, zs)] + ext + [(X0, zs), (X0, zf0), (-X0, zf0)]
    tprism("Spandrel", wall, 0.0, Dp, stone, bevel=0.03)
    for j, (dr, mat, t) in enumerate(((0.12, dark, 0.09), (0.36, stone, 0.08), (0.58, gl, 0.035), (0.75, dark, 0.07))):
        ring = [(x, yfr - 0.05 - 0.04 * j, z) for x, z in _pointed(hw + dr, zs, za + dr * 1.1, 18)]
        tube(f"Archivolt{j}", ring, t, mat, square=(mat is not gl), poly=True)
    soff = [(x, z) for x, z in _pointed(hw + 0.14, zs, za + 0.19, 16)]
    for k, t in enumerate((0.3, 0.5, 0.7)):
        for sx in (-1, 1):
            i = int(len(soff) / 2 + sx * t * len(soff) / 2)
            i = max(0, min(len(soff) - 1, i))
            cx, cz = soff[i]
            _foil(f"Cusp{k}{sx}", cx * 0.93, yfr - 0.1, cz - 0.25, 0.22, stone, lobes=3, thick=0.04)
    for sx in (-1, 1):
        _crest(f"Crest{sx}", sx * (hw - 0.4), yfr - 0.03, zs + 2.9, M, gl, s=1.5)
    # the frieze and its motto (the frieze and gable are their own piece)
    set_group("Gable")
    box("Frieze", (2 * X0 + 1.9, Dp + 0.1, zf1 - zf0), (0, 0, (zf0 + zf1) / 2), stone, bevel=0.04)
    box("FriezeBed", (2 * X0 + 2.1, Dp + 0.3, 0.16), (0, 0, zf0 - 0.05), dark, bevel=0.03)
    box("FriezeCap", (2 * X0 + 2.2, Dp + 0.4, 0.2), (0, 0, zf1 + 0.05), dark, bevel=0.04)
    box("MottoBand", (2 * X0 - 1.2, 0.04, 0.72), (0, yfr - 0.07, (zf0 + zf1) / 2), nm, bevel=0.01)
    for zz in (zf0 + 0.16, zf1 - 0.16):
        box(f"MottoRule{zz:.1f}", (2 * X0 - 1.0, 0.03, 0.03), (0, yfr - 0.1, zz), gl, bevel=0.005)
    _lettering("Motto", "PER NOCTEM AD LUCEM", 0, yfr - 0.09, (zf0 + zf1) / 2, 2 * X0 - 2.0, 0.48, gl, depth=0.025)
    for sx in (-1, 1):
        _moon_face(f"MottoMoon{sx}", sx * (X0 - 0.55), yfr - 0.09, (zf0 + zf1) / 2, 0.28, -1.0 if sx > 0 else 1.0, gl, nm)
    # the gable: a crocketed coping, a full-moon rose window that glows, a crescent and a raven on the apex
    gw = X0 + 0.55
    tri = [(-gw, zg), (gw, zg), (0, zapex)]
    tprism("Gable", tri, 0.0, Dp - 0.8, stone, bevel=0.03)
    for sx in (-1, 1):
        a, b = (sx * (gw + 0.25), yfr + 0.25, zg - 0.05), (0, yfr + 0.25, zapex + 0.3)
        tube(f"Coping{sx}", [a, b], 0.2, dark, square=True, poly=True)
        for k in range(1, 7):
            t = k / 7
            p = Vector(a).lerp(Vector(b), t)
            cone(f"Crocket{sx}{k}", 0.13, 0.0, 0.32, (p.x, p.y - 0.12, p.z + 0.2), stone, verts=6, rot=(0, -sx * 0.5, 0))
    rc, rr = (0, zg + 2.0), 1.55
    tube("RoseFrame", circle_pts(0, yfr + 0.32, rc[1], rr + 0.12, "Y", 32), 0.13, dark, closed=True, square=True, poly=True)
    tube("RoseInner", circle_pts(0, yfr + 0.3, rc[1], rr * 0.42, "Y", 24), 0.05, stone, closed=True, square=True, poly=True)
    for k in range(8):
        a = k * math.pi / 4
        tube(f"RoseBar{k}", [(math.cos(a) * rr * 0.42, yfr + 0.3, rc[1] + math.sin(a) * rr * 0.42), (math.cos(a) * rr, yfr + 0.3, rc[1] + math.sin(a) * rr)],
             0.045, stone, square=True, poly=True)
        _foil(f"RoseFoil{k}", math.cos(a + math.pi / 8) * rr * 0.72, yfr + 0.3, rc[1] + math.sin(a + math.pi / 8) * rr * 0.72, rr * 0.2, stone, lobes=3,
              thick=0.03)
    _foil("RoseHeart", 0, yfr + 0.28, rc[1], rr * 0.3, gl, lobes=4, thick=0.03)
    set_group("MoonGlow")
    tprism("RoseMoon", [(math.cos(t / 40 * 2 * math.pi) * rr, rc[1] + math.sin(t / 40 * 2 * math.pi) * rr) for t in range(40)], yfr + 0.37, 0.02, nm)
    set_group("Gable")
    _finial_moon("Apex", 0, yfr + 0.25, zapex + 0.35, 1.3, gl, stone, dark)
    set_group("Main")
    # the hanging lantern in the arch
    tube("Chain", [(0, yfr + 0.6, za - 0.1), (0, yfr + 0.6, za - 1.6)], 0.025, M["iron"], poly=True)
    for k in range(6):
        hoop(f"Link{k}", (0, yfr + 0.6, za - 0.25 - k * 0.24), 0.06, "X" if k % 2 else "Y", M["iron"], thick=0.014)
    hex_lantern("Hang", M, gl, Matrix.Translation((0, yfr + 0.6, za - 1.6 - 2.22 * 0.9)) @ Matrix.Scale(0.9, 4), bottom="drop", top_ring=True)
    # weathering
    _moss("Moss", [(sx * X0 + rnd.uniform(-0.6, 0.6), yfr - 0.15, 0.42) for sx in (-1, 1) for _ in range(2)], mossy(), rnd, 0.1)
    _crack("Crack", (-X0 - 0.5, yfr - 0.006, 6.0), (0.2, 0, 1), (1, 0, 0), 1.4, rnd, hol)
    _crack("Crack2", (X0 + 0.2, yfr - 0.006, 11.2), (0.3, 0, -1), (1, 0, 0), 0.9, rnd, hol)
    set_group("Main")
    return _dims()


def _sector(name, cx, cy, r0, r1, a0, a1, z0, z1, mat, seg, bev=0.035):
    """An annular sector (radii r0 < r1, angles a0 -> a1 in radians) from z0 to z1; r0 = 0 makes a pie slice."""
    n = max(2, seg)
    outer = [(cx + math.cos(a0 + (a1 - a0) * t / n) * r1, cy + math.sin(a0 + (a1 - a0) * t / n) * r1) for t in range(n + 1)]
    if r0 <= 0:
        poly = outer + [(cx, cy)]
    else:
        inner = [(cx + math.cos(a0 + (a1 - a0) * t / n) * r0, cy + math.sin(a0 + (a1 - a0) * t / n) * r0) for t in range(n + 1)][::-1]
        poly = outer + inner
    tprism(name, poly, z0, z1 - z0, mat, plane="XY", bevel=bev)


def _fan(M, a0, a1, seed, run=1.1, r_top=4.6, steps=STEPS, rise=RISE, moon=False, newels=(), ends=True, seg_per_rad=9.5):
    """Concentric stepped rings fanning out between angles a0 and a1 (radians) round the origin: a landing of radius r_top
    at the top, `steps` treads each a wider ring with a dark worn nosing (their own piece), plinth blocks capping the step
    ends on the flat sides (ends), newels at `newels` ((angle, kind), kind "lamp" or "moon") round the foot. moon: gilt
    moon phases inlaid round every tread and a moon dial on the landing; otherwise a crimson and gilt crest medallion.
    A full turn (a dais) is built as two halves so every piece triangulates cleanly."""
    rnd = random.Random(seed)
    stone, dark = castle()
    gl = gilt()
    nm = night()
    Hh = steps * rise
    R = r_top + steps * run
    span = abs(a1 - a0)
    full = span >= 2 * math.pi - 1e-6
    parts = [(a0, a0 + (a1 - a0) / 2), (a0 + (a1 - a0) / 2, a1)] if full else [(a0, a1)]
    seg = max(8, int(span / len(parts) * seg_per_rad))
    set_group("Main")
    for i in range(steps):
        r1 = R - i * run
        r0 = r1 - run - 0.02
        z = (i + 1) * rise
        for h, (b0, b1) in enumerate(parts):
            _sector(f"Step{i}_{h}", 0, 0, r0, r1, b0, b1, 0.0, z, stone, seg)
            set_group("Noses")
            _sector(f"Nose{i}_{h}", 0, 0, r1 - 0.28, r1 + 0.04, b0, b1, z - 0.1, z + 0.004, dark, seg, bev=0.02)
            set_group("Main")
        if moon and i % 2 == 0:
            set_group("Inlays")
            k_n = max(2, int(span * (r1 - run / 2) / 3.9))
            for k in range(k_n):
                a = a0 + (a1 - a0) * (k + 0.5) / k_n
                r = r1 - run / 2 - 0.05
                ph = (i * 3 + k) % 8
                kk = math.cos(2 * math.pi * ph / 8)
                _moon_flat(f"Phase{i}_{k}", math.cos(a) * r, math.sin(a) * r, z, 0.26, kk if ph != 4 else -1.0, gl, nm, waning=ph > 4, ring=dark,
                           seg=14)
            set_group("Main")
    for h, (b0, b1) in enumerate(parts):
        _sector(f"Landing{h}", 0, 0, 0.0, r_top + 0.02, b0, b1, 0.0, Hh, stone, seg)
    # the landing's medallion, on the fan's bisector (at the centre of a dais)
    am = (a0 + a1) / 2
    mr = min(1.6, r_top * 0.42)
    mc = (0.0, 0.0) if full else (math.cos(am) * r_top * 0.5, math.sin(am) * r_top * 0.5)
    lathe("Medal", [(0, Hh - 0.05), (mr + 0.1, Hh - 0.05), (mr + 0.1, Hh + 0.012), (0, Hh + 0.012)], dark, seg=48, loc=(mc[0], mc[1], 0))
    hoop("MedalRing", (mc[0], mc[1], Hh + 0.016), mr, "Z", gl, thick=0.035)
    if moon:
        for j in range(8):
            a = math.pi / 2 - j * 2 * math.pi / 8
            _moon_flat(f"Dial{j}", mc[0] + math.cos(a) * mr * 0.68, mc[1] + math.sin(a) * mr * 0.68, Hh + 0.014, mr * 0.17,
                       math.cos(2 * math.pi * j / 8) if j != 4 else -1.0, gl, nm, waning=j > 4)
        _moon_flat("DialHeart", mc[0], mc[1], Hh + 0.014, mr * 0.3, -1.0, gl, nm)
    else:
        tprism("MedalField", [(mc[0] + math.cos(t / 36 * 2 * math.pi) * mr * 0.83, mc[1] + math.sin(t / 36 * 2 * math.pi) * mr * 0.83) for t in range(36)],
               Hh + 0.006, 0.014, M["crimson"], plane="XY")
        sm = _mark()
        foil("MedalFoil", 0, 0, 0, mr * 0.5, gl, thick=0.03)
        _xform(sm, Matrix.Translation((mc[0], mc[1], Hh + 0.024)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    # the step ends on the flat sides
    if ends and not full:
        for a, side in ((a0, -1), (a1, 1)):
            d = Vector((math.cos(a), math.sin(a), 0))
            nrm = Vector((-math.sin(a), math.cos(a), 0)) * side      # out of the fan, across the flat side
            for i in range(steps):
                r1 = R - i * run
                z = (i + 1) * rise
                c = d * (r1 - run / 2) + nrm * 0.25
                box(f"End{i}{side}", (run + 0.06, 0.5, z), (c.x, c.y, z / 2), dark, bevel=0.03, rot=(0, 0, math.atan2(d.y, d.x)))
    # weathering
    pts = []
    lo_a, hi_a = min(a0, a1), max(a0, a1)
    for i in range(steps):
        if rnd.random() < 0.6:
            a = rnd.uniform(lo_a + 0.1, hi_a - 0.1)
            r = R - (i + 1) * run + 0.12
            pts.append((math.cos(a) * r, math.sin(a) * r, (i + 1) * rise + 0.005))
    _moss("Moss", pts, mossy(), rnd, 0.1)
    for k in range(4):
        i = rnd.randrange(1, steps)
        a = lo_a + (hi_a - lo_a) * rnd.uniform(0.15, 0.85)
        r = R - i * run + 0.005
        _crack(f"Crack{k}", (math.cos(a) * r, math.sin(a) * r, i * rise + 0.25), (-math.sin(a), math.cos(a), 0.2), (0, 0, 1), 0.7, rnd, hollow(), n=5)
    # newels round the foot
    for a, kind in newels:
        set_group("Newels")
        x, y = math.cos(a) * (R + 0.9), math.sin(a) * (R + 0.9)
        tag = f"{int(round(math.degrees(a))) % 360}"
        if kind == "moon":
            w, h = 1.8, 3.6
            box(f"NPlinth{tag}", (w + 0.2, w + 0.2, 0.4), (x, y, 0.2), dark, bevel=0.05)
            box(f"NShaft{tag}", (w, w, h - 0.6), (x, y, 0.4 + (h - 0.6) / 2), stone, bevel=0.04)
            box(f"NCap{tag}", (w + 0.26, w + 0.26, 0.26), (x, y, h - 0.07), dark, bevel=0.06)
            s = _mark()
            _lancet(f"NLancet{tag}", 0, 0, 0.75, w * 0.3, h * 0.55, h * 0.78, dark, thick=0.035)
            _xform(s, Matrix.Translation((x, y - w / 2 - 0.005, 0)))
            _crest(f"NCrest{tag}", x, y - w / 2 - 0.03, h * 0.3, M, gl, s=1.05)
            _finial_moon(f"NMoon{tag}", x, y, h + 0.06, 1.25, gl, stone, dark, horn=1 if x > 0 else -1)
            _bracket_lantern(f"NLamp{tag}", x, y - w / 2, h - 0.75, M, gl)
        else:
            _pin_newel(f"N{tag}", x, y, M, stone, dark, gl, h=3.2, w=1.6, pinnacle=False)
            _lamp_standard(f"Lamp{tag}", x, y, 3.2, M, gl)
    set_group("Main")
    return _dims()


def entrance_half_round(M):
    """Half-round steps fanning out in front of a doorway (the flat back, y = 0, goes against the facade)."""
    return _fan(M, -math.pi, 0.0, 329, newels=((-math.pi + 0.06, "lamp"), (-0.06, "lamp")))


def entrance_half_round_moon(M):
    """The half-round steps in the Moonrise manner: gilt moon phases round every tread, a moon dial on the landing,
    crescent-and-raven piers with bracket lanterns at the two ends."""
    return _fan(M, -math.pi, 0.0, 330, moon=True, newels=((-math.pi + 0.07, "moon"), (-0.07, "moon")))


def entrance_quarter_round(M):
    """A quarter fan for a corner (flat backs on +Y and -X, against two walls) or the end of a wall; turn it to suit."""
    return _fan(M, -math.pi / 2, 0.0, 331, run=1.15, r_top=3.6, newels=((-math.pi / 2 + 0.08, "lamp"), (-0.08, "lamp")))


def entrance_round_dais(M):
    """A round dais: five steps (3 high) all the way round a round platform with the crest medallion, four lantern newels
    on the diagonals; for a statue, a fountain, a gazebo or a round tower door."""
    return _fan(M, 0.0, 2 * math.pi, 332, run=1.1, r_top=4.0, steps=5, ends=False, seg_per_rad=8.0,
                newels=tuple((math.pi / 4 + k * math.pi / 2, "lamp") for k in range(4)))


def _curved_wall(name, cx, cy, r_in, r_out, a0, a1, zbot, ztop, mat, n=24, bevel=0.03):
    """A curved wall between radii r_in and r_out round (cx, cy) from angle a0 to a1, its bottom zbot(t) and top ztop(t)
    for t 0..1 along it (so it can rake)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for k in range(n + 1):
        t = k / n
        a = a0 + (a1 - a0) * t
        c, s_ = math.cos(a), math.sin(a)
        z0, z1 = zbot(t), ztop(t)
        rings.append([bm.verts.new((cx + c * r_in, cy + s_ * r_in, z0)), bm.verts.new((cx + c * r_out, cy + s_ * r_out, z0)),
                      bm.verts.new((cx + c * r_out, cy + s_ * r_out, z1)), bm.verts.new((cx + c * r_in, cy + s_ * r_in, z1))])
    for k in range(n):
        a, b = rings[k], rings[k + 1]
        for q in range(4):
            bm.faces.new((a[q], a[(q + 1) % 4], b[(q + 1) % 4], b[q]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, bevel)


def _helix_rail(prefix, M, gl, cx, cy, r, a0, a1, zf, height=2.4):
    """The gothic iron balustrade bent round a curve: bars on the arc at radius r from a0 to a1 standing on zf(t) (t 0..1),
    a base rail, a top rail, a mid rail, the brass handrail, gilt collars and roundels between the bars."""
    iron = M["iron"]
    n = max(4, int(round(abs(a1 - a0) * r / 0.72)))
    P3 = lambda t, dz: (cx + math.cos(a0 + (a1 - a0) * t) * r, cy + math.sin(a0 + (a1 - a0) * t) * r, zf(t) + dz)
    fine = [k / (n * 2) for k in range(n * 2 + 1)]
    tube(f"{prefix}Base", [P3(t, 0.1) for t in fine], 0.032, iron, square=True, poly=True)
    tube(f"{prefix}Top", [P3(t, height - 0.08) for t in fine], 0.035, iron, square=True, poly=True)
    tube(f"{prefix}Mid", [P3(t, height - 0.5) for t in fine], 0.022, iron, poly=True)
    tube(f"{prefix}Rail", [P3(t, height + 0.02) for t in fine], 0.06, M["brass"], poly=True)
    for k in range(n + 1):
        t = k / n
        tube(f"{prefix}Bar{k}", [P3(t, 0.1), P3(t, height - 0.08)], 0.026, iron, square=True, poly=True)
        if k % 4 == 0:
            sphere(f"{prefix}Collar{k}", 0.05, P3(t, height * 0.42), gl, seg=8, rings=5, scale=(1, 1, 1.6))
        if k < n and k % 2 == 1:
            tm = (k + 0.5) / n
            a = a0 + (a1 - a0) * tm
            s = _mark()
            foil(f"{prefix}Roundel{k}", 0, 0, 0, 0.14, gl, thick=0.012)
            _xform(s, Matrix.Translation(P3(tm, height - 0.29)) @ Matrix.Rotation(a + math.pi / 2, 4, "Z"))


def _sweep(M, sign):
    """One arm of a horseshoe stair: a flight curving through a quarter turn round the centre (sign * 13, 0), its foot out
    at the side in front (approached from outside, heading inward) and its top arriving heading +Y onto a porch's front at
    x = sign * 1.5 .. sign * 7 (y = 0). Curved stone cheeks with lancets and the iron balustrade on both sides, newels at
    the foot, a lantern on the outer one."""
    rnd = random.Random(333 if sign > 0 else 334)
    stone, dark = castle()
    gl = gilt()
    cx, ri, ro, cw, up = sign * 13.0, 6.0, 11.5, 0.9, 0.6
    a_bot = math.radians(270)
    a_top = math.radians(270 - sign * 90)
    da = (a_top - a_bot) / STEPS
    set_group("Main")
    for i in range(STEPS):
        a_f, a_b = a_bot + da * i, a_bot + da * (i + 1)
        z = (i + 1) * RISE
        _sector(f"Step{i}", cx, 0, ri - 0.05, ro + 0.05, a_f, a_b + 0.004 * sign, 0.0, z, stone, 4)
        _sector(f"Nose{i}", cx, 0, ri, ro, a_f - 0.025 * sign, a_f + 0.02 * sign, z - 0.1, z + 0.004, dark, 4, bev=0.02)
    a_c0, a_c1 = a_bot - sign * 0.06, a_top

    def top(t):
        return RISE + up + (H - RISE) * min(1.0, max(0.0, (t - 0.04) / 0.92))
    for r_mid, side in ((ri - cw / 2, -1), (ro + cw / 2, 1)):
        set_group("Cheeks")
        _curved_wall(f"Cheek{side}", cx, 0, r_mid - cw / 2, r_mid + cw / 2, a_c0, a_c1, lambda t: 0.0, top, stone, n=30)
        _curved_wall(f"Plinth{side}", cx, 0, r_mid - cw / 2 - 0.06, r_mid + cw / 2 + 0.06, a_c0, a_c1, lambda t: 0.0, lambda t: 0.35, dark, n=30)
        _curved_wall(f"Coping{side}", cx, 0, r_mid - cw / 2 - 0.1, r_mid + cw / 2 + 0.1, a_c0, a_c1, top, lambda t: top(t) + 0.22, stone, n=30,
                     bevel=0.05)
        rface = r_mid + side * (cw / 2 + 0.005)
        for k in range(4):
            t = (k + 0.6) / 4.4
            a = a_c0 + (a_c1 - a_c0) * t
            zt = top(t) - 0.35
            z0 = max(0.55, zt - 2.6)
            if zt - z0 < 0.9:
                continue
            s = _mark()
            _lancet(f"Lancet{side}{k}", 0, 0, z0, 0.36, z0 + (zt - z0) * 0.62, zt, dark, thick=0.035)
            # a panel built facing -Y turned by phi faces (sin phi, -cos phi): out of the curve for the outer cheek
            # (phi = a + 90 deg), toward the centre for the inner one (phi = a - 90 deg)
            phi = a + math.pi / 2 if side > 0 else a - math.pi / 2
            _xform(s, Matrix.Translation((cx + math.cos(a) * rface, math.sin(a) * rface, 0)) @ Matrix.Rotation(phi, 4, "Z"))
        set_group("Rail")
        _helix_rail(f"R{side}", M, gl, cx, 0, r_mid, a_c0, a_c1, lambda t: top(t) + 0.22)
    for r_mid, kind in ((ri - cw / 2, "plain"), (ro + cw / 2, "lamp")):
        set_group("Newels")
        a = a_bot - sign * 0.11
        x, y = cx + math.cos(a) * r_mid, math.sin(a) * r_mid
        _pin_newel(f"N{kind}", x, y, M, stone, dark, gl, h=3.2 if kind == "lamp" else RISE + up + 1.5, w=1.4, pinnacle=(kind != "lamp"))
        if kind == "lamp":
            _lamp_standard("Lamp", x, y, 3.2, M, gl, scale=0.85)
    set_group("Main")
    mp = []
    for i in range(STEPS):
        if rnd.random() < 0.5:
            a = a_bot + da * (i + 0.5)
            r = rnd.uniform(ri + 0.2, ro - 0.2)
            mp.append((cx + math.cos(a) * r, math.sin(a) * r, (i + 1) * RISE + 0.005))
    _moss("Moss", mp, mossy(), rnd, 0.1)
    # centre the arm on the origin (its preview and pivot); the showcase joins it to a porch by its bounds
    bpy.context.view_layer.update()
    xs = [(ob.matrix_world @ Vector(c)).x for ob in P.PARTS for c in ob.bound_box]
    ys = [(ob.matrix_world @ Vector(c)).y for ob in P.PARTS for c in ob.bound_box]
    _xform(0, Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, 0)))
    return _dims()


BUILDERS = {
    "EntranceHalfRound": entrance_half_round,
    "EntranceHalfRoundMoon": entrance_half_round_moon,
    "EntranceQuarterRound": entrance_quarter_round,
    "EntranceRoundDais": entrance_round_dais,
    "EntranceSweepL": lambda M: _sweep(M, -1),
    "EntranceSweepR": lambda M: _sweep(M, 1),
    "EntranceFlight": entrance_flight,
    "EntranceFlightBowed": entrance_flight_bowed,
    "EntranceSideFlightL": lambda M: _side_flight(M, 1),
    "EntranceSideFlightR": lambda M: _side_flight(M, -1),
    "EntrancePorch": entrance_porch,
    "EntranceNewelLantern": entrance_newel_lantern,
    "EntranceMoonStair": entrance_moon_stair,
    "EntranceMoonPorch": entrance_moon_porch,
    "EntranceMoonPortico": entrance_moon_portico,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"EntranceNewelLantern": 1.2, "EntranceMoonPortico": 1.0})
