"""Before / after renders of solved hair tucks (review sheets).

E:/Blender/blender.exe -b --factory-startup -P acc_tuckrender.py -- <out folder> <Model.Lead:Hair>[,...] | --sample N
"""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
import acc_hairtuck as T

OUT = argv[0]
items = {f"{m}.{ps[0]}": (m, tuple(ps)) for m, ps in T.game_items()}
if argv[1] == "--sample":
    n = int(argv[2])
    ok = []
    for f in sorted(os.listdir(f"{T.ROOT}/tuck/parts")):
        d = json.load(open(f"{T.ROOT}/tuck/parts/{f}"))
        if d.get("ok") and d.get("bones"):
            ok.append(f[:-5])
    random.seed(7)
    pairs = [p.split("__") for p in random.sample(ok, min(n, len(ok)))]
else:
    pairs = [p.split(":") for p in argv[1].split(",")]
want = {}
for key, h in pairs:
    want.setdefault(items[key], []).append(h)
T.RENDER = OUT
T.render(want)
print("TUCKRENDER done", sum(len(v) for v in want.values()))
