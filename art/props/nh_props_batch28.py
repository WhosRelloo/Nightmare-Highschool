"""Props batch 28 (2026-11-05): the roof kit for nh_props.py, in the Institution's look: slate, lead and verdigris copper,
crimson glaze, soot-dark castle stone, cast iron and gilt, candlelit gothic. Enough pieces to roof the school and the town.

The big roof planes are not baked: they carry world-scaled UVs (u along the eaves, v up the slope, the courses starting
at each plane's eaves) and the seamless roof sets from tools/vfx/make_roof_tiles.py, so they stay sharp at any size:
  Slate  NH_RoofSlate, 6 studs a tile     Moss  NH_RoofMoss, 6       Scale  NH_RoofScale (fish scales), 4
  Crimson  NH_RoofCrimson (glazed scales), 4   Copper  NH_RoofCopper, 6   Lead  NH_RoofLead, 6
  Stone  NH_CastleStone, 8 (gable walls and parapets, the same set as the builder's castle stone walls)
Every other piece (Main: cornices, copings, ridges, cresting, gutters, finials, dormer faces...) is baked at 2048. Glass
is Roblox Glass, Glow a small flame.

Pitched roofs sit on a wall top at z = 0: the footprint W x D is the wall's outer size (16 x 12 for the school wings);
a moulded cornice runs round the wall top, the roof rises from it. Front faces -Y, Z is up, the origin is at the bottom
centre. Registered into nh_props.BUILD on import.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, _finish, material
from nh_props_batch3 import sphere, cone, flame
from nh_props_batch4 import lathe, hoop, prism, _mark, _xform, _dims, flat
from nh_props_batch8 import mossy, hollow, staining, _moss, _crack, _spirelet, _crockets, _spike
from nh_props_batch9 import foil, raven, twist
from nh_props_batch10 import gilt
from nh_props_batch12 import soot_stone
import nh_props_batch20 as B20
import window_shapes as WS

TILES = {"Slate": ("NH_RoofSlate", 6.0), "Moss": ("NH_RoofMoss", 6.0), "Scale": ("NH_RoofScale", 4.0), "Crimson": ("NH_RoofCrimson", 4.0),
         "Copper": ("NH_RoofCopper", 6.0), "Lead": ("NH_RoofLead", 6.0), "Stone": ("NH_CastleStone", 8.0)}
ZP = 0.9          # the cornice's top: where the roof planes spring
CP = 0.45         # how far the cornice stands out from the wall face
TS = 0.12         # the slate layer, on a lead underlay of the same thickness
SPRING = 0.3      # the roof's underside springs from the cornice's flat top this far out from the wall face


# ------------------------------------------------------------------ materials

def kit(M):
    return {
        "st": soot_stone("SootStone", (0.16, 0.165, 0.155)),
        "dk": soot_stone("SootStoneDark", (0.095, 0.1, 0.093)),
        "iron": M["iron"], "brass": M["brass"], "gilt": gilt(), "glass": M["glassclear"],
        "lead": material("Lead", "NH_PaintedMetal", tint=(0.062, 0.066, 0.072), scale=0.7, rough_add=0.25, wear=0.2),
        "enamel": material("CrimsonEnamel", "NH_PaintedMetal", tint=(0.2, 0.025, 0.04), scale=1.4, rough_mul=0.55, rough_add=0.05, wear=0.45,
                           wear_metal=True, dirt=0.85),
        "glaze": material("CrimsonGlaze", "NH_Limestone", tint=(0.14, 0.012, 0.017), scale=0.5, rough_mul=0.3, rough_add=0.08, wear=0.35, dirt=0.9),
        "slate": material("RoofSlate", "NH_Slate", tint=(0.045, 0.055, 0.075), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.15),
        "verdigris": material("Verdigris", "NH_PaintedMetal", tint=(0.1, 0.25, 0.19), scale=0.9, rough_mul=0.8, rough_add=0.3, wear=0.4,
                              wear_metal=True, dirt=1.0),
        "bronze": material("Bronze", "NH_Brass", tint=(0.26, 0.19, 0.12), scale=0.6, rough_add=0.22, wear=0.6, dirt=1.0),
        "charred": material("Charred", "NH_DeskWood", tint=(0.05, 0.038, 0.03), scale=0.3, rough_add=0.2, wear=0.3, dirt=1.0),
        "hollow": hollow(), "moss": mossy(), "stain": staining(),
        "tile": flat("TileTmp", (0.1, 0.1, 0.1), 0.6),
        "room": flat("RoomTmp", (0.5, 0.3, 0.1), 0.9),
    }


# ------------------------------------------------------------------ tiled pieces and their UVs

def tiled(group):
    """Parts built after this go to a tiled piece (see TILES); set_group("Main") goes back to the baked atlas."""
    set_group(group)


def _plane_uv(ob, tile):
    """Each face projected in its own plane: u along the horizontal, v up the slope; every plane's v starts at its
    lowest point, so the first course of slates sits on the eaves."""
    me = ob.data
    uv = me.uv_layers.get("Bake") or me.uv_layers.new(name="Bake")
    mw = ob.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()
    Z = Vector((0, 0, 1))
    lows, rows = {}, []
    for poly in me.polygons:
        n = (nm @ poly.normal).normalized()
        if abs(n.z) > 0.985:
            t, b = Vector((1, 0, 0)), Vector((0, 1 if n.z > 0 else -1, 0))
        else:
            b = (Z - n * n.z).normalized()
            t = b.cross(n).normalized()
        pts = [mw @ me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        key = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(pts[0].dot(n), 1))
        lows[key] = min(lows.get(key, 1e9), min(p.dot(b) for p in pts))
        rows.append((poly, t, b, pts, key))
    for poly, t, b, pts, key in rows:
        for li, p in zip(poly.loop_indices, pts):
            uv.data[li].uv = (p.dot(t) / tile, (p.dot(b) - lows[key]) / tile)


def _lathe_uv(ob, tile):
    """A solid of revolution (lathe()): u round it (a whole number of tiles at its widest ring), v the length along the
    profile from its foot, so the courses run round it and the slates narrow toward the top as real ones are cut."""
    me = ob.data
    uv = me.uv_layers.get("Bake") or me.uv_layers.new(name="Bake")
    prof = [(ob["nh_prof"][i], ob["nh_prof"][i + 1]) for i in range(0, len(ob["nh_prof"]), 2)]
    seg = int(ob["nh_seg"])
    s = [0.0]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        s.append(s[-1] + math.hypot(r1 - r0, z1 - z0))
    ring, idx = [], []
    for k, (r, z) in enumerate(prof):
        cnt = 1 if r <= 1e-6 else seg
        for j in range(cnt):
            ring.append(k)
            idx.append(j if cnt > 1 else -1)
    R = max(r for r, _ in prof)
    nu = max(1, round(2 * math.pi * R / tile))
    for poly in me.polygons:
        vs = [me.loops[li].vertex_index for li in poly.loop_indices]
        js = [idx[v] for v in vs]
        real = [j for j in js if j >= 0]
        wrap = real and max(real) == seg - 1 and min(real) == 0
        js = [(seg if (wrap and j == 0) else j) for j in js]
        real = [j for j in js if j >= 0]
        mean = sum(real) / len(real) if real else 0
        for li, v, j in zip(poly.loop_indices, vs, js):
            uu = (j if j >= 0 else mean) / seg * nu
            uv.data[li].uv = (uu, s[ring[v]] / tile)


def tlathe(name, prof, group, seg=32, loc=(0, 0, 0), mat=None):
    """lathe() on a tiled piece, with its profile kept for the UVs."""
    ob = lathe(name, prof, mat, seg=seg, loc=loc)
    ob["nh_prof"] = [c for p in prof for c in p]
    ob["nh_seg"] = seg
    return ob


def _finish_tiles():
    bpy.context.view_layer.update()
    for ob in P.PARTS:
        g = ob.get("nh_group")
        if g in TILES and ob.type == "MESH":
            if "nh_prof" in ob.keys():
                _lathe_uv(ob, TILES[g][1])
            else:
                _plane_uv(ob, TILES[g][1])


_orig_tile_uv = P.tile_uv


def _tile_uv(ob, tile):
    """Keep the UVs the builder made (the Bake layer) for this batch's tiled pieces (only this batch's props)."""
    if "Bake" in ob.data.uv_layers and ob.name.split("_")[-1] in TILES and ob.name.rsplit("_", 1)[0] in BUILDERS:
        for uv in list(ob.data.uv_layers):
            if uv.name != "Bake":
                ob.data.uv_layers.remove(uv)
        ob.data.uv_layers.active = ob.data.uv_layers["Bake"]
        return
    _orig_tile_uv(ob, tile)


P.tile_uv = _tile_uv


# ------------------------------------------------------------------ mesh helpers

def mk(name, verts, faces, mat, tri=True):
    """A closed mesh from vertices and faces (normals recalculated outward)."""
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


def solid(name, bottom, top, mat):
    """A solid between two matching loops of points (a slab, a wedge, a frustum)."""
    n = len(bottom)
    faces = [list(range(n)), list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    return mk(name, list(bottom) + list(top), faces, mat)


def bar(name, a, b, w, h, mat, up=(0, 0, 1), bevel=0.0):
    """A straight beam from a to b, w wide and h deep (h measured along `up` squared off against the beam)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    x = d.normalized()
    z = (Vector(up) - x * x.dot(Vector(up))).normalized()
    y = z.cross(x)
    R = Matrix((x, y, z)).transposed().to_4x4()
    s = _mark()
    box(name, (L, w, h), (0, 0, 0), mat, bevel=bevel, segments=1)
    _xform(s, Matrix.Translation((a + b) / 2) @ R)


def mould(name, path, profile, mat, closed=True):
    """A moulding swept along a plan path (x, y; counter-clockwise when closed): profile [(d, z), ...] is its section,
    d outward from the path (to the right of travel), a closed polygon. Mitred at the corners; capped when open."""
    loops = [[(x, y, z) for x, y in WS.offset(path, d, closed=closed)] for d, z in profile]
    n, m = len(path), len(profile)
    verts = [loops[k][i] for i in range(n) for k in range(m)]
    faces = []
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((i * m + k, i * m + k2, j * m + k2, j * m + k))
    if not closed:
        faces.append(tuple(range(m)))
        faces.append(tuple((n - 1) * m + k for k in range(m)))
    return mk(name, verts, faces, mat)


def rect_path(hw, hd, cx=0.0, cy=0.0):
    return [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]


def poly_path(r, n, a0=None, cx=0.0, cy=0.0):
    """A regular n-gon by its corner radius r, a flat side to the front (-Y) unless a0 is given."""
    a0 = -math.pi / 2 + math.pi / n if a0 is None else a0
    return [(cx + math.cos(a0 + k * 2 * math.pi / n) * r, cy + math.sin(a0 + k * 2 * math.pi / n) * r) for k in range(n)]


CORNICE = [(-0.35, 0.0), (0.03, 0.0), (0.03, 0.26), (0.1, 0.29), (0.14, 0.35), (0.22, 0.42), (0.32, 0.47), (0.42, 0.52), (0.45, 0.57),
           (0.45, 0.76), (0.41, 0.79), (0.39, 0.85), (0.33, ZP), (-0.35, ZP)]


def cornice(prefix, path, K, closed=True, corbels=True, step=1.3, mat=None):
    """The wall-top cornice: a moulded course standing out CP from the wall face, on a row of little corbels."""
    mould(prefix, path, CORNICE, mat or K["dk"], closed=closed)
    if not corbels:
        return
    m = len(path) if closed else len(path) - 1
    k = 0
    for i in range(m):
        a, b = Vector((*path[i], 0)), Vector((*path[(i + 1) % len(path)], 0))
        d = b - a
        L = d.length
        out = Vector((d.y, -d.x, 0)).normalized()
        cnt = max(1, int(L / step))
        for c in range(cnt):
            t = (c + 0.5) / cnt
            p = a + d * t
            if not closed and (t * L < 0.5 or (1 - t) * L < 0.5):
                continue
            q = p + out * 0.18
            s = _mark()
            box(f"{prefix}Corbel{k}", (0.3, 0.36, 0.3), (0, 0, 0), K["st"], bevel=0.04, segments=1)
            box(f"{prefix}CorbelFoot{k}", (0.22, 0.24, 0.14), (0, -0.04, -0.2), K["st"], bevel=0.03, segments=1)
            _xform(s, Matrix.Translation((q.x, q.y, 0.3)) @ Matrix.Rotation(math.atan2(out.x, -out.y), 4, "Z"))
            k += 1


GUTTER = [(0.0, 0.3), (0.0, 0.05), (0.06, 0.0), (0.34, 0.0), (0.42, 0.08), (0.44, 0.2), (0.49, 0.3), (0.43, 0.31), (0.39, 0.19), (0.36, 0.09),
          (0.3, 0.05), (0.09, 0.05), (0.05, 0.1), (0.05, 0.3)]


def gutter(prefix, path, z, K, closed=False, brackets=True):
    """A cast-iron ogee gutter swept along a plan path (its back on the path, hanging outward to the right of travel),
    its lip at z; mitred round corners, capped at open ends; iron hangers every two studs or so."""
    mould(prefix, path, [(d, z - 0.31 + zz) for d, zz in GUTTER], K["iron"], closed=closed)
    if not brackets:
        return
    m = len(path) if closed else len(path) - 1
    k = 0
    for i in range(m):
        a, b = Vector((*path[i], 0)), Vector((*path[(i + 1) % len(path)], 0))
        d = b - a
        out = Vector((d.y, -d.x, 0)).normalized()
        cnt = max(1, int(d.length / 2.0))
        for c in range(cnt):
            p = a + d * ((c + 0.5) / cnt)
            pts = [p + out * 0.02 + Vector((0, 0, z - 0.02)), p + out * 0.02 + Vector((0, 0, z - 0.33)), p + out * 0.25 + Vector((0, 0, z - 0.36)),
                   p + out * 0.47 + Vector((0, 0, z - 0.06))]
            tube(f"{prefix}Hanger{k}", [tuple(q) for q in pts], 0.018, K["iron"], square=True, poly=True)
            k += 1


def chevron(name, pts, up, down, pos, width, mat, plane="YZ"):
    """A band round an open polyline in a plane (a coping, a verge, a bargeboard): `up` above it, `down` below,
    extruded `width` about pos."""
    top = WS.offset(pts, -up, closed=False)
    bot = WS.offset(pts, down, closed=False)
    return B20.tprism(name, WS.ccw(top + list(reversed(bot))), pos, width, mat, plane=plane)


def finish(fn):
    def run(M):
        dims = fn(M)
        _finish_tiles()
        return dims
    return run


# ------------------------------------------------------------------ pitched roofs

class Pitch:
    """The planes of a roof of `pitch` on a W x D wall top, its ridge along X at y = 0. The underside of the lead
    underlay springs from the cornice's top (y = D/2 + SPRING, z = ZP) and overhangs it by ov."""

    def __init__(self, W, D, pitch, ov=0.45):
        self.W, self.D, self.p = W, D, math.radians(pitch)
        self.t = math.tan(self.p)
        self.ov = ov
        self.ye = D / 2 + SPRING + ov
        self.ze = ZP - ov * self.t
        self.Hb = ZP + (D / 2 + SPRING) * self.t      # the underside at the ridge
        self.c = math.cos(self.p)
        self.top = self.Hb + 2 * TS / self.c - 0.02  # the slate's top at the ridge

    def z_under(self, y):
        return ZP + (self.D / 2 + SPRING - abs(y)) * self.t

    def z_top(self, y):
        return self.z_under(y) + (2 * TS - 0.02) / self.c

    def n(self, s):
        return Vector((0, s * math.sin(self.p), self.c))

    def slab(self, name, x0, x1, s, lift, thick, inset=0.0, inset_x=(0.0, 0.0)):
        """One plane's layer, lift above the roof plane and thick: s -1 the front plane, +1 the back. inset pulls the
        eave edge up the slope, inset_x the ends in."""
        ye = self.ye - inset * self.c
        ze = self.ze + inset * math.sin(self.p)
        nn = self.n(s)
        x0, x1 = x0 + inset_x[0], x1 - inset_x[1]
        bot = [Vector((x0, s * ye, ze)), Vector((x1, s * ye, ze)), Vector((x1, 0, self.Hb)), Vector((x0, 0, self.Hb))]
        def lay(v, h):
            if abs(v.y) < 1e-6:
                return Vector((v.x, 0, v.z + h / self.c))
            return v + nn * h
        b = [lay(v, lift) for v in bot]
        t = [lay(v, lift + thick) for v in bot]
        return solid(name, b, t, self._mat)

    def roof(self, prefix, x0, x1, tile, K, sides=(-1, 1), under_inset_x=(0.05, 0.05)):
        self._mat = K["tile"]
        for s in sides:
            tiled(tile)
            self.slab(f"{prefix}Slate{s}", x0, x1, s, TS - 0.02, TS)
            tiled("Lead")
            self.slab(f"{prefix}Under{s}", x0, x1, s, 0.0, TS, inset=0.06, inset_x=under_inset_x)
        set_group("Main")


def gable_wall(prefix, x_out, x_in, R, K, apex_extra=0.05, parapet=0.0):
    """The gable's triangle of wall above the cornice (tiled castle stone), from the wall face x_out to x_in; with
    parapet > 0 it rises that far above the slates (a parapet gable), else it stops just inside the roof."""
    D = R.D
    if parapet > 0:
        zk = R.z_top(D / 2) + parapet
        za = R.top + parapet
    else:
        zk = R.z_under(D / 2) + apex_extra
        za = R.Hb + apex_extra
    poly = [(-D / 2, ZP - 0.06), (D / 2, ZP - 0.06), (D / 2, zk), (0.0, za), (-D / 2, zk)]
    tiled("Stone")
    B20.tprism(f"{prefix}", WS.ccw(poly), (x_out + x_in) / 2, abs(x_out - x_in), K["tile"], plane="YZ")
    set_group("Main")
    return zk, za


def ridge_tiles(prefix, x0, x1, z, K, r=0.26, step=1.0, knobs=True):
    """Crimson glazed half-round ridge tiles with rolled collars at the joints, gilt knobs on the ends."""
    L = x1 - x0
    cyl(f"{prefix}", r, L, ((x0 + x1) / 2, 0, z), K["glaze"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.0)
    n = max(1, round(L / step))
    for k in range(1, n):
        x = x0 + k * L / n
        cyl(f"{prefix}Collar{k}", r + 0.035, 0.09, (x, 0, z), K["glaze"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.01)
    if knobs:
        for sx, x in ((-1, x0), (1, x1)):
            cyl(f"{prefix}End{sx}", r + 0.05, 0.12, (x - sx * 0.06, 0, z), K["glaze"], rot=(0, math.pi / 2, 0), verts=20, bevel=0.015)


def cresting(prefix, x0, x1, z, K, h=0.85, step=0.9, gilt_tips=True):
    """Cast-iron ridge cresting along X: two rails, spear-headed uprights, a quatrefoil ring in every bay."""
    ir, gl = K["iron"], K["gilt"]
    L = x1 - x0
    n = max(2, round(L / step))
    tube(f"{prefix}RailLo", [(x0, 0, z + 0.1), (x1, 0, z + 0.1)], 0.025, ir, square=True, poly=True)
    tube(f"{prefix}RailHi", [(x0, 0, z + h * 0.62), (x1, 0, z + h * 0.62)], 0.022, ir, square=True, poly=True)
    for k in range(n + 1):
        x = x0 + L * k / n
        tall = h * (1.0 if k % 2 == 0 else 0.82)
        tube(f"{prefix}Post{k}", [(x, 0, z - 0.02), (x, 0, z + tall)], 0.022, ir, square=True, poly=True)
        _spike(f"{prefix}Spear{k}", (x, 0, z + tall + 0.08), 0.06, 0.18, gl if (gilt_tips and k % 2 == 0) else ir, verts=4)
        if k < n:
            xc = x + L / n / 2
            zc = z + (0.1 + h * 0.62) / 2 + 0.02
            rr = min(L / n, h * 0.5) * 0.4
            tube(f"{prefix}Foil{k}", [(x2, 0, z2) for x2, z2 in WS.foil_outline(xc, zc, rr, 4, n=16)], 0.013, ir, closed=True, square=True, poly=True)


def lead_roll(prefix, pts, K, r=0.1):
    tube(prefix, pts, r, K["lead"], poly=True)


def moon_finial(prefix, x, y, z, K, h=2.2, s=1.0):
    """An iron spike rising from a moulded lead base through two gilt orbs to a gilt crescent moon."""
    ir, gl = K["iron"], K["gilt"]
    lathe(f"{prefix}Base", [(0, 0), (0.22 * s, 0), (0.2 * s, 0.12 * s), (0.11 * s, 0.22 * s), (0.08 * s, 0.4 * s), (0, 0.4 * s)], K["lead"], seg=16,
          loc=(x, y, z))
    tube(f"{prefix}Rod", [(x, y, z + 0.3 * s), (x, y, z + h * 0.78)], 0.035 * s, ir, poly=True)
    sphere(f"{prefix}Orb", 0.13 * s, (x, y, z + h * 0.32), gl, seg=14, rings=7)
    sphere(f"{prefix}Orb2", 0.08 * s, (x, y, z + h * 0.55), gl, seg=12, rings=6)
    B20.tprism(f"{prefix}Moon", WS.crescent(x, z + h * 0.86, 0.24 * s, shift=0.42, tilt=math.pi / 2), y, 0.045 * s, gl)
    _spike(f"{prefix}Tip", (x, y, z + h * 0.99), 0.03 * s, 0.14 * s, gl, verts=4)


def key_finial(prefix, x, y, z, K, s=1.0):
    """The crest's key, gilt and upright on an iron rod over a gilt orb."""
    ir, gl = K["iron"], K["gilt"]
    lathe(f"{prefix}Base", [(0, 0), (0.24 * s, 0), (0.22 * s, 0.12 * s), (0.12 * s, 0.26 * s), (0.09 * s, 0.45 * s), (0, 0.45 * s)], K["lead"], seg=16,
          loc=(x, y, z))
    tube(f"{prefix}Rod", [(x, y, z + 0.4 * s), (x, y, z + 1.3 * s)], 0.04 * s, ir, poly=True)
    sphere(f"{prefix}Orb", 0.16 * s, (x, y, z + 0.75 * s), gl, seg=14, rings=7)
    tube(f"{prefix}Shaft", [(x, y, z + 1.2 * s), (x, y, z + 2.35 * s)], 0.045 * s, gl, poly=True)
    for k, zz in enumerate((1.35, 1.6)):
        box(f"{prefix}Bit{k}", (0.28 * s, 0.06 * s, 0.1 * s), (x + 0.16 * s, y, z + zz * s), gl, bevel=0.01 * s)
    hoop(f"{prefix}Bow", (x, y, z + 2.62 * s), 0.27 * s, "Y", gl, thick=0.045 * s)
    foil(f"{prefix}BowFoil", x, y - 0.01 * s, z + 2.62 * s, 0.15 * s, gl, lobes=4, thick=0.02 * s)


def lucarne(prefix, K, w=1.4, h=1.2, hg=0.8, dpt=1.6, mat=None):
    """A little gabled vent dormer built at the origin facing -Y (its front foot at y = 0, running back to +Y): a stone
    face with a dark pointed opening and lead louvres, slate-hung cheeks and roof, a spike on the gable."""
    st = mat or K["st"]
    face = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h), (0.0, h + hg), (-w / 2, h)]
    B20.tprism(f"{prefix}Face", WS.ccw(face), 0.06, 0.12, st)
    op = WS.arch(w * 0.26, 0.15, h * 0.75, h + hg * 0.45, 8)
    B20.tprism(f"{prefix}Hole", WS.ccw(op), -0.008, 0.012, K["hollow"])
    for k in range(4):
        zz = 0.3 + k * (h * 0.75 - 0.2) / 3.5
        box(f"{prefix}Louvre{k}", (w * 0.5, 0.05, 0.04), (0, -0.03, zz), K["lead"], bevel=0.0, segments=1, rot=(0.5, 0, 0))
    tube(f"{prefix}Rim", [(x, -0.025, z) for x, z in WS.offset(WS.ccw(op), 0.04)], 0.03, K["dk"], closed=True, square=True, poly=True)
    for sx in (-1, 1):
        box(f"{prefix}Cheek{sx}", (0.06, dpt - 0.12, h), (sx * (w / 2 - 0.04), 0.12 + (dpt - 0.12) / 2, h / 2), K["slate"], bevel=0.0, segments=1)
    chevron(f"{prefix}Roof", [(-w / 2 - 0.14, h - 0.06), (0.0, h + hg + 0.02), (w / 2 + 0.14, h - 0.06)], 0.08, 0.0, (dpt - 0.14) / 2, dpt + 0.14,
            K["slate"], plane="XZ")
    _spike(f"{prefix}Spike", (0, -0.07, h + hg + 0.3), 0.05, 0.5, K["iron"], verts=4)


def _place(s, p, out):
    """Turn the parts built since s (facing -Y at the origin) to face along `out`, and move them to p."""
    _xform(s, Matrix.Translation(p) @ Matrix.Rotation(math.atan2(out[0], -out[1]), 4, "Z"))


def _moss_on(K, rnd, pts, size=0.13):
    _moss("Moss", pts, K["moss"], rnd, size=size)


# ================================================================== gable roofs

def _eaves(prefix, R, x0, x1, K, front=True, back=True, corbels=True):
    """The cornice and gutter along the long sides of a W x D wall top, from x0 to x1."""
    D = R.D
    for s, ok in ((-1, front), (1, back)):
        if not ok:
            continue
        path = [(x0, s * D / 2), (x1, s * D / 2)] if s < 0 else [(x1, s * D / 2), (x0, s * D / 2)]
        cornice(f"{prefix}Cornice{s}", path, K, closed=False, corbels=corbels)
        gp = [(x0 + 0.02, s * (D / 2 + CP + 0.02)), (x1 - 0.02, s * (D / 2 + CP + 0.02))]
        gutter(f"{prefix}Gutter{s}", gp if s < 0 else list(reversed(gp)), R.ze - 0.03, K)


def _kneeler(prefix, x, sy, R, K):
    """The springer stone at the foot of a parapet gable's coping, corbelled out over the eaves."""
    D = R.D
    zk = R.z_top(D / 2) + 0.45
    y0, y1 = D / 2 - 0.35, R.ye + 0.12
    z0, z1 = ZP - 0.4, zk + 0.22
    box(f"{prefix}", (1.1, y1 - y0, z1 - z0), (x, sy * (y0 + y1) / 2, (z0 + z1) / 2), K["dk"], bevel=0.05)
    box(f"{prefix}Corbel", (0.84, 0.75, 0.42), (x, sy * (D / 2 + 0.33), z0 - 0.21), K["st"], bevel=0.05)
    if sy < 0:
        foil(f"{prefix}Foil", x, -(y1 + 0.012), (z0 + z1) / 2, 0.24, K["st"], lobes=4, thick=0.028)


def _parapet_gable(prefix, R, K, sx, finial=True):
    W, D = R.W, R.D
    x = sx * (W / 2 - 0.4)
    zk, za = gable_wall(f"{prefix}Wall", sx * W / 2, sx * (W / 2 - 0.8), R, K, parapet=0.45)
    ye = R.ye + 0.05
    chevron(f"{prefix}Coping", [(-ye, zk - (ye - D / 2) * R.t), (0.0, za), (ye, zk - (ye - D / 2) * R.t)], 0.2, 0.14, x, 1.04, K["dk"])
    for sy in (-1, 1):
        _kneeler(f"{prefix}Kneeler{sy}", x, sy, R, K)
    if finial:
        _spirelet(f"{prefix}Pinnacle", x, 0, za + 0.18, 2.0, 0.56, K["dk"], crockets=2)
        sphere(f"{prefix}PinnacleOrb", 0.1, (x, 0, za + 2.28), K["gilt"], seg=10, rings=5)
    return zk, za


def gable_roof(M):
    """45 degrees: stone-coped parapet gables on kneelers with crocketed pinnacles, slates, crimson ridge tiles and
    iron cresting, cornices on corbels and cast-iron gutters."""
    K = kit(M)
    rnd = random.Random(2801)
    R = Pitch(16.0, 12.0, 45)
    W, D = R.W, R.D
    R.roof("Roof", -(W / 2 - 0.4), W / 2 - 0.4, "Slate", K)
    _eaves("E", R, -(W / 2 - 0.1), W / 2 - 0.1, K)
    for sx in (-1, 1):
        _parapet_gable(f"Gable{sx}", R, K, sx)
    ridge_tiles("Ridge", -(W / 2 - 0.7), W / 2 - 0.7, R.top - 0.08, K, knobs=False)
    cresting("Crest", -(W / 2 - 1.2), W / 2 - 1.2, R.top + 0.17, K)
    _moss_on(K, rnd, [(-5.2, -R.ye + 0.5, R.z_top(R.ye - 0.5)), (3.9, -R.ye + 0.7, R.z_top(R.ye - 0.7)), (-1.0, R.ye - 0.6, R.z_top(R.ye - 0.6))])
    return _dims()


def gable_section(M):
    """An 8-stud run of the 45 degree gable roof with open ends, to lengthen GableRoof or join it to RoofCornerL."""
    K = kit(M)
    R = Pitch(16.0, 12.0, 45)
    L = 4.0
    R.roof("Roof", -L, L, "Slate", K)
    _eaves("E", R, -L, L, K, corbels=True)
    ridge_tiles("Ridge", -L, L, R.top - 0.08, K, knobs=False)
    cresting("Crest", -L + 0.45, L - 0.45, R.top + 0.17, K)
    return _dims()


def gable_roof_low(M):
    """30 degrees: a low roof for the town and the outbuildings: slates over the gable walls, lead verges and a lead
    ridge roll, a plain cornice and gutters."""
    K = kit(M)
    rnd = random.Random(2802)
    R = Pitch(16.0, 12.0, 30)
    W, D = R.W, R.D
    XE = W / 2 + 0.75
    R.roof("Roof", -XE, XE, "Slate", K)
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=False)
    gp = rect_path(W / 2 + CP + 0.02, D / 2 + CP + 0.02)
    gutter("GutterF", [gp[0], gp[1]], R.ze - 0.03, K)
    gutter("GutterB", [gp[2], gp[3]], R.ze - 0.03, K)
    for sx in (-1, 1):
        gable_wall(f"GableWall{sx}", sx * W / 2, sx * (W / 2 - 0.8), R, K)
        chevron(f"Verge{sx}", [(-R.ye - 0.03, R.ze + 0.1), (0.0, R.Hb + 0.12 / R.c), (R.ye + 0.03, R.ze + 0.1)], 0.2, 0.1, sx * (XE + 0.02), 0.09, K["lead"])
    lead_roll("RidgeRoll", [(-XE - 0.06, 0, R.top - 0.01), (XE + 0.06, 0, R.top - 0.01)], K, r=0.13)
    for sx in (-1, 1):
        _spike(f"Spike{sx}", (sx * (XE - 0.1), 0, R.top + 0.4), 0.06, 0.65, K["iron"], verts=4)
        sphere(f"SpikeKnob{sx}", 0.09, (sx * (XE - 0.1), 0, R.top + 0.14), K["iron"], seg=10, rings=5)
    _moss_on(K, rnd, [(-3.0, -R.ye + 0.4, R.z_top(R.ye - 0.4)), (5.5, R.ye - 0.5, R.z_top(R.ye - 0.5)), (1.4, -R.ye + 0.3, R.z_top(R.ye - 0.3))])
    return _dims()


def gable_roof_steep(M):
    """60 degrees: a tall gothic roof with the slates run out over the gables on cusped crimson-enamel iron
    bargeboards, pendant drops and spiked hip knobs, a lead ridge with tall cresting."""
    K = kit(M)
    rnd = random.Random(2803)
    R = Pitch(16.0, 12.0, 60, ov=0.3)
    W, D = R.W, R.D
    XE = W / 2 + 0.7
    R.roof("Roof", -XE, XE, "Slate", K)
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=True)
    gp = rect_path(W / 2 + CP + 0.02, D / 2 + CP + 0.02)
    gutter("GutterF", [gp[0], gp[1]], R.ze - 0.03, K)
    gutter("GutterB", [gp[2], gp[3]], R.ze - 0.03, K)
    for sx in (-1, 1):
        gable_wall(f"GableWall{sx}", sx * W / 2, sx * (W / 2 - 0.8), R, K)
        # the bargeboard: a band under the verge, its lower edge cut into cusps, gilt studs along it
        n = 40
        ys = [-R.ye + 2 * R.ye * i / n for i in range(n + 1)]
        if 0.0 not in ys:
            ys = sorted(ys + [0.0])
        top = [(y, R.z_under(y) + 0.06) for y in ys]
        bot = [(y, R.z_under(y) - 0.06 - 0.3 - 0.16 * abs(math.sin(abs(y) / 0.9 * math.pi))) for y in ys]
        B20.tprism(f"Barge{sx}", WS.ccw(top + list(reversed(bot))), sx * (XE - 0.06), 0.07, K["enamel"], plane="YZ")
        for k in range(-6, 7):
            y = k * 0.9
            if abs(y) > R.ye - 0.3:
                continue
            sphere(f"BargeStud{sx}{k}", 0.045, (sx * (XE - 0.015), y, R.z_under(y) - 0.14), K["gilt"], seg=8, rings=4, scale=(0.5, 1, 1))
        lathe(f"Pendant{sx}", [(0, -0.9), (0.06, -0.85), (0.14, -0.6), (0.12, -0.4), (0.07, -0.25), (0.1, -0.1), (0.1, 0.0), (0, 0.0)], K["iron"], seg=12,
              loc=(sx * (XE - 0.06), 0, R.Hb - 0.05))
        sphere(f"PendantGilt{sx}", 0.08, (sx * (XE - 0.06), 0, R.Hb - 0.97), K["gilt"], seg=10, rings=5)
        _spike(f"HipKnob{sx}", (sx * (XE - 0.2), 0, R.top + 0.75), 0.06, 1.1, K["iron"], verts=4)
        sphere(f"HipKnobOrb{sx}", 0.13, (sx * (XE - 0.2), 0, R.top + 0.3), K["gilt"], seg=12, rings=6)
    lead_roll("RidgeRoll", [(-XE - 0.05, 0, R.top - 0.01), (XE + 0.05, 0, R.top - 0.01)], K, r=0.14)
    cresting("Crest", -(XE - 0.7), XE - 0.7, R.top + 0.1, K, h=1.15, step=1.0)
    _moss_on(K, rnd, [(-4.4, -R.ye + 0.35, R.z_top(R.ye - 0.35)), (6.0, R.ye - 0.4, R.z_top(R.ye - 0.4))])
    return _dims()


# ================================================================== hipped and pyramid roofs

def hip_planes(xe, ye, ze, t):
    """The four planes of a hipped roof over the eave rectangle (+-xe, +-ye) at ze, all at slope t: lists of corners."""
    xr = max(0.0, xe - ye)
    zr = ze + ye * t
    A, B, C, Dd = (-xe, -ye, ze), (xe, -ye, ze), (xe, ye, ze), (-xe, ye, ze)
    if xr > 1e-4:
        r0, r1 = (-xr, 0.0, zr), (xr, 0.0, zr)
        return [[A, B, r1, r0], [B, C, r1], [C, Dd, r0, r1], [Dd, A, r0]], zr, xr
    r = (0.0, 0.0, zr)
    return [[A, B, r], [B, C, r], [C, Dd, r], [Dd, A, r]], zr, 0.0


def hipped_layers(prefix, xe, ye, ze, t, tile, K, ov_inset=0.06):
    """Slate on a lead underlay over a hipped (or pyramid) roof: every plane lifted straight up by the layer's depth.
    Returns the slates' top at the ridge and the ridge's half length."""
    c = math.cos(math.atan(t))
    planes, zr, xr = hip_planes(xe, ye, ze, t)
    lo, hi = (TS - 0.02) / c, (2 * TS - 0.02) / c
    for k, pl in enumerate(planes):
        tiled(tile)
        solid(f"{prefix}Slate{k}", [(x, y, z + lo) for x, y, z in pl], [(x, y, z + hi) for x, y, z in pl], K["tile"])
    d = ov_inset
    planes2, _, _ = hip_planes(xe - d, ye - d, ze + d * t, t)
    for k, pl in enumerate(planes2):
        tiled("Lead")
        solid(f"{prefix}Under{k}", list(pl), [(x, y, z + TS / c) for x, y, z in pl], K["tile"])
    set_group("Main")
    return zr + hi, xr


def _hips(prefix, xe, ye, ze, top, xr, lift, K, irons=True):
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = (sx * xe, sy * ye, ze + lift)
            lead_roll(f"{prefix}{sx}{sy}", [(a[0] - sx * 0.05, a[1] - sy * 0.05, a[2] + 0.02), (sx * xr, 0.0, top)], K, r=0.11)
            if irons:
                tube(f"{prefix}Iron{sx}{sy}", [(a[0], a[1], a[2] + 0.05), (a[0] + sx * 0.18, a[1] + sy * 0.18, a[2] - 0.05),
                                                (a[0] + sx * 0.22, a[1] + sy * 0.22, a[2] - 0.28), (a[0] + sx * 0.08, a[1] + sy * 0.08, a[2] - 0.3)], 0.025, K["iron"])


def hip_roof(M):
    """45 degrees, hipped all round: lead hip rolls with scrolled hip irons, a short crimson-tiled ridge with cresting,
    gilt-mooned hip knobs, a corbelled cornice and gutters all the way round."""
    K = kit(M)
    rnd = random.Random(2804)
    W, D, pitch, ov = 16.0, 12.0, 45, 0.45
    t = math.tan(math.radians(pitch))
    xe, ye = W / 2 + SPRING + ov, D / 2 + SPRING + ov
    ze = ZP - ov * t
    top, xr = hipped_layers("Roof", xe, ye, ze, t, "Slate", K)
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=True)
    gutter("Gutter", rect_path(W / 2 + CP + 0.02, D / 2 + CP + 0.02), ze - 0.03, K, closed=True)
    lift = (2 * TS - 0.02) / math.cos(math.radians(pitch))
    _hips("Hip", xe, ye, ze, top, xr, lift, K)
    ridge_tiles("Ridge", -xr - 0.15, xr + 0.15, top - 0.08, K, knobs=False)
    cresting("Crest", -xr + 0.4, xr - 0.4, top + 0.17, K)
    for sx in (-1, 1):
        moon_finial(f"Knob{sx}", sx * (xr + 0.1), 0, top - 0.1, K, h=1.8, s=0.8)
    _moss_on(K, rnd, [(-4.0, -ye + 0.5, ze + 0.5 + lift), (5.2, ye - 0.6, ze + 0.6 + lift), (xe - 0.5, 1.5, ze + 0.5 + lift)])
    return _dims()


# ================================================================== turret caps and spires

def cone_turret_cap(M):
    """A round turret's cap of fish-scale slates, bell-cast at the eaves, on a corbelled cornice; four louvred
    lucarnes, a lead apex and an iron finial with a gilt crescent moon. For a round tower 8 across."""
    K = kit(M)
    r0, H = 4.0, 11.2
    cornice("Cornice", poly_path(r0, 40), K, closed=True, corbels=True, step=0.9)
    re = r0 + SPRING + 0.5
    za = ZP + H
    rs, zs = r0 - 0.2, ZP + 1.9
    prof = [(0.0, ZP + 0.02), (r0 - 0.2, ZP + 0.02), (re, ZP - 0.12), (re + 0.03, ZP + 0.02), (re - 0.32, ZP + 0.42), (re - 0.75, ZP + 1.1), (rs, zs)]
    for k in range(1, 9):
        u = k / 8
        prof.append((rs * (1 - u) + 0.14 * u, zs + (za - zs) * u))
    prof.append((0.0, za + 0.05))
    tiled("Scale")
    tlathe("Cone", prof, "Scale", seg=48, mat=K["tile"])
    set_group("Main")

    def r_at(z):
        return rs + (0.14 - rs) * (z - zs) / (za - zs)
    zsl = za - 0.9
    lathe("ApexLead", [(0, zsl), (r_at(zsl) + 0.07, zsl), (r_at(zsl) + 0.1, zsl + 0.12), (0.2, zsl + 0.55), (0.13, zsl + 1.0), (0, zsl + 1.0)], K["lead"],
          seg=20)
    moon_finial("Finial", 0, 0, zsl + 0.95, K, h=2.6)
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        zb = ZP + 3.0
        rf = r_at(zb) + 0.06
        s = _mark()
        lucarne(f"Lucarne{k}", K, w=1.3, h=1.15, hg=0.75, dpt=1.7)
        _place(s, (math.cos(a) * rf, math.sin(a) * rf, zb), (math.cos(a), math.sin(a)))
    return _dims()


def octagon_spire(M):
    """A tall octagonal slate spire for a tower 8 across: lead hip rolls, two tiers of louvred lucarnes, a crocketed
    pinnacle at each corner of the cornice, and the crest's gilt key on top."""
    K = kit(M)
    ap = 4.0                                          # the tower's apothem
    rc = ap / math.cos(math.pi / 8)
    cornice("Cornice", poly_path(rc, 8), K, closed=True, corbels=True, step=1.1)
    a0 = 3.85                                         # the spire's foot sits on the cornice's top
    H = 14.0
    base = poly_path(a0 / math.cos(math.pi / 8), 8)
    zb, za = ZP - 0.04, ZP + H
    tiled("Slate")
    verts = [(x, y, zb) for x, y in base] + [(0.0, 0.0, za)]
    faces = [list(range(8))[::-1]] + [[i, (i + 1) % 8, 8] for i in range(8)]
    mk("Spire", verts, faces, K["tile"])
    set_group("Main")
    for i, (x, y) in enumerate(base):
        lead_roll(f"Hip{i}", [(x * 1.02, y * 1.02, zb + 0.06), (0.0, 0.0, za - 0.35)], K, r=0.085)
    lathe("ApexLead", [(0, za - 1.2), (0.62, za - 1.2), (0.66, za - 1.05), (0.3, za - 0.4), (0.16, za + 0.1), (0, za + 0.1)], K["lead"], seg=16)
    key_finial("Key", 0, 0, za, K, s=1.25)

    def ap_at(z):
        return a0 * (za - z) / (za - zb)
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        big = k % 2 == 0
        zl = ZP + (2.2 if big else 6.2)
        rf = ap_at(zl) + 0.05
        s = _mark()
        if big:
            lucarne(f"Lucarne{k}", K, w=1.5, h=1.3, hg=0.85, dpt=2.0)
        else:
            lucarne(f"Lucarne{k}", K, w=0.95, h=0.85, hg=0.55, dpt=1.6)
        _place(s, (math.cos(a) * rf, math.sin(a) * rf, zl), (math.cos(a), math.sin(a)))
    for i, (x, y) in enumerate(poly_path(rc - 0.08, 8)):
        _spirelet(f"Pinnacle{i}", x, y, ZP, 1.7, 0.4, K["dk"], crockets=2)
    return _dims()



# ------------------------------------------------------------------ more helpers

def radial(poly, cx, cz, n, a0=-math.pi / 2):
    """Sample a star-shaped outline (x, z) by n rays from (cx, cz), starting straight down and going counter-clockwise,
    so two outlines sampled the same way can be bridged face to face."""
    out = []
    for k in range(n):
        a = a0 + k / n * 2 * math.pi
        u = (math.cos(a), math.sin(a))
        best = None
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            ex, ez = q[0] - p[0], q[1] - p[1]
            den = u[0] * ez - u[1] * ex
            if abs(den) < 1e-9:
                continue
            wx, wz = p[0] - cx, p[1] - cz
            t = (wx * ez - wz * ex) / den
            s = (wx * u[1] - wz * u[0]) / den
            if t > 1e-6 and -1e-6 <= s <= 1 + 1e-6 and (best is None or t < best):
                best = t
        out.append((cx + u[0] * best, cz + u[1] * best))
    return out


def holed(name, outer, inner, cx, cz, y0, y1, mat, n=48):
    """A plate in the XZ plane from y0 to y1 with one opening: the outline and the hole are both sampled from (cx, cz)
    and bridged, so the piece is one clean closed solid (no boolean)."""
    o = radial(outer, cx, cz, n)
    i = radial(inner, cx, cz, n)
    verts = [(x, y0, z) for x, z in o] + [(x, y1, z) for x, z in o] + [(x, y0, z) for x, z in i] + [(x, y1, z) for x, z in i]
    faces = []
    for k in range(n):
        j = (k + 1) % n
        faces.append((k, j, 2 * n + j, 2 * n + k))                    # front ring
        faces.append((n + k, 3 * n + k, 3 * n + j, n + j))            # back ring
        faces.append((k, n + k, n + j, j))                            # outer side
        faces.append((2 * n + k, 2 * n + j, 3 * n + j, 3 * n + k))    # the opening's reveal
    return mk(name, verts, faces, mat)


def run_along(s, p0, p1):
    """Move parts built since s along +X from the origin onto the plan line p0 -> p1."""
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    _xform(s, Matrix.Translation((p0[0], p0[1], 0)) @ Matrix.Rotation(a, 4, "Z"))


def crest_run(prefix, p0, p1, z, K, h=0.7, step=0.9, inset=0.0):
    s = _mark()
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    cresting(prefix, inset, L - inset, z, K, h=h, step=step)
    run_along(s, p0, p1)


def lead_cap(prefix, z, r, K, h=1.0, seg=16):
    lathe(f"{prefix}", [(0, z), (r, z), (r + 0.04, z + 0.12), (r * 0.5, z + h * 0.55), (r * 0.32, z + h), (0, z + h)], K["lead"], seg=seg)


def slab2(name, a, b, x0, x1, lift, thick, mat, ridge=False):
    """A slab on the plane through the lines (x0..x1, a) and (x0..x1, b), a and b (y, z) up the slope (a lower);
    with ridge the upper end is cut vertical at b's y."""
    a, b = Vector((0, a[0], a[1])), Vector((0, b[0], b[1]))
    d = (b - a).normalized()
    n = Vector((0, -d.z, d.y)) if d.y > 0 else Vector((0, d.z, -d.y))
    if n.z < 0:
        n = -n
    def at(p, x, h):
        q = Vector((x, p.y, p.z)) + n * h
        if ridge and p is b:
            q = Vector((x, b.y, b.z + h / max(n.z, 1e-3)))
        return q
    bot = [at(a, x0, lift), at(a, x1, lift), at(b, x1, lift), at(b, x0, lift)]
    top = [at(a, x0, lift + thick), at(a, x1, lift + thick), at(b, x1, lift + thick), at(b, x0, lift + thick)]
    return solid(name, bot, top, mat)


def profile_roof(prefix, x0, x1, prof, tile, K, ext=0.12, under_x=0.05):
    """A roof along X from a section: prof is [(y, z), ...] from the front eave over the ridge to the back eave.
    Each plane gets slate on a lead underlay; the planes run a little past each knuckle into their neighbours, and stop
    vertical at the ridge (the middle point, y = 0)."""
    mid = len(prof) // 2
    for k in range(len(prof) - 1):
        a, b = prof[k], prof[k + 1]
        lo, hi = (a, b) if a[1] < b[1] else (b, a)
        ridge = abs(hi[0]) < 1e-6
        L = math.hypot(hi[0] - lo[0], hi[1] - lo[1])
        u = ((hi[0] - lo[0]) / L, (hi[1] - lo[1]) / L)
        lo_top = (lo[0], lo[1]) if k in (0, len(prof) - 2) else (lo[0] - u[0] * ext, lo[1] - u[1] * ext)
        hi_top = hi if ridge else (hi[0] + u[0] * ext, hi[1] + u[1] * ext)
        tiled(tile)
        slab2(f"{prefix}Slate{k}", lo_top, hi_top, x0, x1, TS - 0.02, TS, K["tile"], ridge=ridge)
        tiled("Lead")
        lo_u = (lo[0] + u[0] * 0.06, lo[1] + u[1] * 0.06) if k in (0, len(prof) - 2) else lo_top
        slab2(f"{prefix}Under{k}", lo_u, hi_top, x0 + under_x, x1 - under_x, 0.0, TS, K["tile"], ridge=ridge)
    set_group("Main")
    return mid


# ================================================================== pyramid, mansard, gambrel, lean-to

def pyramid_roof(M):
    """A tower's tall pyramid roof (12 x 12, 55 degrees): slates, lead hips, a louvred lucarne on every face, and a
    tall finial with gilt orbs and a crescent moon."""
    K = kit(M)
    rnd = random.Random(2805)
    W, pitch, ov = 12.0, 55, 0.45
    t = math.tan(math.radians(pitch))
    e = W / 2 + SPRING + ov
    ze = ZP - ov * t
    top, _ = hipped_layers("Roof", e, e, ze, t, "Slate", K)
    cornice("Cornice", rect_path(W / 2, W / 2), K, closed=True, corbels=True)
    gutter("Gutter", rect_path(W / 2 + CP + 0.02, W / 2 + CP + 0.02), ze - 0.03, K, closed=True)
    lift = (2 * TS - 0.02) / math.cos(math.radians(pitch))
    _hips("Hip", e, e, ze, top - 0.25, 0.0, lift, K)
    lead_cap("Apex", top - 0.8, 0.92, K, h=1.1)
    moon_finial("Finial", 0, 0, top + 0.15, K, h=3.4, s=1.3)
    zl = ze + lift + 2.2
    yf = e - (zl - ze - lift) / t + 0.04
    for k in range(4):
        a = -math.pi / 2 + k * math.pi / 2
        s = _mark()
        lucarne(f"Lucarne{k}", K, w=1.6, h=1.3, hg=0.9, dpt=2.2)
        _place(s, (math.cos(a) * yf, math.sin(a) * yf, zl), (math.cos(a), math.sin(a)))
    _moss_on(K, rnd, [(-3.0, -e + 0.5, ze + lift + 0.6), (e - 0.6, 2.4, ze + lift + 0.75)])
    return _dims()


def oxeye(prefix, K, r=0.6, hw=0.95, zc=0.95, dpt=1.4):
    """A round oeil-de-boeuf dormer built facing -Y at the origin: a moulded stone face with a round light (an iron
    quatrefoil, glass, the warm room behind), a lead bonnet over it, lead cheeks, a lead apron at its foot."""
    outer = WS.roundhead(hw, 0.0, zc, n=20)
    inner = WS.circle(0.0, zc, r, n=48)
    holed(f"{prefix}Face", outer, inner, 0.0, zc, -0.1, 0.08, K["st"], n=48)
    tube(f"{prefix}Roll", [(x, -0.12, z) for x, z in WS.circle(0, zc, r + 0.07, n=32)], 0.06, K["dk"], closed=True, square=True, poly=True)
    for k in range(4):
        a = math.pi / 2 + k * math.pi / 2
        box(f"{prefix}Key{k}", (0.22, 0.12, 0.3), (math.cos(a) * (r + 0.1), -0.11, zc + math.sin(a) * (r + 0.1)), K["dk"], bevel=0.03,
            rot=(0, -a + math.pi / 2, 0))
    tube(f"{prefix}Quatrefoil", [(x, -0.04, z) for x, z in WS.foil_outline(0, zc, r * 0.78, 4, n=40)], 0.022, K["iron"], closed=True, square=True, poly=True)
    tube(f"{prefix}BarV", [(0, -0.04, zc - r), (0, -0.04, zc + r)], 0.02, K["iron"], square=True, poly=True)
    tube(f"{prefix}BarH", [(-r, -0.04, zc), (r, -0.04, zc)], 0.02, K["iron"], square=True, poly=True)
    set_group("Glass")
    B20.tprism(f"{prefix}Pane", WS.circle(0, zc, r + 0.03, n=32), -0.01, 0.02, K["glass"])
    set_group("Room")
    B20.tprism(f"{prefix}Room", WS.circle(0, zc, r + 0.03, n=32), 0.12, 0.02, flat("RoomTmp", (0.5, 0.3, 0.1), 0.9))
    set_group("Main")
    rb = hw + 0.08
    rows = []
    for yy in (-0.2, dpt):
        rows.append([Vector((math.cos(math.pi * k / 16) * rb, yy, zc + math.sin(math.pi * k / 16) * rb)) for k in range(17)])
    from nh_props_batch4 import _mesh
    _mesh(f"{prefix}Bonnet", rows, K["lead"], 0.07)
    tube(f"{prefix}BonnetRoll", [(math.cos(math.pi * k / 16) * (rb + 0.03), -0.2, zc + math.sin(math.pi * k / 16) * (rb + 0.03)) for k in range(17)], 0.04,
         K["lead"], square=True, poly=True)
    for sx in (-1, 1):
        box(f"{prefix}Cheek{sx}", (0.06, dpt - 0.08, zc), (sx * (hw - 0.01), 0.08 + (dpt - 0.08) / 2, zc / 2), K["lead"], bevel=0.0, segments=1)


def mansard_roof(M):
    """A mansard on a 16 x 12 wall top: steep fish-scale slate sides with lead corner rolls and four round
    oeil-de-boeuf dormers, a moulded curb with iron cresting all round, and a low lead roof above."""
    K = kit(M)
    rnd = random.Random(2806)
    W, D = 16.0, 12.0
    p1, hl, ov = math.radians(72), 4.2, 0.25
    t1 = math.tan(p1)
    xe, ye = W / 2 + SPRING + ov, D / 2 + SPRING + ov
    ze = ZP - ov * t1
    dI = hl / t1
    xc, yc, zc = xe - dI, ye - dI, ze + hl
    c1 = math.cos(p1)
    lo, hi = (TS - 0.02) / c1, (2 * TS - 0.02) / c1
    outer = [(-xe, -ye), (xe, -ye), (xe, ye), (-xe, ye)]
    curb = [(-xc, -yc), (xc, -yc), (xc, yc), (-xc, yc)]
    for k in range(4):
        j = (k + 1) % 4
        pl = [(*outer[k], ze), (*outer[j], ze), (*curb[j], zc), (*curb[k], zc)]
        tiled("Scale")
        solid(f"LowerSlate{k}", [(x, y, z + lo) for x, y, z in pl], [(x, y, z + hi) for x, y, z in pl], K["tile"])
        d = 0.06
        pin = [(x * (1 - d / abs(x)) if abs(x) > 0 else x, y * (1 - d / abs(y)) if abs(y) > 0 else y, z) for x, y, z in pl[:2]] + pl[2:]
        tiled("Lead")
        solid(f"LowerUnder{k}", [(x, y, z + 0.0) for x, y, z in pin], [(x, y, z + TS / c1) for x, y, z in pin], K["tile"])
    set_group("Main")
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=False)
    gutter("Gutter", rect_path(W / 2 + CP + 0.02, D / 2 + CP + 0.02), ze - 0.03, K, closed=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lead_roll(f"Corner{sx}{sy}", [(sx * (xe - 0.03), sy * (ye - 0.03), ze + hi + 0.02), (sx * (xc + 0.02), sy * (yc + 0.02), zc + hi)], K, r=0.1)
    # the curb: a lead-clad moulded rail where the slopes meet, and the low lead roof above
    zr = zc + hi
    mould("Curb", rect_path(xc + 0.12, yc + 0.12), [(-0.55, zr - 0.35), (0.0, zr - 0.35), (0.1, zr - 0.25), (0.14, zr - 0.05), (0.1, zr + 0.1),
                                                     (0.0, zr + 0.16), (-0.55, zr + 0.16)], K["lead"], closed=True)
    t2 = math.tan(math.radians(18))
    top, xr = hipped_layers("Upper", xc + 0.05, yc + 0.05, zr + 0.04, t2, "Lead", K)
    path = rect_path(xc + 0.04, yc + 0.04)
    for k in range(4):
        crest_run(f"Crest{k}", path[k], path[(k + 1) % 4], zr + 0.14, K, h=0.55, step=1.2, inset=0.4)
    for sx in (-1, 1):
        moon_finial(f"Knob{sx}", sx * xr, 0, top - 0.04, K, h=1.6, s=0.75)
    # oeil-de-boeuf dormers, two to the front and two to the back
    zb = ze + lo + 1.0
    yf = ye - (zb - ze - lo) / t1 + 0.12
    for sy in (-1, 1):
        for x in (-3.6, 3.6):
            s = _mark()
            oxeye(f"Oxeye{sy}{x:+.0f}", K, dpt=1.3)
            _place(s, (x, sy * yf, zb), (0, sy))
    _moss_on(K, rnd, [(-6.3, -(D / 2 + 0.5), ZP + 0.03), (5.0, D / 2 + 0.5, ZP + 0.03)])
    return _dims()


def gambrel_roof(M):
    """A gambrel (barn) roof on a 16 x 12 wall top: steep lower slopes and shallow upper ones in slate, lead rolls at
    the knuckles and the ridge, gable walls of castle stone with a round louvred vent, lead verges."""
    K = kit(M)
    rnd = random.Random(2807)
    W, D = 16.0, 12.0
    pl, pu, ov = math.radians(62), math.radians(26), 0.4
    ys = D / 2 + SPRING
    yk = ys - 3.6 / math.tan(pl)
    zk = ZP + 3.6
    zr = zk + yk * math.tan(pu)
    ye = ys + ov
    ze = ZP - ov * math.tan(pl)
    prof = [(-ye, ze), (-yk, zk), (0.0, zr), (yk, zk), (ye, ze)]
    XE = W / 2 + 0.7
    profile_roof("Roof", -XE, XE, prof, "Slate", K)
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=False)
    gp = rect_path(W / 2 + CP + 0.02, D / 2 + CP + 0.02)
    gutter("GutterF", [gp[0], gp[1]], ze - 0.03, K)
    gutter("GutterB", [gp[2], gp[3]], ze - 0.03, K)
    cl, cu = math.cos(pl), math.cos(pu)
    for sx in (-1, 1):
        wall = [(-D / 2, ZP - 0.06), (D / 2, ZP - 0.06), (D / 2, ZP + SPRING * math.tan(pl) + 0.05), (yk, zk + 0.05), (0.0, zr + 0.05),
                (-yk, zk + 0.05), (-D / 2, ZP + SPRING * math.tan(pl) + 0.05)]
        tiled("Stone")
        B20.tprism(f"GableWall{sx}", WS.ccw(wall), sx * (W / 2 - 0.4), 0.8, K["tile"], plane="YZ")
        set_group("Main")
        vpts = [(-ye - 0.03, ze + 0.1), (-yk, zk + 0.12 / cl + 0.02), (0.0, zr + 0.12 / cu), (yk, zk + 0.12 / cl + 0.02), (ye + 0.03, ze + 0.1)]
        chevron(f"Verge{sx}", vpts, 0.2, 0.1, sx * (XE + 0.02), 0.09, K["lead"])
        # a round louvred vent in the gable
        s = _mark()
        zv = zk - 0.6
        hoop(f"Vent{sx}Ring", (0, -0.06, zv), 0.72, "Y", K["dk"], thick=0.11)
        B20.tprism(f"Vent{sx}Hole", WS.circle(0, zv, 0.68, n=32), 0.01, 0.04, K["hollow"])
        for k in range(5):
            zz = zv - 0.5 + k * 0.25
            hw = math.sqrt(max(0.0, 0.66 ** 2 - (zz - zv) ** 2))
            box(f"Vent{sx}Louvre{k}", (2 * hw, 0.05, 0.05), (0, -0.04, zz), K["lead"], bevel=0.0, segments=1, rot=(0.6, 0, 0))
        for k in range(4):
            a = k * math.pi / 2
            box(f"Vent{sx}Key{k}", (0.24, 0.14, 0.3), (math.cos(a) * 0.8, -0.08, zv + math.sin(a) * 0.8), K["dk"], bevel=0.03, rot=(0, -a + math.pi / 2, 0))
        _xform(s, Matrix.Translation((sx * W / 2, 0, 0)) @ Matrix.Rotation(sx * math.pi / 2, 4, "Z"))
    for k, (y, z) in enumerate(((-yk, zk), (yk, zk))):
        lead_roll(f"Knuckle{k}", [(-XE - 0.04, y, z + 0.15), (XE + 0.04, y, z + 0.15)], K, r=0.11)
    lead_roll("RidgeRoll", [(-XE - 0.05, 0, zr + 0.25), (XE + 0.05, 0, zr + 0.25)], K, r=0.13)
    for sx in (-1, 1):
        _spike(f"Spike{sx}", (sx * (XE - 0.1), 0, zr + 0.75), 0.06, 0.7, K["iron"], verts=4)
        sphere(f"SpikeKnob{sx}", 0.1, (sx * (XE - 0.1), 0, zr + 0.45), K["gilt"], seg=10, rings=5)
    _moss_on(K, rnd, [(-2.0, -ye + 0.4, ze + 0.9), (6.2, ye - 0.5, ze + 1.0)])
    return _dims()


def lean_to_roof(M):
    """A lead lean-to against a taller wall (12 x 6, 25 degrees, its back flat at y = +3): castle-stone cheeks,
    lead verges, a cast-iron valance of crimson cusps along the eaves and a lead flashing up the wall."""
    K = kit(M)
    W, D = 12.0, 6.0
    p = math.radians(25)
    t = math.tan(p)
    c = math.cos(p)
    ov = 0.5
    ys = -(D / 2 + SPRING)
    ye = ys - ov
    ze = ZP - ov * t
    zb = ZP + (D / 2 - 0.02 - ys) * t                       # the underside at the back wall
    yb = D / 2 - 0.02
    XE = W / 2 + 0.55
    tiled("Lead")
    slab2("RoofLead", (ye, ze), (yb, zb), -XE, XE, 0.0, 0.22, K["tile"])
    set_group("Main")
    path = [(-W / 2, D / 2 - 0.05), (-W / 2, -D / 2), (W / 2, -D / 2), (W / 2, D / 2 - 0.05)]
    cornice("Cornice", path, K, closed=False, corbels=True)
    for sx in (-1, 1):
        wall = [(-D / 2, ZP - 0.06), (D / 2 - 0.02, ZP - 0.06), (D / 2 - 0.02, zb + 0.05), (-D / 2, ZP + SPRING * t + 0.05)]
        tiled("Stone")
        B20.tprism(f"Cheek{sx}", WS.ccw(wall), sx * (W / 2 - 0.4), 0.8, K["tile"], plane="YZ")
        set_group("Main")
        chevron(f"Verge{sx}", [(ye - 0.03, ze + 0.12), (yb, zb + 0.22 / c + 0.02)], 0.16, 0.1, sx * (XE + 0.02), 0.09, K["lead"])
    # the flashing up the wall, and the valance
    box("Flashing", (2 * XE + 0.1, 0.05, 0.55), (0, D / 2 - 0.045, zb + 0.22 / c + 0.2), K["lead"], bevel=0.01)
    box("FlashingLip", (2 * XE + 0.1, 0.14, 0.05), (0, D / 2 - 0.09, zb + 0.22 / c + 0.47), K["lead"], bevel=0.01)
    n = 60
    xs = [-XE + 2 * XE * i / n for i in range(n + 1)]
    top = [(x, ze + 0.12) for x in xs]
    bot = [(x, ze - 0.5 + 0.18 * abs(math.sin(x / 0.6 * math.pi))) for x in xs]
    B20.tprism("Valance", WS.ccw(top + list(reversed(bot))), ye - 0.03, 0.05, K["enamel"])
    for k in range(-9, 10):
        x = k * 0.6
        sphere(f"ValanceStud{k}", 0.035, (x, ye - 0.065, ze - 0.05), K["gilt"], seg=8, rings=4, scale=(1, 0.5, 1))
    return _dims()


# ================================================================== flat roofs

def _deck(prefix, hw, hd, z, K):
    tiled("Lead")
    box(f"{prefix}", (2 * hw, 2 * hd, 0.2), (0, 0, z + 0.1), K["tile"], bevel=0.0, segments=1)
    set_group("Main")


def flat_roof_parapet(M):
    """A flat lead roof (16 x 12) behind a castle-stone parapet on a corbelled cornice: a moulded coping, quatrefoil
    panels, crocketed corner pinnacles, two grotesque spouts, a roof hatch and an iron ventilator."""
    K = kit(M)
    rnd = random.Random(2808)
    W, D = 16.0, 12.0
    cornice("Cornice", rect_path(W / 2, D / 2), K, closed=True, corbels=True)
    zp0, zp1 = ZP - 0.02, ZP + 1.7
    tiled("Stone")
    mould("Parapet", rect_path(W / 2, D / 2), [(-0.8, zp0), (0.0, zp0), (0.0, zp1), (-0.8, zp1)], K["tile"], closed=True)
    set_group("Main")
    mould("Coping", rect_path(W / 2, D / 2), [(-0.92, zp1 - 0.04), (-0.86, zp1 - 0.1), (0.1, zp1 - 0.1), (0.14, zp1 - 0.02), (0.1, zp1 + 0.12),
                                             (-0.4, zp1 + 0.28), (-0.92, zp1 + 0.16)], K["dk"], closed=True)
    _deck("Deck", W / 2 - 0.75, D / 2 - 0.75, 0.0, K)
    # quatrefoil panels on the outer faces
    path = rect_path(W / 2, D / 2)
    k = 0
    for i in range(4):
        a, b = path[i], path[(i + 1) % 4]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 1.8)
        for j in range(n):
            if j == 0 or j == n - 1:
                continue
            s = _mark()
            foil(f"Panel{k}", 0, -0.012, (zp0 + zp1) / 2 + 0.05, 0.34, K["dk"], lobes=4, thick=0.035)
            tube(f"PanelFrame{k}", [(-0.6, -0.012, zp0 + 0.32), (0.6, -0.012, zp0 + 0.32), (0.6, -0.012, zp1 - 0.25), (-0.6, -0.012, zp1 - 0.25)], 0.03,
                 K["dk"], closed=True, square=True, poly=True)
            t = (j + 0.5) / n
            run_along(s, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (b[0], b[1]))
            k += 1
    for i, (x, y) in enumerate(path):
        _spirelet(f"Pinnacle{i}", x - math.copysign(0.4, x), y - math.copysign(0.4, y), zp1 + 0.24, 2.2, 0.62, K["dk"], crockets=2)
    for x in (-4.0, 4.0):
        mx = Matrix.Translation((x, -D / 2 - 0.42, ZP + 0.12)) @ Matrix.Rotation(-0.25, 4, "X")
        box(f"Spout{x:+.0f}", (0.42, 1.1, 0.38), (x, -D / 2 - 0.05, ZP + 0.14), K["dk"], bevel=0.05)
        from nh_props_batch8 import _grotesque
        _grotesque(f"Grot{x:+.0f}", mx @ Matrix.Scale(1.4, 4), K["st"], K["hollow"])
    # the roof hatch and a ventilator
    box("Hatch", (1.7, 1.7, 0.5), (-4.5, 2.6, 0.45), K["iron"], bevel=0.05)
    box("HatchLid", (1.85, 1.85, 0.1), (-4.5, 2.6, 0.75), K["iron"], bevel=0.03)
    hoop("HatchRing", (-4.5, 1.72, 0.62), 0.12, "X", K["brass"], thick=0.02)
    for k in range(4):
        tube(f"HatchStrap{k}", [(-5.3 + k * 0.53, 1.75, 0.81), (-5.3 + k * 0.53, 3.45, 0.81)], 0.02, K["iron"], square=True, poly=True)
    cyl("VentPipe", 0.22, 1.6, (4.8, 3.0, 1.0), K["iron"], verts=16, bevel=0.01)
    cone("VentHat", 0.5, 0.05, 0.45, (4.8, 3.0, 2.15), K["iron"], verts=16)
    for k in range(3):
        a = k * 2 * math.pi / 3
        tube(f"VentStay{k}", [(4.8 + math.cos(a) * 0.2, 3.0 + math.sin(a) * 0.2, 1.7), (4.8 + math.cos(a) * 0.42, 3.0 + math.sin(a) * 0.42, 1.95)], 0.02,
             K["iron"], poly=True)
    _moss_on(K, rnd, [(-7.0, -5.0, 0.22), (6.5, 4.8, 0.22), (2.0, -5.1, 0.22), (-6.9, 3.0, 0.22)], size=0.18)
    return _dims()


def battlement_roof(M):
    """A castle tower's top (16 x 12): a machicolated parapet carried out on triple corbels, merlons with arrow
    slits and coped tops, a flat lead roof and a crimson banner on an iron pole with a gilt orb."""
    K = kit(M)
    rnd = random.Random(2809)
    W, D = 16.0, 12.0
    out, th = 0.75, 0.9                 # the parapet stands out this far from the wall face, this thick
    zb, zt = 1.25, 2.6                  # the breastwork's foot and top
    path = rect_path(W / 2, D / 2)
    # triple-stepped corbels round the wall top
    for i in range(4):
        a, b = path[i], path[(i + 1) % 4]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 1.6)
        for j in range(n + 1):
            s = _mark()
            for k, (dd, z0, z1) in enumerate(((0.3, 0.0, 0.42), (0.55, 0.42, 0.84), (out + 0.02, 0.84, zb + 0.02))):
                box(f"Corbel{i}_{j}_{k}", (0.48 - 0.05 * k, dd + 0.2, z1 - z0), (0, -(dd + 0.2) / 2 + 0.2, (z0 + z1) / 2), K["dk"], bevel=0.04, segments=1)
            run_along(s, (a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n), (b[0], b[1]))
    tiled("Stone")
    mould("Breast", path, [(out - th, zb), (out, zb), (out, zt), (out - th, zt)], K["tile"], closed=True)
    set_group("Main")
    # the dark machicolation slots between the corbels
    mould("Slots", path, [(0.06, zb - 0.03), (out - 0.08, zb - 0.03), (out - 0.08, zb - 0.01), (0.06, zb - 0.01)], K["hollow"], closed=True)
    mould("String", path, [(out - 0.02, zb - 0.06), (out + 0.1, zb - 0.06), (out + 0.12, zb + 0.12), (out - 0.02, zb + 0.18)], K["dk"], closed=True)
    # merlons: one on each corner and evenly between
    mpath = WS.offset(path, out - th / 2)
    mw, cw, mh = 1.35, 0.85, 1.45
    m = 0
    for i in range(4):
        a, b = Vector((*mpath[i], 0)), Vector((*mpath[(i + 1) % 4], 0))
        L = (b - a).length
        n = max(2, round((L - mw) / (mw + cw)))
        for j in range(n + 1):
            if j == n:
                continue                     # the next side's first merlon is this corner
            t = j / n
            p = a + (b - a) * t
            s = _mark()
            tiled("Stone")
            box(f"Merlon{m}", (mw, th - 0.06, mh), (0, 0, zt - 0.04 + mh / 2), K["tile"], bevel=0.0, segments=1)
            set_group("Main")
            box(f"MerlonCap{m}", (mw + 0.14, th + 0.12, 0.2), (0, 0, zt - 0.04 + mh + 0.08), K["dk"], bevel=0.04, segments=1)
            box(f"Loop{m}", (0.08, 0.02, 0.9), (0, -(th - 0.06) / 2 - 0.006, zt + 0.72), K["hollow"], bevel=0.0, segments=1)
            for zz in (0.27, 1.17):
                cyl(f"Oillet{m}{zz}", 0.085, 0.02, (0, -(th - 0.06) / 2 - 0.007, zt + zz), K["hollow"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.0)
            ang = math.atan2((b - a).y, (b - a).x)
            _xform(s, Matrix.Translation(p) @ Matrix.Rotation(ang, 4, "Z"))
            m += 1
    mould("CrenelSill", path, [(out - th - 0.04, zt - 0.02), (out + 0.05, zt - 0.02), (out + 0.05, zt + 0.08), (out - th / 2, zt + 0.16),
                               (out - th - 0.04, zt + 0.08)], K["dk"], closed=True)
    # the lead roof inside, on top of the wall
    _deck("Deck", W / 2 - 0.1, D / 2 - 0.1, zb - 0.32, K)
    # the banner
    px, py = W / 2 - 1.2, D / 2 - 1.2
    tube("Pole", [(px, py, zb - 0.1), (px, py, zt + 6.0)], 0.06, K["iron"], poly=True)
    sphere("PoleOrb", 0.14, (px, py, zt + 6.1), K["gilt"], seg=12, rings=6)
    rows = []
    for i in range(9):
        u = i / 8
        x = px - 0.08 - u * 2.6
        dy = 0.18 * math.sin(u * 5.0)
        rows.append((Vector((x, py + dy, zt + 5.8 - u * 0.15)), Vector((x, py + dy, zt + 4.2 + u * 0.25 - (0.5 * u * u if u > 0.7 else 0)))))
    from nh_props_batch4 import _mesh
    banner = flat("Banner", (0.117, 0.009, 0.011), 0.85, dirt=0.6)
    _mesh("Banner", [[a, b] for a, b in rows], banner, 0.03)
    _moss_on(K, rnd, [(-7.4, -5.4, zb - 0.1), (7.3, 5.3, zb - 0.1), (-2.0, 5.5, zt + 0.1)], size=0.16)
    return _dims()


# ================================================================== more caps

def witch_hat_cap(M):
    """A tall, flared candle-snuffer cap of crimson glazed fish scales for a slim round turret 6 across: a gilt band,
    one louvred lucarne, and a gilt candle-flame finial."""
    K = kit(M)
    r0 = 3.0
    cornice("Cornice", poly_path(r0, 32), K, closed=True, corbels=True, step=0.9)
    re = r0 + SPRING + 0.75
    za = ZP + 12.5
    prof = [(0.0, ZP + 0.02), (r0 - 0.2, ZP + 0.02), (re, ZP - 0.2), (re + 0.03, ZP - 0.05)]
    for k in range(1, 15):
        u = k / 14
        r = (r0 - 0.15) * (1 - u) ** 1.25 + 0.1 * u
        r += (re - r0 + 0.1) * (1 - u) ** 6
        prof.append((r, ZP - 0.05 + (za - ZP) * u))
    prof.append((0.0, za + 0.05))
    tiled("Crimson")
    tlathe("Cone", prof, "Crimson", seg=40, mat=K["tile"])
    set_group("Main")

    def r_at(z):
        for (ra, zz0), (rb, zz1) in zip(prof[3:], prof[4:]):
            if zz0 <= z <= zz1:
                return ra + (rb - ra) * (z - zz0) / (zz1 - zz0)
        return 0.1
    zg = ZP + 1.2
    hoop("Band", (0, 0, zg), r_at(zg) + 0.04, "Z", K["gilt"], thick=0.05)
    zsl = za - 1.0
    lead_cap("Apex", zsl, r_at(zsl) + 0.08, K, h=1.0)
    gl = K["gilt"]
    zf = zsl + 1.0
    tube("FinialRod", [(0, 0, zf - 0.1), (0, 0, zf + 1.1)], 0.04, K["iron"], poly=True)
    lathe("Candle", [(0, zf + 0.6), (0.14, zf + 0.6), (0.14, zf + 1.25), (0.0, zf + 1.25)], gl, seg=16)
    lathe("Dish", [(0, zf + 0.5), (0.3, zf + 0.5), (0.34, zf + 0.58), (0.2, zf + 0.62), (0, zf + 0.62)], gl, seg=16)
    lathe("Flame", [(0, zf + 1.28), (0.12, zf + 1.4), (0.15, zf + 1.6), (0.1, zf + 1.85), (0.03, zf + 2.1), (0, zf + 2.2)], gl, seg=16)
    s = _mark()
    zb = ZP + 3.2
    lucarne("Lucarne", K, w=1.1, h=1.0, hg=0.65, dpt=1.6)
    _place(s, (0, -(r_at(zb) + 0.05), zb), (0, -1))
    return _dims()


def broach_spire(M):
    """A lead broach spire on a square tower 8 across: an octagonal spire carried over the corners on broaches, lead
    rolls on the angles, louvred lucarnes in two tiers, a gilt orb and crescent on top."""
    K = kit(M)
    a0 = 3.85
    H = 15.0
    cornice("Cornice", rect_path(4.0, 4.0), K, closed=True, corbels=True)
    zb, za = ZP - 0.04, ZP + H
    base = poly_path(a0 / math.cos(math.pi / 8), 8)
    tiled("Lead")
    verts = [(x, y, zb) for x, y in base] + [(0.0, 0.0, za)]
    mk("Spire", verts, [list(range(8))[::-1]] + [[i, (i + 1) % 8, 8] for i in range(8)], K["tile"])

    def ap_at(z):
        return a0 * (za - z) / (za - zb)
    hb = 3.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            C = (sx * a0, sy * a0, zb)
            A = (sx * a0, sy * a0 * math.tan(math.pi / 8), zb)
            B = (sx * a0 * math.tan(math.pi / 8), sy * a0, zb)
            r = ap_at(zb + hb) * 0.96
            Pp = (sx * r / math.sqrt(2), sy * r / math.sqrt(2), zb + hb)
            mk(f"Broach{sx}{sy}", [C, A, B, Pp], [[0, 1, 2], [0, 1, 3], [1, 2, 3], [2, 0, 3]], K["tile"])
    set_group("Main")
    for i, (x, y) in enumerate(base):
        f = (za - (zb + hb + 0.4)) / (za - zb)
        lead_roll(f"Angle{i}", [(x * f * 1.02, y * f * 1.02, zb + hb + 0.4), (0.0, 0.0, za - 0.4)], K, r=0.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            r = ap_at(zb + hb) * 0.96
            lead_roll(f"BroachRoll{sx}{sy}", [(sx * a0 * 1.01, sy * a0 * 1.01, zb + 0.05), (sx * r / math.sqrt(2), sy * r / math.sqrt(2), zb + hb + 0.05)], K,
                      r=0.08)
    lead_cap("Apex", za - 1.3, 0.62, K, h=1.4)
    moon_finial("Finial", 0, 0, za + 0.05, K, h=3.0, s=1.15)
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        big = k % 2 == 0
        zl = ZP + (4.0 if big else 7.6)
        if not big and zl < zb + hb + 0.5:
            zl = zb + hb + 0.8
        rf = ap_at(zl) + 0.05
        s = _mark()
        if big:
            lucarne(f"Lucarne{k}", K, w=1.4, h=1.25, hg=0.85, dpt=2.0)
        else:
            lucarne(f"Lucarne{k}", K, w=0.9, h=0.8, hg=0.5, dpt=1.6)
        _place(s, (math.cos(a) * rf, math.sin(a) * rf, zl), (math.cos(a), math.sin(a)))
    return _dims()


def _octa(s):
    """Turn the parts built since s by an eighth of a half turn, so a lathe's 8 corners sit on an octagon with a flat to
    the front."""
    _xform(s, Matrix.Rotation(math.pi / 8, 4, "Z"))


def bell_cast_cap(M):
    """An octagonal ogee cap in verdigris copper for a tower 8 across: bell-cast at the eaves and swelling above,
    copper rolls on the angles, a copper finial with a gilt orb and spike."""
    K = kit(M)
    ap = 4.0
    rc = ap / math.cos(math.pi / 8)
    cornice("Cornice", poly_path(rc, 8), K, closed=True, corbels=True, step=1.1)
    k8 = 1 / math.cos(math.pi / 8)
    prof_ap = [(0.0, ZP + 0.02), (3.6, ZP + 0.02), (4.5, ZP - 0.12), (4.52, ZP + 0.03), (4.15, ZP + 0.4), (3.85, ZP + 0.95), (3.75, ZP + 1.6),
               (3.65, ZP + 2.3), (3.35, ZP + 3.0), (2.75, ZP + 3.7), (1.95, ZP + 4.3), (1.2, ZP + 4.8), (0.7, ZP + 5.3), (0.42, ZP + 5.9),
               (0.25, ZP + 6.5), (0.0, ZP + 6.7)]
    prof = [(r * k8, z) for r, z in prof_ap]
    s = _mark()
    tiled("Copper")
    tlathe("Cap", prof, "Copper", seg=8, mat=K["tile"])
    set_group("Main")
    for i in range(8):
        a = i / 8 * 2 * math.pi
        pts = [(math.cos(a) * (r * 1.015 + 0.02), math.sin(a) * (r * 1.015 + 0.02), z + 0.02) for r, z in prof[4:-2]]
        tube(f"Rib{i}", pts, 0.07, K["verdigris"], poly=True)
    _octa(s)
    zf = ZP + 6.45
    lathe("Finial", [(0, zf), (0.42, zf), (0.38, zf + 0.15), (0.16, zf + 0.35), (0.3, zf + 0.7), (0.32, zf + 0.85), (0.12, zf + 1.1), (0.08, zf + 1.6),
                     (0, zf + 1.6)], K["verdigris"], seg=16)
    sphere("FinialOrb", 0.2, (0, 0, zf + 1.75), K["gilt"], seg=14, rings=7)
    _spike("FinialTip", (0, 0, zf + 2.3), 0.05, 0.8, K["gilt"], verts=6)
    return _dims()


def onion_dome(M):
    """A verdigris copper onion dome for a round tower 7 across: gilt ribs, a moulded collar, and a little gilt onion
    and crescent moon on top."""
    K = kit(M)
    r0 = 3.5
    cornice("Cornice", poly_path(r0, 36), K, closed=True, corbels=True, step=0.9)
    z = ZP
    prof = [(0.0, z + 0.02), (3.35, z + 0.02), (3.4, z + 0.3), (3.7, z + 0.75), (4.05, z + 1.4), (4.22, z + 2.15), (4.18, z + 2.85), (3.9, z + 3.6),
            (3.35, z + 4.35), (2.6, z + 5.05), (1.75, z + 5.7), (1.0, z + 6.3), (0.5, z + 6.85), (0.24, z + 7.4), (0.14, z + 7.8), (0.0, z + 7.9)]
    tiled("Copper")
    tlathe("Dome", prof, "Copper", seg=40, mat=K["tile"])
    set_group("Main")
    for i in range(8):
        a = i / 8 * 2 * math.pi + math.pi / 8
        pts = [(math.cos(a) * (r + 0.03), math.sin(a) * (r + 0.03), zz) for r, zz in prof[2:-2]]
        tube(f"Rib{i}", pts, 0.055, K["gilt"], poly=True)
    hoop("Collar", (0, 0, z + 0.3), 3.44, "Z", K["verdigris"], thick=0.09)
    zf = z + 7.65
    lathe("Finial", [(0, zf), (0.24, zf), (0.2, zf + 0.2), (0.38, zf + 0.5), (0.4, zf + 0.7), (0.24, zf + 0.95), (0.1, zf + 1.15), (0.06, zf + 1.5),
                     (0, zf + 1.5)], K["gilt"], seg=16)
    tube("FinialRod", [(0, 0, zf + 1.4), (0, 0, zf + 2.4)], 0.03, K["iron"], poly=True)
    B20.tprism("FinialMoon", WS.crescent(0, zf + 2.6, 0.3, shift=0.42, tilt=math.pi / 2), 0, 0.05, K["gilt"])
    return _dims()



# ================================================================== dormers

def gabled_dormer(M):
    """A stone dormer for a 45 degree roof (its foot line on the slates, the roof plane z = y rising behind it): a tall
    traceried lancet with leaded glass and the warm room behind, slate-hung cheeks, a slate roof run out over a cusped
    crimson-enamel bargeboard with a pendant, a lead ridge and a spiked finial, a lead apron in front."""
    K = kit(M)
    from nh_props_batch23 import leads, glass, room
    W2, zE, za = 1.7, 3.0, 4.5
    outer = [(-W2, 0.0), (W2, 0.0), (W2, zE), (0.0, za), (-W2, zE)]
    lt = WS.arch(0.72, 0.55, 2.55, 3.65, 12)
    holed("Face", outer, lt, 0.0, 2.0, -0.12, 0.14, K["st"], n=56)
    tube("Roll", [(x, -0.15, z) for x, z in WS.offset(WS.ccw(lt), 0.05)], 0.045, K["dk"], closed=True, square=True, poly=True)
    box("Sill", (1.9, 0.55, 0.2), (0, -0.2, 0.47), K["dk"], bevel=0.03)
    tube("Mullion", [(0, -0.02, 0.55), (0, -0.02, 2.75)], 0.035, K["dk"], square=True, poly=True)
    tube("TraceryL", [(0, -0.02, 2.75), (-0.36, -0.02, 3.1), (-0.6, -0.02, 3.25)], 0.03, K["dk"], square=True, poly=True)
    tube("TraceryR", [(0, -0.02, 2.75), (0.36, -0.02, 3.1), (0.6, -0.02, 3.25)], 0.03, K["dk"], square=True, poly=True)
    foil("HeadFoil", 0, -0.03, 3.22, 0.16, K["dk"], lobes=3, thick=0.02)
    glass("Pane", lt, 0.02, K)
    leads("Came", lt, 0.0, 0.3, K["lead"])
    room("Room", [lt], K, y=0.26)
    # cheeks: slate-hung triangles down to the main roof
    for sx in (-1, 1):
        tiled("Slate")
        B20.tprism(f"Cheek{sx}", WS.ccw([(0.14, 0.09), (0.14, zE - 0.02), (zE + 0.05, zE - 0.02)]), sx * (W2 - 0.07), 0.1, K["tile"], plane="YZ")
        set_group("Main")
    # the roof: two slate planes, overhanging the face and running back into the main roof
    xe = W2 + 0.35
    ze = zE - 0.35 * (za - zE) / W2
    zr = za + 0.06
    for sx in (-1, 1):
        a, b = Vector((sx * xe, 0, ze)), Vector((0, 0, zr))
        d = (b - a).normalized()
        n = Vector((-d.z, 0, d.x)) if sx > 0 else Vector((d.z, 0, -d.x))
        if n.z < 0:
            n = -n
        y0, ye_b, yr_b = -0.4, ze + 0.25, zr + 0.3
        bot = [Vector((a.x, y0, a.z)), Vector((b.x, y0, b.z)), Vector((b.x, yr_b, b.z)), Vector((a.x, ye_b, a.z))]
        def lay(v, h):
            if abs(v.x) < 1e-6:
                return Vector((0, v.y, v.z + h / n.z))
            return v + n * h
        tiled("Slate")
        solid(f"DRoof{sx}", [lay(v, 0.0) for v in bot], [lay(v, 0.16) for v in bot], K["tile"])
        set_group("Main")
    pts_t, pts_b = [], []
    for i in range(41):
        x = -xe + 2 * xe * i / 40
        zu = zr - (zr - ze) * abs(x) / xe
        pts_t.append((x, zu + 0.05))
        pts_b.append((x, zu - 0.28 - 0.12 * abs(math.sin(abs(x) / 0.45 * math.pi))))
    B20.tprism("Barge", WS.ccw(pts_t + list(reversed(pts_b))), -0.33, 0.06, K["enamel"])
    lathe("Pendant", [(0, -0.75), (0.05, -0.7), (0.11, -0.5), (0.09, -0.33), (0.06, -0.2), (0.08, -0.08), (0.08, 0.0), (0, 0.0)], K["iron"], seg=12,
          loc=(0, -0.33, zr - 0.05))
    lead_roll("Ridge", [(0, -0.45, zr + 0.18), (0, yr_b - 0.1, zr + 0.18)], K, r=0.09)
    _spike("Spike", (0, -0.3, zr + 0.75), 0.05, 0.9, K["iron"], verts=4)
    sphere("SpikeOrb", 0.1, (0, -0.3, zr + 0.35), K["gilt"], seg=10, rings=5)
    slab2("Apron", (-0.7, -0.68), (0.12, 0.14), -W2 - 0.2, W2 + 0.2, 0.0, 0.05, K["lead"])
    return _dims()


def oxeye_dormer(M):
    """A round oeil-de-boeuf dormer for steep roofs and mansards (60 degrees and up): a moulded stone face with four
    keystones, an iron quatrefoil in the glass and the warm room behind, a rolled lead bonnet and cheeks, a lead apron."""
    K = kit(M)
    oxeye("Oxeye", K, dpt=1.45)
    t = math.tan(math.radians(60))
    slab2("Apron", (-0.4, -0.4 * t + 0.02), (0.1, 0.1 * t + 0.02), -1.15, 1.15, 0.0, 0.05, K["lead"])
    return _dims()


# ================================================================== ridges, hips and the corner

def ridge_cresting(M):
    """An 8-stud run of crimson glazed ridge tiles with iron cresting, to cap any ridge (repeat it end to end)."""
    K = kit(M)
    ridge_tiles("Ridge", -4.0, 4.0, 0.26, K, knobs=False)
    cresting("Crest", -3.55, 3.55, 0.52, K)
    return _dims()


def ridge_tiles_piece(M):
    """An 8-stud run of plain crimson glazed ridge tiles with rolled collars, gilt-knobbed end caps."""
    K = kit(M)
    ridge_tiles("Ridge", -4.0, 4.0, 0.26, K, knobs=True)
    return _dims()


def hip_cap(M):
    """A lead hip roll for a 45 degree hipped roof (the hip falls at 35 degrees), with a scrolled iron hip hook at
    its foot."""
    K = kit(M)
    a = math.atan(1 / math.sqrt(2))
    L = 8.0
    p0 = Vector((0, -L / 2 * math.cos(a), 0.14))
    p1 = Vector((0, L / 2 * math.cos(a), 0.14 + L * math.sin(a)))
    lead_roll("Roll", [tuple(p0), tuple(p1)], K, r=0.14)
    box("Saddle", (0.5, L, 0.06), (0, 0, 0), K["lead"], bevel=0.01, rot=(a, 0, 0))
    _xform(len(P.PARTS) - 1, Matrix.Translation((p0 + p1) / 2 - Vector((0, 0, 0.12))))
    tube("Hook", [(0, p0.y + 0.05, 0.3), (0, p0.y - 0.25, 0.32), (0, p0.y - 0.42, 0.1), (0, p0.y - 0.3, -0.06 + 0.1), (0, p0.y - 0.16, 0.08)], 0.035,
         K["iron"])
    return _dims()


def roof_corner_l(M):
    """The corner where two 45 degree wings meet in an L (both 12 deep; walls on its front and right): a hip on the
    outside, a lead valley on the inside, crimson ridge tiles and cresting along both ridges meeting at a gilt-mooned
    knob. Its open ends (left and back) take a GableSection."""
    K = kit(M)
    H = 6.0
    ye = H + SPRING + 0.45
    ze = ZP - 0.45
    Hb = ZP + H + SPRING
    zv = ZP + SPRING                        # the valley's foot at the inner corner (-6, 6)
    c = math.cos(math.radians(45))
    lo, hi = (TS - 0.02) / c, (2 * TS - 0.02) / c

    def planes(e, z_e, o):
        return [[(-H + o, -e, z_e), (e, -e, z_e), (0, 0, Hb), (-H + o, 0, Hb)],
                [(e, -e, z_e), (e, H - o, z_e), (0, H - o, Hb), (0, 0, Hb)],
                [(-H + o, 0, Hb), (0, 0, Hb), (-H + o, H - o, zv)],
                [(0, 0, Hb), (0, H - o, Hb), (-H + o, H - o, zv)]]
    for k, pl in enumerate(planes(ye, ze, 0.0)):
        tiled("Slate")
        solid(f"Slate{k}", [(x, y, z + lo) for x, y, z in pl], [(x, y, z + hi) for x, y, z in pl], K["tile"])
    for k, pl in enumerate(planes(ye - 0.06, ze + 0.06, 0.05)):
        tiled("Lead")
        solid(f"Under{k}", list(pl), [(x, y, z + TS / c) for x, y, z in pl], K["tile"])
    set_group("Main")
    top = Hb + hi
    cornice("Cornice", [(-H, -H), (H, -H), (H, H)], K, closed=False, corbels=True)
    g = H + CP + 0.02
    gutter("Gutter", [(-H, -g), (g, -g), (g, H)], ze - 0.03, K)
    lead_roll("Hip", [(ye - 0.05, -ye + 0.05, ze + hi + 0.02), (0, 0, top - 0.05)], K, r=0.11)
    tube("HipIron", [(ye, -ye, ze + hi + 0.05), (ye + 0.18, -ye - 0.18, ze + hi - 0.05), (ye + 0.22, -ye - 0.22, ze + hi - 0.28),
                     (ye + 0.08, -ye - 0.08, ze + hi - 0.3)], 0.025, K["iron"])
    bar("Valley", (-H, H, zv + hi + 0.02), (0, 0, Hb + hi + 0.02), 0.5, 0.05, K["lead"])
    ridge_tiles("RidgeA", -H, 0.3, top - 0.08, K, knobs=False)
    s = _mark()
    ridge_tiles("RidgeB", -0.3, H, top - 0.08, K, knobs=False)
    _xform(s, Matrix.Rotation(math.pi / 2, 4, "Z"))
    cresting("CrestA", -H + 0.45, -0.45, top + 0.17, K)
    s = _mark()
    cresting("CrestB", 0.45, H - 0.45, top + 0.17, K)
    _xform(s, Matrix.Rotation(math.pi / 2, 4, "Z"))
    moon_finial("Knob", 0, 0, top + 0.12, K, h=1.8, s=0.8)
    return _dims()


# ================================================================== gutters, chimneys

def eaves_gutter(M):
    """A wall's rainwater goods (its back flat at y = 0): an 8-stud cast-iron ogee gutter on hangers, a crimson enamel
    hopper with the gilt crest's foil, a downpipe down the wall on eared straps, and a shoe at the foot."""
    K = kit(M)
    zg = 10.6
    gutter("Gutter", [(-4.0, -0.06), (4.0, -0.06)], zg, K, brackets=False)
    for k in range(4):
        x = -3.4 + k * 2.27
        tube(f"Hanger{k}", [(x, -0.01, zg - 0.05), (x, -0.08, zg - 0.36), (x, -0.32, zg - 0.38), (x, -0.56, zg - 0.08)], 0.02, K["iron"], square=True, poly=True)
        box(f"HangerPlate{k}", (0.12, 0.03, 0.5), (x, -0.015, zg - 0.2), K["iron"], bevel=0.005)
    hx = 2.4
    tube("Outlet", [(hx, -0.3, zg - 0.29), (hx, -0.3, zg - 0.55)], 0.1, K["iron"], poly=True)
    lo = [(hx - 0.22, -0.48), (hx + 0.22, -0.48), (hx + 0.22, -0.08), (hx - 0.22, -0.08)]
    hi_ = [(hx - 0.42, -0.62), (hx + 0.42, -0.62), (hx + 0.42, -0.04), (hx - 0.42, -0.04)]
    solid("Hopper", [(x, y, zg - 1.35) for x, y in lo], [(x, y, zg - 0.55) for x, y in hi_], K["enamel"])
    mould("HopperRim", [(x, y) for x, y in hi_][::-1][::-1], [(-0.05, zg - 0.6), (0.04, zg - 0.6), (0.04, zg - 0.52), (-0.05, zg - 0.52)], K["iron"], closed=True)
    foil("HopperFoil", hx, -0.56, zg - 0.9, 0.17, K["gilt"], lobes=4, thick=0.02)
    zp = zg - 1.35
    tube("Pipe", [(hx, -0.28, zp + 0.05), (hx, -0.28, 0.55)], 0.15, K["iron"], poly=True)
    tube("Shoe", [(hx, -0.28, 0.6), (hx, -0.3, 0.32), (hx, -0.52, 0.12)], 0.15, K["iron"])
    for k in range(5):
        z = 1.4 + k * 1.95
        cyl(f"Collar{k}", 0.19, 0.16, (hx, -0.28, z), K["iron"], verts=16, bevel=0.01)
        for sx in (-1, 1):
            box(f"Ear{k}{sx}", (0.18, 0.04, 0.14), (hx + sx * 0.25, -0.02, z), K["iron"], bevel=0.008)
            sphere(f"EarNail{k}{sx}", 0.025, (hx + sx * 0.27, -0.045, z), K["brass"], seg=6, rings=3)
    return _dims()


def chimney_stack(M):
    """A castle-stone chimney stack: a lead skirt where it leaves the roof, a soot-stone band, oversailing courses at
    the top, three soot-blackened clay pots on their flaunching, one under a lobster-back iron cowl."""
    K = kit(M)
    rnd = random.Random(2810)
    clay = material("PotClay", "NH_Limestone", tint=(0.11, 0.045, 0.035), scale=0.5, rough_add=0.1, wear=0.3, dirt=1.0)
    w, d, h = 3.2, 1.6, 6.0
    tiled("Stone")
    box("Stack", (w, d, h), (0, 0, h / 2), K["tile"], bevel=0.02, segments=1)
    set_group("Main")
    box("Skirt", (w + 0.3, d + 0.3, 0.35), (0, 0, 0.175), K["lead"], bevel=0.04)
    box("Band", (w + 0.18, d + 0.18, 0.24), (0, 0, 3.2), K["dk"], bevel=0.04)
    for k, (dw, z0, hh) in enumerate(((0.16, h - 0.02, 0.24), (0.36, h + 0.22, 0.3), (0.12, h + 0.52, 0.16))):
        box(f"Course{k}", (w + dw, d + dw, hh), (0, 0, z0 + hh / 2), K["dk"], bevel=0.035)
    zt = h + 0.68
    lathe("Flaunching", [(0, zt - 0.02), (1.3, zt - 0.02), (0.9, zt + 0.18), (0, zt + 0.22)], K["st"], seg=20, scale=(1.15, 0.55))
    for k, (x, ph) in enumerate(((-1.0, 1.1), (0.0, 1.45), (1.0, 1.0))):
        z0 = zt + 0.05
        prof = [(0, z0), (0.36, z0), (0.4, z0 + 0.12), (0.3, z0 + ph * 0.6), (0.27, z0 + ph * 0.92), (0.34, z0 + ph), (0.32, z0 + ph + 0.08), (0.2, z0 + ph + 0.08),
                (0.2, z0 + ph - 0.3), (0, z0 + ph - 0.3)]
        lathe(f"Pot{k}", prof, clay, seg=18, loc=(x, 0, 0))
        lathe(f"Soot{k}", [(0, z0 + ph - 0.29), (0.205, z0 + ph - 0.29), (0.205, z0 + ph - 0.26), (0, z0 + ph - 0.26)], K["hollow"], seg=18, loc=(x, 0, 0))
        hoop(f"PotBand{k}", (x, 0, z0 + ph * 0.75), 0.29, "Z", K["iron"], thick=0.02)
    # the lobster-back cowl on the middle pot
    z0 = zt + 0.05 + 1.45
    tube("CowlStem", [(0, 0, z0 - 0.1), (0, 0, z0 + 0.35)], 0.17, K["iron"], poly=True)
    for k in range(4):
        a = k * 0.32
        tube(f"Cowl{k}", [(0, -0.22 * math.cos(a) + 0.02 * k, z0 + 0.35 + 0.22 * math.sin(a)), (0, 0.0, z0 + 0.62 + 0.04 * k),
                          (0, 0.24 * math.cos(a), z0 + 0.35 + 0.22 * math.sin(a))], 0.19 - 0.02 * k, K["iron"])
    box("CowlVane", (0.03, 0.5, 0.3), (0, 0.45, z0 + 0.55), K["iron"], bevel=0.005)
    _moss_on(K, rnd, [(-1.4, -0.95, 0.37), (1.5, 0.95, 0.37), (-0.6, 0.0, zt + 0.2)], size=0.12)
    return _dims()


def twin_flue(M):
    """A pair of gothic twisted chimney shafts on a moulded soot-stone base, with octagonal bases and crowned caps."""
    K = kit(M)
    st, dk = K["st"], K["dk"]
    box("Base", (3.2, 1.6, 1.2), (0, 0, 0.6), dk, bevel=0.04)
    box("BaseCap", (3.4, 1.8, 0.22), (0, 0, 1.31), st, bevel=0.05)
    for k, x in enumerate((-0.8, 0.8)):
        s = _mark()
        lathe(f"Foot{k}", [(0, 1.42), (0.78, 1.42), (0.78, 1.6), (0.68, 1.72), (0.6, 1.9), (0, 1.9)], dk, seg=8)
        twist(f"Shaft{k}", 1.85, 5.7, 0.6, st, lobes=8, depth=0.16, turns=1.5 if k else -1.5, seg=32, rings=48)
        lathe(f"Neck{k}", [(0, 5.6), (0.58, 5.6), (0.66, 5.75), (0.8, 5.95), (0.84, 6.1), (0.5, 6.1), (0.5, 5.95), (0, 5.95)], dk, seg=16)
        for j in range(8):
            a = j / 8 * 2 * math.pi
            box(f"Crown{k}{j}", (0.2, 0.2, 0.32), (math.cos(a) * 0.72, math.sin(a) * 0.72, 6.25), dk, bevel=0.03, rot=(0, 0, a))
        lathe(f"FlueSoot{k}", [(0, 5.97), (0.49, 5.97), (0.49, 6.0), (0, 6.0)], K["hollow"], seg=16)
        _xform(s, Matrix.Translation((x, 0, 0)))
    foil("BaseFoil", 0, -0.81, 0.62, 0.3, st, lobes=4, thick=0.03)
    return _dims()


# ================================================================== weathervane, bell-cote, cupola, lantern, skylight

def _letter(prefix, ch, K, s=0.45):
    h = s / 2
    w = s * 0.34
    ir = K["iron"]
    paths = {"N": [[(-w, -h), (-w, h), (w, -h), (w, h)]], "E": [[(w, h), (-w, h), (-w, -h), (w, -h)], [(-w, 0), (w * 0.6, 0)]],
             "W": [[(-w * 1.3, h), (-w * 0.6, -h), (0, h * 0.4), (w * 0.6, -h), (w * 1.3, h)]]}
    if ch == "S":
        tube(f"{prefix}", [(w, 0, h * 0.8), (0, 0, h), (-w, 0, h * 0.55), (0, 0, 0), (w, 0, -h * 0.55), (0, 0, -h), (-w, 0, -h * 0.8)], 0.025, ir)
        return
    for k, pth in enumerate(paths[ch]):
        tube(f"{prefix}{k}", [(x, 0, z) for x, z in pth], 0.025, ir, square=True, poly=True)


def weathervane(M):
    """An iron weathervane for a spire or a ridge: scrolled brackets, gilt orbs, the four quarters lettered N, E, S and
    W, and an arrow with a gilt crescent-moon tail and an iron raven perched on it."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    lathe("Base", [(0, 0), (0.5, 0), (0.48, 0.12), (0.3, 0.3), (0.16, 0.55), (0.1, 0.75), (0, 0.75)], K["lead"], seg=4)
    tube("Mast", [(0, 0, 0.6), (0, 0, 6.6)], 0.06, ir, poly=True)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cx, cy = math.cos(a), math.sin(a)
        tube(f"Scroll{k}", [(cx * 0.06, cy * 0.06, 1.3), (cx * 0.45, cy * 0.45, 1.6), (cx * 0.55, cy * 0.55, 2.05), (cx * 0.35, cy * 0.35, 2.2),
                            (cx * 0.25, cy * 0.25, 2.0)], 0.025, ir)
    sphere("Orb", 0.22, (0, 0, 2.6), gl, seg=16, rings=8)
    zc = 3.5
    for k, (dx, dy, ch) in enumerate(((0, 1, "N"), (1, 0, "E"), (0, -1, "S"), (-1, 0, "W"))):
        tube(f"Arm{ch}", [(0, 0, zc), (dx * 1.25, dy * 1.25, zc)], 0.03, ir, square=True, poly=True)
        _spike(f"ArmTip{ch}", (dx * 1.3, dy * 1.3, zc), 0.05, 0.14, ir, verts=4, rot=(dy * math.pi / 2 * -1 if dy else 0, dx * math.pi / 2 if dx else 0, 0))
        s = _mark()
        _letter(f"Letter{ch}", ch, K)
        # E and W read from the front, N and S from the right-hand side
        _xform(s, Matrix.Translation((dx * 1.05, dy * 1.05, zc + 0.38)) @ Matrix.Rotation(0.0 if dx else math.pi / 2, 4, "Z"))
    sphere("Orb2", 0.13, (0, 0, 4.3), gl, seg=14, rings=7)
    zv = 5.0
    cyl("Pivot", 0.1, 0.3, (0, 0, zv - 0.15), ir, verts=12)
    tube("Shaft", [(-1.7, 0, zv), (1.7, 0, zv)], 0.035, ir, poly=True)
    B20.tprism("Head", WS.ccw([(1.6, zv - 0.25), (2.15, zv), (1.6, zv + 0.25), (1.72, zv)]), 0, 0.05, gl)
    B20.tprism("Tail", WS.crescent(-1.75, zv, 0.42, shift=0.45, tilt=0.0), 0, 0.05, gl)
    raven("Raven", (0.2, 0, zv + 0.03), 0.0, 3.0, ir, gl)
    _spike("Tip", (0, 0, 6.75), 0.04, 0.35, gl, verts=6)
    return _dims()


def bell_cote(M):
    """A double bell-cote to stand on a gable: a castle-stone wall pierced by two pointed arches on a moulded base,
    two bronze bells on iron headstocks, a coped gable with quatrefoils, kneelers and a crocketed pinnacle."""
    K = kit(M)
    dk, st = K["dk"], K["st"]
    hw = 2.2
    box("Base", (2 * hw + 0.3, 1.3, 0.55), (0, 0, 0.275), dk, bevel=0.05)
    box("BaseMould", (2 * hw + 0.1, 1.15, 0.25), (0, 0, 0.67), st, bevel=0.06)
    zs, za, z0, zt, zg = 2.5, 3.35, 0.8, 3.85, 5.3
    outline = [(-hw, z0), (-1.7, z0)]
    for cx in (-0.975, 0.975):
        arch = WS.pointed(0.725, zs, za, 10)
        if cx > 0:
            outline += [(0.25, z0)]
        outline += [(cx + x, z) for x, z in arch]
        if cx < 0:
            outline += [(-0.25, z0)]
    outline += [(1.7, z0), (hw, z0), (hw, zt), (0.0, zg), (-hw, zt)]
    tiled("Stone")
    B20.tprism("Wall", WS.ccw(outline), 0, 1.0, K["tile"])
    set_group("Main")
    for cx in (-0.975, 0.975):
        pts = [(cx + x, z) for x, z in WS.pointed(0.725, zs, za, 10)]
        for sy in (-1, 1):
            tube(f"ArchRoll{cx:+.0f}{sy}", [(x, sy * 0.52, z) for x, z in [(cx - 0.725, z0)] + pts + [(cx + 0.725, z0)]], 0.05, dk, square=True, poly=True)
        tube(f"Headstock{cx:+.0f}", [(cx - 0.72, 0, zs + 0.05), (cx + 0.72, 0, zs + 0.05)], 0.07, K["iron"], square=True, poly=True)
        bell = [(0, zs - 0.08), (0.14, zs - 0.08), (0.2, zs - 0.2), (0.24, zs - 0.45), (0.3, zs - 0.7), (0.42, zs - 0.88), (0.45, zs - 0.96), (0.38, zs - 0.95),
                (0.27, zs - 0.8), (0.2, zs - 0.5), (0, zs - 0.5)]
        lathe(f"Bell{cx:+.0f}", bell, K["bronze"], seg=24, loc=(cx, 0, 0))
        sphere(f"Clapper{cx:+.0f}", 0.08, (cx, 0, zs - 0.92), K["iron"], seg=8, rings=4)
        tube(f"ClapperRod{cx:+.0f}", [(cx, 0, zs - 0.55), (cx, 0, zs - 0.86)], 0.02, K["iron"], poly=True)
        box(f"Yoke{cx:+.0f}", (0.36, 0.14, 0.14), (cx, 0, zs - 0.03), K["iron"], bevel=0.01)
    box("String", (2 * hw + 0.2, 1.16, 0.22), (0, 0, zt), dk, bevel=0.04)
    chevron("Coping", [(-hw - 0.15, zt + 0.02), (0.0, zg + 0.1), (hw + 0.15, zt + 0.02)], 0.2, 0.12, 0, 1.2, dk, plane="XZ")
    for sx in (-1, 1):
        box(f"Kneeler{sx}", (0.5, 1.25, 0.5), (sx * (hw - 0.05), 0, zt + 0.25), dk, bevel=0.04)
        foil(f"GableFoil{sx}", sx * 0.75, -0.51, zt + 0.48, 0.2, st, lobes=4, thick=0.025)
    foil("GableFoil", 0, -0.51, zt + 0.82, 0.26, st, lobes=4, thick=0.028)
    _spirelet("Pinnacle", 0, 0, zg + 0.18, 2.1, 0.58, dk, crockets=2)
    sphere("PinnacleOrb", 0.1, (0, 0, zg + 2.38), K["gilt"], seg=10, rings=5)
    return _dims()


def cupola(M):
    """A louvred ridge cupola: a lead saddle that sits astride a 45 degree ridge, an octagonal stage of crimson
    enamel posts and pointed heads with lead louvres, a cornice, a bell-cast verdigris cap and a gilt-mooned finial."""
    K = kit(M)
    en, ld = K["enamel"], K["lead"]
    B20.tprism("Saddle", WS.ccw([(-1.75, 0.0), (0.0, 1.75), (1.75, 0.0), (1.75, 2.4), (-1.75, 2.4)]), 0, 3.5, ld, plane="YZ")
    rc = 1.5
    mould("Plinth", poly_path(rc + 0.1, 8), [(-0.6, 2.38), (0.12, 2.38), (0.16, 2.5), (0.08, 2.62), (-0.6, 2.62)], K["dk"], closed=True)
    lathe("Core", [(0, 2.6), (1.18, 2.6), (1.18, 5.0), (0, 5.0)], K["hollow"], seg=8)
    ap = rc * math.cos(math.pi / 8)
    side = 2 * rc * math.sin(math.pi / 8)
    for i, (x, y) in enumerate(poly_path(rc, 8)):
        tube(f"Post{i}", [(x, y, 2.6), (x, y, 5.0)], 0.075, en, square=True, poly=True)
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        s = _mark()
        hw = side / 2 - 0.06
        head = [(-hw, 5.0), (-hw, 4.25)] + [(x, z) for x, z in WS.pointed(hw * 0.86, 4.25, 4.82, 8)] + [(hw, 4.25), (hw, 5.0)]
        B20.tprism(f"Head{k}", WS.ccw(head), 0.0, 0.06, en)
        for j in range(5):
            box(f"Louvre{k}{j}", (2 * hw, 0.05, 0.3), (0, 0.06, 2.95 + j * 0.25), ld, bevel=0.0, segments=1, rot=(0.6, 0, 0))
        box(f"Sill{k}", (2 * hw + 0.04, 0.16, 0.08), (0, 0.0, 2.68), en, bevel=0.01)
        _place(s, (math.cos(a) * ap, math.sin(a) * ap, 0), (math.cos(a), math.sin(a)))
    mould("Cornice", poly_path(rc, 8), [(-0.5, 4.98), (0.06, 4.98), (0.12, 5.1), (0.22, 5.22), (0.22, 5.32), (-0.5, 5.32)], K["dk"], closed=True)
    k8 = 1 / math.cos(math.pi / 8)
    prof = [(r * k8, z) for r, z in [(0, 5.32), (1.55, 5.32), (1.9, 5.25), (1.92, 5.34), (1.7, 5.55), (1.5, 5.85), (1.35, 6.3), (1.05, 6.8), (0.65, 7.2),
                                      (0.3, 7.45), (0, 7.55)]]
    s = _mark()
    tiled("Copper")
    tlathe("Cap", prof, "Copper", seg=8, mat=K["tile"])
    set_group("Main")
    for i in range(8):
        a = i / 8 * 2 * math.pi
        tube(f"Rib{i}", [(math.cos(a) * (r * 1.015 + 0.015), math.sin(a) * (r * 1.015 + 0.015), z + 0.015) for r, z in prof[3:-1]], 0.045, K["verdigris"])
    _octa(s)
    moon_finial("Finial", 0, 0, 7.4, K, h=1.9, s=0.85)
    return _dims()


def lantern_roof(M):
    """An octagonal glazed roof lantern over a stair or a hall: a stone kerb, iron-framed twin lancet lights in clear
    glass, a crimson frieze with gilt bosses, a lead ogee dome with rolled ribs and a gilt finial; inside hangs an iron
    corona of lit candles."""
    K = kit(M)
    from nh_props_batch9 import candle, wax_mat
    ir = K["iron"]
    ap = 2.8
    rc = ap / math.cos(math.pi / 8)
    tiled("Stone")
    mould("Kerb", poly_path(rc, 8), [(-0.9, 0.0), (0.25, 0.0), (0.25, 0.75), (0.0, 0.92), (-0.9, 0.92)], K["tile"], closed=True)
    set_group("Main")
    mould("KerbCap", poly_path(rc, 8), [(-0.05, 0.88), (0.32, 0.72), (0.36, 0.8), (0.1, 1.0), (-0.05, 1.0)], K["dk"], closed=True)
    z0, z1 = 1.0, 3.8
    side = 2 * rc * math.sin(math.pi / 8)
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4
        s = _mark()
        hw = side / 2
        tube(f"Frame{k}", [(-hw + 0.05, 0, z0 + 0.05), (hw - 0.05, 0, z0 + 0.05), (hw - 0.05, 0, z1 - 0.05), (-hw + 0.05, 0, z1 - 0.05)], 0.05, ir,
             closed=True, square=True, poly=True)
        lw = (hw - 0.2) / 2
        for cx in (-lw - 0.05, lw + 0.05):
            tube(f"Light{k}{cx:+.1f}", [(cx - lw + 0.04, -0.02, z0 + 0.1)] + [(cx + x, -0.02, z) for x, z in WS.pointed(lw - 0.04, z1 - 0.9, z1 - 0.2, 8)] +
                 [(cx + lw - 0.04, -0.02, z0 + 0.1)], 0.03, ir, square=True, poly=True)
            tube(f"Transom{k}{cx:+.1f}", [(cx - lw + 0.04, -0.02, z0 + 1.1), (cx + lw - 0.04, -0.02, z0 + 1.1)], 0.02, ir, square=True, poly=True)
        tube(f"Mullion{k}", [(0, -0.02, z0 + 0.1), (0, -0.02, z1 - 0.1)], 0.035, ir, square=True, poly=True)
        foil(f"Spandrel{k}", 0, -0.03, z1 - 0.3, 0.12, ir, lobes=3, thick=0.015)
        set_group("Glass")
        B20.tprism(f"Glass{k}", WS.rect(hw - 0.06, z0 + 0.08, z1 - 0.08), 0.03, 0.02, K["glass"])
        set_group("Main")
        _place(s, (math.cos(a) * ap, math.sin(a) * ap, 0), (math.cos(a), math.sin(a)))
    for i, (x, y) in enumerate(poly_path(rc + 0.02, 8)):
        tube(f"Shaft{i}", [(x, y, z0), (x, y, z1)], 0.085, ir, poly=True)
        sphere(f"ShaftCap{i}", 0.12, (x, y, z1 - 0.02), ir, seg=10, rings=5, scale=(1, 1, 0.6))
    mould("Frieze", poly_path(rc, 8), [(-0.3, z1 - 0.02), (0.1, z1 - 0.02), (0.1, z1 + 0.4), (-0.3, z1 + 0.4)], K["enamel"], closed=True)
    for i, (x, y) in enumerate(poly_path(rc, 8)):
        nx, ny = poly_path(rc, 8)[(i + 1) % 8]
        mx, my = (x + nx) / 2, (y + ny) / 2
        L = math.hypot(mx, my)
        sphere(f"Boss{i}", 0.11, (mx / L * (L + 0.1), my / L * (L + 0.1), z1 + 0.19), K["gilt"], seg=10, rings=5)
    mould("Cornice", poly_path(rc, 8), [(-0.3, z1 + 0.38), (0.16, z1 + 0.38), (0.26, z1 + 0.5), (0.28, z1 + 0.62), (-0.3, z1 + 0.62)], K["dk"], closed=True)
    k8 = 1 / math.cos(math.pi / 8)
    zd = z1 + 0.62
    prof = [(r * k8, zd + z) for r, z in [(0, 0.0), (3.05, 0.0), (3.1, 0.12), (2.95, 0.4), (2.75, 0.95), (2.4, 1.5), (1.85, 2.0), (1.2, 2.35), (0.7, 2.6),
                                           (0.45, 2.85), (0.3, 3.15), (0, 3.25)]]
    s = _mark()
    tiled("Lead")
    tlathe("Dome", prof, "Lead", seg=8, mat=K["tile"])
    set_group("Main")
    for i in range(8):
        a = i / 8 * 2 * math.pi
        tube(f"Rib{i}", [(math.cos(a) * (r * 1.015 + 0.02), math.sin(a) * (r * 1.015 + 0.02), z + 0.02) for r, z in prof[2:-1]], 0.06, K["lead"])
    _octa(s)
    moon_finial("Finial", 0, 0, zd + 3.15, K, h=2.0, s=0.9)
    # the corona inside
    zc = 2.3
    hoop("Corona", (0, 0, zc), 1.1, "Z", ir, thick=0.04)
    for k in range(3):
        a = k * 2 * math.pi / 3
        tube(f"Chain{k}", [(math.cos(a) * 1.08, math.sin(a) * 1.08, zc), (0, 0, z1 + 0.5)], 0.015, ir, poly=True)
    wax = wax_mat()
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, y = math.cos(a) * 1.1, math.sin(a) * 1.1
        cyl(f"Cup{k}", 0.07, 0.05, (x, y, zc + 0.04), K["brass"], verts=10)
        tip = candle(f"Candle{k}", x, y, zc + 0.065, 0.3, wax, r=0.04)
        set_group("Glow")
        flame(f"Flame{k}", (x, y, tip - 0.005), h=0.12)
        set_group("Main")
    return _dims()


def skylight_roof(M):
    """A ridge rooflight (8 x 4) of clear glass on cast-iron glazing bars, on a lead kerb, glazed gable ends, a little
    cresting along its iron ridge and gilt knobs at the ends."""
    K = kit(M)
    ir = K["iron"]
    hw, hd = 4.0, 2.0
    mould("Kerb", rect_path(hw, hd), [(-0.25, 0.0), (0.06, 0.0), (0.06, 0.5), (-0.25, 0.5)], K["lead"], closed=True)
    z0 = 0.5
    zr = z0 + hd
    for sy in (-1, 1):
        set_group("Glass")
        slab2(f"Glass{sy}", (sy * hd, z0), (0.0, zr), -hw + 0.05, hw - 0.05, 0.02, 0.03, K["glass"], ridge=True)
        set_group("Main")
        n = 10
        for k in range(n + 1):
            x = -hw + 0.05 + (2 * hw - 0.1) * k / n
            tube(f"Bar{sy}{k}", [(x, sy * (hd + 0.02), z0 + 0.04), (x, 0, zr + 0.04)], 0.035, ir, square=True, poly=True)
        tube(f"EaveBar{sy}", [(-hw, sy * (hd + 0.01), z0 + 0.04), (hw, sy * (hd + 0.01), z0 + 0.04)], 0.045, ir, square=True, poly=True)
    for sx in (-1, 1):
        set_group("Glass")
        B20.tprism(f"End{sx}", WS.ccw([(-hd + 0.05, z0 + 0.02), (hd - 0.05, z0 + 0.02), (0.0, zr - 0.04)]), sx * (hw - 0.04), 0.02, K["glass"], plane="YZ")
        set_group("Main")
        tube(f"EndFrame{sx}", [(sx * hw, -hd, z0 + 0.04), (sx * hw, 0, zr + 0.04), (sx * hw, hd, z0 + 0.04)], 0.045, ir, square=True, poly=True)
        tube(f"EndPost{sx}", [(sx * hw, 0, z0 + 0.04), (sx * hw, 0, zr)], 0.03, ir, square=True, poly=True)
        sphere(f"Knob{sx}", 0.13, (sx * (hw + 0.02), 0, zr + 0.2), K["gilt"], seg=12, rings=6)
    tube("Ridge", [(-hw, 0, zr + 0.06), (hw, 0, zr + 0.06)], 0.06, ir, square=True, poly=True)
    cresting("Crest", -hw + 0.4, hw - 0.4, zr + 0.1, K, h=0.45, step=0.8)
    return _dims()


# ================================================================== broken, mossy and patched

def _plane_point(R, s, x, yy, lift):
    """A point on a Pitch's slates (front s = -1 or back), yy studs out from the ridge, and the plane's frame."""
    p = Vector((x, s * yy, R.z_under(yy))) + R.n(s) * lift
    up = Vector((0, -s * math.cos(R.p), math.sin(R.p)))
    return p, Matrix((Vector((1, 0, 0)), up, R.n(s))).transposed().to_4x4()


def _on_roof(R, s, x, yy, lift, rot=0.0):
    p, F = _plane_point(R, s, x, yy, lift)
    return Matrix.Translation(p) @ F @ Matrix.Rotation(rot, 4, "Z")


def loose_slates(prefix, R, K, spots, rnd, mat=None):
    for k, (s, x, yy, rot) in enumerate(spots):
        b = _mark()
        box(f"{prefix}{k}", (0.95, 0.6, 0.035), (0, 0, 0.02), mat or K["slate"], bevel=0.006, segments=1)
        _xform(b, _on_roof(R, s, x, yy, 2 * TS - 0.02 + 0.015, rot) @ Matrix.Rotation(rnd.uniform(-0.06, 0.06), 4, "X"))


def grid_slab(name, R, s, x0, x1, lift, thick, keep, mat, step_x=1.0, step_t=0.6):
    """A plane's layer as a grid of slate-sized cells, keeping those where keep(i, j) (j counts up from the eaves);
    the holes have stepped edges like slates torn off course by course."""
    c, sn = math.cos(R.p), math.sin(R.p)
    T = R.ye / c
    nx = round((x1 - x0) / step_x)
    nt = int(math.ceil(T / step_t))
    n = R.n(s)
    up = Vector((0, -s * c, sn))
    base = Vector((x0, s * R.ye, R.ze))

    def P_(i, j, h):
        t = min(j * step_t, T)
        p = base + Vector((i * (x1 - x0) / nx, 0, 0)) + up * t + n * h
        if j * step_t >= T - 1e-6:                    # the top row is cut vertical at the ridge
            p = p - up * (p.y / up.y)
        return p
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = {}

    def V(i, j, k):
        key = (i, j, k)
        if key not in vs:
            vs[key] = bm.verts.new(P_(i, j, lift if k == 0 else lift + thick))
        return vs[key]
    kept = {(i, j) for i in range(nx) for j in range(nt) if keep(i, j)}
    for (i, j) in kept:
        bm.faces.new((V(i, j, 1), V(i + 1, j, 1), V(i + 1, j + 1, 1), V(i, j + 1, 1)))
        bm.faces.new((V(i, j + 1, 0), V(i + 1, j + 1, 0), V(i + 1, j, 0), V(i, j, 0)))
        for (di, dj, a, b) in ((0, -1, (i, j), (i + 1, j)), (1, 0, (i + 1, j), (i + 1, j + 1)), (0, 1, (i + 1, j + 1), (i, j + 1)), (-1, 0, (i, j + 1), (i, j))):
            if (i + di, j + dj) not in kept:
                bm.faces.new((V(*a, 0), V(*b, 0), V(*b, 1), V(*a, 1)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    md = ob.modifiers.new("Tri", "TRIANGULATE")
    return ob, nx, nt


def ruined_roof(M):
    """A 12-stud run of the 45 degree roof fallen in: slates torn off course by course round a ragged hole down to
    the charred rafters and broken battens, the lead underlay torn back, a gap in the ridge with a fallen tile, a
    bent run of cresting, loose slates on the roof and in a sagging gutter, moss everywhere. Open ends, like
    GableSection."""
    K = kit(M)
    rnd = random.Random(2811)
    R = Pitch(16.0, 12.0, 45)
    L = 6.0
    c = math.cos(R.p)
    noise = {(i, j): rnd.uniform(-0.35, 0.35) for i in range(20) for j in range(20)}

    def hole(i, j, grow=0.0):
        dx, dy = (i + 0.5 - 7.2) / (3.3 + grow), (j + 0.5 - 9.0) / (4.6 + grow)
        return dx * dx + dy * dy < 1.0 + noise.get((i, j), 0)
    tiled("Moss")
    grid_slab("SlateFront", R, -1, -L, L, TS - 0.02, TS, lambda i, j: not hole(i, j), K["tile"])
    tiled("Lead")
    grid_slab("UnderFront", R, -1, -L + 0.05, L - 0.05, 0.0, TS, lambda i, j: not hole(i, j, grow=1.1), K["tile"])
    R._mat = K["tile"]
    tiled("Moss")
    R.slab("SlateBack", -L, L, 1, TS - 0.02, TS)
    tiled("Lead")
    R.slab("UnderBack", -L, L, 1, 0.0, TS, inset=0.06, inset_x=(0.05, 0.05))
    set_group("Main")
    _eaves("E", R, -L, L, K, front=False)
    cornice("CorniceF", [(-L, -R.D / 2), (L, -R.D / 2)], K, closed=False, corbels=True)
    gy = -(R.D / 2 + CP + 0.02)
    gutter("GutterF", [(-L + 0.02, gy), (0.6, gy)], R.ze - 0.03, K)
    s = _mark()
    gutter("GutterSag", [(0.0, gy), (5.4, gy)], R.ze - 0.03, K, brackets=False)
    _xform(s, Matrix.Translation((0.65, 0, R.ze - 0.2)) @ Matrix.Rotation(math.radians(7), 4, "Y") @ Matrix.Translation((0, 0, -(R.ze - 0.2))))
    # charred rafters and broken battens under the hole
    for k in range(8):
        x = -L + 0.75 + k * 1.5
        a = Vector((x, -R.ye + 0.35, R.ze + 0.35)) - R.n(-1) * 0.22
        b = Vector((x, -0.15, R.Hb - 0.15)) - R.n(-1) * 0.22
        if k == 4:
            m = a + (b - a) * 0.42
            bar(f"Rafter{k}", a, m, 0.22, 0.3, K["charred"], up=tuple(R.n(-1)))
            bar(f"RafterBroken{k}", b, b + (m - b) * 0.55 + Vector((0.15, -0.35, -0.6)), 0.22, 0.3, K["charred"], up=(0, 0, 1))
        else:
            bar(f"Rafter{k}", a, b, 0.22, 0.3, K["charred"], up=tuple(R.n(-1)))
    up = Vector((0, c, math.sin(R.p)))
    base = Vector((0, -R.ye, R.ze))
    k = 0
    for j in range(3, 16):
        p = base + up * (j * 0.6 + 0.3) + R.n(-1) * 0.05
        xs = [x for x in range(-6, 6) if hole(x + 6, j, grow=1.1) and not hole(x + 6, j, grow=-0.3) or (hole(x + 6, j, grow=1.1) and rnd.random() < 0.55)]
        if not xs:
            continue
        x0, x1 = min(xs) - 0.2, max(xs) + 1.2
        if rnd.random() < 0.4:
            mid = (x0 + x1) / 2 + rnd.uniform(-0.6, 0.6)
            segs = [(x0, mid - 0.35), (mid + 0.35, x1)]
        else:
            segs = [(x0, x1)]
        for a0, a1 in segs:
            if a1 - a0 < 0.4:
                continue
            bar(f"Batten{k}", (a0, p.y, p.z), (a1, p.y, p.z), 0.12, 0.05, K["charred"], up=tuple(R.n(-1)))
            k += 1
    # the ridge: tiles lost over a stretch, one lying on the roof, and a run of cresting knocked askew
    ridge_tiles("RidgeL", -L, -0.8, R.top - 0.08, K, knobs=False)
    ridge_tiles("RidgeR", 2.6, L, R.top - 0.08, K, knobs=False)
    cyl("RidgeEnd", 0.3, 0.1, (-0.75, 0, R.top - 0.08), K["glaze"], rot=(0, math.pi / 2, 0), verts=20)
    b = _mark()
    cyl("FallenTile", 0.26, 0.95, (0, 0, 0.2), K["glaze"], rot=(0, math.pi / 2, 0.3), verts=16, bevel=0.0)
    _xform(b, _on_roof(R, -1, -2.6, 2.2, 2 * TS, 0.4))
    cresting("CrestL", -L + 0.45, -1.2, R.top + 0.17, K)
    s = _mark()
    cresting("CrestR", 3.0, L - 0.45, R.top + 0.17, K)
    _xform(s, Matrix.Translation((3.0, 0, R.top + 0.1)) @ Matrix.Rotation(math.radians(-16), 4, "X") @ Matrix.Rotation(math.radians(5), 4, "Y") @
           Matrix.Translation((-3.0, 0, -(R.top + 0.1))))
    loose_slates("Loose", R, K, [(-1, 0.8, 5.7, 0.3), (-1, 1.9, 6.1, -0.5), (-1, -0.6, 4.9, 1.1), (-1, 3.4, 5.2, 0.2), (-1, -2.0, 1.8, 0.7),
                                 (-1, 4.3, 1.2, -0.3), (1, -2.5, 4.0, 0.4), (-1, 2.2, 0.9, 1.4)], rnd)
    for k, x in enumerate((1.2, 2.8, 4.2)):
        b = _mark()
        box(f"GutterSlate{k}", (0.6, 0.4, 0.035), (0, 0, 0), K["slate"], bevel=0.006, segments=1, rot=(0.9, 0.3 * k, 0.5))
        _xform(b, Matrix.Translation((x, gy - 0.25, R.ze - 0.22 - 0.03 * k)))
    _moss_on(K, rnd, [(rnd.uniform(-5.5, 5.5), -R.ye + rnd.uniform(0.4, 1.4), 0) for _ in range(6)], size=0.16)
    for ob in P.PARTS[-6:]:
        ob.location.z = R.z_top(abs(ob.location.y)) + 0.02
    return _dims()


def mossy_gable_roof(M):
    """GableRoof gone to moss: mossy slates, cushions of moss along the ridge, the copings and the gutters, slipped
    slates, and one pinnacle broken off at the crockets."""
    K = kit(M)
    rnd = random.Random(2812)
    R = Pitch(16.0, 12.0, 45)
    W, D = R.W, R.D
    R.roof("Roof", -(W / 2 - 0.4), W / 2 - 0.4, "Moss", K)
    _eaves("E", R, -(W / 2 - 0.1), W / 2 - 0.1, K)
    for sx in (-1, 1):
        zk, za = _parapet_gable(f"Gable{sx}", R, K, sx, finial=sx > 0)
        if sx < 0:
            x = sx * (W / 2 - 0.4)
            box("PinnacleStump", (0.56, 0.56, 0.6), (x, 0, za + 0.48), K["dk"], bevel=0.03)
            box("PinnacleBreak", (0.5, 0.5, 0.18), (x + 0.04, 0.03, za + 0.84), K["dk"], bevel=0.06, rot=(0.12, -0.15, 0.3))
        for k in range(5):
            t = (k + 0.5) / 5
            yy = R.ye * (1 - t) + 0.2 * t
            for sy in (-1, 1):
                _moss_on(K, rnd, [(sx * (W / 2 - 0.4 + rnd.uniform(-0.3, 0.3)), sy * yy, R.z_top(yy) + 0.62)], size=0.18)
    ridge_tiles("Ridge", -(W / 2 - 0.7), W / 2 - 0.7, R.top - 0.08, K, knobs=False)
    cresting("Crest", -(W / 2 - 1.2), W / 2 - 1.2, R.top + 0.17, K)
    _moss_on(K, rnd, [(rnd.uniform(-7, 7), rnd.choice((-0.25, 0.25)), R.top + 0.1) for _ in range(9)], size=0.17)
    _moss_on(K, rnd, [(rnd.uniform(-7, 7), s * (D / 2 + CP + 0.27), R.ze - 0.12) for _ in range(5) for s in (-1, 1)], size=0.16)
    loose_slates("Slipped", R, K, [(-1, -3.1, 2.0, 0.35), (-1, 2.4, 3.6, -0.25), (-1, 5.2, 1.4, 0.6), (1, -4.4, 2.6, -0.4), (-1, -5.6, 4.6, 0.15)], rnd)
    return _dims()


def patched_roof(M):
    """GableRoofLow patched up: riveted lead patches and a tin sheet over the worst of it, odd replacement slates, a
    tarred seam."""
    K = kit(M)
    rnd = random.Random(2813)
    gable_roof_low(M)
    R = Pitch(16.0, 12.0, 30)
    tin = material("Tin", "NH_Iron", tint=(0.2, 0.19, 0.17), scale=0.6, rough_add=0.15, wear=0.6, wear_metal=True, dirt=1.0)
    tar = flat("Tar", (0.01, 0.01, 0.012), 0.35, dirt=0.3)
    odd = material("OddSlate", "NH_Slate", tint=(0.1, 0.09, 0.085), scale=0.35, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.2)
    lift = 2 * TS - 0.02
    for k, (s, x, yy, w, h, rot) in enumerate(((-1, -4.2, 3.6, 1.8, 1.3, 0.06), (-1, 2.6, 5.4, 1.1, 0.9, -0.1), (1, 1.0, 3.0, 2.3, 1.1, 0.04))):
        b = _mark()
        box(f"Patch{k}", (w, h, 0.03), (0, 0, 0.015), K["lead"], bevel=0.008, segments=1)
        for cx in (-1, 1):
            for cy in (-1, 1):
                sphere(f"Rivet{k}{cx}{cy}", 0.035, (cx * (w / 2 - 0.08), cy * (h / 2 - 0.08), 0.035), K["iron"], seg=6, rings=3, scale=(1, 1, 0.5))
        _xform(b, _on_roof(R, s, x, yy, lift + 0.005, rot))
    b = _mark()
    box("Tin", (2.2, 1.6, 0.025), (0, 0, 0.02), tin, bevel=0.0, segments=1)
    for k in range(6):
        box(f"TinRib{k}", (0.05, 1.6, 0.035), (-0.95 + k * 0.38, 0, 0.04), tin, bevel=0.0, segments=1)
    _xform(b, _on_roof(R, -1, 5.3, 2.4, lift + 0.005, -0.08))
    spots = [(-1, -1.5, 1.6, 0.0), (-1, -0.5, 1.6, 0.0), (-1, 0.6, 4.5, 0.02), (1, -3.0, 5.0, 0.0), (1, 4.6, 1.9, -0.03), (-1, 6.4, 6.0, 0.0)]
    loose_slates("Odd", R, K, spots, rnd, mat=odd)
    b = _mark()
    box("Tar", (5.0, 0.09, 0.02), (0, 0, 0.012), tar, bevel=0.0, segments=1)
    _xform(b, _on_roof(R, -1, -1.0, 6.4, lift + 0.003, 0.12))
    return _dims()


# ================================================================== finials

def moon_finial_piece(M):
    """A ridge or spire finial: a lead base, an iron spike through two gilt orbs to a gilt crescent moon."""
    K = kit(M)
    moon_finial("Finial", 0, 0, 0, K, h=3.4, s=1.5)
    return _dims()


def key_finial_piece(M):
    """The crest's gilt key standing on a gilt orb and an iron rod, on a lead base."""
    K = kit(M)
    key_finial("Key", 0, 0, 0, K, s=1.5)
    return _dims()


def stone_pinnacle(M):
    """A crocketed stone pinnacle for a parapet or a buttress: a moulded base, a shaft with gablets and blind trefoils
    on its four faces, a spire with crockets up the angles, a fleuron and a gilt orb."""
    K = kit(M)
    dk, st = K["dk"], K["st"]
    w = 1.1
    box("Base", (w + 0.4, w + 0.4, 0.35), (0, 0, 0.175), dk, bevel=0.04)
    box("Mould", (w + 0.2, w + 0.2, 0.18), (0, 0, 0.44), st, bevel=0.05)
    box("Shaft", (w, w, 2.1), (0, 0, 1.58), st, bevel=0.03)
    for k in range(4):
        s = _mark()
        hw = w / 2 + 0.04
        chevron(f"Gablet{k}", [(-hw - 0.05, 2.55), (0.0, 3.45), (hw + 0.05, 2.55)], 0.1, 0.06, 0, 0.18, dk, plane="XZ")
        B20.tprism(f"GabletFace{k}", WS.ccw([(-hw, 2.6), (hw, 2.6), (0.0, 3.35)]), 0.0, 0.1, st)
        foil(f"GabletFoil{k}", 0, -0.06, 2.85, 0.13, dk, lobes=3, thick=0.016)
        tube(f"Blind{k}", [(-0.3, -0.005, 0.8)] + [(x, -0.005, z) for x, z in WS.pointed(0.3, 1.9, 2.35, 8)] + [(0.3, -0.005, 0.8)], 0.03, dk, square=True,
             poly=True)
        foil(f"BlindFoil{k}", 0, -0.01, 1.95, 0.15, dk, lobes=3, thick=0.016)
        _crockets(f"GabletCrocket{k}", [(sx * hw * 0.5, -0.02, 2.55 + 0.9 * 0.5 + 0.05) for sx in (-1, 1)], dk, size=0.07)
        sphere(f"GabletKnob{k}", 0.07, (0, 0, 3.55), dk, seg=8, rings=4)
        a = k * math.pi / 2
        _xform(s, Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, -w / 2 - 0.0, 0)))
    zb, zt = 2.6, 6.0
    _spike("Spire", (0, 0, (zb + zt) / 2), 0.62, zt - zb, st, verts=4, rot=(0, 0, math.pi / 4))
    for k in range(4):
        t = (k + 1) / 5
        r = 0.62 * (1 - t) * 0.72
        for j in range(4):
            a = j * math.pi / 2 + math.pi / 4
            sphere(f"Crocket{k}{j}", 0.11 * (1 - t * 0.4), (math.cos(a) * (r + 0.05), math.sin(a) * (r + 0.05), zb + (zt - zb) * t), dk, seg=6, rings=3,
                   scale=(1, 1, 1.4))
    for j in range(4):
        a = j * math.pi / 2
        sphere(f"Fleuron{j}", 0.1, (math.cos(a) * 0.12, math.sin(a) * 0.12, zt + 0.05), dk, seg=8, rings=4, scale=(1.3, 1.3, 0.7))
    sphere("Orb", 0.11, (0, 0, zt + 0.25), K["gilt"], seg=12, rings=6)
    return _dims()

BUILDERS = {
    "GableRoof": gable_roof,
    "GableSection": gable_section,
    "GableRoofLow": gable_roof_low,
    "GableRoofSteep": gable_roof_steep,
    "HipRoof": hip_roof,
    "PyramidRoof": pyramid_roof,
    "MansardRoof": mansard_roof,
    "GambrelRoof": gambrel_roof,
    "LeanToRoof": lean_to_roof,
    "FlatRoofParapet": flat_roof_parapet,
    "BattlementRoof": battlement_roof,
    "ConeTurretCap": cone_turret_cap,
    "WitchHatCap": witch_hat_cap,
    "OctagonSpire": octagon_spire,
    "BroachSpire": broach_spire,
    "BellCastCap": bell_cast_cap,
    "OnionDome": onion_dome,
    "GabledDormer": gabled_dormer,
    "OxeyeDormer": oxeye_dormer,
    "RidgeCresting": ridge_cresting,
    "RidgeTiles": ridge_tiles_piece,
    "HipCap": hip_cap,
    "RoofCornerL": roof_corner_l,
    "EavesGutter": eaves_gutter,
    "ChimneyStack": chimney_stack,
    "TwinFlue": twin_flue,
    "Weathervane": weathervane,
    "BellCote": bell_cote,
    "Cupola": cupola,
    "LanternRoof": lantern_roof,
    "SkylightRoof": skylight_roof,
    "RuinedRoof": ruined_roof,
    "MossyGableRoof": mossy_gable_roof,
    "PatchedRoof": patched_roof,
    "MoonFinial": moon_finial_piece,
    "KeyFinial": key_finial_piece,
    "StonePinnacle": stone_pinnacle,
}
BUILDERS = {n: finish(f) for n, f in BUILDERS.items()}
for _n in BUILDERS:
    for _g, (_set, _tile) in TILES.items():
        P.TILED[f"{_n}_{_g}"] = (_set, _tile)
    P.CANVAS[f"{_n}_Room"] = "WindowRoom"
P.PREVIEW_PAD.update({n: 1.0 for n in BUILDERS})
P.PREVIEW_PAD.update({"RidgeCresting": 1.1, "RidgeTiles": 1.15, "HipCap": 1.1, "MoonFinial": 1.5, "KeyFinial": 1.5, "StonePinnacle": 1.3,
                      "Weathervane": 1.2, "OxeyeDormer": 1.4, "GabledDormer": 1.2, "TwinFlue": 1.2, "ChimneyStack": 1.2, "BellCote": 1.15})
P.BUILD.update(BUILDERS)
