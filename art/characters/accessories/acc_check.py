"""Clearance check for the accessory kits: nothing may clip into a body or hair, overlap another accessory, or hover.

E:/Blender/blender.exe -b --factory-startup -P acc_check.py -- [--root E:/NH-Work/acc] [--items A,B] [--hair] [--json out.json]

Reads every built item (<root>/blend/<Item>.blend, rest pose) and its layout (<root>/layout/<Item>.json), and reports:
  body   for each body type (the plain R6 boxes + the 11 meshed bodies), after that body's depth fit (layout fit_body):
         clip  = the deepest any vertex of the piece sits inside the body (studs; > CLIP_TOL fails)
         gap   = the smallest distance from the piece to the body (studs; > HOVER_TOL fails for pieces that rest on it,
                 i.e. everything except Halo / Familiar / Trail / held pieces)
  hair   head pieces only (--hair): against each of the game's 35 rigged hairs on the standard head, the deepest
         hair vertex inside the piece's closed volume and how many hairs poke through (reported, see notes)
  pairs  every two pieces of different slots worn on the same part: the number of their triangles that intersect
         (BVHTree.overlap) on the standard body and the Female body; > 0 fails
Exit report: a table per piece and a FAIL list.
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
ONLY = argv[argv.index("--items") + 1].split(",") if "--items" in argv else None
HAIR = "--hair" in argv
OUTJ = argv[argv.index("--json") + 1] if "--json" in argv else os.path.join(ROOT, "check.json")
CLIP_TOL = 0.003
HOVER_TOL = 0.035
FREE_SLOTS = {"Halo", "Familiar", "Trail", "Hand", "Hat"}   # hats rest on the hair: checked by --hair
BODY_BLEND = "E:/NH-Work/bodytypes/NHBodyTypes.blend"
FEM_BLEND = "E:/NH-Work/femalebody/NHFemaleBody.blend"
BODIES = ["standard", "female", "lean", "athletic", "muscular", "stocky", "heavy", "petite", "toned", "curvy", "strong", "plus"]
PART_AT = {"Torso": Vector((0, 0, 0)), "LeftArm": Vector((1.5, 0, 0)), "RightArm": Vector((-1.5, 0, 0)),
           "LeftLeg": Vector((0.5, 0, -2)), "RightLeg": Vector((-0.5, 0, -2))}
MOUNT_CENTRE = dict(PART_AT, Head=Vector((0, 0, 1.5)))
# which slot each item fills (Config.Accessories): pieces of the same slot are never worn together
SLOT_OF = {}


PENDING = "E:/NH-Work/acc/src/pending"   # items_<batch>.luau: a batch's item and conflict lines before they're merged


def config_texts():
    """Config.Accessories plus every pending batch fragment (same line formats)"""
    out = []
    p = "E:/NH-Work/acc/src/Accessories.luau"
    if os.path.exists(p):
        out.append(open(p, encoding="utf-8").read())
    if os.path.isdir(PENDING):
        for f in sorted(os.listdir(PENDING)):
            if f.endswith(".luau"):
                out.append(open(os.path.join(PENDING, f), encoding="utf-8").read())
    return out


def load_slots():
    import re
    for t in config_texts():
        for m in re.finditer(r"Slot = `(\w+)`; Model = `(\w+)`(?:; Piece = `(\w+)`)?", t):
            slot, model, pc = m.groups()
            SLOT_OF[(model, pc)] = slot


CONFLICTS = []
ID_OF = {}


def load_conflicts():
    import re
    for n, t in enumerate(config_texts()):
        for m in re.finditer(r"Id = `([\w-]+)`; Name = `[^`]*`; Slot = `(\w+)`; Model = `(\w+)`(?:; Piece = `(\w+)`)?(?:; Pieces = \{([^}]*)\})?", t):
            iid, slot, model, pc, many = m.groups()
            ID_OF[(model, pc)] = iid
            for q in re.findall(r"`(\w+)`", many or ""):   # an item of several pieces (a hat and its veil)
                ID_OF[(model, q)] = iid
                SLOT_OF[(model, q)] = slot
        if n == 0 and "Accessories.Conflicts = {" in t:
            blk = t[t.index("Accessories.Conflicts = {"):t.index("Accessories.ById = {}")]
        else:   # a fragment: its conflict lines sit under a "-- conflicts" comment
            blk = t[t.index("-- conflicts"):] if "-- conflicts" in t else ""
        CONFLICTS.extend(re.findall(r"\{ `([\w:*-]+)`, `([\w:*-]+)` \}", blk))


CAPE_ID = {"CapeWardenMantle": "CapeWardenMantle", "CapeReaperShroud": "CapeReaperShroud", "CapeDuelistCape": "CapeDuelist",
           "CapeCaptainGreatcape": "CapeCaptain", "CapeMidnightCollar": "CapeMidnight"}   # UI.Appearance.Capes ids


def exclusive(a, b):
    ia, ib = ID_OF.get(a) or ID_OF.get((a[0], None)), ID_OF.get(b) or ID_OF.get((b[0], None))
    if a[0] in CAPE_ID:
        ia = "cape:" + CAPE_ID[a[0]]
    if b[0] in CAPE_ID:
        ib = "cape:" + CAPE_ID[b[0]]
    for x, y in CONFLICTS:   # "cape:*" stands for every cape
        for p, q in ((x, y), (y, x)):
            if p == "cape:*" and ((ia or "").startswith("cape:") and q in (ib, slot_of(*b)) or
                                  (ib or "").startswith("cape:") and q in (ia, slot_of(*a))):
                return True
    sa, sb = slot_of(*a), slot_of(*b)
    for x, y in CONFLICTS:
        if (x in (ia, sa) and y in (ib, sb)) or (x in (ib, sb) and y in (ia, sa)):
            return True
    return False


def slot_of(item, piece):
    return SLOT_OF.get((item, piece)) or SLOT_OF.get((item, None)) or "?"


def tri_bvh(verts, tris):
    return BVHTree.FromPolygons(verts, tris, epsilon=0.0)


def mesh_tris(ob, M=Matrix()):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    W = M @ ob.matrix_world
    verts = [W @ v.co for v in me.vertices]
    me.calc_loop_triangles()
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return verts, tris


def standard_body():
    """the plain R6 body: bevelled boxes (Roblox's R6 parts are boxes) + the head's rounded cylinder"""
    out = {}
    for part, c in PART_AT.items():
        sz = (2, 1, 2) if part == "Torso" else (1, 1, 2)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * sz[0], v.co.y * sz[1], v.co.z * sz[2])) + c
        bmesh.ops.triangulate(bm, faces=bm.faces)
        out[part] = ([v.co.copy() for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces])
        bm.free()
    return out


def head_mesh():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=1.2, location=(0, 0, 1.5), vertices=40)
    hd = bpy.context.object
    md = hd.modifiers.new("b", "BEVEL"); md.width = 0.25; md.segments = 5
    v, t = mesh_tris(hd)
    bpy.data.objects.remove(hd)
    return v, t


def load_body_meshes():
    names = {}
    with bpy.data.libraries.load(BODY_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("NHBody_")]
    with bpy.data.libraries.load(FEM_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("NHFem_")]
    for ob in bpy.data.objects:
        nm = ob.name
        if nm.startswith("NHBody_"):
            _, bid, part = nm.split("_", 2)
        elif nm.startswith("NHFem_"):
            bid, part = "female", nm.split("_", 1)[1]
        else:
            continue
        me = ob.data
        me.calc_loop_triangles()
        names.setdefault(bid, {})[part] = ([v.co + PART_AT[part] for v in me.vertices], [tuple(t.vertices) for t in me.loop_triangles])
    return names


def inside_depth(bvh, p, max_d=0.6):
    """how deep p is inside the closed mesh (0 if outside): the nearest surface point's normal faces away from p"""
    hit = bvh.find_nearest(p, max_d)
    if hit[0] is None:
        return 0.0, None
    loc, nrm, idx, dist = hit
    d = (p - loc)
    if d.dot(nrm) < 0:
        return dist, loc
    return 0.0, dist


def check_body(verts, mount, body_parts, head):
    """clip and gap of a piece's verts against a body (mount part, the torso and the head checked)"""
    clip, gap = 0.0, 9.0
    trees = [(k, tri_bvh(*v)) for k, v in body_parts.items()] + [("Head", tri_bvh(*head))]
    step = max(1, len(verts) // 3000)
    where = ""
    def inside(t, p):
        """ray parity along three axes (robust at sharp box edges); inside when at least two say odd"""
        votes = 0
        for d in (Vector((0.577, 0.577, 0.577)), Vector((-0.6, 0.2, 0.775)), Vector((0.31, -0.81, 0.5))):
            n, o = 0, p.copy()
            for _ in range(12):
                h = t.ray_cast(o, d, 20.0)
                if h[0] is None:
                    break
                n += 1
                o = h[0] + d * 1e-4
            votes += n % 2
        return votes >= 2
    for p in verts[::step]:
        for k, t in trees:
            hit = t.find_nearest(p, 0.6)
            if hit[0] is None:
                continue
            loc, nrm, idx, dist = hit
            if dist > 1e-4 and inside(t, p):
                if k in ("LeftArm", "RightArm") and 1.0 <= abs(p.x) <= 1.10 and p.z <= 1.0:
                    continue   # under the arm: the R6 arm is flush on the torso's side and swings in its own plane, so a
                    # strap in its inner 0.1 studs is covered by it in every pose (it reads as passing under the arm)
                if dist > clip:
                    clip, where = dist, f"{k} at ({p.x:.2f}, {p.y:.2f}, {p.z:.2f})"
            else:
                gap = min(gap, dist)
    return clip, gap, where


def depth_fit(verts, mount, s):
    if s == 1.0 or mount == "Head":
        return verts
    c = MOUNT_CENTRE[mount]
    return [Vector((p.x, c.y + (p.y - c.y) * s, p.z)) for p in verts]


# AccessorySway's profiles (max bend at the tip, max per joint), degrees
SWAY = {"Flutter": (8, 4), "Loops": (9, 6), "Pendulum": (34, 20), "BackHang": (24, 16), "Tails": (50, 15)}
LIMB_DEG = 55   # walking and sprinting swing the R6 limbs to about +-40..50 degrees


def limb_pose(bodies_parts, deg):
    """the body with both arms and legs swung: arms about the shoulder line (y 0, z 0.5), legs about the hips (y 0,
    z -1), the left and right in opposite phase like a stride"""
    out = {}
    for part, (v, t) in bodies_parts.items():
        if part.endswith("Arm"):
            a = math.radians(deg if part == "LeftArm" else -deg)
            piv = Vector((0, 0, 0.5))
        elif part.endswith("Leg"):
            a = math.radians(-deg if part == "LeftLeg" else deg)
            piv = Vector((0, 0, -1.0))
        else:
            out[part] = (v, t)
            continue
        R = Matrix.Rotation(a, 3, "X")
        out[part] = ([R @ (p - piv) + piv for p in v], t)
    return out, {"LeftArm": (0.5, deg), "RightArm": (0.5, -deg)}


def moved_piece(verts, mount, arm_rot):
    if mount in arm_rot:
        zc, deg = arm_rot[mount]
        R = Matrix.Rotation(math.radians(deg), 3, "X")
        piv = Vector((0, 0, zc))
        return [R @ (p - piv) + piv for p in verts]
    return verts


def sway_shapes(ob, arm, profile, keepout, lock=None):
    """the piece bent to its sway limit toward each allowed pull direction (never toward the body: keepout)"""
    bend, joint = SWAY.get(profile, (34, 20))
    pulls = [Vector(d) for d in ((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0.7, 0.7, 0), (-0.7, 0.7, 0))]
    ko = Vector(keepout) if keepout else None
    out = []
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    bones = []
    for pb in arm.pose.bones:
        depth, p = 0, pb.parent
        while p:
            depth += 1; p = p.parent
        bones.append((pb, depth))
    for pull in pulls:
        if ko is not None and pull.dot(ko) > 0.1:
            continue
        if lock == "X" and abs(pull.x) > 0.1:
            continue
        if lock == "Z" and abs(pull.y) > 0.1:
            continue
        for pb, depth in bones:
            if depth < 2:
                pb.rotation_mode = "AXIS_ANGLE"; pb.rotation_axis_angle = (0, 0, 0, 1)
                continue
            # chain length below the hinge, for the share
            n, q = depth, pb
            while q.children:
                q = q.children[0]; n += 1
            cnt = n - 1
            share = (depth - 1) / (cnt * (cnt + 1) / 2) if cnt > 0 else 0
            rest = pb.bone.matrix_local.to_3x3()
            dirw = (rest @ Vector((0, 1, 0))).normalized()
            axis = dirw.cross(pull)
            if lock in ("X", "Z"):   # bend only about the locked axis (Roblox X = Blender X, Roblox Z = Blender Y)
                L = Vector((1, 0, 0)) if lock == "X" else Vector((0, 1, 0))
                axis = L * axis.dot(L)
            if axis.length < 1e-4:
                pb.rotation_axis_angle = (0, 0, 0, 1); continue
            ang = min(math.radians(bend) * share, math.radians(joint))
            ax = (rest.inverted() @ axis.normalized())
            pb.rotation_mode = "AXIS_ANGLE"
            pb.rotation_axis_angle = (ang, *ax)
        bpy.context.view_layer.update()
        v, t = mesh_tris(ob)
        out.append((tuple(round(x, 1) for x in pull), v))
    for pb, depth in bones:
        pb.rotation_axis_angle = (0, 0, 0, 1)
    bpy.ops.object.mode_set(mode="OBJECT")
    return out


KATANA_JSON = "E:/NH-Work/acc/katana_obstacles.json"
KATANA_PAD = 1.12   # the katana's parts vary a little in size with the student (0.43-0.48 blade width seen)


def katana_boxes():
    """the Katana (the game's one sheathed weapon) as padded boxes in Blender body space, measured in NH Combat Test
    (katana_obstacles.json): 'sheathed' hangs off the Torso at the left hip; 'drawn' is gripped by the Right Arm.
    Returns {tag: [(name, verts, tris, centre, axes, half)]}"""
    if not os.path.exists(KATANA_JSON):
        return {}
    out = {}
    for e in json.load(open(KATANA_JSON))["parts"]:
        state, mount = e["tag"].split(":")
        c = e["cf"]
        pos = Vector(c[0:3])
        R = Matrix(((c[3], c[4], c[5]), (c[6], c[7], c[8]), (c[9], c[10], c[11])))   # Roblox rotation, columns = axes
        half = Vector(e["size"]) * 0.5 * KATANA_PAD
        base = PART_AT.get(mount, Vector())
        def to_b(v):   # Roblox mount space -> Blender body space
            return Vector((-v.x, v.z, v.y)) + base
        axes = [R.col[i].copy() for i in range(3)]
        corners = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    corners.append(to_b(pos + axes[0] * half.x * sx + axes[1] * half.y * sy + axes[2] * half.z * sz))
        bm = bmesh.new()
        for p in corners:
            bm.verts.new(p)
        bm.verts.ensure_lookup_table()
        hull = bmesh.ops.convex_hull(bm, input=bm.verts)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        verts = [v.co.copy() for v in bm.verts]
        tris = [tuple(v.index for v in f.verts) for f in bm.faces]
        bm.free()
        baxes = [Vector((-a.x, a.z, a.y)) for a in axes]
        out.setdefault(state, []).append((e["part"], verts, tris, to_b(pos), baxes, half))
    return out


def katana_hits(verts, tris, boxes):
    """(surface crossings, points inside) of a piece against the katana's boxes"""
    tree = tri_bvh(verts, tris)
    cross, inside, where = 0, 0, ""
    for name, bv, bt, c, axes, half in boxes:
        n = len(tree.overlap(tri_bvh(bv, bt)))
        k = 0
        for p in verts:
            d = p - c
            if abs(d.dot(axes[0])) < half.x and abs(d.dot(axes[1])) < half.y and abs(d.dot(axes[2])) < half.z:
                k += 1
                if not where:
                    where = f"{name} at ({p.x:.2f}, {p.y:.2f}, {p.z:.2f})"
        if n and not where:
            where = name
        cross += n
        inside += k
    return cross, inside, where


def fix_layers(pieces):
    """raise each outer torso layer's depth fit on each body only as far as it takes to clear the inner layers it
    crosses (acc_layers.LAYERS: shirt < sash < strap), and write it back to the layouts"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("acc_layers_cfg", os.path.join(HERE, "acc_layers.py"))
    src = open(os.path.join(HERE, "acc_layers.py"), encoding="utf-8").read()
    ns = {}
    exec(src[:src.index("if __name__")], ns)
    order = []
    for li, (_, members) in enumerate(ns["LAYERS"]):
        for m in members:
            if m in pieces:
                order.append((li, m))
    changed = {}
    for bid in BODIES:
        for li, outer in order:
            for lj, inner in order:
                if lj >= li:
                    continue
                if exclusive(outer, inner) or slot_of(*outer) == slot_of(*inner):
                    continue
                Pi, Po = pieces[inner], pieces[outer]
                ti = tri_bvh(depth_fit(Pi["verts"], Pi["mount"], Pi["fit_body"].get(bid, 1.0)), Pi["tris"])
                s_ = Po["fit_body"].get(bid, 1.0)
                n = 0
                while s_ < 1.45 and tri_bvh(depth_fit(Po["verts"], Po["mount"], s_), Po["tris"]).overlap(ti):
                    s_ = round(s_ + 0.01, 3); n += 1
                if n:
                    Po["fit_body"][bid] = s_
                    changed.setdefault(outer, {})[bid] = s_
    for (it, pn), fb in changed.items():
        lp = os.path.join(ROOT, "layout", f"{it}.json")
        lay = json.load(open(lp))
        lay["pieces"][pn].setdefault("fit_body", {}).update(fb)
        json.dump(lay, open(lp, "w"), indent=1)
        print("CHECK fixlayers", f"{it}/{pn}", fb)


def run():
    load_slots()
    load_conflicts()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bodies = {"standard": standard_body()}
    bodies.update(load_body_meshes())
    head = head_mesh()
    items = sorted(f[:-6] for f in os.listdir(os.path.join(ROOT, "blend")) if f.endswith(".blend"))
    if ONLY:
        items = [i for i in items if i in ONLY]
    pieces = {}   # (item, piece) -> dict(verts, tris, mount, fit_body)
    for it in items:
        lay = json.load(open(os.path.join(ROOT, "layout", f"{it}.json")))
        with bpy.data.libraries.load(os.path.join(ROOT, "blend", f"{it}.blend"), link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n in lay["pieces"] or (n.endswith("Rig") and n[:-3] in lay["pieces"])]
        objs = {o.name: o for o in dst.objects if o is not None}
        for o in objs.values():
            bpy.context.scene.collection.objects.link(o)
        for name, ob in objs.items():
            if name not in lay["pieces"]:
                continue
            e = lay["pieces"][name]
            arm = objs.get(name + "Rig")
            v, t = mesh_tris(ob)
            P = dict(verts=v, tris=t, mount=e["mount"], fit_body=e.get("fit_body", {}), kind=e["kind"], hair_fit=e.get("hair_fit"))
            if arm is not None:
                ko = e.get("keepout")   # Roblox mount axes -> Blender (x, y, z) = (-x, z, y)
                kb = (-ko[0], ko[2], ko[1]) if ko else None
                P["sway"] = sway_shapes(ob, arm, e.get("sway", "Pendulum"), kb, e.get("lock"))
            pieces[(it, name)] = P
        for o in objs.values():
            bpy.data.objects.remove(o)
    if "--capes" in argv:   # the admin capes (art/characters/capes): slot Cape, rest pose, standard and female bodies only
        for key in ("WardenMantle", "ReaperShroud", "DuelistCape", "CaptainGreatcape", "MidnightCollar"):
            bp = f"E:/NH-Work/capes/{key}.blend"
            if not os.path.exists(bp):
                continue
            with bpy.data.libraries.load(bp, link=False) as (src, dst):
                dst.objects = [n for n in src.objects if n == "CapeBody"]
            ob = dst.objects[0]
            bpy.context.scene.collection.objects.link(ob)
            for md in list(ob.modifiers):
                ob.modifiers.remove(md)
            ob.parent = None
            v, t = mesh_tris(ob)
            pieces[("Cape" + key, "CapeBody")] = dict(verts=v, tris=t, mount="Torso", fit_body={}, kind="Cape")
            SLOT_OF[("Cape" + key, "CapeBody")] = "Cape"
            bpy.data.objects.remove(ob)
    if "--fixlayers" in argv:
        fix_layers(pieces)
    report, fails = {}, []
    for (it, pn), P in pieces.items():
        slot = slot_of(it, pn)
        if P["kind"] == "Cape":
            continue
        r = {"slot": slot, "mount": P["mount"], "bodies": {}}
        for bid in BODIES:
            if bid not in bodies:
                continue
            s = P["fit_body"].get(bid, 1.0)
            vv = depth_fit(P["verts"], P["mount"], s)
            clip, gap, where = check_body(vv, P["mount"], bodies[bid], head)
            r["bodies"][bid] = [round(clip, 4), round(gap, 4), s]
            if clip > CLIP_TOL:
                fails.append(f"CLIP {it}/{pn} on {bid}: {clip:.3f} into {where}")
            if slot not in FREE_SLOTS and gap > HOVER_TOL and P["kind"] != "Alpha":
                fails.append(f"HOVER {it}/{pn} on {bid}: gap {gap:.3f}")
        report[f"{it}/{pn}"] = r
    # motion: limbs swung to +-LIMB_DEG (both strides), and each rigged piece at its sway limit, on every body
    for (it, pn), P in pieces.items():
        slot = slot_of(it, pn)
        if P["kind"] == "Cape":
            continue
        worst = (0.0, "")
        for bid in BODIES:
            if bid not in bodies:
                continue
            s_ = P["fit_body"].get(bid, 1.0)
            for deg in (LIMB_DEG, -LIMB_DEG):
                posed, arm_rot = limb_pose(bodies[bid], deg)
                vv = moved_piece(depth_fit(P["verts"], P["mount"], s_), P["mount"], arm_rot)
                if P["mount"] in arm_rot:   # a held piece moves with its arm: check it against the rest of the body
                    posed = {k: v for k, v in posed.items() if k != P["mount"]}
                clip, gap, where = check_body(vv, P["mount"], posed, head)
                if clip > worst[0]:
                    worst = (clip, f"{bid}, limbs {deg:+d}: {where}")
            for pull, sv in P.get("sway", []):
                vv = depth_fit(sv, P["mount"], s_)
                clip, gap, where = check_body(vv, P["mount"], bodies[bid], head)
                if clip > worst[0]:
                    worst = (clip, f"{bid}, swung toward {pull}: {where}")
        report[f"{it}/{pn}"]["motion"] = [round(worst[0], 4), worst[1]]
        if worst[0] > CLIP_TOL:
            fails.append(f"MOTION {it}/{pn}: {worst[0]:.3f} into {worst[1]}")
    # carried weapons: the sheathed katana at the left hip against every piece (rest, both strides, every sway limit) on
    # every body; the drawn katana against arm pieces (they move with it). Held-slot pieces are hidden while a weapon is
    # drawn (Services.Features.Accessories), so the drawn check is a report for them, not a fail.
    kb = katana_boxes()
    for (it, pn), P in pieces.items():
        if P["kind"] == "Cape" or not kb:
            continue
        slot = slot_of(it, pn)
        worst = (0, 0, "")
        for bid in BODIES:
            if bid not in bodies:
                continue
            s_ = P["fit_body"].get(bid, 1.0)
            shapes = [("rest", depth_fit(P["verts"], P["mount"], s_))]
            for deg in (LIMB_DEG, -LIMB_DEG):
                _, arm_rot = limb_pose(bodies[bid], deg)
                shapes.append((f"limbs {deg:+d}", moved_piece(depth_fit(P["verts"], P["mount"], s_), P["mount"], arm_rot)))
            for pull, sv in P.get("sway", []):
                shapes.append((f"swung {pull}", depth_fit(sv, P["mount"], s_)))
            for label, vv in shapes:
                c_, i_, w_ = katana_hits(vv, P["tris"], kb.get("sheathed", []))
                if c_ + i_ > worst[0] + worst[1]:
                    worst = (c_, i_, f"sheathed, {bid}, {label}: {w_}")
                if P["mount"] == "RightArm" and (label == "rest" or label.startswith("swung")):
                    c2, i2, w2 = katana_hits(vv, P["tris"], kb.get("drawn", []))
                    if c2 + i2:
                        msg = f"DRAWN {it}/{pn} on {bid}, {label}: {c2} crossings, {i2} points inside ({w2})"
                        if slot == "Hand":
                            report.setdefault(f"{it}/{pn}", {}).setdefault("drawn", []).append(msg)
                        else:
                            fails.append("KATANA-" + msg)
        report[f"{it}/{pn}"]["katana"] = [worst[0], worst[1], worst[2]]
        if worst[0] + worst[1]:
            fails.append(f"KATANA {it}/{pn}: {worst[0]} crossings, {worst[1]} points inside ({worst[2]})")
    # pairs: pieces of different slots on the same (or neighbouring) parts
    keys = list(pieces)
    for bid in ("standard", "female"):
        trees, vvs = {}, {}
        for k in keys:
            P = pieces[k]
            vv = depth_fit(P["verts"], P["mount"], P["fit_body"].get(bid, 1.0))
            trees[k] = tri_bvh(vv, P["tris"])
            vvs[k] = vv
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                sa, sb = slot_of(*a), slot_of(*b)
                if sa == sb or a[0] == b[0] and sa == "?":
                    continue
                if exclusive(a, b):
                    continue   # never worn together (Config.Accessories.Conflicts)
                ov = trees[a].overlap(trees[b])
                # a swinging piece at its limits against the other one at rest (both ways round)
                for x, y in ((a, b), (b, a)):
                    for pull, sv in pieces[x].get("sway", []):
                        t2 = tri_bvh(depth_fit(sv, pieces[x]["mount"], pieces[x]["fit_body"].get(bid, 1.0)), pieces[x]["tris"])
                        o2 = t2.overlap(trees[y])
                        if o2:
                            fails.append(f"OVERLAP-SWING {x[0]}/{x[1]} swung {pull} x {y[0]}/{y[1]} on {bid}: {len(o2)} tri pairs")
                n = len(ov)
                if n:
                    ta = pieces[a]["tris"][ov[0][0]]
                    c = sum((vvs[a][i] for i in ta), Vector()) / 3
                    fails.append(f"OVERLAP {a[0]}/{a[1]} ({sa}) x {b[0]}/{b[1]} ({sb}) on {bid}: {n} tri pairs, e.g. at ({c.x:.2f}, {c.y:.2f}, {c.z:.2f})")
    if HAIR:
        hair_report(pieces, report, fails)
    json.dump(dict(report=report, fails=fails), open(OUTJ, "w"), indent=1)
    print("CHECK pieces", len(pieces))
    for k, r in report.items():
        if not r.get("bodies"):
            continue
        worst = max(r["bodies"].values(), key=lambda x: x[0]) if r["bodies"] else [0, 0]
        gaps = [x[1] for x in r["bodies"].values()]
        print(f"CHECK {k:40s} {r['slot']:9s} clip max {worst[0]:.3f}  gap {min(gaps):.3f}..{max(gaps):.3f}")
    for f in fails:
        print("CHECK FAIL", f)
    print("CHECK done", len(fails), "fails")


def hair_report(pieces, report, fails):
    """head pieces vs the game's rigged hairs (on the standard head): how deep the hair pokes through the piece"""
    import nh_acc as A
    offs = A._hair_offsets()
    hairs = sorted(offs)
    hair_meshes = {}
    for h in hairs:
        ob = A.real_hair(h)
        if ob is None:
            continue
        v, t = mesh_tris(ob)
        hair_meshes[h] = (v, t)
        bpy.data.objects.remove(ob)
    for (it, pn), P in pieces.items():
        if P["mount"] != "Head" or P["kind"] == "Alpha":
            continue
        hits = {}
        fits = P.get("hair_fit") or {}
        piv = Vector((0, 0, 1.93))   # the headband centre: head pieces are worn scaled about it and lifted, per hair
        for h, (v, t) in hair_meshes.items():
            if h in fits and fits[h] is None:
                continue   # this hair can't wear the piece (the Wardrobe and the server refuse it)
            k, dz = fits.get(h) or (1.0, 0.0)
            vv = [piv + (q - piv) * k + Vector((0, 0, dz)) for q in P["verts"]]
            n = len(tri_bvh(vv, P["tris"]).overlap(tri_bvh(v, t)))
            if n:
                hits[h] = n
        report[f"{it}/{pn}"]["hair"] = hits
        if hits:
            fails.append(f"HAIR {it}/{pn}: {len(hits)}/{len(hair_meshes)} hairs cross it ({', '.join(sorted(hits)[:6])}...)")


if __name__ == "__main__":
    run()
