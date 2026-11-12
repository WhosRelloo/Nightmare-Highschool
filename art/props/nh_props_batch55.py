"""Props batch 55: the lunch tray return (the tray trolley and the return hatch), for Services.Features.Tray.

The owner asked for both (2026-11-12): a freestanding trolley the builder can put anywhere, and a hatch in a wall. Each is its
own sheet (one 2048 bake, one FBX with one piece). In NH Combat Test the piece is tagged NHTrayReturn, which gives it a
"Return tray" prompt, and carries Attachments Slot1, Slot2, ... where a returned tray is set (its bottom centre). The
trolley's slots fill in turn and the trays stay a while; the hatch's slots each have a SlotNInto beside them, so the tray
rolls along the conveyor, under the curtain and is gone.

  TrayTrolley       black wrought iron on brass castors: two columns of five slide-in runners for the lunch trays (1.5x,
                    1.97 x 1.45 x up to 0.64 studs), an oak top with a brass edge, gilt finials, a push bar at the back, a
                    pointed-arch grille on each side and a "RETURN TRAYS" plaque over the front
  TrayReturnHatch   a stone wall unit 6.4 x 2.4 x 8: a pointed arch over a slate sill with a brass roller conveyor (two
                    trays side by side), a leather-strip curtain inside, an oak-lined chamber, pilasters, a cornice with
                    finials, a "TRAY RETURN" plaque and a service bell on a bracket

Sizes are in studs (the FBX imports at 100x and is scaled to 0.01). Each stands on z = 0, centred on x = 0, its front facing
-Y; the trolley is centred in Y, the hatch's wall face is at y = 0 (the sill sticks out to y = -0.85).
SLOTS lists the slot positions (Blender space) for the Roblox setup script.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere
from nh_props_batch4 import lathe, flat, _mark, _xform, _dims
import nh_props_batch24 as B24
import nh_props_batch43 as B43

PI = math.pi
DEG = PI / 180
FONT = "C:/Windows/Fonts/georgiab.ttf"   # Georgia Bold (Blender's built-in font if it is missing)


def kit(M):
    return {
        "iron": M["iron"],
        "brass": M["brass"],
        "oak": M["oakdark"],
        "slate": M["slate"],
        # dark castle stone (as the fireplaces), not the pale limestone
        "stone": material("HatchStone", "NH_Limestone", tint=(0.2, 0.205, 0.195), scale=0.28, wear=0.2, dirt=1.0),
        "stonedark": material("HatchStoneDark", "NH_Limestone", tint=(0.13, 0.135, 0.125), scale=0.28, wear=0.16, dirt=1.0),
        "leather": material("CurtainLeather", "NH_Leather", tint=(0.11, 0.08, 0.06), scale=0.3, wear=0.3, dirt=0.8),
        "enamel": material("PlaqueEnamel", base=(0.02, 0.02, 0.026), rough=0.22, wear=0.1, dirt=0.4),
        "gilt": material("PlaqueGilt", base=(0.78, 0.56, 0.24), rough=0.28, metal=1.0, wear=0.12, dirt=0.4),
        "rubber": flat("CastorRubber", (0.03, 0.028, 0.03), 0.75),
    }


def prism(name, pts, y0, y1, mat):
    """A slab whose face is the polygon pts [(x, z), ...] (any shape, concave too), from y = y0 to y = y1."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], b[i], b[j], a[j]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0)


def plaque(prefix, text, w, h, x, y, z, K):
    """A black enamel cartouche w x h on a front face at y (facing -Y), centre (x, z): a brass rim, gilt corner rosettes and
    raised gilt lettering."""
    d = 0.05
    box(f"{prefix}Back", (w, d, h), (x, y - d / 2, z), K["enamel"], bevel=0.012)
    r = 0.03
    pts = [(x - w / 2, y - d - 0.005, z - h / 2), (x + w / 2, y - d - 0.005, z - h / 2), (x + w / 2, y - d - 0.005, z + h / 2),
           (x - w / 2, y - d - 0.005, z + h / 2)]
    tube(f"{prefix}Rim", pts, r, K["brass"], closed=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sphere(f"{prefix}Ro{sx}{sz}", 0.045, (x + sx * (w / 2 - 0.1), y - d - 0.01, z + sz * (h / 2 - 0.1)), K["gilt"],
                   seg=10, rings=6, scale=(1, 0.5, 1))
    B24._text(f"{prefix}Text", text, FONT, K["gilt"],
              lambda u, v, t: (x + u, y - d - t, z + v), fit=(w - 0.42, h - 0.2), depth=0.014, res=3, space=1.06)


# ------------------------------------------------------------------ the trolley

COLW = 1.70                 # a column's inside width (the trays' 1.45 depth, MackerelSet's 1.55, room to slide)
FR = 0.08                   # a frame line's thickness
DEP = 2.2                   # depth (the trays' 1.97 length goes in front to back)
RUN = 0.16                  # how far a runner sticks in (the gap between a column's runners is 1.38 < 1.45)
SLOT_Z = [0.78 + 0.78 * k for k in range(5)]    # a tray's bottom (a runner's top): 0.75 clear between, the tallest is 0.64
TOP = 4.92
FRAME_X = [-(COLW + FR), 0.0, COLW + FR]
COL_X = [-(COLW + FR) / 2, (COLW + FR) / 2]

SLOTS = {
    # (x, y, z) of each tray's bottom centre in Blender space, and the tray's long side along "Y" (in) or "X" (across)
    "TrayTrolley": {"slots": [(cx, 0.0, z) for z in SLOT_Z for cx in COL_X], "long": "Y"},
    "TrayReturnHatch": {"slots": [(-1.05, -0.1, 2.81), (1.05, -0.1, 2.81)], "into": [(-1.05, 1.6, 2.81), (1.05, 1.6, 2.81)],
                        "long": "X"},
}


def castor(prefix, x, y, K):
    """A swivel castor: a brass top plate on the deck, a swivel boss, a fork, a rubber-tyred wheel with a brass hub."""
    box(f"{prefix}Plate", (0.26, 0.26, 0.025), (x, y, 0.405), K["brass"], bevel=0.006)
    cyl(f"{prefix}Boss", 0.07, 0.06, (x, y, 0.36), K["iron"], verts=16)
    for sx in (-1, 1):
        box(f"{prefix}Fork{sx}", (0.022, 0.12, 0.2), (x + sx * 0.06, y + 0.03, 0.24), K["iron"], bevel=0.005)
    cyl(f"{prefix}Tyre", 0.16, 0.075, (x, y + 0.04, 0.16), K["rubber"], rot=(0, PI / 2, 0), verts=24, bevel=0.02)
    cyl(f"{prefix}Hub", 0.08, 0.09, (x, y + 0.04, 0.16), K["brass"], rot=(0, PI / 2, 0), verts=16, bevel=0.01)
    cyl(f"{prefix}Axle", 0.022, 0.15, (x, y + 0.04, 0.16), K["iron"], rot=(0, PI / 2, 0), verts=8, bevel=0.0)


def side_grille(prefix, xs, K):
    """An outer side: a pointed arch between the posts, round bars under it, a quatrefoil ring in the middle."""
    y0, y1 = -DEP / 2 + 0.04, DEP / 2 - 0.04
    arch = B43.arch_xz(y0, y1, 4.15, 0.62, n=12)
    tube(f"{prefix}Arch", [(xs, a, b) for a, b in arch], 0.03, K["iron"], poly=True)
    box(f"{prefix}Band", (0.05, DEP - 0.08, 0.05), (xs, 0, 0.62), K["iron"], bevel=0.008)
    qz, qr = 2.55, 0.34
    for k in range(4):
        a = k * PI / 2
        P_ = (xs, math.cos(a) * qr * 0.55, qz + math.sin(a) * qr * 0.55)
        pts = [(xs, P_[1] + math.cos(t) * qr * 0.5, P_[2] + math.sin(t) * qr * 0.5) for t in (i * 2 * PI / 16 for i in range(16))]
        tube(f"{prefix}Q{k}", pts, 0.018, K["iron"], closed=True, poly=True)
    for yb in (-0.72, -0.36, 0.36, 0.72):
        top = 4.15    # the arch's height over this bar (linear between its points)
        for (a0, b0), (a1, b1) in zip(arch, arch[1:]):
            if a0 <= yb <= a1:
                top = b0 + (b1 - b0) * (yb - a0) / (a1 - a0)
        cyl(f"{prefix}Bar{yb}", 0.02, top - 0.62, (xs, yb, (top + 0.62) / 2), K["iron"], verts=8, bevel=0.0)
    for z0, z1 in ((0.62, qz - qr * 1.05), (qz + qr * 1.05, 4.77)):
        cyl(f"{prefix}Mid{z0}", 0.02, z1 - z0, (xs, 0, (z0 + z1) / 2), K["iron"], verts=8, bevel=0.0)


def tray_trolley(K):
    W = 2 * (COLW + FR) + FR
    yf, yb = -DEP / 2 + 0.04, DEP / 2 - 0.04
    # deck and castors
    box("Deck", (W, DEP, 0.08), (0, 0, 0.46), K["iron"], bevel=0.015)
    box("Kick", (W + 0.02, 0.03, 0.06), (0, -DEP / 2 - 0.012, 0.46), K["brass"], bevel=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            castor(f"C{sx}{sy}", sx * (W / 2 - 0.16), sy * (DEP / 2 - 0.16), K)
    # the posts and the runner rails
    for i, fx in enumerate(FRAME_X):
        for y in (yf, yb):
            box(f"Post{i}{y > 0}", (FR, FR, TOP - 0.5), (fx, y, 0.5 + (TOP - 0.5) / 2), K["iron"], bevel=0.012)
        for k, z in enumerate(SLOT_Z):
            box(f"Rail{i}_{k}", (0.03, DEP - 0.08, 0.1), (fx, 0, z - 0.06), K["iron"], bevel=0.006, segments=1)
            for sgn in (-1, 1):
                if (i == 0 and sgn < 0) or (i == 2 and sgn > 0):
                    continue
                # the runner (its top is the slot) with a turned-down lip at the front to guide a tray in
                rx = fx + sgn * (FR / 2 + RUN / 2 - 0.02)
                box(f"Run{i}_{k}_{sgn}", (RUN, DEP - 0.14, 0.03), (rx, 0.03, z - 0.015), K["iron"], bevel=0.006, segments=1)
                box(f"Lip{i}_{k}_{sgn}", (RUN, 0.04, 0.05), (rx, -DEP / 2 + 0.07, z - 0.04), K["brass"], bevel=0.008, segments=1)
    # the back stops (two bars per column) so a tray can't slide out of the back
    for c, cx in enumerate(COL_X):
        for sx in (-1, 1):
            cyl(f"Stop{c}{sx}", 0.025, TOP - 0.6, (cx + sx * 0.45, yb + 0.01, 0.5 + (TOP - 0.6) / 2), K["iron"], verts=8, bevel=0.0)
        for z in (1.9, 3.45):
            box(f"StopBar{c}{z}", (COLW, 0.04, 0.04), (cx, yb + 0.01, z), K["iron"], bevel=0.006, segments=1)
    for sx in (-1, 1):
        side_grille(f"G{sx}", sx * (W / 2 + 0.03), K)
    # the top: oak with a brass edge, the gilt finials on the corners
    box("Top", (W + 0.14, DEP + 0.14, 0.1), (0, 0, TOP + 0.05), K["oak"], bevel=0.02)
    for sy in (-1, 1):
        box(f"EdgeY{sy}", (W + 0.16, 0.025, 0.06), (0, sy * (DEP / 2 + 0.08), TOP + 0.05), K["brass"], bevel=0.006)
    for sx in (-1, 1):
        box(f"EdgeX{sx}", (0.025, DEP + 0.16, 0.06), (sx * (W / 2 + 0.08), 0, TOP + 0.05), K["brass"], bevel=0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B43.finial(f"F{sx}{sy}", sx * (W / 2 - 0.0), sy * (DEP / 2 - 0.0), TOP + 0.1, K["brass"], s=0.9)
    # the front head rail and its plaque, over the top slot
    box("Head", (W, 0.06, 0.08), (0, -DEP / 2 - 0.0, TOP - 0.36), K["iron"], bevel=0.01)
    plaque("Pl", "RETURN TRAYS", 2.0, 0.32, 0, -DEP / 2 - 0.03, TOP - 0.15, K)
    # the push bar at the back, with brass grips
    hx = W / 2 - 0.04
    pts = [(-hx, DEP / 2, 4.1), (-hx, DEP / 2 + 0.22, 4.12), (-hx + 0.18, DEP / 2 + 0.3, 4.14), (hx - 0.18, DEP / 2 + 0.3, 4.14),
           (hx, DEP / 2 + 0.22, 4.12), (hx, DEP / 2, 4.1)]
    tube("Push", pts, 0.035, K["iron"], res=6)
    for sx in (-1, 1):
        cyl(f"Grip{sx}", 0.05, 0.7, (sx * (hx - 0.75), DEP / 2 + 0.3, 4.14), K["brass"], rot=(0, PI / 2, 0), verts=14, bevel=0.01)


# ------------------------------------------------------------------ the hatch

HW, HD, HH = 6.4, 2.4, 8.0          # the unit
OX = 2.2                            # the opening's half width
SILL, SPRING, APEX = 2.72, 4.5, 6.3


def bell(prefix, x, y, z, K):
    """A service bell hung from a curled iron bracket on a pier's face."""
    tube(f"{prefix}Br", [(x, y, z + 0.5), (x, y - 0.25, z + 0.55), (x, y - 0.45, z + 0.48), (x, y - 0.5, z + 0.36)], 0.025, K["iron"], res=6)
    box(f"{prefix}Pl", (0.16, 0.03, 0.28), (x, y - 0.015, z + 0.5), K["iron"], bevel=0.008)
    lathe(f"{prefix}Bell", [(0, 0.0), (0.15, 0.0), (0.16, 0.02), (0.12, 0.08), (0.095, 0.2), (0.085, 0.27), (0.05, 0.3), (0.02, 0.33),
                            (0, 0.33)], K["brass"], seg=20, loc=(x, y - 0.5, z))
    sphere(f"{prefix}Cl", 0.035, (x, y - 0.5, z - 0.02), K["iron"], seg=8, rings=5)


def tray_return_hatch(K):
    rnd = random.Random(5505)
    # the stone block: piers, the apron under the sill, the top, and the spandrels round the arch (in the front wall only)
    for sx in (-1, 1):
        box(f"Pier{sx}", (HW / 2 - OX, HD, HH - 0.3), (sx * (OX + (HW / 2 - OX) / 2), HD / 2, (HH - 0.3) / 2), K["stone"], bevel=0.02)
    box("Apron", (2 * OX, HD, SILL - 0.12), (0, HD / 2, (SILL - 0.12) / 2), K["stone"], bevel=0.0)
    box("Head", (2 * OX, HD, HH - 0.3 - APEX), (0, HD / 2, APEX + (HH - 0.3 - APEX) / 2), K["stone"], bevel=0.0)
    arch = B43.arch_xz(-OX, OX, SPRING, APEX - SPRING, n=14)
    half = len(arch) // 2
    prism("SpandrelL", [(-OX, SPRING)] + arch[1:half + 1] + [(-OX, APEX)], 0.0, 0.5, K["stone"])
    prism("SpandrelR", [(OX, SPRING)] + list(reversed(arch[half:-1])) + [(OX, APEX)], 0.0, 0.5, K["stone"])
    # the chamber behind: oak boards on its walls, ceiling and back
    for sx in (-1, 1):
        box(f"Line{sx}", (0.04, HD - 0.52, APEX - SILL), (sx * (OX - 0.02), 0.5 + (HD - 0.52) / 2, (SILL + APEX) / 2), K["oak"], bevel=0.0)
    box("LineBack", (2 * OX, 0.04, APEX - SILL), (0, HD - 0.04, (SILL + APEX) / 2), K["oak"], bevel=0.0)
    box("LineTop", (2 * OX, HD - 0.52, 0.04), (0, 0.5 + (HD - 0.52) / 2, APEX - 0.02), K["oak"], bevel=0.0)
    for k in range(7):
        box(f"Batten{k}", (2 * OX - 0.02, 0.03, 0.06), (0, HD - 0.075, SILL + 0.35 + k * 0.42), K["oak"], bevel=0.008)
    # the arch's moulding, its imposts and the keystone
    tube("Archivolt", [(x, -0.06, z) for x, z in arch], 0.09, K["stone"], poly=True)
    for sx in (-1, 1):
        box(f"Impost{sx}", (0.5, 0.2, 0.16), (sx * (OX + 0.15), -0.06, SPRING - 0.08), K["stonedark"], bevel=0.02)
    box("Key", (0.36, 0.24, 0.5), (0, -0.08, APEX + 0.08), K["stonedark"], bevel=0.03)
    # pilasters, the plinth and the cornice
    for sx in (-1, 1):
        px = sx * (OX + (HW / 2 - OX) / 2 + 0.05)
        box(f"Pil{sx}", (0.56, 0.12, 6.9), (px, -0.06, 0.35 + 3.45), K["stone"], bevel=0.02)
        box(f"PilBase{sx}", (0.7, 0.2, 0.3), (px, -0.1, 0.5), K["stonedark"], bevel=0.02)
        box(f"PilCap{sx}", (0.72, 0.22, 0.24), (px, -0.11, 7.24), K["stonedark"], bevel=0.02)
        for k in range(3):
            box(f"Flute{sx}{k}", (0.07, 0.03, 6.0), (px + (k - 1) * 0.15, -0.13, 3.95), K["stonedark"], bevel=0.01)
    box("Plinth", (HW + 0.16, HD + 0.08, 0.35), (0, HD / 2 - 0.04, 0.175), K["stonedark"], bevel=0.02)
    box("CorniceBand", (HW + 0.1, HD + 0.06, 0.12), (0, HD / 2 - 0.03, HH - 0.36), K["stonedark"], bevel=0.02)
    box("Cornice", (HW + 0.3, HD + 0.2, 0.3), (0, HD / 2 - 0.1, HH - 0.15), K["stonedark"], bevel=0.03)
    for x in (-HW / 2 + 0.3, 0.0, HW / 2 - 0.3):
        B43.finial(f"Fin{x}", x, -0.05, HH, K["brass"], s=1.3)
    # the apron's sunk panel
    pts = [(-1.7, -0.02, 0.6), (1.7, -0.02, 0.6), (1.7, -0.02, 2.2), (-1.7, -0.02, 2.2)]
    tube("Panel", pts, 0.05, K["stonedark"], closed=True, poly=True, square=True)
    # the sill: slate, a rounded nose, corbels under its front, the brass roller conveyor and its guide rails
    box("Sill", (2 * OX + 0.2, HD + 0.85, 0.12), (0, (HD - 0.85) / 2, SILL - 0.06), K["slate"], bevel=0.01)
    cyl("Nose", 0.06, 2 * OX + 0.2, (0, -0.85, SILL - 0.06), K["slate"], rot=(0, PI / 2, 0), verts=12, bevel=0.0)
    for sx in (-1, 1):
        for k, (dy, dz, h) in enumerate(((-0.4, -0.22, 0.32), (-0.2, -0.5, 0.32))):
            box(f"Corbel{sx}{k}", (0.3, 0.45 - k * 0.2, h), (sx * 1.6, dy, SILL - 0.12 + dz + 0.06), K["stone"], bevel=0.03)
    n = 0
    y = -0.72
    while y < HD - 0.15:
        cyl(f"Roller{n}", 0.045, 2 * OX - 0.14, (0, y, SILL + 0.045), K["brass"], rot=(0, PI / 2, 0), verts=12, bevel=0.0)
        n += 1
        y += 0.24
    for sx in (-1, 1):
        box(f"Guide{sx}", (0.05, HD + 0.8, 0.14), (sx * (OX - 0.05), (HD - 0.8) / 2, SILL + 0.07), K["iron"], bevel=0.01)
    # the curtain: leather strips on an iron rod, inside the wall
    RZ_ = SPRING + 0.2
    tube("Rod", [(-OX + 0.02, 0.8, RZ_), (OX - 0.02, 0.8, RZ_)], 0.03, K["iron"], poly=True)
    m = 11
    for k in range(m):
        x = -OX + 0.2 + k * (2 * OX - 0.4) / (m - 1)
        box(f"Strip{k}", (0.36, 0.015, RZ_ - 0.05 - SILL - 0.2), (x, 0.8 + rnd.uniform(-0.02, 0.02), (RZ_ - 0.05 + SILL + 0.2) / 2),
            K["leather"], bevel=0.0, rot=(rnd.uniform(-2, 2) * DEG, 0, rnd.uniform(-3, 3) * DEG))
    # the plaque between the arch and the cornice, and the service bell on the right pier
    # the arch's head: an iron sunburst over the curtain rod, inside the wall
    hub = (0.0, SPRING + 0.2)
    tube("Sill2", [(-OX, 0.3, hub[1]), (OX, 0.3, hub[1])], 0.035, K["iron"], poly=True)
    for i, (x, z) in enumerate(arch[1:-1]):
        if i % 2:
            continue
        tube(f"Ray{i}", [(hub[0], 0.3, hub[1]), (x * 0.97, 0.3, z - 0.04)], 0.022, K["iron"], poly=True)
    hp = [(math.cos(t) * 0.42, 0.3, hub[1] + math.sin(t) * 0.42) for t in (k * PI / 12 for k in range(13))]
    tube("Hub", hp, 0.03, K["iron"], poly=True)
    sphere("HubBoss", 0.1, (0, 0.27, hub[1] + 0.02), K["brass"], seg=12, rings=6, scale=(1, 0.6, 1))
    plaque("Pl", "TRAY RETURN", 3.0, 0.5, 0, 0.0, 7.08, K)
    bell("Bell", OX + 0.55, -0.12, 3.6, K)


# ------------------------------------------------------------------ the sheets

SHEETS = {"TrayTrolley": tray_trolley, "TrayReturnHatch": tray_return_hatch}


def sheet(name):
    def build(M):
        K = kit(M)
        set_group(name)
        st = _mark()
        SHEETS[name](K)
        return _dims()
    return build


for _n in SHEETS:
    P.BUILD[_n] = sheet(_n)
    P.PREVIEW_PAD[_n] = 0.5

BUILDERS = list(SHEETS)
