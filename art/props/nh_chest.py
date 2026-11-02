"""Nightmare Highschool Gear Chest (Blender 5.x, headless). Uses the props pipeline (nh_props.py).

usage:
  "E:/Blender/blender.exe" --background --factory-startup --python art/props/nh_chest.py -- GearChest [--size 1024] [--samples 64]

A gothic school footlocker: dark oak body with wrought-iron straps, corner brackets and brass rivets, a brass
lock plate with a crimson quatrefoil, ring handles, and a crimson-velvet lining. The barrel lid is its own
mesh ("GearChest_Lid") with its origin on the back hinge line, so Roblox can swing it open about X.
Output: art/props/fbx/GearChest.fbx, textures/GearChest_*.png, previews/GearChest.png (+ _open).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nh_props as P  # noqa: E402  (its __main__ guard keeps it from running)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

W, D, H = 4.0, 2.4, 1.6       # body width (X), depth (Y), height (Z) in studs
BASE = 0.14                   # feet height
LID_H = 0.75                  # barrel rise


def end_cap(name, x, prof, thick, mat):
    """a solid slab with the lid's half-ellipse profile (closes the barrel ends)"""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    a = [bm.verts.new((x - thick / 2, y, z)) for (y, z) in prof]
    b = [bm.verts.new((x + thick / 2, y, z)) for (y, z) in prof]
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    for i in range(len(prof)):
        j = (i + 1) % len(prof)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return P._finish(ob, mat, 0.02)


def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=max(6, seg // 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return P._finish(ob, mat, 0.0)


def contents(M, floor, velvet):
    """loot on the velvet: skull, tomes, scrolls, candle, dagger, coins, vial, crucifix, bone (all below the rim)"""
    bone = P.material("Bone", base=(0.80, 0.74, 0.62), rough=0.7, wear=0.4, dirt=0.9)
    wax = P.material("Wax", base=(0.86, 0.80, 0.66), rough=0.55, wear=0.0, dirt=0.5)
    steel, brass, paper = M["brasssteel"], M["brass"], M["paper"]
    leather, ink, crim = M["leatherdark"], M["inkblue"], M["crimson"]
    z = floor
    # an R6-style skull (back left): a rounded cylinder head, sockets and nose on the flat front, a square jaw
    sx0, sy0 = -1.05, 0.3
    P.cyl("Skull", 0.3, 0.42, (sx0, sy0, z + 0.33), bone, verts=28, bevel=0.11)
    P.box("Jaw", (0.38, 0.3, 0.14), (sx0, sy0 - 0.06, z + 0.07), bone, bevel=0.05)
    for k in range(5):  # teeth
        P.box(f"Tooth{k}", (0.05, 0.03, 0.06), (sx0 - 0.12 + k * 0.06, sy0 - 0.215, z + 0.15), bone, bevel=0.01)
    for sx in (-1, 1):
        sphere(f"Socket{sx}", 0.075, (sx0 + sx * 0.11, sy0 - 0.27, z + 0.38), M["glass"], scale=(1.0, 0.5, 1.15), seg=12)
    P.box("Nose", (0.07, 0.04, 0.09), (sx0, sy0 - 0.29, z + 0.25), M["glass"], bevel=0.015, rot=(0, math.radians(45), 0))
    # stack of three old tomes (back right)
    for k, (mat, w, d) in enumerate(((leather, 0.9, 0.62), (ink, 0.8, 0.56), (crim, 0.74, 0.5))):
        h = 0.14
        zz = z + h / 2 + k * h
        P.box(f"Tome{k}", (w, d, h), (0.9, 0.35, zz), mat, bevel=0.025, rot=(0, 0, math.radians(8 - k * 9)))
        P.box(f"Pages{k}", (w - 0.06, d - 0.06, h - 0.04), (0.9 + 0.02, 0.35 - 0.02, zz), paper, bevel=0.01, rot=(0, 0, math.radians(8 - k * 9)))
    P.box("Clasp", (0.06, 0.08, 0.2), (0.9, 0.35 - 0.33, z + 0.36), brass, bevel=0.01)
    # two sealed scrolls (front left)
    for k in range(2):
        x, y = -0.55 + k * 0.32, -0.45 + k * 0.08
        P.cyl(f"Scroll{k}", 0.08, 0.95, (x, y, z + 0.08), paper, rot=(0, math.pi / 2, math.radians(70 - k * 25)), verts=14, bevel=0.01)
        P.cyl(f"Ribbon{k}", 0.088, 0.06, (x, y, z + 0.08), crim, rot=(0, math.pi / 2, math.radians(70 - k * 25)), verts=14, bevel=0.0)
    # candle stub in a brass dish (centre back)
    P.cyl("Dish", 0.2, 0.04, (0.05, 0.55, z + 0.02), brass, verts=18, bevel=0.01)
    P.cyl("Candle", 0.08, 0.32, (0.05, 0.55, z + 0.2), wax, verts=14, bevel=0.01)
    P.cyl("Wick", 0.01, 0.06, (0.05, 0.55, z + 0.39), M["glass"], verts=6, bevel=0.0)
    # ornate dagger across the front
    P.box("Blade", (0.85, 0.11, 0.025), (0.45, -0.5, z + 0.06), steel, bevel=0.01, rot=(0, 0, math.radians(-12)))
    P.box("Guard", (0.06, 0.34, 0.06), (0.01, -0.41, z + 0.06), brass, bevel=0.015, rot=(0, 0, math.radians(-12)))
    P.cyl("Grip", 0.04, 0.3, (-0.15, -0.37, z + 0.06), leather, rot=(0, math.pi / 2, math.radians(-12)), verts=10, bevel=0.005)
    sphere("Pommel", 0.055, (-0.31, -0.34, z + 0.06), brass, seg=10)
    # a spill of brass coins
    import random as _r
    rr = _r.Random(11)
    for k in range(16):
        x, y = rr.uniform(-0.25, 0.45), rr.uniform(-0.15, 0.25)
        P.cyl(f"Coin{k}", 0.07, 0.02, (x, y, z + 0.012 + (k % 4) * 0.018), brass, rot=(rr.uniform(-0.3, 0.3), rr.uniform(-0.3, 0.3), 0), verts=12, bevel=0.004)
    # crimson vial with a cork, leaning on the tomes
    P.cyl("Vial", 0.07, 0.3, (0.42, 0.62, z + 0.16), M["glassamber"], rot=(math.radians(12), 0, 0), verts=12, bevel=0.01)
    P.cyl("Potion", 0.06, 0.18, (0.42, 0.615, z + 0.12), crim, rot=(math.radians(12), 0, 0), verts=12, bevel=0.0)
    P.cyl("Cork", 0.045, 0.06, (0.42, 0.65, z + 0.33), M["oak"], rot=(math.radians(12), 0, 0), verts=8, bevel=0.005)
    # brass crucifix lying flat (front right) and a bone
    P.box("CrossLong", (0.07, 0.5, 0.04), (1.25, -0.42, z + 0.02), brass, bevel=0.012)
    P.box("CrossBar", (0.3, 0.07, 0.04), (1.25, -0.32, z + 0.02), brass, bevel=0.012)
    P.cyl("BoneShaft", 0.035, 0.5, (-1.35, -0.25, z + 0.04), bone, rot=(0, math.pi / 2, math.radians(30)), verts=10, bevel=0.005)
    for sx in (-1, 1):
        sphere(f"BoneEnd{sx}", 0.06, (-1.35 + sx * 0.22 * math.cos(math.radians(30)), -0.25 + sx * 0.22 * math.sin(math.radians(30)), z + 0.05), bone, seg=10)


def gear_chest(M):
    oak = P.material("ChestOak", "NH_DeskWood", tint=(0.16, 0.085, 0.05), scale=0.22, rough_add=0.08, wear=0.5)
    dark = P.material("ChestOakDark", "NH_DeskWood", tint=(0.075, 0.04, 0.025), scale=0.22, rough_add=0.1, wear=0.55)
    iron, brass, crim = M["iron"], M["brass"], M["crimson"]
    velvet = P.material("Velvet", "NH_Leather", tint=(0.20, 0.02, 0.035), scale=2.4, normal=0.3, rough_add=0.25, wear=0.1)
    top = BASE + H
    P.set_group("Main")
    # feet: brass claw blocks
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.box(f"Foot{sx}{sy}", (0.34, 0.34, BASE), (sx * (W / 2 - 0.2), sy * (D / 2 - 0.2), BASE / 2), brass, bevel=0.04)
    # body + plank trims
    WT = 0.14
    zc = BASE + H / 2
    P.box("Floor", (W, D, 0.16), (0, 0, BASE + 0.08), dark, bevel=0.03)
    for sy in (-1, 1):
        P.box(f"WallY{sy}", (W, WT, H), (0, sy * (D / 2 - WT / 2), zc), dark, bevel=0.04, segments=3)
    for sx in (-1, 1):
        P.box(f"WallX{sx}", (WT, D - 2 * WT, H), (sx * (W / 2 - WT / 2), 0, zc), dark, bevel=0.04, segments=3)
    # crimson velvet lining
    # a raised velvet bed (the chest reads as full) with the loot heaped on it
    bed = top - 0.5
    P.box("VelvetFloor", (W - 2 * WT - 0.02, D - 2 * WT - 0.02, bed - BASE - 0.16), (0, 0, (bed + BASE + 0.16) / 2), velvet, bevel=0.03)
    contents(M, bed, velvet)
    for sy in (-1, 1):
        P.box(f"VelvetY{sy}", (W - 2 * WT - 0.02, 0.03, H - 0.3), (0, sy * (D / 2 - WT - 0.015), zc + 0.05), velvet, bevel=0.0)
    for sx in (-1, 1):
        P.box(f"VelvetX{sx}", (0.03, D - 2 * WT - 0.02, H - 0.3), (sx * (W / 2 - WT - 0.015), 0, zc + 0.05), velvet, bevel=0.0)
    P.box("TrimBottom", (W + 0.06, D + 0.06, 0.16), (0, 0, BASE + 0.12), oak, bevel=0.03)
    # the top trim is a frame (four boards), so the opening stays open
    tz = top - 0.08
    for sy in (-1, 1):
        P.box(f"TrimTopY{sy}", (W + 0.06, 0.2, 0.16), (0, sy * (D / 2 - 0.07), tz), oak, bevel=0.03)
    for sx in (-1, 1):
        P.box(f"TrimTopX{sx}", (0.2, D - 0.2, 0.16), (sx * (W / 2 - 0.07), 0, tz), oak, bevel=0.03)
    for i in range(1, 4):  # plank seams across the front and back
        z = BASE + H * i / 4
        for sy in (-1, 1):
            P.box(f"Seam{i}{sy}", (W - 0.3, 0.02, 0.025), (0, sy * (D / 2 + 0.005), z), M["iron"], bevel=0.0)
    # inner velvet (seen when the lid is open)
    # iron straps wrapping front-top-back at x = +-1.15
    for sx in (-1, 1):
        x = sx * 1.15
        for sy in (-1, 1):
            P.box(f"StrapV{sx}{sy}", (0.2, 0.05, H + 0.02), (x, sy * (D / 2 + 0.025), BASE + H / 2), iron, bevel=0.012)
        P.box(f"StrapBot{sx}", (0.2, D + 0.1, 0.05), (x, 0, BASE + 0.02), iron, bevel=0.012)
        for k in range(4):  # rivets
            z = BASE + 0.25 + k * (H - 0.5) / 3
            for sy in (-1, 1):
                P.cyl(f"Rivet{sx}{sy}{k}", 0.045, 0.04, (x, sy * (D / 2 + 0.055), z), brass, rot=(math.pi / 2, 0, 0), verts=10, bevel=0.008)
    # corner brackets (L plates on the 8 corners)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (BASE + 0.22, top - 0.22):
                P.box(f"CornX{sx}{sy}{z:.1f}", (0.36, 0.05, 0.4), (sx * (W / 2 - 0.17), sy * (D / 2 + 0.028), z), iron, bevel=0.012)
                P.box(f"CornY{sx}{sy}{z:.1f}", (0.05, 0.36, 0.4), (sx * (W / 2 + 0.028), sy * (D / 2 - 0.17), z), iron, bevel=0.012)
    # ring handles on the ends
    for sx in (-1, 1):
        x = sx * (W / 2 + 0.06)
        P.box(f"HandlePlate{sx}", (0.05, 0.46, 0.3), (x, 0, BASE + H * 0.62), iron, bevel=0.012)
        pts = [(x + sx * 0.05, -0.2, BASE + H * 0.62), (x + sx * 0.16, -0.18, BASE + H * 0.45),
               (x + sx * 0.2, 0.0, BASE + H * 0.38), (x + sx * 0.16, 0.18, BASE + H * 0.45), (x + sx * 0.05, 0.2, BASE + H * 0.62)]
        P.tube(f"Ring{sx}", pts, 0.035, iron)
    # lock plate + keyhole + quatrefoil on the front
    fy = -(D / 2 + 0.04)
    P.box("LockPlate", (0.62, 0.05, 0.72), (0, fy, top - 0.42), brass, bevel=0.02)
    P.box("Keyhole", (0.08, 0.02, 0.2), (0, fy - 0.03, top - 0.55), M["glass"], bevel=0.0)
    P._quatrefoil("Foil", 0, fy - 0.035, top - 0.27, 0.11, crim)

    # the lid: a barrel arc, hinged at the back top edge
    P.set_group("Lid", hinge=(0, D / 2, top), swing=1)
    N = 10
    pts = []
    for i in range(N + 1):
        t = math.pi * i / N
        pts.append((-math.cos(t) * D / 2, top + math.sin(t) * LID_H))   # (y, z), front (-y) to back (+y)
    for i in range(N):
        (y0, z0), (y1, z1) = pts[i], pts[i + 1]
        cy, cz = (y0 + y1) / 2, (z0 + z1) / 2
        ln = math.hypot(y1 - y0, z1 - z0)
        ang = math.atan2(z1 - z0, y1 - y0)
        P.box(f"Slat{i}", (W, ln + 0.02, 0.1), (0, cy, cz), dark, bevel=0.02, rot=(ang, 0, 0))
        P.box(f"LidVelvet{i}", (W - 0.3, ln, 0.02), (0, cy + math.sin(ang) * 0.06, cz - math.cos(ang) * 0.06), velvet, bevel=0.0, rot=(ang, 0, 0))
        # crimson leather panel between the straps on each slat
        P.box(f"Panel{i}", (1.9, ln - 0.04, 0.02), (0, cy - math.sin(ang) * 0.055, cz + math.cos(ang) * 0.055), M["leatherdark"], bevel=0.0, rot=(ang, 0, 0))
        for sx in (-1, 1):
            P.box(f"LidStrap{sx}{i}", (0.2, ln + 0.03, 0.04), (sx * 1.15, cy - math.sin(ang) * 0.06, cz + math.cos(ang) * 0.06), iron, bevel=0.01, rot=(ang, 0, 0))
            if i % 3 == 1:
                P.cyl(f"LidRivet{sx}{i}", 0.045, 0.04, (sx * 1.15, cy - math.sin(ang) * 0.085, cz + math.cos(ang) * 0.085), brass, rot=(ang + math.pi / 2, 0, 0), verts=10, bevel=0.008)
    # lid end caps (oak half-ellipses) + brass rim on the front edge + hasp
    for sx in (-1, 1):
        end_cap(f"Cap{sx}", sx * (W / 2 - 0.02), pts, 0.12, oak)
        prof = [(sx * (W / 2 + 0.03), y, z) for (y, z) in pts]
        P.tube(f"CapRim{sx}", prof, 0.04, iron, square=True)
    P.box("Rim", (W + 0.04, 0.1, 0.12), (0, -D / 2 - 0.02, top + 0.06), brass, bevel=0.02)
    P.box("Hasp", (0.3, 0.05, 0.36), (0, -D / 2 - 0.06, top - 0.04), brass, bevel=0.015)
    return (W + 0.5, D + 0.3, top + LID_H + 0.1)


def run():
    P.PARTS, P.GROUP, P.HINGES = [], "Main", {}
    P.reset()
    M = P.palette()
    dims = gear_chest(M)
    objs = P.join_parts("GearChest")
    P.bake_uv(objs)
    imgs = P.bake_all(objs, "GearChest")
    P.final_material(objs, "GearChest", imgs)
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    P.export(objs, "GearChest")
    # the pipeline's door preview swings about Z; a chest lid swings about X, so clear the swing first
    for o in objs:
        if "nh_swing" in o.keys():
            del o["nh_swing"]
    P.preview(objs, "GearChest", dims)
    lid = [o for o in objs if o.name.endswith("_Lid")]
    for o in lid:
        o.rotation_euler[0] = math.radians(-70)   # hinge at the back: negative X tips the front up
    bpy.context.scene.render.filepath = os.path.join(P.OUT_PRE, "GearChest_open.png")
    bpy.ops.render.render(write_still=True)
    print(f"[props] GearChest: {tris} tris, pieces {[o.name for o in objs]}, dims {dims}")


if __name__ == "__main__":
    run()
