"""Shared 2D window shapes for props batch 23 (the window kit), in studs on the window's face plane (x across, z up).
Pure Python (no bpy): nh_props_batch23.py models from these, and stained_glass.py paints the stained-glass images from
the same layouts, so the painted lights line up with the stone tracery in front of them.

Outlines are closed and counter-clockwise (x right, z up); offset(pts, d) grows one outward by d.
"""
import math


# ------------------------------------------------------------------ basic outlines

def pointed(hw, zs, za, n=12):
    """A gothic pointed arch from the left springing over the apex to the right springing, as (x, z)."""
    h = za - zs
    c = (h * h - hw * hw) / (2 * hw)
    rho = c + hw
    a0, a1 = math.pi, math.acos(max(-1.0, min(1.0, -c / rho)))
    left = [(c + rho * math.cos(a0 + (a1 - a0) * i / n), zs + rho * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    left[-1] = (0.0, za)
    return left + [(-x, z) for x, z in reversed(left[:-1])]


def arch(hw, z0, zs, za, n=12, cx=0.0):
    """A lancet outline: the foot line, up the right jamb, over the point and down the left (counter-clockwise)."""
    return [(cx - hw, z0), (cx + hw, z0)] + [(cx + x, z) for x, z in reversed(pointed(hw, zs, za, n))]


def circle(cx, cz, r, n=48, a0=0.0):
    return [(cx + math.cos(a0 + k / n * 2 * math.pi) * r, cz + math.sin(a0 + k / n * 2 * math.pi) * r) for k in range(n)]


def segmental(hw, z0, zs, rise, n=12):
    """A window with a segmental (shallow arc) head: foot, right jamb, the arc right to left, left jamb."""
    R = (hw * hw + rise * rise) / (2 * rise)
    zc = zs + rise - R
    a = math.asin(hw / R)
    head = [(R * math.sin(a - 2 * a * i / n), zc + R * math.cos(a - 2 * a * i / n)) for i in range(n + 1)]
    return [(-hw, z0), (hw, z0)] + head


def roundhead(hw, z0, zs, n=16, cx=0.0):
    """A round-arched (semicircular) opening: the foot, the right jamb, the half circle, the left jamb."""
    return [(cx - hw, z0), (cx + hw, z0)] + [(cx + math.cos(k / n * math.pi) * hw, zs + math.sin(k / n * math.pi) * hw) for k in range(n + 1)]


def rect(hw, z0, z1, cx=0.0):
    return [(cx - hw, z0), (cx + hw, z0), (cx + hw, z1), (cx - hw, z1)]


def area(pts):
    return 0.5 * sum(pts[i - 1][0] * p[1] - p[0] * pts[i - 1][1] for i, p in enumerate(pts))


def ccw(pts):
    return pts if area(pts) > 0 else list(reversed(pts))


def resample(pts, step, closed=True):
    """Insert points along long edges (corners kept), so straight jambs can be cut into courses."""
    out = []
    m = len(pts) if closed else len(pts) - 1
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(L / step)))
        for k in range(n):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    if not closed:
        out.append(pts[-1])
    return out


def offset(pts, d, closed=True, miter=3.0):
    """Offset a polyline by d: outward for a counter-clockwise closed outline (to the right of the direction of travel),
    mitred at corners (capped at `miter` x d)."""
    n = len(pts)
    out = []
    for i in range(n):
        if closed or 0 < i < n - 1:
            p, c, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        elif i == 0:
            c, q = pts[0], pts[1]
            p = (2 * c[0] - q[0], 2 * c[1] - q[1])
        else:
            p, c = pts[-2], pts[-1]
            q = (2 * c[0] - p[0], 2 * c[1] - p[1])
        e1 = (c[0] - p[0], c[1] - p[1])
        e2 = (q[0] - c[0], q[1] - c[1])
        l1 = math.hypot(*e1) or 1.0
        l2 = math.hypot(*e2) or 1.0
        n1 = (e1[1] / l1, -e1[0] / l1)
        n2 = (e2[1] / l2, -e2[0] / l2)
        mx, mz = n1[0] + n2[0], n1[1] + n2[1]
        ml = math.hypot(mx, mz)
        if ml < 1e-6:
            mx, mz, ml = n1[0], n1[1], 1.0
        mx, mz = mx / ml, mz / ml
        cosh = mx * n1[0] + mz * n1[1]
        k = min(miter, 1.0 / max(cosh, 1e-3))
        out.append((c[0] + mx * d * k, c[1] + mz * d * k))
    return out


def clip_line(p, u, poly):
    """The parts of the infinite line p + t u inside a simple polygon, as [((x, z), (x, z)), ...]."""
    ts = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ez = b[0] - a[0], b[1] - a[1]
        den = u[0] * ez - u[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wz = a[0] - p[0], a[1] - p[1]
        t = (wx * ez - wz * ex) / den
        s = (wx * u[1] - wz * u[0]) / den
        if 0 <= s < 1:
            ts.append(t)
    ts.sort()
    segs = []
    for i in range(0, len(ts) - 1, 2):
        a = (p[0] + u[0] * ts[i], p[1] + u[1] * ts[i])
        b = (p[0] + u[0] * ts[i + 1], p[1] + u[1] * ts[i + 1])
        segs.append((a, b))
    return segs


def inside(pt, poly):
    x, z = pt
    c = False
    n = len(poly)
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az):
            c = not c
    return c


def lattice_lines(poly, step, mode="diamond", angle=None):
    """Leaded-light came lines clipped to an outline: a diamond lattice (two diagonals) or square quarries (upright grid)."""
    xs = [p[0] for p in poly]
    zs = [p[1] for p in poly]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    span = math.hypot(max(xs) - min(xs), max(zs) - min(zs))
    dirs = []
    if mode == "diamond":
        a = angle or math.radians(62)
        dirs = [(math.cos(a), math.sin(a)), (-math.cos(a), math.sin(a))]
    else:
        dirs = [(1.0, 0.0), (0.0, 1.0)]
    segs = []
    for u in dirs:
        nrm = (-u[1], u[0])
        sp = step if mode == "diamond" else (step[0] if u == (0.0, 1.0) else step[1]) if isinstance(step, tuple) else step
        k = int(span / sp) + 2
        for i in range(-k, k + 1):
            p = (cx + nrm[0] * sp * (i + 0.5 * (mode != "diamond")), cz + nrm[1] * sp * (i + 0.5 * (mode != "diamond")))
            segs += clip_line(p, u, poly)
    return [s for s in segs if math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]) > 0.04]


def foil_outline(cx, cz, r, lobes=4, n=72, a0=math.pi / 2, k=0.46):
    """The outline of a cusped foil (trefoil, quatrefoil...): the union of `lobes` circles round the centre, as a
    star-shaped loop (cusps point inward between the lobes)."""
    cs = [(math.cos(a0 + j * 2 * math.pi / lobes) * r * k, math.sin(a0 + j * 2 * math.pi / lobes) * r * k) for j in range(lobes)]
    a = r * (1 - k)
    out = []
    for i in range(n):
        t = a0 + i / n * 2 * math.pi
        ux, uz = math.cos(t), math.sin(t)
        best = 0.0
        for c in cs:
            uc = ux * c[0] + uz * c[1]
            disc = a * a - (c[0] ** 2 + c[1] ** 2) + uc * uc
            if disc >= 0:
                best = max(best, uc + math.sqrt(disc))
        out.append((cx + ux * best, cz + uz * best))
    return out


def hull(pts):
    """Convex hull (counter-clockwise), monotone chain."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def clip_convex(poly, clip):
    """Sutherland-Hodgman: poly clipped to a convex outline (its convex hull is used, so a hairline dent from an offset
    apex can't cut everything away)."""
    clip = hull(clip)
    out = list(poly)
    n = len(clip)
    for i in range(n):
        a, b = clip[i], clip[(i + 1) % n]
        if not out:
            break
        inp, out = out, []
        def side(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            sp, sq = side(p), side(q)
            if sq >= 0:
                if sp < 0:
                    t = sp / (sp - sq)
                    out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
                out.append(q)
            elif sp >= 0:
                t = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def crescent(cx, cz, r, shift=0.38, n=40, tilt=0.5, bite=0.92):
    """A crescent moon: the outer circle (centre cx, cz, radius r) less a bite circle of radius bite x r whose centre is
    shifted by shift x r toward the angle `tilt`, as a counter-clockwise loop."""
    base = tilt
    ox, oz = math.cos(base) * r * shift, math.sin(base) * r * shift
    r2 = r * bite
    d = r * shift
    a = (r * r - r2 * r2 + d * d) / (2 * d)
    half = math.acos(max(-1.0, min(1.0, a / r)))
    outer = [(cx + math.cos(base + half + (2 * math.pi - 2 * half) * i / n) * r,
              cz + math.sin(base + half + (2 * math.pi - 2 * half) * i / n) * r) for i in range(n + 1)]
    def wrap(t):
        return (t + math.pi) % (2 * math.pi) - math.pi
    pe, ps = outer[-1], outer[0]
    be = math.atan2(pe[1] - cz - oz, pe[0] - cx - ox)
    bs = math.atan2(ps[1] - cz - oz, ps[0] - cx - ox)
    mid = base + math.pi
    e, s = wrap(be - mid), wrap(bs - mid)
    inner = [(cx + ox + math.cos(mid + e + (s - e) * i / n) * r2, cz + oz + math.sin(mid + e + (s - e) * i / n) * r2) for i in range(1, n)]
    return ccw(outer + inner)


# ------------------------------------------------------------------ the stained-glass layouts

class Tracery:
    """TraceryWindow: four lights under two pair arches and a head circle."""
    HW, Z0, ZS, ZA = 3.3, 0.7, 6.8, 11.4
    BAR = 0.2                                   # tracery bar width
    PAIR = [(-1.65, 1.65), (1.65, 1.65)]       # (centre x, half width) of the two sub-arches
    PAIR_ZA = 6.8 + 2.35
    LIGHTS = [-2.475, -0.825, 0.825, 2.475]    # lancet centres, half width 0.825
    LIGHT_HW, LIGHT_ZA = 0.825, 6.8 + 1.25
    HEAD = (0.0, 9.75, 1.1)                    # the head circle (x, z, r)
    SPANDREL = [(-1.65, 8.45, 0.38), (1.65, 8.45, 0.38)]

    @classmethod
    def outline(cls, n=16):
        return arch(cls.HW, cls.Z0, cls.ZS, cls.ZA, n)

    @classmethod
    def light(cls, k, n=10):
        return arch(cls.LIGHT_HW, cls.Z0, cls.ZS, cls.LIGHT_ZA, n, cx=cls.LIGHTS[k])


class Rose:
    """RoseWindow: a wheel of twelve petals round a hub, small foils between the petal heads."""
    CZ, R = 5.0, 3.9                           # opening centre height and radius (stone beyond)
    HUB = 0.85
    SPOKE_R = 2.75                             # spokes run from the hub to here
    PETAL_APEX = 3.55
    FOIL_R, FOIL_AT = 0.24, 3.43
    N = 12
    BAR = 0.17

    @classmethod
    def angles(cls):
        return [math.pi / 2 + k * 2 * math.pi / cls.N for k in range(cls.N)]

    @classmethod
    def petal_head(cls, k, n=8):
        """The pointed head of petal k (between spokes k and k+1), as (x, z) from spoke k's end to spoke k+1's."""
        a0 = cls.angles()[k]
        a1 = a0 + 2 * math.pi / cls.N
        am = (a0 + a1) / 2
        # build the arch in a local frame (x across the petal, z outward), then rotate into place
        p0 = (math.cos(a0) * cls.SPOKE_R, math.sin(a0) * cls.SPOKE_R)
        p1 = (math.cos(a1) * cls.SPOKE_R, math.sin(a1) * cls.SPOKE_R)
        half = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 2
        base = math.hypot((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        local = pointed(half, base, cls.PETAL_APEX, n)
        ux, uz = math.cos(am), math.sin(am)            # outward
        vx, vz = -uz, ux                               # across (toward a1)
        out = []
        for x, z in local:
            out.append((ux * z + vx * x, uz * z + vz * x))
        out = [(x, z + cls.CZ) for x, z in out]
        return list(reversed(out)) if math.hypot(out[0][0] - p0[0], out[0][1] - cls.CZ - p0[1]) > 0.01 else out


class StainedLancet:
    HW, Z0, ZS, ZA = 1.15, 0.7, 6.3, 8.4
    FOIL = (0.0, 7.3, 0.42)                     # the trefoil in the head
    SADDLE = [2.0, 3.4, 4.8, 5.95]             # iron saddle bars (z)

    @classmethod
    def outline(cls, n=14):
        return arch(cls.HW, cls.Z0, cls.ZS, cls.ZA, n)


def bounds(pts):
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    return min(xs), max(xs), min(zs), max(zs)
