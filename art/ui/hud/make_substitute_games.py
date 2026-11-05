"""Art for the substitute teacher's chalkboard minigames (Nightmare Highschool), baked to images.

Two classroom games played on the chalkboard when the strange substitute covers a class:

  Seance Sequence (memory): six sigil discs light up in a growing sequence; the player repeats it.
  Candle Vigil (reaction): a ring of candles gutter one by one; the player clicks each to relight it.

Sigils (512 x 512 RGBA, transparent outside the disc), <Name>_idle.png and <Name>_lit.png:
  A precious occult medallion in the fortune deck's manner: a rolled brass lip, a row of 44 brass beads in a dark
  channel, a beveled brass band set with four crimson cabochons in pronged collets (and four leaf studs between), a
  dark gap, an inner bead, and a dished enamel field (each sigil its own tint) engraved with a gilt sunburst. The symbol
  is a pillowed bone inlay in a raised brass cloisonne wire, ink-engraved, with a sunken dark ring round the wire so it
  reads at 110 px. Built like the HUD kit: a height field in px at 1024 work size (anti-aliased signed-distance masks,
  PIL masks drawn at 3x and box-reduced; smoothed distance fields and finite-slope bevels so no pixel staircase shows),
  normals from the height plus the school's brass detail normals, GGX + Lambert by make_health_pbr.shade, AO from the
  height; reduced 2x with premultiplied alpha.
    idle: aged bone, no glow (the gems keep a faint inner fire).   lit: the inlay blazes (white-hot core, tinted glow),
    a halo fills the field, the gilt sunburst rays catch fire, the wire and inner bead glow; edges stay sharp.
  SigilMoon      silver      a crescent moon with a few craters
  SigilEye       crimson     an open almond eye, slit pupil, five lashes
  SigilKey       brass       a skeleton key, quatrefoil bow, toothed bit, laid on the diagonal
  SigilRaven     violet      a perched raven in profile on a twig
  SigilSkullBell bone        a cracked bell with a skull face and a row of teeth along its lip
  SigilStar      night blue  an eight-point faceted star (long cardinal points)

Candle (the Candle Vigil pieces):
  CandleBody.png   256 x 512  a bone-wax pillar on a small beaded brass dish with a crimson gem, drips (one pooling on
                              the dish), a melted rolled rim and pool, a short bent black wick, no flame.
                              Ray-marched from a signed-distance model (cylinder + drips + pool + wick + saucer) seen
                              from slightly above, shaded with the same GGX lights, SDF AO and a soft key shadow, 3x SS.
  CandleFlame.png  256 x 256  a warm teardrop flame (blue root, dim core, gold body, white-hot heart, a thin crimson
                              inked outline as on the fortune cards) and a soft gold glow.
  CandleGutter.png 256 x 256  a small, leaning, sputtering bluish flame with a dim glow ("about to go out").
  CandleSmoke.png  256 x 256  a thin curling wisp of grey smoke that widens and fades as it rises.
  The flame, gutter and smoke share one anchor: the wick tip sits at (128, 208) in their 256 x 256 images. In
  CandleBody the wick tip is at WICK_TIP (printed when the script runs), so overlay a 256-px flame image at
  (wick_x - 128, wick_y - 208) at the same scale as the body.

Lesson-board game icons (512 x 512 RGBA, transparent): the phone-icon family (make_app_icons: layered relief, contact
shadows, inked marks, the same lights) in full colour, in the deck's palette (bone, ink, crimson, brass, night blue):
  GamePopQuiz        a brass-framed slate with chalk "7x8 =?" and a brass stopwatch with a crimson elapsed wedge
  GameLabMix         a round-bottom flask of glowing crimson liquid (see-through glass), bubbles rising out of the neck
  GameWordScramble   five scattered bone / night-blue / crimson letter tiles (E L P S ?) with inked letters and values
  GameMatchThePast   two ruled index cards (a date, an inked tower) and a brass hourglass of gold sand
  GameCandleVigil    a ring of seven bone candles on a beaded brass tray, six lit gold and one guttering blue
  GameSeanceSequence a crimson board with an arc of four brass sigil discs (one lit) and a bone planchette with a lens

No blood or gore anywhere (Roblox moderation). All designs original.

    python make_substitute_games.py            # everything
    python make_substitute_games.py sigils     # just the sigils (or: candle, icons)
Writes art/ui/hud/out/substitute_games/*.png, contact_sheet.png (sigils idle and lit at 110 px, the candle at 90 x 180
in each state and the game icons at 128 px, on chalkboard green #223C2E), and (on a full run) copies the 22 finals to
art/group-upload/substitute-games/SubGame_<file>.
"""
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_health_pbr as PBR

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "substitute_games"
UPLOAD = HERE.parents[1] / "group-upload" / "substitute-games"
OUT.mkdir(parents=True, exist_ok=True)
f32 = np.float32
FONT = "C:/Windows/Fonts/palab.ttf"

SIGILS = ["SigilMoon", "SigilEye", "SigilKey", "SigilRaven", "SigilSkullBell", "SigilStar"]


def lin(c):
    return PBR.srgb_to_lin(np.array(c, f32))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def dome(d, r):
    t = np.clip(d / r, 0, 1)
    return np.sqrt(1 - (1 - t) ** 2)


def bevel(d, r, k=2.4):
    """A rounded bevel with a finite slope at the edge (a dome's vertical tangent aliases into a pixel staircase)."""
    t = np.clip(d / r, 0, 1)
    return 1 - (1 - t) ** k


# ================================================================ 2D grid + shape helpers (work px)
class Grid:
    def __init__(self, w, h, ss=3):
        self.w, self.h, self.ss = w, h, ss
        yy, xx = np.mgrid[0:h, 0:w].astype(f32)
        self.x, self.y = xx + 0.5, yy + 0.5


G = None


def use(g):
    global G
    G = g


def M(sd):
    """Signed distance (px, negative inside) -> anti-aliased mask."""
    return np.clip(0.5 - sd, 0, 1).astype(f32)


def local(cx, cy, rot=0.0):
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    dx, dy = G.x - cx, G.y - cy
    return c * dx + s * dy, -s * dx + c * dy


def to_world(cx, cy, rot, u, v):
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    return cx + c * u - s * v, cy + s * u + c * v


def sd_circle(cx, cy, r):
    return np.hypot(G.x - cx, G.y - cy) - r


def circle(cx, cy, r):
    return M(sd_circle(cx, cy, r))


def ring(cx, cy, r, w):
    return M(np.abs(sd_circle(cx, cy, r)) - w / 2)


def sd_box(cx, cy, w, h, r=0.0, rot=0.0):
    u, v = local(cx, cy, rot)
    qx, qy = np.abs(u) - (w / 2 - r), np.abs(v) - (h / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def box(cx, cy, w, h, r=0.0, rot=0.0):
    return M(sd_box(cx, cy, w, h, r, rot))


def sd_ellipse(cx, cy, rx, ry, rot=0.0):
    u, v = local(cx, cy, rot)
    k = np.hypot(u / rx, v / ry) + 1e-6
    g = np.hypot(u / (rx * rx), v / (ry * ry)) / k + 1e-6
    return (k - 1) / g


def ellipse(cx, cy, rx, ry, rot=0.0):
    return M(sd_ellipse(cx, cy, rx, ry, rot))


def sd_seg(x0, y0, x1, y1):
    px, py = G.x - x0, G.y - y0
    dx, dy = x1 - x0, y1 - y0
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
    return np.hypot(px - t * dx, py - t * dy)


def seg(x0, y0, x1, y1, w):
    return M(sd_seg(x0, y0, x1, y1) - w / 2)


def taper(pts, w0, w1):
    """A stroke along a polyline whose width runs from w0 to w1."""
    n = len(pts) - 1
    acc = np.zeros((G.h, G.w), f32)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i][:2], pts[i + 1][:2]
        wa = w0 + (w1 - w0) * i / n
        wb = w0 + (w1 - w0) * (i + 1) / n
        px, py = G.x - ax, G.y - ay
        dx, dy = bx - ax, by - ay
        t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
        acc = np.maximum(acc, M(np.hypot(px - t * dx, py - t * dy) - (wa + (wb - wa) * t) / 2))
    return acc


def draw(fn):
    ss = G.ss
    m = Image.new("L", (G.w * ss, G.h * ss), 0)
    fn(ImageDraw.Draw(m), ss)
    return np.array(m.resize((G.w, G.h), Image.BOX), f32) / 255.0


def poly(pts):
    return draw(lambda d, k: d.polygon([(p[0] * k, p[1] * k) for p in pts], fill=255))


def spline(pts, closed=True, n=16):
    """Catmull-Rom through the points; a point given as (x, y, 1) is a sharp corner."""
    P = [np.array(p[:2], f32) for p in pts]
    sharp = [len(p) > 2 and p[2] for p in pts]
    m = len(P)
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        p0, p1 = P[i], P[(i + 1) % m]
        pm = P[(i - 1) % m] if (closed or i > 0) else p0
        pn = P[(i + 2) % m] if (closed or i + 2 < m) else p1
        t0 = np.zeros(2, f32) if sharp[i] else (p1 - pm) * 0.5
        t1 = np.zeros(2, f32) if sharp[(i + 1) % m] else (pn - p0) * 0.5
        for t in np.linspace(0, 1, n, endpoint=False):
            h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
            h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
            out.append(tuple(h00 * p0 + h10 * t0 + h01 * p1 + h11 * t1))
    if not closed:
        out.append(tuple(P[-1]))
    return out


def U(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = np.maximum(out, m)
    return out


def sub(a, *bs):
    for b in bs:
        a = a * (1 - b)
    return a


def inner_dist(m):
    """Distance (px) inside a mask to its edge; smoothed so the EDT's pixel staircase never shows in the bevels."""
    d = ndimage.distance_transform_edt(m > 0.5) + (m - 0.5) * (m < 1)
    return ndimage.gaussian_filter(d, 2.5).astype(f32)


def outer_dist(m):
    d = ndimage.distance_transform_edt(m < 0.5) + (0.5 - m) * (m > 0)
    return ndimage.gaussian_filter(d, 2.5).astype(f32)


def noise(shape, sigma, seed):
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.random(shape).astype(f32), sigma, mode="wrap")
    return ((n - n.min()) / (n.max() - n.min() + 1e-6)).astype(f32)


def save_rgba(rgb, alpha, path, down=1):
    """Premultiplied box reduction by `down`, then straight alpha, 8-bit."""
    rgb = np.clip(rgb, 0, 1).astype(f32)
    a = np.clip(alpha, 0, 1).astype(f32)
    if down > 1:
        h, w = a.shape
        pm = rgb * a[..., None]
        pm = pm.reshape(h // down, down, w // down, down, 3).mean((1, 3))
        a = a.reshape(h // down, down, w // down, down).mean((1, 3))
        rgb = pm / np.maximum(a[..., None], 1e-6)
    rgb = np.where(a[..., None] > 1e-4, rgb, 0)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, a * 255]).round().astype(np.uint8)
    Image.fromarray(img, "RGBA").save(path, optimize=True)
    return path


# ================================================================ sigils
S = 1024
C = S / 2
R_OUT, R_FIELD = 500.0, 392.0

SIGIL_STYLE = {   # field enamel, symbol albedo, symbol metalness, symbol roughness, glow colour (sRGB)
    "SigilMoon":      dict(field=(0.105, 0.125, 0.165), sym=(0.90, 0.91, 0.94), met=1.0, rough=0.26, glow=(0.66, 0.84, 1.00)),
    "SigilEye":       dict(field=(0.250, 0.030, 0.055), sym=(0.97, 0.80, 0.70), met=1.0, rough=0.30, glow=(1.00, 0.20, 0.17)),
    "SigilKey":       dict(field=(0.180, 0.105, 0.040), sym=(1.00, 0.80, 0.42), met=1.0, rough=0.28, glow=(1.00, 0.66, 0.20)),
    "SigilRaven":     dict(field=(0.120, 0.050, 0.185), sym=(0.80, 0.72, 0.94), met=1.0, rough=0.30, glow=(0.74, 0.42, 1.00)),
    "SigilSkullBell": dict(field=(0.155, 0.135, 0.100), sym=(0.84, 0.79, 0.66), met=0.0, rough=0.42, glow=(1.00, 0.92, 0.66)),
    "SigilStar":      dict(field=(0.040, 0.065, 0.190), sym=(0.80, 0.87, 1.00), met=1.0, rough=0.24, glow=(0.40, 0.62, 1.00)),
}


# ---- symbol shapes: return (mask, extra) where extra is a list of (mask, op, args) relief details on the symbol
def sym_moon():
    m = sub(circle(C - 34, C + 4, 262), circle(C + 66, C - 40, 218))
    det = []
    for (x, y, r) in ((C - 214, C + 40, 26), (C - 168, C + 170, 18), (C - 196, C - 90, 15), (C - 90, C + 226, 14),
                      (C - 230, C - 10, 10), (C + 40, C + 236, 11)):
        det.append(("crater", (x, y, r)))
    return m, det


def lens(cx, cy, hw, hh):
    R = (hw * hw + hh * hh) / (2 * hh)
    d = R - hh
    return np.minimum(circle(cx, cy + d, R), circle(cx, cy - d, R))


def sym_eye():
    cx, cy = C, C + 22
    outer = lens(cx, cy, 306, 156)
    inner = lens(cx, cy, 244, 104)
    lid = sub(outer, inner)
    iris = circle(cx, cy, 112)
    m = U(lid, iris)
    lashes = []
    for k, a in enumerate((-58, -29, 0, 29, 58)):
        th = math.radians(a)
        x0, y0 = cx + math.sin(th) * 150, cy - 156 * math.cos(th) * 0.86 - 8
        L = 84 if a == 0 else 74
        x1, y1 = x0 + math.sin(th) * L * 1.1, y0 - math.cos(th) * L
        lashes.append(taper([(x0, y0 + 14), (x1, y1)], 38, 20))
    m = U(m, *lashes)
    det = [("pupil", (cx, cy)), ("iris_lines", (cx, cy))]
    return m, det


def sym_key():
    rot = -45.0
    W = lambda u, v: to_world(C, C, rot, u, v)
    bx = -205.0
    bow_c = W(bx, 0)
    lobes = U(*[circle(*W(bx + 60 * math.cos(a), 60 * math.sin(a)), 64) for a in np.arange(4) * math.pi / 2])
    bow = U(lobes, circle(*bow_c, 78))
    hole = U(*[circle(*W(bx + 56 * math.cos(a), 56 * math.sin(a)), 22) for a in np.arange(4) * math.pi / 2],
             circle(*bow_c, 36))
    bow = sub(bow, hole)
    shaft = box(*W(70, 0), 420, 62, 24, rot)
    collar = U(box(*W(-94, 0), 38, 108, 14, rot), box(*W(-50, 0), 26, 86, 12, rot))
    tip = box(*W(284, 0), 34, 80, 14, rot)
    bit = box(*W(214, 74), 116, 132, 12, rot)
    notch = U(box(*W(206, 118), 30, 56, 5, rot), box(*W(190, 66), 54, 26, 5, rot))
    bit = sub(bit, notch)
    m = U(bow, shaft, collar, tip, bit)
    det = [("groove", seg(*W(-10, 0), *W(250, 0), 7))]
    return m, det


def raven_mask():
    ox, oy = C + 4, C - 4
    P = [(-292, -124, 1), (-252, -150), (-212, -170), (-184, -178, 1), (-150, -206), (-104, -214), (-60, -198),
         (-34, -168), (12, -136), (84, -96), (150, -46), (204, 6), (250, 62), (292, 122), (318, 164), (322, 190, 1),
         (292, 194), (250, 176), (214, 150), (160, 114), (96, 100), (30, 102), (-34, 90), (-92, 58),
         (-130, 18), (-152, -22), (-168, -44, 1), (-166, -56), (-184, -72, 1), (-186, -86), (-204, -100, 1),
         (-226, -110), (-292, -118, 1)]
    pts = [(ox + p[0], oy + p[1]) + tuple(p[2:]) for p in P]
    body = poly(spline(pts, True, 14))
    legs = U(taper([(ox - 26, oy + 92), (ox - 34, oy + 168)], 30, 20),
             taper([(ox + 36, oy + 98), (ox + 32, oy + 164)], 30, 20))
    toes = U(taper([(ox - 34, oy + 168), (ox - 82, oy + 182)], 18, 10), taper([(ox - 34, oy + 168), (ox + 4, oy + 182)], 16, 10),
             taper([(ox + 32, oy + 164), (ox - 8, oy + 178)], 18, 10), taper([(ox + 32, oy + 164), (ox + 74, oy + 174)], 16, 10))
    twig = taper([(ox - 262, oy + 212), (ox - 120, oy + 190), (ox + 40, oy + 176), (ox + 176, oy + 160)], 44, 26)
    twig = U(twig, taper([(ox - 150, oy + 196), (ox - 200, oy + 236), (ox - 232, oy + 246)], 22, 14))
    return body, U(legs, toes), twig


def sym_raven():
    body, legs, twig = raven_mask()
    m = U(body, legs, twig)
    ox, oy = C + 4, C - 4
    wing = taper([(ox - 96, oy - 96), (ox - 40, oy - 30), (ox + 40, oy + 30), (ox + 140, oy + 76), (ox + 232, oy + 112)], 8, 6)
    f1 = taper([(ox + 60, oy + 40), (ox + 150, oy + 112)], 7, 5)
    f2 = taper([(ox + 120, oy + 66), (ox + 206, oy + 134)], 7, 5)
    f3 = taper([(ox + 246, oy + 112), (ox + 292, oy + 172)], 7, 4)
    beak = taper([(ox - 190, oy - 126), (ox - 284, oy - 121)], 6, 3)
    nare = taper([(ox - 190, oy - 160), (ox - 236, oy - 146)], 6, 4)
    det = [("groove", U(wing, f1, f2, f3, beak, nare)), ("eye", (ox - 142, oy - 162, 17)),
           ("groove", taper([(ox - 250, oy + 210), (ox + 168, oy + 160)], 6, 3) * twig * (1 - legs))]
    return m, det


def bell_pts(cx, cy, s):
    left, right = [], []
    for t in np.linspace(0, 1, 40):
        v = -0.40 + 0.76 * t
        w = 0.20 + 0.10 * t + 0.24 * t ** 5
        left.append((-w, v))
        right.append((w, v))
    top = [(-0.20 + 0.40 * t, -0.40 - 0.07 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 16)]
    pts = top + right + [(0.56, 0.42), (-0.56, 0.42)] + left[::-1]
    return [(cx + u * s, cy + v * s) for u, v in pts]


def sym_bell():
    cx, cy, s = C, C - 10, 570
    body = poly(bell_pts(cx, cy, s))
    crown = U(ring(cx, cy - 0.53 * s, 0.078 * s, 0.056 * s), box(cx, cy - 0.47 * s, 0.11 * s, 0.05 * s, 8))
    clap = circle(cx, cy + 0.50 * s, 0.072 * s)
    m = U(body, crown, clap)
    lip_y = cy + 0.355 * s
    det = [("socket", (cx - 72, cy + 14, 50, 44)), ("socket", (cx + 72, cy + 14, 50, 44)),
           ("nose", (cx, cy + 92)), ("teeth", (cx, lip_y, s)),
           ("crack", [(cx + 214, lip_y + 30), (cx + 180, lip_y - 22), (cx + 196, cy + 136), (cx + 158, cy + 104),
                      (cx + 170, cy + 66), (cx + 140, cy + 36), (cx + 148, cy + 4)]),
           ("groove", box(cx, cy - 0.29 * s, 0.30 * s, 9, 4)), ("groove", box(cx, cy + 0.27 * s, 0.82 * s, 9, 4))]
    return m, det


def star_pts(cx, cy, r_long, r_short, r_in):
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * math.pi / 8
        r = (r_long if (k // 2) % 2 == 0 else r_short) if k % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def sym_star():
    m = poly(star_pts(C, C, 330, 228, 108))
    return m, [("facets", (C, C)), ("boss", (C, C, 40))]


SYMBOLS = {"SigilMoon": sym_moon, "SigilEye": sym_eye, "SigilKey": sym_key, "SigilRaven": sym_raven,
           "SigilSkullBell": sym_bell, "SigilStar": sym_star}


_MED = {}
GEM_ANGLES = (-90, 0, 90, 180)
R_GEM = 439.0


def medallion_base():
    """The shared rim: a rolled brass lip, a bead row, a beveled band set with four crimson cabochons, a dark gap,
    an inner bead, and a dished enamel field engraved with a gilt sunburst (computed once)."""
    if _MED:
        return _MED
    use(Grid(S, S))
    r = np.hypot(G.x - C, G.y - C)
    th = np.arctan2(G.y - C, G.x - C)
    disc = M(r - R_OUT)
    h = np.zeros((S, S), f32)
    brass_m = np.zeros((S, S), f32)          # 1 = brass, 0 = enamel; the dark gap is brass darkened
    dark = np.zeros((S, S), f32)             # darkened (patinated) brass in recesses
    # A. rolled outer lip
    lip = smooth(484, 486, r)
    h += lip * (30 + 20 * np.sqrt(np.clip(1 - ((r - 493) / 8.0) ** 2, 0, 1)))
    # B. bead row in a dark channel
    chan = smooth(461, 463, r) * (1 - lip)
    h += chan * 22
    dark += chan * 0.55
    nb = 44
    fr = (th / (2 * math.pi) * nb) % 1.0
    du = (fr - 0.5) * (2 * math.pi * 474 / nb)
    db = np.hypot(du, r - 474)
    bead = M(db - 10.5) * chan
    h = np.maximum(h, bead * (22 + 17 * dome(10.5 - db, 9)))
    dark *= 1 - bead
    # C. beveled band: a ridge with a steep inner face; fine engraved lines near its edges
    band = smooth(415, 417, r) * (1 - smooth(461, 463, r))
    tb = np.clip((r - 416) / (462 - 416), 0, 1)
    prof = np.where(tb < 0.62, 34 + 24 * smooth(0.0, 0.62, tb), 58 - 14 * smooth(0.62, 1.0, tb))
    h += band * prof
    h -= band * 3.5 * (np.exp(-((r - 422) / 1.6) ** 2) + np.exp(-((r - 456) / 1.6) ** 2))
    # gems in raised collets with four prongs, and small studs between them
    gems = np.zeros((S, S), f32)
    gem_h = np.zeros((S, S), f32)
    for a in GEM_ANGLES:
        ar = math.radians(a)
        gx, gy = C + math.cos(ar) * R_GEM, C + math.sin(ar) * R_GEM
        dg = np.hypot(G.x - gx, G.y - gy)
        collet = M(dg - 33)
        h = h * (1 - collet) + collet * (62 + 12 * dome(33 - dg, 7))
        h -= collet * 7 * np.exp(-((dg - 26.5) / 1.8) ** 2)
        for j in range(4):
            b = ar + math.pi / 4 + j * math.pi / 2
            pr = circle(gx + math.cos(b) * 24, gy + math.sin(b) * 24, 7)
            h = np.maximum(h, pr * (78 + 6 * dome(7 - np.hypot(G.x - gx - math.cos(b) * 24, G.y - gy - math.sin(b) * 24), 5)))
        gm = M(dg - 23)
        gems = np.maximum(gems, gm)
        gem_h = np.maximum(gem_h, gm * (64 + 30 * np.sqrt(np.clip(1 - (dg / 23) ** 2, 0, 1))))
    for a in GEM_ANGLES:
        ar = math.radians(a + 45)
        sx, sy = C + math.cos(ar) * R_GEM, C + math.sin(ar) * R_GEM
        dsd = np.hypot(G.x - sx, G.y - sy)
        st = M(dsd - 11)
        h = np.maximum(h, st * (60 + 10 * dome(11 - dsd, 8)))
        for j in range(4):
            b = ar + j * math.pi / 2
            lf = ellipse(sx + math.cos(b) * 19, sy + math.sin(b) * 19, 8, 4.5, -math.degrees(b))
            h = np.maximum(h, lf * (52 + 6 * dome(inner_dist(lf), 4)))
    h = h * (1 - gems) + gem_h * gems
    # D. dark gap, E. inner bead
    gap = smooth(403, 405, r) * (1 - smooth(415, 417, r))
    h += gap * 20
    dark += gap * 0.75
    ib = smooth(391, 393, r) * (1 - smooth(403, 405, r))
    h += ib * (28 + 12 * np.sqrt(np.clip(1 - ((r - 398) / 6.5) ** 2, 0, 1)))
    brass_m = np.clip(lip + chan + band + gap + ib, 0, 1)
    brass_m = np.maximum(brass_m, 0)
    # hammered texture on the band and lip only
    dents = noise((S, S), 5.0, 31) - 0.5
    h += dents * 2.5 * (band + lip) * (1 - gems)
    # F. dished enamel field with an engraved gilt sunburst
    fld = 1 - smooth(391, 393, r)
    h += fld * (12 + 10 * (r / R_FIELD) ** 2)
    nr = 32
    fr2 = (th / (2 * math.pi) * nr) % 1.0
    long_ = (np.floor(th / (2 * math.pi) * nr) % 2 == 0)
    dr = np.abs(fr2 - 0.5) * (2 * math.pi * r / nr)
    rw = np.where(long_, 2.2, 1.5) * (0.6 + 0.4 * np.clip(r / 360, 0, 1))
    r0 = np.where(long_, 150, 230)
    rays = M(dr - rw) * smooth(r0 - 10, r0 + 30, r) * (1 - smooth(340, 352, r)) * fld
    gilt = np.clip(rays + M(np.abs(r - 364) - 2.4) * fld + M(np.abs(r - 372) - 1.2) * fld, 0, 1)
    stars = np.zeros((S, S), f32)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        px, py = C + math.cos(a) * 368, C + math.sin(a) * 368
        u, v = G.x - px, G.y - py
        st4 = M((np.abs(u) ** 0.5 + np.abs(v) ** 0.5) ** 2 - 9)
        stars = np.maximum(stars, st4)
    gilt = np.clip(gilt + stars, 0, 1)
    h -= gilt * 2.5
    brass = PBR.material("Brass", (S, S), 512, tint=(1.0, 0.86, 0.52), rough_mul=0.45, rough_add=-0.02)
    brass = (brass[0] * 0.55 + lin((0.92, 0.70, 0.36)) * 0.55, brass[1] * 0.6, brass[2], brass[3])
    _MED.update(r=r, th=th, disc=disc, h=h, brass_m=brass_m, dark=np.clip(dark, 0, 1), gems=gems, fld=fld,
                gilt=gilt, rays=rays, brass=brass)
    return _MED


def sigil(name):
    st = SIGIL_STYLE[name]
    base = medallion_base()
    use(Grid(S, S))
    r = base["r"]
    sym, det = SYMBOLS[name]()
    fld = base["fld"]
    sym = sym * fld
    seed = SIGILS.index(name) + 1
    h = base["h"].copy()
    # cloisonne: a raised brass wire round the bone inlay, and a dark sunken ring outside the wire
    od = outer_dist(sym)
    wire = M(od - 8.5) * (1 - sym) * fld
    gs = ndimage.gaussian_filter(np.maximum(sym, wire), 6.0)
    chan_soft = np.clip((1 - np.exp(-3.2 * gs)) / (1 - math.exp(-3.2 * 0.5)), 0, 1.15) * (1 - sym) * (1 - wire) * fld
    h -= chan_soft * 8
    h = h * (1 - wire) + wire * (h + 6 + 16 * np.sqrt(np.clip(1 - ((od - 4.25) / 5.2) ** 2, 0, 1)))
    gilt = base["gilt"] * (1 - np.clip(sym + wire + chan_soft * 0.6, 0, 1))
    # the bone inlay: pillowed, slightly lower than the wire at its edge
    idd = inner_dist(sym)
    sym_h = h + 10 + 26 * bevel(idd, 26) + 1.6 * (noise((S, S), 2.5, seed * 7) - 0.5)
    alb_sym = np.ones((S, S), f32)
    rough_sym = np.full((S, S), 0.42, f32)
    met_sym = np.zeros((S, S), f32)
    hot = np.ones((S, S), f32)
    for kind, a in det:
        if kind == "crater":
            x, y, rc = a
            d = np.hypot(G.x - x, G.y - y) / rc
            sym_h -= 8 * np.clip(1 - d ** 2, 0, 1) * sym
            sym_h += 3.0 * np.exp(-((d - 1.0) / 0.18) ** 2) * sym
            alb_sym *= 1 - 0.30 * np.clip(1 - d, 0, 1)
            hot *= 1 - 0.25 * np.clip(1 - d, 0, 1)
        elif kind == "groove":
            g = ndimage.gaussian_filter(a, 1.2) * sym
            sym_h -= g * 8
            alb_sym = alb_sym * (1 - g) + 0.10 * g
            hot *= 1 - 0.75 * g
        elif kind == "pupil":
            x, y = a
            pm = ellipse(x, y, 28, 82)
            sym_h -= pm * (14 + 6 * dome(inner_dist(pm), 6))
            alb_sym = alb_sym * (1 - pm) + 0.04 * pm
            rough_sym = rough_sym * (1 - pm) + 0.15 * pm
            hot *= 1 - 0.85 * pm
            ring_in = ndimage.gaussian_filter(ring(x, y, 112 - 14, 7), 1.0)
            sym_h -= ring_in * 5
            alb_sym *= 1 - 0.7 * ring_in
            hot *= 1 - 0.5 * ring_in
        elif kind == "iris_lines":
            x, y = a
            rr = np.hypot(G.x - x, G.y - y)
            ang = np.arctan2(G.y - y, G.x - x)
            dl = np.abs(((ang / (2 * math.pi) * 24) % 1.0) - 0.5) * 2 * math.pi * rr / 24
            rays = M(dl - 2.4) * smooth(34, 40, rr) * (1 - smooth(86, 92, rr)) * (1 - ellipse(x, y, 36, 90))
            sym_h -= rays * 3.0
            alb_sym *= 1 - 0.45 * rays
            hot *= 1 - 0.3 * rays
        elif kind == "eye":
            x, y, re = a
            em = circle(x, y, re)
            sym_h -= em * 9
            alb_sym = alb_sym * (1 - em) + 0.04 * em
            hot *= 1 - 0.9 * em
            bead = circle(x - 4, y - 4, re * 0.35)
            sym_h += bead * 6
            alb_sym = alb_sym * (1 - bead) + 1.0 * bead
        elif kind == "socket":
            x, y, w, hh = a
            sk = ellipse(x, y, w, hh * 0.92, -14 if x > C else 14)
            sym_h -= sk * (16 + 6 * dome(inner_dist(sk), 8))
            alb_sym = alb_sym * (1 - sk) + 0.06 * sk
            hot *= 1 - 0.9 * sk
        elif kind == "nose":
            x, y = a
            nm = poly([(x, y - 26), (x + 20, y + 14), (x - 20, y + 14)])
            sym_h -= nm * 12
            alb_sym = alb_sym * (1 - nm) + 0.08 * nm
            hot *= 1 - 0.9 * nm
        elif kind == "teeth":
            x, y, s_ = a
            band = box(x, y, 1.04 * s_, 58, 12) * sym
            teeth = U(*[U(box(x + k * 68, y - 8, 52, 36, 6), box(x + k * 68, y + 2, 52, 40, 20)) for k in range(-3, 4)]) * band
            sym_h -= band * (1 - teeth) * 14
            sym_h += teeth * (3 * dome(inner_dist(teeth), 8))
            alb_sym *= 1 - 0.85 * band * (1 - teeth)
            hot *= 1 - 0.85 * band * (1 - teeth)
        elif kind == "crack":
            cm = ndimage.gaussian_filter(taper(a, 18, 6), 1.2) * sym
            sym_h -= cm * 16
            alb_sym = alb_sym * (1 - cm) + 0.04 * cm
            hot *= 1 - 0.95 * cm
        elif kind == "facets":
            sym_h = h + 10 + 8 * bevel(idd, 8) + 0.36 * np.minimum(idd, 160) + 1.0 * (noise((S, S), 2.5, seed * 7) - 0.5)
        elif kind == "boss":
            x, y, rb = a
            bm = circle(x, y, rb)
            sym_h = np.maximum(sym_h, bm * (h + 10 + 8 + 0.36 * 108 + 6 + 10 * dome(-sd_circle(x, y, rb), 14)))
            ringb = ndimage.gaussian_filter(ring(x, y, rb, 5), 1.0)
            sym_h -= ringb * 6
            alb_sym *= 1 - 0.6 * ringb
    h = h * (1 - sym) + sym_h * sym
    # ---- materials
    br_col, br_n, br_rough, _ = base["brass"]
    alb = np.zeros((S, S, 3), f32)
    rough = np.zeros((S, S), f32)
    metal = np.zeros((S, S), f32)
    detail = np.zeros((S, S, 3), f32)
    isb = np.clip(base["brass_m"] + wire, 0, 1) * (1 - base["gems"])
    bcol = br_col * (1 - 0.72 * base["dark"][..., None])
    alb += bcol * isb[..., None]
    rough += (br_rough + 0.2 * base["dark"]) * isb
    metal += isb
    detail += br_n * isb[..., None]
    gm = base["gems"]
    gem_col = lin((0.50, 0.035, 0.07))
    alb += gem_col * gm[..., None]
    rough += gm * 0.06
    # enamel field with gilt engraving
    fe = fld * (1 - sym) * (1 - wire)
    fmot = 0.85 + 0.3 * noise((S, S), 9, 50 + seed)[..., None]
    fcol = lin(st["field"]) * fmot * (1 - 0.6 * chan_soft[..., None])
    gl = gilt[..., None]
    fcol = fcol * (1 - gl) + br_col * 0.85 * gl
    alb += fcol * fe[..., None]
    rough += fe * (0.18 + 0.08 * noise((S, S), 1.2, 60 + seed)) * (1 - gilt) + fe * gilt * 0.3
    metal += fe * gilt
    # bone inlay, faintly tinted toward the sigil's colour
    bone = lin((0.90, 0.85, 0.72)) * 0.86 + lin(st["glow"]) * 0.10
    scol = bone * alb_sym[..., None] * (0.90 + 0.14 * noise((S, S), 3, 70 + seed)[..., None])
    alb += scol * sym[..., None]
    rough += rough_sym * sym
    metal += met_sym * sym
    micro = np.dstack([noise((S, S), 1.0, 90 + seed) - 0.5, noise((S, S), 1.0, 91 + seed) - 0.5, np.zeros((S, S), f32)])
    detail += micro * (fe[..., None] * 0.15 + sym[..., None] * 0.35)
    hgt = ndimage.gaussian_filter(h, 1.3)
    N = PBR.normals_from(hgt, 0.95, detail, 0.32)
    ao = PBR.ao_from(hgt, 12, 0.020) * PBR.ao_from(hgt, 4, 0.045)
    shadow = ndimage.gaussian_filter(np.roll(np.roll(np.maximum(sym, wire), 9, 0), 6, 1), 7) * fe
    ao = ao * (1 - 0.55 * shadow)
    # gems: an inner glow and a bright spark, in both states
    gem_em = np.zeros((S, S, 3), f32)
    for a in GEM_ANGLES:
        ar = math.radians(a)
        gx, gy = C + math.cos(ar) * R_GEM + 5, C + math.sin(ar) * R_GEM + 6
        dg = np.hypot(G.x - gx, G.y - gy)
        gem_em += (np.clip(1 - dg / 20, 0, 1) ** 1.5)[..., None] * lin((0.85, 0.06, 0.09)) * 0.75
    gem_em *= gm[..., None]
    g = lin(st["glow"])
    out = {}
    for state in ("idle", "lit"):
        if state == "idle":
            core = dome(idd, 60) * sym * hot
            em = gem_em + g * (0.025 * core)[..., None]
            rgb = PBR.shade(alb * np.where(sym[..., None] > 0, 0.72, 1.0), N, rough, metal, ao, emissive=em) * 0.92
        else:
            core = dome(idd, 60) * hot
            em_sym = (g ** 1.15 * (0.55 + 2.2 * core[..., None]) + np.array([1, 1, 1], f32) * (0.65 * core ** 2)[..., None])
            em_sym = em_sym * (sym * (0.25 + 0.75 * hot))[..., None]
            halo = ndimage.gaussian_filter(sym, 22) * 0.9 + ndimage.gaussian_filter(sym, 70) * 1.2
            halo = halo + 0.30 * np.clip(1 - r / R_FIELD, 0, 1) ** 1.2
            halo_f = 1.3 * halo * fe * (1 - 0.85 * chan_soft)
            em_field = g * (halo_f * 0.60)[..., None] * (lin(st["field"]) * 2.5 + 0.30)
            em_field += g * (halo_f * 0.30)[..., None]
            # the gilt sunburst catches fire
            rayglow = base["rays"] * fe * (1 - chan_soft) * (0.35 + 1.2 * np.clip(1 - r / 360, 0, 1))
            em_field += (g * 0.6 + 0.4 * lin((1.0, 0.8, 0.45)))[None, None] * (rayglow * 1.1)[..., None]
            wire_glow = wire * 0.55
            ib = base["brass_m"] * (1 - smooth(393, 405, r))
            em = em_sym + em_field + g * (wire_glow + ib * 0.45)[..., None] + gem_em * 1.4
            alb_l = alb * (1 - sym[..., None]) + (alb * 0.5 + 0.35 * g) * sym[..., None]
            rgb = PBR.shade(alb_l, N, rough, metal, ao, emissive=em)
        out[state] = rgb
    alpha = base["disc"]
    p_idle = save_rgba(out["idle"], alpha, OUT / f"{name}_idle.png", 2)
    p_lit = save_rgba(out["lit"], alpha, OUT / f"{name}_lit.png", 2)
    return [p_idle, p_lit]


def make_sigils(names=SIGILS):
    out = []
    for n in names:
        out += sigil(n)
        print("sigil", n)
    return out


# ================================================================ candle body (ray-marched SDF)
CB_W, CB_H, CB_SS = 256, 512, 3
K_PX = 62.0                     # final px per world unit (the candle's radius is 1)
TILT = math.radians(16.0)       # the camera looks down this much
Y0 = 446.0                      # final-px row of the world origin (centre of the dish's top surface)
HC = 5.95                       # candle height (to the rim)
POOL = 0.16                     # depth of the melt pool
_ct, _st = math.cos(TILT), math.sin(TILT)
CAM_UP = np.array((0.0, _ct, -_st))
CAM_BACK = np.array((0.0, _st, _ct))          # from the scene toward the viewer


def project(p):
    """World point -> final px (x, y)."""
    p = np.asarray(p, float)
    return CB_W / 2 + p[0] * K_PX, Y0 - float(p @ CAM_UP) * K_PX


def _sines(px, py, pz, freq, terms, seed, amp=1.0):
    r = np.random.default_rng(seed)
    out = 0.0
    for _ in range(terms):
        d = r.normal(size=3)
        d /= np.linalg.norm(d)
        k = freq * r.uniform(0.7, 1.3)
        out = out + np.sin(k * (d[0] * px + d[1] * py + d[2] * pz) + r.uniform(0, 6.283))
    return out * (amp / math.sqrt(terms / 2))


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def sd_capsule(px, py, pz, a, b, r):
    ax, ay, az = a
    bx, by, bz = b
    dx, dy, dz = bx - ax, by - ay, bz - az
    qx, qy, qz = px - ax, py - ay, pz - az
    t = np.clip((qx * dx + qy * dy + qz * dz) / (dx * dx + dy * dy + dz * dz), 0, 1)
    return np.sqrt((qx - t * dx) ** 2 + (qy - t * dy) ** 2 + (qz - t * dz) ** 2) - r


# drips: (angle around the candle in degrees, 90 = facing the viewer; length down from the rim; thickness)
DRIPS = [(62, 1.55, 0.110), (88, 0.62, 0.085), (104, 2.55, 0.125), (128, 1.05, 0.095), (150, 0.45, 0.075),
         (36, 0.85, 0.090), (14, 0.40, 0.070), (172, 1.75, 0.105), (114, 5.62, 0.105), (198, 0.6, 0.08),
         (-12, 1.2, 0.09)]


def rim_height(ang):
    return 0.045 * np.sin(3 * ang + 0.7) + 0.03 * np.sin(5 * ang + 2.1) + 0.02 * np.sin(9 * ang + 0.3)


def _drips(px, py, pz):
    """Union of the drips (only called for points near the candle's skin)."""
    out = np.full(px.shape, 9.0)
    for i, (deg, ln, w) in enumerate(DRIPS):
        a = math.radians(deg)
        rim_y = HC + float(rim_height(np.array(a)))
        y_end = max(rim_y - ln, 0.02)
        wob = 0.05 * np.sin(py * 2.1 + i * 1.7)            # a slow meander sideways
        aa = a + wob
        t = np.clip((rim_y - py) / max(ln, 1e-3), 0, 1)
        wr = w * (1.0 - 0.30 * t) * (0.90 + 0.10 * np.sin(py * 7 + i))
        cx, cz = np.cos(aa) * (1.0 - wr * 0.25), np.sin(aa) * (1.0 - wr * 0.25)
        dd = np.sqrt((px - cx) ** 2 + (pz - cz) ** 2) - wr
        dd = np.maximum(dd, np.maximum(py - rim_y + 0.03, y_end - py))
        if y_end <= 0.05:          # a drip that reached the dish spreads into a puddle instead of a bulb
            db = (np.sqrt(((px - math.cos(a) * 1.2) / 0.46) ** 2 + (py / 0.075) ** 2
                          + ((pz - math.sin(a) * 1.2) / 0.38) ** 2) - 1.0) * 0.07
        else:
            br = w * 1.06
            bx, bz = math.cos(a) * (1.0 - br * 0.3), math.sin(a) * (1.0 - br * 0.3)
            db = np.sqrt((px - bx) ** 2 + ((py - y_end - br * 0.5) / 1.9) ** 2 + (pz - bz) ** 2) - br
        out = smin(out, smin(dd, db, 0.06), 0.02)
    return out


def candle_sdf(px, py, pz, want_id=False):
    r = np.sqrt(px * px + pz * pz)
    ang = np.arctan2(pz, px)
    # wax pillar: a gently uneven radius, a melted top with a pool and an uneven rolled rim
    lump = _sines(px, py * 0.5, pz, 1.8, 8, 11, 0.007) + _sines(px, py * 0.7, pz, 5.0, 8, 12, 0.0018)
    d_side = r - (1.0 + lump)
    rimh = rim_height(ang)
    top = HC + rimh * smooth(0.55, 1.0, r) - POOL * (1 - smooth(0.45, 0.92, r))
    d_top = (py - top) * 0.75
    wax = smax(d_side, d_top, 0.08)
    lipring = np.hypot(r - 0.965, py - (HC + rimh - 0.035)) - 0.05          # a soft rolled lip of melted wax
    wax = smin(wax, lipring, 0.05)
    wax = np.maximum(wax, -py - 0.02)
    near = (np.abs(r - 1.0) < 0.45) & (py > -0.15) & (py < HC + 0.45)
    if near.any():
        ii = np.nonzero(near)[0]
        wax[ii] = smin(wax[ii], _drips(px[ii], py[ii], pz[ii]), 0.06)
    # the wick: a short black cotton wick with a slight bend and a charred knob
    wick = np.full(px.shape, 9.0)
    ty = HC - POOL
    nw = (r < 0.5) & (py > ty - 0.5) & (py < ty + 0.8)
    if nw.any():
        ii = np.nonzero(nw)[0]
        qx, qy, qz = px[ii], py[ii], pz[ii]
        w0, w1, w2 = (0.0, ty - 0.1, 0.0), (0.0, ty + 0.17, 0.0), (0.055, ty + 0.30, 0.02)
        wk = np.minimum(sd_capsule(qx, qy, qz, w0, w1, 0.048), sd_capsule(qx, qy, qz, w1, w2, 0.042))
        wick[ii] = np.minimum(wk, np.sqrt((qx - w2[0]) ** 2 + (qy - w2[1]) ** 2 + (qz - w2[2]) ** 2) - 0.056)
    # the brass dish: a revolved profile (a flat plate with a rolled rim and a shallow foot)
    qx, qy = np.abs(r - 0.83) - 0.83, np.abs(py + 0.09) - 0.09
    plate = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - 0.02
    bead = (0.5 + 0.5 * np.cos(ang * 40)) ** 3
    rim = np.hypot(r - 1.68, py - 0.01) - (0.080 + 0.022 * bead)
    under = np.hypot(np.maximum(np.abs(r - 0.6) - 0.6, 0), np.maximum(np.abs(py + 0.25) - 0.08, 0)) - 0.02
    dish = smin(smin(plate, rim, 0.05), under, 0.04)
    gem = np.sqrt(px ** 2 + ((py - 0.02) / 0.85) ** 2 + ((pz - 1.775) / 0.75) ** 2) - 0.085
    d = np.minimum(np.minimum(np.minimum(wax, wick), dish), gem)
    if not want_id:
        return d
    mid = np.where(dish <= np.minimum(wax, wick), 2, np.where(wick < wax, 1, 0))
    mid = np.where(gem <= np.minimum(np.minimum(wax, wick), dish), 3, mid)
    return d, mid


def candle_body():
    w, h = CB_W * CB_SS, CB_H * CB_SS
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    sx = (xx + 0.5) / CB_SS
    sy = (yy + 0.5) / CB_SS
    X = (sx - CB_W / 2) / K_PX
    Yu = (Y0 - sy) / K_PX
    # ray origins on a plane in front of the scene, all looking along -CAM_BACK
    D0 = 6.0
    ox = X
    oy = Yu * CAM_UP[1] + D0 * CAM_BACK[1]
    oz = Yu * CAM_UP[2] + D0 * CAM_BACK[2]
    dvy, dvz = -CAM_BACK[1], -CAM_BACK[2]
    ox, oy, oz = ox.ravel(), oy.ravel(), oz.ravel()
    n = ox.size
    t = np.full(n, 0.0)
    hit = np.zeros(n, bool)
    idx = np.nonzero(np.abs(ox) < 1.9)[0]          # skip rays that miss the bounding cylinder entirely
    for step in range(260):
        if idx.size == 0:
            break
        px, py, pz = ox[idx], oy[idx] + dvy * t[idx], oz[idx] + dvz * t[idx]
        d = candle_sdf(px, py, pz)
        t[idx] += d * 0.8
        done = d < 4e-4
        hit[idx[done]] = True
        gone = (t[idx] > 14) | (py < -0.8)
        idx = idx[~done & ~gone]
    hidx = np.nonzero(hit)[0]
    px, py, pz = ox[hidx], oy[hidx] + dvy * t[hidx], oz[hidx] + dvz * t[hidx]
    _, mid = candle_sdf(px, py, pz, True)
    e = 1.5e-3
    nx = candle_sdf(px + e, py, pz) - candle_sdf(px - e, py, pz)
    ny = candle_sdf(px, py + e, pz) - candle_sdf(px, py - e, pz)
    nz = candle_sdf(px, py, pz + e) - candle_sdf(px, py, pz - e)
    nl = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    # ambient occlusion along the normal
    ao = np.ones(hidx.size)
    for i, hh in enumerate((0.03, 0.07, 0.13, 0.22, 0.34)):
        dd = candle_sdf(px + nx * hh, py + ny * hh, pz + nz * hh)
        ao -= (hh - dd) * (1.6 / (i + 1)) * 0.9
    ao = np.clip(ao, 0.25, 1.0)
    # soft shadow toward the key light
    Ls = PBR.LIGHTS[0][0]                     # screen space (x right, y down, z to viewer)
    Lw = np.array((Ls[0], 0.0, 0.0)) + CAM_UP * (-Ls[1]) + CAM_BACK * Ls[2]
    Lw /= np.linalg.norm(Lw)
    sh = np.ones(hidx.size)
    tt = np.full(hidx.size, 0.03)
    sx0, sy0, sz0 = px + nx * 0.01, py + ny * 0.01, pz + nz * 0.01
    for _ in range(48):
        dd = candle_sdf(sx0 + Lw[0] * tt, sy0 + Lw[1] * tt, sz0 + Lw[2] * tt)
        sh = np.minimum(sh, np.clip(10 * dd / tt, 0, 1))
        tt += np.clip(dd, 0.02, 0.3)
    sh = np.clip(sh, 0, 1)
    # screen-space normals for the shared PBR shader
    Ns = np.stack([nx, -(ny * CAM_UP[1] + nz * CAM_UP[2]), ny * CAM_BACK[1] + nz * CAM_BACK[2]], -1)
    # materials
    m = hidx.size
    alb = np.zeros((m, 3))
    rough = np.zeros(m)
    metal = np.zeros(m)
    wax = mid == 0
    wick = mid == 1
    brs = mid == 2
    mott = 0.5 + 0.5 * _sines(px, py * 1.4, pz, 9.0, 10, 21)
    streak = 0.5 + 0.5 * _sines(px * 3, py * 0.25, pz * 3, 6.0, 8, 22)
    bone = np.array(lin((0.93, 0.89, 0.78)), float)
    warm = np.array(lin((0.88, 0.80, 0.62)), float)
    yt = np.clip(py / HC, 0, 1)[:, None]
    wcol = bone * (0.92 + 0.08 * mott[:, None]) * (0.94 + 0.06 * streak[:, None])
    wcol = wcol * yt + (wcol * 0.55 + warm * 0.45) * (1 - yt)      # older, yellower wax low down
    alb[wax] = wcol[wax]
    rough[wax] = 0.30 + 0.12 * mott[wax]
    alb[wick] = np.array(lin((0.035, 0.030, 0.028)))
    rough[wick] = 0.85
    bcol = np.array(lin((0.98, 0.76, 0.42)), float)
    alb[brs] = bcol * (0.82 + 0.25 * (0.5 + 0.5 * _sines(px, py, pz, 14.0, 8, 31)[brs]))[:, None]
    rough[brs] = 0.26 + 0.16 * (0.5 + 0.5 * _sines(px, py, pz, 30.0, 8, 32)[brs])
    metal[brs] = 1.0
    gm = mid == 3
    alb[gm] = np.array(lin((0.50, 0.035, 0.07)))
    rough[gm] = 0.08
    occ = ao * (0.5 + 0.5 * sh)
    # wax is translucent: a little light wraps in
    fres = (1 - np.clip(Ns[:, 2], 0, 1)) ** 2
    thin = 0.06 + 0.14 * fres + 0.05 * smooth(HC - 0.7, HC, py)
    emis = alb * (thin * wax)[:, None] * np.array([1.0, 0.78, 0.55]) + gm[:, None] * np.array(lin((0.45, 0.03, 0.05)))
    rgb = PBR.shade(alb[None], Ns[None], rough[None], metal[None], occ[None], emissive=emis[None])[0]
    img = np.zeros((n, 3))
    img[hidx] = rgb
    a = np.zeros(n)
    a[hidx] = 1.0
    img = img.reshape(h, w, 3)
    a = a.reshape(h, w)
    tip = project((0.055, HC - POOL + 0.30 + 0.05, 0.02))
    return save_rgba(img, a, OUT / "CandleBody.png", CB_SS), tip


# ================================================================ flame / gutter / smoke (painted 2D)
FS = 256
F_SS = 4
ANCHOR = (128.0, 208.0)        # the wick tip in the 256 x 256 overlay images


def _fgrid():
    g = Grid(FS * F_SS, FS * F_SS)
    g.x, g.y = g.x / F_SS, g.y / F_SS        # coordinates in final px
    use(g)
    return g


def flame_sdf(x0, y0, height, wmax, lean=0.0, sway=0.0, tb=0.30, kt=1.35):
    """Signed distance (approx, final px) to a teardrop flame whose round bottom sits at y0 (the wick)."""
    v = (y0 - G.y) / height                     # 0 at the bottom, 1 at the tip
    off = (lean * v ** 2 + sway * np.sin(v * math.pi * 1.2) * v) * height
    u = G.x - x0 - off
    t = np.clip(v, 0, 1)
    hw_bottom = wmax * np.sqrt(np.clip(1 - ((t - tb) / tb) ** 2, 0, 1))
    hw_top = wmax * np.clip((1 - t) / (1 - tb), 0, 1) ** kt
    hw = np.where(t < tb, hw_bottom, hw_top)
    sd = np.abs(u) - hw
    sd = np.where((v < 0) | (v > 1), np.maximum(sd, np.abs(v - 0.5) * height - height / 2) + 1, sd)
    return sd, u, v


def over(dst, col, a):
    """Premultiplied 'over' of a colour layer (rgb sRGB 0..1, alpha map) onto dst (H, W, 4)."""
    a = np.clip(a, 0, 1)[..., None]
    dst[..., :3] = np.asarray(col, f32) * a + dst[..., :3] * (1 - a)
    dst[..., 3:] = a + dst[..., 3:] * (1 - a)
    return dst


def finish_layer(dst, name):
    h, w = dst.shape[:2]
    pm = dst.reshape(h // F_SS, F_SS, w // F_SS, F_SS, 4).mean((1, 3))
    a = pm[..., 3]
    rgb = pm[..., :3] / np.maximum(a[..., None], 1e-6)
    rgb = np.where(a[..., None] > 1e-4, rgb, 0)
    img = np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(a, 0, 1) * 255]).round().astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)
    return OUT / name


def paint_flame(dst, x0, y0, height, wmax, lean, sway, pal, glow_a, glow_r, kt=1.05, tb=0.26):
    """A layered candle flame. pal: edge, body, inner, heart, root (blue), tip (body colour near the tip), glow."""
    # glow: a wide soft halo and a tighter bloom around the flame's body
    gx, gy = x0 + lean * height * 0.3, y0 - height * 0.40
    rr = np.hypot(G.x - gx, (G.y - gy) / 1.25)
    edge = np.minimum(np.minimum(G.x, FS - G.x), np.minimum(G.y, FS - G.y))
    win = smooth(2, 46, edge)                    # the glow fades out before the image border
    over(dst, pal["glow"], win * glow_a * (0.50 * np.exp(-(rr / glow_r) ** 2) + 0.50 * np.exp(-(rr / (glow_r * 0.42)) ** 2)))
    sd, u, v = flame_sdf(x0, y0, height, wmax, lean, sway, tb=tb, kt=kt)
    body = np.clip(0.5 - sd * F_SS / 1.4, 0, 1)
    inside = np.clip(-sd / wmax, 0, 1)
    vt = np.clip(v, 0, 1)[..., None]
    # outer flame: a thin luminous edge to the body colour, which turns toward `tip` near the top
    base_col = np.asarray(pal["body"], f32) * (1 - smooth(0.45, 0.95, vt)) + np.asarray(pal["tip"], f32) * smooth(0.45, 0.95, vt)
    k = smooth(0.0, 0.30, inside)[..., None]
    col = np.asarray(pal["edge"], f32) * (1 - k) + base_col * k
    a_body = body * (0.70 + 0.30 * smooth(0.0, 0.30, inside)) * (1 - 0.30 * smooth(0.75, 1.0, v))
    over(dst, col, a_body)
    # a thin inked outline, as on the fortune cards' candles
    ol = np.clip(0.5 - (np.abs(sd + 0.2) - pal.get("ol_w", 1.0)) * F_SS / 1.2, 0, 1)
    over(dst, pal["ol"], ol * pal.get("ol_a", 0.75) * (1 - 0.5 * smooth(0.8, 1.0, v)))
    # bright inner flame and the white-hot heart (soft-edged inside the crisp outline)
    sd2, _, _ = flame_sdf(x0, y0 - height * 0.05, height * 0.78, wmax * 0.66, lean * 0.9, sway * 0.9, tb=tb, kt=kt)
    inner = np.clip(0.5 - sd2 * F_SS / 4.0, 0, 1) * body
    over(dst, pal["inner"], inner * 0.92)
    sd3, _, _ = flame_sdf(x0, y0 - height * 0.10, height * 0.50, wmax * 0.40, lean * 0.7, sway * 0.7, tb=tb, kt=kt)
    heart = np.clip(0.5 - sd3 * F_SS / 7.0, 0, 1) * body
    over(dst, pal["heart"], heart * 0.95)
    # the dim core round the wick and the blue root cupping the bottom
    core = np.exp(-(((G.x - x0) / (wmax * 0.30)) ** 2 + ((G.y - (y0 - height * 0.08)) / (height * 0.085)) ** 2))
    over(dst, pal.get("core", (0.55, 0.34, 0.24)), core * 0.45 * body)
    root = smooth(0.24, 0.03, v) * body * (0.25 + 0.75 * smooth(0.25, 0.85, np.abs(u) / (wmax + 1e-6)))
    over(dst, pal["root"], np.clip(root * 0.95, 0, 0.8))
    return dst


def candle_flame():
    _fgrid()
    dst = np.zeros(G.x.shape + (4,), f32)
    x0, y0 = ANCHOR
    pal = dict(edge=(1.00, 0.52, 0.14), body=(1.00, 0.72, 0.26), tip=(1.00, 0.56, 0.18), inner=(1.00, 0.90, 0.56),
               heart=(1.00, 0.99, 0.92), root=(0.32, 0.46, 0.96), glow=(1.00, 0.72, 0.34), ol=(0.38, 0.055, 0.10))
    paint_flame(dst, x0, y0 + 6, 120, 24, lean=0.02, sway=0.03, pal=pal, glow_a=0.72, glow_r=76)
    return finish_layer(dst, "CandleFlame.png")


def candle_gutter():
    _fgrid()
    dst = np.zeros(G.x.shape + (4,), f32)
    x0, y0 = ANCHOR
    # a short, low, leaning flame: mostly blue, a dim amber lick at its top
    pal = dict(edge=(0.26, 0.42, 1.00), body=(0.38, 0.56, 1.00), tip=(1.00, 0.66, 0.30), inner=(0.62, 0.76, 1.00),
               heart=(0.86, 0.92, 1.00), root=(0.20, 0.32, 0.98), glow=(0.42, 0.56, 1.00), core=(0.20, 0.26, 0.55),
               ol=(0.07, 0.10, 0.26), ol_w=0.8)
    paint_flame(dst, x0, y0 + 5, 58, 15, lean=-0.34, sway=0.12, pal=pal, glow_a=0.34, glow_r=46, kt=1.2, tb=0.36)
    # a detached tongue of flame sputtering off above it
    sd, _, _ = flame_sdf(x0 - 25, y0 - 68, 18, 4.6, lean=0.35, sway=0.0)
    blob = np.clip(0.5 - sd * F_SS / 1.4, 0, 1)
    over(dst, (0.48, 0.64, 1.0), blob * 0.78)
    over(dst, (0.90, 0.94, 1.0), np.clip(0.5 - (sd + 1.5) * F_SS / 2.0, 0, 1) * 0.65)
    # sparks
    for (sx, sy, r) in ((x0 + 14, y0 - 52, 1.5), (x0 - 4, y0 - 92, 1.2), (x0 + 22, y0 - 80, 1.0), (x0 - 36, y0 - 44, 1.1)):
        d = np.hypot(G.x - sx, G.y - sy)
        over(dst, (1.0, 0.78, 0.45), np.exp(-(d / (r * 2.6)) ** 2) * 0.35)
        over(dst, (1.0, 0.95, 0.80), np.clip(0.5 - (d - r) * F_SS / 1.2, 0, 1) * 0.95)
    return finish_layer(dst, "CandleGutter.png")


def candle_smoke():
    _fgrid()
    dst = np.zeros(G.x.shape + (4,), f32)
    x0, y0 = ANCHOR
    strands = [  # (phase, amplitude, width0, width1, alpha, frequency, drift)
        (0.0, 15, 3.4, 12, 0.66, 1.05, 10),
        (2.3, 10, 2.4, 7, 0.46, 1.70, 4),
        (4.4, 24, 1.8, 15, 0.28, 0.80, 16),
    ]
    n = 80
    for k, (ph, amp, w0, w1, a0, fr, drift) in enumerate(strands):
        pts = []
        for i in range(n + 1):
            t = i / n
            y = y0 - 3 - t * 200
            x = (x0 + amp * t ** 0.85 * math.sin(t * math.pi * 2 * fr + ph) * (1 + 0.6 * t)
                 + drift * t ** 2 + 5 * t ** 3 * math.sin(t * 13 + 2 * k))
            pts.append((x, y, t))
        acc = np.zeros(G.x.shape, f32)
        fade = np.zeros(G.x.shape, f32)
        for i in range(n):
            (ax, ay, ta), (bx, by, tb) = pts[i], pts[i + 1]
            px, py = G.x - ax, G.y - ay
            dx, dy = bx - ax, by - ay
            tt = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
            tm = ta + (tb - ta) * tt
            wid = w0 + (w1 - w0) * tm ** 1.2
            dist = np.hypot(px - tt * dx, py - tt * dy)
            prof = np.clip(1 - (dist / (wid / 2 + 0.6)) ** 2, 0, 1)
            better = prof > acc
            acc = np.where(better, prof, acc)
            fade = np.where(better, tm, fade)
        breakup = 0.75 + 0.25 * np.sin(fade * (17 + 5 * k) + k) * smooth(0.2, 0.6, fade)
        alpha = acc ** 0.8 * a0 * smooth(1.0, 0.22, fade) * smooth(0.0, 0.05, fade) * breakup
        tone = 0.60 + 0.20 * (1 - fade)
        col = np.dstack([tone * 0.96, tone * 0.97, tone * 1.0])
        over(dst, col, alpha)
    # an ember glow at the wick tip, the last of the heat
    d = np.hypot(G.x - x0, G.y - (y0 - 1))
    over(dst, (1.0, 0.45, 0.15), np.exp(-(d / 6.0) ** 2) * 0.55)
    over(dst, (1.0, 0.75, 0.40), np.clip(0.5 - (d - 1.8) * F_SS / 1.2, 0, 1) * 0.9)
    return finish_layer(dst, "CandleSmoke.png")


def make_candle():
    global WICK_TIP
    p, tip = candle_body()
    WICK_TIP = tip
    print("candle body", p, "wick tip (px):", tuple(round(v, 1) for v in tip))
    return [p, candle_flame(), candle_gutter(), candle_smoke()]


# ================================================================ lesson-board game icons (full-colour PBR relief)
# The phone-icon family (make_app_icons: layered height field, contact shadows, inked marks, the same GGX lights and
# normal scale) with full-colour albedo in the fortune deck's palette: bone, ink, crimson #600E1A, brass gold, night blue.
GAMES = ["GamePopQuiz", "GameLabMix", "GameWordScramble", "GameMatchThePast", "GameCandleVigil", "GameSeanceSequence"]
C_BONE = (0.93, 0.89, 0.79)
C_PAPER = (0.94, 0.91, 0.83)
C_INK = (0.075, 0.06, 0.075)
C_CRIM = (0.376, 0.055, 0.102)
C_CRIM_L = (0.62, 0.12, 0.15)
C_GOLD = (0.90, 0.70, 0.36)
C_NIGHT = (0.13, 0.17, 0.31)
C_SLATE = (0.13, 0.15, 0.15)
C_GLASS = (0.10, 0.12, 0.17)
FONT_SERIF = "C:/Windows/Fonts/palab.ttf"
FONT_CHALK = "C:/Windows/Fonts/segoeprb.ttf"


def _A():
    import make_app_icons as A
    return A


class CIcon:
    """make_app_icons.Icon with RGB albedo (sRGB) and an emissive layer."""

    def __init__(self, seed):
        A = _A()
        self.A = A
        n = A.S
        self.h = np.zeros((n, n), f32)
        self.alb = np.zeros((n, n, 3), f32) + 0.8
        self.rough = np.full((n, n), 0.55, f32)
        self.metal = np.zeros((n, n), f32)
        self.alpha = np.zeros((n, n), f32)
        self.cast = np.zeros((n, n), f32)
        self.emis = np.zeros((n, n, 3), f32)
        self.opac = np.ones((n, n), f32)          # < 1 where the object is see-through (glass)
        self.halos = []
        self.seed, self.k = seed, 0

    def noise(self, sigma):
        self.k += 1
        return self.A.blur_noise(sigma, self.seed * 1000 + self.k)

    @staticmethod
    def _c(alb):
        a = np.asarray(alb, f32)
        return a if a.ndim == 3 else a[None, None, :]

    def custom(self, m, h, alb, rough, metal=0.0, cast=True):
        if cast:
            sh = ndimage.gaussian_filter(np.roll(np.roll(m, 10, 0), 6, 1), 9)
            self.cast = np.maximum(self.cast * (1 - m), sh * (1 - m) * np.clip(self.alpha * 4, 0, 1))
        else:
            self.cast *= 1 - m
        m3 = m[..., None]
        self.h = self.h * (1 - m) + h * m
        self.alb = self.alb * (1 - m3) + self._c(alb) * m3
        self.rough = self.rough * (1 - m) + rough * m
        self.metal = self.metal * (1 - m) + metal * m
        self.emis = self.emis * (1 - m3)
        self.opac = self.opac * (1 - m) + m
        self.alpha = np.maximum(self.alpha, m)

    def part(self, m, z=0.20, lift=0.16, bevel=26, alb=C_PAPER, rough=0.55, metal=0.0, cast=True, tex=0.012,
             mottle=0.07):
        H = self.A.H
        h = z + lift * H.dome(self.A.inner_dist(m), bevel) + tex * self.noise(2.0) + tex * 1.6 * self.noise(14)
        a = self._c(alb) * (1 - mottle + mottle * self.noise(3))[..., None] if mottle else self._c(alb)
        self.custom(m, h, a, rough, metal, cast)

    def groove(self, m, depth=0.07, dark=0.10):
        self.h -= m * depth
        self.alb *= 1 - dark * m[..., None]

    def emboss(self, m, lift=0.08, bevel=8, alb=None, rough=None, metal=None):
        self.h += m * lift * self.A.H.dome(self.A.inner_dist(m), bevel)
        self._mat(m, alb, rough, metal)

    def recess(self, m, depth=0.10, bevel=8, alb=None, rough=None, metal=None):
        self.h -= m * depth * self.A.H.dome(self.A.inner_dist(m), bevel)
        self._mat(m, alb, rough, metal)

    def ink(self, m, col=C_INK, lift=1.0):
        self.h += m * (0.035 + 0.075 * self.A.H.dome(self.A.inner_dist(m), 7)) * lift
        self._mat(m, col, 0.35, 0.0)

    def glassy(self, m, base=0.38):
        """Make a part see-through: thin in the middle, opaque toward its rim (Fresnel) and on highlights."""
        d = self.A.inner_dist(m)
        rim = np.exp(-d / 22.0)
        self.opac = self.opac * (1 - m) + m * np.clip(base + (1 - base) * rim, 0, 1)

    def solid(self, m):
        self.opac = np.maximum(self.opac, m)

    def glow(self, m, col, k):
        self.emis += m[..., None] * lin(col) * k

    def halo(self, cx, cy, r, col, a):
        self.halos.append((cx, cy, r, col, a))

    def _mat(self, m, alb, rough, metal):
        m3 = m[..., None]
        if alb is not None:
            self.alb = self.alb * (1 - m3) + self._c(alb) * m3
        if rough is not None:
            self.rough = self.rough * (1 - m) + rough * m
        if metal is not None:
            self.metal = self.metal * (1 - m) + metal * m

    def render(self):
        A, H = self.A, self.A.H
        n = A.S
        height = ndimage.gaussian_filter(self.h, 0.9)
        alb = H.srgb_to_lin(np.clip(self.alb, 0, 1)).astype(f32)
        micro = np.dstack([self.noise(1.5) - 0.5, self.noise(1.5) - 0.5, np.zeros((n, n), f32)]).astype(f32)
        N = H.normals_from(height * n * 0.5, 1.0 / 7.5, micro, 0.22)
        ao = H.ao_from(height, 10, 5) * H.ao_from(height, 3, 9)
        ao *= 1 - 0.8 * self.cast
        rgb = H.shade(alb, N, np.clip(self.rough, 0.05, 1), np.clip(self.metal, 0, 1), ao, emissive=self.emis)
        a = np.clip(self.alpha * self.opac, 0, 1)
        if self.halos:            # soft light behind the object (flames), outside its silhouette
            hr = np.zeros((n, n, 3), f32)
            ha = np.zeros((n, n), f32)
            for cx, cy, r, col, aa in self.halos:
                d = np.hypot(A.xx - cx, A.yy - cy)
                g = aa * (0.55 * np.exp(-(d / r) ** 2) + 0.45 * np.exp(-(d / (r * 0.4)) ** 2))
                hr = hr * (1 - g[..., None]) + np.asarray(col, f32) * g[..., None]
                ha = ha + g * (1 - ha)
            pm = rgb * a[..., None] + hr * (1 - a[..., None])
            a2 = a + ha * (1 - a)
            rgb = pm / np.maximum(a2[..., None], 1e-6)
            # inside the object the halo also brightens slightly (light spilling over the surfaces)
            a = a2
        return rgb, a


def tmask(s, size, cx, cy, font=FONT_SERIF, rot=0.0):
    A = _A()
    f = ImageFont.truetype(font, int(size * A.SS))
    m = A.draw(lambda d, k: d.text((cx * k, cy * k), s, font=f, fill=255, anchor="mm"))
    return A.rotate(m, rot, cx, cy) if rot else m


def brass_kw(rough=0.30):
    return dict(alb=C_GOLD, rough=rough, metal=0.85)


def mini_flame(ic, x, y, h, w, blue=False):
    """A small candle flame (wick tip at x, y), with a halo behind it."""
    A = _A()
    tip = (x, y - h)
    fl = A.poly(A.bez((x, y - h), (x + w * 0.9, y - h * 0.55), (x + w * 1.0, y - h * 0.05), (x, y + w * 0.3))
                + A.bez((x, y + w * 0.3), (x - w * 1.0, y - h * 0.05), (x - w * 0.9, y - h * 0.55), (x, y - h)))
    col = (0.62, 0.74, 1.0) if blue else (1.0, 0.86, 0.50)
    ic.custom(fl, ic.h * (1 - fl) + (0.62 + 0.05 * A.H.dome(A.inner_dist(fl), 10)) * fl, col, 0.4, 0.0, cast=False)
    core = A.ellipse(x, y - h * 0.32, w * 0.42, h * 0.30)
    ic.glow(fl, (0.45, 0.55, 1.0) if blue else (1.0, 0.62, 0.22), 2.2)
    ic.glow(core * fl, (1, 1, 1) if not blue else (0.8, 0.9, 1.0), 1.6)
    edge = A.edge_line(fl, 4) * fl
    ic._mat(edge, (0.10, 0.14, 0.40) if blue else C_CRIM, None, None)
    ic.emis *= 1 - 0.85 * edge[..., None]
    ic.halo(x, y - h * 0.45, h * (1.5 if not blue else 1.1), (1.0, 0.72, 0.34) if not blue else (0.45, 0.58, 1.0),
            0.55 if not blue else 0.40)


def game_pop_quiz():
    A = _A()
    ic = CIcon(101)
    cx, cy, rot = 470, 430, -6
    W = lambda u, v: A.to_world(cx, cy, rot, u, v)
    frame = A.box(cx, cy, 760, 580, 40, rot)
    ic.part(frame, z=0.16, lift=0.16, bevel=22, **brass_kw(0.34))
    ic.groove(A.sub(A.edge_line(frame, 22), A.edge_line(frame, 16)), 0.04, 0.2)
    slate = A.box(cx, cy, 650, 470, 16, rot)
    ic.custom(slate, 0.20 + 0.006 * ic.noise(2) + 0.01 * ic.noise(20), np.asarray(C_SLATE, f32)[None, None] *
              (0.85 + 0.3 * ic.noise(8))[..., None], 0.75, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - slate, 9, 0), 6, 1), 8) * slate)
    for u, v in ((-350, -260), (350, -260), (-350, 260), (350, 260)):
        ic.part(A.circle(*W(u, v), 17), z=0.32, lift=0.08, bevel=10, **brass_kw(0.28))
    # chalk sums: soft-edged chalk with a dry, broken texture
    chalk = A.U(tmask("7×8", 210, *W(-60, -86), FONT_CHALK, rot), tmask("=?", 200, *W(-40, 116), FONT_CHALK, rot))
    dry = np.clip((ic.noise(1.2) - 0.25) * 3.0, 0, 1) * np.clip((ic.noise(6) + 0.35), 0, 1)
    chalk_m = chalk * (0.55 + 0.45 * dry)
    ic.h += chalk * 0.02
    ic._mat(chalk_m, (0.93, 0.93, 0.88), 0.9, 0.0)
    # chalk smudge
    sm = A.ellipse(*W(220, -150), 90, 26, rot - 10) * slate
    ic._mat(sm * 0.25, (0.6, 0.62, 0.6), None, None)
    # the timer: a brass stopwatch, a crimson wedge for the time used
    tx, ty, R = 752, 712, 196
    ic.part(A.ring(tx + 60, ty - 236, 38, 24), z=0.34, lift=0.12, bevel=10, **brass_kw())
    ic.part(A.box(tx + 34, ty - 186, 56, 60, 10, 20), z=0.36, lift=0.12, bevel=12, **brass_kw())
    ic.part(A.box(tx - 120, ty - 150, 40, 46, 8, -40), z=0.36, lift=0.10, bevel=10, **brass_kw())
    case = A.circle(tx, ty, R)
    ic.part(case, z=0.38, lift=0.2, bevel=34, **brass_kw(0.28))
    ic.emboss(A.U(*[A.circle(tx + (R - 24) * math.cos(t), ty + (R - 24) * math.sin(t), 8)
                    for t in np.linspace(0, 2 * math.pi, 34, endpoint=False)]), 0.05, 7)
    face = A.circle(tx, ty, R - 50)
    ic.custom(face, 0.46 + 0.01 * ic.noise(14), np.asarray(C_BONE, f32)[None, None] * (0.94 + 0.06 * ic.noise(3))[..., None],
              0.6, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - face, 8, 0), 5, 1), 8) * face)
    ang = np.arctan2(A.xx - tx, -(A.yy - ty))           # 0 at twelve, clockwise
    ang = np.where(ang < 0, ang + 2 * math.pi, ang)
    wedge = (ang < math.radians(250)).astype(f32) * A.circle(tx, ty, R - 70)
    wedge = ndimage.gaussian_filter(wedge, 0.8)
    ic.recess(wedge, 0.02, 4, alb=C_CRIM_L, rough=0.4)
    ticks = []
    for i in range(12):
        a = i * math.pi / 6
        c, s = math.sin(a), -math.cos(a)
        ticks.append(A.seg(tx + c * (R - 66), ty + s * (R - 66), tx + c * (R - 90 - (12 if i % 3 == 0 else 0)),
                           ty + s * (R - 90 - (12 if i % 3 == 0 else 0)), 12 if i % 3 == 0 else 8))
    ic.ink(A.U(*ticks))
    a = math.radians(250)
    hand = A.U(A.seg(tx, ty, tx + math.sin(a) * (R - 78), ty - math.cos(a) * (R - 78), 16),
               A.seg(tx, ty, tx - math.sin(a) * 40, ty + math.cos(a) * 40, 16))
    ic.custom(hand, ic.h + (0.06 + 0.05 * A.H.dome(A.inner_dist(hand), 6)) * hand, C_INK, 0.3, 0.0)
    ic.part(A.circle(tx, ty, 24), z=0.56, lift=0.06, bevel=10, **brass_kw())
    return ic


def game_lab_mix():
    A = _A()
    ic = CIcon(102)
    cx, by, R = 512, 640, 262
    bulb = A.circle(cx, by, R)
    neck = A.box(cx, 330, 136, 330, 18)
    lip = A.box(cx, 170, 186, 46, 22)
    glass = A.U(bulb, neck, lip)
    # glass: dark, glossy, rounded; the liquid shows through as crimson
    gd = A.inner_dist(glass)
    ic.custom(glass, 0.20 + 0.20 * A.H.dome(gd, 60), (0.42, 0.50, 0.58), 0.06, 0.0)
    ic.glassy(glass, 0.30)
    liq = A.sub(A.circle(cx, by, R - 22), A.box(cx, by - 250, 700, 300))      # filled to y ~ by - 100
    wave = 8 * np.sin(A.xx / 38.0)
    liq = liq * A.smooth(by - 100 + wave - 2, by - 100 + wave + 2, A.yy)
    shade_y = np.clip((A.yy - (by - 100)) / (R + 100), 0, 1)
    lcol = (np.asarray((0.42, 0.04, 0.08), f32)[None, None] * (1 - shade_y[..., None] * 0.6)
            + np.asarray((0.90, 0.22, 0.22), f32)[None, None] * np.clip(1 - shade_y * 3, 0, 1)[..., None] * 0.25)
    ic._mat(liq, lcol, 0.12, 0.0)
    ic.solid(liq)
    ic.glow(liq, (0.55, 0.04, 0.08), 0.45)
    ic.glow(liq * np.exp(-((A.xx - cx) ** 2 + (A.yy - by - 40) ** 2) / (2 * 150 ** 2)), (1.0, 0.30, 0.22), 0.6)
    surf = A.smooth(6, 0, np.abs(A.yy - (by - 100 + wave))) * A.circle(cx, by, R - 22)
    ic._mat(surf, (1.0, 0.62, 0.55), None, None)
    ic.glow(surf, (1.0, 0.45, 0.35), 0.8)
    # bubbles in the liquid and rising out of the neck
    for (x, y, r) in ((430, 700, 26), (560, 760, 18), (610, 640, 30), (470, 600, 14), (520, 690, 11), (650, 740, 12),
                      (395, 790, 12), (500, 820, 20)):
        ic.recess(A.ring(x, y, r - 3, 6), 0.0, 2, alb=(1.0, 0.72, 0.66))
        ic.emboss(A.circle(x - r * 0.35, y - r * 0.35, r * 0.28), 0.03, 4, alb=(1, 0.95, 0.92))
    # gilt graduations and a crimson label band
    for i, y in enumerate(range(520, 800, 56)):
        ic.ink(A.box(cx - 150 + (0 if i % 2 else 14), y, 70 if i % 2 else 42, 9, 4), C_GOLD)
    # highlights on the glass
    hl = A.U(A.poly(A.bez((cx - 200, by - 120), (cx - 250, by - 20), (cx - 236, by + 110), (cx - 170, by + 180))
                    + A.bez((cx - 170, by + 180), (cx - 210, by + 100), (cx - 222, by - 20), (cx - 200, by - 120))),
             A.box(cx - 40, 300, 18, 220, 9))
    hl = ndimage.gaussian_filter(hl, 1.5) * glass
    ic._mat(hl * 0.85, (0.95, 0.96, 1.0), 0.05, None)
    ic.opac = np.maximum(ic.opac, hl * 0.95)
    ic.glow(hl * 0.6, (0.9, 0.92, 1.0), 0.5)
    # brass collar on the neck
    ic.part(A.box(cx, 236, 162, 40, 12), z=0.46, lift=0.1, bevel=10, **brass_kw())
    ic.groove(A.box(cx, 236, 162, 6, 3), 0.03, 0.2)
    # bubbles escaping the mouth
    for (x, y, r) in ((cx + 6, 110, 26), (cx - 52, 58, 18), (cx + 60, 40, 14), (cx - 10, 4 + 16, 10)):
        b = A.circle(x, y, r)
        ic.part(b, z=0.36, lift=0.14, bevel=r * 0.9, alb=(0.92, 0.55, 0.52), rough=0.08, mottle=0)
        ic.emboss(A.circle(x - r * 0.35, y - r * 0.35, r * 0.3), 0.04, 4, alb=(1, 0.97, 0.95))
        ic.glow(b, (0.6, 0.1, 0.1), 0.25)
    return ic


def letter_tile(ic, cx, cy, rot, ch, face, ink, num):
    A = _A()
    W = lambda u, v: A.to_world(cx, cy, rot, u, v)
    t = A.box(cx, cy, 250, 250, 36, rot)
    ic.part(t, z=0.20, lift=0.17, bevel=30, alb=face, rough=0.42 if face != C_BONE else 0.5, tex=0.01)
    ic.groove(A.sub(A.edge_line(t, 26), A.edge_line(t, 20)), 0.03, 0.18)
    L = tmask(ch, 180, *W(-4, -8), FONT_SERIF, rot)
    ic.recess(L, 0.05, 6, alb=ink, rough=0.3, metal=0.85 if ink == C_GOLD else 0.0)
    if num != "":
        ic.ink(tmask(str(num), 46, *W(84, 82), FONT_SERIF, rot), ink, 0.6)


def game_word_scramble():
    ic = CIcon(103)
    letter_tile(ic, 300, 330, -16, "E", C_BONE, C_INK, 1)
    letter_tile(ic, 716, 300, 12, "L", C_NIGHT, C_BONE, 2)
    letter_tile(ic, 330, 712, 9, "P", C_BONE, C_INK, 3)
    letter_tile(ic, 720, 700, -8, "S", C_CRIM, C_GOLD, 1)
    letter_tile(ic, 520, 510, 4, "?", C_BONE, C_CRIM, "")
    return ic


def index_card(ic, cx, cy, rot, z, mark):
    A = _A()
    W = lambda u, v: A.to_world(cx, cy, rot, u, v)
    card = A.box(cx, cy, 560, 380, 14, rot)
    ic.part(card, z=z, lift=0.08, bevel=14, alb=C_PAPER, rough=0.7, tex=0.008)
    ic.ink(A.box(*W(0, -110), 480, 9, 4, rot), C_CRIM_L, 0.5)
    for v in (-40, 20, 80, 140):
        ic.ink(A.box(*W(0, v), 480, 5, 2, rot), (0.42, 0.50, 0.66), 0.4)
    if mark == "date":
        ic.ink(tmask("1692", 130, *W(-60, -42), FONT_SERIF, rot))
    else:
        # a small inked tower
        u0, v0 = -150, 40
        tower = A.U(A.box(*W(u0, v0), 70, 170, 4, rot), A.poly([W(u0 - 50, v0 - 85), W(u0 + 50, v0 - 85), W(u0, v0 - 170)]))
        tower = A.U(tower, A.box(*W(u0, v0 + 82), 110, 14, 4, rot))
        tower = A.sub(tower, A.box(*W(u0, v0 - 20), 20, 40, 10, rot))
        ic.ink(tower)
        ic.ink(A.U(A.box(*W(80, -30), 220, 16, 8, rot), A.box(*W(60, 30), 180, 16, 8, rot)))


def game_match_the_past():
    A = _A()
    ic = CIcon(104)
    index_card(ic, 400, 300, -10, 0.14, "date")
    index_card(ic, 470, 560, 6, 0.22, "tower")
    # brass hourglass
    hx, hy = 760, 640
    ic.part(A.box(hx, hy - 236, 300, 46, 14), z=0.40, lift=0.12, bevel=14, **brass_kw())
    ic.part(A.box(hx, hy + 236, 300, 46, 14), z=0.40, lift=0.12, bevel=14, **brass_kw())
    for u in (-118, 118):
        ic.part(A.box(hx + u, hy, 26, 430, 12), z=0.38, lift=0.12, bevel=10, **brass_kw())
        for v in (-120, 0, 120):
            ic.emboss(A.ellipse(hx + u, hy + v, 20, 14), 0.06, 6)
    pts_r = []
    for t in np.linspace(-1, 1, 60):
        y = hy + t * 205
        w = 18 + 74 * (abs(t) ** 0.8) * (1 - 0.25 * abs(t) ** 6)
        pts_r.append((hx + w, y))
    pts = pts_r + [(2 * hx - x, y) for x, y in pts_r[::-1]]
    glass = A.poly(pts)
    ic.custom(glass, 0.40 + 0.12 * A.H.dome(A.inner_dist(glass), 30), (0.42, 0.50, 0.58), 0.06, 0.0)
    ic.glassy(glass, 0.32)
    sand_b = glass * (A.yy > hy + 110 - 70 * np.exp(-((A.xx - hx) / 46) ** 2))
    sand_b = ndimage.gaussian_filter(sand_b.astype(f32) * (A.yy > hy + 30), 1.0)
    sand_t = glass * (A.yy < hy - 16) * (A.yy > hy - 90 + 0.004 * (A.xx - hx) ** 2)
    sand_t = ndimage.gaussian_filter(sand_t.astype(f32), 1.0)
    stream = A.box(hx, hy + 40, 7, 160, 3) * glass
    sand = np.clip(sand_b + sand_t + stream, 0, 1)
    ic._mat(sand, (0.95, 0.74, 0.36), 0.7, 0.0)
    ic.solid(sand)
    ic.h += sand * 0.02
    ic.glow(sand, (0.5, 0.32, 0.1), 0.15)
    hl = ndimage.gaussian_filter(A.U(A.box(hx - 52, hy - 130, 12, 90, 6, -14), A.box(hx - 52, hy + 130, 12, 90, 6, 14)), 1.5) * glass
    ic._mat(hl * 0.8, (0.95, 0.96, 1.0), 0.05, None)
    ic.opac = np.maximum(ic.opac, hl * 0.95)
    return ic


def game_candle_vigil():
    A = _A()
    ic = CIcon(105)
    cx, cy, rx, ry = 512, 770, 400, 132
    # brass tray: a rim ring and a dished floor, drawn as an ellipse in perspective
    tray = A.ellipse(cx, cy, rx, ry)
    ic.part(tray, z=0.10, lift=0.10, bevel=26, **brass_kw(0.3))
    ic.recess(A.ellipse(cx, cy - 6, rx - 40, ry - 24), 0.05, 14)
    ic.emboss(A.U(*[A.circle(cx + (rx - 18) * math.cos(t), cy + (ry - 10) * math.sin(t), 8)
                    for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]), 0.04, 6)
    ic.part(A.box(cx, cy + ry + 14, 240, 40, 14), z=0.06, lift=0.08, bevel=10, **brass_kw())   # foot
    # five candles round the tray: back ones first, smaller and higher
    cand = []
    for k, a in enumerate((-140, -40, 180, 0, 128, 52, 90)):
        t = math.radians(a)
        x, y = cx + (rx - 92) * math.cos(t), cy - 10 + (ry - 46) * math.sin(t)
        cand.append((y, x, k))
    cand.sort()
    heights = {0: 300, 1: 260, 2: 230, 3: 250, 4: 330, 5: 280, 6: 380}
    for y, x, k in cand:
        hgt = heights[k] * (0.82 + 0.18 * (y - (cy - ry)) / (2 * ry))
        w = 60 + 14 * (y - (cy - ry)) / (2 * ry)
        z = 0.24 + 0.2 * (y - (cy - ry)) / (2 * ry)
        top = y - hgt
        ic.part(A.ellipse(x, y + 4, w * 0.95, w * 0.32), z=z - 0.04, lift=0.06, bevel=8, **brass_kw())
        body = A.U(A.box(x, (top + y) / 2, w, hgt, w * 0.22), A.ellipse(x, top + 3, w / 2, w * 0.16))
        dr = A.U(A.seg(x - w * 0.25, top + 6, x - w * 0.25, top + hgt * 0.30, w * 0.20),
                 A.circle(x - w * 0.25, top + hgt * 0.30, w * 0.13))
        ic.part(A.U(body, dr), z=z, lift=0.14, bevel=w * 0.42, alb=C_BONE, rough=0.42, tex=0.008)
        ic.ink(A.seg(x, top + 2, x, top - 20, 9))
        mini_flame(ic, x, top - 18, 104 if k != 3 else 60, 26 if k != 3 else 17, blue=(k == 3))
    return ic


def mini_sigil(ic, x, y, r, kind, lit=False):
    A = _A()
    d = A.circle(x, y, r)
    ic.part(d, z=0.24, lift=0.12, bevel=16, **brass_kw(0.3))
    ic.emboss(A.U(*[A.circle(x + (r - 12) * math.cos(t), y + (r - 12) * math.sin(t), 4.5)
                    for t in np.linspace(0, 2 * math.pi, 22, endpoint=False)]), 0.03, 4)
    f = A.circle(x, y, r - 22)
    ic.recess(f, 0.05, 6, alb=C_NIGHT if not lit else (0.35, 0.10, 0.14), rough=0.2, metal=0.0)
    s = r - 22
    if kind == "moon":
        m = A.sub(A.circle(x - s * 0.08, y, s * 0.66), A.circle(x + s * 0.20, y - s * 0.12, s * 0.56))
    elif kind == "eye":
        m = A.sub(A.ellipse(x, y, s * 0.72, s * 0.40), A.ellipse(x, y, s * 0.56, s * 0.27))
        m = A.U(m, A.circle(x, y, s * 0.22))
    elif kind == "star":
        pts = []
        for k in range(16):
            a = -math.pi / 2 + k * math.pi / 8
            rr = (s * 0.78 if (k // 2) % 2 == 0 else s * 0.52) if k % 2 == 0 else s * 0.22
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        m = A.poly(pts)
    else:   # key
        m = A.U(A.ring(x - s * 0.36, y, s * 0.22, s * 0.14), A.box(x + s * 0.14, y, s * 0.76, s * 0.13, 3),
                A.box(x + s * 0.40, y + s * 0.14, s * 0.12, s * 0.28, 2), A.box(x + s * 0.22, y + s * 0.12, s * 0.10, s * 0.2, 2))
    ic.emboss(m, 0.07, 6, alb=C_BONE if not lit else (1.0, 0.92, 0.80), rough=0.4, metal=0.0)
    if lit:
        ic.glow(m, (1.0, 0.55, 0.40), 2.4)
        ic.glow(f * (1 - m) * np.exp(-((A.xx - x) ** 2 + (A.yy - y) ** 2) / (2 * (s * 0.7) ** 2)), (0.95, 0.20, 0.16), 1.2)


def game_seance_sequence():
    A = _A()
    ic = CIcon(106)
    # the board: a crimson-lacquered slab with a gilt border and an arc of sigils
    bx, byy, rot = 512, 470, -4
    board = A.box(bx, byy, 860, 600, 60, rot)
    ic.part(board, z=0.10, lift=0.10, bevel=24, alb=C_CRIM, rough=0.32, tex=0.008, mottle=0.05)
    ic.ink(A.sub(A.edge_line(board, 34), A.edge_line(board, 26)), C_GOLD, 0.6)
    ic._mat(A.sub(A.edge_line(board, 34), A.edge_line(board, 26)), None, 0.3, 0.85)
    for u in (-360, 360):
        for v in (-230, 230):
            p = A.to_world(bx, byy, rot, u, v)
            ic.part(A.circle(*p, 16), z=0.24, lift=0.06, bevel=8, **brass_kw())
    kinds = ["moon", "eye", "key", "star"]
    for i, kd in enumerate(kinds):
        t = math.radians(-150 + i * 40)
        u, v = 300 * math.cos(t), 300 * math.sin(t) + 160
        x, y = A.to_world(bx, byy, rot, u, v)
        mini_sigil(ic, x, y, 92, kd, lit=(kd == "eye"))
    ex, ey = A.to_world(bx, byy, rot, 300 * math.cos(math.radians(-110)), 300 * math.sin(math.radians(-110)) + 160)
    # the planchette: a bone heart-shaped pointer with a brass rim and a lens, pointing at the lit sigil
    px, py, prot = 500, 700, -6
    P = lambda u, v: A.to_world(px, py, prot, u, v)
    pts = (A.bez(P(0, -250), P(40, -226), P(214, -70), P(210, 90)) + A.bez(P(210, 90), P(196, 190), P(90, 214), P(0, 170))
           + A.bez(P(0, 170), P(-90, 214), P(-196, 190), P(-210, 90)) + A.bez(P(-210, 90), P(-214, -70), P(-40, -226), P(0, -250)))
    pl = A.poly(pts)
    ic.part(pl, z=0.36, lift=0.14, bevel=36, alb=C_BONE, rough=0.42)
    ic.groove(A.sub(A.edge_line(pl, 22), A.edge_line(pl, 15)), 0.035, 0.0)
    ic._mat(A.sub(A.edge_line(pl, 22), A.edge_line(pl, 15)), C_GOLD, 0.3, 0.85)
    lx, ly = P(0, 10)
    ic.part(A.circle(lx, ly, 96), z=0.48, lift=0.1, bevel=16, **brass_kw(0.28))
    lens = A.circle(lx, ly, 72)
    ic.custom(lens, 0.50 + 0.10 * A.H.dome(A.inner_dist(lens), 40), (0.20, 0.06, 0.09), 0.05, 0.0, cast=False)
    ic.cast = np.maximum(ic.cast, ndimage.gaussian_filter(np.roll(np.roll(1 - lens, 7, 0), 5, 1), 7) * lens)
    eye = A.U(A.sub(A.ellipse(lx, ly, 46, 26), A.ellipse(lx, ly, 34, 16)), A.circle(lx, ly, 12))
    ic._mat(eye, (1.0, 0.75, 0.62), None, None)
    ic.glow(eye, (1.0, 0.35, 0.28), 1.4)
    ic.glow(lens * np.exp(-((A.xx - lx) ** 2 + (A.yy - ly) ** 2) / (2 * 40 ** 2)), (0.7, 0.08, 0.10), 0.8)
    ic._mat(ndimage.gaussian_filter(A.ellipse(lx - 30, ly - 34, 24, 12, -35), 1.2) * lens, (1, 1, 1), 0.04, None)
    # three small brass feet and a pointer tip stud
    for u, v in ((-150, 150), (150, 150), (0, -200)):
        ic.part(A.circle(*P(u, v), 16), z=0.52, lift=0.06, bevel=8, **brass_kw())
    return ic


GAME_FUNCS = {"GamePopQuiz": game_pop_quiz, "GameLabMix": game_lab_mix, "GameWordScramble": game_word_scramble,
              "GameMatchThePast": game_match_the_past, "GameCandleVigil": game_candle_vigil,
              "GameSeanceSequence": game_seance_sequence}


def make_game_icons(names=GAMES):
    out = []
    for n in names:
        ic = GAME_FUNCS[n]()
        rgb, a = ic.render()
        p = save_rgba(rgb, a, OUT / f"{n}.png", 2)
        print("icon", p)
        out.append(p)
    return out


# ================================================================ contact sheet
def contact_sheet():
    board = (0x22, 0x3C, 0x2E)
    W, Hh = 1100, 860
    im = Image.new("RGBA", (W, Hh), board + (255,))
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(FONT, 18)
    fs = ImageFont.truetype(FONT, 14)
    chalk = (226, 230, 214, 255)
    d.text((30, 18), "Seance Sequence: sigils at 110 px (idle / lit)", font=ft, fill=chalk)
    for i, n in enumerate(SIGILS):
        x = 30 + i * 172
        for j, stt in enumerate(("idle", "lit")):
            p = OUT / f"{n}_{stt}.png"
            if p.exists():
                im.alpha_composite(Image.open(p).convert("RGBA").resize((110, 110), Image.LANCZOS), (x + 20, 56 + j * 128))
        d.text((x + 75, 312), n.replace("Sigil", ""), font=fs, fill=chalk, anchor="mm")
    d.text((30, 340), "Candle Vigil: candle at 90 x 180 (body / lit / guttering / out)", font=ft, fill=chalk)
    body_p = OUT / "CandleBody.png"
    if body_p.exists():
        body = Image.open(body_p).convert("RGBA")
        sc = 90 / body.size[0]
        b = body.resize((90, 180), Image.LANCZOS)
        wx, wy = WICK_TIP
        states = [("body", None), ("lit", "CandleFlame.png"), ("guttering", "CandleGutter.png"), ("out", "CandleSmoke.png")]
        for i, (lab, over_) in enumerate(states):
            x, y = 60 + i * 200, 425
            im.alpha_composite(b, (x, y))
            if over_ and (OUT / over_).exists():
                f = Image.open(OUT / over_).convert("RGBA").resize((90, 90), Image.LANCZOS)
                im.alpha_composite(f, (int(round(x + wx * sc - 128 * sc)), int(round(y + wy * sc - 208 * sc))))
            d.text((x + 45, 618), lab, font=fs, fill=chalk, anchor="mm")
    d.text((30, 646), "Lesson board: game icons at 128 px", font=ft, fill=chalk)
    for i, n in enumerate(GAMES):
        p = OUT / f"{n}.png"
        x = 30 + i * 176
        if p.exists():
            im.alpha_composite(Image.open(p).convert("RGBA").resize((128, 128), Image.LANCZOS), (x + 10, 682))
        d.text((x + 74, 830), n.replace("Game", ""), font=fs, fill=chalk, anchor="mm")
    im.save(OUT / "contact_sheet.png")
    return OUT / "contact_sheet.png"


WICK_TIP = (128.0, 80.0)      # replaced by make_candle()


def copy_uploads(paths):
    UPLOAD.mkdir(parents=True, exist_ok=True)
    for p in paths:
        shutil.copy2(p, UPLOAD / f"SubGame_{Path(p).name}")


if __name__ == "__main__":
    what = sys.argv[1:] or ["sigils", "candle", "icons"]
    made = []
    if "sigils" in what:
        made += make_sigils()
    if "candle" in what:
        made += make_candle()
    if "icons" in what:
        made += make_game_icons()
    print(contact_sheet())
    if set(what) >= {"sigils", "candle", "icons"}:
        copy_uploads(made)
        print("copied", len(made), "files to", UPLOAD)
