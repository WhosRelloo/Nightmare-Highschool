"""Props batch 21 (2026-11-04): the painting and art kit for nh_props.py, on theme with the Institution: gilt and black
lacquer frames, crimson, iron and brass, candlelight. Every painting's canvas is its own Canvas piece carrying a 2048
painting from paint_canvases.py (front-projected, not squeezed into the frame's atlas), so the brushwork stays sharp.

  PaintingAbbey     6 x 4: a ruined abbey under the full moon; a carved gilt frame with rosette corners and a crocketed
                    crest holding a crimson cartouche
  PaintingBloodMoon 4 x 3: a wolf howling at a blood moon; black lacquer with a gilt slip and gilt quatrefoil corners;
                    a picture light
  PaintingGhostShip 5 x 3.3: a ghost galleon in a moonlit storm; an ebonised frame with a gilt rope moulding; a light
  PaintingRaven     3 x 4, lancet-arched: a raven on a skull by candlelight; a pointed gilt frame with crockets
  CameoSilhouette   1.5 x 2 oval: the founder's silhouette on crimson; an oval gilt frame with a crimson bow
  Triptych          three arched panels in gilt (the crest's moon, raven and key, candle) with pinnacles on a crimson
                    and gilt predella
  GalleryStanchions two brass posts with a sagging crimson velvet rope, 6 apart
  CanvasStack       canvases leaning on the wall, backs out, one under a crimson drape, a gilt frame, paint pots
  PainterTable      an iron painter's table: a palette of paints, brush jars, paint tubes, rags, a small skull and a
                    candle (Glow)

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their backs flat at +Y. Paintings hang
with their bottom at the origin. Registered into nh_props.BUILD on import.
"""
import math
import random

from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere, cone, circle_pts, flame
from nh_props_batch4 import lathe, hoop, prism, strip, _mark, _xform, _dims, flat, _smooth
from nh_props_batch8 import _pointed, _spirelet, _crockets
from nh_props_batch9 import foil, candle, wax_mat
from nh_props_batch10 import gilt, lacquer, velvet, black_marble, _skull
import nh_props_batch20 as B20


# ------------------------------------------------------------------ frames

def frame_gilt():
    """Picture-frame gold: smooth and clean (no brass grain over its broad mouldings), a little rubbed on the high edges,
    dirt only in the crevices."""
    return P.material("FrameGilt", base=(0.78, 0.56, 0.22), rough=0.32, metal=1.0, wear=0.12, dirt=0.45)


def _rect(hw, hh, zc, n=1):
    return [(-hw, zc - hh), (hw, zc - hh), (hw, zc + hh), (-hw, zc + hh)]


def _oval(hw, hh, zc, n=48):
    return [(math.cos(a) * hw, zc + math.sin(a) * hh) for a in [k / n * 2 * math.pi for k in range(n)]]


def _arch(hw, z0, zs, za, n=12):
    """A lancet outline (x, z): the foot line, then up the right jamb over the point and down the left."""
    return [(-hw, z0), (hw, z0)] + list(reversed(_pointed(hw, zs, za, n)))


def _grow(pts, d):
    """Offset a closed outline outward by about d (from its centroid)."""
    cx = sum(x for x, _ in pts) / len(pts)
    cz = sum(z for _, z in pts) / len(pts)
    out = []
    for i, (x, z) in enumerate(pts):
        px, pz = pts[i - 1]
        nx, nz = pts[(i + 1) % len(pts)]
        tx, tz = nx - px, nz - pz
        L = math.hypot(tx, tz) or 1
        ox, oz = tz / L, -tx / L
        if (x - cx) * ox + (z - cz) * oz < 0:
            ox, oz = -ox, -oz
        out.append((x + ox * d, z + oz * d))
    return out


def _canvas(name, outline, y=0.0):
    """The painting itself (group Canvas): a thin board in the outline, its face at y."""
    set_group("Canvas")
    B20.tprism(name, outline, y + 0.02, 0.04, flat("CanvasTmp", (0.5, 0.5, 0.5), 0.5))
    set_group("Main")


def _frame(prefix, outline, mats, y=0.0, widths=(0.16, 0.045, 0.05), back=0.18):
    """A moulded frame round a canvas outline: a broad square-section body (mats[0]), a gilt bead on its outer edge, a
    gilt slip at the sight edge (mats[1]), a backing board."""
    body, slip = mats
    fw, bead, sl = widths
    mid = _grow(outline, fw)
    tube(f"{prefix}Body", [(x, y - 0.06, z) for x, z in mid], fw, body, closed=True, square=True, poly=True)
    tube(f"{prefix}Bead", [(x, y - 0.12, z) for x, z in _grow(outline, fw * 1.85)], bead, slip, closed=True, poly=True)
    tube(f"{prefix}Slip", [(x, y - 0.035, z) for x, z in _grow(outline, sl * 0.6)], sl, slip, closed=True, square=True, poly=True)
    tube(f"{prefix}Cove", [(x, y - 0.2, z) for x, z in _grow(outline, fw * 0.9)], fw * 0.35, slip, closed=True, poly=True)
    B20.tprism(f"{prefix}Back", _grow(outline, fw * 1.6), y + back / 2 + 0.04, back, body)
    return mid


def _picture_light(prefix, x, w, z, M, gl):
    """A brass picture light on an arm over the frame top (its tube Glow)."""
    brass = M["brass"]
    box(f"{prefix}Plate", (0.22, 0.04, 0.28), (x, 0.2, z), brass, bevel=0.01)
    tube(f"{prefix}Arm", [(x, 0.18, z + 0.05), (x, -0.15, z + 0.35), (x, -0.42, z + 0.38)], 0.025, brass)
    cyl(f"{prefix}Hood", 0.1, w, (x, -0.47, z + 0.36), brass, rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    for sx in (-1, 1):
        cyl(f"{prefix}End{sx}", 0.11, 0.02, (x + sx * w / 2, -0.47, z + 0.36), gl, rot=(0, math.pi / 2, 0), verts=16, bevel=0.005)
    set_group("Glow")
    cyl(f"{prefix}Tube", 0.035, w - 0.08, (x, -0.49, z + 0.3), flat("Bulb", (1.0, 0.8, 0.5), 0.4), rot=(0, math.pi / 2, 0), verts=10, bevel=0)
    set_group("Main")


# ------------------------------------------------------------------ the paintings

def painting_abbey(M):
    gl = frame_gilt()
    W, H = 6.0, 4.0
    zc = H / 2 + 0.35
    outline = _rect(W / 2, H / 2, zc)
    _canvas("Canvas", outline)
    _frame("F", outline, (gl, gl), widths=(0.22, 0.05, 0.06))
    # carved corner rosettes and a crocketed crest with a cartouche
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"Corner{sx}{sz}", sx * (W / 2 + 0.22), -0.3, zc + sz * (H / 2 + 0.22), 0.16, gl, thick=0.03)
    crest = [(-1.1, zc + H / 2 + 0.4), (1.1, zc + H / 2 + 0.4)] + [(x, z) for x, z in reversed(_pointed(1.1, zc + H / 2 + 0.4, zc + H / 2 + 1.25, 12))]
    B20.tprism("Crest", crest, -0.08, 0.12, gl, bevel=0.01)
    _crockets("Crocket", [(x, -0.12, z + 0.06) for x, z in _pointed(1.12, zc + H / 2 + 0.42, zc + H / 2 + 1.27, 8)[1:-1]], gl, size=0.07)
    sphere("CrestFinial", 0.1, (0, -0.1, zc + H / 2 + 1.4), gl, seg=12, rings=6)
    B20._crest("Cartouche", 0, -0.16, zc + H / 2 + 0.75, M, gl, s=0.9)
    return _dims()


def painting_bloodmoon(M):
    gl, lq = frame_gilt(), lacquer()
    W, H = 4.0, 3.0
    zc = H / 2 + 0.3
    outline = _rect(W / 2, H / 2, zc)
    _canvas("Canvas", outline)
    _frame("F", outline, (lq, gl), widths=(0.2, 0.04, 0.05))
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"Corner{sx}{sz}", sx * (W / 2 + 0.2), -0.29, zc + sz * (H / 2 + 0.2), 0.12, gl, thick=0.025)
    _picture_light("PL", 0, 2.0, zc + H / 2 + 0.22, M, gl)
    return _dims()


def painting_ghostship(M):
    gl = frame_gilt()
    ebony = flat("Ebony", (0.02, 0.018, 0.02), 0.35, wear=0.15, dirt=0.6)
    W, H = 5.0, 5.0 / 1.5
    zc = H / 2 + 0.3
    outline = _rect(W / 2, H / 2, zc)
    _canvas("Canvas", outline)
    mid = _frame("F", outline, (ebony, gl), widths=(0.2, 0.04, 0.05))
    # a twisted gilt rope moulding round the frame's face
    rope = _grow(outline, 0.2)
    pts = []
    for (ax, az), (bx, bz) in zip(rope, rope[1:] + rope[:1]):
        n = int(math.hypot(bx - ax, bz - az) / 0.08)
        for k in range(n):
            t = k / n
            pts.append((ax + (bx - ax) * t, az + (bz - az) * t))
    for i in range(0, len(pts), 2):
        x, z = pts[i]
        sphere(f"Rope{i}", 0.05, (x, -0.27, z), gl, seg=8, rings=4, scale=(1.3, 0.8, 0.8))
    _picture_light("PL", 0, 2.2, zc + H / 2 + 0.22, M, gl)
    return _dims()


def painting_raven(M):
    gl = frame_gilt()
    W, H = 3.0, 4.0
    z0 = 0.35
    outline = _arch(W / 2, z0, z0 + H * 0.68, z0 + H)
    _canvas("Canvas", outline)
    _frame("F", outline, (gl, gl), widths=(0.2, 0.045, 0.05))
    _crockets("Crocket", [(x, -0.22, z + 0.05) for x, z in _grow(_pointed(W / 2, z0 + H * 0.68, z0 + H, 10), 0.4)][1:-1], gl, size=0.07)
    sphere("Finial", 0.11, (0, -0.15, z0 + H + 0.55), gl, seg=12, rings=6)
    box("Sill", (W + 0.7, 0.36, 0.14), (0, -0.05, z0 - 0.28), gl, bevel=0.03)
    B20._crest("Plaque", 0, -0.24, z0 - 0.28, M, gl, s=0.4)
    return _dims()


def cameo_silhouette(M):
    gl = frame_gilt()
    W, H = 1.5, 2.0
    zc = H / 2 + 0.25
    outline = _oval(W / 2, H / 2, zc)
    _canvas("Canvas", outline)
    _frame("F", outline, (gl, gl), widths=(0.12, 0.035, 0.035), back=0.12)
    # a pierced gilt laurel ring of leaves round the oval and a crimson velvet bow on top
    ring = _grow(outline, 0.24)
    for k in range(0, len(ring), 2):
        x, z = ring[k]
        sphere(f"Leaf{k}", 0.05, (x, -0.16, z), gl, seg=6, rings=4, scale=(1.6, 0.5, 0.8))
    bow = velvet()
    for sx in (-1, 1):
        sphere(f"BowLoop{sx}", 0.16, (sx * 0.2, -0.14, zc + H / 2 + 0.38), bow, seg=12, rings=6, scale=(1.4, 0.4, 0.8))
        strip(f"BowTail{sx}", [(sx * 0.05, -0.14, zc + H / 2 + 0.3), (sx * 0.15, -0.16, zc + H / 2 - 0.1), (sx * 0.12, -0.15, zc + H / 2 - 0.45)], 0.11,
              (1, 0, 0), bow, thick=0.02)
    sphere("BowKnot", 0.08, (0, -0.17, zc + H / 2 + 0.36), bow, seg=10, rings=6)
    return _dims()


def triptych(M):
    gl = frame_gilt()
    cr = M["crimsonin"]
    pw, gap = 1.3, 0.12
    Htot = (3 * pw + 2 * gap) / 1.5            # the image is 3:2 across the three panels
    z0 = 0.75
    outlines = []
    for k, (cx, top) in enumerate(((-(pw + gap), Htot * 0.84), (0.0, Htot), (pw + gap, Htot * 0.84))):
        o = [(cx + x, z) for x, z in _arch(pw / 2, z0, z0 + top * 0.62, z0 + top)]
        outlines.append(o)
    # one Canvas piece holding all three panels, so the image's thirds land on them
    set_group("Canvas")
    for k, o in enumerate(outlines):
        B20.tprism(f"Panel{k}", o, 0.02, 0.04, flat("CanvasTmp", (0.5, 0.5, 0.5), 0.5))
    set_group("Main")
    for k, o in enumerate(outlines):
        tube(f"Frame{k}", [(x, -0.05, z) for x, z in _grow(o, 0.09)], 0.09, gl, closed=True, square=True, poly=True)
        tube(f"Bead{k}", [(x, -0.12, z) for x, z in _grow(o, 0.17)], 0.03, gl, closed=True, poly=True)
        apex = max(z for _, z in o)
        cx = sum(x for x, _ in o) / len(o)
        _crockets(f"Crock{k}", [(x, -0.14, z + 0.04) for x, z in _grow(_pointed(pw / 2, apex - (apex - z0) * 0.38, apex, 8), 0.26)][1:-1], gl, size=0.06)
        sphere(f"Fin{k}", 0.08, (cx, -0.1, apex + 0.35), gl, seg=10, rings=5)
    for sx in (-1, 1):
        x = sx * (pw / 2 + gap / 2)
        box(f"Buttress{sx}", (0.16, 0.24, Htot * 0.8), (x, -0.04, z0 + Htot * 0.4), gl, bevel=0.02)
        _spirelet(f"Pin{sx}", x, -0.04, z0 + Htot * 0.8, 0.9, 0.2, gl, crockets=2)
    for sx in (-1, 1):
        x = sx * (1.5 * pw + gap + 0.08)
        box(f"Outer{sx}", (0.16, 0.24, Htot * 0.7), (x, -0.04, z0 + Htot * 0.35), gl, bevel=0.02)
        _spirelet(f"OPin{sx}", x, -0.04, z0 + Htot * 0.7, 0.8, 0.2, gl, crockets=2)
    Wt = 3 * pw + 2 * gap + 0.6
    box("Predella", (Wt, 0.4, z0 - 0.1), (0, 0.05, (z0 - 0.1) / 2), cr, bevel=0.03)
    box("PredellaTop", (Wt + 0.1, 0.46, 0.08), (0, 0.05, z0 - 0.06), gl, bevel=0.02)
    box("PredellaFoot", (Wt + 0.1, 0.46, 0.08), (0, 0.05, 0.04), gl, bevel=0.02)
    for k in range(5):
        foil(f"PFoil{k}", -Wt / 2 + 0.55 + k * (Wt - 1.1) / 4, -0.16, z0 / 2, 0.13, gl, thick=0.02)
    B20.tprism("Back", [(-Wt / 2, 0), (Wt / 2, 0), (Wt / 2, z0 + Htot * 0.75), (0, z0 + Htot + 0.25), (-Wt / 2, z0 + Htot * 0.75)], 0.16, 0.2,
               lacquer())
    return _dims()


# ------------------------------------------------------------------ the gallery and the studio

def gallery_stanchions(M):
    brass, gl = M["brass"], gilt()
    rope = velvet()
    S = 3.0
    for sx in (-1, 1):
        x = sx * S
        lathe(f"Base{sx}", [(0, 0), (0.36, 0), (0.37, 0.04), (0.3, 0.1), (0.14, 0.16), (0.08, 0.24), (0, 0.24)], brass, seg=32, loc=(x, 0, 0))
        lathe(f"Post{sx}", [(0, 0.22), (0.06, 0.22), (0.055, 2.9), (0.09, 2.95), (0.06, 3.0), (0, 3.0)], brass, seg=20, loc=(x, 0, 0))
        hoop(f"Collar{sx}", (x, 0, 1.5), 0.065, "Z", gl, thick=0.015)
        sphere(f"Ball{sx}", 0.12, (x, 0, 3.1), brass, seg=16, rings=8)
        hoop(f"Eye{sx}", (x - sx * 0.08, 0, 2.85), 0.05, "Y", brass, thick=0.014)
        sphere(f"Hook{sx}", 0.06, (x - sx * 0.11, 0, 2.82), gl, seg=10, rings=5, scale=(1, 1, 1.4))
    pts = []
    for k in range(25):
        t = k / 24
        x = -S + 0.12 + (2 * S - 0.24) * t
        pts.append((x, 0, 2.8 - 0.62 * math.sin(math.pi * t)))
    tube("Rope", pts, 0.06, rope)
    return _dims()


def canvas_stack(M):
    rnd = random.Random(213)
    gl = gilt()
    linen = flat("Linen", (0.6, 0.54, 0.44), 0.9, dirt=0.6)
    stretcher = M["oakdark"]
    cloth = velvet()
    for k, (w, h, x, lean) in enumerate(((2.6, 3.4, -0.6, 0.22), (2.0, 2.6, 0.4, 0.26), (1.6, 2.0, 1.2, 0.3), (3.0, 2.2, -1.4, 0.18))):
        s = _mark()
        box(f"Linen{k}", (w, 0.03, h), (0, 0, h / 2), linen, bevel=0.01)
        for sz in (0.06, h - 0.06):
            box(f"BarH{k}{sz:.1f}", (w, 0.08, 0.1), (0, 0.055, sz), stretcher, bevel=0.012)
        for sx in (-1, 1):
            box(f"BarV{k}{sx}", (0.1, 0.08, h), (sx * (w / 2 - 0.05), 0.055, h / 2), stretcher, bevel=0.012)
        box(f"Brace{k}", (0.08, 0.06, h - 0.1), (0, 0.06, h / 2), stretcher, bevel=0.01)
        _xform(s, Matrix.Translation((x, 0.7 - h * math.sin(lean) - k * 0.06, 0)) @ Matrix.Rotation(-lean, 4, "X") @ Matrix.Rotation(-math.pi, 4, "Z"))
    # an empty gilt frame leaning in front, a crimson drape over the tallest canvas, paint pots and a jar of brushes
    s = _mark()
    for sx in (-1, 1):
        box(f"FrameV{sx}", (0.18, 0.1, 2.0), (sx * 0.75, 0, 1.0), gl, bevel=0.03)
    for sz in (0.09, 1.91):
        box(f"FrameH{sz}", (1.68, 0.1, 0.18), (0, 0, sz), gl, bevel=0.03)
    for sx in (-1, 1):
        for sz in (0.09, 1.91):
            foil(f"FrameCorner{sx}{sz}", sx * 0.75, -0.06, sz, 0.11, gl, thick=0.02)
    _xform(s, Matrix.Translation((0.9, -0.3, 0)) @ Matrix.Rotation(-0.25, 4, "X"))
    strip("Drape", [(-1.8, -0.15, 3.3), (-1.0, -0.25, 3.35), (-0.4, -0.35, 3.0), (-0.3, -0.5, 2.0), (-0.45, -0.6, 0.9), (-0.3, -0.7, 0.05)],
          1.4, (1, 0, 0.1), cloth, thick=0.03)
    pots = [flat(f"Paint{n}", c, 0.4, dirt=0.4) for n, c in (("Crimson", (0.4, 0.03, 0.04)), ("Ochre", (0.55, 0.38, 0.1)), ("Ultra", (0.08, 0.1, 0.4)))]
    for k, p in enumerate(pots):
        x = -1.8 + k * 0.4
        lathe(f"Pot{k}", [(0, 0), (0.13, 0), (0.14, 0.22), (0.12, 0.24), (0, 0.24)], M["iron"], seg=16, loc=(x, -1.0, 0))
        lathe(f"PotPaint{k}", [(0, 0.2), (0.12, 0.2), (0, 0.23)], p, seg=16, loc=(x, -1.0, 0))
        tube(f"PotDrip{k}", [(x + 0.135, -1.0, 0.23), (x + 0.142, -1.0, 0.1)], 0.014, p, poly=True)
    lathe("Jar", [(0, 0), (0.11, 0), (0.12, 0.32), (0.1, 0.33), (0, 0.33)], M["brass"], seg=16, loc=(-0.7, -1.05, 0))
    for k in range(6):
        a = k / 6 * 2 * math.pi
        tube(f"Brush{k}", [(-0.7 + math.cos(a) * 0.04, -1.05 + math.sin(a) * 0.04, 0.1), (-0.7 + math.cos(a) * 0.11, -1.05 + math.sin(a) * 0.09, 0.8)],
             0.012, M["felt"] if k % 2 else M["brass"], poly=True)
    return _dims()


def painter_table(M):
    rnd = random.Random(214)
    gl, iron = gilt(), M["iron"]
    W, D, Ht = 3.0, 1.5, 2.8
    box("Top", (W, D, 0.1), (0, 0, Ht - 0.05), black_marble(), bevel=0.02)
    box("Apron", (W - 0.2, D - 0.2, 0.18), (0, 0, Ht - 0.19), iron, bevel=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), Ht - 0.28), (sx * (W / 2 - 0.12), sy * (D / 2 - 0.12), 1.4),
                                  (sx * (W / 2 - 0.2), sy * (D / 2 - 0.2), 0.3), (sx * (W / 2 - 0.08), sy * (D / 2 - 0.08), 0.03)], 0.05, iron,
                 square=True)
            sphere(f"Foot{sx}{sy}", 0.07, (sx * (W / 2 - 0.08), sy * (D / 2 - 0.08), 0.05), gl, seg=10, rings=5)
    box("Shelf", (W - 0.5, D - 0.5, 0.06), (0, 0, 0.6), iron, bevel=0.01)
    z = Ht
    # the palette with paint, brushes in jars, tubes, rags, a small skull and the candle
    ivory = flat("Ivory", (0.78, 0.72, 0.6), 0.5, dirt=0.5)
    pal = [(math.cos(a) * 0.55, math.sin(a) * 0.38) for a in [k / 24 * 2 * math.pi for k in range(24)]]
    B20.tprism("Palette", pal, z, 0.03, ivory, plane="XY", bevel=0.008)
    _xform(len(P.PARTS) - 1, Matrix.Translation((-0.6, -0.15, 0)) @ Matrix.Rotation(0.3, 4, "Z"))
    cols = ((0.42, 0.03, 0.04), (0.6, 0.42, 0.1), (0.85, 0.82, 0.74), (0.08, 0.1, 0.42), (0.05, 0.12, 0.06), (0.03, 0.02, 0.02), (0.5, 0.12, 0.05))
    for k, c in enumerate(cols):
        a = k / len(cols) * 4.2 + 0.4
        sphere(f"Blob{k}", 0.06, (-0.6 + math.cos(a) * 0.4, -0.15 + math.sin(a) * 0.25, z + 0.04), flat(f"Blob{k}", c, 0.3, dirt=0.2), seg=10, rings=5,
               scale=(1.3, 1.0, 0.45))
    for j, (x, y) in enumerate(((0.55, 0.35), (0.85, 0.2))):
        lathe(f"Jar{j}", [(0, z), (0.12, z), (0.13, z + 0.34), (0.11, z + 0.35), (0, z + 0.35)], M["brass"] if j else iron, seg=16, loc=(x, y, 0))
        for k in range(5):
            a = k / 5 * 2 * math.pi + j
            tip = (x + math.cos(a) * 0.12, y + math.sin(a) * 0.1, z + 0.85 + rnd.uniform(-0.1, 0.1))
            tube(f"Brush{j}{k}", [(x + math.cos(a) * 0.04, y + math.sin(a) * 0.04, z + 0.05), tip], 0.012, M["felt"], poly=True)
            cone(f"Bristle{j}{k}", 0.022, 0.0, 0.1, (tip[0], tip[1], tip[2] + 0.04), M["chalk"] if k % 2 else flat("Wet", (0.35, 0.03, 0.04), 0.3),
                 verts=6)
    for k in range(4):
        x, y = 0.0 + k * 0.17, -0.45 + rnd.uniform(-0.05, 0.05)
        cyl(f"Tube{k}", 0.035, 0.26, (x, y, z + 0.035), M["brasssteel"], rot=(0, math.pi / 2, rnd.uniform(-0.3, 0.3)), verts=10, bevel=0.01)
        box(f"Crimp{k}", (0.06, 0.08, 0.012), (x - 0.15, y, z + 0.035), M["brasssteel"], bevel=0.004)
    sphere("Rag", 0.22, (0.4, -0.25, z + 0.06), flat("Rag", (0.5, 0.44, 0.36), 0.95, dirt=0.8), seg=12, rings=8, scale=(1.4, 1.0, 0.35))
    _skull("Skull", Matrix.Translation((-1.15, 0.35, z)) @ Matrix.Scale(0.7, 4) @ Matrix.Rotation(0.5, 4, "Z"), M["chalk"], M["felt"])
    lathe("CandleDish", [(0, z), (0.13, z), (0.14, z + 0.03), (0.06, z + 0.04), (0, z + 0.04)], M["brass"], seg=16, loc=(1.15, -0.35, 0))
    tip = candle("Candle", 1.15, -0.35, z + 0.04, 0.35, wax_mat(), r=0.045)
    set_group("Glow")
    flame("Flame", (1.15, -0.35, tip - 0.005), h=0.11)
    set_group("Main")
    return _dims()


P.CANVAS.update({"PaintingAbbey_Canvas": "PaintingAbbey", "PaintingBloodMoon_Canvas": "PaintingBloodMoon", "PaintingGhostShip_Canvas": "PaintingGhostShip",
                 "PaintingRaven_Canvas": "PaintingRaven", "CameoSilhouette_Canvas": "CameoSilhouette", "Triptych_Canvas": "Triptych"})
P.PREVIEW_PAD.update({"PaintingAbbey": 1.05, "PaintingBloodMoon": 1.1, "PaintingGhostShip": 1.05, "PaintingRaven": 1.1, "CameoSilhouette": 1.3,
                      "Triptych": 1.1, "GalleryStanchions": 1.0, "CanvasStack": 1.1, "PainterTable": 1.1})
P.BUILD.update({
    "PaintingAbbey": painting_abbey,
    "PaintingBloodMoon": painting_bloodmoon,
    "PaintingGhostShip": painting_ghostship,
    "PaintingRaven": painting_raven,
    "CameoSilhouette": cameo_silhouette,
    "Triptych": triptych,
    "GalleryStanchions": gallery_stanchions,
    "CanvasStack": canvas_stack,
    "PainterTable": painter_table,
})
