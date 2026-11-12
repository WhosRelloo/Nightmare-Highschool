"""Props batch 54: the concession consumables kit (Mrs. Okada's stand, Services.Features.Concession).

Every snack, drink, sweet and candy the stand sells, the lunch meals for a future lunch period, and the cups, wrappers and stock
that dress the stand. The owner asked for "a BUNCH of items: snacks, drinks, candy, hot food, sweets, wrappers and cups, enough
to fully stock the stand" (2026-11-12), approved the list, then asked for "more DETAILED and higher quality" models, "wayyy
cooler" packaging (a look per brand) and "lunch meals for when we add a lunch period" (Japanese set meals, gothic house meals
and lunch extras).

Ten sheet props, each one bake (one 2048 map set shared by its items) and one FBX whose pieces are the items, one piece each
(`<Sheet>_<ItemId>`, the Config.Items Id for things that are sold). Drinks in glass and the candy jars also have a `_Glass` piece
(see-through in Roblox).

  ConcessionBakery      Onigiri, MelonBread, YakisobaBun, GarlicBread, CurryBread, Nikuman, Taiyaki, CreamPuff
  ConcessionHotFood     Bento, MeatLoaf, TakoyakiBoat, CupRamen, RoastSweetPotato, YakitoriSkewers, PumpkinSoup
  ConcessionDrinks      Ramune, BarleyTea, CannedCoffee, RedLantern, HolyLemonade, BlackCatCola, GreenTea, StrawberryMilk
  ConcessionSweets      HotCocoa, MelonSoda, PuddingCup, EctoJelly, MoonCake, Dango, TombstoneCookie
  ConcessionCandy       BatGummies, CandyApple, GhostMints, KonpeitoStars, LicoriceWhips, ChocolateBar, Senbei, GraveCrisps,
                        Popcorn, PrankKit
  ConcessionLunchSets   KatsuCurry, ShoyuRamen, KaraageSet, MackerelSet, Omurice           (lunch trays)
  ConcessionLunchHouse  WitchingStew, ShepherdsPie, PumpkinGratin, RavensRoast             (lunch trays)
  ConcessionLunchExtras FruitCup, SideSalad, RiceBowl, MisoSoup, ChocolateMilk
  ConcessionCounterware CupStack, LidStack, StrawHolder, NapkinDispenser, BoatStack, SkewerCup, SoyBottle, MustardBottle,
                        LitterFilm, LitterChipBag, LitterWrappers, LitterCan
  ConcessionStock       JarGummies, JarKonpeito, JarMints, BottleCrate, CanTray, BentoStack, BunTray

Printed labels come from art/props/concession_atlas.py (ConcessionPrint), mapped through the "Spine" UV layer like the library
and interiors kits. Sizes are in studs, a little larger than life so they read in a hand (a can is 0.62 tall, a lunch tray
1.3 x 0.95). Every item stands on z = 0, centred on x = y = 0 before it is moved into its sheet's row; fronts face -Y. All names
and designs are invented; no gore (the red on the trays is pickles, glaze and enamel).
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, hoop, leaf, _mark, _xform, _dims, flat
import nh_props_batch24 as B24
import nh_props_batch30 as B30
import nh_props_batch43 as B43

PI = math.pi
DEG = PI / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T

CA = json.load(open(os.path.join(P.HERE, "concession_atlas.json")))
for _k, _v in CA["regions"]["ConcessionPrint"].items():
    B30.REG["CP_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_CP_" + _k[7:]] = _v
MISSING = set()


def ck(key):
    """A ConcessionPrint region key, falling back to plain paper (and noted) if the atlas doesn't have it yet."""
    if "CP_" + key not in B30.REG:
        MISSING.add(key)
        B30.REG["CP_" + key] = B30.REG["CP_Swatch_paper"]
    return key


def ce(edge):
    if "Swatch_CP_" + edge not in B30.REG:
        MISSING.add("Swatch_" + edge)
        B30.REG["Swatch_CP_" + edge] = B30.REG["Swatch_CP_paper"]
        B30.REG["CP_Swatch_" + edge] = B30.REG["Swatch_CP_paper"]
    return edge


ITEM = ["Main"]


def as_glass():
    """Parts built after this go in the current item's see-through `_Glass` piece."""
    set_group(ITEM[0] + "_Glass")


def as_main():
    set_group(ITEM[0])


# ------------------------------------------------------------------ materials

def food(name, rgb, rough, bump=0.0, scale=60.0, var=None, var_scale=12.0, dirt=0.15, cells=0.0):
    """Food: a plain colour with a fine noise bump, optionally a second colour mottled through it (crust, char, seeds) and a
    cellular bump (cells = Voronoi scale: crumb, rice grains, panko)."""
    m = flat(name, rgb, rough, dirt=dirt)
    nt = m.node_tree
    h = None
    if bump:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8
        nt.links.new(B24._coords(nt), nz.inputs["Vector"])
        h = nz.outputs["Fac"]
    if cells:
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "F1"; vo.inputs["Scale"].default_value = cells
        nt.links.new(B24._coords(nt), vo.inputs["Vector"])
        c = B24._math(nt, "POWER", vo.outputs["Distance"], 0.6)
        h = c if h is None else B24._math(nt, "ADD", B24._math(nt, "MULTIPLY", h, 0.4), c)
    if h is not None:
        B24._bump(m, h, bump or 0.006)
    if var:
        nv = nt.nodes.new("ShaderNodeTexNoise"); nv.inputs["Scale"].default_value = var_scale; nv.inputs["Detail"].default_value = 4
        nt.links.new(B24._coords(nt), nv.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeMapRange")
        ramp.inputs["From Min"].default_value = 0.42; ramp.inputs["From Max"].default_value = 0.62
        nt.links.new(nv.outputs["Fac"], ramp.inputs["Value"])
        src, dst = B24._colour_in(m)
        nt.links.new(B24._mix_rgb(nt, ramp.outputs["Result"], src, var), dst)
    return m


def striped(name, rgb, stripe, scale, rough=0.5, axis="X", bump=0.0):
    """A colour with soft bands of a second colour along an axis (mackerel skin, chashu fat, naruto, cabbage veins)."""
    m = flat(name, rgb, rough, dirt=0.15)
    nt = m.node_tree
    w = nt.nodes.new("ShaderNodeTexWave"); w.bands_direction = axis; w.inputs["Scale"].default_value = scale
    w.inputs["Distortion"].default_value = 4.0; w.inputs["Detail"].default_value = 3
    nt.links.new(B24._coords(nt), w.inputs["Vector"])
    src, dst = B24._colour_in(m)
    f = B24._math(nt, "GREATER_THAN", w.outputs["Fac"], 0.62)
    nt.links.new(B24._mix_rgb(nt, f, src, stripe), dst)
    if bump:
        B24._bump(m, w.outputs["Fac"], bump)
    return m


def kit(M):
    return {
        "cp": B30.atlas_mat("ConcessionPrintMat", "ConcessionPrint", rough=0.42, leather=0.0, wear=0.0, dirt=0.25),
        # packaging
        "alu": material("CanAlu", base=(0.72, 0.73, 0.76), rough=0.2, metal=1.0, wear=0.0, dirt=0.25),
        "alu_dark": material("CanAluDark", base=(0.5, 0.5, 0.53), rough=0.32, metal=1.0, wear=0.0, dirt=0.3),
        "gilt": material("CapGilt", base=(0.78, 0.56, 0.24), rough=0.28, metal=1.0, wear=0.1, dirt=0.4),
        "paper": food("PaperWhite", (0.8, 0.77, 0.7), 0.85, bump=0.0015, scale=200),
        "kraft": food("Kraft", (0.42, 0.29, 0.16), 0.8, bump=0.002, scale=180),
        "film": flat("ClearFilm", (0.75, 0.75, 0.73), 0.12, dirt=0.1),
                "plastic_red": flat("PlasticCrimson", (0.24, 0.02, 0.035), 0.3),
        "plastic_black": flat("PlasticBlack", (0.025, 0.022, 0.026), 0.35),
        "plastic_blue": flat("PlasticBlue", (0.05, 0.2, 0.45), 0.28),
        "plastic_green": flat("PlasticGreen", (0.08, 0.22, 0.07), 0.3),
        "plastic_cream": flat("PlasticCream", (0.72, 0.68, 0.58), 0.38),
        "glass_teal": flat("GlassTeal", (0.3, 0.55, 0.58), 0.04),
        "glass_dark": flat("GlassDark", (0.12, 0.09, 0.06), 0.04),
        "glass_clear": flat("GlassClear", (0.78, 0.82, 0.82), 0.03),
        "glass_jar": flat("JarGlass", (0.7, 0.74, 0.76), 0.04),
        "marble": flat("Marble", (0.6, 0.78, 0.82), 0.02),
        "lacquer": material("Lacquer", base=(0.022, 0.02, 0.024), rough=0.18, wear=0.12, dirt=0.4),
        "lacquer_red": material("LacquerRed", base=(0.2, 0.014, 0.024), rough=0.2, wear=0.12, dirt=0.4),
        "porcelain": material("Porcelain", base=(0.84, 0.82, 0.76), rough=0.12, wear=0.0, dirt=0.35),
        "glaze_dark": material("GlazeDark", base=(0.05, 0.05, 0.06), rough=0.16, wear=0.05, dirt=0.3),
        "steel": material("Cutlery", base=(0.7, 0.7, 0.72), rough=0.18, metal=1.0, wear=0.0, dirt=0.3),
        "iron": M["iron"],
        "brass": M["brass"],
        "oak": M["oakdark"],
        "pine": material("CratePine", "NH_DeskWood", tint=(0.42, 0.3, 0.18), scale=0.6, rough_add=0.12, wear=0.3, dirt=0.8),
        "enamel": material("TrayEnamel", base=(0.2, 0.014, 0.026), rough=0.28, wear=0.35, wear_metal=True, dirt=0.6),
        "wood": food("SkewerWood", (0.55, 0.42, 0.26), 0.8, bump=0.001, scale=300),
        "string": flat("Twine", (0.5, 0.4, 0.26), 0.9),
        # liquids
        "water": flat("Water", (0.55, 0.62, 0.64), 0.03),
        "cola": flat("ColaLiquid", (0.07, 0.025, 0.01), 0.04),
        "lemonade": flat("Lemonade", (0.85, 0.76, 0.3), 0.04),
        "ramune": flat("RamuneLiquid", (0.6, 0.78, 0.86), 0.04),
        "greentea": flat("GreenTeaLiquid", (0.45, 0.5, 0.15), 0.04),
        "syrup": flat("Syrup", (0.82, 0.74, 0.5), 0.04),
        "broth": flat("Broth", (0.32, 0.17, 0.06), 0.06),
        "miso": food("MisoBroth", (0.48, 0.32, 0.14), 0.12, bump=0.001, scale=30, var=(0.58, 0.42, 0.2), var_scale=10),
        "curry": food("Curry", (0.25, 0.12, 0.04), 0.14, bump=0.002, scale=20),
        "gravy": flat("Gravy", (0.16, 0.07, 0.03), 0.12),
        "demi": flat("DemiGlace", (0.13, 0.05, 0.02), 0.1),
        "stew": food("Stew", (0.24, 0.1, 0.04), 0.16, bump=0.002, scale=15),
        "cocoa": flat("Cocoa", (0.14, 0.06, 0.03), 0.15),
        # food
        "rice": food("Rice", (0.86, 0.85, 0.8), 0.55, bump=0.004, scale=90, cells=160),
        "nori": food("Nori", (0.025, 0.045, 0.028), 0.4, bump=0.002, scale=40, var=(0.06, 0.1, 0.05)),
        "melon": food("MelonCrust", (0.8, 0.58, 0.25), 0.62, bump=0.003, scale=90, var=(0.9, 0.78, 0.5), var_scale=30, cells=220),
        "melon_groove": food("MelonGroove", (0.62, 0.38, 0.14), 0.7, bump=0.002, scale=60),
        "bun": food("BunCrust", (0.5, 0.26, 0.08), 0.45, bump=0.002, scale=30, var=(0.66, 0.4, 0.15), var_scale=6),
        "noodle": food("Noodle", (0.62, 0.4, 0.18), 0.32, bump=0.001, scale=200),
        "noodle_pale": food("RamenNoodle", (0.86, 0.72, 0.4), 0.35, bump=0.001, scale=200),
        "ginger": flat("PickledGinger", (0.6, 0.06, 0.08), 0.3),
        "aonori": food("Aonori", (0.12, 0.3, 0.08), 0.6),
        "crumb": food("Breadcrumb", (0.62, 0.38, 0.12), 0.75, bump=0.012, scale=70, var=(0.45, 0.24, 0.07), var_scale=40, cells=90),
        "garlic": food("GarlicButter", (0.78, 0.6, 0.28), 0.45, bump=0.006, scale=50, var=(0.22, 0.4, 0.08), var_scale=55, cells=60),
        "crust": food("Crust", (0.5, 0.28, 0.1), 0.6, bump=0.004, scale=40, var=(0.36, 0.18, 0.05), var_scale=12),
        "crumbin": food("BreadCrumbIn", (0.86, 0.76, 0.56), 0.8, bump=0.006, scale=30, cells=70),
        "steamed": food("SteamedBun", (0.9, 0.88, 0.82), 0.62, bump=0.002, scale=30),
        "taiyaki": food("Taiyaki", (0.62, 0.36, 0.12), 0.5, bump=0.004, scale=35, var=(0.4, 0.2, 0.06), var_scale=8, cells=45),
        "puff": food("CreamPuff", (0.7, 0.46, 0.18), 0.7, bump=0.01, scale=25, var=(0.86, 0.84, 0.8), var_scale=10),
        "cream": food("WhippedCream", (0.9, 0.88, 0.8), 0.45, bump=0.004, scale=40),
        "tako": food("Takoyaki", (0.52, 0.3, 0.11), 0.5, bump=0.005, scale=30, var=(0.36, 0.18, 0.06)),
        "sauce": flat("TakoSauce", (0.08, 0.03, 0.015), 0.14),
        "mayo": flat("Mayo", (0.88, 0.86, 0.72), 0.22),
        "bonito": food("Bonito", (0.66, 0.46, 0.32), 0.7, bump=0.003, scale=120),
        "skin": food("SweetPotatoSkin", (0.24, 0.05, 0.08), 0.5, bump=0.006, scale=25, var=(0.16, 0.03, 0.05)),
        "imo": food("SweetPotato", (0.88, 0.64, 0.16), 0.55, bump=0.008, scale=40),
        "chicken": food("Yakitori", (0.46, 0.22, 0.07), 0.3, bump=0.008, scale=30, var=(0.18, 0.07, 0.02)),
        "negi": food("Negi", (0.55, 0.68, 0.36), 0.4, var=(0.85, 0.86, 0.72)),
        "soup": food("PumpkinSoup", (0.82, 0.4, 0.06), 0.3, bump=0.002, scale=20),
        "meatloaf": food("MeatLoaf", (0.3, 0.14, 0.07), 0.6, bump=0.008, scale=40),
        "pudding": food("Custard", (0.92, 0.7, 0.22), 0.25, bump=0.001),
        "caramel": flat("Caramel", (0.26, 0.09, 0.02), 0.1),
        "jelly": flat("Ectoplasm", (0.45, 0.86, 0.56), 0.04),
        "jelly_eye": flat("JellyEye", (0.08, 0.2, 0.12), 0.1),
        "mooncake": food("MoonCake", (0.62, 0.36, 0.12), 0.5, bump=0.004, scale=30),
        "dango_pink": food("DangoPink", (0.9, 0.56, 0.62), 0.5, bump=0.002),
        "dango_white": food("DangoWhite", (0.9, 0.88, 0.82), 0.5, bump=0.002),
        "dango_green": food("DangoGreen", (0.42, 0.62, 0.3), 0.5, bump=0.002),
        "shortbread": food("Shortbread", (0.72, 0.52, 0.26), 0.7, bump=0.006, scale=60),
        "candy_red": flat("CandyGlaze", (0.34, 0.02, 0.04), 0.04),
        "choc": food("Chocolate", (0.09, 0.04, 0.02), 0.28, bump=0.001),
        "foil": material("Foil", base=(0.72, 0.73, 0.76), rough=0.18, metal=1.0, wear=0.0, dirt=0.2),
        "foil_gold": material("FoilGold", base=(0.8, 0.6, 0.26), rough=0.2, metal=1.0, wear=0.0, dirt=0.2),
        "licorice": food("Licorice", (0.015, 0.012, 0.014), 0.22, bump=0.002, scale=50),
        "senbei": food("Senbei", (0.5, 0.28, 0.1), 0.32, bump=0.008, scale=25, var=(0.3, 0.14, 0.04), cells=30),
        "popcorn": food("Popcorn", (0.93, 0.86, 0.62), 0.75, bump=0.01, scale=30, var=(0.82, 0.6, 0.25)),
        "gum_red": flat("GummyRed", (0.42, 0.02, 0.05), 0.12),
        "gum_violet": flat("GummyViolet", (0.18, 0.03, 0.28), 0.12),
        "gum_green": flat("GummyGreen", (0.12, 0.38, 0.05), 0.12),
        "k_pink": flat("KonpeitoPink", (0.9, 0.52, 0.62), 0.45),
        "k_yellow": flat("KonpeitoYellow", (0.92, 0.84, 0.45), 0.45),
        "k_blue": flat("KonpeitoBlue", (0.45, 0.68, 0.9), 0.45),
        "k_white": flat("KonpeitoWhite", (0.92, 0.92, 0.9), 0.45),
        "mint": flat("Mint", (0.88, 0.92, 0.9), 0.32),
        "straw_red": flat("StrawRed", (0.5, 0.05, 0.06), 0.28),
        "panko": food("Panko", (0.7, 0.44, 0.14), 0.8, bump=0.014, scale=80, var=(0.5, 0.27, 0.07), var_scale=30, cells=110),
        "pork": striped("Chashu", (0.55, 0.3, 0.2), (0.86, 0.74, 0.6), 18, rough=0.35, axis="Z"),
        "egg_white": flat("EggWhite", (0.9, 0.88, 0.82), 0.25),
        "yolk": flat("Yolk", (0.92, 0.5, 0.06), 0.15),
        "omelette": food("Omelette", (0.95, 0.74, 0.2), 0.3, bump=0.002, scale=12, var=(0.85, 0.58, 0.12), var_scale=5),
        "naruto": striped("Naruto", (0.92, 0.9, 0.86), (0.85, 0.4, 0.5), 30, rough=0.4, axis="X"),
        "menma": striped("Menma", (0.66, 0.5, 0.22), (0.5, 0.36, 0.14), 40, rough=0.4, axis="Z"),
        "tofu": flat("Tofu", (0.9, 0.88, 0.8), 0.5),
        "wakame": flat("Wakame", (0.06, 0.16, 0.06), 0.2),
        "karaage": food("Karaage", (0.55, 0.3, 0.08), 0.5, bump=0.012, scale=40, var=(0.35, 0.16, 0.04), var_scale=20, cells=60),
        "cabbage": striped("Cabbage", (0.72, 0.82, 0.5), (0.92, 0.94, 0.82), 50, rough=0.5, axis="Y"),
        "lemon": flat("Lemon", (0.95, 0.82, 0.2), 0.35),
        "lemon_flesh": food("LemonFlesh", (0.98, 0.92, 0.5), 0.3, cells=40, bump=0.003),
        "mackerel": striped("MackerelSkin", (0.46, 0.5, 0.56), (0.12, 0.14, 0.18), 22, rough=0.25, axis="X", bump=0.002),
        "char": flat("CharMark", (0.08, 0.05, 0.03), 0.6),
        "daikon": food("Daikon", (0.92, 0.9, 0.84), 0.55, bump=0.004, scale=80, cells=150),
        "pickle": flat("Pickle", (0.75, 0.62, 0.1), 0.35),
        "fukujin": flat("Fukujinzuke", (0.55, 0.1, 0.08), 0.3),
        "carrot": food("Carrot", (0.85, 0.36, 0.06), 0.4, bump=0.003, scale=60),
        "potato": food("Potato", (0.86, 0.72, 0.4), 0.55, bump=0.006, scale=40),
        "roastpot": food("RoastPotato", (0.75, 0.5, 0.2), 0.45, bump=0.008, scale=30, var=(0.5, 0.28, 0.08), var_scale=10),
        "beef": food("StewBeef", (0.24, 0.1, 0.05), 0.4, bump=0.01, scale=40),
        "mash": food("Mash", (0.92, 0.84, 0.6), 0.5, bump=0.004, scale=30, var=(0.72, 0.46, 0.16), var_scale=14),
        "pumpkin": food("PumpkinRind", (0.8, 0.34, 0.05), 0.35, bump=0.003, scale=20, var=(0.62, 0.24, 0.03), var_scale=6),
        "stem": food("PumpkinStem", (0.22, 0.2, 0.1), 0.7, bump=0.004, scale=40),
        "gratin": food("Gratin", (0.88, 0.7, 0.32), 0.4, bump=0.008, scale=25, var=(0.55, 0.32, 0.1), var_scale=12),
        "roast": food("RoastSkin", (0.55, 0.28, 0.08), 0.32, bump=0.008, scale=30, var=(0.35, 0.15, 0.04), var_scale=10),
        "bone": flat("Bone", (0.86, 0.8, 0.68), 0.5),
        "herb": flat("Herb", (0.12, 0.28, 0.08), 0.5),
        "lettuce": food("Lettuce", (0.42, 0.66, 0.2), 0.45, bump=0.003, scale=25, var=(0.7, 0.85, 0.45), var_scale=8),
        "tomato": flat("Tomato", (0.7, 0.08, 0.04), 0.2),
        "cucumber": striped("Cucumber", (0.72, 0.84, 0.52), (0.1, 0.3, 0.08), 3, rough=0.3, axis="Z"),
        "peach": flat("Peach", (0.95, 0.62, 0.22), 0.2),
        "pineapple": flat("Pineapple", (0.96, 0.84, 0.3), 0.25),
        "grape": flat("Grape", (0.45, 0.6, 0.18), 0.12),
        "cherry": flat("Cherry", (0.55, 0.03, 0.06), 0.1),
        "umeboshi": food("Umeboshi", (0.45, 0.06, 0.08), 0.3, bump=0.004, scale=40),
        "sesame": flat("Sesame", (0.04, 0.035, 0.03), 0.4),
    }


# ------------------------------------------------------------------ geometry helpers

def _bm_uv(bm):
    return bm.loops.layers.uv.new("Spine"), bm.faces.layers.float.new("nh_uvk")


def band(name, key, r0, r1, z0, z1, K, n=36, k=2.4, sy=1.0, mtx=None, rows=1):
    """A printed band all the way round a can, bottle or cup (radius r0 at z0 to r1 at z1), the region once round.
    The region's u = 0 is at the front (-Y) and runs counter-clockwise, so a wrap drawn with its front panel at u = 0.25 (as
    ConcessionPrint's are) faces +X here, Roblox -X: tools/props/concession_kit_templates.luau turns those items (FRONT_YAW)."""
    u0, v0, u1, v1 = B30.REG["CP_" + ck(key)]
    bm = bmesh.new()
    uvl, kl = _bm_uv(bm)
    rr = [[bm.verts.new((math.cos(-PI / 2 + 2 * PI * i / n) * (r0 + (r1 - r0) * j / rows),
                         math.sin(-PI / 2 + 2 * PI * i / n) * (r0 + (r1 - r0) * j / rows) * sy, z0 + (z1 - z0) * j / rows)) for i in range(n)]
          for j in range(rows + 1)]
    for j in range(rows):
        for i in range(n):
            ii = (i + 1) % n
            f = bm.faces.new((rr[j][i], rr[j][ii], rr[j + 1][ii], rr[j + 1][i]))
            f.smooth = True
            f[kl] = k
            uj = (i + 1) / n
            for lp, (uu, vv) in zip(f.loops, ((i / n, j / rows), (uj, j / rows), (uj, (j + 1) / rows), (i / n, (j + 1) / rows))):
                lp[uvl].uv = (u0 + uu * (u1 - u0), v0 + vv * (v1 - v0))
    # counter-clockwise from above, bottom ring first: every face already faces out
    return B30._bm_object(name, bm, K["cp"], mtx or Matrix.Identity(4))


def pdisc(name, key, r, z, K, n=36, k=2.4, sy=1.0, mtx=None, down=False):
    """A flat printed disc facing up (or down) at height z, the region's inscribed circle on it."""
    u0, v0, u1, v1 = B30.REG["CP_" + ck(key)]
    bm = bmesh.new()
    uvl, kl = _bm_uv(bm)
    vs = [bm.verts.new((math.cos(2 * PI * i / n) * r, math.sin(2 * PI * i / n) * r * sy, z)) for i in range(n)]
    f = bm.faces.new(list(reversed(vs)) if down else vs)
    f[kl] = k
    for lp in f.loops:
        x, y, _ = lp.vert.co
        lp[uvl].uv = (u0 + (0.5 + x / (2 * r)) * (u1 - u0), v0 + (0.5 + y / (2 * r * sy)) * (v1 - v0))
    return B30._bm_object(name, bm, K["cp"], mtx or Matrix.Identity(4))


def pbox(name, w, d, h, K, faces, edge, z0=0.0, k=2.4, mtx=None, taper=1.0):
    """A box w x d x h standing on z0; faces = {"-y": region, "+y": ..., "+z": ..., "-x": ..., "+x": ...} printed (each region
    stretched over its face, read upright from outside); other faces take the `edge` swatch. taper > 1 widens the top."""
    bm = bmesh.new()
    uvl, kl = _bm_uv(bm)
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        s = taper if v.co.z > 0 else 1.0
        v.co = Vector((v.co.x * w * s, v.co.y * d * s, v.co.z * h + h / 2 + z0))
    bm.normal_update()
    sw = B30._swatch("CP_" + ce(edge))
    for f in bm.faces:
        n = f.normal
        key, tagf = None, None
        for tag, axis, sign in (("-y", 1, -1), ("+y", 1, 1), ("+z", 2, 1), ("-z", 2, -1), ("-x", 0, -1), ("+x", 0, 1)):
            if n[axis] * sign > 0.6:
                key, tagf = faces.get(tag), tag
                break
        if not key:
            for lp in f.loops:
                lp[uvl].uv = sw
            f[kl] = 0.5
            continue
        u0, v0, u1, v1 = B30.REG["CP_" + ck(key)]
        up = Vector((0, 0, 1)) if tagf[1] != "z" else Vector((0, 1, 0))
        right = up.cross(n).normalized()
        if tagf == "-z":
            up, right = Vector((0, -1, 0)), Vector((1, 0, 0))
        cs = [lp.vert.co for lp in f.loops]
        xs = [c.dot(right) for c in cs]
        ys = [c.dot(up) for c in cs]
        for lp in f.loops:
            fx = (lp.vert.co.dot(right) - min(xs)) / (max(xs) - min(xs))
            fy = (lp.vert.co.dot(up) - min(ys)) / (max(ys) - min(ys))
            lp[uvl].uv = (u0 + fx * (u1 - u0), v0 + fy * (v1 - v0))
        f[kl] = k
    return B30._bm_object(name, bm, K["cp"], mtx or Matrix.Identity(4))


def pplate(name, key, poly, depth, K, edge, mtx, both=False):
    return B43.pprism(name, "CP_" + ck(key), poly, depth, mtx, K["cp"], "CP_" + ce(edge), k=2.4, both=both)


def flatcard(name, key, w, d, x, y, z, K, edge="paper", yaw=0.0, t=0.004):
    """A printed card lying flat, face up (w along X, d along Y), its bottom at z."""
    return pplate(name, key, B43.rect(w, d, 0), t, K, edge, T(x, y, z + t / 2) @ RZ(yaw) @ RX(-90 * DEG))


def recolour(o, mat):
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def organic(o, strength=0.008, size=0.04, levels=1):
    """Soften a part and push its surface about with cloud noise (rice, crumb, dough, roast skin): subdivision, then a
    displacement."""
    s = o.modifiers.new("Sub", "SUBSURF")
    s.levels = s.render_levels = levels
    tex = bpy.data.textures.new(f"{o.name}_n", "CLOUDS")
    tex.noise_scale = size
    tex.noise_depth = 2
    d = o.modifiers.new("Disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.mid_level = 0.5
    return o


def lumpy(name, r, loc, mat, scale=(1, 1, 1), amt=0.12, seed=1, seg=14, rings=9):
    o = sphere(name, r, loc, mat, seg=seg, rings=rings, scale=scale)
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co = v.co * (1 + rnd.uniform(-amt, amt) * 0.5)
    return o


def spiky(name, r, loc, mat, seed=0):
    """A konpeito sugar star: a small ball with knobs."""
    o = sphere(name, r, loc, mat, seg=12, rings=7)
    rnd = random.Random(seed)
    for v in o.data.vertices:
        v.co = v.co * (1.0 + (0.45 if rnd.random() < 0.35 else 0.0))
    return o


def stick(name, a, b, r, K, mat=None):
    o = tube(name, [a, b], r, K["wood"], poly=True, res=1)
    return recolour(o, mat) if mat is not None else o


def crimp(name, w, z, K, col, h=0.06, teeth=0.012, up=True):
    """A heat-sealed crimp strip w wide and h tall, its outer edge (top if up) cut in a row of small teeth."""
    n = max(8, int(w / 0.028))
    poly = []
    zt, zb = (z + h, z) if up else (z, z + h)
    poly.append((-w / 2, zb))
    for i in range(n + 1):
        x = -w / 2 + w * i / n
        poly.append((x, zt))
        if i < n:
            poly.append((x + w / n / 2, zt - (teeth if up else -teeth)))
    poly.append((w / 2, zb))
    if not up:
        poly.reverse()
    o = B43.pprism(name, "CP_Swatch_" + ce(col), poly, 0.012, Matrix.Identity(4), K["cp"], "CP_" + ce(col))
    # the crimp's fine vertical ribs, as a bump through the bake
    return o


def pillow(name, w, h, d, K, front, back, seal_col, n=16, m=22, seal=0.065):
    """A sealed snack bag standing up: a front and a back sheet bulging apart in the middle and pinching flat into the crimped
    top and bottom seals; a fin seal down the back, a hang hole in the top seal. The print on the front (-Y) and back."""
    bm = bmesh.new()
    uvl, kl = _bm_uv(bm)
    rows = {}
    z0, z1 = seal * 0.6, h - seal * 0.6
    for side, key in ((-1, front), (1, back)):
        reg = B30.REG["CP_" + ck(key)]
        g = []
        for j in range(m + 1):
            t = j / m
            z = z0 + t * (z1 - z0)
            p = min(1.0, max(0.0, min(t, 1 - t) / 0.2))
            pinch = p * p * (3 - 2 * p)
            row = []
            for i in range(n + 1):
                s = i / n
                x = (s - 0.5) * w * (1 - 0.05 * pinch)
                bulge = math.sin(PI * s) ** 0.6 * pinch
                # soft wrinkles across the film
                wr = 0.004 * math.sin(s * 23 + t * 7) * math.sin(t * PI)
                row.append(bm.verts.new((x, side * (0.005 + d / 2 * bulge + wr), z)))
            g.append(row)
        rows[side] = (g, reg)
    for side in (-1, 1):
        g, (u0, v0, u1, v1) = rows[side]
        for j in range(m):
            for i in range(n):
                q = (g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i])
                f = bm.faces.new(q if side == 1 else tuple(reversed(q)))
                f.smooth = True
                f[kl] = 2.2
                for lp in f.loops:
                    x, _, z = lp.vert.co
                    fx = 0.5 + x / w
                    if side == 1:
                        fx = 1 - fx
                    lp[uvl].uv = (u0 + fx * (u1 - u0), v0 + (z - z0) / (z1 - z0) * (v1 - v0))
    gF, _ = rows[-1]
    gB, _ = rows[1]
    sw = B30._swatch("CP_" + ce(seal_col))
    for i in (0, n):
        for j in range(m):
            q = (gF[j][i], gF[j + 1][i], gB[j + 1][i], gB[j][i])
            f = bm.faces.new(q if i == 0 else tuple(reversed(q)))
            f[kl] = 0.4
            for lp in f.loops:
                lp[uvl].uv = sw
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = B30._bm_object(name, bm, K["cp"], Matrix.Identity(4))
    crimp(f"{name}CrimpTop", w, h - seal, K, seal_col, h=seal)
    crimp(f"{name}CrimpBot", w, 0.0, K, seal_col, h=seal, up=False)
    cyl(f"{name}Hole", 0.018, 0.014, (0, 0, h - seal * 0.45), K["plastic_black"], rot=(PI / 2, 0, 0), verts=12, bevel=0.0)
    return ob


def sealed_lid(name, key, r, z, K):
    """A printed peel-off lid sealed flat on a cup's rim at height z, its film pull tab sticking out at the front (-Y).
    (A lid folded back open needs a foil underside a hair from its print, and two faces that close bake streaks in through the
    weathering's edge rounding, so the cups are sold sealed.)"""
    pdisc(name, key, r, z + 0.002, K, n=48)
    box(f"{name}Tab", (0.06, 0.05, 0.003), (0, -r - 0.018, z + 0.0015), K["film"], bevel=0.0)


def rolled_rim(name, r, z, mat, thick=0.008):
    return hoop(name, (0, 0, z), r, "Z", mat, thick=thick)


def chopsticks(prefix, x, y, z, K, yaw=0.0, length=0.78):
    """A pair of lacquered chopsticks with crimson tips, lying side by side."""
    st = _mark()
    for i, dy in enumerate((-0.022, 0.022)):
        lathe(f"{prefix}{i}", [(0, -length / 2), (0.007, -length / 2 + 0.005), (0.011, length / 2 - 0.01), (0, length / 2)],
              K["lacquer"], seg=8, loc=(0, 0, 0))
        P.PARTS[-1].matrix_world = T(0, dy, 0) @ RX(0) @ RY(90 * DEG)
        lathe(f"{prefix}{i}t", [(0.0075, -length / 2 + 0.06), (0.0079, -length / 2 + 0.06), (0.0079, -length / 2 + 0.16),
                                (0.0075, -length / 2 + 0.16)], K["lacquer_red"], seg=8)
        P.PARTS[-1].matrix_world = T(0, dy, 0) @ RY(90 * DEG)
    _xform(st, T(x, y, z + 0.011) @ RZ(yaw))


def spoon(name, x, y, z, K, yaw=0.0, mat=None, s=1.0):
    st = _mark()
    sphere(f"{name}Bowl", 0.05 * s, (0.13 * s, 0, 0.015 * s), mat or K["steel"], seg=16, rings=8, scale=(1.4, 1.0, 0.3))
    box(f"{name}Handle", (0.2 * s, 0.022 * s, 0.008 * s), (-0.03 * s, 0, 0.012 * s), mat or K["steel"], bevel=0.004, rot=(0, -6 * DEG, 0))
    _xform(st, T(x, y, z) @ RZ(yaw))


def fork(name, x, y, z, K, yaw=0.0):
    st = _mark()
    box(f"{name}Handle", (0.2, 0.022, 0.008), (-0.06, 0, 0.012), K["steel"], bevel=0.004)
    box(f"{name}Neck", (0.05, 0.04, 0.006), (0.065, 0, 0.012), K["steel"], bevel=0.002)
    for i in range(4):
        box(f"{name}Tine{i}", (0.07, 0.006, 0.005), (0.125, -0.015 + i * 0.01, 0.012), K["steel"], bevel=0.0015)
    _xform(st, T(x, y, z) @ RZ(yaw))


def knife(name, x, y, z, K, yaw=0.0):
    st = _mark()
    box(f"{name}Handle", (0.17, 0.024, 0.01), (-0.08, 0, 0.012), K["steel"], bevel=0.004)
    B43.pprism(f"{name}Blade", "CP_Swatch_silver" if "CP_Swatch_silver" in B30.REG else "CP_Swatch_alu",
               [(0.0, -0.012), (0.17, -0.012), (0.19, 0.0), (0.16, 0.014), (0.0, 0.012)], 0.004, T(0, 0, 0.012) @ RX(90 * DEG),
               K["steel"], "CP_alu")
    recolour(P.PARTS[-1], K["steel"])
    _xform(st, T(x, y, z) @ RZ(yaw))


# ------------------------------------------------------------------ dishes and the lunch tray

def plate(name, r, K, mat=None, sy=1.0, z=0.0, rim=None):
    """A shallow plate of radius r (oval with sy), its bottom at z, with an optional coloured rim line."""
    lathe(name, [(0, 0), (r * 0.6, 0), (r * 0.62, 0.012), (r * 0.9, 0.03), (r, 0.05), (r * 0.985, 0.058), (r * 0.88, 0.04),
                 (r * 0.6, 0.02), (0, 0.02)], mat or K["porcelain"], seg=40, loc=(0, 0, z), scale=(1, sy))
    if rim is not None:
        o = hoop(f"{name}Rim", (0, 0, z + 0.047), r * 0.96, "Z", rim, thick=0.006)
        o.scale = (1, sy, 1)
    return 0.02 + z


def bowl(name, r, h, K, outer=None, inner=None, z=0.0):
    """A footed bowl: lacquer black outside and crimson inside by default; returns the inside's floor height."""
    lathe(name, [(0, 0), (r * 0.42, 0), (r * 0.44, 0.03), (r * 0.5, 0.032), (r * 0.82, h * 0.4), (r, h), (r * 0.965, h + 0.006),
                 (r * 0.93, h), (r * 0.78, h * 0.42), (r * 0.42, 0.045), (0, 0.045)], outer or K["lacquer"], seg=40, loc=(0, 0, z))
    lathe(f"{name}In", [(0, 0.047), (r * 0.42, 0.047), (r * 0.78, h * 0.42 + 0.002), (r * 0.926, h - 0.002)], inner or K["lacquer_red"],
          seg=40, loc=(0, 0, z))
    return z + 0.047


def surface(name, r, z, mat, sy=1.0, wob=0.0, seed=0):
    """A liquid or mash surface: a thin disc of radius r at height z (its top), optionally wobbly."""
    return lathe(name, [(0, z - 0.012), (r, z - 0.012), (r, z), (0, z + 0.002)], mat, seg=36, scale=(1, sy),
                 jitter=(wob, seed) if wob else None)


def tray(K, W=1.3, D=0.95, mat="Tray_Mat"):
    """The refectory tray: crimson enamel with a rolled lip and a printed paper liner. Returns the liner's top height."""
    box("TrayBase", (W, D, 0.03), (0, 0, 0.015), K["enamel"], bevel=0.05, segments=3)
    r = 0.07
    pts = []
    for cx, cy, a0 in ((W / 2 - r, D / 2 - r, 0), (-W / 2 + r, D / 2 - r, 90), (-W / 2 + r, -D / 2 + r, 180), (W / 2 - r, -D / 2 + r, 270)):
        for k in range(5):
            a = (a0 + k * 22.5) * DEG
            pts.append((cx + math.cos(a) * (r - 0.012), cy + math.sin(a) * (r - 0.012), 0.045))
    tube("TrayLip", pts, 0.02, K["enamel"], closed=True, poly=True)
    for sx in (-1, 1):
        box(f"TrayGrip{sx}", (0.03, 0.26, 0.012), (sx * (W / 2 - 0.05), 0, 0.034), K["iron"], bevel=0.004)
    flatcard("Liner", mat, W - 0.17, D - 0.17, 0, 0, 0.03, K, edge="paper", t=0.004)
    return 0.034


def rice_mound(name, r, x, y, z, K, h=None, sy=1.0):
    o = sphere(name, r, (x, y, z), K["rice"], seg=18, rings=10, scale=(1, sy, (h or r * 0.7) / r))
    return organic(o, 0.008, 0.02)


def miso_bowl(prefix, x, y, z, K):
    st = _mark()
    fl = bowl(f"{prefix}Bowl", 0.17, 0.15, K)
    surface(f"{prefix}Miso", 0.14, 0.12, K["miso"])
    rnd = random.Random(31)
    for i in range(5):
        box(f"{prefix}Tofu{i}", (0.03, 0.03, 0.02), (rnd.uniform(-0.07, 0.07), rnd.uniform(-0.07, 0.07), 0.125), K["tofu"], bevel=0.004,
            rot=(0, 0, rnd.uniform(0, PI)))
    for i in range(4):
        box(f"{prefix}Wakame{i}", (0.05, 0.025, 0.004), (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.123), K["wakame"], bevel=0.001,
            rot=(0, 0, rnd.uniform(0, PI)))
    for i in range(6):
        cyl(f"{prefix}Negi{i}", 0.01, 0.005, (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.124), K["negi"], verts=8, bevel=0.0)
    _xform(st, T(x, y, z))


def rice_bowl(prefix, x, y, z, K, ume=False):
    st = _mark()
    fl = bowl(f"{prefix}Bowl", 0.17, 0.14, K)
    rice_mound(f"{prefix}Rice", 0.14, 0, 0, 0.1, K, h=0.1)
    if ume:
        lumpy(f"{prefix}Ume", 0.035, (0, 0, 0.205), K["umeboshi"], amt=0.15, seed=3)
        rnd = random.Random(8)
        for i in range(14):
            a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0.04, 0.11)
            box(f"{prefix}Ses{i}", (0.008, 0.005, 0.003), (math.cos(a) * rr, math.sin(a) * rr, 0.2 - rr * 0.45), K["sesame"], bevel=0.0,
                rot=(0, 0, rnd.uniform(0, PI)))
    _xform(st, T(x, y, z))


# ------------------------------------------------------------------ items: bakery

def onigiri(K):
    """A triangle of rice, its corners soft, the rice lumpy; a crisp sheet of nori folded up from the bottom, an umeboshi peeking
    out of the top, and the shop's film band label across the front."""
    t = 0.2
    poly = []
    for i in range(48):
        a = -PI / 2 + i / 48 * 2 * PI
        rr = 0.25 * (1 + 0.15 * math.cos(3 * a + PI))
        poly.append((math.cos(a) * rr, 0.2 + math.sin(a) * rr * 0.95))
    lift = 0.006 - min(p[1] for p in poly)
    poly = [(x, z + lift) for x, z in poly]
    o = B43.pprism("Rice", "CP_Swatch_paper", poly, t, Matrix.Identity(4), K["rice"], "CP_paper")
    recolour(o, K["rice"])
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.05; b.segments = 4
    organic(o, 0.006, 0.015)
    zb = min(p[1] for p in poly)
    zt = max(p[1] for p in poly)
    # nori: up the front and back from under the bottom, slightly crinkled
    for side, name in ((-1, "NoriF"), (1, "NoriB")):
        o = box(name, (0.24, 0.007, 0.21), (0, side * (t / 2 + 0.006), zb + 0.105), K["nori"], bevel=0.002)
        organic(o, 0.002, 0.02)
    box("NoriU", (0.24, t + 0.018, 0.007), (0, 0, zb - 0.002), K["nori"], bevel=0.002)
    lumpy("Ume", 0.035, (0.0, -0.02, zt - 0.02), K["umeboshi"], amt=0.15, seed=2)
    pplate("Band", "Onigiri_Band", B43.rect(0.3, 0.06, 0.0), 0.004, K, "film", T(0, -t / 2 - 0.013, zb + 0.26))


def melon_bread(K):
    """A dome of bread under a sugar-cookie crust scored in a diamond lattice (real grooves, not just paint), a sugar sparkle,
    and a paler band round the base where the crust stops."""
    prof = [(0, 0), (0.26, 0), (0.29, 0.012)]
    for k in range(1, 23):
        a = k / 22 * PI / 2
        prof.append((0.3 * math.cos(a) + 0.0001, 0.02 + 0.2 * math.sin(a)))
    prof.append((0, 0.222))
    o = lathe("Dome", prof, K["melon"], seg=64)
    cell, gw, depth = 0.075, 0.16, 0.02
    for v in o.data.vertices:
        x, y, z = v.co
        if z < 0.05:
            continue
        g = 1.0
        for u in ((x + y) / cell, (x - y) / cell):
            d = abs(u - round(u))
            g = min(g, d / gw)
        if g < 1.0:
            nrm = Vector((x, y, z + 0.1)).normalized()
            v.co -= nrm * depth * (1 - g) ** 2 * min(1.0, (z - 0.05) / 0.04)
    lathe("Base", [(0.255, 0.0), (0.285, 0.004), (0.294, 0.022), (0.27, 0.026), (0.25, 0.004)], K["crust"], seg=64)


def yakisoba_bun(K):
    """A glossy hot-dog bun split along the top and stuffed with sauce-fried noodles, pickled ginger, aonori and a mayo zigzag."""
    o = lathe("Bun", [(0, 0), (0.1, 0.0), (0.13, 0.04), (0.135, 0.09), (0.11, 0.14), (0.06, 0.16), (0, 0.165)], K["bun"], seg=32,
              scale=(2.6, 1.0))
    organic(o, 0.006, 0.08)
    # the split: two crumb lips either side of the filling
    for sy in (-1, 1):
        lathe(f"Lip{sy}", [(0, 0.12), (0.035, 0.12), (0.03, 0.15), (0, 0.15)], K["crumbin"], seg=16, loc=(0, sy * 0.05, 0),
              scale=(7.6, 0.8))
    rnd = random.Random(54)
    for i in range(26):
        x0 = rnd.uniform(-0.28, 0.2)
        pts = [(x0 + k * 0.025, rnd.uniform(-0.04, 0.04), 0.155 + 0.03 * math.sin(k * 1.9 + i) + 0.012 * rnd.random()) for k in range(5)]
        tube(f"Noodle{i}", pts, 0.0095, K["noodle"], res=3)
    for i in range(8):
        box(f"Ginger{i}", (0.035, 0.008, 0.008), (rnd.uniform(-0.22, 0.22), rnd.uniform(-0.03, 0.03), 0.2), K["ginger"], bevel=0.002,
            rot=(rnd.uniform(-0.4, 0.4), 0, rnd.uniform(0, PI)))
    for i in range(24):
        box(f"Aonori{i}", (0.008, 0.008, 0.003), (rnd.uniform(-0.26, 0.26), rnd.uniform(-0.045, 0.045), 0.208), K["aonori"], bevel=0.0,
            rot=(0, 0, rnd.uniform(0, PI)))
    tube("Mayo", [(-0.26 + i * 0.065, 0.03 * (-1) ** i, 0.205) for i in range(9)], 0.006, K["mayo"], res=3)


def garlic_bread(K):
    """Two thick slices cut on the bias from a baguette: an open crumb, a ring of crust, garlic butter soaked in and parsley."""
    for i, x in enumerate((-0.16, 0.16)):
        o = cyl(f"Slice{i}", 0.15, 0.1, (x, 0, 0.05), K["crust"], verts=36, bevel=0.025)
        o.scale = (1, 0.7, 1)
        organic(o, 0.004, 0.05)
        o = cyl(f"Top{i}", 0.13, 0.014, (x, 0, 0.102), K["garlic"], verts=36, bevel=0.006)
        o.scale = (1, 0.7, 1)
        rnd = random.Random(i)
        for j in range(10):
            box(f"Parsley{i}{j}", (0.012, 0.01, 0.003), (x + rnd.uniform(-0.09, 0.09), rnd.uniform(-0.06, 0.06), 0.11), K["herb"], bevel=0.0,
                rot=(0, 0, rnd.uniform(0, PI)))


def curry_bread(K):
    """A fried oval bun in coarse panko, a little split at one end showing the curry inside."""
    o = sphere("Body", 0.16, (0, 0, 0.1), K["panko"], seg=32, rings=16, scale=(1.6, 1.0, 0.62))
    organic(o, 0.012, 0.03)
    lumpy("Peek", 0.04, (0.22, -0.02, 0.1), K["curry"], scale=(1.2, 1, 0.6), amt=0.1, seed=4)


def nikuman(K):
    o = lathe("Bun", [(0, 0.012), (0.2, 0.012), (0.23, 0.06), (0.21, 0.13), (0.15, 0.2), (0.07, 0.24), (0.02, 0.255), (0, 0.255)],
              K["steamed"], seg=48, flute=(16, 0.035))
    # the pleats twist up into the knot at the top
    for v in o.data.vertices:
        x, y, z = v.co
        a = (z / 0.255) ** 2 * 0.9
        v.co.x, v.co.y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    lathe("Twist", [(0.0, 0.235), (0.05, 0.235), (0.035, 0.27), (0.012, 0.29), (0.0, 0.292)], K["steamed"], seg=24, flute=(12, 0.3))
    box("Paper", (0.36, 0.36, 0.006), (0, 0, 0.003), K["paper"], bevel=0.0)


TAIYAKI = [(-0.3, 0.0), (-0.24, 0.08), (-0.12, 0.135), (0.04, 0.13), (0.16, 0.07), (0.25, 0.14), (0.31, 0.13), (0.28, 0.0),
           (0.31, -0.13), (0.25, -0.14), (0.16, -0.07), (0.04, -0.13), (-0.12, -0.135), (-0.24, -0.08)]


def chaikin(poly, it=3):
    """Round a closed outline (corner cutting), so its edge is smooth instead of faceted."""
    for _ in range(it):
        out = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        poly = out
    return poly


def taiyaki(K):
    """A fish-shaped cake from the iron mould: puffed, its fins and gills raised, scales stamped in rows, an eye, and the crisp
    'skirt' of batter that squeezed out round the edge, following the fish's own outline."""
    fish = chaikin(TAIYAKI, 2)
    o = B43.pprism("Fish", "CP_Swatch_kraft", [(x, z + 0.15) for x, z in fish], 0.1, Matrix.Identity(4), K["taiyaki"], "CP_kraft")
    recolour(o, K["taiyaki"])
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.035; b.segments = 4
    o.matrix_world = T(0, 0, 0.05) @ RX(90 * DEG) @ T(0, 0, -0.15)
    # the skirt: the outline pushed out a little all round (a touch more at the belly and tail), thin, with a ragged lip
    cx = sum(x for x, z in fish) / len(fish)
    skirt = [(cx + (x - cx) * 1.06 + (0.012 if x > cx else -0.012), z * 1.12) for x, z in fish]
    o = B43.pprism("Skirt", "CP_Swatch_kraft", [(x, z + 0.15) for x, z in skirt], 0.01, Matrix.Identity(4), K["crust"], "CP_kraft")
    recolour(o, K["crust"])
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.004; b.segments = 2
    o.matrix_world = T(0, 0, 0.05) @ RX(90 * DEG) @ T(0, 0, -0.15)
    sphere("Eye", 0.018, (-0.21, -0.035, 0.1), K["choc"], seg=12, rings=6, scale=(1, 1, 0.45))
    hoop("Gill", (-0.13, 0.0, 0.098), 0.07, "Z", K["crust"], thick=0.006)
    for row in range(3):
        for col in range(4):
            sphere(f"Scale{row}{col}", 0.022, (-0.04 + col * 0.055 + row * 0.02, -0.05 + row * 0.05, 0.096), K["taiyaki"], seg=10, rings=5,
                   scale=(1, 1, 0.25))
    for k in range(5):
        box(f"Fin{k}", (0.06, 0.006, 0.006), (0.04 + k * 0.03, 0.095, 0.097), K["crust"], bevel=0.002, rot=(0, 0, 40 * DEG))


def cream_puff(K):
    o = sphere("Shell", 0.18, (0, 0, 0.13), K["puff"], seg=28, rings=14, scale=(1, 1, 0.72))
    organic(o, 0.02, 0.06)
    lathe("Cream", [(0, 0.12), (0.2, 0.12), (0.2, 0.15), (0, 0.15)], K["cream"], seg=36, flute=(12, 0.12))
    sphere("Cap", 0.15, (0.02, 0, 0.2), K["puff"], seg=24, rings=10, scale=(1, 1, 0.45))
    organic(P.PARTS[-1], 0.012, 0.05)


# ------------------------------------------------------------------ items: hot food

def bento(K):
    """A two-tier lacquer bento: crimson base, black lid with a gilt rim line, the printed band, chopsticks in a paper sleeve
    tucked under it."""
    W, D = 0.9, 0.6
    box("Base", (W, D, 0.18), (0, 0, 0.09), K["lacquer_red"], bevel=0.03, segments=3)
    box("Lid", (W + 0.03, D + 0.03, 0.11), (0, 0, 0.18 + 0.055), K["lacquer"], bevel=0.035, segments=3)
    box("LidLine", (W + 0.034, D + 0.034, 0.012), (0, 0, 0.2), K["gilt"], bevel=0.004)
    pbox("Band", 0.16, D + 0.05, 0.125, K, {"+z": "Bento_Band", "-y": "Swatch_ink", "+y": "Swatch_ink"}, "ink", z0=0.17, k=2.6)
    chopsticks("Chop", 0, 0.0, 0.29, K)
    pbox("Sleeve", 0.42, 0.06, 0.012, K, {"+z": "Swatch_crimson"}, "crimson", z0=0.29)


def meat_loaf(K):
    pbox("Box", 0.62, 0.42, 0.24, K, {"+z": "MeatLoaf_Stamp", "-y": "Swatch_kraft"}, "kraft")
    box("FlapLine", (0.6, 0.004, 0.004), (0, -0.21, 0.236), K["kraft"], bevel=0.0)
    for x in (-0.15, 0.15):
        tube(f"String{x}", [(x, -0.214, 0.004), (x, -0.214, 0.244), (x, 0.214, 0.244), (x, 0.214, 0.004)], 0.006, K["string"], poly=True)
    tube("StringX", [(-0.314, 0, 0.004), (-0.314, 0, 0.244), (0.314, 0, 0.244), (0.314, 0, 0.004)], 0.006, K["string"], poly=True)
    tube("Bow1", [(0.0, 0.0, 0.25), (0.06, -0.04, 0.27), (0.09, 0.0, 0.25), (0.0, 0.0, 0.25)], 0.007, K["string"])
    tube("Bow2", [(0.0, 0.0, 0.25), (-0.06, 0.04, 0.27), (-0.09, 0.0, 0.25), (0.0, 0.0, 0.25)], 0.007, K["string"])
    flatcard("Ticket", "Lunch_Ticket", 0.16, 0.09, 0.18, 0.1, 0.24, K, yaw=0.3)


def takoyaki_boat(K):
    pbox("Boat", 0.62, 0.34, 0.08, K, {"-y": "Boat_Print", "+y": "Boat_Print"}, "kraft", taper=1.12)
    rnd = random.Random(11)
    for i in range(6):
        x = -0.19 + (i % 3) * 0.19
        y = -0.075 + (i // 3) * 0.15
        o = sphere(f"Ball{i}", 0.085, (x, y, 0.13), K["tako"], seg=12, rings=8, scale=(1, 1, 0.9))
        organic(o, 0.008, 0.04)
        sphere(f"Sauce{i}", 0.074, (x, y, 0.172), K["sauce"], seg=16, rings=6, scale=(1, 1, 0.38))
        for j in range(5):
            a = rnd.uniform(0, 2 * PI)
            o = box(f"Flake{i}{j}", (0.035, 0.022, 0.0025), (x + math.cos(a) * 0.03, y + math.sin(a) * 0.03, 0.205), K["bonito"], bevel=0.0,
                    rot=(rnd.uniform(-0.6, 0.6), rnd.uniform(-0.4, 0.4), rnd.uniform(0, PI)))
        for j in range(5):
            box(f"Ao{i}{j}", (0.008, 0.008, 0.003), (x + rnd.uniform(-0.05, 0.05), y + rnd.uniform(-0.05, 0.05), 0.2), K["aonori"],
                bevel=0.0)
    tube("Mayo", [(-0.27 + k * 0.0675, (-1) ** k * 0.085, 0.2 + 0.005 * (k % 2)) for k in range(9)], 0.007, K["mayo"], res=4)
    stick("Pick", (0.19, 0.075, 0.2), (0.26, 0.2, 0.34), 0.006, K)
    stick("Pick2", (-0.19, -0.07, 0.2), (-0.3, -0.15, 0.32), 0.006, K)


def cup_ramen(K):
    """A foam-paper cup of instant noodles: rolled lip, the printed wrap, the printed lid sealed on with its pull tab."""
    lathe("Cup", [(0, 0), (0.165, 0), (0.17, 0.012), (0.22, 0.42), (0.21, 0.42), (0.16, 0.025), (0, 0.025)], K["paper"], seg=48)
    rolled_rim("Lip", 0.222, 0.424, K["paper"], thick=0.01)
    band("Wrap", "Ramen_Wrap", 0.172, 0.222, 0.02, 0.41, K, n=48, rows=3)
    sealed_lid("Lid", "Ramen_Lid", 0.228, 0.432, K)


def roast_sweet_potato(K):
    pbox("Bag", 0.36, 0.2, 0.42, K, {"-y": "Imo_Bag", "+y": "Imo_Bag"}, "kraft")
    box("Fold", (0.37, 0.21, 0.03), (0, 0, 0.43), K["kraft"], bevel=0.008)
    o = lathe("Potato", [(0, -0.22), (0.05, -0.2), (0.085, -0.12), (0.098, 0.0), (0.088, 0.1), (0.07, 0.17), (0.04, 0.2), (0.0, 0.21)],
              K["skin"], seg=24, jitter=(0.05, 4))
    organic(o, 0.006, 0.05)
    o.matrix_world = T(0.02, 0.0, 0.5) @ RY(14 * DEG)
    # the broken end: golden flesh, a wisp of a char line
    lathe("Flesh", [(0, 0.0), (0.075, 0.0), (0.06, 0.012), (0, 0.016)], K["imo"], seg=20, jitter=(0.08, 2))
    P.PARTS[-1].matrix_world = T(0.02, 0, 0.5) @ RY(14 * DEG) @ T(0, 0, 0.16)


def yakitori(K):
    for s_, (y, a) in enumerate(((-0.06, 4), (0.07, -6))):
        st = _mark()
        stick(f"Skewer{s_}", (-0.38, 0, 0), (0.3, 0, 0), 0.008, K)
        for i in range(4):
            x = -0.18 + i * 0.12
            o = lumpy(f"Meat{s_}{i}", 0.052, (x, 0, 0), K["chicken"], scale=(0.9, 1.1, 0.9), amt=0.14, seed=s_ * 10 + i, seg=10, rings=7)
            organic(o, 0.006, 0.03)
            for c in range(2):
                box(f"Char{s_}{i}{c}", (0.006, 0.09, 0.004), (x - 0.015 + c * 0.03, 0, 0.05), K["char"], bevel=0.0)
            if i < 3:
                cyl(f"Negi{s_}{i}", 0.032, 0.05, (x + 0.06, 0, 0), K["negi"], rot=(0, PI / 2, 0), verts=16, bevel=0.006)
        _xform(st, T(0, y, 0.058) @ RZ(a * DEG))


def pumpkin_soup(K):
    paper_cup(K, h=0.38, r0=0.17, r1=0.21)
    lathe("Lid", [(0, 0.385), (0.228, 0.385), (0.232, 0.41), (0.205, 0.42), (0.2, 0.435), (0.08, 0.448), (0, 0.448)], K["plastic_cream"],
          seg=48)
    pdisc("LidPrint", "Soup_Lid", 0.075, 0.449, K, n=32)
    lathe("Spout", [(0, 0.43), (0.03, 0.43), (0.032, 0.455), (0, 0.455)], K["plastic_cream"], seg=16, scale=(1.6, 1))
    P.PARTS[-1].matrix_world = T(0, -0.15, 0)
    box("Sip", (0.04, 0.012, 0.004), (0, -0.15, 0.456), K["plastic_black"], bevel=0.0)


# ------------------------------------------------------------------ items: drinks

def can(K, key, h=0.62, r=0.17):
    """A drinks can: domed base on a stacking foot, the printed body, a stepped neck, the double-seam rim, the recessed lid with
    its scored mouth, and a pull tab (finger loop, tongue, rivet)."""
    lathe("Can", [(0, 0.03), (0.08, 0.02), (r * 0.72, 0.0), (r * 0.82, 0.0), (r * 0.96, 0.025), (r, 0.05), (r, h - 0.09),
                  (r * 0.97, h - 0.065), (r * 0.9, h - 0.035), (r * 0.86, h - 0.016), (r * 0.86, h - 0.006), (r * 0.8, h - 0.006),
                  (r * 0.79, h - 0.026), (0, h - 0.026)], K["alu"], seg=48)
    band("Wrap", key, r + 0.0015, r + 0.0015, 0.05, h - 0.09, K, n=48, rows=2)
    rolled_rim("Seam", r * 0.84, h - 0.006, K["alu"], thick=0.008)
    mouth = (0, -r * 0.42, h - 0.025)
    hoop("Score", mouth, r * 0.26, "Z", K["alu_dark"], thick=0.002)
    hoop("Loop", (0, r * 0.28, h - 0.022), 0.032, "Z", K["alu"], thick=0.006)
    box("Tongue", (0.05, r * 0.6, 0.004), (0, -r * 0.05, h - 0.022), K["alu"], bevel=0.002)
    cyl("Rivet", 0.012, 0.008, (0, -0.01, h - 0.022), K["alu"], verts=12, bevel=0.002)


def prof_r(prof, z):
    """A lathe profile's radius at height z (linear between its points)."""
    for (ra, za), (rb, zb) in zip(prof, prof[1:]):
        if za <= z <= zb and zb > za:
            return ra + (rb - ra) * (z - za) / (zb - za)
    return prof[-1][0] if z > prof[-1][1] else prof[0][0]


def glass_bottle(K, liquid, key, cap, prof, label_z, neck_key=None):
    """A glass bottle (a see-through `_Glass` piece) with its drink inside, a printed label, a neck label and a crimped crown cap."""
    as_glass()
    outer = [(0, 0)] + prof
    inner = [(max(0.0, r - 0.012), z) for r, z in reversed(prof)]
    lathe("Bottle", outer + inner[:-1] + [(0, 0.014)], K["glass_clear"], seg=40)
    as_main()
    fill = [(max(0.0, r - 0.016), z) for r, z in prof if z < prof[-1][1] * 0.82]
    lathe("Drink", [(0, 0.016)] + fill + [(0, fill[-1][1])], K[liquid], seg=32)
    top = prof[-1]
    lathe("Cap", [(0, top[1] - 0.012), (top[0] + 0.008, top[1] - 0.012), (top[0] + 0.012, top[1] + 0.022), (top[0] - 0.004, top[1] + 0.03),
                  (0, top[1] + 0.03)], K[cap], seg=42, flute=(21, 0.09))
    r_lab = max(prof_r(prof, label_z[0] + (label_z[1] - label_z[0]) * k / 10) for k in range(11)) + 0.003
    band("Label", key, r_lab, r_lab, label_z[0], label_z[1], K, n=40, rows=2)
    if neck_key:
        rn = max(prof_r(prof, top[1] - 0.16 + 0.006 * k) for k in range(11)) + 0.003
        band("NeckLabel", neck_key, rn, rn, top[1] - 0.16, top[1] - 0.1, K, n=24)


def ramune(K):
    """A codd-neck marble soda: the bottle pinched to hold its glass marble, the drink inside, the blue cap with the opener
    sticker on top and a ring under it, the printed shrink-wrap round the body."""
    prof = [(0.15, 0), (0.16, 0.03), (0.16, 0.42), (0.13, 0.49), (0.095, 0.53), (0.058, 0.555), (0.088, 0.6), (0.09, 0.64),
            (0.066, 0.68), (0.062, 0.74)]
    as_glass()
    inner = [(max(0.0, r - 0.011), z) for r, z in reversed(prof)]
    lathe("Bottle", [(0, 0)] + prof + inner[:-1] + [(0, 0.012)], K["glass_teal"], seg=40)
    as_main()
    sphere("Marble", 0.047, (0, 0, 0.6), K["marble"], seg=20, rings=12)
    lathe("Drink", [(0, 0.03), (0.14, 0.03), (0.142, 0.42), (0.112, 0.48), (0.0, 0.48)], K["ramune"], seg=32)
    lathe("Cap", [(0, 0.73), (0.072, 0.73), (0.076, 0.8), (0.07, 0.815), (0, 0.815)], K["plastic_blue"], seg=32, flute=(24, 0.03))
    hoop("CapRing", (0, 0, 0.735), 0.075, "Z", K["plastic_blue"], thick=0.008)
    pdisc("Sticker", "Ramune_Cap", 0.064, 0.816, K, n=32)
    band("Wrap", "Can_Ramune", 0.163, 0.163, 0.06, 0.4, K, n=40, rows=2)


def green_tea(K):
    """A PET bottle: petal-footed base, ribbed grip bands above and below the wrap label, the tea inside, a ribbed screw cap with
    its tamper ring."""
    prof = [(0.12, 0), (0.15, 0.02), (0.162, 0.06), (0.162, 0.13), (0.152, 0.15), (0.162, 0.17), (0.162, 0.56), (0.152, 0.58),
            (0.162, 0.6), (0.15, 0.66), (0.11, 0.73), (0.064, 0.79), (0.062, 0.84)]
    as_glass()
    inner = [(max(0.0, r - 0.008), z) for r, z in reversed(prof)]
    o = lathe("Bottle", [(0, 0.012)] + prof + inner[:-1] + [(0, 0.02)], K["glass_clear"], seg=40, flute=(5, 0.0))
    for v in o.data.vertices:          # the petaloid foot
        if v.co.z < 0.05:
            a = math.atan2(v.co.y, v.co.x)
            k = 1 - 0.12 * (0.5 + 0.5 * math.cos(5 * a)) * (1 - v.co.z / 0.05)
            v.co.x *= k
            v.co.y *= k
    as_main()
    lathe("Drink", [(0, 0.06), (0.14, 0.06), (0.14, 0.6), (0.128, 0.64), (0, 0.64)], K["greentea"], seg=32)
    band("Label", "Label_GreenTea", 0.165, 0.165, 0.18, 0.55, K, n=40, rows=2)
    lathe("Neck", [(0.062, 0.8), (0.08, 0.8), (0.08, 0.81), (0.062, 0.81)], K["plastic_green"], seg=24)
    lathe("Cap", [(0, 0.82), (0.07, 0.82), (0.07, 0.9), (0.064, 0.906), (0, 0.906)], K["plastic_green"], seg=40, flute=(30, 0.04))


def carton(K, front, back, top, edge, H=0.5, W=0.32, D=0.32):
    """A gable-top school milk carton: the printed sides, the side seam flap, the two roof panels to a crimped fin, and a bendy
    straw in its film sleeve glued to the back."""
    pbox("Body", W, D, H, K, {"-y": front, "+y": back}, edge)
    pbox("Seam", 0.006, 0.05, H - 0.02, K, {}, edge, z0=0.01, mtx=T(W / 2 + 0.003, D / 2 - 0.04, 0))
    L = math.hypot(D / 2, 0.16)
    pplate("RoofF", top, B43.rect(W, L, 0), 0.008, K, edge, T(0, -D / 4, H + 0.08) @ RX(-45 * DEG))
    pplate("RoofB", top, B43.rect(W, L, 0), 0.008, K, edge, T(0, D / 4, H + 0.08) @ RZ(PI) @ RX(-45 * DEG))
    for sx in (-1, 1):
        B43.pprism(f"Gable{sx}", "CP_Swatch_" + ce(edge), [(-D / 2, H), (D / 2, H), (0, H + 0.16)], 0.008, T(sx * (W / 2 - 0.004), 0, 0)
                   @ RZ(PI / 2), K["cp"], "CP_" + ce(edge))
        # the tucked-in fold of each gable end
        B43.pprism(f"Tuck{sx}", "CP_Swatch_" + ce(edge), [(-0.06, H + 0.1), (0.06, H + 0.1), (0, H + 0.158)], 0.006,
                   T(sx * (W / 2 - 0.012), 0, 0) @ RZ(PI / 2), K["cp"], "CP_" + ce(edge))
    pbox("Fin", W, 0.026, 0.07, K, {"-y": "Swatch_" + edge, "+y": "Swatch_" + edge}, edge, z0=H + 0.155)
    for i in range(10):
        pbox(f"FinRib{i}", 0.006, 0.03, 0.05, K, {}, edge, z0=H + 0.165, mtx=T(-W / 2 + 0.03 + i * (W - 0.06) / 9, 0, 0))
    box("StrawFilm", (0.05, 0.012, 0.36), (0.08, D / 2 + 0.006, H * 0.5), K["film"], bevel=0.004, rot=(0, 8 * DEG, 0))
    stick("Straw", (0.06, D / 2 + 0.006, H * 0.5 - 0.15), (0.1, D / 2 + 0.006, H * 0.5 + 0.15), 0.011, K, mat=K["paper"])


# ------------------------------------------------------------------ items: sweets and cups

def paper_cup(K, h=0.5, r0=0.15, r1=0.21, key="Cup_Wrap"):
    lathe("Cup", [(0, 0.012), (r0 - 0.006, 0.012), (r0 - 0.004, 0.0), (r0, 0.0), (r1, h), (r1 - 0.01, h), (r0 - 0.01, 0.03),
                  (0, 0.03)], K["paper"], seg=48)
    rolled_rim("Lip", r1 + 0.002, h + 0.003, K["paper"], thick=0.009)
    band("Wrap", key, r0 + 0.002, r1 + 0.002, 0.012, h - 0.012, K, n=48, rows=3)


def dome_lid(K, r, z, mat, spout=True):
    """A press-on coffee lid: the snap rim, a recessed deck, a raised sip spout with its slot and a little vent hole."""
    lathe("Lid", [(0, z), (r + 0.012, z), (r + 0.016, z + 0.025), (r - 0.01, z + 0.032), (r - 0.02, z + 0.022), (r - 0.04, z + 0.04),
                  (r * 0.55, z + 0.058), (0, z + 0.06)], mat, seg=48)
    if spout:
        o = lathe("Spout", [(0, z + 0.04), (0.04, z + 0.04), (0.04, z + 0.07), (0.03, z + 0.078), (0, z + 0.078)], mat, seg=24,
                  scale=(1.7, 1))
        o.matrix_world = T(0, -(r - 0.07), 0)
        box("Slot", (0.06, 0.012, 0.004), (0, -(r - 0.07), z + 0.079), K["plastic_black"], bevel=0.0)
    cyl("Vent", 0.008, 0.004, (0.06, r * 0.4, z + 0.06), K["plastic_black"], verts=10, bevel=0.0)


def hot_cocoa(K):
    paper_cup(K)
    band("Sleeve", "Cocoa_Sleeve", 0.172, 0.2, 0.14, 0.34, K, n=48, rows=2)
    P.PARTS[-1].modifiers.new("S", "SOLIDIFY").thickness = 0.008
    dome_lid(K, 0.212, 0.5, K["plastic_red"])


def melon_soda(K):
    paper_cup(K, h=0.58, r0=0.14, r1=0.2)
    lathe("Lid", [(0, 0.585), (0.215, 0.585), (0.218, 0.6), (0.19, 0.615), (0.0, 0.615)], K["film"], seg=48)
    cyl("Cross", 0.025, 0.004, (0.04, 0.0, 0.615), K["plastic_black"], verts=12, bevel=0.0)
    st = _mark()
    stick("Straw", (0.0, 0.0, 0.3), (0.0, 0.0, 0.82), 0.02, K, mat=K["straw_red"])
    stick("StrawBend", (0.0, 0.0, 0.82), (0.09, 0.0, 0.9), 0.02, K, mat=K["straw_red"])
    for i in range(6):
        hoop(f"Stripe{i}", (0, 0, 0.62 + i * 0.03), 0.0205, "Z", K["paper"], thick=0.004)
    _xform(st, T(0.04, 0, 0) @ RY(-4 * DEG))


def pudding_cup(K):
    """A custard pudding in its clear cup: the caramel top showing through, the printed lid sealed on, a little plastic spoon."""
    as_glass()
    lathe("Cup", [(0, 0), (0.15, 0), (0.18, 0.24), (0.195, 0.24), (0.195, 0.25), (0.17, 0.25), (0.14, 0.02), (0, 0.02)],
          K["glass_clear"], seg=48)
    as_main()
    lathe("Custard", [(0, 0.022), (0.136, 0.022), (0.164, 0.21), (0, 0.21)], K["pudding"], seg=40)
    lathe("Caramel", [(0, 0.21), (0.164, 0.21), (0.166, 0.226), (0.12, 0.232), (0, 0.233)], K["caramel"], seg=40)
    sealed_lid("Lid", "Pudding_Lid", 0.198, 0.25, K)
    spoon("Spoon", -0.05, -0.12, 0.0, K, yaw=-25 * DEG, mat=K["plastic_cream"], s=0.9)


def ecto_jelly(K):
    """Ectoplasm jelly: a wobbly ghost-shaped mould on a glass dish, two dark eyes and a little 'o' of a mouth set into it."""
    lathe("Dish", [(0, 0), (0.18, 0), (0.24, 0.07), (0.255, 0.08), (0.24, 0.085), (0.17, 0.025), (0, 0.025)], K["glass_clear"], seg=48)
    o = lathe("Jelly", [(0, 0.025), (0.19, 0.025), (0.2, 0.08), (0.18, 0.18), (0.14, 0.26), (0.08, 0.31), (0, 0.325)], K["jelly"], seg=48,
              flute=(7, 0.05))
    for v in o.data.vertices:
        v.co.x += 0.012 * math.sin(v.co.z * 30)
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.026, (sx * 0.055, -0.15, 0.22), K["jelly_eye"], seg=12, rings=8, scale=(0.8, 0.5, 1.2))
    hoop("Mouth", (0, -0.16, 0.15), 0.022, "Y", K["jelly_eye"], thick=0.007)
    spoon("Spoon", 0.18, -0.2, 0.0, K, yaw=-60 * DEG)


def moon_cake(K):
    lathe("Cake", [(0, 0), (0.22, 0), (0.24, 0.03), (0.24, 0.12), (0.22, 0.14), (0, 0.14)], K["mooncake"], seg=64, flute=(12, 0.035))
    pdisc("Top", "MoonCake_Top", 0.2, 0.141, K, n=48)
    box("Card", (0.52, 0.52, 0.008), (0, 0, -0.004), K["paper"], bevel=0.0)


def dango(K):
    """Hanami dango: pink, white and green rice dumplings on a skewer, a glossy glaze, resting on a folded paper."""
    stick("Skewer", (-0.36, 0, 0.075), (0.3, 0, 0.075), 0.008, K)
    for i, m in enumerate(("dango_pink", "dango_white", "dango_green")):
        sphere(f"Ball{i}", 0.072, (-0.15 + i * 0.148, 0, 0.075), K[m], seg=20, rings=12)
    flatcard("Paper", "Lunch_Ticket", 0.3, 0.16, -0.05, 0.0, 0.0, K)


def tombstone_cookie(K):
    """A shortbread tombstone iced grey with R.I.P. HOMEWORK piped on, a crack line and a sugar-moss tuft at its foot."""
    poly = [(-0.17, 0.0), (0.17, 0.0), (0.17, 0.3)]
    for i in range(1, 16):
        a = i / 16 * PI
        poly.append((math.cos(a) * 0.17, 0.3 + math.sin(a) * 0.17))
    poly.append((-0.17, 0.3))
    o = B43.pprism("Base", "CP_Swatch_kraft", [(x * 1.06, z * 1.04 - 0.01) for x, z in poly], 0.04, T(0, -0.15, 0.02) @ RX(-90 * DEG),
                   K["shortbread"], "CP_kraft")
    recolour(o, K["shortbread"])
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.012; b.segments = 3
    pplate("Icing", "Cookie_Icing", poly, 0.012, K, "kraft", T(0, -0.15, 0.046) @ RX(-90 * DEG))
    for i in range(6):
        sphere(f"Moss{i}", 0.018, (-0.1 + i * 0.04, -0.15 - 0.02 * (i % 2), 0.055), K["dango_green"], seg=8, rings=5, scale=(1, 1, 0.6))


# ------------------------------------------------------------------ items: candy and snacks

def bat_gummies(K):
    pillow("Bag", 0.42, 0.58, 0.14, K, "Gummies_Front", "Gummies_Back", "gummies")


def candy_apple(K):
    o = lathe("Apple", [(0, 0.02), (0.08, 0.0), (0.16, 0.04), (0.19, 0.13), (0.17, 0.24), (0.1, 0.29), (0.04, 0.27), (0, 0.255)],
              K["candy_red"], seg=48, flute=(5, 0.025))
    lathe("Pool", [(0, 0), (0.17, 0), (0.175, 0.008), (0.12, 0.016), (0, 0.016)], K["candy_red"], seg=40, jitter=(0.1, 2))
    for i, a in enumerate((20, 140, 250)):
        sphere(f"Drip{i}", 0.018, (math.cos(a * DEG) * 0.18, math.sin(a * DEG) * 0.18, 0.07), K["candy_red"], seg=10, rings=8,
               scale=(1, 1, 2.2))
    stick("Stick", (0, 0, 0.24), (0.02, 0.0, 0.62), 0.016, K)
    for sx in (-1, 1):
        tube(f"Bow{sx}", [(0.01, 0, 0.32), (0.01 + sx * 0.06, -0.02, 0.35), (0.01 + sx * 0.07, 0.0, 0.31), (0.01, 0, 0.32)], 0.008,
             K["string"])
    tube("Tail", [(0.01, 0, 0.32), (0.04, -0.03, 0.28), (0.03, -0.04, 0.24)], 0.007, K["string"])


def ghost_mints(K):
    lathe("Tin", [(0, 0), (0.2, 0), (0.205, 0.006), (0.205, 0.08), (0, 0.08)], K["alu"], seg=64)
    lathe("LidRim", [(0.208, 0.07), (0.214, 0.072), (0.214, 0.124), (0.205, 0.128), (0.0, 0.128)], K["alu"], seg=64)
    rolled_rim("Roll", 0.212, 0.126, K["alu"], thick=0.005)
    band("Side", "Mints_Side", 0.2155, 0.2155, 0.078, 0.12, K, n=64)
    pdisc("Lid", "Mints_Lid", 0.2, 0.1285, K, n=64)


def konpeito(K):
    """A paper sweet bag, its top folded over twice and sealed with a round sticker; a few sugar stars spilled in front."""
    pbox("Bag", 0.3, 0.16, 0.36, K, {"-y": "Konpeito_Front", "+y": "Konpeito_Back"}, "cream")
    pbox("Fold", 0.31, 0.03, 0.08, K, {"-y": "Swatch_crimson", "+y": "Swatch_crimson"}, "crimson", z0=0.0,
         mtx=T(0, 0, 0.35) @ RX(12 * DEG))
    pdisc("Sticker", "Soup_Lid", 0.035, 0.0, K, n=24, mtx=T(0, -0.0255, 0.386) @ RX(102 * DEG))
    rnd = random.Random(5)
    for i, m in enumerate(("k_pink", "k_yellow", "k_blue", "k_white", "k_pink", "k_blue")):
        spiky(f"Star{i}", 0.022, (i * 0.04 - 0.1, -0.16 - rnd.uniform(0, 0.05), 0.03), K[m], seed=i)


def licorice(K):
    """A bundle of twisted black licorice whips (each a three-strand twist) tied with a printed paper band, lying down."""
    st = _mark()
    for i in range(6):
        a = i / 6 * 2 * PI
        cx, cy = math.cos(a) * 0.042, math.sin(a) * 0.042
        for sdx in range(3):
            ph = sdx * 2 * PI / 3
            pts = [(cx + 0.009 * math.cos(k * 1.3 + ph), cy + 0.009 * math.sin(k * 1.3 + ph), 0.02 + k * 0.036) for k in range(16)]
            tube(f"Whip{i}{sdx}", pts, 0.011, K["licorice"], res=1)
    band("Band", "Licorice_Band", 0.068, 0.068, 0.22, 0.32, K, n=32)
    _xform(st, RY(90 * DEG))


def chocolate_bar(K):
    """A bar in its printed paper sleeve, one end torn open: the gold foil crumpled back and four squares of chocolate showing,
    each stamped with a crescent moon."""
    box("Foil", (0.56, 0.24, 0.05), (0.02, 0, 0.026), K["foil_gold"], bevel=0.006)
    organic(P.PARTS[-1], 0.003, 0.02)
    pbox("Wrapper", 0.42, 0.26, 0.064, K, {"+z": "Choc_Wrapper", "-y": "Swatch_choc", "+y": "Swatch_choc", "-z": "Swatch_choc"}, "choc",
         z0=-0.002, mtx=T(0.08, 0, 0))
    for i in range(2):
        for j in range(2):
            x, y = -0.16 - i * 0.07, -0.055 + j * 0.11
            box(f"Square{i}{j}", (0.064, 0.104, 0.024), (x, y, 0.062), K["choc"], bevel=0.008, segments=3)
            o = sphere(f"Moon{i}{j}", 0.018, (x, y, 0.074), K["choc"], seg=12, rings=6, scale=(1, 1, 0.25))


def senbei(K):
    """A soy-glazed rice cracker, cracked and toasted, a strip of nori round it, half in its clear packet with the printed card."""
    o = cyl("Cracker", 0.2, 0.04, (0, 0, 0.022), K["senbei"], verts=40, bevel=0.014)
    organic(o, 0.004, 0.03)
    box("Nori", (0.06, 0.41, 0.046), (0.0, 0, 0.022), K["nori"], bevel=0.004)
    box("Packet", (0.27, 0.45, 0.07), (0.13, 0, 0.035), K["film"], bevel=0.012)
    pplate("Card", "Senbei_Sleeve", B43.rect(0.4, 0.24, 0), 0.004, K, "paper", T(0.13, 0, 0.073) @ RZ(PI / 2) @ RX(-90 * DEG))


def grave_crisps(K):
    pillow("Bag", 0.5, 0.68, 0.18, K, "Crisps_Front", "Crisps_Back", "crisps")


def popcorn(K):
    pbox("Carton", 0.3, 0.22, 0.44, K, {"-y": "Popcorn_Side", "+y": "Popcorn_Back", "-x": "Swatch_crimson", "+x": "Swatch_crimson"}, "cream",
         taper=1.18)
    rnd = random.Random(9)
    for i in range(46):
        a = rnd.uniform(0, 2 * PI)
        rr = rnd.uniform(0, 1) ** 0.6
        x, y = math.cos(a) * rr * 0.16, math.sin(a) * rr * 0.12
        z = 0.44 + 0.08 * (1 - rr) + rnd.uniform(0, 0.03)
        for k in range(3):        # each kernel a cluster of three puffs
            lumpy(f"Pop{i}{k}", 0.022, (x + rnd.uniform(-0.015, 0.015), y + rnd.uniform(-0.015, 0.015), z + rnd.uniform(-0.01, 0.015)),
                  K["popcorn"], amt=0.35, seed=i * 3 + k, seg=7, rings=4)


def prank_kit(K):
    """A taped cardboard box with the PRANK KIT label on its lid and front; a spray can, a roll of tape and a stink-bomb vial
    stood beside it."""
    pbox("Box", 0.6, 0.4, 0.3, K, {"+z": "Prank_Label", "-y": "Prank_Label"}, "cardboard")
    box("Tape", (0.62, 0.08, 0.004), (0, 0.13, 0.302), K["film"], bevel=0.0)
    box("TapeSide", (0.004, 0.08, 0.12), (0.302, 0.13, 0.24), K["film"], bevel=0.0)
    st = _mark()
    lathe("Spray", [(0, 0), (0.058, 0), (0.06, 0.01), (0.06, 0.25), (0.04, 0.29), (0.022, 0.3), (0, 0.3)], K["alu"], seg=24)
    band("SprayLab", "Swatch_redlantern", 0.0615, 0.0615, 0.04, 0.22, K, n=24, k=0.6)
    lathe("Nozzle", [(0, 0.3), (0.02, 0.3), (0.02, 0.34), (0, 0.34)], K["plastic_green"], seg=12)
    _xform(st, T(0.38, -0.1, 0.0))
    st = _mark()
    hoop("Roll", (0, 0, 0.0), 0.05, "Y", K["plastic_cream"], thick=0.022)
    _xform(st, T(-0.2, -0.27, 0.075))
    st = _mark()
    lathe("Vial", [(0, 0), (0.025, 0), (0.025, 0.12), (0.015, 0.14), (0, 0.14)], K["gum_green"], seg=16)
    lathe("Cork", [(0, 0.135), (0.016, 0.135), (0.018, 0.17), (0, 0.17)], K["wood"], seg=12)
    _xform(st, T(-0.05, -0.28, 0.0))


# ------------------------------------------------------------------ items: lunch trays (sets)

def katsu_curry(K):
    """Katsu curry: an oval plate, a mound of rice, the curry sauce (carrot and potato in it), a pork cutlet in panko sliced in
    six and laid across, red pickles; a spoon, a glass of water and the Monday tent card on the tray."""
    z = tray(K)
    st = _mark()
    fl = plate("Plate", 0.36, K, sy=0.7, rim=K["enamel"])
    rice_mound("Rice", 0.18, -0.12, 0, fl, K, h=0.1, sy=0.9)
    o = surface("Curry", 0.2, fl + 0.03, K["curry"], sy=0.82, wob=0.08, seed=3)
    o.matrix_world = T(0.1, 0, 0)
    rnd = random.Random(4)
    for i in range(6):
        box(f"Carrot{i}", (0.035, 0.035, 0.03), (0.18 + rnd.uniform(-0.06, 0.08), rnd.uniform(-0.13, 0.13), fl + 0.035), K["carrot"],
            bevel=0.006, rot=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)))
        lumpy(f"Pot{i}", 0.026, (0.16 + rnd.uniform(-0.04, 0.1), rnd.uniform(-0.14, 0.14), fl + 0.035), K["potato"], amt=0.2, seed=i)
    for i in range(6):
        o = box(f"Katsu{i}", (0.062, 0.25, 0.055), (-0.13 + i * 0.066, 0.0, fl + 0.1), K["panko"], bevel=0.012, segments=2,
                rot=(0, -10 * DEG, 0))
        organic(o, 0.004, 0.02)
        box(f"KatsuIn{i}", (0.064, 0.23, 0.036), (-0.13 + i * 0.066, 0.0, fl + 0.1), K["mash"], bevel=0.004, rot=(0, -10 * DEG, 0))
    for i in range(5):
        box(f"Fuku{i}", (0.02, 0.014, 0.01), (-0.26 + rnd.uniform(-0.02, 0.02), 0.12 + rnd.uniform(-0.03, 0.03), fl + 0.005), K["fukujin"],
            bevel=0.003)
    _xform(st, T(-0.12, 0.05, z))
    spoon("Spoon", 0.38, -0.25, z, K, yaw=90 * DEG)
    st = _mark()
    as_glass()
    lathe("Glass", [(0, 0), (0.07, 0), (0.08, 0.2), (0.072, 0.2), (0.064, 0.012), (0, 0.012)], K["glass_clear"], seg=32)
    as_main()
    lathe("Water", [(0, 0.012), (0.064, 0.012), (0.074, 0.16), (0, 0.16)], K["water"], seg=32)
    _xform(st, T(0.45, 0.25, z))
    pplate("Tent", "Curry_Card", B43.rect(0.2, 0.13, 0.065), 0.004, K, "paper", T(0.42, -0.02, z) @ RX(-12 * DEG))


def shoyu_ramen(K):
    """A big lacquer bowl of shoyu ramen: noodles swirling in the broth, two slices of chashu, a soft egg halved (jammy yolk), a
    sheet of nori stood at the back, a naruto slice, menma and spring onion; chopsticks on a rest and a ceramic spoon."""
    z = tray(K)
    st = _mark()
    fl = bowl("Bowl", 0.36, 0.24, K)
    surface("Broth", 0.32, 0.2, K["broth"])
    rnd = random.Random(7)
    for i in range(18):
        a0 = rnd.uniform(0, 2 * PI)
        r0 = rnd.uniform(0.05, 0.22)
        pts = [(math.cos(a0 + k * 0.35) * (r0 + k * 0.012), math.sin(a0 + k * 0.35) * (r0 + k * 0.012), 0.205 + 0.006 * math.sin(k + i))
               for k in range(7)]
        tube(f"Noodle{i}", pts, 0.009, K["noodle_pale"], res=3)
    for i, (x, y, a) in enumerate(((-0.09, -0.1, 20), (0.02, -0.14, -10))):
        o = cyl(f"Chashu{i}", 0.085, 0.018, (x, y, 0.206), K["pork"], verts=28, bevel=0.006, rot=(8 * DEG, 0, a * DEG))
        organic(o, 0.003, 0.03)
    for i, x in enumerate((0.1, 0.18)):
        st2 = _mark()
        lathe(f"Egg{i}", [(0, 0), (0.05, 0), (0.048, 0.02), (0.035, 0.04), (0, 0.048)], K["egg_white"], seg=24, scale=(1.3, 1))
        _xform(st2, T(x, 0.06 - i * 0.05, 0.245) @ RX(PI))
        lathe(f"Yolk{i}", [(0, 0.0), (0.032, 0.0), (0.028, 0.004), (0, 0.006)], K["yolk"], seg=20, scale=(1.3, 1),
              loc=(x, 0.06 - i * 0.05, 0.245))
    pplate("Nori", "Swatch_paper", B43.rect(0.18, 0.2, 0.0), 0.006, K, "paper", T(0.0, 0.2, 0.3) @ RX(-20 * DEG))
    recolour(P.PARTS[-1], K["nori"])
    cyl("Naruto", 0.045, 0.014, (-0.13, 0.08, 0.205), K["naruto"], verts=24, bevel=0.004, rot=(0, 0, 0))
    tube("NarutoSwirl", [(-0.13 + math.cos(t * 0.6) * 0.004 * t, 0.08 + math.sin(t * 0.6) * 0.004 * t, 0.2135) for t in range(10)],
         0.003, K["dango_pink"], res=2)
    for i in range(5):
        box(f"Menma{i}", (0.07, 0.016, 0.01), (-0.18 + rnd.uniform(-0.02, 0.02), -0.02 + i * 0.022, 0.203), K["menma"], bevel=0.003,
            rot=(0, 0, rnd.uniform(-0.3, 0.3)))
    for i in range(14):
        hoop(f"Negi{i}", (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0.202), 0.009, "Z", K["negi"], thick=0.003)
    _xform(st, T(-0.1, 0.03, z))
    box("Rest", (0.04, 0.06, 0.02), (0.42, 0.1, z + 0.01), K["porcelain"], bevel=0.008)
    chopsticks("Chop", 0.38, 0.1, z + 0.014, K, yaw=90 * DEG, length=0.72)
    st = _mark()
    sphere("RengeBowl", 0.06, (0, 0, 0.02), K["porcelain"], seg=20, rings=8, scale=(1.4, 1.0, 0.4))
    box("RengeHandle", (0.14, 0.03, 0.012), (-0.12, 0, 0.04), K["porcelain"], bevel=0.006, rot=(0, -15 * DEG, 0))
    _xform(st, T(0.4, -0.25, z) @ RZ(-30 * DEG))


def karaage_set(K):
    """Karaage set: fried chicken on a plate with a mound of shredded cabbage, a lemon wedge and mayo; a bowl of rice, miso soup,
    chopsticks."""
    z = tray(K)
    st = _mark()
    fl = plate("Plate", 0.3, K, rim=K["enamel"])
    rnd = random.Random(12)
    o = sphere("Cabbage", 0.13, (0.1, 0.08, fl + 0.02), K["cabbage"], seg=24, rings=12, scale=(1, 1, 0.55))
    organic(o, 0.02, 0.012)
    for i in range(5):
        o = lumpy(f"Karaage{i}", 0.07, (-0.1 + (i % 3) * 0.09 - 0.03, -0.1 + (i // 3) * 0.1, fl + 0.05), K["karaage"], amt=0.2, seed=i,
                  seg=12, rings=8, scale=(1.1, 1, 0.8))
        organic(o, 0.012, 0.025)
    poly = [(math.cos(a / 8 * PI) * 0.07, math.sin(a / 8 * PI) * 0.07) for a in range(9)]
    o = B43.pprism("Lemon", "CP_Swatch_paper", poly, 0.035, T(0.17, -0.12, fl + 0.003) @ RZ(30 * DEG), K["lemon_flesh"], "CP_paper")
    recolour(o, K["lemon_flesh"])
    sphere("Mayo", 0.03, (0.18, 0.0, fl + 0.015), K["mayo"], seg=12, rings=6, scale=(1, 1, 0.5))
    _xform(st, T(-0.2, 0.1, z))
    rice_bowl("Rice", 0.33, 0.2, z, K)
    miso_bowl("Miso", 0.33, -0.22, z, K)
    chopsticks("Chop", -0.1, -0.33, z, K, yaw=0.0, length=0.72)


def mackerel_set(K):
    """Grilled mackerel set: a long dark-glazed plate with a salted mackerel fillet (silver skin, grill bars), a mound of grated
    daikon with soy, a bowl of rice, miso soup, pickles, chopsticks on a rest."""
    z = tray(K)
    st = _mark()
    box("Plate", (0.6, 0.26, 0.03), (0, 0, 0.015), K["glaze_dark"], bevel=0.012, segments=2)
    poly = [(-0.24, 0.0), (-0.2, 0.08), (0.1, 0.1), (0.24, 0.05), (0.26, 0.0), (0.24, -0.05), (0.1, -0.1), (-0.2, -0.08)]
    o = B43.pprism("Fillet", "CP_Swatch_paper", [(x, y + 0.1) for x, y in poly], 0.04, T(-0.04, 0, 0.05) @ RX(90 * DEG) @ T(0, 0, -0.1),
                   K["mackerel"], "CP_paper")
    recolour(o, K["mackerel"])
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.015; b.segments = 3
    organic(o, 0.004, 0.04)
    for i in range(4):
        box(f"Grill{i}", (0.01, 0.17, 0.004), (-0.16 + i * 0.1, 0, 0.072), K["char"], bevel=0.0, rot=(0, 0, 20 * DEG))
    o = sphere("Daikon", 0.05, (0.22, 0.06, 0.04), K["daikon"], seg=16, rings=8, scale=(1, 1, 0.7))
    organic(o, 0.004, 0.02)
    sphere("Soy", 0.012, (0.22, 0.06, 0.074), K["sauce"], seg=8, rings=4, scale=(1, 1, 0.4))
    _xform(st, T(-0.2, 0.18, z))
    rice_bowl("Rice", 0.3, 0.2, z, K)
    miso_bowl("Miso", 0.33, -0.2, z, K)
    st = _mark()
    lathe("PickleDish", [(0, 0), (0.08, 0), (0.09, 0.03), (0.082, 0.03), (0.07, 0.012), (0, 0.012)], K["porcelain"], seg=24)
    for i in range(4):
        box(f"Pickle{i}", (0.04, 0.03, 0.012), (-0.03 + (i % 2) * 0.05, -0.02 + (i // 2) * 0.04, 0.022), K["pickle"], bevel=0.004)
    _xform(st, T(-0.05, -0.15, z))
    box("Rest", (0.04, 0.06, 0.02), (-0.4, -0.25, z + 0.01), K["porcelain"], bevel=0.008)
    chopsticks("Chop", -0.38, -0.25, z + 0.014, K, yaw=90 * DEG, length=0.6)


def omurice(K):
    """Omurice: a smooth, golden omelette folded over fried rice on an oval plate, a ribbon of brown demi-glace down it, parsley;
    a little side salad, a spoon."""
    z = tray(K)
    st = _mark()
    fl = plate("Plate", 0.4, K, sy=0.68, rim=K["gilt"])
    o = sphere("Omelette", 0.17, (0, 0, fl + 0.06), K["omelette"], seg=40, rings=20, scale=(1.6, 0.92, 0.55))
    for v in o.data.vertices:
        v.co.z = max(v.co.z, -0.06)
        v.co.x *= 1 - 0.18 * (v.co.y / 0.16) ** 2
    organic(o, 0.003, 0.08)
    o = sphere("Demi", 0.06, (0, 0, fl + 0.152), K["demi"], seg=24, rings=10, scale=(3.6, 0.9, 0.25))
    organic(o, 0.004, 0.05)
    rnd = random.Random(2)
    for i in range(5):
        sphere(f"Parsley{i}", 0.012, (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.02, 0.02), fl + 0.17), K["herb"], seg=8, rings=5)
    _xform(st, T(-0.12, 0.08, z))
    st = _mark()
    salad_bowl(K)
    _xform(st, T(0.38, 0.18, z))
    spoon("Spoon", 0.32, -0.26, z, K, yaw=80 * DEG)


def salad_bowl(K, r=0.13):
    lathe("SaladBowl", [(0, 0), (r * 0.6, 0), (r, r * 0.6), (r * 0.94, r * 0.6), (r * 0.56, 0.015), (0, 0.015)], K["porcelain"], seg=32)
    rnd = random.Random(15)
    for i in range(7):
        a = i / 7 * 2 * PI
        leaf(f"Lettuce{i}", (math.cos(a) * 0.02, math.sin(a) * 0.02, 0.02), a, 50 * DEG, r * 1.0, 0.05, 0.25, K["lettuce"], n=8, fold=0.5,
             thick=0.006)
    for i in range(3):
        a = i / 3 * 2 * PI + 0.5
        sphere(f"Tomato{i}", 0.026, (math.cos(a) * 0.05, math.sin(a) * 0.05, r * 0.5), K["tomato"], seg=12, rings=8)
    for i in range(3):
        a = i / 3 * 2 * PI + 1.5
        cyl(f"Cucumber{i}", 0.026, 0.008, (math.cos(a) * 0.06, math.sin(a) * 0.06, r * 0.55), K["cucumber"], verts=16, bevel=0.0,
            rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0))


# ------------------------------------------------------------------ items: lunch trays (house meals)

def witching_stew(K):
    """Witching Hour Stew: a round crusty loaf hollowed into a bowl, full of beef stew (beef, carrot, potato), its crust lid set
    against it; on a plate on the tray, with a spoon."""
    z = tray(K, mat="Tray_MatB")
    st = _mark()
    fl = plate("Plate", 0.32, K, rim=K["enamel"])
    o = lathe("Loaf", [(0, 0), (0.18, 0), (0.22, 0.06), (0.23, 0.13), (0.2, 0.21), (0.16, 0.225), (0.14, 0.22), (0.13, 0.08), (0, 0.08)],
              K["crust"], seg=48)
    organic(o, 0.01, 0.05)
    o.matrix_world = T(0, 0, fl)
    lathe("Crumb", [(0.13, 0.08), (0.14, 0.215), (0.16, 0.226), (0.13, 0.226)], K["crumbin"], seg=48, loc=(0, 0, fl))
    surface("Stew", 0.138, fl + 0.19, K["stew"], wob=0.05, seed=4)
    rnd = random.Random(6)
    for i in range(10):
        a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.1)
        m = ("beef", "carrot", "potato")[i % 3]
        o = box(f"Chunk{i}", (0.035, 0.03, 0.028), (math.cos(a) * rr, math.sin(a) * rr, fl + 0.195), K[m], bevel=0.008,
                rot=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 3)))
    for i in range(6):
        sphere(f"Parsley{i}", 0.01, (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), fl + 0.21), K["herb"], seg=6, rings=4)
    o = sphere("Lid", 0.15, (0.33, -0.18, fl + 0.08), K["crust"], seg=28, rings=10, scale=(1, 1, 0.38))
    for v in o.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    organic(o, 0.008, 0.05)
    o.rotation_euler = (0, 50 * DEG, -30 * DEG)
    _xform(st, T(-0.12, 0.05, z))
    spoon("Spoon", 0.38, -0.2, z, K, yaw=70 * DEG)
    flatcard("Ticket", "Lunch_Ticket", 0.18, 0.1, 0.4, 0.25, z, K, yaw=-0.2)


def shepherds_pie(K):
    """Graveyard Shepherd's Pie: a crimson enamel baking dish of mince under piped mash, the peaks browned, three little shortbread
    tombstones stood in it like a churchyard, gravy bubbling at the edge; a spoon."""
    z = tray(K, mat="Tray_MatB")
    st = _mark()
    box("Dish", (0.6, 0.42, 0.14), (0, 0, 0.07), K["enamel"], bevel=0.04, segments=3)
    for sx in (-1, 1):
        box(f"Handle{sx}", (0.06, 0.16, 0.03), (sx * 0.32, 0, 0.11), K["enamel"], bevel=0.012)
    box("Gravy", (0.54, 0.36, 0.02), (0, 0, 0.13), K["gravy"], bevel=0.008)
    for row in range(6):
        y = -0.15 + row * 0.06
        pts = [(-0.24 + k * 0.03, y + 0.008 * math.sin(k * 1.3 + row), 0.15 + 0.012 * math.sin(k * 2.1)) for k in range(17)]
        tube(f"Mash{row}", pts, 0.028, K["mash"], res=3)
    for i, (x, y, a) in enumerate(((-0.14, 0.05, -8), (0.0, -0.04, 4), (0.14, 0.06, 10))):
        poly = [(-0.04, 0.0), (0.04, 0.0), (0.04, 0.06)] + [(math.cos(k / 8 * PI) * 0.04, 0.06 + math.sin(k / 8 * PI) * 0.04) for k in
                                                               range(1, 8)] + [(-0.04, 0.06)]
        o = B43.pprism(f"Stone{i}", "CP_Swatch_kraft", poly, 0.018, T(x, y, 0.16) @ RZ(a * DEG) @ RX(0), K["shortbread"], "CP_kraft")
        recolour(o, K["shortbread"])
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.004; b.segments = 2
    _xform(st, T(-0.1, 0.06, z))
    spoon("Spoon", 0.4, -0.22, z, K, yaw=80 * DEG)


def pumpkin_gratin(K):
    """Pumpkin Gratin: a little ribbed pumpkin, its top cut off and the bowl filled with a bubbling cheese gratin, browned in
    spots; the lid with its curly stem leant against it, on a plate."""
    z = tray(K, mat="Tray_MatB")
    st = _mark()
    fl = plate("Plate", 0.33, K, mat=K["glaze_dark"])
    o = lathe("Pumpkin", [(0, 0.0), (0.12, 0.0), (0.21, 0.05), (0.24, 0.13), (0.22, 0.2), (0.17, 0.23), (0.15, 0.23), (0.16, 0.18),
                          (0.0, 0.18)], K["pumpkin"], seg=60, flute=(10, 0.1), loc=(0, 0, fl))
    o = lathe("Gratin", [(0, fl + 0.18), (0.16, fl + 0.18), (0.155, fl + 0.235), (0.1, fl + 0.25), (0, fl + 0.255)], K["gratin"], seg=48)
    organic(o, 0.008, 0.03)
    st2 = _mark()
    lathe("LidP", [(0, 0.0), (0.16, 0.0), (0.15, 0.04), (0.09, 0.075), (0, 0.085)], K["pumpkin"], seg=48, flute=(10, 0.1))
    tube("Stem", [(0, 0, 0.08), (0.01, 0.0, 0.13), (0.04, 0.01, 0.16), (0.06, 0.03, 0.15)], 0.014, K["stem"], res=4)
    _xform(st2, T(0.26, -0.12, fl + 0.12) @ RY(-70 * DEG))
    _xform(st, T(-0.1, 0.05, z))
    spoon("Spoon", 0.38, -0.24, z, K, yaw=70 * DEG)


def ravens_roast(K):
    """Raven's Roast: a roast chicken leg with crackling skin and a bone end, roast potatoes, glazed carrots, a sprig of rosemary
    and a pool of gravy; knife and fork."""
    z = tray(K, mat="Tray_MatB")
    st = _mark()
    fl = plate("Plate", 0.36, K, rim=K["gilt"])
    o = surface("Gravy", 0.16, fl + 0.008, K["gravy"], wob=0.12, seed=9)
    o.matrix_world = T(-0.05, 0.04, 0)
    st2 = _mark()
    o = lathe("Leg", [(0, -0.02), (0.06, 0.0), (0.09, 0.07), (0.085, 0.15), (0.05, 0.22), (0.028, 0.26), (0.024, 0.3), (0, 0.3)], K["roast"],
              seg=32, scale=(1, 0.85))
    organic(o, 0.01, 0.04)
    lathe("Bone", [(0, 0.29), (0.022, 0.29), (0.022, 0.33), (0.036, 0.35), (0.03, 0.38), (0, 0.385)], K["bone"], seg=20)
    _xform(st2, T(-0.08, 0.04, fl + 0.07) @ RZ(-30 * DEG) @ RY(80 * DEG))
    rnd = random.Random(14)
    for i in range(4):
        o = lumpy(f"Pot{i}", 0.05, (0.15 + (i % 2) * 0.07, -0.12 + (i // 2) * 0.11, fl + 0.04), K["roastpot"], amt=0.25, seed=i, seg=14,
                  rings=8)
        organic(o, 0.008, 0.03)
    for i in range(4):
        o = lathe(f"Carrot{i}", [(0, 0), (0.026, 0.0), (0.02, 0.1), (0, 0.13)], K["carrot"], seg=12)
        o.matrix_world = T(0.02 + i * 0.03, -0.2 + i * 0.01, fl + 0.025) @ RZ(rnd.uniform(-0.3, 0.3)) @ RY(-88 * DEG)
    tube("Rosemary", [(-0.2, 0.15, fl + 0.06), (-0.12, 0.17, fl + 0.06), (-0.04, 0.2, fl + 0.055)], 0.004, K["stem"], res=3)
    for i in range(14):
        box(f"Needle{i}", (0.03, 0.004, 0.003), (-0.19 + i * 0.011, 0.155 + i * 0.003 + (-1) ** i * 0.01, fl + 0.062), K["herb"], bevel=0.0,
            rot=(0, 0, (-1) ** i * 0.8))
    _xform(st, T(-0.1, 0.03, z))
    knife("Knife", 0.42, -0.18, z, K, yaw=90 * DEG)
    fork("Fork", 0.42, 0.12, z, K, yaw=90 * DEG)


# ------------------------------------------------------------------ items: lunch extras

def fruit_cup(K):
    """A clear fruit cup: peach, pineapple, grapes and a cherry in syrup, the printed foil lid sealed on with its tab; a plastic spoon."""
    as_glass()
    lathe("Cup", [(0, 0), (0.15, 0), (0.18, 0.24), (0.2, 0.24), (0.2, 0.25), (0.17, 0.25), (0.14, 0.012), (0, 0.012)], K["glass_clear"],
          seg=48)
    as_main()
    lathe("Syrup", [(0, 0.014), (0.137, 0.014), (0.162, 0.2), (0, 0.2)], K["syrup"], seg=36)
    rnd = random.Random(3)
    for i in range(12):
        m = ("peach", "pineapple", "grape", "peach")[i % 4]
        a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.11)
        if m == "grape":
            sphere(f"F{i}", 0.026, (math.cos(a) * rr, math.sin(a) * rr, 0.18 + rnd.uniform(0, 0.02)), K[m], seg=12, rings=8, scale=(1, 1, 1.2))
        else:
            box(f"F{i}", (0.045, 0.04, 0.035), (math.cos(a) * rr, math.sin(a) * rr, 0.185), K[m], bevel=0.01,
                rot=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 3)))
    sphere("Cherry", 0.032, (0.02, -0.02, 0.225), K["cherry"], seg=16, rings=10)
    tube("CherryStem", [(0.02, -0.02, 0.25), (0.03, -0.01, 0.29), (0.05, 0.0, 0.31)], 0.003, K["stem"], res=3)
    sealed_lid("Lid", "FruitCup_Lid", 0.202, 0.25, K)
    spoon("Spoon", -0.12, -0.24, 0.0, K, yaw=20 * DEG, mat=K["plastic_cream"], s=0.9)


def side_salad(K):
    salad_bowl(K, r=0.2)


def rice_bowl_item(K):
    rice_bowl("Rice", 0, 0, 0, K, ume=True)


def miso_soup(K):
    """Instant miso soup in the stand's cup: the printed wrap, a plain miso-coloured lid sealed on (tofu and wakame inside)."""
    paper_cup(K, h=0.32, r0=0.16, r1=0.2, key="Miso_Wrap")
    surface("Soup", 0.182, 0.28, K["miso"])
    rnd = random.Random(1)
    for i in range(4):
        box(f"Tofu{i}", (0.03, 0.03, 0.02), (rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.285), K["tofu"], bevel=0.004)
        box(f"Wak{i}", (0.05, 0.025, 0.004), (rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 0.283), K["wakame"], bevel=0.001,
            rot=(0, 0, rnd.uniform(0, PI)))
    sealed_lid("Lid", "Swatch_miso", 0.214, 0.332, K)


def chocolate_milk(K):
    carton(K, "ChocoMilk_Front", "ChocoMilk_Back", "ChocoMilk_Top", "choc")


def strawberry_milk(K):
    carton(K, "Carton_Front", "Carton_Back", "Carton_Top", "pink")


# ------------------------------------------------------------------ counterware, litter and stock (dressing; not sold)

def cup_stack(K):
    """Six paper cups nested: the bottom cup whole, then each cup's top 0.06 and rim standing above the last."""
    paper_cup(K)
    for i in range(1, 6):
        z0 = 0.5 + (i - 1) * 0.06
        prof = [(0.198, z0 - 0.01), (0.206, z0 + 0.06), (0.218, z0 + 0.06), (0.218, z0 + 0.072), (0.196, z0 + 0.072)]
        prof += [(0.0, z0)] if i == 5 else [(0.19, z0 - 0.01)]
        lathe(f"Cup{i}", prof, K["paper"], seg=48)
        rolled_rim(f"Lip{i}", 0.218, z0 + 0.066, K["paper"], thick=0.008)


def lid_stack(K):
    for i in range(10):
        z = i * 0.022
        lathe(f"Lid{i}", [(0, z), (0.225, z), (0.228, z + 0.02), (0.2, z + 0.03), (0, z + 0.03)], K["plastic_red"], seg=40)
    box("Band", (0.08, 0.47, 0.232), (0, 0, 0.116), K["paper"], bevel=0.004)


def straw_holder(K):
    lathe("Holder", [(0, 0), (0.12, 0), (0.125, 0.012), (0.09, 0.03), (0.08, 0.45), (0.09, 0.47), (0.0, 0.47)], K["iron"], seg=32)
    hoop("Band", (0, 0, 0.25), 0.083, "Z", K["brass"], thick=0.008)
    rnd = random.Random(3)
    for i in range(11):
        a = i / 11 * 2 * PI
        x, y = math.cos(a) * 0.045, math.sin(a) * 0.045
        stick(f"Straw{i}", (x, y, 0.45), (x * 2.2 + rnd.uniform(-0.02, 0.02), y * 2.2, 0.8 + rnd.uniform(0, 0.05)), 0.014, K,
              mat=K["straw_red"] if i % 2 else K["paper"])


def napkin_dispenser(K):
    box("Body", (0.5, 0.32, 0.4), (0, 0, 0.2), K["iron"], bevel=0.03, segments=3)
    box("Napkins", (0.42, 0.04, 0.22), (0, -0.15, 0.25), K["paper"], bevel=0.004)
    box("Tongue", (0.12, 0.02, 0.06), (0, -0.175, 0.36), K["paper"], bevel=0.004, rot=(-20 * DEG, 0, 0))
    pplate("Plate", "Napkin_Plate", B43.rect(0.3, 0.1, 0), 0.01, K, "gilt", T(0, -0.165, 0.07))
    box("Cap", (0.54, 0.36, 0.03), (0, 0, 0.415), K["brass"], bevel=0.01)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.025, (sx * 0.22, 0, 0.45), K["brass"], seg=12, rings=8)


def boat_stack(K):
    for i in range(6):
        pbox(f"Boat{i}", 0.62, 0.34, 0.08, K, {"-y": "Boat_Print"} if i == 5 else {}, "kraft", z0=i * 0.02, taper=1.12)


def skewer_cup(K):
    lathe("Cup", [(0, 0), (0.1, 0), (0.11, 0.3), (0.1, 0.3), (0.09, 0.02), (0, 0.02)], K["enamel"], seg=32)
    rnd = random.Random(7)
    for i in range(14):
        a = i / 14 * 2 * PI
        x, y = math.cos(a) * 0.05, math.sin(a) * 0.05
        stick(f"Skewer{i}", (x, y, 0.05), (x * 1.8 + rnd.uniform(-0.01, 0.01), y * 1.8, 0.62 + rnd.uniform(0, 0.04)), 0.006, K)


def sauce_bottle(K, key, cap):
    lathe("Bottle", [(0, 0), (0.1, 0), (0.11, 0.04), (0.11, 0.3), (0.06, 0.38), (0.04, 0.4), (0, 0.4)], K["plastic_cream"], seg=32)
    band("Label", key, 0.113, 0.113, 0.08, 0.27, K, n=32, rows=2)
    lathe("Cap", [(0, 0.39), (0.046, 0.39), (0.046, 0.43), (0.04, 0.46), (0.012, 0.5), (0, 0.5)], K[cap], seg=24, flute=(18, 0.04))


def litter_film(K):
    for i, (x, y, a) in enumerate(((-0.08, 0.0, 20), (0.1, 0.04, -35))):
        o = box(f"Film{i}", (0.22, 0.16, 0.004), (x, y, 0.004 + i * 0.006), K["film"], bevel=0.0, rot=(0, 0, a * DEG))
        organic(o, 0.004, 0.03)
    pplate("Band", "Onigiri_Band", B43.rect(0.24, 0.045, 0), 0.004, K, "film", T(0.02, 0.0, 0.016) @ RX(-90 * DEG))


def litter_chipbag(K):
    st = _mark()
    o = pillow("Bag", 0.5, 0.68, 0.05, K, "Crisps_Front", "Crisps_Back", "crisps")
    rnd = random.Random(2)
    for v in o.data.vertices:
        v.co.y += 0.03 * math.sin(v.co.z * 14 + v.co.x * 9) * rnd.uniform(0.4, 1.0)
    _xform(st, T(0, -0.3, 0.035) @ RX(-90 * DEG))


def litter_wrappers(K):
    rnd = random.Random(12)
    for i, key in enumerate(("Choc_Wrapper", "Senbei_Sleeve", "Swatch_gummies", "Licorice_Band")):
        x, y = (i % 2) * 0.24 - 0.12, (i // 2) * 0.2 - 0.1
        pplate(f"Wrap{i}", key, B43.rect(0.2, 0.12, 0), 0.004, K, "paper", T(x, y, 0.004 + i * 0.001) @ RZ(rnd.uniform(0, PI)) @ RX(-90 * DEG))


def litter_can(K):
    st = _mark()
    can(K, "Can_RedLantern")
    for o in P.PARTS[st:]:
        for v in o.data.vertices:
            k = 1.0 - 0.35 * math.exp(-((v.co.z - 0.3) / 0.12) ** 2) * max(0.0, -v.co.y / 0.17 + 0.2)
            v.co.y *= k
    _xform(st, T(0.31, 0, 0.165) @ RY(-90 * DEG))


def candy_jar(K, label, fill):
    lathe("Base", [(0, 0), (0.24, 0), (0.245, 0.02), (0.235, 0.04), (0, 0.04)], K["iron"], seg=40)
    rnd = random.Random(len(label))
    if fill == "gummies":
        for i in range(38):
            a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.16)
            m = ("gum_red", "gum_violet", "gum_green")[i % 3]
            box(f"G{i}", (0.06, 0.035, 0.03), (math.cos(a) * rr, math.sin(a) * rr, 0.07 + (i // 8) * 0.05), K[m], bevel=0.012,
                rot=(rnd.uniform(0, PI), rnd.uniform(0, PI), rnd.uniform(0, PI)))
    elif fill == "konpeito":
        for i in range(60):
            a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.16)
            m = ("k_pink", "k_yellow", "k_blue", "k_white")[i % 4]
            spiky(f"K{i}", 0.022, (math.cos(a) * rr, math.sin(a) * rr, 0.07 + (i // 12) * 0.045), K[m], seed=i)
    else:
        for i in range(44):
            a, rr = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.16)
            cyl(f"M{i}", 0.03, 0.018, (math.cos(a) * rr, math.sin(a) * rr, 0.06 + (i // 9) * 0.04), K["mint"], verts=12, bevel=0.006,
                rot=(rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), 0))
    lathe("Lid", [(0, 0.62), (0.16, 0.62), (0.17, 0.66), (0.12, 0.7), (0.04, 0.72), (0.04, 0.78), (0.0, 0.8)], K["brass"], seg=40)
    sphere("Knob", 0.035, (0, 0, 0.8), K["brass"], seg=16, rings=10)
    pplate("Label", label, B43.rect(0.26, 0.17, 0), 0.006, K, "paper", T(0, -0.226, 0.36))
    as_glass()
    lathe("Glass", [(0, 0.04), (0.2, 0.04), (0.22, 0.1), (0.22, 0.55), (0.17, 0.62), (0.155, 0.62), (0.2, 0.55), (0.2, 0.1),
                    (0.18, 0.055), (0, 0.055)], K["glass_jar"], seg=40)
    as_main()


def bottle_crate(K):
    W, D, H = 1.3, 0.9, 0.42
    box("Floor", (W, D, 0.04), (0, 0, 0.02), K["pine"], bevel=0.008)
    for sx in (-1, 1):
        box(f"End{sx}", (0.05, D, H), (sx * (W / 2 - 0.025), 0, H / 2), K["pine"], bevel=0.01)
        box(f"Grip{sx}", (0.052, 0.3, 0.08), (sx * (W / 2 - 0.025), 0, H - 0.09), K["oak"], bevel=0.02)
        for sy in (-1, 1):
            box(f"Corner{sx}{sy}", (0.06, 0.06, H), (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H / 2), K["iron"], bevel=0.01)
    for sy in (-1, 1):
        for z in (0.1, 0.3):
            box(f"Slat{sy}{z}", (W - 0.1, 0.035, 0.12), (0, sy * (D / 2 - 0.018), z), K["pine"], bevel=0.008)
    pplate("Stencil", "Crate_Stencil", B43.rect(1.0, 0.2, 0), 0.004, K, "kraft", T(0, -D / 2 - 0.003, 0.2))
    for i in range(4):
        for j in range(3):
            st = _mark()
            lathe(f"B{i}{j}", [(0, 0), (0.12, 0), (0.13, 0.03), (0.13, 0.36), (0.1, 0.43), (0.06, 0.47), (0.08, 0.51), (0.06, 0.56),
                               (0.065, 0.62), (0, 0.62)], K["glass_teal"], seg=24)
            lathe(f"C{i}{j}", [(0, 0.615), (0.065, 0.615), (0.066, 0.67), (0, 0.67)], K["plastic_blue"], seg=16, flute=(16, 0.04))
            band(f"L{i}{j}", "Can_Ramune", 0.133, 0.133, 0.08, 0.32, K, n=24, k=0.8)
            _xform(st, T(-0.45 + i * 0.3, -0.27 + j * 0.27, 0.04))


def can_tray(K):
    pbox("Tray", 1.12, 0.82, 0.16, K, {"-y": "Tray_Stencil", "+y": "Tray_Stencil"}, "redlantern")
    for i in range(4):
        for j in range(3):
            st = _mark()
            lathe(f"Can{i}{j}", [(0, 0.02), (0.1, 0.0), (0.135, 0.03), (0.135, 0.44), (0.115, 0.48), (0.115, 0.49), (0.108, 0.49),
                                 (0.105, 0.475), (0, 0.475)], K["alu"], seg=24)
            band(f"W{i}{j}", "Label_Cola", 0.137, 0.137, 0.04, 0.43, K, n=24, k=1.2)
            hoop(f"R{i}{j}", (0, 0, 0.488), 0.112, "Z", K["alu"], thick=0.006)
            _xform(st, T(-0.405 + i * 0.27, -0.27 + j * 0.27, 0.012))


def bento_stack(K):
    for i in range(3):
        st = _mark()
        bento(K)
        _xform(st, T(0.02 * (i % 2), 0, i * 0.335) @ RZ((i - 1) * 3 * DEG))


def bun_tray(K):
    box("Tray", (1.2, 0.8, 0.03), (0, 0, 0.015), K["enamel"], bevel=0.01)
    for sx in (-1, 1):
        box(f"RimX{sx}", (0.03, 0.8, 0.08), (sx * 0.585, 0, 0.04), K["enamel"], bevel=0.01)
    for sy in (-1, 1):
        box(f"RimY{sy}", (1.2, 0.03, 0.08), (0, sy * 0.385, 0.04), K["enamel"], bevel=0.01)
    flatcard("Doily", "Tray_Mat", 1.1, 0.7, 0, 0, 0.03, K)
    for i in range(3):
        st = _mark()
        melon_bread(K)
        _xform(st, T(-0.38 + i * 0.38, -0.17, 0.034) @ RZ(i))
    for i in range(3):
        st = _mark()
        nikuman(K) if i != 1 else curry_bread(K)
        _xform(st, T(-0.38 + i * 0.38, 0.18, 0.034))


# ------------------------------------------------------------------ the sheets

GLASS_BOTTLES = {
    "HolyLemonade": ("lemonade", "Label_Lemonade", "gilt",
                     [(0.14, 0), (0.15, 0.03), (0.15, 0.36), (0.13, 0.48), (0.07, 0.62), (0.055, 0.72), (0.06, 0.74), (0.06, 0.76)],
                     (0.1, 0.33)),
    "BlackCatCola": ("cola", "Label_Cola", "plastic_red",
                     [(0.13, 0), (0.15, 0.06), (0.13, 0.15), (0.15, 0.22), (0.15, 0.36), (0.12, 0.46), (0.065, 0.6), (0.055, 0.72),
                      (0.06, 0.74), (0.06, 0.76)], (0.23, 0.35)),
}


def _gb(item):
    liquid, key, cap, prof, lz = GLASS_BOTTLES[item]
    return lambda K: glass_bottle(K, liquid, key, cap, prof, lz)


SHEETS = {
    "ConcessionBakery": [("Onigiri", onigiri), ("MelonBread", melon_bread), ("YakisobaBun", yakisoba_bun), ("GarlicBread", garlic_bread),
                         ("CurryBread", curry_bread), ("Nikuman", nikuman), ("Taiyaki", taiyaki), ("CreamPuff", cream_puff)],
    "ConcessionHotFood": [("Bento", bento), ("MeatLoaf", meat_loaf), ("TakoyakiBoat", takoyaki_boat), ("CupRamen", cup_ramen),
                          ("RoastSweetPotato", roast_sweet_potato), ("YakitoriSkewers", yakitori), ("PumpkinSoup", pumpkin_soup)],
    "ConcessionDrinks": [("Ramune", ramune), ("BarleyTea", lambda K: can(K, "Can_Barley")),
                         ("CannedCoffee", lambda K: can(K, "Can_Coffee", h=0.46, r=0.13)), ("RedLantern", lambda K: can(K, "Can_RedLantern")),
                         ("HolyLemonade", _gb("HolyLemonade")), ("BlackCatCola", _gb("BlackCatCola")), ("GreenTea", green_tea),
                         ("StrawberryMilk", strawberry_milk)],
    "ConcessionSweets": [("HotCocoa", hot_cocoa), ("MelonSoda", melon_soda), ("PuddingCup", pudding_cup), ("EctoJelly", ecto_jelly),
                         ("MoonCake", moon_cake), ("Dango", dango), ("TombstoneCookie", tombstone_cookie)],
    "ConcessionCandy": [("BatGummies", bat_gummies), ("CandyApple", candy_apple), ("GhostMints", ghost_mints), ("KonpeitoStars", konpeito),
                        ("LicoriceWhips", licorice), ("ChocolateBar", chocolate_bar), ("Senbei", senbei), ("GraveCrisps", grave_crisps),
                        ("Popcorn", popcorn), ("PrankKit", prank_kit)],
    "ConcessionLunchSets": [("KatsuCurry", katsu_curry), ("ShoyuRamen", shoyu_ramen), ("KaraageSet", karaage_set),
                            ("MackerelSet", mackerel_set), ("Omurice", omurice)],
    "ConcessionLunchHouse": [("WitchingStew", witching_stew), ("ShepherdsPie", shepherds_pie), ("PumpkinGratin", pumpkin_gratin),
                             ("RavensRoast", ravens_roast)],
    "ConcessionLunchExtras": [("FruitCup", fruit_cup), ("SideSalad", side_salad), ("RiceBowl", rice_bowl_item), ("MisoSoup", miso_soup),
                              ("ChocolateMilk", chocolate_milk)],
    "ConcessionCounterware": [("CupStack", cup_stack), ("LidStack", lid_stack), ("StrawHolder", straw_holder),
                              ("NapkinDispenser", napkin_dispenser), ("BoatStack", boat_stack), ("SkewerCup", skewer_cup),
                              ("SoyBottle", lambda K: sauce_bottle(K, "Label_Soy", "plastic_red")),
                              ("MustardBottle", lambda K: sauce_bottle(K, "Label_Mustard", "plastic_black")),
                              ("LitterFilm", litter_film), ("LitterChipBag", litter_chipbag), ("LitterWrappers", litter_wrappers),
                              ("LitterCan", litter_can)],
    "ConcessionStock": [("JarGummies", lambda K: candy_jar(K, "Jar_Gummies", "gummies")),
                        ("JarKonpeito", lambda K: candy_jar(K, "Jar_Konpeito", "konpeito")),
                        ("JarMints", lambda K: candy_jar(K, "Jar_Mints", "mints")),
                        ("BottleCrate", bottle_crate), ("CanTray", can_tray), ("BentoStack", bento_stack), ("BunTray", bun_tray)],
}


def _footprint(start):
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for ob in P.PARTS[start:]:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def sheet(name):
    """Build a sheet's items in a row along X (0.2 apart), each its own group, standing on z = 0 and centred in Y."""
    def build(M):
        K = kit(M)
        x = 0.0
        for item, fn in SHEETS[name]:
            ITEM[0] = item
            set_group(item)
            st = _mark()
            fn(K)
            lo, hi = _footprint(st)
            _xform(st, T(x - lo.x, -(lo.y + hi.y) / 2, -lo.z))
            x += (hi.x - lo.x) + 0.2
        _xform(0, T(-(x - 0.2) / 2, 0, 0))
        if MISSING:
            print(f"[props] {name}: atlas regions not drawn yet (paper stand-ins): {sorted(MISSING)}", flush=True)
        return _dims()
    return build


for _n in SHEETS:
    P.BUILD[_n] = sheet(_n)
    P.PREVIEW_PAD[_n] = 0.62

BUILDERS = list(SHEETS)
