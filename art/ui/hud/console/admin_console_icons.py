"""The Headmaster's Console: 3D-rendered icons (Blender 5.2, headless).
E:/Blender/blender.exe -b --factory-startup -P admin_console_icons.py -- <out dir> [--quick] [--only name,name]

Same materials, world, lights, camera and finish as admin_console_render.py (it loads that file's scene, material and
geometry code), so the icons are cast in the console's own iron, brass, crimson enamel, ruby and velvet.
Each icon is 64x64 design px, rendered at 4x (256 px) on a transparent film: bold brass silhouettes with one or two
crimson / ruby / enamel accents, made to read at 64 px in the card and rail wells (iron, dark).
Icons: one per section (11) and one per card family (38). The command -> icon map is in ICONS.md next to this file.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(HERE, "admin_console_render.py"), encoding="utf-8").read()
exec(compile(_src[: _src.index("# ---------------------------------------------------------------- pieces")], "admin_console_render.py", "exec"))
PXSCALE = 4  # icons: 4x (the console art's 2x is too soft for 64 px detail)
SEG = 3 if QUICK else 5


# ---------------------------------------------------------------- 2D outlines (design px)
def circ(r, cx=0.0, cy=0.0, n=48, a0=0.0, a1=360.0, ry=None):
    ry = r if ry is None else ry
    full = abs(a1 - a0) >= 360 or (a1 == 360.0 and a0 != 0.0 and a0 % 360 != 0)
    if full and abs(a1 - a0) < 360:
        a1 = a0 + 360
    k = n if full else n + 1
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(k)]


def rect(w, h, cx=0.0, cy=0.0, rot=0.0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def star(n, ro, ri, cx=0.0, cy=0.0, rot=90.0):
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + 180 * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def xf(pts, dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=1.0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(dx + (x * sx) * c - (y * sy) * s, dy + (x * sx) * s + (y * sy) * c) for x, y in pts]


def mirror(half):
    """A symmetric outline from its right half (top to bottom, x >= 0)."""
    return half + [(-x, y) for x, y in reversed(half)]


# ---------------------------------------------------------------- 3D
def prism(name, pts, depth, z=0.0, mat=None, bevel=1.0):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if a < 0:
        pts = list(reversed(pts))
    bm = bmesh.new()
    vb = [bm.verts.new((x * S, y * S, z * S)) for x, y in pts]
    vt = [bm.verts.new((x * S, y * S, (z + depth) * S)) for x, y in pts]
    bm.faces.new(vt)
    bm.faces.new(list(reversed(vb)))
    n = len(pts)
    for i in range(n):
        bm.faces.new([vb[i], vb[(i + 1) % n], vt[(i + 1) % n], vt[i]])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat is not None:
        o.data.materials.append(mat)
    o["bevel"] = bevel
    return o


def _bool(o, other, op):
    md = o.modifiers.new("Bo", "BOOLEAN")
    md.object = other
    md.operation = op
    md.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(other, do_unlink=True)


def unite(objs):
    base = objs[0]
    for o in objs[1:]:
        _bool(base, o, "UNION")
    return base


def cut(o, pts, depth=40.0):
    _bool(o, prism("cut", pts, depth, -depth / 2), "DIFFERENCE")
    return o


def stroke(name, pts, w, depth, z, mat, bevel=0.8, caps=True, closed=False):
    """A brass bar along a polyline (round joints), as one solid."""
    parts = []
    seq = pts + [pts[0]] if closed else pts
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
        parts.append(prism(name, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], depth, z))
    joints = seq if caps else seq[1:-1]
    for x, y in joints:
        parts.append(prism(name, circ(w / 2, x, y, n=20), depth, z))
    o = unite(parts)
    o.name = name
    o.data.materials.clear()
    o.data.materials.append(mat)
    o["bevel"] = bevel
    return o


def finish():
    """Bevel and smooth everything at the end (after the booleans)."""
    for o in bpy.data.objects:
        if o.type != "MESH" or "bevel" not in o.keys():
            continue
        b = float(o["bevel"])
        if b > 0:
            md = o.modifiers.new("B", "BEVEL")
            md.width = b * S
            md.segments = SEG
            md.limit_method = "ANGLE"
            md.profile = 0.6
            md.harden_normals = True
        for p in o.data.polygons:
            p.use_smooth = True


def arc_band(r_out, r_in, cx, cy, a0, a1, n=24):
    """A curved band (part of a ring) as one outline: no self-overlapping strokes."""
    return circ(r_out, cx, cy, n=n, a0=a0, a1=a1) + list(reversed(circ(r_in, cx, cy, n=n, a0=a0, a1=a1)))


def taper(fn, w0, w1, n=16):
    """A tapered strip along the curve fn(t) -> (x, y), t 0..1, width w0 -> w1 (offset along the true normal)."""
    L, R = [], []
    for i in range(n + 1):
        t = i / n
        x, y = fn(t)
        t2 = min(t + 1e-3, 1.0); t1 = max(t - 1e-3, 0.0)
        (ax, ay), (bx, by) = fn(t1), fn(t2)
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = (w0 + (w1 - w0) * t) / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    return L + list(reversed(R))


def gem(x, y, z, r):
    return sphere("Gem", x, y, z, r, RUBY(), flat=0.6)


def icon(name):
    def deco(fn):
        def build(w, h):
            fn()
            finish()
        piece(name, 64, 64, build)
        return fn
    return deco


# ================================================================ sections
@icon("SecInbox")
def _():
    prism("Env", rect(48, 34, 0, -2), 4, 0, BRASS(), 1.2)
    stroke("Flap", [(-21, 13), (0, -3), (21, 13)], 3.2, 2, 4, BRASS_POL())
    cyl("Seal", 0, -3, 4, 7.5, 2.4, CRIMSON(), bevel=1.0)
    gem(0, -3, 6.6, 2.6)


@icon("SecStudent")
def _():
    prism("Head", circ(10.5, 0, 10), 6, 0, BRASS_POL(), 1.4)
    sh = circ(21, 0, -26, n=40, a0=0, a1=180, ry=17)
    prism("Shoulders", sh, 5, 0, BRASS(), 1.4)
    prism("Collar", [(-6, -9), (6, -9), (0, -18)], 1.5, 5, CRIMSON(), 0.5)


@icon("SecServer")
def _():
    prism("Body", rect(30, 36, 0, -8), 5, 0, BRASS(), 1.0)
    for x in (-11.5, 0, 11.5):
        prism("Merlon", rect(7, 8, x, 14), 5, 0, BRASS(), 0.8)
    door = circ(6, 0, -14, n=16, a0=0, a1=180) + [(-6, -26), (6, -26)]
    prism("Door", door, 1.2, 5, IRON_DARK(), 0.4)
    prism("Win", rect(4, 7, 0, 2), 1.2, 5, IRON_DARK(), 0.3)
    gem(0, 2.5, 6.2, 1.6)


@icon("SecLog")
def _():
    prism("PageL", [(-27, -14), (-1.5, -19), (-1.5, 15), (-27, 19)], 3, 0, BRASS(), 0.8)
    prism("PageR", [(27, -14), (1.5, -19), (1.5, 15), (27, 19)], 3, 0, BRASS(), 0.8)
    for i in range(4):
        y = 10 - i * 7
        stroke("TL", [(-23, y + 2.2), (-6, y - 1)], 1.4, 0.8, 3, IRON_DARK(), 0.2)
        stroke("TR", [(6, y - 1), (23, y + 2.2)], 1.4, 0.8, 3, IRON_DARK(), 0.2)
    prism("Ribbon", [(-2.2, 15), (2.2, 15), (2.2, -24), (0, -21), (-2.2, -24)], 1.2, 3, CRIMSON(), 0.3)


@icon("SecCharacter")
def _():
    rim = prism("Rim", circ(16, 0, 8), 5, 0, BRASS(), 1.0)
    cut(rim, circ(11.5, 0, 8))
    cyl("Glass", 0, 8, 0.5, 11.6, 3.5, ENAMEL(), verts=48, bevel=0.6)
    stroke("Handle", [(0, -8), (0, -26)], 6, 4.5, 0, BRASS_POL(), 1.0)
    gem(0, -8, 4.5, 2.4)


@icon("SecProgress")
def _():
    for i, y in enumerate((-18, -7, 4)):
        stroke("Chev", [(-17, y - 6), (0, y + 6), (17, y - 6)], 5, 4, 0, BRASS_POL() if i == 2 else BRASS(), 0.9)
    prism("Star", star(5, 7.5, 3.2, 0, 20), 3.5, 0, BRASS_POL(), 0.8)
    gem(0, 20, 3.5, 1.8)


@icon("SecSchool")
def _():
    half = [(6, 16), (9, 12), (11, 3), (13.5, -6), (19, -13), (21, -16)]
    prism("Bell", mirror(half), 6, 0, BRASS(), 1.3)
    stroke("Handle", [(0, 15), (0, 23)], 5, 5, 0, BRASS_POL(), 0.8)
    cyl("Knob", 0, 25, 0, 4.2, 6, BRASS_POL(), bevel=1.2)
    stroke("Lip", [(-20, -15), (20, -15)], 3, 1.2, 6, BRASS_POL(), 0.4)
    gem(0, -21, 2, 3.4)


@icon("SecStory")
def _():
    prism("Sheet", rect(32, 34, 0, 0), 3, 0, BRASS(), 0.8)
    for y in (19, -19):
        o = rrect_mesh("Roll", 42, 8, 4, 5, 0.5, bevel=0)
        mat_of(o, BRASS_POL())
        o.location.y = y * S
        o["bevel"] = 1.2
    for i in range(4):
        stroke("Line", [(-11, 9 - i * 6), (11 - (i == 3) * 8, 9 - i * 6)], 1.4, 0.8, 3, IRON_DARK(), 0.2)
    cyl("Seal", 10, -10, 3, 4.5, 1.8, CRIMSON(), bevel=0.6)


@icon("SecWorld")
def _():
    cyl("Globe", 0, 0, 0, 21, 4, IRON_DARK(), verts=64, bevel=1.0)
    rim = prism("Rim", circ(23), 5.5, 0, BRASS(), 1.0)
    cut(rim, circ(19.5))
    m = prism("Meridian", circ(10, ry=20), 1.6, 4, BRASS_POL(), 0.4)
    cut(m, circ(7.6, ry=18.2))
    stroke("Equator", [(-20, 0), (20, 0)], 2.2, 1.6, 4, BRASS_POL(), 0.4)
    for y in (10, -10):
        stroke("Lat", [(-17.3, y), (17.3, y)], 1.4, 1.2, 4, BRASS(), 0.3)


@icon("SecSpawns")
def _():
    skull = unite([prism("Cran", circ(17, 0, 5), 6, 0), prism("Jaw", rect(18, 12, 0, -13), 6, 0)])
    mat_of(skull, BRASS())
    skull["bevel"] = 1.6
    for x in (-6.5, 6.5):
        cyl("Eye", x, 3, 6, 5, 1, IRON_DARK(), bevel=0.4)
        gem(x, 3, 7, 1.6)
    prism("Nose", [(-2.5, -5), (2.5, -5), (0, -1)], 1, 6, IRON_DARK(), 0.2)
    for x in (-4.5, 0, 4.5):
        stroke("Tooth", [(x, -11), (x, -17)], 1.3, 0.8, 6, IRON_DARK(), 0.2)


@icon("SecSelf")
def _():
    # a spread wing: six primaries fanning from one brass root, each with a dark quill line
    for i, (ang, L) in enumerate(((10, 47), (25, 46), (40, 43), (55, 38), (70, 32), (85, 25))):
        feather = xf([(0, -4.4), (L - 8, -4.2), (L, 0), (L - 8, 4.2), (0, 4.4)], -22, -20, ang)
        z = i * 0.4
        prism("Feather", feather, 3.6, z, BRASS() if i % 2 else BRASS_POL(), 1.0)
        stroke("Quill", xf([(6, 0), (L - 9, 0)], -22, -20, ang), 1.0, 0.5, z + 3.6, IRON_DARK(), 0.2)
    cyl("Root", -22, -20, 0, 6.5, 6.5, BRASS_POL(), bevel=1.2)
    gem(-22, -20, 6.5, 2.8)


# ================================================================ Moderate cards
@icon("Warn")
def _():
    tri = circ(26, 0, -3, n=3, a0=90, a1=450)
    o = prism("Tri", tri, 5, 0, BRASS(), 1.6)
    cut(o, circ(16, 0, -3, n=3, a0=90, a1=450))
    prism("Field", circ(16.5, 0, -3, n=3, a0=90, a1=450), 3, 0.5, CRIMSON(), 0.6)
    stroke("Bang", [(0, 5), (0, -6)], 4, 2, 3.5, BRASS_POL(), 0.6)
    cyl("Dot", 0, -11.5, 3.5, 2.4, 2, BRASS_POL(), bevel=0.6)


@icon("Mute")
def _():
    o = unite([prism("Bub", rect(42, 28, 0, 4), 5, 0), prism("Tail", [(-12, -9), (-2, -9), (-16, -20)], 5, 0)])
    mat_of(o, BRASS())
    o["bevel"] = 1.4
    for x in (-10, 0, 10):
        cyl("Dot", x, 4, 5, 2.6, 1, IRON_DARK(), bevel=0.4)
    stroke("Slash", [(-22, -18), (22, 22)], 5, 2.5, 5.5, CRIMSON(), 0.8)


@icon("Freeze")
def _():
    for a in (90, 30, 150):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        stroke("Arm", [(-25 * c, -25 * s), (25 * c, 25 * s)], 4, 4, 0, BRASS_POL(), 0.8)
        for sg in (1, -1):
            bx, by = sg * 16 * c, sg * 16 * s
            for side in (1, -1):
                aa = math.radians(a + side * 40)
                stroke("Twig", [(bx, by), (bx + sg * 8 * math.cos(aa), by + sg * 8 * math.sin(aa))], 3, 3, 0.5, BRASS(), 0.6)
    cyl("Core", 0, 0, 0, 5.5, 5, ENAMEL(), bevel=0.8)
    gem(0, 0, 5, 2.2)


@icon("Jail")
def _():
    f = prism("Frame", rect(42, 46), 5, 0, BRASS(), 1.2)
    cut(f, rect(32, 36))
    prism("Back", rect(33, 37), 1, 0, IRON_DARK(), 0.3)
    for x in (-10.5, -3.5, 3.5, 10.5):
        stroke("Bar", [(x, -18), (x, 18)], 3.4, 4.5, 0.5, IRON(), 0.7)
    stroke("Cross", [(-16, 0), (16, 0)], 3.4, 3, 2.5, BRASS_POL(), 0.6)
    for x in (-15, 15):
        for y in (-17, 17):
            sphere("Rv", x, y, 5, 2, BRASS_POL())


@icon("Spectate")
def _():
    upper = circ(30, 0, -14, n=24, a0=152, a1=28)
    lower = circ(30, 0, 14, n=24, a0=-28, a1=-152)
    prism("Eye", upper + lower, 4, 0, BRASS(), 1.2)
    prism("White", xf(upper + lower, sx=0.82, sy=0.7), 1, 4, IRON_DARK(), 0.4)
    cyl("Iris", 0, 0, 4, 9, 2, CRIMSON(), verts=48, bevel=0.6)
    cyl("Pupil", 0, 0, 6, 4, 1, ENAMEL(), bevel=0.4)
    sphere("Glint", 3, 3, 7, 1.6, BRASS_POL())


@icon("Bring")
def _():
    for a in (45, 135, 225, 315):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        stroke("Shaft", [(26 * c, 26 * s), (15 * c, 15 * s)], 3.6, 3.5, 0, BRASS(), 0.6)
        tip = [(9.5 * c, 9.5 * s), (16 * c - 5.5 * s, 16 * s + 5.5 * c), (16 * c + 5.5 * s, 16 * s - 5.5 * c)]
        prism("Head", tip, 4, 0, BRASS_POL(), 0.6)
    cyl("Core", 0, 0, 0, 5, 5, BRASS_POL(), bevel=1)
    gem(0, 0, 5, 2.4)


@icon("GoTo")
def _():
    r = prism("Ring", circ(24), 3.5, 0, BRASS(), 1.0)
    cut(r, circ(20))
    needle = [(0, 25), (6.5, 0), (0, -25), (-6.5, 0)]
    n = prism("Needle", xf(needle, rot=-35), 5, 0, BRASS_POL(), 0.8)
    prism("South", xf([(6.5, 0), (0, -25), (-6.5, 0)], rot=-35), 1.2, 5, IRON_DARK(), 0.3)
    gem(0, 0, 5.5, 2.4)


@icon("Kick")
def _():
    boot = [(-12, 24), (2, 24), (3, 2), (8, -2), (20, -6), (25, -12), (25, -20), (-13, -20), (-14, -8)]
    prism("Boot", boot, 5.5, 0, BRASS(), 1.4)
    prism("Sole", [(-13, -20), (25, -20), (25, -16), (-13, -16)], 2, 5.5, IRON_DARK(), 0.4)
    prism("Cuff", rect(15, 5, -5, 21), 1.6, 5.5, CRIMSON(), 0.4)
    for y in (12, 6, 0):
        sphere("Lace", 0, y, 5.8, 1.4, BRASS_POL())


@icon("Ban")
def _():
    stroke("Handle", [(-20, -20), (4, 4)], 5, 4, 0, BRASS(), 1.0)
    head = rrect_mesh("Head", 34, 15, 4, 7, 0, bevel=0)
    mat_of(head, BRASS_POL())
    head.location = (8 * S, 8 * S, 0)
    head.rotation_euler.z = math.radians(-45)
    head["bevel"] = 1.4
    for k in (-1, 1):
        band = rrect_mesh("Band", 3.5, 16, 1, 7.4, -0.2, bevel=0)
        mat_of(band, CRIMSON())
        band.location = ((8 + k * 5.5) * S, (8 - k * 5.5) * S, 0)
        band.rotation_euler.z = math.radians(-45)
        band["bevel"] = 0.5
    prism("Block", rect(22, 6, -10, -24), 3, 0, IRON(), 0.8)


@icon("Note")
def _():
    vane = [(0, 28), (7, 19), (8.5, 4), (5, -10), (0, -16), (-5, -8), (-7.5, 6), (-6, 19)]
    prism("Vane", xf(vane, rot=-35, dx=4, dy=3), 4.5, 0, BRASS(), 1.0)
    for k in range(5):
        y = 20 - k * 7
        stroke("Barb", xf([(0, y - 4), (6, y + 1)], rot=-35, dx=4, dy=3), 1.1, 0.6, 4.5, IRON_DARK(), 0.2)
    stroke("Shaft", xf([(0, 24), (0, -16)], rot=-35, dx=4, dy=3), 2, 1, 4.5, BRASS_POL(), 0.3)
    prism("Nib", xf([(-2.4, -16), (2.4, -16), (0, -29)], rot=-35, dx=4, dy=3), 4.5, 0, IRON_DARK(), 0.4)
    sphere("Ink", -19, -21, 1, 4.6, CRIMSON(), flat=0.4)


@icon("Announce")
def _():
    horn = [(-20, 4), (6, 12), (14, 20), (14, -20), (6, -12), (-20, -4)]
    prism("Horn", horn, 5, 0, BRASS(), 1.2)
    bell = prism("Bell", circ(5, 14, 0, ry=20), 6, 0, BRASS_POL(), 1.0)
    cyl("Mouth", -22, 0, 0, 4, 5, IRON(), bevel=0.8)
    for r in (8, 14):
        stroke("Wave", circ(r, 16, 0, n=10, a0=-40, a1=40), 2.2, 2.5, 0, BRASS_POL(), 0.4)


@icon("Lock")
def _():
    sh = stroke("Shackle", circ(11, 0, 4, n=18, a0=0, a1=180) + [(-11, -2)], 4.4, 4, 0, IRON(), 0.8)
    stroke("ShackleR", [(11, 4), (11, -2)], 4.4, 4, 0, IRON(), 0.8)
    o = rrect_mesh("Body", 36, 28, 4, 6, 0, bevel=0)
    mat_of(o, BRASS())
    o.location.y = -10 * S
    o["bevel"] = 1.4
    cyl("Hole", 0, -7, 6, 3.4, 1, ENAMEL(), bevel=0.3)
    prism("Slot", [(-1.6, -8), (1.6, -8), (2.4, -17), (-2.4, -17)], 1, 6, ENAMEL(), 0.3)
    for x in (-14, 14):
        sphere("Rv", x, -10, 6, 1.6, BRASS_POL())


@icon("Shutdown")
def _():
    cyl("Disc", 0, 0, 0, 25, 4, CRIMSON(), verts=64, bevel=1.2)
    rim = prism("Rim", circ(26), 5, 0, BRASS(), 1.0)
    cut(rim, circ(23))
    stroke("Arc", circ(13, n=22, a0=125, a1=415), 4, 2, 4, BRASS_POL(), 0.6)
    stroke("Bar", [(0, 17), (0, 2)], 4, 2.4, 4, BRASS_POL(), 0.6)


@icon("Health")
def _():
    o = rrect_mesh("Frame", 50, 38, 6, 5, 0, bevel=0)
    mat_of(o, BRASS())
    o["bevel"] = 1.2
    s = rrect_mesh("Screen", 42, 30, 4, 1, 5, bevel=0)
    mat_of(s, ENAMEL())
    s["bevel"] = 0.4
    pts = [(-19, -2), (-9, -2), (-5, 9), (0, -11), (4, 4), (7, -2), (19, -2)]
    stroke("Pulse", pts, 2.6, 1, 6, CRIMSON(), 0.4)
    gem(7, -2, 6.6, 1.6)


@icon("Resolve")
def _():
    r = prism("Ring", circ(25), 4.5, 0, BRASS(), 1.0)
    cut(r, circ(20.5))
    cyl("Field", 0, 0, 0, 20.6, 2.5, IRON_DARK(), verts=48, bevel=0.5)
    stroke("Check", [(-11, 1), (-3, -8), (13, 10)], 5, 3, 2.5, BRASS_POL(), 0.8)


@icon("Dismiss")
def _():
    r = prism("Ring", circ(25), 4.5, 0, BRASS(), 1.0)
    cut(r, circ(20.5))
    cyl("Field", 0, 0, 0, 20.6, 2.5, IRON_DARK(), verts=48, bevel=0.5)
    stroke("X1", [(-10, -10), (10, 10)], 5, 3, 2.5, CRIMSON(), 0.8)
    stroke("X2", [(-10, 10), (10, -10)], 5, 3, 2.5, CRIMSON(), 0.8)


# ================================================================ Test cards
@icon("Heal")
def _():
    f = unite([prism("Flask", circ(15, 0, -9), 5, 0), prism("Neck", rect(9, 14, 0, 9), 5, 0)])
    mat_of(f, BRASS())
    f["bevel"] = 1.0
    cut(f, circ(11.5, 0, -9))
    cyl("Glass", 0, -9, 0.4, 11.6, 3.4, ENAMEL(), verts=48, bevel=0.5)
    liquid = circ(11.6, 0, -9, n=24, a0=200, a1=340)
    prism("Liquid", liquid, 1.2, 3.8, CRIMSON(), 0.3)
    prism("Cork", rect(8, 6, 0, 18), 4, 1, LEATHER(), 0.8)
    gem(-4, -4, 4.4, 1.4)


@icon("Revive")
def _():
    loop = prism("Loop", circ(8.5, 0, 13, ry=11), 5, 0, BRASS_POL(), 1.0)
    cut(loop, circ(4.5, 0, 13, ry=6.5))
    stroke("Bar", [(-17, 1), (17, 1)], 5.5, 5, 0, BRASS_POL(), 1.0)
    stroke("Stem", [(0, 1), (0, -26)], 6, 5, 0, BRASS_POL(), 1.0)
    gem(0, 1, 5, 2.6)


@icon("God")
def _():
    h = prism("Halo", circ(23, 0, 4, ry=11), 5, 0, BRASS_POL(), 1.2)
    cut(h, circ(17, 0, 4, ry=7))
    for a in range(0, 360, 30):
        if 200 < a < 340:
            continue
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        prism("Ray", [(c * 26 - s * 1.8, 4 + s * 15 - c * 1.8), (c * 26 + s * 1.8, 4 + s * 15 + c * 1.8), (c * 31, 4 + s * 19)], 2.5, 0, BRASS(), 0.4)
    prism("Star", star(4, 8, 2.4, 0, -14, rot=90), 4, 0, BRASS_POL(), 0.6)
    gem(0, -14, 4, 1.8)


@icon("Kill")
def _():
    blade = [(0, 27), (5, 10), (4.5, -3), (-4.5, -3), (-5, 10)]
    prism("Blade", xf(blade, rot=-35, dx=4, dy=4, sx=1.25, sy=1.12), 3.5, 0, IRON(), 0.9)
    stroke("Fuller", xf([(0, 20), (0, 0)], rot=-35, dx=4, dy=4), 1.2, 0.6, 3.5, IRON_DARK(), 0.2)
    stroke("Guard", xf([(-11, -4), (11, -4)], rot=-35, dx=4, dy=4), 4, 5, 0, BRASS_POL(), 0.8)
    stroke("Grip", xf([(0, -6), (0, -18)], rot=-35, dx=4, dy=4), 4.4, 4.5, 0, LEATHER(), 0.6)
    px, py = xf([(0, -21)], rot=-35, dx=4, dy=4)[0]
    cyl("Pommel", px, py, 0, 4, 5, BRASS_POL(), bevel=1)
    gem(px, py, 5, 2)


@icon("Speed")
def _():
    bolt = [(6, 27), (-14, -2), (-2, -2), (-8, -27), (15, 6), (3, 6)]
    prism("Bolt", bolt, 5.5, 0, BRASS_POL(), 1.2)
    prism("Core", xf(bolt, sx=0.55, sy=0.6), 1, 5.5, CRIMSON(), 0.3)


@icon("Race")
def _():
    half = [(0, 7), (4, 10), (7, 17), (9, 9), (15, 14), (28, 13), (24, 4), (27, -6), (19, -3), (14, -11), (7, -6), (3, -14), (0, -10)]
    prism("Bat", xf(mirror(half), sx=1.05, sy=1.25), 5.5, 0, BRASS(), 1.0)
    prism("Body", circ(5, 0, 0, ry=9), 6.5, 0, BRASS_POL(), 1.0)
    for x in (-2.2, 2.2):
        gem(x, 4, 6.5, 1.4)
    for x in (9, -9):
        stroke("Bone", [(x * 0.35, 5), (x * 2.3, -5)], 1.4, 0.8, 5.5, IRON_DARK(), 0.2)
        stroke("Bone", [(x * 0.35, 5), (x * 1.5, -10)], 1.4, 0.8, 5.5, IRON_DARK(), 0.2)


@icon("Height")
def _():
    o = rrect_mesh("Rule", 13, 52, 3, 5, 0, bevel=0)
    mat_of(o, BRASS())
    o.location.x = -8 * S
    o["bevel"] = 1.0
    for i in range(9):
        y = -22 + i * 5.5
        L = 7 if i % 2 == 0 else 4
        stroke("Tick", [(-14.5 + 0, y), (-14.5 + L, y)], 1.2, 0.8, 5, IRON_DARK(), 0.2)
    stroke("Arrow", [(12, -18), (12, 18)], 3.6, 4, 0, BRASS_POL(), 0.6)
    for sg in (1, -1):
        prism("Tip", [(12, sg * 27), (5, sg * 17), (19, sg * 17)], 4.5, 0, BRASS_POL(), 0.6)


@icon("Transform")
def _():
    cyl("Disc", 0, 0, 0, 23, 3.5, IRON_DARK(), verts=64, bevel=0.8)
    rim = prism("Rim", circ(25), 5, 0, BRASS(), 1.0)
    cut(rim, circ(21.5))
    for dx in (-8, 0, 8):
        pts = [(dx - 6 + 2.5 * t, 16 - 32 * t + 4 * math.sin(math.pi * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        # tapered slash: a strip wider in the middle
        left = [(x - (0.6 + 2.2 * math.sin(math.pi * i / 4)), y) for i, (x, y) in enumerate(pts)]
        right = [(x + (0.6 + 2.2 * math.sin(math.pi * i / 4)), y) for i, (x, y) in enumerate(pts)]
        prism("Slash", left + list(reversed(right)), 1.6, 3.5, CRIMSON(), 0.4)


@icon("Yen")
def _():
    cyl("Coin", 0, 0, 0, 23, 5, BRASS_POL(), verts=64, bevel=1.4)
    rim = prism("Rim", circ(23), 6, 0, BRASS(), 0.8)
    cut(rim, circ(19.5))
    stroke("Y", [(-9, 13), (0, 2), (9, 13)], 3.4, 1, 5, ENAMEL(), 0.3)
    stroke("Stem", [(0, 2), (0, -14)], 3.4, 1, 5, ENAMEL(), 0.3)
    for y in (-2, -7):
        stroke("Bar", [(-8, y), (8, y)], 2.6, 1, 5, ENAMEL(), 0.3)


@icon("Exp")
def _():
    prism("Star", star(5, 27, 11), 5, 0, BRASS_POL(), 1.4)
    prism("Inner", star(5, 15, 6.2), 1.5, 5, CRIMSON(), 0.4)
    gem(0, 0, 6.5, 3)


@icon("Gear")
def _():
    sh = [(-21, 22), (21, 22), (21, 2), (14, -14), (0, -26), (-14, -14), (-21, 2)]
    prism("Shield", sh, 5, 0, BRASS(), 1.4)
    prism("Field", xf(sh, sx=0.78, sy=0.78, dy=0.5), 1.2, 5, CRIMSON(), 0.4)
    stroke("Cross1", [(0, 16), (0, -18)], 3.2, 1.2, 6.2, BRASS_POL(), 0.4)
    stroke("Cross2", [(-14, 6), (14, 6)], 3.2, 1.2, 6.2, BRASS_POL(), 0.4)
    cyl("Boss", 0, 6, 6.2, 4.5, 2, IRON(), bevel=0.8)


@icon("Time")
def _():
    cyl("Face", 0, 0, 0, 22, 3, ENAMEL(), verts=64, bevel=0.6)
    rim = prism("Rim", circ(25), 5.5, 0, BRASS(), 1.2)
    cut(rim, circ(21))
    for a in range(0, 360, 30):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        if a % 90 == 0:
            stroke("Tick", [(c * 15, s * 15), (c * 19, s * 19)], 2.4, 1, 3, BRASS_POL(), 0.3)
        else:
            sphere("Dot", c * 17.5, s * 17.5, 3, 1, BRASS())
    stroke("Hour", [(0, 0), (6, 8)], 3, 1.2, 3.2, BRASS_POL(), 0.3)
    stroke("Min", [(0, 0), (-3, 15)], 2.2, 1.2, 4.2, BRASS_POL(), 0.3)
    gem(0, 0, 5.4, 2)


@icon("Season")
def _():
    leaf = []
    for i in range(25):
        t = i / 24
        y = 27 - 50 * t
        w = 15 * math.sin(math.pi * t) ** 0.8 * (1 + 0.18 * math.sin(t * math.pi * 10))
        leaf.append((w, y))
    prism("Leaf", mirror(leaf), 4, 0, CRIMSON(), 1.0)
    stroke("Rib", [(0, 25), (0, -26)], 2, 1, 4, BRASS_POL(), 0.3)
    for y in (12, 2, -8):
        stroke("Vein", [(0, y - 5), (8, y + 3)], 1.4, 0.8, 4, BRASS(), 0.2)
        stroke("Vein", [(0, y - 5), (-8, y + 3)], 1.4, 0.8, 4, BRASS(), 0.2)
    stroke("Stem", [(0, -23), (-3, -28)], 2.4, 3, 0, BRASS_POL(), 0.4)


@icon("Moon")
def _():
    m = prism("Moon", circ(23, -2, 0), 5.5, 0, BRASS_POL(), 1.4)
    cut(m, circ(19, 8, 5))
    prism("Star", star(4, 8, 2.2, 14, -13), 3.5, 0, BRASS(), 0.5)
    gem(14, -13, 3.5, 1.4)


@icon("Cutscene")
def _():
    o = rrect_mesh("Body", 46, 30, 3, 5, 0, bevel=0)
    mat_of(o, BRASS())
    o.location.y = -9 * S
    o["bevel"] = 1.2
    top = prism("Top", rect(46, 8, 0, 14, rot=12), 5, 0.5, IRON(), 0.8)
    for i in range(4):
        prism("Stripe", xf([(-3, -4), (3, -4), (7, 4), (1, 4)], dx=-15 + i * 10, dy=14, rot=12), 1, 5.5, BRASS_POL(), 0.2)
    for i in range(3):
        stroke("Line", [(-17, -4 - i * 7), (17 - (i == 2) * 12, -4 - i * 7)], 1.6, 0.8, 5, IRON_DARK(), 0.2)
    cyl("Hinge", -21, 8, 5, 2.6, 2, BRASS_POL(), bevel=0.6)


@icon("Tutorial")
def _():
    stroke("Post", [(0, 25), (0, -27)], 4.5, 5, 0, IRON(), 0.8)
    prism("Arm1", [(-14, 18), (16, 18), (23, 12), (16, 6), (-14, 6)], 4, 4, BRASS_POL(), 1.0)
    prism("Arm2", [(14, 0), (-16, 0), (-23, -6), (-16, -12), (14, -12)], 4, 4, BRASS(), 1.0)
    prism("Base", rect(18, 5, 0, -26), 3, 0, BRASS(), 0.6)
    gem(0, 25, 5, 2)


@icon("Clues")
def _():
    r = prism("Ring", circ(14, -5, 5), 5.5, 0, BRASS(), 1.2)
    cut(r, circ(10.5, -5, 5))
    cyl("Lens", -5, 5, 0.4, 10.6, 3.4, ENAMEL(), verts=48, bevel=0.6)
    sphere("Glint", -9, 9, 4, 2.4, BRASS_POL(), flat=0.3)
    stroke("Handle", [(5, -5), (21, -21)], 6, 5, 0, LEATHER(), 1.0)
    stroke("Collar", [(4, -4), (8, -8)], 6.6, 5.5, 0, BRASS_POL(), 0.6)


@icon("Wolf")
def _():
    pad = [(0, -2), (9, -6), (13, -14), (9, -22), (0, -20), (-9, -22), (-13, -14), (-9, -6)]
    prism("Pad", pad, 5, 0, BRASS(), 1.4)
    for x, y, r in ((-17, 2, 5.5), (-6.5, 12, 6), (6.5, 12, 6), (17, 2, 5.5)):
        prism("Toe", circ(r * 0.85, x, y, ry=r), 5, 0, BRASS_POL(), 1.2)
    for x, y in ((-17, 9), (-6.5, 20), (6.5, 20), (17, 9)):
        prism("Claw", [(x - 1.6, y), (x + 1.6, y), (x, y + 5)], 3, 0.5, IRON_DARK(), 0.3)


@icon("Beast")
def _():
    # two horns sweeping out and up from a brow, ruby eyes
    for sg in (1, -1):
        fn = lambda t, sg=sg: (sg * (9 + 15 * math.sin(t * 1.9) ), -2 + 30 * t - 6 * t * t)
        prism("Horn", taper(fn, 9, 1.2, n=20), 5.5, 0, BRASS_POL(), 1.0)
        for k in (0.25, 0.45, 0.65):
            x, y = fn(k)
            stroke("Ridge", [(x - 2.2, y - 1), (x + 2.2, y + 1)], 1, 0.6, 5.5, IRON_DARK(), 0.2)
    prism("Brow", [(-14, 2), (14, 2), (10, -12), (0, -21), (-10, -12)], 5, 0, BRASS(), 1.2)
    for x in (-4.8, 4.8):
        cyl("Socket", x, -6, 5, 3.2, 0.8, IRON_DARK(), bevel=0.3)
        gem(x, -6, 5.8, 2)


@icon("Teleport")
def _():
    for i, (rx, ry) in enumerate(((25, 12), (19, 9), (13, 6))):
        r = prism("Ring", circ(rx, 0, -6 + i * 4, ry=ry), 3 + i, 0, BRASS_POL() if i % 2 == 0 else BRASS(), 0.8)
        cut(r, circ(rx - 3.2, 0, -6 + i * 4, ry=ry - 2.6))
    for a in (60, 120):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        stroke("Spark", [(c * 10, 10 + s * 6), (c * 15, 10 + s * 13)], 2, 3, 0, BRASS_POL(), 0.4)
    gem(0, 6, 5, 3)


@icon("Invisible")
def _():
    top = circ(17, 0, 4, n=24, a0=0, a1=180)
    wave = [(-17, -18), (-11, -24), (-6, -18), (0, -24), (6, -18), (11, -24), (17, -18)]
    prism("Ghost", top + wave, 5, 0, BRASS(), 1.4)
    for x in (-6, 6):
        prism("Eye", circ(2.8, x, 4, ry=4), 1, 5, ENAMEL(), 0.3)
    prism("Mouth", circ(3, 0, -6, ry=4), 1, 5, ENAMEL(), 0.3)
    for i, y in enumerate((14, 2, -10)):
        stroke("Fade", [(21, y), (26, y)], 2, 2, 0, BRASS_POL(), 0.3)


@icon("Discipline")
def _():
    # the master's cane: a straight shaft and a crook (one curved band), with a crimson binding
    stroke("Shaft", [(10, -26), (10, 10)], 5, 5, 0, BRASS(), 1.0)
    prism("Crook", arc_band(11, 6, 2.5, 10, 0, 180, n=24), 5, 0, BRASS(), 1.0)
    prism("Tip", circ(2.5, -6, 10), 5, 0, BRASS(), 0.8)
    stroke("Band", [(10, -4), (10, -11)], 6.4, 5.6, 0, CRIMSON(), 0.5)
    cyl("Ferrule", 10, -26, 0, 3.4, 5.6, IRON(), bevel=0.8)
    for i in range(3):
        stroke("Stroke", [(-20, -20 + i * 8), (-6, -16 + i * 8)], 2.4, 2, 0, CRIMSON(), 0.4)


print("ICONS DONE")
