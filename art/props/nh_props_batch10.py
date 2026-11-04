"""Props batch 10 (2026-11-03): the Headmaster's office, for nh_props.py. Black lacquer, black marble, gilt and brass,
wrought iron, crimson leather and velvet, dark castle stone and candlelight; very little wood. Original designs.

  HeadmasterDesk    a grand pedestal desk in black lacquer with gilt mouldings, a pointed kneehole arch and a crimson
                    leather writing inset; on top a brass inkstand with quills, a blotter, a crested brass plaque, a
                    stack of files and a desk bell (Drawer0: the right pedestal's top drawer slides out, "Desk / Open")
  HeadmasterChair   a tall throne-like wingback in tufted crimson leather on a black and gilt frame, gilt pinnacles on
                    the back posts and a carved crest in the pointed gable over the back
  Fireplace         a wall piece: a gothic castle-stone fireplace with clustered jambs, a four-centred arch with carved
                    spandrels and a grotesque keystone, a mantel with candlesticks, a skull and a clock, an overmantel
                    of blind tracery round a carved shield, and an iron fire basket with logs (Glow: coals and flames,
                    for NHAmbient:Embers)
  FounderPortrait   a wall piece: the founder in a black robe with a crimson stole and a gilt chain of office, a raven
                    on his staff, before a moonlit sky, in a heavy gilt gothic frame with a brass picture light (Glow)
  Safe              a cast-iron safe on brass castors, gilt pinstripes, crimson side panels, brass dial and wheel
                    handle (Door0: swings out on its left hinge, "Safe / Open"; inside: gold, coins, sealed papers)
  CuriosityCabinet  a tall black glass-fronted cabinet of confiscated things: a slingshot, a skull, potion bottles, a
                    cursed doll stuck with pins, a dagger, playing cards, a chained book (Door0 and its pane, Glass, swing
                    out together on the left hinge, "Cabinet / Open")
  OfficeRug         a 12 x 8 crimson and ink gothic rug with gilt lines, a quatrefoil medallion and a fringe
  DeskLamp          brass, with a crimson glass bell shade (Glow: the bulb)
  FounderBust       a white marble bust of the founder on a fluted black marble plinth with gilt bands
  SchoolCrest       a wall piece: the Institution's quartered shield (raven, crescent, key, candle) over crossed swords,
                    a gilt crown, crimson mantling and a scroll of symbols
  DecanterTray      a silver tray with two crystal decanters (amber and wine) and three glasses (Glass)
  Hourglass         brass and black lacquer, twisted posts, red sand (Glass: the bulbs)

Front faces -Y, Z is up, the origin is at the bottom centre. Wall pieces have their back at +Y.
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _gable, _quatrefoil, _arch_loop, _arch_loop_x, _candlestick, _tufts, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, leaf, strip, prism, _mark, _xform, _dims, flat, painting_mat, _book, _smooth
from nh_props_batch5 import marble
from nh_props_batch6 import relief, ellipse, mirror_half
from nh_props_batch7 import lump, coal_mat
from nh_props_batch8 import _spirelet, _spike, _grotesque, _stain, _crockets, castle
from nh_props_batch9 import stones, candle, wax_mat, foil, tracery, twist


# ------------------------------------------------------------------ materials

def lacquer():
    """Black lacquer: the painted-metal set tinted near black, glossy, a little worn at the edges."""
    return material("BlackLacquer", "NH_PaintedMetal", tint=(0.022, 0.02, 0.026), scale=0.8, rough_mul=0.85, rough_add=0.05, wear=0.14, dirt=0.75)


def gilt():
    return material("Gilt", "NH_Brass", tint=(1.0, 0.84, 0.5), scale=0.5, wear=0.3, dirt=0.85)


def black_marble():
    return marble("BlackMarble", base=(0.028, 0.027, 0.032), vein=(0.42, 0.4, 0.38), scale=1.4, width=0.035, distortion=9.0)


def white_marble():
    return marble("WhiteMarble", base=(0.8, 0.78, 0.74), vein=(0.42, 0.41, 0.42), scale=1.2, width=0.03, distortion=8.0)


def velvet():
    return flat("CrimsonVelvet", (0.07, 0.006, 0.012), 0.95, dirt=0.6)


def silver():
    return material("Silver", base=(0.62, 0.62, 0.64), rough=0.2, metal=1.0, wear=0.25, dirt=0.9)


def steel():
    return material("Blade", base=(0.55, 0.56, 0.58), rough=0.18, metal=1.0, wear=0.3, dirt=0.6)


def skin(k=1.0):
    return flat("Skin", (0.42 * k, 0.29 * k, 0.22 * k), 0.6)


def qf(name, cx, y, cz, r, mat):
    """A light quatrefoil on a face at y (facing -Y): a ring and four lobes from poly circles (the shared _quatrefoil
    uses bezier rings, several times the triangles)."""
    foil(name, cx, y, cz, r, mat, lobes=4, thick=max(0.007, r * 0.14), n=8)


def column(prefix, x, y, z0, z1, r, mat, cap_mat):
    """A light clustered column: three shafts, a moulded base and capital (unbevelled, few sides)."""
    for k, (dx, dy) in enumerate([(0, -r * 0.9), (-r * 0.8, r * 0.5), (r * 0.8, r * 0.5)]):
        cyl(f"{prefix}Shaft{k}", r * 0.55, z1 - z0 - 0.5, (x + dx, y + dy, (z0 + z1) / 2), mat, verts=10, bevel=0)
    lathe(f"{prefix}Base", [(0, z0), (r * 1.7, z0), (r * 1.7, z0 + 0.14), (r * 1.45, z0 + 0.2), (r * 1.45, z0 + 0.28), (0, z0 + 0.28)], cap_mat, seg=12)
    lathe(f"{prefix}Cap", [(0, z1 - 0.28), (r * 1.4, z1 - 0.28), (r * 1.45, z1 - 0.18), (r * 1.75, z1 - 0.14), (r * 1.75, z1), (0, z1)], cap_mat, seg=12)


def tongue(name, base, h, w, lean, yaw, mat, seg=8, rows=10):
    """A tapered flame tongue: swelling just above its root, narrowing to a curling point, flattened front to back,
    leaning `lean` sideways at the tip, turned `yaw` about Z."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    c, s_ = math.cos(yaw), math.sin(yaw)
    for j in range(rows):
        t = j / rows
        r = w * (0.35 + 0.65 * math.sin(min(1.0, t * 2.4) * math.pi / 2)) * (1 - t) ** 0.9
        ox = lean * t * t + 0.03 * math.sin(t * 7.0) * w * 4
        ring = []
        for i in range(seg):
            a = i / seg * 2 * math.pi
            lx, ly = ox + math.cos(a) * r, math.sin(a) * r * 0.55
            ring.append(bm.verts.new((base[0] + lx * c - ly * s_, base[1] + lx * s_ + ly * c, base[2] + h * t)))
        rings.append(ring)
    tip = bm.verts.new((base[0] + lean * c, base[1] + lean * s_, base[2] + h))
    bot = bm.verts.new(base)
    for A, B in zip(rings, rings[1:]):
        for i in range(seg):
            k = (i + 1) % seg
            bm.faces.new((A[i], A[k], B[k], B[i]))
    for i in range(seg):
        k = (i + 1) % seg
        bm.faces.new((rings[-1][i], rings[-1][k], tip))
        bm.faces.new((rings[0][k], rings[0][i], bot))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0)


def oil(name, base, x_lit, x_dark, floor=0.1, z_range=None, rough=0.92):
    """Oil paint lit from one side (chiaroscuro): full colour where world X is at x_lit, falling smoothly to `floor`
    (tinted toward umber) at x_dark; optionally darker toward the bottom (z_range = (z dark, z lit)); brush strokes
    in the colour and the normal. Built on world position, so every painted layer shares one light."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])

    def mrange(v, a, b, lo=0.0, hi=1.0):
        n = nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        n.clamp = True
        L(v, n.inputs[0])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = lo, hi
        return n.outputs[0]

    def mth(op, a, b):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    lit = mrange(sep.outputs["X"], x_dark, x_lit)
    if z_range:
        lit = mth("MULTIPLY", lit, mrange(sep.outputs["Z"], z_range[0], z_range[1], 0.45, 1.0))
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (9.0, 2.0, 4.0)
    mp.inputs["Rotation"].default_value = (0.0, 0.7, 0.0)
    L(geo.outputs["Position"], mp.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 6.0
    st.inputs["Detail"].default_value = 3.0
    L(mp.outputs["Vector"], st.inputs["Vector"])
    lit = mth("ADD", lit, mth("MULTIPLY", mth("SUBTRACT", st.outputs["Fac"], 0.5), 0.12))
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.clamp_factor = True
    L(lit, mix.inputs[0])
    mix.inputs[6].default_value = (base[0] * floor + 0.004, base[1] * floor + 0.0025, base[2] * floor + 0.0015, 1)
    mix.inputs[7].default_value = (*base, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    L(st.outputs["Fac"], bump.inputs["Height"])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mix.outputs[2], rough, mv.outputs[0], bump.outputs["Normal"], 0.0, False, 0.0)
    return m


def cased_glass(z_top, z_rim):
    """Crimson cased glass: a deep oxblood at the crown warming to a lit crimson toward the rim (as if the bulb shone
    through), with faint vertical streaks in the casing; satin, not glossy."""
    m = bpy.data.materials.new("CasedGlass")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    L(sep.outputs["Z"], mr.inputs[0])
    mr.inputs[1].default_value, mr.inputs[2].default_value = z_top, z_rim
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0, 3.0, 0.35)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 9.0
    nz.inputs["Detail"].default_value = 2.0
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    L(nz.outputs["Fac"], add.inputs[0])
    add.inputs[1].default_value, add.inputs[2].default_value = 0.35, -0.17
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "ADD"
    fac.use_clamp = True
    L(mr.outputs[0], fac.inputs[0])
    L(add.outputs[0], fac.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L(fac.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = (0.05, 0.003, 0.005, 1)
    mix.inputs[7].default_value = (0.32, 0.018, 0.02, 1)
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mix.outputs[2], 0.62, mv.outputs[0], None, 0.0, False, 0.3)
    return m


def soot_stone(name, tint, centre, rx, rz, darkest=0.16):
    """Castle stone blackened by smoke: the limestone set tinted, darkening smoothly toward `centre` (an ellipse rx
    across, rz up, on world X and Z), broken up by noise so it reads as soot, not a painted shape."""
    m = material(name, "NH_Limestone", tint=tint, scale=0.28, wear=0.18, dirt=1.0)
    nt = m.node_tree
    mix = next(n for n in nt.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY" and n.inputs[6].is_linked
               and n.inputs[6].links[0].from_node.type == "TEX_IMAGE")
    L = nt.links.new
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub_ = nt.nodes.new("ShaderNodeVectorMath")
    sub_.operation = "SUBTRACT"
    L(geo.outputs["Position"], sub_.inputs[0])
    sub_.inputs[1].default_value = centre
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "MULTIPLY"
    L(sub_.outputs[0], sc.inputs[0])
    sc.inputs[1].default_value = (1.0 / rx, 0.0, 1.0 / rz)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L(sc.outputs[0], ln.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.5
    nz.inputs["Detail"].default_value = 6.0
    L(geo.outputs["Position"], nz.inputs["Vector"])
    ad = nt.nodes.new("ShaderNodeMath")
    ad.operation = "MULTIPLY_ADD"
    L(nz.outputs["Fac"], ad.inputs[0])
    ad.inputs[1].default_value, ad.inputs[2].default_value = 0.5, -0.25
    tot = nt.nodes.new("ShaderNodeMath")
    tot.operation = "ADD"
    L(ln.outputs["Value"], tot.inputs[0])
    L(ad.outputs[0], tot.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    L(tot.outputs[0], mr.inputs[0])
    mr.inputs[1].default_value, mr.inputs[2].default_value = 0.15, 1.0
    mr.inputs[3].default_value, mr.inputs[4].default_value = darkest, 1.0
    vs = nt.nodes.new("ShaderNodeVectorMath")
    vs.operation = "SCALE"
    vs.inputs[0].default_value = tint
    L(mr.outputs[0], vs.inputs["Scale"])
    L(vs.outputs[0], mix.inputs[7])
    return m


def candlestick(prefix, x, y, z, h, mat):
    """A light brass candlestick (one lathe): stepped foot, knopped stem, drip pan. Returns the pan top."""
    lathe(prefix, [(0, z), (0.26, z), (0.25, z + 0.04), (0.18, z + 0.07), (0.17, z + 0.12), (0.06, z + 0.16), (0.045, z + 0.2),
                   (0.09, z + 0.2 + h * 0.18), (0.045, z + 0.24 + h * 0.3), (0.04, z + h * 0.6), (0.08, z + h * 0.65), (0.04, z + h * 0.72),
                   (0.04, z + h), (0.15, z + h + 0.02), (0.15, z + h + 0.05), (0.05, z + h + 0.06), (0, z + h + 0.06)], mat, seg=16, loc=(x, y, 0))
    return z + h + 0.06


def trefoil_poly(cx, cz, r, n=30):
    """A cusped gothic trefoil for cresting (x, z), about r tall: a pointed top lobe, two round side lobes and a short
    stem, traced as the outline of their union by marching rays out from the middle."""
    disks = ((0.0, 0.62, 0.22), (-0.27, 0.36, 0.19), (0.27, 0.36, 0.19))

    def inside(u, v):
        if any((u - a) ** 2 + (v - b) ** 2 <= rr * rr for a, b, rr in disks):
            return True
        if 0.62 <= v <= 1.0 and abs(u) <= 0.2 * (1.0 - v) / 0.38:      # the point on the top lobe
            return True
        return abs(u) <= 0.09 and 0.0 <= v <= 0.4                    # the stem
    pts = []
    oc = (0.0, 0.42)
    for i in range(n):
        a = i / n * 2 * math.pi
        d, rr = (math.cos(a), math.sin(a)), 0.0
        while rr < 1.2 and inside(oc[0] + d[0] * (rr + 0.01), oc[1] + d[1] * (rr + 0.01)):
            rr += 0.01
        pts.append((cx + (oc[0] + d[0] * rr) * r, cz - 0.42 * r + (oc[1] + d[1] * rr) * r + 0.42 * r - 0.42 * r))
    return pts


def _rect(name, cx, y, cz, hw, hh, r, mat, square=True):
    """A thin rectangular moulding (or pinstripe) on a face at y."""
    tube(name, [(cx - hw, y, cz - hh), (cx + hw, y, cz - hh), (cx + hw, y, cz + hh), (cx - hw, y, cz + hh)], r, mat,
         closed=True, square=square, poly=True)


def _bail(prefix, x, y, z, mat):
    """A brass bail pull: a backplate with two bosses and a hanging handle, on a face at y (facing -Y)."""
    box(f"{prefix}Plate", (0.42, 0.02, 0.13), (x, y - 0.01, z), mat, bevel=0.008)
    for sx in (-1, 1):
        sphere(f"{prefix}Boss{sx}", 0.03, (x + sx * 0.15, y - 0.03, z + 0.02), mat, seg=8, rings=4)
    tube(f"{prefix}Handle", [(x - 0.15, y - 0.04, z + 0.02), (x - 0.13, y - 0.07, z - 0.07), (x + 0.13, y - 0.07, z - 0.07),
                             (x + 0.15, y - 0.04, z + 0.02)], 0.016, mat)


def _gothic_pts(x0, x1, zs, za, n=10):
    """The underside of a pointed arch from (x0, zs) up to the apex za and back down to (x1, zs), as (x, z)."""
    cx, hw = (x0 + x1) / 2, (x1 - x0) / 2
    left = [(cx - hw + hw * (i / n), zs + (za - zs) * (0.45 * (i / n) + 0.55 * math.sin(i / n * math.pi / 2))) for i in range(n + 1)]
    right = [(cx + hw - hw * (i / n), z) for i, (_, z) in enumerate(left)]
    return left + list(reversed(right))[1:]


def _skull(prefix, mtx, bone, dark):
    """A human skull facing -Y, resting on the origin (about 0.5 tall)."""
    s = _mark()
    sphere(f"{prefix}Cranium", 0.2, (0, 0.03, 0.29), bone, seg=14, rings=8, scale=(0.9, 1.1, 1.0))
    sphere(f"{prefix}Face", 0.14, (0, -0.1, 0.19), bone, seg=10, rings=6, scale=(1.0, 0.8, 1.05))
    box(f"{prefix}Jaw", (0.2, 0.14, 0.08), (0, -0.12, 0.06), bone, bevel=0.035)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.05, (sx * 0.065, -0.2, 0.23), dark, seg=8, rings=4, scale=(1, 0.6, 1))
        sphere(f"{prefix}Cheek{sx}", 0.05, (sx * 0.12, -0.12, 0.15), bone, seg=6, rings=4)
    cone(f"{prefix}Nose", 0.03, 0.0, 0.07, (0, -0.215, 0.165), dark, verts=3, rot=(math.radians(-90), 0, 0))
    for k in range(6):
        box(f"{prefix}Tooth{k}", (0.02, 0.02, 0.035), (-0.055 + k * 0.022, -0.2, 0.105), bone, bevel=0.0, segments=1)
    _xform(s, mtx)


# ================================================================== the Headmaster's desk
def headmaster_desk(M):
    W, D, H = 7.6, 3.4, 3.1
    lq, gl = lacquer(), gilt()
    ink = M["glass"]
    feather = flat("Quill", (0.82, 0.8, 0.74), 0.6)
    feather_dk = flat("QuillDark", (0.05, 0.045, 0.06), 0.55)
    PW = 2.2
    yf = -(D - 0.2) / 2           # pedestal front face
    set_group("Main")
    # the pedestals: plinth, carcass, gilt beads, colonettes at the front corners, a blind arch on each outer side
    for sx in (-1, 1):
        px = sx * (W / 2 - PW / 2 - 0.05)
        box(f"Plinth{sx}", (PW + 0.14, D - 0.06, 0.26), (px, 0, 0.13), lq, bevel=0.03)
        box(f"Carcass{sx}", (PW, D - 0.2, 2.62), (px, 0, 0.26 + 1.31), lq, bevel=0.02)
        tube(f"PlinthBead{sx}", [(px - PW / 2 - 0.07, yf - 0.1, 0.27), (px + PW / 2 + 0.07, yf - 0.1, 0.27)], 0.022, gl, poly=True)
        for cx in (px - PW / 2 + 0.04, px + PW / 2 - 0.04):
            cyl(f"Colonette{sx}{cx:.1f}", 0.07, 2.5, (cx, yf - 0.04, 0.3 + 1.25), lq, verts=12, bevel=0.01)
            for z in (0.36, 2.74):
                cyl(f"ColRing{sx}{cx:.1f}{z}", 0.095, 0.07, (cx, yf - 0.04, z), gl, verts=12, bevel=0.012)
        ox = px + sx * (PW / 2 + 0.005)
        tube(f"SideArch{sx}", _arch_loop_x(ox, 0, 1.05, 0.55, 1.9, 2.65), 0.03, gl, square=True, closed=True, poly=True)
        q = _mark()
        foil(f"SideFoil{sx}", 0, 0, 0, 0.22, gl, lobes=4, thick=0.016)
        _xform(q, Matrix.Translation((ox + sx * 0.01, 0, 2.15)) @ Matrix.Rotation(math.pi / 2 * sx, 4, "Z"))
        # three drawers each; the right pedestal's top drawer slides out
        z0, z1 = 0.36, 2.82
        dh = (z1 - z0) / 3
        for i in range(3):
            zc = z0 + dh * (i + 0.5)
            moving = sx == 1 and i == 2
            if moving:
                set_group("Drawer0")
                tray_d = D - 0.6
                box("DrawerTray", (PW - 0.36, tray_d, dh - 0.24), (px, yf + tray_d / 2 + 0.03, zc - 0.03), lq, bevel=0.012)
                for k in range(6):
                    box(f"Paper{k}", (PW - 0.5, 0.025, dh - 0.36 + (0.04 if k % 2 else 0)), (px, yf + 0.25 + k * 0.32, zc + 0.0),
                        M["paper"] if k % 3 else M["inkblue"], bevel=0.004)
                box("DrawerSeal", (0.3, 0.02, 0.1), (px + 0.3, yf + 0.25, zc + 0.12), M["crimson"], bevel=0.006)
            box(f"Drawer{sx}{i}", (PW - 0.2, 0.07, dh - 0.08), (px, yf - 0.03, zc), lq, bevel=0.02)
            _rect(f"DrawerPanel{sx}{i}", px, yf - 0.07, zc, PW / 2 - 0.24, dh / 2 - 0.13, 0.014, gl)
            _bail(f"Pull{sx}{i}", px, yf - 0.07, zc + 0.02, gl)
            box(f"Escutcheon{sx}{i}", (0.05, 0.02, 0.09), (px, yf - 0.075, zc + 0.19), gl, bevel=0.008)
            set_group("Main")
    # the kneehole: a frieze with a pointed arch cut along its lower edge, gilt edging and spandrel foils
    kx = W / 2 - PW - 0.05
    poly = [(-kx, 2.9), (kx, 2.9)] + list(reversed(_gothic_pts(-kx, kx, 2.05, 2.62, 10)))
    relief("Apron", poly, yf + 0.06, 0.12, lq)
    tube("ApronEdge", [(x, yf - 0.01, z - 0.01) for x, z in _gothic_pts(-kx + 0.02, kx - 0.02, 2.05, 2.62, 10)], 0.022, gl, square=True, poly=True)
    for sx in (-1, 1):
        foil(f"ApronFoil{sx}", sx * kx * 0.55, yf - 0.005, 2.68, 0.14, gl, lobes=3, thick=0.014)
    qf("ApronSeal", 0, yf - 0.01, 2.76, 0.1, gl)
    # the modesty panel at the back, blind tracery on both faces
    box("BackPanel", (2 * kx + 0.1, 0.1, 2.55), (0, D / 2 - 0.25, 0.3 + 1.275), lq, bevel=0.02)
    for k, cx in enumerate((-1.0, 0.0, 1.0)):
        tracery(f"BackTraceryF{k}", cx, D / 2 - 0.3, 0.42, 0.6, 1.9, 2.5, gl, thick=0.016)
        q = _mark()
        tracery(f"BackTraceryB{k}", -cx, 0, 0.42, 0.6, 1.9, 2.5, gl, thick=0.016)
        _xform(q, Matrix.Translation((0, D / 2 - 0.2, 0)) @ Matrix.Rotation(math.pi, 4, "Z"))
    # the top: slab with a gilt bead, a crimson leather inset with a gilt fillet
    box("TopUnder", (W + 0.06, D + 0.06, 0.09), (0, 0, H - 0.18), lq, bevel=0.03)
    box("Top", (W + 0.24, D + 0.24, 0.13), (0, 0, H - 0.065), lq, bevel=0.045, segments=3)
    tube("TopBead", [(-W / 2 - 0.13, -D / 2 - 0.13, H - 0.13), (W / 2 + 0.13, -D / 2 - 0.13, H - 0.13), (W / 2 + 0.13, D / 2 + 0.13, H - 0.13),
                     (-W / 2 - 0.13, D / 2 + 0.13, H - 0.13)], 0.022, gl, closed=True, poly=True)
    box("Inset", (W - 0.9, D - 0.8, 0.014), (0, 0, H + 0.004), M["leather"], bevel=0.004)
    tube("InsetGilt", [(-(W - 0.9) / 2, -(D - 0.8) / 2, H + 0.012), ((W - 0.9) / 2, -(D - 0.8) / 2, H + 0.012),
                       ((W - 0.9) / 2, (D - 0.8) / 2, H + 0.012), (-(W - 0.9) / 2, (D - 0.8) / 2, H + 0.012)], 0.016, gl, closed=True, square=True, poly=True)
    zt = H + 0.012
    # desk set: a blotter with brass corners
    box("Blotter", (2.0, 1.25, 0.045), (0.25, -0.35, zt + 0.022), M["leatherdark"], bevel=0.012)
    box("BlotPaper", (1.8, 1.05, 0.012), (0.25, -0.35, zt + 0.05), flat("BlotPaper", (0.42, 0.38, 0.33), 0.9), bevel=0.0, segments=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = 0.25 + sx * 0.92, -0.35 + sy * 0.55
            prism(f"BlotCorner{sx}{sy}", [(cx + sx * 0.08, cy + sy * 0.08), (cx - sx * 0.14, cy + sy * 0.08), (cx + sx * 0.08, cy - sy * 0.14)],
                  zt + 0.044, 0.02, gl, plane="XY")
    # the inkstand: a brass tray, two inkwells with brass lids, quills, a pen groove
    ix, iy = -2.2, 0.0
    box("InkTray", (1.3, 0.72, 0.05), (ix, iy, zt + 0.025), gl, bevel=0.015)
    tube("InkTrayRim", [(ix - 0.62, iy - 0.33, zt + 0.06), (ix + 0.62, iy - 0.33, zt + 0.06), (ix + 0.62, iy + 0.33, zt + 0.06),
                        (ix - 0.62, iy + 0.33, zt + 0.06)], 0.014, gl, closed=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"InkFoot{sx}{sy}", 0.03, (ix + sx * 0.58, iy + sy * 0.3, zt + 0.0), gl, seg=6, rings=3)
    box("PenGroove", (1.0, 0.14, 0.02), (ix, iy - 0.2, zt + 0.06), M["leatherdark"], bevel=0.005)
    for k, wx in enumerate((ix - 0.35, ix + 0.35)):
        lathe(f"Well{k}", [(0, zt + 0.05), (0.15, zt + 0.05), (0.17, zt + 0.12), (0.16, zt + 0.22), (0.08, zt + 0.25), (0.05, zt + 0.27), (0, zt + 0.27)],
              ink, seg=16, loc=(wx, iy + 0.08, 0))
        lathe(f"WellLid{k}", [(0, zt + 0.26), (0.065, zt + 0.26), (0.07, zt + 0.29), (0.035, zt + 0.32), (0.015, zt + 0.36), (0, zt + 0.37)], gl,
              seg=12, loc=(wx, iy + 0.08, 0))
    # quills standing in the left well, one lying in the groove
    for k, (yaw, pitch, mat) in enumerate(((2.2, 1.15, feather), (2.6, 1.25, feather_dk))):
        base = (ix - 0.35, iy + 0.08, zt + 0.26)
        d = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
        tip = Vector(base) + d * 0.75
        tube(f"QuillShaft{k}", [base, tuple(tip)], 0.008, feather, poly=True)
        leaf(f"QuillVane{k}", tuple(Vector(base) + d * 0.22), yaw, pitch, 0.56, 0.06, 0.04, mat, n=8, fold=0.1, thick=0.006)
    leaf("QuillLying", (ix - 0.4, iy - 0.2, zt + 0.08), 0.05, 0.02, 0.8, 0.05, 0.0, feather, n=8, fold=0.1, thick=0.006)
    # the name plaque: a lacquer wedge with a brass plate and a crest (no lettering)
    prism("PlaqueWedge", [(-1.1, zt), (-1.32, zt), (-1.12, zt + 0.2)], 0.25, 1.3, lq, plane="YZ")
    box("PlaqueBrass", (1.15, 0.015, 0.2), (0.25, -1.232, zt + 0.108), gl, bevel=0.005, rot=(math.radians(-45), 0, 0))
    q = _mark()
    qf("PlaqueCrest", 0, 0, 0, 0.055, lq)
    _xform(q, Matrix.Translation((0.25, -1.245, zt + 0.12)) @ Matrix.Rotation(math.radians(-45), 4, "X"))
    # a stack of files tied with crimson tape
    fx, fy = 2.55, 0.35
    for k in range(5):
        a = math.radians((-4, 3, -2, 5, -1)[k])
        box(f"File{k}", (1.25, 0.95, 0.07), (fx + 0.02 * k, fy - 0.01 * k, zt + 0.035 + k * 0.075), (M["inkblue"], M["paper"], M["leather"], M["paper"], M["inkblue"])[k],
            bevel=0.01, rot=(0, 0, a))
    box("FileTape", (0.08, 0.98, 0.4), (fx + 0.1, fy - 0.02, zt + 0.2), M["crimson"], bevel=0.006)
    box("FileTapeX", (1.28, 0.08, 0.4), (fx + 0.04, fy - 0.02, zt + 0.2), M["crimson"], bevel=0.006)
    # the desk bell
    bx, by = -3.05, -0.8
    lathe("BellBase", [(0, zt), (0.2, zt), (0.21, zt + 0.03), (0.18, zt + 0.05), (0, zt + 0.05)], lq, seg=20, loc=(bx, by, 0))
    lathe("Bell", [(0, zt + 0.05), (0.17, zt + 0.05), (0.17, zt + 0.08), (0.15, zt + 0.15), (0.1, zt + 0.21), (0.03, zt + 0.23), (0, zt + 0.235)],
          gl, seg=20, loc=(bx, by, 0))
    tube("BellPlunger", [(bx, by, zt + 0.23), (bx, by, zt + 0.3)], 0.012, gl, poly=True)
    sphere("BellKnob", 0.03, (bx, by, zt + 0.31), gl, seg=8, rings=4)
    return _dims()


# ================================================================== the Headmaster's chair
def headmaster_chair(M):
    W, D, SH = 3.0, 2.8, 1.6
    lq, gl = lacquer(), gilt()
    lea, lead = M["leather"], M["leatherdark"]
    set_group("Main")
    yb = D / 2 - 0.28                     # back post line
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.22)
        # front legs: turned lacquer with gilt collars on brass ball feet
        lathe(f"FrontLeg{sx}", [(0, 0.1), (0.1, 0.1), (0.13, 0.3), (0.09, 0.45), (0.12, 0.6), (0.08, 0.8), (0.1, 1.15), (0.11, 1.3), (0, 1.3)],
              lq, seg=14, loc=(x, -D / 2 + 0.25, 0))
        sphere(f"FrontFoot{sx}", 0.11, (x, -D / 2 + 0.25, 0.11), gl, seg=10, rings=6)
        hoop(f"FrontCollar{sx}", (x, -D / 2 + 0.25, 0.6), 0.125, "Z", gl, thick=0.02)
        # back posts rising to gilt pinnacles
        box(f"BackPost{sx}", (0.22, 0.24, 6.0), (x, yb, 3.0), lq, bevel=0.03)
        sphere(f"BackFoot{sx}", 0.11, (x, yb, 0.11), gl, seg=10, rings=6)
        for z in (0.5, 1.3, 5.3):
            box(f"PostBand{sx}{z}", (0.25, 0.27, 0.05), (x, yb, z), gl, bevel=0.01)
        _spirelet(f"PostSpire{sx}", x, yb, 6.0, 0.95, 0.22, gl, crockets=2)
        # arms: a lacquer rest on a turned support with a gilt scroll end, a leather pad
        lathe(f"ArmSupport{sx}", [(0, SH), (0.08, SH), (0.1, SH + 0.15), (0.06, SH + 0.35), (0.09, SH + 0.6), (0.06, SH + 0.8), (0, SH + 0.8)],
              lq, seg=12, loc=(x, -D / 2 + 0.3, 0))
        box(f"ArmRest{sx}", (0.26, D - 0.55, 0.12), (x, 0.0, SH + 0.86), lq, bevel=0.04)
        box(f"ArmPad{sx}", (0.2, D - 0.95, 0.08), (x, 0.1, SH + 0.95), lea, bevel=0.035)
        cyl(f"ArmScroll{sx}", 0.1, 0.27, (x, -D / 2 + 0.22, SH + 0.82), gl, rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
        qf(f"ArmSeal{sx}", x + sx * 0.14, -D / 2 + 0.22, SH + 0.82, 0.06, lq)
        # wings
        wx = sx * (W / 2 - 0.3)
        box(f"Wing{sx}", (0.28, 1.35, 2.75), (wx, yb - 0.55, SH + 2.35), lea, bevel=0.12, segments=3)
        box(f"WingFrame{sx}", (0.1, 1.4, 0.1), (sx * (W / 2 - 0.2), yb - 0.55, SH + 3.75), lq, bevel=0.03)
        tube(f"WingEdge{sx}", [(wx, yb - 1.24, SH + 1.0), (wx + sx * 0.02, yb - 1.26, SH + 2.35), (wx, yb - 1.22, SH + 3.68)], 0.025, gl)
        for k in range(8):
            sphere(f"WingNail{sx}{k}", 0.02, (wx + sx * 0.145, yb - 1.15, SH + 1.1 + k * 0.36), gl, seg=6, rings=3)
    # seat frame, seat cushion with a front roll, nailheads
    box("SeatRail", (W - 0.3, D - 0.35, 0.3), (0, 0.0, SH - 0.3), lq, bevel=0.03)
    tube("SeatBead", [(-W / 2 + 0.2, -D / 2 + 0.16, SH - 0.43), (W / 2 - 0.2, -D / 2 + 0.16, SH - 0.43)], 0.02, gl, poly=True)
    box("Seat", (W - 0.6, D - 0.7, 0.34), (0, -0.05, SH + 0.02), lea, bevel=0.13, segments=3)
    cyl("SeatRoll", 0.13, W - 0.7, (0, -D / 2 + 0.42, SH + 0.04), lea, rot=(0, math.pi / 2, 0), verts=16)
    for k in range(13):
        x = -(W - 0.7) / 2 + k * (W - 0.7) / 12
        sphere(f"Nail{k}", 0.022, (x, -D / 2 + 0.17, SH - 0.22), gl, seg=6, rings=3)
    # the tall tufted back
    bw = W - 0.66
    box("Back", (bw, 0.32, 3.9), (0, yb - 0.02, SH + 2.15), lea, bevel=0.13, segments=3)
    # diamond button-tufting: buttons on a staggered grid, creases running diagonally between them
    nx, nz = 5, 8
    x0, x1, z0, z1 = -bw / 2 + 0.2, bw / 2 - 0.2, SH + 0.5, SH + 3.85
    yt = yb - 0.185
    grid = {}
    for j in range(nz):
        for i in range(nx + (j % 2)):
            x = x0 + (x1 - x0) * ((i + (0.0 if j % 2 else 0.5)) / nx)
            if not (x0 - 1e-6 <= x <= x1 + 1e-6):
                continue
            z = z0 + (z1 - z0) * j / (nz - 1)
            grid[(i, j)] = (x, z)
            sphere(f"Button{i}{j}", 0.04, (x, yt + 0.005, z), lead, seg=8, rings=4, scale=(1, 0.6, 1))
    for (i, j), (x, z) in grid.items():
        for di in ((0, 1) if j % 2 == 0 else (-1, 0)):
            n = grid.get((i + di, j + 1))
            if n:
                tube(f"Crease{i}{j}{di}", [(x, yt, z), (n[0], yt, n[1])], 0.009, lead, poly=True)
    # the pointed gable over the back with a carved crest
    _gable("Gable", 0, yb, bw / 2 + 0.1, SH + 4.05, SH + 5.15, 0.22, lq, gl, edge=0.035)
    box("GableBase", (bw + 0.3, 0.3, 0.14), (0, yb, SH + 4.05), lq, bevel=0.03)
    tube("GableBaseBead", [(-bw / 2 - 0.15, yb - 0.16, SH + 4.0), (bw / 2 + 0.15, yb - 0.16, SH + 4.0)], 0.018, gl, poly=True)
    shield = mirror_half([(0, SH + 4.95), (0.32, SH + 4.95), (0.32, SH + 4.55), (0.25, SH + 4.35), (0.1, SH + 4.24), (0, SH + 4.2)])
    relief("Shield", shield, yb - 0.13, 0.05, M["crimson"])
    tube("ShieldEdge", [(x, yb - 0.165, z) for x, z in shield] + [(shield[0][0], yb - 0.165, shield[0][1])], 0.016, gl, square=True, poly=True)
    qf("ShieldSeal", 0, yb - 0.17, SH + 4.6, 0.12, gl)
    sphere("GableFinial", 0.09, (0, yb, SH + 5.27), gl, seg=10, rings=5)
    _spike("GableSpike", (0, yb, SH + 5.45), 0.04, 0.3, gl, verts=6)
    return _dims()


# ================================================================== fireplace
def fireplace(M):
    st = material("FireStone", "NH_Limestone", tint=(0.155, 0.165, 0.15), scale=0.28, wear=0.2, dirt=1.0)    # dark castle stone
    dk = material("FireStoneDark", "NH_Limestone", tint=(0.12, 0.125, 0.115), scale=0.28, wear=0.16, dirt=1.0)
    sooty = soot_stone("FireStoneSooty", (0.155, 0.165, 0.15), (0.0, 0.0, 3.35), 2.9, 1.25, darkest=0.08)
    gl = gilt()
    soot = flat("Soot", (0.018, 0.016, 0.016), 0.95, dirt=0.3)
    logm = flat("CharredLog", (0.07, 0.042, 0.026), 0.85, wear=0.1)
    char = flat("Char", (0.025, 0.02, 0.018), 0.9)
    fire = flat("Fire", (1.0, 0.55, 0.15), 0.5)
    hot = flat("HotCoal", (0.85, 0.2, 0.03), 0.55)
    sootmark = flat("SootMark", (0.022, 0.02, 0.019), 0.95, dirt=0.3)
    bone = flat("Bone", (0.74, 0.69, 0.58), 0.55, dirt=0.8)
    dark = flat("Hollow", (0.015, 0.012, 0.012), 0.9)
    W, YW = 7.0, 0.6                    # width; the wall plane (the back) at +Y
    yf = -0.4                           # breast front face
    zs, za = 2.6, 3.3                   # arch springing and apex
    ow = 2.2                            # half opening width
    set_group("Main")
    # the jamb piers and the arch head (a panel with a four-centred arch cut from its lower edge)
    for sx in (-1, 1):
        box(f"Pier{sx}", (W / 2 - ow, YW - yf, 3.95), (sx * (W / 2 + ow) / 2, (YW + yf) / 2, 1.975), sooty, bevel=0.05)
        box(f"PierPlinth{sx}", (W / 2 - ow + 0.12, YW - yf + 0.12, 0.35), (sx * (W / 2 + ow) / 2, (YW + yf) / 2 - 0.06, 0.175), dk, bevel=0.04)
        column(f"Jamb{sx}", sx * (ow + 0.2), yf - 0.15, 0.35, zs, 0.16, st, dk)
        box(f"SootCheek{sx}", (0.04, YW - yf - 0.1, zs), (sx * (ow - 0.02), (YW + yf) / 2, zs / 2), soot, bevel=0.0, segments=1)
    head = [(-ow, 3.95), (ow, 3.95)] + list(reversed(_gothic_pts(-ow, ow, zs, za, 12)))
    relief("ArchHead", head, (YW + yf) / 2, YW - yf, sooty)
    tube("ArchMould", [(x, yf - 0.03, z - 0.02) for x, z in _gothic_pts(-ow + 0.03, ow - 0.03, zs, za, 12)], 0.05, dk, square=True, poly=True)
    tube("ArchMould2", [(x * 1.06, yf - 0.03, z + 0.13) for x, z in _gothic_pts(-ow, ow, zs, za, 12)], 0.03, dk, poly=True)
    for sx in (-1, 1):
        foil(f"Spandrel{sx}", sx * 1.4, yf - 0.02, 3.58, 0.24, dk, lobes=4, thick=0.03)
        foil(f"SpandrelSmall{sx}", sx * 2.75, yf - 0.02, 3.55, 0.16, dk, lobes=3, thick=0.025)
    _grotesque("Keystone", Matrix.Translation((0, yf - 0.05, 3.62)) @ Matrix.Scale(0.75, 4), st, dark)
    # inside: sooty back and floor
    box("FireBack", (2 * ow, 0.1, za), (0, YW - 0.05, za / 2), soot, bevel=0.0, segments=1)
    for k in range(5):
        tube(f"BackPlateRib{k}", [(-1.4 + k * 0.7, YW - 0.17, 0.45), (-1.4 + k * 0.7, YW - 0.17, 2.05)], 0.03, M["iron"], square=True, poly=True)
    box("FireBackPlate", (3.2, 0.05, 1.8), (0, YW - 0.12, 1.25), M["iron"], bevel=0.02)
    qf("FireBackSeal", 0, YW - 0.17, 1.65, 0.3, M["iron"])
    # the hearth: an inner stone floor and a black marble slab in front, an iron fender with brass knobs
    box("HearthIn", (2 * ow, YW - yf, 0.3), (0, (YW + yf) / 2, 0.15), dk, bevel=0.02)
    box("Hearth", (W - 0.8, 1.05, 0.28), (0, yf - 0.5, 0.14), black_marble(), bevel=0.04)
    tube("Fender", [(-2.6, -1.3, 0.48), (2.6, -1.3, 0.48)], 0.035, M["iron"], poly=True)
    tube("FenderLow", [(-2.6, -1.3, 0.34), (2.6, -1.3, 0.34)], 0.025, M["iron"], poly=True)
    for k in range(14):
        x = -2.6 + k * 5.2 / 13
        tube(f"FenderBar{k}", [(x, -1.3, 0.28), (x, -1.3, 0.48)], 0.015, M["iron"], poly=True)
    for sx in (-1, 1):
        tube(f"FenderEnd{sx}", [(sx * 2.6, -1.3, 0.48), (sx * 2.6, -0.5, 0.48)], 0.035, M["iron"], poly=True)
        sphere(f"FenderKnob{sx}", 0.07, (sx * 2.6, -1.3, 0.55), M["brass"], seg=10, rings=5)
    # fire dogs: iron andirons with a log bar running back, gothic posts with brass finials, scrolled feet
    zh = 0.3                                     # hearth top
    for sx in (-1, 1):
        x = sx * 0.95
        tube(f"DogBar{sx}", [(x, -0.38, zh + 0.16), (x, 0.42, zh + 0.16), (x, 0.45, zh)], 0.04, M["iron"], square=True, poly=True)
        lathe(f"DogPost{sx}", [(0, zh), (0.1, zh), (0.08, zh + 0.08), (0.05, zh + 0.12), (0.05, zh + 0.45), (0.08, zh + 0.5), (0.05, zh + 0.56),
                               (0.045, zh + 0.8), (0, zh + 0.8)], M["iron"], seg=10, loc=(x, -0.42, 0))
        lathe(f"DogFinial{sx}", [(0, zh + 0.8), (0.07, zh + 0.8), (0.1, zh + 0.88), (0.08, zh + 0.97), (0.04, zh + 1.04), (0.05, zh + 1.08), (0, zh + 1.16)],
              M["brass"], seg=12, loc=(x, -0.42, 0))
        for fx in (-1, 1):
            tube(f"DogFoot{sx}{fx}", [(x, -0.42, zh + 0.1), (x + fx * 0.16, -0.46, zh + 0.05), (x + fx * 0.2, -0.5, zh)], 0.025, M["iron"], poly=True)
    # a low front grate rail between the dogs
    for z in (zh + 0.12, zh + 0.3):
        tube(f"GrateRail{z:.2f}", [(-0.9, -0.3, z), (0.9, -0.3, z)], 0.022, M["iron"], poly=True)
    for k in range(7):
        x = -0.75 + k * 0.25
        tube(f"GrateBar{k}", [(x, -0.3, zh + 0.02), (x, -0.3, zh + 0.34)], 0.018, M["iron"], poly=True)
    # crossed logs on the dogs and a third laid across them
    rnd = random.Random(31)
    logs = (((-1.15, 0.3, zh + 0.34), (1.05, -0.12, zh + 0.36), 0.15), ((1.15, 0.3, zh + 0.36), (-1.05, -0.08, zh + 0.38), 0.14),
            ((-0.55, -0.05, zh + 0.62), (0.75, 0.32, zh + 0.58), 0.12))
    for k, (a, b, r) in enumerate(logs):
        tube(f"Log{k}", [a, b], r, logm, poly=True)
        for e in (a, b):
            sphere(f"LogEnd{k}{e[0]:.1f}", r * 0.9, e, char, seg=8, rings=4, scale=(0.4, 1, 1))
    # the coal bed under them: dead coals and hot ones
    for k in range(16):
        lump(f"Coal{k}", (rnd.uniform(-0.95, 0.95), rnd.uniform(-0.25, 0.4), zh + rnd.uniform(0.03, 0.08)), rnd.uniform(0.06, 0.1),
             hot if k % 3 == 0 else char, rnd)
    # the mantel: shelf and moulding on carved corbels
    box("MantelMould", (W + 0.1, 1.15, 0.14), (0, (YW + yf) / 2 - 0.1, 4.02), dk, bevel=0.04)
    box("Mantel", (W + 0.35, 1.4, 0.2), (0, (YW + yf) / 2 - 0.2, 4.19), st, bevel=0.05)
    for sx in (-1, 1):
        prism(f"Corbel{sx}", [(yf, 3.95), (yf - 0.42, 3.95), (yf - 0.42, 3.82), (yf - 0.12, 3.5), (yf, 3.4)], sx * (W / 2 - 0.55), 0.6, dk, plane="YZ", bevel=0.02)
    zm = 4.29
    # the overmantel: a set-back breast with blind tracery round a carved shield, a battlemented cornice
    yo = 0.05
    box("Overmantel", (W - 0.8, YW - yo, 2.6), (0, (YW + yo) / 2, zm + 1.3), st, bevel=0.04)
    for cx in (-2.05, 2.05):
        tracery(f"Tracery{cx}", cx, yo, 0.7, zm + 0.3, zm + 1.55, zm + 2.25, dk, recess=flat("Recess", (0.07, 0.066, 0.062), 0.9))
    shield = mirror_half([(0, zm + 2.25), (0.62, zm + 2.25), (0.62, zm + 1.25), (0.48, zm + 0.8), (0.22, zm + 0.48), (0, zm + 0.38)])
    relief("Shield", shield, yo, 0.1, M["crimson"])
    tube("ShieldEdge", [(x, yo - 0.07, z) for x, z in shield] + [(shield[0][0], yo - 0.07, shield[0][1])], 0.03, gl, square=True, poly=True)
    tube("ShieldCrossV", [(0, yo - 0.07, zm + 2.2), (0, yo - 0.07, zm + 0.45)], 0.022, gl, square=True, poly=True)
    tube("ShieldCrossH", [(-0.6, yo - 0.07, zm + 1.45), (0.6, yo - 0.07, zm + 1.45)], 0.022, gl, square=True, poly=True)
    for k, (x, z) in enumerate(((-0.3, zm + 1.85), (0.3, zm + 1.85), (-0.25, zm + 1.1), (0.25, zm + 1.1))):
        qf(f"ShieldFoil{k}", x, yo - 0.075, z, 0.1, gl)
    # a moulded pointed-arch panel framing the crest, with crockets up its hood and a finial
    hood = _arch_loop(0, yo - 0.05, 0.92, zm + 0.28, zm + 1.75, zm + 2.5)
    tube("CrestPanel", hood, 0.05, dk, square=True, closed=True, poly=True)
    tube("CrestPanelInner", _arch_loop(0, yo - 0.04, 0.82, zm + 0.36, zm + 1.75, zm + 2.38), 0.025, dk, poly=True, closed=True)
    _crockets("CrestCrocket", [p for p in hood if p[2] > zm + 1.8][1:-1], dk, size=0.07)
    # the cornice: a moulded shelf with a hollow, a row of trefoil cresting, a central crocketed gable over the crest
    box("CorniceHollow", (W - 0.7, YW - yo + 0.1, 0.12), (0, (YW + yo) / 2 - 0.05, zm + 2.54), dk, bevel=0.03, segments=1)
    box("Cornice", (W - 0.5, YW - yo + 0.3, 0.2), (0, (YW + yo) / 2 - 0.15, zm + 2.7), st, bevel=0.05)
    zc_ = zm + 2.8
    ycr = yo - 0.08
    n = 13
    for k in range(n):
        x = -(W - 0.9) / 2 + k * (W - 0.9) / (n - 1)
        if abs(x) < 0.75:
            continue
        relief(f"Cresting{k}", trefoil_poly(x, zc_ + 0.0, 0.52), ycr, 0.06, st)
    tube("CrestingRail", [(-(W - 0.9) / 2, ycr, zc_ + 0.02), ((W - 0.9) / 2, ycr, zc_ + 0.02)], 0.03, dk, square=True, poly=True)
    _gable("TopGable", 0, ycr + 0.06, 0.62, zc_, zc_ + 0.55, 0.2, st, dk, edge=0.035)
    foil("TopGableFoil", 0, ycr - 0.05, zc_ + 0.22, 0.12, dk, lobes=4, thick=0.022)
    gp = [(0.62 - 0.62 * t, ycr - 0.02, zc_ + 0.55 * (0.45 * t + 0.55 * math.sin(t * math.pi / 2))) for t in (0.3, 0.65)]
    _crockets("GableCrocketR", gp, dk, size=0.06)
    _crockets("GableCrocketL", [(-x, y, z) for x, y, z in gp], dk, size=0.06)
    _spirelet("TopFinial", 0, ycr + 0.06, zc_ + 0.52, 0.3, 0.1, dk, crockets=1)
    # on the mantel: two candlesticks with candles, a skull and a gothic clock
    wax = wax_mat()
    for sx in (-1, 1):
        top = candlestick(f"Stick{sx}", sx * 3.0, -0.35, zm, 0.55, M["brass"])
        candle(f"Candle{sx}", sx * 3.0, -0.35, top, 0.5, wax, r=0.06)
    _skull("Skull", Matrix.Translation((-1.25, -0.4, zm)) @ Matrix.Rotation(math.radians(18), 4, "Z"), bone, dark)
    cx = 1.15
    box("ClockCase", (0.6, 0.35, 0.65), (cx, -0.35, zm + 0.325), lacquer(), bevel=0.03)
    _gable("ClockGable", cx, -0.35, 0.32, zm + 0.65, zm + 0.98, 0.3, lacquer(), gl, edge=0.02)
    cyl("ClockBezel", 0.21, 0.04, (cx, -0.53, zm + 0.38), gl, rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
    cyl("ClockDial", 0.18, 0.01, (cx, -0.552, zm + 0.38), M["paper"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        box(f"ClockTick{k}", (0.012, 0.006, 0.035), (cx + math.sin(a) * 0.15, -0.558, zm + 0.38 + math.cos(a) * 0.15), M["glass"], bevel=0.0,
            segments=1, rot=(0, -a, 0))
    box("ClockHourHand", (0.014, 0.006, 0.09), (cx + 0.03, -0.56, zm + 0.41), M["glass"], bevel=0.0, segments=1, rot=(0, -0.7, 0))
    box("ClockMinHand", (0.01, 0.006, 0.14), (cx - 0.04, -0.56, zm + 0.43), M["glass"], bevel=0.0, segments=1, rot=(0, 0.5, 0))
    for sx in (-1, 1):
        sphere(f"ClockFoot{sx}", 0.04, (cx + sx * 0.25, -0.5, zm + 0.01), gl, seg=6, rings=3)
    # the fire: embers in the coal bed and tapered flame tongues rising from the logs
    set_group("Glow")
    for k in range(10):
        lump(f"Ember{k}", (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.2, 0.35), zh + rnd.uniform(0.04, 0.1)), rnd.uniform(0.05, 0.08), fire, rnd, squash=0.7)
    flames = ((-0.7, 0.12, zh + 0.42, 0.55, 0.2, 0.14), (-0.38, 0.02, zh + 0.5, 0.9, 0.25, -0.1), (-0.02, 0.12, zh + 0.62, 1.05, 0.27, 0.06),
              (0.34, 0.04, zh + 0.52, 0.85, 0.24, 0.12), (0.7, 0.16, zh + 0.42, 0.5, 0.18, -0.14), (-0.15, -0.14, zh + 0.45, 0.48, 0.15, 0.16),
              (0.18, 0.3, zh + 0.6, 0.7, 0.2, -0.12), (-0.55, 0.32, zh + 0.45, 0.45, 0.15, 0.1), (0.95, 0.0, zh + 0.38, 0.32, 0.12, 0.08),
              (-0.95, 0.05, zh + 0.38, 0.3, 0.12, -0.06))
    for k, (x, y, z, h, w, lean) in enumerate(flames):
        tongue(f"Flame{k}", (x, y, z), h, w, lean, rnd.uniform(-0.5, 0.5), fire)
    set_group("Main")
    return _dims()


def portrait_bg(W, H, glow):
    """An oil portrait's ground (canvas object space, centred): a warm umber glow behind the sitter's head fading to
    near-black at the edges, vertical and diagonal brush strokes, and canvas weave in the normal."""
    m = bpy.data.materials.new("PortraitGround")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])

    def mth(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    dx = mth("MULTIPLY", mth("SUBTRACT", sep.outputs["X"], glow[0]), 1.0 / (W * 0.5))
    dz = mth("MULTIPLY", mth("SUBTRACT", sep.outputs["Z"], glow[1]), 1.0 / (H * 0.5))
    d = mth("SQRT", mth("ADD", mth("MULTIPLY", dx, dx), mth("MULTIPLY", dz, dz)))
    wob = nt.nodes.new("ShaderNodeTexNoise")
    wob.inputs["Scale"].default_value = 2.5
    wob.inputs["Detail"].default_value = 5.0
    L(tc.outputs["Object"], wob.inputs["Vector"])
    d = mth("ADD", d, mth("MULTIPLY", mth("SUBTRACT", wob.outputs["Fac"], 0.5), 0.35))
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.3, 0.15, 0.065, 1)
    e[1].position, e[1].color = 1.1, (0.008, 0.006, 0.006, 1)
    mid = e.new(0.45)
    mid.color = (0.06, 0.03, 0.018, 1)
    L(d, ramp.inputs["Fac"])
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (14.0, 2.0, 3.0)
    mp.inputs["Rotation"].default_value = (0.0, 0.5, 0.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 5.0
    st.inputs["Detail"].default_value = 3.0
    L(mp.outputs["Vector"], st.inputs["Vector"])
    shade = mth("ADD", mth("MULTIPLY", st.outputs["Fac"], 0.55), 0.72)
    cm = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        L(shade, cm.inputs[i])
    mm = nt.nodes.new("ShaderNodeMix")
    mm.data_type = "RGBA"
    mm.blend_type = "MULTIPLY"
    mm.inputs[0].default_value = 1.0
    L(ramp.outputs["Color"], mm.inputs[6])
    L(cm.outputs["Color"], mm.inputs[7])
    cv = nt.nodes.new("ShaderNodeTexNoise")
    cv.inputs["Scale"].default_value = 90.0
    L(tc.outputs["Object"], cv.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    L(mth("ADD", st.outputs["Fac"], mth("MULTIPLY", cv.outputs["Fac"], 0.5)), bump.inputs["Height"])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mm.outputs[2], 0.9, mv.outputs[0], bump.outputs["Normal"], 0.0, False, 0.3)
    return m


def _render_paint(start, path, W, H, zc, px=(360, 495)):
    """Render the painted layers built since `start` (the backdrop and the figure) straight on, small, to an image,
    then delete them: the canvas carries the image instead, so the upscale softens every edge like brushwork and the
    layers' soft occlusion reads as painterly shadow, with no cut-out paper look."""
    sc = bpy.context.scene
    objs = P.PARTS[start:]
    wd = bpy.data.worlds.new("PaintLight")
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = wd
    cam = bpy.data.cameras.new("PaintCam")
    cam.type = "ORTHO"
    cam.ortho_scale = H
    co = bpy.data.objects.new("PaintCam", cam)
    bpy.context.collection.objects.link(co)
    co.location = (0, -6, zc)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    for o in objs:                      # albedo only: no specular sheen lifting the shadows
        for slot in o.material_slots:
            for n in slot.material.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    n.inputs["Specular IOR Level"].default_value = 0.0
    keep = (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath)
    sc.render.resolution_x, sc.render.resolution_y = px
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 48
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples, sc.render.filepath = keep
    sc.camera = None
    sc.world = None
    bpy.data.objects.remove(co, do_unlink=True)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    del P.PARTS[start:]


def paint_mat(path, W, H):
    """The rendered painting on the canvas (object space, centred), with brush strokes and canvas weave on top."""
    m = bpy.data.materials.new("Painting")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    mp.inputs["Location"].default_value = (0.5, 0.5, 0.0)
    mp.inputs["Scale"].default_value = (1.0 / W, 1.0, 1.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(mp.outputs["Vector"], sep.inputs[0])
    vz = nt.nodes.new("ShaderNodeMath")
    vz.operation = "MULTIPLY_ADD"
    sz = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sz.inputs[0])
    L(sz.outputs["Z"], vz.inputs[0])
    vz.inputs[1].default_value, vz.inputs[2].default_value = 1.0 / H, 0.5
    uv = nt.nodes.new("ShaderNodeCombineXYZ")
    L(sep.outputs["X"], uv.inputs["X"])
    L(vz.outputs[0], uv.inputs["Y"])
    im = nt.nodes.new("ShaderNodeTexImage")
    im.image = bpy.data.images.load(path, check_existing=False)
    im.interpolation = "Cubic"
    im.extension = "EXTEND"
    L(uv.outputs[0], im.inputs["Vector"])
    st_map = nt.nodes.new("ShaderNodeMapping")
    st_map.inputs["Scale"].default_value = (10.0, 2.0, 3.0)
    st_map.inputs["Rotation"].default_value = (0.0, 0.6, 0.0)
    L(tc.outputs["Object"], st_map.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 6.0
    st.inputs["Detail"].default_value = 3.0
    L(st_map.outputs["Vector"], st.inputs["Vector"])
    sh = nt.nodes.new("ShaderNodeMath")
    sh.operation = "MULTIPLY_ADD"
    L(st.outputs["Fac"], sh.inputs[0])
    sh.inputs[1].default_value, sh.inputs[2].default_value = 0.35, 0.83
    cm = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        L(sh.outputs[0], cm.inputs[i])
    mm = nt.nodes.new("ShaderNodeMix")
    mm.data_type = "RGBA"
    mm.blend_type = "MULTIPLY"
    mm.inputs[0].default_value = 1.0
    L(im.outputs["Color"], mm.inputs[6])
    L(cm.outputs["Color"], mm.inputs[7])
    cv = nt.nodes.new("ShaderNodeTexNoise")
    cv.inputs["Scale"].default_value = 90.0
    L(tc.outputs["Object"], cv.inputs["Vector"])
    hb = nt.nodes.new("ShaderNodeMath")
    hb.operation = "MULTIPLY_ADD"
    L(cv.outputs["Fac"], hb.inputs[0])
    hb.inputs[1].default_value = 0.5
    L(st.outputs["Fac"], hb.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    L(hb.outputs[0], bump.inputs["Height"])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mm.outputs[2], 0.9, mv.outputs[0], bump.outputs["Normal"], 0.0, False, 0.0)
    return m


# ================================================================== the founder's portrait
def founder_portrait(M):
    W, H, FW = 3.2, 4.4, 0.45
    zc = FW + H / 2
    gl = gilt()
    pflat = lambda n, c, r: flat(n, c, r, dirt=0.0)   # painted layers: no crevice dirt between them
    lq = lacquer()
    # muted oil colours, all lit from the upper left: the sitter's right side falls into shadow
    BROAD = (-1.05, 0.35)
    ZR = (zc - 2.0, zc + 0.6)
    robe = oil("Robe", (0.12, 0.1, 0.105), *BROAD, floor=0.06, z_range=ZR)
    robe_hi = oil("RobeFold", (0.2, 0.17, 0.165), *BROAD, floor=0.06, z_range=ZR)
    stole = oil("Stole", (0.45, 0.06, 0.05), *BROAD, floor=0.07, z_range=ZR)
    beard = oil("Beard", (0.4, 0.37, 0.33), -0.24, 0.2, floor=0.08)
    hair = oil("Hair", (0.26, 0.24, 0.21), -0.32, 0.2, floor=0.06)
    ruff = oil("Ruff", (0.42, 0.38, 0.31), -0.38, 0.3, floor=0.08)
    eye = oil("PaintEye", (0.06, 0.04, 0.03), -0.3, 0.3, floor=0.5)
    sk = oil("Skin", (0.56, 0.37, 0.26), -0.26, 0.08, floor=0.08)
    sk_sh = oil("SkinShade", (0.24, 0.15, 0.1), -0.26, 0.08, floor=0.2)
    gold = oil("PaintGold", (0.72, 0.52, 0.2), *BROAD, floor=0.08)
    hand = oil("Hand", (0.6, 0.41, 0.29), *BROAD, floor=0.08)
    set_group("Main")
    paint_start = _mark()
    box("Backdrop", (W, 0.04, H), (0, 0.04, zc), portrait_bg(W, H, (-0.5, 1.15)), bevel=0.0, segments=1)
    # the painting's figure, in thin painted layers toward the viewer
    y0 = 0.016
    zb, zt = zc - H / 2 + 0.01, zc + H / 2
    # layers step 0.01 toward the viewer and are 0.003 thick, so no two painted faces touch (touching faces z-fight)
    T = 0.003

    def lay(n):
        return y0 - 0.01 * n

    def strip2(name, pts, w, layer, mat):
        """A flat painted stroke along a polyline (x, z), w wide, on a layer."""
        poly_l, poly_r = [], []
        for k, (x, z) in enumerate(pts):
            a, b = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
            dx_, dz_ = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx_, dz_) or 1.0
            nx_, nz_ = -dz_ / ln * w / 2, dx_ / ln * w / 2
            poly_l.append((x + nx_, z + nz_))
            poly_r.append((x - nx_, z - nz_))
        relief(name, poly_l + list(reversed(poly_r)), lay(layer), T, mat)
    # a crimson curtain swag down the right side, with a gold tassel
    curtain = oil("Curtain", (0.2, 0.02, 0.028), 0.3, 1.6, floor=0.15, z_range=(zc - 2.0, zc + 2.0))
    curtain_hi = oil("CurtainFold", (0.34, 0.045, 0.045), 0.3, 1.6, floor=0.15, z_range=(zc - 2.0, zc + 2.0))
    paint_gold = oil("PaintGoldCord", (0.55, 0.39, 0.15), 0.3, 1.6, floor=0.15)
    cpts = [(W / 2 - 0.01, zt - 0.01), (W / 2 - 1.05, zt - 0.01), (W / 2 - 0.95, zt - 0.55), (W / 2 - 0.7, zt - 1.1), (W / 2 - 0.45, zt - 1.45),
            (W / 2 - 0.36, zb + 1.0), (W / 2 - 0.5, zb + 0.01), (W / 2 - 0.01, zb + 0.01)]
    relief("Curtain", cpts, lay(0), T, curtain)
    for k, (xa, xb) in enumerate(((0.85, 0.55), (0.6, 0.42), (0.35, 0.22))):
        strip2(f"CurtainFold{k}", [(W / 2 - xa, zt - 0.05), (W / 2 - xa * 0.75 - 0.05, zt - 1.0), (W / 2 - xb, zb + 0.6)], 0.035, 1, curtain_hi)
    strip2("TasselCord", [(W / 2 - 0.7, zt - 1.1), (W / 2 - 0.5, zt - 1.35)], 0.025, 3, paint_gold)
    relief("Tassel", [(W / 2 - 0.55, zt - 1.35), (W / 2 - 0.45, zt - 1.35), (W / 2 - 0.42, zt - 1.62), (W / 2 - 0.58, zt - 1.62)], lay(3), T, paint_gold)
    # the robe, its folds, the crimson stole, sleeves
    robe_poly = mirror_half([(0, zc + 1.0), (0.24, zc + 0.98), (0.62, zc + 0.86), (0.95, zc + 0.7), (1.12, zc + 0.35), (1.2, zc - 0.4),
                             (1.3, zb), (0, zb)])
    relief("Robe", robe_poly, lay(2), T, robe)
    for k, x in enumerate((-0.75, -0.42, 0.6, 0.9)):
        strip2(f"Fold{k}", [(x, zb + 0.02), (x * 0.96 + 0.03, zc - 0.4), (x * 0.9, zc + 0.3)], 0.03, 3, robe_hi)
    for sx in (-1, 1):
        relief(f"Stole{sx}", [(sx * 0.18, zc + 0.95), (sx * 0.4, zc + 0.9), (sx * 0.5, zb), (sx * 0.28, zb)], lay(4), T, stole)
        relief(f"StoleFoil{sx}", ellipse(sx * 0.39, zb + 0.4, 0.07, 0.07, n=12), lay(5), T, gold)
    relief("SleeveR", [(0.5, zc + 0.85), (0.98, zc + 0.62), (0.78, zc - 0.12), (0.3, zc - 0.05), (0.22, zc + 0.15), (0.62, zc + 0.3)], lay(6), T, robe_hi)
    relief("SleeveL", [(-0.5, zc + 0.85), (-1.0, zc + 0.6), (-0.98, zc - 0.25), (-0.72, zc - 0.28), (-0.6, zc + 0.35)], lay(6), T, robe_hi)
    strip2("SleeveFoldR", [(0.85, zc + 0.5), (0.62, zc + 0.05)], 0.025, 7, robe)
    strip2("SleeveFoldL", [(-0.8, zc + 0.6), (-0.84, zc - 0.2)], 0.025, 7, robe)
    # ruff, chain of office and medallion
    relief("Ruff", ellipse(0, zc + 0.98, 0.36, 0.11, n=20), lay(7), T, ruff)
    chain = [(0.82 * math.cos(a), zc + 0.88 - 0.62 * math.sin(a)) for a in [math.pi * (0.08 + 0.84 * i / 14) for i in range(15)]]
    strip2("ChainOfOffice", chain, 0.03, 8, gold)
    for k, (x, z) in enumerate(chain[1:-1:2]):
        relief(f"ChainLink{k}", ellipse(x, z, 0.03, 0.03, n=8), lay(9), T, gold)
    relief("Medallion", ellipse(0, zc + 0.2, 0.11, 0.13, n=14), lay(9), T, gold)
    # head: neck, hair, face, brows, eyes, cheeks, nose, a long grey beard and moustache
    hz = zc + 1.38
    relief("Neck", [(-0.11, zc + 1.0), (0.11, zc + 1.0), (0.12, hz - 0.15), (-0.12, hz - 0.15)], lay(6), T, sk_sh)
    relief("Hair", ellipse(0, hz + 0.05, 0.29, 0.37, n=24), lay(8), T, hair)
    relief("Face", ellipse(0, hz, 0.235, 0.31, n=24), lay(9), T, sk)
    for sx in (-1, 1):
        relief(f"Socket{sx}", ellipse(sx * 0.095, hz + 0.035, 0.065, 0.035, n=12), lay(10), T, sk_sh)
        relief(f"Eye{sx}", ellipse(sx * 0.095, hz + 0.03, 0.028, 0.012, n=10), lay(11), T, eye)
        relief(f"Brow{sx}", [(sx * 0.035, hz + 0.075), (sx * 0.17, hz + 0.115), (sx * 0.18, hz + 0.1), (sx * 0.045, hz + 0.06)], lay(11), T, hair)
    relief("NoseShade", [(0.012, hz + 0.03), (0.045, hz - 0.075), (0.0, hz - 0.09), (-0.03, hz - 0.08)], lay(10), T, sk_sh)
    relief("CheekShade", [(0.08, hz - 0.02), (0.22, hz + 0.02), (0.21, hz - 0.18), (0.1, hz - 0.12)], lay(10), T, sk_sh)
    relief("Beard", mirror_half([(0, hz - 0.11), (0.12, hz - 0.09), (0.22, hz - 0.12), (0.24, hz - 0.25), (0.17, hz - 0.5), (0.07, hz - 0.7), (0, hz - 0.78)]),
           lay(12), T, beard)
    relief("Moustache", mirror_half([(0, hz - 0.1), (0.08, hz - 0.105), (0.16, hz - 0.18), (0.1, hz - 0.165), (0, hz - 0.135)]), lay(13), T, beard)
    # hands: one on a crimson book, one on a staff with a raven on top
    relief("Book", [(0.18, zc - 0.25), (0.72, zc - 0.32), (0.72, zc + 0.25), (0.18, zc + 0.32)], lay(8), T, stole)
    relief("BookClasp", [(0.42, zc - 0.05), (0.72, zc - 0.07), (0.72, zc + 0.02), (0.42, zc + 0.04)], lay(9), T, gold)
    relief("HandR", ellipse(0.3, zc + 0.05, 0.12, 0.09, n=12), lay(10), T, hand)
    sx = -0.85
    rz = zt - 0.95
    relief("Staff", [(sx - 0.025, zb + 0.02), (sx + 0.025, zb + 0.02), (sx + 0.045, rz), (sx - 0.005, rz)], lay(8), T, gold)
    relief("HandL", ellipse(sx + 0.01, zc - 0.15, 0.09, 0.11, n=12), lay(9), T, hand)
    raven = [(sx - 0.05, rz), (sx + 0.1, rz + 0.02), (sx + 0.2, rz + 0.16), (sx + 0.16, rz + 0.3), (sx + 0.08, rz + 0.34), (sx + 0.0, rz + 0.33),
             (sx - 0.12, rz + 0.36), (sx - 0.02, rz + 0.27), (sx - 0.06, rz + 0.14), (sx - 0.3, rz - 0.05), (sx - 0.12, rz - 0.02)]
    relief("Raven", raven, lay(9), T, robe)
    relief("RavenEye", ellipse(sx + 0.07, rz + 0.29, 0.014, 0.014, n=8), lay(10), T, gold)
    # render the painted layers to the canvas image and build the canvas with it
    paint = os.path.join(P.OUT_TEX, "FounderPortrait_paint.png")
    _render_paint(paint_start, paint, W, H, zc)
    box("Canvas", (W, 0.04, H), (0, 0.04, zc), paint_mat(paint, W, H), bevel=0.0, segments=1)
    # the heavy gilt frame: rails, a black slip, a bead and fillet, corner rosettes, a crest and pinnacles, a plaque
    for name, size, loc in (("RailT", (W + 2 * FW, 0.2, FW), (0, 0, zc + H / 2 + FW / 2)), ("RailB", (W + 2 * FW, 0.2, FW), (0, 0, FW / 2)),
                            ("RailL", (FW, 0.2, H), (-W / 2 - FW / 2, 0, zc)), ("RailR", (FW, 0.2, H), (W / 2 + FW / 2, 0, zc))):
        box(name, size, loc, gl, bevel=0.06, segments=3)
    hw, hh = W / 2, H / 2
    _rect("Slip", 0, -0.03, zc, hw, hh, 0.05, lq)
    ow, oh = hw + FW - 0.04, hh + FW - 0.04
    tube("Bead", [(-ow, -0.11, zc - oh), (ow, -0.11, zc - oh), (ow, -0.11, zc + oh), (-ow, -0.11, zc + oh)], 0.05, gl, closed=True, poly=True)
    _rect("Fillet", 0, -0.115, zc, hw + FW / 2, hh + FW / 2, 0.022, gl, square=False)
    for k in range(9):
        for side in (-1, 1):
            z = zc - hh + 0.25 + k * (H - 0.5) / 8
            sphere(f"Pearl{side}{k}", 0.035, (side * (hw + FW / 2), -0.13, z), gl, seg=6, rings=3)
    for sx_ in (-1, 1):
        for sz in (-1, 1):
            qf(f"Rose{sx_}{sz}", sx_ * (hw + FW / 2), -0.13, zc + sz * (hh + FW / 2), 0.15, gl)
            sphere(f"RoseBoss{sx_}{sz}", 0.06, (sx_ * (hw + FW / 2), -0.13, zc + sz * (hh + FW / 2)), gl, seg=8, rings=4)
        _spirelet(f"Pinnacle{sx_}", sx_ * (hw + FW / 2), 0.0, H + 2 * FW, 0.9, 0.26, gl, crockets=2)
    _gable("Crest", 0, 0.0, 1.05, H + 2 * FW - 0.05, H + 2 * FW + 0.75, 0.16, gl, gl, edge=0.04)
    foil("CrestFoil", 0, -0.09, H + 2 * FW + 0.26, 0.18, lq, lobes=3, thick=0.02)
    box("Plaque", (1.3, 0.04, 0.22), (0, -0.12, FW / 2), lq, bevel=0.015)
    _rect("PlaqueEdge", 0, -0.145, FW / 2, 0.63, 0.09, 0.012, gl)
    # the picture light: a brass arm and a hooded tube over the top of the canvas
    ztop = zc + H / 2
    for sx_ in (-0.5, 0.5):
        tube(f"LightArm{sx_}", [(sx_, -0.1, ztop + 0.25), (sx_, -0.35, ztop + 0.42), (sx_, -0.62, ztop + 0.32)], 0.025, M["brass"])
        box(f"LightMount{sx_}", (0.14, 0.04, 0.14), (sx_, -0.11, ztop + 0.25), M["brass"], bevel=0.01)
    cyl("LightHood", 0.11, 1.7, (0, -0.66, ztop + 0.26), M["brass"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    for sx_ in (-1, 1):
        cyl(f"LightCap{sx_}", 0.125, 0.04, (sx_ * 0.86, -0.66, ztop + 0.26), M["brass"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    set_group("Glow")
    box("LightTube", (1.6, 0.06, 0.04), (0, -0.66, ztop + 0.15), flat("Bulb", (1.0, 0.8, 0.5), 0.4), bevel=0.0, segments=1)
    set_group("Main")
    return _dims()


# ================================================================== the safe
def safe(M):
    W, D = 2.6, 2.3
    z0, z1 = 0.32, 3.95
    lq = lacquer()
    gl = gilt()
    ir = material("SafeIron", "NH_Iron", tint=(0.075, 0.072, 0.08), scale=0.45, rough_add=0.02, wear=0.5, wear_metal=True)
    vel = velvet()
    sc = material("SafeCrimson", "NH_PaintedMetal", tint=(0.11, 0.014, 0.02), scale=1.0, rough_add=0.05, wear=0.22, wear_metal=True)
    set_group("Main")
    # castors
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.25), sy * (D / 2 - 0.25)
            box(f"CastorFork{sx}{sy}", (0.08, 0.2, 0.2), (x, y, 0.22), M["brass"], bevel=0.015)
            cyl(f"Castor{sx}{sy}", 0.12, 0.08, (x, y, 0.12), M["brass"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
    # the body as a shell, so there is room inside when the door opens
    yf = -D / 2 + 0.1
    box("Base", (W + 0.1, D + 0.1, 0.16), (0, 0.05, z0 + 0.08), ir, bevel=0.03)
    box("Bottom", (W, D, 0.32), (0, 0.1, z0 + 0.16 + 0.16), ir, bevel=0.02)
    box("Top", (W, D, 0.3), (0, 0.1, z1 - 0.15), ir, bevel=0.03)
    box("Cap", (W + 0.12, D + 0.12, 0.12), (0, 0.1, z1 + 0.06), ir, bevel=0.035)
    box("Back", (W, 0.25, z1 - z0), (0, D / 2 + 0.1 - 0.125, (z0 + z1) / 2), ir, bevel=0.02)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.22, D, z1 - z0), (sx * (W / 2 - 0.11), 0.1, (z0 + z1) / 2), ir, bevel=0.03)
        # crimson side panels with gilt pinstripes and a corner fleur
        px = sx * (W / 2 + 0.005)
        box(f"SidePanel{sx}", (0.01, D - 0.6, z1 - z0 - 0.8), (px, 0.1, (z0 + z1) / 2), sc, bevel=0.0, segments=1)
        tube(f"SideStripe{sx}", [(px + sx * 0.008, 0.1 - (D - 0.6) / 2 - 0.08, z0 + 0.32), (px + sx * 0.008, 0.1 + (D - 0.6) / 2 + 0.08, z0 + 0.32),
                                 (px + sx * 0.008, 0.1 + (D - 0.6) / 2 + 0.08, z1 - 0.32), (px + sx * 0.008, 0.1 - (D - 0.6) / 2 - 0.08, z1 - 0.32)],
             0.01, gl, closed=True, square=True, poly=True)
        tube(f"SideArch{sx}", _arch_loop_x(px + sx * 0.01, 0.1, 0.5, z0 + 0.7, z1 - 1.3, z1 - 0.7), 0.014, gl, square=True, closed=True, poly=True)
        q = _mark()
        qf(f"SideSeal{sx}", 0, 0, 0, 0.18, gl)
        _xform(q, Matrix.Translation((px + sx * 0.012, 0.1, (z0 + z1) / 2 - 0.2)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        tube(f"Handle{sx}", [(sx * (W / 2 + 0.02), -0.3, z1 - 0.55), (sx * (W / 2 + 0.16), -0.25, z1 - 0.55), (sx * (W / 2 + 0.16), 0.45, z1 - 0.55),
                             (sx * (W / 2 + 0.02), 0.5, z1 - 0.55)], 0.03, M["brass"], poly=True)
    # front frame round the door, with gilt bead
    tube("FrameBead", [(-W / 2 + 0.1, yf - 0.03, z0 + 0.5), (W / 2 - 0.1, yf - 0.03, z0 + 0.5), (W / 2 - 0.1, yf - 0.03, z1 - 0.32),
                       (-W / 2 + 0.1, yf - 0.03, z1 - 0.32)], 0.018, gl, closed=True, poly=True)
    for z in (z0 + 0.9, z1 - 0.8):
        cyl(f"Knuckle{z:.1f}", 0.07, 0.4, (-W / 2 + 0.06, yf - 0.16, z), ir, verts=12, bevel=0.01)
        cyl(f"KnuckleCap{z:.1f}", 0.08, 0.04, (-W / 2 + 0.06, yf - 0.16, z + 0.22), M["brass"], verts=12, bevel=0.005)
    # inside: crimson velvet lining, a shelf, gold bars, coin stacks, sealed papers, a jewel box, a ledger
    ix0, ix1 = -W / 2 + 0.22, W / 2 - 0.22
    iz0, iz1 = z0 + 0.48, z1 - 0.3
    yb = D / 2 + 0.1 - 0.25
    box("LiningBack", (ix1 - ix0, 0.02, iz1 - iz0), (0, yb - 0.01, (iz0 + iz1) / 2), vel, bevel=0.0, segments=1)
    for sx in (-1, 1):
        box(f"LiningSide{sx}", (0.02, yb - yf, iz1 - iz0), (sx * (ix1 - 0.01), (yb + yf) / 2, (iz0 + iz1) / 2), vel, bevel=0.0, segments=1)
    box("LiningFloor", (ix1 - ix0, yb - yf, 0.02), (0, (yb + yf) / 2, iz0 + 0.01), vel, bevel=0.0, segments=1)
    zs = (iz0 + iz1) / 2 + 0.1
    box("Shelf", (ix1 - ix0, yb - yf - 0.1, 0.06), (0, (yb + yf) / 2 + 0.05, zs), ir, bevel=0.01)
    for k in range(5):
        x = -0.75 + (k % 3) * 0.45 + (0.22 if k >= 3 else 0)
        z = zs + 0.03 + (0.13 if k >= 3 else 0)
        prism(f"GoldBar{k}", [(-0.18, 0), (0.18, 0), (0.14, 0.13), (-0.14, 0.13)], 0.0, 0.3, gl, plane="XZ")
        _xform(len(P.PARTS) - 1, Matrix.Translation((x, 0.25, z)))
    for k in range(4):
        h = 0.12 + 0.07 * k
        cyl(f"Coins{k}", 0.1, h, (0.45 + (k % 2) * 0.24, -0.1 + (k // 2) * 0.24, zs + 0.03 + h / 2), gl, verts=16, bevel=0.01)
    for k in range(3):
        box(f"Deed{k}", (0.8, 0.5, 0.06), (-0.4, 0.15, iz0 + 0.05 + k * 0.065), M["paper"], bevel=0.01, rot=(0, 0, math.radians((-6, 4, -2)[k])))
    box("DeedRibbon", (0.06, 0.52, 0.2), (-0.4, 0.15, iz0 + 0.12), M["crimson"], bevel=0.005)
    sphere("DeedSeal", 0.06, (-0.4, -0.12, iz0 + 0.2), M["crimson"], seg=8, rings=4, scale=(1, 0.4, 1))
    box("JewelBox", (0.55, 0.42, 0.32), (0.5, 0.25, iz0 + 0.18), lq, bevel=0.03)
    tube("JewelBoxBand", [(0.22, 0.04, iz0 + 0.33), (0.78, 0.04, iz0 + 0.33)], 0.012, gl, poly=True)
    qf("JewelSeal", 0.5, 0.035, iz0 + 0.2, 0.06, gl)
    # the door: thick iron slab, double gilt pinstripes, a pointed arch, a crest, dial, wheel, keyhole, locking bolts
    hx = -W / 2 + 0.06                      # hinge line (left front edge)
    yd = yf - 0.16
    set_group("Door0", hinge=(hx, yd, 0.0), swing=-1)
    dw, dh = W - 0.18, z1 - z0 - 0.62
    dzc = z0 + 0.32 + dh / 2 + 0.03
    dxc = hx + 0.04 + dw / 2
    box("Door", (dw, 0.3, dh), (dxc, yd, dzc), ir, bevel=0.035)
    yo = yd - 0.155
    _rect("Stripe1", dxc, yo, dzc, dw / 2 - 0.14, dh / 2 - 0.14, 0.009, gl)
    _rect("Stripe2", dxc, yo, dzc, dw / 2 - 0.2, dh / 2 - 0.2, 0.006, gl)
    tube("StripeArch", _arch_loop(dxc, yo, dw / 2 - 0.34, dzc - dh / 2 + 0.34, dzc + dh / 2 - 0.75, dzc + dh / 2 - 0.3), 0.008, gl, square=True,
         closed=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"CornerFoil{sx}{sz}", dxc + sx * (dw / 2 - 0.26), yo, dzc + sz * (dh / 2 - 0.26), 0.06, gl, lobes=4, thick=0.007)
    qf("DoorCrest", dxc, yo - 0.005, dzc + dh / 2 - 0.55, 0.13, gl)
    cyl("CrestDisc", 0.12, 0.01, (dxc, yo, dzc + dh / 2 - 0.55), M["crimson"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0)
    # combination dial
    dz = dzc + 0.45
    cyl("DialRing", 0.3, 0.05, (dxc, yo - 0.02, dz), M["brass"], rot=(math.pi / 2, 0, 0), verts=32, bevel=0.012)
    cyl("Dial", 0.24, 0.07, (dxc, yo - 0.05, dz), lq, rot=(math.pi / 2, 0, 0), verts=32, bevel=0.012)
    for k in range(20):
        a = k / 20 * 2 * math.pi
        box(f"DialTick{k}", (0.012, 0.01, 0.05 if k % 5 == 0 else 0.03), (dxc + math.sin(a) * 0.19, yo - 0.088, dz + math.cos(a) * 0.19), gl,
            bevel=0.0, segments=1, rot=(0, -a, 0))
    cyl("DialKnob", 0.08, 0.1, (dxc, yo - 0.12, dz), M["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.015)
    box("DialMark", (0.03, 0.02, 0.05), (dxc, yo - 0.04, dz + 0.33), gl, bevel=0.005)
    # the wheel handle
    wz = dzc - 0.45
    cyl("WheelHub", 0.09, 0.18, (dxc, yo - 0.09, wz), M["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.015)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        end = (dxc + math.cos(a) * 0.32, yo - 0.16, wz + math.sin(a) * 0.32)
        tube(f"WheelSpoke{k}", [(dxc, yo - 0.16, wz), end], 0.022, M["brass"], poly=True)
        sphere(f"WheelKnob{k}", 0.05, end, M["brass"], seg=8, rings=4)
    # the keyhole escutcheon
    _gable("Escutcheon", dxc + 0.62, yo - 0.01, 0.1, dzc - 0.08, dzc + 0.12, 0.02, M["brass"])
    box("Keyhole", (0.03, 0.01, 0.1), (dxc + 0.62, yo - 0.025, dzc - 0.02), M["glass"], bevel=0.0, segments=1)
    # locking bolts on the door's free edge
    for k in range(3):
        cyl(f"Bolt{k}", 0.06, 0.16, (dxc + dw / 2 - 0.12, yd + 0.2, dzc - 0.8 + k * 0.8), M["brasssteel"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.01)
    for z in (z0 + 0.9, z1 - 0.8):
        box(f"HingeLeaf{z:.1f}", (0.35, 0.03, 0.3), (hx + 0.2, yo + 0.005, z), ir, bevel=0.01)
    set_group("Main")
    return _dims()


# ================================================================== the cabinet of confiscated things
def curiosity_cabinet(M):
    W, D = 3.0, 1.4
    lq, gl = lacquer(), gilt()
    vel = velvet()
    bone = flat("Bone", (0.74, 0.69, 0.58), 0.55, dirt=0.8)
    dark = flat("Hollow", (0.015, 0.012, 0.012), 0.9)
    burlap = material("Burlap", "NH_Leather", tint=(0.42, 0.33, 0.22), scale=3.0, normal=0.9, wear=0.2)
    rubber = flat("Rubber", (0.36, 0.25, 0.14), 0.7)
    zt = 6.1                                          # carcass top
    yf = -D / 2
    set_group("Main")
    # carcass: plinth, base cupboard with a drawer, sides, back with crimson velvet, cornice, pediment and pinnacles
    box("Plinth", (W + 0.16, D + 0.12, 0.25), (0, 0, 0.125), lq, bevel=0.03)
    box("Base", (W, D, 0.8), (0, 0, 0.25 + 0.4), lq, bevel=0.025)
    box("BaseDrawer", (W - 0.3, 0.05, 0.5), (0, yf - 0.02, 0.65), lq, bevel=0.02)
    _rect("BaseDrawerPanel", 0, yf - 0.05, 0.65, W / 2 - 0.3, 0.17, 0.012, gl)
    _bail("BasePull", 0, yf - 0.05, 0.67, gl)
    box("Back", (W, 0.1, zt - 1.05), (0, D / 2 - 0.05, 1.05 + (zt - 1.05) / 2), lq, bevel=0.02)
    box("Velvet", (W - 0.3, 0.02, zt - 1.25), (0, D / 2 - 0.11, 1.05 + (zt - 1.05) / 2), vel, bevel=0.0, segments=1)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.15, D, zt - 1.05), (sx * (W / 2 - 0.075), 0, 1.05 + (zt - 1.05) / 2), lq, bevel=0.02)
        tube(f"SideArch{sx}", _arch_loop_x(sx * (W / 2 + 0.005), 0, 0.42, 1.5, 4.6, 5.4), 0.022, gl, square=True, closed=True, poly=True)
        _spirelet(f"Pinnacle{sx}", sx * (W / 2 - 0.08), yf + 0.12, zt + 0.12, 1.1, 0.24, lq, crockets=2)
        sphere(f"PinnacleGilt{sx}", 0.05, (sx * (W / 2 - 0.08), yf + 0.12, zt + 1.28), gl, seg=8, rings=4)
    box("Cornice", (W + 0.2, D + 0.14, 0.16), (0, -0.02, zt + 0.04), lq, bevel=0.04)
    tube("CorniceBead", [(-W / 2 - 0.1, yf - 0.1, zt - 0.03), (W / 2 + 0.1, yf - 0.1, zt - 0.03)], 0.02, gl, poly=True)
    _gable("Pediment", 0, yf + 0.25, W / 2 - 0.2, zt + 0.12, zt + 1.05, 0.14, lq, gl, edge=0.03)
    foil("PedimentFoil", 0, yf + 0.17, zt + 0.45, 0.2, gl, lobes=3, thick=0.016)
    sphere("PedimentFinial", 0.07, (0, yf + 0.25, zt + 1.12), gl, seg=8, rings=4)
    # shelves with gilt edges
    shelf_z = (1.05, 2.3, 3.55, 4.8)
    for k, z in enumerate(shelf_z[1:]):
        box(f"Shelf{k}", (W - 0.3, D - 0.2, 0.06), (0, 0.0, z), lq, bevel=0.01)
        tube(f"ShelfEdge{k}", [(-(W - 0.3) / 2, yf + 0.1, z + 0.02), ((W - 0.3) / 2, yf + 0.1, z + 0.02)], 0.012, gl, poly=True)
    # --- shelf 1: the cursed doll stuck with pins, playing cards, a slingshot
    z = shelf_z[0]
    dx = -0.75
    sphere("DollBody", 0.2, (dx, 0.05, z + 0.25), burlap, seg=10, rings=6, scale=(0.85, 0.7, 1.2))
    lathe("DollDress", [(0, z + 0.04), (0.24, z + 0.04), (0.2, z + 0.12), (0.14, z + 0.38), (0, z + 0.38)], M["crimson"], seg=14, loc=(dx, 0.05, 0))
    sphere("DollHead", 0.16, (dx, 0.03, z + 0.6), burlap, seg=10, rings=6)
    for sx in (-1, 1):
        cyl(f"DollButton{sx}", 0.035, 0.02, (dx + sx * 0.06, -0.13, z + 0.63), M["glass"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0)
        tube(f"DollArm{sx}", [(dx + sx * 0.15, 0.03, z + 0.36), (dx + sx * 0.3, -0.04, z + 0.2)], 0.045, burlap)
        tube(f"DollLeg{sx}", [(dx + sx * 0.08, 0.0, z + 0.08), (dx + sx * 0.1, -0.25, z + 0.05)], 0.05, burlap)
    for k in range(3):
        box(f"DollStitch{k}", (0.07, 0.01, 0.012), (dx - 0.05 + k * 0.05, -0.155, z + 0.54), dark, bevel=0.0, segments=1, rot=(0, 0.6 if k % 2 else -0.6, 0))
    for k, (px, pz, ay) in enumerate(((dx - 0.06, z + 0.32, 0.4), (dx + 0.08, z + 0.24, -0.3), (dx + 0.02, z + 0.68, 0.2))):
        tube(f"Pin{k}", [(px, -0.08, pz), (px + math.sin(ay) * 0.18, -0.26, pz + 0.05)], 0.006, M["brasssteel"], poly=True)
        sphere(f"PinHead{k}", 0.025, (px + math.sin(ay) * 0.18, -0.26, pz + 0.05), M["crimson"], seg=6, rings=3)
    for k in range(5):
        a = math.radians(-30 + k * 15)
        box(f"Card{k}", (0.22, 0.32, 0.006), (0.05 + math.sin(a) * 0.12, -0.18 + math.cos(a) * 0.05, z + 0.01 + k * 0.004),
            M["paper"] if k % 2 else M["crimson"], bevel=0.0, segments=1, rot=(0, 0, a))
        box(f"CardPip{k}", (0.04, 0.04, 0.003), (0.05 + math.sin(a) * 0.12, -0.18 + math.cos(a) * 0.05, z + 0.016 + k * 0.004),
            M["crimson"] if k % 2 else M["paper"], bevel=0.0, segments=1, rot=(0, 0, a + 0.785))
    sxx = 0.85
    tube("SlingHandle", [(sxx, 0.1, z + 0.02), (sxx, 0.1, z + 0.35)], 0.04, M["oakdark"], poly=True)
    for sx in (-1, 1):
        tube(f"SlingFork{sx}", [(sxx, 0.1, z + 0.35), (sxx + sx * 0.12, 0.1, z + 0.5), (sxx + sx * 0.15, 0.1, z + 0.68)], 0.035, M["oakdark"])
        tube(f"SlingBand{sx}", [(sxx + sx * 0.15, 0.1, z + 0.66), (sxx + sx * 0.06, -0.02, z + 0.55), (sxx, -0.08, z + 0.5)], 0.012, rubber)
    box("SlingPouch", (0.1, 0.03, 0.08), (sxx, -0.09, z + 0.5), M["leatherdark"], bevel=0.01)
    box("SlingTag", (0.18, 0.01, 0.1), (sxx + 0.28, -0.05, z + 0.12), M["paper"], bevel=0.0, segments=1, rot=(0, 0.3, 0))
    tube("SlingString", [(sxx, 0.08, z + 0.15), (sxx + 0.2, -0.04, z + 0.15)], 0.004, M["paper"], poly=True)
    # --- shelf 2: potion bottles and a skull
    z = shelf_z[1] + 0.03
    for k, (bx, col, h) in enumerate(((-0.95, (0.04, 0.22, 0.08), 0.55), (-0.6, (0.2, 0.04, 0.24), 0.42), (-0.32, (0.3, 0.13, 0.02), 0.35))):
        gm = flat(f"Potion{k}", col, 0.08)
        lathe(f"Bottle{k}", [(0, z), (0.12, z), (0.13, z + h * 0.55), (0.06, z + h * 0.72), (0.04, z + h), (0, z + h)], gm, seg=16, loc=(bx, 0.1, 0))
        cyl(f"Cork{k}", 0.04, 0.08, (bx, 0.1, z + h + 0.03), M["paper"], verts=10, bevel=0.01)
        box(f"Label{k}", (0.13, 0.01, 0.1), (bx, -0.03, z + h * 0.32), M["paper"], bevel=0.0, segments=1)
    _skull("Skull", Matrix.Translation((0.55, 0.05, z)) @ Matrix.Rotation(math.radians(-15), 4, "Z") @ Matrix.Scale(1.3, 4), bone, dark)
    # --- shelf 3: a dagger on a little stand, a jar with an eye
    z = shelf_z[2] + 0.03
    for sx in (-1, 1):
        prism(f"DaggerStand{sx}", [(-0.06, 0), (0.06, 0), (0.04, 0.16), (-0.04, 0.16)], sx * 0.4 - 0.3, 0.2, lq, plane="YZ")
        _xform(len(P.PARTS) - 1, Matrix.Translation((0, 0.05, z)))
    relief("Blade", [(0.0, 0.035), (0.72, 0.008), (0.82, 0.0), (0.72, -0.008), (0.0, -0.035)], 0.0, 0.015, steel(), plane="XY")
    _xform(len(P.PARTS) - 1, Matrix.Translation((-0.35, 0.05, z + 0.17)))
    box("Crossguard", (0.04, 0.3, 0.04), (-0.35, 0.05, z + 0.18), gl, bevel=0.01)
    tube("Grip", [(-0.37, 0.05, z + 0.18), (-0.62, 0.05, z + 0.18)], 0.028, M["leatherdark"], poly=True)
    sphere("Pommel", 0.045, (-0.65, 0.05, z + 0.18), gl, seg=8, rings=5)
    lathe("Jar", [(0, z), (0.16, z), (0.18, z + 0.05), (0.18, z + 0.38), (0.12, z + 0.42), (0, z + 0.42)], flat("JarGlass", (0.2, 0.24, 0.16), 0.1),
          seg=18, loc=(0.75, 0.1, 0))
    sphere("Eyeball", 0.09, (0.75, 0.0, z + 0.2), bone, seg=10, rings=6)
    sphere("Iris", 0.04, (0.75, -0.075, z + 0.21), flat("Iris", (0.25, 0.03, 0.03), 0.3), seg=8, rings=4, scale=(1, 0.5, 1))
    cyl("JarLid", 0.15, 0.05, (0.75, 0.1, z + 0.44), M["brass"], verts=18, bevel=0.01)
    # --- shelf 4: a chained black book with a crimson ribbon, a crystal ball on a brass stand
    z = shelf_z[3] + 0.03
    q = _mark()
    _book("Grimoire", 0.7, 0.5, 0.18, flat("GrimoireHide", (0.03, 0.025, 0.03), 0.6), M, corners=True, clasp=True, ribbon=M["crimson"])
    _xform(q, Matrix.Translation((-0.55, 0.0, z)) @ Matrix.Rotation(math.radians(12), 4, "Z"))
    for k in range(6):
        hoop(f"ChainLink{k}", (-0.95 + k * 0.08, -0.15, z + 0.12 - (k % 2) * 0.03), 0.04, "Y" if k % 2 else "Z", M["iron"], thick=0.01)
    lathe("BallStand", [(0, z), (0.14, z), (0.12, z + 0.06), (0.06, z + 0.12), (0.1, z + 0.16), (0, z + 0.16)], gl, seg=16, loc=(0.6, 0.1, 0))
    sphere("CrystalBall", 0.19, (0.6, 0.1, z + 0.33), flat("Crystal", (0.32, 0.36, 0.44), 0.05), seg=16, rings=10)
    # the glazed door: a lacquer frame with gilt tracery; its pane (Glass) swings with it on the same hinge
    hx, yd = -W / 2 + 0.15, yf - 0.05
    dz0, dz1 = 1.05, zt - 0.02
    dw = W - 0.3
    set_group("Door0", hinge=(hx, yd, 0.0), swing=-1)
    for name, size, loc in (("DoorStileL", (0.14, 0.09, dz1 - dz0), (hx + 0.07, yd, (dz0 + dz1) / 2)),
                            ("DoorStileR", (0.14, 0.09, dz1 - dz0), (hx + dw - 0.07, yd, (dz0 + dz1) / 2)),
                            ("DoorRailB", (dw, 0.09, 0.16), (hx + dw / 2, yd, dz0 + 0.08)), ("DoorRailT", (dw, 0.09, 0.16), (hx + dw / 2, yd, dz1 - 0.08))):
        box(name, size, loc, lq, bevel=0.015)
    cx = hx + dw / 2
    spand = [(cx - dw / 2 + 0.14, dz1 - 0.16), (cx + dw / 2 - 0.14, dz1 - 0.16)] + list(reversed(_gothic_pts(cx - dw / 2 + 0.14, cx + dw / 2 - 0.14,
                                                                                                         dz1 - 0.75, dz1 - 0.2, 8)))
    relief("DoorHead", spand, yd, 0.08, lq)
    tube("DoorArch", [(x, yd - 0.05, z) for x, z in _gothic_pts(cx - dw / 2 + 0.16, cx + dw / 2 - 0.16, dz1 - 0.75, dz1 - 0.22, 8)], 0.018, gl,
         square=True, poly=True)
    tube("DoorMullion", [(cx, yd - 0.03, dz0 + 0.16), (cx, yd - 0.03, dz1 - 0.22)], 0.025, lq, square=True, poly=True)
    tube("DoorMullionGilt", [(cx, yd - 0.058, dz0 + 0.16), (cx, yd - 0.058, dz1 - 0.24)], 0.008, gl, poly=True)
    for z in shelf_z[1:]:
        tube(f"Transom{z}", [(hx + 0.14, yd - 0.03, z + 0.1), (hx + dw - 0.14, yd - 0.03, z + 0.1)], 0.018, lq, square=True, poly=True)
    for sx in (-1, 1):
        tube(f"Lancet{sx}", _arch_loop(cx + sx * dw / 4, yd - 0.05, dw / 4 - 0.1, dz1 - 1.4, dz1 - 0.95, dz1 - 0.6), 0.012, gl, square=True,
             closed=True, poly=True)
    foil("DoorFoil", cx, yd - 0.05, dz1 - 0.42, 0.11, gl, lobes=4, thick=0.01)
    box("DoorKeyPlate", (0.08, 0.02, 0.22), (hx + dw - 0.07, yd - 0.055, 3.3), gl, bevel=0.008)
    sphere("DoorKnob", 0.045, (hx + dw - 0.07, yd - 0.1, 3.15), gl, seg=8, rings=4)
    set_group("Glass", hinge=(hx, yd, 0.0), swing=-1)
    box("Pane", (dw - 0.24, 0.02, dz1 - dz0 - 0.3), (cx, yd + 0.01, (dz0 + dz1) / 2), M["glassclear"], bevel=0.0, segments=1)
    set_group("Main")
    return _dims()


# ================================================================== the office rug
def rug_mat():
    """A gothic rug on object space (x across 12, y across 8): an ink border with a gilt line and a crimson band of
    lozenges, a deep crimson field with a fine ink lattice, and a quatrefoil medallion in ink and gold; woollen pile."""
    m = bpy.data.materials.new("Rug")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])

    def mth(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, b):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v, 1)
            else:
                L(v, sock)
        return n.outputs[2]

    INK, CRIM, CRIMD, GOLD = (0.016, 0.014, 0.024), (0.2, 0.022, 0.03), (0.09, 0.012, 0.018), (0.42, 0.28, 0.09)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    ux, uy = mth("ABSOLUTE", x), mth("ABSOLUTE", y)
    edge = mth("MINIMUM", mth("SUBTRACT", 6.0, ux), mth("SUBTRACT", 4.0, uy))        # distance in from the nearest edge
    # field: deep crimson with an ink diagonal lattice and tiny gold dots at the crossings
    lat_a = mth("ABSOLUTE", mth("SUBTRACT", mth("FRACT", mth("MULTIPLY", mth("ADD", x, y), 1.0)), 0.5))
    lat_b = mth("ABSOLUTE", mth("SUBTRACT", mth("FRACT", mth("MULTIPLY", mth("SUBTRACT", x, y), 1.0)), 0.5))
    lattice = mth("MAXIMUM", mth("GREATER_THAN", lat_a, 0.47), mth("GREATER_THAN", lat_b, 0.47))
    dots = mth("MULTIPLY", mth("GREATER_THAN", lat_a, 0.42), mth("GREATER_THAN", lat_b, 0.42))
    col = mix(lattice, CRIMD, INK)
    col = mix(dots, col, GOLD)
    # the medallion: a quatrefoil (r < 1.55 + 0.45 cos 4a) in ink with a gold rim and a crimson heart
    r = mth("SQRT", mth("ADD", mth("MULTIPLY", x, x), mth("MULTIPLY", y, y)))
    ang = mth("ARCTAN2", y, x)
    foil_r = mth("MULTIPLY_ADD", mth("COSINE", mth("MULTIPLY", ang, 4.0)), 0.45, 1.55)
    d = mth("SUBTRACT", foil_r, r)
    col = mix(mth("GREATER_THAN", d, 0.0), col, GOLD)
    col = mix(mth("GREATER_THAN", d, 0.09), col, INK)
    col = mix(mth("LESS_THAN", r, 0.75), col, CRIM)
    col = mix(mth("MULTIPLY", mth("GREATER_THAN", r, 0.62), mth("LESS_THAN", r, 0.68)), col, GOLD)
    # four small foils toward the corners of the field
    for sx in (-1, 1):
        for sy in (-1, 1):
            dx_, dy_ = mth("SUBTRACT", x, sx * 3.3), mth("SUBTRACT", y, sy * 1.85)
            rr = mth("SQRT", mth("ADD", mth("MULTIPLY", dx_, dx_), mth("MULTIPLY", dy_, dy_)))
            aa = mth("ARCTAN2", dy_, dx_)
            fr = mth("MULTIPLY_ADD", mth("COSINE", mth("MULTIPLY", aa, 4.0)), 0.14, 0.42)
            dd = mth("SUBTRACT", fr, rr)
            col = mix(mth("GREATER_THAN", dd, 0.0), col, GOLD)
            col = mix(mth("GREATER_THAN", dd, 0.06), col, INK)
    # the border: ink outer band, gold line, crimson band with ink lozenges, gold line
    along = mth("ADD", mth("MULTIPLY", mth("GREATER_THAN", mth("SUBTRACT", 6.0, ux), mth("SUBTRACT", 4.0, uy)), y),
                mth("MULTIPLY", mth("LESS_THAN", mth("SUBTRACT", 6.0, ux), mth("SUBTRACT", 4.0, uy)), x))
    loz = mth("ADD", mth("ABSOLUTE", mth("SUBTRACT", mth("FRACT", mth("MULTIPLY", along, 1.6)), 0.5)),
              mth("ABSOLUTE", mth("MULTIPLY", mth("SUBTRACT", edge, 0.8), 1.25)))
    bandc = mix(mth("LESS_THAN", loz, 0.32), CRIM, INK)
    bandc = mix(mth("LESS_THAN", loz, 0.12), bandc, GOLD)
    col = mix(mth("LESS_THAN", edge, 1.18), col, GOLD)
    col = mix(mth("LESS_THAN", edge, 1.12), col, bandc)
    col = mix(mth("LESS_THAN", edge, 0.48), col, GOLD)
    col = mix(mth("LESS_THAN", edge, 0.42), col, INK)
    # wool: a fine noise in colour and a pile bump
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 120.0
    nz.inputs["Detail"].default_value = 3.0
    L(tc.outputs["Object"], nz.inputs["Vector"])
    shade = mth("MULTIPLY_ADD", nz.outputs["Fac"], 0.35, 0.82)
    cm = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        L(shade, cm.inputs[i])
    mm = nt.nodes.new("ShaderNodeMix")
    mm.data_type = "RGBA"
    mm.blend_type = "MULTIPLY"
    mm.inputs[0].default_value = 1.0
    L(col, mm.inputs[6])
    L(cm.outputs["Color"], mm.inputs[7])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    L(nz.outputs["Fac"], bump.inputs["Height"])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mm.outputs[2], 0.95, mv.outputs[0], bump.outputs["Normal"], 0.0, False, 0.25)
    return m


def office_rug(M):
    set_group("Main")
    box("Rug", (12.0, 8.0, 0.05), (0, 0, 0.025), rug_mat(), bevel=0.015, segments=1)
    fringe = flat("Fringe", (0.55, 0.5, 0.4), 0.9)
    for sx in (-1, 1):
        for k in range(40):
            y = -3.9 + k * 7.8 / 39
            box(f"Tassel{sx}{k}", (0.32, 0.05, 0.02), (sx * 6.15, y, 0.012), fringe, bevel=0.0, segments=1, rot=(0, 0, math.radians((k * 37) % 9 - 4)))
    return _dims()


# ================================================================== desk lamp
def desk_lamp(M):
    gl = gilt()
    set_group("Main")
    lathe("Base", [(0, 0), (0.38, 0), (0.4, 0.04), (0.36, 0.08), (0.28, 0.12), (0.26, 0.18), (0.16, 0.22), (0.1, 0.3), (0, 0.3)], M["brass"], seg=32)
    hoop("BaseBead", (0, 0, 0.08), 0.37, "Z", gl, thick=0.015)
    lathe("Column", [(0, 0.3), (0.06, 0.3), (0.05, 0.5), (0.09, 0.58), (0.05, 0.66), (0.04, 1.1), (0.08, 1.18), (0.05, 1.26), (0.04, 1.42), (0, 1.42)],
          M["brass"], seg=16, flute=None)
    # the crimson glass bell shade with brass bands and a finial
    # crimson cased glass: the outer casing (satin, darker at the crown) and a lit inner face, gilt ribs and bands
    lathe("Shade", [(0.58, 1.35), (0.56, 1.4), (0.46, 1.6), (0.3, 1.8), (0.14, 1.93), (0.08, 1.96)], cased_glass(1.96, 1.38), seg=32)
    lathe("ShadeInner", [(0.065, 1.925), (0.12, 1.88), (0.27, 1.76), (0.43, 1.58), (0.53, 1.4), (0.555, 1.355)],
          flat("ShadeLit", (0.75, 0.2, 0.08), 0.5, dirt=0.2), seg=32)
    hoop("ShadeRim", (0, 0, 1.36), 0.575, "Z", gl, thick=0.022)
    hoop("ShadeBand", (0, 0, 1.68), 0.39, "Z", gl, thick=0.012)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        tube(f"ShadeRib{k}", [(math.cos(a) * 0.575, math.sin(a) * 0.575, 1.37), (math.cos(a) * 0.45, math.sin(a) * 0.45, 1.6),
                              (math.cos(a) * 0.15, math.sin(a) * 0.15, 1.93)], 0.011, gl)
    lathe("Finial", [(0, 1.94), (0.07, 1.94), (0.06, 2.0), (0.03, 2.06), (0.04, 2.1), (0, 2.15)], gl, seg=12)
    tube("Arm", [(0, 0, 1.42), (0, 0, 1.5)], 0.025, M["brass"], poly=True)
    lathe("Socket", [(0, 1.42), (0.06, 1.42), (0.07, 1.5), (0.05, 1.52), (0, 1.52)], M["brass"], seg=14)
    tube("PullChain", [(0.12, -0.05, 1.5), (0.13, -0.06, 1.2)], 0.006, M["brass"], poly=True)
    sphere("PullBead", 0.025, (0.13, -0.06, 1.18), gl, seg=8, rings=4)
    set_group("Glow")
    sphere("Bulb", 0.12, (0, 0, 1.58), flat("Bulb", (1.0, 0.8, 0.5), 0.4), seg=12, rings=6, scale=(1, 1, 1.2))
    set_group("Main")
    return _dims()


# ================================================================== the founder's bust
def founder_bust(M):
    bm, wm = black_marble(), white_marble()
    gl = gilt()
    set_group("Main")
    box("Plinth", (1.5, 1.5, 0.35), (0, 0, 0.175), bm, bevel=0.04)
    box("Plinth2", (1.3, 1.3, 0.15), (0, 0, 0.425), bm, bevel=0.03)
    lathe("Shaft", [(0, 0.5), (0.55, 0.5), (0.55, 0.62), (0.47, 0.7), (0.45, 3.15), (0.52, 3.25), (0.52, 3.32), (0, 3.32)], bm, seg=48, flute=(16, 0.06))
    hoop("BandLow", (0, 0, 0.74), 0.48, "Z", gl, thick=0.025)
    hoop("BandHigh", (0, 0, 3.12), 0.47, "Z", gl, thick=0.025)
    box("Capital", (1.25, 1.25, 0.16), (0, 0, 3.4), bm, bevel=0.035)
    tube("CapitalBead", [(-0.63, -0.63, 3.4), (0.63, -0.63, 3.4), (0.63, 0.63, 3.4), (-0.63, 0.63, 3.4)], 0.018, gl, closed=True, poly=True)
    box("Plate", (0.55, 0.02, 0.14), (0, -0.465, 2.6), gl, bevel=0.008)
    # the bust in white marble: socle, robed shoulders, neck, head with a beard
    z0 = 3.48
    lathe("Socle", [(0, z0), (0.36, z0), (0.36, z0 + 0.06), (0.26, z0 + 0.12), (0.2, z0 + 0.22), (0.24, z0 + 0.3), (0, z0 + 0.3)], wm, seg=32)
    sphere("Chest", 0.5, (0, 0.02, z0 + 0.72), wm, seg=24, rings=12, scale=(1.55, 0.78, 0.95))
    box("ChestCut", (1.52, 0.7, 0.3), (0, 0.02, z0 + 0.38), wm, bevel=0.12, segments=3)
    hoop("Collar", (0, -0.02, z0 + 1.08), 0.24, "Z", wm, thick=0.07)
    sphere("Clasp", 0.07, (-0.2, -0.36, z0 + 0.92), wm, seg=10, rings=5, scale=(1, 0.5, 1))
    head0 = _mark()
    cyl("Neck", 0.17, 0.32, (0, 0.0, z0 + 1.2), wm, verts=20, bevel=0.03)
    hz = z0 + 1.6
    sphere("Head", 0.3, (0, 0.02, hz), wm, seg=24, rings=14, scale=(0.82, 0.95, 1.08))
    sphere("Jaw", 0.2, (0, -0.08, hz - 0.2), wm, seg=16, rings=8, scale=(1.0, 0.9, 0.8))
    sphere("Brow", 0.15, (0, -0.17, hz + 0.07), wm, seg=14, rings=6, scale=(1.15, 0.42, 0.24))
    cone("Nose", 0.055, 0.022, 0.17, (0, -0.31, hz - 0.04), wm, verts=8, rot=(math.radians(110), 0, 0))
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.04, (sx * 0.09, -0.245, hz + 0.02), wm, seg=8, rings=5, scale=(1, 0.6, 0.7))
        sphere(f"Ear{sx}", 0.06, (sx * 0.25, 0.03, hz), wm, seg=8, rings=4, scale=(0.4, 0.8, 1.3))
        tube(f"Moustache{sx}", [(0, -0.3, hz - 0.13), (sx * 0.08, -0.29, hz - 0.15), (sx * 0.14, -0.25, hz - 0.2)], 0.025, wm)
    sphere("Beard", 0.2, (0, -0.16, hz - 0.33), wm, seg=16, rings=8, scale=(0.95, 0.7, 1.25))
    for k in range(5):
        x = -0.1 + k * 0.05
        tube(f"BeardLock{k}", [(x, -0.25, hz - 0.25), (x * 0.9, -0.28, hz - 0.36), (x * 0.6, -0.24, hz - 0.5)], 0.03, wm)
    sphere("Hair", 0.3, (0, 0.1, hz + 0.05), wm, seg=18, rings=10, scale=(0.86, 0.9, 1.0))
    nb = z0 + 1.06    # the head and neck at a more heroic scale, from the collar up
    _xform(head0, Matrix.Translation((0, 0, nb)) @ Matrix.Scale(1.3, 4) @ Matrix.Translation((0, 0, -nb)))
    return _dims()


# ================================================================== the school crest
def school_crest(M):
    gl = gilt()
    lq = lacquer()
    stl = steel()
    ink = flat("CrestInk", (0.01, 0.01, 0.022), 0.4)
    red = material("CrestCrimson", "NH_PaintedMetal", tint=(0.12, 0.014, 0.02), scale=1.0, rough_add=0.05, wear=0.18, wear_metal=True)
    bone = flat("Scroll", (0.72, 0.66, 0.54), 0.7, dirt=0.8)
    set_group("Main")
    # crossed swords behind the shield
    for sx in (-1, 1):
        s = _mark()
        relief(f"Blade{sx}", [(-0.07, 0.0), (0.07, 0.0), (0.06, 3.3), (0.0, 3.6), (-0.06, 3.3)], 0.0, 0.03, stl)
        tube(f"Fuller{sx}", [(0, -0.018, 0.1), (0, -0.018, 3.0)], 0.012, flat("Fuller", (0.3, 0.31, 0.33), 0.25, metal=1.0), poly=True)
        box(f"Guard{sx}", (0.7, 0.08, 0.08), (0, 0, -0.04), gl, bevel=0.02)
        for gx in (-1, 1):
            sphere(f"GuardEnd{sx}{gx}", 0.06, (gx * 0.37, 0, -0.04), gl, seg=8, rings=4)
        tube(f"Grip{sx}", [(0, 0, -0.08), (0, 0, -0.55)], 0.045, M["leatherdark"], poly=True)
        for k in range(4):
            hoop(f"GripWire{sx}{k}", (0, 0, -0.15 - k * 0.11), 0.047, "Z", gl, thick=0.008)
        sphere(f"Pommel{sx}", 0.08, (0, 0, -0.62), gl, seg=10, rings=5)
        _xform(s, Matrix.Translation((-sx * 1.25, 0.12, 3.7)) @ Matrix.Rotation(math.pi, 4, "Y") @ Matrix.Rotation(-sx * math.radians(38), 4, "Y"))
    # the shield: a lacquer backing, a quartered field (crimson and ink), gilt cross and border, four gilt charges
    sh = mirror_half([(0, 3.6), (1.1, 3.6), (1.1, 2.4), (1.0, 1.75), (0.75, 1.2), (0.4, 0.82), (0, 0.6)])
    big = [(x * 1.08, 0.55 + (z - 0.55) * 1.04) for x, z in sh]
    relief("ShieldBack", big, 0.0, 0.14, lq)
    split = 2.45
    tl = [(-1.1, 3.6), (0, 3.6), (0, split), (-1.1, split)]
    tr = [(0, 3.6), (1.1, 3.6), (1.1, split), (0, split)]
    bl = [(0, split), (-1.1, split), (-1.0, 1.75), (-0.75, 1.2), (-0.4, 0.82), (0, 0.6)]
    br = [(-x, z) for x, z in bl][::-1]
    relief("FieldTL", tl, -0.08, 0.02, red)
    relief("FieldTR", tr, -0.08, 0.02, ink)
    relief("FieldBL", bl, -0.08, 0.02, ink)
    relief("FieldBR", br, -0.08, 0.02, red)
    tube("Border", [(x, -0.1, z) for x, z in sh] + [(sh[0][0], -0.1, sh[0][1])], 0.045, gl, square=True, poly=True)
    tube("CrossV", [(0, -0.1, 3.58), (0, -0.1, 0.64)], 0.035, gl, square=True, poly=True)
    tube("CrossH", [(-1.08, -0.1, split), (1.08, -0.1, split)], 0.035, gl, square=True, poly=True)
    # charges: a raven (top left), a crescent (top right), a key (bottom left), a candle (bottom right)
    rp = [(0.42, 0.17), (0.27, 0.12), (0.22, 0.0), (0.12, -0.12), (0.1, -0.3), (0.06, -0.3), (0.04, -0.13), (-0.12, -0.1), (-0.42, -0.2), (-0.47, -0.12),
          (-0.15, 0.12), (0.08, 0.3), (0.24, 0.33), (0.32, 0.25), (0.42, 0.19)]
    rv = [(-0.55 + 0.9 * x, 3.0 + 0.9 * z) for x, z in rp]
    relief("Raven", rv, -0.1, 0.03, gl)
    cres = [(0.55 + 0.32 * math.cos(a), 3.0 + 0.32 * math.sin(a)) for a in [math.pi * (0.25 + 1.5 * i / 14) for i in range(15)]]
    cres += [(0.68 + 0.24 * math.cos(a), 3.02 + 0.24 * math.sin(a)) for a in [math.pi * (1.75 - 1.5 * i / 14) for i in range(15)]]
    relief("Crescent", cres, -0.1, 0.03, gl)
    hoop("KeyBow", (-0.5, -0.1, 2.05), 0.13, "Y", gl, thick=0.03)
    tube("KeyShank", [(-0.5, -0.1, 1.92), (-0.5, -0.1, 1.2)], 0.03, gl, square=True, poly=True)
    for k, z in enumerate((1.25, 1.38)):
        box(f"KeyBit{k}", (0.16, 0.05, 0.07), (-0.42, -0.1, z), gl, bevel=0.01)
    box("CandleStick", (0.18, 0.05, 0.62), (0.45, -0.1, 1.75), gl, bevel=0.02)
    box("CandleFoot", (0.4, 0.05, 0.07), (0.45, -0.1, 1.42), gl, bevel=0.015)
    relief("CandleFlame", ellipse(0.45, 2.17, 0.07, 0.14, n=12), -0.1, 0.03, gl)
    # the crown above, the crimson mantling down the sides, the scroll of symbols below
    zc = 3.68
    box("CrownBand", (1.2, 0.12, 0.16), (0, -0.02, zc + 0.08), gl, bevel=0.03)
    for k in range(5):
        x = -0.5 + k * 0.25
        h = 0.32 if k % 2 == 0 else 0.22
        _spike(f"CrownSpike{k}", (x, -0.02, zc + 0.16 + h / 2), 0.07, h, gl, verts=4, rot=(0, 0, math.pi / 4))
        sphere(f"CrownPearl{k}", 0.045, (x, -0.02, zc + 0.18 + h), gl, seg=8, rings=4)
    for k in range(4):
        sphere(f"CrownJewel{k}", 0.035, (-0.38 + k * 0.25, -0.09, zc + 0.08), M["crimson"], seg=8, rings=4)
    # a curled parchment ribbon across the shield's point: a front band, tails folding back, rolled ends, gilt edges
    parch = material("Parchment", "NH_Paper", tint=(0.6, 0.48, 0.31), scale=0.7, wear=0.15, dirt=0.95)
    parch_dk = flat("ParchmentFold", (0.38, 0.3, 0.19), 0.85, dirt=0.6)
    RW = 0.3
    band = [(-0.95, -0.22, 1.02), (-0.5, -0.245, 0.93), (0.0, -0.25, 0.97), (0.5, -0.245, 0.93), (0.95, -0.22, 1.02)]
    strip("Scroll", band, RW, (0, 0, 1), parch, thick=0.02, it=3)
    edges = [(_smooth(band, 3), (0, 0, 1))]
    for sx in (-1, 1):
        tail = [(sx * 0.93, -0.19, 1.0), (sx * 1.18, -0.14, 0.95), (sx * 1.42, -0.1, 0.85)]
        side = Vector((0, 0.32, 1)).normalized()
        strip(f"ScrollTail{sx}", tail, RW, tuple(side), parch, thick=0.02, it=2)
        edges.append((_smooth(tail, 2), tuple(side)))
        tube(f"ScrollFold{sx}", [(sx * 0.95, -0.215, 1.02 - RW / 2), (sx * 0.95, -0.215, 1.02 + RW / 2)], 0.016, parch_dk, poly=True)
        # the rolled end: a short cylinder of parchment with the curl spiralling in on both faces
        rx, ry, rz = sx * 1.5, -0.09, 0.82
        cyl(f"ScrollRoll{sx}", 0.085, RW + 0.02, (rx, ry, rz), parch, verts=16, bevel=0.01)
        for zz in (rz + (RW + 0.02) / 2 + 0.002, rz - (RW + 0.02) / 2 - 0.002):
            spiral = [(rx + math.cos(a) * (0.08 - 0.045 * a / 9.4), ry + math.sin(a) * (0.08 - 0.045 * a / 9.4), zz) for a in [i * 0.4 for i in range(24)]]
            tube(f"ScrollCurl{sx}{zz:.2f}", spiral, 0.007, parch_dk, poly=True)
        hoop(f"ScrollRollGilt{sx}", (rx, ry, rz + RW / 2 - 0.02), 0.087, "Z", gl, thick=0.009)
        hoop(f"ScrollRollGiltB{sx}", (rx, ry, rz - RW / 2 + 0.02), 0.087, "Z", gl, thick=0.009)
    for k, (path, side) in enumerate(edges):
        sv_ = Vector(side).normalized() * (RW / 2 - 0.01)
        for e, sg in (("T", 1), ("B", -1)):
            tube(f"ScrollGilt{k}{e}", [tuple(Vector(p) + sv_ * sg + Vector((0, -0.012, 0))) for p in path], 0.011, gl, poly=True)
    return _dims()


# ================================================================== decanter tray
def decanter_tray(M):
    sv = silver()
    amber = flat("Brandy", (0.42, 0.16, 0.025), 0.05)
    wine = flat("Wine", (0.22, 0.008, 0.018), 0.05)
    crystal = M["glassclear"]
    set_group("Main")
    lathe("Tray", [(0, 0.08), (0.98, 0.08), (1.0, 0.1), (1.02, 0.17), (1.0, 0.18), (0.96, 0.11), (0, 0.11)], sv, seg=48, scale=(1, 0.6))
    hoop_pts = [(math.cos(a) * 1.02, math.sin(a) * 0.612, 0.17) for a in [i / 48 * 2 * math.pi for i in range(48)]]
    tube("TrayBead", hoop_pts, 0.014, sv, closed=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Foot{sx}{sy}", 0.045, (sx * 0.65, sy * 0.38, 0.045), sv, seg=8, rings=4)
        tube(f"Handle{sx}", [(sx * 0.98, -0.18, 0.15), (sx * 1.12, -0.15, 0.22), (sx * 1.14, 0.0, 0.24), (sx * 1.12, 0.15, 0.22), (sx * 0.98, 0.18, 0.15)],
             0.02, sv)
    # the liquids (opaque, inside the glass)
    deck = ((-0.45, 0.12, amber, 0.62), (0.3, 0.14, wine, 0.5))
    for k, (x, y, liq, lvl) in enumerate(deck):
        lathe(f"Liquid{k}", [(0, 0.12), (0.27, 0.12), (0.31, 0.25), (0.31, lvl), (0, lvl)], liq, seg=20, loc=(x, y, 0))
        tube(f"LabelChain{k}", circle_pts(x, y, 0.86, 0.175, "Z", 16), 0.006, sv, closed=True, poly=True)
        box(f"Label{k}", (0.17, 0.012, 0.08), (x, y - 0.262, 0.76), sv, bevel=0.004, rot=(math.radians(-22), 0, 0))
    lathe("WineInGlass", [(0, 0.38), (0.07, 0.385), (0.1, 0.43), (0, 0.43)], wine, seg=16, loc=(0.75, -0.12, 0))
    set_group("Glass")
    for k, (x, y, _, _) in enumerate(deck):
        lathe(f"Decanter{k}", [(0, 0.11), (0.3, 0.11), (0.34, 0.25), (0.34, 0.6), (0.22, 0.82), (0.08, 0.92), (0.075, 1.08), (0.1, 1.11), (0.06, 1.12),
                               (0.06, 0.94), (0.2, 0.83), (0.32, 0.6), (0.32, 0.25), (0.28, 0.13), (0, 0.13)], crystal, seg=24, loc=(x, y, 0))
        lathe(f"Stopper{k}", [(0, 1.08), (0.05, 1.08), (0.05, 1.13), (0.11, 1.2), (0.09, 1.3), (0, 1.34)], crystal, seg=8, loc=(x, y, 0))
    for k, (x, y) in enumerate(((0.75, -0.12), (0.38, -0.38), (-0.05, -0.34))):
        lathe(f"Goblet{k}", [(0, 0.11), (0.1, 0.11), (0.1, 0.125), (0.02, 0.15), (0.018, 0.33), (0.08, 0.36), (0.13, 0.45), (0.135, 0.56), (0.125, 0.56),
                             (0.12, 0.46), (0.07, 0.38), (0, 0.37)], crystal, seg=18, loc=(x, y, 0))
    set_group("Main")
    return _dims()


# ================================================================== hourglass
def hourglass(M):
    gl = gilt()
    lq = lacquer()
    sand = flat("RedSand", (0.62, 0.07, 0.04), 0.92)
    thin_lq = flat("LacquerThin", (0.018, 0.016, 0.022), 0.28, wear=0.0, dirt=0.4)   # thin parts: the painted set shows its worn base
    H = 1.6
    set_group("Main")
    for k, z in enumerate((0.0, H - 0.16)):
        lathe(f"Plate{k}", [(0, z), (0.44, z), (0.46, z + 0.03), (0.42, z + 0.07), (0.44, z + 0.11), (0.42, z + 0.16), (0, z + 0.16)], M["brass"], seg=32)
        cyl(f"Lacquer{k}", 0.36, 0.03, (0, 0, 0.17 if k == 0 else H - 0.17), lq, verts=32, bevel=0.008)
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        px, py = math.cos(a) * 0.38, math.sin(a) * 0.38
        s = _mark()
        twist(f"Post{k}", 0.2, H - 0.2, 0.045, thin_lq, lobes=3, depth=0.3, turns=3.0, seg=12, rings=36)
        _xform(s, Matrix.Translation((px, py, 0)))
        sphere(f"PostKnopLow{k}", 0.06, (px, py, 0.2), gl, seg=8, rings=4)
        sphere(f"PostKnopHigh{k}", 0.06, (px, py, H - 0.2), gl, seg=8, rings=4)
        lathe(f"Finial{k}", [(0, H), (0.05, H), (0.04, H + 0.06), (0.02, H + 0.1), (0, H + 0.12)], gl, seg=10, loc=(px, py, 0))
    # the sand: a pile below, the rest above, a thin stream through the neck
    lathe("SandLow", [(0, 0.2), (0.26, 0.2), (0.28, 0.3), (0.24, 0.4), (0.13, 0.48), (0.03, 0.53), (0, 0.54)], sand, seg=20)
    lathe("SandHigh", [(0, 0.83), (0.06, 0.85), (0.17, 0.93), (0.25, 1.0), (0.29, 1.1), (0.25, 1.08), (0.12, 1.05), (0, 1.03)], sand, seg=20)
    cyl("Stream", 0.008, 0.46, (0, 0, 0.63), sand, verts=6, bevel=0)
    set_group("Glass")
    lathe("Bulbs", [(0, 0.19), (0.12, 0.19), (0.27, 0.27), (0.31, 0.42), (0.26, 0.6), (0.1, 0.74), (0.035, 0.8), (0.1, 0.86), (0.26, 1.0),
                    (0.31, 1.18), (0.27, 1.33), (0.12, 1.41), (0, 1.41)], M["glassclear"], seg=28)
    set_group("Main")
    return _dims()


# the tall wall pieces need the preview camera a little further back; doors open outward
P.PREVIEW_PAD.update({"CuriosityCabinet": 1.05, "FounderPortrait": 1.05, "Fireplace": 1.0, "HeadmasterChair": 1.05})
P.OPEN_DEG.update({"Safe_Door0": 100, "CuriosityCabinet_Door0": 100, "CuriosityCabinet_Glass": 100})

P.BUILD.update({
    "HeadmasterDesk": headmaster_desk,
    "HeadmasterChair": headmaster_chair,
    "Fireplace": fireplace,
    "FounderPortrait": founder_portrait,
    "Safe": safe,
    "CuriosityCabinet": curiosity_cabinet,
    "OfficeRug": office_rug,
    "DeskLamp": desk_lamp,
    "FounderBust": founder_bust,
    "SchoolCrest": school_crest,
    "DecanterTray": decanter_tray,
    "Hourglass": hourglass,
})
