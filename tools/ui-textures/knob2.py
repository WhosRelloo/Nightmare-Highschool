import sys, os, math
import numpy as np
OUT = sys.argv[1]
import importlib.util
spec = importlib.util.spec_from_file_location("hq", "gen_hq.py")
# load only the helpers (avoid re-running the whole pipeline): exec up to the re-render section
src = open("gen_hq.py", encoding="utf-8").read().split("# ---------------------------------------------------------------- re-render")[0]
sys.argv = [sys.argv[0], OUT]
g = {"__name__": "hq"}
exec(src, g)
G = g["G"]
p = G.Pen(64, 64); c = 32
p.poly(G.diamond(c, c, 24)); p.poly(G.diamond(c, c, 15), 0); p.poly(G.diamond(c, c, 9))
a = np.asarray(p.result(), np.float32)
g["metal"](a, 31, 0.2, None, 0.5, True, 0.3, 2.3).save(os.path.join(OUT, "knob.png"))
# solid pip (filled gem-cut diamond) for stat pips
q = G.Pen(64, 64); q.poly(G.diamond(c, c, 24))
g["metal"](np.asarray(q.result(), np.float32), 33, 0.2, None, 0.5, True, 0.3, 2.3).save(os.path.join(OUT, "pip.png"))
print("ok")
