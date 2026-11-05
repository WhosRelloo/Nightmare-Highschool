"""Props batch 26, the Seer set (2026-11-05): Sable Vey's fortune-telling table and chair for the Ink Studio (the Ink Club's
hangout), on theme with the Institution: ink, bone, wax, paper, brass, iron and deep crimson (#600E1A), candlelit gothic.
No wood shows on the table (it is all cloth, brass, glass and wax); the chair is black-stained wood dressed in iron. No blood:
the ink is blue-black, the melted wax black and bone.

  SeerTable  a round table 3.2 across, its top at 2.7, draped to the floor in deep crimson cloth (folds that deepen toward
             the floor, a tone-on-tone damask lattice, a bone-embroidered border of diamonds and dots at the hem and a band of
             small diamonds under the edge). On it: a black velvet reading cloth laid as a diamond, its four tips hanging over
             the edge with bone tassels and a bone cord round its edge, an ink-drawn chart in gilt and bone ink (the twelve
             houses, twelve sigils between double rings, an eye at the centre); a short gilt-edged tarot deck (crimson backs,
             bone borders, a gilt crescent), three cards face down in a spread; a brass chamberstick with a lit bone wax
             candle; a black glass ink pot with a bone quill and blue-black ink splashed round it; a bone china saucer of
             melted black wax with a guttered stub.
             Pieces: SeerTable_Main, SeerTable_Glow (the candle flame: Neon + light in Roblox).
  SeerChair  a high-backed carved gothic chair: black-stained wood, a pointed gable with crockets and an iron crescent
             holding a brass star, crocketed pinnacles, a traceried back over crimson velvet, a blind-arcaded apron, iron
             sabot feet, stretchers, corner straps and domed studs, a worn crimson velvet seat cushion with bone piping. No arms
             (a seated R15's arms hang clear). One piece.

Front faces -Y, Z is up, the origin is at the bottom centre. The seer sits behind the table (at +Y) facing -Y, so both props
share one orientation. Registered into nh_props.BUILD on import.
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, tube, _finish, _gable, _arch_loop
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, hoop, _mark, _xform, _dims, flat, _smooth, _mesh
from nh_props_batch8 import _spirelet, _spike, _pointed
from nh_props_batch9 import foil
from nh_props_batch4 import prism
import nh_props_batch20 as B20
from nh_props_batch24 import (_math, _coords, _mix_rgb, _paint, _bump, _splat_mask, _colour_in, _settle, sweep, pages, brass_fine,
                              _crescent, _star, _resample, CRIMSON, BONE, INK)


GILT_INK = (0.5, 0.34, 0.12)
BONE_INK = (0.6, 0.55, 0.44)
INK_BLUE = (0.008, 0.014, 0.075)   # blue-black ink, wet and glossy

# ------------------------------------------------------------------ table layout (studs)
ZT, R0, RB = 2.69, 1.42, 0.05       # cloth top, radius of its flat top, radius of the edge it rolls over
ZE = ZT - RB                       # where the skirt starts hanging
SEG = 104                          # segments round the drape
VE = 0.008                         # the velvet's mid-surface over the crimson (it is 0.01 thick)
ZV = ZT + VE + 0.005               # the velvet's top: things on the table stand here
SIGIL_C = (0.0, 0.1)               # centre of the ink-drawn chart
SIGIL_E = 0.95                     # the chart image covers SIGIL_C +- this


def _fine_mats(mats, k=0.3):
    """Scale the bake-time edge bevels and crevice AO of the given materials to hand-sized things (see batch 24's _fine)."""
    for m in mats:
        for n in m.node_tree.nodes:
            if n.type == "BEVEL":
                n.inputs["Radius"].default_value *= k
            elif n.type == "AMBIENT_OCCLUSION":
                n.inputs["Distance"].default_value *= k


def _vdims():
    """W, D, H of everything built, from the evaluated vertices (the shared _dims uses each part's bounding box, which
    overstates turned parts such as the 45-degree spire cones)."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for ob in P.PARTS:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ob.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            for k in range(3):
                lo[k], hi[k] = min(lo[k], w[k]), max(hi[k], w[k])
        ev.to_mesh_clear()
    return (round(hi[0] - lo[0], 2), round(hi[1] - lo[1], 2), round(hi[2] - lo[2], 2))


def _sep(nt):
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(_coords(nt), s.inputs["Vector"])
    return s.outputs["X"], s.outputs["Y"], s.outputs["Z"]


def _band(nt, v, lo, hi):
    return _math(nt, "MULTIPLY", _math(nt, "GREATER_THAN", v, lo), _math(nt, "LESS_THAN", v, hi))


def _near(nt, v, c, w):
    return _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", v, c)), w)


def _hyp(nt, a, b):
    return _math(nt, "SQRT", _math(nt, "ADD", _math(nt, "MULTIPLY", a, a), _math(nt, "MULTIPLY", b, b)))


def _disc(nt, x, y, cx, cy, r):
    """1 inside the circle (cx, cy, r) in the plane of sockets x, y."""
    return _math(nt, "LESS_THAN", _hyp(nt, _math(nt, "SUBTRACT", x, cx), _math(nt, "SUBTRACT", y, cy)), r)


def _region(nt, x, y, cx, cy, r, soft=0.12):
    """A soft round region (1 inside r, fading to 0 by r + soft)."""
    d = _hyp(nt, _math(nt, "SUBTRACT", x, cx), _math(nt, "SUBTRACT", y, cy))
    return _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", _math(nt, "SUBTRACT", d, r), soft), clamp=True)


# ------------------------------------------------------------------ materials

def drape_mat():
    """Heavy deep-crimson cloth: a weave, faint mottling, a tone-on-tone damask lattice on the skirt, a bone-embroidered border
    (diamonds and dots between two lines over a bone hem binding, and a band of small diamonds under the edge) and blue-black
    ink splashed on the top by the ink pot. Cylindrical masks round the table's axis (the build's origin)."""
    base = tuple(c * 0.92 for c in CRIMSON)
    m = flat("SeerDrape", base, 0.86, wear=0.0, dirt=0.75)
    nt = m.node_tree
    x, y, z = _sep(nt)
    a = _math(nt, "ARCTAN2", y, x)
    turn = lambda n: _math(nt, "MULTIPLY", a, n / (2 * math.pi))
    # mottling
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 3
    nt.links.new(_coords(nt), nz.inputs["Vector"])
    src, dst = _colour_in(m)
    nt.links.new(_mix_rgb(nt, _math(nt, "MULTIPLY", nz.outputs["Fac"], 0.7), src, tuple(c * 0.68 for c in base)), dst)
    # damask: a diamond lattice, a little brighter and silkier (tone on tone), on the skirt only
    p, q = turn(28), _math(nt, "DIVIDE", z, 0.34)
    d1 = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "FRACT", _math(nt, "ADD", p, q)), 0.5))
    d2 = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "FRACT", _math(nt, "SUBTRACT", p, q)), 0.5))
    lat = _math(nt, "MAXIMUM", _math(nt, "LESS_THAN", d1, 0.035), _math(nt, "LESS_THAN", d2, 0.035))
    pip = _math(nt, "LESS_THAN", _math(nt, "ADD", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", d1, 0.5)),
                                        _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", d2, 0.5))), 0.12)
    dam = _math(nt, "MULTIPLY", _math(nt, "MAXIMUM", lat, pip), _band(nt, z, 0.42, 2.36))
    _paint(m, dam, tuple(c * 1.22 for c in base), rough=0.68)
    # the bone embroidery
    zc, h = 0.2, 0.072
    tri = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "MULTIPLY", _math(nt, "FRACT", turn(46)), 2.0), 1.0))
    z1 = _math(nt, "ADD", zc - h, _math(nt, "MULTIPLY", tri, 2 * h))
    z2 = _math(nt, "SUBTRACT", zc + h, _math(nt, "MULTIPLY", tri, 2 * h))
    emb = _math(nt, "MAXIMUM", _near(nt, z, z1, 0.0075), _near(nt, z, z2, 0.0075))
    emb = _math(nt, "MULTIPLY", emb, _band(nt, z, zc - h - 0.01, zc + h + 0.01))
    period = 2 * math.pi * 1.62 / 92
    g = _math(nt, "SUBTRACT", _math(nt, "FRACT", _math(nt, "ADD", turn(92), 0.5)), 0.5)
    dot = _math(nt, "LESS_THAN", _hyp(nt, _math(nt, "MULTIPLY", g, period), _math(nt, "SUBTRACT", z, zc)), 0.017)
    emb = _math(nt, "MAXIMUM", emb, dot)
    for zz in (zc - h - 0.035, zc + h + 0.035):
        emb = _math(nt, "MAXIMUM", emb, _near(nt, z, zz, 0.0085))
    emb = _math(nt, "MAXIMUM", emb, _math(nt, "LESS_THAN", z, 0.04))                 # the hem binding
    # the band under the edge: two lines and small diamonds
    for zz in (2.405, 2.565):
        emb = _math(nt, "MAXIMUM", emb, _near(nt, z, zz, 0.006))
    per2 = 2 * math.pi * 1.56 / 80
    g2 = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", _math(nt, "FRACT", turn(80)), 0.5))
    dia = _math(nt, "LESS_THAN", _math(nt, "ADD", _math(nt, "DIVIDE", _math(nt, "MULTIPLY", g2, per2), 0.032),
                                        _math(nt, "DIVIDE", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", z, 2.485)), 0.05)), 1.0)
    emb = _math(nt, "MAXIMUM", emb, dia)
    emb = _math(nt, "MULTIPLY", emb, _math(nt, "LESS_THAN", z, 2.62))
    _paint(m, emb, BONE, rough=0.5)
    # blue-black ink splashed on the top beside the ink pot, and a few flicks down the skirt below it
    sp = _splat_mask(m, 5.5, blob=0.6, region=0.4, drops=0.1, seed=3.0, detail=6.0)
    reg = _math(nt, "MAXIMUM", _math(nt, "MULTIPLY", _region(nt, x, y, -0.92, -0.86, 0.3, 0.2), _math(nt, "GREATER_THAN", z, 2.66)),
                _math(nt, "MULTIPLY", _region(nt, x, y, -1.12, -1.12, 0.18, 0.15), _band(nt, z, 2.0, 2.66)))
    _paint(m, _math(nt, "MULTIPLY", sp, reg), INK_BLUE, rough=0.12)
    # weave + raised embroidery in the bump
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.bands_direction = "Z"; w1.inputs["Scale"].default_value = 0.314 / 0.01
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.bands_direction = "X"; w2.inputs["Scale"].default_value = 0.314 / 0.01
    w3 = nt.nodes.new("ShaderNodeTexWave"); w3.bands_direction = "Y"; w3.inputs["Scale"].default_value = 0.314 / 0.01
    for w in (w1, w2, w3):
        nt.links.new(_coords(nt), w.inputs["Vector"])
    weave = _math(nt, "MULTIPLY", w1.outputs["Fac"], _math(nt, "MAXIMUM", w2.outputs["Fac"], w3.outputs["Fac"]))
    _bump(m, _math(nt, "ADD", _math(nt, "MULTIPLY", weave, 0.5), _math(nt, "MULTIPLY", emb, 2.5)), 0.0012)
    return m


def _sigil_image(name, N=1536):
    """The chart drawn on the velvet, rasterised with numpy (R = gilt ink, G = bone ink), centred on SIGIL_C, +-SIGIL_E across:
    double gilt rings, the twelve houses in bone, twelve invented sigils between the rings, an eye with gilt rays at the centre.
    Strokes wobble a little, as if drawn by hand."""
    E = SIGIL_E
    px = 2 * E / N
    co = (np.arange(N) + 0.5) * px - E
    gilt = np.zeros((N, N), np.float32)
    bone = np.zeros((N, N), np.float32)
    rnd = random.Random(2511)

    def win(x0, x1, y0, y1):
        i0, i1 = max(0, int((x0 + E) / px) - 2), min(N, int((x1 + E) / px) + 3)
        j0, j1 = max(0, int((y0 + E) / px) - 2), min(N, int((y1 + E) / px) + 3)
        X, Y = np.meshgrid(co[i0:i1], co[j0:j1])
        return (slice(j0, j1), slice(i0, i1)), X, Y

    def put(m, sl, d, w):
        m[sl] = np.maximum(m[sl], np.clip(0.5 - (d - w / 2) / px, 0, 1))

    def seg(m, a, b, w):
        sl, X, Y = win(min(a[0], b[0]) - w, max(a[0], b[0]) + w, min(a[1], b[1]) - w, max(a[1], b[1]) + w)
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        vx, vy = bx - ax, by - ay
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / max(1e-12, vx * vx + vy * vy), 0, 1)
        put(m, sl, np.hypot(X - ax - t * vx, Y - ay - t * vy), w)

    def ring(m, c, r, w, wob=0.0, ph=0.0):
        sl, X, Y = win(c[0] - r - w - wob, c[0] + r + w + wob, c[1] - r - w - wob, c[1] + r + w + wob)
        th = np.arctan2(Y - c[1], X - c[0])
        rr = r + wob * np.sin(3 * th + ph) + wob * 0.5 * np.sin(7 * th + 2 * ph)
        put(m, sl, np.abs(np.hypot(X - c[0], Y - c[1]) - rr), w)

    def arc(m, c, r, a0, a1, w):
        """An arc from angle a0 to a1 (radians, counter-clockwise)."""
        n = max(6, int(abs(a1 - a0) * r / 0.004))
        pts = [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
        for p, q in zip(pts, pts[1:]):
            seg(m, p, q, w)

    def dot(m, c, r):
        sl, X, Y = win(c[0] - r, c[0] + r, c[1] - r, c[1] + r)
        put(m, sl, np.hypot(X - c[0], Y - c[1]), 2 * r)

    # rings and the twelve houses
    O = (0.0, 0.0)
    ring(gilt, O, 0.885, 0.013, 0.0025, 0.3)
    ring(gilt, O, 0.848, 0.005, 0.002, 1.9)
    ring(gilt, O, 0.64, 0.007, 0.002, 2.6)
    ring(bone, O, 0.6, 0.004, 0.0015, 0.8)
    ring(bone, O, 0.24, 0.005, 0.0015, 4.0)
    for k in range(12):
        a = k * math.pi / 6
        seg(bone, (0.24 * math.cos(a), 0.24 * math.sin(a)), (0.6 * math.cos(a), 0.6 * math.sin(a)), 0.0038)
        dot(gilt, (0.744 * math.cos(a), 0.744 * math.sin(a)), 0.009)
        a2 = a + math.pi / 12
        for r0, r1 in ((0.6, 0.625),):
            seg(gilt, (r0 * math.cos(a2), r0 * math.sin(a2)), (r1 * math.cos(a2), r1 * math.sin(a2)), 0.004)

    # twelve sigils, each drawn in a unit box (y up) and set between the rings with its top toward the centre
    def S_sun(L):
        L("ring", (0, 0), 0.7); L("dot", (0, 0), 0.16)

    def S_moon(L):
        L("arc", (0, 0), 0.8, math.radians(50), math.radians(310)); L("arc", (0.42, 0), 0.62, math.radians(78), math.radians(282))

    def S_mercury(L):
        L("ring", (0, 0.1), 0.42); L("seg", (0, -0.32), (0, -0.95)); L("seg", (-0.3, -0.66), (0.3, -0.66))
        L("arc", (0, 0.86), 0.36, math.radians(200), math.radians(340))

    def S_fire(L):
        L("seg", (-0.75, -0.6), (0.75, -0.6)); L("seg", (0.75, -0.6), (0, 0.8)); L("seg", (0, 0.8), (-0.75, -0.6))
        L("dot", (0, -0.12), 0.12)

    def S_earth(L):
        L("seg", (-0.75, 0.6), (0.75, 0.6)); L("seg", (0.75, 0.6), (0, -0.8)); L("seg", (0, -0.8), (-0.75, 0.6))
        L("seg", (-0.5, 0.15), (0.5, 0.15))

    def S_eye(L):
        L("arc", (0, -0.62), 0.95, math.radians(48), math.radians(132)); L("arc", (0, 0.62), 0.95, math.radians(228), math.radians(312))
        L("ring", (0, 0), 0.22); L("dot", (0, 0), 0.08)

    def S_spiral(L):
        pts = [(0.08 * t * math.cos(t), 0.08 * t * math.sin(t)) for t in [k * 0.25 for k in range(45)]]
        for p, q in zip(pts, pts[1:]):
            L("seg", p, q)

    def S_saturn(L):
        L("seg", (-0.2, 0.9), (-0.2, -0.3)); L("seg", (-0.55, 0.55), (0.15, 0.55))
        L("arc", (0.15, -0.3), 0.35, math.radians(180), math.radians(380)); L("seg", (0.5, -0.18), (0.25, -0.85))

    def S_key(L):
        L("ring", (0, 0.55), 0.3); L("seg", (0, 0.25), (0, -0.9)); L("seg", (0, -0.62), (0.35, -0.62)); L("seg", (0, -0.85), (0.28, -0.85))

    def S_twinkle(L):
        pts = []
        for k in range(8):
            a = math.pi / 2 + k * math.pi / 4
            r = 0.85 if k % 2 == 0 else 0.22
            pts.append((r * math.cos(a), r * math.sin(a)))
        for p, q in zip(pts, pts[1:] + pts[:1]):
            L("seg", p, q)

    def S_hourglass(L):
        L("seg", (-0.55, 0.8), (0.55, 0.8)); L("seg", (-0.55, -0.8), (0.55, -0.8))
        L("seg", (-0.45, 0.8), (0.45, -0.8)); L("seg", (0.45, 0.8), (-0.45, -0.8))

    def S_venus(L):
        L("ring", (0, 0.32), 0.45); L("seg", (0, -0.13), (0, -0.92)); L("seg", (-0.3, -0.55), (0.3, -0.55))

    sigils = [S_sun, S_moon, S_mercury, S_fire, S_key, S_eye, S_venus, S_earth, S_spiral, S_hourglass, S_saturn, S_twinkle]
    s = 0.05
    for k, fn in enumerate(sigils):
        a = k * math.pi / 6 + math.pi / 12
        cx, cy = 0.744 * math.cos(a), 0.744 * math.sin(a)
        up = (-math.cos(a), -math.sin(a))              # toward the centre
        rt = (up[1], -up[0])
        tilt = rnd.uniform(-0.06, 0.06)
        ca, sa = math.cos(tilt), math.sin(tilt)

        def W(p, cx=cx, cy=cy, up=up, rt=rt, ca=ca, sa=sa):
            lx, ly = p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca
            return (cx + s * (lx * rt[0] + ly * up[0]), cy + s * (lx * rt[1] + ly * up[1]))

        def L(kind, *args, W=W, up=up, rt=rt):
            w = 0.0042
            if kind == "seg":
                seg(bone, W(args[0]), W(args[1]), w)
            elif kind == "ring":
                ring(bone, W(args[0]), s * args[1], w)
            elif kind == "dot":
                dot(bone, W(args[0]), s * args[1])
            elif kind == "arc":
                c, r, a0, a1 = args
                n = 16
                pts = [W((c[0] + r * math.cos(a0 + (a1 - a0) * j / n), c[1] + r * math.sin(a0 + (a1 - a0) * j / n))) for j in range(n + 1)]
                for p, q in zip(pts, pts[1:]):
                    seg(bone, p, q, w)
        fn(L)

    # the eye at the centre, gilt rays round it
    hw_, hh_ = 0.13, 0.055
    yc = (hw_ * hw_ - hh_ * hh_) / (-2 * hh_)
    re = hh_ - yc
    ae = math.atan2(-yc, hw_)
    arc(bone, (0, yc), re, ae, math.pi - ae, 0.006)
    arc(bone, (0, -yc), re, math.pi + ae, 2 * math.pi - ae, 0.006)
    ring(bone, O, 0.04, 0.005)
    dot(gilt, O, 0.018)
    for k in range(16):
        a = k * math.pi / 8
        r1 = 0.21 if k % 2 == 0 else 0.185
        seg(gilt, (0.15 * math.cos(a), 0.15 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a)), 0.0045)

    img = bpy.data.images.new(name, N, N, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    px_ = np.zeros((N, N, 4), np.float32)
    px_[..., 0], px_[..., 1], px_[..., 3] = gilt, bone, 1.0
    img.pixels.foreach_set(px_.ravel())
    img.update()
    return img


def velvet_mat():
    """Black velvet (a little crushed: soft lighter patches) with the chart drawn on it in gilt and bone ink, and blue-black ink
    blots round the ink pot (they read by their sheen and a faint navy)."""
    m = flat("SeerVelvet", (0.011, 0.01, 0.014), 0.94, dirt=0.5)
    nt = m.node_tree
    x, y, z = _sep(nt)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 4
    nt.links.new(_coords(nt), nz.inputs["Vector"])
    src, dst = _colour_in(m)
    nt.links.new(_mix_rgb(nt, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.45, clamp=True), 1.6), src, (0.026, 0.023, 0.031)), dst)
    fz = nt.nodes.new("ShaderNodeTexNoise"); fz.inputs["Scale"].default_value = 300; fz.inputs["Detail"].default_value = 2
    nt.links.new(_coords(nt), fz.inputs["Vector"])
    _bump(m, fz.outputs["Fac"], 0.0008)
    # the chart
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (2 * SIGIL_E), 1 / (2 * SIGIL_E), 1)
    mp.inputs["Location"].default_value = (0.5 - SIGIL_C[0] / (2 * SIGIL_E), 0.5 - SIGIL_C[1] / (2 * SIGIL_E), 0)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = _sigil_image("SeerSigils")
    t.extension = "CLIP"
    t.interpolation = "Linear"
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    sp = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(t.outputs["Color"], sp.inputs["Color"])
    top = _math(nt, "GREATER_THAN", z, ZT)
    _paint(m, _math(nt, "MULTIPLY", sp.outputs[1], top), BONE_INK, rough=0.6)
    _paint(m, _math(nt, "MULTIPLY", sp.outputs[0], top), GILT_INK, rough=0.32, metal=1.0)
    blots = _splat_mask(m, 6.0, blob=0.58, region=0.36, drops=0.12, seed=5.0, detail=6.0)
    _paint(m, _math(nt, "MULTIPLY", blots, _region(nt, x, y, -1.02, -0.3, 0.2, 0.2)), INK_BLUE, rough=0.1)
    return m


def card_back(name, c, rz, hu, hv):
    """A tarot card's back, painted in the card's own frame (centre c, turned rz): a bone border, a fine gilt rule, a crimson
    field, a gilt crescent with a bone twinkle above and below, gilt corner dots."""
    m = flat(name, (0.075, 0.004, 0.009), 0.55, dirt=0.35)
    nt = m.node_tree
    mp = nt.nodes.new("ShaderNodeMapping"); mp.vector_type = "TEXTURE"
    mp.inputs["Location"].default_value = (c[0], c[1], 0)
    mp.inputs["Rotation"].default_value = (0, 0, rz)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(mp.outputs["Vector"], s.inputs["Vector"])
    u, v = s.outputs["X"], s.outputs["Y"]
    au, av = _math(nt, "ABSOLUTE", u), _math(nt, "ABSOLUTE", v)
    border = _math(nt, "MAXIMUM", _math(nt, "GREATER_THAN", au, hu - 0.022), _math(nt, "GREATER_THAN", av, hv - 0.022))
    ins = _math(nt, "MAXIMUM", _math(nt, "SUBTRACT", au, hu - 0.036), _math(nt, "SUBTRACT", av, hv - 0.036))
    rule = _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", ins), 0.0032)
    cres = _math(nt, "MULTIPLY", _disc(nt, u, v, 0.0, 0.0, 0.072), _math(nt, "SUBTRACT", 1.0, _disc(nt, u, v, 0.03, 0.012, 0.062)))
    dots = _disc(nt, au, av, hu - 0.06, hv - 0.06, 0.012)
    gl = _math(nt, "MAXIMUM", _math(nt, "MAXIMUM", rule, cres), dots)
    tw = None
    for vy in (0.14, -0.14):
        d = _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SQRT", au), 1.0), _math(nt, "SQRT", _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", v, vy))))
        st = _math(nt, "LESS_THAN", d, 0.2)
        tw = st if tw is None else _math(nt, "MAXIMUM", tw, st)
    _paint(m, _math(nt, "MAXIMUM", border, tw), BONE, rough=0.6)
    _paint(m, gl, GILT_INK, rough=0.3, metal=1.0)
    return m


# ------------------------------------------------------------------ table geometry

def skirt_t(z):
    return max(0.0, min(1.0, (ZE - z) / ZE))


def skirt_r(z):
    """The drape's radius (before its folds) at height z on the skirt; it flares a little toward the floor and pools."""
    t = skirt_t(z)
    return R0 + RB + 0.035 * t ** 1.6 + 0.025 * max(0.0, (0.14 - z) / 0.14) ** 2


def fold_amp(z):
    s = max(0.0, min(1.0, (skirt_t(z) - 0.03) / 0.97))
    return 0.09 * s ** 0.85


def fold(a):
    return 0.55 * math.cos(13 * a + 0.4) + 0.3 * math.cos(19 * a + 2.1) + 0.25 * math.cos(7 * a + 1.1)


def drape(mat):
    """The crimson cloth: a flat round top, rolled over the edge, hanging to the floor in folds, the hem turned under."""
    bm = bmesh.new()
    angs = [k / SEG * 2 * math.pi for k in range(SEG)]
    prof = [lambda a, r=r: (r, ZT) for r in (0.45, 0.9, 1.25, R0)]
    for k in range(1, 5):
        th = k / 5 * math.pi / 2
        prof.append(lambda a, th=th: (R0 + RB * math.sin(th), ZE + RB * math.cos(th)))
    nz = 18
    for k in range(nz + 1):
        z = ZE * (1 - k / nz) ** 1.15
        prof.append(lambda a, z=z: (skirt_r(z) + fold_amp(z) * fold(a), z))
    prof.append(lambda a: (skirt_r(0) + fold_amp(0) * fold(a) - 0.035, 0.0))
    prof.append(lambda a: (skirt_r(0) + fold_amp(0) * fold(a) - 0.045, 0.03))
    centre = bm.verts.new((0, 0, ZT))
    rings = []
    for f in prof:
        rg = []
        for a in angs:
            r, z = f(a)
            rg.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(rg)
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((centre, rings[0][i], rings[0][j]))
    for A, B in zip(rings, rings[1:]):
        for i in range(SEG):
            j = (i + 1) % SEG
            bm.faces.new((A[i], B[i], B[j], A[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("Drape")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Drape", me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def drape_pt(x, y, e):
    """A point of a flat sheet laid over the drape (sheet coords x, y), e above the crimson: flat on the top, rolled over the
    edge, hanging straight down the skirt."""
    d = math.hypot(x, y)
    # stand a little further off where it rolls over the edge: the sheet's triangles are chords across the curve and would
    # otherwise cut into the crimson there
    e = e + 0.016 * max(0.0, min(1.0, (d - (R0 - 0.1)) / 0.1))
    if d <= R0:
        return (x, y, ZT + e)
    ux, uy = x / d, y / d
    s = d - R0
    re = RB + e
    q = math.pi / 2 * re
    if s <= q:
        th = s / re
        rad, z = R0 + re * math.sin(th), ZE + re * math.cos(th)
    else:
        z = ZE - (s - q)
        rad = skirt_r(z) + fold_amp(z) * 1.2 + e
    return (ux * rad, uy * rad, z)


def _grid(h, n):
    return [h * (0.35 * t + 0.65 * math.sin(math.pi / 2 * t)) for t in [-1 + 2 * k / (n - 1) for k in range(n)]]


def reading_cloth(vel, cord_m, tassel_m):
    """The black velvet laid as a diamond (its tips to the front, back and sides hang over the edge), a bone cord round its
    edge and a bone tassel at each tip."""
    hd = 1.68                      # centre to tip
    h = hd / math.sqrt(2)
    g = _grid(h, 27)
    r2 = 1 / math.sqrt(2)
    sheet = lambda u, v, e=VE: drape_pt((u - v) * r2, (u + v) * r2, e)
    _mesh("Velvet", [[sheet(u, v) for u in g] for v in g], vel, 0.01)
    loop = [(u, -h) for u in g[:-1]] + [(h, v) for v in g[:-1]] + [(u, h) for u in reversed(g[1:])] + [(-h, v) for v in reversed(g[1:])]
    tube("Cord", [sheet(u, v, VE + 0.0005) for u, v in loop], 0.0068, cord_m, closed=True, poly=True)
    for k, (u, v) in enumerate(((h, h), (-h, -h), (h, -h), (-h, h))):
        p = Vector(sheet(u, v, VE))
        out = Vector((p.x, p.y, 0)).normalized()
        c = p + out * 0.04
        sphere(f"TasselKnob{k}", 0.022, (c.x, c.y, p.z - 0.024), tassel_m, seg=10, rings=6, scale=(1, 1, 1.3))
        tube(f"TasselLoop{k}", [tuple(p + Vector((0, 0, 0.004))), tuple(p + out * 0.025 + Vector((0, 0, -0.004))), (c.x, c.y, p.z - 0.008)],
             0.0055, cord_m, poly=False)
        lathe(f"Tassel{k}", [(0, -0.17), (0.026, -0.168), (0.031, -0.15), (0.024, -0.09), (0.014, -0.05), (0.017, -0.043), (0.013, -0.036),
                             (0, -0.034)], tassel_m, seg=14, flute=(10, 0.22), loc=(c.x, c.y, p.z))


def card(name, c, z0, rz, hu=0.15, hv=0.25, t=0.008):
    m = card_back(name, c, rz, hu, hv)
    box(name, (2 * hu, 2 * hv, t), (c[0], c[1], z0 + t / 2), m, bevel=0.0025, segments=1, rot=(0, 0, rz))
    return m


def chamberstick(x, y, brass, wax, wick_m):
    """A brass chamberstick (dish, socket, ring handle, thumb plate) with a bone wax candle guttering down one side. Returns
    the wick's tip."""
    z = ZV
    lathe("StickDish", [(0, 0), (0.17, 0), (0.2, 0.008), (0.215, 0.028), (0.209, 0.04), (0.196, 0.033), (0.17, 0.019), (0.078, 0.016),
                        (0.064, 0.03), (0.052, 0.052), (0.047, 0.1), (0.058, 0.118), (0.063, 0.133), (0.057, 0.142), (0.046, 0.14),
                        (0.044, 0.112), (0, 0.112)], brass, seg=40, loc=(x, y, z))
    hoop("StickRing", (x + 0.255, y, z + 0.068), 0.046, "Y", brass, thick=0.009)
    box("StickThumb", (0.075, 0.05, 0.008), (x + 0.275, y, z + 0.118), brass, bevel=0.003, segments=1)
    zc = z + 0.112
    lathe("Candle", [(0, 0), (0.04, 0), (0.04, 0.27), (0.0412, 0.315), (0.0395, 0.343), (0.031, 0.35), (0.02, 0.343), (0.008, 0.336),
                     (0, 0.335)], wax, seg=20, loc=(x, y, zc))
    rnd = random.Random(2512)
    for k, a in enumerate((0.4, 2.3, 4.1)):
        L = rnd.uniform(0.05, 0.1)
        sweep(f"Drip{k}", [(x + math.cos(a) * 0.04, y + math.sin(a) * 0.04, zc + 0.335), (x + math.cos(a) * 0.0425, y + math.sin(a) * 0.0425, zc + 0.31),
                           (x + math.cos(a) * 0.0415, y + math.sin(a) * 0.0415, zc + 0.31 - L)],
              lambda t: 0.009 + 0.004 * t, wax, seg=8)
    a = 5.4
    sweep("DripLong", [(x + math.cos(a) * 0.04, y + math.sin(a) * 0.04, zc + 0.34), (x + math.cos(a) * 0.043, y + math.sin(a) * 0.043, zc + 0.2),
                       (x + math.cos(a) * 0.0425, y + math.sin(a) * 0.0425, zc + 0.04), (x + math.cos(a) * 0.05, y + math.sin(a) * 0.05, zc + 0.02)],
          lambda t: 0.01 + 0.006 * t, wax, seg=8)
    sphere("DripPool", 0.04, (x + math.cos(a) * 0.115, y + math.sin(a) * 0.115, z + 0.019), wax, seg=12, rings=6, scale=(1.3, 1.0, 0.16))
    tip = (x + 0.004, y - 0.002, zc + 0.368)
    tube("Wick", [(x, y, zc + 0.33), (x + 0.001, y, zc + 0.35), tip], 0.0045, wick_m)
    return tip


def ink_pot(x, y, glass, ink, brass, label, quill_m, shaft_m):
    """A squat black glass ink pot with a brass collar and a bone paper label, blue-black ink in the neck, a bone quill in it."""
    z = ZV
    lathe("InkPot", [(0, 0), (0.105, 0), (0.118, 0.012), (0.122, 0.05), (0.115, 0.085), (0.09, 0.11), (0.056, 0.125), (0.046, 0.132),
                     (0.046, 0.158), (0.053, 0.162), (0.053, 0.172), (0.045, 0.176), (0.038, 0.171), (0.036, 0.13), (0, 0.13)],
          glass, seg=32, loc=(x, y, z))
    lathe("InkSurface", [(0, 0.146), (0.0358, 0.146), (0.0358, 0.152), (0, 0.152)], ink, seg=24, loc=(x, y, z))
    hoop("InkCollar", (x, y, z + 0.145), 0.0475, "Z", brass, thick=0.0055)
    # the quill: its barrel in the ink, leaning back and out
    az, tilt = math.radians(128), math.radians(19)
    d = Vector((math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt)))
    side = d.cross(Vector((0, 0, 1))).normalized()
    nrm = side.cross(d).normalized()
    base = Vector((x, y, z + 0.06))
    Lq = 0.8
    ctr = lambda s: base + d * (s * Lq) - side * (0.06 * s * s) + nrm * (0.03 * s * s)
    sweep("QuillShaft", [tuple(ctr(k / 20)) for k in range(21)], lambda t: 0.0085 * (1 - 0.7 * t) + 0.0012, shaft_m, seg=8)
    rows = []
    s0, s1 = 0.3, 1.0
    for k in range(25):
        t = k / 24
        s = s0 + (s1 - s0) * t
        p = ctr(s + 0.004)
        env = max(0.0, math.sin(math.pi * (0.08 + 0.92 * t))) ** 0.6
        wl, wr = 0.028 * env, 0.05 * env * (1 - 0.25 * t)
        cup = 0.012
        rows.append((p + side * wl + nrm * (-cup * (wl / 0.03) ** 2), p, p - side * wr + nrm * (-cup * (wr / 0.05) ** 2)))
    _mesh("QuillVane", rows, quill_m, 0.0035)
    return base


def wax_dish(x, y, china, black_wax, wick_m):
    """A bone china saucer (a crimson line round its rim) holding a pool of melted black wax and a guttered stub."""
    z = ZV
    lathe("Saucer", [(0, 0), (0.095, 0), (0.115, 0.006), (0.15, 0.03), (0.163, 0.041), (0.157, 0.045), (0.138, 0.034), (0.1, 0.018),
                     (0, 0.016)], china, seg=36, loc=(x, y, z))
    lathe("WaxPool", [(0, 0.0165), (0.098, 0.0165), (0.108, 0.02), (0.1, 0.025), (0.06, 0.029), (0, 0.0305)], black_wax, seg=36,
          jitter=(0.09, 25), loc=(x, y, z))
    lathe("Stub", [(0, 0.02), (0.034, 0.02), (0.036, 0.07), (0.033, 0.086), (0.024, 0.08), (0.01, 0.076), (0, 0.077)], black_wax, seg=18,
          jitter=(0.05, 26), loc=(x - 0.012, y + 0.01, z))
    tube("StubWick", [(x - 0.012, y + 0.01, z + 0.074), (x - 0.008, y + 0.012, z + 0.095)], 0.004, wick_m, poly=True)
    rnd = random.Random(2513)
    for k in range(4):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.2, 0.29)
        sphere(f"WaxDrop{k}", rnd.uniform(0.011, 0.018), (x + math.cos(a) * r, y + math.sin(a) * r, z + 0.002), black_wax, seg=10, rings=5,
               scale=(1.2, 1.0, 0.28))


def seer_table(M):
    rnd = random.Random(2510)
    drape(drape_mat())             # built first, at the origin: the joined mesh's space is the build's space (masks rely on it)
    tassel = flat("TasselSilk", BONE, 0.55, dirt=0.5)
    cordm = flat("VelvetCord", (0.56, 0.5, 0.39), 0.6, dirt=0.5)
    reading_cloth(velvet_mat(), cordm, tassel)
    small = [tassel, cordm]
    # the spread: three cards face down across the chart
    for k, (x, y, rz) in enumerate(((-0.42, -0.36, 6), (0.0, -0.31, -2), (0.42, -0.37, -7))):
        small.append(card(f"Spread{k}", (x, y), ZV + 0.0015, math.radians(rz)))
    # the deck: a gilt-edged block, a card squared on it and the top card pushed askew
    dx, dy, drz = -0.92, 0.56, math.radians(28)
    edges = pages("DeckEdges", (0.72, 0.52, 0.2), line=0.0026, metal=1.0, rough=0.34)
    small.append(edges)
    box("Deck", (0.296, 0.496, 0.05), (dx, dy, ZV + 0.0015 + 0.025), edges, bevel=0.003, segments=1, rot=(0, 0, drz))
    small.append(card("DeckTop0", (dx, dy), ZV + 0.0525, drz))
    small.append(card("DeckTop1", (dx + 0.03, dy - 0.035), ZV + 0.0615, drz + math.radians(9)))
    # the candle, the ink pot and quill, the saucer of melted wax
    brass = brass_fine()
    wax = flat("CandleWax", (0.74, 0.68, 0.53), 0.45, dirt=0.55)
    wick = flat("Wick", (0.02, 0.018, 0.016), 0.85)
    tip = chamberstick(0.93, 0.6, brass, wax, wick)
    for k in range(3):
        a = rnd.uniform(-0.6, 0.9)
        sphere(f"CandleSpot{k}", rnd.uniform(0.012, 0.017), (0.93 + math.cos(a) * rnd.uniform(0.26, 0.33), 0.6 - 0.25 + math.sin(a) * 0.08, ZV + 0.002),
               wax, seg=10, rings=5, scale=(1.2, 1.0, 0.28))
    glass = flat("BlackGlass", (0.011, 0.012, 0.02), 0.07, dirt=0.3)
    nt = glass.node_tree
    x, y, z = _sep(nt)
    lab = _math(nt, "MULTIPLY", _band(nt, z, ZV + 0.038, ZV + 0.082), _math(nt, "LESS_THAN", y, -0.22 - 0.045))
    _paint(glass, lab, (0.62, 0.56, 0.43), rough=0.85)
    _paint(glass, _math(nt, "MULTIPLY", lab, _near(nt, z, ZV + 0.07, 0.004)), CRIMSON, rough=0.5)
    _paint(glass, _math(nt, "MULTIPLY", lab, _near(nt, z, ZV + 0.05, 0.0025)), INK, rough=0.4)
    ink = flat("InkWet", INK_BLUE, 0.05, dirt=0.1)
    quill = flat("Quill", (0.66, 0.61, 0.5), 0.62, dirt=0.4)
    qn = quill.node_tree
    wv = qn.nodes.new("ShaderNodeTexWave"); wv.bands_direction = "DIAGONAL"; wv.inputs["Scale"].default_value = 140
    qn.links.new(_coords(qn), wv.inputs["Vector"])
    _bump(quill, wv.outputs["Fac"], 0.0008)
    shaft = flat("QuillShaft", (0.7, 0.64, 0.52), 0.35, dirt=0.4)
    sn = shaft.node_tree
    _, _, sz = _sep(sn)
    _paint(shaft, _math(sn, "LESS_THAN", sz, ZV + 0.215), INK_BLUE, rough=0.15)   # ink-stained where it was dipped
    ink_pot(-1.02, -0.22, glass, ink, brass, None, quill, shaft)
    china = flat("BoneChina", (0.72, 0.68, 0.6), 0.18, dirt=0.5)
    cn = china.node_tree
    _, _, cz = _sep(cn)
    _paint(china, _band(cn, cz, ZV + 0.0405, ZV + 0.047), CRIMSON, rough=0.25)
    black_wax = flat("BlackWax", (0.03, 0.022, 0.055), 0.16, dirt=0.4)
    wax_dish(0.84, -0.54, china, black_wax, wick)
    small += [brass, wax, wick, glass, ink, quill, shaft, china, black_wax]
    _fine_mats(small, 0.3)
    # the flame
    P.set_group("Glow")
    lathe("Flame", [(0, -0.005), (0.016, 0.004), (0.028, 0.03), (0.03, 0.055), (0.024, 0.09), (0.012, 0.13), (0, 0.165)],
          P.material("FlameTmp", base=(1.0, 0.7, 0.3), rough=0.5), seg=12, loc=tip)
    P.set_group("Main")
    _settle()
    return _vdims()


# ------------------------------------------------------------------ the chair

def _outline(hw, hd, r, step):
    pts = _resample([(p[0], p[1]) for p in _rr(hw, hd, r)], step)
    n = len(pts)
    nrm = []
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        t = Vector((b[0] - a[0], b[1] - a[1], 0)).normalized()
        nrm.append(Vector((t.y, -t.x, 0)))
    return [Vector((x, y, 0)) for x, y in pts], nrm


def _rr(hw, hd, r, n=5):
    from nh_props_batch4 import rrect
    return rrect(hw, hd, r, 0, n=n)


def pillow(name, cx, cy, hw, hd, r, z0, h, mat, dome=0.02, sag=(0.0, 0.0, 0.0, 0.3)):
    """A seat cushion: a rounded-rectangle block with a rolled edge, its top domed a little and sat in at sag = (x, y, depth, radius).
    Open underneath (it lies on the seat board). Returns the edge loop where the side meets the top (for piping)."""
    B, Nn = _outline(hw, hd, r, 0.07)
    bm = bmesh.new()

    def top_z(p):
        u, v = (p.x - cx) / hw, (p.y - cy) / hd
        zz = z0 + h + dome * max(0.0, 1 - u * u) * max(0.0, 1 - v * v)
        d2 = (p.x - sag[0]) ** 2 + (p.y - sag[1]) ** 2
        return zz - sag[2] * math.exp(-d2 / (sag[3] ** 2))
    rings = []
    for inset, dz in ((0.014, 0.0), (0.002, 0.035), (0.0, h * 0.5), (0.006, h * 0.82), (0.024, h * 0.97)):
        rings.append([Vector((cx, cy, 0)) + b - nn * inset + Vector((0, 0, z0 + dz)) for b, nn in zip(B, Nn)])
    edge = rings[-1]
    for f in (0.93, 0.78, 0.6, 0.4, 0.2):
        rg = []
        for b, nn in zip(B, Nn):
            p = Vector((cx, cy, 0)) + (b - nn * 0.05) * f
            rg.append(Vector((p.x, p.y, top_z(p))))
        rings.append(rg)
    vr = [[bm.verts.new(tuple(p)) for p in rg] for rg in rings]
    n = len(B)
    for A, C in zip(vr, vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], C[j], C[i]))
    c = Vector((cx, cy, 0))
    ctr = bm.verts.new((cx, cy, top_z(c)))
    for i in range(n):
        bm.faces.new((vr[-1][i], vr[-1][(i + 1) % n], ctr))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    return [tuple(p) for p in edge]


def cushion_mat():
    """Worn crimson velvet: the pile rubbed browner and shinier where the seer sits and along the front edge, scuffs."""
    m = flat("SeerCushion", (0.1, 0.006, 0.013), 0.9, wear=0.45, dirt=0.7)
    nt = m.node_tree
    x, y, z = _sep(nt)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 6.0; nz.inputs["Detail"].default_value = 6
    nt.links.new(_coords(nt), nz.inputs["Vector"])
    rub = _math(nt, "MULTIPLY", _region(nt, x, _math(nt, "MULTIPLY", y, 1.25), 0.0, 0.05, 0.25, 0.45),
                _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.38, clamp=True), 3.0))
    front = _math(nt, "MULTIPLY", _math(nt, "LESS_THAN", y, -0.9), _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.42, clamp=True), 4.0))
    rub = _math(nt, "MINIMUM", _math(nt, "MAXIMUM", rub, front), 0.85)
    _paint(m, rub, (0.17, 0.045, 0.04), rough=0.62)
    fz = nt.nodes.new("ShaderNodeTexNoise"); fz.inputs["Scale"].default_value = 240; fz.inputs["Detail"].default_value = 2
    nt.links.new(_coords(nt), fz.inputs["Vector"])
    _bump(m, fz.outputs["Fac"], 0.0012)
    return m


def _parch(cx, y, hw, z0, zs, za, n=10):
    """A closed two-centred gothic arch outline at y (jambs from z0, springing at zs, apex za), as (x, y, z)."""
    return [(cx - hw, y, z0)] + [(cx + x, y, z) for x, z in _pointed(hw, zs, za, n)] + [(cx + hw, y, z0)]


def back_tracery(cx, y, mat, recess):
    """Geometric tracery on the back panel (a face at y, facing -Y) over crimson velvet: a two-centred pointed arch with an inner
    moulding, two pointed lancets on a mullion, a quatrefoil rose in the head."""
    hw, z0, zs, za = 0.66, 1.96, 3.15, 4.25
    yr = y - 0.012
    box("TracRecess", (2 * hw, 0.012, zs - z0), (cx, yr, (z0 + zs) / 2), recess, bevel=0.0, segments=1)
    prism("TracRecessHead", [(cx + x, z) for x, z in _pointed(hw, zs, za, 12)], yr, 0.012, recess)
    yt = y - 0.018 - 0.034
    tube("TracArch", _parch(cx, yt, hw, z0, zs, za, 12), 0.034, mat, square=True, closed=True, poly=True)
    tube("TracArchIn", _parch(cx, yt + 0.012, hw - 0.075, z0 + 0.04, zs, za - 0.12, 12), 0.016, mat, square=True, closed=True, poly=True)
    for sx in (-1, 1):
        tube(f"TracLancet{sx}", _parch(cx + sx * 0.29, yt, 0.2, z0 + 0.08, 2.95, 3.3, 8), 0.024, mat, square=True, closed=True, poly=True)
    tube("TracMullion", [(cx, yt, z0 + 0.06), (cx, yt, 3.0)], 0.026, mat, square=True, poly=True)
    foil("TracRose", cx, yt, 3.72, 0.2, mat, lobes=4, thick=0.022, n=12)


def seer_chair(M):
    SH = 1.6
    wood = P.material("SeerEbony", "NH_DeskWood", tint=(0.024, 0.019, 0.018), scale=0.32, rough_mul=0.8, rough_add=0.02, wear=0.22, dirt=0.85)
    iron = M["iron"]
    stud = flat("IronStud", (0.09, 0.088, 0.095), 0.38, metal=1.0, dirt=0.6)
    cush = cushion_mat()
    piping = flat("Piping", (0.58, 0.52, 0.41), 0.6, wear=0.2, dirt=0.6)
    recess = flat("BackVelvet", (0.07, 0.005, 0.01), 0.92, dirt=0.8)
    brass = brass_fine()
    _fine_mats([stud, piping, brass], 0.4)
    W2, yf, yb = 1.03, -0.9, 0.82            # leg centres: x = +-W2, front legs at yf, back posts at yb
    zb = 1.42                               # seat board top
    # the cushion first (built at the origin: the masks are in the build's space)
    edge = pillow("Cushion", 0.0, -0.145, 1.05, 0.845, 0.1, zb + 0.004, 0.172, cush, dome=0.022, sag=(0.0, 0.05, 0.026, 0.42))
    tube("Piping", edge, 0.013, piping, closed=True, poly=True)

    def studs(prefix, pts, face):
        sc = {"-Y": (1, 0.6, 1), "+X": (0.6, 1, 1), "-X": (0.6, 1, 1), "+Z": (1, 1, 0.6)}[face]
        for k, p in enumerate(pts):
            sphere(f"{prefix}{k}", 0.03, p, stud, seg=8, rings=4, scale=sc)

    # feet, legs, posts
    for sx in (-1, 1):
        for y in (yf, yb):
            box(f"Sabot{sx}{y:.1f}", (0.27, 0.27, 0.13), (sx * W2, y, 0.065), iron, bevel=0.03, segments=2)
            box(f"Band{sx}{y:.1f}", (0.235, 0.235 if y == yf else 0.255, 0.05), (sx * W2, y, 0.4), iron, bevel=0.01, segments=1)
        box(f"Leg{sx}", (0.2, 0.2, 1.24), (sx * W2, yf, 0.12 + 0.62), wood, bevel=0.035, segments=1)
        box(f"Post{sx}", (0.2, 0.22, 4.82), (sx * W2, yb, 0.12 + 2.41), wood, bevel=0.035, segments=1)
        _spirelet(f"Pin{sx}", sx * W2, yb, 4.94, 0.92, 0.25, wood, crockets=2)
        _spike(f"PinSpike{sx}", (sx * W2, yb, 4.94 + 0.92 + 0.12), 0.022, 0.16, iron, verts=6)
    # aprons with a blind arcade on the front, the seat board with iron studs round its edge
    box("ApronF", (1.9, 0.06, 0.3), (0, yf - 0.03, 1.17), wood, bevel=0.012, segments=1)
    box("ApronB", (1.9, 0.06, 0.3), (0, yb - 0.04, 1.17), wood, bevel=0.012, segments=1)
    for sx in (-1, 1):
        box(f"ApronS{sx}", (0.06, 1.62, 0.3), (sx * (W2 - 0.03), (yf + yb) / 2 - 0.04, 1.17), wood, bevel=0.012, segments=1)
    ya = yf - 0.06 - 0.016
    for k in range(5):
        cx = -0.76 + k * 0.38
        tube(f"Arcade{k}", _parch(cx, ya, 0.14, 1.06, 1.15, 1.285, 6), 0.016, wood, square=True, closed=True, poly=True)
    tube("ApronBead", [(-0.95, ya, 1.045), (0.95, ya, 1.045)], 0.014, wood, poly=True)
    box("Seat", (2.36, 1.84, 0.1), (0, -0.11, zb - 0.05), wood, bevel=0.03, segments=2)
    studs("SeatStudF", [(x, -1.03, zb - 0.05) for x in [-1.0 + k * 0.25 for k in range(9)]], "-Y")
    for sx in (-1, 1):
        studs(f"SeatStudS{sx}", [(sx * 1.18, y, zb - 0.05) for y in [-0.88 + k * 0.3 for k in range(6)]], "+X" if sx > 0 else "-X")
    # iron stretchers
    box("StretchF", (1.86, 0.04, 0.07), (0, yf, 0.4), iron, bevel=0.01, segments=1)
    box("StretchB", (1.86, 0.04, 0.07), (0, yb, 0.4), iron, bevel=0.01, segments=1)
    for sx in (-1, 1):
        box(f"StretchS{sx}", (0.04, 1.52, 0.07), (sx * W2, (yf + yb) / 2 - 0.03, 0.4), iron, bevel=0.01, segments=1)
    # the back: rails, a panel with tracery over crimson velvet, iron corner straps and studs up the posts
    box("BackRailLow", (1.9, 0.1, 0.32), (0, yb - 0.01, zb + 0.16), wood, bevel=0.02, segments=1)
    box("BackPanel", (1.9, 0.05, 2.72), (0, yb + 0.03, 1.74 + 1.36), wood, bevel=0.006, segments=1)
    box("BackRailTop", (1.9, 0.12, 0.24), (0, yb - 0.005, 4.46 + 0.12), wood, bevel=0.02, segments=1)
    back_tracery(0, yb + 0.005, wood, recess)
    for sx in (-1, 1):
        x = sx * (W2 - 0.1 - 0.05)
        tube(f"PanelMould{sx}", [(x, yb - 0.008, 1.76), (x, yb - 0.008, 4.44)], 0.02, wood, square=True, poly=True)
    yp = yb - 0.11
    for sx in (-1, 1):
        for zc in (1.76, 4.46):
            box(f"Strap{sx}{zc:.0f}", (0.13, 0.016, 0.46), (sx * W2, yp - 0.008, zc), iron, bevel=0.005, segments=1)
            studs(f"StrapStud{sx}{zc:.0f}", [(sx * W2, yp - 0.016, zc + dz) for dz in (-0.15, 0.0, 0.15)], "-Y")
        studs(f"PostStud{sx}", [(sx * W2, yp, 2.2 + k * 0.36) for k in range(6)], "-Y")
        studs(f"LegStud{sx}", [(sx * W2, yf - 0.1, z) for z in (0.75, 1.0)], "-Y")
    studs("RailStud", [(x, yb - 0.065, 4.58) for x in [-0.72 + k * 0.24 for k in range(7)]], "-Y")
    # the pointed gable with crockets, an iron crescent holding a brass star, an iron finial
    zs, za, hwg = 4.7, 5.5, 0.98
    _gable("Gable", 0, yb, hwg, zs, za, 0.1, wood, iron, edge=0.026)
    for side in (-1, 1):
        for k, t in enumerate((0.25, 0.45, 0.65, 0.85)):
            xg = side * (hwg - hwg * t)
            zg = zs + (za - zs) * (0.45 * t + 0.55 * math.sin(t * math.pi / 2))
            sphere(f"Crocket{side}{k}", 0.045, (xg, yb - 0.02, zg + 0.05), wood, seg=8, rings=4, scale=(1, 1.3, 1.4))
    s = _mark()
    Rm = 0.17
    outer = [(Rm * math.cos(math.radians(a)), Rm * math.sin(math.radians(a))) for a in [-125 + 250 * k / 20 for k in range(21)]]
    tx, ty = Rm * math.cos(math.radians(125)), Rm * math.sin(math.radians(125))
    ci = -0.3 * Rm
    ri = math.hypot(tx - ci, ty)
    ai = math.atan2(ty, tx - ci)
    inner = [(ci + ri * math.cos(ai - 2 * ai * k / 20), ri * math.sin(ai - 2 * ai * k / 20)) for k in range(1, 20)]
    _crescent("Crescent", outer, list(reversed(inner)), 0.0, 0.028, iron)
    _xform(s, Matrix.Rotation(math.radians(-90), 4, "Z"))
    B20.tprism("Star", _star(0.0, 0.075, 0.085, 0.022, n=4), 0.0, 0.03, brass, plane="XY", bevel=0.003)
    sphere("StarBoss", 0.018, (0.0, 0.075, 0.032), brass, seg=8, rings=4, scale=(1, 1, 0.6))
    _xform(s, Matrix.Translation((0, yb - 0.05 + 0.003, 4.96)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    sphere("GableKnop", 0.05, (0, yb, za + 0.06), iron, seg=10, rings=5)
    _spike("GableSpike", (0, yb, za + 0.2), 0.024, 0.2, iron, verts=6)
    _settle()
    return _vdims()


# ------------------------------------------------------------------ previews: a close look at the tabletop too

_prev_preview = P.preview
EXTRA = {"SeerTable": [("_top", (1.9, -3.1, 5.4), (0.0, -0.02, 2.62), 50)],
         "SeerChair": [("_seat", (2.6, -4.6, 3.4), (0.0, 0.0, 2.2), 50)]}


def _preview(objs, name, dims, suffix=""):
    _prev_preview(objs, name, dims, suffix)
    sc = bpy.context.scene
    for sfx, loc, tgt, lens in EXTRA.get(name, ()):
        co = sc.camera
        co.location = loc
        co.data.lens = lens
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}{sfx}{suffix}.png")
        bpy.ops.render.render(write_still=True)


P.preview = _preview
P.PREVIEW_PAD.update({"SeerTable": 1.05, "SeerChair": 1.0})
P.BUILD.update({
    "SeerTable": seer_table,
    "SeerChair": seer_chair,
})
