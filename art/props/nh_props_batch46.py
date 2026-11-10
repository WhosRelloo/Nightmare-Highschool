"""Props batch 46, the shops kit (2026-11-10), for nh_props.py: homes phase 2's two shared shop interiors in the gothic town,
the ARMORY (a monster-hunters' outfitter for the Vigil: katana, fist and claw gear, silver and ash against the undead) and the
SPELL SHOP (a moonlit hex shop: grimoires, potions, crystals and runes, the one place here where things glow). The armory is
iron, steel, silver, leather and crimson; the spell shop is night-violet enamel, brass, black marble, velvet and glow. Every
name, motto and design is invented.

Armory (NHBuildKit "Armory")
    KatanaStand, PolearmRack, PlateArmourStand, MailHauberkStand, ShieldWall (wall), Grindstone, ArmoryCounter,
    SilverDaggerCase (Glass), HelmShelf (wall), BoltBarrel, BeastPell, CrossbowRack (wall), HuntersReliquary (Glass),
    ArmorySign (wall), ClawGauntletDisplay (plinth)
Spell shop (NHBuildKit "SpellShop")
    TetheredGrimoires (Glow), PotionHoneycomb (wall; Glow, Glow2), ScryingOrbStand (Glass, Glow), WandCoffin (Glass, Glow),
    RuneStoneTable (Glow), ScrollCarousel (Glow), WaxfallAltar (Glow), OrreryCounter (Glow), StarChartBanner (wall; Glow),
    HangingCrystals (ceiling; Glow, Glow2), FamiliarPerch (Glow), RuneCircleRug (Glow), OddmentsEtagere (Glass, Glow),
    SpellShopSign (wall; Glow)

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back on y = 0. The house crests come
from batch 43's GymPrint atlas (baked into each prop's maps, not uploaded). Registered into nh_props.BUILD on import.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material, _quatrefoil
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import lathe, hoop, strip, prism, _mark, _xform, _dims, flat
import nh_props_batch24 as B24
import nh_props_batch4 as B4
import nh_props_batch30 as B30
import nh_props_batch43 as B43

DEG = math.pi / 180
PI = math.pi
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
_tube = P.tube


def tube(name, points, radius, mat, closed=False, res=4, square=False, poly=False):
    """nh_props.tube, but a square bar's faces are turned outward (as built its normals point in: the bake's AO darkens it
    and Roblox would cull its outside). The same fix as batch 45's."""
    ob = _tube(name, points, radius, mat, closed=closed, res=res, square=square, poly=poly)
    if square:
        ob.data.flip_normals()
    return ob

FONT = B43.FONT
FONT_I = B43.FONT_I
circ, pprism, crest, label, rivet, finial, arch_xz, chain, rect = (B43.circ, B43.pprism, B43.crest, B43.label, B43.rivet,
                                                                  B43.finial, B43.arch_xz, B43.chain, B43.rect)
# the school crest's shield inside its dark square on the GymPrint atlas
_u0, _v0, _u1, _v1 = B30.REG["GY_School_Crest"]
B30.REG["SH_SchoolShield"] = [_u0 + (_u1 - _u0) * 0.12, _v0 + (_v1 - _v0) * 0.1, _u0 + (_u1 - _u0) * 0.88, _v0 + (_v1 - _v0) * 0.9]
HOUSES = ("Crimson", "Ravens", "Rovers", "Vigil", "Wardens")

GLOW = {}       # prop -> {"Glow": (r, g, b), "Glow2": ...} in 0-255, the Neon colours (preview and docs)
CAM = {}        # prop -> camera elevation factor (default 0.22)


# ------------------------------------------------------------------ materials

def mail_mat(name, rgb, scale=26.0):
    """Riveted mail: a metal with a ring-dimple bump (Voronoi cells) and dark crevices."""
    m = material(name, base=rgb, rough=0.38, metal=1.0, wear=0.15, dirt=1.0)
    nt = m.node_tree
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = "DISTANCE_TO_EDGE"
    v.inputs["Scale"].default_value = scale
    nt.links.new(B24._coords(nt), v.inputs["Vector"])
    B24._bump(m, v.outputs["Distance"], 0.012)
    return m


def kit(M):
    K = B43.kit(M)
    K.update({
        "blade": material("BladeSteel", base=(0.8, 0.81, 0.84), rough=0.14, metal=1.0, wear=0.12, dirt=0.35),
        "plate": material("PlateSteel", base=(0.56, 0.57, 0.6), rough=0.26, metal=1.0, wear=0.25, dirt=0.9),
        "gun": material("Gunmetal", "NH_Iron", tint=(0.2, 0.2, 0.22), scale=1.4, rough_add=0.0, wear=0.45, wear_metal=True, dirt=0.85),
        "mail": mail_mat("SilverMail", (0.6, 0.6, 0.62), scale=42.0),
        "crimson": material("ArmoryEnamel", base=(0.19, 0.01, 0.02), rough=0.32, metal=0.0, wear=0.2, dirt=0.6),
        "saya": flat("SayaLacquer", (0.012, 0.01, 0.012), 0.18, wear=0.15),
        "sayared": material("SayaCrimson", base=(0.2, 0.012, 0.02), rough=0.2, wear=0.2, dirt=0.4),
        "wrap": B24.cloth("TsukaWrap", (0.17, 0.012, 0.02), rough=0.7, weave=0.01),
        "ray": flat("Rayskin", (0.78, 0.74, 0.64), 0.6, dirt=0.6),
        "ash": material("AshWood", "NH_DeskWood", tint=(0.5, 0.38, 0.26), scale=0.7, rough_add=0.05, wear=0.2),
        "grit": material("GrindGrit", "NH_Limestone", tint=(0.6, 0.5, 0.36), scale=1.6, rough_add=0.3, wear=0.1, dirt=0.8),
        "garlic": flat("Garlic", (0.82, 0.78, 0.68), 0.7, dirt=0.6),
        "bane": flat("Wolfsbane", (0.2, 0.1, 0.42), 0.6),
        "stem": flat("BaneStem", (0.1, 0.16, 0.06), 0.7),
        "quilt": B24.cloth("Gambeson", (0.16, 0.014, 0.022), rough=0.9, weave=0.02),
        "hide": B24.leather("PellHide", (0.11, 0.055, 0.03), scale=3.0, wear=0.35),
        "horse": flat("Horsehair", (0.2, 0.012, 0.02), 0.85),
        "water": material("TroughWater", base=(0.03, 0.04, 0.045), rough=0.05, wear=0.0, dirt=0.0),
        # spell shop
        "night": material("NightEnamel", "NH_PaintedMetal", tint=(0.05, 0.03, 0.11), scale=1.3, wear=0.45, wear_metal=True),
        "plum": B24.cloth("PlumVelvet", (0.07, 0.015, 0.1), rough=0.95, weave=0.004),
        "indigo": B24.cloth("IndigoCloth", (0.018, 0.02, 0.07), rough=0.92, weave=0.006),
        "rugwool": B24.wool("RuneRugWool", (0.05, 0.018, 0.08)),
        "rugedge": B24.wool("RuneRugEdge", (0.16, 0.012, 0.03)),
        "quartz": flat("Quartz", (0.5, 0.46, 0.66), 0.12),
        "bronze": material("Bronze", "NH_Brass", tint=(0.6, 0.42, 0.28), scale=1.0, wear=0.4, dirt=0.9),
        "feather": material("OwlFeather", "NH_Leather", tint=(0.36, 0.25, 0.15), scale=7.0, normal=0.4, wear=0.0, dirt=0.6),
        "featherlt": material("OwlBreast", "NH_Leather", tint=(0.66, 0.55, 0.4), scale=9.0, normal=0.4, wear=0.0, dirt=0.6),
        "beak": flat("Beak", (0.09, 0.08, 0.07), 0.4),
        "parch": material("Parchment", "NH_Paper", tint=(0.86, 0.76, 0.58), scale=0.8, wear=0.1, dirt=0.8),
        "g_violet": flat("GlowViolet", (0.55, 0.32, 1.0), 0.4),
        "g_teal": flat("GlowTeal", (0.3, 0.88, 0.84), 0.4),
        "g_green": flat("GlowGreen", (0.55, 1.0, 0.4), 0.4),
        "g_amber": flat("GlowAmber", (1.0, 0.68, 0.3), 0.4),
        "g_pale": flat("GlowPale", (0.78, 0.84, 1.0), 0.4),
    })
    return K


# ------------------------------------------------------------------ shared pieces

def yz_text(name, text, mat, x, yc, zc, w, h, side=1, depth=0.01, font=FONT, res=1):
    """Raised lettering on a face looking to side * X at plane x, centred at (yc, zc), fitted into w x h."""
    if side > 0:
        return B24._text(name, text, font, mat, lambda u, v, hh: (x + hh, yc + u, zc + v), fit=(w, h), depth=depth, res=res)
    return B24._text(name, text, font, mat, lambda u, v, hh: (x - hh, yc - u, zc + v), fit=(w, h), depth=depth, res=res)


def prof_r(prof, z):
    """The radius of a lathe profile [(r, z), ...] (going up) at height z, linearly interpolated."""
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1 and z1 > z0:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return prof[-1][0]


def kat_z(x, L, sori=0.1):
    t = max(0.0, (x - 0.84) / (L - 0.84))
    return sori * t * t


def katana(prefix, mtx, K, L=3.0, drawn=0.0, saya=None, sheath=True):
    """A katana along +X from the butt of its handle at the origin: crimson-wrapped tsuka with rayskin diamonds, gilt fittings,
    an iron tsuba, a curved steel blade, and (sheath) a lacquered saya drawn back `drawn` from the guard, with its cord."""
    s = _mark()
    wrap, br, ir = K["wrap"], K["gilt"], K["iron"]
    cyl(f"{prefix}Tsuka", 0.05, 0.76, (0.4, 0, 0), wrap, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
    for i in range(6):
        for sy in (-1, 1):
            box(f"{prefix}Dia{i}{sy}", (0.045, 0.012, 0.045), (0.1 + i * 0.12, sy * 0.046, 0), K["ray"], bevel=0.0, rot=(0, PI / 4, 0))
    cyl(f"{prefix}Kashira", 0.056, 0.05, (0.0, 0, 0), br, rot=(0, PI / 2, 0), verts=12, bevel=0.008)
    cyl(f"{prefix}Fuchi", 0.056, 0.04, (0.78, 0, 0), br, rot=(0, PI / 2, 0), verts=12, bevel=0.006)
    tb = cyl(f"{prefix}Tsuba", 0.15, 0.025, (0.815, 0, 0), ir, rot=(0, PI / 2, 0), verts=16, bevel=0.006)
    tb.scale = (1, 0.8, 1)
    box(f"{prefix}Habaki", (0.06, 0.03, 0.075), (0.855, 0, 0.004), br, bevel=0.005)
    n = 14
    back, edge = [], []
    for i in range(n + 1):
        t = i / n
        x = 0.84 + (L - 0.84) * t
        c = kat_z(x, L)
        back.append((x, c + 0.032))
        edge.append((x, c - 0.034 + 0.01 * t))
    tip = (L + 0.1, kat_z(L, L) + 0.03)
    prism(f"{prefix}Blade", edge + [tip] + list(reversed(back)), 0, 0.016, K["blade"], plane="XZ")
    if sheath:
        sm = saya or K["saya"]
        xs, xe = 0.86 + drawn, L + 0.12 + drawn
        pts = [(xs + (xe - xs) * i / 10, 0, kat_z(xs + (xe - xs) * i / 10 - drawn, L)) for i in range(11)]
        tube(f"{prefix}Saya", pts, 0.058, sm, res=6)
        cyl(f"{prefix}Koiguchi", 0.064, 0.05, (xs + 0.02, 0, pts[0][2]), K["bone"], rot=(0, PI / 2, 0), verts=12, bevel=0.006)
        cyl(f"{prefix}Kojiri", 0.062, 0.08, (xe - 0.02, 0, pts[-1][2]), br, rot=(0, PI / 2, 0), verts=12, bevel=0.01)
        box(f"{prefix}Kurikata", (0.08, 0.04, 0.05), (xs + 0.3, 0, pts[1][2] - 0.065), sm, bevel=0.01)
        z0 = pts[1][2] - 0.08
        tube(f"{prefix}Sageo", [(xs + 0.3, -0.01, z0), (xs + 0.42, -0.03, z0 - 0.16), (xs + 0.62, -0.02, z0 - 0.06),
                                (xs + 0.85, -0.03, z0 - 0.2), (xs + 1.1, -0.02, z0 - 0.08)], 0.016, K["wrap"], res=6)
    _xform(s, mtx)


def dagger(prefix, mtx, K, L=0.9, silver=True):
    """A double-edged silver dagger along +X from its pommel at the origin, lying flat (blade in the XY plane)."""
    s = _mark()
    bl = K["silver"] if silver else K["blade"]
    sphere(f"{prefix}Pommel", 0.035, (0, 0, 0), K["gilt"], seg=10, rings=6)
    cyl(f"{prefix}Grip", 0.024, 0.24, (0.15, 0, 0), K["leather"], rot=(0, PI / 2, 0), verts=8, bevel=0.0)
    box(f"{prefix}Guard", (0.04, 0.22, 0.03), (0.29, 0, 0), K["gilt"], bevel=0.008)
    for sy in (-1, 1):
        sphere(f"{prefix}GuardEnd{sy}", 0.022, (0.29, sy * 0.11, 0), K["gilt"], seg=8, rings=4)
    poly = [(0.31, -0.045), (0.31 + L * 0.7, -0.032), (0.31 + L, 0.0), (0.31 + L * 0.7, 0.032), (0.31, 0.045)]
    prism(f"{prefix}Blade", poly, 0, 0.014, bl, plane="XY")
    box(f"{prefix}Fuller", (L * 0.6, 0.012, 0.016), (0.31 + L * 0.32, 0, 0.0), K["ink"], bevel=0.0)
    _xform(s, mtx)


def stake(prefix, mtx, K, L=1.1):
    """An ash stake along +X, point at the far end, a silver cap and an iron ring at the butt."""
    s = _mark()
    lathe(f"{prefix}Wood", [(0, 0), (0.045, 0), (0.05, 0.1), (0.046, L * 0.62), (0.02, L * 0.92), (0, L)], K["ash"], seg=8)
    lathe(f"{prefix}Cap", [(0, -0.05), (0.052, -0.05), (0.056, 0.03), (0.052, 0.06), (0, 0.06)], K["silver"], seg=10)
    for ob in P.PARTS[s:]:
        ob.matrix_world = RY(PI / 2) @ ob.matrix_world
    _xform(s, mtx)


def bolt(prefix, mtx, K, L=1.0, fl=None, head=None):
    """A crossbow bolt along +Z from its point at the origin, the fletching at the top."""
    s = _mark()
    cone(f"{prefix}Head", 0.035, 0.0, 0.12, (0, 0, 0.06), head or K["silver"], verts=6, rot=(PI, 0, 0))
    cyl(f"{prefix}Shaft", 0.016, L, (0, 0, L / 2 + 0.1), K["ash"], verts=6, bevel=0.0)
    for k in range(3):
        f = prism(f"{prefix}Fl{k}", [(0.012, L - 0.22), (0.075, L - 0.16), (0.07, L + 0.02), (0.012, L + 0.04)], 0, 0.005,
                  fl or K["leather"] if k else K["bone"], plane="XZ")
        f.matrix_world = RZ(k * 2 * PI / 3) @ f.matrix_world
    _xform(s, mtx)


def tripod(prefix, r, K, mat=None, h=0.5):
    """Three curled cast-iron feet round a hub at the origin."""
    m = mat or K["iron"]
    cyl(f"{prefix}Hub", 0.16, h, (0, 0, h / 2 + 0.1), m, verts=12, bevel=0.02)
    for k in range(3):
        a = PI / 2 + k * 2 * PI / 3 + PI / 3
        c, s_ = math.cos(a), math.sin(a)
        tube(f"{prefix}Leg{k}", [(c * 0.1, s_ * 0.1, h + 0.05), (c * r * 0.5, s_ * r * 0.5, h * 0.5), (c * r * 0.9, s_ * r * 0.9, 0.1),
                                 (c * r, s_ * r, 0.12), (c * r * 1.02, s_ * r * 1.02, 0.22)], 0.05, m, res=6)
        sphere(f"{prefix}Toe{k}", 0.08, (c * r * 0.92, s_ * r * 0.92, 0.07), m, seg=10, rings=6, scale=(1, 1, 0.8))


def shield_iron(prefix, house, h, mtx, K, key=None, rim=None):
    """A heater shield `h` tall, its point at the origin, its face (a house crest) to -Y, with a rolled iron rim."""
    s = _mark()
    poly = B43.shield_poly(h)
    if key:
        pprism(f"{prefix}Face", key, poly, 0.08, Matrix(), K["gp"], "GY_gilt")
    else:
        crest(f"{prefix}Face", house, h, 0.08, Matrix(), K)
    pts = [(u, -0.045, w) for u, w in poly]
    tube(f"{prefix}Rim", pts + [pts[0]], 0.03, rim or K["iron"], poly=True)
    box(f"{prefix}Back", (h * 0.5, 0.04, h * 0.5), (0, 0.06, h * 0.55), K["leather"], bevel=0.01)
    _xform(s, mtx)


def cushion(name, w, d, h, loc, mat):
    """A soft cushion: a rounded box with a puffed top."""
    ob = box(name, (w, d, h), loc, mat, bevel=min(w, d, h) * 0.45, segments=3)
    return ob


def books_row(prefix, x0, x1, y, z, K, rnd, mats, hmin=0.55, hmax=0.8, d=0.5):
    """Books standing on a shelf from x0 to x1 (spines at -Y), random widths, heights and covers."""
    x = x0
    k = 0
    while x < x1 - 0.1:
        w = rnd.uniform(0.09, 0.16)
        h = rnd.uniform(hmin, hmax)
        m = mats[rnd.randrange(len(mats))]
        tilt = rnd.uniform(-0.04, 0.04)
        box(f"{prefix}{k}", (w, d, h), (x + w / 2, y, z + h / 2), m, bevel=0.012, rot=(0, tilt, 0))
        box(f"{prefix}{k}B", (w + 0.006, 0.02, 0.03), (x + w / 2, y - d / 2, z + h * 0.8), K["gilt"], bevel=0.0, rot=(0, tilt, 0))
        x += w + 0.01
        k += 1


# ------------------------------------------------------------------ preview

def preview(objs, name, dims, suffix=""):
    """The template look: Glow / Glow2 pieces lit in their Neon colours, Glass see-through, a moody three-light rig, a dark
    slate floor, 900 x 700."""
    sc = bpy.context.scene
    cols = GLOW.get(name, {})
    for ob in objs:
        suf = ob.name.rsplit("_", 1)[-1] if "_" in ob.name else ""
        if suf not in ("Glow", "Glow2", "Glass"):
            continue
        rgb = tuple((c / 255) ** 2.2 for c in cols.get(suf, (255, 160, 80) if suf != "Glass" else (225, 232, 245)))
        m = bpy.data.materials.new(f"Preview{suf}")
        m.use_nodes = True
        bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        if suf == "Glass":
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Roughness"].default_value = 0.05
            bs.inputs["Transmission Weight"].default_value = 1.0
            bs.inputs["Alpha"].default_value = 0.3      # Roblox Glass reads mostly see-through
        else:
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 2.5
        ob.data.materials.clear()
        ob.data.materials.append(m)
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 900, 700
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.032, 1)
    bpy.context.view_layer.update()
    lo = [min((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    hi = [max((o.matrix_world @ Vector(c))[k] for o in objs for c in o.bound_box) for k in range(3)]
    ctr = Vector([(a + b) / 2 for a, b in zip(lo, hi)])
    size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
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
        o.rotation_euler = (Vector((0, 0, zc)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    light("AREA", (size * 0.9, -size * 1.2, size * 1.2), 480 * size, (1.0, 0.85, 0.7), s=size * 0.8)
    light("AREA", (-size * 1.3, -size * 0.6, size * 0.7), 150 * size, (0.5, 0.55, 0.95), s=size)
    light("AREA", (-size * 0.3, size * 1.4, size * 1.1), 380 * size, (0.95, 0.35, 0.4), s=size)
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.data.materials.append(P.material("Floor46", "NH_Slate", tint=(0.2, 0.2, 0.22), scale=0.15))
    cam = bpy.data.cameras.new("C")
    cam.lens = 50
    co = bpy.data.objects.new("C", cam)
    bpy.context.collection.objects.link(co)
    d = max(size * 1.5, (hi[2] - lo[2]) * 1.95)
    co.location = ctr + Vector((d * 0.45, -d, size * CAM.get(name, 0.22)))
    co.rotation_euler = (ctr - co.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sc.render.filepath = os.path.join(P.OUT_PRE, f"{name}{suffix}.png")
    bpy.ops.render.render(write_still=True)


# ================================================================== ARMORY

def katana_stand(M):
    """A three-tier katana stand in black lacquer with a crimson torii-style top bar (upswept ends) and a Vigil crest plaque:
    a crimson-sheathed katana, a black one, and on top a katana half drawn to show its blade; 4.6 wide, 3.9 tall."""
    K = kit(M)
    lq, br = K["saya"], K["gilt"]
    box("Base", (4.2, 1.3, 0.22), (0, 0, 0.11), lq, bevel=0.05)
    box("BaseLip", (4.0, 1.1, 0.08), (0, 0, 0.26), K["crimson"], bevel=0.02)
    for sx in (-1, 1):
        x = sx * 1.45
        prism(f"Upright{sx}", [(0.35, 0.3), (0.05, 0.3), (0.1, 1.2), (0.05, 3.3), (0.32, 3.3), (0.38, 1.2)], x, 0.18, lq, plane="YZ", bevel=0.02)
        for k, z in enumerate((1.0, 1.85, 2.7)):
            z += 0.1 if sx > 0 else 0.0
            prism(f"Arm{sx}{k}", [(0.15, z - 0.08), (-0.42, z - 0.08), (-0.52, z + 0.14), (-0.42, z + 0.16), (-0.38, z + 0.04),
                                  (-0.2, z + 0.04), (-0.18, z + 0.12), (-0.08, z + 0.12), (-0.08, z + 0.04), (0.15, z + 0.06)], x, 0.16, lq,
                  plane="YZ", bevel=0.012)
            box(f"ArmCap{sx}{k}", (0.17, 0.06, 0.05), (x, -0.47, z + 0.15), br, bevel=0.01)
        box(f"Foot{sx}", (0.5, 1.2, 0.12), (x, 0, 0.36), lq, bevel=0.03)
    # torii top bar
    pts = [(x, 0.2, 3.38 + 0.18 * (abs(x) / 2.3) ** 3) for x in [-2.35 + i * 4.7 / 16 for i in range(17)]]
    tube("Kasagi", pts, 0.11, K["crimson"], square=True)
    tube("KasagiTop", [(x, y, z + 0.13) for x, y, z in pts], 0.07, lq, square=True)
    box("Nuki", (3.3, 0.14, 0.14), (0, 0.2, 3.05), lq, bevel=0.02)
    box("Gakuzuka", (0.3, 0.12, 0.3), (0, 0.2, 3.22), lq, bevel=0.01)
    crest("Crest", "Vigil", 0.62, 0.04, T(0, 0.12, 2.75), K)
    tube("TasselCord", [(0.38, 0.1, 3.3), (0.42, 0.05, 3.0), (0.4, 0.05, 2.8)], 0.015, K["wrap"])
    lathe("Tassel", [(0, 0), (0.05, 0.02), (0.06, 0.2), (0.03, 0.28), (0, 0.3)], K["wrap"], seg=10, loc=(0.4, 0.05, 2.5))
    katana("KatA", T(-1.62, -0.3, 1.09), K, saya=K["sayared"])
    katana("KatB", T(-1.62, -0.3, 1.94), K)
    katana("KatC", T(-1.62, -0.3, 2.79), K, drawn=0.95)
    return _dims()


def _polearm(prefix, kind, K, H=8.6):
    """A polearm standing on its butt at the origin, its head broadside to the front (-Y): the blades lie in the XZ plane with
    their cutting edges picked out in silver."""
    s = _mark()
    ash, sv, ir, bl = K["ash"], K["silver"], K["iron"], K["blade"]
    zt = H - {"glaive": 1.6, "pike": 1.4, "wolfspear": 1.4}.get(kind, 1.0)
    cyl(f"{prefix}Shaft", 0.06, zt, (0, 0, zt / 2), ash, verts=10, bevel=0.0)
    cyl(f"{prefix}Butt", 0.075, 0.25, (0, 0, 0.125), ir, verts=10, bevel=0.01)
    for z in (2.7, 3.05):
        cyl(f"{prefix}Grip{z}", 0.07, 0.22, (0, 0, z), K["leather"], verts=10, bevel=0.006)
    cyl(f"{prefix}Socket", 0.08, 0.55, (0, 0, zt - 0.15), ir, verts=10, bevel=0.012)
    for z in (zt - 0.4, zt + 0.08):
        hoop(f"{prefix}Ring{z:.2f}", (0, 0, z), 0.085, "Z", K["gilt"], thick=0.018)

    def edge(name, pts):
        tube(f"{prefix}{name}", [(x, 0, z) for x, z in pts], 0.024, sv, poly=True)
    if kind == "halberd":
        axe = [(0, zt - 0.6), (-0.12, zt - 0.6), (-0.75, zt - 0.95), (-0.98, zt - 0.35), (-0.86, zt + 0.28), (-0.12, zt + 0.1), (0, zt + 0.1)]
        prism(f"{prefix}Axe", axe, 0, 0.05, bl, plane="XZ", bevel=0.004)
        edge("AxeEdge", axe[2:5])
        prism(f"{prefix}Fluke", [(0, zt - 0.3), (0.5, zt - 0.12), (0.62, zt + 0.06), (0.0, zt + 0.02)], 0, 0.05, ir, plane="XZ", bevel=0.004)
        lathe(f"{prefix}Spike", [(0, 0), (0.09, 0.0), (0.07, 0.25), (0.0, 1.0)], bl, seg=4, loc=(0, 0, zt + 0.1), scale=(1.0, 0.35))
        for k in range(3):
            rivet(f"{prefix}Rv{k}", -0.08, -0.03, zt - 0.4 + k * 0.22, K["gilt"], r=0.025)
    elif kind == "glaive":
        blade = [(0.05, zt - 0.1), (-0.15, zt - 0.1), (-0.3, zt + 0.45), (-0.24, zt + 1.15), (0.06, zt + 1.62), (0.04, zt + 1.0), (0.08, zt + 0.35)]
        prism(f"{prefix}Blade", blade, 0, 0.045, bl, plane="XZ", bevel=0.004)
        edge("Edge", blade[1:5])
        prism(f"{prefix}Hook", [(0.06, zt + 0.15), (0.32, zt + 0.22), (0.4, zt + 0.46), (0.07, zt + 0.36)], 0, 0.045, ir, plane="XZ", bevel=0.004)
        box(f"{prefix}Fuller", (0.05, 0.05, 0.7), (-0.1, 0, zt + 0.55), K["ink"], bevel=0.0, rot=(0, 0.2, 0))
    elif kind == "wolfspear":
        lathe(f"{prefix}Leaf", [(0, 0), (0.08, 0.05), (0.26, 0.45), (0.22, 0.85), (0.0, 1.4)], bl, seg=4, loc=(0, 0, zt + 0.05), scale=(1.0, 0.16))
        edge("LeafEdgeL", [(-0.08, zt + 0.1), (-0.26, zt + 0.5), (-0.22, zt + 0.9), (0.0, zt + 1.45)])
        edge("LeafEdgeR", [(0.08, zt + 0.1), (0.26, zt + 0.5), (0.22, zt + 0.9), (0.0, zt + 1.45)])
        box(f"{prefix}Bar", (0.7, 0.07, 0.07), (0, 0, zt - 0.08), sv, bevel=0.015)
        for sx in (-1, 1):
            cone(f"{prefix}Lug{sx}", 0.06, 0.0, 0.18, (sx * 0.44, 0, zt - 0.08), sv, verts=6, rot=(0, sx * PI / 2, 0))
        strip(f"{prefix}Pennon", [(0.02, -0.1, zt - 0.3), (0.4, -0.12, zt - 0.38), (0.75, -0.12, zt - 0.56), (1.0, -0.12, zt - 0.85)], 0.4, (0, 0, 1),
              K["crimson"], thick=0.012)
    elif kind == "pike":
        lathe(f"{prefix}Head", [(0, 0), (0.07, 0.0), (0.06, 0.35), (0.045, 1.0), (0.0, 1.4)], sv, seg=4, loc=(0, 0, zt + 0.05))
        for k in range(7):
            a = k * 2 * PI / 7
            tube(f"{prefix}Tassel{k}", [(0, 0, zt - 0.05), (0.07 * math.cos(a), 0.07 * math.sin(a), zt - 0.4), (0.1 * math.cos(a), 0.1 * math.sin(a), zt - 0.75)],
                 0.018, K["horse"], res=4)
    elif kind == "corbin":
        beak = [(0, zt - 0.05), (-0.3, zt - 0.03), (-0.78, zt - 0.38), (-0.8, zt - 0.46), (-0.36, zt - 0.24), (0, zt - 0.24)]
        prism(f"{prefix}Beak", beak, 0, 0.07, bl, plane="XZ", bevel=0.006)
        edge("BeakEdge", beak[1:4])
        box(f"{prefix}Hammer", (0.36, 0.18, 0.18), (0.22, 0, zt - 0.14), ir, bevel=0.02)
        for k in range(4):
            cone(f"{prefix}Tooth{k}", 0.03, 0.0, 0.07, (0.42, -0.04 + (k % 2) * 0.08, zt - 0.18 + (k // 2) * 0.08), ir, verts=4, rot=(0, PI / 2, 0))
        lathe(f"{prefix}Top", [(0, 0), (0.07, 0.0), (0.0, 0.7)], bl, seg=4, loc=(0, 0, zt + 0.05), scale=(1.0, 0.4))
        sphere(f"{prefix}Raven", 0.11, (0, 0, zt + 0.02), K["ebony"], seg=10, rings=6, scale=(1.3, 0.9, 0.8))
        cone(f"{prefix}RavenBeak", 0.04, 0.0, 0.16, (-0.2, 0, zt + 0.02), K["ebony"], verts=6, rot=(0, -PI / 2, 0))
    _xform(s, Matrix())
    return s


def polearm_rack(M):
    """A monster hunters' polearm rack: a crimson-enamelled plinth banded in black iron with the Vigil crest, two heavy iron
    posts with silver crescent finials and two loop rails, and five polearms standing broadside with their silver-edged heads
    up: a halberd, a raven's-beak bec de corbin, a boar spear (silver crossbar lugs, a crimson pennon) in the middle, a
    tasselled silver pike and a hooked glaive; 4.9 wide, 1.6 deep, 9.0 tall."""
    K = kit(M)
    ir, br, cr = K["iron"], K["gilt"], K["crimson"]
    W = 4.4
    box("Kick", (W + 0.4, 1.6, 0.16), (0, 0, 0.08), ir, bevel=0.03)
    box("Plinth", (W + 0.2, 1.4, 0.5), (0, 0, 0.41), cr, bevel=0.03)
    box("PlinthTop", (W + 0.3, 1.5, 0.1), (0, 0, 0.71), ir, bevel=0.025)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Corner{sx}{sy}", (0.14, 0.14, 0.62), (sx * (W / 2 + 0.07), sy * 0.67, 0.43), ir, bevel=0.015)
    for k in range(6):
        x = -W / 2 + 0.2 + k * (W - 0.4) / 5
        if abs(x) > 0.3:
            rivet(f"PR{k}", x, -0.71, 0.42, br, r=0.035)
    crest("Crest", "Vigil", 0.44, 0.03, T(0, -0.715, 0.2), K)
    zb = 0.76
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.05)
        box(f"Post{sx}", (0.3, 0.3, 5.6), (x, 0.25, zb + 2.8), ir, bevel=0.03)
        box(f"PostCap{sx}", (0.34, 0.34, 0.14), (x, 0.25, zb + 5.67), ir, bevel=0.03)
        prism(f"Gusset{sx}", [(0, 0), (0.6, 0), (0, 0.6)], 0, 0.06, ir, plane="YZ", bevel=0.01).matrix_world = \
            T(x, 0.13, zb) @ RZ(PI)
        pts = []
        for i in range(17):
            t = PI * 0.15 + PI * 1.7 * i / 16
            pts.append((math.cos(t) * 0.34, math.sin(t) * 0.34))
        for i in range(16, -1, -1):
            t = PI * 0.15 + PI * 1.7 * i / 16
            pts.append((math.cos(t) * 0.25 + 0.08, math.sin(t) * 0.25))
        moon = prism(f"Crescent{sx}", pts, 0, 0.06, K["silver"], plane="XZ")
        moon.matrix_world = T(x, 0.25, zb + 6.12) @ RY(-PI / 2)
        cyl(f"MoonStem{sx}", 0.04, 0.14, (x, 0.25, zb + 5.8), br, verts=8, bevel=0.0)
    for z in (zb + 2.5, zb + 5.2):
        box(f"Rail{z:.1f}", (W + 0.1, 0.16, 0.16), (0, 0.25, z), ir, bevel=0.025)
        box(f"RailTrim{z:.1f}", (W - 0.1, 0.02, 0.05), (0, 0.16, z), br, bevel=0.0)
    # crimson back panel under the lower rail, with an iron arcade, for weight
    box("Panel", (W, 0.08, 2.42), (0, 0.33, zb + 1.21), cr, bevel=0.015)
    for k in range(5):
        x = -1.76 + k * 0.88
        pts = [(px, 0.28, pz) for px, pz in arch_xz(x - 0.4, x + 0.4, zb + 0.2, 2.05, n=10)]
        tube(f"Arcade{k}", pts, 0.035, ir, square=True, poly=True)
        cyl(f"Boss{k}", 0.1, 0.05, (x, 0.28, zb + 1.6), br, rot=(PI / 2, 0, 0), verts=12, bevel=0.01)
    box("PanelBand", (W, 0.1, 0.12), (0, 0.3, zb + 0.12), ir, bevel=0.015)
    kinds = ("halberd", "corbin", "wolfspear", "pike", "glaive")
    for k, kind in enumerate(kinds):
        x = -1.76 + k * 0.88
        cyl(f"Cup{k}", 0.11, 0.2, (x, 0, zb + 0.1), ir, verts=12, bevel=0.015)
        for z in (zb + 2.5, zb + 5.2):
            hoop(f"Loop{k}{z:.1f}", (x, 0.0, z), 0.1, "Z", ir, thick=0.022)
            box(f"LoopArm{k}{z:.1f}", (0.05, 0.22, 0.05), (x, 0.15, z), ir, bevel=0.0)
        s = _polearm(f"P{k}", kind, K, H=8.2 if kind != "wolfspear" else 8.5)
        _xform(s, T(x, 0, zb))
    return _dims()


def _helm_bascinet(prefix, loc, K, plume=True):
    x, y, z = loc
    st = K["plate"]
    lathe(f"{prefix}Skull", [(0, -0.02), (0.3, -0.02), (0.32, 0.25), (0.3, 0.5), (0.22, 0.7), (0.1, 0.82), (0, 0.86)], st, seg=24,
          loc=(x, y, z), scale=(0.9, 1.0))
    lathe(f"{prefix}Aventail", [(0.31, -0.02), (0.36, -0.2), (0.42, -0.32), (0.0, -0.32)], K["mail"], seg=24, loc=(x, y, z), scale=(0.95, 1.0))
    box(f"{prefix}Slit", (0.34, 0.06, 0.035), (x, y - 0.3, z + 0.4), K["socket"], bevel=0.008)
    box(f"{prefix}Brow", (0.42, 0.06, 0.05), (x, y - 0.3, z + 0.47), st, bevel=0.015)
    for i in range(6):
        cyl(f"{prefix}Breath{i}", 0.012, 0.05, (x - 0.1 + (i % 3) * 0.1, y - 0.3, z + 0.2 - (i // 3) * 0.07), K["socket"], rot=(PI / 2, 0, 0), verts=6, bevel=0)
    if plume:
        pts = [(x, y - 0.18 + i * 0.07, z + 0.84 + 0.18 * math.sin(i / 7 * PI) - (0.25 if i > 5 else 0)) for i in range(8)]
        tube(f"{prefix}Plume", pts, 0.07, K["horse"], res=6)
        cyl(f"{prefix}PlumeHolder", 0.04, 0.12, (x, y - 0.1, z + 0.84), K["gilt"], verts=8, bevel=0.005)


def _gauntlet(prefix, mtx, K):
    """A plate gauntlet hanging fingers down from its cuff at the origin."""
    s = _mark()
    st = K["plate"]
    lathe(f"{prefix}Cuff", [(0, 0), (0.12, 0.0), (0.16, 0.2), (0.17, 0.24), (0, 0.24)], st, seg=14, loc=(0, 0, -0.24), scale=(1, 0.8))
    box(f"{prefix}Back", (0.2, 0.1, 0.22), (0, 0, -0.36), st, bevel=0.03)
    for k in range(4):
        x = -0.075 + k * 0.05
        for j in range(3):
            box(f"{prefix}F{k}{j}", (0.045, 0.06, 0.07), (x, -0.01, -0.5 - j * 0.07), st, bevel=0.012, rot=(0.15 * j, 0, 0))
    box(f"{prefix}Thumb", (0.05, 0.06, 0.16), (0.13, -0.03, -0.4), st, bevel=0.012, rot=(0, -0.4, 0))
    _xform(s, mtx)


def plate_armour_stand(M):
    """A suit of Vigil plate on a cross-shaped iron stand: a ridged breastplate scored by three claw gouges (a werewolf's,
    no blood), pauldrons and faulds, a plumed bascinet with a mail aventail, a crimson Vigil tabard and gauntlets hung from
    the crossbar; 3.0 wide, 6.3 tall."""
    K = kit(M)
    ir, st, br = K["iron"], K["plate"], K["gilt"]
    tripod("Foot", 1.0, K)
    cyl("Post", 0.07, 4.2, (0, 0, 2.6), ir, verts=10, bevel=0.0)
    box("Cross", (2.7, 0.14, 0.14), (0, 0.15, 4.05), ir, bevel=0.03)
    for sx in (-1, 1):
        finial(f"CrossFin{sx}", sx * 1.38, 0.15, 3.97, br, s=0.6)
    sy = 0.7
    prof = [(0, 2.8), (0.5, 2.8), (0.58, 3.15), (0.63, 3.55), (0.6, 3.9), (0.47, 4.12), (0.27, 4.24), (0, 4.24)]
    lathe("Breast", prof, st, seg=32, scale=(1.0, sy))
    ridge = [(0, -0.002 - r * sy, z) for r, z in prof[1:-1]]
    tube("Ridge", ridge, 0.025, st, res=4)
    hoop("Gorget", (0, 0, 4.28), 0.3, "Z", st, thick=0.06)
    lathe("GorgetPlate", [(0, 4.2), (0.36, 4.2), (0.32, 4.34), (0.18, 4.4), (0, 4.4)], st, seg=24, scale=(1.0, 0.85))
    for k in range(3):
        z0 = 2.8 - k * 0.2
        lathe(f"Fauld{k}", [(0, z0), (0.52 + k * 0.05, z0), (0.6 + k * 0.06, z0 - 0.22), (0, z0 - 0.22)], st, seg=28, scale=(1.0, sy + 0.04))
        for j in range(5):
            a = -PI / 2 + (j - 2) * 0.35
            rivet(f"FR{k}{j}", math.cos(a) * (0.57 + k * 0.055), math.sin(a) * (0.57 + k * 0.055) * (sy + 0.04) - 0.01, z0 - 0.1, br, r=0.022)
    for sx in (-1, 1):
        for k in range(3):
            sphere(f"Pauldron{sx}{k}", 0.34 - k * 0.04, (sx * (0.62 + k * 0.06), 0, 4.05 - k * 0.16), st, seg=18, rings=9,
                   scale=(1.0, 0.85, 0.62))
        hoop(f"PaulTrim{sx}", (sx * 0.6, 0, 4.12), 0.3, "Z", br, thick=0.015)
        _gauntlet(f"G{sx}", T(sx * 1.25, 0.15, 3.96) @ RZ(sx * 0.2), K)
    # claw gouges across the breastplate (dark grooves)
    for k in range(3):
        pts = []
        for i in range(6):
            t = i / 5
            x = -0.36 + k * 0.1 + t * 0.42
            z = 3.85 - k * 0.04 - t * 0.6
            r = prof_r(prof, z) * math.cos(PI / 32)
            yy = -math.sqrt(max(0.0, r * r - x * x)) * sy - 0.006
            pts.append((x, yy, z))
        tube(f"Gouge{k}", pts, 0.014, K["socket"], res=4)
    # tabard
    tab = [(-0.36, 2.32), (0.36, 2.32), (0.34, 1.3), (0.18, 1.18), (0.0, 1.3), (-0.18, 1.18), (-0.34, 1.3)]
    prism("Tabard", tab, -0.52, 0.03, K["feltc"], plane="XZ")
    for sx in (-1, 1):
        tube(f"TabTrim{sx}", [(sx * 0.36, -0.54, 2.32), (sx * 0.34, -0.54, 1.3)], 0.014, br, poly=True)
    crest("TabCrest", "Vigil", 0.6, 0.02, T(0, -0.545, 1.5), K)
    _helm_bascinet("H", (0, 0, 4.48), K)
    return _dims()


def mail_hauberk_stand(M):
    """A knee-length hauberk of silver mail on an iron dress form: brass-ringed sleeves and hem, a crimson quilted gambeson
    showing beneath, a mail coif and mantle over the head form, a leather belt with a silver buckle and a price tag reading
    SILVER MAIL; 2.0 wide, 5.6 tall."""
    K = kit(M)
    ir, ml, br = K["iron"], K["mail"], K["brassf"]
    tripod("Foot", 0.85, K)
    cyl("Post", 0.06, 1.2, (0, 0, 0.9), ir, verts=10, bevel=0.0)
    sy = 0.72
    lathe("Gambeson", [(0, 1.32), (0.66, 1.32), (0.62, 1.7), (0, 1.7)], K["quilt"], seg=28, scale=(1, sy + 0.02))
    for k in range(6):
        hoop(f"Quilt{k}", (0, 0, 1.35 + k * 0.06), 0.66 - k * 0.006, "Z", K["quilt"], thick=0.012)
    prof = [(0, 1.5), (0.74, 1.5), (0.7, 1.75), (0.58, 2.3), (0.5, 2.8), (0.56, 3.2), (0.6, 3.6), (0.57, 3.95), (0.42, 4.15), (0.28, 4.25), (0, 4.25)]
    lathe("Hauberk", prof, ml, seg=36, scale=(1, sy))
    for r, z in ((0.745, 1.5), (0.75, 1.56)):
        hoop(f"Hem{z}", (0, 0, z), r, "Z", br, thick=0.018)
    for sx in (-1, 1):
        a = sx * 0.55
        mtx = T(sx * 0.6, 0, 3.92) @ RY(PI - a)
        s = _mark()
        lathe(f"Sleeve{sx}", [(0, 0), (0.2, 0), (0.24, 0.85), (0, 0.85)], ml, seg=16)
        hoop(f"Cuff{sx}", (0, 0, 0.84), 0.245, "Z", br, thick=0.02)
        _xform(s, mtx)
    tz = 2.78
    lathe("Belt", [(0, tz - 0.08), (0.52, tz - 0.08), (0.52, tz + 0.08), (0, tz + 0.08)], K["leather"], seg=28, scale=(1, sy + 0.05))
    box("Buckle", (0.18, 0.05, 0.18), (0, -0.39, tz), K["silver"], bevel=0.02)
    box("BuckleIn", (0.1, 0.06, 0.09), (0, -0.395, tz), K["leather"], bevel=0.01)
    tube("TagCord", [(0.28, -0.36, tz - 0.05), (0.3, -0.42, tz - 0.25), (0.32, -0.44, tz - 0.4)], 0.008, K["cord"])
    box("Tag", (0.3, 0.012, 0.18), (0.32, -0.45, tz - 0.5), K["parch"], bevel=0.004)
    B24._text("TagText", "SILVER MAIL", FONT, K["ink"], lambda u, v, hh: (0.32 + u, -0.457 - hh, tz - 0.5 + v), fit=(0.24, 0.07), depth=0.004, res=1)
    # head form and coif
    cyl("Neck", 0.13, 0.3, (0, 0, 4.35), ir, verts=12, bevel=0.01)
    sphere("Head", 0.3, (0, 0, 4.85), ir, seg=16, rings=10, scale=(0.85, 0.95, 1.1))
    lathe("Coif", [(0.7, 4.0), (0.66, 4.12), (0.45, 4.3), (0.34, 4.5), (0.33, 4.8), (0.3, 5.05), (0.2, 5.2), (0, 5.25)], ml, seg=32,
          scale=(1, 0.9))
    sphere("Face", 0.24, (0, -0.25, 4.8), ir, seg=14, rings=8, scale=(0.75, 0.3, 1.15))
    hoop("CoifHem", (0, 0, 4.02), 0.69, "Z", br, thick=0.015)
    return _dims()


def shield_wall(M):
    """A wall of house arms on a black iron trellis: the school's great shield over two crossed silver-headed spears, the five
    house shields round it (Crimson, Ravens, Rovers, Vigil, Wardens), spear-tipped top rail, a brass HOUSE ARMS plate; 6.6
    wide, 6.7 tall (wall)."""
    K = kit(M)
    ir, br = K["iron"], K["gilt"]
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.14, 0.12, 6.2), (sx * 3.1, -0.06, 3.1), ir, bevel=0.02)
        box(f"Mount{sx}", (0.36, 0.06, 0.36), (sx * 3.1, -0.03, 5.7), ir, bevel=0.01)
        box(f"Mount2{sx}", (0.36, 0.06, 0.36), (sx * 3.1, -0.03, 0.5), ir, bevel=0.01)
    for z in (0.3, 6.1):
        box(f"Rail{z}", (6.36, 0.12, 0.14), (0, -0.06, z), ir, bevel=0.02)
    for k in range(13):
        x = -3.0 + k * 0.5
        cone(f"Spike{k}", 0.05, 0.0, 0.32, (x, -0.06, 6.33), ir, verts=4)
        if k % 2 == 0:
            tube(f"Scroll{k}", [(x - 0.2, -0.06, 6.17), (x - 0.1, -0.06, 6.42), (x, -0.06, 6.2), (x + 0.1, -0.06, 6.42), (x + 0.2, -0.06, 6.17)],
                 0.02, ir)
    for sx in (-1, 1):
        a = sx * 0.62
        L = 6.0
        c = Vector((0, -0.12, 3.2))
        d = Vector((math.sin(a), 0, math.cos(a)))
        p0, p1 = c - d * L / 2, c + d * L / 2
        tube(f"Spear{sx}", [tuple(p0), tuple(p1)], 0.04, K["ash"], poly=True)
        s = _mark()
        lathe(f"SpearHead{sx}", [(0, 0), (0.06, 0.04), (0.14, 0.3), (0.0, 0.72)], K["silver"], seg=4, scale=(1, 0.2))
        cyl(f"SpearSock{sx}", 0.05, 0.25, (0, 0, -0.05), ir, verts=8, bevel=0.01)
        _xform(s, T(*p1) @ RY(a))
    shield_iron("Great", None, 3.0, T(0, -0.25, 1.45), K, key="SH_SchoolShield", rim=br)
    plate_pos = {"Crimson": (-2.15, 3.7), "Ravens": (-2.15, 1.15), "Vigil": (0, 4.65), "Rovers": (2.15, 3.7), "Wardens": (2.15, 1.15)}
    for h, (x, z) in plate_pos.items():
        shield_iron(f"S{h}", h, 1.75, T(x, -0.2, z), K)
        cyl(f"Peg{h}", 0.05, 0.2, (x, -0.1, z + 1.2), ir, rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    box("Plate", (1.9, 0.04, 0.3), (0, -0.28, 0.95), br, bevel=0.01)
    label("PlateText", "HOUSE ARMS", K["ink"], 0, -0.302, 0.95, 1.6, 0.17, depth=0.006)
    return _dims()


def grindstone(M):
    """A treadle grindstone: a sandstone wheel on a cast-iron A-frame dipping into an iron water trough, a crank and treadle
    pedal, a copper drip can over the wheel, a tool rest with a blade on it and a side tray with a whetstone and oil can;
    1.9 wide, 3.4 deep, 3.3 tall."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    zc, R = 2.05, 0.85
    for sx in (-1, 1):
        x = sx * 0.42
        tube(f"LegF{sx}", [(x, -0.9, 0.1), (x, -0.08, zc)], 0.06, ir, square=True, poly=True)
        tube(f"LegB{sx}", [(x, 0.9, 0.1), (x, 0.08, zc)], 0.06, ir, square=True, poly=True)
        box(f"FootF{sx}", (0.22, 0.3, 0.1), (x, -0.92, 0.05), ir, bevel=0.02)
        box(f"FootB{sx}", (0.22, 0.3, 0.1), (x, 0.92, 0.05), ir, bevel=0.02)
        box(f"Brace{sx}", (0.1, 1.5, 0.1), (x, 0, 0.75), ir, bevel=0.02)
        cyl(f"Bearing{sx}", 0.14, 0.14, (x, 0, zc), br, rot=(0, PI / 2, 0), verts=14, bevel=0.02)
    cyl("Wheel", R, 0.3, (0, 0, zc), K["grit"], rot=(0, PI / 2, 0), verts=48, bevel=0.03)
    for sx in (-1, 1):
        cyl(f"Flange{sx}", 0.28, 0.05, (sx * 0.17, 0, zc), ir, rot=(0, PI / 2, 0), verts=16, bevel=0.01)
        for k in range(6):
            a = k * PI / 3
            rivet(f"FlR{sx}{k}", sx * 0.2, math.cos(a) * 0.2, zc + math.sin(a) * 0.2, br, r=0.025)
    cyl("Axle", 0.04, 1.3, (0.1, 0, zc), ir, rot=(0, PI / 2, 0), verts=8, bevel=0.0)
    box("Crank", (0.06, 0.08, 0.4), (0.72, 0, zc - 0.17), ir, bevel=0.01)
    tube("Conrod", [(0.78, 0, zc - 0.34), (0.78, -0.35, 0.3)], 0.025, ir, poly=True)
    # treadle
    tube("Treadle", [(0.55, 0.7, 0.14), (0.55, -0.35, 0.22), (0.4, -1.35, 0.26)], 0.04, ir, square=True, poly=True)
    box("Pedal", (0.5, 0.36, 0.05), (0.3, -1.42, 0.28), ir, bevel=0.015)
    for k in range(4):
        box(f"PedalTread{k}", (0.46, 0.03, 0.02), (0.3, -1.56 + k * 0.09, 0.31), ir, bevel=0.0)
    cyl("TreadlePivot", 0.06, 0.24, (0.55, 0.7, 0.14), br, rot=(0, PI / 2, 0), verts=10, bevel=0.01)
    # trough
    zt = 1.38
    box("TroughBase", (0.6, 1.8, 0.06), (0, 0, 0.82), ir, bevel=0.01)
    for sx in (-1, 1):
        box(f"TroughSide{sx}", (0.05, 1.8, zt - 0.82), (sx * 0.28, 0, (zt + 0.82) / 2), ir, bevel=0.01)
        box(f"TroughEnd{sx}", (0.6, 0.05, zt - 0.82), (0, sx * 0.88, (zt + 0.82) / 2), ir, bevel=0.01)
    box("Water", (0.52, 1.72, 0.02), (0, 0, zt - 0.12), K["water"], bevel=0.0)
    for sx in (-1, 1):
        box(f"TroughLip{sx}", (0.1, 1.84, 0.04), (sx * 0.28, 0, zt + 0.02), br, bevel=0.005)
    # drip can
    tube("CanArm", [(-0.42, 0.08, zc + 0.1), (-0.42, 0.3, zc + 1.0), (0.0, 0.35, zc + 1.05)], 0.03, ir, square=True)
    lathe("Can", [(0, 0), (0.16, 0), (0.2, 0.06), (0.2, 0.36), (0.18, 0.4), (0, 0.4)], K["copper"], seg=18, loc=(0, 0.35, zc + 0.9))
    hoop("CanBand", (0, 0.35, zc + 1.2), 0.205, "Z", br, thick=0.012)
    tube("Spout", [(0, 0.2, zc + 0.95), (0, 0.05, zc + 0.92), (0, -0.05, R + zc + 0.05 - 0.02)], 0.02, K["copper"])
    sphere("Drip", 0.025, (0, -0.06, zc + R + 0.0), K["water"], seg=8, rings=6, scale=(1, 1, 1.5))
    # tool rest and blade
    box("Rest", (0.5, 0.08, 0.06), (0, -0.98, zc - 0.05), ir, bevel=0.01)
    for sx in (-1, 1):
        tube(f"RestArm{sx}", [(sx * 0.24, -0.98, zc - 0.05), (sx * 0.42, -0.4, zc - 0.25)], 0.025, ir, poly=True)
    dagger("Blade", T(-1.05, -0.5, 1.34) @ RZ(0.35), K, L=0.7, silver=False)
    dagger("Blade2", T(0.25, -0.92, zc - 0.0) @ RZ(PI * 0.5) @ RY(-0.5), K, L=0.85)
    # side tray
    box("Tray", (0.7, 0.9, 0.05), (-0.8, -0.2, 1.3), ir, bevel=0.01)
    tube("TrayArm", [(-0.42, -0.2, 1.0), (-0.8, -0.2, 1.27)], 0.03, ir, poly=True)
    box("Whetstone", (0.4, 0.16, 0.1), (-0.85, -0.35, 1.38), K["slate"], bevel=0.02)
    lathe("OilCan", [(0, 0), (0.12, 0), (0.12, 0.08), (0.05, 0.2), (0.03, 0.4), (0, 0.42)], K["copper"], seg=14, loc=(-0.8, 0.05, 1.33))
    return _dims()


def armory_counter(M):
    """The armourer's counter: crimson-enamelled steel banded and riveted in black iron, a portcullis grille panel with spiked
    feet either side of a crossed-katanas roundel, a black marble top with a brass blade-length rule inlaid along its front,
    a brass balance weighing silver shot, a ledger with quill and ink, a service bell and a tray of silver bullets; 6.6 wide,
    2.4 deep, 3.9 tall."""
    K = kit(M)
    ir, cr, br = K["iron"], K["crimson"], K["brassf"]
    W, D, H = 6.4, 2.2, 3.0
    box("Kick", (W, D - 0.2, 0.3), (0, 0.1, 0.15), ir, bevel=0.03)
    box("Body", (W - 0.1, D - 0.3, H - 0.3), (0, 0.1, 0.3 + (H - 0.3) / 2), cr, bevel=0.03)
    yf = -D / 2 + 0.25
    for k in range(7):
        x = -W / 2 + 0.1 + k * (W - 0.2) / 6
        box(f"Band{k}", (0.16, 0.06, H - 0.3), (x, yf - 0.03, 0.3 + (H - 0.3) / 2), ir, bevel=0.015)
        for j in range(6):
            rivet(f"BR{k}{j}", x, yf - 0.065, 0.55 + j * 0.42, br, r=0.025)
    for z in (0.42, H - 0.12):
        box(f"HBand{z}", (W - 0.06, 0.07, 0.16), (0, yf - 0.035, z), ir, bevel=0.015)
    # portcullis grilles between bands 1-2 and 4-5
    for k, x0 in enumerate((-W / 2 + 0.1 + (W - 0.2) / 6, -W / 2 + 0.1 + 4 * (W - 0.2) / 6)):
        x1 = x0 + (W - 0.2) / 6
        for i in range(4):
            x = x0 + (x1 - x0) * (i + 0.5) / 4
            box(f"GrV{k}{i}", (0.05, 0.05, 2.05), (x, yf - 0.06, 1.6), ir, bevel=0.008)
            cone(f"GrSpike{k}{i}", 0.04, 0.0, 0.16, (x, yf - 0.06, 0.6), ir, verts=4, rot=(PI, 0, 0))
        for j in range(4):
            box(f"GrH{k}{j}", (x1 - x0 - 0.16, 0.04, 0.05), ((x0 + x1) / 2, yf - 0.055, 1.0 + j * 0.45), ir, bevel=0.008)
        box(f"GrBack{k}", (x1 - x0 - 0.16, 0.02, 2.1), ((x0 + x1) / 2, yf - 0.005, 1.65), K["ink"], bevel=0.0)
    # roundel
    cyl("Roundel", 0.62, 0.08, (0, yf - 0.08, 1.75), ir, rot=(PI / 2, 0, 0), verts=32, bevel=0.02)
    cyl("RoundelIn", 0.5, 0.04, (0, yf - 0.12, 1.75), cr, rot=(PI / 2, 0, 0), verts=32, bevel=0.01)
    hoop("RoundelRim", (0, yf - 0.12, 1.75), 0.55, "Y", br, thick=0.02)
    for sx in (-1, 1):
        katana(f"RK{sx}", T(0, yf - 0.16 - (sx + 1) * 0.012, 1.75) @ RY(sx * PI / 4) @ T(-0.62, 0, 0) @ Matrix.Diagonal((0.4, 0.4, 0.4, 1)),
               K, L=3.0, sheath=False)
    # top
    zt = H
    box("Top", (W + 0.3, D + 0.15, 0.18), (0, 0.02, zt + 0.09), K["marble"], bevel=0.04)
    box("Rule", (W - 0.6, 0.04, 0.05), (0, -D / 2 - 0.05, zt + 0.12), br, bevel=0.005)
    for k in range(25):
        box(f"Tick{k}", (0.012, 0.02, 0.05 if k % 4 else 0.08), (-W / 2 + 0.3 + k * (W - 0.6) / 24, -D / 2 - 0.075, zt + 0.12), K["ink"], bevel=0.0)
    box("RuleTop", (W - 0.6, 0.16, 0.012), (0, -D / 2 + 0.06, zt + 0.186), br, bevel=0.0)
    # balance scale
    bx = -2.1
    cyl("ScaleBase", 0.22, 0.08, (bx, 0.2, zt + 0.22), br, verts=16, bevel=0.015)
    cyl("ScalePost", 0.03, 1.0, (bx, 0.2, zt + 0.75), br, verts=8, bevel=0.0)
    box("Beam", (1.2, 0.04, 0.04), (bx, 0.2, zt + 1.24), br, bevel=0.005, rot=(0, 0.08, 0))
    cone("Pointer", 0.03, 0.0, 0.18, (bx, 0.2, zt + 1.36), br, verts=4)
    for sx, dz in ((-1, -0.05), (1, 0.05)):
        px, pz = bx + sx * 0.58, zt + 1.24 - sx * 0.048
        for k in range(3):
            a = k * 2 * PI / 3
            tube(f"Str{sx}{k}", [(px, 0.2, pz), (px + math.cos(a) * 0.18, 0.2 + math.sin(a) * 0.18, pz - 0.55)], 0.005, br, poly=True)
        lathe(f"Pan{sx}", [(0, 0), (0.2, 0.02), (0.22, 0.06), (0.0, 0.03)], br, seg=18, loc=(px, 0.2, pz - 0.6))
    rnd = random.Random(4611)
    for k in range(12):
        a, r = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.13)
        sphere(f"Shot{k}", 0.035, (bx + 0.58 + math.cos(a) * r, 0.2 + math.sin(a) * r, zt + 1.24 - 0.048 - 0.53 + (0.02 if r < 0.07 else 0)), K["silver"],
               seg=8, rings=4)
    box("Weight", (0.1, 0.1, 0.12), (bx - 0.58, 0.2, zt + 1.24 + 0.05 - 0.55), br, bevel=0.01)
    # ledger, quill, inkpot
    s = _mark()
    box("LedgerL", (0.6, 0.85, 0.06), (-0.31, 0, 0.03), K["leather"], bevel=0.01, rot=(0, 0.04, 0))
    box("LedgerR", (0.6, 0.85, 0.06), (0.31, 0, 0.03), K["leather"], bevel=0.01, rot=(0, -0.04, 0))
    box("PageL", (0.55, 0.78, 0.04), (-0.29, 0, 0.07), K["paper"], bevel=0.01, rot=(0, 0.06, 0))
    box("PageR", (0.55, 0.78, 0.04), (0.29, 0, 0.07), K["paper"], bevel=0.01, rot=(0, -0.06, 0))
    for k in range(7):
        box(f"Line{k}", (0.42, 0.012, 0.004), (0.29, -0.3 + k * 0.1, 0.095), K["ink"], bevel=0.0)
    _xform(s, T(0.6, -0.1, zt + 0.18) @ RZ(0.15))
    lathe("InkPot", [(0, 0), (0.12, 0), (0.13, 0.1), (0.06, 0.16), (0.07, 0.2), (0, 0.2)], K["inkglass"], seg=14, loc=(1.5, 0.3, zt + 0.18))
    prism("Quill", [(0, 0), (0.04, 0.1), (0.07, 0.5), (0.04, 0.75), (0.0, 0.7), (-0.02, 0.4)], 0, 0.006, K["bone"], plane="XZ").matrix_world = \
        T(1.5, 0.3, zt + 0.3) @ RZ(0.6) @ RY(0.35)
    # bell
    lathe("Bell", [(0, 0), (0.18, 0), (0.17, 0.04), (0.12, 0.08), (0.11, 0.18), (0.06, 0.24), (0, 0.25)], br, seg=18, loc=(2.4, -0.3, zt + 0.18))
    cyl("BellKnob", 0.025, 0.08, (2.4, -0.3, zt + 0.47), br, verts=8, bevel=0.0)
    # bullet tray
    box("BTray", (0.7, 0.45, 0.06), (-0.7, -0.4, zt + 0.21), K["leather"], bevel=0.01)
    for i in range(4):
        for j in range(2):
            x, y = -0.95 + i * 0.16, -0.48 + j * 0.16
            cyl(f"Case{i}{j}", 0.035, 0.12, (x, y, zt + 0.3), br, verts=8, bevel=0.0)
            cone(f"Bullet{i}{j}", 0.035, 0.012, 0.08, (x, y, zt + 0.4), K["silver"], verts=8)
    return _dims()


def silver_dagger_case(M):
    """A locked display case of hunters' silver on iron legs with lion-claw feet: silver daggers fanned on crimson velvet with
    four silver-capped ash stakes and a silver rosary, under a sloped glass lid (Glass) barred by an iron cross-hasp and
    padlock; a SILVER ASH IRON plate; 3.8 wide, 1.9 deep, 3.4 tall."""
    K = kit(M)
    ir, br = K["iron"], K["gilt"]
    W, D = 3.6, 1.6
    z0, z1 = 2.2, 2.6
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.12), sy * (D / 2 - 0.12)
            tube(f"Leg{sx}{sy}", [(x, y, z0), (x + sx * 0.02, y + sy * 0.02, 1.2), (x + sx * 0.08, y + sy * 0.08, 0.2)], 0.06, ir, res=5)
            sphere(f"Ball{sx}{sy}", 0.11, (x + sx * 0.08, y + sy * 0.08, 0.11), br, seg=12, rings=8)
            for k in range(3):
                a = math.atan2(sy, sx) + (k - 1) * 0.6
                cone(f"Claw{sx}{sy}{k}", 0.045, 0.01, 0.16, (x + sx * 0.08 + math.cos(a) * 0.09, y + sy * 0.08 + math.sin(a) * 0.09, 0.12), ir, verts=6,
                     rot=(math.sin(a) * 0.9, -math.cos(a) * 0.9, 0))
    box("Stretcher", (W - 0.3, 0.08, 0.08), (0, 0, 0.75), ir, bevel=0.015)
    for sx in (-1, 1):
        box(f"StretcherE{sx}", (0.08, D - 0.3, 0.08), (sx * (W / 2 - 0.15), 0, 0.75), ir, bevel=0.015)
    box("Tray", (W, D, z1 - z0), (0, 0, (z0 + z1) / 2), ir, bevel=0.03)
    box("Apron", (W - 0.3, 0.04, 0.2), (0, -D / 2 - 0.02, z0 + 0.2), K["crimson"], bevel=0.01)
    box("Plate", (1.4, 0.03, 0.14), (0, -D / 2 - 0.045, z0 + 0.2), br, bevel=0.005)
    label("PlateText", "SILVER  ASH  IRON", K["ink"], 0, -D / 2 - 0.062, z0 + 0.2, 1.25, 0.08, depth=0.004)
    box("Velvet", (W - 0.2, D - 0.2, 0.06), (0, 0, z1 + 0.01), K["feltc"], bevel=0.02)
    zv = z1 + 0.05
    for k in range(5):
        dagger(f"D{k}", T(-1.5 + k * 0.26, -0.62 + (k % 2) * 0.08, zv + 0.03) @ RZ(PI / 2 + (k - 2) * 0.03), K, L=0.85 - abs(k - 2) * 0.05)
    for k in range(4):
        stake(f"St{k}", T(-0.1 + k * 0.24, -0.55 + (k % 2) * 0.1, zv + 0.05) @ RZ(PI / 2 + 0.12 - k * 0.08), K, L=1.0)
    pts = [(math.cos(t) * 0.26 + 1.25, math.sin(t) * 0.3 + 0.2, zv + 0.02) for t in [i / 22 * 2 * PI for i in range(23)]]
    for k, p in enumerate(pts[:-1]):
        sphere(f"Bead{k}", 0.025, p, K["silver"], seg=6, rings=4)
    for k in range(4):
        sphere(f"BeadT{k}", 0.025, (1.25, -0.1 - k * 0.07, zv + 0.02), K["silver"], seg=6, rings=4)
    box("CrossV", (0.05, 0.3, 0.025), (1.25, -0.5, zv + 0.02), K["silver"], bevel=0.005)
    box("CrossH", (0.2, 0.05, 0.025), (1.25, -0.44, zv + 0.02), K["silver"], bevel=0.005)
    # lid frame and glass
    zf, zb = z1 + 0.25, z1 + 0.7
    ang = math.atan2(zb - zf, D)
    Ls = math.hypot(D, zb - zf)
    for sx in (-1, 1):
        prism(f"SideFrame{sx}", [(-D / 2, z1), (D / 2, z1), (D / 2, zb), (-D / 2, zf)], sx * (W / 2 - 0.03), 0.06, ir, plane="YZ", bevel=0.01)
    box("FrontFrame", (W, 0.06, zf - z1), (0, -D / 2 + 0.03, (z1 + zf) / 2), ir, bevel=0.01)
    box("BackFrame", (W, 0.06, zb - z1), (0, D / 2 - 0.03, (z1 + zb) / 2), ir, bevel=0.01)
    box("LidEdgeF", (W, 0.1, 0.06), (0, -D / 2 + 0.03, zf), ir, bevel=0.015)
    box("LidEdgeB", (W, 0.1, 0.06), (0, D / 2 - 0.03, zb), ir, bevel=0.015)
    for k in (-1, 0, 1):
        box(f"Mullion{k}", (0.05, Ls, 0.04), (k * W / 3 * 0.999, 0, (zf + zb) / 2 + 0.01), ir, bevel=0.008, rot=(ang, 0, 0))
    # the cross-hasp: a bar along the lid and one across, padlocked at the front
    box("HaspL", (0.12, Ls + 0.1, 0.05), (0, 0, (zf + zb) / 2 + 0.04), ir, bevel=0.015, rot=(ang, 0, 0))
    box("HaspX", (W + 0.1, 0.12, 0.05), (0, 0, (zf + zb) / 2 + 0.04), ir, bevel=0.015, rot=(ang, 0, 0))
    box("HaspDrop", (0.12, 0.05, 0.4), (0, -D / 2 - 0.03, zf - 0.12), ir, bevel=0.015)
    box("Lock", (0.24, 0.09, 0.26), (0, -D / 2 - 0.09, zf - 0.38), ir, bevel=0.03)
    hoop("Shackle", (0, -D / 2 - 0.09, zf - 0.2), 0.08, "Y", K["steel"], thick=0.02)
    cyl("Keyhole", 0.025, 0.02, (0, -D / 2 - 0.14, zf - 0.4), K["ink"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
    set_group("Glass")
    for k in range(3):
        x = -W / 3 + k * W / 3
        box(f"Pane{k}", (W / 3 - 0.06, Ls - 0.08, 0.02), (x, 0, (zf + zb) / 2), K["glass"], bevel=0.0, rot=(ang, 0, 0))
    box("FrontPane", (W - 0.1, 0.02, zf - z1 - 0.06), (0, -D / 2 + 0.03, (z1 + zf) / 2 + 0.02), K["glass"], bevel=0.0)
    set_group("Main")
    return _dims()


def _kabuto(prefix, loc, K):
    x, y, z = loc
    lathe(f"{prefix}Bowl", [(0, 0), (0.33, 0), (0.33, 0.12), (0.3, 0.3), (0.22, 0.45), (0.1, 0.53), (0, 0.55)], K["saya"], seg=24, loc=(x, y, z),
          flute=(16, 0.04))
    cyl(f"{prefix}Tehen", 0.05, 0.04, (x, y, z + 0.56), K["gilt"], verts=12, bevel=0.01)
    for k in range(3):
        zz = z - 0.02 - k * 0.1
        lathe(f"{prefix}Shikoro{k}", [(0.35 + k * 0.06, zz + 0.04), (0.42 + k * 0.07, zz - 0.06), (0.4 + k * 0.07, zz - 0.08), (0.33 + k * 0.06, zz + 0.02)],
              K["saya"] if k != 1 else K["sayared"], seg=24, loc=(x, y + 0.04, 0))
        hoop(f"{prefix}Lace{k}", (x, y + 0.04, zz - 0.02), 0.39 + k * 0.065, "Z", K["wrap"], thick=0.012)
    for sx in (-1, 1):
        prism(f"{prefix}Fuki{sx}", [(0, 0), (0.18, 0.06), (0.2, 0.22), (0.02, 0.18)], 0, 0.03, K["sayared"], plane="YZ").matrix_world = \
            T(x + sx * 0.33, y - 0.18, z + 0.02) @ RZ(sx * 0.5) @ RY(0)
    box(f"{prefix}Visor", (0.6, 0.18, 0.03), (x, y - 0.32, z + 0.13), K["saya"], bevel=0.01, rot=(0.25, 0, 0))
    pts = []
    for i in range(13):
        t = PI * 1.05 + PI * 0.9 * i / 12
        pts.append((x + math.cos(t) * 0.34, z + 0.62 + math.sin(t) * 0.34))
    for i in range(12, -1, -1):
        t = PI * 1.05 + PI * 0.9 * i / 12
        pts.append((x + math.cos(t) * 0.26, z + 0.66 + math.sin(t) * 0.26))
    prism(f"{prefix}Maedate", pts, y - 0.36, 0.025, K["gilt"], plane="XZ")
    box(f"{prefix}Stalk", (0.06, 0.1, 0.1), (x, y - 0.32, z + 0.3), K["gilt"], bevel=0.01)


def _great_helm(prefix, loc, K):
    x, y, z = loc
    st = K["plate"]
    lathe(f"{prefix}Pot", [(0, 0), (0.3, 0), (0.31, 0.5), (0.27, 0.62), (0.12, 0.68), (0, 0.69)], st, seg=24, loc=(x, y, z), scale=(0.95, 1.0))
    for sx in (-1, 1):
        box(f"{prefix}Eye{sx}", (0.2, 0.06, 0.035), (x + sx * 0.12, y - 0.29, z + 0.42), K["socket"], bevel=0.006)
    box(f"{prefix}CrossV", (0.07, 0.05, 0.55), (x, y - 0.3, z + 0.3), K["gilt"], bevel=0.01)
    box(f"{prefix}CrossH", (0.55, 0.05, 0.06), (x, y - 0.3, z + 0.49), K["gilt"], bevel=0.01)
    for i in range(8):
        cyl(f"{prefix}Br{i}", 0.014, 0.05, (x + 0.08 + (i % 2) * 0.07, y - 0.29, z + 0.12 + (i // 2) * 0.06), K["socket"], rot=(PI / 2, 0, 0), verts=6, bevel=0)
    hoop(f"{prefix}Band", (x, y, z + 0.02), 0.3, "Z", K["gilt"], thick=0.015)


def _sallet(prefix, loc, K):
    x, y, z = loc
    st = K["plate"]
    sphere(f"{prefix}Dome", 0.31, (x, y + 0.02, z + 0.25), st, seg=20, rings=10, scale=(0.95, 1.15, 0.9))
    prism(f"{prefix}Tail", [(-0.12, z + 0.25), (0.2, z + 0.22), (0.5, z - 0.02), (0.44, z - 0.06), (0.1, z + 0.05), (-0.12, z + 0.05)], x, 0.5,
          st, plane="YZ", bevel=0.04)
    box(f"{prefix}Slit", (0.46, 0.08, 0.03), (x, y - 0.3, z + 0.27), K["socket"], bevel=0.008)
    prism(f"{prefix}Bevor", [(-0.22, z - 0.12), (-0.33, z + 0.05), (-0.3, z + 0.2), (-0.15, z + 0.2), (-0.1, z - 0.12)], x, 0.5, st, plane="YZ", bevel=0.04)
    rivet(f"{prefix}Pivot1", x - 0.29, y - 0.05, z + 0.25, K["gilt"], r=0.03)
    rivet(f"{prefix}Pivot2", x + 0.29, y - 0.05, z + 0.25, K["gilt"], r=0.03)


def _hound_helm(prefix, loc, K):
    """A wolf-snouted hunter's bascinet: a pointed skull, a hounskull visor drawn out into a snout, two iron ears."""
    x, y, z = loc
    st = K["gun"]
    lathe(f"{prefix}Skull", [(0, 0), (0.3, 0), (0.31, 0.25), (0.26, 0.5), (0.14, 0.7), (0, 0.84)], st, seg=24, loc=(x, y, z), scale=(0.9, 1.0))
    lathe(f"{prefix}Snout", [(0, 0), (0.22, 0.0), (0.18, 0.2), (0.1, 0.4), (0.0, 0.5)], st, seg=16, loc=(0, 0, 0))
    ob = P.PARTS[-1]
    ob.matrix_world = T(x, y - 0.18, z + 0.28) @ RX(PI / 2)
    for sx in (-1, 1):
        box(f"{prefix}Eye{sx}", (0.1, 0.05, 0.03), (x + sx * 0.12, y - 0.3, z + 0.43), K["socket"], bevel=0.006, rot=(0, sx * 0.3, 0))
        cone(f"{prefix}Ear{sx}", 0.09, 0.0, 0.26, (x + sx * 0.18, y + 0.02, z + 0.68), st, verts=4, rot=(0, sx * 0.4, 0))
    box(f"{prefix}Ridge", (0.03, 0.42, 0.03), (x, y - 0.42, z + 0.37), st, bevel=0.008, rot=(-0.22, 0, 0))
    for k in range(5):
        rivet(f"{prefix}R{k}", x - 0.16 + k * 0.08, y - 0.29, z + 0.06, K["silver"], r=0.02)
    lathe(f"{prefix}Aventail", [(0.3, 0.02), (0.34, -0.14), (0.4, -0.24), (0.0, -0.24)], K["mail"], seg=24, loc=(x, y, z), scale=(0.95, 1.0))


def helm_shelf(M):
    """A two-tier black iron helm shelf on scrolled brackets under a gothic arcade with fleur cresting: a gilt-crossed great
    helm, a lacquered kabuto with a gilt crescent and crimson lacing, a sallet with its bevor, and a wolf-snouted hunter's
    bascinet with iron ears; 5.4 wide, 1.2 deep, 4.9 tall (wall)."""
    K = kit(M)
    ir, br = K["iron"], K["gilt"]
    W = 5.0
    box("Back", (W + 0.2, 0.08, 4.4), (0, -0.04, 2.3), K["crimson"], bevel=0.02)
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.16, 0.12, 4.6), (sx * (W / 2 + 0.05), -0.1, 2.3), ir, bevel=0.02)
    for k, z in enumerate((0.25, 2.45)):
        box(f"Shelf{k}", (W + 0.1, 1.1, 0.1), (0, -0.6, z), ir, bevel=0.02)
        box(f"Lip{k}", (W + 0.1, 0.05, 0.14), (0, -1.15, z + 0.05), br, bevel=0.01)
        for sx in (-1, 0, 1):
            x = sx * (W / 2 - 0.15)
            if k == 0:
                box(f"Corbel{sx}", (0.14, 0.5, 0.2), (x, -0.3, 0.1), ir, bevel=0.02)
                continue
            tube(f"Brk{k}{sx}", [(x, -0.08, z - 0.9), (x, -0.25, z - 0.55), (x, -0.7, z - 0.3), (x, -1.0, z - 0.08)], 0.035, ir)
            tube(f"BrkCurl{k}{sx}", [(x, -0.08, z - 0.9), (x, -0.2, z - 1.0), (x, -0.27, z - 0.88), (x, -0.18, z - 0.8)], 0.025, ir)
        for i in range(2):
            x = -W / 4 + i * W / 2
            pts = [(px, -0.1, pz) for px, pz in arch_xz(x - 0.95, x + 0.95, z + 0.2, 1.65, n=12)]
            tube(f"Arch{k}{i}", pts, 0.04, ir, square=True, poly=True)
            _quatrefoil(f"Foil{k}{i}", x, -0.1, z + 1.55, 0.2, br)
            cyl(f"Peg{k}{i}", 0.1, 0.35 if i else 0.25, (x, -0.6, z + 0.05 + (0.175 if i else 0.125)), ir, verts=12, bevel=0.01)
    # cresting
    box("Crest", (W + 0.3, 0.12, 0.12), (0, -0.1, 4.55), ir, bevel=0.02)
    for k in range(9):
        x = -W / 2 + k * W / 8
        cone(f"Fleur{k}", 0.06, 0.0, 0.28, (x, -0.1, 4.75), br, verts=4)
        for sx in (-1, 1):
            tube(f"FleurC{k}{sx}", [(x, -0.1, 4.62), (x + sx * 0.12, -0.1, 4.7), (x + sx * 0.1, -0.1, 4.84)], 0.018, br)
    _great_helm("GH", (-W / 4, -0.6, 0.55), K)
    _kabuto("KB", (W / 4, -0.6, 0.65), K)
    _sallet("SL", (-W / 4, -0.6, 2.85), K)
    _hound_helm("HH", (W / 4, -0.6, 3.0), K)
    return _dims()


def bolt_barrel(M):
    """An iron-hooped oak barrel of hunting ammunition split by an iron cross divider: silver-headed bolts fletched in crimson
    and bone, longer arrows standing out of one quarter, a SILVER TIPPED brass plate, its lid leaning on the side; 2.2 across,
    2.9 tall."""
    K = kit(M)
    ir = K["iron"]
    H = 1.6
    prof = [(0, 0), (0.55, 0), (0.62, 0.2), (0.68, 0.55), (0.7, 0.8), (0.68, 1.05), (0.62, 1.4), (0.56, H), (0.5, H), (0.5, 0.15), (0, 0.15)]
    lathe("Barrel", prof, K["oakdk"], seg=32, flute=(22, 0.012))
    for z, r in ((0.12, 0.6), (0.45, 0.68), (1.15, 0.67), (1.48, 0.59)):
        hoop(f"Hoop{z}", (0, 0, z), r + 0.01, "Z", ir, thick=0.025)
    for k in range(2):
        box(f"Divider{k}", (1.0, 0.03, 0.7), (0, 0, H - 0.3), ir, bevel=0.005, rot=(0, 0, k * PI / 2))
    box("Plate", (0.5, 0.03, 0.2), (0, -0.705, 0.8), K["brassf"], bevel=0.005)
    label("PlateText", "SILVER TIPPED", K["ink"], 0, -0.722, 0.8, 0.42, 0.09, depth=0.004)
    rnd = random.Random(4610)
    k = 0
    for q in range(4):
        a0 = q * PI / 2
        n = 6 if q != 3 else 4
        for i in range(n):
            a = a0 + rnd.uniform(0.25, PI / 2 - 0.25)
            r = rnd.uniform(0.12, 0.42)
            L = 1.0 if q != 3 else 1.75
            tilt = (rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12))
            fl = K["feltc"] if (i + q) % 2 else K["bone"]
            bolt(f"B{k}", T(math.cos(a) * r, math.sin(a) * r, H - 0.7) @ RX(tilt[0]) @ RY(tilt[1]), K, L=L, fl=fl)
            k += 1
    # lid leaning against the side
    s = _mark()
    cyl("Lid", 0.56, 0.06, (0, 0, 0), K["oakdk"], verts=28, bevel=0.01)
    for sx in (-1, 1):
        box(f"LidBatten{sx}", (0.9, 0.1, 0.05), (0, sx * 0.22, 0.05), K["oak"], bevel=0.01)
    cyl("LidRing", 0.08, 0.03, (0, 0, -0.04), ir, verts=10, bevel=0.005)
    _xform(s, T(0.85, -0.3, 0.56) @ RZ(-0.33) @ RY(1.15))
    return _dims()


def beast_pell(M):
    """A beast-fighting pell for fist and claw training: a leather-hide torso on an iron post with three spring-loaded striking
    arms (coiled springs at the joints), a riveted iron wolf mask for a head, claw-scored hide, on a bolted iron cross foot
    weighed down with sandbags; 2.6 wide, 2.6 deep, 6.4 tall."""
    K = kit(M)
    ir, hd, br = K["iron"], K["hide"], K["brassf"]
    for k in range(2):
        box(f"Foot{k}", (2.4, 0.3, 0.22), (0, 0, 0.11), ir, bevel=0.03, rot=(0, 0, k * PI / 2 + PI / 4))
    for k in range(4):
        a = PI / 4 + k * PI / 2
        cyl(f"Bolt{k}", 0.06, 0.05, (math.cos(a) * 1.0, math.sin(a) * 1.0, 0.24), br, verts=6, bevel=0.005)
    rnd = random.Random(4612)
    for k in range(2):
        a = PI * 0.6 + k * PI * 0.8
        sphere(f"Sandbag{k}", 0.35, (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.42), K["canvas"], seg=14, rings=8, scale=(1.3, 0.8, 0.55))
        tube(f"BagTie{k}", [(math.cos(a) * 0.8 - 0.4, math.sin(a) * 0.8, 0.42), (math.cos(a) * 0.8 - 0.48, math.sin(a) * 0.8, 0.45)], 0.04, K["hemp"])
    cyl("Post", 0.13, 2.4, (0, 0, 1.4), ir, verts=12, bevel=0.01)
    for z in (0.6, 2.4):
        hoop(f"PostBand{z}", (0, 0, z), 0.135, "Z", br, thick=0.02)
    prof = [(0, 2.5), (0.38, 2.5), (0.5, 2.8), (0.56, 3.5), (0.62, 4.2), (0.55, 4.6), (0.32, 4.8), (0, 4.8)]
    lathe("Torso", prof, hd, seg=28, scale=(1.0, 0.8))
    for z in (2.7, 3.4, 4.1):
        hoop(f"Strap{z}", (0, 0, z), 0.56 + (z - 2.7) * 0.06, "Z", K["leather"], thick=0.03).scale = (1, 0.8, 1)
    # claw marks on the hide
    for k in range(4):
        x0 = -0.3 + k * 0.12
        tube(f"Claw{k}", [(x0, -0.47, 3.9), (x0 + 0.1, -0.48, 3.6), (x0 + 0.18, -0.47, 3.3)], 0.016, K["socket"], res=4)
    # arms: two high, one low, on coil springs
    arms = ((-0.3, 4.1, 0.25, -0.35), (0.3, 4.1, -0.25, -0.35), (0.0, 3.3, 0.0, -0.1))
    for k, (x, z, yaw, pitch) in enumerate(arms):
        y0 = -0.42
        s = _mark()
        pts = [(math.cos(i * 0.6) * 0.07, -0.02 * i, math.sin(i * 0.6) * 0.07) for i in range(31)]
        tube(f"Spring{k}", [(px, py, pz) for px, py, pz in pts], 0.014, K["steel"], poly=True)
        cyl(f"Arm{k}", 0.05, 1.1, (0, -0.55 - 0.55, 0), K["ash"], rot=(PI / 2, 0, 0), verts=10, bevel=0.01)
        cyl(f"ArmGrip{k}", 0.065, 0.3, (0, -1.4, 0), K["leather"], rot=(PI / 2, 0, 0), verts=10, bevel=0.015)
        sphere(f"ArmCap{k}", 0.07, (0, -1.66, 0), br, seg=10, rings=6)
        _xform(s, T(x, y0, z) @ RZ(yaw) @ RX(pitch))
    # wolf mask head
    cyl("Neck", 0.14, 0.3, (0, 0, 4.9), ir, verts=12, bevel=0.01)
    hz = 5.4
    sphere("Skull", 0.42, (0, 0, hz), ir, seg=20, rings=12, scale=(0.95, 1.0, 1.0))
    s = _mark()
    lathe("Muzzle", [(0, 0), (0.26, 0.0), (0.22, 0.25), (0.15, 0.45), (0.1, 0.55), (0.0, 0.58)], ir, seg=14, scale=(1.0, 0.75))
    _xform(s, T(0, -0.3, hz - 0.12) @ RX(PI / 2 + 0.12))
    sphere("Nose", 0.07, (0, -0.87, hz - 0.08), K["socket"], seg=10, rings=6, scale=(1.2, 0.8, 0.8))
    box("Jaw", (0.36, 0.42, 0.08), (0, -0.55, hz - 0.33), ir, bevel=0.03, rot=(0.12, 0, 0))
    for sx in (-1, 1):
        cone(f"Ear{sx}", 0.14, 0.0, 0.38, (sx * 0.24, 0.05, hz + 0.45), ir, verts=4, rot=(0.1, sx * 0.35, 0))
        box(f"Eye{sx}", (0.14, 0.06, 0.05), (sx * 0.15, -0.38, hz + 0.08), K["socket"], bevel=0.01, rot=(0, sx * 0.35, 0))
        box(f"Brow{sx}", (0.2, 0.08, 0.06), (sx * 0.15, -0.38, hz + 0.16), ir, bevel=0.02, rot=(0, sx * 0.35, sx * 0.3))
        for j in range(3):
            cone(f"Fang{sx}{j}", 0.025, 0.0, 0.1, (sx * (0.08 + j * 0.05), -0.75 + j * 0.1, hz - 0.3), K["bone"], verts=5, rot=(PI, 0, 0))
    for k in range(9):
        a = -PI * 0.9 + k * PI * 0.8 / 8 - PI * 0.05
        rivet(f"MR{k}", math.cos(a) * 0.4, math.sin(a) * 0.4, hz - 0.15, br, r=0.025)
    return _dims()


def _crossbow(prefix, mtx, K, L=2.4, W=1.6, heavy=False):
    """A crossbow standing on its butt at the origin, stock up +Z, its steel prod across X near the top, the string drawn."""
    s = _mark()
    wd = K["ebony"]
    box(f"{prefix}Stock", (0.14, 0.16, L), (0, 0, L / 2), wd, bevel=0.03)
    box(f"{prefix}Butt", (0.2, 0.22, 0.5), (0, 0.02, 0.25), wd, bevel=0.05)
    box(f"{prefix}Rail", (0.06, 0.05, L * 0.6), (0, -0.09, L * 0.62), K["bone"], bevel=0.008)
    zp = L - 0.2
    pts = [(-W / 2, -0.05, zp - 0.35), (-W / 4, -0.05, zp - 0.06), (0, -0.05, zp), (W / 4, -0.05, zp - 0.06), (W / 2, -0.05, zp - 0.35)]
    tube(f"{prefix}Prod", pts, 0.055 if heavy else 0.04, K["steel"], res=8)
    zn = zp - 0.85
    tube(f"{prefix}String", [(-W / 2, -0.08, zp - 0.35), (0, -0.1, zn), (W / 2, -0.08, zp - 0.35)], 0.012, K["cord"], poly=True)
    box(f"{prefix}Nut", (0.1, 0.08, 0.1), (0, -0.1, zn), K["brassf"], bevel=0.015)
    for sx in (-1, 1):
        box(f"{prefix}Binding{sx}", (0.08, 0.2, 0.18), (sx * 0.08, -0.02, zp), K["leather"], bevel=0.02)
    hoop(f"{prefix}Stirrup", (0, -0.03, L + 0.12), 0.16, "Y", K["iron"], thick=0.025)
    tube(f"{prefix}Trigger", [(0, 0.06, zn - 0.15), (0, 0.25, zn - 0.35), (0, 0.22, zn - 0.85)], 0.025, K["iron"])
    if heavy:
        for sx in (-1, 1):
            cyl(f"{prefix}Windlass{sx}", 0.1, 0.12, (sx * 0.16, 0.0, 0.7), K["iron"], rot=(0, PI / 2, 0), verts=12, bevel=0.01)
            tube(f"{prefix}Crank{sx}", [(sx * 0.22, 0, 0.7), (sx * 0.3, -0.05, 0.7), (sx * 0.3, -0.05, 0.95), (sx * 0.4, -0.1, 0.95)], 0.025, K["iron"], poly=True)
        tube(f"{prefix}Rope", [(-0.12, 0.0, 0.8), (-0.3, -0.06, zp - 0.6), (-W / 2 + 0.1, -0.08, zp - 0.4)], 0.015, K["hemp"])
    _xform(s, mtx)


def crossbow_rack(M):
    """A black iron wall rack of three crossbows standing butt-down, strings drawn: a steel-prod arbalest with its windlass in
    the middle, a hunting crossbow and a light one either side; a leather bolt case of silver bolts along the bottom rail and
    a brass BOLT AND BRACE plate; 5.6 wide, 5.3 tall (wall)."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    for sx in (-1, 1):
        box(f"Stile{sx}", (0.16, 0.12, 5.0), (sx * 2.7, -0.06, 2.5), ir, bevel=0.02)
        finial(f"Fin{sx}", sx * 2.7, -0.06, 5.0, br, s=0.8)
    for z in (0.4, 2.6, 4.7):
        box(f"Rail{z}", (5.5, 0.12, 0.14), (0, -0.06, z), ir, bevel=0.02)
    for k in range(6):
        x = -2.25 + k * 0.9
        tube(f"Lattice{k}", [(x - 0.45, -0.04, 0.4), (x + 0.45, -0.04, 2.6)], 0.022, ir, poly=True)
        tube(f"LatticeB{k}", [(x + 0.45, -0.04, 0.4), (x - 0.45, -0.04, 2.6)], 0.022, ir, poly=True)
    box("Plate", (1.9, 0.04, 0.3), (0, -0.14, 4.95), br, bevel=0.01)
    label("PlateText", "BOLT AND BRACE", K["ink"], 0, -0.162, 4.95, 1.65, 0.16, depth=0.006)
    for x, L, W, heavy in ((-1.75, 2.5, 1.3, False), (0, 3.2, 2.0, True), (1.75, 2.2, 1.1, False)):
        _crossbow(f"X{x}", T(x, -0.32, 1.15), K, L=L, W=W, heavy=heavy)
        for z in (1.95, 1.17 + L - 0.6):
            box(f"Hook{x}{z}", (0.06, 0.32, 0.06), (x, -0.2, z), ir, bevel=0.01)
    # bolt case
    box("Case", (4.0, 0.3, 0.55), (0, -0.3, 0.55), K["leather"], bevel=0.05)
    box("CaseStrap", (4.04, 0.32, 0.08), (0, -0.3, 0.7), K["satchel"], bevel=0.01)
    for k in range(14):
        x = -1.85 + k * 0.285
        bolt(f"CB{k}", T(x, -0.3, 0.42), K, L=0.5, fl=K["feltc"] if k % 2 else K["bone"])
    return _dims()


def hunters_reliquary(M):
    """A limestone reliquary shelf under a pointed arch and silver cross, against the night: holy-water flasks with cross
    stoppers (Glass), tins and pouches of silver shot, a bundle of ash stakes, a jar of wolfsbane, a garlic braid on the jamb
    and a rosary over the top shelf; a brass AGAINST THE NIGHT plate; 3.6 wide, 1.4 deep, 7.6 tall."""
    K = kit(M)
    st, ir, br = K["stone"], K["iron"], K["gilt"]
    W, D = 3.2, 1.2
    zs, apex = 5.6, 6.7
    for sx in (-1, 1):
        box(f"Jamb{sx}", (0.36, D, zs), (sx * (W / 2 - 0.18), 0, zs / 2), st, bevel=0.03)
        box(f"Base{sx}", (0.44, D + 0.1, 0.3), (sx * (W / 2 - 0.18), 0, 0.15), st, bevel=0.03)
    head = [(-W / 2, zs), (-W / 2 + 0.36, zs)] + arch_xz(-W / 2 + 0.36, W / 2 - 0.36, zs, apex - zs - 0.2, n=12)[1:-1] + \
        [(W / 2 - 0.36, zs), (W / 2, zs), (W / 2, apex + 0.1), (-W / 2, apex + 0.1)]
    prism("Head", head, -D / 2 + 0.2, 0.4, st, plane="XZ", bevel=0.02)
    box("HeadTop", (W + 0.1, D, 0.15), (0, 0, apex + 0.17), st, bevel=0.03)
    box("Back", (W - 0.6, 0.1, apex - 0.2), (0, D / 2 - 0.05, (apex - 0.2) / 2 + 0.1), K["crimson"], bevel=0.01)
    # silver cross on top
    box("CrossV", (0.14, 0.12, 0.9), (0, 0, apex + 0.7), K["silver"], bevel=0.02)
    box("CrossH", (0.55, 0.12, 0.14), (0, 0, apex + 0.85), K["silver"], bevel=0.02)
    shelves = (0.35, 2.0, 3.6)
    for k, z in enumerate(shelves):
        box(f"Shelf{k}", (W - 0.6, D - 0.1, 0.12), (0, 0, z), st, bevel=0.02)
    box("Plate", (1.8, 0.04, 0.22), (0, -D / 2 + 0.0, 0.2), br, bevel=0.008)
    label("PlateText", "AGAINST THE NIGHT", K["ink"], 0, -D / 2 - 0.022, 0.2, 1.6, 0.12, depth=0.005)
    # top shelf: holy water flasks
    z = shelves[2] + 0.06
    xs = (-0.95, -0.5, 0.0, 0.5, 0.95)
    for k, x in enumerate(xs):
        h = 0.75 + (k % 2) * 0.15
        set_group("Glass")
        lathe(f"Flask{k}", [(0, 0), (0.16, 0), (0.2, 0.12), (0.2, h * 0.45), (0.1, h * 0.75), (0.06, h * 0.85), (0.06, h), (0, h)], K["glass"], seg=16,
              loc=(x, -0.1, z))
        set_group("Main")
        lathe(f"Water{k}", [(0, 0.02), (0.17, 0.02), (0.18, 0.12), (0.18, h * 0.38), (0, h * 0.38)], K["water"], seg=14, loc=(x, -0.1, z))
        cyl(f"Stop{k}", 0.065, 0.08, (x, -0.1, z + h + 0.03), K["silver"], verts=10, bevel=0.01)
        box(f"StopX{k}", (0.03, 0.03, 0.2), (x, -0.1, z + h + 0.16), K["silver"], bevel=0.005)
        box(f"StopY{k}", (0.12, 0.03, 0.03), (x, -0.1, z + h + 0.19), K["silver"], bevel=0.005)
        hoop(f"Neck{k}", (x, -0.1, z + h * 0.88), 0.07, "Z", K["cord"], thick=0.012)
        box(f"Tag{k}", (0.12, 0.01, 0.16), (x + 0.08, -0.2, z + h * 0.7), K["parch"], bevel=0.003, rot=(0, 0.2, 0))
    # rosary draped over the top shelf edge
    pts = [(-0.8 + i * 0.08, -D / 2 + 0.03, shelves[2] + 0.04 - 0.35 * math.sin(i / 20 * PI)) for i in range(21)]
    for i, p in enumerate(pts):
        sphere(f"Bead{i}", 0.03, p, ir if i % 5 else K["silver"], seg=6, rings=4)
    box("RosCrossV", (0.04, 0.03, 0.22), (0.0, -D / 2 + 0.03, shelves[2] - 0.5), K["silver"], bevel=0.005)
    box("RosCrossH", (0.13, 0.03, 0.04), (0.0, -D / 2 + 0.03, shelves[2] - 0.45), K["silver"], bevel=0.005)
    # middle shelf: silver shot
    z = shelves[1] + 0.06
    cyl("Tin", 0.3, 0.2, (-0.75, -0.1, z + 0.1), K["zinc"], verts=24, bevel=0.01)
    rnd = random.Random(4613)
    for k in range(22):
        a, r = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.24)
        sphere(f"Shot{k}", 0.04, (-0.75 + math.cos(a) * r, -0.1 + math.sin(a) * r, z + 0.22), K["silver"], seg=8, rings=4)
    cyl("TinLid", 0.31, 0.03, (-0.75, 0.25, z + 0.35), K["zinc"], verts=24, bevel=0.005, rot=(1.2, 0, 0))
    for k, x in enumerate((0.05, 0.45, 0.85)):
        sphere(f"Pouch{k}", 0.2, (x, -0.1 + k * 0.05, z + 0.17), K["satchel"], seg=12, rings=8, scale=(1, 0.9, 0.9))
        lathe(f"PouchNeck{k}", [(0, 0), (0.08, 0), (0.12, 0.12), (0, 0.12)], K["satchel"], seg=10, loc=(x, -0.1 + k * 0.05, z + 0.3))
        hoop(f"PouchTie{k}", (x, -0.1 + k * 0.05, z + 0.32), 0.085, "Z", K["cord"], thick=0.015)
    for k in range(3):
        box(f"Box{k}", (0.5, 0.35, 0.16), (0.55, 0.3, z + 0.08 + k * 0.165), K["leather"] if k % 2 else K["satchel"], bevel=0.015)
    # bottom shelf: stakes and wolfsbane
    z = shelves[0] + 0.06
    for k in range(7):
        a = k * 2 * PI / 7
        stake(f"S{k}", T(-0.7 + math.cos(a) * 0.09, -0.1 + math.sin(a) * 0.09, z) @ RY(-PI / 2 + 0.05 * math.cos(a)) @ RX(0.05 * math.sin(a)), K, L=1.3)
    hoop("StakeTie", (-0.7, -0.1, z + 0.6), 0.2, "Z", K["cord"], thick=0.025)
    set_group("Glass")
    lathe("Jar", [(0, 0), (0.28, 0), (0.3, 0.05), (0.3, 0.6), (0.22, 0.7), (0.2, 0.76), (0, 0.76)], K["glass"], seg=18, loc=(0.55, -0.05, z))
    set_group("Main")
    lathe("JarWater", [(0, 0.02), (0.27, 0.02), (0.27, 0.3), (0, 0.3)], K["water"], seg=16, loc=(0.55, -0.05, z))
    for k in range(5):
        a = k * 2 * PI / 5
        top = (0.55 + math.cos(a) * 0.12, -0.05 + math.sin(a) * 0.12, z + 1.1 + 0.1 * (k % 2))
        tube(f"Stem{k}", [(0.55, -0.05, z + 0.1), (0.55 + math.cos(a) * 0.06, -0.05 + math.sin(a) * 0.06, z + 0.7), top], 0.012, K["stem"])
        for j in range(4):
            sphere(f"Bloom{k}{j}", 0.045, (top[0], top[1], top[2] - j * 0.08), K["bane"], seg=8, rings=4, scale=(1, 1, 1.3))
    # garlic braid on the left jamb
    x = -W / 2 + 0.18
    box("Hook", (0.06, 0.25, 0.06), (x, -D / 2 - 0.1, 5.0), ir, bevel=0.01)
    for k in range(7):
        zz = 4.8 - k * 0.24
        for sx in (-1, 1):
            if k % 2 == (0 if sx < 0 else 1):
                lathe(f"Bulb{k}{sx}", [(0, 0), (0.08, 0.02), (0.11, 0.1), (0.08, 0.2), (0.03, 0.26), (0, 0.3)], K["garlic"], seg=10,
                      loc=(x + sx * 0.07, -D / 2 - 0.2, zz - 0.15), flute=(6, 0.08))
    tube("Braid", [(x, -D / 2 - 0.15, 5.0), (x + 0.03, -D / 2 - 0.15, 4.2), (x - 0.02, -D / 2 - 0.15, 3.2)], 0.035, K["straw"])
    return _dims()


def armory_sign(M):
    """The hanging sign: a scrolled wrought-iron bracket off the wall holding a crimson enamel shield on two rings, crossed
    silver katanas over three claw slashes, and IRON VIGIL / ARMOURER in gilt on both faces; 3.6 out from the wall, 3.9
    tall (wall; pivot on the wall plate)."""
    K = kit(M)
    ir, br, cr = K["iron"], K["gilt"], K["crimson"]
    box("WallPlate", (0.6, 0.08, 1.6), (0, -0.04, 2.6), ir, bevel=0.02)
    for z in (2.0, 3.2):
        rivet(f"WP{z}", 0, -0.09, z, br, r=0.05)
    tube("Arm", [(0, -0.05, 3.3), (0, -3.5, 3.3)], 0.06, ir, square=True, poly=True)
    tube("Brace", [(0, -0.05, 2.0), (0, -0.8, 2.3), (0, -1.6, 2.85), (0, -2.4, 3.25)], 0.045, ir, square=True)
    for k, (yc, zc, r) in enumerate(((-0.8, 2.8, 0.28), (-1.5, 3.0, 0.2))):
        pts = [(0, yc + math.cos(t) * r * (1 - t / 12), zc + math.sin(t) * r * (1 - t / 12)) for t in [i * 0.4 for i in range(26)]]
        tube(f"Curl{k}", pts, 0.03, ir, poly=True)
    cone("ArmTip", 0.08, 0.0, 0.3, (0, -3.62, 3.3), ir, verts=4, rot=(PI / 2, 0, 0))
    sphere("ArmKnob", 0.09, (0, -3.47, 3.3), br, seg=10, rings=6)
    for y in (-1.1, -2.9):
        hoop(f"Ring{y}", (0, y, 3.15), 0.12, "X", ir, thick=0.025)
    # the shield board (in the YZ plane)
    h = 2.5
    poly = [(-u + -2.0, w) for u, w in B43.shield_poly(h)]
    sh = prism("Board", [(y, z + 0.4) for y, z in poly], 0, 0.14, cr, plane="YZ", bevel=0.02)
    pts = [(0, y, z + 0.4) for y, z in poly]
    for sx in (-1, 1):
        tube(f"Rim{sx}", [(sx * 0.075, p[1], p[2]) for p in pts + [pts[0]]], 0.03, br, poly=True)
    for sx in (-1, 1):
        for k in range(3):
            tube(f"Slash{sx}{k}", [(sx * 0.072, -2.45 + k * 0.18, 1.95), (sx * 0.072, -2.2 + k * 0.18, 1.35), (sx * 0.072, -2.0 + k * 0.18, 0.95)], 0.025,
                 K["socket"], res=4)
        for j in (-1, 1):
            katana(f"K{sx}{j}", T(sx * 0.1, -2.0, 1.6) @ RZ(PI / 2) @ RY(j * 0.78) @ T(-0.7, 0, 0) @ Matrix.Diagonal((0.45, 0.45, 0.45, 1)),
                   K, L=3.0, sheath=False)
        yz_text(f"T1{sx}", "IRON VIGIL", br, sx * 0.075, -2.0, 2.55, 1.6, 0.26, side=sx)
        yz_text(f"T2{sx}", "ARMOURER", br, sx * 0.075, -2.0, 0.72, 0.8, 0.13, side=sx)
    tube("Chain1", [(0, -1.1, 3.05), (0, -1.1, 2.88)], 0.02, ir, poly=True)
    tube("Chain2", [(0, -2.9, 3.05), (0, -2.9, 2.88)], 0.02, ir, poly=True)
    return _dims()


def claw_gauntlet_display(M):
    """A counter-top display for the fist and claw classes: on a raked black iron stand with a crimson velvet bed, a steel
    Specter-claw gauntlet with three long hooked blades raised on an iron hand-form, a spiked fist gauntlet beside it, a row
    of brass knuckle-dusters on a rail and two rolled crimson hand wraps; 1.9 wide, 1.1 deep, 1.7 tall (plinth)."""
    K = kit(M)
    ir, br = K["iron"], K["gilt"]
    box("Base", (1.8, 1.0, 0.12), (0, 0, 0.06), ir, bevel=0.03)
    prism("Rake", [(-0.45, 0.12), (0.45, 0.12), (0.45, 0.55), (-0.45, 0.25)], 0, 1.7, ir, plane="YZ", bevel=0.02)
    box("Bed", (1.66, 0.95, 0.04), (0, 0, 0.42), K["feltc"], bevel=0.015, rot=(math.atan2(0.3, 0.9), 0, 0))
    for k, (x, kind) in enumerate(((-0.42, "claw"), (0.38, "fist"))):
        s = _mark()
        cyl(f"Form{k}", 0.07, 0.5, (0, 0, 0.25), ir, verts=12, bevel=0.01)
        lathe(f"Cuff{k}", [(0, 0.38), (0.1, 0.38), (0.125, 0.64), (0, 0.64)], K["plate"], seg=16, scale=(1, 0.8))
        box(f"Hand{k}", (0.27, 0.14, 0.3), (0, 0, 0.79), K["plate"], bevel=0.04)
        for j in range(4):
            xx = -0.08 + j * 0.055
            for i in range(2):
                box(f"F{k}{j}{i}", (0.048, 0.1, 0.09), (xx, -0.01, 0.95 + i * 0.09), K["plate"], bevel=0.015)
            if kind == "fist":
                cone(f"Spike{k}{j}", 0.025, 0.0, 0.1, (xx, -0.08, 0.92), K["blade"], verts=4, rot=(PI / 2, 0, 0))
        if kind == "claw":
            for j in range(3):
                xx = -0.07 + j * 0.07
                pts = [(xx, -0.07, 0.85), (xx * 1.2, -0.14, 1.15), (xx * 1.4, -0.16, 1.45), (xx * 1.5, -0.1, 1.62), (xx * 1.5, 0.0, 1.66)]
                for i, (a, b) in enumerate(zip(pts, pts[1:])):
                    r = 0.03 - i * 0.006
                    tube(f"Claw{j}{i}", [a, b], r, K["blade"], square=True, poly=True)
                box(f"ClawMount{j}", (0.06, 0.06, 0.12), (xx, -0.07, 0.82), br, bevel=0.01)
        else:
            for j in range(4):
                rivet(f"Knuckle{j}", -0.08 + j * 0.055, -0.065, 0.8, br, r=0.025)
        _xform(s, T(x, 0.12, 0.3) @ RZ(0.2 if kind == "claw" else -0.25))
    # knuckle dusters on a rail
    box("RailBar", (1.3, 0.04, 0.04), (0, -0.42, 0.42), br, bevel=0.005)
    for sx in (-1, 1):
        box(f"RailPost{sx}", (0.04, 0.04, 0.3), (sx * 0.65, -0.42, 0.27), br, bevel=0.005)
    for k in range(3):
        x = -0.4 + k * 0.4
        s = _mark()
        box(f"KD{k}", (0.3, 0.03, 0.06), (0, 0, 0.0), br, bevel=0.01)
        for j in range(4):
            hoop(f"KDR{k}{j}", (-0.11 + j * 0.073, 0, 0.06), 0.035, "Y", br, thick=0.012)
        _xform(s, T(x, -0.44, 0.38))
    for k, x in enumerate((-0.74, 0.74)):
        cyl(f"Wrap{k}", 0.08, 0.22, (x, -0.2, 0.42), K["wrap"], rot=(0, PI / 2, 0), verts=14, bevel=0.02)
        box(f"WrapTail{k}", (0.2, 0.25, 0.012), (x, -0.36, 0.3), K["wrap"], bevel=0.0, rot=(math.atan2(0.3, 0.9), 0, 0))
    return _dims()


# ================================================================== SPELL SHOP

def potion(prefix, kind, loc, K, liquid, liq_group="Glow", glass_group="Glass", h=0.5, glass=None):
    """A potion bottle of shape `kind` (round, tall, cone, bulb, square, heart) standing at loc, `h` tall to the shoulder:
    its glass in `glass_group`, its liquid (material `liquid`) in `liq_group`, the cork and wax in Main."""
    x, y, z = loc
    k = h / 0.6
    g = glass or K["glass"]
    profs = {
        "round": [(0, 0), (0.15, 0), (0.22, 0.12), (0.22, 0.26), (0.12, 0.4), (0.05, 0.46), (0.05, 0.6), (0.06, 0.62), (0, 0.62)],
        "tall": [(0, 0), (0.08, 0), (0.09, 0.05), (0.09, 0.62), (0.05, 0.7), (0.04, 0.82), (0.05, 0.84), (0, 0.84)],
        "cone": [(0, 0), (0.2, 0), (0.18, 0.06), (0.06, 0.4), (0.04, 0.52), (0.05, 0.54), (0, 0.54)],
        "bulb": [(0, 0), (0.08, 0), (0.18, 0.08), (0.2, 0.2), (0.14, 0.32), (0.05, 0.38), (0.04, 0.52), (0.055, 0.55), (0, 0.55)],
    }
    set_group(glass_group)
    if kind == "heart":
        pts = [(math.sin(t) ** 3 * 0.2 * k, (0.8125 * math.cos(t) - 0.3125 * math.cos(2 * t) - 0.125 * math.cos(3 * t) - 0.0625 * math.cos(4 * t)) * 0.2 * k)
               for t in [i / 28 * 2 * PI for i in range(28)]]
        zmin = min(p[1] for p in pts)
        prism(f"{prefix}Body", [(x + u, z + w - zmin) for u, w in pts], y, 0.16 * k, g, plane="XZ", bevel=0.01)
        top = z + max(p[1] for p in pts) - zmin - 0.03 * k
        cyl(f"{prefix}Neck", 0.04 * k, 0.14 * k, (x, y, top + 0.07 * k), g, verts=10, bevel=0.0)
        top += 0.14 * k
        set_group(liq_group)
        prism(f"{prefix}Liquid", [(x + u * 0.8, z + (w - zmin) * 0.8 + 0.02 * k) for u, w in pts if (w - zmin) * 0.8 < 0.2 * k] or [(x, z), (x + 0.1, z), (x, z + 0.1)],
              y, 0.12 * k, liquid, plane="XZ")
    elif kind == "square":
        wv = 0.17 * k
        box(f"{prefix}Body", (wv * 2, wv * 1.4, 0.4 * k), (x, y, z + 0.2 * k), g, bevel=0.02)
        cyl(f"{prefix}Neck", 0.045 * k, 0.16 * k, (x, y, z + 0.48 * k), g, verts=10, bevel=0.0)
        top = z + 0.56 * k
        set_group(liq_group)
        box(f"{prefix}Liquid", (wv * 1.8, wv * 1.2, 0.26 * k), (x, y, z + 0.14 * k), liquid, bevel=0.01)
    else:
        prof = [(r * k, zz * k) for r, zz in profs[kind]]
        lathe(f"{prefix}Body", prof, g, seg=16, loc=(x, y, z))
        top = z + prof[-1][1]
        lim = prof[-1][1] * 0.55
        lp = [(r * 0.86, zz) for r, zz in prof[1:] if zz < lim]
        set_group(liq_group)
        lathe(f"{prefix}Liquid", [(0, 0.015 * k), (lp[0][0], 0.015 * k)] + lp[1:] + [(lp[-1][0], lim), (0, lim)], liquid, seg=14, loc=(x, y, z))
    set_group("Main")
    cyl(f"{prefix}Cork", 0.04 * k, 0.08 * k, (x, y, top + 0.02 * k), K["cork"], verts=8, bevel=0.008)
    sphere(f"{prefix}Wax", 0.05 * k, (x, y, top + 0.065 * k), K["sealwax"], seg=8, rings=4, scale=(1, 1, 0.5))
    return top


def grimoire(prefix, mtx, cover, K, ajar=0.4, w=0.8, d=0.6):
    """A grimoire lying with its spine on -X, its top board ajar by `ajar` radians, a glowing sigil on the top board (Glow),
    gilt corners and a clasp ring at the spine for the chain."""
    s = _mark()
    t = 0.045
    box(f"{prefix}Low", (w, d, t), (0, 0, t / 2), cover, bevel=0.012)
    box(f"{prefix}Block", (w - 0.06, d - 0.05, 0.13), (0.01, 0, t + 0.065), K["paper"], bevel=0.01)
    box(f"{prefix}Spine", (0.07, d, 0.24), (-w / 2, 0, 0.11), cover, bevel=0.025)
    for k in range(3):
        box(f"{prefix}Band{k}", (0.08, 0.03, 0.25), (-w / 2, -d * 0.3 + k * d * 0.3, 0.11), K["gilt"], bevel=0.006)
    for k in range(3):
        a = ajar * (k + 1) / 4
        pg = box(f"{prefix}Leaf{k}", (w - 0.08, d - 0.07, 0.008), (0, 0, 0), K["parch"], bevel=0.0)
        pg.matrix_world = T(-w / 2 + 0.03, 0, t + 0.13) @ RY(-a) @ T((w - 0.08) / 2, 0, 0)
    q = _mark()
    box(f"{prefix}Top", (w, d, t), (w / 2, 0, t / 2), cover, bevel=0.012)
    for sx in (0.06, w - 0.06):
        for sy in (-1, 1):
            box(f"{prefix}Corner{sx}{sy}", (0.1, 0.1, t + 0.012), (sx, sy * (d / 2 - 0.05), t / 2), K["gilt"], bevel=0.008)
    set_group("Glow")
    hoop(f"{prefix}SigilRing", (w / 2, 0, t + 0.006), 0.16, "Z", K["g_violet"], thick=0.012)
    tri = [(w / 2 + math.cos(a) * 0.16, math.sin(a) * 0.16, t + 0.006) for a in (PI / 2, PI / 2 + 2 * PI / 3, PI / 2 + 4 * PI / 3, PI / 2)]
    tube(f"{prefix}SigilTri", tri, 0.01, K["g_violet"], poly=True)
    sphere(f"{prefix}SigilEye", 0.035, (w / 2, 0, t + 0.01), K["g_violet"], seg=8, rings=4, scale=(1.4, 1, 0.4))
    set_group("Main")
    _xform(q, T(-w / 2, 0, t + 0.13) @ RY(-ajar))
    hoop(f"{prefix}Clasp", (-w / 2 - 0.06, 0, 0.11), 0.06, "Y", K["iron"], thick=0.015)
    _xform(s, mtx)
    return mtx @ Vector((-w / 2 - 0.1, 0, 0.11))


def tethered_grimoires(M):
    """Five grimoires that will not stay shelved: they float over an octagonal black marble plinth, straining upward at the
    taut iron chains that moor them to its bollards, boards ajar and loose pages drifting, a violet sigil glowing on each cover
    and a glowing rune ring set in the plinth (Glow); 2.8 across, 6.4 tall."""
    K = kit(M)
    mb, ir, br = K["marble"], K["iron"], K["gilt"]
    cyl("Plinth", 1.35, 0.4, (0, 0, 0.2), mb, verts=8, bevel=0.04)
    cyl("Step", 1.15, 0.3, (0, 0, 0.55), mb, verts=8, bevel=0.04)
    hoop("Band", (0, 0, 0.4), 1.33, "Z", br, thick=0.02)
    covers = [K["leather"], K["inkleather"], K["plum"], K["satchel"], B24.leather("GrimoireGreen", (0.03, 0.08, 0.05), scale=4.0, wear=0.3)]
    rnd = random.Random(4620)
    heights = (2.4, 4.4, 3.2, 5.4, 3.8)
    for k in range(5):
        a = k * 2 * PI / 5 - PI / 2 - 0.35
        px, py = math.cos(a) * 0.95, math.sin(a) * 0.95
        z = heights[k]
        x, y = math.cos(a + 0.25) * (0.75 + 0.06 * k), math.sin(a + 0.25) * (0.75 + 0.06 * k)
        cyl(f"Bollard{k}", 0.09, 0.32, (px, py, 0.86), ir, verts=10, bevel=0.015)
        sphere(f"BollardCap{k}", 0.1, (px, py, 1.03), br, seg=10, rings=6, scale=(1, 1, 0.6))
        hoop(f"BollardRing{k}", (px, py, 1.1), 0.06, "X", ir, thick=0.015)
        yaw = a + PI
        mtx = T(x, y, z) @ RZ(yaw) @ RX(rnd.uniform(-0.25, 0.25)) @ RY(rnd.uniform(-0.3, 0.1))
        end = grimoire(f"G{k}", mtx, covers[k], K, ajar=rnd.uniform(0.25, 0.6))
        chain(f"Ch{k}", [(px, py, 1.12), tuple(end)], ir, r=0.08, thick=0.016)
    for k in range(4):
        a = rnd.uniform(0, 2 * PI)
        pg = box(f"Page{k}", (0.42, 0.32, 0.006), (0, 0, 0), K["parch"], bevel=0.0)
        pg.matrix_world = T(math.cos(a) * 0.9, math.sin(a) * 0.9, 2.6 + k * 0.9) @ RZ(a) @ RX(rnd.uniform(-0.6, 0.6)) @ RY(rnd.uniform(-0.5, 0.5))
    set_group("Glow")
    hoop("RuneRing", (0, 0, 0.705), 0.85, "Z", K["g_violet"], thick=0.02)
    for k in range(10):
        a = k * PI / 5
        c, s_ = math.cos(a), math.sin(a)
        pts = [(c * 0.95 - s_ * 0.05, s_ * 0.95 + c * 0.05, 0.705), (c * 1.05, s_ * 1.05, 0.705), (c * 0.95 + s_ * 0.05, s_ * 0.95 - c * 0.05, 0.705)]
        tube(f"Rune{k}", pts, 0.012, K["g_violet"], poly=True)
    set_group("Main")
    return _dims()


def potion_honeycomb(M):
    """A brass honeycomb wall of potions: 21 hexagonal cells backed in night-violet enamel, each holding a different bottle
    (round, tall, cone, bulb, square, heart) of glowing violet or green elixir (Glow, Glow2), a gilt crescent on top and an
    ELIXIRS plate below; 5.6 wide, 0.6 deep, 5.0 tall (wall)."""
    K = kit(M)
    br = K["brassf"]
    R = 0.55
    dx, dz = 1.5 * R, math.sqrt(3) * R
    kinds = ("round", "tall", "cone", "bulb", "square", "heart")
    rnd = random.Random(4621)
    k = 0
    for c in range(6):
        rows = 4 if c % 2 == 0 else 3
        for r in range(rows):
            x = -2.5 * dx + c * dx
            z = 0.55 + R * math.sqrt(3) / 2 + r * dz + (dz / 2 if c % 2 else 0)
            hexp = [(x + math.cos(i * PI / 3) * R, z + math.sin(i * PI / 3) * R) for i in range(6)]
            prism(f"Back{k}", hexp, -0.04, 0.08, K["night"], plane="XZ")
            for i in range(6):
                a0, a1 = i * PI / 3, (i + 1) * PI / 3
                mx, mz = x + math.cos((a0 + a1) / 2) * R * 0.866, z + math.sin((a0 + a1) / 2) * R * 0.866
                box(f"Wall{k}{i}", (R + 0.04, 0.5, 0.05), (mx, -0.3, mz), br, bevel=0.0, rot=(0, -((a0 + a1) / 2 + PI / 2), 0))
            kind = kinds[rnd.randrange(len(kinds))]
            liq, grp = (K["g_violet"], "Glow") if rnd.random() < 0.55 else (K["g_green"], "Glow2")
            h = 0.42 if kind in ("tall",) else 0.5
            potion(f"B{k}", kind, (x + rnd.uniform(-0.05, 0.05), -0.3, z - R * 0.866 + 0.025), K, liq, liq_group=grp, h=h)
            k += 1
    zt = 0.55 + 4 * dz
    pts = []
    for i in range(17):
        t = PI * 1.1 + PI * 0.8 * i / 16
        pts.append((math.cos(t) * 0.55, zt + 0.42 + math.sin(t) * 0.55))
    for i in range(16, -1, -1):
        t = PI * 1.1 + PI * 0.8 * i / 16
        pts.append((math.cos(t) * 0.42, zt + 0.52 + math.sin(t) * 0.42))
    prism("Crescent", pts, -0.2, 0.06, K["gilt"], plane="XZ")
    box("CrescentFoot", (0.16, 0.2, 0.3), (0, -0.2, zt - 0.08), K["gilt"], bevel=0.01)
    box("Plate", (1.6, 0.04, 0.3), (0, -0.3, 0.3), K["gilt"], bevel=0.01)
    label("PlateText", "ELIXIRS", K["ink"], 0, -0.322, 0.3, 1.2, 0.17, depth=0.006)
    box("Sill", (5.4, 0.6, 0.1), (0, -0.3, 0.5), K["night"], bevel=0.02)
    return _dims()


def scrying_orb_stand(M):
    """A scrying orb held up in a cupped bronze hand on a three-strand twisted bronze column: the orb (Glass) holds a spiral
    of pale mist round a bright core (Glow), and three silver moon-phase lenses on curling arms circle it; 2.4 across,
    5.0 tall."""
    K = kit(M)
    mb, bz, br = K["marble"], K["bronze"], K["gilt"]
    cyl("Base", 0.95, 0.25, (0, 0, 0.125), mb, verts=32, bevel=0.03)
    cyl("Base2", 0.75, 0.2, (0, 0, 0.35), mb, verts=32, bevel=0.03)
    hoop("BaseBand", (0, 0, 0.25), 0.95, "Z", br, thick=0.02)
    cyl("Core", 0.08, 2.9, (0, 0, 1.9), bz, verts=10, bevel=0.0)
    for k in range(3):
        pts = [(math.cos(k * 2 * PI / 3 + t * 0.35) * 0.13, math.sin(k * 2 * PI / 3 + t * 0.35) * 0.13, 0.45 + t * 0.1) for t in range(30)]
        tube(f"Strand{k}", pts, 0.055, bz, poly=True)
    lathe("Collar", [(0, 3.3), (0.2, 3.3), (0.26, 3.4), (0.16, 3.5), (0.12, 3.62), (0, 3.62)], bz, seg=20)
    zc = 4.25
    # hand: palm and curled fingers round the orb
    sphere("Palm", 0.32, (0, 0, 3.75), bz, seg=18, rings=10, scale=(1.0, 0.85, 0.45))
    for k in range(4):
        a = -PI / 2 + (k - 1.5) * 0.55 + PI
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Finger{k}", [(c * 0.22, s_ * 0.22, 3.8), (c * 0.42, s_ * 0.42, 3.95), (c * 0.5, s_ * 0.5, 4.2), (c * 0.46, s_ * 0.46, 4.42)], 0.055 - abs(k - 1.5) * 0.006,
             bz, res=6)
    tube("Thumb", [(0.1, -0.2, 3.8), (0.25, -0.38, 3.95), (0.3, -0.45, 4.15)], 0.06, bz, res=6)
    # moon lenses
    for k in range(3):
        a = PI / 6 + k * 2 * PI / 3
        c, s_ = math.cos(a), math.sin(a)
        tube(f"LensArm{k}", [(c * 0.15, s_ * 0.15, 3.45), (c * 0.6, s_ * 0.6, 3.5), (c * 0.95, s_ * 0.95, 3.9), (c * 1.0, s_ * 1.0, zc)], 0.025, br)
        mtx = T(c * 1.02, s_ * 1.02, zc + 0.08) @ RZ(a + PI / 2)
        s = _mark()
        hoop(f"LensRing{k}", (0, 0, 0), 0.14, "Y", br, thick=0.02)
        cyl(f"Lens{k}", 0.13, 0.02, (0, 0, 0), K["silver"], rot=(PI / 2, 0, 0), verts=20, bevel=0.0)
        if k < 2:
            cyl(f"Shade{k}", 0.13, 0.024, (0.09 if k == 0 else 0.0, 0, 0), K["ink"], rot=(PI / 2, 0, 0), verts=20, bevel=0.0)
        _xform(s, mtx)
    set_group("Glass")
    sphere("Orb", 0.55, (0, 0, zc), K["glass"], seg=32, rings=16)
    set_group("Glow")
    sphere("Spark", 0.1, (0, 0, zc), K["g_pale"], seg=12, rings=8)
    for k in range(2):
        pts = [(math.cos(k * PI + t * 0.5) * (0.05 + t * 0.022), math.sin(k * PI + t * 0.5) * (0.05 + t * 0.022), zc + math.sin(t * 0.4) * 0.05) for t in range(18)]
        tube(f"Mist{k}", pts, 0.022, K["g_pale"], poly=True)
    set_group("Main")
    return _dims()


def wand_coffin(M):
    """A coffin-shaped wand case stood up on a black iron easel, leaning back: black lacquer with gilt corner fittings, seven
    wands of ebony, bone, twisted oak, silver and crystal laid across in plum velvet behind a coffin-shaped glass front
    (Glass) with a brass cross, the crystal-tipped wand glowing (Glow), and a WANDS CHOOSE plate on the ledge; 1.6 wide,
    1.9 deep, 4.2 tall."""
    K = kit(M)
    ir, br, lq = K["iron"], K["gilt"], K["saya"]
    outline = [(-1.8, -0.32), (0.9, -0.62), (1.8, -0.4), (1.8, 0.4), (0.9, 0.62), (-1.8, 0.32)]

    def inset(poly, k):
        return [(u * k, w * (k - 0.04)) for u, w in poly]
    z0, z1 = 0.0, 0.4
    s0 = _mark()
    prism("Case", outline, z0, z1 - z0, lq, plane="XY", bevel=0.03)
    prism("Velvet", inset(outline, 0.93), z1 - 0.06, 0.06, K["plum"], plane="XY", bevel=0.01)
    for u, w in outline:
        box(f"Corner{u}{w}", (0.16, 0.16, z1 - z0 + 0.04), (u * 0.985, w * 0.97, (z0 + z1) / 2), br, bevel=0.02)
    pts = [(u, w, z1 + 0.02) for u, w in outline]
    tube("Rim", pts + [pts[0]], 0.035, br, poly=True)
    box("LidBar", (0.1, 1.2, 0.05), (0.9, 0, z1 + 0.1), br, bevel=0.01)
    box("LidBarL", (2.6, 0.1, 0.05), (0.1, 0, z1 + 0.1), br, bevel=0.01)
    sphere("LidStud", 0.07, (0.9, 0, z1 + 0.14), br, seg=10, rings=6)
    woods = [K["ebony"], K["bone"], K["oak"], K["silver"], K["ebony"], K["oakdk"], K["quartz"]]
    for k in range(7):
        x = -1.35 + k * 0.42
        half = 0.32 + 0.3 * (x + 1.8) / 2.7 if x < 0.9 else 0.62 - 0.22 * (x - 0.9) / 0.9
        L = half * 2 * 0.82
        s = _mark()
        cyl(f"Slot{k}", 0.05, L + 0.06, (0, 0, 0), K["plum"], rot=(PI / 2, 0, 0), verts=8, bevel=0.0)
        prof = [(0, 0), (0.04, 0), (0.045, 0.06), (0.035, L * 0.3), (0.04, L * 0.33), (0.022, L * 0.36), (0.012, L), (0, L + 0.01)]
        if k == 2:
            lathe(f"Wand{k}", prof, woods[k], seg=8, jitter=(0.15, k))
        else:
            lathe(f"Wand{k}", prof, woods[k], seg=8, flute=(4, 0.15) if k == 5 else None)
        hoop(f"WandBand{k}", (0, 0, L * 0.33), 0.04, "Z", br, thick=0.008)
        if k == 6:
            set_group("Glow")
            cone(f"WandTip{k}", 0.03, 0.0, 0.12, (0, 0, L + 0.06), K["g_violet"], verts=6)
            set_group("Main")
        for ob in P.PARTS[s + 1:]:
            ob.matrix_world = RX(PI / 2) @ T(0, 0, -L / 2) @ ob.matrix_world
        _xform(s, T(x, 0, z1 + 0.04))
    set_group("Glass")
    prism("Lid", inset(outline, 0.99), z1 + 0.03, 0.03, K["glass"], plane="XY")
    set_group("Main")
    lean = -0.22
    _xform(s0, T(0, 0.1, 2.25) @ RX(lean) @ RZ(PI / 2) @ RY(-PI / 2) @ T(0, 0, -0.2))
    # the easel
    box("Ledge", (1.5, 0.7, 0.12), (0, -0.25, 0.32), ir, bevel=0.02)
    box("LedgeLip", (1.5, 0.06, 0.16), (0, -0.6, 0.4), br, bevel=0.01)
    box("Plate", (1.0, 0.03, 0.12), (0, -0.64, 0.4), br, bevel=0.004)
    label("PlateText", "WANDS CHOOSE", K["ink"], 0, -0.66, 0.4, 0.85, 0.08, depth=0.004)
    for sx in (-1, 1):
        tube(f"FrontLeg{sx}", [(sx * 0.6, -0.5, 0.0), (sx * 0.5, -0.25, 0.32)], 0.04, ir, poly=True)
        tube(f"Rail{sx}", [(sx * 0.55, -0.35, 0.3), (sx * 0.5, 0.75, 4.15)], 0.045, ir, poly=True)
        tube(f"BackLeg{sx}", [(sx * 0.4, 1.3, 0.0), (sx * 0.2, 0.62, 3.1)], 0.04, ir, poly=True)
        sphere(f"FootBall{sx}", 0.07, (sx * 0.6, -0.5, 0.05), br, seg=8, rings=6)
        sphere(f"BackFoot{sx}", 0.07, (sx * 0.4, 1.3, 0.05), br, seg=8, rings=6)
        finial(f"RailFin{sx}", sx * 0.5, 0.75, 4.15, br, s=0.5)
    tube("BackStay", [(-0.25, 0.8, 2.6), (0.25, 0.8, 2.6)], 0.035, ir, poly=True)
    tube("Spreader", [(-0.38, 1.22, 0.4), (0.38, 1.22, 0.4)], 0.03, ir, poly=True)
    return _dims()


def rune_stone_table(M):
    """A rune-casting table: a round slate top on three squared standing stones, a glowing rune ring cut round its rim (Glow),
    a brass casting bowl, scattered carved rune stones and a velvet bag, and three stones hanging in the air over the centre,
    their runes lit (Glow); 3.0 across, 3.6 tall."""
    K = kit(M)
    st, sl, br = K["stone"], K["slate"], K["gilt"]
    for k in range(3):
        a = PI / 2 + k * 2 * PI / 3
        x, y = math.cos(a) * 0.75, math.sin(a) * 0.75
        cone(f"Stone{k}", 0.34, 0.24, 2.3, (x, y, 1.15), M["stonedark"], verts=4, rot=(0, 0, a + PI / 4))
        box(f"StoneCap{k}", (0.42, 0.42, 0.1), (x, y, 2.3), st, bevel=0.03, rot=(0, 0, a + PI / 4))
    cyl("Top", 1.45, 0.18, (0, 0, 2.44), sl, verts=48, bevel=0.03)
    hoop("TopEdge", (0, 0, 2.44), 1.45, "Z", br, thick=0.02)
    lathe("Bowl", [(0, 0), (0.2, 0), (0.32, 0.12), (0.34, 0.18), (0.3, 0.17), (0.18, 0.06), (0, 0.06)], br, seg=24, loc=(0, 0, 2.53))
    rnd = random.Random(4622)
    for k in range(8):
        a, r = rnd.uniform(0, 2 * PI), rnd.uniform(0.45, 0.95)
        x, y = math.cos(a) * r, math.sin(a) * r
        sphere(f"Pebble{k}", 0.11, (x, y, 2.56), st, seg=10, rings=6, scale=(1.0, 0.8, 0.4)).rotation_euler[2] = a
        tube(f"Mark{k}", [(x - 0.04, y - 0.02, 2.6), (x, y + 0.04, 2.605), (x + 0.04, y - 0.02, 2.6)], 0.01, K["socket"], poly=True)
    sphere("Bag", 0.2, (0.75, -0.6, 2.67), K["plum"], seg=12, rings=8, scale=(1, 1, 0.8))
    lathe("BagNeck", [(0, 0), (0.06, 0), (0.1, 0.1), (0, 0.1)], K["plum"], seg=10, loc=(0.75, -0.6, 2.8))
    hoop("BagTie", (0.75, -0.6, 2.82), 0.065, "Z", K["gilt"], thick=0.012)
    floats = [(-0.15, -0.1, 3.05), (0.2, 0.1, 3.3), (-0.05, 0.15, 3.55)]
    for k, (x, y, z) in enumerate(floats):
        sphere(f"Float{k}", 0.14, (x, y, z), st, seg=12, rings=8, scale=(1.0, 0.45, 1.2))
    set_group("Glow")
    for k, (x, y, z) in enumerate(floats):
        tube(f"FloatRune{k}", [(x - 0.05, y - 0.065, z + 0.08), (x + 0.03, y - 0.066, z), (x - 0.05, y - 0.065, z - 0.08)], 0.014, K["g_teal"], poly=True)
        tube(f"FloatRuneB{k}", [(x + 0.04, y - 0.066, z + 0.1), (x + 0.04, y - 0.066, z - 0.1)], 0.014, K["g_teal"], poly=True)
    hoop("RuneRing", (0, 0, 2.535), 1.2, "Z", K["g_teal"], thick=0.016)
    for k in range(16):
        a = k * PI / 8
        c, s_ = math.cos(a), math.sin(a)
        shape = k % 4
        r0, r1 = 1.26, 1.4
        if shape == 0:
            pts = [(c * r0, s_ * r0), (c * r1, s_ * r1), (c * 1.33 + s_ * 0.05, s_ * 1.33 - c * 0.05)]
        elif shape == 1:
            pts = [(c * r0 - s_ * 0.04, s_ * r0 + c * 0.04), (c * r1, s_ * r1), (c * r0 + s_ * 0.04, s_ * r0 - c * 0.04)]
        elif shape == 2:
            pts = [(c * r0 + s_ * 0.04, s_ * r0 - c * 0.04), (c * r1 - s_ * 0.04, s_ * r1 + c * 0.04), (c * r1 + s_ * 0.04, s_ * r1 - c * 0.04)]
        else:
            pts = [(c * r0, s_ * r0), (c * r1, s_ * r1)]
        tube(f"Rune{k}", [(u, w, 2.535) for u, w in pts], 0.012, K["g_teal"], poly=True)
    set_group("Main")
    return _dims()


def scroll_carousel(M):
    """A revolving brass scroll carousel: three tiers of night-enamel trays on a bronze tripod and centre post, rolled scrolls
    standing in each tier's gallery with coloured wax seals and ribbons, crowned by a crescent moon cradling a glowing star
    (Glow); 2.2 across, 6.6 tall."""
    K = kit(M)
    br, bz = K["brassf"], K["bronze"]
    tripod("Foot", 1.0, K, mat=bz)
    cyl("Post", 0.06, 5.2, (0, 0, 3.0), br, verts=10, bevel=0.0)
    seals = [K["sealwax"], K["violet"], K["athblue"], K["gilt"], K["j_Rovers"]]
    rnd = random.Random(4623)
    for t, (z, R) in enumerate(((1.2, 0.95), (2.75, 0.8), (4.2, 0.62))):
        cyl(f"Tray{t}", R, 0.08, (0, 0, z), K["night"], verts=32, bevel=0.015)
        hoop(f"Gallery{t}", (0, 0, z + 0.35), R - 0.02, "Z", br, thick=0.018)
        hoop(f"TrayRim{t}", (0, 0, z + 0.04), R, "Z", br, thick=0.02)
        n = int(R * 14)
        for k in range(n):
            a = k * 2 * PI / n
            tube(f"Bal{t}{k}", [(math.cos(a) * (R - 0.02), math.sin(a) * (R - 0.02), z + 0.04), (math.cos(a) * (R - 0.02), math.sin(a) * (R - 0.02), z + 0.35)],
                 0.008, br, poly=True)
        m = int(R * 11)
        for k in range(m):
            a = k * 2 * PI / m + t * 0.3
            r = R - 0.16
            L = rnd.uniform(0.6, 0.9)
            tilt = 0.18
            s = _mark()
            cyl(f"Scroll{t}{k}", 0.07, L, (0, 0, L / 2), K["parch"], verts=12, bevel=0.01)
            for zz in (0.0, L):
                cyl(f"ScrEnd{t}{k}{zz}", 0.04, 0.04, (0, 0, zz), K["oakdk"], verts=8, bevel=0.0)
            cyl(f"Ribbon{t}{k}", 0.075, 0.05, (0, 0, L * 0.6), K["silk"] if k % 2 else K["indigo"], verts=12, bevel=0.0)
            cyl(f"Seal{t}{k}", 0.045, 0.02, (0, -0.08, L * 0.6), seals[(k + t) % len(seals)], rot=(PI / 2, 0, 0), verts=10, bevel=0.0)
            _xform(s, T(math.cos(a) * r, math.sin(a) * r, z + 0.04) @ RZ(a + PI / 2) @ RX(-tilt))
        if t < 2:
            for k in range(3):
                a = k * 2 * PI / 3 + PI / 6
                tube(f"Rib{t}{k}", [(0, 0, z + 0.1), (math.cos(a) * 0.25, math.sin(a) * 0.25, z + 0.5), (math.cos(a) * 0.12, math.sin(a) * 0.12, z + 0.9)], 0.02, br)
    # crescent and star on top
    zt = 5.9
    pts = []
    for i in range(17):
        t = -PI * 0.85 + PI * 1.7 * i / 16
        pts.append((math.sin(t) * 0.45, zt - math.cos(t) * 0.45))
    for i in range(16, -1, -1):
        t = -PI * 0.85 + PI * 1.7 * i / 16
        pts.append((math.sin(t) * 0.34, zt + 0.1 - math.cos(t) * 0.34))
    prism("Crescent", pts, 0, 0.06, K["gilt"], plane="XZ")
    tube("StarHang", [(0, 0, zt + 0.45), (0, 0, zt + 0.12)], 0.008, br, poly=True)
    set_group("Glow")
    star = []
    for i in range(10):
        a = PI / 2 + i * PI / 5
        r = 0.16 if i % 2 == 0 else 0.07
        star.append((math.cos(a) * r, zt + math.sin(a) * r))
    prism("Star", star, 0, 0.05, K["g_pale"], plane="XZ")
    set_group("Main")
    return _dims()


def candle(prefix, loc, h, r, K, drip=0.0):
    """A pillar candle of wax standing at loc, h tall: a burned-down cupped top, a wick and a violet flame (Glow), and (drip)
    a run of wax down its side and onto whatever is below."""
    x, y, z = loc
    lathe(f"{prefix}Wax", [(0, 0), (r, 0), (r, h - 0.03), (r * 0.9, h), (r * 0.5, h - 0.04), (0, h - 0.03)], K["wax"], seg=12, loc=(x, y, z),
          jitter=(0.03, hash(prefix) % 97))
    cyl(f"{prefix}Wick", 0.008, 0.06, (x, y, z + h), K["ink"], verts=4, bevel=0.0)
    for k in range(2):
        a = (hash(prefix) % 7) + k * 2.4
        L = h * (0.4 + 0.25 * k)
        tube(f"{prefix}Drip{k}", [(x + math.cos(a) * r, y + math.sin(a) * r, z + h - 0.02), (x + math.cos(a) * (r + 0.012), y + math.sin(a) * (r + 0.012), z + h - L)],
             0.018, K["wax"], poly=True)
    set_group("Glow")
    sphere(f"{prefix}Flame", 0.035 + r * 0.12, (x, y, z + h + 0.1), K["g_violet"], seg=8, rings=6, scale=(1, 1, 2.3))
    set_group("Main")


def waxfall_altar(M):
    """A black marble altar of three steps crowded with burned-down pillar candles whose wax has poured down every riser in a
    frozen waterfall, violet flames (Glow); an open spellbook on a gilt stand on top and a tall pointed backboard with a
    glowing moon sigil (Glow); 3.6 wide, 2.6 deep, 6.0 tall."""
    K = kit(M)
    mb, br = K["marble"], K["gilt"]
    steps = ((3.4, 2.4, 0.0, 0.55, 0.15), (2.7, 1.8, 0.55, 1.1, 0.35), (2.0, 1.2, 1.1, 1.7, 0.6))
    for k, (w, d, z0, z1, y) in enumerate(steps):
        box(f"Step{k}", (w, d, z1 - z0), (0, y, (z0 + z1) / 2), mb, bevel=0.03)
        box(f"Nosing{k}", (w + 0.04, 0.08, 0.06), (0, y - d / 2, z1 - 0.03), br, bevel=0.01)
    # backboard
    zs, apex = 3.9, 5.9
    poly = [(-1.1, 1.7), (1.1, 1.7), (1.1, zs)] + arch_xz(1.1, -1.1, zs, apex - zs, n=12)[1:-1] + [(-1.1, zs)]
    prism("Board", poly, 1.05, 0.2, mb, plane="XZ", bevel=0.02)
    pts = [(x, 0.93, z) for x, z in arch_xz(-0.95, 0.95, zs, apex - zs - 0.15, n=14)]
    tube("BoardArch", pts, 0.035, br, poly=True)
    for sx in (-1, 1):
        tube(f"BoardSide{sx}", [(sx * 0.95, 0.93, 1.75), (sx * 0.95, 0.93, zs)], 0.035, br, poly=True)
    rnd = random.Random(4624)
    k = 0
    for si, (w, d, z0, z1, y) in enumerate(steps):
        n = 7 - si * 2
        for i in range(n):
            x = -w / 2 + 0.25 + i * (w - 0.5) / max(1, n - 1) + rnd.uniform(-0.06, 0.06)
            yy = y - d / 2 + 0.25 + rnd.uniform(-0.05, 0.08)
            h = rnd.uniform(0.25, 0.75) if si < 2 else rnd.uniform(0.5, 1.0)
            r = rnd.uniform(0.07, 0.12)
            candle(f"C{k}", (x, yy, z1), h, r, K)
            if rnd.random() < 0.75 and si >= 0:
                # wax pouring over the nosing and down the riser below
                L = z1 - (steps[si - 1][3] if si > 0 else 0.0)
                yf = y - d / 2 - 0.035
                tube(f"Fall{k}", [(x, yy - r, z1 + 0.02), (x, yf + 0.02, z1 + 0.04), (x, yf - 0.02, z1 - 0.05), (x + 0.02, yf - 0.03, z1 - L * 0.6),
                                  (x + 0.01, yf - 0.03, z1 - L + 0.05)], 0.035, K["wax"], res=4)
                sphere(f"Pool{k}", 0.13, (x + 0.01, yf - 0.12, z1 - L + 0.015), K["wax"], seg=10, rings=4, scale=(1.2, 0.9, 0.2))
            k += 1
    # open book on a gilt stand
    zb = 1.7
    prism("BookStand", [(-0.3, 0), (0.3, 0), (0.25, 0.25), (-0.25, 0.4)], 0, 0.6, br, plane="YZ", bevel=0.01).matrix_world = T(0, 0.35, zb)
    s = _mark()
    for sx in (-1, 1):
        box(f"BookBoard{sx}", (0.5, 0.65, 0.04), (sx * 0.25, 0, 0), K["leather"], bevel=0.01, rot=(0, -sx * 0.12, 0))
        box(f"BookPages{sx}", (0.46, 0.6, 0.06), (sx * 0.23, 0, 0.045), K["parch"], bevel=0.01, rot=(0, -sx * 0.16, 0))
    _xform(s, T(0, 0.35, zb + 0.36) @ RX(-0.55))
    set_group("Glow")
    hoop("Sigil", (0, 0.93, 4.4), 0.5, "Y", K["g_violet"], thick=0.025)
    moon = []
    for i in range(15):
        t = PI * 0.2 + PI * 1.6 * i / 14
        moon.append((math.cos(t) * 0.32, 4.4 + math.sin(t) * 0.32))
    for i in range(14, -1, -1):
        t = PI * 0.2 + PI * 1.6 * i / 14
        moon.append((math.cos(t) * 0.24 + 0.1, 4.4 + math.sin(t) * 0.24))
    prism("SigilMoon", moon, 0.93, 0.03, K["g_violet"], plane="XZ")
    for i in range(7):
        a = PI / 2 + i * 2 * PI / 7
        sphere(f"SigilDot{i}", 0.04, (math.cos(a) * 0.62, 0.93, 4.4 + math.sin(a) * 0.62), K["g_violet"], seg=8, rings=4)
    set_group("Main")
    return _dims()


def orrery_counter(M):
    """The spell shop counter: night-violet enamel between brass pilasters, a row of silver moon-phase medallions along the
    front, a black marble top; on it a great brass orrery (a glowing sun, Glow, five planets on arms, one ringed, one with a
    moon), a brass till and an open ledger; 6.4 wide, 2.4 deep, 5.4 tall."""
    K = kit(M)
    nt, br, mb = K["night"], K["brassf"], K["marble"]
    W, D, H = 6.0, 2.2, 3.0
    box("Plinth", (W + 0.1, D, 0.3), (0, 0.1, 0.15), mb, bevel=0.03)
    box("Body", (W - 0.1, D - 0.25, H - 0.3), (0, 0.12, 0.3 + (H - 0.3) / 2), nt, bevel=0.03)
    yf = 0.12 - (D - 0.25) / 2
    for k in range(5):
        x = -W / 2 + 0.1 + k * (W - 0.2) / 4
        box(f"Pilaster{k}", (0.22, 0.1, H - 0.3), (x, yf - 0.04, 0.3 + (H - 0.3) / 2), br, bevel=0.02)
        box(f"PilCap{k}", (0.3, 0.14, 0.12), (x, yf - 0.05, H - 0.1), br, bevel=0.02)
    for k in range(8):
        x = -W / 2 + 0.1 + (k + 0.5) * (W - 0.2) / 8
        cyl(f"Medal{k}", 0.24, 0.04, (x, yf - 0.02, 1.9), K["silver"], rot=(PI / 2, 0, 0), verts=24, bevel=0.01)
        hoop(f"MedalRim{k}", (x, yf - 0.04, 1.9), 0.25, "Y", br, thick=0.02)
        ph = (k + 0.5) / 8 * 2 - 1
        if abs(ph) > 0.1:
            cyl(f"MedalShade{k}", 0.22, 0.045, (x + ph * 0.34, yf - 0.04, 1.9), nt, rot=(PI / 2, 0, 0), verts=24, bevel=0.0)
        box(f"Panel{k}", (0.5, 0.03, 0.9), (x, yf - 0.015, 0.9), K["plum"], bevel=0.01)
        pts = [(px, yf - 0.035, pz) for px, pz in arch_xz(x - 0.25, x + 0.25, 1.15, 0.25, n=6)]
        tube(f"PanelArch{k}", pts, 0.015, br, poly=True)
    zt = H
    box("Top", (W + 0.3, D + 0.15, 0.18), (0, 0.05, zt + 0.09), mb, bevel=0.04)
    box("TopEdge", (W + 0.32, 0.04, 0.06), (0, 0.05 - (D + 0.15) / 2, zt + 0.12), br, bevel=0.005)
    zt += 0.18
    # orrery
    ox, oy = 1.4, 0.2
    lathe("OrBase", [(0, 0), (0.55, 0), (0.55, 0.12), (0.4, 0.2), (0.3, 0.3), (0, 0.3)], br, seg=28, loc=(ox, oy, zt))
    for k in range(6):
        a = k * PI / 3
        sphere(f"OrFoot{k}", 0.07, (ox + math.cos(a) * 0.5, oy + math.sin(a) * 0.5, zt + 0.03), br, seg=8, rings=4)
    cyl("OrPost", 0.05, 1.6, (ox, oy, zt + 1.1), br, verts=10, bevel=0.0)
    hoop("OrDial", (ox, oy, zt + 0.32), 0.35, "Z", K["gilt"], thick=0.02)
    planets = ((0.45, 0.55, K["copper"], 0.07, 0.0), (0.7, 0.75, K["silver"], 0.09, 1.3), (0.95, 0.95, K["quartz"], 0.11, 2.6),
               (1.2, 1.15, K["bronze"], 0.14, 3.9), (1.45, 1.35, K["athblue"], 0.1, 5.1))
    for k, (r, h, m, pr, a) in enumerate(planets):
        z = zt + h
        c, s_ = math.cos(a), math.sin(a)
        cyl(f"Hub{k}", 0.07, 0.05, (ox, oy, z), br, verts=12, bevel=0.005)
        tube(f"OrArm{k}", [(ox, oy, z), (ox + c * r, oy + s_ * r, z)], 0.015, br, poly=True)
        tube(f"OrDrop{k}", [(ox + c * r, oy + s_ * r, z), (ox + c * r, oy + s_ * r, z + 0.22)], 0.012, br, poly=True)
        sphere(f"Planet{k}", pr, (ox + c * r, oy + s_ * r, z + 0.22 + pr), m, seg=16, rings=10)
        if k == 3:
            hoop(f"PlanetRing{k}", (ox + c * r, oy + s_ * r, z + 0.22 + pr), pr * 1.7, "Z", K["gilt"], thick=0.012)
        if k == 2:
            tube("MoonArm", [(ox + c * r, oy + s_ * r, z + 0.22 + pr), (ox + c * r + 0.22, oy + s_ * r, z + 0.3 + pr)], 0.006, br, poly=True)
            sphere("Moon", 0.035, (ox + c * r + 0.24, oy + s_ * r, z + 0.3 + pr), K["silver"], seg=8, rings=6)
    for k in range(8):
        a = k * PI / 4
        cone(f"SunRay{k}", 0.04, 0.0, 0.16, (ox + math.cos(a) * 0.3, oy + math.sin(a) * 0.3, zt + 1.95), K["gilt"], verts=4, rot=(0, PI / 2, a))
    # till and ledger
    tx = -1.9
    box("Till", (0.9, 0.7, 0.5), (tx, 0.35, zt + 0.25), br, bevel=0.04)
    prism("TillKeys", [(-0.35, 0.5), (0.0, 0.5), (0.0, 0.78), (-0.35, 0.58)], tx, 0.8, K["night"], plane="YZ", bevel=0.01).matrix_world = T(0, 0.35, zt - 0.02)
    for i in range(4):
        for j in range(2):
            cyl(f"Key{i}{j}", 0.04, 0.05, (tx - 0.27 + i * 0.18, 0.35 - 0.2 + j * 0.14 - 0.05, zt + 0.6 + j * 0.06), K["ivory"], verts=10, bevel=0.005,
                rot=(0.5, 0, 0))
    box("TillCrest", (0.4, 0.02, 0.1), (tx, 0.35 - 0.36, zt + 0.42), K["night"], bevel=0.0)
    s = _mark()
    for sx in (-1, 1):
        box(f"LedgerB{sx}", (0.55, 0.8, 0.05), (sx * 0.28, 0, 0.025), K["inkleather"], bevel=0.01, rot=(0, -sx * 0.05, 0))
        box(f"LedgerP{sx}", (0.5, 0.74, 0.04), (sx * 0.26, 0, 0.065), K["parch"], bevel=0.01, rot=(0, -sx * 0.07, 0))
    _xform(s, T(-0.4, -0.3, zt) @ RZ(-0.2))
    set_group("Glow")
    sphere("Sun", 0.24, (ox, oy, zt + 1.95), K["g_amber"], seg=20, rings=12)
    set_group("Main")
    return _dims()


def star_chart_banner(M):
    """A star-chart banner of indigo cloth on an iron rod with crescent finials: five gilt-threaded constellations whose stars
    glow (Glow), a great gilt crescent at the top and a sun medallion near the hem, a gilt border and a dagged hem with
    tassels; 4.2 wide, 7.6 tall (wall)."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    W, Z0, Z1 = 3.2, 0.6, 7.0
    for sx in (-1, 1):
        box(f"Bracket{sx}", (0.12, 0.4, 0.12), (sx * 1.4, -0.2, Z1 + 0.15), ir, bevel=0.02)
        box(f"WallPlate{sx}", (0.3, 0.05, 0.4), (sx * 1.4, -0.025, Z1 + 0.15), ir, bevel=0.01)
    cyl("Rod", 0.05, W + 0.7, (0, -0.38, Z1 + 0.15), ir, rot=(0, PI / 2, 0), verts=10, bevel=0.0)
    for sx in (-1, 1):
        pts = []
        for i in range(11):
            t = PI * 0.15 + PI * 1.7 * i / 10
            pts.append((math.cos(t) * 0.2, math.sin(t) * 0.2))
        for i in range(10, -1, -1):
            t = PI * 0.15 + PI * 1.7 * i / 10
            pts.append((math.cos(t) * 0.14 + 0.05, math.sin(t) * 0.14))
        cr = prism(f"RodMoon{sx}", [(sx * (W / 2 + 0.55) + sx * u, Z1 + 0.15 + w) for u, w in pts], -0.38, 0.04, gl, plane="XZ")
        sphere(f"RodKnob{sx}", 0.08, (sx * (W / 2 + 0.33), -0.38, Z1 + 0.15), gl, seg=10, rings=6)
    for k in range(7):
        x = -W / 2 + 0.2 + k * (W - 0.4) / 6
        hoop(f"RodRing{k}", (x, -0.38, Z1 + 0.15), 0.08, "X", gl, thick=0.012)
    hem = [(-W / 2, Z1), (W / 2, Z1), (W / 2, Z0 + 0.5)]
    for i in range(5):
        x = W / 2 - (i + 0.5) * W / 5
        hem += [(x, Z0), (x - W / 10, Z0 + 0.5)]
    hem[-1] = (-W / 2, Z0 + 0.5)
    yb = -0.38
    prism("Cloth", hem, yb, 0.03, K["indigo"], plane="XZ")
    border = [(x, yb - 0.02, z) for x, z in hem]
    tube("Border", border + [border[0]], 0.022, gl, poly=True)
    for i in range(5):
        x = W / 2 - (i + 0.5) * W / 5
        tube(f"TasselCord{i}", [(x, yb, Z0), (x, yb, Z0 - 0.15)], 0.012, gl, poly=True)
        lathe(f"Tassel{i}", [(0, 0), (0.05, 0.02), (0.06, 0.22), (0.03, 0.28), (0, 0.3)], gl, seg=10, loc=(x, yb, Z0 - 0.45))
    # crescent and sun medallion
    pts = []
    for i in range(17):
        t = PI * 0.3 + PI * 1.4 * i / 16
        pts.append((math.cos(t) * 0.6, 6.1 + math.sin(t) * 0.6))
    for i in range(16, -1, -1):
        t = PI * 0.3 + PI * 1.4 * i / 16
        pts.append((math.cos(t) * 0.48 + 0.16, 6.1 + math.sin(t) * 0.48))
    prism("Crescent", pts, yb - 0.025, 0.02, gl, plane="XZ")
    cyl("Sun", 0.32, 0.02, (0, yb - 0.025, 1.9), gl, rot=(PI / 2, 0, 0), verts=24, bevel=0.0)
    for k in range(12):
        a = k * PI / 6
        r0, r1 = 0.36, 0.55 if k % 2 == 0 else 0.46
        prism(f"Ray{k}", [(math.cos(a - 0.12) * r0, 1.9 + math.sin(a - 0.12) * r0), (math.cos(a) * r1, 1.9 + math.sin(a) * r1),
                          (math.cos(a + 0.12) * r0, 1.9 + math.sin(a + 0.12) * r0)], yb - 0.025, 0.02, gl, plane="XZ")
    cons = [[(-1.1, 5.4), (-0.7, 5.6), (-0.4, 5.3), (-0.6, 4.9), (-0.95, 4.95)],
            [(0.4, 5.2), (0.8, 5.5), (1.15, 5.15), (1.0, 4.7), (1.25, 4.4)],
            [(-1.2, 4.0), (-0.85, 3.7), (-0.5, 3.85), (-0.2, 3.5), (0.1, 3.65), (0.4, 3.35)],
            [(0.6, 3.9), (0.9, 3.4), (1.25, 3.2), (1.0, 2.8), (0.7, 2.95)],
            [(-1.2, 2.8), (-0.9, 2.5), (-1.1, 2.1), (-0.7, 2.0), (-0.45, 2.35)]]
    for c, pts in enumerate(cons):
        tube(f"ConLine{c}", [(x, yb - 0.022, z) for x, z in pts], 0.008, gl, poly=True)
    set_group("Glow")
    rnd = random.Random(4625)
    for c, pts in enumerate(cons):
        for i, (x, z) in enumerate(pts):
            r = 0.05 if i % 3 == 0 else 0.035
            sphere(f"Star{c}{i}", r, (x, yb - 0.03, z), K["g_pale"], seg=8, rings=4, scale=(1, 0.5, 1))
    for k in range(26):
        x, z = rnd.uniform(-1.4, 1.4), rnd.uniform(1.2, 6.8)
        if 1.4 < z < 2.5 and abs(x) < 0.6:
            continue
        sphere(f"Dust{k}", 0.018, (x, yb - 0.025, z), K["g_pale"], seg=6, rings=3, scale=(1, 0.5, 1))
    set_group("Main")
    return _dims()


def _crystal(prefix, loc, L, r, mat, tilt=(0.0, 0.0)):
    """A hanging quartz point: a hexagonal prism with a long point below and a short one above, hung from its top."""
    s = _mark()
    cyl(f"{prefix}Body", r, L * 0.5, (0, 0, -L * 0.3), mat, verts=6, bevel=0.0)
    cone(f"{prefix}Tip", r, 0.0, L * 0.45, (0, 0, -L * 0.55 - L * 0.225), mat, verts=6, rot=(PI, 0, 0))
    cone(f"{prefix}Cap", r, 0.0, L * 0.12, (0, 0, -L * 0.05 + 0.0), mat, verts=6)
    _xform(s, T(*loc) @ RX(tilt[0]) @ RY(tilt[1]))


def hanging_crystals(M):
    """A ceiling cluster of glowing quartz: an iron ring hung on three chains from a ceiling rose, nine quartz points on fine
    chains at different drops round it and a great double cluster in the middle, violet and teal (Glow, Glow2), with brass
    caps; 3.0 across, 5.2 from the ceiling plate to the lowest point (ceiling)."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    H = 5.2
    cyl("Rose", 0.45, 0.1, (0, 0, H - 0.05), ir, verts=24, bevel=0.02)
    lathe("RoseBoss", [(0, 0), (0.25, 0), (0.2, -0.12), (0.06, -0.2), (0, -0.22)], br, seg=18, loc=(0, 0, H - 0.1))
    zr = H - 1.6
    for k in range(3):
        a = k * 2 * PI / 3
        chain(f"Hang{k}", [(0, 0, H - 0.3), (math.cos(a) * 1.2, math.sin(a) * 1.2, zr + 0.05)], ir, r=0.05, thick=0.013)
    hoop("Ring", (0, 0, zr), 1.25, "Z", ir, thick=0.05)
    hoop("RingGilt", (0, 0, zr + 0.06), 1.25, "Z", br, thick=0.015)
    for k in range(12):
        a = k * PI / 6
        cone(f"Spike{k}", 0.04, 0.0, 0.22, (math.cos(a) * 1.25, math.sin(a) * 1.25, zr + 0.13), ir, verts=4)
    rnd = random.Random(4626)
    drops = []
    for k in range(9):
        a = k * 2 * PI / 9 + 0.2
        r = 1.25 if k % 2 == 0 else 0.85
        drop = rnd.uniform(0.4, 1.8)
        drops.append((math.cos(a) * r, math.sin(a) * r, zr - 0.05, drop, k))
        if r < 1.0:
            tube(f"Spoke{k}", [(math.cos(a) * 1.25, math.sin(a) * 1.25, zr), (math.cos(a) * r, math.sin(a) * r, zr)], 0.025, ir, poly=True)
    for x, y, z, drop, k in drops:
        tube(f"Wire{k}", [(x, y, z), (x, y, z - drop)], 0.008, br, poly=True)
        cyl(f"CapB{k}", 0.07, 0.08, (x, y, z - drop - 0.04), br, verts=6, bevel=0.005)
    tube("CentreWire", [(0, 0, H - 0.3), (0, 0, 2.2)], 0.01, br, poly=True)
    cyl("CentreCap", 0.16, 0.12, (0, 0, 2.15), br, verts=6, bevel=0.01)
    for g in ("Glow", "Glow2"):
        set_group(g)
        mat = K["g_violet"] if g == "Glow" else K["g_teal"]
        for x, y, z, drop, k in drops:
            if (k % 2 == 0) != (g == "Glow"):
                continue
            L = rnd.uniform(0.6, 1.0)
            _crystal(f"Q{k}", (x, y, z - drop - 0.08), L, 0.09, mat)
            _crystal(f"Q{k}b", (x + 0.06, y, z - drop - 0.12), L * 0.6, 0.06, mat, tilt=(0.0, 0.35))
        if g == "Glow":
            _crystal("Big", (0, 0, 2.1), 1.7, 0.22, mat)
            for k in range(3):
                a = k * 2 * PI / 3
                _crystal(f"BigS{k}", (math.cos(a) * 0.1, math.sin(a) * 0.1, 2.05), 1.0, 0.12, mat, tilt=(math.sin(a) * 0.45, -math.cos(a) * 0.45))
    set_group("Main")
    return _dims()


def familiar_perch(M):
    """A familiar's perch: a brass T-perch with seed and water cups on a twisted iron column and marble foot, a bronze crescent
    arching over it with a little bell, and a great horned owl on the bar, ear tufts up, amber eyes glowing (Glow), a brass
    message tube on its leg; 2.2 wide, 1.6 deep, 6.4 tall."""
    K = kit(M)
    ir, br, bz = K["iron"], K["brassf"], K["bronze"]
    cyl("Foot", 0.8, 0.22, (0, 0, 0.11), K["marble"], verts=8, bevel=0.03)
    cyl("Foot2", 0.55, 0.18, (0, 0, 0.31), K["marble"], verts=8, bevel=0.03)
    for k in range(4):
        pts = [(math.cos(k * PI / 2 + t * 0.4) * 0.09, math.sin(k * PI / 2 + t * 0.4) * 0.09, 0.4 + t * 0.14) for t in range(29)]
        tube(f"Twist{k}", pts, 0.04, ir, poly=True)
    cyl("Core", 0.06, 4.0, (0, 0, 2.4), ir, verts=8, bevel=0.0)
    zb = 4.45
    lathe("Collar", [(0, zb - 0.2), (0.14, zb - 0.2), (0.1, zb - 0.05), (0.08, zb), (0, zb)], br, seg=16)
    cyl("Bar", 0.05, 2.0, (0, 0, zb + 0.05), br, rot=(0, PI / 2, 0), verts=12, bevel=0.0)
    cyl("BarGrip", 0.065, 0.9, (0, 0, zb + 0.05), K["leather"], rot=(0, PI / 2, 0), verts=12, bevel=0.01)
    for sx in (-1, 1):
        x = sx * 1.0
        lathe(f"Cup{sx}", [(0, 0), (0.12, 0), (0.18, 0.12), (0.19, 0.18), (0.16, 0.17), (0, 0.04)], br, seg=18, loc=(x, 0, zb + 0.1))
        sphere(f"CupFill{sx}", 0.15, (x, 0, zb + 0.25), K["water"] if sx > 0 else K["straw"], seg=12, rings=4, scale=(1, 1, 0.2))
    pts = []
    for i in range(21):
        t = PI * 0.06 + PI * 0.88 * i / 20
        pts.append((math.cos(t) * 1.0, zb + 0.2 + math.sin(t) * 1.5))
    for i in range(20, -1, -1):
        t = PI * 0.06 + PI * 0.88 * i / 20
        pts.append((math.cos(t) * 0.88, zb + 0.2 + math.sin(t) * 1.32))
    prism("Crescent", pts, 0, 0.08, bz, plane="XZ", bevel=0.01)
    tube("BellHang", [(0, 0, zb + 1.55), (0, 0, zb + 1.35)], 0.01, br, poly=True)
    lathe("Bell", [(0, 0.2), (0.04, 0.2), (0.07, 0.15), (0.08, 0.05), (0.11, 0.0), (0.09, 0.0), (0.06, 0.05), (0, 0.15)], br, seg=14, loc=(0, 0, zb + 1.15))
    # the owl, facing -Y, its feet on the bar
    ox, oz = -0.15, zb + 0.1
    fe, fl = K["feather"], K["featherlt"]
    sphere("Body", 0.36, (ox, 0.02, oz + 0.45), fe, seg=18, rings=12, scale=(0.9, 0.85, 1.2))
    sphere("Breast", 0.3, (ox, -0.1, oz + 0.42), fl, seg=16, rings=10, scale=(0.85, 0.7, 1.15))
    for sx in (-1, 1):
        sphere(f"Wing{sx}", 0.3, (ox + sx * 0.25, 0.06, oz + 0.45), fe, seg=14, rings=10, scale=(0.35, 0.8, 1.2))
        for j in range(3):
            cone(f"Talon{sx}{j}", 0.025, 0.0, 0.09, (ox + sx * 0.1 + (j - 1) * 0.035, -0.06, oz - 0.0), K["beak"], verts=5, rot=(-1.9, 0, 0))
        sphere(f"Leg{sx}", 0.07, (ox + sx * 0.1, -0.02, oz + 0.07), fl, seg=8, rings=6, scale=(1, 1, 1.3))
    prism("Tail", [(-0.12, 0), (0.12, 0), (0.08, -0.3), (-0.08, -0.3)], 0, 0.08, fe, plane="XZ").matrix_world = T(ox, 0.28, oz + 0.15) @ RX(-0.4)
    cyl("MsgTube", 0.03, 0.14, (ox + 0.1, -0.08, oz + 0.08), br, verts=8, bevel=0.005)
    hz = oz + 1.0
    sphere("Head", 0.3, (ox, -0.02, hz), fe, seg=18, rings=10, scale=(1.05, 0.9, 0.9))
    for sx in (-1, 1):
        sphere(f"Disc{sx}", 0.14, (ox + sx * 0.12, -0.2, hz + 0.0), fl, seg=14, rings=8, scale=(1, 0.45, 1))
        cone(f"Tuft{sx}", 0.07, 0.0, 0.24, (ox + sx * 0.18, 0.0, hz + 0.3), fe, verts=5, rot=(0, sx * 0.35, 0))
        sphere(f"Pupil{sx}", 0.03, (ox + sx * 0.12, -0.3, hz + 0.02), K["ink"], seg=8, rings=4)
    cone("Beak", 0.04, 0.0, 0.12, (ox, -0.27, hz - 0.1), K["beak"], verts=6, rot=(PI + 0.4, 0, 0))
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.065, (ox + sx * 0.12, -0.255, hz + 0.02), K["g_amber"], seg=12, rings=8, scale=(1, 0.6, 1))
    set_group("Main")
    return _dims()


def rune_circle_rug(M):
    """A round rug of deep violet wool with a crimson border and fringe, a glowing rune circle worked into it (Glow): two
    rings, a seven-pointed star, a crescent at the centre and runes between the rings; 8.4 across, flat."""
    K = kit(M)
    R = 4.0
    cyl("Rug", R, 0.05, (0, 0, 0.025), K["rugwool"], verts=72, bevel=0.01)
    lathe("Border", [(R - 0.35, 0.0), (R + 0.02, 0.0), (R + 0.02, 0.06), (R - 0.35, 0.06)], K["rugedge"], seg=72)
    for k in range(56):
        a = k * 2 * PI / 56
        c, s_ = math.cos(a), math.sin(a)
        tube(f"Fringe{k}", [(c * (R + 0.02), s_ * (R + 0.02), 0.02), (c * (R + 0.2), s_ * (R + 0.2), 0.012)], 0.02, K["rugedge"], poly=True)
    z = 0.06
    set_group("Glow")
    for r in (3.35, 3.0):
        hoop(f"Ring{r}", (0, 0, z), r, "Z", K["g_teal"], thick=0.03)
    hoop("Inner", (0, 0, z), 0.9, "Z", K["g_teal"], thick=0.03)
    vs = [(math.cos(PI / 2 + i * 2 * PI / 7) * 3.0, math.sin(PI / 2 + i * 2 * PI / 7) * 3.0) for i in range(7)]
    star = [vs[(i * 3) % 7] for i in range(8)]
    tube("Heptagram", [(x, y, z) for x, y in star], 0.03, K["g_teal"], poly=True)
    moon = []
    for i in range(15):
        t = PI * 0.25 + PI * 1.5 * i / 14
        moon.append((math.cos(t) * 0.55, math.sin(t) * 0.55))
    for i in range(14, -1, -1):
        t = PI * 0.25 + PI * 1.5 * i / 14
        moon.append((math.cos(t) * 0.42 + 0.15, math.sin(t) * 0.42))
    prism("Moon", moon, z - 0.005, 0.02, K["g_teal"], plane="XY")
    for k in range(21):
        a = k * 2 * PI / 21 + 0.1
        c, s_ = math.cos(a), math.sin(a)
        r0, r1 = 3.07, 3.28
        shape = k % 3
        if shape == 0:
            pts = [(r0, -0.06), (r1, 0.0), (r0, 0.06)]
        elif shape == 1:
            pts = [(r0, 0.0), (r1, 0.0), (r1 - 0.08, 0.07)]
        else:
            pts = [(r0, -0.06), (r1, 0.06), (r0 + 0.1, 0.06)]
        tube(f"Rune{k}", [(c * u - s_ * v, s_ * u + c * v, z) for u, v in pts], 0.018, K["g_teal"], poly=True)
    set_group("Main")
    return _dims()


def oddments_etagere(M):
    """A tall narrow black iron etagere of strange ingredients under a pointed arch: four shelves of glass jars (Glass) holding
    fireflies and glowing toadstools (Glow), a storm cloud with its lightning (Glow2) and drifting star dust, raven feathers,
    quartz points, moon salt and snail shells, each with a paper label; 2.2 wide, 1.0 deep, 7.2 tall."""
    K = kit(M)
    ir, br = K["iron"], K["brassf"]
    W, D = 2.0, 0.9
    zs, apex = 6.0, 7.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Post{sx}{sy}", (0.08, 0.08, zs), (sx * W / 2, sy * D / 2, zs / 2), ir, bevel=0.015)
            sphere(f"PostFoot{sx}{sy}", 0.07, (sx * W / 2, sy * D / 2, 0.05), br, seg=8, rings=6)
    for sy in (-1, 1):
        pts = [(x, sy * D / 2, z) for x, z in arch_xz(-W / 2, W / 2, zs, apex - zs, n=12)]
        tube(f"Arch{sy}", pts, 0.04, ir, square=True, poly=True)
        tube(f"ArchIn{sy}", [(x, sy * D / 2, z) for x, z in arch_xz(-W / 2 + 0.25, W / 2 - 0.25, zs, apex - zs - 0.35, n=10)], 0.025, ir, poly=True)
    finial("Finial", 0, -D / 2, apex, br, s=0.7)
    shelves = (0.35, 1.8, 3.25, 4.7)
    for k, z in enumerate(shelves):
        box(f"Shelf{k}", (W + 0.04, D + 0.04, 0.06), (0, 0, z), ir, bevel=0.01)
        box(f"Gallery{k}", (W, 0.02, 0.02), (0, -D / 2, z + 0.18), br, bevel=0.0)
        for i in range(9):
            tube(f"GalBal{k}{i}", [(-W / 2 + i * W / 8, -D / 2, z), (-W / 2 + i * W / 8, -D / 2, z + 0.18)], 0.008, br, poly=True)
    rnd = random.Random(4627)

    def jar(prefix, x, z, r, h, label=True):
        set_group("Glass")
        lathe(f"{prefix}Jar", [(0, 0), (r, 0), (r + 0.02, 0.05), (r + 0.02, h * 0.85), (r * 0.8, h * 0.95), (r * 0.8, h), (0, h)], K["glass"], seg=18,
              loc=(x, 0, z))
        set_group("Main")
        cyl(f"{prefix}Lid", r * 0.85, 0.06, (x, 0, z + h + 0.03), br, verts=16, bevel=0.01)
        sphere(f"{prefix}Knob", 0.04, (x, 0, z + h + 0.08), br, seg=8, rings=4)
        if label:
            lbl = lathe(f"{prefix}Label", [(r + 0.025, h * 0.3), (r + 0.025, h * 0.48)], K["parch"], seg=18, loc=(x, 0, z))
            B4._solid(lbl, 0.004)
    z = shelves[3] + 0.03
    jar("Fire", -0.5, z, 0.3, 0.9)
    jar("Storm", 0.45, z, 0.32, 1.0)
    z = shelves[2] + 0.03
    jar("Shroom", -0.55, z, 0.28, 0.75)
    jar("Feather", 0.0, z, 0.18, 1.0)
    jar("Quartz", 0.55, z, 0.25, 0.7)
    z = shelves[1] + 0.03
    jar("Salt", -0.5, z, 0.3, 0.6)
    jar("Dust", 0.45, z, 0.3, 0.95)
    z = shelves[0] + 0.03
    jar("Shell", -0.45, z, 0.32, 0.65)
    for k, x in enumerate((0.25, 0.6)):
        sphere(f"Gourd{k}", 0.2, (x, 0.05, z + 0.2), K["frog"], seg=12, rings=8, scale=(1, 1, 1.1))
        cyl(f"GourdNeck{k}", 0.05, 0.22, (x, 0.05, z + 0.48), K["frog"], verts=8, bevel=0.0)
        cyl(f"GourdCork{k}", 0.055, 0.06, (x, 0.05, z + 0.6), K["cork"], verts=8, bevel=0.005)
    # contents (Main)
    z = shelves[3] + 0.03
    for k in range(5):
        sphere(f"Cloud{k}", 0.12 + 0.03 * (k % 2), (0.45 + (k - 2) * 0.09, rnd.uniform(-0.05, 0.05), z + 0.7 + rnd.uniform(-0.04, 0.04)), K["plaster"], seg=10, rings=6)
    z = shelves[2] + 0.03
    for k in range(4):
        tube(f"Stalk{k}", [(-0.55 + (k - 1.5) * 0.12, 0, z + 0.03), (-0.55 + (k - 1.5) * 0.13, 0, z + 0.2 + 0.08 * (k % 2))], 0.025, K["ivory"], poly=True)
    for k in range(4):
        a = k * PI / 2
        prism(f"Plume{k}", [(0, 0), (0.05, 0.2), (0.06, 0.8), (0.02, 1.15), (-0.03, 0.8), (-0.04, 0.2)], 0, 0.006, K["ebony"], plane="XZ").matrix_world = \
            T(math.cos(a) * 0.04, math.sin(a) * 0.04, z + 0.05) @ RZ(a) @ RY(0.12 * math.cos(a))
    for k in range(5):
        a = k * 2 * PI / 5
        _crystal(f"QP{k}", (0.55 + math.cos(a) * 0.1, math.sin(a) * 0.1, z + 0.05), -0.45, 0.05, K["quartz"], tilt=(math.sin(a) * 0.3, -math.cos(a) * 0.3))
    z = shelves[1] + 0.03
    cyl("SaltHeap", 0.27, 0.3, (-0.5, 0, z + 0.15), K["chalk"], verts=16, bevel=0.04)
    z = shelves[0] + 0.03
    for k in range(7):
        sphere(f"ShellS{k}", 0.08, (-0.45 + rnd.uniform(-0.18, 0.18), rnd.uniform(-0.15, 0.15), z + 0.08 + (k // 3) * 0.12), K["horse"], seg=10, rings=6, scale=(1, 0.8, 0.8))
    # glowing contents
    set_group("Glow")
    z = shelves[3] + 0.03
    for k in range(16):
        sphere(f"Fly{k}", 0.025, (-0.5 + rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), z + rnd.uniform(0.15, 0.75)), K["g_green"], seg=6, rings=3)
    z = shelves[2] + 0.03
    for k in range(4):
        x = -0.55 + (k - 1.5) * 0.13
        sphere(f"Cap{k}", 0.08, (x, 0, z + 0.22 + 0.08 * (k % 2)), K["g_green"], seg=10, rings=5, scale=(1, 1, 0.55))
    set_group("Glow2")
    z = shelves[3] + 0.03
    tube("Bolt", [(0.5, 0, z + 0.6), (0.4, -0.02, z + 0.42), (0.5, 0.0, z + 0.36), (0.38, -0.02, z + 0.12)], 0.02, K["g_pale"], poly=True)
    z = shelves[1] + 0.03
    for k in range(20):
        a, r = rnd.uniform(0, 2 * PI), rnd.uniform(0, 0.24)
        sphere(f"Mote{k}", 0.02, (0.45 + math.cos(a) * r, math.sin(a) * r, z + rnd.uniform(0.1, 0.8)), K["g_pale"], seg=6, rings=3)
    set_group("Main")
    return _dims()


def spell_shop_sign(M):
    """The spell shop's hanging sign: a wrought-iron arm off the wall holding a bronze crescent moon that cradles a glowing
    star on a chain (Glow), and beneath it a pointed night-enamel board lettered HEX AND HOLLOW / spells charms oddments in
    gilt on both faces; 3.3 out from the wall, 4.4 tall (wall; pivot on the wall plate)."""
    K = kit(M)
    ir, br, bz = K["iron"], K["gilt"], K["bronze"]
    box("WallPlate", (0.5, 0.08, 1.4), (0, -0.04, 3.4), ir, bevel=0.02)
    tube("Arm", [(0, -0.05, 4.0), (0, -3.2, 4.0)], 0.055, ir, square=True, poly=True)
    pts = [(0, -0.05 - 1.2 * (1 - math.cos(t)), 2.8 + 1.2 * math.sin(t)) for t in [i / 12 * PI / 2 for i in range(13)]]
    tube("Brace", pts, 0.04, ir, poly=True)
    for k in range(5):
        c = (0, -0.4 - k * 0.5, 4.0 - 0.12)
        tube(f"Curl{k}", [(0, c[1] + math.cos(a) * 0.1, c[2] + math.sin(a) * 0.1) for a in [i * 0.5 for i in range(12)]], 0.018, ir, poly=True)
    sphere("ArmKnob", 0.1, (0, -3.3, 4.0), br, seg=10, rings=6)
    # crescent moon hanging from the arm (YZ plane)
    yc, zc = -2.2, 3.15
    moon = []
    for i in range(21):
        t = PI * 0.65 + PI * 1.4 * i / 20
        moon.append((yc + math.cos(t) * 0.75, zc + math.sin(t) * 0.75))
    for i in range(20, -1, -1):
        t = PI * 0.65 + PI * 1.4 * i / 20
        moon.append((yc + math.cos(t) * 0.58 + 0.09, zc + math.sin(t) * 0.58 + 0.18))
    prism("Moon", moon, 0, 0.1, bz, plane="YZ", bevel=0.01)
    tube("MoonHang", [(0, yc - 0.45, 4.0), (0, yc - 0.45, 3.75)], 0.015, ir, poly=True)
    tube("MoonHang2", [(0, yc + 0.6, 4.0), (0, yc + 0.6, 3.62)], 0.015, ir, poly=True)
    tube("StarChain", [(0, yc - 0.05, 4.0), (0, yc - 0.05, 3.25)], 0.01, br, poly=True)
    # board below
    bw, b0, b1 = 2.3, 1.0, 1.9
    board = [(-0.0 - 1.0 - bw / 2, b0), (-1.0 + bw / 2, b0), (-1.0 + bw / 2, b1)] + [(-1.0 + u, w) for u, w in arch_xz(bw / 2, -bw / 2, b1, 0.35, n=10)[1:-1]] + \
        [(-1.0 - bw / 2, b1)]
    board = [(y - 1.0, z) for y, z in board]
    prism("Board", board, 0, 0.1, K["night"], plane="YZ", bevel=0.015)
    pts = [(0, y, z) for y, z in board]
    for sx in (-1, 1):
        tube(f"BoardRim{sx}", [(sx * 0.055, p[1], p[2]) for p in pts + [pts[0]]], 0.022, br, poly=True)
        yz_text(f"T1{sx}", "HEX AND HOLLOW", br, sx * 0.05, -2.0, 1.6, 2.0, 0.28, side=sx)
        yz_text(f"T2{sx}", "spells  charms  oddments", br, sx * 0.05, -2.0, 1.22, 1.7, 0.13, side=sx, font=FONT_I)
    for y in (-2.9, -1.1):
        tube(f"BoardChain{y}", [(0, y, b1 + 0.02), (0, y, 2.6)], 0.015, ir, poly=True)
        hoop(f"BoardRing{y}", (0, y, b1 + 0.05), 0.05, "X", ir, thick=0.012)
    tube("BoardHang", [(0, -2.9, 2.6), (0, -2.2, 2.42), (0, -1.1, 2.6)], 0.015, ir, poly=True)
    set_group("Glow")
    star = []
    for i in range(10):
        a = PI / 2 + i * PI / 5
        r = 0.28 if i % 2 == 0 else 0.12
        star.append((yc - 0.05 + math.cos(a) * r, 3.0 + math.sin(a) * r))
    prism("Star", star, 0, 0.08, K["g_pale"], plane="YZ")
    set_group("Main")
    return _dims()


ARMORY = {
    "KatanaStand": katana_stand,
    "PolearmRack": polearm_rack,
    "PlateArmourStand": plate_armour_stand,
    "MailHauberkStand": mail_hauberk_stand,
    "ShieldWall": shield_wall,
    "Grindstone": grindstone,
    "ArmoryCounter": armory_counter,
    "SilverDaggerCase": silver_dagger_case,
    "HelmShelf": helm_shelf,
    "BoltBarrel": bolt_barrel,
    "BeastPell": beast_pell,
    "CrossbowRack": crossbow_rack,
    "HuntersReliquary": hunters_reliquary,
    "ArmorySign": armory_sign,
    "ClawGauntletDisplay": claw_gauntlet_display,
}
SPELLSHOP = {
    "TetheredGrimoires": tethered_grimoires,
    "PotionHoneycomb": potion_honeycomb,
    "ScryingOrbStand": scrying_orb_stand,
    "WandCoffin": wand_coffin,
    "RuneStoneTable": rune_stone_table,
    "ScrollCarousel": scroll_carousel,
    "WaxfallAltar": waxfall_altar,
    "OrreryCounter": orrery_counter,
    "StarChartBanner": star_chart_banner,
    "HangingCrystals": hanging_crystals,
    "FamiliarPerch": familiar_perch,
    "RuneCircleRug": rune_circle_rug,
    "OddmentsEtagere": oddments_etagere,
    "SpellShopSign": spell_shop_sign,
}
BUILDERS = dict(ARMORY, **SPELLSHOP)
P.BUILD.update(BUILDERS)
GLOW.update({
    "TetheredGrimoires": {"Glow": (180, 120, 255)},
    "PotionHoneycomb": {"Glow": (190, 110, 255), "Glow2": (120, 255, 150)},
    "ScryingOrbStand": {"Glow": (160, 205, 255)},
    "WandCoffin": {"Glow": (210, 180, 255)},
    "RuneStoneTable": {"Glow": (90, 230, 220)},
    "ScrollCarousel": {"Glow": (220, 230, 255)},
    "WaxfallAltar": {"Glow": (190, 140, 255)},
    "OrreryCounter": {"Glow": (255, 190, 90)},
    "StarChartBanner": {"Glow": (200, 220, 255)},
    "HangingCrystals": {"Glow": (180, 120, 255), "Glow2": (100, 230, 230)},
    "FamiliarPerch": {"Glow": (255, 180, 60)},
    "RuneCircleRug": {"Glow": (90, 230, 220)},
    "OddmentsEtagere": {"Glow": (170, 255, 120), "Glow2": (190, 215, 255)},
    "SpellShopSign": {"Glow": (220, 200, 255)},
})
CAM.update({"RuneCircleRug": 0.75, "ClawGauntletDisplay": 0.35, "SilverDaggerCase": 0.9, "BoltBarrel": 0.3})
