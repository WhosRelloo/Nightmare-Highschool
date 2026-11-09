"""Props batch 40, the courtyard / garden kit, for nh_props.py: a haunted gothic academy garden at night. The school's black
wrought iron, weathered limestone (lichen rosettes, rain streaks), cleft slate, aged brass and moss, crimson and violet accents;
elegant and eerie, never gory. Every prop has one signature idea; glows are moonlight blue-white, candle amber or faint violet.

Pathways (10-stud grid; path top about 0.3)
  PathFlagstone, PathFlagstoneCurve, PathFlagstoneJunction, PathFlagstoneCross   hand-cut flags laid by eye over a moss bed, edges
                      bleeding into the grass, a cracked stone with a root through it, a worn carving (garden_atlas.py runes)
  PathCrazyPaving, PathPuddleFlag                         broken slate / limestone / sandstone; a hollow of sunken stones (Glass)
  PathCobble, PathCobbleCurve    fan-laid cobble (Path: NH_GardenCobble; the curve's UVs bend the fans), iron S-curl kerbs
  PathGravel, PathGravelCurve    crushed slate and petals (Path: NH_GardenGravel), bat-wing scalloped stone edging
  PathHerringbone                sooty crimson herringbone (Path: NH_HerringboneBrick), a soldier course, one brick toppled
  PathMoonRoundel                the carved compass of moon phases round the crescent-and-shield Inlay (MoonRoundelInlay)
  SteppingStones, GardenSteps (worn hollows), PathEdgingIron (scrolls), PathBridgeSlab (a rill, Glass), PathGateArch (lantern)
Plants  RoseBushCrimson, RoseBushBlack, HedgeStraight (lancet top), HedgeBattlement, HedgeCorner (tower), HedgeEnd (obelisk),
        HedgeArchway, HedgeWolf, HedgeRaven (estate topiary), WeepingWillow, YewTree, GnarledCrabapple (hunched), CypressPair,
        IvyWallPanel, WisteriaPergola, FernCluster, LavenderBed, RaisedFlowerBed, MushroomRing (glowing gills), MoonflowerPatch,
        TallGrassClump, ThornBramble, NightshadeShrub (glowing berries), PumpkinPatch, PoppyBed, LilyPads, BloodRoseUrn, GhostOrchid
Features  KoiPond (kidney, toad spitter), BirdBath (stone hand), GardenBench (raven-wing back), CurvedStoneBench, LogBench,
          IronGazebo (onion dome, bat-wing brackets), RoseArbor, GardenObelisk (moon phases), UrnPedestal (serpent handles),
          LowGardenWall, GardenWallPier, StoneLanternPost (twisted column, caged flame), Wheelbarrow, GardenToolsLean,
          PottingCluster, ColdFrame, TrellisPanel, KeepOffGrassSign, Birdhouse (a chapel), Scarecrow, CourtyardBenchTable, CrowPerch

Pieces: Main, plus <Prop>_Leaves (alpha-cut cards on NH_GardenLeaves, nh_props.ATLAS, custom normals from the "nh_n" attribute;
AlphaMode = Transparency and DoubleSided in Roblox), _Path (tiled sets, nh_props.TILED, 10 studs a tile), _Inlay, _Glass, _Glow.
Front faces -Y, Z is up, the origin is at the bottom centre. Every piece is under 20k triangles. Registered into nh_props.BUILD.
"""
import json
import math
import os
import random
import zlib

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, _mark, _xform, _dims, flat
from nh_props_batch24 import _text, _fine, sweep, _paint, _math, _coords, _mix_rgb
import nh_props_batch24 as B24
import nh_props_batch30 as B30
from nh_props_batch20 import tprism

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = "C:/Windows/Fonts/palab.ttf"
ART = os.path.normpath(os.path.join(P.HERE, "..", "textures"))
ATL = json.load(open(os.path.join(P.HERE, "garden_atlas.json")))["leaves"]
UP = Vector((0, 0, 1))


# ================================================================== materials

def mossy(m, amount=0.5, scale=1.4, col=(0.05, 0.085, 0.025), low=0.0):
    """Moss on the faces that look up (and low down, `low` studs), in noisy patches, painted into a P.material."""
    nt = m.node_tree
    co = _coords(nt)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 9.0
    nz.inputs["Roughness"].default_value = 0.68
    nt.links.new(co, nz.inputs["Vector"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    up = _math(nt, "ADD", _math(nt, "MULTIPLY", sep.outputs[2], 0.7), 0.3, clamp=True)
    if low:
        sp = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sp.inputs[0])
        lo = _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", sp.outputs[2], low), clamp=True)
        up = _math(nt, "MAXIMUM", up, lo)
    patch = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.62 - amount * 0.28), 7.0, clamp=True)
    mask = _math(nt, "MULTIPLY", patch, up, clamp=True)
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = scale * 9
    nt.links.new(co, nz2.inputs["Vector"])
    shade = _mix_rgb(nt, nz2.outputs["Fac"], tuple(c * 0.55 for c in col), tuple(min(1, c * 1.7) for c in col))
    _paint(m, mask, shade, rough=0.95)
    return m


def leafy_core(name, rgb=(0.025, 0.05, 0.02)):
    """The dark leafy mass under a plant's cards (so you can't see through it): speckled greens."""
    m = flat(name, rgb, 0.85, dirt=0.4)
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 9.0
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", vo.outputs["Distance"], 0.25), 1.6, clamp=True),
           tuple(c * 1.5 for c in rgb), rough=0.75)
    B24._bump(m, vo.outputs["Distance"], 0.05, 0.6)
    return m


def gk(M):
    """The garden kit's materials."""
    lime = mossy(material("GardenLime", "NH_Limestone", tint=(0.66, 0.64, 0.58), scale=0.3, wear=0.4, dirt=1.0, rough_add=0.05), 0.55, low=0.6)
    limel = mossy(material("GardenLimeLight", "NH_Limestone", tint=(0.74, 0.72, 0.66), scale=0.3, wear=0.35, dirt=0.9), 0.2)
    gran = mossy(material("Granite", "NH_Slate", tint=(0.22, 0.22, 0.24), scale=0.5, rough_mul=0.6, rough_add=0.3, normal=0.6, wear=0.3, dirt=0.9), 0.35)
    wall = mossy(material("GardenWallStone", os.path.join(ART, "GothicStone", "GothicStone"), tint=(0.8, 0.8, 0.78), scale=0.16, metal=0.0, wear=0.3,
                          dirt=0.9), 0.6, low=1.2)
    bricks = [mossy(flat(f"GardenBrick{k}", c, 0.88, wear=0.25, dirt=0.9), 0.3, scale=2.5) for k, c in
              enumerate(((0.16, 0.05, 0.035), (0.2, 0.07, 0.045), (0.11, 0.035, 0.035)))]
    for b in bricks:
        B24._bump(b, _noise(b, 30.0), 0.02, 0.5)
    bark = material("GardenBark", os.path.join(P.OUT_TEX, "NH_GardenBark"), scale=0.45, metal=0.0, normal=1.0, wear=0.2, dirt=0.9)
    deadwood = material("DeadWood", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.85, 0.82, 0.8), scale=0.7, metal=0.0, normal=1.0, wear=0.4,
                        dirt=0.9)
    oak = material("GardenOak", "NH_DeskWood", tint=(0.34, 0.26, 0.19), scale=0.25, rough_add=0.12, wear=0.55, dirt=0.9)
    oakd = material("GardenOakDark", "NH_DeskWood", tint=(0.16, 0.1, 0.07), scale=0.25, rough_add=0.1, wear=0.5, dirt=0.9)
    return {
        "iron": M["iron"],
        "ironf": B24.iron_fine(),
        "brass": material("GardenBrass", "NH_Brass", tint=(1, 1, 1), scale=0.5, wear=0.25, dirt=0.75),
        "brassf": material("GardenBrassFine", base=(0.78, 0.56, 0.27), rough=0.3, metal=1.0, wear=0.3, dirt=0.75),
        "verd": mossy(flat("Verdigris", (0.14, 0.3, 0.25), 0.55, metal=0.3, wear=0.3, dirt=0.8), 0.2),
        "lime": lime, "limel": limel, "gran": gran, "wall": wall, "bricks": bricks, "slate": M["slate"],
        "bark": bark, "deadwood": deadwood, "oak": oak, "oakd": oakd,
        "core": leafy_core("LeafCore"), "coredark": leafy_core("LeafCoreDark", (0.014, 0.032, 0.022)),
        "soil": _soil(), "mulch": _soil("Mulch", (0.06, 0.04, 0.028), 18.0),
        "moss": material("Moss", os.path.join(ART, "MossyTurf", "MossyTurf"), scale=0.35, metal=0.0, normal=0.8, wear=0.0, dirt=0.6),
        "terra": mossy(flat("Terracotta", (0.36, 0.13, 0.07), 0.85, wear=0.35, dirt=0.9), 0.25, low=0.4),
        "crimson": flat("GardenCrimson", (0.16, 0.012, 0.022), 0.5, wear=0.2, dirt=0.6),
        "violet": flat("GardenViolet", (0.12, 0.05, 0.2), 0.5, wear=0.2, dirt=0.6),
        "bone": flat("GardenBone", (0.6, 0.56, 0.47), 0.6, dirt=0.6),
        "ink": flat("GardenInk", (0.015, 0.014, 0.018), 0.4, dirt=0.3),
        "zinc": flat("Zinc", (0.42, 0.44, 0.45), 0.42, metal=0.9, wear=0.3, dirt=0.9),
        "glass": flat("GardenGlass", (0.6, 0.65, 0.68), 0.1),
        "water": flat("GardenWater", (0.02, 0.04, 0.05), 0.05),
        "glow": flat("GardenGlow", (1.0, 0.7, 0.35), 0.5),
        "leaf": flat("LeafCard", (0.1, 0.2, 0.08), 0.6),
    }


def _noise(m, scale):
    nt = m.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(_coords(nt), nz.inputs["Vector"])
    return nz.outputs["Fac"]


def _soil(name="GardenSoil", rgb=(0.045, 0.032, 0.024), clods=10.0):
    m = flat(name, rgb, 0.95, dirt=0.5)
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = clods
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    B24._bump(m, vo.outputs["Distance"], 0.06, 0.9)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", _noise(m, 40.0), 0.6), 4.0, clamp=True), (0.11, 0.09, 0.07), rough=0.9)
    return m


# ================================================================== geometry helpers

def mk(name, verts, faces, mat, smooth=True, bevel=0.0, tri=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if tri:
        md = ob.modifiers.new("Tri", "TRIANGULATE")
        md.quad_method = "BEAUTY"
        md.ngon_method = "BEAUTY"
    return _finish(ob, mat, bevel, segments=1)


def poly_slab(name, outline, z0, z1, mat, bottom=False, bevel=0.0, smooth=False):
    """A flat outline [(x, y)...] (counter-clockwise) extruded from z0 to z1; the top (and bottom) triangulated (beauty)."""
    n = len(outline)
    V = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    F = [tuple(range(n, 2 * n))]
    if bottom:
        F.append(tuple(reversed(range(n))))
    for i in range(n):
        j = (i + 1) % n
        F.append((i, j, n + j, n + i))
    return mk(name, V, F, mat, smooth=smooth, bevel=bevel, tri=True)


def ring_slab(name, c, r0, r1, a0, a1, z0, z1, mat, n=16, bevel=0.0, ends=True, inner=True, zfun=None):
    """An annular sector (angles in radians) from radius r0 to r1 round c = (x, y), z0 to z1 (zfun(x, y) can lift the top)."""
    V, F = [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        ca, sa = math.cos(a), math.sin(a)
        for r in (r0, r1):
            x, y = c[0] + ca * r, c[1] + sa * r
            V.append((x, y, z0))
            V.append((x, y, z1 + (zfun(x, y) if zfun else 0)))
    # per step: [r0 low, r0 high, r1 low, r1 high]
    for i in range(n):
        a, b = i * 4, (i + 1) * 4
        F.append((a + 1, a + 3, b + 3, b + 1))           # top
        F.append((a + 2, b + 2, b + 3, a + 3))           # outer
        if inner:
            F.append((a, a + 1, b + 1, b))               # inner
    if ends:
        F.append((0, 2, 3, 1))
        e = n * 4
        F.append((e, e + 1, e + 3, e + 2))
    ob = mk(name, V, F, mat, smooth=False, bevel=bevel)
    P_recalc(ob)
    return ob


def P_recalc(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def blob_outline(rx, ry, n, rng, amt=0.12, cx=0.0, cy=0.0):
    out = []
    ph = rng.uniform(0, 6.28)
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + amt * (math.sin(a * 2 + ph) * 0.5 + rng.uniform(-0.6, 0.6))
        out.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return out


def stone(name, cx, cy, rx, ry, z0, z1, mat, rng, n=10, bevel=0.06, rot=0.0):
    pts = blob_outline(rx, ry, n, rng, 0.14)
    ca, sa = math.cos(rot), math.sin(rot)
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    return poly_slab(name, pts, z0, z1, mat, bevel=bevel)


def bar(name, pts, r, mat, seg=6, caps=True):
    return sweep(name, pts, r, mat, seg=seg, caps=caps)


def blob(name, loc, r, mat, seg=10, rings=6, scale=(1, 1, 1), jitter=0.0, seed=0):
    ob = sphere(name, r, loc, mat, seg=seg, rings=rings, scale=scale)
    if jitter:
        g = random.Random(seed)
        for v in ob.data.vertices:
            v.co *= 1 + g.uniform(-jitter, jitter)
    return ob


def ringbar(name, c, r, axis, mat, thick=0.03, n=20, seg=5):
    """A closed ring of bar (cheaper than hoop for wide rings); axis is its normal ("X", "Y" or "Z")."""
    pts = []
    for i in range(n + 1):
        a = i / n * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        pts.append((c[0], c[1] + u, c[2] + v) if axis == "X" else (c[0] + u, c[1], c[2] + v) if axis == "Y" else (c[0] + u, c[1] + v, c[2]))
    return sweep(name, pts, thick, mat, seg=seg, caps=False)


def bez(p0, p1, p2, n=8):
    return [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2)) for t in [i / n for i in range(n + 1)]]


# ================================================================== leaf cards

def uvr(sprite, inset=2.5 / 2048):
    u0, v0, u1, v1 = ATL[sprite]["uv"]
    return u0 + inset, v0 + inset, u1 - inset, v1 - inset


def frame(n, roll=0.0, up=UP):
    """Card axes (across, up the card) for a card facing n, rolled about n."""
    n = Vector(n).normalized()
    ax = Vector(up).cross(n)
    if ax.length < 1e-4:
        ax = Vector((1, 0, 0))
    ax.normalize()
    ay = n.cross(ax)
    if roll:
        q = Matrix.Rotation(roll, 3, n)
        ax, ay = q @ ax, q @ ay
    return ax, ay


class Cards:
    """Alpha-cut leaf cards for one prop's Leaves piece: quads on NH_GardenLeaves sprites, with the normals each card should
    shade with (the "nh_n" attribute; nh_props.atlas_material makes them the custom normals)."""

    def __init__(self, rng):
        self.V, self.F, self.UV, self.N = [], [], [], []
        self.rng = rng

    def add(self, o, ax, ay, w, h, sprite, anchor="fill", bend=0.0, segs=1, nrm=None, flip=None):
        o, ax, ay = Vector(o), Vector(ax).normalized(), Vector(ay).normalized()
        fn = ax.cross(ay)
        u0, v0, u1, v1 = uvr(sprite)
        if flip is None:
            flip = self.rng.random() < 0.5
        if flip:
            u0, u1 = u1, u0
        bv = bend if isinstance(bend, Vector) else fn * bend
        base = len(self.V)
        for r in range(segs + 1):
            t = r / segs
            if anchor == "base":
                off, bt = t, t
            elif anchor == "top":
                off, bt = t - 1, 1 - t
            else:
                off, bt = t - 0.5, abs(t - 0.5) * 2
            for c in (0, 1):
                p = o + ax * ((c - 0.5) * w) + ay * (off * h) + bv * (bt * bt)
                self.V.append(p)
                self.UV.append((u0 + (u1 - u0) * c, v0 + (v1 - v0) * t))
                n = nrm(p, fn) if callable(nrm) else (Vector(nrm) if nrm is not None else fn)
                self.N.append(n.normalized() if n.length > 1e-6 else fn)
        for r in range(segs):
            a = base + r * 2
            self.F.append((a, a + 1, a + 3, a + 2))

    def build(self, name, M=None):
        if not self.V:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.V], [], self.F)
        me.update()
        uv = me.uv_layers.new(name="Bake")
        for poly in me.polygons:
            poly.use_smooth = True
            for li in poly.loop_indices:
                uv.data[li].uv = self.UV[me.loops[li].vertex_index]
        at = me.attributes.new("nh_n", "FLOAT_VECTOR", "POINT")
        for i, n in enumerate(self.N):
            at.data[i].vector = n
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        g = P.GROUP
        set_group("Leaves")
        _finish(ob, bpy.data.materials.get("LeafCard") or flat("LeafCard", (0.1, 0.2, 0.08), 0.6), 0)
        set_group(g)
        return ob

    # -- placements
    def blob(self, c, radii, n, sprite, size, outward=0.35, nscale=0.8, zmin=-1e9, keep=None):
        """n cards over an ellipsoid round c, facing out (with a random tilt), normals out of the ellipsoid."""
        c, R = Vector(c), Vector(radii)
        rng = self.rng
        k = 0
        tries = 0
        while k < n and tries < n * 6:
            tries += 1
            d = Vector((rng.normal(), rng.normal(), rng.normal()))
            if d.length < 1e-6:
                continue
            d.normalize()
            p = c + Vector((d.x * R.x, d.y * R.y, d.z * R.z)) * rng.uniform(0.82, 1.0)
            if p.z < zmin or (keep and not keep(p)):
                continue
            nn = Vector((d.x / R.x, d.y / R.y, d.z / R.z)).normalized()
            t = (nn + Vector((rng.normal(), rng.normal(), rng.normal())) * outward).normalized()
            ax, ay = frame(t, roll=rng.uniform(0, 6.28))
            s = size * rng.uniform(0.8, 1.2)
            self.add(p, ax, ay, s, s, sprite, "fill", nrm=lambda q, fn, nn=nn: nn * nscale + fn * (1 - nscale))
            k += 1

    def cover(self, ob, density, sprite, size, offset=0.08, tilt=0.35, zmin=0.15, keep=None, nscale=0.8, maxn=100000):
        """Cards over a core object's surface (area-weighted), facing out along its smooth normals."""
        rng = self.rng
        for p, n in surface_samples(ob, density, rng, maxn):
            if p.z < zmin or (keep and not keep(p, n)):
                continue
            t = (n + Vector((rng.normal(), rng.normal(), rng.normal())) * tilt).normalized()
            ax, ay = frame(t, roll=rng.uniform(0, 6.28))
            s = size * rng.uniform(0.8, 1.2)
            self.add(p + n * offset, ax, ay, s, s, sprite, "fill", nrm=lambda q, fn, n=n: n * nscale + fn * (1 - nscale))

    def crossed(self, pos, w, h, sprite, k=3, yaw=None, lean=0.12, up_n=0.65, bend=0.0):
        """k upright cards crossed at pos (anchored at their base): a clump of grass, lavender, poppies."""
        rng = self.rng
        yaw = rng.uniform(0, math.pi) if yaw is None else yaw
        for i in range(k):
            a = yaw + i * math.pi / k
            ax = Vector((math.cos(a), math.sin(a), 0))
            side = ax.cross(UP)
            ay = (UP + side * rng.uniform(-lean, lean)).normalized()
            self.add(pos, ax, ay, w * rng.uniform(0.85, 1.15), h * rng.uniform(0.85, 1.15), sprite, "base", segs=2 if bend else 1,
                     bend=bend, nrm=lambda q, fn: UP * up_n + fn * (1 - up_n))

    def hang(self, top, w, h, sprite, yaw=None, sway=0.15, segs=2):
        """A card hanging from `top` (willow strands, wisteria): faces a random way, normals outward and down a little."""
        rng = self.rng
        yaw = rng.uniform(0, 2 * math.pi) if yaw is None else yaw
        n = Vector((math.cos(yaw), math.sin(yaw), 0))
        ax, ay = frame(n)
        self.add(top, ax, ay, w, h, sprite, "top", segs=segs, bend=n * (h * sway), nrm=lambda q, fn: fn * 0.7 + UP * 0.3)

    def fronds(self, pos, n, L, w, sprite, elev=(30, 60), droop=0.35, segs=3, yaw0=0.0):
        """Fronds radiating from pos, rising at `elev` degrees and drooping at the tips (ferns, palms of grass)."""
        rng = self.rng
        for i in range(n):
            a = yaw0 + i / n * 2 * math.pi + rng.uniform(-0.25, 0.25)
            e = math.radians(rng.uniform(*elev))
            out = Vector((math.cos(a), math.sin(a), 0))
            ay = (out * math.cos(e) + UP * math.sin(e)).normalized()
            ax = UP.cross(out).normalized()
            ll = L * rng.uniform(0.8, 1.15)
            self.add(pos, ax, ay, w * ll / L, ll, sprite, "base", segs=segs, bend=Vector((0, 0, -ll * droop)),
                     nrm=lambda q, fn, out=out: UP * 0.6 + out * 0.4)


def surface_samples(ob, density, rng, maxn=100000):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    me.calc_loop_triangles()
    out = []
    for lt in me.loop_triangles:
        cnt = lt.area * density
        k = int(cnt) + (1 if rng.random() < cnt - int(cnt) else 0)
        vs = [me.vertices[i] for i in lt.vertices]
        for _ in range(k):
            r1, r2 = rng.random(), rng.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            w0 = 1 - r1 - r2
            p = vs[0].co * w0 + vs[1].co * r1 + vs[2].co * r2
            n = vs[0].normal * w0 + vs[1].normal * r1 + vs[2].normal * r2
            out.append((mw @ p, (nm @ n).normalized()))
            if len(out) >= maxn:
                break
    ev.to_mesh_clear()
    rng.shuffle(out)
    return out


def RNG(seed):
    import numpy as np
    return np.random.default_rng(seed)


# ================================================================== pathways

HALF = 3.0          # the paved band's half width
KW = 0.4            # edging width
PT = 0.3            # path top
ET = 0.42           # edging top


def _edge_unit(kind, K, name, L, rng):
    """One edging unit built along +X at the origin (centred), its inner face toward -Y."""
    if kind in ("flag", "crazy"):
        h = ET + rng.uniform(-0.02, 0.02)
        box(name, (L - 0.05, KW, h), (0, 0, h / 2), K["lime"], bevel=0.05 if kind == "flag" else 0.08, segments=1)
    elif kind == "cobble":
        h = 0.4 + rng.uniform(-0.03, 0.02)
        box(name, (L - 0.06, 0.36, h), (0, 0, h / 2), K["gran"], bevel=0.06, segments=1)
    elif kind == "gravel":       # a brick set on edge at 45 degrees: the dog-tooth edging
        b = K["bricks"][rng.integers(3)]
        ob = box(name, (0.5, 0.2, 0.25), (0, 0, 0), b, bevel=0.0)
        ob.matrix_world = T(0, 0, 0.27) @ RY(45 * DEG)
        bpy.context.view_layer.update()
    elif kind == "herring":      # a soldier course: bricks on end, across the edge
        b = K["bricks"][rng.integers(3)]
        box(name, (0.22, 0.42, 0.46), (0, 0, 0.23), b, bevel=0.0)


UNIT = {"flag": 2.5, "crazy": 2.5, "cobble": 1.25, "gravel": 0.5, "herring": 0.27}


def edge_run(kind, K, prefix, p0, p1, rng, unit=None):
    """Edging units from p0 to p1 (x, y), evenly."""
    unit = unit or UNIT[kind]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    n = max(1, round(L / unit))
    a = math.atan2(dy, dx)
    for i in range(n):
        t = (i + 0.5) / n
        s = _mark()
        _edge_unit(kind, K, f"{prefix}{i}", L / n, rng)
        _xform(s, T(p0[0] + dx * t, p0[1] + dy * t, 0) @ RZ(a))


SETS = {"flag": "NH_MossyPaving", "cobble": "NH_GardenCobble", "gravel": "NH_GardenGravel", "herring": "NH_HerringboneBrick",
        "crazy": "NH_CrazyPaving"}


# ================================================================== plants

def mound(name, rx, ry, h, mat, rng, z0=0.0, seg=14):
    ob = sphere(name, 1.0, (0, 0, z0), mat, seg=seg, rings=5, scale=(rx, ry, h))
    for v in ob.data.vertices:
        if v.co.z < 0:
            v.co.z = 0.0
        v.co.x *= 1 + rng.uniform(-0.06, 0.06)
        v.co.y *= 1 + rng.uniform(-0.06, 0.06)
    return ob


def hedge_cards(cards, core, density=1.8, size=1.7, sprite="hedge"):
    cards.cover(core, density, sprite, size, offset=0.12, tilt=0.4, zmin=0.25)


def hedge_core(name, K, size, loc):
    return box(name, size, loc, K["core"], bevel=0.45, segments=3)


def trunk(name, base, top, r0, r1, mat, seg=10, wobble=0.15, rng=None, n=8):
    pts = []
    for i in range(n + 1):
        t = i / n
        p = Vector(base).lerp(Vector(top), t)
        if rng is not None and 0 < i < n:
            p += Vector((rng.uniform(-wobble, wobble), rng.uniform(-wobble, wobble), 0))
        pts.append(tuple(p))
    return bar(name, pts, lambda t: r0 + (r1 - r0) * t ** 0.8, mat, seg=seg)


def roots(prefix, K, r0, n, rng, z=0.4, spread=1.6, mat=None):
    for k in range(n):
        a = k / n * 6.28 + rng.uniform(-0.3, 0.3)
        L = spread * rng.uniform(0.8, 1.2)
        bar(f"{prefix}{k}", bez((math.cos(a) * r0 * 0.4, math.sin(a) * r0 * 0.4, z + 0.5), (math.cos(a) * r0 * 1.0, math.sin(a) * r0 * 1.0, z * 0.4),
                                (math.cos(a) * (r0 + L), math.sin(a) * (r0 + L), 0.06), 5), lambda t: r0 * 0.45 * (1 - t * 0.8), mat or K["bark"], seg=6)


def yew_tree(M):
    """An ancient yew 12.5 tall: a fluted trunk of four stems twisted round one another, a great knot of roots heaved up out of
    the ground at its foot, and a dark, layered, columnar crown in stacked masses (Leaves: yew)."""
    K = gk2(M)
    rng = RNG(32)
    for j in range(4):
        pts = []
        for i in range(12):
            t = i / 11
            a = j * math.pi / 2 + t * 2.4
            r = 0.55 * (1 - t * 0.35)
            pts.append((math.cos(a) * r, math.sin(a) * r, t * 4.6))
        bar(f"Stem{j}", pts, lambda t: 0.48 * (1 - t * 0.45), K["bark"], seg=9)
    for k in range(7):           # the root knot: thick roots heaving out and back into the ground
        a = k / 7 * 6.28 + rng.uniform(-0.2, 0.2)
        L = rng.uniform(1.6, 2.6)
        pts = bez((math.cos(a) * 0.6, math.sin(a) * 0.6, 0.6), (math.cos(a) * (0.9 + L * 0.4), math.sin(a) * (0.9 + L * 0.4), rng.uniform(0.7, 1.1)),
                  (math.cos(a) * (0.9 + L), math.sin(a) * (0.9 + L), 0.05), 7)
        bar(f"Root{k}", pts, lambda t: 0.36 * (1 - t * 0.7), K["root"], seg=8)
        if k % 2 == 0:
            q = pts[3]
            blob(f"Knot{k}", q, 0.32, K["root"], seg=9, rings=6, scale=(1, 1, 0.75), jitter=0.15, seed=k)
    cards = Cards(rng)
    masses = [((0, 0, 4.4), (1.8, 1.8, 1.4)), ((0.2, -0.1, 6.3), (1.9, 1.8, 1.4)), ((-0.2, 0.15, 8.2), (1.7, 1.65, 1.4)),
              ((0.1, 0.0, 10.0), (1.35, 1.3, 1.3)), ((0, 0, 11.6), (0.75, 0.75, 0.9))]
    for i, (c, rr) in enumerate(masses):
        ob = blob(f"Mass{i}", c, 1.0, leafy_core("YewMass", (0.012, 0.028, 0.018)), seg=12, rings=8, scale=tuple(v * 0.85 for v in rr), jitter=0.1, seed=i)
        cards.cover(ob, 3.2, "yew", 1.15, offset=0.08, tilt=0.35, zmin=3.0)
    cards.build("Leaves")
    P.ATLAS["YewTree_Leaves"] = "NH_GardenLeaves"
    return _dims()

def crabapple(M):
    """A gnarled old crabapple 9 tall, grown bent like a hunched figure: its trunk rises then bows forward (toward -Y) into a
    hooded crown, two long crooked branches hanging in front like arms, small red crabapples, windfalls round its foot."""
    K = gk2(M)
    rng = RNG(33)
    spine = bez((0, 1.2, 0.0), (0.2, 1.4, 5.5), (0.0, -1.6, 6.8), 12)
    spine = [tuple(Vector(p) + Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), 0))) for p in spine]
    bar("Trunk", spine, lambda t: 0.78 * (1 - t * 0.55), K["bark"], seg=12)
    roots("Root", K, 0.75, 6, rng, spread=1.6)
    for k in range(4):
        q = spine[3 + k * 2]
        blob(f"Burl{k}", (q[0] + rng.uniform(-0.5, 0.5), q[1] + 0.3, q[2]), 0.3, K["bark"], seg=8, rings=5, jitter=0.15, seed=k)
    head = Vector(spine[-1])
    ends = []
    for sx in (-1, 1):     # the arms: crooked branches hanging forward
        st = Vector(spine[8])
        p1 = st + Vector((sx * 1.6, -1.2, 0.4))
        p2 = st + Vector((sx * 2.4, -2.8, -2.2))
        pts = bez(tuple(st), tuple(p1), tuple(p2), 8)
        pts = [tuple(Vector(p) + Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(-0.1, 0.1)))) for p in pts]
        bar(f"Arm{sx}", pts, lambda t: 0.26 * (1 - t * 0.7), K["bark"], seg=8)
        for j in range(3):          # crooked fingers of twig
            a = rng.uniform(-0.8, 0.8)
            e = Vector(pts[-1]) + Vector((math.sin(a) * 0.6, -0.4, -0.5 - j * 0.2))
            bar(f"Finger{sx}{j}", [pts[-1], tuple((Vector(pts[-1]) + e) / 2 + Vector((0, 0, 0.1))), tuple(e)], lambda t: 0.07 * (1 - t * 0.8), K["bark"], seg=5)
        ends.append(Vector(pts[5]))
    for k in range(5):     # the hood: limbs from the crown curving forward and down
        a = -math.pi / 2 + (k - 2) * 0.55
        e = head + Vector((math.cos(a) * 2.6, math.sin(a) * 1.8 + 0.6, rng.uniform(-0.2, 1.2)))
        bar(f"Limb{k}", [tuple(head), tuple((head + e) / 2 + Vector((0, 0, 0.9))), tuple(e)], lambda t: 0.26 * (1 - t * 0.7), K["bark"], seg=7)
        ends.append(e)
    cards = Cards(rng)
    crown = [(head + Vector((0, 0.4, 0.9)), (2.4, 2.0, 1.3)), (head + Vector((0, -0.9, 0.0)), (2.2, 1.5, 1.1))] + [(e, (1.0, 1.0, 0.8)) for e in ends]
    for i, (c, rr) in enumerate(crown):
        ob = blob(f"Crown{i}", tuple(c), 1.0, K["core"] if False else shrub_core("CrabMass"), seg=10, rings=7,
                  scale=tuple(v * 0.75 for v in rr), jitter=0.12, seed=i)
        cards.cover(ob, 5.0, "crabapple", 1.35, offset=0.1, tilt=0.4)
    for k in range(10):
        a, r = rng.uniform(0, 6.28), rng.uniform(1.2, 4.0)
        sphere(f"Windfall{k}", 0.13, (math.cos(a) * r, math.sin(a) * r - 1.0, 0.11), flat("Crab", (0.3, 0.03, 0.03), 0.4, dirt=0.7), seg=8, rings=5)
    cards.build("Leaves")
    P.ATLAS["GnarledCrabapple_Leaves"] = "NH_GardenLeaves"
    return _dims()

def cypress_pair(M):
    """Two Italian cypresses, sharp dark spires 16 and 13 tall and barely 2 across, 4 apart on a shared bed of mulch."""
    K = gk2(M)
    rng = RNG(34)
    mound("Mulch", 3.3, 1.5, 0.2, K["mulch"], rng)
    cards = Cards(rng)
    for k, (x, H) in enumerate(((-2.0, 16.0), (2.0, 13.0))):
        trunk(f"Trunk{k}", (x, 0, 0), (x, 0, 1.3), 0.3, 0.24, K["bark"], seg=9)
        r = 1.0 if k == 0 else 0.9
        prof = [(0, 0.9), (r * 0.6, 1.0), (r * 0.95, 2.2), (r, H * 0.25), (r * 0.9, H * 0.5), (r * 0.62, H * 0.75), (r * 0.3, H * 0.9), (0.04, H), (0, H + 0.02)]
        core = lathe(f"Core{k}", prof, leafy_core("CypressMass", (0.012, 0.03, 0.02)), seg=12, loc=(x, 0, 0), jitter=(0.06, 5 + k))
        cards.cover(core, 3.6, "yew", 0.95, offset=0.07, tilt=0.3, zmin=0.9)
        tip = Vector((x, 0, H + 0.1))
        cards.add(tuple(tip), (1, 0, 0), (0, 0, 1), 0.5, 1.2, "yew", "top", nrm=UP)
    cards.build("Leaves")
    P.ATLAS["CypressPair_Leaves"] = "NH_GardenLeaves"
    return _dims()

def ivy_panel(M):
    """Ivy for a wall, 8 wide and 8 tall: woody vines spread flat on the wall plane (y = 0, the back), overlapping ivy cards in
    front of them, ragged at the top and sides. Pivot at the bottom centre on the wall plane."""
    K = gk2(M)
    rng = RNG(35)
    for k in range(5):
        x0 = rng.uniform(-2.5, 2.5)
        pts = [(x0, -0.06, 0)]
        x, z = x0, 0.0
        for i in range(8):
            x += rng.uniform(-0.9, 0.9)
            z += rng.uniform(0.8, 1.05)
            pts.append((max(-3.8, min(3.8, x)), -0.06, z))
        bar(f"Vine{k}", pts, lambda t: 0.07 * (1 - t * 0.6), K["bark"], seg=5)
    cards = Cards(rng)
    for i in range(150):
        x = rng.uniform(-3.9, 3.9)
        z = rng.uniform(0.2, 7.9)
        edge = max(abs(x) / 4.0, z / 8.0)
        if edge > 0.85 and rng.random() < 0.5:
            continue
        n = Vector((rng.uniform(-0.25, 0.25), -1, rng.uniform(-0.1, 0.3))).normalized()
        ax, ay = frame(n, roll=rng.uniform(-0.6, 0.6))
        s = rng.uniform(1.3, 1.8)
        cards.add((x, -0.1 - (i % 5) * 0.035, z), ax, ay, s, s, "ivy", "fill", nrm=Vector((0, -0.85, 0.35)))
    cards.build("Leaves")
    P.ATLAS["IvyWallPanel_Leaves"] = "NH_GardenLeaves"
    return _dims()


def ironpost(name, x, y, z1, K, w=0.11):
    box(name, (w * 2, w * 2, z1), (x, y, z1 / 2), K["iron"], bevel=0.02, segments=1)


def wisteria_pergola(M):
    """A walk-through iron pergola 7.6 wide and 10 long (the path runs along Y under it), beams at 8.4: four gothic posts with
    curved brackets, the beams and curled rafters left clear; two old twisted wisteria trunks climb the front posts, a light
    canopy of leaves along the beams, and long violet racemes hanging in tiers from every rafter."""
    K = gk2(M)
    rng = RNG(36)
    X, Y, H = 3.4, 4.6, 8.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * X, sy * Y
            ironpost(f"Post{sx}{sy}", x, y, H, K)
            box(f"Base{sx}{sy}", (0.55, 0.55, 0.5), (x, y, 0.25), K["lime"], bevel=0.05, segments=2)
            cone(f"Cap{sx}{sy}", 0.2, 0.0, 0.5, (x, y, H + 0.45), K["iron"], verts=4)
            for d in (-1, 1):
                bar(f"Brk{sx}{sy}{d}", bez((x, y, H - 1.6), (x, y + d * 0.2, H - 0.3), (x, y + d * 1.3, H - 0.05), 6), 0.035, K["iron"], seg=4)
    for sx in (-1, 1):
        box(f"Beam{sx}", (0.2, 2 * Y + 1.6, 0.42), (sx * X, 0, H + 0.21), K["iron"], bevel=0.02, segments=1)
        bar(f"Arch{sx}", [(sx * X, -Y, H - 1.2)] + [(sx * X, -Y + 2 * Y * t, H - 1.2 + 1.0 * math.sin(math.pi * t) ** 0.5) for t in [i / 12 for i in range(1, 12)]]
            + [(sx * X, Y, H - 1.2)], 0.04, K["iron"], seg=4)
    rafters = []
    for k in range(7):
        y = -Y - 0.6 + k * (2 * Y + 1.2) / 6
        rafters.append(y)
        box(f"Rafter{k}", (2 * X + 1.6, 0.12, 0.28), (0, y, H + 0.56), K["iron"], bevel=0.015, segments=1)
        for sx in (-1, 1):
            c = (sx * (X + 0.8), y, H + 0.4)
            bar(f"Curl{k}{sx}", [(c[0], y, H + 0.7)] + [(c[0] + sx * 0.18 * math.sin(a), y, H + 0.5 + 0.18 * math.cos(a)) for a in
                                                       [i / 6 * math.pi * 1.5 for i in range(1, 7)]], 0.03, K["iron"], seg=4)
    for sx in (-1, 1):
        x = sx * (X - 0.25)
        pts = []
        for i in range(14):
            t = i / 13
            a = t * 6.28 * 2.2
            pts.append((x + math.cos(a) * 0.25, -Y + math.sin(a) * 0.25 + 0.05, t * (H + 0.6)))
        bar(f"Trunk{sx}", pts, lambda t: 0.16 * (1 - t * 0.4), K["bark"], seg=6)
        bar(f"Vine{sx}", [(x, -Y, H + 0.75)] + [(x + math.sin(i) * 0.2, -Y + i * (2 * Y) / 8, H + 0.8 + 0.1 * math.cos(i * 2)) for i in range(1, 9)],
            0.08, K["bark"], seg=5)
    cards = Cards(rng)
    for k in range(26):    # a light canopy of leaves, along the beams only
        sx = -1 if k % 2 else 1
        cards.blob((sx * X + rng.uniform(-0.5, 0.5), rng.uniform(-Y - 0.6, Y + 0.6), H + 0.85), (0.6, 0.8, 0.3), 2, "hedge", 1.1, outward=0.5)
    for y in rafters:      # tiers of racemes from every rafter
        for i in range(14):
            x = -X + 0.3 + i * (2 * X - 0.6) / 13 + rng.uniform(-0.12, 0.12)
            h = rng.uniform(1.8, 3.4) * (1.0 if abs(x) > X - 1.5 else 0.8)
            cards.hang((x, y + rng.uniform(-0.15, 0.15), H + 0.45), rng.uniform(0.75, 1.0), h, "wisteria", yaw=math.pi / 2 + rng.uniform(-0.4, 0.4), sway=0.03)
    for sx in (-1, 1):
        for k in range(5):
            cards.blob((sx * (X - 0.25), -Y, rng.uniform(2.5, 8.0)), (0.5, 0.5, 0.5), 2, "hedge", 1.0)
    cards.build("Leaves")
    P.ATLAS["WisteriaPergola_Leaves"] = "NH_GardenLeaves"
    return _dims()

def fern_cluster(M):
    """A clump of fronds 2.6 tall, 5 across, from a mossy mound with a couple of fiddleheads."""
    K = gk2(M)
    rng = RNG(37)
    mound("Mound", 1.0, 0.9, 0.35, K["moss"], rng)
    cards = Cards(rng)
    cards.fronds((0, 0, 0.25), 9, 2.8, 1.2, "fern", elev=(45, 72), droop=0.3)
    cards.fronds((0, 0, 0.2), 8, 2.4, 1.1, "fern", elev=(18, 40), droop=0.4, yaw0=0.3)
    cards.build("Leaves")
    for k in range(3):
        a = k * 2.1
        x, y = math.cos(a) * 0.3, math.sin(a) * 0.3
        bar(f"Fiddle{k}", [(x, y, 0.2), (x, y, 0.8)] + [(x + 0.1 * math.sin(t), y, 0.9 + 0.1 * math.cos(t)) for t in (0.8, 2.0, 3.2, 4.4)],
            0.03, flat("Fiddle", (0.12, 0.2, 0.06), 0.6), seg=5)
    P.ATLAS["FernCluster_Leaves"] = "NH_GardenLeaves"
    return _dims()


def bed_box(prefix, K, w, d, h, mat, coping=True, rng=None):
    """A stone-edged bed: four walls (one 0.4 thick) round soil 0.15 below the rim."""
    t = 0.4
    for sy in (-1, 1):
        box(f"{prefix}WallY{sy}", (w, t, h), (0, sy * (d / 2 - t / 2), h / 2), mat, bevel=0.05, segments=1)
    for sx in (-1, 1):
        box(f"{prefix}WallX{sx}", (t, d - 2 * t, h), (sx * (w / 2 - t / 2), 0, h / 2), mat, bevel=0.05, segments=1)
    if coping:
        for sy in (-1, 1):
            box(f"{prefix}CopeY{sy}", (w + 0.12, t + 0.12, 0.14), (0, sy * (d / 2 - t / 2), h + 0.07), K["lime"], bevel=0.04, segments=1)
        for sx in (-1, 1):
            box(f"{prefix}CopeX{sx}", (t + 0.12, d - 2 * t - 0.12, 0.14), (sx * (w / 2 - t / 2), 0, h + 0.07), K["lime"], bevel=0.04, segments=1)
    box(f"{prefix}Soil", (w - 2 * t, d - 2 * t, 0.1), (0, 0, h - 0.2), K["soil"], bevel=0.0)


def lavender_bed(M):
    """A low brick-edged bed 6 x 2.4 (edging 0.5) full of lavender, 2.2 tall at its tallest."""
    K = gk2(M)
    rng = RNG(38)
    W, D, h = 6.0, 2.4, 0.5
    for sy in (-1, 1):
        edge_run("gravel", K, f"EY{sy}_", (-W / 2, sy * D / 2), (W / 2, sy * D / 2), rng)
    for sx in (-1, 1):
        edge_run("gravel", K, f"EX{sx}_", (sx * W / 2, -D / 2 + 0.25), (sx * W / 2, D / 2 - 0.25), rng)
    box("Soil", (W - 0.2, D - 0.2, 0.24), (0, 0, 0.12), K["soil"], bevel=0.05, segments=1)
    cards = Cards(rng)
    for i in range(7):
        for j in range(2):
            x = -W / 2 + 0.55 + i * (W - 1.1) / 6 + rng.uniform(-0.15, 0.15)
            y = -0.5 + j * 1.0 + rng.uniform(-0.12, 0.12)
            cards.crossed((x, y, 0.2), 1.25, rng.uniform(1.6, 2.0), "lavender", k=3)
            blob(f"Tuft{i}{j}", (x, y, 0.3), 0.32, K["core"], seg=6, rings=4, scale=(1, 1, 0.6))
    cards.build("Leaves")
    P.ATLAS["LavenderBed_Leaves"] = "NH_GardenLeaves"
    return _dims()


def raised_bed(M):
    """A raised limestone flower bed 6 x 3, rim 1.6 (coping), mossy: poppies, lavender, a fern at each end and trailing ivy
    over the front edge."""
    K = gk2(M)
    rng = RNG(39)
    W, D, h = 6.0, 3.0, 1.5
    bed_box("Bed", K, W, D, h, K["wall"])
    cards = Cards(rng)
    for i in range(5):
        x = -2.0 + i * 1.0 + rng.uniform(-0.15, 0.15)
        cards.crossed((x, 0.35, h - 0.15), 1.2, rng.uniform(1.6, 2.2), "poppy", k=3)
        cards.crossed((x + 0.4, -0.4, h - 0.15), 1.1, rng.uniform(1.2, 1.6), "lavender" if i % 2 else "moonflower", k=2)
    for sx in (-1, 1):
        cards.fronds((sx * 2.4, 0, h - 0.1), 7, 1.6, 0.8, "fern", elev=(30, 65))
    for i in range(7):      # ivy trailing over the front
        x = -2.6 + i * 0.85
        cards.add((x, -D / 2 - 0.08, h - 0.4), (1, 0, 0), (0, 0, 1), 1.1, 1.4, "ivy", "fill", nrm=Vector((0, -0.8, 0.5)))
    cards.build("Leaves")
    P.ATLAS["RaisedFlowerBed_Leaves"] = "NH_GardenLeaves"
    return _dims()


def mushroom_ring(M):
    """A fairy ring 7 across: fifteen tall, thin toadstools of many heights (0.5 to 1.9) with pale bell caps, the gills under
    each cap glowing soft moonlight blue-white (Glow), on moss with grass between."""
    K = gk2(M)
    rng = RNG(40)
    stalk = flat("Stalk", (0.55, 0.52, 0.47), 0.7, dirt=0.7)
    capm = lichen(flat("Cap", (0.34, 0.31, 0.34), 0.55, wear=0.2, dirt=0.7), 9.0, 0.3, cols=((0.55, 0.52, 0.5), (0.2, 0.17, 0.2)))
    cards = Cards(rng)
    for k in range(15):
        a = k / 15 * 6.28 + rng.uniform(-0.12, 0.12)
        r = 3.0 + rng.uniform(-0.3, 0.3)
        x, y = math.cos(a) * r, math.sin(a) * r
        hgt = rng.uniform(0.5, 1.9)
        cr = 0.16 + hgt * rng.uniform(0.12, 0.2)
        lean = rng.uniform(-0.12, 0.12)
        s = _mark()
        lathe(f"Stem{k}", [(0, 0), (0.06 + cr * 0.2, 0), (0.05 + cr * 0.1, 0.08), (0.03 + cr * 0.08, hgt * 0.6), (0.025 + cr * 0.07, hgt), (0, hgt)], stalk, seg=8)
        lathe(f"Cap{k}", [(0, hgt - 0.02), (cr, hgt - 0.05), (cr * 0.92, hgt + cr * 0.25), (cr * 0.7, hgt + cr * 0.7), (cr * 0.35, hgt + cr * 1.05),
                          (0, hgt + cr * 1.2)], capm, seg=12)
        set_group("Glow")
        lathe(f"Gills{k}", [(0.03, hgt - 0.06), (cr * 0.93, hgt - 0.045), (cr * 0.6, hgt + 0.02), (0.03, hgt + 0.02)], K["glow"], seg=12)
        set_group("Main")
        _xform(s, T(x, y, 0) @ RX(lean) @ RY(-lean))
        stone(f"Moss{k}", x, y, 0.45, 0.4, 0, 0.05, K["moss2"], rng, n=8, bevel=0.0)
        if k % 2 == 0:
            cards.crossed((x * 1.12, y * 1.12, 0), 0.7, 0.8, "grass", k=2)
    cards.build("Leaves")
    P.ATLAS["MushroomRing_Leaves"] = "NH_GardenLeaves"
    return _dims()

def moonflower_patch(M):
    """A bed of moonflower, 4.4 x 3.2: a calm, low mat of dark heart-shaped leaves, and six large pale trumpets on clear,
    curving stems (to 1.8), each with a soft glowing throat (Glow, moonlight blue-white)."""
    K = gk2(M)
    rng = RNG(41)
    mound("Soil", 2.2, 1.6, 0.16, K["soil"], rng)
    bed = blob("LeafBed", (0, 0, 0.1), 1.0, shrub_core("MoonBed"), seg=14, rings=6, scale=(1.9, 1.35, 0.35))
    cards = Cards(rng)
    for p, n in surface_samples(bed, 16.0, rng):
        if p.z < 0.12:
            continue
        nn = (UP * 0.85 + n * 0.15).normalized()
        ax, ay = frame(nn, roll=rng.uniform(0, 6.28), up=Vector((0, 1, 0)))
        cards.add(tuple(p + UP * 0.04), ax, ay, 0.85, 0.85, "ivy", "fill", nrm=UP)
    vine = flat("MoonVine", (0.05, 0.08, 0.035), 0.7)
    petal_m = flat("Moonpetal", (0.7, 0.74, 0.74), 0.55, dirt=0.25)
    from nh_props_batch4 import _aim
    for k in range(6):
        a = k / 6 * 6.28 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.4, 1.3)
        base = Vector((math.cos(a) * r, math.sin(a) * r * 0.7, 0.25))
        top = base + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, rng.uniform(1.0, 1.6)))
        bar(f"Stem{k}", bez(tuple(base), tuple(base + UP * (top.z - base.z) * 0.6), tuple(top), 6), 0.03, vine, seg=5)
        d = (Vector((math.cos(a), math.sin(a), 0)) * 0.6 + UP).normalized()
        s = _mark()
        lathe(f"Trumpet{k}", [(0.03, 0), (0.06, 0.1), (0.1, 0.3), (0.22, 0.5), (0.48, 0.62), (0.55, 0.64), (0.5, 0.67), (0.22, 0.56), (0.08, 0.32), (0, 0.3)],
              petal_m, seg=15, flute=(5, 0.12))
        for i in range(5):
            aa = i / 5 * 2 * math.pi
            petal(f"Calyx{k}{i}", (0, 0, 0.0), (math.cos(aa), math.sin(aa), 0), 0.2, 0.05, 0.4, 0.1, vine, curl=0.05, solid=False)
        set_group("Glow")
        lathe(f"Throat{k}", [(0.05, 0.3), (0.2, 0.52), (0.0, 0.52)], K["glow"], seg=10)
        set_group("Main")
        _xform(s, Matrix.Translation(tuple(top)) @ _aim(tuple(d)))
    cards.build("Leaves")
    P.ATLAS["MoonflowerPatch_Leaves"] = "NH_GardenLeaves"
    return _dims()

def tall_grass(M):
    """A clump of tall wild grass with seed heads, 3.2 tall, 2.5 across (its roots a small earth tuft)."""
    K = gk2(M)
    rng = RNG(42)
    mound("Tuft", 0.6, 0.6, 0.15, K["soil"], rng, seg=8)
    cards = Cards(rng)
    for k in range(5):
        a, r = k / 5 * 6.28, 0.35 if k else 0.0
        cards.crossed((math.cos(a) * r, math.sin(a) * r, 0), 1.8, rng.uniform(2.4, 3.2), "grass", k=3, lean=0.25)
    cards.build("Leaves")
    P.ATLAS["TallGrassClump_Leaves"] = "NH_GardenLeaves"
    return _dims()


def thorn_bramble(M):
    """An open tangle of bramble 6.6 across and 3 tall: a dozen thorny canes arching up and back down into the ground, crossing
    each other with gaps between, leaves along them (Leaves), a few clusters of dark berries and two dead brown leaves."""
    K = gk2(M)
    rng = RNG(43)
    cane = flat("Cane", (0.07, 0.025, 0.035), 0.55, dirt=0.6)
    berry = flat("Blackberry", (0.02, 0.006, 0.02), 0.2, dirt=0.3)
    mound("Root", 0.8, 0.7, 0.18, K["soil"], rng, seg=10)
    cards = Cards(rng)
    for k in range(12):
        a = rng.uniform(0, 6.28)
        L = rng.uniform(2.2, 3.4)
        h = rng.uniform(1.6, 3.0)
        side = Vector((-math.sin(a), math.cos(a), 0)) * rng.uniform(-0.8, 0.8)
        p0 = Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.05))
        p2 = Vector((math.cos(a) * L, math.sin(a) * L, 0.0)) + side
        p1 = (p0 + p2) / 2 + Vector((0, 0, h * 1.6))
        pts = bez(tuple(p0), tuple(p1), tuple(p2), 12)
        bar(f"Cane{k}", pts, lambda t: 0.05 * (1 - t * 0.6), cane, seg=6)
        for i in range(1, 12):
            p = Vector(pts[i])
            d = (Vector(pts[i + 1]) - p).normalized()
            for j in range(2):
                o = (d.cross(UP).normalized() * (1 if j else -1) + d * 0.6).normalized()
                th = cone(f"Thorn{k}{i}{j}", 0.025, 0.0, 0.09, tuple(p + o * 0.045), K["thorn"], verts=4, rot=tuple(o.to_track_quat("Z", "Y").to_euler()))
                th.modifiers.clear()
            if i % 2 == 0 and rng.random() < 0.8:
                n = (d.cross(UP).normalized() * rng.uniform(-1, 1) + UP).normalized()
                ax, ay = frame(n, roll=rng.uniform(0, 6.28))
                cards.add(tuple(p + n * 0.1), ax, ay, 0.75, 0.75, "bramble", "fill", nrm=n)
        if k % 3 == 0:
            q = Vector(pts[4])
            for b in range(9):
                sphere(f"Berry{k}{b}", 0.06, tuple(q + Vector((rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), -0.1 + rng.uniform(-0.06, 0.06)))), berry,
                       seg=6, rings=4)
    dead = flat("DeadLeaf", (0.2, 0.11, 0.05), 0.85, dirt=0.6)
    for k in range(2):
        a = rng.uniform(0, 6.28)
        petal(f"DeadLeaf{k}", (math.cos(a) * 1.5, math.sin(a) * 1.5, 0.02), (math.cos(a + 1), math.sin(a + 1), 0), 0.35, 0.16, 1.4, 0.25, dead, curl=0.2,
              solid=False)
    cards.build("Leaves")
    P.ATLAS["ThornBramble_Leaves"] = "NH_GardenLeaves"
    return _dims()

def nightshade(M):
    """A deadly-nightshade shrub 3.6 tall, open and irregular: purplish stems branching out to leafy clumps, violet star flowers,
    and clusters of glossy berries drooping on their stalks; inside each berry a faint violet glow (Glow)."""
    K = gk2(M)
    rng = RNG(44)
    mound("Soil", 1.4, 1.3, 0.16, K["soil"], rng, seg=10)
    stem = flat("NightStem", (0.1, 0.05, 0.1), 0.6, dirt=0.6)
    berry = flat("NightBerry", (0.03, 0.006, 0.05), 0.15, dirt=0.3)
    dark = shrub_core("NightHeart")
    cards = Cards(rng)
    clumps = []
    for k in range(7):
        a = k / 7 * 6.28 + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.6, 1.6)
        top = Vector((math.cos(a) * r, math.sin(a) * r, rng.uniform(1.6, 3.3)))
        pts = bez((0, 0, 0.1), (math.cos(a) * r * 0.3, math.sin(a) * r * 0.3, top.z * 0.6), tuple(top), 6)
        bar(f"Stem{k}", pts, lambda t: 0.06 * (1 - t * 0.5), stem, seg=5)
        rr = (rng.uniform(0.5, 0.75), rng.uniform(0.5, 0.75), rng.uniform(0.35, 0.5))
        ob = blob(f"Clump{k}", tuple(top), 1.0, dark, seg=10, rings=7, scale=tuple(v * 0.5 for v in rr), jitter=0.12, seed=k)
        cards.cover(ob, 9.0, "nightshade", 0.9, offset=0.08, tilt=0.4, zmin=0.4)
        clumps.append((top, a))
    k = 0
    for c, (top, a) in enumerate(clumps):
        for j in range(2):
            out = Vector((math.cos(a + (j - 0.5) * 0.9), math.sin(a + (j - 0.5) * 0.9), 0))
            st = top + out * 0.5
            en = st + out * 0.25 + Vector((0, 0, -0.55))
            bar(f"Stalk{c}{j}", [tuple(st), tuple((st + en) / 2 + out * 0.08), tuple(en)], 0.015, stem, seg=4)
            for b in range(6):
                q = en + Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), -b * 0.05 + rng.uniform(-0.03, 0.03)))
                sphere(f"Berry{k}", 0.065, tuple(q), berry, seg=8, rings=5)
                set_group("Glow")
                sphere(f"BerryGlow{k}", 0.035, tuple(q + Vector((0, -0.03, 0.01))), K["glow"], seg=6, rings=4)
                set_group("Main")
                k += 1
    cards.build("Leaves")
    P.ATLAS["NightshadeShrub_Leaves"] = "NH_GardenLeaves"
    return _dims()

def pumpkin(name, K, loc, r, h, rng, mat=None, rot=0.0):
    prof = [(0, 0)] + [(r * math.sin(t * math.pi) ** 0.85, h * (1 - math.cos(t * math.pi)) / 2) for t in [i / 8 for i in range(1, 8)]] + [(0.08 * r, h * 0.94), (0, h * 0.9)]
    ob = lathe(name, prof, mat, seg=16, loc=loc, flute=(8, 0.09))
    bar(name + "Stalk", [(loc[0], loc[1], loc[2] + h * 0.88), (loc[0] + 0.05, loc[1], loc[2] + h * 1.05), (loc[0] + 0.15, loc[1] + 0.05, loc[2] + h * 1.12)],
        lambda t: 0.07 * r * (1 - t * 0.3) + 0.03, flat("PumpStalk", (0.12, 0.13, 0.06), 0.8), seg=5)
    return ob


def pumpkin_patch(M):
    """A patch of five pumpkins (the biggest 1.6 across) on straw and soil, 6 x 4, under big lobed leaves on curling vines; one
    is a carved lantern with a friendly face, lit inside (Glow: the face's light)."""
    K = gk2(M)
    rng = RNG(45)
    mound("Soil", 3.1, 2.1, 0.15, K["soil"], rng)
    pm = flat("Pumpkin", (0.42, 0.13, 0.015), 0.6, wear=0.1, dirt=0.75)
    pm2 = flat("PumpkinPale", (0.5, 0.42, 0.3), 0.6, wear=0.1, dirt=0.75)
    spots = [((-1.6, -0.6), 0.8, 1.0, pm), ((0.6, -0.9), 0.62, 0.8, pm), ((1.8, 0.6), 0.5, 0.62, pm2), ((-0.3, 0.9), 0.55, 0.7, pm), ((2.2, -1.1), 0.36, 0.45, pm)]
    for k, ((x, y), r, h, mat) in enumerate(spots):
        pumpkin(f"Pumpkin{k}", K, (x, y, 0.08), r, h, rng, mat)
    # the jack-o'-lantern (the first): a face of glowing shapes set into its front
    x, y = spots[0][0]
    r, h = spots[0][1], spots[0][2]
    set_group("Glow")
    yf = y - r * 0.93
    for sx in (-1, 1):
        poly_slab(f"Eye{sx}", [(-0.13, 0), (0.13, 0), (0, 0.2)], 0, 0.04, K["glow"])
        P.PARTS[-1].matrix_world = T(x + sx * 0.26, yf + 0.04, 0.08 + h * 0.55) @ RX(math.pi / 2)
    mouth = [(-0.38, 0.06), (-0.22, -0.06), (-0.12, 0.02), (0, -0.1), (0.12, 0.02), (0.22, -0.06), (0.38, 0.06), (0.2, -0.16), (0, -0.2), (-0.2, -0.16)]
    poly_slab("Mouth", mouth, 0, 0.04, K["glow"])
    P.PARTS[-1].matrix_world = T(x, yf + 0.02, 0.08 + h * 0.4) @ RX(math.pi / 2)
    set_group("Main")
    vine = flat("Vine", (0.1, 0.13, 0.05), 0.7)
    for k in range(5):
        a = rng.uniform(0, 6.28)
        pts = [(math.cos(a + t) * (0.5 + t * 0.9), math.sin(a + t) * (0.4 + t * 0.6), 0.16 + 0.05 * math.sin(t * 5)) for t in [i / 6 * 2.4 for i in range(7)]]
        bar(f"Vine{k}", pts, 0.035, vine, seg=4)
    straw = flat("Straw", (0.42, 0.34, 0.16), 0.9)
    for k in range(18):
        a, rr = rng.uniform(0, 6.28), rng.uniform(0.3, 2.6)
        box(f"Straw{k}", (0.6, 0.03, 0.02), (math.cos(a) * rr, math.sin(a) * rr * 0.7, 0.16), straw, bevel=0.0, rot=(0, 0, rng.uniform(0, 3.14)))
    cards = Cards(rng)
    for k in range(22):
        x, y = rng.uniform(-2.8, 2.8), rng.uniform(-1.8, 1.8)
        n = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 1)).normalized()
        ax, ay = frame(n, roll=rng.uniform(0, 6.28), up=Vector((0, 1, 0)))
        cards.add((x, y, rng.uniform(0.35, 0.9)), ax, ay, 1.3, 1.3, "ivy", "fill", nrm=UP)
    cards.build("Leaves")
    P.ATLAS["PumpkinPatch_Leaves"] = "NH_GardenLeaves"
    return _dims()


def poppy_bed(M):
    """A bed of crimson poppies 6 x 3, 2.4 tall at the top flowers, on dark soil edged with a little rough grass."""
    K = gk2(M)
    rng = RNG(46)
    mound("Soil", 3.2, 1.7, 0.2, K["soil"], rng)
    cards = Cards(rng)
    for k in range(22):
        x, y = rng.uniform(-2.6, 2.6), rng.uniform(-1.2, 1.2)
        cards.crossed((x, y, 0.12), 1.2, rng.uniform(1.6, 2.3), "poppy", k=2, lean=0.2)
    for k in range(8):
        a = k / 8 * 6.28
        cards.crossed((math.cos(a) * 3.0, math.sin(a) * 1.6, 0.0), 1.0, 0.9, "grass", k=2)
    cards.build("Leaves")
    P.ATLAS["PoppyBed_Leaves"] = "NH_GardenLeaves"
    return _dims()


def lily_pads(M):
    """Six big lily pads (1.5 to 2.5 across) and three pale water lilies, to float on a pond, 6 x 5 (pivot on the water line;
    pads at 0.0 to 0.04)."""
    K = gk2(M)
    rng = RNG(47)
    pad = flat("LilyPad", (0.04, 0.1, 0.035), 0.35, wear=0.0, dirt=0.5)
    _paint(pad, _math(pad.node_tree, "MULTIPLY", _math(pad.node_tree, "SUBTRACT", _noise(pad, 3.0), 0.55), 4.0, clamp=True), (0.12, 0.04, 0.05))
    spots = [(-1.6, -1.2), (0.4, -1.5), (1.9, -0.4), (-0.6, 0.6), (1.2, 1.4), (-2.1, 1.3)]
    for k, (x, y) in enumerate(spots):
        r = rng.uniform(0.75, 1.25)
        n = 24
        notch = rng.uniform(0, 6.28)
        V = [(x, y, 0.035)]
        for i in range(n + 1):
            a = notch + 0.3 + i / n * (2 * math.pi - 0.6)
            V.append((x + math.cos(a) * r, y + math.sin(a) * r, 0.0 + 0.02 * math.sin(i * 1.7)))
        ob = mk(f"Pad{k}", V, [(0, i, i + 1) for i in range(1, n + 1)], pad, smooth=True)
        md = ob.modifiers.new("Solid", "SOLIDIFY")
        md.thickness = 0.02
    petal_m = flat("LilyPetal", (0.75, 0.7, 0.8), 0.5, dirt=0.4)
    for k, (x, y) in enumerate(((-0.4, -1.0), (1.5, 0.6), (-1.5, 0.4))):
        s = _mark()
        for ring, (cnt, L, op) in enumerate(((8, 0.55, 1.25), (8, 0.45, 0.85), (6, 0.32, 0.45))):
            for i in range(cnt):
                a = i / cnt * 2 * math.pi + ring * 0.3
                petal(f"Lily{k}{ring}{i}", (0, 0, 0.03), (math.cos(a), math.sin(a), 0), L, 0.14, op, 0.2, petal_m, curl=0.15)
        sphere(f"LilyHeart{k}", 0.1, (0, 0, 0.12), flat("Pollen", (0.6, 0.45, 0.1), 0.6), seg=8, rings=5)
        _xform(s, T(x, y, 0))
    return _dims()

# ================================================================== features

def koi_pond(M):
    """A kidney-shaped pond 13 x 9: big flat coping stones overhanging the water (top 0.95) on a mossy wall, a pebbled floor,
    the water (Glass) at 0.75; two koi under it, lily pads and a water lily; a stone toad squatting on the coping spits a thin
    arc of water into it; reeds at one end (Leaves)."""
    K = gk2(M)
    rng = RNG(51)
    n = 48
    ring = [kidney(i / n * 2 * math.pi) for i in range(n)]
    ow = [(x * 1.16, y * 1.22) for x, y in ring]
    V = [(x, y, 0) for x, y in ow] + [(x, y, 0.7) for x, y in ow]
    P_recalc(mk("Wall", V, [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)], K["wall"], smooth=True))
    poly_slab("Floor", ring, 0.0, 0.1, flat("PondFloor", (0.03, 0.04, 0.03), 0.8))
    V = [(x, y, 0.1) for x, y in ring] + [(x, y, 0.72) for x, y in ring]
    P_recalc(mk("Inner", V, [(i + n, (i + 1) % n + n, (i + 1) % n, i) for i in range(n)],
                mossy(material("PondWall", "NH_Limestone", tint=(0.2, 0.22, 0.2), scale=0.4, wear=0.1, dirt=1.0), 0.9, low=1.5), smooth=True))
    # coping: big flat stones, each overhanging the water by 0.3-0.5
    m = 16
    for k in range(m):
        t0, t1 = k / m * 2 * math.pi, (k + 1) / m * 2 * math.pi
        pts_in, pts_out = [], []
        for j in range(4):
            t = t0 + (t1 - t0) * (0.03 + 0.94 * j / 3)
            x, y = kidney(t)
            L = math.hypot(x, y)
            ov = rng.uniform(0.3, 0.5)
            pts_in.append((x - x / L * ov, y - y / L * ov))
            w = rng.uniform(1.0, 1.35)
            pts_out.append((x + x / L * w, y + y / L * w))
        poly = _roughen(pts_out[::-1] + pts_in if _area(pts_in + pts_out[::-1]) < 0 else pts_in + pts_out[::-1], rng, 0.04, chip=0.3)
        if _area(poly) < 0:
            poly = poly[::-1]
        stone_slab(f"Cope{k}", poly, 0.68, 0.92 + rng.uniform(-0.04, 0.03), K["flag"], tilt=(rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01)), bevel=0.05)
    for k in range(16):
        a, r = rng.uniform(0, 6.28), rng.uniform(0.2, 0.85)
        x, y = kidney(a)
        sphere(f"Pebble{k}", rng.uniform(0.15, 0.3), (x * r, y * r, 0.1), K["gran"], seg=6, rings=4, scale=(1, 0.8, 0.5))
    set_group("Glass")
    poly_slab("Water", ring, 0.73, 0.75, K["water"])
    # the toad's spout: a thin arc of water
    tx, ty = kidney(0.35)
    L = math.hypot(tx, ty)
    st = Vector((tx + tx / L * 0.2, ty + ty / L * 0.2, 1.6))
    en = Vector((tx - tx / L * 1.6, ty - ty / L * 1.6, 0.75))
    bar("Spout", bez(tuple(st), tuple((st + en) / 2 + Vector((0, 0, 0.5))), tuple(en), 10), 0.03, K["water"], seg=5)
    set_group("Main")
    # the stone toad
    s = _mark()
    toad = K["limel"]
    blob("ToadBody", (0, 0, 0.32), 0.42, toad, seg=12, rings=8, scale=(1.1, 1.0, 0.75))
    blob("ToadHead", (0, -0.38, 0.55), 0.3, toad, seg=12, rings=8, scale=(1.15, 0.9, 0.7))
    for sx in (-1, 1):
        blob(f"ToadEye{sx}", (sx * 0.17, -0.48, 0.74), 0.09, toad, seg=8, rings=5)
        blob(f"ToadLeg{sx}", (sx * 0.42, 0.1, 0.16), 0.2, toad, seg=8, rings=5, scale=(0.8, 1.4, 0.6))
        blob(f"ToadArm{sx}", (sx * 0.28, -0.4, 0.12), 0.12, toad, seg=8, rings=5, scale=(0.8, 1.0, 1.4))
    cyl("ToadMouth", 0.07, 0.1, (0, -0.66, 0.52), K["ink"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
    _xform(s, T(tx + tx / L * 0.4, ty + ty / L * 0.4, 0.92) @ RZ(math.atan2(ty, tx) - math.pi / 2))
    for k, (pos, yaw, cols) in enumerate((((-1.5, -0.3), 0.4, ((0.55, 0.12, 0.01), (0.7, 0.68, 0.62))), ((1.8, 0.6), 3.6, ((0.04, 0.035, 0.03), (0.6, 0.35, 0.04))))):
        km = flat(f"Koi{k}", cols[1], 0.35, dirt=0.3)
        nt = km.node_tree
        _paint(km, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", _noise(km, 2.2), 0.48), 8.0, clamp=True), cols[0])
        s = _mark()
        Lk = 1.4
        bar(f"KoiBody{k}", [(-Lk / 2 + Lk * t, 0.1 * math.sin(t * 3 + k), 0) for t in [i / 11 for i in range(12)]],
            lambda t: 0.21 * math.sin(math.pi * min(1, t * 1.15 + 0.08)) ** 0.7 + 0.01, km, seg=10)
        ob = P.PARTS[-1]
        for v in ob.data.vertices:
            v.co.z *= 0.8
            v.co.y *= 0.85
        poly_slab(f"KoiTail{k}", [(-Lk / 2 + 0.05, 0), (-Lk / 2 - 0.4, 0.25), (-Lk / 2 - 0.3, 0), (-Lk / 2 - 0.4, -0.25)], -0.01, 0.01, km)
        for sy in (-1, 1):
            poly_slab(f"KoiFin{k}{sy}", [(0.2, sy * 0.12), (0.0, sy * 0.4), (0.05, sy * 0.12)], -0.08, -0.06, km)
        _xform(s, T(pos[0], pos[1], 0.52) @ RZ(yaw))
    for k in range(6):
        a = rng.uniform(0, 6.28)
        x, y = kidney(a)
        x, y = x * rng.uniform(0.3, 0.7), y * rng.uniform(0.3, 0.7)
        r = rng.uniform(0.35, 0.6)
        V = [(x, y, 0.765)] + [(x + math.cos(t) * r, y + math.sin(t) * r, 0.76) for t in [0.4 + i / 12 * 5.5 for i in range(13)]]
        mk(f"Pad{k}", V, [(0, i, i + 1) for i in range(1, 13)], flat("PondPad", (0.05, 0.12, 0.04), 0.35), smooth=True)
    lathe("Lily", [(0, 0.76), (0.1, 0.76), (0.24, 0.8), (0.3, 0.88), (0.2, 0.9), (0.12, 0.86), (0.08, 0.96), (0, 0.92)],
          flat("PondLily", (0.75, 0.68, 0.8), 0.5), seg=12, loc=(1.2, -1.0, 0), flute=(8, 0.3))
    cards = Cards(rng)
    for k in range(7):
        x, y = kidney(math.pi + rng.uniform(-0.4, 0.4))
        cards.crossed((x * 0.85, y * 0.85, 0.1), 1.2, rng.uniform(2.6, 3.4), "grass", k=3)
    cards.build("Leaves")
    P.ATLAS["KoiPond_Leaves"] = "NH_GardenLeaves"
    return _dims()

def bird_bath(M):
    """A bird bath held up by a carved stone hand, 4.1 tall: a slender forearm in a stone cuff rising from a moulded plinth, its
    open hand cupping a shallow scalloped basin of rainwater (Glass), fingers curling up round the rim; a brass sparrow on it."""
    K = gk2(M)
    st = K["limel"]
    box("Plinth", (1.4, 1.4, 0.35), (0, 0, 0.175), K["lime"], bevel=0.05, segments=2)
    lathe("Cuff", [(0, 0.35), (0.42, 0.35), (0.45, 0.5), (0.38, 0.6), (0.4, 0.9), (0.33, 1.0), (0, 1.0)], st, seg=16)
    bar("Forearm", [(0, 0, 0.95), (0.03, 0.02, 1.8), (0.0, 0.0, 2.55)], lambda t: 0.3 - t * 0.07, st, seg=14)
    blob("Wrist", (0, 0, 2.6), 0.26, st, seg=12, rings=8, scale=(1.05, 0.85, 0.7))
    blob("Palm", (0, 0, 2.86), 0.45, st, seg=14, rings=8, scale=(1.0, 0.85, 0.35))
    zb = 3.0
    lathe("Basin", [(0, zb - 0.06), (0.4, zb - 0.04), (0.9, zb + 0.12), (1.1, zb + 0.3), (1.15, zb + 0.42), (1.04, zb + 0.44), (0.92, zb + 0.32), (0.45, zb + 0.22),
                    (0, zb + 0.2)], K["lime"], seg=28, flute=(12, 0.04))
    for k, a in enumerate((-0.9, -0.3, 0.3, 0.9)):     # four fingers curling up round the basin's front
        base = Vector((math.sin(a) * 0.32, -0.32 * math.cos(a), 2.88))
        out = Vector((math.sin(a), -math.cos(a), 0))
        pts = [tuple(base), tuple(base + out * 0.45 + UP * 0.05), tuple(base + out * 0.85 + UP * 0.3), tuple(base + out * 1.0 + UP * 0.58),
               tuple(base + out * 0.95 + UP * 0.72)]
        bar(f"Finger{k}", pts, lambda t: 0.1 - t * 0.03, st, seg=8)
    th = Vector((0.38, 0.1, 2.85))
    bar("Thumb", [tuple(th), tuple(th + Vector((0.4, 0.05, 0.15))), tuple(th + Vector((0.72, 0.0, 0.45))), tuple(th + Vector((0.78, -0.05, 0.62)))],
        lambda t: 0.12 - t * 0.03, st, seg=8)
    set_group("Glass")
    cyl("Water", 0.98, 0.02, (0, 0, zb + 0.33), K["water"], verts=24, bevel=0.0)
    set_group("Main")
    s = _mark()
    sphere("BirdBody", 0.12, (0, 0, 0.12), K["brassf"], seg=10, rings=6, scale=(1.4, 0.8, 0.9))
    sphere("BirdHead", 0.075, (0.15, 0, 0.22), K["brassf"], seg=8, rings=5)
    cone("Beak", 0.025, 0.0, 0.08, (0.25, 0, 0.22), K["brassf"], verts=5, rot=(0, math.pi / 2, 0))
    poly_slab("BirdTail", [(-0.12, -0.03), (-0.3, -0.06), (-0.3, 0.06), (-0.12, 0.03)], 0.13, 0.15, K["brassf"])
    _xform(s, T(-0.75, 0.72, zb + 0.44) @ RZ(2.3))
    return _dims()

def garden_bench(M):
    """A cast-iron and oak garden bench 6 wide whose back is a raven with its wings spread: a solid cast-iron backrest in the
    shape of two great wings, their feathers raised in relief, rising to the raven's head and hooked beak at the centre (to 4.5).
    Seat top 1.7. Faces -Y."""
    K = gk2(M)
    for sx in (-1, 1):
        x = sx * 2.75
        bar(f"Leg{sx}F", [(x, -0.9, 0), (x, -0.85, 0.8), (x, -0.95, 1.55)], 0.06, K["iron"], seg=6)
        bar(f"Leg{sx}B", [(x, 0.75, 0), (x, 0.6, 0.9), (x, 0.55, 1.6)], 0.06, K["iron"], seg=6)
        bar(f"Arm{sx}", [(x, 0.5, 2.45), (x, 0.0, 2.35), (x, -0.8, 2.35), (x, -1.05, 2.2), (x, -0.95, 2.05), (x, -0.85, 2.15)], 0.055, K["iron"], seg=6)
        bar(f"ArmPost{sx}", [(x, -0.9, 1.6), (x, -0.85, 2.3)], 0.045, K["iron"], seg=5)
        bar(f"Rail{sx}", [(x, -0.95, 1.55), (x, 0.55, 1.6)], 0.05, K["iron"], seg=6)
        for k, (cy, cz, r0) in enumerate(((-0.4, 0.8, 0.3), (0.2, 0.75, 0.25))):
            bar(f"Scroll{sx}{k}", [(x, cy + math.cos(a) * r0 * (1 - a / 12), cz + math.sin(a) * r0 * (1 - a / 12)) for a in [i / 10 * 9.4 for i in range(11)]],
                0.03, K["iron"], seg=4)
        bar(f"Foot{sx}", [(x, -0.95, 0.03), (x, 0.8, 0.03)], 0.05, K["iron"], seg=4)
    for k in range(5):
        box(f"Seat{k}", (5.8, 0.27, 0.1), (0, -0.85 + k * 0.33, 1.62), K["oak"], bevel=0.03, segments=2)
    yb = 0.62
    for sx in (-1, 1):
        # the wing's silhouette: leading edge rising from the body to the wrist, feather tips scalloped back along the bottom
        lead = [(0.3, 2.1), (0.7, 2.75), (1.3, 3.25), (2.0, 3.6), (2.6, 3.75), (2.9, 3.6)]
        trail = []
        n = 7
        for i in range(n + 1):
            t = i / n
            x = 2.9 - 2.6 * t
            zb = 3.3 - 1.45 * t ** 0.8
            trail.append((x, zb))
            if i < n:
                trail.append((x - 2.6 / n * 0.5, zb - 0.32 + 0.08 * t))
        out = [(sx * u, v) for u, v in lead + trail]
        if _area(out) < 0:
            out = out[::-1]
        tprism(f"Wing{sx}", out, yb, 0.08, K["iron"], plane="XZ")
        # feathers in relief: three rows of raised, pointed plates on the front face
        for row, (z0, z1, L) in enumerate(((2.15, 3.0, 0.75), (2.4, 3.3, 0.6), (2.7, 3.55, 0.45))):
            for f in range(6 - row):
                t = f / max(1, 5 - row)
                x = 0.5 + t * (2.1 - row * 0.3)
                z = z0 + (z1 - z0) * t ** 0.7
                fe = [(x - 0.12, z + 0.1), (x + 0.14, z + 0.1), (x + 0.42, z - L * 0.5), (x + 0.26, z - L * 0.6)]
                fe = [(sx * u, v) for u, v in fe]
                if _area(fe) < 0:
                    fe = fe[::-1]
                tprism(f"Feather{sx}{row}{f}", fe, yb - 0.06 - row * 0.012, 0.025, K["iron"], plane="XZ")
    blob("RavenBody", (0, yb - 0.02, 2.55), 0.45, K["iron"], seg=14, rings=9, scale=(0.72, 0.42, 1.2))
    blob("RavenHead", (0, yb - 0.12, 3.6), 0.3, K["iron"], seg=12, rings=8, scale=(0.9, 1.0, 0.95))
    bk = cone("RavenBeak", 0.12, 0.01, 0.62, (0, 0, 0), K["iron"], verts=8)
    bk.matrix_world = T(0, yb - 0.52, 3.47) @ RX(math.pi / 2 + 0.35)
    for sx in (-1, 1):
        sphere(f"RavenEye{sx}", 0.05, (sx * 0.15, yb - 0.32, 3.67), K["crimson"], seg=8, rings=5)
        bar(f"BackPost{sx}", [(sx * 2.75, 0.55, 1.6), (sx * 2.85, 0.65, 3.2)], 0.05, K["iron"], seg=5)
    bar("BackRail", [(-2.75, yb, 1.85), (2.75, yb, 1.85)], 0.05, K["iron"], seg=5)
    return _dims()

def curved_bench(M):
    """A curved limestone bench (a 100-degree arc of radius 4.5, seat top 1.6) on three carved scroll supports, moss on its
    seat edges. Its concave side faces -Y; pivot at the base centre of the middle support."""
    K = gk2(M)
    c = (0, 4.5)
    a0, a1 = -90 * DEG - 50 * DEG, -90 * DEG + 50 * DEG
    ring_slab("Seat", c, 3.95, 5.15, a0, a1, 1.32, 1.6, K["lime"], n=18, bevel=0.06)
    for k, a in enumerate((a0 + 0.12, -90 * DEG, a1 - 0.12)):
        s = _mark()
        prof = [(-0.5, 0), (0.5, 0), (0.45, 0.2), (0.25, 0.4), (0.3, 1.0), (0.5, 1.32), (-0.5, 1.32), (-0.3, 1.0), (-0.25, 0.4), (-0.45, 0.2)]
        from nh_props_batch20 import tprism
        tprism(f"Support{k}", [(y, z) for y, z in prof], 0, 0.5, K["lime"], plane="YZ")
        P.PARTS[-1].modifiers.new("Bevel", "BEVEL").width = 0.04
        _xform(s, T(c[0] + math.cos(a) * 4.55, c[1] + math.sin(a) * 4.55, 0) @ RZ(a - math.pi / 2))
    return _dims()


def iron_gazebo(M):
    """An octagonal gothic iron gazebo 17.5 across and 18 to the finial, walk-in from the front (-Y): a limestone platform 0.6
    high with a step, eight iron posts linked by pointed arches of filigree tracery, bat-wing brackets at every post head, a
    pierced cresting round the eaves, and an onion dome of dark slate on iron ribs rising to a crimson glass lantern; seven
    iron-and-oak benches inside (the front bay is open)."""
    K = gk2(M)
    R, H = 6.0, 8.0
    oct8 = [(math.cos(math.pi / 8 + i * math.pi / 4) * (R + 0.6), math.sin(math.pi / 8 + i * math.pi / 4) * (R + 0.6)) for i in range(8)]
    poly_slab("Platform", oct8, 0, 0.6, K["limel"], bevel=0.05)
    box("Step", (4.4, 1.2, 0.3), (0, -(R + 0.6) * math.cos(math.pi / 8) - 0.55, 0.15), K["lime"], bevel=0.05, segments=2)
    posts = [(math.cos(-math.pi / 2 + math.pi / 8 + i * math.pi / 4) * R, math.sin(-math.pi / 2 + math.pi / 8 + i * math.pi / 4) * R) for i in range(8)]
    zt = 0.6 + H
    from nh_props_batch20 import tprism
    for i, (x, y) in enumerate(posts):
        box(f"Post{i}", (0.26, 0.26, H), (x, y, 0.6 + H / 2), K["iron"], bevel=0.03, segments=2)
        box(f"PostFoot{i}", (0.48, 0.48, 0.35), (x, y, 0.78), K["iron"], bevel=0.04, segments=2)
        for z in (2.4, 4.6):
            ringbar(f"Collar{i}{z}", (x, y, z), 0.19, "Z", K["iron"], thick=0.03, n=8, seg=4)
        a = math.atan2(y, x)
        for side in (-1, 1):      # bat-wing brackets from the post into the beams
            s = _mark()
            wing = [(0.0, 0.0), (0.0, 1.2), (0.25, 1.05), (0.45, 1.15), (0.62, 0.95), (0.85, 1.05), (1.15, 0.9), (0.8, 0.6), (0.5, 0.45), (0.2, 0.15)]
            tprism(f"Bat{i}{side}", [(side * u, v) for u, v in wing] if side > 0 else [(side * u, v) for u, v in reversed(wing)], 0, 0.05, K["iron"],
                   plane="XZ")
            _xform(s, T(x, y, zt - 1.3) @ RZ(a + math.pi / 2))
    for i in range(8):
        (x0, y0), (x1, y1) = posts[i], posts[(i + 1) % 8]
        bar(f"Beam{i}", [(x0, y0, zt), (x1, y1, zt)], 0.1, K["iron"], seg=4)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        for k2, off in enumerate((0.0, 0.25)):
            pts = []
            for k in range(15):
                t = k / 14
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, zt - 2.8 + off + 2.4 * math.sin(math.pi * t) ** 0.55))
            bar(f"Arch{i}{k2}", pts, 0.045, K["iron"], seg=4)
        ang = math.atan2(y1 - y0, x1 - x0)
        for j, t in enumerate((0.25, 0.5, 0.75)):
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            rr = 0.32 if j == 1 else 0.22
            ringbar(f"Foil{i}{j}", (0, 0, 0), rr, "Y", K["iron"], thick=0.025, n=12, seg=4)
            P.PARTS[-1].matrix_world = T(cx, cy, zt - 0.6 + (0.1 if j == 1 else -0.15)) @ RZ(ang)
        for k in range(9):        # cresting: little spears and fleurs along the eaves
            t = (k + 0.5) / 9
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            cone(f"Crest{i}{k}", 0.05, 0.0, 0.45 if k % 2 else 0.3, (cx, cy, zt + 0.3), K["iron"], verts=4)
        if i != 7:
            bar(f"Rail{i}", [(x0, y0, 2.2), (x1, y1, 2.2)], 0.04, K["iron"], seg=4)
            for k in range(1, 8):
                t = k / 8
                bar(f"Spindle{i}{k}", [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.6), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 2.2)], 0.025, K["iron"], seg=4)
    # the onion dome
    prof = [(R + 0.8, zt + 0.05), (R + 0.2, zt + 0.5), (R - 1.2, zt + 1.0), (R - 2.2, zt + 1.6), (R - 2.0, zt + 2.6), (R - 1.6, zt + 3.6), (R - 2.4, zt + 4.8),
            (R - 3.8, zt + 6.0), (1.0, zt + 7.0), (0.4, zt + 7.8), (0, zt + 8.2)]
    roof = lathe("Roof", [(0, zt + 0.05)] + prof, mossy(material("RoofSlate", "NH_Slate", tint=(0.17, 0.18, 0.22), scale=0.6, rough_mul=0.6, rough_add=0.3,
                                                                normal=0.7, wear=0.3), 0.25), seg=16)
    for i in range(8):
        a = -math.pi / 2 + math.pi / 8 + i * math.pi / 4
        bar(f"Rib{i}", [(math.cos(a) * (r + 0.05), math.sin(a) * (r + 0.05), z + 0.04) for r, z in prof], 0.07, K["iron"], seg=4)
    ztop = zt + 8.2
    cyl("LanternBase", 0.32, 0.2, (0, 0, ztop + 0.1), K["iron"], verts=8, bevel=0.02)
    set_group("Glass")
    cyl("Lantern", 0.26, 0.7, (0, 0, ztop + 0.55), K["glass"], verts=8, bevel=0.0)
    set_group("Main")
    for k in range(8):
        a = k / 8 * 2 * math.pi
        bar(f"LanternBar{k}", [(math.cos(a) * 0.28, math.sin(a) * 0.28, ztop + 0.2), (math.cos(a) * 0.28, math.sin(a) * 0.28, ztop + 0.9)], 0.02, K["iron"], seg=4)
    cone("LanternRoof", 0.38, 0.0, 0.6, (0, 0, ztop + 1.2), K["iron"], verts=8)
    bar("Spire", [(0, 0, ztop + 1.4), (0, 0, ztop + 2.3)], 0.04, K["iron"], seg=4)
    s = _mark()
    ring_slab("SpireMoon", (0, 0), 0.22, 0.3, 0.6, 5.7, -0.02, 0.02, K["brass"], n=12)
    _xform(s, T(0, 0, ztop + 2.45) @ RX(math.pi / 2))
    for i in range(7):
        (x0, y0), (x1, y1) = posts[i], posts[(i + 1) % 8]
        mx, my = (x0 + x1) / 2 * 0.86, (y0 + y1) / 2 * 0.86
        a = math.atan2(my, mx)
        s = _mark()
        box(f"BenchSeat{i}", (3.4, 1.0, 0.12), (0, 0, 2.3), K["oak"], bevel=0.03, segments=2)
        for sx in (-1, 1):
            box(f"BenchLeg{i}{sx}", (0.1, 0.8, 1.64), (sx * 1.4, 0, 1.42), K["iron"], bevel=0.02, segments=1)
        box(f"BenchBack{i}", (3.4, 0.1, 0.5), (0, 0.5, 3.1), K["oak"], bevel=0.02, segments=2)
        _xform(s, T(mx, my, 0) @ RZ(a - math.pi / 2))
    return _dims()

def rose_arbor(M):
    """An iron rose arbor 6.2 wide, 2 deep, 9.2 tall (walk-through along Y, opening 5 wide): two lattice sides, a round arch
    of twin bars with a crest boss, climbing crimson roses over it all."""
    K = gk2(M)
    rng = RNG(55)
    hw, D, zs = 2.6, 0.9, 5.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            bar(f"Up{sx}{sy}", [(sx * hw, sy * D, 0), (sx * hw, sy * D, zs)], 0.06, K["iron"], seg=5)
        for k in range(9):      # lattice: diagonals between the uprights
            z0 = 0.4 + k * 0.6
            bar(f"Lat{sx}{k}a", [(sx * hw, -D, z0), (sx * hw, D, z0 + 0.6)], 0.022, K["iron"], seg=4)
            bar(f"Lat{sx}{k}b", [(sx * hw, D, z0), (sx * hw, -D, z0 + 0.6)], 0.022, K["iron"], seg=4)
    for sy in (-1, 1):
        for rr in (hw, hw - 0.3):
            bar(f"Arch{sy}{rr}", [(math.cos(a) * rr, sy * D, zs + math.sin(a) * rr * 1.1) for a in [i / 14 * math.pi for i in range(15)]], 0.05, K["iron"], seg=5)
        for k in range(1, 10):
            a = k / 10 * math.pi
            bar(f"Tie{sy}{k}", [(math.cos(a) * hw, sy * D, zs + math.sin(a) * hw * 1.1), (math.cos(a) * (hw - 0.3), sy * D, zs + math.sin(a) * (hw - 0.3) * 1.1)],
                0.025, K["iron"], seg=4)
    for k in range(7):
        a = k / 6 * math.pi
        bar(f"Purlin{k}", [(math.cos(a) * hw, -D, zs + math.sin(a) * hw * 1.1), (math.cos(a) * hw, D, zs + math.sin(a) * hw * 1.1)], 0.03, K["iron"], seg=4)
    cyl("Boss", 0.3, 0.08, (0, -D - 0.06, zs + hw * 1.1 - 0.15), K["brass"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.02)
    for sx in (-1, 1):
        bar(f"Stem{sx}", [(sx * hw, -D + 0.2, 0)] + [(sx * hw + 0.1 * math.sin(i), -D + 0.2 + 0.2 * math.cos(i * 1.3), i * 0.75) for i in range(1, 9)], 0.07, K["bark"], seg=5)
    cards = Cards(rng)
    for sx in (-1, 1):
        for k in range(26):
            z = rng.uniform(0.6, zs)
            y = rng.uniform(-D - 0.2, D + 0.2)
            n = Vector((sx * 1.0 + rng.uniform(-0.6, 0.6), rng.uniform(-0.8, 0.8), rng.uniform(-0.2, 0.4))).normalized()
            ax, ay = frame(n, roll=rng.uniform(0, 6.28))
            cards.add((sx * (hw + 0.1), y, z), ax, ay, 1.3, 1.3, "rose_crimson", "fill", nrm=n)
    for k in range(60):
        a = rng.uniform(0, math.pi)
        y = rng.uniform(-D - 0.3, D + 0.3)
        p = Vector((math.cos(a) * (hw + 0.15), y, zs + math.sin(a) * (hw + 0.15) * 1.1))
        n = Vector((math.cos(a), 0, math.sin(a))).normalized()
        t = (n + Vector((rng.normal(), rng.normal(), rng.normal())) * 0.4).normalized()
        ax, ay = frame(t, roll=rng.uniform(0, 6.28))
        cards.add(p, ax, ay, 1.35, 1.35, "rose_crimson", "fill", nrm=n)
    for k in range(10):
        a = rng.uniform(0.2, math.pi - 0.2)
        cards.hang((math.cos(a) * (hw - 0.2), rng.uniform(-D, D), zs + math.sin(a) * (hw - 0.2) * 1.1), 1.1, 1.4, "rose_crimson", sway=0.05, segs=1)
    cards.build("Leaves")
    P.ATLAS["RoseArbor_Leaves"] = "NH_GardenLeaves"
    return _dims()


def garden_obelisk(M):
    """A limestone obelisk 9 tall on a stepped base, the moon's phases carved down each face in raised discs (new to full on
    the front, full to new on the back), a brass-capped pyramidion, ivy creeping up from its foot."""
    K = gk2(M)
    rng = RNG(56)
    box("Step1", (2.6, 2.6, 0.35), (0, 0, 0.175), K["lime"], bevel=0.05, segments=2)
    box("Step2", (2.0, 2.0, 0.35), (0, 0, 0.525), K["lime"], bevel=0.05, segments=2)
    box("Die", (1.5, 1.5, 1.2), (0, 0, 1.3), K["limel"], bevel=0.04, segments=2)
    box("Cornice", (1.75, 1.75, 0.2), (0, 0, 2.0), K["lime"], bevel=0.04, segments=2)
    H, b0, b1 = 6.2, 0.6, 0.38
    z0 = 2.1
    V = [(-b0, -b0, z0), (b0, -b0, z0), (b0, b0, z0), (-b0, b0, z0), (-b1, -b1, z0 + H), (b1, -b1, z0 + H), (b1, b1, z0 + H), (-b1, b1, z0 + H),
         (0, 0, z0 + H + 0.6)]
    F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 8), (5, 6, 8), (6, 7, 8), (7, 4, 8), (3, 2, 1, 0)]
    ob = mk("Shaft", V, F, K["limel"], smooth=False)
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = 0.03
    md.segments = 2
    cone("Cap", 0.2, 0.0, 0.32, (0, 0, z0 + H + 0.5), K["brassf"], verts=4, rot=(0, 0, math.pi / 4))
    for face in range(4):
        for k in range(8):
            z = z0 + 0.5 + k * 0.7
            half = b0 + (b1 - b0) * (z - z0) / H
            phase = k if face % 2 == 0 else 7 - k
            s = _mark()
            cyl(f"Disc{face}{k}", 0.25, 0.04, (0, 0, 0), K["slatec"], rot=(math.pi / 2, 0, 0), verts=20, bevel=0.0)
            lit = moon_phase_outline(phase, 0.2)
            if lit is not None:
                tprism(f"Moon{face}{k}", lit, -0.035, 0.03, K["limel"])
            else:
                ringbar(f"NewMoon{face}{k}", (0, -0.03, 0), 0.18, "Y", K["limel"], thick=0.015, n=14, seg=4)
            _xform(s, RZ(face * math.pi / 2) @ T(0, -half - 0.01, z) @ RX(math.atan2(b0 - b1, H)))
    cards = Cards(rng)
    for k in range(16):
        a = rng.uniform(0, 6.28)
        side = k % 4
        n = Vector((math.cos(side * math.pi / 2 - math.pi / 2), math.sin(side * math.pi / 2 - math.pi / 2), 0))
        t = n.cross(UP)
        p = n * 0.78 + t * rng.uniform(-0.7, 0.7) + UP * rng.uniform(0.6, 2.3)
        ax, ay = frame(n, roll=rng.uniform(-0.5, 0.5))
        cards.add(tuple(p), ax, ay, 0.9, 0.9, "ivy", "fill", nrm=n)
    cards.build("Leaves")
    P.ATLAS["GardenObelisk_Leaves"] = "NH_GardenLeaves"
    return _dims()

def urn_pedestal(M):
    """A gadrooned limestone urn on a panelled pedestal, 5.4 to the rim: two serpents for handles, coiled on its shoulders with
    their heads raised over the lip; lavender and a fern in it, ivy trailing over."""
    K = gk2(M)
    rng = RNG(57)
    box("Plinth", (1.9, 1.9, 0.35), (0, 0, 0.175), K["lime"], bevel=0.05, segments=2)
    box("Die", (1.45, 1.45, 2.0), (0, 0, 1.35), K["lime"], bevel=0.05, segments=2)
    for k in range(4):
        s = _mark()
        box(f"Panel{k}", (0.95, 0.06, 1.4), (0, -0.73, 1.35), K["limel"], bevel=0.03, segments=1)
        _xform(s, RZ(k * math.pi / 2))
    box("Cap", (1.8, 1.8, 0.25), (0, 0, 2.47), K["lime"], bevel=0.05, segments=2)
    lathe("Urn", [(0, 2.6), (0.45, 2.6), (0.38, 2.8), (0.3, 2.95), (0.55, 3.15), (0.95, 3.6), (1.1, 4.1), (1.0, 4.6), (0.85, 4.9), (1.05, 5.15),
                  (1.12, 5.35), (1.0, 5.4), (0.85, 5.2), (0, 5.15)], K["lime"], seg=24, flute=(14, 0.06))
    for sx in (-1, 1):          # the serpents
        pts = []
        for i in range(22):
            t = i / 21
            if t < 0.55:        # coiled round the shoulder
                a = t / 0.55 * math.pi * 1.6
                pts.append((sx * (1.08 + 0.12 * math.cos(a)), 0.12 * math.sin(a) * 2.2 - 0.2, 3.9 + t * 0.9 + 0.12 * math.sin(a)))
            else:               # rising over the lip, the head lifted and turned out
                u = (t - 0.55) / 0.45
                pts.append((sx * (1.05 + 0.35 * math.sin(u * 2.4)), -0.2 - 0.25 * u, 4.4 + u * 1.3 - u * u * 0.35))
        bar(f"Serpent{sx}", pts, lambda t: 0.09 * math.sin(math.pi * min(1.0, t * 0.9 + 0.12)) + 0.03, K["limel"], seg=8)
        head = Vector(pts[-1])
        blob(f"SnakeHead{sx}", tuple(head + Vector((sx * 0.05, -0.12, 0.02))), 0.13, K["limel"], seg=10, rings=6, scale=(0.8, 1.4, 0.6))
        for e in (-1, 1):
            sphere(f"SnakeEye{sx}{e}", 0.025, tuple(head + Vector((sx * 0.05 + e * 0.08, -0.2, 0.08))), K["ink"], seg=6, rings=4)
    cyl("Soil", 0.88, 0.05, (0, 0, 5.2), K["soil"], verts=14, bevel=0.0)
    cards = Cards(rng)
    cards.crossed((0.2, 0.1, 5.2), 1.3, 1.7, "lavender", k=3)
    cards.fronds((-0.3, 0.1, 5.2), 6, 1.5, 0.75, "fern", elev=(20, 55))
    for k in range(7):
        a = k / 7 * 6.28 + rng.uniform(-0.2, 0.2)
        p = (math.cos(a) * 1.1, math.sin(a) * 1.1, 5.25)
        n = Vector((math.cos(a), math.sin(a), 0.1)).normalized()
        ax, ay = frame(n)
        cards.add(p, ax, ay, 0.9, rng.uniform(1.4, 2.2), "ivy", "top", segs=2, bend=n * 0.4, nrm=n)
    cards.build("Leaves")
    P.ATLAS["UrnPedestal_Leaves"] = "NH_GardenLeaves"
    return _dims()

def low_wall(M):
    """A mossy garden wall 8 long, 1.4 thick, 3.0 tall to its coping (GothicStone ashlar, rain-streaked, moss along the foot
    and coping), ivy spilling over one end. Snaps end to end."""
    K = gk2(M)
    rng = RNG(58)
    box("Wall", (8.0, 1.2, 2.6), (0, 0, 1.3), K["wall"], bevel=0.04, segments=1)
    box("Plinth", (8.0, 1.4, 0.4), (0, 0, 0.2), K["wall"], bevel=0.04, segments=1)
    for k in range(4):
        box(f"Cope{k}", (1.98, 1.55, 0.32), (-3 + k * 2, 0, 2.76), K["lime"], bevel=0.06, segments=1)
        cyl(f"Bull{k}", 0.15, 1.94, (-3 + k * 2, 0, 2.93), K["lime"], rot=(0, math.pi / 2, 0), verts=8, bevel=0.0)
    cards = Cards(rng)
    for k in range(18):
        x = rng.uniform(1.2, 4.0)
        side = -1 if k % 2 else 1
        n = Vector((0, side, 0.1)).normalized()
        ax, ay = frame(n)
        cards.add((x, side * 0.82, 3.05), ax, ay, 1.2, rng.uniform(1.4, 2.6), "ivy", "top", segs=2, bend=n * 0.15, nrm=n)
    for k in range(6):
        cards.crossed((rng.uniform(-3.8, 3.8), -0.85, 0.0), 0.9, 0.9, "grass", k=2)
    cards.build("Leaves")
    P.ATLAS["LowGardenWall_Leaves"] = "NH_GardenLeaves"
    return _dims()


def wall_pier(M):
    """A garden-wall pier 1.9 square, 4.9 to the top of its ball finial: a plinth, ashlar shaft, a moulded cap and a ball on a
    neck. Sits at the end of a LowGardenWall run (the wall's top is 3.0)."""
    K = gk2(M)
    box("Plinth", (2.1, 2.1, 0.45), (0, 0, 0.225), K["wall"], bevel=0.05, segments=1)
    box("Shaft", (1.8, 1.8, 2.9), (0, 0, 1.9), K["wall"], bevel=0.04, segments=1)
    box("CapA", (2.15, 2.15, 0.22), (0, 0, 3.46), K["lime"], bevel=0.05, segments=1)
    box("CapB", (1.9, 1.9, 0.18), (0, 0, 3.66), K["lime"], bevel=0.04, segments=1)
    lathe("Neck", [(0, 3.75), (0.45, 3.75), (0.42, 3.85), (0.22, 3.95), (0.2, 4.05), (0, 4.05)], K["lime"], seg=12)
    sphere("Ball", 0.48, (0, 0, 4.45), K["lime"], seg=14, rings=8)
    return _dims()


def stone_lantern(M):
    """A gothic stone lantern post 7.4 tall: a Solomonic column twisting up from a moulded base to a capital, a forged iron cage
    round a glass chimney with a candle flame in it (Glass, Glow), a crocketed stone canopy and finial over the cage."""
    K = gk2(M)
    st = K["limel"]
    box("Plinth", (1.5, 1.5, 0.45), (0, 0, 0.225), K["lime"], bevel=0.05, segments=2)
    lathe("Base", [(0, 0.45), (0.6, 0.45), (0.6, 0.55), (0.5, 0.65), (0.52, 0.75), (0.42, 0.85), (0, 0.85)], st, seg=20)
    # the twisted column: a quatrefoil section turning as it rises
    rings, n = 24, 24
    V, F = [], []
    for i in range(rings + 1):
        t = i / rings
        z = 0.85 + t * 3.4
        rot = t * math.pi * 2.0
        for j in range(n):
            a = j / n * 2 * math.pi
            r = 0.3 * (1 + 0.22 * math.cos(4 * (a - rot)))
            V.append((math.cos(a) * r, math.sin(a) * r, z))
    for i in range(rings):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            F.append((a, b, b + n, a + n))
    P_recalc(mk("Column", V, F, st, smooth=True))
    lathe("Capital", [(0, 4.25), (0.38, 4.25), (0.55, 4.45), (0.62, 4.6), (0.62, 4.7), (0, 4.7)], st, seg=20)
    zc = 4.7
    for k in range(8):           # the cage
        a = k / 8 * 2 * math.pi
        bar(f"CageBar{k}", [(math.cos(a) * 0.42, math.sin(a) * 0.42, zc), (math.cos(a) * 0.5, math.sin(a) * 0.5, zc + 0.6), (math.cos(a) * 0.42, math.sin(a) * 0.42, zc + 1.2)],
            0.025, K["iron"], seg=4)
    for z in (zc + 0.05, zc + 0.6, zc + 1.18):
        ringbar(f"CageRing{z:.2f}", (0, 0, z), 0.5 if abs(z - zc - 0.6) < 0.01 else 0.43, "Z", K["iron"], thick=0.03, n=16, seg=4)
    set_group("Glass")
    lathe("Chimney", [(0.2, zc + 0.05), (0.26, zc + 0.5), (0.22, zc + 1.0), (0.0, zc + 1.0)], K["glass"], seg=12)
    set_group("Glow")
    lathe("Flame", [(0, 0), (0.06, 0.04), (0.08, 0.12), (0.06, 0.22), (0.03, 0.32), (0, 0.38)], K["glow"], seg=8, loc=(0, 0, zc + 0.35))
    set_group("Main")
    cyl("Candle", 0.07, 0.3, (0, 0, zc + 0.2), K["bone"], verts=10, bevel=0.0)
    lathe("Canopy", [(0, zc + 1.2), (0.7, zc + 1.2), (0.72, zc + 1.32), (0.5, zc + 1.4), (0.08, zc + 2.4), (0, zc + 2.45)], st, seg=8)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        for t in (0.3, 0.65):
            r = 0.5 * (1 - t) + 0.08
            sphere(f"Crocket{k}{t}", 0.07, (math.cos(a) * r, math.sin(a) * r, zc + 1.4 + t), st, seg=6, rings=4)
    sphere("Finial", 0.14, (0, 0, zc + 2.55), st, seg=10, rings=6)
    return _dims()

def wheelbarrow(M):
    """A wooden wheelbarrow with an iron-shod spoked wheel, 5.2 long (wheel at -Y), heaped with soil and a trowel stuck in it."""
    K = gk2(M)
    s = _mark()
    # tray: a trapezoid box of boards
    bot = [(-0.8, -1.0), (0.8, -1.0), (0.8, 1.2), (-0.8, 1.2)]
    box("TrayFloor", (1.6, 2.2, 0.08), (0, 0.1, 1.2), K["oakd"], bevel=0.02, segments=1)
    for sx in (-1, 1):
        V = [(sx * 0.8, -1.0, 1.2), (sx * 0.8, 1.2, 1.2), (sx * 1.15, 1.5, 2.2), (sx * 1.15, -1.5, 2.2)]
        V += [(x - sx * 0.08, y, z) for x, y, z in V]
        P_recalc(mk(f"Side{sx}", V, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], K["oakd"], smooth=False, bevel=0.015))
    for sy, (y0, y1) in ((-1, (-1.0, -1.5)), (1, (1.2, 1.5))):
        V = [(-0.8, y0, 1.2), (0.8, y0, 1.2), (1.15, y1, 2.2), (-1.15, y1, 2.2)]
        V += [(x, y - sy * 0.08, z) for x, y, z in V]
        P_recalc(mk(f"End{sy}", V, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], K["oakd"], smooth=False, bevel=0.015))
    soil = mound("Soil", 1.0, 1.35, 0.6, K["soil"], RNG(1), z0=1.6, seg=12)
    for sx in (-1, 1):
        bar(f"Handle{sx}", [(sx * 0.7, -2.0, 0.85), (sx * 0.75, 0.0, 1.1), (sx * 0.9, 2.9, 1.6)], 0.07, K["oak"], seg=6)
        bar(f"Grip{sx}", [(sx * 0.9, 2.5, 1.55), (sx * 0.9, 3.0, 1.63)], 0.09, K["oakd"], seg=6)
        bar(f"Leg{sx}", [(sx * 0.75, 1.2, 1.15), (sx * 0.8, 1.4, 0.0)], 0.06, K["iron"], seg=5)
    # the wheel
    ringbar("Tyre", (0, -2.0, 0.85), 0.8, "X", K["iron"], thick=0.07, n=24, seg=6)
    cyl("Hub", 0.14, 0.3, (0, -2.0, 0.85), K["iron"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.02)
    for k in range(8):
        a = k / 8 * 6.28
        bar(f"Spoke{k}", [(0, -2.0, 0.85), (0, -2.0 + math.cos(a) * 0.76, 0.85 + math.sin(a) * 0.76)], 0.035, K["oakd"], seg=4)
    bar("Axle", [(-0.75, -2.0, 0.85), (0.75, -2.0, 0.85)], 0.04, K["iron"], seg=5)
    # a trowel stuck in the soil
    st = _mark()
    poly_slab("TrowelBlade", [(-0.12, 0), (0.12, 0), (0.08, 0.3), (0, 0.4), (-0.08, 0.3)], -0.01, 0.01, K["zinc"])
    P.PARTS[-1].matrix_world = RX(math.pi / 2) @ RX(math.pi)
    bar("TrowelShank", [(0, 0, 0), (0, 0, 0.15)], 0.015, K["zinc"], seg=4)
    cyl("TrowelGrip", 0.05, 0.35, (0, 0, 0.32), K["oak"], verts=8, bevel=0.02)
    _xform(st, T(0.3, 0.4, 2.0) @ RX(0.3))
    return _dims()


def garden_tools(M):
    """A rake, a spade and a garden fork leaning against an old slatted crate (2.4 wide, 1.6 tall), a sack of bulbs beside it."""
    K = gk2(M)
    rng = RNG(60)
    for k in range(4):
        box(f"CrateSlat{k}", (2.4, 0.08, 0.32), (0, -0.6, 0.2 + k * 0.4), K["oakd"], bevel=0.02, segments=1)
        box(f"CrateSlatB{k}", (2.4, 0.08, 0.32), (0, 0.6, 0.2 + k * 0.4), K["oakd"], bevel=0.02, segments=1)
    for sx in (-1, 1):
        box(f"CrateEnd{sx}", (0.08, 1.28, 1.56), (sx * 1.16, 0, 0.78), K["oakd"], bevel=0.02, segments=1)
        for sy in (-1, 1):
            box(f"CratePost{sx}{sy}", (0.14, 0.14, 1.6), (sx * 1.1, sy * 0.55, 0.8), K["oak"], bevel=0.02, segments=1)
    def tool(prefix, x, lean, kind):
        s = _mark()
        cyl(f"{prefix}Haft", 0.05, 4.4, (0, 0, 2.2), K["oak"], verts=8, bevel=0.01)
        if kind == "rake":
            box(f"{prefix}Head", (1.0, 0.08, 0.08), (0, 0, 4.45), K["iron"], bevel=0.01, segments=1)
            for j in range(10):
                cone(f"{prefix}Tine{j}", 0.018, 0.005, 0.25, (-0.45 + j * 0.1, -0.02, 4.55), K["iron"], verts=4)
        elif kind == "spade":
            box(f"{prefix}Blade", (0.5, 0.04, 0.7), (0, 0, -0.25), K["zinc"], bevel=0.02, segments=1)
            bar(f"{prefix}Grip", [(-0.2, 0, 4.6), (0, 0, 4.75), (0.2, 0, 4.6)], 0.04, K["oakd"], seg=5)
        else:
            for j in range(4):
                bar(f"{prefix}Tine{j}", [(-0.18 + j * 0.12, 0, 0.05), (-0.18 + j * 0.12, -0.02, -0.65)], 0.022, K["iron"], seg=4)
            box(f"{prefix}Bar", (0.46, 0.06, 0.08), (0, 0, 0.05), K["iron"], bevel=0.01, segments=1)
            bar(f"{prefix}Grip", [(-0.2, 0, 4.6), (0, 0, 4.75), (0.2, 0, 4.6)], 0.04, K["oakd"], seg=5)
        zb = {"spade": 0.62, "fork": 0.68, "rake": 0.02}[kind]
        yb = -0.66 - (1.65 - zb) * math.tan(lean)
        _xform(s, T(x, yb, zb) @ RX(-lean))
    tool("Spade", -0.6, 0.22, "spade")
    tool("Fork", 0.1, 0.2, "fork")
    tool("Rake", 0.75, 0.24, "rake")
    sack = B24.cloth("Burlap", (0.32, 0.25, 0.15), rough=0.95, weave=0.02)
    lathe("Sack", [(0, 0), (0.5, 0), (0.6, 0.3), (0.55, 0.8), (0.3, 1.05), (0.2, 1.2), (0.28, 1.3), (0, 1.25)], sack, seg=12, loc=(1.9, -0.2, 0), jitter=(0.06, 4))
    for k in range(5):
        sphere(f"Bulb{k}", 0.1, (1.6 + rng.uniform(-0.2, 0.2), -0.75 + rng.uniform(-0.2, 0.2), 0.08), flat("Bulb", (0.45, 0.32, 0.18), 0.8), seg=6, rings=4)
    return _dims()


def potting_cluster(M):
    """Terracotta pots on the ground, 4 x 2.5: a big pot with a fern, two with lavender and a seedling, a stack of empties, one
    on its side, a zinc watering can with a brass rose, and a trowel."""
    K = gk2(M)
    rng = RNG(61)
    def pot(name, x, y, r, h, rot=None):
        ob = lathe(name, [(0, 0), (r * 0.72, 0), (r, h * 0.92), (r * 1.1, h * 0.94), (r * 1.1, h), (r * 0.98, h), (r * 0.9, h * 0.94), (r * 0.65, h * 0.1),
                          (0, h * 0.1)], K["terra"], seg=14, loc=(0, 0, 0))
        ob.matrix_world = (T(x, y, 0) @ rot) if rot is not None else T(x, y, 0)
        return ob
    pot("PotBig", -1.2, 0.3, 0.75, 1.3)
    cyl("SoilBig", 0.7, 0.04, (-1.2, 0.3, 1.18), K["soil"], verts=12, bevel=0.0)
    pot("PotA", 0.2, 0.6, 0.45, 0.8)
    cyl("SoilA", 0.42, 0.04, (0.2, 0.6, 0.72), K["soil"], verts=10, bevel=0.0)
    pot("PotB", 0.9, -0.3, 0.38, 0.65)
    cyl("SoilB", 0.35, 0.04, (0.9, -0.3, 0.58), K["soil"], verts=10, bevel=0.0)
    for k in range(3):
        pot(f"Stack{k}", 1.8, 0.7, 0.32, 0.55).matrix_world = T(1.8, 0.7, k * 0.18)
    pot("Fallen", -0.3, -0.7, 0.3, 0.5, rot=T(0, 0, 0.3) @ RY(math.pi / 2) @ RZ(0.4))
    cards = Cards(rng)
    cards.fronds((-1.2, 0.3, 1.18), 7, 1.7, 0.85, "fern", elev=(30, 65))
    cards.crossed((0.2, 0.6, 0.72), 1.0, 1.3, "lavender", k=3)
    cards.crossed((0.9, -0.3, 0.58), 0.6, 0.6, "grass", k=2)
    cards.build("Leaves")
    # the watering can
    s = _mark()
    lathe("CanBody", [(0, 0), (0.38, 0), (0.4, 0.05), (0.4, 0.75), (0.3, 0.85), (0, 0.85)], K["zinc"], seg=14)
    bar("CanSpout", [(0.35, 0, 0.2), (0.8, 0, 0.7), (1.05, 0, 0.95)], lambda t: 0.06 - t * 0.03, K["zinc"], seg=6)
    cone("CanRose", 0.04, 0.11, 0.12, (1.08, 0, 0.99), K["brassf"], verts=10, rot=(0, math.radians(55), 0))
    bar("CanHandle", [(-0.3, 0, 0.8), (-0.05, 0, 1.15), (0.2, 0, 0.82)], 0.035, K["zinc"], seg=5)
    _xform(s, T(-0.3, -0.2 - 1.0, 0) @ RZ(-0.6))
    st = _mark()
    poly_slab("TrowelBlade", [(-0.1, 0), (0.1, 0), (0.07, 0.26), (0, 0.34), (-0.07, 0.26)], 0, 0.015, K["zinc"])
    cyl("TrowelGrip", 0.045, 0.32, (0, -0.2, 0.05), K["oak"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.015)
    _xform(st, T(1.4, -0.9, 0) @ RZ(0.8))
    P.ATLAS["PottingCluster_Leaves"] = "NH_GardenLeaves"
    return _dims()


def cold_frame(M):
    """A brick cold frame 4.4 x 2.6 (back 1.3 high, front 0.8) with a glazed oak lid propped open on a notched stick; rows of
    seedlings in the soil inside. Glass: the panes."""
    K = gk2(M)
    rng = RNG(62)
    W, D = 4.4, 2.6
    def wall(name, x0, y0, x1, y1, h0, h1):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * 0.22, dx / L * 0.22
        V = [(x0, y0, 0), (x1, y1, 0), (x1, y1, h1), (x0, y0, h0), (x0 + nx, y0 + ny, 0), (x1 + nx, y1 + ny, 0), (x1 + nx, y1 + ny, h1), (x0 + nx, y0 + ny, h0)]
        P_recalc(mk(name, V, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], K["bricks"][1], smooth=False, bevel=0.02))
    wall("Front", W / 2, -D / 2, -W / 2, -D / 2, 0.8, 0.8)
    wall("Back", -W / 2, D / 2, W / 2, D / 2, 1.3, 1.3)
    wall("Left", -W / 2, -D / 2, -W / 2, D / 2, 0.8, 1.3)
    wall("Right", W / 2, D / 2, W / 2, -D / 2, 1.3, 0.8)
    box("Soil", (W - 0.44, D - 0.44, 0.3), (0, 0, 0.35), K["soil"], bevel=0.0)
    s = _mark()
    L = math.hypot(D, 0.5)
    for sx in (-1, 1):
        box(f"LidRail{sx}", (0.12, L, 0.1), (sx * (W / 2 - 0.06), -L / 2, 0), K["oak"], bevel=0.02, segments=1)
    for k in range(3):
        box(f"LidBar{k}", (W, 0.12, 0.1), (0, -L * k / 2, 0), K["oak"], bevel=0.02, segments=1)
    box("LidMid", (0.08, L, 0.08), (0, -L / 2, 0), K["oak"], bevel=0.015, segments=1)
    set_group("Glass")
    box("Panes", (W - 0.2, L - 0.15, 0.02), (0, -L / 2, 0.0), K["glass"], bevel=0.0)
    set_group("Main")
    _xform(s, T(0, D / 2, 1.38) @ RX(-math.atan2(0.5, D) + 0.45))
    bar("Prop", [(1.4, -0.9, 0.8), (1.4, -0.95, 1.65)], 0.04, K["oak"], seg=5)
    cards = Cards(rng)
    for i in range(6):
        for j in range(3):
            cards.crossed((-1.6 + i * 0.65, -0.6 + j * 0.6, 0.5), 0.45, 0.5, "grass" if j == 1 else "fern", k=2)
    cards.build("Leaves")
    P.ATLAS["ColdFrame_Leaves"] = "NH_GardenLeaves"
    return _dims()


def trellis_panel(M):
    """A free-standing iron trellis panel 4.4 wide, 7.6 tall (diamond lattice in a frame with a pointed top), its feet in two
    stone blocks; crimson climbing roses over it. Pivot at the base centre (the panel is in the XZ plane)."""
    K = gk2(M)
    rng = RNG(63)
    hw, H = 2.0, 6.4
    for sx in (-1, 1):
        box(f"Foot{sx}", (0.5, 0.5, 0.35), (sx * hw, 0, 0.175), K["lime"], bevel=0.04, segments=1)
        bar(f"Side{sx}", [(sx * hw, 0, 0.2), (sx * hw, 0, H)], 0.05, K["iron"], seg=4)
        bar(f"Top{sx}", [(sx * hw, 0, H), (0, 0, H + 1.0)], 0.05, K["iron"], seg=4)
    bar("Bottom", [(-hw, 0, 0.5), (hw, 0, 0.5)], 0.045, K["iron"], seg=4)
    step = 0.8
    for k in range(-8, 9):
        x0 = k * step
        for d in (-1, 1):
            # a diagonal from (x0, 0.5) going up at 45 degrees, clipped to the frame
            pts = []
            for t in [i / 20 for i in range(21)]:
                z = 0.5 + t * 8
                x = x0 + d * (z - 0.5)
                top = H if abs(x) > 0 else H
                topz = H + 1.0 * (1 - abs(x) / hw)
                if -hw <= x <= hw and z <= topz:
                    pts.append((x, 0, z))
            if len(pts) >= 2:
                bar(f"Lat{k}{d}", [pts[0], pts[-1]], 0.02, K["iron"], seg=4)
    sphere("Finial", 0.12, (0, 0, H + 1.12), K["iron"], seg=8, rings=5)
    cards = Cards(rng)
    for k in range(46):
        x, z = rng.uniform(-hw - 0.2, hw + 0.2), rng.uniform(0.5, H + 0.4)
        if z > H + 0.8 * (1 - abs(x) / hw):
            continue
        side = -1 if k % 2 else 1
        n = Vector((rng.uniform(-0.4, 0.4), side, rng.uniform(-0.1, 0.4))).normalized()
        ax, ay = frame(n, roll=rng.uniform(0, 6.28))
        cards.add((x, side * 0.1, z), ax, ay, 1.3, 1.3, "rose_crimson", "fill", nrm=n)
    cards.build("Leaves")
    bar("RoseStem", [(-1.2, 0.05, 0)] + [(-1.2 + 0.5 * math.sin(i * 0.9), 0.05, i * 0.8) for i in range(1, 8)], 0.06, K["bark"], seg=5)
    P.ATLAS["TrellisPanel_Leaves"] = "NH_GardenLeaves"
    return _dims()


def keep_off_sign(M):
    """A small brass plaque on an iron stake, 1.9 tall, facing -Y: KEEP OFF THE LAWN in raised black letters on the brass,
    a crimson enamel border (an invented sign)."""
    K = gk2(M)
    bar("Stake", [(0, 0.04, -0.4), (0, 0.04, 1.75)], 0.04, K["iron"], seg=6)
    s = _mark()
    w, h = 1.5, 0.62
    box("Plate", (w, 0.05, h), (0, 0, 0), K["brassf"], bevel=0.015, segments=1)
    box("Enamel", (w - 0.08, 0.012, h - 0.08), (0, -0.028, 0), K["crimson"], bevel=0.0)
    box("Field", (w - 0.18, 0.014, h - 0.18), (0, -0.032, 0), K["brassf"], bevel=0.0)
    _text("Line1", "KEEP OFF", FONT, K["ink"], lambda x, y, d: (x, -0.04 - d, 0.09 + y), fit=(1.0, 0.15), depth=0.012, res=1)
    _text("Line2", "THE LAWN", FONT, K["ink"], lambda x, y, d: (x, -0.04 - d, -0.1 + y), fit=(1.0, 0.15), depth=0.012, res=1)
    for sx in (-1, 1):
        sphere(f"Rivet{sx}", 0.03, (sx * (w / 2 - 0.05), -0.03, 0), K["brassf"], seg=6, rings=3)
    _xform(s, T(0, 0, 1.6) @ RX(-0.12))
    _fine(0.5)
    return _dims()


def birdhouse(M):
    """A birdhouse built as a little gothic chapel on a post, 7.3 tall: a steep slate-roofed nave with buttresses, a pointed
    door (the hole) under a rose window at the front (-Y), a bell tower with a needle spire over the door, a perch."""
    K = gk2(M)
    from nh_props_batch20 import tprism
    box("Post", (0.28, 0.28, 5.0), (0, 0.2, 2.5), K["oakd"], bevel=0.03, segments=2)
    bar("Brace", [(0, 0.35, 4.2), (0, 0.85, 4.95)], 0.05, K["oakd"], seg=4)
    box("Floor", (1.1, 1.6, 0.08), (0, 0.2, 5.04), K["oakd"], bevel=0.02, segments=1)
    hw, zs, za = 0.42, 5.75, 6.4
    nave = tprism("Nave", [(-hw, 5.08), (hw, 5.08), (hw, zs), (0, za), (-hw, zs)], 0.25, 1.3, K["limel"], plane="XZ")
    for sx in (-1, 1):
        V = [(0, -0.45, za + 0.06), (0, 0.95, za + 0.06), (sx * (hw + 0.12), 0.95, zs - 0.08), (sx * (hw + 0.12), -0.45, zs - 0.08)]
        V += [(x, y, z + 0.05) for x, y, z in V]
        P_recalc(mk(f"Roof{sx}", V, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], K["slate"], smooth=False, bevel=0.01))
        for y in (-0.1, 0.5):
            V = [(sx * hw, y - 0.07, 5.08), (sx * (hw + 0.18), y - 0.07, 5.08), (sx * hw, y - 0.07, zs - 0.05)]
            tprism(f"Buttress{sx}{y}", [(sx * hw, 5.08), (sx * (hw + 0.18), 5.08), (sx * (hw + 0.04), zs - 0.1), (sx * hw, zs - 0.05)] if sx > 0 else
                   [(sx * hw, 5.08), (sx * hw, zs - 0.05), (sx * (hw + 0.04), zs - 0.1), (sx * (hw + 0.18), 5.08)], y, 0.12, K["limel"], plane="XZ")
    tprism("Door", [(-0.1, 5.25), (0.1, 5.25), (0.1, 5.45), (0, 5.6), (-0.1, 5.45)], -0.43, 0.02, K["ink"])
    cyl("RoseWindow", 0.11, 0.02, (0, -0.44, 5.92), K["crimson"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.0)
    ringbar("RoseRim", (0, -0.45, 5.92), 0.12, "Y", K["limel"], thick=0.02, n=12, seg=4)
    bar("Perch", [(0, -0.43, 5.2), (0, -0.65, 5.2)], 0.02, K["brassf"], seg=4)
    box("Tower", (0.36, 0.36, 0.6), (0, -0.25, za + 0.15), K["limel"], bevel=0.02, segments=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cone(f"Pinnacle{sx}{sy}", 0.05, 0.0, 0.25, (sx * 0.16, -0.25 + sy * 0.16, za + 0.57), K["limel"], verts=4)
    cone("Spire", 0.2, 0.01, 0.95, (0, -0.25, za + 0.92), K["slate"], verts=8)
    cone("SpireTip", 0.02, 0.0, 0.2, (0, -0.25, za + 1.5), K["brassf"], verts=4)
    return _dims()

def scarecrow(M):
    """A scarecrow in a school blazer, 7.6 tall and unsettling: too tall and too thin, its sack head lolling to one side with
    a stitched grin and mismatched button eyes, a tattered blazer with the crest hanging from the crossbar, straw bursting
    from the cuffs and collar, a crow perched on each arm."""
    K = gk2(M)
    rng = RNG(64)
    burlap = B24.cloth("ScarecrowSack", (0.32, 0.25, 0.15), rough=0.95, weave=0.025)
    blazer = B24.cloth("Blazer", (0.02, 0.018, 0.024), rough=0.85, weave=0.006)
    shirt = B24.cloth("Shirt", (0.52, 0.5, 0.44), rough=0.85, weave=0.005)
    from nh_props_batch20 import tprism
    box("Post", (0.2, 0.2, 7.0), (0, 0.15, 3.5), K["deadwood"], bevel=0.03, segments=2)
    box("Cross", (5.2, 0.16, 0.16), (0, 0.15, 5.4), K["deadwood"], bevel=0.03, segments=2)
    lathe("Body", [(0, 3.0), (0.5, 3.0), (0.55, 3.6), (0.56, 4.4), (0.66, 5.2), (0.45, 5.55), (0.16, 5.65), (0, 5.65)], blazer, seg=14, scale=(1.0, 0.55),
          jitter=(0.05, 3))
    for k in range(7):         # the blazer's ragged hem
        x = -0.45 + k * 0.15
        tprism(f"Rag{k}", [(x, 3.05), (x + 0.13, 3.05), (x + 0.06, 3.05 - rng.uniform(0.2, 0.45))], -0.27, 0.03, blazer)
    for sx in (-1, 1):
        tprism(f"Lapel{sx}", [(0, 5.55), (sx * 0.34, 5.55), (sx * 0.2, 4.95), (sx * 0.03, 4.5)], -0.33, 0.03, blazer)
    tprism("ShirtV", [(-0.25, 5.58), (0.25, 5.58), (0, 4.7)], -0.31, 0.02, shirt)
    tprism("Tie", [(-0.05, 5.5), (0.05, 5.5), (0.08, 4.8), (0, 4.62), (-0.08, 4.8)], -0.34, 0.02, K["crimson"])
    tprism("Crest", [(-0.12, 5.15), (0.12, 5.15), (0.12, 4.98), (0, 4.85), (-0.12, 4.98)], -0.33, 0.02, K["crimson"])
    P.PARTS[-1].matrix_world = T(-0.32, 0.0, 0)
    for sx in (-1, 1):
        pts = [(sx * 0.45, 0.12, 5.35), (sx * 1.3, 0.12, 5.42), (sx * 2.3, 0.12, 5.3)]
        bar(f"Sleeve{sx}", pts, lambda t: 0.22 - t * 0.06, blazer, seg=10)
        for k in range(4):
            tprism(f"Tatter{sx}{k}", [(sx * (2.0 + k * 0.08), 5.18), (sx * (2.08 + k * 0.08), 5.18), (sx * (2.04 + k * 0.08), 5.18 - rng.uniform(0.2, 0.5))],
                   0.0, 0.02, blazer)
    # the head: a sack stuffed and tied, lolling to the left
    s = _mark()
    blob("Head", (0, 0, 0.55), 0.55, burlap, seg=14, rings=9, scale=(0.95, 0.9, 1.1), jitter=0.06, seed=2)
    ringbar("Twine", (0, 0, 0.05), 0.24, "Z", flat("Twine", (0.35, 0.29, 0.18), 0.9), thick=0.03, n=12, seg=4)
    cyl("EyeL", 0.11, 0.04, (-0.2, -0.48, 0.66), K["ink"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.01)
    cyl("EyeR", 0.075, 0.04, (0.21, -0.48, 0.6), flat("BoneButton", (0.5, 0.47, 0.4), 0.4), rot=(math.pi / 2, 0, 0), verts=10, bevel=0.01)
    smile = [(math.sin(t) * 0.32, -0.49 - 0.03 * math.cos(t) ** 2, 0.36 - 0.1 * math.cos(t) + 0.04 * t) for t in [-1.3 + i / 10 * 2.6 for i in range(11)]]
    bar("Smile", smile, 0.016, K["ink"], seg=4)
    for k in range(9):
        x, y, z = smile[k + 1]
        box(f"Stitch{k}", (0.012, 0.012, 0.13), (x, y - 0.01, z), flat("Thread", (0.55, 0.5, 0.42), 0.8), bevel=0.0)
    _xform(s, T(0, -0.02, 5.75) @ RY(0.42) @ RX(0.15))
    cards = Cards(rng)
    for sx in (-1, 1):
        for k in range(4):
            n = Vector((sx, rng.uniform(-0.5, 0.5), rng.uniform(-0.8, 0.1))).normalized()
            ax, ay = frame(n.cross(UP).normalized() if abs(n.z) < 0.9 else Vector((0, -1, 0)), up=n)
            cards.add((sx * 2.3, 0.12, 5.3), ax, n, 0.5, 0.75, "grass", "base", nrm=n)
    for k in range(7):
        a = k / 7 * 6.28
        n = Vector((math.cos(a), math.sin(a), -0.3)).normalized()
        ax, ay = frame(n.cross(UP).normalized(), up=n)
        cards.add((math.cos(a) * 0.25, math.sin(a) * 0.2, 5.62), ax, n, 0.4, 0.55, "grass", "base", nrm=n)
        n2 = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, -1)).normalized()
        ax2, _ = frame(n2.cross(UP).normalized() if abs(n2.z) < 0.99 else Vector((1, 0, 0)), up=n2)
        cards.add((math.cos(a) * 0.45, math.sin(a) * 0.25, 3.0), Vector((-math.sin(a), math.cos(a), 0)), n2, 0.5, 0.75, "grass", "base", nrm=n2)
    cards.build("Leaves")
    crow("CrowL", K, T(-1.7, 0.15, 5.62) @ RZ(-0.4), rng, pose=0)
    crow("CrowR", K, T(1.95, 0.15, 5.6) @ RZ(math.pi + 0.5), rng, pose=1)
    P.ATLAS["Scarecrow_Leaves"] = "NH_GardenLeaves"
    return _dims()

def bench_table(M):
    """A courtyard table for students: an oak-slatted table (top 2.6, 6 x 2.6) on cast-iron A-frames with two attached oak
    benches (seat tops 1.6) either side, the frames joined by an iron stretcher."""
    K = gk2(M)
    for sx in (-1, 1):
        x = sx * 2.4
        bar(f"A{sx}a", [(x, -1.85, 0), (x, 0, 2.5)], 0.07, K["iron"], seg=5)
        bar(f"A{sx}b", [(x, 1.85, 0), (x, 0, 2.5)], 0.07, K["iron"], seg=5)
        bar(f"Cross{sx}", [(x, -2.25, 1.45), (x, 2.25, 1.45)], 0.06, K["iron"], seg=5)
        bar(f"Top{sx}", [(x, -1.25, 2.47), (x, 1.25, 2.47)], 0.06, K["iron"], seg=5)
        ringbar(f"Foil{sx}", (x, 0, 1.95), 0.28, "X", K["iron"], thick=0.035, n=12, seg=4)
        for sy in (-1, 1):
            sphere(f"Toe{sx}{sy}", 0.09, (x, sy * 1.85, 0.06), K["iron"], seg=6, rings=4)
    bar("Stretcher", [(-2.4, 0, 1.0), (2.4, 0, 1.0)], 0.05, K["iron"], seg=5)
    for k in range(6):
        box(f"Top{k}", (6.0, 0.4, 0.12), (0, -1.05 + k * 0.42, 2.6), K["oak"], bevel=0.03, segments=1)
    for sy in (-1, 1):
        for k in range(3):
            box(f"Seat{sy}{k}", (6.0, 0.34, 0.11), (sy * 0 + 0, sy * (1.65 + k * 0.36 - 0.36), 1.58), K["oak"], bevel=0.03, segments=1)
    return _dims()


def crow(prefix, K, mtx, rng, pose=0):
    s = _mark()
    feather = flat("Crow", (0.012, 0.012, 0.016), 0.35, wear=0.05, dirt=0.3)
    sphere(f"{prefix}Body", 0.32, (0, 0, 0.4), feather, seg=10, rings=6, scale=(1.5, 0.85, 0.9))
    sphere(f"{prefix}Head", 0.18, (0.45, 0, 0.72 if pose == 0 else 0.6), feather, seg=8, rings=6)
    cone(f"{prefix}Beak", 0.06, 0.0, 0.28, (0.7, 0, 0.7 if pose == 0 else 0.58), flat("Beak", (0.03, 0.03, 0.03), 0.3), verts=6, rot=(0, math.pi / 2 + (0.1 if pose == 0 else 0.4), 0))
    for sy in (-1, 1):
        sphere(f"{prefix}Eye{sy}", 0.03, (0.56, sy * 0.12, 0.76 if pose == 0 else 0.64), flat("CrowEye", (0.25, 0.2, 0.05), 0.15), seg=6, rings=3)
        poly_slab(f"{prefix}Wing{sy}", [(0.3, 0), (-0.55, 0.02), (-0.75, -0.05), (0.1, -0.2)], -0.012, 0.012, feather)
        P.PARTS[-1].matrix_world = T(0, sy * 0.25, 0.48) @ RX(sy * 1.35)
    poly_slab(f"{prefix}Tail", [(0, -0.12), (0, 0.12), (-0.55, 0.18), (-0.55, -0.18)], -0.015, 0.015, feather)
    P.PARTS[-1].matrix_world = T(-0.4, 0, 0.35) @ RY(-0.35)
    for sy in (-1, 1):
        bar(f"{prefix}Leg{sy}", [(0.05, sy * 0.1, 0.2), (0.08, sy * 0.1, 0.0)], 0.02, flat("CrowLeg", (0.05, 0.05, 0.05), 0.5), seg=4)
    _xform(s, mtx)


def crow_perch(M):
    """A dead-branch perch 6.5 tall: a silvered dead snag on a mossy stump, two crooked limbs, two crows (one cawing down at
    the path, -Y), thorny twigs."""
    K = gk2(M)
    rng = RNG(65)
    lathe("Stump", [(0, 0), (0.9, 0), (0.85, 0.3), (0.65, 0.7), (0.55, 1.2), (0, 1.2)], K["deadwood"], seg=12, jitter=(0.08, 2))
    mound("Moss", 1.3, 1.2, 0.15, K["moss"], rng, seg=12)
    trunk("Snag", (0, 0, 1.0), (0.3, 0.2, 5.8), 0.48, 0.12, K["deadwood"], seg=9, wobble=0.25, rng=rng)
    l1 = bez((0.1, 0.05, 3.2), (1.0, -0.2, 3.8), (2.3, -0.4, 4.0), 7)
    l2 = bez((0.2, 0.1, 4.4), (-0.8, 0.3, 5.0), (-1.8, 0.2, 5.6), 7)
    bar("Limb1", l1, lambda t: 0.2 * (1 - t * 0.6), K["deadwood"], seg=7)
    bar("Limb2", l2, lambda t: 0.16 * (1 - t * 0.6), K["deadwood"], seg=7)
    for k, (st, d) in enumerate(((l1[4], (0.4, -0.3, 0.9)), (l2[3], (-0.3, 0.4, 0.8)), ((0.25, 0.15, 5.0), (0.5, 0.2, 0.9)))):
        en = Vector(st) + Vector(d)
        bar(f"Twig{k}", [st, tuple((Vector(st) + en) / 2 + Vector((0.1, 0, 0.1))), tuple(en)], lambda t: 0.06 * (1 - t * 0.8), K["deadwood"], seg=5)
    crow("CrowA", K, T(*Vector(l1[5])) @ T(0, 0, 0.12) @ RZ(-1.9) @ T(0, 0, -0.1), rng, pose=1)
    crow("CrowB", K, T(*Vector(l2[5])) @ T(0, 0, 0.1) @ RZ(0.4) @ T(0, 0, -0.1), rng, pose=0)
    cards = Cards(rng)
    for p, n in (((0.3, 0.2, 5.7), (0.2, 0.1, 1)), ((2.2, -0.4, 4.0), (1, -0.2, 0.5)), ((-1.7, 0.2, 5.5), (-1, 0.1, 0.6))):
        n = Vector(n).normalized()
        ax, ay = frame(n.cross(UP).normalized() if abs(n.z) < 0.95 else Vector((0, -1, 0)), up=n)
        cards.add(p, ax, n, 1.3, 1.5, "twigs", "base", nrm=n)
    cards.build("Leaves")
    P.ATLAS["CrowPerch_Leaves"] = "NH_GardenLeaves"
    return _dims()



# ================================================================== v2: the haunted academy garden (materials)

def lichen(m, scale=3.0, amount=0.25, cols=((0.55, 0.56, 0.44), (0.5, 0.4, 0.17))):
    """Lichen rosettes: round pale grey-green and ochre spots with darker rims, scattered (object space)."""
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = scale
    vo.inputs["Randomness"].default_value = 1.0
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vo.outputs["Color"], sep.inputs["Color"])
    sel = _math(nt, "GREATER_THAN", sep.outputs[0], 1.0 - amount)
    spot = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 0.36, vo.outputs["Distance"]), 9.0, clamp=True)
    mask = _math(nt, "MULTIPLY", spot, sel, clamp=True)
    col = _mix_rgb(nt, _math(nt, "GREATER_THAN", sep.outputs[1], 0.55), cols[0], cols[1])
    _paint(m, mask, col, rough=0.85)
    return m


def streaks(m, amount=0.45, dark=(0.3, 0.29, 0.28)):
    """Rain streaks: long vertical stains running down (a noise stretched in Z multiplied into the colour)."""
    nt = m.node_tree
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (3.0, 3.0, 0.25)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 5.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mask = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz.outputs["Fac"], 0.52), 5.0 * amount, clamp=True)
    src, dst = B24._colour_in(m)
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    nt.links.new(mask, mx.inputs["Factor"]); nt.links.new(src, mx.inputs[6]); mx.inputs[7].default_value = (*dark, 1)
    nt.links.new(mx.outputs[2], dst)
    return m


def forged(m, rust=0.35):
    """Hand-forged iron: hammer-mark facets in the bump, rust blooming in patches (and in the crevices the bake darkens)."""
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 22.0
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    nm = next((n for n in nt.nodes if n.type == "NORMAL_MAP"), None)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(vo.outputs["Distance"], bump.inputs["Height"])
    bev = [n for n in nt.nodes if n.type == "BEVEL"]
    last = max(bev, key=lambda n: len(n.outputs["Normal"].links)) if bev else None
    if nm is not None:
        nt.links.new(nm.outputs["Normal"], bump.inputs["Normal"])
    for b in bev:
        if b.inputs["Normal"].is_linked and nm is not None and b.inputs["Normal"].links[0].from_node == nm:
            nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nz = _noise(m, 3.5)
    mask = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", nz, 0.62 - rust * 0.2), 6.0, clamp=True)
    _paint(m, mask, (0.2, 0.075, 0.03), rough=0.9, metal=0.15)
    return m


def topiary(name="Topiary", g=(0.022, 0.048, 0.02)):
    """Clipped yew and box: a dense skin of tiny leaves, each a slightly different green, domed in the bump, darker in the
    hollows between them."""
    m = flat(name, g, 0.78, dirt=0.7)
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = 26.0
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vo.outputs["Color"], sep.inputs["Color"])
    _paint(m, _math(nt, "MULTIPLY", sep.outputs[0], 0.8), tuple(c * 2.3 for c in g), rough=0.7)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", sep.outputs[1], 0.75), 3.0, clamp=True), (0.07, 0.1, 0.03), rough=0.7)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", vo.outputs["Distance"], 0.45), 2.5, clamp=True), tuple(c * 0.35 for c in g), rough=0.9)
    B24._bump(m, _math(nt, "SUBTRACT", 1.0, vo.outputs["Distance"]), 0.04, 0.9)
    return m


def gk2(M):
    """The haunted garden's materials: limestone with lichen and rain streaks, forged iron with rust bloom, cleft slate,
    sooty brick, moss only on tops and in crevices."""
    K = gk(M)
    K["lime"] = streaks(lichen(mossy(material("GardenLime2", "NH_Limestone", tint=(0.66, 0.64, 0.58), scale=0.3, wear=0.45, dirt=1.1, rough_add=0.05),
                                     0.5, low=0.5), 2.6, 0.22), 0.4)
    K["limel"] = streaks(lichen(mossy(material("GardenLimeLight2", "NH_Limestone", tint=(0.76, 0.74, 0.68), scale=0.3, wear=0.4, dirt=0.95), 0.2),
                                3.0, 0.15), 0.3)
    soft = ((0.42, 0.43, 0.36), (0.36, 0.31, 0.18))
    K["flag"] = streaks(lichen(mossy(material("Flagstone", "NH_Limestone", tint=(0.54, 0.52, 0.48), scale=0.35, wear=0.55, dirt=1.15, rough_add=0.06),
                                     0.35, scale=1.8), 3.4, 0.1, cols=soft), 0.25)
    K["flagdark"] = lichen(mossy(material("FlagstoneDark", "NH_Limestone", tint=(0.4, 0.39, 0.36), scale=0.35, wear=0.5, dirt=1.15, rough_add=0.06),
                                 0.4, scale=1.8), 3.4, 0.08, cols=soft)
    K["slatec"] = lichen(material("CleftSlate", "NH_Slate", tint=(0.2, 0.22, 0.25), scale=0.45, rough_mul=0.6, rough_add=0.3, normal=0.9, wear=0.35,
                                  dirt=1.0), 2.5, 0.15)
    K["sand"] = lichen(mossy(material("Sandstone", "NH_Limestone", tint=(0.5, 0.3, 0.2), scale=0.35, wear=0.45, dirt=1.0), 0.3), 2.4, 0.2)
    K["iron"] = forged(material("ForgedIron", "NH_Iron", tint=(0.1, 0.095, 0.105), scale=0.45, rough_add=0.06, wear=0.55, wear_metal=True))
    K["wall"] = streaks(K["wall"], 0.5)
    K["moss2"] = mossy(flat("MossBed", (0.035, 0.055, 0.02), 0.9, dirt=0.5), 0.9, scale=3.0, col=(0.06, 0.1, 0.03))
    B24._bump(K["moss2"], _noise(K["moss2"], 40.0), 0.04, 0.8)
    K["root"] = material("Root", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.7, 0.6, 0.55), scale=1.2, metal=0.0, normal=1.0, wear=0.3, dirt=1.0)
    K["petal"] = flat("RosePetal", (0.13, 0.004, 0.011), 0.72, dirt=1.0)      # #8C0F1E, darker into the crevices at the petal bases
    K["petalblack"] = flat("BlackPetal", (0.011, 0.004, 0.007), 0.8, dirt=0.3)
    K["petalheart"] = flat("PetalHeart", (0.3, 0.0, 0.025), 0.6, dirt=0.5)
    K["stem"] = mossy(flat("RoseStem", (0.05, 0.06, 0.03), 0.7, dirt=0.6), 0.1)
    K["thorn"] = flat("Thorn", (0.16, 0.1, 0.07), 0.5, dirt=0.4)
    K["core"] = topiary()
    K["coredark"] = topiary("TopiaryDark", (0.014, 0.034, 0.024))
    return K


# ================================================================== v2: 2D helpers (stones laid by hand)

def _clip_half(poly, a, b):
    """Keep the part of a convex polygon closer to point a than to point b."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    nx, ny = b[0] - a[0], b[1] - a[1]
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = (p[0] - mx) * nx + (p[1] - my) * ny
        dq = (q[0] - mx) * nx + (q[1] - my) * ny
        if dp <= 0:
            out.append(p)
        if (dp < 0) != (dq < 0) and abs(dp - dq) > 1e-12:
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _sh_clip(subject, clip):
    """Sutherland-Hodgman: a (possibly concave) subject polygon clipped by a convex counter-clockwise clip polygon."""
    out = list(subject)
    n = len(clip)
    for i in range(n):
        if not out:
            break
        a, b = clip[i], clip[(i + 1) % n]
        inp, out = out, []

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

        def cross(p, q):
            x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
            x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(den) < 1e-12:
                return q
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q):
                if not inside(p):
                    out.append(cross(p, q))
                out.append(q)
            elif inside(p):
                out.append(cross(p, q))
    return out


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def _centroid(poly):
    a = _area(poly)
    if abs(a) < 1e-9:
        return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    cx = cy = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        f = x0 * y1 - x1 * y0
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    return (cx / (6 * a), cy / (6 * a))


def _inset(poly, d):
    """Shrink a polygon toward its centroid by about d (a hand-cut joint)."""
    c = _centroid(poly)
    out = []
    for x, y in poly:
        dx, dy = x - c[0], y - c[1]
        L = math.hypot(dx, dy)
        k = max(0.0, (L - d) / L) if L > 1e-9 else 0.0
        out.append((c[0] + dx * k, c[1] + dy * k))
    return out


def _clean(poly, eps=0.03):
    out = []
    for p in poly:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def _roughen(poly, rng, amt=0.05, step=0.45, chip=0.35):
    """Hand-cut edges: subdivide the sides and nudge the new points in and out, and knock a corner off now and then."""
    out = []
    c = _centroid(poly)
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if rng.random() < chip and L > 0.5:       # a broken corner
            t = rng.uniform(0.08, 0.16)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        else:
            out.append(p)
        k = int(L / step)
        for j in range(1, k + 1):
            t = j / (k + 1)
            x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
            dx, dy = x - c[0], y - c[1]
            dl = math.hypot(dx, dy) or 1.0
            o = rng.uniform(-amt, amt * 0.6)
            out.append((x + dx / dl * o, y + dy / dl * o))
    return _clean(out)


def poisson(rng, region_bbox, r, inside, k=30, extra=None):
    x0, y0, x1, y1 = region_bbox
    pts = list(extra or [])
    tries = 0
    while tries < 4000:
        tries += 1
        p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
        if not inside(p):
            continue
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > r * r for q in pts):
            pts.append(p)
            tries = 0
            if len(pts) > 400:
                break
        if tries > k * 40:
            break
    return pts


def voronoi_stones(region, seeds, rng, gap=0.09, rough=0.05, chip=0.3, minarea=0.12):
    """Hand-laid stones: each seed's Voronoi cell, clipped to the region (a counter-clockwise outline), shrunk for the joint,
    its edges roughened. Returns (outline, seed) pairs."""
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    box_ = [(min(xs) - 3, min(ys) - 3), (max(xs) + 3, min(ys) - 3), (max(xs) + 3, max(ys) + 3), (min(xs) - 3, max(ys) + 3)]
    out = []
    for i, s in enumerate(seeds):
        cell = list(box_)
        for j, t in enumerate(seeds):
            if i != j and (s[0] - t[0]) ** 2 + (s[1] - t[1]) ** 2 < 36:
                cell = _clip_half(cell, s, t)
                if not cell:
                    break
        if len(cell) < 3:
            continue
        if _area(cell) < 0:
            cell = cell[::-1]
        piece = _clean(_sh_clip(region, cell))
        if len(piece) < 3 or abs(_area(piece)) < minarea:
            continue
        if _area(piece) < 0:
            piece = piece[::-1]
        piece = _roughen(_inset(piece, gap), rng, rough, chip=chip)
        if len(piece) >= 3 and abs(_area(piece)) > minarea * 0.6:
            out.append((piece, s))
    return out


def wobble_line(p0, p1, rng, amt, step=0.6, keep_ends=True, side=None):
    """Points from p0 to p1 with an irregular sideways wobble (an edge that bleeds into the grass)."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = max(1, int(L / step))
    nx, ny = -(p1[1] - p0[1]) / L, (p1[0] - p0[0]) / L
    out = []
    ph = rng.uniform(0, 6.28)
    for i in range(n + 1):
        t = i / n
        o = 0.0 if (keep_ends and i in (0, n)) else (math.sin(t * 7 + ph) * 0.5 + rng.uniform(-1, 1)) * amt
        out.append((p0[0] + (p1[0] - p0[0]) * t + nx * o, p0[1] + (p1[1] - p0[1]) * t + ny * o))
    return out


def stone_slab(name, outline, z0, z1, mat, tilt=(0.0, 0.0), bevel=0.05, dish=0.0):
    """A hand-cut stone from its outline: sides from z0, its top at z1 (tilted a little; dish > 0 wears a hollow into the
    middle of the top, like a step trodden for centuries)."""
    c = _centroid(outline)
    n = len(outline)

    def zt(x, y):
        return z1 + (x - c[0]) * tilt[0] + (y - c[1]) * tilt[1]
    V = [(x, y, z0) for x, y in outline] + [(x, y, zt(x, y)) for x, y in outline]
    F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    if dish > 0:
        ring = [(c[0] + (x - c[0]) * 0.6, c[1] + (y - c[1]) * 0.6) for x, y in outline]
        V += [(x, y, zt(x, y) - dish * 0.7) for x, y in ring]
        V.append((c[0], c[1], zt(*c) - dish))
        ci = len(V) - 1
        for i in range(n):
            j = (i + 1) % n
            F.append((n + i, n + j, 2 * n + j, 2 * n + i))
            F.append((2 * n + i, 2 * n + j, ci))
    else:
        F.append(tuple(range(n, 2 * n)))
    ob = mk(name, V, F, mat, smooth=False, bevel=0.0, tri=True)
    P_recalc(ob)
    if bevel > 0:
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(30)
        md.harden_normals = True
    return ob


def _add_bump(m, height, distance=0.02, strength=0.6):
    """Feed a height into a P.material's normal chain (set or flat), on top of what is there."""
    nt = m.node_tree
    bev = [n for n in nt.nodes if n.type == "BEVEL" and n.inputs["Normal"].is_linked]
    if not bev:
        return m
    b = bev[0]
    src = b.inputs["Normal"].links[0].from_socket
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    nt.links.new(src, bump.inputs["Normal"])
    nt.links.new(height, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def carved(name, c, size, glyph, rot=0.0, tint=(0.6, 0.58, 0.53)):
    """A flagstone with a worn carving (one of garden_atlas.py's rune images, NH_GardenRune<k>), centred at c (x, y), `size`
    across, turned by rot: the cut is darker, rougher and sunk into the bump."""
    m = lichen(mossy(material(name, "NH_Limestone", tint=tint, scale=0.35, wear=0.55, dirt=1.15, rough_add=0.06), 0.3, scale=1.8), 2.2, 0.2)
    nt = m.node_tree
    mp = nt.nodes.new("ShaderNodeMapping")
    s = 1.0 / size
    R = Matrix.Rotation(-rot, 3, "Z")
    cv = R @ Vector((c[0] * s, c[1] * s, 0))
    mp.inputs["Scale"].default_value = (s, s, s)
    mp.inputs["Rotation"].default_value = (0, 0, -rot)
    mp.inputs["Location"].default_value = (0.5 - cv.x, 0.5 - cv.y, 0)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(P.OUT_TEX, f"NH_GardenRune{glyph}.png"), check_existing=True)
    t.extension = "CLIP"
    nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
    mask = _math(nt, "MULTIPLY", t.outputs["Alpha"], 0.85)
    _paint(m, mask, (0.1, 0.095, 0.085), rough=0.92)
    _add_bump(m, _math(nt, "MULTIPLY", t.outputs["Alpha"], -1.0), 0.02, 0.9)
    return m


def inside_poly(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def dist_to_outline(p, poly):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t))
    return best


def flag_region(shape, rng, amt=0.32):
    """The outline of a flagstone path cell (counter-clockwise): the open ends straight on the cell edges (they meet the next
    piece), the sides wobbling in and out where the stones meet the grass."""
    h = HALF + 0.2

    def W(a, b):
        return wobble_line(a, b, rng, amt)
    if shape == "straight":
        pts = W((h, -5), (h, 5)) + W((-h, 5), (-h, -5))
    elif shape == "curve":
        c = (5, -5)
        n = 18
        outer = []
        for i in range(n + 1):
            a = math.pi - (math.pi / 2) * i / n
            r = 5 + h + (0 if i in (0, n) else (math.sin(i * 1.7) * 0.5 + rng.uniform(-1, 1)) * amt)
            outer.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        inner = []
        for i in range(9):
            a = math.pi / 2 + (math.pi / 2) * i / 8
            r = 5 - h + (0 if i in (0, 8) else rng.uniform(-1, 1) * amt * 0.5)
            inner.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        pts = outer + inner
    elif shape == "junction":
        pts = W((-5, -h), (-h, -h)) + W((-h, -h), (-h, -5)) + W((h, -5), (h, -h)) + W((h, -h), (5, -h)) + W((5, h), (-5, h))
    else:
        pts = (W((h, -5), (h, -h)) + W((h, -h), (5, -h)) + W((5, h), (h, h)) + W((h, h), (h, 5)) + W((-h, 5), (-h, h)) + W((-h, h), (-5, h))
               + W((-5, -h), (-h, -h)) + W((-h, -h), (-h, -5)))
    pts = _clean(pts)
    return pts if _area(pts) > 0 else pts[::-1]


def lay_flags(K, region, rng, r=1.75, mats=None, z1=0.3, crack=True, rune=True, drop=0.12, prefix="Flag", root=True, avoid=None):
    """Lay hand-cut flagstones over a region: a moss bed, the stones (one cracked with a root pushing up through it, one with a
    worn carving), a few missing at the grass edge. Returns the stones' outlines."""
    mats = mats or [K["flag"], K["flag"], K["flagdark"]]
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    seeds = poisson(rng, (min(xs), min(ys), max(xs), max(ys)), r, lambda p: inside_poly(p, region))
    stones = voronoi_stones(region, seeds, rng, gap=0.09, rough=0.05, chip=0.3)
    if avoid:
        stones = [s for s in stones if not avoid(_centroid(s[0]))]
    # the moss bed under them, a little proud of the stones at the grass edge
    bed = _inset(region, -0.12) if len(region) < 200 else region
    poly_slab(f"{prefix}Bed", bed, 0.0, z1 - 0.13, K["moss2"])
    edge = [s for s in stones if dist_to_outline(_centroid(s[0]), region) < 0.9]
    gone = set(id(s) for s in edge if rng.random() < drop)
    inner = [s for s in stones if id(s) not in gone and s not in edge]
    big = max(inner, key=lambda s: abs(_area(s[0]))) if (crack and inner) else None
    carve = None
    if rune and inner:
        cands = [s for s in inner if s is not big]
        if cands:
            carve = max(cands, key=lambda s: abs(_area(s[0])) * rng.uniform(0.6, 1.0))
    out = []
    for k, (poly, seed) in enumerate(stones):
        if id((poly, seed)) in gone or (poly, seed) in [stones[i] for i in []]:
            pass
        if any(poly is g[0] for g in edge if id(g) in gone):
            continue
        zt = z1 + rng.uniform(-0.03, 0.025)
        tilt = (rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012))
        mat = mats[rng.integers(len(mats))]
        if big is not None and poly is big[0]:
            c = _centroid(poly)
            a = rng.uniform(0, math.pi)
            d = (math.cos(a), math.sin(a))
            nrm = (-d[1], d[0])
            far = 20
            half1 = [(c[0] - d[0] * far, c[1] - d[1] * far), (c[0] + d[0] * far, c[1] + d[1] * far),
                     (c[0] + d[0] * far + nrm[0] * far, c[1] + d[1] * far + nrm[1] * far), (c[0] - d[0] * far + nrm[0] * far, c[1] - d[1] * far + nrm[1] * far)]
            half2 = [(c[0] - d[0] * far, c[1] - d[1] * far), (c[0] - d[0] * far - nrm[0] * far, c[1] - d[1] * far - nrm[1] * far),
                     (c[0] + d[0] * far - nrm[0] * far, c[1] + d[1] * far - nrm[1] * far), (c[0] + d[0] * far, c[1] + d[1] * far)]
            for j, hp in enumerate((half1, half2)):
                part = _clean(_sh_clip(poly, hp if _area(hp) > 0 else hp[::-1]))
                if len(part) >= 3:
                    part = _inset(part if _area(part) > 0 else part[::-1], 0.07)
                    stone_slab(f"{prefix}{k}c{j}", part, 0.06, zt + (0.03 if j == 0 else -0.01), mat, tilt=(tilt[0] * (2 if j else -2), tilt[1] * 2), bevel=0.05)
            if root:
                L = math.sqrt(abs(_area(poly))) * 0.75
                p0 = (c[0] - d[0] * L * 1.6, c[1] - d[1] * L * 1.6, 0.12)
                p1 = (c[0] - d[0] * L * 0.4, c[1] - d[1] * L * 0.4, zt + 0.14)
                p2 = (c[0] + d[0] * L * 0.5, c[1] + d[1] * L * 0.5, zt + 0.2)
                p3 = (c[0] + d[0] * L * 1.3, c[1] + d[1] * L * 1.3, 0.14)
                pts = bez(p0, p1, p2, 6)[:-1] + bez(p2, (p2[0] + d[0] * L * 0.5, p2[1] + d[1] * L * 0.5, zt + 0.12), p3, 5)
                bar(f"{prefix}Root", pts, lambda t: 0.12 * (1 - abs(t - 0.45) * 0.9), K["root"], seg=7)
                for j in range(2):
                    q = pts[3 + j * 3]
                    e = (q[0] + nrm[0] * (0.5 + j * 0.2) * (1 if j else -1), q[1] + nrm[1] * (0.5 + j * 0.2) * (1 if j else -1), zt - 0.02)
                    bar(f"{prefix}Rootlet{j}", [q, ((q[0] + e[0]) / 2, (q[1] + e[1]) / 2, q[2] + 0.04), e], lambda t: 0.05 * (1 - t * 0.8), K["root"], seg=5)
            out.append(poly)
            continue
        if carve is not None and poly is carve[0]:
            c = _centroid(poly)
            size = math.sqrt(abs(_area(poly))) * 0.75
            mat = carved(f"{prefix}Carved{k}", c, size, int(rng.integers(4)), rot=rng.uniform(-0.4, 0.4))
            tilt = (0.0, 0.0)
        stone_slab(f"{prefix}{k}", poly, 0.06, zt, mat, tilt=tilt, bevel=0.05)
        out.append(poly)
    return out, [s[0] for s in edge if id(s) in gone]


def path_flags(M, shape, name, kind="flag"):
    """A 10-stud cell of hand-cut flagstones (kind "crazy": broken slate, limestone and sandstone, smaller)."""
    K = gk2(M)
    rng = RNG(zlib.crc32((name + shape).encode()) & 0xFFFF)
    region = flag_region(shape, rng, amt=0.34 if kind == "flag" else 0.28)
    if _area(region) < 0:
        region = region[::-1]
    if kind == "crazy":
        mats = [K["slatec"], K["slatec"], K["flag"], K["sand"], K["flagdark"]]
        stones, gaps = lay_flags(K, region, rng, r=1.15, mats=mats, crack=True, rune=False, drop=0.1)
    else:
        stones, gaps = lay_flags(K, region, rng, r=1.8, crack=True, rune=True, drop=0.14, root=(shape in ("straight", "cross")))
    # grass in the gaps at the edge, and a stray chip or two out in the grass
    cards = Cards(rng)
    for poly in gaps:
        c = _centroid(poly)
        cards.crossed((c[0], c[1], 0.12), 0.9, 0.7, "grass", k=2)
    for k in range(3):
        a = rng.uniform(0, 6.28)
        p = region[rng.integers(len(region))]
        if abs(p[1]) < 4.4 and abs(p[0]) < 4.4 or shape == "curve":
            stone(f"Chip{k}", p[0] + math.cos(a) * 0.5, p[1] + math.sin(a) * 0.5, rng.uniform(0.18, 0.3), rng.uniform(0.14, 0.24), 0.0,
                  0.08, K["flagdark"], rng, n=7, bevel=0.03)
    if cards.V:
        cards.build("Leaves")
        P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"
    return _dims()


def puddle_flags(M):
    """PathFlagstone with a rain puddle: the stones in an oval hollow sunk and tipped inward, the water over them (Glass)."""
    K = gk2(M)
    rng = RNG(4242)
    region = flag_region("straight", rng, amt=0.34)
    pc, pr = (-0.3, 0.8), (1.8, 2.5)

    def inp(c):
        return ((c[0] - pc[0]) / pr[0]) ** 2 + ((c[1] - pc[1]) / pr[1]) ** 2 < 1.0
    stones, gaps = lay_flags(K, region, rng, r=1.6, crack=False, rune=True, drop=0.12, avoid=inp)
    # sunken stones in the hollow
    seeds = poisson(rng, (pc[0] - pr[0], pc[1] - pr[1], pc[0] + pr[0], pc[1] + pr[1]), 1.2, inp)
    hollow = blob_outline(pr[0] * 1.02, pr[1] * 1.02, 26, rng, 0.08, cx=pc[0], cy=pc[1])
    for k, (poly, s) in enumerate(voronoi_stones(hollow, seeds, rng, gap=0.08)):
        c = _centroid(poly)
        stone_slab(f"Sunk{k}", poly, 0.03, 0.2, K["flagdark"], tilt=((pc[0] - c[0]) * 0.02, (pc[1] - c[1]) * 0.02), bevel=0.04)
    set_group("Glass")
    poly_slab("Water", blob_outline(pr[0] * 0.9, pr[1] * 0.9, 26, rng, 0.1, cx=pc[0], cy=pc[1]), 0.22, 0.235, K["water"])
    set_group("Main")
    return _dims()


def moon_phase_outline(phase, r, n=14):
    """A moon at phase 0..7 (0 new, 2 first quarter, 4 full, 6 last quarter) as a 2D outline of its lit part (None for new)."""
    k = {1: 0.55, 2: 0.0, 3: -0.55, 4: -1.0, 5: -0.55, 6: 0.0, 7: 0.55}.get(phase)
    if k is None:
        return None
    side = 1 if phase <= 4 else -1
    pts = [(side * math.cos(t) * r, math.sin(t) * r) for t in [-math.pi / 2 + math.pi * i / n for i in range(n + 1)]]
    pts += [(side * k * math.cos(t) * r, math.sin(t) * r) for t in [math.pi / 2 - math.pi * i / n for i in range(1, n)]]
    if phase == 4:
        pts = [(math.cos(t) * r, math.sin(t) * r) for t in [i / (2 * n) * 2 * math.pi for i in range(2 * n)]]
    return pts if _area(pts) > 0 else pts[::-1]


def moon_roundel2(M):
    """A 20-wide round junction, the garden's showpiece: a carved compass of the moon's phases. At its heart the Inlay
    (a crescent cradling the school's shield, MoonRoundelInlay, radius 4.2) in a brass ring; round it a pale limestone field
    with a compass rose of slate rays (the four long ones to 7.4) and eight brass-ringed medallions of the moon's phases;
    a brass band; hand-cut flagstones out to a kerb ring at 10, broken by four threshold stones where the paths come in."""
    K = gk2(M)
    rng = RNG(77)
    zf = PT + 0.04
    set_group("Inlay")
    n = 72
    Ri = 4.2
    V = [(0, 0, zf + 0.02)] + [(math.cos(i / n * 2 * math.pi) * Ri, math.sin(i / n * 2 * math.pi) * Ri, zf + 0.02) for i in range(n)]
    ob = mk("Inlay", V, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)], K["lime"], smooth=False)
    uv = ob.data.uv_layers.new(name="Bake")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            x, y, _ = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv = (x / (2 * Ri) + 0.5, y / (2 * Ri) + 0.5)
    P.ATLAS["PathMoonRoundel_Inlay"] = "MoonRoundelInlay"
    set_group("Main")
    ring_slab("BrassHeart", (0, 0), Ri, Ri + 0.18, 0, 2 * math.pi, 0.06, zf + 0.05, K["brass"], n=72, ends=False)
    ring_slab("Field", (0, 0), Ri + 0.18, 7.45, 0, 2 * math.pi, 0.06, zf, K["limel"], n=72, ends=False)
    ring_slab("BrassBand", (0, 0), 7.45, 7.65, 0, 2 * math.pi, 0.06, zf + 0.05, K["brass"], n=72, ends=False)
    dark = K["slatec"]
    lightslate = material("SlateLight", "NH_Slate", tint=(0.36, 0.38, 0.4), scale=0.45, rough_mul=0.6, rough_add=0.3, normal=0.8, wear=0.35)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 2
        long = k % 2 == 0
        tip = 7.35 if long else 6.0
        w = 0.62 if long else 0.4
        r0 = Ri + 0.25
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa, ca
        mid = r0 + (tip - r0) * 0.18
        base = (ca * r0, sa * r0)
        tp = (ca * tip, sa * tip)
        for side, mat in ((1, dark), (-1, lightslate)):
            pts = [base, (ca * mid + nx * w * side, sa * mid + ny * w * side), tp]
            if _area(pts) < 0:
                pts = pts[::-1]
            poly_slab(f"Ray{k}{side}", pts, zf - 0.02, zf + (0.07 if long else 0.05), mat, bevel=0.0)
        if long:      # a brass line down the middle of each long ray
            bar(f"RayLine{k}", [(base[0], base[1], zf + 0.075), (tp[0], tp[1], zf + 0.075)], 0.03, K["brass"], seg=4)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 2 + math.pi / 8
        cx, cy = math.cos(a) * 6.2, math.sin(a) * 6.2
        s = _mark()
        cyl(f"MedalBase{k}", 0.78, 0.08, (0, 0, zf + 0.0), dark, verts=28, bevel=0.0)
        ring_slab(f"MedalRing{k}", (0, 0), 0.7, 0.82, 0, 2 * math.pi, zf - 0.02, zf + 0.08, K["brass"], n=28, ends=False)
        lit = moon_phase_outline(k, 0.58)
        if lit is None:
            ring_slab(f"NewMoon{k}", (0, 0), 0.5, 0.58, 0, 2 * math.pi, zf, zf + 0.07, K["limel"], n=24, ends=False)
        else:
            poly_slab(f"Moon{k}", lit, zf, zf + 0.07, K["limel"])
        _xform(s, T(cx, cy, 0) @ RZ(a - math.pi / 2))
    # brass ticks round the band (the compass's degrees)
    for k in range(32):
        if k % 4 == 0:
            continue
        a = k / 32 * 2 * math.pi
        box(f"Tick{k}", (0.08, 0.35, 0.03), (math.cos(a) * 7.2, math.sin(a) * 7.2, zf + 0.015), K["brass"], bevel=0.0, rot=(0, 0, a - math.pi / 2))
    # hand-cut flagstones in the outer ring (four sectors), the kerb ring and thresholds
    for q in range(4):
        a0, a1 = q * math.pi / 2 + 0.02, (q + 1) * math.pi / 2 - 0.02
        outer = [(math.cos(a0 + (a1 - a0) * i / 16) * 9.55, math.sin(a0 + (a1 - a0) * i / 16) * 9.55) for i in range(17)]
        inner = [(math.cos(a1 - (a1 - a0) * i / 12) * 7.75, math.sin(a1 - (a1 - a0) * i / 12) * 7.75) for i in range(13)]
        region = outer + inner
        if _area(region) < 0:
            region = region[::-1]
        lay_flags(K, region, rng, r=1.5, crack=(q == 1), rune=(q == 3), drop=0.0, prefix=f"Ring{q}_", root=(q == 1))
    for q in range(4):
        a_mid = q * math.pi / 2 + math.pi / 4
        span = math.pi / 2 - 2 * math.asin(3.45 / 9.8)
        nb = 5
        for b in range(nb):
            a0 = a_mid - span / 2 + span * b / nb
            ring_slab(f"Rim{q}{b}", (0, 0), 9.6, 10.0, a0 + 0.006, a0 + span / nb - 0.006, 0, ET, K["lime"], n=3, bevel=0.04)
    for k in range(4):
        s = _mark()
        box(f"Threshold{k}", (6.9, 1.15, 0.38), (0, 9.42, 0.19), K["lime"], bevel=0.06, segments=2)
        box(f"ThreshStrip{k}", (6.4, 0.1, 0.02), (0, 9.0, 0.385), K["brass"], bevel=0.0)
        poly_slab(f"ThreshArrow{k}", [(-0.3, 9.45), (0.3, 9.45), (0, 9.85)], 0.37, 0.4, K["brass"])
        _xform(s, RZ(k * math.pi / 2))
    return _dims()


# ------------------------------------------------------------------ v2 hedges: gothic topiary

def lancet_top(x0, x1, z_valley, z_peak, n_arch, n=8):
    """A top line of pointed (lancet) crowns from x0 to x1: valleys at z_valley, peaks at z_peak."""
    pts = []
    w = (x1 - x0) / n_arch
    hw = w / 2
    rise = z_peak - z_valley
    R = (hw * hw + rise * rise) / (2 * hw) * 1.02
    for a in range(n_arch):
        xa = x0 + a * w
        for i in range(n + 1):           # the left flank rises (convex) to the peak
            t = i / n
            x = xa + hw * t
            cxl = xa + R                 # centre of the left arc, beyond the peak
            dz = math.sqrt(max(0.0, R * R - (x - cxl) ** 2)) - math.sqrt(max(0.0, R * R - (xa - cxl) ** 2))
            dzmax = math.sqrt(max(0.0, R * R - (xa + hw - cxl) ** 2)) - math.sqrt(max(0.0, R * R - (xa - cxl) ** 2))
            pts.append((x, z_valley + rise * dz / dzmax))
        for i in range(1, n + 1):
            t = i / n
            x = xa + hw + hw * t
            mx = 2 * (xa + hw) - x
            cxl = xa + R
            dz = math.sqrt(max(0.0, R * R - (mx - cxl) ** 2)) - math.sqrt(max(0.0, R * R - (xa - cxl) ** 2))
            dzmax = math.sqrt(max(0.0, R * R - (xa + hw - cxl) ** 2)) - math.sqrt(max(0.0, R * R - (xa - cxl) ** 2))
            pts.append((x, z_valley + rise * dz / dzmax))
    return pts


def hedge_from_profile(name, K, prof, depth, bevel=0.3, mat=None, y=0.0):
    """A hedge core: a profile in XZ (counter-clockwise, from the bottom left) pushed `depth` along Y, rounded."""
    from nh_props_batch20 import tprism
    ob = tprism(name, prof, y, depth, mat or K["core"], plane="XZ")
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = bevel
    md.segments = 3
    md.limit_method = "ANGLE"
    return ob


def clip_cards(cards, core, density=3.2, size=1.05, sprite="hedge", tilt=0.3):
    """A light fuzz of leaf cards over a clipped core (the core carries the clipped surface; the cards soften its edges)."""
    cards.cover(core, min(density, 3.0) * 0.32, sprite, min(size, 0.75), offset=0.05, tilt=0.18, zmin=0.2, nscale=0.9)


def hedge_lancet(M):
    """A clipped yew hedge 8 long, 2.3 thick, its top cut into two lancet crowns like a chapel's arcade (valleys at 4.6, points at
    6.6). Snaps end to end (pivot at the base centre)."""
    K = gk2(M)
    rng = RNG(21)
    prof = [(-4, 0), (4, 0)] + list(reversed(lancet_top(-4, 4, 4.6, 6.6, 2)))
    core = hedge_from_profile("Core", K, prof, 2.3, bevel=0.12)
    cards = Cards(rng)
    clip_cards(cards, core)
    cards.build("Leaves")
    P.ATLAS["HedgeStraight_Leaves"] = "NH_GardenLeaves"
    return _dims()


def hedge_battlement(M):
    """A hedge clipped into battlements, 8 long, 2.3 thick: a wall of yew 5.0 tall with four merlons rising to 6.2, the
    embrasures between them. Snaps end to end."""
    K = gk2(M)
    rng = RNG(25)
    prof = [(-4, 0), (4, 0), (4, 6.2)]
    xs = [4 - i * 1.0 for i in range(9)]
    for i in range(8):
        xa, xb = xs[i], xs[i + 1]
        if i % 2 == 0:
            prof += [(xa, 6.2), (xb, 6.2)]
        else:
            prof += [(xa, 5.0), (xb, 5.0)]
    prof = _clean([(x, z) for x, z in prof])
    prof += [(-4, 0.0)] if prof[-1] != (-4, 0) else []
    prof = [p for i, p in enumerate(prof) if i == 0 or p != prof[i - 1]]
    core = hedge_from_profile("Core", K, prof[:-1] if prof[-1] == prof[0] else prof, 2.3, bevel=0.18)
    cards = Cards(rng)
    clip_cards(cards, core, size=0.95)
    cards.build("Leaves")
    P.ATLAS["HedgeBattlement_Leaves"] = "NH_GardenLeaves"
    return _dims()


def hedge_corner2(M):
    """A corner for the hedges: a square yew tower 3.0 across rising to 8.6 under a clipped pyramid spire, with an arm of hedge
    (5.0 tall) to the right (+X) and one to the back (+Y), ending at x = 4.0 and y = 4.0 to butt onto straights. Pivot at the
    tower's centre."""
    K = gk2(M)
    rng = RNG(22)
    c1 = box("ArmX", (2.6, 2.3, 5.0), (2.7, 0, 2.5), K["core"], bevel=0.25, segments=3)
    c2 = box("ArmY", (2.3, 2.6, 5.0), (0, 2.7, 2.5), K["core"], bevel=0.25, segments=3)
    tw = box("Tower", (3.0, 3.0, 6.6), (0, 0, 3.3), K["core"], bevel=0.25, segments=3)
    sp = cone("Spire", 2.0, 0.08, 2.2, (0, 0, 6.6 + 1.1), K["core"], verts=4, rot=(0, 0, math.pi / 4))
    ball = blob("Finial", (0, 0, 8.95), 0.32, K["core"], seg=8, rings=6)
    cards = Cards(rng)
    for ob in (c1, c2, tw, sp):
        clip_cards(cards, ob, size=1.0)
    cards.cover(ball, 12, "hedge", 0.5, offset=0.04)
    cards.build("Leaves")
    P.ATLAS["HedgeCorner_Leaves"] = "NH_GardenLeaves"
    return _dims()


def hedge_end2(M):
    """The end of a hedge run: a 2.6-square yew pier 5.6 tall with a clipped obelisk on top (to 9.4) and a ball at its tip.
    Its +Y face (y = 1.3) butts onto a straight."""
    K = gk2(M)
    rng = RNG(23)
    pier = box("Pier", (2.6, 2.6, 5.6), (0, 0, 2.8), K["core"], bevel=0.25, segments=3)
    plinth = box("Step", (2.0, 2.0, 0.5), (0, 0, 5.85), K["core"], bevel=0.15, segments=2)
    ob_ = cone("Obelisk", 1.0, 0.18, 3.1, (0, 0, 6.1 + 1.55), K["core"], verts=4, rot=(0, 0, math.pi / 4))
    ball = blob("Ball", (0, 0, 9.5), 0.36, K["core"], seg=8, rings=6)
    cards = Cards(rng)
    for ob in (pier, plinth, ob_):
        clip_cards(cards, ob, size=0.95)
    cards.cover(ball, 12, "hedge", 0.5, offset=0.04)
    cards.build("Leaves")
    P.ATLAS["HedgeEnd_Leaves"] = "NH_GardenLeaves"
    return _dims()


def hedge_arch2(M):
    """A walk-through hedge arch 8 wide (a straight's length), 2.3 thick: a pointed opening 4.4 wide and 7.6 high, the hedge's
    top following the arch up to a point at 10.2, clipped yew pinnacles at both ends (to 8.4). The path runs along Y."""
    K = gk2(M)
    rng = RNG(24)
    hw, zs, za = 2.2, 4.8, 7.6
    n = 12
    R = (za - zs) ** 2 / (2 * hw) + hw / 2
    am = math.acos((R - hw) / R)
    arch = [(-hw + (R - R * math.cos(am * i / n)), zs + R * math.sin(am * i / n)) for i in range(n + 1)]
    top = [(x * 1.0, z) for x, z in lancet_top(-4, 4, 6.4, 10.2, 1, n=10)]
    pts = [(-4, 0), (-hw, 0), (-hw, zs)] + arch[1:] + [(-x, z) for x, z in reversed(arch[1:-1])] + [(hw, zs), (hw, 0), (4, 0)] + list(reversed(top))
    core = hedge_from_profile("Core", K, _clean(pts), 2.3, bevel=0.22)
    cards = Cards(rng)
    clip_cards(cards, core, size=0.95)
    for sx in (-1, 1):
        pn = cone(f"Pinnacle{sx}", 0.55, 0.05, 1.9, (sx * 3.45, 0, 6.4 + 0.95), K["core"], verts=4, rot=(0, 0, math.pi / 4))
        clip_cards(cards, pn, size=0.7)
    cards.build("Leaves")
    P.ATLAS["HedgeArchway_Leaves"] = "NH_GardenLeaves"
    return _dims()


def ell(name, c, r, K, rot=(0, 0, 0), seg=14, rings=9):
    ob = sphere(name, 1.0, (0, 0, 0), K["core"], seg=seg, rings=rings, scale=r)
    ob.matrix_world = T(*c) @ RZ(rot[2]) @ RY(rot[1]) @ RX(rot[0])
    return ob


def hedge_wolf(M):
    """Estate topiary: a great wolf lying like a sphinx on a clipped plinth, 7.2 long and 5.6 tall: forelegs stretched out
    before it, head held up and alert on a thick ruffed neck, long muzzle, tall pointed ears, its bushy tail curled round its
    flank. It faces the front (-Y), so it watches the path."""
    K = gk2(M)
    rng = RNG(26)
    plinth = box("Plinth", (3.6, 7.2, 1.3), (0, 0.3, 0.65), K["core"], bevel=0.15, segments=3)
    zb = 1.3
    parts = [plinth,
             ell("Body", (0, 0.9, zb + 0.95), (1.05, 2.0, 0.95), K),
             ell("Haunch", (0.15, 2.3, zb + 1.0), (1.15, 1.0, 1.0), K),
             ell("Chest", (0, -0.55, zb + 1.25), (0.95, 0.95, 1.1), K),
             ell("Ruff", (0, -0.75, zb + 2.0), (0.92, 0.75, 0.8), K, rot=(0.35, 0, 0)),
             ell("Neck", (0, -0.95, zb + 2.55), (0.55, 0.6, 0.75), K, rot=(0.45, 0, 0)),
             ell("Head", (0, -1.35, zb + 3.15), (0.52, 0.62, 0.5), K)]
    mz = cone("Muzzle", 0.36, 0.13, 1.05, (0, 0, 0), K["core"], verts=10)
    mz.matrix_world = T(0, -2.25, zb + 2.98) @ RX(math.pi / 2 + 0.12)
    parts.append(mz)
    parts.append(ell("Jaw", (0, -1.85, zb + 2.78), (0.3, 0.55, 0.18), K, rot=(0.1, 0, 0)))
    for sx in (-1, 1):
        ear = cone(f"Ear{sx}", 0.26, 0.0, 0.85, (0, 0, 0), K["core"], verts=6)
        ear.matrix_world = T(sx * 0.3, -1.15, zb + 3.82) @ RY(sx * 0.18) @ RX(0.15)
        for v in ear.data.vertices:
            v.co.y *= 0.55
        parts.append(ear)
        parts.append(ell(f"Foreleg{sx}", (sx * 0.5, -1.55, zb + 0.32), (0.3, 1.25, 0.3), K))
        parts.append(ell(f"Paw{sx}", (sx * 0.5, -2.75, zb + 0.22), (0.32, 0.42, 0.2), K))
        parts.append(ell(f"Hind{sx}", (sx * 1.0, 2.25, zb + 0.45), (0.32, 0.95, 0.42), K))
    tail = bar("Tail", [(0.6, 3.3, zb + 0.5), (1.4, 3.0, zb + 0.35), (1.55, 1.8, zb + 0.32), (1.4, 0.4, zb + 0.32), (1.1, -0.6, zb + 0.35)],
               lambda t: 0.42 * math.sin(math.pi * min(1.0, 0.25 + t * 0.85)) + 0.12, K["core"], seg=12)
    parts.append(tail)
    cards = Cards(rng)
    for ob in parts:
        clip_cards(cards, ob, density=2.5 if ob is not plinth else 3.0, size=0.5 if ob is not plinth else 0.75, tilt=0.2)
    cards.build("Leaves")
    P.ATLAS["HedgeWolf_Leaves"] = "NH_GardenLeaves"
    return _dims()

def hedge_raven(M):
    """Estate topiary: a raven perched upright on a clipped yew column, 8.3 tall: a square column with a moulded cap, the bird
    standing tall with a shaggy ruff at its throat, a long heavy beak, wings folded with long primaries crossing over a wedge
    tail. It looks out over the path (-Y)."""
    K = gk2(M)
    rng = RNG(27)
    col = box("Column", (1.9, 1.9, 3.2), (0, 0, 1.6), K["core"], bevel=0.12, segments=3)
    cap = box("Cap", (2.4, 2.4, 0.4), (0, 0, 3.4), K["core"], bevel=0.12, segments=3)
    plinth = box("Perch", (1.5, 1.5, 0.3), (0, 0, 3.75), K["core"], bevel=0.1, segments=2)
    parts = [col, cap, plinth,
             ell("Body", (0, 0.1, 5.0), (0.55, 0.62, 1.05), K, rot=(-0.25, 0, 0)),
             ell("Breast", (0, -0.28, 5.2), (0.5, 0.45, 0.75), K),
             ell("Neck", (0, -0.22, 6.0), (0.36, 0.36, 0.42), K),
             ell("Head", (0, -0.36, 6.48), (0.34, 0.42, 0.34), K, rot=(-0.15, 0, 0)),
             ell("Thigh", (0, 0.05, 4.25), (0.5, 0.45, 0.35), K)]
    for k in range(9):          # the shaggy throat ruff: spiky hackles fanning down
        a = -math.pi * 0.8 + k / 8 * math.pi * 0.6 - math.pi / 2 + math.pi / 2
        a = math.pi * (1.15 + k / 8 * 0.7)
        h = cone(f"Hackle{k}", 0.13, 0.0, 0.55, (0, 0, 0), K["core"], verts=5)
        h.matrix_world = T(math.cos(a) * 0.28, -0.4 + math.sin(a) * 0.12 + 0.05, 5.85) @ RZ(a + math.pi / 2) @ RX(math.pi - 0.5)
        parts.append(h)
    bk = cone("Beak", 0.2, 0.03, 1.05, (0, 0, 0), K["core"], verts=8)
    bk.matrix_world = T(0, -1.05, 6.35) @ RX(math.pi / 2 + 0.28)
    parts.append(bk)
    cres = cone("BeakRidge", 0.09, 0.02, 0.8, (0, 0, 0), K["core"], verts=6)
    cres.matrix_world = T(0, -0.95, 6.52) @ RX(math.pi / 2 + 0.38)
    parts.append(cres)
    for sx in (-1, 1):
        wing = ell(f"Wing{sx}", (sx * 0.5, 0.25, 5.05), (0.16, 0.6, 1.0), K, rot=(-0.3, sx * 0.12, 0))
        parts.append(wing)
        for j in range(3):          # long primaries reaching down past the tail
            pr = cone(f"Primary{sx}{j}", 0.13, 0.0, 1.5, (0, 0, 0), K["core"], verts=5)
            pr.matrix_world = T(sx * (0.42 - j * 0.08), 0.55 + j * 0.06, 4.35) @ RX(math.pi - 0.38) @ RY(sx * 0.12)
            parts.append(pr)
        parts.append(ell(f"Foot{sx}", (sx * 0.22, -0.3, 4.0), (0.12, 0.38, 0.1), K))
    tail = cone("Tail", 0.42, 0.06, 1.5, (0, 0, 0), K["core"], verts=4)
    tail.matrix_world = T(0, 0.85, 3.85) @ RX(math.pi - 0.45) @ RZ(math.pi / 4)
    for v in tail.data.vertices:
        v.co.x *= 1.0
        v.co.y *= 0.35
    parts.append(tail)
    cards = Cards(rng)
    for ob in parts:
        clip_cards(cards, ob, density=2.5 if ob not in (col, cap, plinth) else 3.0, size=0.45, tilt=0.2)
    cards.build("Leaves")
    P.ATLAS["HedgeRaven_Leaves"] = "NH_GardenLeaves"
    return _dims()

# ------------------------------------------------------------------ v2 roses

def petal(name, base, out, L, W, opening, cup, mat, curl=0.25, thick=0.012, solid=True):
    """A cupped petal from `base` growing outward along the horizontal direction `out`, `opening` radians off vertical."""
    out = Vector(out).normalized()
    side = UP.cross(out).normalized()
    ax = (UP * math.cos(opening) + out * math.sin(opening)).normalized()
    nrm = side.cross(ax).normalized()
    rows = []
    for i in range(4):
        t = i / 3
        w = W * math.sin(math.pi * (0.18 + 0.82 * t)) ** 0.55
        c = Vector(base) + ax * (L * t) + nrm * (curl * L * t ** 3)
        row = []
        for j in range(3):
            s = (j / 2 - 0.5) * 2
            row.append(c + side * (s * w) - nrm * (cup * w * (1 - s * s) * (1 - t * 0.4)))
        rows.append(row)
    if not solid:     # one-sided (sepals under a bloom, petals lying on the ground)
        V = [tuple(p) for r in rows for p in r]
        F = [(i * 3 + j, i * 3 + j + 1, (i + 1) * 3 + j + 1, (i + 1) * 3 + j) for i in range(3) for j in range(2)]
        return mk(name, V, F, mat, smooth=True)
    from nh_props_batch4 import _mesh
    return _mesh(name, [[tuple(p) for p in r] for r in rows], mat, thick)


def bloom(prefix, pos, direction, r, mat, heart=None, sepal=None, opened=1.0, rng=None):
    """A rose: a tight heart, rings of cupped petals opening outward, sepals under it; aimed along `direction`."""
    from nh_props_batch4 import _aim
    s = _mark()
    hm = heart or mat
    sphere(f"{prefix}Heart", r * (0.34 if heart else 0.26), (0, 0, r * 0.34), hm, seg=8, rings=5, scale=(1, 1, 1.2))
    spec = ((4, 0.6, 0.2, mat, False), (5, 0.85, 0.75 * opened + 0.2, mat, True), (6, 1.05, 1.2 * opened + 0.3, mat, True))
    for k, (cnt, ln, op, pm, solid) in enumerate(spec):
        for i in range(cnt):
            a = i / cnt * 2 * math.pi + k * 0.7 + (rng.uniform(-0.2, 0.2) if rng is not None else 0)
            d = (math.cos(a), math.sin(a), 0)
            base = (math.cos(a) * r * 0.08 * k, math.sin(a) * r * 0.08 * k, r * 0.05)
            petal(f"{prefix}P{k}{i}", base, d, r * ln, r * (0.38 + 0.08 * k), op, 0.35, pm, curl=0.2 + 0.1 * k, solid=solid)
    if sepal is not None:
        for i in range(5):
            a = i / 5 * 2 * math.pi + 0.3
            petal(f"{prefix}S{i}", (0, 0, 0), (math.cos(a), math.sin(a), 0), r * 0.75, r * 0.14, 2.2, 0.1, sepal, curl=-0.1, solid=False)
    _xform(s, Matrix.Translation(pos) @ _aim(direction))


def rose_bush2(M, black=False):
    """A full shrub rose 4.3 tall and 5 across: a dense, irregular mound of leaves (cards over a near-black heart), thorny canes
    arching out of its sides and down in S-curves, some twenty modelled roses set into its surface and more at the cane tips,
    petals fallen round its foot. The black rose's blooms are near-black with only a crimson heart."""
    K = gk2(M)
    rng = RNG(13 if black else 11)
    pm = K["petalblack"] if black else K["petal"]
    heart = K["petalheart"] if black else None
    mound("Soil", 1.6, 1.5, 0.2, K["soil"], rng, seg=12)
    dark = shrub_core("RoseHeart")
    cores = [((0, 0, 1.2), (2.05, 1.85, 1.15)), ((0.75, -0.45, 2.0), (1.3, 1.2, 1.0)), ((-0.8, 0.5, 1.95), (1.25, 1.2, 1.0)),
             ((0.25, 0.8, 2.3), (1.05, 0.95, 0.9)), ((-0.4, -0.75, 2.35), (0.95, 0.9, 0.85)), ((0.05, 0.0, 2.85), (1.0, 0.95, 0.75))]
    core_obs = []
    for i, (c, rr) in enumerate(cores):
        core_obs.append(blob(f"Mass{i}", c, 1.0, dark, seg=12, rings=8, scale=tuple(v * 0.8 for v in rr), jitter=0.12, seed=i + 7))
    for k in range(6):
        a = k / 6 * 6.28
        bar(f"Stem{k}", bez((math.cos(a) * 0.15, math.sin(a) * 0.15, 0.1), (math.cos(a) * 0.5, math.sin(a) * 0.5, 0.5), (math.cos(a) * 0.9, math.sin(a) * 0.9, 1.0), 4),
            0.07, K["stem"], seg=6)
    cards = Cards(rng)
    for ob in core_obs:
        cards.cover(ob, 9.0, "rose_leaves", 1.0, offset=0.1, tilt=0.35, zmin=0.25, nscale=0.9)
    tips = []
    for k in range(7):          # canes arching out of the sides and down
        a = k / 7 * 2 * math.pi + rng.uniform(-0.25, 0.25)
        out = Vector((math.cos(a), math.sin(a), 0))
        side = UP.cross(out)
        z0 = rng.uniform(1.4, 2.3)
        pts = []
        for i in range(13):
            t = i / 12
            p = out * (1.2 + 1.9 * t) + side * (math.sin(t * math.pi * 1.6) * 0.3) + UP * (z0 + 0.9 * math.sin(t * math.pi * 0.8) - 1.3 * t * t)
            pts.append(tuple(p))
        bar(f"Cane{k}", pts, lambda t: 0.055 * (1 - t * 0.5), K["stem"], seg=6)
        for i in range(2, 12):
            p0, p1 = Vector(pts[i]), Vector(pts[i + 1])
            for j in range(2):
                o = ((side if j else -side) * 0.6 + (p1 - p0).normalized() * 0.5 + UP * 0.2).normalized()
                q = p0.lerp(p1, 0.5 * j + 0.2)
                th = cone(f"Thorn{k}{i}{j}", 0.024, 0.0, 0.1, tuple(q + o * 0.05), K["thorn"], verts=4, rot=tuple(o.to_track_quat("Z", "Y").to_euler()))
                th.modifiers.clear()
            if i % 3 == 1:
                n = (out + UP * 0.5 + side * rng.uniform(-0.5, 0.5)).normalized()
                ax, ay = frame(n, roll=rng.uniform(0, 6.28))
                cards.add(tuple(p0 + n * 0.1), ax, ay, 0.7, 0.7, "rose_leaves", "fill", nrm=n)
        tips.append((Vector(pts[-1]), (Vector(pts[-1]) - Vector(pts[-3])).normalized()))
    spots = []
    for p, n in sum((surface_samples(ob, 1.2, rng) for ob in core_obs), []):
        if n.z > -0.25 and p.z > 1.0 and min((p - q).length for q, _ in spots or [(Vector((99, 99, 99)), None)]) > 0.7:
            spots.append((p, n))
    rng.shuffle(spots)
    from nh_props_batch4 import _aim
    for c, (p, n) in enumerate(spots[:18]):
        d = (n + UP * 0.25).normalized()
        bloom(f"Rose{c}", tuple(p + n * 0.32), tuple(d), rng.uniform(0.3, 0.36), pm, heart=heart, sepal=K["stem"], opened=rng.uniform(0.85, 1.15), rng=rng)
    for c, (p, d) in enumerate(tips[:5]):
        bloom(f"TipRose{c}", tuple(p), tuple((d + UP * 0.6).normalized()), 0.22, pm, heart=heart, sepal=K["stem"], opened=0.9, rng=rng)
    for c, (p, n) in enumerate(spots[18:24]):
        s = _mark()
        sphere(f"Bud{c}", 0.07, (0, 0, 0.08), pm, seg=6, rings=4, scale=(1, 1, 1.7))
        for i in range(4):
            aa = i / 4 * 2 * math.pi
            petal(f"BudSepal{c}{i}", (0, 0, 0), (math.cos(aa), math.sin(aa), 0), 0.19, 0.05, 0.35, 0.15, K["stem"], curl=0.05, solid=False)
        _xform(s, Matrix.Translation(tuple(p + n * 0.15)) @ _aim(tuple(n)))
    for k in range(36):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(1.2, 3.0)
        z = 0.2 * max(0.0, 1 - (rr / 1.6) ** 2) + 0.012
        petal(f"Fallen{k}", (math.cos(a) * rr, math.sin(a) * rr, z), (math.cos(a + rng.uniform(-2, 2)), math.sin(a + rng.uniform(-2, 2)), 0), 0.17, 0.09, 1.45,
              0.25, pm, curl=0.15, solid=False)
    cards.build("Leaves")
    P.ATLAS[f"{'RoseBushBlack' if black else 'RoseBushCrimson'}_Leaves"] = "NH_GardenLeaves"
    return _dims()

# ------------------------------------------------------------------ v2 willow

def weeping_willow2(M):
    """A weeping willow 16 tall, 17 across: a thick, gnarled trunk leaning a little, burred and split into three leaders over a
    knot of roots; limbs that arch up into a dome and fall away; long thin fronds hanging from them in layered, tapering
    curtains, longest at the rim (some nearly to the grass), with gaps that show the trunk; dark green, silvery beneath."""
    K = gk2(M)
    rng = RNG(31)
    lean = Vector((0.9, 0.5, 0))
    trunk("Trunk", (0, 0, 0.0), tuple(lean * 1.0 + Vector((0, 0, 5.0))), 1.25, 0.85, K["bark"], seg=16, wobble=0.3, rng=rng, n=10)
    roots("Root", K, 1.2, 9, rng, spread=2.4)
    for k in range(7):
        a = rng.uniform(0, 6.28)
        z = rng.uniform(0.8, 4.2)
        c = lean * (z / 5.0)
        blob(f"Burl{k}", (c.x + math.cos(a) * 0.95, c.y + math.sin(a) * 0.95, z), rng.uniform(0.25, 0.42), K["bark"], seg=9, rings=6,
             scale=(1, 1, 0.8), jitter=0.18, seed=k)
    top = lean * 1.0 + Vector((0, 0, 4.7))
    leaders = []
    for j in range(3):
        a = j / 3 * 2 * math.pi + 0.4
        end = top + Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, 3.0))
        trunk(f"Leader{j}", tuple(top), tuple(end), 0.68, 0.42, K["bark"], seg=12, wobble=0.22, rng=rng, n=6)
        leaders.append(end)
    cards = Cards(rng)
    for k in range(14):
        a = k / 14 * 2 * math.pi + rng.uniform(-0.15, 0.15)
        s = leaders[k % 3] + Vector((0, 0, rng.uniform(-0.6, 0.3)))
        R = rng.uniform(6.0, 8.2)
        peak = Vector((top.x + math.cos(a) * R * 0.38, top.y + math.sin(a) * R * 0.38, rng.uniform(13.0, 14.6)))
        end = Vector((top.x + math.cos(a) * R, top.y + math.sin(a) * R, rng.uniform(9.5, 11.0)))
        pts = bez(tuple(s), tuple(peak + Vector((0, 0, 0.8))), tuple(end), 12)
        bar(f"Limb{k}", pts, lambda t: 0.34 * (1 - t * 0.82), K["bark"], seg=7)
        for j in range(2):
            a2 = a + rng.uniform(-0.6, 0.6)
            st = Vector(pts[5 + j * 3])
            en = st + Vector((math.cos(a2) * 2.2, math.sin(a2) * 2.2, -rng.uniform(0.4, 1.2)))
            bar(f"Twig{k}{j}", [tuple(st), tuple((st + en) / 2 + Vector((0, 0, 0.25))), tuple(en)], lambda t: 0.1 * (1 - t * 0.75), K["bark"], seg=5)
            pts = pts + [tuple(en)]
        # fronds hang from the limb's outer two thirds (and its twigs): each card a curtain of a few fronds, tapering, swaying out
        for p in pts[3:]:
            p = Vector(p)
            rr = math.hypot(p.x - top.x, p.y - top.y)
            out = Vector((p.x - top.x, p.y - top.y, 0)).normalized()
            for m in range(3):
                q = p + Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), rng.uniform(-0.2, 0.1)))
                rim = min(1.0, rr / 7.5) ** 1.3
                h = (q.z - 0.6) * (0.2 + 0.8 * rim) * rng.uniform(0.3, 1.0)
                if rim > 0.6 and rng.random() < 0.12:     # a few strands nearly to the grass
                    h = q.z - rng.uniform(0.3, 0.8)
                if h < 1.2 or rng.random() < 0.18:      # gaps in the curtain
                    continue
                yaw = math.atan2(out.y, out.x) + math.pi / 2 + rng.uniform(-0.6, 0.6)
                cards.hang(tuple(q), rng.uniform(0.9, 1.4), h, "willow", yaw=yaw, sway=0.0, segs=4)
                for v in (-10, -9):
                    cards.V[v] += out * h * 0.16
                for v in (-8, -7):
                    cards.V[v] += out * h * 0.08
    cards.build("Leaves")
    P.ATLAS["WeepingWillow_Leaves"] = "NH_GardenLeaves"
    return _dims()


def batwing_unit(K, name, L, rng):
    """A limestone edging stone whose top is scalloped into a bat's wing: points at the ends and the middle, concave sweeps
    between (along +X, centred, 0.22 thick)."""
    from nh_props_batch20 import tprism
    hw = L / 2 - 0.02
    top = []
    n = 6
    for half in (0, 1):
        x0 = -hw + half * hw
        for i in range(n + 1):
            t = i / n
            x = x0 + hw * t
            z = 0.36 + 0.2 * ((2 * t - 1) ** 2) ** 0.8 * (1.0 if half == 0 else 1.0) - 0.04 * math.sin(math.pi * t)
            if not (half == 1 and i == 0):
                top.append((x, z))
    top[0] = (top[0][0], 0.6)
    top[-1] = (top[-1][0], 0.6)
    top[n] = (top[n][0], 0.56)
    prof = [(-hw, 0.0), (hw, 0.0)] + list(reversed(top))
    ob = tprism(name, prof, 0, 0.22, K["limel"])
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = 0.025
    md.segments = 2
    md.limit_method = "ANGLE"
    return ob



def curl_unit(K, name, L, rng):
    """A low granite kerb with a wrought-iron S-curl standing on it."""
    box(name, (L - 0.05, 0.34, 0.36), (0, 0, 0.18), K["gran"], bevel=0.05, segments=2)
    pts = []
    for i in range(15):
        t = i / 14
        a = t * 2 * math.pi * 1.25
        rr = 0.18 * (1 - t * 0.55)
        side = 1 if t < 0.5 else -1
        pts.append((side * (0.16 - math.cos(a) * rr * 0.9) * L / 1.25, 0.0, 0.42 + 0.17 + math.sin(a) * rr))
    pts = [(L * 0.42 * (2 * (i / 14) - 1) + 0.12 * math.sin(i / 14 * 6.28 * 1.5), 0.0, 0.44 + 0.16 * abs(math.sin(i / 14 * 6.28 * 1.0)) + 0.06 * math.cos(i / 14 * 6.28 * 2.0))
           for i in range(15)]
    bar(name + "Curl", pts, 0.022, K["iron"], seg=5)
    for sx in (-1, 1):
        c = (sx * L * 0.3, 0, 0.58)
        bar(f"{name}Scroll{sx}", [(c[0] + sx * math.cos(a) * 0.12 * (1 - a / 10), 0.0, c[2] + math.sin(a) * 0.12 * (1 - a / 10)) for a in [i / 9 * 7.5 for i in range(10)]],
            0.018, K["iron"], seg=4)
        sphere(f"{name}Knob{sx}", 0.035, (sx * L * 0.42, 0, 0.62), K["iron"], seg=6, rings=4)



def soldier_unit(K, name, L, rng):
    b = K["bricks"][rng.integers(3)] if rng.random() > 0.18 else K["soot"]
    box(name, (0.22, 0.42, 0.46), (0, 0, 0.23), b, bevel=0.012, segments=1)


EDGE_UNITS = {"cobble": (curl_unit, 1.25), "gravel": (batwing_unit, 1.25), "herring": (soldier_unit, 0.27)}



def edge_run2(kind, K, prefix, p0, p1, rng, skip=()):
    fn, unit = EDGE_UNITS[kind]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    n = max(1, round(L / unit))
    a = math.atan2(dy, dx)
    for i in range(n):
        if i in skip:
            continue
        t = (i + 0.5) / n
        s = _mark()
        fn(K, f"{prefix}{i}", L / n, rng)
        _xform(s, T(p0[0] + dx * t, p0[1] + dy * t, 0) @ RZ(a))



def edge_arc2(kind, K, prefix, c, r, a0, a1, rng):
    fn, unit = EDGE_UNITS[kind]
    L = abs(a1 - a0) * r
    n = max(1, round(L / unit))
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        s = _mark()
        fn(K, f"{prefix}{i}", L / n * 1.02, rng)
        _xform(s, T(c[0] + math.cos(a) * r, c[1] + math.sin(a) * r, 0) @ RZ(a + math.pi / 2))



def polar_uv(ob, c, r_mid, a0, a1, tile=10.0):
    """UVs that follow a curve: across = 5 - r (as a straight piece's x), along = the angle scaled so the 90-degree turn is one
    10-stud tile (so the fan-laid cobble meets the straights at both ends)."""
    me = ob.data
    uv = me.uv_layers.new(name="Bake")
    for poly in me.polygons:
        for li in poly.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            r = math.hypot(x - c[0], y - c[1])
            a = math.atan2(y - c[1], x - c[0])
            along = -5 + (a0 - a) / (a0 - a1) * 10.0
            if abs(z - PT) > 0.01 and r > r_mid:        # outer side faces: run the texture round
                pass
            uv.data[li].uv = ((5 - r) / tile, along / tile)



def path_tiled2(M, kind, shape, name):
    """Gravel, cobble and herringbone cells (Path: the tiled set; the edging in Main). straight: along Y; curve: from the front
    (-Y) edge round to the right (+X)."""
    K = gk2(M)
    K["soot"] = flat("SootBrick", (0.045, 0.03, 0.03), 0.8, wear=0.3, dirt=0.9)
    rng = RNG(zlib.crc32((kind + shape + "v3").encode()) & 0xFFFF)
    h, e = HALF, HALF + 0.2
    top = PT - (0.04 if kind == "gravel" else 0.0)
    set_group("Path")
    if shape == "straight":
        poly_slab("Path", [(-h, -5), (h, -5), (h, 5), (-h, 5)], 0, top, K["lime"])
        P.TILED[f"{name}_Path"] = (SETS[kind], 10.0)
    else:
        ob = ring_slab("Path", (5, -5), 5 - h, 5 + h, math.pi / 2, math.pi, 0, top, K["lime"], n=24, ends=True)
        if kind == "cobble":
            polar_uv(ob, (5, -5), 5, math.pi, math.pi / 2)
            P.ATLAS[f"{name}_Path"] = SETS[kind]
        else:
            P.TILED[f"{name}_Path"] = (SETS[kind], 10.0)
    set_group("Main")
    if shape == "straight":
        for sx in (-1, 1):
            skip = (int(rng.integers(5, 30)),) if kind == "herring" and sx == 1 else ()
            edge_run2(kind, K, f"E{sx}_", (sx * e, -5), (sx * e, 5), rng, skip=skip)
            if skip:          # the missing soldier, toppled onto the grass
                y = -5 + (skip[0] + 0.5) * 10 / round(10 / 0.27)
                box("Toppled", (0.46, 0.22, 0.42), (sx * (e + 0.55), y + 0.1, 0.11), K["soot"], bevel=0.012, segments=1, rot=(0, 0, 0.5))
                P.PARTS[-1].matrix_world = T(sx * (e + 0.55), y + 0.1, 0.11) @ RZ(0.5) @ RX(math.pi / 2)
    else:
        edge_arc2(kind, K, "Ein", (5, -5), 5 - e, math.pi / 2, math.pi, rng)
        edge_arc2(kind, K, "Eout", (5, -5), 5 + e, math.pi / 2, math.pi, rng)
    if kind == "gravel":       # a few rose petals blown onto the gravel and the edging (modelled, so they catch the light)
        for k in range(14):
            x, y = rng.uniform(-2.8, 2.8), rng.uniform(-4.8, 4.8)
            if shape == "curve":
                a, r = rng.uniform(math.pi / 2, math.pi), rng.uniform(2.3, 7.7)
                x, y = 5 + math.cos(a) * r, -5 + math.sin(a) * r
            petal(f"Petal{k}", (x, y, top + 0.01), (math.cos(k * 2.3), math.sin(k * 2.3), 0), 0.17, 0.09, 1.45, 0.25,
                  K["petalblack"] if k % 3 else K["petal"], curl=0.15, solid=False)
    return _dims()



def stepping_stones2(M):
    """Five hand-cut limestone stepping stones bedded in moss along a 10-stud run (Y), tops 0.14 to 0.22, one carved with a
    worn crescent, their edges broken."""
    K = gk2(M)
    rng = RNG(55)
    for i in range(5):
        y = -4.0 + i * 2.0
        x = rng.uniform(-0.4, 0.4)
        out = _roughen(blob_outline(rng.uniform(0.75, 0.95), rng.uniform(0.6, 0.75), 9, rng, 0.16, cx=x, cy=y), rng, 0.05, chip=0.35)
        mat = carved(f"StepCarve{i}", (x, y), 1.1, 0, rot=rng.uniform(-0.3, 0.3)) if i == 2 else K["flag"]
        stone_slab(f"Stone{i}", out, 0.0, rng.uniform(0.15, 0.22), mat, tilt=(rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)), bevel=0.05,
                   dish=0.02)
        stone(f"Moss{i}", x, y, 1.08, 0.92, 0.0, 0.05, K["moss2"], rng, n=12, bevel=0.0, rot=rng.uniform(0, 3))
    return _dims()



def garden_steps2(M):
    """Three wide, shallow limestone steps, 10 deep, 8 wide between mossy cheek walls: each tread of three hand-cut slabs worn
    into hollows in the middle by centuries of feet, lichen on them; risers 0.6 from the path top (0.3) to a landing at 2.1 at
    the back (+Y); ball finials on the cheeks; grass and ferns at their feet (Leaves)."""
    K = gk2(M)
    rng = RNG(9)
    W, go = 8.0, 10 / 3
    for k in range(3):
        y0 = -5 + k * go
        z1 = PT + 0.6 * (k + 1)
        box(f"Core{k}", (W, 10 - k * go, z1 - 0.18), (0, (y0 + 5) / 2, (z1 - 0.18) / 2), K["wall"], bevel=0.0)
        n = 3
        for j in range(n):
            x0 = -W / 2 + W * j / n
            out = _roughen([(x0 + 0.03, y0 - 0.12), (x0 + W / n - 0.03, y0 - 0.12), (x0 + W / n - 0.03, y0 + go - 0.05), (x0 + 0.03, y0 + go - 0.05)], rng,
                           0.03, chip=0.3)
            stone_slab(f"Tread{k}{j}", out, z1 - 0.22, z1 + rng.uniform(-0.015, 0.015), K["flag"], bevel=0.06, dish=0.06 if j == 1 else 0.03)
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.5)
        pts = [(-5, 0), (5, 0), (5, 2.9), (-5, 1.2)]
        V = [(x - 0.5, y, z) for y, z in pts] + [(x + 0.5, y, z) for y, z in pts]
        F = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        P_recalc(mk(f"Cheek{sx}", V, F, K["wall"], smooth=False, bevel=0.05))
        box(f"Cope{sx}", (1.15, 10.4, 0.2), (x, 0, 0), K["lime"], bevel=0.05, segments=2)
        P.PARTS[-1].matrix_world = T(x, 0, 2.15) @ RX(math.atan2(1.7, 10))
        sphere(f"Ball{sx}", 0.42, (x, -4.7, 1.75), K["lime"], seg=14, rings=8)
        cyl(f"BallFoot{sx}", 0.32, 0.25, (x, -4.7, 1.38), K["lime"], verts=14, bevel=0.03)
    cards = Cards(rng)
    for sx in (-1, 1):
        for k in range(4):
            cards.crossed((sx * (W / 2 + rng.uniform(0.95, 1.2)), rng.uniform(-4.6, 4.0), 0), 1.2, 1.3, "grass", k=2)
        cards.fronds((sx * (W / 2 - 0.4), -5.15, 0.1), 5, 1.4, 0.7, "fern", elev=(20, 50))
    cards.build("Leaves")
    P.ATLAS["GardenSteps_Leaves"] = "NH_GardenLeaves"
    return _dims()



def edging_curls(M):
    """A 10-long run of wrought-iron edging in scrolls: a row of S-curls and C-scrolls 0.7 tall between a top and bottom rail,
    spear-tipped stakes every 2.5, in the XZ plane (pivot at ground level)."""
    K = gk2(M)
    for z in (0.08, 0.62):
        bar(f"Rail{z}", [(-5, 0, z), (5, 0, z)], 0.022, K["iron"], seg=5)
    for i in range(10):
        x0 = -5 + i + 0.5
        sgn = 1 if i % 2 else -1
        pts = []
        for j in range(17):
            t = j / 16
            a = t * math.pi * 2
            pts.append((x0 + sgn * 0.32 * math.sin(a) * (1 - abs(t - 0.5)), 0.0, 0.1 + 0.5 * t + 0.08 * math.sin(a * 2)))
        bar(f"S{i}", pts, 0.02, K["iron"], seg=5)
        for end, zc in ((0, 0.22), (1, 0.5)):
            c = (x0 + sgn * (0.15 if end else -0.15), 0.0, zc)
            bar(f"Curl{i}{end}", [(c[0] + math.cos(a) * 0.1 * (1 - a / 11), 0.0, c[2] + math.sin(a) * 0.1 * (1 - a / 11)) for a in [k / 9 * 8.0 for k in range(10)]],
                0.016, K["iron"], seg=4)
    for i in range(5):
        x = -5 + i * 2.5
        bar(f"Stake{i}", [(x, 0, 0.0), (x, 0, 0.75)], 0.03, K["iron"], seg=6)
        cone(f"Spear{i}", 0.06, 0.0, 0.18, (x, 0, 0.84), K["iron"], verts=4)
    return _dims()



def bridge_slab(M):
    """A slab bridge over a narrow rill in a 10-stud cell: two great limestone slabs (top 0.7) on rough abutments, the rill
    running across under it (along X) between mossy banks, its water Glass. The path crosses along Y; the slabs' ends come
    down to the path height (0.3) at the cell's edges."""
    K = gk2(M)
    rng = RNG(61)
    # the rill's bed and banks (the water runs along X across the whole cell)
    poly_slab("Bed", [(-5, -1.3), (5, -1.3), (5, 1.3), (-5, 1.3)], -0.0, 0.02, flat("RillBed", (0.03, 0.035, 0.03), 0.8))
    for sy in (-1, 1):
        V, F = [], []
        xs = [-5 + i * 0.5 for i in range(21)]
        for x in xs:
            V.append((x, sy * (1.3 + rng.uniform(-0.1, 0.1)), 0.02))
            V.append((x, sy * (2.4 + rng.uniform(-0.2, 0.2)), 0.3 + rng.uniform(-0.03, 0.03)))
        for i in range(20):
            a = i * 2
            F.append((a, a + 2, a + 3, a + 1) if sy > 0 else (a, a + 1, a + 3, a + 2))
        P_recalc(mk(f"Bank{sy}", V, F, K["moss2"], smooth=True))
        for k in range(6):
            x = -4.5 + k * 1.8 + rng.uniform(-0.3, 0.3)
            stone(f"BankStone{sy}{k}", x, sy * rng.uniform(1.35, 1.8), rng.uniform(0.3, 0.5), rng.uniform(0.25, 0.4), 0.0, rng.uniform(0.15, 0.3),
                  K["flagdark"], rng, n=8, bevel=0.04)
    set_group("Glass")
    poly_slab("Water", [(-5, -1.32), (5, -1.32), (5, 1.32), (-5, 1.32)], 0.14, 0.16, K["water"])
    set_group("Main")
    # abutments of rough blocks, the two slabs
    for sy in (-1, 1):
        for k, x in enumerate((-2.2, 0.0, 2.2)):
            box(f"Abut{sy}{k}", (2.1, 1.1, 0.55), (x, sy * 1.55, 0.275), K["wall"], bevel=0.06, segments=2)
    for k, x0 in enumerate((-3.2, 0.06)):
        out = _roughen([(x0, -5), (x0 + 3.14, -5), (x0 + 3.14, 5), (x0, 5)], rng, 0.04, chip=0.2)
        V = []
        n = len(out)
        for (x, y) in out:
            zt = 0.3 + 0.4 * max(0.0, 1 - (abs(y) / 5) ** 2 * 1.0) * min(1, (5 - abs(y)) / 2.6)
            V.append((x, y, zt))
        base = [(x, y, z - 0.28) for x, y, z in V]
        Vt = base + V
        F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)] + [tuple(range(n, 2 * n)), tuple(reversed(range(n)))]
        ob = mk(f"Slab{k}", Vt, F, K["flag"], smooth=False, tri=True)
        md = ob.modifiers.new("Bevel", "BEVEL")
        md.width = 0.05
        md.segments = 2
        md.limit_method = "ANGLE"
    return _dims()



def gate_arch(M):
    """A gothic wrought-iron arch over a path, 8 wide and 11 tall: twin square posts with spear finials on stone footings, a
    pointed arch of double bars filled with tracery (quatrefoils, a crescent at the crown), and a lantern hook hanging an iron
    lantern over the path (Glass: its panes; Glow: the candle). Walk through along Y."""
    K = gk2(M)
    hw, zs = 3.6, 6.4
    for sx in (-1, 1):
        x = sx * hw
        box(f"Footing{sx}", (0.9, 0.9, 0.5), (x, 0, 0.25), K["lime"], bevel=0.06, segments=2)
        box(f"Post{sx}", (0.26, 0.26, zs), (x, 0, 0.5 + zs / 2), K["iron"], bevel=0.03, segments=2)
        cone(f"Finial{sx}", 0.18, 0.0, 0.7, (x, 0, 0.5 + zs + 2.3), K["iron"], verts=4)
        box(f"FinialStem{sx}", (0.12, 0.12, 2.0), (x, 0, 0.5 + zs + 1.0), K["iron"], bevel=0.02, segments=1)
        for z in (1.6, 3.4, 5.2):
            ringbar(f"Collar{sx}{z}", (x, 0, z), 0.2, "Z", K["iron"], thick=0.03, n=8, seg=4)
    R = (2 * hw) * 0.85
    for k, off in enumerate((0.0, 0.32)):
        rr = R - off
        pts_l = []
        for i in range(13):
            a = math.acos((rr - (hw - off)) / rr) * i / 12
            pts_l.append((-(hw - off) + (rr - rr * math.cos(a)), 0.0, zs + 0.5 + rr * math.sin(a)))
        pts = pts_l + [(-x, 0.0, z) for x, y, z in reversed(pts_l[:-1])]
        bar(f"Arch{k}", pts, 0.05, K["iron"], seg=6)
    crown = zs + 0.5 + R * math.sin(math.acos((R - hw) / R))
    for i in range(1, 6):
        t = i / 6
        a = math.acos((R - hw) / R) * t
        x = -hw + (R - R * math.cos(a))
        z = zs + 0.5 + R * math.sin(a)
        for sx in (-1, 1):
            ringbar(f"Foil{i}{sx}", (sx * (x + 0.05) * 0.93, 0, z - 0.45), 0.2, "Y", K["iron"], thick=0.025, n=10, seg=4)
    s = _mark()
    ring_slab("Crescent", (0, 0), 0.3, 0.42, 0.6, 5.7, -0.03, 0.03, K["brass"], n=14)
    _xform(s, T(0, 0, crown - 0.7) @ RX(math.pi / 2))
    bar("Hook", [(0, 0, crown - 0.15), (0, 0, crown - 1.2), (0.0, -0.15, crown - 1.4)], 0.03, K["iron"], seg=5)
    bar("Chain", [(0, -0.15, crown - 1.4), (0, -0.15, crown - 2.2)], 0.02, K["iron"], seg=4)
    zl = crown - 2.9
    cone("LampRoof", 0.42, 0.06, 0.45, (0, -0.15, zl + 0.75), K["iron"], verts=6)
    cyl("LampBase", 0.32, 0.12, (0, -0.15, zl - 0.06), K["iron"], verts=6, bevel=0.02)
    for i in range(6):
        a = i / 6 * 2 * math.pi
        bar(f"LampRib{i}", [(math.cos(a) * 0.3, -0.15 + math.sin(a) * 0.3, zl), (math.cos(a) * 0.36, -0.15 + math.sin(a) * 0.36, zl + 0.55)], 0.02, K["iron"], seg=4)
    set_group("Glass")
    lathe("Panes", [(0.28, zl), (0.34, zl + 0.55), (0, zl + 0.55)], K["glass"], seg=6, loc=(0, -0.15, 0))
    set_group("Glow")
    lathe("Flame", [(0, 0), (0.05, 0.03), (0.07, 0.09), (0.05, 0.17), (0, 0.26)], K["glow"], seg=8, loc=(0, -0.15, zl + 0.15))
    set_group("Main")
    cyl("Candle", 0.06, 0.15, (0, -0.15, zl + 0.075), K["bone"], verts=8, bevel=0.0)
    return _dims()



def blood_rose_urn(M):
    """A cast-iron urn 3.6 tall on a square foot, four bat wings spread from its rim, overflowing with deep crimson roses: a
    mound of leaves and blooms, canes trailing over the lip and down its sides, petals fallen round its foot."""
    K = gk2(M)
    rng = RNG(71)
    box("Foot", (1.6, 1.6, 0.35), (0, 0, 0.175), K["iron"], bevel=0.04, segments=2)
    lathe("Urn", [(0, 0.35), (0.42, 0.35), (0.32, 0.55), (0.28, 0.8), (0.55, 1.0), (1.0, 1.5), (1.15, 2.0), (1.05, 2.45), (0.92, 2.6), (1.15, 2.75),
                  (1.2, 2.85), (1.08, 2.9), (0.9, 2.7), (0, 2.65)], K["iron"], seg=24, flute=(16, 0.05))
    from nh_props_batch20 import tprism
    for k in range(4):
        s = _mark()
        wing = [(0.0, 0.0), (0.55, 0.45), (0.95, 0.3), (0.8, 0.12), (0.7, -0.05), (0.52, 0.05), (0.42, -0.12), (0.28, 0.0), (0.15, -0.1)]
        tprism(f"Wing{k}a", wing, 0, 0.04, K["iron"], plane="XZ")
        tprism(f"Wing{k}b", [(-x, z) for x, z in reversed(wing)], 0, 0.04, K["iron"], plane="XZ")
        _xform(s, RZ(k * math.pi / 2 + math.pi / 4) @ T(0, -1.12, 2.62))
    cyl("Soil", 0.95, 0.06, (0, 0, 2.66), K["soil"], verts=16, bevel=0.0)
    leafy = leafy_core("UrnLeaves", (0.022, 0.045, 0.02))
    mass = blob("Mass", (0, 0, 2.95), 1.0, leafy, seg=14, rings=8, scale=(1.05, 1.05, 0.6), jitter=0.08, seed=3)
    cards = Cards(rng)
    cards.cover(mass, 4.5, "rose_leaves", 0.85, offset=0.06, tilt=0.35, zmin=2.6)
    spots = [(p, n) for p, n in surface_samples(mass, 2.0, rng) if n.z > 0.0]
    for c, (p, n) in enumerate(spots[:12]):
        bloom(f"Rose{c}", tuple(p + n * 0.1), tuple((n + UP * 0.3).normalized()), rng.uniform(0.22, 0.28), K["petal"], sepal=K["stem"],
              opened=rng.uniform(0.8, 1.1), rng=rng)
    for k in range(6):          # trailing canes over the lip
        a = k / 6 * 2 * math.pi + 0.3
        out = Vector((math.cos(a), math.sin(a), 0))
        pts = [tuple(out * (0.9 + 0.5 * math.sin(t * 1.6)) + UP * (2.95 - t * t * 1.9)) for t in [i / 8 for i in range(9)]]
        bar(f"Trail{k}", pts, lambda t: 0.04 * (1 - t * 0.5), K["stem"], seg=5)
        for i in range(2, 9, 2):
            q = Vector(pts[i])
            ax, ay = frame(out, roll=rng.uniform(0, 6.28))
            cards.add(tuple(q + out * 0.08), ax, ay, 0.7, 0.7, "rose_leaves", "fill", nrm=out)
        bloom(f"TrailRose{k}", pts[-1], tuple((out - UP * 0.4).normalized()), 0.2, K["petal"], sepal=K["stem"], opened=0.9, rng=rng)
    for k in range(22):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(0.9, 2.2)
        petal(f"Fallen{k}", (math.cos(a) * rr, math.sin(a) * rr, 0.012), (math.cos(a + 1), math.sin(a + 1), 0), 0.17, 0.09, 1.45, 0.25, K["petal"],
              curl=0.15, solid=False)
    cards.build("Leaves")
    P.ATLAS["BloodRoseUrn_Leaves"] = "NH_GardenLeaves"
    return _dims()



def ghost_orchid(M):
    """Ghost orchids in a slender gothic stone planter, 4.6 tall: a tall square stem with lancet panels on a stepped foot,
    a moulded bowl of moss and roots on top, and four arching sprays of pale, almost see-through blooms (six or seven on each),
    their long lower petals trailing (Glass: the petals; Glow: a faint moonlight heart in each)."""
    K = gk2(M)
    rng = RNG(72)
    st = K["limel"]
    box("Foot", (1.1, 1.1, 0.25), (0, 0, 0.125), K["lime"], bevel=0.04, segments=2)
    box("Foot2", (0.85, 0.85, 0.2), (0, 0, 0.35), st, bevel=0.03, segments=2)
    box("Stem", (0.5, 0.5, 1.5), (0, 0, 1.2), st, bevel=0.03, segments=2)
    for k in range(4):
        s = _mark()
        tprism(f"Lancet{k}", [(-0.13, 0.65), (0.13, 0.65), (0.13, 1.45), (0, 1.62), (-0.13, 1.45)], -0.26, 0.025, K["slatec"])
        _xform(s, RZ(k * math.pi / 2))
    lathe("Bowl", [(0, 1.95), (0.3, 1.95), (0.42, 2.05), (0.62, 2.2), (0.72, 2.35), (0.74, 2.45), (0.66, 2.45), (0.6, 2.38), (0, 2.38)], st, seg=20, flute=(8, 0.05))
    blob("Moss", (0, 0, 2.42), 0.6, K["moss2"], seg=12, rings=5, scale=(1, 1, 0.22))
    rootm = flat("OrchidRoot", (0.38, 0.42, 0.36), 0.6, dirt=0.5)
    for k in range(9):
        a = k / 9 * 6.28
        pts = [(math.cos(a + t * 0.5) * (0.45 + 0.3 * t), math.sin(a + t * 0.5) * (0.45 + 0.3 * t), 2.48 - t * 0.5 + 0.1 * math.sin(t * 3)) for t in [i / 6 for i in range(7)]]
        bar(f"Root{k}", pts, 0.022, rootm, seg=4)
    pet = flat("GhostPetal", (0.85, 0.88, 0.86), 0.4)
    for k in range(4):
        a = k / 4 * 6.28 + 0.4
        out = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 2.5))
        pts = [tuple(base + out * (0.9 * t) + UP * (1.6 * math.sin(t * math.pi * 0.55) - 0.3 * t * t)) for t in [i / 12 for i in range(13)]]
        bar(f"Scape{k}", pts, 0.012, rootm, seg=4)
        for j in range(6 + (k % 2)):
            p = Vector(pts[5 + j])
            s = _mark()
            set_group("Glass")
            for i, (ang, L, wdt, op) in enumerate(((0.0, 0.22, 0.07, 0.3), (2.1, 0.2, 0.06, 1.1), (-2.1, 0.2, 0.06, 1.1))):
                petal(f"Sepal{k}{j}{i}", (0, 0, 0), (math.cos(ang), math.sin(ang), 0), L, wdt, op, 0.1, pet, curl=0.15, thick=0.005)
            for sx in (-1, 1):
                petal(f"Leg{k}{j}{sx}", (0, -0.04, -0.02), (sx * 0.35, -1, 0), 0.5, 0.035, 2.6, 0.05, pet, curl=-0.6, thick=0.005)
            petal(f"Lip{k}{j}", (0, -0.02, 0), (0, -1, 0), 0.2, 0.11, 1.9, 0.25, pet, curl=0.3, thick=0.005)
            set_group("Glow")
            sphere(f"Heart{k}{j}", 0.025, (0, -0.015, 0.015), K["glow"], seg=6, rings=4)
            set_group("Main")
            _xform(s, T(*p) @ RZ(a + math.pi / 2 + rng.uniform(-0.4, 0.4)) @ T(0, 0, -0.08))
    return _dims()

def kidney(t, A=5.4, B=3.4):
    """A kidney outline (t = 0..2 pi)."""
    r = 1.0 - 0.28 * math.exp(-((math.atan2(math.sin(t), math.cos(t)) - math.pi / 2) ** 2) * 3.0)
    return (math.cos(t) * A * r, math.sin(t) * B * r + 0.25 * math.cos(2 * t))



def log_bench(M):
    """A bench made from a fallen oak: half a great log, its sawn face the seat (top 1.65, 7 long), its bark rugged and mossy,
    bound with three hammered iron bands, resting on two rough stone blocks; bracket fungi on its flank."""
    K = gk2(M)
    rng = RNG(73)
    L, r = 7.0, 0.85
    seg = 16
    V, F = [], []
    for i in range(12):
        x = -L / 2 + L * i / 11
        for j in range(seg + 1):
            a = math.pi + math.pi * j / seg
            rr = r * (1 + rng.uniform(-0.04, 0.04)) * (1 + 0.04 * math.sin(i * 1.3))
            V.append((x, math.cos(a) * rr, math.sin(a) * rr))
    w = seg + 1
    for i in range(11):
        for j in range(seg):
            a = i * w + j
            F.append((a, a + w, a + w + 1, a + 1))
    ob = mk("LogBark", V, F, K["bark"], smooth=True)
    P_recalc(ob)
    ob.matrix_world = T(0, 0, 1.65)
    # the sawn top and the ends
    poly_slab("Seat", [(-L / 2, -r), (L / 2, -r), (L / 2, r), (-L / 2, r)], 1.6, 1.65, material("SawnOak", "NH_DeskWood", tint=(0.4, 0.32, 0.24), scale=0.3,
                                                                                              rough_add=0.15, wear=0.5, dirt=1.0))
    for sx in (-1, 1):
        V = [(sx * L / 2, math.cos(math.pi + math.pi * j / seg) * r, 1.65 + math.sin(math.pi + math.pi * j / seg) * r) for j in range(seg + 1)]
        mk(f"End{sx}", V, [tuple(range(seg + 1))], material("EndGrain", "NH_DeskWood", tint=(0.36, 0.26, 0.18), scale=0.8, rough_add=0.2, wear=0.3), smooth=False,
           tri=True)
    for k, x in enumerate((-2.6, 0.0, 2.6)):
        pts = [(x, math.cos(math.pi + math.pi * j / 12) * (r + 0.03), 1.65 + math.sin(math.pi + math.pi * j / 12) * (r + 0.03)) for j in range(13)]
        bar(f"Band{k}", pts, 0.045, K["iron"], seg=4)
        for sy in (-1, 1):
            sphere(f"Rivet{k}{sy}", 0.06, (x, sy * (r + 0.05), 1.6), K["iron"], seg=6, rings=4)
    for sx in (-1, 1):
        box(f"Block{sx}", (1.0, 1.4, 0.95), (sx * 2.4, 0, 0.475), K["wall"], bevel=0.08, segments=2)
    for k in range(4):
        x = rng.uniform(-3, 3)
        s = _mark()
        lathe(f"Fungus{k}", [(0, 0), (0.3, 0.02), (0.32, 0.06), (0.2, 0.1), (0, 0.1)], flat("Bracket", (0.32, 0.22, 0.12), 0.7, dirt=0.8), seg=10, scale=(1, 0.6))
        _xform(s, T(x, -r - 0.02, 1.2 + rng.uniform(-0.2, 0.2)) @ RX(math.pi / 2))
    mound("Moss", 0.9, 0.5, 0.1, K["moss2"], rng, seg=10).matrix_world = T(1.2, -0.2, 1.63)
    return _dims()



def shrub_core(name):
    """The shrub's inside: nearly black green, so gaps between the leaf cards read as depth, not as a surface."""
    return flat(name, (0.006, 0.014, 0.006), 0.9, dirt=0.3)


# ------------------------------------------------------------------ registration

PATHS = {
    "PathFlagstone": lambda M: path_flags(M, "straight", "PathFlagstone"),
    "PathFlagstoneCurve": lambda M: path_flags(M, "curve", "PathFlagstoneCurve"),
    "PathFlagstoneJunction": lambda M: path_flags(M, "junction", "PathFlagstoneJunction"),
    "PathFlagstoneCross": lambda M: path_flags(M, "cross", "PathFlagstoneCross"),
    "PathCobble": lambda M: path_tiled2(M, "cobble", "straight", "PathCobble"),
    "PathCobbleCurve": lambda M: path_tiled2(M, "cobble", "curve", "PathCobbleCurve"),
    "PathGravel": lambda M: path_tiled2(M, "gravel", "straight", "PathGravel"),
    "PathGravelCurve": lambda M: path_tiled2(M, "gravel", "curve", "PathGravelCurve"),
    "PathHerringbone": lambda M: path_tiled2(M, "herring", "straight", "PathHerringbone"),
    "PathCrazyPaving": lambda M: path_flags(M, "straight", "PathCrazyPaving", kind="crazy"),
    "PathPuddleFlag": puddle_flags,
    "PathMoonRoundel": moon_roundel2,
    "SteppingStones": stepping_stones2,
    "GardenSteps": garden_steps2,
    "PathEdgingIron": edging_curls,
    "PathBridgeSlab": bridge_slab,
    "PathGateArch": gate_arch,
}
PLANTS = {
    "RoseBushCrimson": lambda M: rose_bush2(M, False),
    "RoseBushBlack": lambda M: rose_bush2(M, True),
    "HedgeStraight": hedge_lancet,
    "HedgeBattlement": hedge_battlement,
    "HedgeCorner": hedge_corner2,
    "HedgeEnd": hedge_end2,
    "HedgeArchway": hedge_arch2,
    "HedgeWolf": hedge_wolf,
    "HedgeRaven": hedge_raven,
    "WeepingWillow": weeping_willow2,
    "YewTree": yew_tree,
    "GnarledCrabapple": crabapple,
    "CypressPair": cypress_pair,
    "IvyWallPanel": ivy_panel,
    "WisteriaPergola": wisteria_pergola,
    "FernCluster": fern_cluster,
    "LavenderBed": lavender_bed,
    "RaisedFlowerBed": raised_bed,
    "MushroomRing": mushroom_ring,
    "MoonflowerPatch": moonflower_patch,
    "TallGrassClump": tall_grass,
    "ThornBramble": thorn_bramble,
    "NightshadeShrub": nightshade,
    "PumpkinPatch": pumpkin_patch,
    "PoppyBed": poppy_bed,
    "LilyPads": lily_pads,
    "BloodRoseUrn": blood_rose_urn,
    "GhostOrchid": ghost_orchid,
}
FEATURES = {
    "KoiPond": koi_pond,
    "BirdBath": bird_bath,
    "GardenBench": garden_bench,
    "CurvedStoneBench": curved_bench,
    "LogBench": log_bench,
    "IronGazebo": iron_gazebo,
    "RoseArbor": rose_arbor,
    "GardenObelisk": garden_obelisk,
    "UrnPedestal": urn_pedestal,
    "LowGardenWall": low_wall,
    "GardenWallPier": wall_pier,
    "StoneLanternPost": stone_lantern,
    "Wheelbarrow": wheelbarrow,
    "GardenToolsLean": garden_tools,
    "PottingCluster": potting_cluster,
    "ColdFrame": cold_frame,
    "TrellisPanel": trellis_panel,
    "KeepOffGrassSign": keep_off_sign,
    "Birdhouse": birdhouse,
    "Scarecrow": scarecrow,
    "CourtyardBenchTable": bench_table,
    "CrowPerch": crow_perch,
}
BUILDERS = {**PATHS, **PLANTS, **FEATURES}
# the showpieces bake at 2048; everything else at 1024 (bake40.sh reads this)
BIG = set(BUILDERS)          # every prop bakes at 2048 (the owner's standard for batches 34-39)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.05 for n in BUILDERS})
P.PREVIEW_PAD.update({"KeepOffGrassSign": 1.3, "LilyPads": 1.2, "TallGrassClump": 1.2, "PathEdgingIron": 0.9, "Birdhouse": 1.1})
