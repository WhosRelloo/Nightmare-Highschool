"""Shared helpers for the gender clothing kits (1.71): the schoolgirl kit and the civilian kit.

Clean edges (the 1.37.0 seam fix, applied to every kit template):
- nhcloth.save() bleeds every template: margins copy the nearest face pixel, and transparent
  pixels take the nearest visible colour, so filtering never pulls black or white into a seam.
- Nothing darkens a face's own outer edge (outline_of never counts it, face_seams is a no-op).
- Fold lines (pleats, darts, seams) are placed relative to each face, never on its first or last
  column, so no dark line runs down a corner of a limb or the torso. `pleats()` replaces
  female.pleated(), whose global x % 8 fold landed on the edge column of some faces.
"""
import numpy as np

import nhcloth
from nhextra import *  # noqa: F401,F403
from nhextra import YY, XX, CX, LEGS, FRONTS, BACKS, OUTERS, INNERS
from shirts_new import base_shirt, hem_line, mirror
from pants import school_shoes, socks, LEG_UPS, SHOE_TOP
from female import bow, scallops, lacing, skirt_shell, waistband, bare_legs, tights, mary_janes, neck_dist, fabric, LACE, LACE_EDGE

F32 = np.float32
KIT = nhcloth.OUT / "kits"

# palette: candlelit gothic, crimson #600E1A, black, brass
NH_CRIMSON = (96, 14, 26)
BRASS = (176, 138, 66)
BRASS_HI = (236, 206, 140)
INK = (14, 12, 14)
JET = (22, 20, 24)
CHAR = (48, 46, 52)
IVORY_B = (232, 226, 210)
CANDLE_G = (214, 172, 78)
WINE = (74, 10, 24)

NO_CREASE = set()


def save(c, name, creases=False):
    KIT.mkdir(parents=True, exist_ok=True)
    c = finish(c, creases=creases, seed=sum(map(ord, name)))
    if name.startswith("pants_"):
        # the upper torso of a pants template stays fully see-through (the source jeans kept it opaque
        # black, which showed as black edges under sheer or cropped tops)
        clear(c, rect_mask(TORSO_RING + ["T_UP"]) & (YY < 178))
        # the jeans' see-through panel reaches row 182 on the front, leaving 2 px slivers at the corners:
        # carry the waistband up to row 178 across the whole front instead
        x, y, w, h = R["T_F"]
        band = c[183, x:x + w].copy()
        if (band[:, 3] > 0).mean() > 0.9:
            c[178:183, x:x + w] = band[None]
    return nhcloth.save(c, f"kits/{name}")


BLOUSE_TEX = dict(cloud=0.022, twill=0.018, grain=0.02)


def blouse_fabric(seed, col=IVORY_B):
    return fabric(seed, col, **BLOUSE_TEX)


def cable_knit2(seed, col, period=20, twist=12):
    """Cable knit with smooth twisted ropes (diagonal twist), purl gutters and fine stitch texture.
    Cable columns are aligned to each face so a rope never splits across a body-part edge."""
    base = tint(fabric_detail(seed, cloud=0.035, twill=0.0, grain=0.03), col)
    ph = face_phase(TORSO_RING + ["T_UP"] + ARM_FACES + ARM_UPS)
    ph = np.where(ph < 0, XX, ph)
    p = (ph + period // 2 - 2) % period
    t = (p - (period - 1) / 2) / ((period - 6) / 2)          # -1..1 across the rope
    inside = np.abs(t) <= 1
    phase = YY / twist + np.where(t < 0, 0.0, 0.5)
    strand = np.cos(np.pi * t / 2) * (0.55 + 0.45 * np.cos(2 * np.pi * (phase - 0.25 * t)))
    stitch = 1 - 0.05 * ((YY % 3) == 0)
    f = np.where(inside, 0.86 + 0.26 * strand, 0.8 * (1 - 0.06 * (((XX + YY) % 2) == 0))) * stitch
    gut = ~inside
    return np.clip(base * f[..., None], 0, 255), gut


def sheer_mesh(c, mask, col=(14, 12, 16), alpha_hole=125, alpha_thread=225):
    """Fine black net: threads every 3 px, sheer holes between (the skin shows through)."""
    c[mask, :3] = np.array(col, F32) + 6 * fabric_detail(1, cloud=0.03, twill=0.0)[mask, None]
    thread = ((XX % 3) == 0) | ((YY % 3) == 0)
    c[mask, 3] = np.where(thread[mask], alpha_thread, alpha_hole)
    return c


def brass_button(c, x, y, r=2.2):
    button(c, x, y, r=r, col=BRASS)


def face_phase(names):
    """Per-pixel x offset from the start of its face (0..w-1), -1 outside those faces."""
    ph = np.full((H, W), -1, np.int32)
    for n in names:
        x, y, w, h = R[n]
        m = rect_mask([n])
        ph[m] = (XX - x)[m]
    return ph


def pleats(c, mask, period=8, lo=0.82, hi=1.14, fold=0.55):
    """Knife pleats aligned to each face: every face starts and ends mid-pleat (no fold on an edge)."""
    names = [n for n in LEGS + TORSO_RING]
    ph = face_phase(names)
    off = period // 2
    p = (ph + off) % period
    t = p / (period - 1.0)
    fac = lo + (hi - lo) * t
    m = mask & (ph >= 0)
    c[m, :3] = np.clip(c[m, :3] * fac[m, None], 0, 255)
    edge = np.zeros((H, W), bool)
    for n in names:
        x, y, w, h = R[n]
        edge |= rect_mask([n]) & ((XX == x) | (XX == x + w - 1))
    fl = m & (p == 0) & ~edge
    shade(c, fl.astype(F32), fold)
    return c


def soft_folds(c, mask, period=16, amp=0.08, seed=0):
    ph = face_phase(LEGS + TORSO_RING)
    fac = 1 + amp * np.sin(2 * np.pi * (ph + period / 4) / period + 0.4 * np.sin(YY / 11 + seed))
    m = mask & (ph >= 0)
    c[m, :3] = np.clip(c[m, :3] * fac[m, None], 0, 255)
    return c


def hem_notches(c, hem_y, period=8):
    """Tiny see-through notch at each pleat fold on the hem row (never on a face edge)."""
    ph = face_phase(LEGS)
    p = (ph + period // 2) % period
    clear(c, rect_mask(LEGS) & (YY == hem_y - 1) & (p == 0) & (ph > 0) & (ph < 63))


def knee_socks(c, y0, col, bands=(), seed=7):
    socks(c, y0, SHOE_TOP - 1, col, bands=bands, seed=seed)


def peter_pan_collar(c, dist, col=IVORY_B, edge=None, seed=0):
    """Two rounded collar lobes meeting under the chin, plus the ring on the top face."""
    lobes = np.clip(shape(lambda d: d.ellipse((262, 66, CX + 1, 98), fill=255)) +
                    shape(lambda d: d.ellipse((CX - 1, 66, 327, 98), fill=255)), 0, 1)
    lobes = lobes * rect_mask(["T_F"])
    ring = (rect_mask(["T_UP"]) & (dist <= 6)).astype(F32)
    m = np.clip(lobes + ring, 0, 1)
    lift(c, m, dy=2, sigma=1.4, strength=0.5)
    paint(c, m, blouse_fabric(seed, col))
    if edge:
        paint(c, outline_of(m > 0.5, 1).astype(F32), edge)
    else:
        shade(c, outline_of(m > 0.5, 1).astype(F32), 0.55)
    paint(c, lines([(CX, 74), (CX, 98)]), dark(col, 0.6))
    return m


def blouse_cuffs(c, col=IVORY_B, y0=452, seed=0, buttons=True):
    cuff = rect_mask(ARM_FACES) & (YY >= y0) & (YY <= SLEEVE_END)
    c[cuff, :3] = blouse_fabric(seed, col)[cuff]
    c[cuff, 3] = 255
    shade(c, (rect_mask(ARM_FACES) & (YY == y0)).astype(F32), 0.55)
    return c


def pants_base_shell(cloth_tex, seed):
    """Pants template shell: black margin (bled on save), see-through upper panel, cloth on hips + legs."""
    c, hole = pants_shell(seed)
    m = (rect_mask(TORSO_RING) & (YY >= 178)) | rect_mask(LEGS) | rect_mask(LEG_UPS) | rect_mask(["T_D"])
    c[m, :3] = cloth_tex[m]
    c[m, 3] = 255
    return c, hole


def face_plaid(sett, seed=0, cloud=0.05, soft=0.35, width=64):
    """Tartan laid out per face: every leg/torso face starts at the same point of the sett, chosen so that
    the colour at a face's first and last column match (no stripe edge or dark line on a corner)."""
    seq = []
    for col, n in list(sett) + list(sett)[::-1]:
        seq += [col] * n
    seq = np.array(seq, F32)
    L = len(seq)
    lum = seq @ np.array([0.299, 0.587, 0.114], F32)
    best, off = 1e9, 0
    for o in range(L):
        a, b = lum[o], lum[(o + width - 1) % L]
        flat = abs(lum[(o + 1) % L] - a) + abs(lum[(o + width - 2) % L] - b)
        sc = abs(a - b) * 2 + flat + abs(a - lum.mean()) * 0.2
        if sc < best:
            best, off = sc, o
    ph = face_phase(TORSO_RING + LEGS + ["T_UP", "T_D"] + ARM_UPS)
    xx = np.where(ph >= 0, ph + off, XX)
    warp = seq[xx % L]
    weft = seq[YY % L]
    tw = ((xx + YY) % 4) < 2
    col = np.where(tw[..., None], warp, weft) * 0.7 + (warp + weft) / 2 * 0.3
    if soft:
        col = ndimage.gaussian_filter(col, (soft, soft, 0))
    d = fabric_detail(seed, cloud=cloud, twill=0.0, grain=0.03)
    return np.clip(col * d[..., None], 0, 255)


NH_TARTAN = [((136, 14, 24), 9), ((22, 16, 18), 4), ((136, 14, 24), 1), ((190, 150, 62), 1), ((136, 14, 24), 1),
             ((22, 16, 18), 4), ((136, 14, 24), 9), ((28, 30, 56), 3), ((220, 206, 176), 1), ((28, 30, 56), 3)]
