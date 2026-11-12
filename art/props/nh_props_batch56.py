"""Props batch 56: the lunch trays eaten in stages (the batch 54 lunch meals, partly eaten, mostly eaten and empty).

The owner asked for "different variants of the lunch trays, as the player progressively eats and finishes the food"
(2026-11-12). Each of the nine lunch trays is built again with its batch 54 builder and then eaten down: food taken off
bite by bite, broth, curry and stew levels dropping in their bowls, sauce smeared where it was scooped, crumbs and grains
left behind, and at the end the dirty dishes (a fish skeleton, a drumstick bone, a squeezed lemon, dregs of miso, the
cutlery laid down, a crumpled napkin), ready for the return hatch (batch 55). No gore.

  ConcessionLunchSets2 / 3 / 4    KatsuCurry, ShoyuRamen, KaraageSet, MackerelSet, Omurice       (2 partly, 3 mostly eaten, 4 empty)
  ConcessionLunchHouse2 / 3 / 4   WitchingStew, ShepherdsPie, PumpkinGratin, RavensRoast

Same layout as batch 54 (each item its own piece `<Sheet>_<Id>`, standing on z = 0, its tray centred), so in Roblox a stage
lines up with the full tray by the tray's bottom centre. The water glass on the katsu tray stays with the full tray's
`_Glass` piece and isn't built here. Stages share batch 54's materials and its ConcessionPrint atlas (the tray liners).
"""
import fnmatch
import math
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, _mark, _xform, _dims
import nh_props_batch54 as B

PI = math.pi
DEG = PI / 180
T, RX, RY, RZ = B.T, B.RX, B.RY, B.RZ

MEALS = {
    "ConcessionLunchSets": [("KatsuCurry", B.katsu_curry), ("ShoyuRamen", B.shoyu_ramen), ("KaraageSet", B.karaage_set),
                            ("MackerelSet", B.mackerel_set), ("Omurice", B.omurice)],
    "ConcessionLunchHouse": [("WitchingStew", B.witching_stew), ("ShepherdsPie", B.shepherds_pie), ("PumpkinGratin", B.pumpkin_gratin),
                             ("RavensRoast", B.ravens_roast)],
}


def kit(M):
    K = B.kit(M)
    K["ketchup_rice"] = B.food("KetchupRice", (0.72, 0.3, 0.12), 0.5, bump=0.004, scale=90, var=(0.8, 0.45, 0.2), var_scale=40, cells=160)
    return K


class Item:
    """The parts of the item being built (everything since `st`), and the edits that eat it down."""

    def __init__(self, st, K):
        self.st, self.K, self.n = st, K, 0

    def parts(self):
        return P.PARTS[self.st:]

    @staticmethod
    def _base(o):
        return o.name.split(".")[0]

    def find(self, *pats):
        return [o for o in self.parts() if any(fnmatch.fnmatchcase(self._base(o), p) for p in pats)]

    def drop(self, *pats):
        for o in self.find(*pats):
            P.PARTS.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)

    def box(self, *pats):
        """World bounds (lo, hi) of the matching parts."""
        bpy.context.view_layer.update()
        obs = self.find(*pats)
        assert obs, f"no part {pats}"
        ws = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
        lo = Vector([min(w[k] for w in ws) for k in range(3)])
        hi = Vector([max(w[k] for w in ws) for k in range(3)])
        return lo, hi

    def centre(self, *pats):
        lo, hi = self.box(*pats)
        return (lo + hi) / 2

    def xform(self, M, *pats):
        for o in self.find(*pats):
            o.matrix_world = M @ o.matrix_world

    def squash(self, pat, k, base=None):
        """Scale a part's height by k about a level (its bottom by default): a mound eaten down."""
        z = self.box(pat)[0].z if base is None else base
        self.xform(T(0, 0, z) @ Matrix.Diagonal((1, 1, k, 1)) @ T(0, 0, -z), pat)

    def trim(self, pat, k, axis=0, keep="min"):
        """Shorten a part along a world axis by k, keeping one end (a fillet or an omelette eaten from the other end)."""
        lo, hi = self.box(pat)
        a = lo[axis] if keep == "min" else hi[axis]
        d = [1, 1, 1, 1]
        d[axis] = k
        o = [0, 0, 0]
        o[axis] = a
        self.xform(T(*o) @ Matrix.Diagonal(d) @ T(*[-v for v in o]), pat)
        return self.box(pat)

    def shrink(self, pat, k, about):
        self.xform(T(*about) @ Matrix.Diagonal((k, k, k, 1)) @ T(*(-about)), pat)

    def sink(self, pat, dz, rs=1.0):
        """Lower a liquid surface by dz and narrow it by rs (about its own axis: a bowl narrows toward its foot)."""
        for o in self.find(pat):
            o.matrix_world = T(0, 0, -dz) @ o.matrix_world @ Matrix.Diagonal((rs, rs, 1, 1))

    def lower(self, dz, *pats):
        self.xform(T(0, 0, -dz), *pats)

    def move_to(self, pats, at, yaw=0.0):
        """Move a group of parts (cutlery) so its centre lands on `at`, turned by yaw about Z."""
        c = self.centre(*pats)
        self.xform(T(*at) @ RZ(yaw) @ T(*(-c)), *pats)

    # ---------------------------------------------------------------- leftovers
    def _name(self, s):
        self.n += 1
        return f"{s}{self.n}"

    def smear(self, mat, x, y, z, r, sy=0.6, yaw=0.0, seed=0):
        """A thin wobbly smear of sauce lying on a dish at height z."""
        o = B.surface(self._name("Smear"), r, z + 0.004, self.K[mat], sy=sy, wob=0.35, seed=seed)
        o.matrix_world = T(x, y, 0) @ RZ(yaw)
        return o

    def crumbs(self, mat, x, y, z, r, n, size, seed=0, flat=0.55):
        rnd = random.Random(seed)
        for _ in range(n):
            a, rr = rnd.uniform(0, 2 * PI), r * math.sqrt(rnd.random())
            B.lumpy(self._name("Crumb"), size * rnd.uniform(0.7, 1.3), (x + math.cos(a) * rr, y + math.sin(a) * rr, z + size * 0.3),
                    self.K[mat], scale=(1, rnd.uniform(0.7, 1.2), flat), amt=0.3, seed=rnd.randint(0, 999), seg=7, rings=5)

    def shreds(self, mat, x, y, z, r, n, seed=0, w=0.05):
        rnd = random.Random(seed)
        for _ in range(n):
            a, rr = rnd.uniform(0, 2 * PI), r * math.sqrt(rnd.random())
            box(self._name("Shred"), (w * rnd.uniform(0.6, 1.2), 0.008, 0.004), (x + math.cos(a) * rr, y + math.sin(a) * rr, z + 0.003),
                self.K[mat], bevel=0.0, rot=(0, 0, rnd.uniform(0, PI)))

    def napkin(self, x, y, z=0.034, seed=0):
        """A crumpled paper napkin."""
        o = B.lumpy(self._name("Napkin"), 0.075, (x, y, z + 0.032), self.K["paper"], scale=(1.25, 1.0, 0.55), amt=0.55, seed=seed,
                    seg=16, rings=10)
        B.organic(o, 0.012, 0.025)
        return o


TRAY_TOP = 0.034


def bowl_floor(it, pat):
    return it.box(pat)[0].z + 0.047


def plate_floor(it, pat="Plate"):
    return it.box(pat)[0].z + 0.02


# ------------------------------------------------------------------ the stages, meal by meal (s: 2 partly, 3 mostly, 4 empty)

def katsu_curry(it, s):
    fl = plate_floor(it)
    n = {2: 2, 3: 4, 4: 6}[s]
    it.drop(*[f"Katsu{i}" for i in range(n)], *[f"KatsuIn{i}" for i in range(n)], *[f"Carrot{i}" for i in range(n)],
            *[f"Pot{i}" for i in range(n)])
    rc = it.centre("Rice")
    if s < 4:
        it.squash("Rice", {2: 0.72, 3: 0.45}[s], base=fl)
        it.sink("Curry", 0.004, {2: 0.8, 3: 0.55}[s])
        it.squash("Water", {2: 0.65, 3: 0.3}[s])
        if s == 3:
            it.drop("Fuku0", "Fuku1", "Fuku2")
        it.smear("curry", rc.x + 0.06, rc.y - 0.04, fl, 0.06, sy=0.5, yaw=0.4, seed=1)
    else:
        cc = it.centre("Curry")
        it.drop("Rice", "Curry", "Water", "Fuku0", "Fuku1", "Fuku2", "Fuku3")
        it.smear("curry", cc.x - 0.02, cc.y + 0.02, fl, 0.13, sy=0.45, yaw=0.3, seed=2)
        it.smear("curry", rc.x + 0.02, rc.y - 0.05, fl, 0.07, sy=0.5, yaw=-0.6, seed=3)
        it.crumbs("rice", rc.x, rc.y, fl, 0.1, 9, 0.012, seed=4)
        it.crumbs("panko", cc.x, cc.y, fl, 0.12, 6, 0.01, seed=5)
        pc = it.centre("Plate")
        it.move_to(("SpoonBowl", "SpoonHandle"), (pc.x + 0.06, pc.y - 0.05, fl + 0.025), yaw=-60 * DEG)
        it.napkin(-0.5, -0.32, seed=1)


def shoyu_ramen(it, s):
    floor = bowl_floor(it, "Bowl")
    dz = {2: 0.03, 3: 0.07, 4: 0.13}[s]
    rs = {2: 0.96, 3: 0.91, 4: 0.7}[s]     # the bowl's inside radius at the new level (a hair over, hidden in the wall)
    drop = {2: ["Chashu0", "Egg0", "Yolk0", "Naruto", "NarutoSwirl"] + [f"Noodle{i}" for i in range(6)] + ["Menma0", "Menma1"]
            + [f"Negi{i}" for i in range(5)],
            3: ["Chashu*", "Egg*", "Yolk*", "Naruto*", "Nori"] + [f"Noodle{i}" for i in range(15)] + ["Menma*"]
            + [f"Negi{i}" for i in range(12)],
            4: ["Chashu*", "Egg*", "Yolk*", "Naruto*", "Nori", "Noodle*", "Menma*"] + [f"Negi{i}" for i in range(13)]}[s]
    it.drop(*drop)
    it.sink("Broth", dz, rs)
    it.lower(dz, "Noodle*", "Chashu*", "Egg*", "Yolk*", "Menma*", "Negi*")
    if s == 4:
        bc = it.centre("Bowl")
        hi = it.box("Bowl")[1].z
        it.move_to(("Chop0", "Chop0t", "Chop1", "Chop1t"), (bc.x, bc.y - 0.06, hi + 0.012), yaw=90 * DEG)
        it.napkin(0.42, 0.3, seed=2)


def _miso(it, s):
    dz = {2: 0.025, 3: 0.045, 4: 0.06}[s]   # a little left in the bottom at the end
    it.drop(*{2: ["MisoTofu0", "MisoTofu1", "MisoNegi0", "MisoNegi1", "MisoNegi2"],
              3: ["MisoTofu0", "MisoTofu1", "MisoTofu2", "MisoTofu3", "MisoWakame0", "MisoWakame1"] + [f"MisoNegi{i}" for i in range(5)],
              4: ["MisoTofu*", "MisoNegi*", "MisoWakame0", "MisoWakame1", "MisoWakame2"]}[s])
    it.sink("MisoMiso", dz, {2: 1.0, 3: 0.97, 4: 0.88}[s])    # fitted to the bowl's inside
    it.lower(dz, "MisoTofu*", "MisoWakame*", "MisoNegi*")


def _rice(it, s, x=0.0):
    floor = bowl_floor(it, "RiceBowl")
    if s < 4:
        it.squash("RiceRice", {2: 0.7, 3: 0.42}[s], base=floor)
        c = it.centre("RiceRice")
        k = {2: 0.95, 3: 0.82}[s]       # narrower too, so from above it reads as less rice
        it.xform(T(c.x, c.y, 0) @ Matrix.Diagonal((k, k, 1, 1)) @ T(-c.x, -c.y, 0), "RiceRice")
    else:
        c = it.centre("RiceBowl")
        it.drop("RiceRice")
        it.crumbs("rice", c.x, c.y, floor, 0.06, 8, 0.011, seed=7)


def karaage_set(it, s):
    fl = plate_floor(it)
    it.drop(*{2: ["Karaage0", "Karaage1"], 3: ["Karaage0", "Karaage1", "Karaage2", "Karaage3", "Mayo"], 4: ["Karaage*", "Mayo"]}[s])
    cab = it.centre("Cabbage")
    if s < 4:
        it.squash("Cabbage", {2: 0.8, 3: 0.5}[s], base=fl)
    else:
        it.drop("Cabbage")
        it.shreds("cabbage", cab.x, cab.y, fl, 0.1, 9, seed=3)
        it.squash("Lemon", 0.55)
    if s >= 3:
        it.smear("mayo", cab.x + 0.08, cab.y - 0.08, fl, 0.035, sy=0.7, seed=4)
    if s == 4:
        pc = it.centre("Plate")
        it.crumbs("karaage", pc.x - 0.08, pc.y - 0.04, fl, 0.1, 6, 0.012, seed=5)
    _rice(it, s)
    _miso(it, s)
    if s == 4:
        # (the chopsticks stay where they lie: across the rice bowl they'd stick out past the tray)
        it.napkin(-0.5, -0.3, seed=3)


def mackerel_set(it, s):
    lo, hi = it.box("Fillet")
    top = it.box("Plate")[1].z
    if s < 4:
        nlo, nhi = it.trim("Fillet", {2: 0.68, 3: 0.36}[s], axis=0, keep="min")
        for o in it.find("Grill*"):
            c = it.centre(it._base(o))
            if c.x > nhi.x - 0.02:
                P.PARTS.remove(o)
                bpy.data.objects.remove(o, do_unlink=True)
        it.drop(*{2: ["Pickle0"], 3: ["Pickle0", "Pickle1", "Pickle2", "Soy"]}[s])
        if s == 3:
            it.squash("Daikon", 0.5)
    else:
        dc = it.centre("Daikon")
        it.drop("Fillet", "Grill*", "Daikon", "Soy", "Pickle[0-9]")
        # the skeleton: a spine down the plate, ribs either side, a little tail
        y = (lo.y + hi.y) / 2
        z = top + 0.008
        x0, x1 = lo.x + 0.04, hi.x - 0.04
        tube(it._name("Spine"), [(x0, y, z), ((x0 + x1) / 2, y + 0.005, z + 0.003), (x1, y, z)], 0.007, it.K["bone"], res=4)
        for k in range(10):
            x = x0 + 0.05 + k * (x1 - x0 - 0.1) / 9
            ln = 0.07 * math.sin(PI * (k + 1) / 11) + 0.02
            for sy in (-1, 1):
                tube(it._name("Rib"), [(x, y, z), (x - 0.015, y + sy * ln * 0.6, z + 0.002), (x - 0.03, y + sy * ln, z)], 0.0028,
                     it.K["bone"], res=2)
        for sy in (-1, 1):
            tube(it._name("Tail"), [(x0, y, z), (x0 - 0.04, y + sy * 0.03, z)], 0.006, it.K["bone"], poly=True)
        it.smear("daikon", dc.x, dc.y, top, 0.03, sy=0.8, seed=5)
        it.smear("sauce", dc.x + 0.02, dc.y - 0.01, top + 0.001, 0.018, sy=0.7, seed=6)
        pc = it.centre("PickleDish")
        it.crumbs("pickle", pc.x, pc.y, it.box("PickleDish")[0].z + 0.012, 0.03, 2, 0.01, seed=7)
        rest = it.centre("Rest")
        it.move_to(("Chop0", "Chop0t", "Chop1", "Chop1t"), ((lo.x + hi.x) / 2 + 0.02, y - 0.09, top + 0.012), yaw=-90 * DEG)
        it.napkin(0.46, -0.32, seed=4)
    _rice(it, s)
    _miso(it, s)


def omurice(it, s):
    fl = plate_floor(it)
    if s < 4:
        k = {2: 0.7, 3: 0.4}[s]
        lo, hi = it.trim("Omelette", k, axis=0, keep="min")
        it.trim("Demi", k, axis=0, keep="min")
        for o in it.find("Parsley*"):
            if it.centre(it._base(o)).x > hi.x - 0.03:
                P.PARTS.remove(o)
                bpy.data.objects.remove(o, do_unlink=True)
        # the ketchup rice where the omelette was cut into
        c = (lo + hi) / 2
        o = B.lumpy(it._name("KRice"), 0.075, (hi.x - 0.02, c.y, fl + 0.02), it.K["ketchup_rice"], scale=(0.7, 1.1, 0.6), amt=0.3, seed=s,
                    seg=12, rings=8)
        B.organic(o, 0.006, 0.02)
        it.smear("demi", hi.x + 0.06, c.y + 0.03, fl, 0.05, sy=0.45, yaw=0.3, seed=1)
        if s == 3:
            it.drop("Lettuce0", "Lettuce1", "Lettuce2", "Lettuce3", "Tomato0", "Cucumber0", "Cucumber1")
    else:
        c = it.centre("Omelette")
        it.drop("Omelette", "Demi", "Parsley*", "Lettuce0", "Lettuce1", "Lettuce2", "Lettuce3", "Lettuce4", "Lettuce5", "Tomato0",
                "Tomato1", "Cucumber*")
        it.smear("demi", c.x, c.y, fl, 0.15, sy=0.22, yaw=0.08, seed=2)
        it.smear("ketchup_rice", c.x + 0.08, c.y - 0.03, fl, 0.06, sy=0.6, seed=3)
        it.crumbs("ketchup_rice", c.x - 0.04, c.y + 0.02, fl, 0.1, 9, 0.011, seed=4)
        pc = it.centre("Plate")
        it.move_to(("SpoonBowl", "SpoonHandle"), (pc.x + 0.1, pc.y - 0.06, fl + 0.025), yaw=-70 * DEG)
        it.napkin(0.45, -0.3, seed=5)


def witching_stew(it, s):
    fl = plate_floor(it)
    dz = {2: 0.04, 3: 0.08, 4: 0.13}[s]
    it.drop(*{2: ["Chunk0", "Chunk1", "Chunk2", "Chunk3", "Parsley0", "Parsley1", "Parsley2"],
              3: [f"Chunk{i}" for i in range(8)] + ["Parsley*", "Lid"],
              4: ["Chunk*", "Parsley*", "Lid"]}[s])
    lid = None
    if s == 4:
        it.squash("Loaf", 0.6, base=fl)
        it.squash("Crumb", 0.6, base=fl)
    it.sink("Stew", dz, {2: 0.97, 3: 0.95, 4: 0.9}[s])
    it.lower(dz, "Chunk*", "Parsley*")
    if s == 2:
        lo, hi = it.box("Lid")
        it.shrink("Lid", 0.72, Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)))
    if s >= 3:
        lc = it.centre("Plate")
        it.crumbs("crust", lc.x + 0.2, lc.y - 0.12, fl, 0.08, 7 if s == 3 else 10, 0.014, seed=s)
    if s == 4:
        c = it.centre("Loaf")
        it.smear("stew", c.x + 0.2, c.y + 0.1, fl, 0.05, sy=0.6, seed=2)
        it.crumbs("crumbin", c.x - 0.2, c.y + 0.12, fl, 0.06, 6, 0.012, seed=3)
        pc = it.centre("Plate")
        it.move_to(("SpoonBowl", "SpoonHandle"), (pc.x + 0.12, pc.y - 0.17, fl + 0.03), yaw=-30 * DEG)
        it.napkin(0.42, -0.04, seed=6)


def shepherds_pie(it, s):
    top = it.box("Dish")[1].z
    it.drop(*{2: ["Mash0", "Mash1"], 3: ["Mash0", "Mash1", "Mash2", "Mash3", "Mash4", "Stone0", "Stone1"],
              4: ["Mash*", "Stone*", "Gravy"]}[s])
    if s < 4:
        # where the mash was dug out, the mince underneath shows (the flat gravy layer read black there)
        for o in it.find("Gravy"):
            B.recolour(o, it.K["beef"])
            B.organic(o, 0.005, 0.012)
        it.lower(-0.006, "Gravy")
    if s == 4:
        lo, hi = it.box("Dish")
        c = (lo + hi) / 2
        # the dish's lip, so the scraped top reads as the inside of the dish
        w, d = (hi.x - lo.x) - 0.1, (hi.y - lo.y) - 0.06
        pts = [(c.x - w / 2, c.y - d / 2, top + 0.01), (c.x + w / 2, c.y - d / 2, top + 0.01), (c.x + w / 2, c.y + d / 2, top + 0.01),
               (c.x - w / 2, c.y + d / 2, top + 0.01)]
        tube(it._name("Lip"), pts, 0.016, it.K["enamel"], closed=True, poly=True, square=True)
        for k, (dx, dy, r, yaw) in enumerate(((-0.1, 0.04, 0.09, 0.2), (0.08, -0.05, 0.11, -0.4), (0.15, 0.08, 0.05, 1.0))):
            it.smear("gravy", c.x + dx, c.y + dy, top, r, sy=0.5, yaw=yaw, seed=k)
        rnd = random.Random(11)
        for k in range(5):
            x, y = c.x + rnd.uniform(-0.18, 0.18), c.y + rnd.uniform(-0.12, 0.12)
            tube(it._name("MashStreak"), [(x, y, top + 0.006), (x + 0.04, y + rnd.uniform(-0.02, 0.02), top + 0.008),
                                          (x + 0.08, y + rnd.uniform(-0.02, 0.02), top + 0.006)], 0.01, it.K["mash"], res=3)
        it.crumbs("shortbread", c.x + 0.14, c.y - 0.1, top, 0.04, 4, 0.01, seed=12)
        it.move_to(("SpoonBowl", "SpoonHandle"), (c.x + 0.02, c.y - 0.04, top + 0.03), yaw=-40 * DEG)
        it.napkin(0.44, 0.28, seed=7)


def pumpkin_gratin(it, s):
    fl = plate_floor(it)
    inner = fl + 0.18
    if s < 4:
        # scooped from the spoon's side: the cheese sinks and is dug back, the pumpkin's inside showing beside it
        it.squash("Gratin", {2: 0.75, 3: 0.45}[s], base=inner)
        it.trim("Gratin", {2: 0.62, 3: 0.32}[s], axis=0, keep="min")
        c = it.centre("Pumpkin")
        it.smear("gratin", c.x + 0.06, c.y + 0.02, inner, 0.05, sy=0.7, seed=s)
    else:
        c = it.centre("Pumpkin")
        it.drop("Gratin")
        it.smear("gratin", c.x, c.y, inner, 0.1, sy=0.85, seed=1)
        it.crumbs("gratin", c.x + 0.04, c.y - 0.03, inner, 0.07, 6, 0.012, seed=2)
        pc = it.centre("Plate")
        it.smear("gratin", pc.x - 0.24, pc.y + 0.1, fl, 0.04, sy=0.6, seed=3)
        # (the spoon stays on the tray where it was: the pumpkin fills its plate)
        it.napkin(0.42, 0.28, seed=8)


def ravens_roast(it, s):
    fl = plate_floor(it)
    bone = it.centre("Bone")
    leg = it.centre("Leg")
    it.drop(*{2: ["Pot0", "Carrot0", "Carrot1"], 3: ["Pot0", "Pot1", "Pot2", "Carrot0", "Carrot1", "Carrot2"],
              4: ["Pot*", "Carrot0", "Carrot1", "Carrot2", "Leg"]}[s])
    if s < 4:
        it.shrink("Leg", {2: 0.85, 3: 0.6}[s], bone)
        it.sink("Gravy", 0.0, {2: 0.8, 3: 0.55}[s])
        if s == 3:
            it.smear("gravy", leg.x + 0.1, leg.y - 0.08, fl, 0.05, sy=0.5, yaw=0.5, seed=1)
    else:
        g = it.centre("Gravy")
        it.drop("Gravy")
        # the drumstick bone: the knuckle (kept) on a clean shaft, a small knob at its far end
        d = (leg - bone)
        d.z = 0
        d = d.normalized()
        a = Vector((bone.x, bone.y, fl + 0.025))
        b = a + d * 0.2
        tube(it._name("Shaft"), [a, (a + b) / 2 + Vector((0, 0, 0.004)), b], 0.016, it.K["bone"], res=4)
        sphere(it._name("Knob"), 0.024, b, it.K["bone"], seg=10, rings=6, scale=(1, 1, 0.8))
        it.smear("gravy", g.x, g.y, fl, 0.12, sy=0.5, yaw=0.4, seed=2)
        it.smear("gravy", g.x + 0.12, g.y - 0.1, fl, 0.05, sy=0.6, yaw=-0.3, seed=3)
        it.crumbs("roast", g.x - 0.05, g.y + 0.05, fl, 0.08, 6, 0.012, seed=4)
        pc = it.centre("Plate")
        # knife and fork laid side by side across the plate (finished)
        # (clear of the bone, which lies across the top of the plate)
        it.move_to(("KnifeHandle", "KnifeBlade"), (pc.x + 0.02, pc.y - 0.17, fl + 0.03), yaw=-45 * DEG)
        it.move_to(("ForkHandle", "ForkNeck", "ForkTine*"), (pc.x + 0.08, pc.y - 0.12, fl + 0.03), yaw=-45 * DEG)
        it.napkin(0.46, 0.3, seed=9)


STAGE = {"KatsuCurry": katsu_curry, "ShoyuRamen": shoyu_ramen, "KaraageSet": karaage_set, "MackerelSet": mackerel_set, "Omurice": omurice,
         "WitchingStew": witching_stew, "ShepherdsPie": shepherds_pie, "PumpkinGratin": pumpkin_gratin, "RavensRoast": ravens_roast}


# ------------------------------------------------------------------ the sheets

def sheet(family, s):
    """A row of the family's trays at stage s, laid out as batch 54 lays its sheets (0.2 apart, centred, z = 0)."""
    def build(M):
        K = kit(M)
        x = 0.0
        for item, fn in MEALS[family]:
            B.ITEM[0] = item
            set_group(item)
            st = _mark()
            fn(K)
            it = Item(st, K)
            # the water glass stays with the full tray's _Glass piece
            for o in [o for o in it.parts() if o["nh_group"].endswith("_Glass")]:
                P.PARTS.remove(o)
                bpy.data.objects.remove(o, do_unlink=True)
            set_group(item)
            STAGE[item](it, s)
            lo, hi = B._footprint(st)
            _xform(st, T(x - lo.x, -(lo.y + hi.y) / 2, -lo.z))
            x += (hi.x - lo.x) + 0.2
        _xform(0, T(-(x - 0.2) / 2, 0, 0))
        return _dims()
    return build


SHEETS = {}
for _fam in MEALS:
    for _s in (2, 3, 4):
        SHEETS[f"{_fam}{_s}"] = (_fam, _s)
        P.BUILD[f"{_fam}{_s}"] = sheet(_fam, _s)
        P.PREVIEW_PAD[f"{_fam}{_s}"] = 0.62

BUILDERS = list(SHEETS)
