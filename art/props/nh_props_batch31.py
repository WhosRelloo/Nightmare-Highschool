"""Props batch 31 (2026-11-05): builder's pieces to blend the stair kit (batch 20) into the map.

  StairStoneBlock a 4 x 4 x 4 block of the stair cheeks' own castle stone (the same material, grain scale, tint, wear and
                  dirt, baked the same way) with their softly worn edges (bevel 0.03), to fill round and under the
                  stairs without a change in the stone. (The bridges' tiled NH_CastleStone is a different stone: its
                  pitting is coarser, so it does not blend with the stairs.)
  StairRailLevel  StairStoneRailed's gothic cast-iron balustrade on a level run: 8 long, 2.3 high, 12 trefoil-headed
                  bays with gilt roundels and collars and the brass handrail. It has no bar at its +X end, so lengths
                  butt end to end with the bays and collars running on unbroken. A separate Post piece (the stair's
                  turned iron newel with its gilt ball) stands at the -X end; copy it to the far end of a run.

Front faces -Y, Z is up, the origin is at the bottom centre. Registered into nh_props.BUILD on import.
"""
import math

import bpy
from mathutils import Matrix

import nh_props as P
from nh_props import box, set_group
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, _mark, _xform, _dims
from nh_props_batch10 import gilt
from nh_props_batch8 import castle
from nh_props_batch20 import _iron_rake


def stone_block(M):
    # the stair cheeks' own stone (batch 8's castle(): NH_Limestone at 0.28, the greenish tint, wear and dirt), baked as they
    # are, so the grain, the cloudy dirt and the worn edges match a cheek wall side by side
    stone, _ = castle()
    set_group("Main")
    box("Block", (4.0, 4.0, 4.0), (0, 0, 2.0), stone, bevel=0.03, segments=2)
    return _dims()


RAIL_LEN, RAIL_H, BAYS = 8.0, 2.3, 12


def stair_rail_level(M):
    gl = gilt()
    set_group("Main")
    s = _mark()
    # built along Y in the plane x = 0 (as on a stair cheek), then turned to run along X
    _iron_rake("R", M, gl, 0.0, [(-RAIL_LEN / 2, 0.0), (RAIL_LEN / 2, 0.0)], RAIL_H, bay=RAIL_LEN / BAYS, rail=0.045, face=1)
    # drop the bar (and its gilt collar) at the far end: the next length's first bar stands there
    last = [ob for ob in P.PARTS[s:] if ob.name in (f"RBar{BAYS}", f"RCollar{BAYS}")]
    for ob in last:
        P.PARTS.remove(ob)
        bpy.data.objects.remove(ob, do_unlink=True)
    _xform(s, Matrix.Rotation(-math.pi / 2, 4, "Z"))
    set_group("Post")
    x = -RAIL_LEN / 2
    lathe("Post", [(0, 0), (0.13, 0), (0.1, 0.25), (0.07, 2.2), (0.12, 2.32), (0.1, 2.45), (0, 2.47)], M["iron"], seg=12, loc=(x, 0, 0))
    sphere("PostBall", 0.1, (x, 0, 2.56), gl, seg=12, rings=6)
    set_group("Main")
    return _dims()


BUILDERS = {
    "StairStoneBlock": stone_block,
    "StairRailLevel": stair_rail_level,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"StairStoneBlock": 1.3, "StairRailLevel": 1.0})
