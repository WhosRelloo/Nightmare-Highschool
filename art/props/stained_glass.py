"""The window kit's stained glass (props batch 23): original designs in crimson, gold and deep blue (the school crest's
candle, crescent moon, key and the Midnight Bell; no copied church glass, no figures, no gore), painted at 2048 from the
same layouts the stone tracery is modelled from (window_shapes.py), so every light lines up with its bars.

Each design is a list of glass pieces (polygons in studs, drawn in order). The leads are traced from the boundaries
between pieces, so they always match. Then: per-piece colour jitter, streaky antique glass, seeds, darkening toward the
leads, grisaille line work, a rounded lead profile with a highlight.

Writes to art/props/textures/:
  <Prop>Stained_canvas.png    the colour map (front-projected onto the Stained piece)
  <Prop>Stained_emissive.png  the emissive mask (glass bright, lead black) for the SurfaceAppearance
  WindowRoom_canvas.png       the warm lit room behind clear glass (shared by every window), and WindowRoom_emissive.png

  python art/props/stained_glass.py [TraceryWindow RoseWindow StainedLancet Room]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import window_shapes as WS  # noqa: E402

OUT = os.path.join(HERE, "textures")
MAXPX = 2048

# jewel glass (sRGB 0..1)
RUBY = (0.66, 0.05, 0.09)
CRIMSON = (0.45, 0.03, 0.07)
GOLD = (0.96, 0.66, 0.15)
PALEGOLD = (1.0, 0.86, 0.48)
AMBER = (0.9, 0.42, 0.07)
BLUE = (0.06, 0.12, 0.44)
MIDBLUE = (0.12, 0.26, 0.64)
PALEBLUE = (0.5, 0.64, 0.86)
NIGHT = (0.04, 0.06, 0.24)
WHITE = (0.9, 0.9, 0.82)
IVORY = (0.93, 0.86, 0.68)
VIOLET = (0.26, 0.1, 0.4)


# ------------------------------------------------------------------ noise

def fbm(w, h, sx, sz, octaves=5, seed=0):
    """Value-noise fbm (0..1): upscaled random grids, sx x sz cells at the coarsest octave."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cw, ch = max(2, int(sx * 2 ** o)), max(2, int(sz * 2 ** o))
        g = rng.random((ch, cw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.55
    return out / tot


def blur(a, r):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


# ------------------------------------------------------------------ the painter

class Panel:
    def __init__(self, outline, seed=1):
        self.outline = outline
        x0, x1, z0, z1 = WS.bounds(outline)
        self.x0, self.x1, self.z0, self.z1 = x0, x1, z0, z1
        sw, sh = x1 - x0, z1 - z0
        if sw >= sh:
            self.W, self.H = MAXPX, int(round(MAXPX * sh / sw / 4)) * 4
        else:
            self.W, self.H = int(round(MAXPX * sw / sh / 4)) * 4, MAXPX
        self.ppu = self.W / sw
        self.pieces = []            # (poly, colour)
        self.lines = []             # grisaille: (pts, width studs, strength)
        self.rng = np.random.default_rng(seed)

    def px(self, p):
        return ((p[0] - self.x0) / (self.x1 - self.x0) * self.W, (self.z1 - p[1]) / (self.z1 - self.z0) * self.H)

    def add(self, poly, col):
        if len(poly) >= 3:
            self.pieces.append((poly, col))

    def ring(self, cx, cz, r0, r1, n, cols, a0=0.0):
        """An annulus of n glass segments, colours cycling."""
        for k in range(n):
            a, b = a0 + k / n * 2 * math.pi, a0 + (k + 1) / n * 2 * math.pi
            m = 4
            outer = [(cx + math.cos(a + (b - a) * i / m) * r1, cz + math.sin(a + (b - a) * i / m) * r1) for i in range(m + 1)]
            inner = [(cx + math.cos(b - (b - a) * i / m) * r0, cz + math.sin(b - (b - a) * i / m) * r0) for i in range(m + 1)]
            self.add(outer + inner, cols[k % len(cols)])

    def border(self, outline, width, cols, step=0.32):
        o = WS.resample(WS.ccw(outline), step)
        i = WS.offset(o, -width)
        for k in range(len(o)):
            j = (k + 1) % len(o)
            self.add([o[k], o[j], i[j], i[k]], cols[k % len(cols)])

    def diamonds(self, region, step, cols, angle=62, jewel=None):
        """Diamond quarries clipped to a convex region; jewel = (colour, size) puts a small square at every crossing."""
        a = math.radians(angle)
        u1, u2 = (math.cos(a), math.sin(a)), (-math.cos(a), math.sin(a))
        n1, n2 = (-u1[1], u1[0]), (-u2[1], u2[0])
        det = n1[0] * n2[1] - n1[1] * n2[0]
        x0, x1, z0, z1 = WS.bounds(region)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        span = int(math.hypot(x1 - x0, z1 - z0) / step) + 3

        def at(s, t):
            return (cx + (s * step * n2[1] - t * step * n1[1]) / det, cz + (t * step * n1[0] - s * step * n2[0]) / det)
        reg = WS.hull(region)
        for i in range(-span, span):
            for j in range(-span, span):
                cell = WS.clip_convex(WS.ccw([at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)]), reg)
                if len(cell) >= 3 and abs(WS.area(cell)) > 1e-4:
                    self.add(cell, cols[(i + 2 * j) % len(cols)])
        if jewel:
            col, s = jewel
            for i in range(-span, span):
                for j in range(-span, span):
                    c = at(i, j)
                    if WS.inside(c, reg) and all(WS.inside(q, reg) for q in ((c[0] + s * 1.5, c[1]), (c[0] - s * 1.5, c[1]), (c[0], c[1] + s * 1.5),
                                                                           (c[0], c[1] - s * 1.5))):
                        self.add([(c[0], c[1] - s), (c[0] + s, c[1]), (c[0], c[1] + s), (c[0] - s, c[1])], col)

    def star(self, cx, cz, r, col, points=8, inner=0.45, a0=math.pi / 2):
        pts = []
        for k in range(points * 2):
            rr = r if k % 2 == 0 else r * inner
            a = a0 + k * math.pi / points
            pts.append((cx + math.cos(a) * rr, cz + math.sin(a) * rr))
        self.add(pts, col)

    def line(self, pts, w=0.02, s=0.7):
        self.lines.append((pts, w, s))

    # -------------------------------------------------------------- render
    def render(self):
        W, H = self.W, self.H
        idim = Image.new("I", (W, H), 0)
        d = ImageDraw.Draw(idim)
        cols = [(0.0, 0.0, 0.0)]
        for k, (poly, col) in enumerate(self.pieces):
            d.polygon([self.px(p) for p in poly], fill=k + 1)
            cols.append(col)
        ids = np.asarray(idim, np.int32)
        outside = np.asarray(self._mask(self.outline), np.float32) < 0.5
        ids = np.where(outside, 0, ids)
        # per-piece colour jitter (brightness and a little hue), streaky antique glass, seeds
        n = len(cols)
        jit = self.rng.uniform(0.86, 1.14, n).astype(np.float32)
        hue = self.rng.uniform(-0.05, 0.05, (n, 3)).astype(np.float32)
        lut = np.clip(np.array(cols, np.float32) * jit[:, None] + hue * np.array(cols, np.float32), 0, 1)
        img = lut[ids]
        streak = fbm(W, H, W / 160, H / 900, seed=int(self.rng.integers(1e6)))
        fine = fbm(W, H, W / 30, H / 30, octaves=4, seed=int(self.rng.integers(1e6)))
        phase = self.rng.uniform(0, 1, n).astype(np.float32)[ids]
        st = 0.82 + 0.36 * ((streak + phase) % 1.0 * 0.6 + streak * 0.4)
        img *= (st * (0.92 + 0.16 * fine))[..., None]
        seeds = (self.rng.random((H, W)) > 0.9993).astype(np.float32)
        seeds = blur(seeds, 1.2) * 6
        img += seeds[..., None] * 0.25
        # the leads: where neighbouring pixels belong to different pieces
        e = np.zeros((H, W), np.float32)
        e[:, 1:] = np.maximum(e[:, 1:], (ids[:, 1:] != ids[:, :-1]))
        e[1:, :] = np.maximum(e[1:, :], (ids[1:, :] != ids[:-1, :]))
        edge_outline = np.asarray(self._mask(self.outline, line=True), np.float32)
        e = np.maximum(e, edge_outline)
        lw = 0.055 * self.ppu                     # lead width in pixels
        prof = blur(e, lw * 0.42)
        prof = prof / max(prof.max(), 1e-6)
        lead = np.clip((prof - 0.08) / 0.12, 0, 1)
        lead = np.maximum(lead, outside.astype(np.float32))
        # glass darkens toward the leads (the painted matting round each piece), and gets a soft inner light
        near = blur(e, lw * 1.6)
        near = near / max(near.max(), 1e-6)
        img *= (1.0 - 0.38 * np.clip(near * 1.6, 0, 1))[..., None]
        # grisaille line work
        if self.lines:
            pm = Image.new("L", (W * 2, H * 2), 0)
            pd = ImageDraw.Draw(pm)
            for pts, w, s in self.lines:
                q = [(x * 2, y * 2) for x, y in (self.px(p) for p in pts)]
                pd.line(q, fill=int(255 * s), width=max(1, int(w * self.ppu * 2)), joint="curve")
            paint = np.asarray(pm.resize((W, H), Image.LANCZOS), np.float32) / 255
            img *= (1.0 - 0.85 * paint)[..., None]
            img = img * (1 - paint[..., None] * 0.15) + paint[..., None] * 0.15 * np.array((0.06, 0.04, 0.02), np.float32)
        # the lead: dark grey with a rounded highlight along its middle and the odd solder joint
        hi = np.clip((prof - 0.45) / 0.5, 0, 1) ** 2
        lc = np.array((0.055, 0.056, 0.062), np.float32) + hi[..., None] * np.array((0.13, 0.13, 0.14), np.float32)
        img = img * (1 - lead[..., None]) + lc * lead[..., None]
        img = np.clip(img, 0, 1)
        glow = np.clip(img.max(axis=2) * 0.85 + img.mean(axis=2) * 0.15, 0, 1) * (1 - lead)
        glow = np.clip(glow ** 0.8 * 1.05, 0, 1)
        return img, glow

    def _mask(self, poly, line=False):
        m = Image.new("L", (self.W, self.H), 0)
        d = ImageDraw.Draw(m)
        pts = [self.px(p) for p in poly]
        if line:
            d.line(pts + [pts[0]], fill=255, width=2)
        else:
            d.polygon(pts, fill=255)
        return m


def save(name, img, glow):
    Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_canvas.png"))
    Image.fromarray((glow * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_emissive.png"))
    print(f"[glass] {name}: {img.shape[1]}x{img.shape[0]}")


# ------------------------------------------------------------------ motifs

def candle(P, cx, z0, w, h, flame_h, halo=True):
    """A tall ivory candle in a gold holder, a gold flame with a white heart, a segmented pale-gold halo."""
    P.add([(cx - w * 1.4, z0), (cx + w * 1.4, z0), (cx + w * 0.9, z0 + 0.12), (cx - w * 0.9, z0 + 0.12)], GOLD)
    P.add([(cx - w * 0.9, z0 + 0.12), (cx + w * 0.9, z0 + 0.12), (cx + w * 1.15, z0 + 0.24), (cx - w * 1.15, z0 + 0.24)], AMBER)
    zb, zt = z0 + 0.24, z0 + 0.24 + h
    P.add([(cx - w / 2, zb), (cx, zb), (cx, zt), (cx - w / 2, zt - 0.04)], IVORY)
    P.add([(cx, zb), (cx + w / 2, zb), (cx + w / 2, zt - 0.06), (cx, zt)], WHITE)
    P.add([(cx + w / 2, zt - 0.4), (cx + w / 2 + 0.05, zt - 0.5), (cx + w / 2 + 0.03, zt - 0.08), (cx + w / 2, zt - 0.06)], IVORY)  # a drip
    fz = zt + 0.06
    if halo:
        P.ring(cx, fz + flame_h * 0.45, flame_h * 0.64, flame_h * 0.84, 12, [PALEGOLD, GOLD])
    fl = [(cx, fz)] + [(cx + flame_h * 0.24 * math.sin(math.pi * (i / 16)) ** 0.8, fz + flame_h * i / 16 * 0.95) for i in range(17)] + \
         [(cx, fz + flame_h)] + [(cx - flame_h * 0.24 * math.sin(math.pi * (i / 16)) ** 0.8, fz + flame_h * i / 16 * 0.95) for i in range(16, -1, -1)]
    P.add(fl, AMBER)
    core = [(cx, fz + flame_h * 0.08)] + [(cx + flame_h * 0.11 * math.sin(math.pi * (i / 10)), fz + flame_h * (0.1 + 0.55 * i / 10)) for i in range(11)] + \
           [(cx - flame_h * 0.11 * math.sin(math.pi * (i / 10)), fz + flame_h * (0.1 + 0.55 * i / 10)) for i in range(10, -1, -1)]
    P.add(core, PALEGOLD)
    P.line([(cx, zt), (cx, fz + 0.04)], 0.02, 0.9)
    for k in range(3):
        P.line([(cx - w / 2 + 0.05, zb + 0.2 + k * 0.25), (cx - w / 2 + 0.09, zb + 0.3 + k * 0.25)], 0.012, 0.35)


def moon(P, cx, cz, r, tilt=0.6, stars=()):
    P.add(WS.crescent(cx, cz, r, shift=0.36, tilt=tilt), WHITE)
    for (x, z, s) in stars:
        P.star(x, z, s, PALEGOLD, points=4, inner=0.35)


def key(P, cx, cz, s, col=GOLD):
    """An upright key: a quatrefoil bow, a shaft, a two-step bit."""
    P.ring(cx, cz + 0.55 * s, 0.17 * s, 0.3 * s, 8, [col, PALEGOLD])
    P.add([(cx - 0.05 * s, cz - 0.75 * s), (cx + 0.05 * s, cz - 0.75 * s), (cx + 0.05 * s, cz + 0.26 * s), (cx - 0.05 * s, cz + 0.26 * s)], col)
    P.add([(cx + 0.05 * s, cz - 0.75 * s), (cx + 0.26 * s, cz - 0.75 * s), (cx + 0.26 * s, cz - 0.6 * s), (cx + 0.05 * s, cz - 0.6 * s)], PALEGOLD)
    P.add([(cx + 0.05 * s, cz - 0.52 * s), (cx + 0.2 * s, cz - 0.52 * s), (cx + 0.2 * s, cz - 0.4 * s), (cx + 0.05 * s, cz - 0.4 * s)], col)
    P.add([(cx - 0.1 * s, cz + 0.18 * s), (cx + 0.1 * s, cz + 0.18 * s), (cx + 0.1 * s, cz + 0.26 * s), (cx - 0.1 * s, cz + 0.26 * s)], AMBER)


def bell(P, cx, cz, s):
    """The Midnight Bell: a flared gold bell with a crown loop and a clapper."""
    prof = [(0.12, 0.42), (0.16, 0.36), (0.18, 0.2), (0.2, 0.02), (0.26, -0.16), (0.36, -0.3), (0.38, -0.36)]
    right = [(cx + x * s, cz + z * s) for x, z in prof]
    left = [(cx - x * s, cz + z * s) for x, z in reversed(prof)]
    P.add(right + left, GOLD)
    P.add([(cx - 0.38 * s, cz - 0.36 * s), (cx + 0.38 * s, cz - 0.36 * s), (cx + 0.4 * s, cz - 0.44 * s), (cx - 0.4 * s, cz - 0.44 * s)], AMBER)
    P.ring(cx, cz + 0.5 * s, 0.05 * s, 0.1 * s, 6, [PALEGOLD])
    P.add(WS.circle(cx, cz - 0.5 * s, 0.07 * s, 12), PALEGOLD)
    P.line([(cx - 0.12 * s, cz + 0.3 * s), (cx - 0.18 * s, cz - 0.2 * s)], 0.014, 0.45)
    P.line([(cx - 0.26 * s, cz - 0.26 * s), (cx + 0.26 * s, cz - 0.26 * s)], 0.014, 0.5)


# ------------------------------------------------------------------ the windows

def tracery_window():
    T = WS.Tracery
    P = Panel(WS.offset(WS.ccw(T.outline(24)), 0.05), seed=231)
    # background behind everything (the stone covers it): deep blue in small pieces so no area is one huge sheet
    P.diamonds(P.outline, 0.42, [NIGHT, BLUE])
    for k in range(4):
        L = WS.offset(WS.ccw(T.light(k, 14)), -T.BAR / 2 + 0.02)
        P.border(L, 0.2, [RUBY, GOLD, CRIMSON, GOLD], step=0.26)
        field = WS.offset(L, -0.2)
        P.diamonds(field, 0.3, [BLUE, MIDBLUE, BLUE, NIGHT], jewel=(GOLD, 0.075))
        cx = T.LIGHTS[k]
        # quatrefoil roundels low and high, the main medallion between
        for z in (1.75, 6.2):
            P.add(WS.circle(cx, z, 0.36, 32), CRIMSON)
            P.add(WS.foil_outline(cx, z, 0.3, 4, n=48, a0=math.pi / 4), GOLD)
            P.add(WS.circle(cx, z, 0.09, 12), RUBY)
        mz = 3.95
        P.ring(cx, mz, 0.42, 0.56, 14, [RUBY, CRIMSON])
        P.add(WS.circle(cx, mz, 0.42, 40), MIDBLUE)
        if k == 0:
            candle(P, cx, mz - 0.4, 0.16, 0.44, 0.3, halo=False)
        elif k == 1:
            moon(P, cx - 0.03, mz + 0.02, 0.32, tilt=0.5, stars=[(cx + 0.27, mz + 0.2, 0.07), (cx + 0.2, mz - 0.27, 0.06)])
        elif k == 2:
            key(P, cx, mz + 0.02, 0.62)
        else:
            bell(P, cx, mz + 0.03, 0.82)
        # the head: a gold trefoil on ruby
        hz = T.ZS + 0.42
        P.add(WS.foil_outline(cx, hz, 0.3, 3, n=36), GOLD)
        P.add(WS.circle(cx, hz, 0.08, 10), RUBY)
    # the head circle: blue round, crimson sexfoil petals, a gold sun holding a blue crescent
    hx, hz, hr = T.HEAD
    P.ring(hx, hz, hr - 0.2, hr, 18, [BLUE, MIDBLUE])
    P.add(WS.foil_outline(hx, hz, hr - 0.18, 6, n=96), RUBY)
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        P.add(WS.circle(hx + math.cos(a) * 0.55, hz + math.sin(a) * 0.55, 0.14, 16), GOLD)
    P.star(hx, hz, 0.42, GOLD, points=12, inner=0.68)
    P.add(WS.circle(hx, hz, 0.25, 32), PALEGOLD)
    moon(P, hx, hz, 0.18, tilt=0.6)
    for (sx, sz, r) in T.SPANDREL:
        P.add(WS.circle(sx, sz, r, 28), CRIMSON)
        P.add(WS.foil_outline(sx, sz, r - 0.08, 3, n=36), GOLD)
        P.add(WS.circle(sx, sz, 0.07, 10), RUBY)
    # the spaces between the sub-arches and the main arch: violet and blue
    save("TraceryWindowStained", *P.render())


def rose_window():
    R = WS.Rose
    out = WS.circle(0, R.CZ, R.R + 0.05, 96)
    P = Panel(out, seed=232)
    # the ground: night blue cut in rings of small pieces
    for k, (r0, r1, n, cols) in enumerate(((R.SPOKE_R, R.R + 0.06, 48, [NIGHT, BLUE]), (R.HUB, R.SPOKE_R, 24, [BLUE]))):
        P.ring(0, R.CZ, r0, r1, n, cols, a0=math.pi / 2)
    ang = R.angles()
    dA = 2 * math.pi / R.N
    for k, a0 in enumerate(ang):
        a1 = a0 + dA
        am = (a0 + a1) / 2
        head = R.petal_head(k, 12)
        wedge = [(math.cos(a0) * R.HUB, R.CZ + math.sin(a0) * R.HUB)] + head + [(math.cos(a1) * R.HUB, R.CZ + math.sin(a1) * R.HUB)]
        wedge = WS.ccw(WS.offset(WS.ccw(wedge), -R.BAR / 2 + 0.02))
        base = RUBY if k % 2 == 0 else MIDBLUE
        alt = CRIMSON if k % 2 == 0 else BLUE
        P.add(wedge, alt)
        # concentric bands across the petal, split along its axis
        bands = ((R.HUB, 1.4, GOLD if k % 2 == 0 else PALEGOLD), (1.4, 2.05, base), (2.05, 2.62, alt), (2.62, 3.7, base))
        for r0, r1, col in bands:
            for side in (0, 1):
                aa, ab = (a0, am) if side == 0 else (am, a1)
                m = 4
                poly = [(math.cos(aa + (ab - aa) * i / m) * r1, R.CZ + math.sin(aa + (ab - aa) * i / m) * r1) for i in range(m + 1)] + \
                       [(math.cos(ab - (ab - aa) * i / m) * r0, R.CZ + math.sin(ab - (ab - aa) * i / m) * r0) for i in range(m + 1)]
                cl = WS.clip_convex(WS.ccw(poly), wedge)
                P.add(cl, col)
        # a roundel in the middle band and a gold lozenge toward the head
        rc = 1.72
        P.add(WS.circle(math.cos(am) * rc, R.CZ + math.sin(am) * rc, 0.24, 24), PALEBLUE if k % 2 == 0 else PALEGOLD)
        P.star(math.cos(am) * rc, R.CZ + math.sin(am) * rc, 0.15, GOLD if k % 2 == 0 else RUBY, points=8, inner=0.5)
        lz = 2.95
        lx, lzz = math.cos(am) * lz, R.CZ + math.sin(am) * lz
        ux, uz = math.cos(am), math.sin(am)
        P.add([(lx - ux * 0.28, lzz - uz * 0.28), (lx - uz * 0.13, lzz + ux * 0.13), (lx + ux * 0.28, lzz + uz * 0.28), (lx + uz * 0.13, lzz - ux * 0.13)],
              GOLD)
        # the foil between this petal head and the next
        fx, fz = math.cos(a0) * R.FOIL_AT, R.CZ + math.sin(a0) * R.FOIL_AT
        P.add(WS.circle(fx, fz, R.FOIL_R + 0.03, 20), CRIMSON)
        P.star(fx, fz, R.FOIL_R - 0.04, GOLD, points=6, inner=0.5)
    # the hub: blue, crimson sexfoil, gold star, a white crescent at the heart
    P.add(WS.circle(0, R.CZ, R.HUB, 48), BLUE)
    P.add(WS.foil_outline(0, R.CZ, R.HUB - 0.12, 6, n=72), RUBY)
    P.star(0, R.CZ, 0.48, GOLD, points=12, inner=0.62)
    P.add(WS.circle(0, R.CZ, 0.26, 32), NIGHT)
    moon(P, 0, R.CZ, 0.2, tilt=0.7)
    save("RoseWindowStained", *P.render())


def stained_lancet():
    S = WS.StainedLancet
    out = WS.offset(WS.ccw(S.outline(24)), 0.05)
    P = Panel(out, seed=233)
    op = WS.ccw(S.outline(24))
    P.border(op, 0.2, [RUBY, GOLD], step=0.24)
    field = WS.offset(op, -0.2)
    hw = S.HW - 0.2
    # the bottom panel: crimson diamonds with gold jewels, a gold step under the candle
    low = WS.clip_convex(field, WS.rect(5, 0, 1.95))
    P.diamonds(low, 0.26, [CRIMSON, RUBY], jewel=(GOLD, 0.07))
    P.add(WS.rect(hw, 1.95, 2.08), GOLD)
    # the night: deep blue diamonds with scattered gold stars
    mid = WS.clip_convex(field, WS.rect(5, 2.08, S.ZS + 0.05))
    P.diamonds(mid, 0.34, [BLUE, NIGHT, MIDBLUE, BLUE])
    rng = np.random.default_rng(91)
    for k in range(40):
        x, z = rng.uniform(-hw + 0.15, hw - 0.15), rng.uniform(2.35, S.ZS - 0.15)
        if abs(x) < 0.38 and z < 5.4:
            continue
        if math.hypot(x - 0.0, z - 5.85) < 0.6 or math.hypot(x, z - 4.6) < 0.8:
            continue
        P.add(WS.circle(x, z, rng.uniform(0.07, 0.1), 14), PALEGOLD if k % 3 else GOLD)
    candle(P, 0.0, 2.08, 0.34, 2.05, 0.78)
    moon(P, 0.02, 5.88, 0.36, tilt=0.55, stars=[(0.45, 6.05, 0.06)])
    # the head: crimson round a gold trefoil with a ruby heart
    head = WS.clip_convex(field, WS.rect(5, S.ZS + 0.05, 20))
    P.diamonds(head, 0.3, [CRIMSON, RUBY])
    fx, fz, fr = S.FOIL
    P.add(WS.foil_outline(fx, fz, fr - 0.04, 3, n=48), GOLD)
    P.add(WS.circle(fx, fz, 0.12, 14), RUBY)
    save("StainedLancetStained", *P.render())


def room():
    """The warm lit room behind clear glass: an amber pool of candle and lamp light low in the middle, falling away to
    dark brown at the edges, with the faint shapes of a room (a dado line, a doorway's edge) in the gloom."""
    W = H = 2048
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W - 0.5, 1.0 - y / H
    d = np.sqrt((u / 0.62) ** 2 + ((v - 0.38) / 0.75) ** 2)
    pool = np.clip(1.0 - d, 0, 1) ** 1.35
    hot = np.array((1.0, 0.64, 0.3), np.float32)
    cold = np.array((0.16, 0.075, 0.035), np.float32)
    n = fbm(W, H, 5, 5, octaves=5, seed=77)
    img = cold + (hot - cold) * (pool * (0.85 + 0.3 * n))[..., None]
    # a dado rail and panelling below it, a dark doorway edge on the left
    dado = np.exp(-((v - 0.3) / 0.006) ** 2) * 0.25
    img *= (1 - dado)[..., None]
    panel = ((np.abs(((u + 0.5) * 6) % 1 - 0.5) < 0.02) & (v < 0.29)).astype(np.float32) * 0.18
    img *= (1 - panel)[..., None]
    door = np.clip((u + 0.33) / 0.01, 0, 1) * np.clip((-u - 0.18) / 0.01, 0, 1) * (v < 0.82)
    img *= (1 - 0.35 * door)[..., None]
    img = np.clip(img, 0, 1)
    glow = np.clip(img.max(axis=2) * 1.1, 0, 1)
    Image.fromarray((img * 255).astype(np.uint8)).save(os.path.join(OUT, "WindowRoom_canvas.png"))
    Image.fromarray((glow * 255).astype(np.uint8)).save(os.path.join(OUT, "WindowRoom_emissive.png"))
    print("[glass] WindowRoom: 2048x2048")


JOBS = {"TraceryWindow": tracery_window, "RoseWindow": rose_window, "StainedLancet": stained_lancet, "Room": room}

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(JOBS)):
        JOBS[name]()
