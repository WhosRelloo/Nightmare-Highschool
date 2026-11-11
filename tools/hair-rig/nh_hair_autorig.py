"""Auto-rig the owner's catalog hairs (exported from Studio as OBJ) so their locks sway (Blender 5.x, headless).

usage:
  "E:/Blender/blender.exe" --background --factory-startup --python tools/hair-rig/nh_hair_autorig.py -- <export.obj|folder> <outdir> [preview]
A folder is searched recursively for .obj files (one hair per file, e.g. "Hair OBJ's/Males/Short.obj" -> Males_Short.fbx).
Each hair is re-centred on its bounding-box centre (where Roblox centres a MeshPart), so the rigged mesh drops into
the original Handle's CFrame unchanged; rig_report.json lists every hair's original size.

For every hair mesh in the OBJ:
  1. the roots never move: the crown (top ~35% of the hair's height, where it meets the scalp) is weighted
     100% to HairRoot, and the lock bones fade in smoothly below it (0 at the root line -> full by ~30% down
     the lock), so only the hanging ends sway; each chain pivots exactly on the root line
  2. the hanging part is clustered into locks by angle around the head (k-means, 3-10 locks by size)
  3. each lock gets a bone chain down its centreline (3-5 bones), parented to HairRoot
  4. every vertex is weighted along its lock by height, blended with the neighbouring lock by angle
     (smooth deformation, no tearing between locks), crown -> HairRoot
UVs are untouched, so the original catalog texture (TextureID) still fits after re-import.

Weights v2 (2026-11-11, for the accessories' hair tuck): the locks carry their strands, so a lock can be bent to lie
over a coat's collar, under a hat's brim or round a mask (Config.Accessories, NHHairTuck). The bones are unchanged
(same chains, names and rest positions as v1); only the weights differ:
  * each vertex follows its nearest lock chain (distance to the chain's bones, not its angle round the head),
    blended with the second nearest, and along the chain by where it lies on it
  * HairRoot holds what is above a lock's start (the crown) and fades out over the first 0.16 of the lock, and
    what lies far from every chain
  * the weights are smoothed over the mesh's edges, so each strand card bends as one piece
Pass "v1" after the out folder (and before "preview") for the old weights.
Writes <outdir>/<HairName>.fbx (armature + skinned mesh) and <outdir>/rig_report.txt.
Controllers.Character.HairSway animates any hair whose Handle has bones.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
V1 = "v1" in argv
if V1:
    argv.remove("v1")
SRC = argv[0] if argv else "hair_export.obj"
OUT = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(SRC), "rigged")
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def kmeans_angles(angles, k, iters=30):
    """1-D k-means on a circle (angles in radians)"""
    centres = [(-math.pi + (i + 0.5) * 2 * math.pi / k) for i in range(k)]
    def d(a, b):
        x = abs(a - b) % (2 * math.pi)
        return min(x, 2 * math.pi - x)
    for _ in range(iters):
        groups = [[] for _ in range(k)]
        for i, a in enumerate(angles):
            j = min(range(k), key=lambda c: d(a, centres[c]))
            groups[j].append(a)
        for j, g in enumerate(groups):
            if g:
                s = sum(math.sin(a) for a in g)
                c = sum(math.cos(a) for a in g)
                centres[j] = math.atan2(s, c)
    return centres


HEAD_HALF = 0.6     # R6 head: 1.2 studs cube (owner's R6 reference rig in Blender), HairAttachment at +0.6


def load_heads():
    """heads.txt (exported from Studio): the head centre each hair was fitted to, in Studio world studs"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heads.txt")
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("#") or "|" not in line:
                continue
            n, h, _ = line.strip().split("|")
            x, y, z = (float(t) for t in h.split(","))
            out.append((n, Vector((x, -z, y))))   # Studio (Y up) -> Blender (Z up), same as the OBJ importer
    return out


HEADS = load_heads()


def head_box_dist(v, hc):
    """distance from v to the R6 head (rounded 1.2 box), 0 inside"""
    d = Vector((max(abs(v.x - hc.x) - HEAD_HALF, 0), max(abs(v.y - hc.y) - HEAD_HALF, 0), max(abs(v.z - hc.z) - HEAD_HALF, 0)))
    return d.length


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rig(ob, report, head=None):
    me = ob.data
    vs = [ob.matrix_world @ v.co for v in me.vertices]
    if not vs:
        return None
    xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
    zmin, zmax = min(zs), max(zs)
    H = max(zmax - zmin, 1e-3)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    crown_z = zmax - H * 0.35
    if head is not None:
        # root line = the scalp: just above the head's mid-line, so the cap that sits on the skull stays fixed
        crown_z = min(zmax - H * 0.15, head.z + 0.1)
    hanging = [i for i, v in enumerate(vs) if v.z < crown_z]
    if len(hanging) < 20 or H < 0.6:
        report.append(f"{ob.name}: short hair (h={H:.2f}), crown-only rig")
    k = max(3, min(10, int(len(hanging) / 220) + 3)) if hanging else 0
    ang = {i: math.atan2(vs[i].x - cx, -(vs[i].y - cy)) for i in hanging}
    centres = kmeans_angles([ang[i] for i in hanging], k) if k else []

    def adist(a, b):
        x = abs(a - b) % (2 * math.pi)
        return min(x, 2 * math.pi - x)

    # chain per lock: centreline from the crown line down to its lowest vertex
    locks = []
    for j, c in enumerate(centres):
        members = [i for i in hanging if min(range(k), key=lambda q: adist(ang[i], centres[q])) == j]
        if len(members) < 8:
            continue
        lo = min(vs[i].z for i in members)
        span = crown_z - lo
        nb = 3 if span < 0.8 else (4 if span < 1.6 else 5)
        pts = []
        for b in range(nb + 1):
            z = crown_z - span * b / nb
            band = [vs[i] for i in members if abs(vs[i].z - z) < span / (nb * 1.6)]
            if not band:
                band = sorted((vs[i] for i in members), key=lambda v: abs(v.z - z))[:6]
            p = sum(band, Vector()) / len(band)
            pts.append(p)
        locks.append(dict(angle=c, pts=pts, lo=lo, span=span, members=set(members)))
    # armature
    arm = bpy.data.armatures.new(ob.name + "_Rig")
    ao = bpy.data.objects.new(ob.name + "_Rig", arm)
    bpy.context.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm.edit_bones.new("HairRoot")
    root.head = Vector((cx, cy, crown_z))
    root.tail = Vector((cx, cy, zmax))
    for n, L in enumerate(locks):
        prev = root
        L["bones"] = []
        for b in range(len(L["pts"]) - 1):
            e = arm.edit_bones.new(f"Lock{n + 1}_{b + 1}")
            e.head, e.tail = L["pts"][b], L["pts"][b + 1]
            if (e.tail - e.head).length < 1e-3:
                e.tail = e.head + Vector((0, 0, -0.05))
            e.parent = prev
            prev = e
            L["bones"].append(e.name)
    bpy.ops.object.mode_set(mode="OBJECT")
    if V1:
        weights_v1(ob, vs, locks, crown_z, head, adist)
    else:
        weights_v2(ob, ao, vs, locks)
    if not V1:
        smooth_weights(ob, 12)
    ob.parent = ao
    md = ob.modifiers.new("Armature", "ARMATURE")
    md.object = ao
    report.append(f"{ob.name[5:]}: height {H:.2f}, {len(locks)} locks, {sum(len(L['bones']) for L in locks) + 1} bones, {len(me.vertices)} verts")
    return ao


def weights_v1(ob, vs, locks, crown_z, head, adist):
    """v1: by angle round the head, pinned crown and skull"""
    vg_root = ob.vertex_groups.new(name="HairRoot")
    vgs = {}
    for L in locks:
        for b in L["bones"]:
            vgs[b] = ob.vertex_groups.new(name=b)
    for i, v in enumerate(vs):
        if v.z >= crown_z or not locks:
            vg_root.add([i], 1.0, "REPLACE")
            continue
        a = math.atan2(v.x - cx, -(v.y - cy))
        order = sorted(locks, key=lambda L: adist(a, L["angle"]))
        near = order[:2]
        da = [adist(a, L["angle"]) for L in near]
        wl = [1.0, 0.0] if len(near) == 1 or da[0] < 1e-4 else [da[1] / (da[0] + da[1]), da[0] / (da[0] + da[1])]
        wl = [w ** 1.5 for w in wl]
        s = sum(wl)
        wl = [w / s for w in wl]
        # pinned roots: rigid at the root line, lock bones fade in over the first ~30% of the lock (smoothstep)
        span0 = max(near[0]["span"], 1e-3)
        r = min(1.0, max(0.0, (crown_z - v.z) / (span0 * (0.3 if V1 else 0.12))))
        blend_root = 1 - r * r * (3 - 2 * r)
        if head is not None:
            # hair lying on the skull (sides, nape) is pinned too: it only frees up once it leaves the scalp
            hug = smooth((head_box_dist(v, head) - 0.05) / 0.22) if V1 else smooth((head_box_dist(v, head) - 0.03) / 0.15)
            below = smooth((head.z - HEAD_HALF + 0.1 - v.z) / 0.3)      # below the jaw: nothing to lie on
            blend_root = 1 - (1 - blend_root) * max(hug, below)
        for L, w in zip(near, wl):
            if w < 0.02:
                continue
            t = min(1.0, max(0.0, (crown_z - v.z) / max(L["span"], 1e-3)))
            f = t * len(L["bones"])
            bi = min(int(f), len(L["bones"]) - 1)
            fr = f - bi
            vgs[L["bones"][bi]].add([i], w * (1 - fr) * (1 - blend_root), "ADD")
            if bi + 1 < len(L["bones"]):
                vgs[L["bones"][bi + 1]].add([i], w * fr * (1 - blend_root), "ADD")
        if blend_root > 0:
            vg_root.add([i], blend_root, "ADD")


def weights_v2(ob, ao, vs, locks):
    """v2: each vertex follows its nearest lock chain (by distance), the crown stays on HairRoot"""
    vg_root = ob.vertex_groups.new(name="HairRoot")
    vgs = {}
    chains = []
    for L in locks:
        segs = []
        for b in L["bones"]:
            vgs[b] = ob.vertex_groups.new(name=b)
            eb = ao.data.bones[b]
            segs.append((b, ao.matrix_world @ eb.head_local, ao.matrix_world @ eb.tail_local))
        chains.append(segs)
    for i, v in enumerate(vs):
        if not chains:
            vg_root.add([i], 1.0, "REPLACE")
            continue
        best = []
        for segs in chains:
            dmin, arc, acc, bi_best, f_best, t0 = 9.0, 0.0, 0.0, 0, 0.0, 0.0
            for bi, (b, h, t) in enumerate(segs):
                ab = t - h
                L2 = max(ab.length_squared, 1e-9)
                tt = (v - h).dot(ab) / L2
                if bi == 0:
                    t0 = tt
                f = min(1.0, max(0.0, tt))
                d = (v - (h + ab * f)).length
                if d < dmin:
                    dmin, arc, bi_best, f_best = d, acc + f * ab.length, bi, f
                acc += ab.length
            if t0 < 0:
                arc = 0.0
            best.append((dmin, arc, bi_best, f_best, segs))
        best.sort(key=lambda x: x[0])
        near = best[:2]
        inv = [1.0 / max(x[0], 1e-3) ** 4 for x in near]
        tot = sum(inv)
        root = 0.0
        for (d, arc, bi, f, segs), w in zip(near, inv):
            share = w / tot
            if share < 0.15:
                root += share
                continue
            r = min(1.0, max(0.0, arc / 0.16))
            far = min(1.0, max(0.0, 1 - (d - 0.30) / 0.30))
            lw = share * r * far
            root += share - lw
            if lw <= 0:
                continue
            names = [x[0] for x in segs]
            if f > 0.5 and bi + 1 < len(names):
                k = f - 0.5
                vgs[names[bi]].add([i], lw * (1 - k), "ADD")
                vgs[names[bi + 1]].add([i], lw * k, "ADD")
            elif f < 0.5 and bi > 0:
                k = 0.5 - f
                vgs[names[bi]].add([i], lw * (1 - k), "ADD")
                vgs[names[bi - 1]].add([i], lw * k, "ADD")
            else:
                vgs[names[bi]].add([i], lw, "ADD")
        if root > 0:
            vg_root.add([i], root, "ADD")


def smooth_weights(ob, iters):
    """average each vertex's weights with its edge neighbours (half its own), keep the 4 largest, normalise"""
    me = ob.data
    n = len(me.vertices)
    names = {g.index: g.name for g in ob.vertex_groups}
    W = [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in me.vertices]
    nb = [[] for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    for _ in range(iters):
        new = []
        for i in range(n):
            if not nb[i]:
                new.append(W[i])
                continue
            acc = {k: x * 0.5 for k, x in W[i].items()}
            sh = 0.5 / len(nb[i])
            for j in nb[i]:
                for k, x in W[j].items():
                    acc[k] = acc.get(k, 0) + x * sh
            new.append(acc)
        W = new
    groups = {g.name: g for g in ob.vertex_groups}
    for g in ob.vertex_groups:
        g.remove(list(range(n)))
    for i, w in enumerate(W):
        top = sorted(w.items(), key=lambda t: -t[1])[:4]
        tot = sum(t[1] for t in top) or 1.0
        for k, x in top:
            groups[k].add([i], x / tot, "REPLACE")


def safe_name(n):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in n)[:60]


def preview(ob, ao, path):
    """bend every lock bone and render front + side over a wireframe of the rest pose: roots must line up"""
    scn = bpy.context.scene
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode="POSE")
    for pb in ao.pose.bones:
        if pb.name != "HairRoot":
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0.3, 0, 0.1)
    bpy.ops.object.mode_set(mode="OBJECT")
    mat = bpy.data.materials.new("prev")
    mat.diffuse_color = (0.55, 0.35, 0.25, 1)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ghost = ob.copy()
    ghost.data = ob.data.copy()
    ghost.modifiers.clear()
    ghost.parent = None
    ghost.matrix_world = ob.matrix_world.copy()
    ghost.display_type = "WIRE"
    ghost.show_in_front = True
    scn.collection.objects.link(ghost)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scn.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 3.4
    scn.camera = cam
    scn.render.engine = "BLENDER_WORKBENCH"
    scn.display.shading.light = "STUDIO"
    scn.display.shading.color_type = "MATERIAL"
    scn.display.shading.show_object_outline = False
    scn.render.resolution_x = scn.render.resolution_y = 420
    for tag, loc, rot in (("front", (0, -6, 0), (math.pi / 2, 0, 0)), ("side", (6, 0, 0), (math.pi / 2, 0, math.pi / 2))):
        cam.location = loc
        cam.rotation_euler = rot
        scn.render.filepath = path + "_" + tag + ".png"
        bpy.ops.render.render(write_still=True)


def do_file(src, name, report, info, want_preview):
    reset()
    bpy.ops.wm.obj_import(filepath=src)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        report.append(f"{name}: no mesh")
        return
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = "Hair_" + name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co.copy() for v in ob.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    c = (lo + hi) / 2
    head = None
    if HEADS:
        n, hw = min(HEADS, key=lambda t: (t[1].x - c.x) ** 2 + (t[1].y - c.y) ** 2)
        if (hw.x - c.x) ** 2 + (hw.y - c.y) ** 2 < 1.5 ** 2:
            head = hw - c
            report.append(f"{name}: head from '{n}' at {tuple(round(t, 2) for t in head)}")
            print("[hairrig]", report[-1], flush=True)
    for v in ob.data.vertices:
        v.co -= c
    ob.data.update()
    ao = rig(ob, report, head)
    if not ao:
        return
    d = hi - lo
    info[name] = {"size_studs": [round(d.x, 4), round(d.z, 4), round(d.y, 4)], "bones": len(ao.data.bones)}
    bpy.ops.object.select_all(action="DESELECT")
    ao.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=True, object_types={"ARMATURE", "MESH"},
                             add_leaf_bones=False, bake_anim=False, apply_unit_scale=True, global_scale=1.0,
                             axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP",
                             use_armature_deform_only=True)
    if want_preview:
        os.makedirs(os.path.join(OUT, "_preview"), exist_ok=True)
        preview(ob, ao, os.path.join(OUT, "_preview", name))


def main():
    import json
    want_preview = len(argv) > 2 and argv[2] == "preview"
    files = []
    if os.path.isdir(SRC):
        for dp, _, fs in os.walk(SRC):
            for f in sorted(fs):
                if f.lower().endswith(".obj"):
                    rel = os.path.relpath(os.path.join(dp, f), SRC)
                    files.append((os.path.join(dp, f), safe_name(os.path.splitext(rel)[0].replace(os.sep, "_"))))
    else:
        files.append((SRC, safe_name(os.path.splitext(os.path.basename(SRC))[0])))
    report, info = [f"source {SRC}: {len(files)} files"], {}
    for src, name in files:
        try:
            do_file(src, name, report, info, want_preview)
        except Exception as e:  # one bad mesh shouldn't stop the batch
            report.append(f"{name}: FAILED {e!r}")
        print("[hairrig]", report[-1], flush=True)
    open(os.path.join(OUT, "rig_report.txt"), "w", encoding="utf-8").write("\n".join(report))
    json.dump(info, open(os.path.join(OUT, "rig_report.json"), "w"), indent=1)
    print("[hairrig] done", len(info), "rigged", flush=True)


main()
