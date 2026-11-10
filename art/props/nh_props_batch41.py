"""Props batch 41 (2026-11-09): the art kit, part two, for nh_props.py: 32 new paintings, portraits, tapestries, banners,
busts, statues, reliefs and gallery pieces for the haunted gothic school, each with its own silhouette and one signature
idea. Every figure (statue, bust, relief, and the sitters in the paintings and the tapestry) is the owner's R6 rig from
PaintRigV3.blend, posed on its armature with the pose applied (art41_rig.py), then dressed and carved.

The paintings carry their own 2048 images (P.CANVAS, front-projected) from art41_canvases.py, painted over R6 renders
from art41_renders.py; the tapestries are woven maps (batch 29's TEXTILE). Sizes shared with the painter are in
art41_layout.py.

Front faces -Y, Z is up, the origin is at the bottom centre; wall pieces have their back flat on y = 0 (their pivot is on
the back face). Registered into nh_props.BUILD on import (BUILDERS).
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import nh_props as P
from nh_props import box, cyl, tube, set_group, material
from nh_props_batch3 import sphere, cone, flame
from nh_props_batch4 import lathe, hoop, strip, _mark, _xform, _dims, flat, _mesh
from nh_props_batch8 import _pointed, _spirelet, _crockets
from nh_props_batch9 import foil, candle, wax_mat, raven
from nh_props_batch10 import gilt, lacquer, velvet, black_marble, _skull
from nh_props_batch12 import frustum
import nh_props_batch20 as B20
import nh_props_batch21 as B21
import nh_props_batch24 as B24
import nh_props_batch27 as B27
import nh_props_batch29 as B29
import window_shapes as WS
import art41_layout as LY
import art41_rig as R

FONT = "C:/Windows/Fonts/palab.ttf"
S = 1.6           # statue scale (studs per R6 unit), as the statue kit


# ------------------------------------------------------------------ materials and helpers

def kit(M):
    K = B27.mats()
    K.update({
        "fgilt": B21.frame_gilt(),
        "iron": M["iron"], "brass": M["brass"], "oak": M["oak"], "oakdark": M["oakdark"],
        "ebony": flat("Ebony41", (0.02, 0.018, 0.02), 0.35, wear=0.15, dirt=0.6),
        "velvet": velvet(),
        "velvetblk": material("VelvetBlack41", "NH_Leather", tint=(0.03, 0.025, 0.03), scale=2.0, normal=0.3, rough_add=0.5, wear=0.05),
        "plaster": flat("Plaster41", (0.82, 0.79, 0.72), 0.85, wear=0.1, dirt=0.9),
        "silver": material("Silver41", base=(0.62, 0.62, 0.64), rough=0.3, metal=1.0, wear=0.25, dirt=0.9),
        "stone": M["stone"], "stonedark": M["stonedark"],
        "inkgloss": flat("InkGloss41", (0.01, 0.01, 0.02), 0.08),
        "bone": flat("Bone41", (0.78, 0.74, 0.64), 0.6, dirt=0.7),
        "obsidian": material("Obsidian41", base=(0.035, 0.032, 0.04), rough=0.2, metal=0.0, wear=0.25, dirt=0.5),
        "wax": wax_mat(),
    })
    return K


def cloth_mat(name, rgb):
    return material(name, "NH_Leather", tint=rgb, scale=4.0, normal=0.3, rough_add=0.45, wear=0.05, dirt=0.6)


def to_wall():
    """Move everything so its back is flat on y = 0 (the wall), keeping x and z."""
    bpy.context.view_layer.update()
    ymax = max((ob.matrix_world @ Vector(c)).y for ob in P.PARTS for c in ob.bound_box)
    for ob in P.PARTS:
        ob.matrix_world = Matrix.Translation((0, -ymax, 0)) @ ob.matrix_world


def tp(name, pts, y, depth, mat, bevel=0.0):
    B20.tprism(name, WS.ccw(pts), y, depth, mat, bevel=bevel)


def chain(prefix, a, b, mat, link=0.11, thick=0.018):
    a, b = Vector(a), Vector(b)
    d = b - a
    n = max(2, int(d.length / (link * 1.5)))
    up = d.normalized()
    for k in range(n):
        p = a + d * (k + 0.5) / n
        s = _mark()
        hoop(f"{prefix}{k}", (0, 0, 0), link * 0.5, "X" if k % 2 else "Y", mat, thick=thick)
        _xform(s, Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(up).to_matrix().to_4x4() @ Matrix.Scale(1.0, 4) @
               Matrix.Diagonal((1, 1, 1.5, 1)))


def text(name, s, mat, x, y, z, fit, depth=0.012):
    B24._text(name, s, FONT, mat, lambda u, v, d: (x + u, y - d, z + v), fit=fit, depth=depth, res=1)


def emblem(prefix, kind, cx, y, cz, s, mat, depth=0.04, width=0.035):
    e = LY.EMBLEM[kind]
    for i, f in enumerate(e["fills"]):
        tp(f"{prefix}F{i}", [(cx + u * s, cz + v * s) for u, v in f], y, depth, mat)
    for i, st in enumerate(e["strokes"]):
        tube(f"{prefix}S{i}", [(cx + u * s, y - depth / 2, cz + v * s) for u, v in st], width * s, mat, poly=True)


def thin_group(group, ratio):
    """Decimate every piece of a group (to keep it under 20k)."""
    for ob in P.PARTS:
        if ob.get("nh_group") == group and ob.type == "MESH":
            md = ob.modifiers.new("Decimate", "DECIMATE")
            md.ratio = ratio


def flatten(start, y0, k, decimate=None):
    """Press everything built since `start` toward the plane y0 (relief): y -> y0 + (y - y0) * k."""
    for ob in P.PARTS[start:]:
        if ob.type != "MESH":
            continue
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix.Identity(4)
        for v in ob.data.vertices:
            v.co.y = y0 + (v.co.y - y0) * k
        ob.data.update()
        for md in ob.modifiers:
            if md.type == "SOLIDIFY":      # even offset spikes on pressed (near-degenerate) cloth
                md.use_even_offset = False
                md.thickness = min(md.thickness, 0.02)
        if decimate:
            md = ob.modifiers.new("Decimate", "DECIMATE")
            md.ratio = decimate


def sheet(name, hw, ztop, zbot, y0, mat, nx=24, nz=30, fold=0.05, k=7.0, thick=0.035, xfn=None):
    """A hanging cloth from ztop down to zbot(x), soft vertical folds growing toward the hem; xfn(x, t) narrows it."""
    rows = []
    for j in range(nz + 1):
        t = j / nz
        row = []
        for i in range(nx + 1):
            u = -1 + 2 * i / nx
            x = u * hw if xfn is None else xfn(u, t)
            z = ztop - t * (ztop - zbot(x))
            y = y0 - fold * math.sin(u * k + 0.7) * (0.25 + 0.75 * t) - 0.02 * math.sin(u * 17) * t
            row.append(Vector((x, y, z)))
        rows.append(row)
    return _mesh(name, rows, mat, thick)


def tassel(prefix, x, y, z, mat, s=1.0):
    sphere(f"{prefix}Knot", 0.06 * s, (x, y, z - 0.05 * s), mat, seg=10, rings=6)
    cone(f"{prefix}Skirt", 0.07 * s, 0.025 * s, 0.3 * s, (x, y, z - 0.25 * s), mat, verts=12, rot=(math.pi, 0, 0))


def candle_sconce(prefix, x, z, K, side=1):
    """A wall sconce: a plate, a scrolled iron arm, a drip pan, a candle and its flame (Glow)."""
    box(f"{prefix}Plate", (0.26, 0.05, 0.5), (x, 0.0, z), K["iron"], bevel=0.015)
    tube(f"{prefix}Arm", [(x, -0.02, z - 0.1), (x, -0.25, z - 0.12), (x + side * 0.12, -0.42, z + 0.05), (x + side * 0.12, -0.45, z + 0.2)], 0.03, K["iron"])
    hoop(f"{prefix}Curl", (x, -0.2, z - 0.24), 0.07, "X", K["iron"], thick=0.015)
    lathe(f"{prefix}Pan", [(0, z + 0.2), (0.16, z + 0.2), (0.17, z + 0.24), (0.05, z + 0.25), (0, z + 0.25)], K["brass"], seg=16, loc=(x + side * 0.12, -0.45, 0))
    tip = candle(f"{prefix}Candle", x + side * 0.12, -0.45, z + 0.25, 0.45, K["wax"], r=0.05)
    set_group("Glow")
    flame(f"{prefix}Flame", (x + side * 0.12, -0.45, tip - 0.005), h=0.12)
    set_group("Main")


def canvas_piece(name, outline, y=0.0):
    B21._canvas(name, outline, y)


def oct_outline(cx, cz, w, h):
    a, b = w / 2, h / 2
    c = min(a, b) * 0.38
    return [(cx - a + c, cz - b), (cx + a - c, cz - b), (cx + a, cz - b + c), (cx + a, cz + b - c), (cx + a - c, cz + b), (cx - a + c, cz + b),
            (cx - a, cz + b - c), (cx - a, cz - b + c)]


def circ(cx, cz, r, n=56):
    return [(cx + math.cos(a) * r, cz + math.sin(a) * r) for a in [k / n * 2 * math.pi for k in range(n)]]


def lancet(hw, z0, h, n=12):
    return B21._arch(hw, z0, z0 + h * 0.68, z0 + h, n)


# ================================================================== paintings and portraits

def portrait_headmaster_gallery(M):
    """Gallery-height: a heavy carved gilt frame, a crocketed crest over it, a brass nameplate, and a crimson velvet swag
    and tails hung on a brass rail above it."""
    K = kit(M)
    gl = K["fgilt"]
    _, W, H = LY.CANVAS["PortraitHeadmasterGallery"]
    z0 = 0.8
    o = B21._rect(W / 2, H / 2, z0 + H / 2)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (gl, gl), widths=(0.3, 0.06, 0.07), back=0.2)
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"Corner{sx}{sz}", sx * (W / 2 + 0.3), -0.32, z0 + H / 2 + sz * (H / 2 + 0.3), 0.2, gl, thick=0.035)
        for k in range(4):
            sphere(f"Bead{sx}{k}", 0.07, (sx * (W / 2 + 0.3), -0.32, z0 + 1.5 + k * 1.7), gl, seg=10, rings=5)
    top = z0 + H + 0.5
    crest = [(-1.3, top - 0.1), (1.3, top - 0.1)] + [(x, z) for x, z in reversed(_pointed(1.3, top - 0.1, top + 1.0, 12))]
    tp("Crest", crest, -0.1, 0.12, gl, bevel=0.01)
    _crockets("Crocket", [(x, -0.14, z + 0.06) for x, z in _pointed(1.32, top - 0.08, top + 1.02, 9)[1:-1]], gl, size=0.08)
    sphere("CrestFinial", 0.12, (0, -0.12, top + 1.18), gl, seg=12, rings=6)
    B20._crest("Arms", 0, -0.18, top + 0.38, M, gl, s=1.1)
    # the nameplate
    box("Plate", (2.4, 0.06, 0.42), (0, -0.36, z0 - 0.02), K["brass"], bevel=0.012)
    text("PlateText", "HEADMASTER C. ASHGRAVE  1871-1903", K["ebony"], 0, -0.39, z0 - 0.02, (2.2, 0.2))
    # the rail, the swag and the tails
    zr = top + 1.6
    tube("Rail", [(-W / 2 - 0.8, -0.55, zr), (W / 2 + 0.8, -0.55, zr)], 0.05, K["brass"], poly=True)
    for sx in (-1, 1):
        sphere(f"RailEnd{sx}", 0.1, (sx * (W / 2 + 0.85), -0.55, zr), K["brass"], seg=12, rings=6)
        box(f"RailBracket{sx}", (0.08, 0.55, 0.08), (sx * (W / 2 + 0.6), -0.27, zr), K["brass"], bevel=0.02)
        box(f"RailPlate{sx}", (0.2, 0.04, 0.3), (sx * (W / 2 + 0.6), 0.0, zr), K["brass"], bevel=0.01)
    vel = K["velvet"]
    rows = []
    for j in range(7):
        t = j / 6
        row = []
        for i in range(33):
            u = -1 + 2 * i / 32
            x = u * (W / 2 + 0.7)
            sag = 0.9 * (1 - u * u) * (0.3 + 0.7 * t)
            row.append(Vector((x, -0.62 - 0.12 * t * (1 - u * u) - 0.04 * math.sin(u * 9), zr - 0.05 - sag - t * 0.35)))
        rows.append(row)
    _mesh("Swag", rows, vel, 0.04)
    for sx in (-1, 1):
        cxt = sx * (W / 2 + 0.45)
        sheet(f"Tail{sx}", 0.35, zr - 0.1, lambda x, sx=sx, cxt=cxt: zr - 2.8 - 0.5 * (sx * (x - cxt) / 0.35 + 1) / 2, -0.66, vel, nx=8, nz=12, fold=0.06, k=11,
              xfn=lambda u, t, sx=sx: sx * (W / 2 + 0.45) + u * 0.35 * (1 - 0.25 * t))
        tassel(f"TailTassel{sx}", sx * (W / 2 + 0.75), -0.68, zr - 3.55, K["gilt"], 1.4)
    to_wall()
    return _dims()


def portrait_headmistress(M):
    """Black wrought iron: a riveted frame with strapwork corners, hung on a V of chain from one iron hook."""
    K = kit(M)
    ir = K["iron"]
    _, W, H = LY.CANVAS["PortraitHeadmistress"]
    z0 = 0.4
    o = B21._rect(W / 2, H / 2, z0 + H / 2)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (ir, K["brass"]), widths=(0.2, 0.035, 0.04), back=0.14)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (W / 2 + 0.12), z0 + H / 2 + sz * (H / 2 + 0.12)
            tp(f"Strap{sx}{sz}", [(x - sx * 0.0, z), (x - sx * 0.75, z), (x - sx * 0.7, z - sz * 0.12), (x - sx * 0.12, z - sz * 0.12), (x - sx * 0.12, z - sz * 0.7),
                                  (x, z - sz * 0.75)], -0.3, 0.04, ir, bevel=0.01)
            for k in range(3):
                sphere(f"Rivet{sx}{sz}{k}", 0.035, (x - sx * (0.2 + k * 0.22), -0.33, z - sz * 0.06), K["brass"], seg=8, rings=4)
                sphere(f"RivetV{sx}{sz}{k}", 0.035, (x - sx * 0.06, -0.33, z - sz * (0.2 + k * 0.22)), K["brass"], seg=8, rings=4)
            tube(f"Scroll{sx}{sz}", [(x - sx * 0.75, -0.3, z - sz * 0.06), (x - sx * 0.95, -0.3, z - sz * 0.02), (x - sx * 1.0, -0.3, z - sz * 0.15),
                                     (x - sx * 0.9, -0.3, z - sz * 0.2)], 0.022, ir)
    zt = z0 + H + 0.25
    zh = zt + 1.4
    box("HookPlate", (0.22, 0.04, 0.4), (0, 0.0, zh), ir, bevel=0.012)
    tube("Hook", [(0, -0.02, zh - 0.05), (0, -0.25, zh - 0.08), (0, -0.3, zh + 0.08)], 0.03, ir)
    for sx in (-1, 1):
        hoop(f"Eye{sx}", (sx * (W / 2 - 0.2), -0.15, zt + 0.05), 0.07, "Y", ir, thick=0.02)
        chain(f"Chain{sx}", (sx * (W / 2 - 0.2), -0.18, zt + 0.12), (0, -0.25, zh - 0.08), ir, link=0.1)
    box("Label", (0.9, 0.05, 0.2), (0, -0.28, z0 - 0.12), K["brass"], bevel=0.01)
    text("LabelText", "I. MORROW", ir, 0, -0.31, z0 - 0.12, (0.75, 0.12))
    to_wall()
    return _dims()


def portrait_cursed_student(M):
    """An ebonised frame chained shut: two iron chains wrapped round its corners, a padlock hanging from them, square
    nails driven into the frame."""
    K = kit(M)
    eb, ir = K["ebony"], K["iron"]
    _, W, H = LY.CANVAS["PortraitCursedStudent"]
    z0 = 0.5
    zc = z0 + H / 2
    o = B21._rect(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (eb, K["silver"]), widths=(0.2, 0.035, 0.04), back=0.14)
    fx, fz = W / 2 + 0.2, H / 2 + 0.2
    # chains wrap the top-left and bottom-right corners, crossing the canvas corners diagonally
    chain("ChainA", (-fx - 0.05, -0.4, zc + fz - 1.0), (-fx + 1.0, -0.4, zc + fz + 0.05), ir, link=0.13, thick=0.024)
    chain("ChainB", (fx + 0.05, -0.4, zc - fz + 1.1), (fx - 1.1, -0.4, zc - fz - 0.05), ir, link=0.13, thick=0.024)
    chain("ChainC", (-0.4, -0.42, zc - fz - 0.02), (0.0, -0.45, zc - fz - 0.5), ir, link=0.12, thick=0.022)
    chain("ChainD", (0.4, -0.42, zc - fz - 0.02), (0.0, -0.45, zc - fz - 0.5), ir, link=0.12, thick=0.022)
    box("Padlock", (0.36, 0.14, 0.32), (0, -0.46, zc - fz - 0.75), K["brass"], bevel=0.04)
    hoop("Shackle", (0, -0.46, zc - fz - 0.56), 0.12, "Y", K["silver"], thick=0.03)
    box("Keyhole", (0.04, 0.02, 0.1), (0, -0.54, zc - fz - 0.78), eb, bevel=0.005)
    rnd = random.Random(4103)
    for k in range(9):
        side = k % 4
        t = rnd.uniform(-0.8, 0.8)
        x, z = ((t * fx, zc + fz) if side == 0 else (t * fx, zc - fz) if side == 1 else (-fx, zc + t * fz) if side == 2 else (fx, zc + t * fz))
        box(f"Nail{k}", (0.06, 0.08, 0.06), (x, -0.36, z), ir, bevel=0.01, rot=(0, rnd.uniform(-0.3, 0.3), 0))
    to_wall()
    return _dims()


def portrait_countess_oval(M):
    """An oval of black iron briars: a thorned stem round the frame, two crimson roses, an iron bat spread on top."""
    K = kit(M)
    ir = K["iron"]
    _, W, H = LY.CANVAS["PortraitCountessOval"]
    z0 = 0.5
    zc = z0 + H / 2
    o = B21._oval(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (ir, K["gilt"]), widths=(0.14, 0.035, 0.035), back=0.12)
    ring = B21._grow(o, 0.26)
    pts = []
    for k in range(len(ring) + 1):
        x, z = ring[k % len(ring)]
        a = k / len(ring) * 2 * math.pi
        pts.append((x + 0.05 * math.sin(a * 9), -0.26 + 0.04 * math.cos(a * 7), z + 0.05 * math.cos(a * 9)))
    tube("Briar", pts, 0.035, ir)
    for k in range(0, len(pts) - 1, 2):
        x, y, z = pts[k]
        dx, dz = x, z - zc
        L = math.hypot(dx, dz) or 1
        cone(f"Thorn{k}", 0.03, 0.0, 0.14, (x + dx / L * 0.07, y, z + dz / L * 0.07), ir, verts=4, rot=(0, math.atan2(dx, dz), 0))
    for k, a in enumerate((math.radians(215), math.radians(325))):
        x, z = math.cos(a) * (W / 2 + 0.28), zc + math.sin(a) * (H / 2 + 0.28)
        for p in range(5):
            b = p / 5 * 2 * math.pi
            sphere(f"Rose{k}P{p}", 0.09, (x + math.cos(b) * 0.06, -0.32, z + math.sin(b) * 0.06), K["crimson"], seg=8, rings=5, scale=(1, 0.6, 1))
        sphere(f"Rose{k}Heart", 0.07, (x, -0.36, z), K["crimson"], seg=8, rings=5)
    zt = zc + H / 2 + 0.3
    wing = [(0.12, 0.0), (0.4, 0.18), (0.7, 0.32), (0.95, 0.3), (0.9, 0.12), (0.78, 0.0), (0.66, 0.08), (0.55, -0.05), (0.42, 0.03), (0.3, -0.08), (0.18, -0.02)]
    for sx in (-1, 1):
        tp(f"BatWing{sx}", [(sx * x, zt + 0.2 + z) for x, z in wing], -0.24, 0.04, ir, bevel=0.005)
    sphere("BatBody", 0.14, (0, -0.26, zt + 0.17), ir, seg=10, rings=6, scale=(0.8, 0.6, 1.3))
    sphere("BatHead", 0.1, (0, -0.28, zt + 0.38), ir, seg=10, rings=6)
    for sx in (-1, 1):
        cone(f"BatEar{sx}", 0.04, 0.0, 0.12, (sx * 0.05, -0.28, zt + 0.5), ir, verts=4)
        sphere(f"BatEye{sx}", 0.018, (sx * 0.04, -0.37, zt + 0.4), K["crimson"], seg=6, rings=3)
    to_wall()
    return _dims()


def painting_vampire_ball(M):
    """A broad gilt frame with a bat-winged cartouche at its crown and an iron candle sconce on each side."""
    K = kit(M)
    gl = K["fgilt"]
    _, W, H = LY.CANVAS["PaintingVampireBall"]
    z0 = 0.6
    o = B21._rect(W / 2, H / 2, z0 + H / 2)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (gl, gl), widths=(0.26, 0.05, 0.06), back=0.18)
    lacq = lacquer()
    zt = z0 + H + 0.3
    sh = [(-0.42, zt + 0.95), (0.42, zt + 0.95), (0.42, zt + 0.45), (0.25, zt + 0.12), (0, zt - 0.02), (-0.25, zt + 0.12), (-0.42, zt + 0.45)]
    tp("Cartouche", sh, -0.2, 0.1, K["crimson"], bevel=0.01)
    tube("CartoucheRim", [(x, -0.26, z) for x, z in sh], 0.025, gl, closed=True, poly=True)
    sphere("CartoucheGem", 0.09, (0, -0.28, zt + 0.55), K["crimson"], seg=10, rings=5)
    wing = [(0.42, 0.75), (0.9, 1.0), (1.5, 1.1), (2.0, 0.95), (1.85, 0.55), (1.6, 0.66), (1.42, 0.38), (1.15, 0.55), (0.95, 0.28), (0.7, 0.45), (0.42, 0.35)]
    for sx in (-1, 1):
        tp(f"Wing{sx}", [(sx * x, zt + z - 0.25) for x, z in wing], -0.15, 0.06, gl, bevel=0.01)
        for k, (x, z) in enumerate(((0.9, 1.0), (1.5, 1.1), (2.0, 0.95))):
            tube(f"WingBone{sx}{k}", [(sx * 0.45, -0.2, zt + 0.5), (sx * x, -0.2, zt + z - 0.25)], 0.022, gl, poly=True)
    for sx in (-1, 1):
        candle_sconce(f"Sconce{sx}", sx * (W / 2 + 0.85), z0 + H * 0.45, K, side=-sx)
    to_wall()
    return _dims()


def painting_wolf_hunt_snow(M):
    """A rough dark-oak frame bound with iron corner straps, and a brass hunting horn hung on a hook under it."""
    K = kit(M)
    oak, ir = K["oakdark"], K["iron"]
    _, W, H = LY.CANVAS["PaintingWolfHuntSnow"]
    z0 = 1.2
    zc = z0 + H / 2
    o = B21._rect(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (oak, ir), widths=(0.28, 0.04, 0.05), back=0.16)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (W / 2 + 0.28), zc + sz * (H / 2 + 0.28)
            box(f"StrapH{sx}{sz}", (0.7, 0.04, 0.16), (x - sx * 0.3, -0.36, z - sz * 0.05), ir, bevel=0.01)
            box(f"StrapV{sx}{sz}", (0.16, 0.04, 0.7), (x - sx * 0.05, -0.36, z - sz * 0.3), ir, bevel=0.01)
            for k in range(2):
                sphere(f"Nail{sx}{sz}{k}", 0.035, (x - sx * (0.25 + k * 0.3), -0.39, z - sz * 0.05), ir, seg=8, rings=4)
    # the horn: a curved tapering brass tube with a flared bell, a leather baldric, on an iron hook
    zh = z0 - 0.55
    box("HookPlate", (0.16, 0.04, 0.3), (0, 0.0, zh + 0.25), ir, bevel=0.01)
    tube("Hook", [(0, -0.02, zh + 0.15), (0, -0.25, zh + 0.12), (0, -0.28, zh + 0.25)], 0.025, ir)
    n = 14
    for k in range(n):
        t = k / (n - 1)
        a = math.pi * (0.15 + 0.8 * t)
        x, z = -math.cos(a) * 0.9, zh - math.sin(a) * 0.38
        r = 0.04 + 0.08 * t ** 2.4
        sphere(f"Horn{k}", r * 1.3, (x, -0.3, z), K["brass"], seg=10, rings=6)
    lathe("HornBell", [(0, 0), (0.12, 0.0), (0.2, 0.14), (0.26, 0.2), (0, 0.2)], K["brass"], seg=20)
    ob = P.PARTS[-1]
    ob.matrix_world = Matrix.Translation((0.85, -0.3, zh - 0.12)) @ Matrix.Rotation(-math.pi / 2 - 0.5, 4, "Y")
    tube("Baldric", [(-0.8, -0.3, zh - 0.15), (-0.4, -0.27, zh + 0.12), (0, -0.28, zh + 0.18), (0.45, -0.27, zh + 0.1), (0.75, -0.3, zh - 0.1)], 0.03,
         K["leather"] if "leather" in K else M["leather"])
    to_wall()
    return _dims()


def tondo_moon_cloister(M):
    """A round gilt frame ringed with the moon's twelve phases in bone and ink enamel medallions."""
    K = kit(M)
    gl = K["fgilt"]
    _, W, H = LY.CANVAS["TondoMoonCloister"]
    R_ = W / 2
    zc = 0.7 + R_ + 0.5
    o = circ(0, zc, R_, 64)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (gl, gl), widths=(0.22, 0.05, 0.05), back=0.16)
    for k in range(12):
        a = math.pi / 2 - k / 12 * 2 * math.pi
        x, z = math.cos(a) * (R_ + 0.5), zc + math.sin(a) * (R_ + 0.5)
        cyl(f"Med{k}", 0.2, 0.06, (x, -0.24, z), K["ebony"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.01)
        hoop(f"MedRim{k}", (x, -0.28, z), 0.2, "Y", gl, thick=0.025)
        ph = k / 12
        # the lit part: a bone disc, its shadow cut by an offset ink disc (full at 6, new at 0)
        if k != 0:
            cyl(f"MedMoon{k}", 0.15, 0.02, (x, -0.28, z), K["bone"], rot=(math.pi / 2, 0, 0), verts=20, bevel=0.0)
            if k != 6:
                s = (6 - k) / 6
                cyl(f"MedShadow{k}", 0.155, 0.02, (x - s * 0.17, -0.295, z), K["ebony"], rot=(math.pi / 2, 0, 0), verts=20, bevel=0.0)
        tube(f"MedLink{k}", [(x, -0.22, z), (x * 0.92, -0.22, zc + (z - zc) * 0.92)], 0.03, gl, poly=True)
    to_wall()
    return _dims()


def painting_academy_panorama(M):
    """A long black-iron frame studded with brass rivets, carried on two scrolled brackets, a long brass picture light
    over it (Glow)."""
    K = kit(M)
    ir = K["iron"]
    _, W, H = LY.CANVAS["PaintingAcademyPanorama"]
    z0 = 0.9
    zc = z0 + H / 2
    o = B21._rect(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (ir, K["brass"]), widths=(0.2, 0.04, 0.04), back=0.14)
    n = int(W / 0.4)
    for k in range(n + 1):
        x = -W / 2 - 0.1 + (W + 0.2) * k / n
        for z in (zc + H / 2 + 0.12, zc - H / 2 - 0.12):
            sphere(f"Rivet{k}{z:.1f}", 0.04, (x, -0.3, z), K["brass"], seg=8, rings=4)
    for sx in (-1, 1):
        x = sx * (W / 2 - 1.0)
        box(f"BracketPlate{sx}", (0.24, 0.04, 0.8), (x, 0.0, z0 - 0.5), ir, bevel=0.012)
        tube(f"Bracket{sx}", [(x, -0.02, z0 - 0.8), (x, -0.2, z0 - 0.55), (x, -0.32, z0 - 0.2)], 0.035, ir)
        hoop(f"BracketCurl{sx}", (x, -0.14, z0 - 0.72), 0.08, "X", ir, thick=0.018)
    B21._picture_light("PL", 0, W * 0.75, zc + H / 2 + 0.22, M, K["brass"])
    to_wall()
    return _dims()


def painting_class_1887(M):
    """A plain oak frame with an engraved brass plate, and a black mourning rosette with two tails on its corner."""
    K = kit(M)
    oak = K["oak"]
    _, W, H = LY.CANVAS["PaintingClassOf1887"]
    z0 = 0.7
    zc = z0 + H / 2
    o = B21._rect(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (oak, K["gilt"]), widths=(0.24, 0.035, 0.045), back=0.14)
    box("Plate", (1.9, 0.05, 0.36), (0, -0.33, z0 - 0.04), K["brass"], bevel=0.012)
    text("PlateText", "THE CLASS OF 1887", K["ebony"], 0, -0.36, z0 - 0.04, (1.7, 0.18))
    x, z = W / 2 + 0.1, zc + H / 2 + 0.1
    bk = K["velvetblk"]
    for k in range(8):
        a = k / 8 * 2 * math.pi
        sphere(f"Rosette{k}", 0.13, (x + math.cos(a) * 0.15, -0.36, z + math.sin(a) * 0.15), bk, seg=8, rings=5, scale=(1.2, 0.5, 0.7))
    sphere("RosetteKnot", 0.09, (x, -0.42, z), bk, seg=10, rings=5)
    for k, dx in enumerate((-0.12, 0.1)):
        strip(f"Ribbon{k}", [(x + dx * 0.3, -0.38, z - 0.1), (x + dx, -0.38, z - 0.6), (x + dx * 1.6, -0.36, z - 1.1)], 0.13, (1, 0, 0), bk, thick=0.02)
    to_wall()
    return _dims()


def clique_heraldry(M):
    """The painted board of the eight cliques' arms in a carved oak arcade: a colonnette between every shield, trefoil-
    headed pointed arches over each one, a rail between the rows, the school crest on a gable over all."""
    K = kit(M)
    oak, gl = K["oakdark"], K["fgilt"]
    _, W, H = LY.CANVAS["CliqueHeraldry"]
    z0 = 0.6
    zc = z0 + H / 2
    o = B21._rect(W / 2, H / 2, zc)
    canvas_piece("Canvas", o)
    B21._frame("F", o, (oak, gl), widths=(0.26, 0.04, 0.05), back=0.16)
    cw, rh = W / 4, H / 2
    for i in range(1, 4):
        x = -W / 2 + i * cw
        tube(f"Colonnette{i}", [(x, -0.12, z0), (x, -0.12, z0 + H)], 0.05, gl, poly=True)
        for z in (z0 + 0.06, z0 + rh, z0 + H - 0.06):
            sphere(f"ColKnop{i}{z:.1f}", 0.08, (x, -0.13, z), gl, seg=10, rings=5)
    tube("Rail", [(-W / 2, -0.12, z0 + rh), (W / 2, -0.12, z0 + rh)], 0.045, gl, poly=True)
    for r in range(2):
        zt = z0 + (r + 1) * rh - 0.04
        for i in range(4):
            cx = -W / 2 + (i + 0.5) * cw
            arch = _pointed(cw / 2 - 0.06, zt - 0.32, zt, 10)
            tube(f"Arch{r}{i}", [(cx + x, -0.12, z) for x, z in arch], 0.03, gl, poly=True)
            for sx in (-1, 1):
                sphere(f"Cusp{r}{i}{sx}", 0.04, (cx + sx * (cw / 4), -0.12, zt - 0.2), gl, seg=8, rings=4)
    zt = z0 + H + 0.26
    gable = [(-1.0, zt), (1.0, zt), (0, zt + 0.9)]
    tp("Gable", gable, -0.12, 0.12, oak, bevel=0.01)
    _crockets("Crocket", [(x, -0.16, z) for x, z in ((-0.7, zt + 0.32), (-0.4, zt + 0.6), (0.4, zt + 0.6), (0.7, zt + 0.32))], gl, size=0.07)
    sphere("Finial", 0.1, (0, -0.12, zt + 1.0), gl, seg=12, rings=6)
    B20._crest("Arms", 0, -0.2, zt + 0.36, M, gl, s=0.75)
    to_wall()
    return _dims()


def portrait_miniatures(M):
    """A salon hang of five miniatures on a crimson velvet board with a gilt edge, hung by a ribbon bow from a nail: an
    oval in gilt, two roundels (iron and gilt), a rectangle in ebony, an octagon in silver."""
    K = kit(M)
    BW, BH = LY.MINI_BOARD
    z0 = 0.3
    box("Board", (BW, 0.12, BH), (0, 0.06, z0 + BH / 2), K["velvet"], bevel=0.02)
    tube("BoardEdge", [(x, -0.01, z) for x, z in B21._rect(BW / 2, BH / 2, z0 + BH / 2)], 0.05, K["fgilt"], closed=True, square=True, poly=True)
    mats = {"oval": (K["fgilt"], K["fgilt"]), "circle": None, "rect": (K["ebony"], K["gilt"]), "octagon": (K["silver"], K["silver"])}
    set_group("Canvas")
    outlines = []
    for scene, shape, cx, cz, w, h in LY.MINIS:
        if shape == "oval":
            ol = B21._oval(w / 2, h / 2, z0 + cz)
            ol = [(x + cx, z) for x, z in ol]
        elif shape == "circle":
            ol = circ(cx, z0 + cz, w / 2, 40)
        elif shape == "rect":
            ol = [(cx + x, z) for x, z in B21._rect(w / 2, h / 2, z0 + cz)]
        else:
            ol = oct_outline(cx, z0 + cz, w, h)
        outlines.append((scene, shape, ol))
        B20.tprism(f"Mini{scene}", ol, -0.06 + 0.02, 0.04, flat("CanvasTmp", (0.5, 0.5, 0.5), 0.5))
    set_group("Main")
    for scene, shape, ol in outlines:
        fm = mats[shape] if shape != "circle" else ((K["iron"], K["brass"]) if "Vampire" in scene else (K["fgilt"], K["fgilt"]))
        B21._frame(f"F{scene}", ol, fm, y=-0.06, widths=(0.09, 0.025, 0.025), back=0.04)
    zt = z0 + BH
    box("Nail", (0.06, 0.3, 0.06), (0, -0.05, zt + 0.9), K["iron"], bevel=0.01)
    rib = K["crimson"]
    for sx in (-1, 1):
        strip(f"Ribbon{sx}", [(sx * 0.9, -0.04, zt - 0.05), (sx * 0.45, -0.07, zt + 0.45), (sx * 0.05, -0.1, zt + 0.85)], 0.14, (0, 1, 0), K["velvet"], thick=0.02)
        sphere(f"BowLoop{sx}", 0.17, (sx * 0.22, -0.12, zt + 0.92), K["velvet"], seg=12, rings=6, scale=(1.4, 0.4, 0.8))
        strip(f"BowTail{sx}", [(sx * 0.05, -0.12, zt + 0.85), (sx * 0.18, -0.13, zt + 0.5), (sx * 0.15, -0.12, zt + 0.25)], 0.11, (1, 0, 0), K["velvet"], thick=0.02)
    sphere("BowKnot", 0.08, (0, -0.15, zt + 0.9), K["velvet"], seg=10, rings=6)
    to_wall()
    return _dims()


# ================================================================== tapestries and banners

def tapestry_cliques(M):
    """A tapestry with a dagged (vandyked) hem of gilt-tasselled points, hung from a black iron spear rod held by two
    iron ravens perched on wall brackets."""
    K = kit(M)
    maps, w, hgt = LY.TAPESTRY["TapestryCliques"]
    z0, dag = 0.9, 0.42
    z1 = z0 + hgt
    yc = -0.5
    set_group("Weave")
    cloth = flat("ClothTmp", (0.4, 0.1, 0.1), 0.9)
    nd = 8

    def zb(x):
        u = ((x / w + 0.5) * nd) % 1.0
        return z0 + dag * abs(u - 0.5) * 2
    sheet("Cloth", w / 2, z1, zb, yc, cloth, nx=nd * 6, nz=40, fold=0.05, k=11, thick=0.04)
    for k in range(nd):
        x = -w / 2 + (k + 0.5) * w / nd
        tassel(f"DagTassel{k}", x, yc - 0.02, z0 + 0.02, cloth, 1.2)
    set_group("Main")
    zr = z1 + 0.3
    tube("Rod", [(-w / 2 - 0.7, yc, zr), (w / 2 + 0.7, yc, zr)], 0.07, K["iron"], poly=True)
    for sx in (-1, 1):
        cone(f"Spear{sx}", 0.13, 0.0, 0.55, (sx * (w / 2 + 0.95), yc, zr), K["iron"], verts=4, rot=(0, sx * math.pi / 2, 0))
        sphere(f"SpearKnop{sx}", 0.1, (sx * (w / 2 + 0.7), yc, zr), K["iron"], seg=10, rings=5)
        bx = sx * (w / 2 + 0.25)
        box(f"BracketPlate{sx}", (0.26, 0.05, 0.6), (bx, 0.0, zr + 0.1), K["iron"], bevel=0.015)
        tube(f"Bracket{sx}", [(bx, -0.02, zr + 0.2), (bx, yc * 0.5, zr + 0.25), (bx, yc, zr + 0.12)], 0.04, K["iron"], poly=True)
        raven(f"Raven{sx}", (bx, yc, zr + 0.05), -math.pi / 2 + sx * 0.6, 3.6, K["iron"], K["ebony"])
    nr = 10
    for k in range(nr + 1):
        x = -w / 2 + 0.1 + (w - 0.2) * k / nr
        hoop(f"Ring{k}", (x, yc, zr - 0.03), 0.12, "X", K["iron"], thick=0.022)
    B29._register(f"TapestryCliques_Weave", maps, "front", (-w / 2, w / 2, z0, z1))
    to_wall()
    return _dims()


def tapestry_procession(M):
    """A frieze tapestry hung below a carved oak pelmet with a gilt battlement cresting and a crimson valance."""
    K = kit(M)
    maps, w, hgt = LY.TAPESTRY["TapestryProcession"]
    z0 = 1.0
    z1 = z0 + hgt
    yc = -0.45
    set_group("Weave")
    cloth = flat("ClothTmp", (0.4, 0.1, 0.1), 0.9)
    sheet("Cloth", w / 2, z1, lambda x: z0, yc, cloth, nx=72, nz=34, fold=0.045, k=14, thick=0.04)
    n = int(w / 0.3)
    for k in range(n + 1):
        x = -w / 2 + 0.06 + (w - 0.12) * k / n
        tube(f"FringeCord{k}", [(x, yc - 0.03, z0 + 0.02), (x, yc - 0.03, z0 - 0.16)], 0.02, cloth, poly=True)
        lathe(f"FringeTassel{k}", [(0, z0 - 0.16), (0.04, z0 - 0.16), (0.07, z0 - 0.4), (0.075, z0 - 0.55), (0, z0 - 0.55)], cloth, seg=8, loc=(x, yc - 0.03, 0))
    set_group("Main")
    oak, gl = K["oakdark"], K["fgilt"]
    zp = z1 + 0.1
    box("Pelmet", (w + 0.8, 0.8, 0.9), (0, -0.4, zp + 0.45), oak, bevel=0.04)
    box("PelmetBand", (w + 0.9, 0.86, 0.12), (0, -0.4, zp + 0.06), gl, bevel=0.02)
    nb = int((w + 0.8) / 0.5)
    for k in range(nb):
        x = -(w + 0.8) / 2 + 0.25 + k * 0.5
        if k % 2 == 0:
            box(f"Merlon{k}", (0.3, 0.84, 0.26), (x, -0.4, zp + 1.03), gl, bevel=0.02)
        foil(f"PelmetFoil{k}", x, -0.81, zp + 0.48, 0.14, gl, lobes=4, thick=0.016)
    B20._crest("Arms", 0, -0.86, zp + 0.48, M, gl, s=1.1)
    for k in range(int(w / 0.5) + 1):
        x = -w / 2 + k * 0.5
        sphere(f"Valance{k}", 0.17, (x, -0.82, zp - 0.04), K["velvet"], seg=10, rings=5, scale=(1.4, 0.4, 0.8))
    B29._register(f"TapestryProcession_Weave", maps, "front", (-w / 2, w / 2, z0, z1))
    to_wall()
    return _dims()


def _banner_base(prefix, K, hw, ztop, zb, y0, colour, trim, emblem_kind, ec, zc, es, xfn=None, nz=34, swing=True):
    cloth = cloth_mat(f"{prefix}Cloth", colour)
    set_group("Cloth", hinge=(0, y0, ztop + 0.06), swing=1)
    sheet("Cloth", hw, ztop, zb, y0, cloth, nx=28, nz=nz, fold=0.045, k=9, xfn=xfn)
    emblem("Emblem", emblem_kind, 0, y0 - 0.07, zc, es, ec, depth=0.05)
    return cloth


def banner_pack(M):
    """The Pack's war banner: olive cloth with a bone paw, torn into ragged points at the hem and slashed by three claw
    rips, lashed with rope to a rough crossbar that hangs from an iron hook."""
    K = kit(M)
    hw, zt = 1.3, 6.4
    rnd = random.Random(4115)
    jag = [rnd.uniform(0.0, 0.55) for _ in range(30)]

    def zb(x):
        u = (x / hw + 1) / 2 * 29
        i = int(min(28, max(0, u)))
        f = u - i
        return 1.2 + jag[i] * (1 - f) + jag[i + 1] * f
    cloth = _banner_base("Pack", K, hw, zt, zb, -0.32, (0.24, 0.29, 0.15), K["bone"], "paw", K["bone"], zt - 2.0, 1.8)
    for k in range(3):
        x = -0.55 + k * 0.3
        tp(f"Rip{k}", [(x, zt - 3.1), (x + 0.05, zt - 3.12), (x + 0.42, zt - 4.4), (x + 0.36, zt - 4.42)], -0.37, 0.01, K["ebony"])
    for k in range(5):
        x = -hw + 0.1 + k * (2 * hw - 0.2) / 4
        tube(f"Lash{k}", [(x, -0.2, zt + 0.1), (x, -0.4, zt + 0.12), (x, -0.42, zt - 0.08), (x, -0.25, zt - 0.1)], 0.025, flat("Rope41", (0.5, 0.42, 0.28), 0.95))
    set_group("Main")
    tube("Crossbar", [(-hw - 0.35, -0.32, zt + 0.05), (hw + 0.35, -0.32, zt + 0.05)], 0.08, K["oakdark"], poly=True)
    for sx in (-1, 1):
        cone(f"BarSpike{sx}", 0.08, 0.0, 0.3, (sx * (hw + 0.5), -0.32, zt + 0.05), K["iron"], verts=6, rot=(0, sx * math.pi / 2, 0))
        tube(f"Rope{sx}", [(sx * (hw - 0.1), -0.32, zt + 0.1), (0, -0.3, zt + 1.3)], 0.025, flat("Rope41", (0.5, 0.42, 0.28), 0.95), poly=True)
    box("HookPlate", (0.22, 0.05, 0.4), (0, 0.0, zt + 1.4), K["iron"], bevel=0.012)
    tube("Hook", [(0, -0.02, zt + 1.3), (0, -0.32, zt + 1.25), (0, -0.34, zt + 1.4)], 0.035, K["iron"])
    to_wall()
    return _dims()


def banner_choir(M):
    """The Chapel Choir's gonfalon: bone cloth with a crimson border and three rounded lobes at its foot, the gilt halo and
    cross, hung from a gilt crossarm with a cross finial on a wall bracket."""
    K = kit(M)
    hw, zt = 1.15, 7.0
    lob = 3

    def zb(x):
        u = ((x / hw + 1) / 2 * lob) % 1.0
        return 1.0 + 0.45 * (1 - math.sin(u * math.pi))
    _banner_base("Choir", K, hw, zt, zb, -0.45, (0.72, 0.68, 0.58), K["gilt"], "halo", K["gilt"], zt - 2.4, 1.9)
    for sx in (-1, 1):
        tube(f"Border{sx}", [(sx * (hw - 0.12), -0.5, zt - 0.1), (sx * (hw - 0.12), -0.5, 1.5)], 0.04, K["crimson"], poly=True)
    tube("BorderTop", [(-hw + 0.12, -0.5, zt - 0.15), (hw - 0.12, -0.5, zt - 0.15)], 0.04, K["crimson"], poly=True)
    for k in range(lob):
        x = -hw + (k + 0.5) * 2 * hw / lob
        tassel(f"Lobe{k}", x, -0.45, 1.0, K["gilt"], 1.3)
    set_group("Main")
    tube("Crossarm", [(-hw - 0.3, -0.45, zt + 0.1), (hw + 0.3, -0.45, zt + 0.1)], 0.06, K["gilt"], poly=True)
    for sx in (-1, 1):
        sphere(f"ArmKnop{sx}", 0.11, (sx * (hw + 0.36), -0.45, zt + 0.1), K["gilt"], seg=12, rings=6)
    tube("Upright", [(0, -0.45, zt + 0.1), (0, -0.45, zt + 1.3)], 0.05, K["gilt"], poly=True)
    box("CrossV", (0.08, 0.08, 0.6), (0, -0.45, zt + 1.55), K["gilt"], bevel=0.02)
    box("CrossH", (0.38, 0.08, 0.08), (0, -0.45, zt + 1.62), K["gilt"], bevel=0.02)
    box("WallPlate", (0.3, 0.05, 0.6), (0, 0.0, zt + 0.7), K["iron"], bevel=0.015)
    tube("Bracket", [(0, -0.02, zt + 0.5), (0, -0.3, zt + 0.6), (0, -0.45, zt + 0.8)], 0.04, K["iron"])
    to_wall()
    return _dims()


def banner_ink(M):
    """The Ink Club's banner as a hanging scroll: violet cloth splashed with ink, the quill, top and bottom rollers with
    brass end caps, hung by a cord from a nail."""
    K = kit(M)
    hw, zt = 1.0, 6.6
    zbot = 1.0
    _banner_base("Ink", K, hw, zt, lambda x: zbot, -0.22, (0.3, 0.12, 0.38), K["gilt"], "quill", K["bone"], zt - 2.3, 1.7, swing=True)
    rnd = random.Random(4117)
    for k in range(9):
        x, z = rnd.uniform(-0.8, 0.8), rnd.uniform(zbot + 0.6, zt - 0.5)
        r = rnd.uniform(0.05, 0.16)
        cyl(f"Splat{k}", r, 0.01, (x, -0.3, z), K["inkgloss"], rot=(math.pi / 2, 0, 0), verts=10, bevel=0.0)
        for j in range(3):
            a = rnd.uniform(0, 2 * math.pi)
            cyl(f"Spot{k}{j}", r * 0.3, 0.01, (x + math.cos(a) * r * 1.8, -0.3, z + math.sin(a) * r * 1.8), K["inkgloss"], rot=(math.pi / 2, 0, 0), verts=6,
                bevel=0.0)
    tube("Drip", [(0.3, -0.3, zt - 1.2), (0.31, -0.3, zt - 1.9)], 0.02, K["inkgloss"], poly=True)
    for zr, r in ((zt, 0.08), (zbot - 0.02, 0.1)):
        tube(f"Roller{zr:.0f}", [(-hw - 0.15, -0.22, zr), (hw + 0.15, -0.22, zr)], r, K["ebony"], poly=True)
        for sx in (-1, 1):
            cyl(f"Cap{zr:.0f}{sx}", r * 1.4, 0.12, (sx * (hw + 0.2), -0.22, zr), K["brass"], rot=(0, math.pi / 2, 0), verts=16, bevel=0.01)
    tube("Cord", [(-hw + 0.1, -0.22, zt + 0.05), (0, -0.2, zt + 0.95), (hw - 0.1, -0.22, zt + 0.05)], 0.02, K["gilt"])
    set_group("Main")
    box("Nail", (0.07, 0.3, 0.07), (0, -0.1, zt + 0.95), K["iron"], bevel=0.01)
    to_wall()
    return _dims()


def gonfalon_stand(M):
    """The school's processional gonfalon on its floor stand: an iron tripod with scroll feet, a tall pole, a gilt cross-
    bar with a crescent finial, a swallow-tailed crimson banner with the crest in gilt relief, gilt fringe."""
    K = kit(M)
    ir, gl = K["iron"], K["gilt"]
    for k in range(3):
        a = k / 3 * 2 * math.pi + math.pi / 2
        tube(f"Leg{k}", [(0, 0, 1.4), (math.cos(a) * 0.6, math.sin(a) * 0.6, 0.6), (math.cos(a) * 1.1, math.sin(a) * 1.1, 0.12)], 0.05, ir)
        hoop(f"Foot{k}", (math.cos(a) * 1.18, math.sin(a) * 1.18, 0.12), 0.1, "Z", ir, thick=0.03)
    lathe("Collar", [(0, 1.2), (0.14, 1.2), (0.16, 1.45), (0.12, 1.6), (0, 1.6)], K["brass"], seg=20)
    tube("Pole", [(0, 0, 1.4), (0, 0, 9.6)], 0.06, K["oakdark"], poly=True)
    zb = 8.8
    tube("Crossbar", [(-1.45, 0, zb), (1.45, 0, zb)], 0.05, gl, poly=True)
    for sx in (-1, 1):
        sphere(f"BarKnop{sx}", 0.1, (sx * 1.5, 0, zb), gl, seg=12, rings=6)
    sphere("PoleKnop", 0.13, (0, 0, 9.65), gl, seg=12, rings=6)
    tp("Crescent", WS.crescent(0, 10.1, 0.35, shift=0.38, tilt=math.pi / 2), 0.0, 0.06, gl)
    hw = 1.3

    def zb_(x):
        return 3.6 + 0.9 * (1 - abs(x) / hw)
    cloth = cloth_mat("GonfalonCloth", (0.3, 0.03, 0.05))
    set_group("Cloth", hinge=(0, -0.1, zb), swing=1)
    sheet("Cloth", hw, zb - 0.05, zb_, -0.1, cloth, nx=28, nz=34, fold=0.05, k=9)
    s = _mark()
    B20._crest("Arms", 0, 0, 0, M, gl, s=3.2)
    _xform(s, Matrix.Translation((0, -0.2, 6.9)))
    x = -hw + 0.06
    while x < hw - 0.05:
        z = zb_(x)
        tube(f"Fringe{x:.2f}", [(x, -0.12, z + 0.02), (x, -0.12, z - 0.16)], 0.012, gl, poly=True)
        x += 0.09
    for sx in (-1, 1):
        tassel(f"Tail{sx}", sx * (hw - 0.03), -0.1, 3.6, gl, 1.4)
    set_group("Main")
    return _dims()


# ================================================================== sculpted drapery, hair and props (for the R6 figures)

import bmesh as _bm


def ring_mesh(name, rows, mat, thick=0.04, closed=True, smooth_=True):
    """A sheet from rings of points; closed rings wrap round (no seam). Given a little thickness (Solidify)."""
    me = bpy.data.meshes.new(name)
    bm = _bm.new()
    vs = [[bm.verts.new(tuple(p)) for p in row] for row in rows]
    n = len(rows[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n if closed else n - 1):
            k2 = (k + 1) % n
            f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
            f.smooth = smooth_
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    P._finish(ob, mat, 0)
    if thick:
        md = ob.modifiers.new("Solid", "SOLIDIFY")
        md.thickness = thick
        md.offset = 0
        md.use_even_offset = False
    return ob


def drape_rings(levels, n=48, a0=0.0, a1=2 * math.pi, closed=True, seed=0, hem=0.0, hem_k=7):
    """levels: (z, cx, cy, rx, ry, amp, folds, train) from the top down. Folds are radial ripples that grow with amp; train
    pushes the back (+Y) out; the last ring's hem waves by `hem`."""
    rnd = random.Random(seed)
    jit = [rnd.uniform(-1, 1) for _ in range(n)]
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    rows = []
    for j, (z, cx, cy, rx, ry, amp, folds, train) in enumerate(levels):
        row = []
        for i in range(n):
            a = a0 + (a1 - a0) * (i / n if closed else i / (n - 1))
            s = 0.65 * math.sin(folds * a + ph[0]) + 0.25 * math.sin(folds * 2.3 * a + ph[1]) + 0.15 * jit[i]
            back = max(0.0, math.sin(a))
            r_x = rx + amp * s
            r_y = (ry + amp * s) * (1 + train * back)
            zz = z
            if j == len(levels) - 1 and hem:
                zz += hem * math.sin(hem_k * a + ph[2]) - train * 0.25 * back
            row.append(Vector((cx + math.cos(a) * r_x, cy + math.sin(a) * r_y, zz)))
        rows.append(row)
    return rows


def gown(f, m, z0=2.15, z1=0.04, top=(1.07, 0.6), bot=(1.75, 1.3), folds=9, amp=0.13, train=0.0, hem=0.05, hem_k=7, n=56, nz=10, seed=1,
         name="Gown", thick=0.05, part="torso"):
    """A skirt from the waist (z0) to the hem (z1), widening, its folds deepening toward the hem, a train behind."""
    lv = []
    for j in range(nz + 1):
        t = j / nz
        e = t ** 1.25
        lv.append((z0 + (z1 - z0) * t, 0, 0.3 * train * t * t, top[0] + (bot[0] - top[0]) * e, top[1] + (bot[1] - top[1]) * e, amp * t ** 0.9, folds,
                   train * t * t))
    f.build(part, lambda: ring_mesh(name, drape_rings(lv, n, seed=seed, hem=hem, hem_k=hem_k), m, thick))


def sleeve2(f, side, m, z0=3.98, z1=2.2, r0=0.62, r1=0.74, folds=5, amp=0.05, n=24, nz=8, cuff=None, name="Sleeve"):
    """A cloth sleeve round the R6 arm (rest frame), flaring a little, folds deepening toward the cuff; it bends with the
    elbow because the build skins it to the arm's two bones."""
    j = "rshoulder" if side > 0 else "lshoulder"
    cx = side * 1.5
    lv = []
    for k in range(nz + 1):
        t = k / nz
        r = r0 + (r1 - r0) * t ** 1.5
        lv.append((z0 + (z1 - z0) * t, cx, 0.0, r, r, amp * (0.3 + 0.7 * t), folds, 0.0))

    def b():
        ring_mesh(f"{name}{side}", drape_rings(lv, n, seed=7 + side), m, 0.04)
        if cuff is not None:
            hoop(f"{name}Cuff{side}", (cx, 0, z1 + 0.04), r1 + 0.03, "Z", cuff, thick=0.05)
    f.build(j, b)


def ruff(name, cz, r_in, r_out, m, flutes=20, depth=0.09, n=80, cx=0.0, cy=0.0):
    """A fluted ruff (or cuff frill): a flat ring waved up and down in flutes."""
    rows = []
    for k in range(4):
        t = k / 3
        r = r_in + (r_out - r_in) * t
        rows.append([Vector((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.92, cz + depth * math.sin(flutes * a) * (0.3 + 0.7 * t)))
                     for a in [i / n * 2 * math.pi for i in range(n)]])
    return ring_mesh(name, rows, m, 0.03)


CAP = [(0.0, 5.26), (0.3, 5.26), (0.52, 5.23), (0.65, 5.15), (0.71, 5.04), (0.73, 4.92), (0.73, 4.86), (0.66, 4.84), (0.0, 4.84)]


def _cap_r(z):
    """The hair cap's radius at height z (it wraps the rig's round-topped head with a clear gap)."""
    pts = CAP[1:7]
    if z >= pts[0][1]:
        return pts[0][0]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            return r0 + (r1 - r0) * (z0 - z) / (z0 - z1)
    return 0.73


def _on(a, z, lift=0.06):
    """A point just off the cap's surface at angle a (from +X, -90 deg is the face), height z."""
    r = _cap_r(min(z, 5.26)) + lift
    return (math.cos(a) * r, math.sin(a) * r, z if z < 5.26 else 5.26 + lift)


def hair_sculpt(f, m, style="slick", seed=3):
    """Hair in layers over the rig's head: a cap that wraps the round-topped head with a clear gap (its hairline above
    the brows), a back piece down to the nape, then carved locks lying on the cap's surface, by style: slick (combed
    straight back, a widow's peak), bun (drawn up to a coiled bun on the crown), coif (a curled updo, ringlets at the
    temples), short (tousled tufts from the crown), curls (round the nape, under a hat)."""
    rnd = random.Random(seed)
    D = math.radians

    def lock(name, pts, r):
        tube(name, pts, r, m)
        sphere(name + "E", r * 0.95, pts[-1], m, seg=8, rings=4)

    def h():
        lathe("HairCap", CAP, m, seg=40)
        rows = []
        for k in range(5):
            z = 4.86 - k * 0.14
            r = 0.73 - 0.01 * k
            rows.append([Vector((math.cos(a) * r, math.sin(a) * r, z)) for a in [D(10 + 160 * i / 24) for i in range(25)]])
        ring_mesh("HairBack", rows, m, 0.06, closed=False)
        if style in ("slick", "bun", "coif"):
            for k in range(11):
                dl = D(-55 + 110 * k / 10)
                af, ab = D(-90) + dl, D(90) - dl
                x = math.cos(af) * 0.75
                if style == "slick":
                    pts = [_on(af, 4.9), _on(af, 5.1), (x * 0.8, -0.35, 5.33), (x * 0.8, 0.35, 5.33), _on(ab, 5.1), _on(ab, 4.85), _on(ab, 4.55, 0.1)]
                else:
                    pts = [_on(af, 4.9), _on(af, 5.12), (x * 0.6, -0.2, 5.34), (x * 0.25, 0.22, 5.38)]
                lock(f"Lock{k}", pts, 0.07)
            for sx in (-1, 1):          # the hair swept back over the ears: broad locks lying on the cap's sides
                for k in range(3):
                    a0 = D(0 if sx > 0 else 180) + sx * D(-30 + 12 * k)
                    lock(f"Side{sx}{k}", [_on(a0, 4.98, 0.05), _on(a0 + sx * D(18), 4.92, 0.05), _on(a0 + sx * D(40), 4.86, 0.05)], 0.06)
            if style == "slick":
                cone("WidowPeak", 0.1, 0.0, 0.2, (0, -0.8, 4.86), m, verts=6, rot=(math.pi + 0.35, 0, 0))
        if style == "bun":
            pts = []
            for i in range(40):
                t = i / 39
                a = t * 4.5 * math.pi
                r = 0.3 * (1 - 0.7 * t)
                pts.append((math.cos(a) * r, 0.25 + math.sin(a) * r * 0.75, 5.42 + 0.2 * t + 0.04 * math.sin(a)))
            tube("BunCoil", pts, 0.085, m)
            sphere("BunCore", 0.24, (0, 0.25, 5.48), m, seg=12, rings=7, scale=(1.0, 0.8, 0.7))
        if style == "coif":
            for k in range(9):
                a = k / 9 * 2 * math.pi
                sphere(f"Puff{k}", 0.2, (math.cos(a) * 0.36, 0.1 + math.sin(a) * 0.3, 5.42 + 0.05 * math.sin(a * 2)), m, seg=10, rings=6)
            sphere("PuffTop", 0.27, (0, 0.1, 5.6), m, seg=12, rings=7)
            for sx in (-1, 1):
                base = _on(D(0 if sx > 0 else 180) - sx * D(30), 4.9, 0.12)
                pts = [(base[0] + sx * 0.04 * (1 - math.cos(t * 9)), base[1] + 0.06 * math.sin(t * 9), base[2] - t * 0.8) for t in [i / 24 for i in range(25)]]
                tube(f"Ringlet{sx}", pts, 0.045, m)
        if style == "short":
            for k in range(7):              # a tousled fringe swept to one side over the brow
                a = D(-140 + 100 * k / 6)
                lock(f"Fringe{k}", [_on(a - D(25), 5.24, 0.05), _on(a, 5.1, 0.07), _on(a + D(12), 4.9, 0.08)], 0.09)
            for k in range(5):              # and a few soft tufts on the crown
                a = D(30 + 30 * k)
                lock(f"Tuft{k}", [(math.cos(a) * 0.1, math.sin(a) * 0.1, 5.3), (math.cos(a) * 0.35, math.sin(a) * 0.35, 5.33), _on(a, 5.18, 0.06)], 0.08)
        if style == "curls":
            for k in range(12):
                a = D(-10 + 200 * k / 11)
                c = _on(a, 4.72, 0.1)
                pts = [(c[0] + 0.06 * math.cos(t * 10) * math.cos(a), c[1] + 0.06 * math.cos(t * 10) * math.sin(a), c[2] + 0.12 - t * 0.35 + 0.04 * math.sin(t * 10))
                       for t in [i / 12 for i in range(13)]]
                tube(f"Curl{k}", pts, 0.05, m)
    f.build("head", h)


def mantle(f, m, open_deg=44, z0=4.12, z1=2.1, n=40, nz=8, folds=6, amp=0.07, name="Mantle", flare=(1.2, 0.68, 1.34, 0.82), seed=5):
    """A cloak over the shoulders, open at the front: from round the neck, over the shoulders, down the back and
    sides in folds."""
    a0 = -math.pi / 2 + math.radians(open_deg)
    a1 = a0 + 2 * math.pi - 2 * math.radians(open_deg)
    lv = [(z0 + 0.06, 0, 0.05, 0.52, 0.5, 0.0, folds, 0.0), (z0, 0, 0.04, flare[0], flare[1], 0.01, folds, 0.0)]
    for k in range(1, nz + 1):
        t = k / nz
        lv.append((z0 + (z1 - z0) * t, 0, 0.04, flare[0] + (flare[2] - flare[0]) * t, flare[1] + (flare[3] - flare[1]) * t, amp * t, folds, 0.0))
    f.build("torso", lambda: ring_mesh(name, drape_rings(lv, n, a0, a1, closed=False, seed=seed, hem=0.04), m, 0.045, closed=False))


def feather(name, root, tip, m, width=0.22, n=12):
    """A quill feather: the shaft and a vane of barbs swept back, a little curled."""
    root, tip = Vector(root), Vector(tip)
    d = tip - root
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    tube(f"{name}Shaft", [tuple(root), tuple(root + d * 0.5 + side * 0.02), tuple(tip)], 0.018, m)
    sides = []
    for s in (-1, 1):
        row = []
        for i in range(n + 1):
            t = 0.25 + 0.75 * i / n
            wv = width * math.sin(math.pi * min(1.0, (t - 0.2) / 0.85)) * (1.0 if s > 0 else 0.7)
            row.append(root + d * t + side * s * wv - d.normalized() * 0.06 * wv)
        sides.append(row)
    rows = [sides[0], [root + d * (0.25 + 0.75 * i / n) for i in range(n + 1)], sides[1]]
    ring_mesh(f"{name}Vane", rows, m, 0.012, closed=False)


def open_book(name, centre, mtx, cover, pages, w=1.0, h=1.3):
    """An open book: a cover, two fanned stacks of curved pages, a ribbon marker."""
    s = _mark()
    box(f"{name}Cover", (2 * w + 0.1, h + 0.1, 0.05), (0, 0, 0), cover, bevel=0.02)
    for side in (-1, 1):
        for k in range(4):
            r = [Vector((side * (0.03 + w * u), -h / 2 + 0.04, 0.03 + 0.03 * k + 0.1 * math.sin(math.pi * u) * (0.7 if side < 0 else 1.0))) for u in
                 [i / 10 for i in range(11)]]
            r2 = [Vector((p.x, h / 2 - 0.04, p.z)) for p in r]
            ring_mesh(f"{name}Pages{side}{k}", [r, r2], pages, 0.012, closed=False)
    strip(f"{name}Ribbon", [(0.02, h / 2 - 0.05, 0.15), (0.05, h / 2 + 0.2, 0.0), (0.03, h / 2 + 0.45, -0.25)], 0.06, (1, 0, 0), cover, thick=0.01)
    _xform(s, Matrix.Translation(centre) @ mtx)


def rock(prefix, cx, cy, z0, rx, ry, h, m, seed=0, n=14):
    """A rough-hewn boulder: overlapping lumps of different sizes."""
    rnd = random.Random(seed)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.0, 0.75)
        sphere(f"{prefix}{k}", rnd.uniform(0.35, 0.6) * min(rx, ry) * 1.4, (cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r, z0 + rnd.uniform(0.2, 0.75) * h),
               m, seg=10, rings=6, scale=(rnd.uniform(0.9, 1.4), rnd.uniform(0.9, 1.4), rnd.uniform(0.55, 0.9)))


# ================================================================== busts and statues

def fitted_torso(f, m, trim=None, buttons=5, lapels=True, collar=True, button_m=None, name="Jacket"):
    """A jacket or bodice fitted over the rig's torso block: a slightly larger rounded block (the same soft bevels), a
    hem band, lapels folded back, a row of buttons, a standing collar; trim in a second material."""
    trim = trim or m
    button_m = button_m or trim

    def b():
        box(f"{name}Body", (2.14, 1.14, 2.06), (0, 0, 3.0), m, bevel=0.16, segments=3)
        box(f"{name}Hem", (2.2, 1.2, 0.16), (0, 0, 2.06), trim, bevel=0.06, segments=2)
        tube(f"{name}Seam", [(-1.07, -0.57, 3.95), (-1.07, -0.57, 2.1)], 0.018, trim, poly=True)
        tube(f"{name}Seam2", [(1.07, -0.57, 3.95), (1.07, -0.57, 2.1)], 0.018, trim, poly=True)
        if lapels:
            for sx in (-1, 1):
                tp(f"{name}Lapel{sx}", [(sx * 0.12, 4.0), (sx * 0.62, 4.0), (sx * 0.5, 3.55), (sx * 0.62, 3.42), (sx * 0.22, 2.75)], -0.6, 0.05, m, bevel=0.01)
                tube(f"{name}LapelEdge{sx}", [(sx * 0.62, -0.63, 4.0), (sx * 0.5, -0.63, 3.55), (sx * 0.62, -0.63, 3.42), (sx * 0.22, -0.63, 2.75)], 0.02, trim,
                     poly=True)
        for k in range(buttons):
            z = 3.3 - k * 0.24
            sphere(f"{name}Button{k}", 0.055, (0, -0.6, z), button_m, seg=10, rings=5, scale=(1, 0.5, 1))
        if collar:
            box(f"{name}Collar", (1.3, 1.12, 0.2), (0, 0.02, 4.07), m, bevel=0.07, segments=2)
    f.build("torso", b)


def belt(f, m, buckle, z=2.22, name="Belt", pouch=None):
    def b():
        box(f"{name}", (2.2, 1.2, 0.2), (0, 0, z), m, bevel=0.05, segments=2)
        box(f"{name}Buckle", (0.34, 0.06, 0.28), (0, -0.62, z), buckle, bevel=0.03)
        box(f"{name}BuckleHole", (0.18, 0.08, 0.13), (0, -0.64, z), m, bevel=0.01)
        tube(f"{name}Tongue", [(0, -0.66, z), (0.14, -0.66, z)], 0.015, buckle, poly=True)
        for k in range(3):
            sphere(f"{name}Rivet{k}", 0.03, (-0.5 + k * 0.5 if k != 1 else 0.6, -0.61, z), buckle, seg=6, rings=3)
        if pouch is not None:
            box(f"{name}Pouch", (0.45, 0.3, 0.5), (0.85, -0.55, z - 0.25), pouch, bevel=0.08, segments=2)
            box(f"{name}PouchFlap", (0.47, 0.32, 0.18), (0.85, -0.57, z - 0.06), pouch, bevel=0.05)
            sphere(f"{name}PouchStud", 0.04, (0.85, -0.72, z - 0.1), buckle, seg=6, rings=3)
    f.build("torso", b)


def boots(f, m, trim=None, name="Boot"):
    """Boots over the rig's leg blocks: a rounded shaft to the knee, a turned cuff, a sole and a heel, a buckle strap."""
    trim = trim or m
    for side in (-1, 1):
        j = "rhip" if side > 0 else "lhip"
        x = side * 0.5

        def b(x=x, side=side):
            box(f"{name}{side}", (1.08, 1.08, 1.15), (x, 0, 0.6), m, bevel=0.14, segments=3)
            box(f"{name}Cuff{side}", (1.14, 1.14, 0.2), (x, 0, 1.2), m, bevel=0.07, segments=2)
            box(f"{name}Sole{side}", (1.1, 1.18, 0.1), (x, -0.03, 0.05), trim, bevel=0.03)
            box(f"{name}Strap{side}", (1.12, 1.12, 0.1), (x, 0, 0.42), trim, bevel=0.03)
            box(f"{name}StrapBuckle{side}", (0.16, 0.05, 0.14), (x + side * 0.25, -0.57, 0.42), trim, bevel=0.015)
        f.build(j, b)


def gloves(f, m, trim=None, long=False, name="Glove"):
    """Gloves over the rig's hands (the lower end of the arm block), a flared gauntlet cuff (to the elbow when long)."""
    trim = trim or m
    for side in (-1, 1):
        j = "rshoulder" if side > 0 else "lshoulder"
        x = side * 1.5

        def b(x=x, side=side):
            top = 3.0 if long else 2.65
            box(f"{name}{side}", (1.07, 1.07, top - 1.96), (x, 0, (top + 1.96) / 2), m, bevel=0.14, segments=3)
            box(f"{name}Cuff{side}", (1.16, 1.16, 0.16), (x, 0, top), trim, bevel=0.05, segments=2)
            for k in range(3):
                tube(f"{name}Stitch{side}{k}", [(x - 0.3 + k * 0.3, -0.54, 2.1), (x - 0.3 + k * 0.3, -0.54, 2.4)], 0.012, trim, poly=True)
        f.build(j, b)


def bracelets(f, m, name="Bracelet"):
    for side in (-1, 1):
        j = "rshoulder" if side > 0 else "lshoulder"
        f.build(j, lambda side=side: [hoop(f"{name}{side}{k}", (side * 1.5, 0, 2.6 + k * 0.1), 0.6, "Z", m, thick=0.03) for k in range(2)])


def stole(f, m, trim, name="Stole"):
    def b():
        for sx in (-1, 1):
            strip(f"{name}{sx}", [(sx * 0.36, -0.62, 4.02), (sx * 0.44, -0.75, 3.0), (sx * 0.5, -1.0, 1.4)], 0.32, (1, 0, 0), m, thick=0.04)
            tube(f"{name}Trim{sx}", [(sx * 0.53, -0.65, 4.02), (sx * 0.61, -0.78, 3.0), (sx * 0.67, -1.03, 1.4)], 0.02, trim)
            for k in range(3):
                sphere(f"{name}Tassel{sx}{k}", 0.05, (sx * 0.4 + (k - 1) * 0.1, -1.02, 1.32), trim, seg=6, rings=4, scale=(1, 1, 1.6))
        tube(f"{name}Neck", [(-0.4, -0.6, 4.02), (-0.5, 0.0, 4.12), (0, 0.55, 4.12), (0.5, 0.0, 4.12), (0.4, -0.6, 4.02)], 0.06, m)
    f.build("torso", b)


def satchel_strap(f, m, buckle, name="Strap"):
    def b():
        tube(f"{name}", [(-0.95, -0.58, 4.0), (-0.3, -0.6, 3.35), (0.4, -0.6, 2.7), (1.0, -0.56, 2.25)], 0.05, m, square=True)
        box(f"{name}Buckle", (0.14, 0.05, 0.14), (-0.3, -0.64, 3.35), buckle, bevel=0.015)
    f.build("torso", b)


def _socle(prefix, K, top_m, band, w=1.1, h=0.7, text_=None):
    lathe(f"{prefix}Foot", [(0, 0), (w * 0.6, 0), (w * 0.62, 0.08), (w * 0.5, 0.16), (w * 0.38, 0.22), (w * 0.36, h - 0.15), (w * 0.46, h - 0.08),
                            (w * 0.5, h), (0, h)], top_m, seg=32)
    hoop(f"{prefix}Band", (0, 0, h * 0.45), w * 0.37, "Z", band, thick=0.03)
    if text_:
        box(f"{prefix}Label", (0.62, 0.04, 0.16), (0, -w * 0.38, h * 0.62), band, bevel=0.008)
        text(f"{prefix}LabelText", text_, top_m, 0, -w * 0.4, h * 0.62, (0.55, 0.09), depth=0.008)
    return h


def _bust_cut(f, m, z=2.0):
    """The bust's foot: a rounded truncation of the chest, swelling onto the socle."""
    f.build("torso", lambda: lathe("BustFoot", [(0, z - 0.02), (0.75, z - 0.02), (0.95, z + 0.12), (1.02, z + 0.3), (0, z + 0.3)], m, seg=36))


def bust_headmistress(M):
    """A bronze bust of Headmistress Morrow on a small socle: the rig's head and chest, hair drawn up in locks to a coiled
    bun, a fluted lace ruff, a shawl over her shoulders in folds, a cameo, gilt spectacles, her head turned and lifted."""
    K = kit(M)
    br, dk = K["bronze"], K["bronzedk"]
    h = _socle("S", K, K["black"], K["gilt"], text_="MORROW")
    set_group("Figure")
    s = 0.62
    f = R.Fig(base=(0, 0, h - 2.0 * s), scale=s, pose={"neck": (-8, 0, 18), "waist": (0, 0, -6)}, mats=br, parts=("head", "torso"), face="stern", dark=dk)
    set_group("Costume")
    hair_sculpt(f, br, "bun", seed=11)
    fitted_torso(f, br, trim=K["gilt"], buttons=4, lapels=False, collar=False, name="Bodice")

    def specs():
        for sx in (-1, 1):
            hoop(f"Lens{sx}", (sx * 0.22, -0.64, 4.6), 0.14, "Y", K["gilt"], thick=0.022)
            tube(f"Temple{sx}", [(sx * 0.36, -0.63, 4.62), (sx * 0.61, -0.4, 4.64), (sx * 0.62, -0.1, 4.62)], 0.014, K["gilt"])
        tube("Bridge", [(-0.08, -0.65, 4.62), (0, -0.67, 4.64), (0.08, -0.65, 4.62)], 0.015, K["gilt"])
    f.build("head", specs)
    f.build("torso", lambda: [ruff("Ruff", 4.02, 0.64, 0.98, br, flutes=22, depth=0.08),
                              cyl("Cameo", 0.2, 0.08, (0, -0.56, 3.55), K["bone"], rot=(math.pi / 2, 0, 0), verts=24, bevel=0.02),
                              hoop("CameoRim", (0, -0.61, 3.55), 0.21, "Y", K["gilt"], thick=0.03)])
    mantle(f, dk, open_deg=50, z0=3.95, z1=2.2, folds=7, amp=0.06, name="Shawl", seed=13)
    _bust_cut(f, br)
    set_group("Main")
    return _dims()


def bust_vampire_count(M):
    """A polished obsidian bust of a vampire count: hair combed back in carved locks to a widow's peak, crimson enamel eyes,
    fangs, high cheekbones; a tall flared collar lined in crimson rising behind his head on ribs, a cloak folded over his
    shoulders, a frilled jabot, a gilt bat clasp and chain; chin raised and head turned, on a black marble socle."""
    K = kit(M)
    bm, cr, gl = K["obsidian"], K["crimson"], K["gilt"]
    h = _socle("S", K, K["black"], gl, text_="COUNT V.")
    set_group("Figure")
    s = 0.62
    f = R.Fig(base=(0, 0, h - 2.0 * s), scale=s, pose={"neck": (-14, 0, -22), "waist": (0, 0, 8)}, mats=bm, parts=("head", "torso"), face="fierce", dark=cr)
    set_group("Costume")
    hair_sculpt(f, bm, "slick", seed=21)
    fitted_torso(f, cr, trim=gl, buttons=4, lapels=True, collar=False, button_m=gl, name="Waistcoat")

    def face():
        for sx in (-1, 1):
            sphere(f"RedEye{sx}", 0.07, (sx * 0.22, -0.62, 4.6), cr, seg=8, rings=4, scale=(1, 0.4, 0.8))
            cone(f"Fang{sx}", 0.03, 0.0, 0.11, (sx * 0.1, -0.62, 4.22), K["bone"], verts=5, rot=(math.pi, 0, 0))
            sphere(f"Cheek{sx}", 0.16, (sx * 0.34, -0.5, 4.42), bm, seg=8, rings=5, scale=(1, 0.5, 0.7))
    f.build("head", face)

    def collar():
        def rows(off, shrink):
            out = []
            for k in range(7):
                t = k / 6
                z = 3.95 + 1.2 * t
                r = (0.9 + 0.18 * t ** 1.4) * shrink
                out.append([Vector((math.cos(a) * r, 0.06 + math.sin(a) * r * (0.95 + 0.1 * t) + off, z + 0.12 * t * math.cos(a) ** 2))
                            for a in [math.radians(-12 + 204 * i / 30) for i in range(31)]])
            return out
        ring_mesh("Collar", rows(0.0, 1.0), bm, 0.05, closed=False)
        ring_mesh("CollarLining", rows(-0.04, 0.95), cr, 0.02, closed=False)
        tube("CollarPiping", [tuple(p) for p in rows(0.0, 1.0)[-1]], 0.03, gl)
        for k in range(5):
            a = math.radians(10 + k * 40)
            tube(f"CollarRib{k}", [(math.cos(a) * 0.94, 0.06 + math.sin(a) * 0.92 - 0.03, 3.98), (math.cos(a) * 1.06, 0.06 + math.sin(a) * 1.1 - 0.04, 5.12)],
                 0.025, bm, poly=True)
    f.build("torso", collar)
    mantle(f, bm, open_deg=34, z0=4.0, z1=2.15, folds=8, amp=0.08, name="Cloak", seed=23)

    def front():
        for k in range(4):
            z = 3.85 - k * 0.2
            pts = [(-0.28 + 0.56 * t, -0.6 - 0.05 * math.sin(t * math.pi) - 0.02 * k, z + 0.04 * math.sin(t * 9)) for t in [i / 10 for i in range(11)]]
            strip(f"Jabot{k}", pts, 0.16, (0, 0, 1), bm, thick=0.02)
        sphere("Clasp", 0.12, (0, -0.66, 3.98), gl, seg=10, rings=6, scale=(1, 0.5, 0.8))
        for sx in (-1, 1):
            tp(f"ClaspWing{sx}", [(sx * 0.08, 4.02), (sx * 0.38, 4.12), (sx * 0.34, 3.92), (sx * 0.24, 3.97), (sx * 0.16, 3.88)], -0.68, 0.03, gl)
        tube("ClaspChain", [(-0.62, -0.5, 3.8), (-0.3, -0.66, 3.55), (0.0, -0.7, 3.5), (0.3, -0.66, 3.55), (0.62, -0.5, 3.8)], 0.025, gl)
    f.build("torso", front)
    _bust_cut(f, bm)
    set_group("Main")
    thin_group("Costume", 0.9)
    return _dims()


def bust_veiled_student(M):
    """A marble bust of a lost student under a carved sheer veil: the veil falls from the crown over the face (the nose
    pressing through it) and over the shoulders in fine folds with a waved hem; the blazer's lapels and crest beneath;
    IN MEMORIAM on the socle."""
    K = kit(M)
    mb = K["marble"]
    h = _socle("S", K, K["soot"], K["brass"], text_="IN MEMORIAM")
    set_group("Figure")
    s = 0.62
    f = R.Fig(base=(0, 0, h - 2.0 * s), scale=s, pose={"neck": (14, 0, 6)}, mats=mb, parts=("head", "torso"), face="sorrow", dark=mb)
    set_group("Costume")
    f.build("torso", lambda: [tp("Crest", [(-0.85, 3.62), (-0.5, 3.62), (-0.5, 3.35), (-0.675, 3.18), (-0.85, 3.35)], -0.6, 0.03, K["bronze"]),
                              strip("Tie", [(0, -0.6, 3.95), (0, -0.62, 3.4), (0, -0.62, 2.9)], 0.18, (1, 0, 0), mb, thick=0.03)])
    lv = [(5.25, 0, 0.0, 0.02, 0.02, 0.0, 9, 0.0), (5.22, 0, 0.0, 0.36, 0.36, 0.0, 9, 0.0), (5.16, 0, 0.0, 0.56, 0.56, 0.0, 9, 0.0), (5.02, 0, 0.0, 0.72, 0.72, 0.005, 9, 0.0),
          (4.6, 0, 0.0, 0.76, 0.76, 0.012, 9, 0.0), (4.25, 0, 0.0, 0.77, 0.77, 0.02, 9, 0.0), (4.0, 0, 0.03, 0.95, 0.72, 0.035, 11, 0.0),
          (3.75, 0, 0.0, 1.3, 0.8, 0.07, 13, 0.0), (3.2, 0, 0.0, 1.38, 0.88, 0.1, 11, 0.0), (2.6, 0, 0.0, 1.42, 0.94, 0.12, 11, 0.0),
          (2.12, 0, 0.0, 1.45, 0.98, 0.13, 11, 0.0)]
    a0, a1 = -math.pi / 2 + math.radians(48), -math.pi / 2 + 2 * math.pi - math.radians(48)
    f.build("head", lambda: ring_mesh("Veil", drape_rings(lv, 72, a0, a1, closed=False, seed=31, hem=0.06, hem_k=14), mb, 0.018, closed=False))
    _bust_cut(f, mb)
    set_group("Main")
    return _dims()


def _cracked_disc(prefix, r, z, m, crack, rnd, n=9):
    """A round slab of flagstones split by radial and ring cracks, shards thrown out (where something landed or burst)."""
    lathe(f"{prefix}Slab", [(0, z - 0.3), (r, z - 0.3), (r + 0.05, z - 0.22), (r, z - 0.02), (0, z)], m, seg=40)
    for k in range(n):
        a = k / n * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        pts, rr = [], 0.25
        while rr < r - 0.05:
            pts.append((math.cos(a) * rr, math.sin(a) * rr, z + 0.005))
            a += rnd.uniform(-0.25, 0.25)
            rr += rnd.uniform(0.25, 0.4)
        if len(pts) > 1:
            tube(f"{prefix}Crack{k}", pts, 0.025, crack, poly=True)
    tube(f"{prefix}Ring", [(math.cos(t) * r * 0.55, math.sin(t) * r * 0.55, z + 0.005) for t in [i / 40 * 2 * math.pi for i in range(41)]], 0.02, crack, poly=True)
    for k in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.6, 1.0) * r
        box(f"{prefix}Shard{k}", (rnd.uniform(0.2, 0.4), rnd.uniform(0.15, 0.3), rnd.uniform(0.08, 0.16)), (math.cos(a) * rr, math.sin(a) * rr, z + 0.06), m,
            bevel=0.02, rot=(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, 3)))


def _aura():
    return flat("Aura41", (0.9, 0.85, 0.6), 0.5)


def statue_choir_child(M):
    """The chorister casting: a marble Chapel Choir singer in a wide, braced stance, one hand raised before his face in
    a sign, the other flung down and back with fingers spread, head bowed in the chant; a ring of holy light blazes
    behind him, a rune circle burns round his feet and the sign-hand flickers (Glow); torn hymnal pages whirl round him,
    his surplice and bell sleeves flare in folds. The scene: a cracked chapel floor split outward from where he stands."""
    K = kit(M)
    mb, st, dk = K["marble"], K["soot"], K["sootdk"]
    rnd = random.Random(4121)
    H = 0.5
    _cracked_disc("Floor", 3.0, H, st, dk, rnd)
    set_group("Figure")
    f = R.Fig(base=(0, 0, H), scale=S, yaw=math.radians(-15),
              pose={"lift": -0.22, "rhip": (-12, -22, 0), "rknee": (28, 0, 0), "lhip": (8, 24, 0), "lknee": (24, 0, 0), "waist": (8, 0, -10),
                    "neck": (16, 0, 8), "rshoulder": (-82, 0, -38), "relbow": (-95, 0, -10), "lshoulder": (25, 48, 0), "lelbow": (0, 18, 0)},
              mats=mb, parts=("head", "torso", "rarm", "larm", "rleg", "lleg"), face="sing", dark=dk)
    set_group("Costume")
    gown(f, mb, z0=3.6, z1=1.0, top=(1.12, 0.64), bot=(1.9, 1.5), folds=12, amp=0.16, train=0.35, hem=0.12, name="Surplice", seed=42)
    for side in (-1, 1):
        sleeve2(f, side, mb, z1=2.05, r0=0.62, r1=0.98, folds=6, amp=0.09, name="BellSleeve")
    f.build("torso", lambda: ruff("Ruff", 4.02, 0.64, 1.02, mb, flutes=24, depth=0.09))
    fitted_torso(f, mb, trim=K["bronze"], buttons=6, lapels=False, collar=False, name="Cassock")
    boots(f, mb, K["bronze"])
    stole(f, K["bronze"], K["gilt"])
    hair_sculpt(f, mb, "short", seed=43)
    for k in range(9):
        a = k / 9 * 2 * math.pi
        rr = rnd.uniform(1.6, 2.6)
        zz = H + rnd.uniform(2.0, 8.5)
        s = _mark()
        rows = [[Vector((-0.28 + 0.56 * i / 6, 0, 0.1 * math.sin(i))) for i in range(7)], [Vector((-0.28 + 0.56 * i / 6, 0.4, 0.06 * math.sin(i + 1))) for i in range(7)]]
        ring_mesh(f"Page{k}", rows, mb, 0.012, closed=False)
        _xform(s, Matrix.Translation((math.cos(a) * rr, math.sin(a) * rr, zz)) @ Matrix.Rotation(rnd.uniform(0, 3), 4, "Z") @ Matrix.Rotation(rnd.uniform(-1, 1), 4, "X"))
    for k in range(5):
        a = k / 5 * 2 * math.pi + 0.3
        tube(f"PageStalk{k}", [(math.cos(a) * 2.2, math.sin(a) * 2.2, H), (math.cos(a + 0.4) * 2.0, math.sin(a + 0.4) * 2.0, H + 2.5)], 0.025, mb)
    set_group("Glow")
    au = _aura()
    c = f.at("torso", (0, 0.9, 4.4))
    s = _mark()
    hoop("AuraRing", (0, 0, 0), 2.6, "Y", au, thick=0.07)
    hoop("AuraRing2", (0, 0, 0), 2.25, "Y", au, thick=0.035)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        cone(f"AuraRay{k}", 0.06, 0.0, 0.55, (math.cos(a) * 2.95, 0, math.sin(a) * 2.95), au, verts=4, rot=(0, -a + math.pi / 2, 0))
    _xform(s, Matrix.Translation(c))
    tube("RuneCircle", [(math.cos(t) * 2.2, math.sin(t) * 2.2, H + 0.03) for t in [i / 64 * 2 * math.pi for i in range(65)]], 0.04, au, poly=True)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        x, y = math.cos(a) * 2.45, math.sin(a) * 2.45
        tube(f"Rune{k}", [(x - 0.1, y, H + 0.03), (x, y + 0.12, H + 0.03), (x + 0.1, y - 0.05, H + 0.03)], 0.025, au, poly=True)
    hp = f.at("rshoulder", (1.5, -0.3, 2.1))
    for k in range(5):
        a = k / 5 * 2 * math.pi
        cone(f"SignFlame{k}", 0.09, 0.0, 0.5, (hp.x + math.cos(a) * 0.25, hp.y - 0.15, hp.z + 0.25 + math.sin(a) * 0.12), au, verts=5,
             rot=(0.2 * math.sin(a), 0.3 * math.cos(a), 0))
    set_group("Main")
    return _dims()


def statue_ink_scribe(M):
    """The Ink Club's duellist in a low lunge, a giant quill drawn back over his shoulder like a sword, an inkwell held out
    in the other hand; the gilt nib flings a whipping ribbon of glossy ink through the air behind it; a long coat flares from
    the lunge, a scarf streams back, a beret over curls. The scene: his front foot planted on a toppled pile of books,
    papers strewn round, an overturned inkwell spreading across the stone."""
    K = kit(M)
    br, dk, st, sd, ink = K["bronze"], K["bronzedk"], K["soot"], K["sootdk"], K["inkgloss"]
    rnd = random.Random(4122)
    box("Foot", (6.0, 3.8, 0.3), (0, 0, 0.15), sd, bevel=0.05)
    box("Top", (5.7, 3.5, 0.3), (0, 0, 0.45), st, bevel=0.04)
    H = 0.6
    for k in range(5):
        w_, d_, h_ = rnd.uniform(0.9, 1.3), rnd.uniform(0.7, 1.0), rnd.uniform(0.18, 0.28)
        box(f"Book{k}", (w_, d_, h_), (-1.4 + rnd.uniform(-0.1, 0.1), -0.6 + rnd.uniform(-0.1, 0.1), H + 0.12 + k * 0.22), dk if k % 2 else br, bevel=0.03,
            rot=(rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), rnd.uniform(-0.5, 0.5)))
    box("BookFallen", (1.2, 0.85, 0.24), (-2.3, 0.4, H + 0.3), dk, bevel=0.03, rot=(0.0, 0.5, 0.4))
    for k in range(8):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.9, 2.4)
        s = _mark()
        rows = [[Vector((-0.3 + 0.6 * i / 5, 0, 0.03 * math.sin(i * 1.3))) for i in range(6)], [Vector((-0.3 + 0.6 * i / 5, 0.42, 0.02 * math.sin(i))) for i in range(6)]]
        ring_mesh(f"Paper{k}", rows, br, 0.01, closed=False)
        _xform(s, Matrix.Translation((math.cos(a) * rr, math.sin(a) * rr * 0.6, H + 0.02)) @ Matrix.Rotation(rnd.uniform(0, 3), 4, "Z"))
    s = _mark()
    sphere("Inkwell", 0.22, (0, 0, 0), K["black"], seg=14, rings=7, scale=(1, 1.3, 0.75))
    _xform(s, Matrix.Translation((1.9, -1.0, H + 0.16)) @ Matrix.Rotation(1.3, 4, "X"))
    pool = [(math.cos(a) * (0.8 + 0.12 * math.sin(a * 5)), math.sin(a) * (0.5 + 0.06 * math.cos(a * 3))) for a in [i / 28 * 2 * math.pi for i in range(28)]]
    B20.tprism("Pool", WS.ccw([(1.9 + x, -1.45 + y) for x, y in pool]), H + 0.012, 0.02, ink, plane="XY")
    set_group("Figure")
    sc = 1.55
    f = R.Fig(base=(0.3, 0.1, H), yaw=math.radians(-55), scale=sc,
              pose={"lift": -0.42, "lhip": (-72, 0, 0), "lknee": (78, 0, 0), "rhip": (52, 0, 0), "rknee": (18, 0, 0), "waist": (22, 0, 18),
                    "neck": (-14, 0, -22), "rshoulder": (55, -55, 0), "relbow": (-70, 0, 0), "lshoulder": (-88, 0, 12), "lelbow": (-8, 0, 0)},
              mats=br, face="fierce", dark=dk)
    set_group("Costume")
    mantle(f, dk, open_deg=40, z0=4.08, z1=1.1, folds=6, amp=0.06, name="Coat", flare=(1.17, 0.65, 1.38, 1.1), seed=51)
    for side in (-1, 1):
        sleeve2(f, side, dk, z0=3.98, z1=2.5, r0=0.62, r1=0.7, folds=7, amp=0.06, name="CoatSleeve", cuff=dk)
    fitted_torso(f, br, trim=K["gilt"], buttons=5, lapels=True, collar=False, name="Waistcoat")
    belt(f, dk, K["gilt"])
    boots(f, dk, K["gilt"])
    gloves(f, dk, K["gilt"])

    def scarf():
        hoop("ScarfWrap", (0, 0, 4.02), 0.64, "Z", br, thick=0.13)
        hoop("ScarfWrap2", (0, 0, 4.18), 0.56, "Z", br, thick=0.11)
        pts = [(0.2 + 0.9 * t, 0.6 + 1.6 * t + 0.12 * math.sin(t * 8), 4.0 + 0.4 * math.sin(t * 3)) for t in [i / 10 for i in range(11)]]
        strip("ScarfStream", pts, 0.32, (0, 0, 1), br, thick=0.04)
    f.build("torso", scarf)
    hair_sculpt(f, br, "curls", seed=53)
    f.build("head", lambda: [sphere("Beret", 0.78, (0.12, 0.05, 5.2), dk, seg=20, rings=10, scale=(1.05, 1.0, 0.32)),
                             hoop("BeretBand", (0.05, 0.02, 4.99), 0.8, "Z", dk, thick=0.06)])
    # the giant quill drawn back over his shoulder like a sword, ink flung from its nib; the inkwell held out before him
    g = f.at("rshoulder", (1.5, -0.1, 1.95))
    dq = ((f.at("rshoulder", (1.5, -0.1, 3.0)) - g).normalized() + Vector((0, 0, 0.6))).normalized()
    nib = g - dq * 0.7
    cone("Nib", 0.09, 0.0, 0.45, tuple(nib - dq * 0.2), K["gilt"], verts=8, rot=Vector((0, 0, -1)).rotation_difference(dq).to_euler())
    feather("Quill", nib, g + dq * 3.6, br, width=0.55, n=16)
    side = dq.cross(Vector((0, 0, 1)))
    side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
    rows = []
    for jj in range(2):
        row = []
        for i_ in range(16):
            t = i_ / 15
            a_ = math.pi * 1.1 * t
            p = nib + (side * math.sin(a_) * 1.6 + dq * (1 - math.cos(a_)) * 0.9) * (0.5 + 0.5 * t) + Vector((0, 0, -0.5 * t))
            row.append(p + Vector((0, 0, 0.12 * (1 - t) * (1 if jj else -1))))
        rows.append(row)
    ring_mesh("InkRibbon", rows, ink, 0.03, closed=False)
    for k in range(5):
        p = rows[0][6 + k * 2] + Vector((0.15 * math.sin(k * 2), 0.15, -0.3 - 0.1 * k))
        sphere(f"InkDrop{k}", 0.07 - 0.008 * k, tuple(p), ink, seg=8, rings=5, scale=(1, 1, 1.5))
    hp = f.at("lshoulder", (-1.5, -0.25, 1.9))
    lathe("InkwellHeld", [(0, 0), (0.3, 0), (0.34, 0.1), (0.3, 0.32), (0.14, 0.4), (0.12, 0.5), (0, 0.5)], K["black"], seg=20,
          loc=tuple(hp + Vector((0, -0.1, 0.1))))
    hoop("InkwellRim", tuple(hp + Vector((0, -0.1, 0.6))), 0.13, "Z", K["gilt"], thick=0.03)
    lathe("InkwellInk", [(0, 0.46), (0.11, 0.46), (0, 0.48)], ink, seg=16, loc=tuple(hp + Vector((0, -0.1, 0.1))))
    set_group("Main")
    thin_group("Costume", 0.78)
    return _dims()


def statue_court_duchess(M):
    """The duchess's over-the-shoulder glare: a Crimson Court duchess in polished obsidian striding away, turned back from the
    waist to glare over her shoulder at you with crimson eyes, her cloak lined in crimson flaring out on the turn, the
    gown's train whipping the other way, one arm flung out with her pleated crimson fan snapped open. The scene: broken iron chains and a burst
    shackle at her feet, crimson rose petals and a fallen goblet, on an octagonal plinth."""
    K = kit(M)
    bm, cr, gl, ir = K["obsidian"], K["crimson"], K["gilt"], K["iron"]
    pl = K["black"]
    rnd = random.Random(4123)
    lathe("Base", [(0, 0), (2.5, 0), (2.55, 0.12), (2.35, 0.3), (2.2, 0.35), (2.2, 1.0), (2.35, 1.1), (2.5, 1.25), (2.5, 1.4), (0, 1.4)], pl, seg=8)
    hoop("BaseBand", (0, 0, 0.7), 2.22, "Z", gl, thick=0.04)
    H = 1.4
    for k in range(3):
        a = rnd.uniform(0, 2 * math.pi)
        start = Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, H + 0.08))
        end = start + Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), 0))
        chain(f"BrokenChain{k}", tuple(start), tuple(end), ir, link=0.18, thick=0.035)
    hoop("Shackle", (1.3, -1.3, H + 0.2), 0.28, "X", ir, thick=0.06)
    box("ShackleHinge", (0.12, 0.2, 0.2), (1.3, -1.3, H + 0.48), ir, bevel=0.02)
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.8, 2.1)
        sphere(f"Petal{k}", 0.09, (math.cos(a) * rr, math.sin(a) * rr, H + 0.02), cr, seg=6, rings=3, scale=(1.2, 0.8, 0.25))
    s = _mark()
    lathe("Goblet", [(0, 0), (0.22, 0), (0.06, 0.08), (0.05, 0.38), (0.26, 0.52), (0.3, 0.85), (0, 0.85)], gl, seg=20)
    _xform(s, Matrix.Translation((-1.5, -1.0, H + 0.25)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    set_group("Figure")
    f = R.Fig(base=(0, 0.2, H), scale=S, yaw=math.radians(125),
              pose={"rhip": (-25, 0, 0), "rknee": (20, 0, 0), "lhip": (22, 0, 0), "waist": (0, 0, 30), "neck": (-10, 0, 45), "root": (0, 0, 6),
                    "rshoulder": (-10, -82, 0), "relbow": (0, -18, 0), "lshoulder": (-25, 35, 0), "lelbow": (-60, 0, 0)},
              mats=bm, parts=("head", "torso", "rarm", "larm"), face="fierce", dark=cr)
    set_group("Costume")
    gown(f, bm, z0=2.2, z1=0.03, top=(1.08, 0.6), bot=(2.1, 1.4), folds=10, amp=0.18, train=0.7, hem=0.1, n=64, nz=12, name="Gown", seed=61)
    import tapestry_renders as TR
    TR.cape(f, bm, cr, flare=2.1, hem=1.7, back=0.75, sway=-0.9, name="Capelet")
    TR.high_collar(f, bm, cr)
    fitted_torso(f, bm, trim=gl, buttons=0, lapels=False, collar=False, name="Bodice")
    f.build("torso", lambda: [tube(f"Lace{k}", [(-0.25, -0.6, 2.4 + k * 0.3), (0.25, -0.6, 2.55 + k * 0.3)], 0.02, cr, poly=True) for k in range(5)] +
            [tube(f"LaceX{k}", [(0.25, -0.6, 2.4 + k * 0.3), (-0.25, -0.6, 2.55 + k * 0.3)], 0.02, cr, poly=True) for k in range(5)])
    gloves(f, cr, gl, long=True)
    bracelets(f, gl)
    belt(f, cr, gl, z=2.25, name="Girdle")

    def bodice():
        strip("Sash", [(-1.05, -0.56, 3.9), (-0.4, -0.6, 3.3), (0.3, -0.6, 2.7), (0.95, -0.56, 2.25)], 0.34, (0.6, 0, 0.8), cr, thick=0.04)
        for k in range(3):
            tube(f"Necklace{k}", [(-0.45 + 0.02 * k, -0.57, 3.98 - 0.08 * k), (0, -0.62, 3.75 - 0.1 * k), (0.45 - 0.02 * k, -0.57, 3.98 - 0.08 * k)], 0.022, gl)
    f.build("torso", bodice)
    for side in (-1, 1):
        f.build("rshoulder" if side > 0 else "lshoulder", lambda side=side: sphere(f"Puff{side}", 0.66, (side * 1.5, 0, 3.55), bm, seg=14, rings=8,
                                                                                    scale=(1.0, 1.0, 0.8)))
        sleeve2(f, side, bm, z0=3.3, z1=2.25, r0=0.58, r1=0.62, folds=5, amp=0.03, name="Sleeve", cuff=cr)
    hair_sculpt(f, bm, "coif", seed=63)

    def tiara():
        pts = [(math.cos(a) * 0.79, math.sin(a) * 0.79, 5.06) for a in [math.radians(200 + 140 * i / 16) for i in range(17)]]
        tube("Tiara", pts, 0.03, gl)
        for k in range(7):
            a = math.radians(210 + k * 20)
            hgt = 0.18 + (0.14 if k == 3 else 0.05 * (3 - abs(k - 3)))
            cone(f"TiaraSpike{k}", 0.055, 0.0, hgt, (math.cos(a) * 0.79, math.sin(a) * 0.79, 5.06 + hgt / 2), gl, verts=4)
        for sx in (-1, 1):
            sphere(f"GlareEye{sx}", 0.06, (sx * 0.22, -0.63, 4.58), cr, seg=8, rings=4, scale=(1.2, 0.4, 0.6))
    f.build("head", tiara)
    hp = f.at("rshoulder", (1.5, -0.3, 1.9))
    s = _mark()
    rows = []
    for r in (0.15, 1.15):
        rows.append([Vector((math.cos(math.radians(10 + 160 * i_ / 30)) * r, 0.05 * (1 if i_ % 2 else -1) * r, math.sin(math.radians(10 + 160 * i_ / 30)) * r))
                     for i_ in range(31)])
    ring_mesh("FanLeaf", rows, cr, 0.015, closed=False)
    for k in range(16):
        a_ = math.radians(10 + k * 160 / 15)
        tube(f"FanRib{k}", [(0, -0.04, 0), (math.cos(a_) * 1.17, -0.04, math.sin(a_) * 1.17)], 0.014, gl, poly=True)
    tube("FanEdge", [(math.cos(math.radians(10 + 160 * i_ / 30)) * 1.15, 0.0, math.sin(math.radians(10 + 160 * i_ / 30)) * 1.15) for i_ in range(31)], 0.02, gl)
    sphere("FanRivet", 0.06, (0, -0.05, 0), gl, seg=8, rings=4)
    _xform(s, Matrix.Translation(hp) @ Matrix.Rotation(math.radians(125), 4, "Z") @ Matrix.Rotation(-0.5, 4, "Y"))
    set_group("Main")
    thin_group("Costume", 0.75)
    return _dims()


def sculpture_clasped_hands(M):
    """Two marble R6 arms in folded sleeves with fluted cuffs rise out of a rough-hewn boulder under a carved cloth,
    their hands holding the school's great gilt key aloft; on a moulded plinth with a gilt plaque."""
    K = kit(M)
    mb, st, dk, gl = K["marble"], K["soot"], K["sootdk"], K["gilt"]
    box("Foot", (2.8, 2.8, 0.3), (0, 0, 0.15), dk, bevel=0.05)
    box("Die", (2.4, 2.4, 1.9), (0, 0, 0.3 + 0.95), st, bevel=0.04)
    box("Cap", (2.7, 2.7, 0.2), (0, 0, 2.3), dk, bevel=0.04)
    box("PlaqueFrame", (1.3, 0.04, 0.42), (0, -1.22, 1.3), gl, bevel=0.01)
    text("PlaqueText", "WE HOLD THE KEY", K["black"], 0, -1.25, 1.3, (1.15, 0.2), depth=0.01)
    H = 2.4
    set_group("Figure")
    rock("Rock", 0, 0, H, 0.95, 0.8, 0.9, mb, seed=4124, n=12)
    lv = [(H + 1.15, 0, 0, 0.55, 0.45, 0.02, 6, 0.0), (H + 0.95, 0, 0, 0.95, 0.8, 0.05, 7, 0.0), (H + 0.55, 0, 0, 1.2, 1.05, 0.1, 9, 0.0),
          (H + 0.05, 0, 0, 1.28, 1.15, 0.13, 9, 0.0)]
    ring_mesh("Drape", drape_rings(lv, 56, seed=71, hem=0.04, hem_k=11), mb, 0.04)
    s = 0.95
    f = R.Fig(base=(0, 0, H + 0.35 - 3.6 * s), scale=s, pose={"rshoulder": (4, -176, 0), "relbow": (0, -12, 0), "lshoulder": (4, 176, 0), "lelbow": (0, 12, 0)},
              mats=mb, parts=("rarm", "larm"))
    set_group("Costume")
    for side in (-1, 1):
        sleeve2(f, side, mb, z0=4.1, z1=2.75, r0=0.6, r1=0.66, folds=6, amp=0.05, name="ArmSleeve")
        f.build("rshoulder" if side > 0 else "lshoulder", lambda side=side: ruff(f"Cuff{side}", 2.7, 0.5, 0.78, mb, flutes=14, depth=0.06, cx=side * 1.5))
    a, b = f.at("rshoulder", (1.5, 0, 1.95)), f.at("lshoulder", (-1.5, 0, 1.95))
    c = (a + b) / 2 + Vector((0, -0.05, -0.6))
    s2 = _mark()
    hoop("KeyBow", (0, 0, 0.75), 0.42, "Y", gl, thick=0.08)
    sphere("KeyGem", 0.17, (0, -0.04, 0.75), K["crimson"], seg=12, rings=6)
    for k in range(4):
        aa = k * math.pi / 2 + math.pi / 4
        sphere(f"KeyLobe{k}", 0.15, (math.cos(aa) * 0.42, 0, 0.75 + math.sin(aa) * 0.42), gl, seg=10, rings=5)
    tube("KeyShaft", [(0, 0, 0.33), (0, 0, -1.9)], 0.1, gl, poly=True)
    box("KeyBit", (0.55, 0.14, 0.3), (0.27, 0, -1.65), gl, bevel=0.03)
    box("KeyBit2", (0.38, 0.14, 0.2), (0.18, 0, -1.25), gl, bevel=0.03)
    _xform(s2, Matrix.Translation(c + Vector((0, 0, 1.0))))
    set_group("Main")
    return _dims()


# ================================================================== reliefs and plaques

def _panel_frame(K, W, H, z0, st, dk, depth=0.5):
    box("Back", (W, depth, H), (0, depth / 2, z0 + H / 2), st, bevel=0.03)
    for sz in (-1, 1):
        box(f"RailH{sz}", (W + 0.3, depth + 0.25, 0.3), (0, depth / 2 - 0.12, z0 + H / 2 + sz * (H / 2 + 0.1)), dk, bevel=0.04)
    for sx in (-1, 1):
        box(f"RailV{sx}", (0.3, depth + 0.25, H), (sx * (W / 2 + 0.1), depth / 2 - 0.12, z0 + H / 2), dk, bevel=0.04)


def relief_founding(M):
    """A carved limestone relief of the school's founding: the three founders on the hill (one kneels to lay the
    cornerstone with a trowel, one lifts the great key, one unrolls the charter), the first towers rising behind them in
    low relief, a crescent moon, all in a moulded frame with an inscription band."""
    K = kit(M)
    st, dk = K["stone"], K["stonedark"]
    W, H, z0 = 7.0, 4.2, 0.9
    _panel_frame(K, W, H, z0, st, dk)
    m0 = _mark()
    for k, (x, w, h) in enumerate(((-2.4, 0.8, 2.6), (-1.5, 1.2, 1.7), (1.9, 0.9, 2.9), (2.8, 0.7, 2.0), (0.4, 1.0, 1.4))):
        box(f"Tower{k}", (w, 0.12, h), (x, -0.06, z0 + 0.6 + h / 2), st, bevel=0.02)
        cone(f"Spire{k}", w * 0.7, 0.0, h * 0.4, (x, -0.06, z0 + 0.6 + h + h * 0.2), st, verts=4, rot=(0, 0, math.pi / 4))
    tp("Moon", WS.crescent(-2.9, z0 + H - 0.6, 0.35, shift=0.4, tilt=math.pi / 2), -0.04, 0.06, st)
    tp("Hill", [(-W / 2, z0), (W / 2, z0), (W / 2, z0 + 0.5), (1.5, z0 + 0.75), (-1.0, z0 + 0.7), (-W / 2, z0 + 0.45)], -0.05, 0.1, st)
    flatten(m0, 0.0, 0.25)
    set_group("Figure")
    m = _mark()
    s = 0.62
    poses = [((-1.6, z0 + 0.62), 20, {"rhip": (-90, 0, 0), "rknee": (95, 0, 0), "lhip": (-20, 0, 0), "lknee": (105, 0, 0), "lift": -0.95,
                                      "waist": (22, 0, 0), "rshoulder": (-75, 0, -10), "relbow": (-30, 0, 0), "lshoulder": (-20, 0, 15), "neck": (18, 0, 0)}),
             ((0.1, z0 + 0.72), 0, {"rshoulder": (0, -165, 0), "relbow": (0, -10, 0), "lshoulder": (0, 30, 0), "lelbow": (-40, 0, 0), "neck": (-18, 0, 0),
                                    "lhip": (-10, 0, 0), "rhip": (12, 0, 0)}),
             ((1.7, z0 + 0.66), -25, {"rshoulder": (-75, 0, -30), "relbow": (-20, 0, 0), "lshoulder": (-75, 0, 30), "lelbow": (-20, 0, 0),
                                      "neck": (8, 0, 20), "rhip": (-15, 0, 0)})]
    for i, ((x, z), yaw, pose) in enumerate(poses):
        f = R.Fig(base=(x, -0.3, z), yaw=math.radians(yaw), scale=s, pose=pose, mats=st, face="stern", dark=dk, decimate=0.55)
        if i == 1:
            gown(f, st, z0=2.2, z1=0.05, top=(1.08, 0.6), bot=(1.6, 1.2), folds=8, amp=0.12, hem=0.05, n=32, nz=6, name="Robe", seed=80 + i)
        mantle(f, st, open_deg=40, z0=4.08, z1=1.2 if i != 1 else 0.6, n=28, nz=6, folds=7, amp=0.1, name="Coat", seed=90 + i)
        for side in (-1, 1):
            sleeve2(f, side, st, z1=2.2, r0=0.62, r1=0.74, folds=5, amp=0.06, n=16, nz=5, name="Sleeve")
        hair_sculpt(f, st, ("short", "slick", "bun")[i], seed=100 + i)
        if i == 1:
            TRkey = f.at("rshoulder", (1.5, 0, 1.6))
            tube("Key", [tuple(TRkey), tuple(TRkey + Vector((0.15, 0, 1.0)))], 0.05, st, poly=True)
            hoop("KeyBow", tuple(TRkey + Vector((0.18, 0, 1.15))), 0.15, "Y", st, thick=0.04)
        if i == 2:
            sc = f.at("rshoulder", (1.5, -0.2, 1.9))
            box("Charter", (1.1, 0.04, 0.8), tuple((sc + f.at("lshoulder", (-1.5, -0.2, 1.9))) / 2 + Vector((0, -0.1, 0.1))), st, bevel=0.02)
    box("Cornerstone", (0.7, 0.5, 0.5), (-0.9, -0.3, z0 + 0.9), st, bevel=0.03)
    flatten(m, 0.0, 0.32, decimate=0.65)
    set_group("Main")
    box("Band", (W, 0.1, 0.42), (0, -0.05, z0 + 0.25), dk, bevel=0.02)
    text("Inscription", "IN THE YEAR OF THE BLOOD MOON THE HOUSE WAS FOUNDED", st, 0, -0.1, z0 + 0.25, (6.2, 0.22))
    to_wall()
    return _dims()


def relief_danse_macabre(M):
    """A soot-dark stone frieze of the danse macabre: students and skeletons hand in hand in a ring dance, every second
    dancer a skeleton (the R6 body with carved ribs, an eyeless skull and a grin), kicking up their heels."""
    K = kit(M)
    st, dk, mb = K["soot"], K["sootdk"], K["marble"]
    W, H, z0 = 9.0, 2.6, 1.0
    _panel_frame(K, W, H, z0, st, dk, depth=0.45)
    set_group("Figure")
    m = _mark()
    s = 0.36
    n = 7
    for i in range(n):
        x = -W / 2 + 0.7 + i * (W - 1.4) / (n - 1)
        bone = i % 2 == 1
        kick = 1 if i % 2 else -1
        pose = {"rshoulder": (0, -95, 0), "relbow": (0, -20, 0), "lshoulder": (0, 95, 0), "lelbow": (0, 20, 0), "rhip": (-35 * kick, 0, 0), "rknee": (40, 0, 0),
                "lhip": (15 * kick, 0, 0), "neck": (0, 0, 15 * kick), "waist": (0, 0, 8 * kick)}
        mat = mb if bone else st
        set_group("Figure" if i < 4 else "Figure2")
        f = R.Fig(base=(x, -0.2, z0 + 0.25), yaw=math.radians(kick * 12), scale=s, pose=pose, mats=mat, face=None if bone else "smile", dark=dk, decimate=0.4)
        if bone:
            def ribs():
                for k in range(5):
                    z = 3.75 - k * 0.3
                    w_ = 0.85 - k * 0.07
                    for sx in (-1, 1):
                        tube(f"Rib{k}{sx}", [(0, -0.54, z + 0.05), (sx * w_ * 0.6, -0.56, z), (sx * w_, -0.52, z - 0.12), (sx * w_ * 1.05, -0.4, z - 0.2)], 0.045, dk)
                tube("Spine", [(0, -0.53, 3.95), (0, -0.55, 3.0), (0, -0.53, 2.2)], 0.06, dk)
                tube("Pelvis", [(-0.7, -0.52, 2.3), (-0.3, -0.56, 2.08), (0.3, -0.56, 2.08), (0.7, -0.52, 2.3)], 0.06, dk)
            f.build("torso", ribs)

            def skull():
                for sx in (-1, 1):
                    sphere(f"Socket{sx}", 0.16, (sx * 0.24, -0.56, 4.6), dk, seg=8, rings=5, scale=(1, 0.4, 1.1))
                tp("NoseHole", [(-0.06, 4.38), (0.06, 4.38), (0, 4.5)], -0.6, 0.03, dk)
                for k in range(5):
                    box(f"Tooth{k}", (0.06, 0.04, 0.12), (-0.2 + k * 0.1, -0.6, 4.2), dk, bevel=0.01)
            f.build("head", skull)
        else:
            if i % 4 == 0:
                gown(f, st, z0=2.2, z1=0.6, top=(1.08, 0.6), bot=(1.9, 1.3), folds=8, amp=0.14, hem=0.08, n=28, nz=5, name="Dress", seed=110 + i)
            else:
                mantle(f, st, open_deg=40, z0=4.08, z1=1.6, n=24, nz=5, folds=6, amp=0.08, name="Coat", seed=120 + i)
            for side in (-1, 1):
                sleeve2(f, side, st, z1=2.3, r0=0.6, r1=0.68, folds=5, amp=0.05, n=14, nz=4, name="Sleeve")
            hair_sculpt(f, st, ("bun", "short", "curls", "slick")[(i // 2) % 4], seed=130 + i)
    flatten(m, 0.0, 0.35, decimate=0.75)
    set_group("Main")
    for k in range(int(W / 0.6)):
        x = -W / 2 + 0.3 + k * 0.6
        tp(f"Grave{k}", [(x - 0.12, z0 + 0.05), (x + 0.12, z0 + 0.05), (x + 0.12, z0 + 0.2), (x, z0 + 0.27), (x - 0.12, z0 + 0.2)], -0.03, 0.05, dk)
    to_wall()
    return _dims()


def plaque_memorial(M):
    """A cast bronze memorial plaque: a raised border of thorned rose stems, a laurel wreath round a crescent, five lines
    of raised lettering, rosette bolts in its corners, and an iron candle bracket beneath with a votive (Glow)."""
    K = kit(M)
    br, dk = K["bronze"], K["bronzedk"]
    W, H, z0 = 3.0, 2.4, 0.7
    box("Plate", (W, 0.12, H), (0, 0.06, z0 + H / 2), br, bevel=0.03)
    tube("Border", [(x, -0.02, z) for x, z in B21._rect(W / 2 - 0.12, H / 2 - 0.12, z0 + H / 2)], 0.035, dk, closed=True, square=True, poly=True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            foil(f"Bolt{sx}{sz}", sx * (W / 2 - 0.2), -0.03, z0 + H / 2 + sz * (H / 2 - 0.2), 0.08, dk, thick=0.02)
    zc = z0 + H - 0.55
    for k in range(14):
        a = math.pi * (0.1 + 0.8 * k / 13)
        for sx in (-1, 1):
            sphere(f"Laurel{sx}{k}", 0.06, (sx * math.cos(a) * 0.32 * -1, -0.04, zc - math.sin(a) * 0.32 + 0.12), br, seg=6, rings=4, scale=(1.4, 0.5, 0.7))
    tp("Moon", WS.crescent(0, zc + 0.02, 0.17, shift=0.4, tilt=math.pi / 2), -0.04, 0.04, dk)
    lines = ["IN MEMORY OF THE STUDENTS", "WHO WALKED INTO THE MIST", "ON THE NIGHT OF THE BLOOD MOON", "OCTOBER 1887", "THE VIGIL REMEMBERS"]
    for k, ln in enumerate(lines):
        text(f"Line{k}", ln, dk, 0, -0.01, z0 + H - 1.05 - k * 0.27, (W - 0.6, 0.15 if k < 4 else 0.12))
    zb = z0 - 0.45
    box("BracketPlate", (0.2, 0.04, 0.4), (0, 0.0, zb + 0.15), K["iron"], bevel=0.01)
    tube("BracketArm", [(0, -0.02, zb), (0, -0.25, zb + 0.02), (0, -0.38, zb + 0.1)], 0.03, K["iron"])
    lathe("Votive", [(0, 0), (0.14, 0), (0.16, 0.2), (0.12, 0.22), (0, 0.22)], flat("VotiveGlass41", (0.4, 0.04, 0.05), 0.15), seg=16,
          loc=(0, -0.38, zb + 0.1))
    set_group("Glow")
    flame("Flame", (0, -0.38, zb + 0.3), h=0.12)
    set_group("Main")
    to_wall()
    return _dims()


# ================================================================== gallery pieces

def easel_covered(M):
    """A tall studio easel holding a large canvas under a crimson velvet dust sheet; one corner is turned back to show a
    sliver of the gilt frame, a brass DO NOT UNVEIL tag hangs from the easel's tray."""
    K = kit(M)
    oak = K["oakdark"]
    for sx in (-1, 1):
        tube(f"Leg{sx}", [(sx * 1.1, -0.4, 0.0), (sx * 0.2, 0.0, 7.6)], 0.07, oak, square=True, poly=True)
    tube("BackLeg", [(0, 1.6, 0.0), (0, 0.15, 7.0)], 0.065, oak, square=True, poly=True)
    box("Tray", (2.4, 0.4, 0.1), (0, -0.33, 2.2), oak, bevel=0.02)
    box("TrayLip", (2.4, 0.06, 0.12), (0, -0.5, 2.28), oak, bevel=0.01)
    box("TopClamp", (0.5, 0.2, 0.18), (0, -0.05, 6.75), oak, bevel=0.02)
    for k in range(2):
        box(f"Brace{k}", (1.4 - k * 0.6, 0.06, 0.08), (0, -0.2 + k * 0.05, 1.0 + k * 3.7), oak, bevel=0.01)
    # the canvas in its frame (mostly hidden) and the sheet over it
    W, H = 3.2, 4.2
    zc = 2.3 + H / 2
    for sx in (-1, 1):
        box(f"FrameV{sx}", (0.22, 0.14, H + 0.2), (sx * W / 2, -0.25, zc), K["fgilt"], bevel=0.03)
    for sz in (-1, 1):
        box(f"FrameH{sz}", (W + 0.2, 0.14, 0.22), (0, -0.25, zc + sz * H / 2), K["fgilt"], bevel=0.03)
    box("CanvasBack", (W, 0.06, H), (0, -0.2, zc), flat("Linen41", (0.6, 0.54, 0.44), 0.9, dirt=0.6), bevel=0.01)
    rows = []
    nx, nz = 26, 26
    for j in range(nz + 1):
        t = j / nz
        row = []
        for i in range(nx + 1):
            u = -1 + 2 * i / nx
            x = u * (W / 2 + 0.25 + 0.35 * t)
            z = zc + H / 2 + 0.22 - t * (H + 0.6) - 0.2 * t * (1 - u * u)
            lift = 0.0
            if u > 0.55 and t > 0.72:          # the turned-back corner
                k = ((u - 0.55) / 0.45) * ((t - 0.72) / 0.28)
                z += k * 0.9
                lift = k * 0.35
            y = -0.38 - 0.06 * math.sin(u * 8 + 0.5) * (0.2 + 0.8 * t) - 0.08 * t - lift
            if t < 0.06:
                y = -0.38 + 0.25 * (0.06 - t) / 0.06 * 0 - 0.0
            row.append(Vector((x, y, z)))
        rows.append(row)
    _mesh("Sheet", rows, K["velvet"], 0.04)
    rows = []
    for j in range(5):
        t = j / 4
        rows.append([Vector((-W / 2 - 0.25 + (W + 0.5) * i / nx, -0.38 + 0.3 * t, zc + H / 2 + 0.22 + 0.06 * math.sin(t * math.pi))) for i in range(nx + 1)])
    _mesh("SheetTop", rows, K["velvet"], 0.04)
    tube("TagCord", [(0.8, -0.5, 2.25), (0.85, -0.53, 1.85)], 0.012, K["gilt"], poly=True)
    box("Tag", (0.4, 0.03, 0.22), (0.85, -0.54, 1.72), K["brass"], bevel=0.01)
    text("TagText", "DO NOT UNVEIL", K["ebony"], 0.85, -0.56, 1.72, (0.34, 0.07), depth=0.006)
    return _dims()


def stained_glass_roundel(M):
    """A leaded stained-glass roundel (the raven on the key under the crescent) in a cusped iron ring, hung on two chains
    from a scrolled wall bracket so it catches the light."""
    K = kit(M)
    ir = K["iron"]
    _, W, _H = LY.CANVAS["StainedGlassRoundel"]
    R_ = W / 2
    yc = -1.0
    zc = 0.5 + R_
    canvas_piece("Canvas", circ(0, zc, R_, 64), y=yc)
    tube("Ring", [(x, yc - 0.02, z) for x, z in circ(0, zc, R_ + 0.06, 64)], 0.09, ir, closed=True, poly=True)
    tube("RingBack", [(x, yc + 0.08, z) for x, z in circ(0, zc, R_ + 0.06, 64)], 0.06, ir, closed=True, poly=True)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        x, z = math.cos(a) * (R_ + 0.22), zc + math.sin(a) * (R_ + 0.22)
        foil(f"Cusp{k}", x, yc - 0.02, z, 0.12, ir, lobes=3, thick=0.025)
    zt = zc + R_ + 1.6
    box("WallPlate", (0.34, 0.05, 0.7), (0, 0.0, zt), ir, bevel=0.015)
    tube("Arm", [(0, -0.02, zt + 0.2), (0, yc * 0.6, zt + 0.25), (0, yc - 0.05, zt + 0.1)], 0.045, ir)
    tube("Strut", [(0, -0.02, zt - 0.3), (0, yc * 0.45, zt - 0.05), (0, yc * 0.8, zt + 0.18)], 0.03, ir)
    hoop("Curl", (0, -0.25, zt - 0.2), 0.1, "X", ir, thick=0.02)
    for sx in (-1, 1):
        chain(f"Chain{sx}", (0, yc - 0.05, zt + 0.05), (sx * R_ * 0.55, yc, zc + R_ * 0.85), ir, link=0.1)
    to_wall()
    return _dims()


def mosaic_raven(M):
    """An arched mosaic panel set in limestone: the moulded arch with a dentil band, a gilt key-pattern fillet round the
    tesserae, a sill on corbels."""
    K = kit(M)
    st, dk, gl = K["stone"], K["stonedark"], K["fgilt"]
    _, W, H = LY.CANVAS["MosaicRaven"]
    z0 = 0.6
    o = lancet(W / 2, z0, H, 14)
    canvas_piece("Canvas", o)
    B20.tprism("Surround", WS.ccw(B21._grow(o, 0.55)), 0.2, 0.36, st, bevel=0.02)
    tube("Moulding", [(x, -0.08, z) for x, z in B21._grow(o, 0.4)], 0.09, dk, poly=True)
    tube("Fillet", [(x, -0.03, z) for x, z in B21._grow(o, 0.1)], 0.05, gl, poly=True)
    arc = B21._grow(o, 0.25)
    for k in range(0, len(arc), 1):
        x, z = arc[k]
        if z > z0 + 0.1:
            box(f"Dentil{k}", (0.1, 0.1, 0.1), (x, -0.1, z), dk, bevel=0.01)
    box("Sill", (W + 1.4, 0.7, 0.24), (0, -0.2, z0 - 0.12), dk, bevel=0.03)
    for sx in (-1, 1):
        box(f"Corbel{sx}", (0.3, 0.5, 0.5), (sx * (W / 2 + 0.2), -0.1, z0 - 0.5), st, bevel=0.04)
    to_wall()
    return _dims()


def icon_triptych(M):
    """A small folding icon triptych for a table: a pointed centre panel and two wings opened at an angle, each painted
    saint in a silver riza of beaded borders, a crested gable with a cross, on a footed stand, a votive before it (Glow)."""
    K = kit(M)
    sv, eb = K["silver"], K["ebony"]
    _, cw, ch = LY.CANVAS["IconTriptych"]
    _, ww, wh = LY.CANVAS["IconTriptychL"]
    z0 = 0.35
    box("Stand", (2.6, 0.9, 0.12), (0, 0.1, 0.06), eb, bevel=0.02)
    box("Stand2", (2.4, 0.7, 0.18), (0, 0.1, 0.21), eb, bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sphere(f"Foot{sx}{sy}", 0.06, (sx * 1.15, 0.1 + sy * 0.35, 0.0), sv, seg=8, rings=4)
    o = lancet(cw / 2, z0, ch, 12)
    set_group("Canvas")
    B20.tprism("Centre", o, 0.02, 0.04, flat("CanvasTmp", (0.5, 0.5, 0.5), 0.5))
    set_group("Main")
    B21._frame("C", o, (eb, sv), widths=(0.08, 0.02, 0.025), back=0.08)
    for k, (x, z) in enumerate(B21._grow(o, 0.08)[::2]):
        sphere(f"CBead{k}", 0.025, (x, -0.1, z), sv, seg=6, rings=3)
    for side, grp, name in ((-1, "Canvas2", "IconTriptychL"), (1, "Canvas3", "IconTriptychR")):
        s = _mark()
        wo = [(side * (ww / 2) + x, z) for x, z in lancet(ww / 2, z0, wh, 10)]
        set_group(grp)
        B20.tprism(f"Wing{side}", wo, 0.02, 0.04, flat("CanvasTmp", (0.5, 0.5, 0.5), 0.5))
        set_group("Main")
        B21._frame(f"W{side}", wo, (eb, sv), widths=(0.07, 0.02, 0.02), back=0.07)
        for k in range(3):
            hoop(f"Hinge{side}{k}", (0, 0.05, z0 + 0.3 + k * 0.5), 0.03, "Z", sv, thick=0.012)
        _xform(s, Matrix.Translation((side * (cw / 2 + 0.12), 0.0, 0)) @ Matrix.Rotation(-side * math.radians(38), 4, "Z"))
    zt = z0 + ch + 0.12
    tp("Gable", [(-0.4, zt - 0.1), (0.4, zt - 0.1), (0, zt + 0.35)], -0.06, 0.1, sv, bevel=0.005)
    box("CrossV", (0.05, 0.05, 0.35), (0, -0.06, zt + 0.55), sv, bevel=0.01)
    box("CrossH", (0.22, 0.05, 0.05), (0, -0.06, zt + 0.6), sv, bevel=0.01)
    lathe("Votive", [(0, 0), (0.1, 0), (0.12, 0.16), (0.09, 0.18), (0, 0.18)], flat("VotiveGlass41", (0.4, 0.04, 0.05), 0.15), seg=16, loc=(0, -0.55, 0.3))
    set_group("Glow")
    flame("Flame", (0, -0.55, 0.47), h=0.1)
    set_group("Main")
    return _dims()


def death_mask_case(M):
    """A plaster death mask (the rig's own head, eyes closed, cast front-half) on a crimson velvet cushion under a glass
    case (Glass) with a brass frame, on a slender ebony pedestal with a brass label."""
    K = kit(M)
    eb, br = K["ebony"], K["brass"]
    lathe("Pedestal", [(0, 0), (0.8, 0), (0.82, 0.1), (0.6, 0.25), (0.35, 0.4), (0.3, 2.7), (0.45, 2.85), (0.75, 3.0), (0.78, 3.1), (0, 3.1)], eb, seg=8)
    hoop("PedBand", (0, 0, 1.5), 0.32, "Z", br, thick=0.025)
    box("LabelPlate", (0.5, 0.04, 0.16), (0, -0.33, 2.3), br, bevel=0.008)
    text("LabelText", "UNKNOWN STUDENT 1887", eb, 0, -0.35, 2.3, (0.44, 0.06), depth=0.006)
    zt = 3.1
    box("CaseBase", (1.7, 1.3, 0.16), (0, 0, zt + 0.08), eb, bevel=0.02)
    box("Cushion", (1.3, 0.9, 0.22), (0, 0, zt + 0.27), K["velvet"], bevel=0.08, segments=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f"Post{sx}{sy}", (0.05, 0.05, 1.2), (sx * 0.8, sy * 0.6, zt + 0.76), br, bevel=0.01)
            sphere(f"PostKnop{sx}{sy}", 0.05, (sx * 0.8, sy * 0.6, zt + 1.4), br, seg=8, rings=4)
    for sz in (zt + 0.17, zt + 1.36):
        tube(f"Rail{sz:.1f}", [(-0.8, -0.6, sz), (0.8, -0.6, sz), (0.8, 0.6, sz), (-0.8, 0.6, sz)], 0.025, br, closed=True, square=True, poly=True)
    set_group("Glass")
    box("Glass", (1.6, 1.2, 1.18), (0, 0, zt + 0.76), flat("GlassTmp", (0.8, 0.85, 0.9), 0.05), bevel=0.0)
    set_group("Main")
    s = _mark()
    f = R.Fig(base=(0, 0, 0), scale=0.48, pose={}, mats=K["plaster"], parts=("head",), face="sorrow", dark=K["plaster"])
    for ob in P.PARTS[s:]:
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix.Identity(4)
        for v in ob.data.vertices:
            v.co.y = min(v.co.y, 0.04)
        ob.data.update()
    _xform(s, Matrix.Translation((0, 0.05, zt + 0.42)) @ Matrix.Rotation(math.radians(-72), 4, "X") @ Matrix.Translation((0, 0, -4.5 * 0.48)))
    return _dims()


# ================================================================== registration

BUILDERS = {
    "PortraitHeadmasterGallery": portrait_headmaster_gallery,
    "PortraitHeadmistress": portrait_headmistress,
    "PortraitCursedStudent": portrait_cursed_student,
    "PortraitCountessOval": portrait_countess_oval,
    "PaintingVampireBall": painting_vampire_ball,
    "PaintingWolfHuntSnow": painting_wolf_hunt_snow,
    "TondoMoonCloister": tondo_moon_cloister,
    "PaintingAcademyPanorama": painting_academy_panorama,
    "PaintingClassOf1887": painting_class_1887,
    "CliqueHeraldry": clique_heraldry,
    "PortraitMiniatures": portrait_miniatures,
    "TapestryCliques": tapestry_cliques,
    "TapestryProcession": tapestry_procession,
    "BannerPack": banner_pack,
    "BannerChoir": banner_choir,
    "BannerInk": banner_ink,
    "GonfalonStand": gonfalon_stand,
    "BustHeadmistress": bust_headmistress,
    "BustVampireCount": bust_vampire_count,
    "BustVeiledStudent": bust_veiled_student,
    "StatueChoirChild": statue_choir_child,
    "StatueInkScribe": statue_ink_scribe,
    "StatueCourtDuchess": statue_court_duchess,
    "SculptureClaspedHands": sculpture_clasped_hands,
    "ReliefFounding": relief_founding,
    "ReliefDanseMacabre": relief_danse_macabre,
    "PlaqueMemorial": plaque_memorial,
    "EaselCovered": easel_covered,
    "StainedGlassRoundel": stained_glass_roundel,
    "MosaicRaven": mosaic_raven,
    "IconTriptych": icon_triptych,
    "DeathMaskCase": death_mask_case,
}

for _n in ("PortraitHeadmasterGallery", "PortraitHeadmistress", "PortraitCursedStudent", "PortraitCountessOval", "PaintingVampireBall",
           "PaintingWolfHuntSnow", "TondoMoonCloister", "PaintingAcademyPanorama", "PaintingClassOf1887", "CliqueHeraldry", "StainedGlassRoundel",
           "MosaicRaven", "PortraitMiniatures", "IconTriptych"):
    P.CANVAS[f"{_n}_Canvas"] = _n
P.CANVAS["IconTriptych_Canvas2"] = "IconTriptychL"
P.CANVAS["IconTriptych_Canvas3"] = "IconTriptychR"

# where each wall piece's bottom goes on the showcase wall (studs above the floor), and the pieces that stand on a plinth
WALL = {"PortraitHeadmasterGallery": 1.0, "PortraitHeadmistress": 4.0, "PortraitCursedStudent": 4.0, "PortraitCountessOval": 4.0,
        "PaintingVampireBall": 3.5, "PaintingWolfHuntSnow": 3.0, "TondoMoonCloister": 4.0, "PaintingAcademyPanorama": 5.5,
        "PaintingClassOf1887": 4.0, "CliqueHeraldry": 4.0, "PortraitMiniatures": 4.0, "TapestryCliques": 1.5, "TapestryProcession": 2.5,
        "BannerPack": 3.0, "BannerChoir": 2.5, "BannerInk": 3.0, "ReliefFounding": 3.0, "ReliefDanseMacabre": 5.0, "PlaqueMemorial": 4.5,
        "StainedGlassRoundel": 4.5, "MosaicRaven": 3.0}
PLINTH = ["BustHeadmistress", "BustVampireCount", "BustVeiledStudent", "IconTriptych"]

P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({n: 1.1 for n in BUILDERS})
P.PREVIEW_PAD.update({"PaintingAcademyPanorama": 1.0, "TapestryProcession": 1.0, "ReliefDanseMacabre": 1.0, "BustHeadmistress": 1.35,
                      "BustVampireCount": 1.35, "BustVeiledStudent": 1.35, "IconTriptych": 1.3})
