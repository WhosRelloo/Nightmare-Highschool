import math, sys, os
import numpy as np
from PIL import Image
sys.argv = [sys.argv[0], sys.argv[1]]
import gen_tex as G
OUT = sys.argv[1]
S = 128
def save(p, name, seed):
    a = G.wear(np.asarray(p.result(), np.float32), seed, 0.15)
    G.to_rgba(a, seed, 0.2).save(os.path.join(OUT, name + ".png"))
# candle
p = G.Pen(S, S); c = S/2
p.poly([(c-14, 56), (c+14, 56), (c+15, 112), (c-15, 112)])
p.d.ellipse(((c-26)*4, 106*4, (c+26)*4, 120*4), fill=255)          # holder
p.poly([(c-14, 56), (c-10, 70), (c-6, 60), (c-2, 74), (c+3, 58), (c+8, 68), (c+14, 56)], 255)  # drips
p.stroke([(c-11, 58), (c-12, 80)], 4); p.stroke([(c+9, 58), (c+10, 72)], 3)
p.stroke([(c, 56), (c, 46)], 2)
p.poly(G.bezier((c, 6), (c+18, 26), (c+10, 44), (c, 46), 30) + G.bezier((c, 46), (c-10, 44), (c-16, 26), (c, 6), 30))
p.poly(G.bezier((c, 20), (c+8, 30), (c+5, 40), (c, 41), 20) + G.bezier((c, 41), (c-5, 40), (c-7, 30), (c, 20), 20), 0)
save(p, "icon_candle", 51)
# blood drop with fang notch
p = G.Pen(S, S)
p.poly(G.bezier((c, 8), (c+10, 30), (c+40, 62), (c+34, 86), 40) + G.bezier((c+34, 86), (c+26, 122), (c-26, 122), (c-34, 86), 40) + G.bezier((c-34, 86), (c-40, 62), (c-10, 30), (c, 8), 40))
p.poly([(c-14, 70), (c-8, 96), (c-2, 70)], 0); p.poly([(c+2, 70), (c+8, 96), (c+14, 70)], 0)
save(p, "icon_drop", 52)
# quill nib
p = G.Pen(S, S)
p.poly([(c, 120), (c-30, 66), (c-24, 30), (c, 8), (c+24, 30), (c+30, 66)])
p.stroke([(c, 116), (c, 64)], 4, 4, 0); p.dot(c, 62, 7, 0)
p.stroke([(c-20, 36), (c+20, 36)], 3, 3, 0)
save(p, "icon_nib", 53)
# cross
p = G.Pen(S, S)
p.poly([(c-9, 8), (c+9, 8), (c+9, 38), (c+34, 38), (c+34, 56), (c+9, 56), (c+9, 120), (c-9, 120), (c-9, 56), (c-34, 56), (c-34, 38), (c-9, 38)])
p.dot(c, 47, 15); p.dot(c, 47, 9, 0); p.dot(c, 47, 4)
for (x, y) in ((c, 6), (c+36, 47), (c-36, 47), (c, 122)): p.poly(G.diamond(x, y, 7))
save(p, "icon_cross", 54)
print("ok")
