"""Props batch 23 (2026-11-05): the window kit for nh_props.py, on theme with the Institution: candlelit gothic, soot-dark
stone, cast iron and lead, brass, gilt and crimson enamel, warm light behind the glass. Little wood (only the boards).

  LancetWindow     a tall single lancet: chamfered soot-stone jambs, square leaded quarries, iron saddle bars, a hood mould
                   on carved label stops, a weathered sill, a candle on the inner sill
  TwinLancet       two lancets under one pointed arch, plate tracery pierced by a quatrefoil, a shafted mullion,
                   diamond leading
  TripletLancet    three stepped lancets (the middle one tallest) with shafts between, square quarries, a shared sill
  TraceryWindow    a great four-light window: mullions, two sub-arches, a cusped head circle and spandrel foils in
                   stone bar tracery; stained glass (candle, moon, key and bell medallions in crimson, gold and blue)
  RoseWindow       a wheel window: twelve petals round a cusped hub, foils between the petal heads, a moulded ring of
                   voussoirs; stained glass
  Oculus           a small round window: moulded voussoirs with four keystones, an iron quatrefoil grille
  DiamondPaneArch  a pointed iron casement: two leaves and a head light, diamond leading, brass stays and handles
  SashWindow       a classroom sash under a segmental voussoir head: crimson enamel sashes, iron glazing bars, Y-tracery
                   in the upper sash, a brass lock and lifts
  GothicBay        a canted bay on a traceried plinth: three faces of trefoil-headed lights, corner shafts, a
                   crenellated parapet; a crimson window seat and a candle inside
  LucarneDormer    a stone dormer: twin trefoil-headed lights, pinnacled piers, a crocketed gable with a foil and a
                   finial, a slate roof with iron cresting running back
  ArrowSlit        a cross loop with round oillets through a coursed block of soot stone (a slice of warm light behind)
  Fanlight         a half-round fanlight over a door: an iron sunburst with a petalled hub, voussoirs and a crimson and
                   gilt keystone shield, on a stone transom
  BasementGrate    a low segmental window in a rusticated plinth: heavy iron bars and rivetted flat bars, rust stains
  StainedLancet    a lancet of stained glass (a candle under a crescent moon on starry blue, a gilt trefoil in the head),
                   moulded jambs, iron saddle bars, a pricket candle on the sill
  BrokenWindow     a leaded lancet smashed through: shards left in the cames, bent leads, two boards nailed across,
                   glass on the sill
  ShutteredWindow  closed cast-iron shutters in crimson enamel: louvres below, a pierced crescent moon above, strap
                   hinges, a drop bar and a brass ring pull

  Regular clear windows (plain glass, no lead):
  PlainSash        a two-over-two sash: black iron sashes, a stone architrave with a flat jointed lintel and keystone
  CrossWindow      a stone mullion and transom dividing four lights in iron casements, a square hood mould
  PictureWindow    one wide clear pane in a slim iron frame, a long sill on brackets
  RoundArchWindow  a semicircular head of voussoirs with a keystone, an iron fan in the head, two lights below
  SquareWindow     a small four-pane window in a chamfered frame, for corridors and stair landings
  HalfRoundWindow  a half-circle lunette: moulded voussoirs and a keystone, two stone mullions, three clear lights

  The conservatory:
  ConservatoryDome a walk-in gothic glass crown, 19.2 across and about 25 high: an octagonal hall of tall two-light iron
                   lancets (roundels, cusped heads, crimson enamel spandrels) on a soot-stone base, a crimson frieze with gilt
                   bosses, a steep faceted glass crown dome on eight crocketed iron ribs, an openwork iron spire with a gilt
                   crescent moon; round it eight soot-stone piers with crocketed pinnacles, each joined to the hall by a pierced
                   flying buttress, and a crown band of iron tracery with gilt quatrefoils between them; a crocketed gable
                   with a rose over the doorway; a hanging iron corona of candles inside.
                   Pieces: Main, Spires, Crown, Drum, Dome (baked), Wall and Floor (tiled castle stone), Glass (Roblox Glass,
                   no maps), Glow
  ConservatoryBeds the planting for its floor: a round bed with an iron obelisk trellis of climbing crimson roses, ferns
                   and broad leaves, four iron urns of ferns at the diagonals
  TraceryWindowClear, RoseWindowClear   the tracery and rose windows with clear glass and the lit room behind

Pieces: Main (baked), Glass (clear panes: Roblox Glass), Room (the lit room behind clear glass: a front-projected warm
amber image shared by every window, art/props/textures/WindowRoom_canvas.png; delete it for a see-through opening),
Stained (the stained glass: its own 2048 painting from stained_glass.py, front-projected, glowing through an emissive
mask in Roblox), Glow (a few small flames).

Front faces -Y, Z is up, the origin is at the bottom centre; the wall pieces have their backs flat at y = 0, the builder's
wall face (LucarneDormer's roof runs back to +Y). Shapes come from window_shapes.py. Registered into nh_props.BUILD.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, material
from nh_props_batch3 import sphere, cone, flame, circle_pts
from nh_props_batch4 import lathe, hoop, prism, leaf, _mark, _xform, _dims, flat
from nh_props_batch8 import mossy, hollow, staining, _moss, _crack, _stain, _spirelet, _crockets, _spike, _lancet
from nh_props_batch9 import foil, candle, wax_mat
from nh_props_batch10 import gilt, velvet
from nh_props_batch12 import soot_stone, sheet
import nh_props_batch20 as B20
import window_shapes as WS


# ------------------------------------------------------------------ materials

def kit(M):
    return {
        "st": soot_stone("SootStone", (0.16, 0.165, 0.155)),
        "dk": soot_stone("SootStoneDark", (0.095, 0.1, 0.093)),
        "iron": M["iron"], "brass": M["brass"], "gilt": gilt(), "glass": M["glassclear"],
        "lead": material("Lead", "NH_PaintedMetal", tint=(0.1, 0.105, 0.11), scale=0.7, rough_add=0.25, wear=0.2),
        "enamel": material("CrimsonEnamel", "NH_PaintedMetal", tint=(0.2, 0.025, 0.04), scale=1.4, rough_mul=0.55, rough_add=0.05, wear=0.45,
                           wear_metal=True, dirt=0.85),
        "crimson": M["crimson"],
        "slate": material("RoofSlate", "NH_Slate", tint=(0.045, 0.055, 0.075), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.15),
        "hollow": hollow(), "moss": mossy(), "stain": staining(),
        "rust": flat("RustStain", (0.09, 0.035, 0.015), 0.95, dirt=0.4),
        "room": flat("RoomTmp", (0.5, 0.3, 0.1), 0.9),
        "stained": flat("StainedTmp", (0.5, 0.5, 0.5), 0.3),
    }


# ------------------------------------------------------------------ mesh helpers

def _mk(name, verts, faces, mat, drop_back=False, tri=True):
    """A mesh from vertices and faces (normals recalculated, so it must be closed); drop_back removes the faces lying on
    the wall plane (y = 0) facing +Y, which nobody sees, so the atlas isn't spent on them."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if drop_back:
        bm.normal_update()
        dead = [f for f in bm.faces if f.normal.y > 0.99 and all(v.co.y > -0.002 for v in f.verts)]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    if tri:
        md = ob.modifiers.new("Tri", "TRIANGULATE")
        md.quad_method = "BEAUTY"
        md.ngon_method = "BEAUTY"
    return ob


def sweep(name, outline, profile, mat, rng=None, drop_back=True, shrink=0.0):
    """Sweep a closed section `profile` [(d, y), ...] (d = offset outward from the outline) round a counter-clockwise
    outline, or only along outline indices rng = (i0, i1) as a capped block. shrink pulls a block in a little on X / Z
    so neighbouring blocks show a joint."""
    loops = [WS.offset(outline, d) for d, _ in profile]
    n = len(outline)
    if rng is None:
        idx, closed = list(range(n)), True
    else:
        i0, i1 = rng
        idx, closed = [(i0 + k) % n for k in range((i1 - i0) % n + 1)], False
    m = len(profile)
    verts = [(loops[k][j][0], y, loops[k][j][1]) for j in idx for k, (_, y) in enumerate(profile)]
    if shrink:
        cx = sum(v[0] for v in verts) / len(verts)
        cz = sum(v[2] for v in verts) / len(verts)
        verts = [(cx + (x - cx) * (1 - shrink), y, cz + (z - cz) * (1 - shrink)) for x, y, z in verts]
    L = len(idx)
    faces = []
    for a in range(L if closed else L - 1):
        b = (a + 1) % L
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((a * m + k, a * m + k2, b * m + k2, b * m + k))
    if not closed:
        faces.append(tuple(range(m)))
        faces.append(tuple((L - 1) * m + k for k in range(m)))
    return _mk(name, verts, faces, mat, drop_back=drop_back)


def stones(prefix, outline, profile, mat, step=0.55, every=2):
    """A jointed stone surround: the outline resampled every `step`, swept with `profile`, cut into blocks of `every`
    points. Returns the resampled outline."""
    o = WS.resample(outline, step)
    n = len(o)
    cuts = list(range(0, n, every))
    for k, c in enumerate(cuts):
        nxt = cuts[(k + 1) % len(cuts)]
        sweep(f"{prefix}{k}", o, profile, mat, rng=(c, nxt), shrink=0.012)
    return o


def ribbon(name, path, w, y0, y1, mat):
    """A flat bar of width w along an open path in the XZ plane, from y0 to y1 (a tracery bar, a glazing bar)."""
    a = WS.offset(path, w / 2, closed=False)
    b = WS.offset(path, -w / 2, closed=False)
    return B20.tprism(name, a + list(reversed(b)), (y0 + y1) / 2, abs(y1 - y0), mat)


def loopbar(name, loop, w, y0, y1, mat):
    """A closed bar of width w round a loop (counter-clockwise), from y0 to y1."""
    loop = WS.ccw(loop)
    return sweep(name, loop, [(w / 2, y0), (w / 2, y1), (-w / 2, y1), (-w / 2, y0)], mat, drop_back=False)


def plate(name, poly, y0, y1, mat):
    return B20.tprism(name, WS.ccw(poly), (y0 + y1) / 2, abs(y1 - y0), mat)


_CUTS = []


def pierce(ob, polys, y0=-3.0, y1=1.0):
    """Cut openings through a part (exact boolean, applied when the parts are joined); the cutters never render."""
    for k, poly in enumerate(polys):
        me = bpy.data.meshes.new(f"{ob.name}Cut{k}")
        bm = bmesh.new()
        p = WS.ccw(poly)
        a = [bm.verts.new((x, y0, z)) for x, z in p]
        b = [bm.verts.new((x, y1, z)) for x, z in p]
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        for i in range(len(p)):
            j = (i + 1) % len(p)
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(ob.data.materials[0])      # cut faces take the part's own material (no empty slot)
        cut = bpy.data.objects.new(me.name, me)
        bpy.context.collection.objects.link(cut)
        cut.hide_render = True
        cut.display_type = "WIRE"
        _CUTS.append(cut)
        md = ob.modifiers.new(f"Cut{k}", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = "EXACT"
        md.object = cut
    return ob


def glass(name, poly, y, K):
    set_group("Glass")
    B20.tprism(name, WS.ccw(poly), y, 0.02, K["glass"])
    set_group("Main")


def room(name, polys, K, y=-0.03, grow=0.06):
    """The lit room behind clear glass (group Room: the shared warm amber canvas)."""
    set_group("Room")
    for k, p in enumerate(polys):
        B20.tprism(f"{name}{k}", WS.offset(WS.ccw(p), grow), y, 0.02, K["room"])
    set_group("Main")


def stained(name, poly, y, K):
    set_group("Stained")
    B20.tprism(name, WS.offset(WS.ccw(poly), 0.05), y, 0.02, K["stained"])
    set_group("Main")


def leads(prefix, poly, y, step, mat, mode="diamond", r=0.011, skip=None):
    """Lead cames across an outline (clipped to it). skip(pt) -> True drops the came near that point (broken glass)."""
    k = 0
    for a, b in WS.lattice_lines(poly, step, mode):
        segs = [(a, b)]
        if skip:
            segs = _split_skip(a, b, skip)
        for p, q in segs:
            tube(f"{prefix}{k}", [(p[0], y, p[1]), (q[0], y, q[1])], r, mat, square=True, poly=True)
            k += 1
    tube(f"{prefix}Rim", [(x, y, z) for x, z in WS.offset(WS.ccw(poly), -0.01)], r * 1.3, mat, closed=True, square=True, poly=True)


def _split_skip(a, b, skip, n=24):
    out, cur = [], None
    for i in range(n + 1):
        t = i / n
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if skip(p):
            if cur and cur[1] != cur[0]:
                out.append(tuple(cur))
            cur = None
        else:
            cur = [cur[0], p] if cur else [p, p]
    if cur and cur[1] != cur[0]:
        out.append(tuple(cur))
    return [s for s in out if math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]) > 0.05]


def saddle_bars(prefix, poly, zs, y, mat, r=0.022, ext=0.12):
    """Iron saddle bars across an opening at heights zs, running into the jambs."""
    big = WS.offset(WS.ccw(poly), ext)
    for k, z in enumerate(zs):
        for a, b in WS.clip_line((0.0, z), (1.0, 0.0), big):
            tube(f"{prefix}{k}", [(a[0], y, z), (b[0], y, z)], r, mat, square=True, poly=True)


def hood(prefix, hw, zs, za, y, mat, label_mat, foil_mat, r=0.085, ret=0.3, n=16, cx=0.0, crockets=None, labels=(-1, 1)):
    """A hood mould over a pointed head (half width hw, springing zs, apex za), returning sideways onto carved label stops
    (on the sides listed in labels)."""
    pts = [(cx + x, z) for x, z in WS.pointed(hw, zs, za, n)]
    path = ([(cx - hw - ret, y, zs)] if -1 in labels else []) + [(x, y, z) for x, z in pts] + ([(cx + hw + ret, y, zs)] if 1 in labels else [])
    tube(f"{prefix}", path, r, mat, square=True, poly=True)
    for sx in labels:
        x = cx + sx * (hw + ret)
        box(f"{prefix}Label{sx}", (0.34, 0.3, 0.36), (x, y + 0.04, zs - 0.24), label_mat, bevel=0.035)
        foil(f"{prefix}LabelFoil{sx}", x, y - 0.12, zs - 0.25, 0.1, foil_mat, lobes=4, thick=0.014)
    if crockets:
        _crockets(f"{prefix}Crocket", [(x, y - 0.02, z + 0.09) for x, z in pts[2:-2:2]], crockets, size=0.07)
    return pts


def sill(prefix, w, z0, mat, depth=1.0, h=0.34):
    """A weathered stone sill under an opening at z0: a sloped top, a drip under its nose."""
    t = z0 + SILL_UP          # the top stands a little above the opening's foot, so it never shares the jamb's plane
    prism(prefix, [(0.0, z0 - h), (-depth, z0 - h), (-depth, t - 0.15), (-depth + 0.24, t), (0.0, t)], 0.0, w, mat, plane="YZ", bevel=0.03)
    box(f"{prefix}Drip", (w - 0.1, 0.04, 0.04), (0, -depth + 0.08, z0 - h - 0.005), mat, bevel=0.0, segments=1)


SILL_UP = 0.03

JAMB = lambda w, D, c: [(c, -D), (w, -D), (w, 0.0), (0.0, 0.0), (0.0, -D + c)]


def moulded(w, D):
    """A moulded jamb section (d out from the opening, y): a chamfer, a roll, a hollow, a fillet and the flat face."""
    return [(0.1, -D), (0.16, -D - 0.04), (0.24, -D - 0.05), (0.3, -D - 0.02), (0.34, -D + 0.04), (0.42, -D + 0.02), (0.48, -D - 0.03),
            (w, -D - 0.03), (w, 0.0), (0.0, 0.0), (0.0, -D + 0.12)]


def _rotz(a):
    return Matrix.Rotation(a, 4, "Z")


def _weather(K, rnd, pts, cracks=()):
    _moss("Moss", pts, K["moss"], rnd, size=0.09)
    for k, (p0, u, L) in enumerate(cracks):
        _crack(f"Crack{k}", p0, u, (1, 0, 0), L, rnd, K["hollow"])


def _candle_on(prefix, x, y, z, K, h=0.42, dish=True):
    if dish:
        lathe(f"{prefix}Dish", [(0, z), (0.1, z), (0.11, z + 0.025), (0.05, z + 0.035), (0, z + 0.035)], K["brass"], seg=14, loc=(x, y, 0))
        z += 0.035
    tip = candle(prefix, x, y, z, h, wax_mat(), r=0.04)
    set_group("Glow")
    flame(f"{prefix}Flame", (x, y, tip - 0.005), h=0.1)
    set_group("Main")


# ================================================================== the gothic lancets

def lancet_window(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2301)
    HW, Z0, ZS, ZA = 1.0, 0.75, 5.8, 7.6
    D = 0.75
    op = WS.arch(HW, Z0, ZS, ZA, 12)
    stones("Jamb", op, JAMB(0.6, D, 0.16), st, step=0.5)
    sill("Sill", 2 * HW + 1.7, Z0, dk)
    hood("Hood", HW + 0.72, ZS, ZA + 0.86, -D - 0.07, dk, dk, st)
    yg = -0.3
    glass("Pane", op, yg, K)
    leads("Came", op, yg - 0.02, (0.42, 0.56), K["lead"], mode="square")
    saddle_bars("Saddle", op, (1.95, 3.1, 4.25, 5.4), yg - 0.045, iron)
    room("Room", [op], K)
    _candle_on("Candle", 0.42, -0.15, Z0 + SILL_UP, K)
    _weather(K, rnd, [(-1.1, -0.85, Z0 + 0.02), (1.05, -0.8, Z0 + 0.02), (HW + 1.0, -D - 0.1, ZS - 0.02)],
             [((-HW - 0.35, -D - 0.005, 3.4), (0.2, 0, -1), 0.8)])
    return _dims()


def twin_lancet(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2302)
    HW, Z0, ZS, ZA = 2.1, 0.75, 4.6, 7.6
    D = 0.85
    op = WS.arch(HW, Z0, ZS, ZA, 16)
    stones("Arch", op, moulded(0.7, D), st, step=0.5)
    sill("Sill", 2 * HW + 1.8, Z0, dk)
    hood("Hood", HW + 0.8, ZS, ZA + 0.95, -D - 0.12, dk, dk, st)
    # the plate: the whole opening in stone, pierced by the two lancets and the quatrefoil
    lx, lhw, lza = 1.05, 0.8, 6.0
    lights = [WS.arch(lhw, Z0, ZS, lza, 10, cx=sx * lx) for sx in (-1, 1)]
    qf = WS.foil_outline(0, 6.72, 0.5, 4, n=64, a0=math.pi / 4)
    pl = plate("Plate", op, -0.7, -0.26, st)
    pierce(pl, [WS.arch(lhw, Z0 - 0.3, ZS, lza, 10, cx=sx * lx) for sx in (-1, 1)] + [qf])
    for k, L in enumerate(lights):
        cx = (-1, 1)[k] * lx
        tube(f"Roll{k}", [(x, -0.72, z) for x, z in WS.offset(L, 0.05)][1:] + [(cx - lhw - 0.05, -0.72, Z0)], 0.035, dk, square=True, poly=True)
        yg = -0.22
        glass(f"Pane{k}", L, yg, K)
        leads(f"Came{k}_", L, yg - 0.02, 0.36, K["lead"])
        saddle_bars(f"Saddle{k}_", L, (1.9, 3.1, 4.3), yg - 0.045, iron, ext=0.06)
    tube("QfRim", [(x, -0.72, z) for x, z in WS.offset(WS.ccw(qf), 0.04)], 0.03, dk, closed=True, square=True, poly=True)
    glass("PaneQf", qf, -0.22, K)
    # a shafted mullion in front of the pier between the lights
    cyl("Shaft", 0.13, ZS - Z0 - 0.5, (0, -0.86, (Z0 + ZS) / 2), dk, verts=16, bevel=0.0)
    box("ShaftBase", (0.42, 0.42, 0.25), (0, -0.82, Z0 + 0.125), st, bevel=0.03)
    box("ShaftCap", (0.46, 0.46, 0.26), (0, -0.82, ZS - 0.13), st, bevel=0.03)
    foil("CapFoil", 0, -1.06, ZS - 0.13, 0.09, dk, lobes=4, thick=0.012)
    room("Room", lights + [qf], K)
    _weather(K, rnd, [(-1.6, -0.9, Z0 + 0.02), (1.4, -0.95, Z0 + 0.02), (-HW - 1.1, -D - 0.15, ZS - 0.02)],
             [((HW + 0.5, -D - 0.035, 2.7), (-0.2, 0, -1), 0.9)])
    return _dims()


def triplet_lancet(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2303)
    Z0, D = 0.75, 0.75
    specs = [(-1.95, 0.58, 4.9, 6.3), (0.0, 0.72, 5.9, 7.7), (1.95, 0.58, 4.9, 6.3)]
    lights = []
    for k, (cx, hw, zs, za) in enumerate(specs):
        op = WS.arch(hw, Z0, zs, za, 12, cx=cx)
        lights.append(op)
        stones(f"Jamb{k}_", op, JAMB(0.32, D, 0.1), st, step=0.5)
        hood(f"Hood{k}", hw + 0.42, zs, za + 0.52, -D - 0.07, dk, dk, st, r=0.07, ret=0.22, cx=cx, labels=((-1,) if k == 0 else (1,) if k == 2 else ()))
        yg = -0.28
        glass(f"Pane{k}", op, yg, K)
        leads(f"Came{k}_", op, yg - 0.02, (0.38, 0.5), K["lead"], mode="square")
        saddle_bars(f"Saddle{k}_", op, [z for z in (1.9, 3.0, 4.1, 5.2) if z < zs], yg - 0.045, iron, ext=0.08)
    # shafts on the piers between the lights and a string course at the side lights' springing
    for sx in (-1, 1):
        x = sx * 0.975
        cyl(f"Shaft{sx}", 0.1, 4.9 - Z0 - 0.4, (x, -D - 0.12, (Z0 + 4.9) / 2), dk, verts=14, bevel=0.0)
        box(f"ShaftBase{sx}", (0.3, 0.3, 0.2), (x, -D - 0.1, Z0 + 0.1), st, bevel=0.025)
        box(f"ShaftCap{sx}", (0.34, 0.34, 0.22), (x, -D - 0.1, 4.9 - 0.11), st, bevel=0.025)
    sill("Sill", 7.0, Z0, dk)
    room("Room", lights, K)
    _weather(K, rnd, [(-2.9, -0.85, Z0 + 0.02), (0.3, -0.9, Z0 + 0.02), (2.7, -0.85, Z0 + 0.02)],
             [((-2.6, -D - 0.005, 3.0), (0.25, 0, -1), 0.7)])
    return _dims()


# ================================================================== stained glass

def tracery_window(M, clear=False):
    K = kit(M)
    st, dk, iron, gl = K["st"], K["dk"], K["iron"], K["gilt"]
    rnd = random.Random(2304)
    T = WS.Tracery
    D = 1.0
    op = T.outline()
    stones("Arch", op, moulded(0.85, D), st, step=0.55)
    sill("Sill", 2 * T.HW + 2.2, T.Z0, dk, depth=1.25, h=0.4)
    hp = hood("Hood", T.HW + 0.98, T.ZS, T.ZA + 1.2, -D - 0.14, dk, dk, st, r=0.1, ret=0.35, n=20, crockets=dk)
    sphere("HoodFinial", 0.16, (0, -D - 0.16, T.ZA + 1.42), gl, seg=12, rings=6)
    _spike("HoodFinialSpike", (0, -D - 0.16, T.ZA + 1.75), 0.06, 0.45, dk, verts=6)
    # bar tracery (y from -0.6 to -0.22): mullions, the sub-arches, the light heads, the head circle and its foil,
    # the spandrel circles
    y0, y1, b = -0.6, -0.22, T.BAR
    for k, x in enumerate((-1.65, 0.0, 1.65)):
        ribbon(f"Mullion{k}", [(x, T.Z0 - 0.05), (x, T.ZS)], b, y0, y1, st)
        box(f"MullionBase{k}", (b + 0.14, 0.5, 0.3), (x, (y0 + y1) / 2, T.Z0 + 0.15), st, bevel=0.03)
    for k, (cx, hw) in enumerate(T.PAIR):
        ribbon(f"Pair{k}", [(cx + x, z) for x, z in WS.pointed(hw, T.ZS, T.PAIR_ZA, 14)], b, y0, y1, st)
    for k, cx in enumerate(T.LIGHTS):
        ribbon(f"Head{k}", [(cx + x, z) for x, z in WS.pointed(T.LIGHT_HW, T.ZS, T.LIGHT_ZA, 10)], b * 0.85, y0 + 0.03, y1, st)
    hx, hz, hr = T.HEAD
    loopbar("HeadRing", WS.circle(hx, hz, hr, 48), b, y0, y1, st)
    loopbar("HeadFoil", WS.foil_outline(hx, hz, hr - 0.1, 6, n=96), b * 0.6, y0 + 0.04, y1, st)
    for k, (cx, cz, r) in enumerate(T.SPANDREL):
        loopbar(f"Spandrel{k}", WS.circle(cx, cz, r, 28), b * 0.8, y0 + 0.02, y1, st)
        loopbar(f"SpandrelFoil{k}", WS.foil_outline(cx, cz, r - 0.07, 3, n=48), b * 0.5, y0 + 0.05, y1, st)
    # iron saddle bars across the lights, the stained glass behind
    for k, cx in enumerate(T.LIGHTS):
        saddle_bars(f"Saddle{k}_", T.light(k), (2.2, 3.7, 5.2), -0.2, iron, ext=0.06)
    if clear:
        # plain leaded quarries behind the bars, the lit room beyond
        glass("Pane", op, -0.15, K)
        for k in range(4):
            leads(f"Came{k}_", WS.offset(WS.ccw(T.light(k)), -T.BAR / 2 + 0.02), -0.17, 0.36, K["lead"])
        room("Room", [op], K)
    else:
        stained("Glass", op, -0.15, K)
    _weather(K, rnd, [(-3.0, -1.15, T.Z0 + 0.02), (-0.6, -1.2, T.Z0 + 0.02), (2.4, -1.1, T.Z0 + 0.02), (T.HW + 1.3, -D - 0.2, T.ZS - 0.02)],
             [((-T.HW - 0.5, -D - 0.035, 3.2), (0.2, 0, -1), 1.0), ((T.HW + 0.6, -D - 0.035, 8.1), (-0.3, 0, -1), 0.7)])
    return _dims()


def rose_window(M, clear=False):
    K = kit(M)
    st, dk, gl = K["st"], K["dk"], K["gilt"]
    rnd = random.Random(2305)
    R = WS.Rose
    D = 0.9
    op = WS.circle(0, R.CZ, R.R, 64)
    stones("Ring", op, moulded(0.75, D), st, step=0.5, every=3)
    # an outer roll round the ring, a plinth course under it
    hoop("OuterRoll", (0, -D - 0.06, R.CZ), R.R + 0.86, "Y", dk, thick=0.07)
    box("Plinth", (3.4, D + 0.2, 0.36), (0, -(D + 0.2) / 2, 0.18), dk, bevel=0.04)
    y0, y1, b = -0.55, -0.2, R.BAR
    loopbar("Hub", WS.circle(0, R.CZ, R.HUB, 36), b, y0, y1, st)
    loopbar("HubFoil", WS.foil_outline(0, R.CZ, R.HUB - 0.07, 6, n=72), b * 0.6, y0 + 0.03, y1, st)
    sphere("HubBoss", 0.14, (0, y0 - 0.04, R.CZ), gl, seg=12, rings=6, scale=(1, 0.5, 1))
    for k, a in enumerate(R.angles()):
        p0 = (math.cos(a) * (R.HUB - 0.02), R.CZ + math.sin(a) * (R.HUB - 0.02))
        p1 = (math.cos(a) * R.SPOKE_R, R.CZ + math.sin(a) * R.SPOKE_R)
        ribbon(f"Spoke{k}", [p0, p1], b, y0, y1, st)
        cyl(f"SpokeRing{k}", 0.1, 0.09, (math.cos(a) * 1.75, -0.6, R.CZ + math.sin(a) * 1.75), dk, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
        ribbon(f"Petal{k}", R.petal_head(k), b * 0.85, y0 + 0.02, y1, st)
        loopbar(f"Foil{k}", WS.circle(math.cos(a) * R.FOIL_AT, R.CZ + math.sin(a) * R.FOIL_AT, R.FOIL_R, 20), b * 0.65, y0 + 0.03, y1, st)
    if clear:
        glass("Pane", op, -0.12, K)
        room("Room", [op], K)
    else:
        stained("Glass", op, -0.12, K)
    _weather(K, rnd, [(-1.2, -1.0, 0.36), (1.3, -1.05, 0.36), (0.0, -1.0, 0.36)],
             [((-R.R - 0.4, -D - 0.035, 5.6), (0.3, 0, -1), 0.9)])
    return _dims()


def stained_lancet(M):
    K = kit(M)
    st, dk, iron, gl = K["st"], K["dk"], K["iron"], K["gilt"]
    rnd = random.Random(2313)
    S = WS.StainedLancet
    D = 0.85
    op = S.outline()
    stones("Jamb", op, moulded(0.7, D), st, step=0.5)
    sill("Sill", 2 * S.HW + 1.9, S.Z0, dk, depth=1.15)
    hood("Hood", S.HW + 0.86, S.ZS, S.ZA + 1.0, -D - 0.12, dk, dk, st, crockets=dk)
    sphere("HoodFinial", 0.12, (0, -D - 0.14, S.ZA + 1.16), gl, seg=10, rings=5)
    fx, fz, fr = S.FOIL
    loopbar("HeadFoil", WS.foil_outline(fx, fz, fr, 3, n=60), 0.12, -0.5, -0.2, st)
    # the cusped head: a thin bar following the arch inside, meeting the foil
    saddle_bars("Saddle", op, S.SADDLE, -0.22, iron, ext=0.1)
    stained("Glass", op, -0.13, K)
    # a pricket candle on the outer sill
    x, y = 0.55, -0.7
    z = S.Z0 + SILL_UP
    lathe("Pricket", [(0, z), (0.13, z), (0.12, z + 0.03), (0.04, z + 0.06), (0.03, z + 0.22), (0.08, z + 0.25), (0.09, z + 0.27), (0, z + 0.27)],
          iron, seg=14, loc=(x, y, 0))
    _candle_on("Candle", x, y, z + 0.27, K, h=0.36, dish=False)
    _weather(K, rnd, [(-1.0, -1.0, S.Z0 + 0.02), (1.25, -1.05, S.Z0 + 0.02)], [((S.HW + 0.4, -D - 0.035, 4.4), (-0.2, 0, -1), 0.8)])
    return _dims()


# ================================================================== round and casement windows

def oculus(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2306)
    r, zc, D = 1.15, 2.0, 0.7
    op = WS.circle(0, zc, r, 40)
    stones("Ring", op, moulded(0.6, D), st, step=0.4, every=5)
    for k in range(4):
        a = k * math.pi / 2
        x, z = math.cos(a) * (r + 0.62), zc + math.sin(a) * (r + 0.62)
        box(f"Key{k}", (0.42, D + 0.14, 0.5) if k % 2 else (0.5, D + 0.14, 0.42), (x, -(D + 0.14) / 2, z), dk, bevel=0.035)
    yg = -0.3
    glass("Pane", op, yg, K)
    loopbar("GrilleRim", WS.offset(WS.ccw(op), -0.03), 0.07, yg - 0.07, yg - 0.01, iron)
    loopbar("GrilleFoil", WS.foil_outline(0, zc, r * 0.82, 4, n=72, a0=math.pi / 4), 0.06, yg - 0.07, yg - 0.01, iron)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ribbon(f"GrilleBar{k}", [(math.cos(a) * 0.12, zc + math.sin(a) * 0.12), (math.cos(a) * (r - 0.05), zc + math.sin(a) * (r - 0.05))], 0.05,
               yg - 0.07, yg - 0.01, iron)
    sphere("Boss", 0.11, (0, yg - 0.08, zc), brass, seg=12, rings=6, scale=(1, 0.55, 1))
    room("Room", [op], K)
    _weather(K, rnd, [(-0.7, -D - 0.02, zc - r - 0.55), (0.9, -D - 0.02, zc - r - 0.5)])
    return _dims()


def diamond_pane_arch(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2307)
    HW, Z0, ZS, ZA = 1.4, 0.75, 4.3, 6.1
    D = 0.8
    op = WS.arch(HW, Z0, ZS, ZA, 14)
    stones("Jamb", op, JAMB(0.62, D, 0.16), st, step=0.5)
    sill("Sill", 2 * HW + 1.7, Z0, dk)
    hood("Hood", HW + 0.75, ZS, ZA + 0.88, -D - 0.07, dk, dk, st)
    # the iron casement: a frame in the reveal, a transom at the springing, two leaves meeting in the middle
    yf0, yf1 = -0.44, -0.3
    loopbar("Frame", WS.offset(WS.ccw(op), -0.07), 0.14, yf0, yf1, iron)
    ribbon("Transom", [(-HW + 0.05, ZS), (HW - 0.05, ZS)], 0.13, yf0 - 0.02, yf1, iron)
    ribbon("Meeting", [(0, Z0 + 0.05), (0, ZS)], 0.16, yf0 - 0.03, yf1, iron)
    ribbon("HeadBar", [(0, ZS), (0, ZA - 0.1)], 0.08, yf0, yf1, iron)
    regions = []
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.08, sx * (HW - 0.14)))
        leaf = WS.rect((x1 - x0) / 2, Z0 + 0.14, ZS - 0.07, cx=(x0 + x1) / 2)
        loopbar(f"Leaf{sx}", leaf, 0.08, yf0 - 0.01, yf1, iron)
        regions.append(leaf)
    head = WS.clip_convex(WS.offset(WS.ccw(op), -0.14), WS.rect(5.0, ZS + 0.07, ZA + 2.0))
    for k, reg in enumerate(regions + [head]):
        leads(f"Came{k}_", reg, -0.34, 0.33, K["lead"])
    yg = -0.32
    glass("Pane", op, yg, K)
    # brass handles (cockspurs) on the meeting stiles and a casement stay on each leaf
    for sx in (-1, 1):
        box(f"HandlePlate{sx}", (0.06, 0.03, 0.26), (sx * 0.12, yf0 - 0.05, 2.6), brass, bevel=0.008)
        tube(f"Handle{sx}", [(sx * 0.12, yf0 - 0.07, 2.65), (sx * 0.14, yf0 - 0.16, 2.6), (sx * 0.3, yf0 - 0.17, 2.52)], 0.018, brass)
        tube(f"Stay{sx}", [(sx * 0.6, yf0 - 0.05, Z0 + 0.22), (sx * 1.2, yf0 - 0.05, Z0 + 0.22)], 0.016, brass, square=True, poly=True)
        for k in range(3):
            sphere(f"StayPin{sx}{k}", 0.025, (sx * (0.7 + k * 0.18), yf0 - 0.07, Z0 + 0.22), brass, seg=8, rings=4)
    room("Room", [op], K)
    _candle_on("Candle", -0.75, -0.16, Z0 + SILL_UP, K, h=0.38)
    _weather(K, rnd, [(-1.4, -0.9, Z0 + 0.02), (1.2, -0.85, Z0 + 0.02)], [((HW + 0.3, -D - 0.005, 2.5), (-0.2, 0, -1), 0.7)])
    return _dims()


def sash_window(M):
    K = kit(M)
    st, dk, iron, brass, en = K["st"], K["dk"], K["iron"], K["brass"], K["enamel"]
    rnd = random.Random(2308)
    HW, Z0, ZS, RISE = 1.6, 0.8, 6.9, 0.55
    D = 0.7
    op = WS.segmental(HW, Z0, ZS, RISE, 14)
    o = stones("Jamb", op, JAMB(0.6, D, 0.12), st, step=0.5)
    apex = max(range(len(o)), key=lambda i: o[i][1])
    ax, az = o[apex]
    prism("Keystone", [(-0.32, az + 0.75), (0.32, az + 0.75), (0.22, az - 0.04), (-0.22, az - 0.04)], -(D + 0.1) / 2, D + 0.1, dk, bevel=0.03)
    foil("KeyFoil", 0, -D - 0.12, az + 0.42, 0.11, st, lobes=4, thick=0.014)
    sill("Sill", 2 * HW + 1.6, Z0, dk)
    for sx in (-1, 1):
        box(f"SillBracket{sx}", (0.3, 0.42, 0.32), (sx * (HW + 0.45), -0.55, Z0 - 0.5), dk, bevel=0.03)
    # crimson enamel sashes with iron glazing bars; the top sash's head follows the arch, with Y-tracery bars
    yl0, yl1 = -0.42, -0.3              # the lower sash (in front)
    yu0, yu1 = -0.3, -0.2               # the upper sash
    zm = 3.95
    loopbar("Box", WS.offset(WS.ccw(op), -0.05), 0.1, -0.44, -0.18, en)
    lower = WS.rect(HW - 0.1, Z0 + 0.1, zm + 0.06)
    upper_out = WS.ccw([(-HW + 0.1, zm - 0.06), (HW - 0.1, zm - 0.06)] + [p for p in WS.offset(WS.ccw(op), -0.1) if p[1] > zm + 0.3])
    upper_out = [p for p in upper_out]
    loopbar("LowerSash", WS.offset(lower, -0.06), 0.12, yl0, yl1, en)
    loopbar("UpperSash", WS.offset(upper_out, -0.06), 0.12, yu0, yu1, en)
    box("MeetingRail", (2 * HW - 0.2, 0.12, 0.14), (0, yl0 + 0.06, zm), en, bevel=0.012)
    for k, x in enumerate((-HW / 3 + 0.03, HW / 3 - 0.03)):
        ribbon(f"LowBarV{k}", [(x, Z0 + 0.16), (x, zm - 0.04)], 0.045, yl0 + 0.02, yl1, iron)
    ribbon("LowBarH", [(-HW + 0.16, (Z0 + zm) / 2), (HW - 0.16, (Z0 + zm) / 2)], 0.045, yl0 + 0.02, yl1, iron)
    ybar = (yu0 + 0.02, yu1)
    ribbon("UpBarV", [(0, zm + 0.04), (0, 5.45)], 0.05, *ybar, iron)
    for sx in (-1, 1):
        ribbon(f"UpY{sx}", [(0, 5.45), (sx * 0.4, 6.15), (sx * 0.95, 6.9), (sx * 1.35, 7.35)], 0.05, *ybar, iron)
        ribbon(f"UpV{sx}", [(sx * 0.9, zm + 0.04), (sx * 0.9, 5.9)], 0.045, *ybar, iron)
        ribbon(f"UpArc{sx}", [(sx * 0.9, 5.9), (sx * 0.6, 6.35), (sx * 0.1, 6.6), (0, 6.62)], 0.04, *ybar, iron)
    # brass: the sash lock on the meeting rail, two lifts on the bottom rail, a pole eye at the top
    box("LockPlate", (0.3, 0.04, 0.08), (0, yl0 - 0.01, zm + 0.08), brass, bevel=0.01)
    tube("LockArm", [(-0.1, yl0 - 0.05, zm + 0.12), (0.05, yl0 - 0.07, zm + 0.14), (0.16, yl0 - 0.05, zm + 0.12)], 0.016, brass)
    sphere("LockKnob", 0.035, (0.17, yl0 - 0.06, zm + 0.12), brass, seg=8, rings=4)
    for sx in (-1, 1):
        tube(f"Lift{sx}", [(sx * 0.7 - 0.07, yl0 - 0.01, Z0 + 0.24), (sx * 0.7, yl0 - 0.06, Z0 + 0.24), (sx * 0.7 + 0.07, yl0 - 0.01, Z0 + 0.24)], 0.016,
             brass)
    hoop("PoleEye", (0, yu0 - 0.03, 6.75), 0.05, "X", brass, thick=0.012)
    yg = -0.25
    glass("PaneLow", lower, yl1 + 0.015, K)
    glass("PaneUp", upper_out, yu1 + 0.015, K)
    room("Room", [op], K)
    _weather(K, rnd, [(-1.9, -0.85, Z0 + 0.02), (1.6, -0.9, Z0 + 0.02)], [((-HW - 0.3, -D - 0.005, 4.8), (0.2, 0, -1), 0.8)])
    return _dims()


# ================================================================== bay and dormer

def gothic_bay(M):
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2309)
    plan = [(-2.9, 0.0), (-1.9, -2.4), (1.9, -2.4), (2.9, 0.0)]        # wall line at y = 0, front face at y = -2.4
    ZB, ZW, ZT = 2.3, 2.6, 7.6                                          # plinth top, window board, window head
    prism("Plinth", plan, 0.0, ZB, st, plane="XY", bevel=0.03)
    prism("PlinthFoot", [(x * 1.03, y * 1.03) for x, y in plan], 0.0, 0.35, dk, plane="XY", bevel=0.03)
    prism("SillBand", [(x * 1.035, y * 1.035) for x, y in plan], ZB, ZW - ZB, dk, plane="XY", bevel=0.03)
    faces = list(zip(plan, plan[1:]))
    for fi, (p, q) in enumerate(faces):
        p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
        e = q - p
        L = e.length
        e.normalize()
        nrm = Vector((e.y, -e.x, 0))
        th = math.atan2(nrm.x, -nrm.y)
        mtx = Matrix.Translation((p + q) / 2) @ _rotz(th)
        s = _mark()
        # blind tracery on the plinth face
        for k, cx in enumerate([0.0] if L < 3 else [-L / 4, L / 4]):
            pw = L * (0.36 if L < 3 else 0.2)
            tube(f"Blind{fi}{k}", [(cx + x, -0.02, z) for x, z in WS.arch(pw, 0.6, 1.5, 2.05, 8)], 0.03, dk, closed=True, square=True, poly=True)
            foil(f"BlindFoil{fi}{k}", cx, -0.03, 1.7, pw * 0.42, dk, lobes=3, thick=0.012)
        # the face: a stone plate pierced by its lights
        lights = [WS.arch(0.7, ZW + 0.1, 6.1, 7.05, 10, cx=cx) for cx in ([0.0] if L < 3 else [-0.92, 0.92])]
        pl = plate(f"Face{fi}", WS.rect(L / 2, ZW, ZT), 0.0, 0.32, st)
        pierce(pl, [WS.arch(0.7, ZW - 0.3, 6.1, 7.05, 10, cx=lt[0][0] + 0.7) for lt in lights])
        for k, lt in enumerate(lights):
            cx = lt[0][0] + 0.7
            tube(f"Roll{fi}{k}", [(x, -0.03, z) for x, z in WS.offset(lt, 0.04)][1:] + [(cx - 0.74, -0.03, ZW + 0.1)], 0.035, dk, square=True, poly=True)
            foil(f"Cusp{fi}{k}", cx, -0.02, 6.55, 0.3, dk, lobes=3, thick=0.016, centre=False)
            glass(f"Pane{fi}{k}", lt, 0.18, K)
            leads(f"Came{fi}{k}_", lt, 0.16, 0.34, K["lead"])
        _xform(s, mtx)
    # corner shafts, the cornice, a crenellated parapet with coping, a lead roof
    for k, (x, y) in enumerate(plan[1:3]):
        cyl(f"Shaft{k}", 0.15, ZT - ZW, (x * 1.02, y - 0.08, (ZW + ZT) / 2), dk, verts=16, bevel=0.0)
        box(f"ShaftCap{k}", (0.4, 0.4, 0.22), (x * 1.02, y - 0.08, ZT - 0.05), st, bevel=0.025)
    for sx in (-1, 1):
        box(f"WallPier{sx}", (0.42, 0.34, ZT + 0.9), (sx * 2.84, -0.17, (ZT + 0.9) / 2), st, bevel=0.03)
    cor = [(x * 1.05, y * 1.05) for x, y in plan]
    prism("Cornice", cor, ZT, 0.25, dk, plane="XY", bevel=0.03)
    prism("RoofLead", [(x * 0.98, y * 0.98) for x, y in plan], ZT + 0.25, 0.05, K["lead"], plane="XY")
    for fi, (p, q) in enumerate(zip(cor, cor[1:])):
        p, q = Vector((p[0], p[1], 0)), Vector((q[0], q[1], 0))
        e = q - p
        L = e.length
        ang = math.atan2(e.y, e.x)
        inward = Vector((-e.y, e.x, 0)).normalized()
        mid = (p + q) / 2 + inward * 0.17
        box(f"Parapet{fi}", (L, 0.3, 0.4), (mid.x, mid.y, ZT + 0.45), st, bevel=0.025, rot=(0, 0, ang))
        n = max(2, int(L / 0.7))
        for k in range(0, n + 1, 2):
            c = p + e * (k / n) + inward * 0.17
            box(f"Merlon{fi}{k}", (0.46, 0.34, 0.62), (c.x, c.y, ZT + 0.65 + 0.31), st, bevel=0.03, rot=(0, 0, ang))
        box(f"Coping{fi}", (L + 0.05, 0.38, 0.08), (mid.x, mid.y, ZT + 0.69), dk, bevel=0.015, rot=(0, 0, ang))
    # inside: a crimson window seat, a ceiling, the room behind; a candle on the seat
    seat = [(x * 0.84, y * 0.84 - 0.02) for x, y in plan]
    prism("SeatBoard", seat, ZW, 0.1, dk, plane="XY", bevel=0.02)
    prism("Cushion", [(x * 0.82, y * 0.8) for x, y in plan], ZW + 0.1, 0.18, velvet(), plane="XY", bevel=0.05)
    prism("Ceiling", seat, ZT - 0.15, 0.1, dk, plane="XY")
    for sx in (-1, 1):
        sphere(f"Bolster{sx}", 0.2, (sx * 1.6, -0.5, ZW + 0.42), velvet(), seg=12, rings=6, scale=(0.6, 1.6, 0.8))
    room("Room", [WS.rect(2.9, ZW, ZT)], K, y=-0.03)
    _candle_on("Candle", 0.9, -1.7, ZW + 0.28, K, h=0.36)
    _weather(K, rnd, [(-1.8, -2.55, 0.36), (1.2, -2.58, 0.36), (2.5, -1.2, 0.36)], [((-1.0, -2.47, 1.4), (0.3, 0, -1), 0.8)])
    return _dims()


def lucarne_dormer(M):
    K = kit(M)
    st, dk, iron, gl = K["st"], K["dk"], K["iron"], K["gilt"]
    rnd = random.Random(2310)
    W, D, ZE, ZR, BACK = 4.2, 0.6, 4.7, 7.7, 3.2            # face width, face depth, eaves, ridge, roof run back
    # the stone face pierced by twin trefoil-headed lights, a mullion between
    lights = [WS.arch(0.6, 0.9, 3.75, 4.55, 10, cx=sx * 0.76) for sx in (-1, 1)]
    face = [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, ZE), (0.0, ZR), (-W / 2, ZE)]
    pl = plate("Face", face, -D, 0.0, st)
    pierce(pl, [WS.arch(0.6, 0.6, 3.75, 4.55, 10, cx=sx * 0.76) for sx in (-1, 1)] + [WS.foil_outline(0, 5.75, 0.48, 3, n=48)])
    for k, lt in enumerate(lights):
        cx = (-1, 1)[k] * 0.76
        tube(f"Roll{k}", [(x, -D - 0.02, z) for x, z in WS.offset(lt, 0.05)][1:] + [(cx - 0.65, -D - 0.02, 0.9)], 0.04, dk, square=True, poly=True)
        foil(f"Cusp{k}", cx, -D + 0.02, 4.12, 0.27, dk, lobes=3, thick=0.016, centre=False)
        glass(f"Pane{k}", lt, -0.2, K)
        leads(f"Came{k}_", lt, -0.22, 0.32, K["lead"])
    glass("PaneFoil", WS.foil_outline(0, 5.75, 0.48, 3, n=48), -0.2, K)
    tube("FoilRim", [(x, -D - 0.02, z) for x, z in WS.offset(WS.foil_outline(0, 5.75, 0.48, 3, n=48), 0.04)], 0.035, dk, closed=True, square=True, poly=True)
    box("Sill", (W - 0.4, 0.5, 0.25), (0, -D - 0.15, 0.78), dk, bevel=0.03)
    # piers with pinnacles at the sides, the gable coping with crockets and a finial
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.05)
        box(f"Pier{sx}", (0.56, D + 0.3, ZE + 0.2), (x, -(D + 0.3) / 2 + 0.05, (ZE + 0.2) / 2), dk, bevel=0.035)
        _spirelet(f"Pin{sx}", x, -(D + 0.3) / 2 + 0.05, ZE + 0.2, 1.7, 0.44, st, crockets=3)
    edge = [(-W / 2 - 0.05, ZE + 0.05), (0.0, ZR + 0.08), (W / 2 + 0.05, ZE + 0.05)]
    tube("Coping", [(x, -D / 2 - 0.05, z) for x, z in edge], 0.13, dk, square=True, poly=True)
    for sx in (-1, 1):
        pts = [((sx * (W / 2) * (1 - t)), -D / 2 - 0.05, ZE + 0.2 + (ZR - ZE) * t) for t in (0.18, 0.34, 0.5, 0.66, 0.82)]
        _crockets(f"Crocket{sx}", pts, st, size=0.1)
    _spirelet("Finial", 0, -D / 2 - 0.05, ZR + 0.12, 1.1, 0.3, st, crockets=2)
    sphere("FinialGilt", 0.07, (0, -D / 2 - 0.05, ZR + 1.27), gl, seg=10, rings=5)
    # the roof behind: slate on both pitches, slate-hung cheeks, an iron cresting on the ridge
    sl = K["slate"]
    for sx in (-1, 1):
        a = Vector((sx * (W / 2 + 0.25), -0.02, ZE - 0.12))
        b = Vector((0, -0.02, ZR + 0.02))
        sheet(f"Roof{sx}", [[a, b, b + Vector((0, BACK, 0)), a + Vector((0, BACK, 0))]], sl, 0.08)
        prism(f"Cheek{sx}", [(0.0, 0.0), (BACK, 0.0), (BACK, ZE - 0.15), (0.0, ZE - 0.15)], sx * (W / 2 - 0.05), 0.12, sl, plane="YZ")
        for k in range(1, 9):
            z = ZE - 0.15 - k * 0.5
            if z < 0.2:
                break
            box(f"SlateCourse{sx}{k}", (0.03, BACK - 0.1, 0.03), (sx * (W / 2 + 0.02), BACK / 2, z), sl, bevel=0.0, segments=1)
    tube("Ridge", [(0, 0.0, ZR + 0.06), (0, BACK, ZR + 0.06)], 0.06, K["lead"], poly=True)
    for k in range(7):
        y = 0.3 + k * (BACK - 0.5) / 6
        _spike(f"Crest{k}", (0, y, ZR + 0.25), 0.04, 0.3, iron, verts=4)
        if k < 6:
            hoop(f"CrestRing{k}", (0, y + (BACK - 0.5) / 12, ZR + 0.2), 0.08, "X", iron, thick=0.012)
    set_group("Room")
    B20.tprism("Room", WS.rect(1.6, 0.6, 4.8), 0.6, 0.02, K["room"])
    set_group("Main")
    set_group("Glow")
    sphere("Lamp", 0.07, (-0.5, 0.3, 1.25), flat("LampGlow", (1.0, 0.55, 0.22), 0.5), seg=10, rings=6, scale=(1, 1, 1.3))
    set_group("Main")
    tube("LampStem", [(-0.5, 0.3, 0.9), (-0.5, 0.3, 1.17)], 0.02, K["brass"], poly=True)
    _weather(K, rnd, [(-1.4, -D - 0.3, 0.92), (1.5, -D - 0.32, 0.92)], [((1.6, -D - 0.005, 2.3), (-0.2, 0, -1), 0.7)])
    return _dims()


# ================================================================== tower, door and basement windows

def _courses(prefix, x0, x1, z0, z1, D, mats, rnd, course=0.85, unit=1.3):
    """Coursed ashlar on a wall face from x0 to x1, z0 to z1, D deep (back at y = 0): staggered blocks with joints."""
    out = []
    z, row = z0, 0
    while z < z1 - 0.05:
        h = min(course, z1 - z)
        x = x0
        w0 = unit * (0.5 if row % 2 else 1.0)
        k = 0
        while x < x1 - 0.05:
            w = min(w0 if k == 0 else unit * rnd.uniform(0.85, 1.15), x1 - x)
            if x1 - (x + w) < 0.35:
                w = x1 - x
            d = D + rnd.uniform(-0.02, 0.03)
            ob = box(f"{prefix}{row}_{k}", (w - 0.025, d, h - 0.025), (x + w / 2, -d / 2, z + h / 2), mats[(row + k) % len(mats)], bevel=0.035)
            out.append(ob)
            x += w
            k += 1
        z += h
        row += 1
    return out


def arrow_slit(M):
    K = kit(M)
    st, dk = K["st"], K["dk"]
    rnd = random.Random(2311)
    W, H, D = 2.8, 7.2, 1.1
    blocks = _courses("Ashlar", -W / 2, W / 2, 0.45, H, D, [st, st, dk], rnd, course=0.8, unit=1.4)
    box("Plinth", (W + 0.3, D + 0.25, 0.45), (0, -(D + 0.25) / 2, 0.225), dk, bevel=0.05)
    box("Cap", (W + 0.25, D + 0.2, 0.3), (0, -(D + 0.2) / 2, H + 0.15), dk, bevel=0.04)
    sw, zt, zb, zx, xw = 0.13, 6.2, 1.25, 4.35, 0.75
    cut = [WS.rect(sw, zb, zt), WS.rect(xw, zx - sw, zx + sw)] + [WS.circle(x, z, 0.21, 20) for x, z in ((0, zt), (0, zb), (-xw, zx), (xw, zx))]
    for ob in blocks:
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
        z0, z1 = min(v.z for v in bb), max(v.z for v in bb)
        if x1 > -xw - 0.3 and x0 < xw + 0.3 and z1 > zb - 0.3 and z0 < zt + 0.3:
            pierce(ob, cut)
    # the slice of warm light at the back
    room("Room", [WS.rect(xw + 0.4, zb - 0.45, zt + 0.45)], K, y=-0.04)
    _weather(K, rnd, [(-1.2, -D - 0.2, 0.46), (0.9, -D - 0.22, 0.46), (0.3, -D - 0.05, H + 0.31)],
             [((-0.9, -D - 0.035, 2.6), (0.2, 0, -1), 0.9), ((0.7, -D - 0.035, 5.6), (-0.1, 0, -1), 0.6)])
    return _dims()


def fanlight(M):
    K = kit(M)
    st, dk, iron, brass, gl = K["st"], K["dk"], K["iron"], K["brass"], K["gilt"]
    rnd = random.Random(2312)
    R, ZC, D = 2.0, 0.55, 0.8
    arc = [(math.cos(a) * R, ZC + math.sin(a) * R) for a in [k / 24 * math.pi for k in range(25)]]
    op = WS.ccw([(-R, ZC), (R, ZC)] + arc[1:-1])
    stones("Vous", op, moulded(0.65, D), st, step=0.4, every=2)
    box("Transom", (2 * R + 1.5, D + 0.1, ZC), (0, -(D + 0.1) / 2, ZC / 2), dk, bevel=0.04)
    box("TransomFillet", (2 * R + 1.6, D + 0.22, 0.08), (0, -(D + 0.22) / 2, ZC - 0.04), st, bevel=0.02)
    # the keystone: proud, carrying a crimson shield with a gilt rim and quatrefoil
    kz = ZC + R
    prism("Keystone", [(-0.38, kz + 0.85), (0.38, kz + 0.85), (0.24, kz - 0.06), (-0.24, kz - 0.06)], -(D + 0.12) / 2, D + 0.12, dk, bevel=0.03)
    B20._crest("Shield", 0, -D - 0.14, kz + 0.42, M, gl, s=0.75)
    # the iron sunburst: a petalled half hub, rays to the rim, a rim bar
    yb0, yb1 = -0.38, -0.3
    hub = [(math.cos(a) * 0.55, ZC + math.sin(a) * 0.55) for a in [k / 16 * math.pi for k in range(17)]]
    ribbon("Hub", hub, 0.06, yb0, yb1, iron)
    ribbon("HubBase", [(-R + 0.05, ZC + 0.03), (R - 0.05, ZC + 0.03)], 0.06, yb0, yb1, iron)
    for k in range(7):
        a0, a1 = k / 7 * math.pi, (k + 1) / 7 * math.pi
        am = (a0 + a1) / 2
        petal = [(math.cos(a0) * 0.55, ZC + math.sin(a0) * 0.55), (math.cos(am) * 0.95, ZC + math.sin(am) * 0.95), (math.cos(a1) * 0.55, ZC + math.sin(a1) * 0.55)]
        ribbon(f"Petal{k}", [petal[0], (math.cos(a0 + 0.12) * 0.82, ZC + math.sin(a0 + 0.12) * 0.82), petal[1],
                             (math.cos(a1 - 0.12) * 0.82, ZC + math.sin(a1 - 0.12) * 0.82), petal[2]], 0.045, yb0, yb1, iron)
        if k > 0:
            ribbon(f"Ray{k}", [(math.cos(a0) * 0.55, ZC + math.sin(a0) * 0.55), (math.cos(a0) * (R - 0.05), ZC + math.sin(a0) * (R - 0.05))], 0.05,
                   yb0, yb1, iron)
        ribbon(f"Spoke{k}", [(math.cos(am) * 0.95, ZC + math.sin(am) * 0.95), (math.cos(am) * (R - 0.05), ZC + math.sin(am) * (R - 0.05))], 0.035,
               yb0 + 0.01, yb1, iron)
    ribbon("Rim", [(math.cos(a) * (R - 0.04), ZC + math.sin(a) * (R - 0.04)) for a in [k / 32 * math.pi for k in range(33)]], 0.07, yb0, yb1, iron)
    ribbon("MidRing", [(math.cos(a) * 1.42, ZC + math.sin(a) * 1.42) for a in [k / 24 * math.pi for k in range(25)]], 0.035, yb0 - 0.01, yb1, iron)
    sphere("Boss", 0.17, (0, yb0 - 0.05, ZC + 0.08), brass, seg=14, rings=6, scale=(1, 0.5, 1))
    glass("Pane", op, -0.26, K)
    room("Room", [op], K)
    _weather(K, rnd, [(-2.2, -D - 0.12, ZC + 0.02), (1.9, -D - 0.12, ZC + 0.02)], [((R + 0.35, -D - 0.035, 1.6), (0.3, 0, -1), 0.6)])
    return _dims()


def basement_grate(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2314)
    W, H, D = 5.4, 3.0, 0.9
    HW, Z0, ZS, RISE = 1.75, 0.65, 1.95, 0.35
    op = WS.segmental(HW, Z0, ZS, RISE, 12)
    # a rusticated plinth: big chamfered blocks, the opening's voussoir head and jambs cut from them
    blocks = _courses("Rustic", -W / 2, W / 2, 0.0, H, D, [st, dk, st], rnd, course=1.0, unit=1.8)
    for ob in blocks:
        pierce(ob, [WS.offset(WS.ccw(op), 0.62)])
    stones("Jamb", op, JAMB(0.62, D + 0.08, 0.12), dk, step=0.45, every=2)
    box("Coping", (W + 0.2, D + 0.25, 0.25), (0, -(D + 0.25) / 2, H + 0.12), dk, bevel=0.04)
    # heavy bars: seven uprights through two rivetted flat bars, leaded into the stone
    yb = -0.5
    big = WS.offset(WS.ccw(op), 0.15)
    for k in range(7):
        x = -HW + (k + 0.5) * 2 * HW / 7
        for a, b in WS.clip_line((x, 0.0), (0.0, 1.0), big):
            tube(f"Bar{k}", [(x, yb, a[1]), (x, yb, b[1])], 0.055, iron, poly=True)
            sphere(f"Caulk{k}", 0.09, (x, yb, a[1] + 0.06), K["lead"], seg=8, rings=4, scale=(1, 1, 0.5))
    for j, z in enumerate((1.05, 1.75)):
        box(f"Flat{j}", (2 * HW + 0.3, 0.05, 0.13), (0, yb - 0.07, z), iron, bevel=0.01)
        for k in range(7):
            x = -HW + (k + 0.5) * 2 * HW / 7
            sphere(f"Rivet{j}{k}", 0.035, (x, yb - 0.1, z), iron, seg=8, rings=4)
    glass("Pane", op, -0.22, K)
    room("Room", [op], K)
    # rust running down under the bars, moss at the foot
    for k in range(3):
        x = -HW + (k * 3 + 1.5) * 2 * HW / 7
        _stain(f"Rust{k}", (x, -D - 0.06, Z0 - 0.35), (1, 0, 0), (0, 0, -1), 0.08, 0.35, K["rust"], rnd)
    _weather(K, rnd, [(-2.3, -D - 0.05, 0.05), (-0.4, -D - 0.06, 0.05), (1.9, -D - 0.05, 0.05), (0.8, -D - 0.1, H + 0.25)],
             [((-2.0, -D - 0.035, 2.2), (0.25, 0, -1), 0.8)])
    return _dims()


# ================================================================== broken and shuttered

def broken_window(M):
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2315)
    HW, Z0, ZS, ZA = 1.2, 0.75, 5.0, 6.8
    D = 0.75
    op = WS.arch(HW, Z0, ZS, ZA, 12)
    stones("Jamb", op, JAMB(0.6, D, 0.16), st, step=0.5)
    sill("Sill", 2 * HW + 1.6, Z0, dk)
    hood("Hood", HW + 0.72, ZS, ZA + 0.85, -D - 0.07, dk, dk, st)
    # the leaded glass, smashed through round hc: whole diamonds, shards round the hole, none inside it
    hc, R1, R2 = (0.25, 3.3), 0.62, 1.0
    yg = -0.3
    step = 0.36
    a = math.radians(62)
    u1, u2 = (math.cos(a), math.sin(a)), (-math.cos(a), math.sin(a))
    # the diamond cells of the same lattice the cames use (centred like WS.lattice_lines)
    xs = [p[0] for p in op]
    zs = [p[1] for p in op]
    cx0, cz0 = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    n1, n2 = (-u1[1], u1[0]), (-u2[1], u2[0])
    det = n1[0] * n2[1] - n1[1] * n2[0]
    set_group("Glass")
    k = 0
    for i in range(-16, 17):
        for j in range(-16, 17):
            def at(s, t):
                # the point whose distance along n1 is s * step and along n2 is t * step from the centre
                return (cx0 + (s * step * n2[1] - t * step * n1[1]) / det, cz0 + (t * step * n1[0] - s * step * n2[0]) / det)
            cell = [at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)]
            cell = WS.clip_convex(WS.ccw(cell), WS.ccw(op))
            if len(cell) < 3 or abs(WS.area(cell)) < 0.004:
                continue
            c = (sum(p[0] for p in cell) / len(cell), sum(p[1] for p in cell) / len(cell))
            dd = math.hypot(c[0] - hc[0], c[1] - hc[1])
            if dd < R1:
                continue
            if dd < R2:
                # a shard: keep the cell's far side, the near side broken off along a jagged line
                far = sorted(cell, key=lambda p: -math.hypot(p[0] - hc[0], p[1] - hc[1]))
                keep = WS.ccw([far[0], far[1], ((far[0][0] + c[0]) / 2 + rnd.uniform(-0.04, 0.04), (far[0][1] + c[1]) / 2 + rnd.uniform(-0.04, 0.04))])
                if rnd.random() < 0.3:
                    continue
                cell = keep
            B20.tprism(f"Shard{k}", cell, yg, 0.02, K["glass"])
            k += 1
    # broken glass on the sill
    for j in range(9):
        x, y = rnd.uniform(-HW, HW), rnd.uniform(-0.7, -0.32)
        s = rnd.uniform(0.07, 0.16)
        tri = [(x, y), (x + s, y + rnd.uniform(-0.05, 0.05)), (x + rnd.uniform(0, s), y + s * rnd.uniform(0.6, 1.2))]
        prism(f"SillShard{j}", tri, Z0 + SILL_UP + 0.002, 0.012, K["glass"], plane="XY")
    set_group("Main")
    hole = lambda p: math.hypot(p[0] - hc[0], p[1] - hc[1]) < R1 * 0.95
    leads("Came", op, yg - 0.02, step, K["lead"], skip=hole)
    # bent came stubs dangling into the hole
    for j in range(5):
        a0 = rnd.uniform(0, 2 * math.pi)
        p = (hc[0] + math.cos(a0) * R1, hc[1] + math.sin(a0) * R1)
        tube(f"BentCame{j}", [(p[0], yg - 0.02, p[1]), (p[0] - math.cos(a0) * 0.18, yg - 0.08, p[1] - math.sin(a0) * 0.18 - 0.06),
                              (p[0] - math.cos(a0) * 0.26, yg - 0.16, p[1] - math.sin(a0) * 0.2 - 0.16)], 0.011, K["lead"])
    saddle_bars("Saddle", op, (1.9, 3.0, 4.1), yg - 0.045, iron)
    # two boards nailed across (the only wood in the kit), grey and split with age
    board = material("BoardWorn", "NH_DeskWood", tint=(0.2, 0.17, 0.15), scale=0.25, rough_add=0.15, wear=0.6, dirt=0.9)
    for k, (zc, ang) in enumerate(((2.55, 0.42), (4.15, -0.32))):
        L = 2 * HW + 1.1
        box(f"Board{k}", (L, 0.07, 0.4), (0.05, -D - 0.06 - k * 0.07, zc), board, bevel=0.015, rot=(0, ang, 0))
        for sx in (-1, 1):
            x = sx * (L / 2 - 0.2) * math.cos(ang)
            z = zc - sx * (L / 2 - 0.2) * math.sin(ang)
            for dz in (-0.1, 0.1):
                sphere(f"Nail{k}{sx}{dz}", 0.028, (x + 0.05, -D - 0.1 - k * 0.07, z + dz), iron, seg=8, rings=4, scale=(1, 0.5, 1))
    room("Room", [op], K)
    _weather(K, rnd, [(-1.4, -0.85, Z0 + 0.02), (1.3, -0.9, Z0 + 0.02), (-HW - 1.0, -D - 0.12, ZS - 0.02), (0.6, -D - 0.05, 0.45)],
             [((-HW - 0.3, -D - 0.005, 2.0), (0.3, 0, -1), 1.0), ((HW + 0.4, -D - 0.005, 4.4), (-0.2, 0, -1), 0.8)])
    return _dims()


def shuttered_window(M):
    K = kit(M)
    st, dk, iron, brass, en = K["st"], K["dk"], K["iron"], K["brass"], K["enamel"]
    rnd = random.Random(2316)
    HW, Z0, ZS, RISE = 1.4, 0.8, 5.5, 0.42
    D = 0.75
    op = WS.segmental(HW, Z0, ZS, RISE, 14)
    o = stones("Jamb", op, JAMB(0.6, D, 0.12), st, step=0.5)
    sill("Sill", 2 * HW + 1.6, Z0, dk)
    hx = HW + 0.75
    hood_pts = [(x, z) for x, z in WS.offset(WS.ccw(op), 0.75) if z > ZS - 0.05]
    hood_pts = sorted(hood_pts, key=lambda p: p[0])
    tube("Hood", [(-hx - 0.25, -D - 0.08, ZS - 0.02)] + [(x, -D - 0.08, z) for x, z in hood_pts] + [(hx + 0.25, -D - 0.08, ZS - 0.02)], 0.09, dk,
         square=True, poly=True)
    for sx in (-1, 1):
        box(f"HoodDrop{sx}", (0.3, 0.32, 0.45), (sx * (hx + 0.25), -D - 0.04, ZS - 0.25), dk, bevel=0.03)
    # the shutters: each leaf a crimson enamel iron plate (lower panel louvred, upper pierced by a crescent moon) in
    # a frame of stiles and rails
    yp0, yp1 = -0.5, -0.42
    zmid = 2.85
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.015, sx * (HW - 0.02)))
        top = [p for p in WS.offset(WS.ccw(op), -0.02) if p[1] > ZS - 0.01 and x0 - 0.01 <= p[0] <= x1 + 0.01]
        top = sorted(top, key=lambda p: -p[0])
        leaf = WS.ccw([(x0, zmid), (x1, zmid)] + top)
        lc = (x0 + x1) / 2
        pl = plate(f"UpperPlate{sx}", leaf, yp0, yp1, en)
        moon = WS.crescent(lc, 4.05, 0.42, tilt=(0.4 if sx < 0 else math.pi - 0.4))
        pierce(pl, [moon])
        tube(f"MoonRim{sx}", [(x, yp0 - 0.015, z) for x, z in WS.offset(moon, 0.02)], 0.02, brass, closed=True, square=True, poly=True)
        loopbar(f"LeafFrame{sx}", WS.ccw([(x0, Z0 + 0.02), (x1, Z0 + 0.02)] + top), 0.16, yp0 - 0.06, yp1, en)
        ribbon(f"MidRail{sx}", [(x0, zmid), (x1, zmid)], 0.16, yp0 - 0.06, yp1, en)
        # louvres in the lower panel, a dark slot behind them
        plate(f"LouvreBack{sx}", WS.rect((x1 - x0) / 2 - 0.05, Z0 + 0.1, zmid - 0.05, cx=lc), -0.3, -0.28, K["hollow"])
        n = 9
        for k in range(n):
            z = Z0 + 0.16 + (k + 0.5) * (zmid - Z0 - 0.26) / n
            box(f"Louvre{sx}{k}", ((x1 - x0) - 0.16, 0.03, 0.24), (lc, -0.42, z), en, bevel=0.006, rot=(0.8, 0, 0), segments=1)
        # strap hinges onto pintles in the jambs, rivets
        for zz in (Z0 + 0.55, ZS - 0.45):
            xo = sx * (HW - 0.05)
            tube(f"Strap{sx}{zz:.1f}", [(xo, yp0 - 0.08, zz), (xo - sx * 0.8, yp0 - 0.08, zz)], 0.035, iron, square=True, poly=True)
            _spike(f"StrapTip{sx}{zz:.1f}", (xo - sx * 0.86, yp0 - 0.08, zz), 0.07, 0.14, iron, verts=4, rot=(0, -sx * math.pi / 2, 0))
            cyl(f"Pintle{sx}{zz:.1f}", 0.05, 0.3, (sx * (HW + 0.06), yp0 - 0.08, zz), iron, verts=10, bevel=0.0)
            for r in range(3):
                sphere(f"Rivet{sx}{zz:.1f}{r}", 0.028, (xo - sx * (0.15 + r * 0.22), yp0 - 0.11, zz), iron, seg=6, rings=3)
    # the drop bar across both leaves in two iron keepers, a brass ring pull
    zb = 2.4
    box("DropBar", (2 * HW + 0.2, 0.08, 0.14), (0, yp0 - 0.18, zb), iron, bevel=0.012)
    for sx in (-1, 1):
        tube(f"Keeper{sx}", [(sx * 1.15, yp0 - 0.06, zb - 0.12), (sx * 1.15, yp0 - 0.25, zb - 0.12), (sx * 1.15, yp0 - 0.25, zb + 0.12),
                             (sx * 1.15, yp0 - 0.06, zb + 0.12)], 0.022, iron, square=True, poly=True)
    cyl("PullRose", 0.09, 0.03, (0.18, yp0 - 0.08, 3.25), brass, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.006)
    hoop("PullRing", (0.18, yp0 - 0.12, 3.12), 0.12, "Y", brass, thick=0.018)
    room("Room", [op], K)
    _weather(K, rnd, [(-1.5, -0.85, Z0 + 0.02), (1.4, -0.9, Z0 + 0.02)], [((HW + 0.3, -D - 0.005, 3.2), (-0.2, 0, -1), 0.8)])
    return _dims()


# ================================================================== regular clear windows (plain glass, no lead)

def _plain_frame(prefix, region, K, y0=-0.4, y1=-0.28, w=0.1):
    """A black iron frame round a light, its clear pane just behind."""
    loopbar(f"{prefix}Frame", WS.offset(WS.ccw(region), -w / 2), w, y0, y1, K["iron"])
    glass(f"{prefix}Pane", region, y1 + 0.015, K)


def _lintel(prefix, hw, z, D, K, n=5, key=True):
    """A flat stone lintel over a square-headed opening: n jointed stones, a proud keystone in the middle."""
    w = 2 * hw + 1.2
    for k in range(n):
        x0 = -w / 2 + k * w / n
        big = key and k == n // 2
        dd = D + 0.08 + (0.1 if big else 0)       # proud of the jamb ring's head, so their faces never share a plane
        box(f"{prefix}{k}", (w / n - 0.025, dd, 0.66 + (0.14 if big else 0)), (x0 + w / n / 2, -dd / 2, z + 0.31 + (0.04 if big else 0)),
            K["dk"] if big else K["st"], bevel=0.035)


def plain_sash(M):
    """A plain two-over-two sash: clear panes, black iron sashes, a stone architrave with a flat lintel."""
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2317)
    HW, Z0, Z1, D = 1.3, 0.8, 6.0, 0.65
    op = WS.rect(HW, Z0, Z1)
    stones("Jamb", op, JAMB(0.5, D, 0.1), st, step=0.55)
    _lintel("Lintel", HW, Z1, D, K)
    sill("Sill", 2 * HW + 1.3, Z0, dk)
    zm = (Z0 + Z1) / 2
    for k, (za, zb, y0, y1) in enumerate(((Z0 + 0.05, zm + 0.05, -0.42, -0.32), (zm - 0.05, Z1 - 0.05, -0.32, -0.22))):
        reg = WS.rect(HW - 0.05, za, zb)
        _plain_frame(f"Sash{k}", reg, K, y0, y1, w=0.12)
        ribbon(f"SashBar{k}", [(0, za + 0.05), (0, zb - 0.05)], 0.05, y0 + 0.01, y1, iron)
    box("MeetingRail", (2 * HW - 0.1, 0.12, 0.12), (0, -0.37, zm), iron, bevel=0.01)
    box("Lock", (0.24, 0.04, 0.07), (0, -0.44, zm + 0.07), brass, bevel=0.008)
    for sx in (-1, 1):
        tube(f"Lift{sx}", [(sx * 0.65 - 0.06, -0.43, Z0 + 0.22), (sx * 0.65, -0.48, Z0 + 0.22), (sx * 0.65 + 0.06, -0.43, Z0 + 0.22)], 0.014, brass)
    room("Room", [op], K)
    _weather(K, rnd, [(-1.4, -0.8, Z0 + SILL_UP), (1.3, -0.82, Z0 + SILL_UP)])
    return _dims()


def cross_window(M):
    """A stone cross window: a mullion and a transom dividing four clear lights, iron casements, a square hood mould."""
    K = kit(M)
    st, dk, iron, brass = K["st"], K["dk"], K["iron"], K["brass"]
    rnd = random.Random(2318)
    HW, Z0, Z1, D = 1.6, 0.8, 6.4, 0.75
    zt = Z0 + (Z1 - Z0) * 0.68
    op = WS.rect(HW, Z0, Z1)
    stones("Jamb", op, moulded(0.55, D), st, step=0.55)
    sill("Sill", 2 * HW + 1.5, Z0, dk)
    ribbon("Mullion", [(0, Z0 - 0.05), (0, Z1 + 0.05)], 0.26, -D + 0.05, 0.0, st)
    ribbon("Transom", [(-HW - 0.05, zt), (HW + 0.05, zt)], 0.26, -D + 0.05, 0.0, st)
    yh = -D - 0.1
    tube("Hood", [(-HW - 0.75, yh, Z1 - 0.6), (-HW - 0.75, yh, Z1 + 0.62), (HW + 0.75, yh, Z1 + 0.62), (HW + 0.75, yh, Z1 - 0.6)], 0.09, dk, square=True,
         poly=True)
    for sx in (-1, 1):
        box(f"HoodStop{sx}", (0.3, 0.3, 0.3), (sx * (HW + 0.75), yh + 0.04, Z1 - 0.72), dk, bevel=0.03)
        foil(f"HoodFoil{sx}", sx * (HW + 0.75), yh - 0.12, Z1 - 0.72, 0.08, st, lobes=4, thick=0.012)
    for k, (x0, x1, za, zb) in enumerate(((-HW, -0.13, Z0, zt - 0.13), (0.13, HW, Z0, zt - 0.13), (-HW, -0.13, zt + 0.13, Z1), (0.13, HW, zt + 0.13, Z1))):
        reg = WS.rect((x1 - x0) / 2 - 0.02, za + 0.02, zb - 0.02, cx=(x0 + x1) / 2)
        _plain_frame(f"Light{k}", reg, K, w=0.09)
        if k < 2:
            ribbon(f"Bar{k}", [(x0 + 0.06, (za + zb) / 2), (x1 - 0.06, (za + zb) / 2)], 0.04, -0.39, -0.28, iron)
            box(f"Catch{k}", (0.05, 0.04, 0.2), ((0.22 if k else -0.22), -0.43, (za + zb) / 2 + 0.3), brass, bevel=0.008)
    room("Room", [op], K)
    _weather(K, rnd, [(-1.6, -0.85, Z0 + SILL_UP), (1.5, -0.88, Z0 + SILL_UP)], [((HW + 0.3, -D - 0.035, 2.6), (-0.2, 0, -1), 0.7)])
    return _dims()


def picture_window(M):
    """A wide window with one big clear pane in a slim iron frame: a stone surround, a lintel, a long sill."""
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2319)
    HW, Z0, Z1, D = 2.4, 1.0, 4.8, 0.65
    op = WS.rect(HW, Z0, Z1)
    stones("Jamb", op, JAMB(0.5, D, 0.1), st, step=0.6, every=2)
    _lintel("Lintel", HW, Z1, D, K, n=7)
    sill("Sill", 2 * HW + 1.3, Z0, dk, depth=0.9)
    for sx in (-1, 1):
        box(f"SillBracket{sx}", (0.32, 0.4, 0.34), (sx * (HW + 0.2), -0.55, Z0 - 0.5), dk, bevel=0.03)
    _plain_frame("Big", WS.rect(HW - 0.03, Z0 + 0.02, Z1 - 0.02), K, w=0.14)
    room("Room", [op], K)
    _weather(K, rnd, [(-2.4, -0.8, Z0 + SILL_UP), (2.0, -0.78, Z0 + SILL_UP)])
    return _dims()


def round_arch_window(M):
    """A round-arched window: voussoirs and a keystone, a transom at the springing, three bars fanning in the head,
    two clear lights below."""
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2320)
    HW, Z0, ZS, D = 1.25, 0.8, 4.7, 0.7
    op = WS.roundhead(HW, Z0, ZS, 16)
    stones("Vous", op, moulded(0.55, D), st, step=0.42, every=2)
    prism("Keystone", [(-0.26, ZS + HW + 0.78), (0.26, ZS + HW + 0.78), (0.17, ZS + HW - 0.04), (-0.17, ZS + HW - 0.04)], -(D + 0.12) / 2, D + 0.12, dk,
          bevel=0.03)
    sill("Sill", 2 * HW + 1.4, Z0, dk)
    yf0, yf1 = -0.4, -0.28
    loopbar("Frame", WS.offset(WS.ccw(op), -0.06), 0.12, yf0, yf1, iron)
    ribbon("Transom", [(-HW + 0.06, ZS), (HW - 0.06, ZS)], 0.1, yf0, yf1, iron)
    ribbon("Mullion", [(0, Z0 + 0.06), (0, ZS)], 0.1, yf0, yf1, iron)
    for k, a in enumerate((math.pi / 4, math.pi / 2, 3 * math.pi / 4)):
        ribbon(f"Fan{k}", [(math.cos(a) * 0.3, ZS + math.sin(a) * 0.3), (math.cos(a) * (HW - 0.08), ZS + math.sin(a) * (HW - 0.08))], 0.05, yf0, yf1, iron)
    ribbon("FanHub", [(math.cos(a) * 0.3, ZS + math.sin(a) * 0.3) for a in [k / 10 * math.pi for k in range(11)]], 0.05, yf0, yf1, iron)
    glass("Pane", op, yf1 + 0.015, K)
    room("Room", [op], K)
    _weather(K, rnd, [(-1.3, -0.82, Z0 + SILL_UP), (1.2, -0.84, Z0 + SILL_UP)], [((-HW - 0.3, -D - 0.035, 3.0), (0.2, 0, -1), 0.7)])
    return _dims()


def square_window(M):
    """A small square four-pane window for a corridor or a stair landing: a chamfered stone frame, an iron cross."""
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2321)
    HW, Z0, Z1, D = 0.95, 1.2, 3.1, 0.6
    op = WS.rect(HW, Z0, Z1)
    stones("Frame", op, JAMB(0.45, D, 0.12), st, step=0.5, every=2)
    sill("Sill", 2 * HW + 1.1, Z0, dk, depth=0.85, h=0.3)
    _plain_frame("Sq", op, K, w=0.1)
    ribbon("CrossV", [(0, Z0 + 0.05), (0, Z1 - 0.05)], 0.06, -0.39, -0.28, iron)
    ribbon("CrossH", [(-HW + 0.05, (Z0 + Z1) / 2), (HW - 0.05, (Z0 + Z1) / 2)], 0.06, -0.39, -0.28, iron)
    room("Room", [op], K)
    _weather(K, rnd, [(-0.9, -0.75, Z0 + SILL_UP), (0.8, -0.72, Z0 + SILL_UP)])
    return _dims()


def half_round_window(M):
    """A half-circle window (a lunette): a semicircle of moulded voussoirs with a keystone on a long sill, split by two
    stone mullions into three clear lights in slim iron frames, a glazing bar across each."""
    K = kit(M)
    st, dk, iron = K["st"], K["dk"], K["iron"]
    rnd = random.Random(2322)
    R, Z0, D = 2.5, 0.8, 0.75
    n = 28
    op = [(math.cos(k / n * math.pi) * R, Z0 + math.sin(k / n * math.pi) * R) for k in range(n + 1)]    # right foot, over, left foot
    stones("Vous", op, moulded(0.65, D), st, step=0.45, every=2)
    kz = Z0 + R
    prism("Keystone", [(-0.3, kz + 0.9), (0.3, kz + 0.9), (0.2, kz - 0.05), (-0.2, kz - 0.05)], -(D + 0.12) / 2, D + 0.12, dk, bevel=0.03)
    foil("KeyFoil", 0, -D - 0.14, kz + 0.5, 0.1, st, lobes=4, thick=0.013)
    sill("Sill", 2 * R + 1.9, Z0, dk)
    # two stone mullions dividing the half circle in three
    xm = R / 3
    big = WS.offset(WS.ccw(op), 0.1)
    for sx in (-1, 1):
        for a, b in WS.clip_line((sx * xm, 0.0), (0.0, 1.0), big):
            ribbon(f"Mullion{sx}", [(sx * xm, a[1]), (sx * xm, b[1])], 0.24, -D + 0.08, 0.0, st)
        box(f"MullionBase{sx}", (0.36, 0.42, 0.22), (sx * xm, -D + 0.25, Z0 + SILL_UP + 0.11), dk, bevel=0.025)
    # the three lights: an iron frame round each, a glazing bar across, clear glass, the room behind
    yf0, yf1 = -0.42, -0.3
    inner = WS.offset(WS.ccw(op), -0.02)
    for k, (x0, x1) in enumerate(((-R, -xm - 0.12), (-xm + 0.12, xm - 0.12), (xm + 0.12, R))):
        light = WS.clip_convex(inner, WS.rect((x1 - x0) / 2, Z0 - 0.5, Z0 + R + 1, cx=(x0 + x1) / 2))
        loopbar(f"Frame{k}", WS.offset(WS.ccw(light), -0.045), 0.09, yf0, yf1, iron)
        zb = Z0 + (R * 0.42 if k == 1 else R * 0.33)
        for a, b in WS.clip_line((0.0, zb), (1.0, 0.0), light):
            ribbon(f"Bar{k}", [(a[0] + 0.05, zb), (b[0] - 0.05, zb)], 0.045, yf0 + 0.01, yf1, iron)
    glass("Pane", op, yf1 + 0.015, K)
    room("Room", [op], K)
    _weather(K, rnd, [(-2.2, -0.85, Z0 + SILL_UP), (0.4, -0.9, Z0 + SILL_UP), (2.1, -0.86, Z0 + SILL_UP)],
             [((R + 0.4, -D - 0.035, 1.6), (-0.3, 0, -1), 0.7)])
    return _dims()


# ================================================================== the conservatory: the gothic crown

NB = 8                     # bays round the glass hall (bay 0, the doorway, faces the front, -Y)
RD = 6.5                   # the hall's corner circle
RP = 8.6                   # the spire piers' circle
ZB, ZD, ZE = 1.8, 9.0, 9.65  # the hall's stone base wall top, its head (entablature foot), the crown dome's springing
RC, ZAPEX = 6.35, 20.6     # the crown dome's corner radius at the springing and the apex of its pointed profile
RL = 0.75                  # where the dome stops and the openwork spire starts


def _corner(k, n=NB):
    """Angle of hall corner k; bay k runs from corner k to corner k + 1."""
    return -math.pi / 2 - math.pi / n + k * 2 * math.pi / n


def _bay(k, r=RD, n=NB):
    """The matrix placing a bay built in the usual frame (across x, front -Y = outward, z up) on a ring of corner radius r."""
    ac = -math.pi / 2 + k * 2 * math.pi / n
    ra = r * math.cos(math.pi / n)
    return Matrix.Translation((math.cos(ac) * ra, math.sin(ac) * ra, 0)) @ _rotz(ac + math.pi / 2)


def _radial(s0, a):
    """Turn the parts built since s0 in the XZ plane (x = radius out from the centre) to face along the angle a."""
    _xform(s0, _rotz(a))


def _ring_plan(prefix, r0, r1, z, h, mat, skip=(), n=NB, a0=None):
    """An n-sided ring in plan from (corner) radius r0 to r1, z to z + h (a prism per side, the sides in skip left open)."""
    for k in range(n):
        if k in skip:
            continue
        a, b = (_corner(k, n), _corner(k + 1, n)) if a0 is None else (a0 + k * 2 * math.pi / n, a0 + (k + 1) * 2 * math.pi / n)
        poly = [(math.cos(a) * r0, math.sin(a) * r0), (math.cos(a) * r1, math.sin(a) * r1), (math.cos(b) * r1, math.sin(b) * r1),
                (math.cos(b) * r0, math.sin(b) * r0)]
        prism(f"{prefix}{k}", poly, z, h, mat, plane="XY", bevel=0.0)


def _dome_profile():
    """(r, z) up a crown-dome corner rib from the springing: one side of a steep pointed arch, cut where r = RL."""
    pts = [(-x, z) for x, z in WS.pointed(RC, ZE, ZAPEX, 26)[:27]]
    out = []
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        out.append((r0, z0))
        if r1 < RL:
            t = (r0 - RL) / (r0 - r1)
            out.append((RL, z0 + (z1 - z0) * t))
            break
    return out


def _at(r, a, z):
    return (math.cos(a) * r, math.sin(a) * r, z)


def conservatory_dome(M):
    K = kit(M)
    st, dk, iron, brass, gl, en = K["st"], K["dk"], K["iron"], K["brass"], K["gilt"], K["enamel"]
    rnd = random.Random(2330)
    wall = K["st"]
    # ---- the platform, the hall's low stone base wall and the floor (tiled castle stone, see TILED below)
    set_group("Wall")
    prism("Platform", [_at(9.45, -math.pi / 2 - math.pi / 16 + k * math.pi / 8, 0)[:2] for k in range(16)], 0.0, 0.4, wall, plane="XY")
    _ring_plan("BaseWall", RD - 0.45, RD + 0.25, 0.4, ZB - 0.4, wall, skip=(0,))
    set_group("Floor")
    prism("Floor", [(math.cos(a) * (RD - 0.4), math.sin(a) * (RD - 0.4)) for a in [_corner(k) for k in range(NB)]], 0.4, 0.06, wall, plane="XY")
    set_group("Main")
    _ring_plan("PlatformEdge", 9.4, 9.6, 0.0, 0.42, dk, n=16, a0=-math.pi / 2 - math.pi / 16)
    _ring_plan("BaseCap", RD - 0.5, RD + 0.34, ZB - 0.02, 0.16, dk, skip=(0,))
    # ---- the hall: clustered iron columns at the corners, a tall two-light lancet in every bay but the doorway's
    for k in range(NB):
        a = _corner(k)
        x, y, _ = _at(RD, a, 0)
        cyl(f"Col{k}", 0.2, ZD - 0.4 - 0.3, (x, y, (0.4 + ZD - 0.3) / 2), iron, verts=12, bevel=0.0)
        for j, da in enumerate((-0.035, 0.035)):
            cyl(f"ColShaft{k}{j}", 0.07, ZD - 0.8, (*_at(RD + 0.16, a + da, 0)[:2], (0.4 + ZD - 0.3) / 2), iron, verts=8, bevel=0.0)
        box(f"ColBase{k}", (0.6, 0.6, 0.3), (x, y, 0.55), iron, bevel=0.015, rot=(0, 0, a), segments=1)
        lathe(f"ColCap{k}", [(0, ZD - 0.5), (0.2, ZD - 0.5), (0.3, ZD - 0.34), (0.36, ZD - 0.18), (0.36, ZD - 0.04), (0, ZD - 0.04)], gl, seg=10,
              loc=(x, y, 0))
    ch = RD * math.sin(math.pi / NB)                     # half the bay's chord
    set_group("Drum")
    glass_bays = []
    for k in range(NB):
        s0 = _mark()
        if k == 0:
            door = WS.arch(1.3, 0.0, 4.9, 6.4, 12)
            sp = plate("Spandrel0", WS.rect(ch - 0.02, 4.8, ZD), -0.05, 0.05, en)
            pierce(sp, [door, WS.circle(0, 7.55, 0.62, 24)])
            loopbar("DoorRose", WS.circle(0, 7.55, 0.62, 24), 0.09, -0.08, 0.08, iron)
            loopbar("DoorRoseFoil", WS.foil_outline(0, 7.55, 0.52, 6, n=48), 0.05, -0.06, 0.06, iron)
            loopbar("DoorFrame", door[1:] + [(-1.3, 0.0)], 0.1, -0.1, 0.1, iron)
            glass_bays.append((k, WS.circle(0, 7.55, 0.62, 24)))
        else:
            L = WS.arch(ch - 0.24, ZB + 0.08, 7.2, 8.85, 10)
            loopbar(f"Lancet{k}", L, 0.12, -0.07, 0.07, iron)
            ribbon(f"Sill{k}", [(-ch, ZB + 0.05), (ch, ZB + 0.05)], 0.12, -0.09, 0.09, iron)
            ribbon(f"Mull{k}", [(0, ZB + 0.1), (0, 7.2)], 0.09, -0.06, 0.06, iron)
            hw2 = (ch - 0.24) / 2
            for sx in (-1, 1):
                ribbon(f"Sub{k}{sx}", [(sx * hw2 + x, z) for x, z in WS.pointed(hw2, 7.2 - 0.85, 7.85, 7)], 0.06, -0.05, 0.05, iron)
                loopbar(f"SubFoil{k}{sx}", WS.foil_outline(sx * hw2, 7.42, hw2 * 0.55, 3, n=30), 0.035, -0.04, 0.04, iron)
            for z in (3.6, 5.3):
                ribbon(f"Transom{k}{z}", [(-ch + 0.25, z), (ch - 0.25, z)], 0.05, -0.04, 0.04, iron)
            loopbar(f"Roundel{k}", WS.circle(0, 8.28, 0.36, 18), 0.06, -0.05, 0.05, iron)
            loopbar(f"RoundelFoil{k}", WS.foil_outline(0, 8.28, 0.3, 4, n=32, a0=math.pi / 4), 0.035, -0.04, 0.04, iron)
            sp = plate(f"Spandrel{k}", WS.rect(ch - 0.02, 7.1, ZD), -0.03, 0.03, en)
            pierce(sp, [WS.offset(WS.ccw(L), -0.03)])
            glass_bays.append((k, L))
        _xform(s0, _bay(k))
    # a hanging iron corona of candles under the crown
    zc = 13.2
    tube("Chain", [(0, 0, 17.4), (0, 0, zc + 1.0)], 0.03, iron, poly=True)
    for k in range(4):
        a = k * math.pi / 2
        tube(f"Strap{k}", [(0, 0, zc + 1.0), _at(1.3, a, zc + 0.02)], 0.02, iron, poly=True)
    hoop("Corona", (0, 0, zc), 1.3, "Z", iron, thick=0.05)
    hoop("CoronaGilt", (0, 0, zc - 0.09), 1.3, "Z", gl, thick=0.022)
    sphere("CoronaBoss", 0.18, (0, 0, zc + 1.0), gl, seg=12, rings=6)
    flames = []
    for k in range(8):
        x, y, _ = _at(1.3, k / 8 * 2 * math.pi, 0)
        lathe(f"Cup{k}", [(0, zc), (0.09, zc), (0.1, zc + 0.04), (0.07, zc + 0.06), (0, zc + 0.06)], brass, seg=10, loc=(x, y, 0))
        tip = candle(f"Candle{k}", x, y, zc + 0.06, 0.32, wax_mat(), r=0.04)
        flames.append((x, y, tip))
    set_group("Main")
    # ---- the hall's head: an iron band, a crimson enamel frieze with gilt bosses, a cornice
    _ring_plan("Band", RD - 0.25, RD + 0.4, ZD, 0.25, iron)
    _ring_plan("Frieze", RD - 0.2, RD + 0.32, ZD + 0.25, 0.18, en)
    _ring_plan("Cornice", RD - 0.3, RD + 0.55, ZD + 0.43, ZE - ZD - 0.43, iron)
    for k in range(NB):
        for j in range(3):
            a = _corner(k) + (j + 0.5) / 3 * 2 * math.pi / NB
            r = RD * math.cos(math.pi / NB) / math.cos(a - (_corner(k) + math.pi / NB)) + 0.33
            sphere(f"Boss{k}{j}", 0.08, _at(r, a, ZD + 0.34), gl, seg=8, rings=4, scale=(1, 1, 0.8))
    # ---- the eight spire piers: stepped soot-stone piers with a blind lancet, crocketed pinnacles, gilt finials
    set_group("Spires")
    for k in range(NB):
        a = _corner(k)
        s0 = _mark()
        w = 0.95
        box(f"PierFoot{k}", (w + 0.3, w + 0.3, 0.6), (RP, 0, 0.7), dk, bevel=0.04)
        box(f"Pier{k}", (w, w, 9.0), (RP, 0, 0.4 + 4.5), st, bevel=0.04)
        for j, z in enumerate((3.4, 6.4)):
            box(f"PierSet{k}{j}", (w + 0.16, w + 0.16, 0.26), (RP, 0, z), dk, bevel=0.03)
        _spirelet(f"PierPin{k}", RP, 0, 9.4, 3.4, w * 0.8, st, crockets=2)
        sphere(f"PierGilt{k}", 0.08, (RP, 0, 9.4 + 3.4 + 0.1), gl, seg=10, rings=5)
        # a blind lancet on the outer face (built facing -Y, turned to face outward along +X)
        s1 = _mark()
        _lancet(f"PierLancet{k}", 0, 0, 1.4, 0.27, 2.9, 3.25, dk, thick=0.03)
        _xform(s1, Matrix.Translation((RP + w / 2 + 0.005, 0, 0)) @ _rotz(math.pi / 2))
        # the flying buttress from the pier up to the hall's head: an arched underside, a straight coping, two pierced foils
        r0, r1 = RD + 0.5, RP - w / 2
        under = [(r1 - (r1 - r0) * (1 - math.cos(t)), 6.1 + 2.2 * math.sin(t)) for t in [i / 10 * math.pi / 2 for i in range(11)]]
        flyer = [(r1, 8.3), (r0, 9.55)] + list(reversed(under))
        fl = B20.tprism(f"Flyer{k}", WS.ccw(flyer), 0.0, 0.42, st)
        pierce(fl, [WS.foil_outline((r0 + r1) / 2 - 0.05, 8.1, 0.26, 3, n=30)])
        tube(f"FlyerCoping{k}", [(r1 + 0.1, 0, 8.36), (r0 - 0.05, 0, 9.62)], 0.12, dk, square=True, poly=True)
        _crockets(f"FlyerCrocket{k}", [(r1 - (r1 - r0) * t, 0, 8.45 + (9.62 - 8.36) * t) for t in (0.3, 0.65)], st, size=0.1)
        _radial(s0, a)
    set_group("Main")
    # ---- the crown band: openwork iron tracery high between the spires, gilt quatrefoils, a crimson enamel rail
    cp = RP * math.sin(math.pi / NB)
    set_group("Crown")
    for k in range(NB):
        s0 = _mark()
        span = cp - 0.5
        z0, z1 = 6.55, 7.95
        ribbon(f"CrownFoot{k}", [(-span, z0), (span, z0)], 0.12, -0.06, 0.06, iron)
        ribbon(f"CrownRail{k}", [(-span, z1), (span, z1)], 0.14, -0.08, 0.08, en)
        n = 4
        aw = span * 2 / n
        for j in range(n):
            cx = -span + aw * (j + 0.5)
            ribbon(f"CrownArch{k}{j}", [(cx + x, z) for x, z in WS.pointed(aw / 2 - 0.04, z0 + 0.62, z1 - 0.05, 6)], 0.06, -0.05, 0.05, iron)
            ribbon(f"CrownPost{k}{j}", [(cx - aw / 2 + 0.04, z0), (cx - aw / 2 + 0.04, z0 + 0.62)], 0.06, -0.05, 0.05, iron)
            foil(f"CrownFoil{k}{j}", cx, -0.05, z0 + 0.36, 0.16, gl, lobes=4, thick=0.016)
        for sx in (-1, 1):
            _spike(f"CrownSpike{k}{sx}", (sx * span * 0.5, 0, z1 + 0.3), 0.04, 0.42, iron, verts=4)
        sphere(f"CrownBoss{k}", 0.08, (0, -0.06, z1), gl, seg=8, rings=4)
        _xform(s0, _bay(k, RP))
    set_group("Main")
    # ---- the crown dome: eight crocketed corner ribs up a steep pointed profile, light mid ribs, purlins, gilt bosses
    prof = _dome_profile()
    set_group("Dome")
    hoop("Curb", (0, 0, ZE + 0.06), RC + 0.12, "Z", en, thick=0.13)
    for k in range(NB):
        a = _corner(k)
        pts = [_at(r + 0.1, a, z + 0.04) for r, z in prof]
        tube(f"Rib{k}", pts, 0.13, iron, square=True, poly=True)
        _crockets(f"RibCrocket{k}", [_at(r + 0.27, a, z + 0.12) for r, z in prof[2:-1:2]], iron, size=0.09)
        am = a + math.pi / NB
        mid = [_at((r + 0.05) * math.cos(math.pi / NB), am, z) for r, z in prof]
        tube(f"MidRib{k}", mid, 0.05, iron, square=True, poly=True)
    for i in (4, 8, 12, 16, 20):
        if i >= len(prof) - 1:
            continue
        r, z = prof[i]
        tube(f"Purlin{i}", [_at(r + 0.07, _corner(k), z + 0.03) for k in range(NB)], 0.055, iron, closed=True, square=True, poly=True)
        for k in range(NB):
            sphere(f"RibBoss{i}{k}", 0.1, _at(r + 0.22, _corner(k), z + 0.05), gl, seg=8, rings=4)
    # ---- the openwork spire on top: eight iron posts drawing to a point, two rings, crockets, the gilt crescent
    rl, zl = prof[-1]
    hoop("SpireRing", (0, 0, zl + 0.04), RL + 0.05, "Z", iron, thick=0.09)
    zt = zl + 3.6
    for k in range(NB):
        a = _corner(k)
        tube(f"SpirePost{k}", [_at(RL, a, zl), _at(RL * 0.55, a, zl + 1.6), _at(0.05, a, zt)], 0.045, iron, square=True, poly=True)
        _crockets(f"SpireCrocket{k}", [_at(RL * 0.62 + 0.1, a, zl + 1.3), _at(RL * 0.3 + 0.1, a, zl + 2.5)], iron, size=0.07)
    tube("SpireBand", [_at(RL * 0.55 + 0.02, _corner(k), zl + 1.6) for k in range(NB)], 0.035, gl, closed=True, square=True, poly=True)
    sphere("SpireKnop", 0.16, (0, 0, zl + 0.9), gl, seg=12, rings=6)
    sphere("FinialBall", 0.14, (0, 0, zt + 0.1), gl, seg=12, rings=6)
    tube("FinialStem", [(0, 0, zt + 0.2), (0, 0, zt + 0.55)], 0.035, gl, poly=True)
    B20.tprism("FinialMoon", WS.crescent(0, zt + 0.92, 0.4, shift=0.4, tilt=math.pi / 2), 0.0, 0.07, gl)
    set_group("Main")
    # ---- the doorway: a crocketed gable over the door bay, a threshold
    s0 = _mark()
    gable = [(-2.0, 6.55), (2.0, 6.55), (0.0, 9.45)]
    gb = B20.tprism("Gable", gable, -0.2, 0.22, st)
    pierce(gb, [WS.foil_outline(0, 7.55, 0.66, 6, n=48)])
    tube("GableCoping", [(-2.1, -0.24, 6.5), (0.0, -0.24, 9.58), (2.1, -0.24, 6.5)], 0.11, dk, square=True, poly=True)
    for sx in (-1, 1):
        _crockets(f"GableCrocket{sx}", [(sx * 2.0 * (1 - t), -0.26, 6.55 + 2.9 * t + 0.15) for t in (0.2, 0.4, 0.6, 0.8)], st, size=0.1)
    _spirelet("GableFinial", 0.0, -0.24, 9.5, 1.3, 0.3, st, crockets=2)
    box("Threshold", (3.0, 1.1, 0.06), (0, -0.25, 0.43), dk, bevel=0.02)
    _xform(s0, _bay(0))
    set_group("Glass")
    # the crown dome's glass: a planar facet between neighbouring ribs at every other profile step
    gp = prof[::2] + ([prof[-1]] if (len(prof) - 1) % 2 else [])
    for i in range(len(gp) - 1):
        (r0, z0), (r1, z1) = gp[i], gp[i + 1]
        for k in range(NB):
            a, b = _corner(k), _corner(k + 1)
            sheet(f"DomePane{i}_{k}", [[Vector(_at(r0, a, z0)), Vector(_at(r0, b, z0)), Vector(_at(r1, b, z1)), Vector(_at(r1, a, z1))]], K["glass"], 0.02)
    for k, L in glass_bays:
        s0 = _mark()
        B20.tprism(f"BayPane{k}", WS.ccw(L), 0.0, 0.02, K["glass"])
        _xform(s0, _bay(k))
    set_group("Glow")
    for k, (x, y, tip) in enumerate(flames):
        flame(f"Flame{k}", (x, y, tip - 0.005), h=0.1)
    set_group("Main")
    _moss("Moss", [_at(RP + 0.6, _corner(k) + 0.04, 0.4) for k in (2, 3, 5, 7)], K["moss"], rnd, size=0.12)
    return _dims()


def conservatory_beds(M):
    """The conservatory's planting: a round soot-stone bed with an iron obelisk trellis climbed by crimson roses,
    ferns and dark broad leaves round it, and four iron urns of ferns at the diagonals. Laid out for the crown's hall floor
    (it stands on z = 0; the setup sets it on the floor)."""
    K = kit(M)
    st, dk, iron, gl = K["st"], K["dk"], K["iron"], K["gilt"]
    rnd = random.Random(2331)
    soil = material("Soil", "NH_Limestone", tint=(0.1, 0.07, 0.05), scale=1.2, rough_add=0.35, wear=0.0, dirt=0.9)
    greens = [flat("FernDark", (0.012, 0.04, 0.016), 0.45, dirt=0.7), flat("FernOld", (0.02, 0.05, 0.016), 0.5, dirt=0.8),
              flat("LeafBroad", (0.01, 0.03, 0.02), 0.35, dirt=0.7)]
    petal = flat("RosePetal", (0.16, 0.006, 0.018), 0.5, dirt=0.85)
    stem = flat("Stem", (0.025, 0.05, 0.02), 0.55)
    # the central bed
    R = 2.6
    lathe("BedCurb", [(R - 0.3, 0.16), (R, 0.16), (R + 0.08, 0.3), (R + 0.04, 0.8), (R + 0.1, 0.86), (R + 0.1, 0.95), (R - 0.3, 0.95)], st, seg=40)
    lathe("BedSoil", [(0, 0.16), (R - 0.3, 0.16), (R - 0.3, 0.88), (0, 0.92)], soil, seg=32)
    lathe("BedPlinth", [(R - 0.2, 0.0), (R + 0.18, 0.0), (R + 0.2, 0.16), (R - 0.2, 0.16)], dk, seg=40)
    # the obelisk trellis: four iron uprights tapering to a gilt ball, rings and diagonal lattice
    zb, zt = 0.9, 6.2
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tube(f"Upright{k}", [(math.cos(a) * 0.75, math.sin(a) * 0.75, zb), (math.cos(a) * 0.12, math.sin(a) * 0.12, zt)], 0.035, iron, square=True, poly=True)
    for j, z in enumerate((1.6, 2.7, 3.8, 4.9)):
        t = (z - zb) / (zt - zb)
        r = 0.75 + (0.12 - 0.75) * t
        tube(f"TrellisRing{j}", [(math.cos(k * math.pi / 2 + math.pi / 4) * r, math.sin(k * math.pi / 2 + math.pi / 4) * r, z) for k in range(4)], 0.022, iron,
             closed=True, square=True, poly=True)
    sphere("TrellisBall", 0.14, (0, 0, zt + 0.1), gl, seg=12, rings=6)
    _spike("TrellisSpike", (0, 0, zt + 0.42), 0.04, 0.4, gl, verts=6)
    # crimson roses climbing it (light roses: a bud and five petals)
    def rose_head(name, p, d, s=1.0):
        s0 = _mark()
        sphere(f"{name}Bud", 0.08 * s, (0, 0, 0.05 * s), petal, seg=8, rings=4, scale=(1, 1, 1.3))
        for i in range(5):
            a = i / 5 * 2 * math.pi
            sphere(f"{name}P{i}", 0.11 * s, (math.cos(a) * 0.08 * s, math.sin(a) * 0.08 * s, 0.02 * s), petal, seg=6, rings=3, scale=(1.0, 0.35, 0.8))
            P.PARTS[-1].rotation_euler = (math.radians(-25), 0, a - math.pi / 2)
        bpy.context.view_layer.update()
        _xform(s0, Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_matrix().to_4x4())
    vine = []
    for k in range(60):
        t = k / 59
        z = zb + 0.1 + t * (zt - zb - 0.6)
        r = 0.78 + (0.16 - 0.75) * (z - zb) / (zt - zb) + 0.06
        a = t * 4.5 * math.pi
        vine.append((math.cos(a) * r, math.sin(a) * r, z))
    set_group("Plants")
    tube("Vine", vine, 0.03, stem)
    for k in range(15):
        x, y, z = vine[3 + k * 3 + (k % 2)]
        out = Vector((x, y, 0.4)).normalized()
        rose_head(f"Rose{k}", (x + out.x * 0.14, y + out.y * 0.14, z), (out.x, out.y, 0.6), s=1.25)
        a = math.atan2(y, x) + (0.7 if k % 2 else -0.7)
        leaf(f"VineLeaf{k}", (x, y, z - 0.1), a, math.radians(10), 0.34, 0.11, 0.08, greens[0], n=5, thick=0.006)
    # ferns and broad leaves round the trellis, roses on low bushes
    for k in range(8):
        a = k / 8 * 2 * math.pi + 0.2
        cx, cy = math.cos(a) * 1.65, math.sin(a) * 1.65
        for j in range(5):
            b = j / 5 * 2 * math.pi + rnd.uniform(-0.3, 0.3)
            leaf(f"Fern{k}{j}", (cx, cy, 0.92), b, math.radians(rnd.uniform(32, 58)), rnd.uniform(1.15, 1.55), 0.17, 0.4, greens[(k + j) % 2], n=7,
                 thick=0.008)
        if k % 3 == 1:
            for j in range(3):
                rose_head(f"Bush{k}{j}", (cx + rnd.uniform(-0.25, 0.25), cy + rnd.uniform(-0.25, 0.25), 1.6 + rnd.uniform(0, 0.25)),
                          (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 1), s=1.35)
                tube(f"BushStem{k}{j}", [(cx, cy, 0.92), (cx, cy, 1.55)], 0.02, stem, poly=True)
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.7
        leaf(f"Broad{k}", (math.cos(a) * 0.95, math.sin(a) * 0.95, 0.92), a, math.radians(42), 1.7, 0.4, 1.0, greens[2], n=8, thick=0.01)
    set_group("Main")
    # four iron urns of ferns, set out at the dome's diagonals (6 from the centre)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 4.3, math.sin(a) * 4.3
        lathe(f"Urn{k}", [(0, 0), (0.55, 0), (0.57, 0.12), (0.3, 0.27), (0.26, 0.52), (0.38, 0.68), (0.7, 1.15), (0.8, 1.45), (0.85, 1.55), (0.75, 1.58),
                          (0, 1.5)], iron, seg=24, loc=(x, y, 0))
        hoop(f"UrnGilt{k}", (x, y, 1.47), 0.81, "Z", gl, thick=0.022)
        lathe(f"UrnSoil{k}", [(0, 1.42), (0.74, 1.42), (0, 1.46)], soil, seg=16, loc=(x, y, 0))
        set_group("Plants")
        for j in range(7):
            b = j / 7 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
            leaf(f"UrnFern{k}{j}", (x, y, 1.5), b, math.radians(rnd.uniform(35, 60)), rnd.uniform(1.2, 1.6), 0.17, 0.5, greens[j % 2], n=7, thick=0.008)
        set_group("Main")
    return _dims()


# ------------------------------------------------------------------ registration

ROOM_IMAGE = "WindowRoom"
STAINED = ("TraceryWindow", "RoseWindow", "StainedLancet")

_orig_canvas_material = P.canvas_material


def _canvas_material(ob, image):
    """The Room and Stained pieces glow in the preview as they do in Roblox (the canvas image through an emissive mask)."""
    _orig_canvas_material(ob, image)
    if ob.name.endswith(("_Stained", "_Room")):
        nt = ob.data.materials[0].node_tree
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        t = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
        nt.links.new(t.outputs["Color"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = 1.6 if ob.name.endswith("_Stained") else 0.9


P.canvas_material = _canvas_material

BUILDERS = {
    "LancetWindow": lancet_window,
    "TwinLancet": twin_lancet,
    "TripletLancet": triplet_lancet,
    "TraceryWindow": tracery_window,
    "RoseWindow": rose_window,
    "Oculus": oculus,
    "DiamondPaneArch": diamond_pane_arch,
    "SashWindow": sash_window,
    "GothicBay": gothic_bay,
    "LucarneDormer": lucarne_dormer,
    "ArrowSlit": arrow_slit,
    "Fanlight": fanlight,
    "BasementGrate": basement_grate,
    "StainedLancet": stained_lancet,
    "BrokenWindow": broken_window,
    "ShutteredWindow": shuttered_window,
    "TraceryWindowClear": lambda M: tracery_window(M, clear=True),
    "RoseWindowClear": lambda M: rose_window(M, clear=True),
    "PlainSash": plain_sash,
    "CrossWindow": cross_window,
    "PictureWindow": picture_window,
    "RoundArchWindow": round_arch_window,
    "SquareWindow": square_window,
    "HalfRoundWindow": half_round_window,
    "ConservatoryDome": conservatory_dome,
    "ConservatoryBeds": conservatory_beds,
}
for _n in BUILDERS:
    if _n.startswith("Conservatory"):
        continue
    if _n in STAINED:
        P.CANVAS[f"{_n}_Stained"] = f"{_n}Stained"
    else:
        P.CANVAS[f"{_n}_Room"] = ROOM_IMAGE
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"SquareWindow": 1.3, "GothicBay": 1.0, "LucarneDormer": 1.1, "ArrowSlit": 1.15, "Oculus": 1.25, "Fanlight": 1.05, "BasementGrate": 1.05})
# the dome's plinth and floor are tiled castle stone (as the bridges' walls), and its glass needs no maps (Roblox Glass), so
# none of them eat the atlas the ironwork is baked into
P.TILED.update({"ConservatoryDome_Wall": ("NH_CastleStone", 8.0), "ConservatoryDome_Floor": ("NH_CastleStone", 8.0),
                "ConservatoryDome_Glass": ("NH_CastleStone", 8.0)})
P.PREVIEW_PAD.update({"ConservatoryDome": 1.05, "ConservatoryBeds": 1.1})
P.BUILD.update(BUILDERS)
