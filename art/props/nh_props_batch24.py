"""Props batch 24 (2026-11-05): the Lost & Found kit for nh_props.py, on theme with the Institution: ink, bone, wax, paper,
brass, iron and deep crimson (#600E1A), candlelit gothic. Eight lost things (one piece each, real hand size: 1 stud is
about 28 cm) and the box they turn up in. No blood; the ink is blue-black.

  LostScarf       an Athletes' varsity scarf folded in three: crimson knit with bone stripes, fringed ends, a bone and
                  crimson shield patch with a star
  LostSketchbook  a battered black cloth sketchbook: blue-black ink splatters on the cover and the page edges, a dog-eared
                  corner, a paper label reading "sketches", an elastic band holding a crimson pencil, a crimson ribbon
  LostWristband   the Delinquents' black leather cuff: two rows of iron pyramid studs, bone stitching, an iron buckle
                  on the strap's tail
  LostPendant     the Pack's wolf-tooth pendant: a fang wired in iron, bone and iron beads, its leather cord coiled
  LostHymnal      the Choir's small hymnal: dark crimson leather, a gilt cross pattee and border, gilt page edges,
                  raised bands, a gilt clasp and two ribbons
  LostLunchTin    the Ordinary's dented tinplate lunch tin: a folding wire handle, a hasp, back hinges, a bone label
                  with a crimson border hand-painted "LUNCH"
  LostPocketWatch a brass hunter watch lying open, the lid up on its hinge: a bone dial (painted hour and minute
                  track), spade hands, a sub-dial, cracks across the face; its chain coiled with a T-bar and a fob
  LostPhone       a slim phone in an iron-grey case, its black screen cracked from one corner, a camera bump, a
                  crimson enamel crescent charm on a black cord
  LostFoundBox    the Lost & Found chest: dark oak bound in iron with brass corners and bun feet, a lock plate, drop
                  handles, the lid propped open on an iron stay (a pasted list inside it); a heap of lost cloth with a
                  bone glove draped over the rim, a book corner, a furled umbrella and a striped scarf end hanging down
                  the side; behind it a painted bone board on a two-post iron stand hand-lettered LOST & FOUND
                  (ink-black capitals, a crimson ampersand and underline)

Front faces -Y, Z is up, the origin is at the bottom centre: every prop is moved so its bounds are centred over the origin
and its lowest point is on z = 0 (the small things lie flat on the floor). Every prop is a single piece.
The hand props get a higher preview camera than nh_props.preview gives (they lie flat); see _preview at the end.
Registered into nh_props.BUILD on import.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, _finish
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, hoop, strip, rrect, _mark, _xform, _dims, flat, _smooth, _mesh
from nh_props_batch10 import gilt, velvet
from nh_props_batch21 import frame_gilt
import nh_props_batch20 as B20


FONT_SIGN = "C:/Windows/Fonts/segoeprb.ttf"   # Segoe Print Bold: hand lettering (Blender's built-in font if missing)
FONT_HAND = "C:/Windows/Fonts/Inkfree.ttf"    # Ink Free: a quick handwritten label
CRIMSON = (0.117, 0.0045, 0.0103)              # #600E1A in linear RGB
BONE = (0.62, 0.565, 0.45)
INK = (0.012, 0.016, 0.05)                     # blue-black ink


# ------------------------------------------------------------------ material plumbing

def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _colour_in(m):
    """(socket feeding the weathering's colour, the socket it feeds) of a P.material."""
    bs = _bsdf(m)
    c2 = bs.inputs["Base Color"].links[0].from_node
    c1 = c2.inputs[6].links[0].from_node
    return c1.inputs[6].links[0].from_socket, c1.inputs[6]


def _rough_in(m):
    sub = _bsdf(m).inputs["Roughness"].links[0].from_node
    add = sub.inputs[0].links[0].from_node
    return add.inputs[0].links[0].from_socket, add.inputs[0]


def _metal_in(m):
    sock = _bsdf(m).inputs["Metallic"]
    nd = sock.links[0].from_node
    if nd.type == "MATH":
        sock = nd.inputs[0]
    return sock.links[0].from_socket, sock


def _coords(nt):
    return nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]


def _mix_rgb(nt, fac, a, b):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MIX"
    nt.links.new(fac, mx.inputs["Factor"])
    for i, v in ((6, a), (7, b)):
        if isinstance(v, tuple):
            mx.inputs[i].default_value = (*v[:3], 1)
        else:
            nt.links.new(v, mx.inputs[i])
    return mx.outputs[2]


def _mix_f(nt, fac, a, b):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "FLOAT"
    nt.links.new(fac, mx.inputs[0])
    for i, v in ((2, a), (3, b)):
        if isinstance(v, (int, float)):
            mx.inputs[i].default_value = v
        else:
            nt.links.new(v, mx.inputs[i])
    return mx.outputs[0]


def _paint(m, mask, rgb, rough=None, metal=None):
    """Lay a colour (and roughness / metalness) over a P.material wherever `mask` (a 0..1 socket) is set."""
    nt = m.node_tree
    src, dst = _colour_in(m)
    nt.links.new(_mix_rgb(nt, mask, src, rgb), dst)
    if rough is not None:
        src, dst = _rough_in(m)
        nt.links.new(_mix_f(nt, mask, src, rough), dst)
    if metal is not None:
        src, dst = _metal_in(m)
        nt.links.new(_mix_f(nt, mask, src, metal), dst)


def _bump(m, height, distance, strength=1.0):
    """Feed a procedural height into a flat material's bump (flat materials only)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BUMP")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height, b.inputs["Height"])


def _splat_mask(m, scale, blob=0.62, region=0.46, drops=0.1, seed=0.0, detail=12.0):
    """A crisp ink-splatter mask in object space: ragged blobs in a few regions plus scattered droplets (a low detail
    gives solid blots, a high one torn, speckled edges)."""
    nt = m.node_tree
    co = _coords(nt)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (seed * 3.1, seed * 1.7, seed * 2.3)
    nt.links.new(co, mp.inputs["Vector"])
    v = mp.outputs["Vector"]
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = scale
    n1.inputs["Detail"].default_value = detail; n1.inputs["Roughness"].default_value = 0.6; n1.inputs["Distortion"].default_value = 0.5
    nt.links.new(v, n1.inputs["Vector"])
    b = _math(nt, "GREATER_THAN", n1.outputs["Fac"], blob)
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = scale * 0.22; n2.inputs["Detail"].default_value = 2
    nt.links.new(v, n2.inputs["Vector"])
    b = _math(nt, "MULTIPLY", b, _math(nt, "GREATER_THAN", n2.outputs["Fac"], region))
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale * 3.2
    nt.links.new(v, vo.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vo.outputs["Color"], sep.inputs["Color"])
    d = _math(nt, "MULTIPLY", _math(nt, "LESS_THAN", vo.outputs["Distance"], drops), _math(nt, "GREATER_THAN", sep.outputs[0], 0.8))
    return _math(nt, "MAXIMUM", b, d)


def splatter(m, rgb, scale=7.0, rough=0.12, metal=None, **kw):
    _paint(m, _splat_mask(m, scale, **kw), rgb, rough, metal)
    return m


def wool(name, rgb, rib=0.016):
    """Knitted wool: ribs running along X (the length of a scarf or a finger), stitches across, a little fuzz."""
    m = flat(name, rgb, 0.96, dirt=0.45)
    nt = m.node_tree
    co = _coords(nt)
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.bands_direction = "Y"; w1.inputs["Scale"].default_value = 0.314 / rib
    w1.inputs["Distortion"].default_value = 0.6
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.bands_direction = "X"; w2.wave_profile = "TRI"; w2.inputs["Scale"].default_value = 0.314 / (rib * 0.7)
    fz = nt.nodes.new("ShaderNodeTexNoise"); fz.inputs["Scale"].default_value = 160; fz.inputs["Detail"].default_value = 3
    for t in (w1, w2, fz):
        nt.links.new(co, t.inputs["Vector"])
    h = _math(nt, "MULTIPLY", w1.outputs["Fac"], _math(nt, "ADD", _math(nt, "MULTIPLY", w2.outputs["Fac"], 0.45), 0.55))
    h = _math(nt, "ADD", h, _math(nt, "MULTIPLY", fz.outputs["Fac"], 0.25))
    _bump(m, h, 0.0035)
    # a faint stitch shading in the colour too, so the knit reads in the colour map alone
    src, dst = _colour_in(m)
    nt.links.new(_mix_rgb(nt, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 1.0, h, clamp=True), 0.35), src, tuple(c * 0.55 for c in rgb)), dst)
    return m


def cloth(name, rgb, rough=0.8, weave=0.006, wear=0.0, dirt=0.55):
    """Book cloth or canvas: a fine square weave in the bump."""
    m = flat(name, rgb, rough, wear=wear, dirt=dirt)
    nt = m.node_tree
    co = _coords(nt)
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.bands_direction = "X"; w1.inputs["Scale"].default_value = 0.314 / weave
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.bands_direction = "Y"; w2.inputs["Scale"].default_value = 0.314 / weave
    nt.links.new(co, w1.inputs["Vector"]); nt.links.new(co, w2.inputs["Vector"])
    _bump(m, _math(nt, "MULTIPLY", w1.outputs["Fac"], w2.outputs["Fac"]), 0.0012)
    return m


def pages(name, rgb, line=0.0032, metal=0.0, rough=0.85):
    """A page block's edges: fine stacked page lines along Z, a little darker in the grooves."""
    m = flat(name, rgb, rough, metal=metal, dirt=0.6)
    nt = m.node_tree
    w = nt.nodes.new("ShaderNodeTexWave"); w.bands_direction = "Z"; w.inputs["Scale"].default_value = 0.314 / line
    w.inputs["Distortion"].default_value = 1.2; w.inputs["Detail"].default_value = 3
    nt.links.new(_coords(nt), w.inputs["Vector"])
    _bump(m, w.outputs["Fac"], 0.0008)
    src, dst = _colour_in(m)
    nt.links.new(_mix_rgb(nt, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 1.0, w.outputs["Fac"]), 0.3), src, tuple(c * 0.6 for c in rgb)), dst)
    return m


def leather(name, rgb, scale=5.0, wear=0.18):
    return P.material(name, "NH_Leather", tint=rgb, scale=scale, normal=0.55, wear=wear, dirt=0.75)


def brass_fine():
    return P.material("BrassFine", "NH_Brass", tint=(1.0, 0.93, 0.8), scale=3.0, wear=0.3, dirt=0.85)


def iron_fine(tint=(0.13, 0.125, 0.135)):
    return P.material("IronFine", "NH_Iron", tint=tint, scale=2.5, rough_add=0.04, wear=0.5, wear_metal=True, dirt=0.8)


def _fine(k=0.3):
    """Scale the bake-time weathering to a hand-sized prop: the edge-wear and rounded-edge bevels and the crevice AO
    are sized for furniture, and would round over or dirty every face of something 3 cm thick."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "BEVEL":
                n.inputs["Radius"].default_value *= k
            elif n.type == "AMBIENT_OCCLUSION":
                n.inputs["Distance"].default_value *= k


# ------------------------------------------------------------------ geometry helpers

def _settle():
    """Move everything so the bounds sit centred over the origin in X and Y with the lowest point on z = 0."""
    bpy.context.view_layer.update()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in P.PARTS:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for k in range(3):
                lo[k], hi[k] = min(lo[k], w[k]), max(hi[k], w[k])
    _xform(0, Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    bpy.context.view_layer.update()


def _recalc(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def sweep(name, pts, radius, mat, seg=8, flat_k=1.0, up=(0, 0, 1), caps=True):
    """A tube of varying radius along a polyline. radius is a number or f(t), t = 0..1 along the path (0 closes the
    end to a point); flat_k squashes the section along the normal nearest `up` (a finger, a flattened fang)."""
    V = [Vector(p) for p in pts]
    n = len(V)
    cum = [0.0]
    for a, b in zip(V, V[1:]):
        cum.append(cum[-1] + (b - a).length)
    T = [(V[min(i + 1, n - 1)] - V[max(i - 1, 0)]).normalized() for i in range(n)]
    u = Vector(up)
    N = u - T[0] * u.dot(T[0])
    if N.length < 1e-6:
        N = T[0].orthogonal()
    N.normalize()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i:
            N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        r = radius(cum[i] / cum[-1]) if callable(radius) else radius
        if r <= 1e-5:
            rings.append([bm.verts.new(V[i])])
            continue
        rings.append([bm.verts.new(V[i] + (N * math.cos(a) * flat_k + B * math.sin(a)) * r)
                      for a in [k / seg * 2 * math.pi for k in range(seg)]])
    for A, Bv in zip(rings, rings[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            if len(A) == 1 and len(Bv) == 1:
                continue
            if len(A) == 1:
                bm.faces.new((A[0], Bv[j], Bv[k]))
            elif len(Bv) == 1:
                bm.faces.new((A[k], A[j], Bv[0]))
            else:
                bm.faces.new((A[k], A[j], Bv[j], Bv[k]))
    if caps:
        for rg in (rings[0], rings[-1]):
            if len(rg) > 2:
                bm.faces.new(rg)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def _resample(loop, step):
    """A closed outline [(x, y), ...] resampled to points about `step` apart."""
    out = []
    for i, a in enumerate(loop):
        b = loop[(i + 1) % len(loop)]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(round(L / step)))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def rbox(name, hw, hd, r, z0, z1, mat, cx=0.0, cy=0.0, step=0.03, rows=6, bevel=0.0, top=True, bottom=True):
    """A rounded-rectangle block with its sides cut into rows and evenly spaced columns (so it can be dented)."""
    ring = _resample([(p[0], p[1]) for p in rrect(hw, hd, r, 0, n=5)], step)
    bm = bmesh.new()
    rings = [[bm.verts.new((cx + x, cy + y, z0 + (z1 - z0) * k / rows)) for x, y in ring] for k in range(rows + 1)]
    m = len(ring)
    for A, B in zip(rings, rings[1:]):
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new((A[i], A[j], B[j], B[i]))
    if bottom:
        bm.faces.new(list(reversed(rings[0])))
    if top:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    md.min_vertices = 5
    _finish(ob, mat, bevel)
    return ob


def dent(ob, c, r, depth, inward):
    """Push the mesh in (along `inward`) round the point c: a smooth dent r across."""
    c, inward = Vector(c), Vector(inward).normalized()
    for v in ob.data.vertices:
        d = (v.co - c).length
        if d < r:
            v.co += inward * depth * (1 - (d / r) ** 2) ** 2
    ob.data.update()


def torus(name, mtx, R, r, mat, seg=(8, 4), sx=1.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg[0], minor_segments=seg[1])
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, 1, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.matrix_world = mtx
    return _finish(ob, mat, 0)


def _text(name, text, font, mat, place, fit=None, size=None, depth=0.005, space=1.0, res=3, bold=0.0):
    """Lettering lying on a surface: place(x, y, h) maps the glyph plane (x right, y up, h the height off the surface,
    0..depth) to the world. Fitted into fit = (width, height), or at `size` per em; bold thickens the strokes (em units).
    The faces on the surface are dropped and the letters triangulated (concave glyph faces import into Roblox cleanly)."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    if font and os.path.exists(font):
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size = 1.0
    cu.space_character = space
    cu.offset = bold
    cu.extrude = 0.5 * depth
    cu.resolution_u = res
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    s = size if fit is None else min(fit[0] / (max(xs) - min(xs)), fit[1] / (max(ys) - min(ys)))
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    zmax = max(v.co.z for v in me.vertices)
    low = set()
    for v in me.vertices:
        x, y, z = v.co
        h = z - (zmax - depth)
        if h < 1e-6:
            low.add(v.index)
        v.co = Vector(place((x - mx) * s, (y - my) * s, max(0.0, h)))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.index in low for v in f.verts)], context="FACES")
    bm.to_mesh(me)
    bm.free()
    _finish(ob, mat, 0)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    md.quad_method = "BEAUTY"
    md.ngon_method = "BEAUTY"
    return ob


def _words(prefix, words, font, place, fit, depth=0.005, gap=0.32, res=3, bold=0.0, space=1.0):
    """A line of words each in its own material, [(text, material), ...], on one baseline at one scale (gap in em
    between words), fitted into fit = (width, height) and centred; place() as in _text. Returns the word objects."""
    built = []
    for k, (text, mat) in enumerate(words):
        cu = bpy.data.curves.new(f"{prefix}{k}", "FONT")
        cu.body = text
        if font and os.path.exists(font):
            cu.font = bpy.data.fonts.load(font, check_existing=True)
        cu.align_x, cu.align_y = "LEFT", "BOTTOM_BASELINE"
        cu.size, cu.space_character, cu.offset = 1.0, space, bold
        cu.extrude, cu.resolution_u = 0.5 * depth, res
        ob = bpy.data.objects.new(f"{prefix}{k}", cu)
        bpy.context.collection.objects.link(ob)
        for o in bpy.context.selected_objects:
            o.select_set(False)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.convert(target="MESH")
        built.append((bpy.context.active_object, mat))
    cursor, starts, lo, hi = 0.0, [], 1e9, -1e9
    for ob, _ in built:
        xs = [v.co.x for v in ob.data.vertices]
        ys = [v.co.y for v in ob.data.vertices]
        starts.append(cursor - min(xs))
        cursor += max(xs) - min(xs) + gap
        lo, hi = min(lo, min(ys)), max(hi, max(ys))
    total = cursor - gap
    s = min(fit[0] / total, fit[1] / (hi - lo))
    out = []
    for (ob, mat), ox in zip(built, starts):
        me = ob.data
        zmax = max(v.co.z for v in me.vertices)
        low = set()
        for v in me.vertices:
            x, y, z = v.co
            h = z - (zmax - depth)
            if h < 1e-6:
                low.add(v.index)
            v.co = Vector(place((x + ox - total / 2) * s, (y - (lo + hi) / 2) * s, max(0.0, h)))
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(v.index in low for v in f.verts)], context="FACES")
        bm.to_mesh(me)
        bm.free()
        _finish(ob, mat, 0)
        md = ob.modifiers.new("Tri", "TRIANGULATE")
        md.quad_method = "BEAUTY"
        md.ngon_method = "BEAUTY"
        out.append(ob)
    return out


def _path_line(a, b, step=0.05):
    n = max(1, int(round(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
    return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]


def _path_arc(c, r, a0, a1, sx=1, n=12):
    """Points round a half fold: angles in degrees from a0 to a1 (sx = -1 bends round the -X side)."""
    return [(c[0] + sx * r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _join_path(*parts):
    out = []
    for p in parts:
        for q in p:
            if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                out.append(q)
    return out


SCARF_STRIPES = [("c", 0.2), ("b", 0.055), ("c", 0.045), ("b", 0.055)]


def striped_band(prefix, pts, width, thick, pattern, mats, side=(0, 1, 0), ref=(0, 0, 1), puff=0.004, ds=0.05, offset=0.0,
                 fringe=(), tassel=0.1, droop=(0.0, 0.0), rnd=None, n_tassel=9, wobble=0.0):
    """A knitted band (a scarf) along a 3D path, `width` across `side`: block stripes by arc length from `pattern`
    [(material key, length), ...], each stripe its own sheet so the edges are crisp; a slight crown across the width
    (toward `ref`); fringed ends ("start", "end") of alternating tassels."""
    rnd = rnd or random.Random(24)
    V = [Vector(p) for p in pts]
    cum = [0.0]
    for a, b in zip(V, V[1:]):
        cum.append(cum[-1] + (b - a).length)
    total = cum[-1]

    def at(s):
        s = max(0.0, min(total, s))
        for i in range(len(cum) - 1):
            if cum[i + 1] >= s:
                t = (s - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
                return V[i].lerp(V[i + 1], t)
        return V[-1]

    def frame(s):
        e = 0.004
        t = (at(min(total, s + e)) - at(max(0.0, s - e))).normalized()
        sv = Vector(side) - t * Vector(side).dot(t)
        sv.normalize()
        nn = t.cross(sv)
        if nn.dot(Vector(ref)) < 0:
            nn = -nn
        return t, sv, nn

    bounds, s, k = [], -offset, 0
    while s < total:
        key, L = pattern[k % len(pattern)]
        bounds.append((s, key))
        s += L
        k += 1
    ss = sorted(set([round(x, 6) for x in cum] + [round(i * ds, 6) for i in range(int(total / ds) + 1)] +
                    [round(b, 6) for b, _ in bounds if 0 < b < total] + [round(total, 6)]))

    def key_at(s):
        kk = bounds[0][1]
        for b, key in bounds:
            if b <= s:
                kk = key
        return kk

    def row(s):
        # soft cloth: a crown across the width, the edges wandering a little sideways and up and down along the length
        p = at(s) + frame(s)[1] * (wobble * math.sin(s * 7.3 + 0.6)) + frame(s)[2] * (wobble * 0.5 * math.sin(s * 11.1))
        t, sv, nn = frame(s)
        w = width * (1 + 0.6 * wobble / max(width, 1e-6) * math.sin(s * 5.1 + 1.3))
        return [p + sv * (u * w / 2) + nn * (puff * (1 - u * u) + wobble * 0.4 * u * math.sin(s * 9.7)) for u in (-1, -0.5, 0, 0.5, 1)]

    seg_start, j = 0, 0
    for i in range(len(ss) - 1):
        kk = key_at((ss[i] + ss[i + 1]) / 2)
        nxt = key_at((ss[i + 1] + ss[i + 2]) / 2) if i + 2 < len(ss) else None
        if nxt != kk:
            _mesh(f"{prefix}{j}", [row(x) for x in ss[seg_start:i + 2]], mats[kk], thick)
            seg_start, j = i + 1, j + 1
    for end in fringe:
        s = 0.0 if end == "start" else total
        p = at(s)
        t, sv, nn = frame(s)
        if end == "start":
            t = -t
        dr = droop[0 if end == "start" else 1]
        for q in range(n_tassel):
            u = -1 + 2 * (q + 0.5) / n_tassel
            b0 = p + sv * (u * width / 2 * 0.9)
            L = tassel * rnd.uniform(0.85, 1.15)
            tip = b0 + t * L + sv * rnd.uniform(-0.015, 0.015) + Vector((0, 0, -dr))
            mid = b0 + t * L * 0.5 + Vector((0, 0, -dr * 0.4))
            sweep(f"{prefix}Tassel{end}{q}", [b0 - t * 0.01, mid, tip], lambda tt: 0.0095 * (1 - 0.35 * tt), mats["b" if q % 2 else "c"], seg=5)
    return at, frame


def _star(cx, cy, ro, ri, n=5, rot=math.pi / 2):
    return [(cx + math.cos(rot + k * math.pi / n) * (ro if k % 2 == 0 else ri), cy + math.sin(rot + k * math.pi / n) * (ro if k % 2 == 0 else ri))
            for k in range(2 * n)]


def _shield(cx, cy, hw, hh, n=8):
    """A heater shield outline (x, y), point toward -Y."""
    pts = [(cx - hw, cy + hh), (cx + hw, cy + hh)]
    for k in range(n + 1):
        t = k / n
        pts.append((cx + hw * math.cos(t * math.pi / 2) ** 0.8, cy + hh * 0.2 - hh * 1.2 * math.sin(t * math.pi / 2)))
    pts[-1] = (cx, cy - hh)
    for k in range(n - 1, -1, -1):
        t = k / n
        pts.append((cx - hw * math.cos(t * math.pi / 2) ** 0.8, cy + hh * 0.2 - hh * 1.2 * math.sin(t * math.pi / 2)))
    return pts


def _cracks(prefix, cx, cy, z, mat, rnd, inside, rays=8, reach=0.12, r=0.0015, rings=(0.025, 0.055)):
    """Crazed glass: jagged rays from an impact point and broken rings between them, as fine tubes lying at z."""
    angs = sorted(k * 2 * math.pi / rays + rnd.uniform(-0.25, 0.25) for k in range(rays))
    ends = []
    for k, a in enumerate(angs):
        pts, x, y, aa = [(cx, cy, z)], cx, cy, a
        L = reach * rnd.uniform(0.6, 1.2)
        for _ in range(5):
            aa += rnd.uniform(-0.35, 0.35)
            x2, y2 = x + math.cos(aa) * L / 5, y + math.sin(aa) * L / 5
            if not inside(x2, y2):
                break
            x, y = x2, y2
            pts.append((x, y, z))
        if len(pts) > 1:
            tube(f"{prefix}Ray{k}", pts, r, mat, poly=True)
        ends.append(a)
    for j, rr in enumerate(rings):
        for k in range(rays):
            if rnd.random() < 0.35:
                continue
            a0, a1 = angs[k], angs[(k + 1) % rays] + (2 * math.pi if k == rays - 1 else 0)
            pts = []
            for q in range(5):
                a = a0 + (a1 - a0) * q / 4
                rq = rr * rnd.uniform(0.85, 1.15)
                x, y = cx + math.cos(a) * rq, cy + math.sin(a) * rq
                if inside(x, y):
                    pts.append((x, y, z))
            if len(pts) > 1:
                tube(f"{prefix}Ring{j}{k}", pts, r * 0.8, mat, poly=True)


# ================================================================== the scarf
def lost_scarf(M):
    rnd = random.Random(2401)
    cr, bn = wool("ScarfCrimson", CRIMSON), wool("ScarfBone", BONE)
    t = 0.042
    pf = 0.012
    z1 = t / 2 + 0.002
    z2 = z1 + t + pf + 0.004
    z3 = z2 + t + pf + 0.004
    rr = (z2 - z1) / 2
    path = _join_path(_path_line((-0.62, z1), (0.55, z1), 0.04), _path_arc((0.55, (z1 + z2) / 2), rr, -90, 90, 1),
                      _path_line((0.55, z2), (-0.55, z2), 0.04), _path_arc((-0.55, (z2 + z3) / 2), rr, -90, 90, -1),
                      _path_line((-0.55, z3), (0.44, z3), 0.04))
    striped_band("Scarf", [(x, 0.0, z) for x, z in path], 0.42, t, SCARF_STRIPES, {"c": cr, "b": bn}, offset=0.14, puff=pf, ds=0.04,
                 fringe=("start", "end"), tassel=0.1, droop=(0.01, 0.016), rnd=rnd, wobble=0.006)
    # the Athletes' shield patch on the top fold: bone felt, a crimson field, a bone star
    felt_b = flat("PatchBone", (0.7, 0.64, 0.52), 0.9, dirt=0.4)
    felt_c = flat("PatchCrimson", CRIMSON, 0.85, dirt=0.4)
    zt = z3 + t / 2 + pf - 0.001
    B20.tprism("Patch", _shield(-0.27, 0.0, 0.085, 0.1), zt - 0.004, 0.008, felt_b, plane="XY", bevel=0.002)
    B20.tprism("PatchField", _shield(-0.27, 0.004, 0.066, 0.08), zt + 0.002, 0.005, felt_c, plane="XY", bevel=0.0015)
    B20.tprism("PatchStar", _star(-0.27, 0.012, 0.034, 0.014), zt + 0.005, 0.004, felt_b, plane="XY", bevel=0.001)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the sketchbook
def lost_sketchbook(M):
    rnd = random.Random(2402)
    W, D = 0.66, 0.9
    cover = cloth("SketchCover", (0.014, 0.013, 0.016), rough=0.72, weave=0.006, wear=0.22, dirt=0.65)
    # glossy blue-black ink blots and flicks on the matt black cloth (they read by their sheen and a faint indigo)
    splatter(cover, (0.008, 0.013, 0.07), scale=3.2, rough=0.06, blob=0.6, region=0.38, drops=0.07, seed=1.0, detail=3.0)
    page = pages("SketchPages", (0.68, 0.62, 0.49))
    splatter(page, INK, scale=7.0, rough=0.2, blob=0.57, region=0.4, drops=0.14, seed=4.0)
    tape = flat("SpineTape", (0.02, 0.02, 0.022), 0.45, wear=0.3, dirt=0.6)
    elastic = flat("Elastic", (0.015, 0.015, 0.017), 0.7, dirt=0.4)
    # back cover, page block, spine
    box("BackCover", (W, D, 0.012), (0, 0, 0.006), cover, bevel=0.004)
    box("Pages", (W - 0.03, D - 0.024, 0.066), (0.01, 0, 0.012 + 0.033), page, bevel=0.003)
    sp = cyl("Spine", 0.046, D + 0.002, (-W / 2 + 0.012, 0, 0.046), tape, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.003)
    sp.scale = (0.5, 1, 1)               # a flattened, rounded spine (not a roll)
    # the front cover, dog-eared at the front right corner (a grid sheet, so the corner can lift)
    zc = 0.084
    rows = []
    for j in range(19):
        y = -D / 2 + D * j / 18
        row = []
        for i in range(15):
            x = -W / 2 + W * i / 14
            lift = 0.035 * max(0.0, (x - W / 2) / 0.16 - (y + D / 2) / 0.16 + 1) ** 2
            row.append((x, y, zc + lift))
        rows.append(row)
    _mesh("FrontCover", rows, cover, 0.012)
    # a paper label with a hand-written "sketches" and an ink blot
    lab = flat("Label", (0.66, 0.6, 0.47), 0.85, dirt=0.5)
    splatter(lab, INK, scale=14.0, rough=0.2, blob=0.7, region=0.62, drops=0.08, seed=7.0)
    box("LabelPaper", (0.32, 0.13, 0.004), (-0.03, 0.22, 0.092), lab, bevel=0.001, segments=1)
    _text("LabelText", "sketches", FONT_HAND, flat("InkText", INK, 0.3, dirt=0.2), lambda x, y, h: (-0.03 + x, 0.22 + y, 0.094 + h),
          fit=(0.25, 0.08), depth=0.0015)
    # the elastic band over the cover, lifted over a crimson pencil tucked under it
    xb = 0.17
    py, pr = 0.1, 0.016
    strip("Band", [(xb, -D / 2 - 0.004, -0.002), (xb, -D / 2 - 0.004, 0.09), (xb, -D / 2 + 0.03, 0.093), (xb, py - 0.07, 0.093),
                   (xb, py - 0.025, 0.093 + 2 * pr + 0.008), (xb, py + 0.025, 0.093 + 2 * pr + 0.008), (xb, py + 0.07, 0.093),
                   (xb, D / 2 - 0.03, 0.093), (xb, D / 2 + 0.004, 0.09), (xb, D / 2 + 0.004, -0.002)], 0.028, (1, 0, 0), elastic, thick=0.004, it=2)
    box("BandUnder", (0.028, D, 0.004), (xb, 0, -0.002), elastic, bevel=0.0, segments=1)
    lq = flat("PencilLacquer", (0.13, 0.008, 0.014), 0.3, wear=0.2, dirt=0.4)
    pz = 0.093 + pr
    cyl("Pencil", pr, 0.56, (0.18, py, pz), lq, rot=(0, math.pi / 2, 0), verts=6, bevel=0.002)
    cyl("Ferrule", pr * 1.04, 0.04, (0.48, py, pz), brass_fine(), rot=(0, math.pi / 2, 0), verts=12, bevel=0.002)
    cyl("Eraser", pr * 0.95, 0.03, (0.515, py, pz), flat("Eraser", (0.55, 0.38, 0.34), 0.8), rot=(0, math.pi / 2, 0), verts=12, bevel=0.004)
    cone("PencilWood", pr, 0.005, 0.05, (-0.125, py, pz), flat("PencilWood", (0.55, 0.38, 0.22), 0.7), verts=6, rot=(0, -math.pi / 2, 0))
    cone("Lead", 0.005, 0.0, 0.014, (-0.157, py, pz), flat("Graphite", (0.05, 0.05, 0.055), 0.35, metal=0.4), verts=6, rot=(0, -math.pi / 2, 0))
    # a crimson ribbon out of the pages onto the floor
    strip("Ribbon", [(-0.12, -D / 2 + 0.03, 0.05), (-0.115, -D / 2 - 0.01, 0.035), (-0.11, -D / 2 - 0.04, 0.008), (-0.09, -D / 2 - 0.09, 0.002),
                     (-0.06, -D / 2 - 0.15, 0.002)], 0.026, (1, 0, 0), velvet(), thick=0.003, it=2)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the studded wristband
def _ellipse_pt(R, sy, a, z):
    p = Vector((R * math.cos(a), R * sy * math.sin(a), z))
    n = Vector((math.cos(a), math.sin(a) / sy, 0)).normalized()
    return p, n


def lost_wristband(M):
    R_in, R_out, Hb, sy = 0.2, 0.226, 0.15, 0.9
    hide = leather("CuffLeather", (0.034, 0.026, 0.025), scale=5.0, wear=0.15)
    # bone stitching along both edges of the outer face
    nt = hide.node_tree
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(_coords(nt), sep.inputs["Vector"])
    x, y, z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    ang = _math(nt, "ARCTAN2", _math(nt, "DIVIDE", y, sy), x)
    dash = _math(nt, "GREATER_THAN", _math(nt, "SINE", _math(nt, "MULTIPLY", ang, 170.0)), 0.3)
    rad = _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", x, x), _math(nt, "MULTIPLY", _math(nt, "DIVIDE", y, sy), _math(nt, "DIVIDE", y, sy))))
    outer = _math(nt, "GREATER_THAN", rad, R_out - 0.004)
    ln = _math(nt, "MAXIMUM", _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", z, 0.016)), 0.0032),
               _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", z, Hb - 0.016)), 0.0032))
    _paint(hide, _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", dash, ln), outer), (0.36, 0.32, 0.25), rough=0.85)
    stud = iron_fine((0.3, 0.3, 0.32))
    iron = iron_fine()
    e = 0.004
    _recalc(lathe("Band", [(R_in, e), (R_in + e, 0), (R_out - e, 0), (R_out, e), (R_out, Hb - e), (R_out - e, Hb), (R_in + e, Hb), (R_in, Hb - e), (R_in, e)],
                  hide, seg=64, scale=(1, sy)))
    ab = -math.pi / 2                   # the buckle sits at the front
    # pyramid studs in two rows
    for row, zz in enumerate((0.047, Hb - 0.047)):
        for k in range(18):
            a = ab + math.pi / 9 * 0.5 * row + k * 2 * math.pi / 18
            da = (a - ab + math.pi) % (2 * math.pi) - math.pi
            if abs(da) < math.radians(40):
                continue
            p, n = _ellipse_pt(R_out, sy, a, zz)
            s = _mark()
            st = cone(f"Stud{row}{k}", 0.026, 0.0, 0.026, (0, 0, 0.013), stud, verts=4)
            st.modifiers.remove(st.modifiers["Bevel"])      # keep the pyramid's edges sharp
            _xform(s, Matrix.Translation(p - n * 0.002) @ Matrix.Rotation(math.atan2(n.y, n.x), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
                   @ Matrix.Rotation(math.pi / 4, 4, "Z"))
    # the strap's tail over the band, with holes, through an iron buckle and a leather keeper
    rows = []
    a0, a1 = ab - math.radians(38), ab + math.radians(30)
    for k in range(15):
        a = a0 + (a1 - a0) * k / 14
        taper = 1.0 if k < 12 else 1 - (k - 11) / 4 * 0.6
        rr = R_out + 0.011 + (0.004 * (k - 11) if k > 11 else 0)
        rows.append([_ellipse_pt(rr, sy, a, Hb / 2 + u * 0.04 * taper)[0] for u in (-1, -0.5, 0, 0.5, 1)])
    _mesh("Tail", rows, hide, 0.016)
    dark = flat("Hole", (0.01, 0.009, 0.009), 0.9)
    for k in range(3):
        a = ab + math.radians(8 + k * 7)
        p, n = _ellipse_pt(R_out + 0.02, sy, a, Hb / 2)
        sphere(f"Hole{k}", 0.008, p, dark, seg=8, rings=4, scale=(1, 1, 1))
    ak = ab - math.radians(6)
    p, n = _ellipse_pt(R_out + 0.026, sy, ak, Hb / 2)
    tg = Vector((-n.y, n.x, 0))
    fr = [p + tg * 0.03 + Vector((0, 0, -0.058)), p + tg * 0.03 + Vector((0, 0, 0.058)), p - tg * 0.03 + Vector((0, 0, 0.058)),
          p - tg * 0.03 + Vector((0, 0, -0.058))]
    tube("Buckle", [tuple(v) for v in fr], 0.007, iron, closed=True, poly=True)
    tube("Prong", [tuple(p - tg * 0.03), tuple(p + tg * 0.012 + n * 0.006)], 0.0045, iron, poly=True)
    pk, nk = _ellipse_pt(R_out + 0.02, sy, ab - math.radians(20), Hb / 2)
    rows = [[pk + Vector((-nk.y, nk.x, 0)) * w + Vector((0, 0, u * 0.055)) for u in (-1, -0.5, 0, 0.5, 1)] for w in (-0.012, 0.0, 0.012)]
    _mesh("Keeper", rows, hide, 0.01)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the wolf-tooth pendant
def lost_pendant(M):
    rnd = random.Random(2404)
    cordm = flat("Cord", (0.075, 0.042, 0.026), 0.6, dirt=0.5)
    nt = cordm.node_tree
    w = nt.nodes.new("ShaderNodeTexWave"); w.bands_direction = "DIAGONAL"; w.inputs["Scale"].default_value = 0.314 / 0.008
    nt.links.new(_coords(nt), w.inputs["Vector"])
    _bump(cordm, w.outputs["Fac"], 0.0012)
    rc = 0.012
    # the cord, coiled: a loose spiral, its inner end knotted, its outer end running out to the beads and the fang
    turns = 2.0
    a_end = turns * 2 * math.pi - math.radians(72)
    pts = []
    n = 70
    for k in range(n + 1):
        a = 0.4 + (a_end - 0.4) * k / n
        r = 0.13 + 0.048 * a / (2 * math.pi) + 0.005 * math.sin(a * 3.0)
        pts.append((r * math.cos(a), r * math.sin(a), rc))
    xe, ye, _ = pts[-1]
    tail = [(xe + 0.005, ye - 0.03, rc), (xe + 0.0, ye - 0.06, 0.02), (xe - 0.006, ye - 0.095, 0.016), (xe - 0.01, ye - 0.12, rc)]
    sweep("Cord", pts + tail, rc, cordm, seg=8)
    sphere("Knot", 0.019, (pts[0][0], pts[0][1], 0.017), cordm, seg=10, rings=6, scale=(1.2, 1.0, 0.9))
    sweep("CordEnd", [(pts[0][0], pts[0][1], rc), (pts[0][0] + 0.02, pts[0][1] - 0.035, rc), (pts[0][0] + 0.01, pts[0][1] - 0.06, rc)],
          lambda t: rc * (1 - 0.3 * t), cordm, seg=8)
    bone = flat("BoneBead", (0.66, 0.6, 0.47), 0.45, dirt=0.6)
    iron = iron_fine((0.2, 0.2, 0.21))
    sphere("BeadBone", 0.022, (xe + 0.0, ye - 0.06, 0.022), bone, seg=12, rings=8, scale=(1, 1.15, 1))
    sphere("BeadIron", 0.016, (xe - 0.006, ye - 0.095, 0.016), iron, seg=12, rings=6)
    # the fang: a curved, slightly flattened cone, yellowed at the root, ivory at the tip
    tooth = flat("Fang", (0.74, 0.68, 0.54), 0.32, dirt=0.55)
    nt = tooth.node_tree
    d = nt.nodes.new("ShaderNodeVectorMath"); d.operation = "LENGTH"
    nt.links.new(_coords(nt), d.inputs[0])
    g = nt.nodes.new("ShaderNodeMapRange")
    g.inputs["From Min"].default_value, g.inputs["From Max"].default_value = 0.02, 0.16
    nt.links.new(d.outputs["Value"], g.inputs["Value"])
    src, dst = _colour_in(tooth)
    nt.links.new(_mix_rgb(nt, g.outputs["Result"], (0.36, 0.25, 0.13), src), dst)
    L, phi = 0.27, 0.75
    Rc = L / phi
    s = _mark()
    cpts = []
    for k in range(17):
        t = k / 16
        cpts.append((Rc * math.sin(phi * t), -Rc * (1 - math.cos(phi * t)), 0.031 - 0.02 * t))
    sweep("Fang", cpts, lambda t: 0.039 * (1 - t) ** 0.75 + 0.0015, tooth, seg=12, flat_k=0.78)
    wire = iron_fine((0.24, 0.24, 0.25))
    for k in range(3):
        hoop(f"Wrap{k}", (0.007 + k * 0.01, 0, 0.031), 0.04, "X", wire, thick=0.004)
    cyl("Cap", 0.04, 0.022, (-0.007, 0, 0.031), wire, rot=(0, math.pi / 2, 0), verts=14, bevel=0.003)
    hoop("Bail", (-0.034, 0, 0.031), 0.019, "Y", wire, thick=0.005)
    _xform(s, Matrix.Translation((xe + 0.012, ye - 0.16, 0)) @ Matrix.Rotation(math.radians(-70), 4, "Z"))
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the hymnal
def lost_hymnal(M):
    W, D, T = 0.5, 0.7, 0.12
    hide = leather("HymnalLeather", (0.055, 0.008, 0.014), scale=5.0, wear=0.16)
    gl = frame_gilt()
    edge = pages("GiltEdges", (0.72, 0.52, 0.2), metal=1.0, rough=0.32)
    ct = 0.014
    for nm, z in (("CoverB", ct / 2), ("CoverT", T - ct / 2)):
        box(nm, (W, D, ct), (0.0, 0, z), hide, bevel=0.005)
    box("Pages", (W - 0.032, D - 0.026, T - 2 * ct + 0.002), (0.012, 0, T / 2), edge, bevel=0.002)
    # a rounded spine, flattened to a shallow curve (not a roll)
    cyl("Spine", T / 2, D, (-W / 2 + 0.014, 0, T / 2), hide, rot=(math.pi / 2, 0, 0), verts=18, bevel=0.003).scale = (0.5, 1, 1)
    for k, y in enumerate((-0.22, -0.075, 0.075, 0.22)):
        cyl(f"RaisedBand{k}", T / 2 + 0.005, 0.016, (-W / 2 + 0.014, y, T / 2), gl, rot=(math.pi / 2, 0, 0), verts=18, bevel=0.003).scale = (0.5, 1, 1)
    # a gilt cross pattee and a gilt border on the front cover
    c, e = 0.012, 0.032
    Lu, Ld, Lr = 0.095, 0.16, 0.085
    cross = [(c, -c), (Lr, -e), (Lr, e), (c, c), (e, Lu), (-e, Lu), (-c, c), (-Lr, e), (-Lr, -e), (-c, -c), (-e, -Ld), (e, -Ld)]
    cx, cy = 0.02, 0.03
    B20.tprism("Cross", [(cx + x, cy + y) for x, y in cross], T - 0.002, 0.006, gl, plane="XY", bevel=0.0015)
    hw, hd = W / 2 - 0.05, D / 2 - 0.04
    tube("Border", [(cx - hw + 0.005, -hd, T + 0.001), (cx + hw - 0.01, -hd, T + 0.001), (cx + hw - 0.01, hd, T + 0.001), (cx - hw + 0.005, hd, T + 0.001)],
         0.0035, gl, closed=True, square=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B20.tprism(f"Fleuron{sx}{sy}", _star(cx + sx * (hw - 0.03), sy * (hd - 0.03), 0.018, 0.007, n=4, rot=math.pi / 4), T - 0.001, 0.004, gl,
                       plane="XY", bevel=0.001)
    # a gilt clasp over the fore-edge, two ribbons out of the foot onto the floor
    box("ClaspTop", (0.07, 0.05, 0.005), (W / 2 - 0.03, 0, T + 0.002), gl, bevel=0.0015)
    box("ClaspEdge", (0.006, 0.05, T + 0.006), (W / 2 + 0.003, 0, T / 2), gl, bevel=0.0015)
    sphere("ClaspStud", 0.011, (W / 2 - 0.05, 0, T + 0.004), gl, seg=10, rings=5, scale=(1, 1, 0.6))
    satin = flat("RibbonBone", (0.66, 0.6, 0.47), 0.45, dirt=0.4)
    for k, (x, mat, L) in enumerate(((-0.04, velvet(), 0.16), (0.06, satin, 0.12))):
        strip(f"Ribbon{k}", [(x, -D / 2 + 0.03, T * 0.55), (x, -D / 2 - 0.012, T * 0.4), (x + 0.004, -D / 2 - 0.04, 0.006), (x + 0.015, -D / 2 - 0.08, 0.002),
                             (x + 0.03 + k * 0.02, -D / 2 - L, 0.002)], 0.02, (1, 0, 0), mat, thick=0.003, it=2)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the lunch tin
def lost_lunch_tin(M):
    rnd = random.Random(2406)
    tin = flat("Tinplate", (0.38, 0.38, 0.39), 0.42, metal=1.0, wear=0.0, dirt=0.9)
    nt = tin.node_tree
    next(n for n in nt.nodes if n.type == "BUMP").inputs["Strength"].default_value = 0.0    # a metal shows every ripple
    # soft handling smudges in the roughness (no fine speckle: on a metal it glitters), a few rust spots
    sm = nt.nodes.new("ShaderNodeTexNoise"); sm.inputs["Scale"].default_value = 5.0; sm.inputs["Detail"].default_value = 3
    nt.links.new(_coords(nt), sm.inputs["Vector"])
    src, dst = _rough_in(tin)
    nt.links.new(_math(nt, "ADD", src, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", sm.outputs["Fac"], 0.4, clamp=True), 0.35)), dst)
    splatter(tin, (0.15, 0.06, 0.028), scale=6.0, rough=0.85, metal=0.0, blob=0.69, region=0.62, drops=0.02, seed=2.0, detail=4.0)
    hw, hd, r = 0.42, 0.25, 0.08
    body = rbox("Body", hw, hd, r, 0.0, 0.3, tin, step=0.03, rows=10, bevel=0.01, top=False)
    lid = rbox("Lid", hw + 0.012, hd + 0.012, r + 0.012, 0.28, 0.4, tin, step=0.03, rows=4, bevel=0.016)
    # dents: one in the front, one at the front-right corner, one in the lid's back corner
    dent(body, (0.16, -hd, 0.15), 0.1, 0.034, (0, 1, 0))
    dent(body, (-0.22, -hd, 0.21), 0.06, 0.018, (0, 1, 0))
    dent(body, (hw - 0.02, -hd + 0.02, 0.07), 0.08, 0.026, (-1, 1, 0.2))
    dent(lid, (-0.28, hd + 0.012, 0.35), 0.085, 0.017, (0, -1, 0))
    ring = [(p[0], p[1], 0.0) for p in rrect(hw + 0.004, hd + 0.004, r + 0.004, 0, n=5)]
    tube("FootBead", [(x, y, 0.012) for x, y, _ in ring], 0.007, tin, closed=True, poly=True)
    ring = [(p[0], p[1], 0.0) for p in rrect(hw + 0.016, hd + 0.016, r + 0.016, 0, n=5)]
    tube("LidBead", [(x, y, 0.285) for x, y, _ in ring], 0.007, tin, closed=True, poly=True)
    # the folding wire handle, lying back on the lid, in two lugs
    wire = iron_fine((0.22, 0.22, 0.23))
    for sx in (-1, 1):
        box(f"Lug{sx}", (0.04, 0.03, 0.02), (sx * 0.22, 0.17, 0.41), tin, bevel=0.006)
    tube("Handle", [(-0.235, 0.17, 0.416), (-0.215, 0.235, 0.414), (-0.12, 0.25, 0.414), (0.12, 0.25, 0.414), (0.215, 0.235, 0.414), (0.235, 0.17, 0.416)],
         0.008, wire)
    cyl("Grip", 0.016, 0.22, (0, 0.249, 0.416), flat("Grip", (0.03, 0.028, 0.03), 0.6), rot=(0, math.pi / 2, 0), verts=12, bevel=0.004)
    # a hasp over the front seam, hinges at the back
    box("Hasp", (0.07, 0.01, 0.1), (0, -hd - 0.018, 0.29), tin, bevel=0.003)
    hoop("HaspLoop", (0, -hd - 0.024, 0.24), 0.014, "Y", wire, thick=0.004)
    sphere("HaspStud", 0.012, (0, -hd - 0.006, 0.235), tin, seg=10, rings=5, scale=(1, 0.7, 1))
    for sx in (-1, 1):
        cyl(f"Hinge{sx}", 0.011, 0.1, (sx * 0.24, hd + 0.016, 0.29), tin, rot=(0, math.pi / 2, 0), verts=10, bevel=0.002)
    # the painted label on the lid: bone with a crimson border, hand-painted LUNCH
    paint_b = flat("LabelPaint", (0.6, 0.55, 0.43), 0.55, dirt=0.5)
    paint_c = flat("LabelCrimson", CRIMSON, 0.45, dirt=0.4)
    lab = [(p[0] + 0.04, p[1] - 0.04) for p in rrect(0.17, 0.075, 0.025, 0, n=4)]
    B20.tprism("Label", lab, 0.399, 0.004, paint_b, plane="XY")
    tube("LabelBorder", [(x, y, 0.4035) for x, y in [(p[0] + 0.04, p[1] - 0.04) for p in rrect(0.155, 0.06, 0.018, 0, n=4)]], 0.0035, paint_c,
         closed=True, poly=True)
    _text("LabelText", "LUNCH", FONT_SIGN, paint_c, lambda x, y, h: (0.04 + x, -0.04 + y, 0.403 + h), fit=(0.22, 0.07), depth=0.002)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the pocket watch
def dial_mat():
    """Bone enamel with the hour batons, the minute track and its rings painted on (the dial is centred at the origin)."""
    m = flat("Dial", (0.76, 0.72, 0.62), 0.28, dirt=0.35)
    nt = m.node_tree
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(_coords(nt), sep.inputs["Vector"])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    r = _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", x, x), _math(nt, "MULTIPLY", y, y)))
    a = _math(nt, "ARCTAN2", y, x)

    def ticks(n, w):
        k = _math(nt, "MULTIPLY", a, n / (2 * math.pi))
        return _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", k, _math(nt, "ROUND", k))), w)

    def band(r0, r1):
        return _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", r, r0), _math(nt, "LESS_THAN", r, r1))

    ink = _math(nt, "MULTIPLY", ticks(12, 0.055), band(0.093, 0.119))
    ink = _math(nt, "MAXIMUM", ink, _math(nt, "MULTIPLY", ticks(4, 0.03), band(0.083, 0.119)))
    ink = _math(nt, "MAXIMUM", ink, _math(nt, "MULTIPLY", ticks(60, 0.12), band(0.112, 0.12)))
    ink = _math(nt, "MAXIMUM", ink, band(0.1195, 0.1215))
    ink = _math(nt, "MAXIMUM", ink, band(0.1105, 0.1115))
    _paint(m, ink, (0.025, 0.024, 0.028), rough=0.4)
    return m


def lost_pocket_watch(M):
    rnd = random.Random(2407)
    # polished brass (the school's brass set is too tarnished for a watch held in the hand): clean, rubbed bright on the
    # edges, dark only in the crevices
    br = P.material("WatchBrass", base=(0.74, 0.53, 0.23), rough=0.24, metal=1.0, wear=0.15, dirt=0.75)
    R = 0.162
    _recalc(lathe("Case", [(0, 0), (0.1, 0.0), (0.14, 0.008), (0.157, 0.021), (R, 0.035), (0.159, 0.05), (0.15, 0.058), (0.143, 0.068), (0.136, 0.07),
                           (0.134, 0.062), (0, 0.062)], br, seg=40))
    hoop("Milling", (0, 0, 0.036), R + 0.001, "Z", br, thick=0.0035)
    _recalc(lathe("DialDisc", [(0, 0.0595), (0.134, 0.0595), (0.134, 0.0635), (0, 0.0635)], dial_mat(), seg=40))
    blk = flat("Blued", (0.015, 0.018, 0.04), 0.25, metal=0.6, dirt=0.2)
    # spade hands stopped at ten past ten-ish, a seconds sub-dial at six
    def hand(name, pts, ang, z, c=(0.0, 0.0)):
        ca, sa = math.cos(ang), math.sin(ang)
        B20.tprism(name, [(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca) for x, y in pts], z, 0.0025, blk, plane="XY")
    hand("HourHand", [(-0.02, -0.004), (0.0, -0.0045), (0.045, -0.003), (0.055, -0.009), (0.072, 0.0), (0.055, 0.009), (0.045, 0.003), (0.0, 0.0045),
                      (-0.02, 0.004)], math.radians(150), 0.0635)
    hand("MinuteHand", [(-0.025, -0.0032), (0.098, -0.0015), (0.106, 0.0), (0.098, 0.0015), (-0.025, 0.0032)], math.radians(42), 0.0661)
    cyl("HandBoss", 0.007, 0.006, (0, 0, 0.067), br, verts=12, bevel=0.0015)
    hoop("SubDial", (0, -0.062, 0.0637), 0.026, "Z", blk, thick=0.0011)
    hand("SecondHand", [(-0.004, -0.0012), (0.022, -0.0006), (0.022, 0.0006), (-0.004, 0.0012)], math.radians(-30), 0.0636, c=(0.0, -0.062))
    # the face cracked from a blow near four o'clock (pale glass cracks lying over the dial)
    crack = flat("GlassCrack", (0.85, 0.86, 0.88), 0.2, dirt=0.0)
    _cracks("Crack", 0.045, -0.04, 0.0695, crack, rnd, lambda x, y: x * x + y * y < 0.128 ** 2, rays=8, reach=0.13, r=0.0016)
    # the pendant, crown and bow, then the chain
    cyl("Pendant", 0.011, 0.024, (0, R + 0.008, 0.035), br, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.002)
    cyl("Crown", 0.019, 0.022, (0, R + 0.03, 0.035), br, rot=(math.pi / 2, 0, 0), verts=16, bevel=0.003)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        box(f"Knurl{k}", (0.004, 0.022, 0.004), (math.cos(a) * 0.019, R + 0.03, 0.035 + math.sin(a) * 0.019), br, bevel=0.0, segments=1,
            rot=(0, -a, 0))
    bow_c = (0, R + 0.075, 0.024)
    tube("Bow", circle_pts(bow_c[0], bow_c[1], bow_c[2], 0.036, "Z", 16, tilt=-0.5), 0.0055, br, closed=True, poly=True)
    # the lid, hinged on the left and standing open past upright
    s = _mark()
    _recalc(lathe("Lid", [(0, 0.0), (0.15, 0.0), (R, 0.006), (0.158, 0.016), (0.12, 0.027), (0.06, 0.033), (0, 0.035)], br, seg=40, loc=(R, 0, 0)))
    hoop("LidEngrave", (R, 0, -0.0005), 0.125, "Z", br, thick=0.0016)
    cyl("Knuckle", 0.011, 0.07, (0, 0, 0.003), br, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.002)
    _xform(s, Matrix.Translation((-R - 0.002, 0, 0.066)) @ Matrix.Rotation(math.radians(-102), 4, "Y"))
    # the chain: alternating flat and upright oval links coiled round the front and right, a T-bar and a fob
    path = _smooth([(0.0, bow_c[1] + 0.036 * math.cos(0.5), 0), (0.17, 0.36, 0), (0.38, 0.28, 0), (0.47, 0.06, 0), (0.41, -0.15, 0), (0.24, -0.27, 0),
                    (0.04, -0.3, 0), (-0.13, -0.26, 0), (-0.2, -0.33, 0), (-0.12, -0.42, 0)], it=3)
    V = [Vector(p) for p in path]
    cum = [0.0]
    for a, b in zip(V, V[1:]):
        cum.append(cum[-1] + (b - a).length)
    pitch, Rl, rl = 0.027, 0.0135, 0.0048
    n = int(cum[-1] / pitch)
    j = 0
    up = Vector((0, 0, 1))
    for k in range(n + 1):
        sk = k * pitch
        while j < len(cum) - 2 and cum[j + 1] < sk:
            j += 1
        tt = (sk - cum[j]) / max(1e-9, cum[j + 1] - cum[j])
        p = V[j].lerp(V[j + 1], tt)
        t = (V[j + 1] - V[j]).normalized()
        sideways = up.cross(t)
        if k % 2 == 0:
            mtx = Matrix(((t.x, sideways.x, 0, p.x), (t.y, sideways.y, 0, p.y), (0, 0, 1, rl), (0, 0, 0, 1)))
        else:
            zc = t.cross(up)
            mtx = Matrix(((t.x, 0, zc.x, p.x), (t.y, 0, zc.y, p.y), (0, 1, zc.z, Rl + rl - 0.001), (0, 0, 0, 1)))
        torus(f"Link{k}", mtx, Rl, rl, br, sx=1.45)
    end = V[-1]
    tdir = (V[-1] - V[-2]).normalized()
    side = up.cross(tdir)
    tube("TBar", [tuple(end + tdir * 0.012 - side * 0.045 + Vector((0, 0, 0.006))), tuple(end + tdir * 0.012 + side * 0.045 + Vector((0, 0, 0.006)))],
         0.0055, br, poly=True)
    sphere("TBarEnd0", 0.008, tuple(end + tdir * 0.012 - side * 0.047 + Vector((0, 0, 0.006))), br, seg=8, rings=4)
    sphere("TBarEnd1", 0.008, tuple(end + tdir * 0.012 + side * 0.047 + Vector((0, 0, 0.006))), br, seg=8, rings=4)
    fob = end + tdir * 0.03 + side * 0.085
    lathe("Fob", [(0, 0), (0.026, 0), (0.03, 0.004), (0.028, 0.008), (0, 0.009)], br, seg=20, loc=(fob.x, fob.y, 0))
    lathe("FobSeal", [(0, 0.008), (0.02, 0.008), (0.018, 0.012), (0, 0.0125)], flat("FobWax", CRIMSON, 0.3, dirt=0.4), seg=20,
          loc=(fob.x, fob.y, 0))
    rg = end + tdir * 0.012 + side * 0.047
    tube("FobLink", [(rg.x, rg.y, 0.006), ((rg.x + fob.x) / 2, (rg.y + fob.y) / 2, 0.005), (fob.x - side.x * 0.028, fob.y - side.y * 0.028, 0.005)],
         0.003, br, poly=True)
    _fine(0.3)
    _settle()
    return _dims()


def _crescent(name, O, I, z0, depth, mat):
    """A flat crescent from z0 up `depth`, built as an explicit strip between the outer arc O (tip to tip, n points) and
    the inner arc I (n - 2 points, the same direction, tips excluded), so its horns never fill in."""
    bm = bmesh.new()
    rows = {}
    for side, z in (("b", z0), ("t", z0 + depth)):
        rows[side] = ([bm.verts.new((x, y, z)) for x, y in O], [bm.verts.new((x, y, z)) for x, y in I])
    for side in ("b", "t"):
        o, i = rows[side]
        fs = [(o[0], o[1], i[0])] + [(o[k], o[k + 1], i[k], i[k - 1]) for k in range(1, len(I))] + [(o[-2], o[-1], i[-1])]
        for f in fs:
            bm.faces.new(f if side == "t" else tuple(reversed(f)))
    loop_b = rows["b"][0] + list(reversed(rows["b"][1]))
    loop_t = rows["t"][0] + list(reversed(rows["t"][1]))
    for k in range(len(loop_b)):
        j = (k + 1) % len(loop_b)
        bm.faces.new((loop_b[k], loop_b[j], loop_t[j], loop_t[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


# ================================================================== the phone
def lost_phone(M):
    rnd = random.Random(2408)
    case = flat("PhoneCase", (0.05, 0.05, 0.056), 0.6, wear=0.25, dirt=0.6)
    nt = case.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 220; nz.inputs["Detail"].default_value = 2
    nt.links.new(_coords(nt), nz.inputs["Vector"])
    _bump(case, nz.outputs["Fac"], 0.0006)
    glass = flat("PhoneGlass", (0.011, 0.011, 0.015), 0.06, dirt=0.05)
    hw, hd, T = 0.17, 0.35, 0.036
    z0 = 0.009
    rbox("Case", hw, hd, 0.055, z0, z0 + T, case, step=0.04, rows=3, bevel=0.009)
    rbox("Screen", hw - 0.016, hd - 0.016, 0.042, z0 + T - 0.004, z0 + T + 0.0022, glass, step=0.04, rows=1, bevel=0.0015)
    zt = z0 + T + 0.0022
    blk = flat("PhoneBlack", (0.004, 0.004, 0.005), 0.4)
    box("Speaker", (0.06, 0.006, 0.001), (0, hd - 0.03, zt + 0.0002), blk, bevel=0.0, segments=1)
    sphere("FrontCam", 0.006, (0.05, hd - 0.03, zt), blk, seg=10, rings=4, scale=(1, 1, 0.3))
    steel = flat("PhoneSteel", (0.5, 0.5, 0.52), 0.25, metal=1.0)
    for k, (y, L) in enumerate(((0.14, 0.07), (0.04, 0.05))):
        box(f"Button{k}", (0.008, L, 0.012), (hw + 0.002, y, z0 + T / 2), steel, bevel=0.003)
    box("Port", (0.04, 0.006, 0.008), (0, -hd - 0.001, z0 + T / 2), blk, bevel=0.002)
    # the camera bump and lenses on the back
    rbox("CamBump", 0.06, 0.06, 0.026, 0.0, z0 + 0.002, case, cx=-hw + 0.085, cy=hd - 0.085, step=0.03, rows=1, bevel=0.003)
    for k, (dx, dy) in enumerate(((-0.022, 0.022), (0.022, -0.022))):
        cyl(f"LensRing{k}", 0.019, 0.004, (-hw + 0.085 + dx, hd - 0.085 + dy, 0.0), steel, verts=16, bevel=0.001)
        cyl(f"Lens{k}", 0.014, 0.004, (-hw + 0.085 + dx, hd - 0.085 + dy, -0.0012), glass, verts=16, bevel=0.001)
    # the screen cracked from a knock on the top-left corner
    crack = flat("ScreenCrack", (0.62, 0.65, 0.7), 0.15, dirt=0.0)
    ix, iy = -hw + 0.05, hd - 0.075
    _cracks("Crack", ix, iy, zt + 0.0012, crack, rnd, lambda x, y: abs(x) < hw - 0.02 and abs(y) < hd - 0.02, rays=10, reach=0.42, r=0.0013,
            rings=(0.03, 0.07, 0.12))
    # the lanyard eyelet, a black cord loop and a crimson enamel crescent charm with a brass rim
    ex, ey = -hw + 0.022, -hd + 0.01
    hoop("Eyelet", (ex - 0.012, ey - 0.012, z0 + T / 2), 0.012, "Z", steel, thick=0.004)
    cordm = flat("CharmCord", (0.02, 0.019, 0.021), 0.55)
    tube("Cord", [(ex - 0.012, ey - 0.024, z0 + T / 2), (ex - 0.05, ey - 0.06, 0.008), (ex - 0.1, ey - 0.11, 0.005), (ex - 0.12, ey - 0.15, 0.005),
                  (ex - 0.085, ey - 0.13, 0.005), (ex - 0.04, ey - 0.075, 0.008)], 0.0045, cordm, closed=True)
    sphere("CordBead", 0.011, (ex - 0.075, ey - 0.088, 0.011), flat("BeadCrimson", CRIMSON, 0.25, dirt=0.3), seg=10, rings=6)
    enamel = flat("CharmEnamel", CRIMSON, 0.22, dirt=0.4)
    Rm = 0.055
    # a slim crescent: the outer circle between tips at +-125 degrees, the inner arc a circle through both tips centred
    # a quarter radius to the left
    outer = [(Rm * math.cos(math.radians(a)), Rm * math.sin(math.radians(a))) for a in [-125 + 250 * k / 20 for k in range(21)]]
    tipx, tipy = Rm * math.cos(math.radians(125)), Rm * math.sin(math.radians(125))
    ci = -0.25 * Rm
    ri = math.hypot(tipx - ci, tipy)
    ai = math.atan2(tipy, tipx - ci)
    # the inner arc runs upper tip -> lower tip, sampled to pair with the outer arc's points (for the strip below)
    inner = [(ci + ri * math.cos(ai - 2 * ai * k / 20), ri * math.sin(ai - 2 * ai * k / 20)) for k in range(1, 20)]
    moon = outer + inner
    rp = (ex - 0.125, ey - 0.158)                     # the jump ring
    rot = math.radians(35)

    def rx_(x, y):
        return x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
    tx, ty = rx_(tipx, tipy)                          # the crescent's upper tip hangs from the ring
    mx, my = rp[0] - tx - 0.006, rp[1] - ty - 0.012
    moon = [(mx + rx_(x, y)[0], my + rx_(x, y)[1]) for x, y in moon]
    _crescent("Charm", moon[:21], list(reversed(moon[21:])), 0.0, 0.014, enamel)
    tube("CharmRim", [(x, y, 0.0135) for x, y in moon], 0.0028, brass_fine(), closed=True, poly=True)
    hoop("JumpRing", (rp[0], rp[1], 0.006), 0.011, "Z", brass_fine(), thick=0.0028)
    _fine(0.3)
    _settle()
    return _dims()


# ================================================================== the Lost & Found box
def lost_found_box(M):
    rnd = random.Random(2409)
    oak = P.material("ChestOak", "NH_DeskWood", tint=(0.125, 0.072, 0.044), scale=0.35, rough_add=0.08, wear=0.35, dirt=0.9)
    oakin = P.material("ChestOakIn", "NH_DeskWood", tint=(0.085, 0.052, 0.034), scale=0.35, rough_add=0.1, wear=0.2, dirt=0.9)
    iron, brass = M["iron"], M["brass"]
    seam = flat("Seam", (0.018, 0.012, 0.009), 0.9)
    W, D, Z0, Z1, wt = 2.4, 1.2, 0.12, 1.3, 0.08
    hy = D / 2
    # body: floor and walls (hollow, the heap shows over the rim), plank seams
    box("Floor", (W, D, 0.08), (0, 0, Z0 + 0.04), oak, bevel=0.015, segments=1)
    for sy in (-1, 1):
        box(f"Wall{sy}", (W, wt, Z1 - Z0), (0, sy * (hy - wt / 2), (Z0 + Z1) / 2), oak, bevel=0.015, segments=1)
        for k in (1, 2):
            box(f"SeamFB{sy}{k}", (W - 0.04, 0.006, 0.014), (0, sy * (hy + 0.001), Z0 + (Z1 - Z0) * k / 3), seam, bevel=0.0, segments=1)
    for sx in (-1, 1):
        box(f"Side{sx}", (wt, D - 2 * wt, Z1 - Z0), (sx * (W / 2 - wt / 2), 0, (Z0 + Z1) / 2), oak, bevel=0.015, segments=1)
        for k in (1, 2):
            box(f"SeamS{sx}{k}", (0.006, D - 0.04, 0.014), (sx * (W / 2 + 0.001), 0, Z0 + (Z1 - Z0) * k / 3), seam, bevel=0.0, segments=1)
    # iron bands round the foot and the rim, vertical straps on the front and back
    bt, bh = 0.03, 0.12
    for z in (Z0 + bh / 2, Z1 - bh / 2):
        for sy in (-1, 1):
            box(f"BandFB{z:.1f}{sy}", (W + 2 * bt, bt, bh), (0, sy * (hy + bt / 2), z), iron, bevel=0.008, segments=1)
        for sx in (-1, 1):
            box(f"BandS{z:.1f}{sx}", (bt, D, bh), (sx * (W / 2 + bt / 2), 0, z), iron, bevel=0.008, segments=1)
    rivet = lambda nm, p: sphere(nm, 0.019, p, iron, seg=6, rings=3, scale=(1, 0.6, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Strap{sx}{sy}", (0.12, 2 * bt, Z1 - Z0), (sx * 0.75, sy * (hy + bt), (Z0 + Z1) / 2), iron, bevel=0.008, segments=1)
            if sy < 0:
                for k in range(5):
                    rivet(f"StrapRivet{sx}{k}", (sx * 0.75, -(hy + bt * 2 + 0.002), Z0 + 0.06 + k * (Z1 - Z0 - 0.12) / 4))
    # brass corners top and bottom on every vertical edge, with a boss
    ct, ch = 0.035, 0.22
    for sx in (-1, 1):
        for sy in (-1, 1):
            for zc in (Z0 + ch / 2, Z1 - ch / 2):
                ox, oy = W / 2 + bt + ct, hy + bt + ct
                box(f"CornerF{sx}{sy}{zc:.1f}", (0.22, ct, ch), (sx * (ox - 0.11), sy * (oy - ct / 2), zc), brass, bevel=0.008, segments=1)
                box(f"CornerS{sx}{sy}{zc:.1f}", (ct, 0.2, ch), (sx * (ox - ct / 2), sy * (oy - 0.1), zc), brass, bevel=0.008, segments=1)
                sphere(f"CornerBoss{sx}{sy}{zc:.1f}", 0.026, (sx * (ox - 0.1), sy * (oy + 0.004), zc), brass, seg=8, rings=4, scale=(1, 0.6, 1))
    # brass bun feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Foot{sx}{sy}", [(0, 0), (0.085, 0), (0.11, 0.035), (0.1, 0.085), (0.075, Z0), (0, Z0)], brass, seg=16,
                  loc=(sx * (W / 2 - 0.12), sy * (hy - 0.12), 0))
    # the lock plate, keyhole and staple on the front
    yl = -(hy + 0.075)                 # the lock plate's face
    box("LockPlate", (0.34, 0.075, 0.4), (0, yl + 0.0375, Z1 - 0.26), iron, bevel=0.01, segments=1)
    ye = yl - 0.012
    box("Escutcheon", (0.13, 0.014, 0.18), (0, yl - 0.005, Z1 - 0.3), brass, bevel=0.006, segments=1)
    dark = flat("Keyhole", (0.008, 0.007, 0.007), 0.9)
    sphere("KeyholeTop", 0.022, (0, ye, Z1 - 0.27), dark, seg=10, rings=5, scale=(1, 0.4, 1))
    B20.tprism("KeyholeSlot", [(-0.012, Z1 - 0.28), (0.012, Z1 - 0.28), (0.022, Z1 - 0.35), (-0.022, Z1 - 0.35)], ye - 0.001, 0.006, dark)
    for k, (x, z) in enumerate(((-0.13, Z1 - 0.1), (0.13, Z1 - 0.1), (-0.13, Z1 - 0.42), (0.13, Z1 - 0.42))):
        rivet(f"LockRivet{k}", (x, yl, z))
    hoop("Staple", (0, yl - 0.028, Z1 - 0.1), 0.03, "X", iron, thick=0.01)
    # iron drop handles on the sides
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.05)
        box(f"HandlePlate{sx}", (0.05, 0.28, 0.12), (sx * (W / 2 + 0.025), 0, Z1 - 0.32), iron, bevel=0.006, segments=1)
        tube(f"Handle{sx}", [(x + sx * 0.02, -0.11, Z1 - 0.3), (x + sx * 0.06, -0.12, Z1 - 0.42), (x + sx * 0.07, 0, Z1 - 0.47), (x + sx * 0.06, 0.12, Z1 - 0.42),
                             (x + sx * 0.02, 0.11, Z1 - 0.3)], 0.022, iron)
    # body hinge leaves and knuckles on the back
    for sx in (-1, 1):
        box(f"HingeLeaf{sx}", (0.12, 0.055, 0.26), (sx * 0.42, hy + 0.0275, Z1 - 0.14), iron, bevel=0.006, segments=1)
        cyl(f"HingeKnuckle{sx}", 0.035, 0.16, (sx * 0.42, hy + 0.05, Z1), iron, rot=(0, math.pi / 2, 0), verts=12, bevel=0.006)

    # the lid, built closed and swung open about its back hinge
    s = _mark()
    LT = 0.2
    box("LidTop", (W + 0.06, D + 0.06, 0.07), (0, 0, Z1 + LT - 0.035), oak, bevel=0.02, segments=1)
    box("LidUnder", (W - 0.06, D - 0.06, 0.012), (0, 0, Z1 + LT - 0.076), oakin, bevel=0.0, segments=1)
    for sy in (-1, 1):
        box(f"LidSkirt{sy}", (W + 0.06, 0.06, LT - 0.07), (0, sy * (hy + 0.0), Z1 + (LT - 0.07) / 2), oak, bevel=0.012, segments=1)
    for sx in (-1, 1):
        box(f"LidSkirtS{sx}", (0.06, D - 0.06, LT - 0.07), (sx * (W / 2), 0, Z1 + (LT - 0.07) / 2), oak, bevel=0.012, segments=1)
    for sy in (-1, 1):
        box(f"LidBand{sy}", (W + 0.1, bt, LT - 0.04), (0, sy * (hy + 0.03 + bt / 2), Z1 + (LT - 0.04) / 2), iron, bevel=0.008, segments=1)
    for sx in (-1, 1):
        box(f"LidBandS{sx}", (bt, D + 0.12, LT - 0.04), (sx * (W / 2 + 0.03 + bt / 2), 0, Z1 + (LT - 0.04) / 2), iron, bevel=0.008, segments=1)
        box(f"LidStrap{sx}", (0.12, D + 0.14, bt), (sx * 0.75, 0, Z1 + LT + bt / 2), iron, bevel=0.008, segments=1)
        for k in range(5):
            rivet(f"LidRivet{sx}{k}", (sx * 0.75, -hy + 0.05 + k * (D - 0.1) / 4, Z1 + LT + bt + 0.002))
        box(f"HingeStrap{sx}", (0.1, 0.55, 0.025), (sx * 0.42, hy - 0.22, Z1 + LT + 0.012), iron, bevel=0.006, segments=1)
        for sy in (-1, 1):
            box(f"LidCorner{sx}{sy}", (0.24, 0.24, 0.036), (sx * (W / 2 - 0.08), sy * (hy - 0.08), Z1 + LT + 0.012), brass, bevel=0.008, segments=1)
    box("Hasp", (0.08, 0.02, 0.24), (0, -(hy + 0.07), Z1 - 0.04), iron, bevel=0.006, segments=1)
    box("HaspSlot", (0.035, 0.006, 0.06), (0, -(hy + 0.082), Z1 - 0.12), dark, bevel=0.0, segments=1)
    # a list of the lost things pasted inside the lid
    note = flat("Note", (0.62, 0.56, 0.43), 0.85, dirt=0.6)
    box("Note", (0.62, 0.44, 0.004), (-0.45, 0.02, Z1 + LT - 0.084), note, bevel=0.0, segments=1)
    inkm = flat("NoteInk", INK, 0.4)
    for k in range(6):
        L = 0.46 - 0.12 * rnd.random()
        box(f"NoteLine{k}", (L, 0.012, 0.002), (-0.45 - (0.46 - L) / 2, 0.17 - k * 0.06, Z1 + LT - 0.0868), inkm, bevel=0.0, segments=1)
    for k, x in enumerate((-0.71, -0.19)):
        sphere(f"NoteTack{k}", 0.014, (x, 0.2, Z1 + LT - 0.088), brass, seg=8, rings=4, scale=(1, 1, 0.5))
    ang = math.radians(-100)
    hinge = Vector((0, hy + 0.05, Z1))
    _xform(s, Matrix.Translation(hinge) @ Matrix.Rotation(ang, 4, "X") @ Matrix.Translation(-hinge))
    # the lid stay (an iron bar from the right wall up to the lid)
    lp = Matrix.Translation(hinge) @ Matrix.Rotation(ang, 4, "X") @ Matrix.Translation(-hinge) @ Vector((W / 2 - 0.12, 0.2, Z1 + 0.1))
    b0 = Vector((W / 2 - 0.12, 0.2, Z1 - 0.22))
    tube("Stay", [tuple(b0), tuple((b0 + lp) / 2 + Vector((0.0, 0.03, 0.0))), tuple(lp)], 0.018, iron, poly=True)
    for p in (b0, lp):
        sphere(f"StayPin{p.z:.1f}", 0.03, tuple(p), iron, seg=8, rings=4)

    # the heap of lost things filling the chest
    # a bed of cloth, then folded jumpers and a coat on it
    sphere("HeapBed", 1.0, (0, 0, 0.8), cloth("HeapInk", (0.03, 0.04, 0.1), rough=0.85), seg=16, rings=8, scale=(1.1, 0.5, 0.33))
    sphere("Coat", 0.55, (0.35, -0.1, 1.0), cloth("Coat", (0.045, 0.045, 0.05), rough=0.8), seg=16, rings=8, scale=(1.0, 0.72, 0.42))
    folds = [(-0.6, -0.22, 1.17, (0.66, 0.5, 0.14), 12, 5, wool("JumperGrey", (0.14, 0.14, 0.15))),
             (-0.06, 0.26, 1.2, (0.6, 0.44, 0.13), -18, -6, wool("JumperBone", BONE)),
             (0.8, 0.24, 1.16, (0.5, 0.42, 0.11), 28, 4, velvet()),
             (-0.86, 0.3, 1.1, (0.42, 0.36, 0.1), -8, 8, wool("JumperGrey2", (0.22, 0.21, 0.2))),
             (0.86, -0.28, 1.14, (0.42, 0.4, 0.1), 16, -5, wool("JumperGrey3", (0.1, 0.1, 0.11)))]
    for k, (x, y, z, sz, rz, rx, mat) in enumerate(folds):
        s = _mark()
        box(f"Fold{k}", sz, (0, 0, 0), mat, bevel=0.045, segments=2)
        box(f"FoldLayer{k}", (sz[0] * 0.98, sz[1] * 0.96, 0.012), (0, -0.01, sz[2] * 0.08), mat, bevel=0.004, segments=1)
        _xform(s, Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(rx), 4, "X"))
    # a bone knit glove draped over the front rim
    gw = wool("Glove", (0.6, 0.55, 0.45), rib=0.012)
    gx = -0.5
    sphere("Palm", 1.0, (gx, -0.36, 1.275), gw, seg=14, rings=8, scale=(0.15, 0.17, 0.045))
    sphere("Cuff", 1.0, (gx - 0.01, -0.17, 1.285), wool("GloveCuff", CRIMSON, rib=0.012), seg=14, rings=8, scale=(0.13, 0.07, 0.05))
    for k, (dx, L) in enumerate(((-0.09, 0.8), (-0.03, 1.0), (0.03, 0.95), (0.09, 0.72))):
        f = [(gx + dx, -0.45, 1.3), (gx + dx * 1.05, -0.56, 1.35), (gx + dx * 1.08, -0.65, 1.31), (gx + dx * 1.1, -0.68, 1.26 - 0.03 * L),
             (gx + dx * 1.1, -0.685, 1.2 - 0.1 * L)]
        sweep(f"Finger{k}", _smooth(f, 2), lambda t: 0.027 * (1 - 0.15 * t) * (1 - 0.55 * max(0.0, (t - 0.88) / 0.12) ** 2), gw, seg=7, flat_k=0.8,
              up=(0, -1, 0.3))
    sweep("Thumb", _smooth([(gx - 0.12, -0.36, 1.285), (gx - 0.19, -0.4, 1.295), (gx - 0.24, -0.46, 1.29)], 2), lambda t: 0.028 * (1 - 0.2 * t), gw,
          seg=8, flat_k=0.8)
    # a book's corner sticking up at the back left
    s = _mark()
    bk = leather("LostBook", (0.03, 0.045, 0.12), scale=1.5, wear=0.25)
    for sy in (-1, 1):
        box(f"BookCover{sy}", (0.56, 0.016, 0.76), (0, sy * 0.044, 0.38), bk, bevel=0.006, segments=1)
    box("BookPages", (0.53, 0.074, 0.73), (0.012, 0, 0.38), pages("BookPages", (0.64, 0.58, 0.45), line=0.005), bevel=0.003, segments=1)
    cyl("BookSpine", 0.052, 0.76, (-0.27, 0, 0.38), bk, verts=12, bevel=0.004)
    for k, z in enumerate((0.15, 0.6)):
        box(f"BookGilt{k}", (0.03, 0.108, 0.02), (-0.27, 0, z), gilt(), bevel=0.004, segments=1)
    _xform(s, Matrix.Translation((-0.36, 0.38, 0.92)) @ Matrix.Rotation(math.radians(14), 4, "Z") @ Matrix.Rotation(math.radians(10), 4, "X")
           @ Matrix.Rotation(math.radians(18), 4, "Y"))
    # a furled black umbrella leaning at the back right, its crook handle out
    s = _mark()
    canopy = cloth("Umbrella", (0.02, 0.02, 0.025), rough=0.6, weave=0.006)
    lathe("Canopy", [(0, 0.1), (0.012, 0.12), (0.055, 0.35), (0.075, 0.62), (0.06, 0.86), (0.03, 0.97), (0, 1.0)], canopy, seg=16, flute=(8, 0.25))
    cyl("Shaft", 0.012, 0.3, (0, 0, 1.12), iron, verts=8, bevel=0.0)
    tube("Crook", [(0, 0, 1.24), (0, 0, 1.36), (0.05, 0, 1.44), (0.11, 0, 1.42), (0.13, 0, 1.33), (0.115, 0, 1.28)], 0.024, oakin)
    cyl("Ferrule", 0.02, 0.05, (0, 0, 1.25), brass, verts=12, bevel=0.004)
    hoop("Strap", (0, 0, 0.62), 0.072, "Z", canopy, thick=0.012)
    sphere("Snap", 0.018, (0.08, 0, 0.62), brass, seg=8, rings=4, scale=(0.5, 1, 1))
    _xform(s, Matrix.Translation((0.7, 0.3, 0.45)) @ Matrix.Rotation(math.radians(-6), 4, "X") @ Matrix.Rotation(math.radians(12), 4, "Y")
           @ Matrix.Rotation(math.pi, 4, "Z"))
    # a striped scarf end hanging over the right side, fringed
    cr, bn = wool("ScarfCrimson", CRIMSON), wool("ScarfBone", BONE)
    sp = _smooth([(0.6, -0.3, 1.215), (0.85, -0.3, 1.205), (1.05, -0.3, 1.26), (1.17, -0.3, 1.35), (1.235, -0.3, 1.34), (1.27, -0.3, 1.27),
                  (1.278, -0.3, 1.1), (1.276, -0.3, 0.92), (1.274, -0.3, 0.78)], 2)
    striped_band("ScarfEnd", sp, 0.24, 0.03, SCARF_STRIPES, {"c": cr, "b": bn}, side=(0, 1, 0), ref=(1, 0, 0.4), puff=0.004, offset=0.05, ds=0.08,
                 fringe=("end",), tassel=0.09, droop=(0.0, 0.0), rnd=rnd, n_tassel=7)

    # the sign: a painted bone board on a two-post iron stand behind the chest
    ys, xs = 1.2, 1.29
    zb0, zb1 = 2.6, 3.4
    for sx in (-1, 1):
        x = sx * xs
        box(f"Post{sx}", (0.05, 0.05, 3.42), (x, ys, 1.71), iron, bevel=0.008, segments=1)
        box(f"PostFoot{sx}", (0.07, 0.36, 0.05), (x, ys, 0.025), iron, bevel=0.01, segments=1)
        for sy in (-1, 1):
            tube(f"Brace{sx}{sy}", [(x, ys + sy * 0.16, 0.05), (x, ys + sy * 0.07, 0.18), (x, ys + sy * 0.02, 0.32)], 0.016, iron)
        sphere(f"PostKnop{sx}", 0.04, (x, ys, 3.43), brass, seg=10, rings=6)
        cone(f"PostFinial{sx}", 0.028, 0.0, 0.08, (x, ys, 3.49), iron, verts=8)
        for z in (zb0 + 0.12, zb1 - 0.12):
            box(f"Bracket{sx}{z:.1f}", (0.1, 0.06, 0.05), (sx * (xs - 0.05), ys - 0.02, z), iron, bevel=0.006, segments=1)
    box("CrossBar", (2 * xs, 0.035, 0.035), (0, ys, 1.75), iron, bevel=0.006, segments=1)
    board = P.material("SignBoard", "NH_DeskWood", tint=(1.0, 0.94, 0.8), scale=0.5, rough_add=0.15, wear=0.15, dirt=0.7)
    # the wood grain only shows faintly through bone paint: lighten the set's colour toward bone
    src, dst = _colour_in(board)
    nt = board.node_tree
    nt.links.new(_mix_rgb(nt, _math(nt, "ADD", 0.0, 0.78), src, (0.6, 0.54, 0.42)), dst)
    bw, by = 2.46, ys - 0.05
    for k, (z0, z1) in enumerate(((zb0, (zb0 + zb1) / 2 - 0.004), ((zb0 + zb1) / 2 + 0.004, zb1))):
        box(f"Plank{k}", (bw, 0.05, z1 - z0), (0, by, (z0 + z1) / 2), board, bevel=0.012, segments=1)
    box("PlankSeam", (bw - 0.04, 0.04, 0.01), (0, by, (zb0 + zb1) / 2), seam, bevel=0.0, segments=1)
    yfront = by - 0.025
    tube("BoardEdge", [(-bw / 2, yfront + 0.004, zb0), (bw / 2, yfront + 0.004, zb0), (bw / 2, yfront + 0.004, zb1), (-bw / 2, yfront + 0.004, zb1)], 0.018,
         iron, closed=True, square=True, poly=True)
    for k, (x, z) in enumerate(((-bw / 2 + 0.05, zb0 + 0.05), (bw / 2 - 0.05, zb0 + 0.05), (-bw / 2 + 0.05, zb1 - 0.05), (bw / 2 - 0.05, zb1 - 0.05))):
        sphere(f"BoardNail{k}", 0.016, (x, yfront - 0.008, z), iron, seg=6, rings=3, scale=(1, 0.5, 1))
    ink = flat("SignInk", (0.018, 0.017, 0.021), 0.5, dirt=0.3)
    red = flat("SignCrimson", CRIMSON, 0.45, dirt=0.3)
    zc = (zb0 + zb1) / 2 + 0.05
    # hand-lettered in ink with a crimson ampersand: three words on one baseline at one scale
    _words("Lettering", [("LOST", ink), ("&", red), ("FOUND", ink)], FONT_SIGN, lambda x, y, h: (x, yfront - h, zc + y), fit=(2.12, 0.46),
           depth=0.007, gap=0.3, res=2, bold=0.018, space=1.06)
    strip("Underline", [(-0.92, yfront - 0.003, zb0 + 0.12), (-0.3, yfront - 0.003, zb0 + 0.1), (0.35, yfront - 0.003, zb0 + 0.115),
                        (0.95, yfront - 0.003, zb0 + 0.095)], 0.032, (0, 0, 1), red, thick=0.004, it=2)
    _settle()
    return _dims()


# ------------------------------------------------------------------ previews

SMALL = {"LostScarf": 1.0, "LostSketchbook": 1.0, "LostWristband": 1.15, "LostPendant": 1.1, "LostHymnal": 1.05, "LostLunchTin": 1.0,
         "LostPocketWatch": 1.05, "LostPhone": 1.05}
_base_preview = P.preview


def _preview(objs, name, dims, suffix=""):
    """nh_props.preview's lights, floor and render, with the camera raised to about 40 degrees for the hand props (they
    lie flat; the shared camera sits nearly level with the floor). Every other prop goes to the shared preview."""
    if name not in SMALL:
        return _base_preview(objs, name, dims, suffix)
    sc = bpy.context.scene
    sc.cycles.samples = 48
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W"); sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.028, 0.045, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    size = max(dims) * SMALL[name]
    target = Vector((0, 0, dims[2] * 0.4))

    def light(kind, loc, energy, color, s):
        L = bpy.data.lights.new(kind, kind)
        L.energy = energy
        L.color = color
        L.size = s
        o = bpy.data.objects.new(kind, L)
        o.location = loc
        bpy.context.collection.objects.link(o)
        o.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    # the shared preview's energies grow with size while the falloff grows with size squared, so a prop this small would
    # be blown out: scale the energies with size squared (the same light on the prop as a 4-stud prop gets)
    k = size / 4.0
    light("AREA", (size * 1.2, -size * 1.4, size * 1.5), 400 * size * k, (1.0, 0.82, 0.6), size)
    light("AREA", (-size * 1.4, -size * 0.6, size * 1.0), 160 * size * k, (0.55, 0.55, 0.9), size)
    light("AREA", (0, size * 1.5, size * 1.4), 260 * size * k, (0.9, 0.3, 0.35), size)
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.data.materials.append(P.material("Floor", "NH_Boards", tint=(0.3, 0.24, 0.2), scale=0.12))
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    bpy.context.collection.objects.link(co)
    az = Vector((1.15, -1.65, 0)).normalized()
    el = math.radians(40)
    co.location = target + Vector((az.x * math.cos(el), az.y * math.cos(el), math.sin(el))) * size * 1.85
    co.rotation_euler = (target - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}{suffix}.png")
    bpy.ops.render.render(write_still=True)


P.preview = _preview
P.PREVIEW_PAD.update({"LostFoundBox": 1.12})
P.BUILD.update({
    "LostScarf": lost_scarf,
    "LostSketchbook": lost_sketchbook,
    "LostWristband": lost_wristband,
    "LostPendant": lost_pendant,
    "LostHymnal": lost_hymnal,
    "LostLunchTin": lost_lunch_tin,
    "LostPocketWatch": lost_pocket_watch,
    "LostPhone": lost_phone,
    "LostFoundBox": lost_found_box,
})
