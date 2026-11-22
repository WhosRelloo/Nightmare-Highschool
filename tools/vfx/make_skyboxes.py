"""Painted gothic skyboxes for Nightmare Highschool (concept 58): one Sky per DayCycle look.

usage: python tools/vfx/make_skyboxes.py [outdir=art/group-upload-skies] [size=1024] [only=Day,Dusk,...] [preview=art/skies-preview]

2.36 (sky-2360): 19 sets. Day and Dusk below, plus the 17 sets painted in tools/vfx/skies2360.py: Dawn; Night, NightNew,
NightCrimson, NightBlue; Storm; WinterDay/Dusk/Night, SpringDay/Dusk/Night, SummerDay/Dusk/Night; NightmareDusk/Night.
The 2.16 descriptions below still describe Day and Dusk; see skies2360.py for the rest.

  NHSkyDay        a muted, cool gothic day: blue-grey zenith, bone haze on the horizon, big painted clouds lit from the
                  sun's side of the sky (-Z), the far hills and the town lost in the haze
  NHSkyDusk       the dusk / dawn sky: a candle-gold glow where the sun sets (-X, a little -Z), crimson-mauve above it,
                  violet zenith, a pink belt and the cool earth shadow opposite, streaky clouds rimmed gold. Dawn uses
                  the same faces turned with Sky.SkyboxOrientation (Config.DayCycle.Skies) so the glow sits at sunrise
  NHSkyNight      ink zenith, a faint ink-blue glow on the horizon, thin moonlit wisps, and a faint distant town
                  silhouette all round (spires, roofs, towers, a few candle-lit windows), the biggest cluster in the
                  east where the moon rises
  NHSkyNightBlue  the night with a faint aurora-like band of ink blue, cold teal and violet on the +Z side, away from
                  the moon's path (the blue-moon nights)
  NHSkyStorm      a low, heavy storm ceiling: rolling dark clouds, a thin cold break on one horizon, rain curtains

Roblox face mapping, measured in Studio (labelled test faces, 2026-11-13). Each face is (forward, image right, image
down) in world space, +Y up; Lf sits on +X and Rt on -X (the reverse of what the names suggest):
  Ft -Z (+X, -Y)   Bk +Z (-X, -Y)   Lf +X (+Z, -Y)   Rt -X (-Z, -Y)   Up +Y (-Z, -X)   Dn -Y (-Z, +X)
Every pixel is painted from its 3D direction (noise is 3D, the horizon strip wraps in azimuth), so the faces meet with
no seams; the preview sheet re-projects the written PNGs through the same mapping and measures the seams.

The moon is left out: Roblox's Sky draws it (Lineage.MoonTextures, World.FullMoon / World.MoonPhases), and so are the
stars (Sky.StarCount), so the upper sky stays dark and clean where the moon travels (it rises at +X, crosses the -Z
side up to ~67 degrees and sets at -X). No blood, no gore; house palette: Ink #07060A, Bone #E4DED0, Candle Gold
#EBCD78, Crimson #C8283C, Ink Blue #5C80D2.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "art", "group-upload-skies")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
ONLY = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] not in ("", "all") else None
PREVIEW = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "art", "skies-preview")

FACES = {  # face: (forward, image right, image down)
    "Ft": ((0, 0, -1), (1, 0, 0), (0, -1, 0)),
    "Bk": ((0, 0, 1), (-1, 0, 0), (0, -1, 0)),
    "Lf": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "Rt": ((-1, 0, 0), (0, 0, -1), (0, -1, 0)),
    "Up": ((0, 1, 0), (0, 0, -1), (-1, 0, 0)),
    "Dn": ((0, -1, 0), (0, 0, -1), (1, 0, 0)),
}
ORDER = ["Bk", "Dn", "Ft", "Lf", "Rt", "Up"]

INK = (7, 6, 10)
BONE = (228, 222, 208)
GOLD = (235, 205, 120)
CRIMSON = (200, 40, 60)
INKBLUE = (92, 128, 210)

SUNSET = np.array([-0.92, -0.04, -0.40])  # where the sun goes down (Lighting:GetSunDirection() at 18:00)
SUNSET /= np.linalg.norm(SUNSET)


def C(rgb):
    return np.array(rgb, np.float32) / 255.0


def face_dirs(face, n):
    f, r, d = (np.array(v, np.float32) for v in FACES[face])
    s = (np.arange(n, dtype=np.float32) + 0.5) / n * 2 - 1
    u, v = np.meshgrid(s, s)
    D = f + u[..., None] * r + v[..., None] * d
    return D / np.linalg.norm(D, axis=-1, keepdims=True)


# ---------------------------------------------------------------- noise (3D value noise, so it has no seams anywhere)

_PERM = {}


def _tables(seed):
    if seed not in _PERM:
        r = np.random.default_rng(seed)
        _PERM[seed] = (np.concatenate([r.permutation(1024)] * 2).astype(np.int64), r.random(1024).astype(np.float32))
    return _PERM[seed]


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise3(P, seed):
    perm, val = _tables(seed)
    i = np.floor(P).astype(np.int64)
    f = (P - i).astype(np.float32)
    u = _fade(f)
    i &= 1023
    ix, iy, iz = i[..., 0], i[..., 1], i[..., 2]
    jx, jy, jz = (ix + 1) & 1023, (iy + 1) & 1023, (iz + 1) & 1023

    def h(a, b, c):
        return val[perm[perm[perm[a] + b] + c] & 1023]

    ux, uy, uz = u[..., 0], u[..., 1], u[..., 2]
    x00 = h(ix, iy, iz) * (1 - ux) + h(jx, iy, iz) * ux
    x10 = h(ix, jy, iz) * (1 - ux) + h(jx, jy, iz) * ux
    x01 = h(ix, iy, jz) * (1 - ux) + h(jx, iy, jz) * ux
    x11 = h(ix, jy, jz) * (1 - ux) + h(jx, jy, jz) * ux
    y0 = x00 * (1 - uy) + x10 * uy
    y1 = x01 * (1 - uy) + x11 * uy
    return y0 * (1 - uz) + y1 * uz


def fbm3(P, octaves, seed, gain=0.5, lac=2.03):
    tot = np.zeros(P.shape[:-1], np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        tot += amp * noise3(P, seed + o * 7)
        norm += amp
        amp *= gain
        P = P * lac + 17.3
    return tot / norm


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    """Lerp colours: t is a scalar or a per-pixel mask (broadcast over the colour channels)."""
    t = np.asarray(t, np.float32)
    if t.ndim:
        t = t[..., None]
    return a + (b - a) * t


def ramp(e, stops):
    """Colour by elevation (degrees): stops = [(deg, rgb255), ...], smooth between stops."""
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32) / 255.0
    k = np.clip(np.searchsorted(xs, e) - 1, 0, len(xs) - 2)
    t = np.clip((e - xs[k]) / (xs[k + 1] - xs[k]), 0, 1)
    t = t * t * (3 - 2 * t)
    return cs[k] + (cs[k + 1] - cs[k]) * t[..., None]


# ---------------------------------------------------------------- the distant land and town (a strip around the horizon)

SW = 16200            # strip width: 45 px a degree of azimuth
PXD = SW / 360.0
EL_TOP, EL_BOT = 8.0, -3.0
SH = int((EL_TOP - EL_BOT) * PXD)


def _fbm1(n, cells, seed, octaves=4):
    r = np.random.default_rng(seed)
    x = np.arange(n) / n
    out = np.zeros(n)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = r.random(c)
        p = x * c
        i0 = np.floor(p).astype(int)
        t = p - i0
        t = t * t * (3 - 2 * t)
        out += amp * (g[i0 % c] * (1 - t) + g[(i0 + 1) % c] * t)
        tot += amp
        amp *= 0.5
    return out / tot


def build_land(seed=58):
    """Returns (far, near, town, windows) float strips [SH, SW] in 0..1 coverage / glow; x = azimuth, y = elevation."""
    rng = np.random.default_rng(seed)

    def ypix(el):
        return (EL_TOP - el) * PXD

    def profile_mask(h_deg):
        img = Image.new("L", (SW, SH), 0)
        dr = ImageDraw.Draw(img)
        pts = [(x, ypix(h_deg[x])) for x in range(0, SW, 4)] + [(SW, ypix(h_deg[0])), (SW, SH), (0, SH)]
        dr.polygon(pts, fill=255)
        return img

    xs = np.arange(SW)
    far_h = 0.35 + 1.1 * _fbm1(SW, 9, seed + 1) ** 1.6
    near_h = 0.12 + 0.55 * _fbm1(SW, 23, seed + 2) + 0.12 * _fbm1(SW, 900, seed + 3, 2)  # with a tree-line fuzz
    far = profile_mask(far_h)
    near = profile_mask(near_h)

    town = Image.new("L", (SW, SH), 0)
    win = Image.new("L", (SW, SH), 0)
    dt, dw = ImageDraw.Draw(town), ImageDraw.Draw(win)

    def poly(pts, wrap=True):
        for off in ((0, -SW, SW) if wrap else (0,)):
            dt.polygon([(x + off, y) for x, y in pts], fill=255)

    def rect(x0, x1, y0, y1, d=None):
        d = d or dt
        for off in (0, -SW, SW):
            d.rectangle([x0 + off, y0, x1 + off, y1], fill=255)

    def building(az, base, scale):
        """One building at azimuth az (deg) standing on elevation base; returns its right edge in degrees."""
        kind = rng.choice(["house", "house", "row", "tall", "tower", "church", "spire"],
                          p=[0.28, 0.12, 0.22, 0.16, 0.1, 0.05, 0.07])
        w = {"house": rng.uniform(0.35, 0.7), "row": rng.uniform(0.8, 1.6), "tall": rng.uniform(0.3, 0.5),
             "tower": rng.uniform(0.22, 0.34), "church": rng.uniform(0.9, 1.3), "spire": rng.uniform(0.12, 0.2)}[kind]
        h = {"house": rng.uniform(0.45, 0.8), "row": rng.uniform(0.6, 1.0), "tall": rng.uniform(0.9, 1.5),
             "tower": rng.uniform(1.4, 2.3), "church": rng.uniform(0.8, 1.1), "spire": rng.uniform(1.2, 1.8)}[kind] * scale
        x0, x1 = az * PXD, (az + w) * PXD
        yb, yt = ypix(base), ypix(base + h)
        rect(x0, x1, yt, yb + 2)
        if kind in ("house", "row", "tall"):
            # pitched roofs: one gable for a house, a saw of gables for a row
            n = 1 if kind != "row" else int(rng.integers(2, 5))
            pitch = rng.uniform(0.18, 0.4) * scale
            for k in range(n):
                a, b = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
                poly([(a - 2, yt), ((a + b) / 2, ypix(base + h + pitch)), (b + 2, yt)])
            for k in range(int(rng.integers(0, 3))):  # chimneys
                cx = rng.uniform(x0 + 4, x1 - 8)
                rect(cx, cx + 0.05 * PXD, ypix(base + h + pitch * 0.9), yt)
        elif kind == "tower":
            if rng.random() < 0.5:  # a conical cap
                poly([(x0 - 3, yt), ((x0 + x1) / 2, ypix(base + h + rng.uniform(0.6, 1.2) * scale)), (x1 + 3, yt)])
            else:  # battlements
                m = 4
                for k in range(m):
                    if k % 2 == 0:
                        a = x0 + (x1 - x0) * k / (m - 1) * 0.86
                        rect(a, a + (x1 - x0) * 0.16, ypix(base + h + 0.12 * scale), yt)
        elif kind == "church":
            poly([(x0 - 2, yt), ((x0 + x1) / 2 - 0.2 * PXD, ypix(base + h + 0.35 * scale)), (x1 + 2, yt)])
            sx0 = x1 - 0.28 * PXD
            sx1 = x1
            th = h + rng.uniform(0.9, 1.3) * scale
            rect(sx0, sx1, ypix(base + th), yb)
            poly([(sx0 - 2, ypix(base + th)), ((sx0 + sx1) / 2, ypix(base + th + rng.uniform(1.8, 2.6) * scale)),
                  (sx1 + 2, ypix(base + th))])
        elif kind == "spire":
            poly([(x0 - 2, yt), ((x0 + x1) / 2, ypix(base + h + rng.uniform(1.0, 1.6) * scale)), (x1 + 2, yt)])
        # windows: small, few, candle-lit
        cols = max(1, int((x1 - x0) / (0.16 * PXD)))
        rows = max(1, int(h / 0.32))
        for cx in range(cols):
            for ry in range(rows):
                if rng.random() < 0.13:
                    wx = x0 + (cx + 0.3) * (x1 - x0) / cols
                    wy = ypix(base + h * (ry + 0.35) / rows)
                    rect(wx, wx + 0.1 * PXD, wy - 0.13 * PXD, wy, dw)
        return az + w + rng.uniform(-0.05, 0.35)

    # (centre azimuth, half width, height scale): az 0 = -Z, 90 = +X (moonrise), 180 = +Z, 270 = -X (sunset)
    clusters = [(88, 21, 1.0), (196, 8, 0.7), (332, 6, 0.6), (140, 4, 0.5)]
    for c, hw, sc in clusters:
        az = c - hw
        while az < c + hw:
            t = 1 - abs(az - c) / hw
            base = float(np.interp((az % 360) * PXD, xs, near_h)) - 0.05
            if rng.random() < 0.82:
                az = building(az, base, sc * (0.45 + 0.75 * t ** 0.7))
            else:
                az += rng.uniform(0.3, 1.2)

    blur = ImageFilter.GaussianBlur(1.6)
    f = lambda im: np.asarray(im.filter(blur), np.float32) / 255.0
    return f(far), f(near), f(town), np.asarray(win.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0


def sample_strip(strip, az, el):
    """Bilinear sample of a horizon strip at azimuth/elevation (degrees); 0 outside it."""
    x = (az % 360.0) * PXD - 0.5
    y = (EL_TOP - el) * PXD - 0.5
    inside = (y > -1) & (y < SH)
    y = np.clip(y, 0, SH - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = (x - x0).astype(np.float32), (y - y0).astype(np.float32)
    x0 %= SW
    x1 = (x0 + 1) % SW
    a = strip[y0, x0] * (1 - fx) + strip[y0, x1] * fx
    b = strip[y0 + 1, x0] * (1 - fx) + strip[y0 + 1, x1] * fx
    out = a * (1 - fy) + b * fy
    out = np.where(inside, out, 0.0)
    # below the strip the land carries on (it is all ground there)
    return np.where(el <= EL_BOT + 0.2, strip[SH - 1, x0], out).astype(np.float32)


LAND = None


def land(az, el):
    global LAND
    if LAND is None:
        LAND = build_land()
    far, near, town, win = LAND
    return (sample_strip(far, az, el), sample_strip(near, az, el), sample_strip(town, az, el), sample_strip(win, az, el))


# ---------------------------------------------------------------- shared painting helpers


def geometry(D):
    x, y, z = D[..., 0], D[..., 1], D[..., 2]
    el = np.degrees(np.arcsin(np.clip(y, -1, 1)))
    az = np.degrees(np.arctan2(x, -z)) % 360.0
    return x, y, z, el, az


def cloud_plane(D, lift=0.16):
    """Where a view ray meets a flat cloud deck: (u, v) grows toward the horizon, so far clouds bunch up."""
    x, y, z = D[..., 0], D[..., 1], D[..., 2]
    k = 1.0 / (np.maximum(y, -0.02) + lift)
    return x * k, z * k


def clouds(D, seed, scale, cover, soft, stretch=1.0, warp=0.6, light=(0.0, -1.0), octaves=6, lift=0.16):
    """Painted cloud deck: (alpha, lit) where lit is 0 on the shadow side and 1 on the edge facing `light` (in u, v)."""
    u, v = cloud_plane(D, lift)
    P = np.stack([u * scale / stretch, v * scale, np.full_like(u, seed * 0.37)], -1)
    W = np.stack([fbm3(P * 0.5, 3, seed + 100), fbm3(P * 0.5 + 9.1, 3, seed + 200), np.zeros_like(u)], -1)
    Pw = P + (W - 0.5) * warp * 2
    d = fbm3(Pw, octaves, seed)
    lx, lv = light
    Pl = Pw + np.array([lx * 0.22 / stretch, lv * 0.22, 0], np.float32)
    dl = fbm3(Pl, octaves - 2, seed)
    a = ss(1 - cover, 1 - cover + soft, d)
    lit = np.clip(0.5 + (d - dl) * 5.0, 0, 1)
    return a.astype(np.float32), lit.astype(np.float32), d


def strokes(D, seed, amount):
    """A faint horizontal brush texture (long along the horizon, short up the sky) so flat sky reads painted."""
    P = D * np.array([9.0, 70.0, 9.0], np.float32)
    s = fbm3(P, 3, seed)
    return 1.0 + (s - 0.5) * 2 * amount


def finish(col, D, seed, brush=0.03):
    col = col * strokes(D, seed, brush)[..., None]
    grain = (noise3(D * 900.0, seed + 5) - 0.5) * (2.0 / 255.0)
    return np.clip(col + grain[..., None], 0, 1)


def put_land(col, el, az, sky_h, land_col, far_mix, near_mix, town_mix, win_rgb=None, win_amt=0.0, below=None):
    """Lay the far hills, near hills and the town over the sky, fading into the horizon colour (they are distant)."""
    far, near, town, win = land(az, el)
    col = mix(col, mix(sky_h, land_col, far_mix), far)
    col = mix(col, mix(sky_h, land_col, near_mix), np.maximum(near, 0))
    col = mix(col, mix(sky_h, land_col, town_mix), town)
    if win_rgb is not None and win_amt > 0:
        col = col + win[..., None] * C(win_rgb) * win_amt
    if below is not None:
        col = mix(col, below, ss(-3.0, -14.0, el))
    return col


# ---------------------------------------------------------------- the skies


def sky_day(D):
    x, y, z, el, az = geometry(D)
    col = ramp(el, [(-90, (58, 60, 66)), (-6, (120, 122, 126)), (0, (206, 204, 196)), (3, (200, 201, 200)),
                    (14, (168, 178, 194)), (40, (124, 142, 174)), (90, (98, 116, 154))])
    horizon = ramp(np.zeros_like(el), [(-1, (206, 204, 196)), (1, (206, 204, 196))])
    # a soft brightening on the sun's side of the sky (the sun's path leans to -Z)
    col = col + (np.maximum(-z, 0) ** 2 * 0.05 * ss(-2, 30, el))[..., None]
    a, lit, d = clouds(D, 11, 1.25, 0.5, 0.2, stretch=1.6, light=(0.0, -1.0))
    a2, lit2, _ = clouds(D, 31, 3.2, 0.32, 0.25, stretch=3.0, warp=0.4, light=(0.0, -1.0), lift=0.3)
    fade = ss(-0.5, 7.0, el)
    body = mix(C((126, 130, 148)), C((236, 230, 216)), lit ** 1.3)
    body = mix(body, C((170, 172, 182)), 0.25 * (1 - ss(0, 12, el)))  # far clouds sit in the haze
    col = mix(col, body, a * fade * 0.92)
    col = mix(col, mix(C((150, 156, 172)), C((226, 222, 212)), lit2), a2 * ss(4, 20, el) * 0.45)
    col = put_land(col, el, az, horizon, C((150, 152, 156)), 0.18, 0.34, 0.3,
                   below=ramp(el, [(-90, (54, 56, 62)), (-14, (92, 96, 100)), (0, (140, 142, 144))]))
    return finish(col, D, 3, 0.02)


def sky_dusk(D):
    x, y, z, el, az = geometry(D)
    S = SUNSET
    cs = np.clip(D @ S.astype(np.float32), -1, 1)
    toward = (cs + 1) / 2                      # 1 at the sun, 0 opposite
    sun_glow = np.maximum(cs, 0) ** 3
    base = ramp(el, [(-90, (12, 10, 16)), (-4, (40, 30, 46)), (0, (96, 66, 96)), (6, (92, 62, 100)),
                     (18, (66, 50, 98)), (45, (42, 37, 80)), (90, (33, 30, 66))])
    # the warm side: candle gold at the horizon, crimson above, fading out by ~45 degrees
    warm = ramp(el, [(-90, (30, 18, 18)), (-3, (120, 70, 50)), (0, (240, 196, 118)), (3, (236, 168, 96)),
                     (9, (206, 92, 78)), (18, (150, 52, 72)), (34, (92, 44, 82)), (90, (40, 30, 64))])
    col = mix(base, warm, np.clip(toward ** 2.2 * 1.15, 0, 1) * ss(70, 0, el))
    col = col + C(GOLD)[None, None, :] * (sun_glow ** 4 * 0.55 * ss(25, -1, el))[..., None]
    # opposite the sun: a pink belt over the cool earth shadow
    anti = np.maximum(-cs, 0) ** 1.5
    belt = np.exp(-((el - 9.0) / 5.0) ** 2) * anti
    col = mix(col, C((168, 108, 132)), belt * 0.45)
    col = mix(col, C((48, 46, 86)), anti * ss(7, 0, el) * (el > -2) * 0.55)
    horizon = mix(C((96, 66, 96)), C((240, 196, 118)), toward ** 3)
    # long streaky clouds, rimmed gold toward the sun
    sx, sz = S[0], S[2]
    a, lit, d = clouds(D, 21, 1.1, 0.46, 0.18, stretch=4.0, warp=0.5, light=(sx, sz))
    a2, lit2, _ = clouds(D, 41, 2.6, 0.3, 0.2, stretch=6.0, warp=0.3, light=(sx, sz), lift=0.28)
    shadow = mix(C((50, 34, 60)), C((84, 44, 62)), toward)
    rim = mix(C((150, 70, 92)), C((250, 206, 130)), toward ** 1.5)
    body = mix(shadow, rim, lit ** 1.6 * (0.35 + 0.65 * toward))
    # the deck thins out smoothly overhead (no hole), keeping the moon's sky clean
    fade = ss(-0.5, 5.0, el) * (0.25 + 0.75 * ss(70, 20, el)) * (0.4 + 0.6 * toward)
    col = mix(col, body, a * fade * 0.9)
    col = mix(col, mix(C((70, 50, 90)), C((236, 150, 110)), lit2 * toward), a2 * ss(3, 18, el) * ss(60, 25, el) * 0.45)
    land_c = mix(C((30, 20, 34)), C((60, 30, 40)), toward)
    col = put_land(col, el, az, horizon, land_c, 0.35, 0.6, 0.78,
                   win_rgb=GOLD, win_amt=0.25,
                   below=ramp(el, [(-90, (10, 8, 14)), (-14, (28, 20, 30))]))
    return finish(col, D, 4, 0.03)


def _night_base(D):
    x, y, z, el, az = geometry(D)
    col = ramp(el, [(-90, (6, 5, 9)), (-5, (12, 12, 20)), (0, (42, 50, 88)), (2.5, (38, 44, 80)),
                    (10, (24, 27, 52)), (30, (13, 14, 30)), (60, (9, 9, 20)), (90, (7, 6, 14))])
    # the glow of the town behind its own roofs, warmest over the big east cluster
    tg = np.exp(-((az - 88.0 + 180) % 360 - 180) ** 2 / (2 * 26.0 ** 2)) * np.exp(-np.maximum(el, 0) / 4.0)
    col = col + C((52, 40, 46))[None, None, :] * (tg * 0.45)[..., None]
    horizon = C((42, 50, 88))
    # thin moonlit wisps, low in the sky so the moon's path stays clean
    a, lit, d = clouds(D, 51, 1.6, 0.34, 0.22, stretch=3.5, warp=0.55, light=(0.0, -1.0))
    fade = ss(-0.5, 4.0, el) * ss(50, 14, el)
    body = mix(C((22, 24, 42)), C((84, 92, 128)), lit ** 2)
    col = mix(col, body, a * fade * 0.55)
    return col, horizon, (x, y, z, el, az)


def _night_land(col, horizon, g):
    x, y, z, el, az = g
    return put_land(col, el, az, horizon, C((9, 8, 14)), 0.32, 0.55, 0.7, win_rgb=GOLD, win_amt=0.55,
                    below=ramp(el, [(-90, (5, 4, 8)), (-14, (10, 9, 15))]))


def sky_night(D):
    col, horizon, g = _night_base(D)
    col = _night_land(col, horizon, g)
    return finish(col, D, 5, 0.035)


def sky_night_blue(D):
    col, horizon, g = _night_base(D)
    x, y, z, el, az = g
    # a faint aurora-like band on the +Z side, away from the moon's path; curtains hang from a wandering lower edge
    ar = np.radians(az)
    circ = np.stack([np.sin(ar) * 2.2, np.cos(ar) * 2.2, np.zeros_like(ar)], -1)
    wander = fbm3(circ + 3.3, 3, 61)
    low = 15.0 + 12.0 * np.sin(ar * 1.0 + 1.2) * 0.5 + (wander - 0.5) * 16.0
    t = (el - low) / 22.0
    curtain = ss(-0.04, 0.05, t) * np.exp(-np.maximum(t, 0) * 2.6) * (t < 1.6)
    rays = fbm3(np.stack([np.sin(ar) * 46, np.cos(ar) * 46, el * 0.05], -1), 4, 71)
    rays = 0.35 + 0.95 * ss(0.35, 0.75, rays)
    side = ss(-0.15, 0.55, z / np.maximum(np.sqrt(x * x + z * z), 1e-4))  # +Z
    breaks = ss(0.3, 0.6, fbm3(circ * 0.8 + 7.7, 3, 81))
    k = curtain * rays * side * breaks * ss(-1, 3, el)
    hue = np.clip(t * 1.5, 0, 1)
    acol = mix(C((96, 196, 210)), C(INKBLUE), ss(0.0, 0.45, hue))
    acol = mix(acol, C((126, 96, 206)), ss(0.45, 1.0, hue))
    col = col + acol * (k * 0.36)[..., None]
    col = _night_land(col, horizon, g)
    return finish(col, D, 6, 0.035)


def sky_storm(D):
    x, y, z, el, az = geometry(D)
    col = ramp(el, [(-90, (16, 16, 22)), (-5, (34, 34, 42)), (0, (86, 88, 100)), (3, (74, 76, 90)),
                    (20, (52, 54, 68)), (90, (36, 36, 48))])
    # a thin, cold break in the cloud on the south-west horizon
    brk = np.exp(-(((az - 228.0 + 180) % 360 - 180) / 30.0) ** 2) * np.exp(-((el - 2.5) / 2.2) ** 2)
    col = col + C((150, 150, 158))[None, None, :] * (brk * 0.45)[..., None]
    horizon = C((86, 88, 100))
    a, lit, d = clouds(D, 91, 0.7, 0.8, 0.32, stretch=1.15, warp=0.35, light=(0.0, -1.0), octaves=6, lift=0.22)
    body = mix(C((26, 26, 36)), C((92, 94, 110)), lit ** 1.4)
    body = mix(body, C((58, 60, 72)), 0.4 * (1 - ss(0, 14, el)))
    col = mix(col, body, a * ss(-0.5, 3.0, el))
    a2, lit2, _ = clouds(D, 97, 1.6, 0.55, 0.3, stretch=1.4, warp=0.3, light=(0.0, -1.0), lift=0.35)
    col = mix(col, mix(C((20, 20, 28)), C((70, 72, 86)), lit2), a2 * ss(2, 12, el) * 0.55)
    # rain curtains: tall soft shafts near the horizon
    ar = np.radians(az)
    shafts = fbm3(np.stack([np.sin(ar) * 14, np.cos(ar) * 14, el * 0.02], -1), 3, 99)
    rain = ss(0.5, 0.75, shafts) * ss(18, 2, el) * ss(-2, 1, el)
    col = mix(col, C((44, 46, 58)), rain * 0.45)
    col = put_land(col, el, az, horizon, C((22, 22, 30)), 0.28, 0.5, 0.55,
                   below=ramp(el, [(-90, (12, 12, 16)), (-14, (24, 24, 30))]))
    return finish(col, D, 7, 0.03)


SKIES = {"Day": sky_day, "Dusk": sky_dusk, "Night": sky_night, "NightBlue": sky_night_blue, "Storm": sky_storm}

# The 2.36 sets (sky-2360): tools/vfx/skies2360.py paints Dawn, the B-style nights (Night, NightNew, NightCrimson,
# NightBlue), the restyled Storm and the Winter/Spring/Summer/Nightmare event skies. Day and Dusk stay as painted above
# (their 2026-11-13 uploads stay live); the 2.16 Night/NightBlue/Storm painters above are kept only as the Storm base.
sys.modules.setdefault("make_skyboxes", sys.modules[__name__])  # so skies2360's `import make_skyboxes` gets this module
sys.path.insert(0, HERE)
import skies2360  # noqa: E402

SKIES_216 = dict(SKIES)
SKIES = {"Day": sky_day, "Dusk": sky_dusk, **skies2360.SETS}


# ---------------------------------------------------------------- preview: re-project the written faces


def load_faces(name):
    return {f: np.asarray(Image.open(os.path.join(OUT, f"NHSky{name}_{f}.png")).convert("RGB"), np.float32) / 255.0
            for f in ORDER}


def sample_cube(faces, D):
    """Look the written face images up through the Roblox mapping (bilinear, clamped at each face's edge)."""
    out = np.zeros(D.shape, np.float32)
    best = np.full(D.shape[:-1], -1.0, np.float32)
    pick = np.empty(D.shape[:-1], dtype=object)
    for name, (f, r, d) in FACES.items():
        fd = D @ np.array(f, np.float32)
        m = fd > best
        best = np.where(m, fd, best)
        pick[m] = name
    for name, (f, r, d) in FACES.items():
        m = pick == name
        if not m.any():
            continue
        Dm = D[m]
        fd = Dm @ np.array(f, np.float32)
        u = (Dm @ np.array(r, np.float32)) / fd
        v = (Dm @ np.array(d, np.float32)) / fd
        img = faces[name]
        n = img.shape[0]
        px = np.clip((u + 1) / 2 * n - 0.5, 0, n - 1.001)
        py = np.clip((v + 1) / 2 * n - 0.5, 0, n - 1.001)
        x0, y0 = px.astype(int), py.astype(int)
        fx, fy = (px - x0)[:, None], (py - y0)[:, None]
        c = (img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy) + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy
        out[m] = c
    return out


def view(faces, yaw, pitch, fov=95, w=640, h=360):
    """A pinhole camera: yaw 0 looks at -Z, 90 at +X; pitch up is positive."""
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    fwd = np.array([sy * cp, sp, -cy * cp], np.float32)
    right = np.array([cy, 0, sy], np.float32)
    up = np.cross(right, fwd)
    t = math.tan(math.radians(fov) / 2)
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = (np.arange(h) + 0.5) / h * 2 - 1
    X, Y = np.meshgrid(xs * t, -ys * t * h / w)
    D = fwd + X[..., None] * right + Y[..., None] * up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    return sample_cube(faces, D)


def panorama(faces, w=1440, h=360, el_top=60, el_bot=-30):
    az = np.radians((np.arange(w) + 0.5) / w * 360)
    el = np.radians(el_top - (np.arange(h) + 0.5) / h * (el_top - el_bot))
    A, E = np.meshgrid(az, el)
    D = np.stack([np.sin(A) * np.cos(E), np.sin(E), -np.cos(A) * np.cos(E)], -1).astype(np.float32)
    return sample_cube(faces, D)


def seam_report(faces):
    """For every face edge: the mean jump across the seam vs the mean step one pixel inside it (both in 0..255)."""
    n = faces["Ft"].shape[0]
    worst = 0.0
    lines = []
    s = (np.arange(n, dtype=np.float32) + 0.5) / n * 2 - 1
    for name, (f, r, d) in FACES.items():
        f, r, d = (np.array(v, np.float32) for v in (f, r, d))
        img = faces[name]
        for edge, (uu, vv, inner) in {
            "top": (s, np.full(n, -1.0), lambda im: (im[0], im[1])),
            "bottom": (s, np.full(n, 1.0), lambda im: (im[-1], im[-2])),
            "left": (np.full(n, -1.0), s, lambda im: (im[:, 0], im[:, 1])),
            "right": (np.full(n, 1.0), s, lambda im: (im[:, -1], im[:, -2])),
        }.items():
            e0, e1 = inner(img)
            # the neighbour's pixel half a pixel past this edge
            px = 1.0 / n
            ou = uu + np.sign(uu) * px * (np.abs(uu) == 1)
            ov = vv + np.sign(vv) * px * (np.abs(vv) == 1)
            Dn = f + ou[:, None] * r + ov[:, None] * d
            Dn /= np.linalg.norm(Dn, axis=-1, keepdims=True)
            nb = sample_cube(faces, Dn[None])[0]
            jump = float(np.abs(nb - e0).mean() * 255)
            step = float(np.abs(e1 - e0).mean() * 255)
            worst = max(worst, jump - step)
            lines.append(f"{name}.{edge}: across {jump:.2f}  inside {step:.2f}")
    return worst, lines


def label(img, text, size=22):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("georgia.ttf", size)
    except OSError:
        font = ImageFont.load_default(size=size)
    dr.text((12, 8), text, font=font, fill=BONE, stroke_width=2, stroke_fill=INK)
    return im


def preview(names):
    os.makedirs(PREVIEW, exist_ok=True)
    rows = []
    report = []
    for name in names:
        faces = load_faces(name)
        worst, lines = seam_report(faces)
        report.append(f"== NHSky{name}: worst seam excess {worst:.2f}/255 (across-seam jump minus the step inside the face)")
        report += ["   " + l for l in lines]
        pano = label(panorama(faces), f"NHSky{name}  360 panorama, -30 to +60 degrees  (0 = -Z, 90 = +X)")
        # corners and the zenith: where seams would show
        v1 = label(view(faces, 45, 30, w=480, h=360), "corner Ft/Lf/Up", 18)
        v2 = label(view(faces, 225, -20, w=480, h=360), "corner Bk/Rt/Dn", 18)
        v3 = label(view(faces, 0, 89, fov=110, w=480, h=360), "zenith (Up)", 18)
        strip = Image.new("RGB", (1440, 360 + 360), INK)
        strip.paste(pano, (0, 0))
        strip.paste(v1, (0, 360))
        strip.paste(v2, (480, 360))
        strip.paste(v3, (960, 360))
        strip.save(os.path.join(PREVIEW, f"NHSky{name}_preview.png"))
        rows.append(strip)
    sheet = Image.new("RGB", (1440, sum(r.height for r in rows) + 8 * len(rows)), INK)
    yy = 0
    for r in rows:
        sheet.paste(r, (0, yy))
        yy += r.height + 8
    sheet.save(os.path.join(PREVIEW, "NHSkies_Preview.png"))
    with open(os.path.join(PREVIEW, "seams.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(l for l in report if l.startswith("==")))


def render_face(job):
    name, face = job
    img = SKIES[name](face_dirs(face, N))
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(
        os.path.join(OUT, f"NHSky{name}_{face}.png"), optimize=True)
    return f"NHSky{name}_{face}.png"


def main():
    from multiprocessing import Pool
    os.makedirs(OUT, exist_ok=True)
    names = [n for n in SKIES if not ONLY or n in ONLY]
    jobs = [(n, f) for n in names for f in ORDER]
    workers = max(1, min(len(jobs), int(os.environ.get("NH_SKY_WORKERS", "6"))))
    with Pool(workers) as pool:  # about 1.5 min a face at 1024 on one core
        for done in pool.imap_unordered(render_face, jobs):
            print(done, flush=True)
    preview(names)


if __name__ == "__main__":
    main()
