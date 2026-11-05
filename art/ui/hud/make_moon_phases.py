"""Moon phases for Nightmare Highschool: sky textures (Sky.MoonTextureId) and HUD clock icons, baked to images.

Sky textures (1024, transparent): an original moon built on a sphere seen face-on. Maria are soft blobs on the sphere with
band-limited 3D sine noise along their shores; craters (a few big ones with central peaks and ray systems, many medium and
hundreds of small ones) are carved into a height field with bowls, raised rims and ejecta; a crisp regolith grain sits on
top. The sphere normal is perturbed by that height and lit with a Lommel-Seeliger / Lambert mix (lunar-looking, with limb
darkening), so the terminator shows crater relief. Roblox draws the sky moon roughly additively, so unlit areas are black
and transparent (alpha follows the brightness there), never grey; alpha is tight to the disc. A faint cool-bone tint.
  Full: lit from just off the viewer.   Waning: the LEFT half lit.   Waxing: the RIGHT half lit.
  New: earthshine only (~12%, maria barely visible) plus a hair-thin crescent on the right limb.

HUD icons (256, greyscale + alpha, tinted bone/gold by the HUD): the kit's relief pipeline (make_app_icons.Icon: the same
PBR lighting as the phone icons): a domed bone disc with a few bold craters, a crisp straight terminator, and for New a dark
disc with a bright crescent and an outline ring so it stays visible on a dark HUD.

    python make_moon_phases.py
Writes art/ui/hud/out/moon/Moon<Phase>.png, IconMoon<Phase>.png and preview.png.
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_app_icons as A

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "moon"
OUT.mkdir(parents=True, exist_ok=True)
f32 = np.float32
PHASES = ["Full", "Waning", "New", "Waxing"]

# ============================================================ the sky moon
N = 1024
RD = 0.92 * N / 2                         # disc radius (px): the disc fills ~92% of the frame
C = (N - 1) / 2
py_, px_ = np.mgrid[0:N, 0:N].astype(f32)
X = (px_ - C) / RD
Y = (py_ - C) / RD
R2 = X * X + Y * Y
INSIDE = R2 < 1
Z = np.sqrt(np.clip(1 - R2, 0, 1))
DISC = np.clip((1 - np.sqrt(R2)) * RD + 0.5, 0, 1).astype(f32)          # analytic 1 px anti-aliased edge
rng = np.random.default_rng(1979)


def sines3(freq, terms, seed):
    """Band-limited, isotropic 3D sine noise sampled on the sphere surface (no smearing, no seams). ~N(0, 1)."""
    r = np.random.default_rng(seed)
    out = np.zeros((N, N), f32)
    for _ in range(terms):
        d = r.normal(size=3)
        d /= np.linalg.norm(d)
        k = freq * r.uniform(0.75, 1.3)
        out += np.sin(k * (d[0] * X + d[1] * Y + d[2] * Z) + r.uniform(0, 6.283)).astype(f32)
    return out / math.sqrt(terms / 2)


def fbm(f0, octaves, seed, gain=0.5):
    out, amp, tot = np.zeros((N, N), f32), 1.0, 0.0
    for o in range(octaves):
        out += sines3(f0 * 2 ** o, 14, seed + o) * amp
        tot += amp
        amp *= gain
    return out / tot


def rand_dir(zmin, bias=None):
    while True:
        v = rng.normal(size=3)
        v /= np.linalg.norm(v)
        if bias is not None:
            v = v + np.array(bias)
            v /= np.linalg.norm(v)
        if v[2] > zmin:
            return v


# ---- maria: an original chain of seas across the upper half (a big western sea, three linked basins with narrow
#      straits, a sea curling down the east side) plus a few isolated ones. Each sea is a run of capsules on the sphere;
#      the sphere is domain-warped first, so the shores grow lobes, bays and branches, then a multi-scale shore noise
#      roughens them and a narrow threshold keeps them fairly crisp (a ~3 px transition at 1024).
def sines3p(P, freq, terms, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((N, N), f32)
    for _ in range(terms):
        d = r.normal(size=3)
        d /= np.linalg.norm(d)
        k = freq * r.uniform(0.75, 1.3)
        out += np.sin(k * (d[0] * P[0] + d[1] * P[1] + d[2] * P[2]) + r.uniform(0, 6.283)).astype(f32)
    return out / math.sqrt(terms / 2)


def fbmp(P, f0, octaves, seed, gain=0.5):
    out, amp, tot = np.zeros((N, N), f32), 1.0, 0.0
    for o in range(octaves):
        out += sines3p(P, f0 * 2 ** o, 14, seed + o) * amp
        tot += amp
        amp *= gain
    return out / tot


P0 = (X, Y, Z)
W1 = [fbmp(P0, 2.2, 3, 500 + 10 * i) for i in range(3)]
P1 = tuple(P0[i] + 0.055 * W1[i] for i in range(3))
W2 = [fbmp(P1, 7.0, 3, 600 + 10 * i) for i in range(3)]
PW = tuple(P1[i] + 0.04 * W2[i] for i in range(3))


def sphere_pt(x, y):
    return np.array((x, y, math.sqrt(max(0.02, 1 - x * x - y * y))), f32)


SEAS = [  # chains of (x, y, radius) in disc units (y down): consecutive nodes are joined by tapered capsules
    [(-0.64, -0.10, 0.24), (-0.60, 0.16, 0.26), (-0.46, 0.40, 0.19), (-0.28, 0.56, 0.11)],      # a broad western sea
    [(-0.54, -0.24, 0.16), (-0.32, -0.38, 0.26)],                                               # the great round basin
    [(-0.32, -0.38, 0.20), (-0.12, -0.42, 0.10), (0.06, -0.40, 0.17)],                         # strait to a second basin
    [(0.06, -0.40, 0.13), (0.17, -0.27, 0.10), (0.30, -0.12, 0.20)],                           # strait to a third
    [(0.30, -0.12, 0.16), (0.38, 0.12, 0.14), (0.28, 0.32, 0.10)],                             # curling down the east
    [(-0.04, 0.00, 0.10), (-0.18, 0.14, 0.11), (-0.34, 0.12, 0.09)],                           # a central sea to the west
    [(-0.16, -0.24, 0.07), (0.00, -0.14, 0.10), (-0.04, 0.00, 0.07), (0.14, 0.02, 0.06)],      # central seas linking the chain
    [(-0.20, 0.32, 0.12)],                                                                    # a southern bay
    [(0.60, -0.30, 0.10)],                                                                    # an isolated round sea
    [(0.10, 0.52, 0.07)],
]
TONES = [0.02, -0.01, 0.025, -0.035, 0.0, 0.015, -0.02, -0.03, 0.01, 0.02]   # each sea its own darkness (+ = lighter)
field = np.full((N, N), -1.0, f32)
tone_w = np.zeros((N, N), f32)
tone_s = np.zeros((N, N), f32)
for ci, chain in enumerate(SEAS):
    fc = np.full((N, N), -1.0, f32)
    pts = [(sphere_pt(x, y), r) for x, y, r in chain]
    if len(pts) == 1:
        pts = pts * 2
    for (pa, ra), (pb, rb) in zip(pts[:-1], pts[1:]):
        ab = pb - pa
        t = np.clip(((PW[0] - pa[0]) * ab[0] + (PW[1] - pa[1]) * ab[1] + (PW[2] - pa[2]) * ab[2])
                    / (float(ab @ ab) + 1e-6), 0, 1)
        dx, dy, dz = (PW[0] - pa[0] - t * ab[0]), (PW[1] - pa[1] - t * ab[1]), (PW[2] - pa[2] - t * ab[2])
        rr = ra + (rb - ra) * t
        fc = np.maximum(fc, 1 - np.sqrt(dx * dx + dy * dy + dz * dz) / rr)
    field = np.maximum(field, fc)
    w = np.exp(np.clip(fc, -1, 1) * 8.0)
    tone_w += w
    tone_s += w * TONES[ci % len(TONES)]
sea_tone = tone_s / (tone_w + 1e-6)
shore = 0.16 * fbmp(PW, 5.0, 3, 700) + 0.10 * fbmp(PW, 16.0, 3, 710) + 0.05 * fbmp(PW, 48.0, 2, 720)
islands = A.smooth(0.52, 0.68, fbmp(PW, 9.0, 3, 900)) * 0.45                # highland islands and peninsulas
fs = field + shore - islands
maria = A.smooth(-0.025, 0.025, fs) * INSIDE
depth_in = A.smooth(0.0, 0.5, fs) * maria                                  # 0 at the shore, 1 deep inside
# wrinkle ridges: thin sinuous ridged-noise lines inside the seas
ridges = np.zeros((N, N), f32)
for i, fq in enumerate((6.0, 9.0)):
    n = np.abs(sines3p(PW, fq, 10, 800 + i) + 0.4 * sines3p(PW, fq * 2.3, 10, 810 + i))
    ridges = np.maximum(ridges, A.smooth(0.16, 0.03, n))
ridges *= A.smooth(0.05, 0.16, fs) * maria * (0.5 + 0.5 * A.smooth(-0.3, 0.3, fbmp(PW, 4.0, 2, 830)))

# ---- craters, carved into a height field (px units)
height = np.zeros((N, N), f32)
bright = np.zeros((N, N), f32)          # fresh-crater albedo boost (floors, rims, ejecta, rays)


def crater(v, r, fresh, rays=False):
    """v: unit centre on the sphere, r: angular radius (rad)."""
    cx, cy = C + v[0] * RD, C + v[1] * RD
    ext = int(r * (6.5 if rays else 2.6) * RD) + 3
    x0, x1 = max(0, int(cx - ext)), min(N, int(cx + ext) + 1)
    y0, y1 = max(0, int(cy - ext)), min(N, int(cy + ext) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    sl = (slice(y0, y1), slice(x0, x1))
    ins = INSIDE[sl]
    d = np.arccos(np.clip(X[sl] * v[0] + Y[sl] * v[1] + Z[sl] * v[2], -1, 1))
    t = d / r
    depth = r * RD * 0.22
    rim = 0.28
    h = np.where(t < 1, (t * t - 1) * (1 - 0.15 * t) + rim * t ** 6,
                 rim * np.exp(-((t - 1) / 0.32) ** 2) + 0.05 * np.exp(-(t - 1) / 0.6) * (t < 3))
    if r > 0.05:
        h += 0.45 * np.exp(-(t / 0.16) ** 2) * (t < 1)                  # central peak
    if r > 0.012:
        h += 0.06 * np.sin(t * 9.0) * np.exp(-((t - 1.6) / 0.5) ** 2) * (t > 1)   # terraced ejecta
    height[sl] += (h * depth * ins).astype(f32)
    b = fresh * (0.06 * (t < 1) + 0.10 * np.exp(-((t - 1) / 0.15) ** 2) + 0.06 * np.exp(-np.clip(t - 1, 0, None) / 0.7))
    b = b - (1 - fresh) * 0.05 * (t < 0.9) + (1 - fresh) * 0.025 * np.exp(-((t - 1) / 0.12) ** 2)                                # old craters: dusty, darker floors
    if rays:
        # bright rays: thin radial streaks fading with distance
        u = np.cross(v, (0, 0, 1.0)) if abs(v[2]) < 0.99 else np.array((1.0, 0, 0))
        u /= np.linalg.norm(u)
        w = np.cross(v, u)
        P = np.stack([X[sl], Y[sl], Z[sl]], -1)
        th = np.arctan2(P @ w, P @ u)
        rr = np.random.default_rng(int(r * 1e6))
        streak = np.zeros_like(th)
        for _ in range(26):
            a0, wdt = rr.uniform(-math.pi, math.pi), rr.uniform(0.05, 0.13)
            ln = rr.uniform(2.5, 6.5)
            dth = np.angle(np.exp(1j * (th - a0)))
            fade = np.clip(1 - (t - 1) / ln, 0, 1) ** 1.5
            streak += np.exp(-(dth / wdt) ** 2) * fade * (0.6 + 0.4 * np.sin(t * rr.uniform(5, 9) + rr.uniform(0, 6)))
        b = b + 0.14 * np.clip(streak, 0, 1.6) * A.smooth(1.0, 1.6, t)
    bright[sl] += (b * ins).astype(f32)


for _ in range(3):                                           # big, with peaks; two have ray systems
    crater(rand_dir(0.5), rng.uniform(0.07, 0.11), fresh=0.25)
crater(rand_dir(0.5, (0.1, 0.55, 0.3)), 0.045, fresh=1.0, rays=True)
crater(rand_dir(0.5, (0.45, -0.2, 0.3)), 0.032, fresh=1.0, rays=True)
for _ in range(80):
    crater(rand_dir(0.25), rng.uniform(0.018, 0.05), fresh=rng.uniform(0.0, 1.0) ** 3)
for _ in range(750):
    v = rand_dir(0.08)
    crater(v, rng.uniform(0.005, 0.017) * (0.7 if rng.random() < 0.3 else 1.0), fresh=rng.uniform(0.0, 1.0) ** 3)
for _ in range(1700):
    crater(rand_dir(0.08), rng.uniform(0.0025, 0.006), fresh=rng.uniform(0.0, 1.0) ** 4)

# ---- albedo: highlands bright and mottled with a fine speckle, maria darker and mottled with ridges, fresh craters
#      bright, a crisp grain
grain = rng.random((N, N)).astype(f32)
grain = ndimage.gaussian_filter(grain, 0.7) - 0.5
mottle = fbm(6.0, 4, 200)
alb = 0.63 + 0.09 * mottle + 0.05 * fbm(18.0, 3, 210)
sea = (0.35 + sea_tone * 2.6 + 0.08 * fbmp(PW, 3.5, 4, 300) + 0.035 * fbmp(PW, 20.0, 3, 310) - 0.04 * depth_in
       + 0.03 * A.smooth(0.0, 0.08, -fs + 0.08) + 0.035 * ridges)                   # slightly lighter shoals at the shore
alb = alb * (1 - maria) + sea * maria
alb -= 0.05 * A.smooth(-0.14, 0.0, fs) * (1 - maria) * INSIDE                    # a faint grey fringe outside the shores
alb += bright * (1 - 0.35 * maria)
alb += grain * 0.10
# fine bright speckle on the highlands (tiny fresh pits and boulders between the craters)
r2 = np.random.default_rng(4242)
speck = ndimage.gaussian_filter((r2.random((N, N)) > 0.988).astype(f32), 0.55) * 2.2
speck -= ndimage.gaussian_filter((r2.random((N, N)) > 0.992).astype(f32), 0.55) * 1.2
alb += np.clip(speck, -1, 1) * 0.16 * (1 - 0.8 * maria)
alb = np.clip(alb, 0.05, 1.0)
height += grain * 0.3 + fbm(30.0, 2, 400) * 0.6 + ndimage.gaussian_filter(ridges, 2.5) * 0.8 - ndimage.gaussian_filter(maria, 4) * 0.35

# ---- normals: the sphere normal perturbed by the height slope
gy, gx = np.gradient(ndimage.gaussian_filter(height, 0.6))
K = 1.15
Nx, Ny, Nz = X - K * gx * Z, Y - K * gy * Z, Z + 1e-3
nl = np.sqrt(Nx * Nx + Ny * Ny + Nz * Nz)
Nx, Ny, Nz = Nx / nl, Ny / nl, Nz / nl
TINT = (np.array((1.0, 0.985, 0.955), f32) * (1 - maria[..., None])          # cool bone: a hair warm of grey,
        + np.array((0.965, 0.975, 0.985), f32) * maria[..., None])             # the seas a touch cooler


def lit(L, earthshine=0.0, gain=1.0):
    L = np.array(L, f32)
    L /= np.linalg.norm(L)
    mu0 = np.clip(Nx * L[0] + Ny * L[1] + Nz * L[2], 0, 1)
    mu = np.clip(Nz, 0.02, 1)
    ls = mu0 / (mu0 + mu + 1e-4)
    I = alb * (1.25 * ls + 0.42 * mu0) * gain
    # the terminator: the sphere itself (not the bumps) decides where day ends, softly
    sph = np.clip(X * L[0] + Y * L[1] + Z * L[2], -1, 1)
    I *= A.smooth(-0.05, 0.12, sph)
    if earthshine:
        I += alb * earthshine * (0.35 + 0.65 * mu ** 0.5)
    return np.clip(I, 0, 1.2)


def to_rgba(I):
    v = np.clip(I, 0, 1) ** (1 / 2.2)
    v = v / 0.97
    # colour stays the true brightness (dark stays dark however the engine blends); alpha eases in with it, so unlit
    # areas are transparent and the alpha is tight to the disc
    a = DISC * np.sqrt(A.smooth(0.0, 0.32, v))
    rgb = np.clip(v[..., None] * TINT, 0, 1) * (a[..., None] > 0)
    return Image.fromarray((np.dstack([rgb, a[..., None]]) * 255 + 0.5).astype(np.uint8), "RGBA")


SKY = {
    "Full": dict(L=(-0.20, -0.14, 1.0), gain=0.9),
    "Waning": dict(L=(-1.0, 0.0, 0.0), gain=1.15),
    "Waxing": dict(L=(1.0, 0.0, 0.0), gain=1.15),
    "New": dict(L=(math.cos(math.radians(73)), 0.0, -math.sin(math.radians(73))), earthshine=0.018, gain=1.8),
}

# ============================================================ HUD icons (kit relief pipeline)
CRATERS = ((372, 360, 96), (612, 300, 58), (604, 610, 116), (352, 650, 64), (480, 820, 40), (780, 470, 46),
           (300, 500, 34), (500, 470, 30))


def moon_icon(phase):
    ic = A.Icon(40 + PHASES.index(phase))
    cx = cy = 512
    R = 430
    disc = A.circle(cx, cy, R)
    ic.part(disc, z=0.20, lift=0.26, bevel=170, alb=A.BONE * 1.08, rough=0.6, tex=0.012)
    sea = ndimage.gaussian_filter(A.U(A.circle(420, 420, 150), A.circle(560, 560, 120), A.circle(360, 600, 90)), 18)
    ic._mat(sea * disc, A.BONE * 0.86, None, None)
    for (x, y, r) in CRATERS:
        ic.recess(A.circle(x, y, r * 0.82), 0.10, r * 0.55, alb=A.BONE * 0.9)
        ic.emboss(A.ring(x, y, r * 0.86, r * 0.26) * disc, 0.06, r * 0.13)
    if phase == "Full":
        return ic
    if phase == "New":
        crescent = np.clip(disc - A.circle(cx - 92, cy, R + 6), 0, 1)
        shadow = np.clip(disc - crescent, 0, 1)
    else:
        side = 1 if phase == "Waning" else -1                    # Waning: left lit, so the right is in shadow
        shadow = np.clip((xx_i - cx) * side + 0.5, 0, 1) * disc
        crescent = None
    ic.alb = ic.alb * (1 - 0.9 * shadow)
    ic.rough = ic.rough * (1 - shadow) + 0.8 * shadow
    outline = A.ring(cx, cy, R - 16, 32) * shadow
    ic._mat(outline, 0.55 if phase == "New" else 0.40, 0.5, None)
    if crescent is not None:
        ic._mat(crescent, 1.0, 0.4, None)
        ic.emboss(crescent, 0.06, 12)
    return ic


xx_i = A.xx


# ============================================================ the two special full moons (in colour)
SPECIAL = ["Crimson", "Blue"]
RPX = np.sqrt(R2) * RD                                   # radius in px from the centre
TH = np.arctan2(Y, X)


def outside_glow(i, col):
    """Light just outside the disc, kept in alpha: colour and alpha both fall to nothing well inside the frame edge."""
    i = np.clip(i, 0, 1) * A.smooth(N / 2 - 2, N / 2 - 26, RPX) * (1 - DISC)
    return i, np.array(col, f32)


def compose(rgb_in, glow_i, glow_c):
    """Disc colour (sRGB, 0..1) over an outside glow. Inside the disc alpha is the disc; outside it is the glow, and the
    glow's colour falls toward black with it (so no grey or coloured box however the engine blends)."""
    a_out = glow_i
    rgb_out = glow_c * (glow_i[..., None] ** 0.35)
    a = DISC + a_out * (1 - DISC)
    rgb = (rgb_in * DISC[..., None] + rgb_out * (a_out * (1 - DISC))[..., None]) / np.maximum(a, 1e-4)[..., None]
    keep = a > 0.002
    rgb = np.clip(rgb, 0, 1) * keep[..., None]
    a = a * keep
    return Image.fromarray((np.dstack([rgb, a[..., None]]) * 255 + 0.5).astype(np.uint8), "RGBA")


def fissure(p0, p1, levels, disp, rr):
    """Midpoint-displaced polyline between two points (disc units): an elegant, irregular crack."""
    pts = [np.array(p0, f32), np.array(p1, f32)]
    d = disp
    for _ in range(levels):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2
            n = np.array((-(b - a)[1], (b - a)[0]), f32)
            out += [m + n * rr.normal() * d, b]
        pts = out
        d *= 0.55
    return pts


def crack_field():
    """A few sparse, branching hairline fissures, drawn at 3x: a crisp core plus a tight and a wide glow."""
    rr = np.random.default_rng(77)
    k = 3
    core = Image.new("L", (N * k, N * k), 0)
    dc = ImageDraw.Draw(core)

    def stroke(pts, w0, taper):
        n = len(pts)
        for j in range(n - 1):
            t = j / (n - 1)
            w = w0 * (1 - 0.55 * abs(2 * t - 1)) if taper == "mid" else w0 * (1 - t) + 0.6
            dc.line(((C + pts[j][0] * RD) * k, (C + pts[j][1] * RD) * k,
                     (C + pts[j + 1][0] * RD) * k, (C + pts[j + 1][1] * RD) * k), fill=255, width=max(1, int(w * k)))

    mains = (((-0.62, -0.52), (0.06, -0.08)), ((0.10, 0.10), (0.70, 0.44)), ((-0.40, 0.26), (-0.10, 0.78)),
             ((0.30, -0.70), (0.52, -0.22)))
    for (a, b) in mains:
        pts = fissure(a, b, 6, 0.12, rr)
        stroke(pts, 2.2, "mid")
        n = len(pts)
        for _ in range(2):                                                 # two short branches each
            j = int(rr.uniform(0.25, 0.75) * (n - 1))
            dirv = pts[min(n - 1, j + 4)] - pts[max(0, j - 4)]
            ang = math.atan2(dirv[1], dirv[0]) + rr.choice((-1, 1)) * rr.uniform(0.5, 0.9)
            L = float(np.linalg.norm(np.array(b) - np.array(a))) * rr.uniform(0.18, 0.32)
            end = pts[j] + L * np.array((math.cos(ang), math.sin(ang)), f32)
            stroke(fissure(pts[j], end, 4, 0.10, rr), 1.3, "end")
    c = np.array(core.resize((N, N), Image.BOX), f32) / 255
    c *= A.smooth(0.0, 0.35, Z) * INSIDE                                 # the cracks fade out toward the limb
    g1 = np.clip(ndimage.gaussian_filter(c, 3.0) * 3.0, 0, 1)
    g2 = np.clip(ndimage.gaussian_filter(c, 11.0) * 5.0, 0, 1)
    return c, g1, g2


def moon_crimson():
    I = lit(**SKY["Full"])
    v = np.clip(I, 0, 1) ** (1 / 2.2) / 0.97
    v = v * (1 - 0.18 * maria)                                           # richer, darker seas
    vv = np.clip(v + 0.9 * (v - ndimage.gaussian_filter(v, 5)), 0, 1)                 # a little local contrast
    stops = [0.0, 0.35, 0.6, 0.85, 1.0]                                                # oxblood > crimson > coral
    rgb = np.dstack([np.interp(vv, stops, [0.05, 0.30, 0.58, 0.80, 0.95]),
                     np.interp(vv, stops, [0.005, 0.02, 0.05, 0.14, 0.30]),
                     np.interp(vv, stops, [0.01, 0.03, 0.06, 0.10, 0.22])]).astype(f32)
    crest = A.smooth(0.8, 3.0, ndimage.gaussian_filter(height, 1.2) - ndimage.gaussian_filter(height, 7.0)) * INSIDE
    rgb += (crest * v)[..., None] * np.array((0.16, 0.05, 0.02), f32)                  # rims catching ember light
    rim = np.exp(-np.clip(1 - np.sqrt(R2), 0, 1) / 0.035) * INSIDE      # an ember rim inside the limb
    rgb += rim[..., None] * np.array((0.26, 0.03, 0.02), f32)
    core, g1, g2 = crack_field()
    rgb = rgb * (1 - 0.35 * g1[..., None])                              # the fissure is a dark cut...
    rgb += g2[..., None] * np.array((0.34, 0.03, 0.02), f32)            # ...leaking light: a wide red glow,
    rgb += g1[..., None] * np.array((0.75, 0.22, 0.06), f32)            # a hot orange edge,
    rgb += core[..., None] * np.array((1.00, 0.70, 0.40), f32)          # and a near-white hairline core
    glow, col = outside_glow(0.62 * np.exp(-(RPX - RD) / 11.0), (0.85, 0.10, 0.06))
    return compose(np.clip(rgb, 0, 1), glow, col)


def astrolabe():
    """A thin etched astrolabe ring: two hairline circles, ticks between them, tiny runes outside, dots inside."""
    k = 3
    m = Image.new("L", (N * k, N * k), 0)
    d = ImageDraw.Draw(m)
    r0, r1 = 0.70 * RD, 0.745 * RD
    for r in (r0, r1):
        d.ellipse(((C - r) * k, (C - r) * k, (C + r) * k, (C + r) * k), outline=255, width=int(1.6 * k))
    for i in range(96):
        a = i / 96 * 2 * math.pi
        ln = r1 if i % 8 == 0 else (r0 + (r1 - r0) * 0.5)
        ca, sa = math.cos(a), math.sin(a)
        d.line(((C + r0 * ca) * k, (C + r0 * sa) * k, (C + ln * ca) * k, (C + ln * sa) * k), fill=255,
               width=int((1.6 if i % 8 == 0 else 1.1) * k))
    rr = 0.80 * RD
    for i, g in enumerate(A.RUNES * 2):
        th = i / 16 * 2 * math.pi + math.pi / 16
        ca, sa = math.cos(th), math.sin(th)
        Hg = 15
        for (ax, ay), (bx, by) in g:
            def P(gx, gy):
                return ((C + (rr - gy * Hg) * ca - gx * Hg * sa) * k, (C + (rr - gy * Hg) * sa + gx * Hg * ca) * k)
            d.line((*P(ax, ay), *P(bx, by)), fill=255, width=int(1.4 * k))
    for i in range(48):
        a = i / 48 * 2 * math.pi + 0.07
        r = 0.66 * RD
        x, y = C + r * math.cos(a), C + r * math.sin(a)
        d.ellipse(((x - 1.6) * k, (y - 1.6) * k, (x + 1.6) * k, (y + 1.6) * k), fill=255)
    return np.array(m.resize((N, N), Image.BOX), f32) / 255


def moon_blue():
    I = lit(**SKY["Full"])
    v = np.clip(I, 0, 1) ** (1 / 2.2) / 0.97
    rgb = v[..., None] * np.array((0.74, 0.86, 1.0), f32) + (v ** 3)[..., None] * np.array((0.22, 0.14, 0.02), f32)
    rgb *= 1 - 0.10 * maria[..., None] * np.array((0.6, 0.3, 0.0), f32)          # seas a cooler, deeper blue
    crest = ndimage.gaussian_filter(height, 1.2) - ndimage.gaussian_filter(height, 7.0)
    crest = A.smooth(0.8, 3.0, crest) * INSIDE                                   # frost-bright crater rims
    rgb += (crest * v)[..., None] * np.array((0.20, 0.26, 0.32), f32)
    etch = astrolabe() * INSIDE * (1 - 0.85 * maria) * A.smooth(0.0, 0.3, Z)
    rgb = rgb * (1 - 0.10 * etch[..., None]) + etch[..., None] * np.array((0.10, 0.16, 0.24), f32)
    rim = np.exp(-np.clip(1 - np.sqrt(R2), 0, 1) / 0.03) * INSIDE                # a faint cold limb
    rgb += rim[..., None] * np.array((0.10, 0.16, 0.24), f32)
    gapm = A.smooth(0.20, 0.55, np.abs(np.angle(np.exp(1j * (TH - math.radians(-40))))))   # a gap at the upper right
    ring = np.exp(-((RPX - (RD + 24)) / 3.0) ** 2) * (0.08 + 0.92 * gapm)
    glow, col = outside_glow(0.45 * np.exp(-(RPX - RD) / 7.0) + 1.0 * ring, (0.76, 0.89, 1.0))
    return compose(np.clip(rgb, 0, 1), glow, col)


def special_icon(kind):
    """The HUD icon for a special moon: the kit relief full moon with a glyph accent, then a hint of colour."""
    ic = moon_icon("Full")
    cx = cy = 512
    crack = None
    if kind == "Blue":
        ang = np.arctan2(A.yy - cy, A.xx - cx)
        gapm = A.smooth(0.25, 0.6, np.abs(np.angle(np.exp(1j * (ang - math.radians(-40))))))
        ic.part(A.ring(cx, cy, 484, 22) * gapm, z=0.26, lift=0.1, bevel=10, alb=1.0, rough=0.3)
    else:
        pts = [(330, 300), (400, 380), (382, 440), (470, 500), (520, 470), (590, 560), (570, 640), (650, 720)]
        crack = A.U(*[A.seg(*pts[i], *pts[i + 1], 22) for i in range(len(pts) - 1)],
                    A.seg(470, 500, 440, 600, 14), A.seg(590, 560, 680, 540, 14))
        ic.recess(crack, 0.10, 6, alb=1.0, rough=0.2)
    lum, alpha = ic.render()
    if kind == "Blue":
        rgb = lum[..., None] * np.array((0.80, 0.90, 1.0), f32)
    else:
        rgb = lum[..., None] * np.array((0.92, 0.34, 0.34), f32)
        glow = np.clip(ndimage.gaussian_filter(crack, 10) * 1.5, 0, 1)
        rgb = rgb + glow[..., None] * np.array((0.45, 0.12, 0.02), f32) * alpha[..., None]
        rgb = rgb * (1 - crack[..., None]) + crack[..., None] * np.array((1.0, 0.62, 0.30), f32)
    im = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), alpha]) * 255 + 0.5).astype(np.uint8), "RGBA")
    return im.resize((256, 256), Image.LANCZOS)


# ============================================================ preview
def night(w, h):
    t = np.linspace(0, 1, h, dtype=f32)[:, None, None]
    top, bot = np.array((14, 12, 38), f32), np.array((52, 40, 92), f32)
    g = np.broadcast_to(top * (1 - t) + bot * t, (h, w, 3)).copy()
    r = np.random.default_rng(3)
    for _ in range(w * h // 2500):                                # a few stars
        x, y = r.integers(0, w), r.integers(0, h)
        g[y, x] = np.minimum(255, g[y, x] + r.uniform(60, 180))
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")


def preview(sky, icons):
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
        fs = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    except OSError:
        f = fs = ImageFont.load_default()
    gap = 40
    ALL = PHASES + SPECIAL
    W = len(ALL) * N + (len(ALL) + 1) * gap
    row1 = N + 2 * gap
    row2 = 240
    row3 = 260
    pv = Image.new("RGBA", (W, row1 + row2 + row3 + 60), (10, 9, 14, 255))
    pv.alpha_composite(night(W, row1 + row2), (0, 0))
    d = ImageDraw.Draw(pv)
    for i, p in enumerate(ALL):
        x = gap + i * (N + gap)
        pv.alpha_composite(sky[p], (x, gap))
        d.text((x + N / 2, gap / 2), f"Moon{p}  (1024)", fill=(220, 214, 230, 255), font=f, anchor="mm")
        s = sky[p].resize((80, 80), Image.LANCZOS)
        pv.alpha_composite(s, (x + N // 2 - 40, row1 + 60))
        d.text((x + N / 2, row1 + 170), f"{p} at 80 px", fill=(200, 194, 214, 255), font=fs, anchor="mm")
    y3 = row1 + row2
    d.rectangle((0, y3, W, y3 + row3 + 60), fill=(18, 16, 22, 255))
    gold = np.array((232, 214, 168), f32) / 255
    for i, p in enumerate(ALL):
        x = gap + i * (N + gap)
        plate = (x + N // 2 - 200, y3 + 40, x + N // 2 + 200, y3 + 200)
        d.rounded_rectangle(plate, radius=22, fill=(30, 26, 34, 255), outline=(70, 60, 70, 255), width=2)
        a = np.array(icons[p], f32)
        if p not in SPECIAL:                                         # the specials keep their own colour
            a[..., :3] *= gold
        t = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        pv.alpha_composite(t.resize((24, 24), Image.LANCZOS), (plate[0] + 40, y3 + 108))
        d.text((plate[0] + 76, y3 + 120), "11:58", fill=(232, 214, 168, 255), font=fs, anchor="lm")
        pv.alpha_composite(t.resize((64, 64), Image.LANCZOS), (plate[0] + 220, y3 + 88))
        d.text((x + N / 2, y3 + 230), f"IconMoon{p}: 24 px and 64 px", fill=(200, 190, 170, 255), font=fs,
               anchor="mm")
    pv.save(OUT / "preview.png")


if __name__ == "__main__":
    sky, icons = {}, {}
    for p in PHASES:
        im = to_rgba(lit(**SKY[p]))
        im.save(OUT / f"Moon{p}.png", optimize=True)
        sky[p] = im
        lum, alpha = moon_icon(p).render()
        ic = Image.fromarray((np.dstack([lum, lum, lum, alpha]) * 255 + 0.5).astype(np.uint8), "RGBA")
        ic = ic.resize((256, 256), Image.LANCZOS)
        ic.save(OUT / f"IconMoon{p}.png", optimize=True)
        icons[p] = ic
        print("wrote", OUT / f"Moon{p}.png", OUT / f"IconMoon{p}.png")
    for p, fn in (("Crimson", moon_crimson), ("Blue", moon_blue)):
        im = fn()
        im.save(OUT / f"Moon{p}.png", optimize=True)
        sky[p] = im
        ic = special_icon(p)
        ic.save(OUT / f"IconMoon{p}.png", optimize=True)
        icons[p] = ic
        print("wrote", OUT / f"Moon{p}.png", OUT / f"IconMoon{p}.png")
    preview(sky, icons)
    print("wrote", OUT / "preview.png")
