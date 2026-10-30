"""Corner + tiled-edge ornate frame. Display units, rendered at K px per unit."""
import math, sys, os
import numpy as np
from PIL import Image
sys.argv = [sys.argv[0], sys.argv[1]]
import gen_tex as G
OUT = sys.argv[1]
K = 4
C = 56   # corner size (display px)
E = 20   # edge strip thickness
T = 16   # tile length
O_Y, I_Y = 4, 14   # outer rail, inner rail

class KPen(G.Pen):
    def __init__(self, w, h):
        super().__init__(w * K, h * K)
    def dot(self, x, y, r, v=255): super().dot(x * K, y * K, r * K, v)
    def poly(self, pts, v=255): super().poly([(x * K, y * K) for x, y in pts], v)
    def stroke(self, pts, w0, w1=None, v=255):
        if w1 is None: w1 = w0
        dense = []
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            n = max(2, int(math.hypot(bx - ax, by - ay) * 3))
            for k in range(n):
                t = k / n
                dense.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        dense.append(pts[-1])
        N = len(dense)
        for i, (x, y) in enumerate(dense):
            t = i / max(N - 1, 1)
            self.dot(x, y, (w0 + (w1 - w0) * t) / 2, v)

def arch(p, x0, x1, ybase, ytop, w):
    mx = (x0 + x1) / 2
    p.stroke(G.bezier((x0, ybase), (x0, ybase - (ybase-ytop)*0.55), (mx - 1, ytop + 1.5), (mx, ytop), 20), w)
    p.stroke(G.bezier((x1, ybase), (x1, ybase - (ybase-ytop)*0.55), (mx + 1, ytop + 1.5), (mx, ytop), 20), w)

def edge_tile():
    p = KPen(T, E)
    p.stroke([(-1, O_Y), (T + 1, O_Y)], 2.2)
    p.stroke([(-1, I_Y), (T + 1, I_Y)], 1.1)
    # gothic arcade between rails (iron-gate arches)
    arch(p, 1, T - 1, I_Y, O_Y + 2.2, 0.8)
    p.stroke([(T / 2, O_Y + 2.5), (T / 2, O_Y + 4.5)], 0.7)   # keystone
    p.stroke([(0, O_Y), (0, I_Y)], 0.9)                       # pillar on tile seam
    # outward thorn on each tile
    p.poly([(T/2 - 1.6, O_Y - 0.5), (T/2, 0.2), (T/2 + 1.6, O_Y - 0.5)])
    # wax drip / bead hanging under inner rail
    p.dot(0, I_Y + 2.4, 1.0)
    p.stroke([(T/2, I_Y), (T/2, I_Y + 2.6)], 0.7)
    p.dot(T/2, I_Y + 3.2, 0.75)
    return p.result()

def corner():
    p = KPen(C, C)
    # rails continuing into corner
    p.stroke([(O_Y, O_Y), (C + 1, O_Y)], 2.2); p.stroke([(O_Y, O_Y), (O_Y, C + 1)], 2.2)
    p.stroke([(I_Y, I_Y), (C + 1, I_Y)], 1.1); p.stroke([(I_Y, I_Y), (I_Y, C + 1)], 1.1)
    # filled spandrel between rails near the corner (solid iron plate with pierced quatrefoil)
    p.poly([(O_Y, O_Y), (I_Y + 8, O_Y), (I_Y, I_Y), (O_Y, I_Y + 8)])
    for (dx, dy) in ((0, -2), (2, 0), (0, 2), (-2, 0)):
        p.dot(9 + dx * 0.8, 9 + dy * 0.8, 1.2, 0)
    # corner boss
    p.poly(G.diamond(O_Y, O_Y, 5.5)); p.dot(O_Y, O_Y, 1.5, 0)
    # outward corner thorn
    p.poly([(O_Y - 1.5, O_Y - 3), (-0.5, -0.5), (O_Y - 3, O_Y - 1.5)])
    for s in (0, 1):
        def P(x, y): return (y, x) if s else (x, y)
        # main C-scroll hugging the inner rail
        a0 = math.pi
        sp = G.spiral(I_Y + 9, 33, 8, 1.6, math.pi * 0.95, -math.pi * 1.75)
        p.stroke([P(x, y) for x, y in G.bezier((I_Y, 52), (I_Y + 1, 44), (I_Y + 2, 40), (I_Y + 1.2, 33))], 1.2, 1.6)
        p.stroke([P(x, y) for x, y in sp], 1.9, 0.8)
        ex, ey = sp[-1]; p.dot(*P(ex, ey), 1.3)
        # leaf sprouting off the scroll
        p.poly([P(x, y) for x, y in G.leaf((I_Y + 10, 41), math.radians(55), 9, 2.2)])
        p.poly([P(x, y) for x, y in G.leaf((I_Y + 3, 46), math.radians(20), 7, 1.6)])
        # small back-curl near the corner
        sp2 = G.spiral(I_Y + 5, I_Y + 12, 3.6, 0.8, -math.pi / 2, math.pi * 1.5)
        p.stroke([P(x, y) for x, y in sp2], 1.1, 0.6)
        # beads along the rail
        for t in (24, 28):
            p.dot(*P(I_Y + 2.4, t), 0.7)
        # arches continue into the corner on each side
        for x0 in range(C - T * 2, C, T):
            if x0 > I_Y + 8:
                q0, q1 = P(x0 + 1, I_Y), P(x0 + T - 1, I_Y)
        # thorns on outer rail
        for t in (24, 40):
            q = [P(t - 1.6, O_Y - 0.5), P(t, 0.2), P(t + 1.6, O_Y - 0.5)]
            p.poly(q)
    # arcade inside the corner rails (outside the spandrel) so it meets the tiled edge
    for x0 in (24, 40):
        arch(p, x0, x0 + T - 2, I_Y, O_Y + 2.2, 0.8)
        p.stroke([(x0 - 1, O_Y), (x0 - 1, I_Y)], 0.9)
        pts = []
    for y0 in (24, 40):
        tmp = KPen(C, C)
    # vertical arches (transpose of horizontal) drawn by transposed coords
    for y0 in (24, 40):
        mx = y0 + (T - 2) / 2
        p.stroke([(y, x) for x, y in G.bezier((y0, I_Y), (y0, I_Y - 4.4), (mx - 1, O_Y + 3.7), (mx, O_Y + 2.2), 20)], 0.8)
        p.stroke([(y, x) for x, y in G.bezier((y0 + T - 2, I_Y), (y0 + T - 2, I_Y - 4.4), (mx + 1, O_Y + 3.7), (mx, O_Y + 2.2), 20)], 0.8)
        p.stroke([(O_Y, y0 - 1), (I_Y, y0 - 1)], 0.9)
    # diagonal spear into the panel
    p.stroke([(I_Y + 1, I_Y + 1), (30, 30)], 2.0, 0.9)
    p.poly(G.diamond(32, 32, 3.2))
    p.poly(G.leaf((24, 24), math.radians(15), 9, 2.0))
    p.poly(G.leaf((24, 24), math.radians(75), 9, 2.0))
    return p.result()

def finish(L, name, seed, ws=0.45):
    a = G.wear(np.asarray(L, np.float32), seed, ws)
    G.to_rgba(a, seed, 0.28).save(os.path.join(OUT, name + ".png"))

c = corner()
finish(c, "corner_tl", 41)
finish(c.transpose(Image.FLIP_LEFT_RIGHT), "corner_tr", 42)
finish(c.transpose(Image.FLIP_TOP_BOTTOM), "corner_bl", 43)
finish(c.transpose(Image.ROTATE_180), "corner_br", 44)
e = edge_tile()
finish(e, "edge_t", 45, 0.35)
finish(e.transpose(Image.FLIP_TOP_BOTTOM), "edge_b", 46, 0.35)
finish(e.transpose(Image.TRANSPOSE), "edge_l", 47, 0.35)
finish(e.transpose(Image.TRANSPOSE).transpose(Image.FLIP_LEFT_RIGHT), "edge_r", 48, 0.35)

# composite preview of a 300x200 panel at display scale and 2x zoom
W, H = 300, 180
pane = Image.new("RGBA", (W * K, H * K), (14, 12, 18, 255))
bg = Image.open(os.path.join(OUT, "panel_bg.png")).convert("RGB").resize((W*K, H*K))
bgarr = (np.asarray(bg, np.float32) * np.array([40, 36, 48]) / 255).astype(np.uint8)
pane = Image.fromarray(bgarr).convert("RGBA")
tint = np.array([200, 196, 210, 255]) / 255
def put(name, x, y, w=None, h=None, tile=False):
    im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    arr = (np.asarray(im, np.float32) * tint).astype(np.uint8); im = Image.fromarray(arr)
    if tile:
        for xx in range(0, w, im.width):
            for yy in range(0, h, im.height):
                pane.alpha_composite(im.crop((0, 0, min(im.width, w - xx), min(im.height, h - yy))), (x + xx, y + yy))
    else:
        pane.alpha_composite(im, (x, y))
put("edge_t", C*K, 0, (W - 2*C)*K, E*K, True)
put("edge_b", C*K, (H - E)*K, (W - 2*C)*K, E*K, True)
put("edge_l", 0, C*K, E*K, (H - 2*C)*K, True)
put("edge_r", (W - E)*K, C*K, E*K, (H - 2*C)*K, True)
put("corner_tl", 0, 0); put("corner_tr", (W - C)*K, 0); put("corner_bl", 0, (H - C)*K); put("corner_br", (W-C)*K, (H-C)*K)
pane.resize((W * 2, H * 2), Image.LANCZOS).save(os.path.join(OUT, "_panel2x.png"))
pane.resize((W, H), Image.LANCZOS).save(os.path.join(OUT, "_panel1x.png"))
print("ok")
