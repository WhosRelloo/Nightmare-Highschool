"""Bake + check one fist clip with the racial-grips generator (pair.py), into tools/fist-moves/out.
The keys' limb slides ("_o", fist_poses) are split off first and baked to out/<name>[Victim].offs.json for pack.py.
usage: python run.py fist_shove        (clips/<name>.py defines CLIP)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import fist_poses  # noqa: E402  (sets sys.path: our clips first, then racial-grips)
import pair  # noqa: E402

if __name__ == "__main__":
    name = sys.argv[1]
    mod = __import__(name)
    clip = mod.CLIP
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    for who, suffix in (("attacker", ""), ("victim", "Victim")):
        keys, offs = fist_poses.split(clip[who])
        clip[who] = keys
        if any(any(abs(c) > 1e-6 for v in o.values() for c in v) for _, o in offs):
            with open(os.path.join(out_dir, clip["name"] + suffix + ".offs.json"), "w") as fh:
                json.dump(fist_poses.bake_offs(offs, clip["length"]), fh)
    res = pair.build(name, out_dir)
    for who, v in res.items():
        print(who, "exit", v["exit"], "failing", v["failing"])
        for l in (v["lint"] or [])[:8]:
            print("  lint:", l)
