"""PBR-style material bake for classic clothing templates (1.71 admin kit).

Roblox's Shirt / Pants templates take one colour image: no normal, roughness or metalness maps (SurfaceAppearance
only works on MeshParts). So the materials are baked in. Every pixel carries
    albedo, height, roughness, metalness, specular, sheen
painted as material layers (wool twill, velvet, satin, leather, brass, silver, linen, knit, embroidery...). Then each of
the 18 template faces is lit on its own:
    normals from the height map (edge-replicated inside the face, so nothing bleeds across a seam),
    a key light from above and toward the viewer (symmetric left/right, so the corners of adjacent faces match),
    Lambert diffuse + GGX specular, a sky/ground environment for metals, velvet sheen, cavity AO,
    and short cast shadows under raised layers (lapels, straps, buttons, embroidery).
The result is saved through nhcloth.save(), which bleeds the margins (the 1.37.0 clean-edge fix).
"""
import numpy as np
from scipy import ndimage

import nhcloth
from nhcloth import R, W, H, TORSO_RING, ARM_FACES, ARM_UPS, ARM_DOWNS, rect_mask, shape, fabric_detail, noise

F32 = np.float32
YY, XX = np.mgrid[0:H, 0:W]
FACES = list(R)

KEY = np.array([0.0, -0.58, 0.81], F32)
KEY /= np.linalg.norm(KEY)
VIEW = np.array([0, 0, 1], F32)


def c3(col):
    return np.array(col, F32)


class Mat:
    """A material: albedo texture, height texture and constant lighting parameters."""

    def __init__(self, kind, col, rough, metal=0.0, spec=0.06, sheen=0.0, relief=1.0, seed=0, **tex):
        self.kind, self.col, self.rough, self.metal = kind, c3(col), rough, metal
        self.spec, self.sheen, self.relief, self.seed, self.tex = spec, sheen, relief, seed, tex

    def maps(self):
        k, s, col = self.kind, self.seed, self.col
        hgt = np.zeros((H, W), F32)
        d = fabric_detail(s, cloud=self.tex.get("cloud", 0.05), twill=0.0, grain=self.tex.get("grain", 0.025))
        if k == "wool":       # 2/2 twill: diagonal ridges
            tw = np.sin(2 * np.pi * (XX + YY) / self.tex.get("period", 4.0))
            hgt = 0.075 * tw + 0.05 * noise(H, W, s + 1, 0.8)
            d = d * (1 + 0.035 * tw)
        elif k == "velvet":
            hgt = 0.05 * noise(H, W, s + 1, 0.7)
            d = d * (1 + 0.05 * noise(H, W, s + 2, 3.0))
        elif k == "satin":
            hgt = 0.02 * noise(H, W, s + 1, 2.0)
        elif k == "leather":
            n = noise(H, W, s + 1, 0.9)
            hgt = 0.22 * np.clip(n, -1.5, 1.5) / 1.5
            d = d * (1 + 0.04 * n)
        elif k in ("brass", "silver", "metal"):
            hgt = 0.04 * noise(H, W, s + 1, 1.5)
        elif k == "linen":
            wv = np.sin(np.pi * XX / 1.0) * np.sin(np.pi * YY / 1.0)
            hgt = 0.06 * wv + 0.04 * noise(H, W, s + 1, 0.6)
        elif k == "knit":     # vertical ribs of V stitches
            ph = (XX % 4) / 4.0
            hgt = 0.25 * np.cos(2 * np.pi * ph) + 0.08 * np.sin(2 * np.pi * (YY / 3.0 + np.abs(ph - 0.5)))
        elif k == "embroidery":   # satin-stitch thread, raised
            hgt = 0.08 * np.sin(2 * np.pi * (XX - YY) / 2.0)
        elif k == "lace":
            hgt = 0.1 * noise(H, W, s + 1, 0.7)
        elif k == "fur":
            hgt = 0.2 * noise(H, W, s + 1, 0.6)
        alb = np.clip(col[None, None] * d[..., None], 0, 255)
        return alb, hgt * self.relief


class Canvas:
    def __init__(self):
        self.alb = np.zeros((H, W, 3), F32)
        self.h = np.zeros((H, W), F32)
        self.rough = np.full((H, W), 0.8, F32)
        self.metal = np.zeros((H, W), F32)
        self.spec = np.full((H, W), 0.05, F32)
        self.sheen = np.zeros((H, W), F32)
        self.a = np.zeros((H, W), F32)
        self._cache = {}

    def _maps(self, mat):
        if getattr(mat, "_m", None) is None:
            mat._m = mat.maps()
        return mat._m

    def paint(self, mask, mat, lift=0.0, ride="avg", alpha=255.0):
        """Lay a material over mask (float 0..1). ride: "avg" sits on the smoothed height below (a strap over folds),
        "keep" adds to the exact height below (stitching), "flat" starts from 0 (a base layer). lift raises it."""
        m = np.clip(np.asarray(mask, F32), 0, 1)
        alb, hgt = self._maps(mat)
        base = ndimage.uniform_filter(self.h, 5) if ride == "avg" else (self.h if ride == "keep" else 0.0)
        newh = base + hgt + lift
        self.h = self.h * (1 - m) + newh * m
        mm = m[..., None]
        self.alb = self.alb * (1 - mm) + alb * mm
        for attr, v in (("rough", mat.rough), ("metal", mat.metal), ("spec", mat.spec), ("sheen", mat.sheen)):
            setattr(self, attr, getattr(self, attr) * (1 - m) + v * m)
        self.a = self.a * (1 - m) + alpha * m
        return self

    def raise_(self, mask, amount, blur=0.0):
        m = np.clip(np.asarray(mask, F32), 0, 1)
        if blur:
            m = ndimage.gaussian_filter(m, blur)
        self.h = self.h + m * amount
        return self

    def tint(self, mask, factor):
        m = np.clip(np.asarray(mask, F32), 0, 1)[..., None]
        self.alb = np.clip(self.alb * (1 - m + m * factor), 0, 255)
        return self

    def clear(self, mask):
        m = np.asarray(mask) > 0.5
        self.a[m] = 0
        return self


# ---------------------------------------------------------------- shaping
def folds(cv, mask, period=14, amp=0.6, wobble=3.0, seed=0, taper=None, angle=0.0):
    """Draped fabric folds: soft ridges (height) along the fall of the cloth, phase per face (none on a seam)."""
    m = np.clip(np.asarray(mask, F32), 0, 1)
    rng = np.random.default_rng(seed)
    ph = np.zeros((H, W), F32)
    for n in FACES:
        x, y, w, hh = R[n]
        fm = rect_mask([n])
        ph[fm] = (XX - x)[fm] + 0.5
    wob = wobble * np.sin(YY / 23.0 + rng.uniform(0, 6)) + wobble * 0.25 * np.sin(YY / 11.0 + rng.uniform(0, 6))
    f = np.sin(2 * np.pi * (ph + wob + angle * YY) / period)
    f = np.sign(f) * np.abs(f) ** 0.7            # rounder crests, tighter valleys
    if taper is not None:
        f = f * taper
    cv.h = cv.h + f * amp * m
    return cv


def cinch(cv, mask, y0, y1, amp=0.5, period=6):
    """Gathered fabric between y0 (tight) and y1 (loose), e.g. under a belt."""
    t = np.clip((YY - y0) / max(1, y1 - y0), 0, 1)
    return folds(cv, np.asarray(mask, F32) * (1 - t) * ((YY >= y0) & (YY <= y1)), period=period, amp=amp, wobble=0.5)


def dome(cv, mask, height=1.0, blur=1.2):
    """Round a raised shape: highest in its middle, falling to its edge (buttons, studs, cords)."""
    m = np.clip(np.asarray(mask, F32), 0, 1)
    dt = ndimage.distance_transform_edt(m > 0.5)
    mx = max(dt.max(), 1)
    prof = np.sqrt(np.clip(dt / min(mx, 3.0), 0, 1))
    cv.h = cv.h + ndimage.gaussian_filter(prof * height, blur) * (m > 0.02)
    return cv


def seam(cv, pts, width=1, depth=0.35, col_factor=0.82):
    """A sewn seam: a narrow groove with a slight ridge each side."""
    g = np.clip(shape(lambda d: d.line(pts, fill=255, width=width)), 0, 1)
    ridge = np.clip(ndimage.gaussian_filter(g, 1.2) * 2.2 - g, 0, 1)
    cv.h = cv.h - g * depth + ridge * depth * 0.4
    cv.tint(g, col_factor)
    return cv


def topstitch(cv, pts, mat, on=2, off=2, lift=0.15):
    m = shape(lambda d: nhcloth.dashed_poly(d, pts, on=on, off=off, fill=255, width=1))
    cv.paint(m, mat, lift=lift, ride="keep")
    return cv


# ---------------------------------------------------------------- bake
def _pad(a, p):
    return np.pad(a, [(p, p), (p, p)] + [(0, 0)] * (a.ndim - 2), mode="edge")


def bake(cv, bump=8.0, ambient=0.42, key=0.78, ao=0.6, shadow=0.5, round_=0.05):
    """Light every face separately; returns an RGBA float array for nhcloth.save."""
    out = np.zeros((H, W, 4), F32)
    out[..., 3] = cv.a
    sky, ground = c3((255, 236, 205)), c3((40, 30, 30))
    for n in FACES:
        x, y, w, hh = R[n]
        p = 6
        sl = (slice(y, y + hh), slice(x, x + w))
        hgt = _pad(cv.h[sl], p)
        alb = cv.alb[sl] / 255.0
        rough, metal, spec, sheen = (getattr(cv, k)[sl] for k in ("rough", "metal", "spec", "sheen"))
        gy, gx = np.gradient(hgt * bump / 4.0)
        nrm = np.dstack([-gx, -gy, np.ones_like(gx)])
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        nrm = nrm[p:-p, p:-p]
        # cavity AO and short downward cast shadows from raised layers (light from the top)
        hb = ndimage.gaussian_filter(hgt, 3.0)[p:-p, p:-p]
        hc = hgt[p:-p, p:-p]
        occ = np.clip((hb - hc) * 0.9, 0, 1)
        sh = np.zeros_like(hc)
        for dy, wgt in ((1, 0.5), (2, 0.35), (3, 0.2)):
            above = hgt[p - dy:p - dy + hh, p:-p]
            sh = np.maximum(sh, np.clip((above - hc - 0.15) * wgt, 0, 1))
        AO = np.clip(1 - occ * ao - sh * shadow, 0.2, 1)
        nl = np.clip((nrm * KEY).sum(-1), 0, 1)
        diffuse = (ambient + key * nl) * AO
        # GGX specular
        hv = KEY + VIEW
        hv /= np.linalg.norm(hv)
        nh = np.clip((nrm * hv).sum(-1), 0, 1)
        r2 = np.maximum(rough, 0.06) ** 4
        D = r2 / (np.pi * (nh * nh * (r2 - 1) + 1) ** 2)
        D = D / (1.0 / (np.pi * np.maximum(r2, 1e-4)))   # 1 at the peak
        F0 = alb * metal[..., None] + 0.04 * (1 - metal[..., None])
        specular = D[..., None] * F0 * (spec[..., None] * 6) * nl[..., None] * AO[..., None]
        # environment for metals: bright above, dark below, by normal
        env = sky * (0.5 - 0.5 * nrm[..., 1:2]) + ground * (0.5 + 0.5 * nrm[..., 1:2])
        env = env / 255.0 * (0.35 + 0.65 * (1 - rough[..., None]))
        metal_col = alb * env * 1.25 * AO[..., None]
        diel = alb * diffuse[..., None]
        sheen_c = sheen[..., None] * np.clip(1 - nrm[..., 2:3], 0, 1) ** 0.6 * 1.8 * alb ** 0.6
        col = diel * (1 - metal[..., None]) + metal_col * metal[..., None] + specular + sheen_c
        # gentle face rounding (symmetric, no dark edge: matches the 1.37.0 rule)
        xr = (np.arange(w) - (w - 1) / 2) / (w / 2)
        col = col * (1 - round_ * xr[None, :, None] ** 2)
        out[y:y + hh, x:x + w, :3] = np.clip(col, 0, 1) * 255
    # margins keep albedo (they're replaced by the bleed on save anyway)
    inside = rect_mask(FACES)
    out[~inside, :3] = cv.alb[~inside]
    return out


def save(cv, name, **kw):
    (nhcloth.OUT / "kits").mkdir(parents=True, exist_ok=True)
    c = bake(cv, **kw)
    if name.startswith("pants_"):
        c[..., 3] = np.where(rect_mask(TORSO_RING + ["T_UP"]) & (YY < 178), 0, c[..., 3])
    return nhcloth.save(c, f"kits/{name}")
