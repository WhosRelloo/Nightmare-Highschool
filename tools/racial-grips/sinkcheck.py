"""Which parts go below the floor, and how deep (worst per part)."""
import sys
sys.path.insert(0, 'clips')
import pair, rig
mod = __import__(sys.argv[1])
P = pair.Pair(mod.CLIP)
for who in sys.argv[2:] or ['attacker', 'victim']:
    fr = P.bake(who)
    worst = {}
    for t, pose in fr:
        for pn, M in rig.fk(pose, P.bodies[who].hrp).items():
            low = min(c[1] for c in pair._corners(M, rig.SIZE[pn]))
            if low < -3.1 and (pn not in worst or low < worst[pn][1]):
                worst[pn] = (round(t, 2), round(low, 2))
    print(who, worst)
