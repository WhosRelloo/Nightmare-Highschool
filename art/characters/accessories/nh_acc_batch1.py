"""Accessories batch 1: uniform and school (Kit A 1-7).

  CliquePins     one enamel-and-brass pin per clique (8 pieces, one shared atlas), on the left lapel
  Sashes         Prefect's sash (crimson silk, brass PREFECT bar, a medal) and Head Student's sash (black velvet,
                 gold braid, a star medal on a crimson rosette)
  Ties           a striped school tie (rigged: the blade flutters) and a velvet bow tie (rigged loops)
  Satchels       a leather satchel on the left hip (pendulum) and a messenger bag on the lower back
  BookStrap      three books in a buckled strap, held in the right hand
  Grimoire       the Ink Club's chained grimoire on the left hip, a faint violet sigil (emissive), pendulum
  ChoirCollars   a falling-band choir collar with a crimson bow, and a pleated ruff with lace edging
  (the Delinquents' long coat moves to the coats batch with the Headmaster's greatcoat: one shared builder)
Run: E:/Blender/blender.exe -b --factory-startup -P nh_acc.py -- batch1 --gpu
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import nh_acc as A
from nh_acc import item, piece, lerp, smooth

TORSO_FRONT = -0.5


# ================================================================== shared helpers
def frame(loc, rot=(0, 0, 0), s=1.0):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Scale(s, 4)


def offset_poly(pts, d):
    """inset (d > 0) a counter-clockwise outline by moving each vertex along its corner bisector"""
    n = len(pts)
    out = []
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e1 = (p1 - p0).normalized(); e2 = (p2 - p1).normalized()
        n1 = Vector((-e1.y, e1.x)) * sgn; n2 = Vector((-e2.y, e2.x)) * sgn
        b = (n1 + n2)
        if b.length < 1e-6:
            b = n1
        b.normalize()
        k = d / max(0.35, b.dot(n1))
        q = p1 + b * k
        out.append((q.x, q.y))
    return out


def ccw(pts):
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if area > 0 else list(reversed(pts))


def bez(p0, p1, p2, p3, n=10):
    p0, p1, p2, p3 = (Vector(p) for p in (p0, p1, p2, p3))
    return [tuple(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
            for t in (i / n for i in range(n))]


def rbox_sdf(p, half=(1.0, 0.5, 1.0), r=0.08):
    q = Vector((abs(p.x) - half[0] + r, abs(p.y) - half[1] + r, abs(p.z) - half[2] + r))
    o = Vector((max(q.x, 0), max(q.y, 0), max(q.z, 0)))
    return o.length + min(max(q.x, max(q.y, q.z)), 0) - r


def on_surface(c, d, off, half=(1.0, 0.5, 1.0), r=0.002):
    """march from c along d to where the rounded torso box's distance = off"""
    t0, t1 = 0.0, 4.0
    for _ in range(40):
        tm = (t0 + t1) / 2
        if rbox_sdf(c + d * tm, half, r) < off:
            t0 = tm
        else:
            t1 = tm
    return c + d * t0


def project_out(p, off, half=(1.0, 0.5, 1.0), r=0.002):
    """push a point to the rounded torso box's offset surface along the box gradient"""
    for _ in range(6):
        e = 1e-3
        g = Vector((rbox_sdf(p + Vector((e, 0, 0)), half, r) - rbox_sdf(p - Vector((e, 0, 0)), half, r),
                    rbox_sdf(p + Vector((0, e, 0)), half, r) - rbox_sdf(p - Vector((0, e, 0)), half, r),
                    rbox_sdf(p + Vector((0, 0, e)), half, r) - rbox_sdf(p - Vector((0, 0, e)), half, r)))
        if g.length < 1e-9:
            break
        g.normalize()
        p = p - g * (rbox_sdf(p, half, r) - off)
    return p


def band_loop(centre, normal, width, off, n=720, half=(1.0, 0.5, 1.0), r=0.002, wobble=None, keep_deg=4.0, max_step=0.09):
    """a strap / sash loop wrapped round the torso in the plane through `centre` with `normal`: grid G[i][j]
    (i across the width, j around the loop, closed by repeating the first column). The loop is sampled finely,
    then thinned where it runs straight: dense round the box's sharp edges (so no segment cuts a corner), sparse
    across the flat faces."""
    nrm = Vector(normal).normalized()
    a = nrm.orthogonal().normalized()
    b_ = nrm.cross(a).normalized()
    fine = []
    for j in range(n):
        ang = 2 * math.pi * j / n
        d = (a * math.cos(ang) + b_ * math.sin(ang)).normalized()
        mid = on_surface(Vector(centre), d, off, half, r)
        fine.append([project_out(mid + nrm * (f * width), off, half, r) for f in (-0.5, -0.17, 0.17, 0.5)])
    keep = [0]
    for j in range(1, n):
        p0 = fine[keep[-1]]
        turn = 0.0
        for k in (0, 3):
            u = fine[j][k] - fine[j - 1][k]
            v = fine[(j + 1) % n][k] - fine[j][k]
            if u.length > 1e-9 and v.length > 1e-9:
                turn = max(turn, math.degrees(u.angle(v)))
        dist = max((fine[j][k] - p0[k]).length for k in (0, 3))
        if turn > keep_deg / 4 or dist > max_step:
            keep.append(j)
    G = [[], [], [], []]
    for j in keep + [0]:
        for i in range(4):
            p = fine[j][i]
            if wobble:
                p = p + wobble(j / n, (-0.5, -0.17, 0.17, 0.5)[i])
            G[i].append(p)
    return G


def drape_point(x, y, base_z=1.0, lift=0.012, half=(1.0, 0.5), corner=0.0):
    """a plan point (x, y) on a cloth lying over the torso top: inside the top it lies flat; past an edge it rolls
    over the rounded edge and hangs down that face by the overhang distance (collars, mantles, shawls)"""
    ox = max(0.0, abs(x) - (half[0] - corner))
    oy = max(0.0, abs(y) - (half[1] - corner))
    d = math.hypot(ox, oy)
    if d <= 1e-9:
        return Vector((x, y, base_z + lift))
    ux, uy = ox / d, oy / d
    rr = max(corner, 0.0) + lift
    arc = math.pi / 2 * rr
    if d < arc:
        th = d / rr
        hx, hz = rr * math.sin(th), rr * math.cos(th) - corner
    else:
        hx, hz = rr, -(d - arc) - corner
    px = math.copysign(half[0] - corner + hx * ux, x) if ox > 0 else x
    py = math.copysign(half[1] - corner + hx * uy, y) if oy > 0 else y
    return Vector((px, py, base_z + hz))


# ================================================================== 1. clique crest pins
CLIQUES = [
    # key, name, enamel colour, frame shape, emblem, metal
    ("Vigil", "The Vigil", (0.020, 0.040, 0.120), "rayed", "lantern", "brass"),
    ("Court", "The Crimson Court", (0.300, 0.020, 0.045), "crowned", "crown_moon", "gold"),
    ("Athletes", "The Athletes", (0.020, 0.110, 0.050), "round", "laurel_star", "brass"),
    ("Delinquents", "The Delinquents", (0.012, 0.012, 0.014), "diamond", "spade_bolt", "silver"),
    ("Pack", "The Pack", (0.170, 0.060, 0.020), "fanged", "paw", "silver"),
    ("Ordinary", "The Ordinary", (0.420, 0.380, 0.300), "heater", "key", "brass"),
    ("Choir", "The Chapel Choir", (0.700, 0.680, 0.620), "lancet", "bell", "gold"),
    ("Ink", "The Ink Club", (0.060, 0.020, 0.100), "drop", "nib", "silver"),
]
PIN_AT = Vector((0.78, TORSO_FRONT - 0.002, 0.28))   # the left lapel (character's left = +X)
PIN_H = 0.40


def frame_outline(shape, h=PIN_H):
    s = h / 2
    if shape == "rayed":
        pts = []
        for i in range(32):
            a = 2 * math.pi * i / 32
            r = s * (0.86 if i % 2 else 1.0)
            pts.append((r * math.cos(a), r * math.sin(a)))
        return pts
    if shape == "round":
        return A.circle_pts(0, 0, s * 0.95, 36)
    if shape == "diamond":
        k = s * 0.98
        P = [(0, k), (k * 0.74, 0), (0, -k), (-k * 0.74, 0)]
        out = []
        for a, b in zip(P, P[1:] + P[:1]):   # slightly bowed sides
            for t in (0, 0.25, 0.5, 0.75):
                m = Vector(a).lerp(Vector(b), t)
                bow = math.sin(math.pi * t) * 0.035 * h
                nrm = Vector((m.x, m.y)).normalized()
                out.append(tuple(m + nrm * bow))
        return out
    if shape == "fanged":
        pts = []
        for i in range(28):
            a = 2 * math.pi * i / 28
            r = s * (0.84 if i % 2 else 0.97)
            pts.append((r * math.cos(a), r * math.sin(a)))
        return pts
    if shape == "heater":
        w = s * 0.88
        top = s * 0.92
        return ([(-w, top), (-w * 0.5, top * 1.04), (0, top), (w * 0.5, top * 1.04), (w, top)] +
                bez((w, top), (w, 0.05 * s), (w * 0.55, -0.55 * s), (0, -s), 10)[1:] +
                bez((0, -s), (-w * 0.55, -0.55 * s), (-w, 0.05 * s), (-w, top), 10)[1:-1])[::-1]
    if shape == "crowned":
        w = s * 0.86
        top = []
        for i in range(9):
            x = lerp(-w, w, i / 8)
            top.append((x, s * (0.98 if i % 2 == 0 else 0.80)))
        side_r = bez((w, s * 0.80), (w * 1.05, -0.2 * s), (w * 0.4, -0.75 * s), (0, -s), 10)[1:]
        side_l = bez((0, -s), (-w * 0.4, -0.75 * s), (-w * 1.05, -0.2 * s), (-w, s * 0.80), 10)[1:-1]
        return ccw(top[::-1] + side_l[::-1] + side_r[::-1])
    if shape == "lancet":
        w = s * 0.70
        pts = [(-w, -s), (w, -s)]
        pts += [(w, -s * 0.05)]
        # pointed gothic arch: two arcs centred on the opposite springers
        R = 2 * w
        for i in range(1, 12):
            a = lerp(0, math.acos(0.5), i / 12)
            pts.append((-w + R * math.cos(a), -s * 0.05 + R * math.sin(a) * 0.62 * s / w * 0.85))
        pts.append((0, s))
        for i in range(11, 0, -1):
            a = lerp(0, math.acos(0.5), i / 12)
            pts.append((w - R * math.cos(a), -s * 0.05 + R * math.sin(a) * 0.62 * s / w * 0.85))
        pts.append((-w, -s * 0.05))
        return ccw(pts)
    if shape == "drop":
        pts = []
        for i in range(40):
            t = i / 40
            a = 2 * math.pi * t
            r = s * 0.62
            x = r * math.sin(a)
            y = -s * 0.36 - r * math.cos(a)
            if y > -s * 0.36:   # the upper half narrows to the point
                k = (y + s * 0.36) / (s * 1.36)
                x *= (1 - k) ** 1.6
                y = -s * 0.36 + (y + s * 0.36) * 2.2
            pts.append((x, min(y, s)))
        return ccw(pts)
    raise KeyError(shape)


def crescent(cx, cz, R, dx, dz, r, n=28):
    """the outline of a crescent: the outer circle minus an offset inner circle (outer arc CCW, inner arc back)"""
    outer = [(cx + R * math.cos(2 * math.pi * i / 96), cz + R * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    ic = (cx + dx, cz + dz)
    keep = [i for i, p in enumerate(outer) if (p[0] - ic[0]) ** 2 + (p[1] - ic[1]) ** 2 > r * r]
    # rotate so the kept arc is contiguous
    start = next(i for i in keep if (i - 1) % 96 not in keep)
    arc = [outer[(start + k) % 96] for k in range(len(keep))]
    a0 = math.atan2(arc[0][1] - ic[1], arc[0][0] - ic[0])
    a1 = math.atan2(arc[-1][1] - ic[1], arc[-1][0] - ic[0])
    while a1 < a0:
        a1 += 2 * math.pi
    inner = [(ic[0] + r * math.cos(lerp(a1, a0, k / n)), ic[1] + r * math.sin(lerp(a1, a0, k / n))) for k in range(1, n)]
    pts = arc[::3] + [arc[-1]] + inner
    return ccw(pts)


def emblem(key, kind, mat, at, h=PIN_H, depth=0.038):
    """the clique's raised emblem on the enamel, built from outlines (x right, z up in the pin's plane)"""
    s = h / 2
    F = frame(at)
    E = lambda nm, pts, d=depth, holes=(): A.extrude_poly(f"Em_{key}_{nm}", ccw(pts), d, mat, F, bevel=0.0035, segments=1, holes=holes)
    if kind == "lantern":
        E("body", [(-0.30 * s, -0.42 * s), (0.30 * s, -0.42 * s), (0.36 * s, 0.22 * s), (-0.36 * s, 0.22 * s)],
          holes=[[(-0.18 * s, -0.30 * s), (0.18 * s, -0.30 * s), (0.22 * s, 0.12 * s), (-0.22 * s, 0.12 * s)][::-1]])
        E("flame", [(0, 0.08 * s), (0.08 * s, -0.08 * s), (0.04 * s, -0.22 * s), (-0.04 * s, -0.22 * s), (-0.08 * s, -0.08 * s)],
          d=depth * 0.85)
        E("roof", [(-0.44 * s, 0.22 * s), (0.44 * s, 0.22 * s), (0.1 * s, 0.46 * s), (-0.1 * s, 0.46 * s)])
        E("ring", A.circle_pts(0, 0.56 * s, 0.11 * s, 16), holes=[A.circle_pts(0, 0.56 * s, 0.05 * s, 12)[::-1]])
        E("base", [(-0.40 * s, -0.42 * s), (0.40 * s, -0.42 * s), (0.34 * s, -0.54 * s), (-0.34 * s, -0.54 * s)])
    elif kind == "crown_moon":
        pts = [(-0.46 * s, -0.02 * s), (0.46 * s, -0.02 * s), (0.50 * s, 0.44 * s), (0.25 * s, 0.20 * s),
               (0.0, 0.54 * s), (-0.25 * s, 0.20 * s), (-0.50 * s, 0.44 * s)]
        E("crown", pts)
        for x, z in ((-0.50, 0.50), (0.0, 0.62), (0.50, 0.50)):
            A.sphere(f"Em_{key}_orb{x}", 0.05 * s * 1.3, F @ Vector((x * s, -depth * 0.9, z * s)), mat, seg=10, rings=6)
        cres = crescent(0, -0.40 * s, 0.30 * s, 0.13 * s, 0.07 * s, 0.25 * s)
        E("moon", cres)
    elif kind == "laurel_star":
        for side in (-1, 1):
            for k in range(7):
                a = math.radians(-70 + k * 22)
                r = 0.62 * s
                cx, cz = side * r * math.cos(a), r * math.sin(a)
                leaf = []
                for i in range(12):
                    t = 2 * math.pi * i / 12
                    leaf.append((0.13 * s * math.cos(t), 0.055 * s * math.sin(t)))
                ang = a + side * math.radians(75) if side > 0 else math.pi - a - math.radians(75)
                ca, sa = math.cos(ang), math.sin(ang)
                E(f"leaf{side}_{k}", [(cx + x * ca - z * sa, cz + x * sa + z * ca) for x, z in leaf], d=depth * 0.9)
        star = []
        for i in range(10):
            a = math.pi / 2 + 2 * math.pi * i / 10
            r = (0.34 if i % 2 == 0 else 0.14) * s
            star.append((r * math.cos(a), r * math.sin(a) - 0.02 * s))
        E("star", star)
    elif kind == "spade_bolt":
        sp = (bez((0, 0.56 * s), (0.10 * s, 0.30 * s), (0.56 * s, 0.10 * s), (0.42 * s, -0.20 * s), 8) +
              bez((0.42 * s, -0.20 * s), (0.30 * s, -0.42 * s), (0.08 * s, -0.30 * s), (0.04 * s, -0.20 * s), 6) +
              [(0.14 * s, -0.56 * s), (-0.14 * s, -0.56 * s)] +
              bez((-0.04 * s, -0.20 * s), (-0.08 * s, -0.30 * s), (-0.30 * s, -0.42 * s), (-0.42 * s, -0.20 * s), 6) +
              bez((-0.42 * s, -0.20 * s), (-0.56 * s, 0.10 * s), (-0.10 * s, 0.30 * s), (0, 0.56 * s), 8))
        E("spade", sp)
        bolt = [(0.06 * s, 0.30 * s), (-0.12 * s, -0.02 * s), (0.02 * s, -0.02 * s), (-0.08 * s, -0.30 * s),
                (0.14 * s, 0.04 * s), (0.0, 0.04 * s), (0.10 * s, 0.30 * s)]
        E("bolt", bolt, d=depth * 1.25)
    elif kind == "paw":
        E("pad", [(x, z - 0.18 * s) for x, z in (bez((0, 0.14 * s), (0.30 * s, 0.16 * s), (0.36 * s, -0.20 * s), (0.10 * s, -0.24 * s), 8) +
                                                bez((0.10 * s, -0.24 * s), (0.04 * s, -0.20 * s), (-0.04 * s, -0.20 * s), (-0.10 * s, -0.24 * s), 4) +
                                                bez((-0.10 * s, -0.24 * s), (-0.36 * s, -0.20 * s), (-0.30 * s, 0.16 * s), (0, 0.14 * s), 8))])
        for i, (x, z, r) in enumerate(((-0.36, 0.14, 0.11), (-0.13, 0.36, 0.12), (0.13, 0.36, 0.12), (0.36, 0.14, 0.11))):
            E(f"toe{i}", [(x * s + r * s * 0.85 * math.cos(t), z * s + r * s * 1.15 * math.sin(t))
                          for t in (2 * math.pi * k / 16 for k in range(16))])
    elif kind == "key":
        ca, sa = math.cos(math.radians(-40)), math.sin(math.radians(-40))
        R = lambda pts: [(x * ca - z * sa, x * sa + z * ca) for x, z in pts]
        E("bow", R(A.circle_pts(-0.40 * s, 0, 0.18 * s, 20)), holes=[R(A.circle_pts(-0.40 * s, 0, 0.09 * s, 14))[::-1]])
        E("shaft", R([(-0.24 * s, -0.04 * s), (0.56 * s, -0.04 * s), (0.56 * s, 0.04 * s), (-0.24 * s, 0.04 * s)]))
        E("bit", R([(0.30 * s, -0.04 * s), (0.30 * s, -0.24 * s), (0.38 * s, -0.24 * s), (0.38 * s, -0.14 * s),
                    (0.44 * s, -0.14 * s), (0.44 * s, -0.24 * s), (0.54 * s, -0.24 * s), (0.54 * s, -0.04 * s)]))
    elif kind == "bell":
        prof = bez((0.06 * s, 0.40 * s), (0.30 * s, 0.40 * s), (0.22 * s, -0.10 * s), (0.46 * s, -0.34 * s), 10)
        pts = [(0, 0.42 * s)] + prof + [(0.40 * s, -0.42 * s), (-0.40 * s, -0.42 * s)] + [(-x, z) for x, z in reversed(prof)]
        E("bell", pts)
        E("clap", A.circle_pts(0, -0.50 * s, 0.07 * s, 12))
        E("crossv", [(-0.03 * s, 0.44 * s), (0.03 * s, 0.44 * s), (0.03 * s, 0.70 * s), (-0.03 * s, 0.70 * s)])
        E("crossh", [(-0.10 * s, 0.58 * s), (0.10 * s, 0.58 * s), (0.10 * s, 0.63 * s), (-0.10 * s, 0.63 * s)])
    elif kind == "nib":
        nib = (bez((0, -0.58 * s), (0.10 * s, -0.30 * s), (0.30 * s, -0.05 * s), (0.30 * s, 0.22 * s), 10) +
               [(0.22 * s, 0.50 * s), (-0.22 * s, 0.50 * s)] +
               bez((-0.30 * s, 0.22 * s), (-0.30 * s, -0.05 * s), (-0.10 * s, -0.30 * s), (0, -0.58 * s), 10)[:-1])
        E("nib", nib, holes=[A.circle_pts(0, 0.12 * s, 0.065 * s, 12)[::-1],
                             [(-0.012 * s, -0.50 * s), (0.012 * s, -0.50 * s), (0.012 * s, 0.06 * s), (-0.012 * s, 0.06 * s)][::-1]])
        E("band", [(-0.24 * s, 0.50 * s), (0.24 * s, 0.50 * s), (0.20 * s, 0.62 * s), (-0.20 * s, 0.62 * s)])
    else:
        raise KeyError(kind)


def pin(M, key, enamel, shape, kind, metal, at):
    met = M[metal] if metal != "silver" else M["silver"]
    en = A.mat_flat(f"Enamel_{key}", enamel, rough=0.10, coat=0.8, noise=90, bump=0.006, vary=0.05, wear=0.05, dirt=0.4)
    out = frame_outline(shape)
    inner = offset_poly(out, 0.024)
    F = frame(at)
    A.extrude_poly(f"Pin_{key}_back", ccw(out), 0.026, met, F, bevel=0.0)
    A.extrude_poly(f"Pin_{key}_rim", ccw(out), 0.040, met, F, bevel=0.005, segments=2, holes=[ccw(inner)[::-1]])
    A.extrude_poly(f"Pin_{key}_field", ccw(inner), 0.031, en, F, bevel=0.0)
    emblem(key, kind, met, at + Vector((0, 0, 0)), depth=0.042)


def _pins_render(objs, cam, man):
    """a lineup close-up of all eight pins, off the body"""
    for o in man:
        o.hide_render = True
    saved = []
    keys = [c[0] for c in CLIQUES]
    for i, k in enumerate(keys):
        ob = objs[f"Pin{k}"]
        saved.append((ob, ob.matrix_world.copy()))
        col, row = i % 4, i // 4
        tgt = Vector(((col - 1.5) * 0.48, -2.0, 1.6 - row * 0.5))
        ob.matrix_world = Matrix.Translation(tgt - PIN_AT) @ ob.matrix_world
    A.shoot(cam, f"{A.OUT}/renders/CliquePins_lineup.png", (0.0, -5.6, 1.36), target=(0, -2.0, 1.36), lens=62, aspect=0.6)
    A.shoot(cam, f"{A.OUT}/renders/CliquePins_lineup34.png", (1.5, -5.3, 2.0), target=(0, -2.0, 1.36), lens=62, aspect=0.6)
    for ob, mw in saved:
        ob.matrix_world = mw
    for o in man:
        o.hide_render = False


@item("CliquePins", "Clique crest pins", focus=(0, 0, 0.2), render=_pins_render, female=True, each=True,
      close=((2.6, -5.2, 1.4), (0.75, 0, 0.28), 120))
def build_pins(M):
    for key, name, enamel, shape, kind, metal in CLIQUES:
        piece(f"Pin{key}", "Torso")
        pin(M, key, enamel, shape, kind, metal, PIN_AT)
    return dict(notes="one pin per clique; all eight share one atlas and sit on the left lapel")


# ================================================================== 3. ties
def tie_blade_grid(top_z=0.80, bot_z=-0.66, w_top=0.17, w_bot=0.38, nu=8, nv=22):
    G = []
    for i in range(nu + 1):
        col = []
        u = i / nu - 0.5
        for j in range(nv + 1):
            t = j / nv
            z = lerp(top_z, bot_z, t)
            w = lerp(w_top, w_bot, smooth(0, 0.8, t))
            tip = smooth(0.84, 1.0, t)
            x = u * w * (1 - 0.15 * tip)
            zz = z + abs(u) * 2 * 0.17 * tip          # the edges rise to make the pointed tip
            bulge = 0.003 * math.cos(u * math.pi)
            y = TORSO_FRONT - 0.008 - bulge
            col.append(Vector((x, y, zz)))
        G.append(col)
    return G


def _tie_rig(ob):
    pts = [Vector((0, -0.512, 0.80)), Vector((0, -0.512, 0.42)), Vector((0, -0.512, 0.04)),
           Vector((0, -0.512, -0.32)), Vector((0, -0.512, -0.68))]
    return A.chain_rig(ob, (0, -0.53, 0.97), [pts])


def _bow_rig(ob):
    y = TORSO_FRONT - 0.09
    return A.chain_rig(ob, (0, y, 0.82), [[Vector((0.06, y, 0.82)), Vector((0.40, y, 0.84))],
                                         [Vector((-0.06, y, 0.82)), Vector((-0.40, y, 0.84))],
                                         [Vector((0.03, -0.512, 0.78)), Vector((0.07, -0.512, 0.62))],
                                         [Vector((-0.03, -0.512, 0.78)), Vector((-0.07, -0.512, 0.62))]])


@item("SchoolTie", "School tie", close=((2.6, -6.2, 1.0), (0, 0, 0.1), 105))
def build_tie(M):
    silk = A.mat_cloth("TieSilk", (0.30, 0.022, 0.045), weave=500, rough=0.40, sheen=0.6, bump=0.05, twill=True,
                       stripe=((0.012, 0.012, 0.016), 0.20, 0.055, 40))
    gold = A.mat_cloth("TieGold", (0.62, 0.43, 0.14), weave=500, rough=0.35, sheen=0.4, bump=0.04)
    piece("SchoolTie", "Torso", rig=_tie_rig, sway="Flutter", keepout=(0, 1, 0), lock="Z")
    A.surface("TieBlade", tie_blade_grid(), 0.009, silk)
    kn = []
    for i in range(11):
        u = i / 10 - 0.5
        col = []
        for j in range(9):
            t = j / 8
            w = lerp(0.30, 0.16, t)
            dimple = 0.012 * math.exp(-((u / 0.08) ** 2)) * math.sin(math.pi * t)
            col.append(Vector((u * w, TORSO_FRONT - 0.036 - 0.045 * math.cos(u * math.pi) * (1 - 0.35 * t) + dimple,
                               lerp(0.955, 0.75, t))))
        kn.append(col)
    A.surface("TieKnot", kn, 0.066, silk)
    sh = ccw([(x * 1.3, z * 1.3) for x, z in [(-0.05, 0.05), (0.05, 0.05), (0.05, -0.01), (0, -0.07), (-0.05, -0.01)]])
    A.extrude_poly("TieCrest", [(x, z + 0.50) for x, z in sh], 0.003, gold, frame((0, TORSO_FRONT - 0.0125, 0)), bevel=0.0, segments=1)
    return dict(notes="crimson silk with black bars and a gold crest; the blade flutters on a 4-bone chain")


@item("BowTie", "Velvet bow tie", close=((2.2, -5.2, 1.3), (0, 0, 0.75), 120))
def build_bowtie(M):
    vel = M["black_velvet"]
    sat = A.mat_cloth("BowSatin", (0.26, 0.018, 0.035), weave=600, rough=0.30, sheen=0.5, bump=0.03, twill=False)
    piece("BowTie", "Torso", rig=_bow_rig, sway="Loops", keepout=(0, 1, 0), lock="Z")
    y0 = TORSO_FRONT - 0.09
    for side in (-1, 1):
        G = []
        for i in range(17):
            a = 2 * math.pi * i / 16
            col = []
            for j in range(13):
                t = j / 12
                x = side * lerp(0.05, 0.30, t)
                h = lerp(0.06, 0.15, math.sin(math.pi * min(1, t * 1.08)) ** 0.6) * (1 - 0.2 * t)
                d = lerp(0.045, 0.075, math.sin(math.pi * t))
                pinch = 1 - 0.18 * math.sin(math.pi * t) * (1 if math.sin(a) > 0 else 0.4)
                col.append(Vector((x, y0 + d * math.cos(a), 0.82 + h * math.sin(a) * pinch + 0.02 * t)))
            G.append(col)
        A.surface(f"BowLoop{side}", G, 0.014, vel, caps=False)
        T = []
        for i in range(6):
            u = i / 5 - 0.5
            col = []
            for j in range(11):
                t = j / 10
                x = side * (0.035 + t * 0.05) + u * lerp(0.08, 0.11, t)
                cut = abs(u) * 0.07 * smooth(0.8, 1, t) * (1 if (u * side) > 0 else -0.4)
                col.append(Vector((x, TORSO_FRONT - 0.012 - 0.01 * math.sin(math.pi * t), 0.78 - t * 0.11 - cut)))
            T.append(col)
        A.surface(f"BowTail{side}", T, 0.012, vel)
    A.sphere("BowKnot", 0.075, (0, y0 - 0.005, 0.83), sat, scale=(0.85, 0.85, 1.3), seg=20, rings=12)
    return dict(notes="black velvet loops with a crimson satin knot; loops and tails on short chains")


# ================================================================== 2. sashes and medals
def sash_plane(left_shoulder=True, x=0.92):
    """the plane of a sash worn over one shoulder: through the shoulder top and the opposite hip"""
    sh = Vector((x if left_shoulder else -x, 0, 1.0))   # the shoulder's outer edge: clear of the hair
    hip = Vector((-1.0 if left_shoulder else 1.0, 0, -0.30))
    d = (sh - hip).normalized()
    n = Vector((0, 1, 0)).cross(d).normalized()
    c = (sh + hip) / 2
    return c, n, d


def medal_disc(name, at, r, mat, rim_mat, relief=None, depth=0.03):
    F = frame(at)
    A.extrude_poly(name + "_disc", A.circle_pts(0, 0, r, 32), depth, mat, F, bevel=0.004, segments=1)
    A.extrude_poly(name + "_rim", A.circle_pts(0, 0, r, 32), depth + 0.008, rim_mat, F, bevel=0.003, segments=1,
                   holes=[A.circle_pts(0, 0, r * 0.86, 32)[::-1]])
    if relief:
        relief(F, depth)


def rosette(name, at, r, mat, pleats=18):
    """a pleated ribbon rosette: a ring of fins round a disc"""
    G = []
    for i in range(pleats * 4 + 1):
        a = 2 * math.pi * i / (pleats * 4)
        col = []
        for j in range(5):
            t = j / 4
            rr = lerp(r * 0.25, r, t)
            fold = 0.018 * math.sin(pleats * a) * t
            col.append(Vector((at[0] + rr * math.cos(a), at[1] - 0.01 - fold - 0.012 * (1 - t), at[2] + rr * math.sin(a))))
        G.append(col)
    A.surface(name, G, 0.008, mat, caps=False)


@item("Sashes", "Prefect and Head Student sashes", close=((2.6, -6.4, 1.2), (0, 0, 0.2), 80), each=True)
def build_sashes(M):
    goldthread = A.mat_metal("GoldThread", (0.85, 0.6, 0.25), rough=0.45, scratch=0.1)
    # Prefect: crimson silk over the left shoulder, a brass PREFECT bar and a medal
    c, n, d = sash_plane(True)
    piece("PrefectSash", "Torso")
    G = band_loop(c, n, 0.30, 0.027)
    A.surface("PrefectBand", G, 0.012, M["crimson_silk"])
    for k in (0, 3):
        A.tube(f"PrefectEdge{k}", [tuple(project_out(p, 0.028)) for p in G[k][:-1]], 0.004, goldthread, closed=True, res=3, poly=True)
    bar_at = Vector((0.28, TORSO_FRONT - 0.04, 0.42))
    bar = ccw([(-0.21, 0.055), (0.21, 0.055), (0.235, 0.0), (0.21, -0.055), (-0.21, -0.055), (-0.235, 0.0)])
    F = frame(bar_at, (0, math.radians(-38), 0))
    A.extrude_poly("PrefectBar", bar, 0.03, M["brass"], F, bevel=0.004, segments=2)
    A.extrude_poly("PrefectBarField", offset_poly(bar, 0.016), 0.034, M["crimson_enamel"], F, bevel=0.0)
    A.text_mesh("PrefectText", "PREFECT", 0.058, M["gold"], F @ Matrix.Translation((0, -0.036, -0.002)),
                font="georgiab.ttf", depth=0.006, spacing=1.12)
    rib_at = bar_at + Vector((-0.06, -0.006, -0.20))
    A.extrude_poly("PrefectRibbon", ccw([(-0.06, 0.07), (0.06, 0.07), (0.06, -0.06), (0, -0.09), (-0.06, -0.06)]),
                   0.012, M["crimson_silk"], frame(rib_at, (0, math.radians(-38), 0)), bevel=0.002, segments=1)
    med_at = rib_at + Vector((0.045, -0.01, -0.15))

    def moon(F, dep):
        A.extrude_poly("PrefectMoon", crescent(0, 0, 0.055, 0.025, 0.012, 0.045), dep + 0.012, M["brass"], F, bevel=0.002, segments=1)
    medal_disc("PrefectMedal", med_at, 0.085, M["brassold"], M["brass"], moon)
    A.torus("PrefectMedalRing", 0.022, 0.007, med_at + Vector((0, -0.015, 0.09)), M["brass"], rot=(math.radians(90), 0, 0), major=12, minor=5)

    # Head Student: black velvet over the left shoulder too (1.79 play-test: over the right shoulder it ended on the left
    # hip, where the sheathed katana's guard sits, and crossed it on the deep bodies), gold braid edges, a gold star
    # medal on a crimson rosette on the left breast
    c, n, d = sash_plane(True)
    piece("HeadSash", "Torso")
    G = band_loop(c, n, 0.32, 0.027)
    A.surface("HeadBand", G, 0.012, M["black_velvet"])
    for k in (0, 3):
        A.tube(f"HeadBraid{k}", [tuple(project_out(p, 0.029)) for p in G[k][:-1]], 0.006, M["gold"], closed=True, res=4, poly=True)
    ros_at = Vector((0.30, TORSO_FRONT - 0.045, 0.38))
    rosette("HeadRosette", ros_at, 0.15, M["crimson_silk"])
    for side in (-1, 1):
        A.extrude_poly(f"HeadTail{side}", ccw([(-0.045, 0.0), (0.045, 0.0), (0.05, -0.26), (0.0, -0.22), (-0.05, -0.26)]),
                       0.01, M["crimson_silk"], frame(ros_at + Vector((side * 0.04, 0.012, -0.05)), (0, math.radians(side * 14), 0)),
                       bevel=0.002, segments=1)
    star = []
    for i in range(16):
        a = math.pi / 2 + 2 * math.pi * i / 16
        r = (0.13 if i % 2 == 0 else 0.062)
        star.append((r * math.cos(a), r * math.sin(a)))
    F = frame(ros_at + Vector((0, -0.02, 0)))
    A.extrude_poly("HeadStar", ccw(star), 0.035, M["gold"], F, bevel=0.006, segments=2)
    A.extrude_poly("HeadStarCore", A.circle_pts(0, 0, 0.045, 24), 0.05, M["crimson_enamel"], F, bevel=0.004, segments=1)
    return dict(notes="two sashes over the left shoulder to the right hip (clear of the sword at the left hip), wrapped "
                      "round the torso")


# ================================================================== 4. satchel and messenger bag
def strap_loop(left_shoulder, width, off):
    c, n, d = sash_plane(left_shoulder, 0.86)
    return band_loop(c, n, width, off)


def buckle(name, at, w, h, mat, rot=(0, 0, 0)):
    F = frame(at, rot)
    outer = ccw([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)])
    inner = offset_poly(outer, min(w, h) * 0.2)
    A.extrude_poly(name, outer, 0.02, mat, F, bevel=0.004, segments=1, holes=[inner[::-1]])
    A.extrude_poly(name + "_tongue", ccw([(-0.006, -h * 0.35), (0.006, -h * 0.35), (0.006, h * 0.42), (-0.006, h * 0.42)]),
                   0.03, mat, F, bevel=0.002, segments=1)


def rounded_bag(name, lo, hi, mat, r=0.05):
    lo, hi = Vector(lo), Vector(hi)
    return A.box(name, hi - lo, (hi + lo) / 2, mat, bevel=r, segments=3)


def _satchel_rig(ob):   # after the mirror: the bag hangs on the right (-X)
    return A.pendulum_rig(ob, Vector((-1.20, 0.0, -0.98)), [Vector((-1.22, 0.0, -1.16)), Vector((-1.22, 0.0, -1.70))])


@item("Satchel", "Leather satchel", views=["front34", "side_r", "back", "back34", "close"],
      close=((-5.6, -3.6, -0.4), (-1.2, 0, -1.3), 75), mirror=True)
def build_satchel(M):
    """built on the left side and mirrored to the RIGHT (1.79 play-test: the sheathed katana hangs at the left hip and
    went through the bag), under the arm: the arm's lowest point is the torso bottom and the leg never passes x = 1,
    so a bag hanging there clears every limb when walking and sprinting"""
    leather = M["leather_oxblood"]
    brass = M["brass"]
    dark = A.mat_leather("StrapDark", (0.12, 0.03, 0.03))
    strapm = A.mat_leather("StrapBrown", (0.20, 0.06, 0.05))
    piece("Satchel", "Torso", rig=_satchel_rig, sway="Pendulum", keepout=(1, 0, 0), lock="X")
    G = strap_loop(False, 0.10, 0.052)
    A.surface("SatchelStrap", G, 0.012, strapm)
    # the drop from the loop on the hip down to the bag (under the arm above z -1)
    for k, y in enumerate((-0.20, 0.20)):
        A.surface(f"SatchelDrop{k}", [[Vector((1.034, y + dy, z)) for z in (-0.60, -0.80, -0.98, -1.05)] for dy in (-0.035, 0.035)], 0.010, strapm)
        A.torus(f"SatchelRing{k}", 0.032, 0.008, (1.10, y, -1.07), brass, rot=(math.radians(90), 0, 0), major=14, minor=5)
    lo, hi = Vector((1.03, -0.34, -1.74)), Vector((1.34, 0.34, -1.10))
    rounded_bag("SatchelBody", lo, hi, leather, r=0.05)
    # the flap over the outer face (+X), two buckled straps, a nameplate
    flap = []
    for i in range(9):
        u = i / 8
        col = []
        for j in range(9):
            t = j / 8
            y = lerp(lo.y + 0.01, hi.y - 0.01, u)
            z = lerp(hi.z + 0.015, lo.z + 0.22, t)
            x = hi.x + 0.014 + 0.012 * math.sin(math.pi * u) * t
            if t > 0.75:
                edge = min(u, 1 - u)
                if edge < 0.18:
                    z += (1 - edge / 0.18) * (t - 0.75) / 0.25 * 0.05
            col.append(Vector((x, y, z)))
        flap.append(col)
    A.surface("SatchelFlap", flap, 0.016, leather)
    for k, y in enumerate((-0.16, 0.16)):
        A.box(f"SatchelBuckleStrap{k}", (0.012, 0.06, 0.26), (hi.x + 0.03, y, lo.z + 0.24), dark, bevel=0.004)
        buckle(f"SatchelBuckle{k}", Vector((hi.x + 0.045, y, lo.z + 0.25)), 0.085, 0.07, brass, rot=(0, 0, math.radians(90)))
    A.extrude_poly("SatchelPlate", ccw([(-0.08, -0.025), (0.08, -0.025), (0.08, 0.025), (-0.08, 0.025)]), 0.008, brass,
                   frame((hi.x + 0.03, 0.0, lo.z + 0.52), (0, 0, math.radians(90))), bevel=0.002, segments=1)
    return dict(notes="oxblood leather, two brass buckles and a nameplate; hangs on the left side below the arm (clear of "
                      "every limb), swings fore and aft on a 2-bone chain, never toward the leg")


@item("MessengerBag", "Messenger bag", views=["front34", "side", "back", "back34", "close"],
      close=((0.0, 7.5, 0.8), (0, 0.5, -0.4), 70))
def build_messenger(M):
    canvas = A.mat_cloth("BagCanvas", (0.035, 0.034, 0.040), weave=160, rough=0.9, sheen=0.2, bump=0.25, twill=False)
    trim = M["leather_brown"]
    brass = M["brass"]
    lo, hi = Vector((-0.74, 0.520, -0.70)), Vector((0.74, 0.730, 0.16))
    # the strap is its own piece (it drapes over the chest layers; the bag sits on the back): its loop is cut where it
    # would cross the bag, so its two ends tuck into the bag's sides
    piece("MessengerStrap", "Torso")
    G = strap_loop(True, 0.11, 0.052)
    inside = lambda p: p.y > 0.3 and lo.x + 0.08 < p.x < hi.x - 0.08 and lo.z - 0.05 < p.z < hi.z + 0.05
    runs, cur = [], []
    for j in range(len(G[0])):
        if any(inside(G[i][j]) for i in range(4)):
            if cur:
                runs.append(cur); cur = []
        else:
            cur.append(j)
    if cur:
        runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(G[0]) - 1:   # the loop's seam: join the two ends
        runs = [runs[-1] + runs[0][1:]] + runs[1:-1]
    web = A.mat_cloth("Webbing", (0.05, 0.045, 0.05), weave=120, rough=0.9, bump=0.3)
    for k, run in enumerate(r for r in runs if len(r) > 1):
        A.surface(f"MessStrap{k}", [[G[i][j] for j in run] for i in range(4)], 0.012, web)
    piece("MessengerBag", "Torso")
    rounded_bag("MessBody", lo, hi, canvas, r=0.06)
    flap = []
    for i in range(13):
        u = i / 12
        col = []
        for j in range(9):
            t = j / 8
            col.append(Vector((lerp(lo.x - 0.01, hi.x + 0.01, u), hi.y + 0.016 + 0.01 * math.sin(math.pi * u),
                               lerp(hi.z + 0.02, lo.z + 0.18, t))))
        flap.append(col)
    A.surface("MessFlap", flap, 0.02, canvas)
    pts = [(lo.x, hi.y + 0.03, hi.z + 0.02), (lo.x, hi.y + 0.035, lo.z + 0.18), (hi.x, hi.y + 0.035, lo.z + 0.18), (hi.x, hi.y + 0.03, hi.z + 0.02)]
    A.tube("MessBinding", pts, 0.016, trim, res=6)
    for k, x in enumerate((-0.42, 0.42)):
        A.box(f"MessStrapV{k}", (0.075, 0.012, 0.40), (x, hi.y + 0.045, lo.z + 0.32), trim, bevel=0.004)
        buckle(f"MessBuckle{k}", Vector((x, hi.y + 0.06, lo.z + 0.24)), 0.1, 0.075, brass, rot=(0, 0, math.radians(180)))
    plate = ccw([(-0.12, -0.08), (0.12, -0.08), (0.12, 0.05), (0, 0.1), (-0.12, 0.05)])
    F = frame((0, hi.y + 0.04, (lo.z + hi.z) / 2 + 0.06), (0, 0, math.radians(180)))
    A.extrude_poly("MessPlate", plate, 0.012, brass, F, bevel=0.003, segments=1)
    A.extrude_poly("MessPlateMoon", crescent(0, -0.005, 0.05, 0.022, 0.012, 0.042), 0.02, M["brassold"], F, bevel=0.002, segments=1)
    return dict(notes="black waxed canvas with leather binding, two brass buckles and a crest plate; on the lower back")


# ================================================================== 5. book strap and the chained grimoire
def book(name, lo, hi, cover, pages, gilt):
    lo, hi = Vector(lo), Vector(hi)
    c = (lo + hi) / 2; sz = hi - lo
    t = 0.016
    A.box(name + "_top", (sz.x, sz.y, t), (c.x, c.y, hi.z - t / 2), cover, bevel=0.006)
    A.box(name + "_bot", (sz.x, sz.y, t), (c.x, c.y, lo.z + t / 2), cover, bevel=0.006)
    A.box(name + "_pages", (sz.x - 0.03, sz.y - 0.03, sz.z - 2 * t), (c.x + 0.012, c.y, c.z), pages, bevel=0.004)
    A.cyl(name + "_spine", sz.z / 2, sz.y, (lo.x + 0.012, c.y, c.z), cover, rot=(math.radians(90), 0, 0), verts=14)
    for k in range(3):
        y = lerp(lo.y + 0.08, hi.y - 0.08, k / 2)
        A.cyl(f"{name}_band{k}", sz.z / 2 + 0.006, 0.018, (lo.x + 0.012, y, c.z), gilt, rot=(math.radians(90), 0, 0), verts=14)


def _bookstrap_rig(ob):
    return A.pendulum_rig(ob, Vector((-1.5, 0, -0.98)), [Vector((-1.5, 0, -1.22)), Vector((-1.5, 0, -1.55))])


@item("BookStrap", "Book strap", views=["front34", "front", "side_r", "close"],
      close=((-4.6, -5.0, -0.4), (-1.5, 0, -1.35), 80))
def build_bookstrap(M):
    pages = M["paper"]
    piece("BookStrap", "RightArm", rig=_bookstrap_rig, sway="Pendulum", keepout=(1, 0, 0))
    covers = [A.mat_leather("BookOx", (0.28, 0.05, 0.05)), A.mat_leather("BookInk", (0.05, 0.07, 0.16)),
              A.mat_leather("BookBlack", (0.06, 0.055, 0.06))]
    z0 = -1.78
    z = z0
    for k, (h, dx, dy) in enumerate(((0.15, 0.0, 0.0), (0.13, 0.025, -0.04), (0.14, -0.02, 0.03))):
        lo = Vector((-1.5 - 0.25 + dx, -0.40 + dy, z)); hi = Vector((-1.5 + 0.25 + dx, 0.40 + dy, z + h))
        book(f"Book{k}", lo, hi, covers[k], pages, M["gold"])
        z += h
    top = z
    strap = A.mat_leather("BookStrapL", (0.16, 0.09, 0.05))
    mz, hz = (top + z0) / 2, (top - z0) / 2 + 0.02
    ring = [(0.43 * math.cos(2 * math.pi * i / 32), mz + hz * math.sin(2 * math.pi * i / 32)) for i in range(33)]
    G = [[Vector((-1.5 + dx, y, zz)) for y, zz in ring] for dx in (-0.04, 0.04)]
    A.surface("BookBand", G, 0.012, strap)
    buckle("BookBuckle", Vector((-1.5, -0.445, mz)), 0.09, 0.08, M["brass"])
    A.tube("BookHandle", [(-1.5, -0.16, top + 0.01), (-1.5, -0.12, top + 0.22), (-1.5, 0.0, top + 0.30), (-1.5, 0.12, top + 0.22),
                          (-1.5, 0.16, top + 0.01)], 0.022, strap, res=8)
    for k, y in enumerate((-0.16, 0.16)):
        A.box(f"BookClip{k}", (0.06, 0.05, 0.05), (-1.5, y, top + 0.02), M["brass"], bevel=0.008)
    return dict(notes="three hardbacks in a buckled strap, held in the right hand; swings from the grip")


def _grim_rig(ob):
    hook = Vector((-1.045, -0.24, -0.97))
    return A.pendulum_rig(ob, hook, [Vector((-1.115, -0.33, -1.16)), Vector((-1.115, -0.14, -1.40)), Vector((-1.115, -0.14, -1.68))])


@item("Grimoire", "Chained grimoire", views=["front34", "front", "side", "close"],
      close=((-5.2, -4.2, -0.6), (-1.05, -0.15, -1.3), 80), mirror=True)
def build_grimoire(M):
    cover = A.mat_leather("GrimCover", (0.10, 0.035, 0.14), scale=2.8)
    pages = A.mat_set("GrimPages", "NH_Paper", tint=(0.78, 0.70, 0.52), scale=3.0, wear=0.3, dirt=0.8)
    glow = A.mat_glow("GrimSigil", (0.62, 0.30, 1.0))
    piece("Grimoire", "Torso", rig=_grim_rig, sway="Pendulum", keepout=(1, 0, 0), lock="X")
    lo = Vector((1.05, -0.36, -1.70)); hi = Vector((1.18, 0.08, -1.16))
    c = (lo + hi) / 2; sz = hi - lo
    t = 0.02
    for k, x in enumerate((lo.x + t / 2, hi.x - t / 2)):
        A.box(f"GrimBoard{k}", (t, sz.y, sz.z), (x, c.y, c.z), cover, bevel=0.007)
    A.box("GrimPagesB", (sz.x - 2 * t, sz.y - 0.03, sz.z - 0.03), (c.x, c.y + 0.012, c.z), pages, bevel=0.004)
    A.cyl("GrimSpine", sz.x / 2 + 0.004, sz.z, (c.x, lo.y + 0.01, c.z), cover, verts=14)
    for k in range(4):
        z = lerp(lo.z + 0.08, hi.z - 0.08, k / 3)
        A.cyl(f"GrimBand{k}", sz.x / 2 + 0.01, 0.022, (c.x, lo.y + 0.01, z), M["brassold"], verts=14)
    for dz in (1, -1):
        y = hi.y - 0.035
        z = hi.z - 0.035 if dz > 0 else lo.z + 0.035
        A.box(f"GrimCorner{dz}", (sz.x + 0.03, 0.07, 0.07), (c.x, y, z), M["brassold"], bevel=0.008)
    A.box("GrimClasp", (sz.x + 0.035, 0.05, 0.06), (c.x, hi.y + 0.012, c.z), A.mat_leather("GrimStrap", (0.05, 0.02, 0.06)), bevel=0.008)
    A.box("GrimClaspPlate", (sz.x + 0.05, 0.03, 0.05), (c.x, hi.y + 0.03, c.z), M["brassold"], bevel=0.006)
    # the sigil on the outward cover (+X): a ring, an eye and runes. Frame: its X/Z plane turned to face +X
    Fc = Matrix.Translation((hi.x + 0.001, c.y - 0.02, c.z)) @ Matrix.Rotation(math.radians(-90), 4, "Z")
    A.extrude_poly("GrimSigilRing", A.circle_pts(0, 0, 0.14, 32), 0.012, glow, Fc, bevel=0.0, holes=[A.circle_pts(0, 0, 0.12, 32)[::-1]])
    eye = ccw(bez((-0.10, 0), (-0.05, 0.06), (0.05, 0.06), (0.10, 0), 10) + bez((0.10, 0), (0.05, -0.06), (-0.05, -0.06), (-0.10, 0), 10))
    A.extrude_poly("GrimSigilEye", eye, 0.012, glow, Fc, bevel=0.0, holes=[ccw(offset_poly(eye, 0.012))[::-1]])
    A.extrude_poly("GrimSigilPupil", A.circle_pts(0, 0, 0.028, 16), 0.014, glow, Fc, bevel=0.0)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        A.extrude_poly(f"GrimRune{k}", ccw([(-0.006, -0.014), (0.006, -0.014), (0.012, 0.014), (-0.012, 0.014)]), 0.01, glow,
                       Fc @ Matrix.Translation((0.165 * math.cos(a), 0, 0.165 * math.sin(a))) @ Matrix.Rotation(-(a - math.pi / 2), 4, "Y"),
                       bevel=0.0)
    A.box("GrimHookPlate", (0.012, 0.10, 0.10), (1.008, -0.24, -0.92), M["iron"], bevel=0.004)
    A.torus("GrimHook", 0.035, 0.010, (1.045, -0.24, -0.97), M["iron"], rot=(math.radians(90), 0, 0), major=14, minor=6)
    A.chain("GrimChain", [(1.05, -0.24, -1.00), (1.08, -0.27, -1.06), (1.11, -0.31, -1.12), (1.115, -0.33, -1.16)], 0.06, M["brassold"])
    A.torus("GrimRing", 0.03, 0.009, (1.115, -0.33, -1.16), M["iron"], major=12, minor=5)
    return dict(notes="violet-black leather, brass corners and bands, a glowing violet eye sigil (emissive mask); hangs "
                      "on an iron chain from a belt hook on the left hip, swings on a 3-bone chain", glow=[0.62, 0.30, 1.0])


# ================================================================== 6. choir collar and ruff
@item("ChoirCollar", "Choir collar", close=((2.4, -5.6, 1.9), (0, 0, 0.8), 95))
def build_choir_collar(M):
    """owner: rework so long hair falls clear of it. Two rounded linen lobes lie on the chest front and roll over the
    torso's front edge at the throat only; nothing reaches the nape or the shoulders, where hair falls"""
    linen = A.mat_cloth("CollarLinen", (0.83, 0.81, 0.76), weave=380, rough=0.78, sheen=0.3, bump=0.06, twill=False)
    lace = A.mat_flat("LaceEdge", (0.88, 0.86, 0.80), rough=0.7, noise=200, bump=0.2, vary=0.04, wear=0.0)
    piece("ChoirCollar", "Torso")
    for side in (-1, 1):
        nu, nv = 14, 12
        G = []
        for i in range(nu + 1):
            u = i / nu
            col = []
            for j in range(nv + 1):
                t = j / nv
                # the lobe's outline: from the throat (x 0.03) out to x 0.40, rounded at the bottom
                x0, x1 = 0.03, 0.40
                x = side * lerp(x0, x1, u)
                depth = 0.40 * math.sin(math.pi * (0.15 + 0.85 * u) * 0.5 + 0.35) ** 0.6   # deeper toward the outside
                L = lerp(0.12, 0.06, u) + depth * t        # down the chest from the edge
                # the first 0.06 rolls over the torso's front edge at the throat (top face, y -0.5 .. -0.44)
                if L <= 0.06:
                    y, z = TORSO_FRONT + (0.06 - L) - 0.0, 1.0 + 0.014
                    y = -0.44 - L
                    q = Vector((x, y, 1.0 + 0.014))
                else:
                    q = Vector((x, TORSO_FRONT - 0.014 - 0.006 * math.sin(math.pi * t), 1.0 - (L - 0.06)))
                # round the outer bottom corner
                if t > 0.7 and u > 0.6:
                    k = (t - 0.7) / 0.3 * (u - 0.6) / 0.4
                    q.z += 0.10 * k ** 1.5
                col.append(q)
            G.append(col)
        G = [[Vector((p.x, p.y, p.z)) for p in c] for c in G]
        A.surface(f"CollarLobe{side}", G, 0.018, linen, caps=True)
        for j in range(0, nv + 1, 1):   # beaded lace along the lobe's outer and bottom edges
            A.sphere(f"Lace{side}_o{j}", 0.016, G[-1][j] + Vector((0, -0.006, 0)), lace, seg=8, rings=5)
        for i in range(0, nu + 1, 1):
            A.sphere(f"Lace{side}_b{i}", 0.016, G[i][-1] + Vector((0, -0.006, 0)), lace, seg=8, rings=5)
    sat = A.mat_cloth("CollarBow", (0.30, 0.02, 0.045), weave=600, rough=0.32, sheen=0.5, bump=0.03, twill=False)
    for side in (-1, 1):
        A.sphere(f"BowLoop{side}", 0.07, (side * 0.085, -0.56, 0.95), sat, scale=(1.4, 0.45, 0.85), seg=14, rings=8)
        A.extrude_poly(f"BowEnd{side}", ccw([(-0.03, 0), (0.03, 0), (0.04, -0.20), (0, -0.17), (-0.04, -0.20)]), 0.01, sat,
                       frame((side * 0.05, -0.548, 0.92), (0, math.radians(side * 12), 0)), bevel=0.002, segments=1)
    A.sphere("BowKnotC", 0.04, (0, -0.575, 0.95), sat, scale=(0.9, 0.7, 1.1), seg=12, rings=8)
    return dict(notes="white linen collar lobes on the chest front with beaded lace edges and a crimson bow; nothing at "
                      "the nape or shoulders (long hair falls clear)")


@item("Ruff", "Falling ruff", close=((2.4, -5.6, 1.7), (0, 0, 0.75), 95))
def build_ruff(M):
    """owner: rework so long hair falls clear of it. A pleated standing frill across the front of the throat over a
    three-tier pleated lace cascade down the chest centre; all of it within x +-0.36, in front of the torso"""
    linen = A.mat_cloth("RuffLinen", (0.86, 0.85, 0.81), weave=420, rough=0.65, sheen=0.35, bump=0.05, twill=False)
    lace = A.mat_flat("RuffLace", (0.90, 0.89, 0.85), rough=0.7, noise=200, bump=0.2, vary=0.04, wear=0.0)
    piece("Ruff", "Torso")
    # the standing frill: figure-eight sets on an arc in front of the throat (radius about the neck axis)
    N = 9
    nu, nv = N * 8, 6
    G = []
    a0, a1 = math.radians(-128), math.radians(-52)
    for i in range(nu + 1):
        th = lerp(a0, a1, i / nu)
        ph = N * (i / nu) * 2 * math.pi
        col = []
        for j in range(nv + 1):
            t = j / nv
            w = math.sin(ph)
            fold = math.copysign(abs(w) ** 0.6, w)
            r = lerp(0.60, 0.76, t)
            z = 0.95 + 0.04 * fold * (0.4 + 0.6 * t) - 0.03 * t
            col.append(Vector((r * math.cos(th) * 0.92, r * math.sin(th) * 1.0 - 0.0, z)))
        G.append(col)
    # keep the frill in front of the torso's front face plane (y <= -0.52) and above the top
    G = [[Vector((p.x, min(p.y, TORSO_FRONT - 0.045), min(p.z, 0.99))) for p in c] for c in G]   # on the chest, below the chin
    A.surface("RuffFrill", G, 0.012, linen, caps=False)
    A.tube("RuffFrillCord", [tuple(G[i][-1]) for i in range(0, nu + 1, 2)], 0.01, lace, res=3)
    # the cascade: three tiers of pleated lace, each hanging over the one below
    top = 0.93
    for k, (w, h) in enumerate(((0.24, 0.15), (0.21, 0.13), (0.18, 0.12))):
        nu2, nv2 = 40, 6
        T = []
        for i in range(nu2 + 1):
            u = i / nu2 - 0.5
            col = []
            for j in range(nv2 + 1):
                t = j / nv2
                pleat = math.sin(u * w * 2 * math.pi / 0.05)
                x = u * w * (1 + 0.15 * t)
                y = TORSO_FRONT - 0.016 - 0.012 * k - 0.022 * t - 0.014 * pleat * (0.3 + 0.7 * t)
                z = top - h * t - 0.03 * (abs(u) * 2) ** 2 * t
                col.append(Vector((x, y, z)))
            T.append(col)
        A.surface(f"RuffTier{k}", T, 0.008, linen, caps=False)
        A.tube(f"RuffTierCord{k}", [tuple(T[i][-1]) for i in range(0, nu2 + 1, 2)], 0.008, lace, res=3)
        top -= h * 0.62
    A.sphere("RuffBrooch", 0.045, (0, TORSO_FRONT - 0.06, 0.90), M["gold"], scale=(1, 0.5, 1.15), seg=14, rings=8)
    A.sphere("RuffBroochStone", 0.028, (0, TORSO_FRONT - 0.08, 0.90), M["crimson_enamel"], scale=(1, 0.5, 1.15), seg=12, rings=8)
    return dict(notes="a starched linen falling ruff: a pleated frill across the front of the throat over a three-tier "
                      "pleated lace cascade, a gold brooch with a crimson stone; clear of the nape and shoulders")
