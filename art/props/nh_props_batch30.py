"""Props batch 30 (2026-11-05): the library kit for nh_props.py, an old haunted school library in the Institution's look: dark
oak and ebonised trim, brass and gilt, wrought iron, deep crimson (#600E1A) leather and enamel, bone paper, wax and ink,
candlelight. Every book is a real book: one of 142 original bindings from library_atlas.py (gilt titles, raised bands,
tooled panels), its spine mapped onto the printed atlas and baked, with extra bake room so the titles stay readable.

Shelving
  LibShelfTall      a tall dark-oak bookcase: seven shelves, ebony pilasters with brass capitals, a cornice, a pointed crest
                    and a gilt HISTORY plaque on the frieze
  LibShelfArched    a gothic bookcase under a pointed arch: carved spandrels, pinnacles, a traceried niche at the top
  LibShelfCorner    a corner bookcase (its two backs meet at +Y), angled shelves, a crest
  LibShelfDouble    a double-sided stack, books on both faces, traceried end panels, plaques both sides
  LibShelfLadder    a very tall bookcase with a brass rail and a rolling ladder hooked on it (Ladder: its own piece)
  LibShelfHalf      a half-height case with a moulded top: a book pile, brass bookends and a chamber candle (Glow)
  ShelfEndCap       an ornate end panel for the end of a stack: twin lancets, a crocketed gable, a POETRY plaque
  ForbiddenCage     the restricted section: a bookcase of black and plum books locked in an iron cage, chained shut, a
                    padlock, a RESTRICTED plaque and a DO NOT OPEN tag
  ChainedBookcase   an old chained-library press: each book on an iron chain to a rod, a sloped reading desk in front
Furniture
  ReadingTableLong  a 12-stud reading table on pierced trestles, a crimson leather top, a raised book rail with two green
                    banker's lamps (Glow), open books, an inkwell and quill
  ReadingTableRound a round table on a baluster and scroll feet, a crimson inset, books and a magnifying glass
  StudyCarrel       a study carrel: high arched sides, a book shelf, a lamp under it (Glow), a QUIET PLEASE card
  LibraryChair      an armless reading chair with a pointed back and a crimson cushion (seat top 1.55, for R6 sitters)
  CirculationDesk   the librarian's desk: traceried front, a LIBRARIAN plaque, a bell, a date stamp, the borrowing ledger,
                    a card box, returned books, a candle lamp (Glow); shelves on the librarian's side
  Lectern           a brass raven with spread wings holding a chained open bestiary, on an iron column and stepped base
  CardCatalogue     a 30-drawer card catalogue (labelled A to Fa-Fz) on a stand, one drawer pulled out with its cards
  MapChest          a plan chest of six wide drawers; on top the map of the moor, brass weights, dividers, a magnifier
  NewspaperRack     an iron and oak rack of three newspapers (The Nightmare Herald) on reading sticks
Fittings
  StepStool         two-step library steps with crimson leather treads
  RollingLadder     a free-standing platform ladder on castors with handrails
  TerrestrialGlobe  a floor globe of an invented world (Orbis Nocturnus) in a brass meridian on a carved stand (Globe spins)
  ArmillarySphere   a brass armillary sphere on a turned stand (Rings spin)
  BankerLamp        a green glass banker's lamp on brass (Glow)
  CandleLamp        a two-candle reading lamp with a crimson shade on its rod (Glow)
  LibCandelabra     a three-light table candelabrum, dripping (Glow)
  LibrarianBust     a bronze bust of the first librarian, spectacles and a quill, on a fluted pedestal
  LibraryClock      a black and crimson longcase clock: a moon-phase arch, a lancet glass door (Glass) and a pendulum
                    (Pendulum: swings, NHSwing)
  SilenceSign       a crimson enamel SILENCE sign in raised gilt letters on an iron stand
Books
  BookPile          three floor piles of books, one open on top
  OpenBook          an open book (the phases of the moon) on a crimson book cushion
  ScrollRack        a diamond-lattice rack of rolled scrolls with numbered tags
  BookCart          a book trolley on iron castors, two tiers of books
  ReturnsBox        an iron-bound returns box: a brass slot, a RETURNS plaque, a book half posted
Atmosphere
  ShelfDusty        a tall bookcase gone quiet: dust on every ledge, cobwebs, gaps and fallen books, a candle stub
  ShelfToppled      a fallen bookcase on its back, books tumbled in it and spilled across the floor
  CobwebCorner      a corner of cobwebs for a room's top corner (the corner is at +Y, the webs span the two walls)

Front faces -Y, Z is up, the origin is at the bottom centre. Pieces: Main; Glow (flames and bulbs: Neon); Glass (the clock
pane); Ladder; Globe and Rings (spin); Pendulum (swings). Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish, _gable, _pinnacle
from nh_props_batch3 import sphere, cone, flame
from nh_props_batch4 import lathe, hoop, strip, prism, _mark, _xform, _dims, flat, _solid
from nh_props_batch8 import _panel
from nh_props_batch9 import foil, tracery, wax_mat
from nh_props_batch10 import gilt
from nh_props_batch12 import frustum
from nh_props_batch24 import _text
import nh_props_batch20 as B20
import window_shapes as WS

ATLAS = json.load(open(os.path.join(P.HERE, "library_atlas.json")))
REG = ATLAS["regions"]
DESIGNS = ATLAS["books"]
SETNAMES = sorted({d["set"] for d in DESIGNS if d["set"]})
FONT_SIGN = "C:/Windows/Fonts/palab.ttf"
FONT_SIGN_I = "C:/Windows/Fonts/palabi.ttf"
DEG = math.pi / 180
BOOK_KS, BOOK_KC = 2.6, 0.12     # bake room: a book's spine at 2.6x the kit's texel density, its boards and edges at 0.12x


def RX(a):
    return Matrix.Rotation(a, 4, "X")


def RY(a):
    return Matrix.Rotation(a, 4, "Y")


def RZ(a):
    return Matrix.Rotation(a, 4, "Z")


def T(x, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def uvk(ob, k):
    """Give a part a bake-room weight (see _scale_islands): below 1 for plain threads and links, above 1 for print."""
    at = ob.data.attributes.get("nh_uvk") or ob.data.attributes.new("nh_uvk", "FLOAT", "FACE")
    for d in at.data:
        d.value = k
    return ob


def chain(prefix, pts, mat, r=0.06, thick=0.014, sag=0.0):
    """An iron chain along a path: oval links, each in the plane of the path, alternately turned a quarter."""
    pts = [Vector(p) for p in pts]
    segs = list(zip(pts, pts[1:]))
    total = sum((b - a).length for a, b in segs)
    n = max(2, int(total / (r * 1.7)))
    k = 0
    for i in range(n):
        t = (i + 0.5) / n * total
        for a, b in segs:
            L = (b - a).length
            if t <= L or (a, b) == segs[-1]:
                d = (b - a).normalized()
                p = a + d * min(t, L)
                p.z -= sag * math.sin((i + 0.5) / n * math.pi)
                break
            t -= L
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        side = d.cross(up).normalized()
        nrm = side if k % 2 else d.cross(side).normalized()
        y = nrm.cross(d).normalized()
        rot = Matrix((d, y, nrm)).transposed().to_4x4()
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=thick, major_segments=8, minor_segments=4)
        lk = bpy.context.active_object
        lk.name = f"{prefix}{k}"
        lk.matrix_world = Matrix.Translation(p) @ rot @ Matrix.Diagonal((1.45, 1.0, 1.0, 1.0))
        uvk(_finish(lk, mat, 0), 0.5)
        k += 1


# ------------------------------------------------------------------ materials

def _image(fname, colour):
    im = bpy.data.images.get(fname)
    if im is None:
        im = bpy.data.images.load(os.path.join(P.OUT_TEX, fname))
        if not colour:
            im.colorspace_settings.name = "Non-Color"
    return im


def atlas_mat(name="LibAtlas", image="LibraryAtlas", maps=True, rough=0.6, wear=0.1, dirt=0.55, leather=0.3):
    """The printed atlas through the "Spine" UV layer: colour, gilt (metal, smoother), height (a bump for the raised bands and
    the debossed titles) over a fine leather grain; then the usual bake-time weathering."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L(bs.outputs["BSDF"], out.inputs["Surface"])
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Spine"

    def tex(kind, colour):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _image(f"{image}_{kind}.png", colour)
        t.interpolation = "Cubic"
        L(uvn.outputs["UV"], t.inputs["Vector"])
        return t.outputs["Color"]

    def mth(op, a, b, c=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]
    col = tex("color", True)
    ln = P._tex(nt, "NH_Leather", "normal", 1.8, 0, -900)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = leather
    L(ln.outputs["Color"], nm.inputs["Color"])
    if maps:
        g = tex("gilt", False)
        h = tex("height", False)
        metal = mth("MULTIPLY", g, 0.92)
        rgh = mth("MULTIPLY_ADD", g, -0.38, rough, clamp=True)
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        bump.inputs["Distance"].default_value = 0.004
        L(h, bump.inputs["Height"])
        L(nm.outputs["Normal"], bump.inputs["Normal"])
        nrm = bump.outputs["Normal"]
    else:
        v = nt.nodes.new("ShaderNodeValue")
        v.outputs[0].default_value = 0.0
        metal = v.outputs[0]
        r = nt.nodes.new("ShaderNodeValue")
        r.outputs[0].default_value = rough
        rgh = r.outputs[0]
        nrm = nm.outputs["Normal"]
    P._weather(nt, bs, col, rgh, metal, nrm, wear, False, dirt)
    return m


def mats(M):
    crim = (0.117, 0.0045, 0.0103)
    return {
        "oak": material("LibOak", "NH_DeskWood", tint=(0.115, 0.062, 0.036), scale=0.22, rough_add=0.04, wear=0.4),
        "oakmid": material("LibOakMid", "NH_DeskWood", tint=(0.19, 0.108, 0.062), scale=0.22, rough_add=0.05, wear=0.45),
        "ebony": material("LibEbony", "NH_DeskWood", tint=(0.065, 0.05, 0.046), scale=0.3, rough_add=0.02, wear=0.35),
        "back": material("LibOakBack", "NH_DeskWood", tint=(0.058, 0.033, 0.021), scale=0.3, rough_add=0.1, wear=0.2),
        "crimson": material("LibCrimsonHide", "NH_Leather", tint=(crim[0] * 1.6, crim[1] * 1.6, crim[2] * 1.6), scale=1.6, normal=0.45, wear=0.25,
                            dirt=0.7),
        "enamel": material("LibEnamel", "NH_PaintedMetal", tint=(0.2, 0.012, 0.025), scale=1.2, rough_mul=0.5, wear=0.1, wear_metal=True),
        "velvet": flat("LibVelvet", (0.085, 0.006, 0.013), 0.95, dirt=0.6),
        "gilt": gilt(),
        "brass": material("LibBrass", "NH_Brass", tint=(1, 1, 1), scale=0.5, wear=0.18, dirt=0.4),      # cleaner than the school's: small pieces
        "iron": M["iron"],
        "steel": M["brasssteel"],
        "paper": M["paper"],
        "wax": wax_mat(),
        "glass": M["glassclear"],
        "ink": M["glass"],
        "green": material("BankerGreen", base=(0.006, 0.075, 0.028), rough=0.16, wear=0.0, dirt=0.3),
        "bone": flat("DialBone", (0.62, 0.57, 0.46), 0.6, dirt=0.6),
        "night": material("MoonNight", base=(0.02, 0.03, 0.09), rough=0.35, wear=0.1),
        "bronze": material("LibBronze", "NH_Brass", tint=(0.26, 0.19, 0.12), scale=0.6, rough_add=0.22, wear=0.3, dirt=0.6),
        "bronzedk": material("LibBronzeDk", "NH_Brass", tint=(0.12, 0.09, 0.06), scale=0.6, rough_add=0.25, wear=0.3, dirt=0.6),
        "web": flat("Cobweb", (0.66, 0.66, 0.64), 0.9, dirt=0.1),
        "atlas": atlas_mat(),
    }


def dustify(strength=0.7, colour=(0.42, 0.4, 0.37)):
    """Dust on everything facing up: mixed into the base colour (with a soft noise), rougher, less metal. Applied to every
    material used so far, before the bake."""
    seen = set()
    for ob in P.PARTS:
        for m in ob.data.materials:
            if m is None or m.name in seen:
                continue
            seen.add(m.name)
            nt = m.node_tree
            bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
            L = nt.links.new
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            L(geo.outputs["Normal"], sep.inputs["Vector"])
            nz = nt.nodes.new("ShaderNodeTexNoise")
            nz.inputs["Scale"].default_value = 5.0

            def mth(op, a, b, clamp=True):
                n = nt.nodes.new("ShaderNodeMath")
                n.operation = op
                n.use_clamp = clamp
                for i, v in enumerate((a, b)):
                    if isinstance(v, (int, float)):
                        n.inputs[i].default_value = v
                    else:
                        L(v, n.inputs[i])
                return n.outputs[0]
            up = mth("MULTIPLY", mth("SUBTRACT", sep.outputs["Z"], 0.35), 2.4)
            fac = mth("MULTIPLY", mth("MULTIPLY", up, mth("ADD", mth("MULTIPLY", nz.outputs["Fac"], 0.8), 0.35)), strength)
            for sock, kind in (("Base Color", "col"), ("Roughness", "rough"), ("Metallic", "metal")):
                inp = bs.inputs[sock]
                if not inp.links:
                    continue
                src = inp.links[0].from_socket
                if kind == "col":
                    mx = nt.nodes.new("ShaderNodeMix")
                    mx.data_type = "RGBA"
                    L(fac, mx.inputs["Factor"])
                    L(src, mx.inputs[6])
                    mx.inputs[7].default_value = (*colour, 1)
                    L(mx.outputs[2], inp)
                elif kind == "rough":
                    L(mth("MAXIMUM", src, mth("MULTIPLY", fac, 1.3)), inp)
                else:
                    L(mth("MULTIPLY", src, mth("SUBTRACT", 1.0, fac)), inp)


# ------------------------------------------------------------------ printed pieces (atlas-mapped meshes)

def _swatch(name):
    r = REG[f"Swatch_{name}"]
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


def _bm_object(name, bm, mat, mtx):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = mtx
    return _finish(ob, mat, 0)


def _bevelled_box(w, d, h, bev, z0=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h + h / 2 + z0))
    if bev > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=1, affect="EDGES", profile=0.5)
    bm.normal_update()
    return bm


def book(name, dz, depth, mtx, mat, bottom=True):
    """One bound book of design dz (spine w x h, at -Y), `depth` deep, its base on z = 0, centred on x. The spine face is
    mapped onto its atlas cell (extra bake room), the boards onto its leather swatch, the edges onto its paper swatch.
    A plain box (the bake rounds its edges in the normal map); bottom=False drops the hidden base of a book standing on a
    shelf."""
    w, h = dz["w"], dz["h"]
    bm = _bevelled_box(w, depth, h, 0.0)
    if not bottom:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES_ONLY")
    uvl = bm.loops.layers.uv.new("Spine")
    ufl = bm.loops.layers.uv.new("Unfold")
    bl = bm.faces.layers.int.new("nh_book")
    u0, v0, u1, v1 = REG[dz["key"]]
    lea, pap = _swatch(dz["leather"]), _swatch(dz["paper"])
    d = depth
    ks, kc = BOOK_KS, BOOK_KC
    for f in bm.faces:
        n = f.normal
        f[bl] = 1
        for lp in f.loops:
            x, y, z = lp.vert.co
            yy = y + d / 2                       # 0 at the spine, d at the back
            # the bake layout, one island per book (studs x weight): the spine big, the boards and edges as thin strips
            # folded out from its sides, its top and (round the right board) the back
            if n.y < -0.5:
                uf = ((x + w / 2) * ks, z * ks)
            elif n.x < -0.5:
                uf = (-yy * kc, z * ks)
            elif n.x > 0.5:
                uf = (w * ks + yy * kc, z * ks)
            elif n.z > 0.5:
                uf = ((x + w / 2) * ks, h * ks + yy * kc)
            elif n.z < -0.5:
                uf = ((x + w / 2) * ks, -yy * kc)
            else:
                uf = (w * ks + d * kc + (w / 2 - x) * kc, z * ks)
            lp[ufl].uv = uf
        if n.y < -0.5:
            for lp in f.loops:
                x, _, z = lp.vert.co
                lp[uvl].uv = (u0 + (h - z) / h * (u1 - u0), v0 + (x + w / 2) / w * (v1 - v0))
        else:
            pt = lea if abs(n.x) >= max(abs(n.y), abs(n.z)) else pap
            for lp in f.loops:
                lp[uvl].uv = pt
    return _bm_object(name, bm, mat, mtx)


def plate(name, key, w, h, t, mtx, mat, edge="black", k=2.0, bev=0.008):
    """A flat plate w x h, t thick, built facing -Y at the origin (centred), its front showing an atlas region."""
    bm = _bevelled_box(w, t, h, min(bev, t * 0.4), z0=-h / 2)
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    u0, v0, u1, v1 = REG[key]
    pt = _swatch(edge)
    for f in bm.faces:
        if f.normal.y < -0.9:
            for lp in f.loops:
                x, _, z = lp.vert.co
                lp[uvl].uv = (u0 + (x + w / 2) / w * (u1 - u0), v0 + (z + h / 2) / h * (v1 - v0))
            f[kl] = k
        else:
            for lp in f.loops:
                lp[uvl].uv = pt
            f[kl] = 0.4
    return _bm_object(name, bm, mat, mtx)


def leaf_sheet(name, key, pts_fn, nu, nv, uv_rect, mat, thick=0.012, k=2.0):
    """A curved sheet (a page, a newspaper) from pts_fn(s, t) -> (x, y, z) over s, t in 0..1, UV-mapped onto part of an atlas
    region (uv_rect = fractions (a0, b0, a1, b1) of it), given a little thickness."""
    u0, v0, u1, v1 = REG[key]
    a0, b0, a1, b1 = uv_rect
    bm = bmesh.new()
    vs = [[bm.verts.new(pts_fn(i / nu, j / nv)) for i in range(nu + 1)] for j in range(nv + 1)]
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            f.smooth = True
            f[kl] = k
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                s, t = ii / nu, jj / nv
                lp[uvl].uv = (u0 + (a0 + (a1 - a0) * s) * (u1 - u0), v0 + (b0 + (b1 - b0) * t) * (v1 - v0))
    ob = _bm_object(name, bm, mat, Matrix.Identity(4))
    return _solid(ob, thick)


def open_book(prefix, key, W, D, mtx, M, K, cover="crimson", lift=0.16):
    """An open book: two boards, two page blocks, and the two printed pages curling up from the gutter. W is the open width,
    D the page height (front to back). Built with its base at the origin, the reader at -Y."""
    s = _mark()
    pw = W / 2 - 0.06
    for sx in (-1, 1):
        box(f"{prefix}Board{sx}", (W / 2, D + 0.06, 0.035), (sx * W / 4, 0, 0.0175), K[cover] if cover in K else M[cover], bevel=0.012)
        box(f"{prefix}Block{sx}", (pw - 0.04, D - 0.04, 0.07), (sx * (pw / 2 + 0.05), 0, 0.07), K["paper"], bevel=0.02)

    def page(side):
        def fn(sv, tv):
            x = side * (0.04 + sv * pw)
            z = 0.1 + lift * math.sin(min(1.0, sv * 1.15) * math.pi / 2) ** 0.6 - 0.05 * sv ** 3
            return (x, -D / 2 + 0.02 + tv * (D - 0.04), z)
        return fn
    leaf_sheet(f"{prefix}PageL", key, page(-1), 10, 1, (0.5, 0, 0.0, 1), K["atlas"], thick=0.01)
    leaf_sheet(f"{prefix}PageR", key, page(1), 10, 1, (0.5, 0, 1.0, 1), K["atlas"], thick=0.01)
    box(f"{prefix}Ribbon", (0.04, 0.5, 0.006), (0.12, -D / 2 - 0.2, 0.09), K["velvet"], bevel=0.0, rot=(0.25, 0, 0))
    _xform(s, mtx)


# ------------------------------------------------------------------ books on shelves

def _fits(hmax, wmax=9.0, pool=None):
    return [d for d in (pool or DESIGNS) if d["h"] <= hmax and d["w"] <= wmax]


def fill_row(prefix, x0, x1, z, y_front, dmax, hmax, rnd, K, p_set=0.22, p_flat=0.1, p_lean=0.1, p_gap=0.06, dfun=None, pool=None,
             fill=1.0):
    """Stand books on a shelf from x0 to x1, spines at y_front facing -Y, none taller than hmax: runs of matching sets,
    stacks lying flat (titles across), books leaning on their neighbour (resting on its top corner, never through it) and
    the odd gap. dfun(xa, xb) caps the depth for a shaped shelf. Returns the number of books."""
    mat = K["atlas"]
    fits = _fits(hmax, pool=pool)
    if not fits:
        return 0
    x = x0 + rnd.uniform(0.0, 0.05)
    xend = x0 + (x1 - x0) * fill
    n = 0
    prev = None           # (right edge, height) of the last upright book
    while x < xend - 0.1:
        roll = rnd.random()
        room = xend - x

        def depth(d, xa, xb):
            dd = min(dmax, d["h"] * rnd.uniform(0.66, 0.8))
            if dfun:
                dd = min(dd, dfun(xa, xb))
            return dd
        if roll < p_set:
            names = [s for s in SETNAMES if any(d["set"] == s for d in fits)]
            if names:
                vols = [d for d in fits if d["set"] == rnd.choice(names)]
                vols.sort(key=lambda d: d["key"])
                dd = depth(vols[0], x, x + 0.3)
                placed = 0
                for d in vols[: rnd.randint(min(3, len(vols)), len(vols))]:
                    if x + d["w"] > xend:
                        break
                    if dfun and dfun(x, x + d["w"]) < 0.3:
                        break
                    dd2 = min(dd, dfun(x, x + d["w"])) if dfun else dd
                    book(f"{prefix}B{n}", d, dd2, T(x + d["w"] / 2, y_front + dd2 / 2, z + 0.003), mat, bottom=False)
                    n += 1
                    placed += 1
                    x += d["w"] + 0.004
                    prev = (x - 0.004, d["h"])
                if placed:
                    continue
        if roll < p_set + p_flat and room > 1.1:
            # a stack lying flat, spines out: book height along x, thickness up
            cand = [d for d in fits if d["h"] < min(room - 0.05, 1.3)]
            if cand:
                nst = rnd.randint(2, 4)
                stack = sorted(rnd.sample(cand, min(nst, len(cand))), key=lambda d: -d["h"])
                zz = z + 0.003
                wide = stack[0]["h"]
                if dfun and dfun(x, x + wide) < 0.45:
                    stack = []
                for d in stack:
                    if zz + d["w"] > z + hmax:
                        break
                    off = rnd.uniform(0.0, wide - d["h"]) if wide > d["h"] else 0.0
                    dd = depth(d, x, x + wide)
                    book(f"{prefix}B{n}", d, dd, T(x + off + d["h"], y_front + dd / 2 + rnd.uniform(0, 0.04), zz + d["w"] / 2) @ RY(-90 * DEG), mat)
                    n += 1
                    zz += d["w"] + 0.002
                if stack:
                    x += wide + rnd.uniform(0.03, 0.08)
                    prev = None
                    continue
        if roll < p_set + p_flat + p_lean and prev is not None:
            # leaning left onto the previous upright book, its bottom-left corner on the shelf
            a = rnd.uniform(9, 17) * DEG
            xn, hn = prev
            cand = [d for d in fits if d["h"] >= hn / math.cos(a) + 0.04 and d["w"] * math.sin(a) + d["h"] * math.cos(a) < hmax - 0.02]
            if cand:
                d = rnd.choice(cand)
                bx = xn + hn * math.tan(a) + 0.006
                if bx + d["w"] * math.cos(a) < xend and not (dfun and dfun(bx - 0.3, bx + d["w"]) < 0.3):
                    dd = depth(d, bx - d["h"] * math.sin(a), bx + d["w"])
                    book(f"{prefix}B{n}", d, dd, T(bx, y_front + dd / 2, z + 0.003) @ RY(-a) @ T(d["w"] / 2), mat)
                    n += 1
                    x = bx + d["w"] * math.cos(a) + rnd.uniform(0.05, 0.3)
                    prev = None
                    continue
        if roll > 1 - p_gap:
            x += rnd.uniform(0.2, 0.5)
            prev = None
            continue
        cand = [d for d in fits if d["w"] <= room and not d["set"]]
        if not cand:
            break
        d = rnd.choice(cand)
        if dfun and dfun(x, x + d["w"]) < 0.3:
            break
        dd = depth(d, x, x + d["w"])
        book(f"{prefix}B{n}", d, dd, T(x + d["w"] / 2, y_front + dd / 2 + rnd.uniform(0, 0.03), z + 0.003), mat, bottom=False)
        n += 1
        x += d["w"] + rnd.uniform(0.002, 0.012)
        prev = (x, d["h"])
    return n


def flat_stack(prefix, x, y, z, count, rnd, K, yaw=0.0, hmax=1.3, jitter=8.0, open_top=None):
    """A pile of books lying on their boards, each turned a little; returns the top."""
    cand = sorted(rnd.sample(_fits(hmax), count), key=lambda d: -d["h"] * d["w"])
    zz = z
    for k, d in enumerate(cand):
        dd = d["h"] * 0.72
        a = yaw + rnd.uniform(-jitter, jitter) * DEG
        # lying on its back board: the spine faces -Y (turned by a), the book's height runs along x
        book(f"{prefix}S{k}", d, dd, T(x, y, zz + d["w"] / 2) @ RZ(a) @ T(d["h"] / 2) @ RY(-90 * DEG), K["atlas"])
        zz += d["w"] + 0.003
    return zz


# ------------------------------------------------------------------ bookcase shells

def pilaster(prefix, x, y, z0, z1, w, K):
    """An ebony pilaster applied to a front edge: a fluted shaft between a brass base and capital, a gilt foil."""
    box(f"{prefix}Shaft", (w, 0.08, z1 - z0 - 0.4), (x, y - 0.04, (z0 + z1) / 2), K["ebony"], bevel=0.02)
    for k in (-1, 1):
        box(f"{prefix}Flute{k}", (0.03, 0.02, z1 - z0 - 0.9), (x + k * w * 0.22, y - 0.088, (z0 + z1) / 2), K["back"], bevel=0.006)
    box(f"{prefix}Base", (w + 0.08, 0.14, 0.2), (x, y - 0.07, z0 + 0.1), K["brass"], bevel=0.025)
    box(f"{prefix}Cap", (w + 0.1, 0.16, 0.2), (x, y - 0.08, z1 - 0.1), K["brass"], bevel=0.03)
    foil(f"{prefix}Foil", x, y - 0.165, z1 - 0.1, 0.06, K["gilt"], lobes=4, thick=0.01)


def case(K, W, D, H, rows, kick=0.5, frieze=0.55, side=0.22, plaque="Cat_HISTORY", crest=True, back=True, both=False, side_panels=True):
    """A dark-oak bookcase, front -Y, its back at +Y = D / 2. Returns the shelf surfaces [(z, hmax), ...]."""
    zk, zt = kick, H - frieze
    pitch = (zt - zk) / rows
    for sx in (-1, 1):
        box(f"Side{sx}", (side, D, zt), (sx * (W / 2 - side / 2), 0, zt / 2), K["oak"], bevel=0.025)
        if side_panels:
            xo = sx * (W / 2 + 0.005)
            tube(f"SidePanel{sx}", [(xo, -D / 2 + 0.22, zk + 0.35), (xo, D / 2 - 0.22, zk + 0.35), (xo, D / 2 - 0.22, zt - 0.35), (xo, -D / 2 + 0.22, zt - 0.35)],
                 0.03, K["ebony"], square=True, closed=True, poly=True)
        pilaster(f"Pil{sx}", sx * (W / 2 - side / 2), -D / 2, zk, zt, side + 0.06, K)
    if back:
        box("Back", (W - 2 * side, 0.08, zt - zk), (0, D / 2 - 0.04, (zk + zt) / 2), K["back"], bevel=0.0)
    box("Kick", (W + 0.06, D + (0.06 if both else 0.03), kick), (0, 0 if both else -0.015, kick / 2), K["ebony"], bevel=0.03)
    out = []
    for i in range(rows):
        zs = zk + i * pitch
        dsh = D - (0.0 if not back else 0.08)
        ysh = 0 if not back else -0.04
        box(f"Shelf{i}", (W - 2 * side, dsh, 0.1), (0, ysh, zs + 0.05), K["oak"], bevel=0.01)
        if i > 0:
            box(f"Lip{i}", (W - 2 * side, 0.05, 0.13), (0, -D / 2 - 0.02, zs + 0.035), K["ebony"], bevel=0.012)
            if both:
                box(f"LipB{i}", (W - 2 * side, 0.05, 0.13), (0, D / 2 + 0.02, zs + 0.035), K["ebony"], bevel=0.012)
        out.append((zs + 0.1, pitch - 0.1 - 0.06))
    box("Ceiling", (W - 2 * side, D - (0.08 if back else 0.0), 0.06), (0, -0.04 if back else 0, zt - 0.03), K["oak"], bevel=0.0)
    if frieze > 0:
        dy = 0.06 if both else 0.03
        box("Frieze", (W + 0.06, D + dy, frieze), (0, 0 if both else -dy / 2, zt + frieze / 2), K["oak"], bevel=0.02)
        ov = 0.25
        dd = D + (2 * ov if both else ov)
        yc = 0 if both else -ov / 2
        box("Mould", (W + 0.32, dd - 0.08, 0.14), (0, yc + (0 if both else 0.04), H + 0.07), K["ebony"], bevel=0.04)
        box("Cap", (W + 0.46, dd, 0.12), (0, yc, H + 0.2), K["oak"], bevel=0.04)
        for f in ((-1, 1) if both else (-1,)):
            s = _mark()
            if plaque:
                pw = min(W * 0.42, 2.6)
                box("PlaqueFrame", (pw + 0.12, 0.04, frieze - 0.12), (0, -D / 2 - dy / 2 - 0.02, zt + frieze / 2), K["gilt"], bevel=0.012)
                plate("Plaque", plaque, pw, frieze - 0.2, 0.03, T(0, -D / 2 - dy / 2 - 0.045, zt + frieze / 2), K["atlas"])
            for sx in (-1, 1):
                foil(f"FriezeFoil{sx}", sx * (W * 0.34), -D / 2 - dy / 2 - 0.01, zt + frieze / 2, 0.14, K["brass"], lobes=4, thick=0.014)
            if crest:
                _gable("Crest", 0, -D / 2 + 0.18, min(1.3, W * 0.22), H + 0.26, H + 1.25, 0.12, K["oak"], K["ebony"], edge=0.035)
                P._quatrefoil("CrestSeal", 0, -D / 2 + 0.1, H + 0.66, 0.16, K["brass"])
                sphere("CrestFinial", 0.07, (0, -D / 2 + 0.18, H + 1.3), K["brass"], seg=10, rings=5)
            if f > 0:
                _xform(s, RZ(math.pi))
    return out


def rows_fill(K, rnd, rows_, W, D, side=0.22, both=False, **kw):
    n = 0
    for i, (z, hm) in enumerate(rows_):
        x0, x1 = -W / 2 + side + 0.04, W / 2 - side - 0.04
        dmax = (D / 2 - 0.18) if both else D - 0.3
        n += fill_row(f"R{i}", x0, x1, z, -D / 2 + 0.12, dmax, hm, rnd, K, **kw)
        if both:
            s = _mark()
            n += fill_row(f"Q{i}", x0, x1, z, -D / 2 + 0.12, dmax, hm, rnd, K, **kw)
            _xform(s, RZ(math.pi))
    return n


# ================================================================== shelving

def lib_shelf_tall(M):
    K = mats(M)
    rnd = random.Random(3001)
    W, D, H = 6.0, 1.7, 10.4
    rows_ = case(K, W, D, H, 7, plaque="Cat_HISTORY")
    rows_fill(K, rnd, rows_, W, D)
    return _dims()


def lib_shelf_arched(M):
    K = mats(M)
    rnd = random.Random(3002)
    W, D, H = 6.0, 1.7, 11.2
    side, kick = 0.22, 0.5
    zs, za = 8.0, H - 0.35           # the arch springs at 8, its point under the cap
    hw = W / 2 - side
    for sx in (-1, 1):
        box(f"Side{sx}", (side, D, H), (sx * (W / 2 - side / 2), 0, H / 2), K["oak"], bevel=0.025)
        pilaster(f"Pil{sx}", sx * (W / 2 - side / 2), -D / 2, kick, zs, side + 0.06, K)
        _pinnacle(f"Pin{sx}", sx * (W / 2 - side / 2), -D / 2 + 0.2, H + 0.12, 1.4, K["oak"])
        xo = sx * (W / 2 + 0.005)
        tube(f"SidePanel{sx}", [(xo, -D / 2 + 0.22, kick + 0.35), (xo, D / 2 - 0.22, kick + 0.35), (xo, D / 2 - 0.22, H - 0.5), (xo, -D / 2 + 0.22, H - 0.5)],
             0.03, K["ebony"], square=True, closed=True, poly=True)
    box("Back", (W - 2 * side, 0.08, H - kick), (0, D / 2 - 0.04, (kick + H) / 2), K["back"], bevel=0.0)
    box("Kick", (W + 0.06, D + 0.03, kick), (0, -0.015, kick / 2), K["ebony"], bevel=0.03)
    box("Ceiling", (W - 2 * side, D - 0.08, 0.1), (0, -0.04, H - 0.05), K["oak"], bevel=0.0)
    box("Cap", (W + 0.46, D + 0.25, 0.14), (0, -0.125, H + 0.07), K["ebony"], bevel=0.04)
    # the arched front: two carved spandrels from the springing to the cap
    arc = WS.pointed(hw, zs, za, 14)
    half = len(arc) // 2
    left = arc[: half + 1]
    yf = -D / 2 - 0.03
    for sx in (-1, 1):
        poly = [(-W / 2 + 0.0, zs), (-hw, zs)] + left[1:] + [(0.0, H), (-W / 2, H)]
        poly = [(sx * x, z) for x, z in poly]
        B20.tprism(f"Spandrel{sx}", WS.ccw(poly), yf, 0.12, K["oak"])
        tube(f"ArchMould{sx}", [(sx * x, yf - 0.07, z) for x, z in left], 0.035, K["ebony"], square=True, poly=True)
        foil(f"SpandrelFoil{sx}", sx * (W / 2 - 0.62), yf - 0.065, H - 0.62, 0.22, K["gilt"], lobes=3, thick=0.016)
    box("SpringRail", (W - 2 * side, 0.12, 0.3), (0, yf, zs - 0.15), K["ebony"], bevel=0.02)
    plate("Plaque", "Cat_ASTRONOMY", 2.2, 0.2, 0.03, T(0, yf - 0.075, zs - 0.15), K["atlas"])
    # the niche: blind tracery on the back, a gilt quatrefoil
    tracery("Niche", 0, D / 2 - 0.08, hw * 0.62, zs + 0.15, zs + 1.2, za - 0.35, K["ebony"], recess=K["back"], thick=0.03)
    P._quatrefoil("NicheSeal", 0, D / 2 - 0.16, za - 0.9, 0.2, K["gilt"])
    sphere("ApexFinial", 0.09, (0, yf, H + 0.23), K["brass"], seg=10, rings=5)
    rows = 5
    pitch = (zs - 0.3 - kick) / rows
    rows_ = []
    for i in range(rows + 1):
        z = kick + i * pitch
        box(f"Shelf{i}", (W - 2 * side, D - 0.08, 0.1), (0, -0.04, z + 0.05), K["oak"], bevel=0.01)
        if 0 < i < rows:
            box(f"Lip{i}", (W - 2 * side, 0.05, 0.13), (0, -D / 2 - 0.02, z + 0.035), K["ebony"], bevel=0.012)
        if i < rows:
            rows_.append((z + 0.1, pitch - 0.16))
    rows_fill(K, rnd, rows_, W, D)
    return _dims()


def lib_shelf_corner(M):
    K = mats(M)
    rnd = random.Random(3003)
    A, F, H = 2.2, 0.7, 9.4          # the front runs x -A..A at y = -F; the backs meet at (0, A - F)
    yb = A - F
    kick, zt = 0.5, H - 0.5
    # the two backs, at 45 degrees
    for sx in (-1, 1):
        L = math.hypot(A, A)
        mid = (sx * A / 2, (yb - F) / 2)
        box(f"Back{sx}", (L, 0.1, zt), (mid[0], mid[1], zt / 2), K["back"], bevel=0.0, rot=(0, 0, sx * -45 * DEG))
        pilaster(f"Pil{sx}", sx * (A - 0.13), -F, kick, zt, 0.3, K)
        box(f"Post{sx}", (0.26, 0.26, zt), (sx * (A - 0.13), -F + 0.13, zt / 2), K["oak"], bevel=0.02)
    tri = lambda inset: WS.ccw([(-A + inset * 2.4, -F + inset), (A - inset * 2.4, -F + inset), (0, yb - inset * 1.4)])
    prism("Kick", tri(0.0), 0, kick, K["ebony"], plane="XY", bevel=0.02)
    rows = 6
    pitch = (zt - kick) / rows
    rows_ = []
    for i in range(rows + 1):
        z = kick + i * pitch
        prism(f"Shelf{i}", tri(0.06), z, 0.1, K["oak"], plane="XY", bevel=0.008)
        if 0 < i < rows:
            box(f"Lip{i}", (2 * A - 0.5, 0.05, 0.13), (0, -F - 0.02, z + 0.035), K["ebony"], bevel=0.012)
        if i < rows:
            rows_.append((z + 0.1, pitch - 0.16))
    prism("Frieze", tri(-0.02), zt, 0.5, K["oak"], plane="XY", bevel=0.02)
    prism("Cap", WS.ccw([(-A - 0.28, -F - 0.22), (A + 0.28, -F - 0.22), (0, yb + 0.0)]), H, 0.14, K["ebony"], plane="XY", bevel=0.03)
    plate("Plaque", "Cat_POETRY", 2.0, 0.32, 0.03, T(0, -F - 0.035, zt + 0.25), K["atlas"])
    _gable("Crest", 0, -F + 0.18, 0.9, H + 0.14, H + 1.0, 0.12, K["oak"], K["ebony"], edge=0.035)
    P._quatrefoil("CrestSeal", 0, -F + 0.1, H + 0.5, 0.13, K["brass"])

    def dfun(xa, xb):
        return (A - max(abs(xa), abs(xb))) - 0.16
    for i, (z, hm) in enumerate(rows_):
        fill_row(f"R{i}", -A + 0.5, A - 0.5, z, -F + 0.1, 1.2, hm, rnd, K, dfun=dfun, p_flat=0.12)
    return _dims()


def lib_shelf_double(M):
    K = mats(M)
    rnd = random.Random(3004)
    W, D, H = 6.0, 2.8, 8.4
    rows_ = case(K, W, D, H, 5, back=False, both=True, plaque="Cat_LANGUAGES", crest=True, side_panels=False)
    box("Divider", (W - 0.44, 0.08, H - 1.05), (0, 0, 0.5 + (H - 1.05) / 2), K["back"], bevel=0.0)
    for sx in (-1, 1):
        s = _mark()
        for k, z0 in enumerate((1.0, 4.6)):
            _panel(f"End{sx}{k}", 0, 0, z0, D - 0.7, 3.0, K["ebony"], thick=0.035)
        B20._side(s, sx * (W / 2 + 0.006), sx)
    # the back face's pilasters: built at the front and turned round
    s = _mark()
    for sx in (-1, 1):
        pilaster(f"PilR{sx}", sx * (W / 2 - 0.11), -D / 2, 0.5, H - 0.55, 0.28, K)
    _xform(s, RZ(math.pi))
    rows_fill(K, rnd, rows_, W, D, both=True)
    return _dims()


def lib_shelf_ladder(M):
    K = mats(M)
    rnd = random.Random(3005)
    W, D, H = 7.0, 1.7, 12.6
    rows_ = case(K, W, D, H, 8, plaque="Cat_FOLKLORE")
    rows_fill(K, rnd, rows_, W, D)
    zr, yr = 9.6, -D / 2 - 0.5
    tube("Rail", [(-W / 2 + 0.1, yr, zr), (W / 2 - 0.1, yr, zr)], 0.05, K["brass"], poly=True)
    for k, x in enumerate((-W / 2 + 0.3, 0.0, W / 2 - 0.3)):
        tube(f"RailArm{k}", [(x, -D / 2 - 0.08, zr), (x, yr, zr)], 0.035, K["brass"], poly=True)
        cyl(f"RailRose{k}", 0.1, 0.05, (x, -D / 2 - 0.115, zr), K["brass"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
        sphere(f"RailKnob{k}", 0.075, (x, yr, zr), K["brass"], seg=10, rings=5)
    for sx in (-1, 1):
        sphere(f"RailEnd{sx}", 0.08, (sx * (W / 2 - 0.08), yr, zr), K["brass"], seg=10, rings=5)
    # the ladder, hooked on the rail and rolling on the floor
    set_group("Ladder")
    lx, lw = -1.4, 1.7
    top = Vector((0, yr - 0.08, zr - 0.15))
    bot = Vector((0, yr - 2.7, 0.24))
    for sx in (-1, 1):
        a, b = top + Vector((lx + sx * lw / 2, 0, 0)), bot + Vector((lx + sx * lw / 2, 0, 0))
        tube(f"Stile{sx}", [tuple(b), tuple(a)], 0.07, K["oakmid"], square=True, poly=True)
        tube(f"Hook{sx}", [tuple(a), (a.x, a.y, a.z + 0.32), (a.x, yr + 0.1, zr + 0.2), (a.x, yr + 0.12, zr - 0.08)], 0.03, K["brass"])
        cyl(f"Wheel{sx}", 0.2, 0.08, (b.x, b.y - 0.05, 0.2), K["brass"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.01)
        box(f"Fork{sx}", (0.16, 0.32, 0.12), (b.x, b.y, 0.33), K["iron"], bevel=0.02)
    nr = 10
    for k in range(1, nr + 1):
        t = k / (nr + 1)
        p = bot.lerp(top, t)
        box(f"Rung{k}", (lw - 0.08, 0.32, 0.06), (lx, p.y + 0.02, p.z), K["oakmid"], bevel=0.015)
        box(f"Tread{k}", (lw - 0.16, 0.24, 0.012), (lx, p.y + 0.02, p.z + 0.035), K["crimson"], bevel=0.0)
    set_group("Main")
    return _dims()


def lib_shelf_half(M):
    K = mats(M)
    rnd = random.Random(3006)
    W, D, H = 5.0, 1.5, 4.1
    rows_ = case(K, W, D, H - 0.2, 2, kick=0.45, frieze=0.0, plaque=None, crest=False)
    box("Top", (W + 0.3, D + 0.18, 0.12), (0, -0.09, H - 0.14), K["oak"], bevel=0.035)
    box("TopMould", (W + 0.14, D + 0.08, 0.1), (0, -0.04, H - 0.25), K["ebony"], bevel=0.03)
    for i, (z, hm) in enumerate(rows_):
        fill_row(f"R{i}", -W / 2 + 0.26, W / 2 - 0.26, z, -D / 2 + 0.12, D - 0.3, hm, rnd, K)
    zt = H - 0.08
    # on top: brass bookends round a short row, a pile, a chamber candle
    for k, x in enumerate((-2.15, -0.95)):
        box(f"BookendBase{k}", (0.16, 0.6, 0.03), (x, -0.1, zt + 0.015), K["brass"], bevel=0.008)
        B20.tprism(f"Bookend{k}", WS.ccw([(-0.06, 0), (0.06, 0), (0.06, 0.55), (0.0, 0.66), (-0.06, 0.55)]), -0.1, 0.5, K["brass"], plane="YZ")
    s = _mark()
    fill_row("Top", -2.08, -1.02, zt + 0.03, -0.42, 0.6, 1.05, rnd, K, p_set=0.0, p_flat=0.0, p_lean=0.0, p_gap=0.0)
    _xform(s, Matrix.Identity(4))
    flat_stack("Pile", 0.65, -0.05, zt, 3, rnd, K, yaw=8 * DEG)
    lathe("Chamber", [(0, 0), (0.32, 0), (0.33, 0.03), (0.3, 0.05), (0.07, 0.06), (0.06, 0.2), (0.09, 0.22), (0.07, 0.25), (0, 0.25)], K["brass"], seg=24,
          loc=(1.75, -0.1, zt))
    tube("ChamberHandle", [(1.75 + 0.3, -0.1, zt + 0.04), (2.17, -0.1, zt + 0.1), (2.12, -0.1, zt + 0.2)], 0.018, K["brass"])
    wick = (1.75, -0.1, zt + 0.25 + 0.42)
    cyl("Candle", 0.055, 0.42, (1.75, -0.1, zt + 0.25 + 0.21), K["wax"], verts=14, bevel=0.01)
    sphere("Drip", 0.022, (1.80, -0.1, zt + 0.55), K["wax"], seg=6, rings=4, scale=(1, 1, 2.4))
    set_group("Glow")
    flame("Flame", wick, h=0.18)
    set_group("Main")
    return _dims()


def shelf_end_cap(M):
    K = mats(M)
    W, D, H = 2.8, 0.42, 8.6
    box("Plinth", (W + 0.1, D + 0.06, 0.5), (0, 0.0, 0.25), K["ebony"], bevel=0.03)
    box("Panel", (W, D, H - 0.5), (0, 0, 0.5 + (H - 0.5) / 2), K["oak"], bevel=0.03)
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.22, 0.06, H - 1.2), (sx * (W / 2 - 0.15), -D / 2 - 0.03, 0.55 + (H - 1.2) / 2), K["ebony"], bevel=0.015)
        _pinnacle(f"Pin{sx}", sx * (W / 2 - 0.15), 0, H, 1.2, K["oak"])
    tracery("Lancets", 0, -D / 2, W / 2 - 0.42, 0.9, 4.6, 6.2, K["ebony"], recess=K["back"], thick=0.03)
    _gable("Gable", 0, 0, W / 2 - 0.3, H, H + 1.4, 0.22, K["oak"], K["ebony"], edge=0.04)
    P._quatrefoil("GableSeal", 0, -0.13, H + 0.5, 0.2, K["brass"])
    sphere("Finial", 0.09, (0, 0, H + 1.46), K["brass"], seg=10, rings=5)
    box("PlaqueFrame", (2.0, 0.05, 0.5), (0, -D / 2 - 0.025, 7.05), K["gilt"], bevel=0.015)
    plate("Plaque", "Cat_POETRY", 1.84, 0.4, 0.03, T(0, -D / 2 - 0.06, 7.05), K["atlas"])
    # a brass card holder low down with the shelf card
    box("CardHolder", (0.8, 0.04, 0.54), (0, -D / 2 - 0.02, 0.85), K["brass"], bevel=0.01)
    plate("Card", "Card", 0.7, 0.44, 0.012, T(0, -D / 2 - 0.046, 0.85), K["atlas"], edge="cardwhite")
    return _dims()


def forbidden_cage(M):
    K = mats(M)
    rnd = random.Random(3008)
    W, D, H = 6.0, 1.7, 9.0
    dark = [d for d in DESIGNS if d["leather"] in ("black", "plum", "oxblood", "slate", "ink")]
    rows_ = case(K, W, D, H, 6, plaque="Plaque_RESTRICTED", crest=False)
    for i, (z, hm) in enumerate(rows_):
        fill_row(f"R{i}", -W / 2 + 0.26, W / 2 - 0.26, z, -D / 2 + 0.12, D - 0.3, hm, rnd, K, pool=dark, p_set=0.1)
    # the cage: a frame in front and round the sides, bars with spear tips, two doors chained shut
    ir, cg = K["iron"], 0.5
    yf = -D / 2 - cg
    xL, xR = -W / 2 - 0.2, W / 2 + 0.2
    zc = H - 0.75
    for sx, x in ((-1, xL), (1, xR)):
        tube(f"CornerF{sx}", [(x, yf, 0.0), (x, yf, zc + 0.2)], 0.06, ir, square=True, poly=True)
        tube(f"CornerB{sx}", [(x, D / 2 - 0.06, 0.0), (x, D / 2 - 0.06, zc + 0.2)], 0.05, ir, square=True, poly=True)
        for j, z in enumerate((0.08, zc)):
            tube(f"SideRail{sx}{j}", [(x, yf, z), (x, D / 2 - 0.06, z)], 0.04, ir, square=True, poly=True)
        n = 5
        for k in range(1, n):
            y = yf + (D / 2 - 0.06 - yf) * k / n
            tube(f"SideBar{sx}{k}", [(x, y, 0.08), (x, y, zc)], 0.022, ir, poly=True)
    for j, z in enumerate((0.08, zc, zc + 0.2)):
        tube(f"FrontRail{j}", [(xL, yf, z), (xR, yf, z)], 0.045, ir, square=True, poly=True)
    tube("DoorJamb", [(0, yf - 0.02, 0.08), (0, yf - 0.02, zc)], 0.05, ir, square=True, poly=True)
    nb = 16
    for k in range(nb + 1):
        x = xL + 0.18 + (xR - xL - 0.36) * k / nb
        if abs(x) < 0.12:
            continue
        tube(f"Bar{k}", [(x, yf, 0.08), (x, yf, zc + 0.2)], 0.024, ir, poly=True)
        cone(f"Spear{k}", 0.05, 0.0, 0.26, (x, yf, zc + 0.33), ir, verts=4)
    for sx in (-1, 1):            # each door's lock rail and diagonal brace, its hinges on the corner post
        x0, x1 = (xL + 0.1, -0.1) if sx < 0 else (0.1, xR - 0.1)
        tube(f"DoorRail{sx}", [(x0, yf - 0.03, 3.2), (x1, yf - 0.03, 3.2)], 0.035, ir, square=True, poly=True)
        tube(f"Brace{sx}", [(x0, yf - 0.03, 0.2), (x1, yf - 0.03, 3.1)], 0.03, ir, square=True, poly=True)
        for j, z in enumerate((1.2, 6.2)):
            cyl(f"Hinge{sx}{j}", 0.075, 0.36, ((xL if sx < 0 else xR), yf, z), ir, verts=10, bevel=0.01)
    # chains crossing the doors, and the padlock where they meet
    pc = Vector((0, yf - 0.16, 3.3))
    for j, a in enumerate(((xL + 0.3, yf - 0.07, 5.0), (xR - 0.3, yf - 0.07, 5.0), (xL + 0.3, yf - 0.07, 1.6), (xR - 0.3, yf - 0.07, 1.6))):
        chain(f"Chain{j}", [a, pc + Vector((0, 0, 0.08))], ir, r=0.085, thick=0.022, sag=0.1)
    box("Padlock", (0.5, 0.2, 0.42), (pc.x, pc.y - 0.02, pc.z - 0.25), K["brass"], bevel=0.05)
    tube("Shackle", [(pc.x - 0.14, pc.y - 0.02, pc.z - 0.05), (pc.x - 0.14, pc.y - 0.02, pc.z + 0.12), (pc.x, pc.y - 0.02, pc.z + 0.25),
                     (pc.x + 0.14, pc.y - 0.02, pc.z + 0.12), (pc.x + 0.14, pc.y - 0.02, pc.z - 0.05)], 0.035, K["steel"])
    box("Keyhole", (0.05, 0.02, 0.12), (pc.x, pc.y - 0.125, pc.z - 0.27), K["ink"], bevel=0.0)
    tube("TagString", [(pc.x + 0.1, pc.y - 0.12, pc.z - 0.42), (pc.x + 0.22, pc.y - 0.16, pc.z - 0.72)], 0.006, K["paper"], poly=True)
    plate("Tag", "Plaque_FORBIDDEN", 0.62, 0.17, 0.01, T(pc.x + 0.26, pc.y - 0.17, pc.z - 0.82) @ RZ(-0.12) @ RY(0.15), K["atlas"], edge="bone")
    return _dims()


def chained_bookcase(M):
    K = mats(M)
    rnd = random.Random(3009)
    W = 5.2
    # the press: a case set back (its front at y = -0.3), a sloping reading desk across the front below the first shelf
    s = _mark()
    rows_ = case(K, W, 1.5, 7.6, 3, kick=3.1, frieze=0.5, plaque="Cat_ALCHEMY", crest=True)
    _xform(s, T(0, 0.45, 0))
    yfc = -0.3
    yc, zc, half, ang = -0.878, 2.9, 0.6, 24 * DEG
    desk = T(0, yc, zc) @ RX(-ang)
    box("Desk", (W - 0.44, 2 * half, 0.1), (0, yc, zc), K["oak"], bevel=0.02, rot=(-ang, 0, 0))
    yfe, zfe = yc - half * math.cos(ang), zc - half * math.sin(ang)
    for sx in (-1, 1):
        prof = [(-1.5, 0.0), (yfc, 0.0), (yfc, zc + half * math.sin(ang) + 0.12), (yfe - 0.02, zfe - 0.05), (-1.5, zfe - 0.05)]
        B20.tprism(f"Cheek{sx}", WS.ccw(prof), sx * (W / 2 - 0.11), 0.22, K["oak"], plane="YZ")
        s = _mark()
        _panel(f"CheekPanel{sx}", -0.95 * sx, 0, 0.5, 0.9, 1.7, K["ebony"], thick=0.03)
        B20._side(s, sx * (W / 2 + 0.002), sx)
    box("DeskFront", (W - 0.44, 0.12, zfe - 0.04), (0, -1.36, (zfe - 0.04) / 2), K["oak"], bevel=0.02)
    for k, cx in enumerate((-1.2, 1.2)):
        tracery(f"DeskTr{k}", cx, -1.42, 0.8, 0.35, 1.5, 2.25, K["ebony"], recess=K["back"], thick=0.025)
    s = _mark()
    box("DeskLedge", (W - 0.6, 0.08, 0.12), (0, -half, 0.1), K["ebony"], bevel=0.015)
    _xform(s, desk)
    for i, (z, hm) in enumerate(rows_):
        fill_row(f"R{i}", -W / 2 + 0.26, W / 2 - 0.26, z, yfc + 0.12, 1.0, hm, rnd, K, p_flat=0.0, p_lean=0.0, p_set=0.3)
    # the chains: from the foot of every other book's spine, over the shelf's lip, to an iron rod in front of it
    bpy.context.view_layer.update()
    books = [o for o in P.PARTS if o.name.startswith("R") and "B" in o.name]
    for i, (z, hm) in enumerate(rows_):
        tube(f"Rod{i}", [(-W / 2 + 0.25, yfc - 0.07, z - 0.06), (W / 2 - 0.25, yfc - 0.07, z - 0.06)], 0.025, K["iron"], poly=True)
    for k, ob in enumerate(books):
        if k % 2:
            continue
        c = ob.matrix_world.translation
        box(f"Clasp{k}", (0.06, 0.02, 0.09), (c.x, yfc + 0.11, c.z + 0.14), K["brass"], bevel=0.005)
        chain(f"BookChain{k}", [(c.x, yfc + 0.09, c.z + 0.12), (c.x, yfc - 0.02, c.z + 0.07), (c.x, yfc - 0.07, c.z - 0.04)], K["iron"], r=0.04, thick=0.011)
    # the open book on the desk, chained to the ledge
    s = _mark()
    open_book("Desk", "Pages_Rules", 1.9, 1.05, Matrix.Identity(4), M, K, cover="crimson")
    _xform(s, desk @ T(0, 0, 0.05))
    a = desk @ Vector((0.95, -0.5, 0.08))
    chain("DeskChain", [a, (1.25, yfe - 0.05, zfe - 0.1), (1.4, yfe - 0.04, zfe - 0.45)], K["iron"], r=0.05, thick=0.013)
    return _dims()


# ================================================================== furniture

def _lamp_banker(prefix, x, y, z, K, scale=1.0, yaw=0.0):
    """A banker's lamp built at (x, y, z): a brass foot and post, a green glass shade; returns the bulb position."""
    s = _mark()
    S = scale
    box(f"{prefix}Foot", (0.9 * S, 0.5 * S, 0.08 * S), (0, 0, 0.04 * S), K["brass"], bevel=0.03 * S)
    box(f"{prefix}Foot2", (0.7 * S, 0.36 * S, 0.06 * S), (0, 0, 0.11 * S), K["brass"], bevel=0.025 * S)
    tube(f"{prefix}Post", [(0, 0.08 * S, 0.13 * S), (0, 0.08 * S, 0.95 * S)], 0.035 * S, K["brass"], poly=True)
    tube(f"{prefix}Yoke", [(-0.42 * S, 0.0, 0.95 * S), (-0.42 * S, 0.08 * S, 1.02 * S), (0.42 * S, 0.08 * S, 1.02 * S), (0.42 * S, 0.0, 0.95 * S)], 0.022 * S,
         K["brass"], poly=True)
    # the shade: a half-cylinder shell along X, tilted toward the reader
    rows = []
    for i in range(9):
        a = math.pi * i / 8
        rows.append([Vector((xx * S, -math.cos(a) * 0.3 * S, 0.78 * S + math.sin(a) * 0.3 * S)) for xx in (-0.45, 0.45)])
    rows = [[r[0], r[1]] for r in rows]
    me = bpy.data.meshes.new(f"{prefix}Shade")
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rows]
    for a, b in zip(vs, vs[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"{prefix}Shade", me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, K["green"], 0)
    _solid(ob, 0.03 * S)
    for sx in (-1, 1):
        B20.tprism(f"{prefix}ShadeEnd{sx}", WS.ccw([(math.cos(math.pi * i / 8) * -0.3 * S, 0.78 * S + math.sin(math.pi * i / 8) * 0.3 * S) for i in range(9)]),
                   sx * 0.45 * S, 0.02 * S, K["brass"], plane="YZ")
    tube(f"{prefix}Chain", [(0.2 * S, -0.1 * S, 0.76 * S), (0.2 * S, -0.12 * S, 0.5 * S)], 0.008 * S, K["brass"], poly=True)
    sphere(f"{prefix}Pull", 0.03 * S, (0.2 * S, -0.12 * S, 0.48 * S), K["brass"], seg=8, rings=4)
    _xform(s, T(x, y, z) @ RZ(yaw))
    return Vector((x, y, z + 0.86 * S))


def _bulb(name, p, K, r=0.09, scale=(1.6, 1, 1)):
    sphere(name, r, tuple(p), K["paper"], seg=10, rings=6, scale=scale)


def reading_table_long(M):
    K = mats(M)
    rnd = random.Random(3010)
    L_, W, H = 12.0, 4.2, 2.55
    box("Top", (L_, W, 0.14), (0, 0, H - 0.07), K["oak"], bevel=0.04)
    box("Inset", (L_ - 0.7, W - 0.7, 0.012), (0, 0, H + 0.004), K["crimson"], bevel=0.0)
    box("Apron", (L_ - 0.8, W - 0.8, 0.3), (0, 0, H - 0.29), K["ebony"], bevel=0.02)
    hw = W / 2 - 0.82
    for k, x in enumerate((-4.6, 0.0, 4.6)):
        for sy in (-1, 1):
            box(f"Post{k}{sy}", (0.34, 0.34, H - 0.5), (x, sy * (W / 2 - 0.65), (H - 0.5) / 2 + 0.08), K["oak"], bevel=0.04)
        box(f"Foot{k}", (0.46, W - 0.5, 0.18), (x, 0, 0.09), K["ebony"], bevel=0.04)
        arch = WS.pointed(hw, H - 1.3, H - 0.66, 8)
        poly = [(-hw, H - 0.44), (hw, H - 0.44)] + list(reversed(arch))
        B20.tprism(f"Brace{k}", WS.ccw(poly), x, 0.16, K["oak"], plane="YZ")
    tube("Stretcher", [(-4.6, 0, 0.55), (4.6, 0, 0.55)], 0.1, K["oak"], square=True, poly=True)
    # the raised book rail down the middle, with two lamps on it
    box("Rail", (L_ - 2.4, 0.42, 0.34), (0, 0, H + 0.17), K["oak"], bevel=0.03)
    box("RailCap", (L_ - 2.3, 0.5, 0.06), (0, 0, H + 0.37), K["ebony"], bevel=0.02)
    bulbs = [_lamp_banker(f"Lamp{sx}", sx * 3.0, 0.0, H + 0.4, K, yaw=0.0) for sx in (-1, 1)]
    s = _mark()
    open_book("BookA", "Pages_Moon", 1.8, 1.2, Matrix.Identity(4), M, K, cover="crimson")
    _xform(s, T(-3.0, -1.25, H + 0.01) @ RZ(4 * DEG))
    s = _mark()
    open_book("BookB", "Pages_Raven", 1.7, 1.15, Matrix.Identity(4), M, K, cover="ebony")
    _xform(s, T(2.6, 1.25, H + 0.01) @ RZ(math.pi - 6 * DEG))
    flat_stack("Pile", 0.5, -1.05, H + 0.01, 4, rnd, K, yaw=-6 * DEG)
    lathe("Inkwell", [(0, 0), (0.12, 0), (0.13, 0.02), (0.13, 0.12), (0.09, 0.16), (0.05, 0.17), (0.05, 0.2), (0, 0.2)], K["ink"], seg=20,
          loc=(4.7, -1.2, H + 0.01))
    hoop("InkCollar", (4.7, -1.2, H + 0.19), 0.052, "Z", K["brass"], thick=0.012)
    quill = flat("Quill", (0.88, 0.86, 0.8), 0.7, wear=0.1)
    tube("QuillShaft", [(4.7, -1.2, H + 0.12), (4.82, -1.13, H + 0.45), (4.98, -1.03, H + 0.8)], 0.009, quill)
    strip("QuillVane", [(4.75, -1.17, H + 0.3), (4.86, -1.1, H + 0.58), (4.97, -1.03, H + 0.8)], 0.1, (0.6, -0.8, 0), quill, thick=0.006)
    set_group("Glow")
    for k, b in enumerate(bulbs):
        _bulb(f"Bulb{k}", b, K, r=0.08, scale=(3.0, 1.0, 1.0))
    set_group("Main")
    return _dims()


def reading_table_round(M):
    K = mats(M)
    rnd = random.Random(3011)
    R, H = 2.5, 2.55
    cyl("Top", R, 0.14, (0, 0, H - 0.07), K["oak"], verts=48, bevel=0.04)
    cyl("Inset", R - 0.38, 0.012, (0, 0, H + 0.004), K["crimson"], verts=48, bevel=0.0)
    hoop("Edge", (0, 0, H - 0.1), R + 0.005, "Z", K["ebony"], thick=0.04)
    cyl("Apron", R - 0.45, 0.3, (0, 0, H - 0.29), K["ebony"], verts=32, bevel=0.02)
    lathe("Pedestal", [(0, 0.5), (0.42, 0.5), (0.48, 0.62), (0.3, 0.8), (0.22, 1.1), (0.34, 1.4), (0.34, 1.6), (0.2, 1.85), (0.24, 2.05), (0.4, 2.1),
                       (0.4, 2.12), (0, 2.12)], K["oak"], seg=32, flute=(16, 0.06))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        pts = [(0.3, 0.75), (0.8, 0.45), (1.25, 0.16), (1.5, 0.22), (1.48, 0.42), (1.32, 0.4)]
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in pts], 0.1, K["oak"], square=True)
        sphere(f"Toe{k}", 0.14, (c * 1.34, s_ * 1.34, 0.12), K["brass"], seg=10, rings=5, scale=(1, 1, 0.85))
    flat_stack("Pile", -0.9, 0.6, H + 0.01, 5, rnd, K, yaw=30 * DEG)
    s = _mark()
    open_book("Open", "Pages_Rules", 1.7, 1.15, Matrix.Identity(4), M, K, cover="crimson")
    _xform(s, T(0.55, -0.6, H + 0.01) @ RZ(-12 * DEG))
    # a magnifying glass lying by the book
    hoop("MagRim", (1.6, 0.7, H + 0.05), 0.24, "Z", K["brass"], thick=0.03)
    cyl("MagLens", 0.23, 0.02, (1.6, 0.7, H + 0.05), K["glass"], verts=24, bevel=0.0)
    tube("MagHandle", [(1.6 + 0.26, 0.7 - 0.12, H + 0.05), (1.6 + 0.75, 0.7 - 0.38, H + 0.05)], 0.035, K["ebony"], poly=True)
    return _dims()


def study_carrel(M):
    K = mats(M)
    rnd = random.Random(3012)
    W, D, H, T_ = 4.8, 2.8, 5.2, 2.55
    for sx in (-1, 1):
        prof = [(-D / 2, 0), (D / 2, 0), (D / 2, H + 0.6), (D / 2 - 0.4, H + 0.6), (-D / 2 + 0.6, H - 0.1), (-D / 2 + 0.25, T_ + 0.6), (-D / 2, T_ + 0.4)]
        B20.tprism(f"Side{sx}", WS.ccw(prof), sx * (W / 2 - 0.08), 0.16, K["oak"], plane="YZ")
        s = _mark()
        foil(f"SideFoil{sx}", 0.0, 0, 3.4, 0.35, K["ebony"], lobes=4, thick=0.025)
        B20._side(s, sx * (W / 2 + 0.002), sx)
        s = _mark()
        foil(f"SideFoilIn{sx}", 0.0, 0, 3.4, 0.35, K["ebony"], lobes=4, thick=0.025)
        B20._side(s, sx * (W / 2 - 0.162), -sx)
    box("Back", (W - 0.32, 0.12, H), (0, D / 2 - 0.06, H / 2), K["back"], bevel=0.01)
    box("Desk", (W - 0.32, D - 0.12, 0.12), (0, -0.06, T_ - 0.06), K["oak"], bevel=0.03)
    box("DeskInset", (W - 0.9, D - 0.8, 0.01), (0, -0.1, T_ + 0.003), K["crimson"], bevel=0.0)
    box("DeskEdge", (W - 0.32, 0.06, 0.2), (0, -D / 2 + 0.03, T_ - 0.1), K["ebony"], bevel=0.015)
    box("Modesty", (W - 0.32, 0.08, T_ - 0.6), (0, D / 2 - 0.5, (T_ - 0.6) / 2 + 0.3), K["oak"], bevel=0.01)
    zsh = 4.2
    box("Shelf", (W - 0.32, 0.9, 0.1), (0, D / 2 - 0.57, zsh), K["oak"], bevel=0.015)
    box("ShelfLip", (W - 0.32, 0.05, 0.13), (0, D / 2 - 1.04, zsh - 0.015), K["ebony"], bevel=0.012)
    fill_row("Shelf", -W / 2 + 0.3, W / 2 - 0.3, zsh + 0.05, D / 2 - 0.98, 0.78, H - zsh - 0.12, rnd, K, p_flat=0.08, p_lean=0.08)
    box("Cap", (W + 0.1, 0.5, 0.1), (0, D / 2 - 0.25, H + 0.05), K["ebony"], bevel=0.02)
    plate("Quiet", "Plaque_QUIET", 1.5, 0.37, 0.015, T(0, D / 2 - 0.125, 3.3), K["atlas"], edge="bone")
    for sx in (-1, 1):
        cyl(f"Pin{sx}", 0.03, 0.02, (sx * 0.68, D / 2 - 0.14, 3.42), K["brass"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)
    # the lamp under the shelf: a brass hood on a short stem
    ly = D / 2 - 0.6
    lathe("LampHood", [(0, 0.0), (0.24, -0.02), (0.25, -0.03), (0.2, 0.08), (0.06, 0.12), (0.05, 0.2), (0, 0.2)], K["brass"], seg=24, loc=(1.2, ly, zsh - 0.42))
    tube("LampArm", [(1.2, ly, zsh - 0.22), (1.2, ly, zsh - 0.04)], 0.02, K["brass"], poly=True)
    flat_stack("Pile", -1.0, -0.4, T_ + 0.01, 3, rnd, K, yaw=-10 * DEG)
    set_group("Glow")
    _bulb("Bulb", (1.2, ly, zsh - 0.46), K, r=0.08, scale=(1, 1, 0.8))
    set_group("Main")
    return _dims()


def library_chair(M):
    K = mats(M)
    W, D, ST = 2.3, 2.0, 1.55
    zs = ST - 0.1
    box("Seat", (W, D, 0.12), (0, 0, zs - 0.06), K["oak"], bevel=0.03)
    box("Cushion", (W - 0.16, D - 0.2, 0.1), (0, -0.03, zs + 0.05), K["crimson"], bevel=0.04)
    box("Apron", (W - 0.2, D - 0.2, 0.22), (0, 0, zs - 0.23), K["ebony"], bevel=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.17), sy * (D / 2 - 0.17)
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.1, 0), (0.11, 0.08), (0.08, 0.3), (0.11, 0.55), (0.09, 0.8), (0.12, 1.12), (0.12, zs - 0.12), (0, zs - 0.12)],
                  K["oak"], seg=14, loc=(x, y, 0))
    for sx in (-1, 1):
        tube(f"Stretch{sx}", [(sx * (W / 2 - 0.17), -D / 2 + 0.17, 0.45), (sx * (W / 2 - 0.17), D / 2 - 0.17, 0.45)], 0.04, K["oak"], poly=True)
    tube("StretchX", [(-W / 2 + 0.17, 0, 0.45), (W / 2 - 0.17, 0, 0.45)], 0.04, K["oak"], poly=True)
    # the back: two posts and a pointed back panel with a carved quatrefoil
    yb = D / 2 - 0.12
    for sx in (-1, 1):
        box(f"BackPost{sx}", (0.16, 0.16, 4.6 - zs), (sx * (W / 2 - 0.12), yb, zs + (4.6 - zs) / 2), K["oak"], bevel=0.03)
        sphere(f"PostFinial{sx}", 0.1, (sx * (W / 2 - 0.12), yb, 4.68), K["brass"], seg=10, rings=5)
    hw = W / 2 - 0.2
    B20.tprism("BackPanel", WS.ccw(WS.arch(hw, zs + 0.3, 3.7, 4.55, n=10)), yb, 0.08, K["oak"])
    tube("BackMould", [(x, yb - 0.05, z) for x, z in WS.arch(hw - 0.06, zs + 0.36, 3.7, 4.47, n=10)[1:]] + [(-(hw - 0.06), yb - 0.05, zs + 0.36)], 0.025,
         K["ebony"], square=True, poly=True)
    box("BackInset", (W - 0.7, 0.012, 1.2), (0, yb - 0.046, 2.65), K["crimson"], bevel=0.0)
    foil("BackFoil", 0, yb - 0.06, 3.75, 0.24, K["gilt"], lobes=4, thick=0.016)
    return _dims()


def circulation_desk(M):
    K = mats(M)
    rnd = random.Random(3014)
    W, D, H = 10.0, 3.2, 3.3
    box("Plinth", (W + 0.1, D + 0.1, 0.3), (0, 0, 0.15), K["ebony"], bevel=0.03)
    box("Front", (W, 0.2, H - 0.45), (0, -D / 2 + 0.1, 0.3 + (H - 0.45) / 2), K["oak"], bevel=0.02)
    for sx in (-1, 1):
        box(f"End{sx}", (0.2, D, H - 0.45), (sx * (W / 2 - 0.1), 0, 0.3 + (H - 0.45) / 2), K["oak"], bevel=0.02)
    box("Counter", (W + 0.4, D + 0.3, 0.15), (0, -0.15, H - 0.075), K["oak"], bevel=0.04)
    box("CounterMould", (W + 0.2, 0.1, 0.12), (0, -D / 2 - 0.12, H - 0.2), K["ebony"], bevel=0.03)
    # the front: five traceried bays, the middle one crimson with the LIBRARIAN plaque
    for k in range(5):
        cx = -4.0 + k * 2.0
        if k == 2:
            box("MidPanel", (1.6, 0.03, 2.2), (cx, -D / 2 - 0.015, 1.65), K["crimson"], bevel=0.0)
            box("PlaqueFrame", (1.55, 0.04, 0.42), (cx, -D / 2 - 0.05, 2.25), K["gilt"], bevel=0.012)
            plate("Plaque", "Plaque_LIBRARIAN", 1.42, 0.32, 0.03, T(cx, -D / 2 - 0.08, 2.25), K["atlas"])
            B20._crest("Crest", cx, -D / 2 - 0.05, 1.25, M, K["gilt"], s=1.3)
        else:
            tracery(f"Bay{k}", cx, -D / 2, 0.75, 0.55, 2.0, 2.75, K["ebony"], recess=K["back"], thick=0.028)
        if k < 4:
            box(f"Muntin{k}", (0.14, 0.06, H - 0.6), (cx + 1.0, -D / 2 - 0.03, 0.3 + (H - 0.6) / 2), K["ebony"], bevel=0.015)
    # the librarian's side: two shelves of books, facing +Y
    s = _mark()
    for i, z in enumerate((0.45, 1.75)):
        box(f"InShelf{i}", (W - 0.4, 1.4, 0.1), (0, -D / 2 + 0.95, z - 0.05), K["oak"], bevel=0.01)
        fill_row(f"In{i}", -W / 2 + 0.3, W / 2 - 0.3, z, -D / 2 + 0.3, 1.15, 1.18, rnd, K)
    _xform(s, RZ(math.pi))
    zc = H
    # on the counter: bell, date stamp and pad, the ledger, a card box, returned books, a candle lamp
    lathe("BellBase", [(0, 0), (0.2, 0), (0.2, 0.04), (0.17, 0.06), (0, 0.06)], K["ebony"], seg=20, loc=(-3.9, -0.9, zc))
    lathe("Bell", [(0, 0.06), (0.17, 0.06), (0.16, 0.1), (0.12, 0.2), (0.05, 0.24), (0, 0.245)], K["brass"], seg=24, loc=(-3.9, -0.9, zc))
    cyl("BellButton", 0.02, 0.06, (-3.9, -0.9, zc + 0.27), K["brass"], verts=10, bevel=0.005)
    box("StampPad", (0.42, 0.3, 0.05), (-3.1, -1.0, zc + 0.025), K["iron"], bevel=0.012)
    box("PadInk", (0.36, 0.24, 0.006), (-3.1, -1.0, zc + 0.052), K["ink"], bevel=0.0)
    box("StampFoot", (0.22, 0.14, 0.06), (-2.6, -1.05, zc + 0.03), K["iron"], bevel=0.01)
    lathe("StampHandle", [(0, 0.06), (0.04, 0.06), (0.035, 0.2), (0.06, 0.26), (0.05, 0.32), (0, 0.33)], K["ebony"], seg=12, loc=(-2.6, -1.05, zc))
    box("LedgerBoard", (1.9, 1.3, 0.06), (-0.6, -0.75, zc + 0.03), K["crimson"], bevel=0.015, rot=(0, 0, 3 * DEG))
    plate("Ledger", "Ledger", 1.8, 1.24, 0.02, T(-0.6, -0.75, zc + 0.07) @ RZ(3 * DEG) @ RX(-90 * DEG), K["atlas"], edge="paper")
    box("CardBox", (0.6, 0.9, 0.35), (1.3, -0.6, zc + 0.175), K["oakmid"], bevel=0.02)
    for k in range(9):
        plate(f"BoxCard{k}", "Card", 0.52, 0.34, 0.006, T(1.3, -0.95 + k * 0.08, zc + 0.36) @ RX(-8 * DEG), K["atlas"], edge="cardwhite", k=0.8)
    flat_stack("Returned", 2.6, -0.65, zc, 5, rnd, K, yaw=8 * DEG)
    flat_stack("Returned2", 3.8, -0.55, zc, 3, rnd, K, yaw=-15 * DEG)
    # a candle lamp at the end
    lathe("LampDish", [(0, 0), (0.3, 0), (0.32, 0.04), (0.25, 0.06), (0.06, 0.08), (0.05, 0.3), (0.08, 0.32), (0.07, 0.36), (0, 0.36)], K["brass"], seg=24,
          loc=(4.3, 0.6, zc))
    cyl("LampCandle", 0.06, 0.5, (4.3, 0.6, zc + 0.61), K["wax"], verts=14, bevel=0.01)
    lathe("LampChimney", [(0.12, 0.38), (0.15, 0.6), (0.13, 0.9), (0.1, 1.05), (0.09, 1.05), (0.12, 0.9), (0.14, 0.6), (0.11, 0.38)], K["glass"], seg=20,
          loc=(4.3, 0.6, zc))
    set_group("Glow")
    flame("LampFlame", (4.3, 0.6, zc + 0.86), h=0.18)
    set_group("Main")
    return _dims()


def _raven_wing(prefix, side, mat):
    """A cast raven wing as a feathered plate in its own frame (x out along the wing, z up), returned for placing."""
    pts = [(0.0, 0.0), (0.4, 0.2), (1.0, 0.34), (1.5, 0.3), (1.75, 0.15), (1.6, 0.0), (1.7, -0.18), (1.45, -0.22), (1.5, -0.4), (1.2, -0.42),
           (1.2, -0.6), (0.9, -0.55), (0.85, -0.72), (0.55, -0.6), (0.3, -0.45), (0.0, -0.3)]
    B20.tprism(f"{prefix}Wing{side}", WS.ccw([(side * x, z) for x, z in pts]), 0, 0.07, mat)
    for k in range(4):
        x0 = 0.35 + k * 0.32
        tube(f"{prefix}Quill{side}{k}", [(side * x0, -0.04, -0.15), (side * (x0 + 0.35), -0.04, -0.45 + k * 0.06)], 0.012, mat, poly=True)


def lectern(M):
    K = mats(M)
    br, ir = K["bronzedk"], K["iron"]          # a raven is dark: blackened bronze, the brass kept for the bands
    lathe("Base", [(0, 0), (1.2, 0), (1.2, 0.18), (1.0, 0.2), (1.0, 0.36), (0.8, 0.4), (0.8, 0.55), (0.45, 0.6), (0, 0.6)], K["ebony"], seg=8)
    lathe("Column", [(0, 0.6), (0.26, 0.6), (0.3, 0.75), (0.16, 0.95), (0.13, 2.4), (0.2, 2.5), (0.13, 2.6), (0.12, 3.0), (0.22, 3.12), (0, 3.15)], ir, seg=20)
    for k in range(3):
        hoop(f"Band{k}", (0, 0, 1.3 + k * 0.5), 0.15, "Z", K["brass"], thick=0.025)
    hoop("ChainRing", (0, 0, 2.62), 0.15, "Z", K["brass"], thick=0.028)
    # the raven, its back and spread wings the book rest (35 degrees), the head out in front below the book
    zb = 3.55
    sphere("Body", 0.42, (0, 0.05, zb - 0.12), br, seg=18, rings=10, scale=(0.9, 1.25, 0.8))
    sphere("Breast", 0.3, (0, -0.42, zb - 0.38), br, seg=14, rings=8, scale=(0.9, 0.8, 1.1))
    tube("Neck", [(0, -0.45, zb - 0.3), (0, -0.7, zb - 0.22), (0, -0.88, zb - 0.12)], 0.16, br)
    sphere("Head", 0.22, (0, -0.95, zb - 0.08), br, seg=14, rings=8, scale=(0.9, 1.1, 0.95))
    cone("Beak", 0.08, 0.0, 0.36, (0, -1.3, zb - 0.12), K["gilt"], verts=8, rot=(math.pi / 2 + 0.15, 0, 0))
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.035, (sx * 0.13, -1.08, zb - 0.02), K["gilt"], seg=8, rings=4)
    B20.tprism("Tail", WS.ccw([(-0.2, 0), (0.2, 0), (0.32, 0.7), (0.0, 0.8), (-0.32, 0.7)]), 0.0, 0.06, br, plane="XY")
    P.PARTS[-1].matrix_world = T(0, 0.5, zb - 0.2) @ RX(-0.35)
    W0 = Vector((0, 0.1, zb + 0.4))
    tilt = RX(-55 * DEG)
    for sx in (-1, 1):
        s = _mark()
        _raven_wing("R", sx, br)
        _xform(s, T(sx * 0.25, W0.y, W0.z) @ tilt)
    for sx in (-1, 1):
        tube(f"Talon{sx}", [(sx * 0.12, -0.1, 3.14), (sx * 0.2, -0.16, 3.14), (sx * 0.23, -0.18, 3.06)], 0.03, K["bronzedk"])
    # the bestiary open on the rest, its ledge at the front, chained to the column
    dirv, nrm = Vector((0, math.cos(35 * DEG), math.sin(35 * DEG))), Vector((0, -math.sin(35 * DEG), math.cos(35 * DEG)))
    o = W0 + nrm * 0.04
    rest = T(0, o.y, o.z) @ RX(35 * DEG)
    s = _mark()
    open_book("Bestiary", "Pages_Raven", 2.1, 1.4, Matrix.Identity(4), M, K, cover="ebony")
    _xform(s, rest)
    led = W0 + dirv * -0.76 + nrm * 0.07
    box("BookLedge", (2.2, 0.06, 0.13), (0, led.y, led.z), K["bronzedk"], bevel=0.02, rot=(35 * DEG, 0, 0))
    a = rest @ Vector((-1.0, -0.6, 0.03))
    chain("BookChain", [a, (-0.6, -0.5, 3.0), (-0.12, -0.1, 2.62)], ir, r=0.05, thick=0.013)
    return _dims()


def card_catalogue(M):
    K = mats(M)
    W, D = 4.6, 2.0
    zb, hc = 1.4, 3.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.13, 0), (0.14, 0.1), (0.1, 0.3), (0.14, 0.6), (0.11, 0.9), (0.15, 1.2), (0.15, zb), (0, zb)], K["oak"], seg=14,
                  loc=(sx * (W / 2 - 0.25), sy * (D / 2 - 0.25), 0))
    box("Stand", (W, D, 0.2), (0, 0, zb + 0.1), K["oak"], bevel=0.03)
    box("Shelf", (W - 0.5, D - 0.5, 0.08), (0, 0, 0.4), K["oak"], bevel=0.01)
    box("Case", (W - 0.1, D - 0.1, hc), (0, 0.05, zb + 0.2 + hc / 2), K["oak"], bevel=0.03)
    box("Top", (W + 0.2, D + 0.15, 0.14), (0, -0.025, zb + 0.2 + hc + 0.07), K["ebony"], bevel=0.04)
    box("Crest", (2.1, 0.3, 0.6), (0, -D / 2 + 0.2, zb + hc + 0.62), K["oak"], bevel=0.04)
    box("PlaqueFrame", (1.9, 0.05, 0.44), (0, -D / 2 + 0.025, zb + hc + 0.65), K["gilt"], bevel=0.015)
    plate("Plaque", "Plaque_CATALOGUE", 1.76, 0.34, 0.03, T(0, -D / 2 - 0.0, zb + hc + 0.65), K["atlas"])
    cols, rows = 6, 5
    dw, dh = (W - 0.5) / cols, (hc - 0.3) / rows
    yf = -D / 2 + 0.1                     # the case front
    k = 0
    for r in range(rows):
        for c in range(cols):
            x = -W / 2 + 0.25 + dw * (c + 0.5)
            z = zb + 0.35 + dh * (r + 0.5)
            out = 0.9 if (r, c) == (2, 3) else 0.0
            yo = yf - out
            box(f"Drawer{k}", (dw - 0.06, 0.08, dh - 0.06), (x, yo - 0.04, z), K["oakmid"], bevel=0.02)
            tube(f"LabelFrame{k}", [(x - 0.2, yo - 0.085, z + 0.05), (x + 0.2, yo - 0.085, z + 0.05), (x + 0.2, yo - 0.085, z + 0.2), (x - 0.2, yo - 0.085, z + 0.2)],
                 0.012, K["brass"], square=True, closed=True, poly=True)
            plate(f"Label{k}", f"Drawer_{k}", 0.38, 0.14, 0.008, T(x, yo - 0.085, z + 0.125), K["atlas"], edge="cardwhite", k=2.6)
            hoop(f"Pull{k}", (x, yo - 0.11, z - 0.1), 0.06, "Y", K["brass"], thick=0.014)
            cyl(f"PullRose{k}", 0.03, 0.03, (x, yo - 0.095, z - 0.04), K["brass"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
            if out:
                # the empty slot it came out of, the drawer's sides and floor, and its cards on their rod
                box("Slot", (dw - 0.06, 0.01, dh - 0.06), (x, yf - 0.004, z), K["back"], bevel=0.0)
                for sx in (-1, 1):
                    box(f"DrawerSide{sx}", (0.04, out, dh - 0.12), (x + sx * (dw / 2 - 0.06), yo + out / 2, z - 0.01), K["oakmid"], bevel=0.005)
                box("DrawerFloor", (dw - 0.1, out, 0.03), (x, yo + out / 2, z - dh / 2 + 0.07), K["oakmid"], bevel=0.0)
                for j in range(10):
                    plate(f"Card{j}", "Card", dw - 0.2, dh - 0.18, 0.006, T(x, yo + 0.1 + j * 0.075, z - 0.02) @ RX(-10 * DEG), K["atlas"], edge="cardwhite",
                          k=0.6 if j else 1.8)
                tube("CardRod", [(x, yo - 0.03, z - 0.12), (x, yf - 0.02, z - 0.12)], 0.01, K["brass"], poly=True)
            k += 1
    return _dims()


def map_chest(M):
    K = mats(M)
    W, D, H = 6.4, 4.0, 3.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Bun{sx}{sy}", 0.22, (sx * (W / 2 - 0.35), sy * (D / 2 - 0.35), 0.18), K["ebony"], seg=14, rings=7, scale=(1, 1, 0.8))
    box("Body", (W, D, H - 0.45), (0, 0, 0.32 + (H - 0.45) / 2), K["oak"], bevel=0.03)
    box("Top", (W + 0.2, D + 0.2, 0.14), (0, 0, H - 0.07), K["oak"], bevel=0.04)
    box("TopInset", (W - 0.6, D - 0.6, 0.01), (0, 0, H + 0.003), K["crimson"], bevel=0.0)
    box("Plinth", (W + 0.08, D + 0.08, 0.2), (0, 0, 0.36), K["ebony"], bevel=0.03)
    nd = 6
    dh = (H - 0.75) / nd
    for k in range(nd):
        z = 0.5 + dh * (k + 0.5)
        box(f"Drawer{k}", (W - 0.3, 0.06, dh - 0.06), (0, -D / 2 - 0.03, z), K["oakmid"], bevel=0.015)
        for sx in (-1, 1):
            x = sx * 1.9
            box(f"Cup{k}{sx}", (0.5, 0.05, 0.12), (x, -D / 2 - 0.08, z - 0.03), K["brass"], bevel=0.02)
            box(f"CupLip{k}{sx}", (0.44, 0.08, 0.04), (x, -D / 2 - 0.1, z - 0.085), K["brass"], bevel=0.01)
        tube(f"LabelFrame{k}", [(-0.45, -D / 2 - 0.07, z - 0.1), (0.45, -D / 2 - 0.07, z - 0.1), (0.45, -D / 2 - 0.07, z + 0.1), (-0.45, -D / 2 - 0.07, z + 0.1)],
             0.012, K["brass"], square=True, closed=True, poly=True)
        if k == nd - 1:
            plate("Label", "Plaque_MAPS", 0.86, 0.18, 0.008, T(0, -D / 2 - 0.07, z), K["atlas"], k=2.4)
        else:
            plate(f"Label{k}", "Card", 0.86, 0.18, 0.008, T(0, -D / 2 - 0.07, z), K["atlas"], edge="cardwhite", k=0.6)
    # the map of the moor on top, curling at one end, held by brass weights
    zt = H + 0.02
    mw, md = 4.6, 3.1

    def sheet(s, t):
        x = -mw / 2 + s * mw
        y = -md / 2 + t * md
        z = zt + (0.25 * ((s - 0.85) / 0.15) ** 2 if s > 0.85 else 0.0)
        return (x - (0.1 * ((s - 0.85) / 0.15) ** 2 if s > 0.85 else 0.0), y, z)
    leaf_sheet("Map", "Map_Moor", sheet, 16, 2, (0, 0, 1, 1), K["atlas"], thick=0.008, k=2.4)
    for k, (x, y) in enumerate(((-2.15, -1.4), (-2.15, 1.4), (1.6, -1.4), (1.6, 1.4))):
        lathe(f"Weight{k}", [(0, 0), (0.14, 0), (0.15, 0.03), (0.12, 0.1), (0.05, 0.13), (0.05, 0.2), (0.08, 0.24), (0, 0.27)], K["brass"], seg=18, loc=(x, y, zt + 0.006))
    for sx in (-1, 1):
        tube(f"Divider{sx}", [(-0.6, 0.5, zt + 0.03), (-0.6 + sx * 0.25 + 0.9, 0.5 - 0.6, zt + 0.02)], 0.018, K["steel"], poly=True)
    sphere("DividerHead", 0.05, (-0.6, 0.5, zt + 0.04), K["brass"], seg=8, rings=4)
    cyl("Roll", 0.12, 2.2, (2.6, 0.2, zt + 0.12), K["paper"], rot=(math.pi / 2, 0, 0.1), verts=16, bevel=0.01)
    return _dims()


def newspaper_rack(M):
    K = mats(M)
    W, H = 3.6, 5.4
    ir = K["iron"]
    for sx in (-1, 1):
        x = sx * (W / 2)
        tube(f"Leg{sx}F", [(x, -0.9, 0.0), (x, -0.55, 2.0), (x, -0.25, 4.6), (x, -0.1, 5.1)], 0.045, ir, square=True)
        tube(f"Leg{sx}B", [(x, 0.9, 0.0), (x, 0.55, 2.0), (x, 0.25, 4.6), (x, 0.1, 5.1)], 0.045, ir, square=True)
        tube(f"Scroll{sx}", [(x, -0.48, 2.4), (x, -0.2, 2.6), (x, 0.0, 2.3), (x, 0.2, 2.6), (x, 0.48, 2.4)], 0.03, ir)
        sphere(f"Finial{sx}", 0.1, (x, 0.0, 5.2), K["brass"], seg=10, rings=5)
        for sy in (-1, 1):
            sphere(f"Toe{sx}{sy}", 0.08, (x, sy * 0.9, 0.06), K["brass"], seg=8, rings=4)
    tube("TopBar", [(-W / 2, 0.0, 5.08), (W / 2, 0.0, 5.08)], 0.04, ir, square=True, poly=True)
    tube("LowBar", [(-W / 2, 0.0, 1.0), (W / 2, 0.0, 1.0)], 0.04, ir, square=True, poly=True)
    plate("Plaque", "Plaque_PAPERS", 1.7, 0.42, 0.03, T(0, -0.05, 5.38), K["atlas"])
    box("PlaqueFrame", (1.84, 0.05, 0.56), (0, -0.01, 5.38), K["gilt"], bevel=0.012)
    # three newspapers on their sticks, hung on hooks at three heights, stepped back
    for k, (z, y) in enumerate(((4.45, -0.32), (3.45, -0.55), (2.45, -0.78))):
        tube(f"Stick{k}", [(-W / 2 + 0.06, y, z), (W / 2 - 0.06, y, z)], 0.045, K["oakmid"], poly=True)
        for sx in (-1, 1):
            tube(f"Hook{k}{sx}", [(sx * (W / 2), y * 0.5, z + 0.12), (sx * (W / 2 - 0.02), y, z + 0.08), (sx * (W / 2 - 0.02), y, z - 0.03)], 0.02, ir, poly=True)
        pw, ph = 1.7, 2.3
        xs = -0.9 + k * 0.85 - 0.0

        def hang(s, t, y=y, z=z, xs=xs):
            return (xs - pw / 2 + s * pw, y - 0.05 - 0.04 * math.sin(s * math.pi) - 0.02 * (1 - t), z - 0.05 - (1 - t) * ph)
        leaf_sheet(f"News{k}", f"News_{k}", hang, 4, 6, (0, 0, 1, 1), K["atlas"], thick=0.008, k=2.2)
    return _dims()


# ================================================================== fittings

def step_stool(M):
    K = mats(M)
    W, D = 2.2, 2.2
    prof = [(-D / 2, 0), (D / 2, 0), (D / 2, 1.6), (0.0, 1.6), (0.0, 0.8), (-D / 2, 0.8)]
    for sx in (-1, 1):
        B20.tprism(f"Cheek{sx}", WS.ccw(prof), sx * (W / 2 - 0.08), 0.16, K["oak"], plane="YZ")
        s = _mark()
        foil(f"CheekFoil{sx}", -0.35, 0, 0.4, 0.2, K["ebony"], lobes=4, thick=0.02)
        foil(f"CheekFoil2{sx}", 0.4, 0, 0.8, 0.26, K["ebony"], lobes=4, thick=0.02)
        B20._side(s, sx * (W / 2 + 0.002), sx)
    for k, (y0, y1, z) in enumerate(((-D / 2, 0.0, 0.8), (0.0, D / 2, 1.6))):
        box(f"Tread{k}", (W - 0.32, y1 - y0 + 0.08, 0.1), (0, (y0 + y1) / 2 - 0.04, z - 0.05), K["oak"], bevel=0.02)
        box(f"Leather{k}", (W - 0.6, y1 - y0 - 0.25, 0.012), (0, (y0 + y1) / 2 - 0.02, z + 0.004), K["crimson"], bevel=0.0)
        box(f"Nosing{k}", (W - 0.3, 0.06, 0.06), (0, y0 - 0.08, z - 0.03), K["brass"], bevel=0.015)
        box(f"Riser{k}", (W - 0.32, 0.08, 0.75), (0, y0 + 0.06, z - 0.47), K["back"], bevel=0.01)
    return _dims()


def rolling_ladder(M):
    K = mats(M)
    W = 2.2
    zp = 5.2
    yb, yt = -1.9, 0.9
    a0, a1 = Vector((0, yb, 0.3)), Vector((0, yt - 0.3, zp))
    for sx in (-1, 1):
        x = sx * W / 2
        tube(f"Stile{sx}", [(x, yb, 0.3), (x, yt - 0.3, zp)], 0.08, K["oakmid"], square=True, poly=True)
        tube(f"Post{sx}", [(x, yt + 0.6, 0.3), (x, yt + 0.6, zp + 2.6)], 0.07, K["oakmid"], square=True, poly=True)
        p0 = a0.lerp(a1, 0.3)
        tube(f"Baluster{sx}", [(x, p0.y, p0.z), (x, p0.y, p0.z + 2.4)], 0.03, K["brass"], poly=True)
        tube(f"Rail{sx}", [(x, p0.y, p0.z + 2.4), (x, a1.y, a1.z + 2.4), (x, yt + 0.6, zp + 2.6)], 0.035, K["brass"], poly=True)
        tube(f"Brace{sx}", [(x, yb + 0.1, 0.32), (x, yt + 0.6, 0.32)], 0.06, K["iron"], square=True, poly=True)
        for j, y in enumerate((yb + 0.05, yt + 0.6)):
            box(f"Caster{sx}{j}", (0.14, 0.24, 0.12), (x, y, 0.22), K["iron"], bevel=0.02)
            cyl(f"Wheel{sx}{j}", 0.15, 0.07, (x, y, 0.15), K["brass"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    for k in range(1, 6):
        p = a0.lerp(a1, k / 6)
        box(f"Step{k}", (W - 0.1, 0.4, 0.07), (0, p.y, p.z), K["oak"], bevel=0.015)
        box(f"StepLeather{k}", (W - 0.4, 0.3, 0.01), (0, p.y, p.z + 0.04), K["crimson"], bevel=0.0)
    box("Platform", (W - 0.1, 1.2, 0.1), (0, yt, zp), K["oak"], bevel=0.02)
    box("PlatformLeather", (W - 0.4, 1.0, 0.01), (0, yt, zp + 0.055), K["crimson"], bevel=0.0)
    tube("BackRail", [(-W / 2, yt + 0.6, zp + 2.6), (W / 2, yt + 0.6, zp + 2.6)], 0.035, K["brass"], poly=True)
    tube("MidRail", [(-W / 2, yt + 0.6, zp + 1.3), (W / 2, yt + 0.6, zp + 1.3)], 0.03, K["brass"], poly=True)
    return _dims()


def _tilt():
    return 23.4 * DEG


def terrestrial_globe(M):
    K = mats(M)
    zc, R = 3.3, 1.2
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        pts = [(0.2, 1.4), (0.75, 0.9), (1.05, 0.35), (1.25, 0.12), (1.45, 0.16)]
        tube(f"Leg{k}", [(c * r, s_ * r, z) for r, z in pts], 0.09, K["oak"], square=True)
        sphere(f"Toe{k}", 0.13, (c * 1.45, s_ * 1.45, 0.13), K["brass"], seg=10, rings=5)
        tube(f"Strut{k}", [(c * 1.2, s_ * 1.2, 0.35), (c * 1.42, s_ * 1.42, zc - 0.05)], 0.07, K["oak"], square=True, poly=True)
    lathe("Hub", [(0, 1.2), (0.3, 1.2), (0.34, 1.35), (0.18, 1.6), (0.14, 1.9), (0.22, 2.0), (0, 2.02)], K["oak"], seg=20)
    hoop("Stretcher", (0, 0, 0.42), 0.95, "Z", K["brass"], thick=0.03)
    # the horizon ring: a flat oak band with a brass edge, the meridian through notches in it
    lathe("Horizon", [(R + 0.12, zc - 0.05), (R + 0.45, zc - 0.05), (R + 0.45, zc + 0.05), (R + 0.12, zc + 0.05)], K["oakmid"], seg=48)
    hoop("HorizonEdge", (0, 0, zc + 0.05), R + 0.45, "Z", K["brass"], thick=0.02)
    tl = _tilt()
    ax = Vector((math.sin(tl), 0, math.cos(tl)))
    s = _mark()
    hoop("Meridian", (0, 0, 0), R + 0.07, "Y", K["brass"], thick=0.035)
    _xform(s, T(0, 0, zc) @ RY(tl))
    set_group("Globe", hinge=(0, 0, zc))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=R, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "GlobeSphere"
    g.data.uv_layers[0].name = "Spine"
    bm = bmesh.new()
    bm.from_mesh(g.data)
    kl = bm.faces.layers.float.new("nh_uvk")
    for f in bm.faces:
        f[kl] = 1.6
    bm.to_mesh(g.data)
    bm.free()
    for p in g.data.polygons:
        p.use_smooth = True
    g.matrix_world = T(0, 0, zc) @ RY(tl)
    _finish(g, atlas_mat("LibGlobe", image="LibraryGlobe", maps=False, rough=0.35, leather=0.05), 0)
    for sgn in (-1, 1):
        p = Vector((0, 0, zc)) + ax * sgn * (R + 0.06)
        sphere(f"Pin{sgn}", 0.05, tuple(p), K["brass"], seg=8, rings=4)
    set_group("Main")
    return _dims()


def armillary_sphere(M):
    K = mats(M)
    br, gl = K["brass"], K["gilt"]
    zc, R = 3.2, 0.95
    lathe("Base", [(0, 0), (0.9, 0), (0.9, 0.12), (0.75, 0.16), (0.7, 0.3), (0.4, 0.36), (0.3, 0.5), (0, 0.5)], K["ebony"], seg=24)
    lathe("Column", [(0, 0.5), (0.16, 0.5), (0.22, 0.65), (0.12, 0.9), (0.1, 1.6), (0.18, 1.7), (0.08, 1.85), (0.06, zc - R - 0.25), (0.14, zc - R - 0.15),
                     (0, zc - R - 0.1)], br, seg=20)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        tube(f"Support{k}", [(math.cos(a) * 0.15, math.sin(a) * 0.15, zc - R - 0.15), (math.cos(a) * (R + 0.18), math.sin(a) * (R + 0.18), zc - 0.4),
                             (math.cos(a) * (R + 0.22), math.sin(a) * (R + 0.22), zc)], 0.03, br)
    hoop("Horizon", (0, 0, zc), R + 0.22, "Z", br, thick=0.04)
    for sx in (-1, 1):            # the meridian rests in two brass blocks on the horizon ring
        box(f"MeridianBlock{sx}", (0.14, 0.1, 0.08), (sx * (R + 0.17), 0, zc), br, bevel=0.015)
    tl = _tilt()
    s = _mark()
    hoop("Meridian", (0, 0, 0), R + 0.12, "Y", br, thick=0.035)
    _xform(s, T(0, 0, zc) @ RY(tl))
    set_group("Rings", hinge=(0, 0, zc))
    s = _mark()
    hoop("Equator", (0, 0, 0), R, "Z", br, thick=0.035)
    for k, zz in enumerate((-0.4, 0.4)):
        hoop(f"Tropic{k}", (0, 0, zz * R), R * math.sqrt(1 - zz * zz), "Z", br, thick=0.02)
    for k in range(2):
        s2 = _mark()
        hoop(f"Colure{k}", (0, 0, 0), R, "Y", br, thick=0.025)
        _xform(s2, RZ(k * math.pi / 2))
    s2 = _mark()
    lathe("Ecliptic", [(R - 0.02, -0.07), (R + 0.02, -0.07), (R + 0.02, 0.07), (R - 0.02, 0.07)], gl, seg=48)
    _xform(s2, RX(tl))
    tube("Axis", [(0, 0, -R - 0.15), (0, 0, R + 0.15)], 0.018, K["steel"], poly=True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.22, location=(0, 0, 0))
    e = bpy.context.active_object
    e.name = "Earth"
    e.data.uv_layers[0].name = "Spine"
    for p in e.data.polygons:
        p.use_smooth = True
    _finish(e, atlas_mat("LibGlobe", image="LibraryGlobe", maps=False, rough=0.35, leather=0.05), 0)
    for sgn in (-1, 1):
        sphere(f"AxisKnob{sgn}", 0.04, (0, 0, sgn * (R + 0.16)), br, seg=8, rings=4)
    _xform(s, T(0, 0, zc) @ RY(tl))
    set_group("Main")
    return _dims()


def banker_lamp(M):
    K = mats(M)
    b = _lamp_banker("Lamp", 0, 0, 0, K, scale=1.0)
    set_group("Glow")
    _bulb("Bulb", b, K, r=0.08, scale=(3.0, 1, 1))
    set_group("Main")
    return _dims()


def candle_lamp(M):
    K = mats(M)
    br = K["brass"]
    lathe("Dish", [(0, 0), (0.55, 0), (0.58, 0.04), (0.55, 0.1), (0.45, 0.12), (0.12, 0.14), (0.1, 0.2), (0, 0.2)], br, seg=32)
    hoop("DishBead", (0, 0, 0.09), 0.565, "Z", br, thick=0.02)
    tube("Rod", [(0, 0, 0.2), (0, 0, 2.05)], 0.03, br, poly=True)
    sphere("Finial", 0.06, (0, 0, 2.1), br, seg=10, rings=5)
    tips = []
    for sx in (-1, 1):
        tube(f"Arm{sx}", [(0, 0, 0.55), (sx * 0.22, 0, 0.48), (sx * 0.38, 0, 0.6), (sx * 0.4, 0, 0.7)], 0.025, br)
        lathe(f"Cup{sx}", [(0, 0), (0.12, 0), (0.13, 0.02), (0.06, 0.04), (0.05, 0.12), (0, 0.12)], br, seg=18, loc=(sx * 0.4, 0, 0.7))
        cyl(f"Candle{sx}", 0.05, 0.42, (sx * 0.4, 0, 0.82 + 0.21), K["wax"], verts=12, bevel=0.01)
        sphere(f"Drip{sx}", 0.02, (sx * 0.4 + 0.05, 0, 1.1), K["wax"], seg=6, rings=4, scale=(1, 1, 2.4))
        tips.append((sx * 0.4, 0, 1.24))
    # the crimson shade: a low drum on the rod, above the flames
    lathe("Shade", [(0.72, 1.42), (0.5, 1.78), (0.49, 1.78), (0.7, 1.43)], K["enamel"], seg=40)
    hoop("ShadeRim", (0, 0, 1.425), 0.715, "Z", K["gilt"], thick=0.018)
    hoop("ShadeTop", (0, 0, 1.78), 0.5, "Z", K["gilt"], thick=0.015)
    for k in range(3):
        a = k * 2 * math.pi / 3
        tube(f"ShadeSpoke{k}", [(0.03 * math.cos(a), 0.03 * math.sin(a), 1.78), (0.49 * math.cos(a), 0.49 * math.sin(a), 1.78)], 0.012, br, poly=True)
    cyl("ShadeCollar", 0.06, 0.1, (0, 0, 1.78), br, verts=12, bevel=0.01)
    tube("Handle", [(0.55, 0, 0.12), (0.75, 0, 0.18), (0.74, 0, 0.32), (0.62, 0, 0.3)], 0.02, br)
    set_group("Glow")
    for k, t in enumerate(tips):
        flame(f"Flame{k}", t, h=0.16)
    set_group("Main")
    return _dims()


def lib_candelabra(M):
    K = mats(M)
    br = K["brass"]
    lathe("Base", [(0, 0), (0.45, 0), (0.47, 0.04), (0.4, 0.1), (0.2, 0.16), (0.12, 0.3), (0.16, 0.4), (0.09, 0.55), (0.07, 1.1), (0.12, 1.18), (0, 1.2)], br, seg=28,
          flute=(12, 0.04))
    tips = [(0, 0, 1.62)]
    lathe("CentreCup", [(0, 1.2), (0.07, 1.2), (0.06, 1.38), (0.12, 1.44), (0.1, 1.5), (0, 1.5)], br, seg=18)
    for sx in (-1, 1):
        tube(f"Arm{sx}", [(0, 0, 1.0), (sx * 0.25, 0, 0.92), (sx * 0.5, 0, 1.0), (sx * 0.58, 0, 1.2), (sx * 0.58, 0, 1.3)], 0.03, br)
        tube(f"Curl{sx}", [(sx * 0.25, 0, 0.92), (sx * 0.2, 0, 0.8), (sx * 0.3, 0, 0.76), (sx * 0.34, 0, 0.84)], 0.018, br)
        lathe(f"Cup{sx}", [(0, 0), (0.12, 0), (0.12, 0.03), (0.06, 0.05), (0.05, 0.14), (0, 0.14)], br, seg=18, loc=(sx * 0.58, 0, 1.3))
        tips.append((sx * 0.58, 0, 1.44))
    rnd = random.Random(3025)
    flames = []
    for k, (x, y, z) in enumerate(tips):
        h = 0.55 if k == 0 else rnd.uniform(0.32, 0.45)
        cyl(f"Candle{k}", 0.055, h, (x, y, z + h / 2), K["wax"], verts=12, bevel=0.01)
        for d in range(2):
            ang = rnd.uniform(0, 2 * math.pi)
            sphere(f"Drip{k}{d}", 0.02, (x + math.cos(ang) * 0.055, y + math.sin(ang) * 0.055, z + h - 0.05 - d * 0.12), K["wax"], seg=6, rings=4,
                   scale=(1, 1, 2.4))
        flames.append((x, y, z + h))
    set_group("Glow")
    for k, f in enumerate(flames):
        flame(f"Flame{k}", f, h=0.16)
    set_group("Main")
    return _dims()


def librarian_bust(M):
    K = mats(M)
    br, dk, eb, gl = K["bronze"], K["bronzedk"], K["ebony"], K["gilt"]
    # a square pedestal: a moulded foot, a shaft with a gilt-framed plaque, a cap
    box("Foot", (1.7, 1.7, 0.3), (0, 0, 0.15), eb, bevel=0.04)
    box("Foot2", (1.45, 1.45, 0.2), (0, 0, 0.4), eb, bevel=0.04)
    box("Shaft", (1.1, 1.1, 2.4), (0, 0, 0.5 + 1.2), eb, bevel=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Arris{sx}{sy}", (0.08, 0.08, 2.3), (sx * 0.53, sy * 0.53, 1.7), gl, bevel=0.015)
    box("Cap", (1.4, 1.4, 0.18), (0, 0, 2.99), eb, bevel=0.04)
    box("Cap2", (1.55, 1.55, 0.12), (0, 0, 3.14), eb, bevel=0.03)
    box("PlaqueFrame", (0.92, 0.03, 0.32), (0, -0.565, 2.4), gl, bevel=0.008)
    plate("Plaque", "Plaque_LIBRARIAN", 0.82, 0.22, 0.02, T(0, -0.585, 2.4), K["atlas"])
    foil("ShaftFoil", 0, -0.56, 1.4, 0.18, gl, lobes=4, thick=0.014)
    z = 3.2
    # the bust: an R6 chest and rounded head (1.1 scale), a soft cap, spectacles, a quill behind the ear, a crimson scarf
    S = 1.1
    lathe("Socle", [(0, z), (0.42, z), (0.4, z + 0.12), (0.3, z + 0.18), (0.3, z + 0.3), (0, z + 0.3)], dk, seg=24)
    cw, cd = 2.0 * S * 0.8, 1.0 * S * 0.8
    box("Chest", (cw, cd, 1.1), (0, 0, z + 0.3 + 0.55), br, bevel=0.14, segments=3)
    zh = z + 0.3 + 1.1
    box("Neck", (0.5, 0.5, 0.25), (0, 0, zh + 0.1), br, bevel=0.06)
    zh += 0.2
    hs = 1.2 * S
    box("Head", (hs, hs, hs), (0, 0, zh + hs / 2), br, bevel=0.3, segments=4)
    sphere("Cap", hs * 0.58, (0, 0.05, zh + hs * 0.98), dk, seg=16, rings=8, scale=(1.15, 1.15, 0.45))
    sphere("CapButton", 0.06, (0, 0.05, zh + hs * 1.24), gl, seg=8, rings=4)
    yf = -hs / 2 - 0.005
    for sx in (-1, 1):
        hoop(f"Lens{sx}", (sx * 0.25, yf - 0.03, zh + hs * 0.58), 0.14, "Y", gl, thick=0.02)
        sphere(f"Eye{sx}", 0.055, (sx * 0.25, yf + 0.01, zh + hs * 0.58), dk, seg=8, rings=4, scale=(1, 0.4, 1))
        tube(f"Temple{sx}", [(sx * 0.39, yf - 0.03, zh + hs * 0.6), (sx * (hs / 2 + 0.02), -0.1, zh + hs * 0.62), (sx * (hs / 2 + 0.02), 0.25, zh + hs * 0.55)],
             0.012, gl)
        box(f"Brow{sx}", (0.26, 0.06, 0.06), (sx * 0.25, yf - 0.01, zh + hs * 0.76), dk, bevel=0.02, rot=(0, sx * 0.15, 0))
    tube("Bridge", [(-0.11, yf - 0.03, zh + hs * 0.6), (0, yf - 0.045, zh + hs * 0.63), (0.11, yf - 0.03, zh + hs * 0.6)], 0.013, gl)
    tube("Mouth", [(-0.17, yf, zh + hs * 0.28), (0, yf - 0.01, zh + hs * 0.25), (0.17, yf, zh + hs * 0.28)], 0.02, dk)
    quill = flat("BustQuill", (0.86, 0.84, 0.78), 0.7, wear=0.1)
    strip("Quill", [(hs / 2 + 0.03, 0.05, zh + hs * 0.55), (hs / 2 + 0.08, 0.15, zh + hs * 0.85), (hs / 2 + 0.12, 0.3, zh + hs * 1.15)], 0.1, (0, 0.5, -0.4), quill,
          thick=0.008)
    box("ScarfWrap", (1.2, 1.0, 0.22), (0, 0, zh - 0.08), K["enamel"], bevel=0.08)
    for sx in (-1, 1):
        strip(f"Scarf{sx}", [(sx * 0.3, -cd / 2 - 0.03, zh - 0.12), (sx * 0.26, -cd / 2 - 0.035, zh - 0.6), (sx * 0.22, -cd / 2 - 0.03, z + 0.5)], 0.3,
              (1, 0, 0), K["enamel"], thick=0.04)
    return _dims()


def library_clock(M):
    K = mats(M)
    eb, cr, br, gl = K["ebony"], K["enamel"], K["brass"], K["gilt"]
    W, D = 2.4, 1.3
    zw0, zw1 = 1.75, 6.35
    zt = zw1 + 2.6
    box("Plinth", (W + 0.3, D + 0.2, 0.25), (0, -0.05, 0.125), eb, bevel=0.03)
    box("Base", (W + 0.1, D + 0.1, 1.5), (0, 0, 0.25 + 0.75), eb, bevel=0.03)
    box("BasePanel", (W - 0.5, 0.03, 1.0), (0, -D / 2 - 0.065, 1.0), cr, bevel=0.0)
    foil("BaseFoil", 0, -D / 2 - 0.085, 1.0, 0.28, gl, lobes=4, thick=0.02)
    # the trunk: hollow, so the pendulum hangs inside behind a lancet glass door
    tw = W - 0.3
    yfr = -D / 2 + 0.075              # the trunk's front face
    for sx in (-1, 1):
        box(f"TrunkSide{sx}", (0.15, D - 0.15, zw1 - zw0), (sx * (tw / 2 - 0.075), 0.075, (zw0 + zw1) / 2), eb, bevel=0.02)
    box("TrunkBack", (tw - 0.3, 0.12, zw1 - zw0), (0, D / 2 - 0.06, (zw0 + zw1) / 2), eb, bevel=0.0)
    box("PendBack", (tw - 0.3, 0.02, zw1 - zw0 - 0.2), (0, D / 2 - 0.13, (zw0 + zw1) / 2), cr, bevel=0.0)
    hw = (W - 0.9) / 2
    zo0, zos, zoa = zw0 + 0.3, zw1 - 1.0, zw1 - 0.3
    arc = WS.pointed(hw, zos, zoa, 10)
    left = arc[: len(arc) // 2 + 1]
    for sx in (-1, 1):
        box(f"Stile{sx}", (tw / 2 - 0.15 - hw, 0.1, zw1 - zw0), (sx * (hw + (tw / 2 - 0.15 - hw) / 2), yfr + 0.05, (zw0 + zw1) / 2), eb, bevel=0.0)
        poly = [(-tw / 2 + 0.15, zos), (-hw, zos)] + left[1:] + [(0.0, zw1), (-tw / 2 + 0.15, zw1)]
        B20.tprism(f"Spandrel{sx}", WS.ccw([(sx * x, z) for x, z in poly]), yfr + 0.05, 0.1, eb)
    box("BottomRail", (2 * hw + 0.02, 0.1, 0.3), (0, yfr + 0.05, zw0 + 0.15), eb, bevel=0.0)
    door = WS.arch(hw, zo0, zos, zoa, n=10)
    tube("DoorFrame", [(x, yfr - 0.02, z) for x, z in door + [door[0]]], 0.05, br, square=True, poly=True)
    outer = WS.arch(hw + 0.14, zo0 - 0.12, zos, zoa + 0.12, n=10)
    tube("DoorMould", [(x, yfr - 0.03, z) for x, z in outer + [outer[0]]], 0.025, gl, square=True, poly=True)
    # the hood, its gable and pinnacles
    box("Hood", (W + 0.2, D + 0.15, 2.6), (0, 0, zw1 + 1.3), eb, bevel=0.03)
    box("HoodCap", (W + 0.45, D + 0.3, 0.16), (0, -0.05, zt + 0.08), eb, bevel=0.04)
    _gable("HoodGable", 0, -D / 2 + 0.12, W / 2 + 0.05, zt + 0.16, zt + 1.2, 0.2, eb, gl, edge=0.03)
    for sx in (-1, 1):
        _pinnacle(f"Pin{sx}", sx * (W / 2 + 0.05), -D / 2 + 0.12, zt + 0.16, 1.1, eb)
        box(f"HoodPost{sx}", (0.2, 0.2, 2.6), (sx * (W / 2 + 0.02), -D / 2 - 0.03, zw1 + 1.3), cr, bevel=0.03)
    # the dial: a bone face, ink chapter ring and ticks, spade hands; the moon disc in the arch above
    zd = zw1 + 0.95
    yd = -D / 2 - 0.09
    cyl("DialPlate", 0.85, 0.04, (0, yd + 0.03, zd), br, rot=(math.pi / 2, 0, 0), verts=40, bevel=0.01)
    cyl("Dial", 0.75, 0.03, (0, yd, zd), K["bone"], rot=(math.pi / 2, 0, 0), verts=40, bevel=0.005)
    hoop("Chapter", (0, yd - 0.02, zd), 0.62, "Y", K["ink"], thick=0.012)
    hoop("Chapter2", (0, yd - 0.02, zd), 0.48, "Y", K["ink"], thick=0.008)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        L = 0.12 if k % 3 == 0 else 0.07
        r0 = 0.6 - L
        tube(f"Tick{k}", [(math.sin(a) * r0, yd - 0.02, zd + math.cos(a) * r0), (math.sin(a) * 0.6, yd - 0.02, zd + math.cos(a) * 0.6)],
             0.018 if k % 3 == 0 else 0.011, K["ink"], square=True, poly=True)
    for k, (a, L, wdt) in enumerate(((-58 * DEG, 0.36, 0.035), (130 * DEG, 0.55, 0.025))):
        p = (math.sin(a) * L, yd - 0.045, zd + math.cos(a) * L)
        tube(f"Hand{k}", [(0, yd - 0.045, zd), p], wdt, K["ink"], square=True, poly=True)
        sphere(f"Spade{k}", 0.05, (math.sin(a) * L * 0.82, yd - 0.045, zd + math.cos(a) * L * 0.82), K["ink"], seg=8, rings=4, scale=(1, 0.4, 1.4))
    cyl("Boss", 0.05, 0.04, (0, yd - 0.06, zd), br, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.005)
    B20.tprism("MoonArch", WS.ccw(WS.arch(0.55, zd + 0.92, zd + 1.02, zd + 1.55, n=10)), yd + 0.01, 0.03, K["night"])
    B20.tprism("Moon", WS.crescent(0.0, zd + 1.22, 0.2, shift=0.42, tilt=0.4), yd - 0.025, 0.03, gl)
    for k, (x, z) in enumerate(((-0.35, zd + 1.12), (0.33, zd + 1.38), (0.22, zd + 1.06), (-0.18, zd + 1.46))):
        sphere(f"Star{k}", 0.025, (x, yd - 0.02, z), gl, seg=6, rings=3)
    for k in range(2):
        tube(f"Chain{k}", [((k - 0.5) * 0.6, D / 2 - 0.45, zw1 - 0.05), ((k - 0.5) * 0.6, D / 2 - 0.45, zw0 + 2.4 + k * 0.5)], 0.012, br, poly=True)
        cyl(f"Weight{k}", 0.11, 0.7, ((k - 0.5) * 0.6, D / 2 - 0.45, zw0 + 2.05 + k * 0.5), br, verts=16, bevel=0.02)
    box("Seat", (tw - 0.3, D - 0.3, 0.06), (0, 0.075, zw1 - 0.03), eb, bevel=0.0)
    set_group("Glass")
    B20.tprism("Pane", WS.ccw(door), yfr + 0.05, 0.03, K["glass"])
    set_group("Pendulum", hinge=(0, -D / 2 + 0.45, zw1 - 0.25), swing=1)
    tube("PendRod", [(0, -D / 2 + 0.45, zw1 - 0.25), (0, -D / 2 + 0.45, zw0 + 1.0)], 0.03, br, poly=True)
    cyl("PendBob", 0.36, 0.06, (0, -D / 2 + 0.45, zw0 + 0.9), br, rot=(math.pi / 2, 0, 0), verts=32, bevel=0.015)
    foil("BobFoil", 0, -D / 2 + 0.41, zw0 + 0.9, 0.16, gl, lobes=4, thick=0.012)
    set_group("Main")
    return _dims()


def silence_sign(M):
    K = mats(M)
    ir, gl = K["iron"], K["gilt"]
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Foot{k}", [(c * r, s_ * r, z) for r, z in ((0.05, 0.7), (0.35, 0.4), (0.62, 0.1), (0.8, 0.14), (0.78, 0.3), (0.68, 0.3))], 0.035, ir, square=True)
        sphere(f"Toe{k}", 0.06, (c * 0.62, s_ * 0.62, 0.06), ir, seg=8, rings=4)
    tube("Post", [(0, 0, 0.6), (0, 0, 3.6)], 0.06, ir, square=True, poly=True)
    cyl("Collar", 0.1, 0.12, (0, 0, 0.75), K["brass"], verts=14, bevel=0.02)
    # the plaque: crimson enamel, a raised gilt border, SILENCE in raised gilt capitals, a line under it
    pw, ph, zc = 3.0, 1.25, 4.15
    box("Plaque", (pw, 0.1, ph), (0, 0, zc), K["enamel"], bevel=0.03)
    tube("Border", [(-pw / 2 + 0.1, -0.055, zc - ph / 2 + 0.1), (pw / 2 - 0.1, -0.055, zc - ph / 2 + 0.1), (pw / 2 - 0.1, -0.055, zc + ph / 2 - 0.1),
                    (-pw / 2 + 0.1, -0.055, zc + ph / 2 - 0.1)], 0.02, gl, square=True, closed=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sphere(f"Rivet{sx}{sz}", 0.04, (sx * (pw / 2 - 0.1), -0.06, zc + sz * (ph / 2 - 0.1)), gl, seg=8, rings=4)
    _text("Word", "SILENCE", FONT_SIGN, gl, lambda x, y, h: (x, -0.05 - h, zc + 0.12 + y), fit=(2.5, 0.56), depth=0.025, res=4)
    _text("Sub", "quiet in the stacks", FONT_SIGN_I, gl, lambda x, y, h: (x, -0.05 - h, zc - 0.36 + y), fit=(1.9, 0.18), depth=0.015, res=3)
    tube("Rule", [(-1.0, -0.06, zc - 0.2), (1.0, -0.06, zc - 0.2)], 0.012, gl, square=True, poly=True)
    for sx in (-1, 1):
        tube(f"Bracket{sx}", [(0, 0, 3.55), (sx * 0.5, 0, 3.52)], 0.03, ir, square=True, poly=True)
        tube(f"Scroll{sx}", [(sx * 0.5, 0, 3.52), (sx * 0.9, 0, 3.4), (sx * 1.1, 0, 3.52)], 0.025, ir)
    box("Crown", (0.8, 0.12, 0.1), (0, 0, zc + ph / 2 + 0.05), ir, bevel=0.02)
    B20.tprism("Crescent", WS.crescent(0.0, zc + ph / 2 + 0.38, 0.22, shift=0.4, tilt=0.6), 0.0, 0.05, K["brass"])
    return _dims()


# ================================================================== books

def book_pile(M):
    K = mats(M)
    rnd = random.Random(3030)
    flat_stack("A", -1.1, 0.2, 0.0, 9, rnd, K, yaw=10 * DEG, jitter=10)
    top = flat_stack("B", 0.7, -0.35, 0.0, 5, rnd, K, yaw=-20 * DEG, jitter=7)
    s = _mark()
    open_book("Open", "Pages_Moon", 1.5, 1.0, Matrix.Identity(4), M, K, cover="crimson", lift=0.12)
    _xform(s, T(0.7, -0.35, top) @ RZ(-14 * DEG))
    flat_stack("C", 1.6, 0.95, 0.0, 3, rnd, K, yaw=50 * DEG)
    return _dims()


def open_book_prop(M):
    K = mats(M)
    # the cushion: a plump crimson velvet pillow with gilt tassels at its corners
    box("Cushion", (2.5, 1.7, 0.42), (0, 0, 0.21), K["velvet"], bevel=0.19, segments=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"TasselKnot{sx}{sy}", 0.05, (sx * 1.2, sy * 0.8, 0.21), K["gilt"], seg=8, rings=4)
            cone(f"Tassel{sx}{sy}", 0.05, 0.02, 0.16, (sx * 1.25, sy * 0.85, 0.13), K["gilt"], verts=8)
    s = _mark()
    open_book("Book", "Pages_Moon", 2.0, 1.35, Matrix.Identity(4), M, K, cover="crimson")
    _xform(s, T(0, 0, 0.4))
    return _dims()


def scroll_rack(M):
    K = mats(M)
    rnd = random.Random(3032)
    W, D, H = 4.0, 1.4, 4.2
    box("Plinth", (W + 0.1, D + 0.05, 0.3), (0, 0, 0.15), K["ebony"], bevel=0.03)
    for sx in (-1, 1):
        box(f"Side{sx}", (0.16, D, H - 0.3), (sx * (W / 2 - 0.08), 0, 0.3 + (H - 0.3) / 2), K["oak"], bevel=0.025)
    box("Top", (W + 0.2, D + 0.1, 0.14), (0, -0.05, H + 0.07), K["oak"], bevel=0.04)
    box("Floor", (W - 0.32, D, 0.08), (0, 0, 0.34), K["oak"], bevel=0.0)
    box("Back", (W - 0.32, 0.06, H - 0.38), (0, D / 2 - 0.03, 0.38 + (H - 0.38) / 2), K["back"], bevel=0.0)
    # the diamond lattice: boards along z - z0 = +-(x - c), clipped to the opening
    x0, x1, z0, z1 = -W / 2 + 0.16, W / 2 - 0.16, 0.38, H
    step = 0.85
    for sgn in (-1, 1):
        for k in range(-8, 9):
            c = k * step
            pts = []
            for x in (x0, x1):
                z = z0 + sgn * (x - c)
                if z0 - 1e-6 <= z <= z1 + 1e-6:
                    pts.append((x, z))
            for z in (z0, z1):
                x = c + (z - z0) * sgn
                if x0 - 1e-6 <= x <= x1 + 1e-6:
                    pts.append((x, z))
            pts = sorted(set((round(a, 4), round(b, 4)) for a, b in pts))
            if len(pts) < 2:
                continue
            (ax, az), (bx, bz) = pts[0], pts[-1]
            L = math.hypot(bx - ax, bz - az)
            if L < 0.2:
                continue
            box(f"Lat{sgn}{k + 8}", (L, D - 0.1, 0.05), ((ax + bx) / 2, -0.02, (az + bz) / 2), K["oak"], bevel=0.008, rot=(0, -sgn * 45 * DEG, 0))
    # scrolls in the diamond cells: cell centres at x = (i + j + 1) step / 2, z = z0 + (j - i) step / 2
    tags = 0
    lay = {1: [(0.0, 0.0)], 2: [(-0.1, -0.06), (0.1, -0.06)], 3: [(-0.1, -0.07), (0.1, -0.07), (0.0, 0.1)]}
    for i in range(-10, 10):
        for j in range(-10, 10):
            cx = (i + j + 1) * step / 2
            cz = z0 + (j - i) * step / 2
            if not (x0 + 0.3 < cx < x1 - 0.3 and z0 + 0.3 < cz < z1 - 0.3):
                continue
            n = rnd.choice((1, 2, 2, 3))
            for m, (ox, oz) in enumerate(lay[n]):
                r = rnd.uniform(0.07, 0.09)
                Lr = rnd.uniform(0.9, D - 0.3)
                y = -D / 2 + Lr / 2 + rnd.uniform(-0.15, 0.0)
                # light on triangles: there are about eighty of them (a mesh may carry 20,000)
                cyl(f"Scroll{i}_{j}_{m}", r, Lr, (cx + ox, y, cz + oz), K["paper"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
                for e in (-1, 1):
                    cyl(f"Knob{i}_{j}_{m}_{e}", r * 0.55, 0.1, (cx + ox, y + e * (Lr / 2 + 0.05), cz + oz), K["ebony"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)
                if m == 0 and tags < 8 and rnd.random() < 0.5:
                    yy = y - Lr / 2 - 0.1
                    tube(f"TagCord{tags}", [(cx + ox, yy, cz + oz), (cx + ox + 0.04, yy - 0.03, cz + oz - 0.12)], 0.006, K["paper"], poly=True)
                    plate(f"Tag{tags}", f"Tag_{tags}", 0.13, 0.13, 0.008, T(cx + ox + 0.05, yy - 0.035, cz + oz - 0.2), K["atlas"], edge="bone", k=1.5)
                    tags += 1
    return _dims()


def book_cart(M):
    K = mats(M)
    rnd = random.Random(3033)
    W, D, H = 3.8, 1.6, 3.2
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.06)
        for sy in (-1, 1):
            tube(f"Post{sx}{sy}", [(x, sy * (D / 2 - 0.06), 0.4), (x, sy * (D / 2 - 0.06), H)], 0.05, K["iron"], square=True, poly=True)
            box(f"Fork{sx}{sy}", (0.12, 0.2, 0.14), (x, sy * (D / 2 - 0.06), 0.38), K["iron"], bevel=0.02)
            cyl(f"Wheel{sx}{sy}", 0.2, 0.08, (x, sy * (D / 2 - 0.06), 0.2), K["iron"], rot=(0, math.pi / 2, 0), verts=18, bevel=0.01)
            cyl(f"Hub{sx}{sy}", 0.07, 0.1, (x, sy * (D / 2 - 0.06), 0.2), K["brass"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.01)
        tube(f"Handle{sx}", [(x, -D / 2 + 0.06, H), (x + sx * 0.3, -D / 2 + 0.06, H + 0.25), (x + sx * 0.3, D / 2 - 0.06, H + 0.25), (x, D / 2 - 0.06, H)], 0.035,
             K["brass"], poly=True)
    for k, z in enumerate((0.55, 1.85)):
        box(f"Tier{k}", (W - 0.2, D - 0.1, 0.1), (0, 0, z - 0.05), K["oak"], bevel=0.015)
        box(f"Rail{k}", (W - 0.2, 0.05, 0.16), (0, -D / 2 + 0.04, z + 0.06), K["ebony"], bevel=0.01)
        box(f"RailB{k}", (W - 0.2, 0.05, 0.16), (0, D / 2 - 0.04, z + 0.06), K["ebony"], bevel=0.01)
        box(f"Spine{k}", (W - 0.2, 0.06, 1.0), (0, 0, z + 0.5), K["back"], bevel=0.0)
        fill_row(f"F{k}", -W / 2 + 0.15, W / 2 - 0.15, z, -D / 2 + 0.08, D / 2 - 0.14, 1.2, rnd, K, p_flat=0.05)
        s = _mark()
        fill_row(f"B{k}", -W / 2 + 0.15, W / 2 - 0.15, z, -D / 2 + 0.08, D / 2 - 0.14, 1.2, rnd, K, p_flat=0.05, fill=0.7)
        _xform(s, RZ(math.pi))
    box("TopTray", (W - 0.2, D - 0.1, 0.08), (0, 0, H + 0.04), K["oak"], bevel=0.015)
    flat_stack("Top", -0.6, 0.0, H + 0.08, 4, rnd, K, yaw=6 * DEG)
    return _dims()


def returns_box(M):
    K = mats(M)
    rnd = random.Random(3034)
    W, D, H = 2.8, 2.0, 3.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Leg{sx}{sy}", (0.22, 0.22, 0.6), (sx * (W / 2 - 0.15), sy * (D / 2 - 0.15), 0.3), K["ebony"], bevel=0.03)
    box("Body", (W, D, H - 0.6), (0, 0, 0.6 + (H - 0.6) / 2), K["oak"], bevel=0.03)
    box("Lid", (W + 0.16, D + 0.16, 0.14), (0, 0, H + 0.07), K["oak"], bevel=0.04)
    for j, z in enumerate((0.85, H - 0.25)):
        box(f"Band{j}", (W + 0.04, D + 0.04, 0.12), (0, 0, z), K["iron"], bevel=0.012)
    for sx in (-1, 1):
        box(f"Strap{sx}", (0.12, D + 0.04, H - 0.62), (sx * 0.95, 0, 0.6 + (H - 0.62) / 2), K["iron"], bevel=0.012)
        for j, z in enumerate((1.2, 1.9, 2.6)):
            sphere(f"Stud{sx}{j}", 0.03, (sx * 0.95, -D / 2 - 0.025, z), K["iron"], seg=6, rings=3)
    # the brass slot plate with a thin book half posted (lying flat, its spine to the right)
    box("SlotPlate", (1.4, 0.04, 0.5), (0, -D / 2 - 0.02, 2.4), K["brass"], bevel=0.015)
    box("Slot", (1.1, 0.02, 0.18), (0, -D / 2 - 0.035, 2.4), K["ink"], bevel=0.0)
    thin = [d for d in DESIGNS if d["w"] <= 0.15 and d["h"] <= 1.0 and not d["set"]]
    dz = thin[3] if len(thin) > 3 else DESIGNS[0]
    book("Posted", dz, 0.9, T(0, -D / 2 - 0.15, 2.4) @ RZ(-math.pi / 2) @ RY(-90 * DEG) @ T(0, 0, -dz["h"] / 2), K["atlas"])
    box("PlaqueFrame", (1.7, 0.04, 0.58), (0, -D / 2 - 0.02, 1.55), K["gilt"], bevel=0.012)
    plate("Plaque", "Plaque_RETURNS", 1.56, 0.45, 0.03, T(0, -D / 2 - 0.055, 1.55), K["atlas"])
    box("Hasp", (0.2, 0.05, 0.4), (0, -D / 2 - 0.045, H - 0.12), K["iron"], bevel=0.01)
    flat_stack("Top", 0.4, 0.1, H + 0.14, 3, rnd, K, yaw=-12 * DEG)
    return _dims()


# ================================================================== atmosphere

def web(prefix, corner, u, v, size, K, rnd, spokes=7, rings=6, sag=0.12):
    """A corner cobweb between two edges u and v (unit vectors from the corner): spokes fanning out and sagging threads."""
    c, u, v = Vector(corner), Vector(u).normalized(), Vector(v).normalized()
    out = (u + v).normalized()
    ends = []
    for k in range(spokes):
        t = k / (spokes - 1)
        d = (u * (1 - t) + v * t).normalized()
        L = size * rnd.uniform(0.85, 1.05) * (1.0 if 0 < k < spokes - 1 else 1.1)
        ends.append((d, L))
        tube(f"{prefix}Spoke{k}", [tuple(c), tuple(c + d * L)], 0.007, K["web"], square=True, poly=True)
        uvk(P.PARTS[-1], 0.25)
    for r in range(1, rings + 1):
        f = r / (rings + 0.5)
        pts = [c + d * L * f for d, L in ends]
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            m = (a + b) / 2 - out * sag * f * (b - a).length
            uvk(tube(f"{prefix}Ring{r}{k}", [tuple(a), tuple(m), tuple(b)], 0.005, K["web"], square=True, poly=True), 0.25)


def corner_web(prefix, c, dirs, lens, K, rnd, spokes=4, rings=6, sag=0.08):
    """A sheet web across a corner: a triangle with one corner along each direction from c (so its edges lie on the planes
    between them), spokes from its centre to its edges, and concentric threads sagging a little."""
    c = Vector(c)
    P_ = [c + Vector(d).normalized() * L for d, L in zip(dirs, lens)]
    hub = (P_[0] + P_[1] + P_[2]) / 3
    edge_pts = []
    for a, b in zip(P_, P_[1:] + P_[:1]):
        for k in range(spokes):
            edge_pts.append(a.lerp(b, (k + rnd.uniform(0.15, 0.4)) / spokes))
    for k, e in enumerate(edge_pts):
        uvk(tube(f"{prefix}Spoke{k}", [tuple(hub), tuple(e)], 0.006, K["web"], square=True, poly=True), 0.25)
    down = Vector((0, 0, -1))
    for r in range(1, rings + 1):
        f = r / (rings + 0.6)
        pts = [hub.lerp(e, f) for e in edge_pts]
        for k in range(len(pts)):
            a, b = pts[k], pts[(k + 1) % len(pts)]
            m = (a + b) / 2 + down * sag * (b - a).length
            uvk(tube(f"{prefix}Ring{r}_{k}", [tuple(a), tuple(m), tuple(b)], 0.0045, K["web"], square=True, poly=True), 0.25)


def shelf_dusty(M):
    K = mats(M)
    rnd = random.Random(3040)
    W, D, H = 6.0, 1.7, 10.4
    rows_ = case(K, W, D, H, 7, plaque="Cat_FOLKLORE")
    for i, (z, hm) in enumerate(rows_):
        fill_row(f"R{i}", -W / 2 + 0.26, W / 2 - 0.26, z, -D / 2 + 0.12, D - 0.3, hm, rnd, K, p_gap=0.16, p_lean=0.18, fill=rnd.uniform(0.6, 1.0))
    # cobwebs in the front corners of shelves (between the side and the shelf above), threads hanging from lips
    for k, i in enumerate((1, 3, 4, 6)):
        z_top = rows_[i][0] + rows_[i][1] + 0.05
        sx = -1 if k % 2 == 0 else 1
        web(f"W{k}", (sx * (W / 2 - 0.23), -D / 2 + 0.05, z_top), (-sx, 0, 0), (0, 0, -1), 0.7, K, rnd)
    for k in range(7):
        i = rnd.randint(1, 6)
        z = rows_[i][0] - 0.1
        x = rnd.uniform(-W / 2 + 0.5, W / 2 - 0.5)
        tube(f"Thread{k}", [(x, -D / 2 - 0.05, z - 0.05), (x + rnd.uniform(-0.05, 0.05), -D / 2 - 0.06, z - rnd.uniform(0.3, 0.7))], 0.004, K["web"], square=True,
             poly=True)
    # webs behind the crest (between the cornice top and the crest's back) and on the floor by the side
    for k, x in enumerate((-0.45, 0.45)):
        web(f"Crest{k}", (x, -D / 2 + 0.25, H + 0.265), (0, 0, 1), (0, 1, 0), 0.55, K, rnd, spokes=5, rings=4)
    web("Foot", (W / 2 + 0.04, -D / 2 + 0.4, 0.002), (0, 0, 1), (1, 0, 0), 0.6, K, rnd, spokes=5, rings=4)
    # a candle stub in a puddle of wax on the third shelf, and books fallen on the floor
    z1 = rows_[2][0]
    cyl("WaxPool", 0.22, 0.02, (2.3, -0.3, z1 + 0.012), K["wax"], verts=16, bevel=0.005)
    cyl("Stub", 0.07, 0.14, (2.3, -0.3, z1 + 0.09), K["wax"], verts=12, bevel=0.01)
    flat_stack("Fallen", -1.4, -D / 2 - 0.9, 0.0, 2, rnd, K, yaw=35 * DEG)
    flat_stack("Fallen2", 1.2, -D / 2 - 1.3, 0.0, 1, rnd, K, yaw=-70 * DEG)
    dustify(0.75)
    return _dims()


def shelf_toppled(M):
    K = mats(M)
    rnd = random.Random(3041)
    W, D, H = 6.0, 1.6, 8.4
    s = _mark()
    rows_ = case(K, W, D, H, 5, plaque="Cat_MATHEMATICS", crest=False)
    # a few books left in each compartment, lying on the back boards (it fell on its back)
    for i, (z, hm) in enumerate(rows_):
        # books tumbled onto the back boards, a few more lying on top of them
        under = []
        for k in range(rnd.randint(3, 5)):
            d = rnd.choice([q for q in _fits(min(hm * 0.7, 0.95)) if q["w"] <= 0.27])
            x = rnd.uniform(-W / 2 + 0.75, W / 2 - 0.75)
            if any(abs(x - a) < 0.95 for a, _ in under):
                continue
            under.append((x, d["w"]))
            book(f"In{i}a{k}", d, d["h"] * 0.72, T(x, D / 2 - 0.089 - d["w"] / 2, z + 0.06 + d["h"] / 2) @ RY(rnd.uniform(-0.3, 0.3)) @ RZ(math.pi / 2) @
                 T(0, 0, -d["h"] / 2), K["atlas"])
        for k, (x, w0) in enumerate(rnd.sample(under, min(len(under), rnd.randint(1, 2)))):
            d = rnd.choice([q for q in _fits(min(hm * 0.7, 0.92)) if q["w"] <= 0.24])
            book(f"In{i}b{k}", d, d["h"] * 0.72, T(x + rnd.uniform(-0.1, 0.1), D / 2 - 0.089 - w0 - 0.004 - d["w"] / 2, z + 0.1 + d["h"] / 2) @
                 RY(rnd.uniform(-0.25, 0.25)) @ RZ(math.pi / 2) @ T(0, 0, -d["h"] / 2), K["atlas"])
    _xform(s, RZ(98 * DEG) @ RX(-90 * DEG) @ T(0, 0, -(H + 0.3) / 2))
    bpy.context.view_layer.update()
    lo = min((ob.matrix_world @ Vector(c)).z for ob in P.PARTS for c in ob.bound_box)
    for ob in P.PARTS:
        ob.matrix_world = T(0, 0, -lo) @ ob.matrix_world
    # books spilled round it, kept off its footprint (W x H, turned 98 degrees) and apart from each other
    spots = []
    tries = 0
    ca, sa = math.cos(-98 * DEG), math.sin(-98 * DEG)
    while len(spots) < 24 and tries < 4000:
        tries += 1
        x, y = rnd.uniform(-6.5, 6.5), rnd.uniform(-6.5, 6.5)
        cx, cy = x * ca - y * sa, x * sa + y * ca
        if abs(cx) < W / 2 + 0.75 and abs(cy) < (H + 0.3) / 2 + 0.75:
            continue
        # most of them on the side it fell from (its front used to face -Y; it went over backwards toward +cx)
        if abs(cx) > W / 2 + (2.2 if cx > 0 else 1.3) or abs(cy) > (H + 0.3) / 2 + 1.0:
            continue
        if any(math.hypot(x - a, y - b) < 0.85 for a, b in spots):
            continue
        spots.append((x, y))
    for k, (x, y) in enumerate(spots):
        if k % 5 == 0:
            s = _mark()
            open_book(f"Open{k}", ["Pages_Moon", "Pages_Raven", "Pages_Rules"][k % 3], 1.3, 0.9, Matrix.Identity(4), M, K, cover="ebony", lift=0.1)
            _xform(s, T(x, y, 0) @ RZ(rnd.uniform(0, 2 * math.pi)))
        else:
            flat_stack(f"Spill{k}", x, y, 0.0, rnd.choice((1, 1, 2)), rnd, K, yaw=rnd.uniform(0, 2 * math.pi), jitter=25, hmax=1.1)
    return _dims()


def cobweb_corner(M):
    K = mats(M)
    rnd = random.Random(3042)
    # the corner: two walls meeting at the back (at +Y, like LibShelfCorner) under a ceiling; turn it 45 degrees for a square room
    c = (0.0, 1.5, 3.4)
    L_, R_, Dn = (-1, -1, 0), (1, -1, 0), (0, 0, -1)
    corner_web("A", c, (L_, R_, Dn), (2.2, 2.0, 2.4), K, rnd, spokes=4, rings=8, sag=0.1)
    corner_web("B", (0.0, 1.5, 1.7), (L_, R_, Dn), (1.0, 1.2, 0.9), K, rnd, spokes=3, rings=5, sag=0.06)
    for k in range(6):
        t = rnd.uniform(-1.3, 1.3)
        x, y = t * 0.707, 1.5 - abs(t) * 0.707
        tube(f"Strand{k}", [(x, y, 3.4), (x + rnd.uniform(-0.08, 0.08), y - 0.04, 3.4 - rnd.uniform(0.4, 1.1))], 0.0045, K["web"], square=True, poly=True)
    bpy.context.view_layer.update()
    lo = min((ob.matrix_world @ Vector(cc)).z for ob in P.PARTS for cc in ob.bound_box)
    for ob in P.PARTS:
        ob.matrix_world = T(0, 0, -lo) @ ob.matrix_world
    return _dims()


# ------------------------------------------------------------------ bake UV: extra room for the titles

_base_bake_uv = P.bake_uv


def _scale_islands(ob):
    """In edit mode: scale each UV island by the largest nh_uvk of its faces (book spines and printed faces up, hidden boards
    down)."""
    me = ob.data
    bm = bmesh.from_edit_mesh(me)
    kl = bm.faces.layers.float.get("nh_uvk")
    if kl is None:
        return
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv["Bake"]
    parent = list(range(len(bm.faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        ls = list(e.link_loops)
        if len(ls) != 2:
            continue
        a, b = ls
        if (a[uvl].uv - b.link_loop_next[uvl].uv).length < 1e-6 and (a.link_loop_next[uvl].uv - b[uvl].uv).length < 1e-6:
            ra, rb = find(a.face.index), find(b.face.index)
            if ra != rb:
                parent[ra] = rb
    islands = {}
    for f in bm.faces:
        islands.setdefault(find(f.index), []).append(f)
    for faces in islands.values():
        k = max((f[kl] if f[kl] > 0 else 1.0) for f in faces)
        if abs(k - 1.0) < 1e-3:
            continue
        loops = [lp for f in faces for lp in f.loops]
        c = sum((lp[uvl].uv for lp in loops), Vector((0, 0))) / len(loops)
        for lp in loops:
            lp[uvl].uv = c + (lp[uvl].uv - c) * k
    bmesh.update_edit_mesh(me)


def _unfold_books(objs):
    """Lay every book out as the single island stored in its Unfold layer, at the kit's texel density (measured on the other
    islands after average_islands_scale), so the bake has a few hundred book islands rather than thousands of faces."""
    num = den = 0.0
    data = []
    for ob in objs:
        bm = bmesh.from_edit_mesh(ob.data)
        bl = bm.faces.layers.int.get("nh_book")
        ufl = bm.loops.layers.uv.get("Unfold")
        uvl = bm.loops.layers.uv["Bake"]
        data.append((ob, bm, bl, ufl, uvl))
        for f in bm.faces:
            if bl is not None and f[bl]:
                continue
            a3 = f.calc_area()
            if a3 < 1e-8:
                continue
            pts = [lp[uvl].uv for lp in f.loops]
            a2 = abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
            num += a2
            den += a3
    if den <= 0:
        return
    s0 = math.sqrt(num / den)
    for ob, bm, bl, ufl, uvl in data:
        if bl is None or ufl is None:
            continue
        for f in bm.faces:
            if f[bl]:
                for lp in f.loops:
                    lp[uvl].uv = lp[ufl].uv * s0
        bmesh.update_edit_mesh(ob.data)


def _fit_unit(objs):
    """Squeeze every bake UV back into 0..1 (one uniform scale), so the pack keeps them in the first tile."""
    lo, hi = Vector((9e9, 9e9)), Vector((-9e9, -9e9))
    bms = []
    for ob in objs:
        bm = bmesh.from_edit_mesh(ob.data)
        uvl = bm.loops.layers.uv["Bake"]
        bms.append((ob, bm, uvl))
        for f in bm.faces:
            for lp in f.loops:
                u = lp[uvl].uv
                lo.x, lo.y, hi.x, hi.y = min(lo.x, u.x), min(lo.y, u.y), max(hi.x, u.x), max(hi.y, u.y)
    sc = 0.98 / max(hi.x - lo.x, hi.y - lo.y, 1e-6)
    for ob, bm, uvl in bms:
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (lp[uvl].uv - lo) * sc + Vector((0.01, 0.01))
        bmesh.update_edit_mesh(ob.data)


def _dbg_bounds(objs, tag):
    lo, hi = [9.0, 9.0], [-9.0, -9.0]
    for ob in objs:
        bm = bmesh.from_edit_mesh(ob.data)
        uvl = bm.loops.layers.uv["Bake"]
        for f in bm.faces:
            for lp in f.loops:
                for i in (0, 1):
                    lo[i], hi[i] = min(lo[i], lp[uvl].uv[i]), max(hi[i], lp[uvl].uv[i])
    print(f"[props] {tag}: {len(objs)} objs, uv {lo} .. {hi}")


def bake_uv_weighted(objs):
    if not any(o.data.attributes.get("nh_uvk") is not None or o.data.attributes.get("nh_book") is not None for o in objs):
        return _base_bake_uv(objs)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        uv = ob.data.uv_layers.new(name="Bake")
        ob.data.uv_layers.active = uv
        uv.active_render = True
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    # a book is a plain box, so each of its faces is an island of its own and can be weighted on its own
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, area_weight=0.6)
    bpy.ops.uv.average_islands_scale()
    _unfold_books(objs)
    for ob in objs:
        _scale_islands(ob)
    _fit_unit(objs)
    bpy.ops.uv.pack_islands(udim_source="ACTIVE_UDIM", scale=True, rotate=True, margin_method="FRACTION", margin=8 / P.SIZE, shape_method="CONCAVE")
    # the pack keeps the islands' scale; if they overrun the tile, shrink the whole packed layout to fit (a pack run a second
    # time on an overrun layout collapses it to a point, which baked black)
    _fit_unit(objs)
    lo, hi, area = [9.0, 9.0], [-9.0, -9.0], 0.0
    for ob in objs:
        bm = bmesh.from_edit_mesh(ob.data)
        uvl = bm.loops.layers.uv["Bake"]
        for f in bm.faces:
            pts = [lp[uvl].uv for lp in f.loops]
            area += abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
            for p_ in pts:
                for i in (0, 1):
                    lo[i], hi[i] = min(lo[i], p_[i]), max(hi[i], p_[i])
    print(f"[props] bake UV bounds {lo[0]:.3f},{lo[1]:.3f} .. {hi[0]:.3f},{hi[1]:.3f}, islands cover {area:.0%}")
    if area < 0.05 or hi[0] > 1.01 or hi[1] > 1.01:
        raise RuntimeError("bake UV layout is broken (outside the tile or collapsed)")
    bpy.ops.object.mode_set(mode="OBJECT")


P.bake_uv = bake_uv_weighted


BUILDERS = {
    "LibShelfTall": lib_shelf_tall,
    "LibShelfArched": lib_shelf_arched,
    "LibShelfCorner": lib_shelf_corner,
    "LibShelfDouble": lib_shelf_double,
    "LibShelfLadder": lib_shelf_ladder,
    "LibShelfHalf": lib_shelf_half,
    "ShelfEndCap": shelf_end_cap,
    "ForbiddenCage": forbidden_cage,
    "ChainedBookcase": chained_bookcase,
    "ReadingTableLong": reading_table_long,
    "ReadingTableRound": reading_table_round,
    "StudyCarrel": study_carrel,
    "LibraryChair": library_chair,
    "CirculationDesk": circulation_desk,
    "Lectern": lectern,
    "CardCatalogue": card_catalogue,
    "MapChest": map_chest,
    "NewspaperRack": newspaper_rack,
    "StepStool": step_stool,
    "RollingLadder": rolling_ladder,
    "TerrestrialGlobe": terrestrial_globe,
    "ArmillarySphere": armillary_sphere,
    "BankerLamp": banker_lamp,
    "CandleLamp": candle_lamp,
    "LibCandelabra": lib_candelabra,
    "LibrarianBust": librarian_bust,
    "LibraryClock": library_clock,
    "SilenceSign": silence_sign,
    "BookPile": book_pile,
    "OpenBook": open_book_prop,
    "ScrollRack": scroll_rack,
    "BookCart": book_cart,
    "ReturnsBox": returns_box,
    "ShelfDusty": shelf_dusty,
    "ShelfToppled": shelf_toppled,
    "CobwebCorner": cobweb_corner,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.05 for n in BUILDERS})
P.PREVIEW_PAD.update({"BankerLamp": 1.3, "CandleLamp": 1.2, "LibCandelabra": 1.25, "OpenBook": 1.3, "ShelfToppled": 1.0, "ReadingTableLong": 1.0,
                      "CirculationDesk": 1.0, "CobwebCorner": 1.2})
