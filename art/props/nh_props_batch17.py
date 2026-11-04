"""Props batch 17 (2026-11-04): the founders' memorial spire as a building piece, for the builder to crown towers, turrets
and big roofs. Same design and stone as the Memorial's spire (batch 8), at building scale.

  Spire       an octagonal stone spire 12 studs tall, 3 across at the base: a moulded collar, crockets climbing the eight
              edges in four rows, a sharp point
  SpireCross  the same spire with the Memorial's wrought-iron cross and ring on top, brass knobs

Scale it in Studio for bigger towers (it is one baked piece, so it scales cleanly). Front faces -Y, Z is up, the origin is
at the bottom centre (sit it on the top of a tower).
Registered into nh_props.BUILD on import (nh_props imports this module at the end).
"""
import math

import nh_props as P
from nh_props import box, tube
from nh_props_batch3 import sphere, cone, circle_pts
from nh_props_batch4 import lathe, _dims
from nh_props_batch8 import castle

R0, H = 1.5, 12.0          # base radius (to the octagon's corners) and the height to the point
ZC = 0.55                  # top of the collar


def _spire(M, cross):
    stone, dark = castle()
    P.set_group("Main")
    # the collar: a plinth course, a hollow and a rolled band, so it seats on a tower top
    lathe("Collar", [(0, 0), (R0 + 0.12, 0), (R0 + 0.12, 0.18), (R0 + 0.02, 0.24), (R0 + 0.08, 0.36), (R0 + 0.08, 0.46),
                     (R0, ZC), (0, ZC)], dark, seg=8)
    # the spire: an eight-sided cone, a corner to each crocket line
    cone("Spire", R0, 0.0, H - ZC, (0, 0, (ZC + H) / 2), stone, verts=8, rot=(0, 0, math.pi / 8))
    # a thin band a third of the way up, as on the memorial's shaft cornice
    zb = ZC + (H - ZC) * 0.12
    rb = R0 * (1 - 0.12)
    lathe("Band", [(0, zb - 0.06), (rb + 0.05, zb - 0.06), (rb + 0.09, zb), (rb + 0.05, zb + 0.06), (0, zb + 0.06)], dark, seg=8)
    # crockets up the eight edges (the cone's corners sit at pi/8 + k * pi/4)
    pts = []
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        for t in (0.26, 0.44, 0.62, 0.8):
            rr = R0 * (1 - t) * math.cos(math.pi / 8) + 0.05
            pts.append((math.cos(a) * rr, math.sin(a) * rr, ZC + (H - ZC) * t))
    # rounder knobs than the memorial's little 6-sided ones, which read as blocks at this size
    for k, p in enumerate(pts):
        sphere(f"Crocket{k}", 0.17, p, stone, seg=12, rings=7, scale=(1, 1, 1.45))
    if cross:
        zt = H - 0.05
        box("CrossStem", (0.16, 0.16, 1.5), (0, 0, zt + 0.7), M["iron"], bevel=0.02)
        box("CrossArm", (0.9, 0.16, 0.16), (0, 0, zt + 0.95), M["iron"], bevel=0.02)
        for p in ((0, 0, zt + 1.48), (0.47, 0, zt + 0.95), (-0.47, 0, zt + 0.95)):
            sphere(f"CrossEnd{p[0]:.2f}{p[2]:.2f}", 0.09, p, M["brass"], seg=8, rings=4)
        tube("CrossRing", circle_pts(0, 0, zt + 0.95, 0.27, "Y", 16), 0.03, M["iron"], closed=True, square=True, poly=True)
    return _dims()


P.PREVIEW_PAD.update({"Spire": 1.05, "SpireCross": 1.05})
P.BUILD.update({
    "Spire": lambda M: _spire(M, False),
    "SpireCross": lambda M: _spire(M, True),
})
