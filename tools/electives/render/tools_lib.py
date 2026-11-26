"""The five Anatomy bench tools, modelled properly (lathed, swept, knurled). Units: metres.

Each build_<tool>(M, loc, rot) returns its root empty. Tools are built lying along +Y (business end at +Y).
M must hold: brass, brass_dark, steel, steel_dark, rosewood, ebony, glass, leather_dk.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Vector

col = bpy.context.scene.collection


def _obj(name, bm, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    if smooth:
        o.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True
    return o


def lathe(name, prof, mat, seg=96, rfun=None):
    """Solid of revolution about +Y. prof: [(r, y)] from one end to the other. rfun(theta, y, r) -> r."""
    bm = bmesh.new()
    rings = []
    for r, y in prof:
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            rr = rfun(t, y, r) if rfun else r
            ring.append(bm.verts.new((math.cos(t) * rr, y, math.sin(t) * rr)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        if ring[0].co.length > 1e-6 or True:
            c = bm.verts.new((0, ring[0].co.y, 0))
            for k in range(seg):
                f = (c, ring[(k + 1) % seg], ring[k]) if rev else (c, ring[k], ring[(k + 1) % seg])
                bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mat)


def sweep(name, sections, mat, smooth=True):
    """Loft through cross-sections: each a list of (x, y, z) points, same count, closed loop."""
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in s] for s in sections]
    n = len(sections[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mat, smooth)


def rrect(cx, y, cz, w, h, r, n=4):
    """A rounded-rectangle cross-section in the XZ plane at height y."""
    pts = []
    r = min(r, w / 2 - 1e-5, h / 2 - 1e-5)
    for qx, qz, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oz = cx + qx * (w / 2 - r), cz + qz * (h / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((ox + math.cos(a) * r, y, oz + math.sin(a) * r))
    return pts


def torus(name, R, r, mat, loc=(0, 0, 0), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=96, minor_segments=24,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


SCALE = 1.6   # stylised: chunkier than life so they read in the bench view


def root(name, loc, rot, parts):
    e = bpy.data.objects.new(name, None)
    e.scale = (SCALE, SCALE, SCALE)
    col.objects.link(e)
    for p in parts:
        p.parent = e
    e.location = loc
    e.rotation_euler = Euler(rot)
    return e


def knurl(depth, count, y0, y1):
    """A diamond knurl between y0 and y1 (rfun)."""
    def f(t, y, r):
        if y0 <= y <= y1:
            return r * (1 - depth * (0.5 + 0.5 * math.cos(count * t + y * 900)) * (0.5 + 0.5 * math.cos(count * t - y * 900)))
        return r
    return f


# ------------------------------------------------------------------ screwdriver (≈ 150 mm)
def build_screwdriver(M, loc, rot):
    def flutes(t, y, r):
        if 0.008 < y < 0.07:
            k = math.sin(math.pi * (y - 0.008) / 0.062) ** 0.4
            return r * (1 - 0.14 * k * max(0.0, math.cos(8 * t)) ** 2)
        return r
    handle = lathe("SD_Handle", [(0.0, 0.0), (0.008, 0.0), (0.0115, 0.002), (0.0128, 0.008), (0.0132, 0.02), (0.0128, 0.045),
                                 (0.0122, 0.06), (0.0128, 0.068), (0.0118, 0.074), (0.009, 0.078)], M["rosewood"], seg=160, rfun=flutes)
    ferrule = lathe("SD_Ferrule", [(0.0, 0.0775), (0.0092, 0.0775), (0.0094, 0.08), (0.0088, 0.09), (0.0075, 0.094), (0.0042, 0.097), (0.0, 0.097)],
                    M["brass"], rfun=knurl(0.06, 40, 0.081, 0.089))
    shank = lathe("SD_Shank", [(0.0, 0.096), (0.0032, 0.096), (0.0032, 0.142), (0.0, 0.142)], M["steel"], seg=48)
    secs = []
    for i in range(9):
        u = i / 8
        y = 0.141 + u * 0.012
        w = 0.0064 - 0.0012 * u
        h = 0.0064 * (1 - u) + 0.0008 * u
        secs.append(rrect(0, y, 0, w, h, 0.0004 + 0.0028 * (1 - u)))
    blade = sweep("SD_Blade", secs, M["steel"])
    return root("Screwdriver", loc, rot, [handle, ferrule, shank, blade])


# ------------------------------------------------------------------ tweezers (≈ 120 mm), open `gap` metres at the tips
def build_tweezers(M, loc, rot, gap=0.012):
    parts = []
    for side in (-1, 1):
        secs = []
        N = 40
        for i in range(N + 1):
            u = i / N
            y = u * 0.12
            spread = (gap / 2 + 0.0012) * (u ** 1.3) if u > 0.08 else 0.0012 * u / 0.08
            x = side * (0.0012 + spread)
            w = 0.0082 * (1 - u) ** 0.7 + 0.0009 * u          # tapers to a fine tip
            th = 0.0013
            z = 0.0
            if u > 0.93:                                       # the bent tip
                z = -((u - 0.93) / 0.07) ** 2 * 0.004
            secs.append(rrect(x + side * th * 0, y, z, th, w, 0.0003))
        # rotate cross-sections so the arm's width runs vertically (arms face each other)
        arm = sweep(f"TW_Arm{side}", [[(p[0], p[1], p[2]) for p in s] for s in secs], M["steel"])
        parts.append(arm)
        # knurled grip pad
        pad_secs = [rrect(side * (0.0012 + (gap / 2 + 0.0012) * (u ** 1.3) + 0.0009), u * 0.12, 0, 0.0007, 0.0078 * (1 - u) ** 0.7, 0.0002)
                    for u in [0.42 + 0.02 * j for j in range(11)]]
        parts.append(sweep(f"TW_Pad{side}", pad_secs, M["steel_dark"]))
    # heel block and rivet
    heel = sweep("TW_Heel", [rrect(0, y, 0, 0.0052, 0.0086, 0.0012) for y in (-0.004, 0.0, 0.006, 0.0085)], M["steel"])
    rivet = lathe("TW_Rivet", [(0, -0.0035), (0.0016, -0.0035), (0.0019, -0.0028), (0.0019, 0.0028), (0.0016, 0.0035), (0, 0.0035)], M["brass"], seg=32)
    rivet.rotation_euler = (0, 0, math.radians(90))
    rivet.location = (0, 0.003, 0)
    parts += [heel, rivet]
    return root("Tweezers", loc, rot, parts)


# ------------------------------------------------------------------ loupe / magnifier (lens Ø 46 mm, ≈ 130 mm long)
def build_loupe(M, loc, rot):
    R = 0.023
    cy = 0.095
    bezel = lathe("LP_Bezel", [(R - 0.002, -0.0045), (R + 0.0035, -0.0045), (R + 0.0042, -0.003), (R + 0.0042, 0.003),
                               (R + 0.0035, 0.0045), (R - 0.002, 0.0045), (R - 0.0015, 0.0)], M["brass"], seg=128,
                  rfun=lambda t, y, r: r * (1 - 0.012 * (0.5 + 0.5 * math.cos(110 * t))) if abs(y) < 0.0031 and r > R else r)
    bezel.rotation_euler = (math.radians(90), 0, 0)
    bezel.location = (0, cy, 0)
    prof = [(0.0, -0.0042)]
    for i in range(1, 13):
        r = (R - 0.0005) * i / 12
        prof.append((r, -0.0042 * (1 - (r / R) ** 2) - 0.0006))
    for i in range(12, -1, -1):
        r = (R - 0.0005) * i / 12
        prof.append((r if i else 0.0, 0.0042 * (1 - (r / R) ** 2) + 0.0006))
    lens = lathe("LP_Lens", prof, M["glass"], seg=96)
    lens.rotation_euler = (math.radians(90), 0, 0)
    lens.location = (0, cy, 0)
    yoke = sweep("LP_Yoke", [rrect(0, y, 0, 0.0075 - (y - 0.06) * 0.05, 0.004, 0.0012) for y in (0.058, 0.064, 0.07, 0.0715)], M["brass"])
    ferrule = lathe("LP_Ferrule", [(0, 0.05), (0.0058, 0.05), (0.0062, 0.052), (0.0062, 0.058), (0.0045, 0.06), (0, 0.06)], M["brass"],
                    rfun=knurl(0.07, 32, 0.052, 0.057))
    handle = lathe("LP_Handle", [(0, 0.0), (0.004, 0.0), (0.0062, 0.003), (0.0068, 0.012), (0.0058, 0.026), (0.0066, 0.038),
                                 (0.0062, 0.046), (0.0056, 0.05)], M["ebony"])
    return root("Loupe", loc, rot, [bezel, lens, yoke, ferrule, handle])


# ------------------------------------------------------------------ clock-winding key (≈ 75 mm)
def build_pinkey(M, loc, rot):
    parts = []
    # an ornate trefoil bow, lying in the XY plane
    parts.append(torus("PK_Bow", 0.012, 0.0024, M["brass"], loc=(0, 0.0, 0)))
    for a in (150, 30):
        x, y = math.cos(math.radians(a)) * 0.017, math.sin(math.radians(a)) * 0.017 - 0.006
        parts.append(torus("PK_Lobe", 0.0055, 0.0018, M["brass"], loc=(x, -y - 0.004, 0)))
    parts.append(torus("PK_Lobe", 0.0055, 0.0018, M["brass"], loc=(0, -0.019, 0)))
    parts.append(lathe("PK_Jewel", [(0, -0.002), (0.0035, -0.002), (0.004, 0), (0.0035, 0.002), (0, 0.002)], M["brass_dark"], seg=32))
    parts[-1].rotation_euler = (math.radians(90), 0, 0)
    stem = lathe("PK_Stem", [(0, 0.011), (0.0042, 0.011), (0.0055, 0.014), (0.0055, 0.018), (0.003, 0.021), (0.0026, 0.045),
                             (0.0042, 0.047), (0.0042, 0.05), (0.0034, 0.052), (0.0034, 0.066), (0.0041, 0.068), (0.0041, 0.072), (0, 0.072)],
                 M["brass"], rfun=knurl(0.05, 24, 0.0145, 0.0175))
    sock = sweep("PK_Socket", [rrect(0, y, 0, 0.0024, 0.0024, 0.0002) for y in (0.0705, 0.0725)], M["steel_dark"], smooth=False)
    parts += [stem, sock]
    return root("PinKey", loc, rot, parts)


# ------------------------------------------------------------------ scalpel (≈ 140 mm)
def build_scalpel(M, loc, rot):
    hsecs = []
    for i in range(13):
        u = i / 12
        y = u * 0.1
        w = 0.0085 - 0.0022 * abs(u - 0.45) * 2
        hsecs.append(rrect(0, y, 0, w, 0.0032, 0.0012))
    handle = sweep("SC_Handle", hsecs, M["steel"])
    grip = sweep("SC_Grip", [rrect(0, 0.03 + 0.004 * j, 0, 0.0086, 0.0034, 0.0012) for j in range(10)], M["steel_dark"])
    collar = lathe("SC_Collar", [(0, 0.098), (0.0046, 0.098), (0.005, 0.1), (0.005, 0.106), (0.0038, 0.108), (0, 0.108)], M["brass"], seg=48)
    collar.scale = (1.0, 1.0, 0.6)
    # the curved blade: a profile in XY, thin in Z, with a ground edge
    bm = bmesh.new()
    top, bot = [], []
    N = 24
    for i in range(N + 1):
        u = i / N
        y = 0.107 + u * 0.05
        upper = 0.0032 * (1 - u ** 3)
        lower = -0.009 * math.sin(math.pi * min(u * 1.05, 1.0)) ** 0.8 - 0.0006 * (1 - u)
        top.append((upper, y))
        bot.append((lower, y))
    outline = top + bot[::-1]
    for z, s in ((0.00045, 1.0), (-0.00045, 1.0)):
        pass
    vs_top = [bm.verts.new((x, y, 0.0004)) for x, y in outline]
    vs_bot = [bm.verts.new((x, y, -0.0004)) for x, y in outline]
    n = len(outline)
    bm.faces.new(vs_top)
    bm.faces.new(vs_bot[::-1])
    for k in range(n):
        bm.faces.new((vs_top[k], vs_bot[k], vs_bot[(k + 1) % n], vs_top[(k + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    blade = _obj("SC_Blade", bm, M["steel_bright"], smooth=False)
    blade.rotation_euler = (0, math.radians(90), 0)
    return root("Scalpel", loc, rot, [handle, grip, collar, blade])
