"""NPC posture (2.3.0): does leaning the whole upper body (torso, head and hair) about the hip line push any rigged hair
into the legs?
E:/Blender/blender.exe -b --factory-startup -P hip_pitch_check.py
Every barber hair as worn (nh_acc.real_hair), rotated about the hip line (0, 0, -1); the legs are the R6 leg boxes
widened to the deepest body (Curvy, 1.23 deep). Reports, per angle, the deepest hair vertex inside the legs against the
same hair at rest. Result (2026-11-13): 0.0000 at every angle from -12 to +12 degrees."""
import bpy, math, sys, json
sys.path.insert(0, "E:/Nightmare-Highschool/art/characters/accessories")
from mathutils import Vector, Matrix
import nh_acc as A

HALF_D = 1.23 / 2


def depth_in_torso(p):
    # here: the legs (R6 leg boxes under the hip line, the deepest body's depth)
    if abs(p.x) <= 1.0 and abs(p.y) <= HALF_D and -3.0 <= p.z <= -1.0:
        return min(1.0 - abs(p.x), HALF_D - abs(p.y), p.z + 3.0, -1.0 - p.z)
    return 0.0


bpy.ops.wm.read_factory_settings(use_empty=True)
angles = [-12, -10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12]
worst = {a: (0.0, None) for a in angles}
rows = {}
for h in sorted(A._hair_attach()):
    ob = A.real_hair(h)
    if ob is None:
        continue
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    bpy.data.objects.remove(ob)
    pivot = Vector((0, 0, -1.0))
    base = max(depth_in_torso(p) for p in pts)
    row = {}
    for a in angles:
        R = Matrix.Rotation(math.radians(a), 3, "X")
        d = max(depth_in_torso(pivot + R @ (p - pivot)) for p in pts)
        extra = max(0.0, d - base)
        row[a] = round(extra, 4)
        if extra > worst[a][0]:
            worst[a] = (extra, h)
    rows[h] = {"rest": round(base, 4), "extra": row}
print("HIPCHECK hairs", len(rows))
for a in angles:
    print("HIPCHECK angle %+3d  worst extra depth %.4f  (%s)" % (a, worst[a][0], worst[a][1]))
json.dump(rows, open("E:/Nightmare-Highschool/tools/npc-builds-230/hip_pitch_check.json", "w"), indent=1)
