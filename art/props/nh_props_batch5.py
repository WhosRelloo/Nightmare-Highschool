"""Props batch 5 (2026-11-03): gym, lighting and bathroom props for nh_props.py, in the same gothic style.

  Bleachers       four tiers of crimson enamel steel seats and iron foot boards on a wrought-iron frame, quatrefoil end frames, a back
                  rail and brass seat numbers
  Chandelier      a two-tier wrought-iron ring chandelier: twelve candles on scrolled arms, a crown of spikes, a
                  turned baluster and a drop finial, hung by a chain from a ceiling rose (Glow: the flames)
  GothicMirror    a tall pointed-arch hall mirror in a cast-iron frame with clustered columns, gilt beads,
                  pinnacles and a black marble ledge (Mirror: the glass)
  BathroomMirror  an iron-framed washroom mirror with a pointed top, rivets and a brass shelf (Mirror: the glass)
  Sink            a marble washstand with a drop-in porcelain basin on a fluted iron pedestal, a marble
                  splashback and two brass pillar taps (TapHot / TapCold: the cross heads, origin on the spindle,
                  they turn; Water: the two streams, shown while the sink runs)
  ToiletStall     a washroom stall in black marble with brass-inlaid arches, cast-iron clustered pilasters with
                  pinnacles, a crimson enamel door in an iron frame with strap hinges and an occupied latch (Door0:
                  origin on the hinge), and inside a porcelain toilet with a black lacquer seat, a high cast-iron
                  cistern with a pull chain, and a paper holder
  TowelRail       a brass towel rail on two brackets with a folded crimson towel

Front faces -Y, Z is up, the origin is at the bottom centre (wall pieces: the back sits at +Y).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, _gable, _quatrefoil, _pinnacle, _column, _arch_loop, \
    _arch_loop_x, _strap_hinge, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, strip, prism, rrect, _mark, _xform, _dims, flat


def marble(name, base=(0.82, 0.8, 0.76), vein=(0.3, 0.29, 0.3), scale=1.6, width=0.06, distortion=14.0, detail=6.0):
    """Polished marble: a pale ground with soft clouding and thin dark veins (wave texture, distorted)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L = nt.links.new
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "DIAGONAL"
    wv.inputs["Scale"].default_value = scale
    wv.inputs["Distortion"].default_value = distortion
    wv.inputs["Detail"].default_value = detail
    wv.inputs["Detail Scale"].default_value = 1.5
    L(tc.outputs["Object"], wv.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeValToRGB")
    e = vr.color_ramp.elements
    e[0].position, e[0].color = 0.0, (*vein, 1)
    e[1].position, e[1].color = width, (*base, 1)
    L(wv.outputs["Fac"], vr.inputs["Fac"])
    cl = nt.nodes.new("ShaderNodeTexNoise")
    cl.inputs["Scale"].default_value = 3.0
    cl.inputs["Detail"].default_value = 4.0
    L(tc.outputs["Object"], cl.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.25
    L(vr.outputs["Color"], mix.inputs[6])
    L(cl.outputs["Color"], mix.inputs[7])
    mv = nt.nodes.new("ShaderNodeValue")
    mv.outputs[0].default_value = 0.0
    P._weather(nt, bs, mix.outputs[2], 0.12, mv.outputs[0], None, 0.05, False, 0.6)
    return m


# ================================================================== bleachers
def bleachers(M):
    W, N = 16.0, 4
    rows = [(1.05 + 0.95 * i, -2.3 + 1.3 * i) for i in range(N)]    # (seat top z, seat centre y)
    frames = (-7.8, -3.9, 0.0, 3.9, 7.8)
    for i, (zs, ys) in enumerate(rows):
        for k, dy in enumerate((-0.15, 0.15)):
            box(f"Seat{i}{k}", (W, 0.28, 0.1), (0, ys + dy, zs - 0.05), M["crimson"], bevel=0.025)
            box(f"Foot{i}{k}", (W, 0.28, 0.08), (0, ys - 0.72 + dy, zs - 0.92), M["iron"], bevel=0.02)
        box(f"Riser{i}", (W, 0.05, 0.78), (0, ys - 0.3, zs - 0.5), M["iron"], bevel=0.012)
        for x in frames[:-1]:
            box(f"Number{i}{x}", (0.36, 0.02, 0.07), (x + 1.95, ys - 0.31, zs - 0.06), M["brass"], bevel=0.006)
    for x in frames:
        tube(f"Stringer{x}", [(x, -3.15, 0.04), (x, rows[-1][1] + 0.45, rows[-1][0] - 0.12)], 0.06, M["iron"], square=True, poly=True)
        for i, (zs, ys) in enumerate(rows):
            tube(f"Post{x}{i}", [(x, ys, 0.04), (x, ys, zs - 0.1)], 0.045, M["iron"], square=True, poly=True)
            tube(f"Bearer{x}{i}", [(x, ys - 0.36, zs - 0.12), (x, ys + 0.36, zs - 0.12)], 0.04, M["iron"], square=True, poly=True)
            tube(f"FootBearer{x}{i}", [(x, ys - 1.02, zs - 0.98), (x, ys - 0.42, zs - 0.98)], 0.035, M["iron"], square=True, poly=True)
            box(f"Shoe{x}{i}", (0.22, 0.22, 0.05), (x, ys, 0.025), M["iron"], bevel=0.01)
        tube(f"Tie{x}", [(x, rows[0][1], 0.5), (x, rows[-1][1], 0.5)], 0.03, M["iron"], square=True, poly=True)
    # back rail on posts
    zt, yt = rows[-1][0] + 1.1, rows[-1][1] + 0.4
    tube("BackRail", [(-W / 2, yt, zt), (W / 2, yt, zt)], 0.045, M["iron"], poly=True)
    for x in frames:
        tube(f"RailPost{x}", [(x, yt, rows[-1][0] - 0.1), (x, yt, zt)], 0.035, M["iron"], square=True, poly=True)
        sphere(f"RailKnob{x}", 0.07, (x, yt, zt + 0.04), M["brass"], seg=10, rings=5)
    # quatrefoil end frames and sloped end handrails
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.06)
        for k, (zs, ys) in enumerate(rows[:3]):
            s = _mark()
            _quatrefoil(f"End{sx}{k}", 0, 0, 0, 0.32, M["iron"])
            _xform(s, Matrix.Translation((x, ys + 0.65, zs - 0.35)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        tube(f"HandRail{sx}", [(x, -3.0, 1.0), (x, rows[-1][1] + 0.4, rows[-1][0] + 1.1)], 0.04, M["iron"], poly=True)
        y0, y1, z0r, z1r = -3.0, rows[-1][1] + 0.4, 1.0, rows[-1][0] + 1.1
        for i, (zs, ys) in enumerate(rows):
            yb = ys - 0.6
            zr = z0r + (yb - y0) / (y1 - y0) * (z1r - z0r)
            tube(f"Baluster{sx}{i}", [(x, yb, zs - 0.9 if i else 0.05), (x, yb, zr)], 0.025, M["iron"], poly=True)
    return _dims()


# ================================================================== chandelier
def chandelier(M):
    wax = flat("Wax", (0.84, 0.77, 0.6), 0.5, dirt=0.55)
    set_group("Main")
    H = 5.2
    # ceiling rose and chain
    lathe("Rose", [(0, H - 0.12), (0.4, H - 0.12), (0.42, H - 0.06), (0.36, H - 0.02), (0.36, H), (0, H)], M["iron"], seg=28)
    for k in range(7):
        z = H - 0.2 - k * 0.17
        hoop(f"Link{k}", (0, 0, z), 0.07, "X" if k % 2 else "Y", M["iron"], thick=0.016)
    zc = H - 1.45
    # crown: a ring with spikes, then the baluster
    hoop("CrownRing", (0, 0, zc), 0.45, "Z", M["iron"], thick=0.03)
    for k in range(4):
        a = k / 4 * 2 * math.pi
        tube(f"Strap{k}", [(math.cos(a) * 0.45, math.sin(a) * 0.45, zc), (0, 0, zc + 0.38)], 0.02, M["iron"], poly=True)
    lathe("Baluster", [(0, 0.55), (0.08, 0.55), (0.14, 0.7), (0.1, 0.9), (0.18, 1.1), (0.22, 1.25), (0.14, 1.45), (0.09, 1.7), (0.09, 2.4),
                       (0.16, 2.55), (0.12, 2.75), (0.08, 3.0), (0.07, zc + 0.4), (0, zc + 0.4)], M["iron"], seg=20)
    cone("Drop", 0.1, 0.0, 0.5, (0, 0, 0.3), M["iron"], verts=8, rot=(math.pi, 0, 0))
    sphere("DropBall", 0.07, (0, 0, 0.58), M["brass"], seg=10, rings=5)
    flames = []
    for tier, (n, r, za, zr, spikes) in enumerate(((8, 1.75, 1.2, 1.35, True), (4, 0.95, 2.45, 2.55, False))):
        hoop(f"Ring{tier}", (0, 0, zr), r, "Z", M["iron"], thick=0.035)
        for k in range(n):
            a = k / n * 2 * math.pi + (math.pi / n if tier else 0)
            c, s_ = math.cos(a), math.sin(a)
            pts = [(0.12, za), (r * 0.35, za - 0.22), (r * 0.7, za - 0.1), (r, zr + 0.05), (r, zr + 0.2)]
            tube(f"Arm{tier}{k}", [(c * rr, s_ * rr, z) for rr, z in pts], 0.03, M["iron"])
            curl = [(r * 0.35, za - 0.22), (r * 0.3, za - 0.38), (r * 0.4, za - 0.44), (r * 0.44, za - 0.34)]
            tube(f"Curl{tier}{k}", [(c * rr, s_ * rr, z) for rr, z in curl], 0.018, M["iron"])
            x, y, z = c * r, s_ * r, zr + 0.2
            cyl(f"Pan{tier}{k}", 0.14, 0.03, (x, y, z), M["brass"], verts=16, bevel=0.008)
            cyl(f"Cup{tier}{k}", 0.07, 0.1, (x, y, z + 0.06), M["brass"], verts=12, bevel=0.01)
            h = 0.42 if tier == 0 else 0.5
            cyl(f"Candle{tier}{k}", 0.055, h, (x, y, z + 0.1 + h / 2), wax, verts=12, bevel=0.01)
            sphere(f"Drip{tier}{k}", 0.022, (x + c * 0.055, y + s_ * 0.055, z + 0.1 + h - 0.08), wax, seg=6, rings=4, scale=(1, 1, 2.4))
            tube(f"Wick{tier}{k}", [(x, y, z + 0.1 + h), (x, y, z + 0.14 + h)], 0.008, M["felt"], poly=True)
            flames.append((x, y, z + 0.11 + h))
            if spikes:
                a2 = a + math.pi / n
                cone(f"Spike{k}", 0.04, 0.0, 0.28, (math.cos(a2) * r, math.sin(a2) * r, zr + 0.16), M["iron"], verts=4)
                sphere(f"Pendant{k}", 0.05, (math.cos(a2) * r, math.sin(a2) * r, zr - 0.12), M["brass"], seg=8, rings=4, scale=(1, 1, 1.5))
    set_group("Glow")
    for k, p in enumerate(flames):
        flame(f"Flame{k}", p, h=0.15)
    set_group("Main")
    return _dims()


# ================================================================== mirrors
def gothic_mirror(M):
    silver = flat("Silvered", (0.72, 0.74, 0.77), 0.04, metal=1.0, dirt=0.3)
    hw, z0, zs, za = 1.15, 0.55, 4.3, 5.55
    set_group("Main")
    back = _arch_loop(0, 0, hw + 0.3, z0 - 0.2, zs, za + 0.32)
    prism("Back", [(x, z) for x, _, z in back], 0.07, 0.1, M["iron"], bevel=0.02)
    tube("Frame", _arch_loop(0, -0.04, hw + 0.1, z0, zs, za + 0.1), 0.13, M["iron"], square=True, closed=True, poly=True)
    tube("Bead", _arch_loop(0, -0.17, hw + 0.01, z0 + 0.02, zs, za), 0.035, M["brass"], closed=True, poly=True)
    tube("OuterBead", _arch_loop(0, -0.1, hw + 0.23, z0 - 0.12, zs, za + 0.25), 0.03, M["brass"], closed=True, poly=True)
    for sx in (-1, 1):
        _column(f"Col{sx}", sx * (hw + 0.33), -0.12, z0 - 0.1, zs + 0.1, 0.06, M["iron"], M["brass"])
        _pinnacle(f"Pin{sx}", sx * (hw + 0.33), -0.1, zs + 0.1, 0.7, M["iron"])
    _pinnacle("Apex", 0, -0.06, za + 0.2, 0.75, M["iron"])
    _quatrefoil("Seal", 0, -0.2, zs + 0.62, 0.16, M["brass"])
    box("Ledge", (2 * hw + 0.9, 0.42, 0.14), (0, -0.14, z0 - 0.2), marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5), bevel=0.03)
    box("LedgeLip", (2 * hw + 1.0, 0.1, 0.08), (0, -0.33, z0 - 0.16), M["brass"], bevel=0.02)
    for sx in (-1, 1):
        # carved corbels under the ledge (side profile in Y, Z)
        prism(f"Corbel{sx}", [(0.06, 0.0), (-0.32, 0.0), (-0.28, -0.07), (-0.1, -0.12), (0.06, -0.25)], sx * 0.8, 0.14, M["iron"],
              plane="YZ", bevel=0.01)
        _xform(len(P.PARTS) - 1, Matrix.Translation((0, 0, z0 - 0.27)))
    set_group("Mirror")
    prism("Glass", [(x, z) for x, _, z in _arch_loop(0, 0, hw, z0, zs, za)], -0.06, 0.02, silver)
    set_group("Main")
    return _dims()


def bathroom_mirror(M):
    silver = flat("Silvered", (0.72, 0.74, 0.77), 0.04, metal=1.0, dirt=0.3)
    hw, z0, zs, za = 0.85, 0.5, 2.05, 2.62
    set_group("Main")
    prism("Back", [(x, z) for x, _, z in _arch_loop(0, 0, hw + 0.12, z0 - 0.1, zs, za + 0.14)], 0.05, 0.06, M["iron"], bevel=0.01)
    tube("Frame", _arch_loop(0, -0.02, hw + 0.05, z0, zs, za + 0.05), 0.065, M["iron"], square=True, closed=True, poly=True)
    tube("Bead", _arch_loop(0, -0.08, hw, z0 + 0.01, zs, za), 0.02, M["brass"], closed=True, poly=True)
    pts = _arch_loop(0, -0.09, hw + 0.05, z0, zs, za + 0.05)
    for k, p in enumerate(pts[::2]):
        sphere(f"Rivet{k}", 0.025, p, M["brass"], seg=8, rings=4)
    sphere("Finial", 0.06, (0, -0.02, za + 0.16), M["brass"], seg=10, rings=5)
    # a brass shelf with a bottle and a comb
    box("Shelf", (1.5, 0.36, 0.04), (0, -0.2, z0 - 0.2), M["brass"], bevel=0.01)
    tube("Gallery", [(-0.74, -0.37, z0 - 0.18), (-0.74, -0.37, z0 - 0.1), (0.74, -0.37, z0 - 0.1), (0.74, -0.37, z0 - 0.18)], 0.012, M["brass"], poly=True)
    for sx in (-1, 1):
        tube(f"Bracket{sx}", [(sx * 0.6, 0.02, z0 - 0.5), (sx * 0.6, -0.04, z0 - 0.3), (sx * 0.6, -0.32, z0 - 0.22)], 0.02, M["brass"])
    lathe("Bottle", [(0, 0), (0.08, 0), (0.085, 0.02), (0.085, 0.2), (0.05, 0.26), (0.03, 0.28), (0.03, 0.33), (0, 0.33)], M["glassamber"], seg=16,
          loc=(-0.45, -0.2, z0 - 0.18))
    cyl("Stopper", 0.035, 0.05, (-0.45, -0.2, z0 + 0.17), M["oakdark"], verts=10)
    box("Comb", (0.32, 0.06, 0.015), (0.35, -0.22, z0 - 0.17), M["glass"], bevel=0.004, rot=(0, 0, 0.3))
    set_group("Mirror")
    prism("Glass", [(x, z) for x, _, z in _arch_loop(0, 0, hw, z0, zs, za)], -0.04, 0.015, silver)
    set_group("Main")
    return _dims()


# ================================================================== sink
def sink(M):
    porcelain = flat("Porcelain", (0.82, 0.8, 0.74), 0.08, wear=0.02, dirt=0.6)
    stone = marble("Marble")
    water = flat("Water", (0.55, 0.68, 0.78), 0.02)
    T, by = 2.7, -0.12            # top of the marble, basin centre y (the back sits at +0.75)
    set_group("Main")
    # fluted iron pedestal
    lathe("PedFoot", [(0, 0), (0.55, 0), (0.57, 0.06), (0.46, 0.16), (0.34, 0.28), (0.3, 0.36), (0, 0.36)], M["iron"], seg=32, loc=(0, by, 0))
    lathe("Pedestal", [(0, 0.3), (0.3, 0.3), (0.22, 0.6), (0.2, 1.6), (0, 1.6)], M["iron"], seg=48, loc=(0, by, 0), flute=(12, 0.1))
    lathe("PedCap", [(0, 1.55), (0.21, 1.55), (0.3, 1.8), (0.45, 2.1), (0.5, T - 0.5), (0, T - 0.5)], M["iron"], seg=32, loc=(0, by, 0))
    hoop("PedBand", (0, by, 0.62), 0.225, "Z", M["brass"], thick=0.018)
    # marble top round a drop-in porcelain basin
    ox, oy = 0.68, 0.5
    for name, x0, x1, y0, y1 in (("TopF", -1.2, 1.2, -0.95, by - oy), ("TopB", -1.2, 1.2, by + oy, 0.7),
                                 ("TopL", -1.2, -ox, by - oy, by + oy), ("TopR", ox, 1.2, by - oy, by + oy)):
        box(name, (x1 - x0, y1 - y0, 0.24), ((x0 + x1) / 2, (y0 + y1) / 2, T - 0.12), stone, bevel=0.02)
    box("TopEdge", (2.46, 0.08, 0.08), (0, -0.97, T - 0.2), stone, bevel=0.025)
    lathe("Basin", [(0, T - 0.5), (0.25, T - 0.48), (0.5, T - 0.3), (0.62, T - 0.05), (0.75, T), (0.76, T + 0.03), (0.6, T + 0.045),
                    (0.54, T + 0.02), (0.5, T - 0.08), (0.4, T - 0.28), (0.2, T - 0.4), (0, T - 0.42)], porcelain, seg=48, loc=(0, by, 0), scale=(1.3, 0.95))
    cyl("Drain", 0.07, 0.01, (0, by, T - 0.415), M["brass"], verts=16, bevel=0)
    tube("DrainChain", [(0.06, by, T - 0.41), (0.3, by + 0.25, T - 0.2), (0.45, by + 0.45, T + 0.02)], 0.008, M["brass"])
    cyl("Plug", 0.065, 0.03, (0.46, by + 0.48, T + 0.015), M["glass"], verts=14, bevel=0.005)
    # splashback with a pointed crest
    box("Splash", (2.4, 0.1, 1.15), (0, 0.72, T + 0.575), stone, bevel=0.02)
    _gable("SplashCrest", 0, 0.72, 0.7, T + 1.15, T + 1.6, 0.1, stone, M["brass"], edge=0.025)
    _quatrefoil("SplashSeal", 0, 0.66, T + 1.33, 0.1, M["brass"])
    # soap in a brass dish
    lathe("SoapDish", [(0, T), (0.2, T), (0.22, T + 0.04), (0.19, T + 0.05), (0, T + 0.02)], M["brass"], seg=20, loc=(0.97, 0.48, 0), scale=(1.0, 0.75))
    box("Soap", (0.26, 0.15, 0.09), (0.97, 0.48, T + 0.075), porcelain, bevel=0.035, segments=3)
    # pillar taps: the bodies and spouts are fixed, the cross heads turn (their own pieces)
    heads = []
    for side, sx, dot in (("TapHot", -1, M["crimson"]), ("TapCold", 1, M["inkblue"])):
        x, y = sx * 0.5, 0.56
        lathe(f"{side}Body", [(0, T), (0.11, T), (0.12, T + 0.03), (0.07, T + 0.08), (0.06, T + 0.3), (0.075, T + 0.36), (0.05, T + 0.42),
                              (0, T + 0.42)], M["brass"], seg=20, loc=(x, y, 0))
        tube(f"{side}Spout", [(x, y, T + 0.3), (x, y - 0.18, T + 0.34), (x * 0.75, y - 0.36, T + 0.3), (x * 0.7, y - 0.42, T + 0.2)], 0.035, M["brass"])
        heads.append((side, x, y, dot))
    for side, x, y, dot in heads:
        set_group(side, hinge=(x, y, T + 0.42), swing=1)
        cyl(f"{side}Spindle", 0.03, 0.1, (x, y, T + 0.47), M["brass"], verts=10)
        for k in range(4):
            a = k / 4 * 2 * math.pi + math.pi / 4
            tube(f"{side}Arm{k}", [(x, y, T + 0.5), (x + math.cos(a) * 0.16, y + math.sin(a) * 0.16, T + 0.52)], 0.02, M["brass"], poly=True)
            sphere(f"{side}Ball{k}", 0.035, (x + math.cos(a) * 0.17, y + math.sin(a) * 0.17, T + 0.52), M["brass"], seg=8, rings=4)
        cyl(f"{side}Cap", 0.05, 0.03, (x, y, T + 0.53), porcelain, verts=14, bevel=0.008)
        cyl(f"{side}Index", 0.03, 0.01, (x, y, T + 0.548), dot, verts=12, bevel=0)
    set_group("Water")
    for side, x, y, dot in heads:
        tube(f"{side}Stream", [(x * 0.7, y - 0.42, T + 0.18), (x * 0.65, y - 0.44, T - 0.1), (x * 0.5, y - 0.45, T - 0.38)], 0.022, water)
    lathe("Pool", [(0, T - 0.405), (0.24, T - 0.405), (0.22, T - 0.39), (0, T - 0.385)], water, seg=24, loc=(0, by, 0), scale=(1.2, 0.9))
    set_group("Main")
    return _dims()


# ================================================================== toilet stall
def toilet_stall(M):
    porcelain = flat("Porcelain", (0.82, 0.8, 0.74), 0.08, wear=0.02, dirt=0.6)
    slab = marble("MarbleBlack", base=(0.03, 0.028, 0.034), vein=(0.4, 0.38, 0.33), scale=0.9, width=0.03, distortion=6.0, detail=2.5)
    lacquer = flat("BlackLacquer", (0.02, 0.018, 0.022), 0.18, wear=0.05)
    W, D, H = 3.6, 5.6, 6.6
    yf = -D / 2 + 0.1                 # the front line (door and pilasters)
    set_group("Body")
    # partitions and back: black marble slabs on iron shoes, brass caps and inlaid pointed arches
    for sx in (-1, 1):
        x = sx * W / 2
        box(f"Panel{sx}", (0.1, D - 0.3, 5.4), (x, 0.05, 3.3), slab, bevel=0.02)
        box(f"Cap{sx}", (0.16, D - 0.2, 0.06), (x, 0.05, 6.03), M["brass"], bevel=0.012)
        for k, cy in enumerate((-1.3, 1.3)):
            for face in (-1, 1):
                tube(f"Inlay{sx}{k}{face}", _arch_loop_x(x + face * 0.055, cy, 1.0, 1.0, 4.6, 5.7), 0.014, M["brass"], square=True, closed=True, poly=True)
        for cy in (yf + 0.3, D / 2 - 0.3):
            box(f"Shoe{sx}{cy:.1f}", (0.2, 0.3, 0.62), (x, cy, 0.31), M["iron"], bevel=0.02)
    box("Back", (W + 0.1, 0.1, 6.0), (0, D / 2 - 0.05, 3.0), slab, bevel=0.02)
    box("BackCap", (W + 0.16, 0.16, 0.06), (0, D / 2 - 0.05, 6.03), M["brass"], bevel=0.012)
    # front: cast-iron clustered pilasters with pinnacles, an iron header, a crimson crest
    for sx in (-1, 1):
        px = sx * (W / 2 - 0.05)
        _column(f"Pilaster{sx}", px, yf, 0.0, H - 0.2, 0.1, M["iron"], M["brass"])
        _pinnacle(f"Pin{sx}", px, yf, H - 0.2, 0.7, M["iron"])
    box("Header", (W - 0.2, 0.24, 0.28), (0, yf, H - 0.34), M["iron"], bevel=0.03)
    box("HeaderBead", (W - 0.2, 0.03, 0.05), (0, yf - 0.13, H - 0.42), M["brass"], bevel=0.01)
    _gable("Crest", 0, yf, 0.6, H - 0.2, H + 0.25, 0.14, M["crimson"], M["brass"], edge=0.03)
    _quatrefoil("CrestSeal", 0, yf - 0.09, H + 0.02, 0.11, M["brass"])
    xh, xl = -W / 2 + 0.2, 0.62       # the door spans the hinge post to the latch post
    box("SidePanel", (W / 2 - 0.2 - xl - 0.1, 0.08, 5.2), ((xl + 0.1 + W / 2 - 0.2) / 2, yf, 3.2), slab, bevel=0.015)
    tube("SideInlay", _arch_loop((xl + 0.1 + W / 2 - 0.2) / 2, yf - 0.045, 0.3, 1.0, 4.7, 5.5), 0.012, M["brass"], square=True, closed=True, poly=True)
    box("LatchPost", (0.12, 0.18, H - 0.5), (xl + 0.05, yf, (H - 0.5) / 2 + 0.3), M["iron"], bevel=0.02)
    box("Keeper", (0.06, 0.08, 0.12), (xl - 0.02, yf - 0.1, 3.0), M["brass"], bevel=0.008)
    # the toilet: porcelain pedestal bowl, black lacquer seat and raised lid, a high cast-iron cistern with a pull chain
    ty = 1.55
    lathe("Bowl", [(0, 0), (0.42, 0), (0.45, 0.05), (0.38, 0.2), (0.32, 0.6), (0.42, 0.95), (0.55, 1.25), (0.58, 1.38), (0.52, 1.42),
                   (0.45, 1.38), (0.38, 1.2), (0.25, 1.0), (0, 0.92)], porcelain, seg=40, loc=(0, ty, 0), scale=(0.8, 1.0))
    seat = [(0.38, 1.42), (0.6, 1.42), (0.62, 1.46), (0.6, 1.5), (0.38, 1.5), (0.36, 1.46), (0.38, 1.42)]
    lathe("Seat", seat, lacquer, seg=40, loc=(0, ty, 0), scale=(0.8, 1.0))
    s = _mark()
    lathe("Lid", [(0, 0), (0.6, 0), (0.62, 0.03), (0.58, 0.06), (0, 0.06)], lacquer, seg=40, scale=(0.8, 1.0))
    _xform(s, Matrix.Translation((0, ty + 0.62, 1.5)) @ Matrix.Rotation(math.radians(-100), 4, "X") @ Matrix.Translation((0, -0.6, 0)))
    for sx in (-1, 1):
        box(f"SeatHinge{sx}", (0.08, 0.1, 0.06), (sx * 0.3, ty + 0.62, 1.5), M["brass"], bevel=0.01)
    tube("FlushPipe", [(0, ty + 0.5, 1.2), (0, D / 2 - 0.35, 1.35), (0, D / 2 - 0.3, 1.8), (0, D / 2 - 0.3, 5.6)], 0.06, M["brass"])
    cz = 5.9
    box("Cistern", (1.5, 0.6, 0.7), (0, D / 2 - 0.45, cz), M["iron"], bevel=0.04)
    box("CisternLid", (1.6, 0.68, 0.08), (0, D / 2 - 0.45, cz + 0.39), M["iron"], bevel=0.02)
    _quatrefoil("CisternSeal", 0, D / 2 - 0.76, cz, 0.14, M["brass"])
    for sx in (-1, 1):
        tube(f"CisternBracket{sx}", [(sx * 0.55, D / 2 - 0.1, cz - 0.6), (sx * 0.55, D / 2 - 0.2, cz - 0.42), (sx * 0.55, D / 2 - 0.62, cz - 0.36),
                                     (sx * 0.55, D / 2 - 0.65, cz - 0.4)], 0.035, M["iron"], square=True)
    tube("FlushLever", [(0.6, D / 2 - 0.73, cz + 0.1), (0.7, D / 2 - 0.98, cz + 0.05)], 0.02, M["iron"], poly=True)
    for k in range(14):
        z = cz - 0.02 - k * 0.15
        hoop(f"Chain{k}", (0.7, D / 2 - 0.99, z), 0.05, "X" if k % 2 else "Y", M["brass"], thick=0.01)
    lathe("PullHandle", [(0, 0), (0.05, 0.02), (0.06, 0.1), (0.04, 0.2), (0.02, 0.24), (0, 0.25)], porcelain, seg=14,
          loc=(0.7, D / 2 - 0.99, cz - 2.4))
    # paper holder on the right partition
    px = W / 2 - 0.07
    box("HolderPlate", (0.03, 0.5, 0.2), (px, 0.4, 2.5), M["brass"], bevel=0.01)
    for cy in (0.2, 0.6):
        tube(f"HolderArm{cy}", [(px, cy, 2.5), (px - 0.28, cy, 2.5)], 0.02, M["brass"], poly=True)
    cyl("PaperRoll", 0.17, 0.36, (px - 0.28, 0.4, 2.5), M["paper"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
    cyl("PaperCore", 0.06, 0.37, (px - 0.28, 0.4, 2.5), M["iron"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0)
    # the door: crimson enamel steel in an iron frame with a pointed-arch overlay, strap hinges, a ring handle, an occupied latch
    set_group("Door0", hinge=(xh, yf, 0), swing=-1)         # -1: swings out (toward -Y, out of the stall)
    dw, z0, z1 = xl - xh, 0.7, 5.7
    cx = (xh + xl) / 2
    box("Door", (dw - 0.04, 0.08, z1 - z0), (cx, yf, (z0 + z1) / 2), M["crimson"], bevel=0.012)
    for face in (-1, 1):
        y = yf + face * 0.05
        tube(f"DoorFrame{face}", [(xh + 0.04, y, z0 + 0.03), (xl - 0.06, y, z0 + 0.03), (xl - 0.06, y, z1 - 0.03), (xh + 0.04, y, z1 - 0.03)], 0.035,
             M["iron"], square=True, closed=True, poly=True)
        tube(f"DoorArch{face}", _arch_loop(cx, y, dw / 2 - 0.3, z0 + 0.4, z1 - 1.4, z1 - 0.35), 0.025, M["iron"], square=True, closed=True, poly=True)
        _quatrefoil(f"DoorSeal{face}", cx, y + face * 0.01, z1 - 1.0, 0.16, M["brass"])
    for z in (z0 + 0.8, z1 - 0.8):
        _strap_hinge(f"Strap{z:.1f}", xh + 0.05, xh + 0.9, yf - 0.06, z, M["iron"])
    hoop("Handle", (xl - 0.28, yf - 0.1, 3.0), 0.08, "Y", M["brass"], thick=0.015)
    cyl("HandleRose", 0.06, 0.03, (xl - 0.28, yf - 0.06, 3.08), M["brass"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.005)
    box("Latch", (0.22, 0.04, 0.07), (xl - 0.15, yf + 0.07, 3.0), M["brass"], bevel=0.008)
    box("Indicator", (0.26, 0.03, 0.12), (xl - 0.28, yf - 0.06, 3.4), M["brass"], bevel=0.008)
    box("IndicatorWindow", (0.16, 0.012, 0.06), (xl - 0.28, yf - 0.08, 3.4), lacquer, bevel=0.0, segments=1)
    set_group("Body")
    return _dims()


# ================================================================== towel rail
def towel_rail(M):
    towel = material("Towel", "NH_Leather", tint=(0.3, 0.03, 0.045), scale=4.0, normal=0.25, rough_add=0.45, wear=0.05)
    W = 2.2
    for sx in (-1, 1):
        cyl(f"Rose{sx}", 0.1, 0.04, (sx * W / 2, 0.06, 0.6), M["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
        tube(f"Bracket{sx}", [(sx * W / 2, 0.06, 0.6), (sx * W / 2, -0.12, 0.62), (sx * W / 2, -0.24, 0.6)], 0.025, M["brass"])
        sphere(f"Knob{sx}", 0.045, (sx * (W / 2 + 0.05), -0.24, 0.6), M["brass"], seg=10, rings=5)
    tube("Rail", [(-W / 2, -0.24, 0.6), (W / 2, -0.24, 0.6)], 0.03, M["brass"], poly=True)
    strip("Towel", [(0, -0.12, 0.05), (0, -0.16, 0.35), (0, -0.2, 0.6), (0, -0.24, 0.65), (0, -0.28, 0.6), (0, -0.32, 0.3), (0, -0.33, 0.0)],
          1.3, (1, 0, 0), towel, thick=0.04)
    for end, (y, z) in enumerate(((-0.12, 0.05), (-0.33, 0.0))):
        box(f"Band{end}", (1.3, 0.05, 0.07), (0, y, z + 0.1), M["chalk"], bevel=0.01)
    return _dims()


P.PREVIEW_PAD.update({"Chandelier": 1.1, "GothicMirror": 1.1, "ToiletStall": 1.15})
# the stall door swings out, clear of its pilaster; the taps turn a quarter
P.OPEN_DEG.update({"ToiletStall_Door0": 95, "Sink_TapHot": 90, "Sink_TapCold": 90})

P.BUILD.update({
    "Bleachers": bleachers,
    "Chandelier": chandelier,
    "GothicMirror": gothic_mirror,
    "BathroomMirror": bathroom_mirror,
    "Sink": sink,
    "ToiletStall": toilet_stall,
    "TowelRail": towel_rail,
})
