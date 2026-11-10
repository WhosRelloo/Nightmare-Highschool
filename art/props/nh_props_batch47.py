"""Props batch 47, the witch hut kit (2026-11-10), for nh_props.py: homes phase 2, a crooked, hand-built, mossy witch's hut the
builder places in the woods by the town, inside and out. Weathered oak, wattle and lime daub, mossy fieldstone, reed thatch, hand
forged iron, bone, horn, wax, old bottle glass and patchwork; the witchy glow (sickly green, faint violet) only on the magical
pieces. Rustic and lived-in, not a shop (the spell shop is batch 46). No blood or gore: animal skulls, bones, feathers and
bottles only. Every name and design is invented.

The hut (modular, on an 8-stud grid; see SNAP below and the docs)
  HutFooting   an 8-long rubble footing run (top 1.6) with a crawl vent
  HutPost      a stone pier (to 1.6) and a jowled, crooked oak post (to 12.6) for every corner and every joint between walls
  HutWall, HutWallWindow, HutWallDoor (Door0 swings out)   8 long between post centres, 11 tall, crooked timbers, wattle and daub
  HutGable     the triangle over a 16-wide end wall, with an owl hole and a goat skull under the apex
  HutRoof      an 8-long run of one thatched slope (45 degrees) with its rafters and battens; HutRidge the block-cut ridge roll
  HutChimney   a leaning fieldstone stack for a gable end, iron-banded, a crooked pot
  HutPorch     a plank porch on stone piers with steps, two tree-trunk posts, a mossy shingle lean-to and hanging charms
Inside and around
  WitchCauldron (Glow brew, Glow2 fire), HerbBeamRack (ceiling), WitchJarShelf (wall; Glass, Glow), BroomCorner (corner),
  SpellLectern (Glow sigils, Glow2 candle), BoneChimes (hanging), HearthKettle (wall; Glow2 embers), StrawBed, WitchWorkTable,
  WitchHatStand, CatBasket (Glow eyes), GourdPile, BraidedRug, SpellNoteShelf (wall), ToadstoolRing (Glow), WispLanternPost
  (Glass, Glow)

Pieces: Main, plus _Glow (sickly green or violet; the template colour per prop is in GLOW), _Glow2 (warm fire and candle),
_Glass, _Leaves (alpha-cut cards on batch 40's NH_GardenLeaves, nh_props.ATLAS) and _Door0. Front faces -Y, Z is up, the
origin is at the bottom centre unless SNAP says otherwise. Printed faces come from art/props/witchhut_atlas.py (WitchPrint).
Registered into nh_props.BUILD on import.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _finish
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, prism, _mark, _xform, _dims, flat
from nh_props_batch24 import _text, sweep, _paint, _math, _coords, _mix_rgb
import nh_props_batch24 as B24
import nh_props_batch30 as B30
import nh_props_batch40 as B40
from nh_props_batch40 import Cards, frame, RNG, mk, poly_slab, blob, bar, UP
from nh_props_batch43 import pprism

_tube = P.tube


def tube(name, points, radius, mat, closed=False, res=4, square=False, poly=False):
    """nh_props.tube, but a square bar's faces turned outward (as built its normals point in, so the bake's AO blackens it and
    Roblox would cull its outside)."""
    ob = _tube(name, points, radius, mat, closed=closed, res=res, square=square, poly=poly)
    if square:
        ob.data.flip_normals()
    return ob


DEG = math.pi / 180
PI = math.pi
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
ART = os.path.normpath(os.path.join(P.HERE, "..", "textures"))
FONT_HAND = "C:/Windows/Fonts/Inkfree.ttf"
C45 = math.cos(math.pi / 4)

WA = json.load(open(os.path.join(P.HERE, "witchhut_atlas.json")))
for _k, _v in WA["regions"]["WitchPrint"].items():
    B30.REG["WP_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_WP_" + _k[7:]] = _v

GLOW = {}          # prop -> {piece suffix: (r, g, b)} for the preview (and the template's Neon colours)
UV_WEIGHT = {"Glow": 0.35, "Glow2": 0.35, "Glass": 0.5, "Door0": 1.0}
GREEN = (120, 255, 90)        # the witch's brew and wisp: sickly green
VIOLET = (170, 90, 255)       # spell sigils, crystals
FIRE = (255, 150, 60)         # wood fire, embers, candle flames
CATEYE = (190, 255, 80)

# the hut's grid (studs): walls run 8 between post centres; the floor is 1.6 above the ground; walls are 11 tall
GRID = 8.0
FLOOR = 1.6
WALL_H = 11.0
WALL_T = 0.9
RISE = 8.0                    # the 45-degree roof rises 8 over the 8 from a long wall to the ridge (a 16-wide hut)


# ================================================================== materials

def _noise_s(nt, scale, detail=6.0, coords=None, dist=0.0):
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nz.inputs["Distortion"].default_value = dist
    nt.links.new(coords if coords is not None else _coords(nt), nz.inputs["Vector"])
    return nz.outputs["Fac"]


def cracks(m, scale=1.6, width=0.035, rgb=(0.12, 0.1, 0.08), depth=0.012):
    """Fine dry cracks: Voronoi cell edges, darker and sunk in the bump."""
    nt = m.node_tree
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = scale
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    mask = _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", vo.outputs["Distance"], width), clamp=True)
    _paint(m, mask, rgb, rough=0.95)
    return m, mask


def daub_mat(name="HutDaub", rgb=(0.125, 0.11, 0.09)):
    """Lime daub gone grey-brown with smoke and weather: blotchy, hairline cracks in patches, rain streaks, moss at the foot."""
    m = flat(name, rgb, 0.92, wear=0.25, dirt=1.0)
    nt = m.node_tree
    n1 = _noise_s(nt, 2.2, 8.0)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", n1, 0.5), 3.0, clamp=True), tuple(c * 1.25 for c in rgb), rough=0.9)
    n2 = _noise_s(nt, 0.9, 4.0)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", n2, 0.56), 4.0, clamp=True), (0.09, 0.075, 0.055), rough=0.95)
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 3.5
    nt.links.new(_coords(nt), vo.inputs["Vector"])
    patch = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", _noise_s(nt, 0.6, 3.0), 0.55), 6.0, clamp=True)
    cr = _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", 1.0, _math(nt, "DIVIDE", vo.outputs["Distance"], 0.012), clamp=True), patch)
    _paint(m, cr, (0.05, 0.04, 0.03), rough=0.95)
    B24._bump(m, _math(nt, "SUBTRACT", _noise_s(nt, 9.0, 8.0), _math(nt, "MULTIPLY", cr, 0.7)), 0.03, 0.8)
    B40.streaks(m, 0.45, dark=(0.5, 0.46, 0.42))
    B40.lichen(m, 5.0, 0.05, cols=((0.17, 0.18, 0.14), (0.18, 0.15, 0.08)))
    B40.mossy(m, 0.45, scale=1.1, low=2.6, col=(0.045, 0.07, 0.022))
    return m


def timber_mat(name="HutTimber", tint=(0.075, 0.08, 0.088), moss=0.3):
    m = material(name, "NH_DeskWood", tint=tint, scale=0.55, rough_add=0.18, wear=0.32, dirt=1.15)
    B40.streaks(m, 0.35, dark=(0.55, 0.52, 0.5))
    if moss:
        B40.mossy(m, moss, scale=1.6)
    return m


def thatch_mat(name="HutThatch", rgb=(0.15, 0.12, 0.08)):
    """Old reed thatch: stems combed down the slope (fine streaks across X), patches of gold and grey, moss in the hollows
    and on the faces that look up."""
    m = flat(name, rgb, 0.93, dirt=0.9)
    nt = m.node_tree
    co = _coords(nt)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.08, 0.08)
    nt.links.new(co, mp.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexNoise")
    w.inputs["Scale"].default_value = 60.0
    w.inputs["Detail"].default_value = 3.0
    nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", w.outputs["Fac"], 0.45), 2.0, clamp=True), (0.24, 0.19, 0.11), rough=0.85)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", w.outputs["Fac"], 0.6), 3.0, clamp=True), (0.05, 0.04, 0.03), rough=0.95)
    n2 = _noise_s(nt, 0.7, 5.0)
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", n2, 0.55), 3.0, clamp=True), (0.17, 0.165, 0.15), rough=0.95)
    B24._bump(m, w.outputs["Fac"], 0.05, 0.9)
    B40.mossy(m, 0.4, scale=0.9, col=(0.05, 0.075, 0.025))
    return m


def straw_mat(name="Straw", rgb=(0.42, 0.33, 0.15)):
    m = flat(name, rgb, 0.85, dirt=0.7)
    nt = m.node_tree
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.1)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexNoise")
    w.inputs["Scale"].default_value = 45.0
    w.inputs["Detail"].default_value = 2.0
    nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", w.outputs["Fac"], 0.5), 2.5, clamp=True), tuple(c * 1.45 for c in rgb), rough=0.75)
    B24._bump(m, w.outputs["Fac"], 0.02, 0.8)
    return m


def fur_mat(name="CatFur", rgb=(0.012, 0.011, 0.014)):
    m = flat(name, rgb, 0.7, dirt=0.4)
    nt = m.node_tree
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.25)
    nt.links.new(_coords(nt), mp.inputs["Vector"])
    w = nt.nodes.new("ShaderNodeTexNoise")
    w.inputs["Scale"].default_value = 70.0
    w.inputs["Detail"].default_value = 2.0
    nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
    _paint(m, _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", w.outputs["Fac"], 0.55), 3.0, clamp=True), (0.05, 0.05, 0.065), rough=0.5)
    B24._bump(m, w.outputs["Fac"], 0.01, 0.6)
    return m


def wk(M):
    """The witch hut kit's materials (batch 40's garden set underneath: moss, bark, forged iron, soil, limestone)."""
    K = B40.gk2(M)
    rubble = material("HutRubble", os.path.join(ART, "MossyFlagstone", "MossyFlagstone"), tint=(0.36, 0.35, 0.33), scale=0.16, metal=0.0, wear=0.3,
                      dirt=1.1)
    B40.streaks(rubble, 0.45)
    B40.mossy(rubble, 0.35, scale=1.3, low=1.0)
    K.update({
        "timber": timber_mat(),
        "timberdk": timber_mat("HutTimberDark", (0.04, 0.04, 0.045), 0.2),
        "plank": timber_mat("HutPlank", (0.1, 0.1, 0.1), 0.15),
        "planklt": timber_mat("HutPlankLight", (0.16, 0.15, 0.14), 0.0),
        "sooty": timber_mat("SootyBeam", (0.025, 0.021, 0.019), 0.0),
        "daub": daub_mat(),
        "daubdk": flat("DaubShadow", (0.08, 0.065, 0.05), 0.95),
        "daubpatch": B40.mossy(daub_mat("DaubPatch", (0.2, 0.185, 0.155)), 0.2, scale=2.0),
        "daubold": daub_mat("DaubOld", (0.075, 0.068, 0.055)),
        "wattle": material("Wattle", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.8, 0.7, 0.6), scale=1.6, metal=0.0, normal=1.0, wear=0.3, dirt=1.0),
        "rubble": rubble,
        "field": B40.lichen(B40.mossy(material("FieldStone", "NH_Slate", tint=(0.34, 0.33, 0.3), scale=0.4, rough_mul=0.6, rough_add=0.32, normal=0.8,
                                              wear=0.2, dirt=1.15), 0.4, scale=1.4, low=0.8), 4.0, 0.06, cols=((0.2, 0.21, 0.17), (0.2, 0.17, 0.09))),
        "fielddk": B40.mossy(material("FieldStoneDark", "NH_Slate", tint=(0.2, 0.2, 0.21), scale=0.45, rough_mul=0.6, rough_add=0.3, normal=0.8, wear=0.35,
                                      dirt=1.1), 0.35, scale=1.4),
        "thatch": thatch_mat(),
        "straw": straw_mat(),
        "strawdk": straw_mat("StrawOld", (0.24, 0.19, 0.1)),
        "shingle": B40.lichen(B40.mossy(timber_mat("Shingle", (0.09, 0.08, 0.07), 0.0), 0.6, scale=1.1), 4.0, 0.05, cols=((0.17, 0.18, 0.14), (0.18, 0.15, 0.08))),
        "hazel": material("Hazel", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.75, 0.62, 0.5), scale=2.2, metal=0.0, normal=1.0, wear=0.3, dirt=0.9),
        "pole": material("Pole", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.6, 0.55, 0.5), scale=0.8, metal=0.0, normal=1.0, wear=0.35, dirt=1.0),
        "soot": flat("Soot", (0.015, 0.013, 0.012), 0.95, dirt=0.3),
        "clay": B40.mossy(flat("ClayPot", (0.3, 0.12, 0.06), 0.85, wear=0.35, dirt=1.0), 0.15),
        "crock": flat("Crock", (0.33, 0.27, 0.19), 0.55, wear=0.3, dirt=0.9),
        "crockdk": flat("CrockDark", (0.1, 0.07, 0.05), 0.35, wear=0.3, dirt=0.8),
        "bonew": flat("BleachedBone", (0.62, 0.58, 0.49), 0.65, wear=0.15, dirt=1.0),
        "horn": flat("Horn", (0.16, 0.12, 0.08), 0.45, wear=0.3, dirt=0.8),
        "feather": flat("Feather", (0.02, 0.02, 0.025), 0.55, dirt=0.3),
        "featherb": flat("FeatherBrown", (0.16, 0.1, 0.05), 0.7, dirt=0.4),
        "wax": flat("Beeswax", (0.55, 0.48, 0.33), 0.45, dirt=0.5),
        "waxdk": flat("TallowGrey", (0.42, 0.4, 0.34), 0.55, dirt=0.6),
        "wick": flat("Wick", (0.02, 0.018, 0.015), 0.9),
        "bottle": flat("BottleGlass", (0.06, 0.12, 0.07), 0.12, dirt=0.4),
        "bottleb": flat("BottleBrown", (0.14, 0.06, 0.02), 0.12, dirt=0.4),
        "bottlev": flat("BottleViolet", (0.07, 0.03, 0.1), 0.12, dirt=0.4),
        "cork": material("HutCork", "NH_Limestone", tint=(0.36, 0.22, 0.11), scale=2.5, normal=1.2, rough_add=0.2, wear=0.0, dirt=0.8),
        "twine": flat("Twine", (0.3, 0.24, 0.15), 0.9, dirt=0.5),
        "rope": B24.cloth("HutRope", (0.3, 0.23, 0.13), rough=0.9, weave=0.03),
        "wicker": B24.cloth("HutWicker", (0.27, 0.18, 0.09), rough=0.8, weave=0.04),
        "felt": B24.cloth("HatFelt", (0.025, 0.02, 0.03), rough=0.95, weave=0.004),
        "wool": B24.cloth("Homespun", (0.15, 0.11, 0.08), rough=0.95, weave=0.01),
        "woolg": B24.cloth("HomespunGreen", (0.04, 0.07, 0.04), rough=0.95, weave=0.01),
        "woolv": B24.cloth("HomespunViolet", (0.06, 0.03, 0.08), rough=0.95, weave=0.01),
        "linen": B24.cloth("OldLinen", (0.5, 0.46, 0.38), rough=0.9, weave=0.006),
        "sack": B24.cloth("Sacking", (0.3, 0.24, 0.16), rough=0.95, weave=0.03),
        "leather": B24.leather("HutLeather", (0.12, 0.07, 0.04), scale=3.0, wear=0.35),
        "leatherb": B24.leather("HutLeatherBlack", (0.025, 0.022, 0.02), scale=3.0, wear=0.3),
        "fur": fur_mat(),
        "fleece": B24.cloth("Fleece", (0.5, 0.46, 0.38), rough=0.98, weave=0.025),
        "fleecedk": fur_mat("Sheepskin", (0.26, 0.22, 0.17)),
        "brass": K["brassf"],
        "copper": material("HutCopper", base=(0.4, 0.2, 0.12), rough=0.45, metal=1.0, wear=0.3, dirt=1.1),
        "tin": material("HutTin", base=(0.36, 0.36, 0.35), rough=0.5, metal=0.9, wear=0.3, dirt=1.1),
        "castiron": B40.forged(material("CastIron", "NH_Iron", tint=(0.06, 0.058, 0.06), scale=0.6, rough_add=0.1, wear=0.45, wear_metal=True, dirt=1.2), 0.05),
        "wp": B30.atlas_mat("WitchPrintMat", "WitchPrint", rough=0.78, leather=0.04, wear=0.06, dirt=0.6),
        "pumpkin": B40.mossy(flat("HutPumpkin", (0.27, 0.075, 0.01), 0.55, wear=0.1, dirt=0.9), 0.1, scale=3.0),
        "pumpkinp": flat("GhostPumpkin", (0.5, 0.47, 0.4), 0.6, wear=0.1, dirt=0.75),
        "gourdg": flat("GourdGreen", (0.07, 0.12, 0.04), 0.4, wear=0.1, dirt=0.7),
        "gourdy": flat("GourdYellow", (0.42, 0.3, 0.06), 0.4, wear=0.1, dirt=0.7),
        "gourdb": flat("GourdBottle", (0.32, 0.22, 0.11), 0.6, wear=0.1, dirt=0.8),
        "stalk": flat("GourdStalk", (0.1, 0.1, 0.05), 0.8),
        "toadred": flat("ToadstoolRed", (0.25, 0.015, 0.01), 0.45, dirt=0.6),
        "toadspot": flat("ToadstoolSpot", (0.66, 0.62, 0.52), 0.7, dirt=0.4),
        "toadstem": flat("ToadstoolStem", (0.58, 0.54, 0.45), 0.75, dirt=0.8),
        "toadv": flat("ToadstoolViolet", (0.08, 0.03, 0.12), 0.5, dirt=0.6),
        "glow": flat("WitchGlow", (0.2, 1.0, 0.2), 0.5),
        "glow2": flat("FireGlow", (1.0, 0.55, 0.2), 0.5),
        "ember": flat("Ember", (0.08, 0.02, 0.01), 0.9, dirt=0.3),
        "ash": flat("Ash", (0.2, 0.19, 0.18), 0.95, dirt=0.4),
        "brew": flat("BrewDark", (0.02, 0.06, 0.02), 0.1),
        "herbg": flat("DriedHerb", (0.1, 0.11, 0.05), 0.8, dirt=0.5),
        "herbb": flat("DriedHerbBrown", (0.15, 0.09, 0.04), 0.8, dirt=0.5),
        "lav": flat("DriedLavender", (0.12, 0.08, 0.17), 0.8, dirt=0.5),
        "garlic": flat("Garlic", (0.58, 0.53, 0.45), 0.6, dirt=0.6),
        "chilli": flat("Chilli", (0.25, 0.03, 0.015), 0.45, dirt=0.6),
        "mush": flat("DriedMushroom", (0.22, 0.15, 0.09), 0.75, dirt=0.6),
        "rootw": material("HutRoot", os.path.join(P.OUT_TEX, "NH_GardenBark"), tint=(0.7, 0.58, 0.48), scale=1.6, metal=0.0, normal=1.0, wear=0.3, dirt=1.0),
        "crystalv": flat("CrystalViolet", (0.12, 0.05, 0.22), 0.1, dirt=0.3),
        "paper": flat("HutPaper", (0.56, 0.5, 0.38), 0.85, dirt=0.6),
        "web": flat("HutCobweb", (0.6, 0.6, 0.58), 0.9, dirt=0.1),
        "toadskin": B40.mossy(flat("ToadSkin", (0.09, 0.08, 0.035), 0.55, dirt=0.8), 0.2, scale=8.0),
        "toadskin2": flat("ToadWart", (0.16, 0.12, 0.05), 0.5, dirt=0.6),
        "toadeye": flat("ToadEye", (0.5, 0.33, 0.05), 0.15, dirt=0.3),
        "socket": flat("SocketShadow", (0.012, 0.009, 0.007), 0.9),
    })
    return K


# ================================================================== helpers

def smooth_noise(seed, n=5, period=None):
    """A smooth 1-D noise f(t) in about -1..1 (a few seeded sines); with `period` it repeats every `period`."""
    g = random.Random(seed)
    terms = []
    for k in range(n):
        if period:
            f = 2 * PI * (k + 1) / period
        else:
            f = g.uniform(0.6, 3.5) * (k + 1) * 0.7
        terms.append((f, g.uniform(0, 2 * PI), g.uniform(0.4, 1.0) / (k + 1)))
    s = sum(a for _, _, a in terms)
    return lambda t: sum(a * math.sin(f * t + p) for f, p, a in terms) / s


def noise2(seed, px=None, pz=None, n=4):
    """A smooth 2-D noise f(x, z) in about -1..1 (sums of seeded sine products); periodic in x with px (and z with pz)."""
    g = random.Random(seed)
    terms = []
    for k in range(n):
        fx = 2 * PI * (k + 1) / px if px else g.uniform(0.8, 3.0) * (k + 1) * 0.6
        fz = 2 * PI * g.randint(1, 3) / pz if pz else g.uniform(0.8, 3.0) * (k + 1) * 0.6
        terms.append((fx, fz, g.uniform(0, 2 * PI), g.uniform(0, 2 * PI), 1.0 / (k + 1)))
    s = sum(t[4] for t in terms)
    return lambda x, z: sum(a * math.sin(fx * x + p) * math.cos(fz * z + q) for fx, fz, p, q, a in terms) / s


def hewn(name, p0, p1, w, h, mat, bow=(0, 0, 0), seed=0, n=None, jit=0.025, cham=0.07, up=(0, 0, 1), taper=0.0, ends=True):
    """A hand-hewn timber from p0 to p1: a w x h section with chamfered corners (eight sides), bowed by `bow` at its middle,
    its faces wandering a little (adze work); the ends cut square."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    d = (p1 - p0) / L
    side = d.cross(Vector(up))
    if side.length < 1e-4:
        side = d.orthogonal()
    side.normalize()
    upv = side.cross(d).normalized()
    n = n or max(2, int(L / 0.5))
    g = random.Random(seed)
    fs, fu = smooth_noise(seed * 3 + 1), smooth_noise(seed * 3 + 2)
    a0, b0 = w / 2, h / 2
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        t = i / n
        c = p0 + (p1 - p0) * t + Vector(bow) * math.sin(PI * t)
        k = 1 - taper * t
        a, b, ch = a0 * k, b0 * k, cham * k
        sec = [(a - ch, b), (a, b - ch), (a, -b + ch), (a - ch, -b), (-a + ch, -b), (-a, -b + ch), (-a, b - ch), (-a + ch, b)]
        ws, wu = fs(t * L) * jit * 2, fu(t * L) * jit * 2
        ring = []
        for x, y in sec:
            jj = g.uniform(-jit, jit) * 0.6 if 0 < i < n else 0.0
            ring.append(bm.verts.new(c + side * (x + ws + jj) + upv * (y + wu + jj)))
        rings.append(ring)
    for A, Bv in zip(rings, rings[1:]):
        for k in range(8):
            j = (k + 1) % 8
            bm.faces.new((A[k], A[j], Bv[j], Bv[k]))
    if ends:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return _finish(ob, mat, 0)


def pole(name, pts, r, mat, seed=0, seg=8, knob=0.08, taper=0.15, caps=True):
    """A crooked round pole along pts: its radius swells and pinches (knots) and tapers a little toward the end."""
    f = smooth_noise(seed, 4)
    return sweep(name, pts, lambda t: r * (1 - taper * t) * (1 + knob * f(t * 9.0)), mat, seg=seg, caps=caps)


def crooked(p0, p1, amt, seed, n=6, perp=None):
    """Points from p0 to p1 wandering sideways by up to `amt` (a branch, a crooked stick)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    a = d.orthogonal().normalized() if perp is None else Vector(perp).normalized()
    b = d.normalized().cross(a)
    fa, fb = smooth_noise(seed, 3), smooth_noise(seed + 99, 3)
    out = []
    for i in range(n + 1):
        t = i / n
        w = math.sin(PI * t)
        out.append(tuple(p0 + d * t + (a * fa(t * 4) + b * fb(t * 4)) * amt * w))
    return out


def rock(name, c, size, mat, rng, rot=None, jit=0.18, bevel=0.06, cuts=1):
    """A rough stone: a cube cut once each way, its points pushed about, scaled to `size` (w, d, h), bevelled."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        v.co = Vector((v.co.x * (1 + rng.uniform(-jit, jit)), v.co.y * (1 + rng.uniform(-jit, jit)), v.co.z * (1 + rng.uniform(-jit, jit))))
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    r = rot if rot is not None else (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), rng.uniform(-0.3, 0.3))
    ob.matrix_world = T(*c) @ RZ(r[2]) @ RY(r[1]) @ RX(r[0])
    _finish(ob, mat, bevel * min(size), segments=1)
    return ob


def grid_slab(name, x0, x1, z0, z1, y0, y1, mat, disp=None, res=0.4, sides=True):
    """A slab from x0..x1, z0..z1 between the planes y0 (front, looks -Y) and y1 (back, looks +Y); disp(x, z, side) pushes
    each face out (side -1 front, +1 back) so a daub panel bulges and dips like hand-laid plaster."""
    nx = max(1, int(round((x1 - x0) / res)))
    nz = max(1, int(round((z1 - z0) / res)))
    V, F = [], []
    idx = {}
    for s, yb in ((-1, y0), (1, y1)):
        for i in range(nx + 1):
            for j in range(nz + 1):
                x = x0 + (x1 - x0) * i / nx
                z = z0 + (z1 - z0) * j / nz
                edge = i in (0, nx) or j in (0, nz)
                dy = 0.0 if (disp is None or edge) else disp(x, z, s)
                idx[(s, i, j)] = len(V)
                V.append((x, yb + s * dy, z))
    for s in (-1, 1):
        for i in range(nx):
            for j in range(nz):
                a, b, c, d = idx[(s, i, j)], idx[(s, i + 1, j)], idx[(s, i + 1, j + 1)], idx[(s, i, j + 1)]
                F.append((a, b, c, d) if s == -1 else (d, c, b, a))
    if sides:
        loop = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(nz)] + [(i, nz) for i in range(nx, 0, -1)] + [(0, j) for j in range(nz, 0, -1)]
        for k in range(len(loop)):
            p, q = loop[k], loop[(k + 1) % len(loop)]
            F.append((idx[(-1,) + p], idx[(1,) + p], idx[(1,) + q], idx[(-1,) + q]))
    ob = mk(name, V, F, mat, smooth=True)
    B40.P_recalc(ob)
    return ob


def daub_panel(name, x0, x1, z0, z1, K, seed, t=0.66, y=0.0):
    """A wattle-and-daub panel between timbers: lime daub laid by hand (pillowed toward its middle, lumpy), t thick."""
    f = noise2(seed)

    def disp(x, z, s):
        u = (x - x0) / (x1 - x0)
        v = (z - z0) / (z1 - z0)
        pillow = math.sin(PI * u) ** 0.6 * math.sin(PI * v) ** 0.6
        return 0.05 * pillow + 0.025 * f(x * 1.7 + s * 3.1, z * 1.7)
    return grid_slab(name, x0, x1, z0, z1, y - t / 2, y + t / 2, K["daub"], disp, res=0.45)


def wattle_patch(prefix, cx, cz, rw, rh, yface, side, K, rng):
    """A place where the daub has fallen away: a ragged rim of daub round woven hazel rods on upright stakes, the dark
    daub core behind. side -1 shows on the front (-Y) face at y = yface, +1 on the back."""
    s = side
    out = [(cx + math.cos(a) * rw * (1 + 0.15 * math.sin(a * 3 + cx)), cz + math.sin(a) * rh * (1 + 0.15 * math.cos(a * 2 + cz)))
           for a in [i / 14 * 2 * PI for i in range(14)]]
    prism(f"{prefix}Core", out, yface + s * 0.07, 0.04, K["daubdk"], plane="XZ")
    xs = [cx + (k - 2) * rw * 0.42 for k in range(5)]
    for k, x in enumerate(xs):
        hh = rh * math.sqrt(max(0.05, 1 - ((x - cx) / rw) ** 2)) * 0.95
        pole(f"{prefix}Stake{k}", [(x, yface + s * 0.12, cz - hh), (x, yface + s * 0.12, cz + hh)], 0.045, K["hazel"], seed=k, seg=6)
    nrod = max(2, int(rh * 2 / 0.13))
    for j in range(nrod):
        z = cz - rh * 0.88 + j * rh * 1.76 / (nrod - 1)
        half = rw * math.sqrt(max(0.05, 1 - ((z - cz) / rh) ** 2)) * 0.95
        pts = []
        m = 10
        for i in range(m + 1):
            x = cx - half + 2 * half * i / m
            ph = (x - xs[0]) / (rw * 0.42) * PI + j * PI
            pts.append((x, yface + s * (0.12 + 0.04 * math.cos(ph)), z))
        bar(f"{prefix}Rod{j}", pts, 0.032, K["hazel"], seg=5)
    rim = [(x, yface + s * 0.1, z) for x, z in out] + [(out[0][0], yface + s * 0.1, out[0][1])]
    bar(f"{prefix}Rim", rim, lambda t: 0.06 + 0.025 * math.sin(t * 37), K["daub"], seg=6)


def ivy(cards, rng, pts, side=(0, -1, 0), n=10, size=0.9):
    """Ivy cards hugging a surface along a path (facing `side`)."""
    nrm = Vector(side).normalized()
    pts = [Vector(p) for p in pts]
    for k in range(n):
        t = rng.uniform(0, 1) * (len(pts) - 1)
        i = min(int(t), len(pts) - 2)
        p = pts[i].lerp(pts[i + 1], t - i)
        ax, ay = frame(nrm, roll=rng.uniform(0, 6.28))
        s = size * rng.uniform(0.75, 1.2)
        cards.add(p + nrm * 0.05, ax, ay, s, s, "ivy", "fill", nrm=nrm)


def uv_planar(ob, key, axes=(0, 1), flip=(False, False), k=2.0, bounds=None):
    """Give a part a "Spine" UV that lays the WitchPrint region `key` over its extent along two of its world axes (for a
    quilt from above, a rug, a page), and a bake-room weight k (nh_uvk)."""
    me = ob.data
    mw = ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    if bounds is None:
        a0, a1 = min(p[axes[0]] for p in pts), max(p[axes[0]] for p in pts)
        b0, b1 = min(p[axes[1]] for p in pts), max(p[axes[1]] for p in pts)
    else:
        a0, a1, b0, b1 = bounds
    u0, v0, u1, v1 = B30.REG["WP_" + key]
    uv = me.uv_layers.get("Spine") or me.uv_layers.new(name="Spine")
    for li, lp in enumerate(me.loops):
        p = pts[lp.vertex_index]
        fu = (p[axes[0]] - a0) / max(1e-6, a1 - a0)
        fv = (p[axes[1]] - b0) / max(1e-6, b1 - b0)
        if flip[0]:
            fu = 1 - fu
        if flip[1]:
            fv = 1 - fv
        uv.data[li].uv = (u0 + fu * (u1 - u0), v0 + fv * (v1 - v0))
    B30.uvk(ob, k)
    return ob


def swatch_uv(ob, name="parch"):
    """A part in the atlas material that only needs one flat swatch colour (all its loops on the swatch's centre)."""
    me = ob.data
    uv = me.uv_layers.get("Spine") or me.uv_layers.new(name="Spine")
    pt = B30._swatch("WP_" + name)
    for d in uv.data:
        d.uv = pt
    B30.uvk(ob, 0.4)
    return ob


def label_tag(name, key, w, h, mtx, K, t=0.012):
    """A parchment label (a WitchPrint region on its front face, parchment edges)."""
    return pprism(name, "WP_" + key, [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], t, mtx, K["wp"], edge="WP_parch", k=2.2)


def candle(prefix, x, y, z, r, h, K, drips=4, rng=None, flame=True, mat=None):
    """A fat candle with wax runs down its sides and a pool at its foot; the flame (Glow2) above the wick."""
    rng = rng or random.Random(int(x * 100 + y * 10))
    m = mat or K["wax"]
    top = [(0, 0), (r * 1.25, 0), (r * 1.3, 0.03), (r * 1.05, 0.05), (r, 0.08), (r * 1.01, h * 0.7), (r * 0.97, h - 0.03), (r * 0.82, h),
           (r * 0.5, h - 0.04), (0, h - 0.05)]
    lathe(f"{prefix}Wax", top, m, seg=14, loc=(x, y, z), jitter=(0.04, int(x * 77) % 1000))
    for k in range(drips):
        a = rng.uniform(0, 2 * PI)
        L = rng.uniform(0.3, 0.8) * h
        pts = [(x + math.cos(a) * r * 0.98, y + math.sin(a) * r * 0.98, z + h - 0.02 - L * t) for t in (0, 0.5, 1.0)]
        bar(f"{prefix}Drip{k}", pts, lambda t: r * 0.12 * (1 - 0.5 * t) + 0.008, m, seg=5)
    cyl(f"{prefix}Wick", r * 0.06, 0.08, (x, y, z + h), K["wick"], verts=5, bevel=0.0)
    if flame:
        g = P.GROUP
        set_group("Glow2")
        lathe(f"{prefix}Flame", [(0, 0), (r * 0.22, r * 0.25), (r * 0.25, r * 0.6), (r * 0.12, r * 1.05), (0, r * 1.35)], K["glow2"], seg=8,
              loc=(x, y, z + h + 0.03))
        set_group(g)


def bottle(prefix, x, y, z, r, h, mat, K, shape=0, cork=True, rot=None):
    """A hand-blown bottle: round, squat, long-necked or square-shouldered (shape 0-3), corked."""
    if shape == 0:
        prof = [(0, 0), (r * 0.9, 0), (r, 0.06 * h), (r, 0.55 * h), (r * 0.85, 0.68 * h), (r * 0.32, 0.8 * h), (r * 0.3, 0.95 * h), (r * 0.36, h), (0, h)]
    elif shape == 1:
        prof = [(0, 0), (r * 0.8, 0), (r * 1.15, 0.25 * h), (r * 1.1, 0.45 * h), (r * 0.6, 0.6 * h), (r * 0.28, 0.72 * h), (r * 0.26, 0.95 * h), (r * 0.33, h),
                (0, h)]
    elif shape == 2:
        prof = [(0, 0), (r * 0.85, 0), (r, 0.12 * h), (r * 0.95, 0.35 * h), (r * 0.4, 0.45 * h), (r * 0.18, 0.5 * h), (r * 0.17, 0.95 * h), (r * 0.24, h),
                (0, h)]
    else:
        prof = [(0, 0), (r, 0), (r, 0.7 * h), (r * 0.5, 0.78 * h), (r * 0.34, 0.82 * h), (r * 0.32, 0.96 * h), (r * 0.38, h), (0, h)]
    s = _mark()
    lathe(f"{prefix}Bottle", prof, mat, seg=12 if shape != 3 else 4)
    if cork:
        ck = prof[-2][0] * 0.92
        cyl(f"{prefix}Cork", ck, 0.12 * h + 0.04, (0, 0, h + 0.02), K["cork"], verts=8, bevel=0.01)
    _xform(s, T(x, y, z) @ (rot or Matrix.Identity(4)))


def jar(prefix, x, y, z, r, h, K, fill, fill_k=0.7, lid="cork", rng=None):
    """A wide hand-blown jar (Glass) with its contents inside (Main) and a cork, cloth or wax lid."""
    g = P.GROUP
    lathe(f"{prefix}Fill", [(0, 0.02), (r * 0.88, 0.02), (r * 0.9, h * fill_k), (r * 0.5, h * fill_k + 0.03), (0, h * fill_k + 0.04)], fill, seg=12,
          loc=(x, y, z))
    set_group("Glass")
    lathe(f"{prefix}Jar", [(0, 0), (r * 0.95, 0), (r, 0.05), (r, h * 0.86), (r * 0.86, h * 0.94), (r * 0.8, h), (r * 0.84, h + 0.02), (r * 0.7, h + 0.02),
                           (r * 0.75, h * 0.9), (r * 0.92, h * 0.85), (r * 0.92, 0.06), (0, 0.06)], K["glass"], seg=14, loc=(x, y, z))
    set_group(g)
    if lid == "cork":
        cyl(f"{prefix}Cork", r * 0.76, 0.16, (x, y, z + h + 0.03), K["cork"], verts=12, bevel=0.02)
    elif lid == "cloth":
        lathe(f"{prefix}Cloth", [(0, h + 0.06), (r * 0.9, h + 0.03), (r * 1.02, h - 0.05), (r * 1.08, h - 0.22), (r * 1.02, h - 0.2), (r * 0.86, h - 0.02),
                                 (0, h + 0.01)], K["linen"], seg=14, loc=(x, y, z), jitter=(0.06, int(x * 31) % 999))
        hoop(f"{prefix}Tie", (x, y, z + h - 0.08), r * 0.95, "Z", K["twine"], thick=0.012)
    else:
        lathe(f"{prefix}Wax", [(0, h + 0.07), (r * 0.82, h + 0.05), (r * 0.9, h - 0.04), (r * 0.86, h - 0.1), (r * 0.78, h - 0.03), (0, h + 0.02)], K["wax"],
              seg=12, loc=(x, y, z))


def skull_small(prefix, mtx, K, s=1.0, horns=False):
    """A small animal skull (a fox or a goat): a cranium, a long muzzle, dark sockets, a jaw; curled horns for the goat."""
    st = _mark()
    bone = K["bonew"]
    blob(f"{prefix}Cran", (0, 0, 0), 0.32 * s, bone, seg=12, rings=8, scale=(0.9, 1.0, 0.8))
    lathe(f"{prefix}Muzzle", [(0, 0), (0.17 * s, 0.0), (0.14 * s, 0.25 * s), (0.08 * s, 0.5 * s), (0.04 * s, 0.56 * s), (0, 0.57 * s)], bone, seg=10,
          scale=(1.0, 0.75))
    P.PARTS[-1].matrix_world = T(0, -0.18 * s, -0.08 * s) @ RX(PI / 2 + 0.25)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.075 * s, (sx * 0.15 * s, -0.22 * s, 0.03 * s), K["socket"], seg=8, rings=5, scale=(1, 0.6, 0.85))
        box(f"{prefix}Cheek{sx}", (0.05 * s, 0.3 * s, 0.06 * s), (sx * 0.2 * s, -0.25 * s, -0.12 * s), bone, bevel=0.015 * s)
        if horns:
            pts = []
            for i in range(14):
                t = i / 13
                a = t * 1.5 * PI
                rr = 0.28 * s * (1 - t * 0.45)
                pts.append((sx * (0.2 * s + 0.1 * s * t + rr * 0.6 * math.sin(a) * 0.5 + 0.18 * s * t), 0.05 * s + rr * math.cos(a) - 0.28 * s * 0.2,
                            0.2 * s + rr * math.sin(a)))
            bar(f"{prefix}Horn{sx}", pts, lambda t: 0.085 * s * (1 - t * 0.85) + 0.01, K["horn"], seg=8)
    box(f"{prefix}Jaw", (0.18 * s, 0.42 * s, 0.05 * s), (0, -0.4 * s, -0.24 * s), bone, bevel=0.02 * s, rot=(0.25, 0, 0))
    for k in range(5):
        box(f"{prefix}Tooth{k}", (0.025 * s, 0.025 * s, 0.05 * s), ((k - 2) * 0.03 * s, -0.66 * s, -0.17 * s), bone, bevel=0.0)
    _xform(st, mtx)


def feather(prefix, base, direction, L, K, mat=None, w=0.07, curl=0.15):
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    pts = [Vector(base) + d * L * t + side * curl * L * t * t for t in (0, 0.33, 0.66, 1.0)]
    strip(f"{prefix}Vane", [tuple(p) for p in pts], w, tuple(side.cross(d)), mat or K["feather"], thick=0.008, it=2)
    bar(f"{prefix}Quill", [tuple(pts[0] - d * 0.08), tuple(pts[-1])], lambda t: 0.008 * (1 - t) + 0.002, K["bonew"], seg=4)


def string(name, a, b, K, sag=0.0, r=0.012, mat=None):
    a, b = Vector(a), Vector(b)
    pts = [tuple(a.lerp(b, t) - Vector((0, 0, sag * math.sin(PI * t)))) for t in (0, 0.25, 0.5, 0.75, 1.0)]
    return bar(name, pts, r, mat or K["twine"], seg=4)


def leaves_done(name, cards):
    if cards.build("Leaves"):
        P.ATLAS[f"{name}_Leaves"] = "NH_GardenLeaves"


def ground_at_zero(s=0):
    bpy.context.view_layer.update()
    lo = min((ob.matrix_world @ Vector(c)).z for ob in P.PARTS[s:] for c in ob.bound_box)
    _xform(s, T(0, 0, -lo))


def cobweb(prefix, c, a, b, L, K, n=6, rings=3):
    """A corner cobweb: threads fanning from the corner c between the directions a and b (L long), and sagging cross strands."""
    c, a, b = Vector(c), Vector(a).normalized(), Vector(b).normalized()
    spokes = []
    for i in range(n):
        t = i / (n - 1)
        d = (a * (1 - t) + b * t).normalized()
        spokes.append(d)
        bar(f"{prefix}Sp{i}", [tuple(c), tuple(c + d * L)], 0.005, K["web"], seg=3)
    for r in range(1, rings + 1):
        k = r / (rings + 0.6)
        pts = []
        for i, d in enumerate(spokes):
            pts.append(tuple(c + d * L * k * (0.92 if i % 2 else 1.0) - Vector((0, 0, 0.03 * k))))
        bar(f"{prefix}Ring{r}", pts, 0.004, K["web"], seg=3, caps=False)


# ================================================================== the hut shell

def wall_frame(K, seed, studs, rails, brace=None, sole=((-4.0, 4.0),)):
    """The timbers of a wall: sole plate(s), a straight wall plate (top at 11.0), crooked studs [(x_bottom, x_top[, z0, z1])],
    rails [(x0, x1, z0, z1)] and a curved brace (x0, z0, x1, z1, bow)."""
    for k, (a, b) in enumerate(sole):
        hewn(f"Sole{k}", (a, 0, 0.3), (b, 0, 0.3), WALL_T, 0.6, K["timber"], bow=(0, 0.05, 0.0), seed=seed + k, jit=0.02)
    hewn("Plate", (-4.0, 0, WALL_H - 0.3), (4.0, 0, WALL_H - 0.3), WALL_T, 0.6, K["timber"], bow=(0, -0.05, 0.0), seed=seed + 7, jit=0.012)
    for k, st in enumerate(studs):
        xb, xt = st[0], st[1]
        z0, z1 = (st[2], st[3]) if len(st) > 2 else (0.55, WALL_H - 0.55)
        hewn(f"Stud{k}", (xb, 0, z0), (xt, 0, z1), 0.55, WALL_T, K["timber"], bow=(0.28 * (1 if k % 2 else -1), -0.06, 0), seed=seed + 11 + k, up=(0, 1, 0))
    for k, (x0, x1, z0, z1) in enumerate(rails):
        hewn(f"Rail{k}", (x0, 0, z0), (x1, 0, z1), WALL_T, 0.45, K["timber"], bow=(0, 0, -0.16), seed=seed + 21 + k, jit=0.03)
    if brace:
        x0, z0, x1, z1, bw = brace
        d = Vector((x1 - x0, 0, z1 - z0)).normalized()
        nrm = Vector((-d.z, 0, d.x))
        hewn("Brace", (x0, 0, z0), (x1, 0, z1), 0.45, WALL_T, K["timber"], bow=tuple(nrm * bw), seed=seed + 31, up=(0, 1, 0), n=10)


def shutter(prefix, mtx, sig, K):
    st = _mark()
    for k in range(3):
        box(f"{prefix}Plank{k}", (0.44, 0.1, 3.3 - k * 0.07), (-0.46 + k * 0.46, 0, 1.65 - k * 0.03), K["plank"], bevel=0.02)
    for z in (0.5, 2.8):
        box(f"{prefix}Ledge{z}", (1.36, 0.08, 0.24), (0, 0.08, z), K["planklt"], bevel=0.02)
        tube(f"{prefix}Strap{z}", [(0.68, -0.07, z), (-0.6, -0.07, z)], 0.025, K["iron"], square=True, poly=True)
    pprism(f"{prefix}Sigil", "WP_" + sig, [(-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)], 0.01, T(0, -0.055, 1.75), K["wp"], edge="WP_wood")
    _xform(st, mtx)


def witchify(K, rng, kind, st0, cards):
    """What makes a cottage wall a witch's: a course of mossy fieldstones along its foot, patched and cracked daub (fresh lime
    patches, a dark old patch, cracks running from the corners of the panels), a bone or a skull on a nail, moss climbing from
    the base; then the whole wall bellies out and sags (the posts, plate and sole stay true, so it still snaps to the grid)."""
    g = random.Random({"plain": 1, "window": 2, "door": 3}[kind] + 4790)
    skip = {"plain": (), "window": (), "door": ((-2.6, 2.6),)}[kind]
    x = -3.65
    k = 0
    while x < 3.6:                      # the foot course
        w = g.uniform(0.55, 1.0)
        cx = x + w / 2
        if not any(a < cx < b for a, b in skip):
            rock(f"Foot{k}", (cx, -0.5, 0.45 + g.uniform(-0.06, 0.06)), (w * 0.95, 0.38, g.uniform(0.55, 0.75)), K["field"] if k % 3 else K["fielddk"], rng,
                 bevel=0.14)
            if k % 2 == 0:
                sphere(f"FootMoss{k}", g.uniform(0.18, 0.3), (cx + g.uniform(-0.2, 0.2), -0.62, 0.78), K["moss2"], seg=8, rings=5, scale=(1.4, 0.7, 0.45))
        x += w
        k += 1
    spots = {"plain": [(-2.6, 4.2, 0.8, 0.55, "daubpatch"), (0.3, 8.6, 0.7, 0.9, "daubold"), (3.0, 3.0, 0.55, 0.45, "daubpatch")],
             "window": [(-3.0, 8.4, 0.6, 0.7, "daubpatch"), (2.9, 8.8, 0.55, 0.5, "daubold"), (3.0, 2.2, 0.5, 0.55, "daubpatch")],
             "door": [(-3.2, 2.4, 0.45, 0.6, "daubpatch"), (-3.1, 8.9, 0.45, 0.55, "daubold"), (0.9, 9.4, 0.8, 0.5, "daubpatch")]}[kind]
    for k, (cx, cz, rw, rh, m) in enumerate(spots):        # patches
        out = [(cx + math.cos(a) * rw * (1 + 0.2 * math.sin(a * 3 + k)), cz + math.sin(a) * rh * (1 + 0.18 * math.cos(a * 2 + k))) for a in [i / 14 * 2 * PI for i in range(14)]]
        prism(f"Patch{k}", out, -0.4, 0.06, K[m], plane="XZ", bevel=0.02)
    cracks_at = {"plain": [(-1.3, 6.4), (1.9, 5.8), (-3.9, 9.5)], "window": [(-1.4, 7.3), (1.5, 3.3), (1.5, 7.2)], "door": [(-2.1, 7.6), (2.1, 7.4), (2.5, 4.8)]}[kind]
    for k, (x0, z0) in enumerate(cracks_at):               # cracks running out from the timbers
        p = Vector((x0, -0.42, z0))
        d = Vector((g.choice((-1, 1)) * 0.7, 0, g.uniform(-0.8, 0.8))).normalized()
        pts = [tuple(p)]
        for i in range(6):
            d = (d + Vector((g.uniform(-0.5, 0.5), 0, g.uniform(-0.5, 0.5)))).normalized()
            p = p + d * g.uniform(0.2, 0.35)
            p.x = max(-3.85, min(3.85, p.x))
            pts.append(tuple(p))
            if i == 2:
                q = p + Vector((g.uniform(-0.3, 0.3), 0, g.uniform(-0.4, 0.4)))
                bar(f"CrackB{k}", [tuple(p), tuple(q)], lambda t: 0.018 * (1 - t), K["soot"], seg=4)
        bar(f"Crack{k}", pts, lambda t: 0.026 * (1 - 0.8 * t), K["soot"], seg=4)
    if kind == "plain":          # a fox skull on a nail, and a string of small bones
        skull_small("NailSkull", T(2.9, -0.78, 7.6) @ RX(-0.2), K, s=0.55)
        sphere("Nail", 0.05, (2.9, -0.5, 7.9), K["iron"], seg=6, rings=3)
    elif kind == "window":
        string("BoneStr", (2.15, -0.55, 7.1), (2.15, -0.6, 5.1), K, r=0.012)
        for j in range(4):
            pole(f"Bone{j}", [(2.15, -0.6, 6.7 - j * 0.45), (2.15, -0.6, 6.4 - j * 0.45)], 0.035, K["bonew"], seed=j, seg=6, knob=0.0)
            for zz in (6.7 - j * 0.45, 6.4 - j * 0.45):
                sphere(f"BoneK{j}{zz:.2f}", 0.05, (2.15, -0.6, zz), K["bonew"], seg=6, rings=4, scale=(1, 0.8, 0.8))
    else:
        skull_small("BirdSkull", T(3.15, -0.62, 6.9) @ RZ(0.2), K, s=0.4)
        for j in range(3):
            feather(f"SkF{j}", (3.15 + (j - 1) * 0.05, -0.6, 6.75), (0.2 * (j - 1), -0.1, -1), 0.6, K, w=0.07, mat=K["feather"] if j != 1 else K["featherb"])
    for k in range(4):           # moss creeping up from the foot
        cards.crossed((-3.3 + k * 2.1 + g.uniform(-0.3, 0.3), -0.75, 0.0), 0.7, 0.7, "grass", k=2)

    def belly(x):
        if kind == "door":
            return math.sin(PI * (abs(x) - 2.6) / 1.4) if 2.6 < abs(x) < 4.0 else 0.0
        if kind == "window":
            return math.sin(PI * (abs(x) - 2.0) / 2.0) if 2.0 < abs(x) < 4.0 else 0.0
        return math.sin(PI * (x + 4.0) / 8.0) if -4.0 < x < 4.0 else 0.0
    bpy.context.view_layer.update()
    for ob in P.PARTS[st0:]:
        if ob.get("nh_group") != "Main" or ob.type != "MESH" or ob.name.startswith(("Plate", "Sole")):
            continue
        mw = ob.matrix_world
        mi = mw.inverted()
        for v in ob.data.vertices:
            w = mw @ v.co
            z = max(0.0, min(WALL_H, w.z))
            f = belly(w.x) * math.sin(PI * z / WALL_H) ** 1.3
            w.y -= 0.17 * f
            w.z -= 0.08 * f * (z / WALL_H)          # and it sags
            v.co = mi @ w


def hut_wall(M, kind="plain"):
    """An 8-long wattle-and-daub wall between two post centres (x = -4..4, the ends tuck into HutPost), 11 tall to the top of
    its wall plate, 0.9 thick, centred on y = 0 with the outside to -Y; pivot at the floor. Crooked studs and rails, a curved
    brace, pillowed daub with places where it has fallen off the wattle."""
    K = wk(M)
    rng = RNG({"plain": 4701, "window": 4702, "door": 4703}[kind])
    g = random.Random(4710 + len(kind))
    cards = Cards(rng)
    st0 = _mark()
    zb, zt = 0.55, WALL_H - 0.55
    if kind == "plain":
        s1, s2 = (-1.5, -1.3), (1.8, 2.05)
        wall_frame(K, 10, [s1, s2], [(-4.0, s1[0] + 0.1, 5.6, 5.9), (s1[0], s2[0], 6.4, 6.1), (s2[0], 4.0, 5.7, 5.8)], brace=(-3.65, 0.6, -1.45, 4.8, 0.35))
        for k, (x0, x1) in enumerate(((-4.0, -1.4), (-1.4, 1.93), (1.93, 4.0))):
            daub_panel(f"Daub{k}", x0, x1, zb, zt, K, 100 + k)
        wattle_patch("WatA", -2.6, 8.3, 0.55, 0.7, -0.36, -1, K, rng)
        wattle_patch("WatB", 0.4, 2.4, 0.5, 0.45, 0.36, 1, K, rng)
        for k, x in enumerate((-0.6, 0.35, 1.3)):          # inside: three pegs for the witch's things
            pole(f"Peg{k}", [(x, 0.33, 7.4), (x, 0.75, 7.48), (x, 0.82, 7.56)], 0.07, K["plank"], seed=k, seg=6)
        ivy(cards, rng, [(3.6, -0.47, 0.3), (3.2, -0.47, 2.5), (3.5, -0.47, 4.2), (3.0, -0.47, 5.6)], n=16, size=0.8)
    elif kind == "window":
        wx0, wx1, wz0, wz1 = -1.35, 1.35, 3.6, 7.0
        wall_frame(K, 20, [(-1.75, -1.62), (1.75, 1.85)], [(-4.0, -1.7, 6.0, 6.3), (-1.75, 1.8, 3.35, 3.3), (-1.75, 1.85, 7.3, 7.15), (1.8, 4.0, 5.8, 5.6)],
                   brace=(3.7, 0.6, 1.95, 4.2, -0.3))
        daub_panel("DaubL", -4.0, -1.7, zb, zt, K, 110)
        daub_panel("DaubR", 1.8, 4.0, zb, zt, K, 111)
        daub_panel("DaubLow", -1.7, 1.8, zb, 3.2, K, 112)
        daub_panel("DaubHigh", -1.7, 1.8, 7.4, zt, K, 113)
        wattle_patch("WatA", -3.0, 2.6, 0.5, 0.6, -0.36, -1, K, rng)
        fr = K["plank"]       # the casement: a crooked oak frame, diamond-leaded panes (Glass)
        hewn("WinHead", (wx0 - 0.1, -0.1, wz1 + 0.02), (wx1 + 0.1, -0.1, wz1 - 0.06), 0.3, 0.22, fr, seed=5, jit=0.01)
        hewn("WinSill", (wx0 - 0.25, -0.2, wz0 - 0.08), (wx1 + 0.25, -0.2, wz0 - 0.05), 0.55, 0.18, fr, seed=6, jit=0.01)
        for sx in (-1, 1):
            hewn(f"WinJamb{sx}", (sx * 1.38, -0.1, wz0), (sx * 1.38, -0.1, wz1), 0.18, 0.3, fr, seed=7 + sx, up=(0, 1, 0), jit=0.01)
        hewn("WinMullion", (0.0, -0.1, wz0), (0.04, -0.1, wz1), 0.14, 0.24, fr, seed=9, up=(0, 1, 0), jit=0.01)
        for side in (-1, 1):
            cx = side * 0.68
            lo, hi = cx - 0.6, cx + 0.6
            for k in range(-5, 6):
                for sgn in (-1, 1):
                    seg = []
                    for i in range(41):
                        z = wz0 + (wz1 - wz0) * i / 40
                        x = cx + k * 0.34 + sgn * (z - (wz0 + wz1) / 2) * 0.55
                        if lo <= x <= hi:
                            seg.append((x, -0.08, z))
                    if len(seg) > 1:
                        tube(f"Came{side}{k}{sgn}", [seg[0], seg[-1]], 0.018, K["iron"], poly=True)
        set_group("Glass")
        for side in (-1, 1):
            box(f"Pane{side}", (1.2, 0.03, wz1 - wz0), (side * 0.68, -0.08, (wz0 + wz1) / 2), K["glass"], bevel=0.0)
        set_group("Main")
        shutter("ShR", T(wx1 + 0.72, -0.55, wz0 - 0.15), "Sigil0", K)       # open flat on the wall
        shutter("ShL", T(wx0 - 0.15, -0.6, wz1 + 0.1) @ RZ(-1.25) @ RY(0.22) @ T(-0.7, 0, -3.3), "Sigil2", K)   # off one hinge
        tube("HingeL", [(wx0 - 0.05, -0.47, wz1 - 0.4), (wx0 - 0.2, -0.55, wz1 - 0.4)], 0.04, K["iron"], poly=True)
        hewn("BoxFront", (-1.45, -0.95, wz0 - 0.55), (1.45, -0.95, wz0 - 0.5), 0.12, 0.6, K["plank"], seed=12, jit=0.01)
        hewn("BoxBottom", (-1.45, -0.72, wz0 - 0.83), (1.45, -0.72, wz0 - 0.83), 0.55, 0.08, K["plank"], seed=13, jit=0.01)
        for sx in (-1, 1):
            box(f"BoxEnd{sx}", (0.1, 0.55, 0.6), (sx * 1.42, -0.72, wz0 - 0.52), K["plank"], bevel=0.02)
            tube(f"Bracket{sx}", [(sx * 1.0, -0.47, wz0 - 1.6), (sx * 1.0, -0.9, wz0 - 0.9), (sx * 1.0, -0.9, wz0 - 0.82)], 0.035, K["iron"], poly=True)
        box("BoxSoil", (2.7, 0.42, 0.1), (0, -0.72, wz0 - 0.33), K["soil"], bevel=0.0)
        for k in range(5):
            p = (-1.1 + k * 0.55, -0.72, wz0 - 0.3)
            if k % 2:
                cards.crossed(p, 0.55, 0.75, "lavender", k=2)
            else:
                cards.fronds(p, 5, 0.65, 0.45, ("fern", "nightshade", "fern")[k // 2], elev=(25, 55))
        box("SillIn", (2.9, 0.42, 0.1), (0, 0.25, wz0 - 0.08), K["plank"], bevel=0.02)
        bottle("SillBottle", 0.7, 0.33, wz0 - 0.03, 0.13, 0.5, K["bottle"], K, shape=2)
        candle("SillCandle", -0.6, 0.3, wz0 - 0.03, 0.1, 0.22, K, drips=3, flame=False, mat=K["waxdk"])
        ivy(cards, rng, [(-3.7, -0.47, 0.3), (-3.4, -0.47, 1.8), (-3.6, -0.47, 3.4)], n=10, size=0.8)
    else:   # the door
        hx = -1.98
        wall_frame(K, 30, [(-2.25, -2.3, 0.0, 7.55), (2.25, 2.2, 0.0, 7.25)], [(-4.0, -2.3, 5.4, 5.7), (2.2, 4.0, 6.0, 5.8)],
                   brace=(3.75, 0.6, 2.4, 3.6, -0.2), sole=((-4.0, -2.35), (2.35, 4.0)))
        hewn("Lintel", (-2.8, 0, 7.92), (2.8, 0, 7.6), WALL_T + 0.05, 0.62, K["timberdk"], bow=(0, 0, 0.08), seed=33, jit=0.02)
        daub_panel("DaubL", -4.0, -2.3, zb, zt, K, 120)
        daub_panel("DaubR", 2.2, 4.0, zb, zt, K, 121)
        daub_panel("DaubHigh", -2.3, 2.2, 8.1, zt, K, 122)
        wattle_patch("WatA", 3.1, 8.6, 0.45, 0.6, -0.36, -1, K, rng)
        rock("Threshold", (0, -0.15, 0.06), (4.3, 1.3, 0.16), K["field"], rng, rot=(0, 0, 0.02), bevel=0.15)
        pts = [(math.cos(a) * 0.26 + 0.9, -0.5, 8.45 + math.sin(a) * 0.3) for a in [PI * (-0.15 + 1.3 * i / 12) for i in range(13)]]
        bar("Horseshoe", pts, 0.045, K["iron"], seg=6)          # luck over the door, and a rowan cross in red thread
        for k, a in enumerate((0.5, -0.5)):
            pole(f"Rowan{k}", [(-0.9 - math.sin(a) * 0.5, -0.52, 7.9), (-0.9, -0.55, 8.2), (-0.9 + math.sin(a) * 0.5, -0.52, 8.55)], 0.03, K["hazel"],
                 seed=40 + k, seg=5)
        hoop("RowanTie", (-0.9, -0.56, 8.2), 0.06, "Y", K["toadred"], thick=0.018)
        set_group("Door0", hinge=(hx, -0.42, 0.0), swing=-1)       # five crooked planks, hinge on the left, opens out (-Y)
        yd = -0.25
        xs = [-1.95, -1.17, -0.37, 0.4, 1.18, 1.95]
        for k in range(5):
            a, b = xs[k] + 0.02, xs[k + 1] - 0.02
            ztop = 7.48 - (a + b) / 2 * 0.07 - g.uniform(0, 0.06)
            poly = [(a, 0.2), (b, 0.2), (b, ztop - 0.03 * (k % 2)), (a, ztop)]
            prism(f"Plank{k}", poly, yd, 0.26 + g.uniform(-0.02, 0.02), K["plank"] if k % 2 else K["timber"], plane="XZ", bevel=0.03)
        for k, z in enumerate((1.3, 6.2)):
            tube(f"Strap{k}", [(hx - 0.02, yd - 0.15, z), (1.3, yd - 0.15, z + 0.04)], 0.06, K["iron"], square=True, poly=True)
            curl = [(1.3 + 0.25 * math.sin(a), yd - 0.16, z + 0.04 + 0.25 - 0.25 * math.cos(a)) for a in [i / 8 * 1.6 * PI for i in range(9)]]
            bar(f"StrapCurl{k}", curl, lambda t: 0.04 * (1 - t * 0.6), K["iron"], seg=5)
            for i in range(5):
                sphere(f"Nail{k}{i}", 0.045, (hx + 0.3 + i * 0.7, yd - 0.2, z + 0.02), K["iron"], seg=6, rings=3, scale=(1, 0.5, 1))
            cyl(f"Knuckle{k}", 0.08, 0.45, (hx, -0.42, z), K["iron"], verts=8, bevel=0.01)
            box(f"Ledge{k}", (3.7, 0.12, 0.42), (0, yd + 0.19, z + 0.05), K["timberdk"], bevel=0.03)
        hewn("DoorBrace", (-1.65, yd + 0.19, 1.6), (1.6, yd + 0.19, 5.9), 0.36, 0.12, K["timberdk"], seed=44, up=(0, 1, 0))
        pprism("Hex", "WP_HexSign", [(math.cos(a) * 0.55, math.sin(a) * 0.55) for a in [i / 24 * 2 * PI for i in range(24)]], 0.04, T(0, yd - 0.15, 4.6),
               K["wp"], edge="WP_wood", k=2.5)
        pole("Pull", [(1.45, yd - 0.15, 3.2), (1.5, yd - 0.42, 3.45), (1.52, yd - 0.44, 3.95), (1.48, yd - 0.15, 4.2)], 0.05, K["bonew"], seed=46, seg=6)
        box("Latch", (0.7, 0.08, 0.1), (1.45, yd + 0.21, 3.75), K["plank"], bevel=0.02)
        set_group("Main")
        box("Keeper", (0.2, 0.25, 0.3), (2.38, 0.2, 3.75), K["planklt"], bevel=0.03)
        cards.fronds((2.9, -0.8, 0.0), 6, 0.9, 0.5, "fern", elev=(15, 45))
        cards.crossed((-3.0, -0.75, 0.0), 0.8, 0.9, "grass", k=2)
    witchify(K, rng, kind, st0, cards)
    leaves_done({"plain": "HutWall", "window": "HutWallWindow", "door": "HutWallDoor"}[kind], cards)
    return _dims()


def hut_post(M):
    """A stone pier (ground to the floor at 1.6) under a jowled oak post to 12.6, for each corner and each joint between walls
    (the wall ends tuck into it). Pivot at the ground."""
    K = wk(M)
    rng = RNG(4720)
    box("Pier", (2.0, 2.0, FLOOR - 0.12), (0, 0, (FLOOR - 0.12) / 2), K["rubble"], bevel=0.06)
    for k in range(4):
        a = k * PI / 2 + PI / 4
        for j in range(2):
            rock(f"Quoin{k}{j}", (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.35 + j * 0.62), (0.75 if (j + k) % 2 else 0.5, 0.55, 0.55), K["field"], rng)
    rock("Cap", (0, 0, FLOOR - 0.07), (2.15, 2.1, 0.16), K["fielddk"], rng, rot=(0, 0, 0.05), bevel=0.12)
    p = hewn("Post", (0, 0, FLOOR), (0.0, 0, FLOOR + WALL_H), 1.45, 1.45, K["timber"], bow=(0.1, -0.08, 0), seed=4721, up=(0, 1, 0), n=18, jit=0.03,
             cham=0.25)
    for v in p.data.vertices:
        t = (v.co.z - FLOOR) / WALL_H
        if t > 0.82:      # the jowl
            k = 1 + 0.16 * ((t - 0.82) / 0.18) ** 1.5
            v.co.x *= k
            v.co.y *= k
        v.co.z = min(v.co.z, FLOOR + WALL_H)
    for k, (z, a) in enumerate(((4.2, 0.3), (8.7, 2.2), (6.1, 4.0))):
        blob(f"Knot{k}", (math.cos(a) * 0.73, math.sin(a) * 0.73, FLOOR + z), 0.13, K["timberdk"], seg=8, rings=5, scale=(1, 1, 1.4))
    pprism("Carve", "WP_Sigil0", [(-0.32, -0.32), (0.32, -0.32), (0.32, 0.32), (-0.32, 0.32)], 0.01, T(0, -0.735, FLOOR + 5.2), K["wp"], edge="WP_wood")
    cards = Cards(rng)
    for k in range(6):
        a = k / 6 * 2 * PI + 0.3
        cards.crossed((math.cos(a) * 1.25, math.sin(a) * 1.25, 0.0), 0.8, 0.8, "grass" if k % 2 else "fern", k=2)
    leaves_done("HutPost", cards)
    return _dims()


def gable_daub(name, x0, x1, z0, top, K, seed, t=0.66):
    """A daub panel under a sloping edge: from z0 up to top(x) (the raking line of the roof)."""
    f = noise2(seed)
    nx = max(2, int((x1 - x0) / 0.45))
    nz = 10
    V, F, idx = [], [], {}
    for s in (-1, 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            zt = top(x)
            for j in range(nz + 1):
                z = z0 + (zt - z0) * j / nz
                edge = i in (0, nx) or j in (0, nz)
                u, v = i / nx, j / nz
                dy = 0 if edge else 0.04 * math.sin(PI * u) ** 0.6 * math.sin(PI * v) ** 0.6 + 0.022 * f(x * 1.7 + s * 3, z * 1.7)
                idx[(s, i, j)] = len(V)
                V.append((x, s * (t / 2 + dy), z))
    for s in (-1, 1):
        for i in range(nx):
            for j in range(nz):
                a, b, c, d = idx[(s, i, j)], idx[(s, i + 1, j)], idx[(s, i + 1, j + 1)], idx[(s, i, j + 1)]
                F.append((a, b, c, d) if s == -1 else (d, c, b, a))
    loop = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(nz)] + [(i, nz) for i in range(nx, 0, -1)] + [(0, j) for j in range(nz, 0, -1)]
    for k in range(len(loop)):
        p, q = loop[k], loop[(k + 1) % len(loop)]
        F.append((idx[(-1,) + p], idx[(1,) + p], idx[(1,) + q], idx[(-1,) + q]))
    ob = mk(name, V, F, K["daub"], smooth=True)
    B40.P_recalc(ob)
    return ob


GABLE_TOP = 8.7        # the gable's apex above the wall plate (tucked up under the ridge pole and the thatch)


def hut_gable(M):
    """The triangle over a 16-wide end wall (on the wall plates, pivot at their top, x across, front -Y): a tie beam, a king
    post and raking struts, daub panels, a round owl hole with a perch, and a goat's skull and a rowan cross under the apex."""
    K = wk(M)
    rng = RNG(4730)
    top = lambda x: GABLE_TOP - abs(x)       # noqa: E731
    hewn("TieBeam", (-8.0, 0, 0.3), (8.0, 0, 0.3), WALL_T, 0.6, K["timber"], bow=(0, 0.06, 0.0), seed=4731, jit=0.015, n=24)
    hewn("KingPost", (0, 0, 0.5), (0.05, 0, GABLE_TOP - 0.2), 0.6, WALL_T, K["timber"], bow=(0.1, 0, 0), seed=4732, up=(0, 1, 0))
    for sx in (-1, 1):
        hewn(f"Stud{sx}", (sx * 4.0, 0, 0.5), (sx * 4.05, 0, top(sx * 4.05) - 0.15), 0.5, WALL_T, K["timber"], bow=(sx * 0.08, 0, 0), seed=4733 + sx,
             up=(0, 1, 0))
        hewn(f"Strut{sx}", (sx * 0.3, 0, 4.2), (sx * 3.8, 0, 1.1), 0.4, WALL_T, K["timber"], bow=(0, 0, 0.25), seed=4735 + sx, up=(0, 1, 0))
        hewn(f"Rake{sx}", (sx * 8.3, -0.05, 0.4), (sx * 0.0, -0.05, GABLE_TOP + 0.3), 0.3, 1.0, K["timberdk"], seed=4737 + sx, up=(0, -1, 0), jit=0.015,
             n=16)
        gable_daub(f"DaubOut{sx}", min(sx * 4.0, sx * 8.0), max(sx * 4.0, sx * 8.0), 0.55, top, K, 4740 + sx)
        gable_daub(f"DaubIn{sx}", min(0.0, sx * 4.0), max(0.0, sx * 4.0), 0.55, top, K, 4742 + sx)
    prism("OwlDark", [(math.cos(a) * 0.48 + 1.9, math.sin(a) * 0.48 + 4.4) for a in [i / 16 * 2 * PI for i in range(16)]], -0.36, 0.06, K["soot"], plane="XZ")
    B40.ringbar("OwlRing", (1.9, -0.4, 4.4), 0.52, "Y", K["hazel"], thick=0.06, n=18, seg=6)
    pole("OwlPerch", [(1.9, -0.35, 3.85), (1.9, -0.9, 3.82), (1.95, -1.05, 3.86)], 0.04, K["hazel"], seed=4744, seg=5)
    skull_small("Goat", T(0, -0.75, 6.4) @ RX(-0.15), K, s=1.25, horns=True)
    for k, a in enumerate((0.6, -0.6)):
        pole(f"Rowan{k}", [(-1.8 - math.sin(a) * 0.55, -0.52, 4.8), (-1.8, -0.56, 5.2), (-1.8 + math.sin(a) * 0.55, -0.52, 5.6)], 0.035, K["hazel"],
             seed=4745 + k, seg=5)
    hoop("RowanTie", (-1.8, -0.57, 5.2), 0.07, "Y", K["toadred"], thick=0.02)
    wattle_patch("WatA", -5.2, 1.9, 0.5, 0.55, -0.36, -1, K, rng)
    wattle_patch("WatB", 2.6, 1.6, 0.45, 0.5, 0.36, 1, K, rng)
    cobweb("Web", (-0.35, 0.48, GABLE_TOP - 1.0), (-1, 0, -1), (0, 0.9, -1), 1.1, K)
    return _dims()


# ------------------------------------------------------------------ the thatch

D45 = Vector((0, C45, C45))         # up the slope
N45 = Vector((0, -C45, C45))        # out of the slope
RAFTER_Z = 0.25                     # the rafters' centre line at the wall line (they sit on the wall plate)
RAFTER_R = 0.22
UNDER = 0.38                        # rafter centre to the thatch's underside (over the battens)
THATCH_T = 1.3
S_EAVE, S_RIDGE = -3.0, 13.0         # along the slope from the wall line


def overlap_d(x):
    """The 1-stud overlap at each end of an 8-long run: thicker over the +X neighbour then tucked under it, tucked under the
    -X neighbour; two runs placed 8 apart cross along one clean line instead of fighting over the same faces."""
    if x > 3.0:
        u = (x - 3.0) / 2.0
        return 0.13 * math.sin(1.2 * PI * u)
    if x < -3.0:
        u = (-3.0 - x) / 2.0
        return -0.13 * math.sin(PI * u / 2)
    return 0.0


def thatch_pt(x, s, t):
    """A point on the slope: x along the eaves, s up the slope from the wall line, t out from the rafters' centre line."""
    return Vector((x, 0, RAFTER_Z)) + D45 * s + N45 * t


def hut_roof(M):
    """An 8-long run (along X) of one 45-degree thatched slope, its pivot on the wall plate's top at the wall's centre line,
    rising to the ridge 8 behind it (+Y); the eaves hang 1.6 below the plate and 2.4 out. Poles for rafters, hazel battens,
    1.3 of combed reed thatch with a bell at the eaves, moss in the hollows between the rafters, a hazel ligger along the
    eaves. The thatch runs 1 stud past each end, so runs 8 apart overlap; the back slope is the same piece turned round."""
    K = wk(M)
    rng = RNG(4750)
    ln = noise2(4751, px=8.0)
    xs = [-5.0 + 0.25 * i for i in range(41)]
    ss = [S_EAVE + (S_RIDGE - S_EAVE) * j / 52 for j in range(53)]
    S = S_RIDGE - S_EAVE

    def thick(x, s):
        u = (s - S_EAVE) / S
        bell = 0.3 * math.exp(-(s - S_EAVE) / 1.4)
        sag = (0.5 - 0.5 * math.cos(PI * (x + 1))) * 0.13 * math.sin(PI * min(1, u * 1.2)) ** 0.6
        course = 0.05 * max(0.0, math.sin(2 * PI * s / 1.7)) ** 6
        return THATCH_T + bell - sag + course + 0.045 * ln(x, s) + overlap_d(x)

    def surf(x, s, lift=0.0):
        return thatch_pt(x, s, UNDER + thick(x, s) + lift)
    V, F = [], []
    nI, nJ = len(xs), len(ss)
    top = lambda i, j: i * nJ + j                        # noqa: E731
    und = lambda i, j: nI * nJ + i * nJ + j              # noqa: E731
    for x in xs:
        for j, s in enumerate(ss):
            V.append(tuple(thatch_pt(x, s - (0.25 if j == 0 else 0.0), UNDER + thick(x, s))))
    for x in xs:
        for s in ss:
            V.append(tuple(thatch_pt(x * 0.8, s, UNDER)))
    for i in range(nI - 1):
        for j in range(nJ - 1):
            F.append((top(i, j), top(i + 1, j), top(i + 1, j + 1), top(i, j + 1)))
            F.append((und(i, j + 1), und(i + 1, j + 1), und(i + 1, j), und(i, j)))
    for i in range(nI - 1):
        F.append((und(i, 0), und(i + 1, 0), top(i + 1, 0), top(i, 0)))
        F.append((top(i, nJ - 1), top(i + 1, nJ - 1), und(i + 1, nJ - 1), und(i, nJ - 1)))
    for j in range(nJ - 1):
        F.append((und(0, j), top(0, j), top(0, j + 1), und(0, j + 1)))
        F.append((und(nI - 1, j + 1), top(nI - 1, j + 1), top(nI - 1, j), und(nI - 1, j)))
    th = mk("Thatch", V, F, K["thatch"], smooth=True)
    B40.P_recalc(th)
    for k, x in enumerate((-3.0, -1.0, 1.0, 3.0)):        # rafters (poles) and hazel battens across them
        a = thatch_pt(x, S_EAVE + 0.35, 0)
        b = thatch_pt(x, RISE / C45 + 0.35, 0)
        pts = [tuple(a.lerp(b, t) + Vector((0.06 * math.sin(t * 7 + k), 0, 0))) for t in [i / 8 for i in range(9)]]
        pole(f"Rafter{k}", pts, RAFTER_R, K["pole"], seed=4752 + k, seg=8, taper=0.2)
    for j in range(15):
        c = thatch_pt(0, S_EAVE + 0.6 + j * 0.88, RAFTER_R + 0.075)
        pole(f"Batten{j}", [tuple(c + Vector((-4.0, 0, 0))), tuple(c + Vector((0, 0, 0.02 * math.sin(j)))), tuple(c + Vector((4.0, 0, 0)))], 0.075,
             K["hazel"], seed=4760 + j, seg=6, taper=0.1, knob=0.05)
    s_l = S_EAVE + 0.9          # the eaves ligger and its spars
    bar("Ligger", [tuple(surf(x, s_l, 0.04)) for x in [-3.9 + 7.8 * i / 12 for i in range(13)]], 0.05, K["hazel"], seg=6)
    for k in range(9):
        x = -3.6 + k * 0.9
        bar(f"Spar{k}", [tuple(surf(x - 0.18, s_l + 0.35, -0.05)), tuple(surf(x, s_l - 0.05, 0.1)), tuple(surf(x + 0.18, s_l + 0.35, -0.05))], 0.03,
            K["hazel"], seg=5)
    cards = Cards(rng)
    for k in range(9):           # moss cushions in clumps, and grass seeded in the thatch
        x0, s0 = rng.uniform(-3.3, 3.3), rng.uniform(S_EAVE + 1.5, S_RIDGE - 3.0)
        for j in range(int(rng.integers(3, 6))):
            x, s = x0 + rng.uniform(-0.5, 0.5), s0 + rng.uniform(-0.5, 0.5)
            p = surf(x, s, -0.06)
            r = rng.uniform(0.16, 0.36)
            blob(f"Moss{k}_{j}", (0, 0, 0), r, K["moss2"], seg=9, rings=6, scale=(1.2, 1.0, 0.6), jitter=0.25, seed=k * 10 + j)
            P.PARTS[-1].matrix_world = T(*p) @ RX(PI / 4)
        if k % 2 == 0:
            cards.crossed(tuple(surf(x0, s0, 0.0)), 0.6, 0.6, "grass", k=2)
    leaves_done("HutRoof", cards)
    return _dims()


RIDGE_Z = RAFTER_Z + RISE + 2 * (UNDER + THATCH_T) * C45 - 0.05    # the thatch's top surface where the two slopes cross


def hut_ridge(M):
    """The block-cut ridge roll for an 8-long run, astride the two slopes (pivot at the hut's centre line, at the wall-plate
    height, like the roofs): sedge laid over the apex, its lower edges cut into points, two hazel liggers a side with criss-cross
    spars between, moss; under it, inside, the ridge pole. Overlaps its neighbours like HutRoof."""
    K = wk(M)
    rng = RNG(4770)
    ln = noise2(4771, px=8.0)
    xs = [-5.0 + 0.2 * i for i in range(51)]
    nv = 25

    def edge(x):
        tri = abs(((x + 0.25) % 1.0) - 0.5) * 2         # 0..1, a point every stud
        return 2.25 - 0.45 * tri

    def under(y):
        return RIDGE_Z - abs(y) - 0.12

    def surf(x, y, ov=True):
        e = edge(x)
        v = max(-1.0, min(1.0, y / e))
        t = 0.75 + 0.25 * (1 - v * v) + 0.04 * ln(x, v * 3) + (overlap_d(x) * 0.8 if ov else 0)
        return under(y) + t * (0.35 + 0.65 * (1 - abs(v) ** 6)) + 0.35 * (1 - v * v) ** 2
    V, F = [], []
    for x in xs:
        e = edge(x)
        for j in range(nv):
            y = (-1 + 2 * j / (nv - 1)) * e
            V.append((x, y, surf(x, y)))
    for x in xs:
        e = edge(x)
        for j in range(nv):
            y = (-1 + 2 * j / (nv - 1)) * e * 0.995
            V.append((x * 0.98, y, under(y) - 0.02))
    nI = len(xs)
    top = lambda i, j: i * nv + j                    # noqa: E731
    und = lambda i, j: nI * nv + i * nv + j          # noqa: E731
    for i in range(nI - 1):
        for j in range(nv - 1):
            F.append((top(i, j), top(i, j + 1), top(i + 1, j + 1), top(i + 1, j)))
            F.append((und(i + 1, j), und(i + 1, j + 1), und(i, j + 1), und(i, j)))
        F.append((und(i, 0), top(i, 0), top(i + 1, 0), und(i + 1, 0)))
        F.append((und(i + 1, nv - 1), top(i + 1, nv - 1), top(i, nv - 1), und(i, nv - 1)))
    for j in range(nv - 1):
        F.append((und(0, j), und(0, j + 1), top(0, j + 1), top(0, j)))
        F.append((top(nI - 1, j), top(nI - 1, j + 1), und(nI - 1, j + 1), und(nI - 1, j)))
    rid = mk("Roll", V, F, K["thatch"], smooth=True)
    B40.P_recalc(rid)
    for sy in (-1, 1):
        for k, yy in enumerate((0.9, 1.55)):
            y = sy * yy
            bar(f"Ligger{sy}{k}", [(x, y, surf(x, y, False) + 0.03) for x in [-4.0 + 8.0 * i / 16 for i in range(17)]], 0.045, K["hazel"], seg=6)
        for i in range(8):
            x0 = -3.5 + i * 1.0
            for d in (-1, 1):
                a, b = (x0 - d * 0.5, sy * 0.9), (x0 + d * 0.5, sy * 1.55)
                pts = []
                for t in (0, 0.5, 1):
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    pts.append((x, y, surf(x, y, False) + 0.04))
                bar(f"Spar{sy}{i}{d}", pts, 0.028, K["hazel"], seg=4)
    for k in range(6):
        x = rng.uniform(-3.4, 3.4)
        y = (1 if k % 2 else -1) * rng.uniform(0.2, 1.1)
        sphere(f"Moss{k}", rng.uniform(0.25, 0.5), (x, y, surf(x, y, False) - 0.05), K["moss2"], seg=9, rings=5, scale=(1.4, 1.0, 0.4))
    pole("RidgePole", [(-4.0, 0, RAFTER_Z + RISE + 0.12), (0, 0.02, RAFTER_Z + RISE + 0.1), (4.0, 0, RAFTER_Z + RISE + 0.12)], 0.33, K["pole"], seed=4772,
         seg=10, taper=0.05)
    return _dims()


def hut_footing(M):
    """An 8-long run of rubble footing under a wall (x = -4..4 between two HutPost piers, which cover its ends), 1.8 wide,
    its top at the floor (1.6); fieldstones bedded in mossy mortar, flat capstones, a little arched crawl vent with an iron
    grate, toadstools in the damp at its foot. Pivot at the ground."""
    K = wk(M)
    rng = RNG(4780)
    box("Core", (8.0, 1.7, FLOOR - 0.08), (0, 0, (FLOOR - 0.08) / 2), K["rubble"], bevel=0.05)
    for sy in (-1, 1):            # proud stones on both faces, in rough courses
        x = -3.9
        row = 0
        while x < 3.9:
            w = rng.uniform(0.6, 1.25)
            for zc, hh in ((0.35, 0.6), (1.05, 0.55)):
                if abs(x + w / 2) < 0.9 and sy < 0 and zc < 0.6:
                    continue      # the vent
                rock(f"St{sy}{row}{zc}", (x + w / 2, sy * 0.78, zc + rng.uniform(-0.05, 0.05)), (w * 0.95, 0.4, hh * rng.uniform(0.85, 1.0)),
                     K["field"] if rng.random() < 0.7 else K["fielddk"], rng, bevel=0.12)
            x += w
            row += 1
    x = -3.0
    k = 0
    while x < 3.0:                # flat capstones (the piers cap the last stud at each end)
        w = min(rng.uniform(1.0, 1.6), 3.0 - x)
        rock(f"Cap{k}", (x + w / 2, rng.uniform(-0.05, 0.05), FLOOR - 0.08), (w * 0.97, 1.85, 0.16), K["fielddk"], rng, rot=(0, 0, rng.uniform(-0.03, 0.03)),
             bevel=0.12)
        x += w
        k += 1
    pts = [(math.cos(a) * 0.55, math.sin(a) * 0.55 + 0.1) for a in [i / 10 * PI for i in range(11)]] + [(-0.55, 0.0), (0.55, 0.0)]
    prism("Vent", [(-0.55, 0.0), (0.55, 0.0)] + [(math.cos(a) * 0.55, math.sin(a) * 0.55 + 0.1) for a in [i / 10 * PI for i in range(11)]], -0.86, 0.04,
          K["soot"], plane="XZ")
    for k in range(5):
        x = -0.4 + k * 0.2
        tube(f"Grate{k}", [(x, -0.9, 0.0), (x, -0.9, 0.1 + math.sqrt(max(0, 0.3 - x * x)))], 0.025, K["iron"], poly=True)
    tube("GrateBar", [(-0.5, -0.9, 0.35), (0.5, -0.9, 0.35)], 0.025, K["iron"], poly=True)
    for k, (x, y, h, r) in enumerate(((1.4, -1.1, 0.35, 0.16), (1.65, -1.2, 0.22, 0.11), (-2.2, -1.05, 0.28, 0.13))):
        lathe(f"Stool{k}", [(0, 0), (r * 0.35, 0), (r * 0.3, h), (0, h)], K["toadstem"], seg=8, loc=(x, y, 0))
        lathe(f"Cap{k}", [(0, h - 0.02), (r, h - 0.04), (r * 0.9, h + r * 0.35), (r * 0.5, h + r * 0.6), (0, h + r * 0.65)], K["mush"], seg=10, loc=(x, y, 0))
    cards = Cards(rng)
    for k in range(9):
        x = -3.6 + k * 0.9 + rng.uniform(-0.2, 0.2)
        if k % 3 == 1:
            cards.fronds((x, -1.05, 0.0), 5, 0.8, 0.45, "fern", elev=(15, 45))
        else:
            cards.crossed((x, -1.0, 0.0), 0.8, 0.7, "grass", k=2)
    leaves_done("HutFooting", cards)
    return _dims()


def hut_chimney(M):
    """A leaning fieldstone chimney for a gable end (its back on y = 0 against the gable wall's outside face, pivot at the
    ground): a wide firebox base to 12.5, weathered shoulders, a stack 2.6 x 2.0 that leans out and kinks back, iron bands and
    ties to the wall, an oversailing cap, a crooked clay pot and a broken one, soot, moss, ivy; a cleanout door and an ash heap."""
    K = wk(M)
    rng = RNG(4790)
    rb = K["rubble"]

    def lean(z):          # out (-Y) and sideways as it climbs, with a kink back at 20
        if z < 12.0:
            return 0.0, 0.0
        u = z - 12.0
        dy = -0.07 * u + (0.04 * (z - 20.0) if z > 20.0 else 0.0)
        dx = 0.035 * u - (0.03 * (z - 20.0) if z > 20.0 else 0.0)
        return dx, dy
    box("Base", (4.4, 2.8, 12.5), (0, -1.4, 6.25), rb, bevel=0.08)
    # the weathered shoulders: a sloped course from the base to the stack
    prism("Shoulder", [(-2.2, 12.5), (2.2, 12.5), (1.3, 14.0), (-1.3, 14.0)], -1.45, 2.7, rb, plane="XZ", bevel=0.05)
    rock("ShoulderCapL", (-1.85, -1.4, 13.2), (1.2, 2.9, 0.2), K["fielddk"], rng, rot=(0, -0.95, 0), bevel=0.1)
    rock("ShoulderCapR", (1.85, -1.4, 13.2), (1.2, 2.9, 0.2), K["fielddk"], rng, rot=(0, 0.95, 0), bevel=0.1)
    # the stack in sections that follow the lean
    zs = [13.8 + i * 1.4 for i in range(9)]
    for k, z in enumerate(zs):
        dx, dy = lean(z + 0.7)
        box(f"Stack{k}", (2.6, 2.0, 1.45), (dx, -1.2 + dy, z + 0.7), rb, bevel=0.04)
    ztop = zs[-1] + 1.4
    # quoins at the corners of the base and the stack
    for k in range(9):
        z = 0.45 + k * 1.35
        for sx in (-1, 1):
            long = (k + (sx > 0)) % 2
            rock(f"QB{k}{sx}", (sx * (2.2 - (0.45 if long else 0.3)), -2.62, z), (0.9 if long else 0.6, 0.55 if long else 0.85, 0.62), K["field"], rng, bevel=0.12)
    for k, z in enumerate(zs):
        dx, dy = lean(z + 0.7)
        for sx in (-1, 1):
            long = (k + (sx > 0)) % 2
            rock(f"QS{k}{sx}", (dx + sx * (1.3 - (0.38 if long else 0.26)), -1.2 + dy - 0.84, z + 0.7), (0.75 if long else 0.5, 0.5 if long else 0.7, 0.62),
                 K["field"], rng, bevel=0.12)
    # proud stones scattered on the faces
    for k in range(26):
        z = rng.uniform(0.6, 12.0)
        x = rng.uniform(-1.8, 1.8)
        rock(f"Face{k}", (x, -2.82, z), (rng.uniform(0.5, 0.9), 0.2, rng.uniform(0.35, 0.55)), K["fielddk"], rng, bevel=0.15)
    for k in range(4):
        z = rng.uniform(1.0, 11.0)
        for sx in (-1, 1):
            rock(f"Side{k}{sx}", (sx * 2.22, rng.uniform(-2.2, -0.6), z), (0.2, rng.uniform(0.6, 0.9), rng.uniform(0.35, 0.5)), K["field"], rng, bevel=0.15)
    # the oversailing cap and the pots
    dx, dy = lean(ztop)
    rock("Oversail", (dx, -1.2 + dy, ztop + 0.12), (3.1, 2.5, 0.28), K["fielddk"], rng, rot=(0, 0, 0.03), bevel=0.12)
    rock("Flaunch", (dx, -1.2 + dy, ztop + 0.36), (2.5, 1.9, 0.3), rb, rng, bevel=0.2)
    px, py = dx - 0.45, -1.2 + dy
    s = _mark()
    lathe("Pot", [(0, 0), (0.42, 0), (0.38, 1.4), (0.3, 2.0), (0.34, 2.1), (0.4, 2.25), (0.36, 2.3), (0.27, 2.26), (0.24, 0.2), (0, 0.2)], K["clay"], seg=16)
    lathe("PotSoot", [(0.3, 2.31), (0.36, 2.32), (0.33, 2.36), (0.26, 2.33)], K["soot"], seg=16)
    cone("Cowl", 0.55, 0.05, 0.5, (0, 0, 2.75), K["tin"], verts=12)
    for a in (0.5, 2.6, 4.7):
        tube(f"CowlLeg{a}", [(math.cos(a) * 0.32, math.sin(a) * 0.32, 2.3), (math.cos(a) * 0.42, math.sin(a) * 0.42, 2.55)], 0.02, K["iron"], poly=True)
    _xform(s, T(px, py, ztop + 0.5) @ RY(-0.12) @ RX(0.06))
    s = _mark()
    lathe("PotBroken", [(0, 0), (0.36, 0), (0.33, 0.8), (0.31, 1.0), (0.27, 1.02), (0.25, 0.2), (0, 0.2)], K["clay"], seg=14, jitter=(0.05, 3))
    for v in P.PARTS[-1].data.vertices:
        if v.co.z > 0.7:
            v.co.z -= 0.25 * (0.5 + 0.5 * math.sin(math.atan2(v.co.y, v.co.x) * 3))
    _xform(s, T(px + 0.95, py + 0.05, ztop + 0.5) @ RY(0.08))
    for k in range(6):        # soot round the top courses
        a = k / 6 * 2 * PI
        rock(f"Soot{k}", (dx + math.cos(a) * 1.25, -1.2 + dy + math.sin(a) * 0.95, ztop - 0.3), (0.6, 0.35, 0.5), K["soot"], rng, bevel=0.15)
    # iron bands round the stack, tied back to the wall
    for k, z in enumerate((16.5, 22.5)):
        dx, dy = lean(z)
        c = Vector((dx, -1.2 + dy, z))
        pts = [tuple(c + Vector((sx * 1.36, sy * 1.06, 0))) for sx, sy in ((-1, 1), (-1, -1), (1, -1), (1, 1))]
        tube(f"Band{k}", pts + [pts[0]], 0.06, K["iron"], square=True, poly=True)
        for sx in (-1, 1):
            tube(f"Tie{k}{sx}", [(dx + sx * 1.1, -0.15 + dy * 0.5, z), (sx * 1.1, 0.0, z + 0.2)], 0.05, K["iron"], poly=True)
            box(f"TiePlate{k}{sx}", (0.5, 0.05, 0.5), (sx * 1.1, -0.02, z + 0.2), K["iron"], bevel=0.01)
    # moss on the shoulders, the cleanout door and the ash heap at its foot
    for k in range(5):
        sphere(f"MossS{k}", rng.uniform(0.3, 0.5), (rng.uniform(-1.9, 1.9), rng.uniform(-2.5, -0.5), 12.9 + rng.uniform(-0.2, 0.4)), K["moss2"], seg=9, rings=5,
               scale=(1.3, 1.0, 0.4))
    box("Cleanout", (0.9, 0.08, 0.8), (0.9, -2.83, 0.9), K["castiron"], bevel=0.03)
    for zz in (0.65, 1.15):
        tube(f"CleanBar{zz}", [(0.5, -2.88, zz), (1.3, -2.88, zz)], 0.025, K["iron"], square=True, poly=True)
    sphere("Ash", 0.6, (1.0, -3.2, 0.0), K["ash"], seg=12, rings=6, scale=(1.4, 1.0, 0.35))
    for k in range(3):
        pole(f"Log{k}", [(-1.6 + k * 0.4, -3.3, 0.22 + (k % 2) * 0.36), (-1.4 + k * 0.4, -3.3 + 1.6, 0.22 + (k % 2) * 0.36)], 0.2, K["bark"], seed=k, seg=8)
        P.PARTS[-1].matrix_world = T(-1.8, -3.5, 0) @ RZ(1.5) @ T(1.8, 3.5, 0)
    cards = Cards(rng)
    ivy(cards, rng, [(-2.25, -2.85, 0.3), (-1.9, -2.85, 2.5), (-1.4, -2.85, 4.5), (-1.7, -2.85, 6.5), (-1.2, -2.85, 8.0)], n=30, size=1.0)
    ivy(cards, rng, [(-2.25, -2.0, 0.3), (-2.25, -1.4, 2.6), (-2.25, -1.8, 4.6)], side=(-1, 0, 0), n=12, size=0.9)
    cards.fronds((-1.8, -3.1, 0.0), 6, 1.0, 0.55, "fern", elev=(15, 45))
    cards.crossed((2.0, -3.1, 0.0), 0.9, 0.9, "grass", k=3)
    leaves_done("HutChimney", cards)
    return _dims()


PORCH_D = 5.0         # the deck runs from the wall line out to y = -5.0


def charm(prefix, x, y, ztop, L, kind, K, rng):
    """One hanging charm on a string from (x, y, ztop): a bird skull with feathers, three witch bottles, a hag stone with bells,
    a tin moon and star, a straw star, or a violet crystal (Glow)."""
    zb = ztop - L
    string(f"{prefix}Str", (x, y, ztop), (x + rng.uniform(-0.04, 0.04), y, zb), K, r=0.012)
    if kind == "skull":
        sp = _mark()
        blob(f"{prefix}Skull", (0, 0, 0), 0.13, K["bonew"], seg=10, rings=6, scale=(0.85, 1.0, 0.8))
        cone(f"{prefix}Beak", 0.06, 0.005, 0.32, (0, -0.2, -0.03), K["horn"], verts=8, rot=(PI / 2 + 0.3, 0, 0))
        for sx in (-1, 1):
            sphere(f"{prefix}Eye{sx}", 0.04, (sx * 0.07, -0.08, 0.02), K["socket"], seg=6, rings=4)
        _xform(sp, T(x, y, zb - 0.1))
        for k in range(3):
            feather(f"{prefix}F{k}", (x + (k - 1) * 0.06, y, zb - 0.22), (math.sin((k - 1) * 0.35), 0, -1), 0.55, K, w=0.07,
                    mat=K["feather"] if k != 1 else K["featherb"])
    elif kind == "bottles":
        for k in range(3):
            zz = zb + 0.45 - k * 0.42
            bottle(f"{prefix}B{k}", x + (k - 1) * 0.03, y, zz - 0.36, 0.11, 0.34, (K["bottle"], K["bottleb"], K["bottlev"])[k], K, shape=k % 3)
    elif kind == "hagstone":
        rk = rock(f"{prefix}Stone", (x, y, zb - 0.1), (0.36, 0.2, 0.3), K["field"], rng, bevel=0.2)
        hoop(f"{prefix}Hole", (x + 0.02, y - 0.1, zb - 0.08), 0.06, "Y", K["soot"], thick=0.03)
        for k in range(2):
            lathe(f"{prefix}Bell{k}", [(0, 0.12), (0.03, 0.11), (0.05, 0.04), (0.07, 0.0), (0, 0.01)], K["brass"], seg=10, loc=(x + (k - 0.5) * 0.18, y, zb - 0.42))
            string(f"{prefix}BS{k}", (x, y, zb - 0.25), (x + (k - 0.5) * 0.18, y, zb - 0.3), K, r=0.008)
    elif kind == "moon":
        prism(f"{prefix}Moon", [(math.cos(a) * 0.3, math.sin(a) * 0.3) for a in [PI * (0.25 + 1.5 * i / 12) for i in range(13)]] +
              [(math.cos(a) * 0.22 + 0.09, math.sin(a) * 0.22) for a in [PI * (1.75 - 1.5 * i / 12) for i in range(13)]], y, 0.025, K["tin"], plane="XZ")
        P.PARTS[-1].matrix_world = T(x, 0, zb - 0.3)
        pts = []
        for i in range(10):
            a = PI / 2 + i * PI / 5
            r = 0.14 if i % 2 == 0 else 0.06
            pts.append((math.cos(a) * r, math.sin(a) * r))
        prism(f"{prefix}Star", pts, y, 0.02, K["tin"], plane="XZ")
        P.PARTS[-1].matrix_world = T(x + 0.05, 0, zb - 0.78)
        string(f"{prefix}S2", (x, y, zb - 0.6), (x + 0.05, y, zb - 0.64), K, r=0.008)
    elif kind == "straw":
        for k in range(4):
            a = k * PI / 4
            pole(f"{prefix}Straw{k}", [(x - math.cos(a) * 0.32, y, zb - 0.32 - math.sin(a) * 0.32), (x + math.cos(a) * 0.32, y, zb - 0.32 + math.sin(a) * 0.32)],
                 0.02, K["straw"], seed=k, seg=4, knob=0.0)
        hoop(f"{prefix}Tie", (x, y, zb - 0.32), 0.05, "Y", K["toadred"], thick=0.02)
    else:      # the crystal
        g = P.GROUP
        set_group("Glow")
        cone(f"{prefix}CrystalA", 0.09, 0.0, 0.32, (x, y, zb - 0.18), K["glow"], verts=6)
        cone(f"{prefix}CrystalB", 0.09, 0.0, 0.2, (x, y, zb - 0.43), K["glow"], verts=6, rot=(PI, 0, 0))
        set_group(g)
        hoop(f"{prefix}Wrap", (x, y, zb - 0.32), 0.095, "Z", K["copper"], thick=0.015)


def hut_porch(M):
    """A porch for the door wall: a plank deck (top at the floor, 1.6) on log joists and stone piers, from the wall line out to
    y = -5, three big stone steps down in front, two crooked tree-trunk posts carrying a log beam, a lean-to of mossy shingles
    that tucks under the thatch eaves, branch railings at the sides, and charms hung from the beam: a bird skull and feathers,
    witch bottles, a hag stone with bells, a tin moon and star, a straw star and a violet crystal (Glow). Pivot at the ground
    on the wall's centre line (put it under the door wall)."""
    K = wk(M)
    rng = RNG(4800)
    W = 4.4
    y0, y1 = -0.5, -PORCH_D
    for k, (x, y) in enumerate(((-W + 0.4, y1 + 0.4), (W - 0.4, y1 + 0.4), (-W + 0.4, -1.0), (W - 0.4, -1.0), (0, y1 + 0.4))):
        rock(f"Pier{k}", (x, y, 0.45), (0.8, 0.8, 0.9), K["field"], rng, bevel=0.12)
    for k, y in enumerate((-1.0, -2.8, y1 + 0.4)):
        pole(f"Joist{k}", [(-W, y, FLOOR - 0.45), (0, y + 0.03, FLOOR - 0.47), (W, y, FLOOR - 0.45)], 0.25, K["pole"], seed=4801 + k, seg=8)
    n = 7
    pw = (y0 - y1) / n
    for k in range(n):
        y = y0 - pw * (k + 0.5)
        warp = 0.04 if k == 4 else 0.0
        hewn(f"Plank{k}", (-W - rng.uniform(0, 0.15), y, FLOOR - 0.1), (W + rng.uniform(0, 0.15), y, FLOOR - 0.1 + warp), pw - 0.04, 0.2,
             K["plank"] if k % 2 else K["timber"], seed=4810 + k, jit=0.015, cham=0.03)
        for x in (-W + 0.4, 0.0, W - 0.4):
            sphere(f"Nail{k}{x}", 0.035, (x, y, FLOOR + 0.005), K["iron"], seg=6, rings=3, scale=(1, 1, 0.4))
    for k in range(3):          # the steps
        top = FLOOR - 0.4 * (k + 1)
        rock(f"Step{k}", (rng.uniform(-0.1, 0.1), y1 - 0.5 - k * 0.95, top / 2), (3.2 - k * 0.1, 1.25, top), K["field"] if k != 1 else K["fielddk"], rng,
             rot=(0, 0, rng.uniform(-0.05, 0.05)), bevel=0.06)
    # the posts: crooked trunks with a fork at the top, the beam in the forks
    zb = 9.4
    for k, sx in enumerate((-1, 1)):
        x = sx * (W - 0.5)
        pole(f"Post{k}", crooked((x, y1 + 0.4, FLOOR - 0.1), (x + sx * 0.1, y1 + 0.4, zb - 0.1), 0.18, 4802 + k, n=8, perp=(1, 0, 0)), 0.3, K["bark"],
             seed=4803 + k, seg=10, taper=0.25)
        for d in (-1, 1):
            pole(f"Fork{k}{d}", [(x + sx * 0.1, y1 + 0.4, zb - 0.2), (x + sx * 0.1 + d * 0.18, y1 + 0.4, zb + 0.25), (x + sx * 0.1 + d * 0.32, y1 + 0.38, zb + 0.5)],
                 0.11, K["bark"], seed=4805 + k * 2 + d, seg=6)
    pole("Beam", [(-W - 0.5, y1 + 0.4, zb + 0.1), (0, y1 + 0.4, zb + 0.02), (W + 0.5, y1 + 0.4, zb + 0.1)], 0.28, K["pole"], seed=4808, seg=10, taper=0.1)
    # the lean-to: rafters from the beam to a ledger on the wall, mossy shingles in courses (a few slipped)
    zf, zw = zb + 0.45, zb + 1.55
    yf, yw = y1 + 0.1, -0.55
    rr = lambda y: zf + (zw - zf) * (y - yf) / (yw - yf)       # noqa: E731
    hewn("Ledger", (-W - 0.3, -0.62, zw - 0.2), (W + 0.3, -0.62, zw - 0.2), 0.3, 0.4, K["timberdk"], seed=4809, jit=0.01)
    for k, x in enumerate((-W + 0.3, -1.4, 1.4, W - 0.3)):
        pole(f"Rafter{k}", [(x, yf - 0.4, rr(yf - 0.4) - 0.15), (x, yw, rr(yw) - 0.15)], 0.14, K["pole"], seed=4815 + k, seg=6)
    ang = math.atan2(zw - zf, yw - yf)
    rows = 7
    for r in range(rows):
        t = r / (rows - 1)
        y = (yf - 0.5) + (yw - (yf - 0.5)) * t
        x = -W - 0.4 + (0.3 if r % 2 else 0.0)
        k = 0
        while x < W + 0.4:
            w = rng.uniform(0.5, 0.8)
            sl = 0.12 if rng.random() < 0.05 else 0.0
            box(f"Sh{r}_{k}", (w - 0.04, 1.05, 0.07), (x + w / 2, y - sl, rr(y) + 0.02 * r + 0.03), K["shingle"], bevel=0.02, segments=1,
                rot=(ang + rng.uniform(-0.04, 0.04), rng.uniform(-0.03, 0.03), rng.uniform(-0.04, 0.04)))
            x += w
            k += 1
    for k in range(7):
        x, y = rng.uniform(-W + 0.5, W - 0.5), rng.uniform(yf + 0.2, yw - 0.6)
        sphere(f"Moss{k}", rng.uniform(0.25, 0.5), (x, y, rr(y) + 0.22), K["moss2"], seg=9, rings=5, scale=(1.4, 1.0, 0.35))
    # branch railings at the sides
    for sx in (-1, 1):
        x = sx * (W - 0.15)
        for k, y in enumerate((-0.8, y1 + 0.4)):
            pole(f"RPost{sx}{k}", [(x, y, FLOOR), (x + sx * 0.03, y, FLOOR + 3.3)], 0.12, K["bark"], seed=4820 + k + sx, seg=6)
        for k, z in enumerate((FLOOR + 1.6, FLOOR + 3.2)):
            pole(f"Rail{sx}{k}", crooked((x, -0.7, z), (x, y1 + 0.3, z + 0.05), 0.06, 4823 + k + sx * 3, n=6, perp=(0, 0, 1)), 0.08, K["bark"], seed=4826 + k,
                 seg=6)
        for k in range(3):
            y = -1.6 - k * 1.0
            pole(f"Bal{sx}{k}", [(x, y, FLOOR + 0.05), (x, y + 0.15 * (1 if k % 2 else -1), FLOOR + 1.6)], 0.05, K["hazel"], seed=4830 + k, seg=5)
    # the charms along the beam
    kinds = ["skull", "bottles", "straw", "crystal", "hagstone", "moon"]
    for k, x in enumerate((-2.9, -1.8, -0.75, 0.9, 1.95, 3.0)):
        charm(f"Ch{k}", x, y1 + 0.4, zb - 0.2, rng.uniform(1.0, 1.8), kinds[k], K, random.Random(k))
    cards = Cards(rng)
    for k in range(4):            # dried herbs tied to the beam, grass round the piers
        cards.hang((-2.35 + k * 1.55, y1 + 0.4, zb - 0.15), 0.6, 0.9, ("lavender", "fern", "nightshade", "twigs")[k], sway=0.05)
    ground_cards(cards, rng, -W, W, y1 - 2.0, y1 + 0.5, 10)
    leaves_done("HutPorch", cards)
    return _dims()


def ground_cards(cards, rng, x0, x1, y0, y1, n, z=0.0, sprites=("grass", "fern")):
    for k in range(n):
        p = (rng.uniform(x0, x1), rng.uniform(y0, y1), z)
        sp = sprites[k % len(sprites)]
        if sp == "fern":
            cards.fronds(p, 5, 0.9, 0.5, "fern", elev=(15, 45))
        else:
            cards.crossed(p, 0.8, 0.9, sp, k=2)


# ================================================================== inside and around: helpers

def sheet(name, fn, nu, nv, mat, key=None, thick=0.03, k=2.0, swatch=None):
    """A cloth or paper sheet: fn(u, v) -> point for u, v in 0..1, nu x nv quads, given `thick` (Solidify). With key, its
    "Spine" UV lays that WitchPrint region over (u, v)."""
    bm = bmesh.new()
    if key or swatch:
        uvl = bm.loops.layers.uv.new("Spine")
        kl = bm.faces.layers.float.new("nh_uvk")
    vs = [[bm.verts.new(tuple(fn(i / nu, j / nv))) for j in range(nv + 1)] for i in range(nu + 1)]
    faces = []
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            f.smooth = True
            faces.append((f, i, j))
    if key or swatch:
        if key:
            u0, v0, u1, v1 = B30.REG["WP_" + key]
        for f, i, j in faces:
            f[kl] = k if key else 0.4
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (u0 + (u1 - u0) * ii / nu, v0 + (v1 - v0) * jj / nv) if key else B30._swatch("WP_" + swatch)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    _finish(ob, mat, 0)
    if thick:
        md = ob.modifiers.new("Solid", "SOLIDIFY")
        md.thickness = thick
        md.offset = 0
        md.use_even_offset = True
    return ob


def wrap_label(name, key, cx, cy, r, zc, h, width, K, face=-PI / 2, n=8):
    """A parchment label wrapped round a jar of radius r (centred at cx, cy), facing `face` (radians, -pi/2 = -Y)."""
    a = width / r

    def fn(u, v):
        t = face - a / 2 + a * u
        return Vector((cx + math.cos(t) * r, cy + math.sin(t) * r, zc - h / 2 + h * v))
    return sheet(name, fn, n, 1, K["wp"], key=key, thick=0.006, k=2.5)


def flame(name, x, y, z, r, h, mat, lean=(0.0, 0.0), seg=8):
    """A licking flame: a teardrop that leans and twists as it rises."""
    prof = [(0, 0), (r * 0.7, h * 0.1), (r, h * 0.3), (r * 0.75, h * 0.6), (r * 0.3, h * 0.88), (0, h)]
    ob = lathe(name, prof, mat, seg=seg, loc=(0, 0, 0))
    for v in ob.data.vertices:
        t = v.co.z / h
        v.co.x += lean[0] * t * t * h
        v.co.y += lean[1] * t * t * h
    ob.matrix_world = T(x, y, z)
    return ob


def toad(prefix, mtx, K, s=1.0):
    """A warty toad sitting (a living one: olive-brown, gold eyes)."""
    st = _mark()
    skin = K["toadskin"]
    blob(f"{prefix}Body", (0, 0, 0.18 * s), 0.25 * s, skin, seg=12, rings=7, scale=(1.0, 1.2, 0.7), jitter=0.06, seed=3)
    blob(f"{prefix}Head", (0, -0.24 * s, 0.24 * s), 0.17 * s, skin, seg=10, rings=6, scale=(1.2, 0.9, 0.7), jitter=0.04, seed=4)
    for sx in (-1, 1):
        sphere(f"{prefix}Eye{sx}", 0.055 * s, (sx * 0.1 * s, -0.3 * s, 0.33 * s), K["toadeye"], seg=8, rings=5)
        sphere(f"{prefix}Pupil{sx}", 0.025 * s, (sx * 0.11 * s, -0.345 * s, 0.34 * s), K["ink"], seg=6, rings=4, scale=(1.6, 0.6, 0.6))
        blob(f"{prefix}Leg{sx}", (sx * 0.24 * s, 0.05 * s, 0.1 * s), 0.12 * s, skin, seg=8, rings=5, scale=(0.8, 1.4, 0.7))
        blob(f"{prefix}Arm{sx}", (sx * 0.15 * s, -0.25 * s, 0.06 * s), 0.06 * s, skin, seg=8, rings=4, scale=(0.8, 0.8, 1.4))
    g = random.Random(5)
    for k in range(10):
        a, b = g.uniform(0, 2 * PI), g.uniform(0.2, 1.2)
        sphere(f"{prefix}Wart{k}", 0.025 * s, (math.cos(a) * 0.22 * s * math.sin(b), math.sin(a) * 0.27 * s * math.sin(b), 0.18 * s + math.cos(b) * 0.17 * s),
               K["toadskin2"], seg=6, rings=3)
    _xform(st, mtx)


# ================================================================== the cauldron

def witch_cauldron(M):
    """The big cauldron on its fire: a cast-iron pot (rim at 3.3, 3.4 across) on three stubby legs over a ring of hearthstones,
    charred logs crossed under it; the brew bubbling up to the rim (Glow, sickly green) with bubbles bursting and a drip down
    the side, flames licking the belly (Glow2); a long stirring paddle, a bone-handled ladle hung on the rim, a toad on a
    stone, logs to hand."""
    K = wk(M)
    rng = RNG(4840)
    for k in range(11):           # the ring of hearthstones
        a = k / 11 * 2 * PI
        rock(f"Hearth{k}", (math.cos(a) * 2.35, math.sin(a) * 2.35, 0.22), (0.75, 0.6, 0.45), K["field"] if k % 3 else K["fielddk"], rng,
             rot=(0, 0, a + rng.uniform(-0.2, 0.2)), bevel=0.15)
    sphere("AshBed", 2.0, (0, 0, 0.0), K["ash"], seg=20, rings=8, scale=(1.0, 1.0, 0.07))
    for k, a in enumerate((0.3, 1.35, 2.4, 3.5, 4.6, 5.5)):       # logs crossed like spokes, charred at the middle
        p0 = (math.cos(a) * 2.0, math.sin(a) * 2.0, 0.35)
        p1 = (math.cos(a) * 0.35, math.sin(a) * 0.35, 0.18)
        pole(f"Log{k}", [p0, tuple((Vector(p0) + Vector(p1)) / 2), p1], 0.2, K["bark"], seed=4841 + k, seg=8)
        sphere(f"Char{k}", 0.21, p1, K["soot"], seg=8, rings=5, scale=(1.4, 1.0, 1.0))
    set_group("Glow2")
    for k in range(9):            # embers among the logs and flames licking up round the pot
        a = k / 9 * 2 * PI + 0.2
        blob(f"Ember{k}", (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.12), 0.16, K["glow2"], seg=8, rings=4, scale=(1.3, 1.0, 0.5), jitter=0.2, seed=k)
    for k in range(10):
        a = k / 10 * 2 * PI + rng.uniform(-0.2, 0.2)
        r = rng.uniform(1.05, 1.45)
        flame(f"Flame{k}", math.cos(a) * r, math.sin(a) * r, 0.15, rng.uniform(0.16, 0.26), rng.uniform(0.7, 1.4), K["glow2"],
              lean=(math.cos(a) * 0.35, math.sin(a) * 0.35))
    set_group("Main")
    z0 = 0.55
    for k in range(3):            # legs
        a = k / 3 * 2 * PI + PI / 2
        cone(f"Leg{k}", 0.2, 0.12, 0.75, (math.cos(a) * 1.05, math.sin(a) * 1.05, 0.38), K["castiron"], verts=8)
    prof = [(0, z0), (0.6, z0 + 0.02), (1.25, z0 + 0.3), (1.62, z0 + 0.85), (1.72, z0 + 1.45), (1.62, z0 + 2.05), (1.45, z0 + 2.45), (1.42, z0 + 2.6),
            (1.58, z0 + 2.7), (1.6, z0 + 2.8), (1.45, z0 + 2.82), (1.32, z0 + 2.62), (1.5, z0 + 2.05), (1.58, z0 + 1.45), (1.48, z0 + 0.85), (1.1, z0 + 0.4),
            (0, z0 + 0.3)]
    lathe("Pot", prof, K["castiron"], seg=40)
    for sx in (-1, 1):            # lugs and the bail
        box(f"Lug{sx}", (0.22, 0.3, 0.32), (sx * 1.62, 0, z0 + 2.45), K["castiron"], bevel=0.05)
    pts = [(math.cos(a) * 1.75, 0, z0 + 2.45 + math.sin(a) * 0.3) for a in [PI * i / 14 for i in range(15)]]
    pts = [(-1.75, 0, z0 + 2.45)] + [(math.cos(a) * 1.75, -math.sin(a) * 0.6, z0 + 2.4 - math.sin(a) * 0.9) for a in [PI * i / 14 for i in range(1, 14)]] + [(1.75, 0, z0 + 2.45)]
    bar("Bail", pts, 0.07, K["iron"], seg=8)
    # the brew: a surface just under the rim, bubbles and a slop over the lip (Glow)
    zb = z0 + 2.55
    set_group("Glow")
    f = noise2(4842)
    sheet("Brew", lambda u, v: Vector((math.cos(u * 2 * PI) * 1.36 * v, math.sin(u * 2 * PI) * 1.36 * v, zb + 0.06 * f(u * 6, v * 3) * v)), 32, 6, K["glow"],
          thick=0.0)
    for k in range(9):
        a, r = rng.uniform(0, 2 * PI), rng.uniform(0.1, 1.1)
        rr = rng.uniform(0.08, 0.24)
        sphere(f"Bubble{k}", rr, (math.cos(a) * r, math.sin(a) * r, zb + 0.02), K["glow"], seg=10, rings=5, scale=(1, 1, 0.65))
    for k in range(3):
        a, r = rng.uniform(0, 2 * PI), rng.uniform(0.3, 1.0)
        hoop(f"Ring{k}", (math.cos(a) * r, math.sin(a) * r, zb + 0.02), rng.uniform(0.15, 0.3), "Z", K["glow"], thick=0.02)
    a = -PI / 2 - 0.4
    pts = [(math.cos(a) * 1.5, math.sin(a) * 1.5, z0 + 2.85), (math.cos(a) * 1.63, math.sin(a) * 1.63, z0 + 2.7), (math.cos(a) * 1.66, math.sin(a) * 1.66, z0 + 2.2),
           (math.cos(a) * 1.73, math.sin(a) * 1.73, z0 + 1.6)]
    bar("Slop", pts, lambda t: 0.1 * (1 - t * 0.6), K["glow"], seg=8)
    sphere("SlopDrop", 0.07, (math.cos(a) * 1.74, math.sin(a) * 1.74, z0 + 1.5), K["glow"], seg=8, rings=5, scale=(1, 1, 1.4))
    set_group("Main")
    # the paddle, the ladle, the toad, logs to hand
    pole("Paddle", [(0.3, 0.4, zb - 0.6), (1.2, 1.3, zb + 1.6), (1.75, 1.85, zb + 3.1)], 0.07, K["plank"], seed=4843, seg=7, taper=0.0)
    box("PaddleBlade", (0.35, 0.08, 0.8), (0.18, 0.25, zb - 0.8), K["plank"], bevel=0.03, rot=(0.5, 0.0, PI / 4))
    s = _mark()
    lathe("LadleCup", [(0, 0), (0.18, 0.02), (0.22, 0.14), (0.2, 0.16), (0.16, 0.05), (0, 0.04)], K["copper"], seg=12)
    pole("LadleHandle", [(0.18, 0, 0.12), (0.2, 0, 0.7), (0.32, 0, 1.05), (0.46, 0, 1.08)], 0.035, K["bonew"], seed=4844, seg=6)
    _xform(s, T(-1.6, -0.9, z0 + 1.75) @ RZ(-2.6))
    rock("ToadStone", (2.75, -1.1, 0.3), (0.8, 0.7, 0.6), K["field"], rng, bevel=0.2)
    toad("Toad", T(2.75, -1.15, 0.58) @ RZ(0.5), K, s=1.0)
    for k in range(3):
        pole(f"Spare{k}", [(-3.6 + k * 0.05, 0.8 + k * 0.42, 0.2 + (k == 2) * 0.36), (-2.4 + k * 0.05, 1.6 + k * 0.42, 0.2 + (k == 2) * 0.36)], 0.19,
             K["bark"], seed=4845 + k, seg=8)
    GLOW["WitchCauldron"] = {"Glow": GREEN, "Glow2": FIRE}
    return _dims()


# ================================================================== the herb-drying rack

def herb_bundle(prefix, top, L, mat, K, cards, sprite, rng):
    """A bundle of herbs hung head-down from `top`: stems tied with twine, the leaves and flowers (cards) below."""
    x, y, z = top
    string(f"{prefix}Tie", (x, y, z), (x, y, z - 0.3), K, r=0.015)
    for k in range(6):
        a = k / 6 * 2 * PI
        bar(f"{prefix}Stem{k}", [(x + math.cos(a) * 0.03, y + math.sin(a) * 0.03, z - 0.3), (x + math.cos(a) * 0.1, y + math.sin(a) * 0.1, z - 0.3 - L * 0.5)],
            0.012, mat, seg=4)
    hoop(f"{prefix}Wrap", (x, y, z - 0.35), 0.05, "Z", K["twine"], thick=0.015)
    for k in range(3):
        cards.hang((x, y, z - 0.35), 0.55, L, sprite, yaw=k * PI / 3 + rng.uniform(-0.2, 0.2), sway=0.08)


def herb_beam_rack(M):
    """A ceiling piece: a crooked ladder of hazel poles (7.6 long) slung from the rafters on four ropes, hung with bundles of
    drying herbs (lavender, fern, nightshade, poppy heads, rose leaves, twigs), a braid of garlic, a string of chillies, a
    string of dried mushrooms and a sickle on a hook. Pivot at the bottom centre (the lowest tips); the ropes' tops are at 5.0
    (tie them to a beam or rafters there)."""
    K = wk(M)
    rng = RNG(4850)
    cards = Cards(rng)
    zr = 2.7
    for sy in (-1, 1):
        pole(f"Rail{sy}", crooked((-3.8, sy * 0.55, zr), (3.8, sy * 0.55, zr + 0.05), 0.08, 4851 + sy, n=8, perp=(0, 0, 1)), 0.1, K["hazel"], seed=4851 + sy,
             seg=7, taper=0.1)
    for k in range(6):
        x = -3.3 + k * 1.32
        pole(f"Rung{k}", [(x, -0.62, zr + 0.02), (x + 0.04, 0, zr + 0.06), (x, 0.62, zr + 0.02)], 0.06, K["hazel"], seed=4853 + k, seg=6)
        hoop(f"Lash{k}a", (x, -0.55, zr), 0.11, "X", K["twine"], thick=0.015)
    for k, x in enumerate((-3.4, 3.4)):
        for sy in (-1, 1):
            string(f"Rope{k}{sy}", (x, sy * 0.55, zr + 0.08), (x * 0.95, sy * 0.25, 5.0), K, r=0.035, mat=K["rope"])
        pole(f"Toggle{k}", [(x * 0.95 - 0.2, 0, 5.0), (x * 0.95 + 0.2, 0, 5.0)], 0.04, K["hazel"], seed=k, seg=5)
    sprites = ["lavender", "fern", "nightshade", "poppy", "rose_leaves", "twigs", "lavender", "fern", "grass", "nightshade"]
    mats = [K["lav"], K["herbg"], K["herbg"], K["herbb"], K["herbg"], K["herbb"], K["lav"], K["herbg"], K["herbb"], K["herbg"]]
    for k in range(10):
        x = -3.5 + k * 0.78 + rng.uniform(-0.1, 0.1)
        sy = (-1 if k % 2 else 1) * 0.55
        herb_bundle(f"H{k}", (x, sy, zr - 0.05), rng.uniform(1.0, 1.6), mats[k], K, cards, sprites[k], rng)
    # a braid of garlic
    x0 = -1.98
    pts = [(x0 + 0.04 * math.sin(i), 0.0, zr - 0.1 - i * 0.12) for i in range(16)]
    bar("GarlicCord", pts, 0.04, K["strawdk"], seg=5)
    for i in range(1, 14):
        a = i * 2.3
        lathe(f"Garlic{i}", [(0, 0), (0.1, 0.03), (0.16, 0.13), (0.11, 0.24), (0.03, 0.32), (0, 0.34)], K["garlic"], seg=10, flute=(8, 0.08),
              loc=(x0 + math.cos(a) * 0.14, math.sin(a) * 0.14, zr - 0.3 - i * 0.12))
    # chillies and mushrooms on threads
    string("ChilliThread", (1.98, -0.55, zr - 0.05), (1.98, -0.55, zr - 1.9), K)
    for i in range(14):
        a = i * 2.1
        cone(f"Chilli{i}", 0.045, 0.005, 0.32, (1.98 + math.cos(a) * 0.08, -0.55 + math.sin(a) * 0.08, zr - 0.3 - i * 0.11), K["chilli"], verts=8,
             rot=(math.sin(a) * 0.5 + PI, math.cos(a) * 0.5, 0))
    string("MushThread", (0.66, 0.55, zr - 0.05), (0.66, 0.55, zr - 1.7), K)
    for i in range(8):
        lathe(f"Mush{i}", [(0, 0), (0.14, 0.01), (0.16, 0.05), (0.1, 0.09), (0, 0.1)], K["mush"], seg=10, loc=(0.66, 0.55, zr - 0.35 - i * 0.17),
              jitter=(0.1, i))
    # a sickle on an S-hook
    tube("Hook", [(3.0, 0.0, zr - 0.05), (3.05, 0.0, zr - 0.25), (2.95, 0.0, zr - 0.35), (3.0, 0.0, zr - 0.45)], 0.02, K["iron"])
    blade = [(math.cos(a) * 0.55, math.sin(a) * 0.55) for a in [PI * (0.1 + 0.85 * i / 12) for i in range(13)]] + \
            [(math.cos(a) * 0.44 + 0.06, math.sin(a) * 0.4) for a in [PI * (0.95 - 0.85 * i / 12) for i in range(13)]]
    prism("Sickle", [(3.0 + u - 0.0, zr - 1.1 + w) for u, w in blade], 0.0, 0.03, K["copper"], plane="XZ")
    pole("SickleGrip", [(3.53, 0.0, zr - 1.05), (3.6, 0.0, zr - 1.55)], 0.05, K["bonew"], seed=9, seg=6)
    leaves_done("HerbBeamRack", cards)
    s = 0
    ground_at_zero(s)
    return _dims()


# ================================================================== the jar shelf

JAR_FILLS = ["herbg", "lav", "soot", "mush", "rootw", "feather", "herbb", "web", "field", "gourdy", "featherb", "toadspot"]


def witch_jar_shelf(M):
    """A wall piece: three crooked plank shelves (5.4 wide, the middle one sagging) on forked-branch brackets, crowded with
    hand-blown jars and bottles, every one hand-labelled on a parchment tag or a wrapped label (Moonwort, Wolfsbane, Black Salt,
    Moon Dew, Toadstool, Crow Quills, Mandrake, Hemlock ...), corked, waxed or tied with cloth; one jar of moon dew and one of
    glow-worms glow (Glow), a bird skull and a candle stub on top, herbs hung under the bottom shelf, a cobweb in a corner.
    Back on y = 0; pivot at the bottom of the lowest bracket (hang it at about 2.4)."""
    K = wk(M)
    rng = RNG(4860)
    g = random.Random(4861)
    cards = Cards(rng)
    shelves = [(0.9, 0.0, 0.0), (2.6, 0.14, -0.05), (4.3, 0.0, 0.04)]      # (z, sag, tilt)
    W = 5.4
    for k, (z, sag, tilt) in enumerate(shelves):
        hewn(f"Shelf{k}", (-W / 2, -0.6, z + tilt), (W / 2, -0.6, z - tilt), 1.15, 0.16, K["plank"] if k != 1 else K["timber"], bow=(0, 0, -sag),
             seed=4862 + k, jit=0.012, cham=0.03, n=12)
        for sx in (-1, 1):       # forked branch brackets
            x = sx * (W / 2 - 0.55)
            pole(f"Br{k}{sx}", [(x, -0.05, z - 0.85), (x, -0.4, z - 0.35), (x + sx * 0.05, -1.05, z - 0.1)], 0.07, K["hazel"], seed=4865 + k * 2 + sx, seg=6)
            pole(f"BrUp{k}{sx}", [(x, -0.05, z - 0.85), (x, -0.08, z - 0.06)], 0.08, K["hazel"], seed=4870 + k * 2 + sx, seg=6)
            sphere(f"Peg{k}{sx}", 0.06, (x, -0.06, z - 0.6), K["plank"], seg=6, rings=4)
    li = 0
    for k, (z, sag, tilt) in enumerate(shelves):
        x = -W / 2 + 0.35
        while x < W / 2 - 0.4:
            res = {1: [(-0.15, 0.65)], 2: [(-2.0, -1.2), (0.8, 3.0)]}.get(k, [])
            hit = next((b for a, b in res if a - 0.3 < x < b), None)
            if hit is not None:
                x = hit + 0.05
                continue
            t = (x + W / 2) / W
            zz = z + 0.08 - sag * math.sin(PI * t) + tilt * (1 - 2 * t)
            kind = g.random()
            y = -0.6 + g.uniform(-0.15, 0.15)
            if kind < 0.45:          # a jar with contents and a wrapped label
                r, h = g.uniform(0.24, 0.34), g.uniform(0.6, 0.95)
                fill = K[JAR_FILLS[li % len(JAR_FILLS)]]
                jar(f"J{k}{li}", x + r, y, zz, r, h, K, fill, fill_k=g.uniform(0.45, 0.85), lid=("cork", "cloth", "wax")[li % 3])
                wrap_label(f"JL{k}{li}", f"Label{li % 16}", x + r, y, r + 0.012, zz + h * 0.45, 0.28, 0.42, K)
                x += 2 * r + 0.1
            elif kind < 0.8:         # a bottle with a tag on a string round its neck
                r, h = g.uniform(0.13, 0.2), g.uniform(0.6, 1.0)
                shape = g.randrange(4)
                bottle(f"B{k}{li}", x + r, y, zz, r, h, (K["bottle"], K["bottleb"], K["bottlev"])[li % 3], K, shape=shape)
                label_tag(f"BT{k}{li}", f"Label{li % 16}", 0.36, 0.24, T(x + r + 0.03, y - r - 0.04, zz + h * 0.62) @ RZ(g.uniform(-0.3, 0.3)) @ RY(g.uniform(-0.2, 0.2)),
                          K)
                string(f"BS{k}{li}", (x + r - 0.1, y - r * 0.4, zz + h * 0.85), (x + r + 0.03, y - r - 0.03, zz + h * 0.62 + 0.12), K, r=0.008)
                x += 2 * r + 0.1
            else:                    # a glazed crock with a slate lid and a tag
                r, h = g.uniform(0.25, 0.32), g.uniform(0.45, 0.6)
                lathe(f"C{k}{li}", [(0, 0), (r * 0.8, 0), (r, h * 0.3), (r * 0.95, h * 0.85), (r * 0.75, h), (r * 0.7, h * 0.95), (0, h * 0.95)],
                      K["crock"] if li % 2 else K["crockdk"], seg=14, loc=(x + r, y, zz))
                cyl(f"CL{k}{li}", r * 0.78, 0.06, (x + r, y, zz + h), K["fielddk"], verts=12, bevel=0.015)
                label_tag(f"CT{k}{li}", f"Label{li % 16}", 0.4, 0.26, T(x + r, y - r - 0.01, zz + h * 0.5) @ RX(0.05), K)
                x += 2 * r + 0.1
            li += 1
    set_group("Glow")         # moon dew and glow-worms
    lathe("MoonDew", [(0, 2.68), (0.2, 2.68), (0.21, 3.15), (0, 3.18)], K["glow"], seg=12, loc=(0.0, 0, 0))
    P.PARTS[-1].matrix_world = T(0.25, -0.55, 0)
    for k in range(9):
        sphere(f"Worm{k}", 0.04, (-1.6 + g.uniform(-0.15, 0.15), -0.55 + g.uniform(-0.15, 0.15), 4.5 + g.uniform(0.0, 0.45)), K["glow"], seg=6, rings=4)
    set_group("Glass")
    lathe("MoonDewJar", [(0, 2.66), (0.26, 2.66), (0.27, 3.3), (0.2, 3.4), (0, 3.4)], K["glass"], seg=14)
    P.PARTS[-1].matrix_world = T(0.25, -0.55, 0)
    lathe("WormJar", [(0, 0), (0.28, 0), (0.29, 0.6), (0.2, 0.68), (0, 0.68)], K["glass"], seg=14, loc=(-1.6, -0.55, 4.38))
    set_group("Main")
    cyl("WormJarLid", 0.2, 0.1, (-1.6, -0.55, 5.1), K["linen"], verts=12, bevel=0.03)
    skull_small("BirdSkull", T(1.9, -0.6, 4.6) @ RZ(0.5), K, s=0.45)
    candle("Stub", 1.1, -0.55, 4.38, 0.12, 0.25, K, drips=3, flame=False, mat=K["waxdk"])
    cobweb("Web", (-W / 2 + 0.45, -0.08, 4.36), (1, 0, -0.15), (0.1, -1, -0.5), 0.9, K)
    for k in range(3):
        x = -1.5 + k * 1.5
        herb_bundle(f"Hang{k}", (x, -0.9, 0.82), 0.9, (K["lav"], K["herbg"], K["herbb"])[k], K, cards, ("lavender", "fern", "twigs")[k], rng)
    leaves_done("WitchJarShelf", cards)
    ground_at_zero(0)
    GLOW["WitchJarShelf"] = {"Glow": GREEN, "Glass": (190, 215, 195)}
    return _dims()


# ================================================================== the broom corner

def besom(prefix, base, top, K, rng, L_brush=1.6, n=70, flying=False):
    """A besom: a crooked handle from `top` down to the brush at `base`, birch twigs bound in three willow bands."""
    base, top = Vector(base), Vector(top)
    d = (top - base).normalized()
    pole(f"{prefix}Handle", crooked(tuple(base + d * 0.2), tuple(top), 0.12, int(top.x * 100) % 997, n=8), 0.09, K["pole" if flying else "plank"],
         seed=int(top.y * 50) % 997, seg=8, taper=0.1)
    side = d.orthogonal().normalized()
    other = d.cross(side)
    for k in range(n):
        a = rng.uniform(0, 2 * PI)
        r0 = rng.uniform(0.02, 0.16)
        spread = rng.uniform(0.25, 0.5)
        p0 = base + d * 0.35 + (side * math.cos(a) + other * math.sin(a)) * r0
        p1 = base - d * L_brush * rng.uniform(0.85, 1.05) + (side * math.cos(a) + other * math.sin(a)) * (r0 + spread)
        mid = p0.lerp(p1, 0.5) + (side * math.cos(a) + other * math.sin(a)) * 0.05
        bar(f"{prefix}Twig{k}", [tuple(p0), tuple(mid), tuple(p1)], lambda t: 0.018 * (1 - t * 0.6), K["herbb"] if k % 3 else K["hazel"], seg=3, caps=False)
    for j, t in enumerate((0.25, 0.0, -0.3)):
        c = base + d * t
        rr = 0.2 + (0.05 if t < 0 else 0)
        pts = [tuple(c + (side * math.cos(a) + other * math.sin(a)) * rr) for a in [i / 12 * 2 * PI for i in range(13)]]
        bar(f"{prefix}Band{j}", pts, 0.035, K["hazel"], seg=5, caps=False)
    if flying:     # a carved crescent near the top, a ribbon and a tiny bell
        c = top - d * 0.6
        hoop(f"{prefix}Collar", tuple(c), 0.11, "Z", K["copper"], thick=0.02)
        strip(f"{prefix}Ribbon", [tuple(c + side * 0.1), tuple(c + side * 0.25 - d * 0.4), tuple(c + side * 0.2 - d * 0.8)], 0.07, tuple(other), K["woolv"],
              thick=0.01)
        lathe(f"{prefix}Bell", [(0, 0.1), (0.03, 0.09), (0.045, 0.03), (0.06, 0.0), (0, 0.01)], K["brass"], seg=10, loc=tuple(c + side * 0.18 - d * 0.95))


def broom_corner(M):
    """A corner piece for an inside corner (the walls on y = 0 behind and x = 0 to the left; pivot on the corner at the floor,
    the piece fills +X / -Y): the witch's flying besom (a crooked ash handle with a copper collar, a violet ribbon and a bell)
    leaning in the corner, a straw sweeping broom beside it, a hearth brush and a dustpan on a peg board, a bucket of kindling,
    a pile of swept leaves and dust, a cobweb across the corner."""
    K = wk(M)
    rng = RNG(4880)
    g = random.Random(4881)
    hewn("PegBoard", (0.3, -0.08, 5.0), (3.4, -0.08, 4.96), 0.16, 0.45, K["plank"], seed=4882, jit=0.01)
    for k, x in enumerate((0.9, 1.9, 2.9)):
        pole(f"Peg{k}", [(x, -0.15, 5.0), (x, -0.5, 5.05), (x, -0.55, 5.15)], 0.06, K["planklt"], seed=k, seg=6)
    besom("Fly", (0.75, -0.75, 0.0 + 1.55), (0.12, -0.15, 6.6), K, rng, L_brush=1.55, n=80, flying=True)
    besom("Sweep", (1.75, -0.7, 1.15), (1.0, -0.15, 5.0), K, rng, L_brush=1.1, n=50)
    # the hearth brush and dustpan on the pegs
    s = _mark()
    pole("BrushHandle", [(0, 0, 0), (0, 0, -0.7)], 0.05, K["planklt"], seed=1, seg=6)
    for k in range(18):
        a = k / 18 * 2 * PI
        bar(f"Bristle{k}", [(math.cos(a) * 0.05, math.sin(a) * 0.05, -0.65), (math.cos(a) * 0.12, math.sin(a) * 0.12, -1.25)], 0.016, K["strawdk"], seg=3)
    hoop("BrushBand", (0, 0, -0.7), 0.09, "Z", K["twine"], thick=0.02)
    _xform(s, T(1.9, -0.52, 5.05))
    s = _mark()
    prism("Pan", [(-0.4, 0.0), (0.4, 0.0), (0.33, 0.6), (-0.33, 0.6)], 0, 0.04, K["tin"], plane="XZ", bevel=0.01)
    pole("PanHandle", [(0, 0, 0.6), (0, 0, 1.0)], 0.04, K["planklt"], seed=2, seg=6)
    hoop("PanLoop", (0, 0, 1.08), 0.06, "Y", K["twine"], thick=0.012)
    _xform(s, T(2.9, -0.45, 3.95))
    # the kindling bucket, the swept pile, the cobweb
    bx, by = 2.6, -1.4
    lathe("Bucket", [(0, 0), (0.45, 0), (0.52, 0.9), (0.48, 0.92), (0.42, 0.08), (0, 0.08)], K["plank"], seg=18, loc=(bx, by, 0))
    for z in (0.15, 0.75):
        hoop(f"BHoop{z}", (bx, by, z), 0.46 + z * 0.08, "Z", K["iron"], thick=0.022)
    for k in range(9):
        a = rng.uniform(0, 2 * PI)
        pole(f"Kind{k}", [(bx + math.cos(a) * 0.2, by + math.sin(a) * 0.2, 0.1), (bx + math.cos(a) * 0.32 + g.uniform(-0.1, 0.1), by + math.sin(a) * 0.32, 1.4 + g.uniform(-0.2, 0.3))],
             0.04, K["hazel"], seed=k, seg=5)
    sphere("Dust", 0.6, (1.7, -2.3, 0.0), K["soil"], seg=12, rings=6, scale=(1.3, 0.9, 0.22))
    cards = Cards(rng)
    for k in range(10):
        p = Vector((1.7 + rng.uniform(-0.7, 0.7), -2.3 + rng.uniform(-0.5, 0.5), 0.07))
        ax, ay = frame(Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1)), roll=rng.uniform(0, 6.28), up=Vector((0, 1, 0)))
        cards.add(tuple(p), ax, ay, 0.45, 0.45, ("crabapple", "twigs", "rose_leaves")[k % 3], "fill", nrm=UP)
    cobweb("Web", (0.04, -0.04, 6.9), (1, 0, -0.3), (0, -1, -0.3), 1.4, K, n=7, rings=4)
    leaves_done("BroomCorner", cards)
    return _dims()


# ================================================================== the spellbook lectern

def spell_lectern(M):
    """A lectern grown, not made: three twisted roots rising from a stump with spreading feet into a crooked book rest (4.3 at
    its front edge); the open spellbook on it (a moon circle and a finding charm on the left page, moonwort and rue on the
    right), the sigils on the left page glowing faint violet (Glow), a ribbon marker; a fat candle on a side branch in a pool
    of wax (Glow2 flame), an inkpot and a raven quill."""
    K = wk(M)
    rng = RNG(4890)
    lathe("Stump", [(0, 0), (0.95, 0), (0.8, 0.25), (0.6, 0.7), (0.55, 1.0), (0, 1.0)], K["bark"], seg=14, jitter=(0.08, 4891))
    for k in range(6):          # spreading root feet
        a = k / 6 * 2 * PI + 0.3
        pts = [(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.6), (math.cos(a) * 1.0, math.sin(a) * 1.0, 0.25), (math.cos(a) * 1.5, math.sin(a) * 1.5, 0.05)]
        pole(f"Root{k}", pts, 0.2, K["bark"], seed=4892 + k, seg=7, taper=0.6)
    for k in range(3):          # three roots twisting round each other up to the rest
        pts = []
        for i in range(13):
            t = i / 12
            a = k * 2 * PI / 3 + t * 2.4 * PI
            r = 0.28 - 0.1 * math.sin(PI * t)
            pts.append((math.cos(a) * r, math.sin(a) * r - 0.1 * t, 0.8 + t * 2.8))
        pole(f"Twist{k}", pts, 0.18, K["rootw"], seed=4895 + k, seg=8, taper=0.2)
    # the rest: a crooked plank board tilted toward the reader (-Y), a lip at its foot
    tilt = 0.42
    s = _mark()
    hewn("Rest", (-1.25, 0, 0.0), (1.25, 0, 0.0), 1.9, 0.16, K["plank"], seed=4898, jit=0.012, cham=0.03)
    hewn("Lip", (-1.2, -0.98, 0.1), (1.2, -0.98, 0.12), 0.12, 0.22, K["timberdk"], seed=4899, jit=0.01)
    for sx in (-1, 1):
        pole(f"Prop{sx}", [(sx * 0.3, 0.2, -0.1), (sx * 0.6, 0.6, -0.55)], 0.1, K["rootw"], seed=sx, seg=6)
    # the open book: two leather boards, page blocks curving up to the gutter, the printed pages
    for sx in (-1, 1):
        box(f"Board{sx}", (1.08, 1.5, 0.05), (sx * 0.56, 0.0, 0.11), K["leather"], bevel=0.02)
        for sy in (-1, 1):
            box(f"Corner{sx}{sy}", (0.16, 0.16, 0.06), (sx * 1.03, sy * 0.68, 0.115), K["brass"], bevel=0.01)

    def page(sx):
        def fn(u, v):
            x = sx * (0.04 + u * 0.98)
            z = 0.22 + 0.1 * math.sin(PI * u) ** 0.7 * (1 - u * 0.3) - 0.05 * u
            return Vector((x, -0.68 + v * 1.36, z))
        return fn
    for sx, key in ((-1, "PageL"), (1, "PageR")):
        sheet(f"Page{sx}", page(sx), 12, 4, K["wp"], key=key, thick=0.0, k=3.0)
        P.PARTS[-1]["flipu"] = 1
        ob = P.PARTS[-1]
        if sx < 0:       # u runs from the gutter outward; the left page's image runs left to right
            uv = ob.data.uv_layers["Spine"]
            u0, v0, u1, v1 = B30.REG["WP_PageL"]
            for d in uv.data:
                d.uv = (u0 + u1 - d.uv[0], d.uv[1])
        sheet(f"Block{sx}", lambda u, v, sx=sx: Vector((sx * (0.04 + u * 0.98), -0.68 + v * 1.36, 0.14 + (0.08 * math.sin(PI * u) ** 0.7 * (1 - u * 0.3)))),
              8, 2, K["paper"], thick=0.08)
    strip("Ribbon", [(0.0, 0.1, 0.25), (0.05, -0.4, 0.24), (0.08, -0.75, 0.1), (0.1, -0.85, -0.25)], 0.06, (1, 0, 0), K["woolv"], thick=0.008)
    # the glowing sigils: the moon circle's two rings and the crescent on the left page
    set_group("Glow")
    fnL = page(-1)
    u0, v0 = 0.5, 1 - 330 / 900          # the circle's centre on the page image (cx = W/2, cy = 330 of 900)
    for rk, rr in enumerate((250 / 700, 205 / 700)):
        pts = []
        for i in range(33):
            a = i / 32 * 2 * PI
            uu = u0 + math.cos(a) * rr * 0.98
            vv = v0 + math.sin(a) * rr * 0.98 * 700 / 900
            p = fnL(1 - uu, vv)
            pts.append(tuple(p + Vector((0, 0, 0.012))))
        bar(f"SigilRing{rk}", pts, 0.012, K["glow"], seg=4, caps=False)
    pts = []
    for i in range(17):
        a = i / 16 * 2 * PI
        p = fnL(1 - (u0 + math.cos(a) * 0.065), v0 + math.sin(a) * 0.065 * 700 / 900)
        pts.append(tuple(p + Vector((0, 0, 0.012))))
    bar("SigilMoon", pts, 0.014, K["glow"], seg=4, caps=False)
    set_group("Main")
    lathe("Inkpot", [(0, 0), (0.12, 0), (0.14, 0.1), (0.08, 0.16), (0.07, 0.2), (0, 0.2)], K["crockdk"], seg=10, loc=(1.12, -0.78, 0.08))
    feather("Quill", (1.1, -0.76, 0.24), (0.2, 0.3, 0.9), 0.85, K, w=0.09, curl=0.1)
    _xform(s, T(0, 0.05, 3.75) @ RX(tilt))
    # the candle on a side branch, the inkpot and quill on the rest's corner
    pole("Arm", [(0.3, 0.1, 2.4), (0.9, 0.0, 2.75), (1.55, -0.1, 2.85)], 0.12, K["rootw"], seed=4900, seg=7)
    cyl("Saucer", 0.42, 0.08, (1.6, -0.1, 2.92), K["rootw"], verts=14, bevel=0.03)
    lathe("WaxPool", [(0, 0), (0.42, 0), (0.44, 0.03), (0.3, 0.06), (0, 0.06)], K["wax"], seg=14, loc=(1.6, -0.1, 2.95), jitter=(0.08, 3))
    candle("Candle", 1.6, -0.1, 2.98, 0.2, 0.75, K, drips=6)
    bar("WaxRun", [(1.95, -0.1, 2.95), (2.0, -0.1, 2.75), (1.98, -0.12, 2.55)], lambda t: 0.04 * (1 - t * 0.7), K["wax"], seg=5)
    GLOW["SpellLectern"] = {"Glow": VIOLET, "Glow2": FIRE}
    return _dims()


# ================================================================== bone and glass wind chimes

def bone_chimes(M):
    """Wind chimes for the porch: a crooked ring of driftwood hung on three cords from a loop, strung with bird bones,
    vertebrae, sea-glass and bottle glass shards (Glass), little copper bells and feathers, a hag stone in the middle with a
    green bead under it. A hanging piece: pivot at the bottom centre (the lowest tip); hang its loop (at 4.0) from a hook."""
    K = wk(M)
    rng = RNG(4910)
    g = random.Random(4911)
    zr = 2.9
    pts = [(math.cos(a) * 0.95 * (1 + 0.06 * math.sin(a * 3)), math.sin(a) * 0.95 * (1 + 0.06 * math.cos(a * 2)), zr + 0.05 * math.sin(a * 2))
           for a in [i / 24 * 2 * PI for i in range(25)]]
    bar("Ring", pts, lambda t: 0.08 + 0.02 * math.sin(t * 17), K["deadwood"], seg=7)
    for k in range(3):
        a = k / 3 * 2 * PI
        string(f"Cord{k}", (math.cos(a) * 0.95, math.sin(a) * 0.95, zr + 0.05), (0, 0, 3.9), K, r=0.014)
    hoop("Loop", (0, 0, 4.0), 0.1, "Y", K["twine"], thick=0.02)
    n = 10
    for k in range(n):
        a = k / n * 2 * PI + 0.15
        x, y = math.cos(a) * 0.92, math.sin(a) * 0.92
        L = g.uniform(0.6, 1.3)
        zb = zr - L
        string(f"S{k}", (x, y, zr), (x, y, zb), K, r=0.009)
        kind = k % 5
        if kind == 0:      # a bird bone
            pole(f"Bone{k}", [(x, y, zb), (x, y, zb - 0.75)], 0.035, K["bonew"], seed=k, seg=6, knob=0.0)
            for zz in (zb, zb - 0.75):
                sphere(f"Knob{k}{zz:.1f}", 0.055, (x, y, zz), K["bonew"], seg=8, rings=5, scale=(1, 0.8, 0.7))
        elif kind == 1:    # three vertebrae
            for j in range(3):
                zz = zb - j * 0.2
                lathe(f"Vert{k}{j}", [(0, 0), (0.08, 0.0), (0.09, 0.05), (0.08, 0.1), (0, 0.1)], K["bonew"], seg=8, loc=(x, y, zz - 0.1))
                for d in (-1, 1):
                    cone(f"Proc{k}{j}{d}", 0.025, 0.005, 0.18, (x + d * 0.12, y, zz - 0.05), K["bonew"], verts=5, rot=(0, d * PI / 2, 0))
        elif kind == 2:    # glass shards
            set_group("Glass")
            for j in range(2):
                pp = [(g.uniform(-0.12, -0.05), 0), (g.uniform(0.05, 0.12), g.uniform(-0.05, 0.05)), (g.uniform(0.0, 0.08), -g.uniform(0.3, 0.45)),
                      (g.uniform(-0.1, 0.0), -g.uniform(0.2, 0.35))]
                prism(f"Shard{k}{j}", [(x + u, zb - j * 0.42 + w) for u, w in pp], y, 0.03, K["glass"], plane="XZ")
            set_group("Main")
        elif kind == 3:    # a copper bell
            lathe(f"Bell{k}", [(0, 0.22), (0.05, 0.21), (0.08, 0.1), (0.12, 0.0), (0.11, -0.01), (0, 0.0)], K["copper"], seg=12, loc=(x, y, zb - 0.22))
            sphere(f"Clapper{k}", 0.03, (x, y, zb - 0.25), K["iron"], seg=6, rings=4)
        else:              # feathers
            for j in range(2):
                feather(f"Fe{k}{j}", (x, y, zb), (0.25 * (j - 0.5), 0.1, -1), 0.6, K, w=0.08, mat=K["feather"] if j else K["featherb"])
    string("Mid", (0, 0, 3.9), (0, 0, 1.2), K, r=0.014)
    rock("HagStone", (0, 0, 1.0), (0.42, 0.24, 0.36), K["field"], rng, bevel=0.2)
    hoop("HagHole", (0.03, -0.12, 1.02), 0.07, "Y", K["soot"], thick=0.03)
    string("MidLow", (0, 0, 0.82), (0, 0, 0.35), K, r=0.01)
    set_group("Glass")
    sphere("Bead", 0.12, (0, 0, 0.22), K["glass"], seg=12, rings=8)
    set_group("Main")
    ground_at_zero(0)
    GLOW["BoneChimes"] = {"Glass": (150, 220, 170)}
    return _dims()


# ================================================================== the hearth and kettle

def hearth_kettle(M):
    """A wall piece (back on y = 0, standing on the floor): a fieldstone hearth 7.2 wide under a soot-black oak lintel carved
    with marks, the fire opening 4.2 wide and 3.7 tall, the stone breast rising to 10.5; a raised hearthstone, iron firedogs,
    logs and embers (Glow2) with low flames, an iron crane swung over the fire with a soot-black kettle on a pot hook; a mantel
    shelf of crocks, a candle stub and drying herbs; bellows and a toasting fork at the side, a basket of logs."""
    K = wk(M)
    rng = RNG(4920)
    W, D = 7.2, 2.6
    ow, oh = 4.2, 3.7
    rb = K["rubble"]
    rock("HearthStone", (0, -D / 2 - 0.6, 0.18), (W + 0.6, D + 1.4, 0.36), K["fielddk"], rng, rot=(0, 0, 0.01), bevel=0.08)
    for sx in (-1, 1):
        jw = (W - ow) / 2
        box(f"Jamb{sx}", (jw, D, oh), (sx * (ow / 2 + jw / 2), -D / 2, 0.36 + oh / 2), rb, bevel=0.06)
        for k in range(4):
            long = (k + (sx > 0)) % 2
            rock(f"Quoin{sx}{k}", (sx * (W / 2 - (0.4 if long else 0.3)), -D + 0.05, 0.75 + k * 0.85), (0.85 if long else 0.6, 0.35, 0.7), K["field"], rng,
                 bevel=0.12)
    box("Back", (ow + 0.2, 0.5, oh), (0, -0.25, 0.36 + oh / 2), K["soot"], bevel=0.04)
    box("Throat", (ow, D - 0.5, 0.4), (0, -D / 2 + 0.25, 0.36 + oh + 0.2), K["soot"], bevel=0.02)
    hewn("Lintel", (-W / 2 - 0.2, -D + 0.3, 0.36 + oh + 0.35), (W / 2 + 0.2, -D + 0.3, 0.36 + oh + 0.28), 0.75, 0.7, K["sooty"], bow=(0, 0, 0.08),
         seed=4921, jit=0.03, n=14)
    for k, x in enumerate((-2.4, -1.5, 1.2, 2.5)):     # marks cut into the lintel (witch marks: a daisy wheel, Vs, a mesh)
        pprism(f"Mark{k}", "WP_Sigil" + str((1, 3, 5, 0)[k]), [(-0.25, -0.25), (0.25, -0.25), (0.25, 0.25), (-0.25, 0.25)], 0.008,
               T(x, -D + 0.3 - 0.385, 0.36 + oh + 0.32), K["wp"], edge="WP_wood")
    zt = 0.36 + oh + 0.7
    prism("Breast", [(-W / 2 + 0.2, zt), (W / 2 - 0.2, zt), (2.2, 8.6), (1.9, 10.5), (-1.9, 10.5), (-2.2, 8.6)], -1.05, 2.1, rb, plane="XZ", bevel=0.05)
    for k in range(14):
        z = rng.uniform(zt + 0.4, 10.0)
        hw = 3.4 - (z - zt) * 0.28
        rock(f"Face{k}", (rng.uniform(-hw + 0.6, hw - 0.6), -2.12, z), (rng.uniform(0.5, 0.85), 0.16, rng.uniform(0.35, 0.5)), K["field"], rng, bevel=0.15)
    # the mantel shelf with its crocks, candle and herbs
    hewn("Mantel", (-W / 2 + 0.1, -D - 0.1, zt + 0.12), (W / 2 - 0.1, -D - 0.1, zt + 0.12), 0.9, 0.16, K["plank"], seed=4922, jit=0.01)
    for k, (x, r, h, m) in enumerate(((-2.7, 0.3, 0.65, "crock"), (-2.05, 0.22, 0.45, "crockdk"), (2.3, 0.28, 0.55, "crock"))):
        lathe(f"Crock{k}", [(0, 0), (r * 0.8, 0), (r, h * 0.35), (r * 0.9, h * 0.85), (r * 0.65, h), (r * 0.7, h * 1.05), (0, h)], K[m], seg=14,
              loc=(x, -D - 0.1, zt + 0.2))
    candle("Stub", 1.6, -D - 0.1, zt + 0.2, 0.13, 0.3, K, drips=3, flame=False, mat=K["waxdk"])
    toad("Carved", T(-0.6, -D - 0.1, zt + 0.2) @ RZ(0.3), {**K, "toadskin": K["planklt"], "toadskin2": K["plank"], "toadeye": K["plank"]}, s=0.8)
    cards = Cards(rng)
    for k in range(3):
        herb_bundle(f"Hb{k}", (-0.2 + k * 0.8, -D - 0.5, zt + 0.05), 0.8, (K["herbg"], K["lav"], K["herbb"])[k], K, cards, ("fern", "lavender", "twigs")[k], rng)
    # the fire: firedogs, logs, embers and low flames
    yf = -D / 2 - 0.2
    for sx in (-1, 1):
        x = sx * 1.1
        tube(f"Dog{sx}", [(x, yf - 0.6, 0.36), (x, yf - 0.6, 0.95), (x, yf - 0.7, 1.1)], 0.06, K["iron"], poly=True)
        tube(f"DogBar{sx}", [(x, yf - 0.6, 0.6), (x, yf + 0.9, 0.55)], 0.05, K["iron"], poly=True)
        sphere(f"DogKnob{sx}", 0.1, (x, yf - 0.72, 1.15), K["iron"], seg=8, rings=5)
    for k, (dx, dz, rot) in enumerate(((-0.1, 0.75, 0.1), (0.3, 0.78, -0.15), (0.0, 1.12, 0.05))):
        pole(f"Log{k}", [(-1.6 + dx, yf + 0.2, dz), (0 + dx, yf + 0.2 + rot, dz + 0.02), (1.6 + dx, yf + 0.2, dz)], 0.24, K["bark"], seed=4923 + k, seg=8)
        sphere(f"LogChar{k}", 0.25, (dx, yf + 0.2 + rot, dz - 0.05), K["soot"], seg=8, rings=5, scale=(2.2, 1.0, 0.9))
    sphere("Ash", 1.4, (0, yf + 0.2, 0.36), K["ash"], seg=16, rings=6, scale=(1.3, 0.8, 0.12))
    set_group("Glow2")
    for k in range(8):
        blob(f"Ember{k}", (rng.uniform(-1.2, 1.2), yf + rng.uniform(-0.2, 0.6), 0.45), 0.14, K["glow2"], seg=8, rings=4, scale=(1.3, 1.0, 0.5), jitter=0.2, seed=k)
    for k in range(7):
        flame(f"Flame{k}", -1.2 + k * 0.4 + rng.uniform(-0.1, 0.1), yf + 0.2 + rng.uniform(-0.2, 0.2), 0.9, rng.uniform(0.14, 0.22), rng.uniform(0.5, 1.0),
              K["glow2"], lean=(rng.uniform(-0.15, 0.15), 0.1))
    set_group("Main")
    # the crane: a post pivoting on two pins in the left jamb, an arm with a pot hook, the kettle
    cx, cy = -ow / 2 + 0.15, -D + 0.6
    tube("CranePost", [(cx, cy, 0.5), (cx, cy, 3.2)], 0.06, K["iron"], square=True, poly=True)
    tube("CraneArm", [(cx, cy, 3.1), (cx + 2.4, cy + 0.35, 3.1)], 0.06, K["iron"], square=True, poly=True)
    tube("CraneStay", [(cx, cy, 1.4), (cx + 1.6, cy + 0.23, 3.05)], 0.045, K["iron"], square=True, poly=True)
    for z in (0.8, 3.0):
        hoop(f"Pin{z}", (cx, cy, z), 0.09, "Z", K["iron"], thick=0.03)
    kx, ky = cx + 2.2, cy + 0.32
    chain_pts = [(kx, ky, 3.05), (kx, ky, 2.4)]
    B30.chain("Hook", chain_pts, K["iron"], r=0.06, thick=0.015)
    tube("PotHook", [(kx, ky, 2.4), (kx, ky, 2.25), (kx + 0.06, ky, 2.18)], 0.03, K["iron"])
    s = _mark()
    lathe("Kettle", [(0, 0), (0.4, 0), (0.6, 0.15), (0.66, 0.4), (0.6, 0.62), (0.4, 0.75), (0.22, 0.8), (0.24, 0.85), (0, 0.85)], K["castiron"], seg=20)
    lathe("Lid", [(0, 0.85), (0.24, 0.85), (0.18, 0.92), (0.06, 0.95), (0.06, 1.02), (0, 1.03)], K["castiron"], seg=14)
    bar("Spout", [(0.5, 0, 0.3), (0.75, 0, 0.42), (0.92, 0, 0.66), (1.0, 0, 0.78)], lambda t: 0.1 * (1 - t * 0.55), K["castiron"], seg=8)
    pts = [(math.cos(a) * 0.5, 0, 0.75 + math.sin(a) * 0.55) for a in [PI * i / 10 for i in range(11)]]
    bar("Bail", pts, 0.03, K["iron"], seg=5)
    _xform(s, T(kx, ky, 2.18 - 1.3) @ RZ(0.4))
    sphere("KettleSoot", 0.64, (kx, ky, 0.88 + 0.32), K["soot"], seg=14, rings=6, scale=(1.0, 1.0, 0.5))
    # bellows, a toasting fork, a basket of logs
    s = _mark()
    prism("BellowsTop", [(-0.35, 0), (0.35, 0), (0.42, 0.7), (0.0, 0.95), (-0.42, 0.7)], 0.12, 0.06, K["plank"], plane="XY")
    prism("BellowsBot", [(-0.35, 0), (0.35, 0), (0.42, 0.7), (0.0, 0.95), (-0.42, 0.7)], -0.12, 0.06, K["plank"], plane="XY")
    prism("BellowsHide", [(-0.32, 0.05), (0.32, 0.05), (0.38, 0.68), (0.0, 0.9), (-0.38, 0.68)], -0.08, 0.2, K["leather"], plane="XY")
    cone("Nozzle", 0.05, 0.02, 0.45, (0, -0.22, 0.0), K["brass"], verts=8, rot=(PI / 2, 0, 0))
    _xform(s, T(3.1, -D - 0.6, 0.5) @ RX(-PI / 2 + 0.2) @ RZ(0.4))
    pole("Fork", [(-3.3, -D - 0.2, 0.36), (-3.45, -D - 0.25, 3.4)], 0.04, K["iron"], seed=1, seg=5, knob=0.0, taper=0.0)
    for d in (-1, 0, 1):
        tube(f"Tine{d}", [(-3.45 + d * 0.06, -D - 0.25, 3.4), (-3.46 + d * 0.08, -D - 0.27, 3.75)], 0.015, K["iron"], poly=True)
    bx, by = -3.0, -D - 1.6
    lathe("LogBasket", [(0, 0), (0.6, 0), (0.75, 0.7), (0.72, 0.72), (0.58, 0.05), (0, 0.05)], K["wicker"], seg=18, loc=(bx, by, 0.0))
    for k in range(4):
        a = k * 1.3
        pole(f"BLog{k}", [(bx - 0.6 * math.cos(a), by - 0.3 * math.sin(a), 0.55 + k * 0.12), (bx + 0.6 * math.cos(a), by + 0.3 * math.sin(a), 0.6 + k * 0.12)], 0.17,
             K["bark"], seed=k + 20, seg=7)
    leaves_done("HearthKettle", cards)
    GLOW["HearthKettle"] = {"Glow2": FIRE}
    return _dims()


# ================================================================== the straw bed

def straw_bed(M):
    """A low box bed of rough logs (4.6 x 7.6, the headboard at +Y), a lumpy straw mattress with straw poking out, the patchwork
    quilt (moons and stars stitched on its patches) thrown over it and hanging down the sides, a lumpy linen pillow, a headboard
    of woven bent branches hung with a bone-hoop charm and dried flowers, a sheepskin on the floor."""
    K = wk(M)
    rng = RNG(4930)
    g = random.Random(4931)
    W, L = 4.6, 7.6
    hz = 1.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            pole(f"Leg{sx}{sy}", [(sx * W / 2, sy * L / 2, 0), (sx * W / 2, sy * L / 2, hz + (1.2 if sy > 0 else 0.25))], 0.28, K["bark"], seed=4932 + sx + 2 * sy,
                 seg=8, taper=0.1)
        pole(f"Side{sx}", [(sx * W / 2, -L / 2, hz - 0.1), (sx * (W / 2 + 0.05), 0, hz - 0.14), (sx * W / 2, L / 2, hz - 0.1)], 0.22, K["pole"], seed=4934 + sx,
             seg=8)
    for sy in (-1, 1):
        pole(f"End{sy}", [(-W / 2, sy * L / 2, hz - 0.1), (0, sy * L / 2, hz - 0.12), (W / 2, sy * L / 2, hz - 0.1)], 0.22, K["pole"], seed=4936 + sy, seg=8)
    for k in range(6):
        box(f"Slat{k}", (W, 0.45, 0.08), (0, -L / 2 + 0.6 + k * 1.28, hz - 0.2), K["plank"], bevel=0.02)
    # the straw mattress: a lumpy sack
    f = noise2(4937)
    mz = hz - 0.12

    def mat_fn(u, v):
        x = -W / 2 + 0.15 + u * (W - 0.3)
        y = -L / 2 + 0.15 + v * (L - 0.3)
        edge = min(u, 1 - u, v, 1 - v)
        hgt = 0.55 * min(1, edge * 8) ** 0.4 + 0.06 * f(x * 1.3, y * 1.3)
        return Vector((x, y, mz + hgt))
    sheet("Mattress", mat_fn, 14, 20, K["sack"], thick=0.0)
    box("MattressBase", (W - 0.3, L - 0.3, 0.1), (0, 0, mz + 0.03), K["sack"], bevel=0.04)
    for k in range(40):          # straw poking out at the seams
        side = g.randrange(4)
        if side < 2:
            x = (-1 if side == 0 else 1) * (W / 2 - 0.12)
            y = g.uniform(-L / 2 + 0.3, L / 2 - 0.3)
            d = Vector(((-1 if side == 0 else 1), g.uniform(-0.6, 0.6), g.uniform(-0.6, 0.3))).normalized()
        else:
            y = (-1 if side == 2 else 1) * (L / 2 - 0.12)
            x = g.uniform(-W / 2 + 0.3, W / 2 - 0.3)
            d = Vector((g.uniform(-0.6, 0.6), (-1 if side == 2 else 1), g.uniform(-0.6, 0.3))).normalized()
        p = Vector((x, y, mz + 0.3))
        bar(f"Straw{k}", [tuple(p), tuple(p + d * g.uniform(0.25, 0.5))], 0.012, K["straw"], seg=3)
    # the quilt: thrown over from the foot to under the pillow, falling over the sides in folds
    top = mz + 0.62
    qw, ql = W + 1.5, L - 1.3

    def quilt_fn(u, v):
        xx = (u - 0.5) * qw
        yy = -L / 2 - 0.35 + v * ql
        half = W / 2 - 0.1
        fold = 0.09 * math.sin(u * 13 + v * 3) + 0.06 * math.sin(v * 11)
        if abs(xx) <= half:
            z = top + 0.05 * math.cos(xx / half * PI / 2) + 0.03 * f(xx, yy)
            x = xx
        else:
            over = abs(xx) - half          # hangs down the side
            x = math.copysign(half + 0.12 + over * 0.15 + fold * 0.5, xx)
            z = top - over * 0.98
        if yy < -L / 2 + 0.2:              # and over the foot
            over = -L / 2 + 0.2 - yy
            yy = -L / 2 + 0.05 - over * 0.12
            z = min(z, top) - over * 0.95
        return Vector((x, yy, z + fold * 0.3))
    q = sheet("Quilt", quilt_fn, 24, 26, K["wp"], key="Quilt", thick=0.06, k=1.6)
    # the pillow and the headboard of woven branches
    blob("Pillow", (0.0, L / 2 - 0.95, top + 0.1), 0.6, K["linen"], seg=14, rings=8, scale=(2.6, 1.2, 0.45), jitter=0.05, seed=3)
    for k in range(5):
        z = hz + 0.4 + k * 0.32
        pts = [(-W / 2, L / 2, z), (-W / 4, L / 2 + 0.06 * (1 if k % 2 else -1), z + 0.1), (0, L / 2 - 0.06 * (1 if k % 2 else -1), z + 0.15),
               (W / 4, L / 2 + 0.06 * (1 if k % 2 else -1), z + 0.1), (W / 2, L / 2, z)]
        pole(f"Weave{k}", pts, 0.07, K["hazel"], seed=4940 + k, seg=6)
    for k in range(7):
        x = -W / 2 + 0.6 + k * (W - 1.2) / 6
        pole(f"Stake{k}", [(x, L / 2, hz + 0.1), (x + 0.05 * math.sin(k), L / 2, hz + 1.9 + 0.25 * math.sin(PI * (k / 6)))], 0.06, K["hazel"], seed=4950 + k, seg=5)
    pts = [(math.cos(a) * W / 2, L / 2, hz + 1.25 + math.sin(a) * 1.0) for a in [PI * i / 12 for i in range(13)]]
    pole("Arch", pts, 0.12, K["bark"], seed=4960, seg=7)
    # the bone hoop charm hanging from the arch and dried flowers along it
    hx, hy, hzz = 0.0, L / 2 - 0.25, hz + 1.65
    B40.ringbar("Hoop", (hx, hy, hzz), 0.35, "Y", K["bonew"], thick=0.035, n=18, seg=5)
    string("HoopStr", (hx, hy, hzz + 0.35), (0, L / 2, hz + 2.25), K, r=0.01)
    for k in range(5):
        a = k / 5 * 2 * PI
        string(f"Web{k}", (hx + math.cos(a) * 0.34, hy, hzz + math.sin(a) * 0.34), (hx - math.cos(a) * 0.34, hy, hzz - math.sin(a) * 0.34), K, r=0.006)
    feather("HoopF", (hx, hy - 0.02, hzz - 0.36), (0.1, 0, -1), 0.5, K, w=0.08)
    cards = Cards(rng)
    for k in range(6):
        a = PI * (0.15 + 0.7 * k / 5)
        cards.hang((math.cos(a) * W / 2, L / 2 - 0.12, hz + 1.25 + math.sin(a) * 1.0), 0.45, 0.6, ("lavender", "poppy", "moonflower")[k % 3], sway=0.05)
    leaves_done("StrawBed", cards)
    sk = blob("Sheepskin", (W / 2 + 1.35, -0.8, 0.02), 1.25, K["fleecedk"], seg=20, rings=8, scale=(1.0, 1.45, 0.1), jitter=0.16, seed=7)
    for v in sk.data.vertices:
        v.co.z = max(v.co.z, 0.0) + 0.03 * math.sin(v.co.x * 9) * math.cos(v.co.y * 7)
    return _dims()


# ================================================================== the work table

def witch_work_table(M):
    """A heavy work table (7.4 x 3.4, top at 3.2): a split-log top scored by the knife on crossed branch trestles, a shelf of
    crocks and a sack of roots under it; on top a stone mortar and pestle full of crushed herbs, gnarled roots, a chopping board
    of cut leaves, a brass-bladed sickle, bowls of seeds and berries, a garlic bulb, a notebook open at the hiccup remedy, a
    candle (Glow2) and a toad watching."""
    K = wk(M)
    rng = RNG(4970)
    g = random.Random(4971)
    L, D, H = 7.4, 3.4, 3.2
    for k, y in enumerate((-D / 2 + 0.55, 0.0, D / 2 - 0.55)):
        hewn(f"Top{k}", (-L / 2, y, H - 0.15), (L / 2, y, H - 0.15), 1.12, 0.3, K["timber"] if k != 1 else K["plank"], seed=4972 + k, jit=0.02, cham=0.06,
             n=14)
    for k in range(6):          # knife scores
        x = g.uniform(-2.5, 2.5)
        box(f"Score{k}", (g.uniform(0.4, 0.9), 0.02, 0.01), (x, g.uniform(-1.2, 1.2), H + 0.003), K["timberdk"], bevel=0.0, rot=(0, 0, g.uniform(-0.6, 0.6)))
    for sx in (-1, 1):          # the crossed-branch trestles and a stretcher
        x = sx * (L / 2 - 0.8)
        for d in (-1, 1):
            pole(f"Leg{sx}{d}", crooked((x, d * (D / 2 - 0.2), 0.0), (x, -d * (D / 2 - 0.5), H - 0.3), 0.08, 4975 + sx + d * 3, n=6, perp=(1, 0, 0)), 0.17,
                 K["bark"], seed=4976 + sx + d, seg=8, taper=0.15)
        hoop(f"Lash{sx}", (x, 0.0, (H - 0.3) / 2 + 0.1), 0.2, "X", K["rope"], thick=0.035)
    pole("Stretcher", [(-L / 2 + 0.8, 0, 1.0), (0, 0.03, 0.96), (L / 2 - 0.8, 0, 1.0)], 0.13, K["pole"], seed=4980, seg=7)
    box("Shelf", (L - 2.0, 2.2, 0.12), (0, 0, 0.55), K["plank"], bevel=0.02)
    for k, (x, r, h, m) in enumerate(((-2.0, 0.35, 0.7, "crock"), (-1.2, 0.28, 0.5, "crockdk"), (1.6, 0.33, 0.6, "crock"))):
        lathe(f"UCrock{k}", [(0, 0), (r * 0.8, 0), (r, h * 0.35), (r * 0.9, h * 0.85), (r * 0.65, h), (r * 0.7, h * 1.05), (0, h)], K[m], seg=14, loc=(x, 0.2, 0.61))
    sphere("Sack", 0.55, (0.3, -0.1, 0.61 + 0.45), K["sack"], seg=14, rings=8, scale=(1.0, 0.9, 0.85))
    for k in range(3):
        pole(f"SackRoot{k}", crooked((0.2 + k * 0.15, -0.2, 1.3), (0.4 + k * 0.3, -0.6, 1.8 + k * 0.1), 0.08, k, n=5), 0.06, K["rootw"], seed=k, seg=6)
    zt = H
    # the mortar and pestle
    lathe("Mortar", [(0, 0), (0.55, 0), (0.62, 0.12), (0.6, 0.6), (0.65, 0.68), (0.52, 0.7), (0.44, 0.35), (0, 0.32)], K["field"], seg=20, loc=(-2.6, -0.4, zt))
    sphere("Crushed", 0.44, (-2.6, -0.4, zt + 0.42), K["herbg"], seg=12, rings=5, scale=(1, 1, 0.25))
    pole("Pestle", [(-2.55, -0.4, zt + 0.35), (-2.25, -0.3, zt + 1.2)], 0.1, K["fielddk"], seed=2, seg=8, taper=-0.4)
    # gnarled roots
    for k in range(3):
        base = Vector((-1.2 + k * 0.5, 0.8 + g.uniform(-0.2, 0.2), zt + 0.12))
        pts = [tuple(base + Vector((math.cos(k) * t * 1.0, math.sin(k + 1) * t * 0.6, 0.1 * math.sin(t * 3)))) for t in (0, 0.3, 0.6, 1.0)]
        pole(f"Root{k}", pts, 0.12, K["rootw"], seed=4981 + k, seg=7, taper=0.8)
        for j in range(3):
            q = Vector(pts[1 + j % 3])
            pole(f"Rootlet{k}{j}", [tuple(q), tuple(q + Vector((g.uniform(-0.4, 0.4), g.uniform(-0.4, 0.4), -0.05)))], 0.035, K["rootw"], seed=j, seg=4, taper=0.8)
    # the chopping board and cut leaves, the sickle
    box("Board", (1.6, 1.0, 0.1), (0.6, -0.6, zt + 0.05), K["planklt"], bevel=0.03, rot=(0, 0, 0.15))
    for k in range(16):
        box(f"Cut{k}", (0.09, 0.05, 0.015), (0.4 + g.uniform(-0.5, 0.5), -0.6 + g.uniform(-0.35, 0.35), zt + 0.11), K["herbg"], bevel=0.0,
            rot=(0, 0, g.uniform(0, 3)))
    blade = [(math.cos(a) * 0.5, math.sin(a) * 0.5) for a in [PI * (0.05 + 0.8 * i / 12) for i in range(13)]] + \
            [(math.cos(a) * 0.4 + 0.06, math.sin(a) * 0.36) for a in [PI * (0.85 - 0.8 * i / 12) for i in range(13)]]
    prism("Sickle", [(u, w) for u, w in blade], zt + 0.12, 0.03, K["brass"], plane="XY")
    P.PARTS[-1].matrix_world = T(1.3, -0.2, 0) @ RZ(-0.5)
    pole("SickleGrip", [(1.3 + 0.48 * math.cos(-0.5), -0.2 + 0.48 * math.sin(-0.5), zt + 0.14), (1.3 + 0.48 * math.cos(-0.5) + 0.5 * math.cos(-2.1),
                                                                                                -0.2 + 0.48 * math.sin(-0.5) + 0.5 * math.sin(-2.1), zt + 0.14)],
         0.05, K["bonew"], seed=3, seg=6)
    # bowls of seeds and berries, garlic, the notebook, the candle, the toad
    for k, (x, y, fill) in enumerate(((2.3, 0.6, "gourdy"), (2.9, -0.3, "chilli"), (1.9, 1.15, "lav"))):
        lathe(f"Bowl{k}", [(0, 0), (0.25, 0), (0.42, 0.2), (0.45, 0.25), (0.38, 0.24), (0.22, 0.06), (0, 0.06)], K["crock"], seg=14, loc=(x, y, zt))
        for j in range(10):
            a, r = g.uniform(0, 2 * PI), g.uniform(0, 0.28)
            sphere(f"Seed{k}{j}", 0.05 if fill != "chilli" else 0.07, (x + math.cos(a) * r, y + math.sin(a) * r, zt + 0.19), K[fill], seg=6, rings=4)
    lathe("Garlic", [(0, 0), (0.12, 0.03), (0.19, 0.15), (0.13, 0.28), (0.04, 0.37), (0, 0.4)], K["garlic"], seg=10, flute=(8, 0.08), loc=(-0.4, -1.1, zt))
    for sx in (-1, 1):
        sheet(f"Note{sx}", lambda u, v, sx=sx: Vector((-1.2 + sx * (0.03 + u * 0.75), 0.15 + v * 1.0, zt + 0.06 + 0.05 * math.sin(PI * u) * (1 - u * 0.5))), 6, 2,
              K["wp"], key=("Note1" if sx > 0 else "Note3"), thick=0.0, k=2.2)
        if sx < 0:
            ob = P.PARTS[-1]
            u0, v0, u1, v1 = B30.REG["WP_Note3"]
            for d in ob.data.uv_layers["Spine"].data:
                d.uv = (u0 + u1 - d.uv[0], d.uv[1])
        box(f"NoteCover{sx}", (0.8, 1.06, 0.04), (-1.2 + sx * 0.4, 0.65, zt + 0.02), K["leather"], bevel=0.01)
    candle("Candle", 3.0, 1.1, zt, 0.17, 0.6, K, drips=5)
    toad("Toad", T(-3.1, 0.7, zt) @ RZ(-0.6), K, s=1.0)
    cards = Cards(rng)
    for k in range(5):          # bunches of herbs lying on the table
        p = (-0.2 + k * 0.45, 1.1 + g.uniform(-0.2, 0.2), zt + 0.04)
        ax, ay = frame(Vector((0, 0, 1)), roll=g.uniform(0, 6.28), up=Vector((0, 1, 0)))
        cards.add(p, ax, ay, 0.6, 0.9, ("fern", "lavender", "rose_leaves", "nightshade", "twigs")[k], "fill", nrm=UP)
    leaves_done("WitchWorkTable", cards)
    GLOW["WitchWorkTable"] = {"Glow2": FIRE}
    return _dims()


# ================================================================== the hat stand

def witch_hat_stand(M):
    """A crooked hat stand grown from a sapling: three root feet, a twisted trunk 6.6 tall, forked branch hooks curling up; the
    witch's tall black hat on the top fork (a broad wavy brim, a crown that bends over at the tip, a violet band with a tin
    buckle), a hooded wool cloak and a striped scarf hung below, a satchel; her buckled boots at its foot."""
    K = wk(M)
    rng = RNG(4990)
    for k in range(3):
        a = k / 3 * 2 * PI + 0.4
        pole(f"Foot{k}", [(0, 0, 0.7), (math.cos(a) * 0.7, math.sin(a) * 0.7, 0.25), (math.cos(a) * 1.25, math.sin(a) * 1.25, 0.06)], 0.14, K["bark"],
             seed=4991 + k, seg=7, taper=0.5)
    trunk = crooked((0, 0, 0.0), (0.1, 0.05, 6.6), 0.25, 4992, n=10, perp=(1, 0.3, 0))
    pole("Trunk", trunk, 0.17, K["bark"], seed=4993, seg=9, taper=0.35)
    hooks = [(5.6, 0.3), (5.2, 2.4), (4.6, 4.3), (3.9, 1.3)]
    tips = []
    for k, (z, a) in enumerate(hooks):
        b = Vector((0.06, 0.03, z))
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [tuple(b), tuple(b + d * 0.45 + Vector((0, 0, 0.1))), tuple(b + d * 0.75 + Vector((0, 0, 0.45))), tuple(b + d * 0.7 + Vector((0, 0, 0.7)))]
        pole(f"Hook{k}", pts, 0.08, K["bark"], seed=4994 + k, seg=6, taper=0.5)
        tips.append((b + d * 0.6, d))
    # the hat on the top of the trunk
    top = Vector(trunk[-1])
    hz = top.z - 0.15
    s = _mark()
    f = smooth_noise(4997, 4)
    prof = []
    brim = []
    for i in range(48):
        a = i / 48 * 2 * PI
        brim.append(a)
    lathe("Brim", [(0.45, 0.0), (1.45, -0.06), (1.5, -0.02), (1.42, 0.02), (0.45, 0.06)], K["felt"], seg=48)
    for v in P.PARTS[-1].data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        a = math.atan2(v.co.y, v.co.x)
        if r > 0.8:
            v.co.z += 0.14 * f(a * 2.0) * (r - 0.8) / 0.7 + 0.12 * ((r - 0.8) / 0.7) ** 2
    pts = []
    for i in range(14):
        t = i / 13
        bend = max(0.0, t - 0.55) / 0.45
        pts.append((0.55 * bend ** 1.6, 0.1 * math.sin(t * 5), 0.05 + t * 2.4 - 0.5 * bend ** 2))
    sweep("Crown", pts, lambda t: 0.5 * (1 - t) ** 0.85 + 0.015, K["felt"], seg=24)
    for v in P.PARTS[-1].data.vertices:       # dents and crumples
        v.co.x += 0.03 * math.sin(v.co.z * 7 + v.co.y * 4)
    hoop("Band", (0.0, 0.0, 0.25), 0.49, "Z", K["woolv"], thick=0.07)
    box("Buckle", (0.24, 0.05, 0.2), (0.0, -0.53, 0.25), K["tin"], bevel=0.02)
    box("BuckleIn", (0.12, 0.06, 0.1), (0.0, -0.535, 0.25), K["woolv"], bevel=0.0)
    _xform(s, T(top.x, top.y, hz) @ RY(0.08) @ RX(-0.05))
    # the cloak: a hood and folds hanging from the hook at 5.2
    (hp, hd) = tips[1]

    def cloak(u, v):
        a = (u - 0.5) * 2.6
        z = 5.2 - v * 4.0
        r = 0.25 + v * 0.75
        fold = 0.08 * math.sin(u * 22) * v
        return Vector((hp.x + math.sin(a) * r * 0.9, hp.y + math.cos(a) * r * 0.55 + fold, z + 0.05 * math.cos(u * 9)))
    sheet("Cloak", cloak, 22, 12, K["woolg"], thick=0.06)
    sphere("Hood", 0.42, (hp.x, hp.y - 0.05, 5.0), K["woolg"], seg=14, rings=8, scale=(1.0, 0.75, 1.1))
    # the scarf over the low hook
    (sp, sd) = tips[3]
    for k, side in enumerate((-1, 1)):
        pts = [(sp.x, sp.y, 3.95), (sp.x + sd.x * 0.1 + side * 0.15, sp.y + side * 0.05, 3.5), (sp.x + side * 0.22, sp.y + side * 0.08, 2.4 - k * 0.4)]
        strip(f"Scarf{k}", pts, 0.38, (sd.y, -sd.x, 0), K["woolv"] if k else K["wool"], thick=0.05)
    for k in range(6):
        z = 3.4 - k * 0.3
        box(f"Stripe{k}", (0.4, 0.07, 0.07), (sp.x - 0.22, sp.y - 0.08, z), K["wool"] if k % 2 else K["toadred"], bevel=0.02)
    # the satchel on the third hook
    (bp, bd) = tips[2]
    box("Satchel", (0.7, 0.3, 0.6), (bp.x, bp.y, 3.6), K["leather"], bevel=0.08)
    box("Flap", (0.72, 0.06, 0.4), (bp.x, bp.y - 0.17, 3.75), K["leather"], bevel=0.04)
    string("Strap", (bp.x - 0.3, bp.y, 3.85), (bp.x, bp.y, 4.62), K, r=0.035, mat=K["leather"])
    string("Strap2", (bp.x + 0.3, bp.y, 3.85), (bp.x, bp.y, 4.62), K, r=0.035, mat=K["leather"])
    # the boots, pointed toes curling up, one fallen over
    for k, (x, y, rot, fall) in enumerate(((0.9, -1.0, -0.3, 0.0), (1.55, -0.55, 0.6, 1.25))):
        s = _mark()
        pts = [(0, 0.35, 0.55), (0, 0.3, 0.25), (0, 0.0, 0.18), (0, -0.4, 0.14), (0, -0.65, 0.2), (0, -0.75, 0.38)]
        sweep(f"Foot{k}", pts, lambda t: 0.2 * (1 - 0.7 * t ** 2) + 0.03, K["leatherb"], seg=12, flat_k=0.6)
        lathe(f"Shaft{k}", [(0.0, 0.4), (0.24, 0.4), (0.26, 1.2), (0.3, 1.45), (0.26, 1.46), (0.0, 1.42)], K["leatherb"], seg=16, loc=(0, 0.3, 0))
        box(f"Sole{k}", (0.36, 1.05, 0.08), (0, -0.15, 0.04), K["leather"], bevel=0.03)
        box(f"BBuckle{k}", (0.2, 0.05, 0.16), (0, 0.03, 0.85), K["tin"], bevel=0.02)
        _xform(s, T(x, y, 0) @ RZ(rot) @ (T(0, 0, 0.25) @ RY(fall) if fall else Matrix.Identity(4)))
    ground_at_zero(0)
    return _dims()


# ================================================================== the cat's basket

def cat_basket(M):
    """A round wicker basket (2.7 across) with a patchwork cushion, and the witch's black cat curled asleep in it, nose in its
    tail, one eye open a slit (Glow, yellow-green); a ball of wool with a loose end, a saucer of milk and a picked fish-bone
    beside it."""
    K = wk(M)
    rng = RNG(5000)
    R = 1.35
    lathe("Basket", [(0, 0), (R * 0.9, 0), (R, 0.15), (R * 1.05, 0.7), (R * 0.97, 0.72), (R * 0.92, 0.18), (0, 0.15)], K["wicker"], seg=32)
    B40.ringbar("Rim", (0, 0, 0.74), R * 1.02, "Z", K["wicker"], thick=0.09, n=32, seg=7)
    for k in range(16):
        a = k / 16 * 2 * PI
        tube(f"Stake{k}", [(math.cos(a) * R * 0.95, math.sin(a) * R * 0.95, 0.05), (math.cos(a) * R * 1.06, math.sin(a) * R * 1.06, 0.72)], 0.025, K["hazel"],
             poly=True)
    ob = blob("Cushion", (0, 0, 0.3), R * 0.9, K["wp"], seg=20, rings=8, scale=(1.0, 1.0, 0.2), jitter=0.03, seed=2)
    uv_planar(ob, "Quilt", axes=(0, 1), k=1.4)
    # the cat: a curled body (a sweep round a spiral), the head resting on its forepaws, ears, the tail round its nose
    zc = 0.55
    body = []
    for i in range(15):
        t = i / 14
        a = -0.3 + t * 1.75 * PI
        r = 0.62 - 0.12 * t
        body.append((math.cos(a) * r, math.sin(a) * r, zc + 0.28 - 0.05 * t))
    sweep("Body", body, lambda t: 0.36 * (0.75 + 0.35 * math.sin(PI * min(1, t * 1.25))) - 0.06 * t, K["fur"], seg=16, flat_k=0.75)
    hx, hy = math.cos(-0.45) * 0.62 + 0.05, math.sin(-0.45) * 0.62 - 0.18
    blob("Head", (hx, hy, zc + 0.36), 0.3, K["fur"], seg=16, rings=10, scale=(1.05, 1.0, 0.85), jitter=0.0)
    blob("Muzzle", (hx + 0.12, hy - 0.2, zc + 0.3), 0.13, K["fur"], seg=10, rings=6, scale=(1.0, 0.9, 0.7))
    sphere("Nose", 0.035, (hx + 0.17, hy - 0.32, zc + 0.33), K["horn"], seg=6, rings=4)
    for k, (ex, ey) in enumerate(((-0.12, 0.05), (0.18, -0.05))):
        cone(f"Ear{k}", 0.13, 0.01, 0.26, (hx + ex, hy + ey, zc + 0.6), K["fur"], verts=8, rot=(0.2 * (k * 2 - 1), -0.3 * (k * 2 - 1), 0))
    sphere("EyeShut", 0.05, (hx - 0.02, hy - 0.26, zc + 0.43), K["fur"], seg=8, rings=4, scale=(1.4, 0.5, 0.35))
    set_group("Glow")
    sphere("EyeSlit", 0.05, (hx + 0.2, hy - 0.25, zc + 0.42), K["glow"], seg=8, rings=4, scale=(1.2, 0.5, 0.3))
    set_group("Main")
    for k in range(2):           # forepaws under the chin
        sweep(f"Paw{k}", [(hx - 0.25 + k * 0.2, hy + 0.15, zc + 0.15), (hx - 0.1 + k * 0.22, hy - 0.2, zc + 0.12), (hx + k * 0.22, hy - 0.38, zc + 0.12)],
              lambda t: 0.09 + 0.02 * t, K["fur"], seg=8)
    tail = []
    for i in range(12):
        t = i / 11
        a = 1.45 * PI + t * 0.85 * PI
        r = 0.78 - 0.12 * t
        tail.append((math.cos(a) * r, math.sin(a) * r, zc + 0.12 + 0.05 * math.sin(t * PI)))
    sweep("Tail", tail, lambda t: 0.12 * (1 - 0.35 * t), K["fur"], seg=10)
    for sx in (-1, 1):
        for j in range(3):
            bar(f"Whisker{sx}{j}", [(hx + 0.14 + sx * 0.06, hy - 0.3, zc + 0.31), (hx + 0.14 + sx * 0.45, hy - 0.45, zc + 0.3 + (j - 1) * 0.05)], 0.006, K["bonew"],
                seg=3)
    # the ball of wool, the saucer, the fish-bone
    sphere("Wool", 0.32, (1.75, -0.9, 0.32), K["woolv"], seg=14, rings=8)
    for k in range(4):
        hoop(f"Wind{k}", (1.75, -0.9, 0.32), 0.325, ("X", "Y", "Z", "X")[k], K["woolv"], thick=0.02)
        P.PARTS[-1].matrix_world = T(1.75, -0.9, 0.32) @ RZ(k * 0.8) @ RX(k * 0.5) @ T(-1.75, 0.9, -0.32)
    bar("Thread", [(1.6, -0.65, 0.1), (1.3, -0.2, 0.02), (1.25, 0.3, 0.02), (1.0, 0.6, 0.4), (0.9, 0.7, 0.72)], 0.018, K["woolv"], seg=4)
    lathe("Saucer", [(0, 0), (0.35, 0), (0.48, 0.08), (0.46, 0.1), (0.3, 0.04), (0, 0.04)], K["crock"], seg=18, loc=(-1.7, -1.0, 0.0))
    cyl("Milk", 0.33, 0.02, (-1.7, -1.0, 0.065), K["linen"], verts=18, bevel=0.0)
    pole("Spine", [(-1.9, -1.9, 0.03), (-1.2, -1.75, 0.03)], 0.02, K["bonew"], seed=1, seg=4, knob=0.0)
    for k in range(6):
        x = -1.8 + k * 0.1
        for d in (-1, 1):
            bar(f"Rib{k}{d}", [(x, -1.88 + 0.03 * k, 0.03), (x + 0.06, -1.88 + 0.03 * k + d * 0.18, 0.04)], 0.008, K["bonew"], seg=3)
    blob("FishHead", (-1.12, -1.74, 0.07), 0.1, K["bonew"], seg=8, rings=5, scale=(1.4, 0.8, 0.6))
    GLOW["CatBasket"] = {"Glow": CATEYE}
    return _dims()


# ================================================================== gourds and pumpkins

def gourd(name, kind, loc, s, K, rng, rot=None):
    st = _mark()
    if kind in ("pumpkin", "ghost"):
        h = s * (1.0 if kind == "pumpkin" else 0.75)
        prof = [(0, 0.06 * h)] + [(s * math.sin(t * PI) ** 0.7, h * (1 - math.cos(t * PI)) / 2) for t in [i / 14 for i in range(1, 14)]] +                [(0.12 * s, h * 0.93), (0, h * 0.86)]
        lathe(name, prof, K["pumpkin"] if kind == "pumpkin" else K["pumpkinp"], seg=40, flute=(10, 0.07))
        bar(name + "Stalk", [(0, 0, h * 0.84), (0.04 * s, 0, h * 1.02), (0.16 * s, 0.05 * s, h * 1.12)], lambda t: 0.08 * s * (1 - t * 0.35) + 0.02, K["stalk"],
            seg=6)
    elif kind == "bottle":
        lathe(name, [(0, 0), (s * 0.55, 0.05 * s), (s * 0.62, 0.35 * s), (s * 0.45, 0.7 * s), (s * 0.25, 0.85 * s), (s * 0.3, 1.05 * s), (s * 0.28, 1.25 * s),
                     (s * 0.12, 1.4 * s), (0, 1.42 * s)], K["gourdb"], seg=16)
    elif kind == "swan":
        pts = [(0, 0, 0.3 * s), (0, 0, 0.9 * s), (0.15 * s, 0, 1.6 * s), (0.6 * s, 0, 1.9 * s), (0.95 * s, 0, 1.6 * s)]
        sweep(name, pts, lambda t: s * (0.45 * (1 - t) ** 1.5 + 0.08), K["gourdg"], seg=14)
        sphere(name + "Belly", 0.45 * s, (0, 0, 0.42 * s), K["gourdg"], seg=14, rings=8, scale=(1, 1, 0.95))
    elif kind == "warty":
        blob(name, (0, 0, 0.5 * s), 0.5 * s, K["gourdy"], seg=14, rings=8, scale=(1.0, 1.0, 0.95), jitter=0.06, seed=int(s * 100))
        for k in range(14):
            a, b = rng.uniform(0, 2 * PI), rng.uniform(0.3, 2.6)
            sphere(f"{name}Wart{k}", 0.06 * s, (math.cos(a) * math.sin(b) * 0.5 * s, math.sin(a) * math.sin(b) * 0.5 * s, 0.5 * s + math.cos(b) * 0.47 * s),
                   K["gourdg"], seg=6, rings=4)
    else:        # striped pear gourd
        lathe(name, [(0, 0), (s * 0.4, 0.05 * s), (s * 0.45, 0.3 * s), (s * 0.3, 0.7 * s), (s * 0.16, 0.95 * s), (0, 1.0 * s)], K["gourdg"], seg=16,
              flute=(10, 0.05))
    if kind not in ("pumpkin", "ghost"):
        top = max((v.co.z for v in P.PARTS[st].data.vertices), default=s)
        bar(name + "Stalk", [(0, 0, top - 0.05), (0.03, 0, top + 0.12 * s), (0.1, 0.02, top + 0.18 * s)], 0.035 * s + 0.02, K["stalk"], seg=5)
    _xform(st, T(*loc) @ (rot or Matrix.Identity(4)))


def gourd_pile(M):
    """A harvest heap spilling from a tipped wicker basket: big ribbed pumpkins, a pale ghost pumpkin, warty yellow gourds,
    a swan-neck gourd, bottle gourds, striped pear gourds, a gourd dipper; straw, husks and fallen leaves round it."""
    K = wk(M)
    rng = RNG(5010)
    s = _mark()
    lathe("Basket", [(0, 0), (0.9, 0), (1.15, 1.1), (1.1, 1.12), (0.86, 0.06), (0, 0.06)], K["wicker"], seg=24)
    B40.ringbar("BRim", (0, 0, 1.12), 1.13, "Z", K["wicker"], thick=0.07, n=24, seg=6)
    _xform(s, T(1.7, 0.6, 0.95) @ RY(1.45) @ T(0, 0, -0.5))
    items = [("pumpkin", (-1.2, -0.2, 0.0), 1.05), ("pumpkin", (0.4, -0.9, 0.0), 0.8), ("ghost", (-0.3, 0.9, 0.0), 0.85), ("warty", (0.9, 0.25, 0.0), 0.65),
             ("bottle", (-2.2, 0.7, 0.0), 0.8), ("swan", (-2.4, -0.9, 0.0), 0.7), ("pear", (1.2, -1.5, 0.0), 0.5), ("warty", (-0.5, -1.7, 0.0), 0.45),
             ("pear", (2.4, 0.1, 0.0), 0.45), ("pumpkin", (-0.8, 0.2, 1.75), 0.6), ("warty", (0.2, -0.1, 1.15), 0.4), ("pear", (2.2, -0.8, 0.0), 0.4)]
    for k, (kind, loc, sz) in enumerate(items):
        gourd(f"G{k}", kind, loc, sz, K, rng, rot=RZ(rng.uniform(0, 6.28)) @ RY(rng.uniform(-0.2, 0.2)))
    s = _mark()        # the dipper: half a bottle gourd with its neck as the handle
    lathe("Dipper", [(0, 0), (0.4, 0.05), (0.45, 0.3), (0.4, 0.32), (0.35, 0.08), (0, 0.06)], K["gourdb"], seg=16)
    bar("DipperNeck", [(0.4, 0, 0.3), (0.8, 0, 0.42), (1.2, 0, 0.5)], lambda t: 0.1 * (1 - t * 0.4), K["gourdb"], seg=7)
    _xform(s, T(-1.9, -1.9, 0) @ RZ(0.4))
    straw = K["straw"]
    g = random.Random(5011)
    for k in range(30):
        a, r = g.uniform(0, 2 * PI), g.uniform(0.5, 3.0)
        box(f"Straw{k}", (0.6, 0.025, 0.02), (math.cos(a) * r, math.sin(a) * r * 0.8, 0.015), straw, bevel=0.0, rot=(0, 0, g.uniform(0, 3.14)))
    cards = Cards(rng)
    for k in range(12):
        p = (g.uniform(-3, 3), g.uniform(-2.3, 2.0), 0.05)
        ax, ay = frame(Vector((g.uniform(-0.3, 0.3), g.uniform(-0.3, 0.3), 1)), roll=g.uniform(0, 6.28), up=Vector((0, 1, 0)))
        cards.add(p, ax, ay, 0.7, 0.7, ("ivy", "crabapple", "rose_leaves")[k % 3], "fill", nrm=UP)
    leaves_done("GourdPile", cards)
    ground_at_zero(0)
    return _dims()


# ================================================================== the braided rug

def braided_rug(M):
    """An oval braided rag rug 9 x 6.4: sixteen coils of three-strand braid in faded rags (crimson, violet, moss, ochre, ink),
    each coil a raised round ridge; one end kicked up in a ripple."""
    K = wk(M)
    A, Bb = 4.5, 3.2
    na, nr = 72, 44
    coils = 16

    def fn(u, v):
        a = u * 2 * PI
        r = v
        ridge = 0.035 * abs(math.sin(PI * r * coils)) ** 0.5
        z = 0.03 + ridge * (1 if r < 0.995 else 0.0)
        x, y = math.cos(a) * A * r, math.sin(a) * Bb * r
        if x > 3.0:                          # the kicked-up ripple at one end
            z += 0.18 * math.sin(PI * (x - 3.0) / 1.5) * max(0, math.sin(a * 2 + 1.0))
        return Vector((x, y, z))
    ob = sheet("Rug", fn, na, nr, K["wp"], key=None, thick=0.0)
    uv_planar(ob, "Rug", axes=(0, 1), k=1.3, bounds=(-A, A, -Bb, Bb))
    md = ob.modifiers.new("Solid", "SOLIDIFY")
    md.thickness = 0.03
    md.offset = -1
    return _dims()


# ================================================================== the crooked bookshelf of spell notes

def spell_note_shelf(M):
    """A wall piece (back on y = 0, standing on the floor): a crooked bookshelf of rough planks with bark still on their edges,
    leaning a little, five uneven shelves of hand-bound spellbooks (stitched leather, the titles inked on their spines), rolled
    scrolls tied with twine, bundles of notes, a jar of quills, a fox skull, a candle stub and a stone on a pile of papers;
    the loose spell notes (a moon calendar, a remedy, a toadstool study, a list of chores) pinned to its side and front."""
    K = wk(M)
    rng = RNG(5020)
    g = random.Random(5021)
    W, D, H = 4.6, 1.4, 7.6
    lean = 0.06

    def lx(z):
        return lean * z

    for sx in (-1, 1):
        hewn(f"Side{sx}", (sx * W / 2, -D / 2, 0.0), (sx * W / 2 + lx(H), -D / 2, H), 0.16, D, K["plank"], seed=5022 + sx, up=(0, 1, 0), jit=0.02, n=12,
             cham=0.03)
        pole(f"Bark{sx}", [(sx * (W / 2 + 0.06), -D + 0.05, 0.1), (sx * (W / 2 + 0.06) + lx(H), -D + 0.05, H - 0.1)], 0.07, K["bark"], seed=5024 + sx, seg=6)
    box("Back", (W, 0.08, H - 0.1), (lx(H / 2), -0.04, H / 2), K["timberdk"], bevel=0.01, rot=(0, lean, 0))
    zs = [0.25, 1.75, 3.15, 4.45, 5.95, H - 0.08]
    for k, z in enumerate(zs):
        t = g.uniform(-0.06, 0.06) if 0 < k < 5 else 0.0
        hewn(f"Shelf{k}", (-W / 2 + lx(z), -D / 2, z + t), (W / 2 + lx(z), -D / 2, z - t), D - 0.1, 0.12, K["plank"] if k % 2 else K["timber"], seed=5026 + k,
             jit=0.012, cham=0.02, bow=(0, 0, -0.06 if k == 3 else 0))
    bi = 0
    for k in range(5):
        z0, z1 = zs[k] + 0.06, zs[k + 1] - 0.06
        x = -W / 2 + 0.15 + lx(z0)
        xend = W / 2 - 0.15 + lx(z0)
        while x < xend - 0.25:
            r = g.random()
            if r < 0.62:                     # a spellbook standing (or leaning on its neighbour)
                th = g.uniform(0.2, 0.38)
                hh = min(z1 - z0 - 0.08, g.uniform(0.8, 1.2))
                dd = g.uniform(0.8, 1.05)
                if x + th > xend:
                    break
                tilt = g.uniform(-0.12, 0.0) if g.random() < 0.25 else 0.0
                s = _mark()
                col = (K["leather"], K["leatherb"], K["woolv"], K["woolg"], K["wool"])[bi % 5]
                box(f"Bk{bi}", (th, dd, hh), (0, 0, hh / 2), col, bevel=0.025, segments=1)
                box(f"BkPages{bi}", (th - 0.05, dd - 0.06, hh - 0.08), (0, 0.04, hh / 2), K["paper"], bevel=0.0)
                pprism(f"BkSpine{bi}", f"WP_Spine{bi % 10}", [(-th / 2 + 0.01, 0.04), (th / 2 - 0.01, 0.04), (th / 2 - 0.01, hh - 0.04), (-th / 2 + 0.01, hh - 0.04)],
                       0.01, T(0, -dd / 2 - 0.004, 0), K["wp"], edge="WP_leather", k=2.0)
                _xform(s, T(x + th / 2, -D / 2 - 0.05 + (1.0 - dd) / 2, z0) @ RY(tilt))
                x += th + (0.1 if tilt else 0.02)
                bi += 1
            elif r < 0.78:                   # scrolls lying, tied with twine
                for j in range(g.randint(2, 3)):
                    cyl(f"Scroll{bi}{j}", 0.11, D - 0.25, (x + 0.12, -D / 2, z0 + 0.11 + j * 0.2), K["paper"], rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
                    B40.ringbar(f"ScrollTie{bi}{j}", (x + 0.12, -D / 2 - 0.2, z0 + 0.11 + j * 0.2), 0.115, "Y", K["twine"], thick=0.014, n=10, seg=4)
                    x += 0.0
                x += 0.4
                bi += 1
            elif r < 0.9:                    # a bundle of notes under a stone
                box(f"Notes{bi}", (0.7, 0.9, 0.22), (x + 0.36, -D / 2, z0 + 0.11), K["paper"], bevel=0.02, rot=(0, 0, g.uniform(-0.1, 0.1)))
                B40.ringbar(f"NotesTie{bi}", (x + 0.36, -D / 2, z0 + 0.11), 0.2, "X", K["twine"], thick=0.015, n=12, seg=4)
                rock(f"Weight{bi}", (x + 0.4, -D / 2, z0 + 0.32), (0.3, 0.25, 0.18), K["field"], rng, bevel=0.2)
                x += 0.8
                bi += 1
            else:
                x += 0.3
    # top: a fox skull, a jar of quills, a candle stub
    zt = H + 0.04
    skull_small("Fox", T(-1.2 + lx(H), -0.75, zt + 0.25) @ RZ(0.35), K, s=0.7)
    lathe("QuillJar", [(0, 0), (0.18, 0), (0.2, 0.4), (0.16, 0.45), (0, 0.45)], K["crock"], seg=12, loc=(0.6 + lx(H), -0.7, zt))
    for k in range(4):
        feather(f"Quill{k}", (0.6 + lx(H) + (k - 1.5) * 0.05, -0.7, zt + 0.3), ((k - 1.5) * 0.25, 0.1, 1), 0.8, K, w=0.08,
                mat=K["feather"] if k % 2 else K["featherb"])
    candle("Stub", 1.6 + lx(H), -0.7, zt, 0.14, 0.3, K, drips=4, flame=False, mat=K["waxdk"])
    # the pinned notes: two on the right side, one on the front of the left side, one hanging from a shelf
    for k, (key, mtx) in enumerate((("Note0", T(W / 2 + 0.09 + lx(5.2), -0.75, 5.2) @ RZ(PI / 2) @ RY(0.05)),
                                    ("Note2", T(W / 2 + 0.09 + lx(2.4), -0.6, 2.4) @ RZ(PI / 2) @ RY(-0.08)),
                                    ("Note3", T(-W / 2 + lx(3.8), -D - 0.03, 3.8) @ RY(0.1) @ T(-0.35, 0, 0)),
                                    ("Note1", T(0.6 + lx(3.0), -D - 0.04, 2.85) @ RY(-0.06)))):
        pprism(f"Pinned{k}", f"WP_{key}", [(-0.4, -0.53), (0.4, -0.53), (0.4, 0.53), (-0.4, 0.53)], 0.008, mtx, K["wp"], edge="WP_page", k=2.4)
        sphere(f"Pin{k}", 0.04, tuple(mtx @ Vector((0, -0.01, 0.45))), K["iron"], seg=6, rings=4)
    cobweb("Web", (-W / 2 + 0.1 + lx(H - 0.2), -0.1, H - 0.15), (1, 0, -0.2), (0, -1, -0.6), 1.0, K)
    return _dims()


# ================================================================== the toadstool ring

def toadstool(prefix, x, y, h, r, K, cap="toadred", glow=False, lean=(0.0, 0.0), rng=None):
    st = _mark()
    lathe(f"{prefix}Stem", [(0, 0), (r * 0.45, 0), (r * 0.36, h * 0.15), (r * 0.28, h * 0.7), (r * 0.3, h), (0, h)], K["toadstem"], seg=12)
    lathe(f"{prefix}Skirt", [(r * 0.28, h * 0.72), (r * 0.5, h * 0.62), (r * 0.48, h * 0.6), (r * 0.28, h * 0.68)], K["toadstem"], seg=12)
    lathe(f"{prefix}Cap", [(0, h - 0.02), (r, h - 0.06), (r * 1.02, h + r * 0.12), (r * 0.85, h + r * 0.45), (r * 0.45, h + r * 0.68), (0, h + r * 0.72)], K[cap],
          seg=20)
    if not glow:
        g = rng or random.Random(int(x * 100))
        for k in range(int(5 + r * 8)):
            a, b = g.uniform(0, 2 * PI), g.uniform(0.15, 0.95)
            rr = r * b
            zz = h + r * 0.72 * (1 - b ** 2) ** 0.8
            sphere(f"{prefix}Spot{k}", r * 0.1, (math.cos(a) * rr, math.sin(a) * rr, zz), K["toadspot"], seg=5, rings=3, scale=(1, 1, 0.45))
    else:
        g0 = P.GROUP
        set_group("Glow")
        lathe(f"{prefix}Gills", [(r * 0.3, h - 0.02), (r * 0.95, h - 0.05), (r * 0.6, h + 0.02), (r * 0.3, h + 0.02)], K["glow"], seg=16)
        set_group(g0)
    _xform(st, T(x, y, 0) @ RX(lean[0]) @ RY(lean[1]))


def toadstool_ring(M):
    """A fairy ring 6.4 across where the witch gathers: fat fly-agaric toadstools (crimson caps spotted in bone, ringed stems)
    in clusters round a ring of deep moss, small violet toadstools whose gills glow (Glow, violet) between them, a few old
    stones and fallen leaves. Don't step in it."""
    K = wk(M)
    rng = RNG(5030)
    g = random.Random(5031)
    B40.ring_slab("MossRing", (0, 0), 2.6, 3.6, 0, 2 * PI, 0.0, 0.08, K["moss2"], n=40, bevel=0.0, ends=False,
                  zfun=lambda x, y: 0.04 * math.sin(x * 2.1) * math.cos(y * 1.7))
    clusters = [0.2, 1.1, 1.9, 2.8, 3.6, 4.5, 5.4]
    k = 0
    for c, a0 in enumerate(clusters):
        n = g.randint(1, 3)
        for j in range(n):
            a = a0 + g.uniform(-0.18, 0.18)
            r = 3.1 + g.uniform(-0.35, 0.35)
            hh = g.uniform(0.6, 1.5) * (1.0 if j == 0 else 0.6)
            toadstool(f"T{k}", math.cos(a) * r, math.sin(a) * r, hh, hh * g.uniform(0.45, 0.6), K, lean=(g.uniform(-0.15, 0.15), g.uniform(-0.15, 0.15)), rng=g)
            k += 1
        a = a0 + 0.45
        for j in range(3):
            toadstool(f"V{c}{j}", math.cos(a + j * 0.07) * (3.0 + j * 0.12), math.sin(a + j * 0.07) * (3.0 + j * 0.12), g.uniform(0.25, 0.45), 0.13, K, cap="toadv",
                      glow=True, lean=(g.uniform(-0.2, 0.2), 0.0))
    for k in range(4):
        a = k * PI / 2 + 0.6
        rock(f"Stone{k}", (math.cos(a) * 3.9, math.sin(a) * 3.9, 0.15), (0.45, 0.4, 0.32), K["field"], rng, bevel=0.2)
    cards = Cards(rng)
    for k in range(16):
        a = g.uniform(0, 2 * PI)
        r = g.uniform(2.6, 3.7)
        if k % 2:
            cards.crossed((math.cos(a) * r, math.sin(a) * r, 0.05), 0.6, 0.6, "grass", k=2)
        else:
            p = (math.cos(a) * r, math.sin(a) * r, 0.1)
            ax, ay = frame(Vector((0, 0, 1)), roll=g.uniform(0, 6.28), up=Vector((0, 1, 0)))
            cards.add(p, ax, ay, 0.5, 0.5, ("crabapple", "rose_leaves")[k % 4 // 2], "fill", nrm=UP)
    leaves_done("ToadstoolRing", cards)
    GLOW["ToadstoolRing"] = {"Glow": VIOLET}
    return _dims()


# ================================================================== the wisp lantern post

def wisp_lantern_post(M):
    """A lantern post outside the hut: a gnarled staff driven into a cairn of mossy stones, crooked up to 8 with a curled branch
    arm; from its tip a crude iron-banded lantern with bottle-glass panes (Glass) and a peaked tin cap hangs on a chain, a
    will-o'-the-wisp curling inside it instead of a candle (Glow, sickly green); a bone charm, a crow feather and a bundle of
    herbs tied to the staff."""
    K = wk(M)
    rng = RNG(5040)
    for k in range(9):
        a = k / 9 * 2 * PI
        r = 0.75 if k % 3 else 0.55
        rock(f"Cairn{k}", (math.cos(a) * r, math.sin(a) * r, 0.25 + (k % 2) * 0.25), (0.65, 0.55, 0.45), K["field"] if k % 3 else K["fielddk"], rng, bevel=0.2)
    rock("CairnTop", (0.05, 0.0, 0.85), (0.8, 0.7, 0.4), K["field"], rng, bevel=0.2)
    staff = crooked((0, 0, 0.2), (0.25, -0.1, 7.6), 0.35, 5041, n=10, perp=(1, 0.2, 0))
    pole("Staff", staff, 0.2, K["deadwood"], seed=5042, seg=9, taper=0.35)
    top = Vector(staff[-1])
    arm = [tuple(top + Vector(v)) for v in ((0, 0, 0), (0.4, -0.05, 0.35), (0.95, -0.1, 0.45), (1.45, -0.1, 0.25), (1.6, -0.1, -0.05), (1.45, -0.1, -0.25))]
    pole("Arm", arm, 0.11, K["deadwood"], seed=5043, seg=7, taper=0.6)
    hx, hy, hz = top.x + 1.5, top.y - 0.1, top.z + 0.3
    B30.chain("Chain", [(hx, hy, hz), (hx, hy, hz - 0.75)], K["iron"], r=0.06, thick=0.015)
    lz = hz - 2.35                              # the lantern's foot
    s = _mark()
    lathe("Base", [(0, 0), (0.42, 0), (0.45, 0.1), (0.4, 0.18), (0, 0.18)], K["tin"], seg=6)
    for k in range(6):
        a = k / 6 * 2 * PI
        tube(f"Upright{k}", [(math.cos(a) * 0.4, math.sin(a) * 0.4, 0.15), (math.cos(a) * 0.4, math.sin(a) * 0.4, 1.15)], 0.035, K["iron"], poly=True)
    for z in (0.18, 1.12):
        hoop(f"Band{z}", (0, 0, z), 0.41, "Z", K["iron"], thick=0.03)
    cone("Cap", 0.55, 0.06, 0.45, (0, 0, 1.38), K["tin"], verts=6)
    hoop("Ring", (0, 0, 1.68), 0.08, "Y", K["iron"], thick=0.02)
    set_group("Glass")
    lathe("Panes", [(0.38, 0.17), (0.38, 1.14)], K["glass"], seg=6)
    set_group("Glow")         # the wisp: a curling flame with a tail spiralling up
    lathe("Wisp", [(0, 0.35), (0.12, 0.42), (0.16, 0.55), (0.1, 0.72), (0.04, 0.85), (0, 0.9)], K["glow"], seg=10)
    pts = [(math.cos(t * 3.5 * PI) * 0.14 * (1 - t), math.sin(t * 3.5 * PI) * 0.14 * (1 - t), 0.5 + t * 0.55) for t in [i / 16 for i in range(17)]]
    bar("WispTail", pts, lambda t: 0.04 * (1 - t) + 0.005, K["glow"], seg=6)
    set_group("Main")
    _xform(s, T(hx, hy, lz))
    # charms tied to the staff
    p = Vector(staff[5])
    hoop("Tie", tuple(p + Vector((0, 0, 0.0))), 0.22, "Z", K["twine"], thick=0.025)
    skull_small("Charm", T(p.x + 0.05, p.y - 0.3, p.z - 0.45) @ RX(-0.1), K, s=0.35)
    string("CharmStr", tuple(p + Vector((0.05, -0.2, 0))), (p.x + 0.05, p.y - 0.3, p.z - 0.32), K)
    feather("Crow", tuple(p + Vector((-0.15, -0.18, -0.05))), (-0.3, -0.2, -1), 0.8, K, w=0.11)
    cards = Cards(rng)
    herb_bundle("Herbs", tuple(p + Vector((0.2, -0.18, 0.0))), 0.9, K["herbg"], K, cards, "fern", rng)
    ground_cards(cards, rng, -1.2, 1.2, -1.2, 1.2, 8)
    leaves_done("WispLanternPost", cards)
    GLOW["WispLanternPost"] = {"Glow": GREEN, "Glass": (170, 210, 170)}
    return _dims()


# ================================================================== preview and registration

def preview(objs, name, dims, suffix=""):
    """nh_props.preview's warm key, violet fill and crimson rim on a dark floor, with the Glow / Glow2 / Glass pieces in their
    template colours and a closer camera for the small pieces; the night fog of the woods in the background."""
    sc = bpy.context.scene
    cols = GLOW.get(name, {})
    for ob in objs:
        suf = ob.name.rsplit("_", 1)[-1] if "_" in ob.name else ""
        if suf not in ("Glow", "Glow2", "Glass"):
            continue
        dflt = {"Glow": GREEN, "Glow2": FIRE, "Glass": (200, 225, 210)}[suf]
        rgb = tuple(c / 255 for c in cols.get(suf, dflt))
        m = bpy.data.materials.new(f"Preview{suf}")
        m.use_nodes = True
        bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        if suf == "Glass":
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Roughness"].default_value = 0.08
            bs.inputs["Transmission Weight"].default_value = 1.0
        else:
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 2.2 if suf == "Glow" else 3.0
        ob.data.materials.clear()
        ob.data.materials.append(m)
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.028, 0.04, 1)
    bpy.context.view_layer.update()
    lo = [min((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    hi = [max((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    ctr = Vector([(a + b) / 2 for a, b in zip(lo, hi)])
    size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) * P.PREVIEW_PAD.get(name, 1.0)
    k2 = (size / 6.0) ** 2 if size < 6.0 else size / 6.0
    zc = ctr.z

    def light(kind, loc, energy, color, s=2.0):
        L = bpy.data.lights.new(kind, kind)
        L.energy = energy
        L.color = color
        if kind == "AREA":
            L.size = s
        o = bpy.data.objects.new(kind, L)
        o.location = loc
        bpy.context.collection.objects.link(o)
        o.rotation_euler = (Vector((ctr.x, ctr.y, zc)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    light("AREA", (ctr.x + size * 0.9, ctr.y - size * 1.2, size * 1.2), 3100 * k2, (1.0, 0.84, 0.66), s=size * 0.8)
    light("AREA", (ctr.x - size * 1.3, ctr.y - size * 0.5, size * 0.6), 850 * k2, (0.55, 0.55, 0.95), s=size)
    light("AREA", (ctr.x - size * 0.3, ctr.y + size * 1.4, size * 1.1), 2200 * k2, (0.75, 0.4, 0.55), s=size)
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(ctr.x, ctr.y, min(0.0, lo[2])))
    fl = bpy.context.active_object
    fl.data.materials.append(P.material("Floor47", "NH_Boards", tint=(0.2, 0.17, 0.14), scale=0.12))
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    bpy.context.collection.objects.link(co)
    el = math.radians(CAM_EL.get(name, 22))
    az = Vector((1.15, -1.65, 0)).normalized()
    if name in CAM_AZ:
        a = math.radians(CAM_AZ[name])
        az = Vector((math.sin(a), -math.cos(a), 0))
    dist = size * 2.15
    co.location = ctr + Vector((az.x * math.cos(el), az.y * math.cos(el), math.sin(el))) * dist
    co.rotation_euler = (ctr - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}{suffix}.png")
    bpy.ops.render.render(write_still=True)


CAM_EL = {}       # prop -> camera elevation in degrees (default 22)
CAM_AZ = {}       # prop -> camera azimuth in degrees round from the front (default about 35 to the right)

BUILDERS = {
    "HutFooting": hut_footing,
    "HutPost": hut_post,
    "HutWall": lambda M: hut_wall(M, "plain"),
    "HutWallWindow": lambda M: hut_wall(M, "window"),
    "HutWallDoor": lambda M: hut_wall(M, "door"),
    "HutGable": hut_gable,
    "HutRoof": hut_roof,
    "HutRidge": hut_ridge,
    "HutChimney": hut_chimney,
    "HutPorch": hut_porch,
    "WitchCauldron": witch_cauldron,
    "HerbBeamRack": herb_beam_rack,
    "WitchJarShelf": witch_jar_shelf,
    "BroomCorner": broom_corner,
    "SpellLectern": spell_lectern,
    "BoneChimes": bone_chimes,
    "HearthKettle": hearth_kettle,
    "StrawBed": straw_bed,
    "WitchWorkTable": witch_work_table,
    "WitchHatStand": witch_hat_stand,
    "CatBasket": cat_basket,
    "GourdPile": gourd_pile,
    "BraidedRug": braided_rug,
    "SpellNoteShelf": spell_note_shelf,
    "ToadstoolRing": toadstool_ring,
    "WispLanternPost": wisp_lantern_post,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.0 for n in BUILDERS})
P.OPEN_DEG.update({"HutWallDoor_Door0": 100})
CAM_EL.update({"BraidedRug": 55, "ToadstoolRing": 38, "GourdPile": 30, "CatBasket": 38, "WitchWorkTable": 32, "HutRoof": 16, "HutRidge": 24,
               "HerbBeamRack": 15, "WitchCauldron": 30, "StrawBed": 34, "HutFooting": 25})
CAM_AZ.update({"HutRoof": 62, "HutRidge": 40})
