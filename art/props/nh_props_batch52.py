"""Props batch 52, the gate passageways kit, for nh_props.py: the paved ways and covered passages that lead through and round the
school's gate. Weathered limestone, granite, sooty crimson brick, black wrought iron, slate, moss, ivy and candlelight; never gory.

The path pieces tile on an 8-stud grid. Every path's centreline runs on a grid line, and every piece's origin is the centre of its
entry end (at ground level) with the piece running toward +Y, so a piece placed on a grid point and turned in 90-degree steps
lands its ports on grid points. Three widths, each with one cross-section that every piece of that width shares exactly:
  W8   walks: dressed limestone edging 0.5 wide (top 0.42), path top 0.25   (Flag*: coursed limestone flags, Gravel*: leaf gravel)
  W12  courts: limestone kerb 0.5, a crimson brick soldier course 0.3, basket-weave brick (Brick*)
  W16  the avenue: granite kerb 0.5, a dished granite gutter 0.7, granite setts in courses (Cobble*, GateThreshold16)
The tiled faces (<Prop>_Path) keep the UVs the builder gives them (nh_props.ATLAS): 8 studs a tile, u across from the centreline,
v along it (a whole number of tiles per piece), so the setts, bricks and gravel run on unbroken across every joint.
Covered passages: GateTunnel, RosePergola, ColonnadeBay, LychPassage, YewTunnel. Registered into nh_props.BUILD.
"""
import math
import os
import zlib

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, set_group, material, _finish
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, _mark, _xform, _dims, flat
import nh_props_batch24 as B24
from nh_props_batch24 import sweep, _paint, _math, _coords, _mix_rgb
import nh_props_batch30 as B30
import nh_props_batch40 as G

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T

PT = 0.25        # path top at every port
KT = 0.42        # kerb top
KW = 0.5         # kerb width
JT = 0.06        # flag joint
TILE = 8.0       # studs per tile of the tiled faces
SETS = {"brick": "NH_GateBasketBrick", "cobble": "NH_GateSetts", "gravel": "NH_GateLeafGravel"}
PORTS = {}       # prop -> [(x, y, z, outward heading in degrees, width, kind)]
CLEAR = {}       # covered prop -> (x0, x1, y0, y1) walk area to test headroom over


# ================================================================== square bars (the fixed winding)

def tube(name, points, radius, mat, closed=False, res=4, square=False, poly=False):
    """nh_props.tube, but a square bar is built here with its profile wound [(-r,-r),(-r,r),(r,r),(r,-r)] so its side faces point
    out (the square-bar audit's fix, whatever nh_props.py's own winding is)."""
    if not square:
        return P.tube(name, points, radius, mat, closed=closed, res=res, square=False, poly=poly)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    if poly:
        sp = cu.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for p, co in zip(sp.points, points):
            p.co = (co[0], co[1], co[2], 1)
    else:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for p, co in zip(sp.bezier_points, points):
            p.co = co
            p.handle_left_type = p.handle_right_type = "AUTO"
    sp.use_cyclic_u = closed
    prof = bpy.data.curves.new(name + "_prof", "CURVE")
    ps = prof.splines.new("POLY")
    ps.points.add(3)
    r = radius
    for i, (x, y) in enumerate([(-r, -r), (-r, r), (r, r), (r, -r)]):
        ps.points[i].co = (x, y, 0, 1)
    ps.use_cyclic_u = True
    prof_ob = bpy.data.objects.new(name + "_prof", prof)
    bpy.context.collection.objects.link(prof_ob)
    cu.bevel_mode = "OBJECT"
    cu.bevel_object = prof_ob
    cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    bpy.data.objects.remove(prof_ob)
    return _finish(ob, mat, 0)


def bar_outward(ob):
    """Share of a square bar's side faces whose normals point away from the bar's axis (1.0 = all outward)."""
    me = ob.data
    pts = [v.co for v in me.vertices]
    c = sum(pts, Vector()) / len(pts)
    good = tot = 0
    for p in me.polygons:
        if len(p.vertices) != 4:
            continue
        tot += 1
        d = p.center - c
        d.z = 0 if abs(p.normal.z) < 0.5 else d.z
        good += p.normal.dot(d) > 0
    return good / max(tot, 1)


# ================================================================== the centreline

def nR(h):
    return (math.sin(h), -math.cos(h))


def nL(h):
    return (-math.sin(h), math.cos(h))


class Run:
    """A centreline of straights and arcs, evaluated exactly at any arc length s. Heading h in radians from +X; the offset o
    is measured to the RIGHT of the heading."""

    def __init__(self, x=0.0, y=0.0, h=90.0):
        self.x0, self.y0, self.h0 = x, y, math.radians(h)
        self.segs = []
        self.L = 0.0

    def end(self):
        return self.at(self.L) if self.segs else (self.x0, self.y0, self.h0)

    def straight(self, L):
        x, y, h = self.end()
        self.segs.append(("S", self.L, L, x, y, h, 0, 0))
        self.L += L
        return self

    def arc(self, R, deg, side):
        """side +1 turns right (clockwise), -1 left."""
        x, y, h = self.end()
        a = math.radians(deg)
        self.segs.append(("A", self.L, R * a, x, y, h, R, side))
        self.L += R * a
        return self

    def at(self, s):
        for k, (t, s0, L, x, y, h, R, side) in enumerate(self.segs):
            if s <= s0 + L + 1e-9 or k == len(self.segs) - 1:
                d = s - s0
                if t == "S":
                    return (x + math.cos(h) * d, y + math.sin(h) * d, h)
                n0 = nR(h) if side > 0 else nL(h)
                cx, cy = x + R * n0[0], y + R * n0[1]
                h1 = h - side * d / R
                n1 = nR(h1) if side > 0 else nL(h1)
                return (cx - R * n1[0], cy - R * n1[1], h1)
        return (self.x0, self.y0, self.h0)

    def pt(self, s, o=0.0):
        x, y, h = self.at(s)
        n = nR(h)
        return (x + o * n[0], y + o * n[1])

    def samples(self, s0, s1, deg=3.0, step=None):
        out = {round(s0, 9), round(s1, 9)}
        for (t, a, L, x, y, h, R, side) in self.segs:
            for b in (a, a + L):
                if s0 < b < s1:
                    out.add(round(b, 9))
            if t == "A":
                st = R * math.radians(deg)
                k = 1
                while a + k * st < a + L:
                    if s0 < a + k * st < s1:
                        out.add(round(a + k * st, 9))
                    k += 1
            elif step:
                k = 1
                while a + k * step < a + L:
                    if s0 < a + k * step < s1:
                        out.add(round(a + k * step, 9))
                    k += 1
        return sorted(out)


# ================================================================== mesh builders

def prism(name, run, s0, s1, prof, mat, bevel=0.0, seg=2, zfun=None, deg=3.0):
    """A closed (o, z) profile swept along the run from s0 to s1 (flat end caps on the planes at s0 and s1). zfun(s) lifts the
    profile's upper points (z > 0.001)."""
    ss = run.samples(s0, s1, deg)
    V, F = [], []
    n = len(prof)
    for s in ss:
        dz = zfun(s) if zfun else 0.0
        for o, z in prof:
            x, y = run.pt(s, o)
            V.append((x, y, z + (dz if z > 0.001 else 0.0)))
    for i in range(len(ss) - 1):
        a, b = i * n, (i + 1) * n
        for k in range(n):
            j = (k + 1) % n
            F.append((a + k, a + j, b + j, b + k))
    F.append(tuple(range(n)))
    F.append(tuple(range((len(ss) - 1) * n, len(ss) * n)))
    ob = G.mk(name, V, F, mat, smooth=False, bevel=0.0)
    G.P_recalc(ob)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = seg
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = True
    return ob


def blocks(prefix, run, s0, s1, prof, mats, unit, rng, bevel=0.035, seg=2, zfun=None):
    """Kerb-like blocks of about `unit` length laid end to end from s0 to s1 (the first starts on s0, the last ends on s1)."""
    n = max(1, round((s1 - s0) / unit))
    mats = mats if isinstance(mats, (list, tuple)) else [mats]
    for i in range(n):
        a, b = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        prism(f"{prefix}{i}", run, a, b, prof, mats[int(rng.integers(len(mats)))], bevel=bevel, seg=seg, zfun=zfun)


def slab3(name, top, depth, mat, bevel=0.03, seg=1):
    """A stone from its top outline (3D points, counter-clockwise seen from above), sides straight down by `depth`."""
    n = len(top)
    V = [(x, y, z - depth) for x, y, z in top] + [tuple(p) for p in top]
    F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n, 2 * n))]
    ob = G.mk(name, V, F, mat, smooth=False, bevel=0.0, tri=True)
    G.P_recalc(ob)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = seg
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = True
    return ob


def poly_prism(name, poly, z0, z1, mat, bevel=0.0, seg=1):
    """A flat outline (x, y) extruded from z0 to z1 (counter-clockwise or not)."""
    if G._area(poly) < 0:
        poly = poly[::-1]
    return slab3(name, [(x, y, z1) for x, y in poly], z1 - z0, mat, bevel=bevel, seg=seg)


def subdiv(poly, step=0.4):
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        k = max(1, int(math.ceil(L / step)))
        for j in range(k):
            t = j / k
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def inset_convex(poly, d):
    """Offset a (nearly) convex counter-clockwise polygon inward by d (each edge moves d along its inward normal)."""
    n = len(poly)
    lines = []
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / L, dx / L
        lines.append(((p[0] + nx * d, p[1] + ny * d), (dx / L, dy / L)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            out.append(p2)
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


# ================================================================== tiled faces

def _tiled_mesh(name, V, F, UV, set_name, prop):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    uv = me.uv_layers.new(name="Bake")
    for poly in me.polygons:
        poly.use_smooth = False
        for li in poly.loop_indices:
            uv.data[li].uv = UV[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    g = P.GROUP
    set_group("Path")
    _finish(ob, bpy.data.materials.get("PathTile") or flat("PathTile", (0.3, 0.3, 0.3), 0.8), 0)
    set_group(g)
    P.ATLAS[f"{prop}_Path"] = set_name
    return ob


def strip(prop, run, s0, s1, o0, o1, set_name, vk=None, v0=0.0, zfun=None, ends=(True, True), across=2):
    """The tiled walking face from o0 to o1 along the run (top at PT, plus end walls down to the ground at the ports). UVs: u = o / 8,
    v = (s - s0) * vk + v0, vk making a whole number of tiles."""
    if vk is None:
        vk = max(1, round((s1 - s0) / TILE)) / (s1 - s0)
    ss = run.samples(s0, s1, 3.0)
    os_ = [o0 + (o1 - o0) * k / (across - 1) for k in range(across)]
    V, F, UV = [], [], []
    m = len(os_)
    for s in ss:
        dz = zfun(s) if zfun else 0.0
        for o in os_:
            x, y = run.pt(s, o)
            V.append((x, y, PT + dz))
            UV.append((o / TILE, (s - s0) * vk + v0))
    for i in range(len(ss) - 1):
        for k in range(m - 1):
            a, b = i * m + k, (i + 1) * m + k
            F.append((a, a + 1, b + 1, b))
    for e, s in ((0, ss[0]), (1, ss[-1])):
        if not ends[e]:
            continue
        dz = zfun(s) if zfun else 0.0
        base = len(V)
        for o in os_:
            x, y = run.pt(s, o)
            V.append((x, y, 0.0))
            UV.append((o / TILE, (s - s0) * vk + v0 - 0.03))
        top = (0 if e == 0 else len(ss) - 1) * m
        for k in range(m - 1):
            if e == 0:
                F.append((base + k, base + k + 1, top + k + 1, top + k))
            else:
                F.append((base + k + 1, base + k, top + k, top + k + 1))
    return _tiled_mesh("PathStrip", V, F, UV, set_name, prop)


def poly_face(prop, poly, set_name, uvfn, z=PT, walls=()):
    """A tiled walking face over a polygon (triangulated), UVs from uvfn(x, y); `walls` lists edges (i, i+1) that get an end wall."""
    if G._area(poly) < 0:
        poly = poly[::-1]
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z)) for x, y in poly]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    for f_ in bm.faces:            # a concave outline can come back with a flipped ear: keep every triangle facing up
        if f_.normal.z < 0:
            f_.normal_flip()
    V = [tuple(v.co) for v in bm.verts]
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    UV = [uvfn(x, y) for x, y, _ in V]
    cx, cy = G._centroid(poly)
    for (p, q) in walls:
        if (q[1] - p[1]) * ((p[0] + q[0]) / 2 - cx) - (q[0] - p[0]) * ((p[1] + q[1]) / 2 - cy) < 0:
            p, q = q, p
        a, b = len(V), len(V) + 1
        V += [(p[0], p[1], 0.0), (q[0], q[1], 0.0), (q[0], q[1], z), (p[0], p[1], z)]
        UV += [uvfn(*p), uvfn(*q), uvfn(*q), uvfn(*p)]
        F.append((a, b, b + 1, b + 2))
    return _tiled_mesh("PathFace", V, F, UV, set_name, prop)


def world_uv(x, y):
    return (x / TILE, y / TILE)


# ================================================================== materials

def kit(M):
    K = G.gk2(M)
    K["gran"] = G.lichen(G.mossy(material("KerbGranite", "NH_Slate", tint=(0.25, 0.25, 0.27), scale=0.45, rough_mul=0.6, rough_add=0.3, normal=0.7,
                                          wear=0.35, dirt=1.0), 0.2, scale=2.0), 3.0, 0.08)
    K["grandark"] = G.mossy(material("GraniteDark", "NH_Slate", tint=(0.16, 0.16, 0.18), scale=0.45, rough_mul=0.6, rough_add=0.3, normal=0.7,
                                     wear=0.3, dirt=1.0), 0.25, scale=2.0)
    K["mortar"] = G.mossy(flat("Mortar", (0.07, 0.07, 0.06), 0.95, dirt=0.6), 0.75, scale=3.5, col=(0.05, 0.09, 0.03))
    B24._bump(K["mortar"], G._noise(K["mortar"], 30.0), 0.02, 0.5)
    K["flags"] = [K["flag"], K["flag"], K["flagdark"], K["limel"]]
    K["leaves"] = [G.mossy(flat(f"FallenLeaf{k}", c, 0.72, dirt=0.4), 0.0) for k, c in
                   enumerate(((0.32, 0.085, 0.025), (0.42, 0.2, 0.035), (0.15, 0.022, 0.02), (0.19, 0.1, 0.045), (0.38, 0.28, 0.07)))]
    K["glow"] = flat("GateGlow", (1.0, 0.68, 0.32), 0.5)
    K["stone"], K["stonedark"] = M["stone"], M["stonedark"]
    K["glass"] = flat("GateGlass", (0.55, 0.5, 0.4), 0.1)
    return K


def rng_for(name):
    return G.RNG(zlib.crc32(name.encode()) & 0xFFFF)


# ================================================================== cross-sections

def kerb_prof(W, side, h=KT, ch=0.08, kw=KW):
    oi, oo = W / 2 - kw, W / 2
    pr = [(oi, 0.0), (oo, 0.0), (oo, h), (oi + ch, h), (oi, h - ch)]
    if side < 0:
        pr = [(-o, z) for o, z in pr][::-1]
    return pr


def gutter_prof(side):
    o0, o1 = 6.8, 7.5
    pr = [(o0, 0.0), (o1, 0.0), (o1, PT), (7.33, PT - 0.045), (7.15, PT - 0.065), (6.97, PT - 0.045), (o0, PT)]
    if side < 0:
        pr = [(-o, z) for o, z in pr][::-1]
    return pr


def band_prof(o0, o1, z1, z0=0.0):
    return [(o0, z0), (o1, z0), (o1, z1), (o0, z1)]


INNER = {"flag": 3.5, "gravel": 3.5, "brick": 5.2, "cobble": 6.8}
WIDTH = {"flag": 8, "gravel": 8, "brick": 12, "cobble": 16}


def flag_course(K, run, s0, s1, a, rng, prefix, zfun=None, ports=(True, True), flat_=False, mats=None, depth=0.16):
    """Coursed limestone flags from o = -a to a, s0 to s1: courses across the path, flags of random width in each course, joints JT
    (half a joint at every edge, so two pieces meet on a whole one). Flags at a port are dead flat on PT."""
    mats = mats or K["flags"]
    zf = zfun or (lambda s: 0.0)
    cs, s = [], s0
    while s < s1 - 1e-6:
        c = rng.uniform(1.05, 1.75)
        if s1 - (s + c) < 0.85:
            c = s1 - s
        cs.append((s, min(s + c, s1)))
        s += c
    j = JT / 2
    out = []
    for ci, (sa, sb) in enumerate(cs):
        parts, o = [], -a
        while o < a - 1e-6:
            w = rng.uniform(1.25, 2.5)
            if a - (o + w) < 0.9:
                w = a - o
            parts.append((o, min(o + w, a)))
            o += w
        port0 = ports[0] and abs(sa - s0) < 1e-6
        port1 = ports[1] and abs(sb - s1) < 1e-6
        for fi, (oa, ob) in enumerate(parts):
            q = [(oa + j, sa + j), (ob - j, sa + j), (ob - j, sb - j), (oa + j, sb - j)]
            if not (port0 or port1) and rng.random() < 0.22:      # a broken corner
                k = int(rng.integers(4))
                p, pn, pp = q[k], q[(k + 1) % 4], q[k - 1]
                t1, t2 = rng.uniform(0.12, 0.25), rng.uniform(0.12, 0.25)
                c1 = (p[0] + (pn[0] - p[0]) * t1, p[1] + (pn[1] - p[1]) * t1)
                c2 = (p[0] + (pp[0] - p[0]) * t2, p[1] + (pp[1] - p[1]) * t2)
                q = q[:k] + [c2, c1] + q[k + 1:]
            q = subdiv(q, 0.45)
            flat_here = flat_ or port0 or port1
            dz = 0.0 if flat_here else rng.uniform(-0.035, 0.0)
            to, ts = (0.0, 0.0) if flat_here else (rng.uniform(-0.01, 0.01), rng.uniform(-0.008, 0.008))
            oc, sc = (oa + ob) / 2, (sa + sb) / 2
            top = []
            for o_, s_ in q:
                x, y = run.pt(s_, o_)
                top.append((x, y, PT + dz + to * (o_ - oc) + ts * (s_ - sc) + zf(s_)))
            slab3(f"{prefix}{ci}_{fi}", top, depth, mats[int(rng.integers(len(mats)))], bevel=0.035)
            out.append(((oa, ob), (sa, sb)))
    return out


def flags_poly(K, region, rng, prefix, ports=(), ang=0.0, z=PT, mats=None, depth=0.16, origin=(0.0, 0.0)):
    """Coursed flags over a polygon (courses along the local X turned by ang), each flag clipped to the region; flags touching a
    port segment (a list of ((x0, y0), (x1, y1))) are flat on PT."""
    mats = mats or K["flags"]
    if G._area(region) < 0:
        region = region[::-1]
    ca, sa_ = math.cos(ang), math.sin(ang)

    def W(u, v):
        return (origin[0] + u * ca - v * sa_, origin[1] + u * sa_ + v * ca)
    loc = [((x - origin[0]) * ca + (y - origin[1]) * sa_, -(x - origin[0]) * sa_ + (y - origin[1]) * ca) for x, y in region]
    u0, u1 = min(p[0] for p in loc), max(p[0] for p in loc)
    v0, v1 = min(p[1] for p in loc), max(p[1] for p in loc)
    j = JT / 2
    v = v0
    k = 0
    while v < v1 - 1e-6:
        c = rng.uniform(1.05, 1.75)
        u = u0 - rng.uniform(0, 1.5)
        while u < u1:
            w = rng.uniform(1.25, 2.5)
            rect = [W(u, v), W(u + w, v), W(u + w, v + c), W(u, v + c)]
            piece = G._clean(G._sh_clip(region, rect))
            if len(piece) >= 3 and abs(G._area(piece)) > 0.004:
                if G._area(piece) < 0:
                    piece = piece[::-1]
                piece = inset_convex(piece, j)
                if len(piece) >= 3 and G._area(piece) > 0.002 and all(G.inside_poly(p, region) or _seg_dist(p, *_nearest_edge(p, region)) < 0.05
                                                                        for p in piece):
                    near = any(_seg_dist(p, a, b) < 0.08 for p in piece for a, b in ports)
                    dz = 0.0 if near else rng.uniform(-0.03, 0.0)
                    slab3(f"{prefix}{k}", [(x, y, z + dz) for x, y in subdiv(piece, 0.6)], depth, mats[int(rng.integers(len(mats)))], bevel=0.035)
                    k += 1
            u += w
        v += c


def _nearest_edge(p, poly):
    best, e = 1e9, (poly[0], poly[1])
    for i in range(len(poly)):
        q, r = poly[i], poly[(i + 1) % len(poly)]
        d = _seg_dist(p, q, r)
        if d < best:
            best, e = d, (q, r)
    return e


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t)


def soldiers(K, run, s0, s1, o0, o1, rng, prefix, zfun=None):
    """A soldier course: bricks on end side by side along the run (0.22 a brick), tops on PT, over a mortar bed."""
    prism(f"{prefix}Bed", run, s0, s1, band_prof(o0, o1, PT - 0.07), K["mortar"])
    n = max(1, round((s1 - s0) / 0.24))
    j = 0.018
    for i in range(n):
        a, b = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
        q = [(o0 + j, a + j), (o1 - j, a + j), (o1 - j, b - j), (o0 + j, b - j)]
        dz = rng.uniform(-0.012, 0.0)
        top = [(*run.pt(s_, o_), PT + dz + (zfun(s_) if zfun else 0.0)) for o_, s_ in q]
        slab3(f"{prefix}{i}", top, 0.2, K["bricks"][int(rng.integers(3))], bevel=0.012)


def lay_run(K, kind, run, s0, s1, rng, prop, prefix="R", left=True, right=True, vk=None, v0=0.0, zfun=None, ports=(True, True)):
    """The whole cross-section of a path kind along a run: kerbs (and gutters / soldier courses) and the walking face."""
    W = WIDTH[kind]
    a = INNER[kind]
    sides = [sd for sd, on in ((-1, left), (1, right)) if on]
    if kind == "flag":
        for sd in sides:
            blocks(f"{prefix}Kerb{sd}_", run, s0, s1, kerb_prof(W, sd), [K["lime"], K["lime"], K["limel"]], 2.0, rng, zfun=zfun)
        prism(f"{prefix}Bed", run, s0, s1, band_prof(-a, a, PT - 0.1), K["mortar"], zfun=zfun)
        flag_course(K, run, s0, s1, a, rng, f"{prefix}Flag", zfun=zfun, ports=ports)
    elif kind == "gravel":
        for sd in sides:
            blocks(f"{prefix}Kerb{sd}_", run, s0, s1, kerb_prof(W, sd), [K["slatec"], K["grandark"]], 0.85, rng, zfun=zfun)
        strip(prop, run, s0, s1, -a, a, SETS["gravel"], vk=vk, v0=v0, zfun=zfun)
    elif kind == "brick":
        for sd in sides:
            blocks(f"{prefix}Kerb{sd}_", run, s0, s1, kerb_prof(W, sd), [K["limel"], K["lime"]], 2.4, rng, zfun=zfun)
            o0, o1 = (5.2, 5.5) if sd > 0 else (-5.5, -5.2)
            soldiers(K, run, s0, s1, o0, o1, rng, f"{prefix}Sold{sd}_", zfun=zfun)
        strip(prop, run, s0, s1, -a, a, SETS["brick"], vk=vk, v0=v0, zfun=zfun)
    elif kind == "cobble":
        for sd in sides:
            blocks(f"{prefix}Kerb{sd}_", run, s0, s1, kerb_prof(W, sd), [K["gran"], K["gran"], K["grandark"]], 1.6, rng, zfun=zfun)
            blocks(f"{prefix}Gut{sd}_", run, s0, s1, gutter_prof(sd), [K["gran"], K["grandark"]], 1.0, rng, bevel=0.02, seg=1, zfun=zfun)
        strip(prop, run, s0, s1, -a, a, SETS["cobble"], vk=vk, v0=v0, zfun=zfun)


def port(name, x, y, h, kind, z=0.0):
    PORTS.setdefault(name, []).append((round(x, 4), round(y, 4), z, h, WIDTH[kind], kind))


# ================================================================== simple runs: straights, curves, S-bends

def run_piece(M, name, kind, segs):
    K = kit(M)
    rng = rng_for(name)
    r = Run()
    for sg in segs:
        if sg[0] == "S":
            r.straight(sg[1])
        else:
            r.arc(sg[1], sg[2], sg[3])
    lay_run(K, kind, r, 0.0, r.L, rng, name)
    x, y, h = r.end()
    PORTS[name] = []
    port(name, 0, 0, -90, kind)
    port(name, x, y, math.degrees(h), kind)
    return _dims()


SB_T = math.degrees(2 * math.atan(0.5))     # the S-bend: two arcs of 10 shifting the line 8 over 16
FORK_R = 8 / (1 - math.cos(math.pi / 4)) - 16   # branch arcs of the fork: with a FlagCurve45 after, the lanes land 8 out and 24 on
FORK_T = 24 - (FORK_R + 16) * math.sin(math.pi / 4)


# ================================================================== the fork

def _cross_s(run, o, xline, lo, hi):
    """The s (lo..hi) where the run's offset line o crosses x = xline."""
    f = lambda s: run.pt(s, o)[0] - xline
    a, b = lo, hi
    for _ in range(60):
        m = (a + b) / 2
        if (f(a) > 0) == (f(m) > 0):
            a = m
        else:
            b = m
    return (a + b) / 2


def flag_fork(M):
    name = "FlagFork"
    K = kit(M)
    rng = rng_for(name)
    t = FORK_T
    trunk = Run().straight(t)
    Lr = Run(0, t, 90).arc(FORK_R, 45, -1)     # left branch
    Rr = Run(0, t, 90).arc(FORK_R, 45, 1)
    Lb = Lr.L
    for sd, rr in ((-1, trunk), (1, trunk)):
        blocks(f"TrunkKerb{sd}_", rr, 0, t, kerb_prof(8, sd), [K["lime"], K["limel"]], 2.0, rng)
    blocks("LKerbOut", Lr, 0, Lb, kerb_prof(8, -1), [K["lime"], K["limel"]], 2.0, rng)
    blocks("RKerbOut", Rr, 0, Lb, kerb_prof(8, 1), [K["lime"], K["limel"]], 2.0, rng)
    # the gore: each branch's inner kerb once it is clear of the other branch, and a nose stone where they part
    sI = _cross_s(Lr, 3.5, 0.0, 0.5, Lb)          # inner faces cross here
    sO = _cross_s(Lr, 4.0, 0.0, 0.5, Lb)          # outer faces cross here
    blocks("LKerbIn", Lr, sO, Lb, kerb_prof(8, 1), [K["lime"]], 2.0, rng)
    blocks("RKerbIn", Rr, sO, Lb, kerb_prof(8, -1), [K["lime"]], 2.0, rng)
    A = Lr.pt(sO, 3.5)
    B = Lr.pt(sO, 4.0)
    C = Lr.pt(sI, 3.5)
    nose = [C] + [Rr.pt(sI + (sO - sI) * k / 6, -3.5) for k in range(1, 7)] + [B] + [Lr.pt(sO - (sO - sI) * k / 6, 3.5) for k in range(0, 6)]
    poly_prism("GoreNose", G._clean(nose, 1e-4), 0.0, KT, K["lime"], bevel=0.03)
    # the paving: one outline round the trunk and both branches
    out = [(-3.5, 0.0)]
    out += [Lr.pt(s, -3.5) for s in Lr.samples(0, Lb, 3)]
    out += [Lr.pt(s, 3.5) for s in reversed(Lr.samples(sI, Lb, 3))]
    out += [Rr.pt(s, -3.5) for s in Rr.samples(sI, Lb, 3)]
    out += [Rr.pt(s, 3.5) for s in reversed(Rr.samples(0, Lb, 3))]
    out += [(3.5, 0.0)]
    out = G._clean(out, 1e-4)
    poly_prism("Bed", out, 0.0, PT - 0.1, K["mortar"])
    pe = [((-3.5, 0), (3.5, 0)), (Lr.pt(Lb, -3.5), Lr.pt(Lb, 3.5)), (Rr.pt(Lb, -3.5), Rr.pt(Lb, 3.5))]
    flags_poly(K, out, rng, "Flag", ports=pe)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    for rr in (Lr, Rr):
        x, y, h = rr.end()
        port(name, x, y, math.degrees(h), "flag")
    # a waymark on the gore nose: a squat limestone marker with an iron hand pointing both ways
    return _dims()


# ================================================================== flag steps, ramp, gate apron, fallen leaves

def flag_steps(M):
    """Four risers of 0.5 between limestone cheek walls (the kerbs rise with the stair), iron handrails on the cheeks."""
    name = "FlagSteps"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(8.0)
    noses = [1.2, 2.8, 4.4, 6.0]
    rise = 0.5

    def zstep(s):
        return rise * sum(1 for n in noses if s >= n - 1e-9)

    def zcheek(s):        # the cheek's coping: level at both ends, sloping through the nosings (never below a tread)
        if s <= noses[0] - 0.6:
            return 0.0
        if s <= noses[0]:
            return rise * (s - noses[0] + 0.6) / 0.6
        return min(4 * rise, rise + rise * (s - noses[0]) / (noses[1] - noses[0]))
    for sd in (-1, 1):
        blocks(f"Cheek{sd}_", r, 0, 8, kerb_prof(8, sd), [K["lime"], K["limel"]], 2.0, rng, zfun=zcheek)
    # the bed under each tread, the risers and the treads (one or two big slabs across, a rounded nosing)
    edges = [0.0] + noses + [8.0]
    for i in range(len(edges) - 1):
        sa, sb = edges[i], edges[i + 1]
        z = zstep(sa)
        prism(f"TreadBed{i}", r, sa, sb, band_prof(-3.5, 3.5, PT - 0.1 + z), K["mortar"])
        if i == 0 or i == len(edges) - 2:
            flag_course(K, r, sa, sb, 3.5, rng, f"Land{i}_", zfun=lambda s, z=z: z, ports=(i == 0, i == len(edges) - 2))
        else:
            o_mid = rng.uniform(-0.8, 0.8)
            for k, (oa, ob) in enumerate(((-3.5, o_mid), (o_mid, 3.5))):
                j = JT / 2
                q = subdiv([(oa + j, sa + j), (ob - j, sa + j), (ob - j, sb - j), (oa + j, sb - j)], 0.45)
                top = [(*r.pt(s_, o_), PT + z) for o_, s_ in q]
                slab3(f"Tread{i}_{k}", top, 0.18, K["flags"][int(rng.integers(4))], bevel=0.05, seg=2)
        if i > 0:      # the riser face under this tread's nosing
            prism(f"Riser{i}", r, sa - 0.02, sa + 0.1, band_prof(-3.5, 3.5, PT + z - 0.02, PT + z - rise - 0.1), K["flagdark"], bevel=0.02)
    # iron handrails on the cheek copings: newel posts at the foot and head, a rail parallel to the slope
    for sd in (-1, 1):
        o = sd * 3.75
        p0, p1 = r.pt(0.55, o), r.pt(7.45, o)
        z0, z1 = KT + zcheek(0.55), KT + zcheek(7.45)
        for k, (p, z) in enumerate(((p0, z0), (p1, z1))):
            tube(f"Newel{sd}{k}", [(p[0], p[1], z), (p[0], p[1], z + 2.6)], 0.06, K["iron"], square=True, poly=True)
            sphere(f"NewelKnob{sd}{k}", 0.11, (p[0], p[1], z + 2.72), K["brass"], seg=12, rings=6)
        pts = []
        for k in range(15):
            s = 0.55 + (7.45 - 0.55) * k / 14
            p = r.pt(s, o)
            pts.append((p[0], p[1], KT + zcheek(s) + 2.35))
        tube(f"Rail{sd}", pts, 0.05, K["iron"], square=True, poly=True)
        for k in range(1, 7):
            s = 0.55 + (7.45 - 0.55) * k / 7
            p = r.pt(s, o)
            tube(f"Baluster{sd}{k}", [(p[0], p[1], KT + zcheek(s)), (p[0], p[1], KT + zcheek(s) + 2.35)], 0.025, K["iron"], square=True, poly=True)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, 8, 90, "flag", z=4 * rise)
    return _dims()


def flag_ramp(M):
    """A 16-long flagged ramp rising 2.0 on an eased curve (level at both ends, so it meets the walks with no kink), low cheek walls
    and an iron handrail."""
    name = "FlagRamp"
    K = kit(M)
    rng = rng_for(name)
    L, H = 16.0, 2.0
    r = Run().straight(L)
    zf = lambda s: H * (1 - math.cos(math.pi * max(0.0, min(1.0, s / L)))) / 2
    for sd in (-1, 1):
        blocks(f"Cheek{sd}_", r, 0, L, kerb_prof(8, sd), [K["lime"], K["limel"]], 2.0, rng, zfun=zf)
    prism("Bed", r, 0, L, band_prof(-3.5, 3.5, PT - 0.1), K["mortar"], zfun=zf)
    flag_course(K, r, 0, L, 3.5, rng, "Flag", zfun=zf)
    for sd in (-1, 1):
        o = sd * 3.75
        pts = []
        for k in range(25):
            s = 0.6 + (L - 1.2) * k / 24
            p = r.pt(s, o)
            pts.append((p[0], p[1], KT + zf(s) + 2.3))
        tube(f"Rail{sd}", pts, 0.05, K["iron"], square=True, poly=True)
        for k in range(6):
            s = 0.6 + (L - 1.2) * k / 5
            p = r.pt(s, o)
            tube(f"Post{sd}{k}", [(p[0], p[1], KT + zf(s)), (p[0], p[1], KT + zf(s) + 2.42)], 0.05, K["iron"], square=True, poly=True)
            cone(f"PostCap{sd}{k}", 0.09, 0.0, 0.22, (p[0], p[1], KT + zf(s) + 2.53), K["iron"], verts=4)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, L, 90, "flag", z=H)
    return _dims()


def gate_apron(M):
    """The 8-wide walk's end at IronGate (place IronGate's origin at (0, 8, 0) of this piece): the flags run up to a granite sill that
    eases down to the gate's own threshold (top 0.08); the edging ends in rounded stones short of the gate piers' feet."""
    name = "GateApron8"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(8.0)
    ke = 6.9
    y0 = 6.7            # the sill's front
    for sd in (-1, 1):
        blocks(f"Kerb{sd}_", r, 0, ke - 0.35, kerb_prof(8, sd), [K["lime"], K["limel"]], 2.0, rng)
        cx = sd * 3.75
        pts = [(cx + 0.25 * math.cos(math.pi * k / 12), ke - 0.35 + 0.35 * math.sin(math.pi * k / 12)) for k in range(13)]
        poly_prism(f"KerbEnd{sd}", pts, 0.0, KT, K["lime"], bevel=0.05, seg=2)
    prism("Bed", r, 0, y0, band_prof(-3.5, 3.5, PT - 0.1), K["mortar"])
    flag_course(K, r, 0, y0, 3.5, rng, "Flag", ports=(True, True))
    # the sill: a granite slab 7.4 wide whose top eases from PT down to 0.08 (IronGate's threshold) at the gate line's front
    n, y1, xw = 10, 7.5, 3.45
    V, F = [], []
    for i in range(n + 1):
        y = y0 + JT / 2 + (y1 - y0 - JT / 2) * i / n
        tt = max(0.0, (y - 7.0) / (y1 - 7.0))
        z = PT - (PT - 0.08) * (3 * tt * tt - 2 * tt ** 3)
        V += [(-xw, y, z), (xw, y, z)]
    base = len(V)
    V += [(x, y, 0.0) for (x, y, z) in V]
    for i in range(n):
        a, b = i * 2, (i + 1) * 2
        F += [(a, a + 1, b + 1, b), (base + b, base + b + 1, base + a + 1, base + a), (a, b, base + b, base + a), (a + 1, base + a + 1, base + b + 1, b + 1)]
    F += [(0, base, base + 1, 1), (n * 2, n * 2 + 1, base + n * 2 + 1, base + n * 2)]
    ob = G.mk("Sill", V, F, K["gran"], smooth=False)
    G.P_recalc(ob)
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width, md.segments, md.limit_method = 0.03, 1, "ANGLE"
    md.angle_limit = math.radians(30)
    cyl("BoltSocket", 0.09, 0.03, (0.0, 6.95, PT - 0.005), K["brass"], verts=16)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    return _dims()


def _leaf(name, c, L, w, ang, z, mat, rng, curl=0.006):
    pts = []
    n = 7
    for k in range(n + 1):
        t = k / n
        x = (t - 0.5) * L
        y = w * 0.5 * math.sin(math.pi * t) ** 0.8 * (1 + 0.25 * math.sin(t * 9 + rng.uniform(0, 3)))
        pts.append((x, y))
    pts += [(x, -y * rng.uniform(0.85, 1.0)) for x, y in reversed(pts[1:-1])]
    ca, sa = math.cos(ang), math.sin(ang)
    top = [(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca, z + curl * (abs(x) / (L / 2)) ** 2 + 0.006 * (1 - abs(y) / (w / 2 + 1e-6))) for x, y in pts]
    me_ob = slab3(name, top, 0.006, mat, bevel=0.0)
    return me_ob


def leaf_walk(M):
    """A 16-long flagged walk under fallen leaves: rust, amber, oxblood and brown, drifted against the edging and lying on it."""
    name = "LeafWalk16"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(16)
    for sd in (-1, 1):
        blocks(f"Kerb{sd}_", r, 0, 16, kerb_prof(8, sd), [K["lime"], K["limel"]], 2.0, rng)
    prism("Bed", r, 0, 16, band_prof(-3.5, 3.5, PT - 0.1), K["mortar"])
    flag_course(K, r, 0, 16, 3.5, rng, "Flag", flat_=True)
    k = 0
    for i in range(240):
        # more toward the edges (drifts), fewer in the middle where feet clear them
        o = rng.uniform(-1, 1)
        o = math.copysign(abs(o) ** 0.55, o) * 3.2
        s = rng.uniform(0.3, 15.7)
        if abs(o) < 1.4 and rng.random() < 0.6:
            continue
        x, y = r.pt(s, o)
        L = rng.uniform(0.28, 0.5)
        _leaf(f"Leaf{k}", (x, y), L, L * rng.uniform(0.45, 0.7), rng.uniform(0, 6.28), PT + 0.004, K["leaves"][int(rng.integers(5))], rng)
        k += 1
    for sd in (-1, 1):       # a few on the edging stones
        for i in range(9):
            s = rng.uniform(0.4, 15.6)
            x, y = r.pt(s, sd * 3.78)
            L = rng.uniform(0.22, 0.34)
            _leaf(f"KLeaf{sd}{i}", (x, y), L, L * 0.55, rng.uniform(-0.4, 0.4) + math.pi / 2, KT + 0.004, K["leaves"][int(rng.integers(5))], rng)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, 16, 90, "flag")
    return _dims()


# ================================================================== the brick court (W12)

def brick_tee(M):
    """W12 brick through along Y with an 8-wide flag walk leaving to +X (its port at (8, 8)); the soldier course runs on across the
    mouth and a flush limestone mouth stone takes the walk's flags."""
    name = "BrickTee"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(16)
    blocks("KerbL", r, 0, 16, kerb_prof(12, -1), [K["limel"], K["lime"]], 2.4, rng)
    soldiers(K, r, 0, 16, -5.5, -5.2, rng, "SoldL")
    soldiers(K, r, 0, 16, 5.2, 5.5, rng, "SoldR")
    blocks("KerbRa", r, 0, 4.5, kerb_prof(12, 1), [K["limel"], K["lime"]], 2.4, rng)
    blocks("KerbRb", r, 11.5, 16, kerb_prof(12, 1), [K["limel"], K["lime"]], 2.4, rng)
    strip(name, r, 0, 16, -5.2, 5.2, SETS["brick"])
    poly_prism("MouthStone", [(5.5, 4.5 + JT / 2), (6.0 - JT / 2, 4.5 + JT / 2), (6.0 - JT / 2, 11.5 - JT / 2), (5.5, 11.5 - JT / 2)], 0.0, PT,
               K["limel"], bevel=0.03)
    b = Run(6.0, 8.0, 0.0).straight(2.0)
    lay_run(K, "flag", b, 0, 2.0, rng, name, prefix="B", ports=(False, True))
    PORTS[name] = []
    port(name, 0, 0, -90, "brick")
    port(name, 0, 16, 90, "brick")
    port(name, 8, 8, 0, "flag")
    return _dims()


def brick_cross(M):
    """W12 brick crossroads in a 16 x 16 cell: the basket weave runs straight through both ways (its pattern is the same turned a
    quarter, so the arms meet the straights on the lattice); kerb corners are squared, the soldier courses run round them."""
    name = "BrickCross"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(16)
    for sd in (-1, 1):
        x = sd * 5.75
        blocks(f"KerbA{sd}", r, 0, 2.5, kerb_prof(12, sd), [K["limel"], K["lime"]], 2.4, rng)
        blocks(f"KerbB{sd}", r, 13.5, 16, kerb_prof(12, sd), [K["limel"], K["lime"]], 2.4, rng)
        soldiers(K, r, 0, 2.8, *sorted((sd * 5.2, sd * 5.5)), rng, f"SoldA{sd}")
        soldiers(K, r, 13.2, 16, *sorted((sd * 5.2, sd * 5.5)), rng, f"SoldB{sd}")
        arm = Run(sd * 6.0, 8.0, 0.0 if sd > 0 else 180.0).straight(2.0)
        for sk in (-1, 1):
            blocks(f"ArmKerb{sd}{sk}", arm, 0, 2.0, kerb_prof(12, sk), [K["limel"]], 2.4, rng)
        arm2 = Run(sd * 5.5, 8.0, 0.0 if sd > 0 else 180.0).straight(2.5)
        for sk in (-1, 1):
            soldiers(K, arm2, 0, 2.5, *sorted((sk * 5.2, sk * 5.5)), rng, f"ArmSold{sd}{sk}")
    # the brick: one face over the plus shape, world UVs
    poly_face(name, [(-5.2, 0), (5.2, 0), (5.2, 16), (-5.2, 16)], SETS["brick"], world_uv, walls=[((-5.2, 0), (5.2, 0)), ((-5.2, 16), (5.2, 16))])
    poly_face(name, [(5.2, 2.8), (8, 2.8), (8, 13.2), (5.2, 13.2)], SETS["brick"], world_uv, walls=[((8, 2.8), (8, 13.2))])
    poly_face(name, [(-8, 2.8), (-5.2, 2.8), (-5.2, 13.2), (-8, 13.2)], SETS["brick"], world_uv, walls=[((-8, 2.8), (-8, 13.2))])
    PORTS[name] = []
    port(name, 0, 0, -90, "brick")
    port(name, 0, 16, 90, "brick")
    port(name, 8, 8, 0, "brick")
    port(name, -8, 8, 180, "brick")
    return _dims()


def brick_curve90(M):
    """W12 brick quarter turn (centre line radius 8): its basket weave in world UVs, so it meets a straight at either end on the
    lattice."""
    name = "BrickCurve90"
    K = kit(M)
    rng = rng_for(name)
    r = Run().arc(8, 90, 1)
    for sd in (-1, 1):
        blocks(f"Kerb{sd}_", r, 0, r.L, kerb_prof(12, sd), [K["limel"], K["lime"]], 2.4 if sd < 0 else 1.2, rng)
        soldiers(K, r, 0, r.L, *sorted((sd * 5.2, sd * 5.5)), rng, f"Sold{sd}_")
    ss = r.samples(0, r.L, 2.0)
    pl = [r.pt(s, -5.2) for s in ss] + [r.pt(s, 5.2) for s in reversed(ss)]
    poly_face(name, pl, SETS["brick"], world_uv, walls=[((-5.2, 0), (5.2, 0)), (r.pt(r.L, -5.2), r.pt(r.L, 5.2))])
    x, y, h = r.end()
    PORTS[name] = []
    port(name, 0, 0, -90, "brick")
    port(name, x, y, math.degrees(h), "brick")
    return _dims()


# ================================================================== the avenue (W16)

def cobble_branch(M):
    """The avenue through along Y with an 8-wide flag walk leaving at a dropped kerb to +X (its port at (8, 8)); the gutter runs on
    across the mouth."""
    name = "CobbleBranch"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(16)
    blocks("KerbL", r, 0, 16, kerb_prof(16, -1), [K["gran"], K["grandark"]], 1.6, rng)
    blocks("KerbRa", r, 0, 4.0, kerb_prof(16, 1), [K["gran"], K["grandark"]], 1.5, rng)
    blocks("KerbRb", r, 12.0, 16, kerb_prof(16, 1), [K["gran"], K["grandark"]], 1.5, rng)
    stub = Run(7.5, 8.0, 0.0).straight(0.5)
    for sd in (-1, 1):
        prism(f"Stub{sd}", stub, 0, 0.5, kerb_prof(8, sd), K["gran"], bevel=0.035)
    prism("MouthBed", stub, 0, 0.5, band_prof(-3.5, 3.5, PT - 0.1), K["mortar"])
    for sd in (-1, 1):
        blocks(f"Gut{sd}_", r, 0, 16, gutter_prof(sd), [K["gran"], K["grandark"]], 1.0, rng, bevel=0.02, seg=1)
    strip(name, r, 0, 16, -6.8, 6.8, SETS["cobble"])
    # the dropped kerb: three flush granite stones across the mouth
    for k in range(3):
        y0 = 4.5 + 7.0 * k / 3 + JT / 2
        y1 = 4.5 + 7.0 * (k + 1) / 3 - JT / 2
        poly_prism(f"Dropped{k}", [(7.5, y0), (8.0 - JT / 2, y0), (8.0 - JT / 2, y1), (7.5, y1)], PT - 0.16, PT, K["gran"], bevel=0.03)
    PORTS[name] = []
    port(name, 0, 0, -90, "cobble")
    port(name, 0, 16, 90, "cobble")
    port(name, 8, 8, 0, "flag")
    return _dims()


def cobble_flare(M):
    """A forecourt widening: an 8-wide flag walk (y = 0) opening out over 16 into the avenue (y = 16): the kerbs swing out on
    reverse curves, a granite band where the flags give way to setts, the gutters begin half way."""
    name = "CobbleFlare"
    K = kit(M)
    rng = rng_for(name)
    th = math.degrees(2 * math.atan(4 / 16))
    R = 8 / math.sin(math.radians(th))
    kr = {sd: Run(sd * 3.75, 0, 90).arc(R, th, sd).arc(R, th, -sd) for sd in (-1, 1)}
    L = kr[1].L
    g0 = L * 0.5
    kp = {1: [(-0.25, 0.0), (0.25, 0.0), (0.25, KT), (-0.17, KT), (-0.25, KT - 0.08)],
          -1: [(-0.25, 0.0), (0.25, 0.0), (0.25, KT - 0.08), (0.17, KT), (-0.25, KT)]}
    gp = {1: [(-0.95, 0.0), (-0.25, 0.0), (-0.25, PT), (-0.42, PT - 0.045), (-0.6, PT - 0.065), (-0.78, PT - 0.045), (-0.95, PT)],
          -1: [(0.25, 0.0), (0.95, 0.0), (0.95, PT), (0.78, PT - 0.045), (0.6, PT - 0.065), (0.42, PT - 0.045), (0.25, PT)]}
    for sd in (-1, 1):
        blocks(f"Kerb{sd}_", kr[sd], 0, L, kp[sd], [K["gran"], K["grandark"], K["lime"]], 1.6, rng)
        blocks(f"Gut{sd}_", kr[sd], g0, L, gp[sd], [K["gran"], K["grandark"]], 1.0, rng, bevel=0.02, seg=1)

    def face(sd, s):       # the walking face's edge on side sd at s (the kerb's inner face, or the gutter's once it starts)
        return kr[sd].pt(s, -sd * (0.95 if s >= g0 - 1e-9 else 0.25))
    yb0, yb1 = 3.0, 3.6
    sb0 = {sd: _y_at(kr[sd], -sd * 0.25, yb0) for sd in (-1, 1)}
    sb1 = {sd: _y_at(kr[sd], -sd * 0.25, yb1) for sd in (-1, 1)}
    # flags (y 0 .. 3)
    fl = [face(-1, 0.0), face(1, 0.0)] + [face(1, s) for s in kr[1].samples(0, sb0[1], 2.0)[1:]]
    fl += [face(-1, s) for s in reversed(kr[-1].samples(0, sb0[-1], 2.0)[1:])]
    fl = G._clean(fl, 1e-4)
    poly_prism("FlagBed", fl, 0.0, PT - 0.1, K["mortar"])
    flags_poly(K, fl, rng, "Flag", ports=[((-3.5, 0), (3.5, 0))])
    # the band: five granite slabs across
    a0, b0 = face(-1, sb0[-1]), face(1, sb0[1])
    a1, b1 = face(-1, sb1[-1]), face(1, sb1[1])
    nb = 5
    for k in range(nb):
        t0, t1 = k / nb, (k + 1) / nb
        lerp = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        q = [lerp(a0, b0, t0), lerp(a0, b0, t1), lerp(a1, b1, t1), lerp(a1, b1, t0)]
        q = inset_convex(q, JT / 2)
        poly_prism(f"Band{k}", q, 0.0, PT, K["gran"], bevel=0.03)
    # the setts, out to the gutters (the outline steps out where the gutters begin)
    sl = [a1, b1]
    for s in kr[1].samples(sb1[1], L, 2.0)[1:]:
        if abs(s - g0) < 1e-6:
            continue
        if s > g0 and sl[-1] != face(1, g0) and all(abs(p[1] - kr[1].pt(g0, -0.95)[1]) > 1e-6 for p in sl[-1:]):
            pass
        sl.append(face(1, s))
    sl = [a1, b1]
    right = [s for s in kr[1].samples(sb1[1], L, 2.0)[1:] if abs(s - g0) > 1e-6]
    for s in right:
        if s > g0 and not any(abs(p[0] - kr[1].pt(g0, -0.95)[0]) < 1e-9 for p in sl):
            sl += [kr[1].pt(g0, -0.25), kr[1].pt(g0, -0.95)]
        sl.append(face(1, s))
    left = [s for s in reversed(kr[-1].samples(sb1[-1], L, 2.0)[1:]) if abs(s - g0) > 1e-6]
    done = False
    for s in left:
        if s < g0 and not done:
            sl += [kr[-1].pt(g0, 0.95), kr[-1].pt(g0, 0.25)]
            done = True
        sl.append(face(-1, s))
    sl = G._clean(sl, 1e-4)
    poly_face(name, sl, SETS["cobble"], world_uv, walls=[((-6.8, 16.0), (6.8, 16.0))])
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, 16, 90, "cobble")
    return _dims()


def _y_at(run, o, y):
    """The s where the run's offset line o reaches height y (runs that climb in y)."""
    a, b = 0.0, run.L
    for _ in range(60):
        m = (a + b) / 2
        if run.pt(m, o)[1] < y:
            a = m
        else:
            b = m
    return (a + b) / 2


def gate_threshold16(M):
    """The avenue's end at a grand gate (the gate line is y = 8; an opening up to 14 wide): setts to a full granite threshold sill
    with a brass drop-bolt socket and a central gate stop; the kerbs end in conical granite guard stones that keep wheels off the
    piers; the gutters drop into cast-iron gratings."""
    name = "GateThreshold16"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(8)
    ke = 6.4
    for sd in (-1, 1):
        blocks(f"Kerb{sd}_", r, 0, ke, kerb_prof(16, sd), [K["gran"], K["grandark"]], 1.6, rng)
        blocks(f"Gut{sd}_", r, 0, 5.4, gutter_prof(sd), [K["gran"], K["grandark"]], 1.0, rng, bevel=0.02, seg=1)
        # the gully grating at the gutter's end (iron, flush) in a granite surround
        x0, x1 = sorted((sd * 6.8, sd * 7.5))
        poly_prism(f"GullySurround{sd}", [(x0, 5.4 + JT / 2), (x1, 5.4 + JT / 2), (x1, 6.4), (x0, 6.4)], 0.0, PT - 0.02, K["grandark"], bevel=0.02)
        for k in range(6):
            y = 5.55 + k * 0.14
            box(f"GullyBar{sd}{k}", (0.56, 0.06, 0.04), ((x0 + x1) / 2, y, PT - 0.005), K["iron"], bevel=0.01)
        # the guard stone: a granite cone with a dressed collar, on the kerb's end
        gx, gy = sd * 7.6, 7.15
        x0, x1 = sorted((sd * 7.0, sd * 8.1))
        poly_prism(f"GuardPad{sd}", [(x0, 6.43), (x1, 6.43), (x1, 7.95), (x0, 7.95)], 0.0, PT, K["grandark"], bevel=0.03)
        lathe(f"Guard{sd}", [(0, 0), (0.45, 0), (0.44, 0.12), (0.37, 0.2), (0.34, 0.85), (0.27, 1.25), (0.15, 1.48), (0.0, 1.53)], K["gran"], seg=18,
              loc=(gx, gy, PT))
        lathe(f"GuardHoop{sd}", [(0.0, 0.8), (0.355, 0.8), (0.37, 0.84), (0.365, 0.92), (0.345, 0.95), (0.0, 0.95)], K["iron"], seg=18, loc=(gx, gy, PT))
    strip(name, r, 0, 6.6, -6.8, 6.8, SETS["cobble"], ends=(True, False))
    # the sill: five granite slabs across the opening, a brass bolt socket and a gate stop in the middle
    xs = [-7.0, -4.2, -1.4, 1.4, 4.2, 7.0]
    for k in range(5):
        q = [(xs[k] + JT / 2, 6.6 + JT / 2), (xs[k + 1] - JT / 2, 6.6 + JT / 2), (xs[k + 1] - JT / 2, 7.95), (xs[k] + JT / 2, 7.95)]
        poly_prism(f"Sill{k}", q, 0.0, PT + 0.04, K["gran"], bevel=0.04)
    for sd in (-1, 1):       # setts' end walls between gutter and sill corners are covered by the gutters; fill beside the sill
        x0, x1 = sorted((sd * 6.8, sd * 7.0))
        poly_prism(f"SillEnd{sd}", [(x0, 6.4), (x1, 6.4), (x1, 7.95), (x0, 7.95)], 0.0, PT, K["grandark"], bevel=0.02)
    cyl("BoltSocket", 0.11, 0.03, (0.9, 7.3, PT + 0.03), K["brass"], verts=16)
    cyl("BoltSocket2", 0.11, 0.03, (-0.9, 7.3, PT + 0.03), K["brass"], verts=16)
    lathe("GateStop", [(0, 0), (0.28, 0), (0.26, 0.1), (0.16, 0.2), (0.0, 0.24)], K["iron"], seg=14, loc=(0.0, 7.5, PT + 0.04))
    PORTS[name] = []
    port(name, 0, 0, -90, "cobble")
    return _dims()


# ================================================================== the roundel (four quarters round a centre)

def roundel_quarter(M):
    """A quarter of the ring round the gate cross: limestone and slate setts laid in rings between radius 8 (the centre's kerb) and
    15.5 (the granite kerb), with half of an 8-wide walk's mouth at each end (ports at (0, -16) and (16, 0); the origin is the ring's
    centre, so four turned copies make the whole ring)."""
    name = "RoundelQuarter"
    K = kit(M)
    rng = rng_for(name)
    r0, r1, r2 = 8.0, 15.5, 16.0
    a_k = math.asin(4.0 / r2)
    # the outer kerb: an arc of blocks from where the south mouth ends to where the east mouth begins (angles measured from +X)
    A0, A1 = -math.pi / 2 + a_k, -a_k
    n = 8
    for i in range(n):
        a, b = A0 + (A1 - A0) * i / n, A0 + (A1 - A0) * (i + 1) / n
        V, F = [], []
        m = 6
        prof = [(r1, 0.0), (r2, 0.0), (r2, KT), (r1 + 0.08, KT), (r1, KT - 0.08)]
        for k in range(m + 1):
            t = a + (b - a) * k / m
            for rr, z in prof:
                V.append((rr * math.cos(t), rr * math.sin(t), z))
        np_ = len(prof)
        for k in range(m):
            for q in range(np_):
                w = (q + 1) % np_
                F.append((k * np_ + q, k * np_ + w, (k + 1) * np_ + w, (k + 1) * np_ + q))
        F.append(tuple(range(np_)))
        F.append(tuple(range(m * np_, (m + 1) * np_)))
        ob = G.mk(f"Kerb{i}", V, F, [K["gran"], K["grandark"]][i % 2], smooth=False)
        G.P_recalc(ob)
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width, md.segments, md.limit_method = 0.035, 2, "ANGLE"
        md.angle_limit = math.radians(30)
    # the mouth kerbs: from the port line to the ring kerb's end face, and the mouth sills (half a mouth each end)
    for rot in (0.0, math.pi / 2):
        ca, sa = math.cos(rot), math.sin(rot)

        def W(x, y):        # south mouth coordinates turned to the east mouth (rot = 90 degrees: (x, y) -> (-y, x)... mirrored to stay in the quarter)
            if rot == 0.0:
                return (x, y)
            return (-y, -x)
        e1 = (r1 * math.cos(A0), r1 * math.sin(A0))
        e2 = (r2 * math.cos(A0), r2 * math.sin(A0))
        yc = -math.sqrt(r1 * r1 - 3.5 * 3.5)
        ys = -r2 + 0.4
        kp = [(3.5, ys), (4.0, ys), e2, e1] + [(r1 * math.cos(t), r1 * math.sin(t)) for t in
                                               [A0 - (A0 - math.atan2(yc, 3.5)) * k / 4 for k in range(1, 5)]]
        poly_prism(f"MouthKerb{int(rot > 0)}", [W(*p) for p in G._clean(kp, 1e-4)], 0.0, KT, K["gran"], bevel=0.035)
        if rot == 0.0:
            stub = Run(0.0, -r2, 90.0).straight(0.4)
            prism("MouthStub0", stub, 0, 0.4, kerb_prof(8, 1), K["gran"], bevel=0.035)
        else:
            stub = Run(r2, 0.0, 180.0).straight(0.4)
            prism("MouthStub1", stub, 0, 0.4, kerb_prof(8, -1), K["gran"], bevel=0.035)
        bed = [(0.0, -r2), (3.5, -r2), (3.5, yc), (0.0, -r1)]
        poly_prism(f"MouthBed{int(rot > 0)}", [W(*p) for p in bed], 0.0, PT - 0.1, K["mortar"])
        sp = [(0.0, -r2 + JT / 2), (3.5 - JT / 2, -r2 + JT / 2)] + [(r1 * math.cos(t), r1 * math.sin(t)) for t in
                                                                   [math.atan2(yc, 3.5) - (math.atan2(yc, 3.5) + math.pi / 2) * k / 8 for k in range(9)]]
        sp = [(min(x, 3.5 - JT / 2), y) for x, y in sp]
        poly_prism(f"MouthSill{int(rot > 0)}", [W(*p) for p in G._clean(sp, 1e-4)], PT - 0.16, PT, K["limel"], bevel=0.03)
    # the setts in rings, stretcher bond (every other ring half a sett on), limestone rings and slate rings in turn
    nr = 8
    wr = (r1 - r0) / nr
    prism_bed = [(r0 * math.cos(t), r0 * math.sin(t)) for t in [-math.pi / 2 + (math.pi / 2) * k / 24 for k in range(25)]]
    prism_bed += [(r1 * math.cos(t), r1 * math.sin(t)) for t in [-(math.pi / 2) * k / 24 for k in range(25)]]
    poly_prism("Bed", prism_bed, 0.0, PT - 0.1, K["mortar"])
    j = 0.035
    for i in range(nr):
        ra, rb = r0 + wr * i, r0 + wr * (i + 1)
        rm = (ra + rb) / 2
        cnt = max(4, round(rm * math.pi / 2 / 0.95))
        da = (math.pi / 2) / cnt
        off = 0.5 if i % 2 else 0.0
        ks = [(-math.pi / 2 + da * (k + off)) for k in range(-1, cnt + 1)]
        mats = [K["slatec"], K["grandark"], K["flagdark"]] if i % 3 == 2 else [K["limel"], K["flag"], K["flagdark"]]
        for k in range(len(ks) - 1):
            t0, t1 = max(ks[k], -math.pi / 2), min(ks[k + 1], 0.0)
            if t1 - t0 < 1e-4:
                continue
            jt0 = j / rm if t0 > -math.pi / 2 + 1e-6 else (JT / 2) / rm
            jt1 = j / rm if t1 < -1e-6 else (JT / 2) / rm
            ri0 = ra + (j if i else JT / 2)
            ri1 = rb - j
            pts = []
            for q in range(4):
                t = t0 + jt0 + (t1 - jt1 - t0 - jt0) * q / 3
                pts.append((ri0 * math.cos(t), ri0 * math.sin(t)))
            for q in range(4):
                t = t1 - jt1 - (t1 - jt1 - t0 - jt0) * q / 3
                pts.append((ri1 * math.cos(t), ri1 * math.sin(t)))
            dz = rng.uniform(-0.02, 0.0)
            slab3(f"Sett{i}_{k}", [(x, y, PT + dz) for x, y in pts], 0.16, mats[int(rng.integers(2))], bevel=0.03)
    PORTS[name] = []
    port(name, 0, -16, -90, "flag")
    port(name, 16, 0, 0, "flag")
    return _dims()


# ================================================================== covered passages: shared helpers

def xz_prism(name, outline, y0, y1, mat, bevel=0.0, seg=1):
    """An outline in the X-Z plane [(x, z)...] extruded along Y from y0 to y1 (concave outlines are fine)."""
    n = len(outline)
    V = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    F = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    ob = G.mk(name, V, F, mat, smooth=False, bevel=0.0, tri=True)
    G.P_recalc(ob)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width, md.segments, md.limit_method = bevel, seg, "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = True
    return ob


def yz_prism(name, outline, x0, x1, mat, bevel=0.0, seg=1):
    """An outline in the Y-Z plane [(y, z)...] extruded along X."""
    n = len(outline)
    V = [(x0, y, z) for y, z in outline] + [(x1, y, z) for y, z in outline]
    F = [tuple(range(n)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    ob = G.mk(name, V, F, mat, smooth=False, bevel=0.0, tri=True)
    G.P_recalc(ob)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width, md.segments, md.limit_method = bevel, seg, "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = True
    return ob


def pointed(cx, half, zs, R, n=10):
    """A two-centred pointed arch from (cx - half, zs) over to (cx + half, zs), radius R (>= half): [(u, z)...] left to right."""
    cl = cx - half + R
    za = zs + math.sqrt(max(R * R - (cx - cl) ** 2, 0.0))
    t0, t1 = math.pi, math.atan2(za - zs, cx - cl)
    left = [(cl + R * math.cos(t0 + (t1 - t0) * k / n), zs + R * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]
    right = [(2 * cx - u, z) for u, z in reversed(left[:-1])]
    return left + right


def arch_z(cx, half, zs, R, u):
    """Height of that pointed arch's intrados above u."""
    d = abs(u - cx)
    cl = half - R
    return zs + math.sqrt(max(R * R - (d - cl) ** 2, 0.0)) if d <= half else zs


def lantern(prefix, K, top, h=1.1, chain=0.6, r=0.3):
    """An iron hanging lantern under `top` (x, y, z): a chain, a hexagonal cage of square bars round a glass (Glass), a candle
    flame (Glow), a crown and a drop finial. Returns its lowest z."""
    x, y, z = top
    for k in range(int(chain / 0.12)):
        zz = z - 0.06 - k * 0.12
        ring_lo(f"{prefix}Link{k}", (x, y, zz), 0.05, "X" if k % 2 else "Y", K["iron"], thick=0.012)
    zt = z - chain
    cone(f"{prefix}Crown", r * 1.15, 0.05, 0.3, (x, y, zt - 0.15), K["iron"], verts=6)
    zb = zt - 0.3 - h * 0.8
    for k in range(6):
        a = k / 6 * 2 * math.pi + math.pi / 6
        tube(f"{prefix}Bar{k}", [(x + math.cos(a) * r, y + math.sin(a) * r, zt - 0.3), (x + math.cos(a) * r, y + math.sin(a) * r, zb)], 0.018,
             K["iron"], square=True, poly=True)
    cyl(f"{prefix}Pan", r * 1.05, 0.06, (x, y, zb - 0.03), K["iron"], verts=6, bevel=0.01)
    cone(f"{prefix}Drop", r * 0.5, 0.0, 0.25, (x, y, zb - 0.185), K["iron"], verts=6)
    g = P.GROUP
    set_group("Glass")
    cyl(f"{prefix}Glass", r * 0.9, h * 0.8 - 0.04, (x, y, (zt - 0.3 + zb) / 2), K["glass"], verts=6, bevel=0.0)
    set_group("Glow")
    cyl(f"{prefix}Candle", 0.07, 0.25, (x, y, zb + 0.16), K["glow"], verts=8, bevel=0.0)
    sphere(f"{prefix}Flame", 0.06, (x, y, zb + 0.35), K["glow"], seg=8, rings=5, scale=(1, 1, 1.8))
    set_group(g)
    return zb - 0.31


def ring_lo(name, c, r, axis, mat, thick=0.03, n=12, seg=4):
    """A low-poly closed ring (axis X: in the YZ plane, Y: XZ, Z: XY)."""
    pts = []
    for k in range(n + 1):
        a = k / n * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        if axis == "X":
            pts.append((c[0], c[1] + u, c[2] + v))
        elif axis == "Z":
            pts.append((c[0] + u, c[1] + v, c[2]))
        else:
            pts.append((c[0] + u, c[1], c[2] + v))
    return sweep(name, pts, thick, mat, seg=seg, caps=False)


def tiled_wall(prop):
    P.TILED[f"{prop}_Wall"] = ("NH_CastleStone", 8.0)


# ================================================================== GateTunnel: a pointed barrel passage through a gate wall

def gate_tunnel(M):
    """A 16-wide, 8-deep stretch of gate wall (both faces ashlar; Wall: the tiled CastleStone) pierced by a pointed barrel vault over
    an 8-wide flag walk (ports at y = 0 and 8): dark voussoirs with a keystone and brass roundel, hood moulds with label stops, a
    battlemented top, two transverse ribs, a boss and a lantern, gate pintles left in the jambs, ivy over one face."""
    name = "GateTunnel"
    K = kit(M)
    rng = rng_for(name)
    zs, R, half, H = 5.5, 6.0, 4.0, 12.4
    r = Run().straight(8.0)
    set_group("Floor")
    lay_run(K, "flag", r, 0, 8, rng, name)
    set_group("Main")
    arch = pointed(0, half, zs, R, 12)
    set_group("Wall")
    xz_prism("PierL", [(-8, 0), (-4, 0), (-4, zs), (-8, zs)], 0, 8, K["wall"])
    xz_prism("PierR", [(4, 0), (8, 0), (8, zs), (4, zs)], 0, 8, K["wall"])
    head = [(-8, zs), (-4, zs)] + arch[1:-1] + [(4, zs), (8, zs), (8, H), (-8, H)]
    xz_prism("Head", head, 0, 8, K["wall"])
    set_group("Main")
    for y0, y1 in ((-0.22, 0.0), (8.0, 8.22)):
        for sd in (-1, 1):
            x0, x1 = sorted((sd * 4.0, sd * 8.0))
            box(f"Plinth{y0}{sd}", (x1 - x0 - 0.02, y1 - y0, 0.8), ((x0 + x1) / 2, (y0 + y1) / 2, 0.85), K["stonedark"], bevel=0.05)
        box(f"String{y0}", (16.0, y1 - y0, 0.35), (0, (y0 + y1) / 2, H - 1.2), K["stonedark"], bevel=0.05)
    box("Coping", (16.3, 8.6, 0.3), (0, 4, H + 0.15), K["stonedark"], bevel=0.05)
    for k in range(8):
        x = -7.0 + k * 2.0
        for y in (0.65, 7.35):
            box(f"Merlon{k}{y}", (1.2, 1.2, 1.25), (x, y, H + 0.3 + 0.625), K["stone"], bevel=0.06)
            box(f"MerlonCap{k}{y}", (1.34, 1.34, 0.16), (x, y, H + 0.3 + 1.33), K["stonedark"], bevel=0.04)
    nv = 15
    for face, y0, y1 in (("F", -0.16, 0.0), ("B", 8.0, 8.16)):
        ext = pointed(0, half + 0.95, zs, R + 0.95, 30)
        intr = pointed(0, half, zs, R, 30)
        for k in range(nv):
            if k == nv // 2:
                continue
            a, b = round(k * 60 / nv), round((k + 1) * 60 / nv)
            seg_ = intr[a:b + 1] + list(reversed(ext[a:b + 1]))
            xz_prism(f"Vous{face}{k}", seg_, y0, y1, K["stonedark"] if k % 2 else K["stone"], bevel=0.03)
        ka, kb = round((nv // 2) * 60 / nv), round((nv // 2 + 1) * 60 / nv)
        key = intr[ka:kb + 1] + list(reversed(pointed(0, half + 1.3, zs, R + 1.3, 30)[ka:kb + 1]))
        yk0, yk1 = (y0 - 0.14, y1) if face == "F" else (y0, y1 + 0.14)
        xz_prism(f"Key{face}", key, yk0, yk1, K["stone"], bevel=0.04)
        zk = arch_z(0, half, zs, R, 0) + 0.65
        yy = yk0 - 0.02 if face == "F" else yk1 + 0.02
        cyl(f"KeyDisc{face}", 0.32, 0.06, (0, yy, zk), K["brass"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
        hood = pointed(0, half + 1.35, zs, R + 1.35, 24)
        yh = y0 - 0.12 if face == "F" else y1 + 0.12
        sweep(f"Hood{face}", [(u, yh, z) for u, z in hood], 0.13, K["stonedark"], seg=6)
        for u, z in (hood[0], hood[-1]):
            box(f"Stop{face}{u}", (0.42, 0.3, 0.42), (u, yh, z - 0.18), K["stone"], bevel=0.06)
    for k, yr in enumerate((2.6, 5.4)):
        rib_o = pointed(0, half, zs, R, 24)
        rib_i = pointed(0, half - 0.22, zs, R - 0.22, 24)
        xz_prism(f"Rib{k}", rib_o + list(reversed(rib_i)), yr - 0.22, yr + 0.22, K["stonedark"], bevel=0.04)
    zap = arch_z(0, half, zs, R, 0)
    sphere("Boss", 0.42, (0, 4.0, zap - 0.1), K["stonedark"], seg=14, rings=8, scale=(1, 1, 0.7))
    lantern("Lamp", K, (0, 4.0, zap - 0.35), h=1.0, chain=0.55)
    for sd in (-1, 1):
        for z in (1.2, 4.0):
            box(f"Pintle{sd}{z}", (0.16, 0.16, 0.28), (sd * 3.96, 1.0, z), K["iron"], bevel=0.02)
        box(f"Keep{sd}", (0.08, 0.36, 0.36), (sd * 3.97, 7.2, 2.6), K["iron"], bevel=0.02)
    cards = G.Cards(rng)
    for k in range(130):
        x = rng.uniform(-7.9, -4.7)
        z = rng.uniform(1.8, H - 0.4) if rng.random() < 0.8 else rng.uniform(1.4, 3)
        if x > -6.0 and z < 9.5 and rng.random() < 0.6:
            continue
        p = Vector((x, -0.08 - rng.uniform(0.0, 0.08), z))
        ax, ay = G.frame((0, -1, 0), roll=rng.uniform(0, 6.28))
        sz = rng.uniform(0.45, 0.8)
        cards.add(p, ax, ay, sz, sz, "ivy", "fill", nrm=lambda q, fn: Vector((0, -1, 0.25)))
    cards.build("Leaves")
    P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"
    tiled_wall(name)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, 8, 90, "flag")
    CLEAR[name] = (-3.4, 3.4, 0.0, 8.0)
    return _dims()


# ================================================================== RosePergola: pierced iron arches and climbing roses

def rose_pergola(M):
    """An 8-long walk-over module for an 8-wide walk (tiles end to end: its rails end flush on y = 0 and 8): two pointed arches of
    doubled square iron bars with foiled tracery between them (y = 2 and 6, so a run has an arch every 4), diamond trellis sides,
    rails along the springing and the crown, brass rose bosses, crimson climbing roses and a lantern at the crown."""
    name = "RosePergola"
    K = kit(M)
    rng = rng_for(name)
    xp, zs, R = 4.45, 5.8, 6.0
    for ya in (2.0, 6.0):
        for sd in (-1, 1):
            box(f"Foot{ya}{sd}", (0.7, 0.7, 0.35), (sd * xp, ya, 0.175), K["lime"], bevel=0.05)
            tube(f"Post{ya}{sd}", [(sd * xp, ya, 0.35), (sd * xp, ya, zs)], 0.075, K["iron"], square=True, poly=True)
            tube(f"PostIn{ya}{sd}", [(sd * (xp - 0.32), ya, 0.35), (sd * (xp - 0.32), ya, zs)], 0.045, K["iron"], square=True, poly=True)
            for q in range(8):
                z = 0.9 + (zs - 1.3) * q / 7
                tube(f"Ladder{ya}{sd}{q}", [(sd * xp, ya, z), (sd * (xp - 0.32), ya, z)], 0.03, K["iron"], square=True, poly=True)
        outer = pointed(0, xp, zs, R, 16)
        inner = pointed(0, xp - 0.32, zs, R - 0.32, 16)
        tube(f"ArchO{ya}", [(u, ya, z) for u, z in outer], 0.07, K["iron"], square=True, poly=True)
        tube(f"ArchI{ya}", [(u, ya, z) for u, z in inner], 0.045, K["iron"], square=True, poly=True)
        for k in range(2, 31, 4):
            if k in (14, 18):
                continue
            po, pi = outer[k], inner[k]
            c = ((po[0] + pi[0]) / 2, (po[1] + pi[1]) / 2)
            for q in range(4):
                a = q * math.pi / 2 + math.pi / 4
                ring_lo(f"Foil{ya}{k}{q}", (c[0] + math.cos(a) * 0.065, ya, c[1] + math.sin(a) * 0.065), 0.065, "Y", K["iron"], thick=0.012)
        za = arch_z(0, xp, zs, R, 0)
        sphere(f"Boss{ya}", 0.17, (0, ya, za), K["brass"], seg=12, rings=6)
        for q in range(5):
            a = q / 5 * 2 * math.pi
            for yy in (ya - 0.08, ya + 0.08):
                sphere(f"Petal{ya}{q}{yy}", 0.1, (math.cos(a) * 0.15, yy, za + math.sin(a) * 0.15), K["brass"], seg=8, rings=4, scale=(1, 0.5, 1))
        cone(f"Finial{ya}", 0.08, 0.0, 0.45, (0, ya, za + 0.34), K["iron"], verts=4)
    za = arch_z(0, xp, zs, R, 0)
    for sd in (-1, 1):
        for z in (0.9, zs - 0.4):
            tube(f"SideRail{sd}{z}", [(sd * xp, 0.0, z), (sd * xp, 8.0, z)], 0.04, K["iron"], square=True, poly=True)
        u = sd * 2.6
        tube(f"Purlin{sd}", [(u, 0.0, arch_z(0, xp, zs, R, u)), (u, 8.0, arch_z(0, xp, zs, R, u))], 0.045, K["iron"], square=True, poly=True)
        tube(f"Eave{sd}", [(sd * xp, 0.0, zs), (sd * xp, 8.0, zs)], 0.06, K["iron"], square=True, poly=True)
        # the diamond trellis: bars at 45 degrees, clipped to the module (so a run's lattice continues)
        dz = zs - 1.3
        for k in range(-6, 15):
            y0 = k * 1.0
            for dirn in (1, -1):
                ya_, yb_ = y0, y0 + dirn * dz
                lo, hi = min(ya_, yb_), max(ya_, yb_)
                if hi <= 0.0 or lo >= 8.0:
                    continue
                t0 = (max(lo, 0.0) - ya_) / (yb_ - ya_)
                t1 = (min(hi, 8.0) - ya_) / (yb_ - ya_)
                t0, t1 = min(t0, t1), max(t0, t1)
                pa = (sd * (xp + 0.04), ya_ + (yb_ - ya_) * t0, 0.9 + dz * t0)
                pb = (sd * (xp + 0.04), ya_ + (yb_ - ya_) * t1, 0.9 + dz * t1)
                if abs(pa[1] - pb[1]) > 0.05:
                    tube(f"Lat{sd}{k}{dirn}", [pa, pb], 0.022, K["iron"], square=True, poly=True)
    tube("Ridge", [(0, 0.0, za + 0.1), (0, 8.0, za + 0.1)], 0.05, K["iron"], square=True, poly=True)
    lantern("Lamp", K, (0, 4.0, za + 0.05), h=0.9, chain=0.5, r=0.26)
    cards = G.Cards(rng)
    for ya in (2.0, 6.0):
        for sd in (-1, 1):
            pts = []
            for k in range(30):
                t = k / 29
                a = t * 7 + sd
                pts.append((sd * (xp - 0.16) + math.cos(a) * 0.24, ya + math.sin(a) * 0.24, 0.3 + t * (zs + 0.8)))
            sweep(f"Stem{ya}{sd}", pts, 0.035, K["stem"], seg=5)
            for k in range(16):
                z = rng.uniform(1.0, zs + 0.8)
                cards.blob((sd * (xp - 0.05), ya, z), (0.45, 0.45, 0.5), 3, "rose_leaves", 0.7, keep=lambda p: abs(p.x) > 3.9)
            for k in range(5):
                z = rng.uniform(2.0, zs)
                cards.blob((sd * (xp - 0.0), ya, z), (0.35, 0.35, 0.3), 1, "rose_crimson", 0.45, keep=lambda p: abs(p.x) > 3.9)
    for k in range(60):
        y = rng.uniform(0.3, 7.7)
        u = rng.uniform(-3.0, 3.0)
        z = arch_z(0, xp, zs, R, u) + rng.uniform(0.2, 0.55)
        cards.blob((u, y, z), (0.35, 0.35, 0.2), 2, "rose_leaves" if rng.random() < 0.75 else "rose_crimson", 0.6,
                   keep=lambda p: p.z > arch_z(0, xp, zs, R, max(-xp, min(xp, p.x))) + 0.1 and 0.05 < p.y < 7.95)
    cards.build("Leaves")
    P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"
    PORTS[name] = []
    CLEAR[name] = (-3.4, 3.4, 0.0, 8.0)
    return _dims()


# ================================================================== ColonnadeBay: a covered walk with coupled columns

def colonnade_bay(M):
    """One 8-long bay of a covered walk over its own 8-wide flag floor (ports at y = 0 and 8): clustered columns with brass annulets
    on a stylobate at y = 0.6 and 7.4 each side (bays set end to end give coupled columns), pointed arcades with quatrefoil tympana
    (Wall: tiled CastleStone), a pointed barrel vault painted deep crimson and set with gilt stars, ribs, a gilt boss and lantern,
    and a flat leaded roof behind a parapet pierced with quatrefoils."""
    name = "ColonnadeBay"
    K = kit(M)
    rng = rng_for(name)
    r = Run().straight(8.0)
    set_group("Floor")
    lay_run(K, "flag", r, 0, 8, rng, name)
    set_group("Main")
    zst = 0.35
    vault = material("VaultCrimson", "NH_PaintedMetal", tint=(0.2, 0.025, 0.035), scale=0.8, metal=0.0, rough_add=0.35, wear=0.3, dirt=1.0)
    gilt = K["brassf"]
    xc, zcap = 5.0, 6.3
    for sd in (-1, 1):
        x0, x1 = sorted((sd * 4.0, sd * 6.2))
        poly_prism(f"Stylobate{sd}", [(x0, 0.0), (x1, 0.0), (x1, 8.0), (x0, 8.0)], 0.0, zst, K["stonedark"], bevel=0.04)
        for yc in (0.6, 7.4):
            box(f"Plinth{sd}{yc}", (1.1, 1.1, 0.4), (sd * xc, yc, zst + 0.2), K["stone"], bevel=0.05)
            lathe(f"Base{sd}{yc}", [(0, 0), (0.52, 0), (0.52, 0.08), (0.44, 0.16), (0.47, 0.24), (0.38, 0.3), (0.0, 0.3)], K["stone"], seg=20,
                  loc=(sd * xc, yc, zst + 0.4))
            cyl(f"Core{sd}{yc}", 0.3, zcap - zst - 0.7, (sd * xc, yc, (zst + 0.7 + zcap) / 2), K["stone"], verts=16)
            for q in range(4):
                a = q * math.pi / 2 + math.pi / 4
                cyl(f"Shaft{sd}{yc}{q}", 0.14, zcap - zst - 0.7, (sd * xc + math.cos(a) * 0.3, yc + math.sin(a) * 0.3, (zst + 0.7 + zcap) / 2),
                    K["stonedark"], verts=10)
            for q in range(2):
                hz = zst + 1.8 + q * 2.6
                lathe(f"Ring{sd}{yc}{q}", [(0, 0), (0.48, 0), (0.5, 0.05), (0.48, 0.1), (0, 0.1)], K["brass"], seg=20, loc=(sd * xc, yc, hz))
            lathe(f"Cap{sd}{yc}", [(0, 0), (0.42, 0), (0.5, 0.2), (0.62, 0.42), (0.72, 0.5), (0.72, 0.62), (0, 0.62)], K["stone"], seg=8,
                  loc=(sd * xc, yc, zcap))
    zs = zcap + 0.62
    zt = 11.6
    ah, aR = 3.4 - 0.62, 4.2
    set_group("Wall")
    for sd in (-1, 1):
        x0, x1 = sorted((sd * 4.6, sd * 5.4))
        arc = pointed(4.0, ah, zs, aR, 14)
        outline = [(0.0, zs), (4.0 - ah, zs)] + arc[1:-1] + [(4.0 + ah, zs), (8.0, zs), (8.0, zt), (0.0, zt)]
        yz_prism(f"Spandrel{sd}", outline, x0, x1, K["wall"])
        zt0 = zs + 0.9
        arc2 = [p for p in pointed(4.0, ah, zs, aR, 14) if p[1] >= zt0]
        tymp = [(arc2[0][0], zt0)] + arc2 + [(arc2[-1][0], zt0)]
        xm0, xm1 = sorted((sd * 4.85, sd * 5.15))
        yz_prism(f"Tympanum{sd}", tymp, xm0, xm1, K["wall"])
    set_group("Main")
    for sd in (-1, 1):
        arc = pointed(4.0, ah, zs, aR, 18)
        for xf in (sd * 4.58, sd * 5.42):
            sweep(f"ArchMould{sd}{xf}", [(xf, u, z) for u, z in arc], 0.1, K["stonedark"], seg=6)
        for xf in (sd * 4.83, sd * 5.17):
            zq = zs + 2.6
            for q in range(4):
                a = q * math.pi / 2
                ring_lo(f"Quatre{sd}{xf}{q}", (xf, 4.0 + math.cos(a) * 0.38, zq + math.sin(a) * 0.38), 0.38, "X", K["stonedark"], thick=0.06)
        box(f"String{sd}", (0.95, 8.0, 0.3), (sd * 5.0, 4.0, zt - 0.6), K["stonedark"], bevel=0.04)
    vR, vh, vs = 5.6, 4.6, 7.0
    intr = pointed(0, vh, vs, vR, 20)
    outline = [(-4.6, zt), (-4.6, vs)] + intr[1:-1] + [(4.6, vs), (4.6, zt)]
    xz_prism("VaultMass", outline, 0.0, 8.0, vault)
    for k, yr in enumerate((0.6, 7.4)):
        o = pointed(0, vh, vs, vR, 20)
        i_ = pointed(0, vh - 0.2, vs, vR - 0.2, 20)
        xz_prism(f"TRib{k}", o + list(reversed(i_)), yr - 0.25, yr + 0.25, K["stone"], bevel=0.03)
    zap = arch_z(0, vh, vs, vR, 0)
    box("RidgeRib", (0.34, 8.0, 0.22), (0, 4.0, zap - 0.1), K["stone"], bevel=0.03)
    sphere("Boss", 0.34, (0, 4.0, zap - 0.2), gilt, seg=14, rings=8, scale=(1, 1, 0.6))
    lantern("Lamp", K, (0, 4.0, zap - 0.4), h=0.95, chain=0.45)
    for i in range(7):
        for k in range(1, 9):
            u = -4.2 + 8.4 * k / 9 + (0.45 if i % 2 else 0.0)
            if abs(u) > 4.3 or abs(u) < 0.3:
                continue
            y = 1.0 + 6.0 * i / 6
            z = arch_z(0, vh, vs, vR, u) - 0.012
            sphere(f"Star{i}{k}", 0.07, (u, y, z), gilt, seg=6, rings=3, scale=(1, 1, 0.4))
    box("Roof", (12.4, 8.0, 0.4), (0, 4.0, zt + 0.2), K["slate"], bevel=0.0)
    for sd in (-1, 1):
        box(f"Cornice{sd}", (0.5, 8.0, 0.35), (sd * 6.05, 4.0, zt + 0.1), K["stonedark"], bevel=0.0)
        for k in range(4):
            yc = 1.0 + 2.0 * k
            yz_prism(f"Parapet{sd}{k}", [(yc - 1.0, zt + 0.4), (yc + 1.0, zt + 0.4), (yc + 1.0, zt + 1.6), (yc - 1.0, zt + 1.6)],
                     *sorted((sd * 5.7, sd * 6.1)), K["stone"], bevel=0.0)
            for q in range(4):
                a = q * math.pi / 2
                ring_lo(f"PQ{sd}{k}{q}", (sd * 6.12, yc + math.cos(a) * 0.2, zt + 1.0 + math.sin(a) * 0.2), 0.2, "X", K["stonedark"], thick=0.04)
        box(f"ParCap{sd}", (0.55, 8.0, 0.16), (sd * 5.9, 4.0, zt + 1.68), K["stonedark"], bevel=0.0)
    tiled_wall(name)
    PORTS[name] = []
    port(name, 0, 0, -90, "flag")
    port(name, 0, 8, 90, "flag")
    CLEAR[name] = (-3.4, 3.4, 0.0, 8.0)
    return _dims()


# ================================================================== LychPassage: a roofed resting passage

def lych_passage(M):
    """A roofed stone passage over an 8-wide walk, 8 long (batch 51's GateLych is the iron-and-slate lychgate with leaves; this is its
    stone cousin without any): four rubble piers with ashlar quoins, low side screens of stone colonnettes with iron quatrefoil
    grilles, four-centred arched lintels front and back (the front one carved with a winged hourglass), a hipped roof of stone slates
    in diminishing courses with lead hip rolls and ball finials, a lantern from the ridge."""
    name = "LychPassage"
    K = kit(M)
    rng = rng_for(name)
    xp, yps, hp = 4.75, (0.6, 7.4), 7.6
    rough = K["stonedark"]
    for sd in (-1, 1):
        for yp in yps:
            box(f"PierFoot{sd}{yp}", (1.25, 1.25, 0.5), (sd * xp, yp, 0.25), K["stonedark"], bevel=0.05)
            box(f"Pier{sd}{yp}", (1.0, 1.0, hp - 0.5), (sd * xp, yp, 0.5 + (hp - 0.5) / 2), K["wall"], bevel=0.04)
            for k in range(6):          # ashlar quoins, alternating long and short
                z = 0.7 + k * 1.1
                lx, ly = (1.08, 0.7) if k % 2 == 0 else (0.7, 1.08)
                box(f"Quoin{sd}{yp}{k}", (lx, ly, 0.5), (sd * xp + sd * (0.54 - lx / 2), yp + (0.54 - ly / 2) * (1 if yp < 4 else -1), z + 0.25),
                    K["stone"], bevel=0.04)
            box(f"PierCap{sd}{yp}", (1.2, 1.2, 0.3), (sd * xp, yp, hp + 0.15), K["stone"], bevel=0.05)
    # the side screens between the piers: a plinth, three colonnettes, iron quatrefoil grilles, a coping rail
    for sd in (-1, 1):
        y0, y1 = yps[0] + 0.5, yps[1] - 0.5
        poly_prism(f"ScreenPlinth{sd}", [(sd * 4.35, y0), (sd * 5.15, y0), (sd * 5.15, y1), (sd * 4.35, y1)], 0.0, 0.8, K["stone"], bevel=0.04)
        box(f"ScreenRail{sd}", (0.8, y1 - y0, 0.3), (sd * 4.75, 4.0, 2.75), K["stone"], bevel=0.04)
        for k in range(4):
            yc = y0 + (y1 - y0) * k / 3
            if k in (0, 3):
                continue
            cyl(f"Colonnette{sd}{k}", 0.13, 1.8, (sd * 4.75, yc, 1.7), K["stone"], verts=10)
        for k in range(3):
            ya, yb = y0 + (y1 - y0) * k / 3, y0 + (y1 - y0) * (k + 1) / 3
            yc = (ya + yb) / 2
            tube(f"GrilleF{sd}{k}", [(sd * 4.75, ya + 0.16, 0.85), (sd * 4.75, yb - 0.16, 0.85), (sd * 4.75, yb - 0.16, 2.55),
                                     (sd * 4.75, ya + 0.16, 2.55)], 0.03, K["iron"], closed=True, square=True, poly=True)
            for q in range(4):
                a = q * math.pi / 2
                ring_lo(f"GrilleQ{sd}{k}{q}", (sd * 4.75, yc + math.cos(a) * 0.3, 1.7 + math.sin(a) * 0.3), 0.3, "X", K["iron"], thick=0.025)
            ring_lo(f"GrilleR{sd}{k}", (sd * 4.75, yc, 1.7), 0.72, "X", K["iron"], thick=0.03, n=16)
    # side beams over the piers, arched lintels across the ends
    for sd in (-1, 1):
        box(f"Beam{sd}", (0.9, 7.8, 0.8), (sd * xp, 4.0, hp + 1.0), K["stone"], bevel=0.04)
    for k, yl in enumerate((yps[0], yps[1])):
        # a four-centred arch: quarter circles of 1.5 at the haunches, a flat-pitched centre, from x = +-4.25 at 7.4
        u0, zs_ = 4.25, 7.2
        pts = []
        for q in range(9):
            a = math.pi * q / 16
            pts.append((-u0 + 1.4 - 1.4 * math.cos(a), zs_ + 1.4 * math.sin(a) * 0.75))
        xa, za = pts[-1]
        pts += [(xa + (0 - xa) * t, za + (8.45 - za) * t) for t in (0.5, 1.0)]
        under = pts + [(-u, z) for u, z in reversed(pts[:-1])]
        outline = [(-u0 - 0.2, hp + 1.4), (-u0 - 0.2, zs_)] + under + [(u0 + 0.2, zs_), (u0 + 0.2, hp + 1.4)]
        xz_prism(f"Lintel{k}", outline, yl - 0.4, yl + 0.4, K["stone"], bevel=0.04)
    # the winged hourglass on the front lintel's face (y = 0.2)
    yf = yps[0] - 0.4 - 0.05
    zc = 8.72
    cone("GlassTop", 0.14, 0.02, 0.2, (0, yf, zc + 0.1), K["brass"], rot=(math.pi, 0, 0), verts=12)
    cone("GlassBot", 0.14, 0.02, 0.2, (0, yf, zc - 0.1), K["brass"], verts=12)
    for zz in (zc + 0.215, zc - 0.215):
        box(f"GlassPlate{zz}", (0.36, 0.1, 0.03), (0, yf, zz), K["brass"], bevel=0.008)
    for sd in (-1, 1):
        feathers = []
        for q in range(5):
            L = 0.3 + q * 0.07
            a = math.radians(10 + q * 12)
            x0_ = sd * 0.2
            feathers.append([(x0_, zc + 0.05 - q * 0.04), (x0_ + sd * L * math.cos(a), zc + 0.05 + L * math.sin(a) - q * 0.05),
                             (x0_ + sd * (L - 0.12) * math.cos(a), zc - 0.06 + (L - 0.12) * math.sin(a) - q * 0.05)])
        for q, fpts in enumerate(feathers):
            xz_prism(f"Wing{sd}{q}", fpts if sd > 0 else fpts[::-1], yf - 0.04, yf + 0.06, K["stone"], bevel=0.0)
    # the hipped roof: stone slates in diminishing courses; eaves at 9.1 over x +-5.7, y -0.5..8.5, a short ridge at 12.6
    ez, rz_ = hp + 1.4, 12.9
    ex, ey0, ey1 = 5.75, -0.55, 8.55
    rx, ry0, ry1 = 0.0, 2.7, 5.3
    nc = 10
    for c in range(nc):
        t0, t1 = c / nc, (c + 1) / nc

        def ring(t):
            return (ex + (rx - ex) * t, ey0 + (ry0 - ey0) * t, ey1 + (ry1 - ey1) * t, ez + (rz_ - ez) * t)
        a0, b0 = ring(t0), ring(min(1.0, t1 + 0.04))
        lift = 0.1
        for side in range(4):
            if side == 0:      # +x slope
                q = [(a0[0], a0[1], a0[3]), (a0[0], a0[2], a0[3]), (b0[0], b0[2], b0[3]), (b0[0], b0[1], b0[3])]
            elif side == 1:
                q = [(-a0[0], a0[2], a0[3]), (-a0[0], a0[1], a0[3]), (-b0[0], b0[1], b0[3]), (-b0[0], b0[2], b0[3])]
            elif side == 2:    # +y end
                q = [(a0[0], a0[2], a0[3]), (-a0[0], a0[2], a0[3]), (-b0[0], b0[2], b0[3]), (b0[0], b0[2], b0[3])]
            else:
                q = [(-a0[0], a0[1], a0[3]), (a0[0], a0[1], a0[3]), (b0[0], b0[1], b0[3]), (-b0[0], b0[1], b0[3])]
            # a course is a thick wedge: its tail lifted by `lift`
            V = [(x, y, z) for x, y, z in q] + [(x, y, z + (lift if k < 2 else 0.04)) for k, (x, y, z) in enumerate(q)]
            F = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            if abs(b0[0] - rx) < 1e-6 and side in (2, 3):
                pass
            ob = G.mk(f"Slates{c}{side}", V, F, [K["slatec"], K["stonedark"], K["slatec"]][(c + side) % 3], smooth=False, tri=True)
            G.P_recalc(ob)
    # a solid core under the courses (so nothing shows through the joints), lead hip rolls, the ridge, ball finials
    core = [(ex, ey0, ez), (ex, ey1, ez), (-ex, ey1, ez), (-ex, ey0, ez), (rx, ry0, rz_), (rx, ry1, rz_)]
    ob = G.mk("RoofCore", core, [(0, 1, 2, 3)[::-1], (0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)], K["slate"], smooth=False, tri=True)
    G.P_recalc(ob)
    lead = flat("Lead", (0.1, 0.105, 0.11), 0.45, metal=0.6, wear=0.2, dirt=0.8)
    for (p, q) in (((ex, ey0, ez), (rx, ry0, rz_)), ((-ex, ey0, ez), (rx, ry0, rz_)), ((ex, ey1, ez), (rx, ry1, rz_)), ((-ex, ey1, ez), (rx, ry1, rz_)),
                   ((rx, ry0, rz_), (rx, ry1, rz_))):
        pv, qv = Vector(p), Vector(q)
        d = (qv - pv).normalized()
        sweep(f"Hip{p}{q}", [tuple(pv + Vector((0, 0, 0.12))), tuple(qv + Vector((0, 0, 0.12)))], 0.09, lead, seg=8)
    for yy in (ry0, ry1):
        lathe(f"Ball{yy}", [(0, 0), (0.18, 0), (0.12, 0.12), (0.2, 0.2), (0.3, 0.38), (0.2, 0.6), (0, 0.65)], K["stone"], seg=14, loc=(0, yy, rz_ + 0.12))
    # the underside: a stone ceiling slab at the eaves level, the lantern from it
    poly_prism("Ceiling", [(-ex + 0.3, ey0 + 0.3), (ex - 0.3, ey0 + 0.3), (ex - 0.3, ey1 - 0.3), (-ex + 0.3, ey1 - 0.3)], hp + 1.4, hp + 1.5, K["stonedark"])
    lantern("Lamp", K, (0, 4.0, hp + 1.4), h=0.8, chain=0.25, r=0.25)
    PORTS[name] = []
    CLEAR[name] = (-3.4, 3.4, 0.0, 8.0)
    return _dims()


# ================================================================== YewTunnel: a clipped yew passage

def yew_tunnel(M):
    """An 8-long clipped yew passage over an 8-wide walk: a thick yew mass with a round-headed opening, its top clipped into
    battlements, yew orbs on the front corners and a clipped spire over the crown; an old iron arch frame half swallowed by the yew
    at both ends, a lantern hanging between. Leaves: alpha cards over the clipped core (NH_GardenLeaves)."""
    name = "YewTunnel"
    K = kit(M)
    rng = rng_for(name)
    xi, xo, zs, H = 4.15, 6.6, 5.9, 10.2
    rr = xi
    arch = [(xi * math.cos(math.pi * k / 18), zs + rr * math.sin(math.pi * k / 18)) for k in range(19)]   # right to left
    merl = []
    n = 7
    for k in range(n):
        xa = xo - (2 * xo) * k / n
        xb = xo - (2 * xo) * (k + 1) / n
        zz = H + 1.1 if k % 2 == 0 else H
        merl += [(xa, zz), (xb, zz)]
    outline = [(xi, 0.0), (xo, 0.0)] + merl + [(-xo, 0.0), (-xi, 0.0), (-xi, zs)] + arch[1:-1][::-1] + [(xi, zs)]
    outline = G._clean(outline, 1e-4)
    core = K["core"]
    xz_prism("Yew", outline, 0.2, 7.8, core, bevel=0.3, seg=2)
    for sd in (-1, 1):
        sphere(f"Orb{sd}", 0.85, (sd * (xo - 0.85), 1.0, H + 1.1 + 0.75), core, seg=16, rings=10)
    lathe("Spire", [(0, 0), (1.1, 0), (1.15, 0.4), (0.8, 0.9), (0.55, 2.2), (0.25, 3.0), (0.0, 3.4)], core, seg=16, loc=(0, 4.0, H + 1.1 - 0.05))
    for yf in (0.12, 7.88):
        pts = [(xi - 0.12, yf, 0.0), (xi - 0.12, yf, zs)] + [((xi - 0.12) * math.cos(math.pi * k / 18), yf, zs + (rr - 0.12) * math.sin(math.pi * k / 18))
                                                           for k in range(1, 18)] + [(-(xi - 0.12), yf, zs), (-(xi - 0.12), yf, 0.0)]
        tube(f"Frame{yf}", pts, 0.07, K["iron"], square=True, poly=True)
        for sd in (-1, 1):
            box(f"FrameFoot{yf}{sd}", (0.3, 0.3, 0.12), (sd * (xi - 0.12), yf, 0.06), K["iron"], bevel=0.02)
        ring_lo(f"FrameRose{yf}", (0, yf, zs + rr - 0.55), 0.3, "Y", K["iron"], thick=0.03)
    lantern("Lamp", K, (0, 4.0, zs + rr - 0.02), h=0.85, chain=0.35, r=0.25)
    cards = G.Cards(rng)
    bpy.context.view_layer.update()

    def keep(p, nn):       # no cards on the opening's jambs and soffit (the clipped core shows there), so none hang into the walk
        m = 0.35
        return not (abs(p.x) < xi + m and (p.z < zs + 0.01 or math.hypot(p.x, p.z - zs) < rr + m) and -0.3 < p.y < 8.3)
    for o in [o for o in P.PARTS if o.name.startswith(("Yew", "Orb", "Spire"))]:
        cards.cover(o, 2.6, "yew", 0.95, offset=0.06, tilt=0.3, zmin=0.1, keep=keep)
    cards.build("Leaves")
    P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"
    PORTS[name] = []
    CLEAR[name] = (-3.4, 3.4, 0.0, 8.0)
    return _dims()


# ================================================================== RoundelCentre: the island and its lantern cross

def roundel_centre(M):
    """The island in the middle of the four RoundelQuarters (radius 8, origin at the ring's centre): a granite kerb, a mossy turf,
    a three-stepped octagonal calvary carrying a tall chamfered shaft and a stone lantern head with a candle (Glow) behind glass
    (Glass) under four pointed gables and pinnacles, an iron cross finial; eight spear-headed iron bollards slung with chains."""
    name = "RoundelCentre"
    K = kit(M)
    rng = rng_for(name)
    n = 12
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        V, F = [], []
        prof = [(7.5, 0.0), (8.0, 0.0), (8.0, KT - 0.08), (7.92, KT), (7.5, KT)]
        m = 8
        for k in range(m + 1):
            t = a + (b - a) * k / m
            for rr_, z in prof:
                V.append((rr_ * math.cos(t), rr_ * math.sin(t), z))
        npf = len(prof)
        for k in range(m):
            for q in range(npf):
                w = (q + 1) % npf
                F.append((k * npf + q, k * npf + w, (k + 1) * npf + w, (k + 1) * npf + q))
        F += [tuple(range(npf)), tuple(range(m * npf, (m + 1) * npf))]
        ob = G.mk(f"Kerb{i}", V, F, [K["gran"], K["grandark"]][i % 2], smooth=False)
        G.P_recalc(ob)
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width, md.segments, md.limit_method = 0.035, 2, "ANGLE"
        md.angle_limit = math.radians(30)
    lathe("Turf", [(0, 0), (7.5, 0.0), (7.5, 0.34), (6.0, 0.42), (3.0, 0.48), (0, 0.5)], K["moss2"], seg=48)
    z = 0.3
    for k, (rad, hh) in enumerate(((3.7, 0.45), (3.0, 0.45), (2.3, 0.45))):
        lathe(f"Step{k}", [(0, 0), (rad, 0), (rad, hh - 0.06), (rad - 0.06, hh), (0, hh)], K["lime"] if k != 1 else K["limel"], seg=8, loc=(0, 0, z))
        z += hh
    lathe("ShaftBase", [(0, 0), (0.95, 0), (0.95, 0.3), (0.75, 0.45), (0.62, 0.6), (0, 0.6)], K["stone"], seg=8, loc=(0, 0, z))
    z += 0.6
    lathe("Shaft", [(0, 0), (0.55, 0), (0.42, 6.0), (0, 6.0)], K["stone"], seg=8, loc=(0, 0, z))
    for q in range(2):
        rq = 0.55 - (0.13 * (2.0 + q * 2.4) / 6.0)
        lathe(f"Collar{q}", [(0, 0), (rq + 0.05, 0), (rq + 0.09, 0.08), (rq + 0.05, 0.16), (0, 0.16)], K["stonedark"], seg=8, loc=(0, 0, z + 2.0 + q * 2.4))
    z += 6.0
    lathe("Capital", [(0, 0), (0.45, 0), (0.7, 0.3), (0.95, 0.45), (0.95, 0.6), (0, 0.6)], K["stone"], seg=8, loc=(0, 0, z))
    z += 0.6
    hw, hh = 0.75, 1.6
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * (hw - 0.13), sy * (hw - 0.13)
            box(f"HeadPier{sx}{sy}", (0.26, 0.26, hh), (px, py, z + hh / 2), K["stone"], bevel=0.03)
            box(f"PinBase{sx}{sy}", (0.3, 0.3, 0.6), (px, py, z + hh + 0.3), K["stone"], bevel=0.03)
            cone(f"Pinnacle{sx}{sy}", 0.17, 0.0, 0.7, (px, py, z + hh + 0.95), K["stone"], verts=4)
    box("HeadFloor", (2 * hw, 2 * hw, 0.14), (0, 0, z + 0.07), K["stonedark"], bevel=0.03)
    for face in range(4):
        s = _mark()
        gab = pointed(0, hw - 0.26, z + hh, hw - 0.1, 8)
        xz_prism(f"Gable{face}", gab + [(hw - 0.26, z + hh - 0.25), (-(hw - 0.26), z + hh - 0.25)], -hw + 0.02, -hw + 0.18, K["stone"], bevel=0.02)
        _xform(s, RZ(face * math.pi / 2))
    box("HeadRoof", (2 * hw - 0.1, 2 * hw - 0.1, 0.2), (0, 0, z + hh + 0.1), K["stonedark"], bevel=0.03)
    lathe("Spirelet", [(0, 0), (0.5, 0), (0.0, 1.5)], K["stone"], seg=8, loc=(0, 0, z + hh + 0.2))
    zt = z + hh + 1.7
    tube("CrossV", [(0, 0, zt), (0, 0, zt + 1.0)], 0.05, K["iron"], square=True, poly=True)
    tube("CrossH", [(-0.32, 0, zt + 0.65), (0.32, 0, zt + 0.65)], 0.045, K["iron"], square=True, poly=True)
    ring_lo("CrossRing", (0, 0, zt + 0.65), 0.2, "Y", K["iron"], thick=0.02)
    set_group("Glass")
    box("LanternGlass", (2 * hw - 0.36, 2 * hw - 0.36, hh - 0.34), (0, 0, z + 0.16 + (hh - 0.34) / 2), K["glass"], bevel=0.0)
    set_group("Glow")
    cyl("Candle", 0.1, 0.45, (0, 0, z + 0.4), K["glow"], verts=8, bevel=0.0)
    sphere("Flame", 0.08, (0, 0, z + 0.75), K["glow"], seg=8, rings=5, scale=(1, 1, 1.8))
    set_group("Main")
    rb = 5.6
    tops = []
    for k in range(8):
        a = k / 8 * 2 * math.pi + math.pi / 8
        x, y = rb * math.cos(a), rb * math.sin(a)
        zb = 0.44
        tube(f"Bollard{k}", [(x, y, zb - 0.1), (x, y, zb + 1.6)], 0.07, K["iron"], square=True, poly=True)
        sphere(f"BollardKnob{k}", 0.1, (x, y, zb + 1.62), K["iron"], seg=8, rings=4)
        cone(f"BollardSpear{k}", 0.09, 0.0, 0.32, (x, y, zb + 1.86), K["iron"], verts=4)
        tops.append((x, y, zb + 1.35))
    for k in range(8):
        p, q = Vector(tops[k]), Vector(tops[(k + 1) % 8])
        pts = []
        for i in range(9):
            t = i / 8
            c = p.lerp(q, t)
            c.z -= 0.55 * 4 * t * (1 - t)
            pts.append(c)
        for i in range(8):
            m_ = (pts[i] + pts[i + 1]) / 2
            ring_lo(f"Chain{k}_{i}", tuple(m_), 0.07, "Z" if i % 2 else "X", K["iron"], thick=0.013)
    cards = G.Cards(rng)
    for k in range(70):
        a = rng.uniform(0, 6.28)
        rr_ = rng.uniform(3.85, 7.1)
        cards.crossed((rr_ * math.cos(a), rr_ * math.sin(a), 0.36), 0.5, 0.4, "grass" if rng.random() < 0.6 else "ivy", k=2)
    for k in range(40):
        a = rng.uniform(0, 6.28)
        p = (3.75 * math.cos(a), 3.75 * math.sin(a), rng.uniform(0.4, 0.75))
        cards.blob(p, (0.3, 0.3, 0.25), 2, "ivy", 0.45)
    cards.build("Leaves")
    P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"
    PORTS[name] = []
    return _dims()



BUILDERS = {
    "FlagWalk8": lambda M: run_piece(M, "FlagWalk8", "flag", [("S", 8)]),
    "FlagWalk16": lambda M: run_piece(M, "FlagWalk16", "flag", [("S", 16)]),
    "FlagCurve90": lambda M: run_piece(M, "FlagCurve90", "flag", [("A", 8, 90, 1)]),
    "FlagCurve90Wide": lambda M: run_piece(M, "FlagCurve90Wide", "flag", [("A", 16, 90, 1)]),
    "FlagCurve45": lambda M: run_piece(M, "FlagCurve45", "flag", [("A", 16, 45, 1)]),
    "FlagCurve22": lambda M: run_piece(M, "FlagCurve22", "flag", [("A", 16, 22.5, 1)]),
    "FlagSBendR": lambda M: run_piece(M, "FlagSBendR", "flag", [("A", 10, SB_T, 1), ("A", 10, SB_T, -1)]),
    "FlagSBendL": lambda M: run_piece(M, "FlagSBendL", "flag", [("A", 10, SB_T, -1), ("A", 10, SB_T, 1)]),
    "FlagFork": flag_fork,
    "FlagSteps": flag_steps,
    "FlagRamp": flag_ramp,
    "GateApron8": gate_apron,
    "LeafWalk16": leaf_walk,
    "GravelWalk16": lambda M: run_piece(M, "GravelWalk16", "gravel", [("S", 16)]),
    "GravelCurve90": lambda M: run_piece(M, "GravelCurve90", "gravel", [("A", 8, 90, 1)]),
    "BrickWalk8": lambda M: run_piece(M, "BrickWalk8", "brick", [("S", 8)]),
    "BrickWalk16": lambda M: run_piece(M, "BrickWalk16", "brick", [("S", 16)]),
    "BrickCurve90": brick_curve90,
    "BrickCurve45": lambda M: run_piece(M, "BrickCurve45", "brick", [("A", 16, 45, 1)]),
    "BrickTee": brick_tee,
    "BrickCross": brick_cross,
    "CobbleWalk8": lambda M: run_piece(M, "CobbleWalk8", "cobble", [("S", 8)]),
    "CobbleWalk16": lambda M: run_piece(M, "CobbleWalk16", "cobble", [("S", 16)]),
    "CobbleCurve45": lambda M: run_piece(M, "CobbleCurve45", "cobble", [("A", 16, 45, 1)]),
    "CobbleBranch": cobble_branch,
    "CobbleFlare": cobble_flare,
    "GateThreshold16": gate_threshold16,
    "RoundelQuarter": roundel_quarter,
    "RoundelCentre": roundel_centre,
    "GateTunnel": gate_tunnel,
    "RosePergola": rose_pergola,
    "ColonnadeBay": colonnade_bay,
    "LychPassage": lych_passage,
    "YewTunnel": yew_tunnel,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
