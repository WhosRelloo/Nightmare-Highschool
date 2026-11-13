"""Where each head looks: face pitch (deg, + up) and the angle between the gaze and a target point on the other body.
usage: python gaze.py <clip> attacker|victim [t1 t2 ...]"""
import math
import sys

import numpy as np

sys.path.insert(0, "clips")
import pair  # noqa: E402
import rig  # noqa: E402

mod = __import__(sys.argv[1])
who = sys.argv[2]
other = "victim" if who == "attacker" else "attacker"
P = pair.Pair(mod.CLIP)
frames = P.bake(who)
oframes = P.bake(other) if not (other == "attacker" and mod.CLIP.get("external_attacker")) else None
times = [float(x) for x in sys.argv[3:]] or [round(t, 2) for t, _ in frames[::6]]
for t in times:
    i = min(range(len(frames)), key=lambda k: abs(frames[k][0] - t))
    F = rig.fk(frames[i][1], P.bodies[who].hrp)
    head = F["Head"]
    fwd = -head[:3, 2]
    pitch = math.degrees(math.asin(max(-1, min(1, fwd[1]))))
    if oframes:
        O = rig.fk(oframes[i][1], P.bodies[other].hrp)
        tgts = {"head": O["Head"][:3, 3], "chest": O["Torso"][:3, 3]}
    else:
        root = P.root_at(P.bodies[other], frames[i][0])
        T = P.bodies[other].hrp @ rig.cf(root["p"], root["R"])
        tgts = {"head": rig.xf(T, (0, 1.5, 0)), "chest": T[:3, 3]}
    eye = head[:3, 3]
    miss = {k: math.degrees(math.acos(max(-1, min(1, float(np.dot(fwd, (v - eye) / np.linalg.norm(v - eye))))))) for k, v in tgts.items()}
    print(f"t={frames[i][0]:.2f} pitch {pitch:+5.0f}  miss head {miss['head']:4.0f}  chest {miss['chest']:4.0f}")
