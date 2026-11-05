"""
Nightmare High face layers that sit UNDER the painted eyes (2026-11-04).

  Form faces  (a menacing transformed face, shown while Transformation is set)
      formface_<vampire|vampire2|wolf|ghoul|ghoul2|wraith>.png
      sunken sockets, a glow round the eyes, void / ooze tears, snarl creases, cracks, fur (no blood: Roblox
      moderation warned the owner's account over blood on 2026-11-04)
  Race marks  (an everyday face mark, race-locked in the wardrobe)
      mark_<id>.png

Every layer is a 1024x1024 RGBA image on the same strip shell as the eyes, drawn at 4x and box-filtered
down, with the PBR-style bake for raised / wet / metal details. Crisp marks are checked against every eye
(all shapes, both sets, every form), every brow and every mouth: no line pixel may come within GAP px.
Soft shading (sockets, glow) lies under the eyes on purpose and is not part of the check.

usage: python gen_menace.py <outdir> <eyes_dir> <faceparts_dir>
"""
import glob, json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

OUT, EYES, PARTS = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], os.path.join(OUT, "_scratch"), EYES]
import gen_face as G   # Canvas, stroke, PBR helpers
G.OUT = OUT

os.makedirs(OUT, exist_ok=True)
S, N = G.S, G.N
GAP = 10
F32 = np.float32


def load_a(p):
    return np.asarray(Image.open(p).convert("RGBA"), F32)[..., 3] / 255.0


def union(paths):
    u = np.zeros((N, N), F32)
    for p in paths:
        u = np.maximum(u, load_a(p))
    return u


FORMKEYS = ["vampire", "vampire2", "wolf", "ghoul", "ghoul2", "wraith"]
eye_by_form = {}
for fk in ["base"] + FORMKEYS:
    eye_by_form[fk] = union(glob.glob(os.path.join(EYES, f"eyes_*_{fk}_main.png")) +
                            glob.glob(os.path.join(EYES, f"eyes_*_{fk}_iris.png")))
veins = union(glob.glob(os.path.join(EYES, "eyes_*_veins.png")))
eyes_all = np.max(np.stack(list(eye_by_form.values())), 0)
brows = union(glob.glob(os.path.join(PARTS, "brow_*.png")))
mouths_all = union(glob.glob(os.path.join(PARTS, "mouth_*.png")))
form_mouth = {fk: load_a(os.path.join(PARTS, f"mouth_{fk.rstrip('2')}.png")) for fk in FORMKEYS}
print("eye files:", {k: int((v > 0.05).sum()) for k, v in eye_by_form.items()})


def near(mask, gap=GAP):
    return ndimage.binary_dilation(mask > 0.05, iterations=gap)


KEEP_ALL = near(eyes_all) | near(brows) | near(mouths_all)


def up(a):
    return np.kron(a, np.ones((S, S), F32))


class _Paint:
    """Just the colour + alpha buffers of a Canvas (for the soft shading pass)."""

    def __init__(self, sh):
        self.sh = sh
        self.rgb = np.zeros(sh + (3,), F32)
        self.a = np.zeros(sh, F32)

    def over(self, rgb, a):
        a = np.clip(a, 0, 1)
        rgb = np.broadcast_to(np.asarray(rgb, F32), self.sh + (3,))
        oa = a + self.a * (1 - a)
        self.rgb = (rgb * a[..., None] + self.rgb * (self.a * (1 - a))[..., None]) / np.maximum(oa[..., None], 1e-6)
        self.a = oa


FADE = 14   # px over which a crisp mark fades out before it would reach the GAP zone round any eye / brow / mouth


class Layer:
    """Crisp marks (lines, stitches, tears) and soft shading (sockets, glow) are painted on separate buffers.
    On save, crisp marks fade smoothly to nothing before the GAP zone, so no line can touch the eyes, brows
    or mouths; soft shading may lie under the eyes on purpose."""

    def __init__(self):
        self.C = G.Canvas(0, 0, N, N)                 # crisp marks (+ the geometry helpers)
        self.Cs = _Paint(self.C.sh)                   # soft shading

    def over(self, col, a, crisp=True):
        (self.C if crisp else self.Cs).over(np.asarray(col, F32), np.clip(a, 0, 1))

    def stroke(self, pts, w, prof=None, col=(0, 0, 0), alpha=1.0, crisp=True):
        prof = prof or (lambda q: np.clip(np.sin(np.pi * np.clip(q, 0, 1)) ** 0.5, 0, 1))
        m = self.C.mask([G.stroke(np.asarray(pts, float), w, prof)])
        self.over(col, m * alpha, crisp)
        return m

    def soft(self, col, a1024, strength):
        self.over(col, up(a1024) * strength, crisp=False)

    def save(self, name, keep, bake=True):
        dist = ndimage.distance_transform_edt(~keep).astype(F32)
        fade = up(np.clip(dist / FADE, 0, 1) ** 1.5)
        ca = self.C.a * fade
        sa = self.Cs.a
        oa = ca + sa * (1 - ca)
        self.C.rgb = (self.C.rgb * ca[..., None] + self.Cs.rgb * (sa * (1 - ca))[..., None]) / np.maximum(oa[..., None], 1e-6)
        self.C.a = oa
        if bake:
            G.pbr_bake(self.C, 0.85)
        crisp = (ca.reshape(N, S, N, S).mean((1, 3)) > 0.35)
        bad = int((crisp & keep).sum())
        self.C.save(name)
        return bad


rng0 = np.random.default_rng(7)


def eye_geom(e):
    """Per-eye boxes from an eye union: [(x0, x1, top, bottom, cx)] left then right."""
    m = e > 0.05
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=6))
    boxes = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) > 2000:
            boxes.append((xs.min(), xs.max(), ys.min(), ys.max(), (xs.min() + xs.max()) / 2))
    boxes.sort(key=lambda b: b[4])
    return boxes[:2]


def bottom_at(e, x):
    col = np.nonzero(e[:, int(x)] > 0.05)[0]
    return int(col.max()) if len(col) else 560


def tear(L, x, y0, length, w0, col, hi=None, seed=0, wob=1.6):
    r = np.random.default_rng(seed)
    q = np.linspace(0, 1, 30)
    pts = np.stack([x + wob * np.sin(q * 5 + r.uniform(0, 6)) + r.uniform(-1, 1) * q * 3, y0 + length * q], 1)
    L.stroke(pts, w0, lambda t: np.clip(0.45 + 0.55 * t, 0, 1) * np.clip(t * 6, 0, 1) ** 0.6, col)
    L.over(col, L.C.ell(pts[-1, 0], pts[-1, 1] + w0 * 0.3, w0 * 0.75, w0 * 1.0, soft=0.9))
    if hi is not None:
        L.over(hi, L.C.ell(pts[-1, 0] - w0 * 0.2, pts[-1, 1] - w0 * 0.1, w0 * 0.18, w0 * 0.28, soft=0.6) * 0.8)


def crack(L, p0, heading, length, w, col, seed, branches=2, light=None):
    r = np.random.default_rng(seed)
    pts = [np.array(p0, float)]
    h = heading
    for _ in range(9):
        h += r.uniform(-0.6, 0.6)
        pts.append(pts[-1] + length / 9 * np.array([math.cos(h), math.sin(h)]))
    pts = np.array(pts)
    if light is not None:
        L.stroke(pts + [0.9, 1.1], w * 0.7, col=light, alpha=0.6)
    L.stroke(pts, w, lambda t: np.clip(1 - t, 0, 1) ** 0.5, col)
    for b in range(branches):
        k = r.integers(2, 7)
        crack(L, pts[k], h + r.choice([-1, 1]) * r.uniform(0.6, 1.1), length * 0.4, w * 0.7, col, seed + 11 + b, 0, light)


def fur_tufts(L, side, col, seed, y0=560, y1=780):
    """Wolfish cheek fur: clumps of curved, tapering locks sweeping out toward the edge of the face,
    dark at the root and lighter at the tip."""
    r = np.random.default_rng(seed)
    dark = np.array(col, float)
    light = np.minimum(dark * 1.9 + 0.08, 1)
    for k in range(16):
        cy = r.uniform(y0, y1)
        cx = r.uniform(70, 150) if side < 0 else r.uniform(874, 954)
        base_ang = math.pi / 2 + side * r.uniform(0.35, 0.9)      # down and out
        for j in range(5):
            x = cx + r.normal(0, 6)
            y = cy + r.normal(0, 8)
            ang = base_ang + r.normal(0, 0.12)
            Lh = r.uniform(32, 58)
            bow = side * r.uniform(6, 14)
            t = np.linspace(0, 1, 14)
            px = x + np.cos(ang) * Lh * t + bow * t * t
            py = y + np.sin(ang) * Lh * t
            pts = np.stack([px, py], 1)
            w = r.uniform(4.5, 6.5)
            L.stroke(pts, w, lambda q: np.clip(1 - q, 0, 1) ** 0.8, tuple(dark * r.uniform(0.75, 1.0)))
            L.stroke(pts[5:], w * 0.45, lambda q: np.clip(1 - q, 0, 1) ** 0.9, tuple(light * r.uniform(0.8, 1.0)), alpha=0.6)


def creases(L, pts_list, col, w=3.2):
    for pts in pts_list:
        L.stroke(np.array(pts, float) + [1.2, 1.5], w * 0.8, col=(0.96, 0.82, 0.74), alpha=0.35, crisp=False)
        L.stroke(pts, w, lambda t: np.clip(np.sin(np.pi * t), 0, 1) ** 0.6, col)


def sockets(L, e, col, strength, grow=16, sigma=20, inner=0.0):
    m = (e > 0.05).astype(F32)
    d = ndimage.binary_dilation(m > 0, iterations=grow).astype(F32)
    soft = ndimage.gaussian_filter(d, sigma)
    L.soft(col, soft / max(soft.max(), 1e-6), strength)
    if inner:
        ring = ndimage.gaussian_filter(ndimage.binary_dilation(m > 0, iterations=5).astype(F32), 5)
        L.soft(col, ring / max(ring.max(), 1e-6), inner)


def aura(L, e, col, strength, sigma=34):
    g = ndimage.gaussian_filter(ndimage.binary_dilation(e > 0.05, iterations=8).astype(F32), sigma)
    L.soft(col, g / max(g.max(), 1e-6), strength)


BLOOD = (0.5, 0.02, 0.06)
BLOOD_HI = (0.9, 0.3, 0.32)
VOID = (0.02, 0.02, 0.05)
ICE = (0.72, 0.9, 1.0)
GOLD = (0.86, 0.66, 0.24)
SCAR = (0.86, 0.62, 0.56)
INK = (0.20, 0.07, 0.09)
report = {}


# ================================================================== form faces
def form_vampire(stage2=False):
    fk = "vampire2" if stage2 else "vampire"
    e = eye_by_form[fk]
    L = Layer()
    sockets(L, e, (0.16, 0.0, 0.06), 0.85 if stage2 else 0.7, grow=18, sigma=20, inner=0.45)
    aura(L, e, (0.9, 0.06, 0.14), 0.4 if stage2 else 0.3)
    yy, xx = np.mgrid[0:N, 0:N].astype(F32)
    for cx, sg in ((262, -1), (762, 1)):      # hollow cheekbones: a soft shadow under each, no hard edge
        u, v = (xx - (cx + sg * 30)) / 95.0, (yy - 690) / 34.0
        band = np.clip(1 - np.sqrt(u * u + v * v), 0, 1) ** 1.5
        L.soft((0.22, 0.06, 0.12), ndimage.gaussian_filter(band, 10), 0.42 if stage2 else 0.32)
    keep = near(e) | near(brows) | near(form_mouth[fk])
    report[fk] = L.save(f"formface_{fk}.png", keep)


def form_wolf():
    fk = "wolf"
    e = eye_by_form[fk]
    L = Layer()
    sockets(L, e, (0.22, 0.12, 0.02), 0.5, inner=0.3)
    aura(L, e, (0.95, 0.6, 0.1), 0.26)
    g = eye_geom(e)
    if len(g) == 2:
        mid = (g[0][1] + g[1][0]) / 2
        top = min(g[0][2], g[1][2])
        ys = np.linspace(top + 26, top + 70, 8)
        # a frown knotted between the eyes, and snarl creases over the bridge of the nose
        creases(L, [np.stack([mid - 9 - 4 * np.sin((ys - ys[0]) / 18), ys], 1),
                    np.stack([mid + 9 + 4 * np.sin((ys - ys[0]) / 18), ys], 1)], INK)
        yb = max(g[0][3], g[1][3]) + 40
        for j in range(3):
            y = yb + j * 15
            xs = np.linspace(mid - 34 + j * 6, mid + 34 - j * 6, 12)
            creases(L, [np.stack([xs, y - 7 * np.sin(np.linspace(0, np.pi, 12))], 1)], INK, 3.0)
    fur_tufts(L, -1, (0.32, 0.22, 0.14), 5)
    fur_tufts(L, 1, (0.32, 0.22, 0.14), 6)
    keep = near(e) | near(brows) | near(form_mouth[fk])
    report[fk] = L.save("formface_wolf.png", keep)


def form_ghoul(stage2=False):
    fk = "ghoul2" if stage2 else "ghoul"
    e = eye_by_form[fk]
    L = Layer()
    sockets(L, e, (0.1, 0.03, 0.12), 0.8 if stage2 else 0.65, grow=20, sigma=22, inner=0.45)
    for cx in (250, 774):   # hollow cheeks
        L.soft((0.12, 0.08, 0.14), ndimage.gaussian_filter((np.hypot(np.arange(N)[None] - cx, np.arange(N)[:, None] - 690) < 60).astype(F32), 26), 0.5)
    # rot mottling on the temples and brow, cracked skin
    blot = ndimage.gaussian_filter(np.random.default_rng(3).standard_normal((N, N)), 14)
    blot = np.clip((blot / blot.std() - 1.1) * 0.7, 0, 1)
    band = np.zeros((N, N), F32)
    band[60:330, :] = 1
    band[:, :170] = 1
    band[:, 854:] = 1
    band[820:, :] = 0
    band = ndimage.gaussian_filter(band, 28)            # no hard edge where the rot stops
    L.soft((0.33, 0.4, 0.24), blot * band * ndimage.gaussian_filter((~KEEP_ALL).astype(F32), 6), 0.55)
    for p0, hd, s in (((120, 430), 1.2, 1), ((904, 430), 1.95, 2), ((420, 190), 0.4, 3), ((640, 160), 2.6, 4), ((90, 640), 0.9, 5), ((934, 650), 2.2, 6)):
        crack(L, p0, hd, 120, 3.6, (0.16, 0.12, 0.12), 40 + s, 2, light=(0.78, 0.76, 0.64))
    if stage2:   # black ooze weeping from the eyes
        for k, (x0, x1, top, bot, cx) in enumerate(eye_geom(e)):
            for j, f in enumerate((-0.2, 0.1, 0.28)):
                x = cx + (x1 - x0) * f
                tear(L, x, bottom_at(e, x) + GAP + 4, 70 + 40 * (j % 2), 7.0, (0.04, 0.03, 0.04), (0.5, 0.5, 0.55), seed=71 + k * 5 + j)
    keep = near(e) | near(brows) | near(form_mouth[fk]) | near(veins)
    report[fk] = L.save(f"formface_{fk}.png", keep)


def form_wraith():
    fk = "wraith"
    e = eye_by_form[fk]
    L = Layer()
    sockets(L, e, VOID, 0.9, grow=24, sigma=20, inner=0.6)
    aura(L, e, ICE, 0.3, sigma=40)
    for k, (x0, x1, top, bot, cx) in enumerate(eye_geom(e)):
        for j, f in enumerate((-0.05, 0.22)):
            x = cx + (x1 - x0) * f
            tear(L, x, bottom_at(e, x) + GAP + 4, 150 + 30 * j, 7.5, VOID, None, seed=91 + k * 3 + j, wob=2.4)
    for p0, hd, s in (((96, 400), 1.0, 1), ((928, 400), 2.1, 2), ((512, 120), 1.57, 3)):
        crack(L, p0, hd, 110, 3.0, (0.55, 0.82, 0.95), 60 + s, 2)
    keep = near(e) | near(brows) | near(form_mouth[fk])
    report[fk] = L.save("formface_wraith.png", keep)


# ================================================================== race marks
def eyes_geom_all():
    return eye_geom(eyes_all)


def mark_freckles():
    L = Layer()
    r = np.random.default_rng(12)
    g = eyes_geom_all()
    yb = max(b[3] for b in g)
    n = 0
    while n < 46:
        side = r.choice([-1, 1])
        x = 512 + side * r.uniform(90, 290)
        y = r.uniform(yb + 30, yb + 150)
        if abs(x - 512) < 60 and y > yb + 110:
            continue
        rad = r.uniform(2.4, 4.4)
        L.over((0.55, 0.32, 0.22), L.C.ell(x, y, rad, rad * 0.9, soft=1.2) * r.uniform(0.45, 0.75))
        n += 1
    return L


def mark_scar():
    L = Layer()
    pts = np.array([[188 + 110 * t, 610 + 150 * t + 6 * math.sin(t * 7)] for t in np.linspace(0, 1, 40)])
    L.stroke(pts + [0, 2], 9, col=(0.62, 0.36, 0.34), alpha=0.5)
    L.stroke(pts, 6.5, col=SCAR)
    for t in np.linspace(0.1, 0.9, 6):
        p = pts[int(t * 39)]
        L.stroke([p + [-9, 5], p + [9, -5]], 2.6, col=(0.7, 0.44, 0.42), alpha=0.8)
    return L


def mark_beauty():
    L = Layer()
    L.over((0.24, 0.12, 0.1), L.C.ell(700, 690, 5.5, 5.0, soft=1.0))
    return L


def mark_bandage():
    L = Layer()
    cx, cy, w, h, ang = 790, 690, 120, 40, -0.42
    ca, sa = math.cos(ang), math.sin(ang)
    def rect(w_, h_):
        return np.array([[cx + ca * x - sa * y, cy + sa * x + ca * y] for x, y in ((-w_ / 2, -h_ / 2), (w_ / 2, -h_ / 2), (w_ / 2, h_ / 2), (-w_ / 2, h_ / 2))])
    L.over((0.5, 0.36, 0.3), L.C.mask([rect(w + 4, h + 4) + [2, 3]]) * 0.35)
    L.over((0.9, 0.78, 0.64), L.C.mask([rect(w, h)]))
    L.over((0.96, 0.92, 0.86), L.C.mask([rect(w * 0.34, h - 6)]))
    r = np.random.default_rng(4)
    for _ in range(14):
        x, y = r.uniform(-w / 2 + 8, w / 2 - 8), r.uniform(-h / 2 + 6, h / 2 - 6)
        if abs(x) < w * 0.17:
            continue
        L.over((0.72, 0.58, 0.48), L.C.ell(cx + ca * x - sa * y, cy + sa * x + ca * y, 1.6, 1.6, soft=0.8) * 0.8)
    return L


def mark_vamp_bat():
    L = Layer()
    cx, cy, w = 838, 640, 70
    right = [(0.06, -0.08), (0.18, -0.2), (0.34, -0.24), (0.5, -0.12), (0.42, 0.0), (0.36, -0.03),
             (0.3, 0.07), (0.23, 0.01), (0.16, 0.11), (0.09, 0.04), (0.04, 0.16)]
    head = [(0.0, -0.06), (0.03, -0.17), (0.045, -0.08)]
    pts = [(-x, y) for x, y in head[::-1]] + list(head) + right + [(0, 0.2)] + [(-x, y) for x, y in right[::-1]]
    poly = np.array([[cx + x * w, cy + y * w] for x, y in pts])
    L.over((0.3, 0.04, 0.1), L.C.mask([poly]))
    return L


def mark_vamp_pallor():
    L = Layer()
    sockets(L, eyes_all, (0.3, 0.26, 0.36), 0.42, grow=10, sigma=14)
    yy, xx = np.mgrid[0:N, 0:N].astype(F32)
    for cx, sg in ((262, -1), (762, 1)):     # hollow cheekbones, soft
        u, v = (xx - (cx + sg * 30)) / 90.0, (yy - 690) / 30.0
        band = np.clip(1 - np.sqrt(u * u + v * v), 0, 1) ** 1.5
        L.soft((0.42, 0.3, 0.38), ndimage.gaussian_filter(band, 10), 0.3)
    return L


def mark_wolf_scars():
    L = Layer()
    for j in range(3):
        pts = np.array([[150 + j * 34 + 120 * t, 590 + 160 * t] for t in np.linspace(0, 1, 30)])
        L.stroke(pts + [1.5, 2], 8, col=(0.5, 0.22, 0.22), alpha=0.45)
        L.stroke(pts, 5.5, lambda t: np.clip(np.sin(np.pi * t), 0, 1) ** 0.5, (0.82, 0.5, 0.48))
    return L


def mark_wolf_tufts():
    L = Layer()
    fur_tufts(L, -1, (0.3, 0.22, 0.16), 21, 520, 760)
    fur_tufts(L, 1, (0.3, 0.22, 0.16), 22, 520, 760)
    return L


def mark_ghoul_stitches():
    """Stitched seams down the outer cheeks and across the scalp, as if the face was sewn back on."""
    L = Layer()

    def seam(pts):
        pts = np.asarray(pts, float)
        L.stroke(pts + [0, 2], 8, col=(0.45, 0.26, 0.28), alpha=0.5)
        L.stroke(pts, 4.5, col=(0.4, 0.14, 0.16))
        n = len(pts)
        for t in np.linspace(0.06, 0.94, max(4, n // 4)):
            i = int(t * (n - 1))
            d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
            nv = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
            a_, b_ = pts[i] - nv * 14 + d * 0.5, pts[i] + nv * 14 - d * 0.5
            L.stroke(np.linspace(a_, b_, 8), 4.0, lambda q: np.clip(np.sin(np.pi * np.clip(q, 0, 1)) ** 0.3, 0, 1), (0.14, 0.08, 0.08))
            a2, b2 = pts[i] - nv * 14 - d * 0.5, pts[i] + nv * 14 + d * 0.5
            L.stroke(np.linspace(a2, b2, 8), 4.0, lambda q: np.clip(np.sin(np.pi * np.clip(q, 0, 1)) ** 0.3, 0, 1), (0.14, 0.08, 0.08))

    t = np.linspace(0, 1, 30)
    for sg in (-1, 1):
        seam(np.stack([512 + sg * (372 + 14 * np.sin(t * 3)), 540 + 230 * t], 1))
    seam(np.stack([300 + 424 * t, 190 - 26 * np.sin(np.pi * t)], 1))
    return L


def mark_ghoul_rot():
    L = Layer()
    blot = ndimage.gaussian_filter(np.random.default_rng(8).standard_normal((N, N)), 12)
    blot = np.clip((blot / blot.std() - 1.0) * 0.8, 0, 1)
    band = np.zeros((N, N), F32)
    band[80:300, 200:824] = 1
    band[420:780, 30:170] = 1
    band[420:780, 854:994] = 1
    band = ndimage.gaussian_filter(band, 28)
    L.soft((0.36, 0.42, 0.26), blot * band * ndimage.gaussian_filter((~KEEP_ALL).astype(F32), 6), 0.7)
    for p0, hd, s in (((110, 450), 1.25, 1), ((914, 460), 1.9, 2), ((380, 160), 0.3, 3)):
        crack(L, p0, hd, 110, 3.2, (0.16, 0.12, 0.12), 80 + s, 2, light=(0.78, 0.76, 0.64))
    return L


def mark_wraith_frost():
    L = Layer()
    for p0, hd, s in (((80, 380), 0.9, 1), ((944, 380), 2.2, 2), ((150, 640), 0.7, 3), ((874, 640), 2.4, 4)):
        crack(L, p0, hd, 120, 7.0, (0.6, 0.85, 1.0), 100 + s, 3)        # faint frosted halo
        crack(L, p0, hd, 120, 2.8, ICE, 100 + s, 3)
    return L


def mark_wraith_tears():
    L = Layer()
    for k, (x0, x1, top, bot, cx) in enumerate(eyes_geom_all()):
        x = cx + (x1 - x0) * (-0.02 if k else 0.02)
        tear(L, x, bottom_at(eyes_all, x) + GAP + 4, 120, 5.0, (0.05, 0.05, 0.1), None, seed=55 + k, wob=2.0)
    return L


def mark_priest_brand():
    L = Layer()
    cx, cy = 512, 200
    for grow, col in ((3.0, (0.36, 0.24, 0.06)), (0.0, GOLD)):
        L.over(col, L.C.mask([np.array([[cx - 8 - grow, cy - 50 - grow], [cx + 8 + grow, cy - 50 - grow], [cx + 8 + grow, cy + 56 + grow], [cx - 8 - grow, cy + 56 + grow]]),
                                np.array([[cx - 36 - grow, cy - 22 - grow], [cx + 36 + grow, cy - 22 - grow], [cx + 36 + grow, cy - 6 + grow], [cx - 36 - grow, cy - 6 + grow]])]))
    L.soft((1.0, 0.86, 0.5), ndimage.gaussian_filter((np.hypot(np.arange(N)[None] - cx, np.arange(N)[:, None] - cy) < 50).astype(F32), 24), 0.25)
    return L


def mark_priest_script():
    L = Layer()
    r = np.random.default_rng(9)
    yb = max(b[3] for b in eyes_geom_all()) + GAP + 26
    for sg in (-1, 1):
        x = 512 + sg * 330
        for i in range(9):
            gx = x + sg * -i * 22
            y = yb + 6 * math.sin(i * 0.8)
            kind = r.integers(0, 3)
            if kind == 0:
                L.stroke([[gx, y - 7], [gx, y + 7]], 2.4, col=GOLD)
                L.stroke([[gx - 5, y - 2], [gx + 5, y - 2]], 2.4, col=GOLD)
            elif kind == 1:
                L.stroke(np.array([[gx - 6 + 12 * t, y + 5 * math.sin(t * 6)] for t in np.linspace(0, 1, 10)]), 2.2, col=GOLD)
            else:
                L.over(GOLD, L.C.ell(gx, y, 3.2, 3.2, soft=0.8))
    return L


MARKS = {
    "freckles": mark_freckles, "scar": mark_scar, "beauty": mark_beauty, "bandage": mark_bandage,
    "vamp_bat": mark_vamp_bat, "vamp_pallor": mark_vamp_pallor,
    "wolf_scars": mark_wolf_scars, "wolf_tufts": mark_wolf_tufts,
    "ghoul_stitches": mark_ghoul_stitches, "ghoul_rot": mark_ghoul_rot,
    "wraith_frost": mark_wraith_frost, "wraith_tears": mark_wraith_tears,
    "priest_brand": mark_priest_brand, "priest_script": mark_priest_script,
}

if __name__ == "__main__":
    only = os.environ.get("ONLY", "").split(",") if os.environ.get("ONLY") else None
    jobs = [("formface_vampire", lambda: form_vampire()), ("formface_vampire2", lambda: form_vampire(True)),
            ("formface_wolf", form_wolf), ("formface_ghoul", lambda: form_ghoul()), ("formface_ghoul2", lambda: form_ghoul(True)),
            ("formface_wraith", form_wraith)]
    for name, fn in jobs:
        if only and name not in only:
            continue
        fn()
        print("ok", name, flush=True)
    for mid, fn in MARKS.items():
        if only and ("mark_" + mid) not in only:
            continue
        L = fn()
        report["mark_" + mid] = L.save(f"mark_{mid}.png", KEEP_ALL)
        print("ok mark", mid, flush=True)
    bad = {k: v for k, v in report.items() if v}
    print("OVERLAPS:", bad if bad else "none")
    json.dump(report, open(os.path.join(OUT, "overlap_report.json"), "w"), indent=1)
