"""The Brass Loupe Monocle: the Anatomy elective's mastery piece (an A or better on the Frog, the Raven and the Wyvern;
Config.Anatomy.Mastery). Never sold: Services.School.Electives grants it with Features.Accessories.Grant.

A jeweller's loupe worn over the character's right painted eye (x -0.205, z 1.49 on the R6 head, the eye centres the
masks are fitted to; docs/Accessories.md "Masks sit on the painted eyes"):
  - a gold eye ring with a knurled edge, sitting on the face (its back 0.012 off the head's face cylinder)
  - a short flared brass barrel stepping out from the ring, with two turned bands
  - a front bezel with three screws and a pale, slightly tinted lens
  - a small hinge lug on the outer side with a gold loop, and a fine gold chain down the cheek to a teardrop fob at the
    jaw, so it reads as a monocle at a glance; the chain stays on the face (angle under 55 degrees from the front),
    clear of side locks and of the collar.
One Head piece, `LoupeMonocle` (Main, baked). Slot Face (Accessories.Slots has no Eyes slot yet: Kit C's C4 is not
built), so it is not worn with a mask.

E:/Blender/blender.exe -b --factory-startup -P nh_kitc_monocle.py -- LoupeMonocle --gpu --out E:/NH-Work/kitc_monocle
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mathutils import Vector
import nh_acc as A
sys.modules.setdefault("nh_acc", A)
from nh_acc import item, piece

HP = math.pi / 2
HEAD_R = 0.6          # the R6 mannequin head's face cylinder
GAP = 0.012
EYE_X, EYE_Z = -0.205, 1.49
ANG = EYE_X / 0.612   # the face angle of the eye (the masks' HEAD_R), negative = the character's right


def radial(ang):
    return Vector((math.sin(ang), -math.cos(ang), 0.0))


def on_head(ang, z, off):
    return radial(ang) * (HEAD_R + off) + Vector((0, 0, z))


@item("LoupeMonocle", "Brass Loupe Monocle", views=["front34", "front", "side", "close"],
      close=((-1.4, -3.4, 1.62), (-0.2, -0.62, 1.42), 70))
def build(M):
    piece("LoupeMonocle", "Head")
    rot = (HP, 0, ANG)          # a lathe's +Z points out of the face along the eye's radial
    base = on_head(ANG, EYE_Z, GAP)
    out = radial(ANG)
    gold, brass, old = M["gold"], M["brass"], M["brassold"]
    steel = M["steel"]
    lens = A.mat_flat("LoupeLens", (0.035, 0.05, 0.048), rough=0.03, coat=1.0, noise=6, bump=0.0, vary=0.02, wear=0.0, dirt=0.1)   # dark glass: a baked map cannot be see-through

    # the eye ring: a flat gold ring on the face with a knurled outer edge
    A.lathe("EyeRing", [(0.082, 0.0), (0.112, 0.0), (0.118, 0.006), (0.118, 0.016), (0.112, 0.022), (0.088, 0.024),
                        (0.082, 0.018), (0.082, 0.0)], tuple(base), gold, seg=48, rot=rot)
    for k in range(36):
        a = 2 * math.pi * k / 36
        A.box(f"Knurl{k}", (0.006, 0.008, 0.014), (0, 0, 0), old, bevel=0.0015)
        ob = A.PARTS[-1]
        loc_local = Vector((0.119 * math.cos(a), 0.119 * math.sin(a), 0.011))
        from mathutils import Euler
        R = Euler(rot).to_matrix()
        ob.location = R @ loc_local + base
        ob.rotation_euler = (R.to_4x4() @ Euler((0, 0, a)).to_matrix().to_4x4()).to_euler()
    # the barrel: steps out and flares toward the front, two turned bands
    A.lathe("Barrel", [(0.084, 0.02), (0.086, 0.05), (0.080, 0.06), (0.080, 0.085), (0.088, 0.095), (0.088, 0.105),
                       (0.082, 0.112), (0.084, 0.14), (0.096, 0.155), (0.100, 0.16)], tuple(base), brass, seg=40, rot=rot)
    A.lathe("BandA", [(0.085, 0.06), (0.091, 0.064), (0.091, 0.078), (0.085, 0.082)], tuple(base), old, seg=40, rot=rot)
    A.lathe("BandB", [(0.083, 0.118), (0.089, 0.122), (0.089, 0.132), (0.083, 0.136)], tuple(base), old, seg=40, rot=rot)
    # the front bezel, the lens and three screws
    A.lathe("Bezel", [(0.074, 0.15), (0.104, 0.155), (0.108, 0.165), (0.104, 0.178), (0.078, 0.18), (0.074, 0.172)],
            tuple(base), gold, seg=48, rot=rot)
    A.lathe("Lens", [(0.0, 0.176), (0.04, 0.174), (0.076, 0.168), (0.076, 0.162), (0.04, 0.164), (0.0, 0.166)],
            tuple(base), lens, seg=40, rot=rot)
    from mathutils import Euler
    R = Euler(rot).to_matrix()
    for k in range(3):
        a = 2 * math.pi * k / 3 + HP
        p = R @ Vector((0.093 * math.cos(a), 0.093 * math.sin(a), 0.181)) + base
        A.sphere(f"Screw{k}", 0.008, tuple(p), steel, scale=(1, 1, 1), seg=10, rings=6)
    # the hinge lug on the outer side (toward the character's right ear) and the chain loop
    side = R @ Vector((-1.0, 0.0, 0.0))
    side = Vector((side.x, side.y, 0)).normalized() if side.x < 0 else -Vector((side.x, side.y, 0)).normalized()
    lug = base + side * 0.125 + out * 0.03 + Vector((0, 0, -0.03))
    A.box("Lug", (0.03, 0.03, 0.03), tuple(lug), brass, bevel=0.006)
    loop = lug + side * 0.025 + Vector((0, 0, -0.012))
    A.torus("Loop", 0.016, 0.0045, tuple(loop), gold, rot=(0, HP, ANG))
    # the chain: down the cheek, following the face round toward the jaw (off the surface by 0.03)
    a0 = math.atan2(loop.x, -loop.y)
    pts = [tuple(loop + Vector((0, 0, -0.016)))]
    for t, dz in ((0.25, -0.10), (0.5, -0.20), (0.75, -0.28), (1.0, -0.33)):
        a = a0 + (math.radians(-52) - a0) * t
        pts.append(tuple(on_head(a, loop.z - 0.016 + dz, 0.03 - 0.004 * t)))
    A.chain("Chain", pts, 0.010, gold)
    # the fob: a little teardrop on a cap
    end = Vector(pts[-1])
    A.sphere("FobCap", 0.012, tuple(end + Vector((0, 0, -0.014))), gold, seg=12, rings=8)
    A.lathe("Fob", [(0.0, 0.0), (0.012, -0.006), (0.022, -0.022), (0.022, -0.036), (0.014, -0.05), (0.0, -0.056)],
            tuple(end + Vector((0, 0, -0.022))), brass, seg=20)
    return {"notes": "Anatomy mastery (Config.Anatomy.Mastery); never sold"}


if __name__ == "__main__":
    targets = [a for a in A.argv if not a.startswith("--") and (A.argv.index(a) == 0 or not A.argv[A.argv.index(a) - 1].startswith("--"))]
    keys = targets[0].split(",") if targets else ["LoupeMonocle"]
    for k in keys:
        try:
            A.run(k)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[monocle] {k} FAILED: {e}")
