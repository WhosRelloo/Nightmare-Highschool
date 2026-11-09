"""Props batch 35, the Teachers' Lounge kit (2026-11-08) for nh_props.py. The staff room of the Institution: a corner to
brew tea, mark books and sit out a free period. The house look: cast iron, black marble, crimson enamel (#600E1A), brass and
gilt, dark oak and ebonised wood, bone china, ink, wax, paper and slate. Every name and word on the props is invented.

  TeaUrn              a brass samovar urn on a small cast-iron stand with a spirit lamp under it, a tap at the front, two
                      handles, a crest medallion (bone enamel in a brass bezel)
  SpiritKettle        a copper kettle with a brass swing handle on a little cast-iron spirit stove (a brass burner)
  TeaSet              on an ebonised tray: a teapot, three cups and saucers, a sugar bowl and a milk jug in bone china with a
                      crimson band between gilt lines, a teaspoon
  MugRack             a dark oak wall rack with a shelf (a tea caddy and a sugar jar) and six iron cup hooks, six different
                      staff mugs hanging on them
  BiscuitBarrel       a bone china barrel printed with the crest and BISCUITS, a brass lid, foot and bail handle
  KitchenetteCounter  base cupboards: three drawers, two drawers over two doors (crimson enamel pointed panels), brass pulls,
                      a black marble top (3.0) with a marble upstand
  IceBox              a dark oak larder ice box: an ice door over a food door, zinc-lined door openings, brass latches and
                      hinges, a brass ICE plate, a zinc drip tray between bun feet
  MarkingStack        a pile of printed exercise books, a red fountain pen on top, marked sheets beside it
  Gradebook           an open ledger: two printed pages of marks (columns I..X, totals, remarks), an inkwell and a dip pen
  StaffRotaBoard      a framed slate chalked STAFF DUTY ROTA (DUTY / MON..FRI), a chalk ledge, a brass rail of name hooks
                      with bone tags (Mr. Hale, Miss Vane, Dr. Crowe, Mrs. Ashby, Mr. Thorne, Mr. Graves)
  WallTelephone       an oak crank wall telephone: two brass bells, a mouthpiece horn, a crank, the earpiece on its hook and
                      cord, a writing shelf, the battery box below
  CardTable           a small folding card table: green baize in an ebonised frame, two hands of cards, the deck, a face-up
                      pile and stacks of chips
  StaffOnlySign       a brass door plaque, crimson enamel field, raised gilt STAFF ONLY
  Dartboard           a dark oak cabinet with its doors swung open, the board inside (printed face, wire spider), three
                      darts, a chalk score slate in the left door
  StaffLockers        a bank of three tall dark oak staff lockers: louvred pointed-arch vents, raised panels, brass name
                      plates with tags, keyholes, lever handles

The printed faces come from art/props/staff_atlas.py (StaffPrint, shared with batch 36) through the "Spine" UV, as the dorm and
library kits do. Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back face on y = 0.
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
from nh_props import box, cyl, tube, material, _finish, _gable
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _solid
from nh_props_batch9 import foil, wax_mat
from nh_props_batch10 import gilt
from nh_props_batch24 import _text, _fine
import nh_props_batch20 as B20
import nh_props_batch24 as B24
import nh_props_batch29 as B29
import nh_props_batch30 as B30
import nh_props_batch34_dorm as DM
import window_shapes as WS

DEG = math.pi / 180
RX, RY, RZ, T = B30.RX, B30.RY, B30.RZ, B30.T
FONT = "C:/Windows/Fonts/palab.ttf"

SA = json.load(open(os.path.join(P.HERE, "staff_atlas.json")))
for _k, _v in SA["print"].items():
    B30.REG["SP_" + _k] = _v
    if _k.startswith("Swatch_"):
        B30.REG["Swatch_SP_" + _k[7:]] = _v


# ------------------------------------------------------------------ materials

def kit(M):
    K = DM.kit(M)
    K.update({
        "oak": material("LoungeOak", "NH_DeskWood", tint=(0.2, 0.115, 0.066), scale=0.22, rough_add=0.05, wear=0.4),
        "oakdk": material("LoungeOakDark", "NH_DeskWood", tint=(0.12, 0.068, 0.04), scale=0.22, rough_add=0.06, wear=0.35),
        "copper": material("Copper", base=(0.72, 0.34, 0.2), rough=0.3, metal=1.0, wear=0.3, dirt=0.75),
        "zinc": material("Zinc", base=(0.5, 0.51, 0.52), rough=0.42, metal=1.0, wear=0.15, dirt=0.85),
        "steel": material("Steel", base=(0.62, 0.63, 0.65), rough=0.25, metal=1.0, wear=0.2, dirt=0.6),
        "china": flat("BoneChina", (0.74, 0.7, 0.6), 0.16, dirt=0.4),
        "glaze": B30.atlas_mat("StaffGlazeMat", "StaffPrint", rough=0.16, leather=0.0, wear=0.02, dirt=0.4),
        "sp": B30.atlas_mat("StaffPrintMat", "StaffPrint", rough=0.7, leather=0.04, wear=0.04, dirt=0.45),
        "slate": material("BenchSlate", "NH_Slate", tint=(0.2, 0.22, 0.23), scale=0.22, rough_mul=0.7, rough_add=0.3, normal=0.7, wear=0.25, dirt=0.8),
        "baize": B24.cloth("Baize", (0.012, 0.07, 0.035), rough=0.95, weave=0.006),
        "tea": flat("Tea", (0.09, 0.035, 0.012), 0.05, dirt=0.2),
        "cord": flat("Cord", (0.03, 0.026, 0.024), 0.7),
        "red": material("RedLacquer", base=(0.32, 0.015, 0.02), rough=0.2, wear=0.1, dirt=0.4),
        "inkglass": material("InkGlass", base=(0.02, 0.045, 0.04), rough=0.08, wear=0.0, dirt=0.2),
        "chalk": M["chalk"],
        "felt": M["felt"],
    })
    return K


# ------------------------------------------------------------------ helpers

def _resample_prof(prof, step, cuts=()):
    out = [prof[0]]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        L = math.hypot(r1 - r0, z1 - z0)
        n = max(1, int(math.ceil(L / step)))
        ts = sorted({i / n for i in range(1, n + 1)} | {(c - z0) / (z1 - z0) for c in cuts if z1 != z0 and 0 < (c - z0) / (z1 - z0) < 1})
        for t in ts:
            out.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
    return out


def wrap_lathe(name, prof, mat, key=None, wrap=None, bands=(), base="SP_mugbone", seg=32, mtx=None, step=0.03, rect=(0, 0, 1, 1), k=2.0):
    """A solid of revolution (like lathe) with a "Spine" UV: the faces whose centre z is inside wrap = (z0, z1) on the outside
    (the profile going up) carry the atlas region `key` wrapped once round (u = 0.25 faces -Y); bands = [(z0, z1, swatch)]
    paint rings of plain swatches (the china's crimson band and gilt lines); everything else is the `base` swatch."""
    cuts = [b[0] for b in bands] + [b[1] for b in bands] + (list(wrap) if wrap else [])
    pr = _resample_prof(prof, step, cuts)
    bm = bmesh.new()
    rings = []
    for r, z in pr:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((math.cos(-math.pi + i / seg * 2 * math.pi) * r, math.sin(-math.pi + i / seg * 2 * math.pi) * r, z))
                          for i in range(seg)])
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    sw_base = DM.swatch_uv(base)
    for ri, (A, B) in enumerate(zip(rings, rings[1:])):
        if len(A) == 1 and len(B) == 1:
            continue
        (ra, za), (rb, zb) = pr[ri], pr[ri + 1]
        zc = (za + zb) / 2
        up = zb > za + 1e-6
        for i in range(seg):
            j = (i + 1) % seg
            if len(A) == 1:
                f = bm.faces.new((A[0], B[j], B[i]))
                idx = [(None, 0), (i + 1, 1), (i, 1)]
            elif len(B) == 1:
                f = bm.faces.new((A[i], A[j], B[0]))
                idx = [(i, 0), (i + 1, 0), (None, 1)]
            else:
                f = bm.faces.new((A[i], A[j], B[j], B[i]))
                idx = [(i, 0), (i + 1, 0), (i + 1, 1), (i, 1)]
            f.smooth = True
            sw = None
            for b0, b1, s in bands:
                if b0 <= zc <= b1 and up:
                    sw = s
            if sw is None and key and wrap and up and wrap[0] <= zc <= wrap[1] and len(A) > 1 and len(B) > 1:
                for lp, (ii, side) in zip(f.loops, idx):
                    zz = za if side == 0 else zb
                    s_ = rect[0] + (rect[2] - rect[0]) * (ii / seg)
                    t_ = rect[1] + (rect[3] - rect[1]) * ((zz - wrap[0]) / (wrap[1] - wrap[0]))
                    lp[uvl].uv = DM.region_uv(key, s_, t_)
                f[kl] = k
                continue
            uvp = DM.swatch_uv(sw) if sw else sw_base
            for lp in f.loops:
                lp[uvl].uv = uvp
            f[kl] = 0.4
    ob = DM.mesh_obj(name, bm, mat)
    if mtx is not None:
        ob.matrix_world = mtx
    return ob


def disc_print(name, key, r, t, mtx, mat, rect=(0, 0, 1, 1), edge="SP_mugbone", seg=40, k=2.4):
    """A disc r x t facing -Y (front face at y = -t/2), its face printed with an atlas region (the square `rect` of it)."""
    bm = bmesh.new()
    fr = [bm.verts.new((math.cos(i / seg * 2 * math.pi) * r, -t / 2, math.sin(i / seg * 2 * math.pi) * r)) for i in range(seg)]
    bk = [bm.verts.new((v.co.x, t / 2, v.co.z)) for v in fr]
    uvl = bm.loops.layers.uv.new("Spine")
    kl = bm.faces.layers.float.new("nh_uvk")
    f = bm.faces.new(list(reversed(fr)))
    for lp in f.loops:
        x, _, z = lp.vert.co
        lp[uvl].uv = DM.region_uv(key, rect[0] + (rect[2] - rect[0]) * (x / r * 0.5 + 0.5), rect[1] + (rect[3] - rect[1]) * (z / r * 0.5 + 0.5))
    f[kl] = k
    sw = DM.swatch_uv(edge)
    faces = [bm.faces.new(bk)]
    for i in range(seg):
        j = (i + 1) % seg
        faces.append(bm.faces.new((fr[i], fr[j], bk[j], bk[i])))
    for f2 in faces:
        for lp in f2.loops:
            lp[uvl].uv = sw
        f2[kl] = 0.4
    bm.normal_update()
    ob = DM.mesh_obj(name, bm, mat)
    ob.modifiers.new("Tri", "TRIANGULATE")
    ob.matrix_world = mtx
    return ob


# the crest on the left of the Mug_Crest wrap: a square round it (fractions of the region)
CREST_RECT = (0.25 - 150 / 900, 0.0, 0.25 + 150 / 900, 1.0)


def brass_bail(prefix, x, y, z, w, mat, drop=0.07):
    """A drawer's bail pull on a face at y (facing -Y): two roses and a hanging loop."""
    for sx in (-1, 1):
        cyl(f"{prefix}Rose{sx}", 0.032, 0.02, (x + sx * w / 2, y - 0.01, z), mat, rot=(math.pi / 2, 0, 0), verts=12, bevel=0.006)
    tube(f"{prefix}Bail", [(x - w / 2, y - 0.02, z), (x - w / 2 + 0.03, y - 0.05, z - drop), (x + w / 2 - 0.03, y - 0.05, z - drop),
                           (x + w / 2, y - 0.02, z)], 0.011, mat)


def knob(name, x, y, z, mat, r=0.05):
    cyl(name + "Rose", r * 0.9, 0.02, (x, y - 0.01, z), mat, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.005)
    s = _mark()
    lathe(name, [(0, 0), (r * 0.45, 0), (r * 0.4, r * 0.6), (r, r * 1.1), (r * 0.95, r * 1.6), (r * 0.5, r * 1.9), (0, r * 1.9)], mat, seg=14)
    _xform(s, T(x, y - 0.02, z) @ RX(math.pi / 2))


def keyhole(name, x, y, z, K):
    cyl(name, 0.045, 0.012, (x, y - 0.006, z), K["brassf"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.004)
    box(name + "Slot", (0.016, 0.006, 0.04), (x, y - 0.013, z - 0.012), K["ink"], bevel=0.0)
    cyl(name + "Hole", 0.013, 0.006, (x, y - 0.013, z + 0.008), K["ink"], rot=(math.pi / 2, 0, 0), verts=8, bevel=0.0)


def enamel_arch_panel(prefix, cx, y, hw, z0, z1, K, t=0.05):
    """A pointed crimson enamel panel in an iron bead, on a face at y (facing -Y)."""
    zs = z1 - hw * 1.4
    pts = WS.arch(hw, z0, zs, z1, 12, cx=cx)
    B20.tprism(f"{prefix}Panel", WS.ccw(pts), y - t / 2, t, K["enamel"])
    tube(f"{prefix}Bead", [(x, y - t - 0.004, z) for x, z in pts] + [(pts[0][0], y - t - 0.004, pts[0][1])], 0.018, K["iron"], square=True, poly=True)


def mug(prefix, key, mtx, K, plain=None):
    """A staff mug 0.4 tall, its handle toward +Y; key = a Mug_* wrap (or plain = a swatch for a plain glaze)."""
    s = _mark()
    r, h = 0.19, 0.4
    prof = [(0, 0), (r * 0.92, 0), (r, 0.02), (r, h - 0.01), (r - 0.005, h), (r - 0.022, h), (r - 0.022, 0.03), (0, 0.03)]
    if plain:
        wrap_lathe(f"{prefix}Body", prof, K["glaze"], base=plain, seg=24, step=0.06)
    else:
        wrap_lathe(f"{prefix}Body", prof, K["glaze"], key=key, wrap=(0.02, h - 0.01), seg=24, step=0.06)
    cyl(f"{prefix}Inside", r - 0.024, 0.005, (0, 0, 0.033), K["china"], verts=24, bevel=0.0)
    hmat = K["glaze"]
    sw = plain or {"SP_Mug_Crest": "SP_mugbone", "SP_Mug_Staff": "SP_mugcrim", "SP_Mug_Stripe": "SP_mugbone", "SP_Mug_Raven": "SP_mugink",
                   "SP_Mug_Moon": "SP_mugblue"}[key]
    t0 = _mark()
    tube(f"{prefix}Handle", [(0, r - 0.01, h - 0.07), (0, r + 0.1, h - 0.08), (0, r + 0.13, h * 0.5), (0, r + 0.1, 0.1), (0, r - 0.01, 0.09)], 0.028, hmat)
    _swatch_uv(P.PARTS[-1], sw)
    _xform(s, mtx)


def _swatch_uv(ob, sw):
    """Give a plain mesh a Spine UV on one swatch (for parts in an atlas material)."""
    me = ob.data
    uv = me.uv_layers.new(name="Spine")
    p = DM.swatch_uv(sw)
    for d in uv.data:
        d.uv = p
    B30.uvk(ob, 0.4)
    return ob


# ================================================================== tea

def tea_urn(M):
    K = kit(M)
    ir, br = K["iron"], K["brass"]
    # the stand: a ring on three scrolled legs, a plate for the urn, a spirit lamp under it
    zt = 0.5
    hoop("StandRing", (0, 0, zt - 0.03), 0.4, "Z", ir, thick=0.03)
    cyl("StandPlate", 0.38, 0.03, (0, 0, zt - 0.015), ir, verts=32, bevel=0.008)
    hoop("StandLow", (0, 0, 0.12), 0.46, "Z", ir, thick=0.02)
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s = math.cos(a), math.sin(a)
        tube(f"Leg{k}", [(c * 0.4, s * 0.4, zt - 0.03), (c * 0.42, s * 0.42, 0.3), (c * 0.48, s * 0.48, 0.12), (c * 0.56, s * 0.56, 0.03)], 0.028, ir,
             square=True)
        sphere(f"Toe{k}", 0.04, (c * 0.57, s * 0.57, 0.03), ir, seg=10, rings=5)
        tube(f"Scroll{k}", [(c * 0.41, s * 0.41, 0.4), (c * 0.52, s * 0.52, 0.36), (c * 0.52, s * 0.52, 0.24), (c * 0.44, s * 0.44, 0.24)], 0.016, ir)
    lathe("Lamp", [(0, 0.06), (0.12, 0.06), (0.14, 0.09), (0.13, 0.17), (0.07, 0.2), (0.04, 0.2), (0.04, 0.24), (0, 0.24)], K["brassf"], seg=20)
    tube("Wick", [(0, 0, 0.24), (0.005, 0, 0.27)], 0.012, K["linen"], poly=True)
    # the urn
    z0 = zt
    lathe("Body", [(0, 0), (0.3, 0), (0.32, 0.03), (0.2, 0.08), (0.16, 0.15), (0.2, 0.19), (0.34, 0.27), (0.46, 0.45), (0.53, 0.7), (0.54, 0.86),
                   (0.51, 1.05), (0.43, 1.22), (0.32, 1.33), (0.3, 1.38), (0, 1.38)], br, seg=40, loc=(0, 0, z0))
    for z, r in ((0.27, 0.345), (0.86, 0.545), (1.33, 0.322)):
        hoop(f"Band{z}", (0, 0, z0 + z), r, "Z", K["brassf"], thick=0.014)
    lathe("Lid", [(0, 1.37), (0.32, 1.37), (0.33, 1.4), (0.28, 1.47), (0.18, 1.55), (0.08, 1.6), (0.05, 1.63), (0, 1.63)], br, seg=36, loc=(0, 0, z0))
    lathe("Finial", [(0, 0), (0.05, 0), (0.035, 0.04), (0.06, 0.09), (0.05, 0.14), (0.02, 0.18), (0, 0.2)], K["ebony"], seg=16, loc=(0, 0, z0 + 1.62))
    for sx in (-1, 1):
        tube(f"Handle{sx}", [(sx * 0.5, 0, z0 + 1.0), (sx * 0.66, 0, z0 + 1.06), (sx * 0.7, 0, z0 + 1.2), (sx * 0.6, 0, z0 + 1.3), (sx * 0.42, 0, z0 + 1.26)],
             0.026, K["brassf"])
        cyl(f"HandleGrip{sx}", 0.04, 0.16, (sx * 0.69, 0, z0 + 1.15), K["ebony"], verts=12, bevel=0.01)
        sphere(f"HandleBoss{sx}", 0.045, (sx * 0.5, 0, z0 + 1.0), K["brassf"], seg=10, rings=5)
    # the tap: a boss on the body, a pipe forward, a valve with an ebony lever, a nozzle turned down
    zt_ = z0 + 0.36
    cyl("TapBoss", 0.07, 0.08, (0, -0.4, zt_), K["brassf"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.01)
    cyl("TapPipe", 0.035, 0.26, (0, -0.55, zt_), K["brassf"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.006)
    cyl("Valve", 0.055, 0.12, (0, -0.6, zt_ + 0.01), K["brassf"], verts=16, bevel=0.01)
    box("Lever", (0.26, 0.04, 0.03), (0, -0.6, zt_ + 0.1), K["ebony"], bevel=0.012)
    cyl("LeverStem", 0.016, 0.06, (0, -0.6, zt_ + 0.075), K["brassf"], verts=8, bevel=0.0)
    lathe("Nozzle", [(0, 0), (0.03, 0), (0.035, 0.03), (0.03, 0.09), (0, 0.09)], K["brassf"], seg=14, loc=(0, -0.69, zt_ - 0.1))
    tube("NozzleBend", [(0, -0.62, zt_), (0, -0.69, zt_ - 0.01), (0, -0.69, zt_ - 0.06)], 0.03, K["brassf"])
    # the crest medallion on the front: bone enamel with the crest in a brass bezel
    zc = z0 + 0.78
    cyl("MedalBack", 0.235, 0.06, (0, -0.5, zc), K["brassf"], rot=(math.pi / 2, 0, 0), verts=36, bevel=0.01)
    disc_print("Medal", "SP_Mug_Crest", 0.2, 0.02, T(0, -0.535, zc), K["glaze"], rect=CREST_RECT)
    hoop("Bezel", (0, -0.545, zc), 0.21, "Y", K["gilt"], thick=0.016)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        sphere(f"Bead{k}", 0.014, (math.cos(a) * 0.226, -0.535, zc + math.sin(a) * 0.226), K["gilt"], seg=8, rings=4)
    return _dims()


def spirit_kettle(M):
    K = kit(M)
    ir = K["iron"]
    # the stove: a cast-iron ring frame on three legs, pan supports, a brass burner on a base plate
    zt = 0.42
    hoop("Ring", (0, 0, zt), 0.3, "Z", ir, thick=0.03)
    hoop("BaseRing", (0, 0, 0.05), 0.32, "Z", ir, thick=0.025)
    cyl("BasePlate", 0.3, 0.025, (0, 0, 0.06), ir, verts=32, bevel=0.006)
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        c, s = math.cos(a), math.sin(a)
        tube(f"Post{k}", [(c * 0.3, s * 0.3, 0.05), (c * 0.31, s * 0.31, zt)], 0.025, ir, square=True, poly=True)
        tube(f"Foot{k}", [(c * 0.3, s * 0.3, 0.06), (c * 0.38, s * 0.38, 0.04), (c * 0.42, s * 0.42, 0.0)], 0.022, ir)
        tube(f"Prong{k}", [(c * 0.31, s * 0.31, zt), (c * 0.2, s * 0.2, zt + 0.04), (c * 0.14, s * 0.14, zt + 0.04)], 0.016, ir, square=True, poly=True)
        tube(f"Arch{k}", [(c * 0.3, s * 0.3, 0.14), (math.cos(a + 1.05) * 0.335, math.sin(a + 1.05) * 0.335, 0.32),
                          (math.cos(a + 2.09) * 0.3, math.sin(a + 2.09) * 0.3, 0.14)], 0.012, ir)
    lathe("Burner", [(0, 0.07), (0.13, 0.07), (0.14, 0.1), (0.12, 0.16), (0.08, 0.19), (0.08, 0.24), (0.06, 0.25), (0, 0.25)], K["brassf"], seg=24)
    cyl("Snuffer", 0.03, 0.04, (0.12, 0, 0.21), K["brassf"], rot=(0, math.pi / 2, 0), verts=10, bevel=0.005)
    tube("SnufferArm", [(0.14, 0, 0.21), (0.32, 0, 0.18)], 0.008, K["brassf"], poly=True)
    # the kettle
    z0 = zt + 0.035
    cu = K["copper"]
    lathe("Kettle", [(0, 0), (0.22, 0), (0.28, 0.02), (0.33, 0.1), (0.34, 0.2), (0.31, 0.28), (0.24, 0.34), (0.15, 0.37), (0.14, 0.39), (0, 0.39)],
          cu, seg=40, loc=(0, 0, z0))
    hoop("KettleBand", (0, 0, z0 + 0.2), 0.342, "Z", K["brassf"], thick=0.01)
    lathe("Lid", [(0, 0.38), (0.15, 0.38), (0.15, 0.41), (0.1, 0.45), (0.04, 0.46), (0, 0.46)], K["brassf"], seg=28, loc=(0, 0, z0))
    sphere("LidKnob", 0.04, (0, 0, z0 + 0.49), K["ebony"], seg=12, rings=6, scale=(1, 1, 0.8))
    # the spout, rising from the low front and curving out
    pts = [(0, -0.28, z0 + 0.1), (0, -0.38, z0 + 0.16), (0, -0.46, z0 + 0.28), (0, -0.53, z0 + 0.36)]
    tube("Spout", pts, 0.04, cu)
    tube("SpoutTip", [(0, -0.52, z0 + 0.35), (0, -0.56, z0 + 0.38)], 0.032, cu, poly=True)
    hoop("SpoutRim", (0, -0.555, z0 + 0.38), 0.032, "Y", K["brassf"], thick=0.008)
    # a swing handle over the lid, pivoting in lugs at the sides, an ebony grip
    for sx in (-1, 1):
        sphere(f"Lug{sx}", 0.035, (sx * 0.27, 0, z0 + 0.33), K["brassf"], seg=10, rings=5)
    tube("Handle", [(-0.27, 0, z0 + 0.33), (-0.25, 0, z0 + 0.55), (-0.12, 0, z0 + 0.66), (0.12, 0, z0 + 0.66), (0.25, 0, z0 + 0.55), (0.27, 0, z0 + 0.33)],
         0.018, K["brassf"])
    cyl("Grip", 0.035, 0.24, (0, 0, z0 + 0.665), K["ebony"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.01)
    _fine(0.6)
    return _dims()


CHINA_BANDS = [(-1, -1, "SP_crimson")]


def china_bands(zc, w=0.05):
    return [(zc - w / 2 - 0.008, zc - w / 2, "SP_gilt"), (zc - w / 2, zc + w / 2, "SP_crimson"), (zc + w / 2, zc + w / 2 + 0.008, "SP_gilt")]


def teacup(prefix, mtx, K, tea=True):
    s = _mark()
    g = K["glaze"]
    wrap_lathe(f"{prefix}Saucer", [(0, 0), (0.08, 0), (0.09, 0.008), (0.2, 0.028), (0.215, 0.036), (0.2, 0.034), (0.09, 0.02), (0, 0.02)], g,
               bands=[(0.026, 0.037, "SP_gilt")], seg=24, step=0.06)
    prof = [(0, 0.02), (0.055, 0.02), (0.06, 0.03), (0.09, 0.07), (0.125, 0.15), (0.135, 0.18), (0.125, 0.18), (0.115, 0.15), (0.08, 0.075),
            (0.05, 0.04), (0, 0.04)]
    wrap_lathe(f"{prefix}Cup", prof, g, bands=china_bands(0.145, 0.03), seg=22, step=0.035)
    if tea:
        cyl(f"{prefix}Tea", 0.108, 0.004, (0, 0, 0.135), K["tea"], verts=24, bevel=0.0)
    tube(f"{prefix}Handle", [(0.11, 0, 0.15), (0.17, 0, 0.16), (0.19, 0, 0.12), (0.16, 0, 0.08), (0.095, 0, 0.075)], 0.012, g)
    _swatch_uv(P.PARTS[-1], "SP_mugbone")
    _xform(s, mtx)


def teaspoon(name, mtx, K):
    s = _mark()
    tube(name + "Stem", [(0, 0, 0.004), (0.12, 0, 0.006), (0.22, 0, 0.012)], 0.006, K["steel"])
    sphere(name + "Bowl", 0.035, (-0.03, 0, 0.008), K["steel"], seg=12, rings=6, scale=(1.4, 1, 0.3))
    _xform(s, mtx)


def tea_set(M):
    K = kit(M)
    g = K["glaze"]
    W, D = 1.9, 1.25
    zt = 0.06
    box("Tray", (W, D, 0.04), (0, 0, 0.02), K["ebony"], bevel=0.015)
    tube("Gallery", [(x, y, 0.06) for x, y in ((-W / 2 + 0.02, -D / 2 + 0.02), (W / 2 - 0.02, -D / 2 + 0.02), (W / 2 - 0.02, D / 2 - 0.02),
                                              (-W / 2 + 0.02, D / 2 - 0.02))], 0.018, K["brassf"], closed=True, poly=True)
    for sx in (-1, 1):
        tube(f"TrayHandle{sx}", [(sx * (W / 2 - 0.02), -0.2, 0.06), (sx * (W / 2 + 0.06), -0.15, 0.12), (sx * (W / 2 + 0.06), 0.15, 0.12),
                                 (sx * (W / 2 - 0.02), 0.2, 0.06)], 0.018, K["brassf"])
    box("TrayInset", (W - 0.14, D - 0.14, 0.004), (0, 0, 0.042), K["leather"], bevel=0.0)
    # the teapot
    s = _mark()
    prof = [(0, 0), (0.15, 0), (0.17, 0.02), (0.15, 0.03), (0.24, 0.1), (0.29, 0.2), (0.28, 0.3), (0.23, 0.38), (0.16, 0.42), (0.14, 0.43),
            (0.12, 0.43), (0.12, 0.4), (0, 0.4)]
    wrap_lathe("Teapot", prof, g, bands=china_bands(0.24, 0.05), seg=28, step=0.05)
    wrap_lathe("TeapotLid", [(0, 0.42), (0.145, 0.42), (0.14, 0.45), (0.1, 0.48), (0.05, 0.5), (0.03, 0.5), (0.04, 0.53), (0.02, 0.56), (0, 0.56)], g,
               bands=[(0.425, 0.44, "SP_gilt"), (0.5, 0.56, "SP_gilt")], seg=24, step=0.04)
    tube("TeapotSpout", [(0, -0.22, 0.12), (0, -0.33, 0.18), (0, -0.4, 0.3), (0, -0.45, 0.38)], 0.04, g)
    _swatch_uv(P.PARTS[-1], "SP_mugbone")
    tube("TeapotHandle", [(0, 0.25, 0.32), (0, 0.38, 0.33), (0, 0.42, 0.22), (0, 0.36, 0.12), (0, 0.24, 0.1)], 0.026, g)
    _swatch_uv(P.PARTS[-1], "SP_mugbone")
    _xform(s, T(-0.45, 0.2, zt) @ RZ(-30 * DEG))
    # cups and saucers, the sugar bowl, the milk jug
    for k, (x, y, a) in enumerate(((0.25, -0.3, 10), (0.65, 0.05, -20), (-0.05, 0.38, 40))):
        teacup(f"Cup{k}", T(x, y, zt) @ RZ(a * DEG), K, tea=k != 2)
    teaspoon("Spoon", T(0.45, -0.38, zt + 0.03) @ RZ(-15 * DEG), K)
    s = _mark()
    wrap_lathe("SugarBowl", [(0, 0), (0.08, 0), (0.09, 0.02), (0.15, 0.08), (0.17, 0.14), (0.16, 0.2), (0.15, 0.21), (0.14, 0.2), (0, 0.2)], g,
               bands=china_bands(0.13, 0.03), seg=24, step=0.04)
    wrap_lathe("SugarLid", [(0, 0.205), (0.16, 0.205), (0.12, 0.25), (0.05, 0.27), (0.03, 0.27), (0.035, 0.3), (0, 0.31)], g,
               bands=[(0.26, 0.31, "SP_gilt")], seg=20, step=0.04)
    for sx in (-1, 1):
        tube(f"SugarEar{sx}", [(sx * 0.16, 0, 0.17), (sx * 0.22, 0, 0.17), (sx * 0.2, 0, 0.1), (sx * 0.15, 0, 0.09)], 0.012, g)
        _swatch_uv(P.PARTS[-1], "SP_mugbone")
    _xform(s, T(0.6, 0.42, zt))
    s = _mark()
    wrap_lathe("MilkJug", [(0, 0), (0.07, 0), (0.08, 0.02), (0.12, 0.08), (0.12, 0.14), (0.09, 0.2), (0.1, 0.25), (0.09, 0.25), (0.08, 0.2), (0.1, 0.14),
                           (0.1, 0.08), (0, 0.03)], g, bands=china_bands(0.11, 0.025), seg=24, step=0.04)
    jug = P.PARTS[-1]
    for v in jug.data.vertices:          # pull the rim out into a pouring lip at the front
        if v.co.z > 0.22 and v.co.y < 0:
            k = max(0.0, -v.co.y / 0.1) ** 3
            v.co.y -= 0.05 * k
            v.co.z += 0.02 * k
    tube("MilkHandle", [(0, 0.09, 0.2), (0, 0.16, 0.2), (0, 0.17, 0.12), (0, 0.11, 0.06)], 0.012, g)
    _swatch_uv(P.PARTS[-1], "SP_mugbone")
    _xform(s, T(-0.75, -0.35, zt) @ RZ(160 * DEG))
    _fine(0.35)
    return _dims()


def mug_rack(M):
    K = kit(M)
    W, H, t = 2.6, 1.6, 0.1
    oak = K["oak"]
    box("Board", (W, t, H), (0, -t / 2, H / 2), oak, bevel=0.025)
    tube("Bead", [(-W / 2 + 0.08, -t - 0.01, 0.08), (W / 2 - 0.08, -t - 0.01, 0.08), (W / 2 - 0.08, -t - 0.01, H - 0.5), (-W / 2 + 0.08, -t - 0.01, H - 0.5)],
         0.015, K["ebony"], square=True, closed=True, poly=True)
    # the shelf on top on two iron brackets, a crest gable at the back of it
    zs = H - 0.38
    box("Shelf", (W + 0.1, 0.5, 0.07), (0, -0.25, zs), oak, bevel=0.02)
    box("ShelfLip", (W + 0.1, 0.04, 0.08), (0, -0.49, zs + 0.06), K["ebony"], bevel=0.01)
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.25)
        tube(f"Bracket{sx}", [(x, -t, zs - 0.4), (x, -t, zs - 0.03), (x, -0.42, zs - 0.03), (x, -t, zs - 0.4)], 0.018, K["iron"], square=True, poly=True)
        tube(f"BracketScroll{sx}", [(x, -0.14, zs - 0.12), (x, -0.25, zs - 0.1), (x, -0.27, zs - 0.2), (x, -0.2, zs - 0.21)], 0.012, K["iron"])
    _gable("Crest", 0, -0.04, 0.5, H, H + 0.35, 0.06, oak, K["ebony"], edge=0.02)
    foil("CrestFoil", 0, -0.08, H + 0.12, 0.08, K["brassf"], lobes=4, thick=0.01)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.05, (sx * (W / 2 - 0.05), -0.05, H + 0.04), K["brassf"], seg=10, rings=5)
    # on the shelf: a brass tea caddy, a glass sugar jar with a brass lid
    lathe("Caddy", [(0, 0), (0.16, 0), (0.17, 0.02), (0.17, 0.32), (0.15, 0.34), (0, 0.34)], K["brassf"], seg=6, loc=(-0.7, -0.25, zs + 0.035))
    lathe("CaddyLid", [(0, 0.33), (0.165, 0.33), (0.13, 0.38), (0.04, 0.4), (0.04, 0.44), (0, 0.44)], K["brass"], seg=6, loc=(-0.7, -0.25, zs + 0.035))
    lathe("SugarJar", [(0, 0), (0.13, 0), (0.14, 0.03), (0.14, 0.24), (0.1, 0.28), (0, 0.28)], K["china"], seg=24, loc=(0.75, -0.25, zs + 0.035))
    lathe("SugarJarLid", [(0, 0.27), (0.11, 0.27), (0.11, 0.31), (0.03, 0.33), (0.03, 0.36), (0, 0.37)], K["brassf"], seg=20, loc=(0.75, -0.25, zs + 0.035))
    # six cup hooks and six mugs
    keys = ["SP_Mug_Crest", "SP_Mug_Staff", "SP_Mug_Raven", None, "SP_Mug_Stripe", "SP_Mug_Moon"]
    zh = 0.95
    rnd = random.Random(3504)
    for k in range(6):
        x = -W / 2 + 0.3 + k * (W - 0.6) / 5
        cyl(f"HookRose{k}", 0.03, 0.02, (x, -t - 0.01, zh), K["iron"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.005)
        tube(f"Hook{k}", [(x, -t, zh), (x, -0.22, zh - 0.01), (x, -0.27, zh + 0.02), (x, -0.27, zh + 0.07)], 0.014, K["iron"])
        sphere(f"HookTip{k}", 0.018, (x, -0.27, zh + 0.075), K["brassf"], seg=8, rings=4)
        a = rnd.uniform(-8, 8)
        # the handle's inner loop (0.27 from the mug's axis at its top) round the hook's bend
        mug(f"Mug{k}", keys[k], T(x, -0.25 - 0.27, zh - 0.31) @ RZ(a * DEG) @ RX(-6 * DEG), K, plain=None if keys[k] else "SP_crimson")
    return _dims()


def biscuit_barrel(M):
    K = kit(M)
    z0 = 0.06
    lathe("Foot", [(0, 0), (0.27, 0), (0.29, 0.02), (0.27, 0.04), (0.25, 0.065), (0, 0.065)], K["brassf"], seg=36)
    hoop("FootBead", (0, 0, 0.03), 0.285, "Z", K["brassf"], thick=0.008)
    prof = [(0, 0), (0.24, 0), (0.28, 0.03), (0.32, 0.12), (0.34, 0.3), (0.33, 0.48), (0.29, 0.6), (0.27, 0.64), (0.25, 0.64), (0.25, 0.04), (0, 0.04)]
    wrap_lathe("Barrel", prof, K["glaze"], key="SP_Barrel", wrap=(0.03, 0.6), base="SP_mugbone", seg=48, mtx=T(0, 0, z0), step=0.025)
    lathe("Collar", [(0.245, 0.6), (0.29, 0.6), (0.3, 0.63), (0.29, 0.67), (0.245, 0.67)], K["brassf"], seg=40, loc=(0, 0, z0))
    lathe("Lid", [(0, 0.66), (0.3, 0.66), (0.3, 0.69), (0.25, 0.74), (0.15, 0.79), (0.07, 0.81), (0.0, 0.81)], K["brassf"], seg=40, loc=(0, 0, z0))
    lathe("Knob", [(0, 0), (0.03, 0), (0.025, 0.03), (0.055, 0.07), (0.05, 0.1), (0.02, 0.13), (0, 0.13)], K["ebony"], seg=16, loc=(0, 0, z0 + 0.8))
    for sx in (-1, 1):
        sphere(f"Lug{sx}", 0.035, (sx * 0.31, 0, z0 + 0.62), K["brassf"], seg=10, rings=5)
    tube("Bail", [(-0.31, 0, z0 + 0.62), (-0.33, 0, z0 + 0.82), (-0.2, 0, z0 + 1.0), (0.2, 0, z0 + 1.0), (0.33, 0, z0 + 0.82), (0.31, 0, z0 + 0.62)],
         0.016, K["brassf"])
    cyl("BailGrip", 0.03, 0.26, (0, 0, z0 + 1.0), K["ebony"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.008)
    _fine(0.6)
    return _dims()


# ================================================================== kitchenette

COUNTER_W, COUNTER_D, COUNTER_TOP = 6.0, 2.2, 3.0


def counter_door(prefix, cx, y, w, z0, z1, K):
    t = 0.07
    st = 0.18
    yc = y - t / 2
    box(f"{prefix}StileL", (st, t, z1 - z0), (cx - w / 2 + st / 2, yc, (z0 + z1) / 2), K["oak"], bevel=0.015)
    box(f"{prefix}StileR", (st, t, z1 - z0), (cx + w / 2 - st / 2, yc, (z0 + z1) / 2), K["oak"], bevel=0.015)
    box(f"{prefix}RailT", (w - 2 * st + 0.01, t, st), (cx, yc, z1 - st / 2), K["oak"], bevel=0.015)
    box(f"{prefix}RailB", (w - 2 * st + 0.01, t, st + 0.04), (cx, yc, z0 + st / 2 + 0.02), K["oak"], bevel=0.015)
    box(f"{prefix}Back", (w - 2 * st + 0.02, t * 0.5, z1 - z0 - 2 * st), (cx, yc + 0.01, (z0 + z1) / 2), K["oakdk"], bevel=0.0)
    enamel_arch_panel(prefix, cx, y - 0.005, w / 2 - st - 0.06, z0 + st + 0.08, z1 - st - 0.06, K, t=0.035)


def kitchenette_counter(M):
    K = kit(M)
    W, D, H = COUNTER_W, COUNTER_D, COUNTER_TOP
    zk = 0.32
    box("Kick", (W - 0.16, D - 0.3, zk), (0, 0.08, zk / 2), K["ebony"], bevel=0.015)
    box("KickIron", (W - 0.1, 0.03, 0.06), (0, -D / 2 + 0.23 - 0.015, zk - 0.04), K["iron"], bevel=0.008)
    yf = -D / 2 + 0.08               # front of the carcass
    box("Carcass", (W - 0.06, D - 0.1, H - 0.15 - zk), (0, 0.05 - 0.0, zk + (H - 0.15 - zk) / 2), K["oakdk"], bevel=0.02)
    zt0 = H - 0.15
    box("Top", (W + 0.12, D + 0.06, 0.15), (0, -0.0, zt0 + 0.075), K["marble"], bevel=0.045, segments=3)
    box("Upstand", (W + 0.12, 0.1, 0.42), (0, D / 2 - 0.02, H + 0.21), K["marble"], bevel=0.025)
    box("TopIron", (W + 0.08, 0.03, 0.06), (0, -D / 2 + 0.1, zt0 - 0.04), K["iron"], bevel=0.008)
    # the face frame: stiles between the three bays, a rail under the top
    bw = (W - 0.24) / 3
    xs = [-W / 2 + 0.12 + bw * (i + 0.5) for i in range(3)]
    for i in range(4):
        x = -W / 2 + 0.06 + i * (W - 0.12) / 3
        box(f"Stile{i}", (0.14, 0.06, H - 0.15 - zk), (x, yf - 0.03, zk + (H - 0.15 - zk) / 2), K["ebony"], bevel=0.015)
    box("TopRail", (W - 0.06, 0.06, 0.1), (0, yf - 0.03, zt0 - 0.08), K["ebony"], bevel=0.012)
    box("BotRail", (W - 0.06, 0.06, 0.08), (0, yf - 0.03, zk + 0.04), K["ebony"], bevel=0.012)
    y = yf - 0.06
    z_lo, z_hi = zk + 0.1, zt0 - 0.15
    # bay 0: three drawers
    n = 3
    hh = (z_hi - z_lo) / n
    for k in range(n):
        zc = z_lo + hh * (k + 0.5)
        box(f"Drawer0{k}", (bw - 0.1, 0.07, hh - 0.08), (xs[0], y - 0.035, zc), K["oak"], bevel=0.02)
        box(f"DrawerPanel0{k}", (bw - 0.42, 0.02, hh - 0.34), (xs[0], y - 0.075, zc), K["oakdk"], bevel=0.01)
        brass_bail(f"Pull0{k}", xs[0], y - 0.085, zc + 0.04, 0.4, K["brassf"])
    # bays 1 and 2: a drawer over a door
    for b in (1, 2):
        zd = z_hi - 0.3
        box(f"Drawer{b}", (bw - 0.1, 0.07, 0.52), (xs[b], y - 0.035, zd), K["oak"], bevel=0.02)
        box(f"DrawerPanel{b}", (bw - 0.42, 0.02, 0.24), (xs[b], y - 0.075, zd), K["oakdk"], bevel=0.01)
        brass_bail(f"Pull{b}", xs[b], y - 0.085, zd + 0.04, 0.4, K["brassf"])
        counter_door(f"Door{b}", xs[b], y, bw - 0.1, z_lo - 0.04, zd - 0.32, K)
        knob(f"Knob{b}", xs[b] + (bw / 2 - 0.25) * (1 if b == 1 else -1), y - 0.07, (z_lo + zd - 0.36) / 2 + 0.25, K["brassf"])
        keyhole(f"Key{b}", xs[b] + (bw / 2 - 0.25) * (1 if b == 1 else -1), y - 0.07, (z_lo + zd - 0.36) / 2 + 0.05, K)
    # side panels: an iron frame round a crimson enamel field
    for sx in (-1, 1):
        xo = sx * (W / 2 - 0.03 + 0.004)
        box(f"SideField{sx}", (0.012, D - 0.6, H - zk - 0.75), (xo, 0.05, zk + (H - zk - 0.15) / 2), K["enamel"], bevel=0.0)
        tube(f"SideFrame{sx}", [(xo + sx * 0.008, -D / 2 + 0.32, zk + 0.27), (xo + sx * 0.008, D / 2 - 0.22, zk + 0.27),
                                (xo + sx * 0.008, D / 2 - 0.22, zt0 - 0.32), (xo + sx * 0.008, -D / 2 + 0.32, zt0 - 0.32)], 0.022, K["iron"], square=True,
             closed=True, poly=True)
    return _dims()


def ice_box(M):
    K = kit(M)
    W, D, H = 2.4, 1.7, 3.6
    zb = 0.32
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f"Foot{sx}{sy}", [(0, 0), (0.1, 0), (0.13, 0.08), (0.11, 0.2), (0.08, 0.26), (0.09, 0.32), (0, 0.32)], K["ebony"], seg=16,
                  loc=(sx * (W / 2 - 0.18), sy * (D / 2 - 0.18), 0))
    box("Body", (W, D, H - zb - 0.18), (0, 0, zb + (H - zb - 0.18) / 2), K["oak"], bevel=0.03)
    box("Lid", (W + 0.12, D + 0.12, 0.12), (0, 0, H - 0.12), K["oakdk"], bevel=0.035)
    box("LidMould", (W + 0.04, D + 0.04, 0.08), (0, 0, H - 0.21), K["ebony"], bevel=0.02)
    box("Plinth", (W + 0.06, D + 0.06, 0.16), (0, 0, zb + 0.08), K["ebony"], bevel=0.02)
    # the zinc drip tray under the body between the feet
    box("DripTray", (W - 0.6, D - 0.5, 0.08), (0, 0.0, 0.06), K["zinc"], bevel=0.015)
    box("DripTrayLip", (0.4, 0.04, 0.05), (0, -(D - 0.5) / 2 - 0.02, 0.08), K["zinc"], bevel=0.01)
    yf = -D / 2
    doors = [("Ice", zb + 2.0, H - 0.3), ("Food", zb + 0.25, zb + 1.85)]
    for nm, z0, z1 in doors:
        w = W - 0.36
        zc = (z0 + z1) / 2
        # the zinc-lined opening, then the door proud of the body
        tube(f"{nm}Zinc", [(-w / 2 - 0.03, yf - 0.012, z0 - 0.03), (w / 2 + 0.03, yf - 0.012, z0 - 0.03), (w / 2 + 0.03, yf - 0.012, z1 + 0.03),
                           (-w / 2 - 0.03, yf - 0.012, z1 + 0.03)], 0.03, K["zinc"], square=True, closed=True, poly=True)
        box(f"{nm}Door", (w, 0.1, z1 - z0), (0, yf - 0.06, zc), K["oak"], bevel=0.025)
        box(f"{nm}Panel", (w - 0.4, 0.04, z1 - z0 - 0.4), (0, yf - 0.12, zc), K["oakdk"], bevel=0.03, segments=3)
        tube(f"{nm}Bead", [(-w / 2 + 0.16, yf - 0.115, z0 + 0.16), (w / 2 - 0.16, yf - 0.115, z0 + 0.16), (w / 2 - 0.16, yf - 0.115, z1 - 0.16),
                           (-w / 2 + 0.16, yf - 0.115, z1 - 0.16)], 0.016, K["ebony"], square=True, closed=True, poly=True)
        # hinges on the left, a lever latch on the right
        for z in (z0 + 0.25, z1 - 0.25):
            cyl(f"{nm}Knuckle{z:.1f}", 0.04, 0.28, (-w / 2 - 0.02, yf - 0.06, z), K["brassf"], verts=12, bevel=0.008)
            box(f"{nm}Leaf{z:.1f}", (0.3, 0.015, 0.2), (-w / 2 + 0.13, yf - 0.118, z), K["brassf"], bevel=0.006)
        zl = zc
        box(f"{nm}LatchPlate", (0.14, 0.03, 0.4), (w / 2 - 0.14, yf - 0.12, zl), K["brassf"], bevel=0.01)
        cyl(f"{nm}LatchPivot", 0.04, 0.05, (w / 2 - 0.14, yf - 0.15, zl + 0.08), K["brassf"], rot=(math.pi / 2, 0, 0), verts=12, bevel=0.006)
        tube(f"{nm}Lever", [(w / 2 - 0.14, yf - 0.18, zl + 0.08), (w / 2 + 0.06, yf - 0.19, zl + 0.06), (w / 2 + 0.2, yf - 0.16, zl + 0.0)], 0.022,
             K["brassf"])
        box(f"{nm}Catch", (0.1, 0.06, 0.16), (w / 2 + 0.2, yf - 0.03, zl), K["brassf"], bevel=0.01)
    # the brass ICE plate on the ice door's top rail
    zc = H - 0.62
    box("Plate", (0.6, 0.02, 0.22), (0, yf - 0.13, zc + 0.22), K["brassf"], bevel=0.008)
    _text("PlateWord", "ICE", FONT, K["gilt"], lambda x, y, h: (x, yf - 0.14 - h, zc + 0.22 + y), fit=(0.4, 0.13), depth=0.012, res=4)
    # side panels
    for sx in (-1, 1):
        xo = sx * (W / 2 + 0.005)
        for z0, z1 in ((zb + 0.3, zb + 1.8), (zb + 2.0, H - 0.35)):
            box(f"Side{sx}{z0:.1f}", (0.04, D - 0.5, z1 - z0), (xo, 0, (z0 + z1) / 2), K["oakdk"], bevel=0.015)
    return _dims()


# ================================================================== marking

def exercise_book(name, key, back, mtx, K, w=0.62, d=0.8, t=0.034):
    DM.pbox(name, (w, d, t), (0, 0, t / 2), K["sp"], {"top": key, "bottom": back, "else": "sw:SP_paper"}, k=2.0, mtx=mtx)


def red_pen(prefix, mtx, K):
    s = _mark()
    cyl(f"{prefix}Barrel", 0.028, 0.32, (0, 0, 0), K["red"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.008)
    cyl(f"{prefix}Cap", 0.031, 0.2, (0.24, 0, 0), K["red"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.008)
    cyl(f"{prefix}Band", 0.032, 0.025, (0.15, 0, 0), K["gilt"], rot=(0, math.pi / 2, 0), verts=14, bevel=0.004)
    sphere(f"{prefix}End", 0.03, (0.34, 0, 0), K["red"], seg=12, rings=6, scale=(0.7, 1, 1))
    box(f"{prefix}Clip", (0.15, 0.012, 0.012), (0.25, 0, 0.034), K["gilt"], bevel=0.004)
    s2 = _mark()
    lathe(f"{prefix}Grip", [(0, 0), (0.026, 0), (0.02, 0.06), (0, 0.065)], K["ink"], seg=12)
    lathe(f"{prefix}Nib", [(0, 0), (0.016, 0), (0.008, 0.05), (0, 0.06)], K["gilt"], seg=8, loc=(0, 0, 0.06))
    _xform(s2, T(-0.16, 0, 0) @ RY(-math.pi / 2))
    _xform(s, mtx)


def marking_stack(M):
    K = kit(M)
    rnd = random.Random(3508)
    covers = ["SP_Ex_Crimson", "SP_Ex_Ink", "SP_Ex_Kraft"]
    backs = {"SP_Ex_Crimson": "sw:SP_excrim", "SP_Ex_Ink": "sw:SP_exink", "SP_Ex_Kraft": "sw:SP_kraft"}
    z = 0.0
    for k in range(9):
        key = covers[rnd.randrange(3)] if k < 8 else "SP_Ex_Crimson"
        exercise_book(f"Book{k}", key, backs[key], T(rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), z) @ RZ(rnd.uniform(-7, 7) * DEG), K)
        z += 0.036
    red_pen("Pen", T(0.0, -0.05, z + 0.03) @ RZ(28 * DEG), K)
    # the marked sheets beside it, the top one pulled out
    for k, (key, x, y, a) in enumerate((("SP_Sheet_B", 0.85, 0.05, -12), ("SP_Sheet_A", 0.95, -0.2, 8), ("SP_Sheet_C", 0.7, 0.35, 25))):
        DM.sheet(f"Sheet{k}", key, 0.6, 0.79, T(x, y, 0.004 + k * 0.005) @ RZ(a * DEG), K["sp"], curl=rnd.uniform(0.01, 0.025), lift=0.01, rnd=rnd)
    # an open book face down on the far side
    exercise_book("Open", "SP_Ex_Ink", "sw:SP_exink", T(-0.82, 0.25, 0.0) @ RZ(-20 * DEG), K, w=0.6, d=0.78, t=0.02)
    _fine(0.35)
    return _dims()


def gradebook(M):
    K = kit(M)
    W, D = 1.7, 1.15
    pw = W / 2 - 0.05
    for sx in (-1, 1):
        box(f"Board{sx}", (W / 2, D + 0.06, 0.04), (sx * W / 4, 0, 0.02), K["leather"], bevel=0.012)
        box(f"Corner{sx}", (0.18, 0.18, 0.042), (sx * (W / 2 - 0.08), -D / 2 + 0.06, 0.021), K["brassf"], bevel=0.008)
        box(f"CornerB{sx}", (0.18, 0.18, 0.042), (sx * (W / 2 - 0.08), D / 2 - 0.06, 0.021), K["brassf"], bevel=0.008)
        box(f"Block{sx}", (pw - 0.04, D - 0.04, 0.08), (sx * (pw / 2 + 0.05), 0, 0.08), K["paper"], bevel=0.02)
    cyl("Spine", 0.06, D + 0.06, (0, 0, 0.04), K["leather"], rot=(math.pi / 2, 0, 0), verts=16, bevel=0.008)

    def page(side):
        def fn(sv, tv):
            x = side * (0.03 + sv * pw)
            z = 0.12 + 0.11 * math.sin(min(1.0, sv * 1.15) * math.pi / 2) ** 0.6 - 0.04 * sv ** 3
            return (x, -D / 2 + 0.02 + tv * (D - 0.04), z)
        return fn
    B30.leaf_sheet("PageL", "SP_Ledger_L", lambda s, t: page(-1)(1 - s, t), 12, 2, (0, 0, 1, 1), K["sp"], thick=0.008, k=3.0)
    B30.leaf_sheet("PageR", "SP_Ledger_R", page(1), 12, 2, (0, 0, 1, 1), K["sp"], thick=0.008, k=3.0)
    box("Ribbon", (0.04, 0.5, 0.006), (0.1, -D / 2 - 0.18, 0.06), K["velvet"], bevel=0.0, rot=(0.3, 0, 0))
    # an inkwell and a dip pen beside it
    x0, y0 = 1.25, 0.25
    lathe("Inkwell", [(0, 0), (0.15, 0), (0.16, 0.02), (0.16, 0.12), (0.12, 0.16), (0.06, 0.17), (0.06, 0.21), (0, 0.21)], K["inkglass"], seg=8,
          loc=(x0, y0, 0))
    cyl("Ink", 0.13, 0.08, (x0, y0, 0.06), K["ink"], verts=8, bevel=0.0)
    lathe("InkCollar", [(0.055, 0.19), (0.075, 0.19), (0.075, 0.23), (0.055, 0.23)], K["brassf"], seg=16, loc=(x0, y0, 0))
    s = _mark()
    lathe("InkLid", [(0, 0), (0.08, 0), (0.08, 0.025), (0.05, 0.04), (0.02, 0.06), (0, 0.06)], K["brassf"], seg=16)
    _xform(s, T(x0, y0 + 0.12, 0.27) @ RX(-70 * DEG))
    s = _mark()
    lathe("PenHolder", [(0, 0), (0.016, 0), (0.024, 0.1), (0.022, 0.42), (0.014, 0.5), (0, 0.5)], K["ebony"], seg=10)
    lathe("PenFerrule", [(0.016, -0.06), (0.019, -0.06), (0.019, 0.02), (0.016, 0.02)], K["brassf"], seg=10)
    strip("PenNib", [(0, 0, -0.06), (0, 0, -0.1), (0, 0, -0.13)], 0.025, (1, 0, 0), K["steel"], thick=0.004, it=1)
    _xform(s, T(x0 - 0.15, y0 - 0.45, 0.03) @ RZ(-25 * DEG) @ RY(-86 * DEG))
    _fine(0.35)
    return _dims()


def staff_rota_board(M):
    K = kit(M)
    W, H = 4.6, 3.6
    zc = 2.05
    oak = K["oak"]
    box("Back", (W - 0.1, 0.08, H - 0.1), (0, -0.04, H / 2), K["oakdk"], bevel=0.01)
    B30.plate("Slate", "SP_Rota", 3.98, 2.65, 0.04, T(0, -0.1, zc), K["sp"], edge="SP_slate", k=3.0)
    fw = 0.24
    for nm, sz, loc in (("FrameT", (W, 0.16, fw), (0, -0.12, H - fw / 2)), ("FrameB", (W, 0.16, fw), (0, -0.12, zc - 1.325 - fw / 2 + 0.02)),
                        ("FrameL", (fw, 0.16, H), (-W / 2 + fw / 2, -0.12, H / 2)), ("FrameR", (fw, 0.16, H), (W / 2 - fw / 2, -0.12, H / 2)),
                        ("FrameFoot", (W, 0.16, fw), (0, -0.12, fw / 2))):
        box(nm, sz, loc, oak, bevel=0.04, segments=3)
    tube("SlateBead", [(-1.99, -0.125, zc - 1.325), (1.99, -0.125, zc - 1.325), (1.99, -0.125, zc + 1.325), (-1.99, -0.125, zc + 1.325)], 0.02,
         K["gilt"], square=True, closed=True, poly=True)
    # the crest gable
    _gable("Crest", 0, -0.1, 0.9, H - 0.02, H + 0.55, 0.1, oak, K["ebony"], edge=0.03)
    foil("CrestFoil", 0, -0.16, H + 0.18, 0.13, K["brassf"], lobes=4, thick=0.014)
    for sx in (-1, 1):
        sphere(f"Finial{sx}", 0.08, (sx * (W / 2 - 0.12), -0.12, H + 0.06), K["brassf"], seg=12, rings=6)
    # the chalk ledge
    zl = zc - 1.325 - fw + 0.02
    box("Ledge", (W - 0.6, 0.36, 0.05), (0, -0.33, zl + 0.03), oak, bevel=0.015)
    box("LedgeLip", (W - 0.6, 0.04, 0.06), (0, -0.5, zl + 0.07), K["ebony"], bevel=0.01)
    for k, x in enumerate((-1.2, -1.0, 0.9)):
        cyl(f"Chalk{k}", 0.03, 0.3 - k * 0.06, (x, -0.33, zl + 0.085), K["chalk"], rot=(0, math.pi / 2, 0.2 * k), verts=10, bevel=0.005)
    box("DusterWood", (0.5, 0.18, 0.08), (1.4, -0.32, zl + 0.15), oak, bevel=0.02)
    box("DusterFelt", (0.48, 0.16, 0.04), (1.4, -0.32, zl + 0.09), K["felt"], bevel=0.008)
    # the name rail below: brass hooks and bone tags
    zr = 0.62
    box("Rail", (W - 0.6, 0.06, 0.12), (0, -0.12, zr), K["brassf"], bevel=0.015)
    for k in range(6):
        x = -1.75 + k * 0.7
        tube(f"Hook{k}", [(x, -0.15, zr), (x, -0.24, zr - 0.02), (x, -0.25, zr + 0.05)], 0.012, K["brassf"])
        hoop(f"Ring{k}", (x, -0.23, zr - 0.07), 0.04, "X", K["brassf"], thick=0.008)
        a = (k % 3 - 1) * 3
        B30.plate(f"Tag{k}", f"SP_Tag_{k}", 0.56, 0.235, 0.015, T(x + 0.215, -0.22, zr - 0.22) @ RY(a * DEG), K["sp"], edge="SP_bone", k=2.5)
    return _dims()


def wall_telephone(M):
    K = kit(M)
    oak, br = K["oak"], K["brassf"]
    box("Backboard", (1.2, 0.06, 2.75), (0, -0.03, 1.375), K["oakdk"], bevel=0.02)
    # the bell box
    zb0, zb1 = 1.55, 2.6
    box("BellBox", (0.95, 0.45, zb1 - zb0), (0, -0.285, (zb0 + zb1) / 2), oak, bevel=0.025)
    box("BellBoxTop", (1.03, 0.5, 0.08), (0, -0.29, zb1 + 0.03), K["oakdk"], bevel=0.02)
    _gable("BoxCrest", 0, -0.29, 0.38, zb1 + 0.07, zb1 + 0.3, 0.05, oak, K["ebony"], edge=0.015)
    box("BellPanel", (0.7, 0.03, 0.52), (0, -0.52, zb0 + 0.45), K["oakdk"], bevel=0.012)
    for sx in (-1, 1):
        s = _mark()
        lathe(f"Bell{sx}", [(0, 0), (0.17, 0), (0.17, 0.03), (0.15, 0.08), (0.1, 0.12), (0.04, 0.14), (0, 0.14)], br, seg=28)
        _xform(s, T(sx * 0.2, -0.535, zb1 - 0.22) @ RX(math.pi / 2))
        sphere(f"BellNut{sx}", 0.025, (sx * 0.2, -0.68, zb1 - 0.22), br, seg=8, rings=4)
    tube("Striker", [(0, -0.54, zb1 - 0.42), (0, -0.62, zb1 - 0.3), (0, -0.62, zb1 - 0.22)], 0.012, br)
    sphere("StrikerBall", 0.03, (0, -0.62, zb1 - 0.2), br, seg=8, rings=4)
    # the mouthpiece on its arm
    zm = zb0 + 0.25
    cyl("ArmBase", 0.07, 0.04, (0, -0.53, zm), br, rot=(math.pi / 2, 0, 0), verts=14, bevel=0.008)
    tube("Arm", [(0, -0.53, zm), (0, -0.7, zm + 0.02), (0, -0.8, zm + 0.1)], 0.028, br)
    s = _mark()
    lathe("Horn", [(0, 0), (0.04, 0), (0.05, 0.05), (0.08, 0.12), (0.13, 0.18), (0.14, 0.2), (0.12, 0.2), (0.07, 0.15), (0, 0.13)], K["ebony"], seg=24)
    _xform(s, T(0, -0.8, zm + 0.1) @ RX(math.pi / 2 + 0.25))
    # the crank on the right side
    x = 0.475
    cyl("CrankBoss", 0.06, 0.04, (x + 0.02, -0.3, zb0 + 0.55), br, rot=(0, math.pi / 2, 0), verts=14, bevel=0.008)
    tube("CrankArm", [(x + 0.05, -0.3, zb0 + 0.55), (x + 0.06, -0.33, zb0 + 0.42), (x + 0.07, -0.34, zb0 + 0.35)], 0.016, br)
    cyl("CrankKnob", 0.03, 0.12, (x + 0.13, -0.34, zb0 + 0.35), K["ebony"], rot=(0, math.pi / 2, 0), verts=12, bevel=0.008)
    # the earpiece hanging on its hook at the left, its cord looping down to the box
    x = -0.475
    tube("Hook", [(x - 0.02, -0.3, zb0 + 0.62), (x - 0.12, -0.3, zb0 + 0.6), (x - 0.15, -0.3, zb0 + 0.68)], 0.018, br)
    tube("HookFork", [(x - 0.15, -0.34, zb0 + 0.68), (x - 0.15, -0.26, zb0 + 0.68)], 0.012, br, poly=True)
    s = _mark()
    lathe("Earpiece", [(0, 0), (0.035, 0), (0.04, 0.06), (0.04, 0.3), (0.06, 0.34), (0.1, 0.38), (0.11, 0.42), (0.09, 0.43), (0.05, 0.42), (0, 0.42)],
          K["ebony"], seg=20)
    hoop("EarBand", (0, 0, 0.32), 0.045, "Z", br, thick=0.01)
    _xform(s, T(x - 0.15, -0.3, zb0 + 0.75) @ RX(math.pi))
    tube("Cord", [(x - 0.15, -0.3, zb0 + 0.33), (x - 0.18, -0.32, zb0 + 0.1), (x - 0.12, -0.36, zb0 - 0.1), (x - 0.02, -0.4, zb0 + 0.05),
                  (x + 0.01, -0.4, zb0 + 0.2)], 0.012, K["cord"])
    # the writing shelf
    box("Shelf", (1.1, 0.42, 0.05), (0, -0.27, zb0 - 0.12), oak, bevel=0.015, rot=(-6 * DEG, 0, 0))
    for sx in (-1, 1):
        tube(f"ShelfBracket{sx}", [(sx * 0.45, -0.06, zb0 - 0.45), (sx * 0.45, -0.06, zb0 - 0.15), (sx * 0.45, -0.42, zb0 - 0.13)], 0.018, K["iron"],
             square=True, poly=True)
    # the battery box below
    box("BatteryBox", (0.85, 0.42, 1.05), (0, -0.27, 0.2 + 0.525), oak, bevel=0.025)
    box("BatteryDoor", (0.65, 0.03, 0.82), (0, -0.495, 0.73), K["oakdk"], bevel=0.012)
    knob("BatteryKnob", 0.24, -0.51, 0.73, br, r=0.035)
    box("BatteryCap", (0.9, 0.46, 0.06), (0, -0.28, 1.27), K["oakdk"], bevel=0.015)
    box("BatteryFoot", (0.9, 0.46, 0.06), (0, -0.28, 0.2), K["oakdk"], bevel=0.015)
    return _dims()


def card_table(M):
    K = kit(M)
    W, H = 2.8, 2.45
    rnd = random.Random(3512)
    box("Apron", (W - 0.3, W - 0.3, 0.24), (0, 0, H - 0.17), K["ebony"], bevel=0.02)
    box("Frame", (W, W, 0.08), (0, 0, H - 0.04), K["ebony"], bevel=0.025)
    box("Baize", (W - 0.36, W - 0.36, 0.012), (0, 0, H + 0.002), K["baize"], bevel=0.0)
    tube("Bead", [(x, y, H - 0.002) for x, y in ((-W / 2 + 0.18, -W / 2 + 0.18), (W / 2 - 0.18, -W / 2 + 0.18), (W / 2 - 0.18, W / 2 - 0.18),
                                                (-W / 2 + 0.18, W / 2 - 0.18))], 0.014, K["brassf"], closed=True, poly=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"CornerCap{sx}{sy}", (0.22, 0.22, 0.086), (sx * (W / 2 - 0.1), sy * (W / 2 - 0.1), H - 0.04), K["brassf"], bevel=0.01)
            x, y = sx * (W / 2 - 0.22), sy * (W / 2 - 0.22)
            lathe(f"Leg{sx}{sy}", [(0, 0), (0.05, 0), (0.06, 0.06), (0.05, 0.12), (0.06, 0.9), (0.075, 1.6), (0.09, 1.95), (0.09, H - 0.29), (0, H - 0.29)],
                  K["ebony"], seg=12, loc=(x, y, 0))
            cyl(f"Ferrule{sx}{sy}", 0.058, 0.08, (x, y, 0.04), K["brassf"], verts=12, bevel=0.006)
    # the folding braces: an iron X under the apron on each pair of legs
    for sy in (-1, 1):
        y = sy * (W / 2 - 0.22)
        tube(f"BraceA{sy}", [(-(W / 2 - 0.22), y, 0.7), ((W / 2 - 0.22), y, H - 0.32)], 0.022, K["iron"], poly=True)
        tube(f"BraceB{sy}", [((W / 2 - 0.22), y, 0.7), (-(W / 2 - 0.22), y, H - 0.32)], 0.022, K["iron"], poly=True)
        sphere(f"BracePin{sy}", 0.04, (0, y, (0.7 + H - 0.32) / 2), K["brassf"], seg=10, rings=5)
    # the game: two fanned hands, the deck, a face-up pile, chips
    z = H + 0.01
    cw, ch, ct = 0.24, 0.34, 0.006
    faces_ = ["SP_Card_1S", "SP_Card_7H", "SP_Card_10D", "SP_Card_3C", "SP_Card_9S", "SP_Card_5H"]
    for hand, (hx, hy, ha, up) in enumerate(((-0.55, -0.75, 0, True), (0.6, 0.7, 180, False))):
        for k in range(5):
            a = (k - 2) * 12
            key = faces_[(k + hand * 2) % 6] if up else "SP_Card_Back"
            DM.pbox(f"Hand{hand}{k}", (cw, ch, ct), (0, 0, 0), K["sp"], {"top": key, "else": "sw:SP_card"}, k=2.2,
                    mtx=T(hx, hy, z + ct / 2 + k * 0.004) @ RZ((ha + a) * DEG) @ T(0, ch * 0.35))
    for k in range(14):
        DM.pbox(f"Deck{k}", (cw, ch, ct), (0, 0, 0), K["sp"], {"top": "SP_Card_Back", "else": "sw:SP_card"}, k=1.2 if k < 13 else 2.2,
                mtx=T(0.05, -0.05, z + ct / 2 + k * ct) @ RZ((rnd.uniform(-3, 3) - 8) * DEG))
    for k, key in enumerate(("SP_Card_9S", "SP_Card_5H", "SP_Card_3C")):
        DM.pbox(f"Pile{k}", (cw, ch, ct), (0, 0, 0), K["sp"], {"top": key, "else": "sw:SP_card"}, k=2.2,
                mtx=T(-0.35 + k * 0.03, 0.15, z + ct / 2 + k * ct) @ RZ(rnd.uniform(-25, 25) * DEG))
    chip = {"c": flat("ChipCrimson", (0.2, 0.015, 0.025), 0.35), "b": flat("ChipBone", (0.62, 0.57, 0.46), 0.35),
            "i": flat("ChipInk", (0.02, 0.022, 0.04), 0.35)}
    for k, (x, y, n, c) in enumerate(((0.8, -0.6, 6, "c"), (0.95, -0.45, 4, "b"), (0.7, -0.4, 8, "i"), (-0.9, 0.6, 5, "b"), (-0.75, 0.75, 3, "c"),
                                      (0.15, -0.55, 2, "i"))):
        for j in range(n):
            cyl(f"Chip{k}{j}", 0.07, 0.02, (x + rnd.uniform(-0.006, 0.006), y + rnd.uniform(-0.006, 0.006), z + 0.01 + j * 0.021), chip[c], verts=16,
                bevel=0.004)
    return _dims()


def staff_only_sign(M):
    K = kit(M)
    w, h, t = 1.8, 0.55, 0.06
    zc = h / 2
    box("Plate", (w, t, h), (0, -t / 2, zc), K["brassf"], bevel=0.02)
    box("Field", (w - 0.2, 0.012, h - 0.18), (0, -t - 0.004, zc), K["enamel"], bevel=0.0)
    tube("Border", [(-w / 2 + 0.08, -t - 0.008, zc - h / 2 + 0.08), (w / 2 - 0.08, -t - 0.008, zc - h / 2 + 0.08), (w / 2 - 0.08, -t - 0.008, zc + h / 2 - 0.08),
                    (-w / 2 + 0.08, -t - 0.008, zc + h / 2 - 0.08)], 0.012, K["gilt"], square=True, closed=True, poly=True)
    for sx in (-1, 1):
        sphere(f"Screw{sx}", 0.03, (sx * (w / 2 - 0.04), -t, zc), K["ironf"], seg=10, rings=5, scale=(1, 0.45, 1))
        box(f"Slot{sx}", (0.04, 0.01, 0.008), (sx * (w / 2 - 0.04), -t - 0.013, zc), K["ink"], bevel=0.0)
        foil(f"Foil{sx}", sx * (w / 2 - 0.2), -t - 0.012, zc, 0.06, K["gilt"], lobes=4, thick=0.008, n=8)
    _text("Word", "STAFF ONLY", FONT, K["gilt"], lambda x, y, hh: (x, -t - 0.01 - hh, zc + y), fit=(w - 0.65, h - 0.26), depth=0.018, res=5)
    _fine(0.4)
    return _dims()


def dartboard(M):
    K = kit(M)
    W, H, D = 2.2, 2.4, 0.36
    oak = K["oak"]
    zc = H / 2
    box("CabBack", (W, 0.06, H), (0, -0.03, zc), K["oakdk"], bevel=0.01)
    for nm, sz, loc in (("CabTop", (W, D, 0.1), (0, -D / 2, H - 0.05)), ("CabBot", (W, D, 0.1), (0, -D / 2, 0.05)),
                        ("CabL", (0.1, D, H), (-W / 2 + 0.05, -D / 2, zc)), ("CabR", (0.1, D, H), (W / 2 - 0.05, -D / 2, zc))):
        box(nm, sz, loc, oak, bevel=0.02)
    box("Cornice", (W + 0.12, D + 0.06, 0.08), (0, -D / 2 - 0.03, H + 0.02), K["ebony"], bevel=0.02)
    box("Inside", (W - 0.2, 0.02, H - 0.2), (0, -0.07, zc), K["leather"], bevel=0.0)
    # the board
    zb = zc + 0.02
    disc_print("Board", "SP_Dartboard", 0.86, 0.16, T(0, -0.16, zb), K["sp"], edge="SP_dart", seg=64, k=3.0)
    hoop("BoardRim", (0, -0.24, zb), 0.86, "Y", K["iron"], thick=0.02)
    # three darts in the board
    for k, (x, z, ax, az) in enumerate(((0.05, 0.62, 8, -5), (-0.18, 0.2, -6, 10), (0.32, -0.12, 4, 14))):
        s = _mark()
        lathe(f"Dart{k}Point", [(0, 0), (0.008, 0), (0.008, 0.1), (0, 0.12)], K["steel"], seg=8, loc=(0, 0, -0.12))
        lathe(f"Dart{k}Barrel", [(0, 0), (0.016, 0), (0.024, 0.04), (0.024, 0.14), (0.014, 0.18), (0, 0.18)], K["brassf"], seg=10)
        cyl(f"Dart{k}Shaft", 0.008, 0.14, (0, 0, 0.24), K["ink"], verts=8, bevel=0.0)
        for a in (0, 90):
            box(f"Dart{k}Flight{a}", (0.14, 0.004, 0.14), (0, 0, 0.32), K["enamel"], bevel=0.0, rot=(0, 0, a * DEG))
        _xform(s, T(x, -0.24 - 0.0, zb + z) @ RZ(az * DEG) @ RX((90 + ax) * DEG))
    # the doors swung open almost flat against the wall either side; their insides face the room. The left one holds the
    # chalk score slate, the right one a rest of spare darts
    dw = W / 2
    for sx in (-1, 1):
        s = _mark()
        # built open at the hinge (origin): the door runs outward along sx, its inside face toward -Y
        box(f"Door{sx}", (dw, 0.08, H), (sx * dw / 2, 0.04, zc), oak, bevel=0.02)
        box(f"DoorPanel{sx}", (dw - 0.3, 0.03, H - 0.4), (sx * dw / 2, 0.092, zc), K["oakdk"], bevel=0.012)
        box(f"DoorIn{sx}", (dw - 0.24, 0.02, H - 0.34), (sx * dw / 2, -0.005, zc), K["oakdk"], bevel=0.008)
        if sx < 0:
            B30.plate("Score", "SP_Score", 0.72, 1.05, 0.03, T(sx * dw / 2, -0.03, zc + 0.15), K["sp"], edge="SP_slate", k=2.6)
            box("ChalkCup", (0.4, 0.1, 0.06), (sx * dw / 2, -0.06, zc - 0.48), oak, bevel=0.01)
            cyl("ScoreChalk", 0.025, 0.18, (sx * dw / 2, -0.07, zc - 0.43), K["chalk"], rot=(0, math.pi / 2, 0), verts=8, bevel=0.004)
        else:
            box("DartRest", (0.6, 0.1, 0.05), (dw / 2, -0.06, zc - 0.03), oak, bevel=0.01)
            for k in range(3):
                x = dw / 2 - 0.15 + k * 0.15
                lathe(f"SpareBarrel{k}", [(0, 0), (0.016, 0), (0.022, 0.03), (0.022, 0.12), (0.012, 0.15), (0, 0.15)], K["brassf"], seg=10,
                      loc=(x, -0.06, zc))
                cyl(f"SpareShaft{k}", 0.007, 0.12, (x, -0.06, zc + 0.2), K["ink"], verts=8, bevel=0.0)
                for a in (0, 90):
                    box(f"SpareFlight{k}{a}", (0.12, 0.004, 0.12), (x, -0.06, zc + 0.3), K["enamel"], bevel=0.0, rot=(0, 0, (a + 45) * DEG))
        for z in (0.35, H - 0.35):
            cyl(f"Hinge{sx}{z:.1f}", 0.03, 0.2, (0, 0.0, z), K["brassf"], verts=10, bevel=0.005)
        knob(f"Knob{sx}", sx * (dw - 0.12), -0.01, zc, K["brassf"], r=0.035)
        _xform(s, T(sx * W / 2, -D - 0.04, 0) @ RZ(sx * 14 * DEG))
    return _dims()


def staff_lockers(M):
    K = kit(M)
    n, lw, D, H = 3, 1.6, 1.6, 7.2
    W = n * lw + 0.16
    oak = K["oak"]
    zb = 0.4
    box("Plinth", (W, D - 0.1, zb), (0, 0.05, zb / 2), K["ebony"], bevel=0.02)
    box("Body", (W, D - 0.1, H - zb - 0.5), (0, 0.05, zb + (H - zb - 0.5) / 2), K["oakdk"], bevel=0.02)
    box("Cornice", (W + 0.2, D + 0.06, 0.18), (0, 0.0, H - 0.41), oak, bevel=0.05, segments=3)
    box("CorniceTop", (W + 0.3, D + 0.12, 0.12), (0, 0.0, H - 0.26), K["ebony"], bevel=0.03)
    box("Frieze", (W, 0.06, 0.25), (0, -D / 2 + 0.07, H - 0.62), oak, bevel=0.015)
    yf = -D / 2 + 0.04
    for i in range(n + 1):
        x = -W / 2 + 0.08 + i * lw
        box(f"Stile{i}", (0.16, 0.08, H - zb - 0.75), (x, yf - 0.04, zb + (H - zb - 0.75) / 2), K["ebony"], bevel=0.015)
    for i in range(n):
        cx = -W / 2 + 0.08 + (i + 0.5) * lw
        dw = lw - 0.2
        z0, z1 = zb + 0.08, H - 0.82
        y = yf - 0.08
        t = 0.08
        box(f"D{i}StileL", (0.2, t, z1 - z0), (cx - dw / 2 + 0.1, y - t / 2, (z0 + z1) / 2), oak, bevel=0.02)
        box(f"D{i}StileR", (0.2, t, z1 - z0), (cx + dw / 2 - 0.1, y - t / 2, (z0 + z1) / 2), oak, bevel=0.02)
        for nm, z, hh in (("T", z1 - 0.12, 0.24), ("M", z0 + 2.6, 0.22), ("B", z0 + 0.15, 0.3)):
            box(f"D{i}Rail{nm}", (dw - 0.38, t, hh), (cx, y - t / 2, z), oak, bevel=0.02)
        box(f"D{i}Back", (dw - 0.36, 0.03, z1 - z0 - 0.2), (cx, y - 0.01, (z0 + z1) / 2), K["oakdk"], bevel=0.0)
        # the lower raised panel
        box(f"D{i}Raised", (dw - 0.58, 0.05, 2.0), (cx, y - 0.04, z0 + 1.43), oak, bevel=0.05, segments=3)
        # the upper vent: louvres under a pointed iron arch
        hw = dw / 2 - 0.22
        za, zs = z1 - 0.3, z1 - 0.3 - hw * 1.3
        vz0 = z0 + 2.85
        for k in range(int((zs - vz0) / 0.13)):
            box(f"D{i}Louvre{k}", (2 * hw, 0.08, 0.035), (cx, y - 0.035, vz0 + 0.07 + k * 0.13), K["ebony"], bevel=0.008, rot=(-35 * DEG, 0, 0))
        arch = WS.arch(hw, vz0, zs, za, 12, cx=cx)
        tube(f"D{i}Arch", [(x, y - 0.08, z) for x, z in arch] + [(arch[0][0], y - 0.08, arch[0][1])], 0.025, K["iron"], square=True, poly=True)
        top = [(cx + x, z) for x, z in WS.pointed(hw, zs, za, 12)]
        B20.tprism(f"D{i}ArchFill", WS.ccw(top + [(cx, za)]), y - 0.04, 0.05, K["enamel"])
        # name plate, keyhole, lever handle, hinges
        zp = z0 + 3.9 - 1.0
        box(f"D{i}PlateFrame", (0.68, 0.025, 0.3), (cx, y - t - 0.012, zp), K["brassf"], bevel=0.008)
        B30.plate(f"D{i}Tag", f"SP_Tag_{i}", 0.56, 0.22, 0.01, T(cx, y - t - 0.03, zp), K["sp"], edge="SP_bone", k=2.5)
        tube(f"D{i}PlateRim", [(cx - 0.31, y - t - 0.036, zp - 0.13), (cx + 0.31, y - t - 0.036, zp - 0.13), (cx + 0.31, y - t - 0.036, zp + 0.13),
                               (cx - 0.31, y - t - 0.036, zp + 0.13)], 0.012, K["brassf"], square=True, closed=True, poly=True)
        hx = cx + dw / 2 - 0.12
        keyhole(f"D{i}Key", hx, y - t, z0 + 2.75 - 0.25, K)
        cyl(f"D{i}HandleRose", 0.05, 0.03, (hx, y - t - 0.015, z0 + 2.75), K["brassf"], rot=(math.pi / 2, 0, 0), verts=14, bevel=0.006)
        tube(f"D{i}Handle", [(hx, y - t - 0.03, z0 + 2.75), (hx, y - t - 0.1, z0 + 2.75), (hx - 0.25, y - t - 0.11, z0 + 2.73)], 0.022, K["brassf"])
        for z in (z0 + 0.6, (z0 + z1) / 2, z1 - 0.6):
            cyl(f"D{i}Hinge{z:.1f}", 0.035, 0.26, (cx - dw / 2 - 0.02, y - 0.03, z), K["brassf"], verts=10, bevel=0.006)
    for sx in (-1, 1):
        xo = sx * (W / 2 + 0.005)
        box(f"SideField{sx}", (0.012, D - 0.6, H - zb - 1.6), (xo, 0.05, zb + (H - zb - 0.6) / 2), K["enamel"], bevel=0.0)
        tube(f"SideFrame{sx}", [(xo + sx * 0.008, -D / 2 + 0.35, zb + 0.5), (xo + sx * 0.008, D / 2 - 0.25, zb + 0.5),
                                (xo + sx * 0.008, D / 2 - 0.25, H - 1.1), (xo + sx * 0.008, -D / 2 + 0.35, H - 1.1)], 0.025, K["iron"], square=True,
             closed=True, poly=True)
    return _dims()


# ------------------------------------------------------------------ registration

BUILDERS = {
    "TeaUrn": tea_urn,
    "SpiritKettle": spirit_kettle,
    "TeaSet": tea_set,
    "MugRack": mug_rack,
    "BiscuitBarrel": biscuit_barrel,
    "KitchenetteCounter": kitchenette_counter,
    "IceBox": ice_box,
    "MarkingStack": marking_stack,
    "Gradebook": gradebook,
    "StaffRotaBoard": staff_rota_board,
    "WallTelephone": wall_telephone,
    "CardTable": card_table,
    "StaffOnlySign": staff_only_sign,
    "Dartboard": dartboard,
    "StaffLockers": staff_lockers,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.08 for n in BUILDERS})
P.PREVIEW_PAD.update({"TeaUrn": 1.25, "SpiritKettle": 1.35, "BiscuitBarrel": 1.4, "StaffOnlySign": 1.4, "WallTelephone": 1.15, "MugRack": 1.1})
B24.SMALL.update({"TeaSet": 1.25, "MarkingStack": 1.2, "Gradebook": 1.15})
