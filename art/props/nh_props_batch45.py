"""Props batch 45, the interiors kit (2026-11-10), for nh_props.py: homes phase 2, the shared building interiors the builder
places by hand in the Map place. A Victorian-gothic general store (MORROW & VANE, Purveyors of Sundries), a dark bookseller
(LANTERNLIGHT BOOKS) and a candlelit cafe (THE WICK & KETTLE), in the house look of batches 34-43: cast iron, black marble,
crimson enamel, brass and gilt, glass, ink and paper; wood only for books, crates and accents. Every name and label is invented.

Counter    ShopCounter, ShopCounterCorner (Glass, Glow), ShopCounterEnd (Door0), CashRegister (Drawer0, Glass), ShopScales,
           CounterBell (plinth), WrapStand
Display    DisplayCase (Glass), GlassCabinetTall (Door0, Glass), WallShelfStocked (wall), IslandShelf, ApothecaryDrawers (wall),
           SweetJarShelf (wall, Glass), PostcardSpinner, StockSacks, StockCrates
Bookshop   BookshopCounter (Glass), NewReleasesTable, BookStandAngled, BargainBinCart, StaffPicksEasel
Cafe       CafeBarCounter (Glass, Glow), BarStool, CafeBackShelf (wall, Mirror)
Fittings   OpenClosedSign (wall), ShopSignInterior (ceiling), PriceTagRail (wall), DoorBellBracket (wall), ShopStool,
           HatUmbrellaStand (wall)

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back on y = 0 (pivot on the wall plane at
their lowest point). The counters are 2.2 deep with their front on y = -1.1 (the marble's nosing to -1.22) and 3.4 tall, so
ShopCounter (6 long), ShopCounterCorner (a quarter round, 2.2 square) and ShopCounterEnd line up. Printed faces come from
art/props/interiors_atlas.py (InteriorsPrint), books from the library atlas (batch 30). Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _quatrefoil
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, prism, _mark, _xform, _dims, flat, _solid
import nh_props_batch24 as B24
import nh_props_batch30 as B30
import nh_props_batch43 as B43

DEG = math.pi / 180
PI = math.pi
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
arch_xz, circ, rect, finial, castor, rivet = B43.arch_xz, B43.circ, B43.rect, B43.finial, B43.castor, B43.rivet

_tube = P.tube


def tube(name, points, radius, mat, closed=False, res=4, square=False, poly=False):
    """nh_props.tube, but a square bar's faces are turned outward (its bevel profile winds the other way, so as built its
    normals point in: the bake's AO then darkens it to black and Roblox would cull its outside)."""
    ob = _tube(name, points, radius, mat, closed=closed, res=res, square=square, poly=poly)
    if square:
        ob.data.flip_normals()
    return ob


IA = json.load(open(os.path.join(P.HERE, "interiors_atlas.json")))
for _k, _v in IA["regions"]["InteriorsPrint"].items():
    B30.REG["IN_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_IN_" + _k[7:]] = _v

H_C, D_C = 3.4, 2.2          # counter height and depth
PAD = {"ShopCounterCorner": 1.25, "WrapStand": 1.1, "DoorBellBracket": 1.6}
SMALLP = {"CounterBell": 1.05, "PriceTagRail": 1.0, "OpenClosedSign": 1.25, "ShopScales": 1.05, "CashRegister": 1.1}
COVER_SW = ("crimson", "night", "night", "black", "bone", "black", "night", "black", "black", "crimson")


# ------------------------------------------------------------------ materials

def kit(M):
    K = B43.kit(M)
    K.update({
        "ip": B30.atlas_mat("InteriorsPrintMat", "InteriorsPrint", rough=0.72, leather=0.03, wear=0.05, dirt=0.4),
        "atlas": B30.atlas_mat(),
        "cen": material("InCrimsonEnamel", base=(0.2, 0.014, 0.026), rough=0.3, wear=0.3, wear_metal=True, dirt=0.6),
        "lacquer": material("InLacquer", base=(0.024, 0.021, 0.027), rough=0.28, wear=0.22, wear_metal=True, dirt=0.55),
        "pine": material("CratePine", "NH_DeskWood", tint=(0.42, 0.3, 0.18), scale=0.3, rough_add=0.12, wear=0.35, dirt=0.8),
        "pinedk": material("CratePineDark", "NH_DeskWood", tint=(0.26, 0.18, 0.11), scale=0.3, rough_add=0.12, wear=0.35, dirt=0.8),
        "hessian": B24.cloth("Hessian", (0.095, 0.064, 0.034), rough=1.0, weave=0.035, dirt=0.85),
        "flour": flat("Flour", (0.78, 0.76, 0.7), 0.95, dirt=0.3),
        "beans": flat("CoffeeBeans", (0.07, 0.035, 0.02), 0.35, dirt=0.4),
        "kraft": B24.cloth("KraftPaper", (0.42, 0.28, 0.15), rough=0.8, weave=0.004, dirt=0.5),
        "twine": flat("Twine", (0.5, 0.4, 0.26), 0.9, dirt=0.5),
        "tallow": flat("Tallow", (0.74, 0.68, 0.54), 0.5, dirt=0.4),
        "black": flat("Umbrella", (0.02, 0.02, 0.025), 0.6, dirt=0.4),
        "felthat": B24.cloth("HatFelt", (0.025, 0.022, 0.026), rough=0.85, weave=0.004),
        "galv": material("Galvanised", base=(0.26, 0.27, 0.28), rough=0.5, metal=0.85, wear=0.3, dirt=0.9),
        "s_violet": flat("SweetViolet", (0.2, 0.05, 0.3), 0.25, dirt=0.2),
        "s_red": flat("SweetRed", (0.35, 0.02, 0.04), 0.25, dirt=0.2),
        "s_amber": flat("SweetAmber", (0.6, 0.35, 0.05), 0.25, dirt=0.2),
        "s_black": flat("SweetBlack", (0.02, 0.018, 0.02), 0.3, dirt=0.2),
        "s_white": flat("SweetWhite", (0.8, 0.78, 0.74), 0.4, dirt=0.2),
        "s_green": flat("SweetGreen", (0.1, 0.35, 0.12), 0.25, dirt=0.2),
        "s_teal": flat("SweetTeal", (0.1, 0.35, 0.38), 0.3, dirt=0.2),
        "s_toffee": flat("SweetToffee", (0.45, 0.2, 0.04), 0.3, dirt=0.2),
        "herb": flat("DriedHerb", (0.16, 0.16, 0.07), 0.9, dirt=0.6),
        "apple": flat("BlackApple", (0.09, 0.015, 0.03), 0.3, dirt=0.4),
        "turnip": flat("Turnip", (0.62, 0.55, 0.5), 0.6, dirt=0.6),
        "onion": flat("Onion", (0.42, 0.22, 0.08), 0.5, dirt=0.5),
        "glow": flat("FlameGlow", (1.0, 0.6, 0.25), 0.5),
    })
    return K


# ------------------------------------------------------------------ printed pieces

def iplate(name, key, w, h, t, mtx, K, edge="black"):
    """A flat plate (w x h, t thick, centred, facing -Y) showing an InteriorsPrint region."""
    return B43.pprism(name, "IN_" + key, rect(w, h), t, mtx, K["ip"], "IN_" + edge)


def ipoly(name, key, poly, t, mtx, K, edge="black"):
    return B43.pprism(name, "IN_" + key, poly, t, mtx, K["ip"], "IN_" + edge)


def wrap(name, key, r, zc, h, arc, mtx, K, n=10, sy=1.0, k=2.5):
    """A label wrapped round a jar or tin of radius r about the local Z axis, centred on its front (-Y), `arc` studs across."""
    u0, v0, u1, v1 = B30.REG["IN_" + key]
    a = min(arc / r, 2 * PI - 0.01)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    rows = []
    for j in range(2):
        z = zc - h / 2 + j * h
        rows.append([bm.verts.new((math.cos(-PI / 2 - a / 2 + a * i / n) * r, math.sin(-PI / 2 - a / 2 + a * i / n) * r * sy, z)) for i in range(n + 1)])
    for i in range(n):
        f = bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        f.smooth = True
        f[kl] = k
        for lp, (ii, jj) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            lp[uvl].uv = (u0 + ii / n * (u1 - u0), v0 + jj * (v1 - v0))
    return B30._bm_object(name, bm, K["ip"], mtx)


def cover_book(name, i, w, d, t, mtx, K):
    """A book lying on its back, its front cover (InteriorsPrint Cover_i) up, the spine at -X, the title's top toward +Y."""
    bm = B30._bevelled_box(w, d, t, min(0.012, t * 0.2))
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    u0, v0, u1, v1 = B30.REG[f"IN_Cover_{i % 10}"]
    sp, pa = B30._swatch("IN_" + COVER_SW[i % 10]), B30._swatch("IN_paper")
    for f in bm.faces:
        n = f.normal
        if n.z > 0.9:
            f[kl] = 2.0
            for lp in f.loops:
                x, y, _ = lp.vert.co
                lp[uvl].uv = (u0 + (x + w / 2) / w * (u1 - u0), v0 + (y + d / 2) / d * (v1 - v0))
        else:
            f[kl] = 0.4
            pt = sp if (n.z < -0.9 or n.x < -0.9) else pa
            for lp in f.loops:
                lp[uvl].uv = pt
    return B30._bm_object(name, bm, K["ip"], mtx)


def stand_book(name, i, x, yback, z, K, w=0.85, d=1.25, t=0.16, lean=12, yaw=0.0):
    """A book standing face-out, its back cover against yback, leaning back `lean` degrees."""
    return cover_book(name, i, w, d, t, T(x, yback, z) @ RZ(yaw) @ RX(-lean * DEG) @ T(0, 0, d / 2) @ RX(PI / 2) @ T(0, 0, -t), K)


# ------------------------------------------------------------------ shared pieces

def _quatrefoil(name, cx, y, cz, r, mat):
    """A gilt quatrefoil (four lobes of 0.45 r about centres 0.5 r out, their outer arcs) as one square bar in the XZ plane at y;
    lighter than nh_props._quatrefoil's five rings."""
    d, rl = 0.5 * r, 0.45 * r
    a = math.degrees(math.atan2(0.447, -0.053)) * DEG
    pts = []
    for k in range(4):
        base = k * PI / 2
        ox, oz = cx + math.cos(base) * d, cz + math.sin(base) * d
        for i in range(9):
            t = base - a + 2 * a * i / 8
            pts.append((ox + math.cos(t) * rl, y, oz + math.sin(t) * rl))
    tube(name, pts, max(0.01, r * 0.07), mat, closed=True, square=True, poly=True)
    sphere(name + "B", r * 0.14, (cx, y, cz), mat, seg=8, rings=4, scale=(1, 0.4, 1))


def lowring(name, center, r, axis, mat, thick, n=8):
    pts = []
    for i in range(n):
        t = i / n * 2 * PI
        c, s_ = math.cos(t) * r, math.sin(t) * r
        pts.append((center[0] + c, center[1] + s_, center[2]) if axis == "Z" else (center[0], center[1] + c, center[2] + s_) if axis == "X"
                   else (center[0] + c, center[1], center[2] + s_))
    return tube(name, pts, thick, mat, closed=True, square=True, poly=True)


def lancet(prefix, w, h, K, mat=None, rise=None):
    """A gilt pointed-arch moulding w x h (feet at z = 0, centred on x = 0) on a face looking to -Y at y = 0."""
    mat = mat or K["gilt"]
    rise = rise if rise is not None else min(w * 0.75, h * 0.4)
    zs = h - rise
    pts = [(-w / 2, 0.0)] + arch_xz(-w / 2, w / 2, zs, rise, n=12) + [(w / 2, 0.0)]
    tube(prefix, [(x, -0.02, z) for x, z in pts], 0.022, mat, square=True, poly=True)


def gothic_panel(prefix, w, h, K, mtx, foil=True, mat=None):
    """A crimson enamel panel w x h (bottom centre at the origin, its face on y = 0 looking -Y) with a gilt lancet and quatrefoil."""
    s = _mark()
    box(f"{prefix}P", (w, 0.05, h), (0, 0.025, h / 2), mat or K["cen"], bevel=0.012)
    lancet(f"{prefix}L", w - 0.24, h - 0.24, K)
    _xform(s + 1, T(0, 0, 0.12))
    if foil and h > 1.0:
        _quatrefoil(f"{prefix}Q", 0, -0.025, h - 0.12 - min((w - 0.24) * 0.75, (h - 0.24) * 0.4) * 0.45, min(0.16, w * 0.16), K["gilt"])
    _xform(s, mtx)


def turned_leg(name, h, r, mat, loc, cap=None):
    lathe(name, [(0, 0), (r * 0.9, 0), (r * 1.1, 0.06), (r * 0.6, 0.16), (r * 0.7, h * 0.3), (r * 1.15, h * 0.36), (r * 0.6, h * 0.42),
                 (r * 0.75, h * 0.9), (r * 1.1, h * 0.95), (r * 1.0, h), (0, h)], mat, seg=12, loc=loc)


def parcel(prefix, w, d, h, mtx, K, tied=True):
    """A brown paper parcel tied with twine."""
    s = _mark()
    box(f"{prefix}B", (w, d, h), (0, 0, h / 2), K["kraft"], bevel=min(0.03, h * 0.2))
    if tied:
        box(f"{prefix}T1", (w + 0.01, 0.025, h + 0.01), (0, 0, h / 2), K["twine"], bevel=0.0)
        box(f"{prefix}T2", (0.025, d + 0.01, h + 0.01), (0, 0, h / 2), K["twine"], bevel=0.0)
        hoop(f"{prefix}K", (0, 0, h + 0.02), 0.04, "Z", K["twine"], thick=0.012)
    _xform(s, mtx)


def candle(prefix, x, y, z, h, r, K, glow=False):
    cyl(f"{prefix}C", r, h, (x, y, z + h / 2), K["wax"], verts=12, bevel=0.01)
    if glow:
        set_group("Glow")
        lathe(f"{prefix}F", [(0, 0), (r * 0.45, r * 0.6), (r * 0.35, r * 1.6), (0, r * 2.8)], K["glow"], seg=10, loc=(x, y, z + h + 0.02))
        set_group("Main")
    else:
        cyl(f"{prefix}W", 0.008, 0.06, (x, y, z + h + 0.03), K["ink"], verts=5, bevel=0.0)


def tin(prefix, label, r, h, x, y, z, K, lid=None, yaw=0.0):
    s = _mark()
    cyl(f"{prefix}Body", r, h, (0, 0, h / 2), K["zinc"] if lid is None else lid, verts=16, bevel=0.008)
    cyl(f"{prefix}Lid", r * 1.03, 0.06, (0, 0, h - 0.02), K["brassf"], verts=16, bevel=0.0)
    wrap(f"{prefix}Lab", label, r + 0.006, h * 0.48, h * 0.62, 2 * PI * r * 0.62, Matrix.Identity(4), K, n=10)
    _xform(s, T(x, y, z) @ RZ(yaw))


def jar(prefix, x, y, z, r, h, liquid, K, glass="glass", label=None):
    """A stoppered glass jar or bottle with something inside."""
    lathe(f"{prefix}G", [(0, 0), (r, 0), (r, h * 0.78), (r * 0.55, h * 0.86), (r * 0.45, h * 0.92), (r * 0.45, h), (0, h)], K[glass], seg=14,
          loc=(x, y, z))
    if liquid:
        cyl(f"{prefix}In", r * 0.92, h * 0.6, (x, y, z + h * 0.32), K[liquid], verts=12, bevel=0.0)
    cyl(f"{prefix}Cork", r * 0.4, h * 0.12, (x, y, z + h + 0.03), K["cork"], verts=8, bevel=0.0)
    if label:
        wrap(f"{prefix}Lab", label, r + 0.006, h * 0.45, h * 0.35, r * 2.2, T(x, y, z), K, n=8)


def soap_stack(prefix, x, y, z, K, n=4):
    for k in range(n):
        box(f"{prefix}{k}", (0.42, 0.28, 0.12), (x + (k % 2) * 0.03, y, z + 0.06 + k * 0.125), K["tallow"] if k % 2 else K["linen"], bevel=0.03)


# ================================================================== the counter

def counter_body(prefix, x0, x1, K, H=H_C, goods=True, rnd=None, bays=None, top=True, back=True):
    """A shop counter section from x0 to x1: black marble top with a brass nosing (to y = -1.22), a cast-iron frame of crimson
    enamel gothic panels, an iron plinth with a brass kick plate; the shopkeeper's side (+Y) open, with two shelves."""
    L = x1 - x0
    cx = (x0 + x1) / 2
    ir, br, mb, lq = K["iron"], K["brassf"], K["marble"], K["lacquer"]
    if top:
        box(f"{prefix}Top", (L, D_C + 0.12, 0.18), (cx, -0.06, H - 0.09), mb, bevel=0.03)
        box(f"{prefix}Nose", (L, 0.05, 0.12), (cx, -1.21, H - 0.1), br, bevel=0.012)
    box(f"{prefix}Frieze", (L, 0.12, 0.34), (cx, -1.04, H - 0.35), lq, bevel=0.02)
    box(f"{prefix}Bead", (L, 0.03, 0.04), (cx, -1.11, H - 0.48), K["gilt"], bevel=0.008)
    box(f"{prefix}Plinth", (L, 0.2, 0.34), (cx, -0.98, 0.17), ir, bevel=0.02)
    box(f"{prefix}Kick", (L, 0.03, 0.22), (cx, -1.09, 0.15), br, bevel=0.008)
    box(f"{prefix}Floor", (L, D_C - 0.2, 0.08), (cx, 0.02, 0.38), lq, bevel=0.01)
    n = bays or max(1, round(L / 2.0))
    bw = L / n
    zb, zt = 0.34, H - 0.52
    for i in range(n + 1):
        x = x0 + i * bw
        xi = min(max(x, x0 + 0.08), x1 - 0.08)
        box(f"{prefix}Stile{i}", (0.16, 0.16, zt - zb), (xi, -1.02, (zb + zt) / 2), ir, bevel=0.02)
        cyl(f"{prefix}Boss{i}", 0.06, 0.04, (xi, -1.11, zt - 0.18), br, rot=(PI / 2, 0, 0), verts=10, bevel=0.006)
    for i in range(n):
        x = x0 + (i + 0.5) * bw
        gothic_panel(f"{prefix}Bay{i}", bw - 0.2, zt - zb - 0.12, K, T(x, -0.96, zb + 0.06))
    if back:
        # the shopkeeper's side: end posts, a mid shelf and the underside of the top
        box(f"{prefix}Shelf", (L - 0.04, D_C - 0.4, 0.06), (cx, 0.05, 1.7), lq, bevel=0.01)
        box(f"{prefix}BackRail", (L, 0.12, 0.2), (cx, 1.04, H - 0.28), lq, bevel=0.015)
        box(f"{prefix}Back", (L, 0.06, zt - zb), (cx, -0.86, (zb + zt) / 2), lq, bevel=0.0)
        for x in (x0 + 0.03, x1 - 0.03):
            box(f"{prefix}End{x:.1f}", (0.06, D_C - 0.24, H - 0.52), (x, 0.08, (H - 0.52) / 2 + 0.34 - 0.17), lq, bevel=0.008)
        for x in (x0 + 0.06, x1 - 0.06):
            box(f"{prefix}Post{x:.1f}", (0.12, 0.12, H - 0.62), (x, 1.04, (H - 0.18) / 2 + 0.15), ir, bevel=0.015)
    if goods and rnd is not None:
        x = x0 + 0.35
        k = 0
        while x < x1 - 0.5:
            roll = rnd.random()
            if roll < 0.35:
                for j in range(rnd.randint(3, 6)):
                    box(f"{prefix}Bag{k}_{j}", (0.5, 0.7, 0.025), (x + 0.25, 0.1 + rnd.uniform(-0.04, 0.04), 1.76 + j * 0.03), K["kraft"], bevel=0.004)
                x += 0.65
            elif roll < 0.55:
                cyl(f"{prefix}Spool{k}", 0.16, 0.22, (x + 0.16, 0.2, 1.84), K["twine"], verts=14, bevel=0.02)
                cyl(f"{prefix}SpoolC{k}", 0.05, 0.24, (x + 0.16, 0.2, 1.84), K["pinedk"], verts=8, bevel=0.0)
                x += 0.45
            elif roll < 0.8:
                parcel(f"{prefix}Pc{k}", rnd.uniform(0.5, 0.8), rnd.uniform(0.4, 0.7), rnd.uniform(0.2, 0.4),
                       T(x + 0.4, 0.15, 1.73) @ RZ(rnd.uniform(-0.2, 0.2)), K)
                x += 0.9
            else:
                box(f"{prefix}Ledger{k}", (0.6, 0.85, 0.14), (x + 0.3, 0.1, 1.8), K["leather"], bevel=0.02)
                box(f"{prefix}LedgerP{k}", (0.56, 0.8, 0.1), (x + 0.33, 0.1, 1.8), K["paper"], bevel=0.01)
                x += 0.75
            k += 1
        # the floor shelf: string-tied stacks of paper and a box of twine
        for j, xx in enumerate((x0 + 0.6, cx + 0.3)):
            parcel(f"{prefix}Low{j}", 0.9, 0.9, 0.5, T(xx, 0.2, 0.42) @ RZ(rnd.uniform(-0.1, 0.1)), K, tied=j == 0)


def shop_counter(M):
    """The general store's counter: 6 long, 2.2 deep, 3.4 tall. Black marble top with a brass nosing and a brass yard rule set
    into it along the front (the draper's measure), three crimson enamel gothic panels in a cast-iron frame, a brass kick plate;
    on the shopkeeper's side, a shelf of brown paper bags, twine spools, parcels and a ledger. Ends flush, so runs line up."""
    K = kit(M)
    rnd = random.Random(4501)
    L = 6.0
    counter_body("C", -L / 2, L / 2, K, rnd=rnd, bays=3)
    iplate("Rule", "Rule", 5.6, 0.2, 0.01, T(0, -1.0, H_C + 0.004) @ RX(-PI / 2), K, edge="brass")
    for x in (-2.8, 2.8):
        cyl(f"RulePin{x}", 0.025, 0.02, (x, -1.0, H_C + 0.01), K["brassf"], verts=8, bevel=0.0)
    return _dims()


def arc_slab(name, cx, cy, r0, r1, a0, a1, z0, z1, mat, n=16, bevel=0.012):
    """A curved slab between radii r0 and r1 (about the vertical axis at cx, cy) from angle a0 to a1; r0 = 0 makes a wedge."""
    bm = bmesh.new()
    ang = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    ob_ = [bm.verts.new((cx + math.cos(a) * r1, cy + math.sin(a) * r1, z0)) for a in ang]
    ot = [bm.verts.new((cx + math.cos(a) * r1, cy + math.sin(a) * r1, z1)) for a in ang]
    if r0 > 1e-4:
        ib = [bm.verts.new((cx + math.cos(a) * r0, cy + math.sin(a) * r0, z0)) for a in ang]
        it = [bm.verts.new((cx + math.cos(a) * r0, cy + math.sin(a) * r0, z1)) for a in ang]
        for i in range(n):
            bm.faces.new((ib[i + 1], ib[i], it[i], it[i + 1]))
            bm.faces.new((it[i], ot[i], ot[i + 1], it[i + 1]))
            bm.faces.new((ib[i + 1], ob_[i + 1], ob_[i], ib[i]))
        bm.faces.new((ib[0], it[0], ot[0], ob_[0]))
        bm.faces.new((ob_[n], ot[n], it[n], ib[n]))
    else:
        cb, ct = bm.verts.new((cx, cy, z0)), bm.verts.new((cx, cy, z1))
        for i in range(n):
            bm.faces.new((ct, ot[i], ot[i + 1]))
            bm.faces.new((cb, ob_[i + 1], ob_[i]))
        bm.faces.new((cb, ct, ot[0], ob_[0]))
        bm.faces.new((ob_[n], ot[n], ct, cb))
    for i in range(n):
        bm.faces.new((ob_[i], ob_[i + 1], ot[i + 1], ot[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = abs(f.normal.z) < 0.5 and abs(f.normal.dot(Vector((math.cos(a0), math.sin(a0), 0)))) < 0.99 and             abs(f.normal.dot(Vector((math.cos(a1), math.sin(a1), 0)))) < 0.99
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, bevel)


def shop_counter_corner(M):
    """The counter's outside corner: a quarter round 2.2 x 2.2 (its centre on the inside corner), so a ShopCounter run along X
    and one turned -90 (along Y, facing -X) meet on its flat ends. A bowed black marble top and brass nosing, three curved
    crimson enamel panels between iron colonnettes; on top the shop's brass student lamp: a crimson tole shade over a glass
    chimney (Glass) and its flame (Glow)."""
    K = kit(M)
    ir, br, mb, lq = K["iron"], K["brassf"], K["marble"], K["lacquer"]
    cx = cy = 1.1
    R = D_C
    a0, a1 = PI, 1.5 * PI
    arc_slab("Top", cx, cy, 0.0, R + 0.12, a0, a1, H_C - 0.18, H_C, mb, n=20)
    arc_slab("Nose", cx, cy, R + 0.1, R + 0.13, a0, a1, H_C - 0.16, H_C - 0.04, br, n=20)
    arc_slab("Frieze", cx, cy, R - 0.1, R + 0.02, a0, a1, H_C - 0.52, H_C - 0.18, lq, n=20)
    arc_slab("Bead", cx, cy, R + 0.02, R + 0.05, a0, a1, H_C - 0.5, H_C - 0.46, K["gilt"], n=20)
    arc_slab("Plinth", cx, cy, R - 0.3, R - 0.1, a0, a1, 0.0, 0.34, ir, n=20)
    arc_slab("Kick", cx, cy, R - 0.1, R - 0.07, a0, a1, 0.04, 0.26, br, n=20)
    arc_slab("Body", cx, cy, 0.0, R - 0.18, a0, a1, 0.34, H_C - 0.52, lq, n=20)
    zb, zt = 0.34, H_C - 0.52
    for i in range(4):
        a = a0 + (a1 - a0) * i / 3
        a = min(max(a, a0 + 0.04), a1 - 0.04)
        x, y = cx + math.cos(a) * (R - 0.08), cy + math.sin(a) * (R - 0.08)
        lathe(f"Colonnette{i}", [(0, 0), (0.1, 0), (0.1, 0.1), (0.07, 0.16), (0.065, zt - zb - 0.16), (0.1, zt - zb - 0.08), (0.1, zt - zb),
                                 (0, zt - zb)], ir, seg=12, loc=(x, y, zb), flute=(8, 0.15))
    for i in range(3):
        b0, b1 = a0 + (a1 - a0) * i / 3 + 0.05, a0 + (a1 - a0) * (i + 1) / 3 - 0.05
        arc_slab(f"Panel{i}", cx, cy, R - 0.2, R - 0.15, b0, b1, zb + 0.06, zt - 0.06, K["cen"], n=8)
        # the gilt lancet bent round the panel
        w = (b1 - b0) * (R - 0.14)
        h = zt - zb - 0.36
        rise = min(w * 0.75, h * 0.4)
        pts = [(-w / 2 + 0.12, 0.0)] + arch_xz(-w / 2 + 0.12, w / 2 - 0.12, h - rise, rise, n=12) + [(w / 2 - 0.12, 0.0)]
        am = (b0 + b1) / 2
        rr = R - 0.13
        tube(f"Lancet{i}", [(cx + math.cos(am - u / rr) * rr, cy + math.sin(am - u / rr) * rr, zb + 0.18 + z) for u, z in pts], 0.022,
             K["gilt"], square=True, poly=True)
        fx, fy = cx + math.cos(am) * rr, cy + math.sin(am) * rr
        s = _mark()
        _quatrefoil(f"Foil{i}", 0, 0, 0, 0.15, K["gilt"])
        _xform(s, T(fx, fy, zb + 0.18 + h - rise * 0.45) @ RZ(am + PI / 2))
    # the lamp, on the bow
    lx, ly = cx + math.cos(1.25 * PI) * 1.35, cy + math.sin(1.25 * PI) * 1.35
    z = H_C
    lathe("LampFoot", [(0, 0), (0.32, 0), (0.33, 0.04), (0.26, 0.08), (0.12, 0.14), (0.07, 0.2), (0.07, 1.25), (0, 1.25)], br, seg=24, loc=(lx, ly, z))
    lathe("LampFont", [(0, 1.2), (0.12, 1.2), (0.22, 1.32), (0.24, 1.45), (0.18, 1.56), (0.1, 1.6), (0, 1.6)], br, seg=24, loc=(lx, ly, z))
    for k in range(4):
        a = k * PI / 2 + PI / 4
        tube(f"Gallery{k}", [(lx + math.cos(a) * 0.08, ly + math.sin(a) * 0.08, z + 1.6), (lx + math.cos(a) * 0.2, ly + math.sin(a) * 0.2, z + 1.78)],
             0.012, br, poly=True)
    hoop("ShadeRing", (lx, ly, z + 1.82), 0.2, "Z", br, thick=0.015)
    lathe("Shade", [(0.2, 0), (0.5, -0.28), (0.53, -0.3), (0.5, -0.27), (0.18, 0.02)], K["cen"], seg=28, loc=(lx, ly, z + 2.08))
    cyl("Wick", 0.03, 0.08, (lx, ly, z + 1.64), br, verts=8, bevel=0.0)
    set_group("Glass")
    lathe("Chimney", [(0, 0), (0.09, 0), (0.12, 0.08), (0.13, 0.2), (0.08, 0.34), (0.07, 0.62), (0.0, 0.62)], K["glass"], seg=18, loc=(lx, ly, z + 1.6))
    set_group("Glow")
    lathe("Flame", [(0, 0), (0.035, 0.03), (0.04, 0.09), (0.02, 0.16), (0, 0.2)], K["glow"], seg=10, loc=(lx, ly, z + 1.68))
    set_group("Main")
    return _dims()


def shop_counter_end(M):
    """The end of the run, 3.0 long: a 1.2 counter stub (its +X end meets a ShopCounter) closed by a crimson end panel with the
    gilt M & V monogram, a square cast-iron newel with a brass ball, and the shopkeeper's way in: a cast-iron swing gate (Door0;
    hinged on the newel, opens out to the front) with a brass top rail, scrolled infill and a PROPRIETOR ONLY plate, latching
    on a slim iron post with a brass finial."""
    K = kit(M)
    rnd = random.Random(4503)
    ir, br, lq = K["iron"], K["brassf"], K["lacquer"]
    x0, x1 = 0.3, 1.5
    counter_body("C", x0, x1, K, rnd=rnd, bays=1, goods=False)
    box("EndPanel", (0.08, D_C - 0.1, H_C - 0.7), (x0 - 0.02, -0.02, 0.34 + (H_C - 0.7) / 2), lq, bevel=0.015)
    box("EndCap", (0.1, D_C + 0.12, 0.18), (x0 + 0.03, -0.06, H_C - 0.09), K["marble"], bevel=0.03)
    gothic_panel("EndCrimson", 1.6, 2.2, K, T(x0 - 0.07, -0.05, 0.5) @ RZ(-PI / 2), foil=False)
    iplate("Monogram", "Monogram", 0.62, 0.62, 0.02, T(x0 - 0.1, -0.05, 1.75) @ RZ(-PI / 2), K, edge="crimson")
    parcel("Pc", 0.7, 0.5, 0.3, T(1.0, 0.0, 1.73), K)
    # newel and latch post
    nx = 0.12
    box("Newel", (0.3, 0.3, 3.6), (nx, -0.9, 1.8), ir, bevel=0.03)
    box("NewelCap", (0.4, 0.4, 0.12), (nx, -0.9, 3.66), ir, bevel=0.03)
    sphere("NewelBall", 0.16, (nx, -0.9, 3.88), br, seg=16, rings=8)
    box("NewelBase", (0.42, 0.42, 0.2), (nx, -0.9, 0.1), ir, bevel=0.03)
    for k in range(3):
        box(f"NewelBand{k}", (0.32, 0.32, 0.05), (nx, -0.9, 1.0 + k * 1.0), br, bevel=0.01)
    px = -1.38
    lathe("LatchPost", [(0, 0), (0.14, 0), (0.14, 0.12), (0.08, 0.2), (0.07, 3.1), (0.1, 3.18), (0, 3.2)], ir, seg=12, loc=(px, -0.9, 0))
    finial("LatchFin", px, -0.9, 3.18, br, s=0.9)
    box("Latch", (0.14, 0.08, 0.1), (px + 0.1, -0.9, 2.2), br, bevel=0.01)
    # the gate
    hx, hy = nx - 0.17, -0.9
    set_group("Door0", hinge=(hx, hy, 0.0), swing=1)
    gx0, gx1 = px + 0.12, hx - 0.03
    gw = gx1 - gx0
    gcx = (gx0 + gx1) / 2
    for z in (0.35, 2.85):
        box(f"GateRail{z}", (gw, 0.08, 0.1), (gcx, hy, z), ir, bevel=0.015)
    box("GateTop", (gw + 0.06, 0.12, 0.08), (gcx, hy, 2.95), br, bevel=0.02)
    for x in (gx0 + 0.04, gx1 - 0.04):
        box(f"GateStile{x:.2f}", (0.08, 0.08, 2.7), (x, hy, 1.6), ir, bevel=0.015)
    n = 6
    for k in range(1, n):
        x = gx0 + k * gw / n
        tube(f"GateBar{k}", [(x, hy, 0.35), (x, hy, 2.0)], 0.022, ir, poly=True)
        sphere(f"GateKnop{k}", 0.04, (x, hy, 1.2), br, seg=8, rings=4)
    for k in range(n // 2):
        x = gx0 + (2 * k + 1) * gw / n
        dx = gw / n
        tube(f"GateScroll{k}", [(x - dx, hy, 2.0), (x - dx * 0.6, hy, 2.35), (x, hy, 2.5), (x + dx * 0.6, hy, 2.35), (x + dx, hy, 2.0)], 0.02, ir)
        hoop(f"GateCurl{k}", (x, hy, 2.25), 0.12, "Y", ir, thick=0.016)
    iplate("GatePlate", "GatePlate", 1.0, 0.2, 0.02, T(gcx, hy - 0.05, 1.55), K)
    for k in range(2):
        cyl(f"Hinge{k}", 0.05, 0.2, (hx, hy, 0.6 + k * 2.0), br, verts=10, bevel=0.01)
    set_group("Main")
    return _dims()


def cash_register(M):
    """The brass till on the counter: an embossed brass case 1.8 wide with scrolled side panels, three stepped rows of ivory key
    caps on brass stalks (1 to 500 yen and NO SALE), the crested sale window (Glass) with the YEN 4 50 flags up under an AMOUNT
    PURCHASED plate, a crank on the right and the till drawer below (Drawer0, slides out to the front) with a brass pull."""
    K = kit(M)
    br, gl, ir = K["brassf"], K["gilt"], K["iron"]
    W, Dd = 1.7, 1.4
    box("Base", (W + 0.1, Dd + 0.06, 0.08), (0, 0, 0.04), K["marble"], bevel=0.02)
    box("Till", (W, Dd, 0.36), (0, 0.04, 0.26), br, bevel=0.03)
    # side profile: a sloped keyboard front rising to the window tower
    prof = [(-0.7, 0.44), (0.7, 0.44), (0.7, 1.45), (0.25, 1.45), (0.25, 1.2), (-0.7, 0.62)]
    for sx in (-1, 1):
        prism(f"Side{sx}", prof, sx * (W / 2 - 0.04), 0.08, br, plane="YZ", bevel=0.015)
        s = _mark()
        for k, (yy, zz, rr) in enumerate(((-0.25, 0.75, 0.13), (0.25, 0.95, 0.16), (0.48, 1.25, 0.1))):
            hoop(f"Scroll{sx}{k}", (0, yy, zz), rr, "X", gl, thick=0.022)
            sphere(f"ScrollBoss{sx}{k}", 0.035, (0, yy, zz), gl, seg=8, rings=4)
        _xform(s, T(sx * (W / 2 + 0.005), 0, 0))
    prism("Deck", [(-0.7, 0.62), (0.25, 1.2), (0.25, 1.15), (-0.7, 0.57)], 0, W - 0.1, br, plane="YZ")
    box("Front", (W - 0.1, 0.06, 0.2), (0, -0.67, 0.52), br, bevel=0.01)
    box("Back", (W - 0.1, 0.4, 1.0), (0, 0.5, 0.95), br, bevel=0.02)
    # the keys: three rows stepping up the slope
    labels = [["1", "2", "5", "10", "20", "NS"], ["1", "2", "5", "10", "20", "50"], ["50", "100", "500", "100", "500", "NS"]]
    for r in range(3):
        y = -0.5 + r * 0.28
        zdeck = 0.62 + (y + 0.7) / 0.95 * 0.58
        for c in range(6):
            x = -0.62 + c * 0.248
            cyl(f"Stalk{r}{c}", 0.016, 0.22, (x, y, zdeck + 0.11), br, verts=6, bevel=0.0)
            cyl(f"Rim{r}{c}", 0.085, 0.03, (x, y, zdeck + 0.235), br, verts=16, bevel=0.006)
            B43.pprism(f"Key{r}{c}", f"IN_Key_{labels[r][c]}", circ(0.075, 16), 0.02, T(x, y, zdeck + 0.255) @ RX(-PI / 2), K["ip"], "IN_bone")
    # the window tower and crest
    box("Apron", (W - 0.1, 0.45, 0.2), (0, 0.475, 1.55), br, bevel=0.015)
    box("TowerBack", (W - 0.1, 0.14, 0.42), (0, 0.66, 1.84), br, bevel=0.02)
    for sx in (-1, 1):
        box(f"Cheek{sx}", (0.1, 0.5, 0.5), (sx * (W / 2 - 0.05), 0.48, 1.8), br, bevel=0.02)
    iplate("Plate", "TillPlate", 1.3, 0.16, 0.02, T(0, 0.24, 1.55), K, edge="brass")
    iplate("Flags", "TillFlags", 1.3, 0.3, 0.01, T(0, 0.585, 1.8), K)
    box("WinTop", (W - 0.1, 0.1, 0.07), (0, 0.28, 1.985), br, bevel=0.012)
    box("WinSill", (W - 0.1, 0.12, 0.05), (0, 0.29, 1.635), br, bevel=0.012)
    box("TowerLid", (W - 0.1, 0.5, 0.05), (0, 0.48, 2.03), br, bevel=0.012)
    crest = [(-0.85, 2.05), (0.85, 2.05), (0.7, 2.15), (0.45, 2.2)] + arch_xz(0.45, -0.45, 2.2, 0.28, n=10)[1:-1] + [(-0.45, 2.2), (-0.7, 2.15)]
    prism("Crest", crest, 0.62, 0.12, br, plane="XZ", bevel=0.01)
    iplate("Maker", "TillMaker", 0.66, 0.1, 0.01, T(0, 0.555, 2.24), K, edge="brass")
    finial("CrestFin", 0, 0.62, 2.47, gl, s=0.7)
    for sx in (-1, 1):
        sphere(f"CrestBall{sx}", 0.06, (sx * 0.8, 0.62, 2.14), gl, seg=10, rings=5)
    # crank on the right side
    cyl("CrankHub", 0.1, 0.1, (W / 2 + 0.05, 0.1, 0.9), br, rot=(0, PI / 2, 0), verts=14, bevel=0.01)
    tube("CrankArm", [(W / 2 + 0.1, 0.1, 0.9), (W / 2 + 0.12, -0.05, 0.75), (W / 2 + 0.14, -0.15, 0.55)], 0.025, br)
    cyl("CrankGrip", 0.035, 0.18, (W / 2 + 0.22, -0.15, 0.55), K["ebony"], rot=(0, PI / 2, 0), verts=10, bevel=0.01)
    set_group("Glass")
    box("Window", (W - 0.3, 0.02, 0.3), (0, 0.29, 1.8), K["glass"], bevel=0.0)
    set_group("Drawer0")
    box("DrawerFront", (W - 0.14, 0.05, 0.28), (0, -0.665, 0.26), br, bevel=0.012)
    box("DrawerTray", (W - 0.2, 1.1, 0.24), (0, -0.1, 0.26), K["lacquer"], bevel=0.01)
    for k in range(5):
        box(f"Cup{k}", (0.26, 0.4, 0.04), (-0.6 + k * 0.3, -0.25, 0.39), K["velvet"], bevel=0.01)
    lathe("Pull", [(0, 0), (0.07, 0), (0.08, 0.03), (0.04, 0.08), (0, 0.1)], gl, seg=12, loc=(0, 0, 0))
    _xform(len(P.PARTS) - 1, T(0, -0.69, 0.26) @ RX(PI / 2))
    cyl("Keyhole", 0.03, 0.01, (0.5, -0.693, 0.26), K["ink"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    set_group("Main")
    return _dims()



def bell_weight(name, s, mat, loc):
    """A brass bell weight `s` studs tall with a knob."""
    lathe(name, [(0, 0), (0.42 * s, 0), (0.44 * s, 0.06 * s), (0.36 * s, 0.4 * s), (0.22 * s, 0.62 * s), (0.18 * s, 0.7 * s), (0.2 * s, 0.76 * s),
                 (0.1 * s, 0.82 * s), (0.14 * s, 0.92 * s), (0.1 * s, 1.0 * s), (0, 1.0 * s)], mat, seg=16, loc=loc)


def shop_scales(M):
    """The grocer's scales on the counter: a crimson enamel cast-iron bed on turned feet, a brass scoop pan on the left and a flat
    platform with two bell weights on the right, a dial tower between (the TRUE MEASURE dial in a brass ring), and a stepped
    black marble stand of five graduated brass bell weights beside it; 2.6 wide."""
    K = kit(M)
    br, gl, ir = K["brassf"], K["gilt"], K["iron"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Foot{sx}{sy}", [(0, 0), (0.07, 0), (0.08, 0.04), (0.05, 0.1), (0.06, 0.12), (0, 0.12)], ir, seg=10, loc=(sx * 0.75 - 0.25, sy * 0.3, 0))
    box("Bed", (1.8, 0.8, 0.3), (-0.25, 0, 0.27), K["cen"], bevel=0.04)
    box("BedTop", (1.85, 0.85, 0.05), (-0.25, 0, 0.44), br, bevel=0.015)
    box("BedLine", (1.6, 0.02, 0.03), (-0.25, -0.41, 0.3), gl, bevel=0.0)
    for k, x in enumerate((-0.85, 0.35)):
        _quatrefoil(f"BedFoil{k}", x, -0.41, 0.27, 0.08, gl)
    # the scoop pan (left) and the platform (right) on brass pillars
    cyl("PillarL", 0.06, 0.3, (-0.8, 0, 0.6), br, verts=12, bevel=0.01)
    cyl("PillarR", 0.06, 0.3, (0.3, 0, 0.6), br, verts=12, bevel=0.01)
    lathe("Scoop", [(0, 0), (0.18, 0), (0.33, 0.06), (0.42, 0.16), (0.45, 0.24), (0.43, 0.25), (0.4, 0.17), (0.3, 0.09), (0.16, 0.04), (0, 0.04)],
          br, seg=28, loc=(-0.8, 0, 0.75), scale=(1.15, 0.75))
    box("ScoopLip", (0.2, 0.3, 0.03), (-1.33, 0, 0.99), br, bevel=0.01, rot=(0, 0.3, 0))
    cyl("Platform", 0.34, 0.05, (0.3, 0, 0.78), br, verts=28, bevel=0.012)
    bell_weight("PW1", 0.32, br, (0.18, 0.02, 0.8))
    bell_weight("PW2", 0.22, br, (0.44, -0.08, 0.8))
    # dial tower
    lathe("Tower", [(0, 0), (0.14, 0), (0.1, 0.1), (0.07, 0.8), (0.1, 0.86), (0, 0.86)], ir, seg=12, loc=(-0.25, 0.1, 0.46))
    cyl("DialCase", 0.42, 0.16, (-0.25, 0.1, 1.62), br, rot=(PI / 2, 0, 0), verts=32, bevel=0.03)
    hoop("DialBezel", (-0.25, 0.01, 1.62), 0.39, "Y", gl, thick=0.03)
    B43.pprism("Dial", "IN_ScaleDial", circ(0.37, 32), 0.01, T(-0.25, 0.015, 1.62), K["ip"], "IN_enamel")
    box("Needle", (0.018, 0.01, 0.3), (-0.25 + 0.06, 0.0, 1.62 + 0.13), K["cen"], bevel=0.0, rot=(0, 0.45, 0))
    cyl("NeedleHub", 0.03, 0.03, (-0.25, -0.005, 1.62), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    finial("DialFin", -0.25, 0.1, 2.04, gl, s=0.6)
    # the weights stand
    for k, (w, h) in enumerate(((1.1, 0.12), (0.9, 0.12))):
        box(f"Step{k}", (w, 0.5, h), (1.35 - k * 0.1, 0, 0.06 + k * 0.12), K["marble"], bevel=0.02)
    for k, s in enumerate((0.42, 0.34, 0.27, 0.21, 0.16)):
        bell_weight(f"W{k}", s, br, (0.98 + k * 0.2, 0, 0.24))
    return _dims()


def counter_bell(M):
    """The shop bell: a brass dome bell on a black marble octagon with a crimson enamel skirt and gilt bead, a plunger on top,
    and a little brass easel holding the RING FOR SERVICE card; a plinth piece, 1.1 wide."""
    K = kit(M)
    br, gl = K["brassf"], K["gilt"]
    cyl("Base", 0.3, 0.08, (0, 0, 0.04), K["marble"], verts=8, bevel=0.015)
    lathe("Skirt", [(0, 0.08), (0.25, 0.08), (0.26, 0.12), (0.22, 0.16), (0, 0.16)], K["cen"], seg=24)
    hoop("Bead", (0, 0, 0.16), 0.22, "Z", gl, thick=0.012)
    lathe("Dome", [(0, 0.16), (0.24, 0.16), (0.24, 0.18), (0.2, 0.28), (0.12, 0.34), (0.04, 0.36), (0, 0.36)], br, seg=32)
    cyl("Stem", 0.018, 0.08, (0, 0, 0.4), br, verts=8, bevel=0.0)
    lathe("Plunger", [(0, 0), (0.04, 0), (0.05, 0.02), (0.03, 0.045), (0, 0.05)], gl, seg=12, loc=(0, 0, 0.43))
    x = 0.62
    tube("EaselL", [(x - 0.2, 0.0, 0.0), (x - 0.17, 0.1, 0.24)], 0.008, br, poly=True)
    tube("EaselR", [(x + 0.2, 0.0, 0.0), (x + 0.17, 0.1, 0.24)], 0.008, br, poly=True)
    tube("EaselBack", [(x, 0.18, 0.0), (x, 0.09, 0.22)], 0.008, br, poly=True)
    box("EaselLedge", (0.46, 0.04, 0.015), (x, -0.02, 0.03), br, bevel=0.0)
    iplate("Card", "BellCard", 0.44, 0.185, 0.008, T(x, 0.03, 0.135) @ RX(-0.35), K, edge="enamel")
    return _dims()


def roll_mapped(name, key, r, L, mtx, K, seg=24, edge="paper"):
    """A paper roll along X (centred), its round face mapped once round with an InteriorsPrint region, the ends paper."""
    u0, v0, u1, v1 = B30.REG["IN_" + key]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    rg = [[bm.verts.new((sx * L / 2, math.cos(i / seg * 2 * PI) * r, math.sin(i / seg * 2 * PI) * r)) for i in range(seg)] for sx in (-1, 1)]
    for i in range(seg):
        j = (i + 1) % seg
        f = bm.faces.new((rg[0][i], rg[0][j], rg[1][j], rg[1][i]))
        f.smooth = True
        f[kl] = 1.5
        for lp, (ii, jj) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            lp[uvl].uv = (u0 + jj * (u1 - u0), v0 + ii / seg * (v1 - v0))
    pt = B30._swatch("IN_" + edge)
    for side in (0, 1):
        f = bm.faces.new(rg[side] if side else list(reversed(rg[side])))
        f[kl] = 0.5
        for lp in f.loops:
            lp[uvl].uv = pt
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return B30._bm_object(name, bm, K["ip"], mtx)


def sheet(name, key, pts, width, K):
    """A sheet of paper hanging along a path of (y, z) points (centred on x = 0, `width` across), mapped with a region."""
    u0, v0, u1, v1 = B30.REG["IN_" + key]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    total = sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
    rows, acc = [], 0.0
    for i, p in enumerate(pts):
        if i:
            acc += (Vector(p) - Vector(pts[i - 1])).length
        rows.append(([bm.verts.new((-width / 2, p[0], p[1])), bm.verts.new((width / 2, p[0], p[1]))], acc / total))
    for (a, ta), (b, tb) in zip(rows, rows[1:]):
        f = bm.faces.new((a[0], a[1], b[1], b[0]))
        f.smooth = True
        f[kl] = 1.5
        for lp, (u, t) in zip(f.loops, ((0, ta), (1, ta), (1, tb), (0, tb))):
            lp[uvl].uv = (u0 + u * (u1 - u0), v1 - t * (v1 - v0) * 0.5)
    ob = B30._bm_object(name, bm, K["ip"], Matrix.Identity(4))
    return _solid(ob, 0.006)


def wrap_stand(M):
    """The wrapping stand: two cast-iron gothic A-frame ends on bun feet carrying a roll of brown kraft paper and, above it, a roll
    of the shop's crimson paper printed with gilt crescents and quatrefoils, each sheet drawn down over a serrated brass cutter;
    on top a cone of twine on a spike, its string run up through a brass eyelet on a gooseneck and hanging down, and a pair of
    shears on a hook; 2.9 wide, 4.6 tall."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    for sx in (-1, 1):
        x = sx * 1.3
        for sy in (-1, 1):
            tube(f"Leg{sx}{sy}", [(x, sy * 0.75, 0.15), (x, sy * 0.18, 3.45)], 0.05, ir, square=True, poly=True)
            sphere(f"Bun{sx}{sy}", 0.12, (x, sy * 0.78, 0.1), ir, seg=10, rings=6, scale=(1, 1, 0.8))
        tube(f"Arch{sx}", [(x, y, z) for y, z in arch_xz(-0.5, 0.5, 2.6, 0.75, n=10)], 0.035, ir, square=True, poly=True)
        tube(f"Stretch{sx}", [(x, -0.62, 0.7), (x, 0.62, 0.7)], 0.035, ir, square=True, poly=True)
        tube(f"Mid{sx}", [(x, -0.38, 1.9), (x, 0.38, 1.9)], 0.03, ir, square=True, poly=True)
        s = _mark()
        _quatrefoil(f"Foil{sx}", 0, 0, 0, 0.2, gl)
        _xform(s, T(x + sx * 0.04, 0, 1.3) @ RZ(PI / 2))
        box(f"Cap{sx}", (0.16, 0.5, 0.1), (x, 0, 3.48), ir, bevel=0.02)
        finial(f"Fin{sx}", x, 0, 3.53, br, s=0.8)
        for z, y in ((1.05, -0.2), (2.15, -0.05)):
            cyl(f"Bear{sx}{z}", 0.09, 0.1, (x - sx * 0.02, y, z), br, rot=(0, PI / 2, 0), verts=12, bevel=0.01)
    box("FootBar", (2.6, 0.08, 0.08), (0, 0, 0.7), ir, bevel=0.015)
    tube("RodLow", [(-1.36, -0.2, 1.05), (1.36, -0.2, 1.05)], 0.03, ir, poly=True)
    tube("RodHigh", [(-1.36, -0.05, 2.15), (1.36, -0.05, 2.15)], 0.03, ir, poly=True)
    cyl("KraftRoll", 0.32, 2.3, (0, -0.2, 1.05), K["kraft"], rot=(0, PI / 2, 0), verts=28, bevel=0.02)
    roll_mapped("CrimsonRoll", "WrapPaper", 0.27, 2.3, T(0, -0.05, 2.15), K)
    strip("KraftSheet", [(0, -0.52, 1.05), (0, -0.58, 0.8), (0, -0.62, 0.58), (0, -0.6, 0.46)], 2.2, (1, 0, 0), K["kraft"], thick=0.008, it=2)
    sheet("CrimsonSheet", "WrapPaper", [(-0.32, 2.15), (-0.37, 1.95), (-0.42, 1.72), (-0.41, 1.6)], 2.2, K)
    for k, (y, z) in enumerate(((-0.64, 0.56), (-0.44, 1.7))):
        box(f"Cutter{k}", (2.5, 0.06, 0.08), (0, y, z), br, bevel=0.01)
        for j in range(24):
            prism(f"Tooth{k}{j}", [(-1.15 + j * 0.1, z - 0.04), (-1.1 + j * 0.1, z - 0.1), (-1.05 + j * 0.1, z - 0.04)], y - 0.02, 0.015, br, plane="XZ")
    box("Shelf", (2.6, 0.5, 0.06), (0, 0, 3.0), ir, bevel=0.012)
    cyl("Spike", 0.02, 0.5, (0.6, 0, 3.28), br, verts=6, bevel=0.0)
    lathe("Cone", [(0, 0), (0.24, 0), (0.2, 0.3), (0.12, 0.5), (0.07, 0.52), (0, 0.52)], K["twine"], seg=18, loc=(0.6, 0, 3.03))
    for k in range(5):
        hoop(f"Wind{k}", (0.6, 0, 3.08 + k * 0.08), 0.23 - k * 0.025, "Z", K["twine"], thick=0.012)
    tube("Gooseneck", [(1.3, 0, 3.5), (1.3, 0, 4.2), (1.1, -0.1, 4.5), (0.8, -0.2, 4.55), (0.6, -0.25, 4.45)], 0.025, ir)
    hoop("Eyelet", (0.6, -0.25, 4.38), 0.04, "X", br, thick=0.012)
    tube("String", [(0.6, 0, 3.55), (0.6, -0.15, 4.0), (0.6, -0.24, 4.37), (0.62, -0.28, 4.2), (0.66, -0.36, 3.5), (0.65, -0.4, 3.1)], 0.008, K["twine"])
    tube("Hook", [(1.3, -0.08, 2.9), (1.32, -0.25, 2.85), (1.32, -0.28, 2.95)], 0.015, br)
    for k, a in enumerate((-0.18, 0.18)):
        s = _mark()
        prism(f"Blade{k}", [(0, 0), (0.05, 0), (0.025, -0.55)], 0, 0.012, K["steel"], plane="XZ")
        hoop(f"Bow{k}", (0.03 * (1 if k else -1), 0, 0.1), 0.06, "Y", K["ebony"], thick=0.014)
        _xform(s, T(1.31, -0.3, 2.78) @ RY(a) @ RZ(PI / 2))
    return _dims()


# ================================================================== display

def display_case(M):
    """The jeweller's case: 4 wide, 3.4 tall. Turned iron legs and a stretcher shelf, a lacquered cabinet with two crimson gothic
    panels, and a glass vitrine with a sloped front (Glass: front, top, sides and back) over crimson velvet: pocket watches, a
    roll of rings, cameo brooches, fountain pens, a silver flask, spectacles, an iron key and price tickets."""
    K = kit(M)
    ir, br, gl, lq, vv = K["iron"], K["brassf"], K["gilt"], K["lacquer"], K["velvet"]
    W, Dd = 4.0, 2.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(f"Leg{sx}{sy}", 1.0, 0.1, ir, (sx * (W / 2 - 0.15), sy * (Dd / 2 - 0.15), 0))
    box("Stretch", (W - 0.4, Dd - 0.4, 0.06), (0, 0, 0.3), lq, bevel=0.015)
    box("Cab", (W, Dd, 1.4), (0, 0, 1.7), lq, bevel=0.03)
    for k, x in enumerate((-0.95, 0.95)):
        gothic_panel(f"Pan{k}", 1.7, 1.1, K, T(x, -Dd / 2 - 0.005, 1.15))
    box("Bead", (W + 0.04, Dd + 0.04, 0.06), (0, 0, 2.4), gl, bevel=0.015)
    zf, zt, yb, ys = 2.7, 3.4, Dd / 2 - 0.05, -0.35
    yf = -Dd / 2 + 0.05
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.05)
        tube(f"SideFrame{sx}", [(x, yf, 2.43), (x, yf, zf), (x, ys, zt), (x, yb, zt), (x, yb, 2.43)], 0.04, ir, square=True, poly=True)
    for name, y, z in (("RailF", yf, zf), ("RailS", ys, zt), ("RailB", yb, zt), ("RailLo", yf, 2.46)):
        tube(name, [(-W / 2 + 0.05, y, z), (W / 2 - 0.05, y, z)], 0.04, ir if name != "RailS" else br, square=True, poly=True)
    for x in (-0.67, 0.67):
        tube(f"Mull{x}", [(x, yf, zf), (x, ys, zt), (x, yb, zt)], 0.025, br, square=True, poly=True)
    for sx in (-1, 1):
        finial(f"Fin{sx}", sx * (W / 2 - 0.05), yb, zt + 0.02, gl, s=0.5)
    box("Velvet", (W - 0.14, Dd - 0.14, 0.05), (0, 0, 2.455), vv, bevel=0.01)
    box("Riser", (W - 0.3, 0.5, 0.2), (0, 0.55, 2.58), vv, bevel=0.04)
    z0 = 2.48
    for k, x in enumerate((-1.5, -1.05)):
        cyl(f"Watch{k}", 0.16, 0.06, (x, -0.35, z0 + 0.03), br, verts=24, bevel=0.015)
        cyl(f"Face{k}", 0.13, 0.065, (x, -0.35, z0 + 0.035), K["china"], verts=24, bevel=0.0)
        hoop(f"WatchBow{k}", (x, -0.53, z0 + 0.04), 0.05, "Z", br, thick=0.012)
        box(f"Hand{k}", (0.01, 0.09, 0.005), (x, -0.39, z0 + 0.07), K["ink"], bevel=0.0)
        tube(f"WatchChain{k}", [(x, -0.58, z0 + 0.03), (x + 0.15, -0.7, z0 + 0.01), (x + 0.32, -0.62, z0 + 0.01), (x + 0.4, -0.45, z0 + 0.01)], 0.008, gl)
    cyl("RingRoll", 0.11, 1.0, (-0.1, 0.3, 2.79), vv, rot=(0, PI / 2, 0), verts=14, bevel=0.03)
    for k in range(6):
        x = -0.5 + k * 0.16
        hoop(f"Ring{k}", (x, 0.3, 2.79), 0.115, "X", gl if k % 2 else K["silver"], thick=0.012)
        sphere(f"Gem{k}", 0.03, (x, 0.3, 2.91), (K["liq_c"], K["liq_v"], K["liq_g"])[k % 3], seg=8, rings=4)
    for k, x in enumerate((0.3, 0.65)):
        sphere(f"Cameo{k}", 0.13, (x, -0.35, z0 + 0.02), K["bone"], seg=16, rings=6, scale=(0.8, 1.0, 0.25))
        hoop(f"CameoRim{k}", (x, -0.35, z0 + 0.02), 0.11, "Z", gl, thick=0.014)
        sphere(f"CameoHead{k}", 0.05, (x, -0.35, z0 + 0.05), K["ivory"], seg=10, rings=5, scale=(0.8, 1.0, 0.35))
    for k in range(3):
        x = 1.05 + k * 0.14
        cyl(f"Pen{k}", 0.025, 0.5, (x, -0.3, z0 + 0.03), (K["ink"], K["cen"], K["ink"])[k], rot=(PI / 2, 0, 0.1 * k), verts=10, bevel=0.005)
        cyl(f"PenBand{k}", 0.027, 0.04, (x, -0.42, z0 + 0.03), gl, rot=(PI / 2, 0, 0.1 * k), verts=10, bevel=0.0)
    box("Flask", (0.32, 0.12, 0.5), (1.55, 0.5, 2.93), K["silver"], bevel=0.05, rot=(0, 0, 0.1))
    cyl("FlaskCap", 0.04, 0.06, (1.58, 0.5, 3.21), K["silver"], verts=10, bevel=0.01)
    for sx in (-1, 1):
        hoop(f"Lens{sx}", (0.55 + sx * 0.1, 0.5, 2.81), 0.08, "Y", gl, thick=0.01)
    tube("Bridge", [(0.47, 0.5, 2.83), (0.55, 0.5, 2.86), (0.63, 0.5, 2.83)], 0.008, gl)
    tube("Key", [(-1.6, 0.4, 2.81), (-1.1, 0.4, 2.81)], 0.02, ir, poly=True)
    hoop("KeyBow", (-1.66, 0.4, 2.81), 0.07, "Z", ir, thick=0.018)
    box("KeyBit", (0.06, 0.08, 0.02), (-1.12, 0.45, 2.81), ir, bevel=0.0)
    for k, x in enumerate((-1.3, 0.0, 0.5, 1.25)):
        iplate(f"Tag{k}", f"Ticket_{k}", 0.2, 0.12, 0.01, T(x, -0.62, z0 + 0.06) @ RX(-0.6), K, edge="bone")
    set_group("Glass")
    a = math.atan2(zt - zf, ys - yf)
    L = math.hypot(zt - zf, ys - yf)
    box("PaneFront", (W - 0.1, 0.02, L), (0, (yf + ys) / 2, (zf + zt) / 2), K["glass"], bevel=0.0, rot=(a - PI / 2, 0, 0))
    box("PaneLow", (W - 0.1, 0.02, zf - 2.45), (0, yf, (zf + 2.45) / 2), K["glass"], bevel=0.0)
    box("PaneTop", (W - 0.1, yb - ys, 0.02), (0, (yb + ys) / 2, zt), K["glass"], bevel=0.0)
    box("PaneBack", (W - 0.1, 0.02, zt - 2.45), (0, yb, (zt + 2.45) / 2), K["glass"], bevel=0.0)
    for sx in (-1, 1):
        prism(f"PaneSide{sx}", [(yf, 2.45), (yf, zf), (ys, zt), (yb, zt), (yb, 2.45)], sx * (W / 2 - 0.05), 0.02, K["glass"], plane="YZ")
    set_group("Main")
    return _dims()


def glass_cabinet_tall(M):
    """A tall glazed shop cabinet, 3.2 wide and 8.6 tall: a lacquered plinth with a crimson gothic panel, cast-iron corner posts,
    crimson enamel gothic side panels, four frosted glass shelves with brass edges (scent bottles, bone china cups and saucers, a
    pair of silver candlesticks and a gift box, ink bottles; boxed candles on the floor), a frieze with a gilt bead and a pointed
    iron gable with a gilt quatrefoil and finials. The glazed door (Door0 + Glass, hinged on the left, opens out) has a gothic
    arched head, a brass handle and escutcheon."""
    K = kit(M)
    rnd = random.Random(4509)
    ir, br, gl, lq = K["iron"], K["brassf"], K["gilt"], K["lacquer"]
    W, Dd = 3.2, 1.5
    z0, z1 = 0.7, 7.2
    box("Plinth", (W + 0.1, Dd + 0.1, z0), (0, 0, z0 / 2), lq, bevel=0.03)
    box("Kick", (W + 0.12, 0.03, 0.16), (0, -Dd / 2 - 0.06, 0.1), br, bevel=0.008)
    gothic_panel("PlinthPan", 2.6, 0.4, K, T(0, -Dd / 2 - 0.055, 0.2), foil=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Post{sx}{sy}", (0.16, 0.16, z1 - z0), (sx * (W / 2 - 0.08), sy * (Dd / 2 - 0.08), (z0 + z1) / 2), ir, bevel=0.02)
        gothic_panel(f"Side{sx}", Dd - 0.3, z1 - z0 - 0.3, K, T(sx * (W / 2 + 0.005), 0, z0 + 0.15) @ RZ(sx * PI / 2), foil=True)
    box("BackP", (W - 0.2, 0.06, z1 - z0), (0, Dd / 2 - 0.05, (z0 + z1) / 2), lq, bevel=0.0)
    box("Frieze", (W + 0.1, Dd + 0.1, 0.4), (0, 0, z1 + 0.2), lq, bevel=0.03)
    box("FriezeBead", (W + 0.14, 0.03, 0.05), (0, -Dd / 2 - 0.06, z1 + 0.08), gl, bevel=0.01)
    gable = [(-W / 2 - 0.05, z1 + 0.4), (W / 2 + 0.05, z1 + 0.4)] + arch_xz(W / 2 + 0.05, -W / 2 - 0.05, z1 + 0.4, 1.0, n=12)[1:-1]
    prism("Gable", gable, -Dd / 2 + 0.05, 0.12, ir, plane="XZ", bevel=0.015)
    tube("GableEdge", [(x, -Dd / 2 - 0.02, z) for x, z in arch_xz(-W / 2, W / 2, z1 + 0.45, 0.9, n=12)], 0.03, gl, square=True, poly=True)
    _quatrefoil("GableFoil", 0, -Dd / 2 - 0.03, z1 + 0.85, 0.22, gl)
    for x in (-W / 2 - 0.05, 0.0, W / 2 + 0.05):
        finial(f"Fin{x:.1f}", x, -Dd / 2 + 0.05, z1 + (1.38 if x == 0 else 0.4), gl, s=1.0 if x == 0 else 0.7)
    for k, z in enumerate((1.95, 3.25, 4.55, 5.85)):
        box(f"Shelf{k}", (W - 0.3, Dd - 0.3, 0.04), (0, 0.0, z), K["frost"], bevel=0.0)
        box(f"ShelfEdge{k}", (W - 0.3, 0.03, 0.06), (0, -Dd / 2 + 0.16, z), br, bevel=0.005)
    box("Floor", (W - 0.2, Dd - 0.2, 0.05), (0, 0, z0 + 0.025), K["velvet"], bevel=0.01)
    for k in range(3):
        x = -1.0 + k * 1.0
        box(f"CBox{k}", (0.8, 0.5, 0.3), (x, 0.1, z0 + 0.2), K["kraft"], bevel=0.02)
        for j in range(5):
            cyl(f"CBoxC{k}{j}", 0.04, 0.6, (x - 0.24 + j * 0.12, 0.1, z0 + 0.5), K["tallow"], verts=8, bevel=0.0)
    cols = ("liq_v", "liq_c", "amber", "liq_g", "liq_b")
    for k in range(7):
        x = -1.2 + k * 0.4
        h, y = rnd.uniform(0.35, 0.55), rnd.uniform(-0.15, 0.2)
        lathe(f"Scent{k}", [(0, 0), (0.12, 0), (0.14, h * 0.3), (0.1, h * 0.7), (0.04, h * 0.8), (0.04, h), (0, h)], K[cols[k % 5]], seg=12,
              loc=(x, y, 1.97))
        sphere(f"Stop{k}", 0.06, (x, y, 1.97 + h + 0.04), gl, seg=8, rings=4)
    for k in range(4):
        x = -1.1 + k * 0.72
        cyl(f"Saucer{k}", 0.2, 0.03, (x, 0, 3.285), K["china"], verts=20, bevel=0.01)
        lathe(f"Cup{k}", [(0, 0), (0.07, 0), (0.13, 0.08), (0.15, 0.2), (0.14, 0.2), (0.12, 0.09), (0.0, 0.03)], K["china"], seg=18, loc=(x, 0, 3.3))
        hoop(f"CupH{k}", (x + 0.16, 0, 3.42), 0.05, "Y", K["china"], thick=0.015)
        hoop(f"CupG{k}", (x, 0, 3.49), 0.145, "Z", gl, thick=0.006)
    for k, x in enumerate((-0.9, 0.9)):
        lathe(f"Stick{k}", [(0, 0), (0.18, 0), (0.18, 0.04), (0.08, 0.1), (0.05, 0.5), (0.09, 0.6), (0.06, 0.66), (0, 0.66)], K["silver"], seg=16,
              loc=(x, 0, 4.59))
        candle(f"SC{k}", x, 0, 5.25, 0.4, 0.05, K)
    box("GiftBox", (0.6, 0.45, 0.35), (0, 0.05, 4.75), K["cen"], bevel=0.02)
    box("Ribbon", (0.62, 0.06, 0.37), (0, 0.05, 4.75), gl, bevel=0.0)
    for k in range(6):
        jar(f"Ink{k}", -1.1 + k * 0.44, rnd.uniform(-0.1, 0.2), 5.89, 0.11, 0.32, None, K, glass="inkglass")
    hx, yd = -W / 2 + 0.16, -Dd / 2 + 0.02
    set_group("Door0", hinge=(hx, yd, 0.0), swing=-1)
    dw = W - 0.32
    zs, rise = z1 - 0.9, 0.7
    for x in (hx + 0.06, hx + dw - 0.06):
        box(f"DStile{x:.2f}", (0.12, 0.08, z1 - z0 - 0.1), (x, yd, (z0 + z1) / 2), ir, bevel=0.015)
    box("DRailLo", (dw, 0.08, 0.14), (hx + dw / 2, yd, z0 + 0.12), ir, bevel=0.015)
    box("DRailHi", (dw, 0.08, 0.14), (hx + dw / 2, yd, z1 - 0.12), ir, bevel=0.015)
    tube("DArch", [(hx + 0.12, yd - 0.01, zs - 0.4)] + [(x, yd - 0.01, z) for x, z in arch_xz(hx + 0.12, hx + dw - 0.12, zs, rise, n=12)] +
         [(hx + dw - 0.12, yd - 0.01, zs - 0.4)], 0.03, ir, square=True, poly=True)
    tube("DBead", [(x, yd - 0.04, z) for x, z in arch_xz(hx + 0.16, hx + dw - 0.16, zs, rise - 0.05, n=12)], 0.015, gl, poly=True)
    tube("DMull", [(hx + dw / 2, yd, z0 + 0.2), (hx + dw / 2, yd, zs + rise - 0.05)], 0.02, ir, square=True, poly=True)
    box("Handle", (0.04, 0.08, 0.6), (hx + dw - 0.14, yd - 0.08, 3.9), br, bevel=0.015)
    for z in (3.62, 4.18):
        box(f"HPost{z}", (0.04, 0.06, 0.04), (hx + dw - 0.14, yd - 0.05, z), br, bevel=0.0)
    box("Escutch", (0.1, 0.02, 0.18), (hx + dw - 0.14, yd - 0.05, 3.4), gl, bevel=0.01)
    set_group("Glass", hinge=(hx, yd, 0.0), swing=-1)
    box("Pane", (dw - 0.1, 0.02, z1 - z0 - 0.3), (hx + dw / 2, yd + 0.01, (z0 + z1) / 2), K["glass"], bevel=0.0)
    set_group("Main")
    return _dims()



def shelf_goods(prefix, x0, x1, z, yf, depth, K, rnd, kinds):
    """Stock a shelf from x0 to x1 (its top at z, its front edge at yf, `depth` deep) with a run of goods."""
    x = x0 + 0.1
    k = 0
    while x < x1 - 0.3:
        kind = kinds[k % len(kinds)] if rnd.random() < 0.75 else rnd.choice(kinds)
        p = f"{prefix}{k}"
        if kind == "tin":
            r = rnd.uniform(0.17, 0.22)
            tin(p, f"Tin_{rnd.randrange(7)}", r, rnd.uniform(0.45, 0.6), x + r, yf + depth * 0.4, z, K, lid=K["zinc"])
            x += 2 * r + 0.06
        elif kind == "jar":
            r = rnd.uniform(0.15, 0.2)
            jar(p, x + r, yf + depth * 0.4, z, r, rnd.uniform(0.5, 0.65), rnd.choice(("liq_a", "liq_c", "liq_g", "tea")), K, label=f"CafeJar_{rnd.randrange(6)}")
            x += 2 * r + 0.08
        elif kind == "bottle":
            r = 0.1
            lathe(f"{p}B", [(0, 0), (r, 0), (r, 0.42), (0.04, 0.52), (0.035, 0.66), (0, 0.66)], K[rnd.choice(("inkglass", "amber", "liq_g"))], seg=12,
                  loc=(x + r, yf + depth * 0.35, z))
            cyl(f"{p}C", 0.04, 0.06, (x + r, yf + depth * 0.35, z + 0.69), K["cork"], verts=8, bevel=0.0)
            x += 2 * r + 0.05
        elif kind == "box":
            w, h = rnd.uniform(0.5, 0.75), rnd.uniform(0.3, 0.5)
            box(f"{p}X", (w, depth * 0.7, h), (x + w / 2, yf + depth * 0.45, z + h / 2), K[rnd.choice(("kraft", "cen", "lacquer"))], bevel=0.015)
            iplate(f"{p}L", f"Tin_{rnd.randrange(7)}", w * 0.85, h * 0.4, 0.005, T(x + w / 2, yf + depth * 0.1 - 0.003, z + h * 0.5), K)
            x += w + 0.06
        elif kind == "soap":
            soap_stack(p, x + 0.22, yf + depth * 0.45, z, K, n=rnd.randint(2, 4))
            x += 0.5
        elif kind == "can":
            box(f"{p}Can", (0.4, 0.3, 0.6), (x + 0.2, yf + depth * 0.45, z + 0.3), K["zinc"], bevel=0.03)
            cyl(f"{p}Sp", 0.04, 0.2, (x + 0.32, yf + depth * 0.4, z + 0.66), K["zinc"], verts=8, bevel=0.0, rot=(0.4, 0, 0))
            tube(f"{p}H", [(x + 0.05, yf + depth * 0.45, z + 0.6), (x + 0.2, yf + depth * 0.45, z + 0.75), (x + 0.3, yf + depth * 0.45, z + 0.6)], 0.015,
                 K["iron"])
            iplate(f"{p}L", f"Crate_{1}", 0.34, 0.17, 0.005, T(x + 0.2, yf + depth * 0.45 - 0.155, z + 0.3), K)
            x += 0.48
        elif kind == "candles":
            for j in range(rnd.randint(4, 7)):
                cyl(f"{p}C{j}", 0.045, 0.7, (x + 0.06 + j * 0.1, yf + depth * 0.5, z + 0.05), K["tallow"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
            box(f"{p}Band", (0.08, 0.72, 0.1), (x + 0.3, yf + depth * 0.5, z + 0.05), K["kraft"], bevel=0.0)
            x += 0.8
        k += 1


def wall_shelf_stocked(M):
    """The general store's wall of stock (wall piece): 6 wide, 8.2 tall, 1.2 deep. Crimson enamel end frames with scrolled tops,
    cast-iron uprights, five shelves with brass ticket edges and price tickets: zinc lamp-oil cans and soap, labelled tins of tea,
    blacking and wax, jars and boxes, bottles; bundles of tallow candles hung in pairs by their wicks from a brass rod under the
    top shelf, and MORROW & VANE on the cornice."""
    K = kit(M)
    rnd = random.Random(4510)
    ir, br, gl, lq = K["iron"], K["brassf"], K["gilt"], K["lacquer"]
    W, Dd = 6.0, 1.2
    box("Back", (W, 0.06, 7.6), (0, -0.03, 3.8), lq, bevel=0.0)
    end = [(-Dd, 0), (0, 0), (0, 8.2), (-0.35, 8.2), (-0.5, 7.9), (-0.8, 7.7), (-Dd, 7.65)]
    for sx in (-1, 1):
        prism(f"End{sx}", end, sx * (W / 2 + 0.06), 0.12, K["cen"], plane="YZ", bevel=0.015)
        tube(f"EndEdge{sx}", [(sx * (W / 2 + 0.13), y, z) for y, z in end[1:] + end[:1]], 0.018, gl, square=True, poly=True)
        for k, z in enumerate((2.6, 5.6)):
            s = _mark()
            _quatrefoil(f"EndFoil{sx}{k}", 0, 0, 0, 0.24, gl)
            _xform(s, T(sx * (W / 2 + 0.13), -0.6, z) @ RZ(PI / 2))
    for x in (-1.0, 1.0):
        box(f"Upright{x}", (0.12, 0.12, 7.6), (x, -Dd + 0.08, 3.8), ir, bevel=0.015)
    zs = (0.35, 1.9, 3.4, 4.9, 6.4)
    for k, z in enumerate(zs):
        box(f"Shelf{k}", (W, Dd - 0.06, 0.08), (0, -Dd / 2, z - 0.04), lq, bevel=0.01)
        box(f"Edge{k}", (W, 0.04, 0.14), (0, -Dd + 0.01, z - 0.05), br, bevel=0.008)
        for j in range(3):
            x = -2.2 + j * 2.2 + rnd.uniform(-0.3, 0.3)
            iplate(f"Tick{k}{j}", f"Ticket_{(k * 3 + j) % 8}", 0.26, 0.15, 0.01, T(x, -Dd - 0.02, z - 0.05), K, edge="bone")
    box("Plinth", (W, Dd, 0.31), (0, -Dd / 2, 0.155), ir, bevel=0.02)
    box("Cornice", (W + 0.4, Dd + 0.1, 0.3), (0, -Dd / 2 - 0.05, 7.75), lq, bevel=0.03)
    box("CorniceBead", (W + 0.42, 0.03, 0.05), (0, -Dd - 0.11, 7.62), gl, bevel=0.01)
    iplate("Sign", "ShopSign", 3.4, 0.81, 0.03, T(0, -Dd - 0.12, 8.15), K, edge="crimson")
    for sx in (-1, 1):
        finial(f"Fin{sx}", sx * 2.0, -Dd + 0.1, 7.9, gl, s=0.8)
    shelf_goods("A", -W / 2, W / 2, zs[0], -Dd, Dd, K, rnd, ["can", "soap", "can", "box"])
    shelf_goods("B", -W / 2, W / 2, zs[1], -Dd, Dd, K, rnd, ["tin", "tin", "tin", "box"])
    shelf_goods("C", -W / 2, W / 2, zs[2], -Dd, Dd, K, rnd, ["jar", "box", "jar", "soap"])
    shelf_goods("D", -W / 2, W / 2, zs[3], -Dd, Dd, K, rnd, ["bottle", "bottle", "candles", "tin"])
    # the hanging candles under the top shelf, and boxes on it
    tube("CandleRod", [(-2.7, -0.75, 6.2), (2.7, -0.75, 6.2)], 0.025, br, poly=True)
    for sx in (-1, 1):
        tube(f"RodHook{sx}", [(sx * 2.7, -0.75, 6.2), (sx * 2.75, -0.5, 6.3), (sx * 2.75, -0.3, 6.32)], 0.02, br)
    for k in range(9):
        x = -2.4 + k * 0.6
        lowring(f"Loop{k}", (x, -0.75, 6.2), 0.04, "X", K["twine"], 0.008, n=6)
        for sy in (-1, 1):
            L = 0.75 + (k % 3) * 0.1
            tube(f"Wick{k}{sy}", [(x, -0.75, 6.17), (x, -0.75 + sy * 0.06, 6.08)], 0.006, K["twine"], poly=True)
            lathe(f"Hang{k}{sy}", [(0, 0), (0.035, 0.0), (0.05, 0.08), (0.05, L), (0, L)], K["tallow"], seg=10, loc=(x, -0.75 + sy * 0.06, 6.08 - L))
    for k in range(4):
        x = -2.3 + k * 1.5
        box(f"TopBox{k}", (1.1, 0.9, 0.55), (x, -0.55, 6.4 + 0.275), K["kraft"] if k % 2 else K["pine"], bevel=0.02)
        iplate(f"TopLab{k}", f"Crate_{k % 6}", 0.9, 0.42, 0.005, T(x, -1.005, 6.68), K)
    return _dims()


def island_shelf(M):
    """The freestanding island shelf, 5.0 long, 2.6 deep, 5.2 tall, stocked both sides: a stepped pyramid of three tiers between
    crimson enamel cast-iron end frames edged in gilt with quatrefoils; wire baskets of turnips, onions and black apples on the
    bottom tier, tins, jars and bottles above, parcels and candle boxes on top, and a brass ticket holder on the ridge."""
    K = kit(M)
    rnd = random.Random(4511)
    ir, br, gl, lq = K["iron"], K["brassf"], K["gilt"], K["lacquer"]
    L = 4.8
    prof = [(-1.3, 0), (1.3, 0), (1.3, 1.0), (0.9, 1.0), (0.9, 2.3), (0.55, 2.3), (0.55, 3.6), (0.25, 3.6), (0.25, 4.6), (0, 5.0), (-0.25, 4.6),
            (-0.25, 3.6), (-0.55, 3.6), (-0.55, 2.3), (-0.9, 2.3), (-0.9, 1.0), (-1.3, 1.0)]
    for sx in (-1, 1):
        x = sx * (L / 2 + 0.06)
        prism(f"End{sx}", prof, x, 0.12, K["cen"], plane="YZ", bevel=0.015)
        tube(f"EndEdge{sx}", [(x + sx * 0.065, y, z) for y, z in prof + prof[:1]], 0.02, gl, square=True, poly=True)
        for k, (y, z) in enumerate(((0, 1.6), (0, 2.95), (0, 4.15))):
            s = _mark()
            _quatrefoil(f"EndFoil{sx}{k}", 0, 0, 0, 0.3 if k < 2 else 0.18, gl)
            _xform(s, T(x + sx * 0.07, y, z) @ RZ(PI / 2))
        finial(f"Fin{sx}", x, 0, 5.0, gl, s=0.8)
    inner = [(y * 0.98, z) for y, z in prof]
    prism("Body", [(y, max(z - 0.04, 0.3)) for y, z in inner], 0, L, lq, plane="YZ")
    box("Plinth", (L, 2.5, 0.3), (0, 0, 0.15), ir, bevel=0.02)
    for sy in (-1, 1):
        for k, (yy, z) in enumerate(((1.3, 1.0), (0.9, 2.3), (0.55, 3.6))):
            box(f"Lip{sy}{k}", (L, 0.04, 0.12), (0, sy * (yy - 0.01), z + 0.02), br, bevel=0.008)
    for sy in (-1, 1):
        s = _mark()
        # bottom tier: wire baskets of produce
        for b in range(4):
            x = -1.8 + b * 1.2
            for side in (-1, 1):
                tube(f"Bk{sy}{b}{side}", [(x + side * 0.5, -1.25, 1.0), (x + side * 0.5, -1.25, 1.35), (x + side * 0.5, -0.92, 1.35),
                                          (x + side * 0.5, -0.92, 1.0)], 0.015, ir, poly=True)
            for z in (1.12, 1.35):
                tube(f"BkF{sy}{b}{z}", [(x - 0.5, -1.25, z), (x + 0.5, -1.25, z)], 0.012, ir, poly=True)
            box(f"BkBase{sy}{b}", (1.0, 0.34, 0.04), (x, -1.085, 1.02), ir, bevel=0.0)
            mat = (K["turnip"], K["onion"], K["apple"], K["turnip"])[b]
            for j in range(8):
                r = rnd.uniform(0.1, 0.13)
                sphere(f"Pr{sy}{b}{j}", r, (x - 0.36 + (j % 4) * 0.24 + rnd.uniform(-0.02, 0.02), -1.16 + (j // 4) * 0.15, 1.08 + r + (j // 4) * 0.05),
                       mat, seg=7, rings=4, scale=(1, 1, 0.9 if mat is not K["turnip"] else 1.1))
            iplate(f"BkTag{sy}{b}", f"Ticket_{(b + (sy > 0) * 4) % 8}", 0.24, 0.14, 0.01, T(x, -1.28, 1.2), K, edge="bone")
        shelf_goods(f"T2{sy}", -L / 2 + 0.05, L / 2 - 0.05, 2.32, -0.9, 0.35, K, rnd, ["tin", "jar", "bottle", "tin"])
        shelf_goods(f"T3{sy}", -L / 2 + 0.05, L / 2 - 0.05, 3.62, -0.55, 0.3, K, rnd, ["box", "candles", "box"])
        _xform(s, Matrix.Identity(4) if sy < 0 else RZ(PI))
    box("Ridge", (L, 0.1, 0.4), (0, 0, 4.75), br, bevel=0.015)
    for sy in (-1, 1):
        iplate(f"RidgeTag{sy}", f"Ticket_{3 if sy < 0 else 6}", 0.5, 0.3, 0.01, T(0, sy * 0.06, 4.75) @ RZ(0 if sy < 0 else PI), K, edge="bone")
    return _dims()


def apothecary_drawers(M):
    """The apothecary wall (wall piece): 6.4 wide, 9.6 tall. A lacquered cupboard base with three crimson gothic panels under a
    black marble ledge (3.4) with a brass mortar and pestle and stoppered bottles; above it 48 crimson-enamelled tin drawers, 8
    by 6, each with a brass label frame (Latin simples: RAD. VALER., FOL. MENTH., PULV. NOCTIS ...) and a knob, one pulled out
    full of dried herbs; a shelf of three great show globes of coloured water (Glass) and the gilt APOTHECARY header."""
    K = kit(M)
    rnd = random.Random(4512)
    ir, br, gl, lq = K["iron"], K["brassf"], K["gilt"], K["lacquer"]
    W = 6.4
    box("Base", (W, 1.3, 3.0), (0, -0.65, 1.7), lq, bevel=0.03)
    box("BasePlinth", (W + 0.1, 1.36, 0.2), (0, -0.68, 0.1), ir, bevel=0.02)
    for k, x in enumerate((-2.1, 0.0, 2.1)):
        gothic_panel(f"BasePan{k}", 1.8, 2.4, K, T(x, -1.305, 0.45))
        sphere(f"BaseKnob{k}", 0.06, (x + 0.75, -1.36, 1.7), br, seg=10, rings=5)
    box("Ledge", (W + 0.2, 1.45, 0.2), (0, -0.725, 3.3), K["marble"], bevel=0.03)
    box("LedgeNose", (W + 0.2, 0.04, 0.12), (0, -1.45, 3.3), br, bevel=0.01)
    # the drawer bank
    z0, z1 = 3.45, 7.65
    box("Bank", (W, 0.9, z1 - z0), (0, -0.45, (z0 + z1) / 2), lq, bevel=0.02)
    nc, nr = 8, 6
    cw, rh = (W - 0.2) / nc, (z1 - z0 - 0.1) / nr
    out = (1, 5)
    for r in range(nr):
        for c in range(nc):
            x = -W / 2 + 0.1 + (c + 0.5) * cw
            z = z0 + 0.05 + (r + 0.5) * rh
            dy = -0.55 if (r, c) == out else 0.0
            box(f"Dr{r}{c}", (cw - 0.06, 0.05, rh - 0.06), (x, -0.925 + dy, z), K["cen"], bevel=0.012, segments=1)
            box(f"DrF{r}{c}", (0.4, 0.02, 0.18), (x, -0.955 + dy, z + 0.12), br, bevel=0.0)
            iplate(f"DrL{r}{c}", f"Apo_{(r * nc + c) % 24}", 0.36, 0.145, 0.005, T(x, -0.966 + dy, z + 0.12), K, edge="parch")
            sphere(f"DrK{r}{c}", 0.045, (x, -0.99 + dy, z - 0.13), br, seg=8, rings=4)
            if (r, c) == out:
                for sx in (-1, 1):
                    box(f"DrSide{sx}", (0.03, 0.55, rh - 0.14), (x + sx * (cw / 2 - 0.06), -0.65, z - 0.02), K["cen"], bevel=0.0)
                for j in range(14):
                    sphere(f"Herb{j}", rnd.uniform(0.05, 0.08), (x + rnd.uniform(-0.25, 0.25), rnd.uniform(-1.05, -0.5), z - 0.08 + rnd.uniform(0, 0.08)),
                           K["herb"], seg=6, rings=4, scale=(1.4, 1, 0.6))
                for j in range(4):
                    tube(f"Stalk{j}", [(x - 0.25 + j * 0.15, -1.1, z - 0.05), (x - 0.15 + j * 0.12, -0.6, z + 0.02)], 0.012, K["herb"], poly=True)
    for c in range(nc + 1):
        box(f"Muntin{c}", (0.04, 0.03, z1 - z0), (-W / 2 + 0.1 + c * cw, -0.91, (z0 + z1) / 2), br, bevel=0.0)
    # the show globe shelf and the header
    box("GlobeShelf", (W, 1.0, 0.12), (0, -0.5, z1 + 0.06), lq, bevel=0.02)
    box("GlobeLip", (W, 0.04, 0.1), (0, -1.0, z1 + 0.08), br, bevel=0.008)
    globe = [(0, 0), (0.2, 0), (0.26, 0.05), (0.18, 0.12), (0.34, 0.3), (0.4, 0.55), (0.32, 0.8), (0.12, 0.95), (0.09, 1.05), (0.12, 1.12),
             (0.1, 1.14), (0, 1.14)]
    liq = ("liq_c", "liq_g", "liq_v")
    for k, x in enumerate((-2.2, 0.0, 2.2)):
        zb = z1 + 0.12
        lathe(f"Fill{k}", [(0, 0.14), (0.3, 0.3), (0.36, 0.55), (0.29, 0.72), (0, 0.72)], K[liq[k]], seg=20, loc=(x, -0.5, zb))
        lathe(f"Stopper{k}", [(0, 0), (0.1, 0), (0.14, 0.12), (0.1, 0.2), (0, 0.24)], gl, seg=14, loc=(x, -0.5, zb + 1.12))
        iplate(f"GlobeTag{k}", f"Apo_{(k * 7 + 3) % 24}", 0.5, 0.2, 0.01, T(x, -1.03, z1 + 0.06), K, edge="parch")
    for sx in (-1, 1):
        box(f"Pier{sx}", (0.25, 0.5, 2.0), (sx * (W / 2 - 0.12), -0.25, z1 + 1.1), lq, bevel=0.02)
    box("Crown", (W + 0.3, 0.55, 0.65), (0, -0.28, z1 + 2.42), lq, bevel=0.03)
    iplate("Header", "ApoHeader", 4.6, 0.52, 0.03, T(0, -0.57, z1 + 2.42), K)
    for x in (-W / 2, 0.0, W / 2):
        finial(f"Fin{x}", x, -0.3, z1 + 2.74, gl, s=0.9)
    # on the ledge: mortar and pestle, bottles, a funnel
    lathe("Mortar", [(0, 0), (0.3, 0), (0.33, 0.06), (0.36, 0.34), (0.32, 0.36), (0.26, 0.12), (0, 0.1)], br, seg=24, loc=(-2.0, -0.85, 3.4))
    tube("Pestle", [(-2.05, -0.85, 3.55), (-1.85, -0.95, 3.95)], 0.05, br)
    sphere("PestleEnd", 0.08, (-1.83, -0.96, 3.98), br, seg=10, rings=5)
    for k in range(4):
        jar(f"Bot{k}", 1.2 + k * 0.4, -0.85, 3.4, 0.13, 0.5, ("liq_a", "liq_g", "liq_v", "liq_c")[k], K, glass="amber" if k % 2 else "inkglass")
    set_group("Glass")
    for k, x in enumerate((-2.2, 0.0, 2.2)):
        lathe(f"Globe{k}", globe, K["glass"], seg=24, loc=(x, -0.5, z1 + 0.12))
    set_group("Main")
    return _dims()


def sweet_jar_shelf(M):
    """The confectioner's shelf (wall piece): 4.8 wide, 7.4 tall. A lacquered base cupboard, three stepped crimson enamel shelves
    of tall glass sweet jars (Glass) with black and brass lids and their oval labels (BAT DROPS, HUMBUGS, SHERBET MOONS,
    LIQUORICE BONES, VIOLET CREAMS, ACID TEARS, CINDER TOFFEE, MINT GHOSTS), the sweets heaped inside; a brass scoop, an open
    jar and a rack of paper cones on the counter top, and the gilt CONFECTIONS crest."""
    K = kit(M)
    rnd = random.Random(4513)
    ir, br, gl, lq = K["iron"], K["brassf"], K["gilt"], K["lacquer"]
    W = 4.8
    box("Back", (W, 0.08, 6.4), (0, -0.04, 3.2), K["cen"], bevel=0.0)
    box("Base", (W, 1.2, 1.6), (0, -0.6, 0.8), lq, bevel=0.03)
    for k, x in enumerate((-1.2, 1.2)):
        gothic_panel(f"BasePan{k}", 2.0, 1.1, K, T(x, -1.205, 0.3), foil=False)
    box("BaseTop", (W + 0.1, 1.3, 0.1), (0, -0.65, 1.65), K["marble"], bevel=0.02)
    for sx in (-1, 1):
        prism(f"Side{sx}", [(-1.25, 1.6), (0, 1.6), (0, 6.4), (-0.3, 6.4), (-0.35, 5.9), (-0.55, 5.6), (-0.6, 4.6), (-0.8, 4.4), (-0.85, 3.4),
                            (-1.05, 3.2), (-1.1, 2.2)], sx * (W / 2 + 0.05), 0.1, ir, plane="YZ", bevel=0.015)
    jars = []
    for t, (z, yb, n) in enumerate(((1.7, -0.95, 4), (3.35, -0.65, 4), (4.95, -0.35, 3))):
        if t:
            box(f"Tier{t}", (W, 0.7 if t == 1 else 0.5, 0.1), (0, yb + (0.35 if t == 1 else 0.25) - 0.05, z - 0.05), K["cen"], bevel=0.015)
            box(f"TierLip{t}", (W, 0.04, 0.12), (0, yb - 0.04, z - 0.03), br, bevel=0.008)
        for j in range(n):
            x = -W / 2 + W * (j + 0.5) / n
            jars.append((x, yb + 0.3 if t else -0.8, z))
    cols = ("s_violet", "s_black", "s_amber", "s_black", "s_violet", "s_green", "s_toffee", "s_teal")
    r, h = 0.3, 1.25
    shell = [(0, 0), (r, 0), (r + 0.02, 0.05), (r + 0.02, h * 0.8), (r * 0.8, h * 0.9), (r * 0.62, h * 0.93), (r * 0.62, h), (0, h)]
    for k, (x, y, z) in enumerate(jars):
        lab = k % 8
        if k == 0:
            continue    # its place is taken by the open jar and the scoop
        fill = rnd.uniform(0.45, 0.75) * h
        lathe(f"Fill{k}", [(0, 0.02), (r - 0.02, 0.02), (r - 0.02, fill), (0, fill + 0.05)], K[cols[lab]], seg=16, loc=(x, y, z))
        for j in range(7):
            a = j / 7 * 2 * PI
            sphere(f"Sw{k}{j}", 0.07, (x + math.cos(a) * 0.17, y + math.sin(a) * 0.17, z + fill + 0.02), K[cols[(lab + j) % 8]], seg=6, rings=4)
        lathe(f"Lid{k}", [(0, 0), (r * 0.66, 0), (r * 0.7, 0.04), (r * 0.66, 0.12), (r * 0.3, 0.16), (r * 0.12, 0.24), (0, 0.26)],
              K["ink"] if k % 2 else br, seg=18, loc=(x, y, z + h))
        sphere(f"LidKnob{k}", 0.05, (x, y, z + h + 0.28), br, seg=8, rings=4)
        wrap(f"Lab{k}", f"Sweet_{lab}", r + 0.03, h * 0.42, 0.42, 0.62, T(x, y, z), K, n=8)
    # the open jar and the scoop on the counter top
    x, y, z = jars[0]
    x -= 0.2
    lathe("OpenFill", [(0, 0.02), (r - 0.02, 0.02), (r - 0.02, 0.5), (0, 0.55)], K["s_red"], seg=16, loc=(x, y, z))
    for j in range(9):
        sphere(f"OSw{j}", 0.07, (x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15), z + 0.55), K["s_red"], seg=6, rings=4)
    wrap("OpenLab", "Sweet_0", r + 0.03, h * 0.42, 0.42, 0.62, T(x, y, z), K, n=8)
    lathe("OpenLid", [(0, 0), (r * 0.66, 0), (r * 0.7, 0.04), (r * 0.66, 0.12), (r * 0.3, 0.16), (r * 0.12, 0.24), (0, 0.26)], br, seg=18,
          loc=(x + 0.62, y - 0.1, z))
    lathe("Scoop", [(0, 0), (0.1, 0.0), (0.12, 0.12), (0.11, 0.13), (0.09, 0.02), (0, 0.02)], br, seg=14, loc=(0, 0, 0), scale=(1.6, 1))
    _xform(len(P.PARTS) - 1, T(x + 0.05, y - 0.1, z + 0.75) @ RY(0.5))
    tube("ScoopHandle", [(x + 0.15, y - 0.1, z + 0.82), (x + 0.45, y - 0.15, z + 1.05)], 0.025, br)
    # a rack of paper cones
    cx = 1.75
    box("ConeRack", (0.7, 0.25, 0.05), (cx, -0.9, 2.3), br, bevel=0.01)
    for sx in (-1, 1):
        tube(f"ConeLeg{sx}", [(cx + sx * 0.3, -0.9, 1.7), (cx + sx * 0.3, -0.9, 2.3)], 0.015, br, poly=True)
    for j in range(4):
        cone(f"PCone{j}", 0.09, 0.005, 0.55, (cx - 0.24 + j * 0.16, -0.9, 2.2), K["kraft"] if j % 2 else K["paper"], verts=12, rot=(PI, 0, 0))
    # the crest
    crest = [(-2.0, 6.4), (2.0, 6.4)] + arch_xz(2.0, -2.0, 6.4, 1.0, n=12)[1:-1]
    prism("Crest", crest, -0.1, 0.14, K["cen"], plane="XZ", bevel=0.015)
    tube("CrestEdge", [(x, -0.18, z) for x, z in arch_xz(-2.0, 2.0, 6.42, 1.0, n=12)], 0.025, gl, square=True, poly=True)
    iplate("Header", "SweetHeader", 2.8, 0.43, 0.02, T(0, -0.19, 6.78), K)
    for xx in (-2.3, 2.3):
        finial(f"Fin{xx}", xx, -0.3, 6.4, gl, s=0.8)
    set_group("Glass")
    for k, (x, y, z) in enumerate(jars):
        if k == 0:
            x -= 0.2
            lathe("OpenJar", [(0, 0), (r, 0), (r + 0.02, 0.05), (r + 0.02, h * 0.8), (r * 0.8, h * 0.9), (r * 0.62, h * 0.93), (r * 0.62, h),
                              (r * 0.58, h), (r * 0.58, h * 0.94), (r * 0.76, h * 0.9), (r - 0.01, h * 0.8), (r - 0.01, 0.05), (0, 0.04)], K["glass"], seg=24,
                  loc=(x, y, z))
            continue
        lathe(f"Jar{k}", shell, K["glass"], seg=24, loc=(x, y, z))
    set_group("Main")
    return _dims()


def postcard_spinner(M):
    """The postcard spinner: a cast-iron spindle 6.6 tall on four scrolled feet, a square revolving rack of four faces with four
    tiers of wire pockets holding painted postcards (the Institution by night, the bell tower, moonrise on Blackwater, a raven,
    the high street, the old watchers, the chapel, a full moon), a bottom tier of pamphlets (the night omnibus, the old crypts,
    curfew, the harvest fair), a POSTCARDS one-yen sign and a crowned finial."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    for k in range(4):
        a = k * PI / 2 + PI / 4
        s = _mark()
        prism(f"Foot{k}", [(0.0, 0.0), (0.95, 0.0), (1.0, 0.08), (0.7, 0.14), (0.35, 0.35), (0.12, 0.6), (0.0, 0.6)], 0, 0.1, ir, plane="XZ", bevel=0.01)
        sphere(f"Toe{k}", 0.08, (0.95, 0, 0.06), br, seg=8, rings=5)
        _xform(s, RZ(a))
    lathe("Spindle", [(0, 0), (0.12, 0), (0.12, 0.6), (0.06, 0.7), (0.05, 6.1), (0.08, 6.15), (0, 6.15)], ir, seg=12)
    lathe("Collar", [(0, 0), (0.14, 0), (0.16, 0.06), (0.14, 0.12), (0, 0.12)], br, seg=16, loc=(0, 0, 0.75))
    hw = 0.68
    zt = tuple(1.62 + t * 0.66 for t in range(6))
    for k in range(4):
        s = _mark()
        y = -hw
        for x in (-0.33, 0.33):
            tube(f"Back{k}{x}", [(x, y + 0.12, 0.9), (x, y + 0.12, 5.7)], 0.014, ir, poly=True)
        for t, z in enumerate((0.95,) + zt):
            tube(f"Lip{k}{t}", [(-hw + 0.04, y, z + 0.12), (hw - 0.04, y, z + 0.12)], 0.015, ir, poly=True)
            tube(f"Tray{k}{t}", [(-hw + 0.04, y, z), (-hw + 0.04, y + 0.12, z)], 0.012, ir, poly=True)
            tube(f"Tray2{k}{t}", [(hw - 0.04, y, z), (hw - 0.04, y + 0.12, z)], 0.012, ir, poly=True)
            if t == 0:
                for c in range(2):
                    iplate(f"Pam{k}{c}", f"Pamph_{(k + c) % 4}", 0.42, 0.61, 0.01, T(-0.32 + c * 0.64, y + 0.07, z + 0.32) @ RX(-0.12), K, edge="parch")
            else:
                tube(f"Div{k}{t}", [(0, y, z), (0, y, z + 0.2)], 0.012, ir, poly=True)
                for c in range(2):
                    iplate(f"Post{k}{t}{c}", f"Post_{(k * 2 + t * 3 + c) % 8}", 0.62, 0.41, 0.01, T(-0.32 + c * 0.64, y + 0.07, z + 0.23) @ RX(-0.15), K,
                           edge="paper")
        _xform(s, RZ(k * PI / 2))
    for z in (0.9, 5.7):
        box(f"Frame{z}", (2 * hw, 2 * hw, 0.06), (0, 0, z), ir, bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f"Corner{sx}{sy}", [(sx * hw, sy * hw, 0.9), (sx * hw, sy * hw, 5.7)], 0.025, ir, poly=True)
            sphere(f"CornerBall{sx}{sy}", 0.05, (sx * hw, sy * hw, 5.76), br, seg=8, rings=4)
    for sy in (-1, 1):
        iplate(f"Sign{sy}", "PostHeader", 1.3, 0.33, 0.02, T(0, sy * 0.015, 6.0) @ RZ(0 if sy < 0 else PI), K)
    box("SignFrame", (1.38, 0.06, 0.04), (0, 0, 6.18), br, bevel=0.01)
    box("SignFrameLo", (1.38, 0.06, 0.04), (0, 0, 5.82), br, bevel=0.01)
    for k in range(4):
        a = k * PI / 2
        tube(f"Crown{k}", [(0, 0, 6.2), (math.cos(a) * 0.2, math.sin(a) * 0.2, 6.35), (math.cos(a) * 0.12, math.sin(a) * 0.12, 6.5)], 0.02, gl)
    finial("Fin", 0, 0, 6.5, gl, s=0.7)
    return _dims()


def _lumpy(ob, strength, size, seed):
    """Cloth lumps: a Displace modifier with a clouds texture (applied when the parts are joined)."""
    tx = bpy.data.textures.new(f"Lump{seed}", "CLOUDS")
    tx.noise_scale = size
    tx.noise_depth = 2
    sd = ob.modifiers.new("Smooth", "SUBSURF")
    sd.levels = 1
    sd.render_levels = 1
    md = ob.modifiers.new("Lump", "DISPLACE")
    md.texture = tx
    md.strength = strength
    md.mid_level = 0.5
    md.texture_coords = "LOCAL"
    return ob


def sack(prefix, h, r, mtx, K, label=None, mat=None, open_fill=None, jit=4401):
    """A hessian sack h tall: slumped and lumpy, tied at the neck with its gathered ears flopping (or open with its top rolled down
    over `open_fill`), a stencilled print on its front."""
    s = _mark()
    mat = mat or K["hessian"]
    rnd = random.Random(jit)
    if open_fill is None:
        prof = [(0, 0), (r * 0.8, 0), (r * 1.0, 0.05 * h), (r * 1.1, 0.18 * h), (r * 1.08, 0.35 * h), (r * 1.0, 0.52 * h), (r * 0.9, 0.66 * h),
                (r * 0.72, 0.77 * h), (r * 0.46, 0.85 * h), (r * 0.22, 0.9 * h), (r * 0.15, 0.93 * h), (0, 0.935 * h)]
        ob = lathe(f"{prefix}S", prof, mat, seg=20, jitter=(0.03, jit), scale=(1, 0.78))
        _lumpy(ob, r * 0.22, r * 0.5, jit)
        hoop(f"{prefix}Tie", (0, 0, 0.915 * h), r * 0.17, "Z", K["twine"], thick=0.025)
        for k in range(6):
            a = k * PI / 3 + rnd.uniform(-0.3, 0.3)
            tilt = rnd.uniform(0.9, 1.4)
            ss = _mark()
            lathe(f"{prefix}Ear{k}", [(0, 0), (r * 0.09, 0.0), (r * 0.14, 0.05 * h), (r * 0.08, 0.1 * h), (0, 0.11 * h)], mat, seg=8, scale=(1.7, 0.45))
            _xform(ss, T(0, 0, 0.92 * h) @ RZ(a) @ RY(tilt))
    else:
        prof = [(0, 0), (r * 0.8, 0), (r * 1.0, 0.05 * h), (r * 1.08, 0.2 * h), (r * 1.05, 0.5 * h), (r * 1.0, 0.75 * h), (r * 1.08, 0.79 * h),
                (r * 1.14, 0.84 * h), (r * 1.1, 0.89 * h), (r * 0.98, 0.9 * h), (r * 0.94, 0.85 * h), (r * 0.93, 0.6 * h), (0, 0.6 * h)]
        ob = lathe(f"{prefix}S", prof, mat, seg=20, jitter=(0.025, jit), scale=(1, 0.85))
        _lumpy(ob, r * 0.15, r * 0.5, jit)
        lathe(f"{prefix}F", [(0, 0.8 * h), (r * 0.92, 0.8 * h), (r * 0.6, 0.86 * h), (0, 0.9 * h)], K[open_fill], seg=16, scale=(1, 0.85))
    if label:
        wrap(f"{prefix}L", label, r * 1.14, 0.38 * h, h * 0.42, h * 0.42, Matrix.Identity(4), K, n=8, sy=0.8)
    _xform(s, mtx)


def stock_sacks(M):
    """Sacks of stock by the store-room door: a cast-iron sack truck with brass grips and rubber-tyred wheels loaded with two
    sacks, a slumped sack of FINE FLOUR and one of BROWN SUGAR, and an open sack of COFFEE beans with its top rolled down and a
    brass scoop in it; the hessian stencilled MORROW & VANE."""
    K = kit(M)
    rnd = random.Random(4514)
    ir, br = K["iron"], K["brassf"]
    # the sack truck, leaning back
    s = _mark()
    for sx in (-1, 1):
        tube(f"Rail{sx}", [(sx * 0.5, 0, 0.1), (sx * 0.5, 0, 3.6), (sx * 0.42, 0.1, 4.0)], 0.05, ir, poly=True)
        cyl(f"Grip{sx}", 0.06, 0.35, (sx * 0.38, 0.14, 4.1), br, rot=(0.3, 0, 0), verts=10, bevel=0.015)
        cyl(f"Wheel{sx}", 0.38, 0.16, (sx * 0.68, 0.3, 0.38), K["rubber"], rot=(0, PI / 2, 0), verts=20, bevel=0.04)
        cyl(f"Hub{sx}", 0.14, 0.2, (sx * 0.68, 0.3, 0.38), br, rot=(0, PI / 2, 0), verts=12, bevel=0.02)
        for k in range(5):
            a = k * 2 * PI / 5
            tube(f"Spoke{sx}{k}", [(sx * 0.68, 0.3, 0.38), (sx * 0.68, 0.3 + math.cos(a) * 0.3, 0.38 + math.sin(a) * 0.3)], 0.02, ir, poly=True)
    for z in (1.0, 2.0, 3.0):
        tube(f"Cross{z}", [(-0.5, 0.02, z), (0.5, 0.02, z)], 0.035, ir, poly=True)
    tube("Axle", [(-0.62, 0.3, 0.38), (0.62, 0.3, 0.38)], 0.04, ir, poly=True)
    box("Toe", (1.2, 0.6, 0.05), (0, -0.28, 0.08), ir, bevel=0.01)
    for sx in (-1, 1):
        tube(f"Strut{sx}", [(sx * 0.5, 0.02, 0.6), (sx * 0.58, 0.3, 0.38)], 0.03, ir, poly=True)
    sack("TA", 1.6, 0.48, T(0, -0.3, 0.12), K, label="Sack_1", jit=4402)
    sack("TB", 1.4, 0.44, T(0.02, -0.25, 1.72) @ RZ(0.15), K, label="Sack_3", jit=4403)
    _xform(s, T(-1.6, 0.4, 0) @ RZ(0.3) @ T(0, 0.3, 0.0) @ RX(-0.28) @ T(0, -0.3, 0))
    # the floor sacks
    sack("F1", 1.5, 0.55, T(0.3, -0.2, 0) @ RZ(0.4) @ Matrix.Diagonal((1.05, 1.05, 0.88, 1)), K, label="Sack_0", jit=4404)
    sack("F2", 1.7, 0.5, T(1.35, 0.5, 0) @ RZ(-0.3), K, label="Sack_4", jit=4405)
    sack("F3", 1.5, 0.52, T(1.3, -0.75, 0) @ RZ(0.1), K, label="Sack_2", open_fill="beans", jit=4406)
    for j in range(24):
        a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.4)
        sphere(f"Bean{j}", 0.035, (1.3 + math.cos(a) * rr, -0.75 + math.sin(a) * rr * 0.85, 1.25 + rnd.uniform(0.0, 0.08)), K["beans"], seg=6, rings=4,
               scale=(1.3, 0.9, 0.7))
    s = _mark()
    lathe("Scoop", [(0, 0), (0.14, 0.0), (0.16, 0.25), (0.15, 0.26), (0.13, 0.03), (0, 0.03)], br, seg=16, scale=(1.3, 1))
    tube("ScoopH", [(0.2, 0, 0.1), (0.55, 0, 0.12)], 0.03, br, poly=True)
    _xform(s, T(1.25, -0.8, 1.22) @ RZ(-0.8) @ RY(-0.5))
    for j in range(10):
        sphere(f"Spill{j}", 0.035, (1.3 + rnd.uniform(-0.6, 0.6), -1.4 + rnd.uniform(-0.2, 0.2), 0.02), K["beans"], seg=6, rings=4, scale=(1.3, 0.9, 0.7))
    return _dims()


def crate(prefix, w, d, h, mtx, K, label, lid=True, rnd=None):
    """A slatted pine crate w x d x h with dark corner battens, iron corner plates, rope handles and a stencil on its front."""
    s = _mark()
    pine, dk, ir = K["pine"], K["pinedk"], K["iron"]
    box(f"{prefix}Core", (w - 0.1, d - 0.1, h - (0.08 if lid else 0.2)), (0, 0, (h - (0.08 if lid else 0.2)) / 2 + 0.04), dk, bevel=0.0)
    n = max(2, round(h / 0.45))
    ph = (h - 0.04 * (n - 1)) / n
    for k in range(n):
        z = ph / 2 + k * (ph + 0.04)
        for sy in (-1, 1):
            box(f"{prefix}P{k}{sy}", (w, 0.06, ph), (0, sy * (d / 2 - 0.03), z), pine, bevel=0.012, segments=1)
        for sx in (-1, 1):
            box(f"{prefix}Q{k}{sx}", (0.06, d - 0.12, ph), (sx * (w / 2 - 0.03), 0, z), pine, bevel=0.012, segments=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"{prefix}B{sx}{sy}", (0.12, 0.12, h), (sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), h / 2), dk, bevel=0.015, segments=1)
            for z in (0.08, h - 0.08):
                box(f"{prefix}I{sx}{sy}{z:.1f}", (0.16, 0.16, 0.12), (sx * (w / 2 - 0.02), sy * (d / 2 - 0.02), z), ir, bevel=0.01, segments=1)
    if lid:
        for k in range(3):
            box(f"{prefix}L{k}", (w + 0.02, (d - 0.04) / 3, 0.06), (0, -d / 2 + (k + 0.5) * d / 3, h + 0.01), pine, bevel=0.012, segments=1)
    for sx in (-1, 1):
        tube(f"{prefix}R{sx}", [(sx * (w / 2 + 0.01), -0.2, h * 0.7), (sx * (w / 2 + 0.1), -0.12, h * 0.6), (sx * (w / 2 + 0.1), 0.12, h * 0.6),
                                (sx * (w / 2 + 0.01), 0.2, h * 0.7)], 0.03, K["hemp"])
    iplate(f"{prefix}St", label, min(w * 0.74, (h * 0.62) * 2.0), min(h * 0.62, w * 0.74 / 2.0), 0.005, T(0, -d / 2 - 0.004, h * 0.5), K, edge="crate")
    _xform(s, mtx)


def stock_crates(M):
    """Stacked stock crates with stencilled labels: a big TALLOW CANDLES crate under an INK crate, a LAMP OIL crate beside them,
    a SAFETY MATCHES crate on the floor and, on top, an open CARBOLIC SOAP crate packed with straw and bundles of candles, its
    lid propped against the stack; a crowbar leaning, straw spilled on the floor; 4.3 wide, 4.6 tall."""
    K = kit(M)
    rnd = random.Random(4515)
    crate("A", 2.6, 1.7, 1.5, T(-0.7, 0, 0), K, "Crate_0")
    crate("B", 1.7, 1.5, 1.35, T(1.55, -0.05, 0) @ RZ(-0.08), K, "Crate_1")
    crate("C", 2.0, 1.4, 1.2, T(-0.75, 0.05, 1.56) @ RZ(0.06), K, "Crate_2")
    crate("D", 1.5, 1.2, 0.95, T(-0.65, 0.0, 2.83) @ RZ(-0.1), K, "Crate_4", lid=False)
    crate("E", 1.3, 1.1, 0.9, T(1.6, -1.55, 0) @ RZ(0.25), K, "Crate_3")
    # straw and candles in the open crate
    s = _mark()
    for j in range(16):
        sphere(f"Straw{j}", rnd.uniform(0.16, 0.24), (rnd.uniform(-0.55, 0.55), rnd.uniform(-0.4, 0.4), 0.8), K["straw"], seg=8, rings=4,
               scale=(1.3, 1.0, 0.45))
    for j in range(5):
        cyl(f"Bundle{j}", 0.12, 0.6, (-0.45 + j * 0.22, rnd.uniform(-0.15, 0.15), 1.0), K["tallow"], rot=(rnd.uniform(-0.25, 0.25), 0.15, 0), verts=12,
            bevel=0.02)
        hoop(f"BundleTie{j}", (-0.45 + j * 0.22, 0, 1.0), 0.125, "Z", K["twine"], thick=0.012)
    for j in range(10):
        a = rnd.uniform(0, 2 * PI)
        tube(f"Strand{j}", [(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.45, 0.45), 0.9), (rnd.uniform(-0.8, 0.8), -0.62, 0.95 + rnd.uniform(0, 0.15)),
                            (rnd.uniform(-0.8, 0.8), -0.7, 0.75)], 0.008, K["straw"])
    _xform(s, T(-0.65, 0.0, 2.83) @ RZ(-0.1))
    # the lid, propped
    s = _mark()
    for k in range(3):
        box(f"LidP{k}", (0.06, 1.52, 0.38), (0, 0, 0.2 + k * 0.4), K["pine"], bevel=0.012, segments=1)
    for k in range(2):
        box(f"LidBatten{k}", (0.05, 0.12, 1.15), (0.055, -0.55 + k * 1.1, 0.6), K["pinedk"], bevel=0.01, segments=1)
    _xform(s, T(-2.32, -0.1, 0) @ RY(0.28))
    # crowbar and straw on the floor
    tube("Crowbar", [(2.75, -0.5, 0.05), (2.5, -0.45, 1.25), (2.44, -0.4, 1.36), (2.4, -0.32, 1.34)], 0.035, K["iron"], poly=True)
    for j in range(12):
        x, y = rnd.uniform(-1.6, 1.6), rnd.uniform(-1.6, -0.9)
        tube(f"Floor{j}", [(x, y, 0.01), (x + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.2, 0.2), 0.01)], 0.008, K["straw"], poly=True)
    B43._ground(0)
    return _dims()



# ================================================================== the bookshop

def bookshop_counter(M):
    """The bookseller's sales counter, 5 long and 3.4 tall: a black marble top and brass nosing on a cast-iron front holding a
    locked rare-books case behind two glass doors (Glass), the gilt LANTERNLIGHT BOOKS plate on its frieze; on top a tower of
    string-tied books, a stack of new covers, an open ledger and a brass bell-less letter scale; the bookseller's side has two
    shelves of stock."""
    K = kit(M)
    rnd = random.Random(4520)
    ir, br, gl, lq, mb = K["iron"], K["brassf"], K["gilt"], K["lacquer"], K["marble"]
    L, Dd = 5.0, D_C
    box("Top", (L, Dd + 0.12, 0.18), (0, -0.06, H_C - 0.09), mb, bevel=0.03)
    box("Nose", (L, 0.05, 0.12), (0, -1.21, H_C - 0.1), br, bevel=0.012)
    box("Frieze", (L, 0.12, 0.42), (0, -1.04, H_C - 0.39), lq, bevel=0.02)
    iplate("Plate", "BookPlate", 3.2, 0.36, 0.02, T(0, -1.11, H_C - 0.39), K)
    box("Plinth", (L, 0.2, 0.34), (0, -0.98, 0.17), ir, bevel=0.02)
    box("Kick", (L, 0.03, 0.22), (0, -1.09, 0.15), br, bevel=0.008)
    box("Carcass", (L, Dd - 0.3, H_C - 0.5), (0, 0.15, (H_C - 0.5) / 2), lq, bevel=0.02)
    zb, zt = 0.34, H_C - 0.6
    for x in (-L / 2 + 0.1, -0.05, L / 2 - 0.1):
        box(f"Stile{x:.1f}", (0.2, 0.16, zt - zb), (x, -1.02, (zb + zt) / 2), ir, bevel=0.02)
    # the rare-books case: two bays of two shelves behind glass
    for bay, (bx0, bx1) in enumerate(((-L / 2 + 0.2, -0.15), (0.05, L / 2 - 0.2))):
        box(f"CaseBack{bay}", (bx1 - bx0, 0.05, zt - zb), ((bx0 + bx1) / 2, -0.1, (zb + zt) / 2), K["velvet"], bevel=0.0)
        box(f"CaseShelf{bay}", (bx1 - bx0, 0.9, 0.06), ((bx0 + bx1) / 2, -0.55, 1.5), lq, bevel=0.01)
        box(f"CaseFloor{bay}", (bx1 - bx0, 0.9, 0.06), ((bx0 + bx1) / 2, -0.55, zb + 0.03), lq, bevel=0.01)
        for z in (zb + 0.06, 1.53):
            B30.fill_row(f"RB{bay}{z:.1f}", bx0 + 0.05, bx1 - 0.05, z, -0.98, 0.8, 1.1, rnd, K, p_set=0.6, p_flat=0.05, p_lean=0.08, p_gap=0.02)
        dx0, dx1 = bx0 + 0.03, bx1 - 0.03
        box(f"DoorTop{bay}", (dx1 - dx0, 0.06, 0.1), ((dx0 + dx1) / 2, -1.06, zt - 0.05), br, bevel=0.01)
        box(f"DoorBot{bay}", (dx1 - dx0, 0.06, 0.1), ((dx0 + dx1) / 2, -1.06, zb + 0.05), br, bevel=0.01)
        xm = (dx0 + dx1) / 2
        for x in (dx0 + 0.04, xm - 0.03, xm + 0.03, dx1 - 0.04):
            box(f"DoorStile{bay}{x:.2f}", (0.06, 0.06, zt - zb), (x, -1.06, (zb + zt) / 2), br, bevel=0.01)
        tube(f"DoorArch{bay}", [(x, -1.09, z) for x, z in arch_xz(dx0 + 0.08, xm - 0.06, zt - 0.6, 0.45, n=10)], 0.02, gl, square=True, poly=True)
        tube(f"DoorArchB{bay}", [(x, -1.09, z) for x, z in arch_xz(xm + 0.06, dx1 - 0.08, zt - 0.6, 0.45, n=10)], 0.02, gl, square=True, poly=True)
        box(f"Lock{bay}", (0.1, 0.04, 0.16), (xm, -1.1, 1.5), gl, bevel=0.01)
    # the bookseller's side: two shelves of stock
    for z in (0.4, 1.7):
        box(f"BackShelf{z}", (L - 0.1, 0.9, 0.06), (0, 0.6, z - 0.03), lq, bevel=0.01)
        s = _mark()
        B30.fill_row(f"BS{z}", -L / 2 + 0.15, L / 2 - 0.15, 0, -0.45, 0.8, 1.2, rnd, K, p_flat=0.2, p_gap=0.1)
        _xform(s, T(0, 0.6, z) @ RZ(PI) @ T(0, 0.0, 0))
    # on top
    zt0 = H_C
    s = _mark()
    top = B30.flat_stack("Tower", 0, 0, 0, 7, rnd, K, jitter=6, hmax=1.3)
    box("TowerTieA", (0.03, 1.05, top + 0.02), (0, 0, (top + 0.02) / 2), K["twine"], bevel=0.0)
    box("TowerTieB", (1.35, 0.03, top + 0.02), (0, 0, (top + 0.02) / 2), K["twine"], bevel=0.0)
    hoop("TowerKnot", (0, 0, top + 0.03), 0.05, "Z", K["twine"], thick=0.015)
    _xform(s, T(-1.7, -0.2, zt0) @ RZ(0.15))
    for k in range(4):
        cover_book(f"New{k}", k + 2, 0.85, 1.25, 0.15, T(-0.4 + rnd.uniform(-0.03, 0.03), -0.45, zt0 + k * 0.152) @ RZ(rnd.uniform(-0.12, 0.12)), K)
    s = _mark()
    B30.open_book("Ledger", "Pages_Moon", 1.4, 0.95, Matrix.Identity(4), M, K, cover="leather", lift=0.08)
    _xform(s, T(0.95, -0.35, zt0) @ RZ(-0.08))
    tube("Pen", [(1.45, -0.6, zt0 + 0.12), (1.85, -0.4, zt0 + 0.12)], 0.02, K["ink"], poly=True)
    lathe("Inkwell", [(0, 0), (0.12, 0), (0.12, 0.12), (0.05, 0.16), (0.05, 0.2), (0, 0.2)], K["inkglass"], seg=14, loc=(1.9, -0.2, zt0))
    set_group("Glass")
    for bay, (bx0, bx1) in enumerate(((-L / 2 + 0.2, -0.15), (0.05, L / 2 - 0.2))):
        box(f"Pane{bay}", (bx1 - bx0 - 0.1, 0.02, zt - zb - 0.15), ((bx0 + bx1) / 2, -1.05, (zb + zt) / 2), K["glass"], bevel=0.0)
    set_group("Main")
    return _dims()


def iron_trestle(prefix, x, w, h, K, depth=2.4):
    """A cast-iron table trestle at x: two legs splayed in Y with a pointed arch between and a foot bar."""
    ir = K["iron"]
    for sy in (-1, 1):
        tube(f"{prefix}Leg{sy}", [(x, sy * (depth / 2 - 0.15), 0.08), (x, sy * (depth / 2 - 0.35), h - 0.12)], 0.06, ir, square=True, poly=True)
        sphere(f"{prefix}Foot{sy}", 0.1, (x, sy * (depth / 2 - 0.15), 0.07), ir, seg=8, rings=5, scale=(1, 1.4, 0.7))
    tube(f"{prefix}Arch", [(x, y, z) for y, z in arch_xz(-(depth / 2 - 0.4), depth / 2 - 0.4, h - 1.0, 0.75, n=10)], 0.04, ir, square=True, poly=True)
    tube(f"{prefix}Bar", [(x, -(depth / 2 - 0.25), 0.5), (x, depth / 2 - 0.25, 0.5)], 0.04, ir, square=True, poly=True)
    _quatrefoil(f"{prefix}Q", 0, 0, 0, 0.22, K["gilt"])
    _xform(len(P.PARTS) - 2, T(x, 0, h - 0.55) @ RZ(PI / 2))


def new_releases_table(M):
    """The new-releases table: a black marble top 4.4 x 2.6 (2.9 tall) on two cast-iron gothic trestles with a slatted iron shelf
    of boxed stock; pyramids of new books face up (THE LANTERN BELOW, RAVENS OF GREYHALLOW, SALT & BONE ...), books stood up on
    brass wire stands and the NEW THIS MOON card on a brass stand in the middle."""
    K = kit(M)
    rnd = random.Random(4521)
    ir, br, gl, mb = K["iron"], K["brassf"], K["gilt"], K["marble"]
    W, Dd, H = 4.4, 2.6, 2.9
    box("Top", (W, Dd, 0.16), (0, 0, H - 0.08), mb, bevel=0.04)
    box("Apron", (W - 0.3, Dd - 0.3, 0.2), (0, 0, H - 0.26), K["lacquer"], bevel=0.02)
    box("ApronBead", (W - 0.28, Dd - 0.28, 0.04), (0, 0, H - 0.36), gl, bevel=0.01)
    for x in (-W / 2 + 0.45, W / 2 - 0.45):
        iron_trestle(f"T{x:.1f}", x, W, H - 0.16, K, depth=Dd)
    for k in range(5):
        box(f"Slat{k}", (W - 1.0, 0.24, 0.05), (0, -0.8 + k * 0.4, 0.55), ir, bevel=0.01)
    for k in range(3):
        box(f"StockBox{k}", (0.9, 0.8, 0.45), (-1.0 + k * 1.0, rnd.uniform(-0.3, 0.3), 0.8), K["kraft"], bevel=0.02)
        iplate(f"StockLab{k}", "BookPlate", 0.7, 0.1, 0.005, T(-1.0 + k * 1.0, -0.4 + 0.0, 0.85), K)
    z = H
    # three pyramids of covers
    for p_, (cx, cy, base) in enumerate(((-1.45, -0.35, 0), (0.0, 0.45, 3), (1.45, -0.35, 6))):
        n = 5 - (p_ % 2)
        for k in range(n):
            cover_book(f"Py{p_}{k}", base + (k % 3), 0.85, 1.25, 0.16, T(cx + rnd.uniform(-0.04, 0.04), cy + rnd.uniform(-0.04, 0.04), z + k * 0.162) @
                       RZ(rnd.uniform(-0.18, 0.18)), K)
    # books on wire stands
    for k, (x, y, i) in enumerate(((-0.75, -0.75, 4), (0.75, -0.75, 1))):
        tube(f"Stand{k}", [(x - 0.3, y + 0.1, z), (x - 0.3, y - 0.05, z + 0.06), (x - 0.3, y + 0.15, z + 0.7), (x - 0.3, y + 0.5, z)], 0.012, br, poly=True)
        tube(f"Stand2{k}", [(x + 0.3, y + 0.1, z), (x + 0.3, y - 0.05, z + 0.06), (x + 0.3, y + 0.15, z + 0.7), (x + 0.3, y + 0.5, z)], 0.012, br, poly=True)
        tube(f"StandLip{k}", [(x - 0.3, y - 0.05, z + 0.06), (x + 0.3, y - 0.05, z + 0.06)], 0.012, br, poly=True)
        stand_book(f"SB{k}", i, x, y + 0.14, z + 0.06, K, lean=18)
    # the header card
    tube("CardPost", [(0, -0.35, z), (0, -0.35, z + 1.3)], 0.02, br, poly=True)
    cyl("CardFoot", 0.18, 0.04, (0, -0.35, z + 0.02), br, verts=16, bevel=0.01)
    for sy in (-1, 1):
        iplate(f"Card{sy}", "NewHeader", 1.2, 0.3, 0.01, T(0, -0.35 + sy * 0.012, z + 1.15) @ RZ(0 if sy < 0 else PI), K)
    box("CardClip", (1.24, 0.04, 0.03), (0, -0.35, z + 1.31), br, bevel=0.0)
    return _dims()


def book_stand_angled(M):
    """The angled book stand for the window or an aisle end: cast-iron side frames with pointed-arch tracery carrying a sloped
    crimson enamel back with four ledges of brass, twelve new books face out leaning on it, the LANTERNLIGHT BOOKS plate on its
    crest; 3.6 wide, 5.6 tall."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    W = 3.6
    side = [(-1.0, 0), (0.4, 0), (0.4, 0.3), (0.0, 5.2), (-0.25, 5.2), (-0.8, 0.3), (-1.0, 0.3)]
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.05)
        prism(f"Side{sx}", side, x, 0.1, ir, plane="YZ", bevel=0.015)
        tube(f"SideArch{sx}", [(x + sx * 0.055, y, z) for y, z in arch_xz(-0.55, 0.2, 1.0, 0.9, n=10)], 0.025, gl, square=True, poly=True)
        tube(f"SideArch2{sx}", [(x + sx * 0.055, y, z) for y, z in arch_xz(-0.32, 0.06, 3.0, 0.6, n=10)], 0.025, gl, square=True, poly=True)
        finial(f"Fin{sx}", x, -0.12, 5.2, gl, s=0.8)
    # sloped back, from (y=-0.75, z=0.3) to (y=-0.12, z=5.1)
    ya, za, yb, zb = -0.7, 0.4, -0.08, 5.1
    ang = math.atan2(zb - za, yb - ya)
    L = math.hypot(zb - za, yb - ya)
    box("Back", (W, 0.06, L), (0, (ya + yb) / 2 + 0.04, (za + zb) / 2), K["cen"], bevel=0.01, rot=(ang - PI / 2, 0, 0))
    box("Base", (W + 0.2, 1.1, 0.3), (0, -0.4, 0.15), ir, bevel=0.02)
    ledges = 4
    i = 0
    for k in range(ledges):
        t = (k + 0.08) / ledges
        y, z = ya + (yb - ya) * t, za + (zb - za) * t
        box(f"Ledge{k}", (W, 0.24, 0.05), (0, y - 0.12, z), br, bevel=0.01)
        box(f"Lip{k}", (W, 0.03, 0.1), (0, y - 0.235, z + 0.05), br, bevel=0.005)
        for c in range(3):
            x = -1.15 + c * 1.15
            stand_book(f"B{k}{c}", i, x, y - 0.02, z + 0.03, K, lean=math.degrees(PI / 2 - ang), w=0.8, d=1.17, t=0.15)
            i += 1
    crest = [(-1.3, 5.1), (1.3, 5.1)] + arch_xz(1.3, -1.3, 5.1, 0.55, n=10)[1:-1]
    prism("Crest", crest, -0.1, 0.1, ir, plane="XZ", bevel=0.01)
    iplate("Plate", "BookPlate", 2.2, 0.32, 0.02, T(0, -0.16, 5.28), K)
    return _dims()


def bargain_bin_cart(M):
    """The bargain barrow: a deep zinc bin on a cast-iron frame with two big spoked iron wheels at the front and turned legs and
    brass-gripped handles behind, heaped with jumbled second-hand books, the chalked BARGAINS 3 for 10 yen slate hung on its front;
    3.9 long."""
    K = kit(M)
    rnd = random.Random(4522)
    ir, br, zn = K["iron"], K["brassf"], K["zinc"]
    # the bin: a tapered tub, open top
    L, Dd, zb, zt = 2.6, 1.5, 1.2, 2.4
    lathe("Bin", [(0, zb), (0.7, zb), (0.78, zb + 0.05), (1.0, zt), (0.95, zt + 0.04), (0.93, zt), (0.72, zb + 0.08), (0, zb + 0.08)], K["galv"], seg=4)
    P.PARTS[-1].data.transform(Matrix.Diagonal((1.45 * math.sqrt(2), 0.82 * math.sqrt(2), 1, 1)) @ RZ(PI / 4))
    for z in (zb + 0.35, zt - 0.05):
        r = 0.72 + (z - zb) / (zt - zb) * 0.28
        for sy in (-1, 1):
            box(f"Band{z:.1f}{sy}", (2 * r * 1.45 + 0.04, 0.04, 0.08), (0, sy * (r * 0.82 + 0.02), z), ir, bevel=0.01)
    # frame, wheels, legs, handles
    for sy in (-1, 1):
        tube(f"Rail{sy}", [(-1.2, sy * 0.55, zb - 0.05), (1.3, sy * 0.55, zb - 0.05), (2.1, sy * 0.45, zb + 0.4)], 0.05, ir, square=True, poly=True)
        cyl(f"Grip{sy}", 0.06, 0.4, (2.25, sy * 0.43, zb + 0.5), br, rot=(0, PI / 2 - 0.45, 0), verts=12, bevel=0.015)
        x = -1.05
        hoop(f"Rim{sy}", (x, sy * 0.85, 0.75), 0.69, "Y", ir, thick=0.045)
        hoop(f"Tyre{sy}", (x, sy * 0.85, 0.75), 0.74, "Y", K["rubber"], thick=0.04)
        cyl(f"Hub{sy}", 0.14, 0.2, (x, sy * 0.85, 0.75), br, rot=(PI / 2, 0, 0), verts=14, bevel=0.02)
        for k in range(8):
            a = k * PI / 4
            tube(f"Spoke{sy}{k}", [(x, sy * 0.85, 0.75), (x + math.cos(a) * 0.68, sy * 0.85, 0.75 + math.sin(a) * 0.68)], 0.025, ir, poly=True)
        turned_leg(f"Leg{sy}", zb - 0.1, 0.08, ir, (1.15, sy * 0.5, 0))
    tube("Axle", [(-1.05, -0.95, 0.75), (-1.05, 0.95, 0.75)], 0.04, ir, poly=True)
    for sy in (-1, 1):
        tube(f"Strut{sy}", [(-1.05, sy * 0.6, 0.75), (-0.8, sy * 0.55, zb - 0.05)], 0.04, ir, poly=True)
    # the books, jumbled
    fits = B30._fits(1.25)
    k = 0
    for layer in range(3):
        for j in range(14 - layer * 3):
            d = rnd.choice(fits)
            x = rnd.uniform(-1.1 + layer * 0.15, 1.1 - layer * 0.15)
            y = rnd.uniform(-0.45 + layer * 0.08, 0.45 - layer * 0.08)
            z = zt - 0.55 + layer * 0.22 + rnd.uniform(-0.05, 0.05)
            B30.book(f"Bk{k}", d, d["h"] * 0.7, T(x, y, z) @ RZ(rnd.uniform(0, 2 * PI)) @ RX(rnd.uniform(-1.4, 1.4)) @ RY(rnd.uniform(-0.6, 0.6)) @
                     T(0, 0, -d["h"] / 2), K["atlas"])
            k += 1
    box("Fill", (2.3, 1.0, 0.5), (0, 0, zt - 0.6), K["kraft"], bevel=0.04)
    # the slate on hooks
    box("SlateFrame", (1.3, 0.06, 0.88), (0.1, -1.02, zt - 0.62), K["pinedk"], bevel=0.02)
    iplate("Slate", "Bargain", 1.18, 0.77, 0.02, T(0.1, -1.06, zt - 0.62), K, edge="slate")
    for sx in (-1, 1):
        tube(f"SlateHook{sx}", [(0.1 + sx * 0.5, -0.86, zt + 0.02), (0.1 + sx * 0.5, -1.0, zt - 0.05), (0.1 + sx * 0.5, -1.02, zt - 0.18)], 0.015, br)
    B43._ground(0)
    return _dims()


def staff_picks_easel(M):
    """The staff-picks easel: a cast-iron tripod easel 5.4 tall with a crescent finial, a gilt-framed card in the night shift's
    hand (STAFF PICKS: The Lantern Below, Ravens of Greyhallow, A Grammar of Shadows) and two of the books face out on its ledge,
    a crimson ribbon bookmark trailing."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    for sx in (-1, 1):
        tube(f"Leg{sx}", [(sx * 0.75, -0.3, 0.0), (sx * 0.2, 0.0, 5.0)], 0.04, ir, square=True, poly=True)
        sphere(f"Shoe{sx}", 0.06, (sx * 0.75, -0.3, 0.04), br, seg=8, rings=4)
    tube("BackLeg", [(0, 1.3, 0.0), (0, 0.06, 4.6)], 0.035, ir, square=True, poly=True)
    tube("Brace", [(-0.6, -0.24, 1.0), (0.6, -0.24, 1.0)], 0.03, ir, square=True, poly=True)
    tube("BackBrace", [(0, -0.22, 1.0), (0, 1.0, 1.0)], 0.02, ir, poly=True)
    box("Ledge", (1.6, 0.36, 0.06), (0, -0.33, 2.2), ir, bevel=0.012)
    box("LedgeLip", (1.6, 0.03, 0.1), (0, -0.5, 2.25), br, bevel=0.006)
    box("TopClamp", (0.5, 0.12, 0.1), (0, -0.05, 4.95), ir, bevel=0.015)
    lean = math.atan2(0.3, 5.0)
    s = _mark()
    box("Frame", (1.4, 0.08, 1.9), (0, 0, 0.95), gl, bevel=0.03)
    iplate("Card", "StaffPicks", 1.22, 1.69, 0.02, T(0, -0.045, 0.95), K, edge="parch")
    _quatrefoil("FrameFoil", 0, -0.05, 2.02, 0.12, gl)
    _xform(s, T(0, -0.15, 2.95) @ RX(-lean))
    for k, (x, i) in enumerate(((-0.42, 0), (0.42, 1))):
        stand_book(f"B{k}", i, x, -0.24, 2.23, K, lean=12, w=0.68, d=1.0, t=0.14)
    tube("Ribbon", [(-0.3, -0.36, 2.4), (-0.32, -0.42, 2.15), (-0.28, -0.45, 1.9)], 0.012, K["cen"], square=True)
    crescent_pts = [(math.cos(a) * 0.22, 5.25 + math.sin(a) * 0.22) for a in [i / 12 * 2 * PI for i in range(13)][3:11]]
    inner = [(0.07 + math.cos(a) * 0.17, 5.27 + math.sin(a) * 0.17) for a in [i / 12 * 2 * PI for i in range(13)][10:2:-1]]
    prism("Crescent", crescent_pts + inner, 0.0, 0.04, gl, plane="XZ", bevel=0.005)
    return _dims()


# ================================================================== the cafe

def bat_bracket(name, x, y, z, mat, s=1.0):
    """A cast-iron bat-wing bracket in the YZ plane, its foot on the counter front at y."""
    wing = [(0, 0), (0, 0.5), (-0.12, 0.42), (-0.2, 0.48), (-0.28, 0.36), (-0.38, 0.4), (-0.42, 0.22), (-0.3, 0.12), (-0.16, 0.06)]
    prism(name, [(y + u * s, z + w * s) for u, w in wing], x, 0.06, mat, plane="YZ", bevel=0.008)


def cafe_bar_counter(M):
    """The cafe's high bar, 6 long, 2.2 deep and 4.0 tall: a black marble top with a rounded nosing, crimson enamel gothic arcading
    on a cast-iron frame, a brass foot rail 0.7 up on cast-iron bat-wing brackets; on top a brass candlestick in a glass hurricane
    shade (Glass, the flame Glow), a sugar bowl, a stack of saucers and two cups; shelves of cups behind. Ends flush to line up."""
    K = kit(M)
    rnd = random.Random(4523)
    ir, br, gl, mb, lq = K["iron"], K["brassf"], K["gilt"], K["marble"], K["lacquer"]
    L, H = 6.0, 4.0
    counter_body("C", -L / 2, L / 2, K, H=H, goods=False, bays=4, top=False)
    box("Top", (L, D_C + 0.25, 0.2), (0, -0.12, H - 0.1), mb, bevel=0.06)
    cyl("Nosing", 0.1, L, (0, -1.25, H - 0.1), mb, rot=(0, PI / 2, 0), verts=12, bevel=0.0)
    # foot rail on bat brackets
    for k in range(4):
        x = -L / 2 + 0.4 + k * (L - 0.8) / 3
        bat_bracket(f"Bat{k}", x, -1.1, 0.45, ir, s=1.0)
        cyl(f"RailCollar{k}", 0.08, 0.14, (x, -1.45, 0.7), br, rot=(0, PI / 2, 0), verts=12, bevel=0.01)
    cyl("FootRail", 0.06, L, (0, -1.45, 0.7), br, rot=(0, PI / 2, 0), verts=16, bevel=0.0)
    # shelves behind with cups
    for z in (1.0, 2.2):
        box(f"BShelf{z}", (L - 0.1, 0.8, 0.06), (0, 0.6, z), lq, bevel=0.01)
        for j in range(10):
            x = -2.6 + j * 0.58
            lathe(f"BCup{z}{j}", [(0, 0), (0.08, 0), (0.15, 0.1), (0.17, 0.24), (0.15, 0.24), (0.13, 0.11), (0, 0.04)], K["china"], seg=14,
                  loc=(x, 0.6, z + 0.03))
    # on top
    z = H
    cx, cy = -1.6, -0.45
    lathe("Stick", [(0, 0), (0.2, 0), (0.2, 0.04), (0.09, 0.1), (0.05, 0.4), (0.1, 0.48), (0.12, 0.52), (0.04, 0.55), (0, 0.55)], br, seg=18,
          loc=(cx, cy, z))
    candle("Cdl", cx, cy, z + 0.5, 0.45, 0.06, K, glow=True)
    for k, (x, y) in enumerate(((0.4, -0.5), (0.9, -0.35))):
        cyl(f"Saucer{k}", 0.2, 0.03, (x, y, z + 0.015), K["china"], verts=18, bevel=0.01)
        lathe(f"Cup{k}", [(0, 0), (0.07, 0), (0.14, 0.09), (0.16, 0.22), (0.14, 0.22), (0.12, 0.1), (0, 0.04)], K["china"], seg=16, loc=(x, y, z + 0.03))
        cyl(f"Coffee{k}", 0.135, 0.01, (x, y, z + 0.22), K["tea"], verts=14, bevel=0.0)
        hoop(f"CupH{k}", (x + 0.17, y, z + 0.15), 0.05, "Y", K["china"], thick=0.015)
    for k in range(6):
        cyl(f"Stack{k}", 0.2, 0.03, (1.8, -0.2, z + 0.015 + k * 0.034), K["china"], verts=18, bevel=0.01)
    lathe("Sugar", [(0, 0), (0.1, 0), (0.18, 0.08), (0.2, 0.2), (0.16, 0.26), (0.0, 0.26)], K["silver"], seg=16, loc=(2.4, -0.5, z))
    lathe("SugarLid", [(0, 0), (0.15, 0), (0.12, 0.06), (0.03, 0.08), (0.04, 0.12), (0, 0.13)], K["silver"], seg=16, loc=(2.4, -0.5, z + 0.26))
    set_group("Glass")
    lathe("Hurricane", [(0, 0), (0.18, 0.0), (0.24, 0.2), (0.26, 0.5), (0.2, 0.85), (0.19, 1.0), (0, 1.0)], K["glass"], seg=24, loc=(cx, cy, z + 0.55))
    set_group("Main")
    return _dims()


def bar_stool(M):
    """A cafe bar stool, seat 3.0: a fluted cast-iron pedestal on four clawed feet, a quatrefoil foot ring at 1.1, a brass swivel
    collar and a buttoned crimson leather seat with a low curved iron back hoop."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    for k in range(4):
        a = k * PI / 2 + PI / 4
        s = _mark()
        prism(f"Claw{k}", [(0.0, 0.0), (0.75, 0.0), (0.82, 0.06), (0.72, 0.1), (0.4, 0.22), (0.15, 0.55), (0.0, 0.6)], 0, 0.1, ir, plane="XZ", bevel=0.012)
        sphere(f"Ball{k}", 0.07, (0.78, 0, 0.07), br, seg=8, rings=5)
        _xform(s, RZ(a))
    lathe("Pedestal", [(0, 0.3), (0.16, 0.3), (0.12, 0.5), (0.09, 0.6), (0.08, 2.5), (0.12, 2.6), (0, 2.6)], ir, seg=16, flute=(8, 0.12))
    lathe("Collar", [(0, 2.55), (0.16, 2.55), (0.18, 2.62), (0.16, 2.7), (0, 2.7)], br, seg=18)
    lathe("SeatPan", [(0, 2.7), (0.42, 2.72), (0.46, 2.78), (0, 2.78)], ir, seg=24)
    lathe("Seat", [(0, 2.78), (0.5, 2.78), (0.54, 2.86), (0.52, 2.96), (0.4, 3.02), (0, 3.04)], K["leather"], seg=28)
    for k in range(5):
        a = k * 2 * PI / 5
        sphere(f"Button{k}", 0.025, (math.cos(a) * 0.25, math.sin(a) * 0.25, 3.02), K["leather"], seg=6, rings=3)
    sphere("ButtonC", 0.025, (0, 0, 3.04), K["leather"], seg=6, rings=3)
    hoop("SeatBead", (0, 0, 2.86), 0.54, "Z", br, thick=0.015)
    # the foot ring and its spokes
    hoop("FootRing", (0, 0, 1.1), 0.45, "Z", br, thick=0.03)
    for k in range(4):
        a = k * PI / 2
        tube(f"Spoke{k}", [(0, 0, 1.1), (math.cos(a) * 0.44, math.sin(a) * 0.44, 1.1)], 0.025, ir, poly=True)
        s = _mark()
        _quatrefoil(f"Foil{k}", 0, 0, 0, 0.12, gl)
        _xform(s, T(math.cos(a + PI / 4) * 0.3, math.sin(a + PI / 4) * 0.3, 1.1) @ RZ(a + PI / 4) @ RX(PI / 2))
    # low back hoop (to the rear, +Y)
    pts = []
    for i in range(13):
        a = PI * 0.15 + i / 12 * PI * 0.7
        pts.append((math.cos(a) * 0.47, math.sin(a) * 0.47, 3.45 - 0.05 * math.sin((i / 12) * PI) * 0))
    tube("BackHoop", pts, 0.035, ir, poly=True)
    for k, i in enumerate((0, 6, 12)):
        x, y, _ = pts[i]
        tube(f"BackPost{k}", [(x * 0.95, y * 0.95, 2.9), (x, y, 3.45)], 0.025, ir, poly=True)
    for i in (0, 12):
        sphere(f"BackKnob{i}", 0.04, pts[i], br, seg=8, rings=4)
    return _dims()


def cafe_back_shelf(M):
    """The cafe's back bar (wall piece): 6 wide, 7.7 tall. A lacquered cupboard with crimson gothic panels under a black marble top
    (3.4) carrying big labelled jars (COFFEE, CHOCOLATE, LOOSE TEA, SUGAR, COCOA, BISCOTTI); above it a black-silvered mirror
    (Mirror) between iron pilasters behind two shelves of cups and jars, mugs hung on brass hooks, and the gilt-scripted THE WICK
    & KETTLE board on the cornice."""
    K = kit(M)
    rnd = random.Random(4524)
    ir, br, gl, lq, mb = K["iron"], K["brassf"], K["gilt"], K["lacquer"], K["marble"]
    W = 6.0
    box("Cup", (W, 1.0, 3.2), (0, -0.5, 1.6), lq, bevel=0.03)
    for k, x in enumerate((-2.0, 0.0, 2.0)):
        gothic_panel(f"Pan{k}", 1.7, 2.4, K, T(x, -1.005, 0.4))
        box(f"PanKnob{k}", (0.06, 0.06, 0.25), (x + 0.75, -1.05, 1.7), br, bevel=0.01)
    box("Kick", (W + 0.04, 0.03, 0.18), (0, -1.02, 0.1), br, bevel=0.006)
    box("Top", (W + 0.1, 1.15, 0.18), (0, -0.575, 3.29), mb, bevel=0.03)
    for k in range(6):
        x = -2.5 + k * 1.0
        r, h = 0.26, 0.85
        lathe(f"BigJar{k}", [(0, 0), (r, 0), (r + 0.02, 0.05), (r + 0.02, h * 0.85), (r * 0.7, h * 0.95), (r * 0.7, h), (0, h)], K["china"], seg=20,
              loc=(x, -0.55, 3.38))
        lathe(f"BigLid{k}", [(0, 0), (r * 0.78, 0), (r * 0.8, 0.05), (r * 0.5, 0.12), (r * 0.15, 0.15), (r * 0.15, 0.22), (0, 0.24)], br, seg=18,
              loc=(x, -0.55, 3.38 + h))
        wrap(f"BigLab{k}", f"CafeJar_{k}", r + 0.025, 0.42, 0.32, 0.5, T(x, -0.55, 3.38), K, n=8)
    # mirror bay
    z0, z1 = 3.5, 7.0
    for x in (-W / 2 + 0.15, W / 2 - 0.15):
        box(f"Pilaster{x:.1f}", (0.3, 0.3, z1 - z0), (x, -0.15, (z0 + z1) / 2), ir, bevel=0.02)
        lathe(f"Cap{x:.1f}", [(0, 0), (0.2, 0), (0.24, 0.08), (0.2, 0.16), (0, 0.16)], gl, seg=4, loc=(x, -0.15, z1 - 0.16))
    box("MirrorFrame", (W - 0.6, 0.08, z1 - z0), (0, -0.04, (z0 + z1) / 2), gl, bevel=0.02)
    for k, z in enumerate((4.5, 5.7)):
        box(f"Shelf{k}", (W - 0.6, 0.55, 0.06), (0, -0.33, z), lq, bevel=0.01)
        box(f"ShelfLip{k}", (W - 0.6, 0.03, 0.08), (0, -0.6, z + 0.02), br, bevel=0.005)
        for sx in (-1, 1):
            bat_bracket(f"ShelfBat{k}{sx}", sx * 2.0, -0.08, z - 0.48, ir, s=0.9)
        for j in range(8):
            x = -2.4 + j * 0.68 + rnd.uniform(-0.05, 0.05)
            if (j + k) % 3 == 0:
                jar(f"SJ{k}{j}", x, -0.33, z + 0.03, 0.15, 0.5, rnd.choice(("tea", "liq_a", "beans")), K, label=f"CafeJar_{(j + k) % 6}")
            else:
                cyl(f"SSaucer{k}{j}", 0.17, 0.03, (x, -0.33, z + 0.045), K["china"], verts=16, bevel=0.008)
                lathe(f"SCup{k}{j}", [(0, 0), (0.07, 0), (0.13, 0.08), (0.15, 0.2), (0.13, 0.2), (0.11, 0.09), (0, 0.03)], K["china"], seg=14,
                      loc=(x, -0.33, z + 0.06))
    # mugs on hooks under the upper shelf
    for j in range(7):
        x = -2.1 + j * 0.7
        tube(f"Hook{j}", [(x, -0.5, 5.7), (x, -0.5, 5.55), (x, -0.42, 5.5), (x, -0.36, 5.56)], 0.012, br)
        s = _mark()
        lathe(f"Mug{j}", [(0, 0), (0.12, 0), (0.13, 0.3), (0.12, 0.3), (0.11, 0.03), (0, 0.03)], K["china"] if j % 2 else K["cen"], seg=14)
        hoop(f"MugH{j}", (0.14, 0, 0.16), 0.07, "Y", K["china"] if j % 2 else K["cen"], thick=0.018)
        _xform(s, T(x - 0.14, -0.42, 5.5) @ RY(PI) @ T(-0.14, 0, -0.08) @ RY(0.0))
    box("Cornice", (W + 0.3, 0.6, 0.35), (0, -0.3, z1 + 0.175), lq, bevel=0.03)
    box("CorniceBead", (W + 0.32, 0.03, 0.05), (0, -0.61, z1 + 0.03), gl, bevel=0.01)
    iplate("Name", "CafeName", 3.8, 0.81, 0.03, T(0, -0.62, z1 + 0.72), K)
    box("NameBoard", (4.0, 0.08, 0.95), (0, -0.55, z1 + 0.72), lq, bevel=0.02)
    for x in (-2.3, 2.3):
        finial(f"Fin{x}", x, -0.3, z1 + 0.35, gl, s=0.8)
    set_group("Mirror")
    box("Mirror", (W - 0.8, 0.02, z1 - z0 - 0.2), (0, -0.09, (z0 + z1) / 2), K["mirror"], bevel=0.0)
    set_group("Main")
    return _dims()


# ================================================================== signs and fittings

def open_closed_sign(M):
    """The door sign (wall piece, for the inside of a shop door or its glass): a brass hook plate with a crescent finial and two
    fine chains holding a double-sided enamel sign, OPEN (do come in) in crimson on the front, CLOSED (back at dusk) in ink on the
    back; 1.3 wide, 1.5 tall. Turn it round to change it."""
    K = kit(M)
    br, gl = K["brassf"], K["gilt"]
    W, H = 1.3, 0.75
    y = -0.12
    shape = [(-W / 2 + 0.08, 0), (W / 2 - 0.08, 0), (W / 2, 0.08), (W / 2, H - 0.08), (W / 2 - 0.08, H), (-W / 2 + 0.08, H), (-W / 2, H - 0.08),
             (-W / 2, 0.08)]
    ipoly("Front", "Open", [(u, w - H / 2) for u, w in shape], 0.025, T(0, y - 0.0125, H / 2), K, edge="crimson")
    ipoly("Back", "Closed", [(u, w - H / 2) for u, w in shape], 0.025, T(0, y + 0.0125, H / 2) @ RZ(PI), K, edge="ink")
    box("HookPlate", (0.36, 0.03, 0.14), (0, -0.015, 1.36), br, bevel=0.01)
    cyl("Screw", 0.02, 0.02, (0, -0.035, 1.36), gl, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    tube("Hook", [(0, -0.03, 1.3), (0, -0.12, 1.26), (0, -0.14, 1.32)], 0.015, br)
    prism("Crescent", [(math.cos(a) * 0.09, 1.48 + math.sin(a) * 0.09) for a in [i / 10 * 2 * PI for i in range(2, 9)]] +
          [(0.03 + math.cos(a) * 0.07, 1.49 + math.sin(a) * 0.07) for a in [i / 10 * 2 * PI for i in range(8, 1, -1)]], -0.02, 0.02, gl, plane="XZ")
    for sx in (-1, 1):
        hoop(f"Eye{sx}", (sx * 0.45, y, H + 0.04), 0.03, "Y", br, thick=0.008)
        B30.chain(f"Ch{sx}", [(sx * 0.45, y, H + 0.07), (0, -0.13, 1.25)], br, r=0.025, thick=0.006)
    return _dims()


def shop_sign_interior(M):
    """The indoor hanging shop sign (ceiling piece): a double-sided crimson board 5.0 wide with MORROW & VANE, Purveyors of
    Sundries, in gilt, in a cast-iron frame with a pierced cresting and crescent finials, hung on two chains from an iron rod and
    ceiling roses. The pivot is at the board's bottom; the roses' tops are 4.6 above it."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    W, H = 5.0, 1.19
    for sy in (-1, 1):
        iplate(f"Board{sy}", "ShopSign", W, H, 0.04, T(0, sy * 0.03, H / 2 + 0.1) @ RZ(0 if sy < 0 else PI), K, edge="crimson")
    for z in (0.05, H + 0.15):
        box(f"Rail{z:.1f}", (W + 0.2, 0.14, 0.1), (0, 0, z), ir, bevel=0.02)
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.1, 0.14, H + 0.2), (sx * (W / 2 + 0.05), 0, H / 2 + 0.1), ir, bevel=0.02)
        finial(f"Fin{sx}", sx * (W / 2 + 0.05), 0, H + 0.2, gl, s=0.7)
        sphere(f"Drop{sx}", 0.07, (sx * (W / 2 + 0.05), 0, 0.0 + 0.07), gl, seg=8, rings=4)
    # cresting: a row of pointed arches with a crescent at the middle
    n = 8
    for k in range(n):
        x0 = -W / 2 + k * W / n
        tube(f"Crest{k}", [(x, 0, z) for x, z in arch_xz(x0 + 0.05, x0 + W / n - 0.05, H + 0.2, 0.3, n=8)], 0.02, ir, square=True, poly=True)
    cr = [(math.cos(a) * 0.22, H + 0.6 + math.sin(a) * 0.22) for a in [i / 12 * 2 * PI for i in range(-2, 9)]]
    cr += [(0.08 + math.cos(a) * 0.17, H + 0.62 + math.sin(a) * 0.17) for a in [i / 12 * 2 * PI for i in range(8, -3, -1)]]
    prism("Crescent", cr, 0, 0.04, gl, plane="XZ", bevel=0.005)
    zr = H + 1.2
    tube("Rod", [(-W / 2 + 0.3, 0, zr), (W / 2 - 0.3, 0, zr)], 0.04, ir, poly=True)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.5)
        tube(f"Strap{sx}", [(x, 0, H + 0.2), (x, 0, zr)], 0.02, ir, poly=True)
        B30.chain(f"Ch{sx}", [(x, 0, zr), (x, 0, zr + 2.0)], ir, r=0.05, thick=0.012)
        lathe(f"Rose{sx}", [(0, 0), (0.16, 0), (0.25, 0.08), (0.28, 0.14), (0, 0.14)], br, seg=18, loc=(x, 0, zr + 2.06))
        hoop(f"RoseEye{sx}", (x, 0, zr + 2.03), 0.05, "X", br, thick=0.012)
    return _dims()


def price_tag_rail(M):
    """A brass ticket rail for a shelf edge or counter front (wall piece): a 4-long brass ticket moulding with six clip-in bone and
    enamel price tickets (3 to 40 yen), and three paper tags on twine hung from little hooks under it; 0.8 tall."""
    K = kit(M)
    br, gl = K["brassf"], K["gilt"]
    L = 4.0
    box("Back", (L, 0.03, 0.34), (0, -0.015, 0.55), br, bevel=0.006)
    box("LipLo", (L, 0.06, 0.04), (0, -0.05, 0.4), br, bevel=0.008)
    box("LipHi", (L, 0.06, 0.04), (0, -0.05, 0.7), br, bevel=0.008)
    for sx in (-1, 1):
        box(f"End{sx}", (0.05, 0.07, 0.36), (sx * L / 2, -0.04, 0.55), gl, bevel=0.01)
        for z in (0.45, 0.65):
            cyl(f"Screw{sx}{z}", 0.02, 0.02, (sx * (L / 2 - 0.1), -0.04, z), gl, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    for k in range(6):
        x = -1.65 + k * 0.66
        iplate(f"Ticket{k}", f"Ticket_{(k * 3) % 8}", 0.42, 0.26, 0.012, T(x, -0.05, 0.55), K, edge="bone")
    for k, x in enumerate((-1.2, 0.2, 1.4)):
        tube(f"Hook{k}", [(x, -0.06, 0.38), (x, -0.1, 0.32), (x, -0.08, 0.28)], 0.008, br)
        tube(f"Twine{k}", [(x, -0.09, 0.3), (x + 0.02, -0.1, 0.15)], 0.005, K["twine"], poly=True)
        s = _mark()
        prism(f"Tag{k}", [(-0.09, 0), (0.09, 0), (0.09, 0.2), (0.05, 0.24), (-0.05, 0.24), (-0.09, 0.2)], 0, 0.01, K["kraft"], plane="XZ")
        cyl(f"Hole{k}", 0.012, 0.012, (0, 0, 0.2), K["ink"], rot=(PI / 2, 0, 0), verts=6, bevel=0.0)
        iplate(f"TagP{k}", f"Ticket_{(k * 5 + 1) % 8}", 0.15, 0.09, 0.003, T(0, -0.006, 0.09), K, edge="paper")
        _xform(s, T(x + 0.02, -0.1, -0.08) @ RZ(0.2 * (k - 1)))
    return _dims()


def door_bell_bracket(M):
    """The shop door's bell (wall piece, over the inside of the door): a cast-iron back plate in a pointed-arch outline, an S-scroll
    arm reaching out 1.1, and a brass bell with its clapper hung on a coiled steel spring so it jangles when the door knocks it;
    1.6 tall."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    plate = [(-0.18, 0.7), (0.18, 0.7)] + arch_xz(0.18, -0.18, 1.3, 0.3, n=8)[1:-1]
    prism("Plate", plate, -0.02, 0.04, ir, plane="XZ", bevel=0.008)
    for z in (0.82, 1.3):
        cyl(f"Screw{z}", 0.025, 0.02, (0, -0.045, z), br, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    tube("Scroll", [(0, -0.05, 1.05), (0, -0.35, 1.15), (0, -0.7, 1.05), (0, -0.95, 1.12), (0, -1.1, 1.3), (0, -1.0, 1.42), (0, -0.9, 1.33)], 0.03, ir)
    tube("Brace", [(0, -0.05, 0.78), (0, -0.4, 0.85), (0, -0.62, 1.07)], 0.022, ir)
    hoop("Curl", (0, -0.25, 0.9), 0.08, "X", ir, thick=0.016)
    # the spring: a coil hanging from the arm's end
    pts = []
    turns, top, bot, r = 7, 1.08, 0.68, 0.05
    for i in range(turns * 10 + 1):
        t = i / 10 * 2 * PI
        pts.append((math.cos(t) * r, -1.05 + math.sin(t) * r, top - (top - bot) * i / (turns * 10)))
    tube("Spring", pts, 0.008, K["steel"], poly=True)
    tube("SpringTop", [(0.05, -1.05, top), (0, -1.05, top + 0.05), (0, -1.05, 1.12)], 0.01, K["steel"], poly=True)
    lathe("Bell", [(0, 0.66), (0.04, 0.66), (0.08, 0.62), (0.12, 0.5), (0.15, 0.38), (0.21, 0.3), (0.22, 0.28), (0.2, 0.29), (0.14, 0.36),
                   (0.1, 0.48), (0.06, 0.6), (0, 0.63)], br, seg=24, loc=(0, -1.05, 0.0))
    hoop("BellLip", (0, -1.05, 0.29), 0.215, "Z", gl, thick=0.012)
    tube("Clapper", [(0, -1.05, 0.62), (0.02, -1.05, 0.36)], 0.008, ir, poly=True)
    sphere("ClapperBall", 0.04, (0.02, -1.05, 0.34), ir, seg=8, rings=4)
    B43._ground(0)
    return _dims()


def shop_stool(M):
    """The shopkeeper's screw stool, seat 2.4 (it winds up and down): a cast-iron tripod on claw-and-ball feet, an exposed brass
    screw column with its threads and a lock wheel, a round crimson leather seat with a brass rim, and a foot ring."""
    K = kit(M)
    ir, br, gl = K["iron"], K["brassf"], K["gilt"]
    for k in range(3):
        a = k * 2 * PI / 3
        s = _mark()
        tube(f"Leg{k}", [(0.7, 0, 0.1), (0.45, 0, 0.6), (0.2, 0, 1.3)], 0.045, ir, square=True)
        sphere(f"Ball{k}", 0.08, (0.72, 0, 0.08), br, seg=8, rings=5)
        prism(f"Claw{k}", [(0.6, 0.02), (0.82, 0.02), (0.8, 0.12), (0.66, 0.2)], 0, 0.06, ir, plane="XZ", bevel=0.006)
        _xform(s, RZ(a))
    lathe("Hub", [(0, 1.2), (0.22, 1.2), (0.2, 1.42), (0.12, 1.46), (0, 1.46)], ir, seg=16)
    hoop("FootRing", (0, 0, 0.6), 0.48, "Z", br, thick=0.028)
    cyl("Screw", 0.075, 0.9, (0, 0, 1.85), br, verts=14, bevel=0.0)
    pts = []
    for i in range(9 * 10 + 1):
        t = i / 10 * 2 * PI
        pts.append((math.cos(t) * 0.085, math.sin(t) * 0.085, 1.45 + 0.8 * i / 90))
    tube("Thread", pts, 0.012, br, poly=True)
    cyl("LockWheel", 0.16, 0.05, (0, 0, 1.52), br, verts=16, bevel=0.01)
    for k in range(6):
        a = k * PI / 3
        sphere(f"Knurl{k}", 0.025, (math.cos(a) * 0.16, math.sin(a) * 0.16, 1.52), br, seg=6, rings=3)
    lathe("Plate", [(0, 2.25), (0.4, 2.25), (0.44, 2.3), (0, 2.3)], ir, seg=24)
    lathe("Seat", [(0, 2.3), (0.46, 2.3), (0.48, 2.36), (0.44, 2.42), (0.3, 2.46), (0, 2.47)], K["leather"], seg=28)
    hoop("Rim", (0, 0, 2.33), 0.47, "Z", br, thick=0.018)
    sphere("Button", 0.03, (0, 0, 2.47), br, seg=8, rings=4)
    return _dims()


def hat_umbrella_stand(M):
    """The hat and umbrella stand by the door (wall piece, against the wall): a cast-iron trough with pierced quatrefoil front and
    three umbrella loops over a zinc drip tray; a back panel rising to a pointed arch with a raven on top, three brass-knobbed hat
    pegs, a bowler and a tall hat hung up; two furled black umbrellas with crook handles and a silver-topped cane in it; 6.3 tall."""
    K = kit(M)
    ir, br, gl, zn = K["iron"], K["brassf"], K["gilt"], K["zinc"]
    W = 2.4
    box("Tray", (W, 0.85, 0.12), (0, -0.45, 0.06), zn, bevel=0.03)
    box("TrayIn", (W - 0.16, 0.7, 0.04), (0, -0.45, 0.11), K["ink"], bevel=0.0)
    for sx in (-1, 1):
        turned_leg(f"Foot{sx}", 0.18, 0.06, ir, (sx * (W / 2 - 0.1), -0.82, 0))
    # trough front and sides
    box("TroughFront", (W, 0.06, 0.7), (0, -0.84, 0.55), ir, bevel=0.012)
    for k in range(5):
        _quatrefoil(f"TFoil{k}", -0.96 + k * 0.48, -0.88, 0.55, 0.2, gl)
    for sx in (-1, 1):
        box(f"TroughSide{sx}", (0.06, 0.85, 0.7), (sx * (W / 2 - 0.03), -0.45, 0.55), ir, bevel=0.012)
    # the back panel: two stiles, a pointed arch and a raven
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.12, 0.08, 5.2), (sx * (W / 2 - 0.06), -0.04, 2.6), ir, bevel=0.015)
    tube("Arch", [(-W / 2 + 0.06, -0.04, 5.1)] + [(x, -0.04, z) for x, z in arch_xz(-W / 2 + 0.06, W / 2 - 0.06, 5.1, 0.9, n=12)] +
         [(W / 2 - 0.06, -0.04, 5.1)], 0.05, ir, square=True, poly=True)
    tube("InnerArch", [(x, -0.06, z) for x, z in arch_xz(-0.7, 0.7, 4.2, 0.9, n=10)], 0.03, gl, square=True, poly=True)
    for z in (1.0, 2.2, 3.6):
        box(f"Bar{z}", (W - 0.1, 0.06, 0.08), (0, -0.04, z), ir, bevel=0.01)
    _quatrefoil("ArchFoil", 0, -0.08, 4.75, 0.28, gl)
    tube("Spine", [(0, -0.04, 1.0), (0, -0.04, 4.2)], 0.025, ir, square=True, poly=True)
    rv = [(-0.5, 0.1), (-0.3, 0.0), (-0.15, -0.12), (0.0, -0.2), (0.12, -0.32), (0.24, -0.34), (0.34, -0.3), (0.46, -0.3), (0.34, -0.24),
          (0.3, -0.14), (0.22, 0.04), (0.1, 0.18), (0.0, 0.24), (0.04, 0.4), (-0.04, 0.4), (-0.06, 0.26), (-0.2, 0.24), (-0.5, 0.3), (-0.62, 0.32),
          (-0.44, 0.18)]
    prism("Raven", [(u * 0.7, 6.3 - (w + 0.4) * 0.7) for u, w in rv], -0.04, 0.08, K["ink"], plane="XZ", bevel=0.01)
    # hat pegs
    for k, x in enumerate((-0.8, 0.0, 0.8)):
        tube(f"Peg{k}", [(x, -0.05, 3.9), (x, -0.4, 3.95), (x, -0.5, 4.08)], 0.035, ir)
        sphere(f"PegKnob{k}", 0.06, (x, -0.5, 4.1), br, seg=10, rings=5)
    # umbrella loops
    for k, x in enumerate((-0.7, 0.0, 0.7)):
        hoop(f"Loop{k}", (x, -0.42, 2.2), 0.17, "Z", br, thick=0.02)
        tube(f"LoopArm{k}", [(x, -0.04, 2.2), (x, -0.25, 2.2)], 0.02, br, poly=True)
    # the umbrellas and the cane
    for k, (x, lean) in enumerate(((-0.7, 0.08), (0.0, -0.05))):
        s = _mark()
        lathe(f"Brolly{k}", [(0, 0), (0.02, 0.0), (0.06, 0.15), (0.12, 0.9), (0.14, 1.6), (0.11, 2.2), (0.04, 2.45), (0.02, 2.55), (0, 2.55)], K["black"],
              seg=8, jitter=(0.06, 4440 + k))
        cyl(f"Shaft{k}", 0.02, 0.5, (0, 0, 2.75), K["steel"], verts=6, bevel=0.0)
        tube(f"Crook{k}", [(0, 0, 2.95), (0, 0, 3.15), (0.1, 0, 3.3), (0.22, 0, 3.25), (0.24, 0, 3.12)], 0.035, K["ebony"] if k else K["cen"])
        hoop(f"Strap{k}", (0, 0, 1.9), 0.125, "Z", K["black"], thick=0.015)
        _xform(s, T(x, -0.42, 0.13) @ RY(lean) @ RZ(0.6 * k))
    s = _mark()
    cyl("Cane", 0.03, 3.0, (0, 0, 1.5), K["ebony"], verts=8, bevel=0.0)
    sphere("CaneTop", 0.07, (0, 0, 3.03), K["silver"], seg=10, rings=5)
    cyl("Ferrule", 0.032, 0.1, (0, 0, 0.05), br, verts=8, bevel=0.0)
    _xform(s, T(0.72, -0.42, 0.13) @ RY(-0.08))
    # the hats
    s = _mark()
    lathe("Bowler", [(0, 0), (0.42, 0), (0.44, 0.03), (0.3, 0.05), (0.31, 0.2), (0.26, 0.32), (0.14, 0.38), (0, 0.39)], K["felthat"], seg=24, scale=(1, 0.88))
    hoop("BowlerBand", (0, 0, 0.08), 0.305, "Z", K["silk"], thick=0.02)
    _xform(s, T(-0.8, -0.48, 3.98) @ RX(-0.3))
    s = _mark()
    lathe("TopHat", [(0, 0), (0.45, 0), (0.46, 0.03), (0.3, 0.05), (0.28, 0.12), (0.3, 0.75), (0.32, 0.8), (0, 0.8)], K["felthat"], seg=24, scale=(1, 0.88))
    hoop("TopBand", (0, 0, 0.15), 0.29, "Z", K["silk"], thick=0.03)
    _xform(s, T(0.8, -0.5, 3.98) @ RX(-0.3))
    return _dims()


BUILDERS = {
    "ShopCounter": shop_counter,
    "ShopCounterCorner": shop_counter_corner,
    "ShopCounterEnd": shop_counter_end,
    "CashRegister": cash_register,
    "ShopScales": shop_scales,
    "CounterBell": counter_bell,
    "WrapStand": wrap_stand,
    "DisplayCase": display_case,
    "GlassCabinetTall": glass_cabinet_tall,
    "WallShelfStocked": wall_shelf_stocked,
    "IslandShelf": island_shelf,
    "ApothecaryDrawers": apothecary_drawers,
    "SweetJarShelf": sweet_jar_shelf,
    "PostcardSpinner": postcard_spinner,
    "StockSacks": stock_sacks,
    "StockCrates": stock_crates,
    "BookshopCounter": bookshop_counter,
    "NewReleasesTable": new_releases_table,
    "BookStandAngled": book_stand_angled,
    "BargainBinCart": bargain_bin_cart,
    "StaffPicksEasel": staff_picks_easel,
    "CafeBarCounter": cafe_bar_counter,
    "BarStool": bar_stool,
    "CafeBackShelf": cafe_back_shelf,
    "OpenClosedSign": open_closed_sign,
    "ShopSignInterior": shop_sign_interior,
    "PriceTagRail": price_tag_rail,
    "DoorBellBracket": door_bell_bracket,
    "ShopStool": shop_stool,
    "HatUmbrellaStand": hat_umbrella_stand,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update(PAD)
B24.SMALL.update(SMALLP)
