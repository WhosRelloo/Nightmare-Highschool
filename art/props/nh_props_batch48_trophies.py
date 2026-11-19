"""Props batch 48, trophies (2026-11-18), for nh_props.py: the Permanent Record's trophies (docs/expansion/14 §5,
release 2.33). Shelf pieces, about 1.2 to 2 studs tall, made to read in a 3D turntable (the Locker's Trophy Case) and on
the dorm room's trophy wall. Gilt and brass, deep crimson enamel, oak plinths with brass plates, black leather, iron.
Gothic, polished and earned: no blood, no gore, no Seal motif (the owner retired it).

  ClubCup            a two-handled loving cup on a stepped oak plinth: a fluted gilt bowl, a crimson enamel band, curled
                     handles, a lidded finial (a club's weekly match win)
  HonourRollPlaque   an oak heater-shield plaque: a gilt laurel wreath round an open book, a brass scroll banner, a crimson
                     ribbon and tassel hung from the top (an A report card)
  RingBelt           the Ring's championship belt on an iron stand: black tooled leather, a big gilt centre plate with a
                     crimson cabochon and raised fists, two side plates, rivets (beating the champion)
  TheRegister        Chapter One: the school register on a small oak lectern, a brass corner-bound ledger with a clasp and a
                     crimson bookmark ribbon, a quill in a pewter well
  PathMedal<Path>    a medal on a ribbon hung from a small iron stand on an oak base, one per Standing Path at its top tier:
                     Academic (an open book), Social (two figures), Combat (a fist), Athletic (a pennant), Supernatural (a
                     crescent moon and star); struck gilt with a crimson enamel ring

Front faces -Y, Z up, the origin at the bottom centre. One piece (Main) each. Registered into nh_props.BUILD on import.
  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_props_batch48_trophies.py -- <Prop|all> [--size 1024] [--samples 64]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import nh_props as P  # noqa: E402
from nh_props import box, cyl, tube, material  # noqa: E402
from nh_props_batch4 import lathe, hoop, prism, _dims  # noqa: E402

PI = math.pi


def tk(M):
    """The trophy materials: the school palette plus a brighter gilt, a polished crimson enamel and pewter."""
    K = dict(M)
    K["gilt"] = material("TrophyGilt", "NH_Brass", tint=(1.12, 0.96, 0.62), scale=0.6, rough_mul=0.55, wear=0.2, dirt=0.45)
    K["giltdk"] = material("TrophyGiltDark", "NH_Brass", tint=(0.7, 0.55, 0.3), scale=0.6, rough_mul=0.8, wear=0.3, dirt=0.7)
    K["enamel"] = material("TrophyEnamel", base=(0.16, 0.005, 0.02), rough=0.2, metal=0.0, wear=0.1, dirt=0.25)
    K["plinth"] = material("TrophyPlinth", "NH_DeskWood", tint=(0.2, 0.11, 0.065), scale=0.22, rough_add=0.02, wear=0.4)
    K["pewter"] = material("TrophyPewter", "NH_Iron", tint=(0.55, 0.55, 0.58), scale=0.5, rough_mul=0.7, wear=0.3, wear_metal=True)
    K["ribbon"] = material("TrophyRibbon", "NH_Leather", tint=(0.17, 0.008, 0.02), scale=2.6, normal=0.25, rough_add=0.25, wear=0.1)
    K["ribbonblk"] = material("TrophyRibbonBlack", "NH_Leather", tint=(0.04, 0.035, 0.04), scale=2.6, normal=0.25, rough_add=0.2, wear=0.1)
    K["belt"] = material("TrophyBelt", "NH_Leather", tint=(0.06, 0.045, 0.045), scale=1.4, normal=0.9, wear=0.35)
    return K


def plinth(K, w, d, h, steps=2):
    """A stepped oak plinth with a moulded top and a brass name plate on the front."""
    z = 0.0
    for i in range(steps):
        s = 1 - i * 0.14
        hh = h / steps
        box(f"Plinth{i}", (w * s, d * s, hh), (0, 0, z + hh / 2), K["plinth"], bevel=0.03, segments=3)
        z += hh
    box("PlinthCap", (w * (1 - steps * 0.14) - 0.04, d * (1 - steps * 0.14) - 0.04, 0.04), (0, 0, z + 0.02), K["gilt"], bevel=0.012)
    pw = w * 0.55
    box("NamePlate", (pw, 0.02, h / steps * 0.55), (0, -d / 2 - 0.005, h / steps * 0.5), K["gilt"], bevel=0.008)
    for sx in (-1, 1):
        cyl(f"Screw{sx}", 0.018, 0.02, (sx * (pw / 2 - 0.05), -d / 2 - 0.02, h / steps * 0.5), K["giltdk"], rot=(PI / 2, 0, 0), verts=10)
    return z + 0.04


def club_cup(M):
    K = tk(M)
    top = plinth(K, 0.95, 0.95, 0.42)
    # foot, stem knop, fluted bowl, lip
    lathe("CupFoot", [(0.0, 0), (0.34, 0), (0.34, 0.03), (0.3, 0.06), (0.16, 0.12), (0.09, 0.2), (0.0, 0.2)], K["gilt"], seg=48, loc=(0, 0, top))
    lathe("CupKnop", [(0.0, 0), (0.09, 0), (0.15, 0.06), (0.09, 0.12), (0.07, 0.2), (0.0, 0.2)], K["gilt"], seg=40, loc=(0, 0, top + 0.18))
    bowl = [(0.0, 0.0), (0.12, 0.0), (0.3, 0.08), (0.42, 0.26), (0.46, 0.5), (0.47, 0.66), (0.5, 0.7), (0.47, 0.72), (0.43, 0.68), (0.0, 0.68)]
    lathe("CupBowl", bowl, K["gilt"], seg=64, loc=(0, 0, top + 0.36), flute=(24, 0.035))
    lathe("CupBand", [(0.0, 0), (0.465, 0), (0.47, 0.03), (0.47, 0.09), (0.465, 0.12), (0.0, 0.12)], K["enamel"], seg=64, loc=(0, 0, top + 0.78))
    hoop("BandRimLo", (0, 0, top + 0.78), 0.47, "Z", K["gilt"], thick=0.014)
    hoop("BandRimHi", (0, 0, top + 0.9), 0.47, "Z", K["gilt"], thick=0.014)
    # ear handles: a C from the band down to the bowl's waist, with a curl at the foot of each
    for sx in (-1, 1):
        pts = []
        for i in range(13):
            ang = math.radians(100 - i * 200 / 12)
            pts.append((sx * (0.46 + 0.2 * math.cos(ang)), 0, top + 0.72 + 0.2 * math.sin(ang)))
        tube(f"Handle{sx}", pts, 0.034, K["gilt"], poly=True)
        lathe(f"HandleCurl{sx}", [(0.0, 0), (0.05, 0), (0.06, 0.03), (0.0, 0.06)], K["gilt"], seg=16, loc=(sx * 0.43, 0, top + 0.5))
    # the lid and its flame finial
    lid = top + 1.06
    lathe("Lid", [(0.0, 0), (0.48, 0), (0.48, 0.03), (0.36, 0.08), (0.14, 0.16), (0.06, 0.2), (0.0, 0.2)], K["gilt"], seg=56, loc=(0, 0, lid))
    lathe("Finial", [(0.0, 0), (0.05, 0), (0.09, 0.06), (0.07, 0.14), (0.03, 0.22), (0.0, 0.28)], K["enamel"], seg=24, loc=(0, 0, lid + 0.2))
    return _dims()


def honour_roll_plaque(M):
    K = tk(M)
    # a heater shield, standing on a small oak foot
    box("Foot", (0.9, 0.42, 0.12), (0, 0.02, 0.06), K["plinth"], bevel=0.03, segments=3)
    shield = [(-0.52, 1.5), (0.52, 1.5), (0.52, 0.8)]
    for i in range(1, 12):
        t = i / 11
        shield.append((0.52 * (1 - t) ** 0.9 * math.cos(t * 0.6), 0.8 - t * 0.66))
    shield += [(-x, z) for x, z in reversed(shield[2:-1])]  # the left side, without repeating the tip
    prism("Shield", shield, 0.04, 0.12, K["oak"], plane="XZ", bevel=0.025)
    inner = [(x * 0.84, 0.16 + (z - 0.16) * 0.9 + 0.04) for x, z in shield]
    prism("ShieldPanel", inner, -0.03, 0.03, K["oakdark"], plane="XZ", bevel=0.01)
    # a gilt laurel wreath: two curving sprays of pointed leaves on a stem, round an open book
    cx, cz, R = 0.0, 0.9, 0.33
    for side in (-1, 1):
        stem = []
        for i in range(12):
            a = math.radians(-70 + i * 12.5)          # from the bottom up round each side
            stem.append((side * R * math.cos(a), -0.075, cz + R * math.sin(a)))
        tube(f"Stem{side}", stem, 0.012, K["gilt"], res=6)
        for i in range(11):
            a = math.radians(-64 + i * 12.5)
            px, pz = side * R * math.cos(a), cz + R * math.sin(a)
            for k, out in ((0, 1), (1, -1)):        # a pair of leaves, one either side of the stem
                tx, tz = -side * math.sin(a), math.cos(a)       # the stem's direction (up the arc)
                nx, nz = side * math.cos(a) * out, math.sin(a) * out  # out from (or into) the ring
                dx, dz = tx * 0.6 + nx * 0.8, tz * 0.6 + nz * 0.8
                L = math.hypot(dx, dz)
                dx, dz = dx / L, dz / L
                ln, wd = 0.085 - i * 0.003, 0.028
                leaf = []
                for t in range(9):
                    u = t / 8
                    w = wd * math.sin(u * PI)
                    leaf.append((px + dx * ln * u - dz * w, pz + dz * ln * u + dx * w))
                for t in range(7, 0, -1):
                    u = t / 8
                    w = wd * math.sin(u * PI)
                    leaf.append((px + dx * ln * u + dz * w, pz + dz * ln * u - dx * w))
                prism(f"Leaf{side}_{i}_{k}", leaf, -0.078, 0.022, K["gilt"], plane="XZ", bevel=0.006)
    # the open book: two gently raised page blocks with a cover lip and a spine
    for sx in (-1, 1):
        page = [(sx * 0.015, 0.8), (sx * 0.12, 0.79), (sx * 0.22, 0.77), (sx * 0.22, 1.0), (sx * 0.12, 1.02), (sx * 0.015, 1.04)]
        if sx < 0:
            page = list(reversed(page))
        prism(f"Cover{sx}", [(x + sx * 0.012, z - 0.012) for x, z in page], -0.06, 0.03, K["giltdk"], plane="XZ", bevel=0.006)
        prism(f"Pages{sx}", page, -0.085, 0.03, K["gilt"], plane="XZ", bevel=0.01)
    box("Spine", (0.02, 0.03, 0.25), (0, -0.09, 0.915), K["giltdk"], bevel=0.005)
    # a scroll banner across the bottom, rolled at both ends
    box("Scroll", (0.74, 0.03, 0.14), (0, -0.07, 0.48), K["gilt"], bevel=0.01)
    for sx in (-1, 1):
        cyl(f"ScrollEnd{sx}", 0.05, 0.16, (sx * 0.38, -0.07, 0.48), K["giltdk"], verts=16)
    # the crimson ribbon and tassel from the top
    tube("RibbonL", [(-0.08, -0.05, 1.5), (-0.14, -0.08, 1.38), (-0.12, -0.08, 1.24)], 0.03, K["ribbon"], square=True)
    tube("RibbonR", [(0.08, -0.05, 1.5), (0.13, -0.08, 1.36), (0.16, -0.08, 1.2)], 0.03, K["ribbon"], square=True)
    lathe("Tassel", [(0.0, 0), (0.04, 0.02), (0.05, 0.12), (0.03, 0.16), (0.0, 0.17)], K["ribbon"], seg=16, loc=(0, -0.07, 1.48))
    cyl("Hook", 0.035, 0.05, (0, -0.06, 1.55), K["gilt"], rot=(PI / 2, 0, 0), verts=12)
    return _dims()


def ring_belt(M):
    """The belt shown as champions' belts are: flat to the front on a display stand, the strap tooled black leather with a
    gilt edge, a big gilt centre plate (a crimson cabochon, two raised fists, a laurel rim), two side plates, studs."""
    K = tk(M)
    # the stand: an oak base, two iron posts with cradles behind the belt
    box("Base", (1.9, 0.5, 0.12), (0, 0.06, 0.06), K["plinth"], bevel=0.035, segments=3)
    box("BasePlate", (0.5, 0.02, 0.07), (0, -0.19, 0.06), K["gilt"], bevel=0.006)
    for sx in (-1, 1):
        box(f"Post{sx}", (0.05, 0.05, 0.86), (sx * 0.62, 0.12, 0.55), K["iron"], bevel=0.012)
        tube(f"Cradle{sx}", [(sx * 0.62, 0.12, 0.66), (sx * 0.62, 0.05, 0.64), (sx * 0.62, 0.02, 0.7)], 0.02, K["iron"], res=6)
    # the strap: a long band, its ends tapering, curved gently back toward the stand
    def band(w_half, h_half, zc, y, depth, mat, name, taper=0.7):
        poly = []
        n = 24
        for t in range(n + 1):
            x = -w_half + 2 * w_half * t / n
            h = h_half * (taper + (1 - taper) * math.cos(x / w_half * PI / 2) ** 0.4)
            poly.append((x, zc + h))
        for t in range(n, -1, -1):
            x = -w_half + 2 * w_half * t / n
            h = h_half * (taper + (1 - taper) * math.cos(x / w_half * PI / 2) ** 0.4)
            poly.append((x, zc - h))
        ob = prism(name, poly, y, depth, mat, plane="XZ", bevel=0.012)
        md = ob.modifiers.new("Bend", "SIMPLE_DEFORM")
        md.deform_method = "BEND"
        md.deform_axis = "Z"
        md.angle = math.radians(-28)
        return ob
    band(0.95, 0.2, 0.88, 0.0, 0.05, K["belt"], "Strap")
    band(0.95, 0.205, 0.88, 0.012, 0.035, K["giltdk"], "StrapEdge", taper=0.7)
    for i, x in enumerate([-0.84, -0.72, -0.34, -0.26, 0.26, 0.34, 0.72, 0.84]):
        for zz in (0.76, 1.0):
            st = lathe(f"Stud{i}_{zz}", [(0.0, 0), (0.022, 0), (0.02, 0.012), (0.0, 0.02)], K["gilt"], seg=12)
            st.rotation_euler = (PI / 2, 0, 0)
            st.location = (x, -0.03 - 0.02 * (x / 0.95) ** 2, zz)
    # the centre plate: a scalloped gilt oval, a laurel rim, a darker field, a crimson cabochon and two raised fists
    plate = []
    for i in range(72):
        a = i / 72 * 2 * PI
        r = 1 + 0.035 * math.cos(a * 18)
        plate.append((0.4 * r * math.cos(a), 0.88 + 0.3 * r * math.sin(a)))
    prism("CentrePlate", plate, -0.06, 0.05, K["gilt"], plane="XZ", bevel=0.02)
    field = [(0.31 * math.cos(a), 0.88 + 0.22 * math.sin(a)) for a in [i / 48 * 2 * PI for i in range(48)]]
    prism("PlateField", field, -0.088, 0.016, K["giltdk"], plane="XZ", bevel=0.006)
    for i in range(20):
        a = i / 20 * 2 * PI
        lx, lz = 0.355 * math.cos(a), 0.88 + 0.26 * math.sin(a)
        leaf = [(lx + 0.03 * math.cos(a + k / 6 * 2 * PI) * (1.4 if k % 3 == 0 else 0.7), lz + 0.02 * math.sin(a + k / 6 * 2 * PI) * (1.4 if k % 3 == 0 else 0.7)) for k in range(6)]
        prism(f"RimLeaf{i}", leaf, -0.09, 0.014, K["gilt"], plane="XZ", bevel=0.004)
    cab = lathe("Cabochon", [(0.0, 0), (0.08, 0), (0.078, 0.025), (0.05, 0.055), (0.0, 0.068)], K["enamel"], seg=32)
    cab.rotation_euler = (PI / 2, 0, 0)
    cab.location = (0, -0.095, 0.9)
    setting = hoop("Setting", (0, -0.1, 0.9), 0.085, "Y", K["gilt"], thick=0.012)
    for sx in (-1, 1):
        cx = sx * 0.19
        for k in range(4):
            box(f"Knuckle{sx}_{k}", (0.038, 0.03, 0.05), (cx + (k - 1.5) * 0.04, -0.1, 0.96), K["gilt"], bevel=0.012)
        box(f"Fist{sx}", (0.16, 0.03, 0.08), (cx, -0.1, 0.9), K["gilt"], bevel=0.016)
        box(f"Thumb{sx}", (0.05, 0.03, 0.03), (cx - sx * 0.06, -0.11, 0.87), K["gilt"], bevel=0.01)
    # side plates: gilt shields with a small crimson stone
    for sx in (-1, 1):
        cx = sx * 0.55
        shield = [(cx - 0.11, 1.0), (cx + 0.11, 1.0), (cx + 0.11, 0.86), (cx, 0.74), (cx - 0.11, 0.86)]
        prism(f"SidePlate{sx}", shield, -0.045 - 0.02 * (cx / 0.95) ** 2, 0.04, K["gilt"], plane="XZ", bevel=0.014)
        gem = lathe(f"SideGem{sx}", [(0.0, 0), (0.035, 0), (0.03, 0.018), (0.0, 0.03)], K["enamel"], seg=20)
        gem.rotation_euler = (PI / 2, 0, 0)
        gem.location = (cx, -0.075 - 0.02 * (cx / 0.95) ** 2, 0.89)
    return _dims()


def _place(start: int, mat4):
    """Move every part built since P.PARTS[start] by one transform (build flat at the origin, then set in place)."""
    bpy.context.view_layer.update()
    for ob in P.PARTS[start:]:
        ob.matrix_world = mat4 @ ob.matrix_world


def the_register(M):
    """The school register, open, on an oak lectern: a black leather ledger with gilt corner guards and a clasp, pages
    gently bowed, a crimson bookmark hanging over the front; a pewter inkwell and a quill on the lectern's ledge."""
    from mathutils import Matrix
    K = tk(M)
    top = plinth(K, 0.92, 0.76, 0.16, steps=1)
    lathe("Column", [(0.0, 0.0), (0.12, 0.0), (0.1, 0.06), (0.07, 0.14), (0.06, 0.46), (0.08, 0.52), (0.11, 0.56), (0.0, 0.56)], K["oak"], seg=32, loc=(0, 0, top))
    deck = top + 0.56
    box("Bracket", (0.5, 0.36, 0.05), (0, 0, deck + 0.025), K["oakdark"], bevel=0.015)
    # the sloped desk and everything on it, built flat (its top at z = 0, front edge toward -Y), then tilted 22 degrees
    start = len(P.PARTS)
    box("Desk", (0.96, 0.7, 0.05), (0, 0, -0.025), K["oak"], bevel=0.018, segments=3)
    box("Ledge", (0.96, 0.06, 0.07), (0, -0.37, 0.01), K["oakdark"], bevel=0.012)
    box("Cover", (0.84, 0.6, 0.035), (0, 0.02, 0.0175), K["belt"], bevel=0.012)
    for sx in (-1, 1):
        pg = box(f"Pages{sx}", (0.38, 0.54, 0.06), (sx * 0.2, 0.02, 0.065), K["paper"], bevel=0.025, segments=4)
        md = pg.modifiers.new("Bow", "SIMPLE_DEFORM")
        md.deform_method = "BEND"
        md.deform_axis = "Y"
        md.angle = math.radians(14 * sx)
        # a few ruled lines and the struck-through name on the right page
        if sx > 0:
            for k in range(6):
                box(f"Rule{k}", (0.28, 0.006, 0.002), (0.2, -0.17 + k * 0.07, 0.097), K["glass"], bevel=0)
            box("Strike", (0.2, 0.012, 0.003), (0.18, 0.04, 0.099), K["enamel"], bevel=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tri = [(sx * 0.42, sy * 0.32), (sx * 0.42 - sx * 0.1, sy * 0.32), (sx * 0.42, sy * 0.32 - sy * 0.1)]
            ob = prism(f"Guard{sx}{sy}", tri, 0.03, 0.025, K["gilt"], plane="XY", bevel=0.006)
    box("ClaspStrap", (0.1, 0.07, 0.02), (0.46, 0.02, 0.03), K["belt"], bevel=0.008)
    box("Clasp", (0.05, 0.08, 0.035), (0.5, 0.02, 0.03), K["gilt"], bevel=0.01)
    tube("Bookmark", [(0.0, 0.0, 0.1), (0.01, -0.2, 0.105), (0.02, -0.3, 0.08), (0.03, -0.36, 0.0), (0.04, -0.37, -0.14)], 0.016, K["ribbon"], square=True)
    lathe("Inkwell", [(0.0, 0), (0.06, 0), (0.065, 0.03), (0.05, 0.065), (0.025, 0.08), (0.0, 0.08)], K["pewter"], seg=24, loc=(-0.38, -0.37, 0.045))
    tube("QuillShaft", [(-0.38, -0.37, 0.1), (-0.33, -0.33, 0.24), (-0.27, -0.29, 0.4)], 0.008, K["chalk"], res=8)
    vane = []
    for t in range(13):
        u = t / 12
        vane.append((u * 0.24, 0.035 * math.sin(u * PI) ** 0.7))
    for t in range(12, -1, -1):
        u = t / 12
        vane.append((u * 0.24, -0.02 * math.sin(u * PI) ** 0.8))
    v = prism("QuillVane", vane, 0.0, 0.004, K["chalk"], plane="XZ")
    v.matrix_world = Matrix.Translation((-0.33, -0.33, 0.2)) @ Matrix.Rotation(math.radians(58), 4, "Y") @ Matrix.Rotation(math.radians(-38), 4, "Z") @ v.matrix_world
    _place(start, Matrix.Translation((0, 0, deck + 0.13)) @ Matrix.Rotation(math.radians(22), 4, "X"))
    return _dims()


EMBLEMS = {
    "Academic": [[(-0.17, -0.06), (-0.01, -0.03), (-0.01, 0.11), (-0.17, 0.08)], [(0.01, -0.03), (0.17, -0.06), (0.17, 0.08), (0.01, 0.11)]],
    "Social": "figures",
    "Combat": [[(-0.13, -0.12), (0.13, -0.12), (0.14, 0.02), (-0.14, 0.02)], [(-0.13, 0.02), (-0.07, 0.02), (-0.07, 0.12), (-0.13, 0.12)],
               [(-0.065, 0.02), (-0.005, 0.02), (-0.005, 0.13), (-0.065, 0.13)], [(0.0, 0.02), (0.06, 0.02), (0.06, 0.13), (0.0, 0.13)],
               [(0.065, 0.02), (0.125, 0.02), (0.125, 0.11), (0.065, 0.11)]],
    "Athletic": [[(-0.12, -0.14), (-0.09, -0.14), (-0.09, 0.14), (-0.12, 0.14)], [(-0.09, 0.13), (0.14, 0.06), (-0.09, -0.01)]],
    "Supernatural": "moon",
}


def path_medal(M, path):
    K = tk(M)
    box("Base", (0.7, 0.42, 0.1), (0, 0, 0.05), K["plinth"], bevel=0.03, segments=3)
    box("BasePlate", (0.36, 0.02, 0.06), (0, -0.215, 0.05), K["gilt"], bevel=0.006)
    # an iron gallows stand
    box("Post", (0.05, 0.05, 1.2), (0.26, 0.06, 0.7), K["iron"], bevel=0.012)
    tube("Arm", [(0.26, 0.06, 1.28), (0.1, 0.06, 1.32), (-0.02, 0.06, 1.3)], 0.022, K["iron"], res=6)
    lathe("PostCap", [(0.0, 0), (0.04, 0), (0.05, 0.03), (0.0, 0.07)], K["gilt"], seg=16, loc=(0.26, 0.06, 1.3))
    # the ribbon: a black-and-crimson V from the hook to the medal's ring
    for sx in (-1, 1):
        tube(f"Ribbon{sx}", [(0.0, 0.04, 1.28), (sx * 0.05, 0.02, 1.1), (sx * 0.07, 0.0, 0.96)], 0.04, K["ribbon"] if sx < 0 else K["ribbonblk"], square=True)
    hoop("Ring", (0, -0.01, 0.93), 0.035, "Y", K["gilt"], thick=0.01)
    # the medal: a gilt disc, a crimson enamel ring, a raised rim, the path's emblem in relief
    cz = 0.68
    disc = [(0.24 * math.cos(a), cz + 0.24 * math.sin(a)) for a in [i / 48 * 2 * PI for i in range(48)]]
    prism("Disc", disc, -0.01, 0.05, K["gilt"], plane="XZ", bevel=0.02)
    ring = [(0.2 * math.cos(a), cz + 0.2 * math.sin(a)) for a in [i / 48 * 2 * PI for i in range(48)]]
    prism("Enamel", ring, -0.04, 0.012, K["enamel"], plane="XZ", bevel=0.004)
    field = [(0.165 * math.cos(a), cz + 0.165 * math.sin(a)) for a in [i / 48 * 2 * PI for i in range(48)]]
    prism("Field", field, -0.048, 0.012, K["gilt"], plane="XZ", bevel=0.004)
    E = EMBLEMS[path]
    if E == "figures":
        for sx in (-1, 1):
            head = [(sx * 0.06 + 0.035 * math.cos(a), cz + 0.05 + 0.035 * math.sin(a)) for a in [i / 20 * 2 * PI for i in range(20)]]
            prism(f"Head{sx}", head, -0.06, 0.016, K["giltdk"], plane="XZ", bevel=0.004)
            body = [(sx * 0.06 + 0.06 * math.cos(a), cz - 0.06 + 0.06 * math.sin(a)) for a in [i / 20 * PI for i in range(21)]]
            prism(f"Body{sx}", body, -0.06, 0.016, K["giltdk"], plane="XZ", bevel=0.004)
    elif E == "moon":
        moon = []
        for i in range(25):
            a = PI * 0.33 + i / 24 * PI * 1.34
            moon.append((0.12 * math.cos(a), cz + 0.12 * math.sin(a)))
        for i in range(25):
            a = PI * 1.62 - i / 24 * PI * 1.24
            moon.append((0.065 + 0.095 * math.cos(a), cz + 0.025 + 0.095 * math.sin(a)))
        prism("Moon", moon, -0.06, 0.016, K["giltdk"], plane="XZ", bevel=0.004)
        star = []
        for i in range(8):
            r = 0.04 if i % 2 == 0 else 0.016
            a = i / 8 * 2 * PI
            star.append((0.07 + r * math.cos(a), cz - 0.06 + r * math.sin(a)))
        prism("Star", star, -0.06, 0.016, K["giltdk"], plane="XZ", bevel=0.003)
    else:
        for i, poly in enumerate(E):
            prism(f"Emblem{i}", [(x, cz + z) for x, z in poly], -0.06, 0.016, K["giltdk"], plane="XZ", bevel=0.004)
    return _dims()


BUILDERS = {
    "ClubCup": club_cup,
    "HonourRollPlaque": honour_roll_plaque,
    "RingBelt": ring_belt,
    "TheRegister": the_register,
}
for _p in ("Academic", "Social", "Combat", "Athletic", "Supernatural"):
    BUILDERS[f"PathMedal{_p}"] = (lambda p: (lambda M: path_medal(M, p)))(_p)
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.15 for n in BUILDERS})

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    names = list(BUILDERS) if (not argv or argv[0] == "all") else [argv[0]]
    for n in names:
        P.run(n)
