"""The gothic motifs for props batch 29's textiles (weave_textiles.py and tapestry_weave.py): original designs drawn on a
weave_textiles.Canvas in px (y down), each in woven-rug detail: an outline round every shape, two or three tones
inside it, and the small inner drawing that makes it read (finger bones, feather quills, wing veins, iris rays...).

Colours are dye names from weave_textiles.C or sRGB tuples; tone(c, k) darkens (k < 1) or lightens (k > 1) one. The
rug weave builds its knot palette from the colours a design actually used, so derived tones survive the knotting.
"""
import math

from weave_textiles import C, band, circle, crescent, diamond, foil, leaf, lobed, rot, star


def rgb(c):
    return C[c] if isinstance(c, str) else tuple(int(v) for v in c)


def tone(c, k):
    r, g, b = rgb(c)
    if k <= 1:
        return (int(r * k), int(g * k), int(b * k * 1.04 if k < 0.6 else b * k))
    t = min(1.0, k - 1)
    return (int(r + (255 - r) * t * 1.0), int(g + (255 - g) * t * 0.94), int(b + (255 - b) * t * 0.85))


def _w(s, k=0.012):
    return max(2, s * k)


# ------------------------------------------------------------------ bat

def bat(cv, cx, cy, s, col, eye=None, tilt=0.0, ol=None):
    """A bat, wings spread, s across: the arm and five finger bones, the membrane panels between them shaded in turn and
    scalloped at the edge, a furred body, pointed ears with dark insides, glowing eyes, two small fangs."""
    ol = ol or tone(col, 0.45)
    sh, hi = tone(col, 0.72), tone(col, 1.35)
    P = lambda u, v: (cx + u * s / 2, cy + v * s / 2)
    R = lambda pts: rot(pts, cx, cy, tilt)
    shoulder, wrist = (0.08, -0.06), (0.47, -0.27)
    top = [(0.08, -0.06), (0.2, -0.16), (0.34, -0.24), (0.47, -0.27), (0.62, -0.23), (0.8, -0.13), (0.99, 0.02)]
    tips = [(0.99, 0.02), (0.8, 0.21), (0.6, 0.26), (0.38, 0.21), (0.13, 0.13)]

    def scallop(a, b, n=8):
        return [(a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n - 0.08 * math.sin(math.pi * j / n)) for j in range(1, n)]
    for sx in (-1, 1):
        X = lambda pts: [P(sx * u, v) for u, v in pts]
        edge = top[:]
        for a, b in zip(tips, tips[1:]):
            edge += scallop(a, b) + [b]
        cv.poly(R(X(edge + [(0.06, 0.12)])), col, ol, _w(s, 0.014))
        # alternate panels a shade darker, between each pair of finger bones
        for k in range(len(tips) - 1):
            if k % 2 == 0:
                cv.poly(R(X([wrist, tips[k]] + scallop(tips[k], tips[k + 1]) + [tips[k + 1]])), sh)
        cv.poly(R(X([shoulder, wrist, tips[-1], (0.06, 0.12)])), sh)
        for t in tips[:-1]:
            cv.line(R(X([wrist, t])), hi, _w(s, 0.011))
        cv.line(R(X([shoulder, wrist])), hi, _w(s, 0.02))
        cv.line(R(X([wrist, tips[-1]])), hi, _w(s, 0.009))
        cv.poly(R(X([(0.46, -0.27), (0.5, -0.34), (0.5, -0.27)])), ol)            # the thumb claw
    body = [P(u * 0.11, 0.04 + v * 0.2) for u, v in circle(0, 0, 1, 28)]
    cv.poly(R(body), col, ol, _w(s, 0.012))
    for k in range(4):
        y = -0.06 + k * 0.07
        cv.line(R([P(-0.05, y), P(0, y + 0.03), P(0.05, y)]), hi, _w(s, 0.008))
    for sx in (-1, 1):
        cv.poly(R([P(sx * 0.025, -0.2), P(sx * 0.11, -0.35), P(sx * 0.09, -0.16)]), col, ol, _w(s, 0.01))
        cv.poly(R([P(sx * 0.045, -0.2), P(sx * 0.1, -0.3), P(sx * 0.085, -0.19)]), tone(col, 0.5))
    cv.poly(R([P(u * 0.09, -0.16 + v * 0.085) for u, v in circle(0, 0, 1, 24)]), col, ol, _w(s, 0.01))
    if eye:
        for sx in (-1, 1):
            cv.circle(*R([P(sx * 0.038, -0.17)])[0], 0.02 * s, eye)
            cv.circle(*R([P(sx * 0.032, -0.176)])[0], 0.007 * s, tone(eye, 1.6))
    for sx in (-1, 1):
        cv.poly(R([P(sx * 0.03, -0.12), P(sx * 0.012, -0.12), P(sx * 0.02, -0.095)]), "bone")


# ------------------------------------------------------------------ raven

def raven(cv, cx, cy, s, col, eye=None, accent=None, beak=None, claw=None):
    """A raven displayed (heraldic), s high: raised wings of outlined feathers (six long primaries with their quills,
    secondaries, three rows of covert scales), scaled breast feathers, a fanned tail, the head turned with a grey beak,
    a gilt eye, claws."""
    hi = accent or tone(col, 1.22)
    ol = tone(col, 0.6)
    beak = beak or tone(col, 1.3)
    claw = claw or "bone"
    P = lambda u, v: (cx + u * s, cy + v * s)
    W = _w(s, 0.008)
    for sx in (-1, 1):
        # primaries, rooted along the wing's outer edge, fanning from up-and-out to out
        for k in range(6, -1, -1):
            t = k / 6
            root = P(sx * (0.5 - 0.16 * t), -0.34 + 0.36 * t)
            a = math.radians(30 + 62 * t)
            L = (0.31 - 0.08 * t) * s
            tip = (root[0] + sx * math.sin(a) * L, root[1] - math.cos(a) * L)
            back = (root[0] - sx * math.sin(a) * 0.1 * s, root[1] + math.cos(a) * 0.1 * s)
            cv.poly(leaf(back[0], back[1], tip[0], tip[1], 0.088 * s), col, hi, W)
            cv.line([back, ((back[0] + tip[0] * 3) / 4, (back[1] + tip[1] * 3) / 4)], hi, W * 0.8)
        # the wing's base, secondaries along its foot, then rows of coverts
        cv.poly([P(sx * 0.05, -0.1), P(sx * 0.28, -0.29), P(sx * 0.52, -0.37), P(sx * 0.57, -0.2), P(sx * 0.36, 0.04), P(sx * 0.1, 0.11)], col, hi, W)
        for k in range(5):
            r0 = P(sx * (0.1 + k * 0.06), 0.06 - k * 0.012)
            cv.poly(leaf(r0[0], r0[1], r0[0] + sx * 0.05 * s, r0[1] + 0.13 * s, 0.07 * s), col, hi, W)
        # coverts: rows of small pointed feathers lying toward the wingtip, overlapping like scales
        for row in range(3):
            n = 6 - row
            for k in range(n):
                t = k / max(1, n - 1)
                u = sx * (0.1 + t * (0.36 - row * 0.06))
                v = -0.1 - t * (0.2 - row * 0.03) + row * 0.075
                r0 = P(u, v)
                r1 = P(u + sx * 0.07, v + 0.05)
                cv.poly(leaf(r0[0], r0[1], r1[0], r1[1], 0.05 * s), col, hi, W)
    # the tail fan and the body with its breast scales
    for k in range(5):
        a = math.radians(-32 + 16 * k)
        cv.poly(leaf(*P(0, 0.18), *P(math.sin(a) * 0.28, 0.18 + math.cos(a) * 0.28), 0.075 * s), col, hi, W)
    cv.poly([P(u * 0.13, 0.06 + v * 0.22) for u, v in circle(0, 0, 1, 32)], col, hi, W)
    for row in range(4):
        for k in range(3 - row % 2):
            u = -0.06 + k * 0.06 + (0.03 if row % 2 else 0)
            v = -0.06 + row * 0.07
            cv.line([P(u - 0.03, v), P(u, v + 0.025), P(u + 0.03, v)], hi, W * 0.9)
    # the head turned right, the beak, the eye
    cv.poly([P(u * 0.095, -0.2 + v * 0.088) for u, v in circle(0, 0, 1, 28)], col, hi, W)
    cv.poly([P(0.06, -0.24), P(0.25, -0.212), P(0.07, -0.163)], beak, ol, W)
    cv.line([P(0.07, -0.205), P(0.21, -0.208)], ol, W * 0.8)
    if eye:
        cv.circle(*P(0.035, -0.215), 0.022 * s, eye)
        cv.circle(*P(0.035, -0.215), 0.01 * s, ol)
        cv.circle(*P(0.03, -0.221), 0.005 * s, "bone")
    for sx in (-1, 1):
        cv.line([P(sx * 0.05, 0.25), P(sx * 0.09, 0.34)], tone(col, 1.15), 0.025 * s)
        for k in (-1, 0, 1):
            cv.line([P(sx * 0.09, 0.34), P(sx * 0.09 + k * 0.045, 0.385)], claw, 0.014 * s)


# ------------------------------------------------------------------ moth

def moth(cv, cx, cy, s, col, accent, mark, spot=None, ol=None):
    """A night moth, s across: outlined forewings with veins, a crescent mark and a row of dots along the edge, rounded
    hindwings with ringed eye spots, a furred thorax with a crescent, a banded abdomen, feathered antennae."""
    ol = ol or tone(col, 0.45)
    P = lambda u, v: (cx + u * s / 2, cy + v * s / 2)
    W = _w(s, 0.01)
    for sx in (-1, 1):
        X = lambda pts: [P(sx * u, v) for u, v in pts]
        hind = [(0.08, 0.02), (0.45, 0.02), (0.68, 0.2), (0.6, 0.45), (0.3, 0.5), (0.1, 0.25)]
        cv.poly(X(hind), col, ol, W)
        cv.poly(X([(0.15, 0.08), (0.42, 0.08), (0.58, 0.22), (0.52, 0.4), (0.3, 0.44), (0.15, 0.24)]), accent)
        for a in (0.1, 0.45, 0.8):
            cv.line(X([(0.1, 0.06), (0.1 + 0.55 * math.cos(a), 0.06 + 0.42 * math.sin(a))]), tone(accent, 0.6), W * 0.7)
        cv.circle(*P(sx * 0.36, 0.26), 0.08 * s, ol)
        cv.circle(*P(sx * 0.36, 0.26), 0.072 * s, spot or mark)
        cv.circle(*P(sx * 0.36, 0.26), 0.04 * s, col)
        cv.circle(*P(sx * 0.345, 0.248), 0.012 * s, tone(col, 1.5))
        fore = [(0.05, -0.08), (0.3, -0.42), (0.62, -0.5), (0.98, -0.42), (0.9, -0.2), (0.6, 0.0), (0.12, 0.04)]
        cv.poly(X(fore), col, ol, W)
        cv.poly(X([(0.16, -0.08), (0.34, -0.34), (0.62, -0.42), (0.86, -0.36), (0.8, -0.22), (0.56, -0.08), (0.2, -0.02)]), accent)
        for (u, v) in ((0.4, -0.46), (0.62, -0.47), (0.85, -0.4), (0.82, -0.2), (0.6, -0.03)):
            cv.line(X([(0.1, -0.04), (u, v)]), tone(accent, 0.6), W * 0.7)
        cv.poly(X([(0.62, -0.18), (0.7, -0.3), (0.66, -0.16)]), tone(accent, 1.4))
        cv.poly(crescent(*P(sx * 0.6, -0.26), 0.075 * s, tilt=math.pi if sx > 0 else 0.0), mark)
        for k in range(6):
            x = 0.3 + k * 0.11
            cv.circle(*P(sx * x, -0.44 + abs(x - 0.62) * 0.28), 0.013 * s, mark)
        a0, a1 = P(sx * 0.03, -0.2), P(sx * 0.24, -0.58)
        cv.line([a0, a1], ol, 0.014 * s)
        for k in range(1, 9):
            t = k / 9
            x, y = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
            L = 0.04 * s * math.sin(math.pi * t) + 0.01 * s
            cv.line([(x, y), (x + sx * L, y + L * 0.4)], ol, 0.007 * s)
            cv.line([(x, y), (x - sx * L * 0.3, y - L * 0.8)], ol, 0.007 * s)
    cv.poly([P(u * 0.075, 0.08 + v * 0.36) for u, v in circle(0, 0, 1, 28)], col, ol, W)
    for k in range(5):
        v = 0.0 + k * 0.1
        cv.line([P(-0.06, v), P(0, v + 0.02), P(0.06, v)], tone(col, 0.6), W)
    cv.poly([P(u * 0.1, -0.14 + v * 0.11) for u, v in circle(0, 0, 1, 24)], accent, ol, W)
    cv.poly(crescent(*P(0, -0.14), 0.045 * s, tilt=math.pi / 2), mark)
    cv.poly([P(u * 0.06, -0.24 + v * 0.05) for u, v in circle(0, 0, 1, 16)], col, ol, W)


# ------------------------------------------------------------------ eye

def eye(cv, cx, cy, s, white, iris, pupil, lid=None, lashes=True):
    """A watchful eye, s wide: a heavy lid, a shaded white, a ringed iris with rays and a pale ring, a slit pupil, two
    glints, the inner corner, curved lashes."""
    lid = lid or pupil

    def almond(k, up, dn, dy=0.0):
        a = [(cx + (t - 0.5) * s * k, cy + dy - math.sin(t * math.pi) * s * up) for t in [i / 40 for i in range(41)]]
        b = [(cx + (t - 0.5) * s * k, cy + dy + math.sin(t * math.pi) * s * dn) for t in [i / 40 for i in range(39, 0, -1)]]
        return a + b
    cv.poly(almond(1.04, 0.3, 0.24), lid)
    cv.poly(almond(0.92, 0.24, 0.19), white)
    cv.poly(almond(0.92, 0.24, -0.12), tone(white, 0.72))          # the lid's shadow over the top of the white
    cv.poly([(cx - 0.46 * s, cy), (cx - 0.38 * s, cy - 0.03 * s), (cx - 0.36 * s, cy + 0.03 * s)], tone("rose", 1.1))
    ri = s * 0.165
    cv.circle(cx, cy, ri * 1.08, pupil)
    cv.circle(cx, cy, ri, tone(iris, 0.75))
    cv.circle(cx, cy, ri * 0.86, iris)
    for k in range(28):
        a = k / 28 * 2 * math.pi
        c = tone(iris, 0.6) if k % 2 else tone(iris, 1.35)
        cv.line([(cx + math.cos(a) * ri * 0.4, cy + math.sin(a) * ri * 0.4), (cx + math.cos(a) * ri * 0.84, cy + math.sin(a) * ri * 0.84)], c, max(1.5, s * 0.008))
    cv.ring(cx, cy, ri * 0.42, max(2, s * 0.012), tone(iris, 1.6))
    cv.poly([(cx, cy - ri * 0.86), (cx + s * 0.042, cy), (cx, cy + ri * 0.86), (cx - s * 0.042, cy)], pupil)
    cv.circle(cx - s * 0.055, cy - s * 0.06, s * 0.028, "bone")
    cv.circle(cx + s * 0.04, cy + s * 0.05, s * 0.012, tone("bone", 0.9))
    up = [(cx + (t - 0.5) * s * 1.04, cy - math.sin(t * math.pi) * s * 0.3) for t in [i / 40 for i in range(41)]]
    cv.line(up, lid, s * 0.035)
    cv.line([(cx + (t - 0.5) * s * 0.9, cy + math.sin(t * math.pi) * s * 0.21) for t in [i / 30 for i in range(4, 27)]], tone(lid, 1.6), s * 0.012)
    if lashes:
        for k in range(9):
            t = 0.1 + k * 0.8 / 8
            x, y = cx + (t - 0.5) * s * 1.04, cy - math.sin(t * math.pi) * s * 0.3
            a = -math.pi / 2 + (t - 0.5) * 1.9
            L = s * (0.08 + 0.04 * math.sin(t * math.pi))
            pts = [(x + math.cos(a + 0.35 * j / 4 * (1 if t > 0.5 else -1)) * L * j / 4, y + math.sin(a + 0.35 * j / 4 * (1 if t > 0.5 else -1)) * L * j / 4) for j in range(5)]
            cv.poly(band(pts, s * 0.024, s * 0.004), lid)


# ------------------------------------------------------------------ webs, spiders, roses, stems

def web(cv, cx, cy, R, col, width, spokes=12, rings=8, a0=0.0, span=2 * math.pi, dew=None):
    """A cobweb: spokes from the hub, sagging threads between them, dew drops caught on some crossings (a corner web
    when span < 2 pi)."""
    full = span >= 2 * math.pi - 1e-6
    angs = [a0 + span * k / spokes for k in range(spokes + (0 if full else 1))]
    for a in angs:
        cv.line([(cx, cy), (cx + math.cos(a) * R, cy + math.sin(a) * R)], col, width)
    pairs = [(angs[k], angs[k + 1]) for k in range(len(angs) - 1)]
    if full:
        pairs.append((angs[-1], angs[0] + 2 * math.pi))
    dew = dew or tone(col, 1.4)
    for r in range(1, rings + 1):
        rr = R * r / (rings + 0.6)
        pts = []
        for a, b in pairs:
            for j in range(10):
                t = j / 10
                ang = a + (b - a) * t
                sag = 1 - 0.1 * math.sin(math.pi * t)
                pts.append((cx + math.cos(ang) * rr * sag, cy + math.sin(ang) * rr * sag))
        b = pairs[-1][1]
        pts.append((cx + math.cos(b) * rr, cy + math.sin(b) * rr))
        cv.line(pts, col, width * 0.75)
        for k, (a, _) in enumerate(pairs):
            if (k * 7 + r * 3) % 5 == 0:
                cv.circle(cx + math.cos(a) * rr, cy + math.sin(a) * rr, width * 1.3, dew)


def spider(cv, cx, cy, s, col, mark=None, thread=True):
    """A spider on its thread, s across its legs: jointed legs with knees, a glossy abdomen with an hourglass mark."""
    hi = tone(col, 1.8)
    if thread:
        cv.line([(cx, cy - 0.12 * s), (cx, cy - 0.9 * s)], tone(col, 2.2), max(2, s * 0.018))
    for sx in (-1, 1):
        for k in range(4):
            a = math.radians(-55 + k * 32)
            hip = (cx + sx * 0.06 * s, cy - 0.07 * s)
            knee = (cx + sx * math.cos(a) * s * 0.3, cy - 0.18 * s + math.sin(a) * s * 0.3)
            foot = (cx + sx * math.cos(a) * s * 0.52, cy + math.sin(a) * s * 0.5 + 0.1 * s)
            cv.line([hip, knee, foot], col, s * 0.034)
            cv.circle(*knee, s * 0.022, hi)
    cv.poly([(cx + u * s * 0.17, cy + 0.09 * s + v * s * 0.21) for u, v in circle(0, 0, 1, 24)], col)
    cv.poly([(cx + u * s * 0.105, cy - 0.1 * s + v * s * 0.09) for u, v in circle(0, 0, 1, 18)], col)
    cv.circle(cx - 0.06 * s, cy + 0.02 * s, 0.035 * s, hi)
    if mark:
        cv.poly([(cx - 0.05 * s, cy + 0.02 * s), (cx + 0.05 * s, cy + 0.02 * s), (cx, cy + 0.09 * s)], mark)
        cv.poly([(cx - 0.05 * s, cy + 0.17 * s), (cx + 0.05 * s, cy + 0.17 * s), (cx, cy + 0.1 * s)], mark)
    for sx in (-1, 1):
        cv.circle(cx + sx * 0.035 * s, cy - 0.13 * s, 0.016 * s, mark or hi)


def thorn_vine(cv, path, w, col, every=5, thorn=1.7):
    """A thorned stem: a band with a light line down it and thorns hooked back on alternate sides."""
    cv.poly(band(path, w, w * 0.75), col)
    hi = tone(col, 1.6)
    for i in range(every, len(path) - 1, every):
        (ax, ay), (bx, by) = path[i - 1], path[i + 1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        sd = 1 if (i // every) % 2 else -1
        x, y = path[i]
        cv.poly([(x - ux * w * 0.8, y - uy * w * 0.8), (x + nx * sd * w * thorn + ux * w * 0.7, y + ny * sd * w * thorn + uy * w * 0.7),
                 (x + ux * w * 0.4, y + uy * w * 0.4)], col)
    off = [(x - (path[min(i + 1, len(path) - 1)][1] - path[max(i - 1, 0)][1]) * 0.0, y) for i, (x, y) in enumerate(path)]
    cv.line([(x, y - w * 0.2) for x, y in off], hi, max(1.5, w * 0.18))


def rose(cv, cx, cy, r, col, dark, light, a0=0.0):
    """A full-blown rose from above: an outlined outer ring of petals with their separations, a turned inner ring, a
    tight spiral heart, light on the curled-back petal edges."""
    cv.poly(lobed(cx, cy, r, r, 5, 0.18, a0=a0), dark)
    cv.poly(lobed(cx, cy, r * 0.92, r * 0.92, 5, 0.18, a0=a0), col)
    for k in range(5):
        a = a0 + (k + 0.5) * 2 * math.pi / 5
        cv.line([(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55), (cx + math.cos(a + 0.12) * r * 0.86, cy + math.sin(a + 0.12) * r * 0.86)], dark, r * 0.05)
    cv.poly(lobed(cx, cy, r * 0.68, r * 0.68, 5, 0.2, a0=a0 + math.pi / 5), dark)
    cv.poly(lobed(cx, cy, r * 0.6, r * 0.6, 5, 0.2, a0=a0 + math.pi / 5), tone(col, 1.12))
    cv.poly(lobed(cx, cy, r * 0.4, r * 0.4, 4, 0.2, a0=a0), dark)
    cv.poly(lobed(cx, cy, r * 0.34, r * 0.34, 4, 0.2, a0=a0), col)
    sp = [(cx + math.cos(a0 + t * 10) * r * 0.3 * (1 - t), cy + math.sin(a0 + t * 10) * r * 0.3 * (1 - t)) for t in [i / 60 for i in range(61)]]
    cv.line(sp, dark, r * 0.06)
    for k in range(5):
        a = a0 + k * 2 * math.pi / 5 + 0.25
        arc = [(cx + math.cos(a + t * 0.7) * r * 0.8, cy + math.sin(a + t * 0.7) * r * 0.8) for t in [i / 10 for i in range(11)]]
        cv.poly(band(arc, r * 0.02, r * 0.08), light)
        a += math.pi / 5
        arc = [(cx + math.cos(a + t * 0.5) * r * 0.52, cy + math.sin(a + t * 0.5) * r * 0.52) for t in [i / 10 for i in range(11)]]
        cv.poly(band(arc, r * 0.015, r * 0.05), light)


def rose_leaf(cv, x0, y0, x1, y1, w, col, vein):
    """A serrated rose leaf with a midrib and side veins."""
    pts = leaf(x0, y0, x1, y1, w, n=16)
    n = len(pts)
    jag = []
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    for i, (x, y) in enumerate(pts):
        k = 1.0 + (0.08 if i % 2 else -0.02)
        jag.append((mx + (x - mx) * k, my + (y - my) * k))
    cv.poly(jag, col, vein, max(1.5, w * 0.05))
    cv.poly(leaf(x0, y0, x1, y1, w * 0.5, n=12)[: n // 2], tone(col, 1.18))
    cv.line([(x0, y0), (x0 + (x1 - x0) * 0.9, y0 + (y1 - y0) * 0.9)], vein, max(2, w * 0.08))
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for t in (0.3, 0.5, 0.7):
        bx, by = x0 + dx * t, y0 + dy * t
        for sd in (-1, 1):
            cv.line([(bx, by), (bx + dx * 0.12 + nx * sd * w * 0.32, by + dy * 0.12 + ny * sd * w * 0.32)], vein, max(1.5, w * 0.045))


def rose_spray(cv, path, w, stem, flower, dark, light, leafc, vein, every=12, r=None):
    """A thorned stem along a path with roses and serrated leaves set along it."""
    thorn_vine(cv, path, w, stem, every=max(3, every // 3))
    r = r or w * 3.2
    for i in range(every // 2, len(path) - 2, every):
        (ax, ay), (bx, by) = path[i - 1], path[i + 1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        x, y = path[i]
        sd = 1 if (i // every) % 2 else -1
        rose_leaf(cv, x, y, x + nx * sd * r * 1.7 + dx / L * r * 0.6, y + ny * sd * r * 1.7 + dy / L * r * 0.6, r * 0.8, leafc, vein)
        rose(cv, x - nx * sd * r * 0.45, y - ny * sd * r * 0.45, r, flower, dark, light, a0=i * 0.7)


# ------------------------------------------------------------------ candle, bell, sun

def candle(cv, cx, base_y, w, h, wax, flame, glow, holder=None):
    """A candle standing at base_y: a shaded wax column with drips, a flame with its hot core, a dish."""
    cv.rect(cx - w / 2, base_y - h, cx + w / 2, base_y, wax)
    cv.rect(cx + w * 0.18, base_y - h, cx + w / 2, base_y, tone(wax, 0.8))
    cv.rect(cx - w / 2, base_y - h, cx - w * 0.3, base_y, tone(wax, 1.15))
    for k, dx in enumerate((-0.3, 0.15, 0.35)):
        cv.poly(leaf(cx + dx * w, base_y - h, cx + dx * w, base_y - h + h * (0.18 + 0.12 * k), w * 0.25), tone(wax, 1.08))
    cv.line([(cx, base_y - h), (cx, base_y - h - w * 0.25)], "soot", max(2, w * 0.07))
    cv.poly(leaf(cx, base_y - h - w * 0.05, cx, base_y - h - w * 1.7, w * 0.75), tone(flame, 0.85))
    cv.poly(leaf(cx, base_y - h - w * 0.1, cx, base_y - h - w * 1.45, w * 0.55), flame)
    cv.poly(leaf(cx, base_y - h - w * 0.15, cx, base_y - h - w * 0.95, w * 0.3), glow)
    if holder:
        cv.poly([(cx - w * 1.2, base_y), (cx + w * 1.2, base_y), (cx + w * 0.8, base_y + w * 0.4), (cx - w * 0.8, base_y + w * 0.4)], holder)


def bell(cv, cx, cy, s, col, dark):
    """A church bell, s high: shaded down one side, a lip band, a crown and its clapper."""
    half = [(0.06, -0.5), (0.18, -0.46), (0.24, -0.3), (0.27, 0.0), (0.33, 0.25), (0.45, 0.4), (0.45, 0.46)]
    cv.poly([(cx + u * s, cy + v * s) for u, v in half] + [(cx - u * s, cy + v * s) for u, v in reversed(half)], col, dark, _w(s, 0.012))
    cv.poly([(cx + u * s * 0.55 + 0.12 * s, cy + v * s) for u, v in half[1:-1]] + [(cx + u * s, cy + v * s) for u, v in reversed(half[1:-1])], tone(col, 0.75))
    cv.poly([(cx - u * s * 0.3 - 0.08 * s, cy + v * s) for u, v in half[1:-2]] + [(cx - u * s * 0.5 - 0.1 * s, cy + v * s) for u, v in reversed(half[1:-2])], tone(col, 1.3))
    cv.rect(cx - 0.45 * s, cy + 0.4 * s, cx + 0.45 * s, cy + 0.46 * s, dark)
    cv.circle(cx, cy + 0.53 * s, 0.07 * s, dark)
    cv.rect(cx - 0.1 * s, cy - 0.58 * s, cx + 0.1 * s, cy - 0.48 * s, dark)
    for v in (-0.2, 0.3):
        cv.line([(cx - (0.24 if v < 0 else 0.34) * s, cy + v * s), (cx + (0.24 if v < 0 else 0.34) * s, cy + v * s)], dark, 0.02 * s)


def sun_face(cv, cx, cy, r, col, dark, rays=16):
    """A radiant sun: alternate straight and flaming rays, each outlined, round a ringed disc."""
    for k in range(rays):
        a = k / rays * 2 * math.pi
        if k % 2:
            pts = [(cx + math.cos(a + 0.12 * math.sin(t * 9)) * r * (1.05 + 0.6 * t), cy + math.sin(a + 0.12 * math.sin(t * 9)) * r * (1.05 + 0.6 * t)) for t in [i / 16 for i in range(17)]]
            cv.poly(band(pts, r * 0.16, r * 0.02), col, dark, max(1.5, r * 0.02))
        else:
            cv.poly(leaf(cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9, cx + math.cos(a) * r * 1.95, cy + math.sin(a) * r * 1.95, r * 0.26), col, dark, max(1.5, r * 0.02))
    cv.circle(cx, cy, r, col, dark, max(2, r * 0.04))
    cv.circle(cx + r * 0.15, cy + r * 0.15, r * 0.8, tone(col, 0.88))
    cv.circle(cx - r * 0.1, cy - r * 0.1, r * 0.7, col)
    cv.ring(cx, cy, r * 0.86, r * 0.05, dark)
