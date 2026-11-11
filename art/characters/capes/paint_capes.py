"""Paint the admin capes' PBR maps (2048: color, normal, roughness, metalness) in each cape's own UV atlas.

    python paint_capes.py [Set ...]       (after nh_admin_capes.py has written layout/<Set>.json and bake/<Set>_ao.png)

Every island is painted in studs: the cape panels from the per-row widths and per-column lengths the builder measured,
so the weave, trims and embroidery keep their real size and shape from the neckline to the hem. Heights are in studs
and become a tangent-space normal map (OpenGL, +Y up). Baked AO darkens the folds. Palette: crimson #600E1A, black,
brass; no blood.
Out: E:/NH-Work/capes/maps/NHCape_<Set>_<color|normal|roughness|metalness>.png
"""
import json, math, os, sys, zlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

WORK = "E:/NH-Work/capes"
OUT = os.path.join(WORK, "maps")
os.makedirs(OUT, exist_ok=True)
FONT = "C:/Windows/Fonts/georgiab.ttf"


def c255(*rgb):
    return np.array(rgb, np.float32) / 255.0


def noise(rng, shape, sigma):
    g = rng.standard_normal(shape).astype(np.float32)
    g = ndimage.gaussian_filter(g, sigma, mode="wrap")
    return g / (g.std() + 1e-6)


def band(d, lo, hi, soft=0.004):
    """1 inside lo..hi (studs), soft edges"""
    return np.clip((d - lo) / soft + 0.5, 0, 1) * np.clip((hi - d) / soft + 0.5, 0, 1)


def line(d, at, w, soft=0.003):
    return band(d, at - w / 2, at + w / 2, soft)


class Island:
    """pixel box of one UV island with stud coordinates for every pixel"""

    def __init__(self, lay, name, size=None):
        S = lay["atlas"]
        u0, v0, u1, v1 = lay["islands"][name]
        self.x0, self.x1 = int(round(u0 * S)), int(round(u1 * S))
        self.y0, self.y1 = int(round((1 - v1) * S)), int(round((1 - v0) * S))
        self.w, self.h = self.x1 - self.x0, self.y1 - self.y0
        pad = lay["pad"] * S
        xs = (np.arange(self.w) + 0.5 - pad) / max(1.0, self.w - 2 * pad)
        ys = (np.arange(self.h) + 0.5 - pad) / max(1.0, self.h - 2 * pad)
        self.fu, self.fv = np.meshgrid(np.clip(xs, 0, 1), np.clip(ys, 0, 1))
        st = lay.get("outer_stats") or {}
        if size is None and st.get("row_w"):
            rw, cl = np.array(st["row_w"]), np.array(st["col_l"])
            RW = np.interp(self.fv, np.linspace(0, 1, len(rw)), rw)
            CL = np.interp(self.fu, np.linspace(0, 1, len(cl)), cl)
            self.X = (self.fu - 0.5) * RW          # from the back centre, along the cloth
            if st.get("col_s"):                    # true running length down each column at each row
                cs = np.array(st["col_s"], np.float64)       # [column][row]
                ci = self.fu * (cs.shape[0] - 1); rj = self.fv * (cs.shape[1] - 1)
                self.Y = ndimage.map_coordinates(cs, [ci, rj], order=1, mode="nearest").astype(np.float32)
            else:
                self.Y = self.fv * CL
            self.Yb = CL - self.Y                  # up from the hem
            self.Xl, self.Xr = self.fu * RW, (1 - self.fu) * RW
            self.sx = np.maximum(np.abs(np.gradient(self.X, axis=1)), 1e-5)   # studs per pixel, locally
            self.sy = np.maximum(np.abs(np.gradient(self.Y, axis=0)), 1e-5)
        else:
            W, H = size
            self.X = (self.fu - 0.5) * W
            self.Y = self.fv * H
            self.Yb = (1 - self.fv) * H
            self.Xl, self.Xr = self.fu * W, (1 - self.fu) * W
            self.sx = np.full_like(self.fu, W / self.w)
            self.sy = np.full_like(self.fu, H / self.h)
        self.px = 1.0 / float(np.mean(self.sx))     # pixels per stud
        self.rng = np.random.default_rng(zlib.crc32((lay["key"] + name).encode()))

    def zeros(self, c=1):
        return np.zeros((self.h, self.w, c) if c > 1 else (self.h, self.w), np.float32)


# ------------------------------------------------------------------ cloth materials: (albedo, height, rough, metal)
def wool(I, col, period=0.032, amp=0.0018, rough=0.86):
    n1 = noise(I.rng, (I.h, I.w), 0.9)
    n2 = noise(I.rng, (I.h, I.w), max(2.0, 0.12 * I.px))
    tw = np.sin(2 * np.pi * (I.X + I.Y) / period)
    h = amp * (0.6 * tw + 0.35 * n1)
    a = col[None, None, :] * (1 + 0.05 * tw[..., None] + 0.045 * n2[..., None] + 0.03 * n1[..., None])
    r = rough + 0.04 * n1
    return a, h, r, np.zeros_like(h)


def velvet(I, col, rough=0.8):
    n1 = noise(I.rng, (I.h, I.w), 0.7)
    crush = noise(I.rng, (I.h, I.w), (max(2.0, 0.08 * I.px), max(2.0, 0.22 * I.px)))
    h = 0.0006 * n1 + 0.0012 * crush
    a = col[None, None, :] * (1 + 0.12 * crush[..., None] + 0.03 * n1[..., None])
    r = rough - 0.08 * crush
    return a, h, r, np.zeros_like(h)


def satin(I, col, rough=0.3):
    streak = noise(I.rng, (I.h, I.w), (0.8, max(6.0, 0.25 * I.px)))
    n1 = noise(I.rng, (I.h, I.w), 0.6)
    h = 0.0003 * n1 + 0.0004 * streak
    a = col[None, None, :] * (1 + 0.07 * streak[..., None])
    r = rough + 0.05 * streak
    return a, h, r, np.zeros_like(h)


def linen(I, col, period=0.024, rough=0.92, weather=0.0):
    n1 = noise(I.rng, (I.h, I.w), 0.8)
    wx = np.sin(2 * np.pi * I.X / period); wy = np.sin(2 * np.pi * I.Y / period)
    weave = wx * wy
    slub = noise(I.rng, (I.h, I.w), (0.7, max(8.0, 0.35 * I.px)))
    slub = np.clip(slub - 1.2, 0, None)
    h = 0.0012 * weave + 0.0008 * n1 + 0.0016 * slub
    a = col[None, None, :] * (1 + 0.05 * weave[..., None] + 0.05 * n1[..., None] + 0.12 * slub[..., None])
    r = rough + 0.03 * n1
    return a, h, r, np.zeros_like(h)


def metal(I, col, rough=0.34, scratch=0.06, hammered=0.0006):
    n1 = noise(I.rng, (I.h, I.w), 1.2)
    n2 = noise(I.rng, (I.h, I.w), 6.0)
    sc = noise(I.rng, (I.h, I.w), (0.5, 9.0))
    a = col[None, None, :] * (1 + 0.06 * n2[..., None] - 0.04 * np.clip(sc, 0, None)[..., None])
    r = rough + 0.08 * n2 + scratch * np.clip(sc - 1.5, 0, None)
    return a, hammered * n1, r, np.ones_like(n1)


def gem(I):
    a = np.broadcast_to(c255(132, 10, 30)[None, None, :], (I.h, I.w, 3)).copy()
    return a, np.zeros((I.h, I.w), np.float32), np.full((I.h, I.w), 0.06, np.float32), np.zeros((I.h, I.w), np.float32)


def gold_thread(I, mask, a, h, r, m, raise_=0.004, col=c255(206, 160, 82), stitch=0.012):
    """satin-stitch gold embroidery over cloth: raised, metallic, fine stitch lines"""
    st = 0.5 + 0.5 * np.sin(2 * np.pi * (I.X - I.Y) / stitch)
    mk = mask[..., None]
    a[:] = a * (1 - mk) + mk * col[None, None, :] * (0.82 + 0.25 * st[..., None])
    h += mask * (raise_ + 0.0012 * st)
    r[:] = r * (1 - mask) + mask * (0.36 + 0.08 * st)
    m[:] = m * (1 - mask) + mask * 0.85


def paint(I, mask, col, rough=None, metal_=None, raise_=0.0, a=None, h=None, r=None, m=None):
    mk = mask[..., None]
    a[:] = a * (1 - mk) + mk * col[None, None, :]
    if rough is not None:
        r[:] = r * (1 - mask) + mask * rough
    if metal_ is not None:
        m[:] = m * (1 - mask) + mask * metal_
    h += mask * raise_


# ------------------------------------------------------------------ motifs (drawn in studs, sampled per pixel)
def sample(img, I, cx, cy, size):
    """img: square float array covering size x size studs centred at (cx, cy) in island X/Y; bilinear"""
    N = img.shape[0]
    gx = ((I.X - cx) / size + 0.5) * N - 0.5
    gy = ((I.Y - cy) / size + 0.5) * N - 0.5
    return ndimage.map_coordinates(img, [gy, gx], order=1, mode="constant", cval=0.0).astype(np.float32)


def canvas(N=1024):
    im = Image.new("L", (N, N), 0)
    return im, ImageDraw.Draw(im)


def arr(im, blur=1.0):
    a = np.asarray(im, np.float32) / 255.0
    return ndimage.gaussian_filter(a, blur) if blur else a


def key_motif(N=1024):
    """the Warden's key over a crescent moon"""
    im, d = canvas(N)
    c = N / 2
    # crescent behind
    d.ellipse([c - 0.36 * N, c - 0.36 * N, c + 0.36 * N, c + 0.36 * N], fill=255)
    d.ellipse([c - 0.27 * N, c - 0.42 * N, c + 0.43 * N, c + 0.30 * N], fill=0)
    moon = arr(im)
    im, d = canvas(N)
    # key: bow ring, shaft, bit with two teeth
    d.ellipse([c - 0.12 * N, 0.1 * N, c + 0.12 * N, 0.34 * N], outline=255, width=int(0.045 * N))
    d.ellipse([c - 0.035 * N, 0.19 * N, c + 0.035 * N, 0.25 * N], fill=255)
    d.rectangle([c - 0.025 * N, 0.33 * N, c + 0.025 * N, 0.86 * N], fill=255)
    d.rectangle([c, 0.7 * N, c + 0.14 * N, 0.76 * N], fill=255)
    d.rectangle([c, 0.8 * N, c + 0.11 * N, 0.86 * N], fill=255)
    d.rectangle([c - 0.07 * N, 0.4 * N, c + 0.07 * N, 0.43 * N], fill=255)
    return moon, arr(im)


def crest_motif(N=1024):
    """the Council crest: a shield (border, field), crossed keys and a crescent, a ribbon reading CONCILIUM"""
    def shield(d, inset, fill):
        x0, x1, top, side_bot, tip = 0.2 + inset, 0.8 - inset, 0.08 + inset, 0.42, 0.72 - 1.4 * inset
        pts = [(x0, top), (x1, top), (x1, side_bot)]
        for k in range(1, 25):  # quadratic curve from the side down to the point, then back up the other side
            t = k / 24
            cxp, cyp = x1, tip - 0.08
            x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cxp + t * t * 0.5
            y = (1 - t) ** 2 * side_bot + 2 * (1 - t) * t * cyp + t * t * tip
            pts.append((x, y))
        pts += [(1 - x, y) for x, y in reversed(pts[3:-1])]
        pts += [(x0, side_bot)]
        d.polygon([(x * N, y * N) for x, y in pts], fill=fill)
    im, d = canvas(N); shield(d, 0.0, 255); outer = arr(im, 1.5)
    im, d = canvas(N); shield(d, 0.035, 255); inner = arr(im, 1.5)
    border = np.clip(outer - inner, 0, 1)
    im, d = canvas(N)
    c = N / 2
    # crossed keys (two rotated keys)
    for ang in (35, -35):
        k = Image.new("L", (N, N), 0); kd = ImageDraw.Draw(k)
        kd.ellipse([c - 0.06 * N, 0.2 * N, c + 0.06 * N, 0.32 * N], outline=255, width=int(0.022 * N))
        kd.rectangle([c - 0.013 * N, 0.31 * N, c + 0.013 * N, 0.62 * N], fill=255)
        kd.rectangle([c, 0.53 * N, c + 0.07 * N, 0.56 * N], fill=255)
        kd.rectangle([c, 0.585 * N, c + 0.055 * N, 0.615 * N], fill=255)
        k = k.rotate(ang, center=(c, 0.42 * N), resample=Image.BICUBIC)
        im.paste(255, mask=k)
    d = ImageDraw.Draw(im)
    # crescent above
    d.ellipse([c - 0.075 * N, 0.11 * N, c + 0.075 * N, 0.26 * N], fill=255)
    d.ellipse([c - 0.055 * N, 0.095 * N, c + 0.095 * N, 0.235 * N], fill=0)
    emblem = arr(im, 1.0) * inner
    # ribbon with the motto
    im, d = canvas(N)
    d.polygon([(0.08 * N, 0.76 * N), (0.92 * N, 0.76 * N), (0.86 * N, 0.81 * N), (0.92 * N, 0.87 * N),
               (0.08 * N, 0.87 * N), (0.14 * N, 0.81 * N)], fill=255)
    ribbon = arr(im, 1.2)
    im, d = canvas(N)
    f = ImageFont.truetype(FONT, int(0.07 * N))
    d.text((N / 2, 0.815 * N), "CONCILIUM", font=f, fill=255, anchor="mm")
    text = arr(im, 0.8)
    return dict(border=border, field=inner, emblem=emblem, ribbon=ribbon, text=text)


def damask_tile(N=512):
    """tone-on-tone tile: a diamond lattice of fine lines, a crescent and a small bat in each cell"""
    im, d = canvas(N)
    w = int(0.018 * N)
    for a, b in (((0, N / 2), (N / 2, 0)), ((N / 2, 0), (N, N / 2)), ((N, N / 2), (N / 2, N)), ((N / 2, N), (0, N / 2))):
        d.line([a, b], fill=255, width=w)
    c = N / 2
    d.ellipse([c - 0.13 * N, c - 0.2 * N, c + 0.13 * N, c + 0.06 * N], fill=255)
    d.ellipse([c - 0.09 * N, c - 0.23 * N, c + 0.17 * N, c + 0.03 * N], fill=0)
    bat = [(0.0, 0.0), (0.05, -0.04), (0.1, -0.02), (0.16, -0.08), (0.2, 0.0), (0.14, 0.0), (0.1, 0.04), (0.06, 0.02),
           (0.0, 0.07), (-0.06, 0.02), (-0.1, 0.04), (-0.14, 0.0), (-0.2, 0.0), (-0.16, -0.08), (-0.1, -0.02),
           (-0.05, -0.04)]
    d.polygon([(c + x * 0.8 * N, c + 0.17 * N + y * 0.8 * N) for x, y in bat], fill=255)
    for cx, cy in ((0, 0), (N, 0), (0, N), (N, N)):  # small four-point stars at the lattice nodes
        d.polygon([(cx, cy - 0.06 * N), (cx + 0.015 * N, cy), (cx, cy + 0.06 * N), (cx - 0.015 * N, cy)], fill=255)
        d.polygon([(cx - 0.06 * N, cy), (cx, cy + 0.015 * N), (cx + 0.06 * N, cy), (cx, cy - 0.015 * N)], fill=255)
    return arr(im, 1.0)


def tile_sample(tile, I, period):
    N = tile.shape[0]
    gx = (I.X / period % 1.0) * N
    gy = (I.Y / period % 1.0) * N
    return ndimage.map_coordinates(tile, [gy, gx], order=1, mode="wrap").astype(np.float32)


# ------------------------------------------------------------------ per-cape island painters
BRASS, SILVER = c255(196, 150, 72), c255(206, 206, 214)
CRIMSON = c255(96, 14, 26)


def edges_band(I, sides):
    """distance (studs) to the chosen edges of a cape panel: 'hem', 'left' (u=0), 'right' (u=1)"""
    ds = []
    if "hem" in sides:
        ds.append(I.Yb)
    if "left" in sides:
        ds.append(I.Xl)
    if "right" in sides:
        ds.append(I.Xr)
    return np.minimum.reduce(ds)


def mat_island(key, name, matname, I, lay):
    rng = I.rng
    if matname in ("brass",):
        return metal(I, BRASS)
    if matname in ("silver",):
        return metal(I, SILVER, rough=0.24, scratch=0.05)
    if matname == "gem":
        return gem(I)
    if matname == "bullion":
        a, h, r, m = metal(I, c255(206, 160, 82), rough=0.36)
        tw = np.sin(2 * np.pi * (I.fu * 40 + I.fv * 3))
        h = h + 0.003 * tw
        a *= (0.85 + 0.2 * (0.5 + 0.5 * tw))[..., None]
        return a, h, r, m
    if matname == "gold_cord":
        a, h, r, m = metal(I, c255(200, 156, 80), rough=0.4)
        tw = np.sin(2 * np.pi * (I.fu * 70 + I.fv * 4))
        h = h + 0.004 * tw
        a *= (0.8 + 0.25 * (0.5 + 0.5 * tw))[..., None]
        m *= 0.85
        return a, h, r, m
    if matname == "gold_rim":
        a, h, r, m = metal(I, c255(190, 148, 76), rough=0.42)
        return a, h, r, m * 0.8
    if matname == "brass_rim":
        return metal(I, BRASS, rough=0.42)
    if matname == "silver_rim":
        return metal(I, SILVER, rough=0.3)
    if matname == "warden_rim":
        return wool(I, c255(30, 28, 34))
    if matname == "reaper_rim":
        return linen(I, c255(30, 28, 31))

    # ---- Night Warden
    if matname in ("warden_wool", "warden_wool_collar"):
        a, h, r, m = wool(I, c255(38, 35, 42))
        if matname == "warden_wool":
            d = I.Yb
            for at in (0.05, 0.085):  # crimson piping above the hem
                pm = line(d, at, 0.011)
                paint(I, pm, c255(118, 18, 34), rough=0.5, raise_=0.0025, a=a, h=h, r=r, m=m)
            fr = np.minimum(I.Xl, I.Xr)  # brass thread down the front edges
            gold_thread(I, line(fr, 0.035, 0.012), a, h, r, m, raise_=0.002, col=c255(190, 146, 70))
            moon, key_ = key_motif()
            cy = 0.5 * float(np.interp(0.5, np.linspace(0, 1, len(lay["outer_stats"]["col_l"])), lay["outer_stats"]["col_l"]))
            mm = sample(moon, I, 0.0, cy, 0.72)
            km = sample(key_, I, 0.0, cy, 0.72)
            moon_only = np.clip(mm - km, 0, 1)
            paint(I, moon_only, c255(128, 20, 36), rough=0.5, raise_=0.002, a=a, h=h, r=r, m=m)
            edge = np.clip(ndimage.morphological_gradient(moon_only, size=5) * 1.5, 0, 1) * (1 - km)
            gold_thread(I, edge, a, h, r, m, raise_=0.0025)
            gold_thread(I, km, a, h, r, m)
        return a, h, r, m
    if matname == "crimson_silk":
        a, h, r, m = satin(I, CRIMSON, rough=0.34)
        return a, h, r, m

    # ---- Reaper
    if matname in ("reaper_linen", "reaper_linen_hood"):
        a, h, r, m = linen(I, c255(44, 41, 45))
        ash = c255(98, 93, 90)
        nd = noise(rng, (I.h, I.w), max(3.0, 0.1 * I.px))
        if matname == "reaper_linen":
            dust = np.clip(1 - I.Yb / 0.95, 0, 1) ** 1.6 * (0.55 + 0.2 * nd)
            a[:] = a * (1 - dust[..., None]) + ash[None, None, :] * dust[..., None] * (0.9 + 0.1 * nd[..., None])
            # fraying: loose vertical threads at the torn hem
            thr = np.clip(noise(rng, (I.h, I.w), (max(10.0, 0.25 * I.px), 0.6)) - 1.0, 0, None)
            fray = thr * np.clip(1 - I.Yb / 0.18, 0, 1)
            h += 0.002 * fray
            a *= (1 - 0.25 * np.clip(fray, 0, 1))[..., None]
            # mends: a few patches, stitched round in crimson thread
            pr = np.random.default_rng(77)
            for _ in range(5):
                px, py = pr.uniform(-1.8, 1.8), pr.uniform(0.7, 2.6)
                pw, ph = pr.uniform(0.22, 0.36), pr.uniform(0.18, 0.3)
                inside = band(I.X, px - pw / 2, px + pw / 2, 0.006) * band(I.Y, py - ph / 2, py + ph / 2, 0.006)
                a[:] = a * (1 - 0.35 * inside[..., None]) + 0.35 * inside[..., None] * c255(58, 54, 56)[None, None, :]
                h += 0.0015 * inside
                edge = np.maximum(line(np.abs(I.X - px), pw / 2 - 0.012, 0.012), line(np.abs(I.Y - py), ph / 2 - 0.012, 0.012))
                edge *= band(I.X, px - pw / 2 - 0.01, px + pw / 2 + 0.01, 0.004) * band(I.Y, py - ph / 2 - 0.01, py + ph / 2 + 0.01, 0.004)
                stitch = (np.sin(2 * np.pi * (I.X + I.Y) / 0.03) > 0.2).astype(np.float32)
                paint(I, edge * stitch, c255(110, 16, 30), rough=0.7, raise_=0.0015, a=a, h=h, r=r, m=m)
        # rot stains
        stain = np.clip(noise(rng, (I.h, I.w), max(4.0, 0.14 * I.px)) - 1.3, 0, None)
        a *= (1 - 0.3 * np.clip(stain, 0, 1))[..., None]
        r += 0.03 * stain
        return a, h, r, m
    if matname == "reaper_lining":
        return linen(I, c255(26, 24, 28))
    if matname == "reaper_cowl":
        a, h, r, m = linen(I, c255(46, 43, 47))
        roll = np.sin(2 * np.pi * (I.fu * 26 + I.fv * 1.5))
        h += 0.006 * roll
        a *= (0.9 + 0.1 * roll)[..., None]
        return a, h, r, m

    # ---- Duelist
    if matname == "duelist_velvet":
        a, h, r, m = velvet(I, c255(104, 14, 30), rough=0.78)
        d = edges_band(I, ("hem", "left", "right"))
        # along-edge coordinate: X near the hem, Y near the side edges
        along = np.where(I.Yb < np.minimum(I.Xl, I.Xr), I.X, I.Y)
        trim = np.maximum(line(d, 0.016, 0.01), line(d, 0.082, 0.008))
        vine_d = 0.049 + 0.017 * np.sin(2 * np.pi * along / 0.13)
        vine = np.clip(1 - np.abs(d - vine_d) / 0.0045, 0, 1)
        kk = np.floor(along / 0.065)
        ac = (kk + 0.5) * 0.065
        side = np.where(kk % 2 == 0, 1.0, -1.0)
        lc = 0.049 + 0.017 * np.sin(2 * np.pi * ac / 0.13) + side * 0.011
        leaf = np.clip(1 - (((along - ac) / 0.014) ** 2 + ((d - lc) / 0.006) ** 2), 0, 1)
        leaf = np.clip(leaf * 4, 0, 1)
        emb = np.clip(trim + vine + leaf, 0, 1) * (d < 0.095)
        gold_thread(I, emb.astype(np.float32), a, h, r, m, raise_=0.003)
        return a, h, r, m
    if matname == "black_satin":
        return satin(I, c255(18, 17, 21), rough=0.3)

    # ---- Captain
    if matname in ("captain_wool", "captain_wool_collar"):
        a, h, r, m = wool(I, c255(92, 13, 26), period=0.03, rough=0.82)
        if matname == "captain_wool":
            d = edges_band(I, ("hem", "left", "right"))
            along = np.where(I.Yb < np.minimum(I.Xl, I.Xr), I.X, I.Y)
            braid_w = np.where(I.Yb < np.minimum(I.Xl, I.Xr), 0.11, 0.07)
            inband = band(d, 0.012, braid_w, 0.004)
            zz = ((along / 0.034) + np.abs(d - braid_w / 2) / 0.034) % 1.0
            braid = inband * (0.55 + 0.45 * (zz < 0.5))
            a2, h2, r2, m2 = metal(I, BRASS, rough=0.38)
            bm = braid[..., None]
            a[:] = a * (1 - inband[..., None]) + a2 * bm
            h += inband * (0.003 + 0.0015 * (zz < 0.5)) + h2 * inband
            r[:] = r * (1 - inband) + r2 * inband
            m[:] = m * (1 - inband) + inband * 0.95
            paint(I, line(d, braid_w + 0.018, 0.012), c255(16, 14, 18), rough=0.8, raise_=0.001, a=a, h=h, r=r, m=m)
            # the Council crest on the back
            cl = lay["outer_stats"]["col_l"]
            cy = 0.42 * float(np.interp(0.5, np.linspace(0, 1, len(cl)), cl))
            cr = crest_motif()
            S_ = 1.3
            fld = sample(cr["field"], I, 0.0, cy, S_)
            paint(I, fld, c255(18, 15, 20), rough=0.82, raise_=0.0012, a=a, h=h, r=r, m=m)
            gold_thread(I, sample(cr["border"], I, 0.0, cy, S_), a, h, r, m, raise_=0.0035)
            gold_thread(I, sample(cr["emblem"], I, 0.0, cy, S_), a, h, r, m, raise_=0.003)
            rb = sample(cr["ribbon"], I, 0.0, cy, S_)
            gold_thread(I, rb, a, h, r, m, raise_=0.002, col=c255(190, 150, 80))
            tx = sample(cr["text"], I, 0.0, cy, S_) * rb
            paint(I, tx, c255(30, 8, 14), rough=0.7, raise_=-0.0015, a=a, h=h, r=r, m=m)
        return a, h, r, m
    if matname == "black_velvet":
        return velvet(I, c255(20, 17, 23), rough=0.82)

    # ---- Midnight Lord
    if matname in ("midnight_velvet", "midnight_velvet_collar"):
        a, h, r, m = velvet(I, c255(24, 19, 29), rough=0.8)
        dm = tile_sample(damask_tile(), I, 0.24)
        a *= (1 + 0.2 * dm)[..., None]
        r -= 0.2 * dm
        h += 0.0006 * dm
        if matname == "midnight_velvet":
            d = I.Yb
            paint(I, line(d, 0.035, 0.012), c255(150, 150, 160), rough=0.28, metal_=1.0, raise_=0.002, a=a, h=h, r=r, m=m)
            fr = np.minimum(I.Xl, I.Xr)
            paint(I, line(fr, 0.03, 0.012), c255(150, 150, 160), rough=0.28, metal_=1.0, raise_=0.002, a=a, h=h, r=r, m=m)
        return a, h, r, m
    if matname in ("crimson_satin", "crimson_satin_collar"):
        a, h, r, m = satin(I, c255(112, 15, 33), rough=0.27)
        if matname == "crimson_satin_collar":   # diamond quilting on the inside of the collar
            q1 = np.abs(((I.X + I.Y) / 0.11) % 1.0 - 0.5); q2 = np.abs(((I.X - I.Y) / 0.11) % 1.0 - 0.5)
            groove = np.clip(1 - np.minimum(q1, q2) / 0.06, 0, 1)
            h -= 0.0015 * groove
            a *= (1 - 0.2 * groove)[..., None]
            puff = (1 - groove) * 0.001
            h += puff
        return a, h, r, m
    raise KeyError(matname)


def default_size(name, I):
    """nominal stud sizes for islands that aren't measured cape panels"""
    aspect = I.w / max(1, I.h)
    base = {"collar_out": 0.45, "collar_in": 0.45, "hood_out": 0.9, "hood_in": 0.9, "cowl": 0.75, "fringe": 0.3,
            "rim": 0.05}.get(name, 0.35)
    return (base * aspect, base)


def build(key):
    lay = json.load(open(os.path.join(WORK, "layout", f"{key}.json")))
    S = lay["atlas"]
    A = np.zeros((S, S, 3), np.float32); A[:] = c255(30, 26, 32)
    R = np.full((S, S), 0.8, np.float32); Mt = np.zeros((S, S), np.float32)
    Nn = np.zeros((S, S, 3), np.float32); Nn[..., 2] = 1.0
    ao_path = os.path.join(WORK, "bake", f"{key}_ao.png")
    if os.path.exists(ao_path):
        im = Image.open(ao_path).convert("L")
        if im.size != (S, S):
            im = im.resize((S, S), Image.BICUBIC)
        ao = ndimage.gaussian_filter(np.asarray(im, np.float32) / 255.0, 1.2)
    else:
        ao = np.ones((S, S), np.float32)
    for name, matname in lay["mats"].items():
        if name not in lay["islands"]:
            continue
        measured = name in ("outer", "lining")
        I = Island(lay, name, None if measured else (1, 1))
        if not measured:
            I = Island(lay, name, default_size(name, I))
        a, h, r, m = mat_island(key, name, matname, I, lay)
        if name == "lining":
            pass
        # normal from height (studs): slopes per stud along the cloth
        gx = np.gradient(h, axis=1) / I.sx
        gy = np.gradient(h, axis=0) / I.sy
        n = np.stack([-gx, gy, np.ones_like(h)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        ys, xs = slice(I.y0, I.y1), slice(I.x0, I.x1)
        if name not in lay["no_ao"]:
            aoi = ao[ys, xs]
            a = a * (0.25 + 0.75 * aoi[..., None] ** 1.1)
            r = r + 0.05 * (1 - aoi)
        A[ys, xs] = a; R[ys, xs] = r; Mt[ys, xs] = m; Nn[ys, xs] = n
    def save(arr_, kind):
        Image.fromarray(np.clip(arr_ * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"NHCape_{key}_{kind}.png"))
    save(A, "color")
    save(Nn * 0.5 + 0.5, "normal")
    save(np.clip(R, 0.03, 1.0), "roughness")
    save(np.clip(Mt, 0, 1), "metalness")
    print(f"[paint] {key}: done")


if __name__ == "__main__":
    keys = sys.argv[1:] or ["WardenMantle", "ReaperShroud", "DuelistCape", "CaptainGreatcape", "MidnightCollar"]
    for k in keys:
        build(k)
